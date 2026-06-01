---
corso: "Automazioni e Flussi di Lavoro"
fase: "3 — Automazione per Dominio"
modulo: 5
titolo: "Automazione per Dominio"
versione: "1.0"
livello: "Avanzato"
prerequisiti:
  - "Moduli 01-04"
  - "Conoscenza base dei domini HR, Sales, Finance, IT Ops"
obiettivi:
  - "Identificare le automazioni a più alto ROI per ciascun dominio aziendale"
  - "Progettare workflow HR/Finance rispettando vincoli GDPR, retention e audit trail"
  - "Costruire automazioni IT Ops per provisioning, monitoring e incident response"
  - "Applicare pattern ricorrenti cross-dominio (notifiche, approvazioni, data sync)"
  - "Valutare rischio e compliance prima di automatizzare processi sensibili"
tag: [dominio, hr, finance, sales, it-ops, marketing, gdpr, compliance]
---

# Automazione per Dominio — Guida Completa

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 5 — Governance · Modulo 05
> **Prerequisiti:** Moduli 01-04, 09-14 (piattaforme).
> **Obiettivi:** identificare automazioni di valore per dominio (HR, Sales, Finance, IT Ops, Marketing); pattern ricorrenti per dominio.
> **Tempo:** lettura 90 min · lab 240 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Identificare le automazioni a più alto ROI per ciascun dominio aziendale
> 2. Progettare workflow HR/Finance rispettando vincoli GDPR, retention e audit trail
> 3. Costruire automazioni IT Ops per provisioning, monitoring e incident response
> 4. Applicare pattern ricorrenti cross-dominio (notifiche, approvazioni, data sync)
> 5. Valutare rischio e compliance prima di automatizzare processi sensibili
>
> **Prerequisiti:** [Modulo 01](01-fondamenti-automazione.md), [Modulo 02](02-piattaforme-low-code.md), [Modulo 03](03-scripting-automazione.md), [Modulo 04](04-integrazione-api.md)
> **Tempo stimato:** 5-6 ore · **Livello:** Avanzato

## Idee guida

1. **L'automazione segue il valore di business, non il valore tecnico.** Automatizzare un task da 5min/settimana e tempo perso; uno da 5h/settimana e ROI immediato.
2. **Dominio HR/Finance ha compliance constraint forti.** GDPR, retention period, audit trail.
3. **Dominio IT Ops e dove iniziare quasi sempre.** Tu controlli sia processo che strumento.
4. **Marketing automation richiede A/B test.** Senza misurazione e bias driven.

---

## Indice

