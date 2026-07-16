# Tutorial Lab — Python per l'Automazione Avanzata

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `12-python-automazione-avanzata.md`
> **Livello:** competent → proficient
> **Tempo stimato:** 7-8 ore (lab completo)
> **Prerequisiti:** Python 3.11+ intermedio, pip/uv basics, concetto async/await
> **Versioni di riferimento:** Python 3.11+ · uv 0.4+ · httpx 0.27 · Pydantic v2 · structlog · APScheduler 3.x · Playwright

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Strutturare un progetto di automazione production-grade con `uv` e `pyproject.toml`
2. Implementare client HTTP asincroni con `httpx`, retry intelligente e rate limiting
3. Monitorare il file system in tempo reale con `watchdog`
4. Automatizzare file Excel con `openpyxl` e generare PDF con `reportlab`
5. Eseguire web automation con Playwright (headless browser)
6. Schedulare task con APScheduler e deployarli come servizi systemd
7. Implementare structured logging con `structlog` e tracing OpenTelemetry

---

## Lab Environment Setup

### Installazione uv (package manager moderno)

```bash
# uv: più veloce di pip, lock file deterministico, virtual env automatico
curl -LsSf https://astral.sh/uv/install.sh | sh
# oppure su Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verifica installazione
uv --version
# Output: uv 0.4.x
```

### Setup Progetto con pyproject.toml

```bash
# Crea progetto
uv init automation-lab
cd automation-lab

# Struttura progetto
mkdir -p src/automation/{file_ops,http_client,excel,pdf,browser,scheduler,logging}
mkdir -p tests/
touch src/automation/__init__.py
```

```toml
# pyproject.toml
[project]
name = "automation-lab"
version = "0.1.0"
description = "Framework di automazione production-grade"
requires-python = ">=3.11"
dependencies = [
    "httpx[http2]>=0.27.0",
    "pydantic>=2.0.0",
    "structlog>=24.0.0",
    "watchdog>=4.0.0",
    "openpyxl>=3.1.0",
    "reportlab>=4.0.0",
    "playwright>=1.43.0",
    "apscheduler>=3.10.0",
    "tenacity>=8.3.0",
    "redis>=5.0.0",
    "opentelemetry-sdk>=1.24.0",
    "opentelemetry-exporter-otlp>=1.24.0",
]

[project.scripts]
automation = "automation.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "mypy>=1.9.0",
    "ruff>=0.4.0",
]
```

```bash
# Installa tutto
uv sync

# Installa browser per Playwright
uv run playwright install chromium
```

### Script di Verifica Prerequisiti

```bash
#!/bin/bash
# check-prereqs-python.sh
echo "=== Verifica prerequisiti Python Automation Lab ==="

uv --version || { echo "uv non trovato — installare da https://astral.sh/uv"; exit 1; }
python3 --version

echo "--- Librerie Python ---"
uv run python -c "
import httpx, pydantic, structlog, watchdog, openpyxl, reportlab
import apscheduler, tenacity, redis
print('Tutte le librerie core presenti')
"

echo "--- Playwright ---"
uv run playwright --version || echo "Playwright non installato — run: uv run playwright install chromium"

echo "--- Spazio disco ---"
df -h . | tail -1

echo "=== Pronto per il lab ==="
```

---

## Analogia Introduttiva

> **Python per l'automazione è come un factotum onnisciente**:
> può aprire file (file system), compilare moduli (web automation),
> inviare fax (HTTP API), fotocopiare documenti (Excel/PDF),
> e soprattutto farlo in orari prestabiliti senza che tu debba alzarti.
>
> La differenza tra uno script Python "per casa" e uno "production-grade":
> - Casa: `print("errore")` e il programma muore in silenzio
> - Produzione: log strutturati, retry automatico, alert su Slack,
>   servizio systemd che si riavvia in caso di crash

---

## PART A — File System Automation

### A1 — Organizzazione File con pathlib

