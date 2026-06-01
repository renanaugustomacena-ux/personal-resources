---
corso: "GitHub e Git Actions"
fase: "5 — Sicurezza"
modulo: 26
titolo: "OIDC Cloud Credentials in GitHub Actions"
versione: "OpenID Connect Core 1.0 / GitHub Actions OIDC GA"
livello: "Avanzato"
prerequisiti:
  - "17-github-actions-workflow-sintassi"
  - "18-github-actions-avanzate"
  - "16-github-security-scanning"
obiettivi:
  - "Comprendere il flusso OIDC tra GitHub Actions e i cloud provider"
  - "Configurare IAM OIDC Provider su AWS, Azure e GCP"
  - "Analizzare e vincolare i claim del JWT token (audience, subject, workflow_ref)"
  - "Implementare trust policy multi-environment con least-privilege"
  - "Diagnosticare e risolvere i failure comuni nel token exchange"
tag: [oidc, jwt, aws, azure, gcp, workload-identity, federated-credentials, zero-secrets]
---

# OIDC Cloud Credentials in GitHub Actions

> **Modulo 26** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Comprendere il flusso OIDC tra GitHub Actions e i cloud provider
> 2. Configurare IAM OIDC Provider su AWS, Azure e GCP
> 3. Analizzare e vincolare i claim del JWT token (audience, subject, workflow_ref)
> 4. Implementare trust policy multi-environment con least-privilege
> 5. Diagnosticare e risolvere i failure comuni nel token exchange

---

## Indice

