# Tutorial 15 — Web Scraping in Python: Dal Semplice al Robusto

> **Companion a:** `15-web-scraping.md`
> **Scope:** requests, BeautifulSoup 4, httpx, Playwright, rate limiting, rispetto robots.txt, anti-pattern
> **Prerequisiti:** `tutorial_10_programmazione_asincrona.md`, `tutorial_14_data_processing.md`
> **Durata stimata:** 14-18 ore
> **Stack:** Python 3.12+, httpx 0.27+, beautifulsoup4, playwright, parsel

---

## Mappa concettuale

```
Web Scraping Stack
│
├── HTTP Client
│   ├── httpx — sync e async, HTTP/2, session
│   ├── requests — sync, semplice, ecosystem maturo
│   └── aiohttp — async, performance massima
│
├── HTML Parsing
│   ├── BeautifulSoup 4 — API intuitiva, forgiving
│   ├── lxml — veloce, XPath, namespace XML
│   └── parsel — CSS selector + XPath (da Scrapy)
│
├── Browser Automation
│   ├── Playwright — headless Chrome/Firefox/Safari
│   ├── Selenium — WebDriver classico
│   └── Pyppeteer — Puppeteer port in Python
│
├── Pattern di robustezza
│   ├── Rate limiting — rispetta i server
│   ├── Retry con backoff — errori transitori
│   ├── robots.txt — correttezza etica/legale
│   ├── User-Agent rotation — buon cittadino
│   └── Cache locale — evita richieste duplicate
│
└── Storage
    ├── SQLite / PostgreSQL — dati strutturati
    ├── JSON Lines — log progressivo
    └── Parquet — analisi batch
```

---

# Parte A — HTTP e parsing HTML

---

## A1. httpx: client HTTP moderno

```python
import httpx
from pathlib import Path

# Richiesta GET semplice
def scarica_pagina(url: str) -> str:
    with httpx.Client(timeout=10.0) as client:
        risposta = client.get(url)
        risposta.raise_for_status()   # eccezione per 4xx/5xx
        return risposta.text

# Session con headers comuni
def crea_client() -> httpx.Client:
    return httpx.Client(
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; MioBot/1.0; +https://example.com/bot)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "it-IT,it;q=0.9",
        },
        timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
        follow_redirects=True,
        http2=True,     # usa HTTP/2 se disponibile
    )

# POST con form data
def login_form(client: httpx.Client, url: str, username: str, password: str) -> httpx.Response:
    return client.post(url, data={"username": username, "password": password})

# Asincrono con httpx
import asyncio

async def scarica_molte_pagine(urls: list[str]) -> dict[str, str]:
    risultati: dict[str, str] = {}
    async with httpx.AsyncClient(
        headers={"User-Agent": "MioBot/1.0"},
        timeout=10.0,
    ) as client:
        tasks = {url: client.get(url) for url in urls}
        for url, coro in tasks.items():
            try:
                r = await coro
                r.raise_for_status()
                risultati[url] = r.text
            except httpx.HTTPError as e:
                print(f"Errore per {url}: {e}")
    return risultati
```

---

## A2. BeautifulSoup 4: parsing HTML

