---
corso: "Automazioni e Flussi di Lavoro"
fase: "2 — Scripting e Integrazione"
modulo: 12
titolo: "Python per l'Automazione Avanzata — Guida Progettuale"
versione: "Python 3.11+, uv 0.4+, pydantic 2.x, httpx, structlog"
livello: "competent → proficient"
prerequisiti:
  - "Python intermedio"
  - "pip/uv basics"
  - "httpx/requests"
  - "click/typer"
obiettivi:
  - "Strutturare progetti di automazione production-grade con uv e pyproject.toml"
  - "Implementare client HTTP asincroni con httpx, retry e rate limiting"
  - "Configurare structured logging con structlog e tracing con OpenTelemetry"
  - "Costruire CLI robuste con click/typer, validazione Pydantic e packaging"
  - "Deployare automazioni come servizi systemd con monitoring e alerting"
tag: [python, automazione, uv, pydantic, httpx, structlog, opentelemetry, cli]
---

# Python per l'Automazione Avanzata — Guida Progettuale

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 3 — Piattaforme · Modulo 12
> **Prerequisiti:** Python intermedio; pip/uv basics; httpx/requests; click/typer.
> **Obiettivi:** automation framework production-grade: project scaffolding, dependency management, packaging, deployment, observability.
> **Tempo:** lettura 90 min · lab 480 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-05-24
> **Versioni:** Python 3.11+, uv 0.4+, pydantic 2.x, httpx, structlog, OpenTelemetry SDK.

## Idee guida

1. **`uv` > `pip` per nuovi progetti.** Veloce, lock file deterministico, package management migliore.
2. **`pyproject.toml` (PEP 621) > `setup.py`.** Standard moderno; tutti i tool lo capiscono.
3. **httpx > requests per nuovo codice.** httpx supporta async, HTTP/2, type hints proper.
4. **Pydantic v2 per data validation, dataclasses per non-validated.** v2 e ~10x piu veloce di v1.
5. **structlog > logging stdlib per produzione.** Strutturato JSON nativo.

---

## Indice