1. [Idee guida](#idee-guida)
2. [Perché OIDC e non static secrets](#perché-oidc-e-non-static-secrets)
3. [Come funziona OIDC in GitHub Actions](#come-funziona-oidc-in-github-actions)
4. [Anatomia del JWT token](#anatomia-del-jwt-token)
5. [Audience e Subject claims](#audience-e-subject-claims)
6. [Configurare AWS — IAM OIDC Provider](#configurare-aws--iam-oidc-provider)
7. [Configurare Azure — Federated Credentials](#configurare-azure--federated-credentials)
8. [Configurare GCP — Workload Identity Federation](#configurare-gcp--workload-identity-federation)
9. [Token exchange flow in dettaglio](#token-exchange-flow-in-dettaglio)
10. [Multi-environment setups](#multi-environment-setups)
11. [Organization-level policies](#organization-level-policies)
12. [Security benefits e confronto con static secrets](#security-benefits-e-confronto-con-static-secrets)
13. [Debugging OIDC failures](#debugging-oidc-failures)
14. [Pattern avanzati](#pattern-avanzati)
15. [Esercizi](#esercizi)
16. [Troubleshooting — 20 problemi comuni](#troubleshooting--20-problemi-comuni)
17. [FAQ — 20 domande e risposte](#faq--20-domande-e-risposte)
18. [Configurare HashiCorp Vault — JWT Auth con GitHub OIDC](#configurare-hashicorp-vault--jwt-auth-con-github-oidc)
19. [Configurare Terraform Cloud / HCP Terraform — Dynamic Provider Credentials](#configurare-terraform-cloud--hcp-terraform--dynamic-provider-credentials)
20. [AWS Session Tags e Principal Tags con OIDC](#aws-session-tags-e-principal-tags-con-oidc)
21. [Azure Flexible Federated Identity Credentials](#azure-flexible-federated-identity-credentials)
22. [Repository Custom Properties nei token OIDC](#repository-custom-properties-nei-token-oidc)
23. [Security hardening avanzato — Checklist operativa](#security-hardening-avanzato--checklist-operativa)
24. [Vettori di attacco e mitigazioni](#vettori-di-attacco-e-mitigazioni)
25. [Architettura OIDC per organizzazioni enterprise](#architettura-oidc-per-organizzazioni-enterprise)
26. [Monitoring, alerting e compliance](#monitoring-alerting-e-compliance)
27. [Migrazione da secret statici a OIDC — Playbook completo](#migrazione-da-secret-statici-a-oidc--playbook-completo)
28. [OIDC con provider aggiuntivi](#oidc-con-provider-aggiuntivi)
29. [Confronto dettagliato tra cloud provider](#confronto-dettagliato-tra-cloud-provider)
30. [Scenari reali e case study](#scenari-reali-e-case-study)
31. [Esercizi avanzati — Laboratori pratici](#esercizi-avanzati--laboratori-pratici)
32. [Troubleshooting avanzato — 20 problemi aggiuntivi](#troubleshooting-avanzato--20-problemi-aggiuntivi)
33. [FAQ avanzate — 20 domande aggiuntive](#faq-avanzate--20-domande-aggiuntive)
34. [Letture consigliate](#letture-consigliate)
35. [Glossario](#glossario)

---

## Idee guida

1. **OIDC = workload identity federation.** Nessun secret long-lived nel repository.
2. **AWS, Azure, GCP supportano nativamente** il trust verso `token.actions.githubusercontent.com`.
3. **Trust policy vincolata** a `repo`, `branch`, `environment`, `workflow`.
4. **Audit trail completo:** ogni autenticazione registra quale workflow, da quale ref, a quale ora.
5. **Rotation automatica:** il token vive pochi minuti, non esiste un secret da ruotare.

---

## Perché OIDC e non static secrets

### Il problema dei secret statici

I secret statici (access key, client secret, service account key) presentano rischi strutturali:

| Rischio | Descrizione |
|---|---|
| **Leaking** | Un secret in un log, un artifact, un fork: compromissione immediata |
| **Rotation burden** | Rotazione manuale ogni 90 giorni (best practice) o mai (realtà) |
| **Blast radius** | Un secret compromesso dà accesso fino a revoca manuale |
| **Audit gap** | Difficile distinguere chi ha usato lo stesso secret |
| **Scope creep** | Secret riutilizzato in più workflow con scope diversi |

### La soluzione OIDC

Con OIDC il workflow **non possiede mai un secret**. Invece:

1. GitHub emette un JWT firmato che identifica il workflow.
2. Il cloud provider verifica la firma e i claims.
3. Il cloud provider emette credenziali temporanee (15 min–1 h).
4. Le credenziali scadono automaticamente.

```text
┌──────────────────┐     1. Richiede JWT        ┌──────────────────────────────┐
│  GitHub Actions  │ ──────────────────────────► │  GitHub OIDC Provider        │
│  Workflow        │ ◄────────────────────────── │  token.actions.github...com  │
│                  │     2. JWT firmato           └──────────────────────────────┘
│                  │
│                  │     3. Presenta JWT          ┌──────────────────────────────┐
│                  │ ──────────────────────────► │  Cloud Provider (AWS/Azure/  │
│                  │ ◄────────────────────────── │  GCP) STS / Token Service    │
│                  │     4. Credenziali temp.     └──────────────────────────────┘
└──────────────────┘
```

**Risultato:** zero secret nel repository, zero rotazione manuale, audit granulare per workflow.

---

## Come funziona OIDC in GitHub Actions

### Prerequisiti

1. Il workflow deve dichiarare `permissions: id-token: write`.
2. Il cloud provider deve avere un trust configurato verso `token.actions.githubusercontent.com`.
3. L'action del provider deve richiedere un token al runtime.

### Flusso passo-passo

```text
1. Il runner avvia il job.
2. L'action (es. aws-actions/configure-aws-credentials) chiama
   l'API interna di GitHub: GET $ACTIONS_ID_TOKEN_REQUEST_URL
   con header Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN
3. GitHub restituisce un JWT firmato con le informazioni del workflow.
4. L'action invia il JWT al cloud provider STS endpoint.
5. Il cloud provider:
   a. Scarica le chiavi pubbliche JWKS da GitHub.
   b. Verifica la firma del JWT.
   c. Valida i claims (issuer, audience, subject, ecc.).
   d. Se tutto ok, emette credenziali temporanee.
6. L'action imposta le variabili d'ambiente (AWS_ACCESS_KEY_ID, ecc.).
7. I passi successivi usano le credenziali temporanee.
8. Le credenziali scadono (default: 1 ora per AWS).
```

### Variabili d'ambiente interne

Il runner di GitHub Actions espone due variabili **non visibili nei log**:

| Variabile | Scopo |
|---|---|
| `ACTIONS_ID_TOKEN_REQUEST_URL` | Endpoint interno per richiedere il JWT |
| `ACTIONS_ID_TOKEN_REQUEST_TOKEN` | Bearer token per autenticarsi verso l'endpoint |

Queste variabili esistono **solo** se `permissions.id-token` è `write`.

### Richiedere il token manualmente

```bash
# Dentro un step di GitHub Actions
OIDC_TOKEN=$(curl -sS \
  -H "Authorization: bearer ${ACTIONS_ID_TOKEN_REQUEST_TOKEN}" \
  "${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=sts.amazonaws.com" \
  | jq -r '.value')

echo "Token length: ${#OIDC_TOKEN}"
# NON loggare mai il token completo
```

---

## Anatomia del JWT token

Il JWT emesso da GitHub ha tre parti: header, payload, signature.

### Header

```json
{
  "typ": "JWT",
  "alg": "RS256",
  "kid": "xxxxx-xxxxx-xxxxx",
  "x5t": "yyyyy"
}
```

### Payload — claims standard

```json
{
  "iss": "https://token.actions.githubusercontent.com",
  "sub": "repo:myorg/myrepo:ref:refs/heads/main",
  "aud": "https://github.com/myorg",
  "exp": 1716400000,
  "nbf": 1716396400,
  "iat": 1716396400,
  "jti": "unique-token-id"
}
```

### Payload — claims GitHub-specifici

```json
{
  "ref": "refs/heads/main",
  "sha": "abc123def456",
  "repository": "myorg/myrepo",
  "repository_owner": "myorg",
  "repository_owner_id": "12345",
  "repository_id": "67890",
  "repository_visibility": "private",
  "actor": "username",
  "actor_id": "11111",
  "workflow": "Deploy",
  "workflow_ref": "myorg/myrepo/.github/workflows/deploy.yml@refs/heads/main",
  "workflow_sha": "abc123def456",
  "event_name": "push",
  "run_id": "123456789",
  "run_number": "42",
  "run_attempt": "1",
  "runner_environment": "github-hosted",
  "environment": "production",
  "environment_node_id": "EN_xxxxx",
  "job_workflow_ref": "myorg/myrepo/.github/workflows/deploy.yml@refs/heads/main",
  "job_workflow_sha": "abc123def456"
}
```

### Claims chiave per trust policy

| Claim | Esempio | Uso in trust policy |
|---|---|---|
| `sub` | `repo:org/repo:ref:refs/heads/main` | Vincolo primario — chi può assumere il ruolo |
| `aud` | `sts.amazonaws.com` | Impedisce token replay verso altri provider |
| `repository` | `myorg/myrepo` | Filtro per repository specifico |
| `repository_owner` | `myorg` | Filtro per organizzazione |
| `environment` | `production` | Vincolo per environment GitHub |
| `ref` | `refs/heads/main` | Vincolo per branch/tag |
| `workflow_ref` | `org/repo/.github/workflows/x.yml@ref` | Vincolo per workflow specifico |
| `runner_environment` | `github-hosted` | Solo runner hosted (non self-hosted) |

### Decodifica per debug

```bash
# Decodifica payload senza verifica firma (solo debug)
echo "$OIDC_TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | jq .
```

---

## Audience e Subject claims

### Audience (`aud`)

L'audience identifica il **destinatario previsto** del token. Ogni cloud provider usa un valore diverso:

| Provider | Audience default |
|---|---|
| AWS | `sts.amazonaws.com` |
| Azure | API URI dell'applicazione registrata (es. `api://AzureADTokenExchange`) |
| GCP | URL del Workload Identity Provider |
| Custom | Qualsiasi stringa concordata |

L'audience si specifica nel workflow:

```yaml
# AWS — audience implicito nell'action
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123:role/deploy
    aws-region: eu-central-1
    # audience: sts.amazonaws.com  # default

# Azure — audience personalizzato
- uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
    # audience è api://AzureADTokenExchange per default

# GCP — audience esplicito
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: projects/123/locations/global/workloadIdentityPools/pool/providers/ghprovider
    service_account: deploy@project.iam.gserviceaccount.com
```

### Subject (`sub`)

Il subject identifica **chi** sta richiedendo il token. Il formato varia in base al contesto:

| Contesto | Formato `sub` |
|---|---|
| Push a branch | `repo:ORG/REPO:ref:refs/heads/BRANCH` |
| Push a tag | `repo:ORG/REPO:ref:refs/tags/TAG` |
| Pull request | `repo:ORG/REPO:pull_request` |
| Environment | `repo:ORG/REPO:environment:ENV_NAME` |
| Reusable workflow | `repo:ORG/REPO:ref:refs/heads/BRANCH` (del caller) |

**Attenzione ai filtri:** se la trust policy richiede `sub` = `repo:org/repo:ref:refs/heads/main` ma il workflow usa un environment, il `sub` sarà `repo:org/repo:environment:production` → **mismatch → errore**.

### Personalizzare i subject claims

GitHub permette di personalizzare i claims nel subject a livello di organizzazione o repository:

```bash
# Via API — personalizzare claims per repository
curl -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/ORG/REPO/actions/oidc/customization/sub" \
  -d '{
    "use_default": false,
    "include_claim_keys": ["repo", "context", "ref"]
  }'
```

Con questa configurazione il subject diventa:

```text
repo:ORG/REPO:environment:production:ref:refs/heads/main
```

---

## Configurare AWS — IAM OIDC Provider

### Passo 1 — Creare l'OIDC Identity Provider

```bash
# Ottenere il thumbprint del certificato TLS
THUMBPRINT=$(openssl s_client -connect token.actions.githubusercontent.com:443 \
  -servername token.actions.githubusercontent.com < /dev/null 2>/dev/null \
  | openssl x509 -fingerprint -noout \
  | sed 's/://g' | cut -d= -f2 | tr '[:upper:]' '[:lower:]')

# Creare il provider (una volta per account AWS)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list "$THUMBPRINT"
```

> **Nota 2024+:** AWS non richiede più il thumbprint per OIDC provider noti, ma è buona pratica specificarlo.

### Passo 2 — Creare il IAM Role con trust policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:*"
        }
      }
    }
  ]
}
```

**Varianti della trust policy per diversi scenari:**

```json
// Solo branch main
"StringEquals": {
  "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:ref:refs/heads/main"
}

// Solo environment production
"StringEquals": {
  "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:environment:production"
}

// Multipli repository della stessa org
"StringLike": {
  "token.actions.githubusercontent.com:sub": "repo:myorg/*:ref:refs/heads/main"
}

// Solo tag di release
"StringLike": {
  "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:ref:refs/tags/v*"
}
```

### Passo 3 — Permission policy del ruolo

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-deploy-bucket",
        "arn:aws:s3:::my-deploy-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    }
  ]
}
```

### Passo 4 — Workflow completo

```yaml
name: Deploy to AWS via OIDC
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

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy
          role-session-name: gha-deploy-${{ github.run_id }}
          aws-region: eu-central-1
          role-duration-seconds: 900  # 15 minuti

      - name: Verify identity
        run: aws sts get-caller-identity

      - name: Deploy
        run: aws s3 sync ./build s3://my-deploy-bucket --delete
```

### Passo 5 — Terraform per OIDC provider + ruolo

```hcl
# oidc.tf
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]

  tags = {
    Purpose = "GitHub Actions OIDC"
  }
}

resource "aws_iam_role" "github_actions" {
  name = "github-actions-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:myorg/myrepo:*"
          }
        }
      }
    ]
  })

  tags = {
    ManagedBy = "terraform"
  }
}

resource "aws_iam_role_policy" "deploy" {
  name = "deploy-policy"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::my-deploy-bucket",
          "arn:aws:s3:::my-deploy-bucket/*"
        ]
      }
    ]
  })
}
```

---

## Configurare Azure — Federated Credentials

### Passo 1 — Registrare un'applicazione Azure AD

```bash
# Creare l'app registration
az ad app create --display-name "github-actions-deploy"

# Ottenere l'application ID
APP_ID=$(az ad app list --display-name "github-actions-deploy" \
  --query "[0].appId" -o tsv)

# Creare il service principal
az ad sp create --id "$APP_ID"
```

### Passo 2 — Aggiungere federated credential

```bash
# Creare la federated credential per il branch main
az ad app federated-credential create --id "$APP_ID" --parameters '{
  "name": "github-main-branch",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:myorg/myrepo:ref:refs/heads/main",
  "description": "GitHub Actions deploy from main",
  "audiences": ["api://AzureADTokenExchange"]
}'

# Creare una credential separata per l'environment production
az ad app federated-credential create --id "$APP_ID" --parameters '{
  "name": "github-production-env",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:myorg/myrepo:environment:production",
  "description": "GitHub Actions deploy to production environment",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

### Passo 3 — Assegnare permessi RBAC

```bash
# Contributor su un resource group
az role assignment create \
  --assignee "$APP_ID" \
  --role "Contributor" \
  --scope "/subscriptions/SUB_ID/resourceGroups/my-rg"

# AcrPush su un container registry
az role assignment create \
  --assignee "$APP_ID" \
  --role "AcrPush" \
  --scope "/subscriptions/SUB_ID/resourceGroups/my-rg/providers/Microsoft.ContainerRegistry/registries/myacr"
```

### Passo 4 — Workflow completo

```yaml
name: Deploy to Azure via OIDC
on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

env:
  AZURE_CLIENT_ID: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  AZURE_TENANT_ID: "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
  AZURE_SUBSCRIPTION_ID: "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz"

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login via OIDC
        uses: azure/login@v2
        with:
          client-id: ${{ env.AZURE_CLIENT_ID }}
          tenant-id: ${{ env.AZURE_TENANT_ID }}
          subscription-id: ${{ env.AZURE_SUBSCRIPTION_ID }}

      - name: Verify identity
        run: az account show

      - name: Deploy to App Service
        uses: azure/webapps-deploy@v3
        with:
          app-name: my-web-app
          package: ./build
```

### Passo 5 — Managed Identity alternativa

Per scenari con Azure Kubernetes Service o VM:

```bash
# Creare User-Assigned Managed Identity
az identity create \
  --name github-actions-identity \
  --resource-group my-rg

IDENTITY_ID=$(az identity show \
  --name github-actions-identity \
  --resource-group my-rg \
  --query "principalId" -o tsv)

# Aggiungere federated credential alla managed identity
az identity federated-credential create \
  --name github-federation \
  --identity-name github-actions-identity \
  --resource-group my-rg \
  --issuer "https://token.actions.githubusercontent.com" \
  --subject "repo:myorg/myrepo:environment:production" \
  --audiences "api://AzureADTokenExchange"
```

### Terraform per Azure

```hcl
# azure_oidc.tf
resource "azuread_application" "github_actions" {
  display_name = "github-actions-deploy"
}

resource "azuread_service_principal" "github_actions" {
  client_id = azuread_application.github_actions.client_id
}

resource "azuread_application_federated_identity_credential" "main_branch" {
  application_id = azuread_application.github_actions.id
  display_name   = "github-main-branch"
  description    = "GitHub Actions deploy from main"
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:myorg/myrepo:ref:refs/heads/main"
}

resource "azuread_application_federated_identity_credential" "production_env" {
  application_id = azuread_application.github_actions.id
  display_name   = "github-production-env"
  description    = "GitHub Actions deploy to production"
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:myorg/myrepo:environment:production"
}

resource "azurerm_role_assignment" "contributor" {
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Contributor"
  principal_id         = azuread_service_principal.github_actions.object_id
}
```

---

## Configurare GCP — Workload Identity Federation

### Passo 1 — Creare Workload Identity Pool

```bash
# Abilitare le API necessarie
gcloud services enable iamcredentials.googleapis.com
gcloud services enable sts.googleapis.com

# Creare il pool
gcloud iam workload-identity-pools create "github-pool" \
  --project="my-project" \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

### Passo 2 — Creare il Provider

```bash
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="my-project" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Actions Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository_owner == 'myorg'" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### Passo 3 — Creare Service Account e binding

```bash
# Creare il service account
gcloud iam service-accounts create github-actions-deploy \
  --project="my-project" \
  --display-name="GitHub Actions Deploy"

# Pool ID completo
POOL_ID="projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool"

# Binding: il pool può impersonare il service account
gcloud iam service-accounts add-iam-policy-binding \
  "github-actions-deploy@my-project.iam.gserviceaccount.com" \
  --project="my-project" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/myorg/myrepo"

# Dare permessi al service account
gcloud projects add-iam-policy-binding my-project \
  --member="serviceAccount:github-actions-deploy@my-project.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

### Passo 4 — Attribute conditions avanzate

```bash
# Solo branch main
--attribute-condition="assertion.repository_owner == 'myorg' && assertion.ref == 'refs/heads/main'"

# Solo repository specifico + environment
--attribute-condition="assertion.repository == 'myorg/myrepo' && assertion.environment == 'production'"

# Multipli repository
--attribute-condition="assertion.repository_owner == 'myorg' && assertion.repository in ['myorg/frontend', 'myorg/backend']"
```

### Passo 5 — Workflow completo

```yaml
name: Deploy to GCP via OIDC
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
          workload_identity_provider: "projects/123456/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
          service_account: "github-actions-deploy@my-project.iam.gserviceaccount.com"
          token_format: "access_token"

      - name: Setup gcloud
        uses: google-github-actions/setup-gcloud@v2

      - name: Verify identity
        run: gcloud auth list

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy my-service \
            --image=gcr.io/my-project/my-service:${{ github.sha }} \
            --region=europe-west1 \
            --platform=managed
```

### Terraform per GCP

```hcl
# gcp_oidc.tf
resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Actions Provider"

  attribute_mapping = {
    "google.subject"             = "assertion.sub"
    "attribute.actor"            = "assertion.actor"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
    "attribute.ref"              = "assertion.ref"
  }

  attribute_condition = "assertion.repository_owner == '${var.github_org}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "github_actions" {
  project      = var.project_id
  account_id   = "github-actions-deploy"
  display_name = "GitHub Actions Deploy"
}

resource "google_service_account_iam_member" "workload_identity" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_org}/${var.github_repo}"
}

resource "google_project_iam_member" "storage" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}
```

---

## Token exchange flow in dettaglio

### Sequenza completa

```text
Tempo  Attore                Azione
─────  ────────────────────  ──────────────────────────────────────────
t0     Runner                Job inizia, variabili OIDC disponibili
t1     Action                POST $ACTIONS_ID_TOKEN_REQUEST_URL
                              → Header: Authorization: bearer $TOKEN
                              → Body: { "audience": "sts.amazonaws.com" }
t2     GitHub OIDC Service   Genera JWT:
                              - Firma con chiave privata RSA
                              - Include claims del workflow
                              - exp = iat + 5 minuti (breve!)
t3     Action                Riceve JWT (campo .value nella response)
t4     Action                Chiama STS del cloud provider:
                              AWS:   POST https://sts.amazonaws.com
                                     Action=AssumeRoleWithWebIdentity
                                     WebIdentityToken=<JWT>
                                     RoleArn=<arn>
                              Azure: POST https://login.microsoftonline.com/
                                     tenant/oauth2/v2.0/token
                                     client_assertion=<JWT>
                              GCP:   POST https://sts.googleapis.com/v1/token
                                     subjectToken=<JWT>
t5     Cloud STS             Fetch JWKS da:
                              https://token.actions.githubusercontent.com/
                              .well-known/jwks
t6     Cloud STS             Verifica firma JWT con chiave pubblica
t7     Cloud STS             Valida claims: iss, aud, sub, exp, nbf
t8     Cloud STS             Verifica trust policy / federated credential
t9     Cloud STS             Emette credenziali temporanee:
                              AWS:   AccessKeyId + SecretAccessKey
                                     + SessionToken (max 1h default)
                              Azure: access_token (1h)
                              GCP:   access_token (1h)
t10    Action                Imposta env vars per i passi successivi
t11    Steps successivi      Usano le credenziali temporanee
t12    Fine job              Credenziali scadono (o prima se TTL breve)
```

### Durata delle credenziali

| Provider | Default | Minimo | Massimo |
|---|---|---|---|
| AWS | 1 ora | 15 minuti | 12 ore (configurabile sul ruolo) |
| Azure | 1 ora | — | 1 ora (per federated credentials) |
| GCP | 1 ora | 10 minuti | 12 ore (con constraints) |

```yaml
# AWS — ridurre la durata per least privilege temporale
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123:role/deploy
    aws-region: eu-central-1
    role-duration-seconds: 900  # 15 minuti
```

---

## Multi-environment setups

### Pattern: un ruolo per environment

```text
┌─────────────┐      ┌──────────────────────────┐
│ Environment │      │ Cloud Role               │
│ dev         │ ───► │ github-actions-dev        │
│ staging     │ ───► │ github-actions-staging    │
│ production  │ ───► │ github-actions-production │
└─────────────┘      └──────────────────────────┘
```

### Workflow con environment matrix

```yaml
name: Deploy multi-environment
on:
  push:
    branches: [main, develop]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - environment: dev
            aws_role: arn:aws:iam::111:role/github-actions-dev
            aws_region: eu-central-1
            branch: develop
          - environment: staging
            aws_role: arn:aws:iam::222:role/github-actions-staging
            aws_region: eu-central-1
            branch: main
          - environment: production
            aws_role: arn:aws:iam::333:role/github-actions-production
            aws_region: eu-central-1
            branch: main
    environment: ${{ matrix.environment }}
    if: github.ref == format('refs/heads/{0}', matrix.branch)
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ matrix.aws_role }}
          aws-region: ${{ matrix.aws_region }}
          role-duration-seconds: 900

      - run: |
          echo "Deploying to ${{ matrix.environment }}"
          aws sts get-caller-identity
```

### Pattern: trust policy per environment

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::333:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:environment:production"
        }
      }
    }
  ]
}
```

### Cross-account deployment

```yaml
# Account A = management, Account B = workload
jobs:
  deploy-cross-account:
    runs-on: ubuntu-latest
    steps:
      # Step 1: assume role in Account A (hub)
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT_A:role/github-hub
          aws-region: eu-central-1

      # Step 2: assume role in Account B (spoke)
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT_B:role/deploy-spoke
          aws-region: eu-central-1
          role-chaining: true
```

---

## Organization-level policies

### Personalizzazione claims a livello org

```bash
# Impostare template personalizzato per tutta l'org
curl -X PUT \
  -H "Authorization: token $ORG_ADMIN_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/orgs/myorg/actions/oidc/customization/sub" \
  -d '{
    "include_claim_keys": ["repo", "context", "ref"]
  }'
```

### Policy per limitare i provider OIDC

A livello organizzazione, si può definire quali audience sono permessi:

```bash
# Listare la configurazione corrente
curl -H "Authorization: token $ORG_ADMIN_TOKEN" \
  "https://api.github.com/orgs/myorg/actions/oidc/customization/sub"
```

### Governance multi-team

| Strategia | Implementazione |
|---|---|
| **Naming convention** | Ruoli: `github-actions-{team}-{env}` |
| **Tag enforcement** | Tag obbligatori sui ruoli cloud: `team`, `repo`, `environment` |
| **Permission boundaries** | AWS: permission boundary su ogni ruolo |
| **Audit logging** | CloudTrail / Azure Activity Log filtrato per session name |
| **Centralized IaC** | Un repository Terraform per tutti i ruoli OIDC |
| **PR approval** | Modifiche ai ruoli richiedono review del security team |

### Template organizzazione per trust policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "GitHubOIDCTrust",
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AccountId}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:myorg/${RepoName}:environment:${Environment}"
        },
        "ForAnyValue:StringEquals": {
          "token.actions.githubusercontent.com:runner_environment": "github-hosted"
        }
      }
    }
  ]
}
```

---

## Security benefits e confronto con static secrets

### Matrice di confronto

| Aspetto | Static Secrets | OIDC |
|---|---|---|
| **Secret nel repo** | Sì (encrypted, ma presente) | No |
| **Rotazione** | Manuale, spesso dimenticata | Automatica (ogni token è nuovo) |
| **Blast radius** | Fino a revoca manuale | Max durata della sessione (minuti/ore) |
| **Audit** | "Qualcuno ha usato la key" | "Workflow X dal repo Y, branch Z, run N" |
| **Fork safety** | Fork possono avere accesso ai secret (se secrets ereditati) | Fork non possono generare token con il subject del repo padre |
| **Self-hosted runner risk** | Secret in memoria del runner | Token temporaneo in memoria, scade |
| **Compliance** | Richiede inventario e rotazione | Soddisfa automaticamente policy di rotazione |

### Scenari dove OIDC è mandatorio

1. **SOC 2 / ISO 27001:** audit trail per ogni accesso, nessun secret long-lived.
2. **PCI DSS:** separazione degli ambienti, credenziali non riutilizzabili.
3. **GDPR/NIS2:** tracciabilità degli accessi ai dati.
4. **Zero Trust:** mai fidarsi implicitamente, sempre verificare.

### Defense in depth con OIDC

```text
Livello 1: Trust policy → solo repo/branch/env specifici
Livello 2: Environment protection → approval richiesta
Livello 3: Permission policy → least privilege su risorse
Livello 4: Permission boundary → limite massimo per team
Livello 5: SCP / Policy org → guardrail a livello account
Livello 6: CloudTrail / audit → registrazione di ogni chiamata
```

---

## Debugging OIDC failures

### Strumenti di debug

#### 1. Decodificare il JWT nel workflow

```yaml
- name: Debug OIDC token
  run: |
    OIDC_TOKEN=$(curl -sS \
      -H "Authorization: bearer ${ACTIONS_ID_TOKEN_REQUEST_TOKEN}" \
      "${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=sts.amazonaws.com" \
      | jq -r '.value')

    echo "=== Token Header ==="
    echo "$OIDC_TOKEN" | cut -d. -f1 | base64 -d 2>/dev/null | jq .

    echo "=== Token Payload ==="
    echo "$OIDC_TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | jq .

    echo "=== Subject Claim ==="
    echo "$OIDC_TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | jq -r '.sub'

    echo "=== Audience Claim ==="
    echo "$OIDC_TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | jq -r '.aud'
```

> **Attenzione:** non loggare il token completo in produzione. Questo step è solo per debug temporaneo.

#### 2. Verificare il JWKS endpoint

```bash
curl -s https://token.actions.githubusercontent.com/.well-known/openid-configuration | jq .
curl -s https://token.actions.githubusercontent.com/.well-known/jwks | jq .
```

#### 3. Testare la trust policy con AWS CLI

```bash
# Simulare il token exchange localmente (con un token valido)
aws sts assume-role-with-web-identity \
  --role-arn "arn:aws:iam::123:role/github-actions-deploy" \
  --role-session-name "test-session" \
  --web-identity-token "$OIDC_TOKEN"
```

#### 4. CloudTrail per AWS

```bash
# Cercare eventi AssumeRoleWithWebIdentity
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRoleWithWebIdentity \
  --max-results 10 \
  | jq '.Events[].CloudTrailEvent | fromjson | {
    eventTime,
    sourceIPAddress,
    errorCode,
    errorMessage,
    requestParameters: .requestParameters
  }'
```

### Errori comuni e diagnosi

| Errore | Causa probabile | Fix |
|---|---|---|
| `Not authorized to perform sts:AssumeRoleWithWebIdentity` | Trust policy non matcha il subject | Verificare `sub` claim vs condition |
| `Token is expired` | Clock skew o token richiesto troppo presto | Retry, verificare timing |
| `Invalid identity token` | Audience sbagliata | Verificare `aud` nella trust policy |
| `Could not retrieve credentials` | Permesso `id-token: write` mancante | Aggiungere la permission |
| `AccessDenied: Not authorized` | Permission policy insufficiente | Aggiungere le azioni necessarie |

---

## Pattern avanzati

### Reusable workflow con OIDC

```yaml
# .github/workflows/reusable-deploy.yml
name: Reusable OIDC Deploy
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      aws-role:
        required: true
        type: string
      aws-region:
        required: true
        type: string
        default: eu-central-1

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ inputs.aws-role }}
          aws-region: ${{ inputs.aws-region }}
          role-duration-seconds: 900

      - run: |
          echo "Deploying to ${{ inputs.environment }}"
          ./scripts/deploy.sh
```

```yaml
# .github/workflows/deploy-production.yml
name: Deploy Production
on:
  push:
    branches: [main]

jobs:
  deploy:
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: production
      aws-role: arn:aws:iam::333:role/github-actions-production
      aws-region: eu-central-1
```

### Multi-cloud deployment

```yaml
name: Multi-cloud deploy
on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy-aws:
    runs-on: ubuntu-latest
    environment: aws-production
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123:role/deploy
          aws-region: eu-central-1
      - run: ./scripts/deploy-aws.sh

  deploy-gcp:
    runs-on: ubuntu-latest
    environment: gcp-production
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: projects/123/locations/global/workloadIdentityPools/pool/providers/ghprovider
          service_account: deploy@project.iam.gserviceaccount.com
      - run: ./scripts/deploy-gcp.sh

  deploy-azure:
    runs-on: ubuntu-latest
    environment: azure-production
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - run: ./scripts/deploy-azure.sh
```

### OIDC per provider custom

```yaml
# Vault HashiCorp via OIDC
- name: Authenticate to Vault
  run: |
    OIDC_TOKEN=$(curl -sS \
      -H "Authorization: bearer ${ACTIONS_ID_TOKEN_REQUEST_TOKEN}" \
      "${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=vault.mycompany.com" \
      | jq -r '.value')

    VAULT_TOKEN=$(curl -sS \
      --request POST \
      --data "{\"role\":\"github-actions\",\"jwt\":\"${OIDC_TOKEN}\"}" \
      "https://vault.mycompany.com/v1/auth/jwt/login" \
      | jq -r '.auth.client_token')

    echo "VAULT_TOKEN=$VAULT_TOKEN" >> "$GITHUB_ENV"
    echo "::add-mask::$VAULT_TOKEN"
```

---

## Esercizi

### Lab 1 — OIDC AWS S3 deploy

1. Crea un OIDC Identity Provider nel tuo account AWS.
2. Crea un IAM Role con trust policy vincolata al tuo repository + branch main.
3. Crea un workflow che fa deploy di un file statico su S3.
4. Verifica con `aws sts get-caller-identity` che le credenziali siano temporanee.
5. Prova a triggerare il workflow da un branch diverso da main → deve fallire.

### Lab 2 — OIDC Azure App Service

1. Registra un'applicazione Azure AD con federated credential.
2. Assegna Contributor sul resource group.
3. Crea un workflow che fa deploy su un Azure App Service.
4. Verifica con `az account show`.

### Lab 3 — Multi-environment AWS

1. Crea tre ruoli AWS: `dev`, `staging`, `production`.
2. Ciascuno con trust policy per il rispettivo GitHub environment.
3. Crea un workflow con matrix che deploya all'environment corretto.
4. Proteggi l'environment `production` con required reviewers.

### Lab 4 — GCP Cloud Run deploy

1. Configura Workload Identity Federation su GCP.
2. Crea il service account con solo i permessi necessari per Cloud Run.
3. Crea un workflow che builda un container e lo deploya su Cloud Run.
4. Verifica che l'attribute condition limiti l'accesso al solo repository.

### Lab 5 — Debug OIDC failure

1. Crea intenzionalmente una trust policy con subject sbagliato.
2. Analizza l'errore nel log del workflow.
3. Decodifica il JWT per confrontare il subject reale con quello atteso.
4. Correggi la trust policy e verifica il successo.

### Stretch — OIDC per HashiCorp Vault

1. Configura Vault JWT auth method per GitHub OIDC.
2. Crea una policy Vault per leggere un secret path.
3. Crea un workflow che autentica via OIDC e legge un secret da Vault.

---

## Troubleshooting — 20 problemi comuni

### 1. `Error: Not authorized to perform sts:AssumeRoleWithWebIdentity`

**Causa:** la trust policy IAM non matcha i claims del JWT.

**Soluzione:**
```bash
# Decodifica il JWT e confronta il subject con la trust policy
echo "$TOKEN" | cut -d. -f2 | base64 -d | jq -r '.sub'
# Output: repo:myorg/myrepo:environment:production

# La trust policy deve avere esattamente lo stesso valore
# o usare StringLike con wildcard
```

### 2. `Error: Could not retrieve credentials from the instance metadata service`

**Causa:** `permissions.id-token: write` non dichiarato nel workflow.

**Soluzione:**
```yaml
permissions:
  id-token: write    # ← OBBLIGATORIO
  contents: read
```

### 3. `Error: Audience in token does not match`

**Causa:** l'audience nel JWT non corrisponde a quello configurato nel provider cloud.

**Soluzione:**
```yaml
# AWS: deve essere sts.amazonaws.com (default nell'action)
# Azure: deve essere api://AzureADTokenExchange
# GCP: deve essere l'URL completo del provider
```

### 4. `Error: Token expired`

**Causa:** il JWT GitHub ha una vita molto breve (~5 min). Se il workflow ha step lunghi prima dell'auth, il token potrebbe scadere.

**Soluzione:** posizionare lo step di autenticazione il più presto possibile nel job.

### 5. `Error: OIDC provider not found`

**Causa:** il provider OIDC non è stato creato nell'account cloud.

**Soluzione:**
```bash
# AWS: verificare che il provider esista
aws iam list-open-id-connect-providers
```

### 6. Fork del repository non riesce ad autenticarsi

**Causa:** i fork non possono generare token con il subject del repo originale. Questo è **by design** — è una protezione di sicurezza.

**Soluzione:** nessuna. I fork non devono poter assumere ruoli del repository originale.

### 7. Pull request workflow fallisce l'autenticazione

**Causa:** il subject per le PR è `repo:org/repo:pull_request`, diverso da `repo:org/repo:ref:refs/heads/main`.

**Soluzione:**
```json
// Aggiungere una condition separata per PR
"StringEquals": {
  "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:pull_request"
}
```

### 8. `Error: Session duration exceeds maximum`

**Causa:** `role-duration-seconds` supera il `MaxSessionDuration` del ruolo IAM.

**Soluzione:**
```bash
# Verificare il MaxSessionDuration del ruolo
aws iam get-role --role-name github-actions-deploy \
  | jq '.Role.MaxSessionDuration'

# Aumentare se necessario (max 43200 = 12h)
aws iam update-role --role-name github-actions-deploy \
  --max-session-duration 3600
```

### 9. Workflow funziona da main ma non da tag

**Causa:** il subject per i tag è `repo:org/repo:ref:refs/tags/v1.0`, non `refs/heads/main`.

**Soluzione:**
```json
"StringLike": {
  "token.actions.githubusercontent.com:sub": [
    "repo:myorg/myrepo:ref:refs/heads/main",
    "repo:myorg/myrepo:ref:refs/tags/v*"
  ]
}
```

### 10. Azure: `AADSTS70021: No matching federated identity record found`

**Causa:** il subject nella federated credential non corrisponde al JWT.

**Soluzione:** verificare se il workflow usa un environment (che cambia il subject) e aggiungere la federated credential corrispondente.

### 11. GCP: `The caller does not have permission`

**Causa:** il service account non ha il binding `roles/iam.workloadIdentityUser` per il pool.

**Soluzione:**
```bash
gcloud iam service-accounts add-iam-policy-binding \
  "sa@project.iam.gserviceaccount.com" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/POOL/attribute.repository/org/repo"
```

### 12. GCP: `Permission iam.serviceAccounts.getAccessToken denied`

**Causa:** l'attribute condition del provider filtra il token.

**Soluzione:** verificare che `attribute-condition` matchi i claims del JWT. Controllare `assertion.repository_owner`, `assertion.repository`, ecc.

### 13. Reusable workflow non riceve il token OIDC

**Causa:** `permissions.id-token: write` deve essere dichiarato sia nel caller che nel reusable workflow.

**Soluzione:**
```yaml
# Nel caller workflow
permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    uses: ./.github/workflows/reusable.yml
    permissions:
      id-token: write
      contents: read
```

### 14. `Error: Process completed with exit code 1` senza dettagli

**Causa:** errore generico. Spesso legato a permessi mancanti o variabili non impostate.

**Soluzione:** aggiungere step di debug prima dell'auth:
```yaml
- name: Debug env
  run: |
    echo "ACTIONS_ID_TOKEN_REQUEST_URL is set: ${{ env.ACTIONS_ID_TOKEN_REQUEST_URL != '' }}"
    echo "GitHub ref: ${{ github.ref }}"
    echo "GitHub event: ${{ github.event_name }}"
```

### 15. Multipli ruoli nello stesso job

**Causa:** il secondo `configure-aws-credentials` sovrascrive il primo.

**Soluzione:** usare `role-chaining: true` o separare in job diversi.

### 16. Self-hosted runner non funziona con OIDC

**Causa:** il runner deve poter raggiungere `token.actions.githubusercontent.com` e il STS del cloud provider.

**Soluzione:** verificare firewall/proxy per consentire:
- `token.actions.githubusercontent.com` (porta 443)
- `sts.amazonaws.com` / `login.microsoftonline.com` / `sts.googleapis.com`

### 17. `Error: AADSTS700024: Client assertion is not within its valid time range`

**Causa:** clock skew tra GitHub e Azure AD.

**Soluzione:** normalmente transitorio. Retry il workflow. Se persistente, verificare che il runner non abbia l'orologio sfasato.

### 18. Terraform plan funziona ma apply no

**Causa:** `role-duration-seconds` troppo breve per apply lunghi.

**Soluzione:** aumentare la durata del ruolo e del session:
```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-duration-seconds: 3600  # 1 ora per apply
```

### 19. `Error: 403 Forbidden` dopo autenticazione riuscita

**Causa:** autenticazione OIDC ok, ma la permission policy del ruolo non include l'azione richiesta.

**Soluzione:** aggiungere le azioni mancanti alla permission policy (non alla trust policy).

### 20. Token non disponibile in composite action

**Causa:** le composite action non ricevono automaticamente le variabili OIDC.

**Soluzione:** passare il token come input o usare una JavaScript action che chiama `core.getIDToken()`.

---

## FAQ — 20 domande e risposte

### 1. Posso usare OIDC con repository privati?

Sì. OIDC funziona identicamente per repository pubblici e privati. La visibilità del repository è inclusa come claim `repository_visibility` nel JWT.

### 2. OIDC funziona con i fork?

I fork **non** possono generare token OIDC con il subject del repository padre. Questo è intenzionale: impedisce a un fork malevolo di assumere i ruoli del repo originale.

### 3. Quanto dura il JWT emesso da GitHub?

Circa 5 minuti. È progettato per essere scambiato immediatamente con credenziali cloud, non per essere conservato.

### 4. Cosa succede se il cloud provider è irraggiungibile?

Il workflow fallisce allo step di autenticazione. Si può aggiungere retry logic:
```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123:role/deploy
    aws-region: eu-central-1
    retry-max-attempts: 3
```

### 5. Posso usare OIDC con più cloud provider nello stesso workflow?

Sì. Ogni job (o step) può autenticarsi verso un provider diverso. L'audience viene specificato separatamente per ogni richiesta di token.

### 6. OIDC sostituisce completamente i GitHub Secrets?

Per le credenziali cloud, sì. Per altri secret (API key di terze parti, token npm, ecc.), i GitHub Secrets restano necessari.

### 7. Come faccio audit di chi ha usato OIDC?

- **AWS:** CloudTrail → eventi `AssumeRoleWithWebIdentity`, session name contiene il run ID.
- **Azure:** Azure AD sign-in logs → service principal.
- **GCP:** Cloud Audit Logs → `SetIamPolicy` e access logs.

### 8. Posso limitare OIDC a specifici workflow file?

Sì, usando il claim `job_workflow_ref`:
```json
"StringEquals": {
  "token.actions.githubusercontent.com:job_workflow_ref": "myorg/myrepo/.github/workflows/deploy.yml@refs/heads/main"
}
```

### 9. OIDC funziona con GitHub Enterprise Server (GHES)?

Sì, da GHES 3.5+. L'issuer sarà `https://YOUR_GHES_HOSTNAME/_services/token`.

### 10. Come gestisco la migrazione da static secrets a OIDC?

1. Configura il provider OIDC nel cloud.
2. Crea il ruolo con trust policy.
3. Modifica il workflow per usare OIDC.
4. Testa su un branch non-production.
5. Fai merge e verifica.
6. Rimuovi i secret statici da GitHub.
7. Revoca le credenziali statiche nel cloud provider.

### 11. OIDC ha un costo aggiuntivo?

No. OIDC è gratuito sia su GitHub che sui cloud provider. Non ci sono costi per la federazione dell'identità.

### 12. Cosa succede durante un outage di GitHub OIDC?

Il cloud provider non può verificare i token → i workflow falliscono. È lo stesso rischio di qualsiasi dipendenza da GitHub Actions. Monitorare [githubstatus.com](https://www.githubstatus.com/).

### 13. Posso usare OIDC con Dependabot?

No (al momento). Dependabot non supporta `permissions.id-token: write`. Usare i Dependabot Secrets per le credenziali cloud.

### 14. Come faccio il rollback se OIDC smette di funzionare?

Mantenere i secret statici come backup (disabilitati) per i primi 30 giorni dopo la migrazione. Se OIDC fallisce, riattivare temporaneamente i secret e investigare.

### 15. OIDC funziona con act (test locale di Actions)?

`act` non supporta nativamente OIDC perché non ha accesso all'OIDC provider di GitHub. Per test locali, usare credenziali locali o mock.

### 16. Quanti ruoli/federated credentials posso creare?

- **AWS:** nessun limite pratico su OIDC provider; limite ruoli per account ~1000 (soft limit).
- **Azure:** max 20 federated credentials per app registration.
- **GCP:** max 200 provider per pool, 200 pool per progetto.

### 17. Posso condividere lo stesso ruolo tra più repository?

Sì, usando `StringLike` con wildcard:
```json
"StringLike": {
  "token.actions.githubusercontent.com:sub": "repo:myorg/*:ref:refs/heads/main"
}
```
Ma è **sconsigliato** per production: violare il least privilege. Creare un ruolo per repository.

### 18. Come integro OIDC con Terraform Cloud/Enterprise?

Terraform Cloud supporta OIDC nativo. Configurare il workspace con "Dynamic Provider Credentials" e collegare il cloud provider.

### 19. Il session name è personalizzabile?

Sì, per AWS:
```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-session-name: deploy-${{ github.actor }}-${{ github.run_id }}
```

### 20. Come proteggo i workflow che usano OIDC da modifiche non autorizzate?

1. **Branch protection:** richiedi review per modifiche a `.github/workflows/`.
2. **CODEOWNERS:** assegna il security team come owner di `/.github/`.
3. **Environment protection:** required reviewers per `production`.
4. **Trust policy:** vincola a `workflow_ref` specifico.

---

## Configurare HashiCorp Vault — JWT Auth con GitHub OIDC

HashiCorp Vault supporta nativamente l'autenticazione via JWT/OIDC, rendendolo un componente naturale nelle pipeline CI/CD che usano GitHub Actions OIDC. Vault può verificare i token JWT emessi da GitHub e concedere token Vault temporanei con policy granulari.

### Architettura del flusso Vault + GitHub OIDC

```text
┌──────────────────┐     1. Richiede JWT        ┌──────────────────────────────┐
│  GitHub Actions  │ ──────────────────────────► │  GitHub OIDC Provider        │
│  Workflow        │ ◄────────────────────────── │  token.actions.github...com  │
│                  │     2. JWT firmato           └──────────────────────────────┘
│                  │
│                  │     3. POST /auth/jwt/login  ┌──────────────────────────────┐
│                  │ ──────────────────────────► │  HashiCorp Vault             │
│                  │ ◄────────────────────────── │  JWT Auth Method             │
│                  │     4. Vault token temp.     │                              │
│                  │                              │  5. Vault verifica firma JWT │
│                  │     6. GET /secret/data/...  │     via JWKS di GitHub       │
│                  │ ──────────────────────────► │                              │
│                  │ ◄────────────────────────── │  7. Restituisce secret       │
└──────────────────┘                              └──────────────────────────────┘
```

### Passo 1 — Abilitare JWT auth in Vault

```bash
# Abilitare il metodo di autenticazione JWT
vault auth enable jwt

# Configurare GitHub come OIDC provider
vault write auth/jwt/config \
  bound_issuer="https://token.actions.githubusercontent.com" \
  oidc_discovery_url="https://token.actions.githubusercontent.com"
```

Il parametro `oidc_discovery_url` permette a Vault di scaricare automaticamente le chiavi pubbliche JWKS da GitHub per la verifica delle firme dei token.

### Passo 2 — Creare una policy Vault

```hcl
# policy-github-deploy.hcl
# Policy per leggere secret di deploy
path "secret/data/deploy/*" {
  capabilities = ["read", "list"]
}

path "secret/data/shared/certificates" {
  capabilities = ["read"]
}

# Negare esplicitamente l'accesso ai secret di produzione critica
path "secret/data/production/database-root" {
  capabilities = ["deny"]
}
```

```bash
# Applicare la policy
vault policy write github-deploy policy-github-deploy.hcl
```

### Passo 3 — Creare un ruolo JWT con bound_claims

```bash
# Ruolo vincolato a un repository specifico e branch main
vault write auth/jwt/role/github-deploy \
  role_type="jwt" \
  user_claim="actor" \
  bound_claims_type="glob" \
  bound_claims='{"repository":"myorg/myrepo","ref":"refs/heads/main"}' \
  bound_audiences="https://vault.mycompany.com" \
  bound_subject="repo:myorg/myrepo:ref:refs/heads/main" \
  token_policies="github-deploy" \
  token_type="service" \
  token_ttl="10m" \
  token_max_ttl="15m" \
  token_no_default_policy=true
```

I parametri chiave del ruolo sono:

| Parametro | Significato |
|---|---|
| `bound_claims` | Claims del JWT che devono corrispondere — repository, ref, environment, ecc. |
| `bound_audiences` | L'audience atteso nel token (deve corrispondere a quello richiesto nel workflow) |
| `bound_subject` | Il subject atteso — vincolo primario di identità |
| `token_ttl` | Durata del token Vault emesso — mantenerla breve (5-15 min) |
| `token_max_ttl` | Durata massima del token Vault anche dopo rinnovo |
| `bound_claims_type` | `string` (match esatto) o `glob` (supporto wildcard) |

### Passo 4 — Ruoli per diversi ambienti

```bash
# Ruolo per ambiente staging
vault write auth/jwt/role/github-staging \
  role_type="jwt" \
  user_claim="actor" \
  bound_claims='{"repository":"myorg/myrepo","environment":"staging"}' \
  bound_audiences="https://vault.mycompany.com" \
  token_policies="github-staging" \
  token_ttl="10m" \
  token_max_ttl="15m"

# Ruolo per ambiente production — più restrittivo
vault write auth/jwt/role/github-production \
  role_type="jwt" \
  user_claim="actor" \
  bound_claims='{"repository":"myorg/myrepo","environment":"production","runner_environment":"github-hosted"}' \
  bound_audiences="https://vault.mycompany.com" \
  bound_subject="repo:myorg/myrepo:environment:production" \
  token_policies="github-production" \
  token_ttl="5m" \
  token_max_ttl="10m" \
  token_num_uses=3

# Ruolo per workflow specifico (massima granularità)
vault write auth/jwt/role/github-release \
  role_type="jwt" \
  user_claim="actor" \
  bound_claims='{"repository":"myorg/myrepo","job_workflow_ref":"myorg/myrepo/.github/workflows/release.yml@refs/heads/main"}' \
  bound_audiences="https://vault.mycompany.com" \
  token_policies="github-release" \
  token_ttl="5m" \
  token_max_ttl="10m"
```

### Passo 5 — Workflow completo con Vault

```yaml
name: Deploy with Vault secrets
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

      - name: Authenticate to Vault via OIDC
        id: vault-auth
        run: |
          # Richiedere JWT con audience personalizzato per Vault
          OIDC_TOKEN=$(curl -sS \
            -H "Authorization: bearer ${ACTIONS_ID_TOKEN_REQUEST_TOKEN}" \
            "${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=https://vault.mycompany.com" \
            | jq -r '.value')

          # Autenticarsi con Vault usando il JWT
          VAULT_RESPONSE=$(curl -sS \
            --request POST \
            --data "{\"role\":\"github-production\",\"jwt\":\"${OIDC_TOKEN}\"}" \
            "https://vault.mycompany.com/v1/auth/jwt/login")

          # Estrarre il token Vault
          VAULT_TOKEN=$(echo "$VAULT_RESPONSE" | jq -r '.auth.client_token')

          if [ "$VAULT_TOKEN" = "null" ] || [ -z "$VAULT_TOKEN" ]; then
            echo "Errore: autenticazione Vault fallita"
            echo "$VAULT_RESPONSE" | jq '.errors'
            exit 1
          fi

          echo "VAULT_TOKEN=$VAULT_TOKEN" >> "$GITHUB_ENV"
          echo "::add-mask::$VAULT_TOKEN"

      - name: Retrieve deploy secrets from Vault
        id: secrets
        run: |
          # Leggere i secret necessari per il deploy
          SECRETS=$(curl -sS \
            -H "X-Vault-Token: $VAULT_TOKEN" \
            "https://vault.mycompany.com/v1/secret/data/deploy/production")

          DB_PASSWORD=$(echo "$SECRETS" | jq -r '.data.data.db_password')
          API_KEY=$(echo "$SECRETS" | jq -r '.data.data.api_key')

          echo "::add-mask::$DB_PASSWORD"
          echo "::add-mask::$API_KEY"
          echo "DB_PASSWORD=$DB_PASSWORD" >> "$GITHUB_ENV"
          echo "API_KEY=$API_KEY" >> "$GITHUB_ENV"

      - name: Deploy
        run: ./scripts/deploy.sh

      - name: Revoke Vault token
        if: always()
        run: |
          curl -sS \
            -H "X-Vault-Token: $VAULT_TOKEN" \
            --request POST \
            "https://vault.mycompany.com/v1/auth/token/revoke-self" || true
```

### Passo 6 — Workflow con hashicorp/vault-action

```yaml
name: Deploy with vault-action
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

      - name: Import secrets from Vault
        uses: hashicorp/vault-action@v3
        with:
          url: https://vault.mycompany.com
          method: jwt
          role: github-production
          jwtGithubAudience: https://vault.mycompany.com
          exportEnv: true
          secrets: |
            secret/data/deploy/production db_password | DB_PASSWORD ;
            secret/data/deploy/production api_key | API_KEY ;
            secret/data/deploy/production deploy_token | DEPLOY_TOKEN

      - name: Deploy
        run: ./scripts/deploy.sh
```

### Terraform per Vault JWT Auth

```hcl
# vault_jwt_auth.tf
resource "vault_jwt_auth_backend" "github" {
  description        = "GitHub Actions OIDC authentication"
  path               = "jwt"
  type               = "jwt"
  oidc_discovery_url = "https://token.actions.githubusercontent.com"
  bound_issuer       = "https://token.actions.githubusercontent.com"

  default_role = ""  # Nessun ruolo default — richiede esplicito

  tune {
    max_lease_ttl     = "15m"
    default_lease_ttl = "10m"
    token_type        = "default-service"
  }
}

resource "vault_policy" "github_deploy" {
  name   = "github-deploy"
  policy = <<-EOT
    path "secret/data/deploy/*" {
      capabilities = ["read", "list"]
    }
    path "secret/data/shared/*" {
      capabilities = ["read"]
    }
  EOT
}

resource "vault_jwt_auth_backend_role" "github_production" {
  backend        = vault_jwt_auth_backend.github.path
  role_name      = "github-production"
  role_type      = "jwt"
  user_claim     = "actor"
  bound_audiences = ["https://vault.mycompany.com"]
  bound_subject  = "repo:myorg/myrepo:environment:production"

  bound_claims = {
    repository         = "myorg/myrepo"
    environment        = "production"
    runner_environment = "github-hosted"
  }

  token_policies  = [vault_policy.github_deploy.name]
  token_ttl       = 600   # 10 minuti
  token_max_ttl   = 900   # 15 minuti
  token_num_uses  = 5     # Massimo 5 utilizzi del token
}

resource "vault_jwt_auth_backend_role" "github_staging" {
  backend        = vault_jwt_auth_backend.github.path
  role_name      = "github-staging"
  role_type      = "jwt"
  user_claim     = "actor"
  bound_audiences = ["https://vault.mycompany.com"]

  bound_claims = {
    repository  = "myorg/myrepo"
    environment = "staging"
  }

  token_policies = ["github-staging"]
  token_ttl      = 600
  token_max_ttl  = 900
}
```

### Vault Namespaces per multi-tenancy

In Vault Enterprise è possibile isolare i team usando i namespace:

```bash
# Creare un namespace per il team platform
vault namespace create platform

# Configurare JWT auth dentro il namespace
VAULT_NAMESPACE=platform vault auth enable jwt
VAULT_NAMESPACE=platform vault write auth/jwt/config \
  bound_issuer="https://token.actions.githubusercontent.com" \
  oidc_discovery_url="https://token.actions.githubusercontent.com"

# Il ruolo è isolato nel namespace
VAULT_NAMESPACE=platform vault write auth/jwt/role/deploy \
  role_type="jwt" \
  bound_claims='{"repository_owner":"myorg"}' \
  bound_audiences="https://vault.mycompany.com" \
  token_policies="platform-deploy" \
  token_ttl="10m"
```

---

## Configurare Terraform Cloud / HCP Terraform — Dynamic Provider Credentials

Terraform Cloud (ora HCP Terraform) supporta le Dynamic Provider Credentials basate su OIDC per autenticarsi verso i cloud provider senza secret statici salvati nelle variabili del workspace.

### Come funzionano le Dynamic Provider Credentials

```text
┌──────────────────────┐     1. Trigger run        ┌──────────────────────────────┐
│  GitHub Actions      │ ──────────────────────────► │  HCP Terraform               │
│  (o VCS trigger)     │                              │  Workspace                   │
└──────────────────────┘                              │                              │
                                                      │  2. Genera Workload Identity │
                                                      │     Token (JWT)              │
                                                      │                              │
                                                      │  3. Presenta JWT al cloud    │
                                                      │ ──────────────────────────►  │
                                                      │                              │
                                                      │  ◄────────────────────────── │
                                                      │  4. Riceve credenziali temp. │
                                                      │                              │
                                                      │  5. Esegue plan/apply con    │
                                                      │     credenziali temporanee   │
                                                      └──────────────────────────────┘
                                                                   │
                                                                   ▼
                                                      ┌──────────────────────────────┐
                                                      │  Cloud Provider              │
                                                      │  (AWS / Azure / GCP)         │
                                                      └──────────────────────────────┘
```

### Claims nel Workload Identity Token di HCP Terraform

Il JWT emesso da HCP Terraform contiene claims specifici:

```json
{
  "iss": "https://app.terraform.io",
  "sub": "organization:myorg:project:myproject:workspace:production:run_phase:apply",
  "aud": "aws.workload.identity",
  "exp": 1716400000,
  "iat": 1716396400,
  "terraform_organization_id": "org-xxxxx",
  "terraform_organization_name": "myorg",
  "terraform_project_id": "prj-xxxxx",
  "terraform_project_name": "myproject",
  "terraform_workspace_id": "ws-xxxxx",
  "terraform_workspace_name": "production",
  "terraform_run_id": "run-xxxxx",
  "terraform_run_phase": "apply",
  "terraform_full_workspace": "organization:myorg:project:myproject:workspace:production"
}
```

### Configurare Dynamic Credentials per AWS

```hcl
# hcp_terraform_aws_oidc.tf

# 1. OIDC Provider per HCP Terraform
resource "aws_iam_openid_connect_provider" "terraform_cloud" {
  url             = "https://app.terraform.io"
  client_id_list  = ["aws.workload.identity"]
  thumbprint_list = ["9e99a48a9960b14926bb7f3b02e22da2b0ab7280"]

  tags = {
    Purpose = "HCP Terraform Dynamic Provider Credentials"
  }
}

# 2. Ruolo IAM per HCP Terraform
resource "aws_iam_role" "terraform_cloud" {
  name = "terraform-cloud-production"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.terraform_cloud.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "app.terraform.io:aud" = "aws.workload.identity"
          }
          StringLike = {
            "app.terraform.io:sub" = "organization:myorg:project:myproject:workspace:production:run_phase:*"
          }
        }
      }
    ]
  })
}

# 3. Policy per le risorse gestite da Terraform
resource "aws_iam_role_policy" "terraform_cloud" {
  name = "terraform-cloud-policy"
  role = aws_iam_role.terraform_cloud.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ec2:*", "s3:*", "rds:*", "iam:*"]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = ["eu-central-1", "eu-west-1"]
          }
        }
      }
    ]
  })
}
```

### Variabili del workspace HCP Terraform

Configurare le variabili nel workspace per abilitare le Dynamic Credentials:

| Variabile | Valore | Tipo |
|---|---|---|
| `TFC_AWS_PROVIDER_AUTH` | `true` | Environment |
| `TFC_AWS_RUN_ROLE_ARN` | `arn:aws:iam::123:role/terraform-cloud-production` | Environment |
| `TFC_AWS_WORKLOAD_IDENTITY_AUDIENCE` | `aws.workload.identity` | Environment |

### GitHub Actions + HCP Terraform con OIDC

```yaml
name: Terraform via HCP Terraform
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  terraform:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan
        if: github.event_name == 'pull_request'
        run: terraform plan -no-color -input=false
        continue-on-error: true

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: terraform apply -auto-approve -input=false
```

### Doppia federazione — GitHub OIDC per HCP Terraform + HCP Terraform OIDC per cloud

Nel modello più avanzato, sia il trigger del run sia l'accesso al cloud usano OIDC:

```text
GitHub Actions ──OIDC──► HCP Terraform ──OIDC──► AWS/Azure/GCP
     JWT #1                    JWT #2
  (identifica il              (identifica il
   workflow GHA)               workspace TFC)
```

Questo elimina completamente i secret statici dalla catena: nessun `TF_API_TOKEN` come GitHub Secret, nessuna access key nel workspace Terraform.

---

## AWS Session Tags e Principal Tags con OIDC

### Il problema dei session tags con WebIdentity

AWS supporta i session tag per le sessioni STS, ma con un vincolo importante per OIDC: quando si usa `AssumeRoleWithWebIdentity`, i session tag possono essere forniti **solo dall'OIDC provider** nel token JWT, non possono essere impostati come parametri della chiamata API.

GitHub OIDC non include session tag nativamente nel JWT. Questo crea una limitazione quando si vogliono usare condizioni basate su `aws:PrincipalTag` nelle policy IAM.

### Workaround con AWS Cognito Identity Pools

AWS Cognito Identity Pools permette di mappare i claims del JWT GitHub in session tag utilizzabili nelle policy IAM:

```text
┌──────────────────┐     JWT GitHub        ┌──────────────────────────────┐
│  GitHub Actions  │ ────────────────────► │  AWS Cognito Identity Pool   │
│                  │ ◄──────────────────── │  (mappatura claims → tags)   │
│                  │     JWT con tags       └──────────────────────────────┘
│                  │
│                  │     JWT Cognito        ┌──────────────────────────────┐
│                  │ ────────────────────► │  AWS STS                     │
│                  │ ◄──────────────────── │  AssumeRoleWithWebIdentity   │
│                  │     Credenziali temp.  └──────────────────────────────┘
│                  │     con session tags
└──────────────────┘
```

### Configurare Cognito per session tags

```bash
# 1. Creare un Identity Pool
IDENTITY_POOL_ID=$(aws cognito-identity create-identity-pool \
  --identity-pool-name "github-actions-pool" \
  --allow-unauthenticated-identities false \
  --open-id-connect-provider-arns \
    "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com" \
  --query "IdentityPoolId" --output text)

# 2. Configurare il mapping dei claims
aws cognito-identity set-principal-tag-attribute-map \
  --identity-pool-id "$IDENTITY_POOL_ID" \
  --identity-provider-name "token.actions.githubusercontent.com" \
  --use-defaults false \
  --principal-tags '{
    "repository": "repository",
    "repository_owner": "repository_owner",
    "actor": "actor",
    "environment": "environment",
    "ref": "ref"
  }'
```

### Policy IAM con Principal Tags

Con i session tag disponibili tramite Cognito, è possibile scrivere policy IAM basate su attributi (ABAC):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::deploy-*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalTag/repository_owner": "myorg",
          "aws:PrincipalTag/environment": "production"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": "ecr:*",
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "aws:PrincipalTag/repository": "myorg/*"
        }
      }
    }
  ]
}
```

### Vantaggi di ABAC con OIDC

| Aspetto | Trust policy tradizionale | ABAC con session tags |
|---|---|---|
| **Granularità** | Vincolo sul subject | Vincolo su qualsiasi attributo del token |
| **Scalabilità** | Un ruolo per combinazione repo/env | Un ruolo per molti repo con policy basata su tag |
| **Manutenzione** | Aggiornare trust policy per ogni nuovo repo | La policy resta invariata, i tag vengono dal token |
| **Audit** | Session name contiene info limitate | I tag sono visibili in CloudTrail |

### Trust policy con sts:TagSession

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "cognito-identity.amazonaws.com"
      },
      "Action": [
        "sts:AssumeRoleWithWebIdentity",
        "sts:TagSession"
      ],
      "Condition": {
        "StringEquals": {
          "cognito-identity.amazonaws.com:aud": "${IDENTITY_POOL_ID}"
        }
      }
    }
  ]
}
```

---

## Azure Flexible Federated Identity Credentials

### Limiti delle federated credentials tradizionali

Le federated identity credentials standard in Azure/Entra ID richiedono un **match esatto** per il campo subject. Questo comporta limitazioni operative:

- Servono credenziali separate per ogni combinazione di branch, tag, environment.
- Massimo 20 federated credentials per app registration.
- Non è possibile usare wildcard o pattern matching.

### Cosa sono le Flexible Federated Identity Credentials

Introdotte in preview a marzo 2025, le Flexible Federated Identity Credentials aggiungono un linguaggio di espressioni che supporta wildcard e operatori booleani per il matching dei claims del token.

### Sintassi delle espressioni

Le espressioni sono composte da tre parti: lookup del claim, operatore e comparando.

```text
# Sintassi base
claims['<claim_name>'] <operatore> '<valore>'

# Operatori disponibili
claims['sub'] eq 'valore-esatto'                    # match esatto
claims['sub'] matches 'repo:contoso/*:ref:refs/heads/*'  # wildcard
claims['sub'] startsWith 'repo:contoso/'             # prefisso

# Operatori booleani
claims['sub'] matches 'repo:contoso/*' && claims['ref'] eq 'refs/heads/main'
claims['sub'] matches 'repo:contoso/*' || claims['sub'] matches 'repo:fabrikam/*'
```

### Esempi pratici

```text
# Qualsiasi branch di un repository specifico
claims['sub'] matches 'repo:myorg/myrepo:ref:refs/heads/*'

# Qualsiasi repository dell'organizzazione, solo branch main
claims['sub'] matches 'repo:myorg/*:ref:refs/heads/main'

# Ambiente production di qualsiasi repository
claims['sub'] matches 'repo:myorg/*:environment:production'

# Tag di release (v1.*, v2.*, ecc.)
claims['sub'] matches 'repo:myorg/myrepo:ref:refs/tags/v*'

# Combinazione: repository specifico + branch main O environment production
(claims['sub'] eq 'repo:myorg/myrepo:ref:refs/heads/main') || (claims['sub'] eq 'repo:myorg/myrepo:environment:production')

# Vincolo su workflow specifico + repository
claims['repository'] eq 'myorg/myrepo' && claims['job_workflow_ref'] matches 'myorg/myrepo/.github/workflows/deploy.yml@*'
```

### Creare Flexible Federated Credentials via Microsoft Graph

Al momento (2026), le flexible federated identity credentials possono essere create solo tramite Microsoft Graph API o il portale Azure — non sono ancora supportate in Azure CLI, Azure PowerShell o nel provider Terraform per Azure.

```bash
# Creare una flexible federated credential via Microsoft Graph
APP_OBJECT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

curl -X POST \
  -H "Authorization: Bearer $GRAPH_TOKEN" \
  -H "Content-Type: application/json" \
  "https://graph.microsoft.com/beta/applications/${APP_OBJECT_ID}/federatedIdentityCredentials" \
  -d '{
    "name": "github-flexible-production",
    "issuer": "https://token.actions.githubusercontent.com",
    "audiences": ["api://AzureADTokenExchange"],
    "claimsMatchingExpression": {
      "value": "claims['\''sub'\''] matches '\''repo:myorg/*:environment:production'\''",
      "languageVersion": 1
    }
  }'
```

### Confronto: tradizionale vs flexible

| Aspetto | Tradizionale | Flexible |
|---|---|---|
| **Matching** | Solo match esatto su subject | Wildcard, prefisso, operatori booleani |
| **Claim utilizzabili** | Solo subject, issuer, audience | Qualsiasi claim del token |
| **Limite per app** | 20 credential | 20 credential (ma ogni una copre più scenari) |
| **Manutenzione** | Alta — una credential per ogni combinazione | Bassa — pattern matching riduce il numero |
| **Disponibilità** | GA | Preview (2025-2026) |
| **Strumenti** | CLI, PowerShell, Terraform, Graph | Solo Graph API e portale Azure |

### Impatto pratico

Con le flexible federated credentials, un'organizzazione con 50 repository che necessita di deploy a production può passare da **50 federated credentials separate** (che superano il limite di 20 per app) a **una singola credential** con espressione:

```text
claims['sub'] matches 'repo:myorg/*:environment:production'
```

---

## Repository Custom Properties nei token OIDC

### Funzionalità introdotta a marzo 2026

GitHub ha annunciato a marzo 2026 la possibilità di includere **repository custom properties** come claims nei token OIDC. Questa funzionalità abilita l'Attribute-Based Access Control (ABAC) basato su metadati personalizzati del repository.

### Come funziona

1. **Definire custom properties** a livello di organizzazione o enterprise (es. `business_unit`, `data_classification`, `environment_tier`).
2. **Assegnare valori** ai repository.
3. **Abilitare le proprietà** per l'inclusione nei token OIDC (via UI settings o REST API).
4. Ogni workflow run include i valori delle proprietà abilitate nel JWT, con prefisso `repo_property_`.

### Configurazione via REST API

```bash
# 1. Creare custom properties per l'organizzazione
curl -X PATCH \
  -H "Authorization: token $ORG_ADMIN_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/orgs/myorg/properties/schema" \
  -d '{
    "properties": [
      {
        "property_name": "business_unit",
        "value_type": "single_select",
        "required": true,
        "allowed_values": ["platform", "frontend", "backend", "data", "security"]
      },
      {
        "property_name": "data_classification",
        "value_type": "single_select",
        "required": true,
        "allowed_values": ["public", "internal", "confidential", "restricted"]
      },
      {
        "property_name": "environment_tier",
        "value_type": "single_select",
        "required": false,
        "allowed_values": ["tier1-critical", "tier2-standard", "tier3-experimental"]
      }
    ]
  }'

# 2. Assegnare valori a un repository
curl -X PATCH \
  -H "Authorization: token $ORG_ADMIN_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/orgs/myorg/properties/values" \
  -d '{
    "repository_names": ["payment-service"],
    "properties": [
      {"property_name": "business_unit", "value": "platform"},
      {"property_name": "data_classification", "value": "restricted"},
      {"property_name": "environment_tier", "value": "tier1-critical"}
    ]
  }'

# 3. Abilitare le proprietà nei token OIDC
curl -X PUT \
  -H "Authorization: token $ORG_ADMIN_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/orgs/myorg/actions/oidc/customization/sub" \
  -d '{
    "include_claim_keys": ["repo", "context", "ref"],
    "include_repo_custom_properties": ["business_unit", "data_classification"]
  }'
```

### Claims risultanti nel JWT

Dopo la configurazione, il JWT includerà claims aggiuntivi:

```json
{
  "sub": "repo:myorg/payment-service:environment:production:ref:refs/heads/main",
  "repo_property_business_unit": "platform",
  "repo_property_data_classification": "restricted",
  "repo_property_environment_tier": "tier1-critical",
  "repository": "myorg/payment-service",
  "environment": "production"
}
```

### Uso nelle trust policy AWS

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:repo_property_data_classification": "restricted"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:myorg/*:environment:production:*"
        }
      }
    }
  ]
}
```

### Uso nelle attribute conditions GCP

```bash
gcloud iam workload-identity-pools providers update-oidc "github-provider" \
  --project="my-project" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --attribute-condition="assertion.repository_owner == 'myorg' && assertion.repo_property_data_classification == 'restricted'"
```

### Casi d'uso per custom properties OIDC

| Caso d'uso | Custom property | Effetto |
|---|---|---|
| **Segregazione per business unit** | `business_unit` | Ogni team accede solo ai propri account cloud |
| **Classificazione dati** | `data_classification` | Solo repo con dati `restricted` accedono a risorse PCI |
| **Tier di servizio** | `environment_tier` | Ruoli diversi per servizi critici vs sperimentali |
| **Compliance** | `compliance_standard` | Solo repo conformi a SOC2 accedono a certi ambienti |
| **Cost center** | `cost_center` | Tracking dei costi per team/progetto |

---

## Security hardening avanzato — Checklist operativa

### Checklist pre-deploy OIDC

Prima di mettere in produzione una configurazione OIDC, verificare ogni punto:

#### Trust policy / federated credentials

- [ ] La trust policy usa `StringEquals` (non `StringLike`) per il subject dove possibile
- [ ] L'audience è esplicitamente vincolato (non wildcard)
- [ ] Il vincolo include `repository` o `sub` — mai solo `repository_owner`
- [ ] Per i deploy di produzione, il vincolo include `environment:production`
- [ ] Se si usa `StringLike`, il pattern è il più restrittivo possibile
- [ ] La trust policy vincola anche `runner_environment` a `github-hosted` quando si usano solo runner hosted
- [ ] Il vincolo `workflow_ref` o `job_workflow_ref` è presente per workflow critici
- [ ] Nessun wildcard `*` senza prefisso (es. `repo:*` — **MAI**)

#### Permessi del ruolo cloud

- [ ] La permission policy segue il principio di least privilege
- [ ] Le risorse sono specificate con ARN esatti, non `*`
- [ ] Le region sono limitate a quelle effettivamente necessarie
- [ ] È presente un permission boundary per limitare l'escalation
- [ ] La durata massima della sessione è impostata al minimo necessario
- [ ] Per AWS: nessuna azione `iam:*` a meno che strettamente necessaria
- [ ] Per Azure: RBAC scope limitato al resource group, non alla subscription
- [ ] Per GCP: ruoli predefiniti (non `Owner` o `Editor`)

#### Workflow

- [ ] `permissions.id-token: write` è dichiarato esplicitamente
- [ ] `permissions.contents: read` è dichiarato (non `write` se non necessario)
- [ ] Le azioni usano commit SHA pinned, non tag floating
- [ ] L'environment GitHub è configurato con protection rules
- [ ] Lo step di autenticazione è il più vicino possibile all'inizio del job
- [ ] Il `role-session-name` include informazioni identificative (run_id, actor)
- [ ] La durata della sessione (`role-duration-seconds`) è minimizzata
- [ ] Nessun token viene loggato (nemmeno parzialmente) in produzione

#### Organizzazione

- [ ] I subject claims sono personalizzati a livello organizzazione
- [ ] CODEOWNERS protegge le modifiche ai workflow in `.github/`
- [ ] Branch protection richiede review per merge su branch protetti
- [ ] L'audit log dell'organizzazione è monitorato per eventi OIDC
- [ ] Esiste documentazione su quali repository hanno accesso a quali ruoli cloud
- [ ] I ruoli OIDC sono gestiti via IaC (Terraform/Pulumi), non manualmente

### Hardening del claim `workflow_ref`

Il claim `workflow_ref` è uno dei più potenti per la sicurezza. Identifica il **file workflow specifico** (includendo il percorso e il commit ref) che ha richiesto il token.

```json
// Trust policy AWS vincolata a workflow specifico
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:job_workflow_ref": "myorg/myrepo/.github/workflows/deploy.yml@refs/heads/main"
    }
  }
}
```

Questo impedisce che **qualsiasi altro workflow** nello stesso repository possa assumere il ruolo — anche se il repository e il branch sono corretti. Un attaccante che riesce a creare un nuovo file workflow in `.github/workflows/` non potrà usarlo per assumere il ruolo.

### Hardening del claim `runner_environment`

Il claim `runner_environment` distingue tra runner GitHub-hosted e self-hosted:

| Valore | Significato |
|---|---|
| `github-hosted` | Runner gestito da GitHub (ambiente controllato) |
| `self-hosted` | Runner gestito dall'utente (ambiente potenzialmente meno sicuro) |

```json
// Solo runner GitHub-hosted possono assumere il ruolo
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:runner_environment": "github-hosted"
    }
  }
}
```

Questo è particolarmente importante se l'organizzazione ha self-hosted runner condivisi tra team con diversi livelli di trust.

### Hardening con `repository_visibility`

```json
// Solo repository privati possono assumere ruoli di produzione
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:repository_visibility": "private"
    }
  }
}
```

---

## Vettori di attacco e mitigazioni

### Tassonomia delle minacce OIDC

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    MINACCE ALL'ECOSISTEMA OIDC                         │
├─────────────────────────┬───────────────────────────────────────────────┤
│  SUPPLY CHAIN           │  CONFIGURAZIONE                              │
│  • Action malevola      │  • Trust policy troppo permissiva            │
│  • Tag mutabile         │  • Wildcard su subject                       │
│  • Fork poisoning       │  • Permission policy eccessiva               │
│  • Dependency injection │  • Audience non vincolato                    │
├─────────────────────────┼───────────────────────────────────────────────┤
│  WORKFLOW MANIPULATION  │  INFRASTRUTTURA                              │
│  • pwn request          │  • Self-hosted runner compromesso            │
│  • Script injection     │  • Network intercept (MITM)                  │
│  • Workflow dispatch    │  • Cloud provider misconfiguration           │
│  • Reusable workflow    │  • DNS hijacking dell'OIDC endpoint          │
│    abuse                │                                              │
└─────────────────────────┴───────────────────────────────────────────────┘
```

### Attacco 1 — Supply chain via action malevola

**Scenario:** un attaccante compromette un'action di terze parti (come avvenuto con tj-actions/changed-files nel marzo 2025). L'action modificata legge le variabili d'ambiente OIDC e richiede un token JWT al posto del workflow legittimo.

**Impatto:** l'action malevola può ottenere un JWT valido e usarlo per assumere ruoli cloud se la trust policy è troppo permissiva.

**Mitigazione:**

```yaml
# SBAGLIATO: tag floating (vulnerabile a tag poisoning)
- uses: some-action/deploy@v3

# CORRETTO: commit SHA pinned (immutabile)
- uses: some-action/deploy@a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2

# CORRETTO: con commento per leggibilità
- uses: some-action/deploy@a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2 # v3.2.1
```

Combinare con trust policy granulare:

```json
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:job_workflow_ref": "myorg/myrepo/.github/workflows/deploy.yml@refs/heads/main"
    }
  }
}
```

### Attacco 2 — Trust policy troppo permissiva

**Scenario:** la trust policy usa `StringLike` con wildcard troppo ampie.

```json
// PERICOLOSO: qualsiasi repository dell'org può assumere il ruolo
"StringLike": {
  "token.actions.githubusercontent.com:sub": "repo:myorg/*"
}
```

Se un qualsiasi repository dell'organizzazione è compromesso (anche un repo test dimenticato), l'attaccante può assumere il ruolo.

**Mitigazione:** vincolare a repository e branch specifici:

```json
// SICURO: solo il repo specifico, solo branch main
"StringEquals": {
  "token.actions.githubusercontent.com:sub": "repo:myorg/production-deploy:ref:refs/heads/main"
}
```

### Attacco 3 — pwn request con OIDC

**Scenario:** un workflow `pull_request_target` processa il codice del PR (potenzialmente malevolo) e ha `permissions.id-token: write`. Il codice iniettato nel PR può richiedere un JWT.

**Mitigazione:**

```yaml
# MAI concedere id-token: write a workflow pull_request_target
# che eseguono codice dal PR
on:
  pull_request_target:

permissions:
  contents: read
  # id-token: NON PRESENTE — il workflow non può richiedere JWT
```

Se è necessario OIDC per le PR, usare un ambiente con protezioni:

```yaml
on:
  pull_request:

permissions:
  id-token: write
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    environment: pr-test  # Environment con permessi limitati
    steps:
      # L'environment pr-test ha un ruolo cloud con permessi minimi
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123:role/github-pr-readonly
          aws-region: eu-central-1
```

### Attacco 4 — Token replay

**Scenario:** un attaccante intercetta il JWT GitHub (es. da un log accidentale) e tenta di usarlo per ottenere credenziali cloud.

**Mitigazione:** il JWT di GitHub ha una scadenza molto breve (~5 minuti) e include un `jti` (JWT ID) unico. Tuttavia, per mitigare ulteriormente:

1. **Non loggare mai il token**, nemmeno in debug temporanei che vanno in produzione.
2. **Usare audience specifici** per impedire che un token destinato a un provider venga usato con un altro.
3. **Ridurre la durata della sessione** cloud al minimo necessario.

### Attacco 5 — Self-hosted runner compromesso

**Scenario:** un self-hosted runner è compromesso. L'attaccante può intercettare le variabili `ACTIONS_ID_TOKEN_REQUEST_URL` e `ACTIONS_ID_TOKEN_REQUEST_TOKEN` per richiedere JWT.

**Mitigazione:**

1. Vincolare la trust policy a `runner_environment: github-hosted` per workflow critici.
2. Se necessario usare self-hosted runner, isolarli con ephemeral runner (un runner per job, distrutto dopo).
3. Usare runner self-hosted in container isolati con network policy restrittive.

### Matrice MITRE ATT&CK per OIDC in CI/CD

| Tecnica MITRE | Vettore OIDC | Mitigazione |
|---|---|---|
| **T1195.002** Supply Chain Compromise | Action malevola che ruba JWT | Pin SHA delle action |
| **T1078.004** Cloud Accounts | Trust policy permissiva | Vincoli granulari su subject |
| **T1550.001** Application Access Token | Token replay | TTL breve, audience specifico |
| **T1098** Account Manipulation | Modifica workflow per assumere ruoli | CODEOWNERS, branch protection |
| **T1537** Transfer to Cloud Account | Credenziali temporanee per exfiltration | Least privilege, permission boundary |
| **T1059** Command Execution | Script injection in workflow | Input validation, pinning |

---

## Architettura OIDC per organizzazioni enterprise

### Modello hub-and-spoke

```text
┌──────────────────────────────────────────────────────────────────────┐
│                        ORGANIZZAZIONE GITHUB                        │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Team Platform │  │ Team Backend │  │ Team Frontend│              │
│  │              │  │              │  │              │              │
│  │ repo-infra   │  │ repo-api     │  │ repo-web     │              │
│  │ repo-k8s     │  │ repo-worker  │  │ repo-mobile  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐        │
│  │                 Repository IaC centralizzato              │        │
│  │     (gestisce tutti i ruoli OIDC via Terraform)           │        │
│  │                                                           │        │
│  │  module "oidc_role_platform_dev" { ... }                  │        │
│  │  module "oidc_role_platform_prod" { ... }                 │        │
│  │  module "oidc_role_backend_dev" { ... }                   │        │
│  │  module "oidc_role_backend_prod" { ... }                  │        │
│  └──────────────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      CLOUD PROVIDER (AWS)                            │
│                                                                      │
│  Account Hub (Management)                                            │
│  ├── OIDC Provider: token.actions.githubusercontent.com              │
│  ├── Permission Boundaries per team                                  │
│  └── SCPs a livello Organization                                     │
│                                                                      │
│  Account Spoke — Platform Dev                                        │
│  └── Role: github-platform-dev (trust: repo-infra, repo-k8s)        │
│                                                                      │
│  Account Spoke — Platform Prod                                       │
│  └── Role: github-platform-prod (trust: repo-infra + env:production) │
│                                                                      │
│  Account Spoke — Backend Dev                                         │
│  └── Role: github-backend-dev (trust: repo-api, repo-worker)        │
│                                                                      │
│  Account Spoke — Backend Prod                                        │
│  └── Role: github-backend-prod (trust: repo-api + env:production)    │
└──────────────────────────────────────────────────────────────────────┘
```

### Terraform module riusabile per ruoli OIDC

```hcl
# modules/github-oidc-role/variables.tf
variable "role_name" {
  type        = string
  description = "Nome del ruolo IAM"
}

variable "github_org" {
  type        = string
  description = "Organizzazione GitHub"
}

variable "github_repos" {
  type        = list(string)
  description = "Lista di repository autorizzati"
}

variable "allowed_branches" {
  type        = list(string)
  default     = ["main"]
  description = "Branch autorizzati"
}

variable "allowed_environments" {
  type        = list(string)
  default     = []
  description = "Environment GitHub autorizzati"
}

variable "require_github_hosted_runner" {
  type        = bool
  default     = true
  description = "Richiedere runner GitHub-hosted"
}

variable "max_session_duration" {
  type        = number
  default     = 3600
  description = "Durata massima della sessione in secondi"
}

variable "permission_boundary_arn" {
  type        = string
  default     = null
  description = "ARN del permission boundary"
}

variable "policy_statements" {
  type = list(object({
    effect    = string
    actions   = list(string)
    resources = list(string)
  }))
  description = "Statement della permission policy"
}

variable "oidc_provider_arn" {
  type        = string
  description = "ARN dell'OIDC provider GitHub"
}

# modules/github-oidc-role/main.tf
locals {
  # Costruire le condizioni del subject
  subject_conditions = concat(
    # Branch-based conditions
    [for repo in var.github_repos :
      [for branch in var.allowed_branches :
        "repo:${var.github_org}/${repo}:ref:refs/heads/${branch}"
      ]
    ],
    # Environment-based conditions
    [for repo in var.github_repos :
      [for env in var.allowed_environments :
        "repo:${var.github_org}/${repo}:environment:${env}"
      ]
    ]
  )

  flat_subjects = flatten(local.subject_conditions)
}

resource "aws_iam_role" "this" {
  name                 = var.role_name
  max_session_duration = var.max_session_duration
  permissions_boundary = var.permission_boundary_arn

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = var.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = merge(
          {
            StringEquals = {
              "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            }
          },
          length(local.flat_subjects) == 1 ? {
            StringEquals = {
              "token.actions.githubusercontent.com:sub" = local.flat_subjects[0]
            }
          } : {
            StringLike = {
              "token.actions.githubusercontent.com:sub" = local.flat_subjects
            }
          },
          var.require_github_hosted_runner ? {
            StringEquals = {
              "token.actions.githubusercontent.com:runner_environment" = "github-hosted"
            }
          } : {}
        )
      }
    ]
  })

  tags = {
    ManagedBy = "terraform"
    GitHubOrg = var.github_org
    Purpose   = "github-actions-oidc"
  }
}

resource "aws_iam_role_policy" "this" {
  name = "${var.role_name}-policy"
  role = aws_iam_role.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [for stmt in var.policy_statements : {
      Effect   = stmt.effect
      Action   = stmt.actions
      Resource = stmt.resources
    }]
  })
}

# modules/github-oidc-role/outputs.tf
output "role_arn" {
  value       = aws_iam_role.this.arn
  description = "ARN del ruolo IAM"
}

output "role_name" {
  value       = aws_iam_role.this.name
  description = "Nome del ruolo IAM"
}
```

### Utilizzo del module

```hcl
# live/production/oidc-roles.tf

module "oidc_provider" {
  source = "../../modules/github-oidc-provider"
}

module "oidc_role_api_production" {
  source = "../../modules/github-oidc-role"

  role_name              = "github-api-production"
  github_org             = "myorg"
  github_repos           = ["api-service"]
  allowed_environments   = ["production"]
  oidc_provider_arn      = module.oidc_provider.arn
  permission_boundary_arn = aws_iam_policy.team_backend_boundary.arn
  max_session_duration   = 1800

  policy_statements = [
    {
      effect    = "Allow"
      actions   = ["ecs:UpdateService", "ecs:DescribeServices"]
      resources = ["arn:aws:ecs:eu-central-1:123:service/prod-cluster/api-*"]
    },
    {
      effect    = "Allow"
      actions   = ["ecr:GetAuthorizationToken"]
      resources = ["*"]
    },
    {
      effect    = "Allow"
      actions   = ["ecr:BatchCheckLayerAvailability", "ecr:PutImage", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart", "ecr:CompleteLayerUpload"]
      resources = ["arn:aws:ecr:eu-central-1:123:repository/api-service"]
    }
  ]
}
```

### Naming convention per ruoli OIDC

| Pattern | Esempio | Uso |
|---|---|---|
| `github-{team}-{env}` | `github-platform-production` | Ruolo per team + environment |
| `github-{repo}-{env}` | `github-api-service-production` | Ruolo per repository specifico |
| `github-{action}-{env}` | `github-deploy-production` | Ruolo per azione specifica |
| `gha-{provider}-{scope}` | `gha-ecr-push` | Ruolo per permesso specifico |

### Tag obbligatori sui ruoli cloud

```hcl
# Variabile per tag obbligatori
variable "required_tags" {
  type = map(string)
  default = {
    ManagedBy          = "terraform"
    Purpose            = "github-actions-oidc"
    SecurityReviewDate = "2026-05-24"
    Owner              = "platform-team"
  }
}
```

---

## Monitoring, alerting e compliance

### AWS CloudTrail — monitoring degli eventi OIDC

```bash
# Query CloudTrail per eventi AssumeRoleWithWebIdentity recenti
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRoleWithWebIdentity \
  --start-time "$(date -u -d '24 hours ago' '+%Y-%m-%dT%H:%M:%SZ')" \
  --max-results 50 \
  | jq '.Events[] | .CloudTrailEvent | fromjson | {
    eventTime,
    sourceIPAddress,
    recipientAccountId,
    requestParameters: {
      roleArn: .requestParameters.roleArn,
      roleSessionName: .requestParameters.roleSessionName
    },
    responseElements: {
      assumedRoleId: .responseElements.assumedRoleUser.assumedRoleId
    },
    errorCode,
    errorMessage
  }'
```

### CloudWatch Alarms per eventi OIDC anomali

```hcl
# cloudwatch_oidc_monitoring.tf

# Metric filter per errori di autenticazione OIDC
resource "aws_cloudwatch_log_metric_filter" "oidc_auth_failure" {
  name           = "oidc-auth-failures"
  pattern        = "{ $.eventName = \"AssumeRoleWithWebIdentity\" && $.errorCode = \"*\" }"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name

  metric_transformation {
    name      = "OIDCAuthFailures"
    namespace = "GitHubActions/OIDC"
    value     = "1"
  }
}

# Alarm per troppi errori di autenticazione
resource "aws_cloudwatch_metric_alarm" "oidc_auth_failures" {
  alarm_name          = "oidc-auth-failures-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "OIDCAuthFailures"
  namespace           = "GitHubActions/OIDC"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Troppe autenticazioni OIDC fallite negli ultimi 5 minuti"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
}

# Metric filter per utilizzo da repository inattesi
resource "aws_cloudwatch_log_metric_filter" "oidc_unknown_repo" {
  name           = "oidc-unknown-repository"
  pattern        = "{ $.eventName = \"AssumeRoleWithWebIdentity\" && $.requestParameters.roleSessionName != \"gha-deploy-*\" }"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name

  metric_transformation {
    name      = "OIDCUnknownRepo"
    namespace = "GitHubActions/OIDC"
    value     = "1"
  }
}

# Alarm per utilizzo da repository sconosciuti
resource "aws_cloudwatch_metric_alarm" "oidc_unknown_repo" {
  alarm_name          = "oidc-unknown-repository-usage"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "OIDCUnknownRepo"
  namespace           = "GitHubActions/OIDC"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Autenticazione OIDC da repository non riconosciuto"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
  treat_missing_data  = "notBreaching"
}
```

### Azure Monitor — diagnostica OIDC

```bash
# Query Azure AD sign-in logs per autenticazioni federate
az monitor log-analytics query \
  --workspace "$LOG_ANALYTICS_WORKSPACE_ID" \
  --analytics-query "
    AADServicePrincipalSignInLogs
    | where TimeGenerated > ago(24h)
    | where AuthenticationProcessingDetails contains 'Federated'
    | project TimeGenerated, ServicePrincipalName, IPAddress,
              ResourceDisplayName, Status, ConditionalAccessStatus
    | order by TimeGenerated desc
  " \
  --output table
```

### GCP Cloud Audit Logs — monitoring OIDC

```bash
# Filtrare i log di autenticazione Workload Identity
gcloud logging read '
  resource.type="audited_resource"
  protoPayload.methodName="google.iam.credentials.v1.IAMCredentials.GenerateAccessToken"
  timestamp>="2026-05-24T00:00:00Z"
' \
  --project="my-project" \
  --format="json" \
  | jq '.[].protoPayload | {
    timestamp: .requestMetadata.requestAttributes.time,
    callerIp: .requestMetadata.callerIp,
    serviceAccountEmail: .request.name,
    status: .status
  }'
```

### Dashboard di compliance OIDC

Una dashboard di compliance dovrebbe tracciare le seguenti metriche:

| Metrica | Soglia | Alert |
|---|---|---|
| Autenticazioni OIDC fallite / ora | > 10 | WARNING |
| Autenticazioni OIDC fallite / ora | > 50 | CRITICAL |
| Autenticazioni da IP non previsti | > 0 | CRITICAL |
| Sessioni con durata > 1 ora | > 5 / giorno | WARNING |
| Ruoli OIDC senza permission boundary | > 0 | HIGH |
| Trust policy con wildcard `*` non qualificato | > 0 | CRITICAL |
| Secret statici ancora presenti in GitHub | > 0 | HIGH (dopo migrazione) |
| Ruoli OIDC non usati da > 90 giorni | > 0 | INFO (cleanup) |

### Report di compliance periodico

```bash
#!/usr/bin/env bash
# report_oidc_compliance.sh — genera report settimanale

echo "=== OIDC Compliance Report — $(date -u '+%Y-%m-%d') ==="
echo ""

echo "--- Ruoli OIDC AWS ---"
aws iam list-roles --query "Roles[?AssumeRolePolicyDocument.Statement[?Condition.StringEquals.\"token.actions.githubusercontent.com:aud\"]].[RoleName,MaxSessionDuration,CreateDate]" --output table

echo ""
echo "--- Ruoli senza Permission Boundary ---"
aws iam list-roles --query "Roles[?AssumeRolePolicyDocument.Statement[?Condition.StringEquals.\"token.actions.githubusercontent.com:aud\"] && !PermissionsBoundary].[RoleName]" --output table

echo ""
echo "--- Eventi OIDC falliti nelle ultime 24h ---"
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRoleWithWebIdentity \
  --start-time "$(date -u -d '24 hours ago' '+%Y-%m-%dT%H:%M:%SZ')" \
  | jq '[.Events[].CloudTrailEvent | fromjson | select(.errorCode != null)] | length'

echo ""
echo "--- Audit completato ---"
```

---

## Migrazione da secret statici a OIDC — Playbook completo

### Fase 0 — Inventario (settimana 1)

Catalogare tutti i secret statici cloud presenti nei repository GitHub:

```bash
# Listare tutti i secret di un repository
gh secret list --repo myorg/myrepo

# Listare i secret di tutti i repository dell'org
for repo in $(gh repo list myorg --limit 500 --json name -q '.[].name'); do
  echo "=== $repo ==="
  gh secret list --repo "myorg/$repo" 2>/dev/null | grep -iE 'AWS|AZURE|GCP|CLOUD'
done
```

Creare una matrice di inventario:

| Repository | Secret | Cloud Provider | Uso | Priorità migrazione |
|---|---|---|---|---|
| api-service | `AWS_ACCESS_KEY_ID` | AWS | Deploy ECS | Alta |
| api-service | `AWS_SECRET_ACCESS_KEY` | AWS | Deploy ECS | Alta |
| web-app | `AZURE_CREDENTIALS` | Azure | Deploy App Service | Alta |
| data-pipeline | `GCP_SA_KEY` | GCP | Deploy Cloud Run | Media |

### Fase 1 — Configurare il provider OIDC (settimana 2)

```bash
# AWS: creare OIDC provider (una volta per account)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com

# Azure: registrare app con federated credential
az ad app create --display-name "github-actions-oidc"
# ... aggiungere federated credentials

# GCP: creare workload identity pool e provider
gcloud iam workload-identity-pools create github-pool \
  --project="my-project" --location="global"
```

### Fase 2 — Creare ruoli con trust policy (settimana 2-3)

Applicare il principio di least privilege:

```hcl
# Per ogni repository/environment, creare un ruolo dedicato
# Usare il module Terraform riutilizzabile descritto sopra
module "oidc_role_api_dev" {
  source = "../../modules/github-oidc-role"
  # ...
}
```

### Fase 3 — Testare su branch non-production (settimana 3-4)

```yaml
# Creare un workflow di test su un feature branch
name: Test OIDC Authentication
on:
  push:
    branches: [feature/oidc-migration]

permissions:
  id-token: write
  contents: read

jobs:
  test-oidc:
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123:role/github-api-dev
          aws-region: eu-central-1

      - name: Verify credentials
        run: |
          aws sts get-caller-identity
          echo "OIDC authentication successful"

      - name: Test access to required resources
        run: |
          aws s3 ls s3://dev-deploy-bucket/ || echo "S3 access OK"
          aws ecr describe-repositories || echo "ECR access OK"
```

### Fase 4 — Migrazione graduale in produzione (settimana 4-6)

Strategia: **dual-mode** — mantenere sia OIDC che secret statici durante la transizione.

```yaml
name: Deploy (OIDC + fallback)
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

      # Tentare OIDC prima
      - name: Configure AWS (OIDC)
        id: oidc
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123:role/github-deploy
          aws-region: eu-central-1
        continue-on-error: true

      # Fallback a secret statici solo se OIDC fallisce
      - name: Configure AWS (static - fallback)
        if: steps.oidc.outcome == 'failure'
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: eu-central-1

      - name: Log auth method
        run: |
          if [ "${{ steps.oidc.outcome }}" = "success" ]; then
            echo "Authenticated via OIDC"
          else
            echo "WARNING: Fell back to static credentials"
          fi

      - name: Deploy
        run: ./scripts/deploy.sh
```

### Fase 5 — Rimozione dei secret statici (settimana 7-8)

Dopo aver verificato che OIDC funziona stabilmente per almeno 2 settimane:

```bash
# 1. Rimuovere i secret dal repository GitHub
gh secret delete AWS_ACCESS_KEY_ID --repo myorg/api-service
gh secret delete AWS_SECRET_ACCESS_KEY --repo myorg/api-service

# 2. Revocare le credenziali statiche nel cloud provider
# AWS: disattivare la access key
aws iam update-access-key \
  --user-name github-actions-user \
  --access-key-id AKIAEXAMPLE \
  --status Inactive

# Attendere 7 giorni, poi eliminare
# aws iam delete-access-key --user-name github-actions-user --access-key-id AKIAEXAMPLE

# 3. Rimuovere il fallback dal workflow
# Eliminare gli step con secret statici
```

### Fase 6 — Validazione e documentazione (settimana 8)

- [ ] Tutti i workflow usano OIDC
- [ ] Nessun secret statico cloud rimane nei repository
- [ ] Le credenziali statiche sono revocate nel cloud
- [ ] I ruoli OIDC sono documentati
- [ ] Il monitoring è attivo
- [ ] Il team è formato sulla nuova architettura

---

## OIDC con provider aggiuntivi

### DigitalOcean Spaces e Container Registry

DigitalOcean supporta OIDC via Spaces e Container Registry usando un approccio basato su token API scambiato tramite un servizio intermediario.

```yaml
# Workaround: usare Vault come intermediario per DigitalOcean
name: Deploy to DigitalOcean via OIDC + Vault
on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Get DigitalOcean token from Vault via OIDC
        uses: hashicorp/vault-action@v3
        with:
          url: https://vault.mycompany.com
          method: jwt
          role: github-digitalocean
          jwtGithubAudience: https://vault.mycompany.com
          secrets: |
            secret/data/digitalocean api_token | DIGITALOCEAN_ACCESS_TOKEN

      - name: Deploy to DigitalOcean App Platform
        uses: digitalocean/app_action/deploy@v2
        with:
          token: ${{ env.DIGITALOCEAN_ACCESS_TOKEN }}
```

### Oracle Cloud Infrastructure (OCI)

OCI supporta nativamente la federazione OIDC con GitHub Actions:

```bash
# Creare un identity provider per GitHub
oci iam identity-provider create \
  --compartment-id "$TENANCY_OCID" \
  --name "GitHubActions" \
  --description "GitHub Actions OIDC" \
  --metadata-url "https://token.actions.githubusercontent.com/.well-known/openid-configuration" \
  --protocol "SAML2"  # OCI usa SAML come wrapper per OIDC
```

### Cloudflare Workers e R2

Cloudflare supporta API tokens con scope limitato; per integrare con OIDC usare Vault come intermediario:

```yaml
- name: Get Cloudflare token from Vault
  uses: hashicorp/vault-action@v3
  with:
    url: https://vault.mycompany.com
    method: jwt
    role: github-cloudflare
    jwtGithubAudience: https://vault.mycompany.com
    secrets: |
      secret/data/cloudflare api_token | CLOUDFLARE_API_TOKEN

- name: Deploy to Cloudflare Workers
  uses: cloudflare/wrangler-action@v3
  with:
    apiToken: ${{ env.CLOUDFLARE_API_TOKEN }}
```

### Pattern generico — OIDC per provider non nativi

Per qualsiasi provider che non supporta nativamente OIDC con GitHub, il pattern è:

```text
GitHub Actions ──OIDC──► HashiCorp Vault ──secret──► Provider non-OIDC
     JWT                     Token Vault              (DO, Cloudflare, etc.)
```

Vantaggi di questo pattern:
1. Il secret del provider è custodito in Vault, non in GitHub.
2. L'accesso a Vault è autenticato via OIDC (zero secret nel repo).
3. Il token Vault è temporaneo (5-15 min).
4. Vault fornisce audit log completo di chi ha letto quale secret.

---

## Confronto dettagliato tra cloud provider

### Matrice comparativa completa

| Caratteristica | AWS | Azure | GCP |
|---|---|---|---|
| **Servizio di federazione** | IAM OIDC Provider | Entra ID Federated Credentials | Workload Identity Federation |
| **Azione STS** | `AssumeRoleWithWebIdentity` | Token exchange OAuth2 | `ExchangeToken` via STS |
| **Audience default** | `sts.amazonaws.com` | `api://AzureADTokenExchange` | URL del provider WIF |
| **Action ufficiale** | `aws-actions/configure-aws-credentials@v4` | `azure/login@v2` | `google-github-actions/auth@v2` |
| **Durata credenziali** | 15 min - 12 ore | 1 ora (fisso) | 10 min - 12 ore |
| **Durata configurabile** | Si (`role-duration-seconds`) | No (1 ora fisso) | Si (`token_format` e `access_token_lifetime`) |
| **Limite federated creds** | Nessuno pratico | 20 per app registration | 200 provider per pool |
| **Wildcard nel subject** | Si (`StringLike`) | Solo con Flexible FIC (preview) | Si (CEL expressions) |
| **Attribute mapping** | No (solo claims standard) | No (solo subject) | Si (mappatura claims → attributi) |
| **Attribute conditions** | Condition keys nella trust policy | Claims matching expression (preview) | CEL expressions |
| **Session tags** | Solo via Cognito Identity Pools | Non supportato | Tramite attribute mapping |
| **Cross-account** | Si (role chaining) | Si (multi-tenant app) | Si (cross-project binding) |
| **Terraform support** | Completo | Completo (tranne flexible FIC) | Completo |
| **Audit** | CloudTrail | Azure AD Sign-in logs | Cloud Audit Logs |
| **GHES supporto** | Si (3.5+) | Si (3.5+) | Si (3.5+) |

### Matrice di sicurezza comparativa

| Controllo di sicurezza | AWS | Azure | GCP |
|---|---|---|---|
| **Vincolo su repository** | Via `sub` claim | Via `subject` match | Via `attribute.repository` |
| **Vincolo su branch** | Via `sub` claim | Via `subject` match | Via `attribute.ref` |
| **Vincolo su environment** | Via `sub` claim | Via `subject` match | Via `attribute.environment` (custom) |
| **Vincolo su workflow file** | Via `job_workflow_ref` | Via flexible FIC claims | Via `attribute.job_workflow_ref` (custom) |
| **Vincolo su runner type** | Via `runner_environment` | Non supportato nativamente | Via custom attribute |
| **Permission boundary** | Si | No (ma scoped RBAC) | No (ma IAM conditions) |
| **SCP / Policy org** | Si (Organizations) | Si (Azure Policy) | Si (Organization Policy) |
| **Audit granulare** | Session name in CloudTrail | Service principal in logs | Caller identity in audit logs |

### Quale provider scegliere per ogni scenario

| Scenario | Raccomandazione | Motivo |
|---|---|---|
| **Massima granularità claim** | GCP | Attribute mapping e CEL expressions offrono il matching più flessibile |
| **Cross-account complesso** | AWS | Role chaining e Organizations forniscono il modello multi-account più maturo |
| **Semplicità di setup** | Azure | Meno componenti da configurare (app registration + federated credential) |
| **Multi-repo con pattern matching** | GCP o AWS | GCP con CEL, AWS con StringLike; Azure richiede flexible FIC in preview |
| **Session-based ABAC** | AWS (con Cognito) | Unico provider con percorso per session tags da OIDC |
| **Enterprise multi-tenant** | Azure | Entra ID supporta nativamente multi-tenancy |

---

## Scenari reali e case study

### Caso 1 — Migrazione di una piattaforma e-commerce (45 repository)

**Contesto:** un'organizzazione con 45 repository, 120 workflow di deploy, 3 ambienti (dev, staging, production), distribuiti su AWS (primario) e GCP (datalake).

**Sfide:**
- 90 secret statici AWS sparsi nei repository
- 15 service account key GCP
- Nessuna standardizzazione dei permessi

**Soluzione implementata:**

1. **Repository centralizzato IaC** per gestire tutti i ruoli OIDC via Terraform.
2. **Module Terraform riusabile** con input standardizzati (repository, environment, permessi).
3. **Naming convention** rigida: `github-{team}-{env}-{scope}`.
4. **Permission boundaries** per team per limitare l'escalation.
5. **Migrazione graduale:** 3 settimane per dev, 2 settimane per staging, 3 settimane per production.

**Risultati:**
- Secret statici eliminati: da 105 a 0
- Tempo medio di rotazione: da 90 giorni (manuale) a 0 (automatico)
- Incidenti di credential leak: da 2/anno a 0
- Compliance SOC 2: audit OIDC automatizzato

### Caso 2 — Pipeline multi-cloud per SaaS (AWS + Azure + GCP)

**Contesto:** un'applicazione SaaS distribuita su tutti e tre i major cloud provider con deploy simultanei.

**Architettura workflow:**

```yaml
name: Multi-cloud release
on:
  release:
    types: [published]

permissions:
  id-token: write
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build artifact
        run: make build
      - uses: actions/upload-artifact@v4
        with:
          name: release-artifact
          path: ./dist/

  deploy-aws:
    needs: build
    runs-on: ubuntu-latest
    environment: aws-production
    steps:
      - uses: actions/download-artifact@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123:role/github-release
          aws-region: eu-central-1
          role-duration-seconds: 1800
      - run: ./scripts/deploy-aws.sh

  deploy-azure:
    needs: build
    runs-on: ubuntu-latest
    environment: azure-production
    steps:
      - uses: actions/download-artifact@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ vars.AZURE_CLIENT_ID }}
          tenant-id: ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - run: ./scripts/deploy-azure.sh

  deploy-gcp:
    needs: build
    runs-on: ubuntu-latest
    environment: gcp-production
    steps:
      - uses: actions/download-artifact@v4
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: projects/123/locations/global/workloadIdentityPools/pool/providers/ghprovider
          service_account: deploy@project.iam.gserviceaccount.com
      - run: ./scripts/deploy-gcp.sh

  verify:
    needs: [deploy-aws, deploy-azure, deploy-gcp]
    runs-on: ubuntu-latest
    steps:
      - name: Smoke test all regions
        run: ./scripts/smoke-test-all.sh
```

### Caso 3 — Vault come hub dei secret per team di 200 sviluppatori

**Contesto:** grande organizzazione con 200 sviluppatori, 300+ repository, necessità di accesso a secret applicativi (DB passwords, API keys di terze parti, certificati TLS).

**Architettura:**

```text
200 sviluppatori
    │
    ▼
300+ repository GitHub
    │ (OIDC JWT per ogni workflow run)
    ▼
HashiCorp Vault Enterprise (3 namespace)
    ├── namespace: platform
    │   ├── secret/deploy/production/*
    │   └── secret/certificates/*
    ├── namespace: backend
    │   ├── secret/databases/*
    │   └── secret/api-keys/*
    └── namespace: frontend
        ├── secret/cdn/*
        └── secret/analytics/*
```

**Benefici chiave:**
- Zero secret nei repository GitHub
- Audit centralizzato di tutti gli accessi ai secret
- Rotazione automatica dei secret (Vault dynamic secrets per database)
- Isolamento tra team via namespace Vault

---

## Esercizi avanzati — Laboratori pratici

### Lab 6 — OIDC Vault con dynamic database secrets

1. Configura Vault JWT auth per il tuo repository GitHub.
2. Configura il database secret engine di Vault per PostgreSQL.
3. Crea una policy Vault che permetta al workflow di generare credenziali DB temporanee.
4. Crea un workflow che autentica via OIDC, ottiene credenziali DB temporanee da Vault, esegue una migrazione, e verifica che le credenziali scadano automaticamente.

### Lab 7 — Multi-cloud OIDC con environment protection

1. Configura OIDC su tutti e tre i cloud provider (AWS, Azure, GCP).
2. Crea un workflow multi-cloud con job paralleli.
3. Proteggi ogni environment cloud con required reviewers diversi.
4. Verifica che il deploy richieda approvazione per ogni cloud provider indipendentemente.

### Lab 8 — ABAC con repository custom properties

1. Crea custom properties a livello organizzazione: `team`, `data_classification`.
2. Assegna valori a tre repository diversi.
3. Abilita le proprietà nei token OIDC.
4. Crea trust policy AWS basate sui custom property claims.
5. Verifica che repository con valori diversi non possano assumere ruoli sbagliati.

### Lab 9 — Azure Flexible Federated Credentials

1. Crea un'app registration Azure con una flexible federated credential.
2. Usa un'espressione che accetti qualsiasi branch del tuo repository.
3. Testa l'accesso da branch main, develop, e un feature branch.
4. Modifica l'espressione per limitare a main e tag di release.

### Lab 10 — Monitoring e alerting OIDC

1. Configura CloudTrail per registrare tutti gli eventi `AssumeRoleWithWebIdentity`.
2. Crea un CloudWatch metric filter per contare le autenticazioni fallite.
3. Imposta un alarm che notifica via SNS quando ci sono più di 5 errori in 10 minuti.
4. Genera intenzionalmente errori di autenticazione e verifica che l'alarm scatti.

### Lab 11 — Migrazione incrementale da secret statici

1. Prendi un workflow esistente che usa secret statici AWS.
2. Implementa il pattern dual-mode (OIDC con fallback a secret statici).
3. Esegui il workflow 5 volte verificando che OIDC venga usato ogni volta.
4. Rimuovi il fallback e i secret statici.
5. Revoca le credenziali statiche in AWS.

### Lab 12 — Cross-account role chaining con OIDC

1. Configura due account AWS (hub e spoke).
2. Crea un OIDC provider solo nell'account hub.
3. Crea un ruolo hub che il workflow assume via OIDC.
4. Crea un ruolo spoke che il ruolo hub può assumere.
5. Implementa il workflow con role chaining e verifica l'identità in ogni step.

---

## Troubleshooting avanzato — 20 problemi aggiuntivi

### 21. Vault: `permission denied` dopo autenticazione JWT riuscita

**Causa:** il token Vault è stato emesso ma la policy associata al ruolo non include il path richiesto.

**Soluzione:**
```bash
# Verificare le policy del token
vault token lookup -accessor "$TOKEN_ACCESSOR"

# Verificare la policy del ruolo
vault read auth/jwt/role/github-production

# Aggiungere il path mancante alla policy
vault policy write github-deploy - <<EOF
path "secret/data/deploy/*" {
  capabilities = ["read", "list"]
}
path "secret/data/missing-path/*" {
  capabilities = ["read"]
}
EOF
```

### 22. Vault: `role not found` durante il login JWT

**Causa:** il ruolo specificato nel workflow non esiste nel mount path JWT configurato.

**Soluzione:**
```bash
# Listare i ruoli disponibili
vault list auth/jwt/role

# Verificare che il mount path sia corretto
vault auth list
# Se il mount è "jwt-github/" invece di "jwt/"
# specificare nel workflow: method: jwt-github
```

### 23. HCP Terraform: `Error: Invalid provider configuration`

**Causa:** le variabili del workspace per Dynamic Provider Credentials non sono configurate correttamente.

**Soluzione:** verificare che le variabili environment siano impostate nel workspace Terraform:
- `TFC_AWS_PROVIDER_AUTH` = `true`
- `TFC_AWS_RUN_ROLE_ARN` = ARN del ruolo
- `TFC_AWS_WORKLOAD_IDENTITY_AUDIENCE` = audience configurato nel provider OIDC

### 24. AWS: `AssumeRoleWithWebIdentity` funziona ma le credenziali non hanno i permessi attesi

**Causa:** permission boundary sul ruolo limita i permessi effettivi.

**Soluzione:**
```bash
# Verificare se c'è un permission boundary
aws iam get-role --role-name github-deploy | jq '.Role.PermissionsBoundary'

# I permessi effettivi sono l'intersezione tra:
# permission policy ∩ permission boundary ∩ SCP
```

### 25. GCP: `FAILED_PRECONDITION: Workload Identity Pool Provider is disabled`

**Causa:** il provider nel pool è stato disabilitato (manualmente o via IaC).

**Soluzione:**
```bash
gcloud iam workload-identity-pools providers update-oidc "github-provider" \
  --project="my-project" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --disabled=false
```

### 26. Azure: massimo 20 federated credentials raggiunto

**Causa:** Azure limita a 20 federated identity credentials per app registration.

**Soluzione:** opzioni alternative:
1. Usare Flexible Federated Identity Credentials (preview) per ridurre il numero necessario.
2. Creare più app registration, una per team o per gruppo di repository.
3. Usare User-Assigned Managed Identity (stesso limite, ma isolamento migliore).

### 27. OIDC token non disponibile in job che usa container

**Causa:** i container custom non ereditano automaticamente le variabili OIDC.

**Soluzione:**
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    container:
      image: node:20
      # Le variabili OIDC sono passate automaticamente al container
      # MA l'action deve supportare il contesto container
    steps:
      # Usare l'action direttamente — gestisce il contesto
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123:role/deploy
          aws-region: eu-central-1
```

### 28. Errore intermittente: `Error: Couldn't retrieve verification key`

**Causa:** il cloud provider non riesce a scaricare le chiavi JWKS da GitHub. Problema transitorio di rete o rate limiting.

**Soluzione:**
```yaml
# Aggiungere retry logic
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123:role/deploy
    aws-region: eu-central-1
    retry-max-attempts: 5
    http-proxy: ""  # Verificare che non ci sia un proxy che blocca
```

### 29. Workflow dispatch manuale non funziona con trust policy per `push`

**Causa:** `workflow_dispatch` genera un subject diverso rispetto a `push`. Il `ref` potrebbe essere diverso se l'utente seleziona un branch non protetto.

**Soluzione:**
```json
{
  "Condition": {
    "StringLike": {
      "token.actions.githubusercontent.com:sub": [
        "repo:myorg/myrepo:ref:refs/heads/main",
        "repo:myorg/myrepo:environment:production"
      ]
    }
  }
}
```

### 30. GCP: `attribute_condition` con CEL expression complessa causa errore di sintassi

**Causa:** le espressioni CEL hanno una sintassi precisa; errori comuni includono virgolette sbagliate o operatori non supportati.

**Soluzione:**
```bash
# Sintassi corretta per espressioni CEL complesse
--attribute-condition="
  assertion.repository_owner == 'myorg' &&
  (assertion.ref == 'refs/heads/main' || assertion.ref.startsWith('refs/tags/v'))
"

# Operatori CEL supportati: ==, !=, &&, ||, !, in, startsWith, matches
# NON supportati: =~, like, contains (per stringhe usare .contains())
```

### 31. Credenziali OIDC scadono durante build Docker lunga

**Causa:** il build Docker impiega più tempo della durata delle credenziali temporanee.

**Soluzione:**
```yaml
# Aumentare la durata per job con build lunghi
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123:role/deploy
    aws-region: eu-central-1
    role-duration-seconds: 7200  # 2 ore

# Oppure: ri-autenticarsi prima del push
- name: Build Docker image
  run: docker build -t myimage .

# Ri-autenticarsi con credenziali fresche prima di pushare
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123:role/deploy
    aws-region: eu-central-1
    role-duration-seconds: 900

- name: Push to ECR
  run: |
    aws ecr get-login-password | docker login --username AWS --password-stdin 123.dkr.ecr.eu-central-1.amazonaws.com
    docker push 123.dkr.ecr.eu-central-1.amazonaws.com/myimage
```

### 32. Scheduled workflow (cron) e OIDC

**Causa:** i workflow schedulati generano un subject con il branch default del repository, ma la trust policy potrebbe richiedere un environment.

**Soluzione:**
```yaml
on:
  schedule:
    - cron: '0 2 * * *'

# Il subject per schedule è: repo:org/repo:ref:refs/heads/main
# NON include environment anche se il job specifica environment:
```

Trust policy compatibile con schedule:
```json
{
  "StringLike": {
    "token.actions.githubusercontent.com:sub": [
      "repo:myorg/myrepo:ref:refs/heads/main",
      "repo:myorg/myrepo:environment:production"
    ]
  }
}
```

### 33. Composite action non propaga il token OIDC

**Causa:** le composite action hanno accesso limitato alle API interne di GitHub.

**Soluzione:** nelle composite action, usare `${{ github.token }}` non è sufficiente per OIDC. Passare il token come input:

```yaml
# Nella composite action
inputs:
  oidc-token:
    description: 'OIDC token from caller'
    required: true
runs:
  using: composite
  steps:
    - run: |
        # Usare il token passato come input
        echo "Token disponibile: ${#OIDC_TOKEN}"
      env:
        OIDC_TOKEN: ${{ inputs.oidc-token }}
```

Oppure usare una JavaScript action con `@actions/core`:

```javascript
const core = require('@actions/core');
const token = await core.getIDToken('sts.amazonaws.com');
```

### 34. AWS Organizations SCP blocca AssumeRoleWithWebIdentity

**Causa:** un Service Control Policy a livello Organization nega `sts:AssumeRoleWithWebIdentity` per il principale.

**Soluzione:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowOIDCFromGitHub",
      "Effect": "Allow",
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Resource": "arn:aws:iam::*:role/github-*",
      "Condition": {
        "StringEquals": {
          "sts:ExternalIdType": "token.actions.githubusercontent.com"
        }
      }
    }
  ]
}
```

### 35. Azure: login riesce ma le operazioni successive falliscono con `AuthorizationFailed`

**Causa:** il service principal ha la federated credential configurata correttamente, ma non ha l'assegnazione RBAC sulle risorse target.

**Soluzione:**
```bash
# Verificare le assegnazioni RBAC
az role assignment list --assignee "$APP_ID" --all --output table

# Aggiungere l'assegnazione mancante con scope specifico
az role assignment create \
  --assignee "$APP_ID" \
  --role "Contributor" \
  --scope "/subscriptions/$SUB_ID/resourceGroups/$RG_NAME"
```

### 36. GCP: `IAM_PERMISSION_DENIED` per `iam.serviceAccounts.getAccessToken`

**Causa:** il binding `roles/iam.workloadIdentityUser` non è impostato correttamente, oppure il membro nel binding non corrisponde all'attributo mappato.

**Soluzione:**
```bash
# Verificare il binding
gcloud iam service-accounts get-iam-policy \
  "sa@project.iam.gserviceaccount.com" \
  --format=json | jq '.bindings'

# Il membro deve corrispondere esattamente all'attributo mappato
# Formato: principalSet://iam.googleapis.com/POOL/attribute.ATTR/VALUE
```

### 37. Multipli audience nello stesso job

**Causa:** un job deve autenticarsi verso più provider OIDC con audience diversi.

**Soluzione:** richiedere token separati con audience diversi:

```yaml
- name: Auth to AWS
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123:role/deploy
    aws-region: eu-central-1
    # audience: sts.amazonaws.com (default)

# Dopo aver usato AWS, autenticarsi verso Vault con audience diverso
- name: Auth to Vault
  run: |
    VAULT_JWT=$(curl -sS \
      -H "Authorization: bearer ${ACTIONS_ID_TOKEN_REQUEST_TOKEN}" \
      "${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=https://vault.mycompany.com" \
      | jq -r '.value')
    # Il JWT per Vault ha audience diverso da quello per AWS
```

### 38. `dependabot` workflow non supporta OIDC

**Causa:** Dependabot non ha il permesso `id-token: write` e non può richiedere token OIDC.

**Soluzione:** per Dependabot, continuare a usare Dependabot Secrets per le credenziali cloud. Non esiste un workaround.

```yaml
# Workflow separato per Dependabot
on:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      # Per Dependabot: usare secret statici dedicati
      - if: github.actor == 'dependabot[bot]'
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.DEPENDABOT_AWS_KEY }}
          aws-secret-access-key: ${{ secrets.DEPENDABOT_AWS_SECRET }}
          aws-region: eu-central-1

      # Per utenti umani: usare OIDC
      - if: github.actor != 'dependabot[bot]'
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123:role/github-pr
          aws-region: eu-central-1
```

### 39. OIDC con GitHub Enterprise Server (GHES) e certificati self-signed

**Causa:** GHES usa un issuer diverso (`https://YOUR_GHES/_services/token`) e potrebbe usare certificati TLS non trusted pubblicamente.

**Soluzione:**
```bash
# AWS: aggiungere il thumbprint del certificato GHES
THUMBPRINT=$(openssl s_client -connect ghes.mycompany.com:443 \
  -servername ghes.mycompany.com < /dev/null 2>/dev/null \
  | openssl x509 -fingerprint -noout \
  | sed 's/://g' | cut -d= -f2 | tr '[:upper:]' '[:lower:]')

aws iam create-open-id-connect-provider \
  --url "https://ghes.mycompany.com/_services/token" \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list "$THUMBPRINT"
```

### 40. Gestire la rotazione dei thumbprint del certificato

**Causa:** AWS richiede il thumbprint del certificato TLS per verificare l'identità del provider OIDC. Se il certificato di GitHub viene rinnovato, il thumbprint cambia.

**Soluzione:**
```bash
# Aggiornare il thumbprint
NEW_THUMBPRINT=$(openssl s_client -connect token.actions.githubusercontent.com:443 \
  -servername token.actions.githubusercontent.com < /dev/null 2>/dev/null \
  | openssl x509 -fingerprint -noout \
  | sed 's/://g' | cut -d= -f2 | tr '[:upper:]' '[:lower:]')

aws iam update-open-id-connect-provider-thumbprint \
  --open-id-connect-provider-arn "arn:aws:iam::123:oidc-provider/token.actions.githubusercontent.com" \
  --thumbprint-list "$NEW_THUMBPRINT"

# Nota: da luglio 2023, AWS verifica anche tramite la CA root trust store,
# quindi l'aggiornamento del thumbprint è meno critico per github.com.
# Rimane importante per GHES con certificati self-signed.
```

---

## FAQ avanzate — 20 domande aggiuntive

### 21. Posso usare OIDC con GitHub Actions Large Runners?

Si. I large runner (GitHub-hosted) supportano OIDC esattamente come i runner standard. Il claim `runner_environment` sarà `github-hosted`. Per i large runner self-hosted di tipo macOS o GPU, il claim sarà `self-hosted`.

### 22. Come gestisco OIDC in un monorepo con deploy indipendenti?

Usa environment diversi per ogni servizio del monorepo. Ogni environment mappa a un ruolo cloud separato:

```yaml
jobs:
  deploy-service-a:
    environment: service-a-production
    # Assume ruolo specifico per service-a

  deploy-service-b:
    environment: service-b-production
    # Assume ruolo specifico per service-b
```

### 23. OIDC funziona con le GitHub Actions Immutable Actions (2026)?

Si. Le Immutable Actions (annunciate nel roadmap 2026) fissano il codice dell'action a un commit immutabile. OIDC rimane invariato — il claim `job_workflow_ref` rifletterà il commit immutabile dell'action.

### 24. Posso usare OIDC per autenticarmi verso container registries?

Si. I principali container registry cloud supportano OIDC:
- **ECR**: via `aws-actions/configure-aws-credentials` + `aws ecr get-login-password`
- **ACR**: via `azure/login` + `azure/docker-login`
- **Artifact Registry / GCR**: via `google-github-actions/auth` + `docker/login-action`
- **GHCR**: non serve OIDC — usa `GITHUB_TOKEN` nativo

### 25. Come faccio testing locale di workflow OIDC?

Non puoi replicare OIDC localmente in modo fedele. Alternative:
1. Usare un branch di test con trust policy dedicata.
2. Per Vault, creare un ruolo di test con vincoli meno rigidi.
3. Per test di integrazione puri, usare credenziali locali (AWS profiles, `gcloud auth`).

### 26. Quanto impatta OIDC sulla velocità del workflow?

L'overhead è minimo: tipicamente 2-5 secondi per il token exchange. Il round-trip include la richiesta JWT a GitHub (~200ms), la verifica JWKS da parte del cloud provider (~500ms), e l'emissione delle credenziali (~300ms).

### 27. OIDC supporta token per ambienti che richiedono multi-factor authentication?

No direttamente. OIDC fornisce autenticazione a livello di workflow, non di utente. Per richiedere MFA sul deploy di produzione, usare:
1. GitHub Environment protection rules con required reviewers.
2. Un approval gate che richiede 2FA prima di approvare il deploy.

### 28. Posso revocarer un token OIDC prima della scadenza?

Il JWT GitHub non può essere revocato (è stateless). Tuttavia, le credenziali cloud risultanti possono essere revocate:
- **AWS**: `aws sts revoke-session` per la sessione STS
- **Azure**: revoca del token via Microsoft Graph
- **GCP**: non è possibile revocare singoli access token; scadono automaticamente

### 29. Come gestisco il disaster recovery per la configurazione OIDC?

1. Gestire tutta la configurazione OIDC via IaC (Terraform) con stato remoto.
2. Mantenere un documento di runbook per la riconfigurazione manuale d'emergenza.
3. Avere una coppia di credenziali statiche (disabilitate) come break-glass per emergenze.
4. Testare il recovery periodicamente.

### 30. OIDC è compatibile con i workflow matrix?

Si. Ogni job nella matrix riceve il proprio JWT con i claims corretti. Ogni job può autenticarsi verso un ruolo diverso:

```yaml
strategy:
  matrix:
    env: [dev, staging, production]
    include:
      - env: dev
        role: arn:aws:iam::111:role/github-dev
      - env: staging
        role: arn:aws:iam::222:role/github-staging
      - env: production
        role: arn:aws:iam::333:role/github-prod
environment: ${{ matrix.env }}
```

### 31. Posso limitare quali utenti possono triggerare workflow OIDC?

Indirettamente. OIDC non filtra per utente, ma puoi:
1. Usare branch protection per limitare chi può pushare a `main`.
2. Usare environment protection con designated reviewers.
3. Il claim `actor` nel JWT contiene lo username — usabile in Vault `bound_claims`.

### 32. Qual è la differenza tra `workflow_ref` e `job_workflow_ref`?

| Claim | Contenuto | Uso |
|---|---|---|
| `workflow_ref` | Il file workflow del caller | Identifica il workflow top-level |
| `job_workflow_ref` | Il file workflow che contiene il job | Per reusable workflows, identifica il workflow chiamato |

Per workflow semplici (non reusable), entrambi sono identici. Per reusable workflows, `job_workflow_ref` identifica il workflow riusabile e `workflow_ref` identifica il caller.

### 33. Come monitoro l'adozione di OIDC nella mia organizzazione?

```bash
# Contare i workflow che usano OIDC vs secret statici
for repo in $(gh repo list myorg --limit 500 --json name -q '.[].name'); do
  OIDC=$(gh api "repos/myorg/$repo/contents/.github/workflows" 2>/dev/null \
    | jq -r '.[].download_url' \
    | xargs -I{} curl -sL {} 2>/dev/null \
    | grep -c 'id-token: write' || echo 0)
  STATIC=$(gh secret list --repo "myorg/$repo" 2>/dev/null \
    | grep -ciE 'AWS_ACCESS_KEY|AZURE_CREDENTIALS|GCP_SA_KEY' || echo 0)
  echo "$repo: OIDC=$OIDC, Static=$STATIC"
done
```

### 34. OIDC funziona con i GitHub App installation tokens?

No. OIDC e GitHub App tokens sono meccanismi separati. Un workflow può usare entrambi: OIDC per autenticazione cloud e un GitHub App token per operazioni API GitHub.

### 35. Posso usare OIDC con HashiCorp Boundary per accesso SSH?

Si. Configurare Vault come intermediario: OIDC autentica il workflow verso Vault, Vault genera credenziali Boundary temporanee per la sessione SSH:

```yaml
- name: Get Boundary credentials from Vault
  uses: hashicorp/vault-action@v3
  with:
    url: https://vault.mycompany.com
    method: jwt
    role: github-boundary
    jwtGithubAudience: https://vault.mycompany.com
    secrets: |
      boundary/creds/ssh-session auth_token | BOUNDARY_TOKEN
```

### 36. OIDC è compatibile con GitHub Codespaces?

No direttamente. Codespaces non espone le variabili `ACTIONS_ID_TOKEN_REQUEST_*` perché non è un contesto GitHub Actions. Per Codespaces, usare credenziali locali dell'utente o device flow.

### 37. Posso usare un solo OIDC provider per multipli issuer?

No. Ogni OIDC issuer richiede una configurazione separata:
- GitHub.com: `https://token.actions.githubusercontent.com`
- GHES: `https://ghes.mycompany.com/_services/token`
- GitLab: `https://gitlab.com`

### 38. Come prevengo l'uso non autorizzato dei ruoli OIDC da parte di nuovi repository?

Usare vincoli espliciti per repository nella trust policy. Non usare mai `repo:myorg/*` senza ulteriori restrizioni. Implementare un processo di PR-review per aggiungere nuovi repository alla trust policy:

```hcl
# Nuovi repository richiedono un merge al repository IaC
variable "authorized_repos" {
  type = list(string)
  default = [
    "api-service",
    "web-frontend",
    # Aggiungere qui con PR review
  ]
}
```

### 39. Qual è l'impatto di OIDC sulla fatturazione cloud?

Le chiamate STS sono gratuite su tutti i provider. Non ci sono costi aggiuntivi per l'uso di OIDC. I costi sono gli stessi delle operazioni effettuate con le credenziali risultanti.

### 40. Come gestisco OIDC durante un incidente di sicurezza?

Procedura di risposta:
1. **Identificare** quali ruoli OIDC sono stati potenzialmente compromessi.
2. **Isolare**: disabilitare temporaneamente il provider OIDC nel cloud o restringere la trust policy.
3. **Investigare**: analizzare CloudTrail/audit logs per uso anomalo.
4. **Contenere**: revocare tutte le sessioni attive.
5. **Rimediare**: aggiornare trust policy, ruotare secret in Vault se compromessi.
6. **Ripristinare**: riabilitare OIDC con trust policy aggiornate.
7. **Post-mortem**: documentare la catena di compromissione e le lezioni apprese.

---

## Letture consigliate

- GitHub OIDC docs — [docs.github.com/en/actions/deployment/security-hardening-your-deployments](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments)
- AWS OIDC with GitHub — [aws.amazon.com/blogs/security/use-iam-roles-to-connect-github-actions-to-actions-in-aws](https://aws.amazon.com/blogs/security/use-iam-roles-to-connect-github-actions-to-actions-in-aws/)
- Azure Federated Credentials — [learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-create-trust](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-create-trust)
- GCP Workload Identity Federation — [cloud.google.com/iam/docs/workload-identity-federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- OIDC spec — [openid.net/specs/openid-connect-core-1_0.html](https://openid.net/specs/openid-connect-core-1_0.html)
- GitHub OIDC token claims — [docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect#understanding-the-oidc-token](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- Terraform AWS OIDC module — [registry.terraform.io/modules/unfunco/oidc-github/aws](https://registry.terraform.io/modules/unfunco/oidc-github/aws)

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [16 — GitHub Security e Scanning](16-github-security-scanning.md) | Fondamenti di security scanning; OIDC elimina i secret statici rilevati dallo scanning |
| [17 — GitHub Actions: Workflow e Sintassi](17-github-actions-workflow-sintassi.md) | Sintassi `permissions: id-token: write` necessaria per richiedere il JWT |
| [19 — GitHub Actions: Ricette CI/CD](19-github-actions-ci-cd-ricette.md) | Pipeline di deploy dove OIDC sostituisce le credenziali statiche |
| [21 — Self-Hosted Runners](21-github-actions-self-hosted-runners.md) | OIDC funziona anche con runner self-hosted; trust policy diversa |
| [27 — Supply-Chain Attestation e SLSA](27-supply-chain-attestation-slsa.md) | Le attestazioni SLSA usano OIDC per la provenance firmata dal workflow |
| [28 — CodeQL e GitHub Advanced Security](28-codeql-advanced-security.md) | Secret scanning rileva credenziali statiche che OIDC rende superflue |

---

## Glossario

| Termine | Definizione |
|---|---|
| **OIDC** | OpenID Connect — protocollo di autenticazione basato su OAuth 2.0, permette a un'entità di provare la propria identità senza condividere un secret |
| **Workload Identity Federation** | Meccanismo cross-platform che permette a un workload esterno (es. GitHub Actions) di autenticarsi verso un cloud provider usando OIDC, senza secret statici |
| **JWT** | JSON Web Token — token firmato che contiene claims verificabili |
| **Claims** | Coppie chiave-valore nel payload del JWT che descrivono il soggetto e il contesto (es. `sub`, `aud`, `iss`) |
| **`sub` (subject)** | Claim che identifica chi sta richiedendo il token. In GitHub Actions: `repo:ORG/REPO:ref:refs/heads/BRANCH` |
| **`aud` (audience)** | Claim che identifica il destinatario previsto del token (es. `sts.amazonaws.com`) |
| **`iss` (issuer)** | Claim che identifica chi ha emesso il token: `https://token.actions.githubusercontent.com` |
| **`id-token: write`** | Permission del workflow necessaria per richiedere un JWT OIDC dall'API interna di GitHub |
| **Trust policy** | Policy IAM (AWS) che definisce chi può assumere un ruolo — in OIDC, condizionata ai claims del JWT |
| **Federated credential** | Configurazione Azure AD che lega un'app registration a un issuer OIDC esterno e a un subject specifico |
| **Workload Identity Pool** | Container GCP che raggruppa identity provider esterni per la federazione |
| **STS** | Security Token Service — servizio del cloud provider che scambia un JWT con credenziali temporanee |
| **JWKS** | JSON Web Key Set — insieme di chiavi pubbliche usate per verificare la firma dei JWT |
| **Token exchange** | Processo di scambio di un JWT OIDC con credenziali cloud temporanee |
| **Role chaining** | Assumere un ruolo AWS usando le credenziali temporanee di un altro ruolo (cross-account) |
| **Permission boundary** | Limite massimo dei permessi applicabile a un ruolo IAM — limita anche OIDC |
| **Session name** | Identificatore della sessione STS, utile per audit trail |
| **Attribute mapping** | Mappatura tra claims OIDC e attributi interni del cloud provider (usato in GCP) |
| **Attribute condition** | Espressione booleana (GCP) che filtra quali token sono accettati dal provider |
| **Thumbprint** | Hash del certificato TLS usato per verificare l'identità dell'OIDC provider |
| **`workflow_ref`** | Claim che identifica il file workflow specifico + ref — usato per trust policy granulari |
