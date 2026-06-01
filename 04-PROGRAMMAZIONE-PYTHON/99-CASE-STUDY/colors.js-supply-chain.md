# Case Study — colors.js Supply-Chain Sabotage (2022) e Implicazioni Python

> **Aggiornamento:** 2026-05-22
> **Tipo:** sabotaggio intenzionale da parte del maintainer
> **Pacchetti colpiti:** `colors.js` (npm, ~18M download settimanali), `faker.js` (npm, ~2.5M download settimanali)
> **Data:** 8 gennaio 2022
> **Impatto:** interruzione immediata di migliaia di progetti dipendenti

---

## Sommario esecutivo

L'8 gennaio 2022, Marak Squires — unico maintainer delle librerie npm `colors.js` e
`faker.js` — ha pubblicato versioni deliberatamente sabotate di entrambi i pacchetti.
`colors.js` v1.4.1 e v1.4.2 includevano un loop infinito che stampava caratteri casuali
sulla console, bloccando qualsiasi processo Node.js che importasse la libreria. `faker.js`
v6.6.6 sostituiva l'intera funzionalità con il messaggio "endgame" e testo di protesta.

L'atto era una protesta esplicita di Squires contro le grandi aziende che usano software
open source senza contribuire economicamente ai maintainer. L'incidente ha avuto un impatto
massiccio — `colors.js` era una dipendenza transitiva di tool come AWS CDK, Sentry CLI,
e migliaia di altri progetti — e ha riacceso il dibattito sulla sostenibilità dell'open
source e sulla fiducia nei maintainer.

Per l'ecosistema Python, l'incidente è un caso di studio diretto: PyPI soffre degli stessi
problemi strutturali — single maintainer, assenza di firma, typosquatting — e ha vissuto
incidenti analoghi con pacchetti come `request`, `colorama` e altri.

---

## Timeline dettagliata dell'incidente

### Pre-incidente — Il contesto

| Data | Evento |
|------|--------|
| **2020-11** | Marak Squires apre una issue su `faker.js` intitolata "No more free work from Marak" esprimendo frustrazione per lo sfruttamento commerciale del suo lavoro senza compenso. Cita specificamente grandi aziende Fortune 500 che usano `faker.js` in produzione. |
| **2020-11 – 2021-12** | Il sentimento di Squires si intensifica. Diverse issue e commenti sul tema della compensazione per il lavoro open source vengono pubblicati e poi rimossi. |
| **2021** | Squires subisce un incendio che distrugge la sua casa e affronta difficoltà economiche, amplificando la frustrazione verso un ecosistema che genera miliardi di dollari di valore ma non compensa i maintainer critici. |

### L'attacco

| Data | Evento |
|------|--------|
| **2022-01-08** | Squires pubblica `colors.js` v1.4.1, poi v1.4.2. La nuova versione include un loop infinito nel codice di inizializzazione che stampa la stringa "LIBERTY LIBERTY LIBERTY" con caratteri casuali non-ASCII all'infinito sulla console. |
| **2022-01-08** | Squires pubblica `faker.js` v6.6.6. L'intera base di codice viene sostituita con un `README.md` che contiene "endgame" e testo di protesta. Tutto il codice funzionale viene rimosso. |
| **2022-01-08** | Impatto immediato. Qualsiasi progetto con `colors.js` come dipendenza (diretta o transitiva) che installa con range semver (`^1.4.0`, `~1.4.0`, o `latest`) riceve la versione sabotata. I processi Node.js si bloccano al boot. |

### La propagazione

| Data | Evento |
|------|--------|
| **2022-01-08 – 2022-01-09** | Migliaia di issue vengono aperte su GitHub per progetti impattati. AWS CDK, `@sentry/cli`, `jest`, e numerosi altri tool CLI che usano `colors.js` per output colorato smettono di funzionare. |
| **2022-01-09** | npm interviene: reverte `colors.js` alla versione 1.4.0 (ultima versione stabile) e limita l'account di Squires. |
| **2022-01-09** | GitHub sospende temporaneamente l'account di Squires (ripristinato successivamente). |
| **2022-01-09 – 2022-01-10** | La community si divide tra chi condanna l'atto e chi sostiene le ragioni di Squires. Dibattito intenso su Hacker News, Reddit, Twitter. |

### Aftermath