- [Panoramica](#panoramica)
- [Automazione del File System](#automazione-del-file-system)
- [Monitoraggio File in Tempo Reale con Watchdog](#monitoraggio-file-in-tempo-reale-con-watchdog)
- [Automazione Email](#automazione-email)
- [Automazione Excel con openpyxl](#automazione-excel-con-openpyxl)
- [Generazione e Manipolazione PDF](#generazione-e-manipolazione-pdf)
- [Automazione Documenti Word](#automazione-documenti-word)
- [Web Automation con Selenium](#web-automation-con-selenium)
- [Web Automation con Playwright](#web-automation-con-playwright)
- [Pattern di Integrazione API](#pattern-di-integrazione-api)
- [Scheduling: APScheduler e Cron](#scheduling-apscheduler-e-cron)
- [Database Automation con SQLAlchemy](#database-automation-con-sqlalchemy)
- [Sistemi di Notifica](#sistemi-di-notifica)
- [Progetto Completo: Pipeline di Reportistica Automatizzata](#progetto-completo-pipeline-di-reportistica-automatizzata)
- [Progetto Completo: Sistema di Monitoring con Alert](#progetto-completo-sistema-di-monitoring-con-alert)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

Python è il linguaggio di riferimento per l'automazione di sistema grazie alla sua ricchezza di librerie mature, alla sintassi leggibile e alla capacità di integrarsi con praticamente qualsiasi sistema, protocollo o formato di dati. Mentre le piattaforme low-code eccellono nell'integrazione tra servizi SaaS, Python si distingue per le automazioni che richiedono logica complessa, manipolazione avanzata dei dati, interazione con il file system, automazione dell'interfaccia utente, e integrazione con sistemi legacy che non espongono API moderne.

Questa guida è strutturata come una raccolta di pattern e progetti concreti, ciascuno con codice completo e funzionante. L'obiettivo non è fornire una panoramica teorica delle librerie, ma dimostrare come combinare diverse librerie in soluzioni operative per problemi reali di automazione aziendale. Ogni sezione include la gestione degli errori, il logging, e le considerazioni di produzione che distinguono un prototipo da un sistema affidabile.

Le librerie trattate coprono l'intero spettro dell'automazione: `pathlib` e `shutil` per il file system, `watchdog` per il monitoraggio in tempo reale, `smtplib` e `imaplib` per le email, `openpyxl` per Excel, `reportlab` e `PyPDF2` per i PDF, `python-docx` per Word, `selenium` e `playwright` per il browser, `requests` per le API HTTP, `APScheduler` per lo scheduling, `SQLAlchemy` per i database, e le API di Slack e Telegram per le notifiche.

---

## Automazione del File System

### Operazioni con pathlib e shutil

`pathlib` (standard library da Python 3.4) offre un'interfaccia orientata agli oggetti per la manipolazione dei percorsi. `shutil` fornisce operazioni di alto livello su file e directory.

```python
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import hashlib
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def organizza_file_per_data(source_dir: str, dest_base: str, extensions: set[str] | None = None) -> dict[str, int]:
    """
    Organizza i file di una directory in sottocartelle anno/mese/giorno
    basate sulla data di modifica del file.

    Args:
        source_dir: directory sorgente contenente i file da organizzare
        dest_base: directory base di destinazione
        extensions: set di estensioni da includere (es. {'.pdf', '.xlsx'}), None per tutte

    Returns:
        dizionario con statistiche {percorso_destinazione: numero_file_spostati}
    """
    source = Path(source_dir)
    dest = Path(dest_base)
    stats: dict[str, int] = {}

    if not source.is_dir():
        raise FileNotFoundError(f"Directory sorgente non trovata: {source}")

    for file_path in source.iterdir():
        if not file_path.is_file():
            continue

        if extensions and file_path.suffix.lower() not in extensions:
            continue

        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        dest_dir = dest / f"{mod_time.year}" / f"{mod_time.month:02d}" / f"{mod_time.day:02d}"
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_file = dest_dir / file_path.name
        if dest_file.exists():
            # Aggiungere timestamp per evitare sovrascrittura
            stem = file_path.stem
            suffix = file_path.suffix
            dest_file = dest_dir / f"{stem}_{mod_time.strftime('%H%M%S')}{suffix}"

        shutil.move(str(file_path), str(dest_file))
        logger.info(f"Spostato: {file_path.name} → {dest_dir}")
        stats[str(dest_dir)] = stats.get(str(dest_dir), 0) + 1

    return stats


def trova_file_duplicati(directory: str, chunk_size: int = 8192) -> dict[str, list[Path]]:
    """
    Trova file duplicati in una directory calcolando l'hash SHA-256.
    Utilizza un approccio a due fasi: prima raggruppa per dimensione,
    poi calcola l'hash solo per i file con dimensione identica.
    """
    size_groups: dict[int, list[Path]] = {}
    duplicates: dict[str, list[Path]] = {}

    # Fase 1: raggruppamento per dimensione (O(n))
    for file_path in Path(directory).rglob('*'):
        if file_path.is_file():
            size = file_path.stat().st_size
            size_groups.setdefault(size, []).append(file_path)

    # Fase 2: hash solo per gruppi con dimensione identica
    for size, files in size_groups.items():
        if len(files) < 2:
            continue

        hash_groups: dict[str, list[Path]] = {}
        for file_path in files:
            file_hash = _calculate_hash(file_path, chunk_size)
            hash_groups.setdefault(file_hash, []).append(file_path)

        for file_hash, hash_files in hash_groups.items():
            if len(hash_files) > 1:
                duplicates[file_hash] = hash_files

    return duplicates


def _calculate_hash(file_path: Path, chunk_size: int = 8192) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def pulizia_file_vecchi(directory: str, max_age_days: int, dry_run: bool = True) -> list[Path]:
    """
    Elimina file più vecchi di max_age_days.
    Con dry_run=True, restituisce la lista senza eliminare.
    """
    threshold = datetime.now() - timedelta(days=max_age_days)
    old_files: list[Path] = []

    for file_path in Path(directory).rglob('*'):
        if file_path.is_file():
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mod_time < threshold:
                old_files.append(file_path)
                if not dry_run:
                    file_path.unlink()
                    logger.info(f"Eliminato: {file_path}")

    logger.info(f"{'[DRY RUN] ' if dry_run else ''}File trovati: {len(old_files)}")
    return old_files
```

L'approccio a due fasi nella ricerca dei duplicati è un'ottimizzazione significativa: il raggruppamento per dimensione (operazione O(1) per file) filtra la maggior parte dei file prima di calcolare l'hash (operazione O(n) sulla dimensione del file), riducendo drasticamente il tempo di esecuzione su directory con migliaia di file.

---

## Monitoraggio File in Tempo Reale con Watchdog

La libreria `watchdog` monitora il file system per eventi in tempo reale (creazione, modifica, eliminazione, spostamento di file).

```python
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
import logging

logger = logging.getLogger(__name__)


class InvoiceProcessor(FileSystemEventHandler):
    """
    Monitora una directory per nuovi file PDF e li processa automaticamente.
    Implementa un debounce per gestire gli eventi multipli generati
    durante la scrittura di un file.
    """

    def __init__(self, output_dir: str, debounce_seconds: float = 2.0):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._pending: dict[str, float] = {}
        self._debounce = debounce_seconds

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix.lower() != '.pdf':
            return

        # Debounce: registra il timestamp, processa dopo il debounce
        self._pending[str(file_path)] = time.time()
        logger.info(f"Nuovo file rilevato: {file_path.name}")

    def on_modified(self, event: FileModifiedEvent) -> None:
        # Aggiorna il timestamp di debounce
        if str(event.src_path) in self._pending:
            self._pending[str(event.src_path)] = time.time()

    def process_pending(self) -> None:
        """Chiamato periodicamente per processare i file con debounce scaduto."""
        now = time.time()
        ready = [
            path for path, ts in self._pending.items()
            if now - ts >= self._debounce
        ]

        for path_str in ready:
            del self._pending[path_str]
            file_path = Path(path_str)
            if file_path.exists():
                try:
                    self._process_file(file_path)
                except Exception as e:
                    logger.error(f"Errore processando {file_path.name}: {e}")

    def _process_file(self, file_path: Path) -> None:
        logger.info(f"Processamento: {file_path.name}")
        # Spostare nella directory di output con timestamp
        dest = self.output_dir / f"processed_{file_path.name}"
        import shutil
        shutil.copy2(str(file_path), str(dest))
        logger.info(f"Completato: {file_path.name} → {dest}")


def start_file_monitor(watch_dir: str, output_dir: str) -> None:
    handler = InvoiceProcessor(output_dir)
    observer = Observer()
    observer.schedule(handler, watch_dir, recursive=False)
    observer.start()

    logger.info(f"Monitoraggio attivo su: {watch_dir}")

    try:
        while True:
            handler.process_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Monitoraggio terminato")

    observer.join()
```

Il meccanismo di debounce è essenziale perché molti sistemi operativi generano eventi multipli durante la scrittura di un singolo file (creazione del file, scrittura parziale, flush, chiusura). Senza debounce, il processamento potrebbe avviarsi su un file incompleto.

---

## Automazione Email

### Invio Email con smtplib

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True


def send_email(
    config: EmailConfig,
    to: list[str],
    subject: str,
    body_html: str,
    cc: list[str] | None = None,
    attachments: list[str] | None = None,
) -> None:
    """
    Invia un'email con supporto HTML e allegati.

    Args:
        config: configurazione SMTP
        to: lista destinatari
        subject: oggetto dell'email
        body_html: corpo HTML
        cc: lista destinatari in copia
        attachments: lista percorsi file da allegare
    """
    msg = MIMEMultipart('mixed')
    msg['From'] = config.username
    msg['To'] = ', '.join(to)
    msg['Subject'] = subject

    if cc:
        msg['Cc'] = ', '.join(cc)

    # Corpo HTML
    html_part = MIMEText(body_html, 'html', 'utf-8')
    msg.attach(html_part)

    # Allegati
    if attachments:
        for file_path_str in attachments:
            file_path = Path(file_path_str)
            if not file_path.exists():
                logger.warning(f"Allegato non trovato: {file_path}")
                continue

            with open(file_path, 'rb') as f:
                attachment = MIMEApplication(f.read(), Name=file_path.name)
            attachment['Content-Disposition'] = f'attachment; filename="{file_path.name}"'
            msg.attach(attachment)

    # Invio
    all_recipients = to + (cc or [])

    with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
        if config.use_tls:
            server.starttls()
        server.login(config.username, config.password)
        server.sendmail(config.username, all_recipients, msg.as_string())

    logger.info(f"Email inviata a {', '.join(to)}: {subject}")
```

### Lettura Email con imaplib

```python
import imaplib
import email
from email.header import decode_header
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParsedEmail:
    subject: str
    sender: str
    date: str
    body_text: str
    body_html: str
    attachments: list[dict]


def fetch_unread_emails(
    server: str,
    username: str,
    password: str,
    folder: str = "INBOX",
    search_criteria: str = "UNSEEN",
    download_attachments_to: str | None = None,
) -> list[ParsedEmail]:
    """
    Recupera le email non lette dalla casella di posta.
    """
    results: list[ParsedEmail] = []

    with imaplib.IMAP4_SSL(server) as mail:
        mail.login(username, password)
        mail.select(folder)

        _, message_numbers = mail.search(None, search_criteria)

        for num in message_numbers[0].split():
            _, msg_data = mail.fetch(num, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Decodifica subject
            subject_parts = decode_header(msg['Subject'])
            subject = ''
            for part, charset in subject_parts:
                if isinstance(part, bytes):
                    subject += part.decode(charset or 'utf-8', errors='replace')
                else:
                    subject += part

            # Decodifica sender
            sender = msg['From']
            date_str = msg['Date']

            body_text = ''
            body_html = ''
            attachments = []

            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get('Content-Disposition', ''))

                if 'attachment' in disposition:
                    filename = part.get_filename()
                    if filename:
                        decoded_name = decode_header(filename)
                        if isinstance(decoded_name[0][0], bytes):
                            filename = decoded_name[0][0].decode(decoded_name[0][1] or 'utf-8')
                        else:
                            filename = decoded_name[0][0]

                        attachment_data = part.get_payload(decode=True)
                        att_info = {'filename': filename, 'size': len(attachment_data)}

                        if download_attachments_to:
                            dest = Path(download_attachments_to)
                            dest.mkdir(parents=True, exist_ok=True)
                            file_path = dest / filename
                            file_path.write_bytes(attachment_data)
                            att_info['saved_to'] = str(file_path)

                        attachments.append(att_info)

                elif content_type == 'text/plain':
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body_text = payload.decode(charset, errors='replace')

                elif content_type == 'text/html':
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body_html = payload.decode(charset, errors='replace')

            results.append(ParsedEmail(
                subject=subject,
                sender=sender,
                date=date_str,
                body_text=body_text,
                body_html=body_html,
                attachments=attachments,
            ))

            logger.info(f"Email recuperata: {subject} da {sender}")

    return results
```

---

## Automazione Excel con openpyxl

```python
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter
from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)


def genera_report_vendite(
    dati: list[dict[str, Any]],
    output_path: str,
    titolo: str = "Report Vendite",
) -> Path:
    """
    Genera un report Excel formattato con tabella dati, formule di riepilogo
    e grafico automatico.

    Args:
        dati: lista di dizionari con chiavi 'prodotto', 'quantita', 'prezzo', 'regione'
        output_path: percorso del file Excel di output
        titolo: titolo del report

    Returns:
        Path del file generato
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Vendite"

    # Stili
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
    title_font = Font(bold=True, size=16, color="1F3864")
    currency_format = '€ #,##0.00'
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin'),
    )

    # Titolo
    ws.merge_cells('A1:E1')
    ws['A1'] = titolo
    ws['A1'].font = title_font
    ws['A1'].alignment = Alignment(horizontal='center')

    # Header
    headers = ['Prodotto', 'Regione', 'Quantità', 'Prezzo Unitario', 'Totale']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        cell.border = border

    # Dati
    for row_idx, record in enumerate(dati, 4):
        ws.cell(row=row_idx, column=1, value=record['prodotto']).border = border
        ws.cell(row=row_idx, column=2, value=record['regione']).border = border
        ws.cell(row=row_idx, column=3, value=record['quantita']).border = border

        price_cell = ws.cell(row=row_idx, column=4, value=record['prezzo'])
        price_cell.number_format = currency_format
        price_cell.border = border

        total_cell = ws.cell(row=row_idx, column=5)
        total_cell.value = f"=C{row_idx}*D{row_idx}"
        total_cell.number_format = currency_format
        total_cell.border = border

    last_data_row = len(dati) + 3
    summary_row = last_data_row + 2

    # Riepilogo
    ws.cell(row=summary_row, column=1, value="RIEPILOGO").font = Font(bold=True, size=12)
    ws.cell(row=summary_row + 1, column=1, value="Totale Quantità:")
    ws.cell(row=summary_row + 1, column=2, value=f"=SUM(C4:C{last_data_row})")
    ws.cell(row=summary_row + 2, column=1, value="Totale Vendite:")
    total_sales_cell = ws.cell(row=summary_row + 2, column=2, value=f"=SUM(E4:E{last_data_row})")
    total_sales_cell.number_format = currency_format
    total_sales_cell.font = Font(bold=True, size=12)
    ws.cell(row=summary_row + 3, column=1, value="Media per Transazione:")
    ws.cell(row=summary_row + 3, column=2, value=f"=AVERAGE(E4:E{last_data_row})")
    ws.cell(row=summary_row + 3, column=2).number_format = currency_format

    # Grafico
    chart = BarChart()
    chart.type = "col"
    chart.title = "Vendite per Prodotto"
    chart.y_axis.title = "Totale (€)"
    chart.x_axis.title = "Prodotto"
    chart.style = 10

    data_ref = Reference(ws, min_col=5, min_row=3, max_row=last_data_row)
    cats_ref = Reference(ws, min_col=1, min_row=4, max_row=last_data_row)
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats_ref)
    chart.shape = 4
    chart.width = 20
    chart.height = 12

    ws.add_chart(chart, f"A{summary_row + 6}")

    # Larghezza colonne
    for col_idx in range(1, 6):
        ws.column_dimensions[get_column_letter(col_idx)].width = 18

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(output))
    logger.info(f"Report generato: {output}")
    return output
```

---

## Generazione e Manipolazione PDF

### Generazione PDF con reportlab

```python
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)


def genera_fattura_pdf(
    dati_fattura: dict[str, Any],
    output_path: str,
) -> Path:
    """
    Genera una fattura in formato PDF.

    Args:
        dati_fattura: dizionario con chiavi 'numero', 'data', 'cliente', 'righe', 'note'
        output_path: percorso di output

    Returns:
        Path del PDF generato
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=20, spaceAfter=10 * mm)
    normal_style = styles['Normal']

    elements = []

    # Intestazione
    elements.append(Paragraph(f"Fattura N. {dati_fattura['numero']}", title_style))
    elements.append(Paragraph(f"Data: {dati_fattura['data']}", normal_style))
    elements.append(Spacer(1, 10 * mm))

    # Dati cliente
    cliente = dati_fattura['cliente']
    elements.append(Paragraph(f"<b>Cliente:</b> {cliente['nome']}", normal_style))
    elements.append(Paragraph(f"Indirizzo: {cliente['indirizzo']}", normal_style))
    elements.append(Paragraph(f"P.IVA: {cliente['piva']}", normal_style))
    elements.append(Spacer(1, 10 * mm))

    # Tabella righe
    table_data = [['Descrizione', 'Quantità', 'Prezzo Unit.', 'IVA %', 'Totale']]
    totale_imponibile = 0
    totale_iva = 0

    for riga in dati_fattura['righe']:
        imponibile = riga['quantita'] * riga['prezzo_unitario']
        iva = imponibile * riga['iva'] / 100
        totale = imponibile + iva
        totale_imponibile += imponibile
        totale_iva += iva

        table_data.append([
            riga['descrizione'],
            str(riga['quantita']),
            f"€ {riga['prezzo_unitario']:.2f}",
            f"{riga['iva']}%",
            f"€ {totale:.2f}",
        ])

    # Righe di riepilogo
    table_data.append(['', '', '', 'Imponibile:', f"€ {totale_imponibile:.2f}"])
    table_data.append(['', '', '', 'IVA:', f"€ {totale_iva:.2f}"])
    table_data.append(['', '', '', 'TOTALE:', f"€ {totale_imponibile + totale_iva:.2f}"])

    table = Table(table_data, colWidths=[70 * mm, 25 * mm, 30 * mm, 20 * mm, 30 * mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2F5496')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
        ('FONTNAME', (3, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (3, -1), (-1, -1), 12),
        ('LINEABOVE', (3, -1), (-1, -1), 1.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)

    if dati_fattura.get('note'):
        elements.append(Spacer(1, 10 * mm))
        elements.append(Paragraph(f"<b>Note:</b> {dati_fattura['note']}", normal_style))

    doc.build(elements)
    logger.info(f"Fattura PDF generata: {output_path}")
    return Path(output_path)
```

### Manipolazione PDF con PyPDF2

```python
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def merge_pdfs(input_paths: list[str], output_path: str) -> Path:
    """Unisce più file PDF in un unico file."""
    merger = PdfMerger()

    for pdf_path in input_paths:
        if Path(pdf_path).exists():
            merger.append(pdf_path)
            logger.info(f"Aggiunto: {pdf_path}")
        else:
            logger.warning(f"File non trovato, ignorato: {pdf_path}")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    merger.write(str(output))
    merger.close()

    logger.info(f"PDF unificato creato: {output}")
    return output


def split_pdf(input_path: str, output_dir: str) -> list[Path]:
    """Divide un PDF in singole pagine."""
    reader = PdfReader(input_path)
    output_base = Path(output_dir)
    output_base.mkdir(parents=True, exist_ok=True)
    result_paths = []

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        output_path = output_base / f"pagina_{i + 1:03d}.pdf"
        with open(output_path, 'wb') as f:
            writer.write(f)
        result_paths.append(output_path)

    logger.info(f"PDF diviso in {len(result_paths)} pagine")
    return result_paths


def extract_text_from_pdf(pdf_path: str) -> str:
    """Estrae il testo da tutte le pagine di un PDF."""
    reader = PdfReader(pdf_path)
    text_parts = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)

    return '\n\n'.join(text_parts)
```

---

## Automazione Documenti Word

```python
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)


def genera_report_word(
    template_path: str | None,
    output_path: str,
    dati: dict[str, Any],
) -> Path:
    """
    Genera un documento Word da un template o da zero.
    Se template_path è fornito, sostituisce i placeholder {{chiave}}.
    """
    if template_path and Path(template_path).exists():
        doc = Document(template_path)
        _replace_placeholders(doc, dati)
    else:
        doc = Document()
        _build_document(doc, dati)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output))
    logger.info(f"Documento Word generato: {output}")
    return output


def _replace_placeholders(doc: Document, dati: dict[str, Any]) -> None:
    """Sostituisce i placeholder {{chiave}} nel documento."""
    for paragraph in doc.paragraphs:
        for key, value in dati.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in paragraph.text:
                for run in paragraph.runs:
                    if placeholder in run.text:
                        run.text = run.text.replace(placeholder, str(value))

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for key, value in dati.items():
                        placeholder = f"{{{{{key}}}}}"
                        if placeholder in paragraph.text:
                            for run in paragraph.runs:
                                if placeholder in run.text:
                                    run.text = run.text.replace(placeholder, str(value))


def _build_document(doc: Document, dati: dict[str, Any]) -> None:
    """Costruisce un documento da zero con i dati forniti."""
    doc.add_heading(dati.get('titolo', 'Report'), level=0)
    doc.add_paragraph(f"Data: {dati.get('data', 'N/D')}")
    doc.add_paragraph(f"Autore: {dati.get('autore', 'N/D')}")
    doc.add_paragraph('')

    if 'sezioni' in dati:
        for sezione in dati['sezioni']:
            doc.add_heading(sezione['titolo'], level=1)
            doc.add_paragraph(sezione['contenuto'])

    if 'tabella' in dati:
        headers = dati['tabella']['headers']
        rows = dati['tabella']['rows']
        table = doc.add_table(rows=1, cols=len(headers))
        table.style = 'Light Grid Accent 1'

        for i, header in enumerate(headers):
            table.rows[0].cells[i].text = header

        for row_data in rows:
            row = table.add_row()
            for i, value in enumerate(row_data):
                row.cells[i].text = str(value)
```

---

## Web Automation con Selenium

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import time

logger = logging.getLogger(__name__)


class WebAutomator:
    """
    Classe base per automazioni web con Selenium.
    Gestisce il ciclo di vita del browser e fornisce metodi utility.
    """

    def __init__(self, headless: bool = True, download_dir: str | None = None):
        options = Options()
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')

        if download_dir:
            prefs = {
                'download.default_directory': download_dir,
                'download.prompt_for_download': False,
            }
            options.add_experimental_option('prefs', prefs)

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    def wait_and_click(self, by: By, value: str) -> None:
        element = self.wait.until(EC.element_to_be_clickable((by, value)))
        element.click()

    def wait_and_type(self, by: By, value: str, text: str, clear: bool = True) -> None:
        element = self.wait.until(EC.presence_of_element_located((by, value)))
        if clear:
            element.clear()
        element.send_keys(text)

    def wait_for_text(self, by: By, value: str, timeout: int = 30) -> str:
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element.text

    def screenshot(self, path: str) -> None:
        self.driver.save_screenshot(path)
        logger.info(f"Screenshot salvato: {path}")


def esempio_scraping_tabella(url: str) -> list[dict]:
    """Esempio di estrazione dati da una tabella HTML."""
    with WebAutomator(headless=True) as bot:
        bot.driver.get(url)
        table = bot.wait.until(EC.presence_of_element_located((By.TAG_NAME, 'table')))

        headers = [th.text for th in table.find_elements(By.TAG_NAME, 'th')]
        rows = table.find_elements(By.TAG_NAME, 'tr')[1:]

        data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if cells:
                record = {headers[i]: cells[i].text for i in range(min(len(headers), len(cells)))}
                data.append(record)

        logger.info(f"Estratte {len(data)} righe dalla tabella")
        return data
```

---

## Web Automation con Playwright

Playwright è un'alternativa moderna a Selenium, sviluppata da Microsoft, con supporto nativo per l'esecuzione asincrona e auto-wait degli elementi.

```python
from playwright.sync_api import sync_playwright, Page, Browser
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PlaywrightAutomator:
    def __init__(self, headless: bool = True):
        self._playwright = sync_playwright().start()
        self._browser: Browser = self._playwright.chromium.launch(headless=headless)
        self.page: Page = self._browser.new_page()

    def close(self) -> None:
        self._browser.close()
        self._playwright.stop()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def login(self, url: str, username_selector: str, password_selector: str,
              submit_selector: str, username: str, password: str) -> None:
        self.page.goto(url)
        self.page.fill(username_selector, username)
        self.page.fill(password_selector, password)
        self.page.click(submit_selector)
        self.page.wait_for_load_state('networkidle')
        logger.info(f"Login completato su {url}")

    def download_file(self, click_selector: str, save_path: str) -> Path:
        with self.page.expect_download() as download_info:
            self.page.click(click_selector)
        download = download_info.value
        output = Path(save_path)
        download.save_as(str(output))
        logger.info(f"File scaricato: {output}")
        return output

    def extract_table(self, table_selector: str) -> list[dict]:
        headers = self.page.eval_on_selector_all(
            f"{table_selector} th",
            "elements => elements.map(e => e.textContent.trim())"
        )
        rows = self.page.eval_on_selector_all(
            f"{table_selector} tbody tr",
            """rows => rows.map(row => {
                const cells = row.querySelectorAll('td');
                return Array.from(cells).map(c => c.textContent.trim());
            })"""
        )
        return [dict(zip(headers, row)) for row in rows]
```

---

## Pattern di Integrazione API

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import logging
from typing import Any, Generator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    base_url: str
    api_key: str
    timeout: int = 30
    max_retries: int = 3
    rate_limit_per_second: float = 10


class ResilientAPIClient:
    """
    Client API con retry automatico, rate limiting e gestione errori.
    """

    def __init__(self, config: APIConfig):
        self.config = config
        self.session = requests.Session()

        # Retry strategy con backoff esponenziale
        retry_strategy = Retry(
            total=config.max_retries,
            backoff_factor=1,  # 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "PATCH"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.session.headers.update({
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'AutomationClient/1.0',
        })

        self._last_request_time: float = 0
        self._min_interval = 1.0 / config.rate_limit_per_second

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def get(self, endpoint: str, params: dict | None = None) -> dict:
        self._rate_limit()
        url = f"{self.config.base_url}{endpoint}"
        response = self.session.get(url, params=params, timeout=self.config.timeout)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: dict) -> dict:
        self._rate_limit()
        url = f"{self.config.base_url}{endpoint}"
        response = self.session.post(url, json=data, timeout=self.config.timeout)
        response.raise_for_status()
        return response.json()

    def get_paginated(self, endpoint: str, page_param: str = 'page',
                      per_page: int = 100) -> Generator[dict, None, None]:
        """Generator che gestisce automaticamente la paginazione."""
        page = 1
        while True:
            params = {page_param: page, 'per_page': per_page}
            response = self.get(endpoint, params=params)

            data = response.get('data', response.get('results', []))
            if not data:
                break

            for item in data:
                yield item

            if len(data) < per_page:
                break

            page += 1
            logger.debug(f"Pagina {page} recuperata, {len(data)} record")
```

---

## Scheduling: APScheduler e Cron

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobExecutionEvent
import logging

logger = logging.getLogger(__name__)


def job_listener(event: JobExecutionEvent) -> None:
    if event.exception:
        logger.error(f"Job {event.job_id} fallito: {event.exception}")
    else:
        logger.info(f"Job {event.job_id} completato con successo")


def setup_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone='Europe/Rome')
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # Job giornaliero alle 08:00
    scheduler.add_job(
        func=daily_report_job,
        trigger=CronTrigger(hour=8, minute=0),
        id='daily_report',
        name='Report Giornaliero',
        misfire_grace_time=3600,
    )

    # Job ogni 15 minuti
    scheduler.add_job(
        func=check_email_job,
        trigger=IntervalTrigger(minutes=15),
        id='email_check',
        name='Controllo Email',
    )

    # Job settimanale (lunedì alle 09:00)
    scheduler.add_job(
        func=weekly_cleanup_job,
        trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
        id='weekly_cleanup',
        name='Pulizia Settimanale',
    )

    return scheduler


def daily_report_job():
    logger.info("Esecuzione report giornaliero")
    # Logica del report


def check_email_job():
    logger.info("Controllo nuove email")
    # Logica controllo email


def weekly_cleanup_job():
    logger.info("Pulizia settimanale")
    # Logica pulizia


if __name__ == '__main__':
    scheduler = setup_scheduler()
    logger.info("Scheduler avviato")
    scheduler.start()
```

Per l'integrazione con cron di sistema, il file crontab:

```cron
# Crontab per automazioni Python
# m h dom mon dow command

# Report giornaliero alle 08:00
0 8 * * * /opt/automation/venv/bin/python /opt/automation/scripts/daily_report.py >> /var/log/automation/daily_report.log 2>&1

# Controllo email ogni 15 minuti
*/15 * * * * /opt/automation/venv/bin/python /opt/automation/scripts/check_email.py >> /var/log/automation/email_check.log 2>&1

# Pulizia settimanale (lunedì alle 09:00)
0 9 * * 1 /opt/automation/venv/bin/python /opt/automation/scripts/weekly_cleanup.py >> /var/log/automation/cleanup.log 2>&1
```

---

## Database Automation con SQLAlchemy

```python
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Fattura(Base):
    __tablename__ = 'fatture'
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(String(50), unique=True, nullable=False)
    fornitore = Column(String(200), nullable=False)
    importo = Column(Float, nullable=False)
    data_emissione = Column(DateTime, nullable=False)
    data_inserimento = Column(DateTime, default=datetime.utcnow)
    stato = Column(String(20), default='nuovo')


class DatabaseManager:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string, pool_pre_ping=True, pool_size=5)
        Base.metadata.create_all(self.engine)
        self._SessionFactory = sessionmaker(bind=self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session = self._SessionFactory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def inserisci_fattura(self, numero: str, fornitore: str,
                          importo: float, data_emissione: datetime) -> Fattura:
        with self.session() as s:
            fattura = Fattura(
                numero=numero,
                fornitore=fornitore,
                importo=importo,
                data_emissione=data_emissione,
            )
            s.add(fattura)
            s.flush()
            logger.info(f"Fattura inserita: {numero}")
            return fattura

    def cerca_fatture(self, stato: str | None = None,
                      fornitore: str | None = None) -> list[Fattura]:
        with self.session() as s:
            query = s.query(Fattura)
            if stato:
                query = query.filter(Fattura.stato == stato)
            if fornitore:
                query = query.filter(Fattura.fornitore.ilike(f'%{fornitore}%'))
            return query.all()
```

---

## Sistemi di Notifica

### Slack Webhook

```python
import requests
import logging

logger = logging.getLogger(__name__)


def send_slack_notification(
    webhook_url: str,
    message: str,
    channel: str | None = None,
    username: str = "Automation Bot",
    color: str = "#36a64f",
    fields: list[dict] | None = None,
) -> None:
    payload = {
        "username": username,
        "attachments": [{
            "color": color,
            "text": message,
            "ts": __import__('time').time(),
        }],
    }

    if channel:
        payload["channel"] = channel

    if fields:
        payload["attachments"][0]["fields"] = fields

    response = requests.post(webhook_url, json=payload, timeout=10)
    response.raise_for_status()
    logger.info(f"Notifica Slack inviata: {message[:50]}...")
```

### Telegram Bot API

```python
import requests
import logging

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, default_chat_id: str):
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.default_chat_id = default_chat_id

    def send_message(self, text: str, chat_id: str | None = None,
                     parse_mode: str = "HTML") -> dict:
        response = requests.post(
            f"{self.base_url}/sendMessage",
            json={
                "chat_id": chat_id or self.default_chat_id,
                "text": text,
                "parse_mode": parse_mode,
            },
            timeout=10,
        )
        response.raise_for_status()
        logger.info(f"Messaggio Telegram inviato: {text[:50]}...")
        return response.json()

    def send_document(self, file_path: str, caption: str = "",
                      chat_id: str | None = None) -> dict:
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/sendDocument",
                data={
                    "chat_id": chat_id or self.default_chat_id,
                    "caption": caption,
                },
                files={"document": f},
                timeout=30,
            )
        response.raise_for_status()
        logger.info(f"Documento Telegram inviato: {file_path}")
        return response.json()
```

---

## Progetto Completo: Pipeline di Reportistica Automatizzata

Questo progetto combina diverse librerie per creare una pipeline end-to-end che recupera dati da un'API, li processa, genera un report Excel e PDF, e invia il risultato via email e Slack.

```python
"""
Pipeline di reportistica automatizzata.
Esecuzione giornaliera: recupera dati vendite, genera report, distribuisce.
"""
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/automation/report_pipeline.log'),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger('report_pipeline')


def run_pipeline():
    """Esegue l'intera pipeline di reportistica."""
    logger.info("=== Inizio pipeline reportistica ===")
    report_date = datetime.now().strftime('%Y-%m-%d')
    output_dir = Path(f'/opt/reports/{report_date}')
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Recupera dati dall'API
        logger.info("Fase 1: Recupero dati")
        # client = ResilientAPIClient(config)
        # dati = list(client.get_paginated('/api/vendite', per_page=100))

        # 2. Genera report Excel
        logger.info("Fase 2: Generazione report Excel")
        # excel_path = genera_report_vendite(dati, str(output_dir / 'report_vendite.xlsx'))

        # 3. Genera report PDF
        logger.info("Fase 3: Generazione report PDF")
        # pdf_path = genera_fattura_pdf(dati_fattura, str(output_dir / 'riepilogo.pdf'))

        # 4. Invio email
        logger.info("Fase 4: Distribuzione via email")
        # send_email(email_config, to=['team@company.com'], subject=f'Report {report_date}',
        #            body_html=html_body, attachments=[str(excel_path), str(pdf_path)])

        # 5. Notifica Slack
        logger.info("Fase 5: Notifica Slack")
        # send_slack_notification(webhook_url, f"Report {report_date} generato con successo")

        logger.info("=== Pipeline completata con successo ===")

    except Exception as e:
        logger.error(f"Pipeline fallita: {e}", exc_info=True)
        # send_slack_notification(webhook_url, f"ERRORE pipeline report: {e}", color="#ff0000")
        raise


if __name__ == '__main__':
    run_pipeline()
```

---

## Progetto Completo: Sistema di Monitoring con Alert

```python
"""
Sistema di monitoring che controlla lo stato di servizi web
e invia alert graduali in base alla severità.
"""
import requests
import time
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger('monitoring')


@dataclass
class ServiceCheck:
    name: str
    url: str
    expected_status: int = 200
    timeout: int = 10
    consecutive_failures: int = 0
    last_check: datetime | None = None
    last_status: str = "unknown"


@dataclass
class MonitoringSystem:
    services: list[ServiceCheck] = field(default_factory=list)
    alert_thresholds: dict[int, str] = field(default_factory=lambda: {
        1: "warning",    # Primo fallimento: warning
        3: "critical",   # 3 consecutivi: critical
        5: "emergency",  # 5 consecutivi: emergency
    })

    def check_all(self) -> list[dict]:
        results = []
        for service in self.services:
            result = self._check_service(service)
            results.append(result)
            if result['status'] == 'down':
                self._handle_failure(service)
            else:
                if service.consecutive_failures > 0:
                    logger.info(f"{service.name}: recuperato dopo {service.consecutive_failures} fallimenti")
                service.consecutive_failures = 0
                service.last_status = "up"
        return results

    def _check_service(self, service: ServiceCheck) -> dict:
        try:
            start = time.time()
            response = requests.get(service.url, timeout=service.timeout)
            duration = time.time() - start

            if response.status_code == service.expected_status:
                return {
                    'name': service.name,
                    'status': 'up',
                    'response_time': round(duration, 3),
                    'status_code': response.status_code,
                }
            else:
                return {
                    'name': service.name,
                    'status': 'down',
                    'reason': f"HTTP {response.status_code}",
                }
        except requests.exceptions.Timeout:
            return {'name': service.name, 'status': 'down', 'reason': 'timeout'}
        except requests.exceptions.ConnectionError:
            return {'name': service.name, 'status': 'down', 'reason': 'connection_error'}

    def _handle_failure(self, service: ServiceCheck) -> None:
        service.consecutive_failures += 1
        service.last_status = "down"
        logger.warning(f"{service.name}: fallimento #{service.consecutive_failures}")

        for threshold, severity in sorted(self.alert_thresholds.items()):
            if service.consecutive_failures == threshold:
                self._send_alert(service, severity)
                break

    def _send_alert(self, service: ServiceCheck, severity: str) -> None:
        message = (
            f"[{severity.upper()}] {service.name} non raggiungibile\n"
            f"URL: {service.url}\n"
            f"Fallimenti consecutivi: {service.consecutive_failures}"
        )
        logger.critical(message)
        # Integrare con Slack/Telegram/PagerDuty
```

---

## Best Practices

### Struttura del Progetto

1. **Virtual environment dedicato**: ogni progetto di automazione deve avere il proprio virtual environment con le dipendenze pinned in `requirements.txt`.
2. **Configurazione esternalizzata**: mai hardcodare credenziali o parametri nel codice. Utilizzare variabili di ambiente o file `.env` (con `python-dotenv`).
3. **Logging strutturato**: configurare il logging con file rotation per ogni script di automazione.
4. **Idempotenza**: progettare le automazioni in modo che possano essere eseguite più volte senza effetti collaterali indesiderati.

### Robustezza

5. **Timeout su ogni operazione di rete**: mai lasciare una richiesta HTTP o una connessione database senza timeout.
6. **Retry con backoff**: per le operazioni che possono fallire temporaneamente (API, email, database), implementare retry con backoff esponenziale.
7. **Graceful degradation**: se un componente non critico fallisce, l'automazione deve continuare con gli altri componenti e notificare l'errore.
8. **Gestione dei file temporanei**: utilizzare `tempfile` per i file temporanei e assicurarsi di pulirli in un blocco `finally`.

### Sicurezza

9. **Mai archiviare credenziali nel codice**: usare variabili di ambiente, file `.env` (esclusi da git), o sistemi di secrets management.
10. **Validare tutti gli input**: anche nelle automazioni interne, validare i dati in ingresso per prevenire injection e corruzione dei dati.
11. **Principio del minimo privilegio**: le credenziali utilizzate dalle automazioni devono avere solo i permessi strettamente necessari.

---

## Troubleshooting

### Problema: Selenium Non Trova gli Elementi

**Sintomi**: `NoSuchElementException` o `TimeoutException` anche quando l'elemento è visibile nel browser.

**Causa**: l'elemento potrebbe essere dentro un iframe, caricato dinamicamente via JavaScript, o avere un selettore che cambia tra le esecuzioni.

**Soluzione**: verificare la presenza di iframe con `driver.switch_to.frame()`. Utilizzare WebDriverWait con condizioni esplicite anziché `find_element` diretto. Per elementi dinamici, utilizzare selettori CSS o XPath più robusti basati su attributi stabili (`data-testid`, `aria-label`).

### Problema: Email Non Arrivano al Destinatario

**Sintomi**: `smtplib` non genera errori ma le email non vengono ricevute.

**Causa**: il server SMTP potrebbe richiedere autenticazione specifica (OAuth2 per Gmail), le email potrebbero finire in spam, o il server potrebbe avere rate limiting.

**Soluzione**: per Gmail, utilizzare un "App Password" anziché la password principale. Configurare correttamente i record SPF e DKIM del dominio. Verificare la cartella spam del destinatario. Aggiungere header `Reply-To` e `Return-Path` corretti.

### Problema: openpyxl Non Legge Formule

**Sintomi**: le celle con formule restituiscono `None` anziché il valore calcolato.

**Causa**: `openpyxl` legge le formule come stringhe (es. `=SUM(A1:A10)`), non i valori calcolati, a meno che non si usi `data_only=True`.

**Soluzione**: aprire il workbook con `load_workbook(path, data_only=True)`. Nota: questo funziona solo se il file è stato precedentemente aperto e salvato con Excel (che calcola le formule). Per file mai aperti con Excel, i valori calcolati non sono disponibili.

---

## Riferimenti

- **Python pathlib**: https://docs.python.org/3/library/pathlib.html
- **watchdog**: https://python-watchdog.readthedocs.io/
- **openpyxl**: https://openpyxl.readthedocs.io/
- **reportlab**: https://docs.reportlab.com/
- **PyPDF2**: https://pypdf2.readthedocs.io/
- **python-docx**: https://python-docx.readthedocs.io/
- **Selenium**: https://www.selenium.dev/documentation/
- **Playwright Python**: https://playwright.dev/python/docs/intro
- **requests**: https://requests.readthedocs.io/
- **APScheduler**: https://apscheduler.readthedocs.io/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Slack Webhooks**: https://api.slack.com/messaging/webhooks
- **Telegram Bot API**: https://core.telegram.org/bots/api

---

## Letture e Riferimenti

### Documentazione ufficiale

- uv — Python Package Manager Documentation: https://docs.astral.sh/uv/ (consultato: 2026-05-24)
- Pydantic v2 — Documentation: https://docs.pydantic.dev/latest/ (consultato: 2026-05-24)
- httpx — Async Client Guide: https://www.python-httpx.org/async/ (consultato: 2026-05-24)
- structlog — Getting Started: https://www.structlog.org/en/stable/getting-started.html (consultato: 2026-05-24)
- OpenTelemetry Python SDK: https://opentelemetry.io/docs/languages/python/ (consultato: 2026-05-24)
- Click — CLI Creation Kit: https://click.palletsprojects.com/en/stable/ (consultato: 2026-05-24)
- PEP 621 — Storing project metadata in pyproject.toml: https://peps.python.org/pep-0621/ (consultato: 2026-05-24)

### Libri

- **"Robust Python"** — Patrick Viafore (O'Reilly). Type hints, Pydantic, e tecniche per codice Python production-grade — direttamente applicabile alla struttura di automazioni robuste.
- **"Python for DevOps"** — Noah Gift, Kennedy Behrman, Alfredo Deza, Grig Gheorghiu (O'Reilly). Automazione, testing, packaging e deployment di strumenti Python in contesti operativi.

---

## Esercizi

1. **Lab — automation tool with uv + click.** Crea CLI Python con uv, click 5 sotto-comandi, structlog JSON, packaging via `uv build`, deploy come service systemd.
2. **Lab — async API client.** httpx async con concurrency 10, retry exponential backoff, rate limit handling.
3. **Stretch — OpenTelemetry instrumentation.** Aggiungi traces + metrics al CLI del lab 1; export su Jaeger.

## Auto-valutazione

1. uv vs pip vs poetry: differenze.
2. Pydantic v2: cosa cambia rispetto a v1?
3. httpx async: come strutturare?
4. structlog: setup minimo per JSON logging.
5. PEP 621: cosa standardizza?

## Collegamenti incrociati

- Modulo 03 — `03-scripting-automazione.md`: scripting fundamentals.
- Modulo `../04-PROGRAMMAZIONE-PYTHON/`: deep Python.

## Glossario locale

| Termine | Definizione |
|---|---|
| **uv** | Python package manager veloce (Rust-based). |
| **`pyproject.toml`** | Configuration file PEP 621. |
| **httpx** | Async HTTP client moderno. |
| **Pydantic v2** | Data validation library, Rust-core. |
| **structlog** | Structured logging library. |
| **OTel SDK** | OpenTelemetry SDK per Python. |
