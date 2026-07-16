# 27 — RPA con Playwright: Automazione Browser Headless in Produzione

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Tipo:** Documento ufficiale
> **Livello:** intermediate → advanced
> **Prerequisiti:** Python 3.11+, concetti HTTP, HTML/CSS selettori base
> **Versioni di riferimento:** Playwright for Python 1.44+, Python 3.11+

---

## Introduzione

La Robotic Process Automation (RPA) con Playwright riguarda l'automazione di
interfacce web che non espongono API — legacy portal, sistemi ERP vecchi,
siti di terze parti. È lo strato di automazione di "ultimo ricorso",
da usare solo quando l'API non esiste o non è accessibile.

Questo documento copre l'uso di Playwright in contesti di produzione:
selettori robusti, strategie anti-flakiness, gestione autenticazione,
screenshot/PDF per audit, scheduling e monitoring.

---

## 1. Playwright vs Selenium vs Puppeteer

| Caratteristica | Playwright | Selenium 4 | Puppeteer |
|---------------|-----------|-----------|-----------|
| Language | Python, JS, Java, .NET | Tutti i principali | JS/TS |
| Browser | Chromium, Firefox, WebKit | Tutti (con driver) | Chromium |
| Auto-wait | Sì (built-in) | No (manuale) | Parziale |
| Network intercept | Sì | Limitato | Sì |
| Multi-page/tab | Nativo | Difficile | Difficile |
| Velocità | Veloce | Lento | Veloce |
| Installazione | 1 comando | WebDriver separato | NPM only |
| Uso produzione PMI | ★★★★★ | ★★★☆☆ | ★★★☆☆ |

**Perché Playwright per RPA in produzione:**
- Auto-wait integrato: aspetta automaticamente che gli elementi siano interagibili
- Selettori ARIA-first: più stabili di CSS/XPath
- Network interception: mock API, intercetta richieste, logger traffico
- Contesti di browser isolati: sessioni parallele senza interferenze
- Trace viewer: registra ogni step per debugging

---

## 2. Installazione e Setup

```bash
# Installazione
pip install playwright

# Download browser (una tantum, ~200MB Chromium)
playwright install chromium  # solo Chromium per RPA

# Oppure install completo (tutti i browser)
playwright install

# Dipendenze sistema (Linux/Docker)
playwright install-deps chromium

# Verifica installazione
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

### 2.1 Dockerfile per RPA in Produzione

```dockerfile
# Dockerfile ottimizzato per RPA con Playwright
FROM python:3.11-slim

# Dipendenze sistema Playwright
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libatspi2.0-0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libcairo2 libpangocairo-1.0-0 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY . .
CMD ["python", "rpa_main.py"]
```

---

## 3. Selettori Robusti

### 3.1 Gerarchia di Selettori (dalla più alla meno robusta)

```python
# PRIMA SCELTA: ARIA selettori (semantici, stabili)
page.get_by_role("button", name="Invia ordine")
page.get_by_label("Email")
page.get_by_placeholder("Inserisci email aziendale")
page.get_by_text("Conferma acquisto")
page.get_by_title("Esporta CSV")
page.get_by_alt_text("Logo azienda")
page.get_by_test_id("submit-btn")  # data-testid attribute

# SECONDA SCELTA: CSS con attributi stabili
page.locator("[data-id='order-form']")
page.locator("input[name='email']")
page.locator("form#checkout button[type='submit']")

# TERZA SCELTA: testo (attenzione a variazioni linguistiche)
page.get_by_text("Conferma", exact=True)

# EVITARE: selettori fragili che si rompono a ogni deploy
page.locator(".col-md-3 > div:nth-child(2) > span.text-primary")  # ❌ fragile
page.locator("#app > div > main > section:nth-child(3) button")    # ❌ fragile