```python
# src/automation/file_ops/organizer.py
"""
Organizza file in sottocartelle per data/estensione.
Use case: archivio automatico di fatture, report, backup.
"""
from __future__ import annotations

import hashlib
import shutil
import structlog
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = structlog.get_logger(__name__)


@dataclass
class OrganizationResult:
    moved: int = 0
    skipped: int = 0
    errors: int = 0
    duplicate_groups: list[list[Path]] = field(default_factory=list)


def organizza_file_per_data(
    source_dir: Path,
    dest_base: Path,
    extensions: Optional[set[str]] = None,
    dry_run: bool = False
) -> OrganizationResult:
    """
    Organizza i file di una directory in sottocartelle anno/mese/giorno
    basate sulla data di modifica del file.

    Args:
        source_dir: directory sorgente
        dest_base:  directory base di destinazione
        extensions: set estensioni da includere (None = tutte)
        dry_run:    simula senza spostare file
    """
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Directory sorgente non trovata: {source_dir}")

    result = OrganizationResult()
    log = logger.bind(source=str(source_dir), dest=str(dest_base))

    for file_path in sorted(source_dir.iterdir()):
        if not file_path.is_file():
            continue

        if extensions and file_path.suffix.lower() not in extensions:
            result.skipped += 1
            continue

        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        dest_dir = dest_base / f"{mod_time.year}" / f"{mod_time.month:02d}" / f"{mod_time.day:02d}"

        dest_file = dest_dir / file_path.name
        if dest_file.exists():
            # Evita sovrascrittura — aggiungi timestamp
            stem = file_path.stem
            suffix = file_path.suffix
            dest_file = dest_dir / f"{stem}_{mod_time.strftime('%H%M%S')}{suffix}"

        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file_path), str(dest_file))

        log.info("file_moved", file=file_path.name, dest=str(dest_dir), dry_run=dry_run)
        result.moved += 1

    return result


def trova_duplicati(directory: Path, chunk_size: int = 8192) -> dict[str, list[Path]]:
    """
    Trova file duplicati calcolando SHA-256 (approccio a due fasi per efficienza).
    Fase 1: raggruppa per dimensione (O(n))
    Fase 2: calcola hash solo per file stessa dimensione (minimizza I/O)
    """
    size_groups: dict[int, list[Path]] = {}

    for file_path in directory.rglob("*"):
        if file_path.is_file():
            size = file_path.stat().st_size
            size_groups.setdefault(size, []).append(file_path)

    duplicates: dict[str, list[Path]] = {}

    for size, paths in size_groups.items():
        if len(paths) <= 1:
            continue  # nessun duplicato possibile per questa dimensione

        hash_groups: dict[str, list[Path]] = {}
        for path in paths:
            file_hash = _compute_sha256(path, chunk_size)
            hash_groups.setdefault(file_hash, []).append(path)

        for file_hash, dup_paths in hash_groups.items():
            if len(dup_paths) > 1:
                duplicates[file_hash] = dup_paths

    return duplicates


def _compute_sha256(path: Path, chunk_size: int = 8192) -> str:
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()
```

```python
# test: usa il codice
from pathlib import Path
from src.automation.file_ops.organizer import organizza_file_per_data, trova_duplicati

# Test organizzazione
result = organizza_file_per_data(
    source_dir=Path("/tmp/fatture_disorganizzate"),
    dest_base=Path("/tmp/archivio"),
    extensions={".pdf", ".xml", ".xlsx"},
    dry_run=True  # Simula prima di eseguire
)
print(f"Spostati: {result.moved}, Saltati: {result.skipped}")
```

### A2 — Monitoraggio File in Tempo Reale (watchdog)

```python
# src/automation/file_ops/watcher.py
"""
Monitora una directory e processa automaticamente i nuovi file.
Use case: fatture che arrivano in una cartella → process automatico.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import structlog
from watchdog.events import FileCreatedEvent, FileMovedEvent, FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = structlog.get_logger(__name__)


class FattureWatcher(FileSystemEventHandler):
    """
    Monitora una directory per nuovi file e chiama un handler.
    Pattern: new file → validate → process → move to archive
    """

    def __init__(
        self,
        watch_dir: Path,
        process_fn: Callable[[Path], None],
        extensions: set[str] = frozenset({".pdf", ".xml"}),
        stable_wait_seconds: float = 1.0,
    ):
        self.watch_dir = watch_dir
        self.process_fn = process_fn
        self.extensions = extensions
        self.stable_wait = stable_wait_seconds
        self._processing: set[str] = set()

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self._handle_new_file(Path(event.src_path))

    def on_moved(self, event: FileSystemEvent) -> None:
        """Gestisce anche file spostati nella directory (move atomico)."""
        if isinstance(event, FileMovedEvent) and not event.is_directory:
            self._handle_new_file(Path(event.dest_path))

    def _handle_new_file(self, file_path: Path) -> None:
        if file_path.suffix.lower() not in self.extensions:
            return
        if str(file_path) in self._processing:
            return  # Evita doppio processing (watchdog può generare eventi multipli)

        self._processing.add(str(file_path))
        log = logger.bind(file=file_path.name)

        try:
            # Attendi che il file sia completamente scritto
            self._wait_for_stable(file_path)
            log.info("new_file_detected")
            self.process_fn(file_path)
            log.info("file_processed_ok")
        except Exception as e:
            log.error("file_processing_failed", error=str(e), exc_info=True)
        finally:
            self._processing.discard(str(file_path))

    def _wait_for_stable(self, path: Path, checks: int = 3) -> None:
        """
        Aspetta che la dimensione del file non cambi per N controlli consecutivi.
        Previene processing di file ancora in scrittura.
        """
        prev_size = -1
        for _ in range(checks):
            time.sleep(self.stable_wait)
            if not path.exists():
                raise FileNotFoundError(f"File scomparso: {path}")
            curr_size = path.stat().st_size
            if curr_size == prev_size:
                return
            prev_size = curr_size
        # Dopo N check se la dimensione continua a cambiare, proviamo comunque
        logger.warning("file_still_growing", file=path.name, size=prev_size)


def avvia_monitoraggio(
    watch_dir: Path,
    process_fn: Callable[[Path], None],
    extensions: set[str] = frozenset({".pdf", ".xml"}),
) -> None:
    """
    Avvia il monitoraggio della directory e blocca finché non viene interrotto.
    Gestisce SIGINT/SIGTERM per shutdown pulito.
    """
    watch_dir.mkdir(parents=True, exist_ok=True)
    handler = FattureWatcher(watch_dir, process_fn, extensions)
    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=False)
    observer.start()
    logger.info("watcher_started", directory=str(watch_dir))

    try:
        while observer.is_alive():
            observer.join(timeout=1)
    except KeyboardInterrupt:
        logger.info("watcher_stopping")
    finally:
        observer.stop()
        observer.join()
        logger.info("watcher_stopped")


# Esempio di utilizzo
if __name__ == "__main__":
    def process_fattura(path: Path) -> None:
        print(f"Processando fattura: {path.name}")
        # Qui: parse XML SDI, validazione, inserimento DB, invio notifica

    avvia_monitoraggio(
        watch_dir=Path("/opt/inbox/fatture"),
        process_fn=process_fattura,
        extensions={".xml", ".p7m"}
    )
```

