---
corso: "Automazioni e Flussi di Lavoro"
fase: "6 — Governance"
modulo: 25
titolo: "Multi-Environment Promotion — Dev → Staging → Prod"
versione: "GitHub Actions, GitLab CI, Docker, Kubernetes"
livello: "proficient"
prerequisiti: ["Modulo 07 — Logging e Monitoring", "Modulo 18 — Workflow Versioning e Rollback"]
obiettivi:
  - "Progettare ambienti separati (dev/staging/prod) con secret distinti e isolamento delle risorse"
  - "Costruire promotion pipeline automatizzata con gate di approvazione tra ambienti"
  - "Implementare smoke test specifici per ogni environment con validazione post-deploy"
  - "Configurare rollback per singolo environment senza impatto sugli altri ambienti"
  - "Gestire configuration drift e environment parity con IaC e secret management centralizzato"
tag: [multi-environment, promotion, dev-staging-prod, ci-cd, smoke-test, rollback, iac, secret-management]
---

# Multi-Environment Promotion — Dev → Staging → Prod

> **Obiettivi di apprendimento**
> 1. Progettare ambienti separati (dev/staging/prod) con secret distinti e isolamento delle risorse
> 2. Costruire promotion pipeline automatizzata con gate di approvazione tra ambienti
> 3. Implementare smoke test specifici per ogni environment con validazione post-deploy
> 4. Configurare rollback per singolo environment senza impatto sugli altri ambienti
> 5. Gestire configuration drift e environment parity con IaC e secret management centralizzato

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 5 — Governance · Modulo 25 (nuovo)
> **Prerequisiti:** Moduli 07, 18.
> **Obiettivi:** ambienti separati con secret distinti; promotion pipeline; smoke test per env; rollback per env.
> **Tempo:** lettura 90 min · lab 360 min
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-24

---

## Indice

