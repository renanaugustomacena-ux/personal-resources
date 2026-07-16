# Tutorial Lab — RPA con Playwright: Automazione Browser in Produzione

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `27-rpa-playwright-automazione.md`
> **Livello:** intermediate → advanced
> **Tempo stimato:** 3 ore
> **Prerequisiti:** Python 3.11+, HTML/CSS base, concetti HTTP
> **Versioni di riferimento:** Playwright for Python 1.44+, Python 3.11+

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Installare Playwright e configurare l'ambiente per RPA in produzione
2. Scrivere selettori robusti che non si rompono a ogni deploy
3. Estrarre dati da tabelle con paginazione automatica
4. Compilare form complessi con upload file e datepicker
5. Salvare sessioni autenticate per evitare login ripetuti
6. Produrre screenshot audit e PDF da pagine web
7. Eseguire RPA in modalità asincrona per batch processing

---

## Lab Environment Setup

```bash
# 1. Installazione Playwright
pip install playwright

# 2. Download browser Chromium (una tantum, ~200MB)
playwright install chromium

# 3. Verifica installazione
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"

# 4. Dipendenze aggiuntive
pip install structlog httpx

# 5. Crea directory per output
mkdir -p audit/screenshots audit/pdf sessions logs

# SCRIPT VERIFICA PREREQUISITI
python - <<'EOF'
import subprocess
import sys

try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://example.com")
        titolo = page.title()
        browser.close()
    print(f"✅ Playwright OK - titolo pagina test: {titolo}")
except Exception as e:
    print(f"❌ Playwright non funzionante: {e}")
    sys.exit(1)
EOF
```

---

## Analogia Introduttiva

> **Playwright in RPA è come un assistente che guarda lo stesso schermo che guarderesti tu**,
> ma esegue le azioni 100x più veloce e senza stancarsi.
>
> Il vantaggio rispetto a Selenium è l'**auto-wait**:
> un assistente umano aspetta naturalmente che il pulsante sia cliccabile;
> Selenium senza wait espliciti clicca mentre il pulsante è ancora in caricamento.
> Playwright fa come l'umano — aspetta che l'elemento sia pronto.
>
> Il **selettore ARIA** è come dire "clicca il pulsante che si chiama 'Invia'",
> invece di "clicca sul terzo figlio del div con classe 'col-md-3 text-right'".
> Se il design cambia, il secondo selettore si rompe; il primo no.

---

## Architettura del Lab RPA

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PIPELINE RPA PRODUZIONE                           │
│                                                                       │
│  [Dati input] ──────────────────────────────────────────────────┐   │
│                                                                  │   │
│  ┌─────────────────────────────────────────────────────────┐    │   │
│  │                  Playwright Browser                      │    │   │
│  │                                                          │    │   │
│  │  [Login / Riusa Sessione] → [Naviga] → [Esegui Azioni] │ ◄──┘   │
│  │              │                              │            │        │
│  │              ▼                              ▼            │        │
│  │  [Screenshot Audit]            [Estrai/Compila Dati]    │        │
│  └──────────────────────────────────────────────────────────┘        │
│                          │                                            │
│  [Dati estratti / Azioni eseguite] ──────────────────────────────►  │
│  [Log strutturato] ──────────────────────────────────────────────►  │
│  [Screenshot Audit] ─────────────────────────────────────────────►  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PART A — Selettori e Auto-Wait

### A1 — Demo con Sito di Test Locale

