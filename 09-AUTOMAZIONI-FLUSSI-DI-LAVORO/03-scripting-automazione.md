---
corso: "Automazioni e Flussi di Lavoro"
fase: "2 — Scripting e Integrazione"
modulo: 3
titolo: "Scripting e Programmazione per l'Automazione"
versione: "1.0"
livello: "Intermedio"
prerequisiti:
  - "Modulo 01 — Fondamenti dell'Automazione"
  - "Bash basics, Python intermedio, CLI Linux/Windows"
obiettivi:
  - "Scegliere il linguaggio adatto (Bash, Python, PowerShell) in base alla complessità del task"
  - "Gestire variabili d'ambiente, secrets e logging in modo sicuro negli script"
  - "Applicare pattern CLI robusti con argparse/click e validazione degli input"
  - "Scrivere script testabili con separazione logica, funzioni pure e mocking"
  - "Implementare fail-fast con set -euo pipefail in Bash e equivalenti in Python"
tag: [scripting, bash, python, powershell, cli, automazione, secrets]
---

# Scripting e Programmazione per l'Automazione — Guida Completa

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 1 — Fondamenti · Modulo 03
> **Prerequisiti:** Bash basics, Python intermedio, fluency CLI Linux/Windows.
> **Obiettivi:** scegliere fra Bash, Python, PowerShell; gestire env, secrets, logging; applicare patterns CLI argparse/click; testabilita.
> **Tempo:** lettura 90-120 min · lab 180-240 min
> **Livello:** competent (Dreyfus 3)
> **Ultimo aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Scegliere il linguaggio adatto (Bash, Python, PowerShell) in base alla complessità del task
> 2. Gestire variabili d'ambiente, secrets e logging in modo sicuro negli script
> 3. Applicare pattern CLI robusti con argparse/click e validazione degli input
> 4. Scrivere script testabili con separazione logica, funzioni pure e mocking
> 5. Implementare fail-fast con `set -euo pipefail` in Bash e equivalenti in Python
>
> **Prerequisiti:** [Modulo 01](01-fondamenti-automazione.md) -- Bash basics, Python intermedio, CLI Linux/Windows
> **Tempo stimato:** 4-6 ore · **Livello:** Intermedio

## Idee guida

1. **Bash per <50 righe, Python sopra.** Bash trionfa per pipeline di file. Python vince in tutto il resto.
2. **Mai hardcode credentials in script.** Env vars, secret manager, vault. `.env` solo in dev con `.gitignore`.
3. **`set -euo pipefail` in ogni script Bash.** Il default di Bash e silently-fail; questi flag rendono fail-fast.
4. **Logging strutturato JSON > print debug.** `logging` Python con formatter JSON, parsabile da SIEM.
5. **Test scripts: even 3 unit test cattura il 80% dei bug di regressione.** Mai "ho testato manuale, ok".

---

## Indice