# CONCATENARE per specificità senza fragilità
page.locator("section[aria-label='Riepilogo ordine']").get_by_role("button", name="Conferma")
```

### 3.2 Pattern Auto-Wait

```python
# Playwright attende automaticamente che gli elementi siano:
# - presenti nel DOM
# - visibili
# - stabili (non in animazione)
# - interagibili (non disabled, non coperto)

# Tutto ciò avviene implicitamente in:
page.click("button[name='submit']")    # attende fino a 30s (default)
page.fill("input[name='email']", "test@test.it")
page.select_option("select#paese", "IT")

# Aspetta stato esplicito
page.wait_for_selector("div.risultato", state="visible", timeout=10_000)
page.wait_for_url("**/dashboard", wait_until="networkidle")
page.wait_for_load_state("domcontentloaded")

# Aspetta risposta specifica
with page.expect_response("**/api/orders") as resp_info:
    page.click("button#submit-order")
response = resp_info.value
assert response.status == 200
dati_ordine = response.json()
```

---

## 4. Gestione Autenticazione

### 4.1 Login e Session Storage

```python
from playwright.sync_api import sync_playwright
import json
from pathlib import Path

STORAGE_STATE_PATH = Path("auth/session.json")

def login_e_salva_sessione(username: str, password: str, url_login: str) -> None:
    """Esegue login e salva il session state (cookie + localStorage)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url_login)
        page.get_by_label("Username").fill(username)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="Accedi").click()
        page.wait_for_url("**/dashboard")
        STORAGE_STATE_PATH.parent.mkdir(exist_ok=True)
        context.storage_state(path=str(STORAGE_STATE_PATH))
        browser.close()

def esegui_con_sessione_salvata(funzione_rpa) -> None:
    """Riusa sessione esistente (evita login ad ogni esecuzione)."""
    if not STORAGE_STATE_PATH.exists():
        raise RuntimeError("Sessione non trovata — esegui login_e_salva_sessione prima")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(STORAGE_STATE_PATH))
        page = context.new_page()
        try:
            funzione_rpa(page)
        finally:
            browser.close()
```

### 4.2 Rilevamento Sessione Scaduta

```python
def verifica_sessione_valida(page) -> bool:
    """Controlla se la sessione è ancora valida."""
    page.goto("/dashboard")
    is_logged_in = page.url.endswith("/dashboard") and not page.url.contains("/login")
    return is_logged_in

def login_con_retry(page, username: str, password: str,
                     max_tentativi: int = 3) -> bool:
    for tentativo in range(1, max_tentativi + 1):
        try:
            page.goto("/login")
            page.get_by_label("Username").fill(username)
            page.get_by_label("Password").fill(password)
            page.click("button[type='submit']")
            page.wait_for_url("**/dashboard", timeout=10_000)
            return True
        except Exception as e:
            if tentativo == max_tentativi:
                raise RuntimeError(f"Login fallito dopo {max_tentativi} tentativi: {e}")
    return False
```

---

## 5. Estrazione Dati (Scraping Strutturato)

### 5.1 Estrazione da Tabelle

```python
def estrai_tabella(page, selettore_tabella: str) -> list[dict]:
    """Estrae una tabella HTML in lista di dizionari."""
    tabella = page.locator(selettore_tabella)
    intestazioni = tabella.locator("thead th").all_text_contents()
    righe = tabella.locator("tbody tr").all()
    risultati = []
    for riga in righe:
        celle = riga.locator("td").all_text_contents()
        if len(celle) == len(intestazioni):
            risultati.append(dict(zip(intestazioni, [c.strip() for c in celle])))
    return risultati

def estrai_con_paginazione(page, url_base: str,
                            selettore_tabella: str,
                            selettore_btn_next: str) -> list[dict]:
    """Naviga tutte le pagine e raccoglie i dati."""
    tutti_i_dati: list[dict] = []
    pagina_corrente = 1
    while True:
        page.goto(f"{url_base}?page={pagina_corrente}")
        dati_pagina = estrai_tabella(page, selettore_tabella)
        if not dati_pagina:
            break
        tutti_i_dati.extend(dati_pagina)
        btn_next = page.locator(selettore_btn_next)
        if not btn_next.is_visible() or btn_next.is_disabled():
            break
        pagina_corrente += 1
        page.wait_for_timeout(500)  # throttle educato
    return tutti_i_dati
```

---

## 6. Compilazione Form e Azioni

```python
def compila_ordine(page, dati_ordine: dict) -> str:
    """Compila e invia un form ordine. Restituisce numero ordine confermato."""
    page.goto("/ordini/nuovo")
    # Compilazione campi
    page.get_by_label("Prodotto").select_option(dati_ordine["prodotto_id"])
    page.get_by_label("Quantità").fill(str(dati_ordine["quantita"]))
    page.get_by_label("Note").fill(dati_ordine.get("note", ""))
    # Selezione data con date picker
    data_input = page.get_by_label("Data consegna")
    data_input.fill(dati_ordine["data_consegna"])
    data_input.press("Tab")  # chiude il datepicker
    # Upload allegato se presente
    if "allegato_path" in dati_ordine:
        page.get_by_label("Allegato").set_input_files(dati_ordine["allegato_path"])
    # Intercetta la risposta per catturare il numero ordine
    with page.expect_response("**/ordini") as resp_info:
        page.get_by_role("button", name="Invia ordine").click()
    risposta = resp_info.value
    if risposta.status != 200:
        raise RuntimeError(f"Ordine fallito: HTTP {risposta.status}")
    numero_ordine = page.get_by_test_id("ordine-confermato-numero").text_content()
    return numero_ordine.strip()
```

---

## 7. Screenshot e PDF per Audit

```python
from pathlib import Path
from datetime import datetime

def screenshot_audit(page, nome_step: str, cartella: str = "audit/screenshots") -> Path:
    """Cattura screenshot full-page per audit trail."""
    Path(cartella).mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    nome_file = f"{ts}_{nome_step.replace(' ', '_')}.png"
    path = Path(cartella) / nome_file
    page.screenshot(path=str(path), full_page=True)
    return path

def esporta_pdf(page, url: str, output_path: str) -> Path:
    """Esporta una pagina come PDF (solo Chromium)."""
    page.goto(url)
    page.wait_for_load_state("networkidle")
    page.pdf(
        path=output_path,
        format="A4",
        print_background=True,
        margin={"top": "20mm", "right": "15mm", "bottom": "20mm", "left": "15mm"},
    )
    return Path(output_path)

def screenshot_con_evidenziazione(page, selettore: str, nome_step: str) -> Path:
    """Screenshot con elemento evidenziato (bordo rosso) per documentazione."""
    page.evaluate(f"""
        const el = document.querySelector('{selettore}');
        if (el) el.style.outline = '3px solid red';
    """)
    path = screenshot_audit(page, nome_step)
    # Rimuovi evidenziazione
    page.evaluate(f"""
        const el = document.querySelector('{selettore}');
        if (el) el.style.outline = '';
    """)
    return path
```

---

## 8. Esecuzione Asincrona e Parallela

```python
import asyncio
from playwright.async_api import async_playwright

async def processa_ordine_async(ordine: dict, semaphore: asyncio.Semaphore) -> dict:
    """Processa un singolo ordine in modo asincrono."""
    async with semaphore:  # limita concorrenza
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state="auth/session.json")
            page = await context.new_page()
            try:
                await page.goto("/ordini/nuovo")
                await page.get_by_label("Prodotto").select_option(ordine["prodotto_id"])
                await page.get_by_label("Quantità").fill(str(ordine["quantita"]))
                await page.get_by_role("button", name="Invia").click()
                await page.wait_for_selector(".conferma-numero")
                numero = await page.locator(".conferma-numero").text_content()
                return {"ordine_id": ordine["id"], "numero_confermato": numero, "ok": True}
            except Exception as e:
                return {"ordine_id": ordine["id"], "errore": str(e), "ok": False}
            finally:
                await browser.close()

async def processa_batch_ordini(ordini: list[dict], max_concorrenti: int = 3) -> list[dict]:
    """Processa più ordini in parallelo con limite di concorrenza."""
    semaphore = asyncio.Semaphore(max_concorrenti)
    tasks = [processa_ordine_async(o, semaphore) for o in ordini]
    return await asyncio.gather(*tasks)
```

---

## 9. Anti-Rilevamento e Robustezza

```python
def configura_browser_stealth(playwright):
    """Configura browser per minimizzare rilevamento automazione."""
    browser = playwright.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
        ],
    )
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1920, "height": 1080},
        locale="it-IT",
        timezone_id="Europe/Rome",
    )
    # Rimuovi webdriver flag
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    """)
    return browser, context