---

## PART B — HTTP Client Asincrono con Retry

### B1 — Client httpx con Tenacity

```python
# src/automation/http_client/api_client.py
"""
Client HTTP asincrono production-grade:
- Retry con exponential backoff (tenacity)
- Rate limiting (token bucket)
- Connection pooling
- Structured logging con correlation ID
"""
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx
import structlog
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger(__name__)


@dataclass
class RateLimiter:
    """Token bucket per rate limiting."""
    max_tokens: float          # es. 10 richieste al secondo
    refill_rate: float         # token per secondo
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)

    def __post_init__(self) -> None:
        self._tokens = self.max_tokens
        self._last_refill = time.monotonic()

    async def acquire(self) -> None:
        """Aspetta finché non c'è un token disponibile."""
        while True:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self.max_tokens, self._tokens + elapsed * self.refill_rate)
            self._last_refill = now

            if self._tokens >= 1:
                self._tokens -= 1
                return
            wait_time = (1 - self._tokens) / self.refill_rate
            await asyncio.sleep(wait_time)


def is_retriable_error(exc: Exception) -> bool:
    """Determina se un'eccezione è retriable."""
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.ConnectError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {429, 500, 502, 503, 504}
    return False


class ApiClient:
    """
    Client HTTP asincrono con retry, rate limiting e tracing.
    Gestisce session (connection pool) e headers comuni.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout_seconds: float = 30.0,
        rate_limit_per_second: float = 10.0,
    ):
        self.base_url = base_url
        self.rate_limiter = RateLimiter(
            max_tokens=rate_limit_per_second,
            refill_rate=rate_limit_per_second
        )
        self.timeout = httpx.Timeout(timeout_seconds, connect=5.0)
        self.max_retries = max_retries

        headers = {"User-Agent": "automation-lab/1.0", "Accept": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=self.timeout,
            http2=True,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

    async def __aenter__(self) -> "ApiClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.aclose()

    async def get(self, path: str, **kwargs: Any) -> dict:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> dict:
        return await self._request("POST", path, **kwargs)

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        correlation_id = str(uuid.uuid4())[:8]
        log = logger.bind(method=method, path=path, correlation_id=correlation_id)

        await self.rate_limiter.acquire()

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=30),
            retry=retry_if_exception(is_retriable_error),
            reraise=True,
        ):
            with attempt:
                attempt_num = attempt.retry_state.attempt_number
                if attempt_num > 1:
                    log.warning("retry_attempt", attempt=attempt_num)

                start = time.monotonic()
                try:
                    response = await self._client.request(
                        method,
                        path,
                        headers={"X-Correlation-ID": correlation_id},
                        **kwargs
                    )
                    duration_ms = (time.monotonic() - start) * 1000

                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", "5"))
                        log.warning("rate_limited", retry_after=retry_after)
                        await asyncio.sleep(retry_after)
                        response.raise_for_status()

                    response.raise_for_status()
                    log.info("request_ok", status=response.status_code, duration_ms=round(duration_ms))
                    return response.json()

                except httpx.HTTPStatusError as e:
                    log.error("http_error", status=e.response.status_code, body=e.response.text[:200])
                    raise
                except httpx.TimeoutException:
                    log.error("request_timeout", duration_ms=round((time.monotonic() - start) * 1000))
                    raise


# ─── Funzione helper: paginated fetch ─────────────────────────────────────────

async def fetch_all_pages(
    client: ApiClient,
    path: str,
    page_size: int = 100,
    max_pages: int = 100,
) -> list[dict]:
    """
    Recupera tutte le pagine di un endpoint paginato.
    Supporta sia cursor-based che page-based pagination.
    """
    all_items: list[dict] = []
    page = 1
    cursor: Optional[str] = None

    for _ in range(max_pages):
        params: dict[str, Any] = {"limit": page_size}
        if cursor:
            params["cursor"] = cursor
        else:
            params["page"] = page

        data = await client.get(path, params=params)

        items = data.get("data") or data.get("results") or data.get("items") or []
        all_items.extend(items)

        # Aggiorna cursor per pagina successiva
        next_cursor = (
            data.get("meta", {}).get("next_cursor")
            or data.get("pagination", {}).get("next_cursor")
        )
        if next_cursor:
            cursor = next_cursor
        elif data.get("meta", {}).get("has_next") is False:
            break
        elif len(items) < page_size:
            break  # ultima pagina (incompleta)
        else:
            page += 1

    logger.info("pagination_complete", total_items=len(all_items), pages=page)
    return all_items


# ─── Esempio di utilizzo ──────────────────────────────────────────────────────

async def example_usage() -> None:
    async with ApiClient(
        base_url="https://api.example.com",
        api_key="your_api_key_here",
        rate_limit_per_second=5.0,
    ) as client:
        # Fetch singolo
        user = await client.get("/v1/users/123")
        print(f"Utente: {user}")

        # Fetch paginato
        all_orders = await fetch_all_pages(client, "/v1/orders", page_size=50)
        print(f"Ordini totali: {len(all_orders)}")

if __name__ == "__main__":
    asyncio.run(example_usage())
```