1. [Panoramica](#panoramica)
2. [Python per l'Automazione](#python-per-lautomazione)
   - [Panoramica e Setup](#panoramica-e-setup)
   - [requests — Interazione con API](#requests--interazione-con-api)
   - [selenium — Automazione Web](#selenium--automazione-web)
   - [playwright — Automazione Web Moderna](#playwright--automazione-web-moderna)
   - [watchdog — Monitoraggio File System](#watchdog--monitoraggio-file-system)
   - [schedule e APScheduler](#schedule-e-apscheduler)
   - [Librerie Utili Aggiuntive](#librerie-utili-aggiuntive)
3. [Bash Scripting per Automazione](#bash-scripting-per-automazione)
4. [PowerShell per Automazione](#powershell-per-automazione)
5. [Ansible — Configuration Management e Automazione](#ansible--configuration-management-e-automazione)
   - [Architettura](#architettura)
   - [Componenti Fondamentali](#componenti-fondamentali)
   - [Playbook Pratici](#playbook-pratici)
   - [Ansible Avanzato](#ansible-avanzato)
6. [Best Practices](#best-practices)

---

## Panoramica

L'automazione tramite scripting rappresenta il cuore dell'efficienza operativa in ambito IT. Mentre le piattaforme low-code offrono accessibilita e rapidita di implementazione, la programmazione tradizionale garantisce un controllo granulare, flessibilita illimitata e la capacita di affrontare scenari complessi che nessuna interfaccia grafica potrebbe gestire adeguatamente.

L'approccio allo scripting per l'automazione si articola su diversi livelli di complessita e ambito di applicazione. Al livello piu basilare troviamo gli **script shell** (Bash su sistemi Unix/Linux, PowerShell su Windows), ideali per operazioni di sistema, gestione di file e orchestrazione di comandi. A un livello intermedio, **Python** si impone come linguaggio di riferimento per la sua versatilita, l'ecosistema sterminato di librerie e la leggibilita del codice. Per l'automazione infrastrutturale su larga scala, strumenti come **Ansible** forniscono un framework dichiarativo che astrae la complessita della gestione di flotte di server.

La scelta dello strumento dipende da molteplici fattori: la complessita del task, l'ambiente di esecuzione, le competenze del team, la necessita di manutenzione a lungo termine e l'integrazione con sistemi esistenti. In molti scenari reali, la soluzione ottimale combina piu strumenti: uno script Python che richiama comandi Bash, orchestrato da Ansible e schedulato tramite cron o un task scheduler. Questa guida esplora ciascuno di questi strumenti in profondita, fornendo esempi pratici e pattern consolidati.

---

## Python per l'Automazione

### Panoramica e Setup

Python e il linguaggio di programmazione piu utilizzato per l'automazione IT, e le ragioni sono molteplici. La sintassi leggibile e concisa riduce il tempo di sviluppo e facilita la manutenzione. L'ecosistema di pacchetti su PyPI conta oltre 400.000 librerie, coprendo praticamente ogni necessita. La comunita attiva garantisce documentazione abbondante e supporto. Inoltre, Python e preinstallato sulla maggior parte delle distribuzioni Linux ed e facilmente installabile su ogni piattaforma.

**Setup dell'ambiente di sviluppo:**

```bash
# Installazione Python (se non presente)
sudo apt update && sudo apt install python3 python3-pip python3-venv

# Creazione di un ambiente virtuale (fondamentale per isolamento dipendenze)
python3 -m venv ~/automazione-env
source ~/automazione-env/bin/activate

# Verifica
python --version
pip --version
```

**Struttura consigliata di un progetto di automazione:**

```
progetto-automazione/
├── README.md
├── requirements.txt
├── setup.py
├── config/
│   ├── settings.yaml
│   └── credentials.yaml.example
├── src/
│   ├── __init__.py
│   ├── api_client.py
│   ├── file_processor.py
│   └── notifier.py
├── scripts/
│   ├── daily_report.py
│   └── sync_data.py
├── tests/
│   ├── __init__.py
│   ├── test_api_client.py
│   └── test_file_processor.py
└── logs/
    └── .gitkeep
```

**Gestione delle dipendenze con `requirements.txt`:**

```txt
requests>=2.31.0
selenium>=4.15.0
playwright>=1.40.0
watchdog>=3.0.0
schedule>=1.2.0
APScheduler>=3.10.0
paramiko>=3.3.0
openpyxl>=3.1.0
pandas>=2.1.0
jinja2>=3.1.0
pyyaml>=6.0.0
python-dotenv>=1.0.0
```

L'utilizzo di ambienti virtuali (`venv`) e assolutamente imprescindibile. Ogni progetto di automazione deve avere il proprio ambiente isolato per evitare conflitti tra dipendenze e garantire la riproducibilita. Il file `requirements.txt` consente a qualsiasi membro del team di ricreare l'ambiente identico con un semplice `pip install -r requirements.txt`.

---

### requests — Interazione con API

La libreria `requests` e lo standard de facto per le interazioni HTTP in Python. Offre un'interfaccia elegante e intuitiva per comunicare con API REST, scaricare file, inviare dati e gestire autenticazione.

**Operazioni CRUD fondamentali:**

```python
import requests

BASE_URL = "https://api.esempio.com/v1"

# GET — Recupero risorse
response = requests.get(f"{BASE_URL}/utenti", params={"page": 1, "limit": 50})
if response.status_code == 200:
    utenti = response.json()
    for utente in utenti["data"]:
        print(f"{utente['nome']} - {utente['email']}")

# POST — Creazione risorse
nuovo_utente = {"nome": "Marco Rossi", "email": "marco@esempio.com", "ruolo": "admin"}
response = requests.post(f"{BASE_URL}/utenti", json=nuovo_utente)
if response.status_code == 201:
    print(f"Utente creato con ID: {response.json()['id']}")

# PUT — Aggiornamento completo
aggiornamento = {"nome": "Marco Rossi", "email": "marco.rossi@esempio.com", "ruolo": "superadmin"}
response = requests.put(f"{BASE_URL}/utenti/42", json=aggiornamento)

# DELETE — Eliminazione
response = requests.delete(f"{BASE_URL}/utenti/42")
if response.status_code == 204:
    print("Utente eliminato con successo")
```

**Autenticazione — API Key, Bearer Token e OAuth:**

```python
import requests
from requests.auth import HTTPBasicAuth

# Autenticazione tramite API Key nell'header
headers_apikey = {
    "X-API-Key": "la-tua-api-key-segreta",
    "Content-Type": "application/json"
}
response = requests.get(f"{BASE_URL}/dati", headers=headers_apikey)

# Autenticazione Bearer Token (JWT)
token = "eyJhbGciOiJIUzI1NiIs..."
headers_bearer = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
response = requests.get(f"{BASE_URL}/profilo", headers=headers_bearer)

# Basic Auth
response = requests.get(
    f"{BASE_URL}/risorse",
    auth=HTTPBasicAuth("utente", "password")
)

# OAuth 2.0 — Flusso Client Credentials
def ottieni_token_oauth(client_id, client_secret, token_url):
    """Ottiene un access token tramite OAuth 2.0 Client Credentials."""
    response = requests.post(token_url, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "read write"
    })
    response.raise_for_status()
    return response.json()["access_token"]
```

**Gestione delle sessioni, errori e retry:**

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def crea_sessione_resiliente(max_retries=3, backoff_factor=0.5):
    """Crea una sessione HTTP con retry automatico e backoff esponenziale."""
    sessione = requests.Session()

    strategia_retry = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "DELETE"]
    )

    adapter = HTTPAdapter(max_retries=strategia_retry)
    sessione.mount("https://", adapter)
    sessione.mount("http://", adapter)

    # Header comuni per tutte le richieste della sessione
    sessione.headers.update({
        "Content-Type": "application/json",
        "User-Agent": "AutomazioneScript/1.0"
    })

    return sessione

# Utilizzo
sessione = crea_sessione_resiliente()
try:
    response = sessione.get(f"{BASE_URL}/dati", timeout=30)
    response.raise_for_status()
    dati = response.json()
except requests.exceptions.Timeout:
    logger.error("Timeout nella richiesta: il server non ha risposto in tempo")
except requests.exceptions.HTTPError as e:
    logger.error(f"Errore HTTP {e.response.status_code}: {e.response.text}")
except requests.exceptions.ConnectionError:
    logger.error("Impossibile connettersi al server")
except requests.exceptions.RequestException as e:
    logger.error(f"Errore generico nella richiesta: {e}")
```

**Gestione della paginazione:**

```python
def recupera_tutti_i_risultati(sessione, url, params=None):
    """Recupera tutti i risultati da un'API paginata."""
    if params is None:
        params = {}

    tutti_i_risultati = []
    pagina = 1

    while True:
        params["page"] = pagina
        params["per_page"] = 100

        response = sessione.get(url, params=params, timeout=30)
        response.raise_for_status()
        dati = response.json()

        risultati = dati.get("items", [])
        if not risultati:
            break

        tutti_i_risultati.extend(risultati)
        logger.info(f"Pagina {pagina}: recuperati {len(risultati)} elementi")

        # Controllo se ci sono altre pagine
        if pagina >= dati.get("total_pages", 1):
            break
        pagina += 1

    logger.info(f"Totale elementi recuperati: {len(tutti_i_risultati)}")
    return tutti_i_risultati
```

**Esempio completo — Interazione con GitHub API:**

```python
import requests
import os
from datetime import datetime

class GitHubClient:
    """Client per interagire con l'API di GitHub."""

    def __init__(self, token):
        self.sessione = requests.Session()
        self.sessione.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        })
        self.base_url = "https://api.github.com"

    def lista_repository(self, org):
        """Recupera tutti i repository di un'organizzazione."""
        return recupera_tutti_i_risultati(
            self.sessione,
            f"{self.base_url}/orgs/{org}/repos"
        )

    def crea_issue(self, owner, repo, titolo, corpo, etichette=None):
        """Crea una nuova issue in un repository."""
        payload = {"title": titolo, "body": corpo}
        if etichette:
            payload["labels"] = etichette

        response = self.sessione.post(
            f"{self.base_url}/repos/{owner}/{repo}/issues",
            json=payload
        )
        response.raise_for_status()
        issue = response.json()
        print(f"Issue #{issue['number']} creata: {issue['html_url']}")
        return issue

    def report_attivita(self, owner, repo, giorni=7):
        """Genera un report delle attivita recenti di un repository."""
        from datetime import timedelta
        data_inizio = (datetime.now() - timedelta(days=giorni)).isoformat()

        # Commit recenti
        commits = self.sessione.get(
            f"{self.base_url}/repos/{owner}/{repo}/commits",
            params={"since": data_inizio}
        ).json()

        # Issue recenti
        issues = self.sessione.get(
            f"{self.base_url}/repos/{owner}/{repo}/issues",
            params={"since": data_inizio, "state": "all"}
        ).json()

        print(f"Report attivita per {owner}/{repo} (ultimi {giorni} giorni)")
        print(f"  Commit: {len(commits)}")
        print(f"  Issue: {len(issues)}")
        return {"commits": commits, "issues": issues}

# Utilizzo
client = GitHubClient(os.environ["GITHUB_TOKEN"])
client.report_attivita("mia-org", "mio-repo", giorni=14)
```

---

### selenium — Automazione Web

Selenium e la libreria storica per l'automazione del browser. Consente di controllare programmaticamente un browser reale (Chrome, Firefox, Edge) per simulare interazioni utente, eseguire test end-to-end e automatizzare operazioni su applicazioni web.

**Setup e configurazione iniziale:**

```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def crea_driver(headless=True):
    """Crea e configura un'istanza di Chrome WebDriver."""
    opzioni = Options()
    if headless:
        opzioni.add_argument("--headless=new")
    opzioni.add_argument("--no-sandbox")
    opzioni.add_argument("--disable-dev-shm-usage")
    opzioni.add_argument("--window-size=1920,1080")
    opzioni.add_argument("--disable-gpu")

    # Il driver viene scaricato automaticamente da Selenium 4.6+
    driver = webdriver.Chrome(options=opzioni)
    driver.implicitly_wait(10)  # Wait implicito globale
    return driver
```

**Strategie di localizzazione degli elementi:**

```python
driver = crea_driver()
driver.get("https://esempio.com/login")

# Per ID
campo_email = driver.find_element(By.ID, "email")

# Per Name
campo_password = driver.find_element(By.NAME, "password")

# Per CSS Selector (molto versatile)
pulsante_login = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

# Per XPath (per strutture complesse)
messaggio = driver.find_element(By.XPATH, "//div[@class='alert']//span[contains(text(), 'Errore')]")

# Per Class Name
elementi_menu = driver.find_elements(By.CLASS_NAME, "menu-item")

# Per Link Text
link_registrazione = driver.find_element(By.LINK_TEXT, "Registrati ora")
```

**Gestione delle attese (waits):**

```python
# Wait esplicito — attende una condizione specifica
wait = WebDriverWait(driver, timeout=20)

# Attende che l'elemento sia visibile
elemento = wait.until(
    EC.visibility_of_element_located((By.ID, "risultati"))
)

# Attende che l'elemento sia cliccabile
pulsante = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-conferma"))
)

# Attende che il testo sia presente
wait.until(
    EC.text_to_be_present_in_element((By.ID, "stato"), "Completato")
)

# Attende la scomparsa di un loader
wait.until(
    EC.invisibility_of_element_located((By.CLASS_NAME, "spinner"))
)
```

**Pattern Page Object Model (POM):**

```python
class PaginaLogin:
    """Page Object per la pagina di login."""

    URL = "https://app.esempio.com/login"

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)

    def naviga(self):
        self.driver.get(self.URL)
        return self

    def inserisci_email(self, email):
        campo = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
        campo.clear()
        campo.send_keys(email)
        return self

    def inserisci_password(self, password):
        campo = self.driver.find_element(By.ID, "password")
        campo.clear()
        campo.send_keys(password)
        return self

    def clicca_accedi(self):
        pulsante = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        pulsante.click()
        return PaginaDashboard(self.driver)

    def login(self, email, password):
        """Metodo di convenienza per il login completo."""
        self.naviga()
        self.inserisci_email(email)
        self.inserisci_password(password)
        return self.clicca_accedi()


class PaginaDashboard:
    """Page Object per la dashboard."""

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)

    def ottieni_nome_utente(self):
        elemento = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".user-name"))
        )
        return elemento.text

    def vai_a_impostazioni(self):
        link = self.driver.find_element(By.LINK_TEXT, "Impostazioni")
        link.click()
        return self

# Utilizzo
driver = crea_driver(headless=False)
try:
    login_page = PaginaLogin(driver)
    dashboard = login_page.login("admin@esempio.com", "password123")
    print(f"Benvenuto, {dashboard.ottieni_nome_utente()}")
finally:
    driver.quit()
```

---

### playwright — Automazione Web Moderna

Playwright, sviluppato da Microsoft, rappresenta l'evoluzione moderna dell'automazione browser. Supera molti limiti di Selenium offrendo auto-waiting integrato, supporto multi-browser nativo (Chromium, Firefox, WebKit), intercettazione di rete e strumenti di generazione codice.

**Perche Playwright rispetto a Selenium:** Playwright non richiede wait espliciti nella maggior parte dei casi grazie al meccanismo di auto-waiting. Ogni azione attende automaticamente che l'elemento sia visibile, stabile e pronto per l'interazione. Inoltre, Playwright offre prestazioni superiori, supporto nativo per contesti multipli (utile per test paralleli) e un'API piu moderna e coerente.

**Setup e utilizzo base:**

```python
from playwright.sync_api import sync_playwright
import os

def automazione_con_playwright():
    with sync_playwright() as p:
        # Lancio del browser (chromium, firefox o webkit)
        browser = p.chromium.launch(headless=True)
        contesto = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="it-IT"
        )
        pagina = contesto.new_page()

        # Navigazione — Playwright attende automaticamente il caricamento
        pagina.goto("https://app.esempio.com")

        # Interazione — auto-waiting integrato
        pagina.fill("#email", "utente@esempio.com")
        pagina.fill("#password", "password-sicura")
        pagina.click("button[type='submit']")

        # Attesa di navigazione implicita dopo il click
        pagina.wait_for_url("**/dashboard")

        # Estrazione dati
        titolo = pagina.text_content("h1.page-title")
        print(f"Pagina corrente: {titolo}")

        # Interazione con liste e tabelle
        righe = pagina.query_selector_all("table.dati tbody tr")
        for riga in righe:
            celle = riga.query_selector_all("td")
            valori = [cella.text_content() for cella in celle]
            print(valori)

        browser.close()
```

**Intercettazione di rete:**

```python
def intercetta_api():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pagina = browser.new_page()

        risposte_api = []

        # Intercetta tutte le risposte API
        def gestisci_risposta(response):
            if "/api/" in response.url:
                risposte_api.append({
                    "url": response.url,
                    "status": response.status,
                    "body": response.json() if "json" in response.headers.get("content-type", "") else None
                })

        pagina.on("response", gestisci_risposta)
        pagina.goto("https://app.esempio.com/dashboard")
        pagina.wait_for_load_state("networkidle")

        for r in risposte_api:
            print(f"[{r['status']}] {r['url']}")

        browser.close()
```

**Screenshot e generazione PDF:**

```python
def cattura_screenshot_e_pdf():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pagina = browser.new_page()
        pagina.goto("https://report.esempio.com/mensile")
        pagina.wait_for_load_state("networkidle")

        # Screenshot completo della pagina
        pagina.screenshot(path="report_screenshot.png", full_page=True)

        # Generazione PDF (solo Chromium)
        pagina.pdf(
            path="report_mensile.pdf",
            format="A4",
            margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"},
            print_background=True
        )

        browser.close()
```

**Codegen — Registrazione automatica delle azioni:**

```bash
# Avvia il code generator interattivo
playwright codegen https://app.esempio.com

# Con opzioni aggiuntive
playwright codegen --target python --output script_registrato.py https://app.esempio.com
```

Il codegen di Playwright e uno strumento straordinariamente utile per la prototipazione rapida: registra ogni click, digitazione e navigazione e genera codice Python equivalente. Lo script generato va poi rifattorizzato applicando pattern come il Page Object Model, ma offre un punto di partenza immediato.

---

### watchdog — Monitoraggio File System

La libreria `watchdog` consente di monitorare il file system in tempo reale, reagendo a eventi come creazione, modifica, cancellazione e spostamento di file e directory. Questo la rende ideale per pipeline di elaborazione automatica, backup incrementali e sincronizzazione.

**FileSystemEventHandler e Observer:**

```python
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


class GestoreElaborazioneFile(FileSystemEventHandler):
    """Gestisce i file in arrivo nella directory monitorata."""

    def __init__(self, estensioni_valide=None):
        self.estensioni_valide = estensioni_valide or [".csv", ".xlsx", ".json"]

    def on_created(self, event):
        if event.is_directory:
            return
        if any(event.src_path.endswith(ext) for ext in self.estensioni_valide):
            logger.info(f"Nuovo file rilevato: {event.src_path}")
            self._elabora_file(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        logger.info(f"File modificato: {event.src_path}")

    def on_deleted(self, event):
        logger.info(f"File eliminato: {event.src_path}")

    def on_moved(self, event):
        logger.info(f"File spostato: {event.src_path} -> {event.dest_path}")

    def _elabora_file(self, percorso):
        """Logica di elaborazione personalizzata."""
        try:
            if percorso.endswith(".csv"):
                self._elabora_csv(percorso)
            elif percorso.endswith(".xlsx"):
                self._elabora_excel(percorso)
            elif percorso.endswith(".json"):
                self._elabora_json(percorso)
            logger.info(f"Elaborazione completata: {percorso}")
        except Exception as e:
            logger.error(f"Errore elaborazione {percorso}: {e}")

    def _elabora_csv(self, percorso):
        import pandas as pd
        df = pd.read_csv(percorso)
        logger.info(f"CSV caricato: {len(df)} righe, {len(df.columns)} colonne")
        # ... logica di trasformazione ...

    def _elabora_excel(self, percorso):
        import openpyxl
        wb = openpyxl.load_workbook(percorso)
        logger.info(f"Excel caricato: fogli = {wb.sheetnames}")

    def _elabora_json(self, percorso):
        import json
        with open(percorso) as f:
            dati = json.load(f)
        logger.info(f"JSON caricato: {len(dati)} elementi di primo livello")


def avvia_monitoraggio(directory, ricorsivo=True):
    """Avvia il monitoraggio di una directory."""
    gestore = GestoreElaborazioneFile(estensioni_valide=[".csv", ".xlsx", ".json", ".xml"])
    observer = Observer()
    observer.schedule(gestore, directory, recursive=ricorsivo)
    observer.start()

    logger.info(f"Monitoraggio avviato su: {directory}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Monitoraggio interrotto")
    observer.join()

# Avvio
avvia_monitoraggio("/percorso/directory/input")
```

---

### schedule e APScheduler

La schedulazione e fondamentale per l'automazione: report periodici, sincronizzazioni, backup, invio notifiche. Python offre due librerie principali con diversi livelli di sofisticazione.

**`schedule` — Schedulazione semplice ed elegante:**

```python
import schedule
import time
import logging

logger = logging.getLogger(__name__)

def genera_report_giornaliero():
    logger.info("Generazione report giornaliero in corso...")
    # ... logica di generazione report ...

def sincronizza_dati():
    logger.info("Sincronizzazione dati con sistema esterno...")
    # ... logica di sincronizzazione ...

def controllo_salute_servizi():
    logger.info("Verifica stato dei servizi...")
    # ... health check ...

# Definizione della schedulazione
schedule.every().day.at("08:00").do(genera_report_giornaliero)
schedule.every(30).minutes.do(sincronizza_dati)
schedule.every(5).minutes.do(controllo_salute_servizi)
schedule.every().monday.at("09:00").do(lambda: print("Inizio settimana lavorativa"))

# Loop principale
while True:
    schedule.run_pending()
    time.sleep(1)
```

**`APScheduler` — Schedulazione avanzata con persistenza:**

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import logging

logging.basicConfig(level=logging.INFO)

# Configurazione con persistenza dei job su database
configurazione_jobstore = {
    "default": SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")
}

scheduler = BackgroundScheduler(jobstores=configurazione_jobstore)

def backup_database():
    """Esegue il backup del database."""
    print("Backup database in esecuzione...")

def pulizia_file_temporanei():
    """Rimuove i file temporanei piu vecchi di 7 giorni."""
    print("Pulizia file temporanei...")

def invio_report_settimanale():
    """Genera e invia il report settimanale."""
    print("Invio report settimanale...")

# Job con espressione cron-like
scheduler.add_job(
    backup_database,
    CronTrigger(hour=2, minute=0),  # Ogni giorno alle 02:00
    id="backup_db",
    name="Backup Database Giornaliero",
    replace_existing=True
)

# Job a intervallo regolare
scheduler.add_job(
    pulizia_file_temporanei,
    IntervalTrigger(hours=6),
    id="pulizia_temp",
    name="Pulizia File Temporanei"
)

# Job settimanale con espressione cron completa
scheduler.add_job(
    invio_report_settimanale,
    CronTrigger(day_of_week="fri", hour=17, minute=30),
    id="report_settimana",
    name="Report Settimanale Venerdi"
)

scheduler.start()

# Mantenere il programma in esecuzione
import time
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    scheduler.shutdown()
```

APScheduler offre vantaggi significativi rispetto a `schedule`: la persistenza dei job (sopravvivono ai riavvii dell'applicazione), trigger sofisticati (cron, intervalli, date specifiche), esecuzione in thread o processi separati e integrazione con framework web come Flask e Django.

---

### Librerie Utili Aggiuntive

**`paramiko` e `fabric` — Esecuzione remota via SSH:**

```python
import paramiko

def esegui_comando_remoto(host, utente, chiave_privata, comando):
    """Esegue un comando su un server remoto via SSH."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(host, username=utente, key_filename=chiave_privata)
        stdin, stdout, stderr = client.exec_command(comando)

        output = stdout.read().decode()
        errori = stderr.read().decode()
        codice_uscita = stdout.channel.recv_exit_status()

        return {"output": output, "errori": errori, "codice": codice_uscita}
    finally:
        client.close()

# Utilizzo
risultato = esegui_comando_remoto(
    host="server-produzione.esempio.com",
    utente="deploy",
    chiave_privata="/home/utente/.ssh/id_rsa",
    comando="systemctl status nginx"
)
print(risultato["output"])
```

**`openpyxl` e `pandas` — Elaborazione Excel e CSV:**

```python
import pandas as pd
import openpyxl

# Lettura e trasformazione dati CSV
df = pd.read_csv("vendite_raw.csv")
df["data"] = pd.to_datetime(df["data"])
df["mese"] = df["data"].dt.month
riepilogo = df.groupby("mese").agg({"importo": ["sum", "mean", "count"]})
riepilogo.to_excel("riepilogo_vendite.xlsx", sheet_name="Mensile")

# Creazione report Excel formattato con openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Report Mensile"

# Intestazione con stile
intestazione = ["Mese", "Totale Vendite", "Media", "Numero Transazioni"]
stile_header = Font(bold=True, color="FFFFFF", size=12)
sfondo_header = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")

for col, testo in enumerate(intestazione, 1):
    cella = ws.cell(row=1, column=col, value=testo)
    cella.font = stile_header
    cella.fill = sfondo_header
    cella.alignment = Alignment(horizontal="center")

wb.save("report_formattato.xlsx")
```

**`jinja2` — Rendering di template:**

```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("report_email.html")

contenuto = template.render(
    titolo="Report Settimanale",
    data_generazione="2026-03-27",
    metriche=[
        {"nome": "Uptime", "valore": "99.97%", "stato": "ok"},
        {"nome": "Tempo Risposta", "valore": "142ms", "stato": "ok"},
        {"nome": "Errori 5xx", "valore": "23", "stato": "attenzione"},
    ]
)
```

**`smtplib` — Invio email automatizzate:**

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def invia_email(destinatario, oggetto, corpo_html, allegati=None):
    """Invia un'email con possibili allegati."""
    msg = MIMEMultipart()
    msg["From"] = "automazione@esempio.com"
    msg["To"] = destinatario
    msg["Subject"] = oggetto

    msg.attach(MIMEText(corpo_html, "html"))

    if allegati:
        for percorso_file in allegati:
            with open(percorso_file, "rb") as f:
                parte = MIMEBase("application", "octet-stream")
                parte.set_payload(f.read())
            encoders.encode_base64(parte)
            nome_file = percorso_file.split("/")[-1]
            parte.add_header("Content-Disposition", f"attachment; filename={nome_file}")
            msg.attach(parte)

    with smtplib.SMTP("smtp.esempio.com", 587) as server:
        server.starttls()
        server.login("automazione@esempio.com", "password-app")
        server.send_message(msg)
```

**`subprocess` — Esecuzione comandi di sistema:**

```python
import subprocess

def esegui_comando(comando, timeout=60):
    """Esegue un comando di sistema con gestione errori e timeout."""
    try:
        risultato = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "successo": risultato.returncode == 0,
            "stdout": risultato.stdout.strip(),
            "stderr": risultato.stderr.strip(),
            "codice": risultato.returncode
        }
    except subprocess.TimeoutExpired:
        return {"successo": False, "stdout": "", "stderr": "Timeout superato", "codice": -1}
```

---

## Bash Scripting per Automazione

Bash e il linguaggio di scripting nativo dei sistemi Unix/Linux. Per operazioni di sistema, gestione file e orchestrazione di comandi, resta insostituibile per semplicita e immediatezza.

**Struttura di uno script Bash robusto:**

```bash
#!/usr/bin/env bash
#
# backup_giornaliero.sh — Script di backup giornaliero con rotazione
# Utilizzo: ./backup_giornaliero.sh [directory_sorgente] [directory_destinazione]
#

# Modalita rigorosa: esce in caso di errore, variabili non definite, errori in pipe
set -euo pipefail
IFS=$'\n\t'

# === Configurazione ===
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly LOG_FILE="/var/log/backup_giornaliero.log"
readonly DATA_OGGI=$(date +%Y-%m-%d_%H%M%S)
readonly RETENTION_DAYS=30

# === Parametri ===
SORGENTE="${1:-/home}"
DESTINAZIONE="${2:-/backup}"

# === Funzioni ===
log() {
    local livello="$1"
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$livello] $*" | tee -a "$LOG_FILE"
}

cleanup() {
    local codice_uscita=$?
    if [[ $codice_uscita -ne 0 ]]; then
        log "ERROR" "Script terminato con errore (codice: $codice_uscita)"
    fi
    # Rimuovi file temporanei se presenti
    rm -f /tmp/backup_temp_*
}
trap cleanup EXIT

verifica_prerequisiti() {
    if ! command -v rsync &> /dev/null; then
        log "ERROR" "rsync non trovato. Installalo con: sudo apt install rsync"
        exit 1
    fi

    if [[ ! -d "$SORGENTE" ]]; then
        log "ERROR" "Directory sorgente non esistente: $SORGENTE"
        exit 1
    fi

    mkdir -p "$DESTINAZIONE"
}

esegui_backup() {
    local archivio="${DESTINAZIONE}/backup_${DATA_OGGI}.tar.gz"

    log "INFO" "Avvio backup: $SORGENTE -> $archivio"

    rsync -avz --delete \
        --exclude='.cache' \
        --exclude='node_modules' \
        --exclude='.git' \
        "$SORGENTE/" "${DESTINAZIONE}/corrente/"

    tar -czf "$archivio" -C "${DESTINAZIONE}" "corrente/"

    local dimensione
    dimensione=$(du -sh "$archivio" | cut -f1)
    log "INFO" "Backup completato: $archivio ($dimensione)"
}

ruota_backup() {
    log "INFO" "Rotazione backup: rimozione archivi piu vecchi di $RETENTION_DAYS giorni"

    local contatore=0
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((contatore++))
    done < <(find "$DESTINAZIONE" -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -print0)

    log "INFO" "Rimossi $contatore archivi obsoleti"
}

# === Esecuzione ===
main() {
    log "INFO" "=== Avvio $SCRIPT_NAME ==="
    verifica_prerequisiti
    esegui_backup
    ruota_backup
    log "INFO" "=== $SCRIPT_NAME completato con successo ==="
}

main "$@"
```

**Pattern comuni — Health check dei servizi:**

```bash
#!/usr/bin/env bash
set -euo pipefail

SERVIZI=("nginx" "postgresql" "redis-server" "docker")
ENDPOINT_HTTP=(
    "http://localhost:80|200"
    "http://localhost:8080/health|200"
    "http://localhost:3000/api/status|200"
)

verifica_servizi_systemd() {
    echo "=== Verifica Servizi Systemd ==="
    for servizio in "${SERVIZI[@]}"; do
        if systemctl is-active --quiet "$servizio"; then
            echo "[OK]     $servizio"
        else
            echo "[ERRORE] $servizio non attivo!"
            systemctl status "$servizio" --no-pager -l 2>&1 | tail -5
        fi
    done
}

verifica_endpoint_http() {
    echo ""
    echo "=== Verifica Endpoint HTTP ==="
    for entry in "${ENDPOINT_HTTP[@]}"; do
        url="${entry%%|*}"
        codice_atteso="${entry##*|}"
        codice_reale=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")

        if [[ "$codice_reale" == "$codice_atteso" ]]; then
            echo "[OK]     $url (HTTP $codice_reale)"
        else
            echo "[ERRORE] $url (atteso $codice_atteso, ricevuto $codice_reale)"
        fi
    done
}

verifica_spazio_disco() {
    echo ""
    echo "=== Utilizzo Disco ==="
    while read -r uso mount; do
        percentuale="${uso%%%}"
        if [[ $percentuale -ge 90 ]]; then
            echo "[CRITICO] $mount al ${uso}"
        elif [[ $percentuale -ge 75 ]]; then
            echo "[ATTENZIONE] $mount al ${uso}"
        else
            echo "[OK]     $mount al ${uso}"
        fi
    done < <(df -h --output=pcent,target | tail -n +2 | grep -v tmpfs)
}

verifica_servizi_systemd
verifica_endpoint_http
verifica_spazio_disco
```

**Gestione cron e strumenti utili:**

```bash
# Editing crontab
crontab -e

# Esempi di espressioni cron
# ┌───────── minuto (0-59)
# │ ┌─────── ora (0-23)
# │ │ ┌───── giorno del mese (1-31)
# │ │ │ ┌─── mese (1-12)
# │ │ │ │ ┌─ giorno della settimana (0-7, 0 e 7 = domenica)

# Backup giornaliero alle 02:00
0 2 * * * /opt/scripts/backup_giornaliero.sh >> /var/log/cron_backup.log 2>&1

# Health check ogni 5 minuti
*/5 * * * * /opt/scripts/health_check.sh >> /var/log/cron_health.log 2>&1

# Report settimanale il lunedi alle 08:00
0 8 * * 1 /opt/scripts/report_settimanale.sh

# jq — Elaborazione JSON da riga di comando
curl -s https://api.esempio.com/dati | jq '.risultati[] | {nome: .name, stato: .status}'

# rsync — Sincronizzazione file efficiente
rsync -avz --progress --exclude='.git' /locale/progetto/ utente@server:/remoto/progetto/
```

Il flag `set -euo pipefail` e essenziale per ogni script Bash di automazione. Senza di esso, gli errori possono passare inosservati, creando situazioni in cui lo script continua l'esecuzione dopo un fallimento parziale con conseguenze potenzialmente disastrose.

---

## PowerShell per Automazione

PowerShell e il linguaggio di scripting di riferimento per ambienti Windows e, dalla versione Core 7+, e disponibile anche su Linux e macOS. La sua caratteristica distintiva e il modello a oggetti: ogni comando restituisce oggetti .NET, non semplice testo, rendendo l'elaborazione dei dati molto piu robusta.

**Struttura e execution policy:**

```powershell
# Verifica e impostazione della policy di esecuzione
Get-ExecutionPolicy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Struttura di uno script PowerShell ben organizzato
#Requires -Version 7.0
#Requires -Modules ActiveDirectory

<#
.SYNOPSIS
    Script per la gestione automatizzata degli account utente.
.DESCRIPTION
    Crea, modifica e disabilita account Active Directory in base
    a un file CSV di input proveniente dall'ufficio HR.
.PARAMETER PercorsoCSV
    Percorso del file CSV con i dati degli utenti.
.EXAMPLE
    .\Gestione-Utenti.ps1 -PercorsoCSV "C:\HR\nuovi_utenti.csv"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path $_ -PathType Leaf })]
    [string]$PercorsoCSV,

    [Parameter()]
    [switch]$SoloSimulazione
)

# Configurazione errori
$ErrorActionPreference = "Stop"

# Funzione di logging
function Write-Log {
    param(
        [string]$Messaggio,
        [ValidateSet("INFO", "WARN", "ERROR")]
        [string]$Livello = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $entry = "[$timestamp] [$Livello] $Messaggio"
    Add-Content -Path "C:\Logs\gestione_utenti.log" -Value $entry
    switch ($Livello) {
        "ERROR" { Write-Error $Messaggio }
        "WARN"  { Write-Warning $Messaggio }
        default { Write-Host $entry }
    }
}
```

**Automazione Active Directory:**

```powershell
function New-UtenteAutomatico {
    param(
        [string]$Nome,
        [string]$Cognome,
        [string]$Reparto,
        [string]$Email
    )

    $username = "$($Nome.Substring(0,1).ToLower()).$($Cognome.ToLower())"
    $ou = "OU=$Reparto,OU=Utenti,DC=esempio,DC=com"

    try {
        $parametri = @{
            Name              = "$Nome $Cognome"
            GivenName         = $Nome
            Surname           = $Cognome
            SamAccountName    = $username
            UserPrincipalName = "$username@esempio.com"
            EmailAddress      = $Email
            Department        = $Reparto
            Path              = $ou
            AccountPassword   = (ConvertTo-SecureString "PasswordTemp123!" -AsPlainText -Force)
            ChangePasswordAtLogon = $true
            Enabled           = $true
        }

        New-ADUser @parametri
        Write-Log "Utente creato: $username in $ou"

        # Aggiunta ai gruppi predefiniti
        $gruppi = Get-GruppiPerReparto -Reparto $Reparto
        foreach ($gruppo in $gruppi) {
            Add-ADGroupMember -Identity $gruppo -Members $username
            Write-Log "Aggiunto $username al gruppo $gruppo"
        }
    }
    catch {
        Write-Log "Errore creazione utente $username : $_" -Livello "ERROR"
    }
}
```

**Esecuzione remota e gestione errori:**

```powershell
# Esecuzione remota su piu server
$servers = @("server01", "server02", "server03")
$credenziali = Get-Credential

$risultati = Invoke-Command -ComputerName $servers -Credential $credenziali -ScriptBlock {
    [PSCustomObject]@{
        Hostname    = $env:COMPUTERNAME
        Uptime      = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
        CPUPercent  = (Get-CimInstance Win32_Processor).LoadPercentage
        RAMLibera   = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
        DiscoLibero = (Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace / 1GB
    }
}

$risultati | Format-Table -AutoSize

# Gestione errori strutturata
try {
    # Operazione potenzialmente rischiosa
    Stop-Service -Name "ServizioImportante" -Force
    # ... manutenzione ...
    Start-Service -Name "ServizioImportante"
}
catch [System.ServiceProcess.ServiceNotFoundException] {
    Write-Log "Servizio non trovato sul sistema" -Livello "WARN"
}
catch {
    Write-Log "Errore imprevisto: $($_.Exception.Message)" -Livello "ERROR"
    # Tentativo di ripristino
    Start-Service -Name "ServizioImportante" -ErrorAction SilentlyContinue
}
finally {
    Write-Log "Operazione di manutenzione completata"
}
```

PowerShell eccelle nell'automazione di ambienti Windows grazie all'integrazione nativa con Active Directory, Exchange, Azure, IIS e l'intero ecosistema Microsoft. Le scheduled task di Windows si configurano tramite `Register-ScheduledTask` o il Task Scheduler grafico, offrendo capacita di trigger avanzate (evento di sistema, login utente, stato della rete).

---

## Ansible — Configuration Management e Automazione

### Architettura

Ansible e uno strumento di automazione IT che adotta un modello **agentless**: non richiede l'installazione di alcun software sui nodi gestiti. Comunica tramite SSH (per Linux/macOS) o WinRM (per Windows), utilizzando il **control node** (la macchina da cui si esegue Ansible) per orchestrare le operazioni su tutti i **managed nodes**.

Questo approccio agentless offre vantaggi significativi: nessun demone da mantenere aggiornato sui server gestiti, nessuna porta aggiuntiva da aprire nel firewall (SSH e gia presente), nessun certificato da distribuire e nessun single point of failure dovuto a un agent server centralizzato.

L'architettura di Ansible si basa su un modello **push**: il control node invia i comandi ai nodi gestiti. Questo contrasta con strumenti come Puppet o Chef che adottano un modello **pull** dove gli agent scaricano periodicamente la configurazione da un server centrale.

**Installazione:**

```bash
# Su Ubuntu/Debian
sudo apt update && sudo apt install ansible

# Tramite pip (consigliato per avere la versione piu recente)
pip install ansible

# Verifica
ansible --version
```

---

### Componenti Fondamentali

**Inventory — Definizione dell'infrastruttura:**

```ini
# /etc/ansible/hosts oppure inventory.ini

[webservers]
web01.esempio.com ansible_host=192.168.1.10
web02.esempio.com ansible_host=192.168.1.11

[dbservers]
db01.esempio.com ansible_host=192.168.1.20 ansible_user=postgres
db02.esempio.com ansible_host=192.168.1.21 ansible_user=postgres

[loadbalancers]
lb01.esempio.com ansible_host=192.168.1.5

# Variabili per gruppi
[webservers:vars]
http_port=8080
max_clients=200
ansible_user=deploy
ansible_python_interpreter=/usr/bin/python3

[produzione:children]
webservers
dbservers
loadbalancers

[produzione:vars]
ambiente=produzione
monitoring_enabled=true
```

**Inventory dinamico** per ambienti cloud (AWS, Azure, GCP):

```yaml
# aws_ec2.yml — Inventory dinamico per AWS
plugin: amazon.aws.aws_ec2
regions:
  - eu-south-1
  - eu-west-1
keyed_groups:
  - key: tags.Environment
    prefix: env
  - key: tags.Role
    prefix: role
filters:
  instance-state-name: running
```

**Playbook — Il cuore dell'automazione Ansible:**

```yaml
# setup_webserver.yml
---
- name: Configurazione server web
  hosts: webservers
  become: true
  vars:
    pacchetti_richiesti:
      - nginx
      - certbot
      - python3-certbot-nginx
      - fail2ban
    dominio: "app.esempio.com"

  tasks:
    - name: Aggiornamento cache dei pacchetti
      apt:
        update_cache: true
        cache_valid_time: 3600

    - name: Installazione pacchetti richiesti
      apt:
        name: "{{ pacchetti_richiesti }}"
        state: present
      notify: Riavvia Nginx

    - name: Copia configurazione Nginx
      template:
        src: templates/nginx.conf.j2
        dest: /etc/nginx/sites-available/{{ dominio }}
        owner: root
        group: root
        mode: "0644"
      notify: Riavvia Nginx

    - name: Attivazione sito
      file:
        src: /etc/nginx/sites-available/{{ dominio }}
        dest: /etc/nginx/sites-enabled/{{ dominio }}
        state: link
      notify: Riavvia Nginx

    - name: Rimozione configurazione predefinita
      file:
        path: /etc/nginx/sites-enabled/default
        state: absent
      notify: Riavvia Nginx

    - name: Apertura porte firewall
      ufw:
        rule: allow
        port: "{{ item }}"
        proto: tcp
      loop:
        - "80"
        - "443"

    - name: Avvio e abilitazione servizi
      systemd:
        name: "{{ item }}"
        state: started
        enabled: true
      loop:
        - nginx
        - fail2ban

  handlers:
    - name: Riavvia Nginx
      systemd:
        name: nginx
        state: restarted
```

**Moduli fondamentali:**

I moduli sono le unita operative di Ansible. Ogni task invoca un modulo specifico. I moduli piu utilizzati includono:

- **`apt` / `yum` / `dnf`** — gestione pacchetti per le diverse distribuzioni
- **`copy`** — copia file dal control node ai managed nodes
- **`template`** — rendering di template Jinja2 e distribuzione
- **`service` / `systemd`** — gestione servizi di sistema
- **`user` / `group`** — gestione utenti e gruppi
- **`file`** — gestione permessi, creazione directory, link simbolici
- **`command` / `shell`** — esecuzione di comandi arbitrari (da usare solo quando non esiste un modulo specifico)
- **`git`** — operazioni su repository Git
- **`cron`** — gestione job cron
- **`docker_container` / `docker_image`** — gestione container Docker

**Variables e Facts:**

```yaml
# group_vars/webservers.yml
---
http_port: 8080
document_root: /var/www/html
ssl_enabled: true
max_upload_size: "50M"

# host_vars/web01.esempio.com.yml
---
server_id: 1
extra_modules:
  - mod_rewrite
  - mod_headers
```

I **facts** sono informazioni raccolte automaticamente dai nodi gestiti all'inizio di ogni playbook:

```yaml
# Utilizzo dei facts nei task
- name: Configurazione basata sul sistema operativo
  template:
    src: "config_{{ ansible_os_family }}.j2"
    dest: /etc/app/config.conf
  when: ansible_os_family == "Debian"

- name: Allocazione memoria basata sulla RAM disponibile
  template:
    src: memory_config.j2
    dest: /etc/app/memory.conf
  vars:
    memoria_app: "{{ (ansible_memtotal_mb * 0.7) | int }}"
```

**Roles — Organizzazione modulare:**

```
roles/
└── webserver/
    ├── defaults/
    │   └── main.yml        # Variabili predefinite (sovrascrivibili)
    ├── files/
    │   └── index.html       # File statici
    ├── handlers/
    │   └── main.yml        # Handler (riavvii servizi, etc.)
    ├── meta/
    │   └── main.yml        # Metadati e dipendenze
    ├── tasks/
    │   └── main.yml        # Task principali
    ├── templates/
    │   └── nginx.conf.j2   # Template Jinja2
    └── vars/
        └── main.yml        # Variabili del ruolo
```

```yaml
# roles/webserver/tasks/main.yml
---
- name: Inclusione task specifici per OS
  include_tasks: "setup_{{ ansible_os_family | lower }}.yml"

- name: Configurazione Nginx
  import_tasks: configure_nginx.yml

- name: Configurazione SSL
  import_tasks: configure_ssl.yml
  when: ssl_enabled | default(false)
```

---

### Playbook Pratici

**Provisioning completo di un server:**

```yaml
---
- name: Provisioning iniziale del server
  hosts: nuovi_server
  become: true
  vars:
    utenti_admin:
      - nome: "deploy"
        chiave_ssh: "ssh-rsa AAAAB3..."
      - nome: "monitor"
        chiave_ssh: "ssh-rsa AAAAB4..."
    pacchetti_base:
      - vim
      - htop
      - tmux
      - curl
      - wget
      - git
      - unzip
      - net-tools
      - jq

  tasks:
    - name: Aggiornamento completo del sistema
      apt:
        upgrade: dist
        update_cache: true

    - name: Installazione pacchetti base
      apt:
        name: "{{ pacchetti_base }}"
        state: present

    - name: Creazione utenti amministrativi
      user:
        name: "{{ item.nome }}"
        groups: sudo
        shell: /bin/bash
        create_home: true
        state: present
      loop: "{{ utenti_admin }}"

    - name: Distribuzione chiavi SSH
      authorized_key:
        user: "{{ item.nome }}"
        key: "{{ item.chiave_ssh }}"
        state: present
      loop: "{{ utenti_admin }}"

    - name: Configurazione sudoers senza password per deploy
      lineinfile:
        path: /etc/sudoers.d/deploy
        line: "deploy ALL=(ALL) NOPASSWD: ALL"
        create: true
        validate: "visudo -cf %s"

    - name: Configurazione timezone
      timezone:
        name: Europe/Rome

    - name: Configurazione NTP
      apt:
        name: chrony
        state: present
      notify: Avvia Chrony

    - name: Disabilitazione login root via SSH
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: "^PermitRootLogin"
        line: "PermitRootLogin no"
      notify: Riavvia SSH

    - name: Disabilitazione autenticazione password SSH
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: "^PasswordAuthentication"
        line: "PasswordAuthentication no"
      notify: Riavvia SSH

    - name: Configurazione firewall UFW
      ufw:
        rule: allow
        port: "{{ item }}"
      loop:
        - "22"
        - "80"
        - "443"

    - name: Attivazione UFW
      ufw:
        state: enabled
        policy: deny

  handlers:
    - name: Riavvia SSH
      systemd:
        name: sshd
        state: restarted

    - name: Avvia Chrony
      systemd:
        name: chrony
        state: started
        enabled: true
```

**Gestione dei servizi applicativi:**

```yaml
---
- name: Deploy applicazione web
  hosts: webservers
  become: true
  serial: 1  # Deploy rolling (un server alla volta)
  vars:
    app_version: "2.4.1"
    app_dir: /opt/webapp
    app_user: webapp

  pre_tasks:
    - name: Rimozione server dal load balancer
      uri:
        url: "http://{{ lb_host }}/api/backends/{{ inventory_hostname }}/disable"
        method: POST
      delegate_to: localhost

    - name: Attesa drenaggio connessioni
      pause:
        seconds: 30

  tasks:
    - name: Download nuova versione dell'applicazione
      get_url:
        url: "https://releases.esempio.com/webapp-{{ app_version }}.tar.gz"
        dest: /tmp/webapp-{{ app_version }}.tar.gz
        checksum: "sha256:{{ app_checksum }}"

    - name: Estrazione archivio
      unarchive:
        src: /tmp/webapp-{{ app_version }}.tar.gz
        dest: "{{ app_dir }}"
        remote_src: true
        owner: "{{ app_user }}"
        group: "{{ app_user }}"

    - name: Aggiornamento configurazione
      template:
        src: app_config.yml.j2
        dest: "{{ app_dir }}/config.yml"
        owner: "{{ app_user }}"
      notify: Riavvia Applicazione

    - name: Esecuzione migrazioni database
      command: "{{ app_dir }}/bin/migrate --apply"
      become_user: "{{ app_user }}"
      run_once: true  # Esegui solo una volta, non su ogni server

  post_tasks:
    - name: Verifica health check applicazione
      uri:
        url: "http://localhost:{{ http_port }}/health"
        status_code: 200
      register: health_result
      retries: 10
      delay: 5
      until: health_result.status == 200

    - name: Reinserimento server nel load balancer
      uri:
        url: "http://{{ lb_host }}/api/backends/{{ inventory_hostname }}/enable"
        method: POST
      delegate_to: localhost

  handlers:
    - name: Riavvia Applicazione
      systemd:
        name: webapp
        state: restarted
```

---

### Ansible Avanzato

**Vault — Gestione dei segreti:**

Ansible Vault consente di cifrare file e variabili contenenti informazioni sensibili (password, chiavi API, certificati) direttamente nel repository di codice.

```bash
# Creazione di un file cifrato
ansible-vault create secrets.yml

# Cifratura di un file esistente
ansible-vault encrypt group_vars/produzione/secrets.yml

# Modifica di un file cifrato
ansible-vault edit group_vars/produzione/secrets.yml

# Esecuzione playbook con vault
ansible-playbook deploy.yml --ask-vault-pass
ansible-playbook deploy.yml --vault-password-file ~/.vault_password
```

```yaml
# group_vars/produzione/secrets.yml (cifrato con vault)
---
db_password: "SuperSegreta123!"
api_key_monitoring: "sk-live-xxxxxxxxxxxx"
ssl_private_key: |
  -----BEGIN PRIVATE KEY-----
  MIIEvQIBADANBg...
  -----END PRIVATE KEY-----
```

**Template Jinja2:**

```jinja2
{# templates/nginx.conf.j2 #}
upstream app_backend {
{% for host in groups['webservers'] %}
    server {{ hostvars[host]['ansible_host'] }}:{{ http_port }} weight={{ hostvars[host].get('weight', 1) }};
{% endfor %}
}

server {
    listen 80;
    server_name {{ dominio }};

{% if ssl_enabled %}
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name {{ dominio }};

    ssl_certificate /etc/letsencrypt/live/{{ dominio }}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{{ dominio }}/privkey.pem;
{% endif %}

    client_max_body_size {{ max_upload_size | default('10M') }};

    location / {
        proxy_pass http://app_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias {{ document_root }}/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

**Condizionali, loop e gestione errori:**

```yaml
---
- name: Configurazione condizionale e gestione errori
  hosts: all
  become: true

  tasks:
    # Condizionali
    - name: Installazione su Debian/Ubuntu
      apt:
        name: nginx
        state: present
      when: ansible_os_family == "Debian"

    - name: Installazione su RedHat/CentOS
      yum:
        name: nginx
        state: present
      when: ansible_os_family == "RedHat"

    # Loop con condizionale
    - name: Creazione utenti con ruoli specifici
      user:
        name: "{{ item.nome }}"
        groups: "{{ item.gruppi | join(',') }}"
        state: present
      loop:
        - { nome: "sviluppatore1", gruppi: ["dev", "docker"], attivo: true }
        - { nome: "sviluppatore2", gruppi: ["dev"], attivo: true }
        - { nome: "exdipendente", gruppi: [], attivo: false }
      when: item.attivo

    # Gestione errori con block/rescue/always
    - name: Deploy con rollback automatico
      block:
        - name: Backup versione corrente
          command: cp -r /opt/app /opt/app.backup

        - name: Deploy nuova versione
          unarchive:
            src: /tmp/app-nuova.tar.gz
            dest: /opt/app
            remote_src: true

        - name: Verifica funzionamento
          uri:
            url: http://localhost:8080/health
            status_code: 200
          register: health
          retries: 5
          delay: 3
          until: health.status == 200

      rescue:
        - name: Rollback alla versione precedente
          command: mv /opt/app.backup /opt/app

        - name: Riavvio servizio con versione precedente
          systemd:
            name: webapp
            state: restarted

        - name: Notifica fallimento deploy
          mail:
            to: team@esempio.com
            subject: "ALERT: Deploy fallito su {{ inventory_hostname }}"
            body: "Il deploy e fallito. Rollback eseguito automaticamente."
          delegate_to: localhost

      always:
        - name: Pulizia file temporanei
          file:
            path: /tmp/app-nuova.tar.gz
            state: absent

        - name: Registrazione stato deploy
          lineinfile:
            path: /var/log/deploy.log
            line: "{{ ansible_date_time.iso8601 }} - Deploy {{ 'FALLITO' if ansible_failed_task is defined else 'RIUSCITO' }}"
            create: true
```

**Tags per esecuzione selettiva:**

```yaml
tasks:
  - name: Aggiornamento sistema
    apt:
      upgrade: dist
    tags: [sistema, aggiornamento]

  - name: Configurazione Nginx
    template:
      src: nginx.conf.j2
      dest: /etc/nginx/nginx.conf
    tags: [nginx, configurazione]

  - name: Deploy applicazione
    git:
      repo: "https://github.com/org/app.git"
      dest: /opt/app
      version: "{{ app_version }}"
    tags: [deploy, applicazione]
```

```bash
# Esecuzione solo dei task con tag specifico
ansible-playbook site.yml --tags "deploy"

# Esclusione di tag specifici
ansible-playbook site.yml --skip-tags "aggiornamento"
```

**AWX/Tower — Interfaccia grafica per Ansible:**

AWX (versione open-source) e Ansible Tower (versione enterprise, ora parte di Ansible Automation Platform) forniscono un'interfaccia web per la gestione di Ansible, aggiungendo funzionalita enterprise:

- **Dashboard centralizzata** con visibilita su tutti i job e il loro stato
- **RBAC** (Role-Based Access Control) per il controllo degli accessi granulare
- **Inventari dinamici** integrati con provider cloud
- **Schedulazione** dei playbook tramite interfaccia grafica
- **Notifiche** (email, Slack, webhook) al completamento dei job
- **API REST** per l'integrazione con pipeline CI/CD e strumenti di orchestrazione
- **Audit log** completo di tutte le operazioni eseguite

AWX si installa su Kubernetes ed e la scelta consigliata per team che necessitano di governance, tracciabilita e collaborazione nell'utilizzo di Ansible.

---

## Best Practices

1. **Versionare sempre tutto il codice di automazione in Git.** Ogni script, playbook, template e file di configurazione deve essere tracciato in un sistema di controllo versione. Questo garantisce tracciabilita, collaborazione, possibilita di rollback e audit completo di ogni modifica. Non esistono eccezioni: anche uno script "temporaneo" merita un commit.

2. **Separare rigorosamente i segreti dal codice.** Mai inserire password, chiavi API, token o certificati direttamente nel codice sorgente. Utilizzare variabili d'ambiente, file `.env` (esclusi da Git tramite `.gitignore`), Ansible Vault, HashiCorp Vault o il secrets manager del proprio cloud provider. La compromissione di un singolo segreto nel codice puo avere conseguenze devastanti.

3. **Implementare logging strutturato e centralizzato.** Ogni script di automazione deve produrre log dettagliati con timestamp, livello di severita e contesto sufficiente per il debugging. Per ambienti complessi, centralizzare i log con strumenti come ELK Stack, Grafana Loki o CloudWatch. I log sono la prima risorsa diagnostica quando qualcosa non funziona alle 03:00 di notte.

4. **Adottare l'idempotenza come principio guida.** Uno script idempotente produce lo stesso risultato indipendentemente da quante volte viene eseguito. Questo e particolarmente cruciale per Ansible (dove e un principio architetturale), ma vale per qualsiasi automazione. Prima di creare un file, verificare se esiste. Prima di installare un pacchetto, verificare se e gia presente. L'idempotenza elimina una classe intera di errori.

5. **Testare l'automazione in ambienti isolati prima della produzione.** Utilizzare macchine virtuali, container Docker o ambienti di staging per validare ogni modifica prima di applicarla ai sistemi di produzione. Per Ansible, Molecule offre un framework di test dedicato. Per script Python, i test unitari con pytest e i mock sono essenziali. L'automazione non testata e un rischio, non un vantaggio.

6. **Gestire gli errori in modo esplicito e prevedibile.** Ogni operazione che puo fallire deve essere gestita con try/except (Python), set -euo pipefail (Bash), block/rescue (Ansible) o try/catch (PowerShell). Definire chiaramente cosa succede in caso di fallimento: il processo si interrompe? Esegue un rollback? Invia una notifica? La gestione degli errori non e un'aggiunta opzionale, e parte integrante della logica.

7. **Documentare il "perche", non solo il "cosa".** Il codice spiega gia cosa fa (se scritto bene). I commenti e la documentazione devono spiegare le motivazioni dietro le scelte progettuali, i vincoli, le dipendenze e le assunzioni. Un playbook Ansible con commenti che spiegano perche un certo ordine di operazioni e necessario e infinitamente piu utile di uno senza commenti.

8. **Implementare notifiche e alerting per ogni automazione critica.** Se un backup fallisce ma nessuno lo sa, il backup non esiste. Ogni automazione che opera in background deve notificare il team in caso di successo, fallimento o anomalia. Utilizzare canali appropriati: email per report, Slack/Teams per alert urgenti, sistemi di monitoring per metriche continue.

9. **Applicare il principio del privilegio minimo.** Gli script di automazione devono operare con i permessi strettamente necessari per svolgere il loro compito. Un cron job che legge file di log non necessita di accesso root. Un playbook Ansible che configura Nginx non necessita di accesso al database. Limitare i permessi riduce la superficie di attacco e i danni potenziali in caso di errore o compromissione.

10. **Evolvere l'automazione in modo incrementale e iterativo.** Non tentare di automatizzare tutto in una volta. Iniziare con i task piu ripetitivi e a basso rischio, consolidare, quindi estendere gradualmente. Ogni iterazione deve essere stabile prima di procedere alla successiva. L'automazione e un percorso continuo di miglioramento, non un progetto con una data di fine definita.

---

## Esercizi

1. **Lab — Bash to Python migration.** Prendi uno script Bash di 100+ righe e riscrivilo in Python. Confronta linee, leggibilita, error handling, test.
2. **Lab — secret management.** Implementa lo stesso script con 3 strategie: hardcoded (anti-pattern), env vars, HashiCorp Vault. Documenta trade-off.
3. **Stretch — CLI tool con click.** Scrivi un CLI Python (con `click`) che ha 5 sotto-comandi (init, sync, status, rollback, version), con `--help` per ognuno, completion shell, logging JSON.

## Auto-valutazione

1. Quando preferire Bash a Python (e viceversa)?
2. Cosa fa `set -euo pipefail`?
3. argparse vs click: differenze pratiche.
4. Logging strutturato JSON: come configurarlo in Python?
5. Privilegio minimo per cron: cosa significa?

## Letture primarie consigliate

- Bash manual — `man bash` (specialmente sezione `set`).
- Python — `logging` documentation. https://docs.python.org/3/library/logging.html
- click — Python CLI framework. https://click.palletsprojects.com/
- Google — Bash style guide. https://google.github.io/styleguide/shellguide.html

## Collegamenti incrociati

- Modulo 12 — `12-python-automazione-avanzata.md`: deep dive Python.
- Modulo 13 — `13-ansible-automazione-infrastruttura.md`: Ansible YAML.

## Glossario locale

| Termine | Definizione |
|---|---|
| **`set -e`** | Bash exits on error. |
| **`set -u`** | Bash errors on undefined var. |
| **`set -o pipefail`** | Bash propagates error in pipeline. |
| **`argparse`** | Python stdlib CLI parser. |
| **`click`** | Third-party CLI framework, piu ricco. |
| **Structured logging** | Log in JSON per parsing automatico. |
| **Privilegio minimo** | Esegui con permessi minimi necessari. |