```

> **NOTA ETICA**: le tecniche anti-rilevamento devono essere usate
> per automazione legittima su sistemi aziendali propri o per cui si ha autorizzazione.
> Lo scraping non autorizzato viola i ToS dei siti e può avere implicazioni legali.

---

## 10. Monitoring e Alerting per RPA

```python
import time
import structlog
from dataclasses import dataclass

log = structlog.get_logger()

@dataclass
class MetricheRPA:
    job_id: str
    iniziato_at: float
    step_corrente: str
    step_completati: int
    step_falliti: int
    screenshot_audit: list[str]

class RunnerRPA:
    def __init__(self, job_id: str) -> None:
        self.metriche = MetricheRPA(
            job_id=job_id, iniziato_at=time.monotonic(),
            step_corrente="", step_completati=0, step_falliti=0,
            screenshot_audit=[],
        )

    def step(self, nome: str):
        """Context manager per step con log e metriche."""
        import contextlib

        @contextlib.contextmanager
        def _step_ctx():
            self.metriche.step_corrente = nome
            t_inizio = time.monotonic()
            log.info("rpa_step_avviato", job=self.metriche.job_id, step=nome)
            try:
                yield
                durata = time.monotonic() - t_inizio
                self.metriche.step_completati += 1
                log.info("rpa_step_ok", job=self.metriche.job_id,
                         step=nome, durata_s=round(durata, 2))
            except Exception as e:
                self.metriche.step_falliti += 1
                log.error("rpa_step_fallito", job=self.metriche.job_id,
                          step=nome, errore=str(e))
                raise
        return _step_ctx()

    def report_finale(self) -> dict:
        return {
            "job_id": self.metriche.job_id,
            "durata_totale_s": round(time.monotonic() - self.metriche.iniziato_at, 2),
            "step_completati": self.metriche.step_completati,
            "step_falliti": self.metriche.step_falliti,
            "screenshot": self.metriche.screenshot_audit,
        }
```

---

## 11. Best Practice RPA in Produzione

1. **Prefer API over RPA**: prima verifica sempre se esiste un'API ufficiale o non documentata
2. **Selettori stabili**: usa data-testid, ARIA role, name — evita indici CSS
3. **Auto-wait**: non usare `page.wait_for_timeout()` come attesa principale — è flaky
4. **Screenshot audit**: cattura screenshot a ogni step critico per debugging e audit
5. **Session management**: salva e riusa la sessione — non fare login ad ogni esecuzione
6. **Throttle educato**: inserisci pause (`wait_for_timeout(300-1000ms)`) tra azioni
7. **Isolamento contesti**: usa un `BrowserContext` separato per ogni sessione/utente
8. **Error recovery**: cattura screenshot al fallimento, notifica, non lasciare browser aperti
9. **Headless in prod, headed in dev**: usa headed (`headless=False`) per debugging
10. **Monitoring**: logga ogni step con durata, tasso di successo, alert su failure >20%

---

## Riferimenti

- Playwright Python: https://playwright.dev/python/
- Best selectors: https://playwright.dev/docs/locators
- Trace viewer: https://playwright.dev/docs/trace-viewer
- Playwright Docker: https://playwright.dev/docs/docker