```python
from bs4 import BeautifulSoup
import httpx

html = """
<html>
<body>
  <nav class="menu">
    <a href="/prodotti">Prodotti</a>
    <a href="/about">Chi siamo</a>
  </nav>
  <main>
    <article class="prodotto" id="p001" data-prezzo="29.99">
      <h2 class="titolo">Notebook A5</h2>
      <p class="descrizione">Perfetto per appunti</p>
      <span class="prezzo">€ 29.99</span>
    </article>
    <article class="prodotto" id="p002" data-prezzo="49.99">
      <h2 class="titolo">Penna stilografica</h2>
      <p class="descrizione">Scrittura elegante</p>
      <span class="prezzo">€ 49.99</span>
    </article>
  </main>
</body>
</html>
"""

soup = BeautifulSoup(html, "lxml")   # parser C, più veloce di html.parser

# Trovare elementi
titolo = soup.find("h2", class_="titolo")
print(titolo.text.strip())  # "Notebook A5"

tutti_titoli = soup.find_all("h2", class_="titolo")
for t in tutti_titoli:
    print(t.text.strip())

# CSS selector
prodotti = soup.select("article.prodotto")
for p in prodotti:
    id_prod = p.get("id")
    prezzo_data = float(p.get("data-prezzo", 0))
    nome = p.select_one("h2.titolo").text.strip()
    prezzo_testo = p.select_one("span.prezzo").text.strip()
    print(f"{id_prod}: {nome} — {prezzo_testo} (data: {prezzo_data})")

# Link
link = soup.select("nav a")
for l in link:
    href = l.get("href", "")
    testo = l.text.strip()
    print(f"{testo} → {href}")

# Navigazione DOM
main = soup.find("main")
primo_prodotto = main.find("article")
secondo_prodotto = primo_prodotto.find_next_sibling("article")
genitore = primo_prodotto.parent
```

---

## A3. Scraper completo con rate limiting

```python
import asyncio
import time
import logging
import httpx
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from pathlib import Path
import json

logger = logging.getLogger(__name__)

@dataclass
class Prodotto:
    url: str
    nome: str
    prezzo: float | None
    disponibile: bool
    categoria: str

@dataclass
class StatisticheScraperState:
    pagine_visitate: int = 0
    prodotti_estratti: int = 0
    errori: int = 0
    inizio: float = field(default_factory=time.monotonic)

    @property
    def durata(self) -> float:
        return time.monotonic() - self.inizio

class RateLimiter:
    """Garantisce massimo N richieste per secondo."""
    def __init__(self, max_per_sec: float = 1.0) -> None:
        self._min_intervallo = 1.0 / max_per_sec
        self._ultima_richiesta = 0.0
        self._lock = asyncio.Lock()

    async def aspetta(self) -> None:
        async with self._lock:
            ora = time.monotonic()
            attesa = self._min_intervallo - (ora - self._ultima_richiesta)
            if attesa > 0:
                await asyncio.sleep(attesa)
            self._ultima_richiesta = time.monotonic()

class Scraper:
    def __init__(
        self,
        base_url: str,
        output_path: Path,
        richieste_al_secondo: float = 1.0,
    ) -> None:
        self.base_url = base_url
        self.output_path = output_path
        self._rate_limiter = RateLimiter(richieste_al_secondo)
        self._statistiche = StatisticheScraperState()
        self._cache: set[str] = set()   # URL già visitati
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "Scraper":
        self._client = httpx.AsyncClient(
            headers={"User-Agent": "MioScraper/1.0"},
            timeout=15.0,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._client:
            await self._client.aclose()

    async def _get(self, url: str) -> str | None:
        if url in self._cache:
            return None
        self._cache.add(url)

        await self._rate_limiter.aspetta()

        for tentativo in range(3):
            try:
                assert self._client is not None
                r = await self._client.get(url)
                r.raise_for_status()
                self._statistiche.pagine_visitate += 1
                return r.text
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    attesa = float(e.response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, attendo {attesa}s")
                    await asyncio.sleep(attesa)
                elif e.response.status_code >= 500:
                    await asyncio.sleep(2 ** tentativo)
                else:
                    logger.error(f"HTTP {e.response.status_code} per {url}")
                    self._statistiche.errori += 1
                    return None
            except httpx.RequestError as e:
                logger.warning(f"Errore rete ({tentativo+1}/3): {e}")
                await asyncio.sleep(2 ** tentativo)

        self._statistiche.errori += 1
        return None

    def _estrai_prodotto(self, html: str, url: str) -> Prodotto | None:
        soup = BeautifulSoup(html, "lxml")
        try:
            nome = soup.select_one("h1.product-title")
            if not nome:
                return None
            prezzo_el = soup.select_one(".price")
            prezzo = None
            if prezzo_el:
                testo = prezzo_el.text.strip().replace("€", "").replace(",", ".").strip()
                try:
                    prezzo = float(testo)
                except ValueError:
                    pass
            disponibile = bool(soup.select_one(".in-stock"))
            categoria_el = soup.select_one(".breadcrumb li:nth-child(2)")
            categoria = categoria_el.text.strip() if categoria_el else "Sconosciuta"
            return Prodotto(url=url, nome=nome.text.strip(), prezzo=prezzo, disponibile=disponibile, categoria=categoria)
        except Exception as e:
            logger.error(f"Estrazione fallita per {url}: {e}")
            return None

    async def scrapa_lista(self, lista_url: str) -> list[str]:
        html = await self._get(lista_url)
        if not html:
            return []
        soup = BeautifulSoup(html, "lxml")
        links = []
        for a in soup.select("a.product-link"):
            href = a.get("href", "")
            if href:
                links.append(urljoin(self.base_url, href))
        return links

    async def esegui(self, pagine: list[str]) -> list[Prodotto]:
        prodotti: list[Prodotto] = []
        urls_prodotti: list[str] = []

        for pagina in pagine:
            urls = await self.scrapa_lista(pagina)
            urls_prodotti.extend(urls)

        for url in urls_prodotti:
            html = await self._get(url)
            if html:
                p = self._estrai_prodotto(html, url)
                if p:
                    prodotti.append(p)
                    self._statistiche.prodotti_estratti += 1

        logger.info(
            f"Completato: {self._statistiche.pagine_visitate} pagine, "
            f"{self._statistiche.prodotti_estratti} prodotti, "
            f"{self._statistiche.errori} errori in {self._statistiche.durata:.1f}s"
        )
        return prodotti
```