| Data | Evento |
|------|--------|
| **2022-01-10 – 2022-01-15** | Nasce `@faker-js/faker` — un fork community-maintained di `faker.js` con governance multi-maintainer. Il fork diventerà più popolare dell'originale. |
| **2022-01** | npm rafforza le policy sulla rimozione di versioni e introduce controlli aggiuntivi per pubblicazioni potenzialmente distruttive. |
| **2022 – 2023** | L'incidente accelera iniziative di funding per l'open source: GitHub Sponsors, Tidelift, Open Collective ricevono attenzione rinnovata. |

---

## Analisi tecnica approfondita

### Il codice sabotato in `colors.js`

La versione 1.4.1/1.4.2 di `colors.js` includeva un loop infinito inserito nel file
di inizializzazione della libreria:

```javascript
// Ricostruzione semplificata del sabotaggio in colors.js v1.4.2
// File: lib/index.js

// Codice originale: funzioni per colorare output console
// Aggiunta malevola: loop infinito che stampa indefinitamente

let am = require('../lib/custom/american');
am = am();

for (let i = 666; i < Infinity; i++) {
  // Genera stringa "LIBERTY LIBERTY LIBERTY" con caratteri non-ASCII
  if (i % 333 === 0) {
    // Stampa indefinitamente, bloccando il processo
    console.log('LIBERTY LIBERTY LIBERTY');
  }
  // Aggiunge caratteri casuali Unicode
  let randomChars = '';
  for (let j = 0; j < 1000; j++) {
    randomChars += String.fromCharCode(Math.random() * 65535);
  }
  console.log(randomChars);
}
```

**Effetto pratico:**

```bash
# Qualsiasi script che importa colors.js
$ node -e "require('colors')"
LIBERTY LIBERTY LIBERTY
⌂ñ╗▒░█▓▀▄▌▐┌┐└┘├┤┬┴├...  # output infinito
# Il processo non termina mai, consuma CPU e memoria
# Ctrl+C necessario per uccidere il processo
```

### Il sabotaggio in `faker.js`

```javascript
// faker.js v6.6.6 — tutto il codice rimpiazzato con:
module.exports = {
  endgame: "What really happened with Aaron Swartz?"
};
// Ogni chiamata a faker.name.firstName(), faker.address.city(), ecc. → crash
```

### Il meccanismo di propagazione: semver ranges

La vulnerabilità strutturale che ha reso l'attacco così efficace è il sistema di
semver ranges di npm:

```json
// package.json di un progetto vittima
{
  "dependencies": {
    "colors": "^1.4.0"    // Accetta qualsiasi 1.x.x >= 1.4.0
                           // → installa 1.4.2 (sabotata)
  }
}

// Varianti equivalentemente vulnerabili:
{
  "dependencies": {
    "colors": "~1.4.0",   // Accetta 1.4.x >= 1.4.0 → installa 1.4.2
    "colors": ">=1.0.0",  // Accetta qualsiasi >= 1.0.0 → installa 1.4.2
    "colors": "latest",   // Sempre l'ultima → installa 1.4.2
    "colors": "*"          // Qualsiasi versione → installa 1.4.2
  }
}

// UNICA variante SICURA:
{
  "dependencies": {
    "colors": "1.4.0"     // Versione esatta, pinned
  }
}
```

Ma anche con versione pinned, senza lockfile la risoluzione delle sotto-dipendenze
può variare:

```bash
# Con lockfile (package-lock.json / yarn.lock / pnpm-lock.yaml):
# → Versione fissa, riproducibile, immune al sabotaggio
npm ci  # Installa da lockfile, NON da package.json

# Senza lockfile:
npm install  # Risolve da package.json, range semver → riceve versione sabotata
```

### Il problema delle dipendenze transitive

`colors.js` era una dipendenza transitiva di centinaia di pacchetti popolari:

```text
aws-cdk → @aws-cdk/core → colors → colors.js v1.4.2 (sabotata)
sentry-cli → @sentry/cli → colors → colors.js v1.4.2 (sabotata)
jest (alcune configurazioni) → ... → colors → colors.js v1.4.2 (sabotata)
```

Nessuno dei progetti intermedi aveva pinned la versione esatta di `colors.js`.
Questo significa che il sabotaggio ha impattato progetti che non sapevano nemmeno
di dipendere da `colors.js`.

---

## Root cause analysis

### Causa primaria

Un singolo maintainer con controllo esclusivo su un pacchetto critico
dell'ecosistema ha scelto deliberatamente di sabotare il proprio software.

### Cause contribuenti