1. [Idee guida](#idee-guida)
2. [Parte teorica — Architettura multi-environment](#parte-teorica--architettura-multi-environment)
3. [Topologia degli ambienti](#topologia-degli-ambienti)
4. [Strategie di promotion](#strategie-di-promotion)
5. [Gestione configurazione per ambiente](#gestione-configurazione-per-ambiente)
6. [Parita degli ambienti e drift detection](#parita-degli-ambienti-e-drift-detection)
7. [GitOps per workflow promotion](#gitops-per-workflow-promotion)
8. [Pipeline CI/CD per workflow di automazione](#pipeline-cicd-per-workflow-di-automazione)
9. [Testing workflow prima della promotion](#testing-workflow-prima-della-promotion)
10. [Strategie di rollback](#strategie-di-rollback)
11. [Pattern di isolamento ambienti](#pattern-di-isolamento-ambienti)
12. [Blue-green deployment per workflow](#blue-green-deployment-per-workflow)
13. [Feature flag nelle automazioni](#feature-flag-nelle-automazioni)
14. [Routing environment-specific](#routing-environment-specific)
15. [Infrastructure-as-Code per piattaforme workflow](#infrastructure-as-code-per-piattaforme-workflow)
16. [Esercizi](#esercizi)
17. [Troubleshooting — 20 problemi comuni](#troubleshooting--20-problemi-comuni)
18. [FAQ — 20 domande e risposte](#faq--20-domande-e-risposte)
19. [Auto-valutazione](#auto-valutazione)
20. [Letture primarie consigliate](#letture-primarie-consigliate)
21. [Collegamenti incrociati](#collegamenti-incrociati)
22. [Glossario locale](#glossario-locale)

---

## Idee guida

1. **3 env minimi: dev, staging, prod.** Con dati realistici (sanitized) in staging.
2. **Secret per env, non condivisi.** Stripe test key in dev/staging, live key in prod.
3. **Promotion = git merge + auto-deploy.** Merge `dev` → `staging` triggera deploy staging; merge `staging` → `prod` triggera prod.
4. **Smoke test per env post-deploy.** Validare basic functionality automaticamente.
5. **Rollback per env: dropdown nella pipeline.** "Rollback prod alla versione precedente" deve essere 1 click.
6. **Parita come vincolo architetturale.** Staging deve rispecchiare prod nella topologia, nelle versioni runtime e nella struttura dei dati — altrimenti il testing pre-promotion e teatro.
7. **Promozione unidirezionale e immutabile.** Un artefatto promosso non viene ricompilato; lo stesso binario/container viaggia dev → staging → prod.

---

## Parte teorica — Architettura multi-environment

### Perche servono piu ambienti

Un singolo ambiente per sviluppo e produzione e una ricetta per incidenti. Ogni modifica al codice o alla configurazione viene esposta direttamente agli utenti finali senza filtro. L'architettura multi-environment introduce strati di verifica progressiva:

| Fase | Scopo | Chi lo usa |
|------|-------|------------|
| Sviluppo | Iterazione rapida, debug, prototipazione | Sviluppatori |
| Integrazione/QA | Test automatizzati, verifica integrazioni | CI/CD, QA team |
| Staging | Replica prod, test manuali, UAT | QA, PM, stakeholder |
| Produzione | Traffico reale, utenti finali | Tutti |

Il numero esatto di ambienti dipende dalla maturita del team e dalla criticita del sistema. Per workflow di automazione, tre ambienti (dev/staging/prod) rappresentano il minimo pratico; organizzazioni mature ne aggiungono un quarto (integration/QA) o un quinto (canary/shadow).

### Principi architetturali fondamentali

**Principio 1 — Isolamento totale.** Ogni ambiente possiede risorse dedicate: database, code segreti, endpoint API, credenziali di servizi esterni. Zero condivisione di stato fra ambienti.

**Principio 2 — Artefatto immutabile.** Il container Docker, il pacchetto ZIP o il bundle workflow che passa da dev a staging a prod e identico byte-per-byte. Cio che cambia e solo la configurazione iniettata dall'ambiente.

**Principio 3 — Configurazione esterna.** Nessun valore hard-coded nel workflow. Ogni parametro dipendente dall'ambiente (URL, credenziali, timeout, feature flag) e iniettato tramite variabili d'ambiente, secret manager o config server.

**Principio 4 — Gate di qualita.** La promozione da un ambiente al successivo richiede il superamento di criteri oggettivi (test verdi, soglie di performance, approvazione umana).

**Principio 5 — Tracciabilita.** Ogni promozione e registrata: chi ha approvato, quando, quale versione, quale diff di configurazione.

### Matrice di responsabilita ambienti

```
┌─────────────────────────────────────────────────────────────────┐
│                   MATRICE RESPONSABILITA                        │
├──────────────┬─────────┬──────────┬──────────┬─────────────────┤
│ Aspetto      │   Dev   │ Staging  │   Prod   │ Chi decide      │
├──────────────┼─────────┼──────────┼──────────┼─────────────────┤
│ Deploy       │ Auto    │ Auto+Gate│ Gate     │ Pipeline CI/CD  │
│ Dati         │ Mock/   │ Sanitized│ Reali    │ DBA + Compliance│
│              │ Seed    │ da prod  │          │                 │
│ Secret       │ Test    │ Test     │ Live     │ Security team   │
│ Monitoring   │ Base    │ Medio    │ Completo │ SRE / DevOps    │
│ Accesso      │ Dev team│ Dev+QA   │ Ops only │ Security team   │
│ SLA          │ Nessuno │ Best-eff │ 99.9%+   │ Management      │
│ Backup       │ No      │ Giornali │ Continui │ DBA             │
│ Scaling      │ Minimo  │ Ridotto  │ Full     │ Infra team      │
└──────────────┴─────────┴──────────┴──────────┴─────────────────┘
```

---

## Topologia degli ambienti

### Architettura a tre ambienti — vista d'insieme

```
                    ┌─────────────────┐
                    │   Sviluppatore  │
                    └────────┬────────┘
                             │ git push feature/*
                             ▼
                    ┌─────────────────┐
                    │    Dev Env      │
                    │  ┌───────────┐  │
                    │  │ Workflow   │  │
                    │  │ Engine    │  │
                    │  ├───────────┤  │
                    │  │ DB (seed) │  │
                    │  ├───────────┤  │
                    │  │ Test Keys │  │
                    │  └───────────┘  │
                    └────────┬────────┘
                             │ merge → staging + CI green
                             ▼
                    ┌─────────────────┐
                    │  Staging Env    │
                    │  ┌───────────┐  │
                    │  │ Workflow   │  │
                    │  │ Engine    │  │
                    │  ├───────────┤  │
                    │  │ DB (sani- │  │
                    │  │ tized)    │  │
                    │  ├───────────┤  │
                    │  │ Test Keys │  │
                    │  └───────────┘  │
                    └────────┬────────┘
                             │ merge → main + approval gate
                             ▼
                    ┌─────────────────┐
                    │   Prod Env      │
                    │  ┌───────────┐  │
                    │  │ Workflow   │  │
                    │  │ Engine    │  │
                    │  ├───────────┤  │
                    │  │ DB (live) │  │
                    │  ├───────────┤  │
                    │  │ Live Keys │  │
                    │  └───────────┘  │
                    └─────────────────┘
```

### Topologia con namespace Kubernetes

Per team che usano Kubernetes, l'isolamento via namespace e il pattern piu comune:

```yaml
# k8s-namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: workflows-dev
  labels:
    env: dev
    team: automation
---
apiVersion: v1
kind: Namespace
metadata:
  name: workflows-staging
  labels:
    env: staging
    team: automation
---
apiVersion: v1
kind: Namespace
metadata:
  name: workflows-prod
  labels:
    env: prod
    team: automation
```

Con network policy per impedire comunicazione cross-namespace:

```yaml
# network-policy-isolation.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-cross-env
  namespace: workflows-prod
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector: {}
  egress:
    - to:
        - podSelector: {}
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - protocol: UDP
          port: 53
```

### Topologia con account cloud separati

Per isolamento massimo, ogni ambiente risiede in un account AWS / progetto GCP / sottoscrizione Azure dedicato:

```
┌────────────────────────────────────────────────┐
│             Organization Root                   │
├───────────┬───────────────┬────────────────────┤
│ Account   │ Account       │ Account            │
│ DEV       │ STAGING       │ PROD               │
│           │               │                    │
│ VPC-dev   │ VPC-staging   │ VPC-prod           │
│ IAM-dev   │ IAM-staging   │ IAM-prod           │
│ KMS-dev   │ KMS-staging   │ KMS-prod           │
│ Secrets-  │ Secrets-      │ Secrets-           │
│ Manager-  │ Manager-      │ Manager-           │
│ dev       │ staging       │ prod               │
└───────────┴───────────────┴────────────────────┘
```

Vantaggi: blast radius limitato (un errore in dev non puo toccare prod), fatturazione separata, IAM indipendente. Svantaggio: complessita operativa maggiore.

---

## Strategie di promotion

### Pipeline tipica

```
git push dev branch
  → CI lint + unit test
  → deploy DEV env
  → smoke test DEV
git merge dev → staging
  → CI integration test (dati staging)
  → deploy STAGING
  → smoke test STAGING + manual QA
git merge staging → prod (require approval)
  → deploy PROD with canary 10%
  → monitor 30 min
  → rollout to 100% or rollback
```

### Promotion manuale con gate di approvazione

La strategia piu conservativa: ogni passaggio richiede un'approvazione esplicita da parte di un umano autorizzato. Appropriata per workflow critici (pagamenti, compliance, dati sanitari).

Implementazione in GitHub Actions:

```yaml
# .github/workflows/promote-staging-to-prod.yml
name: Promote Staging to Production

on:
  workflow_dispatch:
    inputs:
      version:
        description: "Versione da promuovere (tag)"
        required: true
        type: string
      reason:
        description: "Motivo della promozione"
        required: true
        type: string

jobs:
  approval-gate:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://workflows.example.com
    steps:
      - name: Log promotion request
        run: |
          echo "Richiesta promozione versione ${{ inputs.version }}"
          echo "Motivo: ${{ inputs.reason }}"
          echo "Richiedente: ${{ github.actor }}"
          echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

  pre-checks:
    needs: approval-gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.version }}

      - name: Verifica che staging test siano passati
        run: |
          STAGING_STATUS=$(gh run list \
            --workflow=deploy-staging.yml \
            --branch=staging \
            --limit=1 \
            --json conclusion \
            --jq '.[0].conclusion')
          if [ "$STAGING_STATUS" != "success" ]; then
            echo "ERRORE: l'ultimo deploy staging non e andato a buon fine"
            exit 1
          fi

      - name: Verifica versione artefatto
        run: |
          EXPECTED_SHA=$(git rev-parse HEAD)
          STAGING_SHA=$(curl -s https://staging.example.com/health | jq -r '.version')
          if [ "$EXPECTED_SHA" != "$STAGING_SHA" ]; then
            echo "ERRORE: versione staging ($STAGING_SHA) != versione richiesta ($EXPECTED_SHA)"
            exit 1
          fi

  deploy-prod:
    needs: pre-checks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.version }}

      - name: Deploy to production
        env:
          DEPLOY_TOKEN: ${{ secrets.PROD_DEPLOY_TOKEN }}
        run: |
          ./scripts/deploy.sh \
            --env prod \
            --version ${{ inputs.version }} \
            --canary-percent 10
```

### Promotion automatica condizionale

La promozione avviene automaticamente se tutti i criteri sono soddisfatti. Nessuna approvazione umana, ma gate oggettivi rigorosi.

```yaml
# .github/workflows/auto-promote.yml
name: Auto-promote on green pipeline

on:
  workflow_run:
    workflows: ["Deploy Staging"]
    types: [completed]

jobs:
  evaluate-promotion:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    steps:
      - name: Controlla test coverage
        id: coverage
        run: |
          COVERAGE=$(curl -s https://staging-api.example.com/metrics/coverage)
          echo "coverage=$COVERAGE" >> "$GITHUB_OUTPUT"
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "Coverage $COVERAGE% < 80% — promozione bloccata"
            exit 1
          fi

      - name: Controlla error rate staging (ultimi 30 min)
        id: error_rate
        run: |
          ERROR_RATE=$(curl -s \
            'https://prometheus.example.com/api/v1/query?query=rate(workflow_errors_total{env="staging"}[30m])' \
            | jq -r '.data.result[0].value[1]')
          echo "error_rate=$ERROR_RATE" >> "$GITHUB_OUTPUT"
          if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
            echo "Error rate $ERROR_RATE > 1% — promozione bloccata"
            exit 1
          fi

      - name: Controlla latenza p99
        run: |
          P99=$(curl -s \
            'https://prometheus.example.com/api/v1/query?query=histogram_quantile(0.99,rate(workflow_duration_seconds_bucket{env="staging"}[30m]))' \
            | jq -r '.data.result[0].value[1]')
          if (( $(echo "$P99 > 5.0" | bc -l) )); then
            echo "Latenza p99 ${P99}s > 5s — promozione bloccata"
            exit 1
          fi

      - name: Promuovi a produzione
        run: |
          gh workflow run deploy-production.yml \
            --field version="${{ github.event.workflow_run.head_sha }}" \
            --field reason="auto-promotion: coverage=${{ steps.coverage.outputs.coverage }}%, error_rate=${{ steps.error_rate.outputs.error_rate }}"
```

### Promotion canary progressiva

Il rilascio canary espone la nuova versione a una percentuale crescente di traffico. Se le metriche degradano, il rollback e automatico.

```
Fase 1:  canary 5%  → osserva 15 min → metriche OK?
Fase 2:  canary 25% → osserva 15 min → metriche OK?
Fase 3:  canary 50% → osserva 15 min → metriche OK?
Fase 4:  rollout 100%

Se in qualsiasi fase error_rate > soglia:
  → rollback immediato a versione precedente
  → alert al team
  → incident report automatico
```

Implementazione con Argo Rollouts:

```yaml
# argo-rollout-canary.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: workflow-engine
  namespace: workflows-prod
spec:
  replicas: 10
  strategy:
    canary:
      steps:
        - setWeight: 5
        - pause: { duration: 15m }
        - analysis:
            templates:
              - templateName: workflow-success-rate
            args:
              - name: service-name
                value: workflow-engine
        - setWeight: 25
        - pause: { duration: 15m }
        - analysis:
            templates:
              - templateName: workflow-success-rate
        - setWeight: 50
        - pause: { duration: 15m }
        - analysis:
            templates:
              - templateName: workflow-success-rate
        - setWeight: 100
      canaryService: workflow-engine-canary
      stableService: workflow-engine-stable
      trafficRouting:
        istio:
          virtualService:
            name: workflow-engine-vsvc
            routes:
              - primary
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: workflow-success-rate
spec:
  metrics:
    - name: success-rate
      interval: 60s
      successCondition: result[0] >= 0.99
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(workflow_executions_total{status="success",
              service="{{args.service-name}}"}[5m]))
            /
            sum(rate(workflow_executions_total{
              service="{{args.service-name}}"}[5m]))
```

### Tabella comparativa strategie di promotion

| Strategia | Rischio | Velocita | Complessita | Quando usarla |
|-----------|---------|----------|-------------|---------------|
| Manuale con gate | Molto basso | Lenta | Bassa | Workflow critici (pagamenti, compliance) |
| Automatica condizionale | Basso | Veloce | Media | Workflow con buona copertura test |
| Canary progressiva | Molto basso | Media | Alta | Workflow ad alto traffico |
| Blue-green | Basso | Veloce | Media-alta | Workflow con requisiti di zero-downtime |
| Ring-based | Molto basso | Lenta | Alta | Organizzazioni enterprise multi-regione |

---

## Gestione configurazione per ambiente

### Struttura directory per configurazione multi-env

```
config/
├── base/                    # Configurazione comune a tutti gli ambienti
│   ├── workflow-defaults.yaml
│   ├── retry-policy.yaml
│   └── notification-channels.yaml
├── overlays/
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   ├── env-config.yaml
│   │   └── resource-limits.yaml
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   ├── env-config.yaml
│   │   └── resource-limits.yaml
│   └── prod/
│       ├── kustomization.yaml
│       ├── env-config.yaml
│       └── resource-limits.yaml
└── secrets/                 # NON in git — gestiti da secret manager
    ├── dev.env.encrypted
    ├── staging.env.encrypted
    └── prod.env.encrypted
```

### Configurazione base (condivisa)

```yaml
# config/base/workflow-defaults.yaml
workflow:
  engine:
    max_concurrent_executions: 50
    execution_timeout_seconds: 3600
    retry_policy:
      max_attempts: 3
      backoff_multiplier: 2
      initial_delay_seconds: 5
      max_delay_seconds: 300
  notifications:
    on_failure: true
    on_success: false
    channels:
      - type: email
        template: workflow-failure
      - type: slack
        template: workflow-failure
  logging:
    format: json
    include_payload: false
```

### Override per ambiente — Dev

```yaml
# config/overlays/dev/env-config.yaml
workflow:
  engine:
    max_concurrent_executions: 5      # Limitato in dev
    execution_timeout_seconds: 300    # Timeout breve per debug rapido
    log_level: DEBUG
  notifications:
    on_failure: false                 # Niente notifiche in dev
    on_success: false
  integrations:
    payment_gateway:
      base_url: https://sandbox.stripe.com
      mode: test
    email_service:
      provider: mailhog              # Cattura email localmente
      base_url: http://mailhog:8025
    crm:
      base_url: https://dev.salesforce.example.com
      sandbox: true
  feature_flags:
    new_approval_workflow: true       # Testare feature in dev
    enhanced_retry_logic: true
```

### Override per ambiente — Staging

```yaml
# config/overlays/staging/env-config.yaml
workflow:
  engine:
    max_concurrent_executions: 20
    execution_timeout_seconds: 1800
    log_level: INFO
  notifications:
    on_failure: true
    channels:
      - type: slack
        channel: "#staging-alerts"
  integrations:
    payment_gateway:
      base_url: https://sandbox.stripe.com
      mode: test
    email_service:
      provider: ses
      base_url: https://email-sandbox.us-east-1.amazonaws.com
      sandbox: true
    crm:
      base_url: https://staging.salesforce.example.com
      sandbox: true
  feature_flags:
    new_approval_workflow: true
    enhanced_retry_logic: true
```

### Override per ambiente — Prod

```yaml
# config/overlays/prod/env-config.yaml
workflow:
  engine:
    max_concurrent_executions: 50
    execution_timeout_seconds: 3600
    log_level: WARN
  notifications:
    on_failure: true
    channels:
      - type: slack
        channel: "#prod-alerts"
      - type: pagerduty
        severity: critical
  integrations:
    payment_gateway:
      base_url: https://api.stripe.com
      mode: live
    email_service:
      provider: ses
      base_url: https://email.us-east-1.amazonaws.com
      sandbox: false
    crm:
      base_url: https://login.salesforce.com
      sandbox: false
  feature_flags:
    new_approval_workflow: false      # Non ancora abilitato in prod
    enhanced_retry_logic: true        # Gia validato in staging
```

### Gestione secret per ambiente

I secret **non devono mai** risiedere in git, neppure cifrati (a meno di usare strumenti dedicati come SOPS o Sealed Secrets). Ogni ambiente ha il proprio set di credenziali.

#### Pattern con HashiCorp Vault

```
┌──────────────────────────────────────────────────┐
│                  HashiCorp Vault                  │
├──────────────────────────────────────────────────┤
│ secret/workflows/dev/                             │
│   ├── stripe_api_key = sk_test_...               │
│   ├── db_password = dev-password-123             │
│   ├── smtp_password = mailhog-no-auth            │
│   └── oauth_client_secret = dev-secret           │
│                                                   │
│ secret/workflows/staging/                         │
│   ├── stripe_api_key = sk_test_...               │
│   ├── db_password = Stg$ecure!Pass               │
│   ├── smtp_password = ses-staging-key            │
│   └── oauth_client_secret = staging-secret       │
│                                                   │
│ secret/workflows/prod/                            │
│   ├── stripe_api_key = sk_live_...               │
│   ├── db_password = Pr0d$uperS3cure!            │
│   ├── smtp_password = ses-prod-key               │
│   └── oauth_client_secret = prod-secret          │
└──────────────────────────────────────────────────┘
```

Accesso via policy Vault:

```hcl
# vault-policy-dev.hcl
path "secret/data/workflows/dev/*" {
  capabilities = ["read", "list"]
}

# vault-policy-staging.hcl
path "secret/data/workflows/staging/*" {
  capabilities = ["read"]
}

# vault-policy-prod.hcl — solo il service account di prod puo leggere
path "secret/data/workflows/prod/*" {
  capabilities = ["read"]
}
# Nessun accesso dev/staging ai secret di prod
```

#### Pattern con Kubernetes Secrets + Sealed Secrets

```yaml
# sealed-secret-prod.yaml — sicuro da committare in git
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: workflow-secrets
  namespace: workflows-prod
spec:
  encryptedData:
    STRIPE_API_KEY: AgBzN3...encrypted...
    DB_PASSWORD: AgCx8K...encrypted...
    OAUTH_CLIENT_SECRET: AgDm2P...encrypted...
```

Il Sealed Secrets controller nel cluster decripta e crea il Kubernetes Secret corrispondente. Solo la chiave privata del controller (mai esposta) puo decifrare i valori.

#### Pattern con AWS Secrets Manager

```json
{
  "SecretId": "workflows/prod/stripe",
  "SecretString": {
    "api_key": "sk_live_...",
    "webhook_secret": "whsec_..."
  },
  "Tags": [
    { "Key": "env", "Value": "prod" },
    { "Key": "team", "Value": "automation" },
    { "Key": "rotation", "Value": "90-days" }
  ]
}
```

Con rotazione automatica:

```json
{
  "RotationRules": {
    "AutomaticallyAfterDays": 90,
    "Duration": "2h",
    "ScheduleExpression": "rate(90 days)"
  },
  "RotationLambdaARN": "arn:aws:lambda:eu-west-1:123456789:function:rotate-workflow-secrets"
}
```

### Configurazione n8n multi-environment

```yaml
# docker-compose.dev.yml
services:
  n8n-dev:
    image: n8nio/n8n:1.72.1
    environment:
      - N8N_HOST=dev.n8n.example.com
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - N8N_ENCRYPTION_KEY=${DEV_ENCRYPTION_KEY}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres-dev
      - DB_POSTGRESDB_DATABASE=n8n_dev
      - DB_POSTGRESDB_USER=n8n_dev
      - DB_POSTGRESDB_PASSWORD=${DEV_DB_PASSWORD}
      - N8N_LOG_LEVEL=debug
      - EXECUTIONS_MODE=regular
      - N8N_DIAGNOSTICS_ENABLED=false
      - N8N_PERSONALIZATION_ENABLED=false
    volumes:
      - n8n_dev_data:/home/node/.n8n
    networks:
      - dev-network

---
# docker-compose.staging.yml
services:
  n8n-staging:
    image: n8nio/n8n:1.72.1
    environment:
      - N8N_HOST=staging.n8n.example.com
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - N8N_ENCRYPTION_KEY=${STAGING_ENCRYPTION_KEY}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres-staging
      - DB_POSTGRESDB_DATABASE=n8n_staging
      - DB_POSTGRESDB_USER=n8n_staging
      - DB_POSTGRESDB_PASSWORD=${STAGING_DB_PASSWORD}
      - N8N_LOG_LEVEL=info
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis-staging
    volumes:
      - n8n_staging_data:/home/node/.n8n
    networks:
      - staging-network

---
# docker-compose.prod.yml
services:
  n8n-prod:
    image: n8nio/n8n:1.72.1
    environment:
      - N8N_HOST=n8n.example.com
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - N8N_ENCRYPTION_KEY=${PROD_ENCRYPTION_KEY}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres-prod
      - DB_POSTGRESDB_DATABASE=n8n_prod
      - DB_POSTGRESDB_USER=n8n_prod
      - DB_POSTGRESDB_PASSWORD=${PROD_DB_PASSWORD}
      - N8N_LOG_LEVEL=warn
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis-prod
      - EXECUTIONS_DATA_PRUNE=true
      - EXECUTIONS_DATA_MAX_AGE=168
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: "2"
          memory: 4G
    volumes:
      - n8n_prod_data:/home/node/.n8n
    networks:
      - prod-network
```

---

## Parita degli ambienti e drift detection

### Cos'e il drift

Il drift e la divergenza progressiva fra ambienti che dovrebbero essere identici nella struttura. Cause comuni:

- Hotfix applicati direttamente in prod senza backport a staging/dev.
- Aggiornamenti manuali di dipendenze in un solo ambiente.
- Configurazioni modificate a mano via console cloud.
- Versioni di runtime diverse (Node 20.x in staging, Node 18.x in prod).
- Schema database fuori sync.

### Livelli di parita

| Livello | Cosa deve essere identico | Tolleranza drift |
|---------|---------------------------|------------------|
| Infrastruttura | OS, runtime, versioni middleware | Zero |
| Configurazione strutturale | Topologia servizi, network layout | Zero |
| Schema dati | Tabelle, indici, vincoli | Zero |
| Dati | Volume e distribuzione | Diverso (sanitized in staging) |
| Configurazione operativa | Scaling, repliche, timeout | Diverso (proporzionale) |
| Secret | Chiavi e credenziali | Diverso (test vs live) |

### Drift detection con Terraform

```hcl
# drift-detection.tf — modulo riusabile

variable "environments" {
  type    = list(string)
  default = ["dev", "staging", "prod"]
}

variable "expected_state" {
  type = object({
    engine_version    = string
    runtime_version   = string
    db_engine_version = string
    redis_version     = string
  })
  default = {
    engine_version    = "1.72.1"
    runtime_version   = "20.18.0"
    db_engine_version = "16.4"
    redis_version     = "7.2"
  }
}

# Esempio: verifica che tutte le istanze n8n usino la stessa versione
data "http" "health_check" {
  for_each = toset(var.environments)
  url      = "https://${each.value}.n8n.example.com/healthz"
}

resource "null_resource" "drift_check" {
  for_each = toset(var.environments)

  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<-EOT
      ACTUAL_VERSION=$(echo '${data.http.health_check[each.value].response_body}' | jq -r '.version')
      EXPECTED="${var.expected_state.engine_version}"
      if [ "$ACTUAL_VERSION" != "$EXPECTED" ]; then
        echo "DRIFT RILEVATO in ${each.value}: atteso $EXPECTED, trovato $ACTUAL_VERSION"
        exit 1
      fi
      echo "${each.value}: versione $ACTUAL_VERSION OK"
    EOT
  }
}
```

### Script di drift detection automatico

```bash
#!/usr/bin/env bash
# drift-check.sh — confronta versioni tra ambienti

set -euo pipefail

ENVIRONMENTS=("dev" "staging" "prod")
DRIFT_FOUND=false
REPORT=""

check_version() {
  local env=$1
  local endpoint=$2
  local jq_path=$3
  local expected=$4
  local label=$5

  actual=$(curl -sf "https://${env}.n8n.example.com${endpoint}" | jq -r "$jq_path" 2>/dev/null || echo "UNREACHABLE")

  if [ "$actual" != "$expected" ]; then
    DRIFT_FOUND=true
    REPORT+="DRIFT [$label] in $env: atteso=$expected, trovato=$actual\n"
  else
    REPORT+="OK   [$label] in $env: $actual\n"
  fi
}

for env in "${ENVIRONMENTS[@]}"; do
  check_version "$env" "/healthz" ".version" "1.72.1" "n8n-version"
  check_version "$env" "/healthz" ".nodeVersion" "v20.18.0" "node-version"
done

echo -e "\n=== DRIFT DETECTION REPORT — $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo -e "$REPORT"

if [ "$DRIFT_FOUND" = true ]; then
  echo "RISULTATO: DRIFT RILEVATO — intervento necessario"
  # Invia alert
  curl -sf -X POST "$SLACK_WEBHOOK_URL" \
    -H 'Content-Type: application/json' \
    -d "{\"text\": \"Drift rilevato tra ambienti workflow. Dettagli nel CI job.\"}"
  exit 1
else
  echo "RISULTATO: Nessun drift — tutti gli ambienti allineati"
fi
```

### Drift detection programmata in CI

```yaml
# .github/workflows/drift-detection.yml
name: Drift Detection Schedulato

on:
  schedule:
    - cron: "0 6 * * *"  # Ogni giorno alle 06:00 UTC
  workflow_dispatch:

jobs:
  detect-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Installa dipendenze
        run: |
          sudo apt-get update && sudo apt-get install -y jq

      - name: Esegui drift detection
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        run: ./scripts/drift-check.sh

      - name: Terraform plan per drift infrastrutturale
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          cd terraform/
          for env in dev staging prod; do
            echo "=== Terraform plan per $env ==="
            terraform init -backend-config="envs/${env}/backend.hcl"
            terraform plan -var-file="envs/${env}/terraform.tfvars" \
              -detailed-exitcode 2>&1 || {
              EXIT_CODE=$?
              if [ $EXIT_CODE -eq 2 ]; then
                echo "DRIFT INFRASTRUTTURALE in $env — terraform plan mostra differenze"
              fi
            }
          done
```

---

## GitOps per workflow promotion

### Principi GitOps applicati ai workflow

GitOps tratta il repository Git come unica fonte di verita per lo stato desiderato del sistema. Applicato ai workflow di automazione:

1. **Ogni workflow e definito in un file versionato** (JSON/YAML nel repo).
2. **La promozione avviene tramite merge/PR**, non tramite import manuale nella piattaforma.
3. **Un operatore riconcilia** lo stato del repo con lo stato della piattaforma.
4. **Drift = divergenza tra repo e piattaforma** — l'operatore riporta la piattaforma allo stato dichiarato.

### Struttura repository GitOps

```
workflows-gitops/
├── base/
│   └── workflows/
│       ├── order-processing.json
│       ├── customer-onboarding.json
│       ├── invoice-generation.json
│       └── data-sync.json
├── environments/
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   └── patches/
│   │       └── order-processing-dev.json
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   └── patches/
│   │       └── order-processing-staging.json
│   └── prod/
│       ├── kustomization.yaml
│       └── patches/
│           └── order-processing-prod.json
├── pipelines/
│   ├── promote-dev-to-staging.yml
│   └── promote-staging-to-prod.yml
└── scripts/
    ├── export-workflows.sh
    ├── import-workflows.sh
    ├── diff-workflows.sh
    └── validate-workflows.sh
```

### Branch strategy per GitOps

```
main (prod)
  │
  ├── staging (auto-merge da develop quando CI verde)
  │     │
  │     └── develop (merge da feature/*)
  │           │
  │           ├── feature/new-onboarding-flow
  │           ├── feature/enhanced-retry
  │           └── fix/invoice-timeout
```

### Operatore di riconciliazione per n8n

Script che sincronizza i workflow dal repo Git alla piattaforma n8n:

```bash
#!/usr/bin/env bash
# sync-workflows.sh — riconcilia workflow n8n con repo Git

set -euo pipefail

ENV=${1:?Uso: sync-workflows.sh <dev|staging|prod>}
N8N_URL="https://${ENV}.n8n.example.com"
N8N_API_KEY="${N8N_API_KEY:?N8N_API_KEY non impostata}"
WORKFLOW_DIR="environments/${ENV}/workflows"
DIFF_FOUND=false

echo "=== Sincronizzazione workflow per ambiente: $ENV ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

for workflow_file in "${WORKFLOW_DIR}"/*.json; do
  WORKFLOW_NAME=$(jq -r '.name' "$workflow_file")
  WORKFLOW_ID=$(jq -r '.id // empty' "$workflow_file")

  echo "Processando: $WORKFLOW_NAME (file: $workflow_file)"

  # Recupera versione attuale dalla piattaforma
  if [ -n "$WORKFLOW_ID" ]; then
    CURRENT=$(curl -sf \
      -H "X-N8N-API-KEY: $N8N_API_KEY" \
      "${N8N_URL}/api/v1/workflows/${WORKFLOW_ID}" 2>/dev/null || echo "{}")
  else
    CURRENT="{}"
  fi

  # Confronta (ignora campi volatili)
  DESIRED=$(jq 'del(.updatedAt, .createdAt, .statistics)' "$workflow_file")
  ACTUAL=$(echo "$CURRENT" | jq 'del(.updatedAt, .createdAt, .statistics)' 2>/dev/null || echo "{}")

  if [ "$DESIRED" != "$ACTUAL" ]; then
    DIFF_FOUND=true
    echo "  → Divergenza rilevata, aggiornamento in corso..."

    if [ "$CURRENT" = "{}" ]; then
      # Crea nuovo workflow
      curl -sf -X POST \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        -H "Content-Type: application/json" \
        -d @"$workflow_file" \
        "${N8N_URL}/api/v1/workflows"
      echo "  → Workflow creato"
    else
      # Aggiorna workflow esistente
      curl -sf -X PATCH \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        -H "Content-Type: application/json" \
        -d @"$workflow_file" \
        "${N8N_URL}/api/v1/workflows/${WORKFLOW_ID}"
      echo "  → Workflow aggiornato"
    fi
  else
    echo "  → Nessuna divergenza"
  fi
done

if [ "$DIFF_FOUND" = true ]; then
  echo "Sincronizzazione completata con modifiche."
else
  echo "Tutti i workflow gia allineati."
fi
```

### ArgoCD per workflow su Kubernetes

```yaml
# argocd-application-prod.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: workflows-prod
  namespace: argocd
spec:
  project: automation
  source:
    repoURL: https://github.com/example/workflows-gitops.git
    targetRevision: main
    path: environments/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: workflows-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  revisionHistoryLimit: 10
```

---

## Pipeline CI/CD per workflow di automazione

### Pipeline completa con GitHub Actions

```yaml
# .github/workflows/workflow-pipeline.yml
name: Workflow Automation Pipeline

on:
  push:
    branches: [develop, staging, main]
    paths:
      - "workflows/**"
      - "config/**"
  pull_request:
    branches: [develop, staging, main]

env:
  WORKFLOW_ENGINE_VERSION: "1.72.1"

jobs:
  # ─── FASE 1: Validazione ───
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Valida sintassi JSON workflow
        run: |
          find workflows/ -name "*.json" -exec sh -c '
            for f; do
              jq empty "$f" 2>/dev/null || {
                echo "ERRORE: JSON invalido in $f"
                exit 1
              }
            done
          ' _ {} +

      - name: Valida schema workflow
        run: |
          for f in workflows/*.json; do
            # Verifica campi obbligatori
            NAME=$(jq -r '.name // empty' "$f")
            NODES=$(jq -r '.nodes | length' "$f")
            if [ -z "$NAME" ]; then
              echo "ERRORE: workflow senza nome in $f"
              exit 1
            fi
            if [ "$NODES" -eq 0 ]; then
              echo "ERRORE: workflow senza nodi in $f"
              exit 1
            fi
            echo "OK: $f (nome=$NAME, nodi=$NODES)"
          done

      - name: Controlla credenziali hard-coded
        run: |
          # Pattern di secret comuni da intercettare
          PATTERNS='(sk_live_|sk_test_|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|password\s*[:=]\s*["\x27][^"\x27]+)'
          if grep -rEn "$PATTERNS" workflows/ config/; then
            echo "ERRORE: possibili credenziali hard-coded trovate"
            exit 1
          fi
          echo "OK: nessuna credenziale hard-coded rilevata"

  # ─── FASE 2: Test ───
  test:
    needs: validate
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: n8n_test
          POSTGRES_USER: n8n_test
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7.2-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Esegui unit test workflow
        run: |
          npm ci
          npm run test:unit -- --coverage
        env:
          DB_HOST: localhost
          DB_PORT: 5432
          DB_NAME: n8n_test
          DB_USER: n8n_test
          DB_PASSWORD: test_password

      - name: Esegui integration test
        run: npm run test:integration
        env:
          N8N_HOST: localhost
          REDIS_HOST: localhost

      - name: Verifica copertura >= 80%
        run: |
          COVERAGE=$(jq -r '.total.lines.pct' coverage/coverage-summary.json)
          echo "Copertura: ${COVERAGE}%"
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "ERRORE: copertura ${COVERAGE}% < 80%"
            exit 1
          fi

  # ─── FASE 3: Build artefatto ───
  build:
    needs: test
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}
      image_digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@v4

      - name: Metadata Docker
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}/workflow-engine
          tags: |
            type=sha,prefix=
            type=ref,event=branch

      - name: Build e push immagine
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  # ─── FASE 4: Deploy per ambiente ───
  deploy-dev:
    if: github.ref == 'refs/heads/develop'
    needs: build
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - uses: actions/checkout@v4
      - name: Deploy a Dev
        run: |
          ./scripts/deploy.sh \
            --env dev \
            --image ${{ needs.build.outputs.image_tag }} \
            --config config/overlays/dev/

      - name: Smoke test Dev
        run: ./scripts/smoke-test.sh dev

  deploy-staging:
    if: github.ref == 'refs/heads/staging'
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Deploy a Staging
        run: |
          ./scripts/deploy.sh \
            --env staging \
            --image ${{ needs.build.outputs.image_tag }} \
            --config config/overlays/staging/

      - name: Smoke test Staging
        run: ./scripts/smoke-test.sh staging

      - name: Integration test Staging
        run: ./scripts/integration-test.sh staging

  deploy-prod:
    if: github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://n8n.example.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy canary 10%
        run: |
          ./scripts/deploy.sh \
            --env prod \
            --image ${{ needs.build.outputs.image_tag }} \
            --canary-percent 10

      - name: Monitor canary 30 minuti
        run: ./scripts/canary-monitor.sh prod 30

      - name: Rollout completo o rollback
        run: |
          ERROR_RATE=$(curl -sf \
            'https://prometheus.example.com/api/v1/query?query=rate(workflow_errors_total{env="prod",version="canary"}[30m])' \
            | jq -r '.data.result[0].value[1]')
          if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
            echo "Error rate canary troppo alto: $ERROR_RATE — rollback"
            ./scripts/deploy.sh --env prod --rollback
            exit 1
          fi
          echo "Canary OK — rollout al 100%"
          ./scripts/deploy.sh --env prod --promote-canary
```

### Pipeline GitLab CI equivalente

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - test
  - build
  - deploy-dev
  - deploy-staging
  - deploy-prod

variables:
  WORKFLOW_ENGINE_VERSION: "1.72.1"

validate-workflows:
  stage: validate
  image: alpine:3.20
  before_script:
    - apk add --no-cache jq grep
  script:
    - |
      find workflows/ -name "*.json" -exec jq empty {} \;
      echo "Tutti i workflow JSON sono validi"
    - |
      PATTERNS='(sk_live_|AKIA[0-9A-Z]{16}|password\s*[:=]\s*["\x27])'
      if grep -rEn "$PATTERNS" workflows/ config/; then
        echo "ERRORE: credenziali hard-coded"
        exit 1
      fi

test-workflows:
  stage: test
  image: node:20-alpine
  services:
    - postgres:16
    - redis:7.2-alpine
  variables:
    POSTGRES_DB: n8n_test
    POSTGRES_USER: n8n_test
    POSTGRES_PASSWORD: test_password
  script:
    - npm ci
    - npm run test:unit -- --coverage
    - npm run test:integration
    - |
      COVERAGE=$(jq -r '.total.lines.pct' coverage/coverage-summary.json)
      if (( $(echo "$COVERAGE < 80" | bc -l) )); then
        exit 1
      fi
  coverage: '/Copertura:\s*(\d+\.?\d*)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

build-image:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy-dev:
  stage: deploy-dev
  environment:
    name: dev
    url: https://dev.n8n.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"
  script:
    - ./scripts/deploy.sh --env dev --image $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - ./scripts/smoke-test.sh dev

deploy-staging:
  stage: deploy-staging
  environment:
    name: staging
    url: https://staging.n8n.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == "staging"
  script:
    - ./scripts/deploy.sh --env staging --image $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - ./scripts/smoke-test.sh staging
    - ./scripts/integration-test.sh staging

deploy-prod:
  stage: deploy-prod
  environment:
    name: production
    url: https://n8n.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
  script:
    - ./scripts/deploy.sh --env prod --image $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA --canary-percent 10
    - ./scripts/canary-monitor.sh prod 30
    - ./scripts/deploy.sh --env prod --promote-canary
```

---

## Testing workflow prima della promotion

### Piramide di test per workflow di automazione

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E╲           Pochi test lenti e costosi
                 ╱ test  ╲         Flussi critici end-to-end
                ╱──────────╲
               ╱ Integration╲      Test con servizi reali
              ╱    test       ╲    API, database, code
             ╱─────────────────╲
            ╱    Unit test       ╲  Molti test veloci
           ╱  logica workflow     ╲ Funzioni, trasformazioni,
          ╱    condizioni, mapping ╲ routing, validazione
         ╱─────────────────────────╲
        ╱   Static analysis /       ╲ JSON schema, lint,
       ╱    schema validation        ╲ secret scanning
      ╱───────────────────────────────╲
```

### Unit test per logica workflow

```javascript
// test/workflow-logic.test.js
const { describe, it, expect } = require("@jest/globals");
const {
  calculateRetryDelay,
  shouldEscalate,
  transformOrderPayload,
  validateWebhookSignature,
} = require("../src/workflow-utils");

describe("calculateRetryDelay", () => {
  it("applica backoff esponenziale con jitter", () => {
    const delay1 = calculateRetryDelay(1, { base: 1000, multiplier: 2 });
    const delay2 = calculateRetryDelay(2, { base: 1000, multiplier: 2 });
    const delay3 = calculateRetryDelay(3, { base: 1000, multiplier: 2 });

    expect(delay1).toBeGreaterThanOrEqual(1000);
    expect(delay1).toBeLessThanOrEqual(1500);
    expect(delay2).toBeGreaterThanOrEqual(2000);
    expect(delay3).toBeGreaterThanOrEqual(4000);
  });

  it("rispetta max_delay", () => {
    const delay = calculateRetryDelay(10, {
      base: 1000,
      multiplier: 2,
      maxDelay: 30000,
    });
    expect(delay).toBeLessThanOrEqual(30000);
  });
});

describe("shouldEscalate", () => {
  it("escala dopo 3 fallimenti consecutivi", () => {
    expect(shouldEscalate({ consecutiveFailures: 2 })).toBe(false);
    expect(shouldEscalate({ consecutiveFailures: 3 })).toBe(true);
  });

  it("escala per errori critici indipendentemente dal conteggio", () => {
    expect(
      shouldEscalate({
        consecutiveFailures: 1,
        errorType: "PAYMENT_FAILED",
      })
    ).toBe(true);
  });
});

describe("transformOrderPayload", () => {
  it("trasforma payload Shopify in formato interno", () => {
    const shopifyOrder = {
      id: 12345,
      email: "cliente@example.com",
      total_price: "99.99",
      line_items: [{ title: "Prodotto A", quantity: 2, price: "49.99" }],
    };

    const result = transformOrderPayload(shopifyOrder, "shopify");

    expect(result).toEqual({
      externalId: "shopify-12345",
      customerEmail: "cliente@example.com",
      totalAmount: 99.99,
      currency: "EUR",
      items: [{ name: "Prodotto A", qty: 2, unitPrice: 49.99 }],
      source: "shopify",
      receivedAt: expect.any(String),
    });
  });
});
```

### Integration test per workflow

```javascript
// test/integration/order-workflow.integration.test.js
const { describe, it, expect, beforeAll, afterAll } = require("@jest/globals");
const axios = require("axios");

const N8N_URL = process.env.N8N_URL || "http://localhost:5678";
const API_KEY = process.env.N8N_API_KEY;

describe("Order Processing Workflow - Integration", () => {
  let workflowId;

  beforeAll(async () => {
    // Recupera ID workflow
    const resp = await axios.get(`${N8N_URL}/api/v1/workflows`, {
      headers: { "X-N8N-API-KEY": API_KEY },
    });
    const wf = resp.data.data.find((w) => w.name === "Order Processing");
    workflowId = wf.id;

    // Assicura che il workflow sia attivo
    await axios.patch(
      `${N8N_URL}/api/v1/workflows/${workflowId}`,
      { active: true },
      { headers: { "X-N8N-API-KEY": API_KEY } }
    );
  });

  it("processa un ordine valido end-to-end", async () => {
    // Trigger workflow via webhook
    const response = await axios.post(
      `${N8N_URL}/webhook/order-received`,
      {
        orderId: "TEST-001",
        customerEmail: "test@example.com",
        items: [{ sku: "PROD-A", quantity: 1, price: 29.99 }],
        total: 29.99,
      },
      { timeout: 30000 }
    );

    expect(response.status).toBe(200);
    expect(response.data).toMatchObject({
      status: "processed",
      orderId: "TEST-001",
    });
  });

  it("rifiuta payload invalido con errore chiaro", async () => {
    try {
      await axios.post(`${N8N_URL}/webhook/order-received`, {
        // Manca orderId — campo obbligatorio
        items: [],
      });
      throw new Error("Avrebbe dovuto fallire");
    } catch (err) {
      expect(err.response.status).toBe(400);
      expect(err.response.data.error).toContain("orderId");
    }
  });

  afterAll(async () => {
    // Cleanup: disattiva workflow di test
    if (workflowId) {
      await axios.patch(
        `${N8N_URL}/api/v1/workflows/${workflowId}`,
        { active: false },
        { headers: { "X-N8N-API-KEY": API_KEY } }
      );
    }
  });
});
```

### Smoke test post-deploy

```bash
#!/usr/bin/env bash
# smoke-test.sh — verifica rapida post-deploy

set -euo pipefail

ENV=${1:?Uso: smoke-test.sh <dev|staging|prod>}
BASE_URL="https://${ENV}.n8n.example.com"
FAILURES=0

smoke() {
  local name=$1
  local url=$2
  local expected_status=${3:-200}
  local jq_check=${4:-"."}

  echo -n "  [$name] $url ... "

  HTTP_CODE=$(curl -sf -o /tmp/smoke-response.json \
    -w "%{http_code}" \
    -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
    "$url" 2>/dev/null || echo "000")

  if [ "$HTTP_CODE" != "$expected_status" ]; then
    echo "FAIL (HTTP $HTTP_CODE, atteso $expected_status)"
    FAILURES=$((FAILURES + 1))
    return
  fi

  if [ "$jq_check" != "." ]; then
    RESULT=$(jq -r "$jq_check" /tmp/smoke-response.json 2>/dev/null || echo "PARSE_ERROR")
    if [ "$RESULT" = "PARSE_ERROR" ] || [ "$RESULT" = "null" ]; then
      echo "FAIL (jq check fallito: $jq_check)"
      FAILURES=$((FAILURES + 1))
      return
    fi
  fi

  echo "OK"
}

echo "=== SMOKE TEST — $ENV — $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

smoke "Health check"      "${BASE_URL}/healthz"       200 ".status"
smoke "API raggiungibile" "${BASE_URL}/api/v1/workflows" 200 ".data"
smoke "Versione corretta" "${BASE_URL}/healthz"       200 ".version"

# Test webhook (solo in dev/staging con endpoint di test)
if [ "$ENV" != "prod" ]; then
  smoke "Webhook echo" "${BASE_URL}/webhook-test/echo" 200 ".received"
fi

echo ""
if [ "$FAILURES" -gt 0 ]; then
  echo "RISULTATO: $FAILURES test falliti — DEPLOY NON VALIDO"
  exit 1
else
  echo "RISULTATO: tutti gli smoke test passati"
fi
```

### Contract test fra workflow e servizi esterni

```javascript
// test/contract/stripe-contract.test.js
const { Pact } = require("@pact-foundation/pact");

const provider = new Pact({
  consumer: "WorkflowEngine",
  provider: "StripeAPI",
  port: 1234,
});

describe("Contratto con Stripe API", () => {
  beforeAll(() => provider.setup());
  afterAll(() => provider.finalize());

  it("crea un PaymentIntent", async () => {
    await provider.addInteraction({
      state: "cliente esistente",
      uponReceiving: "richiesta creazione PaymentIntent",
      withRequest: {
        method: "POST",
        path: "/v1/payment_intents",
        headers: {
          Authorization: "Bearer sk_test_xxx",
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: "amount=9999&currency=eur&customer=cus_test123",
      },
      willRespondWith: {
        status: 200,
        body: {
          id: "pi_test_abc",
          status: "requires_confirmation",
          amount: 9999,
          currency: "eur",
        },
      },
    });

    // Il workflow sotto test chiamerebbe Stripe qui
    // e verificherebbe la risposta attesa
  });
});
```

---

## Strategie di rollback

### Rollback immediato — versione precedente

Il meccanismo piu semplice: ri-deploy dell'artefatto precedente. Funziona se l'artefatto e immutabile e lo stato dati e compatibile.

```bash
#!/usr/bin/env bash
# rollback.sh — rollback alla versione precedente

set -euo pipefail

ENV=${1:?Uso: rollback.sh <dev|staging|prod>}
DEPLOY_HISTORY="deployments/${ENV}/history.json"

# Recupera versione attuale e precedente
CURRENT=$(jq -r '.deployments[-1].version' "$DEPLOY_HISTORY")
PREVIOUS=$(jq -r '.deployments[-2].version' "$DEPLOY_HISTORY")

if [ "$PREVIOUS" = "null" ]; then
  echo "ERRORE: nessuna versione precedente disponibile per rollback"
  exit 1
fi

echo "=== ROLLBACK $ENV ==="
echo "Versione attuale:   $CURRENT"
echo "Rollback a:         $PREVIOUS"
echo "Timestamp:          $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Operatore:          ${OPERATOR:-unknown}"

# Conferma in produzione
if [ "$ENV" = "prod" ]; then
  echo ""
  echo "ATTENZIONE: rollback in PRODUZIONE"
  read -rp "Conferma digitando 'ROLLBACK-PROD': " CONFIRM
  if [ "$CONFIRM" != "ROLLBACK-PROD" ]; then
    echo "Rollback annullato"
    exit 1
  fi
fi

# Esegui rollback
./scripts/deploy.sh \
  --env "$ENV" \
  --version "$PREVIOUS" \
  --reason "rollback da $CURRENT"

# Registra rollback
jq --arg ver "$PREVIOUS" \
   --arg from "$CURRENT" \
   --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
   '.rollbacks += [{"from": $from, "to": $ver, "timestamp": $ts}]' \
   "$DEPLOY_HISTORY" > "${DEPLOY_HISTORY}.tmp" \
   && mv "${DEPLOY_HISTORY}.tmp" "$DEPLOY_HISTORY"

# Smoke test post-rollback
./scripts/smoke-test.sh "$ENV"

echo "Rollback completato con successo."
```

### Rollback database-aware

Se il deploy include migrazioni database, il rollback e piu complesso. Servono migrazioni reversibili.

```
Deploy v2.0:
  1. Migrazione DB: ALTER TABLE orders ADD COLUMN priority INT DEFAULT 0;
  2. Deploy codice v2.0

Rollback a v1.0:
  1. Deploy codice v1.0 (ignora colonna priority)
  2. [Opzionale] Migrazione down: ALTER TABLE orders DROP COLUMN priority;
```

Regole per migrazioni sicure:

1. **Additive-only.** Aggiungi colonne, tabelle, indici. Non rimuovere mai nella stessa release.
2. **Backward-compatible.** Il codice v1.0 deve funzionare con lo schema di v2.0 (ignora la nuova colonna).
3. **Drop differito.** Le colonne/tabelle rimosse vengono droppate solo dopo che v2.0 e stabile (release successiva).

### Versioning degli artefatti per rollback rapido

```json
{
  "deployments": [
    {
      "version": "abc1234",
      "image": "ghcr.io/example/workflow-engine:abc1234",
      "deployed_at": "2026-05-20T14:30:00Z",
      "deployed_by": "ci-pipeline",
      "config_hash": "sha256:9f86d081...",
      "status": "superseded"
    },
    {
      "version": "def5678",
      "image": "ghcr.io/example/workflow-engine:def5678",
      "deployed_at": "2026-05-22T10:15:00Z",
      "deployed_by": "ci-pipeline",
      "config_hash": "sha256:a3c2b1d0...",
      "status": "active"
    }
  ],
  "rollbacks": [],
  "retention_policy": {
    "keep_last_n_versions": 10,
    "max_age_days": 90
  }
}
```

### Runbook di rollback

| Fase | Azione | Tempo max | Chi |
|------|--------|-----------|-----|
| 1 | Identificare la versione da rollback | 2 min | On-call |
| 2 | Eseguire script rollback | 5 min | On-call |
| 3 | Smoke test post-rollback | 3 min | Automatico |
| 4 | Verificare metriche tornate normali | 10 min | On-call |
| 5 | Comunicare agli stakeholder | 5 min | On-call |
| 6 | Post-mortem (entro 48h) | - | Team |

---

## Pattern di isolamento ambienti

### Isolamento a livello di rete

Ogni ambiente ha una propria rete virtuale (VPC/VNet) senza peering fra ambienti:

```hcl
# terraform/modules/network/main.tf

variable "env" {
  type = string
}

variable "cidr_blocks" {
  type = map(string)
  default = {
    dev     = "10.0.0.0/16"
    staging = "10.1.0.0/16"
    prod    = "10.2.0.0/16"
  }
}

resource "aws_vpc" "workflow_vpc" {
  cidr_block           = var.cidr_blocks[var.env]
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "workflow-vpc-${var.env}"
    Environment = var.env
    ManagedBy   = "terraform"
  }
}

resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.workflow_vpc.id
  cidr_block        = cidrsubnet(aws_vpc.workflow_vpc.cidr_block, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name        = "workflow-private-${var.env}-${count.index}"
    Environment = var.env
  }
}

# Nessun VPC peering tra ambienti — isolamento totale
```

### Isolamento a livello di identita (IAM)

```hcl
# terraform/modules/iam/main.tf

variable "env" {
  type = string
}

# Ruolo per il workflow engine — scope limitato al proprio ambiente
resource "aws_iam_role" "workflow_engine" {
  name = "workflow-engine-${var.env}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = "eu-west-1"
          }
        }
      }
    ]
  })
}

# Accesso solo ai secret del proprio ambiente
resource "aws_iam_role_policy" "secrets_access" {
  name = "workflow-secrets-${var.env}"
  role = aws_iam_role.workflow_engine.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "arn:aws:secretsmanager:eu-west-1:*:secret:workflows/${var.env}/*"
      },
      {
        Effect   = "Deny"
        Action   = "secretsmanager:*"
        Resource = "arn:aws:secretsmanager:eu-west-1:*:secret:workflows/prod/*"
        Condition = {
          StringNotEquals = {
            "aws:PrincipalTag/env" = "prod"
          }
        }
      }
    ]
  })
}
```

### Isolamento a livello di dati

Ogni ambiente ha il proprio database con credenziali separate:

```yaml
# Database per ambiente
databases:
  dev:
    host: postgres-dev.internal
    name: workflows_dev
    user: wf_dev_user
    ssl_mode: prefer
    max_connections: 10
    data_source: seed/fixtures

  staging:
    host: postgres-staging.internal
    name: workflows_staging
    user: wf_staging_user
    ssl_mode: require
    max_connections: 25
    data_source: sanitized_prod_snapshot

  prod:
    host: postgres-prod.internal
    name: workflows_prod
    user: wf_prod_user
    ssl_mode: verify-full
    max_connections: 100
    data_source: live
    backup:
      frequency: continuous
      retention_days: 30
      point_in_time_recovery: true
```

Script per sanitizzazione dati prod → staging:

```bash
#!/usr/bin/env bash
# sanitize-prod-to-staging.sh

set -euo pipefail

PROD_DUMP="/tmp/prod-dump-$(date +%Y%m%d).sql"
SANITIZED="/tmp/prod-sanitized-$(date +%Y%m%d).sql"

echo "1. Dump prod (escludendo tabelle con PII diretto)..."
pg_dump \
  --host="$PROD_DB_HOST" \
  --dbname="$PROD_DB_NAME" \
  --username="$PROD_DB_USER" \
  --no-owner \
  --exclude-table='audit_logs' \
  --exclude-table='user_sessions' \
  > "$PROD_DUMP"

echo "2. Sanitizzazione PII..."
sed \
  -e "s/[a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]*\.[a-zA-Z]*/user_REDACTED@example.com/g" \
  -e "s/\+[0-9]\{10,15\}/+390000000000/g" \
  "$PROD_DUMP" > "$SANITIZED"

echo "3. Import in staging..."
psql \
  --host="$STAGING_DB_HOST" \
  --dbname="$STAGING_DB_NAME" \
  --username="$STAGING_DB_USER" \
  -f "$SANITIZED"

echo "4. Cleanup file temporanei..."
rm -f "$PROD_DUMP" "$SANITIZED"

echo "Sanitizzazione completata."
```

---

## Blue-green deployment per workflow

### Architettura blue-green

```
                         ┌─────────────┐
                         │   Load      │
                         │  Balancer   │
                         └──────┬──────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
              ┌─────▼─────┐         ┌─────▼─────┐
              │   BLUE     │         │   GREEN    │
              │  (attivo)  │         │ (standby)  │
              │            │         │            │
              │ Workflow   │         │ Workflow   │
              │ Engine     │         │ Engine     │
              │ v1.0       │         │ v2.0       │
              │            │         │            │
              │ ┌────────┐ │         │ ┌────────┐ │
              │ │ DB v1  │ │         │ │ DB v2  │ │
              │ └────────┘ │         │ └────────┘ │
              └────────────┘         └────────────┘

        Traffico: 100% → BLUE          Traffico: 0% → GREEN

        --- Dopo validazione GREEN ---

              ┌────────────┐         ┌────────────┐
              │   BLUE     │         │   GREEN    │
              │ (standby)  │         │  (attivo)  │
              │ v1.0       │         │ v2.0       │
              └────────────┘         └────────────┘

        Traffico: 0% → BLUE          Traffico: 100% → GREEN
```

### Implementazione con Nginx

```nginx
# /etc/nginx/conf.d/workflow-blue-green.conf

upstream workflow_blue {
    server 10.2.1.10:5678;
    server 10.2.1.11:5678;
}

upstream workflow_green {
    server 10.2.2.10:5678;
    server 10.2.2.11:5678;
}

# Variabile per selezionare ambiente attivo
# Cambiata da script di deploy
map $host $active_upstream {
    default workflow_blue;   # ← cambiare a workflow_green per switch
}

server {
    listen 443 ssl;
    server_name n8n.example.com;

    location / {
        proxy_pass http://$active_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Endpoint per health check del deployment standby
    location /internal/standby-health {
        internal;
        proxy_pass http://workflow_green/healthz;
    }
}
```

### Script di switch blue-green

```bash
#!/usr/bin/env bash
# blue-green-switch.sh — switch traffico tra blue e green

set -euo pipefail

CURRENT_ACTIVE=$(grep -oP 'default workflow_\K\w+' \
  /etc/nginx/conf.d/workflow-blue-green.conf)

if [ "$CURRENT_ACTIVE" = "blue" ]; then
  NEW_ACTIVE="green"
else
  NEW_ACTIVE="blue"
fi

echo "Switch: $CURRENT_ACTIVE → $NEW_ACTIVE"

# 1. Verifica che il nuovo ambiente sia sano
HEALTH=$(curl -sf "http://workflow_${NEW_ACTIVE}/healthz" | jq -r '.status')
if [ "$HEALTH" != "ok" ]; then
  echo "ERRORE: $NEW_ACTIVE non e healthy — switch annullato"
  exit 1
fi

# 2. Switch configurazione Nginx
sed -i "s/default workflow_${CURRENT_ACTIVE}/default workflow_${NEW_ACTIVE}/" \
  /etc/nginx/conf.d/workflow-blue-green.conf

# 3. Reload Nginx (zero downtime)
nginx -t && nginx -s reload

echo "Switch completato: traffico ora su $NEW_ACTIVE"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 4. Smoke test post-switch
./scripts/smoke-test.sh prod

# 5. Mantieni il vecchio ambiente attivo per rollback rapido (30 min)
echo "L'ambiente $CURRENT_ACTIVE restera attivo per 30 minuti come fallback."
echo "Per rollback: esegui nuovamente questo script."
```

### Vantaggi e svantaggi blue-green per workflow

| Vantaggi | Svantaggi |
|----------|-----------|
| Zero downtime durante switch | Costo raddoppiato (due set di risorse) |
| Rollback istantaneo (switch indietro) | Complessita gestione database (due DB o shared) |
| Test completo su infra reale prima dello switch | Workflow in esecuzione possono rimanere orfani durante switch |
| Nessuna incompatibilita di versione durante transition | Richiede drain delle esecuzioni attive |

---

## Feature flag nelle automazioni

### Perche usare feature flag nei workflow

I feature flag permettono di:

- Abilitare nuove funzionalita gradualmente senza rideploy.
- Testare feature in produzione con un subset di utenti/clienti.
- Disabilitare istantaneamente una feature problematica (kill switch).
- Eseguire A/B test su percorsi di workflow diversi.

### Configurazione feature flag

```json
{
  "flags": {
    "new_approval_workflow": {
      "enabled": false,
      "description": "Nuovo flusso approvazione ordini con doppia firma",
      "rollout": {
        "strategy": "percentage",
        "percentage": 0,
        "sticky": true
      },
      "environments": {
        "dev": { "enabled": true, "percentage": 100 },
        "staging": { "enabled": true, "percentage": 100 },
        "prod": { "enabled": false, "percentage": 0 }
      },
      "owner": "team-automation",
      "created_at": "2026-05-15",
      "expires_at": "2026-07-15",
      "jira_ticket": "AUTO-1234"
    },
    "enhanced_retry_logic": {
      "enabled": true,
      "description": "Retry con backoff adattivo basato su tipo errore",
      "rollout": {
        "strategy": "all",
        "percentage": 100
      },
      "environments": {
        "dev": { "enabled": true },
        "staging": { "enabled": true },
        "prod": { "enabled": true }
      },
      "owner": "team-platform",
      "created_at": "2026-04-01",
      "permanent": true
    },
    "parallel_execution_v2": {
      "enabled": false,
      "description": "Esecuzione parallela branch con pool condiviso",
      "rollout": {
        "strategy": "user_list",
        "users": ["customer-abc", "customer-xyz"]
      },
      "environments": {
        "dev": { "enabled": true },
        "staging": { "enabled": true, "users": ["test-customer-1"] },
        "prod": { "enabled": false }
      },
      "owner": "team-automation",
      "created_at": "2026-05-10"
    }
  },
  "metadata": {
    "schema_version": "1.0",
    "last_audit": "2026-05-20"
  }
}
```

### Integrazione feature flag nel codice workflow

```javascript
// src/feature-flags.js
const flags = require("./config/feature-flags.json");

class FeatureFlagService {
  constructor(environment) {
    this.env = environment;
    this.flags = flags.flags;
  }

  isEnabled(flagName, context = {}) {
    const flag = this.flags[flagName];
    if (!flag) return false;

    // Controlla override per ambiente
    const envConfig = flag.environments?.[this.env];
    if (envConfig && typeof envConfig.enabled === "boolean") {
      if (!envConfig.enabled) return false;
    } else if (!flag.enabled) {
      return false;
    }

    // Strategia di rollout
    const rollout = envConfig?.strategy
      ? envConfig
      : flag.rollout;

    switch (rollout.strategy) {
      case "all":
        return true;

      case "percentage": {
        if (!context.userId) return false;
        const hash = this._hashUserId(context.userId);
        return hash < (rollout.percentage / 100);
      }

      case "user_list":
        return (rollout.users || []).includes(context.userId);

      default:
        return false;
    }
  }

  _hashUserId(userId) {
    // Hash deterministico per sticky assignment
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      const char = userId.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // 32-bit
    }
    return Math.abs(hash) / 2147483647;
  }
}

module.exports = { FeatureFlagService };
```

### Uso nel workflow n8n (Function node)

```javascript
// n8n Function node — feature flag check
const env = $env.N8N_ENVIRONMENT || "dev";

const featureFlags = {
  new_approval_workflow: {
    dev: true,
    staging: true,
    prod: false,
  },
  enhanced_retry: {
    dev: true,
    staging: true,
    prod: true,
  },
};

const isEnabled = (flagName) => {
  return featureFlags[flagName]?.[env] ?? false;
};

// Routing condizionale basato su feature flag
if (isEnabled("new_approval_workflow")) {
  return [{ json: { ...items[0].json, route: "new_approval" } }];
} else {
  return [{ json: { ...items[0].json, route: "legacy_approval" } }];
}
```

### Lifecycle dei feature flag

```
1. CREAZIONE
   → Flag creato con enabled=false in tutti gli ambienti
   → Codice scritto con if(flag) per nuovo percorso

2. TEST DEV
   → enabled=true solo in dev
   → Test automatici + manuali

3. TEST STAGING
   → enabled=true in staging
   → UAT con dati sanitizzati

4. ROLLOUT PROD GRADUALE
   → percentage: 5% → 25% → 50% → 100%
   → Monitoraggio metriche a ogni step

5. FLAG PERMANENTE o CLEANUP
   → Se temporaneo: rimuovi flag + codice old path entro 30 giorni
   → Se operativo (kill switch): mantieni come flag permanente
```

---

## Routing environment-specific

### Routing basato su header

I workflow possono ricevere richieste destinate a ambienti diversi; un reverse proxy o API gateway instrada in base a header specifici.

```yaml
# Configurazione Traefik — routing per ambiente
# traefik-dynamic.yaml
http:
  routers:
    workflow-dev:
      rule: "Host(`api.example.com`) && Headers(`X-Environment`, `dev`)"
      service: workflow-dev
      entryPoints:
        - websecure
      middlewares:
        - dev-auth

    workflow-staging:
      rule: "Host(`api.example.com`) && Headers(`X-Environment`, `staging`)"
      service: workflow-staging
      entryPoints:
        - websecure
      middlewares:
        - staging-auth

    workflow-prod:
      rule: "Host(`api.example.com`)"
      service: workflow-prod
      priority: 1
      entryPoints:
        - websecure
      middlewares:
        - prod-auth
        - rate-limit

  services:
    workflow-dev:
      loadBalancer:
        servers:
          - url: "http://n8n-dev:5678"

    workflow-staging:
      loadBalancer:
        servers:
          - url: "http://n8n-staging:5678"

    workflow-prod:
      loadBalancer:
        servers:
          - url: "http://n8n-prod-1:5678"
          - url: "http://n8n-prod-2:5678"
          - url: "http://n8n-prod-3:5678"

  middlewares:
    rate-limit:
      rateLimit:
        average: 100
        burst: 200
        period: 1m

    dev-auth:
      basicAuth:
        users:
          - "dev:$apr1$..."

    staging-auth:
      basicAuth:
        users:
          - "staging:$apr1$..."

    prod-auth:
      forwardAuth:
        address: "http://auth-service:8080/verify"
        trustForwardHeader: true
```

### Routing basato su subdomain

Pattern piu semplice: ogni ambiente ha il proprio sottodominio.

```
dev.n8n.example.com     → cluster dev
staging.n8n.example.com → cluster staging
n8n.example.com         → cluster prod
```

Configurazione DNS (Terraform):

```hcl
# terraform/dns.tf

resource "aws_route53_record" "n8n_dev" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "dev.n8n.example.com"
  type    = "A"
  alias {
    name                   = aws_lb.workflow_dev.dns_name
    zone_id                = aws_lb.workflow_dev.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "n8n_staging" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "staging.n8n.example.com"
  type    = "A"
  alias {
    name                   = aws_lb.workflow_staging.dns_name
    zone_id                = aws_lb.workflow_staging.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "n8n_prod" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "n8n.example.com"
  type    = "A"
  alias {
    name                   = aws_lb.workflow_prod.dns_name
    zone_id                = aws_lb.workflow_prod.zone_id
    evaluate_target_health = true
  }
}
```

### Routing webhook per ambiente

I webhook in ingresso devono raggiungere l'ambiente corretto. Pattern consigliato: URL con prefisso ambiente.

```
POST https://webhooks.example.com/dev/order-received
POST https://webhooks.example.com/staging/order-received
POST https://webhooks.example.com/prod/order-received
```

Oppure con un singolo endpoint e routing interno:

```yaml
# webhook-router.yaml — configurazione API Gateway
paths:
  /webhook/{environment}/{workflow}:
    post:
      parameters:
        - name: environment
          in: path
          required: true
          schema:
            type: string
            enum: [dev, staging, prod]
        - name: workflow
          in: path
          required: true
          schema:
            type: string
      x-gateway-integration:
        type: http_proxy
        uri: "https://{environment}.n8n.example.com/webhook/{workflow}"
        requestParameters:
          integration.request.path.environment: method.request.path.environment
          integration.request.path.workflow: method.request.path.workflow
```

---

## Infrastructure-as-Code per piattaforme workflow

### Provisioning completo con Terraform

```hcl
# terraform/main.tf — modulo principale

terraform {
  required_version = ">= 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }

  backend "s3" {
    bucket         = "terraform-state-workflows"
    key            = "workflows/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-lock"
    encrypt        = true
  }
}

variable "env" {
  type        = string
  description = "Ambiente: dev, staging, prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "Ambiente deve essere dev, staging o prod."
  }
}

variable "config" {
  type = map(object({
    instance_count = number
    instance_type  = string
    db_instance    = string
    db_storage_gb  = number
    redis_node     = string
  }))
  default = {
    dev = {
      instance_count = 1
      instance_type  = "t3.small"
      db_instance    = "db.t3.micro"
      db_storage_gb  = 20
      redis_node     = "cache.t3.micro"
    }
    staging = {
      instance_count = 2
      instance_type  = "t3.medium"
      db_instance    = "db.t3.small"
      db_storage_gb  = 50
      redis_node     = "cache.t3.small"
    }
    prod = {
      instance_count = 3
      instance_type  = "t3.large"
      db_instance    = "db.r6g.large"
      db_storage_gb  = 200
      redis_node     = "cache.r6g.large"
    }
  }
}

locals {
  cfg = var.config[var.env]
}

# ── Rete ──
module "network" {
  source = "./modules/network"
  env    = var.env
}

# ── Database ──
resource "aws_db_instance" "workflow_db" {
  identifier     = "workflow-db-${var.env}"
  engine         = "postgres"
  engine_version = "16.4"
  instance_class = local.cfg.db_instance
  allocated_storage = local.cfg.db_storage_gb

  db_name  = "workflows_${var.env}"
  username = "wf_${var.env}_admin"
  password = data.aws_secretsmanager_secret_version.db_password.secret_string

  vpc_security_group_ids = [module.network.db_security_group_id]
  db_subnet_group_name   = module.network.db_subnet_group_name

  backup_retention_period = var.env == "prod" ? 30 : 7
  multi_az               = var.env == "prod" ? true : false
  deletion_protection    = var.env == "prod" ? true : false
  skip_final_snapshot    = var.env != "prod"

  storage_encrypted = true
  kms_key_id       = aws_kms_key.workflow_key.arn

  tags = {
    Environment = var.env
    ManagedBy   = "terraform"
    Service     = "workflow-engine"
  }
}

# ── Redis ──
resource "aws_elasticache_replication_group" "workflow_redis" {
  replication_group_id = "workflow-redis-${var.env}"
  description          = "Redis per code workflow - ${var.env}"
  node_type            = local.cfg.redis_node
  num_cache_clusters   = var.env == "prod" ? 3 : 1

  engine_version       = "7.2"
  port                 = 6379
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  subnet_group_name    = module.network.redis_subnet_group_name
  security_group_ids   = [module.network.redis_security_group_id]

  automatic_failover_enabled = var.env == "prod" ? true : false

  tags = {
    Environment = var.env
    ManagedBy   = "terraform"
  }
}

# ── ECS Service (n8n) ──
resource "aws_ecs_service" "workflow_engine" {
  name            = "workflow-engine-${var.env}"
  cluster         = aws_ecs_cluster.workflow.id
  task_definition = aws_ecs_task_definition.workflow_engine.arn
  desired_count   = local.cfg.instance_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.network.private_subnet_ids
    security_groups  = [module.network.app_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.workflow.arn
    container_name   = "n8n"
    container_port   = 5678
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = var.env == "prod" ? 100 : 50
  }

  tags = {
    Environment = var.env
    ManagedBy   = "terraform"
  }
}

# ── KMS per crittografia ──
resource "aws_kms_key" "workflow_key" {
  description             = "Chiave crittografia workflow - ${var.env}"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Environment = var.env
    ManagedBy   = "terraform"
  }
}
```

### Terraform per ambienti separati — struttura directory

```
terraform/
├── modules/
│   ├── network/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── database/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── cache/
│   ├── compute/
│   └── monitoring/
├── envs/
│   ├── dev/
│   │   ├── main.tf          # module calls con var.env = "dev"
│   │   ├── terraform.tfvars
│   │   └── backend.hcl
│   ├── staging/
│   │   ├── main.tf
│   │   ├── terraform.tfvars
│   │   └── backend.hcl
│   └── prod/
│       ├── main.tf
│       ├── terraform.tfvars
│       └── backend.hcl
└── scripts/
    ├── plan-all.sh
    ├── apply-all.sh
    └── drift-check.sh
```

### Pulumi (alternativa IaC in TypeScript)

```typescript
// infra/index.ts — provisioning con Pulumi
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const env = pulumi.getStack(); // dev | staging | prod

const config = new pulumi.Config();

const sizing: Record<string, {
  instanceCount: number;
  instanceType: string;
  dbInstance: string;
}> = {
  dev: { instanceCount: 1, instanceType: "t3.small", dbInstance: "db.t3.micro" },
  staging: { instanceCount: 2, instanceType: "t3.medium", dbInstance: "db.t3.small" },
  prod: { instanceCount: 3, instanceType: "t3.large", dbInstance: "db.r6g.large" },
};

const s = sizing[env];

const vpc = new aws.ec2.Vpc(`workflow-vpc-${env}`, {
  cidrBlock: env === "prod" ? "10.2.0.0/16" : env === "staging" ? "10.1.0.0/16" : "10.0.0.0/16",
  enableDnsSupport: true,
  enableDnsHostnames: true,
  tags: { Environment: env, ManagedBy: "pulumi" },
});

const db = new aws.rds.Instance(`workflow-db-${env}`, {
  identifier: `workflow-db-${env}`,
  engine: "postgres",
  engineVersion: "16.4",
  instanceClass: s.dbInstance,
  allocatedStorage: env === "prod" ? 200 : 50,
  dbName: `workflows_${env}`,
  username: `wf_${env}_admin`,
  password: config.requireSecret("dbPassword"),
  vpcSecurityGroupIds: [/* security group IDs */],
  storageEncrypted: true,
  multiAz: env === "prod",
  deletionProtection: env === "prod",
  tags: { Environment: env },
});

export const dbEndpoint = db.endpoint;
export const vpcId = vpc.id;
```

---

## Esercizi

1. **Lab — 3-env n8n.** Setup 3 istanze n8n (dev/staging/prod) + Git pipeline che deploya secondo branch.

2. **Stretch — canary deploy.** Aggiungi al lab 1 canary deploy 10% / 50% / 100% con monitoring.

3. **Lab — GitOps promotion.** Crea un repository Git con workflow n8n esportati in JSON. Implementa uno script che sincronizza automaticamente i workflow dal repo alla piattaforma quando un merge avviene su branch `staging` o `main`. Verifica che le modifiche manuali nella piattaforma vengano sovrascritte dal reconciler.

4. **Lab — Drift detection.** Scrivi uno script bash che confronta le versioni di n8n, Node.js e PostgreSQL tra dev, staging e prod. Eseguilo come job schedulato (cron o CI) che invia un alert Slack quando rileva divergenze.

5. **Lab — Feature flag routing.** In un workflow n8n, implementa un nodo Function che controlla un feature flag e instrada l'esecuzione su due percorsi diversi (legacy vs nuovo). Testa il comportamento cambiando la configurazione del flag in dev vs staging.

6. **Lab — Rollback procedure.** Simula un deploy difettoso in staging: deploya una versione con un bug intenzionale, verifica che lo smoke test fallisca, esegui il rollback alla versione precedente, conferma che il sistema torna funzionante. Documenta i tempi di ogni fase (target: rollback completo < 5 minuti).

7. **Stretch — IaC completo.** Usa Terraform (o Pulumi) per provisionare l'infrastruttura di un ambiente n8n completo: VPC, subnet, RDS PostgreSQL, ElastiCache Redis, ECS Fargate con task definition n8n. Parametrizza il modulo per accettare `env = dev|staging|prod` e adattare sizing e configurazione.

---

## Troubleshooting — 20 problemi comuni

### 1. Workflow funziona in dev ma fallisce in staging

**Sintomo:** Il workflow si esegue correttamente in dev ma produce errori in staging.

**Causa:** Credenziali diverse, endpoint API diversi, o dati di staging con struttura inattesa.

**Soluzione:** Confronta le variabili d'ambiente tra i due ambienti con un diff. Verifica che i secret di staging siano configurati correttamente. Controlla che i dati sanitizzati di staging mantengano la stessa struttura dei dati di dev/prod.

### 2. Secret di produzione accessibili da staging

**Sintomo:** Un workflow in staging riesce a leggere i secret di prod tramite Vault o Secrets Manager.

**Causa:** Policy IAM/Vault troppo permissive, scope non limitato per ambiente.

**Soluzione:** Applica il principio del least privilege: ogni ambiente deve avere una policy che consente accesso solo ai propri secret. Aggiungi una deny esplicita ai secret di prod per tutti i ruoli non-prod. Audita le policy regolarmente.

### 3. Promotion pipeline bloccata senza errori chiari

**Sintomo:** Il merge da staging a main non triggera il deploy prod, nessun errore visibile.

**Causa:** Branch protection rules che richiedono status check non configurati, o il workflow CI non e triggerato dal tipo di merge usato.

**Soluzione:** Verifica che il workflow CI abbia `on: push: branches: [main]`. Controlla le branch protection rules su GitHub/GitLab. Assicurati che i required status checks esistano e siano associati al branch corretto.

### 4. Canary rileva falsi positivi

**Sintomo:** Il canary viene rollbackato automaticamente nonostante la nuova versione sia funzionante.

**Causa:** Volume di traffico canary troppo basso (rumore statistico), o metriche di baseline instabili, o soglie troppo aggressive.

**Soluzione:** Aumenta la percentuale canary iniziale (dal 5% al 10-15%). Allunga la finestra di osservazione (da 5 a 15 minuti). Usa metriche con smoothing (media mobile) invece di valori istantanei. Verifica che le metriche di baseline siano stabili prima di iniziare il canary.

### 5. Drift tra staging e prod non rilevato

**Sintomo:** Dopo mesi senza problemi, un deploy fallisce in prod perche staging ha una versione di runtime diversa.

**Causa:** Aggiornamenti manuali applicati solo a un ambiente, assenza di drift detection automatico.

**Soluzione:** Implementa drift detection schedulato (giornaliero). Usa IaC (Terraform/Pulumi) per tutti i componenti infrastrutturali. Vieta modifiche manuali in produzione (enforced via IAM).

### 6. Smoke test passa ma il workflow e rotto

**Sintomo:** Lo smoke test post-deploy e verde, ma i workflow reali falliscono.

**Causa:** Lo smoke test verifica solo health check e disponibilita API, non la logica di business.

**Soluzione:** Aggiungi test funzionali allo smoke test: triggera un workflow di test end-to-end con dati noti e verifica l'output atteso. Includi almeno un test per ogni integrazione critica (DB, API esterna, queue).

### 7. Rollback non ripristina lo stato precedente dei dati

**Sintomo:** Il rollback del codice va a buon fine, ma i dati creati dalla versione difettosa restano.

**Causa:** Il rollback copre solo il codice/container, non lo stato del database.

**Soluzione:** Per migrazioni additive, il codice precedente deve ignorare le nuove colonne (backward-compatible). Per migrazioni distruttive, prepara script di rollback dati prima del deploy. Considera point-in-time recovery per casi estremi.

### 8. Feature flag non si aggiorna senza rideploy

**Sintomo:** Si cambia un feature flag in configurazione, ma il workflow continua a usare il valore vecchio.

**Causa:** Il flag e caricato in memoria all'avvio e non ricaricato dinamicamente.

**Soluzione:** Usa un servizio di feature flag esterno (LaunchDarkly, Unleash, Flagsmith) con polling periodico. In alternativa, ricarica la configurazione da file/Vault a intervalli regolari (ogni 60 secondi) senza restart.

### 9. Pipeline CI/CD lenta — deploy da 45+ minuti

**Sintomo:** Il tempo totale dal push al deploy in staging supera i 45 minuti.

**Causa:** Test sequenziali, build non cachati, step ridondanti.

**Soluzione:** Parallelizza test unitari e integration test. Usa cache Docker layer e cache dipendenze npm/pip. Elimina step duplicati. Sposta test pesanti (E2E) a un job asincrono post-deploy che non blocca la pipeline.

### 10. Configurazione diversa tra Docker Compose locale e Kubernetes

**Sintomo:** Il workflow funziona in Docker Compose locale ma fallisce su Kubernetes.

**Causa:** Differenze in networking (service discovery), volumi, variabili d'ambiente, resource limits.

**Soluzione:** Usa la stessa immagine Docker in entrambi gli ambienti. Mantieni un `docker-compose.yml` che rispecchia la topologia Kubernetes (nomi servizi, porte, variabili). Usa ConfigMap/Secret in K8s invece di file `.env`.

### 11. Webhook non raggiunge l'ambiente corretto

**Sintomo:** Un webhook configurato su un servizio esterno (es. Stripe) invia notifiche all'ambiente sbagliato.

**Causa:** URL del webhook non aggiornato dopo cambio ambiente, o wildcard DNS non configurato.

**Soluzione:** Usa URL di webhook con prefisso ambiente esplicito (`https://staging.webhooks.example.com/...`). Automatizza la registrazione dei webhook per ambiente nello script di deploy. Verifica la corrispondenza URL-ambiente dopo ogni deploy.

### 12. Database staging pieno per dati non prunati

**Sintomo:** Staging diventa lento o esaurisce disco perche i dati di esecuzione workflow crescono indefinitamente.

**Causa:** Mancanza di retention policy in staging (che in prod e configurata).

**Soluzione:** Applica la stessa retention policy di prod anche in staging. Configura `EXECUTIONS_DATA_PRUNE=true` e `EXECUTIONS_DATA_MAX_AGE=168` (7 giorni) in staging. Aggiungi un cron job per pulizia periodica.

### 13. Secret rotazione rompe i workflow

**Sintomo:** Dopo la rotazione automatica dei secret, i workflow che usano il vecchio valore falliscono.

**Causa:** Il workflow engine non ricarica i secret dopo la rotazione.

**Soluzione:** Configura il workflow engine per ricaricare i secret periodicamente (o al prossimo avvio del workflow). Usa il pattern "dual secret" durante la rotazione: il nuovo e il vecchio secret sono entrambi validi per un periodo di transizione. Testa la rotazione in staging prima di abilitarla in prod.

### 14. Blue-green switch lascia esecuzioni orfane

**Sintomo:** Dopo lo switch da blue a green, le esecuzioni in corso su blue vengono interrotte.

**Causa:** Lo switch del load balancer e immediato, ma le esecuzioni attive su blue non hanno completato.

**Soluzione:** Implementa un drain period: prima dello switch, smetti di assegnare nuove esecuzioni a blue. Attendi il completamento delle esecuzioni in corso (con timeout). Solo dopo il drain, esegui lo switch. Per workflow molto lunghi, considera la possibilita di riprendere l'esecuzione su green.

### 15. Terraform state lock impedisce deploy paralleli

**Sintomo:** Due pipeline cercano di deployare contemporaneamente e una fallisce con "Error acquiring the state lock".

**Causa:** DynamoDB lock per lo state Terraform e acquisito dalla prima pipeline.

**Soluzione:** Non deployare lo stesso ambiente in parallelo (serializza i deploy per ambiente). Se serve parallelismo, usa state separati per componenti indipendenti (network, database, compute). Configura un timeout ragionevole per il lock.

### 16. GitOps reconciler sovrascrive modifiche manuali legittime

**Sintomo:** Un hotfix applicato manualmente in produzione viene sovrascritto dal reconciler GitOps.

**Causa:** Il reconciler riporta sempre lo stato alla versione nel repo Git — e il suo scopo.

**Soluzione:** Ogni modifica deve passare da Git, anche gli hotfix. Per hotfix urgenti: crea un branch `hotfix/xxx`, applica la modifica, apri PR direttamente su `main`, merga con fast-track approval. Il reconciler poi applica la versione corretta.

### 17. Variabili d'ambiente mancanti dopo deploy

**Sintomo:** Il workflow engine si avvia ma fallisce immediatamente con errori di configurazione mancante.

**Causa:** Il deploy non ha iniettato tutte le variabili d'ambiente necessarie, o il secret manager e irraggiungibile.

**Soluzione:** Aggiungi un health check all'avvio che verifica la presenza di tutte le variabili richieste. Fallisci all'avvio (fail fast) con un messaggio chiaro che elenca le variabili mancanti. Includi la verifica delle variabili nello smoke test.

### 18. Monitoring diverso tra ambienti causa alert persi

**Sintomo:** Un problema che sarebbe stato rilevato in prod non genera alert in staging perche il monitoring e configurato diversamente.

**Causa:** Il monitoring di staging e una versione ridotta di quello di prod, senza le stesse soglie di alert.

**Soluzione:** Usa la stessa configurazione di alerting in staging e prod (stesse regole, stesse soglie), ma con canali di notifica diversi (Slack #staging-alerts vs #prod-alerts). Cosi i problemi vengono intercettati in staging prima di arrivare in prod.

### 19. Container image diversa tra ambienti

**Sintomo:** Il workflow funziona in staging ma fallisce in prod con errori di runtime.

**Causa:** L'immagine Docker viene ricostruita per ogni ambiente invece di essere promossa immutabilmente.

**Soluzione:** Costruisci l'immagine una sola volta (nel job `build`). Tagga con lo SHA del commit. Promuovi lo stesso digest (non solo tag) da dev a staging a prod. Verifica il digest nell'health check: `image_digest` nel response body.

### 20. CI/CD pipeline fallisce per rate limiting API esterne

**Sintomo:** I test di integrazione falliscono in modo intermittente con errori 429 (Too Many Requests).

**Causa:** I test usano le API sandbox dei servizi esterni (Stripe, Sendgrid), che hanno rate limit anche in modalita test.

**Soluzione:** Usa mock/stub per i test unitari. Per i test di integrazione, usa un server di mock locale (WireMock, Prism) che replica le risposte API senza colpire il servizio reale. Riserva le chiamate API reali solo per gli smoke test post-deploy (poche chiamate).

---

## FAQ — 20 domande e risposte

### 1. Quanti ambienti servono realmente?

Il minimo pratico e tre: dev, staging, prod. Per organizzazioni con esigenze di compliance (HIPAA, PCI-DSS, GDPR), un quarto ambiente dedicato ai test di sicurezza e consigliato. Team molto grandi aggiungono spesso un ambiente di "integration" dove le feature di piu team convergono prima di staging.

### 2. Staging deve avere le stesse dimensioni di prod?

No, ma deve avere la stessa *topologia*. Se prod ha 3 nodi dietro un load balancer, staging ne ha almeno 2. Le dimensioni delle macchine possono essere ridotte (t3.medium invece di t3.large), ma l'architettura deve essere identica per catturare problemi di concorrenza, failover e networking.

### 3. Come gestire i dati in staging?

Tre approcci in ordine di preferenza: (1) Snapshot sanitizzato di prod — rimuovi PII (email, nomi, telefoni) ma mantieni la struttura e il volume. (2) Dataset sintetico generato — simula il volume e la distribuzione dei dati reali. (3) Subset di prod — un campione rappresentativo sanitizzato. L'approccio peggiore e usare solo fixture/seed: non cattura problemi legati a volumi reali.

### 4. Feature flag o branch per ambiente?

Entrambi, per scopi diversi. I branch per ambiente (dev/staging/main) controllano *quale codice* e deployato. I feature flag controllano *quale comportamento* e attivo a runtime. Un feature flag permette di deployare codice nuovo in prod ma tenerlo disabilitato — separando il deploy dalla release.

### 5. Come evitare che i secret di prod finiscano in dev?

(1) Account/progetto cloud separato per prod. (2) Secret manager con policy per ambiente — ogni service account accede solo ai propri secret. (3) Deny esplicito: i ruoli non-prod hanno una policy deny su `secret/prod/*`. (4) Audit log attivi per ogni accesso ai secret. (5) Rotazione: se un secret prod viene esposto, e rotabile in minuti.

### 6. Quando usare canary vs blue-green?

Canary quando il traffico e sufficiente per avere significativita statistica (centinaia di richieste al minuto). Blue-green quando il traffico e basso o quando serve zero-downtime assoluto con rollback istantaneo. Per workflow batch (non HTTP), blue-green e generalmente piu appropriato perche non c'e traffico da splittare.

### 7. Come testare workflow asincroni (code, eventi)?

(1) In dev: usa code in-memory o embedded (BullMQ con Redis locale). (2) In staging: code reali con dati di test dedicati. (3) Per i test automatici: pubblica un messaggio, attendi l'evento di completamento con timeout esplicito (30s), verifica il risultato. Evita sleep fissi nei test — usa polling con backoff.

### 8. GitOps e obbligatorio per multi-env?

No, ma e fortemente consigliato per ambienti prod. GitOps fornisce: audit trail completo (chi ha cambiato cosa, quando), riconciliazione automatica (drift corretto automaticamente), rollback tramite git revert. Per team piccoli con 1-2 workflow, il deploy manuale via CLI e accettabile per dev/staging.

### 9. Come gestire hotfix urgenti con promotion pipeline?

(1) Crea un branch `hotfix/xxx` da `main`. (2) Implementa il fix. (3) Apri PR su `main` con label `hotfix` — questo abilita fast-track review (1 approvatore invece di 2). (4) Merge e deploy automatico. (5) Backport il fix su `staging` e `develop` con cherry-pick. Il fix deve comunque passare dallo smoke test.

### 10. Quanti smoke test sono sufficienti?

Per un workflow engine: (1) Health check — il servizio risponde. (2) API check — l'API restituisce la lista workflow. (3) Workflow trigger — un workflow di test end-to-end si completa. (4) Integrazione DB — il DB e raggiungibile e lo schema e corretto. (5) Integrazione coda — un messaggio di test viene pubblicato e consumato. Totale minimo: 5. Tempo target: sotto i 2 minuti.

### 11. Come gestire migrazioni database nella promotion?

Le migrazioni devono essere: (1) Additive-only nella release corrente (aggiungi colonne, non rimuoverle). (2) Backward-compatible (il codice precedente funziona con il nuovo schema). (3) Testate in staging con dati realistici prima della promotion a prod. (4) Reversibili dove possibile (migration down). Le drop di colonne/tabelle avvengono nella release *successiva*, quando il codice vecchio non e piu in uso.

### 12. Posso usare lo stesso cluster Kubernetes per tutti gli ambienti?

Si, con namespace separati e network policy rigorose. Ma per prod e consigliato un cluster dedicato: (1) Un bug nel controller Kubernetes non impatta prod se il cluster e separato. (2) Scaling di prod non compete con dev/staging per risorse. (3) Sicurezza: un'escalation in dev non raggiunge pod prod.

### 13. Come automatizzare la creazione di un nuovo ambiente?

Con IaC parametrizzato: `terraform apply -var="env=sandbox-team-a"` crea un ambiente completo identico agli altri ma con sizing ridotto. Usa un modulo Terraform/Pulumi che accetta `env` come variabile e adatta tutte le risorse. Prevedi un TTL (time-to-live) per ambienti temporanei, con cleanup automatico.

### 14. Feature flag hanno un costo di complessita?

Si. Ogni feature flag e debito tecnico se non gestito: (1) Flag temporanei devono avere una data di scadenza e un ticket Jira associato. (2) Dopo il rollout al 100%, il flag e il vecchio percorso devono essere rimossi entro 30 giorni. (3) Audita i flag attivi mensilmente. (4) Non superare 20 flag attivi contemporaneamente — oltre questa soglia la complessita diventa difficile da gestire.

### 15. Come gestire il rollback di un workflow stateful?

Per workflow che mantengono stato (es. saga, long-running process): (1) Lo stato delle esecuzioni in corso deve essere preservato durante il rollback. (2) Le nuove esecuzioni usano la versione precedente. (3) Le esecuzioni in corso possono continuare sulla versione nuova (se non e crashata) o essere riprese dalla versione precedente (se lo stato e serializzabile). (4) Caso peggiore: le esecuzioni in corso vengono marcate come "needs manual review".

### 16. CI/CD: GitHub Actions o GitLab CI per workflow di automazione?

Entrambi sono adatti. GitHub Actions: migliore ecosistema di action pre-costruite, `environment` con approval gate nativi, integration con GitHub Packages per container. GitLab CI: `environment` con deploy board visivo, auto-devops, runner self-hosted piu semplici da gestire. Scegli in base a dove risiede il codice. Non migrare solo per la CI.

### 17. Come monitorare la promotion pipeline stessa?

(1) Dashboard con metriche della pipeline: tempo medio di deploy, tasso di successo, tempo medio di rollback. (2) Alert quando una pipeline e bloccata da piu di N minuti. (3) Metriche DORA: deployment frequency, lead time for changes, change failure rate, time to recover. (4) Audit log: chi ha approvato quale promozione, quando.

### 18. Serve un ambiente di pre-prod separato da staging?

Per la maggior parte dei team, no. Staging e sufficiente se: usa dati sanitizzati di prod, ha la stessa topologia di prod, esegue tutti i test automatici. Un pre-prod separato e giustificato quando: (1) Staging e usato per demo/UAT e non puo essere rotto. (2) Servono test di carico che non devono impattare staging. (3) Compliance richiede un ambiente certificato separato.

### 19. Come sincronizzare workflow n8n tra ambienti senza API?

Per versioni di n8n senza API di management: (1) Export manuale via UI → JSON → commit in Git. (2) Import manuale via UI nell'ambiente target. (3) Per automazione parziale: accedi direttamente al database PostgreSQL di n8n per export/import workflow (tabella `workflow_entity`). Attenzione: i campi `credential_id` sono environment-specific e devono essere rimappati.

### 20. Come gestire i costi di ambienti multipli?

(1) Dev e staging con sizing ridotto (t3.small/micro). (2) Dev spento fuori orario lavorativo (cron per stop/start). (3) Ambienti temporanei (feature branch env) con TTL automatico. (4) Spot instances per dev e staging. (5) Condivisione risorse: un solo cluster RDS con database separati per dev/staging (non per prod). (6) Monitora i costi per ambiente con tag cloud (tag `env=dev|staging|prod` su ogni risorsa).

---

## Auto-valutazione

1. Perche 3 env minimi?
2. Secret promotion: come gestire?
3. Smoke test: cosa includere?
4. Canary deploy: criteri di rollout.
5. Qual e la differenza tra promotion manuale, automatica condizionale e canary progressiva? Quando scegliere ciascuna?
6. Come si implementa il drift detection tra ambienti? Quali componenti devono avere parita?
7. Spiega il principio dell'artefatto immutabile: perche non si ricostruisce l'immagine per ogni ambiente?
8. Come si gestisce il rollback quando il deploy include migrazioni database?
9. Descrivi il lifecycle di un feature flag: dalla creazione al cleanup. Perche il cleanup e importante?
10. Quali sono i vantaggi e gli svantaggi di GitOps per la gestione di workflow di automazione rispetto al deploy manuale?

---

## Letture primarie consigliate

- Atlassian — Continuous deployment best practices. https://www.atlassian.com/continuous-delivery/
- Google SRE — Release Engineering. https://sre.google/sre-book/release-engineering/
- Martin Fowler — BlueGreenDeployment. https://martinfowler.com/bliki/BlueGreenDeployment.html
- Martin Fowler — CanaryRelease. https://martinfowler.com/bliki/CanaryRelease.html
- Martin Fowler — FeatureToggle (Feature Flags). https://martinfowler.com/articles/feature-toggles.html
- HashiCorp — Terraform Best Practices. https://developer.hashicorp.com/terraform/cloud-docs/recommended-practices
- Argo Rollouts — Progressive Delivery. https://argoproj.github.io/argo-rollouts/
- GitOps Working Group — Principles. https://opengitops.dev/
- n8n docs — Environment Variables. https://docs.n8n.io/hosting/configuration/environment-variables/

---

## Collegamenti incrociati

- Modulo 07 — governance.
- Modulo 18 — versioning rollback.
- Modulo 06 — testing e qualita.
- Modulo 09 — n8n guida completa (self-hosted).
- Modulo 13 — Ansible automazione infrastruttura.
- Modulo 15 — webhook security HMAC verifica.
- Modulo 17 — retry e idempotency pattern.
- Modulo 23 — osservabilita workflow (OTel).
- Modulo 24 — audit logging e compliance.

---

## Glossario locale

| Termine | Definizione |
|---|---|
| **Dev / Staging / Prod** | Ambienti tipici di promozione. |
| **Promotion pipeline** | Movimento codice/config dev → prod. |
| **Smoke test** | Test rapido post-deploy. |
| **Canary deploy** | Rilascio progressivo a % utenti. |
| **Manual approval gate** | Step richiede approvazione umana. |
| **Artefatto immutabile** | Container/pacchetto identico in tutti gli ambienti; cambia solo la configurazione iniettata. |
| **Drift** | Divergenza progressiva tra ambienti che dovrebbero essere strutturalmente identici. |
| **Drift detection** | Processo automatico che rileva e segnala divergenze tra ambienti. |
| **GitOps** | Pratica in cui Git e l'unica fonte di verita per lo stato desiderato del sistema. |
| **Reconciler** | Operatore (umano o automatico) che allinea lo stato reale al stato dichiarato in Git. |
| **Blue-green deployment** | Due ambienti identici (blue/green); il traffico viene switchato dall'uno all'altro. |
| **Feature flag** | Interruttore a runtime che abilita/disabilita una funzionalita senza rideploy. |
| **Kill switch** | Feature flag di emergenza: disabilita una feature istantaneamente in caso di problemi. |
| **Sealed Secrets** | Pattern Kubernetes: secret cifrati committabili in Git, decifrati solo nel cluster. |
| **IaC (Infrastructure-as-Code)** | Infrastruttura definita in file versionati (Terraform, Pulumi, CloudFormation). |
| **Backward-compatible migration** | Migrazione database che non rompe la compatibilita con il codice della versione precedente. |
| **Canary analysis** | Confronto automatico delle metriche tra la versione canary e quella stabile. |
| **Drain period** | Periodo in cui un ambiente smette di ricevere nuove richieste ma completa quelle in corso. |
| **Ring-based deployment** | Rilascio progressivo a gruppi concentrici (ring 0 = team interno, ring 1 = beta, ring 2 = tutti). |
| **Environment parity** | Identita strutturale tra ambienti (stessa topologia, versioni, schema). |
| **DORA metrics** | Quattro metriche chiave per le performance di delivery: deployment frequency, lead time, change failure rate, MTTR. |
| **Kustomize** | Strumento Kubernetes per gestire varianti di configurazione (base + overlay per ambiente). |
| **Argo Rollouts** | Controller Kubernetes per deployment canary e blue-green con analysis automatica. |