```python
# rpa/demo_selettori.py
"""
Demo selettori Playwright usando il sito di test https://playwright.dev/python/docs/input
(non richiede credenziali, accessibile pubblicamente)
"""
from playwright.sync_api import sync_playwright, expect

def demo_selettori_base():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Usa sito di test pubblico
        page.goto("https://demo.playwright.dev/todomvc/")
        page.wait_for_load_state("domcontentloaded")

        # ==============================
        # GERARCHIA SELETTORI (migliore → peggiore)
        # ==============================

        # 1. ARIA Role + Name (il più stabile)
        todo_input = page.get_by_placeholder("What needs to be done?")
        todo_input.fill("Comprare latte")
        todo_input.press("Enter")

        todo_input.fill("Andare in palestra")
        todo_input.press("Enter")

        # 2. Text exact
        primo_todo = page.get_by_text("Comprare latte", exact=True)
        print(f"Todo presente: {primo_todo.is_visible()}")

        # 3. Locator composto (specifico senza fragilità)
        todos_list = page.locator(".todo-list li")
        count = todos_list.count()
        print(f"Todo totali: {count}")  # atteso: 2

        # 4. Seleziona specifico con filtro testo
        primo = page.locator(".todo-list li").filter(has_text="Comprare latte")
        primo.locator(".toggle").click()  # mettilo come completato

        # Verifica stato
        completati = page.locator(".todo-list li.completed")
        print(f"Todo completati: {completati.count()}")

        # Screenshot per documentazione
        page.screenshot(path="audit/screenshots/demo_selettori.png", full_page=True)
        browser.close()

def demo_auto_wait():
    """Dimostra auto-wait vs sleep esplicito."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://the-internet.herokuapp.com/dynamic_loading/1")

        # BAD: sleep fisso — fragile, lento
        # page.wait_for_timeout(3000)  # ❌ evita

        # GOOD: auto-wait su elemento specifico
        page.get_by_role("button", name="Start").click()
        # Playwright aspetta automaticamente che l'elemento sia visibile (max 30s)
        page.wait_for_selector("#finish h4", state="visible", timeout=15_000)
        testo = page.locator("#finish h4").text_content()
        print(f"Testo caricato dinamicamente: {testo}")

        browser.close()

if __name__ == "__main__":
    demo_selettori_base()
    demo_auto_wait()
```

---

## PART B — Estrazione Dati con Paginazione

### B1 — Scraper con Paginazione Automatica

```python
# rpa/scraper_tabella.py
from __future__ import annotations

import csv
import time
from pathlib import Path

import structlog
from playwright.sync_api import Page, sync_playwright

log = structlog.get_logger()

def estrai_riga_tabella(riga_locator) -> dict:
    """Estrae dati da una riga di tabella HTML."""
    celle = riga_locator.locator("td").all()
    testi = [cella.text_content().strip() for cella in celle]
    return testi  # restituisce lista ordinata di valori

def scrapa_tabella_con_intestazioni(page: Page, selettore_tabella: str) -> list[dict]:
    """Estrae tabella HTML come lista di dizionari usando le intestazioni come chiavi."""
    tabella = page.locator(selettore_tabella)
    intestazioni = [
        th.text_content().strip()
        for th in tabella.locator("thead th").all()
    ]
    if not intestazioni:
        # Prova con prima riga se non c'è thead
        intestazioni = [
            td.text_content().strip()
            for td in tabella.locator("tr:first-child td, tr:first-child th").all()
        ]
    righe = tabella.locator("tbody tr").all()
    risultati = []
    for riga in righe:
        celle = [td.text_content().strip() for td in riga.locator("td").all()]
        if len(celle) == len(intestazioni) and any(c for c in celle):
            risultati.append(dict(zip(intestazioni, celle)))
    return risultati

def scrapa_con_paginazione(page: Page,
                            url_base: str,
                            selettore_tabella: str,
                            selettore_btn_next: str = "a[aria-label='Next']",
                            max_pagine: int = 50,
                            delay_ms: int = 500) -> list[dict]:
    """Naviga tutte le pagine e raccoglie i dati dalla tabella."""
    tutti_i_dati: list[dict] = []
    pagina = 1

    page.goto(url_base)
    page.wait_for_load_state("domcontentloaded")

    while pagina <= max_pagine:
        log.info("scraping_pagina", pagina=pagina, url=page.url)
        dati_pagina = scrapa_tabella_con_intestazioni(page, selettore_tabella)
        if not dati_pagina:
            log.info("nessun_dato_pagina", pagina=pagina)
            break
        tutti_i_dati.extend(dati_pagina)
        log.info("dati_estratti", pagina=pagina, righe=len(dati_pagina))

        btn_next = page.locator(selettore_btn_next)
        if not btn_next.is_visible() or btn_next.get_attribute("aria-disabled") == "true":
            log.info("ultima_pagina_raggiunta", pagina=pagina)
            break

        btn_next.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(delay_ms)
        pagina += 1

    return tutti_i_dati

def salva_csv(dati: list[dict], output_path: Path) -> None:
    if not dati:
        log.warning("nessun_dato_da_salvare")
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=dati[0].keys())
        writer.writeheader()
        writer.writerows(dati)
    log.info("csv_salvato", path=str(output_path), righe=len(dati))

# Esempio con sito di test pubblico
def demo_scraping():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Usa sito demo pubblico con tabella e paginazione
        page.goto("https://datatables.net/examples/basic_init/zero_config.html")
        page.wait_for_load_state("domcontentloaded")
        dati = scrapa_tabella_con_intestazioni(page, "table#example")
        print(f"Righe estratte: {len(dati)}")
        for riga in dati[:3]:
            print(f"  {riga}")
        browser.close()

if __name__ == "__main__":
    import structlog
    structlog.configure()
    demo_scraping()
```