| Causa | Dettaglio |
|-------|-----------|
| **Single-maintainer risk** | Un individuo controllava pacchetti con ~20M download settimanali combinati. Nessun meccanismo di governance, nessun co-maintainer con accesso. |
| **Mancanza di compenso strutturale** | Il maintainer non riceveva compenso adeguato nonostante il software generasse valore commerciale significativo per aziende Fortune 500. |
| **Semver ranges come default** | L'ecosistema npm incoraggia range come `^1.0.0` che accettano automaticamente nuove versioni minor/patch — il canale perfetto per propagare modifiche distruttive. |
| **Lockfile non universalmente adottato** | Molti progetti non committano o non usano lockfile, rendendoli vulnerabili a cambiamenti upstream. |
| **Nessuna review per pubblicazione** | npm non ha un meccanismo di review per versioni potenzialmente distruttive di pacchetti ad alta diffusione. |
| **Assenza di scoping dei permessi npm** | Un token npm con permesso di pubblicazione ha accesso illimitato — può pubblicare qualsiasi versione, incluse quelle distruttive. |

---

## Valutazione dell'impatto

### Impatto diretto

| Dimensione | Dettaglio |
|------------|-----------|
| **colors.js** | ~18M download settimanali al momento dell'incidente; dipendenza diretta o transitiva di migliaia di progetti |
| **faker.js** | ~2.5M download settimanali; usato estensivamente per testing e seeding di database |
| **Durata interruzione** | ~24-48 ore prima che npm revertisse la versione e i progetti aggiornassero i lockfile |
| **Progetti confermati impattati** | AWS CDK, Sentry CLI, vari tool CLI e build system |

### Impatto sull'ecosistema

- **Fiducia nel modello open source:** l'incidente ha dimostrato che la fiducia
  nel maintainer è il fondamento fragile su cui poggia l'intero ecosistema di
  pacchetti.
- **Dibattito sulla sostenibilità:** ha generato una conversazione globale sul
  modello economico dell'open source e sul fatto che infrastruttura critica
  dipende da volontari non compensati.
- **Fork community:** la nascita di `@faker-js/faker` come fork con governance
  multi-maintainer è diventata un modello di riferimento per la resilienza.

---

## Implicazioni per l'ecosistema Python

### Incidenti analoghi su PyPI

L'ecosistema Python soffre degli stessi problemi strutturali. Incidenti documentati:

#### Typosquatting: `request` vs `requests` (2022)

```bash
# Il pacchetto legittimo
pip install requests    # Kenneth Reitz, ~30M download/settimana

# Typosquat malevolo (rimosso)
pip install request     # Pacchetto malevolo con nome quasi identico
                        # Conteneva codice per esfiltrare variabili d'ambiente
```

#### Typosquatting: `colorama` (2023)

```bash
# Pacchetto legittimo
pip install colorama    # Output colorato per terminale, molto popolare

# Typosquat malevoli (rimossi)
pip install colourama   # Variante con spelling britannico
pip install coloramma   # Doppia 'm'
pip install colorsama   # Variante fonetica
# Contenevano codice per rubare variabili d'ambiente e credenziali browser
```

#### Malware su PyPI: campagne 2023-2024

```text
Esempi documentati:
- Pacchetti con nomi simili a librerie AI/ML popolari
- Pacchetti che impersonano tool DevOps
- Pacchetti che contengono codice di cryptomining
- Pacchetti che installano backdoor via setup.py
```

### Difese specifiche per Python

#### 1. Lockfile e versioni pinned

```bash
# PERICOLOSO — range semver / nessun pin
pip install requests>=2.0  # Installa qualsiasi versione >= 2.0

# SICURO — versione esatta con lockfile
# Con pip-tools
pip-compile requirements.in  # Genera requirements.txt con versioni esatte
pip install -r requirements.txt

# Con uv (raccomandato)
uv lock                      # Genera uv.lock con hash
uv sync                      # Installa da lockfile

# Con Poetry
poetry lock                  # Genera poetry.lock
poetry install               # Installa da lockfile
```

#### 2. Verifica integrità con hash

```bash
# requirements.txt con hash (pip-compile --generate-hashes)
requests==2.31.0 \
    --hash=sha256:58cd2187c01e70e6e26505bca751777aa9f2ee0b7f4300988b709f44e013003e

# pip verifica automaticamente l'hash al download
pip install --require-hashes -r requirements.txt
```

#### 3. pip-audit in CI

```yaml
# GitHub Actions — verifica CVE note nelle dipendenze
- name: Audit dependencies
  run: |
    pip install pip-audit
    pip-audit -r requirements.txt --strict

# Output di esempio per vulnerabilità trovata:
# Name    Version  ID              Fix Versions
# ------- -------- --------------- ------------
# django  3.2.0    CVE-2021-XXXXX  3.2.1
```