---

## PART C — Automazione Excel e PDF

### C1 — Report Excel Automatizzato

```python
# src/automation/excel/report_generator.py
"""
Genera report Excel con formattazione professionale.
Use case: report vendite mensile per management.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


@dataclass
class VenditeMensili:
    mese: str
    fatturato: float
    margine: float
    ordini: int
    top_prodotto: str


# Palette colori aziendale
COLORS = {
    "header_bg": "1F4E79",    # Blu scuro
    "header_fg": "FFFFFF",    # Bianco
    "row_alt": "EBF3FB",      # Azzurro chiaro (righe alternate)
    "total_bg": "D6E4F0",     # Azzurro medio (riga totale)
    "positive": "1E8449",     # Verde
    "negative": "C0392B",     # Rosso
}

BORDER_THIN = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)


def genera_report_vendite(
    data: list[VenditeMensili],
    output_path: Path,
    anno: int,
) -> Path:
    """
    Genera un report Excel professionale delle vendite mensili.
    Include: tabella dati, totali, grafico, foglio raw data.
    """
    wb = openpyxl.Workbook()

    # ── Foglio 1: Report Visivo ──────────────────────────────────────────────
    ws = wb.active
    ws.title = f"Vendite {anno}"

    # Titolo
    ws.merge_cells("A1:F1")
    title_cell = ws["A1"]
    title_cell.value = f"Report Vendite Annuale {anno}"
    title_cell.font = Font(name="Calibri", size=16, bold=True, color=COLORS["header_fg"])
    title_cell.fill = PatternFill("solid", fgColor=COLORS["header_bg"])
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    # Header tabella
    headers = ["Mese", "Fatturato (€)", "Margine (€)", "% Margine", "Ordini", "Top Prodotto"]
    ws.row_dimensions[2].height = 20
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=col, value=header)
        cell.font = Font(bold=True, color=COLORS["header_fg"])
        cell.fill = PatternFill("solid", fgColor=COLORS["header_bg"])
        cell.alignment = Alignment(horizontal="center")
        cell.border = BORDER_THIN

    # Dati
    totale_fatturato = 0.0
    totale_margine = 0.0
    totale_ordini = 0

    for row_idx, mese in enumerate(data, start=3):
        pct_margine = (mese.margine / mese.fatturato * 100) if mese.fatturato else 0

        values: list[Any] = [
            mese.mese,
            mese.fatturato,
            mese.margine,
            pct_margine / 100,   # Excel formatta come % automaticamente
            mese.ordini,
            mese.top_prodotto
        ]

        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col, value=value)
            cell.border = BORDER_THIN

            # Formattazione alternata righe
            if row_idx % 2 == 0:
                cell.fill = PatternFill("solid", fgColor=COLORS["row_alt"])

            # Formattazione specifica per colonna
            if col == 2:  # Fatturato
                cell.number_format = '#,##0.00 "€"'
                totale_fatturato += mese.fatturato
            elif col == 3:  # Margine
                cell.number_format = '#,##0.00 "€"'
                totale_margine += mese.margine
                # Colora verde/rosso in base al valore
                cell.font = Font(
                    color=COLORS["positive"] if mese.margine >= 0 else COLORS["negative"]
                )
            elif col == 4:  # % Margine
                cell.number_format = "0.0%"
            elif col == 5:  # Ordini
                totale_ordini += mese.ordini

    # Riga totali
    total_row = len(data) + 3
    totals = ["TOTALE", totale_fatturato, totale_margine,
              totale_margine / totale_fatturato if totale_fatturato else 0,
              totale_ordini, ""]

    for col, value in enumerate(totals, start=1):
        cell = ws.cell(row=total_row, column=col, value=value)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor=COLORS["total_bg"])
        cell.border = BORDER_THIN
        if col == 2:
            cell.number_format = '#,##0.00 "€"'
        elif col == 3:
            cell.number_format = '#,##0.00 "€"'
        elif col == 4:
            cell.number_format = "0.0%"

    # Larghezza colonne auto
    col_widths = [12, 18, 16, 12, 10, 25]
    for col, width in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(col)].width = width

    # ── Grafico BarChart ──────────────────────────────────────────────────────
    chart = BarChart()
    chart.type = "col"
    chart.title = f"Fatturato Mensile {anno}"
    chart.y_axis.title = "€"
    chart.x_axis.title = "Mese"
    chart.style = 10
    chart.width = 20
    chart.height = 12

    data_ref = Reference(ws, min_col=2, max_col=3,
                         min_row=2, max_row=len(data) + 2)
    categories = Reference(ws, min_col=1, min_row=3, max_row=len(data) + 2)
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(categories)

    ws.add_chart(chart, f"A{total_row + 2}")

    # ── Foglio 2: Raw Data ────────────────────────────────────────────────────
    ws_raw = wb.create_sheet("Raw Data")
    ws_raw.append(["mese", "fatturato", "margine", "ordini", "top_prodotto"])
    for mese in data:
        ws_raw.append([mese.mese, mese.fatturato, mese.margine, mese.ordini, mese.top_prodotto])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path


# Demo
if __name__ == "__main__":
    import random
    test_data = [
        VenditeMensili(f"{m:02d}/{2026}", random.uniform(80000, 200000),
                       random.uniform(15000, 45000), random.randint(120, 400),
                       random.choice(["Prodotto A", "Prodotto B", "Prodotto C"]))
        for m in range(1, 13)
    ]
    path = genera_report_vendite(test_data, Path("/tmp/report_vendite_2026.xlsx"), 2026)
    print(f"Report generato: {path}")
```