---

# Parte B — Browser automation con Playwright

---

## B1. Playwright per pagine JavaScript-heavy

```python
import asyncio
from playwright.async_api import async_playwright, Page, Browser

async def scrapa_pagina_js(url: str) -> str:
    """Scrapa una SPA che richiede JavaScript."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Headers e User-Agent
        await page.set_extra_http_headers({"Accept-Language": "it-IT"})
        await page.set_viewport_size({"width": 1280, "height": 720})

        # Naviga e aspetta che il contenuto sia caricato
        await page.goto(url, wait_until="networkidle")

        # Aspetta elemento specifico
        await page.wait_for_selector(".products-grid", timeout=10_000)

        # Scrolla per caricare contenuto lazy
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)

        content = await page.content()
        await browser.close()
        return content

async def clicca_e_estrai(url: str) -> list[dict]:
    """Interazione con paginazione via click."""
    risultati: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")

        while True:
            # Estrai prodotti dalla pagina corrente
            prodotti = await page.evaluate("""
                () => Array.from(document.querySelectorAll('.product-card')).map(el => ({
                    nome: el.querySelector('.name')?.textContent?.trim(),
                    prezzo: el.querySelector('.price')?.textContent?.trim(),
                }))
            """)
            risultati.extend(prodotti)

            # Prova a cliccare "Prossima pagina"
            btn_prossima = await page.query_selector("button.next-page:not([disabled])")
            if not btn_prossima:
                break
            await btn_prossima.click()
            await page.wait_for_load_state("networkidle")

        await browser.close()
        return risultati

async def intercetta_api(url: str) -> list[dict]:
    """Intercetta le chiamate XHR/fetch per ottenere dati JSON direttamente."""
    dati_api: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        async def handle_response(response):
            if "/api/prodotti" in response.url:
                try:
                    data = await response.json()
                    dati_api.extend(data.get("items", []))
                except Exception:
                    pass

        page.on("response", handle_response)
        await page.goto(url, wait_until="networkidle")
        await browser.close()
        return dati_api
```

---

# Parte C — robots.txt e etica

---

## C1. Rispettare robots.txt