---

## PART C — Compilazione Form e Autenticazione

### C1 — Login e Session Persistence

```python
# rpa/autenticazione.py
from __future__ import annotations

import json
from pathlib import Path

import structlog
from playwright.sync_api import sync_playwright, Page

log = structlog.get_logger()

SESSION_PATH = Path("sessions/auth_state.json")

def esegui_login(url_login: str, username: str, password: str,
                  url_post_login: str | None = None) -> None:
    """Esegue login e salva il session state per riuso."""
    SESSION_PATH.parent.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto(url_login)
        # Selettori ARIA — più stabili di CSS
        page.get_by_label("Username").fill(username)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="Accedi").click()

        if url_post_login:
            page.wait_for_url(url_post_login, timeout=15_000)
        else:
            page.wait_for_load_state("networkidle")

        # Salva sessione (cookie + localStorage + sessionStorage)
        context.storage_state(path=str(SESSION_PATH))
        log.info("sessione_salvata", path=str(SESSION_PATH))
        browser.close()

def sessione_valida() -> bool:
    """Verifica che la sessione salvata sia ancora attiva."""
    if not SESSION_PATH.exists():
        return False
    try:
        state = json.loads(SESSION_PATH.read_text())
        # Controlla che ci siano cookie non scaduti
        return len(state.get("cookies", [])) > 0
    except Exception:
        return False

def esegui_con_sessione(funzione_rpa, url_verifica: str = "/dashboard") -> None:
    """Esegue una funzione RPA usando la sessione salvata."""
    if not sessione_valida():
        raise RuntimeError("Sessione non disponibile. Esegui esegui_login() prima.")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(SESSION_PATH),
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        try:
            funzione_rpa(page)
        except Exception as e:
            # Screenshot al fallimento per debug
            page.screenshot(path="audit/screenshots/errore.png")
            log.error("rpa_fallita", errore=str(e))
            raise
        finally:
            browser.close()
```

### C2 — Compilazione Form Complesso

```python
# rpa/form_compiler.py
from __future__ import annotations

from pathlib import Path

import structlog
from playwright.sync_api import Page

log = structlog.get_logger()

def screenshot_step(page: Page, nome_step: str) -> str:
    """Screenshot con timestamp per audit trail."""
    from datetime import datetime
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"audit/screenshots/{ts}_{nome_step.replace(' ', '_')}.png"
    page.screenshot(path=path, full_page=True)
    log.info("screenshot_salvato", path=path, step=nome_step)
    return path

def compila_form_ordine(page: Page, dati: dict) -> str:
    """
    Compila form ordine con screenshot ad ogni step critico.
    Restituisce numero ordine confermato.
    """
    page.goto("/ordini/nuovo")
    page.wait_for_load_state("domcontentloaded")
    screenshot_step(page, "01_form_vuoto")

    # Selezione dropdown (Select)
    page.get_by_label("Categoria prodotto").select_option(dati["categoria"])

    # Input testo
    page.get_by_label("Nome prodotto").fill(dati["nome_prodotto"])
    page.get_by_label("Quantità").fill(str(dati["quantita"]))

    # Date picker (gestione variabile per browser)
    data_input = page.get_by_label("Data consegna")
    data_input.click()
    data_input.fill(dati["data_consegna"])  # formato YYYY-MM-DD
    page.keyboard.press("Escape")           # chiude eventuali datepicker overlay

    # Checkbox opzionale
    if dati.get("spedizione_urgente"):
        page.get_by_label("Spedizione urgente").check()

    # Textarea
    if dati.get("note"):
        page.get_by_label("Note speciali").fill(dati["note"])

    # Upload file se presente
    if dati.get("allegato_path") and Path(dati["allegato_path"]).exists():
        page.get_by_label("Allegato").set_input_files(dati["allegato_path"])

    screenshot_step(page, "02_form_compilato")

    # Intercetta risposta per catturare numero ordine
    with page.expect_response(lambda r: "/api/ordini" in r.url and r.request.method == "POST") as resp_info:
        page.get_by_role("button", name="Invia ordine").click()

    risposta = resp_info.value
    if risposta.status not in (200, 201):
        screenshot_step(page, "03_errore_invio")
        raise RuntimeError(f"Ordine fallito: HTTP {risposta.status}")

    # Attendi conferma
    page.wait_for_selector("[data-testid='numero-ordine-confermato']", state="visible")
    numero_ordine = page.get_by_test_id("numero-ordine-confermato").text_content()
    screenshot_step(page, "03_ordine_confermato")
    log.info("ordine_creato", numero=numero_ordine)
    return numero_ordine.strip()
```