### C2 — Generazione PDF con reportlab

```python
# src/automation/pdf/fattura_generator.py
"""
Genera PDF di fatture/preventivi con reportlab.
Use case: automazione fatturazione per PMI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)


@dataclass
class RigaFattura:
    descrizione: str
    quantita: float
    prezzo_unitario: float
    aliquota_iva: float = 0.22

    @property
    def imponibile(self) -> float:
        return self.quantita * self.prezzo_unitario

    @property
    def iva(self) -> float:
        return self.imponibile * self.aliquota_iva

    @property
    def totale(self) -> float:
        return self.imponibile + self.iva


@dataclass
class Fattura:
    numero: str
    data: date
    cliente_nome: str
    cliente_piva: str
    cliente_indirizzo: str
    righe: list[RigaFattura] = field(default_factory=list)
    note: Optional[str] = None

    @property
    def totale_imponibile(self) -> float:
        return sum(r.imponibile for r in self.righe)

    @property
    def totale_iva(self) -> float:
        return sum(r.iva for r in self.righe)

    @property
    def totale_fattura(self) -> float:
        return sum(r.totale for r in self.righe)


def genera_pdf_fattura(fattura: Fattura, output_path: Path) -> Path:
    """Genera PDF professionale di una fattura."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # Stili custom
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#1F4E79"),
        spaceAfter=6,
    )
    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
    )
    normal = styles["Normal"]

    # ── Intestazione ───────────────────────────────────────────────────────────
    story.append(Paragraph(f"FATTURA N. {fattura.numero}", title_style))
    story.append(Paragraph(f"Data: {fattura.data.strftime('%d/%m/%Y')}", header_style))
    story.append(Spacer(1, 10 * mm))

    # ── Dati cliente ───────────────────────────────────────────────────────────
    cliente_data = [
        ["FATTURATO A:", ""],
        [fattura.cliente_nome, ""],
        [f"P.IVA: {fattura.cliente_piva}", ""],
        [fattura.cliente_indirizzo, ""],
    ]
    cliente_table = Table(cliente_data, colWidths=[170 * mm, 0])
    cliente_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, 0), colors.HexColor("#1F4E79")),
    ]))
    story.append(cliente_table)
    story.append(Spacer(1, 8 * mm))

    # ── Tabella voci ───────────────────────────────────────────────────────────
    header = ["Descrizione", "Q.tà", "Prezzo Unit.", "IVA %", "Imponibile", "Totale"]
    table_data = [header]

    for riga in fattura.righe:
        table_data.append([
            riga.descrizione,
            f"{riga.quantita:g}",
            f"€ {riga.prezzo_unitario:,.2f}",
            f"{riga.aliquota_iva * 100:.0f}%",
            f"€ {riga.imponibile:,.2f}",
            f"€ {riga.totale:,.2f}",
        ])

    # Riga totali
    table_data.append(["", "", "", "", "Imponibile:", f"€ {fattura.totale_imponibile:,.2f}"])
    table_data.append(["", "", "", "", "IVA totale:", f"€ {fattura.totale_iva:,.2f}"])
    table_data.append(["", "", "", "", "TOTALE FATTURA:", f"€ {fattura.totale_fattura:,.2f}"])

    col_widths = [85 * mm, 20 * mm, 25 * mm, 15 * mm, 30 * mm, 25 * mm]
    t = Table(table_data, colWidths=col_widths)

    n_rows = len(table_data)
    n_totals = 3  # ultime 3 righe sono i totali

    t.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        # Righe alternate
        ("ROWBACKGROUNDS", (0, 1), (-1, n_rows - n_totals - 1),
         [colors.white, colors.HexColor("#EBF3FB")]),
        # Totali
        ("FONTNAME", (4, -n_totals), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (4, -1), (-1, -1), colors.HexColor("#D6E4F0")),
        # Bordi
        ("GRID", (0, 0), (-1, n_rows - n_totals - 1), 0.5, colors.grey),
        ("LINEBELOW", (4, -1), (-1, -1), 1, colors.HexColor("#1F4E79")),
        # Allineamento numeri
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))

    story.append(t)

    if fattura.note:
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph(f"<b>Note:</b> {fattura.note}", normal))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story)
    return output_path


# Demo
if __name__ == "__main__":
    fattura = Fattura(
        numero="2026/001",
        data=date.today(),
        cliente_nome="Acme S.r.l.",
        cliente_piva="IT01234567890",
        cliente_indirizzo="Via Roma 1, 20100 Milano (MI)",
        righe=[
            RigaFattura("Sviluppo software — Modulo ordini", 40, 80.0),
            RigaFattura("Consulenza architettura cloud", 8, 120.0),
            RigaFattura("Licenza annuale piattaforma", 1, 2400.0),
        ],
        note="Pagamento a 30 giorni data fattura. IBAN: IT60 X054 2811 1010 0000 0123 456"
    )
    path = genera_pdf_fattura(fattura, Path("/tmp/fattura_2026_001.pdf"))
    print(f"Fattura generata: {path}")
```