```python
import urllib.robotparser
from urllib.parse import urlparse

def crea_parser_robots(base_url: str) -> urllib.robotparser.RobotFileParser:
    """Scarica e parsa robots.txt del sito."""
    rp = urllib.robotparser.RobotFileParser()
    robots_url = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}/robots.txt"
    rp.set_url(robots_url)
    rp.read()
    return rp

def posso_scrapare(rp: urllib.robotparser.RobotFileParser, url: str, user_agent: str = "MioBot") -> bool:
    return rp.can_fetch(user_agent, url)

def crawl_delay(rp: urllib.robotparser.RobotFileParser, user_agent: str = "MioBot") -> float:
    """Ritorna il Crawl-delay specificato in robots.txt."""
    delay = rp.crawl_delay(user_agent)
    return delay or 1.0   # default 1 secondo se non specificato

# Uso
rp = crea_parser_robots("https://example.com")
url_da_visitare = "https://example.com/prodotti"

if posso_scrapare(rp, url_da_visitare):
    delay = crawl_delay(rp)
    # Rispetta il delay
    import time
    time.sleep(delay)
    # ... scarica la pagina
else:
    print(f"robots.txt vieta l'accesso a {url_da_visitare}")
```

---

# Parte D — Anti-pattern e troubleshooting

---

## D1. Anti-pattern comuni

```python
# SBAGLIATO: nessun rate limiting
def cattiva_pratica():
    for url in urls:
        r = requests.get(url)   # DDoS involontario!
        # Nessuna pausa, nessun backoff

# SBAGLIATO: non gestire errori
def altra_cattiva_pratica(url):
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    return soup.find(".prezzo").text   # AttributeError se non trovato!

# CORRETTO
def buona_pratica(url: str) -> str | None:
    try:
        r = httpx.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        el = soup.select_one(".prezzo")
        return el.text.strip() if el else None
    except httpx.HTTPError as e:
        logger.error(f"HTTP error {e}")
        return None
    except Exception as e:
        logger.error(f"Parsing error: {e}")
        return None
```

## D2. Debug di selettori CSS

```python
from bs4 import BeautifulSoup

def debug_selettore(html: str, selettore: str) -> None:
    soup = BeautifulSoup(html, "lxml")
    elementi = soup.select(selettore)
    print(f"Selettore '{selettore}' ha trovato {len(elementi)} elementi")
    for i, el in enumerate(elementi[:3]):
        print(f"  [{i}] tag={el.name}, text='{el.text[:50].strip()}', attrs={dict(el.attrs)}")

# Con Playwright — debug in browser
async def debug_playwright(url: str) -> None:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)   # headless=False per vedere
        page = await browser.new_page()
        await page.goto(url)
        await page.pause()   # apre il Playwright Inspector
        await browser.close()
```

---

# Parte E — Riepilogo

## Scelta dello strumento

| Scenario | Strumento |
|---|---|
| HTML statico, veloce | httpx + BeautifulSoup |
| Molte pagine in parallelo | httpx async + asyncio.TaskGroup |
| JavaScript richiesto | Playwright headless |
| Sito con SPA/React/Vue | Playwright + intercettazione API |
| Scraping industriale | Scrapy |

## Checklist prima di iniziare uno scraping

- [ ] Controllare i Termini di Servizio del sito
- [ ] Leggere e rispettare `robots.txt`
- [ ] Identificare se esiste un'API ufficiale
- [ ] Impostare rate limiting (≥1s tra richieste per siti piccoli)
- [ ] Usare User-Agent identificativo con contatti
- [ ] Implementare retry con backoff esponenziale
- [ ] Non salvare PII senza consenso (GDPR)
- [ ] Cachare le risposte per evitare richieste duplicate

## Prossimi passi

- `tutorial_16_automazione.md` — automazione con scheduling e watchdog
- `tutorial_17_network_programming.md` — socket TCP/UDP, protocolli di rete
