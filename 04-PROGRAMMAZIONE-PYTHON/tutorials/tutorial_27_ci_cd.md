# Tutorial 27 — CI/CD per Python: GitHub Actions, Testing, Deploy

> **Companion a:** `27-ci-cd.md`
> **Scope:** GitHub Actions, pipeline test/lint/build/deploy, Docker registry, ambienti
> **Prerequisiti:** `tutorial_26_docker.md`, `tutorial_23_packaging.md`
> **Durata stimata:** 12-16 ore

---

## Mappa concettuale

```
CI/CD Pipeline Python
│
├── CI — Continuous Integration
│   ├── Trigger: push, PR, tag, schedule
│   ├── Lint: ruff check
│   ├── Type check: mypy --strict
│   ├── Test: pytest --cov
│   ├── Security: pip-audit, trivy
│   └── Build: docker buildx
│
├── CD — Continuous Delivery
│   ├── Staging: deploy su ogni merge in main
│   ├── Production: deploy su tag v*
│   └── Rollback: revert del deploy
│
├── GitHub Actions
│   ├── jobs — task paralleli/sequenziali
│   ├── steps — azioni sequenziali in un job
│   ├── actions — block riutilizzabili
│   ├── secrets — credenziali cifrate
│   └── environments — staging/production
│
└── Pattern
    ├── Matrix build — test su più versioni
    ├── Caching dipendenze — build veloci
    ├── Artifact upload/download
    └── Trusted Publisher — PyPI senza API key
```

---

# Parte A — Pipeline CI completa

---

## A1. Workflow GitHub Actions principale

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:   # trigger manuale

env:
  PYTHON_VERSION: "3.12"
  UV_CACHE_DIR: /tmp/.uv-cache

jobs:
  # ─── Lint e Type Check ──────────────────────────────────────
  qualita-codice:
    name: Qualità codice
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - run: uv sync --frozen --group dev

      - name: Lint con ruff
        run: uv run ruff check . --output-format=github

      - name: Format check
        run: uv run ruff format --check .

      - name: Type check con mypy
        run: uv run mypy src/ --strict

  # ─── Test su matrice Python ────────────────────────────────
  test:
    name: Test Python ${{ matrix.python-version }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13"]
        os: [ubuntu-latest, windows-latest, macos-latest]

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: testdb
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v3
        with:
          python-version: ${{ matrix.python-version }}
          enable-cache: true

      - run: uv sync --frozen --group test

      - name: Esegui migrazioni test
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/testdb
        run: uv run alembic upgrade head

      - name: Test con coverage
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/testdb
        run: uv run pytest --cov=mio_progetto --cov-report=xml --cov-fail-under=80

      - name: Upload coverage a Codecov
        uses: codecov/codecov-action@v4
        if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.12'
        with:
          file: ./coverage.xml

  # ─── Security scan ─────────────────────────────────────────
  security:
    name: Security scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --frozen

      - name: Audit dipendenze
        run: uv run pip-audit --format=json --output=audit.json
        continue-on-error: true

      - name: Upload audit report
        uses: actions/upload-artifact@v4
        with:
          name: security-audit
          path: audit.json

  # ─── Build Docker ──────────────────────────────────────────
  build:
    name: Build Docker image
    runs-on: ubuntu-latest
    needs: [qualita-codice, test]
    outputs:
      image-digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login su GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build e push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          target: runtime
          push: ${{ github.event_name != 'pull_request' }}
          tags: |
            ghcr.io/${{ github.repository }}:latest
            ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64
```

---

## A2. Workflow deploy staging e production

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]
    tags: ["v*"]

jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Deploy su staging
        run: |
          # Esempio con SSH
          echo "$SSH_KEY" > /tmp/deploy_key
          chmod 600 /tmp/deploy_key
          ssh -i /tmp/deploy_key -o StrictHostKeyChecking=no \
            deploy@staging.example.com \
            "cd /app && git pull && docker compose pull && docker compose up -d"
        env:
          SSH_KEY: ${{ secrets.STAGING_SSH_KEY }}

      - name: Smoke test staging
        run: |
          sleep 30   # attende che il container sia pronto
          curl -f https://staging.example.com/salute

  deploy-production:
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    environment: production
    needs: [deploy-staging]
    steps:
      - name: Deploy su produzione
        run: echo "Deploy versione ${{ github.ref_name }}"
```

---

# Parte B — Pattern avanzati

---

## B1. Cache dipendenze uv

```yaml
# Ottimizzazione: cache layer uv per build veloci
- uses: astral-sh/setup-uv@v3
  with:
    enable-cache: true
    # Cache invalidata quando uv.lock cambia
    cache-dependency-glob: "uv.lock"

# Alternatively: cache manuale
- name: Cache uv
  uses: actions/cache@v4
  with:
    path: /tmp/.uv-cache
    key: ${{ runner.os }}-uv-${{ hashFiles('uv.lock') }}
    restore-keys: |
      ${{ runner.os }}-uv-

- run: uv sync --frozen
  env:
    UV_CACHE_DIR: /tmp/.uv-cache
```

---

## B2. Pre-commit hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: ["--fix"]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        args: ["--strict"]
        additional_dependencies: ["pydantic>=2.0", "types-redis"]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-yaml
      - id: check-toml
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-added-large-files
        args: ["--maxkb=500"]
      - id: detect-private-key
```

```bash
# Installa e configura pre-commit
pip install pre-commit
pre-commit install        # installa hook .git/hooks/pre-commit
pre-commit run --all-files   # esegui su tutti i file
```

---

# Parte C — pyproject.toml configurazione tools

---

## C1. Configurazione centralizzata

```toml
# pyproject.toml — tutte le configurazioni tool in un file

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--strict-markers",
    "-x",                    # stop al primo failure
    "--tb=short",
]
markers = [
    "slow: test lento (deseleziona con -m 'not slow')",
    "integration: richiede database reale",
]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
show_missing = true
fail_under = 80

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = false
warn_unused_configs = true

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "D",     # docstrings — opzionali
    "ANN",   # annotations — mypy le controlla
    "COM812", # conflitto con formatter
]

[tool.ruff.lint.isort]
known-first-party = ["mio_progetto"]
```

---

# Parte D — Riepilogo

## Checklist pipeline CI/CD

**CI (ogni push/PR):**
- [ ] `ruff check` — nessun warning
- [ ] `ruff format --check` — codice formattato
- [ ] `mypy --strict` — nessun errore tipo
- [ ] `pytest --cov --cov-fail-under=80` — test verdi, coverage > 80%
- [ ] `pip-audit` — nessuna vulnerabilità critica
- [ ] Docker build — immagine si costruisce

**CD Staging (merge in main):**
- [ ] Pull nuova immagine
- [ ] Migrate DB
- [ ] Smoke test endpoint `/salute`
- [ ] Notifica Slack/Teams

**CD Production (tag v*):**
- [ ] Approval manuale (GitHub Environments)
- [ ] Deploy con zero downtime
- [ ] Smoke test
- [ ] Rollback plan documentato

## Prossimi passi

- `tutorial_31_otel.md` — osservabilità per sapere se il deploy ha avuto successo
- `tutorial_33_profiling.md` — profiling in produzione
