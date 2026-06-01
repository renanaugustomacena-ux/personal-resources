---
corso: "GitHub e Git Actions"
fase: "4 — GitHub Actions"
modulo: 19
titolo: "GitHub Actions: Ricette CI/CD — Guida Approfondita"
versione: "GitHub Actions 2024"
livello: "Avanzato"
prerequisiti: ["GitHub Actions Avanzate (modulo 18)", "Docker e container", "CI/CD concetti base"]
obiettivi:
  - "Implementare pipeline CI complete per Node.js, Python, Go e Rust con lint, test e build"
  - "Costruire pipeline CD con deploy multi-ambiente (staging, production) e approvazione manuale"
  - "Configurare build e push di immagini Docker con caching multi-layer e registri multipli"
  - "Integrare security scanning (CodeQL, Trivy, Gitleaks) e performance testing (Lighthouse, k6) nella CI"
  - "Automatizzare release con semantic-release, changelog e notifiche Slack/email"
tag: [github-actions, ci-cd, docker, deploy, security-scanning, lighthouse, semantic-release, oidc, terraform, k6]
---

# GitHub Actions: Ricette CI/CD — Guida Approfondita

> **Modulo 19** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al termine di questo modulo sarai in grado di:
>
> 1. Implementare pipeline CI complete per Node.js, Python, Go e Rust con lint, test e build
> 2. Costruire pipeline CD con deploy multi-ambiente (staging, production) e approvazione manuale
> 3. Configurare build e push di immagini Docker con caching multi-layer e registri multipli
> 4. Integrare security scanning (CodeQL, Trivy, Gitleaks) e performance testing (Lighthouse, k6) nella CI
> 5. Automatizzare release con semantic-release, changelog e notifiche Slack/email

## Idee guida
1. **Explicit `permissions: {}` minimo necessario.**
2. **SHA-pinning + Renovate: `actions/checkout@8e5e7e5...` poi auto-update.**
3. **`concurrency` per cancel duplicate run su PR push.**
4. **Environment protection: manual approval per prod deploy.**


