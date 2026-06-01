---
corso: "GitHub e Git Actions"
fase: "6 — Avanzato"
modulo: 23
titolo: "Migrazione a GitHub da Altre Piattaforme"
versione: "GitHub Enterprise Importer 2024"
livello: "Avanzato"
prerequisiti: ["Piattaforma GitHub (modulo 03)", "GitHub Actions CI/CD (modulo 19)", "Git fondamenti (modulo 01)"]
obiettivi:
  - "Pianificare una migrazione completa da GitLab, Bitbucket o Azure DevOps a GitHub"
  - "Migrare repository preservando storia Git, branch, tag e Large File Storage"
  - "Convertire pipeline CI/CD (GitLab CI, Bitbucket Pipelines, Azure Pipelines) in GitHub Actions"
  - "Trasferire issue, merge request, wiki e integrazioni con mapping corretto degli utenti"
  - "Validare la migrazione con checklist di verifica e gestire il periodo di transizione"
tag: [migrazione, gitlab, bitbucket, azure-devops, github-importer, ci-cd-conversion, git-history, issue-migration, webhook, cutover]
---

# 23 — Migrazione a GitHub da Altre Piattaforme

> **Modulo 23** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al termine di questo modulo sarai in grado di:
>
> 1. Pianificare una migrazione completa da GitLab, Bitbucket o Azure DevOps a GitHub
> 2. Migrare repository preservando storia Git, branch, tag e Large File Storage
> 3. Convertire pipeline CI/CD (GitLab CI, Bitbucket Pipelines, Azure Pipelines) in GitHub Actions
> 4. Trasferire issue, merge request, wiki e integrazioni con mapping corretto degli utenti
> 5. Validare la migrazione con checklist di verifica e gestire il periodo di transizione

## Idee guida
1. **GitHub Importer per GitLab/Bitbucket basico.**
2. **Migration include: code, issues, PR/MR, wiki.**
3. **Action conversion (GitLab CI → GHA) manual.**
4. **Webhook + integration redirection plan.**


## Indice