#### 4. PyPI Trusted Publishers (OIDC)

```yaml
# Pubblicazione sicura via GitHub Actions OIDC
# Elimina la necessità di token PyPI statici
# pyproject.toml non richiede modifiche

# .github/workflows/publish.yml
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # Richiesto per OIDC
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      - uses: pypa/gh-action-pypi-publish@release/v1
        # Nessun token necessario — autenticazione via OIDC
```

#### 5. Verificare la provenienza di un pacchetto

```bash
# Verificare chi pubblica un pacchetto
pip show requests
# ...
# Author: Kenneth Reitz
# Home-page: https://requests.readthedocs.io

# Verificare su PyPI
python -c "
import requests
r = requests.get('https://pypi.org/pypi/requests/json')
info = r.json()['info']
print(f'Author: {info[\"author\"]}')
print(f'Maintainer: {info[\"maintainer\"]}')
print(f'Project URL: {info[\"project_url\"]}')
"

# Verificare la storia delle release per anomalie
pip index versions requests
```

---

## Remediation — Azioni correttive

### Per progetti Node.js (contesto dell'incidente originale)

```bash
# 1. Verificare la versione attuale di colors.js
npm ls colors
# Se mostra 1.4.1 o 1.4.2 → impattato

# 2. Downgrade a versione sicura
npm install colors@1.4.0

# 3. Committare il lockfile aggiornato
git add package-lock.json
git commit -m "fix: pin colors.js a v1.4.0, evita sabotaggio v1.4.2"

# 4. Per faker.js — migrare al fork community
npm uninstall faker
npm install @faker-js/faker
# Aggiornare gli import:
# PRIMA: const faker = require('faker');
# DOPO:  const { faker } = require('@faker-js/faker');
```

### Per progetti Python (difesa preventiva)

```bash
# 1. Verificare dipendenze per CVE note
pip install pip-audit
pip-audit

# 2. Generare lockfile con hash
pip install pip-tools
pip-compile --generate-hashes requirements.in -o requirements.txt

# 3. Installare solo da lockfile in CI
pip install --require-hashes -r requirements.txt

# 4. Configurare scan automatico in CI
# Vedi sezione "pip-audit in CI" sopra

# 5. Verificare typosquatting nelle proprie dipendenze
# Controllare manualmente ogni pacchetto in requirements.txt
# confrontando con il nome ufficiale su pypi.org
```

---

## Risposta dell'industria

### Reazioni immediate

- **npm** ha revertito `colors.js` alla versione 1.4.0 e sospeso temporaneamente
  l'account di Squires.
- **GitHub** ha sospeso temporaneamente l'account GitHub di Squires (poi ripristinato).
- **Community fork:** `@faker-js/faker` è nato come fork con governance multi-maintainer
  e ha rapidamente superato l'originale in popolarità e funzionalità.

### Cambiamenti strutturali

| Area | Prima | Dopo |
|------|-------|------|
| **npm policy** | Nessun controllo su pubblicazioni potenzialmente distruttive | Introduzione di policy aggiuntive per pacchetti ad alta diffusione |
| **Governance open source** | Single-maintainer accettato come norma | Spinta verso governance multi-maintainer per progetti critici |
| **Funding** | Donazioni volontarie, sporadiche | Crescita di GitHub Sponsors, Tidelift, Open Collective; alcune aziende iniziano programmi strutturati |
| **Lockfile adoption** | Opzionale, spesso non committato | Best practice consolidata: committare sempre il lockfile |
| **PyPI** | Nessun meccanismo OIDC per pubblicazione | Lancio di Trusted Publishers (OIDC) nel 2023 |

### Il dibattito sulla sostenibilità

L'incidente ha cristallizzato una tensione fondamentale dell'open source:

```text
"Se il software open source è infrastruttura critica,
 chi paga per mantenerla?"

Modello attuale:
  Maintainer → lavoro gratuito → software critico → aziende Fortune 500 → miliardi di $
  Maintainer ← $0 (nella maggior parte dei casi)

Il paradosso:
  - Le aziende dipendono da software mantenuto da volontari
  - I volontari non hanno incentivi economici sostenibili
  - Un singolo volontario frustrato può impattare milioni di utenti
```

Proposte emerse dal dibattito:
1. **Corporate sponsorship strutturato** — le aziende che dipendono da un pacchetto
   contribuiscono proporzionalmente al valore che ne estraggono.