## Indice
- [Panoramica](#panoramica)
- [Node.js CI: Lint, Test, Build](#nodejs-ci-lint-test-build)
- [Python CI: pytest, mypy, black](#python-ci-pytest-mypy-black)
- [Docker Build e Push a GHCR](#docker-build-e-push-a-ghcr)
- [Multi-Platform Docker Builds](#multi-platform-docker-builds)
- [Deploy su AWS](#deploy-su-aws)
- [Deploy su Azure](#deploy-su-azure)
- [Deploy su GCP](#deploy-su-gcp)
- [Terraform Plan/Apply Workflow](#terraform-planapply-workflow)
- [Release Automation con semantic-release](#release-automation-con-semantic-release)
- [Notifiche: Slack e Email](#notifiche-slack-e-email)
- [Security Scanning in CI](#security-scanning-in-ci)
- [Performance Testing in CI](#performance-testing-in-ci)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Go CI: Lint, Test, Build e Cross-Compilation](#go-ci-lint-test-build-e-cross-compilation)
- [Rust CI: Clippy, Test, Build e Release Binaries](#rust-ci-clippy-test-build-e-release-binaries)
- [Monorepo CI con Turborepo e Nx](#monorepo-ci-con-turborepo-e-nx)
- [Matrix Testing Avanzato Multi-OS e Multi-Versione](#matrix-testing-avanzato-multi-os-e-multi-versione)
- [Reusable Workflows e Composite Actions](#reusable-workflows-e-composite-actions)
- [Deploy Multi-Ambiente con Strategie Avanzate](#deploy-multi-ambiente-con-strategie-avanzate)
- [Kubernetes Deployment con Helm e ArgoCD](#kubernetes-deployment-con-helm-e-argocd)
  - [Flux CD come Alternativa GitOps](#flux-cd-come-alternativa-gitops)
- [Database Migration in CI/CD](#database-migration-in-cicd)
  - [Liquibase Migration Workflow](#liquibase-migration-workflow)
- [Terraform Drift Detection e Multi-Workspace](#terraform-drift-detection-e-multi-workspace)
- [OIDC e Workload Identity Federation](#oidc-e-workload-identity-federation)
- [Cache Optimization Avanzata](#cache-optimization-avanzata)
- [Self-Hosted Runners e Actions Runner Controller](#self-hosted-runners-e-actions-runner-controller)
- [Dockerfile Ottimizzati per CI/CD](#dockerfile-ottimizzati-per-cicd)
- [Release Automation Avanzata e Changelog](#release-automation-avanzata-e-changelog)
- [Pipeline E2E: dal Commit alla Produzione](#pipeline-e2e-dal-commit-alla-produzione)
- [E2E Testing con Playwright e Cypress](#e2e-testing-con-playwright-e-cypress)
- [Mobile App CI/CD: React Native e Flutter](#mobile-app-cicd-react-native-e-flutter)
- [Performance Testing Avanzato con Artillery](#performance-testing-avanzato-con-artillery)
- [Anti-Pattern e Errori Comuni](#anti-pattern-e-errori-comuni)
- [Riferimenti](#riferimenti)

---

## Panoramica

Questa guida raccoglie ricette pratiche e pronte all'uso per i casi d'uso CI/CD più comuni con GitHub Actions. Ogni ricetta è un workflow completo e testato che può essere adattato alle esigenze specifiche del progetto. Dall'integrazione continua per Node.js e Python, al build e push di immagini Docker multi-piattaforma, dal deploy su cloud provider (AWS, Azure, GCP) all'automazione delle release con semantic-release, ogni ricetta include la configurazione completa, le spiegazioni delle scelte di design e le varianti per scenari comuni.

L'obiettivo è fornire una raccolta di riferimento che acceleri l'implementazione di pipeline CI/CD robuste e sicure, seguendo le best practices del settore.

---

## Node.js CI: Lint, Test, Build

```yaml
# .github/workflows/node-ci.yml
name: Node.js CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      - name: ESLint
        run: npx eslint . --format=json --output-file=eslint-report.json
        continue-on-error: true

      - name: Annotate ESLint results
        if: always()
        uses: ataylorme/eslint-annotate-action@v2
        with:
          report-json: eslint-report.json

      - name: Prettier check
        run: npx prettier --check .

      - name: TypeScript check
        run: npx tsc --noEmit

  test:
    name: Test (Node ${{ matrix.node-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        node-version: [18, 20, 22]

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - run: npm ci

      - name: Run tests with coverage
        run: npx jest --coverage --ci --reporters=default --reporters=jest-junit
        env:
          DATABASE_URL: postgres://test:test@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379

      - name: Upload coverage
        if: matrix.node-version == 20
        uses: codecov/codecov-action@v3
        with:
          files: coverage/lcov.info
          fail_ci_if_error: false

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-node-${{ matrix.node-version }}
          path: junit.xml

  build:
    name: Build
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci
      - run: npm run build

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 7

      - name: Bundle size check
        run: |
          SIZE=$(du -sb dist/ | cut -f1)
          MAX_SIZE=5242880  # 5 MB
          echo "Bundle size: $((SIZE / 1024)) KB"
          if [ "$SIZE" -gt "$MAX_SIZE" ]; then
            echo "::warning::Bundle size exceeds 5 MB!"
          fi
          echo "## Build Summary" >> "$GITHUB_STEP_SUMMARY"
          echo "- Bundle size: $((SIZE / 1024)) KB" >> "$GITHUB_STEP_SUMMARY"
```

---

## Python CI: pytest, mypy, black

```yaml
# .github/workflows/python-ci.yml
name: Python CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: python-ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: Lint & Format
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install ruff mypy black isort

      - name: Ruff lint
        run: ruff check . --output-format=github

      - name: Black format check
        run: black --check --diff .

      - name: isort check
        run: isort --check-only --diff .

      - name: mypy type check
        run: mypy src/ --ignore-missing-imports

  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: |
          pytest tests/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=html \
            --junitxml=junit.xml \
            -v
        env:
          DATABASE_URL: postgres://test:test@localhost:5432/testdb

      - name: Upload coverage
        if: matrix.python-version == '3.12'
        uses: codecov/codecov-action@v3
        with:
          files: coverage.xml

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-python-${{ matrix.python-version }}
          path: |
            junit.xml
            htmlcov/

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install safety
        run: pip install safety pip-audit

      - name: Check for known vulnerabilities
        run: pip-audit -r requirements.txt

      - name: Bandit security linter
        run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json || true
          bandit -r src/ -f screen
```

---

## Docker Build e Push a GHCR

```yaml
# .github/workflows/docker-publish.yml
name: Docker Build and Push

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

permissions:
  contents: read
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GHCR
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=sha,prefix=
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            BUILD_DATE=${{ github.event.repository.updated_at }}
            VCS_REF=${{ github.sha }}

      - name: Scan image for vulnerabilities
        if: github.event_name != 'pull_request'
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy scan results
        if: always() && github.event_name != 'pull_request'
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

---

## Multi-Platform Docker Builds

```yaml
# .github/workflows/docker-multiplatform.yml
name: Multi-Platform Docker Build

on:
  push:
    tags: ['v*']

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

permissions:
  contents: read
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64,linux/arm/v7
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          provenance: true
          sbom: true
```

---

## Deploy su AWS

```yaml
# .github/workflows/deploy-aws.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://app.example.com
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsDeployRole
          aws-region: eu-west-1

      # Opzione A: Deploy a ECS
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, and push image to ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: my-app
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster my-cluster \
            --service my-service \
            --force-new-deployment

      # Opzione B: Deploy a S3 + CloudFront (static site)
      - name: Build static site
        run: npm ci && npm run build

      - name: Deploy to S3
        run: |
          aws s3 sync dist/ s3://my-bucket/ \
            --delete \
            --cache-control "public, max-age=31536000, immutable" \
            --exclude "index.html"
          aws s3 cp dist/index.html s3://my-bucket/index.html \
            --cache-control "public, max-age=0, must-revalidate"

      - name: Invalidate CloudFront cache
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CF_DISTRIBUTION_ID }} \
            --paths "/*"

      # Opzione C: Deploy a Lambda
      - name: Deploy Lambda function
        run: |
          zip -r function.zip .
          aws lambda update-function-code \
            --function-name my-function \
            --zip-file fileb://function.zip
```

---

## Deploy su Azure

```yaml
# .github/workflows/deploy-azure.yml
name: Deploy to Azure

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v1
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      # Deploy a Azure App Service
      - name: Build and deploy
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'my-web-app'
          slot-name: 'staging'
          package: '.'

      # Swap staging e production
      - name: Swap slots
        run: |
          az webapp deployment slot swap \
            --resource-group my-rg \
            --name my-web-app \
            --slot staging \
            --target-slot production

      # Deploy a AKS
      - name: Set AKS context
        uses: azure/aks-set-context@v3
        with:
          resource-group: my-rg
          cluster-name: my-cluster

      - name: Deploy to AKS
        uses: azure/k8s-deploy@v4
        with:
          namespace: production
          manifests: |
            k8s/deployment.yml
            k8s/service.yml
          images: |
            myregistry.azurecr.io/myapp:${{ github.sha }}
```

---

## Deploy su GCP

```yaml
# .github/workflows/deploy-gcp.yml
name: Deploy to GCP

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to Google Cloud (OIDC)
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/123456/locations/global/workloadIdentityPools/gh-pool/providers/gh-provider'
          service_account: 'deploy@my-project.iam.gserviceaccount.com'

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      # Deploy a Cloud Run
      - name: Build and push to Artifact Registry
        run: |
          gcloud builds submit --tag \
            europe-west1-docker.pkg.dev/my-project/my-repo/my-app:${{ github.sha }}

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: my-service
          region: europe-west1
          image: europe-west1-docker.pkg.dev/my-project/my-repo/my-app:${{ github.sha }}

      # Deploy a GKE
      - name: Get GKE credentials
        uses: google-github-actions/get-gke-credentials@v2
        with:
          cluster_name: my-cluster
          location: europe-west1

      - name: Deploy to GKE
        run: |
          kubectl set image deployment/my-app \
            app=europe-west1-docker.pkg.dev/my-project/my-repo/my-app:${{ github.sha }}
          kubectl rollout status deployment/my-app --timeout=300s

      # Deploy a App Engine
      - name: Deploy to App Engine
        uses: google-github-actions/deploy-appengine@v2
        with:
          project_id: my-project
```

---

## Terraform Plan/Apply Workflow

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  push:
    branches: [main]
    paths: ['terraform/**']
  pull_request:
    branches: [main]
    paths: ['terraform/**']

permissions:
  id-token: write
  contents: read
  pull-requests: write

env:
  TF_VERSION: '1.7.0'
  TF_WORKING_DIR: 'terraform'

jobs:
  plan:
    name: Terraform Plan
    runs-on: ubuntu-latest
    outputs:
      has-changes: ${{ steps.plan.outputs.has-changes }}
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: eu-west-1

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Init
        working-directory: ${{ env.TF_WORKING_DIR }}
        run: terraform init -no-color

      - name: Terraform Validate
        working-directory: ${{ env.TF_WORKING_DIR }}
        run: terraform validate -no-color

      - name: Terraform Plan
        id: plan
        working-directory: ${{ env.TF_WORKING_DIR }}
        run: |
          terraform plan -no-color -out=tfplan -detailed-exitcode 2>&1 | tee plan-output.txt
          EXIT_CODE=${PIPESTATUS[0]}
          if [ $EXIT_CODE -eq 2 ]; then
            echo "has-changes=true" >> "$GITHUB_OUTPUT"
          else
            echo "has-changes=false" >> "$GITHUB_OUTPUT"
          fi

      - name: Comment PR with plan
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const plan = fs.readFileSync('${{ env.TF_WORKING_DIR }}/plan-output.txt', 'utf8');
            const truncated = plan.length > 65000 ? plan.substring(0, 65000) + '\n\n... (truncated)' : plan;

            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `## Terraform Plan\n\n<details>\n<summary>Show Plan</summary>\n\n\`\`\`\n${truncated}\n\`\`\`\n\n</details>`
            });

      - name: Upload plan
        uses: actions/upload-artifact@v4
        with:
          name: tfplan
          path: ${{ env.TF_WORKING_DIR }}/tfplan

  apply:
    name: Terraform Apply
    needs: plan
    if: github.event_name == 'push' && github.ref == 'refs/heads/main' && needs.plan.outputs.has-changes == 'true'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: eu-west-1

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Init
        working-directory: ${{ env.TF_WORKING_DIR }}
        run: terraform init -no-color

      - name: Download plan
        uses: actions/download-artifact@v4
        with:
          name: tfplan
          path: ${{ env.TF_WORKING_DIR }}

      - name: Terraform Apply
        working-directory: ${{ env.TF_WORKING_DIR }}
        run: terraform apply -no-color -auto-approve tfplan
```

---

## Release Automation con semantic-release

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [main]

permissions:
  contents: write
  issues: write
  pull-requests: write
  packages: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - run: npm ci

      - name: Semantic Release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
        run: npx semantic-release
```

```json
// .releaserc.json
{
  "branches": ["main"],
  "plugins": [
    ["@semantic-release/commit-analyzer", {
      "preset": "conventionalcommits",
      "releaseRules": [
        {"type": "feat", "release": "minor"},
        {"type": "fix", "release": "patch"},
        {"type": "perf", "release": "patch"},
        {"type": "revert", "release": "patch"},
        {"breaking": true, "release": "major"}
      ]
    }],
    ["@semantic-release/release-notes-generator", {
      "preset": "conventionalcommits"
    }],
    ["@semantic-release/changelog", {
      "changelogFile": "CHANGELOG.md"
    }],
    ["@semantic-release/npm"],
    ["@semantic-release/github", {
      "assets": [
        {"path": "dist/*.tar.gz", "label": "Distribution"}
      ]
    }],
    ["@semantic-release/git", {
      "assets": ["CHANGELOG.md", "package.json"],
      "message": "chore(release): ${nextRelease.version}\n\n${nextRelease.notes}"
    }]
  ]
}
```

---

## Notifiche: Slack e Email

```yaml
# Notifica Slack
jobs:
  notify:
    runs-on: ubuntu-latest
    needs: [build, test, deploy]
    if: always()
    steps:
      - name: Determine status
        id: status
        run: |
          if [ "${{ contains(needs.*.result, 'failure') }}" = "true" ]; then
            echo "status=failure" >> "$GITHUB_OUTPUT"
            echo "color=danger" >> "$GITHUB_OUTPUT"
            echo "emoji=:x:" >> "$GITHUB_OUTPUT"
          elif [ "${{ contains(needs.*.result, 'cancelled') }}" = "true" ]; then
            echo "status=cancelled" >> "$GITHUB_OUTPUT"
            echo "color=warning" >> "$GITHUB_OUTPUT"
            echo "emoji=:warning:" >> "$GITHUB_OUTPUT"
          else
            echo "status=success" >> "$GITHUB_OUTPUT"
            echo "color=good" >> "$GITHUB_OUTPUT"
            echo "emoji=:white_check_mark:" >> "$GITHUB_OUTPUT"
          fi

      - name: Send Slack notification
        uses: slackapi/slack-github-action@v1.25.0
        with:
          payload: |
            {
              "blocks": [
                {
                  "type": "header",
                  "text": {
                    "type": "plain_text",
                    "text": "${{ steps.status.outputs.emoji }} CI/CD Pipeline - ${{ steps.status.outputs.status }}"
                  }
                },
                {
                  "type": "section",
                  "fields": [
                    {"type": "mrkdwn", "text": "*Repository:*\n${{ github.repository }}"},
                    {"type": "mrkdwn", "text": "*Branch:*\n${{ github.ref_name }}"},
                    {"type": "mrkdwn", "text": "*Author:*\n${{ github.actor }}"},
                    {"type": "mrkdwn", "text": "*Commit:*\n<${{ github.event.head_commit.url }}|${{ github.sha }}>"}
                  ]
                },
                {
                  "type": "actions",
                  "elements": [
                    {
                      "type": "button",
                      "text": {"type": "plain_text", "text": "View Run"},
                      "url": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
                    }
                  ]
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          SLACK_WEBHOOK_TYPE: INCOMING_WEBHOOK

      # Email notification (con action)
      - name: Send email on failure
        if: steps.status.outputs.status == 'failure'
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 465
          secure: true
          username: ${{ secrets.SMTP_USERNAME }}
          password: ${{ secrets.SMTP_PASSWORD }}
          subject: "CI Failed: ${{ github.repository }} - ${{ github.ref_name }}"
          to: team@example.com
          from: ci@example.com
          body: |
            CI pipeline failed for ${{ github.repository }}
            Branch: ${{ github.ref_name }}
            Commit: ${{ github.sha }}
            Author: ${{ github.actor }}
            Run: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

---

## Security Scanning in CI

```yaml
# .github/workflows/security.yml
name: Security Scanning

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'

permissions:
  security-events: write
  contents: read

jobs:
  codeql:
    name: CodeQL Analysis
    runs-on: ubuntu-latest
    strategy:
      matrix:
        language: ['javascript', 'python']
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: security-extended
      - uses: github/codeql-action/analyze@v3

  dependency-scan:
    name: Dependency Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-fs.sarif'
          severity: 'CRITICAL,HIGH'

      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-fs.sarif'

  secret-scan:
    name: Secret Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  container-scan:
    name: Container Scan
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t app:scan .

      - name: Run Trivy container scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'app:scan'
          format: 'sarif'
          output: 'trivy-container.sarif'
          severity: 'CRITICAL,HIGH'

      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-container.sarif'

  license-check:
    name: License Compliance
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - name: Check licenses
        run: |
          npx license-checker --production --onlyAllow \
            "MIT;Apache-2.0;BSD-2-Clause;BSD-3-Clause;ISC;0BSD;CC0-1.0;Unlicense"
```

---

## Performance Testing in CI

```yaml
# .github/workflows/performance.yml
name: Performance Testing

on:
  pull_request:
    branches: [main]

permissions:
  pull-requests: write

jobs:
  lighthouse:
    name: Lighthouse CI
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci && npm run build

      - name: Start server
        run: npm run preview &

      - name: Wait for server
        run: npx wait-on http://localhost:4173 --timeout 30000

      - name: Run Lighthouse
        uses: treosh/lighthouse-ci-action@v11
        with:
          urls: |
            http://localhost:4173/
            http://localhost:4173/about
          uploadArtifacts: true
          temporaryPublicStorage: true
          configPath: .lighthouserc.json

  bundle-analysis:
    name: Bundle Size Analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci

      - name: Build and analyze
        run: npm run build

      - name: Bundle size
        uses: andresz1/size-limit-action@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}

  load-test:
    name: Load Test
    runs-on: ubuntu-latest
    if: contains(github.event.pull_request.labels.*.name, 'load-test')
    steps:
      - uses: actions/checkout@v4

      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
            --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D68
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
            sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update && sudo apt-get install k6

      - name: Run load test
        run: k6 run tests/load/script.js --out json=results.json

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: load-test-results
          path: results.json
```

---

## Best Practices

### Organizzazione dei Workflow

1. **Un workflow per scopo**: Separare CI, CD, security scanning e release in workflow distinti.
2. **Reusable workflows per standardizzazione**: Creare workflow riutilizzabili per pattern comuni nell'organizzazione.
3. **Naming convention**: Usare nomi descrittivi per workflow, job e step.
4. **Documentazione**: Commentare le scelte non ovvie direttamente nel YAML.

### Sicurezza

1. **OIDC per cloud provider**: Eliminare le credenziali statiche per AWS, Azure e GCP.
2. **Permessi minimi**: Specificare sempre i permessi esatti necessari.
3. **Pin delle azioni**: Usare gli hash SHA per le azioni di terze parti in workflow critici.
4. **Environment protection**: Usare gli environments con approvazione manuale per il deploy in produzione.

### Performance

1. **Caching aggressivo**: Cache di dipendenze, build intermedi e Docker layers.
2. **Parallelizzazione**: Eseguire job indipendenti in parallelo.
3. **Cancellazione**: Usare `cancel-in-progress` per evitare esecuzioni ridondanti.
4. **Paths filter**: Triggerare solo quando i file rilevanti cambiano.

### Affidabilità

1. **Retry per fallimenti transitori**: Usare `retry` per step che possono fallire per problemi di rete.
2. **Timeout**: Impostare sempre un timeout per evitare job bloccati.
3. **Fallback**: Implementare strategie di rollback per i deploy.
4. **Monitoraggio**: Aggiungere notifiche per fallimenti dei workflow critici.

---

## Troubleshooting

### Build Docker Lento

```yaml
# Usare il caching di Buildx
cache-from: type=gha
cache-to: type=gha,mode=max

# Multi-stage build per ridurre la dimensione
# Dockerfile ottimizzato per cache layers
```

### Deploy Fallisce Silenziosamente

```yaml
# Aggiungere health check dopo il deploy
- name: Health check
  run: |
    for i in $(seq 1 30); do
      STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://app.example.com/health)
      if [ "$STATUS" = "200" ]; then
        echo "Health check passed!"
        exit 0
      fi
      echo "Attempt $i: status $STATUS, retrying..."
      sleep 10
    done
    echo "Health check failed after 30 attempts"
    exit 1
```

### Terraform Plan Diverge da Apply

```yaml
# Salvare il plan come artifact e usarlo per l'apply
# NON rieseguire il plan durante l'apply
- uses: actions/upload-artifact@v4
  with:
    name: tfplan
    path: terraform/tfplan

# Nell'apply job:
- uses: actions/download-artifact@v4
- run: terraform apply -auto-approve tfplan
```

### Secrets Non Disponibili in Fork PR

```yaml
# I secrets non sono disponibili nelle PR da fork (sicurezza)
# Soluzioni:
# 1. Usare pull_request_target (ATTENZIONE: esegue codice del target branch)
# 2. Eseguire test senza segreti per le PR da fork
# 3. Usare un workflow separato che si attiva dopo l'approvazione
```

---

## Go CI: Lint, Test, Build e Cross-Compilation

Go richiede un approccio specifico alla CI per via del suo sistema di moduli, della compilazione statica e della facilità di cross-compilation nativa. Il workflow seguente copre linting con `golangci-lint`, test con race detector, build per multiple piattaforme e caching ottimizzato dei moduli Go.

```yaml
# .github/workflows/go-ci.yml
name: Go CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

concurrency:
  group: go-ci-${{ github.ref }}
  cancel-in-progress: true

env:
  GO_VERSION: '1.23'

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: ${{ env.GO_VERSION }}
          cache: true

      - name: golangci-lint
        uses: golangci/golangci-lint-action@v6
        with:
          version: latest
          args: --timeout=5m --config=.golangci.yml

      - name: Verify go.mod tidy
        run: |
          go mod tidy
          git diff --exit-code go.mod go.sum

      - name: Verify no generated files out of date
        run: |
          go generate ./...
          git diff --exit-code

  test:
    name: Test (Go ${{ matrix.go-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        go-version: ['1.22', '1.23']

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go-version }}
          cache: true

      - name: Run tests with race detector
        run: |
          go test -v -race -coverprofile=coverage.out -covermode=atomic ./...
        env:
          DATABASE_URL: postgres://test:test@localhost:5432/testdb?sslmode=disable

      - name: Check coverage threshold
        run: |
          COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
          echo "Total coverage: ${COVERAGE}%"
          echo "## Go Test Coverage: ${COVERAGE}%" >> "$GITHUB_STEP_SUMMARY"
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "::error::Coverage ${COVERAGE}% is below 80% threshold"
            exit 1
          fi

      - name: Upload coverage
        if: matrix.go-version == '1.23'
        uses: codecov/codecov-action@v3
        with:
          files: coverage.out

  build:
    name: Build
    needs: [lint, test]
    runs-on: ubuntu-latest
    strategy:
      matrix:
        goos: [linux, darwin, windows]
        goarch: [amd64, arm64]
        exclude:
          - goos: windows
            goarch: arm64

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: ${{ env.GO_VERSION }}
          cache: true

      - name: Build binary
        env:
          GOOS: ${{ matrix.goos }}
          GOARCH: ${{ matrix.goarch }}
          CGO_ENABLED: 0
        run: |
          BINARY_NAME=myapp
          if [ "$GOOS" = "windows" ]; then
            BINARY_NAME="${BINARY_NAME}.exe"
          fi
          go build -ldflags="-s -w -X main.version=${{ github.ref_name }} -X main.commit=${{ github.sha }}" \
            -o "dist/${BINARY_NAME}-${GOOS}-${GOARCH}" ./cmd/myapp

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: binary-${{ matrix.goos }}-${{ matrix.goarch }}
          path: dist/
          retention-days: 7

  release:
    name: Release
    needs: build
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: dist/
          merge-multiple: true

      - name: Create checksums
        run: |
          cd dist
          sha256sum * > checksums.txt

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          files: |
            dist/*
```

### Configurazione golangci-lint consigliata

```yaml
# .golangci.yml
run:
  timeout: 5m
  modules-download-mode: readonly

linters:
  enable:
    - errcheck
    - gosimple
    - govet
    - ineffassign
    - staticcheck
    - unused
    - gofumpt
    - goimports
    - misspell
    - unconvert
    - unparam
    - gocritic
    - revive
    - gosec

linters-settings:
  govet:
    enable-all: true
  revive:
    rules:
      - name: exported
        severity: warning
  gosec:
    excludes:
      - G104  # unhandled errors — coperto da errcheck

issues:
  max-issues-per-linter: 50
  max-same-issues: 3
```

La cross-compilation in Go non richiede toolchain esterne: basta impostare `GOOS` e `GOARCH` come variabili d'ambiente. Con `CGO_ENABLED=0` si ottiene un binario completamente statico, ideale per container `scratch` o `distroless`. La matrice `exclude` rimuove combinazioni non supportate (ad esempio `windows/arm64` per certi progetti). L'uso di `-ldflags="-s -w"` riduce la dimensione del binario eliminando i simboli di debug, mentre l'iniezione di versione e commit hash tramite `-X` consente di tracciare esattamente quale build è in esecuzione.

---

## Rust CI: Clippy, Test, Build e Release Binaries

Rust ha tempi di compilazione più lunghi rispetto a Go, rendendo il caching particolarmente critico. Il workflow seguente implementa una pipeline CI completa con formatting check, linting via Clippy, test paralleli, build ottimizzato e release con cross-compilation.

```yaml
# .github/workflows/rust-ci.yml
name: Rust CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: rust-ci-${{ github.ref }}
  cancel-in-progress: true

env:
  CARGO_TERM_COLOR: always
  RUSTFLAGS: -Dwarnings

jobs:
  check:
    name: Check & Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy

      - uses: Swatinem/rust-cache@v2
        with:
          cache-on-failure: true

      - name: Check formatting
        run: cargo fmt --all -- --check

      - name: Clippy lints
        run: cargo clippy --all-targets --all-features -- -D warnings

      - name: Check for security advisories
        run: |
          cargo install cargo-audit --locked
          cargo audit

  test:
    name: Test (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]

    steps:
      - uses: actions/checkout@v4

      - uses: dtolnay/rust-toolchain@stable

      - uses: Swatinem/rust-cache@v2
        with:
          cache-on-failure: true

      - name: Run tests
        run: cargo test --all-features --workspace -- --test-threads=4

      - name: Run doc tests
        run: cargo test --doc --workspace

  coverage:
    name: Coverage
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: Swatinem/rust-cache@v2

      - name: Install cargo-llvm-cov
        run: cargo install cargo-llvm-cov --locked

      - name: Generate coverage
        run: cargo llvm-cov --all-features --workspace --lcov --output-path lcov.info

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: lcov.info

  release:
    name: Release (${{ matrix.target }})
    needs: [check, test]
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ${{ matrix.os }}
    permissions:
      contents: write
    strategy:
      matrix:
        include:
          - target: x86_64-unknown-linux-gnu
            os: ubuntu-latest
            archive: tar.gz
          - target: x86_64-apple-darwin
            os: macos-latest
            archive: tar.gz
          - target: aarch64-apple-darwin
            os: macos-latest
            archive: tar.gz
          - target: x86_64-pc-windows-msvc
            os: windows-latest
            archive: zip

    steps:
      - uses: actions/checkout@v4

      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.target }}

      - uses: Swatinem/rust-cache@v2

      - name: Build release binary
        run: cargo build --release --target ${{ matrix.target }}

      - name: Package (Unix)
        if: matrix.archive == 'tar.gz'
        run: |
          cd target/${{ matrix.target }}/release
          tar czf ../../../myapp-${{ matrix.target }}.tar.gz myapp
          cd ../../..
          sha256sum myapp-${{ matrix.target }}.tar.gz > myapp-${{ matrix.target }}.tar.gz.sha256

      - name: Package (Windows)
        if: matrix.archive == 'zip'
        shell: pwsh
        run: |
          Compress-Archive -Path "target/${{ matrix.target }}/release/myapp.exe" `
            -DestinationPath "myapp-${{ matrix.target }}.zip"

      - name: Upload Release Asset
        uses: softprops/action-gh-release@v2
        with:
          files: |
            myapp-*.tar.gz
            myapp-*.tar.gz.sha256
            myapp-*.zip
```

Il caching Rust merita attenzione speciale. L'azione `Swatinem/rust-cache@v2` gestisce automaticamente la cache della directory `target/` e del registry cargo. L'opzione `cache-on-failure: true` è importante perché le compilazioni Rust possono fallire dopo aver compilato molte dipendenze — senza questa opzione, quel lavoro di compilazione andrebbe perso. Il flag `RUSTFLAGS: -Dwarnings` trasforma tutti i warning in errori, garantendo che il codice sia pulito prima del merge. `cargo-audit` verifica che le dipendenze non abbiano CVE note, complementando la scansione con Trivy a livello di progetto.

---

## Monorepo CI con Turborepo e Nx

I monorepo richiedono strategie CI specifiche per evitare di eseguire l'intera suite di test e build ad ogni push. Sia Turborepo che Nx offrono change detection intelligente che determina quali pacchetti sono stati modificati e quali devono essere ricostruiti.

### Turborepo Monorepo

```yaml
# .github/workflows/monorepo-turbo.yml
name: Monorepo CI (Turborepo)

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: monorepo-${{ github.ref }}
  cancel-in-progress: true

jobs:
  detect-changes:
    name: Detect Changes
    runs-on: ubuntu-latest
    outputs:
      packages: ${{ steps.filter.outputs.changes }}
      has-changes: ${{ steps.filter.outputs.changes != '[]' }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            web:
              - 'apps/web/**'
              - 'packages/ui/**'
              - 'packages/shared/**'
            api:
              - 'apps/api/**'
              - 'packages/shared/**'
              - 'packages/database/**'
            docs:
              - 'apps/docs/**'
              - 'packages/ui/**'

  ci:
    name: CI
    needs: detect-changes
    if: needs.detect-changes.outputs.has-changes == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Turbo cache
        uses: actions/cache@v4
        with:
          path: .turbo
          key: turbo-${{ runner.os }}-${{ github.sha }}
          restore-keys: |
            turbo-${{ runner.os }}-

      - name: Lint affected packages
        run: pnpm turbo lint --filter='...[origin/main]'

      - name: Type check affected packages
        run: pnpm turbo typecheck --filter='...[origin/main]'

      - name: Test affected packages
        run: pnpm turbo test --filter='...[origin/main]'

      - name: Build affected packages
        run: pnpm turbo build --filter='...[origin/main]'

      - name: Summary
        run: |
          echo "## Turborepo CI Summary" >> "$GITHUB_STEP_SUMMARY"
          echo "Changed packages: ${{ needs.detect-changes.outputs.packages }}" >> "$GITHUB_STEP_SUMMARY"
          pnpm turbo build --filter='...[origin/main]' --dry-run=json | \
            jq -r '.packages[]' >> "$GITHUB_STEP_SUMMARY" || true
```

### Nx Monorepo

```yaml
# .github/workflows/monorepo-nx.yml
name: Monorepo CI (Nx)

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: nx-ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  ci:
    name: Nx CI
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: nrwl/nx-set-shas@v4
        id: nx-shas

      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile

      - name: Nx affected lint
        run: pnpm nx affected --target=lint --base=${{ steps.nx-shas.outputs.base }} --head=${{ steps.nx-shas.outputs.head }}

      - name: Nx affected test
        run: pnpm nx affected --target=test --base=${{ steps.nx-shas.outputs.base }} --head=${{ steps.nx-shas.outputs.head }}

      - name: Nx affected build
        run: pnpm nx affected --target=build --base=${{ steps.nx-shas.outputs.base }} --head=${{ steps.nx-shas.outputs.head }}

      - name: Nx affected e2e
        run: pnpm nx affected --target=e2e --base=${{ steps.nx-shas.outputs.base }} --head=${{ steps.nx-shas.outputs.head }}
```

La differenza fondamentale tra i due approcci: Turborepo usa `--filter='...[origin/main]'` per determinare i pacchetti modificati rispetto al branch base, mentre Nx usa `nx affected` con `--base` e `--head` impostati dall'azione `nrwl/nx-set-shas`. Entrambi supportano il task graph caching, dove i risultati delle task precedenti vengono riutilizzati se gli input non sono cambiati. Con `dorny/paths-filter` si ottiene un controllo ancora più granulare, permettendo di saltare interi job quando nessun file rilevante è stato modificato. Nei monorepo di grandi dimensioni, l'esecuzione selettiva riduce tipicamente i tempi CI del 70-80%, passando da pipeline di 15 minuti a 3-4 minuti.

---

## Matrix Testing Avanzato Multi-OS e Multi-Versione

La strategia matrix consente di testare il codice su molteplici combinazioni di sistema operativo, versione del linguaggio e configurazione. Le tecniche avanzate includono matrici dinamiche, filtri di esclusione/inclusione e generazione condizionale.

### Matrix con Include/Exclude

```yaml
# .github/workflows/matrix-advanced.yml
name: Advanced Matrix Testing

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    name: Test (${{ matrix.os }} / ${{ matrix.node-version }} / ${{ matrix.database }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        node-version: [18, 20, 22]
        database: [postgres, sqlite]
        exclude:
          # SQLite su Windows con Node 18 ha problemi noti di binding
          - os: windows-latest
            node-version: 18
            database: sqlite
          # macOS + Postgres richiede setup extra, testare solo su Linux
          - os: macos-latest
            database: postgres
        include:
          # Aggiungere test con Node canary solo su Linux
          - os: ubuntu-latest
            node-version: 23
            database: postgres
            experimental: true

    continue-on-error: ${{ matrix.experimental || false }}

    services:
      postgres:
        image: ${{ matrix.database == 'postgres' && 'postgres:16' || '' }}
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - run: npm ci

      - name: Run tests
        run: npm test
        env:
          DB_TYPE: ${{ matrix.database }}
          DATABASE_URL: ${{ matrix.database == 'postgres' && 'postgres://test:test@localhost:5432/testdb' || 'sqlite::memory:' }}

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: results-${{ matrix.os }}-node${{ matrix.node-version }}-${{ matrix.database }}
          path: test-results/
```

### Matrix Dinamica Generata da Job Precedente

```yaml
# .github/workflows/dynamic-matrix.yml
name: Dynamic Matrix

on:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  generate-matrix:
    name: Generate Matrix
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4

      - name: Determine matrix
        id: set-matrix
        run: |
          # Generare matrice basata sui file modificati
          CHANGED=$(git diff --name-only HEAD~1 HEAD)

          MATRIX='{"include":[]}'

          if echo "$CHANGED" | grep -q "^packages/api/"; then
            MATRIX=$(echo "$MATRIX" | jq '.include += [{"package":"api","test_cmd":"npm run test:api"}]')
          fi

          if echo "$CHANGED" | grep -q "^packages/web/"; then
            MATRIX=$(echo "$MATRIX" | jq '.include += [{"package":"web","test_cmd":"npm run test:web"}]')
          fi

          if echo "$CHANGED" | grep -q "^packages/shared/"; then
            MATRIX=$(echo "$MATRIX" | jq '.include += [{"package":"shared","test_cmd":"npm run test:shared"}]')
          fi

          # Fallback: se nessun pacchetto specifico, testare tutto
          if [ "$(echo "$MATRIX" | jq '.include | length')" -eq 0 ]; then
            MATRIX='{"include":[{"package":"all","test_cmd":"npm test"}]}'
          fi

          echo "matrix=$MATRIX" >> "$GITHUB_OUTPUT"
          echo "## Generated Matrix" >> "$GITHUB_STEP_SUMMARY"
          echo '```json' >> "$GITHUB_STEP_SUMMARY"
          echo "$MATRIX" | jq . >> "$GITHUB_STEP_SUMMARY"
          echo '```' >> "$GITHUB_STEP_SUMMARY"

  test:
    name: Test ${{ matrix.package }}
    needs: generate-matrix
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix: ${{ fromJson(needs.generate-matrix.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: ${{ matrix.test_cmd }}
```

La matrice dinamica è particolarmente utile nei monorepo dove i pacchetti da testare dipendono dai file modificati. Il job `generate-matrix` analizza il diff e produce una matrice JSON che viene consumata dal job `test` tramite `fromJson()`. Il pattern `fail-fast: false` per la matrice su main branch garantisce che tutti i test vengano eseguiti anche se uno fallisce, fornendo un quadro completo dello stato del codice. Al contrario, `fail-fast: true` sulle PR permette di ottenere feedback più rapido fermando tutto al primo fallimento. L'uso di `continue-on-error` per le versioni sperimentali consente di monitorare la compatibilità futura senza bloccare la pipeline.

---

## Reusable Workflows e Composite Actions

I reusable workflows e le composite actions sono i due meccanismi principali per eliminare la duplicazione tra workflow. Un reusable workflow incapsula un intero set di job, mentre una composite action raggruppa più step in una singola unità riutilizzabile all'interno di un job.

### Reusable Workflow per CI Generica

```yaml
# .github/workflows/reusable-node-ci.yml
name: Reusable Node.js CI

on:
  workflow_call:
    inputs:
      node-version:
        description: 'Node.js version'
        required: false
        type: string
        default: '20'
      working-directory:
        description: 'Working directory'
        required: false
        type: string
        default: '.'
      run-e2e:
        description: 'Run E2E tests'
        required: false
        type: boolean
        default: false
    secrets:
      NPM_TOKEN:
        required: false
      CODECOV_TOKEN:
        required: false

permissions:
  contents: read

jobs:
  lint:
    name: Lint
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
          cache-dependency-path: ${{ inputs.working-directory }}/package-lock.json
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  test:
    name: Test
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
          cache-dependency-path: ${{ inputs.working-directory }}/package-lock.json
      - run: npm ci
      - run: npm test -- --coverage
      - name: Upload coverage
        if: secrets.CODECOV_TOKEN != ''
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}

  e2e:
    name: E2E Tests
    if: inputs.run-e2e
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
          cache-dependency-path: ${{ inputs.working-directory }}/package-lock.json
      - run: npm ci
      - name: Install Playwright
        run: npx playwright install --with-deps chromium
      - run: npm run e2e

  build:
    name: Build
    needs: [lint, test]
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
          cache-dependency-path: ${{ inputs.working-directory }}/package-lock.json
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: build-${{ inputs.working-directory }}
          path: ${{ inputs.working-directory }}/dist/
```

### Chiamata del Reusable Workflow

```yaml
# .github/workflows/ci.yml (nel repository consumer)
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    uses: my-org/.github/.github/workflows/reusable-node-ci.yml@main
    with:
      node-version: '20'
      run-e2e: true
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

### Composite Action per Setup Comune

```yaml
# .github/actions/setup-project/action.yml
name: Setup Project
description: 'Setup Node.js project with caching and dependencies'

inputs:
  node-version:
    description: 'Node.js version'
    required: false
    default: '20'
  working-directory:
    description: 'Working directory'
    required: false
    default: '.'
  install-playwright:
    description: 'Install Playwright browsers'
    required: false
    default: 'false'

runs:
  using: 'composite'
  steps:
    - uses: pnpm/action-setup@v4
      with:
        version: 9

    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'pnpm'
        cache-dependency-path: ${{ inputs.working-directory }}/pnpm-lock.yaml

    - name: Install dependencies
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: pnpm install --frozen-lockfile

    - name: Install Playwright
      if: inputs.install-playwright == 'true'
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: pnpm exec playwright install --with-deps chromium

    - name: Cache Turbo
      uses: actions/cache@v4
      with:
        path: ${{ inputs.working-directory }}/.turbo
        key: turbo-${{ runner.os }}-${{ hashFiles('**/pnpm-lock.yaml') }}-${{ github.sha }}
        restore-keys: |
          turbo-${{ runner.os }}-${{ hashFiles('**/pnpm-lock.yaml') }}-
          turbo-${{ runner.os }}-
```

### Uso della Composite Action

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: ./.github/actions/setup-project
        with:
          node-version: '20'
          install-playwright: 'true'

      - run: pnpm turbo test
      - run: pnpm turbo e2e
```

La differenza chiave: i reusable workflows definiscono interi job con i propri runner, mentre le composite actions sono step che vengono eseguiti all'interno del job chiamante. Ciò significa che le composite actions condividono il filesystem, l'ambiente e il contesto del job che le invoca, rendendole più efficienti per operazioni di setup comuni. I reusable workflows, al contrario, sono ideali per incapsulare pipeline complete che possono essere standardizzate attraverso un'organizzazione. La convenzione consigliata è di posizionare i reusable workflows nel repository `.github` dell'organizzazione e le composite actions nel repository specifico o in un repository condiviso di actions.

---

## Deploy Multi-Ambiente con Strategie Avanzate

I deploy moderni richiedono strategie che garantiscano zero-downtime e la possibilità di rollback rapido. Le tre strategie principali sono blue-green, canary e rolling deployment.

### Blue-Green Deployment

```yaml
# .github/workflows/deploy-blue-green.yml
name: Blue-Green Deployment

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://app.example.com
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: eu-west-1

      - name: Determine active environment
        id: active
        run: |
          # Determinare quale target group è attivo
          ACTIVE=$(aws elbv2 describe-rules \
            --listener-arn ${{ secrets.ALB_LISTENER_ARN }} \
            --query "Rules[?Priority=='1'].Actions[0].TargetGroupArn" \
            --output text)
          if [[ "$ACTIVE" == *"blue"* ]]; then
            echo "current=blue" >> "$GITHUB_OUTPUT"
            echo "target=green" >> "$GITHUB_OUTPUT"
          else
            echo "current=green" >> "$GITHUB_OUTPUT"
            echo "target=blue" >> "$GITHUB_OUTPUT"
          fi
          echo "Active: $(cat "$GITHUB_OUTPUT")"

      - name: Deploy to inactive environment
        run: |
          TARGET=${{ steps.active.outputs.target }}
          aws ecs update-service \
            --cluster my-cluster \
            --service "my-service-${TARGET}" \
            --task-definition my-app:${{ github.sha }} \
            --force-new-deployment
          aws ecs wait services-stable \
            --cluster my-cluster \
            --services "my-service-${TARGET}"

      - name: Health check inactive environment
        run: |
          TARGET_URL="https://${TARGET}.internal.example.com/health"
          for i in $(seq 1 30); do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$TARGET_URL")
            if [ "$STATUS" = "200" ]; then
              echo "Health check passed on ${{ steps.active.outputs.target }}"
              exit 0
            fi
            echo "Attempt $i: status $STATUS"
            sleep 5
          done
          echo "::error::Health check failed"
          exit 1

      - name: Switch traffic to new environment
        run: |
          TARGET_TG=${{ steps.active.outputs.target == 'blue' && secrets.BLUE_TG_ARN || secrets.GREEN_TG_ARN }}
          aws elbv2 modify-rule \
            --rule-arn ${{ secrets.ALB_RULE_ARN }} \
            --actions Type=forward,TargetGroupArn="$TARGET_TG"
          echo "Traffic switched to ${{ steps.active.outputs.target }}"

      - name: Verify production health
        run: |
          sleep 10
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://app.example.com/health)
          if [ "$STATUS" != "200" ]; then
            echo "::error::Production health check failed, initiating rollback"
            # Rollback: switchare il traffico al vecchio ambiente
            OLD_TG=${{ steps.active.outputs.current == 'blue' && secrets.BLUE_TG_ARN || secrets.GREEN_TG_ARN }}
            aws elbv2 modify-rule \
              --rule-arn ${{ secrets.ALB_RULE_ARN }} \
              --actions Type=forward,TargetGroupArn="$OLD_TG"
            exit 1
          fi
          echo "Production verified successfully"
```

### Canary Deployment con Weight Shifting

```yaml
# .github/workflows/deploy-canary.yml
name: Canary Deployment

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  canary:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: eu-west-1

      - name: Deploy canary (5% traffic)
        run: |
          # Deployare la nuova versione sul target group canary
          aws ecs update-service \
            --cluster my-cluster \
            --service my-service-canary \
            --task-definition my-app:${{ github.sha }} \
            --force-new-deployment
          aws ecs wait services-stable --cluster my-cluster --services my-service-canary

          # Inviare 5% del traffico al canary
          aws elbv2 modify-rule \
            --rule-arn ${{ secrets.ALB_RULE_ARN }} \
            --actions '[
              {"Type":"forward","ForwardConfig":{"TargetGroups":[
                {"TargetGroupArn":"${{ secrets.STABLE_TG_ARN }}","Weight":95},
                {"TargetGroupArn":"${{ secrets.CANARY_TG_ARN }}","Weight":5}
              ]}}
            ]'

      - name: Monitor canary (5 min)
        run: |
          echo "Monitoring canary for 5 minutes..."
          for i in $(seq 1 30); do
            # Controllare error rate dal canary
            ERROR_RATE=$(aws cloudwatch get-metric-statistics \
              --namespace AWS/ApplicationELB \
              --metric-name HTTPCode_Target_5XX_Count \
              --dimensions Name=TargetGroup,Value=${{ secrets.CANARY_TG_SHORT }} \
              --start-time "$(date -u -d '1 minute ago' +%Y-%m-%dT%H:%M:%S)" \
              --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
              --period 60 \
              --statistics Sum \
              --query 'Datapoints[0].Sum' \
              --output text 2>/dev/null || echo "0")

            if [ "$ERROR_RATE" != "None" ] && [ "$ERROR_RATE" -gt 10 ]; then
              echo "::error::Canary error rate too high: $ERROR_RATE. Rolling back."
              aws elbv2 modify-rule \
                --rule-arn ${{ secrets.ALB_RULE_ARN }} \
                --actions '[
                  {"Type":"forward","ForwardConfig":{"TargetGroups":[
                    {"TargetGroupArn":"${{ secrets.STABLE_TG_ARN }}","Weight":100},
                    {"TargetGroupArn":"${{ secrets.CANARY_TG_ARN }}","Weight":0}
                  ]}}
                ]'
              exit 1
            fi
            sleep 10
          done

      - name: Promote canary to full traffic
        run: |
          # Promuovere al 100%
          aws ecs update-service \
            --cluster my-cluster \
            --service my-service-stable \
            --task-definition my-app:${{ github.sha }} \
            --force-new-deployment
          aws ecs wait services-stable --cluster my-cluster --services my-service-stable

          # Riportare tutto il traffico allo stable
          aws elbv2 modify-rule \
            --rule-arn ${{ secrets.ALB_RULE_ARN }} \
            --actions '[
              {"Type":"forward","ForwardConfig":{"TargetGroups":[
                {"TargetGroupArn":"${{ secrets.STABLE_TG_ARN }}","Weight":100},
                {"TargetGroupArn":"${{ secrets.CANARY_TG_ARN }}","Weight":0}
              ]}}
            ]'
          echo "Canary promoted successfully"
```

Il blue-green deployment mantiene due ambienti identici e switcha il traffico istantaneamente, offrendo il rollback più rapido possibile (basta un cambio di routing). Il canary deployment, invece, invia una piccola percentuale di traffico alla nuova versione e la monitora progressivamente — più lento ma con rischio minore perché solo una frazione degli utenti è esposta. Il rolling deployment aggiorna le istanze gradualmente ed è il default di Kubernetes (`RollingUpdate`). La scelta dipende dalla tolleranza al rischio: canary per servizi ad alto traffico dove un bug potrebbe impattare milioni di utenti, blue-green per applicazioni con test meno granulari dove serve rollback immediato.

---

## Kubernetes Deployment con Helm e ArgoCD

Il deploy su Kubernetes può essere gestito direttamente con `kubectl`, tramite Helm chart, oppure con un approccio GitOps usando ArgoCD. Ogni metodo ha vantaggi specifici.

### Deploy Diretto con Helm

```yaml
# .github/workflows/deploy-k8s-helm.yml
name: Deploy to Kubernetes (Helm)

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  build-push:
    name: Build & Push Image
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.meta.outputs.version }}
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: type=sha,prefix=

      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    name: Deploy Staging
    needs: build-push
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/checkout@v4

      - name: Configure kubeconfig
        uses: azure/k8s-set-context@v4
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}

      - name: Deploy with Helm
        run: |
          helm upgrade --install my-app ./helm/my-app \
            --namespace staging \
            --create-namespace \
            --set image.tag=${{ needs.build-push.outputs.image-tag }} \
            --set environment=staging \
            --set replicas=2 \
            --values helm/my-app/values-staging.yaml \
            --wait \
            --timeout 300s

      - name: Verify deployment
        run: |
          kubectl rollout status deployment/my-app -n staging --timeout=120s
          kubectl get pods -n staging -l app=my-app

      - name: Run smoke tests
        run: |
          ENDPOINT=$(kubectl get svc my-app -n staging -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
          curl -sf "http://${ENDPOINT}/health" || exit 1

  deploy-production:
    name: Deploy Production
    needs: [build-push, deploy-staging]
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://app.example.com
    steps:
      - uses: actions/checkout@v4

      - name: Configure kubeconfig
        uses: azure/k8s-set-context@v4
        with:
          method: kubeconfig
          kubeconfig: ${{ secrets.KUBE_CONFIG_PRODUCTION }}

      - name: Deploy with Helm
        run: |
          helm upgrade --install my-app ./helm/my-app \
            --namespace production \
            --set image.tag=${{ needs.build-push.outputs.image-tag }} \
            --set environment=production \
            --set replicas=3 \
            --values helm/my-app/values-production.yaml \
            --wait \
            --timeout 600s

      - name: Verify deployment
        run: |
          kubectl rollout status deployment/my-app -n production --timeout=180s
```

### GitOps con ArgoCD

```yaml
# .github/workflows/gitops-argocd.yml
name: GitOps Deploy (ArgoCD)

on:
  push:
    branches: [main]

permissions:
  contents: write
  packages: write

jobs:
  build-push:
    name: Build & Push
    runs-on: ubuntu-latest
    outputs:
      image-digest: ${{ steps.build.outputs.digest }}
      image-tag: ${{ github.sha }}
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  update-manifests:
    name: Update GitOps Manifests
    needs: build-push
    runs-on: ubuntu-latest
    steps:
      - name: Checkout gitops repo
        uses: actions/checkout@v4
        with:
          repository: my-org/gitops-manifests
          token: ${{ secrets.GITOPS_PAT }}
          ref: main

      - name: Update image tag in Helm values
        run: |
          # Aggiornare il tag dell'immagine nel values file
          yq eval ".image.tag = \"${{ needs.build-push.outputs.image-tag }}\"" \
            -i environments/staging/values.yaml

          # Aggiornare il digest per verifica di integrità
          yq eval ".image.digest = \"${{ needs.build-push.outputs.image-digest }}\"" \
            -i environments/staging/values.yaml

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add environments/staging/values.yaml
          git commit -m "chore: update staging image to ${{ needs.build-push.outputs.image-tag }}"
          git push

      # ArgoCD rileva automaticamente il cambio nel repository
      # e sincronizza lo stato desiderato con il cluster
```

### Helm Chart di Esempio

```yaml
# helm/my-app/values.yaml
replicaCount: 2

image:
  repository: ghcr.io/my-org/my-app
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8080

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: app.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: app-tls
      hosts:
        - app.example.com

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
```

Nel modello GitOps con ArgoCD, la pipeline CI (GitHub Actions) si limita a buildare l'immagine e aggiornare il repository dei manifesti. ArgoCD monitora quel repository e applica automaticamente le modifiche al cluster Kubernetes, garantendo che lo stato del cluster corrisponda sempre a quello definito nel repository Git. Questo approccio separa completamente CI (build/test) e CD (deploy), migliorando la sicurezza perché il cluster Kubernetes non ha mai bisogno di credenziali per il registry delle immagini — ArgoCD si occupa di tutto internamente.

### Flux CD come Alternativa GitOps

Flux CD è l'alternativa CNCF-graduated ad ArgoCD per il continuous deployment GitOps su Kubernetes. Mentre ArgoCD offre una UI ricca e un modello centralizzato, Flux adotta un approccio decentralizzato basato su controller CRD nativi di Kubernetes, risultando più leggero e adatto a team che preferiscono gestire tutto via `kubectl` e manifesti YAML senza interfaccia grafica.

```yaml
# .github/workflows/flux-gitops.yml
name: Flux CD GitOps Pipeline

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'Dockerfile'

permissions:
  contents: write
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-update:
    name: Build Image & Update Flux Manifests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

      # Flux usa ImagePolicy e ImageRepository CRD per
      # auto-update, ma il pattern manuale via CI è più esplicito
      - name: Update Flux image tag in manifests
        run: |
          cd deploy/flux
          # Aggiorna il tag dell'immagine nel kustomization
          kustomize edit set image \
            app=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Commit manifest update
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add deploy/flux/
          git diff --staged --quiet || \
            git commit -m "chore: update image to ${{ github.sha }}"
          git push
```

Con Flux, la struttura del repository di deployment segue un pattern basato su Kustomize:

```yaml
# deploy/flux/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
  - hpa.yaml
images:
  - name: app
    newName: ghcr.io/org/app
    newTag: latest  # Aggiornato automaticamente da CI o Flux ImageAutomation
```

Per abilitare l'aggiornamento automatico delle immagini senza CI, Flux offre il componente **Image Automation Controller**:

```yaml
# flux-system/image-automation.yaml
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImageRepository
metadata:
  name: app
  namespace: flux-system
spec:
  image: ghcr.io/org/app
  interval: 5m0s
---
apiVersion: image.toolkit.fluxcd.io/v1beta2
kind: ImagePolicy
metadata:
  name: app
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: app
  policy:
    semver:
      range: '>=1.0.0'
---
apiVersion: image.toolkit.fluxcd.io/v1beta1
kind: ImageUpdateAutomation
metadata:
  name: app
  namespace: flux-system
spec:
  interval: 5m0s
  sourceRef:
    kind: GitRepository
    name: flux-system
  git:
    checkout:
      ref:
        branch: main
    commit:
      author:
        email: fluxbot@example.com
        name: fluxbot
      messageTemplate: 'chore: update image {{range .Updated.Images}}{{println .}}{{end}}'
    push:
      branch: main
  update:
    path: ./deploy/flux
    strategy: Setters
```

La differenza architetturale fondamentale: ArgoCD è un'applicazione centralizzata che osserva N repository e deploya su N cluster, con una dashboard unificata e RBAC integrato. Flux è un set di controller Kubernetes-native che vivono dentro ogni cluster, ciascuno responsabile del proprio stato. Flux eccelle in scenari multi-tenant dove ogni team gestisce il proprio namespace con un proprio `Kustomization` CRD, senza condividere un control plane centralizzato. ArgoCD eccelle quando serve visibilità centralizzata e un'interfaccia grafica per operazioni e audit. Entrambi supportano Helm, Kustomize e manifesti raw. La scelta dipende dal modello organizzativo: team centralizzato → ArgoCD, team autonomi → Flux.

---

## Database Migration in CI/CD

Le migrazioni di database in CI/CD richiedono attenzione particolare: devono essere eseguite in modo ordinato, verificate prima dell'applicazione e compatibili con rollback. I tool principali sono Flyway, Liquibase e i framework ORM-specific come Prisma e Drizzle.

### Flyway Migration Workflow

```yaml
# .github/workflows/db-migration-flyway.yml
name: Database Migration (Flyway)

on:
  push:
    branches: [main]
    paths:
      - 'db/migrations/**'
      - 'flyway.conf'
  pull_request:
    branches: [main]
    paths:
      - 'db/migrations/**'
      - 'flyway.conf'

permissions:
  contents: read
  pull-requests: write

jobs:
  validate:
    name: Validate Migrations
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: flyway
          POSTGRES_PASSWORD: flyway
          POSTGRES_DB: migration_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4

      - name: Run Flyway validate
        uses: docker://flyway/flyway:10
        with:
          args: >-
            -url=jdbc:postgresql://postgres:5432/migration_test
            -user=flyway
            -password=flyway
            -locations=filesystem:db/migrations
            validate

      - name: Run Flyway info
        uses: docker://flyway/flyway:10
        with:
          args: >-
            -url=jdbc:postgresql://postgres:5432/migration_test
            -user=flyway
            -password=flyway
            -locations=filesystem:db/migrations
            info

      - name: Dry-run migrate
        uses: docker://flyway/flyway:10
        with:
          args: >-
            -url=jdbc:postgresql://postgres:5432/migration_test
            -user=flyway
            -password=flyway
            -locations=filesystem:db/migrations
            migrate

      - name: Verify schema after migration
        run: |
          PGPASSWORD=flyway psql -h localhost -U flyway -d migration_test -c "
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
          "

  apply-staging:
    name: Apply to Staging
    needs: validate
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Run migration on staging
        uses: docker://flyway/flyway:10
        with:
          args: >-
            -url=${{ secrets.STAGING_DB_URL }}
            -user=${{ secrets.STAGING_DB_USER }}
            -password=${{ secrets.STAGING_DB_PASSWORD }}
            -locations=filesystem:db/migrations
            -outOfOrder=false
            -validateOnMigrate=true
            migrate

  apply-production:
    name: Apply to Production
    needs: apply-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Run migration on production
        uses: docker://flyway/flyway:10
        with:
          args: >-
            -url=${{ secrets.PROD_DB_URL }}
            -user=${{ secrets.PROD_DB_USER }}
            -password=${{ secrets.PROD_DB_PASSWORD }}
            -locations=filesystem:db/migrations
            -outOfOrder=false
            -validateOnMigrate=true
            migrate
```

### Prisma Migration Workflow

```yaml
# .github/workflows/db-migration-prisma.yml
name: Database Migration (Prisma)

on:
  push:
    branches: [main]
    paths:
      - 'prisma/**'

permissions:
  contents: read

jobs:
  migrate:
    name: Run Prisma Migrations
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      - name: Check migration status
        run: npx prisma migrate status
        env:
          DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}

      - name: Apply migrations
        run: npx prisma migrate deploy
        env:
          DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}

      - name: Verify schema
        run: npx prisma db pull --force && npx prisma validate
        env:
          DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
```

Il pattern fondamentale per le migrazioni in CI/CD è: (1) validare le migrazioni su un database di test pulito nella PR, (2) applicare allo staging automaticamente dopo il merge in main, (3) applicare alla produzione con approvazione manuale tramite environment protection. L'ordine è cruciale: le migrazioni devono essere eseguite prima del deploy dell'applicazione, altrimenti il nuovo codice potrebbe trovare uno schema non aggiornato. Per garantire la compatibilità con rollback, ogni migrazione dovrebbe essere backward-compatible: aggiungere colonne prima di usarle, rimuovere colonne solo dopo che il codice che le usa è stato rimosso.

### Liquibase Migration Workflow

Liquibase è un'alternativa enterprise a Flyway con supporto nativo per changelog in XML, YAML, JSON e SQL. Il vantaggio principale è la gestione declarativa delle migrazioni tramite changeset identificati univocamente, con supporto per preconditions, rollback espliciti e contesti di esecuzione (dev, test, prod).

```yaml
# .github/workflows/db-migration-liquibase.yml
name: Database Migration (Liquibase)

on:
  push:
    branches: [main]
    paths:
      - 'db/changelog/**'

permissions:
  contents: read

jobs:
  validate:
    name: Validate Changelog
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Liquibase
        uses: liquibase/liquibase-github-action@v7
        with:
          operation: validate
          classpath: 'db/changelog'
          changeLogFile: 'db-changelog-master.yaml'
          url: 'jdbc:postgresql://localhost:5432/testdb'
          username: ${{ secrets.DB_USERNAME }}
          password: ${{ secrets.DB_PASSWORD }}

      - name: Check pending changesets
        uses: liquibase/liquibase-github-action@v7
        with:
          operation: status
          classpath: 'db/changelog'
          changeLogFile: 'db-changelog-master.yaml'
          url: 'jdbc:postgresql://${{ secrets.STAGING_DB_HOST }}:5432/app'
          username: ${{ secrets.DB_USERNAME }}
          password: ${{ secrets.DB_PASSWORD }}

  migrate-staging:
    name: Apply to Staging
    needs: validate
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Run Liquibase update
        uses: liquibase/liquibase-github-action@v7
        with:
          operation: update
          classpath: 'db/changelog'
          changeLogFile: 'db-changelog-master.yaml'
          url: 'jdbc:postgresql://${{ secrets.STAGING_DB_HOST }}:5432/app'
          username: ${{ secrets.DB_USERNAME }}
          password: ${{ secrets.DB_PASSWORD }}
          contexts: 'staging'

      - name: Generate diff report
        uses: liquibase/liquibase-github-action@v7
        with:
          operation: diff
          classpath: 'db/changelog'
          changeLogFile: 'db-changelog-master.yaml'
          url: 'jdbc:postgresql://${{ secrets.STAGING_DB_HOST }}:5432/app'
          referenceUrl: 'jdbc:postgresql://${{ secrets.PROD_DB_HOST }}:5432/app'
          username: ${{ secrets.DB_USERNAME }}
          password: ${{ secrets.DB_PASSWORD }}
          referenceUsername: ${{ secrets.PROD_DB_USERNAME }}
          referencePassword: ${{ secrets.PROD_DB_PASSWORD }}

  migrate-production:
    name: Apply to Production
    needs: migrate-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Tag current state (pre-migration)
        uses: liquibase/liquibase-github-action@v7
        with:
          operation: tag
          tag: 'pre-${{ github.sha }}'
          classpath: 'db/changelog'
          changeLogFile: 'db-changelog-master.yaml'
          url: 'jdbc:postgresql://${{ secrets.PROD_DB_HOST }}:5432/app'
          username: ${{ secrets.PROD_DB_USERNAME }}
          password: ${{ secrets.PROD_DB_PASSWORD }}

      - name: Apply migration
        uses: liquibase/liquibase-github-action@v7
        with:
          operation: update
          classpath: 'db/changelog'
          changeLogFile: 'db-changelog-master.yaml'
          url: 'jdbc:postgresql://${{ secrets.PROD_DB_HOST }}:5432/app'
          username: ${{ secrets.PROD_DB_USERNAME }}
          password: ${{ secrets.PROD_DB_PASSWORD }}
          contexts: 'production'
```

Il vantaggio di Liquibase rispetto a Flyway nelle pipeline CI/CD è il comando `diff` che genera automaticamente un report delle differenze tra due database — utile per verificare che staging e produzione siano allineati prima di applicare nuove migrazioni. Il comando `tag` consente di marcare lo stato del database prima di ogni migrazione, facilitando il rollback con `liquibase rollback --tag pre-<sha>` in caso di problemi post-deploy. I `contexts` permettono di applicare changeset diversi per ambiente: ad esempio, dati di seed solo in staging ma mai in produzione.

---

## Terraform Drift Detection e Multi-Workspace

Oltre al classico workflow plan/apply, Terraform in CI/CD beneficia di drift detection schedulato e gestione multi-workspace per ambienti separati.

### Drift Detection Schedulato

```yaml
# .github/workflows/terraform-drift.yml
name: Terraform Drift Detection

on:
  schedule:
    - cron: '0 8 * * 1-5'  # Lun-Ven alle 08:00 UTC
  workflow_dispatch:

permissions:
  id-token: write
  contents: read
  issues: write

env:
  TF_VERSION: '1.8.0'

jobs:
  drift-detect:
    name: Detect Drift (${{ matrix.workspace }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        workspace: [staging, production]
        include:
          - workspace: staging
            tf_dir: terraform/environments/staging
            aws_role: arn:aws:iam::111111111111:role/TerraformDriftRole
          - workspace: production
            tf_dir: terraform/environments/production
            aws_role: arn:aws:iam::222222222222:role/TerraformDriftRole

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ matrix.aws_role }}
          aws-region: eu-west-1

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Init
        working-directory: ${{ matrix.tf_dir }}
        run: terraform init -no-color

      - name: Check for drift
        id: plan
        working-directory: ${{ matrix.tf_dir }}
        run: |
          set +e
          terraform plan -no-color -detailed-exitcode -out=drift.plan 2>&1 | tee drift-output.txt
          EXIT_CODE=$?
          set -e

          if [ $EXIT_CODE -eq 0 ]; then
            echo "drift=false" >> "$GITHUB_OUTPUT"
            echo "No drift detected in ${{ matrix.workspace }}"
          elif [ $EXIT_CODE -eq 2 ]; then
            echo "drift=true" >> "$GITHUB_OUTPUT"
            echo "::warning::Drift detected in ${{ matrix.workspace }}!"
          else
            echo "drift=error" >> "$GITHUB_OUTPUT"
            echo "::error::Terraform plan failed in ${{ matrix.workspace }}"
            exit 1
          fi

      - name: Create issue for drift
        if: steps.plan.outputs.drift == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const output = fs.readFileSync('${{ matrix.tf_dir }}/drift-output.txt', 'utf8');
            const truncated = output.length > 60000 ? output.substring(0, 60000) + '\n...(truncated)' : output;

            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `[Drift] Infrastructure drift detected in ${context.payload.repository.name} (${{ matrix.workspace }})`,
              body: `## Drift Detection Report\n\n**Environment:** ${{ matrix.workspace }}\n**Detected:** ${new Date().toISOString()}\n\n<details>\n<summary>Terraform Plan Output</summary>\n\n\`\`\`\n${truncated}\n\`\`\`\n\n</details>\n\nPlease investigate and remediate.`,
              labels: ['infrastructure', 'drift', '${{ matrix.workspace }}']
            });
```

### Multi-Workspace con Moduli Condivisi

```yaml
# .github/workflows/terraform-multi-workspace.yml
name: Terraform Multi-Workspace

on:
  push:
    branches: [main]
    paths: ['terraform/**']
  pull_request:
    branches: [main]
    paths: ['terraform/**']

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  detect-changes:
    name: Detect Changed Workspaces
    runs-on: ubuntu-latest
    outputs:
      workspaces: ${{ steps.filter.outputs.workspaces }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Determine affected workspaces
        id: filter
        run: |
          CHANGED=$(git diff --name-only ${{ github.event.before || 'HEAD~1' }} HEAD -- terraform/)
          WORKSPACES='[]'

          # Se i moduli condivisi sono cambiati, ricostruire tutto
          if echo "$CHANGED" | grep -q "terraform/modules/"; then
            WORKSPACES='["staging","production"]'
          else
            if echo "$CHANGED" | grep -q "terraform/environments/staging/"; then
              WORKSPACES=$(echo "$WORKSPACES" | jq '. += ["staging"]')
            fi
            if echo "$CHANGED" | grep -q "terraform/environments/production/"; then
              WORKSPACES=$(echo "$WORKSPACES" | jq '. += ["production"]')
            fi
          fi

          echo "workspaces=$WORKSPACES" >> "$GITHUB_OUTPUT"
          echo "Affected workspaces: $WORKSPACES"

  plan:
    name: Plan (${{ matrix.workspace }})
    needs: detect-changes
    if: needs.detect-changes.outputs.workspaces != '[]'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        workspace: ${{ fromJson(needs.detect-changes.outputs.workspaces) }}
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: '1.8.0'
      - name: Terraform Plan
        working-directory: terraform/environments/${{ matrix.workspace }}
        run: |
          terraform init -no-color
          terraform plan -no-color -out=tfplan
```

Il drift detection schedulato è fondamentale per identificare modifiche manuali all'infrastruttura che bypassano il processo IaC. L'exit code dettagliato di `terraform plan` (`-detailed-exitcode`) distingue tra "nessun cambiamento" (0) e "cambiamenti rilevati" (2), permettendo di creare automaticamente issue GitHub quando viene rilevato drift. La strategia multi-workspace con detection dei cambiamenti evita di eseguire plan su ambienti non impattati, riducendo i tempi CI e il consumo di risorse. Quando i moduli condivisi cambiano, tutti i workspace dipendenti vengono ricalcolati.

---

## OIDC e Workload Identity Federation

L'autenticazione OIDC elimina completamente i secrets statici per i cloud provider. Ogni workflow run riceve un token JWT firmato da GitHub che viene scambiato con credenziali temporanee dal cloud provider.

### Configurazione OIDC per AWS

```yaml
# Prerequisiti AWS:
# 1. Creare OIDC Identity Provider: https://token.actions.githubusercontent.com
# 2. Creare IAM Role con trust policy:
#
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Effect": "Allow",
#       "Principal": {
#         "Federated": "arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com"
#       },
#       "Action": "sts:AssumeRoleWithWebIdentity",
#       "Condition": {
#         "StringEquals": {
#           "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
#         },
#         "StringLike": {
#           "token.actions.githubusercontent.com:sub": "repo:my-org/my-repo:*"
#         }
#       }
#     }
#   ]
# }

# .github/workflows/oidc-aws.yml
name: Deploy with OIDC (AWS)

on:
  push:
    branches: [main]

permissions:
  id-token: write    # Obbligatorio per OIDC
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: eu-west-1
          # Durata sessione: minimo necessario
          role-duration-seconds: 900
          # Restrizioni aggiuntive opzionali
          role-session-name: gha-deploy-${{ github.run_id }}

      - name: Verify identity
        run: aws sts get-caller-identity
```

### Configurazione OIDC per GCP (Workload Identity Federation)

```yaml
# Prerequisiti GCP:
# 1. Creare Workload Identity Pool
# 2. Creare Workload Identity Provider
# 3. Configurare IAM binding per il service account
#
# gcloud iam workload-identity-pools create "github-pool" \
#   --location="global" \
#   --display-name="GitHub Pool"
#
# gcloud iam workload-identity-pools providers create-oidc "github-provider" \
#   --location="global" \
#   --workload-identity-pool="github-pool" \
#   --display-name="GitHub Provider" \
#   --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
#   --issuer-uri="https://token.actions.githubusercontent.com"

# .github/workflows/oidc-gcp.yml
name: Deploy with OIDC (GCP)

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
          service_account: 'deploy@my-project.iam.gserviceaccount.com'

      - name: Setup gcloud
        uses: google-github-actions/setup-gcloud@v2

      - name: Verify identity
        run: gcloud auth list
```

Il punto chiave dell'OIDC è la condizione nella trust policy: `StringLike` sul claim `sub` limita quali repository, branch e ambienti possono assumere il ruolo. Ad esempio, `repo:my-org/my-repo:environment:production` restringe il ruolo al solo environment `production`, impedendo che un workflow di test possa accedere alle credenziali di produzione. La durata della sessione (`role-duration-seconds`) dovrebbe essere impostata al minimo necessario per completare il deploy — 900 secondi (15 minuti) è un buon default. Per GCP, la Workload Identity Federation usa lo stesso meccanismo ma con terminologia diversa: il Workload Identity Pool è l'equivalente dell'OIDC Identity Provider di AWS, e l'attribute mapping mappa i claims del token GitHub ai attributi GCP.

---

## Cache Optimization Avanzata

Il caching è la leva più potente per ridurre i tempi CI. Esistono tre livelli di caching: dipendenze, build artifact e Docker layers, ognuno con strategie diverse.

### Cache Multi-Layer per Node.js

```yaml
# .github/workflows/optimized-cache.yml
name: Optimized Caching

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile

      # Cache di build intermedi (es. Next.js)
      - name: Cache Next.js build
        uses: actions/cache@v4
        with:
          path: |
            apps/web/.next/cache
          key: nextjs-${{ runner.os }}-${{ hashFiles('**/pnpm-lock.yaml') }}-${{ hashFiles('apps/web/src/**') }}
          restore-keys: |
            nextjs-${{ runner.os }}-${{ hashFiles('**/pnpm-lock.yaml') }}-
            nextjs-${{ runner.os }}-

      # Cache di Playwright browsers
      - name: Cache Playwright
        id: playwright-cache
        uses: actions/cache@v4
        with:
          path: ~/.cache/ms-playwright
          key: playwright-${{ runner.os }}-${{ hashFiles('**/pnpm-lock.yaml') }}

      - name: Install Playwright
        if: steps.playwright-cache.outputs.cache-hit != 'true'
        run: pnpm exec playwright install --with-deps chromium

      - run: pnpm turbo build test
```

### Cache per Go con Module Proxy

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'
          cache: true
          # Chiave di cache basata su go.sum
          cache-dependency-path: go.sum

      # Cache aggiuntiva per il build cache
      - name: Go build cache
        uses: actions/cache@v4
        with:
          path: |
            ~/.cache/go-build
          key: go-build-${{ runner.os }}-${{ hashFiles('**/*.go') }}
          restore-keys: |
            go-build-${{ runner.os }}-

      - run: go build -v ./...
```

### Cache Docker Layer con Registry Backend

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
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
          # Cache su registry anziché GHA — utile per immagini molto grandi
          cache-from: type=registry,ref=ghcr.io/${{ github.repository }}:buildcache
          cache-to: type=registry,ref=ghcr.io/${{ github.repository }}:buildcache,mode=max
```

La strategia di cache optimale dipende dal progetto. Per Node.js, la cache di `pnpm` riduce i tempi di install del 60-80%, ma la cache di Next.js build può eliminare ulteriori 2-3 minuti nelle build successive. Per Go, `actions/setup-go` gestisce automaticamente la cache dei moduli, ma aggiungere la cache del build directory (`~/.cache/go-build`) velocizza anche la compilazione. Per Docker, la scelta tra cache GHA (`type=gha`, limite 10 GB condivisi) e cache su registry (`type=registry`, senza limite) dipende dalla dimensione delle immagini: immagini sotto i 2 GB funzionano bene con GHA, immagini più grandi beneficiano della cache su registry. Il parametro `mode=max` nella cache Docker include tutti i layer intermedi, non solo quelli del risultato finale, massimizzando il riuso nelle build successive.

---

## Self-Hosted Runners e Actions Runner Controller

I runner GitHub-hosted hanno limiti di risorse e tempo. Per pipeline con requisiti specifici (GPU, hardware dedicato, rete privata, compliance), i self-hosted runners o Actions Runner Controller (ARC) su Kubernetes sono la soluzione.

### ARC su Kubernetes con Helm

```yaml
# Installazione ARC con Helm
# helm repo add actions-runner-controller https://actions-runner-controller.github.io/actions-runner-controller
# helm install arc --namespace arc-systems --create-namespace \
#   oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller

# Configurazione del runner scale set:
# helm install arc-runner-set --namespace arc-runners --create-namespace \
#   oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set \
#   --set githubConfigUrl="https://github.com/my-org" \
#   --set githubConfigSecret.github_token="ghp_xxx" \
#   --set maxRunners=10 \
#   --set minRunners=1

# .github/workflows/self-hosted.yml
name: Build on Self-Hosted

on:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  build:
    runs-on: arc-runner-set    # Nome del runner scale set
    steps:
      - uses: actions/checkout@v4

      - name: Build with custom hardware
        run: |
          echo "Running on self-hosted runner"
          echo "CPU: $(nproc)"
          echo "RAM: $(free -h | grep Mem | awk '{print $2}')"
          make build

  gpu-test:
    runs-on: [self-hosted, gpu, linux]   # Label matching
    steps:
      - uses: actions/checkout@v4
      - name: Run GPU tests
        run: |
          nvidia-smi
          python -m pytest tests/gpu/ -v
```

### Configurazione Runner Scale Set

```yaml
# arc-runner-values.yaml — valori Helm per il runner scale set
githubConfigUrl: "https://github.com/my-org"
githubConfigSecret:
  github_token: ""    # oppure github_app_id + github_app_installation_id + github_app_private_key

maxRunners: 20
minRunners: 2

template:
  spec:
    containers:
      - name: runner
        image: ghcr.io/actions/actions-runner:latest
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
          limits:
            cpu: "4"
            memory: "8Gi"
        volumeMounts:
          - name: work
            mountPath: /home/runner/_work
    volumes:
      - name: work
        emptyDir:
          sizeLimit: 20Gi

    # Tollerazioni per nodi dedicati ai runner
    tolerations:
      - key: "ci-runner"
        operator: "Exists"
        effect: "NoSchedule"

    nodeSelector:
      node-role: ci-runner
```

ARC (Actions Runner Controller) è il metodo consigliato da GitHub per gestire runner self-hosted su Kubernetes. I runner vengono creati come pod efimeri: ogni job riceve un pod nuovo, che viene distrutto al termine. Questo garantisce isolamento completo tra job e previene l'accumulo di stato. Il `minRunners` mantiene un pool di runner pronti per ridurre il cold-start, mentre `maxRunners` limita il consumo di risorse del cluster. I label multipli (`[self-hosted, gpu, linux]`) permettono di targetizzare runner specifici in base alle capabilities richieste dal job.

---

## Dockerfile Ottimizzati per CI/CD

Un Dockerfile ben strutturato è fondamentale per build veloci in CI. I principi chiave sono: multi-stage build, ordinamento dei layer per massimizzare il cache hit e dimensioni finali minime.

### Node.js Multi-Stage Optimized

```dockerfile
# Dockerfile per applicazione Node.js
# Stage 1: Dipendenze (cache separata)
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production=false

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build
# Rimuovere devDependencies dopo il build
RUN npm prune --production

# Stage 3: Runtime (immagine minimale)
FROM node:20-alpine AS runner
WORKDIR /app

# Sicurezza: non eseguire come root
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 appuser

# Copiare solo ciò che serve
COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./

USER appuser

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "dist/server.js"]
```

### Go Distroless

```dockerfile
# Dockerfile per applicazione Go
# Stage 1: Build
FROM golang:1.23-alpine AS builder
WORKDIR /app

# Cache dei moduli separata
COPY go.mod go.sum ./
RUN go mod download && go mod verify

COPY . .

# Build statico senza CGO
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-s -w -extldflags '-static'" \
    -o /app/server ./cmd/server

# Stage 2: Runtime minimo — distroless per sicurezza massima
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app/server /server

EXPOSE 8080
USER nonroot:nonroot

ENTRYPOINT ["/server"]
```

### Python Multi-Stage

```dockerfile
# Dockerfile per applicazione Python
# Stage 1: Build delle dipendenze
FROM python:3.12-slim AS builder
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runner
WORKDIR /app

# Copiare solo i pacchetti installati
COPY --from=builder /install /usr/local

# Sicurezza: utente non-root
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

COPY --chown=appuser:appuser . .

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

L'ordine dei layer è critico per il caching: i file che cambiano meno frequentemente (come `package.json` o `go.mod`) devono essere copiati prima del codice sorgente. In questo modo, il layer delle dipendenze viene cachato finché il lockfile non cambia, anche se il codice sorgente è stato modificato. L'immagine distroless per Go è la scelta più sicura: non contiene shell, package manager o tool di sistema, riducendo drasticamente la superficie d'attacco (e la dimensione dell'immagine a pochi MB). Per Node.js, il `npm prune --production` dopo il build elimina le devDependencies, riducendo la dimensione finale. Il `HEALTHCHECK` nel Dockerfile permette a Docker e agli orchestratori di verificare automaticamente lo stato dell'applicazione.

---

## Release Automation Avanzata e Changelog

Oltre a semantic-release, esistono alternative come `release-please` (di Google) e workflow personalizzati per scenari specifici come pre-release, hotfix e multi-package release.

### Release con release-please

```yaml
# .github/workflows/release-please.yml
name: Release Please

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    outputs:
      release_created: ${{ steps.release.outputs.release_created }}
      tag_name: ${{ steps.release.outputs.tag_name }}
      version: ${{ steps.release.outputs.version }}
    steps:
      - uses: googleapis/release-please-action@v4
        id: release
        with:
          release-type: node
          # Per monorepo, usare manifest mode:
          # config-file: release-please-config.json
          # manifest-file: .release-please-manifest.json

  publish:
    name: Publish
    needs: release-please
    if: needs.release-please.outputs.release_created == 'true'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          registry-url: 'https://registry.npmjs.org'

      - run: npm ci
      - run: npm run build
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:${{ needs.release-please.outputs.version }}
            ghcr.io/${{ github.repository }}:latest
```

### Release Manuale con Changelog Generato

```yaml
# .github/workflows/manual-release.yml
name: Manual Release

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Release version (e.g. 1.2.3)'
        required: true
        type: string
      prerelease:
        description: 'Mark as pre-release'
        required: false
        type: boolean
        default: false

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate changelog
        id: changelog
        run: |
          # Trovare l'ultimo tag
          LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
          if [ -z "$LAST_TAG" ]; then
            RANGE="HEAD"
          else
            RANGE="${LAST_TAG}..HEAD"
          fi

          # Generare changelog da conventional commits
          CHANGELOG=""
          FEATURES=$(git log "$RANGE" --pretty=format:"%s" | grep "^feat" | sed 's/^feat[:(]//' | sed 's/):/: /' || true)
          FIXES=$(git log "$RANGE" --pretty=format:"%s" | grep "^fix" | sed 's/^fix[:(]//' | sed 's/):/: /' || true)
          BREAKING=$(git log "$RANGE" --pretty=format:"%b" | grep "BREAKING CHANGE" || true)

          if [ -n "$FEATURES" ]; then
            CHANGELOG="${CHANGELOG}\n## Features\n"
            while IFS= read -r line; do
              CHANGELOG="${CHANGELOG}\n- ${line}"
            done <<< "$FEATURES"
          fi

          if [ -n "$FIXES" ]; then
            CHANGELOG="${CHANGELOG}\n\n## Bug Fixes\n"
            while IFS= read -r line; do
              CHANGELOG="${CHANGELOG}\n- ${line}"
            done <<< "$FIXES"
          fi

          if [ -n "$BREAKING" ]; then
            CHANGELOG="${CHANGELOG}\n\n## BREAKING CHANGES\n"
            while IFS= read -r line; do
              CHANGELOG="${CHANGELOG}\n- ${line}"
            done <<< "$BREAKING"
          fi

          echo "changelog<<EOF" >> "$GITHUB_OUTPUT"
          echo -e "$CHANGELOG" >> "$GITHUB_OUTPUT"
          echo "EOF" >> "$GITHUB_OUTPUT"

      - name: Create tag
        run: |
          git tag "v${{ inputs.version }}"
          git push origin "v${{ inputs.version }}"

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: v${{ inputs.version }}
          name: v${{ inputs.version }}
          body: ${{ steps.changelog.outputs.changelog }}
          prerelease: ${{ inputs.prerelease }}
          generate_release_notes: true
```

### Configurazione release-please per Monorepo

```json
// release-please-config.json
{
  "packages": {
    "packages/core": {
      "release-type": "node",
      "component": "core",
      "changelog-path": "CHANGELOG.md"
    },
    "packages/cli": {
      "release-type": "node",
      "component": "cli",
      "changelog-path": "CHANGELOG.md"
    },
    "packages/sdk": {
      "release-type": "python",
      "component": "sdk",
      "changelog-path": "CHANGELOG.md"
    }
  },
  "group-pull-requests": true,
  "separate-pull-requests": false,
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json"
}
```

La differenza tra `semantic-release` e `release-please`: il primo esegue la release direttamente dopo il merge in main, mentre il secondo crea una PR di release che accumula le modifiche e viene mergiata quando si è pronti per rilasciare. `release-please` è particolarmente adatto ai monorepo grazie al suo manifest mode che gestisce versioning indipendente per ogni pacchetto. Il workflow manuale con `workflow_dispatch` è utile per release controllate dove il team decide esattamente quando e quale versione rilasciare, con la generazione automatica del changelog dai conventional commits accumulati dall'ultimo tag.

---

## Pipeline E2E: dal Commit alla Produzione

Una pipeline end-to-end completa orchestra tutti i passaggi dalla modifica del codice al deploy in produzione, integrando CI, security, staging, approvazione e deploy finale.

```yaml
# .github/workflows/pipeline-e2e.yml
name: Full Pipeline

on:
  push:
    branches: [main]

permissions:
  contents: read
  packages: write
  security-events: write
  id-token: write
  pull-requests: write

concurrency:
  group: pipeline-${{ github.ref }}
  cancel-in-progress: false  # Non cancellare deploy in corso

jobs:
  # === FASE 1: CI ===
  lint-and-typecheck:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  test:
    name: Unit & Integration Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
        env:
          DATABASE_URL: postgres://test:test@localhost:5432/testdb
      - uses: codecov/codecov-action@v3

  # === FASE 2: SECURITY ===
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: javascript
      - uses: github/codeql-action/analyze@v3
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  # === FASE 3: BUILD ===
  build:
    name: Build & Push Image
    needs: [lint-and-typecheck, test, security]
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ github.sha }}
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
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
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Scan image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ghcr.io/${{ github.repository }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy.sarif'
          severity: 'CRITICAL,HIGH'
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy.sarif

  # === FASE 4: DEPLOY STAGING ===
  deploy-staging:
    name: Deploy Staging
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_STAGING_ROLE }}
          aws-region: eu-west-1
      - name: Deploy to ECS staging
        run: |
          aws ecs update-service \
            --cluster staging-cluster \
            --service my-app \
            --task-definition my-app:${{ github.sha }} \
            --force-new-deployment
          aws ecs wait services-stable --cluster staging-cluster --services my-app
      - name: Smoke tests
        run: |
          sleep 15
          curl -sf https://staging.example.com/health
          curl -sf https://staging.example.com/api/v1/status

  # === FASE 5: E2E SU STAGING ===
  e2e-staging:
    name: E2E Tests on Staging
    needs: deploy-staging
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - name: Run E2E
        run: npx playwright test --project=chromium
        env:
          BASE_URL: https://staging.example.com
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/

  # === FASE 6: DEPLOY PRODUCTION ===
  deploy-production:
    name: Deploy Production
    needs: e2e-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://app.example.com
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_PRODUCTION_ROLE }}
          aws-region: eu-west-1
      - name: Deploy to ECS production
        run: |
          aws ecs update-service \
            --cluster production-cluster \
            --service my-app \
            --task-definition my-app:${{ github.sha }} \
            --force-new-deployment
          aws ecs wait services-stable --cluster production-cluster --services my-app

      - name: Production health check
        run: |
          for i in $(seq 1 30); do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://app.example.com/health)
            if [ "$STATUS" = "200" ]; then
              echo "Production is healthy"
              exit 0
            fi
            sleep 10
          done
          echo "::error::Production health check failed"
          exit 1

  # === NOTIFICHE ===
  notify:
    name: Notify
    needs: [deploy-production]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Slack notification
        uses: slackapi/slack-github-action@v1.25.0
        with:
          payload: |
            {
              "text": "${{ needs.deploy-production.result == 'success' && 'Deploy successful' || 'Deploy failed' }}: ${{ github.repository }} (${{ github.sha }})"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          SLACK_WEBHOOK_TYPE: INCOMING_WEBHOOK
```

Questa pipeline E2E segue il pattern "fail fast, deploy slow": le fasi di CI (lint, test, security) eseguono in parallelo per ottenere feedback rapido, poi convergono sulla build. Il deploy segue un flusso sequenziale obbligato: staging, E2E su staging, approvazione manuale (tramite environment protection), deploy in produzione. Il flag `cancel-in-progress: false` è critico: non si deve mai cancellare un deploy in corso perché potrebbe lasciare l'ambiente in uno stato inconsistente. L'environment `production` con approvazione manuale garantisce che nessun deploy raggiunga la produzione senza review umana.

---

## E2E Testing con Playwright e Cypress

Il testing end-to-end nelle pipeline CI/CD va oltre la semplice esecuzione dei test: richiede gestione dei browser, parallelizzazione, sharding, retry intelligenti e raccolta sistematica degli artifact di debug. Playwright e Cypress sono i due framework dominanti, ciascuno con pattern di integrazione specifici per GitHub Actions.

### Playwright con Sharding e Retry

Playwright supporta nativamente lo sharding — la distribuzione dei test su più runner paralleli — riducendo drasticamente il tempo di esecuzione per suite di test grandi.

```yaml
# .github/workflows/e2e-playwright.yml
name: E2E Tests (Playwright)

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: e2e-${{ github.ref }}
  cancel-in-progress: true

jobs:
  playwright:
    name: Playwright Shard ${{ matrix.shard }}
    runs-on: ubuntu-latest
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix:
        shard: [1/4, 2/4, 3/4, 4/4]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      - name: Cache Playwright browsers
        uses: actions/cache@v4
        id: playwright-cache
        with:
          path: ~/.cache/ms-playwright
          key: playwright-${{ runner.os }}-${{ hashFiles('package-lock.json') }}

      - name: Install Playwright browsers
        if: steps.playwright-cache.outputs.cache-hit != 'true'
        run: npx playwright install --with-deps

      - name: Install system dependencies
        if: steps.playwright-cache.outputs.cache-hit == 'true'
        run: npx playwright install-deps

      - name: Run Playwright tests
        run: npx playwright test --shard=${{ matrix.shard }} --retries=2
        env:
          BASE_URL: ${{ vars.STAGING_URL || 'http://localhost:3000' }}
          CI: true

      - name: Upload blob report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: blob-report-${{ strategy.job-index }}
          path: blob-report/
          retention-days: 7

      - name: Upload test results
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-traces-${{ strategy.job-index }}
          path: |
            test-results/
            playwright-report/

  merge-reports:
    name: Merge Playwright Reports
    needs: playwright
    if: always()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      - name: Download blob reports
        uses: actions/download-artifact@v4
        with:
          pattern: blob-report-*
          path: all-blob-reports
          merge-multiple: true

      - name: Merge reports
        run: npx playwright merge-reports --reporter html ./all-blob-reports

      - name: Upload merged HTML report
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-full
          path: playwright-report/
          retention-days: 14
```

### Cypress con Dashboard e Parallelizzazione

Cypress offre parallelizzazione tramite il Cypress Cloud (ex-Dashboard) oppure in self-hosted con l'action `cypress-io/github-action`. Il pattern chiave è separare l'installazione dalla build e dall'esecuzione, usando il caching aggressivo della directory `.cypress/cache`.

```yaml
# .github/workflows/e2e-cypress.yml
name: E2E Tests (Cypress)

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  cypress:
    name: Cypress (${{ matrix.browser }})
    runs-on: ubuntu-latest
    timeout-minutes: 25
    strategy:
      fail-fast: false
      matrix:
        browser: [chrome, firefox]
        containers: [1, 2, 3]
    steps:
      - uses: actions/checkout@v4

      - name: Cypress run
        uses: cypress-io/github-action@v6
        with:
          browser: ${{ matrix.browser }}
          build: npm run build
          start: npm start
          wait-on: 'http://localhost:3000'
          wait-on-timeout: 120
          record: true
          parallel: true
          group: 'e2e-${{ matrix.browser }}'
        env:
          CYPRESS_RECORD_KEY: ${{ secrets.CYPRESS_RECORD_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Upload screenshots on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: cypress-screenshots-${{ matrix.browser }}-${{ matrix.containers }}
          path: cypress/screenshots/
          retention-days: 7

      - name: Upload videos
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: cypress-videos-${{ matrix.browser }}-${{ matrix.containers }}
          path: cypress/videos/
          retention-days: 5
```

La scelta tra Playwright e Cypress dipende da diversi fattori: Playwright supporta nativamente WebKit (Safari), ha sharding built-in senza servizio cloud esterno, e supporta test su mobile viewport. Cypress offre un'esperienza di debug superiore con time-travel debugging e una community più matura di plugin. In entrambi i casi, i pattern critici per CI sono: (1) `fail-fast: false` nella matrix per non perdere risultati degli altri shard/browser se uno fallisce, (2) upload sistematico di screenshot, video e trace come artifact, (3) timeout espliciti per evitare runner bloccati, (4) retry automatici (Playwright `--retries`, Cypress retry-ability integrata) per gestire la flakiness intrinseca dei test E2E. Il merge dei report di Playwright tramite blob report è essenziale quando si usa lo sharding: ogni shard produce un report parziale che viene combinato in un unico report HTML navigabile nel job finale.

---

## Mobile App CI/CD: React Native e Flutter

Le pipeline CI/CD per applicazioni mobile presentano sfide uniche rispetto al web: build nativa per iOS e Android, signing dei certificati, distribuzione tramite store o canali interni, e tempi di build significativamente più lunghi. GitHub Actions supporta runner macOS per le build iOS e runner Linux/Ubuntu per Android.

### React Native CI/CD

```yaml
# .github/workflows/mobile-react-native.yml
name: React Native CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: mobile-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  # === FASE 1: LINT E TEST ===
  quality:
    name: Lint & Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      - name: TypeScript check
        run: npx tsc --noEmit

      - name: ESLint
        run: npx eslint . --ext .ts,.tsx --max-warnings 0

      - name: Jest unit tests
        run: npx jest --coverage --ci --reporters=default
        env:
          CI: true

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage/

  # === FASE 2: BUILD ANDROID ===
  build-android:
    name: Build Android
    needs: quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      - uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'
          cache: 'gradle'

      - name: Cache Gradle
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
          key: gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}

      - name: Decode keystore
        run: echo "${{ secrets.ANDROID_KEYSTORE_BASE64 }}" | base64 -d > android/app/release.keystore

      - name: Build release APK
        working-directory: android
        run: ./gradlew assembleRelease
        env:
          ANDROID_KEYSTORE_PASSWORD: ${{ secrets.ANDROID_KEYSTORE_PASSWORD }}
          ANDROID_KEY_ALIAS: ${{ secrets.ANDROID_KEY_ALIAS }}
          ANDROID_KEY_PASSWORD: ${{ secrets.ANDROID_KEY_PASSWORD }}

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: android-release-apk
          path: android/app/build/outputs/apk/release/*.apk

  # === FASE 3: BUILD iOS ===
  build-ios:
    name: Build iOS
    needs: quality
    runs-on: macos-14
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      - name: Cache CocoaPods
        uses: actions/cache@v4
        with:
          path: ios/Pods
          key: pods-${{ runner.os }}-${{ hashFiles('ios/Podfile.lock') }}

      - name: Install CocoaPods
        working-directory: ios
        run: pod install --repo-update

      - name: Install Apple certificate and provisioning profile
        env:
          BUILD_CERTIFICATE_BASE64: ${{ secrets.IOS_BUILD_CERTIFICATE_BASE64 }}
          P12_PASSWORD: ${{ secrets.IOS_P12_PASSWORD }}
          BUILD_PROVISION_PROFILE_BASE64: ${{ secrets.IOS_PROVISION_PROFILE_BASE64 }}
          KEYCHAIN_PASSWORD: ${{ secrets.IOS_KEYCHAIN_PASSWORD }}
        run: |
          # Crea keychain temporanea
          CERTIFICATE_PATH=$RUNNER_TEMP/build_certificate.p12
          PP_PATH=$RUNNER_TEMP/build_pp.mobileprovision
          KEYCHAIN_PATH=$RUNNER_TEMP/app-signing.keychain-db

          echo -n "$BUILD_CERTIFICATE_BASE64" | base64 --decode -o $CERTIFICATE_PATH
          echo -n "$BUILD_PROVISION_PROFILE_BASE64" | base64 --decode -o $PP_PATH

          security create-keychain -p "$KEYCHAIN_PASSWORD" $KEYCHAIN_PATH
          security set-keychain-settings -lut 21600 $KEYCHAIN_PATH
          security unlock-keychain -p "$KEYCHAIN_PASSWORD" $KEYCHAIN_PATH

          security import $CERTIFICATE_PATH -P "$P12_PASSWORD" \
            -A -t cert -f pkcs12 -k $KEYCHAIN_PATH
          security list-keychain -d user -s $KEYCHAIN_PATH

          mkdir -p ~/Library/MobileDevice/Provisioning\ Profiles
          cp $PP_PATH ~/Library/MobileDevice/Provisioning\ Profiles

      - name: Build iOS archive
        working-directory: ios
        run: |
          xcodebuild -workspace App.xcworkspace \
            -scheme App \
            -configuration Release \
            -archivePath $RUNNER_TEMP/App.xcarchive \
            archive \
            CODE_SIGN_STYLE=Manual \
            DEVELOPMENT_TEAM=${{ secrets.IOS_TEAM_ID }}

      - name: Export IPA
        run: |
          xcodebuild -exportArchive \
            -archivePath $RUNNER_TEMP/App.xcarchive \
            -exportOptionsPlist ios/ExportOptions.plist \
            -exportPath $RUNNER_TEMP/export

      - name: Upload IPA
        uses: actions/upload-artifact@v4
        with:
          name: ios-release-ipa
          path: ${{ runner.temp }}/export/*.ipa

      - name: Cleanup keychain
        if: always()
        run: security delete-keychain $RUNNER_TEMP/app-signing.keychain-db

  # === FASE 4: DISTRIBUZIONE ===
  distribute:
    name: Distribute via Fastlane
    needs: [build-android, build-ios]
    if: github.ref == 'refs/heads/main'
    runs-on: macos-14
    steps:
      - uses: actions/checkout@v4

      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          path: build-artifacts/

      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.2'
          bundler-cache: true

      - name: Upload to TestFlight
        run: bundle exec fastlane ios beta
        env:
          APP_STORE_CONNECT_API_KEY: ${{ secrets.ASC_API_KEY }}

      - name: Upload to Google Play Internal
        run: bundle exec fastlane android internal
        env:
          GOOGLE_PLAY_JSON_KEY: ${{ secrets.GOOGLE_PLAY_JSON_KEY }}
```

### Flutter CI/CD

```yaml
# .github/workflows/mobile-flutter.yml
name: Flutter CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  # === ANALISI E TEST ===
  analyze-and-test:
    name: Analyze & Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.24.0'
          channel: 'stable'
          cache: true
          cache-key: flutter-${{ runner.os }}-${{ hashFiles('pubspec.lock') }}

      - run: flutter pub get

      - name: Analyze code
        run: flutter analyze --fatal-infos

      - name: Check formatting
        run: dart format --set-exit-if-changed .

      - name: Run tests with coverage
        run: flutter test --coverage --reporter=expanded

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: flutter-coverage
          path: coverage/lcov.info

  # === BUILD ANDROID ===
  build-android:
    name: Build Android AAB
    needs: analyze-and-test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.24.0'
          channel: 'stable'
          cache: true

      - run: flutter pub get

      - name: Decode keystore
        run: echo "${{ secrets.ANDROID_KEYSTORE_BASE64 }}" | base64 -d > android/app/upload-keystore.jks

      - name: Build App Bundle
        run: flutter build appbundle --release --build-number=${{ github.run_number }}
        env:
          ANDROID_KEYSTORE_PATH: android/app/upload-keystore.jks
          ANDROID_KEYSTORE_PASSWORD: ${{ secrets.ANDROID_KEYSTORE_PASSWORD }}
          ANDROID_KEY_ALIAS: ${{ secrets.ANDROID_KEY_ALIAS }}
          ANDROID_KEY_PASSWORD: ${{ secrets.ANDROID_KEY_PASSWORD }}

      - name: Upload AAB
        uses: actions/upload-artifact@v4
        with:
          name: android-aab
          path: build/app/outputs/bundle/release/*.aab

  # === BUILD iOS ===
  build-ios:
    name: Build iOS
    needs: analyze-and-test
    runs-on: macos-14
    steps:
      - uses: actions/checkout@v4

      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.24.0'
          channel: 'stable'
          cache: true

      - run: flutter pub get

      - name: Build iOS (no codesign for CI)
        run: flutter build ios --release --no-codesign --build-number=${{ github.run_number }}

      - name: Upload iOS build
        uses: actions/upload-artifact@v4
        with:
          name: ios-build
          path: build/ios/iphoneos/

  # === DISTRIBUZIONE EAS (Expo) ===
  distribute-eas:
    name: Distribute via EAS Build
    needs: [build-android, build-ios]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: expo/expo-github-action@v8
        with:
          eas-version: latest
          token: ${{ secrets.EXPO_TOKEN }}

      - name: Submit to EAS
        run: eas build --platform all --non-interactive --profile production
```

Le pipeline mobile richiedono attenzione a diversi aspetti critici che non esistono nel web: (1) **Code signing** — il certificato iOS e il keystore Android devono essere conservati come secrets base64-encoded e decodificati a runtime; la keychain temporanea su macOS deve essere sempre pulita nel blocco `if: always()` per evitare leak di credenziali. (2) **Runner macOS** — necessario per le build iOS e significativamente più costoso dei runner Linux (10x per i runner hosted); usare `macos-14` (Apple Silicon M1) per build 2-3x più veloci rispetto a `macos-13` (Intel). (3) **Distribuzione** — Fastlane rimane lo standard de facto per automatizzare l'upload su TestFlight e Google Play Internal Track; EAS Build (Expo Application Services) offre un'alternativa cloud-hosted che non richiede runner macOS per le build iOS. (4) **Build number** — usare `${{ github.run_number }}` come build number garantisce incremento monotono automatico senza stato esterno. (5) **Caching** — il caching di Gradle, CocoaPods e Flutter SDK è essenziale per mantenere tempi di build accettabili; senza cache, una build Flutter completa può superare i 30 minuti.

---

## Performance Testing Avanzato con Artillery

Oltre a Lighthouse (performance web) e k6 (load testing), Artillery offre un framework di performance testing moderno con supporto nativo per scenari HTTP, WebSocket, Socket.io e gRPC, particolarmente adatto per testare microservizi e API in pipeline CI/CD.

### Load Testing con Artillery in CI

```yaml
# .github/workflows/perf-artillery.yml
name: Performance Tests (Artillery)

on:
  pull_request:
    branches: [main]
    paths:
      - 'src/api/**'
      - 'artillery/**'
  workflow_dispatch:
    inputs:
      target_url:
        description: 'Target URL for load test'
        required: false
        default: 'https://staging.example.com'
      duration:
        description: 'Test duration in seconds'
        required: false
        default: '120'

permissions:
  contents: read
  pull-requests: write

jobs:
  artillery-test:
    name: Artillery Load Test
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci

      - name: Install Artillery
        run: npm install -g artillery@latest

      - name: Run load test
        run: |
          artillery run \
            --target ${{ inputs.target_url || vars.STAGING_URL || 'https://staging.example.com' }} \
            --output results.json \
            artillery/load-test.yaml
        env:
          API_TOKEN: ${{ secrets.PERF_TEST_API_TOKEN }}

      - name: Generate HTML report
        if: always()
        run: artillery report results.json --output report.html

      - name: Check performance thresholds
        run: |
          artillery run \
            --target ${{ inputs.target_url || vars.STAGING_URL || 'https://staging.example.com' }} \
            --ensure \
            artillery/load-test.yaml
        # --ensure fa fallire il test se le soglie definite nel file YAML vengono superate

      - name: Upload Artillery report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: artillery-report
          path: |
            results.json
            report.html
          retention-days: 14

      - name: Comment PR with results
        if: github.event_name == 'pull_request' && always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('results.json', 'utf8'));
            const agg = results.aggregate;

            const body = `## Artillery Load Test Results

            | Metrica | Valore |
            |---------|--------|
            | Richieste totali | ${agg.counters['http.requests'] || 'N/A'} |
            | Risposte 2xx | ${agg.counters['http.codes.200'] || 0} |
            | Risposte 4xx/5xx | ${(agg.counters['http.codes.400'] || 0) + (agg.counters['http.codes.500'] || 0)} |
            | Latenza p50 | ${agg.summaries?.['http.response_time']?.p50 || 'N/A'} ms |
            | Latenza p95 | ${agg.summaries?.['http.response_time']?.p95 || 'N/A'} ms |
            | Latenza p99 | ${agg.summaries?.['http.response_time']?.p99 || 'N/A'} ms |
            | RPS medio | ${agg.rates?.['http.request_rate'] || 'N/A'} |

            📊 Report completo disponibile negli artifact del workflow.`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

Lo scenario Artillery utilizza un file YAML con fasi di carico progressive e soglie di accettazione:

```yaml
# artillery/load-test.yaml
config:
  phases:
    - name: Warm-up
      duration: 30
      arrivalRate: 5
    - name: Ramp-up
      duration: 60
      arrivalRate: 5
      rampTo: 50
    - name: Sustained load
      duration: 120
      arrivalRate: 50
    - name: Spike test
      duration: 30
      arrivalRate: 100
  ensure:
    thresholds:
      - http.response_time.p95: 500
      - http.response_time.p99: 1000
      - http.codes.500: 0
  plugins:
    expect: {}

scenarios:
  - name: API Flow
    flow:
      - get:
          url: '/api/v1/health'
          expect:
            - statusCode: 200
      - think: 1
      - post:
          url: '/api/v1/search'
          json:
            query: 'test'
            limit: 20
          expect:
            - statusCode: 200
            - hasProperty: 'data.results'
      - think: 2
      - get:
          url: '/api/v1/products?page=1&limit=10'
          capture:
            - json: '$.data[0].id'
              as: 'productId'
          expect:
            - statusCode: 200
      - get:
          url: '/api/v1/products/{{ productId }}'
          expect:
            - statusCode: 200
```

Artillery si distingue da k6 per tre aspetti: (1) configurazione YAML dichiarativa anziché script JavaScript, rendendo i test più leggibili e manutenibili per team che non sono specialisti di performance; (2) il flag `--ensure` con soglie definite nel file YAML permette di integrare gate di qualità direttamente nella pipeline senza script aggiuntivi — se la latenza p95 supera 500ms o ci sono errori 500, il job fallisce automaticamente; (3) il plugin `expect` permette asserzioni funzionali inline, trasformando il load test in un test funzionale sotto carico. Il pattern di commentare la PR con i risultati aggregati fornisce visibilità immediata sull'impatto delle modifiche sulle performance senza dover navigare negli artifact o nei log del workflow.

---

## Anti-Pattern e Errori Comuni

### 1. Secrets nei Log

```yaml
# SBAGLIATO: il secret viene espanso e potrebbe comparire nei log di debug
- run: curl -H "Authorization: Bearer ${{ secrets.API_TOKEN }}" https://api.example.com

# CORRETTO: usare variabile d'ambiente — GitHub Actions masca automaticamente i secrets
- name: Call API
  run: curl -H "Authorization: Bearer $API_TOKEN" https://api.example.com
  env:
    API_TOKEN: ${{ secrets.API_TOKEN }}
```

### 2. Permessi Troppo Ampi

```yaml
# SBAGLIATO: permessi di default (tutti read-write)
permissions: write-all

# CORRETTO: permessi minimi necessari
permissions:
  contents: read
  packages: write
```

### 3. Azioni Non Pinnate

```yaml
# SBAGLIATO: il tag può essere spostato dall'autore
- uses: actions/checkout@v4

# MIGLIORE: pin al SHA del commit
- uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab  # v4.2.2

# PRATICO: tag con Renovate/Dependabot per auto-aggiornamento
# renovate: datasource=github-tags depName=actions/checkout
- uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab  # v4.2.2
```

### 4. Cancel-in-Progress su Deploy

```yaml
# SBAGLIATO: potrebbe cancellare un deploy a metà
concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: true

# CORRETTO per deploy: non cancellare, attendere
concurrency:
  group: deploy-production
  cancel-in-progress: false
```

### 5. Mancanza di Timeout

```yaml
# SBAGLIATO: job che potrebbe girare per ore se bloccato
jobs:
  build:
    runs-on: ubuntu-latest

# CORRETTO: timeout esplicito
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 15
```

### 6. Artefatti Senza Retention

```yaml
# SBAGLIATO: artefatti mantenuti per 90 giorni (default)
- uses: actions/upload-artifact@v4
  with:
    name: build
    path: dist/

# CORRETTO: retention appropriata
- uses: actions/upload-artifact@v4
  with:
    name: build
    path: dist/
    retention-days: 7    # PR artifacts
    # retention-days: 30  # Release artifacts
```

### 7. Fork PR con Secrets

```yaml
# SBAGLIATO: pull_request_target con checkout del codice della PR
# Questo espone i secrets a codice non fidato
on:
  pull_request_target:
    branches: [main]
jobs:
  build:
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # PERICOLOSO
      - run: npm test
        env:
          SECRET: ${{ secrets.MY_SECRET }}

# CORRETTO: separare l'esecuzione del codice non fidato
on:
  pull_request:
    branches: [main]
jobs:
  # Job senza secrets: esegue codice della PR
  test:
    steps:
      - uses: actions/checkout@v4
      - run: npm test

  # Job con secrets: solo su codice fidato
  deploy-preview:
    if: github.event.pull_request.head.repo.full_name == github.repository
    steps:
      - uses: actions/checkout@v4
      - run: npm run deploy:preview
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

### 8. Mancata Gestione dei Fallimenti

```yaml
# SBAGLIATO: il workflow si ferma al primo errore senza cleanup
- name: Deploy
  run: deploy.sh

# CORRETTO: gestire fallimenti con cleanup
- name: Deploy
  id: deploy
  run: deploy.sh
  continue-on-error: true

- name: Rollback on failure
  if: steps.deploy.outcome == 'failure'
  run: rollback.sh

- name: Fail the job if deploy failed
  if: steps.deploy.outcome == 'failure'
  run: exit 1
```

Questi anti-pattern sono tra le cause più comuni di problemi di sicurezza, spreco di risorse e pipeline inaffidabili. La regola generale è: permessi minimi, timeout espliciti, caching aggressivo, secrets mai esposti direttamente, e gestione esplicita di ogni possibile stato di errore. Il SHA-pinning con auto-update tramite Renovate o Dependabot bilancia sicurezza (immutabilità) e manutenibilità (aggiornamenti automatici verificati).

---

## Riferimenti

- **GitHub Docs — GitHub Actions**: https://docs.github.com/en/actions
- **GitHub Actions Marketplace**: https://github.com/marketplace?type=actions
- **AWS Actions**: https://github.com/aws-actions
- **Azure Actions**: https://github.com/Azure/actions
- **Google GitHub Actions**: https://github.com/google-github-actions
- **HashiCorp Terraform Action**: https://github.com/hashicorp/setup-terraform
- **semantic-release**: https://semantic-release.gitbook.io/
- **Lighthouse CI**: https://github.com/GoogleChrome/lighthouse-ci
- **k6 Load Testing**: https://k6.io/
- **Trivy Security Scanner**: https://trivy.dev/
- **Codecov**: https://codecov.io/
- **Slack GitHub Action**: https://github.com/slackapi/slack-github-action
- **Actions Runner Controller (ARC)**: https://github.com/actions/actions-runner-controller
- **Docker Build Push Action**: https://github.com/docker/build-push-action
- **release-please**: https://github.com/googleapis/release-please
- **golangci-lint Action**: https://github.com/golangci/golangci-lint-action
- **Rust Cache Action**: https://github.com/Swatinem/rust-cache
- **Turborepo CI Guide**: https://turborepo.dev/docs/guides/ci-vendors/github-actions
- **Nx Set SHAs Action**: https://github.com/nrwl/nx-set-shas
- **dorny/paths-filter**: https://github.com/dorny/paths-filter
- **GitHub OIDC Docs**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-cloud-providers
- **ArgoCD**: https://argo-cd.readthedocs.io/
- **Helm**: https://helm.sh/docs/
- **Flyway**: https://documentation.red-gate.com/fd/
- **Liquibase Setup Action**: https://github.com/liquibase/setup-liquibase
- **cargo-audit**: https://github.com/rustsec/rustsec/tree/main/cargo-audit
- **Distroless Images**: https://github.com/GoogleContainerTools/distroless
- **Flux CD**: https://fluxcd.io/
- **Liquibase**: https://www.liquibase.com/
- **Playwright**: https://playwright.dev/
- **Cypress**: https://www.cypress.io/
- **Artillery**: https://www.artillery.io/
- **Fastlane**: https://fastlane.tools/
- **EAS Build (Expo)**: https://docs.expo.dev/build/introduction/
- **Flutter CI/CD**: https://docs.flutter.dev/deployment/cd
- **cypress-io/github-action**: https://github.com/cypress-io/github-action
- **subosito/flutter-action**: https://github.com/subosito/flutter-action

---

## Esercizi Pratici

### Esercizio 1: Pipeline CI Node.js Completa

Costruisci una pipeline CI production-ready per un progetto Node.js:

```yaml
# .github/workflows/ci.yml
# 1. Trigger: push su main, PR verso main, path filter su src/ e test/
# 2. Permissions: contents read, pull-requests write (per coverage comment)
# 3. Concurrency: cancel-in-progress per PR
# 4. Job lint: eslint + prettier check
# 5. Job test: jest con coverage, upload coverage come artifact
# 6. Job build: npm run build, upload dist/ come artifact
# 7. Job security: npm audit + Trivy fs scan
# 8. Caching: npm cache con restore-keys per fallback

# Verifica:
# - Pushare una PR con un lint error → il job lint fallisce
# - Pushare una PR corretta → tutti i job passano
# - Verificare che la cache venga riusata al secondo push
```

**Criteri di successo:** pipeline completa sotto i 5 minuti, cache hit dal secondo run, coverage report visibile.

### Esercizio 2: Deploy Multi-Ambiente con OIDC

Implementa un deployment pipeline che deploya su AWS senza credenziali statiche:

```yaml
# 1. Configurare OIDC identity provider su AWS IAM
# 2. Creare IAM role con trust policy per il repository GitHub
# 3. Workflow deploy:
#    - Job deploy-staging: trigger su merge in main, usa OIDC per assumere role staging
#    - Job deploy-production: trigger su tag v*.*.*, usa OIDC per assumere role production
#    - Environment protection: staging auto, production con approvazione manuale
# 4. Health check post-deploy con curl + retry
# 5. Rollback automatico se il health check fallisce

# Attenzione: non committare credenziali AWS!
# Usare aws-actions/configure-aws-credentials@v4 con role-to-assume
```

### Esercizio 3: Build Docker Multi-Architettura

Crea un workflow che builda e pusha immagini Docker multi-architettura:

```yaml
# 1. Usare docker/setup-buildx-action per buildx
# 2. Usare docker/setup-qemu-action per emulazione cross-platform
# 3. Login a GHCR (GitHub Container Registry)
# 4. Build per linux/amd64 e linux/arm64
# 5. Caching con cache-from/cache-to type=gha
# 6. Tag: latest + SHA commit + semver dal tag git
# 7. Aggiungere SBOM e provenance attestation

# Verifica:
# - L'immagine è presente su ghcr.io con i tag corretti
# - docker manifest inspect mostra entrambe le architetture
# - La cache riduce il tempo di build del 50%+
```

### Esercizio 4: Security Scanning Integrato

Implementa un workflow di security scanning completo:

```yaml
# .github/workflows/security.yml
# 1. CodeQL per analisi statica (JavaScript + Python)
# 2. Trivy per vulnerabilità nelle dipendenze e nei container
# 3. Gitleaks per rilevamento di secrets nel codice
# 4. License checker per compliance delle dipendenze
# 5. Upload risultati come SARIF per integrazione con GitHub Security tab
# 6. Trigger: push su main + PR + schedule settimanale

# Test:
# - Introdurre intenzionalmente una dipendenza vulnerabile → Trivy la rileva
# - Aggiungere un secret finto nel codice → Gitleaks lo blocca
# - Verificare che i risultati appaiano nella tab Security del repository
```

### Esercizio 5: Release Automation Completa

Configura semantic-release per automatizzare il ciclo di rilascio:

```yaml
# 1. Installare e configurare semantic-release con .releaserc.json
# 2. Plugin: commit-analyzer, release-notes-generator, changelog, npm, github, git
# 3. Configurare Conventional Commits come preset
# 4. Il workflow deve:
#    - Analizzare i commit dalla ultima release
#    - Determinare il bump (major/minor/patch)
#    - Generare CHANGELOG.md
#    - Creare tag e GitHub Release con release notes
#    - Pubblicare su npm (se applicabile)
# 5. Aggiungere notifica Slack con il risultato

# Verifica:
# - Commit "feat: new feature" → bump minor
# - Commit "fix: bug fix" → bump patch
# - Commit "feat!: breaking change" → bump major
# - CHANGELOG.md aggiornato con le note della release
```

---

## Letture Consigliate

- **Libro**: "Learning GitHub Actions" di Brent Laster, O'Reilly Media, 2024 — capitoli su CI/CD patterns e deployment strategies
- **Libro**: "Continuous Delivery" di Jez Humble e David Farley, Addison-Wesley, 2010 — principi fondamentali di deployment pipeline
- **Libro**: "Release It!" di Michael Nygard, Pragmatic Programmers, 2nd edition, 2018 — stability patterns per deploy in produzione
- **GitHub Blog**: "Security hardening for GitHub Actions" — https://github.blog/security/supply-chain-security/security-hardening-for-github-actions/ (consultato: 2026-05-24)
- **Semantic Release docs**: https://semantic-release.gitbook.io/semantic-release/ (consultato: 2026-05-24)
- **SLSA Framework**: "Supply-chain Levels for Software Artifacts" — https://slsa.dev/ (consultato: 2026-05-24)

---

## Collegamenti Incrociati

| Modulo | Collegamento | Relazione |
|--------|-------------|-----------|
| 18 | [18-github-actions-avanzate.md](18-github-actions-avanzate.md) | Tecniche avanzate — matrix, cache, environments usati nelle ricette |
| 17 | [17-github-actions-workflow-sintassi.md](17-github-actions-workflow-sintassi.md) | Sintassi workflow — base per scrivere le pipeline |
| 21 | [21-github-actions-self-hosted-runners.md](21-github-actions-self-hosted-runners.md) | Self-hosted runners — per pipeline con requisiti hardware specifici |
| 16 | [16-github-security-scanning.md](16-github-security-scanning.md) | Security scanning — Dependabot, CodeQL, secret scanning |
| 14 | [14-github-packages-pages-releases.md](14-github-packages-pages-releases.md) | Packages e Releases — destinazione dei deploy e delle pubblicazioni |
| 24 | [24-devops-completo-con-github.md](24-devops-completo-con-github.md) | Pipeline DevOps completa — integra tutte le ricette CI/CD |
| 26 | [26-oidc-cloud-credentials.md](26-oidc-cloud-credentials.md) | OIDC — credenziali cloud senza secrets statici |
| 27 | [27-supply-chain-attestation-slsa.md](27-supply-chain-attestation-slsa.md) | Supply chain — attestation e SBOM per build sicure |
| 05 | [05-progetti-pratici.md](05-progetti-pratici.md) | Progetti pratici — esempi concreti di pipeline |

---

## Glossario Locale

| Termine | Definizione |
|---------|------------|
| **CI (Continuous Integration)** | Pratica di integrare e testare automaticamente le modifiche ad ogni push o pull request |
| **CD (Continuous Delivery/Deployment)** | Pratica di deployare automaticamente le build validate in ambienti staging o produzione |
| **CodeQL** | Motore di analisi statica di GitHub che tratta il codice come database interrogabile per trovare vulnerabilità |
| **Concurrency** | Meccanismo GitHub Actions per limitare esecuzioni parallele dello stesso workflow, con opzione cancel-in-progress |
| **GHCR** | GitHub Container Registry — registro OCI per immagini Docker integrato in GitHub Packages |
| **Gitleaks** | Tool open-source che scansiona la storia Git per rilevare secrets (API key, password, token) committati |
| **OIDC** | OpenID Connect — protocollo usato per autenticazione federata con cloud provider senza credenziali statiche |
| **SARIF** | Static Analysis Results Interchange Format — formato standard per risultati di analisi statica, integrato nella Security tab |
| **semantic-release** | Tool che automatizza versioning e release basandosi sulla convenzione dei commit message |
| **SHA-pinning** | Fissare le actions di terze parti all'hash SHA del commit anziché al tag, per evitare modifiche malevole |
| **SLSA** | Supply-chain Levels for Software Artifacts — framework per garantire l'integrità della supply chain software |
| **Trivy** | Scanner di vulnerabilità open-source per immagini container, filesystem, repository Git e configurazioni IaC |
| **concurrency group** | Identificatore che raggruppa workflow run per lo stesso branch/PR, permettendo cancellazione dei duplicati |
| **path filter** | Clausola `paths:` nel trigger che limita l'esecuzione del workflow ai file modificati in percorsi specifici |
| **ARC (Actions Runner Controller)** | Controller Kubernetes che orchestra e scala automaticamente self-hosted runners per GitHub Actions come pod efimeri |
| **ArgoCD** | Tool di continuous deployment GitOps per Kubernetes che sincronizza lo stato del cluster con i manifesti in un repository Git |
| **Blue-Green Deployment** | Strategia di deploy che mantiene due ambienti identici e switcha il traffico istantaneamente, permettendo rollback immediato |
| **Canary Deployment** | Strategia di deploy che invia una piccola percentuale di traffico alla nuova versione e la incrementa progressivamente dopo monitoraggio |
| **Composite Action** | Azione GitHub Actions che raggruppa più step in una singola unità riutilizzabile all'interno di un job |
| **Distroless** | Immagini container minimali che contengono solo l'applicazione e le sue dipendenze runtime, senza shell o package manager |
| **Drift Detection** | Processo schedulato che confronta lo stato reale dell'infrastruttura con quello dichiarato nel codice IaC per identificare modifiche manuali |
| **Flyway** | Tool di database migration che applica script SQL versionati in ordine sequenziale per gestire l'evoluzione dello schema |
| **Helm** | Package manager per Kubernetes che usa chart (template di manifesti) per definire, installare e aggiornare applicazioni |
| **Matrix Strategy** | Funzionalità GitHub Actions che genera automaticamente multiple esecuzioni di un job per ogni combinazione di variabili definite |
| **Monorepo** | Strategia di organizzazione del codice in cui più progetti o pacchetti risiedono nello stesso repository Git |
| **release-please** | Tool di Google che automatizza il versioning e la release creando PR di release con changelog generato dai conventional commits |
| **Reusable Workflow** | Workflow GitHub Actions che può essere invocato da altri workflow tramite `workflow_call`, incapsulando interi set di job |
| **Rolling Deployment** | Strategia di deploy che aggiorna le istanze gradualmente, sostituendo le vecchie versioni una alla volta mantenendo il servizio operativo |
| **Runner Scale Set** | Configurazione ARC che definisce un pool di runner auto-scalanti su Kubernetes con limiti min/max configurabili |
| **Workload Identity Federation** | Meccanismo di autenticazione che scambia token OIDC esterni con credenziali cloud temporanee, eliminando secrets statici |
| **Artillery** | Framework di performance testing open-source con configurazione YAML dichiarativa, supporto per HTTP/WebSocket/gRPC e soglie di accettazione integrate |
| **Cypress** | Framework di E2E testing basato su browser con time-travel debugging, parallelizzazione via Cypress Cloud e architettura in-process |
| **EAS Build** | Expo Application Services Build — servizio cloud-hosted per build native iOS e Android senza necessità di runner macOS locali |
| **Fastlane** | Tool di automazione per build e distribuzione di app mobile, supporta upload automatico su TestFlight, App Store e Google Play |
| **Flux CD** | Tool CNCF-graduated di continuous deployment GitOps per Kubernetes, basato su controller CRD nativi con approccio decentralizzato |
| **Liquibase** | Tool enterprise di database migration con changelog declarativi, supporto per preconditions, rollback espliciti e contesti di esecuzione |
| **Playwright** | Framework E2E testing di Microsoft con supporto nativo per Chromium, Firefox e WebKit, sharding built-in e trace recording |
| **Sharding** | Tecnica di distribuzione parallela dei test su più runner, dove ogni shard esegue un sottoinsieme dei test per ridurre il tempo totale |
