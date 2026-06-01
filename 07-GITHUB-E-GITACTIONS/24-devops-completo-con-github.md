---
corso: "GitHub e Git Actions"
fase: "6 — Avanzato"
modulo: 24
titolo: "DevOps Completo con GitHub: Pipeline End-to-End"
versione: "GitHub Actions 2024 / Terraform 1.7"
livello: "Avanzato"
prerequisiti: ["GitHub Actions CI/CD (modulo 19)", "Self-Hosted Runners (modulo 21)", "Docker e Kubernetes base"]
obiettivi:
  - "Costruire una pipeline DevOps end-to-end usando esclusivamente strumenti GitHub"
  - "Configurare CI multi-stage con lint, test, build Docker e security scanning integrati"
  - "Implementare CD con deploy automatico in staging e deploy in produzione con approvazione"
  - "Gestire infrastructure as code con Terraform integrato in GitHub Actions"
  - "Automatizzare release, changelog, documentazione e incident response nel ciclo DevOps"
tag: [devops, github-actions, ci-cd, terraform, docker, kubernetes, monorepo, dependabot, release-automation, incident-response]
---

# 24 — DevOps Completo con GitHub: Pipeline End-to-End

> **Modulo 24** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al termine di questo modulo sarai in grado di:
>
> 1. Costruire una pipeline DevOps end-to-end usando esclusivamente strumenti GitHub
> 2. Configurare CI multi-stage con lint, test, build Docker e security scanning integrati
> 3. Implementare CD con deploy automatico in staging e deploy in produzione con approvazione
> 4. Gestire infrastructure as code con Terraform integrato in GitHub Actions
> 5. Automatizzare release, changelog, documentazione e incident response nel ciclo DevOps

## Idee guida
1. **GitHub stack completo: Issues + Projects + Code + Actions + Packages + Pages + Releases.**
2. **CI: lint + test + build + scan; CD: deploy via OIDC.**
3. **Observability: status badges, deployment notifications.**
4. **GitHub Apps per fine-grained permission.**


## Indice