2. **Foundation model** — pacchetti critici migrati sotto fondazioni con governance
   multi-stakeholder (modello Linux Foundation / Apache Foundation).
3. **Licensing alternativo** — licenze che richiedono compenso per uso commerciale
   oltre una soglia (es. Business Source License, Fair Source).
4. **Attestation e provenienza** — rendere trasparente chi mantiene cosa e con
   quali risorse.

---

## Lezioni apprese

### 1. Single-maintainer è un single point of failure

Un individuo che controlla un pacchetto con milioni di download è un rischio
sistemico — che agisca per protesta, che venga compromesso da un attaccante,
o che semplicemente abbandoni il progetto.

### 2. Il lockfile è la prima difesa

```bash
# Senza lockfile: qualsiasi `npm install` / `pip install` può ricevere
# una versione sabotata pubblicata tra l'ultimo install e il corrente.

# Con lockfile: le versioni sono fissate. Solo un `npm update` / `uv lock`
# esplicito aggiorna le dipendenze.

# REGOLA: committare SEMPRE il lockfile nel repository.
```

### 3. Le dipendenze transitive sono il vero rischio

La maggior parte dei progetti impattati non sapeva nemmeno di dipendere da
`colors.js`. La dipendenza era transitiva, nascosta 2-3 livelli sotto nella
catena. Strumenti come `npm ls`, `pipdeptree`, `uv tree` rendono visibile
la catena completa.

### 4. La fiducia nel maintainer è il fondamento

Tutto il modello di sicurezza dei package registry si basa sulla fiducia nel
maintainer. Quando il maintainer è il threat actor, le difese tradizionali
(firma, CVE scanning) non servono — il codice è "legittimo" dal punto di
vista crittografico.

### 5. L'ecosistema Python non è immune

PyPI ha gli stessi problemi strutturali di npm: single maintainer, typosquatting,
assenza di review per pubblicazioni. Le difese (lockfile, hash verification,
pip-audit, Trusted Publishers) esistono ma non sono universalmente adottate.

---

## Checklist di prevenzione

### Per ogni progetto (npm e Python)

- [ ] Lockfile committato e aggiornato (`package-lock.json`, `uv.lock`, `poetry.lock`)
- [ ] CI installa da lockfile (`npm ci`, `uv sync`, `pip install --require-hashes`)
- [ ] Audit automatico in CI (`npm audit`, `pip-audit`)
- [ ] Dipendenze transitive visibili (`npm ls`, `pipdeptree`, `uv tree`)
- [ ] Nessun range aperto come `*`, `latest`, `>=1.0` in produzione
- [ ] Review periodica delle dipendenze dirette e transitive
- [ ] Alert configurati per nuove versioni di dipendenze critiche

### Per organizzazioni

- [ ] Policy sulle dipendenze: solo pacchetti con maintainer multipli per uso critico
- [ ] Registry privato (Artifactory, Nexus, Verdaccio) come proxy con caching
- [ ] Scan SCA (Software Composition Analysis) integrato nel pipeline
- [ ] Piano di fallback per pacchetti critici (fork pronti, alternative identificate)
- [ ] Contribuzione economica ai progetti open source da cui si dipende

### Per maintainer open source

- [ ] Governance multi-maintainer per progetti con alto numero di dipendenti
- [ ] Processo di release con review (branch protection, CI obbligatorio)
- [ ] Comunicazione trasparente sullo stato del progetto e le proprie intenzioni
- [ ] Considerare Trusted Publishers / OIDC per pubblicazione sicura

---

## Riferimenti

1. Issue originale di Marak Squires — "No more free work from Marak":
   `https://github.com/Marak/colors.js/issues/285`
2. colors.js commit del sabotaggio:
   `https://github.com/Marak/colors.js/commit/074a0c1b4c9e1b7e5c91f9a5c1c1f3a74e4e7b2d`
3. @faker-js/faker — fork community:
   `https://github.com/faker-js/faker`
4. Snyk — analisi dell'incidente colors.js:
   `https://snyk.io/blog/open-source-npm-packages-colors-702a/`
5. PyPI Trusted Publishers:
   `https://docs.pypi.org/trusted-publishers/`
6. pip-audit:
   `https://github.com/pypa/pip-audit`
7. Tidelift — State of the Open Source Maintainer Report:
   `https://tidelift.com/about/press`

---

## Cross-links

- Modulo 18 — `../18-sicurezza.md`.
- Modulo 24 — `../24-virtual-environments.md`.
- Modulo 32 — `../32-packaging-distribuzione.md`.
- Case Study correlato — `./log4shell-python-equivalent.md`.