1. [Introduzione](#introduzione)
2. [Pianificazione della Migrazione](#pianificazione-della-migrazione)
3. [Migrazione da GitLab](#migrazione-da-gitlab)
   - [Migrazione dei Repository](#migrazione-repository-gitlab)
   - [Migrazione delle Pipeline CI/CD a GitHub Actions](#migrazione-cicd-gitlab)
   - [Migrazione delle Issue e Merge Request](#migrazione-issue-gitlab)
4. [Migrazione da Bitbucket](#migrazione-da-bitbucket)
   - [Migrazione dei Repository](#migrazione-repository-bitbucket)
   - [Migrazione delle Pipelines a GitHub Actions](#migrazione-cicd-bitbucket)
5. [Migrazione da Azure DevOps](#migrazione-da-azure-devops)
   - [Migrazione dei Repository](#migrazione-repository-azure)
   - [Migrazione delle Pipelines a GitHub Actions](#migrazione-cicd-azure)
   - [Migrazione dei Boards a GitHub Projects](#migrazione-boards-azure)
6. [Migrazione da SVN a Git](#migrazione-da-svn-a-git)
   - [Approccio con git-svn](#approccio-git-svn)
   - [Approccio con svn2git](#approccio-svn2git)
   - [Preservazione della Storia](#preservazione-della-storia)
7. [Migrazione da TFVC a Git (git-tfs)](#migrazione-da-tfvc-a-git)
   - [Import tramite Azure DevOps](#import-tramite-azure-devops)
   - [Migrazione con git-tfs](#migrazione-con-git-tfs)
   - [Gestione Branch TFVC](#gestione-branch-tfvc)
8. [GitHub Enterprise Importer (GEI) in Dettaglio](#github-enterprise-importer-gei-in-dettaglio)
   - [Architettura e Componenti](#architettura-e-componenti-gei)
   - [gh gei — Migrazione tra GitHub](#gh-gei-migrazione-tra-github)
   - [gh ado2gh — Migrazione da Azure DevOps](#gh-ado2gh-migrazione-da-azure-devops)
   - [gh bbs2gh — Migrazione da Bitbucket Server](#gh-bbs2gh-migrazione-da-bitbucket-server)
   - [Cosa Migra GEI e Cosa No](#cosa-migra-gei)
9. [Mannequin e Mapping degli Utenti](#mannequin-e-mapping-degli-utenti)
   - [Processo di Reclaiming](#processo-di-reclaiming)
   - [Reclaiming in Massa con CSV](#reclaiming-in-massa-con-csv)
   - [Enterprise Managed Users (EMU)](#enterprise-managed-users)
10. [GitHub Actions Importer](#github-actions-importer)
    - [Installazione e Configurazione](#installazione-e-configurazione-actions-importer)
    - [Comando audit](#comando-audit)
    - [Comando forecast](#comando-forecast)
    - [Comando dry-run](#comando-dry-run)
    - [Comando migrate](#comando-migrate-actions-importer)
11. [Migrazione da Jenkins a GitHub Actions](#migrazione-da-jenkins-a-github-actions)
    - [Mapping dei Concetti Jenkins](#mapping-concetti-jenkins)
    - [Conversione Jenkinsfile](#conversione-jenkinsfile)
    - [Mapping dei Plugin Jenkins](#mapping-plugin-jenkins)
12. [Migrazione da CircleCI e Travis CI](#migrazione-da-circleci-e-travis-ci)
    - [Migrazione da CircleCI](#migrazione-da-circleci)
    - [Migrazione da Travis CI](#migrazione-da-travis-ci)
13. [Pulizia Pre-Migrazione del Repository](#pulizia-pre-migrazione)
    - [BFG Repo Cleaner](#bfg-repo-cleaner)
    - [git-filter-repo](#git-filter-repo)
    - [Rimozione Segreti dalla Storia](#rimozione-segreti-dalla-storia)
14. [Migrazione Git LFS Approfondita](#migrazione-git-lfs-approfondita)
    - [Analisi Pre-Migrazione LFS](#analisi-pre-migrazione-lfs)
    - [Strategia di Tracking con .gitattributes](#strategia-tracking-gitattributes)
    - [Ottimizzazione Costi e Bandwidth](#ottimizzazione-costi-bandwidth-lfs)
15. [Gestione Segreti nella Migrazione](#gestione-segreti-nella-migrazione)
    - [Livelli di Segreti GitHub](#livelli-segreti-github)
    - [Migrazione da Altre Piattaforme](#migrazione-segreti-da-altre-piattaforme)
    - [OIDC e Credenziali Effimere](#oidc-credenziali-effimere)
    - [Rotazione Post-Migrazione](#rotazione-post-migrazione)
16. [Migrazione Webhook e Integrazioni](#migrazione-webhook-e-integrazioni)
    - [Riconfigurazione Slack](#riconfigurazione-slack)
    - [Riconfigurazione Jira](#riconfigurazione-jira)
    - [Riconfigurazione SonarQube](#riconfigurazione-sonarqube)
    - [GitHub Apps vs Webhook Tradizionali](#github-apps-vs-webhook)
17. [Strategie di Rollback e Coesistenza](#strategie-di-rollback)
    - [Periodo di Dual-Run](#periodo-dual-run)
    - [Piano di Emergenza](#piano-emergenza)
18. [Checklist di Migrazione](#checklist-di-migrazione)
19. [URL Redirects e Comunicazione al Team](#url-redirects-e-comunicazione)
20. [Validazione Post-Migrazione](#validazione-post-migrazione)
21. [Errori Comuni e Come Evitarli](#errori-comuni)
22. [Riepilogo](#riepilogo)

---

## Introduzione

La migrazione da una piattaforma di hosting del codice a un'altra è uno dei progetti più rischiosi e delicati che un team di sviluppo possa affrontare. Non si tratta semplicemente di spostare repository Git: bisogna migrare la storia dei commit, le issue, le pull/merge request con i loro commenti e review, le pipeline CI/CD, i segreti, le configurazioni, le integrazioni con strumenti esterni, le permission, e — forse la cosa più importante — le abitudini e i processi del team.

Una migrazione mal gestita può causare perdita di dati, interruzione del lavoro, regressione nelle pipeline CI/CD, e frustrazione generalizzata nel team. Al contrario, una migrazione ben pianificata è un'opportunità per rivedere e migliorare i processi, eliminare il debito tecnico, e standardizzare le pratiche di sviluppo.

Questa guida copre la migrazione a GitHub dalle piattaforme più comuni: GitLab, Bitbucket, Azure DevOps e SVN. Per ciascuna piattaforma, esamineremo la migrazione dei repository, delle pipeline CI/CD, delle issue e dei progetti, con comandi specifici, mapping delle funzionalità, e soluzioni ai problemi più comuni.

Le ragioni per migrare a GitHub sono molteplici: ecosistema di integrazioni più ampio, GitHub Actions come piattaforma CI/CD unificata, GitHub Copilot e Codespaces per produttività del team, community e visibilità per progetti open source, o semplicemente la standardizzazione su una singola piattaforma all'interno dell'organizzazione.

---

## Pianificazione della Migrazione

### Fasi della Migrazione

```
Fase 1: Inventario e Assessment (1-2 settimane)
  ├── Catalogare tutti i repository
  ├── Identificare le dipendenze tra repository
  ├── Mappare le pipeline CI/CD
  ├── Inventariare segreti e variabili d'ambiente
  ├── Documentare le integrazioni esterne
  └── Definire la priorità di migrazione

Fase 2: Preparazione (1-2 settimane)
  ├── Creare l'organizzazione GitHub
  ├── Configurare SSO e permessi
  ├── Preparare i template per repository
  ├── Scrivere gli script di migrazione
  ├── Configurare i redirect DNS se necessario
  └── Pianificare la formazione del team

Fase 3: Migrazione Pilota (1 settimana)
  ├── Migrare 2-3 repository non critici
  ├── Convertire le pipeline CI/CD
  ├── Testare end-to-end
  ├── Raccogliere feedback dal team
  └── Iterare sugli script di migrazione

Fase 4: Migrazione in Massa (2-4 settimane)
  ├── Migrare per batch (5-10 repository alla volta)
  ├── Validare ogni batch
  ├── Aggiornare le integrazioni
  └── Comunicare il progresso al team

Fase 5: Decommissioning (2-4 settimane)
  ├── Periodo di coesistenza (entrambe le piattaforme attive)
  ├── Redirect degli URL vecchi
  ├── Archiviare i repository sulla vecchia piattaforma
  └── Disattivare la vecchia piattaforma
```

### Script di Inventario

```bash
#!/bin/bash
# inventory.sh - Inventario repository dalla piattaforma sorgente

# === GitLab ===
gitlab_inventory() {
  echo "=== Inventario GitLab ==="
  GITLAB_URL="${GITLAB_URL:-https://gitlab.com}"
  GITLAB_TOKEN="${GITLAB_TOKEN:?Set GITLAB_TOKEN}"

  curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
    "$GITLAB_URL/api/v4/projects?membership=true&per_page=100&page=1" \
    | jq -r '.[] | [
      .id,
      .path_with_namespace,
      .default_branch,
      .visibility,
      (.statistics.repository_size // 0 | . / 1048576 | floor | tostring) + "MB",
      (.statistics.commit_count // 0 | tostring) + " commits",
      .last_activity_at
    ] | @tsv' | column -t -s $'\t'
}

# === Bitbucket ===
bitbucket_inventory() {
  echo "=== Inventario Bitbucket ==="
  BB_WORKSPACE="${BB_WORKSPACE:?Set BB_WORKSPACE}"
  BB_USER="${BB_USER:?Set BB_USER}"
  BB_APP_PASSWORD="${BB_APP_PASSWORD:?Set BB_APP_PASSWORD}"

  curl -s -u "$BB_USER:$BB_APP_PASSWORD" \
    "https://api.bitbucket.org/2.0/repositories/$BB_WORKSPACE?pagelen=100" \
    | jq -r '.values[] | [
      .slug,
      .mainbranch.name // "N/A",
      .is_private | if . then "private" else "public" end,
      .size | . / 1048576 | floor | tostring + "MB",
      .updated_on
    ] | @tsv' | column -t -s $'\t'
}

# === Azure DevOps ===
azdevops_inventory() {
  echo "=== Inventario Azure DevOps ==="
  AZ_ORG="${AZ_ORG:?Set AZ_ORG}"
  AZ_PROJECT="${AZ_PROJECT:?Set AZ_PROJECT}"
  AZ_PAT="${AZ_PAT:?Set AZ_PAT}"

  curl -s -u ":$AZ_PAT" \
    "https://dev.azure.com/$AZ_ORG/$AZ_PROJECT/_apis/git/repositories?api-version=7.0" \
    | jq -r '.value[] | [
      .name,
      .defaultBranch // "N/A" | sub("refs/heads/";""),
      .size | . / 1048576 | floor | tostring + "MB",
      .project.name
    ] | @tsv' | column -t -s $'\t'
}

# Eseguire l'inventario appropriato
case "${1:-gitlab}" in
  gitlab) gitlab_inventory ;;
  bitbucket) bitbucket_inventory ;;
  azure) azdevops_inventory ;;
  *) echo "Uso: $0 {gitlab|bitbucket|azure}" ;;
esac
```

---

## Migrazione da GitLab

### Migrazione Repository GitLab

#### GitHub Importer (Interfaccia Web)

Il modo più semplice per migrare un singolo repository è usare l'importer integrato di GitHub:

```
1. github.com/new/import
2. Inserire l'URL del repository GitLab
3. Inserire credenziali GitLab (username + PAT con scope read_repository)
4. Scegliere il nome del repository su GitHub
5. Cliccare "Begin import"
```

Limitazioni dell'importer web: non migra pipeline CI/CD, non migra issue e MR con commenti, non gestisce repository molto grandi (>1 GB).

#### Migrazione via Command Line

```bash
#!/bin/bash
# migrate-gitlab-repo.sh

GITLAB_URL="${GITLAB_URL:-https://gitlab.com}"
GITLAB_TOKEN="${GITLAB_TOKEN:?}"
GITHUB_ORG="${GITHUB_ORG:?}"

migrate_repo() {
  local gitlab_project="$1"  # es. "gruppo/progetto"
  local github_repo="$2"     # es. "nome-progetto"

  echo "=== Migrazione: $gitlab_project -> $GITHUB_ORG/$github_repo ==="

  # 1. Clone bare dal GitLab
  echo "Cloning from GitLab..."
  git clone --bare "https://oauth2:${GITLAB_TOKEN}@${GITLAB_URL#https://}/${gitlab_project}.git" \
    "/tmp/migration-${github_repo}"
  cd "/tmp/migration-${github_repo}"

  # 2. Verificare i branch e i tag
  echo "Branch trovati:"
  git branch -a
  echo ""
  echo "Tag trovati:"
  git tag -l
  echo ""

  # 3. Verificare LFS
  if git lfs ls-files 2>/dev/null | head -1 > /dev/null; then
    echo "Repository usa Git LFS. Scaricando oggetti LFS..."
    git lfs fetch --all "https://oauth2:${GITLAB_TOKEN}@${GITLAB_URL#https://}/${gitlab_project}.git"
  fi

  # 4. Creare il repository su GitHub
  echo "Creando repository su GitHub..."
  gh repo create "${GITHUB_ORG}/${github_repo}" \
    --private \
    --description "Migrato da GitLab: ${gitlab_project}" \
    || echo "Repository già esistente, continuo..."

  # 5. Push mirror su GitHub
  echo "Pushing to GitHub..."
  git push --mirror "https://github.com/${GITHUB_ORG}/${github_repo}.git"

  # 6. Push LFS se presente
  if git lfs ls-files 2>/dev/null | head -1 > /dev/null; then
    echo "Pushing LFS objects..."
    git lfs push --all "https://github.com/${GITHUB_ORG}/${github_repo}.git"
  fi

  # 7. Pulizia
  rm -rf "/tmp/migration-${github_repo}"

  echo "=== Migrazione completata: $github_repo ==="
  echo ""
}

# Migrazione singola
# migrate_repo "gruppo/progetto" "nome-progetto"

# Migrazione batch da file CSV
# Formato CSV: gitlab_path,github_name
while IFS=',' read -r gitlab_path github_name; do
  migrate_repo "$gitlab_path" "$github_name"
done < repos-to-migrate.csv
```

### Migrazione CI/CD GitLab

La conversione delle pipeline GitLab CI/CD (`.gitlab-ci.yml`) a GitHub Actions richiede comprensione delle differenze tra i due sistemi.

#### Mapping dei Concetti

| GitLab CI/CD | GitHub Actions |
|-------------|----------------|
| `.gitlab-ci.yml` | `.github/workflows/*.yml` |
| `stages` | Job dependencies / `needs` |
| `jobs` | `jobs` |
| `script` | `steps` con `run` |
| `image` | `container` o `runs-on` |
| `services` | `services` |
| `variables` | `env` |
| `CI_* variables` | `github.*` context |
| `rules/only/except` | `on` triggers + `if` conditions |
| `cache` | `actions/cache` |
| `artifacts` | `actions/upload-artifact` |
| `include` | Reusable workflows / composite actions |
| `extends` | Reusable workflows |
| `environment` | `environment` |
| `needs` | `needs` |
| `parallel` | `strategy.matrix` |
| `trigger` | `workflow_dispatch` / `repository_dispatch` |

#### Esempio Completo di Conversione

**GitLab CI/CD originale:**

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - test
  - build
  - deploy

variables:
  NODE_VERSION: "20"
  DOCKER_REGISTRY: "registry.gitlab.com"

default:
  image: node:${NODE_VERSION}
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
      - .npm/
  before_script:
    - npm ci --cache .npm --prefer-offline

lint:
  stage: lint
  script:
    - npm run lint
    - npm run type-check
  rules:
    - if: $CI_MERGE_REQUEST_ID
    - if: $CI_COMMIT_BRANCH == "main"

test:unit:
  stage: test
  script:
    - npm run test:unit -- --coverage
  coverage: /All files[^|]*\|[^|]*\s+([\d\.]+)/
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
    paths:
      - coverage/
    expire_in: 1 week
  rules:
    - if: $CI_MERGE_REQUEST_ID
    - if: $CI_COMMIT_BRANCH == "main"

test:integration:
  stage: test
  services:
    - postgres:16-alpine
    - redis:7-alpine
  variables:
    POSTGRES_DB: test
    POSTGRES_USER: test
    POSTGRES_PASSWORD: test
    DATABASE_URL: "postgresql://test:test@postgres:5432/test"
    REDIS_URL: "redis://redis:6379"
  script:
    - npm run test:integration
  rules:
    - if: $CI_MERGE_REQUEST_ID
    - if: $CI_COMMIT_BRANCH == "main"

build:docker:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - |
      if [ "$CI_COMMIT_BRANCH" == "main" ]; then
        docker tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA $CI_REGISTRY_IMAGE:latest
        docker push $CI_REGISTRY_IMAGE:latest
      fi
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy:staging:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: staging
    url: https://staging.example.com
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - kubectl rollout status deployment/app
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy:production:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: production
    url: https://example.com
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - kubectl rollout status deployment/app
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
  when: manual
```

**GitHub Actions equivalente:**

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
    tags: ['v*.*.*']
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci
      - run: npm run lint
      - run: npm run type-check

  test-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci
      - run: npm run test:unit -- --coverage

      - uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/
          retention-days: 7

  test-integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    env:
      DATABASE_URL: postgresql://test:test@localhost:5432/test
      REDIS_URL: redis://localhost:6379
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci
      - run: npm run test:integration

  build-docker:
    needs: [lint, test-unit, test-integration]
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build-docker
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: azure/k8s-set-context@v4
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}

      - run: |
          kubectl set image deployment/app \
            app=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}
          kubectl rollout status deployment/app --timeout=300s

  deploy-production:
    needs: build-docker
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: azure/k8s-set-context@v4
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_PRODUCTION }}

      - run: |
          TAG="${GITHUB_REF#refs/tags/}"
          kubectl set image deployment/app \
            app=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${TAG}
          kubectl rollout status deployment/app --timeout=300s
```

#### Mapping delle Variabili CI

| GitLab CI Variable | GitHub Actions Equivalent |
|-------------------|--------------------------|
| `CI_COMMIT_SHA` | `${{ github.sha }}` |
| `CI_COMMIT_SHORT_SHA` | `${{ github.sha }}` (primi 7 caratteri con substring) |
| `CI_COMMIT_REF_NAME` | `${{ github.ref_name }}` |
| `CI_COMMIT_BRANCH` | `${{ github.ref_name }}` (per push) |
| `CI_COMMIT_TAG` | `${{ github.ref_name }}` (per tag push) |
| `CI_MERGE_REQUEST_ID` | `${{ github.event.pull_request.number }}` |
| `CI_MERGE_REQUEST_SOURCE_BRANCH_NAME` | `${{ github.head_ref }}` |
| `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` | `${{ github.base_ref }}` |
| `CI_PROJECT_NAME` | `${{ github.event.repository.name }}` |
| `CI_PROJECT_PATH` | `${{ github.repository }}` |
| `CI_REGISTRY_IMAGE` | `ghcr.io/${{ github.repository }}` |
| `CI_REGISTRY_USER` | `${{ github.actor }}` |
| `CI_REGISTRY_PASSWORD` | `${{ secrets.GITHUB_TOKEN }}` |
| `CI_JOB_TOKEN` | `${{ secrets.GITHUB_TOKEN }}` |
| `CI_PIPELINE_ID` | `${{ github.run_id }}` |
| `CI_PIPELINE_URL` | `${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}` |

### Migrazione Issue GitLab

```python
#!/usr/bin/env python3
# migrate-gitlab-issues.py
"""
Migra le issue da GitLab a GitHub, preservando:
- Titolo e descrizione
- Labels
- Milestone
- Commenti
- Stato (open/closed)
- Autore originale (come menzione nel body)
"""

import requests
import time
import json
import sys

GITLAB_URL = "https://gitlab.com"
GITLAB_TOKEN = "glpat-xxxxx"
GITLAB_PROJECT_ID = "12345"

GITHUB_ORG = "my-org"
GITHUB_REPO = "my-repo"
GITHUB_TOKEN = "ghp_xxxxx"

gitlab_headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
github_headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_gitlab_issues():
    """Recupera tutte le issue da GitLab."""
    issues = []
    page = 1
    while True:
        resp = requests.get(
            f"{GITLAB_URL}/api/v4/projects/{GITLAB_PROJECT_ID}/issues",
            headers=gitlab_headers,
            params={"per_page": 100, "page": page, "sort": "asc"}
        )
        batch = resp.json()
        if not batch:
            break
        issues.extend(batch)
        page += 1
        print(f"  Recuperate {len(issues)} issue da GitLab...")
    return issues

def get_gitlab_comments(issue_iid):
    """Recupera i commenti di una issue GitLab."""
    resp = requests.get(
        f"{GITLAB_URL}/api/v4/projects/{GITLAB_PROJECT_ID}/issues/{issue_iid}/notes",
        headers=gitlab_headers,
        params={"per_page": 100, "sort": "asc"}
    )
    return [n for n in resp.json() if not n.get("system", False)]

def create_github_issue(title, body, labels, state):
    """Crea una issue su GitHub."""
    data = {
        "title": title,
        "body": body,
        "labels": labels
    }
    resp = requests.post(
        f"https://api.github.com/repos/{GITHUB_ORG}/{GITHUB_REPO}/issues",
        headers=github_headers,
        json=data
    )

    if resp.status_code == 201:
        issue = resp.json()
        issue_number = issue["number"]

        # Chiudere se necessario
        if state == "closed":
            requests.patch(
                f"https://api.github.com/repos/{GITHUB_ORG}/{GITHUB_REPO}/issues/{issue_number}",
                headers=github_headers,
                json={"state": "closed"}
            )

        return issue_number
    else:
        print(f"  ERRORE creazione issue: {resp.status_code} {resp.text}")
        return None

def create_github_comment(issue_number, body):
    """Aggiunge un commento a una issue GitHub."""
    requests.post(
        f"https://api.github.com/repos/{GITHUB_ORG}/{GITHUB_REPO}/issues/{issue_number}/comments",
        headers=github_headers,
        json={"body": body}
    )

def migrate():
    print("=== Migrazione Issue da GitLab a GitHub ===")
    print(f"Sorgente: {GITLAB_URL}/projects/{GITLAB_PROJECT_ID}")
    print(f"Destinazione: github.com/{GITHUB_ORG}/{GITHUB_REPO}")
    print()

    # Recuperare le issue
    print("Recupero issue da GitLab...")
    issues = get_gitlab_issues()
    print(f"Trovate {len(issues)} issue")

    # Creare le label su GitHub (se non esistono)
    existing_labels = set()
    for issue in issues:
        for label in issue.get("labels", []):
            if label not in existing_labels:
                requests.post(
                    f"https://api.github.com/repos/{GITHUB_ORG}/{GITHUB_REPO}/labels",
                    headers=github_headers,
                    json={"name": label, "color": "ededed"}
                )
                existing_labels.add(label)

    # Migrare le issue
    migrated = 0
    for issue in issues:
        # Costruire il body con metadati originali
        body_parts = [
            f"> **Migrata da GitLab** | Issue originale: #{issue['iid']}",
            f"> Autore originale: @{issue['author']['username']}",
            f"> Data creazione: {issue['created_at']}",
            "",
            issue.get("description", "") or "*Nessuna descrizione*"
        ]
        body = "\n".join(body_parts)

        # Creare la issue
        gh_issue_num = create_github_issue(
            title=issue["title"],
            body=body,
            labels=issue.get("labels", []),
            state=issue["state"]
        )

        if gh_issue_num:
            # Migrare i commenti
            comments = get_gitlab_comments(issue["iid"])
            for comment in comments:
                comment_body = (
                    f"> Commento originale di @{comment['author']['username']} "
                    f"({comment['created_at']})\n\n"
                    f"{comment['body']}"
                )
                create_github_comment(gh_issue_num, comment_body)
                time.sleep(0.5)  # Rate limiting

            migrated += 1
            print(f"  [{migrated}/{len(issues)}] GitLab #{issue['iid']} -> GitHub #{gh_issue_num}")

        time.sleep(1)  # Rate limiting

    print(f"\n=== Migrazione completata: {migrated}/{len(issues)} issue migrate ===")

if __name__ == "__main__":
    migrate()
```

---

## Migrazione da Bitbucket

### Migrazione Repository Bitbucket

```bash
#!/bin/bash
# migrate-bitbucket-repos.sh

BB_WORKSPACE="${BB_WORKSPACE:?}"
BB_USER="${BB_USER:?}"
BB_APP_PASSWORD="${BB_APP_PASSWORD:?}"
GITHUB_ORG="${GITHUB_ORG:?}"

migrate_bb_repo() {
  local repo_slug="$1"
  local github_name="${2:-$repo_slug}"

  echo "=== Migrazione: bitbucket:${BB_WORKSPACE}/${repo_slug} -> github:${GITHUB_ORG}/${github_name} ==="

  # Clone bare
  git clone --bare \
    "https://${BB_USER}:${BB_APP_PASSWORD}@bitbucket.org/${BB_WORKSPACE}/${repo_slug}.git" \
    "/tmp/bb-migration-${repo_slug}"

  cd "/tmp/bb-migration-${repo_slug}"

  # Verificare la dimensione
  SIZE=$(du -sh . | cut -f1)
  echo "Dimensione repository: $SIZE"

  # Creare repository su GitHub
  gh repo create "${GITHUB_ORG}/${github_name}" --private \
    --description "Migrato da Bitbucket: ${BB_WORKSPACE}/${repo_slug}"

  # Push
  git push --mirror "https://github.com/${GITHUB_ORG}/${github_name}.git"

  # Pulizia
  cd /
  rm -rf "/tmp/bb-migration-${repo_slug}"

  echo "=== Completato: ${github_name} ==="
}

# Elencare tutti i repository e migrare
curl -s -u "$BB_USER:$BB_APP_PASSWORD" \
  "https://api.bitbucket.org/2.0/repositories/$BB_WORKSPACE?pagelen=100" \
  | jq -r '.values[].slug' \
  | while read -r slug; do
      migrate_bb_repo "$slug"
    done
```

### Migrazione Pipelines Bitbucket a GitHub Actions

#### Mapping dei Concetti

| Bitbucket Pipelines | GitHub Actions |
|--------------------|----------------|
| `bitbucket-pipelines.yml` | `.github/workflows/*.yml` |
| `pipelines.default` | `on: push` |
| `pipelines.branches.main` | `on: push: branches: [main]` |
| `pipelines.pull-requests` | `on: pull_request` |
| `pipelines.tags` | `on: push: tags` |
| `step` | `steps` item |
| `image` | `container` |
| `services` | `services` |
| `caches` | `actions/cache` |
| `artifacts` | `actions/upload-artifact` |
| `deployment` | `environment` |
| `pipe` | GitHub Action (marketplace) |
| `parallel` | Jobs paralleli |
| `BITBUCKET_*` variables | `github.*` context |

#### Conversione Esempio

**Bitbucket Pipelines originale:**

```yaml
# bitbucket-pipelines.yml
image: node:20

definitions:
  caches:
    npm: ~/.npm
  services:
    postgres:
      image: postgres:16
      variables:
        POSTGRES_DB: test
        POSTGRES_USER: test
        POSTGRES_PASSWORD: test
    redis:
      image: redis:7

pipelines:
  default:
    - parallel:
      - step:
          name: Lint
          caches:
            - npm
          script:
            - npm ci
            - npm run lint

      - step:
          name: Unit Tests
          caches:
            - npm
          script:
            - npm ci
            - npm run test:unit -- --coverage
          artifacts:
            - coverage/**

    - step:
        name: Integration Tests
        caches:
          - npm
        services:
          - postgres
          - redis
        script:
          - npm ci
          - npm run test:integration

  branches:
    main:
      - step:
          name: Build & Push Docker
          services:
            - docker
          script:
            - docker build -t $DOCKER_REGISTRY/$BITBUCKET_REPO_SLUG:$BITBUCKET_COMMIT .
            - docker push $DOCKER_REGISTRY/$BITBUCKET_REPO_SLUG:$BITBUCKET_COMMIT

      - step:
          name: Deploy to Staging
          deployment: staging
          script:
            - pipe: atlassian/kubectl-run:3.0.0
              variables:
                KUBE_CONFIG: $KUBE_CONFIG
                KUBECTL_COMMAND: "set image deployment/app app=$DOCKER_REGISTRY/$BITBUCKET_REPO_SLUG:$BITBUCKET_COMMIT"

  tags:
    'v*':
      - step:
          name: Deploy to Production
          deployment: production
          trigger: manual
          script:
            - pipe: atlassian/kubectl-run:3.0.0
              variables:
                KUBE_CONFIG: $KUBE_CONFIG_PROD
                KUBECTL_COMMAND: "set image deployment/app app=$DOCKER_REGISTRY/$BITBUCKET_REPO_SLUG:$BITBUCKET_TAG"
```

**GitHub Actions equivalente:**

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint

  test-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run test:unit -- --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  test-integration:
    runs-on: ubuntu-latest
    needs: [lint, test-unit]
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
      redis:
        image: redis:7
        ports: ['6379:6379']
    env:
      DATABASE_URL: postgresql://test:test@localhost:5432/test
      REDIS_URL: redis://localhost:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run test:integration

  build-push:
    needs: test-integration
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}

  deploy-staging:
    needs: build-push
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: azure/k8s-set-context@v4
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG }}
      - run: kubectl set image deployment/app app=ghcr.io/${{ github.repository }}:${{ github.sha }}

  deploy-production:
    needs: build-push
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: azure/k8s-set-context@v4
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_PROD }}
      - run: kubectl set image deployment/app app=ghcr.io/${{ github.repository }}:${{ github.ref_name }}
```

---

## Migrazione da Azure DevOps

### Migrazione Repository Azure DevOps

```bash
#!/bin/bash
# migrate-azure-repos.sh

AZ_ORG="${AZ_ORG:?}"
AZ_PROJECT="${AZ_PROJECT:?}"
AZ_PAT="${AZ_PAT:?}"
GITHUB_ORG="${GITHUB_ORG:?}"

# Codificare il PAT per l'URL
AZ_PAT_ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$AZ_PAT'))")

# Elencare tutti i repository
REPOS=$(curl -s -u ":${AZ_PAT}" \
  "https://dev.azure.com/${AZ_ORG}/${AZ_PROJECT}/_apis/git/repositories?api-version=7.0" \
  | jq -r '.value[] | .name')

for repo in $REPOS; do
  echo "=== Migrazione: Azure DevOps ${repo} ==="

  # Clone bare
  git clone --bare \
    "https://${AZ_PAT_ENCODED}@dev.azure.com/${AZ_ORG}/${AZ_PROJECT}/_git/${repo}" \
    "/tmp/az-migration-${repo}"

  cd "/tmp/az-migration-${repo}"

  # Creare su GitHub
  gh repo create "${GITHUB_ORG}/${repo}" --private

  # Push
  git push --mirror "https://github.com/${GITHUB_ORG}/${repo}.git"

  cd /
  rm -rf "/tmp/az-migration-${repo}"

  echo "=== Completato: ${repo} ==="
done
```

### Migrazione Pipelines Azure DevOps a GitHub Actions

#### Mapping dei Concetti

| Azure DevOps Pipelines | GitHub Actions |
|----------------------|----------------|
| `azure-pipelines.yml` | `.github/workflows/*.yml` |
| `trigger` | `on: push` |
| `pr` | `on: pull_request` |
| `schedules` | `on: schedule` |
| `stages` | Jobs con `needs` |
| `jobs` | `jobs` |
| `steps` | `steps` |
| `task@version` | `uses: action@version` |
| `pool.vmImage` | `runs-on` |
| `variables` | `env` / `vars` / `secrets` |
| `parameters` | `workflow_dispatch.inputs` |
| `condition` | `if` |
| `template` | Reusable workflows |
| `resources.containers` | `services` / `container` |
| `$(Build.SourceVersion)` | `${{ github.sha }}` |
| `$(Build.BuildId)` | `${{ github.run_id }}` |
| `$(System.PullRequest.PullRequestId)` | `${{ github.event.pull_request.number }}` |

#### Conversione Esempio

**Azure DevOps Pipeline originale:**

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
  paths:
    exclude:
      - docs/*
      - README.md

pr:
  branches:
    include:
      - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: app-secrets
  - name: nodeVersion
    value: '20'

stages:
  - stage: Build
    jobs:
      - job: BuildAndTest
        steps:
          - task: NodeTool@0
            inputs:
              versionSpec: '$(nodeVersion)'

          - task: Cache@2
            inputs:
              key: 'npm | "$(Agent.OS)" | package-lock.json'
              path: '$(Pipeline.Workspace)/.npm'

          - script: npm ci
            displayName: 'Install dependencies'

          - script: npm run lint
            displayName: 'Lint'

          - script: npm run test -- --coverage
            displayName: 'Test'

          - task: PublishCodeCoverageResults@2
            inputs:
              summaryFileLocation: 'coverage/cobertura-coverage.xml'

          - task: Docker@2
            condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
            inputs:
              containerRegistry: 'docker-connection'
              repository: 'myapp'
              command: 'buildAndPush'
              Dockerfile: 'Dockerfile'
              tags: |
                $(Build.BuildId)
                latest

  - stage: DeployStaging
    dependsOn: Build
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployStaging
        environment: staging
        strategy:
          runOnce:
            deploy:
              steps:
                - task: KubernetesManifest@1
                  inputs:
                    action: deploy
                    kubernetesServiceConnection: 'k8s-staging'
                    manifests: 'k8s/staging/'

  - stage: DeployProduction
    dependsOn: DeployStaging
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployProduction
        environment: production
        strategy:
          runOnce:
            deploy:
              steps:
                - task: KubernetesManifest@1
                  inputs:
                    action: deploy
                    kubernetesServiceConnection: 'k8s-production'
                    manifests: 'k8s/production/'
```

**GitHub Actions equivalente:**

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD

on:
  push:
    branches: [main]
    paths-ignore:
      - 'docs/**'
      - 'README.md'
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci
      - run: npm run lint
      - run: npm run test -- --coverage

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage
          path: coverage/

  build-docker:
    needs: build-and-test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:${{ github.run_id }}
            ghcr.io/${{ github.repository }}:latest

  deploy-staging:
    needs: build-docker
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: azure/k8s-set-context@v4
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}
      - run: kubectl apply -f k8s/staging/

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: azure/k8s-set-context@v4
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_PRODUCTION }}
      - run: kubectl apply -f k8s/production/
```

### Migrazione Boards Azure DevOps a GitHub Projects

Azure DevOps Boards e GitHub Projects hanno filosofie diverse. Azure DevOps usa Work Items strutturati (Epics, Features, User Stories, Tasks, Bugs), mentre GitHub Projects usa Issue con viste personalizzabili.

```bash
#!/bin/bash
# migrate-azure-workitems.sh
# Migra Work Items da Azure DevOps a GitHub Issues

AZ_ORG="${AZ_ORG:?}"
AZ_PROJECT="${AZ_PROJECT:?}"
AZ_PAT="${AZ_PAT:?}"
GITHUB_ORG="${GITHUB_ORG:?}"
GITHUB_REPO="${GITHUB_REPO:?}"

# Mapping dei tipi di Work Item a Labels GitHub
declare -A TYPE_LABELS=(
  ["Bug"]="bug"
  ["User Story"]="user-story"
  ["Feature"]="feature"
  ["Task"]="task"
  ["Epic"]="epic"
)

# Mapping degli stati
declare -A STATE_MAP=(
  ["New"]="open"
  ["Active"]="open"
  ["Resolved"]="closed"
  ["Closed"]="closed"
  ["Done"]="closed"
)

# Recuperare tutti i work items
QUERY='{"query": "Select [System.Id], [System.Title], [System.State], [System.WorkItemType], [System.Description], [System.AssignedTo] From WorkItems Where [System.TeamProject] = '"'"''"$AZ_PROJECT"''"'"' Order By [System.Id] Asc"}'

WORK_ITEMS=$(curl -s -u ":${AZ_PAT}" \
  -H "Content-Type: application/json" \
  -d "$QUERY" \
  "https://dev.azure.com/${AZ_ORG}/${AZ_PROJECT}/_apis/wit/wiql?api-version=7.0")

IDS=$(echo "$WORK_ITEMS" | jq -r '.workItems[].id')

for id in $IDS; do
  # Recuperare dettagli del work item
  WI=$(curl -s -u ":${AZ_PAT}" \
    "https://dev.azure.com/${AZ_ORG}/${AZ_PROJECT}/_apis/wit/workitems/${id}?api-version=7.0&\$expand=all")

  TITLE=$(echo "$WI" | jq -r '.fields["System.Title"]')
  TYPE=$(echo "$WI" | jq -r '.fields["System.WorkItemType"]')
  STATE=$(echo "$WI" | jq -r '.fields["System.State"]')
  DESCRIPTION=$(echo "$WI" | jq -r '.fields["System.Description"] // ""')
  ASSIGNED=$(echo "$WI" | jq -r '.fields["System.AssignedTo"].displayName // "Non assegnato"')

  LABEL="${TYPE_LABELS[$TYPE]:-other}"
  GH_STATE="${STATE_MAP[$STATE]:-open}"

  # Creare issue su GitHub
  BODY="**Migrato da Azure DevOps Work Item #${id}**
**Tipo**: ${TYPE}
**Assegnato a**: ${ASSIGNED}
**Stato originale**: ${STATE}

---

${DESCRIPTION}"

  gh issue create \
    --repo "${GITHUB_ORG}/${GITHUB_REPO}" \
    --title "[${TYPE}] ${TITLE}" \
    --body "$BODY" \
    --label "$LABEL"

  if [ "$GH_STATE" = "closed" ]; then
    ISSUE_NUM=$(gh issue list --repo "${GITHUB_ORG}/${GITHUB_REPO}" --limit 1 --json number -q '.[0].number')
    gh issue close "$ISSUE_NUM" --repo "${GITHUB_ORG}/${GITHUB_REPO}"
  fi

  echo "Migrato: #${id} - ${TITLE} (${TYPE}, ${STATE})"
  sleep 1  # Rate limiting
done
```

---

## Migrazione da SVN a Git

La migrazione da SVN a Git è la più complessa perché i due sistemi hanno modelli fondamentalmente diversi. SVN è centralizzato con una struttura trunk/branches/tags, mentre Git è distribuito con branch leggeri e una storia basata su grafi.

### Approccio con git-svn

`git-svn` è un ponte bidirezionale tra Git e SVN. Per la migrazione, lo usiamo per convertire la storia SVN in storia Git.

```bash
#!/bin/bash
# migrate-svn-to-git.sh

SVN_URL="${SVN_URL:?Set SVN_URL (es. https://svn.example.com/svn/project)}"
GITHUB_ORG="${GITHUB_ORG:?}"
GITHUB_REPO="${GITHUB_REPO:?}"

# Passo 1: Creare il file di mapping degli autori
# SVN usa username, Git usa "Nome <email>"
echo "=== Passo 1: Generare mapping autori ==="

# Estrarre gli autori SVN
svn log --quiet "$SVN_URL" | \
  grep -E "^r" | \
  awk '{print $3}' | \
  sort -u | \
  while read author; do
    echo "$author = $author <$author@azienda.com>"
  done > authors.txt

echo "File authors.txt generato. MODIFICARE con i nomi reali prima di continuare!"
echo "Formato: svn-username = Nome Cognome <email@reale.com>"
echo ""
cat authors.txt
echo ""
read -p "Premi Enter dopo aver modificato authors.txt..."

# Passo 2: Clone con git-svn
echo "=== Passo 2: Clonare da SVN (può richiedere ore per repository grandi) ==="

# Layout standard SVN: trunk, branches, tags
git svn clone "$SVN_URL" \
  --stdlayout \
  --authors-file=authors.txt \
  --no-metadata \
  --prefix="" \
  "${GITHUB_REPO}-git"

cd "${GITHUB_REPO}-git"

# Passo 3: Convertire i tag SVN in tag Git
echo "=== Passo 3: Convertire tag SVN in tag Git ==="

for tag in $(git for-each-ref --format='%(refname:short)' refs/remotes/tags); do
  TAG_NAME="${tag#tags/}"
  GIT_COMMITTER_DATE="$(git log -1 --format='%ai' "$tag")" \
  GIT_COMMITTER_EMAIL="$(git log -1 --format='%ae' "$tag")" \
  GIT_COMMITTER_NAME="$(git log -1 --format='%an' "$tag")" \
  git tag -a "$TAG_NAME" -m "Tag $TAG_NAME (da SVN)" "$tag"
  echo "Tag creato: $TAG_NAME"
done

# Passo 4: Convertire i branch SVN in branch Git
echo "=== Passo 4: Convertire branch SVN in branch Git ==="

for branch in $(git for-each-ref --format='%(refname:short)' refs/remotes/ | grep -v tags); do
  BRANCH_NAME="${branch#*/}"
  if [ "$BRANCH_NAME" != "trunk" ]; then
    git branch "$BRANCH_NAME" "refs/remotes/$branch"
    echo "Branch creato: $BRANCH_NAME"
  fi
done

# Rinominare trunk in main
git branch -m trunk main 2>/dev/null || git branch main refs/remotes/trunk

# Passo 5: Pulire i riferimenti SVN
echo "=== Passo 5: Pulizia ==="

git for-each-ref --format='%(refname)' refs/remotes/ | xargs -I {} git update-ref -d {}

# Rimuovere la configurazione svn
git config --remove-section svn-remote.svn 2>/dev/null
rm -rf .git/svn

# Passo 6: Push su GitHub
echo "=== Passo 6: Push su GitHub ==="

gh repo create "${GITHUB_ORG}/${GITHUB_REPO}" --private

git remote add origin "https://github.com/${GITHUB_ORG}/${GITHUB_REPO}.git"
git push -u origin --all
git push origin --tags

echo "=== Migrazione completata! ==="
echo "Repository: https://github.com/${GITHUB_ORG}/${GITHUB_REPO}"
```

### Approccio con svn2git

`svn2git` è uno strumento più automatizzato che gestisce molte delle complessità della conversione.

```bash
# Installare svn2git
# Ubuntu/Debian:
sudo apt-get install git-svn ruby
sudo gem install svn2git

# macOS:
brew install svn2git

# Conversione
svn2git "$SVN_URL" \
  --authors authors.txt \
  --verbose \
  --rootistrunk  # Se il repo non ha la struttura standard trunk/branches/tags

# Con struttura standard
svn2git "$SVN_URL" \
  --authors authors.txt \
  --trunk trunk \
  --branches branches \
  --tags tags \
  --verbose

# Per repository molto grandi, escludere i path non necessari
svn2git "$SVN_URL" \
  --authors authors.txt \
  --exclude "vendor" \
  --exclude "old-releases" \
  --verbose
```

### Preservazione della Storia

Preservare la storia completa è importante per traceability e per strumenti come `git blame` e `git bisect`.

```bash
# Verificare che la storia sia preservata correttamente
echo "=== Verifica post-migrazione ==="

# Contare i commit
SVN_COMMITS=$(svn log --quiet "$SVN_URL" | grep "^r" | wc -l)
GIT_COMMITS=$(git rev-list --count HEAD)
echo "Commit SVN: $SVN_COMMITS"
echo "Commit Git: $GIT_COMMITS"

# I numeri potrebbero non corrispondere esattamente a causa di
# merge e operazioni SVN che non hanno equivalenti diretti in Git

# Verificare gli autori
echo ""
echo "Autori nel repository Git:"
git shortlog -sne | head -20

# Verificare i branch
echo ""
echo "Branch:"
git branch -a

# Verificare i tag
echo ""
echo "Tag:"
git tag -l

# Verificare le date
echo ""
echo "Primo commit:"
git log --reverse --format="%ai %an: %s" | head -1
echo "Ultimo commit:"
git log --format="%ai %an: %s" | head -1

# Verificare i file con git-blame
echo ""
echo "Verifica git blame su un file di esempio:"
git blame --date=short README.md | head -10
```

---

## Migrazione da TFVC a Git

Team Foundation Version Control (TFVC) è il sistema di versionamento centralizzato di Microsoft, utilizzato in Azure DevOps e nel precedente Team Foundation Server (TFS). A differenza di SVN, TFVC ha concetti propri come workspace, shelveset e changeset che non hanno equivalenti diretti in Git. GitHub supporta esclusivamente Git, quindi qualsiasi repository TFVC deve essere convertito prima della migrazione.

### Import tramite Azure DevOps

Azure DevOps offre uno strumento di importazione integrato che converte repository TFVC in repository Git direttamente all'interno della piattaforma. Questo approccio è il più semplice ma ha una limitazione significativa: conserva solo gli ultimi 180 giorni di storia.

```bash
# Passo 1: Verificare la struttura del repository TFVC
# Accedere ad Azure DevOps → Project → Repos → selezionare il repository TFVC
# Identificare la struttura: $/Project/trunk, $/Project/branches, $/Project/releases

# Passo 2: Importare tramite l'interfaccia Azure DevOps
# Azure DevOps → Repos → Import Repository
# Source type: TFVC
# Path: $/NomeProgetto/trunk (o il path principale)
# Max history: 180 days (limitazione dello strumento integrato)
# Risultato: un nuovo repository Git all'interno di Azure DevOps

# Passo 3: Clonare e pushare verso GitHub
AZ_ORG="mia-org"
AZ_PROJECT="mio-progetto"
AZ_REPO="repo-convertito"
GITHUB_ORG="mia-org-github"

git clone "https://dev.azure.com/${AZ_ORG}/${AZ_PROJECT}/_git/${AZ_REPO}" \
  /tmp/tfvc-to-github

cd /tmp/tfvc-to-github

# Creare il repository su GitHub
gh repo create "${GITHUB_ORG}/${AZ_REPO}" --private

# Aggiungere il remote GitHub e pushare
git remote add github "https://github.com/${GITHUB_ORG}/${AZ_REPO}.git"
git push github --all
git push github --tags

echo "Repository TFVC migrato su GitHub via Azure DevOps import"
```

### Migrazione con git-tfs

Per conservare la storia completa oltre i 180 giorni, `git-tfs` è lo strumento raccomandato. Si tratta di un bridge bidirezionale tra Git e TFS/TFVC che permette di clonare repository TFVC in repository Git preservando l'intera cronologia dei changeset.

```bash
# Installazione git-tfs
# Windows (via Chocolatey):
choco install gittfs

# Linux/macOS (via .NET tool):
dotnet tool install -g GitTfs

# Verificare l'installazione
git tfs --version

# === Clone con storia completa ===

# Clone semplice (solo trunk, nessun branch)
git tfs clone \
  "https://dev.azure.com/mia-org" \
  "$/MioProgetto/trunk" \
  /tmp/mio-progetto-git

# Clone con branch
# L'opzione --branches=all tenta di convertire tutti i branch TFVC
git tfs clone \
  --branches=all \
  "https://dev.azure.com/mia-org" \
  "$/MioProgetto" \
  /tmp/mio-progetto-git

# Clone con autori mappati (raccomandato)
# Creare prima il file authors.txt:
# DOMAIN\utente1 = Mario Rossi <mario.rossi@azienda.com>
# DOMAIN\utente2 = Luigi Bianchi <luigi.bianchi@azienda.com>
git tfs clone \
  --authors=authors.txt \
  "https://dev.azure.com/mia-org" \
  "$/MioProgetto/trunk" \
  /tmp/mio-progetto-git

# === Per repository molto grandi ===
# Usare --changeset per iniziare da un changeset specifico
# (utile se la storia completa è troppo grande)
git tfs clone \
  --changeset=50000 \
  "https://dev.azure.com/mia-org" \
  "$/MioProgetto/trunk" \
  /tmp/mio-progetto-git

# Se il clone si interrompe, continuare con fetch
cd /tmp/mio-progetto-git
git tfs fetch
```

### Gestione Branch TFVC

I branch in TFVC funzionano in modo fondamentalmente diverso da Git. In TFVC un branch è una copia fisica di un'intera directory, mentre in Git è un puntatore leggero a un commit. Questa differenza rende la conversione dei branch complessa, specialmente quando ci sono merge relationships tra branch TFVC.

```bash
# Elencare i branch TFVC
git tfs branch --remote

# Inizializzare un singolo branch specifico
git tfs branch --init "$/MioProgetto/branches/release-2.0"

# Verificare lo stato dopo la conversione
cd /tmp/mio-progetto-git

echo "=== Verifica conversione TFVC → Git ==="

# Verificare i branch convertiti
echo "Branch Git creati:"
git branch -a

# Verificare la corrispondenza dei changeset
echo ""
echo "Ultimo changeset convertito:"
git log --oneline -1

# Contare i commit (dovrebbero corrispondere ai changeset)
echo ""
echo "Totale commit Git: $(git rev-list --count HEAD)"

# === Differenze importanti tra TFVC e Git ===
# 1. TFVC rename → Git mostra come delete + add nello stesso commit
# 2. TFVC shelveset → non ha equivalente diretto (usare stash o branch)
# 3. TFVC changeset number → non esiste in Git (usare git log per hash)
# 4. TFVC lock → non esiste in Git (usare branch protection rules)
# 5. TFVC workspace mapping → non necessario in Git

# === Pulizia post-conversione ===
# Rimuovere i metadati git-tfs
git filter-branch -f --msg-filter \
  'sed "s/^git-tfs-id:.*$//"' -- --all

# Rimuovere i remote git-tfs
git remote remove tfs 2>/dev/null

# Push verso GitHub
gh repo create "${GITHUB_ORG}/mio-progetto" --private
git remote add origin "https://github.com/${GITHUB_ORG}/mio-progetto.git"
git push -u origin --all
git push origin --tags
```

#### Tabella di Corrispondenza TFVC → Git

| Concetto TFVC | Equivalente Git/GitHub | Note |
|--------------|----------------------|------|
| Changeset | Commit | I numeri di changeset non sono preservati |
| Workspace | Clone locale | Git non richiede mapping esplicito |
| Shelveset | Stash / Branch temporaneo | Usare `git stash` o branch di feature |
| Lock | Branch protection rules | Protezione a livello di branch, non di file |
| Check-in policy | Pre-commit hooks / GitHub Actions | Validazione tramite hook o CI |
| Label | Tag | `git tag` per marcare versioni specifiche |
| Branch (directory copy) | Branch (puntatore leggero) | Conversione automatica con git-tfs |
| Merge (baseless) | Merge / Rebase | Git richiede un antenato comune |
| Get latest | `git pull` | Equivalente funzionale |
| Check-in | `git commit` + `git push` | Due passi separati in Git |

---

## GitHub Enterprise Importer (GEI) in Dettaglio

GitHub Enterprise Importer (GEI), precedentemente noto come Octoshift, è lo strumento ufficiale di GitHub per migrazioni su larga scala verso GitHub Enterprise Cloud. GEI è un'offerta API-first altamente personalizzabile, progettata per portare l'intero contesto dei repository — issue, pull request, discussioni, release, impostazioni e altro — mantenendo l'attribuzione degli autori e fornendo visibilità su cosa è stato migrato e cosa no.

### Architettura e Componenti GEI

GEI si compone di tre CLI separate, distribuite come estensioni per la GitHub CLI ufficiale (`gh`):

```
GitHub Enterprise Importer (GEI) - Architettura
┌─────────────────────────────────────────────────────┐
│                    gh CLI (base)                     │
├───────────────┬────────────────┬─────────────────────┤
│   gh gei      │   gh ado2gh   │     gh bbs2gh       │
│  GitHub →     │  Azure DevOps │  Bitbucket Server   │
│  GitHub       │  → GitHub     │  → GitHub           │
│               │               │                     │
│  GA           │  GA           │  Public Beta        │
└───────────────┴────────────────┴─────────────────────┘

Flusso di Migrazione:
1. Generare script di migrazione (generate-script)
2. Eseguire la migrazione (migrate-repo)
3. Verificare il risultato (wait-for-migration)
4. Reclamare i mannequin (reclaim-mannequin)
```

#### Installazione

```bash
# Prerequisiti: GitHub CLI installata
# https://cli.github.com/

# Installare le estensioni GEI
gh extension install github/gh-gei
gh extension install github/gh-ado2gh
gh extension install github/gh-bbs2gh

# Aggiornare (GEI viene aggiornato settimanalmente)
gh extension upgrade github/gh-gei
gh extension upgrade github/gh-ado2gh
gh extension upgrade github/gh-bbs2gh

# Verificare la versione (minimo v1.9.0 per blob storage GitHub-owned)
gh gei --version
gh ado2gh --version
gh bbs2gh --version
```

#### Requisiti dei Token

GEI funziona esclusivamente con Personal Access Token (PAT) classici. Non supporta fine-grained token o GitHub App token.

```bash
# Token per repository sorgente (GitHub → GitHub)
# Scope richiesti: repo, admin:org, workflow
export GH_SOURCE_PAT="ghp_xxxxxxxxx"

# Token per repository destinazione
# Scope richiesti: repo, admin:org, workflow
export GH_PAT="ghp_xxxxxxxxx"

# Per Azure DevOps sorgente
# Scope richiesti: Code (Read), Work Items (Read), Build (Read)
export ADO_PAT="xxxxxxxxxxxxx"

# Per Bitbucket Server sorgente
export BBS_USERNAME="admin"
export BBS_PASSWORD="xxxxxxxxxxxxx"

# Verificare che i token siano validi
gh auth status
```

### gh gei — Migrazione tra GitHub

Il comando `gh gei` gestisce migrazioni da GitHub.com a GitHub.com e da GitHub Enterprise Server (GHES) a GitHub.com.

```bash
# === Generare lo script di migrazione per un'intera organizzazione ===
gh gei generate-script \
  --github-source-org "org-sorgente" \
  --github-target-org "org-destinazione" \
  --output migrate.sh

# Lo script generato contiene un comando migrate-repo per ogni repository.
# Esaminare e personalizzare prima di eseguire.
cat migrate.sh

# === Migrare un singolo repository ===
gh gei migrate-repo \
  --github-source-org "org-sorgente" \
  --source-repo "nome-repo" \
  --github-target-org "org-destinazione" \
  --target-repo "nome-repo"

# === Con GitHub-owned blob storage (v1.9.0+) ===
# Non richiede configurazione aggiuntiva di Azure Blob Storage
gh gei migrate-repo \
  --github-source-org "org-sorgente" \
  --source-repo "nome-repo" \
  --github-target-org "org-destinazione" \
  --target-repo "nome-repo" \
  --use-github-storage

# === Migrazione da GHES (GitHub Enterprise Server) ===
gh gei migrate-repo \
  --github-source-org "org-sorgente" \
  --source-repo "nome-repo" \
  --github-target-org "org-destinazione" \
  --target-repo "nome-repo" \
  --ghes-api-url "https://ghes.azienda.com/api/v3"

# === Controllare lo stato della migrazione ===
gh gei wait-for-migration \
  --migration-id "RM_xxxxxxxxx"

# === Generare script con esclusioni ===
gh gei generate-script \
  --github-source-org "org-sorgente" \
  --github-target-org "org-destinazione" \
  --output migrate.sh \
  --skip-archived     # Escludere repository archiviati
```

### gh ado2gh — Migrazione da Azure DevOps

Il comando `gh ado2gh` è specializzato per migrazioni da Azure DevOps (cloud e server) a GitHub Enterprise Cloud. Oltre ai repository, migra anche team, pipeline e artefatti correlati.

```bash
# === Generare lo script per un'intera organizzazione Azure DevOps ===
gh ado2gh generate-script \
  --ado-org "mia-org-ado" \
  --github-org "mia-org-github" \
  --all \
  --output migrate-ado.sh

# === Migrare un singolo repository ===
gh ado2gh migrate-repo \
  --ado-org "mia-org-ado" \
  --ado-team-project "MioProgetto" \
  --ado-repo "mio-repo" \
  --github-org "mia-org-github" \
  --github-repo "mio-repo"

# === Migrare tutti i repository di un team project ===
gh ado2gh generate-script \
  --ado-org "mia-org-ado" \
  --ado-team-project "MioProgetto" \
  --github-org "mia-org-github" \
  --output migrate-progetto.sh

# === Creare team GitHub basati sui team Azure DevOps ===
gh ado2gh create-team \
  --github-org "mia-org-github" \
  --team-name "team-backend"

# === Inventario completo Azure DevOps ===
gh ado2gh inventory-report \
  --ado-org "mia-org-ado" \
  --output inventario-ado.csv
```

### gh bbs2gh — Migrazione da Bitbucket Server

Il comando `gh bbs2gh` gestisce migrazioni da Bitbucket Server e Data Center verso GitHub. Questo strumento è attualmente in beta pubblica.

```bash
# === Generare lo script per un'istanza Bitbucket Server ===
gh bbs2gh generate-script \
  --bbs-server-url "https://bitbucket.azienda.com" \
  --github-org "mia-org-github" \
  --output migrate-bbs.sh

# === Migrare un singolo repository ===
gh bbs2gh migrate-repo \
  --bbs-server-url "https://bitbucket.azienda.com" \
  --bbs-project "PROJ" \
  --bbs-repo "mio-repo" \
  --github-org "mia-org-github" \
  --github-repo "mio-repo" \
  --bbs-username "$BBS_USERNAME" \
  --bbs-password "$BBS_PASSWORD"

# === Con archivio SMB (per repository grandi) ===
gh bbs2gh migrate-repo \
  --bbs-server-url "https://bitbucket.azienda.com" \
  --bbs-project "PROJ" \
  --bbs-repo "mio-repo" \
  --github-org "mia-org-github" \
  --github-repo "mio-repo" \
  --archive-download-host "smb-server.azienda.com" \
  --smb-user "$SMB_USER" \
  --smb-password "$SMB_PASSWORD"
```

### Cosa Migra GEI e Cosa No

La comprensione di cosa GEI migra e cosa richiede intervento manuale è fondamentale per pianificare una migrazione completa.

| Elemento | GEI Migra? | Note |
|---------|-----------|------|
| Codice sorgente (tutti i branch) | Si | Inclusa storia completa |
| Tag | Si | Tutti i tag annotati e leggeri |
| Pull Request / Merge Request | Si | Con commenti, review, e stato |
| Issue | Si | Con commenti e label |
| Discussioni | Si | Solo GitHub → GitHub |
| Release | Si | Con asset allegati |
| Wiki | Parziale | Solo per GitHub → GitHub |
| Pipeline CI/CD | No | Usare GitHub Actions Importer |
| Segreti / Variabili | No | Ricreare manualmente |
| Webhook | No | Riconfiguare manualmente |
| Branch protection rules | Si | Solo GitHub → GitHub |
| CODEOWNERS | Si | Come parte del codice |
| GitHub Actions workflows | Si | Come file nel repository |
| Packages (GHCR) | No | Ricreare o ripubblicare |
| Projects (boards) | No | Ricreare manualmente |
| Git LFS objects | Si | Con configurazione corretta |
| Submodule references | Si | Ma gli URL devono essere aggiornati |
| Deploy keys | No | Ricreare manualmente |
| Environments | No | Ricreare manualmente |
| Commit status checks | No | Gestiti dalle nuove pipeline |
| Autolink references | No | Ricreare manualmente |
| Mannequin → User mapping | Post-migrazione | Processo di reclaiming separato |

---

## Mannequin e Mapping degli Utenti

Quando GEI migra contenuto da una piattaforma sorgente, tutte le attività utente (eccetto i commit Git) vengono attribuite a identità placeholder chiamate mannequin. Ogni mannequin ha solo un display name dalla piattaforma sorgente, non ha membership nell'organizzazione né accesso ai repository, e utilizza sempre lo stesso avatar — un ghost octocat — con l'etichetta "mannequin".

I commit Git mantengono l'attribuzione originale basata su nome e email nel commit stesso, ma le attività come apertura di issue, commenti su PR, review di codice e simili vengono associate ai mannequin.

### Processo di Reclaiming

Dopo aver completato una migrazione, è possibile "reclamare" i mannequin, collegando l'attività migrata agli account GitHub.com reali degli utenti. Il processo di reclaiming è opzionale e può avvenire in qualsiasi momento dopo il completamento della migrazione, permettendo al team di iniziare a lavorare nei repository migrati prima di completare il mapping degli utenti.

```bash
# === Elencare i mannequin in un'organizzazione ===
# Accedere a: github.com/org/NOME-ORG/settings/mannequins
# Oppure via API:
gh api \
  -H "Accept: application/vnd.github+json" \
  "/orgs/mia-org/mannequins" \
  --jq '.[] | {login: .login, id: .id, email: .email}'

# === Reclamare un singolo mannequin ===
# L'utente target riceverà un invito di attribuzione
# che può accettare o rifiutare
gh api \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  "/orgs/mia-org/mannequins/MANNEQUIN_ID/reattribution" \
  -f target_user_id="USER_ID"

# === Verificare lo stato dei reclaiming ===
gh api \
  "/orgs/mia-org/mannequins" \
  --jq '.[] | select(.reattribution_state != null) |
    {login: .login, state: .reattribution_state, target: .target_user.login}'
```

### Reclaiming in Massa con CSV

Per organizzazioni con molti utenti, il reclaiming in massa tramite CSV è il metodo più efficiente.

```bash
# === Formato del file CSV ===
# mannequin-user,mannequin-id,target-user
# mario-rossi-gitlab,MDQ6VXNlcjE,mario-rossi
# luigi-bianchi-ado,MDQ6VXNlcjI,luigi-bianchi

# === Generare il CSV template ===
# 1. Scaricare la lista mannequin
gh api "/orgs/mia-org/mannequins" \
  --jq '.[] | [.login, .id, ""] | @csv' > mannequins.csv

# 2. Aggiungere l'header
sed -i '1i mannequin-user,mannequin-id,target-user' mannequins.csv

# 3. Compilare la colonna target-user con gli username GitHub reali
# Editare mannequins.csv manualmente o con script

# === Importare il CSV per reclaiming massivo ===
# Accedere a: github.com/org/NOME-ORG/settings/mannequins
# Cliccare "Invite" → "Upload CSV"
# Caricare il file mannequins.csv compilato

# === Script di mapping automatico ===
#!/bin/bash
# auto-map-mannequins.sh
# Tenta di mappare automaticamente mannequin a utenti GitHub
# basandosi sull'indirizzo email

GITHUB_ORG="mia-org"

# Recuperare mannequin
MANNEQUINS=$(gh api "/orgs/${GITHUB_ORG}/mannequins" \
  --jq '.[] | {login: .login, id: .id, email: .email}')

echo "mannequin-user,mannequin-id,target-user" > mapping.csv

echo "$MANNEQUINS" | jq -r '. | @base64' | while read -r encoded; do
  decoded=$(echo "$encoded" | base64 -d)
  login=$(echo "$decoded" | jq -r '.login')
  id=$(echo "$decoded" | jq -r '.id')
  email=$(echo "$decoded" | jq -r '.email')

  # Cercare l'utente GitHub per email
  if [ "$email" != "null" ] && [ -n "$email" ]; then
    gh_user=$(gh api "/search/users?q=${email}+in:email" \
      --jq '.items[0].login // empty' 2>/dev/null)
    if [ -n "$gh_user" ]; then
      echo "${login},${id},${gh_user}" >> mapping.csv
      echo "Mappato: $login ($email) -> $gh_user"
    else
      echo "${login},${id}," >> mapping.csv
      echo "Non trovato: $login ($email)"
    fi
  else
    echo "${login},${id}," >> mapping.csv
    echo "Nessuna email: $login"
  fi
done

echo ""
echo "File mapping.csv generato. Completare manualmente le righe vuote."
```

### Enterprise Managed Users (EMU)

Le organizzazioni che utilizzano Enterprise Managed Users possono reclamare i mannequin immediatamente, saltando il processo di invito. Questo è possibile perché l'amministratore dell'enterprise ha il controllo completo sugli account utente. Il reclaiming avviene one-by-one o in massa tramite CSV, ma senza la necessità di attendere l'accettazione dell'invito da parte degli utenti.

Limitazione critica: l'attribuzione dei commit Git (nome e email nell'header del commit) non è associata ai mannequin e non può essere modificata tramite il processo di reclaiming. Per correggere l'attribuzione dei commit, è necessario usare `git filter-branch` o `git filter-repo` per riscrivere la storia, operazione che modifica gli hash dei commit e richiede un force push.

---

## GitHub Actions Importer

GitHub Actions Importer è uno strumento separato da GEI, specificamente progettato per la conversione automatica delle pipeline CI/CD da altre piattaforme a GitHub Actions. Supporta la migrazione da sette piattaforme: Azure DevOps, Bamboo, Bitbucket, CircleCI, GitLab, Jenkins e Travis CI.

Actions Importer è distribuito come container Docker e come estensione della GitHub CLI. Richiede Docker installato e in esecuzione sulla macchina locale.

### Installazione e Configurazione

```bash
# Prerequisiti: Docker installato e in esecuzione
docker --version  # Verificare Docker
gh --version      # Verificare GitHub CLI

# Installare l'estensione
gh extension install github/gh-actions-importer

# Aggiornare
gh extension upgrade github/gh-actions-importer

# Configurare le credenziali per la piattaforma sorgente
gh actions-importer configure

# La configurazione interattiva chiederà:
# - Piattaforma CI/CD sorgente
# - URL dell'istanza
# - Token/credenziali di accesso
# - Token GitHub per il repository destinazione

# === Configurazione manuale tramite variabili d'ambiente ===

# Per GitLab:
export GITLAB_ACCESS_TOKEN="glpat-xxxxx"
export GITLAB_INSTANCE_URL="https://gitlab.com"

# Per Jenkins:
export JENKINS_ACCESS_TOKEN="xxxxxxxxxxxxx"
export JENKINS_INSTANCE_URL="https://jenkins.azienda.com"
export JENKINS_USERNAME="admin"

# Per CircleCI:
export CIRCLE_CI_ACCESS_TOKEN="xxxxxxxxxxxxx"
export CIRCLE_CI_INSTANCE_URL="https://circleci.com"
export CIRCLE_CI_ORGANIZATION="mia-org"

# Per Travis CI:
export TRAVIS_CI_ACCESS_TOKEN="xxxxxxxxxxxxx"
export TRAVIS_CI_INSTANCE_URL="https://travis-ci.com"
export TRAVIS_CI_ORGANIZATION="mia-org"

# Per Azure DevOps:
export AZURE_DEVOPS_ACCESS_TOKEN="xxxxxxxxxxxxx"
export AZURE_DEVOPS_ORGANIZATION="mia-org"
export AZURE_DEVOPS_PROJECT="mio-progetto"

# Token GitHub (necessario per tutti):
export GITHUB_ACCESS_TOKEN="ghp_xxxxx"
```

### Comando audit

Il comando `audit` analizza l'intera footprint CI/CD della piattaforma sorgente, generando un report dettagliato che aiuta a pianificare la timeline della migrazione. Il report include il numero di pipeline, la complessità di ciascuna, e una stima della percentuale di conversione automatica.

```bash
# === Audit GitLab ===
gh actions-importer audit gitlab \
  --output-dir audit-results/ \
  --namespace "mia-org"

# === Audit Jenkins ===
gh actions-importer audit jenkins \
  --output-dir audit-results/

# === Audit CircleCI ===
gh actions-importer audit circle-ci \
  --output-dir audit-results/

# === Audit Azure DevOps ===
gh actions-importer audit azure-devops \
  --output-dir audit-results/

# === Audit Travis CI ===
gh actions-importer audit travis-ci \
  --output-dir audit-results/

# Il report generato contiene:
# - audit_summary.md: riepilogo con statistiche
# - Per ogni pipeline: file YAML convertito + note di conversione
# - Percentuale di step convertiti automaticamente
# - Step che richiedono intervento manuale
# - Mapping dei plugin/task alle action GitHub equivalenti
```

### Comando forecast

Il comando `forecast` analizza l'utilizzo storico delle pipeline per creare una previsione dell'utilizzo di GitHub Actions. Per impostazione predefinita include gli ultimi sette giorni di dati, ma il periodo è configurabile.

```bash
# === Forecast per Jenkins ===
gh actions-importer forecast jenkins \
  --output-dir forecast-results/ \
  --start-date 2026-04-01 \
  --end-date 2026-04-30

# === Forecast per GitLab ===
gh actions-importer forecast gitlab \
  --output-dir forecast-results/ \
  --namespace "mia-org"

# Il report di forecast include:
# - Numero di job eseguiti nel periodo
# - Tempo totale di esecuzione
# - Runner utilizzati (tipi e quantità)
# - Stima dei minuti GitHub Actions necessari
# - Raccomandazione sul piano GitHub (Free, Team, Enterprise)
```

### Comando dry-run

Il comando `dry-run` converte una pipeline nel suo equivalente GitHub Actions e scrive il workflow sul filesystem locale, senza creare pull request o modificare il repository. È il modo più sicuro per verificare la qualità della conversione prima di committare.

```bash
# === Dry-run di una pipeline GitLab ===
gh actions-importer dry-run gitlab \
  --output-dir dry-run-results/ \
  --namespace "mia-org" \
  --project "mio-progetto"

# === Dry-run di un Jenkinsfile ===
gh actions-importer dry-run jenkins \
  --output-dir dry-run-results/ \
  --source-url "https://jenkins.azienda.com/job/mio-progetto"

# === Dry-run di una pipeline CircleCI ===
gh actions-importer dry-run circle-ci \
  --output-dir dry-run-results/ \
  --project "mio-progetto"

# === Dry-run con custom transformer ===
# I custom transformer permettono di personalizzare la conversione
# per gestire plugin proprietari o configurazioni specifiche
gh actions-importer dry-run jenkins \
  --output-dir dry-run-results/ \
  --source-url "https://jenkins.azienda.com/job/mio-progetto" \
  --custom-transformers custom-transformers.rb

# Esaminare il risultato
cat dry-run-results/.github/workflows/*.yml
```

### Comando migrate

Il comando `migrate` esegue la conversione effettiva e apre una pull request nel repository GitHub destinazione con il workflow convertito.

```bash
# === Migrazione completa da GitLab ===
gh actions-importer migrate gitlab \
  --target-url "https://github.com/mia-org/mio-progetto" \
  --namespace "mia-org" \
  --project "mio-progetto"

# === Migrazione da Jenkins ===
gh actions-importer migrate jenkins \
  --target-url "https://github.com/mia-org/mio-progetto" \
  --source-url "https://jenkins.azienda.com/job/mio-progetto"

# === Migrazione con custom transformer per plugin proprietari ===
gh actions-importer migrate jenkins \
  --target-url "https://github.com/mia-org/mio-progetto" \
  --source-url "https://jenkins.azienda.com/job/mio-progetto" \
  --custom-transformers custom-transformers.rb

# Il risultato è una PR nel repository target contenente:
# - .github/workflows/nome-pipeline.yml (workflow convertito)
# - Commenti sulla PR con note di conversione
# - Indicazione degli step non convertiti automaticamente
```

---

## Migrazione da Jenkins a GitHub Actions

Jenkins è uno dei sistemi CI/CD più diffusi e la migrazione a GitHub Actions è una delle conversioni più comuni. La complessità varia enormemente in base al numero di plugin utilizzati: pipeline Jenkins semplici con pochi plugin standard hanno un tasso di conversione automatica dell'80-90%, mentre pipeline complesse con plugin proprietari possono richiedere significativo lavoro manuale.

### Mapping dei Concetti Jenkins

| Jenkins | GitHub Actions | Note |
|---------|---------------|------|
| `Jenkinsfile` (Declarative) | `.github/workflows/*.yml` | Formato diverso (Groovy vs YAML) |
| `Jenkinsfile` (Scripted) | Conversione manuale | Scripted Pipeline non supportato dall'importer |
| `pipeline { }` | Intero file workflow | Struttura top-level |
| `agent any` | `runs-on: ubuntu-latest` | Specificare il runner |
| `agent { docker { image '...' } }` | `container: { image: '...' }` | Container di esecuzione |
| `stages { stage('...') { } }` | `jobs:` | Ogni stage diventa un job |
| `steps { sh '...' }` | `steps: - run: ...` | Esecuzione comandi |
| `environment { }` | `env:` | Variabili d'ambiente |
| `parameters { }` | `workflow_dispatch: inputs:` | Input manuali |
| `when { branch 'main' }` | `if: github.ref == 'refs/heads/main'` | Condizioni |
| `post { always { } }` | `if: always()` | Esecuzione post |
| `post { failure { } }` | `if: failure()` | Solo su fallimento |
| `post { success { } }` | `if: success()` | Solo su successo |
| `credentials('id')` | `${{ secrets.NAME }}` | Gestione segreti |
| `Shared Library` | Reusable Workflows / Composite Actions | Codice riutilizzabile |
| `input { }` | `environment: ... (con approval)` | Approvazione manuale |
| `parallel { }` | Jobs paralleli con `needs` | Esecuzione parallela |
| `matrix { }` | `strategy: matrix:` | Matrici di build |
| `stash/unstash` | `actions/upload-artifact` / `download-artifact` | Passaggio artefatti tra job |
| `cron('H/15 * * * *')` | `schedule: - cron: '*/15 * * * *'` | Esecuzione schedulata |
| `timeout(time: 30, unit: 'MINUTES')` | `timeout-minutes: 30` | Timeout del job |
| `retry(3)` | `continue-on-error` + logica custom | Ripetizione automatica |

### Conversione Jenkinsfile

**Jenkinsfile originale (Declarative Pipeline):**

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = credentials('docker-registry-url')
        DOCKER_CREDS = credentials('docker-registry-creds')
        SONAR_TOKEN = credentials('sonarqube-token')
        DEPLOY_KEY = credentials('deploy-ssh-key')
    }

    options {
        timeout(time: 60, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    parameters {
        choice(name: 'ENVIRONMENT', choices: ['staging', 'production'],
               description: 'Seleziona ambiente di deploy')
        booleanParam(name: 'RUN_SONAR', defaultValue: true,
                     description: 'Eseguire analisi SonarQube')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh 'npm ci'
                sh 'npm run build'
            }
        }

        stage('Test') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh 'npm run test:unit -- --coverage'
                    }
                    post {
                        always {
                            junit 'test-results/**/*.xml'
                            publishHTML([
                                reportDir: 'coverage',
                                reportFiles: 'index.html',
                                reportName: 'Coverage Report'
                            ])
                        }
                    }
                }
                stage('Integration Tests') {
                    steps {
                        sh 'docker-compose up -d postgres redis'
                        sh 'npm run test:integration'
                    }
                    post {
                        always {
                            sh 'docker-compose down'
                        }
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            when {
                expression { params.RUN_SONAR == true }
            }
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh 'npx sonar-scanner'
                }
            }
        }

        stage('Docker Build & Push') {
            when {
                branch 'main'
            }
            steps {
                sh """
                    docker login -u ${DOCKER_CREDS_USR} -p ${DOCKER_CREDS_PSW} ${DOCKER_REGISTRY}
                    docker build -t ${DOCKER_REGISTRY}/myapp:${BUILD_NUMBER} .
                    docker push ${DOCKER_REGISTRY}/myapp:${BUILD_NUMBER}
                """
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            input {
                message 'Procedere con il deploy?'
                ok 'Deploy'
            }
            steps {
                sh """
                    ssh -i ${DEPLOY_KEY} deploy@server \
                        "docker pull ${DOCKER_REGISTRY}/myapp:${BUILD_NUMBER} && \
                         docker-compose up -d"
                """
            }
        }
    }

    post {
        failure {
            slackSend(channel: '#ci-alerts',
                      message: "Build FALLITA: ${env.JOB_NAME} #${env.BUILD_NUMBER}")
        }
        success {
            slackSend(channel: '#ci-alerts',
                      message: "Build OK: ${env.JOB_NAME} #${env.BUILD_NUMBER}")
        }
    }
}
```

**GitHub Actions equivalente:**

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Seleziona ambiente di deploy'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production
      run_sonar:
        description: 'Eseguire analisi SonarQube'
        required: true
        default: true
        type: boolean

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false

env:
  REGISTRY: ${{ secrets.DOCKER_REGISTRY }}

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci
      - run: npm run build

      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 3

  test-unit:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run test:unit -- --coverage

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: test-results/

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: coverage/

  test-integration:
    needs: build
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ['6379:6379']
        options: --health-cmd "redis-cli ping" --health-interval 10s --health-timeout 5s --health-retries 5
    env:
      DATABASE_URL: postgresql://test:test@localhost:5432/test
      REDIS_URL: redis://localhost:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run test:integration

  sonarqube:
    needs: [test-unit, test-integration]
    if: >
      github.event_name != 'workflow_dispatch' ||
      github.event.inputs.run_sonar == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Necessario per SonarQube

      - uses: actions/download-artifact@v4
        with:
          name: coverage-report
          path: coverage/

      - uses: SonarSource/sonarqube-scan-action@v5
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}

  docker-build-push:
    needs: [test-unit, test-integration]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      packages: write
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ${{ env.REGISTRY }}/myapp
          tags: |
            type=raw,value=${{ github.run_number }}
            type=sha

      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: docker-build-push
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: ${{ github.event.inputs.environment || 'staging' }}
      url: ${{ github.event.inputs.environment == 'production' && 'https://app.example.com' || 'https://staging.example.com' }}
    steps:
      - uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.DEPLOY_SSH_KEY }}

      - run: |
          ssh deploy@${{ vars.DEPLOY_HOST }} \
            "docker pull ${{ env.REGISTRY }}/myapp:${{ github.run_number }} && \
             docker-compose up -d"

  notify:
    needs: [deploy]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - uses: slackapi/slack-github-action@v2.0.0
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
          webhook-type: incoming-webhook
          payload: |
            {
              "text": "${{ needs.deploy.result == 'success' && 'Build OK' || 'Build FALLITA' }}: ${{ github.repository }} #${{ github.run_number }}"
            }
```

### Mapping dei Plugin Jenkins

I plugin Jenkins più comuni hanno equivalenti diretti come GitHub Actions:

| Plugin Jenkins | GitHub Action Equivalente | Note |
|---------------|--------------------------|------|
| `git` | `actions/checkout@v4` | Checkout del repository |
| `nodejs` | `actions/setup-node@v4` | Setup Node.js |
| `maven-plugin` | `actions/setup-java@v4` + `mvn` | Setup Java + Maven |
| `gradle` | `actions/setup-java@v4` + `gradle/actions/setup-gradle@v4` | Setup Gradle |
| `docker-workflow` | `docker/build-push-action@v5` | Build e push Docker |
| `junit` | `dorny/test-reporter@v1` | Report test JUnit |
| `jacoco` | `madrapps/jacoco-report@v1.7` | Report coverage JaCoCo |
| `cobertura` | `irongut/CodeCoverageSummary@v1.3` | Report coverage Cobertura |
| `sonar` | `SonarSource/sonarqube-scan-action@v5` | Analisi SonarQube |
| `slack` | `slackapi/slack-github-action@v2.0.0` | Notifiche Slack |
| `email-ext` | `dawidd6/action-send-mail@v3` | Notifiche email |
| `pipeline-aws` | `aws-actions/configure-aws-credentials@v4` | Credenziali AWS |
| `kubernetes-cli` | `azure/k8s-set-context@v4` | Contesto Kubernetes |
| `terraform` | `hashicorp/setup-terraform@v3` | Setup Terraform |
| `ansible` | `dawidd6/action-ansible-playbook@v2` | Esecuzione Ansible |
| `artifactory` | `jfrog/setup-jfrog-cli@v4` | JFrog Artifactory CLI |
| `htmlpublisher` | `actions/upload-artifact@v4` + GitHub Pages | Pubblicazione report HTML |
| `credentials-binding` | `${{ secrets.NAME }}` | Binding dei segreti |
| `build-discarder` | Retention policy automatica | GitHub gestisce automaticamente |
| `lockable-resources` | `concurrency:` | Controllo concorrenza |
| `timestamper` | Timestamp nativi nei log | Supportato di default |

---

## Migrazione da CircleCI e Travis CI

### Migrazione da CircleCI

CircleCI e GitHub Actions condividono diversi concetti simili, rendendo la migrazione relativamente diretta. Entrambi usano YAML per la configurazione, supportano job paralleli, e utilizzano container Docker come ambienti di esecuzione.

#### Mapping dei Concetti CircleCI

| CircleCI | GitHub Actions | Note |
|---------|---------------|------|
| `.circleci/config.yml` | `.github/workflows/*.yml` | File di configurazione |
| `workflows` | `on` triggers + `jobs` | Orchestrazione |
| `jobs` | `jobs` | Unità di esecuzione |
| `steps` | `steps` | Passi individuali |
| `executor` / `docker` | `runs-on` / `container` | Ambiente di esecuzione |
| `orbs` | Marketplace Actions | Componenti riutilizzabili |
| `commands` | Composite Actions | Comandi riutilizzabili |
| `cache` (con key) | `actions/cache@v4` | Caching delle dipendenze |
| `store_artifacts` | `actions/upload-artifact@v4` | Artefatti |
| `store_test_results` | `dorny/test-reporter@v1` | Report test |
| `contexts` | Environment secrets | Gruppi di segreti |
| `approval` job | `environment` con reviewers | Approvazione manuale |
| `matrix` | `strategy: matrix:` | Matrici di build |
| `when` condition | `if:` condition | Condizioni |
| `CIRCLE_SHA1` | `${{ github.sha }}` | Hash del commit |
| `CIRCLE_BRANCH` | `${{ github.ref_name }}` | Nome del branch |
| `CIRCLE_BUILD_NUM` | `${{ github.run_number }}` | Numero di build |
| `CIRCLE_PROJECT_REPONAME` | `${{ github.event.repository.name }}` | Nome del repository |

#### Esempio di Conversione CircleCI

**CircleCI originale:**

```yaml
# .circleci/config.yml
version: 2.1

orbs:
  node: circleci/node@5.2
  docker: circleci/docker@2.6
  slack: circleci/slack@4.13

executors:
  node-executor:
    docker:
      - image: cimg/node:20.11
    working_directory: ~/project

commands:
  install-deps:
    steps:
      - checkout
      - node/install-packages:
          pkg-manager: npm
          cache-key: "package-lock.json"

jobs:
  lint:
    executor: node-executor
    steps:
      - install-deps
      - run: npm run lint
      - run: npm run type-check

  test:
    executor: node-executor
    parallelism: 4
    steps:
      - install-deps
      - run:
          name: Run tests
          command: |
            TESTFILES=$(circleci tests glob "src/**/*.test.ts" | circleci tests split)
            npm test -- $TESTFILES --coverage
      - store_test_results:
          path: test-results
      - store_artifacts:
          path: coverage

  build-docker:
    executor: docker/docker
    steps:
      - setup_remote_docker
      - checkout
      - docker/build:
          image: myapp
          tag: ${CIRCLE_SHA1}
      - docker/push:
          image: myapp
          tag: ${CIRCLE_SHA1}

  deploy:
    executor: node-executor
    steps:
      - checkout
      - run:
          name: Deploy
          command: ./deploy.sh
      - slack/notify:
          event: pass
          template: success_tagged_deploy_1

workflows:
  build-test-deploy:
    jobs:
      - lint
      - test:
          requires: [lint]
      - build-docker:
          requires: [test]
          filters:
            branches:
              only: main
      - deploy:
          requires: [build-docker]
          context: production
          filters:
            branches:
              only: main
```

**GitHub Actions equivalente:**

```yaml
# .github/workflows/ci-cd.yml
name: Build Test Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check

  test:
    needs: lint
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --shard=${{ matrix.shard }}/4 --coverage
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results-${{ matrix.shard }}
          path: test-results/
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-${{ matrix.shard }}
          path: coverage/

  build-docker:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}

  deploy:
    needs: build-docker
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
      - uses: slackapi/slack-github-action@v2.0.0
        if: success()
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
          webhook-type: incoming-webhook
          payload: |
            {"text": "Deploy completato: ${{ github.repository }}@${{ github.sha }}"}
```

### Migrazione da Travis CI

Travis CI e GitHub Actions condividono la stessa filosofia di configurazione via YAML e file nel repository. La migrazione è generalmente la più semplice tra tutte le piattaforme, dato che i concetti sono molto simili.

#### Mapping dei Concetti Travis CI

| Travis CI | GitHub Actions | Note |
|----------|---------------|------|
| `.travis.yml` | `.github/workflows/*.yml` | File di configurazione |
| `language` | `actions/setup-*` | Setup del linguaggio |
| `os` | `runs-on` | Sistema operativo |
| `dist` | `runs-on: ubuntu-*` | Distribuzione Linux |
| `services` | `services:` | Servizi container |
| `env.global` | `env:` (a livello workflow) | Variabili globali |
| `env.matrix` / `env.jobs` | `strategy: matrix:` | Matrici di build |
| `cache` | `actions/cache@v4` | Caching |
| `before_install` | Steps prima dell'installazione | Primi passi |
| `install` | Step di installazione | Installazione dipendenze |
| `before_script` | Steps prima degli script | Preparazione |
| `script` | `run:` steps | Esecuzione principale |
| `after_success` | `if: success()` | Post-successo |
| `after_failure` | `if: failure()` | Post-fallimento |
| `deploy` | Job di deploy separato | Deploy |
| `stages` | `jobs` con `needs` | Fasi |
| `if: branch = main` | `if: github.ref == 'refs/heads/main'` | Condizioni branch |
| `TRAVIS_COMMIT` | `${{ github.sha }}` | Hash commit |
| `TRAVIS_BRANCH` | `${{ github.ref_name }}` | Nome branch |
| `TRAVIS_BUILD_NUMBER` | `${{ github.run_number }}` | Numero build |
| `TRAVIS_PULL_REQUEST` | `${{ github.event.pull_request.number }}` | Numero PR |

#### Esempio di Conversione Travis CI

**Travis CI originale:**

```yaml
# .travis.yml
language: python
python:
  - "3.11"
  - "3.12"

os: linux
dist: jammy

services:
  - docker
  - postgresql

cache:
  pip: true
  directories:
    - .tox

env:
  global:
    - DJANGO_SETTINGS_MODULE=myapp.settings.test
  jobs:
    - TOXENV=lint
    - TOXENV=tests

before_install:
  - pip install --upgrade pip setuptools

install:
  - pip install tox

before_script:
  - psql -c 'CREATE DATABASE test_db;' -U postgres

script:
  - tox -e $TOXENV

after_success:
  - if [ "$TOXENV" = "tests" ]; then pip install codecov && codecov; fi

deploy:
  provider: pypi
  username: __token__
  password:
    secure: "encrypted_token"
  on:
    tags: true
    python: "3.12"
```

**GitHub Actions equivalente:**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:

env:
  DJANGO_SETTINGS_MODULE: myapp.settings.test

jobs:
  lint:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install tox
      - run: tox -e lint

  test:
    runs-on: ubuntu-22.04
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
    env:
      DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      - run: pip install tox
      - run: tox -e tests
      - uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.12'
        with:
          token: ${{ secrets.CODECOV_TOKEN }}

  deploy-pypi:
    needs: [lint, test]
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-22.04
    permissions:
      id-token: write  # Per trusted publishing PyPI
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
        # Trusted publishing: non servono token PyPI
```

---

## Pulizia Pre-Migrazione del Repository

Prima di migrare un repository verso GitHub, è fondamentale effettuare una pulizia della storia Git per rimuovere file grandi accidentalmente committati, segreti esposti e artefatti non necessari. GitHub ha un limite di 100 MB per singolo file e raccomanda repository inferiori a 5 GB. Pulire prima della migrazione è molto più semplice che farlo dopo.

### BFG Repo Cleaner

BFG Repo Cleaner è uno strumento specificamente progettato per la pulizia dei repository Git. È 10-720 volte più veloce di `git filter-branch` e sfrutta il multi-core processing per ottimizzare le prestazioni.

```bash
# Installazione
# Scaricare da https://rtyley.github.io/bfg-repo-cleaner/
# Richiede Java Runtime Environment

# === Preparazione ===
# Clonare il repository come mirror
git clone --mirror https://gitlab.com/org/repo.git repo.git

# === Rimuovere file grandi dalla storia ===
# Rimuovere tutti i blob superiori a 100 MB
java -jar bfg.jar --strip-blobs-bigger-than 100M repo.git

# Rimuovere file con estensioni specifiche dalla storia
java -jar bfg.jar --delete-files '*.{zip,tar.gz,war,jar,exe,dll,iso}' repo.git

# Rimuovere file specifici per nome
java -jar bfg.jar --delete-files 'database-dump.sql' repo.git

# === Rimuovere segreti dalla storia ===
# Creare un file con i segreti da rimuovere (uno per riga)
cat > passwords.txt << 'EOF'
ghp_oldtoken123456789
AKIAIOSFODNN7EXAMPLE
regex:password\s*=\s*['"].*['"]
regex:api[_-]?key\s*=\s*['"].*['"]
EOF

# Sostituire le occorrenze con ***REMOVED***
java -jar bfg.jar --replace-text passwords.txt repo.git

# === Rimuovere directory non necessarie ===
java -jar bfg.jar --delete-folders '.svn' repo.git
java -jar bfg.jar --delete-folders 'node_modules' repo.git
java -jar bfg.jar --delete-folders '.git' repo.git  # Sottodirectory .git annidate

# === Pulizia post-BFG (obbligatoria) ===
cd repo.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Verificare la riduzione di dimensione
du -sh .

# Push verso il nuovo remote
git push --mirror https://github.com/org/repo.git
```

### git-filter-repo

`git-filter-repo` è lo strumento raccomandato ufficialmente da Git come sostituto di `git filter-branch`. Offre maggiore flessibilità e prestazioni migliori per operazioni complesse di riscrittura della storia.

```bash
# Installazione
pip install git-filter-repo

# === Rimuovere file grandi dalla storia ===
git filter-repo --strip-blobs-bigger-than 100M

# === Rimuovere file per path ===
git filter-repo --path-glob '*.sql' --invert-paths
git filter-repo --path 'vendor/' --invert-paths
git filter-repo --path 'node_modules/' --invert-paths

# === Rimuovere segreti con regex ===
git filter-repo --blob-callback '
    import re
    # Rimuovere API key patterns
    content = blob.data
    content = re.sub(rb"(api[_-]?key\s*[=:]\s*['\"])[^'\"]+(['\"])",
                     rb"\1***REMOVED***\2", content)
    content = re.sub(rb"(password\s*[=:]\s*['\"])[^'\"]+(['\"])",
                     rb"\1***REMOVED***\2", content)
    blob.data = content
'

# === Riscrivere gli autori durante la migrazione ===
# Creare un file di mapping
cat > mailmap << 'EOF'
Mario Rossi <mario.rossi@github.com> <mario@vecchia-azienda.com>
Luigi Bianchi <luigi.bianchi@github.com> <luigi@vecchia-azienda.com>
EOF

git filter-repo --mailmap mailmap

# === Analisi pre-pulizia ===
# Vedere i file più grandi nella storia
git filter-repo --analyze
cat .git/filter-repo/analysis/blob-shas-and-paths.txt | head -20

# === Estrarre un sotto-directory come nuovo repository ===
# Utile per splitare un monorepo
git filter-repo --subdirectory-filter src/microservice-a
```

### Rimozione Segreti dalla Storia

La rimozione dei segreti dalla storia Git è una operazione critica di sicurezza che deve precedere qualsiasi migrazione verso una piattaforma pubblica o condivisa. Anche se il repository è privato, i segreti nella storia rappresentano un rischio significativo.

```bash
#!/bin/bash
# scan-and-clean-secrets.sh
# Script completo per scansione e pulizia segreti pre-migrazione

REPO_PATH="${1:-.}"
cd "$REPO_PATH"

echo "=== Fase 1: Scansione segreti nella storia ==="

# Usare git log per cercare pattern comuni di segreti
echo "Cercando pattern di API key..."
git log -p --all -S 'AKIA' -- | grep -n 'AKIA' | head -20

echo ""
echo "Cercando pattern di token..."
git log -p --all -S 'ghp_' -- | grep -c 'ghp_'
git log -p --all -S 'glpat-' -- | grep -c 'glpat-'
git log -p --all -S 'sk-' -- | grep -c 'sk-'

echo ""
echo "Cercando pattern di password..."
git log -p --all --diff-filter=A -- '*.env' '*.env.*' '.env.*' | head -30

echo ""
echo "Cercando file sensibili committati accidentalmente..."
git log --all --diff-filter=A --name-only -- \
  '*.pem' '*.key' '*.p12' '*.pfx' \
  '*.env' '*.env.*' \
  'credentials.json' 'service-account.json' \
  'id_rsa' 'id_ed25519' | sort -u

echo ""
echo "=== Fase 2: Report dimensioni ==="
echo "Dimensione attuale del repository:"
du -sh .git

echo ""
echo "File più grandi nella storia (top 20):"
git rev-list --objects --all |
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' |
  sed -n 's/^blob //p' |
  sort -rnk2 |
  head -20 |
  awk '{printf "%s\t%s\t%s\n", $1, int($2/1048576)"MB", $3}'

echo ""
echo "=== Fase 3: Raccomandazioni ==="
echo "Se trovati segreti, procedere con la pulizia usando BFG o git-filter-repo"
echo "IMPORTANTE: Ruotare TUTTI i segreti trovati, la pulizia dalla storia"
echo "non li rende sicuri se sono già stati esposti."
```

---

## Migrazione Git LFS Approfondita

Git Large File Storage (LFS) è un'estensione open source che sostituisce file grandi (video, dataset, asset grafici) con puntatori nel repository, memorizzando il contenuto effettivo su un server remoto separato. La migrazione di repository che utilizzano LFS richiede attenzione speciale per evitare la perdita di oggetti o la creazione di puntatori orfani.

### Analisi Pre-Migrazione LFS

Prima di migrare, è essenziale capire quali file sono tracciati da LFS, la loro dimensione totale e l'impatto sui costi di storage e bandwidth GitHub.

```bash
# === Analisi del repository sorgente ===

# Verificare se il repository usa LFS
git lfs env

# Elencare tutti i file LFS con dimensioni
git lfs ls-files --all --long

# Calcolare lo spazio LFS totale
git lfs ls-files --all --size | awk '{
  total += $NF
}
END {
  printf "Totale LFS: %.2f MB (%.2f GB)\n", total/1048576, total/1073741824
}'

# Identificare i file che DOVREBBERO essere in LFS ma non lo sono
# (file grandi tracciati normalmente)
git lfs migrate info --everything --above=10M

# Output tipico:
# migrate: Sorting commits: ..., done.
# migrate: Examining commits: 100% (1523/1523), done.
# *.psd    120 MB    23/23 files(s)  100%
# *.zip     85 MB    12/12 files(s)  100%
# *.mp4    340 MB     8/8  files(s)  100%

# Verificare .gitattributes per i pattern LFS attuali
cat .gitattributes
# Esempio:
# *.psd filter=lfs diff=lfs merge=lfs -text
# *.zip filter=lfs diff=lfs merge=lfs -text
# *.mp4 filter=lfs diff=lfs merge=lfs -text

# === Stima dei costi GitHub LFS ===
# GitHub offre 1 GB storage e 1 GB bandwidth gratis
# Oltre: $5/mese per 50 GB storage + 50 GB bandwidth (data pack)
echo ""
echo "=== Stima Costi GitHub LFS ==="
TOTAL_MB=$(git lfs ls-files --all --size | awk '{total += $NF} END {print total/1048576}')
echo "Storage necessario: ${TOTAL_MB} MB"
if (( $(echo "$TOTAL_MB > 1024" | bc -l) )); then
  PACKS=$(echo "($TOTAL_MB - 1024) / 51200 + 1" | bc)
  echo "Data packs necessari: $PACKS (= \$$((PACKS * 5))/mese)"
else
  echo "Rientra nel piano gratuito (1 GB)"
fi
```

### Strategia di Tracking con .gitattributes

La configurazione corretta di `.gitattributes` è critica per la migrazione LFS. Tracciare per estensione piuttosto che per nome file garantisce che futuri file dello stesso tipo vengano automaticamente gestiti da LFS.

```bash
# === Configurazione .gitattributes consigliata ===
cat > .gitattributes << 'GITATTR'
# === Asset grafici ===
*.psd filter=lfs diff=lfs merge=lfs -text
*.ai filter=lfs diff=lfs merge=lfs -text
*.sketch filter=lfs diff=lfs merge=lfs -text
*.fig filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.jpeg filter=lfs diff=lfs merge=lfs -text
*.gif filter=lfs diff=lfs merge=lfs -text
*.svg filter=lfs diff=lfs merge=lfs -text
*.ico filter=lfs diff=lfs merge=lfs -text
*.webp filter=lfs diff=lfs merge=lfs -text

# === Video e audio ===
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.mov filter=lfs diff=lfs merge=lfs -text
*.avi filter=lfs diff=lfs merge=lfs -text
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.wav filter=lfs diff=lfs merge=lfs -text

# === Archivi ===
*.zip filter=lfs diff=lfs merge=lfs -text
*.tar.gz filter=lfs diff=lfs merge=lfs -text
*.7z filter=lfs diff=lfs merge=lfs -text
*.rar filter=lfs diff=lfs merge=lfs -text

# === Binari compilati ===
*.exe filter=lfs diff=lfs merge=lfs -text
*.dll filter=lfs diff=lfs merge=lfs -text
*.so filter=lfs diff=lfs merge=lfs -text
*.dylib filter=lfs diff=lfs merge=lfs -text

# === Dati e dataset ===
*.sqlite filter=lfs diff=lfs merge=lfs -text
*.db filter=lfs diff=lfs merge=lfs -text
*.csv filter=lfs diff=lfs merge=lfs -text
*.parquet filter=lfs diff=lfs merge=lfs -text

# === Font ===
*.ttf filter=lfs diff=lfs merge=lfs -text
*.otf filter=lfs diff=lfs merge=lfs -text
*.woff filter=lfs diff=lfs merge=lfs -text
*.woff2 filter=lfs diff=lfs merge=lfs -text
GITATTR

# === Migrare file esistenti nella storia a LFS ===
# Questo riscrive la storia Git convertendo i file in puntatori LFS
git lfs migrate import \
  --include="*.psd,*.zip,*.mp4,*.exe" \
  --everything

# Verificare il risultato
git lfs ls-files --all

# === IMPORTANTE: dopo git lfs migrate import ===
# 1. La storia è stata riscritta (nuovi hash per tutti i commit)
# 2. Tutti i collaboratori devono fare un fresh clone
# 3. Force push necessario se il repository remoto esiste già
```

### Ottimizzazione Costi e Bandwidth LFS

```bash
# === Saltare LFS nelle CI quando non necessario ===
# Impostare GIT_LFS_SKIP_SMUDGE=1 nei workflow GitHub Actions
# per evitare di scaricare i file LFS quando non servono

# Esempio workflow con skip LFS:
cat > .github/workflows/ci-skip-lfs.yml << 'WORKFLOW'
name: CI (senza LFS)
on: [push, pull_request]
env:
  GIT_LFS_SKIP_SMUDGE: 1  # Non scaricare oggetti LFS

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        # lfs: false è il default, non scarica oggetti LFS
      - run: npm ci
      - run: npm run lint
      - run: npm test

  build-with-assets:
    runs-on: ubuntu-latest
    needs: lint-and-test
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true  # Scaricare LFS solo quando serve
      - run: npm ci
      - run: npm run build  # Il build ha bisogno degli asset
WORKFLOW

# === Script di migrazione LFS completo ===
#!/bin/bash
# migrate-lfs-between-platforms.sh

SOURCE_REMOTE="https://gitlab.com/org/repo.git"
TARGET_REMOTE="https://github.com/org/repo.git"

echo "=== Migrazione LFS: $SOURCE_REMOTE -> $TARGET_REMOTE ==="

# 1. Clone con tutti gli oggetti LFS
GIT_LFS_SKIP_SMUDGE=0 git clone "$SOURCE_REMOTE" /tmp/lfs-migration
cd /tmp/lfs-migration

# 2. Fetch tutti gli oggetti LFS da tutti i branch
git lfs fetch --all "$SOURCE_REMOTE"

# 3. Verificare la completezza
echo "Oggetti LFS scaricati:"
git lfs ls-files --all | wc -l

# 4. Aggiungere il remote GitHub
git remote add github "$TARGET_REMOTE"

# 5. Push del codice
git push github --all
git push github --tags

# 6. Push degli oggetti LFS
git lfs push --all github

# 7. Verifica
echo ""
echo "Verificare su GitHub che tutti gli oggetti LFS siano accessibili"
echo "Clonare dal nuovo remote e verificare che i file non siano puntatori"

# 8. Pulizia
cd /
rm -rf /tmp/lfs-migration
```

---

## Gestione Segreti nella Migrazione

La migrazione dei segreti è una delle parti più delicate del processo perché GitHub non offre un'API di esportazione dei segreti (per ragioni di sicurezza) e i segreti devono essere ricreati manualmente sulla nuova piattaforma. Questo è anche un momento opportuno per ruotare tutti i segreti e rivedere la strategia di gestione.

### Livelli di Segreti GitHub

GitHub organizza i segreti su tre livelli gerarchici, ciascuno con un diverso ambito di visibilità:

```
Gerarchia Segreti GitHub
┌─────────────────────────────────────────────┐
│           Organization Secrets              │
│  Visibili a tutti o a repository selezionati│
│  Configurati in: Org Settings → Secrets     │
├─────────────────────────────────────────────┤
│           Repository Secrets                │
│  Visibili solo al singolo repository        │
│  Configurati in: Repo Settings → Secrets    │
├─────────────────────────────────────────────┤
│           Environment Secrets               │
│  Visibili solo in uno specifico environment │
│  Possono richiedere approvazione            │
│  Configurati in: Environments → Secrets     │
└─────────────────────────────────────────────┘

Precedenza: Environment > Repository > Organization
(Se un segreto con lo stesso nome esiste a più livelli,
quello più specifico ha la precedenza)
```

```bash
# === Creare segreti a livello organizzazione ===
# Visibili a repository selezionati
gh secret set DOCKER_REGISTRY_URL \
  --org "mia-org" \
  --visibility selected \
  --repos "repo-1,repo-2,repo-3" \
  --body "registry.azienda.com"

# Visibili a tutti i repository dell'organizzazione
gh secret set NPM_TOKEN \
  --org "mia-org" \
  --visibility all \
  --body "npm_xxxxxxxxxxxxx"

# === Creare segreti a livello repository ===
gh secret set DATABASE_URL \
  --repo "mia-org/mio-repo" \
  --body "postgresql://user:pass@host:5432/db"

# === Creare segreti a livello environment ===
gh secret set DEPLOY_SSH_KEY \
  --repo "mia-org/mio-repo" \
  --env "production" \
  < deploy-key.pem

# === Creare variabili (per dati non sensibili) ===
gh variable set NODE_ENV \
  --repo "mia-org/mio-repo" \
  --body "production"

gh variable set DEPLOY_HOST \
  --repo "mia-org/mio-repo" \
  --env "staging" \
  --body "staging.example.com"

# === Verificare i segreti configurati ===
gh secret list --repo "mia-org/mio-repo"
gh secret list --repo "mia-org/mio-repo" --env "production"
gh secret list --org "mia-org"
```

### Migrazione Segreti da Altre Piattaforme

I segreti non possono essere esportati da nessuna piattaforma CI/CD per ragioni di sicurezza. La migrazione richiede la ricreazione manuale e offre l'opportunità di migliorare la gestione.

```bash
#!/bin/bash
# migrate-secrets.sh
# Script di supporto per la migrazione dei segreti

GITHUB_ORG="mia-org"
GITHUB_REPO="mio-repo"

# === Fase 1: Inventario dei segreti dalla piattaforma sorgente ===
echo "=== Inventario Segreti ==="

# GitLab: elencare le variabili CI/CD (solo nomi, non valori)
# curl -s -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
#   "https://gitlab.com/api/v4/projects/ID/variables" \
#   | jq -r '.[] | {key: .key, protected: .protected, masked: .masked}'

# Azure DevOps: elencare le variabili
# curl -s -u ":$AZ_PAT" \
#   "https://dev.azure.com/org/project/_apis/distributedtask/variablegroups?api-version=7.0" \
#   | jq '.value[].variables | keys[]'

# Jenkins: elencare le credentials (solo ID, non valori)
# curl -s -u "admin:$JENKINS_TOKEN" \
#   "https://jenkins.example.com/credentials/api/json?depth=2" \
#   | jq '.stores.system.domains._.credentials[].id'

# === Fase 2: Classificare i segreti ===
cat > secrets-inventory.md << 'EOF'
| Nome Segreto | Tipo | Livello | Vecchia Piattaforma | Nuovo Valore | Stato |
|-------------|------|---------|--------------------|--------------| ------|
| DOCKER_REGISTRY | URL | Org | GitLab CI Variable | Stesso | [ ] |
| DATABASE_URL | Connection String | Env (prod) | GitLab Protected | RUOTARE | [ ] |
| DEPLOY_SSH_KEY | SSH Key | Env (prod) | Jenkins Credential | RUOTARE | [ ] |
| NPM_TOKEN | Token | Org | GitLab CI Variable | RUOTARE | [ ] |
| AWS_ACCESS_KEY_ID | Credential | Repo | Env var Jenkins | Migrare a OIDC | [ ] |
EOF

echo "File secrets-inventory.md creato."
echo "Completare manualmente e usare come checklist durante la migrazione."

# === Fase 3: Creare i segreti su GitHub ===
# Esempio di creazione batch da file (ATTENZIONE: non committare questo file!)
while IFS='=' read -r key value; do
  [ -z "$key" ] && continue
  [[ "$key" == \#* ]] && continue
  gh secret set "$key" --repo "${GITHUB_ORG}/${GITHUB_REPO}" --body "$value"
  echo "Creato: $key"
done < secrets.env  # File locale, MAI committato
```

### OIDC e Credenziali Effimere

Una delle best practice moderne per la gestione dei segreti è l'utilizzo di OIDC (OpenID Connect) per ottenere credenziali effimere (short-lived) anziché memorizzare credenziali statiche nei segreti del repository. GitHub Actions supporta nativamente OIDC per i principali cloud provider.

```yaml
# === Esempio: AWS con OIDC (nessun segreto AWS memorizzato) ===
# .github/workflows/deploy-aws-oidc.yml
name: Deploy AWS (OIDC)
on:
  push:
    branches: [main]

permissions:
  id-token: write   # Necessario per OIDC
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-role
          aws-region: eu-west-1
          # Non serve AWS_ACCESS_KEY_ID o AWS_SECRET_ACCESS_KEY!
          # Il token è effimero e scade dopo la sessione

      - run: aws s3 sync dist/ s3://my-bucket/

# === Esempio: Azure con OIDC ===
# Prerequisito: configurare federated credentials in Azure AD
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
          # Nessun client secret memorizzato!

# === Esempio: GCP con OIDC ===
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/123/locations/global/workloadIdentityPools/github/providers/github'
          service_account: 'deploy@project.iam.gserviceaccount.com'
          # Nessuna service account key memorizzata!
```

### Rotazione Post-Migrazione

Dopo la migrazione, è mandatorio ruotare tutti i segreti che potrebbero essere stati esposti durante il processo di transizione. I segreti che erano memorizzati sulla vecchia piattaforma devono essere considerati potenzialmente compromessi, specialmente se il vecchio sistema resta attivo per un periodo di coesistenza.

```bash
#!/bin/bash
# rotate-secrets-post-migration.sh

echo "=== Rotazione Segreti Post-Migrazione ==="
echo "Data: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Ruotare token di accesso API
echo "[1/5] Ruotare token API..."
# Generare nuovi token dalle rispettive piattaforme
# NPM: npm token create
# Docker Hub: tramite UI o API
# Cloud provider: tramite CLI o console

# 2. Ruotare chiavi SSH di deploy
echo "[2/5] Ruotare chiavi SSH..."
ssh-keygen -t ed25519 -f deploy-key -N "" -C "deploy@$(date +%Y%m%d)"
gh secret set DEPLOY_SSH_KEY --repo "mia-org/mio-repo" --env "production" < deploy-key

# 3. Ruotare database credentials
echo "[3/5] Ruotare credenziali database..."
# Esempio per PostgreSQL:
# ALTER USER deploy_user WITH PASSWORD 'nuovo-password-sicuro';
# gh secret set DATABASE_URL --body "postgresql://..."

# 4. Invalidare i vecchi token sulla piattaforma sorgente
echo "[4/5] Invalidare vecchi token..."
# GitLab: revocare il PAT usato per la migrazione
# Jenkins: revocare le credentials usate
# Azure DevOps: revocare il PAT usato

# 5. Verificare che le pipeline funzionino con i nuovi segreti
echo "[5/5] Verificare pipeline..."
gh workflow run ci.yml --repo "mia-org/mio-repo"

echo ""
echo "=== Rotazione completata ==="
echo "AZIONE RICHIESTA: Verificare il risultato dell'esecuzione CI"
```

---

## Migrazione Webhook e Integrazioni

La riconfigurazione dei webhook e delle integrazioni esterne è un passo spesso sottovalutato nella migrazione. Slack, Jira, SonarQube e altri strumenti devono essere riconfigurati per puntare ai nuovi repository GitHub. La migrazione è anche un'opportunità per passare da webhook tradizionali a GitHub Apps, che offrono permessi più granulari e rate limit più alti.

### Riconfigurazione Slack

```bash
# === Opzione 1: GitHub App per Slack (raccomandata) ===
# Installare la GitHub App ufficiale per Slack
# https://slack.github.com/
# Nella conversazione Slack:
# /github subscribe mia-org/mio-repo issues pulls commits releases
# /github subscribe mia-org/mio-repo workflows:{nome-workflow}

# === Opzione 2: Webhook Incoming Slack + GitHub Webhook ===
# 1. Creare un Incoming Webhook in Slack
#    Slack → Apps → Incoming Webhooks → Add to Slack
#    Copiare l'URL del webhook

# 2. Configurare il webhook nel repository GitHub
gh api repos/mia-org/mio-repo/hooks \
  --method POST \
  -f name="web" \
  -f active=true \
  -f config[url]="https://hooks.slack.com/services/T00000/B00000/XXXXXXXXX" \
  -f config[content_type]="json" \
  -f events[]="push" \
  -f events[]="pull_request" \
  -f events[]="issues" \
  -f events[]="release"

# === Opzione 3: GitHub Actions per notifiche personalizzate ===
# Creare un workflow di notifica
# Vedi esempio nella sezione Jenkins → GitHub Actions (job notify)
```

### Riconfigurazione Jira

```bash
# === Opzione 1: GitHub for Jira App (raccomandata) ===
# Installare da: https://github.com/marketplace/jira-software-github
# Collegare l'organizzazione GitHub all'istanza Jira
# Le commit e PR che menzionano chiavi Jira (es. PROJ-123)
# verranno automaticamente linkate alle issue Jira

# === Opzione 2: Jira Automation con webhook GitHub ===
# In Jira → Project Settings → Automation
# Creare una regola: "When GitHub event received"
# Copiare il webhook URL generato da Jira

# Configurare il webhook nel repository GitHub
gh api repos/mia-org/mio-repo/hooks \
  --method POST \
  -f name="web" \
  -f active=true \
  -f config[url]="https://automation.atlassian.com/pro/hooks/XXXXXX" \
  -f config[content_type]="json" \
  -f events[]="push" \
  -f events[]="pull_request"

# === Convenzione nei commit per linking automatico ===
# Usare la chiave Jira nel messaggio di commit:
# git commit -m "feat: aggiunta autenticazione OAuth2 [PROJ-456]"
# GitHub for Jira App linkerà automaticamente il commit alla issue Jira
```

### Riconfigurazione SonarQube

```bash
# === Configurazione SonarQube con GitHub Actions ===
# 1. Creare un token SonarQube per GitHub Actions
#    SonarQube → My Account → Security → Generate Token

# 2. Salvare come segreto GitHub
gh secret set SONAR_TOKEN --repo "mia-org/mio-repo" --body "squ_xxxxx"
gh secret set SONAR_HOST_URL --repo "mia-org/mio-repo" --body "https://sonarqube.azienda.com"

# 3. Configurare il progetto SonarQube
# sonar-project.properties
cat > sonar-project.properties << 'EOF'
sonar.projectKey=mia-org_mio-repo
sonar.organization=mia-org
sonar.sources=src
sonar.tests=tests
sonar.javascript.lcov.reportPaths=coverage/lcov.info
sonar.coverage.exclusions=**/*.test.ts,**/*.spec.ts
EOF

# 4. Aggiungere il workflow GitHub Actions
# Vedi esempio nella sezione Jenkins → GitHub Actions (job sonarqube)

# 5. Configurare la PR decoration in SonarQube
# SonarQube → Administration → Configuration → GitHub
# Inserire GitHub App ID e Private Key
# Questo permette a SonarQube di commentare direttamente sulle PR GitHub
```

### GitHub Apps vs Webhook Tradizionali

Nella migrazione, è consigliato preferire le GitHub Apps ai webhook tradizionali dove possibile:

| Aspetto | Webhook Tradizionale | GitHub App |
|---------|---------------------|------------|
| Rate limit | 5000 req/h (per IP) | 5000 req/h (per installazione) |
| Autenticazione | Secret condiviso | JWT + Installation token |
| Permessi | Tutti gli eventi selezionati | Granulari per tipo di risorsa |
| Installazione | Per repository | Per organizzazione o repository |
| Retry automatico | No | Si (con backoff esponenziale) |
| Delivery log | Si | Si (con dettagli extra) |
| Sicurezza | HMAC-SHA256 signature | HMAC-SHA256 + JWT |
| Marketplace | N/A | Pubblicabile su Marketplace |

---

## Strategie di Rollback e Coesistenza

Una migrazione senza piano di rollback è una scommessa. Anche con test approfonditi, problemi imprevisti possono emergere dopo il cutover. La strategia di coesistenza permette un periodo di transizione sicuro dove entrambe le piattaforme sono operative.

### Periodo di Dual-Run

Durante il periodo di dual-run, entrambe le piattaforme restano attive. I repository sulla vecchia piattaforma sono impostati in sola lettura (o con accesso limitato), mentre GitHub diventa la piattaforma primaria. Questo periodo dura tipicamente 2-4 settimane.

```bash
#!/bin/bash
# dual-run-monitor.sh
# Monitorare la salute della migrazione durante il periodo di coesistenza

GITHUB_ORG="mia-org"
OLD_PLATFORM="gitlab"  # o "bitbucket", "azure"

echo "=== Dual-Run Health Check ==="
echo "Data: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Verificare che nessuno stia pushando sulla vecchia piattaforma
echo ""
echo "--- Attività sulla vecchia piattaforma ---"
# Per GitLab:
if [ "$OLD_PLATFORM" = "gitlab" ]; then
  RECENT_PUSHES=$(curl -s -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
    "https://gitlab.com/api/v4/projects/ID/events?action=pushed&after=$(date -d '-1 day' +%Y-%m-%d)" \
    | jq length)
  echo "Push nelle ultime 24h su GitLab: $RECENT_PUSHES"
  if [ "$RECENT_PUSHES" -gt 0 ]; then
    echo "ATTENZIONE: Qualcuno sta ancora pushando su GitLab!"
  fi
fi

# 2. Verificare la salute delle pipeline GitHub
echo ""
echo "--- Stato Pipeline GitHub ---"
gh run list --repo "${GITHUB_ORG}/mio-repo" --limit 5 \
  --json conclusion,status,name,createdAt \
  --jq '.[] | "\(.name): \(.conclusion // .status) (\(.createdAt))"'

# 3. Verificare che i segreti funzionino
echo ""
echo "--- Ultimo workflow eseguito ---"
LAST_RUN=$(gh run list --repo "${GITHUB_ORG}/mio-repo" --limit 1 \
  --json conclusion --jq '.[0].conclusion')
if [ "$LAST_RUN" = "failure" ]; then
  echo "ATTENZIONE: L'ultimo workflow è fallito!"
  echo "Verificare i segreti e le configurazioni"
fi

# 4. Contare le PR aperte
echo ""
echo "--- Attività su GitHub ---"
PR_COUNT=$(gh pr list --repo "${GITHUB_ORG}/mio-repo" --json number --jq 'length')
echo "PR aperte: $PR_COUNT"

ISSUE_COUNT=$(gh issue list --repo "${GITHUB_ORG}/mio-repo" --json number --jq 'length')
echo "Issue aperte: $ISSUE_COUNT"

echo ""
echo "=== Health Check Completato ==="
```

### Piano di Emergenza

```bash
#!/bin/bash
# emergency-rollback.sh
# USARE SOLO IN CASO DI EMERGENZA

echo "=== ROLLBACK DI EMERGENZA ==="
echo "ATTENZIONE: Questo script ripristina la vecchia piattaforma come primaria"
echo ""
read -p "Confermare il rollback? Digitare 'ROLLBACK' per procedere: " confirm
if [ "$confirm" != "ROLLBACK" ]; then
  echo "Rollback annullato"
  exit 1
fi

GITHUB_ORG="mia-org"
GITHUB_REPO="mio-repo"

echo ""
echo "=== Fase 1: Sincronizzare le modifiche da GitHub alla vecchia piattaforma ==="

# Clonare la versione più recente da GitHub
git clone "https://github.com/${GITHUB_ORG}/${GITHUB_REPO}.git" /tmp/rollback-sync
cd /tmp/rollback-sync

# Aggiungere il vecchio remote
git remote add old-platform "https://gitlab.com/org/repo.git"

# Push verso la vecchia piattaforma
git push old-platform --all --force
git push old-platform --tags

echo ""
echo "=== Fase 2: Ripristinare l'accesso sulla vecchia piattaforma ==="
echo "AZIONE MANUALE: Rimuovere il read-only dalla vecchia piattaforma"
echo "AZIONE MANUALE: Riabilitare le pipeline CI/CD sulla vecchia piattaforma"
echo "AZIONE MANUALE: Comunicare al team il rollback"

echo ""
echo "=== Fase 3: Disabilitare temporaneamente GitHub ==="
echo "AZIONE MANUALE: Archiviare il repository su GitHub per prevenire confusione"
echo "AZIONE MANUALE: Aggiornare i webhook per puntare alla vecchia piattaforma"

echo ""
echo "=== Rollback completato ==="
echo "IMPORTANTE: Analizzare la causa del fallimento prima di riprovare la migrazione"
echo "Documentare il problema in un post-mortem"

# Pulizia
cd /
rm -rf /tmp/rollback-sync
```

#### Checklist di Rollback

```markdown
## Checklist Rollback di Emergenza

### Trigger per il Rollback
- [ ] Pipeline CI/CD falliscono ripetutamente su GitHub (non risolvibile entro 4h)
- [ ] Perdita di dati confermata (commit, issue, PR mancanti)
- [ ] Integrazioni critiche non funzionanti (deploy bloccati)
- [ ] Più del 30% del team non riesce a lavorare su GitHub

### Azioni Immediate (entro 1 ora)
- [ ] Comunicare al team: "ROLLBACK IN CORSO - tornare alla vecchia piattaforma"
- [ ] Sincronizzare le modifiche recenti da GitHub alla vecchia piattaforma
- [ ] Riabilitare l'accesso in scrittura sulla vecchia piattaforma
- [ ] Riabilitare le pipeline CI/CD sulla vecchia piattaforma

### Azioni Successive (entro 24 ore)
- [ ] Archiviare i repository GitHub per prevenire confusione
- [ ] Aggiornare webhook e integrazioni alla vecchia piattaforma
- [ ] Condurre un'analisi root-cause del fallimento
- [ ] Documentare il post-mortem
- [ ] Pianificare un nuovo tentativo con le correzioni necessarie

### Prevenzione per il Prossimo Tentativo
- [ ] Estendere il periodo di pilota
- [ ] Aggiungere più test automatizzati alla validazione
- [ ] Pianificare il cutover in un periodo di bassa attività
- [ ] Assicurarsi che il team sia stato formato adeguatamente
```

---

## Checklist di Migrazione

```markdown
## Checklist Pre-Migrazione

### Inventario
- [ ] Lista completa di tutti i repository da migrare
- [ ] Dimensione di ogni repository (storage, numero commit, numero branch)
- [ ] Dipendenze tra repository (submodules, package references)
- [ ] Lista di tutte le pipeline CI/CD per ogni repository
- [ ] Lista di segreti e variabili d'ambiente per ogni pipeline
- [ ] Lista di integrazioni esterne (Slack, Jira, SonarQube, etc.)
- [ ] Lista di webhook configurati
- [ ] Mapping degli utenti (vecchia piattaforma -> GitHub)

### Preparazione GitHub
- [ ] Organizzazione GitHub creata e configurata
- [ ] SSO/SAML configurato (se enterprise)
- [ ] Team e permessi definiti
- [ ] Branch protection rules pronte
- [ ] Template per issue e PR preparati
- [ ] CODEOWNERS file preparato
- [ ] Segreti configurati in GitHub (org level o repo level)
- [ ] GitHub Actions abilitato e configurato

### Preparazione CI/CD
- [ ] Pipeline CI/CD convertite in GitHub Actions
- [ ] Pipeline testate su un repository pilota
- [ ] Segreti migrati e verificati
- [ ] Runner self-hosted configurati (se necessari)
- [ ] Ambienti (staging, production) creati in GitHub

### Comunicazione
- [ ] Piano di migrazione comunicato al team
- [ ] Date di freeze del codice definite
- [ ] Guida rapida GitHub preparata per il team
- [ ] Sessione di formazione pianificata
- [ ] Canale di supporto dedicato (Slack, Teams)

## Checklist Giorno della Migrazione

### Per Ogni Repository
- [ ] Codice freezato sulla vecchia piattaforma
- [ ] Repository clonato (bare) dalla vecchia piattaforma
- [ ] Tutti i branch migrati
- [ ] Tutti i tag migrati
- [ ] LFS objects migrati (se presente)
- [ ] Push su GitHub completato
- [ ] Branch protection attivata
- [ ] Pipeline CI/CD funzionante
- [ ] Segreti verificati
- [ ] Webhook ricreati

### Post-Push
- [ ] Build CI passa su tutti i branch principali
- [ ] Deploy di test funzionante
- [ ] Issue/ticket migrati (se necessario)
- [ ] Wiki migrata (se presente)
- [ ] README aggiornato con nuovi badge CI

## Checklist Post-Migrazione

- [ ] Tutti i team hanno accesso ai repository corretti
- [ ] Tutte le integrazioni funzionano
- [ ] Le pipeline CI/CD funzionano per PR, push, e tag
- [ ] I deploy automatici funzionano
- [ ] Le notifiche sono configurate
- [ ] I vecchi repository sono archiviati (read-only)
- [ ] I redirect sono configurati (se possibile)
- [ ] La documentazione è aggiornata con i nuovi URL
- [ ] Il team è stato formato e ha risorse di riferimento
- [ ] I bookmark/link nei tool esterni sono aggiornati
```

---

## URL Redirects e Comunicazione

### Redirect degli URL

Quando si migra, tutti gli URL della vecchia piattaforma (nei commenti di codice, nella documentazione, nei ticket) diventano invalidi. Se possibile, configurare dei redirect.

#### GitLab

```
# Se si ha accesso al server GitLab, configurare un redirect:
# In nginx config per il dominio GitLab:
location ~ ^/(.+) {
  return 301 https://github.com/nuova-org/$1;
}

# Se non si ha accesso, aggiornare il README nel repository GitLab:
# "Questo repository è stato migrato su https://github.com/org/repo"
```

#### Aggiornamento Riferimenti nel Codebase

```bash
#!/bin/bash
# update-references.sh - Aggiorna tutti i riferimenti alla vecchia piattaforma

OLD_URL="gitlab.com/vecchia-org"
NEW_URL="github.com/nuova-org"

# Trovare tutti i file con riferimenti alla vecchia piattaforma
echo "File con riferimenti a $OLD_URL:"
grep -rl "$OLD_URL" --include="*.md" --include="*.yml" --include="*.yaml" \
  --include="*.json" --include="*.toml" --include="*.cfg" --include="*.ini" \
  --include="*.txt" --include="*.rst" .

# Sostituire (con conferma)
read -p "Sostituire tutti i riferimenti? (y/n) " confirm
if [ "$confirm" = "y" ]; then
  grep -rl "$OLD_URL" --include="*.md" --include="*.yml" --include="*.yaml" \
    --include="*.json" --include="*.toml" --include="*.cfg" \
    . | xargs sed -i "s|${OLD_URL}|${NEW_URL}|g"
  echo "Riferimenti aggiornati"
fi
```

### Piano di Comunicazione

```markdown
## Comunicazione Migrazione a GitHub

### T-2 settimane: Annuncio
Oggetto: Migrazione dei repository a GitHub - Pianificazione

Cari colleghi,
Stiamo pianificando la migrazione dei nostri repository da [piattaforma] a GitHub.

Timeline:
- Settimana 1-2: Migrazione pilota (repository non critici)
- Settimana 3: Migrazione batch 1 (servizi backend)
- Settimana 4: Migrazione batch 2 (frontend e mobile)
- Settimana 5: Decommissioning vecchia piattaforma

Cosa dovete fare:
1. Creare un account GitHub (se non lo avete)
2. Aggiungere la vostra SSH key a GitHub
3. Partecipare alla sessione di formazione del [data]

### T-1 giorno: Reminder
Oggetto: DOMANI - Code Freeze per Migrazione

Ricordiamo che domani [data] alle [ora] inizierà il code freeze
per la migrazione dei repository del batch [N].

Azioni richieste:
- Mergiate tutte le MR/PR in corso entro oggi
- Pushate tutti i commit locali
- Non pushate domani fino a comunicazione di completamento

### T+0: Completamento
Oggetto: Migrazione Completata - Nuovi URL Repository

La migrazione del batch [N] è completata!

Nuovi URL:
- [vecchio-nome] → https://github.com/org/[nuovo-nome]
- ...

Prossimi passi:
1. Clonate i repository dal nuovo URL
2. Aggiornate i vostri remote: git remote set-url origin [nuovo-url]
3. Verificate che le vostre pipeline CI funzionino
```

---

## Validazione Post-Migrazione

```bash
#!/bin/bash
# validate-migration.sh

GITHUB_ORG="${GITHUB_ORG:?}"
GITHUB_REPO="${GITHUB_REPO:?}"
OLD_REPO_PATH="${OLD_REPO_PATH:?}"  # Path al clone bare del vecchio repo

echo "=== Validazione Migrazione: $GITHUB_REPO ==="

# Clone del nuovo repository
git clone "https://github.com/${GITHUB_ORG}/${GITHUB_REPO}.git" /tmp/validate-new
cd /tmp/validate-new

ERRORS=0

# 1. Verificare i branch
echo ""
echo "--- Verifica Branch ---"
OLD_BRANCHES=$(cd "$OLD_REPO_PATH" && git branch | wc -l)
NEW_BRANCHES=$(git branch -r | grep -v HEAD | wc -l)
echo "Branch vecchio repo: $OLD_BRANCHES"
echo "Branch nuovo repo: $NEW_BRANCHES"
if [ "$OLD_BRANCHES" -ne "$NEW_BRANCHES" ]; then
  echo "ATTENZIONE: Numero di branch diverso!"
  ERRORS=$((ERRORS + 1))
fi

# 2. Verificare i tag
echo ""
echo "--- Verifica Tag ---"
OLD_TAGS=$(cd "$OLD_REPO_PATH" && git tag | wc -l)
NEW_TAGS=$(git tag | wc -l)
echo "Tag vecchio repo: $OLD_TAGS"
echo "Tag nuovo repo: $NEW_TAGS"
if [ "$OLD_TAGS" -ne "$NEW_TAGS" ]; then
  echo "ATTENZIONE: Numero di tag diverso!"
  ERRORS=$((ERRORS + 1))
fi

# 3. Verificare l'hash dell'ultimo commit
echo ""
echo "--- Verifica Commit ---"
OLD_HEAD=$(cd "$OLD_REPO_PATH" && git rev-parse HEAD)
NEW_HEAD=$(git rev-parse HEAD)
echo "HEAD vecchio: $OLD_HEAD"
echo "HEAD nuovo: $NEW_HEAD"
if [ "$OLD_HEAD" != "$NEW_HEAD" ]; then
  echo "NOTA: Gli hash differiscono (normale se si è usato filter o rebase)"
fi

# 4. Verificare il contenuto dei file
echo ""
echo "--- Verifica Contenuto ---"
OLD_FILES=$(cd "$OLD_REPO_PATH" && git ls-tree -r HEAD --name-only | wc -l)
NEW_FILES=$(git ls-tree -r HEAD --name-only | wc -l)
echo "File vecchio repo: $OLD_FILES"
echo "File nuovo repo: $NEW_FILES"
if [ "$OLD_FILES" -ne "$NEW_FILES" ]; then
  echo "ATTENZIONE: Numero di file diverso!"
  ERRORS=$((ERRORS + 1))
fi

# 5. Verificare la CI
echo ""
echo "--- Verifica CI ---"
WORKFLOWS=$(ls .github/workflows/*.yml 2>/dev/null | wc -l)
echo "Workflow GitHub Actions trovati: $WORKFLOWS"
if [ "$WORKFLOWS" -eq 0 ]; then
  echo "ATTENZIONE: Nessun workflow trovato!"
  ERRORS=$((ERRORS + 1))
fi

# 6. Verificare la branch protection
echo ""
echo "--- Verifica Branch Protection ---"
PROTECTION=$(gh api repos/${GITHUB_ORG}/${GITHUB_REPO}/branches/main/protection 2>/dev/null)
if [ $? -eq 0 ]; then
  echo "Branch protection attiva su main"
else
  echo "ATTENZIONE: Branch protection non configurata su main!"
  ERRORS=$((ERRORS + 1))
fi

# Risultato
echo ""
echo "=== Risultato ==="
if [ "$ERRORS" -eq 0 ]; then
  echo "SUCCESSO: Nessun problema rilevato"
else
  echo "ATTENZIONE: $ERRORS problemi rilevati"
fi

# Pulizia
rm -rf /tmp/validate-new
```

---

## Errori Comuni

### 1. Perdita di Branch o Tag

```bash
# Problema: git push --mirror non ha pushato tutti i branch
# Causa: il remote origin puntava ancora alla vecchia piattaforma

# Soluzione: assicurarsi che il remote sia corretto prima del push
git remote -v
git remote set-url origin "https://github.com/org/repo.git"
git push --all origin
git push --tags origin
```

### 2. File LFS Mancanti

```bash
# Problema: i file LFS risultano come pointer anziché contenuto reale
# Causa: git lfs fetch --all non è stato eseguito prima del push

# Soluzione:
git lfs fetch --all  # Dal vecchio remote
git lfs push --all origin  # Al nuovo remote
```

### 3. Dimensione Repository Eccessiva

```bash
# Problema: il repository è troppo grande per GitHub (>5 GB)
# Causa: file binari nella storia

# Soluzione: usare BFG Repo Cleaner per rimuovere file grandi dalla storia
java -jar bfg.jar --strip-blobs-bigger-than 100M repo.git
cd repo.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### 4. Pipeline CI/CD Rotte dopo la Migrazione

Le cause più comuni sono:
- Segreti non migrati
- Variabili d'ambiente con nomi diversi
- Path dei file modificati
- Servizi di integrazione non riconfigurati

```bash
# Verificare che tutti i segreti siano configurati
gh secret list --repo org/repo

# Confrontare con la lista dei segreti necessari dalla vecchia piattaforma
```

### 5. Permessi Errati

```bash
# Problema: sviluppatori non possono pushare o creare PR
# Causa: i team e i permessi non sono stati configurati correttamente

# Verificare i permessi
gh api repos/{org}/{repo}/collaborators \
  --jq '.[] | {login: .login, permission: .permissions}'

# Aggiungere team con i permessi corretti
gh api orgs/{org}/teams/{team}/repos/{org}/{repo} \
  --method PUT \
  -f permission=push
```

---

## Riepilogo

La migrazione a GitHub è un progetto che richiede pianificazione meticolosa, esecuzione precisa e validazione approfondita. I repository Git sono relativamente semplici da migrare (sono Git dopotutto), ma il valore reale di una piattaforma risiede nelle pipeline CI/CD, nelle issue, nei processi di review, nelle integrazioni, e nelle abitudini del team.

La conversione delle pipeline CI/CD è tipicamente la parte più impegnativa della migrazione: ogni piattaforma ha il proprio DSL, le proprie convenzioni e le proprie funzionalità uniche. Il mapping non è sempre 1:1, e spesso la migrazione è un'opportunità per ripensare e migliorare le pipeline.

La comunicazione con il team è altrettanto importante quanto la parte tecnica. Una migrazione tecnicamente perfetta può fallire se il team non è preparato, non ha ricevuto formazione, e non conosce i nuovi processi. Investire tempo nella formazione e nel supporto durante la transizione è un investimento che si ripaga rapidamente.

Infine, ricordare che la migrazione è anche un'opportunità: per pulire repository non più necessari, standardizzare i processi, eliminare debito tecnico nelle pipeline CI/CD, e adottare best practice che la vecchia piattaforma non supportava o rendeva difficili.

---

## Esercizi Pratici

### Esercizio 1: Migrazione Repository da GitLab

Migra un repository GitLab completo a GitHub preservando tutta la storia:

```bash
# 1. Clone mirror del repository GitLab:
#    git clone --mirror https://gitlab.com/org/project.git
#    cd project.git
# 2. Verificare la completezza:
#    git branch -a           # Tutti i branch presenti?
#    git tag -l              # Tutti i tag presenti?
#    git log --oneline | wc -l  # Contare i commit
# 3. Creare il repository destinazione su GitHub:
#    gh repo create org/project --private
# 4. Push mirror verso GitHub:
#    git push --mirror https://github.com/org/project.git
# 5. Verificare su GitHub:
#    - Stesso numero di commit, branch e tag
#    - La storia è intatta (git log identico)
#    - Se presente Git LFS, migrare separatamente:
#      git lfs fetch --all
#      git lfs push --all https://github.com/org/project.git

# Verifica:
# - git log su GitLab e GitHub producono output identico
# - Tutti i branch e tag sono presenti
# - File LFS accessibili (se applicabile)
```

**Criteri di successo:** storia identica, zero commit persi, LFS funzionante.

### Esercizio 2: Conversione Pipeline GitLab CI in GitHub Actions

Converti un `.gitlab-ci.yml` completo in GitHub Actions:

```yaml
# GitLab CI di partenza:
# stages: [lint, test, build, deploy]
# variables: { NODE_VERSION: "20" }
# cache: { key: ${CI_COMMIT_REF_SLUG}, paths: [node_modules/] }
# lint: { stage: lint, script: [npm ci, npm run lint] }
# test: { stage: test, script: [npm test], coverage: '/Statements.*?(\d+\.?\d*)%/' }
# build: { stage: build, script: [npm run build], artifacts: { paths: [dist/] } }
# deploy: { stage: deploy, script: [./deploy.sh], environment: { name: production } }

# Compiti:
# 1. Mappare stages → job dependencies (needs:)
# 2. Mappare variables → env: nel workflow
# 3. Mappare cache → actions/cache@v4
# 4. Mappare artifacts → actions/upload-artifact@v4
# 5. Mappare coverage → coverage report come PR comment
# 6. Mappare environment → GitHub Environments con protection rules
# 7. Aggiungere permissions: espliciti

# Verifica:
# - La pipeline GitHub Actions produce lo stesso risultato
# - I tempi di esecuzione sono comparabili
# - Il coverage report è visibile nella PR
```

### Esercizio 3: Migrazione Issue e Wiki

Trasferisci issue e wiki da un'altra piattaforma a GitHub:

```bash
# 1. Esportare le issue da GitLab via API:
#    curl -s "https://gitlab.com/api/v4/projects/PROJECT_ID/issues?per_page=100" \
#      -H "PRIVATE-TOKEN: $GITLAB_TOKEN" > issues.json
# 2. Per ogni issue, creare la corrispondente su GitHub:
#    - Mappare labels (GitLab labels → GitHub labels)
#    - Mappare assignee (gitlab username → github username)
#    - Preservare la data di creazione nel body
#    - Migrare i commenti
# 3. Scrivere uno script di migrazione:
#    jq -r '.[] | {title, description, labels}' issues.json | while read issue; do
#      gh issue create --title "$title" --body "$body" --label "$labels"
#    done
# 4. Migrare la wiki:
#    git clone https://gitlab.com/org/project.wiki.git
#    # Convertire formato (se necessario)
#    git push https://github.com/org/project.wiki.git
# 5. Verificare:
#    - Stesso numero di issue (con note sulla migrazione)
#    - Wiki accessibile e formattata correttamente
#    - Link interni aggiornati

# Nota: GitHub Enterprise Importer può automatizzare parte di questo processo
```

### Esercizio 4: Migrazione da Bitbucket con Pipeline Conversion

Migra un progetto da Bitbucket Cloud a GitHub:

```bash
# 1. Clonare il repository Bitbucket:
#    git clone --mirror https://bitbucket.org/team/project.git
# 2. Convertire bitbucket-pipelines.yml → .github/workflows/ci.yml
#    Mapping chiave:
#    - pipelines.default → on: push (senza branch filter)
#    - pipelines.branches.main → on: push: branches: [main]
#    - pipelines.pull-requests → on: pull_request
#    - step.caches → actions/cache@v4
#    - step.artifacts → actions/upload-artifact@v4
#    - pipe: → uses: (trovare l'action GitHub equivalente)
#    - deployment → environment
# 3. Migrazione delle variabili:
#    - Repository variables → GitHub repository secrets/variables
#    - Deployment variables → Environment secrets
#    - Secured variables → GitHub secrets
# 4. Riconfiguare webhook e integrazioni:
#    - Jira: installare la GitHub for Jira app
#    - Slack: configurare GitHub integration
# 5. Testare la pipeline convertita prima del cutover

# Verifica:
# - Pipeline produce gli stessi artifact
# - Deploy funziona verso gli stessi target
# - Integrazioni (Jira, Slack) ricevono eventi
```

### Esercizio 5: Cutover Plan e Validazione

Crea e esegui un piano di cutover completo:

```bash
# 1. Pre-cutover checklist:
#    [ ] Repository migrato e verificato (esercizio 1)
#    [ ] Pipeline CI/CD convertita e testata (esercizio 2)
#    [ ] Issue e wiki migrati (esercizio 3)
#    [ ] Secrets configurati su GitHub
#    [ ] Branch protection rules configurate
#    [ ] CODEOWNERS creato
#    [ ] Team e permessi configurati
#    [ ] Webhook e integrazioni configurati
#    [ ] DNS/redirect dalla vecchia piattaforma (se applicabile)
# 2. Cutover day:
#    a. Comunicare al team: freeze del repository vecchio
#    b. Sync finale: git fetch --all dalla vecchia piattaforma
#    c. Push mirror verso GitHub
#    d. Verificare l'integrità (confronto hash dell'ultimo commit)
#    e. Eseguire la pipeline CI su GitHub → deve passare
#    f. Impostare il repository vecchio come read-only
#    g. Aggiungere un notice nel README del repository vecchio
# 3. Post-cutover validation:
#    - Tutti i developer possono clonare e pushare
#    - CI/CD funziona correttamente
#    - Integrazioni ricevono eventi
#    - Nessun secret mancante
# 4. Rollback plan:
#    - Se problemi critici entro 48h, ripristinare il repository vecchio
#    - Mantenere il repository vecchio in read-only per 30 giorni
```

---

## Letture Consigliate

- **GitHub Docs**: "Importing a repository with GitHub Importer" — https://docs.github.com/en/migrations/importing-source-code/using-github-importer/importing-a-repository-with-github-importer (consultato: 2026-05-24)
- **GitHub Docs**: "GitHub Enterprise Importer" — https://docs.github.com/en/migrations/using-github-enterprise-importer (consultato: 2026-05-24)
- **GitHub Blog**: "Migrate to GitHub Actions" — https://github.blog/developer-skills/github/migrate-your-ci-cd-to-github-actions/ (consultato: 2026-05-24)
- **GitLab Docs**: "Migrating from GitLab to GitHub" — https://docs.gitlab.com/ee/user/project/import/github.html (consultato: 2026-05-24)
- **Libro**: "Git for Teams" di Emma Jane Hogbin Westby, O'Reilly Media, 2015 — gestione della transizione tra piattaforme
- **Articolo**: "Actions Importer — Automating migration to GitHub Actions" — https://docs.github.com/en/actions/migrating-to-github-actions/using-github-actions-importer-to-automate-migrations (consultato: 2026-05-24)

---

## Collegamenti Incrociati

| Modulo | Collegamento | Relazione |
|--------|-------------|-----------|
| 01 | [01-fondamenti-git.md](01-fondamenti-git.md) | Fondamenti Git — clone mirror, push mirror, remote management |
| 03 | [03-piattaforma-github.md](03-piattaforma-github.md) | Piattaforma GitHub — repository creation, settings, teams |
| 19 | [19-github-actions-ci-cd-ricette.md](19-github-actions-ci-cd-ricette.md) | Ricette CI/CD — pipeline target della conversione |
| 17 | [17-github-actions-workflow-sintassi.md](17-github-actions-workflow-sintassi.md) | Sintassi workflow — riferimento per la conversione delle pipeline |
| 09 | [09-git-lfs-submodules-monorepo.md](09-git-lfs-submodules-monorepo.md) | Git LFS — migrazione di file grandi e submodule |
| 12 | [12-github-repository-management.md](12-github-repository-management.md) | Repository management — configurazione post-migrazione |
| 13 | [13-github-issues-projects-collaboration.md](13-github-issues-projects-collaboration.md) | Issues e Projects — destinazione della migrazione issue |
| 16 | [16-github-security-scanning.md](16-github-security-scanning.md) | Security — configurazione security scanning post-migrazione |
| 22 | [22-github-copilot-codespaces-enterprise.md](22-github-copilot-codespaces-enterprise.md) | Enterprise — SAML SSO e user provisioning per migrazione organizzativa |

---

## Glossario Locale

| Termine | Definizione |
|---------|------------|
| **Clone mirror** | Clone completo di un repository inclusi tutti i ref (branch, tag, notes), usato per migrazione fedele |
| **Cutover** | Momento in cui si passa definitivamente dalla vecchia piattaforma alla nuova, con freeze del vecchio sistema |
| **GitHub Enterprise Importer (GEI)** | Tool ufficiale per migrazione massiva di repository, issue, PR da GitLab/Azure DevOps/Bitbucket a GitHub |
| **GitHub Importer** | Tool web di GitHub per importare repository da qualsiasi URL Git accessibile pubblicamente |
| **Actions Importer** | Tool CLI che converte automaticamente pipeline CI/CD da altre piattaforme (GitLab CI, Jenkins, ecc.) in GitHub Actions |
| **Mannequin** | Account placeholder creato durante la migrazione per utenti della piattaforma sorgente non ancora mappati su GitHub |
| **Push mirror** | Operazione `git push --mirror` che replica tutti i ref di un repository verso un remote di destinazione |
| **Redirect** | Reindirizzamento dalla vecchia URL del repository alla nuova URL su GitHub, per evitare link rotti |
| **SCIM mapping** | Associazione tra utenti dell'Identity Provider e account GitHub durante una migrazione enterprise |
| **User mapping** | Tabella di corrispondenza tra username della piattaforma sorgente e username GitHub per attribuzione corretta |
| **Webhook migration** | Processo di riconfigurazione dei webhook dalla vecchia piattaforma verso i nuovi endpoint GitHub |
| **Freeze** | Periodo durante il cutover in cui il repository sorgente è impostato in sola lettura per evitare divergenze |
