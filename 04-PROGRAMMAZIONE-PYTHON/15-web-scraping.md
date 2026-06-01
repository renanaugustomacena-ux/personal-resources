---
corso: "Programmazione Python"
fase: "3 — Librerie e Framework"
modulo: "15"
titolo: "Web Scraping"
versione: "requests 2.32+ / Playwright 1.x / Scrapy 2.11+ / BeautifulSoup 4.12+"
livello: "Intermedio"
prerequisiti:
  - "01-06 — Python Base"
  - "06 — Regex e Text Processing"
  - "17 — Network Programming"
obiettivi:
  - "Estrarre dati da pagine web con BeautifulSoup e lxml"
  - "Automatizzare browser con Playwright per contenuti JavaScript"
  - "Costruire spider scalabili con Scrapy"
  - "Gestire anti-scraping: rate limiting, rotazione proxy, stealth"
  - "Validare e strutturare dati estratti con Pydantic"
  - "Rispettare robots.txt, ToS e considerazioni legali/etiche"
tag: [web-scraping, BeautifulSoup, Playwright, Scrapy, requests, lxml, proxy, anti-scraping]
---

# Web Scraping — Guida Completa

> **Modulo 15** · **Aggiornamento:** 2026-05-24 · **Versione:** requests 2.32+ / Playwright 1.x / Scrapy 2.11+ / BeautifulSoup 4.12+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Python Base](01-fondamenti-linguaggio.md), [Regex](06-regex-e-text-processing.md), [Network Programming](17-network-programming.md)
>
> Al termine di questo modulo saprai:
> 1. Estrarre dati da pagine web con BeautifulSoup e lxml
> 2. Automatizzare browser con Playwright per contenuti JavaScript-rendered
> 3. Costruire spider scalabili con Scrapy e pipeline di elaborazione
> 4. Gestire tecniche anti-scraping: rate limiting, rotazione proxy, stealth
> 5. Validare e strutturare dati estratti con Pydantic
> 6. Rispettare robots.txt, ToS e considerazioni legali/etiche
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio

## Idee guida
1. **Respect `robots.txt` + ToS.** Legal/ethical.
2. **httpx async > `requests` per concurrent.**
3. **Playwright per JS-rendered.** beautifulsoup per static HTML.
4. **Rate limit + retry + user-agent rotation.**

### Mappa concettuale

```
                        ┌─────────────────────┐
                        │    WEB SCRAPING      │
                        └──────────┬──────────┘
               ┌───────────────────┼───────────────────┐
               ▼                   ▼                   ▼
      ┌────────────────┐  ┌───────────────┐   ┌───────────────┐
      │  HTML statico   │  │ JS rendering  │   │  Framework    │
      │  requests + BS4 │  │ Playwright    │   │  Scrapy       │
      │  httpx + lxml   │  │ Selenium      │   │  Pipeline     │
      └───────┬────────┘  └──────┬────────┘   └──────┬────────┘
              │                  │                    │
              ▼                  ▼                    ▼
      ┌────────────────┐  ┌───────────────┐   ┌───────────────┐
      │  Parsing        │  │ Anti-scraping │   │  Data Pipeline│
      │  CSS / XPath    │  │ CAPTCHA       │   │  Item / Export│
      │  JSON-LD        │  │ Headless det. │   │  Middleware   │
      └───────┬────────┘  └──────┬────────┘   └──────┬────────┘
              │                  │                    │
              └──────────────────┼────────────────────┘
                                 ▼
                     ┌───────────────────────┐
                     │  Etica & Legalita     │
                     │  robots.txt · ToS     │
                     │  GDPR · Rate Limit    │
                     └───────────────────────┘
```


## Indice