1. [Panoramica](#panoramica)
2. [Automazione Gestione Documenti e File](#automazione-gestione-documenti-e-file)
   - [Organizzazione Automatica File](#organizzazione-automatica-file)
   - [Conversione Formato](#conversione-formato)
   - [Backup e Sincronizzazione](#backup-e-sincronizzazione)
   - [Archiviazione](#archiviazione)
3. [Automazione IT Operations](#automazione-it-operations)
   - [User Provisioning/Deprovisioning](#user-provisioningdeprovisioning)
   - [Patch Management Automation](#patch-management-automation)
   - [Monitoring e Alerting](#monitoring-e-alerting)
   - [Report Generation](#report-generation)
4. [Automazione Comunicazione](#automazione-comunicazione)
   - [Email Automation](#email-automation)
   - [Notifiche Multi-Canale](#notifiche-multi-canale)
   - [Chatbot e Assistenti](#chatbot-e-assistenti)
5. [Automazione Sicurezza](#automazione-sicurezza)
   - [Scansione Automatica](#scansione-automatica)
   - [Incident Response Automation](#incident-response-automation)
   - [Gestione Certificati](#gestione-certificati)
6. [Automazione Cloud e DevOps](#automazione-cloud-e-devops)
   - [Infrastructure as Code](#infrastructure-as-code)
   - [Container Automation](#container-automation)
7. [Best Practices](#best-practices)

---

## Panoramica

L'automazione per dominio rappresenta l'applicazione di tecniche, strumenti e flussi automatizzati a specifici ambiti operativi all'interno di un'organizzazione. A differenza dell'automazione generica, che si concentra su principi e piattaforme trasversali, l'automazione per dominio parte dalle esigenze concrete di ogni area funzionale e costruisce soluzioni mirate che risolvono problemi reali e ricorrenti.

In un contesto aziendale moderno, le attivita ripetitive consumano una porzione significativa del tempo lavorativo. Secondo diverse analisi di settore, fino al 40% delle ore lavorate viene dedicato a compiti che possono essere parzialmente o totalmente automatizzati. L'automazione per dominio affronta questa realta suddividendo il panorama in categorie operative distinte:

- **Gestione Documenti e File**: organizzazione, conversione, backup e archiviazione automatica dei file aziendali.
- **IT Operations**: provisioning utenti, gestione patch, monitoring infrastrutturale e generazione report.
- **Comunicazione**: automazione email, notifiche multi-canale, chatbot e assistenti conversazionali.
- **Sicurezza**: scansioni automatiche, incident response, gestione certificati e compliance.
- **Cloud e DevOps**: Infrastructure as Code, automazione container e pipeline di deployment.

Ogni dominio presenta sfide uniche, requisiti di conformita specifici e strumenti dedicati. L'obiettivo di questa guida e fornire una comprensione approfondita di ciascuna area, con esempi pratici di codice, architetture di riferimento e indicazioni operative che permettano di implementare soluzioni di automazione efficaci e manutenibili.

Il valore dell'automazione per dominio non risiede soltanto nel risparmio di tempo. Essa introduce coerenza nei processi, riduce gli errori umani, migliora la tracciabilita delle operazioni e consente ai team di concentrarsi su attivita ad alto valore aggiunto. Un processo di onboarding automatizzato, ad esempio, non solo risparmia ore di lavoro manuale, ma garantisce che ogni nuovo dipendente riceva esattamente le stesse risorse, accessi e configurazioni, eliminando dimenticanze e discrepanze.

Nel corso di questa guida, per ogni dominio verranno presentati: il contesto operativo, gli strumenti principali, esempi di codice funzionanti e considerazioni architetturali. Il linguaggio di riferimento per gli script e Python, con integrazioni in Bash, PowerShell e strumenti specifici dove necessario.

---

## Automazione Gestione Documenti e File

La gestione documentale rappresenta uno dei domini dove l'automazione produce risultati immediati e tangibili. Ogni organizzazione genera, riceve e archivia quotidianamente centinaia o migliaia di file. Senza processi automatizzati, la gestione manuale diventa rapidamente insostenibile e soggetta a errori.

### Organizzazione Automatica File

L'organizzazione automatica dei file e il punto di partenza per qualsiasi strategia di automazione documentale. L'idea fondamentale e semplice: definire regole che determinano dove ogni file deve risiedere, con quale nome e in quale struttura di cartelle, e applicare queste regole automaticamente.

**Ordinamento per tipo, data e progetto**

Un sistema di organizzazione efficace classifica i file lungo piu dimensioni. La classificazione per tipo (estensione) e la piu immediata, ma spesso insufficiente. Un approccio maturo combina il tipo di file con metadati temporali e contestuali:

```python
import os
import shutil
from pathlib import Path
from datetime import datetime

# Mappa delle categorie per estensione
CATEGORIE_FILE = {
    'Documenti': ['.pdf', '.doc', '.docx', '.txt', '.odt', '.rtf', '.xlsx', '.csv'],
    'Immagini': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff'],
    'Video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
    'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'],
    'Archivi': ['.zip', '.tar', '.gz', '.rar', '.7z', '.bz2'],
    'Codice': ['.py', '.js', '.ts', '.java', '.cpp', '.html', '.css', '.json'],
    'Presentazioni': ['.ppt', '.pptx', '.key', '.odp'],
}

def determina_categoria(estensione: str) -> str:
    """Restituisce la categoria di appartenenza per una data estensione."""
    for categoria, estensioni in CATEGORIE_FILE.items():
        if estensione.lower() in estensioni:
            return categoria
    return 'Altro'

def organizza_directory(sorgente: str, destinazione: str):
    """
    Organizza i file dalla directory sorgente nella destinazione,
    creando sottocartelle per categoria e data.
    """
    sorgente_path = Path(sorgente)
    destinazione_path = Path(destinazione)

    for file in sorgente_path.iterdir():
        if not file.is_file():
            continue

        categoria = determina_categoria(file.suffix)
        data_modifica = datetime.fromtimestamp(file.stat().st_mtime)
        sottocartella_data = data_modifica.strftime('%Y/%Y-%m')

        percorso_finale = destinazione_path / categoria / sottocartella_data
        percorso_finale.mkdir(parents=True, exist_ok=True)

        destinazione_file = percorso_finale / file.name
        if destinazione_file.exists():
            # Gestione conflitto nomi: aggiunge timestamp
            stem = file.stem
            suffisso = file.suffix
            timestamp = data_modifica.strftime('%H%M%S')
            destinazione_file = percorso_finale / f"{stem}_{timestamp}{suffisso}"

        shutil.move(str(file), str(destinazione_file))
        print(f"Spostato: {file.name} -> {percorso_finale}")
```

**Convenzioni di denominazione automatiche**

Le naming conventions garantiscono uniformita e facilitano la ricerca. Un sistema automatico puo rinominare i file secondo uno schema predefinito:

```python
import re
from datetime import datetime

def normalizza_nome_file(nome: str, prefisso_progetto: str = '') -> str:
    """
    Normalizza il nome di un file secondo le convenzioni aziendali.
    Formato: [PROGETTO]_YYYYMMDD_nome-normalizzato.ext
    """
    path = Path(nome)
    stem = path.stem
    ext = path.suffix.lower()

    # Rimuovi caratteri speciali, sostituisci spazi con trattini
    normalizzato = re.sub(r'[^\w\s-]', '', stem)
    normalizzato = re.sub(r'\s+', '-', normalizzato.strip())
    normalizzato = normalizzato.lower()

    data = datetime.now().strftime('%Y%m%d')

    if prefisso_progetto:
        return f"{prefisso_progetto}_{data}_{normalizzato}{ext}"
    return f"{data}_{normalizzato}{ext}"
```

**Monitoraggio basato su watchdog**

La libreria `watchdog` permette di reagire in tempo reale alle modifiche nel filesystem. Questo e il meccanismo ideale per implementare un'organizzazione automatica continua:

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class GestoreNuoviFile(FileSystemEventHandler):
    """Gestisce automaticamente i nuovi file creati in una directory."""

    def __init__(self, directory_destinazione: str):
        self.destinazione = Path(directory_destinazione)

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        # Attendi che il file sia completamente scritto
        time.sleep(1)

        if file_path.exists():
            categoria = determina_categoria(file_path.suffix)
            target = self.destinazione / categoria
            target.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file_path), str(target / file_path.name))
            print(f"[AUTO] {file_path.name} -> {categoria}/")

def avvia_monitoraggio(directory_osservata: str, directory_destinazione: str):
    """Avvia il monitoraggio continuo di una directory."""
    handler = GestoreNuoviFile(directory_destinazione)
    observer = Observer()
    observer.schedule(handler, directory_osservata, recursive=False)
    observer.start()
    print(f"Monitoraggio attivo su: {directory_osservata}")

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

Questo script puo essere eseguito come servizio systemd su Linux o come servizio Windows, garantendo il funzionamento continuo dell'organizzazione automatica.

### Conversione Formato

La conversione automatica dei formati e essenziale in contesti dove i documenti devono essere distribuiti in formati specifici o dove diversi sistemi richiedono input in formati differenti.

**Generazione PDF con ReportLab e WeasyPrint**

ReportLab offre un controllo granulare sulla generazione PDF programmatica, mentre WeasyPrint converte HTML/CSS in PDF con un approccio piu dichiarativo:

```python
# Generazione PDF con ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet

def genera_report_pdf(dati: dict, percorso_output: str):
    """Genera un report PDF strutturato a partire da un dizionario di dati."""
    doc = SimpleDocTemplate(percorso_output, pagesize=A4,
                           topMargin=2*cm, bottomMargin=2*cm)
    stili = getSampleStyleSheet()
    elementi = []

    # Titolo
    elementi.append(Paragraph(dati['titolo'], stili['Title']))
    elementi.append(Spacer(1, 12))

    # Data generazione
    data_gen = datetime.now().strftime('%d/%m/%Y %H:%M')
    elementi.append(Paragraph(f"Generato il: {data_gen}", stili['Normal']))
    elementi.append(Spacer(1, 24))

    # Tabella dati
    if 'tabella' in dati:
        tabella = Table(dati['tabella'])
        elementi.append(tabella)

    doc.build(elementi)
    print(f"PDF generato: {percorso_output}")

# Generazione PDF da HTML con WeasyPrint
from weasyprint import HTML

def html_a_pdf(contenuto_html: str, percorso_output: str):
    """Converte contenuto HTML in PDF mantenendo gli stili CSS."""
    HTML(string=contenuto_html).write_pdf(percorso_output)
```

**Elaborazione immagini con Pillow**

L'automazione del trattamento immagini copre ridimensionamento, conversione formato, applicazione watermark e ottimizzazione:

```python
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def elabora_batch_immagini(directory_input: str, directory_output: str,
                           dimensione_max: tuple = (1920, 1080),
                           formato_output: str = 'JPEG',
                           qualita: int = 85):
    """Elabora un batch di immagini: ridimensiona, converte e ottimizza."""
    input_path = Path(directory_input)
    output_path = Path(directory_output)
    output_path.mkdir(parents=True, exist_ok=True)

    formati_supportati = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}

    for file_img in input_path.iterdir():
        if file_img.suffix.lower() not in formati_supportati:
            continue

        with Image.open(file_img) as img:
            # Ridimensionamento mantenendo le proporzioni
            img.thumbnail(dimensione_max, Image.Resampling.LANCZOS)

            # Conversione in RGB se necessario (per JPEG)
            if formato_output == 'JPEG' and img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            nome_output = file_img.stem + '.' + formato_output.lower()
            percorso_finale = output_path / nome_output
            img.save(percorso_finale, formato_output, quality=qualita, optimize=True)
            print(f"Elaborata: {file_img.name} -> {nome_output}")
```

**Conversione documenti con pandoc e python-docx**

Per conversioni tra formati documentali complessi, pandoc e lo strumento di riferimento. L'integrazione con Python avviene tramite subprocess o la libreria `pypandoc`:

```python
import pypandoc
from docx import Document

def converti_markdown_a_docx(file_md: str, file_output: str):
    """Converte un file Markdown in documento Word."""
    pypandoc.convert_file(file_md, 'docx', outputfile=file_output)

def converti_docx_a_pdf(file_docx: str, file_pdf: str):
    """Converte un documento Word in PDF tramite pandoc."""
    pypandoc.convert_file(file_docx, 'pdf', outputfile=file_pdf,
                          extra_args=['--pdf-engine=xelatex'])

def crea_documento_da_template(template_path: str, dati: dict, output_path: str):
    """Genera un documento Word personalizzato da un template."""
    doc = Document(template_path)
    for paragrafo in doc.paragraphs:
        for chiave, valore in dati.items():
            placeholder = f'{{{{{chiave}}}}}'
            if placeholder in paragrafo.text:
                paragrafo.text = paragrafo.text.replace(placeholder, str(valore))
    doc.save(output_path)
```

**Pipeline di elaborazione batch**

Una pipeline di conversione batch orchestra piu operazioni in sequenza, gestendo errori e producendo un report finale:

```python
from dataclasses import dataclass, field
from typing import Callable
import traceback

@dataclass
class RisultatoElaborazione:
    file: str
    successo: bool
    errore: str = ''

@dataclass
class PipelineConversione:
    """Pipeline per l'elaborazione batch di documenti."""
    passaggi: list[Callable] = field(default_factory=list)
    risultati: list[RisultatoElaborazione] = field(default_factory=list)

    def aggiungi_passaggio(self, funzione: Callable):
        self.passaggi.append(funzione)
        return self

    def esegui(self, file_input: list[str]):
        for file in file_input:
            try:
                dato = file
                for passaggio in self.passaggi:
                    dato = passaggio(dato)
                self.risultati.append(RisultatoElaborazione(file, True))
            except Exception as e:
                self.risultati.append(
                    RisultatoElaborazione(file, False, traceback.format_exc())
                )

    def report(self) -> str:
        successi = sum(1 for r in self.risultati if r.successo)
        fallimenti = len(self.risultati) - successi
        return f"Completati: {successi}, Falliti: {fallimenti}"
```

### Backup e Sincronizzazione

I backup automatizzati sono una componente critica di qualsiasi infrastruttura IT. L'automazione garantisce che i backup vengano eseguiti regolarmente, verificati e ruotati secondo politiche definite.

**Automazione rsync**

`rsync` e lo strumento standard per la sincronizzazione efficiente di file su sistemi Unix/Linux. Trasferisce solo le differenze, riducendo drasticamente il tempo e la banda necessari:

```bash
#!/bin/bash
# backup_incrementale.sh — Backup incrementale con rsync e hard link

SORGENTE="/dati/produzione/"
DESTINAZIONE="/backup/incrementale"
DATA=$(date +%Y-%m-%d_%H%M%S)
ULTIMO_BACKUP=$(ls -td ${DESTINAZIONE}/backup-* 2>/dev/null | head -1)
BACKUP_CORRENTE="${DESTINAZIONE}/backup-${DATA}"
LOG="/var/log/backup/backup_${DATA}.log"

mkdir -p "$(dirname "$LOG")"

echo "=== Backup iniziato: $(date) ===" | tee "$LOG"

if [ -n "$ULTIMO_BACKUP" ]; then
    # Backup incrementale con hard link al precedente
    rsync -avz --delete \
        --link-dest="$ULTIMO_BACKUP" \
        --exclude='*.tmp' \
        --exclude='.cache/' \
        --log-file="$LOG" \
        "$SORGENTE" "$BACKUP_CORRENTE"
else
    # Primo backup completo
    rsync -avz --delete \
        --exclude='*.tmp' \
        --exclude='.cache/' \
        --log-file="$LOG" \
        "$SORGENTE" "$BACKUP_CORRENTE"
fi

ESITO=$?
if [ $ESITO -eq 0 ]; then
    echo "=== Backup completato con successo: $(date) ===" | tee -a "$LOG"
else
    echo "=== ERRORE nel backup (codice: $ESITO): $(date) ===" | tee -a "$LOG"
fi
```

**rclone per la sincronizzazione cloud**

`rclone` estende il concetto di rsync al cloud, supportando decine di provider tra cui Amazon S3, Azure Blob Storage, Google Drive, Dropbox e molti altri:

```python
import subprocess
import json
from datetime import datetime

class GestoreBackupCloud:
    """Gestisce backup automatizzati verso storage cloud tramite rclone."""

    def __init__(self, remote_name: str, bucket: str):
        self.remote = remote_name
        self.bucket = bucket

    def sincronizza(self, directory_locale: str, prefisso_remoto: str = ''):
        """Sincronizza una directory locale verso lo storage cloud."""
        destinazione = f"{self.remote}:{self.bucket}/{prefisso_remoto}"
        cmd = [
            'rclone', 'sync',
            directory_locale, destinazione,
            '--progress',
            '--transfers', '8',
            '--checkers', '16',
            '--log-level', 'INFO',
            '--stats', '30s',
            '--exclude', '*.tmp',
            '--exclude', '.DS_Store',
        ]
        risultato = subprocess.run(cmd, capture_output=True, text=True)
        return risultato.returncode == 0

    def verifica_integrita(self, directory_locale: str, prefisso_remoto: str = ''):
        """Verifica l'integrita del backup confrontando hash locali e remoti."""
        destinazione = f"{self.remote}:{self.bucket}/{prefisso_remoto}"
        cmd = ['rclone', 'check', directory_locale, destinazione, '--one-way']
        risultato = subprocess.run(cmd, capture_output=True, text=True)
        return risultato.returncode == 0

    def lista_backup(self, prefisso: str = '') -> list[dict]:
        """Elenca i backup presenti nello storage remoto."""
        percorso = f"{self.remote}:{self.bucket}/{prefisso}"
        cmd = ['rclone', 'lsjson', percorso, '--dirs-only']
        risultato = subprocess.run(cmd, capture_output=True, text=True)
        if risultato.returncode == 0:
            return json.loads(risultato.stdout)
        return []
```

**Automazione delle politiche di retention**

Le politiche di retention definiscono per quanto tempo i backup vengono conservati. Uno script di retention automatico applica regole come "mantieni gli ultimi 7 giornalieri, 4 settimanali e 12 mensili":

```python
from pathlib import Path
from datetime import datetime, timedelta
import shutil

def applica_retention(directory_backup: str,
                      giornalieri: int = 7,
                      settimanali: int = 4,
                      mensili: int = 12):
    """
    Applica la politica di retention ai backup.
    Mantiene i backup piu recenti secondo le soglie configurate.
    """
    backup_path = Path(directory_backup)
    oggi = datetime.now()

    backup_list = []
    for d in sorted(backup_path.iterdir(), reverse=True):
        if d.is_dir() and d.name.startswith('backup-'):
            try:
                data_str = d.name.replace('backup-', '').split('_')[0]
                data_backup = datetime.strptime(data_str, '%Y-%m-%d')
                backup_list.append((d, data_backup))
            except ValueError:
                continue

    da_mantenere = set()
    contatori = {'giornaliero': 0, 'settimanale': 0, 'mensile': 0}

    for percorso, data in backup_list:
        eta = (oggi - data).days
        mantenere = False

        if eta <= giornalieri:
            mantenere = True
            contatori['giornaliero'] += 1
        elif eta <= settimanali * 7 and contatori['settimanale'] < settimanali:
            if data.weekday() == 6:  # Domenica
                mantenere = True
                contatori['settimanale'] += 1
        elif contatori['mensile'] < mensili:
            if data.day == 1:  # Primo del mese
                mantenere = True
                contatori['mensile'] += 1

        if mantenere:
            da_mantenere.add(percorso)

    for percorso, data in backup_list:
        if percorso not in da_mantenere:
            print(f"Eliminazione backup obsoleto: {percorso.name}")
            shutil.rmtree(percorso)
```

### Archiviazione

L'archiviazione automatica gestisce il ciclo di vita dei file, spostando i dati meno recenti verso storage piu economici e mantenendo puliti i sistemi di produzione.

**Regole di archiviazione basate sull'eta**

```python
from pathlib import Path
from datetime import datetime, timedelta
import tarfile
import os

def archivia_per_eta(directory: str, archivio_dest: str,
                     giorni_soglia: int = 90,
                     comprimi: bool = True):
    """
    Archivia i file piu vecchi della soglia specificata.
    Crea un archivio compresso e rimuove gli originali.
    """
    dir_path = Path(directory)
    archivio_path = Path(archivio_dest)
    archivio_path.mkdir(parents=True, exist_ok=True)

    soglia = datetime.now() - timedelta(days=giorni_soglia)
    file_da_archiviare = []

    for file in dir_path.rglob('*'):
        if file.is_file():
            data_modifica = datetime.fromtimestamp(file.stat().st_mtime)
            if data_modifica < soglia:
                file_da_archiviare.append(file)

    if not file_da_archiviare:
        print("Nessun file da archiviare.")
        return

    # Crea archivio tar.gz
    data_archivio = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome_archivio = f"archivio_{data_archivio}.tar.gz" if comprimi else f"archivio_{data_archivio}.tar"
    modalita = 'w:gz' if comprimi else 'w'
    percorso_archivio = archivio_path / nome_archivio

    with tarfile.open(percorso_archivio, modalita) as tar:
        for file in file_da_archiviare:
            percorso_relativo = file.relative_to(dir_path)
            tar.add(file, arcname=str(percorso_relativo))
            print(f"Archiviato: {percorso_relativo}")

    # Rimuovi i file originali dopo l'archiviazione riuscita
    for file in file_da_archiviare:
        file.unlink()
        # Rimuovi directory vuote
        try:
            file.parent.rmdir()
        except OSError:
            pass  # Directory non vuota, ignorare

    print(f"Archiviazione completata: {len(file_da_archiviare)} file -> {nome_archivio}")
```

**Migrazione verso cold storage**

Per grandi volumi di dati archiviati, la migrazione verso classi di storage economiche (come S3 Glacier o Azure Archive) riduce significativamente i costi:

```python
def migra_a_cold_storage(archivio_locale: str, remote: str,
                         bucket: str, classe_storage: str = 'GLACIER'):
    """Migra archivi compressi verso cold storage cloud."""
    cmd = [
        'rclone', 'move',
        archivio_locale,
        f"{remote}:{bucket}/cold-archive/",
        '--s3-storage-class', classe_storage,
        '--transfers', '4',
        '--log-level', 'INFO',
    ]
    risultato = subprocess.run(cmd, capture_output=True, text=True)
    if risultato.returncode == 0:
        print(f"Migrazione completata verso {classe_storage}")
    else:
        print(f"Errore migrazione: {risultato.stderr}")
```

**Script di pulizia programmata**

Uno script di pulizia rimuove file temporanei, cache scadute e artefatti di build che consumano spazio inutilmente:

```python
def pulizia_programmata(directory: str, regole: list[dict]):
    """
    Esegue la pulizia secondo regole configurabili.
    Ogni regola specifica un pattern glob e un'eta massima in giorni.
    Esempio regola: {'pattern': '*.tmp', 'max_giorni': 7}
    """
    dir_path = Path(directory)
    file_rimossi = 0
    spazio_liberato = 0

    for regola in regole:
        pattern = regola['pattern']
        max_giorni = regola.get('max_giorni', 30)
        soglia = datetime.now() - timedelta(days=max_giorni)

        for file in dir_path.rglob(pattern):
            if file.is_file():
                data_modifica = datetime.fromtimestamp(file.stat().st_mtime)
                if data_modifica < soglia:
                    dimensione = file.stat().st_size
                    file.unlink()
                    file_rimossi += 1
                    spazio_liberato += dimensione

    spazio_mb = spazio_liberato / (1024 * 1024)
    print(f"Pulizia completata: {file_rimossi} file rimossi, {spazio_mb:.2f} MB liberati")
```

---

## Automazione IT Operations

L'automazione delle operazioni IT e probabilmente il dominio dove l'impatto e piu immediato e misurabile. Le attivita ripetitive dell'IT Operations — creazione utenti, gestione patch, monitoring — sono candidate ideali per l'automazione.

### User Provisioning/Deprovisioning

Il provisioning automatizzato degli utenti garantisce che ogni nuovo collaboratore riceva tutte le risorse necessarie in modo rapido, coerente e documentato. Il deprovisioning, altrettanto importante, assicura che gli accessi vengano revocati puntualmente alla cessazione del rapporto lavorativo.

**Creazione utenti Active Directory con PowerShell**

```powershell
# Funzione per il provisioning completo di un nuovo utente AD
function New-UserProvisioning {
    param(
        [Parameter(Mandatory)]
        [string]$Nome,
        [Parameter(Mandatory)]
        [string]$Cognome,
        [Parameter(Mandatory)]
        [string]$Dipartimento,
        [Parameter(Mandatory)]
        [string]$Ruolo,
        [string]$Manager
    )

    $Username = "$($Nome.Substring(0,1).ToLower()).$($Cognome.ToLower())"
    $Email = "$Username@azienda.com"
    $OU = "OU=$Dipartimento,OU=Utenti,DC=azienda,DC=local"
    $Password = New-RandomPassword -Length 16

    # 1. Creazione account AD
    New-ADUser -Name "$Nome $Cognome" `
        -GivenName $Nome `
        -Surname $Cognome `
        -SamAccountName $Username `
        -UserPrincipalName $Email `
        -Path $OU `
        -AccountPassword (ConvertTo-SecureString $Password -AsPlainText -Force) `
        -ChangePasswordAtLogon $true `
        -Enabled $true `
        -Department $Dipartimento `
        -Title $Ruolo `
        -Manager $Manager

    # 2. Aggiunta ai gruppi di sicurezza
    $GruppiDipartimento = Get-DepartmentGroups -Department $Dipartimento
    foreach ($Gruppo in $GruppiDipartimento) {
        Add-ADGroupMember -Identity $Gruppo -Members $Username
    }

    # 3. Creazione home directory
    $HomeDir = "\\fileserver\home\$Username"
    New-Item -Path $HomeDir -ItemType Directory -Force
    $Acl = Get-Acl $HomeDir
    $Rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        "$Username", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
    )
    $Acl.SetAccessRule($Rule)
    Set-Acl -Path $HomeDir -AclObject $Acl

    Write-Output "Provisioning completato per $Nome $Cognome ($Username)"
    return @{
        Username = $Username
        Email = $Email
        Password = $Password
    }
}
```

**Assegnazione licenze Microsoft 365**

```powershell
function Set-M365Licensing {
    param(
        [Parameter(Mandatory)]
        [string]$UserPrincipalName,
        [string]$LicenseSKU = "azienda:ENTERPRISEPACK"
    )

    Connect-MgGraph -Scopes "User.ReadWrite.All"

    $User = Get-MgUser -UserId $UserPrincipalName
    $License = New-Object -TypeName Microsoft.Graph.PowerShell.Models.MicrosoftGraphAssignedLicense
    $License.SkuId = (Get-MgSubscribedSku | Where-Object {$_.SkuPartNumber -eq $LicenseSKU.Split(':')[1]}).SkuId

    Set-MgUserLicense -UserId $User.Id -AddLicenses @($License) -RemoveLicenses @()
    Write-Output "Licenza $LicenseSKU assegnata a $UserPrincipalName"
}
```

**Workflow di onboarding completo con n8n**

Un workflow di onboarding completo orchestrato da n8n o da uno script Python coordina tutte le operazioni necessarie:

```python
import requests
from dataclasses import dataclass

@dataclass
class NuovoDipendente:
    nome: str
    cognome: str
    email: str
    dipartimento: str
    ruolo: str
    data_inizio: str
    manager_email: str

class WorkflowOnboarding:
    """Orchestratore del processo di onboarding automatizzato."""

    def __init__(self, config: dict):
        self.config = config
        self.log = []

    def esegui(self, dipendente: NuovoDipendente) -> dict:
        risultati = {}

        # Fase 1: Creazione account
        risultati['account_ad'] = self._crea_account_ad(dipendente)
        self.log.append(f"Account AD creato: {dipendente.email}")

        # Fase 2: Assegnazione licenze
        risultati['licenze_m365'] = self._assegna_licenze(dipendente)
        self.log.append("Licenze M365 assegnate")

        # Fase 3: Configurazione email
        risultati['email'] = self._configura_email(dipendente)
        self.log.append("Casella email configurata")

        # Fase 4: Aggiunta a gruppi e canali
        risultati['gruppi'] = self._aggiungi_a_gruppi(dipendente)
        self.log.append("Aggiunto a gruppi di lavoro")

        # Fase 5: Notifica al manager e al team
        self._notifica_team(dipendente)
        self.log.append("Notifiche inviate")

        # Fase 6: Invio credenziali iniziali
        self._invia_credenziali(dipendente, risultati)
        self.log.append("Credenziali inviate in modo sicuro")

        return risultati

    def _crea_account_ad(self, d: NuovoDipendente) -> dict:
        """Chiama l'API di provisioning AD (potrebbe essere un webhook o API REST)."""
        # Implementazione specifica dell'ambiente
        pass

    def _assegna_licenze(self, d: NuovoDipendente) -> dict:
        """Assegna le licenze software necessarie per il ruolo."""
        pass

    def _configura_email(self, d: NuovoDipendente) -> dict:
        """Configura la casella email con firma, regole e deleghe."""
        pass

    def _aggiungi_a_gruppi(self, d: NuovoDipendente) -> list:
        """Aggiunge l'utente ai gruppi di sicurezza e distribuzione."""
        pass

    def _notifica_team(self, d: NuovoDipendente):
        """Invia notifiche su Slack/Teams al team e al manager."""
        pass

    def _invia_credenziali(self, d: NuovoDipendente, risultati: dict):
        """Invia le credenziali iniziali tramite canale sicuro."""
        pass
```

**Workflow di offboarding**

Il deprovisioning e altrettanto critico per la sicurezza. Un workflow di offboarding automatizzato deve disabilitare tutti gli accessi, archiviare i dati e notificare i responsabili, il tutto in modo tracciabile e conforme alle normative.

### Patch Management Automation

La gestione automatizzata delle patch e fondamentale per mantenere i sistemi sicuri e conformi. L'automazione riduce il tempo di esposizione alle vulnerabilita e garantisce l'applicazione coerente degli aggiornamenti.

**Automazione WSUS con PowerShell**

```powershell
# Approvazione automatica delle patch critiche
function Approve-CriticalUpdates {
    $WsusServer = Get-WsusServer -Name "wsus.azienda.local" -PortNumber 8530
    $Updates = Get-WsusUpdate -UpdateServer $WsusServer -Approval Unapproved |
        Where-Object {
            $_.Update.MsrcSeverity -eq 'Critical' -or
            $_.Update.MsrcSeverity -eq 'Important'
        }

    $TargetGroup = $WsusServer.GetComputerTargetGroups() |
        Where-Object {$_.Name -eq 'Server-Produzione'}

    foreach ($Update in $Updates) {
        Approve-WsusUpdate -Update $Update -Action Install -TargetGroupName $TargetGroup.Name
        Write-Output "Approvata: $($Update.Update.Title)"
    }
}
```

**Patching Linux con Ansible**

Ansible e lo strumento ideale per gestire il patching su larga scala in ambienti Linux:

```yaml
# playbook: patch_management.yml
---
- name: Patch Management Automatizzato
  hosts: server_produzione
  become: yes
  serial: "25%"   # Aggiorna il 25% dei server alla volta
  max_fail_percentage: 10

  pre_tasks:
    - name: Verifica stato servizi prima del patching
      service_facts:

    - name: Crea snapshot pre-patching (se VM)
      command: "virsh snapshot-create-as {{ inventory_hostname }} pre-patch-{{ ansible_date_time.date }}"
      delegate_to: hypervisor
      ignore_errors: yes

  tasks:
    - name: Aggiorna cache repository
      apt:
        update_cache: yes
        cache_valid_time: 3600
      when: ansible_os_family == "Debian"

    - name: Applica aggiornamenti di sicurezza
      apt:
        upgrade: safe
        default_release: "{{ ansible_distribution_release }}-security"
      when: ansible_os_family == "Debian"
      register: risultato_patch

    - name: Verifica se riavvio necessario
      stat:
        path: /var/run/reboot-required
      register: riavvio_necessario

    - name: Riavvio controllato se necessario
      reboot:
        reboot_timeout: 300
        msg: "Riavvio per applicazione patch di sicurezza"
      when: riavvio_necessario.stat.exists

  post_tasks:
    - name: Verifica stato servizi dopo il patching
      service_facts:

    - name: Verifica che i servizi critici siano attivi
      assert:
        that:
          - ansible_facts.services['nginx.service'].state == 'running'
          - ansible_facts.services['postgresql.service'].state == 'running'
        fail_msg: "Servizi critici non attivi dopo il patching!"
```

**Automazione rollback**

Un meccanismo di rollback automatico e essenziale per gestire i casi in cui un aggiornamento causa problemi:

```bash
#!/bin/bash
# rollback_patch.sh — Rollback automatico se i servizi non rispondono

SERVIZI_CRITICI=("nginx" "postgresql" "redis-server")
SNAPSHOT_NAME="pre-patch-$(date +%Y-%m-%d)"
TIMEOUT_VERIFICA=60

verifica_servizi() {
    for servizio in "${SERVIZI_CRITICI[@]}"; do
        if ! systemctl is-active --quiet "$servizio"; then
            echo "ERRORE: $servizio non attivo!"
            return 1
        fi
    done
    return 0
}

echo "Verifica servizi post-patching..."
sleep $TIMEOUT_VERIFICA

if ! verifica_servizi; then
    echo "ROLLBACK: Ripristino snapshot $SNAPSHOT_NAME"
    # Il meccanismo specifico dipende dall'infrastruttura
    # Esempio per VM: virsh snapshot-revert $HOSTNAME $SNAPSHOT_NAME
    # Esempio per apt: apt-get install --reinstall pacchetto=versione_precedente
    exit 1
fi

echo "Verifica completata: tutti i servizi operativi."
```

### Monitoring e Alerting

Il monitoring automatizzato e il sistema nervoso dell'infrastruttura IT. Un buon sistema di monitoring non solo rileva i problemi, ma in molti casi li risolve autonomamente.

**Health check automatizzati**

```python
import requests
import psutil
import socket
from dataclasses import dataclass

@dataclass
class RisultatoCheck:
    nome: str
    stato: str   # 'ok', 'warning', 'critical'
    messaggio: str
    valore: float = 0.0

class HealthChecker:
    """Sistema di health check automatizzato per servizi e risorse."""

    def __init__(self):
        self.checks = []
        self.risultati = []

    def check_http(self, url: str, timeout: int = 10) -> RisultatoCheck:
        """Verifica la disponibilita di un endpoint HTTP."""
        try:
            risposta = requests.get(url, timeout=timeout)
            if risposta.status_code == 200:
                return RisultatoCheck('HTTP', 'ok', f'{url} risponde', risposta.elapsed.total_seconds())
            return RisultatoCheck('HTTP', 'warning', f'{url} risponde con {risposta.status_code}')
        except requests.exceptions.RequestException as e:
            return RisultatoCheck('HTTP', 'critical', f'{url} non raggiungibile: {e}')

    def check_disco(self, soglia_warning: int = 80, soglia_critical: int = 90) -> RisultatoCheck:
        """Verifica lo spazio disco disponibile."""
        uso = psutil.disk_usage('/')
        percentuale = uso.percent
        if percentuale >= soglia_critical:
            return RisultatoCheck('Disco', 'critical', f'Uso disco: {percentuale}%', percentuale)
        elif percentuale >= soglia_warning:
            return RisultatoCheck('Disco', 'warning', f'Uso disco: {percentuale}%', percentuale)
        return RisultatoCheck('Disco', 'ok', f'Uso disco: {percentuale}%', percentuale)

    def check_memoria(self, soglia_warning: int = 80, soglia_critical: int = 95) -> RisultatoCheck:
        """Verifica l'utilizzo della memoria RAM."""
        mem = psutil.virtual_memory()
        if mem.percent >= soglia_critical:
            return RisultatoCheck('Memoria', 'critical', f'Uso RAM: {mem.percent}%', mem.percent)
        elif mem.percent >= soglia_warning:
            return RisultatoCheck('Memoria', 'warning', f'Uso RAM: {mem.percent}%', mem.percent)
        return RisultatoCheck('Memoria', 'ok', f'Uso RAM: {mem.percent}%', mem.percent)

    def check_porta(self, host: str, porta: int, timeout: int = 5) -> RisultatoCheck:
        """Verifica che una porta TCP sia raggiungibile."""
        try:
            sock = socket.create_connection((host, porta), timeout=timeout)
            sock.close()
            return RisultatoCheck('Porta', 'ok', f'{host}:{porta} raggiungibile')
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            return RisultatoCheck('Porta', 'critical', f'{host}:{porta} non raggiungibile: {e}')

    def esegui_tutti(self) -> list[RisultatoCheck]:
        """Esegue tutti i check registrati e restituisce i risultati."""
        self.risultati = []
        for check_fn in self.checks:
            self.risultati.append(check_fn())
        return self.risultati
```

**Routing degli alert e escalation**

Un sistema di alerting maturo instrada le notifiche verso i canali appropriati in base alla severita:

```python
class GestoreAlert:
    """Instrada gli alert verso i canali appropriati in base alla severita."""

    def __init__(self, config: dict):
        self.config = config

    def invia_alert(self, risultato: RisultatoCheck):
        if risultato.stato == 'critical':
            self._notifica_slack(risultato, canale='#incidenti-critici')
            self._notifica_pagerduty(risultato)
            self._invia_email(risultato, destinatari=self.config['team_ops'])
        elif risultato.stato == 'warning':
            self._notifica_slack(risultato, canale='#monitoring')
            self._invia_email(risultato, destinatari=self.config['team_ops'])

    def _notifica_slack(self, risultato: RisultatoCheck, canale: str):
        colore = '#ff0000' if risultato.stato == 'critical' else '#ffaa00'
        payload = {
            'channel': canale,
            'attachments': [{
                'color': colore,
                'title': f"Alert {risultato.stato.upper()}: {risultato.nome}",
                'text': risultato.messaggio,
                'ts': int(datetime.now().timestamp())
            }]
        }
        requests.post(self.config['slack_webhook'], json=payload)

    def _notifica_pagerduty(self, risultato: RisultatoCheck):
        payload = {
            'routing_key': self.config['pagerduty_key'],
            'event_action': 'trigger',
            'payload': {
                'summary': f"{risultato.nome}: {risultato.messaggio}",
                'severity': 'critical',
                'source': socket.gethostname(),
            }
        }
        requests.post('https://events.pagerduty.com/v2/enqueue', json=payload)

    def _invia_email(self, risultato: RisultatoCheck, destinatari: list[str]):
        # Implementazione con smtplib
        pass
```

**Script di auto-remediation (self-healing)**

Gli script di auto-remediation risolvono automaticamente problemi comuni senza intervento umano:

```python
import subprocess
import os

class AutoRemediation:
    """Script di auto-remediation per problemi comuni."""

    def riavvia_servizio(self, nome_servizio: str) -> bool:
        """Riavvia un servizio che non risponde."""
        risultato = subprocess.run(
            ['systemctl', 'restart', nome_servizio],
            capture_output=True, text=True
        )
        return risultato.returncode == 0

    def libera_spazio_disco(self, soglia_mb: int = 1000):
        """Libera spazio disco rimuovendo file temporanei e log vecchi."""
        percorsi_pulizia = [
            '/tmp/*',
            '/var/log/*.gz',
            '/var/log/*.old',
            '/var/cache/apt/archives/*.deb',
        ]
        for percorso in percorsi_pulizia:
            subprocess.run(['bash', '-c', f'rm -f {percorso}'], capture_output=True)

        # Ruota i log di grandi dimensioni
        subprocess.run(['logrotate', '-f', '/etc/logrotate.conf'], capture_output=True)

    def termina_processi_zombie(self):
        """Identifica e gestisce i processi zombie."""
        for proc in psutil.process_iter(['pid', 'status', 'name']):
            if proc.info['status'] == psutil.STATUS_ZOMBIE:
                try:
                    parent = psutil.Process(proc.info['pid']).parent()
                    if parent:
                        os.kill(parent.pid, 9)
                except (psutil.NoSuchProcess, ProcessLookupError):
                    pass
```

### Report Generation

La generazione automatica di report trasforma dati grezzi in documenti utili e distribuibili, eliminando ore di lavoro manuale ripetitivo.

```python
import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, Alignment, PatternFill

class GeneratoreReport:
    """Genera report Excel automatizzati con grafici e formattazione."""

    def __init__(self, titolo: str):
        self.wb = openpyxl.Workbook()
        self.ws = self.wb.active
        self.ws.title = titolo
        self.riga_corrente = 1

    def aggiungi_intestazione(self, colonne: list[str]):
        """Aggiunge una riga di intestazione formattata."""
        font_intestazione = Font(bold=True, color='FFFFFF', size=11)
        sfondo = PatternFill(start_color='2F5496', end_color='2F5496', fill_type='solid')

        for col, testo in enumerate(colonne, 1):
            cella = self.ws.cell(row=self.riga_corrente, column=col, value=testo)
            cella.font = font_intestazione
            cella.fill = sfondo
            cella.alignment = Alignment(horizontal='center')

        self.riga_corrente += 1

    def aggiungi_dati(self, righe: list[list]):
        """Aggiunge righe di dati al report."""
        for riga in righe:
            for col, valore in enumerate(riga, 1):
                self.ws.cell(row=self.riga_corrente, column=col, value=valore)
            self.riga_corrente += 1

    def aggiungi_grafico_barre(self, titolo: str, riga_inizio: int,
                                riga_fine: int, col_categorie: int,
                                col_valori: int):
        """Aggiunge un grafico a barre al foglio."""
        chart = BarChart()
        chart.title = titolo
        chart.style = 10

        dati = Reference(self.ws, min_col=col_valori,
                        min_row=riga_inizio, max_row=riga_fine)
        categorie = Reference(self.ws, min_col=col_categorie,
                             min_row=riga_inizio + 1, max_row=riga_fine)

        chart.add_data(dati, titles_from_data=True)
        chart.set_categories(categorie)
        self.ws.add_chart(chart, f"A{self.riga_corrente + 2}")

    def salva(self, percorso: str):
        """Salva il report su disco."""
        # Auto-dimensiona le colonne
        for col in self.ws.columns:
            max_length = max(len(str(cell.value or '')) for cell in col)
            self.ws.column_dimensions[col[0].column_letter].width = min(max_length + 4, 50)
        self.wb.save(percorso)
```

La distribuzione automatica dei report via email completa il ciclo:

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

def distribuisci_report(percorso_report: str, destinatari: list[str],
                       oggetto: str, corpo: str, config_smtp: dict):
    """Distribuisce un report via email come allegato."""
    msg = MIMEMultipart()
    msg['From'] = config_smtp['mittente']
    msg['To'] = ', '.join(destinatari)
    msg['Subject'] = oggetto

    msg.attach(MIMEText(corpo, 'html'))

    with open(percorso_report, 'rb') as f:
        allegato = MIMEBase('application', 'octet-stream')
        allegato.set_payload(f.read())
        encoders.encode_base64(allegato)
        nome_file = Path(percorso_report).name
        allegato.add_header('Content-Disposition', f'attachment; filename="{nome_file}"')
        msg.attach(allegato)

    with smtplib.SMTP(config_smtp['server'], config_smtp['porta']) as server:
        server.starttls()
        server.login(config_smtp['utente'], config_smtp['password'])
        server.send_message(msg)
```

---

## Automazione Comunicazione

L'automazione della comunicazione aziendale garantisce che le informazioni giuste raggiungano le persone giuste al momento giusto, senza intervento manuale e con piena tracciabilita.

### Email Automation

L'email rimane il canale di comunicazione piu utilizzato in ambito professionale. L'automazione email copre l'invio basato su template, l'elaborazione in massa e il parsing automatico dei messaggi in ingresso.

**Email basate su template**

```python
from jinja2 import Environment, FileSystemLoader
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

class MotoreEmailTemplate:
    """Sistema di invio email basato su template Jinja2."""

    def __init__(self, directory_template: str, config_smtp: dict):
        self.env = Environment(loader=FileSystemLoader(directory_template))
        self.config = config_smtp

    def invia(self, template_nome: str, destinatario: str,
              oggetto: str, dati: dict):
        """Compila un template e invia l'email."""
        template = self.env.get_template(template_nome)
        corpo_html = template.render(**dati)

        msg = MIMEMultipart('alternative')
        msg['From'] = self.config['mittente']
        msg['To'] = destinatario
        msg['Subject'] = oggetto
        msg.attach(MIMEText(corpo_html, 'html'))

        with smtplib.SMTP(self.config['server'], self.config['porta']) as server:
            server.starttls()
            server.login(self.config['utente'], self.config['password'])
            server.send_message(msg)

    def invio_massivo(self, template_nome: str, destinatari: list[dict],
                      oggetto: str, rate_limit: float = 1.0):
        """
        Invio massivo con rate limiting per evitare blocchi dal server.
        Ogni elemento di destinatari e un dict con 'email' e i dati del template.
        """
        import time
        for idx, dest in enumerate(destinatari):
            email = dest.pop('email')
            self.invia(template_nome, email, oggetto, dest)
            print(f"Inviata {idx + 1}/{len(destinatari)}: {email}")
            time.sleep(rate_limit)
```

**Parsing e elaborazione email in ingresso**

L'elaborazione automatica delle email in ingresso permette di estrarre informazioni, classificare richieste e attivare workflow:

```python
import imaplib
import email
from email.header import decode_header

class ElaboratoreEmail:
    """Legge e processa automaticamente le email in ingresso."""

    def __init__(self, server: str, utente: str, password: str):
        self.mail = imaplib.IMAP4_SSL(server)
        self.mail.login(utente, password)

    def leggi_non_lette(self, cartella: str = 'INBOX') -> list[dict]:
        """Recupera tutte le email non lette dalla cartella specificata."""
        self.mail.select(cartella)
        _, numeri_messaggi = self.mail.search(None, 'UNSEEN')
        messaggi = []

        for num in numeri_messaggi[0].split():
            _, dati = self.mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(dati[0][1])

            oggetto = decode_header(msg['Subject'])[0][0]
            if isinstance(oggetto, bytes):
                oggetto = oggetto.decode()

            corpo = ''
            if msg.is_multipart():
                for parte in msg.walk():
                    if parte.get_content_type() == 'text/plain':
                        corpo = parte.get_payload(decode=True).decode()
                        break
            else:
                corpo = msg.get_payload(decode=True).decode()

            messaggi.append({
                'da': msg['From'],
                'oggetto': oggetto,
                'corpo': corpo,
                'data': msg['Date'],
                'id': num,
            })

        return messaggi

    def chiudi(self):
        self.mail.close()
        self.mail.logout()
```

### Notifiche Multi-Canale

Le notifiche multi-canale assicurano che gli alert e le comunicazioni raggiungano i destinatari attraverso il canale piu appropriato alla situazione.

**Notifiche Slack tramite webhook e bot**

```python
import requests
import json

class NotificatoreSlack:
    """Gestisce le notifiche verso Slack tramite webhook e Bot API."""

    def __init__(self, webhook_url: str = None, bot_token: str = None):
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.api_base = 'https://slack.com/api'

    def invia_webhook(self, messaggio: str, canale: str = None,
                      blocchi: list = None):
        """Invia un messaggio tramite Incoming Webhook."""
        payload = {'text': messaggio}
        if canale:
            payload['channel'] = canale
        if blocchi:
            payload['blocks'] = blocchi
        risposta = requests.post(self.webhook_url, json=payload)
        return risposta.status_code == 200

    def invia_messaggio_bot(self, canale: str, messaggio: str,
                            blocchi: list = None):
        """Invia un messaggio tramite Bot Token (piu flessibile)."""
        headers = {
            'Authorization': f'Bearer {self.bot_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'channel': canale,
            'text': messaggio,
        }
        if blocchi:
            payload['blocks'] = blocchi

        risposta = requests.post(
            f'{self.api_base}/chat.postMessage',
            headers=headers, json=payload
        )
        return risposta.json().get('ok', False)

    def invia_alert_formattato(self, canale: str, titolo: str,
                                messaggio: str, severita: str = 'info'):
        """Invia un alert formattato con Block Kit."""
        colori = {
            'info': '#36a64f',
            'warning': '#ffcc00',
            'critical': '#ff0000'
        }
        emoji = {
            'info': ':information_source:',
            'warning': ':warning:',
            'critical': ':rotating_light:'
        }
        blocchi = [
            {
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': f"{emoji.get(severita, '')} {titolo}"
                }
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': messaggio
                }
            },
            {
                'type': 'context',
                'elements': [{
                    'type': 'mrkdwn',
                    'text': f"Severita: *{severita.upper()}* | Timestamp: {datetime.now().isoformat()}"
                }]
            }
        ]
        return self.invia_messaggio_bot(canale, titolo, blocchi)
```

**Notifiche Microsoft Teams con Adaptive Cards**

```python
class NotificatoreTeams:
    """Gestisce le notifiche verso Microsoft Teams tramite Incoming Webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def invia_adaptive_card(self, titolo: str, messaggio: str,
                             fatti: dict = None, colore: str = '0076D7'):
        """Invia una Adaptive Card formattata a Teams."""
        card = {
            'type': 'message',
            'attachments': [{
                'contentType': 'application/vnd.microsoft.card.adaptive',
                'content': {
                    '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
                    'type': 'AdaptiveCard',
                    'version': '1.4',
                    'body': [
                        {
                            'type': 'TextBlock',
                            'text': titolo,
                            'weight': 'Bolder',
                            'size': 'Large',
                            'color': 'Accent'
                        },
                        {
                            'type': 'TextBlock',
                            'text': messaggio,
                            'wrap': True
                        }
                    ]
                }
            }]
        }

        if fatti:
            fact_set = {
                'type': 'FactSet',
                'facts': [{'title': k, 'value': str(v)} for k, v in fatti.items()]
            }
            card['attachments'][0]['content']['body'].append(fact_set)

        risposta = requests.post(self.webhook_url, json=card)
        return risposta.status_code == 200
```

**Integrazione SMS con Twilio**

Per notifiche urgenti che richiedono attenzione immediata, l'SMS tramite Twilio e una soluzione affidabile:

```python
from twilio.rest import Client

class NotificatoreSMS:
    """Invia notifiche SMS tramite Twilio."""

    def __init__(self, account_sid: str, auth_token: str, numero_mittente: str):
        self.client = Client(account_sid, auth_token)
        self.mittente = numero_mittente

    def invia_sms(self, destinatario: str, messaggio: str) -> str:
        """Invia un singolo SMS e restituisce il SID del messaggio."""
        msg = self.client.messages.create(
            body=messaggio,
            from_=self.mittente,
            to=destinatario
        )
        return msg.sid

    def invia_alert_sms(self, destinatari: list[str], messaggio: str):
        """Invia un alert SMS a piu destinatari."""
        for numero in destinatari:
            sid = self.invia_sms(numero, messaggio)
            print(f"SMS inviato a {numero}: {sid}")
```

### Chatbot e Assistenti

I chatbot e gli assistenti conversazionali introducono il paradigma ChatOps, dove le operazioni IT vengono eseguite direttamente dalle piattaforme di messaggistica.

**Bot Slack per ChatOps**

```python
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token="xoxb-il-tuo-bot-token")

@app.command("/deploy")
def gestisci_deploy(ack, say, command):
    """Comando slash per avviare un deployment."""
    ack()
    ambiente = command['text'].strip() or 'staging'
    utente = command['user_name']
    say(f":rocket: Deploy verso *{ambiente}* avviato da @{utente}...")

    # Avvia il processo di deploy
    risultato = esegui_deploy(ambiente)

    if risultato['successo']:
        say(f":white_check_mark: Deploy verso *{ambiente}* completato!\n"
            f"Versione: `{risultato['versione']}`\n"
            f"Durata: {risultato['durata']}s")
    else:
        say(f":x: Deploy fallito: {risultato['errore']}")

@app.command("/stato-servizi")
def stato_servizi(ack, say, command):
    """Mostra lo stato dei servizi monitorati."""
    ack()
    checker = HealthChecker()
    risultati = checker.esegui_tutti()

    blocchi = []
    for r in risultati:
        icona = ':white_check_mark:' if r.stato == 'ok' else ':warning:' if r.stato == 'warning' else ':x:'
        blocchi.append({
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': f"{icona} *{r.nome}*: {r.messaggio}"
            }
        })

    say(blocks=blocchi, text="Stato servizi")

@app.message("help")
def mostra_aiuto(message, say):
    """Risponde con la lista dei comandi disponibili."""
    say("*Comandi disponibili:*\n"
        "`/deploy [ambiente]` - Avvia un deployment\n"
        "`/stato-servizi` - Mostra lo stato dei servizi\n"
        "`/ticket [descrizione]` - Crea un ticket di supporto\n"
        "`help` - Mostra questo messaggio")

if __name__ == "__main__":
    handler = SocketModeHandler(app, "xapp-il-tuo-app-token")
    handler.start()
```

L'approccio ChatOps consente di eseguire operazioni direttamente dalla chat, con piena tracciabilita (ogni comando e visibile nel canale), collaborazione in tempo reale e barriera di accesso molto bassa per i nuovi membri del team.

---

## Automazione Sicurezza

L'automazione della sicurezza non e un lusso, ma una necessita. Il volume e la velocita delle minacce moderne rendono impossibile una difesa puramente manuale. L'automazione copre la scansione proattiva, la risposta automatica agli incidenti e la gestione del ciclo di vita dei certificati.

### Scansione Automatica

Le scansioni automatiche identificano vulnerabilita, configurazioni errate e non conformita prima che possano essere sfruttate.

**Programmazione scansioni di vulnerabilita**

```python
import subprocess
from datetime import datetime

class GestoreScansioni:
    """Gestisce l'esecuzione programmata di scansioni di sicurezza."""

    def scansione_nmap(self, target: str, porte: str = '1-1024') -> dict:
        """Esegue una scansione Nmap e restituisce i risultati."""
        output_file = f"/tmp/nmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        cmd = [
            'nmap', '-sV', '-sC',
            '-p', porte,
            '-oX', output_file,
            target
        ]
        risultato = subprocess.run(cmd, capture_output=True, text=True)
        return {
            'file_output': output_file,
            'successo': risultato.returncode == 0,
            'stdout': risultato.stdout,
        }

    def scansione_owasp_zap(self, target_url: str, api_key: str) -> dict:
        """Avvia una scansione OWASP ZAP automatizzata."""
        zap_base = 'http://localhost:8080'

        # Avvia spider
        requests.get(f"{zap_base}/JSON/spider/action/scan/",
                     params={'apikey': api_key, 'url': target_url})

        # Attendi completamento spider
        import time
        while True:
            stato = requests.get(f"{zap_base}/JSON/spider/view/status/",
                                params={'apikey': api_key}).json()
            if int(stato['status']) >= 100:
                break
            time.sleep(5)

        # Avvia scansione attiva
        requests.get(f"{zap_base}/JSON/ascan/action/scan/",
                     params={'apikey': api_key, 'url': target_url})

        # Attendi completamento
        while True:
            stato = requests.get(f"{zap_base}/JSON/ascan/view/status/",
                                params={'apikey': api_key}).json()
            if int(stato['status']) >= 100:
                break
            time.sleep(10)

        # Recupera report
        alert = requests.get(f"{zap_base}/JSON/core/view/alerts/",
                            params={'apikey': api_key, 'baseurl': target_url}).json()
        return alert
```

**Monitoraggio certificati SSL/TLS**

```python
import ssl
import socket
from datetime import datetime

def verifica_certificato_ssl(hostname: str, porta: int = 443) -> dict:
    """Verifica lo stato e la scadenza di un certificato SSL/TLS."""
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, porta), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                scadenza = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                giorni_rimanenti = (scadenza - datetime.now()).days
                return {
                    'hostname': hostname,
                    'emesso_da': dict(x[0] for x in cert['issuer']),
                    'scadenza': scadenza.isoformat(),
                    'giorni_rimanenti': giorni_rimanenti,
                    'stato': 'ok' if giorni_rimanenti > 30 else
                             'warning' if giorni_rimanenti > 7 else 'critical',
                    'valido': True
                }
    except ssl.SSLError as e:
        return {'hostname': hostname, 'valido': False, 'errore': str(e), 'stato': 'critical'}

def monitora_certificati(domini: list[str]):
    """Monitora lo stato dei certificati per una lista di domini."""
    risultati = []
    for dominio in domini:
        info = verifica_certificato_ssl(dominio)
        risultati.append(info)
        if info['stato'] != 'ok':
            print(f"ATTENZIONE: {dominio} - {info.get('giorni_rimanenti', 'N/A')} giorni alla scadenza")
    return risultati
```

**Verifiche di compliance automatizzate**

Le verifiche di compliance assicurano che i sistemi rispettino le politiche di sicurezza aziendali e le normative di settore:

```python
class VerificatoreCompliance:
    """Esegue verifiche di compliance automatizzate."""

    def verifica_password_policy(self) -> list[dict]:
        """Verifica che la password policy sia conforme agli standard."""
        problemi = []
        # Esempio: verifica complessita minima, scadenza, storico
        policy = self._leggi_password_policy()
        if policy.get('lunghezza_minima', 0) < 12:
            problemi.append({'regola': 'Lunghezza minima password', 'stato': 'NON CONFORME',
                           'dettaglio': f"Attuale: {policy.get('lunghezza_minima')}, Richiesta: 12"})
        if not policy.get('complessita_abilitata'):
            problemi.append({'regola': 'Complessita password', 'stato': 'NON CONFORME'})
        return problemi

    def verifica_porte_aperte(self, host: str) -> list[dict]:
        """Verifica che solo le porte autorizzate siano aperte."""
        porte_autorizzate = {22, 80, 443}
        problemi = []
        # Scansione porte con socket
        for porta in range(1, 1025):
            try:
                sock = socket.create_connection((host, porta), timeout=1)
                sock.close()
                if porta not in porte_autorizzate:
                    problemi.append({'porta': porta, 'stato': 'NON AUTORIZZATA'})
            except (socket.timeout, ConnectionRefusedError, OSError):
                pass
        return problemi

    def _leggi_password_policy(self) -> dict:
        """Legge la password policy corrente dal sistema."""
        # Implementazione specifica per il sistema operativo
        return {}
```

### Incident Response Automation

L'automazione della risposta agli incidenti riduce il tempo tra il rilevamento e il contenimento, un fattore critico per limitare l'impatto delle violazioni.

**Aggregazione e correlazione log**

```python
import re
from collections import defaultdict

class AnalizzatoreLog:
    """Analizza e correla eventi da piu sorgenti di log."""

    def __init__(self):
        self.pattern_sospetti = [
            (r'Failed password for .+ from (\d+\.\d+\.\d+\.\d+)', 'brute_force'),
            (r'POSSIBLE BREAK-IN ATTEMPT', 'intrusione'),
            (r'segfault at', 'crash_applicazione'),
            (r'Out of memory', 'esaurimento_memoria'),
        ]

    def analizza_file_log(self, percorso_log: str) -> dict:
        """Analizza un file di log alla ricerca di pattern sospetti."""
        eventi = defaultdict(list)
        ip_sospetti = defaultdict(int)

        with open(percorso_log, 'r') as f:
            for riga in f:
                for pattern, tipo in self.pattern_sospetti:
                    match = re.search(pattern, riga)
                    if match:
                        eventi[tipo].append(riga.strip())
                        if match.groups():
                            ip_sospetti[match.group(1)] += 1

        return {
            'eventi': dict(eventi),
            'ip_sospetti': dict(ip_sospetti),
            'totale_eventi': sum(len(v) for v in eventi.values()),
        }

    def rileva_brute_force(self, percorso_log: str, soglia: int = 5) -> list[str]:
        """Identifica IP con tentativi di accesso falliti oltre la soglia."""
        risultati = self.analizza_file_log(percorso_log)
        return [ip for ip, count in risultati['ip_sospetti'].items() if count >= soglia]
```

**Blocco automatico degli IP sospetti**

```python
import subprocess

class GestoreFirewall:
    """Gestisce il blocco automatico di IP sospetti tramite iptables/nftables."""

    def blocca_ip(self, ip: str, motivo: str = ''):
        """Blocca un indirizzo IP a livello firewall."""
        cmd = ['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP']
        risultato = subprocess.run(cmd, capture_output=True, text=True)
        if risultato.returncode == 0:
            self._registra_blocco(ip, motivo)
            print(f"IP bloccato: {ip} - Motivo: {motivo}")
        return risultato.returncode == 0

    def blocca_ip_da_analisi(self, percorso_log: str, soglia_tentativi: int = 10):
        """Analizza i log e blocca automaticamente gli IP sospetti."""
        analizzatore = AnalizzatoreLog()
        ip_sospetti = analizzatore.rileva_brute_force(percorso_log, soglia_tentativi)

        for ip in ip_sospetti:
            self.blocca_ip(ip, f"Superata soglia di {soglia_tentativi} tentativi falliti")

    def _registra_blocco(self, ip: str, motivo: str):
        """Registra il blocco per audit trail."""
        with open('/var/log/ip_bloccati.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()} | {ip} | {motivo}\n")
```

**Raccolta dati forensi automatizzata**

Quando viene rilevato un incidente, la raccolta rapida e strutturata delle evidenze e fondamentale:

```python
class RaccoltaForense:
    """Raccoglie automaticamente dati forensi in caso di incidente."""

    def __init__(self, directory_output: str):
        self.output = Path(directory_output)
        self.output.mkdir(parents=True, exist_ok=True)

    def raccogli_tutto(self, hostname: str) -> str:
        """Esegue una raccolta forense completa."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        cartella = self.output / f"forense_{hostname}_{timestamp}"
        cartella.mkdir()

        self._raccogli_connessioni_rete(cartella)
        self._raccogli_processi_attivi(cartella)
        self._raccogli_utenti_connessi(cartella)
        self._raccogli_log_recenti(cartella)
        self._raccogli_hash_file_critici(cartella)

        return str(cartella)

    def _raccogli_connessioni_rete(self, dest: Path):
        risultato = subprocess.run(['ss', '-tunapl'], capture_output=True, text=True)
        (dest / 'connessioni_rete.txt').write_text(risultato.stdout)

    def _raccogli_processi_attivi(self, dest: Path):
        risultato = subprocess.run(['ps', 'auxf'], capture_output=True, text=True)
        (dest / 'processi_attivi.txt').write_text(risultato.stdout)

    def _raccogli_utenti_connessi(self, dest: Path):
        risultato = subprocess.run(['w'], capture_output=True, text=True)
        (dest / 'utenti_connessi.txt').write_text(risultato.stdout)

    def _raccogli_log_recenti(self, dest: Path):
        log_files = ['/var/log/auth.log', '/var/log/syslog', '/var/log/kern.log']
        for log in log_files:
            if Path(log).exists():
                # Copia le ultime 1000 righe
                risultato = subprocess.run(['tail', '-n', '1000', log],
                                          capture_output=True, text=True)
                nome = Path(log).name
                (dest / nome).write_text(risultato.stdout)

    def _raccogli_hash_file_critici(self, dest: Path):
        file_critici = ['/etc/passwd', '/etc/shadow', '/etc/hosts']
        hash_list = []
        for file in file_critici:
            if Path(file).exists():
                risultato = subprocess.run(['sha256sum', file],
                                          capture_output=True, text=True)
                hash_list.append(risultato.stdout.strip())
        (dest / 'hash_file_critici.txt').write_text('\n'.join(hash_list))
```

### Gestione Certificati

La gestione automatizzata dei certificati SSL/TLS elimina il rischio di scadenze non previste, che possono causare interruzioni di servizio e problemi di sicurezza.

**Monitoraggio scadenza e rinnovo automatico con certbot**

```bash
#!/bin/bash
# rinnovo_certificati.sh — Rinnovo automatico certificati Let's Encrypt

LOG="/var/log/certbot_rinnovo.log"

echo "=== Verifica rinnovo certificati: $(date) ===" >> "$LOG"

# Tentativo di rinnovo per tutti i certificati
certbot renew --quiet --deploy-hook "systemctl reload nginx" 2>> "$LOG"

ESITO=$?
if [ $ESITO -eq 0 ]; then
    echo "Rinnovo completato con successo" >> "$LOG"
else
    echo "ERRORE nel rinnovo (codice: $ESITO)" >> "$LOG"
    # Invio notifica in caso di errore
    curl -X POST "https://hooks.slack.com/services/TOKEN" \
        -H 'Content-type: application/json' \
        -d '{"text":":warning: Errore rinnovo certificati SSL. Verificare immediatamente."}'
fi
```

**Automazione certificati CA interna**

Per gli ambienti con una PKI interna, l'automazione copre la generazione, la distribuzione e il rinnovo dei certificati:

```python
import subprocess
from pathlib import Path

class GestoreCertificatiInterni:
    """Gestisce il ciclo di vita dei certificati dalla CA interna."""

    def __init__(self, ca_dir: str):
        self.ca_dir = Path(ca_dir)

    def genera_certificato(self, cn: str, san: list[str] = None,
                           durata_giorni: int = 365) -> dict:
        """Genera un nuovo certificato firmato dalla CA interna."""
        cert_dir = self.ca_dir / 'certs' / cn
        cert_dir.mkdir(parents=True, exist_ok=True)

        key_file = cert_dir / f"{cn}.key"
        csr_file = cert_dir / f"{cn}.csr"
        cert_file = cert_dir / f"{cn}.crt"

        # Genera chiave privata
        subprocess.run([
            'openssl', 'genrsa', '-out', str(key_file), '4096'
        ], check=True)

        # Genera CSR
        subj = f"/CN={cn}/O=Azienda/C=IT"
        cmd_csr = ['openssl', 'req', '-new', '-key', str(key_file),
                   '-out', str(csr_file), '-subj', subj]
        subprocess.run(cmd_csr, check=True)

        # Firma con CA
        cmd_sign = [
            'openssl', 'x509', '-req',
            '-in', str(csr_file),
            '-CA', str(self.ca_dir / 'ca.crt'),
            '-CAkey', str(self.ca_dir / 'ca.key'),
            '-CAcreateserial',
            '-out', str(cert_file),
            '-days', str(durata_giorni),
            '-sha256'
        ]
        subprocess.run(cmd_sign, check=True)

        return {
            'chiave': str(key_file),
            'certificato': str(cert_file),
            'scadenza_giorni': durata_giorni,
        }
```

**Alert preventivo prima della scadenza**

Un sistema di monitoraggio che avvisa con anticipo crescente man mano che la scadenza si avvicina:

```python
def alert_scadenza_certificati(domini: list[str], notificatore):
    """Invia alert graduali in base ai giorni alla scadenza."""
    for dominio in domini:
        info = verifica_certificato_ssl(dominio)
        if not info.get('valido'):
            notificatore.invia_alert_formattato(
                '#sicurezza', f"Certificato non valido: {dominio}",
                f"Errore: {info.get('errore', 'sconosciuto')}", 'critical')
            continue

        giorni = info['giorni_rimanenti']
        if giorni <= 7:
            notificatore.invia_alert_formattato(
                '#sicurezza', f"Certificato in scadenza IMMINENTE: {dominio}",
                f"Scade tra {giorni} giorni!", 'critical')
        elif giorni <= 30:
            notificatore.invia_alert_formattato(
                '#sicurezza', f"Certificato in scadenza: {dominio}",
                f"Scade tra {giorni} giorni. Pianificare il rinnovo.", 'warning')
        elif giorni <= 60:
            notificatore.invia_alert_formattato(
                '#monitoring', f"Certificato: {dominio}",
                f"Scadenza tra {giorni} giorni. Rinnovo da programmare.", 'info')
```

---

## Automazione Cloud e DevOps

L'automazione nel dominio Cloud e DevOps rappresenta la frontiera piu avanzata dell'automazione IT. In questo contesto, l'intera infrastruttura viene trattata come codice, le operazioni sono completamente automatizzate e i deployment avvengono in modo continuo e affidabile.

### Infrastructure as Code

L'Infrastructure as Code (IaC) e il paradigma fondamentale dell'automazione cloud: l'infrastruttura viene definita in file dichiarativi, versionati e applicati automaticamente.

**Terraform per l'automazione infrastrutturale**

Terraform e lo strumento IaC piu diffuso, con supporto multi-cloud e un vasto ecosistema di provider:

```hcl
# main.tf — Infrastruttura applicazione web su AWS

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket = "terraform-state-azienda"
    key    = "produzione/terraform.tfstate"
    region = "eu-south-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.regione
}

# VPC e networking
resource "aws_vpc" "principale" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = {
    Name        = "vpc-produzione"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

resource "aws_subnet" "pubblica" {
  count             = 2
  vpc_id            = aws_vpc.principale.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = "${var.regione}${count.index == 0 ? "a" : "b"}"
  map_public_ip_on_launch = true
  tags = {
    Name = "subnet-pubblica-${count.index + 1}"
  }
}

# Application Load Balancer
resource "aws_lb" "applicazione" {
  name               = "alb-produzione"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.pubblica[*].id
}

# Auto Scaling Group
resource "aws_autoscaling_group" "app" {
  name                = "asg-app-produzione"
  desired_capacity    = var.istanze_desiderate
  max_size            = var.istanze_massime
  min_size            = var.istanze_minime
  vpc_zone_identifier = aws_subnet.pubblica[*].id
  target_group_arns   = [aws_lb_target_group.app.arn]

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "Environment"
    value               = "production"
    propagate_at_launch = true
  }
}

variable "regione" {
  default = "eu-south-1"
}

variable "istanze_desiderate" {
  default = 2
}

variable "istanze_massime" {
  default = 6
}

variable "istanze_minime" {
  default = 2
}
```

**Panoramica CloudFormation e Bicep**

CloudFormation (AWS) e Bicep (Azure) sono le alternative native dei rispettivi cloud provider. CloudFormation utilizza JSON o YAML, mentre Bicep offre una sintassi piu concisa per Azure Resource Manager:

```bicep
// main.bicep — Infrastruttura Azure
param location string = resourceGroup().location
param appName string = 'webapp-produzione'

resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${appName}-plan'
  location: location
  sku: {
    name: 'P1v3'
    tier: 'PremiumV3'
  }
}

resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: appName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: true
      minTlsVersion: '1.2'
    }
  }
}
```

**Provisioning automatizzato degli ambienti**

L'automazione del provisioning permette di creare ambienti completi (sviluppo, staging, produzione) con un singolo comando, garantendo coerenza tra i vari ambienti:

```python
import subprocess

class ProvisionerAmbienti:
    """Gestisce il provisioning automatizzato di ambienti tramite Terraform."""

    def __init__(self, terraform_dir: str):
        self.tf_dir = terraform_dir

    def provisiona_ambiente(self, ambiente: str, variabili: dict = None) -> bool:
        """Provisiona un ambiente completo."""
        var_file = f"environments/{ambiente}.tfvars"

        # Init
        self._esegui_terraform(['init', '-backend-config', f'key={ambiente}/terraform.tfstate'])

        # Plan
        cmd_plan = ['plan', f'-var-file={var_file}', '-out=tfplan']
        if variabili:
            for k, v in variabili.items():
                cmd_plan.extend(['-var', f'{k}={v}'])

        risultato_plan = self._esegui_terraform(cmd_plan)
        if not risultato_plan:
            return False

        # Apply
        return self._esegui_terraform(['apply', '-auto-approve', 'tfplan'])

    def distruggi_ambiente(self, ambiente: str) -> bool:
        """Distrugge un ambiente (utile per ambienti temporanei)."""
        var_file = f"environments/{ambiente}.tfvars"
        return self._esegui_terraform(['destroy', '-auto-approve', f'-var-file={var_file}'])

    def _esegui_terraform(self, args: list) -> bool:
        cmd = ['terraform'] + args
        risultato = subprocess.run(cmd, cwd=self.tf_dir, capture_output=True, text=True)
        if risultato.returncode != 0:
            print(f"Errore Terraform: {risultato.stderr}")
        return risultato.returncode == 0
```

### Container Automation

L'automazione dei container copre l'intero ciclo di vita: build, test, push, deployment e monitoring.

**Pipeline di build e push Docker**

```python
import subprocess
from datetime import datetime

class PipelineDocker:
    """Pipeline automatizzata per build, test e push di immagini Docker."""

    def __init__(self, registry: str, repository: str):
        self.registry = registry
        self.repository = repository

    def build_e_push(self, dockerfile: str, context: str,
                     tag: str = None) -> dict:
        """Esegue build, tag e push di un'immagine Docker."""
        if not tag:
            tag = datetime.now().strftime('%Y%m%d-%H%M%S')

        immagine = f"{self.registry}/{self.repository}"
        tags = [f"{immagine}:{tag}", f"{immagine}:latest"]

        # Build
        cmd_build = ['docker', 'build', '-f', dockerfile, '-t', tags[0], '-t', tags[1], context]
        risultato = subprocess.run(cmd_build, capture_output=True, text=True)
        if risultato.returncode != 0:
            return {'successo': False, 'fase': 'build', 'errore': risultato.stderr}

        # Push entrambi i tag
        for t in tags:
            cmd_push = ['docker', 'push', t]
            risultato = subprocess.run(cmd_push, capture_output=True, text=True)
            if risultato.returncode != 0:
                return {'successo': False, 'fase': 'push', 'errore': risultato.stderr}

        return {'successo': True, 'immagine': tags[0], 'tag': tag}

    def scansione_sicurezza(self, immagine: str) -> dict:
        """Esegue una scansione di sicurezza sull'immagine tramite Trivy."""
        cmd = ['trivy', 'image', '--format', 'json', '--severity', 'HIGH,CRITICAL', immagine]
        risultato = subprocess.run(cmd, capture_output=True, text=True)
        if risultato.returncode == 0:
            import json
            return json.loads(risultato.stdout)
        return {'errore': risultato.stderr}
```

**Monitoraggio salute container e auto-scaling**

```python
import docker
from dataclasses import dataclass

@dataclass
class StatoContainer:
    nome: str
    stato: str
    cpu_percent: float
    memoria_mb: float
    riavvii: int

class MonitorContainer:
    """Monitora lo stato dei container e attiva azioni correttive."""

    def __init__(self):
        self.client = docker.from_env()

    def stato_container(self) -> list[StatoContainer]:
        """Recupera lo stato di tutti i container in esecuzione."""
        stati = []
        for container in self.client.containers.list():
            stats = container.stats(stream=False)
            cpu = self._calcola_cpu_percent(stats)
            mem = stats['memory_stats'].get('usage', 0) / (1024 * 1024)
            riavvii = container.attrs['RestartCount']

            stati.append(StatoContainer(
                nome=container.name,
                stato=container.status,
                cpu_percent=cpu,
                memoria_mb=round(mem, 2),
                riavvii=riavvii
            ))
        return stati

    def riavvia_se_non_sano(self):
        """Riavvia i container non sani."""
        for container in self.client.containers.list():
            health = container.attrs.get('State', {}).get('Health', {})
            if health.get('Status') == 'unhealthy':
                print(f"Container non sano: {container.name}. Riavvio in corso...")
                container.restart(timeout=30)

    def _calcola_cpu_percent(self, stats: dict) -> float:
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                    stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                       stats['precpu_stats']['system_cpu_usage']
        if system_delta > 0:
            num_cpus = len(stats['cpu_stats']['cpu_usage'].get('percpu_usage', [1]))
            return round((cpu_delta / system_delta) * num_cpus * 100, 2)
        return 0.0
```

**Trigger di auto-scaling**

L'auto-scaling automatico adatta il numero di istanze al carico corrente:

```python
class GestoreAutoScaling:
    """Gestisce l'auto-scaling dei container in base a metriche."""

    def __init__(self, servizio: str, min_repliche: int = 1,
                 max_repliche: int = 10):
        self.servizio = servizio
        self.min_repliche = min_repliche
        self.max_repliche = max_repliche
        self.client = docker.from_env()

    def valuta_scaling(self, cpu_media: float, soglia_scale_up: float = 70,
                       soglia_scale_down: float = 30):
        """Valuta se e necessario scalare il servizio."""
        repliche_attuali = self._conta_repliche()

        if cpu_media > soglia_scale_up and repliche_attuali < self.max_repliche:
            nuove_repliche = min(repliche_attuali + 1, self.max_repliche)
            self._scala(nuove_repliche)
            print(f"Scale UP: {repliche_attuali} -> {nuove_repliche}")
        elif cpu_media < soglia_scale_down and repliche_attuali > self.min_repliche:
            nuove_repliche = max(repliche_attuali - 1, self.min_repliche)
            self._scala(nuove_repliche)
            print(f"Scale DOWN: {repliche_attuali} -> {nuove_repliche}")

    def _conta_repliche(self) -> int:
        servizio = self.client.services.get(self.servizio)
        return servizio.attrs['Spec']['Mode']['Replicated']['Replicas']

    def _scala(self, repliche: int):
        servizio = self.client.services.get(self.servizio)
        servizio.scale(repliche)
```

---

## Best Practices

Le seguenti best practices sintetizzano i principi fondamentali per implementare con successo l'automazione per dominio in qualsiasi organizzazione.

1. **Iniziare dal valore, non dalla tecnologia.** Prima di scegliere uno strumento, identificare il processo che genera il maggiore impatto se automatizzato. Calcolare il tempo speso manualmente, la frequenza degli errori e il costo delle interruzioni. L'automazione che risolve un problema reale e sentito viene adottata naturalmente; quella costruita attorno a una tecnologia alla moda rischia di rimanere inutilizzata.

2. **Automatizzare in modo incrementale.** Non tentare di automatizzare tutto simultaneamente. Partire con un singolo processo ben definito, misurare i risultati, raccogliere feedback e poi estendere. Un'automazione parziale che funziona e infinitamente piu utile di un sistema completo che non viene mai completato. L'approccio incrementale riduce anche il rischio e permette di correggere il corso durante lo sviluppo.

3. **Implementare logging e observability fin dall'inizio.** Ogni automazione deve produrre log strutturati, metriche di esecuzione e audit trail. Senza observability, non e possibile diagnosticare problemi, misurare l'efficacia o dimostrare la compliance. Utilizzare formati standardizzati (JSON per i log, metriche Prometheus-compatibili) e centralizzare la raccolta con strumenti come ELK Stack o Loki.

4. **Gestire gli errori come cittadini di prima classe.** Le automazioni operano senza supervisione umana diretta. Ogni script deve gestire esplicitamente i casi di errore: catturare le eccezioni, tentare retry con backoff esponenziale dove appropriato, notificare i responsabili quando l'auto-remediation fallisce e soprattutto non fallire silenziosamente. Un errore non gestito in un'automazione puo propagarsi per ore o giorni prima di essere scoperto.

5. **Versionare tutto e trattare l'automazione come codice.** Script, configurazioni, template, playbook Ansible, moduli Terraform: tutto deve risiedere in un repository Git con revisione del codice, branching strategy e pipeline di test. L'automazione non versionata diventa rapidamente ingestibile e non riproducibile. La revisione del codice garantisce qualita e condivisione della conoscenza all'interno del team.

6. **Separare la configurazione dal codice.** Le credenziali, gli URL degli endpoint, le soglie di alerting e tutti i parametri specifici dell'ambiente devono risiedere in file di configurazione esterni, variabili d'ambiente o sistemi di gestione dei segreti (come HashiCorp Vault o AWS Secrets Manager). Mai incorporare credenziali nel codice sorgente. Questa separazione facilita il riutilizzo degli script tra ambienti diversi e migliora la sicurezza.

7. **Progettare per l'idempotenza.** Ogni automazione deve poter essere eseguita piu volte senza effetti collaterali indesiderati. Se un backup e gia stato eseguito, non deve essere duplicato. Se un utente esiste gia, il provisioning deve aggiornarsi senza errori. L'idempotenza e fondamentale per la robustezza: in caso di errori parziali, deve essere possibile rieseguire l'intero flusso senza rischi.

8. **Documentare il "perche", non solo il "come".** Il codice mostra il "come", ma raramente il "perche". Ogni automazione deve avere documentazione che spiega: quale problema risolve, quali sono le dipendenze, come viene attivata, quali sono i possibili stati di errore e come viene monitorata. Questa documentazione e essenziale per il passaggio di consegne, la manutenzione a lungo termine e l'onboarding di nuovi membri del team.

9. **Testare le automazioni come si testa il software.** Le automazioni sono codice e meritano lo stesso livello di testing. Utilizzare unit test per le funzioni di logica, integration test per verificare le interazioni con sistemi esterni e test end-to-end per validare l'intero flusso. Strumenti come pytest, Molecule (per Ansible) e Terratest (per Terraform) rendono il testing delle automazioni sistematico e ripetibile.

10. **Pianificare la manutenzione e il ciclo di vita.** Le automazioni non sono artefatti statici. Le API cambiano, i sistemi operativi vengono aggiornati, le librerie introducono breaking change. Assegnare un responsabile per ogni automazione, programmare revisioni periodiche e monitorare le dipendenze per vulnerabilita e deprecazioni. Un'automazione non manutenuta diventa un debito tecnico che cresce silenziosamente fino a causare un problema nel momento peggiore.

---

> **Nota conclusiva**: L'automazione per dominio non e un progetto con una data di fine, ma un percorso continuo di miglioramento. Ogni processo automatizzato libera tempo e risorse che possono essere reinvestite per automatizzare il prossimo processo, creando un ciclo virtuoso di efficienza crescente. La chiave del successo risiede nella combinazione di competenze tecniche, comprensione profonda dei processi aziendali e una cultura organizzativa che valorizza il miglioramento continuo.

---

## Esercizi

1. **Mapping dominio aziendale.** Per la tua organizzazione (o cliente), identifica 5 processi candidati per automazione. Per ognuno: dominio, tempo manuale/settimana, criticita, complessita, ROI stimato.
2. **Lab — onboarding nuovo dipendente.** Implementa workflow: Form HR → creazione account M365/Google → Slack invite → benvenuto email → calendar onboarding. Idempotente, audit log GDPR-compliant.
3. **Stretch — pipeline lead-to-deal.** Workflow CRM (HubSpot/Pipedrive) integrato con email (Mailchimp), calendar, Slack notify; ROI report mensile.

## Auto-valutazione

1. Quali domini hanno ROI tipico piu alto?
2. Compliance constraint per HR vs Finance.
3. Marketing automation senza A/B test: rischio?
4. IT Ops perche e domini di partenza?

## Letture primarie consigliate

- Vendor case studies: HubSpot, Pipedrive, Workday.
- Vedi `00-BIBLIOGRAFIA.md`.

## Collegamenti incrociati

- Modulo 21 — `21-ricette-vertical-pmi-italia.md`: ricette per PMI italiana.
- Modulo 24 (NEW) — `24-audit-logging-compliance.md`: audit GDPR.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Dominio (business)** | Area funzionale aziendale (HR, Sales, ecc.). |
| **Onboarding workflow** | Automazione provisioning nuovo dipendente. |
| **Lead-to-deal pipeline** | Sales automation. |
| **A/B test** | Comparazione due varianti su utenti. |
| **CRM** | Customer Relationship Management. |
| **Compliance constraint** | Vincolo regolamentare (GDPR, SOX, HIPAA). |