---

## PART D — Web Automation con Playwright

### D1 — Scraping e Form Filling

```python
# src/automation/browser/playwright_utils.py
"""
Web automation con Playwright (headless browser).
Playwright >> Selenium per: async nativo, auto-wait, tracce, intercept rete.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import structlog
from playwright.async_api import Browser, Page, async_playwright

logger = structlog.get_logger(__name__)


async def fetch_public_data(url: str, selector: str) -> list[dict]:
    """
    Esempio: scraping dati pubblici da siti che richiedono JavaScript.
    (N.B. rispettare sempre robots.txt e Terms of Service del sito)
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="it-IT",
        )

        page = await context.new_page()
        log = logger.bind(url=url)

        try:
            # Intercetta errori di rete
            page.on("pageerror", lambda err: log.error("page_error", error=str(err)))

            log.info("navigating")
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Attendi elemento (auto-retry fino a timeout)
            await page.wait_for_selector(selector, timeout=15000)

            # Estrai dati
            elements = await page.query_selector_all(selector)
            results = []
            for el in elements:
                text = await el.inner_text()
                href = await el.get_attribute("href")
                results.append({"text": text.strip(), "href": href})

            log.info("data_extracted", count=len(results))
            return results

        except Exception as e:
            log.error("scraping_failed", error=str(e))
            # Screenshot per debug
            screenshot_path = Path(f"/tmp/error_{url.split('//')[1][:30]}.png")
            await page.screenshot(path=str(screenshot_path))
            log.info("screenshot_saved", path=str(screenshot_path))
            raise
        finally:
            await browser.close()


async def compila_form_e_salva_pdf(
    url: str,
    form_data: dict[str, str],
    output_pdf: Path,
    submit_selector: Optional[str] = None,
) -> Path:
    """
    Compila un form web e salva il risultato come PDF.
    Use case: compilazione automatica di preventivi, ordini online, portali PA.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded")

            # Compila ogni campo del form
            for field_selector, value in form_data.items():
                element = await page.wait_for_selector(field_selector, timeout=5000)
                await element.fill(value)
                await page.wait_for_timeout(200)  # simula digitazione umana

            logger.info("form_filled", fields=len(form_data))

            # Submit (opzionale)
            if submit_selector:
                await page.click(submit_selector)
                await page.wait_for_load_state("networkidle")

            # Salva come PDF (dimensione A4, senza header/footer browser)
            output_pdf.parent.mkdir(parents=True, exist_ok=True)
            await page.pdf(
                path=str(output_pdf),
                format="A4",
                print_background=True,
                margin={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"},
            )

            logger.info("pdf_saved", path=str(output_pdf))
            return output_pdf

        finally:
            await browser.close()


async def screenshot_periodico(
    urls: list[str],
    output_dir: Path,
    interval_seconds: float = 300.0,
) -> None:
    """
    Prende screenshot periodici di una lista di URL.
    Use case: monitoring visuale di dashboard, portali interni.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    import time

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})

        while True:
            timestamp = int(time.time())
            for url in urls:
                page = await context.new_page()
                try:
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    safe_name = url.replace("://", "_").replace("/", "_")[:50]
                    path = output_dir / f"{safe_name}_{timestamp}.png"
                    await page.screenshot(path=str(path), full_page=True)
                    logger.info("screenshot_taken", url=url, path=str(path))
                except Exception as e:
                    logger.error("screenshot_failed", url=url, error=str(e))
                finally:
                    await page.close()

            await asyncio.sleep(interval_seconds)
```