1. [Introduzione](#introduzione)
2. [Struttura del Progetto (Monorepo)](#struttura-del-progetto)
3. [Strategia di Branching](#strategia-di-branching)
4. [Pipeline CI: Linting, Testing, Building](#pipeline-ci)
5. [Pipeline CD: Staging e Production](#pipeline-cd)
6. [Infrastructure as Code con Terraform](#infrastructure-as-code)
7. [Deployment su Kubernetes](#deployment-kubernetes)
8. [Security Scanning nella Pipeline](#security-scanning)
9. [Gestione delle Dipendenze](#gestione-dipendenze)
10. [Release Automation con Semantic Versioning](#release-automation)
11. [Documentazione con GitHub Pages](#documentazione-github-pages)
12. [Incident Response con GitHub Issues](#incident-response)
13. [Progetto Completo: Tutti i File YAML](#progetto-completo)
14. [GitOps: Modello Dichiarativo e Riconciliazione Continua](#gitops-modello-dichiarativo-e-riconciliazione-continua)
15. [Platform Engineering e Internal Developer Platform](#platform-engineering-e-internal-developer-platform)
16. [DORA Metrics e Misurazione delle Performance DevOps](#dora-metrics-e-misurazione-delle-performance-devops)
17. [Developer Experience (DevEx)](#developer-experience-devex)
18. [Strategie di Deploy Avanzate](#strategie-di-deploy-avanzate)
19. [Supply Chain Security e Attestazione SLSA](#supply-chain-security-e-attestazione-slsa)
20. [Osservabilità Integrata: OpenTelemetry, Prometheus, Grafana](#osservabilità-integrata-opentelemetry-prometheus-grafana)
21. [FinOps: Ottimizzazione dei Costi Cloud](#finops-ottimizzazione-dei-costi-cloud-nel-ciclo-devops)
22. [Workflow Riutilizzabili e Composite Actions](#workflow-riutilizzabili-e-composite-actions)
23. [GitHub Environments e Deployment Protection Rules](#github-environments-e-deployment-protection-rules)
24. [AI e Automazione nel Ciclo DevOps](#ai-e-automazione-nel-ciclo-devops)
25. [Anti-Pattern DevOps e Come Evitarli](#anti-pattern-devops-e-come-evitarli)
26. [OIDC per Deploy Cloud Sicuri](#oidc-per-deploy-cloud-sicuri)
27. [Monitoring e Alerting: SLO, Error Budget e PagerDuty](#monitoring-e-alerting-slo-error-budget-e-pagerduty)
28. [Compliance-as-Code con OPA e Policy Gates](#compliance-as-code-con-opa-e-policy-gates)
29. [Ottimizzazione dei Costi GitHub Actions: Pricing e Strategie 2026](#ottimizzazione-dei-costi-github-actions-pricing-e-strategie-2026)
30. [Chaos Engineering nella Pipeline DevOps](#chaos-engineering-nella-pipeline-devops)
31. [Riepilogo](#riepilogo)

---

## Introduzione

DevOps non è un tool o una tecnologia: è un insieme di pratiche culturali e tecniche che unificano lo sviluppo software (Dev) e le operazioni IT (Ops). L'obiettivo è ridurre il ciclo di vita dello sviluppo, aumentare la frequenza dei deploy, e migliorare la qualità e l'affidabilità del software.

GitHub fornisce un ecosistema completo per implementare una pipeline DevOps end-to-end: GitHub Actions per CI/CD, GitHub Container Registry per le immagini Docker, GitHub Packages per le dipendenze, GitHub Security per la scansione delle vulnerabilità, GitHub Projects per la gestione del lavoro, e GitHub Pages per la documentazione.

Questa guida costruisce un progetto completo da zero, mostrando come ogni pezzo si incastra. L'esempio è una web application composta da un frontend React, un backend Node.js, un database PostgreSQL, e un deployment su Kubernetes. Ogni file di configurazione è completo e funzionante, non un frammento o pseudocodice.

Le pratiche DevOps chiave che implementeremo sono:

- **Continuous Integration**: Ogni commit viene testato automaticamente
- **Continuous Delivery**: Il codice approvato è sempre pronto per il deploy
- **Continuous Deployment**: I deploy avvengono automaticamente in staging, manualmente in produzione
- **Infrastructure as Code**: L'infrastruttura è definita in codice, versionata, e automatizzata
- **Monitoring e Observability**: Metriche, log, e alerting integrati
- **Security Scanning**: Vulnerabilità rilevate automaticamente nella pipeline
- **Incident Response**: Processo strutturato per la gestione degli incidenti

---

## Struttura del Progetto

### Monorepo Layout

```
project-root/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # Pipeline CI principale
│   │   ├── cd-staging.yml            # Deploy in staging
│   │   ├── cd-production.yml         # Deploy in produzione
│   │   ├── security-scan.yml         # Scansione di sicurezza
│   │   ├── release.yml               # Automazione rilasci
│   │   ├── docs.yml                  # Build e deploy documentazione
│   │   └── dependency-update.yml     # Aggiornamento dipendenze
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   ├── feature_request.yml
│   │   └── incident_report.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS
│   └── dependabot.yml
├── apps/
│   ├── frontend/                     # React frontend
│   │   ├── src/
│   │   ├── public/
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── backend/                      # Node.js backend
│       ├── src/
│       ├── tests/
│       ├── Dockerfile
│       ├── package.json
│       └── tsconfig.json
├── packages/
│   └── shared/                       # Codice condiviso
│       ├── src/
│       ├── package.json
│       └── tsconfig.json
├── infrastructure/
│   ├── terraform/
│   │   ├── environments/
│   │   │   ├── staging/
│   │   │   │   ├── main.tf
│   │   │   │   ├── variables.tf
│   │   │   │   └── terraform.tfvars
│   │   │   └── production/
│   │   │       ├── main.tf
│   │   │       ├── variables.tf
│   │   │       └── terraform.tfvars
│   │   └── modules/
│   │       ├── kubernetes/
│   │       ├── database/
│   │       ├── networking/
│   │       └── monitoring/
│   └── kubernetes/
│       ├── base/
│       │   ├── namespace.yml
│       │   ├── backend-deployment.yml
│       │   ├── backend-service.yml
│       │   ├── frontend-deployment.yml
│       │   ├── frontend-service.yml
│       │   ├── ingress.yml
│       │   └── kustomization.yml
│       ├── overlays/
│       │   ├── staging/
│       │   │   ├── kustomization.yml
│       │   │   └── patches/
│       │   └── production/
│       │       ├── kustomization.yml
│       │       └── patches/
│       └── monitoring/
│           ├── prometheus-config.yml
│           └── grafana-dashboard.json
├── docs/
│   ├── index.md
│   ├── architecture.md
│   ├── api-reference.md
│   └── runbook.md
├── scripts/
│   ├── setup-local.sh
│   ├── run-tests.sh
│   └── health-check.sh
├── docker-compose.yml                # Sviluppo locale
├── docker-compose.test.yml           # Test di integrazione
├── package.json                      # Root workspace
├── turbo.json                        # Turborepo configuration
├── .editorconfig
├── .gitignore
├── .gitattributes
├── CHANGELOG.md
├── LICENSE
└── README.md
```

### Configurazione Monorepo con npm Workspaces

```json
// package.json (root)
{
  "name": "my-project",
  "private": true,
  "workspaces": [
    "apps/*",
    "packages/*"
  ],
  "scripts": {
    "build": "turbo build",
    "test": "turbo test",
    "lint": "turbo lint",
    "dev": "turbo dev",
    "type-check": "turbo type-check",
    "clean": "turbo clean",
    "format": "prettier --write \"**/*.{ts,tsx,js,json,md}\""
  },
  "devDependencies": {
    "turbo": "^2.0.0",
    "prettier": "^3.2.0",
    "husky": "^9.0.0",
    "@commitlint/cli": "^19.0.0",
    "@commitlint/config-conventional": "^19.0.0"
  }
}
```

```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**", "build/**"]
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"]
    },
    "lint": {
      "outputs": []
    },
    "type-check": {
      "dependsOn": ["^build"],
      "outputs": []
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "clean": {
      "cache": false
    }
  }
}
```

---

## Strategia di Branching

Per questo progetto usiamo un approccio trunk-based con release branch:

```
main (produzione)
  │
  ├── feature/PROJ-123-add-search     (max 1-2 giorni, merge via PR)
  ├── bugfix/PROJ-456-fix-auth         (max 1 giorno)
  ├── hotfix/PROJ-789-fix-payment      (ore, deploy immediato)
  │
  └── release/v1.2.0                   (branch di stabilizzazione pre-release)
```

Ogni push su `main` viene deployato automaticamente in staging. I deploy in produzione avvengono creando un tag `v*.*.*` o manualmente.

---

## Pipeline CI

### Workflow CI Principale

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

env:
  NODE_VERSION: '20'
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
  TURBO_TEAM: ${{ vars.TURBO_TEAM }}

jobs:
  # ============================================
  # Job 1: Lint e Type Check
  # ============================================
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci

      - name: Lint
        run: npx turbo lint

      - name: Type Check
        run: npx turbo type-check

      - name: Format Check
        run: npx prettier --check "**/*.{ts,tsx,js,json,md}"

      - name: Commit Lint
        if: github.event_name == 'pull_request'
        run: |
          npx commitlint \
            --from ${{ github.event.pull_request.base.sha }} \
            --to ${{ github.event.pull_request.head.sha }} \
            --verbose

  # ============================================
  # Job 2: Test Unitari
  # ============================================
  test-unit:
    name: Unit Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        app: [frontend, backend, shared]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci

      - name: Test ${{ matrix.app }}
        run: |
          if [ "${{ matrix.app }}" = "shared" ]; then
            cd packages/shared
          else
            cd apps/${{ matrix.app }}
          fi
          npm run test -- --coverage --ci

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage-${{ matrix.app }}
          path: |
            apps/${{ matrix.app }}/coverage/
            packages/${{ matrix.app }}/coverage/
          retention-days: 7

  # ============================================
  # Job 3: Test di Integrazione
  # ============================================
  test-integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: [lint, test-unit]
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ['6379:6379']
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      DATABASE_URL: postgresql://test:test@localhost:5432/testdb
      REDIS_URL: redis://localhost:6379
      JWT_SECRET: test-secret-key-for-ci
      NODE_ENV: test

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci

      - name: Build
        run: npx turbo build

      - name: Eseguire migrazioni database
        run: cd apps/backend && npx prisma migrate deploy

      - name: Seed database di test
        run: cd apps/backend && npx prisma db seed

      - name: Test di integrazione
        run: cd apps/backend && npm run test:integration

      - name: Test E2E (API)
        run: |
          cd apps/backend
          npm start &
          sleep 5
          npm run test:e2e

  # ============================================
  # Job 4: Build delle Immagini Docker
  # ============================================
  build:
    name: Build Docker Images
    runs-on: ubuntu-latest
    needs: [test-integration]
    permissions:
      contents: read
      packages: write
    strategy:
      matrix:
        app: [frontend, backend]
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ghcr.io/${{ github.repository }}/${{ matrix.app }}
          tags: |
            type=sha,prefix=
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest,enable={{is_default_branch}}

      - uses: docker/build-push-action@v5
        with:
          context: .
          file: apps/${{ matrix.app }}/Dockerfile
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            NODE_VERSION=${{ env.NODE_VERSION }}
            BUILD_SHA=${{ github.sha }}

      - name: Verifica dimensione immagine
        if: github.event_name != 'pull_request'
        run: |
          IMAGE="ghcr.io/${{ github.repository }}/${{ matrix.app }}:${{ github.sha }}"
          docker pull "$IMAGE"
          SIZE=$(docker image inspect "$IMAGE" --format='{{.Size}}' | numfmt --to=iec)
          echo "Dimensione immagine ${{ matrix.app }}: $SIZE"
          echo "### Docker Image ${{ matrix.app }}" >> $GITHUB_STEP_SUMMARY
          echo "- Tag: \`${{ github.sha }}\`" >> $GITHUB_STEP_SUMMARY
          echo "- Dimensione: $SIZE" >> $GITHUB_STEP_SUMMARY
```

### Dockerfiles

```dockerfile
# apps/backend/Dockerfile
FROM node:20-alpine AS base
RUN apk add --no-cache dumb-init
WORKDIR /app

# Dipendenze
FROM base AS deps
COPY package.json package-lock.json ./
COPY apps/backend/package.json apps/backend/
COPY packages/shared/package.json packages/shared/
RUN npm ci --production=false

# Build
FROM deps AS build
COPY apps/backend/ apps/backend/
COPY packages/shared/ packages/shared/
COPY tsconfig.json turbo.json ./
RUN npx turbo build --filter=backend

# Dipendenze produzione
FROM base AS prod-deps
COPY package.json package-lock.json ./
COPY apps/backend/package.json apps/backend/
COPY packages/shared/package.json packages/shared/
RUN npm ci --production

# Runtime
FROM base AS runtime
ARG BUILD_SHA=unknown
ENV NODE_ENV=production
ENV BUILD_SHA=$BUILD_SHA

COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=prod-deps /app/apps/backend/node_modules ./apps/backend/node_modules
COPY --from=build /app/apps/backend/dist ./apps/backend/dist
COPY --from=build /app/packages/shared/dist ./packages/shared/dist
COPY apps/backend/prisma ./apps/backend/prisma

RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001
USER nodejs

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["dumb-init", "node", "apps/backend/dist/main.js"]
```

```dockerfile
# apps/frontend/Dockerfile
FROM node:20-alpine AS base
WORKDIR /app

# Dipendenze
FROM base AS deps
COPY package.json package-lock.json ./
COPY apps/frontend/package.json apps/frontend/
COPY packages/shared/package.json packages/shared/
RUN npm ci

# Build
FROM deps AS build
ARG BUILD_SHA=unknown
ARG API_URL=https://api.example.com
ENV VITE_BUILD_SHA=$BUILD_SHA
ENV VITE_API_URL=$API_URL

COPY apps/frontend/ apps/frontend/
COPY packages/shared/ packages/shared/
COPY tsconfig.json turbo.json ./
RUN npx turbo build --filter=frontend

# Runtime con Nginx
FROM nginx:1.25-alpine AS runtime

COPY --from=build /app/apps/frontend/dist /usr/share/nginx/html
COPY apps/frontend/nginx.conf /etc/nginx/conf.d/default.conf

RUN addgroup -g 1001 -S nginx-app && \
    adduser -S nginx-app -u 1001 -G nginx-app && \
    chown -R nginx-app:nginx-app /var/cache/nginx /var/log/nginx /etc/nginx/conf.d

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# apps/frontend/nginx.conf
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api.example.com;" always;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        return 200 'ok';
        add_header Content-Type text/plain;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## Pipeline CD

### Deploy in Staging (Automatico)

```yaml
# .github/workflows/cd-staging.yml
name: Deploy Staging

on:
  push:
    branches: [main]

concurrency:
  group: deploy-staging
  cancel-in-progress: false

env:
  REGISTRY: ghcr.io
  KUBE_NAMESPACE: staging

jobs:
  deploy:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    permissions:
      contents: read
      packages: read
    steps:
      - uses: actions/checkout@v4

      - name: Configurare kubectl
        uses: azure/k8s-set-context@v4
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}

      - name: Aggiornare immagini deployment
        run: |
          IMAGE_TAG="${{ github.sha }}"

          # Backend
          kubectl set image deployment/backend \
            backend=${{ env.REGISTRY }}/${{ github.repository }}/backend:${IMAGE_TAG} \
            -n ${{ env.KUBE_NAMESPACE }}

          # Frontend
          kubectl set image deployment/frontend \
            frontend=${{ env.REGISTRY }}/${{ github.repository }}/frontend:${IMAGE_TAG} \
            -n ${{ env.KUBE_NAMESPACE }}

      - name: Attendere rollout
        run: |
          kubectl rollout status deployment/backend -n ${{ env.KUBE_NAMESPACE }} --timeout=300s
          kubectl rollout status deployment/frontend -n ${{ env.KUBE_NAMESPACE }} --timeout=300s

      - name: Smoke test
        run: |
          # Attendere che l'ingress sia pronto
          sleep 30

          # Verificare l'health endpoint
          for i in {1..10}; do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://staging.example.com/api/health)
            if [ "$STATUS" = "200" ]; then
              echo "Health check OK (attempt $i)"
              break
            fi
            echo "Health check fallito ($STATUS), retry in 10s (attempt $i)..."
            sleep 10
          done

          if [ "$STATUS" != "200" ]; then
            echo "ERRORE: Health check fallito dopo 10 tentativi!"
            kubectl logs deployment/backend -n ${{ env.KUBE_NAMESPACE }} --tail=50
            exit 1
          fi

          # Test API endpoint
          curl -sf https://staging.example.com/api/v1/status | jq .

      - name: Rollback se fallisce
        if: failure()
        run: |
          echo "Deploy fallito, eseguendo rollback..."
          kubectl rollout undo deployment/backend -n ${{ env.KUBE_NAMESPACE }}
          kubectl rollout undo deployment/frontend -n ${{ env.KUBE_NAMESPACE }}
          kubectl rollout status deployment/backend -n ${{ env.KUBE_NAMESPACE }} --timeout=120s
          kubectl rollout status deployment/frontend -n ${{ env.KUBE_NAMESPACE }} --timeout=120s
          echo "Rollback completato"

      - name: Notifica deploy
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "${{ job.status == 'success' && 'Deploy staging completato' || 'Deploy staging FALLITO' }}: ${{ github.event.head_commit.message }}\nCommit: ${{ github.sha }}\nAutore: ${{ github.actor }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Deploy in Produzione (Manuale con Approvazione)

```yaml
# .github/workflows/cd-production.yml
name: Deploy Production

on:
  push:
    tags: ['v*.*.*']
  workflow_dispatch:
    inputs:
      tag:
        description: 'Tag versione da deployare (es. v1.2.3)'
        required: true
        type: string

concurrency:
  group: deploy-production
  cancel-in-progress: false

env:
  REGISTRY: ghcr.io
  KUBE_NAMESPACE: production

jobs:
  validate:
    name: Validate Release
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.tag }}
    steps:
      - name: Determinare la versione
        id: version
        run: |
          if [ "${{ github.event_name }}" = "push" ]; then
            echo "tag=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT
          else
            echo "tag=${{ inputs.tag }}" >> $GITHUB_OUTPUT
          fi

      - name: Verificare che le immagini Docker esistano
        run: |
          TAG="${{ steps.version.outputs.tag }}"
          for app in frontend backend; do
            IMAGE="${{ env.REGISTRY }}/${{ github.repository }}/${app}:${TAG}"
            docker manifest inspect "$IMAGE" > /dev/null 2>&1 || {
              echo "ERRORE: Immagine non trovata: $IMAGE"
              exit 1
            }
            echo "Immagine verificata: $IMAGE"
          done

  deploy:
    name: Deploy to Production
    needs: validate
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ needs.validate.outputs.version }}

      - name: Configurare kubectl
        uses: azure/k8s-set-context@v4
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_PRODUCTION }}

      - name: Creare snapshot pre-deploy
        run: |
          echo "=== Stato pre-deploy ==="
          kubectl get deployments -n ${{ env.KUBE_NAMESPACE }} -o wide
          echo ""
          kubectl get pods -n ${{ env.KUBE_NAMESPACE }}

      - name: Deploy con strategia rolling update
        run: |
          VERSION="${{ needs.validate.outputs.version }}"

          kubectl set image deployment/backend \
            backend=${{ env.REGISTRY }}/${{ github.repository }}/backend:${VERSION} \
            -n ${{ env.KUBE_NAMESPACE }}

          kubectl set image deployment/frontend \
            frontend=${{ env.REGISTRY }}/${{ github.repository }}/frontend:${VERSION} \
            -n ${{ env.KUBE_NAMESPACE }}

      - name: Attendere rollout
        run: |
          kubectl rollout status deployment/backend -n ${{ env.KUBE_NAMESPACE }} --timeout=600s
          kubectl rollout status deployment/frontend -n ${{ env.KUBE_NAMESPACE }} --timeout=600s

      - name: Health check produzione
        run: |
          for i in {1..15}; do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://example.com/api/health)
            if [ "$STATUS" = "200" ]; then
              echo "Health check produzione OK"
              exit 0
            fi
            echo "Tentativo $i/15 fallito ($STATUS), attendo 20s..."
            sleep 20
          done
          echo "CRITICO: Health check produzione fallito!"
          exit 1

      - name: Rollback automatico se fallisce
        if: failure()
        run: |
          echo "CRITICO: Deploy produzione fallito, rollback in corso..."
          kubectl rollout undo deployment/backend -n ${{ env.KUBE_NAMESPACE }}
          kubectl rollout undo deployment/frontend -n ${{ env.KUBE_NAMESPACE }}
          kubectl rollout status deployment/backend -n ${{ env.KUBE_NAMESPACE }} --timeout=120s
          kubectl rollout status deployment/frontend -n ${{ env.KUBE_NAMESPACE }} --timeout=120s

      - name: Aggiornare il tag su GitHub
        if: success()
        run: |
          echo "Deploy produzione completato: ${{ needs.validate.outputs.version }}"
```

---

## Infrastructure as Code

### Terraform per l'Infrastruttura

```hcl
# infrastructure/terraform/environments/staging/main.tf

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
  }

  backend "s3" {
    bucket         = "my-project-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
    }
  }
}

# VPC
module "vpc" {
  source = "../modules/networking"

  environment     = var.environment
  vpc_cidr        = "10.0.0.0/16"
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  azs             = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
}

# EKS Cluster
module "kubernetes" {
  source = "../modules/kubernetes"

  environment      = var.environment
  cluster_name     = "${var.project_name}-${var.environment}"
  cluster_version  = "1.29"
  vpc_id           = module.vpc.vpc_id
  subnet_ids       = module.vpc.private_subnet_ids
  node_instance_type = "t3.medium"
  node_min_size    = 2
  node_max_size    = 6
  node_desired_size = 3
}

# RDS PostgreSQL
module "database" {
  source = "../modules/database"

  environment       = var.environment
  engine_version    = "16.1"
  instance_class    = "db.t3.medium"
  allocated_storage = 50
  database_name     = "appdb"
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.private_subnet_ids
  allowed_security_groups = [module.kubernetes.node_security_group_id]
}

# Monitoring
module "monitoring" {
  source = "../modules/monitoring"

  environment  = var.environment
  cluster_name = module.kubernetes.cluster_name
  alert_email  = var.alert_email
}
```

### Terraform in GitHub Actions

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  push:
    branches: [main]
    paths: ['infrastructure/terraform/**']
  pull_request:
    paths: ['infrastructure/terraform/**']

env:
  TF_VERSION: '1.7.0'
  AWS_REGION: 'eu-west-1'

jobs:
  plan:
    name: Terraform Plan
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [staging, production]
    defaults:
      run:
        working-directory: infrastructure/terraform/environments/${{ matrix.environment }}
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Configurare AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets[format('AWS_ROLE_{0}', matrix.environment)] }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Terraform Init
        run: terraform init

      - name: Terraform Validate
        run: terraform validate

      - name: Terraform Plan
        id: plan
        run: terraform plan -no-color -out=tfplan
        continue-on-error: true

      - name: Commentare PR con il plan
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const output = `#### Terraform Plan - ${{ matrix.environment }}
            \`\`\`
            ${{ steps.plan.outputs.stdout }}
            \`\`\`
            *Pushed by: @${{ github.actor }}*`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            });

  apply:
    name: Terraform Apply (Staging)
    needs: plan
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: staging-infra
    defaults:
      run:
        working-directory: infrastructure/terraform/environments/staging
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_STAGING }}
          aws-region: ${{ env.AWS_REGION }}

      - run: terraform init
      - run: terraform apply -auto-approve
```

---

## Deployment su Kubernetes

### Manifesti Kubernetes (Kustomize)

```yaml
# infrastructure/kubernetes/base/backend-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  labels:
    app: backend
    tier: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
        tier: api
    spec:
      containers:
        - name: backend
          image: ghcr.io/org/project/backend:latest
          ports:
            - containerPort: 3000
              protocol: TCP
          env:
            - name: NODE_ENV
              value: production
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: database-url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: redis-url
            - name: JWT_SECRET
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: jwt-secret
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: 1000m
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 15
            periodSeconds: 20
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 10
          startupProbe:
            httpGet:
              path: /health
              port: 3000
            failureThreshold: 30
            periodSeconds: 5
      imagePullSecrets:
        - name: ghcr-pull-secret
```

```yaml
# infrastructure/kubernetes/base/backend-service.yml
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  selector:
    app: backend
  ports:
    - port: 80
      targetPort: 3000
      protocol: TCP
  type: ClusterIP
```

```yaml
# infrastructure/kubernetes/base/ingress.yml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - example.com
        - api.example.com
      secretName: app-tls
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 80
    - host: example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
```

```yaml
# infrastructure/kubernetes/base/kustomization.yml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - namespace.yml
  - backend-deployment.yml
  - backend-service.yml
  - frontend-deployment.yml
  - frontend-service.yml
  - ingress.yml

commonLabels:
  project: my-project
```

```yaml
# infrastructure/kubernetes/overlays/staging/kustomization.yml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: staging

resources:
  - ../../base

patches:
  - patch: |-
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: backend
      spec:
        replicas: 1
        template:
          spec:
            containers:
              - name: backend
                resources:
                  requests:
                    cpu: 100m
                    memory: 128Mi
                  limits:
                    cpu: 500m
                    memory: 256Mi
  - patch: |-
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: frontend
      spec:
        replicas: 1
```

---

## Security Scanning

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 6 * * 1'  # Ogni lunedì alle 6:00

permissions:
  security-events: write
  contents: read

jobs:
  codeql:
    name: CodeQL Analysis
    runs-on: ubuntu-latest
    strategy:
      matrix:
        language: [javascript-typescript]
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
      - uses: github/codeql-action/analyze@v3

  dependency-audit:
    name: Dependency Audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Audit delle dipendenze
        run: |
          npm audit --audit-level=high
          echo ""
          echo "=== Licenze ==="
          npx license-checker --summary

  container-scan:
    name: Container Vulnerability Scan
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    strategy:
      matrix:
        app: [frontend, backend]
    steps:
      - uses: actions/checkout@v4

      - uses: docker/build-push-action@v5
        with:
          context: .
          file: apps/${{ matrix.app }}/Dockerfile
          push: false
          tags: scan-target:latest
          load: true

      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: scan-target:latest
          format: 'sarif'
          output: 'trivy-${{ matrix.app }}.sarif'
          severity: 'CRITICAL,HIGH'

      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-${{ matrix.app }}.sarif'

  secret-scan:
    name: Secret Detection
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified
```

---

## Gestione delle Dipendenze

```yaml
# .github/dependabot.yml
version: 2
updates:
  # npm (root + workspaces)
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "06:00"
      timezone: "Europe/Rome"
    open-pull-requests-limit: 10
    reviewers:
      - "team-leads"
    labels:
      - "dependencies"
      - "automated"
    groups:
      minor-and-patch:
        update-types:
          - "minor"
          - "patch"
      major:
        update-types:
          - "major"
    ignore:
      - dependency-name: "typescript"
        update-types: ["version-update:semver-major"]

  # Docker
  - package-ecosystem: "docker"
    directory: "/apps/backend"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "docker"

  - package-ecosystem: "docker"
    directory: "/apps/frontend"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "docker"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "ci"

  # Terraform
  - package-ecosystem: "terraform"
    directory: "/infrastructure/terraform/environments/staging"
    schedule:
      interval: "monthly"
    labels:
      - "dependencies"
      - "infrastructure"
```

---

## Release Automation

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ['v*.*.*']

permissions:
  contents: write
  packages: write

jobs:
  release:
    name: Create Release
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Generare changelog
        id: changelog
        run: |
          npm install conventional-changelog-cli
          npx conventional-changelog -p angular -r 2 -o RELEASE_NOTES.md

          # Aggiungere info Docker images
          VERSION="${GITHUB_REF#refs/tags/}"
          cat >> RELEASE_NOTES.md << EOF

          ## Docker Images

          \`\`\`bash
          docker pull ghcr.io/${{ github.repository }}/backend:${VERSION}
          docker pull ghcr.io/${{ github.repository }}/frontend:${VERSION}
          \`\`\`

          ## Deploy

          Questa versione è stata deployata automaticamente in staging.
          Per il deploy in produzione, approvare il workflow "Deploy Production".
          EOF

      - name: Creare GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          body_path: RELEASE_NOTES.md
          generate_release_notes: false
          draft: false
          prerelease: ${{ contains(github.ref, '-alpha') || contains(github.ref, '-beta') || contains(github.ref, '-rc') }}
```

---

## Documentazione con GitHub Pages

```yaml
# .github/workflows/docs.yml
name: Documentation

on:
  push:
    branches: [main]
    paths: ['docs/**']
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Installare MkDocs
        run: pip install mkdocs-material mkdocs-mermaid2-plugin

      - name: Build documentazione
        run: mkdocs build

      - uses: actions/upload-pages-artifact@v3
        with:
          path: site/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

```yaml
# mkdocs.yml
site_name: My Project Documentation
site_url: https://org.github.io/project
repo_url: https://github.com/org/project

theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Light mode

nav:
  - Home: index.md
  - Architecture: architecture.md
  - API Reference: api-reference.md
  - Runbook: runbook.md

plugins:
  - search
  - mermaid2

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - admonition
  - pymdownx.details
  - pymdownx.tabbed:
      alternate_style: true
```

---

## Incident Response con GitHub Issues

### Template Incident Report

```yaml
# .github/ISSUE_TEMPLATE/incident_report.yml
name: Incident Report
description: Segnala un incidente di produzione
title: "[INCIDENT] "
labels: ["incident", "P0"]

body:
  - type: dropdown
    id: severity
    attributes:
      label: Severità
      options:
        - P0 - Critico (servizio down, perdita dati)
        - P1 - Alto (degradazione significativa)
        - P2 - Medio (degradazione minore)
        - P3 - Basso (impatto minimo)
    validations:
      required: true

  - type: textarea
    id: impact
    attributes:
      label: Impatto
      description: Chi è impattato? Quanti utenti? Quali funzionalità?
    validations:
      required: true

  - type: textarea
    id: timeline
    attributes:
      label: Timeline
      value: |
        - **Rilevato**: [data/ora]
        - **Confermato**: [data/ora]
        - **Mitigazione iniziata**: [data/ora]
        - **Mitigato**: [data/ora]
        - **Risolto**: [data/ora]
    validations:
      required: true

  - type: textarea
    id: root_cause
    attributes:
      label: Root Cause (da compilare dopo la risoluzione)

  - type: textarea
    id: action_items
    attributes:
      label: Action Items
      value: |
        - [ ] Action item 1
        - [ ] Action item 2
```

---

## Progetto Completo: Riepilogo di Tutti i File

Ecco il riepilogo di tutti i workflow e la loro interazione:

```
Trigger                  Workflow              Ambiente        Azione
─────────────────────────────────────────────────────────────────────
PR aperta/aggiornata  → ci.yml              → -             → Lint, Test, Build
Push su main          → ci.yml              → -             → Lint, Test, Build
                      → cd-staging.yml      → staging       → Deploy automatico
                      → security-scan.yml   → -             → Scansione sicurezza
                      → docs.yml            → github-pages  → Deploy documentazione
Push tag v*.*.*       → release.yml         → -             → Crea GitHub Release
                      → cd-production.yml   → production    → Deploy (con approvazione)
Cron settimanale      → security-scan.yml   → -             → Scansione sicurezza
Dependabot            → ci.yml              → -             → Test dipendenze aggiornate
Terraform change      → terraform.yml       → staging-infra → Plan & Apply
```

```
┌─────────────┐     ┌──────────┐     ┌───────────┐     ┌────────────┐
│  Developer   │────►│  GitHub   │────►│  CI/CD    │────►│  Staging   │
│  push/PR     │     │  Actions  │     │  Pipeline │     │  (auto)    │
└─────────────┘     └──────────┘     └───────────┘     └─────┬──────┘
                                                              │
                                           tag v*.*.*         │ approvazione
                                              │               │
                                    ┌─────────▼───────────────▼──────────┐
                                    │        Production Deploy            │
                                    │  (richiede approvazione manuale)    │
                                    └────────────────────────────────────┘
```

---

## GitOps: Modello Dichiarativo e Riconciliazione Continua

### Che cos'è GitOps

GitOps è un framework operativo che applica le best practice dello sviluppo software — controllo di versione, collaborazione, compliance e CI/CD — all'automazione dell'infrastruttura. Il repository Git diventa la **single source of truth** per lo stato dichiarativo dell'infrastruttura e delle applicazioni. Ogni modifica avviene tramite pull request, e agenti automatizzati garantiscono che l'ambiente live corrisponda allo stato desiderato archiviato in Git.

A differenza del modello push tradizionale di CI/CD (dove la pipeline esegue comandi verso il cluster), GitOps adotta un modello **pull-based**: un agente residente nel cluster confronta continuamente lo stato attuale con lo stato dichiarato in Git e corregge automaticamente qualsiasi deviazione. Questo meccanismo si chiama **riconciliazione continua**.

### GitOps vs CI/CD Tradizionale

```
┌──────────────────────────────────────────────────────────────────────┐
│                   MODELLO PUSH (CI/CD Tradizionale)                   │
│                                                                      │
│  Developer → Git Push → CI Pipeline → kubectl apply → Cluster K8s   │
│                                                                      │
│  Problemi:                                                           │
│  • Pipeline ha credenziali cluster (superficie d'attacco ampia)      │
│  • Nessuna rilevazione drift (modifiche manuali non tracciate)       │
│  • Stato desiderato non verificato continuamente                     │
│  • Rollback manuale                                                  │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                   MODELLO PULL (GitOps)                               │
│                                                                      │
│  Developer → Git Push → Repository ← Agent nel Cluster → Cluster    │
│                                          ↕                           │
│                                   Riconciliazione                    │
│                                    continua                          │
│                                                                      │
│  Vantaggi:                                                           │
│  • Credenziali cluster isolate nel cluster stesso                    │
│  • Drift detection automatica                                        │
│  • Self-healing: stato corretto automaticamente                      │
│  • Audit trail completo via Git history                               │
│  • Rollback = git revert                                             │
└──────────────────────────────────────────────────────────────────────┘
```

### Argo CD: GitOps per Kubernetes

Argo CD è il tool GitOps più diffuso, graduato dalla CNCF, progettato specificamente per Kubernetes. Rileva il drift attraverso riconciliazione continua, confrontando i manifesti renderizzati da Git con lo stato live del cluster tramite un algoritmo di diff semantico.

```yaml
# argocd-application.yml — Esempio di Application Argo CD
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-project-staging
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/project.git
    targetRevision: main
    path: infrastructure/kubernetes/overlays/staging
  destination:
    server: https://kubernetes.default.svc
    namespace: staging
  syncPolicy:
    automated:
      prune: true           # Rimuovi risorse non presenti in Git
      selfHeal: true         # Correggi drift automaticamente
      allowEmpty: false      # Non svuotare il namespace
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas   # HPA gestisce le repliche, ignora drift
```

### Flux CD: Alternativa GitOps

Flux CD, anch'esso graduato dalla CNCF, adotta un approccio più modulare con componenti separati (source-controller, kustomize-controller, helm-controller, notification-controller). Con Flux 2.0 (2026), il supporto multi-cluster è migliorato significativamente.

```yaml
# flux-gitrepository.yml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: my-project
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/org/project.git
  ref:
    branch: main
  secretRef:
    name: github-deploy-key
---
# flux-kustomization.yml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: staging
  namespace: flux-system
spec:
  interval: 5m
  path: ./infrastructure/kubernetes/overlays/staging
  prune: true
  sourceRef:
    kind: GitRepository
    name: my-project
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: backend
      namespace: staging
    - apiVersion: apps/v1
      kind: Deployment
      name: frontend
      namespace: staging
  timeout: 3m
```

### Confronto Argo CD vs Flux CD

| Caratteristica | Argo CD | Flux CD |
|----------------|---------|---------|
| **Interfaccia UI** | Dashboard web completa e ricca | Nessuna UI nativa (usa Weave GitOps) |
| **Architettura** | Monolitica, tutto-in-uno | Modulare, componenti separati |
| **Multi-tenancy** | AppProject con RBAC granulare | Kustomization con namespace isolation |
| **Helm support** | Nativo, con template rendering | Via HelmRelease controller |
| **Notifiche** | Plugin notification | notification-controller integrato |
| **SSO/RBAC** | Integrato (OIDC, LDAP, SAML) | Delegato a Kubernetes RBAC |
| **Drift detection** | Diff semantico avanzato | Comparazione hash-based |
| **Adozione (2026)** | ~72% mercato GitOps | ~23% mercato GitOps |
| **CNCF status** | Graduated | Graduated |

### GitHub Actions + GitOps: Integrazione Ibrida

GitHub Actions usa nativamente un modello push, ma può essere integrato con GitOps per ottenere il meglio di entrambi i mondi. Il pattern consigliato prevede che GitHub Actions gestisca CI (build, test, scan, push immagine) e aggiorni i manifesti nel repository Git, mentre Argo CD o Flux rilevano la modifica e sincronizzano il cluster.

```yaml
# .github/workflows/update-manifests.yml
name: Update Kubernetes Manifests

on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [main]

jobs:
  update-manifests:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.MANIFEST_UPDATE_TOKEN }}

      - name: Aggiornare tag immagine nei manifesti
        run: |
          IMAGE_TAG="${{ github.event.workflow_run.head_sha }}"
          cd infrastructure/kubernetes/base

          # Aggiorna il tag immagine nel kustomization
          kustomize edit set image \
            ghcr.io/org/project/backend=ghcr.io/org/project/backend:${IMAGE_TAG} \
            ghcr.io/org/project/frontend=ghcr.io/org/project/frontend:${IMAGE_TAG}

      - name: Commit e push dei manifesti aggiornati
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add infrastructure/kubernetes/
          git diff --cached --quiet || \
            git commit -m "chore: update image tags to ${{ github.event.workflow_run.head_sha }}"
          git push

      # Argo CD rileverà automaticamente la modifica e sincronizzerà
```

### Drift Detection e Remediation

La drift detection è il processo con cui lo strumento GitOps identifica discrepanze tra lo stato dichiarato in Git e lo stato effettivo del cluster. Le cause comuni di drift includono:

- **Modifiche manuali via kubectl**: un operatore che modifica direttamente una risorsa
- **Mutating webhooks**: admission controller che modificano le risorse
- **HPA (Horizontal Pod Autoscaler)**: modifica il numero di repliche
- **Controller mutations**: controller Kubernetes che aggiungono campi
- **Operazioni di emergenza**: hotfix manuali durante un incidente

```yaml
# Workflow per rilevare drift e notificare
# .github/workflows/drift-detection.yml
name: Infrastructure Drift Detection

on:
  schedule:
    - cron: '0 */6 * * *'  # Ogni 6 ore

jobs:
  detect-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup ArgoCD CLI
        run: |
          curl -sSL -o argocd \
            https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
          chmod +x argocd
          sudo mv argocd /usr/local/bin/

      - name: Check drift per tutte le applicazioni
        env:
          ARGOCD_SERVER: ${{ secrets.ARGOCD_SERVER }}
          ARGOCD_AUTH_TOKEN: ${{ secrets.ARGOCD_AUTH_TOKEN }}
        run: |
          DRIFTED_APPS=""
          for app in $(argocd app list -o name); do
            STATUS=$(argocd app get "$app" -o json | jq -r '.status.sync.status')
            if [ "$STATUS" != "Synced" ]; then
              DRIFTED_APPS="${DRIFTED_APPS}\n- ${app}: ${STATUS}"
            fi
          done

          if [ -n "$DRIFTED_APPS" ]; then
            echo "DRIFT RILEVATO:"
            echo -e "$DRIFTED_APPS"
            echo "drift_detected=true" >> $GITHUB_OUTPUT
            echo "drifted_apps=$DRIFTED_APPS" >> $GITHUB_OUTPUT
          else
            echo "Nessun drift rilevato"
          fi

      - name: Creare issue per drift
        if: steps.detect-drift.outputs.drift_detected == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '[DRIFT] Configurazione fuori sincronizzazione',
              body: `## Drift Rilevato\n\nLe seguenti applicazioni sono fuori sincronizzazione:\n${{ steps.detect-drift.outputs.drifted_apps }}\n\nVerificare e risolvere manualmente o eseguire sync forzato.`,
              labels: ['infrastructure', 'drift', 'automated']
            });
```

---

## Platform Engineering e Internal Developer Platform

### Il Paradigma Platform Engineering

Platform Engineering è la disciplina di costruire e mantenere una **Internal Developer Platform (IDP)** — un layer self-service che astrae la complessità infrastrutturale e fornisce ai developer strumenti standardizzati per deployare e operare il proprio codice. Secondo Gartner (2026), l'80% delle organizzazioni di software engineering mantiene team di piattaforma dedicati, in crescita dal 55% nel 2025.

Il principio fondamentale è semplice: i developer non dovrebbero aver bisogno di diventare esperti Kubernetes, Terraform o cloud networking per deployare le proprie applicazioni. La piattaforma offre **golden path** (percorsi ottimali preconfigurati) che codificano le best practice dell'organizzazione.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    INTERNAL DEVELOPER PLATFORM                       │
│                                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │  Developer  │  │  Developer  │  │  Developer  │  │  Developer  │    │
│  │  Team A     │  │  Team B     │  │  Team C     │  │  Team D     │    │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘    │
│         │               │               │               │            │
│  ┌──────▼───────────────▼───────────────▼───────────────▼──────┐    │
│  │              PORTALE SVILUPPATORI (Backstage)                │    │
│  │  • Catalogo servizi    • Template scaffolding                │    │
│  │  • Documentazione      • Tech Radar                          │    │
│  │  • Stato CI/CD         • Costi infrastruttura                │    │
│  │  • Ownership graph     • Scorecard qualità                   │    │
│  └──────────────────────────┬───────────────────────────────────┘    │
│                              │                                       │
│  ┌──────────────────────────▼───────────────────────────────────┐    │
│  │              PIATTAFORMA SELF-SERVICE                         │    │
│  │  • GitHub Actions (CI/CD)    • Terraform (IaC)               │    │
│  │  • ArgoCD (GitOps)           • Vault (Secrets)               │    │
│  │  • Prometheus/Grafana        • PagerDuty (On-call)           │    │
│  │  • Cost dashboards           • Compliance gates              │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │              INFRASTRUTTURA (AWS / GCP / Azure)               │    │
│  │  • Kubernetes    • Database    • Networking    • Storage      │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

### Backstage: Il Portale Sviluppatori Open Source

Backstage, creato da Spotify e ora progetto CNCF, è il framework dominante per costruire portali sviluppatori interni, con circa l'89% di quota di mercato nel segmento developer portal (2026). Conta oltre 36.000 GitHub star e contributi da più di 45.000 sviluppatori in 13.500 organizzazioni. Il suo ecosistema comprende oltre 230 plugin open source che integrano CI/CD, monitoring, cloud provider, security scanning, cost management e documentazione API.

I componenti principali di Backstage sono:

- **Software Catalog**: inventario centralizzato di tutti i servizi, librerie, siti web e pipeline con ownership, dipendenze e metadati
- **Software Templates**: scaffolding per creare nuovi servizi con best practice preconfigurate (golden path)
- **TechDocs**: documentazione tecnica integrata nel portale, generata da Markdown nei repository
- **Plugins**: estensioni per integrare qualsiasi tool (GitHub Actions, Grafana, PagerDuty, Snyk, ecc.)
- **Search**: ricerca unificata attraverso catalogo, documentazione e plugin

```yaml
# catalog-info.yaml — File di registrazione servizio in Backstage
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: backend-api
  description: API backend principale del progetto
  annotations:
    github.com/project-slug: org/project
    backstage.io/techdocs-ref: dir:.
    grafana/dashboard-selector: app=backend
    pagerduty.com/service-id: P1234ABC
    sonarqube.org/project-key: org_project_backend
  tags:
    - nodejs
    - typescript
    - rest-api
  links:
    - url: https://staging.example.com/api/docs
      title: API Documentation
      icon: docs
    - url: https://grafana.example.com/d/backend
      title: Grafana Dashboard
      icon: dashboard
spec:
  type: service
  lifecycle: production
  owner: team-backend
  system: my-project
  dependsOn:
    - resource:default/postgres-db
    - resource:default/redis-cache
  providesApis:
    - backend-rest-api
  consumesApis:
    - payment-gateway-api
```

```yaml
# Backstage Software Template per nuovo microservizio
# template.yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: nodejs-microservice
  title: Node.js Microservice
  description: Crea un nuovo microservizio Node.js con CI/CD preconfigurato
  tags:
    - nodejs
    - typescript
    - recommended
spec:
  owner: platform-team
  type: service
  parameters:
    - title: Informazioni servizio
      required: [name, owner]
      properties:
        name:
          title: Nome del servizio
          type: string
          pattern: '^[a-z0-9-]+$'
        description:
          title: Descrizione
          type: string
        owner:
          title: Team proprietario
          type: string
          ui:field: OwnerPicker
    - title: Configurazione infrastruttura
      properties:
        database:
          title: Database
          type: string
          enum: [none, postgresql, mongodb]
          default: none
        hasRedis:
          title: Richiede Redis
          type: boolean
          default: false
  steps:
    - id: fetch-template
      name: Generare codice dal template
      action: fetch:template
      input:
        url: ./skeleton
        values:
          name: ${{ parameters.name }}
          owner: ${{ parameters.owner }}
          description: ${{ parameters.description }}
          database: ${{ parameters.database }}
          hasRedis: ${{ parameters.hasRedis }}

    - id: publish
      name: Creare repository GitHub
      action: publish:github
      input:
        allowedHosts: ['github.com']
        repoUrl: github.com?owner=org&repo=${{ parameters.name }}
        description: ${{ parameters.description }}
        defaultBranch: main
        protectDefaultBranch: true
        requireCodeOwnerReviews: true

    - id: register
      name: Registrare nel catalogo Backstage
      action: catalog:register
      input:
        repoContentsUrl: ${{ steps.publish.output.repoContentsUrl }}
        catalogInfoPath: /catalog-info.yaml

  output:
    links:
      - title: Repository
        url: ${{ steps.publish.output.remoteUrl }}
      - title: Catalogo
        entityRef: ${{ steps.register.output.entityRef }}
```

### Scorecard di Qualità dei Servizi

Le scorecard consentono al team di piattaforma di definire standard misurabili per tutti i servizi. Ogni criterio viene valutato automaticamente e mostrato nel portale.

| Criterio | Peso | Come si misura |
|----------|------|----------------|
| Ha CI pipeline funzionante | 15% | GitHub Actions status check |
| Coverage test ≥ 80% | 15% | Coverage report artifacts |
| Documentazione aggiornata | 10% | TechDocs presenti e < 90 giorni |
| Ha owner definito | 10% | Campo `spec.owner` in catalog-info.yaml |
| Zero vulnerabilità critiche | 15% | Dependabot + Trivy results |
| Monitoring configurato | 10% | Grafana dashboard annotazione |
| On-call configurato | 10% | PagerDuty annotazione |
| Runbook aggiornato | 10% | File runbook.md presente |
| SBOM generato | 5% | Attestazione presente nella release |

---

## DORA Metrics e Misurazione delle Performance DevOps

### Le Quattro Metriche DORA Fondamentali

Le metriche DORA (DevOps Research and Assessment), create dal team di ricerca di Google, sono lo standard de facto per misurare l'efficacia delle pratiche DevOps. Identificano ciò che distingue i team ad alte prestazioni e forniscono benchmark misurabili.

| Metrica | Definizione | Elite (2026) | High | Medium | Low |
|---------|------------|--------------|------|--------|-----|
| **Deployment Frequency** | Frequenza dei deploy in produzione | Più volte al giorno | Da giornaliero a settimanale | Da settimanale a mensile | Meno di una volta al mese |
| **Lead Time for Changes** | Tempo dal commit al deploy in produzione | < 1 ora | Da 1 giorno a 1 settimana | Da 1 settimana a 1 mese | > 1 mese |
| **Change Failure Rate** | Percentuale di deploy che causano incidenti | < 5% | 5–10% | 10–15% | > 15% |
| **Time to Restore** | Tempo per ripristinare il servizio dopo un incidente | < 1 ora | < 1 giorno | Da 1 giorno a 1 settimana | > 1 settimana |

### La Quinta Metrica: Rework Rate

Nel 2025 il team DORA ha aggiunto una quinta metrica ufficiale: il **Rework Rate**, che misura quanta attività ingegneristica è reattiva (fix di bug, rollback, hotfix) rispetto a lavoro pianificato (nuove feature, miglioramenti). Un rework rate elevato indica instabilità nella pipeline e problemi di qualità a monte.

```
Formula: Rework Rate = (Commit che modificano codice con meno di 21 giorni) / (Commit totali) × 100

Benchmark:
• Elite:  < 5%   — Quasi tutto il lavoro è pianificato
• High:   5–10%  — Rework gestibile
• Medium: 10–20% — Segnale di problemi di qualità
• Low:    > 20%  — Il team è in modalità reattiva costante
```

### Misurare DORA con GitHub Actions

```yaml
# .github/workflows/dora-metrics.yml
name: DORA Metrics Collection

on:
  schedule:
    - cron: '0 0 * * 0'  # Ogni domenica a mezzanotte
  workflow_dispatch:

jobs:
  collect-metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Calcolare Deployment Frequency
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          echo "=== Deployment Frequency (ultimi 30 giorni) ==="
          DEPLOYS=$(gh api repos/${{ github.repository }}/deployments \
            --paginate \
            --jq "[.[] | select(.created_at > \"$(date -d '30 days ago' -Iseconds)\") ] | length")
          echo "Deploy totali: $DEPLOYS"
          echo "Media giornaliera: $(echo "scale=2; $DEPLOYS / 30" | bc)"

      - name: Calcolare Lead Time for Changes
        run: |
          echo "=== Lead Time for Changes ==="
          # Tempo medio tra primo commit nella PR e merge
          gh api repos/${{ github.repository }}/pulls \
            --paginate \
            -q '.[] | select(.merged_at != null) |
              {pr: .number, created: .created_at, merged: .merged_at}' \
            | head -50 | jq -s '
              [.[] |
                ((.merged | fromdateiso8601) - (.created | fromdateiso8601)) / 3600
              ] | (add / length) | round' \
            || echo "Calcolo in corso..."
          echo "(in ore, media sulle ultime 50 PR)"

      - name: Calcolare Change Failure Rate
        run: |
          echo "=== Change Failure Rate ==="
          TOTAL=$(gh api repos/${{ github.repository }}/deployments \
            --paginate --jq 'length')
          FAILURES=$(gh api repos/${{ github.repository }}/deployments \
            --paginate \
            --jq '[.[] | select(.statuses_url != null)] |
              [.[] | select(.payload.environment == "production")] |
              length')
          echo "Deploy totali: $TOTAL"
          echo "Nota: calcolo completo richiede integrazione con incident tracking"

      - name: Pubblicare risultati
        run: |
          cat >> $GITHUB_STEP_SUMMARY << 'EOF'
          ## DORA Metrics Report

          | Metrica | Valore | Target Elite |
          |---------|--------|-------------|
          | Deployment Frequency | $DEPLOYS/mese | Multiplo/giorno |
          | Lead Time | In calcolo | < 1 ora |
          | Change Failure Rate | In calcolo | < 5% |
          | MTTR | In calcolo | < 1 ora |
          EOF
```

### Oltre DORA: Il Framework SPACE

Nel 2026 misurare solo le metriche DORA non è più sufficiente. Il framework **SPACE** (Satisfaction, Performance, Activity, Communication, Efficiency) e il **DX Core 4** (Speed, Effectiveness, Quality, Business Impact) offrono una visione più completa della produttività ingegneristica, specialmente nell'era degli strumenti AI che possono inflazionare metriche superficiali come il deployment frequency senza migliorare realmente la qualità.

```
┌─────────────────────────────────────────────────────────┐
│           FRAMEWORK COMBINATO DI MISURAZIONE            │
│                                                         │
│  DORA (Operational)           SPACE (Holistic)          │
│  ├─ Deployment Frequency      ├─ Satisfaction           │
│  ├─ Lead Time                 ├─ Performance            │
│  ├─ Change Failure Rate       ├─ Activity               │
│  ├─ Time to Restore           ├─ Communication          │
│  └─ Rework Rate               └─ Efficiency             │
│                                                         │
│  DX Core 4 (Business)        Flow Metrics               │
│  ├─ Speed                     ├─ Flow Velocity           │
│  ├─ Effectiveness             ├─ Flow Time               │
│  ├─ Quality                   ├─ Flow Efficiency         │
│  └─ Business Impact           └─ Flow Load               │
└─────────────────────────────────────────────────────────┘
```

---

## Developer Experience (DevEx)

### Le Tre Dimensioni della DevEx

La Developer Experience (DevEx) è la qualità percepita dell'esperienza degli sviluppatori durante il loro lavoro quotidiano. Non si tratta solo di produttività misurabile: comprende soddisfazione, capacità cognitiva e flusso di lavoro. Le organizzazioni con alta qualità DevEx hanno il 31% di probabilità in più di migliorare il delivery flow (Gartner, 2026).

Le tre dimensioni fondamentali sono:

1. **Feedback Loops**: quanto velocemente un developer può testare e validare il proprio lavoro. Un ciclo di feedback di CI che richiede 45 minuti è un killer della produttività. L'obiettivo è CI in meno di 10 minuti.

2. **Cognitive Load**: la quantità di sforzo mentale necessario per completare un task. Sistemi non intuitivi, documentazione assente, e necessità di context-switching continuo aumentano il carico cognitivo. La piattaforma deve ridurlo attraverso astrazione e standardizzazione.

3. **Flow State**: la capacità dei developer di entrare e rimanere in uno stato di concentrazione profonda. Interruzioni, permessi da richiedere, e pipeline lente distruggono il flow.

### Ottimizzare i Feedback Loop nella CI

```yaml
# Strategia per CI veloce (target: < 10 minuti)
# .github/workflows/fast-ci.yml
name: Fast CI

on:
  pull_request:
    branches: [main]

concurrency:
  group: ci-${{ github.head_ref }}
  cancel-in-progress: true  # Cancella run precedenti sulla stessa PR

jobs:
  # Job 1: Controlli rapidi (< 2 minuti)
  quick-checks:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 1  # Shallow clone per velocità

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci --prefer-offline  # Usa cache locale

      - name: Lint (solo file modificati)
        run: |
          FILES=$(git diff --name-only --diff-filter=ACMRT ${{ github.event.pull_request.base.sha }} \
            | grep -E '\.(ts|tsx|js|jsx)$' || true)
          if [ -n "$FILES" ]; then
            echo "$FILES" | xargs npx eslint --max-warnings 0
          fi

      - name: Type check (incrementale)
        run: npx tsc --noEmit --incremental

  # Job 2: Test (< 5 minuti con parallelismo)
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    needs: quick-checks
    strategy:
      matrix:
        shard: [1, 2, 3, 4]  # Parallelismo 4x
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci --prefer-offline

      - name: Test (shard ${{ matrix.shard }}/4)
        run: |
          npx vitest run \
            --shard=${{ matrix.shard }}/4 \
            --reporter=verbose \
            --coverage.enabled=true
```

### Metriche DevEx da Monitorare

| Metrica | Come misurarla | Target |
|---------|---------------|--------|
| **Tempo CI medio** | Durata media workflow CI | < 10 minuti |
| **Tempo primo feedback PR** | Tempo tra apertura PR e primo commento/review | < 4 ore |
| **Onboarding time** | Tempo dal primo giorno al primo deploy in produzione | < 1 settimana |
| **Tooling satisfaction** | Survey trimestrale (scala 1-5) | ≥ 4.0 |
| **Context switches/giorno** | Conteggio interruzioni e cambio contesto | < 3 |
| **Tempo per setup ambiente locale** | Dal clone al `npm run dev` funzionante | < 15 minuti |
| **Documentazione freshness** | Percentuale docs aggiornati negli ultimi 90 giorni | > 80% |

---

## Strategie di Deploy Avanzate

### Blue-Green Deployment

Il blue-green deployment mantiene due ambienti di produzione identici (blue e green). In ogni momento, uno dei due è attivo (riceve traffico), mentre l'altro è inattivo (pronto per il prossimo deploy). Il cutover avviene spostando il traffico dall'ambiente attivo a quello aggiornato.

```
┌───────────────────────────────────────────────────────┐
│                  BLUE-GREEN DEPLOY                     │
│                                                       │
│  Stato iniziale:                                      │
│  Load Balancer ──────► [BLUE v1.0] ← attivo           │
│                        [GREEN v1.0] ← standby         │
│                                                       │
│  Deploy v1.1:                                         │
│  Load Balancer ──────► [BLUE v1.0] ← attivo           │
│                        [GREEN v1.1] ← deploy in corso │
│                                                       │
│  Cutover:                                             │
│  Load Balancer ──────► [GREEN v1.1] ← nuovo attivo    │
│                        [BLUE v1.0] ← rollback pronto  │
│                                                       │
│  Vantaggi:                                            │
│  • Zero downtime                                      │
│  • Rollback istantaneo (basta reindirizzare)          │
│  • Test completo su ambiente identico a produzione    │
│                                                       │
│  Svantaggi:                                           │
│  • Costo doppio infrastruttura                        │
│  • Complessità database migration (schemi condivisi)  │
│  • Cutover tutto-o-niente                             │
└───────────────────────────────────────────────────────┘
```

### Canary Deployment

Il canary deployment instrada gradualmente una percentuale crescente di traffico alla nuova versione, monitorando le metriche prima di procedere.

```yaml
# .github/workflows/canary-deploy.yml
name: Canary Deployment

on:
  workflow_dispatch:
    inputs:
      image_tag:
        description: 'Tag immagine da deployare'
        required: true
      canary_percentage:
        description: 'Percentuale traffico canary iniziale'
        required: true
        default: '10'

jobs:
  canary:
    runs-on: ubuntu-latest
    environment: production-canary
    steps:
      - uses: actions/checkout@v4

      - name: Setup kubectl
        uses: azure/k8s-set-context@v4
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_PRODUCTION }}

      - name: Deploy canary (versione nuova)
        run: |
          # Creare deployment canary con percentuale ridotta
          cat <<YAML | kubectl apply -f -
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: backend-canary
            namespace: production
            labels:
              app: backend
              track: canary
          spec:
            replicas: 1
            selector:
              matchLabels:
                app: backend
                track: canary
            template:
              metadata:
                labels:
                  app: backend
                  track: canary
              spec:
                containers:
                  - name: backend
                    image: ghcr.io/org/project/backend:${{ inputs.image_tag }}
                    ports:
                      - containerPort: 3000
          YAML

      - name: Configurare split del traffico
        run: |
          # Configurare Istio VirtualService per canary
          cat <<YAML | kubectl apply -f -
          apiVersion: networking.istio.io/v1beta1
          kind: VirtualService
          metadata:
            name: backend
            namespace: production
          spec:
            hosts:
              - api.example.com
            http:
              - route:
                  - destination:
                      host: backend
                      subset: stable
                    weight: $((100 - ${{ inputs.canary_percentage }}))
                  - destination:
                      host: backend
                      subset: canary
                    weight: ${{ inputs.canary_percentage }}
          YAML

      - name: Monitorare metriche canary (15 minuti)
        run: |
          echo "Monitoraggio canary per 15 minuti..."
          for i in $(seq 1 15); do
            # Query Prometheus per error rate canary
            ERROR_RATE=$(curl -s "http://prometheus:9090/api/v1/query" \
              --data-urlencode "query=rate(http_requests_total{track=\"canary\",code=~\"5..\"}[5m]) / rate(http_requests_total{track=\"canary\"}[5m])" \
              | jq -r '.data.result[0].value[1] // "0"')

            LATENCY_P99=$(curl -s "http://prometheus:9090/api/v1/query" \
              --data-urlencode "query=histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{track=\"canary\"}[5m]))" \
              | jq -r '.data.result[0].value[1] // "0"')

            echo "Minuto $i - Error rate: ${ERROR_RATE}% | P99 latency: ${LATENCY_P99}s"

            # Soglie di abort
            if (( $(echo "$ERROR_RATE > 0.05" | bc -l) )); then
              echo "ABORT: Error rate canary troppo alto (${ERROR_RATE} > 5%)"
              kubectl delete deployment backend-canary -n production
              exit 1
            fi

            sleep 60
          done
          echo "Canary stabile. Pronto per promozione."

      - name: Promuovere canary a stabile
        if: success()
        run: |
          kubectl set image deployment/backend \
            backend=ghcr.io/org/project/backend:${{ inputs.image_tag }} \
            -n production
          kubectl rollout status deployment/backend -n production --timeout=300s
          kubectl delete deployment backend-canary -n production
          echo "Promozione completata."
```

### Progressive Delivery con Feature Flags

I feature flags separano il deploy del codice dall'attivazione delle funzionalità. Questo permette di deployare codice inattivo in produzione e attivarlo gradualmente.

```
┌───────────────────────────────────────────────────────────┐
│              PROGRESSIVE DELIVERY                          │
│                                                           │
│  1. Deploy codice      → Codice in produzione, flag OFF   │
│  2. Internal testing   → Flag ON per team interno         │
│  3. Beta users         → Flag ON per 5% utenti beta      │
│  4. Canary rollout     → Flag ON per 10% traffico        │
│  5. Progressive        → 25% → 50% → 75% → 100%         │
│  6. General release    → Flag rimosso, codice permanente  │
│                                                           │
│  In ogni momento: rollback = flag OFF (istantaneo)        │
└───────────────────────────────────────────────────────────┘
```

### Confronto Strategie di Deploy

| Strategia | Zero Downtime | Rollback | Costo Infra | Complessità | Validazione Graduale |
|-----------|:---:|:---:|:---:|:---:|:---:|
| **Rolling Update** | Sì | Lento (rollback) | Basso | Bassa | No |
| **Blue-Green** | Sì | Istantaneo | Alto (2x) | Media | No |
| **Canary** | Sì | Veloce | Medio | Alta | Sì |
| **Feature Flags** | Sì | Istantaneo | Basso | Media | Sì |
| **Progressive** | Sì | Istantaneo | Medio | Molto alta | Sì |

---

## Supply Chain Security e Attestazione SLSA

### Il Framework SLSA

SLSA (Supply-chain Levels for Software Artifacts, pronunciato "salsa") è un framework per migliorare l'integrità end-to-end degli artefatti software durante il loro ciclo di vita. Definisce livelli incrementali di sicurezza per la supply chain.

| Livello | Requisiti | GitHub Actions |
|---------|-----------|----------------|
| **SLSA Build L0** | Nessuna garanzia | Build senza attestazione |
| **SLSA Build L1** | Provenienza documentata | Artifact attestations base |
| **SLSA Build L2** | Provenienza firmata, build service ospitato | GitHub Actions + attestations |
| **SLSA Build L3** | Build isolata, provenienza non falsificabile | Reusable workflows + attestations |

### Generare Attestazioni SLSA con GitHub Actions

```yaml
# .github/workflows/slsa-release.yml
name: SLSA Release

on:
  push:
    tags: ['v*.*.*']

permissions:
  contents: write
  packages: write
  id-token: write       # Necessario per OIDC e Sigstore
  attestations: write   # Necessario per artifact attestations

jobs:
  build-and-attest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build e push immagine
        id: build
        uses: docker/build-push-action@v5
        with:
          context: apps/backend
          push: true
          tags: ghcr.io/${{ github.repository }}/backend:${{ github.ref_name }}

      - name: Generare SBOM
        uses: anchore/sbom-action@v0
        with:
          image: ghcr.io/${{ github.repository }}/backend:${{ github.ref_name }}
          format: spdx-json
          output-file: sbom.spdx.json

      - name: Attestare provenienza build
        uses: actions/attest-build-provenance@v2
        with:
          subject-name: ghcr.io/${{ github.repository }}/backend
          subject-digest: ${{ steps.build.outputs.digest }}
          push-to-registry: true

      - name: Attestare SBOM
        uses: actions/attest-sbom@v2
        with:
          subject-name: ghcr.io/${{ github.repository }}/backend
          subject-digest: ${{ steps.build.outputs.digest }}
          sbom-path: sbom.spdx.json
          push-to-registry: true

      - name: Verificare attestazione
        run: |
          gh attestation verify \
            oci://ghcr.io/${{ github.repository }}/backend:${{ github.ref_name }} \
            --owner ${{ github.repository_owner }}
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### SBOM (Software Bill of Materials)

L'SBOM è un inventario completo di tutte le dipendenze di un software, sempre più richiesto per compliance (Executive Order 14028 USA, NIS2 EU). GitHub supporta la generazione e l'attestazione SBOM nativamente.

```
┌───────────────────────────────────────────────────────────────┐
│                    SUPPLY CHAIN SECURITY                       │
│                                                               │
│  Source Code ──────► Build ──────► Artifact ──────► Deploy    │
│       │                │              │                │      │
│  ┌────▼────┐    ┌─────▼─────┐  ┌────▼────┐    ┌─────▼────┐  │
│  │ Secret  │    │ Build     │  │ SBOM    │    │ Runtime  │  │
│  │ Scan    │    │ Provenance│  │ Attestat│    │ Verifica │  │
│  │ (Gitleaks)│  │ (Sigstore)│  │ (SPDX)  │    │ (Cosign) │  │
│  └─────────┘    └───────────┘  └─────────┘    └──────────┘  │
│       │                │              │                │      │
│  Pre-commit      SLSA L3        Compliance       Admission   │
│  hook            attestation    requirement      controller  │
└───────────────────────────────────────────────────────────────┘
```

---

## Osservabilità Integrata: OpenTelemetry, Prometheus, Grafana

### I Tre Pilastri dell'Osservabilità

L'osservabilità moderna si basa su tre pilastri fondamentali — metriche, log e tracce — idealmente unificati tramite il protocollo OpenTelemetry.

| Pilastro | Cosa misura | Tool | Protocollo |
|----------|------------|------|------------|
| **Metriche** | Valori numerici aggregati nel tempo (CPU, latenza, error rate) | Prometheus → Grafana | OTLP / Prometheus exposition |
| **Log** | Eventi testuali strutturati con timestamp | Loki → Grafana | OTLP / Loki push |
| **Tracce** | Percorso di una richiesta attraverso servizi distribuiti | Tempo → Grafana | OTLP / Jaeger |

### OpenTelemetry: Lo Standard Unificato

OpenTelemetry (OTel) è il progetto CNCF che fornisce un set unificato di API, SDK e tool per generare, raccogliere e esportare dati di telemetria. Nel 2026 il 48,5% delle organizzazioni usa già OpenTelemetry, con un ulteriore 25,3% che pianifica l'adozione.

Con la release di Prometheus 3.9.0 (2025), il supporto nativo per il protocollo OTLP Metrics è diventato stabile, permettendo a Prometheus di ricevere metriche direttamente dagli esportatori OpenTelemetry senza bisogno di sidecar. Grafana Alloy ha sostituito Grafana Agent (EOL novembre 2025) come pipeline di telemetria unificata.

```yaml
# infrastructure/kubernetes/monitoring/otel-collector.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
  namespace: monitoring
data:
  config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318

    processors:
      batch:
        send_batch_size: 1024
        timeout: 5s
      memory_limiter:
        check_interval: 1s
        limit_mib: 512
        spike_limit_mib: 128
      resource:
        attributes:
          - key: environment
            action: insert
            value: "${ENVIRONMENT}"
          - key: service.namespace
            action: insert
            value: "my-project"

    exporters:
      prometheusremotewrite:
        endpoint: http://prometheus:9090/api/v1/write
        resource_to_telemetry_conversion:
          enabled: true
      loki:
        endpoint: http://loki:3100/loki/api/v1/push
      otlp/tempo:
        endpoint: http://tempo:4317
        tls:
          insecure: true

    service:
      pipelines:
        metrics:
          receivers: [otlp]
          processors: [memory_limiter, batch, resource]
          exporters: [prometheusremotewrite]
        logs:
          receivers: [otlp]
          processors: [memory_limiter, batch, resource]
          exporters: [loki]
        traces:
          receivers: [otlp]
          processors: [memory_limiter, batch, resource]
          exporters: [otlp/tempo]
```

### Dashboard Grafana per Pipeline DevOps

```json
{
  "dashboard": {
    "title": "DevOps Pipeline Overview",
    "panels": [
      {
        "title": "Deployment Frequency (ultimi 30 giorni)",
        "type": "stat",
        "targets": [
          {
            "expr": "count(kube_deployment_status_observed_generation{namespace=\"production\"} != kube_deployment_metadata_generation{namespace=\"production\"}) or vector(0)"
          }
        ]
      },
      {
        "title": "Error Rate per Servizio",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{code=~\"5..\"}[5m])) by (service) / sum(rate(http_requests_total[5m])) by (service) * 100"
          }
        ]
      },
      {
        "title": "Latenza P99 per Endpoint",
        "type": "heatmap",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler))"
          }
        ]
      },
      {
        "title": "Pod Health",
        "type": "table",
        "targets": [
          {
            "expr": "kube_pod_status_phase{namespace=~\"staging|production\"}"
          }
        ]
      }
    ]
  }
}
```

### Integrare Osservabilità con GitHub Actions

```yaml
# .github/workflows/observability-check.yml
name: Post-Deploy Observability Check

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      duration_minutes:
        required: false
        type: number
        default: 10

jobs:
  check-metrics:
    runs-on: ubuntu-latest
    steps:
      - name: Attendere stabilizzazione
        run: sleep 120  # 2 minuti per warm-up

      - name: Verificare error rate
        run: |
          ERROR_RATE=$(curl -s "${{ secrets.PROMETHEUS_URL }}/api/v1/query" \
            --data-urlencode "query=sum(rate(http_requests_total{namespace=\"${{ inputs.environment }}\",code=~\"5..\"}[5m])) / sum(rate(http_requests_total{namespace=\"${{ inputs.environment }}\"}[5m]))" \
            | jq -r '.data.result[0].value[1] // "0"')

          echo "Error rate: ${ERROR_RATE}"
          if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
            echo "::error::Error rate superiore all'1%: ${ERROR_RATE}"
            exit 1
          fi

      - name: Verificare latenza
        run: |
          P99=$(curl -s "${{ secrets.PROMETHEUS_URL }}/api/v1/query" \
            --data-urlencode "query=histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{namespace=\"${{ inputs.environment }}\"}[5m])) by (le))" \
            | jq -r '.data.result[0].value[1] // "0"')

          echo "P99 latency: ${P99}s"
          if (( $(echo "$P99 > 2.0" | bc -l) )); then
            echo "::error::P99 latenza superiore a 2s: ${P99}s"
            exit 1
          fi

      - name: Verificare disponibilità pod
        run: |
          READY=$(curl -s "${{ secrets.PROMETHEUS_URL }}/api/v1/query" \
            --data-urlencode "query=sum(kube_deployment_status_replicas_ready{namespace=\"${{ inputs.environment }}\"}) / sum(kube_deployment_spec_replicas{namespace=\"${{ inputs.environment }}\"})" \
            | jq -r '.data.result[0].value[1] // "0"')

          echo "Pod readiness: ${READY}"
          if (( $(echo "$READY < 1.0" | bc -l) )); then
            echo "::warning::Non tutti i pod sono ready: ${READY}"
          fi
```

---

## FinOps: Ottimizzazione dei Costi Cloud nel Ciclo DevOps

### FinOps come Pratica DevOps

FinOps (Financial Operations) è la pratica di gestire i costi cloud con la stessa disciplina ingegneristica applicata al codice. Nel 2026, il mercato globale FinOps è valutato a circa 12,4 miliardi di dollari e proiettato a raggiungere 28 miliardi entro il 2028. Gli studi dimostrano che le organizzazioni sprecano dal 25% al 35% della spesa cloud in risorse inattive, istanze sovradimensionate e storage orfano.

FinOps non è più un'attività centralizzata guidata dal finance: è una capacità core del toolkit dell'ingegnere di piattaforma. L'evoluzione nel 2026 vede FinOps espandersi oltre il cloud per gestire anche SaaS (90% delle organizzazioni), licensing (64%), private cloud (57%) e data center (48%).

### FinOps as Code nella Pipeline

```yaml
# .github/workflows/cost-check.yml
name: Infrastructure Cost Check

on:
  pull_request:
    paths: ['infrastructure/terraform/**']

jobs:
  cost-estimate:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Setup Infracost
        uses: infracost/actions/setup@v3
        with:
          api-key: ${{ secrets.INFRACOST_API_KEY }}

      - name: Generare baseline dei costi
        run: |
          infracost breakdown \
            --path infrastructure/terraform/environments/staging \
            --format json \
            --out-file /tmp/infracost-base.json
        env:
          INFRACOST_TERRAFORM_CLOUD_TOKEN: ${{ secrets.TFC_TOKEN }}

      - name: Generare diff dei costi
        run: |
          infracost diff \
            --path infrastructure/terraform/environments/staging \
            --compare-to /tmp/infracost-base.json \
            --format json \
            --out-file /tmp/infracost-diff.json

      - name: Commentare PR con stima costi
        uses: infracost/actions/comment@v1
        with:
          path: /tmp/infracost-diff.json
          behavior: update

      - name: Gate: bloccare se costi superano soglia
        run: |
          MONTHLY_DIFF=$(jq -r '.diffTotalMonthlyCost' /tmp/infracost-diff.json)
          THRESHOLD=500

          if (( $(echo "$MONTHLY_DIFF > $THRESHOLD" | bc -l) )); then
            echo "::error::L'aumento di costo mensile ($MONTHLY_DIFF USD) supera la soglia di $THRESHOLD USD"
            echo "::error::Richiesta approvazione esplicita del team FinOps"
            exit 1
          fi

          echo "Aumento di costo mensile: $MONTHLY_DIFF USD (sotto soglia di $THRESHOLD USD)"
```

### Checklist FinOps per DevOps Engineer

| Area | Controllo | Automazione |
|------|----------|-------------|
| **Compute** | Istanze right-sized | Kube resource recommender |
| **Storage** | Nessun volume orfano | Script pulizia settimanale |
| **Network** | NAT Gateway ottimizzato | VPC endpoint dove possibile |
| **Database** | Istanze non-prod spente fuori orario | Lambda scheduled |
| **CI/CD** | Runner appropriatamente dimensionati | Spot instances per CI |
| **Container** | Immagini base ottimizzate (alpine) | Trivy + size check |
| **Ambienti** | Preview env con TTL | Auto-cleanup dopo merge |
| **Caching** | Turbo Remote Cache abilitato | turbo.json configurato |

---

## Workflow Riutilizzabili e Composite Actions

### Principio DRY nella CI/CD

Man mano che un'organizzazione cresce, la duplicazione dei workflow diventa un problema di manutenibilità. GitHub Actions offre due meccanismi di riuso: **Reusable Workflows** e **Composite Actions**. La scelta dipende dal livello di astrazione necessario.

```
┌────────────────────────────────────────────────────────┐
│              GERARCHIA DI RIUSO                         │
│                                                        │
│  Reusable Workflow (intero pipeline)                   │
│  ├─ Definisce job completi con runs-on, services       │
│  ├─ Può contenere multiple job                         │
│  ├─ Chiamato con workflow_call                         │
│  └─ Isolamento SLSA Build L3                           │
│                                                        │
│  Composite Action (set di step riutilizzabili)         │
│  ├─ Combinazione di step dentro un singolo job         │
│  ├─ Inputs, outputs, env vars                          │
│  ├─ Deve specificare shell per ogni run step           │
│  └─ NON può definire job o services                    │
│                                                        │
│  Shared Action (singola operazione)                    │
│  ├─ JavaScript o Docker action                         │
│  ├─ Singolo task specializzato                         │
│  └─ Marketplace o repository interno                   │
└────────────────────────────────────────────────────────┘
```

### Reusable Workflow: CI Template

```yaml
# .github/workflows/reusable-ci.yml
name: Reusable CI Pipeline

on:
  workflow_call:
    inputs:
      node-version:
        required: false
        type: string
        default: '20'
      working-directory:
        required: false
        type: string
        default: '.'
      run-e2e:
        required: false
        type: boolean
        default: false
    secrets:
      TURBO_TOKEN:
        required: false
      CODECOV_TOKEN:
        required: false
    outputs:
      coverage:
        description: 'Percentuale di coverage'
        value: ${{ jobs.test.outputs.coverage }}

jobs:
  lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check

  test:
    runs-on: ubuntu-latest
    needs: lint
    outputs:
      coverage: ${{ steps.coverage.outputs.pct }}
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'npm'
      - run: npm ci
      - run: npm run test -- --coverage
      - name: Estrarre percentuale coverage
        id: coverage
        run: |
          PCT=$(jq -r '.total.lines.pct' coverage/coverage-summary.json)
          echo "pct=$PCT" >> $GITHUB_OUTPUT
          echo "Coverage: ${PCT}%"
      - name: Gate: coverage minima 80%
        run: |
          PCT="${{ steps.coverage.outputs.pct }}"
          if (( $(echo "$PCT < 80" | bc -l) )); then
            echo "::error::Coverage ${PCT}% è sotto il minimo del 80%"
            exit 1
          fi
```

```yaml
# Chiamata dal workflow specifico del progetto
# .github/workflows/ci.yml
name: CI
on:
  pull_request:
    branches: [main]

jobs:
  ci:
    uses: org/.github/.github/workflows/reusable-ci.yml@main
    with:
      node-version: '20'
      working-directory: 'apps/backend'
      run-e2e: true
    secrets:
      TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

### Composite Action: Setup Comune

```yaml
# .github/actions/setup-project/action.yml
name: Setup Project
description: Configura l'ambiente di sviluppo del progetto

inputs:
  node-version:
    description: 'Versione Node.js'
    required: false
    default: '20'
  install-playwright:
    description: 'Installare browser Playwright'
    required: false
    default: 'false'

outputs:
  cache-hit:
    description: 'Se la cache npm è stata utilizzata'
    value: ${{ steps.cache.outputs.cache-hit }}

runs:
  using: composite
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'

    - name: Cache node_modules
      id: cache
      uses: actions/cache@v4
      with:
        path: node_modules
        key: node-${{ runner.os }}-${{ hashFiles('package-lock.json') }}
        restore-keys: node-${{ runner.os }}-

    - name: Installare dipendenze
      if: steps.cache.outputs.cache-hit != 'true'
      shell: bash
      run: npm ci

    - name: Installare Playwright
      if: inputs.install-playwright == 'true'
      shell: bash
      run: npx playwright install --with-deps chromium
```

### Organizzazione Repository per Workflow Condivisi

```
org/.github/                          # Repository speciale dell'organizzazione
├── .github/
│   ├── workflows/
│   │   ├── reusable-ci.yml           # CI template
│   │   ├── reusable-cd.yml           # CD template
│   │   ├── reusable-security.yml     # Security scan template
│   │   └── reusable-release.yml      # Release template
│   └── actions/
│       ├── setup-project/
│       │   └── action.yml
│       ├── docker-build/
│       │   └── action.yml
│       ├── deploy-k8s/
│       │   └── action.yml
│       └── notify-slack/
│           └── action.yml
├── workflow-templates/               # Template per nuovi repository
│   ├── ci.yml
│   ├── ci.properties.json
│   ├── cd.yml
│   └── cd.properties.json
└── profile/
    └── README.md                     # Profilo organizzazione
```

---

## GitHub Environments e Deployment Protection Rules

### Architettura degli Environments

GitHub Environments forniscono un meccanismo nativo per gestire deployment target con isolamento di secrets, protection rules e audit trail. Ogni environment può avere i propri secrets, variabili, e regole di protezione indipendenti.

```
┌────────────────────────────────────────────────────────────┐
│                    ENVIRONMENT HIERARCHY                     │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  development  │  │   staging    │  │  production  │     │
│  │              │  │              │  │              │     │
│  │ Secrets:     │  │ Secrets:     │  │ Secrets:     │     │
│  │ • DB_URL     │  │ • DB_URL     │  │ • DB_URL     │     │
│  │ • API_KEY    │  │ • API_KEY    │  │ • API_KEY    │     │
│  │              │  │              │  │              │     │
│  │ Protection:  │  │ Protection:  │  │ Protection:  │     │
│  │ • Nessuna    │  │ • Branch     │  │ • Reviewers  │     │
│  │              │  │   rules      │  │ • Wait timer │     │
│  │              │  │              │  │ • Branch     │     │
│  │              │  │              │  │   rules      │     │
│  │              │  │              │  │ • Custom     │     │
│  │              │  │              │  │   rules      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                            │
│  Flow: dev ──► staging (auto) ──► production (approval)    │
└────────────────────────────────────────────────────────────┘
```

### Tipi di Protection Rules

| Tipo | Comportamento | Caso d'uso |
|------|--------------|------------|
| **Required Reviewers** | Richiede approvazione da persone/team specifici (max 6) | Deploy produzione |
| **Wait Timer** | Introduce un delay (0-43200 minuti) | Finestra di osservazione post-staging |
| **Branch Restrictions** | Solo branch specifici possono triggerare il deploy | Solo `main` e `release/*` |
| **Custom Protection Rules** | GitHub App esterna valida readiness | Datadog monitors, Honeycomb SLO |

### Custom Deployment Protection Rules

Le custom deployment protection rules permettono di integrare sistemi esterni nel processo di approvazione. Ad esempio, un deploy può essere bloccato se Datadog rileva anomalie nei monitor, o se Honeycomb segnala violazioni degli SLO.

```yaml
# Workflow che usa environments con protection rules
# .github/workflows/deploy-with-gates.yml
name: Deploy with Gates

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy staging
        run: echo "Deploying to staging..."

  # Questo job si blocca fino all'approvazione manuale
  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production        # Ha required reviewers configurati
      url: https://example.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy production
        run: echo "Deploying to production..."

      - name: Annotare deployment
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.repos.createDeploymentStatus({
              owner: context.repo.owner,
              repo: context.repo.repo,
              deployment_id: context.payload.deployment?.id,
              state: 'success',
              environment_url: 'https://example.com',
              description: 'Production deploy completed'
            });
```

---

## AI e Automazione nel Ciclo DevOps

### L'Era del DevOps Agentico (2025-2026)

L'integrazione dell'AI nel DevOps sta evolvendo rapidamente. Nel 2025, il 76% dei team DevOps ha integrato AI nelle pipeline CI/CD. Nel 2026, l'evoluzione verso il **DevOps Agentico** vede agenti AI autonomi che gestiscono task multi-step attraverso l'intero SDLC.

Le aree principali di applicazione dell'AI nel DevOps sono:

```
┌────────────────────────────────────────────────────────┐
│              AI NEL CICLO DEVOPS                        │
│                                                        │
│  1. CODE GENERATION                                    │
│     • Copilot per sviluppo                             │
│     • Generazione test automatica                      │
│     • Refactoring assistito                            │
│                                                        │
│  2. CODE REVIEW                                        │
│     • Analisi automatica delle PR                      │
│     • Suggerimenti di sicurezza                        │
│     • Rilevamento pattern problematici                 │
│                                                        │
│  3. INCIDENT RESPONSE                                  │
│     • Triage automatico alert                          │
│     • Root cause analysis assistita                    │
│     • Suggerimenti di remediation                      │
│                                                        │
│  4. PIPELINE OPTIMIZATION                              │
│     • Test selection intelligente                      │
│     • Predizione failure                               │
│     • Ottimizzazione parallelismo                      │
│                                                        │
│  5. INFRASTRUCTURE                                     │
│     • Right-sizing automatico risorse                  │
│     • Anomaly detection su metriche                    │
│     • Capacity planning predittivo                     │
│                                                        │
│  6. SECURITY                                           │
│     • Analisi vulnerabilità assistita                  │
│     • Pattern detection in log di sicurezza            │
│     • Compliance checking automatizzato                │
└────────────────────────────────────────────────────────┘
```

### GitHub Copilot e Agent Mode per DevOps

GitHub Copilot Agent Mode (2025-2026) trasforma Copilot da strumento di completamento codice a partner di sviluppo agentico completo. L'agente può tradurre idee in codice, identificare sottotask necessari, eseguirli su file multipli, e gestire task infrastrutturali complessi. Quando si assegna una issue GitHub a Copilot, l'agente lavora autonomamente e invia commit a una draft pull request, con log di sessione consultabili in tempo reale.

Il Copilot SDK permette di costruire agenti AI custom per DevOps che coprono validazione infrastruttura, incident response e automazione delle pipeline.

### Automazione Code Review con AI

```yaml
# .github/workflows/ai-review.yml
name: AI-Assisted Code Review

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  pull-requests: write
  contents: read

jobs:
  ai-review:
    runs-on: ubuntu-latest
    if: github.event.pull_request.draft == false
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Analisi diff per review
        id: diff
        run: |
          DIFF=$(git diff ${{ github.event.pull_request.base.sha }}..${{ github.event.pull_request.head.sha }} -- '*.ts' '*.tsx' '*.js')
          STATS=$(git diff --stat ${{ github.event.pull_request.base.sha }}..${{ github.event.pull_request.head.sha }})
          echo "files_changed=$(echo "$STATS" | tail -1)" >> $GITHUB_OUTPUT

      - name: Verificare dimensione PR
        run: |
          ADDITIONS=$(gh pr view ${{ github.event.pull_request.number }} --json additions -q '.additions')
          DELETIONS=$(gh pr view ${{ github.event.pull_request.number }} --json deletions -q '.deletions')
          TOTAL=$((ADDITIONS + DELETIONS))

          if [ "$TOTAL" -gt 500 ]; then
            gh pr comment ${{ github.event.pull_request.number }} \
              --body "Questa PR modifica $TOTAL righe. Considera di dividerla in PR più piccole per facilitare la review (target: < 400 righe)."
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Verificare test coverage
        run: |
          # Verificare che nuovi file .ts abbiano file .test.ts corrispondenti
          NEW_FILES=$(git diff --name-only --diff-filter=A \
            ${{ github.event.pull_request.base.sha }}..${{ github.event.pull_request.head.sha }} \
            | grep -E '\.tsx?$' | grep -v '\.test\.' | grep -v '\.spec\.' || true)

          MISSING_TESTS=""
          for f in $NEW_FILES; do
            TEST_FILE="${f%.ts}.test.ts"
            TEST_FILE2="${f%.tsx}.test.tsx"
            if [ ! -f "$TEST_FILE" ] && [ ! -f "$TEST_FILE2" ]; then
              MISSING_TESTS="${MISSING_TESTS}\n- \`${f}\`"
            fi
          done

          if [ -n "$MISSING_TESTS" ]; then
            gh pr comment ${{ github.event.pull_request.number }} \
              --body "I seguenti nuovi file non hanno test corrispondenti:${MISSING_TESTS}"
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Attenzione: Rischi dell'AI nel DevOps

Nonostante i benefici, l'adozione dell'AI nel DevOps richiede cautela:

- **Code churn raddoppiato**: il codice generato da AI necessita spesso di rework, con previsioni di raddoppio del churn nel 2026
- **Metriche inflate**: deployment frequency e lead time possono migliorare artificialmente senza reale guadagno di qualità
- **Stability decrease**: il report DORA 2024 di Google ha registrato un calo del 7,2% nella stabilità del delivery
- **Sicurezza**: output AI va trattato come input non fidato — validare, sanitizzare, sandboxare
- **Dipendenza eccessiva**: rischio di perdita di competenza nel debugging e problem-solving manuale

---

## Anti-Pattern DevOps e Come Evitarli

### I 12 Anti-Pattern Più Comuni

| # | Anti-Pattern | Problema | Soluzione |
|---|-------------|----------|-----------|
| 1 | **Snowflake servers** | Ogni server è configurato manualmente e unico | Infrastructure as Code (Terraform, Pulumi) |
| 2 | **CI/CD teatro** | Pipeline esistono ma nessuno le guarda | Alert su failure, dashboard visibili, ownership |
| 3 | **GitOps senza Git** | Manifesti in Git ma modifiche manuali in produzione | Self-heal attivo (ArgoCD), deny manual kubectl |
| 4 | **Mega-PR** | PR con migliaia di righe impossibili da revieware | PR < 400 righe, feature flags per WIP |
| 5 | **Secret sprawl** | Segreti duplicati in più posti senza rotazione | Vault centralizzato, OIDC, rotazione automatica |
| 6 | **Alert fatigue** | Troppi alert non azionabili | SLO-based alerting, error budget policies |
| 7 | **Hero culture** | Una persona sa tutto, singolo punto di failure | Runbook, pair rotation, blameless postmortem |
| 8 | **Env parity gap** | Staging diverso da produzione | Container identici, same IaC, traffic mirroring |
| 9 | **Test in produzione (non intenzionale)** | Feature non testate che raggiungono produzione | Quality gates automatiche, coverage minima |
| 10 | **Cargo cult DevOps** | Adottare tool senza capire i principi | Partire dai problemi, non dagli strumenti |
| 11 | **Pipeline monolitica** | Un workflow CI/CD unico per tutto | Workflow modulari, reusable workflows |
| 12 | **FinOps afterthought** | Costi cloud ignorati fino alla fattura | Cost gates in PR, budget alert, right-sizing |

### Pattern di Maturità DevOps

```
┌───────────────────────────────────────────────────────────┐
│           MODELLO DI MATURITÀ DEVOPS                       │
│                                                           │
│  Livello 0: MANUALE                                       │
│  • Deploy manuali via SSH                                 │
│  • Nessun test automatizzato                              │
│  • Nessun IaC                                             │
│                                                           │
│  Livello 1: CI BASICO                                     │
│  • Test automatizzati su push                             │
│  • Build automatica                                       │
│  • Deploy semi-automatico (script)                        │
│                                                           │
│  Livello 2: CI/CD COMPLETO                                │
│  • Pipeline CI/CD end-to-end                              │
│  • Environments con protection rules                      │
│  • IaC (Terraform)                                        │
│  • Monitoring basico                                      │
│                                                           │
│  Livello 3: GITOPS + PLATFORM                             │
│  • GitOps con riconciliazione continua                     │
│  • Internal Developer Platform                            │
│  • Observability completa (metriche, log, tracce)         │
│  • DORA metrics tracking                                  │
│  • Supply chain security (SLSA, SBOM)                     │
│                                                           │
│  Livello 4: ELITE                                         │
│  • Progressive delivery con feature flags                 │
│  • AI-assisted operations                                 │
│  • FinOps integrato nella pipeline                        │
│  • Self-healing infrastructure                            │
│  • SLO-based alerting e error budgets                     │
│  • Developer scorecard e DevEx misurata                   │
│  • Chaos engineering proattivo                            │
└───────────────────────────────────────────────────────────┘
```

---

## OIDC per Deploy Cloud Sicuri

### Perché OIDC Sostituisce i Segreti Statici

L'autenticazione OIDC (OpenID Connect) elimina la necessità di archiviare credenziali cloud come segreti GitHub a lunga durata. Invece, si stabilisce una relazione di fiducia con il cloud provider, e il workflow richiede un access token a breve durata direttamente dal provider.

I tre vantaggi di sicurezza principali sono:

1. **Gestione credenziali**: il cloud provider emette un token a breve durata valido solo per un singolo job, che scade automaticamente
2. **Controllo granulare**: il cloud provider applica le proprie politiche authN/authZ per controllare l'accesso alle risorse
3. **Accesso basato su attributi**: gli admin possono includere proprietà custom del repository nei claim OIDC per politiche ABAC

```yaml
# .github/workflows/deploy-oidc.yml — Deploy AWS con OIDC (no segreti statici)
name: Deploy con OIDC

on:
  push:
    branches: [main]

permissions:
  id-token: write    # Necessario per richiedere il token OIDC
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Configurare credenziali AWS via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy
          role-session-name: github-actions-${{ github.run_id }}
          aws-region: eu-west-1
          # Nessun access key, nessun secret key!
          # Il token OIDC viene scambiato automaticamente

      - name: Verificare identità
        run: aws sts get-caller-identity

      - name: Deploy
        run: |
          # L'accesso è limitato al ruolo IAM specificato
          # Il token scade al termine del job
          aws eks update-kubeconfig --name my-cluster --region eu-west-1
          kubectl apply -k infrastructure/kubernetes/overlays/staging/
```

### Configurazione Trust Policy AWS per GitHub OIDC

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:org/project:environment:staging"
        }
      }
    }
  ]
}
```

Il campo `sub` (subject) limita quale repository e quale environment possono assumere il ruolo. Questo impedisce a repository non autorizzati di richiedere access token per le risorse cloud.

---

## Monitoring e Alerting: SLO, Error Budget e PagerDuty

### SLO-Based Alerting

L'approccio tradizionale di alertare su ogni singolo errore genera **alert fatigue**: troppi alert non azionabili che vengono ignorati. L'approccio SLO-based (Service Level Objective) definisce obiettivi di affidabilità e genera alert solo quando l'**error budget** (margine di errore accettabile) si sta esaurendo.

```
Esempio:
• SLO: 99.9% disponibilità mensile
• Error Budget: 0.1% = 43.2 minuti di downtime ammessi al mese
• Alert quando: error budget consumato > 50% in finestra temporale

┌────────────────────────────────────────────────────┐
│  Mese inizia:  Error Budget = 43.2 min (100%)      │
│                                                    │
│  Giorno 5:     2 min downtime   → Budget = 41.2m  │
│  Giorno 12:    5 min downtime   → Budget = 36.2m  │
│  Giorno 15:    15 min downtime  → Budget = 21.2m  │
│                                                    │
│  ⚠ ALERT: Budget al 49%, burn rate elevato         │
│  → Bloccare deploy non critici                     │
│  → Focalizzarsi su stabilizzazione                 │
│                                                    │
│  Giorno 20:    0 min downtime   → Stabilizzato     │
│  → Riabilitare deploy                              │
└────────────────────────────────────────────────────┘
```

### Integrare PagerDuty con GitHub Actions

```yaml
# .github/workflows/incident-bridge.yml
name: Incident Bridge

on:
  issues:
    types: [opened, labeled]

jobs:
  create-pagerduty-incident:
    if: contains(github.event.issue.labels.*.name, 'incident')
    runs-on: ubuntu-latest
    steps:
      - name: Determinare severità
        id: severity
        run: |
          LABELS='${{ toJSON(github.event.issue.labels.*.name) }}'
          if echo "$LABELS" | grep -q "P0"; then
            echo "urgency=high" >> $GITHUB_OUTPUT
          elif echo "$LABELS" | grep -q "P1"; then
            echo "urgency=high" >> $GITHUB_OUTPUT
          else
            echo "urgency=low" >> $GITHUB_OUTPUT
          fi

      - name: Creare incidente PagerDuty
        run: |
          curl -s -X POST https://events.pagerduty.com/v2/enqueue \
            -H 'Content-Type: application/json' \
            -d '{
              "routing_key": "'${{ secrets.PAGERDUTY_ROUTING_KEY }}'",
              "event_action": "trigger",
              "payload": {
                "summary": "${{ github.event.issue.title }}",
                "severity": "critical",
                "source": "github-issues",
                "custom_details": {
                  "issue_url": "${{ github.event.issue.html_url }}",
                  "author": "${{ github.event.issue.user.login }}",
                  "body": "${{ github.event.issue.body }}"
                }
              },
              "links": [
                {
                  "href": "${{ github.event.issue.html_url }}",
                  "text": "GitHub Issue"
                }
              ]
            }'
```

---

## Compliance-as-Code con OPA e Policy Gates

### Il Problema: Governance Manuale Non Scala

Nelle organizzazioni enterprise, le policy di sicurezza, naming convention e conformità vengono spesso verificate manualmente durante le code review. Questo approccio presenta tre problemi fondamentali: è lento (rallenta il ciclo di feedback), è inconsistente (dipende dall'esperienza del reviewer), e non è auditabile (non lascia traccia strutturata delle decisioni). La soluzione è trattare le policy come codice — versionato, testato, e applicato automaticamente nella pipeline CI/CD.

### Open Policy Agent (OPA) e il Linguaggio Rego

**Open Policy Agent** è il motore di policy standard de facto nel cloud-native. OPA separa la logica decisionale dal software che la applica: le policy vengono scritte in **Rego**, un linguaggio dichiarativo progettato per interrogare strutture dati JSON/YAML complesse.

Rego utilizza un modello basato su regole: ogni regola produce un risultato (allow/deny) in base ai dati di input. Questa separazione consente di riutilizzare le stesse policy su contesti diversi — Terraform plan, manifesti Kubernetes, Dockerfile, configurazioni di rete — senza modificare il codice applicativo.

Esempio di policy Rego per verificare che ogni risorsa Terraform abbia tag obbligatori:

```rego
# policy/terraform/required_tags.rego
package terraform.tags

import future.keywords.in
import future.keywords.every

required_tags := {"team", "environment", "cost-center"}

deny[msg] {
    resource := input.resource_changes[_]
    resource.change.actions[_] == "create"

    tags := object.get(resource.change.after, "tags", {})
    missing := required_tags - {key | tags[key]}
    count(missing) > 0

    msg := sprintf(
        "Risorsa '%s' (%s) manca dei tag obbligatori: %v",
        [resource.address, resource.type, missing]
    )
}

deny[msg] {
    resource := input.resource_changes[_]
    resource.change.actions[_] == "create"
    resource.type == "aws_s3_bucket"

    encryption := object.get(
        resource.change.after,
        "server_side_encryption_configuration", []
    )
    count(encryption) == 0

    msg := sprintf(
        "Bucket S3 '%s' deve avere encryption abilitata",
        [resource.address]
    )
}
```

### Conftest: Policy Validation nella CI

**Conftest** è il tool che porta OPA nella pipeline CI. Utilizza le stesse policy Rego ma le applica direttamente a file di configurazione strutturati — Terraform plan JSON, manifesti Kubernetes, Dockerfile, file Helm values. Conftest restituisce exit code non-zero quando almeno una policy viene violata, integrandosi naturalmente nei workflow GitHub Actions.

```yaml
# .github/workflows/policy-check.yml
name: Policy Compliance Check
on:
  pull_request:
    paths:
      - 'infra/**'
      - 'k8s/**'
      - 'Dockerfile*'

jobs:
  terraform-policy:
    name: Terraform Policy Gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.9.x"

      - name: Terraform Init & Plan
        working-directory: infra/
        run: |
          terraform init -backend=false
          terraform plan -out=tfplan
          terraform show -json tfplan > tfplan.json

      - name: Install Conftest
        run: |
          CONFTEST_VERSION="0.56.0"
          curl -fsSL "https://github.com/open-policy-agent/conftest/releases/download/v${CONFTEST_VERSION}/conftest_${CONFTEST_VERSION}_Linux_x86_64.tar.gz" \
            | tar xz -C /usr/local/bin conftest
          conftest --version

      - name: Run Policy Checks
        working-directory: infra/
        run: |
          conftest test tfplan.json \
            --policy ../policy/terraform/ \
            --output table \
            --all-namespaces

  kubernetes-policy:
    name: Kubernetes Manifest Policy
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Conftest
        run: |
          CONFTEST_VERSION="0.56.0"
          curl -fsSL "https://github.com/open-policy-agent/conftest/releases/download/v${CONFTEST_VERSION}/conftest_${CONFTEST_VERSION}_Linux_x86_64.tar.gz" \
            | tar xz -C /usr/local/bin conftest

      - name: Validate K8s Manifests
        run: |
          conftest test k8s/base/*.yaml \
            --policy policy/kubernetes/ \
            --output table
```

### Policy Kubernetes: Esempio Pratico

Le policy per i manifesti Kubernetes sono tra le più comuni. Ecco una policy che enforcea limiti di risorse e proibisce l'esecuzione come root:

```rego
# policy/kubernetes/workload_security.rego
package kubernetes.security

deny[msg] {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    not container.resources.limits

    msg := sprintf(
        "Container '%s' nel Deployment '%s' deve specificare resource limits",
        [container.name, input.metadata.name]
    )
}

deny[msg] {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    container.securityContext.runAsRoot == true

    msg := sprintf(
        "Container '%s' non può eseguire come root (runAsRoot=true)",
        [container.name]
    )
}

deny[msg] {
    input.kind == "Deployment"
    not input.spec.template.spec.containers[_].securityContext.readOnlyRootFilesystem

    msg := sprintf(
        "Deployment '%s': tutti i container devono avere readOnlyRootFilesystem=true",
        [input.metadata.name]
    )
}
```

### Policy Gates nelle Pull Request

Il vero potere del Compliance-as-Code emerge quando le policy diventano **gate obbligatorie** nelle PR. Configurando i job di policy come **required status checks** nelle branch protection rules, nessun merge può avvenire se una policy viene violata. Questo crea un ciclo di feedback immediato: lo sviluppatore vede l'errore direttamente nella PR, con un messaggio che spiega quale policy è stata violata e come correggerla.

Per organizzazioni con centinaia di repository, le policy possono essere centralizzate in un repository dedicato (`org-policies`) e distribuite tramite **OPA bundles** o semplicemente referenziate come path in un reusable workflow. Ogni modifica alle policy passa attraverso lo stesso ciclo di review del codice applicativo — PR, review, test, merge — garantendo auditabilità completa.

### Test delle Policy

Le policy stesse devono essere testate. OPA fornisce un framework di test nativo:

```rego
# policy/terraform/required_tags_test.rego
package terraform.tags

test_deny_missing_tags {
    result := deny with input as {
        "resource_changes": [{
            "address": "aws_instance.web",
            "type": "aws_instance",
            "change": {
                "actions": ["create"],
                "after": {
                    "tags": {"team": "backend"}
                }
            }
        }]
    }
    count(result) > 0
}

test_allow_all_tags_present {
    result := deny with input as {
        "resource_changes": [{
            "address": "aws_instance.web",
            "type": "aws_instance",
            "change": {
                "actions": ["create"],
                "after": {
                    "tags": {
                        "team": "backend",
                        "environment": "prod",
                        "cost-center": "eng-42"
                    }
                }
            }
        }]
    }
    count(result) == 0
}
```

Eseguire i test con `opa test policy/ -v` nella CI garantisce che le policy non introducano regressioni. Trattare le policy come first-class code — con test, review, e versioning — è il principio fondamentale del Compliance-as-Code.

---

## Ottimizzazione dei Costi GitHub Actions: Pricing e Strategie 2026

### Modello di Pricing GitHub Actions 2026

A partire da gennaio 2026, GitHub ha introdotto cambiamenti significativi al pricing dei runner hosted. I **runner Linux standard** hanno ricevuto una riduzione del 39%, portando il costo da $0.008/minuto a circa $0.005/minuto. I runner **Windows** e **macOS** mantengono moltiplicatori rispettivamente di 2x e 10x rispetto al costo base Linux.

Da marzo 2026, GitHub applica un **platform charge di $0.002/minuto** anche per i runner self-hosted, per coprire i costi di orchestrazione, log storage e gestione dei job. Questo cambiamento impatta le organizzazioni che avevano migrato a self-hosted esclusivamente per motivi di costo — il risparmio rimane significativo per workload pesanti, ma il costo non è più zero.

La tabella aggiornata dei costi (Q1 2026):

| Tipo Runner | Costo/minuto | Note |
|-------------|-------------|------|
| Linux hosted (standard) | $0.005 | -39% rispetto a pre-2026 |
| Linux hosted (4-core) | $0.016 | Larger runner |
| Linux hosted (8-core) | $0.032 | Larger runner |
| Windows hosted | $0.010 | 2x Linux |
| macOS hosted (M1) | $0.050 | 10x Linux |
| Self-hosted (platform fee) | $0.002 | Nuovo da marzo 2026 |

I minuti inclusi nel piano Free (2.000/mese) e Team (3.000/mese) rimangono invariati. Per il piano Enterprise, i minuti sono negoziati nel contratto.

### Strategie di Riduzione Costi

#### 1. Caching Aggressivo delle Dipendenze

Il caching è la singola ottimizzazione con il maggiore impatto. Ogni minuto risparmiato nel download e nell'installazione di dipendenze si traduce direttamente in risparmio economico:

```yaml
- name: Cache node_modules
  uses: actions/cache@v4
  with:
    path: |
      node_modules
      ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-

- name: Cache Terraform providers
  uses: actions/cache@v4
  with:
    path: |
      ~/.terraform.d/plugin-cache
      infra/.terraform/providers
    key: tf-${{ hashFiles('infra/.terraform.lock.hcl') }}
```

Per monorepo con Turborepo, abilitare il **Remote Caching** riduce drasticamente i tempi di build incrementale — solo i pacchetti effettivamente modificati vengono ricostruiti.

#### 2. Concurrency Control

Evitare esecuzioni parallele ridondanti. Se tre commit vengono pushati in rapida successione sullo stesso branch, solo l'ultimo deve completare la CI:

```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

Questa configurazione annulla automaticamente i run precedenti ancora in corso, risparmiando minuti fatturabili su ogni push rapido durante lo sviluppo attivo.

#### 3. Path Filtering e Job Condizionali

Non eseguire l'intera pipeline quando la modifica riguarda solo la documentazione:

```yaml
on:
  push:
    paths-ignore:
      - 'docs/**'
      - '*.md'
      - '.github/ISSUE_TEMPLATE/**'
```

Combinato con `dorny/paths-filter` per job condizionali all'interno dello stesso workflow, il path filtering può ridurre i minuti consumati del 30-50% in monorepo con aree di codice indipendenti.

#### 4. Scelta Strategica dei Runner

Per job CPU-bound (compilazione, test paralleli), i **larger runner** a 4 o 8 core possono risultare più economici nonostante il costo/minuto superiore. Un build che impiega 20 minuti su un runner standard (2 core) potrebbe completarsi in 6 minuti su un 8-core:

- Standard: 20 min × $0.005 = $0.10
- 8-core: 6 min × $0.032 = $0.192

Il costo è superiore, ma il **tempo di feedback** è 3x più rapido — un valore diretto per la developer experience e le DORA metrics (lead time).

Per job I/O-bound o leggeri (lint, formatting, policy check), i runner standard restano la scelta ottimale.

#### 5. Self-Hosted Runner per Workload Pesanti

Nonostante il nuovo platform fee di $0.002/minuto, i self-hosted runner restano convenienti per:

- **Build Docker multi-stage** con layer caching locale persistente
- **Test suite pesanti** (> 30 minuti) dove il costo hosted supera quello dell'infrastruttura
- **GPU workload** (ML/AI) non disponibili su runner hosted
- **Compliance**: dati che non possono transitare su infrastruttura GitHub

Un'analisi costi-benefici trimestrale, confrontando i minuti self-hosted × $0.002 + costo infrastruttura vs. minuti hosted × tariffa, guida la decisione. Integrare questa analisi nella dashboard FinOps descritta nella sezione dedicata.

#### 6. Monitoraggio e Budget Alert

GitHub espone le metriche di consumo via API. Automatizzare alert quando il consumo supera soglie predefinite:

```yaml
# .github/workflows/cost-monitor.yml
name: Actions Usage Alert
on:
  schedule:
    - cron: '0 8 * * 1'  # Ogni lunedì mattina

jobs:
  check-usage:
    runs-on: ubuntu-latest
    steps:
      - name: Query Actions Usage
        env:
          GH_TOKEN: ${{ secrets.ORG_ADMIN_TOKEN }}
        run: |
          USAGE=$(gh api /orgs/${{ github.repository_owner }}/settings/billing/actions \
            --jq '.total_minutes_used')
          INCLUDED=$(gh api /orgs/${{ github.repository_owner }}/settings/billing/actions \
            --jq '.included_minutes')
          PERCENT=$((USAGE * 100 / INCLUDED))

          if [ "$PERCENT" -gt 80 ]; then
            echo "::warning::Consumo Actions al ${PERCENT}% del budget mensile"
            # Inviare notifica Slack/Teams
          fi
```

---

## Chaos Engineering nella Pipeline DevOps

### Perché il Chaos Engineering nella CI/CD

Il modello di maturità DevOps descritto in questa guida posiziona il **chaos engineering proattivo** al Livello 5 — il livello più alto di maturità. L'idea fondamentale: non aspettare che i guasti accadano in produzione, ma **iniettarli deliberatamente** in ambienti controllati per scoprire debolezze prima che diventino incidenti reali.

Il chaos engineering nella pipeline DevOps non si limita a testare la resilienza dell'applicazione — testa anche la resilienza della **pipeline stessa**, dei meccanismi di rollback, degli alert, e della risposta del team. È la differenza tra "crediamo che il rollback funzioni" e "abbiamo verificato che il rollback funziona sotto pressione".

### Principi Fondamentali

1. **Steady-State Hypothesis**: Definire il comportamento normale del sistema tramite metriche osservabili (latenza p99, error rate, throughput). Ogni esperimento inizia con un'ipotesi: "il sistema mantiene latenza p99 < 200ms anche quando il database replica primaria diventa irraggiungibile".

2. **Blast Radius Controllato**: Iniziare sempre con l'ambito più piccolo possibile. In staging, non in produzione. Un singolo pod, non l'intero cluster. Un 1% del traffico, non il 100%.

3. **Automazione e Ripetibilità**: Gli esperimenti devono essere codificati e versionati — non eseguiti manualmente. Questo consente di ripeterli ad ogni release e di includerli nella CI/CD.

4. **Rollback Automatico**: L'esperimento deve terminare automaticamente se le metriche superano soglie di sicurezza predefinite. Nessun esperimento chaos deve poter causare un outage non controllato.

### Litmus e Chaos Mesh con GitHub Actions

I due framework open-source più maturi per chaos engineering su Kubernetes sono **Litmus** (ora parte della CNCF) e **Chaos Mesh** (creato da PingCAP, anch'esso CNCF). Entrambi si integrano con GitHub Actions per automatizzare gli esperimenti.

```yaml
# .github/workflows/chaos-experiment.yml
name: Chaos Engineering - Post-Deploy Validation
on:
  workflow_run:
    workflows: ["Deploy to Staging"]
    types: [completed]
    branches: [main]

jobs:
  chaos-pod-kill:
    name: Pod Failure Resilience
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/setup-kubectl@v4
        with:
          version: 'v1.30.0'

      - name: Setup kubeconfig
        run: |
          echo "${{ secrets.STAGING_KUBECONFIG }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig

      - name: Verify Steady State (pre-chaos)
        run: |
          # Verificare che l'applicazione risponda normalmente
          LATENCY=$(curl -s -o /dev/null -w "%{time_total}" \
            https://staging.example.com/healthz)
          ERROR_RATE=$(kubectl get --raw \
            "/apis/custom.metrics.k8s.io/v1beta1/namespaces/app/pods/*/error_rate" \
            | jq '.items[0].value // "0"' -r)

          echo "Pre-chaos latency: ${LATENCY}s"
          echo "Pre-chaos error rate: ${ERROR_RATE}"

          # Salvare come baseline
          echo "BASELINE_LATENCY=${LATENCY}" >> "$GITHUB_ENV"

      - name: Apply Chaos Experiment
        run: |
          kubectl apply -f - <<'CHAOS_EOF'
          apiVersion: chaos-mesh.org/v1alpha1
          kind: PodChaos
          metadata:
            name: pod-kill-api
            namespace: chaos-testing
          spec:
            action: pod-kill
            mode: one
            selector:
              namespaces:
                - app
              labelSelectors:
                app: api-server
            duration: "60s"
            scheduler:
              cron: "@every 30s"
          CHAOS_EOF

      - name: Wait and Monitor
        run: |
          echo "Esperimento chaos in corso (120s)..."
          sleep 120

      - name: Verify Steady State (post-chaos)
        run: |
          LATENCY=$(curl -s -o /dev/null -w "%{time_total}" \
            https://staging.example.com/healthz)

          echo "Post-chaos latency: ${LATENCY}s"

          # Verificare che il sistema sia tornato allo steady state
          THRESHOLD="2.0"
          if (( $(echo "$LATENCY > $THRESHOLD" | bc -l) )); then
            echo "::error::Latenza post-chaos ${LATENCY}s supera soglia ${THRESHOLD}s"
            exit 1
          fi

          echo "Sistema recuperato entro i limiti accettabili"

      - name: Cleanup Chaos Experiment
        if: always()
        run: |
          kubectl delete podchaos pod-kill-api \
            -n chaos-testing --ignore-not-found

      - name: Report Results
        if: always()
        run: |
          echo "## Risultati Chaos Experiment" >> "$GITHUB_STEP_SUMMARY"
          echo "| Metrica | Pre-Chaos | Post-Chaos | Soglia |" >> "$GITHUB_STEP_SUMMARY"
          echo "|---------|-----------|------------|--------|" >> "$GITHUB_STEP_SUMMARY"
          echo "| Latenza | ${BASELINE_LATENCY}s | ${LATENCY}s | 2.0s |" >> "$GITHUB_STEP_SUMMARY"
```

### GameDay Automation

Il **GameDay** è un esercizio strutturato in cui il team simula scenari di guasto per validare runbook, alert e procedure di risposta. Tradizionalmente manuale, può essere parzialmente automatizzato con GitHub Actions:

```yaml
# .github/workflows/gameday.yml
name: GameDay Automation
on:
  workflow_dispatch:
    inputs:
      scenario:
        description: 'Scenario da simulare'
        required: true
        type: choice
        options:
          - database-failover
          - cache-invalidation
          - dns-failure
          - high-cpu-load
      environment:
        description: 'Ambiente target'
        required: true
        type: choice
        options:
          - staging
          - gameday-cluster
      duration_minutes:
        description: 'Durata esperimento (minuti)'
        required: true
        default: '5'
        type: string

jobs:
  gameday:
    name: GameDay - ${{ inputs.scenario }}
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4

      - name: Pre-flight Checks
        run: |
          echo "Scenario: ${{ inputs.scenario }}"
          echo "Ambiente: ${{ inputs.environment }}"
          echo "Durata: ${{ inputs.duration_minutes }} minuti"

          # Verificare che non siamo in produzione
          if [ "${{ inputs.environment }}" == "production" ]; then
            echo "::error::GameDay non consentito in produzione"
            exit 1
          fi

      - name: Execute Scenario
        run: |
          chmod +x scripts/gameday/${{ inputs.scenario }}.sh
          timeout $((60 * ${{ inputs.duration_minutes }})) \
            scripts/gameday/${{ inputs.scenario }}.sh \
            || echo "Esperimento terminato per timeout"

      - name: Collect Observations
        if: always()
        run: |
          echo "## GameDay Report" >> "$GITHUB_STEP_SUMMARY"
          echo "**Scenario:** ${{ inputs.scenario }}" >> "$GITHUB_STEP_SUMMARY"
          echo "**Durata:** ${{ inputs.duration_minutes }} min" >> "$GITHUB_STEP_SUMMARY"
          echo "" >> "$GITHUB_STEP_SUMMARY"
          echo "### Checklist Post-GameDay" >> "$GITHUB_STEP_SUMMARY"
          echo "- [ ] Alert ricevuti entro SLO (< 5 min)" >> "$GITHUB_STEP_SUMMARY"
          echo "- [ ] Runbook seguito correttamente" >> "$GITHUB_STEP_SUMMARY"
          echo "- [ ] Recovery completato entro MTTR target" >> "$GITHUB_STEP_SUMMARY"
          echo "- [ ] Nessun impatto su ambienti non-target" >> "$GITHUB_STEP_SUMMARY"
          echo "- [ ] Action items documentati" >> "$GITHUB_STEP_SUMMARY"
```

### Chaos Engineering nel Modello di Maturità

Il chaos engineering si integra progressivamente nel modello di maturità DevOps:

- **Livello 3**: Primi esperimenti manuali in staging. Il team esegue GameDay trimestrali con scenari predefiniti. Focus su validazione dei meccanismi di rollback e degli alert.

- **Livello 4**: Esperimenti automatizzati post-deploy in staging. Ogni release passa attraverso un set base di test di resilienza (pod kill, network delay, resource exhaustion). I risultati sono gate per la promozione a produzione.

- **Livello 5**: Chaos engineering proattivo in produzione con blast radius controllato. Esperimenti continui su un sottoinsieme del traffico reale. Il sistema dimostra **antifragilità** — non solo sopravvive ai guasti, ma li usa come segnale per migliorare automaticamente (auto-scaling, circuit breaking, failover).

La progressione richiede maturità nelle aree prerequisite: osservabilità completa (per misurare lo steady state), rollback affidabile (per contenere il blast radius), e cultura blameless (per analizzare i risultati senza cercare colpevoli).

---

## Riepilogo

Questa guida ha costruito una pipeline DevOps completa usando esclusivamente strumenti GitHub e ha esplorato le pratiche DevOps avanzate del 2025-2026:

1. **Repository**: Monorepo con npm workspaces e Turborepo per build incrementali
2. **CI**: Lint, type-check, test unitari (paralleli per app), test di integrazione con servizi Docker, build immagini Docker multi-stage
3. **CD**: Deploy automatico in staging ad ogni merge su main, deploy in produzione tramite tag con approvazione manuale, rollback automatico in caso di fallimento
4. **Infrastructure**: Terraform per il provisioning di VPC, EKS, RDS; Kustomize per i manifesti Kubernetes con overlay per ambiente
5. **Sicurezza**: CodeQL per analisi statica, Trivy per scansione container, audit delle dipendenze, detection dei segreti
6. **Dipendenze**: Dependabot per aggiornamenti automatici di npm, Docker, GitHub Actions e Terraform
7. **Rilasci**: Automazione completa con tag semantici, changelog generato automaticamente, GitHub Release con note
8. **Documentazione**: MkDocs Material deployato su GitHub Pages ad ogni modifica
9. **Incident Response**: Template strutturato per incident report con timeline e action items
10. **GitOps**: Riconciliazione continua con Argo CD e Flux CD, drift detection, modello pull-based per deploy Kubernetes
11. **Platform Engineering**: Internal Developer Platform con Backstage, catalogo servizi, software templates, scorecard qualità
12. **DORA Metrics**: Le quattro metriche fondamentali più Rework Rate (quinta metrica 2025), framework SPACE e DX Core 4
13. **Developer Experience**: Ottimizzazione feedback loop CI (< 10 minuti), riduzione cognitive load, flow state
14. **Deploy Avanzato**: Blue-green, canary con monitoraggio metriche, progressive delivery con feature flags
15. **Supply Chain Security**: SLSA Build Level 3 con reusable workflows, SBOM attestation, verifica provenance con Sigstore
16. **Osservabilità**: Stack completo OpenTelemetry + Prometheus + Grafana + Loki + Tempo, dashboard DevOps
17. **FinOps**: Cost gates nelle PR con Infracost, checklist right-sizing, preview environments con TTL
18. **Workflow Riutilizzabili**: Reusable workflows e composite actions per DRY nella CI/CD organizzativa
19. **Environments**: Protection rules con required reviewers, wait timers, branch restrictions, custom deployment rules
20. **AI DevOps**: Copilot Agent Mode, automazione code review, rischi e best practice dell'AI nella pipeline
21. **Anti-Pattern**: I 12 anti-pattern più comuni e il modello di maturità DevOps a 5 livelli
22. **OIDC**: Autenticazione cloud senza segreti statici, trust policy, least privilege
23. **Compliance-as-Code**: Policy-as-Code con OPA e Rego, Conftest per validazione Terraform e Kubernetes, policy gates obbligatorie nelle PR
24. **Costi Actions 2026**: Pricing aggiornato con riduzione 39% hosted runner, platform fee self-hosted $0.002/min, strategie di caching, concurrency control, path filtering
25. **Chaos Engineering**: Esperimenti automatizzati con Litmus e Chaos Mesh, steady-state hypothesis, GameDay automation, integrazione nel modello di maturità

Ogni pezzo di questa pipeline è indipendente e può essere adottato separatamente. Non è necessario implementare tutto in una volta. Il modello di maturità DevOps fornisce una roadmap: partire dal Livello 1 (CI basico con lint e test), avanzare al Livello 2 (CI/CD completo con environments), poi al Livello 3 (GitOps e piattaforma), fino al Livello 4 (progressive delivery, AI, FinOps). La chiave è l'iterazione continua: la pipeline DevOps stessa è un prodotto che evolve con il progetto.

---

## Esercizi Pratici

### Esercizio 1: Pipeline CI Completa per Monorepo

Costruisci una CI per un monorepo con due app e una libreria condivisa:

```bash
# Struttura:
# apps/web/        → React frontend
# apps/api/        → Node.js backend
# libs/shared/     → Libreria condivisa (types, utils)
# infra/           → Terraform

# 1. Configurare npm workspaces o Turborepo
# 2. Creare .github/workflows/ci.yml:
#    - Usare dorny/paths-filter per rilevare le aree modificate
#    - Job condizionali:
#      lint-web: solo se apps/web/ o libs/shared/ modificati
#      lint-api: solo se apps/api/ o libs/shared/ modificati
#      test-web: dipende da lint-web
#      test-api: dipende da lint-api
#      build: dipende da test-web + test-api
# 3. Caching condiviso per node_modules
# 4. Artifacts: upload dist/ per ogni app
# 5. Matrice per test cross-versione su Node 18 e 20

# Verifica:
# - Modifica solo apps/web/ → solo job web eseguiti
# - Modifica libs/shared/ → tutti i job eseguiti
# - Tempo totale CI < 10 minuti
```

**Criteri di successo:** CI condizionale funzionante, caching efficace, artifacts pronti per il deploy.

### Esercizio 2: CD Multi-Ambiente con Rollback

Implementa un deployment pipeline con deploy automatico e rollback:

```yaml
# 1. Creare tre GitHub Environments: staging, canary, production
# 2. Workflow CD:
#    - Trigger: merge su main → deploy staging (auto)
#    - Test di integrazione su staging
#    - Se test passano → deploy canary (10% traffico)
#    - Monitorare metriche per 15 minuti
#    - Se metriche OK → deploy production (con approvazione manuale)
# 3. Rollback automatico:
#    - Health check post-deploy (curl /health con retry 30x)
#    - Se fallisce → redeploy della versione precedente
#    - Notifica Slack con dettagli del rollback
# 4. Configurare environment secrets separati:
#    - DATABASE_URL diverso per staging/canary/production
#    - AWS_ROLE_ARN diverso per ambiente
# 5. Usare OIDC per autenticazione AWS (no secrets statici)

# Verifica:
# - Deploy staging automatico dopo merge su main
# - Deploy production bloccato senza approvazione
# - Rollback funzionante (introdurre un bug intenzionale)
```

### Esercizio 3: Infrastructure as Code con Terraform

Integra Terraform nella pipeline GitHub Actions:

```yaml
# 1. Struttura Terraform:
#    infra/
#    ├── main.tf
#    ├── variables.tf
#    ├── environments/
#    │   ├── staging.tfvars
#    │   └── production.tfvars
#    └── modules/
#        ├── vpc/
#        ├── eks/
#        └── rds/
# 2. Workflow terraform.yml:
#    - Trigger: push su main con paths: [infra/**]
#    - Job plan: terraform init → validate → plan
#    - Salvare plan come artifact
#    - Commentare il piano sulla PR (con hashicorp/setup-terraform)
#    - Job apply: solo su merge in main, usa il plan salvato
#    - Environment: staging-infra con protection rules
# 3. State management:
#    - Backend S3 con DynamoDB lock
#    - State separato per staging e production
# 4. Drift detection:
#    - Cron settimanale: terraform plan -detailed-exitcode
#    - Alert se drift rilevato

# Verifica:
# - PR mostra il plan come commento
# - Apply usa il plan esatto della PR (no re-plan)
# - Drift detection rileva modifiche manuali
```

### Esercizio 4: Security Pipeline Integrata

Configura un security scanning end-to-end nella pipeline:

```yaml
# 1. Dependency scanning:
#    - Dependabot configurato per npm, Docker, GitHub Actions, Terraform
#    - Dependabot auto-merge per patch updates con CI verde
# 2. Static analysis:
#    - CodeQL per JavaScript e TypeScript
#    - Queries: security-extended + quality
# 3. Container scanning:
#    - Trivy scan dell'immagine Docker
#    - Risultati uploadati come SARIF
# 4. Secret scanning:
#    - Gitleaks in pre-commit hook e in CI
#    - Push protection abilitato
# 5. License compliance:
#    - license-checker per dipendenze npm
#    - Whitelist: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC
# 6. SBOM generation:
#    - Generare Software Bill of Materials con ogni release
#    - Attestazione con sigstore

# Verifica:
# - Introdurre una dipendenza con vulnerabilità → Dependabot crea PR
# - Committare un API key finto → Gitleaks blocca il push
# - Tutte le scansioni appaiono nella tab Security
```

### Esercizio 5: Release Automation e Documentazione

Automatizza il processo completo di rilascio:

```yaml
# 1. Configurare semantic-release:
#    - Analisi commit per determinare version bump
#    - Generazione CHANGELOG.md
#    - Creazione tag Git e GitHub Release
#    - Pubblicazione immagine Docker con tag versione
# 2. Documentazione con MkDocs Material:
#    - Struttura: docs/ con mkdocs.yml
#    - Deploy su GitHub Pages ad ogni merge su main
#    - Versioning della documentazione (mike)
# 3. Status badges nel README:
#    - CI status
#    - Coverage
#    - Latest release
#    - License
# 4. Incident response template:
#    - .github/ISSUE_TEMPLATE/incident.yml con form strutturato
#    - Timeline, impact, root cause, action items
# 5. Release notes automation:
#    - Raggruppare per tipo: Features, Bug Fixes, Breaking Changes
#    - Linkare automaticamente PR e issue

# Verifica:
# - Commit "feat: new feature" → minor bump, changelog aggiornato
# - Docs aggiornati e visibili su GitHub Pages
# - Release note complete e leggibili
```

---

## Letture Consigliate

- **Libro**: "Accelerate" di Nicole Forsgren, Jez Humble, Gene Kim, IT Revolution Press, 2018 — metriche DevOps e DORA
- **Libro**: "The Phoenix Project" di Gene Kim, Kevin Behr, George Spafford, IT Revolution Press, 2018 — narrazione DevOps
- **Libro**: "Continuous Delivery" di Jez Humble e David Farley, Addison-Wesley, 2010 — principi fondamentali di pipeline
- **DORA Research**: "State of DevOps Reports" — https://dora.dev/research/ (consultato: 2026-05-24)
- **GitHub Blog**: "DevOps with GitHub" — https://github.blog/enterprise-software/ci-cd/githubs-engineering-team-moved-to-codespaces/ (consultato: 2026-05-24)
- **Terraform Documentation**: "GitHub Actions integration" — https://developer.hashicorp.com/terraform/tutorials/automation/github-actions (consultato: 2026-05-24)
- **MkDocs Material**: https://squidfunk.github.io/mkdocs-material/ (consultato: 2026-05-24)

---

## Collegamenti Incrociati

| Modulo | Collegamento | Relazione |
|--------|-------------|-----------|
| 19 | [19-github-actions-ci-cd-ricette.md](19-github-actions-ci-cd-ricette.md) | Ricette CI/CD — building block della pipeline DevOps |
| 18 | [18-github-actions-avanzate.md](18-github-actions-avanzate.md) | Actions avanzate — matrix, cache, environments usati nella pipeline |
| 21 | [21-github-actions-self-hosted-runners.md](21-github-actions-self-hosted-runners.md) | Self-hosted runners — infrastruttura runner per la pipeline |
| 16 | [16-github-security-scanning.md](16-github-security-scanning.md) | Security scanning — Dependabot, CodeQL, secret scanning |
| 14 | [14-github-packages-pages-releases.md](14-github-packages-pages-releases.md) | Packages e Pages — distribuzione artifact e documentazione |
| 17 | [17-github-actions-workflow-sintassi.md](17-github-actions-workflow-sintassi.md) | Sintassi workflow — base per scrivere le pipeline |
| 26 | [26-oidc-cloud-credentials.md](26-oidc-cloud-credentials.md) | OIDC — credenziali cloud per deploy sicuri |
| 27 | [27-supply-chain-attestation-slsa.md](27-supply-chain-attestation-slsa.md) | Supply chain — SBOM e attestation nelle release |
| 28 | [28-codeql-advanced-security.md](28-codeql-advanced-security.md) | CodeQL — analisi statica avanzata nella CI |
| 20 | [20-git-workflow-team-guida-completa.md](20-git-workflow-team-guida-completa.md) | Workflow team — convenzioni di branching e PR per il team DevOps |

---

## Glossario Locale

| Termine | Definizione |
|---------|------------|
| **Canary deploy** | Strategia di deployment che instrada una percentuale ridotta del traffico alla nuova versione per validazione |
| **Chaos Engineering** | Disciplina che inietta guasti controllati nei sistemi per scoprire debolezze prima che causino incidenti reali in produzione |
| **Chaos Mesh** | Framework CNCF per chaos engineering su Kubernetes, sviluppato da PingCAP, con supporto per pod kill, network fault, I/O chaos |
| **Conftest** | Tool che applica policy OPA/Rego a file di configurazione strutturati (Terraform plan, K8s manifest, Dockerfile) nella CI |
| **CHANGELOG** | File che documenta le modifiche di ogni versione, generabile automaticamente dai commit message convenzionali |
| **CI/CD pipeline** | Sequenza automatizzata di step: build, test, analisi, deploy che trasforma il codice in software rilasciabile |
| **Dependabot** | Bot GitHub che crea automaticamente PR per aggiornare dipendenze con vulnerabilità note |
| **DORA metrics** | Quattro metriche chiave DevOps: deployment frequency, lead time, change failure rate, time to recovery |
| **GameDay** | Esercizio strutturato in cui il team simula scenari di guasto per validare runbook, alert e procedure di incident response |
| **GitHub Pages** | Servizio di hosting statico di GitHub, usato per documentazione del progetto (MkDocs, Jekyll) |
| **Infrastructure as Code (IaC)** | Pratica di gestire infrastruttura attraverso file di configurazione versionati (Terraform, Pulumi, CloudFormation) |
| **Litmus** | Framework CNCF per chaos engineering, supporta esperimenti dichiarativi su Kubernetes con workflow ChaosHub predefiniti |
| **Monorepo** | Repository singolo che contiene codice di più applicazioni e librerie, gestito con workspace e build incrementali |
| **OPA (Open Policy Agent)** | Motore di policy general-purpose della CNCF che separa le decisioni di policy dal codice applicativo usando il linguaggio Rego |
| **Policy-as-Code** | Pratica di definire regole di governance, sicurezza e compliance come codice versionato, testabile e applicabile automaticamente |
| **Rego** | Linguaggio dichiarativo di OPA per scrivere policy; interroga strutture dati JSON/YAML con un modello basato su regole |
| **Rollback** | Ripristino automatico della versione precedente quando il deploy della nuova versione fallisce i health check |
| **SBOM** | Software Bill of Materials — inventario completo delle dipendenze di un software, richiesto per compliance |
| **semantic-release** | Tool che automatizza versioning e release basandosi sulla convenzione dei commit message |
| **Steady-State Hypothesis** | Nel chaos engineering, definizione del comportamento normale del sistema tramite metriche osservabili, usata come baseline per validare la resilienza |
| **Status badge** | Immagine SVG nel README che mostra lo stato corrente di CI, coverage, versione o licenza |
| **Terraform plan** | Anteprima delle modifiche infrastrutturali che Terraform applicherà, salvabile come artifact per apply deterministico |
| **Turborepo** | Build system per monorepo JavaScript/TypeScript con caching incrementale e esecuzione parallela |
