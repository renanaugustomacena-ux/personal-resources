---
corso: Programmazione Python
fase: 6 — DevOps e Distribuzione
modulo: "27"
versione: Python 3.12+
livello: intermedio-avanzato
prerequisiti:
  - completamento moduli 08 (testing) e 24 (virtual-environments)
  - familiarità con git e GitHub (corso 07)
  - conoscenza base di Docker (modulo 26)
obiettivi:
  - configurare pipeline CI/CD complete per progetti Python con GitHub Actions e GitLab CI
  - implementare matrix testing su Python 3.10-3.13 e sistemi operativi multipli
  - automatizzare la pubblicazione su PyPI via Trusted Publishers OIDC
  - integrare security scanning (pip-audit, bandit, safety) nella pipeline
  - configurare release automation con semantic-release e commitizen
  - implementare caching efficace per dipendenze uv/pip
  - gestire environment protection rules e approval gate per deployment in produzione
  - progettare workflow riutilizzabili e pattern CI per monorepo
tag:
  - ci-cd
  - github-actions
  - gitlab-ci
  - pypi
  - trusted-publishers
  - pre-commit
  - nox
  - tox
---

# CI/CD per Python — Guida Completa

> **Modulo 27** · **Aggiornamento:** 2026-05-24

> **Modulo del corso:** Programmazione Python
> **Prerequisiti:** [08-testing.md](08-testing.md), [24-virtual-environments.md](24-virtual-environments.md), [26-docker-per-python.md](26-docker-per-python.md)
> **Obiettivi di apprendimento:**
> 1. Configurare pipeline CI/CD complete per progetti Python con GitHub Actions e GitLab CI
> 2. Implementare matrix testing su Python 3.10-3.13 e OS multipli
> 3. Automatizzare la pubblicazione su PyPI via Trusted Publishers OIDC
> 4. Integrare security scanning (pip-audit, bandit, safety) nella pipeline
> 5. Configurare release automation con semantic-release e commitizen
> 6. Implementare caching efficace per dipendenze uv/pip
> 7. Gestire environment protection rules e approval gate per deployment in produzione
> **Tempo stimato:** lettura 60 min · lab 120 min
> **Livello:** intermedio-avanzato
> **Ultimo aggiornamento:** 2026-05-24

## Idee guida
1. **Pipeline standard: lint (ruff) + typecheck (mypy/pyright) + test (pytest) + audit (pip-audit).**
2. **uv lock + uv sync in CI per reproducibility.**
3. **PyPI publish via Trusted Publishers OIDC (no token).**
4. **Cache `~/.cache/uv` o pip cache.**


## Indice