---

## PART E — Scheduling e Deployment

### E1 — APScheduler

```python
# src/automation/scheduler/job_scheduler.py
"""
Scheduler per task periodici.
APScheduler 3.x con executor asincrono e MongoDB/Redis jobstore.
"""
from __future__ import annotations

import asyncio
import signal
from typing import Callable

import structlog
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = structlog.get_logger(__name__)


class AutomationScheduler:
    """Wrapper su APScheduler con logging strutturato e graceful shutdown."""

    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.scheduler = AsyncIOScheduler(
            jobstores={
                "default": RedisJobStore(url=redis_url)
            },
            executors={
                "default": AsyncIOExecutor()
            },
            job_defaults={
                "coalesce": True,        # Non eseguire job accumulati (es. dopo downtime)
                "max_instances": 1,      # Una sola istanza per job alla volta
                "misfire_grace_time": 60 # Esegui anche se in ritardo fino a 60s
            }
        )
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda s, f: asyncio.create_task(self._shutdown()))

    async def _shutdown(self) -> None:
        logger.info("scheduler_shutting_down")
        self.scheduler.shutdown(wait=True)

    def add_cron_job(
        self,
        func: Callable,
        job_id: str,
        cron_expression: str,
        **kwargs
    ) -> None:
        """Aggiunge un job con sintassi cron (es. '0 8 * * 1' = lunedì 08:00)."""
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Cron expression non valida (richiede 5 parti): {cron_expression}")

        minute, hour, day, month, day_of_week = parts
        self.scheduler.add_job(
            func,
            trigger="cron",
            id=job_id,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            replace_existing=True,
            timezone="Europe/Rome",
            **kwargs
        )
        logger.info("job_scheduled", job_id=job_id, cron=cron_expression)

    def add_interval_job(
        self,
        func: Callable,
        job_id: str,
        seconds: int,
        **kwargs
    ) -> None:
        """Aggiunge un job con intervallo fisso."""
        self.scheduler.add_job(
            func,
            trigger="interval",
            id=job_id,
            seconds=seconds,
            replace_existing=True,
            **kwargs
        )
        logger.info("interval_job_scheduled", job_id=job_id, interval_s=seconds)

    async def run(self) -> None:
        self.scheduler.start()
        logger.info("scheduler_started", jobs=len(self.scheduler.get_jobs()))
        try:
            while True:
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            await self._shutdown()


# ─── Esempio job reali ────────────────────────────────────────────────────────

async def job_report_settimanale() -> None:
    logger.info("job_started", name="report_settimanale")
    # Qui: fetch dati, genera Excel, invia email
    await asyncio.sleep(1)  # Simula lavoro
    logger.info("job_completed", name="report_settimanale")

async def job_sync_contatti_crm() -> None:
    logger.info("job_started", name="sync_crm")
    # Qui: leggi nuovi lead, aggiorna HubSpot/Salesforce
    await asyncio.sleep(2)
    logger.info("job_completed", name="sync_crm")

async def job_backup_verifica() -> None:
    logger.info("job_started", name="backup_verifica")
    # Qui: verifica che i backup di ieri esistano e non siano corrotti
    await asyncio.sleep(0.5)
    logger.info("job_completed", name="backup_verifica")


async def main() -> None:
    sched = AutomationScheduler()

    # Report vendite ogni lunedì alle 08:30
    sched.add_cron_job(job_report_settimanale, "report-settimanale", "30 8 * * 1")

    # Sync CRM ogni 2 ore
    sched.add_interval_job(job_sync_contatti_crm, "sync-crm", seconds=7200)

    # Verifica backup ogni mattina alle 07:00
    sched.add_cron_job(job_backup_verifica, "backup-verifica", "0 7 * * *")

    await sched.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### E2 — Deployment come Servizio systemd

```ini
# /etc/systemd/system/automation-scheduler.service
[Unit]
Description=Automation Scheduler Service
Documentation=https://interno.example.com/docs/automation
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=automation
Group=automation
WorkingDirectory=/opt/automation

# Usa uv per eseguire con l'ambiente corretto
ExecStart=/usr/local/bin/uv run python -m automation.scheduler.job_scheduler

# Variabili d'ambiente da file (più sicuro che hardcoding)
EnvironmentFile=/opt/automation/.env

# Restart automatico
Restart=always
RestartSec=10
StartLimitBurst=3
StartLimitInterval=60s

# Log output
StandardOutput=journal
StandardError=journal
SyslogIdentifier=automation-scheduler

# Sicurezza
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/opt/automation/data /var/log/automation