---

## PART D — PDF e Report Automatici

### D1 — Generazione PDF da Pagine Web

```python
# rpa/generatore_pdf.py
from __future__ import annotations

from pathlib import Path

import structlog
from playwright.sync_api import sync_playwright

log = structlog.get_logger()

def genera_pdf(url: str, output_path: str,
               session_path: str | None = None) -> Path:
    """
    Genera PDF da una URL (solo Chromium).
    Usa la sessione salvata se fornita.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        kwargs = {}
        if session_path and Path(session_path).exists():
            kwargs["storage_state"] = session_path
        context = browser.new_context(**kwargs)
        page = context.new_page()

        page.goto(url, wait_until="networkidle")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "20mm", "right": "15mm", "bottom": "20mm", "left": "15mm"},
            display_header_footer=True,
            header_template="<div style='font-size:10px;width:100%;text-align:right;padding-right:15mm'><span class='date'></span></div>",
            footer_template="<div style='font-size:10px;width:100%;text-align:center'><span class='pageNumber'></span> / <span class='totalPages'></span></div>",
        )
        browser.close()
        log.info("pdf_generato", url=url, output=output_path)
        return Path(output_path)

def genera_pdf_batch(report_items: list[dict]) -> list[dict]:
    """
    Genera PDF multipli in batch.
    report_items: [{"url": ..., "output": ..., "nome": ...}]
    """
    risultati = []
    for item in report_items:
        try:
            path = genera_pdf(item["url"], item["output"])
            risultati.append({"nome": item["nome"], "path": str(path), "ok": True})
        except Exception as e:
            log.error("pdf_batch_errore", nome=item["nome"], errore=str(e))
            risultati.append({"nome": item["nome"], "errore": str(e), "ok": False})
    return risultati

if __name__ == "__main__":
    import structlog
    structlog.configure()
    path = genera_pdf(
        url="https://playwright.dev/python/",
        output_path="audit/pdf/playwright_docs.pdf",
    )
    print(f"PDF generato: {path} ({path.stat().st_size // 1024}KB)")
```

---

## Esercizi

### Esercizio 1 — Scraper con Autenticazione (40 min)

Usa il sito di demo https://the-internet.herokuapp.com/login (username: tomsmith, password: SuperSecretPassword!)

1. Scrivi `login_the_internet()` che fa login e salva la sessione
2. Scrivi `verifica_area_sicura(page)` che:
   - Naviga a `/secure`
   - Verifica che ci sia testo "Welcome to the Secure Area!"
   - Cattura screenshot
3. Scrivi `logout_e_verifica(page)` che clicca "Logout" e verifica il redirect

### Esercizio 2 — Estrazione con Paginazione Reale (25 min)

Usa `https://books.toscrape.com` (sito legalmente scrappabile per pratica):
1. Estrai titolo, prezzo e disponibilità per tutti i libri nella categoria "Travel"
2. Naviga automaticamente le pagine della categoria
3. Salva in CSV `libri_travel.csv`
4. Conta quanti libri hanno stock "In stock"

### Esercizio 3 — Report PDF Schedulato (20 min)

Scrivi uno script che:
1. Si esegue ogni lunedì (usa `schedule` library)
2. Naviga su `https://example.com` (o altra URL statica)
3. Genera PDF con nome `report_YYYY-MM-DD.pdf`
4. Salva in `audit/pdf/settimanali/`
5. Pulisce PDF più vecchi di 90 giorni

---

## Riferimenti

- Playwright Python API: https://playwright.dev/python/docs/api/class-page
- Locators guide: https://playwright.dev/python/docs/locators
- Auth best practices: https://playwright.dev/python/docs/auth
- Trace viewer: https://playwright.dev/python/docs/trace-viewer-intro
- Modulo sorgente: `27-rpa-playwright-automazione.md`