1. [Panoramica](#panoramica)
2. [GitHub Actions per Python](#github-actions-per-python)
3. [uv nella CI](#uv-nella-ci)
4. [GitLab CI/CD per Python](#gitlab-cicd-per-python)
5. [Pre-commit Framework](#pre-commit-framework)
6. [Makefile per Python](#makefile-per-python)
7. [tox](#tox)
8. [Nox](#nox)
9. [Release Automation](#release-automation)
10. [Deployment Strategies](#deployment-strategies)
11. [Workflow Riutilizzabili](#workflow-riutilizzabili)
12. [Dependabot e Renovate](#dependabot-e-renovate)
13. [Branch Protection e Environment Rules](#branch-protection-e-environment-rules)
14. [Pattern CI per Monorepo](#pattern-ci-per-monorepo)
15. [Docker Multi-Stage Build per Python](#docker-multi-stage-build-per-python)
16. [CI/CD Security — SLSA e Sigstore](#cicd-security--slsa-e-sigstore)
17. [GitHub Actions Avanzate](#github-actions-avanzate)
18. [Troubleshooting CI/CD](#troubleshooting-cicd)
19. [Modello di Maturita CI/CD](#modello-di-maturita-cicd)
20. [Best Practices](#best-practices)
21. [Esercizi di Consolidamento](#esercizi-di-consolidamento)
22. [Letture e Riferimenti](#letture-e-riferimenti)
23. [Riferimenti Incrociati](#riferimenti-incrociati)
24. [Glossario](#glossario)

---

## Panoramica

CI/CD — Continuous Integration e Continuous Delivery (o Deployment) — rappresenta una delle pratiche fondamentali dell'ingegneria del software moderna. Per i progetti Python, adottare una pipeline CI/CD solida significa automatizzare tutto cio che va dalla verifica del codice alla pubblicazione in produzione, eliminando errori umani e accelerando il ciclo di rilascio.

La **Continuous Integration** si occupa di integrare frequentemente le modifiche nel repository condiviso. Ogni push o pull request attiva automaticamente una serie di controlli: il codice viene analizzato staticamente (linting), verificato con i type checker, sottoposto ai test automatizzati e compilato. Se uno qualunque di questi passaggi fallisce, lo sviluppatore riceve un feedback immediato e puo correggere il problema prima che raggiunga il branch principale.

La **Continuous Delivery** estende la CI automatizzando anche il processo di rilascio. Una volta che il codice supera tutti i controlli, viene impacchettato (wheel, sdist, Docker image) e pubblicato su un registry (PyPI, GHCR, un registry privato). La differenza con il Continuous Deployment e sottile: nella delivery il rilascio in produzione richiede un'approvazione manuale, nel deployment avviene automaticamente.

### Benefici per i progetti Python

I benefici dell'adozione di CI/CD nei progetti Python sono molteplici e concreti:

- **Feedback rapido** — gli errori vengono identificati entro minuti dal push, non giorni dopo durante una revisione manuale
- **Qualita costante** — ogni modifica passa attraverso gli stessi controlli, indipendentemente da chi la scrive
- **Compatibilita garantita** — il matrix testing verifica il funzionamento su diverse versioni di Python e sistemi operativi
- **Rilasci affidabili** — il processo di pubblicazione e automatizzato e ripetibile, eliminando il rischio di errori manuali
- **Sicurezza proattiva** — la scansione automatica delle dipendenze identifica vulnerabilita note prima che raggiungano la produzione
- **Documentazione vivente** — i file di configurazione della pipeline documentano implicitamente il processo di build e rilascio

### Stadi di una pipeline tipica

Una pipeline CI/CD per un progetto Python attraversa tipicamente questi stadi:

1. **Checkout** — il codice sorgente viene scaricato dal repository
2. **Setup ambiente** — viene configurata la versione di Python e l'environment manager
3. **Installazione dipendenze** — vengono installate le dipendenze del progetto e quelle di sviluppo
4. **Linting e formatting** — il codice viene analizzato staticamente per errori di stile e potenziali bug
5. **Type checking** — mypy verifica la correttezza dei type hint
6. **Testing** — pytest esegue la suite di test con raccolta della coverage
7. **Build** — il progetto viene impacchettato come wheel e sdist
8. **Security scanning** — le dipendenze vengono controllate per vulnerabilita note
9. **Publish** — il pacchetto viene pubblicato su PyPI o un registry privato
10. **Deploy** — il software viene distribuito in produzione

Non tutti i progetti richiedono tutti gli stadi. Un piccolo script di automazione potrebbe limitarsi a lint + test, mentre una libreria pubblica su PyPI necessita dell'intera pipeline. La chiave e partire semplici e aggiungere complessita man mano che il progetto cresce.

### Panorama degli strumenti

L'ecosistema CI/CD per Python e ricco di strumenti, ognuno con un ruolo specifico:

| Categoria | Strumenti | Ruolo |
|-----------|-----------|-------|
| Piattaforma CI | GitHub Actions, GitLab CI, CircleCI, Jenkins | Esecuzione della pipeline |
| Linting | Ruff, flake8, pylint | Analisi statica del codice |
| Formatting | Ruff formatter, Black | Formattazione automatica |
| Type checking | mypy, pyright, pytype | Verifica dei type hint |
| Testing | pytest, unittest, nox, tox | Esecuzione dei test |
| Coverage | coverage.py, pytest-cov | Misurazione della copertura |
| Build | build, setuptools, hatch | Costruzione dei pacchetti |
| Publish | twine, flit, gh-action-pypi-publish | Pubblicazione su registry |
| Security | pip-audit, safety, bandit, semgrep | Scansione vulnerabilita |
| Hooks | pre-commit | Controlli pre-commit |
| Release | python-semantic-release, commitizen | Automazione rilasci |

Questa guida si concentra su GitHub Actions come piattaforma CI/CD, essendo di gran lunga la piu utilizzata per i progetti Python open source e ampiamente adottata anche nel contesto aziendale. I concetti e le pratiche illustrate, tuttavia, sono trasferibili a qualsiasi altra piattaforma CI/CD con adattamenti minimi nella sintassi dei file di configurazione.

---

## GitHub Actions per Python

GitHub Actions e la piattaforma di CI/CD integrata in GitHub. Per i progetti Python e diventata lo standard de facto grazie all'integrazione nativa con il repository, l'ecosistema di action riutilizzabili e la generosita del piano gratuito (2.000 minuti al mese per repository pubblici, illimitati per i progetti open source).

I workflow vengono definiti in file YAML nella directory `.github/workflows/` del repository. Ogni workflow e composto da uno o piu job, e ogni job contiene una sequenza di step. I job girano su runner (macchine virtuali gestite da GitHub) con Ubuntu, macOS o Windows.

### Pipeline Base

Ecco un workflow completo che copre gli stadi fondamentali di una pipeline Python:

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  ci:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('**/requirements*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-${{ matrix.python-version }}-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint with ruff
        run: |
          ruff check .
          ruff format --check .

      - name: Type check with mypy
        run: mypy src/

      - name: Test with pytest
        run: pytest --cov=src --cov-report=xml --cov-report=term-missing

      - name: Build package
        run: |
          pip install build
          python -m build
```

### Matrix Testing

Il matrix testing e una delle funzionalita piu potenti di GitHub Actions. Permette di eseguire lo stesso job con combinazioni diverse di parametri, garantendo che il progetto funzioni su tutte le configurazioni supportate.

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.11", "3.12", "3.13"]
        exclude:
          # Esclude combinazioni problematiche
          - os: macos-latest
            python-version: "3.11"
        include:
          # Aggiungi configurazioni specifiche
          - os: ubuntu-latest
            python-version: "3.13"
            experimental: true

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest
```

La chiave `fail-fast: false` e importante: senza di essa, il fallimento di una combinazione cancellerebbe tutte le altre, impedendo di vedere il quadro completo delle compatibilita.

#### Gotcha YAML: versioni Python come float

Un errore comune e dimenticare le virgolette attorno alle versioni Python nel YAML:

```yaml
# SBAGLIATO — YAML interpreta 3.10 come float 3.1
matrix:
  python-version: [3.11, 3.12, 3.13]  # 3.10 diventa 3.1!

# CORRETTO — stringhe con virgolette
matrix:
  python-version: ["3.11", "3.12", "3.13"]
```

YAML interpreta numeri come `3.10` come il float `3.1`, causando l'installazione di Python 3.1 (inesistente) invece di 3.10. Questo e il bug piu comune nelle pipeline Python con matrix e genera errori criptici.

#### Matrici dinamiche

Per progetti che supportano molte versioni Python, la matrice puo essere generata dinamicamente leggendo le versioni da `pyproject.toml`:

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest
    outputs:
      python-versions: ${{ steps.versions.outputs.versions }}
    steps:
      - uses: actions/checkout@v4
      - id: versions
        run: |
          # Estrai le versioni supportate da pyproject.toml
          versions=$(python -c "
          import tomllib, json
          with open('pyproject.toml', 'rb') as f:
              data = tomllib.load(f)
          classifiers = data['project'].get('classifiers', [])
          versions = [c.split('::')[-1].strip()
                      for c in classifiers
                      if 'Programming Language :: Python ::' in c
                      and c.count('::') == 3]
          print(json.dumps(versions))
          ")
          echo "versions=$versions" >> "$GITHUB_OUTPUT"

  test:
    needs: prepare
    strategy:
      matrix:
        python-version: ${{ fromJson(needs.prepare.outputs.python-versions) }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: uv sync --frozen && uv run pytest
```

#### Ottimizzazione dei costi della matrice

Ogni combinazione della matrice crea un job separato, consumando minuti billabili. Strategie di ottimizzazione:

| Strategia | Risparmio | Trade-off |
|-----------|-----------|-----------|
| Ridurre gli OS a solo Linux per le PR, full matrix solo su `main` | ~60% | Bug OS-specifici scoperti tardi |
| Usare `include` per aggiungere solo combinazioni critiche | Variabile | Matrice meno completa |
| Eseguire matrix solo su file modificati (path filter) | ~40-70% | Falsa sicurezza se i filter sono troppo stretti |
| Separare lint (un solo Python) da test (matrix) | ~30% | Nessuno significativo |

```yaml
# Pattern: matrix ridotta per PR, completa per main
strategy:
  matrix:
    python-version: ${{ github.event_name == 'pull_request'
      && fromJson('["3.12"]')
      || fromJson('["3.11", "3.12", "3.13"]') }}
    os: ${{ github.event_name == 'pull_request'
      && fromJson('["ubuntu-latest"]')
      || fromJson('["ubuntu-latest", "macos-latest", "windows-latest"]') }}
```

### Caching delle dipendenze

Il caching riduce drasticamente i tempi della pipeline. Per un progetto con molte dipendenze, l'installazione puo richiedere diversi minuti; con la cache, scende a pochi secondi.

```yaml
# Cache per pip
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}

# Cache per Poetry
- uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pypoetry
      .venv
    key: ${{ runner.os }}-poetry-${{ hashFiles('poetry.lock') }}

# Cache nativa di setup-python (alternativa piu semplice)
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
    cache: "pip"  # oppure "poetry" o "pipenv"
```

#### Antipattern di caching comuni

La cache CI e una fonte frequente di bug silenziosi. Problemi tipici e soluzioni:

**Cache poisoning**: una cache corrotta causa fallimenti in tutti i job successivi. La chiave della cache deve includere il lock file esatto e la versione Python. Se la cache sembra corrotta, la soluzione e cambiare la `restore-keys` per invalidarla:

```yaml
# Aggiungere un suffisso di versione per invalidare la cache
key: ${{ runner.os }}-pip-v2-${{ hashFiles('requirements.txt') }}
#                         ^^ incrementare per invalidare
```

**Cache stale**: la cache contiene pacchetti vecchi che mascherano problemi. La `restore-keys` permette di usare cache parziali (prefix matching), ma questo puo portare a installare dipendenze obsolete. Per i rilasci critici, considerare l'opzione di disabilitare la cache per una build pulita.

**Cache troppo ampia**: cachare tutto `/home/runner` include file transitori che cambiano ad ogni run, causando miss continui. Cachare solo i path specifici del tool (es. `~/.cache/uv`, `~/.cache/pip`).

**Limiti di cache**: GitHub Actions ha un limite di 10 GB per repository. Le cache piu vecchie vengono eliminate automaticamente (FIFO). Per repository con molti branch e matrix testing, il limite puo essere raggiunto rapidamente. Strategia: usare `restore-keys` con prefix matching per condividere cache tra branch.

### Linting e Formatting

Il linting automatizzato nella CI garantisce che tutto il codice nel repository rispetti gli standard stabiliti dal team. Ruff e diventato lo strumento dominante nell'ecosistema Python grazie alla sua velocita eccezionale (scritto in Rust) e alla capacita di sostituire molteplici tool (flake8, isort, pyupgrade, ecc.).

```yaml
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install tools
        run: pip install ruff mypy

      - name: Ruff check (linting)
        run: ruff check . --output-format=github

      - name: Ruff format (formatting)
        run: ruff format --check .

      - name: Mypy (type checking)
        run: mypy src/ --strict

      # Alternativa: usare pre-commit nella CI
      - name: Run pre-commit
        uses: pre-commit/action@v3.0.1
```

L'opzione `--output-format=github` di Ruff e particolarmente utile: produce annotazioni inline direttamente nella pull request, mostrando gli errori di linting accanto alle righe di codice corrispondenti.

### Testing

Il testing nella CI va oltre la semplice esecuzione di pytest. Una pipeline matura include raccolta della coverage, reporting automatico e parallelizzazione dei test.

```yaml
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests with coverage
        run: |
          pytest \
            --cov=src \
            --cov-report=xml:coverage.xml \
            --cov-report=term-missing \
            --junitxml=test-results.xml \
            -n auto  # parallelizzazione con pytest-xdist

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
          token: ${{ secrets.CODECOV_TOKEN }}
          fail_ci_if_error: false

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: test-results.xml
```

Per aggiungere i risultati dei test come commenti nella pull request:

```yaml
      - name: Publish test results as PR comment
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: test-results.xml
```

La parallelizzazione con `pytest-xdist` (`-n auto`) distribuisce i test su tutti i core disponibili. Sul runner GitHub standard (2 core), il miglioramento e modesto; su runner piu grandi o self-hosted, il beneficio diventa significativo.

### Build e Publish

La pubblicazione su PyPI e il passo finale per le librerie Python. GitHub Actions supporta il meccanismo dei **trusted publishers** con OIDC (OpenID Connect), che elimina la necessita di gestire token API manualmente.

```yaml
  publish:
    needs: [lint, test]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')

    permissions:
      id-token: write  # necessario per OIDC trusted publishing

    environment:
      name: pypi
      url: https://pypi.org/project/mio-progetto/

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install build
        run: pip install build

      - name: Build wheel and sdist
        run: python -m build

      - name: Verify build
        run: |
          pip install twine
          twine check dist/*

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # Nessun token necessario con trusted publishers!
```

Per pubblicare su TestPyPI (utile per verificare il pacchetto prima del rilascio ufficiale):

```yaml
      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/
```

Per un registry privato (ad esempio un Artifactory aziendale o un DevPI locale):

```yaml
      - name: Publish to private registry
        run: |
          twine upload \
            --repository-url ${{ secrets.PRIVATE_REGISTRY_URL }} \
            --username ${{ secrets.REGISTRY_USER }} \
            --password ${{ secrets.REGISTRY_PASSWORD }} \
            dist/*
```

#### Configurazione step-by-step dei Trusted Publishers

Il meccanismo Trusted Publishers elimina completamente la gestione manuale di token API. Il flusso si basa su OIDC (OpenID Connect): GitHub Actions emette un token temporaneo che identifica univocamente il workflow, e PyPI lo verifica senza bisogno di credenziali statiche.

**Passo 1 — Configurare il Trusted Publisher su PyPI:**

1. Accedi a `pypi.org` e naviga al progetto → Settings → Publishing.
2. Clicca "Add a new publisher" e seleziona "GitHub Actions".
3. Compila i campi:
   - **Owner**: il proprietario del repository (es. `tuo-username`).
   - **Repository name**: il nome del repository (es. `mia-libreria`).
   - **Workflow name**: il nome esatto del file workflow (es. `release.yml`).
   - **Environment name** (opzionale ma raccomandato): `pypi`. Questo aggiunge un livello di protezione aggiuntivo.
4. Salva. Da questo momento, solo il workflow specificato puo pubblicare.

**Passo 2 — Configurare il workflow:**

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build && python -m build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      id-token: write        # FONDAMENTALE per OIDC
      contents: read
    environment:
      name: pypi              # Deve corrispondere alla configurazione su PyPI
      url: https://pypi.org/project/mia-libreria/
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
        # Nessun token, nessuna password — OIDC gestisce tutto
```

**Passo 3 — Proteggere con environment rules:**

Configurare l'environment `pypi` in Settings → Environments con:
- **Required reviewers**: almeno un approvatore prima della pubblicazione.
- **Wait timer**: opzionale, aggiunge un ritardo prima del deploy.
- **Deployment branches**: limitare ai tag (`refs/tags/v*`).

**Perche OIDC e superiore ai token API:**

| Aspetto | Token API | Trusted Publishers (OIDC) |
|---------|-----------|---------------------------|
| Credenziali memorizzate | Si (nei secrets GitHub) | No |
| Rischio di leak | Il token puo essere copiato o esposto | Nessun segreto da esporre |
| Rotazione | Manuale | Automatica (token temporanei) |
| Scope | Per-utente o per-progetto | Per-workflow e per-environment |
| Revoca | Manuale su PyPI | Basta rimuovere il publisher |
| Audit trail | Limitato | Completo (chi, quando, quale workflow) |

#### PyPI Attestations

A partire dal 2024, PyPI supporta le **attestazioni** (attestations) per i pacchetti pubblicati tramite Trusted Publishers. Le attestazioni sono prove crittografiche che legano un artefatto (wheel o sdist) al codice sorgente e al workflow che l'ha prodotto.

```yaml
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          attestations: true  # Genera attestazioni per ogni artefatto
```

Le attestazioni permettono agli utenti di verificare:
- Che il pacchetto e stato costruito dal repository dichiarato.
- Che il workflow specifico l'ha prodotto.
- Che il codice sorgente corrispondente e accessibile.

Verifica:
```bash
# Verifica attestazioni di un pacchetto (richiede pip 25+)
pip install --require-attestations mia-libreria

# O tramite l'API PyPI
curl https://pypi.org/simple/mia-libreria/ | grep "data-dist-info-metadata"
```

### Docker Build

La costruzione di immagini Docker nella CI e essenziale per i progetti che vengono distribuiti come container. GitHub Container Registry (GHCR) e la scelta naturale per i progetti su GitHub.

```yaml
  docker:
    needs: [test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v')

    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Set up QEMU (for multi-platform)
        uses: docker/setup-qemu-action@v3

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          platforms: linux/amd64,linux/arm64
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

La cache `type=gha` sfrutta la cache di GitHub Actions per i layer Docker, riducendo drasticamente i tempi di build successivi. Il supporto multi-piattaforma tramite QEMU permette di costruire immagini per architetture diverse (amd64 per server x86, arm64 per Apple Silicon e Graviton AWS).

### Security Scanning

La sicurezza nella pipeline CI/CD non e un optional. Le dipendenze Python, come in qualsiasi ecosistema, possono contenere vulnerabilita note. Automatizzare la scansione garantisce che nessuna vulnerabilita conosciuta raggiunga la produzione senza essere stata almeno identificata.

```yaml
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      # Scansione vulnerabilita dipendenze con pip-audit
      - name: Audit dependencies
        run: |
          pip install pip-audit
          pip install -r requirements.txt
          pip-audit

      # Analisi statica di sicurezza con Bandit
      - name: Security scan with Bandit
        run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json || true
          bandit -r src/ -ll  # mostra solo severity media e alta

      # Scanning con Semgrep (regole specifiche per Python)
      - name: Semgrep SAST
        uses: semgrep/semgrep-action@v1
        with:
          config: >-
            p/python
            p/security-audit
            p/secrets

      # Secret scanning (cerca credenziali nel codice)
      - name: Detect secrets
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified
```

`pip-audit` e lo strumento ufficiale raccomandato dalla Python Packaging Authority (PyPA) per la scansione delle vulnerabilita. Interroga il database di vulnerabilita OSV e PyPI per identificare dipendenze con CVE note. `safety` e un'alternativa popolare che utilizza un database proprietario di Safety (ex PyUp).

Bandit analizza il codice sorgente Python alla ricerca di pattern di sicurezza problematici: uso di `eval()`, password hardcoded, binding su tutte le interfacce di rete, uso di moduli crittografici deboli e molti altri pattern.

Semgrep e un motore di analisi statica piu avanzato che supporta regole personalizzate e ha un vasto catalogo di regole per Python, incluse regole specifiche per framework come Django e Flask.

#### Security scanning con uv

Quando si usa uv come package manager, la scansione delle vulnerabilita si integra direttamente:

```yaml
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5

      # pip-audit con uv
      - name: Audit dependencies
        run: |
          uv sync --frozen
          uv run pip-audit --require-hashes -r <(uv export --format requirements-txt --generate-hashes)

      # Bandit con uv
      - name: Security scan
        run: uv run --with bandit bandit -r src/ -ll -f json -o bandit-report.json

      # Upload report come artifact
      - name: Upload security reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            bandit-report.json
```

Il pattern `uv run --with bandit bandit` esegue bandit in un ambiente temporaneo senza doverlo aggiungere alle dipendenze del progetto. Questo mantiene le dipendenze di sviluppo pulite e garantisce che la versione di bandit usata in CI sia sempre la piu recente.

#### Confronto strumenti di security scanning

| Strumento | Tipo | Database | Costo | Velocita | Copertura |
|-----------|------|----------|-------|----------|-----------|
| **pip-audit** | Dipendenze | OSV + PyPI | Gratuito | Veloce | Vulnerabilita note |
| **safety** | Dipendenze | Safety DB | Free tier + paid | Veloce | Vulnerabilita note + consigli |
| **Bandit** | SAST (codice) | Regole built-in | Gratuito | Medio | Pattern di sicurezza Python |
| **Semgrep** | SAST (codice) | Community + Pro | Free tier + paid | Veloce | Multi-linguaggio, regole custom |
| **TruffleHog** | Secrets | N/A | Gratuito | Medio | Credenziali nel codice e nella storia git |
| **Snyk** | Dipendenze + SAST | Snyk DB | Free tier + paid | Medio | Ecosistema completo |

La raccomandazione minima per ogni progetto Python: **pip-audit** (dipendenze) + **bandit** (codice sorgente). Per progetti con requisiti di sicurezza elevati, aggiungere Semgrep e TruffleHog.

#### Scheduled security scans

Le scansioni di sicurezza non devono essere limitate ai push: le vulnerabilita vengono scoperte in continuazione. Una scansione periodica cattura CVE pubblicate dopo l'ultimo push:

```yaml
# .github/workflows/security-scan.yml
name: Weekly Security Scan

on:
  schedule:
    - cron: '0 6 * * 1'  # Ogni lunedi alle 6:00 UTC
  workflow_dispatch:       # Esecuzione manuale on-demand

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Audit dependencies
        run: |
          uv sync --frozen
          uv run pip-audit 2>&1 | tee audit-output.txt
          if grep -q "found" audit-output.txt; then
            echo "## Security Alert" >> "$GITHUB_STEP_SUMMARY"
            echo '```' >> "$GITHUB_STEP_SUMMARY"
            cat audit-output.txt >> "$GITHUB_STEP_SUMMARY"
            echo '```' >> "$GITHUB_STEP_SUMMARY"
          fi

      - name: Create issue on findings
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const output = fs.readFileSync('audit-output.txt', 'utf8');
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Security: vulnerabilita rilevate in dipendenze',
              body: `## Risultato scansione automatica\n\n\`\`\`\n${output}\n\`\`\`\n\nEseguita da: workflow security-scan`,
              labels: ['security', 'dependencies']
            });
```

Questo workflow crea automaticamente una issue GitHub quando vengono rilevate vulnerabilita, assicurando che il team sia notificato anche per i progetti con attivita di push ridotta.

---

## uv nella CI

uv e il package manager Python scritto in Rust da Astral (gli stessi creatori di Ruff). La sua velocita lo rende particolarmente adatto alla CI, dove ogni secondo di installazione dipendenze viene moltiplicato per il numero di job nella matrice. Un'installazione che con pip richiede 45 secondi, con uv si completa in 2-3 secondi.

### Setup base con uv

```yaml
# .github/workflows/ci.yml
name: CI (uv)

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  ci:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --frozen --dev

      - name: Lint
        run: |
          uv run ruff check .
          uv run ruff format --check .

      - name: Type check
        run: uv run mypy src/

      - name: Test
        run: uv run pytest --cov=src --cov-report=xml --cov-report=term-missing

      - name: Build
        run: uv build
```

Il flag `--frozen` e fondamentale in CI: impedisce a uv di aggiornare il lockfile, garantendo che vengano installate esattamente le versioni specificate in `uv.lock`. Senza questo flag, uv potrebbe risolvere nuove versioni delle dipendenze, creando inconsistenze tra l'ambiente locale dello sviluppatore e la CI.

### Cache uv

L'action `astral-sh/setup-uv` gestisce automaticamente il caching quando `enable-cache: true` e specificato. La cache include sia il download delle dipendenze sia gli ambienti virtuali compilati. La chiave della cache viene generata dal hash di `uv.lock` (o del glob specificato in `cache-dependency-glob`), garantendo che la cache venga invalidata quando le dipendenze cambiano.

Per un controllo piu granulare:

```yaml
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
          cache-dependency-glob: |
            uv.lock
            pyproject.toml
          cache-suffix: ${{ matrix.python-version }}
```

Il `cache-suffix` e utile nel matrix testing: crea una cache separata per ogni versione Python, evitando che la cache di Python 3.12 venga usata (e fallisca) per Python 3.13.

### Coverage enforcement con uv

Per garantire che la coverage non scenda sotto una soglia minima:

```yaml
      - name: Test with coverage enforcement
        run: |
          uv run pytest \
            --cov=src \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=80
```

Il flag `--cov-fail-under=80` fa fallire il job se la copertura totale scende sotto l'80%. Questo e preferibile rispetto a controllare la coverage come step separato perche integra il controllo direttamente nell'esecuzione dei test.

Per un controllo piu sofisticato, configura il file `.coveragerc` o la sezione `[tool.coverage]` in `pyproject.toml`:

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/migrations/*",
    "*/tests/*",
    "*/__main__.py",
]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "@overload",
    "raise NotImplementedError",
]
```

L'opzione `branch = true` attiva la branch coverage, che verifica non solo che ogni riga venga eseguita ma anche che ogni ramo condizionale (if/else) venga attraversato. La branch coverage e piu rigorosa della line coverage e cattura bug che la line coverage non vede.

#### Diff coverage — copertura solo sulle righe modificate

La diff coverage misura la copertura solo sulle righe di codice modificate nella PR, non su tutto il codebase. Questo e un indicatore piu utile per le code review: garantisce che il codice **nuovo** sia testato, senza penalizzare per il codice legacy non coperto.

```yaml
      - name: Test with coverage
        run: uv run pytest --cov=src --cov-report=xml

      - name: Diff coverage
        run: |
          uv run --with diff-cover diff-cover coverage.xml \
            --compare-branch=origin/main \
            --fail-under=90 \
            --markdown-report diff-cover.md

      - name: Post diff coverage to PR
        if: github.event_name == 'pull_request'
        run: |
          echo "## Diff Coverage" >> "$GITHUB_STEP_SUMMARY"
          cat diff-cover.md >> "$GITHUB_STEP_SUMMARY"
```

La soglia di diff coverage (90%) e volutamente piu alta della soglia globale (80%): il codice nuovo deve avere una copertura eccellente, mentre il debito tecnico esistente puo essere ridotto gradualmente.

#### Coverage badge

Per visualizzare la copertura nel README del progetto:

```yaml
      - name: Generate coverage badge
        if: github.ref == 'refs/heads/main'
        run: |
          COVERAGE=$(uv run coverage report --format=total)
          echo "Coverage: $COVERAGE%"
          # Genera il badge con shields.io
          curl -o badge.svg "https://img.shields.io/badge/coverage-${COVERAGE}%25-brightgreen"

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
          token: ${{ secrets.CODECOV_TOKEN }}
          fail_ci_if_error: false
```

Alternative a Codecov: **Coveralls**, **Code Climate**, o il semplice `coverage report --format=markdown` nel `GITHUB_STEP_SUMMARY` per chi non vuole servizi esterni.

### Pubblicazione su PyPI con uv

```yaml
  publish:
    needs: [ci]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    permissions:
      id-token: write
    environment:
      name: pypi
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

---

## GitLab CI/CD per Python

GitLab CI/CD e l'alternativa principale a GitHub Actions, particolarmente diffusa in contesti aziendali e self-hosted. La configurazione avviene tramite un file `.gitlab-ci.yml` nella root del repository.

### Pipeline base

```yaml
# .gitlab-ci.yml
image: python:3.12-slim

stages:
  - lint
  - test
  - build
  - security
  - publish

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  UV_CACHE_DIR: "$CI_PROJECT_DIR/.cache/uv"

cache:
  key:
    files:
      - uv.lock
    prefix: ${CI_JOB_NAME}
  paths:
    - .cache/pip
    - .cache/uv
    - .venv/

before_script:
  - pip install uv
  - uv sync --frozen --dev

lint:
  stage: lint
  script:
    - uv run ruff check .
    - uv run ruff format --check .
    - uv run mypy src/
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

test:
  stage: test
  parallel:
    matrix:
      - PYTHON_VERSION: ["3.11", "3.12", "3.13"]
  image: python:${PYTHON_VERSION}-slim
  script:
    - pip install uv
    - uv sync --frozen --dev
    - uv run pytest --cov=src --cov-report=xml --cov-report=term-missing --junitxml=report.xml
  coverage: '/(?i)total.*? (100(?:\.0+)?\%|[1-9]?\d(?:\.\d+)?\%)$/'
  artifacts:
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    when: always

build:
  stage: build
  script:
    - uv build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/

security:
  stage: security
  script:
    - pip install pip-audit bandit
    - pip install -r requirements.txt 2>/dev/null || true
    - pip-audit || true
    - bandit -r src/ -ll -f json -o bandit-report.json || true
  artifacts:
    reports:
      sast: bandit-report.json
    when: always
  allow_failure: true

publish-pypi:
  stage: publish
  script:
    - pip install twine
    - twine upload dist/*
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
  environment:
    name: pypi
    url: https://pypi.org/project/mio-progetto/
  variables:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: $PYPI_TOKEN
```

### Differenze chiave rispetto a GitHub Actions

| Aspetto | GitHub Actions | GitLab CI |
|---------|---------------|-----------|
| Configurazione | `.github/workflows/*.yml` (multipli file) | `.gitlab-ci.yml` (singolo file) |
| Runner | Hosted gratuiti (pubblici) o self-hosted | Self-hosted (gratuiti) o SaaS (a pagamento) |
| Cache | `actions/cache` o cache nativa | Cache nativa con chiavi e policy |
| Artifacts | `actions/upload-artifact` | `artifacts:` nativo con scadenza |
| Matrix | `strategy.matrix` | `parallel.matrix` |
| Environment protection | Environment con approval rules | Environment con approval rules |
| Secrets | Repository/org secrets | CI/CD Variables (protected/masked) |
| Container registry | GHCR (ghcr.io) | GitLab Container Registry integrato |
| Merge request pipeline | `on: pull_request` | `rules: - if: $CI_PIPELINE_SOURCE == "merge_request_event"` |

GitLab CI ha il vantaggio di un container registry integrato, pipeline visualization nativa e gestione degli environment piu granulare. GitHub Actions ha un ecosistema di action riutilizzabili enormemente piu vasto e un piano gratuito piu generoso per i progetti open source.

### GitLab CI con Docker

```yaml
build-docker:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG
  rules:
    - if: $CI_COMMIT_TAG
```

---

## Pre-commit Framework

pre-commit e un framework per la gestione e l'esecuzione di hook che vengono attivati prima di ogni commit Git. Funziona sia localmente sulla macchina dello sviluppatore sia nella pipeline CI, garantendo che il codice non conforme non raggiunga mai il repository.

### Configurazione

La configurazione avviene tramite il file `.pre-commit-config.yaml` nella root del progetto:

```yaml
# .pre-commit-config.yaml
repos:
  # Hook standard per file generici
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: debug-statements  # rileva print/pdb dimenticati

  # Ruff per linting e formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # Mypy per type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies:
          - types-requests
          - types-PyYAML

  # Controllo dipendenze
  - repo: https://github.com/Lucas-C/pre-commit-hooks-safety
    rev: v1.3.3
    hooks:
      - id: python-safety-dependencies-check
        files: requirements
```

Installazione e utilizzo:

```bash
# Installazione
pip install pre-commit

# Installazione degli hook nel repository
pre-commit install

# Esecuzione su tutti i file (non solo quelli modificati)
pre-commit run --all-files

# Aggiornamento delle versioni degli hook
pre-commit autoupdate
```

### Hook personalizzati

E possibile definire hook personalizzati per esigenze specifiche del progetto:

```yaml
  # Hook locale personalizzato
  - repo: local
    hooks:
      - id: check-migrations
        name: Check Django migrations
        entry: python manage.py makemigrations --check --dry-run
        language: system
        types: [python]
        pass_filenames: false

      - id: verify-version
        name: Verify version consistency
        entry: python scripts/check_version.py
        language: system
        pass_filenames: false
        files: '(pyproject\.toml|src/.*__version__.*)'
```

### Integrazione con la CI

Pre-commit nella CI funge da rete di sicurezza: anche se uno sviluppatore dimentica di installare gli hook localmente, la CI cattura comunque le violazioni.

```yaml
# .github/workflows/pre-commit.yml
name: Pre-commit

on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - uses: pre-commit/action@v3.0.1
```

L'action ufficiale `pre-commit/action` gestisce automaticamente il caching degli ambienti degli hook, rendendo le esecuzioni successive molto rapide.

### Ordine degli hook Ruff: lint prima di format

L'ordine degli hook nella configurazione e critico. Ruff fornisce due hook separati (`ruff` per il linting e `ruff-format` per la formattazione) e devono essere dichiarati nell'ordine corretto:

```yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      # 1. PRIMA il linting (con --fix per autofix)
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      # 2. POI la formattazione
      - id: ruff-format
```

**Perche questo ordine?** Il linter puo modificare il codice (rimuovere import inutilizzati, semplificare espressioni). Se la formattazione viene eseguita prima del lint, le modifiche del linter potrebbero rompere la formattazione. Eseguendo il lint prima, la formattazione ha l'ultima parola sul layout finale del codice.

Il flag `--exit-non-zero-on-fix` e importante: senza di esso, `ruff --fix` restituisce exit code 0 anche quando modifica file, e il commit procederebbe con file che lo sviluppatore non ha ancora rivisto. Con questo flag, il commit fallisce, lo sviluppatore vede le modifiche, le verifica con `git diff`, e fa un nuovo commit.

### pre-commit autoupdate e pinning

```bash
# Aggiorna tutti gli hook alle ultime versioni
pre-commit autoupdate

# Aggiorna solo un hook specifico
pre-commit autoupdate --repo https://github.com/astral-sh/ruff-pre-commit

# Mostra le versioni correnti
pre-commit autoupdate --dry-run
```

L'automazione degli aggiornamenti degli hook e delegabile a Dependabot o Renovate. Dependabot supporta nativamente `pre-commit` come ecosystem:

```yaml
# .github/dependabot.yml
updates:
  - package-ecosystem: "pre-commit"
    directory: "/"
    schedule:
      interval: "weekly"
    commit-message:
      prefix: "chore(hooks):"
```

### pre-commit.ci — CI dedicata per pre-commit

[pre-commit.ci](https://pre-commit.ci) e un servizio gratuito (per repository pubblici) che esegue gli hook di pre-commit come check CI e puo anche **autofix** le violazioni direttamente nella PR:

1. Installa l'app GitHub `pre-commit.ci` sul repository.
2. Aggiungi la configurazione nel file esistente:

```yaml
# .pre-commit-config.yaml (sezione ci in cima al file)
ci:
  autofix_prs: true           # Commit automatico dei fix nella PR
  autofix_commit_msg: "style: auto-fix pre-commit hooks"
  autoupdate_schedule: weekly  # Aggiornamento automatico delle rev
  autoupdate_commit_msg: "chore: update pre-commit hooks"
  skip: [mypy]                 # Hook da saltare in CI (mypy e lento)
```

Vantaggi di pre-commit.ci rispetto a eseguire pre-commit in GitHub Actions:
- **Autofix**: commita le correzioni direttamente nella PR, eliminando round-trip.
- **Cache ottimizzata**: ambienti degli hook cachati a livello di servizio, piu veloce della cache GitHub Actions.
- **Autoupdate**: aggiorna automaticamente le `rev` degli hook senza Dependabot.
- **Gratuito** per repository pubblici, con tempi di esecuzione generalmente inferiori.

Il trade-off e che mypy e hook pesanti sono meglio eseguiti nella pipeline principale con l'ambiente completo del progetto, dove le dipendenze e i type stubs sono disponibili.

---

## Makefile per Python

Il Makefile e uno strumento classico che mantiene la sua rilevanza nei progetti Python come interfaccia unificata per i comandi di sviluppo. Invece di ricordare lunghe righe di comando, il team usa target semplici come `make test` o `make lint`.

```makefile
# Makefile
.PHONY: help install install-dev test lint format build clean docker-build docker-run publish

PYTHON := python3
PACKAGE := mio_progetto
SRC_DIR := src
TEST_DIR := tests

help: ## Mostra questo messaggio di aiuto
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installa le dipendenze di produzione
	$(PYTHON) -m pip install --upgrade pip
	pip install -e .

install-dev: ## Installa le dipendenze di sviluppo
	$(PYTHON) -m pip install --upgrade pip
	pip install -e ".[dev]"
	pre-commit install

test: ## Esegui i test con coverage
	pytest $(TEST_DIR) \
		--cov=$(SRC_DIR)/$(PACKAGE) \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		-v

test-fast: ## Esegui i test senza coverage (veloce)
	pytest $(TEST_DIR) -x -q

lint: ## Esegui linting e type checking
	ruff check $(SRC_DIR) $(TEST_DIR)
	ruff format --check $(SRC_DIR) $(TEST_DIR)
	mypy $(SRC_DIR)

format: ## Formatta il codice automaticamente
	ruff check --fix $(SRC_DIR) $(TEST_DIR)
	ruff format $(SRC_DIR) $(TEST_DIR)

build: clean ## Costruisci wheel e sdist
	$(PYTHON) -m build
	twine check dist/*

clean: ## Rimuovi artefatti di build
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build: ## Costruisci immagine Docker
	docker build -t $(PACKAGE):latest .

docker-run: ## Esegui il container Docker
	docker run --rm -p 8000:8000 $(PACKAGE):latest

publish: build ## Pubblica su PyPI
	twine upload dist/*

publish-test: build ## Pubblica su TestPyPI
	twine upload --repository testpypi dist/*
```

### Alternativa: Justfile

`just` e un moderno sostituto di `make`, progettato specificamente come command runner (non come build system). La sintassi e piu leggibile e supporta nativamente parametri, variabili di ambiente e condizioni.

```just
# justfile
set dotenv-load

default:
    @just --list

package := "mio_progetto"
src_dir := "src"

install:
    python -m pip install --upgrade pip
    pip install -e ".[dev]"
    pre-commit install

test *args='':
    pytest tests/ --cov={{src_dir}}/{{package}} --cov-report=term-missing {{args}}

lint:
    ruff check {{src_dir}} tests/
    ruff format --check {{src_dir}} tests/
    mypy {{src_dir}}

format:
    ruff check --fix {{src_dir}} tests/
    ruff format {{src_dir}} tests/

build: clean
    python -m build
    twine check dist/*

clean:
    rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache

docker-build tag='latest':
    docker build -t {{package}}:{{tag}} .

publish: build
    twine upload dist/*
```

La differenza principale rispetto al Makefile e che `just` non ha il concetto di dipendenze tra file (non e un build system) ma offre una sintassi piu pulita e funzionalita come il passaggio di argomenti (`just test -k test_login`) e il caricamento automatico di file `.env`.

---

## tox

tox e lo strumento storico per il testing multi-ambiente in Python. La sua funzione principale e creare ambienti virtuali isolati per ogni configurazione di test, garantendo che i test non siano influenzati dall'ambiente di sviluppo locale.

### Configurazione

```ini
# tox.ini
[tox]
envlist = py311, py312, py313, lint, typecheck
min_version = 4.0
isolated_build = true

[testenv]
description = Esegui test con pytest
deps =
    pytest
    pytest-cov
    pytest-xdist
commands =
    pytest {posargs:tests/} --cov=src --cov-report=term-missing

[testenv:lint]
description = Esegui linting con ruff
skip_install = true
deps =
    ruff
commands =
    ruff check src/ tests/
    ruff format --check src/ tests/

[testenv:typecheck]
description = Type checking con mypy
deps =
    mypy
    types-requests
commands =
    mypy src/

[testenv:docs]
description = Costruisci la documentazione
deps =
    sphinx
    sphinx-rtd-theme
commands =
    sphinx-build -b html docs/ docs/_build/

[testenv:security]
description = Scansione di sicurezza
skip_install = true
deps =
    pip-audit
    bandit
commands =
    pip-audit
    bandit -r src/ -ll
```

Esecuzione:

```bash
# Esegui tutti gli ambienti
tox

# Esegui solo un ambiente specifico
tox -e py312

# Passa argomenti a pytest
tox -e py312 -- -k test_login -v

# Esegui in parallelo
tox -p auto

# Ricrea gli ambienti (utile dopo modifiche alle dipendenze)
tox -r
```

### Integrazione con GitHub Actions

Il pacchetto `tox-gh-actions` mappa automaticamente la versione di Python del runner all'ambiente tox corrispondente:

```ini
# tox.ini — sezione aggiuntiva
[gh-actions]
python =
    3.11: py311
    3.12: py312, lint, typecheck
    3.13: py313
```

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install tox tox-gh-actions
      - run: tox
```

In questo modo, quando la CI esegue il job con Python 3.12, tox esegue automaticamente gli ambienti `py312`, `lint` e `typecheck`. Con Python 3.11 o 3.13, esegue solo l'ambiente di test corrispondente. Questo evita di eseguire il linting e il type checking tre volte inutilmente.

---

## Nox

Nox e l'alternativa moderna a tox, sviluppata da un ingegnere di Google. La differenza fondamentale e che le sessioni vengono definite in Python puro anziche in un file di configurazione INI, offrendo tutta la flessibilita di un linguaggio di programmazione completo.

### Configurazione

```python
# noxfile.py
import nox

# Impostazioni globali
nox.options.sessions = ["lint", "tests"]
nox.options.reuse_existing_virtualenvs = True

PYTHON_VERSIONS = ["3.11", "3.12", "3.13"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Esegui la suite di test."""
    session.install(".[dev]")
    session.run(
        "pytest",
        "--cov=src",
        "--cov-report=term-missing",
        *session.posargs,
    )


@nox.session(python="3.12")
def lint(session: nox.Session) -> None:
    """Esegui linting e formatting check."""
    session.install("ruff")
    session.run("ruff", "check", "src/", "tests/")
    session.run("ruff", "format", "--check", "src/", "tests/")


@nox.session(python="3.12")
def typecheck(session: nox.Session) -> None:
    """Esegui type checking con mypy."""
    session.install(".", "mypy", "types-requests")
    session.run("mypy", "src/")


@nox.session(python="3.12")
def security(session: nox.Session) -> None:
    """Scansione di sicurezza."""
    session.install("pip-audit", "bandit")
    session.run("pip-audit")
    session.run("bandit", "-r", "src/", "-ll")


@nox.session(python="3.12")
def docs(session: nox.Session) -> None:
    """Costruisci la documentazione Sphinx."""
    session.install(".", "sphinx", "sphinx-rtd-theme")
    session.run("sphinx-build", "-b", "html", "docs/", "docs/_build/")
```

### Parametrize

La vera potenza di Nox emerge con la parametrizzazione, dove la logica Python permette combinazioni che sarebbero complesse in un file INI:

```python
@nox.session
@nox.parametrize("django", ["4.2", "5.0", "5.1"])
@nox.parametrize("database", ["sqlite", "postgresql"])
def test_django(session: nox.Session, django: str, database: str) -> None:
    """Testa con diverse versioni di Django e database."""
    session.install(f"django=={django}")

    if database == "postgresql":
        session.install("psycopg2-binary")

    session.run("pytest", "tests/", env={"DB_BACKEND": database})
```

Esecuzione:

```bash
# Esegui tutte le sessioni predefinite
nox

# Esegui una sessione specifica
nox -s tests

# Esegui con una versione Python specifica
nox -s tests-3.12

# Passa argomenti a pytest
nox -s tests -- -k test_login -v

# Lista tutte le sessioni disponibili
nox -l

# Esegui con parametri specifici
nox -s "test_django(django='5.1', database='postgresql')"
```

### Confronto con tox

La scelta tra tox e Nox dipende dalle esigenze del progetto:

| Aspetto | tox | Nox |
|---------|-----|-----|
| Configurazione | INI/TOML | Python |
| Flessibilita | Limitata | Completa |
| Curva di apprendimento | Bassa | Media |
| Adozione | Molto diffuso | In crescita |
| Parametrizzazione | Base | Avanzata |
| Integrazione CI | tox-gh-actions | Manuale |
| Riuso ambienti | Si | Si |

Per progetti semplici con requisiti standard, tox e perfettamente adeguato e la sua configurazione dichiarativa rende immediatamente chiaro cosa fa ogni ambiente. Per progetti complessi con logica condizionale nei test (diverse versioni di framework, database diversi, configurazioni platform-specific), Nox offre una flessibilita superiore grazie alla potenza espressiva di Python. Un esempio concreto: in tox, eseguire un comando solo su Linux richiede workaround con `platform` e condizioni limitate; in Nox, basta un `if sys.platform == "linux"` all'interno della funzione di sessione.

Un aspetto pratico da considerare e che tox ha un ecosistema di plugin piu maturo (tox-gh-actions, tox-docker, tox-conda) e una comunita piu ampia, il che si traduce in piu risposte su StackOverflow e piu esempi di configurazione disponibili. Nox, d'altra parte, non necessita di plugin per la maggior parte dei casi d'uso avanzati perche la logica puo essere scritta direttamente in Python.

Entrambi gli strumenti possono essere integrati nella CI. La differenza pratica e che con tox si usa il plugin `tox-gh-actions` per il mapping automatico delle versioni Python, mentre con Nox il mapping va gestito manualmente nel workflow YAML (specificando quale sessione eseguire per ogni versione Python nella matrice).

---

## Release Automation

L'automazione dei rilasci elimina uno dei processi piu soggetti a errori nello sviluppo software. Un rilascio manuale richiede di aggiornare la versione, generare il changelog, creare il tag, costruire il pacchetto, pubblicarlo su PyPI, creare la GitHub Release e possibilmente costruire e pubblicare l'immagine Docker. Automatizzare tutto questo riduce il rischio di dimenticare un passaggio o di commettere un errore.

### Semantic Versioning con python-semantic-release

`python-semantic-release` analizza i messaggi di commit che seguono la convenzione **Conventional Commits** per determinare automaticamente il prossimo numero di versione, generare il changelog e creare il rilascio.

Convenzione dei commit:

- `fix: correggi il parsing delle date` → **patch** (1.0.0 → 1.0.1)
- `feat: aggiungi supporto per export CSV` → **minor** (1.0.0 → 1.1.0)
- `feat!: cambia il formato dell'API di risposta` → **major** (1.0.0 → 2.0.0)
- `BREAKING CHANGE:` nel body del commit → **major**

Configurazione in `pyproject.toml`:

```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
version_variables = ["src/mio_progetto/__init__.py:__version__"]
branch = "main"
commit_message = "chore(release): {version}"
build_command = "python -m build"

[tool.semantic_release.changelog]
template_dir = "templates"
changelog_file = "CHANGELOG.md"

[tool.semantic_release.remote.token]
env = "GH_TOKEN"
```

Workflow GitHub Actions:

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [main]

permissions:
  contents: write
  id-token: write

jobs:
  release:
    runs-on: ubuntu-latest
    concurrency: release

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GH_TOKEN }}

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Semantic Release
        uses: python-semantic-release/python-semantic-release@v9
        with:
          github_token: ${{ secrets.GH_TOKEN }}
```

### Pipeline di rilascio manuale (tag-triggered)

Per i team che preferiscono il controllo manuale sul timing dei rilasci, una pipeline attivata dalla creazione di un tag Git e un'alternativa robusta:

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*.*.*'

permissions:
  contents: write
  packages: write
  id-token: write

jobs:
  # 1. Verifica che i test passino
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest

  # 2. Costruisci e pubblica su PyPI
  publish-pypi:
    needs: verify
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1

  # 3. Costruisci e pubblica immagine Docker
  publish-docker:
    needs: verify
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:${{ github.ref_name }}
            ghcr.io/${{ github.repository }}:latest
          platforms: linux/amd64,linux/arm64

  # 4. Crea la GitHub Release
  create-release:
    needs: [publish-pypi, publish-docker]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate changelog
        id: changelog
        run: |
          # Trova il tag precedente
          PREV_TAG=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "")
          if [ -z "$PREV_TAG" ]; then
            CHANGES=$(git log --pretty=format:"- %s" HEAD)
          else
            CHANGES=$(git log --pretty=format:"- %s" ${PREV_TAG}..HEAD)
          fi
          echo "changes<<EOF" >> $GITHUB_OUTPUT
          echo "$CHANGES" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          body: |
            ## Novita in ${{ github.ref_name }}

            ${{ steps.changelog.outputs.changes }}

            ### Installazione
            ```bash
            pip install mio-progetto==${{ github.ref_name }}
            ```

            ### Docker
            ```bash
            docker pull ghcr.io/${{ github.repository }}:${{ github.ref_name }}
            ```
          generate_release_notes: true
```

Il processo di rilascio manuale segue questi passi:

```bash
# 1. Aggiorna la versione in pyproject.toml
# 2. Crea il tag
git tag -a v1.2.0 -m "Release v1.2.0"
# 3. Pusha il tag (attiva la pipeline)
git push origin v1.2.0
```

---

## Deployment Strategies

Il deployment — la distribuzione del software in un ambiente di produzione — varia enormemente in base all'architettura del progetto. Un'applicazione web Django ha requisiti diversi da una CLI distribuita via PyPI, che a sua volta differisce da un servizio serverless. Questa sezione copre le strategie piu comuni.

Prima di scegliere una strategia, e fondamentale definire alcuni requisiti:

- **Zero-downtime deployment** — l'applicazione deve rimanere disponibile durante il rilascio?
- **Rollback** — quanto velocemente si deve poter tornare alla versione precedente in caso di problemi?
- **Ambienti multipli** — esiste una progressione staging → production?
- **Scalabilita** — il deployment deve gestire piu istanze dell'applicazione?
- **Conformita** — esistono requisiti normativi sul processo di rilascio (audit trail, approvazioni)?

Le risposte a queste domande guidano la scelta tra un semplice deployment SSH e un'orchestrazione Kubernetes completa.

### Deployment diretto (SSH/rsync)

La strategia piu semplice per server singoli. Adatta a piccoli progetti, applicazioni interne o ambienti dove non si utilizzano container. Il vantaggio principale e la semplicita: non richiede infrastruttura aggiuntiva. Lo svantaggio e la mancanza di zero-downtime deployment e la difficolta di gestire il rollback in modo affidabile.

```yaml
  deploy:
    needs: [test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_SSH_KEY }}
          script: |
            cd /opt/mio-progetto
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            python manage.py migrate
            sudo systemctl restart mio-progetto
```

Per un approccio piu sofisticato con rsync (trasferimento solo dei file modificati):

```yaml
      - name: Deploy via rsync
        uses: burnett01/rsync-deployments@v7
        with:
          switches: -avzr --delete --exclude='.env' --exclude='venv/'
          path: .
          remote_path: /opt/mio-progetto/
          remote_host: ${{ secrets.DEPLOY_HOST }}
          remote_user: ${{ secrets.DEPLOY_USER }}
          remote_key: ${{ secrets.DEPLOY_SSH_KEY }}
```

### Deployment Docker-based

Quando il progetto e containerizzato, il deployment consiste nel pullare la nuova immagine e riavviare il servizio. Questa strategia offre diversi vantaggi rispetto al deployment diretto: l'immagine Docker e immutabile (cio che funziona in staging funzionera in produzione), il rollback e istantaneo (basta riavviare con l'immagine precedente) e l'ambiente di runtime e completamente isolato dal sistema host.

```yaml
      - name: Deploy Docker
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_SSH_KEY }}
          script: |
            docker pull ghcr.io/${{ github.repository }}:latest
            docker compose -f /opt/app/docker-compose.yml up -d --no-deps app
            docker image prune -f
```

### Deployment Kubernetes

Per architetture piu complesse che richiedono scaling automatico, alta disponibilita e gestione avanzata del traffico, Kubernetes e la soluzione standard dell'industria. Il deployment su Kubernetes offre rolling updates (aggiornamento graduale dei pod senza downtime), health checks automatici, rollback automatico in caso di fallimento e scaling orizzontale basato sul carico.

```yaml
  deploy-k8s:
    needs: [publish-docker]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/setup-kubectl@v4

      - name: Set Kubernetes context
        uses: azure/k8s-set-context@v4
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG }}

      - name: Update deployment image
        run: |
          kubectl set image deployment/mio-progetto \
            app=ghcr.io/${{ github.repository }}:${{ github.sha }} \
            -n production
          kubectl rollout status deployment/mio-progetto -n production
```

### Serverless (AWS Lambda)

Python e uno dei linguaggi piu usati per le funzioni Lambda grazie alla sua velocita di cold start relativamente bassa e alla ricchezza dell'ecosistema di librerie. Il modello serverless elimina completamente la gestione dell'infrastruttura: non ci sono server da mantenere, il scaling e automatico e si paga solo per il tempo di esecuzione effettivo. Il deployment puo essere gestito tramite AWS SAM (Serverless Application Model) o il Serverless Framework:

```yaml
  deploy-lambda:
    needs: [test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - uses: aws-actions/setup-sam@v2
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: eu-west-1

      - name: Build and deploy
        run: |
          sam build
          sam deploy --no-confirm-changeset --no-fail-on-empty-changeset
```

### Deployment su piattaforme PaaS

Le piattaforme Platform-as-a-Service offrono il deployment piu semplice, ideale per prototipi e applicazioni di medie dimensioni.

**Railway:**

```yaml
  deploy-railway:
    needs: [test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: railwayapp/nixpacks@v1
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: mio-progetto
```

**Render:**

Render supporta il deploy automatico connettendo il repository GitHub direttamente dalla dashboard. Per un controllo piu granulare tramite la CI:

```yaml
  deploy-render:
    needs: [test]
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render deploy
        run: |
          curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}"
```

**Heroku:**

```yaml
  deploy-heroku:
    needs: [test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: akhileshns/heroku-deploy@v3.13.15
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: mio-progetto
          heroku_email: ${{ secrets.HEROKU_EMAIL }}
```

La scelta della piattaforma dipende da molteplici fattori: costo, regione geografica, requisiti di compliance, stack tecnologico e competenze del team. Le piattaforme PaaS sono eccellenti per iniziare rapidamente, ma possono diventare costose e limitanti al crescere del progetto. Kubernetes offre il massimo controllo ma richiede competenze specialistiche significative.

### Confronto strategie di deployment

| Strategia | Zero-downtime | Rollback | Complessita | Caso d'uso |
|-----------|---------------|----------|-------------|------------|
| SSH/rsync | No | Manuale (lento) | Minima | Server singolo, progetti interni |
| Docker pull + restart | Parziale | Veloce (immagine precedente) | Bassa | Piccoli team, server singolo |
| Docker Compose rolling | Si | Veloce | Media | Servizi multipli, server singolo |
| Kubernetes rolling update | Si | Automatico | Alta | Microservizi, alta disponibilita |
| Blue/Green | Si | Istantaneo (switch) | Media-alta | Requisiti zero-downtime stretti |
| Canary | Si | Graduale | Alta | Rilasci ad alto rischio |
| PaaS (Railway/Render) | Si | Veloce (dashboard) | Minima | Prototipi, startup, MVP |
| Serverless | N/A | Per-invocazione | Media | Event-driven, API leggere |

### Blue/Green deployment

Il deployment blue/green mantiene due ambienti identici: uno attivo (blue, che serve il traffico) e uno inattivo (green, dove si installa la nuova versione). Dopo la verifica sul green, il traffico viene rediretto dal blue al green in un singolo passaggio. Se qualcosa va storto, il rollback e istantaneo: basta redirigere il traffico al blue.

```yaml
  deploy-blue-green:
    needs: [test, publish-docker]
    runs-on: ubuntu-latest
    environment:
      name: production
    steps:
      - uses: actions/checkout@v4
      - name: Determine active environment
        id: active
        run: |
          # Verifica quale ambiente e attivo leggendo un tag/label
          ACTIVE=$(curl -s https://api.example.com/deployment/active)
          if [ "$ACTIVE" = "blue" ]; then
            echo "target=green" >> "$GITHUB_OUTPUT"
          else
            echo "target=blue" >> "$GITHUB_OUTPUT"
          fi

      - name: Deploy to inactive environment
        run: |
          TARGET=${{ steps.active.outputs.target }}
          ssh deploy@${{ secrets.DEPLOY_HOST }} \
            "cd /opt/$TARGET && docker compose pull && docker compose up -d"

      - name: Health check on new environment
        run: |
          TARGET=${{ steps.active.outputs.target }}
          for i in $(seq 1 10); do
            if curl -sf "https://$TARGET.example.com/health"; then
              echo "Health check passed"
              exit 0
            fi
            sleep 5
          done
          echo "Health check failed"
          exit 1

      - name: Switch traffic
        if: success()
        run: |
          # Aggiorna il reverse proxy/load balancer
          TARGET=${{ steps.active.outputs.target }}
          ssh deploy@${{ secrets.DEPLOY_HOST }} \
            "update-upstream --target $TARGET && nginx -s reload"
```

### Canary deployment

Il canary deployment instrada una percentuale ridotta del traffico (tipicamente 1-10%) alla nuova versione, monitorando metriche chiave (latenza, tasso di errore, CPU). Se le metriche rimangono nella norma, la percentuale viene aumentata gradualmente fino al 100%. Se si rilevano anomalie, tutto il traffico torna alla versione precedente.

Questo pattern richiede un load balancer con supporto al traffic splitting (nginx con upstream weights, AWS ALB con target groups, Istio su Kubernetes) e un sistema di monitoraggio per le metriche di confronto.

```yaml
  deploy-canary:
    needs: [test, publish-docker]
    runs-on: ubuntu-latest
    environment:
      name: production
    steps:
      - name: Deploy canary (5% traffic)
        run: |
          ssh deploy@${{ secrets.DEPLOY_HOST }} << 'EOF'
            docker pull ghcr.io/${{ github.repository }}:${{ github.sha }}
            docker run -d --name canary \
              -e CANARY=true \
              ghcr.io/${{ github.repository }}:${{ github.sha }}
            # Configura nginx per 5% al canary
            sed -i 's/weight=0/weight=5/' /etc/nginx/conf.d/upstream.conf
            sed -i 's/weight=100/weight=95/' /etc/nginx/conf.d/upstream.conf
            nginx -s reload
          EOF

      - name: Monitor canary (10 minutes)
        run: |
          # Verifica metriche per 10 minuti
          for i in $(seq 1 20); do
            ERROR_RATE=$(curl -s https://metrics.example.com/api/v1/query \
              --data-urlencode 'query=rate(http_errors{canary="true"}[1m])' \
              | jq '.data.result[0].value[1] // "0"' -r)
            if (( $(echo "$ERROR_RATE > 0.05" | bc -l) )); then
              echo "Canary error rate too high: $ERROR_RATE"
              exit 1
            fi
            sleep 30
          done
          echo "Canary stable"

      - name: Promote canary to full
        if: success()
        run: |
          ssh deploy@${{ secrets.DEPLOY_HOST }} << 'EOF'
            # Aggiorna l'istanza principale
            docker compose pull && docker compose up -d
            # Rimuovi il canary
            docker stop canary && docker rm canary
            # Ripristina i pesi
            sed -i 's/weight=5/weight=0/' /etc/nginx/conf.d/upstream.conf
            sed -i 's/weight=95/weight=100/' /etc/nginx/conf.d/upstream.conf
            nginx -s reload
          EOF

      - name: Rollback canary
        if: failure()
        run: |
          ssh deploy@${{ secrets.DEPLOY_HOST }} << 'EOF'
            docker stop canary && docker rm canary
            sed -i 's/weight=5/weight=0/' /etc/nginx/conf.d/upstream.conf
            sed -i 's/weight=95/weight=100/' /etc/nginx/conf.d/upstream.conf
            nginx -s reload
          EOF
```

---

## Modello di Maturita CI/CD

La maturita di una pipeline CI/CD non e binaria. Il percorso da "nessun CI" a "pipeline completa con deploy automatico" e graduale. Questa tabella descrive i livelli tipici e le azioni per progredire:

| Livello | Nome | Caratteristiche | Azione per avanzare |
|---------|------|-----------------|---------------------|
| **0** | Nessuna CI | Nessun controllo automatico. Test ed build manuali. | Aggiungere un workflow minimo: checkout + pytest |
| **1** | CI base | Lint + test su push/PR. Un solo Python, un solo OS. | Aggiungere matrix testing, caching, branch protection |
| **2** | CI robusta | Matrix testing, caching, pre-commit, coverage enforcement. Branch protection attiva. | Aggiungere security scanning, CD automatico |
| **3** | CI/CD automatico | Build + publish automatici su tag. Trusted Publishers. Dependabot/Renovate. | Aggiungere SLSA provenance, diff coverage, environments |
| **4** | CI/CD maturo | SLSA Level 2+, attestazioni, monitoring in CI, deployment progressivo (canary/blue-green). Pipeline documentata, tempi <10min. | Ottimizzare, ridurre debito tecnico, self-hosted runner se necessario |

La maggior parte dei progetti open source raggiunge il livello 2 senza sforzo significativo. Il livello 3 richiede un investimento iniziale per configurare Trusted Publishers e l'automazione dei rilasci, ma una volta configurato richiede manutenzione minima. Il livello 4 e tipico di team professionali con requisiti di sicurezza e affidabilita elevati.

**Raccomandazione pratica:** non tentare di implementare tutto in una volta. Inizia dal livello 1, stabilizza la pipeline, poi procedi al livello successivo quando il team ha familiarizzato con gli strumenti. Ogni livello dovrebbe essere consolidato prima di procedere al successivo.

---

## Best Practices

Le best practice per CI/CD nei progetti Python derivano da anni di esperienza collettiva della comunita. Non sono regole rigide ma linee guida che, se seguite, riducono significativamente i problemi.

**1. Mantieni la pipeline veloce.** Una pipeline CI che impiega 20 minuti scoraggia il push frequente e rallenta il feedback loop. Obiettivo: meno di 10 minuti per la pipeline completa. Usa il caching aggressivamente, parallelizza i job indipendenti (lint e test possono girare contemporaneamente), ed evita di ripetere lavoro gia fatto. Se i test richiedono troppo tempo, considera di suddividerli in una suite veloce (eseguita su ogni push) e una suite completa (eseguita solo sui merge al branch principale).

**2. Usa il matrix testing in modo strategico.** Testare su 3 versioni di Python e 3 sistemi operativi genera 9 job. Se ciascuno richiede 5 minuti, il tempo totale e comunque 5 minuti (i job girano in parallelo), ma il consumo di minuti di CI e 45 minuti. Per i progetti open source con minuti illimitati questo non e un problema, ma per repository privati conviene essere selettivi. Testa su tutte le versioni Python supportate ma limita i test multi-OS ai rilasci o al branch principale.

**3. Pinning delle dipendenze nella CI.** Le dipendenze non pinnate (`pip install ruff`) possono causare fallimenti imprevisti quando viene rilasciata una nuova versione con breaking changes. Pinna le versioni degli strumenti di CI (`ruff==0.8.4`) o, meglio ancora, usa pre-commit che gestisce il versioning degli hook automaticamente. Per le action di GitHub, usa il SHA completo del commit anziche il tag della versione per maggiore sicurezza (`uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11` anziche `@v4`).

**4. Separa i job per responsabilita.** Non mettere linting, testing, building e deployment in un unico job monolitico. Separandoli, puoi vedere immediatamente quale fase e fallita, riavviare solo la fase fallita, e far girare le fasi indipendenti in parallelo. Usa `needs:` per definire le dipendenze tra job (il deploy dipende dal test, il publish dipende dal build).

**5. Proteggi i secrets e usa i permessi minimi.** Ogni workflow dovrebbe dichiarare esplicitamente i permessi necessari con la chiave `permissions`. Il principio del minimo privilegio si applica anche alla CI: se un job ha bisogno solo di leggere il codice, non dargli permessi di scrittura. I secrets non devono mai apparire nei log; GitHub li maschera automaticamente, ma fai attenzione ai comandi che potrebbero stamparli indirettamente (ad esempio `env` o `printenv`).

**6. Implementa la protezione dei branch.** Configura le branch protection rules per richiedere che tutti i check CI passino prima di poter fare il merge. Questo garantisce che nessun codice rotto raggiunga il branch principale. Richiedi almeno: check di linting, suite di test completa e una revisione approvata. Abilita anche l'opzione "Require branches to be up to date before merging" per evitare che un merge introduca incompatibilita con modifiche recenti.

**7. Automatizza tutto cio che e ripetitivo.** Se un'operazione viene eseguita piu di due volte manualmente, vale la pena automatizzarla. Questo include non solo il testing e il deployment, ma anche la generazione del changelog, l'aggiornamento delle dipendenze (Dependabot, Renovate), il labeling automatico delle pull request e la chiusura delle issue stale. Ogni operazione manuale e un'opportunita per un errore e un costo in termini di tempo dello sviluppatore.

**8. Testa la pipeline stessa.** La pipeline CI/CD e codice come qualsiasi altro, e come tale puo contenere bug. Quando modifichi un workflow, verifica che funzioni correttamente. Per le modifiche complesse, usa `act` (https://github.com/nektos/act) per eseguire i workflow localmente prima di pusharli. Mantieni un workflow di test minimale che viene eseguito su ogni push per verificare che la configurazione di base funzioni.

**9. Monitora i tempi e i costi della CI.** GitHub fornisce metriche sui tempi di esecuzione dei workflow. Monitora questi dati nel tempo: se la pipeline rallenta gradualmente, intervenire presto e piu facile che affrontare il problema quando e diventato critico. Per i repository privati, tieni d'occhio il consumo di minuti per evitare sorprese nella fatturazione. Considera l'uso di runner self-hosted per i progetti con esigenze elevate di CI.

**10. Documenta il processo di rilascio.** Anche con l'automazione completa, il team deve sapere come funziona il processo di rilascio: come si attiva un rilascio, cosa succede in caso di errore, come si esegue un rollback, chi ha i permessi per approvare un deploy in produzione. Questa documentazione deve vivere accanto al codice (un file `RELEASING.md` nella root del progetto) e deve essere aggiornata ogni volta che il processo cambia. Una pipeline automatizzata senza documentazione e una scatola nera che diventa un rischio quando l'unica persona che la capisce non e disponibile.

---

## Workflow Riutilizzabili

I workflow riutilizzabili (reusable workflows) di GitHub Actions permettono di definire una pipeline una volta e richiamarla da piu repository. Questo e particolarmente utile per le organizzazioni con molti progetti Python che condividono la stessa struttura CI.

### Definizione del workflow riutilizzabile

```yaml
# .github/workflows/reusable-python-ci.yml (nel repository template)
name: Reusable Python CI

on:
  workflow_call:
    inputs:
      python-versions:
        description: "Versioni Python da testare (JSON array)"
        type: string
        default: '["3.12", "3.13"]'
      coverage-threshold:
        description: "Soglia minima di coverage"
        type: number
        default: 80
      run-security-scan:
        description: "Eseguire la scansione di sicurezza"
        type: boolean
        default: true
      src-dir:
        description: "Directory del codice sorgente"
        type: string
        default: "src"
    secrets:
      CODECOV_TOKEN:
        required: false

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
      - run: uv sync --frozen --dev
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy ${{ inputs.src-dir }}/

  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ${{ fromJson(inputs.python-versions) }}
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
          cache-suffix: ${{ matrix.python-version }}
      - run: uv python install ${{ matrix.python-version }}
      - run: uv sync --frozen --dev
      - run: |
          uv run pytest \
            --cov=${{ inputs.src-dir }} \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=${{ inputs.coverage-threshold }}

  security:
    if: inputs.run-security-scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
      - run: uv sync --frozen --dev
      - run: uv run pip-audit
      - run: uv run bandit -r ${{ inputs.src-dir }}/ -ll
```

### Utilizzo da un altro repository

```yaml
# .github/workflows/ci.yml (nel repository consumer)
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  ci:
    uses: mia-org/shared-workflows/.github/workflows/reusable-python-ci.yml@main
    with:
      python-versions: '["3.11", "3.12", "3.13"]'
      coverage-threshold: 85
      src-dir: "src"
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

### Composite Actions

Per condividere singoli step (anziche interi workflow), le composite actions sono piu appropriate:

```yaml
# .github/actions/python-setup/action.yml
name: Python Setup
description: "Setup Python con uv e dipendenze"

inputs:
  python-version:
    description: "Versione Python"
    required: false
    default: "3.12"

runs:
  using: composite
  steps:
    - uses: astral-sh/setup-uv@v4
      with:
        enable-cache: true
        cache-suffix: ${{ inputs.python-version }}

    - run: uv python install ${{ inputs.python-version }}
      shell: bash

    - run: uv sync --frozen --dev
      shell: bash
```

Utilizzo:

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: ./.github/actions/python-setup
    with:
      python-version: "3.13"
  - run: uv run pytest
```

---

## Dependabot e Renovate

L'aggiornamento automatico delle dipendenze e un pilastro della sicurezza e della manutenibilita. Dipendenze obsolete accumulano vulnerabilita note, e l'aggiornamento manuale e un compito che viene sistematicamente procrastinato fino a diventare un'operazione rischiosa e complessa.

### Dependabot

Dependabot e integrato nativamente in GitHub e crea pull request automatiche quando sono disponibili aggiornamenti per le dipendenze.

```yaml
# .github/dependabot.yml
version: 2

updates:
  # Dipendenze Python (pip/uv)
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "Europe/Rome"
    open-pull-requests-limit: 10
    reviewers:
      - "team-backend"
    labels:
      - "dependencies"
      - "python"
    commit-message:
      prefix: "chore(deps):"
    groups:
      # Raggruppa aggiornamenti minori e patch
      minor-and-patch:
        update-types:
          - "minor"
          - "patch"
      # Aggiornamenti di sicurezza sempre separati
    ignore:
      # Ignora aggiornamenti major per librerie critiche
      - dependency-name: "django"
        update-types: ["version-update:semver-major"]

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    commit-message:
      prefix: "ci(deps):"

  # Docker
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "monthly"
    commit-message:
      prefix: "chore(docker):"
```

### Renovate

Renovate e un'alternativa piu potente e configurabile di Dependabot, disponibile per GitHub, GitLab, Bitbucket e altri. La differenza principale e la capacita di raggruppare gli aggiornamenti in modo piu intelligente, il supporto per monorepo, e la possibilita di auto-merge degli aggiornamenti di patch che passano la CI.

```json5
// renovate.json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    ":semanticCommits",
    ":automergeMinor",
    "group:allNonMajor"
  ],
  "python": {
    "enabled": true
  },
  "pip_requirements": {
    "fileMatch": ["requirements.*\\.txt$"]
  },
  "packageRules": [
    {
      "matchManagers": ["pip_requirements", "pep621"],
      "matchUpdateTypes": ["patch"],
      "automerge": true,
      "automergeType": "pr",
      "requiredStatusChecks": ["ci"]
    },
    {
      "matchManagers": ["pip_requirements"],
      "matchUpdateTypes": ["major"],
      "labels": ["breaking-change"],
      "automerge": false
    },
    {
      "matchPackageNames": ["ruff", "mypy", "pytest"],
      "groupName": "dev-tools",
      "schedule": ["before 8am on monday"]
    }
  ],
  "lockFileMaintenance": {
    "enabled": true,
    "schedule": ["before 5am on the first day of the month"]
  }
}
```

### Confronto

| Aspetto | Dependabot | Renovate |
|---------|-----------|----------|
| Setup | Zero (nativo GitHub) | App da installare |
| Raggruppamento | Basico (gruppi manuali) | Avanzato (pattern, regex) |
| Auto-merge | No (richiede workflow esterno) | Si (nativo) |
| Monorepo | Limitato | Eccellente |
| Piattaforme | Solo GitHub | GitHub, GitLab, Bitbucket, Azure |
| Personalizzazione | Moderata | Molto estesa |
| Lock file | Si | Si + manutenzione automatica |

Per progetti semplici su GitHub, Dependabot e sufficiente e non richiede configurazione aggiuntiva. Per organizzazioni con molti repository, monorepo o esigenze di auto-merge, Renovate offre una flessibilita superiore.

### Supporto uv.lock e pyproject.toml

**Dependabot** al momento (2025) supporta `requirements.txt`, `Pipfile.lock`, `poetry.lock` e `pyproject.toml` (PEP 621). Il supporto per `uv.lock` nativo non e ancora disponibile; come workaround, si usa `uv export` nella CI per generare `requirements.txt` e monitorare quelli.

**Renovate** offre supporto piu ampio:
- `pyproject.toml` (PEP 621 + Poetry + PDM).
- `requirements*.txt` (qualsiasi pattern via `fileMatch`).
- `uv.lock` tramite il manager `uv` (sperimentale, in fase di stabilizzazione).
- `.pre-commit-config.yaml` per hook pre-commit.

```json5
// renovate.json — configurazione per progetto uv
{
  "extends": ["config:recommended"],
  "uv": {
    "enabled": true,
    "fileMatch": ["pyproject\\.toml$"]
  },
  "lockFileMaintenance": {
    "enabled": true,
    "schedule": ["before 6am on monday"],
    "commitMessageAction": "update",
    "commitMessageTopic": "lock file"
  },
  "packageRules": [
    {
      "matchManagers": ["uv"],
      "matchUpdateTypes": ["patch", "minor"],
      "automerge": true,
      "automergeType": "pr",
      "platformAutomerge": true
    }
  ]
}
```

### Auto-merge sicuro per dipendenze

L'auto-merge delle dipendenze richiede garanzie: i test devono passare, e gli aggiornamenti major devono essere rivisti manualmente. Pattern raccomandato con GitHub Actions:

```yaml
# .github/workflows/auto-merge-deps.yml
name: Auto-merge dependency updates

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: write
  pull-requests: write

jobs:
  auto-merge:
    if: |
      github.actor == 'dependabot[bot]' ||
      github.actor == 'renovate[bot]'
    runs-on: ubuntu-latest
    steps:
      - name: Fetch Dependabot metadata
        if: github.actor == 'dependabot[bot]'
        id: metadata
        uses: dependabot/fetch-metadata@v2
        with:
          github-token: "${{ secrets.GITHUB_TOKEN }}"

      - name: Auto-merge patch and minor updates
        if: |
          steps.metadata.outputs.update-type != 'version-update:semver-major'
        run: gh pr merge --auto --squash "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Questo workflow abilita l'auto-merge solo per aggiornamenti patch e minor, lasciando i major per la revisione manuale. Il prerequisito e che le branch protection rules richiedano il passaggio dei check CI prima del merge.

---

## Branch Protection e Environment Rules

La protezione dei branch e gli environment rules sono il complemento indispensabile della pipeline CI/CD. Una pipeline che esegue tutti i controlli ma non impedisce il merge di codice che fallisce quei controlli e inutile.

### Branch Protection Rules

Su GitHub, le branch protection rules si configurano in `Settings > Branches > Branch protection rules`:

**Configurazione raccomandata per il branch `main`:**

| Regola | Valore | Motivazione |
|--------|--------|-------------|
| Require a pull request before merging | Si | Nessun push diretto a main |
| Required approvals | 1+ | Revisione obbligatoria |
| Dismiss stale reviews | Si | Nuovi push invalidano l'approvazione |
| Require status checks to pass | Si | CI obbligatoria |
| Required checks | `lint`, `test`, `security` | I job specifici che devono passare |
| Require branches to be up to date | Si | Merge solo con branch aggiornato |
| Require signed commits | Opzionale | Verifica identita dell'autore |
| Include administrators | Si | Nessuna eccezione, neanche per admin |
| Restrict pushes | Solo bot di release | Per semantic-release |
| Allow force pushes | No | Mai su branch protetti |
| Allow deletions | No | Protezione contro errori |

Per configurare le required status checks, i nomi dei check devono corrispondere esattamente ai nomi dei job nel workflow YAML. Se il job si chiama `test` nel workflow, il check si chiamera `test` nella lista dei required checks.

### Environment Protection Rules

Gli environment di GitHub permettono di definire gate di approvazione per i deployment. Sono essenziali per separare staging e production:

```yaml
# Il job di deploy referenzia l'environment
  deploy-production:
    needs: [deploy-staging, integration-tests]
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://mio-progetto.example.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: ./scripts/deploy.sh production
```

**Configurazione dell'environment `production` su GitHub:**

1. `Settings > Environments > New environment > "production"`
2. **Required reviewers**: aggiungere gli utenti o team che devono approvare il deploy
3. **Wait timer**: opzionale, aggiunge un delay (es. 15 minuti) per permettere il ripensamento
4. **Deployment branches**: limitare a `main` e tag `v*`
5. **Environment secrets**: secrets specifici per produzione (database URL, API key, ecc.)

Quando un workflow raggiunge un job con environment protetto, l'esecuzione si ferma e attende l'approvazione. I revisori ricevono una notifica e possono approvare o rifiutare direttamente dall'interfaccia di GitHub.

### Rulesets (alternativa moderna)

GitHub Rulesets sono l'evoluzione delle branch protection rules, con supporto per tag, organizzazione e bypass granulare:

```json
{
  "name": "main-protection",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/heads/main"],
      "exclude": []
    }
  },
  "rules": [
    { "type": "pull_request", "parameters": { "required_approving_review_count": 1 } },
    { "type": "required_status_checks", "parameters": {
        "required_status_checks": [
          { "context": "lint" },
          { "context": "test" },
          { "context": "security" }
        ]
      }
    },
    { "type": "non_fast_forward" }
  ],
  "bypass_actors": [
    { "actor_id": 1, "actor_type": "Integration", "bypass_mode": "always" }
  ]
}
```

---

## Pattern CI per Monorepo

Quando un singolo repository contiene piu progetti Python (ad esempio, un backend API, un worker di background e una libreria condivisa), la CI deve essere ottimizzata per eseguire solo i controlli pertinenti ai file modificati. Senza questa ottimizzazione, ogni push attiva la pipeline completa per tutti i progetti, sprecando tempo e risorse.

### Path filtering

```yaml
# .github/workflows/ci-api.yml
name: CI — API

on:
  push:
    branches: [main]
    paths:
      - 'services/api/**'
      - 'libs/shared/**'
      - 'pyproject.toml'
  pull_request:
    paths:
      - 'services/api/**'
      - 'libs/shared/**'

jobs:
  test-api:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/api
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
      - run: uv sync --frozen --dev
      - run: uv run pytest --cov=. --cov-fail-under=80
```

### Path filter con dorny/paths-filter

Per un controllo piu granulare, l'action `dorny/paths-filter` permette di definire filtri complessi e usarli come condizioni nei job successivi:

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      api: ${{ steps.filter.outputs.api }}
      worker: ${{ steps.filter.outputs.worker }}
      shared: ${{ steps.filter.outputs.shared }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            api:
              - 'services/api/**'
              - 'libs/shared/**'
            worker:
              - 'services/worker/**'
              - 'libs/shared/**'
            shared:
              - 'libs/shared/**'

  test-api:
    needs: changes
    if: needs.changes.outputs.api == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/api
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
      - run: uv sync --frozen --dev
      - run: uv run pytest

  test-worker:
    needs: changes
    if: needs.changes.outputs.worker == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/worker
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
      - run: uv sync --frozen --dev
      - run: uv run pytest
```

### Struttura monorepo Python tipica

```
my-monorepo/
├── .github/
│   └── workflows/
│       ├── ci-api.yml
│       ├── ci-worker.yml
│       └── ci-shared.yml
├── services/
│   ├── api/
│   │   ├── pyproject.toml
│   │   ├── uv.lock
│   │   ├── src/
│   │   └── tests/
│   └── worker/
│       ├── pyproject.toml
│       ├── uv.lock
│       ├── src/
│       └── tests/
├── libs/
│   └── shared/
│       ├── pyproject.toml
│       ├── src/
│       └── tests/
└── pyproject.toml          # workspace root (opzionale con uv)
```

Con uv workspaces, e possibile definire un workspace root che gestisce tutte le dipendenze in modo coordinato:

```toml
# pyproject.toml (root)
[tool.uv.workspace]
members = [
    "services/api",
    "services/worker",
    "libs/shared",
]
```

---

## Docker Multi-Stage Build per Python

Le multi-stage build di Docker sono il pattern standard per produrre immagini di produzione leggere. La tecnica consiste nel separare la fase di build (compilazione dipendenze, asset) dalla fase di runtime (solo binari e pacchetti necessari), ottenendo riduzioni del 60-80% nella dimensione dell'immagine finale.

### Pattern base con uv

```dockerfile
# ===== STAGE 1: Build =====
FROM python:3.12-slim AS builder

# Installa uv
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /usr/local/bin/

# Dipendenze di sistema per la compilazione (es. per psycopg2, lxml)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Layer 1: dipendenze (cambia raramente → cache Docker efficace)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Layer 2: codice sorgente
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ===== STAGE 2: Runtime =====
FROM python:3.12-slim AS runtime

# Solo le librerie runtime (no gcc, no dev headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copia SOLO il venv dalla fase di build
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"

# Utente non-root
RUN groupadd -r app && useradd -r -g app -d /app app
USER app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Confronto dimensioni immagini

| Approccio | Dimensione | Tempo build (no cache) |
|-----------|------------|----------------------|
| `python:3.12` singolo stage | ~1.2 GB | 90s |
| `python:3.12-slim` singolo stage | ~450 MB | 60s |
| Multi-stage `slim` | ~180 MB | 70s |
| Multi-stage `distroless` | ~120 MB | 80s |
| Multi-stage Alpine + uv | ~90 MB | 75s |

### Pattern distroless

Le immagini distroless di Google contengono solo il runtime Python, senza shell, package manager, o utility di sistema. Questo riduce drasticamente la superficie di attacco:

```dockerfile
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /usr/local/bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Stage finale: distroless
FROM gcr.io/distroless/python3-debian12

COPY --from=builder /app/.venv/lib/python3.12/site-packages /usr/lib/python3.12/site-packages
COPY --from=builder /app/src /app/src

WORKDIR /app
ENV PYTHONPATH="/app/src"
CMD ["src/app/main.py"]
```

Attenzione: le immagini distroless non hanno shell, quindi `docker exec -it container sh` non funziona. Il debug richiede strumenti esterni come `kubectl debug` o l'uso di un'immagine di debug dedicata.

### BuildKit cache mount

I `--mount=type=cache` di BuildKit sono il meccanismo chiave per velocizzare le build Docker con uv/pip:

```dockerfile
# Cache per uv — persiste tra build sullo stesso host
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Cache per pip — equivalente
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Cache multipla: uv + apt
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/root/.cache/uv \
    apt-get update && apt-get install -y gcc && \
    uv sync --frozen --no-dev
```

La cache mount non viene inclusa nell'immagine finale — esiste solo durante la build e persiste tra invocazioni successive sullo stesso host Docker. Per la CI, la cache deve essere esportata con `cache-from`/`cache-to`.

### Health check

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
```

Il HEALTHCHECK e fondamentale per orchestratori come Docker Swarm e Kubernetes: un container che risponde a HTTP ma non funziona correttamente viene riavviato automaticamente.

---

## CI/CD Security — SLSA e Sigstore

La sicurezza della supply chain software e diventata una priorita dopo attacchi ad alto profilo come SolarWinds (2020) e log4shell (2021). Due framework emergenti — **SLSA** e **Sigstore** — forniscono meccanismi concreti per attestare l'integrita degli artefatti prodotti dalla CI.

### SLSA (Supply-chain Levels for Software Artifacts)

SLSA (pronunciato "salsa") e un framework graduato che definisce livelli di sicurezza progressivi per la supply chain software:

| Livello | Requisiti | Cosa garantisce |
|---------|-----------|-----------------|
| **SLSA 0** | Nessuno | Nessuna garanzia |
| **SLSA 1** | Build documentata | L'artefatto ha provenienza (provenance) |
| **SLSA 2** | Build su piattaforma hosted, provenance firmata | L'artefatto e stato costruito dal codice dichiarato |
| **SLSA 3** | Build isolata, source verificata, provenance non falsificabile | Protezione contro compromissione del build system |

**SLSA 2 e raggiungibile in un giorno** per la maggior parte dei progetti Python su GitHub Actions. Richiede:
1. Build su runner hosted (non self-hosted) — gia vero per la maggior parte dei progetti.
2. Generazione di provenance firmata — una action lo gestisce automaticamente.

```yaml
# .github/workflows/slsa-release.yml
name: SLSA Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      hashes: ${{ steps.hash.outputs.hashes }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Build
        run: pip install build && python -m build

      - name: Generate hashes
        id: hash
        run: |
          cd dist
          echo "hashes=$(sha256sum * | base64 -w0)" >> "$GITHUB_OUTPUT"

      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  provenance:
    needs: build
    permissions:
      actions: read
      id-token: write
      contents: write
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.1.0
    with:
      base64-subjects: ${{ needs.build.outputs.hashes }}
      upload-assets: true

  publish:
    needs: [build, provenance]
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    environment:
      name: pypi
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          attestations: true
```

Il job `provenance` genera e firma un documento SLSA provenance in formato in-toto, che attesta:
- **Chi** ha avviato la build (l'actor GitHub).
- **Cosa** e stato costruito (hash degli artefatti).
- **Come** e stato costruito (workflow, parametri, input).
- **Da dove** proviene il codice (repository, commit, tag).

### Sigstore e cosign per Python

Sigstore e un'infrastruttura di firma crittografica **keyless**: non serve generare, memorizzare o ruotare chiavi private. Il flusso:

1. Il CI ottiene un token OIDC dal provider (GitHub Actions).
2. Sigstore emette un certificato X.509 di breve durata (10 minuti) legato all'identita OIDC.
3. L'artefatto viene firmato con la chiave privata effimera.
4. La firma e il certificato vengono registrati in un **transparency log** (Rekor) pubblico e immutabile.
5. La chiave privata viene distrutta — non esiste fuori dal processo CI.

```yaml
      - name: Sign artifacts with Sigstore
        uses: sigstore/gh-action-sigstore-python@v3
        with:
          inputs: dist/*.tar.gz dist/*.whl
```

Verifica locale:

```bash
# Installa sigstore cli
uvx sigstore verify identity \
    --cert-identity "https://github.com/org/repo/.github/workflows/release.yml@refs/tags/v1.0.0" \
    --cert-oidc-issuer "https://token.actions.githubusercontent.com" \
    dist/pacchetto-1.0.0.tar.gz
```

### PyPI e la supply chain

PyPI sta integrando progressivamente questi standard:
- **Trusted Publishers**: gia disponibili e raccomandati (OIDC per pubblicazione).
- **Attestations**: supporto per attestazioni SLSA-like sugli artefatti pubblicati.
- **PEP 740**: specifica per attestazioni digitali su PyPI, in fase di implementazione.
- **Transparency log**: le firme dei pacchetti vengono registrate in Sigstore Rekor.

L'obiettivo a medio termine e che `pip install` possa verificare crittograficamente che un pacchetto e stato costruito dal repository dichiarato, senza fidarsi ciecamente del contenuto su PyPI.

---

## GitHub Actions Avanzate

Questa sezione copre pattern avanzati di GitHub Actions che migliorano la robustezza, l'osservabilita e l'efficienza delle pipeline CI/CD.

### Concurrency control

Il concurrency control impedisce l'esecuzione di workflow duplicati sullo stesso branch o PR:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

Quando un nuovo push arriva sullo stesso branch, il workflow in esecuzione viene cancellato e sostituito. Questo risparmia minuti billabili e evita merge di risultati obsoleti. Per branch protetti come `main`, disabilitare `cancel-in-progress`:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

### Timeout e retry

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15      # Kill il job dopo 15 minuti
    steps:
      - name: Run tests
        timeout-minutes: 10  # Timeout per singolo step
        run: uv run pytest --timeout=60  # Timeout per singolo test
```

Senza timeout espliciti, un test appeso puo consumare l'intero budget di minuti (6 ore e il default). Tre livelli di timeout: job, step, test individuale.

### workflow_dispatch — trigger manuale

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: "Target environment"
        required: true
        type: choice
        options:
          - staging
          - production
      dry_run:
        description: "Dry run mode"
        type: boolean
        default: true
      version:
        description: "Version to deploy"
        type: string
        required: false

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - name: Deploy
        run: |
          echo "Deploying to ${{ inputs.environment }}"
          echo "Dry run: ${{ inputs.dry_run }}"
          echo "Version: ${{ inputs.version || github.sha }}"
```

Il trigger `workflow_dispatch` abilita l'esecuzione manuale dal tab Actions di GitHub, con input parametrizzabili. Indispensabile per deployment manuali, rollback e operazioni una tantum.

### GITHUB_STEP_SUMMARY — report in-workflow

`GITHUB_STEP_SUMMARY` permette di scrivere contenuto Markdown che appare nella pagina di riepilogo del workflow run:

```yaml
      - name: Test report
        if: always()
        run: |
          echo "## Test Results" >> "$GITHUB_STEP_SUMMARY"
          echo "" >> "$GITHUB_STEP_SUMMARY"

          if uv run pytest --tb=short -q 2>&1 | tee test-output.txt; then
            echo "✅ All tests passed" >> "$GITHUB_STEP_SUMMARY"
          else
            echo "❌ Some tests failed" >> "$GITHUB_STEP_SUMMARY"
          fi

          echo "" >> "$GITHUB_STEP_SUMMARY"
          echo '```' >> "$GITHUB_STEP_SUMMARY"
          tail -20 test-output.txt >> "$GITHUB_STEP_SUMMARY"
          echo '```' >> "$GITHUB_STEP_SUMMARY"

      - name: Coverage report
        if: always()
        run: |
          echo "## Coverage" >> "$GITHUB_STEP_SUMMARY"
          uv run coverage report --format=markdown >> "$GITHUB_STEP_SUMMARY"
```

Questo elimina la necessita di cercare informazioni nei log: il riepilogo appare direttamente nella pagina del workflow run, visibile a tutti i revisori della PR.

### Permissions minime (principle of least privilege)

```yaml
# Permissions al livello di workflow (restrittive per default)
permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    # Non serve override — eredita contents: read

  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write    # Solo per OIDC
      contents: read     # Per checkout
    # Nessun altro permesso
```

La best practice e dichiarare `permissions` restrittive a livello di workflow e aggiungere solo le permissions necessarie a livello di job. Il default di GitHub e `permissions: write-all`, che da a ogni job la capacita di modificare il repository, creare release, e accedere ai secrets — eccessivo per la maggior parte dei job.

### Job output e inter-job communication

```yaml
jobs:
  analyze:
    runs-on: ubuntu-latest
    outputs:
      should_deploy: ${{ steps.check.outputs.deploy }}
      version: ${{ steps.version.outputs.version }}
    steps:
      - id: check
        run: |
          if [[ "${{ github.ref }}" == refs/tags/v* ]]; then
            echo "deploy=true" >> "$GITHUB_OUTPUT"
          else
            echo "deploy=false" >> "$GITHUB_OUTPUT"
          fi
      - id: version
        run: echo "version=$(python -c 'import app; print(app.__version__)')" >> "$GITHUB_OUTPUT"

  deploy:
    needs: analyze
    if: needs.analyze.outputs.should_deploy == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying version ${{ needs.analyze.outputs.version }}"
```

---

## Troubleshooting CI/CD

Le pipeline CI/CD possono fallire per ragioni non ovvie. Questa sezione copre i problemi piu comuni e le relative soluzioni.

### Problemi frequenti

**1. Test che passano localmente ma falliscono in CI**

Cause comuni:
- **Timezone diversa**: il runner usa UTC, la macchina locale potrebbe usare un fuso diverso. Soluzione: usare sempre UTC nei test (`datetime.now(timezone.utc)`)
- **Ordine dei test**: localmente i test girano sempre nello stesso ordine; in CI, `pytest-randomly` o l'esecuzione parallela possono esporre dipendenze tra test. Soluzione: ogni test deve essere indipendente
- **File system case-sensitivity**: macOS usa un filesystem case-insensitive per default, Linux no. Un `import MyModule` che funziona su macOS fallisce su Linux se il file si chiama `mymodule.py`
- **Dipendenze di sistema mancanti**: librerie C come `libpq-dev` o `libxml2-dev` non sono installate di default sui runner

**2. Cache che non viene utilizzata**

```yaml
# Problema: la cache key cambia ad ogni run
key: ${{ runner.os }}-pip-${{ hashFiles('**/*.txt') }}
#                                    ^^^^^^^^ troppo generico

# Soluzione: specificare il file esatto
key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt', 'requirements-dev.txt') }}
```

**3. Rate limiting su PyPI/TestPyPI**

PyPI ha rate limit per i download delle dipendenze. Se la pipeline fallisce con errori HTTP 429, aggiungere retry o usare un mirror:

```yaml
      - name: Install with retry
        run: |
          pip install --retries 3 --timeout 60 -r requirements.txt
```

**4. Workflow che non si attiva**

Verificare:
- Il file YAML e sintatticamente valido (usare `actionlint` localmente)
- I path filter corrispondono ai file modificati
- Il branch e incluso nel trigger (`branches:`)
- Per le PR da fork, i secrets non sono disponibili (per sicurezza)

### Debug dei workflow

```yaml
      - name: Debug information
        if: failure()
        run: |
          echo "Python version: $(python --version)"
          echo "uv version: $(uv --version 2>/dev/null || echo 'not installed')"
          echo "pip list:"
          pip list 2>/dev/null || uv pip list
          echo "Disk usage:"
          df -h
          echo "Environment:"
          env | sort | grep -v TOKEN | grep -v SECRET | grep -v KEY
```

Per eseguire i workflow localmente prima di pusharli, `act` (https://github.com/nektos/act) emula l'ambiente GitHub Actions sulla macchina locale:

```bash
# Installazione
brew install act  # macOS
# oppure
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Esecuzione
act push                          # simula un push event
act pull_request                  # simula una PR
act -j test                       # esegui solo il job "test"
act --secret-file .secrets        # fornisci i secrets da file
act -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest  # immagine custom
```

### Validazione YAML

```bash
# actionlint — linter specifico per GitHub Actions
# Installazione: go install github.com/rhysd/actionlint/cmd/actionlint@latest
actionlint .github/workflows/*.yml

# yamllint — linter YAML generico
pip install yamllint
yamllint .github/workflows/
```

---

## Esercizi di Consolidamento

**Esercizio 1 — Pipeline base con uv:**
Crea un repository Python con una CLI minimale (argparse o click), scrivi 5 test con pytest, e configura una pipeline GitHub Actions che esegua: ruff check, ruff format --check, mypy, pytest con coverage (soglia 80%), e build del pacchetto. Usa uv come package manager. Verifica che un push con un errore di linting faccia fallire la pipeline.

**Esercizio 2 — Matrix testing e caching:**
Estendi la pipeline dell'esercizio 1 con matrix testing su Python 3.11, 3.12 e 3.13, e su ubuntu-latest e macos-latest. Configura il caching delle dipendenze uv con cache-suffix per versione Python. Misura il tempo della pipeline con e senza cache (confronta le esecuzioni nel tab Actions).

**Esercizio 3 — Pre-commit e security scanning:**
Configura `.pre-commit-config.yaml` con hook per: trailing-whitespace, end-of-file-fixer, ruff, ruff-format, mypy. Aggiungi un job di security scanning nella pipeline CI che esegua pip-audit e bandit. Introduci deliberatamente una dipendenza con CVE nota (es. una versione vecchia di requests) e verifica che pip-audit la rilevi.

**Esercizio 4 — Release automation:**
Implementa una pipeline di rilascio tag-triggered. Il workflow deve: verificare che i test passino, costruire wheel e sdist con `python -m build`, verificare il pacchetto con `twine check dist/*`, e pubblicare su TestPyPI. Configura il trusted publisher su TestPyPI per il tuo repository. Crea un tag `v0.1.0` e verifica che il pacchetto appaia su test.pypi.org.

**Esercizio 5 — Pipeline completa con nox e deployment:**
Crea un progetto FastAPI con un endpoint `/health`. Configura un `noxfile.py` con sessioni: tests (multi-Python), lint, typecheck, security. Crea un Dockerfile multi-stage. Configura una pipeline CI/CD completa che: esegua nox nella CI, costruisca e pubblichi l'immagine Docker su GHCR, e simuli un deployment (anche solo un job che fa `docker pull` e `docker run --rm` dell'immagine appena pubblicata).

**Esercizio 6 — Docker multi-stage build:**
Crea un Dockerfile multi-stage per un'applicazione FastAPI con dipendenze native (psycopg2). Lo stage di build deve usare `python:3.12-slim` con gcc e libpq-dev; lo stage di runtime deve includere solo libpq5. Usa `uv` per le dipendenze con BuildKit cache mount. Confronta le dimensioni dell'immagine singolo-stage vs multi-stage con `docker images`. Verifica che l'applicazione si avvii correttamente nel container finale con `docker run --rm -p 8000:8000 app`. Aggiungi un `HEALTHCHECK` che verifichi l'endpoint `/health`.

**Esercizio 7 — SLSA provenance:**
Configura una pipeline di rilascio con SLSA provenance Level 2. Il workflow deve: (1) costruire il pacchetto Python in un job dedicato, (2) calcolare gli hash SHA256 degli artefatti, (3) usare `slsa-framework/slsa-github-generator` per generare la provenance firmata, (4) pubblicare su TestPyPI con attestazioni. Verifica che la provenance sia accessibile nelle release di GitHub. Esamina il contenuto del documento di provenance: quale informazioni contiene?

**Esercizio 8 — Renovate con auto-merge:**
Configura Renovate per un progetto Python con le seguenti regole: (1) auto-merge per aggiornamenti patch e minor che passano la CI, (2) aggiornamenti major bloccati con label "breaking-change", (3) raggruppamento dei dev-tools (ruff, mypy, pytest) in una singola PR settimanale, (4) lockFileMaintenance mensile per il `uv.lock`, (5) aggiornamento automatico di `.pre-commit-config.yaml`. Attendi almeno una PR automatica da Renovate e verifica che il processo funzioni end-to-end.

**Esercizio 9 — GitHub Actions avanzate:**
Crea un workflow con: (1) concurrency control che cancelli esecuzioni precedenti su PR ma non su main, (2) trigger `workflow_dispatch` con input per scegliere l'environment (staging/production) e un flag dry_run, (3) `GITHUB_STEP_SUMMARY` che mostri i risultati dei test e la coverage in formato Markdown, (4) permissions minime dichiarate a livello di workflow con override per job specifici, (5) timeout di 15 minuti a livello di job e 10 minuti per lo step di test. Esegui il workflow manualmente dal tab Actions e verifica che il summary appaia correttamente.

**Esercizio 10 — Pipeline GitLab CI migrazione:**
Prendi la pipeline GitHub Actions dell'esercizio 1 e migra a GitLab CI. Mappa: `runs-on` → `image`, `strategy.matrix` → `parallel:matrix`, `actions/cache` → `cache:`, `needs` → `needs:`, `if` → `rules:`. Verifica che la pipeline funzioni su GitLab. Documenta le differenze principali incontrate durante la migrazione (sintassi, caching, artifacts, environments).

---

## Letture e Riferimenti

### Fonti Primarie

- **GitHub Actions Documentation** — https://docs.github.com/en/actions (consultato: 2026-05-24). Documentazione ufficiale: workflow syntax, context, expressions, environment variables.

- **GitLab CI/CD Documentation** — https://docs.gitlab.com/ee/ci/ (consultato: 2026-05-24). Reference per `.gitlab-ci.yml`, pipeline architecture, runners, environments.

- **PyPA Publishing Guide** — https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/ (consultato: 2026-05-24). Guida ufficiale PyPA per pubblicazione automatizzata su PyPI con Trusted Publishers.

- **Trusted Publishers — PyPI** — https://docs.pypi.org/trusted-publishers/ (consultato: 2026-05-24). Specifica OIDC trusted publishing: configurazione, supported CI providers, security model.

- **uv Documentation** — https://docs.astral.sh/uv/ (consultato: 2026-05-24). Reference per uv: lockfile, sync, build, publish, workspace, CI integration.

- **pre-commit Documentation** — https://pre-commit.com/ (consultato: 2026-05-24). Framework per hook pre-commit: configurazione, hook disponibili, integrazione CI.

- **tox Documentation** — https://tox.wiki/ (consultato: 2026-05-24). Testing multi-ambiente: configurazione, plugin, integrazione CI.

- **Nox Documentation** — https://nox.thea.codes/ (consultato: 2026-05-24). Task runner basato su Python: sessioni, parametrizzazione, CI.

- **python-semantic-release** — https://python-semantic-release.readthedocs.io/ (consultato: 2026-05-24). Automazione rilasci basata su Conventional Commits.

- **pip-audit** — https://github.com/pypa/pip-audit (consultato: 2026-05-24). Strumento ufficiale PyPA per scansione vulnerabilita dipendenze Python.

- **Bandit** — https://bandit.readthedocs.io/ (consultato: 2026-05-24). Analisi statica di sicurezza per codice Python (AST-based).

- **SLSA Framework** — https://slsa.dev/ (consultato: 2026-05-24). Specifica SLSA: livelli di sicurezza, requisiti per provenance, guida all'implementazione.

- **slsa-github-generator** — https://github.com/slsa-framework/slsa-github-generator (consultato: 2026-05-24). Action ufficiale SLSA per generare provenance firmata in GitHub Actions.

- **Sigstore** — https://www.sigstore.dev/ (consultato: 2026-05-24). Infrastruttura di firma keyless: cosign, fulcio, rekor, sigstore-python.

- **PEP 740** — https://peps.python.org/pep-0740/ (consultato: 2026-05-24). Specifica per attestazioni digitali (digital attestations) su PyPI.

- **pre-commit.ci** — https://pre-commit.ci/ (consultato: 2026-05-24). Servizio CI dedicato per pre-commit con autofix e autoupdate.

- **Renovate Documentation** — https://docs.renovatebot.com/ (consultato: 2026-05-24). Documentazione completa per Renovate: configurazione, managers, packageRules, auto-merge.

- **Docker Multi-Stage Builds** — https://docs.docker.com/build/building/multi-stage/ (consultato: 2026-05-24). Guida ufficiale Docker per build multi-stage.

### Testi Consigliati

- **"Python Packages" di Tomas Beuzen e Tiffany Timbers (online gratuito)** — Guida al packaging Python moderno, inclusa automazione CI/CD. https://py-pkgs.org/

- **"Serious Python" di Julien Danjou (No Starch Press)** — Capitoli su packaging, distribuzione e deployment di progetti Python professionali.

---

## Riferimenti Incrociati

| Argomento | Modulo | File |
|-----------|--------|------|
| pytest, coverage, fixture, parametrize | 08 | [08-testing.md](08-testing.md) |
| Sicurezza Python: input validation, secrets, audit | 18 | [18-sicurezza.md](18-sicurezza.md) |
| Virtual environments, uv, pip, pyproject.toml | 24 | [24-virtual-environments.md](24-virtual-environments.md) |
| Docker: Dockerfile, multi-stage, compose, registry | 26 | [26-docker-per-python.md](26-docker-per-python.md) |
| Packaging: wheel, sdist, build, pyproject.toml | 23 | [23-packaging-distribuzione.md](23-packaging-distribuzione.md) |
| Type hints, mypy, pyright, strict mode | 09 | [09-type-hints-e-mypy.md](09-type-hints-e-mypy.md) |
| Osservabilita: OpenTelemetry, Prometheus | 31 | [31-osservabilita-otel-prometheus.md](31-osservabilita-otel-prometheus.md) |
| Ruff, linting moderno, formatting, tooling Python | 22 | [22-tooling-moderno.md](22-tooling-moderno.md) |
| Supply chain security, SBOM, dependency auditing | 18 | [18-sicurezza.md](18-sicurezza.md) |
| PEP 735 dependency groups, PEP 723 script metadata | 24 | [24-virtual-environments.md](24-virtual-environments.md) |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **artifact** | File prodotto da un job CI (report, pacchetto, immagine) reso disponibile ai job successivi o per download. |
| **branch protection** | Regole che impediscono push diretti, merge senza approvazione o merge con check falliti su branch specifici. |
| **cache** | Meccanismo per conservare file tra esecuzioni CI (dipendenze, build intermedi), riducendo tempi di pipeline. |
| **composite action** | Action GitHub riutilizzabile composta da piu step, definita in un `action.yml` e richiamabile come singolo step. |
| **Conventional Commits** | Convenzione per messaggi di commit (`feat:`, `fix:`, `chore:`) che abilita automazione del versioning semantico. |
| **coverage** | Percentuale di codice sorgente eseguita durante i test. Misurata come line coverage o branch coverage. |
| **Dependabot** | Servizio GitHub che crea pull request automatiche per aggiornare dipendenze con vulnerabilita note o versioni obsolete. |
| **environment** | Contesto di deployment in GitHub Actions (staging, production) con secrets dedicati e regole di approvazione. |
| **fail-fast** | Strategia di matrix testing: se `true`, il fallimento di un job cancella tutti gli altri; se `false`, tutti completano. |
| **matrix testing** | Esecuzione dello stesso job con combinazioni diverse di parametri (versione Python, OS, database). |
| **OIDC** | OpenID Connect — protocollo di autenticazione usato dai Trusted Publishers per pubblicare su PyPI senza token API. |
| **pre-commit** | Framework per hook Git che esegue controlli (linting, formatting, type checking) prima di ogni commit. |
| **reusable workflow** | Workflow GitHub Actions definito con `workflow_call` e richiamabile da altri workflow, anche in repository diversi. |
| **runner** | Macchina (virtuale o fisica) che esegue i job di una pipeline CI. Hosted (gestito dalla piattaforma) o self-hosted. |
| **semantic versioning** | Schema di versionamento `MAJOR.MINOR.PATCH` dove major = breaking changes, minor = nuove feature, patch = bugfix. |
| **Trusted Publisher** | Meccanismo PyPI che autentica pipeline CI via OIDC, eliminando necessita di gestire token API manuali. |
| **workflow** | File YAML che definisce una pipeline CI/CD: trigger, job, step, permessi, environment. |
| **attestation** | Prova crittografica che lega un artefatto al codice sorgente e al workflow che l'ha prodotto. Supportato da PyPI tramite PEP 740. |
| **BuildKit** | Backend di build Docker avanzato con supporto per cache mount, build secrets, parallelismo migliorato. Abilitato con `DOCKER_BUILDKIT=1`. |
| **concurrency** | Meccanismo GitHub Actions per impedire esecuzioni duplicate di workflow sullo stesso branch o PR. |
| **distroless** | Immagini Docker minimali di Google che contengono solo il runtime applicativo, senza shell, package manager o utility di sistema. |
| **GITHUB_STEP_SUMMARY** | Variabile d'ambiente che permette di scrivere contenuto Markdown nel riepilogo di un workflow run. |
| **multi-stage build** | Tecnica Docker che usa piu `FROM` per separare la fase di build dalla fase di runtime, producendo immagini piu piccole e sicure. |
| **pre-commit.ci** | Servizio SaaS gratuito (per repo pubblici) che esegue hook pre-commit come check CI e puo autofix le violazioni nella PR. |
| **provenance** | Documento SLSA che attesta chi ha costruito un artefatto, da quale codice, con quale workflow, e con quali parametri. |
| **Renovate** | Bot per aggiornamento automatico delle dipendenze, alternativa a Dependabot, con supporto multi-piattaforma e auto-merge nativo. |
| **Sigstore** | Infrastruttura di firma crittografica keyless che usa certificati OIDC temporanei e un transparency log pubblico (Rekor). |
| **SLSA** | Supply-chain Levels for Software Artifacts — framework graduato (livelli 0-3) per la sicurezza della supply chain software. |
| **transparency log** | Registro pubblico e immutabile (Rekor in Sigstore) dove vengono registrate le firme crittografiche degli artefatti. |
| **workflow_dispatch** | Trigger GitHub Actions per esecuzione manuale con input parametrizzabili, utile per deployment manuali e rollback. |
| **blue/green deployment** | Strategia di deployment che mantiene due ambienti identici, commutando il traffico tra essi per aggiornamenti con zero downtime e rollback istantaneo. |
| **branch coverage** | Misura di coverage che verifica che ogni ramo condizionale (if/else) venga attraversato, piu rigorosa della line coverage. |
| **canary deployment** | Strategia che instrada una percentuale ridotta di traffico alla nuova versione, monitorando metriche prima della promozione completa. |
| **diff coverage** | Misura di coverage applicata solo alle righe di codice modificate nella PR, garantendo che il codice nuovo sia testato indipendentemente dal debito tecnico. |
| **dynamic matrix** | Matrice GitHub Actions generata a runtime da un job preparatorio, utile per derivare le versioni supportate dal pyproject.toml. |
| **health check** | Endpoint HTTP (tipicamente `/health`) che verifica lo stato dell'applicazione. Usato da orchestratori per riavvio automatico di container non funzionanti. |
| **keyless signing** | Firma crittografica senza chiavi persistenti. Sigstore emette certificati di breve durata legati all'identita OIDC, eliminando la gestione delle chiavi. |
| **PEP 740** | Specifica per attestazioni digitali su PyPI, che permette di verificare crittograficamente la provenienza dei pacchetti pubblicati. |
| **pip-audit** | Strumento ufficiale PyPA per la scansione delle vulnerabilita note nelle dipendenze Python, basato sul database OSV. |
| **Semgrep** | Motore di analisi statica multi-linguaggio con regole personalizzabili, usato per rilevare pattern di sicurezza problematici nel codice. |
| **SAST** | Static Application Security Testing — analisi statica del codice sorgente alla ricerca di vulnerabilita senza eseguire l'applicazione. |
| **actionlint** | Linter specifico per i file YAML dei workflow GitHub Actions. Rileva errori di sintassi, riferimenti a contesti inesistenti e pattern problematici. |