[Install]
WantedBy=multi-user.target
```

```bash
# Installa e avvia il servizio
sudo systemctl daemon-reload
sudo systemctl enable automation-scheduler
sudo systemctl start automation-scheduler

# Monitora i log in tempo reale
sudo journalctl -u automation-scheduler -f

# Verifica stato
sudo systemctl status automation-scheduler
```

---

## PART F — Structured Logging con structlog

```python
# src/automation/logging/setup.py
"""
Setup logging production-grade con structlog.
Output: JSON su stdout (per aggregatori log come Loki, CloudWatch, Datadog).
"""
import logging
import sys

import structlog


def setup_logging(level: str = "INFO", json_output: bool = True) -> None:
    """
    Configura structlog per output strutturato JSON.
    In sviluppo usa ConsoleRenderer (leggibile).
    In produzione usa JSONRenderer (parseable da Loki/ELK).
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, level.upper()))


# ─── Utilizzo con correlation ID ─────────────────────────────────────────────

import uuid
from contextlib import contextmanager
from typing import Generator

@contextmanager
def request_context(correlation_id: str | None = None) -> Generator:
    """
    Context manager per propagare correlation_id in tutti i log del blocco.
    Utile per tracciare tutti i log di una singola richiesta/job.
    """
    cid = correlation_id or str(uuid.uuid4())[:8]
    structlog.contextvars.bind_contextvars(correlation_id=cid)
    try:
        yield cid
    finally:
        structlog.contextvars.unbind_contextvars("correlation_id")


# Demo
if __name__ == "__main__":
    import os
    setup_logging(
        level="INFO",
        json_output=os.environ.get("ENV", "dev") == "production"
    )

    log = structlog.get_logger("demo")

    with request_context("req_abc123") as cid:
        log.info("processing_started", user_id=42, action="sync_crm")
        log.warning("rate_limit_approaching", remaining=3)
        log.info("processing_completed", records=150, duration_ms=234)

    # Output JSON (produzione):
    # {"event": "processing_started", "user_id": 42, "action": "sync_crm",
    #  "correlation_id": "req_abc123", "level": "info", "timestamp": "..."}
```

---

## Esercizi Pratici

### Esercizio 1 — File Watcher per Fatture (30 min)

Configura il watcher per monitorare `/tmp/inbox_fatture/` e:
1. Rilevare nuovi file `.xml`
2. Stampare il contenuto del tag `<Numero>` (simulazione parsing SDI)
3. Spostare il file processato in `/tmp/archivio_fatture/<anno>/<mese>/`

```bash
mkdir -p /tmp/inbox_fatture /tmp/archivio_fatture
python3 -c "from src.automation.file_ops.watcher import *; avvia_monitoraggio(Path('/tmp/inbox_fatture'), lambda p: print(f'Nuova fattura: {p.name}'), {'.xml'})" &

# Simula arrivo fattura
echo '<FatturaPA><Numero>2026/001</Numero></FatturaPA>' > /tmp/inbox_fatture/FT_2026_001.xml
```

### Esercizio 2 — Report Excel Reale (45 min)

Scarica i dati di esempio e genera un report completo:

```python
# Genera dati di test e crea il report
import asyncio
from pathlib import Path
from src.automation.excel.report_generator import VenditeMensili, genera_report_vendite

mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
        "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
dati = [
    VenditeMensili(m, f, f * 0.25, n, p)
    for m, f, n, p in zip(mesi,
        [98000, 87000, 112000, 95000, 145000, 103000,
         78000, 65000, 118000, 132000, 156000, 189000],
        [142, 128, 167, 143, 198, 152, 115, 98, 172, 187, 221, 256],
        ["Prod A", "Prod B", "Prod A", "Prod C", "Prod A", "Prod B",
         "Prod C", "Prod B", "Prod A", "Prod A", "Prod C", "Prod A"]
    )
]
genera_report_vendite(dati, Path("/tmp/report_2026.xlsx"), 2026)
print("Apri /tmp/report_2026.xlsx con LibreOffice Calc o Excel")
```

### Esercizio 3 — Playwright Screenshot Monitor (20 min)

```python
# Monitora una pagina ogni 60 secondi
import asyncio
from pathlib import Path
from src.automation.browser.playwright_utils import screenshot_periodico

asyncio.run(screenshot_periodico(
    urls=["https://httpbin.org/anything"],
    output_dir=Path("/tmp/monitor_screenshots"),
    interval_seconds=60.0
))
```

---

## Riferimenti

- `uv` package manager: https://docs.astral.sh/uv/
- httpx documentation: https://www.python-httpx.org/
- Pydantic v2 migration: https://docs.pydantic.dev/latest/migration/
- structlog: https://www.structlog.org/en/stable/
- watchdog: https://watchdog.readthedocs.io/
- Playwright Python: https://playwright.dev/python/docs/intro
- APScheduler 3.x: https://apscheduler.readthedocs.io/
- tenacity retry: https://tenacity.readthedocs.io/
- Modulo sorgente: `12-python-automazione-avanzata.md`