1. [Panoramica](#panoramica)
2. [requests + BeautifulSoup](#requests--beautifulsoup)
3. [Selenium](#selenium)
4. [Playwright](#playwright)
5. [Scrapy](#scrapy)
6. [Tecniche Avanzate](#tecniche-avanzate)
7. [Etica e Legalita](#etica-e-legalità)
8. [Best Practices](#best-practices)
9. [Playwright vs Selenium — Confronto Approfondito](#playwright-vs-selenium--confronto-approfondito)
10. [Tecniche Anti-Scraping e Contromisure](#tecniche-anti-scraping-e-contromisure)
11. [robots.txt — Parsing e Rispetto Programmatico](#robotstxt--parsing-e-rispetto-programmatico)
12. [Estrazione Dati Strutturati](#estrazione-dati-strutturati)
13. [Scraping Asincrono con aiohttp](#scraping-asincrono-con-aiohttp)
14. [Data Pipeline — dal Crawl al Database](#data-pipeline--dal-crawl-al-database)
15. [Playwright per lo Scraping — Deep Dive](#playwright-per-lo-scraping--deep-dive)
16. [Scrapy Deep Dive — Spider, Middleware, Pipeline, Crawling Distribuito](#scrapy-deep-dive--spider-middleware-pipeline-crawling-distribuito)
17. [Anti-Bot Detection ed Evasione](#anti-bot-detection-ed-evasione)
18. [Pattern di Estrazione Dati Avanzati](#pattern-di-estrazione-dati-avanzati)
19. [API Reverse Engineering](#api-reverse-engineering)
20. [Scraping di Siti JavaScript-Heavy](#scraping-di-siti-javascript-heavy)
21. [Gestione Proxy e Rotazione](#gestione-proxy-e-rotazione)
22. [Pattern di Storage dei Dati](#pattern-di-storage-dei-dati)
23. [Scraping su Larga Scala — Architettura Distribuita](#scraping-su-larga-scala--architettura-distribuita)
24. [Monitoraggio degli Scraper](#monitoraggio-degli-scraper)
25. [Testing del Codice di Scraping](#testing-del-codice-di-scraping)
26. [FAQ](#faq)
27. [Esercizi](#esercizi)
28. [Letture](#letture)
29. [Glossario](#glossario)

---

## Panoramica

### Che cos'e il Web Scraping

Il **web scraping** e la tecnica di estrazione automatica di dati da pagine web. Consiste nel
programmare script o applicazioni che navigano siti internet, scaricano il contenuto HTML delle
pagine e ne estraggono le informazioni desiderate in modo strutturato. A differenza della
navigazione manuale, il web scraping consente di raccogliere grandi quantita di dati in tempi
molto ridotti, automatizzando operazioni che sarebbero altrimenti ripetitive e dispendiose.

### Casi d'uso comuni

Il web scraping trova applicazione in numerosi contesti professionali e di ricerca:

- **Monitoraggio prezzi**: e-commerce, comparatori di prezzi, analisi della concorrenza
- **Aggregazione di notizie**: raccolta di articoli da diverse fonti per portali informativi
- **Ricerca accademica**: raccolta di dataset da fonti pubbliche per analisi statistiche
- **Lead generation**: estrazione di contatti aziendali da directory pubbliche
- **Monitoraggio social media**: analisi del sentimento, tendenze, menzioni di brand
- **Immobiliare**: raccolta di annunci e prezzi da portali immobiliari
- **Finanza**: dati di borsa, indicatori economici, report aziendali
- **SEO e marketing**: analisi dei contenuti dei concorrenti, monitoraggio del posizionamento

### Considerazioni legali ed etiche

Prima di avviare qualsiasi progetto di web scraping, e fondamentale comprendere il quadro
legale e le buone pratiche etiche.

**robots.txt**: ogni sito web puo pubblicare un file `robots.txt` nella directory radice
(es. `https://esempio.com/robots.txt`) che indica quali sezioni del sito possono essere
visitate dai bot automatici e quali no. Rispettare questo file e considerata una pratica
etica imprescindibile.

```
# Esempio di robots.txt
User-agent: *
Disallow: /admin/
Disallow: /private/
Crawl-delay: 10

User-agent: Googlebot
Allow: /
```

**Terms of Service (ToS)**: molti siti web vietano esplicitamente lo scraping nei propri
termini di servizio. Violare i ToS puo comportare conseguenze legali, il blocco dell'accesso
al sito o azioni legali civili.

**Rate limiting**: anche quando lo scraping e consentito, e essenziale limitare la frequenza
delle richieste per non sovraccaricare i server del sito target. Un numero eccessivo di
richieste in tempi brevi puo causare disservizi e configura un comportamento scorretto,
oltre a portare al ban del proprio indirizzo IP.

**GDPR e privacy**: quando si raccolgono dati personali di cittadini europei, si applica il
Regolamento Generale sulla Protezione dei Dati (GDPR). La raccolta, conservazione e
trattamento di dati personali senza base giuridica adeguata e illegale.

---

## requests + BeautifulSoup

La combinazione di **requests** e **BeautifulSoup** rappresenta il punto di partenza classico
per il web scraping in Python. `requests` gestisce le richieste HTTP, mentre `BeautifulSoup`
si occupa del parsing e dell'estrazione dei dati dall'HTML.

### Installazione

```bash
pip install requests beautifulsoup4 lxml
```

### requests

La libreria `requests` e lo strumento piu diffuso in Python per effettuare richieste HTTP.
Offre un'interfaccia pulita e intuitiva che nasconde la complessita del protocollo HTTP.

#### Richieste GET e POST

```python
import requests

# Richiesta GET semplice
response = requests.get("https://esempio.com")
print(response.status_code)    # 200
print(response.text)           # Contenuto HTML come stringa
print(response.encoding)       # Encoding della risposta
print(response.headers)        # Header della risposta

# Richiesta GET con parametri
params = {"q": "python web scraping", "page": 1}
response = requests.get("https://esempio.com/search", params=params)
# URL risultante: https://esempio.com/search?q=python+web+scraping&page=1

# Richiesta POST (es. login)
data = {"username": "utente", "password": "password123"}
response = requests.post("https://esempio.com/login", data=data)

# POST con payload JSON
import json
payload = {"nome": "Mario", "citta": "Roma"}
response = requests.post(
    "https://esempio.com/api/utenti",
    json=payload  # Serializza automaticamente e imposta Content-Type
)
```

#### Headers e User-Agent

Molti siti web verificano l'header `User-Agent` per distinguere i browser reali dai bot.
Impostare un User-Agent realistico e spesso necessario per evitare il blocco.

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
}

response = requests.get("https://esempio.com", headers=headers)
```

#### Sessioni e cookie

Le sessioni di `requests` mantengono i cookie tra le richieste successive, simulando il
comportamento di un browser reale. Questo e fondamentale per i siti che richiedono
autenticazione.

```python
# Creazione di una sessione
session = requests.Session()

# Impostazione di header predefiniti per tutte le richieste
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
})

# Login: i cookie vengono salvati automaticamente nella sessione
login_data = {"username": "utente", "password": "password123"}
session.post("https://esempio.com/login", data=login_data)

# Le richieste successive includono automaticamente i cookie di sessione
profile = session.get("https://esempio.com/profilo")
dashboard = session.get("https://esempio.com/dashboard")

# Accesso diretto ai cookie
print(session.cookies.get_dict())

# Impostazione manuale di cookie
session.cookies.set("preferenza", "scuro", domain="esempio.com")
```

#### Autenticazione

```python
# Autenticazione HTTP Basic
from requests.auth import HTTPBasicAuth

response = requests.get(
    "https://api.esempio.com/dati",
    auth=HTTPBasicAuth("utente", "password")
)

# Autenticazione con token Bearer
headers = {"Authorization": "Bearer il_tuo_token_jwt_qui"}
response = requests.get("https://api.esempio.com/dati", headers=headers)
```

#### Proxy

I proxy sono utili per distribuire le richieste su diversi indirizzi IP, evitando blocchi
e migliorando l'anonimato.

```python
proxies = {
    "http": "http://utente:password@proxy.esempio.com:8080",
    "https": "http://utente:password@proxy.esempio.com:8080",
}

response = requests.get("https://esempio.com", proxies=proxies)

# Proxy SOCKS (richiede pip install requests[socks])
proxies_socks = {
    "http": "socks5://utente:password@proxy.esempio.com:1080",
    "https": "socks5://utente:password@proxy.esempio.com:1080",
}
```

#### Timeout e gestione degli errori

```python
try:
    # Timeout: (connessione, lettura) in secondi
    response = requests.get("https://esempio.com", timeout=(5, 30))
    response.raise_for_status()  # Solleva eccezione per status 4xx/5xx
except requests.exceptions.ConnectionError:
    print("Errore di connessione")
except requests.exceptions.Timeout:
    print("Timeout della richiesta")
except requests.exceptions.HTTPError as e:
    print(f"Errore HTTP: {e.response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"Errore generico: {e}")
```

### BeautifulSoup

**BeautifulSoup** e una libreria per il parsing di documenti HTML e XML. Trasforma un
documento HTML in un albero di oggetti Python facilmente navigabile e interrogabile.

#### Parser disponibili

BeautifulSoup supporta diversi parser, ciascuno con caratteristiche specifiche:

| Parser | Installazione | Velocita | Tolleranza |
|---|---|---|---|
| `html.parser` | Incluso in Python | Media | Buona |
| `lxml` | `pip install lxml` | Molto veloce | Buona |
| `html5lib` | `pip install html5lib` | Lenta | Eccellente |

```python
from bs4 import BeautifulSoup

html = """
<html>
<head><title>Pagina di esempio</title></head>
<body>
    <div class="contenuto">
        <h1 id="titolo">Benvenuto</h1>
        <p class="intro">Questo e un paragrafo introduttivo.</p>
        <ul class="lista-prodotti">
            <li class="prodotto" data-prezzo="29.99">
                <a href="/prodotti/1">Prodotto A</a>
            </li>
            <li class="prodotto" data-prezzo="49.99">
                <a href="/prodotti/2">Prodotto B</a>
            </li>
            <li class="prodotto" data-prezzo="19.99">
                <a href="/prodotti/3">Prodotto C</a>
            </li>
        </ul>
    </div>
</body>
</html>
"""

# Creazione dell'oggetto BeautifulSoup
soup = BeautifulSoup(html, "lxml")         # Parser lxml (consigliato)
# soup = BeautifulSoup(html, "html.parser")  # Parser standard
# soup = BeautifulSoup(html, "html5lib")     # Parser piu tollerante
```

#### find() e find_all()

Questi metodi cercano elementi nel documento HTML in base a tag, attributi, classi CSS
e altri criteri.

```python
# Trovare il primo elemento per tag
titolo = soup.find("h1")
print(titolo.text)  # "Benvenuto"

# Trovare per attributo id
titolo = soup.find(id="titolo")
print(titolo.string)  # "Benvenuto"

# Trovare per classe CSS
intro = soup.find("p", class_="intro")
print(intro.text)  # "Questo e un paragrafo introduttivo."

# Trovare tutti gli elementi di un tipo
prodotti = soup.find_all("li", class_="prodotto")
for prodotto in prodotti:
    nome = prodotto.find("a").text
    prezzo = prodotto["data-prezzo"]
    link = prodotto.find("a")["href"]
    print(f"{nome}: EUR {prezzo} - {link}")

# Ricerca con attributi personalizzati
prodotti_costosi = soup.find_all("li", attrs={"data-prezzo": "49.99"})

# Ricerca con espressioni regolari
import re
paragrafi = soup.find_all("p", string=re.compile(r"introduttivo"))

# Limitare il numero di risultati
primi_due = soup.find_all("li", limit=2)
```

#### select() — Selettori CSS

Il metodo `select()` utilizza la sintassi dei selettori CSS, familiare a chi lavora con
sviluppo web.

```python
# Selettore per tag
titoli = soup.select("h1")

# Selettore per classe
prodotti = soup.select(".prodotto")

# Selettore per ID
titolo = soup.select_one("#titolo")  # select_one restituisce un solo elemento

# Selettori combinati
link_prodotti = soup.select("ul.lista-prodotti > li > a")

# Selettore per attributo
elementi_con_prezzo = soup.select("[data-prezzo]")
prodotti_cari = soup.select('[data-prezzo="49.99"]')

# Pseudo-selettori
primo_prodotto = soup.select_one("li.prodotto:first-child")
ultimo_prodotto = soup.select_one("li.prodotto:last-child")
pari = soup.select("li.prodotto:nth-of-type(2n)")
```

#### Navigazione dell'albero DOM

BeautifulSoup permette di navigare l'albero del documento in modo intuitivo, spostandosi
tra nodi padre, figli, fratelli e discendenti.

```python
lista = soup.find("ul", class_="lista-prodotti")

# Figli diretti (solo elementi, no stringhe vuote)
for figlio in lista.children:
    if figlio.name:
        print(figlio.name, figlio.text.strip())

# Tutti i discendenti (ricorsivo)
for discendente in lista.descendants:
    if discendente.name:
        print(f"  Tag: {discendente.name}")

# Genitore
primo_link = soup.find("a")
print(primo_link.parent.name)  # "li"

# Catena dei genitori
for genitore in primo_link.parents:
    if genitore.name:
        print(genitore.name)  # li -> ul -> div -> body -> html -> [document]

# Fratelli (siblings)
primo_li = soup.find("li", class_="prodotto")
fratello_successivo = primo_li.find_next_sibling("li")
fratello_precedente = fratello_successivo.find_previous_sibling("li")

# Tutti i fratelli successivi
tutti_successivi = primo_li.find_next_siblings("li")
```

#### Estrazione di testo, attributi e link

```python
# Estrarre testo
elemento = soup.find("h1")
print(elemento.text)          # Testo con spazi
print(elemento.get_text())    # Equivalente
print(elemento.string)        # Solo se contiene un unico nodo di testo
print(elemento.get_text(strip=True))  # Testo senza spazi iniziali/finali
print(elemento.get_text(separator=" | "))  # Separatore personalizzato

# Estrarre attributi
link = soup.find("a")
print(link["href"])           # Accesso diretto (KeyError se mancante)
print(link.get("href"))       # Accesso sicuro (None se mancante)
print(link.get("target", "_self"))  # Valore predefinito
print(link.attrs)             # Dizionario di tutti gli attributi

# Estrarre tutti i link della pagina
tutti_link = []
for a in soup.find_all("a", href=True):
    tutti_link.append({
        "testo": a.get_text(strip=True),
        "url": a["href"]
    })
```

#### Esempio completo di scraping

```python
import requests
from bs4 import BeautifulSoup
import csv
import time

def scrape_prodotti(url_base, num_pagine=5):
    """Scraping di un catalogo prodotti con paginazione."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    })

    tutti_prodotti = []

    for pagina in range(1, num_pagine + 1):
        url = f"{url_base}?page={pagina}"
        print(f"Scaricando pagina {pagina}...")

        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Errore nella pagina {pagina}: {e}")
            continue

        soup = BeautifulSoup(response.text, "lxml")
        prodotti = soup.select(".scheda-prodotto")

        if not prodotti:
            print(f"Nessun prodotto trovato a pagina {pagina}. Fine.")
            break

        for prodotto in prodotti:
            nome = prodotto.select_one(".nome-prodotto")
            prezzo = prodotto.select_one(".prezzo")
            valutazione = prodotto.select_one(".valutazione")
            link = prodotto.select_one("a.link-dettaglio")

            tutti_prodotti.append({
                "nome": nome.get_text(strip=True) if nome else "N/D",
                "prezzo": prezzo.get_text(strip=True) if prezzo else "N/D",
                "valutazione": valutazione.get_text(strip=True) if valutazione else "N/D",
                "url": link["href"] if link else "N/D",
            })

        # Rispetto del rate limiting
        time.sleep(2)

    return tutti_prodotti


def salva_csv(prodotti, nome_file="prodotti.csv"):
    """Salva i prodotti estratti in un file CSV."""
    if not prodotti:
        print("Nessun prodotto da salvare.")
        return

    chiavi = prodotti[0].keys()
    with open(nome_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=chiavi)
        writer.writeheader()
        writer.writerows(prodotti)

    print(f"Salvati {len(prodotti)} prodotti in {nome_file}")


# Utilizzo
prodotti = scrape_prodotti("https://esempio.com/catalogo")
salva_csv(prodotti)
```

---

## Selenium

**Selenium** e un framework per l'automazione del browser. A differenza di `requests`, che
scarica solo l'HTML statico, Selenium controlla un vero browser (Chrome, Firefox, Edge) ed
e in grado di eseguire JavaScript, attendere il caricamento dinamico dei contenuti e interagire
con la pagina come farebbe un utente reale. Questo lo rende indispensabile per lo scraping
di siti che caricano i contenuti tramite JavaScript (Single Page Application, contenuti AJAX).

### Installazione

```bash
pip install selenium webdriver-manager
```

### WebDriver Setup

Il WebDriver e il componente che permette a Selenium di comunicare con il browser. Ogni
browser richiede il proprio driver specifico.

```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Setup con Chrome e webdriver-manager (gestione automatica del driver)
options = Options()
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Setup con Firefox
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

firefox_options = webdriver.FirefoxOptions()
service_ff = FirefoxService(GeckoDriverManager().install())
driver_ff = webdriver.Firefox(service=service_ff, options=firefox_options)
```

Il pacchetto `webdriver-manager` scarica e gestisce automaticamente la versione corretta del
driver per il browser installato, eliminando la necessita di scaricare e aggiornare manualmente
i driver.

### Navigazione e ricerca degli elementi

```python
from selenium.webdriver.common.by import By

# Navigare a un URL
driver.get("https://esempio.com")

# Trovare elementi con diversi metodi
elemento_id = driver.find_element(By.ID, "titolo")
elemento_classe = driver.find_element(By.CLASS_NAME, "contenuto")
elemento_css = driver.find_element(By.CSS_SELECTOR, "div.contenuto > h1")
elemento_xpath = driver.find_element(By.XPATH, "//div[@class='contenuto']/h1")
elemento_tag = driver.find_element(By.TAG_NAME, "h1")
elemento_nome = driver.find_element(By.NAME, "campo_ricerca")
elemento_link = driver.find_element(By.LINK_TEXT, "Clicca qui")
elemento_parziale = driver.find_element(By.PARTIAL_LINK_TEXT, "Clicca")

# Trovare piu elementi
tutti_link = driver.find_elements(By.CSS_SELECTOR, "a.prodotto")
for link in tutti_link:
    print(link.text, link.get_attribute("href"))
```

### Attese (Waits)

Le attese sono fondamentali nello scraping con Selenium. Le pagine web moderne caricano i
contenuti in modo asincrono, e tentare di accedere a un elemento prima che sia presente nel DOM
causa errori.

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Attesa implicita: si applica globalmente a tutte le ricerche di elementi
driver.implicitly_wait(10)  # Attende fino a 10 secondi

# Attesa esplicita: attende una condizione specifica
wait = WebDriverWait(driver, 15)

# Attendere che un elemento sia presente nel DOM
elemento = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".risultati"))
)

# Attendere che un elemento sia visibile
elemento_visibile = wait.until(
    EC.visibility_of_element_located((By.ID, "tabella-dati"))
)

# Attendere che un elemento sia cliccabile
bottone = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.carica-altro"))
)

# Attendere che il testo sia presente in un elemento
wait.until(
    EC.text_to_be_present_in_element((By.ID, "stato"), "Completato")
)

# Attendere che un elemento scompaia (utile per spinner di caricamento)
wait.until(
    EC.invisibility_of_element_located((By.CSS_SELECTOR, ".spinner"))
)

# Gestione del timeout
try:
    elemento = wait.until(
        EC.presence_of_element_located((By.ID, "elemento-lento"))
    )
except TimeoutException:
    print("L'elemento non e stato trovato entro il tempo limite.")
```

### Interazione con la pagina

```python
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Click su un elemento
bottone = driver.find_element(By.CSS_SELECTOR, "button.invia")
bottone.click()

# Digitare testo in un campo
campo = driver.find_element(By.NAME, "ricerca")
campo.clear()                          # Pulire il campo
campo.send_keys("python scraping")     # Digitare testo
campo.send_keys(Keys.RETURN)           # Premere Invio

# Scroll della pagina
# Scroll fino in fondo
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

# Scroll fino a un elemento specifico
elemento = driver.find_element(By.ID, "sezione-bassa")
driver.execute_script("arguments[0].scrollIntoView(true);", elemento)

# Scroll incrementale (utile per infinite scroll)
import time
altezza_precedente = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    altezza_nuova = driver.execute_script("return document.body.scrollHeight")
    if altezza_nuova == altezza_precedente:
        break
    altezza_precedente = altezza_nuova

# Esecuzione di JavaScript arbitrario
titolo_pagina = driver.execute_script("return document.title;")
driver.execute_script("document.querySelector('.popup').remove();")

# Azioni complesse con ActionChains
actions = ActionChains(driver)
# Hover su un menu
menu = driver.find_element(By.CSS_SELECTOR, ".menu-dropdown")
actions.move_to_element(menu).perform()

# Drag and drop
sorgente = driver.find_element(By.ID, "draggable")
destinazione = driver.find_element(By.ID, "droppable")
actions.drag_and_drop(sorgente, destinazione).perform()
```

### Modalita headless

La modalita headless esegue il browser senza interfaccia grafica, riducendo il consumo di
risorse e consentendo l'esecuzione su server senza display.

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument("--headless=new")       # Modalita headless moderna
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

# User-Agent personalizzato (evita il rilevamento headless)
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://esempio.com")
print(driver.title)
driver.quit()
```

### Screenshot

```python
# Screenshot dell'intera pagina
driver.save_screenshot("pagina_intera.png")

# Screenshot di un singolo elemento
elemento = driver.find_element(By.CSS_SELECTOR, ".grafico")
elemento.screenshot("grafico.png")

# Screenshot con dimensioni specifiche (utile in headless)
driver.set_window_size(1920, 1080)
driver.save_screenshot("screenshot_hd.png")
```

Ricordate sempre di chiudere il browser al termine delle operazioni:

```python
driver.quit()  # Chiude il browser e il processo del driver

# Oppure usare un context manager personalizzato
from contextlib import contextmanager

@contextmanager
def browser_chrome(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    try:
        yield driver
    finally:
        driver.quit()

# Utilizzo
with browser_chrome() as driver:
    driver.get("https://esempio.com")
    print(driver.title)
```

---

## Playwright

**Playwright** e un framework di automazione del browser sviluppato da Microsoft. Rappresenta
un'evoluzione moderna rispetto a Selenium, offrendo prestazioni superiori, API piu intuitive
e funzionalita avanzate come l'auto-waiting, l'intercettazione di rete e il supporto nativo
per operazioni asincrone.

### Installazione

```bash
pip install playwright
playwright install  # Scarica i browser (Chromium, Firefox, WebKit)
```

Il comando `playwright install` scarica versioni specifiche dei browser ottimizzate per
Playwright. Non e necessario avere Chrome o Firefox gia installati sul sistema.

### API sincrona e asincrona

Playwright offre sia un'API sincrona che una asincrona. L'API sincrona e piu semplice per
script lineari, mentre quella asincrona e ideale per scraping ad alte prestazioni.

```python
# ── API Sincrona ──
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://esempio.com")
    print(page.title())
    browser.close()


# ── API Asincrona ──
import asyncio
from playwright.async_api import async_playwright

async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://esempio.com")
        print(await page.title())
        await browser.close()

asyncio.run(scrape())
```

### Browser context e pagine

Il **browser context** e un ambiente isolato simile a un profilo del browser in modalita
incognito. Ogni contesto ha i propri cookie, storage e impostazioni.

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # Creare un contesto con impostazioni specifiche
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        locale="it-IT",
        timezone_id="Europe/Rome",
        geolocation={"latitude": 41.9028, "longitude": 12.4964},
        permissions=["geolocation"],
    )

    # Creare piu pagine nello stesso contesto (condividono cookie)
    pagina1 = context.new_page()
    pagina2 = context.new_page()

    pagina1.goto("https://esempio.com/login")
    # ... effettuare login su pagina1 ...
    # pagina2 avra accesso ai cookie di autenticazione

    # Salvare e caricare lo stato di autenticazione
    context.storage_state(path="stato_auth.json")

    # Riutilizzare lo stato salvato in una sessione successiva
    context_auth = browser.new_context(storage_state="stato_auth.json")

    context.close()
    browser.close()
```

### Selettori e auto-waiting

Playwright implementa un meccanismo di **auto-waiting**: ogni azione attende automaticamente
che l'elemento sia visibile, abilitato e stabile prima di interagire. Questo elimina la
necessita di scrivere manualmente le attese nella maggior parte dei casi.

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://esempio.com")

    # Selettori CSS
    page.click("button.invia")
    page.fill("input[name='email']", "utente@esempio.com")

    # Selettori di testo
    page.click("text=Accedi")
    page.click("text=/accedi/i")  # Case insensitive con regex

    # Selettori per ruolo (accessibilita)
    page.get_by_role("button", name="Invia").click()
    page.get_by_role("textbox", name="Email").fill("utente@esempio.com")
    page.get_by_role("link", name="Registrati").click()

    # Selettori per etichetta, placeholder, testo
    page.get_by_label("Email").fill("utente@esempio.com")
    page.get_by_placeholder("Cerca...").fill("python")
    page.get_by_text("Benvenuto").is_visible()

    # Selettore per test ID (data-testid)
    page.get_by_test_id("bottone-invio").click()

    # XPath
    page.locator("xpath=//div[@class='prodotto']//span[@class='prezzo']").all()

    # Attese esplicite quando necessario
    page.wait_for_selector(".risultati", state="visible", timeout=10000)
    page.wait_for_load_state("networkidle")

    # Estrazione di dati
    titoli = page.locator(".titolo-prodotto").all_text_contents()
    prezzi = page.locator(".prezzo").all_text_contents()

    for titolo, prezzo in zip(titoli, prezzi):
        print(f"{titolo}: {prezzo}")

    browser.close()
```

### Intercettazione di rete

Una funzionalita potente di Playwright e la possibilita di intercettare e modificare le
richieste di rete, utile per catturare risposte API o bloccare risorse non necessarie.

```python
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    # Catturare risposte API
    dati_api = []

    def gestisci_risposta(response):
        if "/api/prodotti" in response.url and response.status == 200:
            try:
                dati_api.append(response.json())
            except Exception:
                pass

    page.on("response", gestisci_risposta)

    # Bloccare risorse non necessarie (velocizza lo scraping)
    def blocca_risorse(route):
        if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
            route.abort()
        else:
            route.continue_()

    page.route("**/*", blocca_risorse)

    page.goto("https://esempio.com/catalogo")
    page.wait_for_load_state("networkidle")

    print(f"Catturate {len(dati_api)} risposte API")
    for dati in dati_api:
        print(json.dumps(dati, indent=2, ensure_ascii=False))

    browser.close()
```

### Screenshot e PDF

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://esempio.com")

    # Screenshot della pagina
    page.screenshot(path="pagina.png", full_page=True)

    # Screenshot di un elemento
    page.locator(".grafico").screenshot(path="grafico.png")

    # Generazione PDF (solo Chromium)
    page.pdf(
        path="pagina.pdf",
        format="A4",
        margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"},
        print_background=True,
    )

    browser.close()
```

### Confronto con Selenium

| Caratteristica | Selenium | Playwright |
|---|---|---|
| **Auto-waiting** | Manuale (WebDriverWait) | Automatico |
| **Velocita** | Moderata | Superiore |
| **API asincrona** | Limitata | Nativa |
| **Browser supportati** | Chrome, Firefox, Edge, Safari | Chromium, Firefox, WebKit |
| **Intercettazione rete** | Limitata | Nativa e potente |
| **Generazione PDF** | Non supportata | Nativa (Chromium) |
| **Installazione browser** | Manuale o webdriver-manager | `playwright install` |
| **Comunita** | Molto ampia, matura | In crescita rapida |
| **Multi-tab/contesto** | Complesso | Semplice e isolato |

**Quando scegliere Selenium**: progetti legacy, necessita di supporto per browser specifici
(Safari nativo, vecchie versioni di IE/Edge), ampia comunita e documentazione consolidata.

**Quando scegliere Playwright**: nuovi progetti, necessita di prestazioni elevate, scraping
di SPA complesse, intercettazione di rete, generazione di PDF.

---

## Scrapy

**Scrapy** e un framework completo e ad alte prestazioni per il web scraping. A differenza
delle soluzioni basate su `requests` o `Selenium`, Scrapy e progettato specificamente per lo
scraping su larga scala: gestisce automaticamente la concorrenza, il rispetto del `robots.txt`,
la gestione degli errori e l'esportazione dei dati.

### Installazione

```bash
pip install scrapy
```

### Fondamenti

#### Struttura del progetto

```bash
# Creare un nuovo progetto Scrapy
scrapy startproject negozio_spider
cd negozio_spider
```

La struttura generata e la seguente:

```
negozio_spider/
    scrapy.cfg                # File di configurazione di deploy
    negozio_spider/
        __init__.py
        items.py              # Definizione dei modelli di dati
        middlewares.py        # Middleware personalizzati
        pipelines.py          # Pipeline di elaborazione dati
        settings.py           # Impostazioni del progetto
        spiders/              # Directory per gli spider
            __init__.py
```

#### Spider

Uno spider e una classe che definisce come navigare un sito e quali dati estrarre.

```python
# negozio_spider/spiders/prodotti_spider.py
import scrapy


class ProdottiSpider(scrapy.Spider):
    name = "prodotti"
    allowed_domains = ["esempio.com"]
    start_urls = ["https://esempio.com/catalogo"]

    def parse(self, response):
        """Metodo principale chiamato per ogni risposta."""
        # Estrarre i prodotti dalla pagina
        for prodotto in response.css("div.scheda-prodotto"):
            yield {
                "nome": prodotto.css("h2.nome::text").get(),
                "prezzo": prodotto.css("span.prezzo::text").get(),
                "descrizione": prodotto.css("p.descrizione::text").get(),
                "url": response.urljoin(
                    prodotto.css("a.dettaglio::attr(href)").get()
                ),
            }

        # Seguire il link alla pagina successiva
        prossima_pagina = response.css("a.prossima::attr(href)").get()
        if prossima_pagina:
            yield response.follow(prossima_pagina, callback=self.parse)
```

```bash
# Eseguire lo spider
scrapy crawl prodotti

# Eseguire con output su file
scrapy crawl prodotti -o prodotti.json
scrapy crawl prodotti -o prodotti.csv
```

#### CrawlSpider

Il `CrawlSpider` estende le funzionalita dello spider base con regole automatiche per
seguire i link.

```python
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class CatalogoSpider(CrawlSpider):
    name = "catalogo"
    allowed_domains = ["esempio.com"]
    start_urls = ["https://esempio.com"]

    rules = (
        # Seguire i link delle categorie senza estrarre dati
        Rule(
            LinkExtractor(allow=r"/categoria/"),
            follow=True,
        ),
        # Seguire i link dei prodotti e estrarre i dati
        Rule(
            LinkExtractor(allow=r"/prodotto/\d+"),
            callback="parse_prodotto",
            follow=False,
        ),
    )

    def parse_prodotto(self, response):
        yield {
            "nome": response.css("h1.titolo::text").get(),
            "prezzo": response.css(".prezzo-attuale::text").get(),
            "descrizione": response.css(".descrizione::text").getall(),
            "immagini": response.css(".galleria img::attr(src)").getall(),
            "url": response.url,
        }
```

#### Selettori (CSS e XPath)

Scrapy supporta sia selettori CSS che espressioni XPath, con una sintassi potenziata rispetto
a BeautifulSoup.

```python
def parse(self, response):
    # ── Selettori CSS ──
    titolo = response.css("h1::text").get()          # Primo risultato (stringa)
    prezzi = response.css(".prezzo::text").getall()   # Tutti i risultati (lista)
    link = response.css("a.prodotto::attr(href)").get()

    # ── Selettori XPath ──
    titolo = response.xpath("//h1/text()").get()
    prezzi = response.xpath("//span[@class='prezzo']/text()").getall()
    link = response.xpath("//a[@class='prodotto']/@href").get()

    # ── Combinare CSS e XPath ──
    for prodotto in response.css("div.prodotto"):
        nome = prodotto.xpath(".//h2/text()").get()  # XPath relativo al contesto
        prezzo = prodotto.css("span.prezzo::text").get()
        yield {"nome": nome, "prezzo": prezzo}

    # ── Espressioni regolari nei selettori ──
    prezzo_numerico = response.css(".prezzo::text").re_first(r"[\d,.]+")
    tutti_numeri = response.css(".prezzo::text").re(r"[\d,.]+")
```

#### Items e Item Loaders

Gli **Items** definiscono un modello strutturato per i dati estratti, mentre gli
**Item Loaders** offrono meccanismi per popolarli e pulirli in modo dichiarativo.

```python
# items.py
import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags


def pulisci_prezzo(valore):
    """Rimuove il simbolo EUR e converte in float."""
    return float(valore.replace("EUR", "").replace(",", ".").strip())


class ProdottoItem(scrapy.Item):
    nome = scrapy.Field()
    prezzo = scrapy.Field()
    descrizione = scrapy.Field()
    categoria = scrapy.Field()
    url = scrapy.Field()


class ProdottoLoader(ItemLoader):
    default_item_class = ProdottoItem
    default_output_processor = TakeFirst()  # Prende il primo valore

    nome_in = MapCompose(str.strip)
    prezzo_in = MapCompose(remove_tags, pulisci_prezzo)
    descrizione_in = MapCompose(remove_tags, str.strip)
    descrizione_out = Join(" ")  # Unisce piu stringhe


# Utilizzo nello spider
class ProdottiSpider(scrapy.Spider):
    name = "prodotti"

    def parse_prodotto(self, response):
        loader = ProdottoLoader(selector=response)
        loader.add_css("nome", "h1.titolo::text")
        loader.add_css("prezzo", "span.prezzo")
        loader.add_css("descrizione", "div.descrizione p")
        loader.add_css("categoria", "span.categoria::text")
        loader.add_value("url", response.url)
        yield loader.load_item()
```

#### Pipeline

Le **pipeline** elaborano i dati estratti dagli spider prima dell'esportazione. Sono utili
per validazione, pulizia, deduplicazione e salvataggio su database.

```python
# pipelines.py
import sqlite3


class ValidazionePipeline:
    """Scarta gli elementi senza nome o prezzo."""

    def process_item(self, item, spider):
        if not item.get("nome") or not item.get("prezzo"):
            from scrapy.exceptions import DropItem
            raise DropItem(f"Elemento incompleto: {item}")
        return item


class DeduplicazionePipeline:
    """Scarta elementi duplicati basandosi sull'URL."""

    def __init__(self):
        self.urls_visti = set()

    def process_item(self, item, spider):
        url = item.get("url")
        if url in self.urls_visti:
            from scrapy.exceptions import DropItem
            raise DropItem(f"Elemento duplicato: {url}")
        self.urls_visti.add(url)
        return item


class SQLitePipeline:
    """Salva gli elementi in un database SQLite."""

    def open_spider(self, spider):
        self.conn = sqlite3.connect("prodotti.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS prodotti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                prezzo REAL,
                descrizione TEXT,
                url TEXT UNIQUE
            )
        """)
        self.conn.commit()

    def close_spider(self, spider):
        self.conn.close()

    def process_item(self, item, spider):
        self.cursor.execute("""
            INSERT OR IGNORE INTO prodotti (nome, prezzo, descrizione, url)
            VALUES (?, ?, ?, ?)
        """, (item["nome"], item["prezzo"], item["descrizione"], item["url"]))
        self.conn.commit()
        return item
```

### Funzionalita Avanzate

#### Middleware

I middleware intercettano ed elaborano le richieste e le risposte. Sono utili per la rotazione
degli User-Agent, la gestione dei proxy e il retry personalizzato.

```python
# middlewares.py
import random


class RotazioneUserAgentMiddleware:
    """Ruota gli User-Agent ad ogni richiesta."""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0",
    ]

    def process_request(self, request, spider):
        request.headers["User-Agent"] = random.choice(self.USER_AGENTS)


class RotazioneProxyMiddleware:
    """Ruota i proxy ad ogni richiesta."""

    def __init__(self, proxy_list):
        self.proxies = proxy_list

    @classmethod
    def from_crawler(cls, crawler):
        proxy_list = crawler.settings.getlist("PROXY_LIST", [])
        return cls(proxy_list)

    def process_request(self, request, spider):
        if self.proxies:
            request.meta["proxy"] = random.choice(self.proxies)
```

#### Impostazioni (settings.py)

```python
# settings.py

# Identificazione del bot
BOT_NAME = "negozio_spider"

# Rispetto del robots.txt
ROBOTSTXT_OBEY = True

# Limitazione della velocita
DOWNLOAD_DELAY = 2                   # Secondi tra le richieste
CONCURRENT_REQUESTS = 8             # Richieste parallele totali
CONCURRENT_REQUESTS_PER_DOMAIN = 4  # Richieste parallele per dominio
RANDOMIZE_DOWNLOAD_DELAY = True     # Randomizza il delay (0.5x - 1.5x)

# Auto-throttle (adattamento automatico della velocita)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Pipeline (ordine di esecuzione: numeri piu bassi = priorita maggiore)
ITEM_PIPELINES = {
    "negozio_spider.pipelines.ValidazionePipeline": 100,
    "negozio_spider.pipelines.DeduplicazionePipeline": 200,
    "negozio_spider.pipelines.SQLitePipeline": 300,
}

# Middleware downloader personalizzati
DOWNLOADER_MIDDLEWARES = {
    "negozio_spider.middlewares.RotazioneUserAgentMiddleware": 400,
    "negozio_spider.middlewares.RotazioneProxyMiddleware": 410,
}

# Cache delle richieste (utile durante lo sviluppo)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = "httpcache"

# Retry
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Header predefiniti
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}

# Log
LOG_LEVEL = "INFO"
LOG_FILE = "scrapy.log"

# Esportazione dei dati
FEEDS = {
    "output/prodotti.json": {
        "format": "json",
        "encoding": "utf-8",
        "indent": 2,
    },
    "output/prodotti.csv": {
        "format": "csv",
        "encoding": "utf-8",
    },
}
```

#### Gestione della paginazione

```python
class PaginazioneSpider(scrapy.Spider):
    name = "paginazione"
    start_urls = ["https://esempio.com/prodotti?page=1"]

    def parse(self, response):
        # Estrarre i prodotti dalla pagina corrente
        for prodotto in response.css(".prodotto"):
            yield {
                "nome": prodotto.css("h2::text").get(),
                "prezzo": prodotto.css(".prezzo::text").get(),
            }

        # Metodo 1: Seguire il link "Pagina successiva"
        prossima = response.css("a.pagina-successiva::attr(href)").get()
        if prossima:
            yield response.follow(prossima, callback=self.parse)

        # Metodo 2: Generare URL di paginazione
        # pagina_corrente = response.css(".paginazione .attiva::text").get()
        # if pagina_corrente:
        #     prossima_num = int(pagina_corrente) + 1
        #     yield scrapy.Request(
        #         f"https://esempio.com/prodotti?page={prossima_num}",
        #         callback=self.parse
        #     )
```

#### Esportazione dei dati

```bash
# Esportazione tramite linea di comando
scrapy crawl prodotti -o risultati.json
scrapy crawl prodotti -o risultati.csv
scrapy crawl prodotti -o risultati.xml

# Formato JSON Lines (un oggetto JSON per riga, ottimo per grandi dataset)
scrapy crawl prodotti -o risultati.jl
```

Per l'esportazione su database, si utilizzano le pipeline come mostrato nella sezione
precedente (SQLitePipeline). Per database piu complessi come PostgreSQL o MongoDB:

```python
# Pipeline per MongoDB
import pymongo


class MongoDBPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get("MONGO_URI", "mongodb://localhost:27017"),
            mongo_db=crawler.settings.get("MONGO_DATABASE", "scraping"),
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[spider.name].insert_one(dict(item))
        return item
```

---

## Tecniche Avanzate

### Anti-Scraping e Contromisure

I siti web moderni implementano diverse misure per rilevare e bloccare i bot. Conoscere queste
tecniche e fondamentale per costruire scraper robusti (sempre nel rispetto della legalita e
dell'etica).

#### Rotazione degli User-Agent

Inviare sempre lo stesso User-Agent e un segnale evidente di attivita automatizzata.

```python
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
    "Gecko/20100101 Firefox/121.0",
]

# Con requests
session = requests.Session()
session.headers["User-Agent"] = random.choice(USER_AGENTS)

# Libreria dedicata: fake-useragent
# pip install fake-useragent
from fake_useragent import UserAgent
ua = UserAgent()
headers = {"User-Agent": ua.random}
```

#### Rotazione dei proxy

```python
import itertools

PROXIES = [
    "http://proxy1.esempio.com:8080",
    "http://proxy2.esempio.com:8080",
    "http://proxy3.esempio.com:8080",
]

# Rotazione circolare
proxy_cycle = itertools.cycle(PROXIES)

def richiesta_con_proxy(url):
    proxy = next(proxy_cycle)
    proxies = {"http": proxy, "https": proxy}
    try:
        response = requests.get(url, proxies=proxies, timeout=10)
        return response
    except requests.exceptions.ProxyError:
        # Provare con il prossimo proxy
        return richiesta_con_proxy(url)
```

#### Gestione dei CAPTCHA

I CAPTCHA rappresentano una delle sfide piu complesse nello scraping. Le strategie possibili
includono:

```python
# Approccio 1: Servizi di risoluzione CAPTCHA (a pagamento)
# Servizi come 2Captcha, Anti-Captcha inviano il CAPTCHA a operatori umani

# Esempio concettuale con 2Captcha
import requests

def risolvi_captcha_2captcha(api_key, site_key, page_url):
    """Invia un reCAPTCHA a 2Captcha per la risoluzione."""
    # Fase 1: Inviare il CAPTCHA
    response = requests.post("http://2captcha.com/in.php", data={
        "key": api_key,
        "method": "userrecaptcha",
        "googlekey": site_key,
        "pageurl": page_url,
    })
    captcha_id = response.text.split("|")[1]

    # Fase 2: Attendere e recuperare la soluzione
    import time
    for _ in range(30):
        time.sleep(5)
        result = requests.get(
            f"http://2captcha.com/res.php?key={api_key}"
            f"&action=get&id={captcha_id}"
        )
        if "CAPCHA_NOT_READY" not in result.text:
            return result.text.split("|")[1]

    return None

# Approccio 2: Evitare i CAPTCHA
# - Limitare la frequenza delle richieste
# - Simulare comportamento umano (movimenti del mouse, pause casuali)
# - Utilizzare le API ufficiali quando disponibili
```

#### Rate limiting e ritardi

```python
import time
import random

def scrape_con_ritardo(urls, ritardo_min=1, ritardo_max=3):
    """Scraping con ritardo casuale tra le richieste."""
    risultati = []
    for url in urls:
        response = requests.get(url)
        risultati.append(response)

        # Ritardo casuale per simulare comportamento umano
        ritardo = random.uniform(ritardo_min, ritardo_max)
        time.sleep(ritardo)

    return risultati

# Backoff esponenziale in caso di errore 429 (Too Many Requests)
def richiesta_con_backoff(url, max_tentativi=5):
    for tentativo in range(max_tentativi):
        response = requests.get(url)
        if response.status_code == 429:
            attesa = (2 ** tentativo) + random.uniform(0, 1)
            print(f"Rate limited. Attendo {attesa:.1f} secondi...")
            time.sleep(attesa)
        else:
            return response
    return None
```

#### Gestione delle sessioni

```python
def scrape_con_sessione():
    """Mantiene una sessione persistente come un browser reale."""
    session = requests.Session()

    # Simulare una prima visita alla homepage
    session.get("https://esempio.com")
    time.sleep(random.uniform(1, 2))

    # Navigare come un utente reale
    session.get("https://esempio.com/categoria/elettronica")
    time.sleep(random.uniform(1, 3))

    # Ora accedere alla pagina target
    response = session.get("https://esempio.com/prodotto/12345")
    return response
```

#### Evitare il rilevamento del browser headless

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")

# Contromisure per il rilevamento headless
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)

# Rimuovere le tracce di automazione tramite JavaScript
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['it-IT', 'it', 'en-US', 'en']
        });
        window.chrome = { runtime: {} };
    """
})
```

### Parsing Avanzato

#### Espressioni XPath

XPath e un linguaggio potente per navigare e selezionare nodi in documenti XML/HTML.

```python
from lxml import html

tree = html.fromstring(contenuto_html)

# Selezionare per attributo
titoli = tree.xpath("//h2[@class='titolo']/text()")

# Selezionare con condizioni multiple
prodotti_scontati = tree.xpath(
    "//div[@class='prodotto' and .//span[@class='sconto']]"
)

# Funzioni XPath
# contains(): testo parziale
link_pdf = tree.xpath("//a[contains(@href, '.pdf')]/@href")

# starts-with(): inizio del testo
link_immagini = tree.xpath("//img[starts-with(@src, 'https://')]/@src")

# normalize-space(): pulizia degli spazi
testi = tree.xpath("normalize-space(//div[@class='contenuto'])")

# Posizione
primo_elemento = tree.xpath("(//li[@class='prodotto'])[1]")
ultimo_elemento = tree.xpath("(//li[@class='prodotto'])[last()]")

# Assi di navigazione
fratelli = tree.xpath("//h2[@id='titolo']/following-sibling::p")
genitori = tree.xpath("//span[@class='prezzo']/ancestor::div[@class='prodotto']")
```

#### Espressioni regolari nello scraping

```python
import re
from bs4 import BeautifulSoup

soup = BeautifulSoup(html_content, "lxml")

# Trovare elementi con regex sugli attributi
link_prodotti = soup.find_all("a", href=re.compile(r"/prodotto/\d+"))

# Estrarre dati con regex dal testo
testo_prezzo = "Prezzo: EUR 29,99 (IVA inclusa)"
prezzo = re.search(r"EUR\s*([\d,]+)", testo_prezzo)
if prezzo:
    valore = float(prezzo.group(1).replace(",", "."))
    print(f"Prezzo: {valore}")  # 29.99

# Estrarre numeri di telefono
testo = "Contattaci al +39 06 1234567 o al 02-9876543"
telefoni = re.findall(r"[\+\d][\d\s\-]{7,}", testo)

# Estrarre indirizzi email
testo = "Scrivi a info@esempio.com o supporto@esempio.it"
email = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", testo)

# Pulire HTML con regex (usare BeautifulSoup quando possibile)
testo_pulito = re.sub(r"<[^>]+>", "", html_content)
testo_pulito = re.sub(r"\s+", " ", testo_pulito).strip()
```

#### JSON da JavaScript (API discovery)

Molti siti moderni caricano i dati tramite chiamate API interne. Intercettare queste chiamate
e spesso piu efficiente e affidabile del parsing dell'HTML.

```python
import requests
import json
import re
from bs4 import BeautifulSoup

# Metodo 1: Estrarre JSON incorporato nel codice JavaScript della pagina
response = requests.get("https://esempio.com/prodotti")
soup = BeautifulSoup(response.text, "lxml")

# Cercare script contenenti dati JSON
for script in soup.find_all("script"):
    testo = script.string
    if testo and "productData" in testo:
        # Estrarre l'oggetto JSON con regex
        match = re.search(r"productData\s*=\s*(\{.*?\});", testo, re.DOTALL)
        if match:
            dati = json.loads(match.group(1))
            print(json.dumps(dati, indent=2, ensure_ascii=False))

# Cercare tag script di tipo application/ld+json (dati strutturati)
for script in soup.find_all("script", type="application/ld+json"):
    dati_strutturati = json.loads(script.string)
    print(json.dumps(dati_strutturati, indent=2, ensure_ascii=False))

# Metodo 2: Analizzare le richieste di rete con gli strumenti di sviluppo
# del browser e replicarle direttamente
# Spesso i dati sono disponibili come JSON puro su endpoint API interni

headers = {
    "Accept": "application/json",
    "X-Requested-With": "XMLHttpRequest",  # Simula richiesta AJAX
}
api_response = requests.get(
    "https://esempio.com/api/prodotti?page=1&limit=50",
    headers=headers,
)
if api_response.headers.get("Content-Type", "").startswith("application/json"):
    prodotti = api_response.json()
    for prodotto in prodotti.get("risultati", []):
        print(f"{prodotto['nome']}: EUR {prodotto['prezzo']}")
```

#### Gestione dei contenuti dinamici (AJAX)

```python
import requests

# Simulare richieste AJAX per il caricamento incrementale
def scrape_infinite_scroll(url_api, max_pagine=50):
    """Simula l'infinite scroll effettuando richieste API dirette."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 Chrome/120.0.0.0",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    })

    tutti_dati = []
    for pagina in range(1, max_pagine + 1):
        response = session.get(f"{url_api}?page={pagina}&per_page=20")

        if response.status_code != 200:
            break

        dati = response.json()
        elementi = dati.get("items", [])

        if not elementi:
            break

        tutti_dati.extend(elementi)
        print(f"Pagina {pagina}: {len(elementi)} elementi")

        import time
        time.sleep(1)

    return tutti_dati
```

### Data Cleaning

La pulizia dei dati e una fase cruciale del web scraping. I dati estratti dalle pagine web
sono spesso sporchi, inconsistenti e richiedono normalizzazione prima dell'utilizzo.

#### Pulizia del testo estratto

```python
import re
import unicodedata


def pulisci_testo(testo):
    """Pulisce il testo estratto da una pagina web."""
    if not testo:
        return ""

    # Rimuovere spazi bianchi eccessivi
    testo = re.sub(r"\s+", " ", testo).strip()

    # Rimuovere caratteri di controllo
    testo = "".join(c for c in testo if not unicodedata.category(c).startswith("C")
                    or c in "\n\t")

    # Rimuovere caratteri zero-width
    testo = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", testo)

    return testo


def pulisci_prezzo(testo_prezzo):
    """Estrae un valore numerico da una stringa di prezzo."""
    if not testo_prezzo:
        return None
    # Rimuovere tutto tranne cifre, virgole e punti
    numeri = re.findall(r"[\d.,]+", testo_prezzo)
    if numeri:
        # Gestire formati europei (1.234,56) e americani (1,234.56)
        valore = numeri[0]
        if "," in valore and "." in valore:
            if valore.rindex(",") > valore.rindex("."):
                # Formato europeo: 1.234,56
                valore = valore.replace(".", "").replace(",", ".")
            else:
                # Formato americano: 1,234.56
                valore = valore.replace(",", "")
        elif "," in valore:
            valore = valore.replace(",", ".")
        return float(valore)
    return None
```

#### Gestione dell'encoding

```python
import chardet

def decodifica_risposta(response):
    """Decodifica correttamente la risposta HTTP."""
    # Tentare il rilevamento automatico dell'encoding
    encoding_rilevato = chardet.detect(response.content)
    encoding = encoding_rilevato.get("encoding", "utf-8")
    confidence = encoding_rilevato.get("confidence", 0)

    if confidence > 0.8:
        return response.content.decode(encoding)

    # Fallback: provare encoding comuni
    for enc in ["utf-8", "latin-1", "iso-8859-1", "windows-1252"]:
        try:
            return response.content.decode(enc)
        except UnicodeDecodeError:
            continue

    # Ultima risorsa
    return response.content.decode("utf-8", errors="replace")
```

#### Normalizzazione dei dati

```python
import re
from datetime import datetime


def normalizza_data(testo_data):
    """Converte diverse rappresentazioni di date in formato ISO."""
    formati = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d %B %Y",       # 15 gennaio 2024
        "%d %b %Y",       # 15 gen 2024
        "%Y-%m-%d",
        "%d.%m.%Y",
    ]
    # Mesi italiani
    mesi_it = {
        "gennaio": "01", "febbraio": "02", "marzo": "03", "aprile": "04",
        "maggio": "05", "giugno": "06", "luglio": "07", "agosto": "08",
        "settembre": "09", "ottobre": "10", "novembre": "11", "dicembre": "12",
    }
    testo_normalizzato = testo_data.lower().strip()
    for mese_it, numero in mesi_it.items():
        testo_normalizzato = testo_normalizzato.replace(mese_it, numero)

    for fmt in formati:
        try:
            data = datetime.strptime(testo_normalizzato, fmt)
            return data.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return testo_data


def normalizza_url(url, base_url):
    """Converte URL relativi in assoluti."""
    from urllib.parse import urljoin, urlparse
    url_completo = urljoin(base_url, url)
    parsed = urlparse(url_completo)
    # Rimuovere frammenti (#) e normalizzare
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
```

#### Deduplicazione

```python
import hashlib


class Deduplicatore:
    """Gestisce la deduplicazione dei dati estratti."""

    def __init__(self):
        self.hash_visti = set()

    def genera_hash(self, elemento, chiavi=None):
        """Genera un hash basato su chiavi specifiche dell'elemento."""
        if chiavi:
            valori = tuple(str(elemento.get(k, "")) for k in chiavi)
        else:
            valori = tuple(sorted(str(v) for v in elemento.values()))
        stringa = "|".join(valori)
        return hashlib.md5(stringa.encode()).hexdigest()

    def e_duplicato(self, elemento, chiavi=None):
        """Verifica se l'elemento e gia stato visto."""
        hash_elem = self.genera_hash(elemento, chiavi)
        if hash_elem in self.hash_visti:
            return True
        self.hash_visti.add(hash_elem)
        return False

    def filtra(self, elementi, chiavi=None):
        """Restituisce solo gli elementi unici."""
        return [e for e in elementi if not self.e_duplicato(e, chiavi)]


# Utilizzo
dedup = Deduplicatore()
prodotti_unici = dedup.filtra(tutti_prodotti, chiavi=["nome", "url"])
print(f"Prodotti unici: {len(prodotti_unici)}/{len(tutti_prodotti)}")
```

---

## Etica e Legalita

Il web scraping e uno strumento potente che comporta responsabilita significative. E essenziale
operare nel rispetto della legge e dell'etica professionale.

### Conformita al robots.txt

Il file `robots.txt` e lo standard de facto per comunicare ai bot quali parti di un sito
possono essere visitate. Rispettarlo e un dovere etico fondamentale.

```python
from urllib.robotparser import RobotFileParser


def verifica_permesso(url, user_agent="*"):
    """Verifica se il robots.txt consente l'accesso a un URL."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception:
        # Se non e possibile leggere il robots.txt, procedere con cautela
        return True

    return rp.can_fetch(user_agent, url)


# Utilizzo
url = "https://esempio.com/dati/catalogo"
if verifica_permesso(url):
    print("Accesso consentito dal robots.txt")
else:
    print("Accesso VIETATO dal robots.txt. Non procedere.")
```

### Termini di servizio

I Termini di Servizio (ToS) di un sito web sono un contratto legale tra il sito e l'utente.
Molti ToS vietano esplicitamente lo scraping automatizzato. Prima di avviare un progetto di
scraping, e indispensabile leggere e comprendere i ToS del sito target. La violazione dei ToS
puo comportare azioni legali, come dimostrato da numerosi casi giudiziari (ad esempio, le
cause di LinkedIn e Facebook contro scraper non autorizzati).

### Rate limiting: essere un buon cittadino digitale

Anche quando lo scraping e tecnicamente e legalmente consentito, e fondamentale rispettare le
risorse del sito target.

```python
import time
import random


class ScraperEtico:
    """Scraper che rispetta i server altrui."""

    def __init__(self, ritardo_base=2.0, fattore_casualita=0.5):
        self.ritardo_base = ritardo_base
        self.fattore_casualita = fattore_casualita
        self.sessione = requests.Session()

    def richiesta(self, url, **kwargs):
        """Effettua una richiesta con ritardo casuale."""
        # Ritardo prima della richiesta
        ritardo = self.ritardo_base + random.uniform(
            -self.fattore_casualita, self.fattore_casualita
        )
        time.sleep(max(0.5, ritardo))

        response = self.sessione.get(url, **kwargs)

        # Rispettare l'header Retry-After se presente
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited. Attendo {retry_after} secondi.")
            time.sleep(retry_after)
            return self.richiesta(url, **kwargs)

        return response
```

### Data privacy e GDPR

Il Regolamento Generale sulla Protezione dei Dati (GDPR) si applica alla raccolta di dati
personali di cittadini dell'Unione Europea, indipendentemente dalla localizzazione di chi
effettua la raccolta. I principi chiave da rispettare sono:

- **Base giuridica**: e necessaria una base giuridica per raccogliere dati personali
  (consenso, interesse legittimo, esecuzione di un contratto, ecc.)
- **Minimizzazione**: raccogliere solo i dati strettamente necessari per lo scopo dichiarato
- **Trasparenza**: gli interessati devono poter sapere come vengono trattati i loro dati
- **Sicurezza**: i dati raccolti devono essere conservati in modo sicuro
- **Diritto all'oblio**: gli interessati possono richiedere la cancellazione dei loro dati

Le sanzioni per violazione del GDPR possono raggiungere i 20 milioni di euro o il 4% del
fatturato annuo globale dell'azienda.

### Alternative allo scraping

Prima di ricorrere allo scraping, esplorare sempre le alternative disponibili:

- **API ufficiali**: molti siti offrono API documentate per l'accesso strutturato ai dati
  (Twitter/X API, Google Maps API, Amazon Product Advertising API)
- **Feed RSS/Atom**: ideali per notizie e blog, forniscono dati strutturati aggiornati
- **Open Data**: portali governativi e istituzionali pubblicano dataset aperti
  (data.gov.it, data.europa.eu)
- **Dataset pubblici**: Kaggle, Google Dataset Search, UCI Machine Learning Repository
- **Accordi commerciali**: contattare direttamente il proprietario del sito per accordi
  di licenza dati
- **Data provider**: servizi specializzati che forniscono dati gia raccolti e strutturati

---

## Best Practices

1. **Rispettare sempre il robots.txt e i Termini di Servizio.** Prima di effettuare qualsiasi
   operazione di scraping, verificare che il sito target lo consenta. Utilizzare la classe
   `RobotFileParser` di Python per analizzare programmaticamente il file `robots.txt`. Se i
   ToS vietano lo scraping, cercare alternative come API ufficiali.

2. **Implementare ritardi adeguati tra le richieste.** Non bombardare mai un server con
   richieste rapide e consecutive. Utilizzare ritardi casuali (tipicamente tra 1 e 5 secondi)
   per simulare il comportamento umano e ridurre il carico sul server. L'auto-throttle di
   Scrapy e un ottimo esempio di gestione automatica della velocita.

3. **Utilizzare sessioni HTTP e gestire correttamente i cookie.** Le sessioni mantengono lo
   stato tra le richieste, riducono il numero di connessioni TCP necessarie e consentono di
   gestire automaticamente i cookie di autenticazione. Usare `requests.Session()` per le
   soluzioni basate su requests.

4. **Gestire gli errori in modo robusto con retry e backoff esponenziale.** Le richieste HTTP
   possono fallire per molte ragioni (timeout, errori del server, rate limiting). Implementare
   sempre la logica di retry con backoff esponenziale e gestire specificamente i codici di
   stato HTTP 429, 503 e 5xx.

5. **Preferire le API alle pagine HTML quando disponibili.** Le API restituiscono dati gia
   strutturati (JSON), sono piu stabili nel tempo e generalmente piu veloci da consumare.
   Analizzare le richieste di rete nel browser (tab Network degli strumenti di sviluppo) per
   scoprire endpoint API interni prima di procedere con il parsing HTML.

6. **Estrarre i dati strutturati (JSON-LD, microdata) quando presenti.** Molti siti
   incorporano dati strutturati nelle pagine per la SEO. Cercare i tag
   `<script type="application/ld+json">` che contengono informazioni gia organizzate in
   formato JSON, spesso piu affidabili e complete dei dati visibili sulla pagina.

7. **Conservare le risposte HTTP grezze per il debug.** Durante lo sviluppo, salvare le
   risposte HTML originali in file locali. Questo consente di sviluppare e testare i selettori
   senza effettuare richieste ripetute al server, velocizzando lo sviluppo e riducendo il
   carico sul sito target. In Scrapy, attivare la cache HTTP con `HTTPCACHE_ENABLED = True`.

8. **Scrivere codice modulare e manutenibile.** Separare la logica di download, parsing,
   pulizia e salvataggio in funzioni o classi distinte. I siti web cambiano frequentemente:
   un codice ben organizzato facilita l'aggiornamento dei selettori quando la struttura della
   pagina cambia.

9. **Monitorare e validare i dati estratti.** Implementare controlli di qualita sui dati:
   verificare che i campi obbligatori siano presenti, che i valori numerici siano nel range
   atteso, che gli URL siano validi. Registrare le anomalie nei log per identificare
   rapidamente i problemi causati da cambiamenti nel sito target.

10. **Documentare e versionare il codice di scraping.** Annotare nel codice gli URL target,
    la struttura attesa della pagina, la data dell'ultimo test e le eventuali limitazioni note.
    Utilizzare il controllo di versione (Git) per tracciare le modifiche nel tempo e facilitare
    il rollback in caso di problemi.

---

> **Nota**: il web scraping e uno strumento potente che deve essere utilizzato in modo
> responsabile. Rispettare sempre le leggi vigenti, i diritti dei proprietari dei siti web e
> la privacy degli utenti. Quando possibile, privilegiare l'uso di API ufficiali e fonti
> di dati aperte.

---

## Playwright vs Selenium — Confronto Approfondito

La tabella nella sezione Playwright offre un confronto sintetico. Questa sezione approfondisce gli aspetti architetturali e operativi che guidano la scelta in progetti reali.

### Architettura del protocollo di comunicazione

**Selenium** utilizza il protocollo W3C WebDriver, che comunica con il browser attraverso un HTTP server intermedio (ChromeDriver, GeckoDriver). Ogni comando attraversa una catena: client Python -> WebDriver HTTP -> browser. Questa indirezione introduce latenza e rende complessa la gestione degli eventi asincroni.

**Playwright** comunica direttamente con il browser tramite il CDP (Chrome DevTools Protocol) per Chromium, il protocollo interno di Firefox e il protocollo di automazione di WebKit. Questa connessione diretta elimina la latenza del WebDriver e consente funzionalita come l'intercettazione della rete, l'emulazione di dispositivi e la manipolazione di contesti isolati.

```python
# Selenium: gestione manuale degli wait
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://esempio.com/spa")
elemento = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".contenuto-dinamico"))
)
testo = elemento.text

# Playwright: auto-waiting integrato
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://esempio.com/spa")
    # Playwright attende automaticamente che l'elemento sia visibile e stabile
    testo = page.locator(".contenuto-dinamico").text_content()
    browser.close()
```

### Isolamento dei contesti

Playwright supporta nativamente i **browser context**, ambienti di navigazione isolati che condividono lo stesso processo browser ma hanno cookie, storage e sessioni indipendenti. Questo e fondamentale per lo scraping parallelo.

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()

    # Due contesti isolati — come due finestre di navigazione in incognito
    contesto_utente_1 = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
        viewport={"width": 1920, "height": 1080},
        locale="it-IT",
    )
    contesto_utente_2 = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605",
        viewport={"width": 1440, "height": 900},
        locale="en-US",
    )

    pagina_1 = contesto_utente_1.new_page()
    pagina_2 = contesto_utente_2.new_page()

    # Ciascun contesto ha sessione e cookie indipendenti
    pagina_1.goto("https://esempio.com")
    pagina_2.goto("https://esempio.com")

    contesto_utente_1.close()
    contesto_utente_2.close()
    browser.close()
```

### Quando Selenium rimane la scelta migliore

- **Ecosistema legacy**: il progetto usa gia Selenium con Page Object Model consolidato
- **Safari nativo su macOS**: Selenium supporta Safari tramite SafariDriver senza browser aggiuntivi
- **Browser reale con profilo utente**: Selenium puo collegarsi a browser gia avviati con `--remote-debugging-port`
- **Grid distribuito**: Selenium Grid e maturo per l'esecuzione distribuita su decine di nodi

---

## Tecniche Anti-Scraping e Contromisure

I siti web implementano diverse tecniche per rilevare e bloccare i bot automatici. Comprendere queste difese e fondamentale per progettare scraper robusti e rispettosi.

### Rilevamento headless browser

I siti moderni utilizzano JavaScript per rilevare i browser in modalita headless. Le verifiche piu comuni includono:

- **`navigator.webdriver`**: proprieta che vale `true` nei browser controllati da automazione
- **Dimensione del viewport**: i browser headless hanno dimensioni predefinite riconoscibili
- **Plugin e lingue**: i browser headless espongono liste vuote o anomale
- **WebGL fingerprint**: il rendering WebGL in headless differisce dal browser reale

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
        ]
    )
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        locale="it-IT",
        timezone_id="Europe/Rome",
    )

    page = context.new_page()

    # Rimuovere il flag navigator.webdriver
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
    """)

    page.goto("https://esempio.com")
    browser.close()
```

### CAPTCHA — strategie lecite

I CAPTCHA sono una difesa legittima. Le strategie etiche per gestirli:

1. **Evitare i trigger**: rispettare il rate limit, usare sessioni persistenti, non eseguire azioni rapide e innaturali
2. **API ufficiali**: se il sito offre un'API, usarla al posto dello scraping
3. **Servizi di risoluzione**: servizi come 2captcha o anti-captcha risolvono CAPTCHA tramite operatori umani (costo per risoluzione)
4. **Cookie di sessione**: dopo la risoluzione manuale iniziale, persistere i cookie di sessione per evitare CAPTCHA successivi

### Rate limiting e throttling

```python
import asyncio
import random
import httpx
from dataclasses import dataclass


@dataclass
class ThrottleConfig:
    min_delay: float = 1.0
    max_delay: float = 5.0
    max_concurrent: int = 3
    backoff_factor: float = 2.0
    max_retries: int = 3


async def scrape_con_throttle(urls: list[str], config: ThrottleConfig):
    """Scraping con rate limiting adattivo e concorrenza limitata."""
    semaforo = asyncio.Semaphore(config.max_concurrent)
    risultati = []

    async def scarica(client: httpx.AsyncClient, url: str):
        async with semaforo:
            for tentativo in range(config.max_retries):
                ritardo = random.uniform(config.min_delay, config.max_delay)
                await asyncio.sleep(ritardo)

                try:
                    risposta = await client.get(url, timeout=30.0)

                    if risposta.status_code == 429:
                        # Too Many Requests — backoff esponenziale
                        attesa = config.backoff_factor ** (tentativo + 1)
                        retry_after = risposta.headers.get("Retry-After")
                        if retry_after:
                            attesa = float(retry_after)
                        await asyncio.sleep(attesa)
                        continue

                    risposta.raise_for_status()
                    risultati.append({"url": url, "html": risposta.text})
                    return
                except httpx.HTTPStatusError:
                    if tentativo == config.max_retries - 1:
                        risultati.append({"url": url, "errore": "max retry"})

    async with httpx.AsyncClient(
        headers={"User-Agent": "MioBot/1.0 (+https://miosito.com/bot)"},
        follow_redirects=True,
    ) as client:
        tasks = [scarica(client, url) for url in urls]
        await asyncio.gather(*tasks)

    return risultati
```

### Rotazione User-Agent e proxy

```python
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def headers_randomizzati() -> dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
```

---

## robots.txt — Parsing e Rispetto Programmatico

Il modulo `urllib.robotparser` della libreria standard consente di verificare programmaticamente se un URL e accessibile secondo il file `robots.txt` del sito.

```python
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin


class RobotsChecker:
    """Verifica il rispetto del robots.txt prima dello scraping."""

    def __init__(self, base_url: str, user_agent: str = "MioBot"):
        self.base_url = base_url
        self.user_agent = user_agent
        self.parser = RobotFileParser()
        self.parser.set_url(urljoin(base_url, "/robots.txt"))
        self.parser.read()

    def puo_accedere(self, percorso: str) -> bool:
        """Verifica se il percorso e accessibile per il nostro user-agent."""
        url = urljoin(self.base_url, percorso)
        return self.parser.can_fetch(self.user_agent, url)

    def crawl_delay(self) -> float | None:
        """Restituisce il crawl-delay consigliato, se presente."""
        return self.parser.crawl_delay(self.user_agent)

    def sitemap(self) -> list[str]:
        """Restituisce gli URL delle sitemap dichiarate."""
        sitemaps = self.parser.site_maps()
        return sitemaps if sitemaps else []


# Utilizzo
checker = RobotsChecker("https://esempio.com", user_agent="MioScraper/1.0")

percorsi_da_verificare = ["/catalogo", "/admin", "/api/prodotti", "/profilo/utente"]
for percorso in percorsi_da_verificare:
    consentito = checker.puo_accedere(percorso)
    print(f"  {percorso}: {'consentito' if consentito else 'BLOCCATO'}")

delay = checker.crawl_delay()
if delay:
    print(f"Crawl delay consigliato: {delay} secondi")
```

### Considerazioni legali per giurisdizione

| Aspetto | UE (GDPR) | USA | Italia |
|---------|-----------|-----|--------|
| Dati personali | Trattamento richiede base giuridica | Varia per stato (CCPA in California) | GDPR + Codice Privacy |
| Database right | Direttiva 96/9/CE — protegge investimento nella raccolta dati | Non esiste equivalente federale | Recepita nel d.lgs. 169/1999 |
| ToS violation | Puo configurare illecito contrattuale | CFAA (Computer Fraud and Abuse Act) | Art. 615-ter c.p. (accesso abusivo) |
| Web scraping commerciale | Legittimo interesse puo applicarsi | hiQ Labs v. LinkedIn (2022) — dati pubblici scrapabili | Caso per caso — giurisprudenza in evoluzione |

---

## Estrazione Dati Strutturati

Molti siti incorporano dati strutturati nelle pagine HTML per migliorare la SEO. Estrarre questi dati e piu affidabile del parsing del DOM visuale.

### JSON-LD

```python
import json
import httpx
from bs4 import BeautifulSoup


def estrai_jsonld(html: str) -> list[dict]:
    """Estrae tutti i blocchi JSON-LD da una pagina HTML."""
    soup = BeautifulSoup(html, "lxml")
    blocchi = soup.find_all("script", {"type": "application/ld+json"})
    risultati = []
    for blocco in blocchi:
        try:
            dati = json.loads(blocco.string)
            if isinstance(dati, list):
                risultati.extend(dati)
            else:
                risultati.append(dati)
        except json.JSONDecodeError:
            continue
    return risultati


# Utilizzo
risposta = httpx.get("https://esempio.com/prodotto/123")
dati_strutturati = estrai_jsonld(risposta.text)

for dato in dati_strutturati:
    tipo = dato.get("@type", "Sconosciuto")
    print(f"Tipo: {tipo}")
    if tipo == "Product":
        print(f"  Nome: {dato.get('name')}")
        print(f"  Prezzo: {dato.get('offers', {}).get('price')}")
        print(f"  Valuta: {dato.get('offers', {}).get('priceCurrency')}")
```

### Microdata e Open Graph

```python
from bs4 import BeautifulSoup


def estrai_open_graph(html: str) -> dict[str, str]:
    """Estrae i metadati Open Graph da una pagina."""
    soup = BeautifulSoup(html, "lxml")
    og = {}
    for tag in soup.find_all("meta", attrs={"property": True}):
        proprietà = tag["property"]
        if proprietà.startswith("og:"):
            og[proprietà] = tag.get("content", "")
    return og


def estrai_microdata(html: str) -> list[dict]:
    """Estrae gli elementi con attributi microdata itemscope/itemprop."""
    soup = BeautifulSoup(html, "lxml")
    items = []
    for scope in soup.find_all(attrs={"itemscope": True}):
        item = {"tipo": scope.get("itemtype", "")}
        for prop in scope.find_all(attrs={"itemprop": True}):
            nome = prop["itemprop"]
            valore = prop.get("content") or prop.get("href") or prop.get_text(strip=True)
            item[nome] = valore
        items.append(item)
    return items
```

---

## Scraping Asincrono con aiohttp

Per operazioni su larga scala, `aiohttp` con `asyncio` offre throughput significativamente superiore rispetto a `requests` sincrono.

```python
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from dataclasses import dataclass, field


@dataclass
class RisultatoScraping:
    url: str
    titolo: str = ""
    stato: int = 0
    errore: str = ""


async def scrape_pagina(
    session: aiohttp.ClientSession,
    url: str,
    semaforo: asyncio.Semaphore,
) -> RisultatoScraping:
    """Scarica e parsa una singola pagina con concorrenza limitata."""
    async with semaforo:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, "lxml")
                titolo = soup.title.string.strip() if soup.title and soup.title.string else ""
                return RisultatoScraping(url=url, titolo=titolo, stato=resp.status)
        except asyncio.TimeoutError:
            return RisultatoScraping(url=url, errore="timeout")
        except aiohttp.ClientError as e:
            return RisultatoScraping(url=url, errore=str(e))


async def scrape_batch(urls: list[str], max_concorrenza: int = 10) -> list[RisultatoScraping]:
    """Scraping asincrono di un batch di URL con concorrenza controllata."""
    semaforo = asyncio.Semaphore(max_concorrenza)
    connector = aiohttp.TCPConnector(limit=max_concorrenza, ttl_dns_cache=300)

    async with aiohttp.ClientSession(
        connector=connector,
        headers={"User-Agent": "MioBot/1.0 (+https://miosito.com/bot)"},
    ) as session:
        tasks = [scrape_pagina(session, url, semaforo) for url in urls]
        return await asyncio.gather(*tasks)


# Utilizzo
urls = [f"https://esempio.com/pagina/{i}" for i in range(1, 101)]
risultati = asyncio.run(scrape_batch(urls, max_concorrenza=5))

successi = sum(1 for r in risultati if r.stato == 200)
errori = sum(1 for r in risultati if r.errore)
print(f"Successi: {successi}, Errori: {errori}")
```

---

## Data Pipeline — dal Crawl al Database

Un progetto di scraping professionale necessita di una pipeline strutturata che separi il download, il parsing, la validazione e la persistenza dei dati.

```python
"""Pipeline di scraping: download -> parsing -> validazione -> storage."""
from dataclasses import dataclass, field
from datetime import datetime
import json
import sqlite3
from pathlib import Path
import httpx
from bs4 import BeautifulSoup


@dataclass
class Prodotto:
    nome: str
    prezzo: float
    valuta: str = "EUR"
    url: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class Downloader:
    """Scarica le pagine con cache locale."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(
            follow_redirects=True,
            timeout=30.0,
            headers={"User-Agent": "MioBot/1.0"},
        )

    def scarica(self, url: str) -> str:
        cache_file = self.cache_dir / f"{hash(url)}.html"
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")
        risposta = self.client.get(url)
        risposta.raise_for_status()
        cache_file.write_text(risposta.text, encoding="utf-8")
        return risposta.text


class Parser:
    """Estrae dati strutturati dall'HTML."""

    def parse_lista_prodotti(self, html: str, base_url: str) -> list[Prodotto]:
        soup = BeautifulSoup(html, "lxml")
        prodotti = []
        for card in soup.select(".scheda-prodotto"):
            nome = card.select_one("h2.nome")
            prezzo = card.select_one("span.prezzo")
            link = card.select_one("a.dettaglio")
            if nome and prezzo:
                try:
                    prezzo_val = float(
                        prezzo.get_text(strip=True)
                        .replace("€", "").replace(",", ".").strip()
                    )
                    prodotti.append(Prodotto(
                        nome=nome.get_text(strip=True),
                        prezzo=prezzo_val,
                        url=f"{base_url}{link['href']}" if link else "",
                    ))
                except (ValueError, KeyError):
                    continue
        return prodotti


class Storage:
    """Salva i dati in SQLite."""

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS prodotti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                prezzo REAL NOT NULL,
                valuta TEXT DEFAULT 'EUR',
                url TEXT,
                timestamp TEXT
            )
        """)

    def salva_batch(self, prodotti: list[Prodotto]) -> int:
        inseriti = 0
        for p in prodotti:
            self.conn.execute(
                "INSERT INTO prodotti (nome, prezzo, valuta, url, timestamp) VALUES (?, ?, ?, ?, ?)",
                (p.nome, p.prezzo, p.valuta, p.url, p.timestamp),
            )
            inseriti += 1
        self.conn.commit()
        return inseriti

    def close(self):
        self.conn.close()
```

---

## Playwright per lo Scraping — Deep Dive

La sezione precedente su Playwright ne introduce le basi. Qui approfondiamo le tecniche avanzate che lo rendono lo strumento di riferimento per lo scraping di siti moderni nel 2025-2026.

### Playwright Stealth — Eludere il Rilevamento

Il pacchetto `playwright-stealth` applica patch automatiche al browser per nascondere i segnali tipici dell'automazione. Interviene su `navigator.webdriver`, plugin mancanti, codec incoerenti e fingerprint WebGL/Canvas.

```bash
pip install playwright-stealth
```

```python
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async


async def scrape_stealth(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="it-IT",
            timezone_id="Europe/Rome",
        )
        page = await context.new_page()
        await stealth_async(page)

        await page.goto(url, wait_until="networkidle")
        contenuto = await page.content()

        await browser.close()
        return contenuto


html = asyncio.run(scrape_stealth("https://esempio.com"))
```

### Fingerprint Realistici con fingerprint-suite

`playwright-stealth` risolve i leak piu evidenti ma non genera fingerprint statisticamente realistici. La libreria `fingerprint-suite` (del progetto Apify) usa una rete bayesiana generativa addestrata su dati reali di navigazione per produrre fingerprint che si confondono con il traffico legittimo.

```python
# pip install fingerprint-suite
from fingerprint_suite import FingerprintGenerator

generatore = FingerprintGenerator(
    browsers=["chrome"],
    operating_systems=["windows", "macos"],
    locales=["it-IT", "en-US"],
)

fingerprint = generatore.generate()
# fingerprint contiene: user_agent, viewport, headers, WebGL vendor/renderer,
# canvas hash, audio context, ecc.

# Applicare il fingerprint a un contesto Playwright
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=fingerprint.navigator.user_agent,
        viewport={
            "width": fingerprint.screen.width,
            "height": fingerprint.screen.height,
        },
        locale=fingerprint.navigator.language,
    )
    page = context.new_page()
    # Iniettare override JavaScript per canvas, WebGL, ecc.
    page.add_init_script(fingerprint.to_playwright_script())
    page.goto("https://esempio.com")
    browser.close()
```

### Scraping Parallelo con Contesti Multipli

Playwright consente di aprire decine di contesti isolati sullo stesso processo browser, ciascuno con cookie, storage e fingerprint indipendenti. Questo approccio e molto piu efficiente rispetto a lanciare processi browser separati.

```python
import asyncio
from playwright.async_api import async_playwright


async def scrape_pagina(context, url: str) -> dict:
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        titolo = await page.title()
        # Estrarre dati con selettori
        prezzi = await page.locator(".prezzo").all_text_contents()
        return {"url": url, "titolo": titolo, "prezzi": prezzi}
    except Exception as e:
        return {"url": url, "errore": str(e)}
    finally:
        await page.close()


async def scrape_parallelo(urls: list[str], max_parallelo: int = 5):
    semaforo = asyncio.Semaphore(max_parallelo)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        async def con_semaforo(url):
            async with semaforo:
                return await scrape_pagina(context, url)

        risultati = await asyncio.gather(
            *[con_semaforo(u) for u in urls]
        )
        await browser.close()
        return risultati


urls = [f"https://esempio.com/prodotto/{i}" for i in range(1, 51)]
dati = asyncio.run(scrape_parallelo(urls, max_parallelo=5))
```

### Intercettazione Avanzata delle Risposte

Oltre al blocco delle risorse non necessarie, Playwright consente di catturare le risposte API in transito, modificare le richieste in uscita e iniettare header personalizzati.

```python
from playwright.sync_api import sync_playwright
import json


def cattura_api_e_scrape(url_target: str, pattern_api: str) -> list[dict]:
    """Intercetta le risposte API e le raccoglie."""
    risposte_api = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def intercetta_risposta(response):
            if pattern_api in response.url and response.ok:
                try:
                    dati = response.json()
                    risposte_api.append(dati)
                except Exception:
                    pass

        page.on("response", intercetta_risposta)

        # Modificare header per tutte le richieste in uscita
        page.route("**/*", lambda route: route.continue_(
            headers={
                **route.request.headers,
                "X-Custom-Header": "valore",
            }
        ))

        page.goto(url_target)

        # Attendere che le chiamate API siano completate
        page.wait_for_load_state("networkidle")

        # Simulare scroll per triggerare lazy loading
        for _ in range(5):
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            page.wait_for_timeout(1000)

        browser.close()

    return risposte_api
```

### Confronto Dettagliato Playwright vs Selenium per Scraping

| Aspetto | Selenium | Playwright |
|---------|----------|------------|
| Protocollo | W3C WebDriver (HTTP) | CDP / protocollo nativo per browser |
| Latenza per azione | ~50-100ms (indirezione HTTP) | ~5-20ms (connessione diretta) |
| Auto-waiting | No — richiede WebDriverWait esplicito | Si — ogni azione attende automaticamente |
| Contesti isolati | No — un profilo per istanza | Si — multipli contesti per istanza |
| Intercettazione rete | Solo tramite proxy esterno | Nativa — route, blocco, modifica |
| Generazione PDF | Non supportata | Nativa (solo Chromium) |
| Emulazione mobile | Limitata | Completa (device, geolocation, touch) |
| Supporto HTTP/2 | Via browser | Via browser |
| Gestione iframe | Complicata (switch_to.frame) | Semplice (frame_locator) |
| Tracciamento HAR | Plugin di terze parti | `context.tracing.start()` nativo |
| Stealth/anti-detect | undetected-chromedriver | playwright-stealth, fingerprint-suite |
| Overhead memoria | ~150-300 MB per istanza | ~100-200 MB per istanza |
| Ecosistema CI/CD | Maturo, ampia documentazione | Crescente, supporto Docker ufficiale |

**Regola pratica**: per nuovi progetti di scraping nel 2025-2026, Playwright e la scelta predefinita. Selenium resta valido solo per ecosistemi legacy gia consolidati o quando serve Safari nativo su macOS.

---

## Scrapy Deep Dive — Spider, Middleware, Pipeline, Crawling Distribuito

La sezione base su Scrapy introduce la struttura del progetto. Qui approfondiamo le componenti architetturali e le strategie di scaling.

### Architettura Interna di Scrapy

L'engine di Scrapy orchestra cinque componenti principali:

```
┌─────────────────────────────────────────────────────────┐
│                     SCRAPY ENGINE                        │
│                                                          │
│  Spider ──▶ Scheduler ──▶ Downloader ──▶ Spider          │
│    │            │              │             │            │
│    │        Dedup Filter  DL Middleware   SP Middleware   │
│    │                                        │            │
│    ▼                                        ▼            │
│  Items ─────────────────────────────▶ Item Pipeline      │
│                                          │               │
│                                     ┌────┴────┐         │
│                                     │ Export   │         │
│                                     │ Storage  │         │
│                                     └─────────┘         │
└─────────────────────────────────────────────────────────┘
```

1. **Spider**: genera le richieste iniziali e parsa le risposte
2. **Scheduler**: gestisce la coda delle richieste con deduplicazione
3. **Downloader**: esegue le richieste HTTP (con middleware)
4. **Downloader Middleware**: intercetta richieste/risposte (proxy, UA, retry)
5. **Spider Middleware**: modifica le risposte prima che arrivino allo spider
6. **Item Pipeline**: elabora, valida e salva i dati estratti

### Spider Avanzati — Pattern Comuni

#### Spider con Login e Sessione Autenticata

```python
import scrapy


class SpiderAutenticato(scrapy.Spider):
    name = "autenticato"
    login_url = "https://esempio.com/login"
    start_urls = ["https://esempio.com/dashboard"]

    def start_requests(self):
        # Prima effettuare il login
        yield scrapy.FormRequest(
            url=self.login_url,
            formdata={
                "username": self.settings.get("LOGIN_USER"),
                "password": self.settings.get("LOGIN_PASS"),
            },
            callback=self.dopo_login,
        )

    def dopo_login(self, response):
        # Verificare che il login sia riuscito
        if "Benvenuto" in response.text:
            self.logger.info("Login riuscito")
            for url in self.start_urls:
                yield scrapy.Request(url, callback=self.parse)
        else:
            self.logger.error("Login fallito")

    def parse(self, response):
        for riga in response.css("table.dati tr"):
            yield {
                "colonna_1": riga.css("td:nth-child(1)::text").get(),
                "colonna_2": riga.css("td:nth-child(2)::text").get(),
            }
```

#### Spider con Profondita Controllata e Meta-dati

```python
import scrapy


class SpiderProfondita(scrapy.Spider):
    name = "profondita"
    start_urls = ["https://esempio.com"]
    custom_settings = {
        "DEPTH_LIMIT": 3,
        "DEPTH_STATS_VERBOSE": True,
    }

    def parse(self, response):
        profondita = response.meta.get("depth", 0)
        yield {
            "url": response.url,
            "titolo": response.css("title::text").get(),
            "profondita": profondita,
        }

        if profondita < 3:
            for link in response.css("a[href]::attr(href)").getall():
                yield response.follow(
                    link,
                    callback=self.parse,
                    meta={"depth": profondita + 1},
                )
```

### Downloader Middleware Avanzati

I downloader middleware formano una catena che processa ogni richiesta in uscita e ogni risposta in entrata. Oltre alla rotazione User-Agent e proxy (gia vista), middleware avanzati gestiscono retry intelligenti, cookie rotation e ban detection.

```python
# middlewares.py
import logging
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message


class BanDetectionMiddleware:
    """Rileva pagine di ban/blocco e forza il retry con nuovo proxy."""

    BAN_MARKERS = [
        "access denied",
        "blocked",
        "captcha",
        "please verify you are human",
        "too many requests",
    ]

    def process_response(self, request, response, spider):
        if response.status in (403, 429, 503):
            spider.logger.warning(
                f"Possibile ban (HTTP {response.status}): {request.url}"
            )
            return self._retry(request, response, spider)

        body_lower = response.text[:2000].lower()
        for marker in self.BAN_MARKERS:
            if marker in body_lower:
                spider.logger.warning(
                    f"Ban rilevato (marker: '{marker}'): {request.url}"
                )
                return self._retry(request, response, spider)

        return response

    def _retry(self, request, response, spider):
        retry_count = request.meta.get("retry_times", 0)
        if retry_count < 3:
            new_request = request.copy()
            new_request.meta["retry_times"] = retry_count + 1
            new_request.dont_filter = True
            return new_request
        return response


class CookieRotationMiddleware:
    """Ruota i cookie jar tra le richieste per evitare il tracking."""

    def __init__(self, num_jar: int = 10):
        self.num_jar = num_jar
        self.contatore = 0

    @classmethod
    def from_crawler(cls, crawler):
        return cls(num_jar=crawler.settings.getint("COOKIE_JAR_COUNT", 10))

    def process_request(self, request, spider):
        self.contatore = (self.contatore + 1) % self.num_jar
        request.meta["cookiejar"] = self.contatore
```

### Pipeline Avanzate — Validazione con Pydantic

```python
# pipelines.py
from pydantic import BaseModel, field_validator, ValidationError
from scrapy.exceptions import DropItem
from datetime import datetime


class ProdottoSchema(BaseModel):
    nome: str
    prezzo: float
    url: str
    categoria: str = ""
    timestamp: str = ""

    @field_validator("prezzo")
    @classmethod
    def prezzo_positivo(cls, v):
        if v <= 0:
            raise ValueError("Il prezzo deve essere positivo")
        return round(v, 2)

    @field_validator("nome")
    @classmethod
    def nome_non_vuoto(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome troppo corto")
        return v


class PydanticValidationPipeline:
    """Valida ogni item con Pydantic prima di proseguire nella pipeline."""

    def process_item(self, item, spider):
        try:
            validato = ProdottoSchema(**dict(item))
            # Restituire come dizionario per compatibilita con le pipeline successive
            return dict(validato)
        except ValidationError as e:
            raise DropItem(f"Validazione fallita per {item.get('url', '?')}: {e}")
```

### Scrapy + Playwright — Rendering JavaScript dentro Scrapy

Il pacchetto `scrapy-playwright` integra Playwright come download handler di Scrapy, consentendo il rendering JavaScript mantenendo la pipeline e i middleware di Scrapy.

```bash
pip install scrapy-playwright
```

```python
# settings.py
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}
```

```python
# spiders/spa_spider.py
import scrapy


class SPASpider(scrapy.Spider):
    name = "spa"
    start_urls = ["https://esempio.com/app"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        # Attendere il caricamento del contenuto dinamico
                        {"method": "wait_for_selector", "args": [".contenuto-dinamico"]},
                    ],
                },
            )

    def parse(self, response):
        # response.text contiene l'HTML dopo il rendering JavaScript
        for card in response.css(".card-prodotto"):
            yield {
                "nome": card.css("h3::text").get(),
                "prezzo": card.css(".prezzo::text").get(),
            }
```

### Crawling Distribuito con Scrapy-Redis

`scrapy-redis` sostituisce lo scheduler in-memory di Scrapy con una coda Redis condivisa, consentendo a piu istanze di spider di lavorare in parallelo su macchine diverse.

```bash
pip install scrapy-redis
```

```python
# settings.py per crawling distribuito
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
SCHEDULER_PERSIST = True
REDIS_URL = "redis://redis-host:6379/0"

# Coda di tipo priorita (alternative: SpiderQueue, SpiderStack)
SCHEDULER_QUEUE_CLASS = "scrapy_redis.queue.SpiderPriorityQueue"
```

```python
# spiders/distribuito_spider.py
from scrapy_redis.spiders import RedisSpider


class SpiderDistribuito(RedisSpider):
    name = "distribuito"
    redis_key = "distribuito:start_urls"

    def parse(self, response):
        for prodotto in response.css(".prodotto"):
            yield {
                "nome": prodotto.css("h2::text").get(),
                "prezzo": prodotto.css(".prezzo::text").get(),
                "url": response.urljoin(
                    prodotto.css("a::attr(href)").get()
                ),
            }

        prossima = response.css("a.next::attr(href)").get()
        if prossima:
            yield response.follow(prossima, callback=self.parse)
```

```bash
# Avviare le istanze dello spider (su macchine diverse)
scrapy crawl distribuito

# Iniettare URL nella coda Redis
redis-cli lpush distribuito:start_urls "https://esempio.com/catalogo?page=1"
redis-cli lpush distribuito:start_urls "https://esempio.com/catalogo?page=2"
```

---

## Anti-Bot Detection ed Evasione

I sistemi anti-bot moderni (Cloudflare, DataDome, PerimeterX/HUMAN, Kasada, Akamai Bot Manager) utilizzano tecniche sofisticate che vanno ben oltre il semplice controllo dello User-Agent.

### Vettori di Rilevamento

I principali segnali analizzati dai sistemi anti-bot:

| Categoria | Segnali | Livello di difficolta evasione |
|-----------|---------|-------------------------------|
| HTTP Header | User-Agent, Accept, Accept-Language, ordine degli header | Facile |
| TLS Fingerprint | Cipher suite, estensioni TLS, ordine (JA3/JA4) | Medio-alto |
| JavaScript | navigator.webdriver, plugin, lingue, canvas, WebGL | Medio |
| Comportamentale | Velocita di navigazione, pattern di mouse/tastiera | Alto |
| IP Reputation | Datacenter vs residenziale, storico abusi, geolocalizzazione | Medio |
| Browser Fingerprint | Canvas hash, AudioContext, font installati, dimensione schermo | Medio |

### TLS Fingerprinting e curl_cffi

Le librerie HTTP standard di Python (requests, httpx, aiohttp) hanno un fingerprint TLS riconoscibile perche usano la libreria `ssl` di Python, i cui cipher e la cui negoziazione differiscono da quelli di un browser reale. `curl_cffi` risolve questo problema emulando il fingerprint TLS di browser specifici.

```bash
pip install curl_cffi
```

```python
from curl_cffi import requests as cffi_requests

# Impersonare Chrome 124 — il fingerprint TLS corrisponde esattamente
response = cffi_requests.get(
    "https://esempio.com",
    impersonate="chrome124",
    headers={
        "Accept-Language": "it-IT,it;q=0.9",
    },
)
print(response.status_code)
print(response.text[:500])

# Supporta anche sessioni con cookie persistenti
session = cffi_requests.Session(impersonate="chrome124")
session.get("https://esempio.com")
risposta = session.get("https://esempio.com/prodotti")
```

### Canvas e WebGL Fingerprinting

I siti generano un hash unico basato su come il browser renderizza un'immagine canvas o una scena WebGL. I browser headless producono hash diversi da quelli reali.

```python
# Script di init per mascherare il canvas fingerprint in Playwright
CANVAS_OVERRIDE_SCRIPT = """
(function() {
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        if (type === 'image/png' || type === undefined) {
            // Aggiungere rumore impercettibile al canvas
            const ctx = this.getContext('2d');
            if (ctx) {
                const imageData = ctx.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    // Rumore di ±1 su ogni canale colore
                    imageData.data[i] += (Math.random() * 2 - 1);
                }
                ctx.putImageData(imageData, 0, 0);
            }
        }
        return originalToDataURL.apply(this, arguments);
    };

    // Override WebGL
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(param) {
        // UNMASKED_VENDOR_WEBGL
        if (param === 37445) return 'Google Inc. (NVIDIA)';
        // UNMASKED_RENDERER_WEBGL
        if (param === 37446) return 'ANGLE (NVIDIA, GeForce GTX 1650)';
        return getParameter.call(this, param);
    };
})();
"""

# Applicare in Playwright
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.add_init_script(CANVAS_OVERRIDE_SCRIPT)
    page.goto("https://bot.sannysoft.com")
    page.screenshot(path="fingerprint_test.png", full_page=True)
    browser.close()
```

### Simulazione del Comportamento Umano

I sistemi avanzati analizzano i pattern di interazione. Movimenti di mouse irrealistici, navigazione troppo veloce o assenza di scroll sono segnali di automazione.

```python
import asyncio
import random
from playwright.async_api import async_playwright


async def naviga_come_umano(page, url: str):
    """Simula un pattern di navigazione realistico."""
    await page.goto(url, wait_until="domcontentloaded")

    # Pausa iniziale come un utente che legge
    await asyncio.sleep(random.uniform(1.5, 3.0))

    # Simulare movimenti del mouse casuali
    viewport = page.viewport_size
    for _ in range(random.randint(3, 8)):
        x = random.randint(100, viewport["width"] - 100)
        y = random.randint(100, viewport["height"] - 100)
        await page.mouse.move(x, y, steps=random.randint(5, 15))
        await asyncio.sleep(random.uniform(0.1, 0.5))

    # Scroll graduale (non istantaneo)
    altezza_totale = await page.evaluate("document.body.scrollHeight")
    posizione_corrente = 0
    while posizione_corrente < altezza_totale * 0.7:
        incremento = random.randint(200, 500)
        posizione_corrente += incremento
        await page.evaluate(f"window.scrollTo(0, {posizione_corrente})")
        await asyncio.sleep(random.uniform(0.3, 1.2))

    # Pausa finale di "lettura"
    await asyncio.sleep(random.uniform(1.0, 2.5))
```

### Cloudflare Bypass — Considerazioni

Cloudflare e il sistema anti-bot piu diffuso. Il suo challenge JavaScript (`__cf_bm`, `cf_clearance`) verifica il browser tramite:

1. **JS Challenge**: esecuzione di JavaScript computazionale nel browser
2. **Managed Challenge (Turnstile)**: challenge interattivo leggero
3. **WAF Rules**: regole personalizzate basate su header, IP, rate

Strategie lecite per siti che permettono l'accesso automatizzato:

- Usare `curl_cffi` con impersonazione TLS per richieste statiche
- Usare Playwright con stealth per risolvere il JS challenge
- Persistere il cookie `cf_clearance` dopo la prima risoluzione
- Rispettare i rate limit per evitare di triggerare il WAF

```python
from curl_cffi import requests as cffi_requests


def richiesta_con_cloudflare(url: str, max_tentativi: int = 3) -> str | None:
    """Tentativo di accesso a un sito protetto da Cloudflare."""
    session = cffi_requests.Session(impersonate="chrome124")

    for tentativo in range(max_tentativi):
        response = session.get(url, timeout=30)

        if response.status_code == 200:
            return response.text

        if response.status_code == 403:
            # Cloudflare potrebbe richiedere un challenge browser
            # In questo caso serve Playwright con stealth
            break

        # Backoff
        import time
        time.sleep(2 ** tentativo)

    return None
```

---

## Pattern di Estrazione Dati Avanzati

### Selettori CSS Avanzati

Oltre ai selettori base, CSS offre pseudo-classi e combinatori potenti per la selezione precisa degli elementi.

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "lxml")

# Selettore per attributo parziale
# Attributo che inizia con un valore
link_esterni = soup.select('a[href^="https://"]')

# Attributo che finisce con un valore
documenti_pdf = soup.select('a[href$=".pdf"]')

# Attributo che contiene un valore
link_prodotti = soup.select('a[href*="prodotto"]')

# Combinatore fratello adiacente (+)
# Seleziona il paragrafo immediatamente dopo un h2
descrizioni = soup.select("h2 + p")

# Combinatore fratello generale (~)
# Seleziona tutti i paragrafi che seguono un h2
tutti_p_dopo_h2 = soup.select("h2 ~ p")

# Pseudo-classe :not()
# Tutti i div che NON hanno classe "nascosto"
visibili = soup.select("div:not(.nascosto)")

# Pseudo-classe :has() (supporto limitato in BS4, pieno in lxml)
# Container che contengono un'immagine
con_immagine = soup.select("div:has(img)")

# Selettori annidati complessi
# Terzo prodotto nella lista, il link al suo interno
terzo_link = soup.select_one(
    "ul.lista-prodotti > li:nth-child(3) > a"
)
```

### XPath Avanzato — Assi e Funzioni

XPath offre espressioni molto piu potenti dei selettori CSS, specialmente per la navigazione relativa nell'albero DOM.

```python
from lxml import html

tree = html.fromstring(contenuto_html)

# Asse ancestor — risalire l'albero
# Trovare il div.prodotto che contiene un prezzo specifico
contenitore = tree.xpath(
    "//span[text()='29.99']/ancestor::div[@class='prodotto']"
)

# Asse preceding-sibling — fratelli precedenti
# L'etichetta che precede un campo input
etichetta = tree.xpath(
    "//input[@name='email']/preceding-sibling::label[1]/text()"
)

# Asse following — tutti i nodi successivi nel documento
# Tutti i paragrafi dopo una sezione specifica
paragrafi = tree.xpath(
    "//h2[@id='sezione-target']/following::p"
)

# Funzione substring-before / substring-after
# Estrarre la parte prima di " - " in un testo
codice = tree.xpath(
    "substring-before(//span[@class='codice']/text(), ' - ')"
)

# Funzione translate — conversione caratteri (simile a str.translate)
# Convertire in minuscolo per confronto case-insensitive
risultati = tree.xpath(
    "//h2[translate(text(),"
    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
    "'abcdefghijklmnopqrstuvwxyz')='prodotto speciale']"
)

# Combinazione di condizioni con operatori logici
prodotti_in_sconto = tree.xpath(
    "//div[@class='prodotto' and .//span[@class='sconto'] "
    "and number(.//span[@class='prezzo']/text()) < 50]"
)

# Conteggio nodi
num_prodotti = tree.xpath("count(//div[@class='prodotto'])")

# Posizione condizionale
# Dal terzo al settimo prodotto
dal_terzo = tree.xpath(
    "(//div[@class='prodotto'])[position() >= 3 and position() <= 7]"
)
```

### Regex nel Contesto dello Scraping

Le regex sono utili per estrarre pattern specifici dal testo grezzo dopo il parsing DOM, non come sostituto del parser HTML.

```python
import re

# Pattern comuni nello scraping

# Prezzo con valuta variabile
PREZZO_RE = re.compile(
    r"(?:EUR|€|\$|USD|£|GBP)\s*([\d.,]+)"
    r"|"
    r"([\d.,]+)\s*(?:EUR|€|\$|USD|£|GBP)",
    re.IGNORECASE,
)

# Codice prodotto / SKU
SKU_RE = re.compile(r"\b[A-Z]{2,4}-\d{4,8}\b")

# Data in vari formati europei
DATA_EU_RE = re.compile(
    r"\b(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})\b"
)

# Numero di telefono italiano
TELEFONO_IT_RE = re.compile(
    r"(?:\+39\s?)?(?:0\d{1,4}|\d{3})[\s.\-]?\d{6,8}"
)

# Codice fiscale italiano
CF_RE = re.compile(
    r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b",
    re.IGNORECASE,
)


def estrai_pattern(testo: str) -> dict:
    """Estrae tutti i pattern riconosciuti da un blocco di testo."""
    return {
        "prezzi": PREZZO_RE.findall(testo),
        "sku": SKU_RE.findall(testo),
        "date": DATA_EU_RE.findall(testo),
        "telefoni": TELEFONO_IT_RE.findall(testo),
    }
```

---

## API Reverse Engineering

Invece di parsare l'HTML, spesso e piu efficiente e affidabile individuare le API interne che il frontend di un sito chiama e replicarle direttamente.

### Metodologia di Analisi

1. Aprire gli strumenti di sviluppo del browser (F12)
2. Tab Network -> filtrare per XHR/Fetch
3. Navigare la pagina e osservare le richieste
4. Analizzare URL, header, payload e risposta di ogni chiamata API
5. Replicare le richieste con httpx o requests

### Cattura Automatica con Playwright

```python
from playwright.sync_api import sync_playwright
import json


def cattura_chiamate_api(url: str, filtro: str = "/api/") -> list[dict]:
    """Cattura tutte le chiamate API effettuate da una pagina."""
    chiamate = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def registra_richiesta(request):
            if filtro in request.url:
                chiamate.append({
                    "metodo": request.method,
                    "url": request.url,
                    "headers": dict(request.headers),
                    "post_data": request.post_data,
                })

        def registra_risposta(response):
            if filtro in response.url:
                for c in chiamate:
                    if c["url"] == response.url and "risposta" not in c:
                        try:
                            c["risposta"] = response.json()
                        except Exception:
                            c["risposta_text"] = response.text()[:1000]
                        c["status"] = response.status
                        break

        page.on("request", registra_richiesta)
        page.on("response", registra_risposta)

        page.goto(url)
        page.wait_for_load_state("networkidle")

        # Interagire con la pagina per triggerare altre chiamate
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)

        browser.close()

    return chiamate


# Analizzare le chiamate catturate
chiamate = cattura_chiamate_api("https://esempio.com/catalogo")
for c in chiamate:
    print(f"{c['metodo']} {c['url']} -> {c.get('status', '?')}")
```

### Replicare le API Scoperte

Una volta individuata la struttura dell'API, replicarla direttamente e molto piu veloce e leggero rispetto al rendering browser.

```python
import httpx
from dataclasses import dataclass


@dataclass
class APIEndpoint:
    url: str
    metodo: str = "GET"
    headers: dict = None
    params: dict = None

    def chiama(self, client: httpx.Client, **kwargs) -> dict | None:
        merged_params = {**(self.params or {}), **kwargs}
        response = client.request(
            self.metodo,
            self.url,
            params=merged_params if self.metodo == "GET" else None,
            json=merged_params if self.metodo == "POST" else None,
        )
        response.raise_for_status()
        return response.json()


# Definire gli endpoint scoperti
api_prodotti = APIEndpoint(
    url="https://esempio.com/api/v2/products",
    headers={
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    },
    params={"per_page": 50, "sort": "price_asc"},
)

# Scraping tramite API diretta — ordini di grandezza piu veloce
with httpx.Client(headers=api_prodotti.headers, timeout=30.0) as client:
    for pagina in range(1, 101):
        dati = api_prodotti.chiama(client, page=pagina)
        prodotti = dati.get("items", [])
        if not prodotti:
            break
        for p in prodotti:
            print(f"{p['name']}: {p['price']} {p['currency']}")
```

---

## Scraping di Siti JavaScript-Heavy

I siti basati su framework JavaScript (React, Vue, Angular, Next.js, Nuxt) caricano i dati in modo dinamico. Esistono diverse strategie per gestirli, ordinate per efficienza.

### Strategia 1 — API Diretta (Preferita)

Come descritto nella sezione API Reverse Engineering: intercettare le chiamate XHR/Fetch e replicarle. Questa e sempre la prima strategia da tentare perche e la piu veloce e leggera.

### Strategia 2 — Dati Incorporati nella Pagina

Molti framework SSR (Next.js, Nuxt) includono i dati pre-renderizzati nel tag `<script id="__NEXT_DATA__">` o `<script id="__NUXT_DATA__">`.

```python
import httpx
import json
from bs4 import BeautifulSoup


def estrai_next_data(url: str) -> dict | None:
    """Estrae i dati pre-renderizzati da una pagina Next.js."""
    response = httpx.get(url)
    soup = BeautifulSoup(response.text, "lxml")

    # Next.js incorpora i dati nel tag __NEXT_DATA__
    script = soup.find("script", id="__NEXT_DATA__")
    if script and script.string:
        dati = json.loads(script.string)
        return dati.get("props", {}).get("pageProps", {})

    # Nuxt.js usa un formato diverso
    for script in soup.find_all("script"):
        if script.string and "window.__NUXT__" in script.string:
            # Il formato Nuxt richiede parsing piu complesso
            # (non e JSON puro ma JavaScript)
            pass

    return None


# Utilizzo
dati = estrai_next_data("https://esempio-nextjs.com/prodotti")
if dati:
    for prodotto in dati.get("products", []):
        print(f"{prodotto['name']}: {prodotto['price']}")
```

### Strategia 3 — Rendering con Playwright (Ultima Risorsa)

Quando le API non sono accessibili e i dati non sono pre-renderizzati, il rendering completo con Playwright e necessario. Ottimizzare bloccando le risorse non necessarie.

```python
from playwright.sync_api import sync_playwright


def scrape_spa_ottimizzato(url: str) -> list[dict]:
    """Scraping ottimizzato di una SPA bloccando risorse pesanti."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Bloccare risorse pesanti
        page.route("**/*.{png,jpg,jpeg,gif,svg,webp,avif}", lambda r: r.abort())
        page.route("**/*.{woff,woff2,ttf,eot}", lambda r: r.abort())
        page.route("**/analytics/**", lambda r: r.abort())
        page.route("**/tracking/**", lambda r: r.abort())
        page.route("**/ads/**", lambda r: r.abort())

        page.goto(url, wait_until="domcontentloaded")

        # Attendere che il contenuto dinamico sia caricato
        page.wait_for_selector("[data-loaded='true']", timeout=15000)

        # Estrarre dati
        prodotti = []
        for card in page.locator(".card-prodotto").all():
            prodotti.append({
                "nome": card.locator("h3").text_content(),
                "prezzo": card.locator(".prezzo").text_content(),
            })

        browser.close()
        return prodotti
```

---

## Gestione Proxy e Rotazione

La rotazione dei proxy e essenziale per lo scraping su larga scala. Esistono due categorie principali di proxy con caratteristiche molto diverse.

### Proxy Datacenter vs Residenziali

| Aspetto | Datacenter | Residenziali |
|---------|------------|-------------|
| Origine IP | Server in data center | Dispositivi reali di utenti |
| Velocita | Molto alta (1-5ms latenza) | Variabile (50-500ms latenza) |
| Costo | Basso (~$1-2/GB) | Alto (~$5-15/GB) |
| Detection rate | Alto — facilmente riconoscibili | Basso — IP di ISP reali |
| Casi d'uso | Siti senza anti-bot, API, volume alto | Siti con anti-bot, e-commerce, social |
| Pool tipico | 10k-100k IP | 10M-70M IP |

### Implementazione della Rotazione Proxy

```python
import httpx
import random
import time
from dataclasses import dataclass, field


@dataclass
class ProxyPool:
    """Gestisce un pool di proxy con health checking."""
    proxy_list: list[str]
    proxy_sani: list[str] = field(default_factory=list)
    proxy_falliti: dict = field(default_factory=dict)
    max_fallimenti: int = 3

    def __post_init__(self):
        self.proxy_sani = list(self.proxy_list)

    def prossimo(self) -> str | None:
        if not self.proxy_sani:
            return None
        return random.choice(self.proxy_sani)

    def segnala_fallimento(self, proxy: str):
        conteggio = self.proxy_falliti.get(proxy, 0) + 1
        self.proxy_falliti[proxy] = conteggio
        if conteggio >= self.max_fallimenti:
            if proxy in self.proxy_sani:
                self.proxy_sani.remove(proxy)

    def segnala_successo(self, proxy: str):
        self.proxy_falliti.pop(proxy, None)
        if proxy not in self.proxy_sani:
            self.proxy_sani.append(proxy)

    @property
    def disponibili(self) -> int:
        return len(self.proxy_sani)


def scrape_con_rotazione(urls: list[str], pool: ProxyPool) -> list[dict]:
    """Scraping con rotazione proxy e fallback automatico."""
    risultati = []

    for url in urls:
        for _ in range(3):  # Tentativi con proxy diversi
            proxy = pool.prossimo()
            if not proxy:
                break

            try:
                with httpx.Client(
                    proxy=proxy,
                    timeout=15.0,
                    follow_redirects=True,
                ) as client:
                    response = client.get(url)
                    response.raise_for_status()
                    pool.segnala_successo(proxy)
                    risultati.append({"url": url, "html": response.text})
                    break
            except (httpx.ProxyError, httpx.TimeoutException, httpx.HTTPStatusError):
                pool.segnala_fallimento(proxy)
                continue

        time.sleep(random.uniform(1.0, 3.0))

    return risultati
```

### Rotazione Proxy in Scrapy

```python
# middlewares.py per Scrapy
import random


class SmartProxyMiddleware:
    """Rotazione proxy con sticky session e ban detection."""

    def __init__(self, proxy_list, sticky_domains=None):
        self.proxy_list = proxy_list
        self.sticky = sticky_domains or []
        self.sticky_map = {}  # dominio -> proxy assegnato

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            proxy_list=crawler.settings.getlist("PROXY_LIST"),
            sticky_domains=crawler.settings.getlist("STICKY_PROXY_DOMAINS"),
        )

    def process_request(self, request, spider):
        from urllib.parse import urlparse
        dominio = urlparse(request.url).netloc

        if dominio in self.sticky:
            # Usare sempre lo stesso proxy per questo dominio
            if dominio not in self.sticky_map:
                self.sticky_map[dominio] = random.choice(self.proxy_list)
            request.meta["proxy"] = self.sticky_map[dominio]
        else:
            request.meta["proxy"] = random.choice(self.proxy_list)

    def process_response(self, request, response, spider):
        if response.status in (403, 429, 503):
            proxy = request.meta.get("proxy")
            spider.logger.warning(f"Proxy bloccato: {proxy}")
            # Rimuovere dal pool e ritentare
            if proxy in self.proxy_list:
                self.proxy_list.remove(proxy)
        return response
```

---

## Pattern di Storage dei Dati

La scelta dello storage dipende dal volume dei dati, dai pattern di accesso e dai requisiti di durabilita.

### SQLite — Piccoli/Medi Volumi

SQLite e ideale per progetti singoli con meno di qualche milione di righe. Zero configurazione, file singolo, transazioni ACID.

```python
import sqlite3
from contextlib import contextmanager


@contextmanager
def database(path: str):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")  # Performance di scrittura
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def crea_tabella_con_indici(conn: sqlite3.Connection, tabella: str):
    conn.executescript(f"""
        CREATE TABLE IF NOT EXISTS {tabella} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            prezzo REAL,
            categoria TEXT,
            raw_html TEXT,
            scrape_timestamp TEXT DEFAULT (datetime('now')),
            checksum TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_{tabella}_categoria
            ON {tabella}(categoria);
        CREATE INDEX IF NOT EXISTS idx_{tabella}_prezzo
            ON {tabella}(prezzo);
        CREATE INDEX IF NOT EXISTS idx_{tabella}_timestamp
            ON {tabella}(scrape_timestamp);
    """)
```

### MongoDB — Dati Semi-strutturati

MongoDB e adatto quando la struttura dei dati varia tra le pagine (e-commerce con attributi variabili per categoria, siti con schema non uniforme).

```python
from pymongo import MongoClient, UpdateOne
from datetime import datetime, timezone


class MongoStorage:
    def __init__(self, uri: str, database: str, collezione: str):
        self.client = MongoClient(uri)
        self.db = self.client[database]
        self.coll = self.db[collezione]
        # Indice unico su URL per evitare duplicati
        self.coll.create_index("url", unique=True)
        self.coll.create_index("scrape_timestamp")

    def upsert_batch(self, documenti: list[dict]) -> int:
        """Inserisce o aggiorna un batch di documenti."""
        if not documenti:
            return 0

        operazioni = []
        now = datetime.now(timezone.utc).isoformat()

        for doc in documenti:
            doc["scrape_timestamp"] = now
            operazioni.append(
                UpdateOne(
                    {"url": doc["url"]},
                    {"$set": doc},
                    upsert=True,
                )
            )

        risultato = self.coll.bulk_write(operazioni)
        return risultato.upserted_count + risultato.modified_count

    def close(self):
        self.client.close()
```

### CSV Streaming — Export Incrementale

Per dataset grandi dove il caricamento in memoria non e praticabile, il CSV streaming scrive i dati riga per riga.

```python
import csv
from pathlib import Path
from typing import Iterator


class CSVStreamer:
    """Scrive dati in CSV in modo incrementale senza caricare tutto in memoria."""

    def __init__(self, percorso: Path, campi: list[str]):
        self.percorso = percorso
        self.campi = campi
        self.file = None
        self.writer = None

    def __enter__(self):
        esiste = self.percorso.exists()
        self.file = open(self.percorso, "a", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.file, fieldnames=self.campi)
        if not esiste:
            self.writer.writeheader()
        return self

    def __exit__(self, *args):
        if self.file:
            self.file.close()

    def scrivi(self, riga: dict):
        # Filtrare solo i campi dichiarati
        riga_filtrata = {k: riga.get(k, "") for k in self.campi}
        self.writer.writerow(riga_filtrata)

    def scrivi_batch(self, righe: list[dict]):
        for riga in righe:
            self.scrivi(riga)
        self.file.flush()


# Utilizzo
campi = ["url", "nome", "prezzo", "categoria", "timestamp"]
with CSVStreamer(Path("output/prodotti.csv"), campi) as streamer:
    for batch in genera_batch_prodotti():
        streamer.scrivi_batch(batch)
```

---

## Scraping su Larga Scala — Architettura Distribuita

Per progetti che richiedono il crawling di milioni di pagine, un'architettura distribuita e necessaria.

### Architettura con Scrapy-Redis e Worker Multipli

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Worker 1   │      │   Worker 2   │      │   Worker N   │
│  Scrapy +    │      │  Scrapy +    │      │  Scrapy +    │
│  scrapy-redis│      │  scrapy-redis│      │  scrapy-redis│
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             │
                    ┌────────┴────────┐
                    │      Redis      │
                    │  Coda richieste │
                    │  Deduplicazione │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │    Storage      │
                    │  MongoDB / S3 / │
                    │  PostgreSQL     │
                    └─────────────────┘
```

### Separazione Crawl e Parsing

Una pratica fondamentale nello scraping su larga scala e separare il download dell'HTML dal parsing dei dati. Questo consente di scalare indipendentemente le due operazioni e rende il sistema piu tollerante ai guasti.

```python
# worker_download.py — Scarica HTML e lo salva in Redis
import scrapy
from scrapy_redis.spiders import RedisSpider
import json


class DownloadWorker(RedisSpider):
    name = "download_worker"
    redis_key = "download:urls"

    custom_settings = {
        "ITEM_PIPELINES": {
            "progetto.pipelines.SalvaHTMLRedisPipeline": 100,
        },
    }

    def parse(self, response):
        yield {
            "url": response.url,
            "html": response.text,
            "status": response.status,
            "headers": dict(response.headers),
        }


# worker_parse.py — Legge HTML da Redis e lo parsa
import redis
import json
from bs4 import BeautifulSoup


def worker_parse(redis_url: str, chiave_input: str, chiave_output: str):
    """Worker che legge HTML dalla coda Redis e produce dati strutturati."""
    r = redis.from_url(redis_url)

    while True:
        _, dati_raw = r.brpop(chiave_input)
        dati = json.loads(dati_raw)

        soup = BeautifulSoup(dati["html"], "lxml")

        risultato = {
            "url": dati["url"],
            "titolo": soup.title.string if soup.title else "",
            "prodotti": [],
        }

        for card in soup.select(".prodotto"):
            risultato["prodotti"].append({
                "nome": card.select_one("h2").get_text(strip=True),
                "prezzo": card.select_one(".prezzo").get_text(strip=True),
            })

        r.lpush(chiave_output, json.dumps(risultato))
```

### Gestione delle Code e Priorita

In un sistema distribuito, le code permettono di gestire le priorita di crawling e il bilanciamento del carico.

```python
# settings.py per priorita di crawling
SCHEDULER_QUEUE_CLASS = "scrapy_redis.queue.SpiderPriorityQueue"
# Le richieste con priorita piu alta (numero piu basso) vengono elaborate prima

# Nello spider — assegnare priorita
def parse(self, response):
    # Pagine prodotto: priorita alta (numero basso)
    for link in response.css("a.prodotto::attr(href)").getall():
        yield response.follow(
            link, callback=self.parse_prodotto, priority=1
        )
    # Pagine di navigazione: priorita bassa
    for link in response.css("a.paginazione::attr(href)").getall():
        yield response.follow(
            link, callback=self.parse, priority=10
        )
```

---

## Monitoraggio degli Scraper

Uno scraper in produzione necessita di monitoraggio per rilevare problemi (cambio struttura del sito, ban IP, degrado performance).

### Metriche Chiave

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricheScraper:
    """Raccoglie metriche durante l'esecuzione dello scraper."""
    inizio: float = field(default_factory=time.monotonic)
    pagine_scaricate: int = 0
    pagine_fallite: int = 0
    item_estratti: int = 0
    item_scartati: int = 0
    byte_scaricati: int = 0
    errori_per_tipo: dict = field(default_factory=dict)

    def registra_successo(self, byte_risposta: int, num_item: int):
        self.pagine_scaricate += 1
        self.byte_scaricati += byte_risposta
        self.item_estratti += num_item

    def registra_errore(self, tipo_errore: str):
        self.pagine_fallite += 1
        self.errori_per_tipo[tipo_errore] = (
            self.errori_per_tipo.get(tipo_errore, 0) + 1
        )

    def registra_scarto(self):
        self.item_scartati += 1

    @property
    def durata_secondi(self) -> float:
        return time.monotonic() - self.inizio

    @property
    def pagine_al_secondo(self) -> float:
        durata = self.durata_secondi
        return self.pagine_scaricate / durata if durata > 0 else 0

    @property
    def tasso_successo(self) -> float:
        totale = self.pagine_scaricate + self.pagine_fallite
        return self.pagine_scaricate / totale if totale > 0 else 0

    def report(self) -> str:
        return (
            f"--- Report Scraper ---\n"
            f"Durata: {self.durata_secondi:.1f}s\n"
            f"Pagine: {self.pagine_scaricate} ok, "
            f"{self.pagine_fallite} fallite "
            f"({self.tasso_successo:.1%} successo)\n"
            f"Velocita: {self.pagine_al_secondo:.1f} pagine/s\n"
            f"Item estratti: {self.item_estratti}, "
            f"scartati: {self.item_scartati}\n"
            f"Dati scaricati: {self.byte_scaricati / 1024 / 1024:.1f} MB\n"
            f"Errori: {self.errori_per_tipo}\n"
        )


# Integrazione in Scrapy tramite extension
import scrapy
from scrapy import signals


class MetricheExtension:
    """Extension Scrapy per raccogliere metriche."""

    def __init__(self):
        self.metriche = MetricheScraper()

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(ext.item_dropped, signal=signals.item_dropped)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        return ext

    def item_scraped(self, item, spider):
        self.metriche.item_estratti += 1

    def item_dropped(self, item, response, exception, spider):
        self.metriche.registra_scarto()

    def spider_closed(self, spider):
        logger.info(self.metriche.report())
```

### Alert su Anomalie

```python
import logging

logger = logging.getLogger(__name__)


class AlertMonitor:
    """Monitora le metriche e genera alert quando superano le soglie."""

    def __init__(
        self,
        soglia_errori: float = 0.2,
        soglia_item_vuoti: float = 0.3,
        min_pagine_per_alert: int = 50,
    ):
        self.soglia_errori = soglia_errori
        self.soglia_item_vuoti = soglia_item_vuoti
        self.min_pagine = min_pagine_per_alert

    def controlla(self, metriche: MetricheScraper) -> list[str]:
        alert = []
        totale = metriche.pagine_scaricate + metriche.pagine_fallite

        if totale < self.min_pagine:
            return alert

        # Tasso di errore troppo alto
        if (1 - metriche.tasso_successo) > self.soglia_errori:
            alert.append(
                f"CRITICO: tasso errore "
                f"{1 - metriche.tasso_successo:.1%} "
                f"supera soglia {self.soglia_errori:.1%}"
            )

        # Troppi item vuoti (possibile cambio struttura del sito)
        if metriche.pagine_scaricate > 0:
            rapporto = metriche.item_scartati / metriche.pagine_scaricate
            if rapporto > self.soglia_item_vuoti:
                alert.append(
                    f"ATTENZIONE: {rapporto:.1%} item scartati — "
                    f"possibile cambio struttura del sito target"
                )

        for a in alert:
            logger.warning(a)

        return alert
```

---

## Testing del Codice di Scraping

Il codice di scraping e notoriamente fragile perche dipende dalla struttura di siti esterni. Un buon testing mitiga questa fragilita.

### Fixture HTML per Test Unitari

Salvare copie dell'HTML delle pagine target e usarle come fixture nei test, evitando richieste di rete durante il test.

```python
# tests/conftest.py
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def html_catalogo():
    return (FIXTURES_DIR / "catalogo.html").read_text(encoding="utf-8")


@pytest.fixture
def html_prodotto():
    return (FIXTURES_DIR / "prodotto_dettaglio.html").read_text(encoding="utf-8")
```

```python
# tests/test_parser.py
from parser import Parser  # il modulo del progetto


class TestParser:
    def test_parse_catalogo_estrae_prodotti(self, html_catalogo):
        parser = Parser()
        prodotti = parser.parse_lista_prodotti(
            html_catalogo, base_url="https://esempio.com"
        )
        assert len(prodotti) > 0
        assert all(p.nome for p in prodotti)
        assert all(p.prezzo > 0 for p in prodotti)

    def test_parse_catalogo_vuoto(self):
        parser = Parser()
        prodotti = parser.parse_lista_prodotti(
            "<html><body></body></html>",
            base_url="https://esempio.com",
        )
        assert prodotti == []

    def test_parse_prezzo_formato_europeo(self):
        html = '<span class="prezzo">EUR 1.234,56</span>'
        parser = Parser()
        prezzo = parser._estrai_prezzo(html)
        assert prezzo == 1234.56
```

### Test di Regressione sui Selettori

I selettori CSS/XPath si rompono quando il sito target cambia struttura. Test di regressione periodici rilevano questi cambiamenti.

```python
# tests/test_selettori_regressione.py
import httpx
import pytest
from bs4 import BeautifulSoup


SELETTORI_ATTESI = {
    "https://books.toscrape.com/": {
        ".product_pod": {"min_count": 10, "max_count": 30},
        ".product_pod h3 a": {"min_count": 10},
        ".product_pod .price_color": {"min_count": 10},
    },
}


@pytest.mark.parametrize("url,selettori", SELETTORI_ATTESI.items())
def test_selettori_ancora_validi(url, selettori):
    """Verifica che i selettori producano ancora risultati attesi."""
    response = httpx.get(url, timeout=30)
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, "lxml")

    for selettore, vincoli in selettori.items():
        elementi = soup.select(selettore)
        conteggio = len(elementi)

        if "min_count" in vincoli:
            assert conteggio >= vincoli["min_count"], (
                f"Selettore '{selettore}' ha trovato {conteggio} elementi, "
                f"attesi almeno {vincoli['min_count']}. "
                f"Possibile cambio struttura del sito."
            )
        if "max_count" in vincoli:
            assert conteggio <= vincoli["max_count"]
```

### Mock delle Richieste HTTP

Per i test unitari, usare `respx` (per httpx) o `responses` (per requests) per simulare le risposte HTTP senza effettuare richieste reali.

```python
# tests/test_downloader.py
import respx
import httpx
import pytest
from downloader import Downloader


@respx.mock
def test_downloader_gestisce_404():
    respx.get("https://esempio.com/pagina-mancante").respond(404)

    downloader = Downloader()
    with pytest.raises(httpx.HTTPStatusError):
        downloader.scarica("https://esempio.com/pagina-mancante")


@respx.mock
def test_downloader_retry_su_429():
    # Prima risposta: 429 con Retry-After
    # Seconda risposta: 200
    respx.get("https://esempio.com/pagina").side_effect = [
        httpx.Response(429, headers={"Retry-After": "1"}),
        httpx.Response(200, text="<html>OK</html>"),
    ]

    downloader = Downloader()
    html = downloader.scarica("https://esempio.com/pagina")
    assert "OK" in html
```

### Testing degli Spider Scrapy

Scrapy fornisce utilita per testare gli spider in isolamento usando contratti e il metodo `fake_response_from_file`.

```python
# tests/test_spider.py
import pytest
from scrapy.http import HtmlResponse
from spiders.prodotti_spider import ProdottiSpider


def fake_response(url: str, body: str) -> HtmlResponse:
    """Crea una HtmlResponse fittizia per i test."""
    return HtmlResponse(
        url=url,
        body=body,
        encoding="utf-8",
    )


def test_spider_estrae_prodotti():
    spider = ProdottiSpider()
    html = """
    <div class="scheda-prodotto">
        <h2 class="nome">Prodotto Test</h2>
        <span class="prezzo">29.99</span>
        <a class="dettaglio" href="/prodotto/1">Dettagli</a>
    </div>
    """
    response = fake_response("https://esempio.com/catalogo", html)
    risultati = list(spider.parse(response))

    # Filtrare solo gli item (non le richieste di follow)
    items = [r for r in risultati if isinstance(r, dict)]
    assert len(items) == 1
    assert items[0]["nome"] == "Prodotto Test"


def test_spider_segue_paginazione():
    spider = ProdottiSpider()
    html = """
    <a class="prossima" href="/catalogo?page=2">Prossima</a>
    """
    response = fake_response("https://esempio.com/catalogo", html)
    risultati = list(spider.parse(response))

    # Verificare che venga generata una richiesta per la pagina successiva
    from scrapy.http import Request
    richieste = [r for r in risultati if isinstance(r, Request)]
    assert len(richieste) == 1
    assert "page=2" in richieste[0].url
```

---

## FAQ

### 1. Qual e la differenza tra web scraping e web crawling?

Il **web crawling** e la navigazione sistematica di un sito seguendo i link per scoprire pagine. Il **web scraping** e l'estrazione di dati specifici dalle pagine visitate. Un crawler scopre; uno scraper estrae. In pratica, molti progetti combinano entrambe le attivita.

### 2. Come gestisco i siti che richiedono login?

Usare `requests.Session()` o i browser context di Playwright per persistere i cookie di sessione. Per i siti con login basato su form, eseguire una POST con le credenziali e mantenere la sessione. Per OAuth, utilizzare le API ufficiali se disponibili.

### 3. Quando preferire Scrapy rispetto a requests + BeautifulSoup?

Scrapy e preferibile quando il progetto richiede: crawling di molte pagine (>1000), concorrenza gestita automaticamente, middleware per retry/proxy/throttle, pipeline di export strutturate. Per scraping di poche pagine o prototipi rapidi, requests + BS4 e piu immediato.

### 4. Come gestisco le pagine con scroll infinito?

Usare Playwright con `page.evaluate("window.scrollTo(0, document.body.scrollHeight)")` in un loop che verifica il caricamento di nuovi elementi. In alternativa, intercettare le richieste XHR/Fetch che caricano i dati incrementali e chiamarle direttamente.

### 5. Lo scraping di dati pubblici e legale?

Dipende dalla giurisdizione e dal contesto. In linea generale, i dati pubblicamente accessibili possono essere raccolti, ma i ToS del sito possono vietarlo contrattualmente. La raccolta di dati personali richiede base giuridica sotto GDPR. Consultare sempre un legale per progetti commerciali.

### 6. Come rilevo i cambiamenti nella struttura delle pagine?

Implementare test di regressione sui selettori CSS/XPath. Eseguire periodicamente il parser su pagine campione e confrontare il numero e il tipo di elementi estratti con i valori attesi. Usare alert quando i dati estratti sono vuoti o anomali.

### 7. Come gestisco i contenuti dietro JavaScript pesante?

Tre approcci: (1) Playwright/Selenium per rendering completo; (2) intercettare le API chiamate dal JavaScript e usarle direttamente; (3) cercare versioni pre-rendered (Google Cache, Wayback Machine). L'approccio (2) e il piu efficiente quando possibile.

### 8. httpx async o aiohttp per scraping su larga scala?

Entrambi sono validi. `httpx` offre un'API piu simile a `requests` e supporta HTTP/2. `aiohttp` ha un throughput leggermente superiore per volumi molto alti e un ecosistema piu maturo per connessioni WebSocket. Per la maggior parte dei progetti, `httpx` e la scelta piu ergonomica.

### 9. Come evitare il ban dell'IP?

Rispettare i rate limit, usare ritardi casuali tra le richieste, ruotare gli User-Agent, non effettuare richieste parallele eccessive. Per progetti su larga scala, considerare proxy rotanti. Il modo piu efficace per evitare il ban e ridurre il volume di richieste usando le API ufficiali quando disponibili.

### 10. Come gestisco i contenuti in diverse lingue/localizzazioni?

Impostare l'header `Accept-Language` appropriato. Per i siti che geolocalizzano tramite IP, usare proxy nel paese target. Playwright consente di impostare `locale` e `timezone_id` per ciascun contesto.

---

## Esercizi

### Esercizio 1 — Scraper con robots.txt (Fondamentale)

Scrivere uno scraper che prima di accedere a qualsiasi URL verifichi il `robots.txt` del sito. Deve rispettare il `Crawl-delay`, registrare in un log gli URL bloccati e procedere solo con quelli consentiti. Testare su almeno 3 siti con `robots.txt` diversi.

### Esercizio 2 — Pipeline completa con Scrapy

Creare un progetto Scrapy che estragga prodotti da un sito e-commerce (o sito di test come `books.toscrape.com`). Implementare: Item con validazione, Pipeline che salva in SQLite, middleware per retry con backoff, rispetto del `robots.txt`, export in JSON e CSV.

### Esercizio 3 — Scraping asincrono con aiohttp

Scrivere uno scraper asincrono che scarichi 100 pagine da un sito con concorrenza limitata a 5 richieste simultanee. Implementare: ritardi casuali, gestione del 429, logging delle performance (tempo totale, media per pagina, errori).

### Esercizio 4 — Estrazione dati strutturati

Scrivere un modulo che, data una pagina HTML, estragga automaticamente JSON-LD, Open Graph e microdata. Testare su almeno 5 siti diversi (e-commerce, news, ricette). Confrontare la completezza dei dati strutturati rispetto al parsing del DOM.

### Esercizio 5 — Confronto Playwright vs Selenium

Implementare lo stesso scraper (login + navigazione + estrazione) sia con Playwright sia con Selenium. Misurare: tempo di esecuzione, linee di codice, gestione degli errori, facilita di debugging. Documentare i risultati in una tabella comparativa.

### Esercizio 6 — Anti-detection e fingerprinting

Usare Playwright per accedere a `bot.sannysoft.com` e verificare quanti test di rilevamento vengono superati. Implementare le contromisure (rimozione `navigator.webdriver`, viewport realistico, user-agent coerente) e confrontare il punteggio prima e dopo.

### Esercizio 7 — Monitoraggio prezzi con alert

Creare un sistema che monitora i prezzi di 10 prodotti da un sito e-commerce, salva lo storico in SQLite, e invia un alert (email o file) quando un prezzo scende sotto una soglia configurabile. Schedulare l'esecuzione ogni ora con APScheduler.

### Esercizio 8 — Scraper resiliente con data pipeline

Progettare e implementare una pipeline completa: Downloader con cache → Parser con validazione → Storage (SQLite + export JSON). Implementare dry-run, logging strutturato, metriche (pagine/secondo, tasso errore) e report finale.

---

## Letture

- Documentazione ufficiale Requests. https://docs.python-requests.org/en/latest/
- Documentazione BeautifulSoup 4. https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- Documentazione Playwright per Python. https://playwright.dev/python/
- Documentazione Scrapy. https://docs.scrapy.org/en/latest/
- Documentazione Selenium per Python. https://www.selenium.dev/documentation/webdriver/
- Documentazione httpx. https://www.python-httpx.org/
- Documentazione aiohttp. https://docs.aiohttp.org/en/stable/
- Documentazione lxml. https://lxml.de/
- RFC 9309 — Robots Exclusion Protocol. https://www.rfc-editor.org/rfc/rfc9309
- Schema.org — Vocabolario dati strutturati. https://schema.org/
- OWASP Web Scraping Guidelines. https://owasp.org/www-community/controls/Web_Scraping
- GDPR — Regolamento UE 2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj
- Real Python — Web Scraping Tutorial. https://realpython.com/python-web-scraping-practical-introduction/
- Documentazione scrapy-redis. https://github.com/rmax/scrapy-redis
- Documentazione scrapy-playwright. https://github.com/scrapy-plugins/scrapy-playwright
- Documentazione playwright-stealth. https://pypi.org/project/playwright-stealth/
- Documentazione curl_cffi. https://curl-cffi.readthedocs.io/
- Documentazione fingerprint-suite. https://github.com/nicedash/fingerprint-suite
- Documentazione respx (mock per httpx). https://lundberg.github.io/respx/

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **aiohttp** | Libreria HTTP asincrona per Python basata su asyncio, ideale per scraping ad alto throughput. |
| **BeautifulSoup** | Libreria per il parsing di HTML e XML che fornisce un'API Pythonica per navigare e cercare nell'albero del documento. |
| **Browser context** | Ambiente di navigazione isolato in Playwright con cookie, storage e sessione indipendenti. |
| **CDP** | Chrome DevTools Protocol — protocollo di comunicazione diretta con il browser Chromium usato da Playwright. |
| **CAPTCHA** | Completely Automated Public Turing test to tell Computers and Humans Apart — meccanismo di verifica anti-bot. |
| **CrawlSpider** | Spider Scrapy che segue automaticamente i link secondo regole configurabili (LinkExtractor + Rule). |
| **CSS selector** | Sintassi per selezionare elementi HTML basata sulle regole CSS (es. `div.classe > h2::text`). |
| **Data pipeline** | Catena di trasformazioni che porta i dati grezzi dal download alla persistenza strutturata. |
| **Headless browser** | Browser eseguito senza interfaccia grafica, controllato programmaticamente per rendering di pagine JavaScript. |
| **httpx** | Client HTTP moderno per Python con supporto sincrono e asincrono, HTTP/2 e API simile a requests. |
| **JSON-LD** | JSON for Linking Data — formato per incorporare dati strutturati nelle pagine HTML tramite `<script type="application/ld+json">`. |
| **lxml** | Parser XML/HTML ad alte prestazioni basato su libxml2, usato come backend veloce per BeautifulSoup. |
| **Microdata** | Specifica W3C per annotare elementi HTML con attributi `itemscope`, `itemtype` e `itemprop`. |
| **Open Graph** | Protocollo di metadati (tag `<meta property="og:*">`) usato da Facebook per la preview dei link condivisi. |
| **Playwright** | Framework di automazione browser di Microsoft con auto-waiting, contesti isolati e supporto multi-browser. |
| **Rate limiting** | Tecnica per limitare la frequenza delle richieste a un server, sia come difesa (lato server) sia come buona pratica (lato client). |
| **robots.txt** | File di testo nella root di un sito che dichiara le regole di accesso per i bot, secondo RFC 9309. |
| **Scrapy** | Framework Python completo per web crawling e scraping su larga scala con middleware, pipeline e scheduling integrati. |
| **Selenium** | Framework di automazione browser basato sul protocollo W3C WebDriver, con supporto per tutti i browser principali. |
| **Selector** | Espressione (CSS o XPath) che identifica uno o piu elementi nel DOM di una pagina HTML. |
| **Sitemap** | File XML che elenca gli URL di un sito con metadati (frequenza di aggiornamento, priorita) per facilitare il crawling. |
| **Throttling** | Rallentamento deliberato della frequenza delle richieste per rispettare i limiti del server e ridurre il rischio di ban. |
| **User-Agent** | Header HTTP che identifica il client che effettua la richiesta. I bot dovrebbero identificarsi con un User-Agent descrittivo. |
| **XPath** | Linguaggio per navigare e selezionare nodi in documenti XML/HTML, piu espressivo dei CSS selector per query complesse. |
| **curl_cffi** | Client HTTP Python che emula il fingerprint TLS di browser reali (JA3/JA4), eludendo il rilevamento basato sulla negoziazione TLS. |
| **fingerprint-suite** | Libreria che genera fingerprint browser statisticamente realistici tramite rete bayesiana addestrata su traffico reale. |
| **JA3/JA4** | Metodo di fingerprinting TLS basato sull'hash dei parametri della negoziazione client hello (cipher, estensioni, curve). |
| **playwright-stealth** | Pacchetto Python che applica patch a Playwright per nascondere i segnali di automazione (navigator.webdriver, plugin, codec). |
| **Scrapy-Redis** | Estensione di Scrapy che sostituisce lo scheduler in-memory con una coda Redis per il crawling distribuito su piu macchine. |
| **scrapy-playwright** | Download handler che integra Playwright in Scrapy per il rendering JavaScript mantenendo pipeline e middleware. |
| **Sticky session** | Tecnica di rotazione proxy che assegna lo stesso proxy a uno specifico dominio per tutta la sessione di scraping. |

---

> **Moduli correlati**: [16-automazione.md](16-automazione.md) (scheduling e pipeline), [17-network-programming.md](17-network-programming.md) (HTTP client, socket), [10-programmazione-asincrona.md](10-programmazione-asincrona.md) (asyncio per scraping concorrente), [18-sicurezza.md](18-sicurezza.md) (GDPR, gestione credenziali), [14-data-processing.md](14-data-processing.md) (elaborazione dati estratti).
