# Infrastruttura DevOps per SaaS — Guida Completa

## Indice

- [Panoramica](#panoramica)
- [CI/CD Pipelines per SaaS](#cicd-pipelines-per-saas)
- [Infrastructure as Code](#infrastructure-as-code)
- [Containerizzazione e Orchestrazione](#containerizzazione-e-orchestrazione)
- [Monitoring e Observability](#monitoring-e-observability)
- [Incident Management](#incident-management)
- [Database Management in Produzione](#database-management-in-produzione)
- [CDN e Edge Caching](#cdn-e-edge-caching)
- [Zero-Downtime Deployments](#zero-downtime-deployments)
- [Gestione degli Ambienti](#gestione-degli-ambienti)
- [Ottimizzazione dei Costi Cloud](#ottimizzazione-dei-costi-cloud)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

L'infrastruttura DevOps rappresenta il sistema nervoso di qualsiasi SaaS in produzione. Mentre l'architettura applicativa definisce come il software funziona, l'infrastruttura DevOps determina come viene costruito, distribuito, monitorato e mantenuto. Per un SaaS, questo è particolarmente critico: i clienti si aspettano disponibilità 24/7 (SLA tipici del 99.9%-99.99%), aggiornamenti continui senza interruzioni, performance consistenti sotto carico variabile e tempi di risposta rapidi in caso di incidenti.

Un'infrastruttura DevOps matura per SaaS copre l'intero ciclo di vita del software: dal commit del codice al monitoraggio in produzione, passando per build automatizzate, test, deploy, observability e incident response. L'obiettivo è ridurre il lead time (tempo da commit a produzione) mantenendo alta affidabilità, sicurezza e controllo dei costi.

Questa guida copre in profondità ogni componente dell'infrastruttura DevOps necessaria per operare un SaaS professionale, con esempi di codice reali, pattern architetturali collaudati e procedure operative concrete.

---

## CI/CD Pipelines per SaaS

La Continuous Integration e la Continuous Delivery/Deployment (CI/CD) sono il fondamento dell'automazione DevOps. Una pipeline CI/CD ben progettata consente deploy frequenti (anche multipli al giorno) con alta confidenza nella qualità del rilascio.

### Principi Fondamentali

| Principio | Descrizione | Impatto SaaS |
|---|---|---|
| Build once, deploy everywhere | Un singolo artefatto viene promosso tra ambienti | Coerenza tra staging e produzione |
| Fast feedback | Pipeline fallisce il prima possibile | Developer productivity alta |
| Trunk-based development | Branch di vita breve, merge frequenti | Riduce conflitti, deploy più sicuri |
| Immutable artifacts | Container images, non codice sorgente in prod | Rollback istantanei, riproducibilità |
| Pipeline as code | Pipeline definita nel repository | Versionata, reviewable, riproducibile |

### GitHub Actions — Pipeline Completa

```yaml
# .github/workflows/ci-cd.yml
name: SaaS CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  NODE_VERSION: '20'

# Evita esecuzioni concorrenti sullo stesso branch
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # ======================
  # Stage 1: Lint e Static Analysis
  # ======================
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: ESLint
        run: npx eslint . --format=json --output-file=eslint-report.json
        continue-on-error: true

      - name: TypeScript type check
        run: npx tsc --noEmit

      - name: Security audit
        run: npm audit --audit-level=high

      - name: Upload lint results
        uses: actions/upload-artifact@v4
        with:
          name: lint-results
          path: eslint-report.json

  # ======================
  # Stage 2: Unit Tests
  # ======================
  unit-tests:
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      matrix:
        shard: [1, 2, 3, 4]  # Parallelismo per velocizzare
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
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
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci

      - name: Run database migrations
        run: npx prisma migrate deploy
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_db

      - name: Run unit tests (shard ${{ matrix.shard }}/4)
        run: |
          npx jest --ci --coverage --shard=${{ matrix.shard }}/4 \
            --reporters=default --reporters=jest-junit
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
          JEST_JUNIT_OUTPUT_DIR: ./reports

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage-shard-${{ matrix.shard }}
          path: coverage/

  # ======================
  # Stage 3: Integration Tests
  # ======================
  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci

      - name: Start application stack
        run: docker compose -f docker-compose.test.yml up -d --wait

      - name: Run integration tests
        run: npx jest --config jest.integration.config.ts --ci
        env:
          API_BASE_URL: http://localhost:3000

      - name: Tear down
        if: always()
        run: docker compose -f docker-compose.test.yml down -v

  # ======================
  # Stage 4: Build e Push Image
  # ======================
  build:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build-push.outputs.digest }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
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
            type=sha,prefix=
            type=raw,value=latest

      - name: Build and push
        id: build-push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64

  # ======================
  # Stage 5: Deploy to Staging
  # ======================
  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}

      - name: Deploy to staging
        run: |
          kubectl set image deployment/api-server \
            api-server=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ needs.build.outputs.image-digest }} \
            -n staging
          kubectl rollout status deployment/api-server -n staging --timeout=300s

      - name: Run smoke tests
        run: |
          curl -sf https://staging.example.com/health || exit 1
          npm run test:smoke -- --base-url=https://staging.example.com

  # ======================
  # Stage 6: Deploy to Production
  # ======================
  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production  # Richiede approvazione manuale in GitHub
    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_PRODUCTION }}

      - name: Canary deploy (10%)
        run: |
          kubectl set image deployment/api-server-canary \
            api-server=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ needs.build.outputs.image-digest }} \
            -n production
          kubectl rollout status deployment/api-server-canary -n production --timeout=300s

      - name: Monitor canary (5 min)
        run: |
          sleep 300
          ERROR_RATE=$(curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~"5..",deployment="canary"}[5m])' | jq '.data.result[0].value[1] // "0"' -r)
          if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
            echo "Canary error rate too high: $ERROR_RATE"
            kubectl rollout undo deployment/api-server-canary -n production
            exit 1
          fi

      - name: Full rollout
        run: |
          kubectl set image deployment/api-server \
            api-server=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ needs.build.outputs.image-digest }} \
            -n production
          kubectl rollout status deployment/api-server -n production --timeout=600s

      - name: Notify team
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Deploy ${{ job.status }}: ${{ github.sha }} to production"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### GitLab CI — Pipeline Equivalente

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - test
  - build
  - deploy-staging
  - deploy-production

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  NODE_VERSION: "20"

# Template riutilizzabile per setup Node
.node-setup: &node-setup
  image: node:${NODE_VERSION}-alpine
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths:
      - node_modules/
      - .npm/
  before_script:
    - npm ci --cache .npm

lint:
  <<: *node-setup
  stage: lint
  script:
    - npx eslint . --max-warnings=0
    - npx tsc --noEmit
    - npm audit --audit-level=high
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

unit-tests:
  <<: *node-setup
  stage: test
  services:
    - postgres:16
    - redis:7-alpine
  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_pass
    DATABASE_URL: postgresql://test_user:test_pass@postgres:5432/test_db
    REDIS_URL: redis://redis:6379
  script:
    - npx prisma migrate deploy
    - npx jest --ci --coverage --forceExit
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  artifacts:
    reports:
      junit: reports/junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

build-image:
  stage: build
  image: docker:24-dind
  services:
    - docker:24-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build --cache-from $CI_REGISTRY_IMAGE:latest -t $DOCKER_IMAGE -t $CI_REGISTRY_IMAGE:latest .
    - docker push $DOCKER_IMAGE
    - docker push $CI_REGISTRY_IMAGE:latest
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy-staging:
  stage: deploy-staging
  image: bitnami/kubectl:latest
  script:
    - kubectl config use-context staging
    - kubectl set image deployment/api-server api-server=$DOCKER_IMAGE -n staging
    - kubectl rollout status deployment/api-server -n staging --timeout=300s
    - curl -sf https://staging.example.com/health
  environment:
    name: staging
    url: https://staging.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy-production:
  stage: deploy-production
  image: bitnami/kubectl:latest
  script:
    - kubectl config use-context production
    - kubectl set image deployment/api-server api-server=$DOCKER_IMAGE -n production
    - kubectl rollout status deployment/api-server -n production --timeout=600s
  environment:
    name: production
    url: https://app.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual  # Approvazione manuale per produzione
```

### Confronto Pipeline CI/CD

| Caratteristica | GitHub Actions | GitLab CI | CircleCI |
|---|---|---|---|
| Costo iniziale | Gratis per repo pubblici | 400 min/mese gratis | 6000 min/mese gratis |
| Runner self-hosted | Supportato | Supportato | Limitato |
| Cache nativi | GitHub Cache | Cache artifacts | Layer caching |
| Secrets management | Repository/Org secrets | CI/CD variables | Contexts |
| Approvazioni deploy | Environments | Manual jobs | Approval jobs |
| Marketplace plugins | 20.000+ Actions | Templates limitati | Orbs ecosystem |
| Parallelismo | Matrix strategy | parallel keyword | Parallelism native |

---

## Infrastructure as Code

L'Infrastructure as Code (IaC) consente di definire, versionare e gestire l'infrastruttura cloud con gli stessi strumenti e processi usati per il codice applicativo. Per un SaaS, IaC garantisce riproducibilità (ogni ambiente identico), auditabilità (ogni modifica tracciata in git) e velocità (nuovi ambienti in minuti, non giorni).

### Terraform — Infrastruttura AWS per SaaS

```hcl
# terraform/environments/production/main.tf

terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "myapp-terraform-state"
    key            = "production/terraform.tfstate"
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
      ManagedBy   = "terraform"
      Project     = "myapp-saas"
    }
  }
}

# ======================
# Networking — VPC
# ======================
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.5.0"

  name = "${var.project}-${var.environment}"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = var.environment != "production"
  enable_dns_hostnames   = true
  enable_dns_support     = true

  # Flow logs per debug networking
  enable_flow_log                      = true
  create_flow_log_cloudwatch_log_group = true
  create_flow_log_iam_role             = true
}

# ======================
# Database — RDS PostgreSQL
# ======================
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "6.4.0"

  identifier = "${var.project}-${var.environment}"

  engine               = "postgres"
  engine_version       = "16.2"
  family               = "postgres16"
  major_engine_version = "16"
  instance_class       = var.environment == "production" ? "db.r6g.xlarge" : "db.t4g.medium"

  allocated_storage     = 100
  max_allocated_storage = 500  # Autoscaling storage

  db_name  = "myapp"
  username = "myapp_admin"
  port     = 5432

  # Multi-AZ per produzione
  multi_az = var.environment == "production"

  # Subnet e security
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [module.rds_sg.security_group_id]

  # Backup
  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # Performance Insights
  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  # Read replica per produzione
  create_db_instance = true

  # Encryption
  storage_encrypted = true

  # Deletion protection in produzione
  deletion_protection = var.environment == "production"

  parameters = [
    {
      name  = "shared_preload_libraries"
      value = "pg_stat_statements,auto_explain"
    },
    {
      name  = "log_min_duration_statement"
      value = "1000"  # Log query > 1s
    },
    {
      name  = "max_connections"
      value = "200"
    }
  ]
}

# Read Replica (solo produzione)
resource "aws_db_instance" "read_replica" {
  count = var.environment == "production" ? 1 : 0

  identifier          = "${var.project}-${var.environment}-replica"
  replicate_source_db = module.rds.db_instance_identifier
  instance_class      = "db.r6g.large"

  performance_insights_enabled = true
  storage_encrypted           = true

  tags = {
    Role = "read-replica"
  }
}

# ======================
# EKS Cluster
# ======================
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.0"

  cluster_name    = "${var.project}-${var.environment}"
  cluster_version = "1.29"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    # Node group per workload generali
    general = {
      desired_size = var.environment == "production" ? 3 : 1
      min_size     = var.environment == "production" ? 2 : 1
      max_size     = var.environment == "production" ? 10 : 3

      instance_types = ["m6i.xlarge"]
      capacity_type  = "ON_DEMAND"

      labels = {
        workload = "general"
      }
    }

    # Spot instances per workload tolleranti a interruzioni
    spot = {
      desired_size = var.environment == "production" ? 2 : 0
      min_size     = 0
      max_size     = 20

      instance_types = ["m6i.xlarge", "m5.xlarge", "m5a.xlarge"]
      capacity_type  = "SPOT"

      labels = {
        workload = "spot-tolerant"
      }

      taints = [{
        key    = "spot"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
    }
  }

  # Addons
  cluster_addons = {
    coredns = { most_recent = true }
    kube-proxy = { most_recent = true }
    vpc-cni = { most_recent = true }
    aws-ebs-csi-driver = { most_recent = true }
  }
}

# ======================
# ElastiCache — Redis
# ======================
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.project}-${var.environment}"
  description                = "Redis cluster per ${var.project}"

  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.environment == "production" ? "cache.r6g.large" : "cache.t4g.micro"
  num_cache_clusters   = var.environment == "production" ? 3 : 1

  automatic_failover_enabled = var.environment == "production"
  multi_az_enabled          = var.environment == "production"

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [module.redis_sg.security_group_id]

  snapshot_retention_limit = var.environment == "production" ? 7 : 1
  snapshot_window         = "05:00-06:00"

  parameter_group_name = aws_elasticache_parameter_group.redis.name
}

# ======================
# CloudFront CDN
# ======================
resource "aws_cloudfront_distribution" "cdn" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"  # Solo edge locations in EU/NA

  aliases = [var.domain_name, "www.${var.domain_name}"]

  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "api"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  origin {
    domain_name = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id   = "static"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.oai.cloudfront_access_identity_path
    }
  }

  # Cache behavior per API (no cache)
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "api"

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Accept", "Origin"]
      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "https-only"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
  }

  # Default: static assets con cache aggressiva
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "static"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400     # 1 giorno
    max_ttl                = 31536000  # 1 anno
    compress               = true
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.main.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
}

# ======================
# Outputs
# ======================
output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  value     = module.rds.db_instance_endpoint
  sensitive = true
}

output "redis_endpoint" {
  value     = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive = true
}

output "cdn_domain" {
  value = aws_cloudfront_distribution.cdn.domain_name
}
```

### Terraform — Infrastruttura GCP per SaaS

```hcl
# terraform/environments/production/gcp-main.tf

terraform {
  required_version = ">= 1.7"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "myapp-terraform-state"
    prefix = "production"
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# GKE Cluster
resource "google_container_cluster" "primary" {
  name     = "${var.project}-${var.environment}"
  location = var.gcp_region

  # Autopilot mode: Google gestisce i nodi
  enable_autopilot = true

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.private.id

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block = "172.16.0.0/28"
  }

  release_channel {
    channel = "REGULAR"
  }
}

# Cloud SQL PostgreSQL
resource "google_sql_database_instance" "main" {
  name             = "${var.project}-${var.environment}"
  database_version = "POSTGRES_16"
  region           = var.gcp_region

  settings {
    tier              = var.environment == "production" ? "db-custom-4-16384" : "db-f1-micro"
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"

    disk_size         = 100
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "03:00"
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 4096
      record_application_tags = true
      record_client_address   = true
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"
    }
  }

  deletion_protection = var.environment == "production"
}

# Cloud Memorystore (Redis)
resource "google_redis_instance" "cache" {
  name           = "${var.project}-${var.environment}"
  tier           = var.environment == "production" ? "STANDARD_HA" : "BASIC"
  memory_size_gb = var.environment == "production" ? 4 : 1
  region         = var.gcp_region

  authorized_network = google_compute_network.vpc.id

  redis_version = "REDIS_7_0"

  transit_encryption_mode = "SERVER_AUTHENTICATION"
}
```

### Struttura Terraform Raccomandata

```
terraform/
  modules/           # Moduli riutilizzabili
    vpc/
    rds/
    eks/
    redis/
    monitoring/
  environments/
    dev/
      main.tf
      variables.tf
      terraform.tfvars
    staging/
      main.tf
      variables.tf
      terraform.tfvars
    production/
      main.tf
      variables.tf
      terraform.tfvars
```

---

## Containerizzazione e Orchestrazione

I container sono lo standard de facto per il packaging e il deploy di applicazioni SaaS. Docker fornisce il formato container, Kubernetes fornisce l'orchestrazione: scheduling, scaling, self-healing, service discovery e load balancing.

### Dockerfile Ottimizzato per SaaS (Multi-Stage)

```dockerfile
# Dockerfile
# Stage 1: Dependencies
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
# Rimuovi devDependencies
RUN npm prune --production

# Stage 3: Production image
FROM node:20-alpine AS runner
WORKDIR /app

# Security: non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 appuser

# Copia solo il necessario
COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

USER appuser
EXPOSE 3000

# Segnali di terminazione gestiti correttamente
CMD ["node", "--enable-source-maps", "dist/server.js"]
```

### Kubernetes Manifests per SaaS

```yaml
# k8s/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  labels:
    app: api-server
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Zero-downtime
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: api-server
      terminationGracePeriodSeconds: 60
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001

      containers:
        - name: api-server
          image: ghcr.io/myorg/myapp:latest
          ports:
            - containerPort: 3000
              name: http
            - containerPort: 9090
              name: metrics

          env:
            - name: NODE_ENV
              value: "production"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: url
            - name: LOG_LEVEL
              value: "info"
            - name: LOG_FORMAT
              value: "json"

          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"

          readinessProbe:
            httpGet:
              path: /health/ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 3

          livenessProbe:
            httpGet:
              path: /health/live
              port: 3000
            initialDelaySeconds: 15
            periodSeconds: 20
            failureThreshold: 3

          startupProbe:
            httpGet:
              path: /health/live
              port: 3000
            failureThreshold: 30
            periodSeconds: 2

          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 10"]

      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: api-server
---
# k8s/base/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-server
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 3
  maxReplicas: 50
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Evita flapping
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "100"
---
# k8s/base/pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-server
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: api-server
---
# k8s/base/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api-server
spec:
  type: ClusterIP
  selector:
    app: api-server
  ports:
    - port: 80
      targetPort: 3000
      name: http
    - port: 9090
      targetPort: 9090
      name: metrics
```

---

## Monitoring e Observability

L'observability per un SaaS è costruita su tre pilastri: **metriche** (numeri aggregati nel tempo), **log** (eventi discreti) e **trace** (percorso di una richiesta attraverso i servizi). Senza observability, si opera alla cieca: non si sa se il sistema funziona, dove sono i colli di bottiglia, o perché un cliente ha avuto un problema.

### I Tre Pilastri dell'Observability

| Pilastro | Strumenti | Cosa risponde |
|---|---|---|
| Metriche | Prometheus, Datadog, CloudWatch | "Quante richieste? Qual è la latenza p99? Quanta CPU?" |
| Log | ELK Stack, Loki, CloudWatch Logs | "Cosa è successo esattamente alle 14:32?" |
| Trace | Jaeger, Zipkin, AWS X-Ray | "Perché questa richiesta ha impiegato 5 secondi?" |

### Prometheus + Grafana — Configurazione

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerts/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port, __meta_kubernetes_pod_ip]
        action: replace
        target_label: __address__
        regex: (.+);(.+)
        replacement: $2:$1

  - job_name: 'node-exporter'
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
```

```yaml
# prometheus/alerts/saas-alerts.yml
groups:
  - name: saas-sla
    rules:
      # Errore rate > 1% per 5 minuti
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          /
          sum(rate(http_requests_total[5m]))
          > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate superiore all'1%"
          description: "Error rate attuale: {{ $value | humanizePercentage }}"
          runbook_url: "https://wiki.internal/runbooks/high-error-rate"

      # Latenza p99 > 2 secondi
      - alert: HighLatency
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Latenza p99 superiore a 2 secondi"
          description: "p99 attuale: {{ $value }}s"

      # Database connection pool esaurito
      - alert: DBConnectionPoolExhausted
        expr: |
          pg_stat_activity_count / pg_settings_max_connections > 0.85
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Connection pool database quasi esaurito (>85%)"

      # Disk space
      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.15
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Spazio disco sotto il 15%"

      # Pod restart loop
      - alert: PodCrashLooping
        expr: |
          rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pod {{ $labels.pod }} in crash loop"
```

### Structured Logging

```typescript
// src/lib/logger.ts
import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  base: {
    service: process.env.SERVICE_NAME || 'api-server',
    version: process.env.APP_VERSION || 'unknown',
    environment: process.env.NODE_ENV || 'development',
  },
  // Redact sensitive fields
  redact: {
    paths: ['req.headers.authorization', 'req.headers.cookie', 'password', 'token', 'secret'],
    censor: '[REDACTED]',
  },
  timestamp: pino.stdTimeFunctions.isoTime,
});

// Middleware Express per request logging
export function requestLogger() {
  return (req: Request, res: Response, next: NextFunction) => {
    const requestId = req.headers['x-request-id'] || crypto.randomUUID();
    const start = process.hrtime.bigint();

    // Attach logger con context al request
    req.log = logger.child({
      requestId,
      tenantId: req.tenantId,
      userId: req.userId,
      method: req.method,
      path: req.path,
      userAgent: req.headers['user-agent'],
      ip: req.ip,
    });

    res.setHeader('x-request-id', requestId);

    res.on('finish', () => {
      const duration = Number(process.hrtime.bigint() - start) / 1e6; // ms
      const logData = {
        statusCode: res.statusCode,
        duration,
        contentLength: res.getHeader('content-length'),
      };

      if (res.statusCode >= 500) {
        req.log.error(logData, 'Request completed with server error');
      } else if (res.statusCode >= 400) {
        req.log.warn(logData, 'Request completed with client error');
      } else {
        req.log.info(logData, 'Request completed');
      }
    });

    next();
  };
}
```

### Distributed Tracing con OpenTelemetry

```typescript
// src/instrumentation.ts
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-grpc';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { Resource } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';

const sdk = new NodeSDK({
  resource: new Resource({
    [ATTR_SERVICE_NAME]: process.env.SERVICE_NAME || 'api-server',
    [ATTR_SERVICE_VERSION]: process.env.APP_VERSION || '0.0.0',
    'deployment.environment': process.env.NODE_ENV || 'development',
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4317',
  }),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4317',
    }),
    exportIntervalMillis: 30000,
  }),
  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-http': {
        ignoreIncomingPaths: ['/health', '/metrics'],
      },
      '@opentelemetry/instrumentation-pg': { enabled: true },
      '@opentelemetry/instrumentation-redis': { enabled: true },
    }),
  ],
});

sdk.start();
process.on('SIGTERM', () => sdk.shutdown());
```

### Dashboard SaaS — Metriche Chiave

| Metrica | Query Prometheus | Target SaaS tipico |
|---|---|---|
| Request rate | `sum(rate(http_requests_total[5m]))` | Baseline + trend |
| Error rate | `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` | < 0.1% |
| Latenza p50 | `histogram_quantile(0.5, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))` | < 100ms |
| Latenza p99 | `histogram_quantile(0.99, ...)` | < 1s |
| Apdex score | Custom formula basata su soglie | > 0.95 |
| Active users | `sum(saas_active_sessions)` | Trend |
| DB connections | `pg_stat_activity_count` | < 80% max |
| Memory usage | `container_memory_usage_bytes` | < 80% limit |
| CPU usage | `rate(container_cpu_usage_seconds_total[5m])` | < 70% limit |

---

## Incident Management

La gestione degli incidenti è il processo che determina quanto velocemente un SaaS si riprende dai problemi. Per un SaaS con SLA del 99.9%, il budget di downtime annuale è di circa 8.7 ore. Ogni minuto conta.

### Severity Levels

| Severity | Descrizione | Response Time | Esempio |
|---|---|---|---|
| SEV1 - Critical | Servizio completamente down per tutti i clienti | 5 minuti | Database irraggiungibile, deploy corrotto |
| SEV2 - Major | Funzionalità critica degradata per molti clienti | 15 minuti | Pagamenti falliscono, latenza >10s |
| SEV3 - Minor | Funzionalità non critica degradata per alcuni clienti | 1 ora | Export CSV fallisce, notifiche ritardate |
| SEV4 - Low | Problema minore senza impatto su clienti | Business hours | Bug UI non bloccante, log warning anomalo |

### Runbook Template

```markdown
# Runbook: High Error Rate (>1%)

## Symptom
Alert: HighErrorRate - Error rate superiore all'1% per 5+ minuti

## Quick Diagnosis (< 2 minuti)
1. Controlla la dashboard principale: https://grafana.internal/d/saas-overview
2. Identifica il servizio con errori:
   kubectl get pods -n production --field-selector status.phase!=Running
   kubectl top pods -n production --sort-by=cpu
3. Controlla i log recenti:
   kubectl logs -n production -l app=api-server --tail=100 --since=5m | grep ERROR
4. Controlla se c'è stato un deploy recente:
   kubectl rollout history deployment/api-server -n production

## Common Causes & Fixes

### Causa 1: Deploy difettoso
  # Rollback immediato
  kubectl rollout undo deployment/api-server -n production
  kubectl rollout status deployment/api-server -n production

### Causa 2: Database overloaded
  # Controlla connessioni attive
  psql $DATABASE_URL -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

  # Kill query lunghe (>60s)
  psql $DATABASE_URL -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '60 seconds';"

### Causa 3: Dependency esterna down
  # Controlla connettività
  curl -sf https://api.stripe.com/v1/charges -H "Authorization: Bearer sk_test" || echo "Stripe unreachable"

## Escalation
- Se non risolto in 15 minuti: escalare a on-call senior
- Se non risolto in 30 minuti: escalare a engineering manager
```

### On-Call Rotation

```yaml
# pagerduty-config (concettuale)
schedules:
  primary-oncall:
    rotation_type: weekly
    participants:
      - team: backend-engineers
        rotation_virtual_start: "2024-01-01T09:00:00+01:00"
    restrictions:
      - type: daily_restriction
        start_time_of_day: "09:00:00"
        duration_seconds: 57600  # 16 ore (09:00-01:00)

  secondary-oncall:
    rotation_type: weekly
    participants:
      - team: senior-engineers
    # Backup per SEV1 quando primary non risponde in 5 min

escalation_policies:
  production:
    rules:
      - targets: [primary-oncall]
        escalation_delay_in_minutes: 5
      - targets: [secondary-oncall]
        escalation_delay_in_minutes: 10
      - targets: [engineering-manager]
        escalation_delay_in_minutes: 15
```

### Template Postmortem

Un postmortem è un documento scritto dopo ogni incidente SEV1/SEV2 per imparare dall'errore e prevenire che si ripeta. È blameless: non cerca colpevoli, ma cause sistemiche.

```markdown
# Postmortem: [Titolo incidente]

**Data incidente**: YYYY-MM-DD
**Durata**: HH:MM - HH:MM (XX minuti)
**Severity**: SEV1/SEV2
**Autore**: [Nome]
**Stato**: Draft / In Review / Completed

## Sommario
[1-2 frasi che descrivono cosa è successo e l'impatto]

## Impatto
- Clienti impattati: XXX (YY% del totale)
- Revenue persa stimata: EUR XXX
- SLA impattato: 99.XX% -> 99.XX% (mese corrente)

## Timeline (UTC)
| Ora | Evento |
|---|---|
| 14:00 | Deploy v2.3.1 completato |
| 14:05 | Alert HighErrorRate triggered |
| 14:07 | On-call acknowledges |
| 14:12 | Root cause identificata: migration difettosa |
| 14:15 | Rollback deployment avviato |
| 14:18 | Servizio ripristinato |
| 14:30 | Conferma stabilità |

## Root Cause
[Descrizione tecnica della causa radice]

## Contributing Factors
- [Fattore 1 che ha contribuito all'incidente]
- [Fattore 2]

## Cosa ha funzionato bene
- Alert triggato in tempo
- Runbook aggiornato e utilizzato
- Rollback rapido

## Cosa non ha funzionato
- Migration non testata con volume dati reale
- Smoke test post-deploy non copriva questa funzionalità

## Action Items
| Azione | Owner | Priorità | Deadline | Stato |
|---|---|---|---|---|
| Aggiungere test migration con snapshot prod | @dev1 | P1 | 2024-02-01 | Open |
| Espandere smoke test post-deploy | @dev2 | P1 | 2024-02-01 | Open |
| Documentare procedura rollback migration | @dev1 | P2 | 2024-02-15 | Open |
```

---

## Database Management in Produzione

La gestione del database in produzione è una delle attività più critiche e rischiose per un SaaS. Un errore qui può causare data loss, downtime o corruzione dei dati dei clienti.

### Migration Strategy

```typescript
// migrations/20240115_001_add_invoice_status.ts
import { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  // 1. Aggiungere colonna nullable (non-breaking, nessun lock)
  await knex.schema.alterTable('invoices', (table) => {
    table.string('status', 20).nullable().defaultTo(null);
    table.index('status', 'idx_invoices_status');
  });

  // 2. Backfill in batch (non blocca la tabella)
  let lastId = 0;
  const BATCH_SIZE = 1000;

  while (true) {
    const rows = await knex('invoices')
      .where('id', '>', lastId)
      .whereNull('status')
      .orderBy('id')
      .limit(BATCH_SIZE)
      .select('id');

    if (rows.length === 0) break;

    await knex('invoices')
      .whereIn('id', rows.map(r => r.id))
      .update({ status: 'active' });

    lastId = rows[rows.length - 1].id;

    // Pausa per non sovraccaricare il DB
    await new Promise(resolve => setTimeout(resolve, 100));
  }
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.alterTable('invoices', (table) => {
    table.dropIndex('status', 'idx_invoices_status');
    table.dropColumn('status');
  });
}
```

### Pattern: Expand-Contract Migration

Le migration su database in produzione seguono il pattern expand-contract per evitare downtime:

1. **Expand**: Aggiungi nuova colonna/tabella (backward compatible)
2. **Migrate code**: Aggiorna il codice per scrivere sia nella vecchia che nella nuova struttura
3. **Backfill**: Popola i dati esistenti nella nuova struttura
4. **Switch**: Aggiorna il codice per leggere dalla nuova struttura
5. **Contract**: Rimuovi la vecchia colonna/tabella

```
Deploy 1: ALTER TABLE ADD COLUMN new_status VARCHAR(20);   -- Expand
Deploy 2: Codice scrive in entrambe le colonne              -- Dual write
Deploy 3: Script backfill per dati esistenti                 -- Backfill
Deploy 4: Codice legge da new_status                         -- Switch
Deploy 5: ALTER TABLE DROP COLUMN old_status;                -- Contract
```

### Backup Strategy

| Tipo | Frequenza | Retention | RPO | RTO |
|---|---|---|---|---|
| Snapshot completo | Giornaliero | 30 giorni | 24h | 1-4h |
| WAL/Binlog continuo | Continuo (streaming) | 7 giorni | Minuti | 30min-1h |
| Logical dump | Settimanale | 90 giorni | 7 giorni | 4-8h |
| Cross-region copy | Giornaliero | 14 giorni | 24h | 2-4h (DR) |

```bash
#!/bin/bash
# scripts/backup-verify.sh
# Verifica settimanale che i backup siano ripristinabili

set -euo pipefail

BACKUP_DATE=$(date -d "yesterday" +%Y-%m-%d)
RESTORE_INSTANCE="backup-verify-$(date +%s)"

echo "Verifico backup del $BACKUP_DATE..."

# 1. Ripristina in istanza temporanea
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier myapp-production \
  --target-db-instance-identifier "$RESTORE_INSTANCE" \
  --restore-time "${BACKUP_DATE}T23:59:59Z" \
  --db-instance-class db.t4g.medium \
  --no-multi-az \
  --no-publicly-accessible

echo "Attendo che l'istanza sia disponibile..."
aws rds wait db-instance-available \
  --db-instance-identifier "$RESTORE_INSTANCE"

# 2. Verifica integrità
ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier "$RESTORE_INSTANCE" \
  --query 'DBInstances[0].Endpoint.Address' --output text)

TABLES=$(psql "postgresql://admin:${DB_PASS}@${ENDPOINT}:5432/myapp" \
  -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")

USERS=$(psql "postgresql://admin:${DB_PASS}@${ENDPOINT}:5432/myapp" \
  -t -c "SELECT count(*) FROM users;")

echo "Tabelle trovate: $TABLES"
echo "Utenti trovati: $USERS"

# 3. Cleanup
aws rds delete-db-instance \
  --db-instance-identifier "$RESTORE_INSTANCE" \
  --skip-final-snapshot

echo "Verifica backup completata con successo"
```

### Connection Pooling

Il connection pooling è essenziale per SaaS ad alto traffico. Ogni connessione PostgreSQL consuma circa 5-10 MB di RAM; senza pooling, 1000 worker = 1000 connessioni = 5-10 GB solo per le connessioni.

```ini
# pgbouncer.ini
[databases]
myapp = host=rds-endpoint.amazonaws.com port=5432 dbname=myapp

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# Pool mode: transaction è il migliore per SaaS
# (connessione restituita al pool dopo ogni transazione)
pool_mode = transaction

# Dimensionamento pool
default_pool_size = 25       # Connessioni per database
max_client_conn = 1000       # Max connessioni client totali
reserve_pool_size = 5        # Connessioni extra per picchi
reserve_pool_timeout = 3     # Secondi prima di usare reserve

# Timeouts
server_idle_timeout = 600    # Chiudi connessioni idle dopo 10 min
client_idle_timeout = 0      # Non chiudere client idle
query_timeout = 30           # Timeout query (secondi)
client_login_timeout = 60

# Logging
log_connections = 0
log_disconnections = 0
log_pooler_errors = 1
stats_period = 60
```

---

## CDN e Edge Caching

Una CDN (Content Delivery Network) è essenziale per qualsiasi SaaS con utenti distribuiti geograficamente. Riduce la latenza servendo contenuti da edge locations vicine all'utente, riduce il carico sui server di origine e migliora la resilienza.

### Strategia di Caching per SaaS

| Tipo di contenuto | TTL | Cache-Control Header | CDN Cache |
|---|---|---|---|
| Static assets (JS, CSS, images) | 1 anno | `public, max-age=31536000, immutable` | Si (con hash nel filename) |
| HTML pages | 0 | `no-cache, no-store` | No |
| API responses (pubbliche) | 1-5 min | `public, max-age=60, s-maxage=300` | Si |
| API responses (private/auth) | 0 | `private, no-store` | No |
| Fonts | 1 anno | `public, max-age=31536000, immutable` | Si |
| User uploads (S3) | 1 giorno | `public, max-age=86400` | Si |

```typescript
// src/middleware/cache-control.ts
export function cacheControl() {
  return (req: Request, res: Response, next: NextFunction) => {
    // API endpoints autenticati: mai cacheare
    if (req.path.startsWith('/api/') && req.headers.authorization) {
      res.setHeader('Cache-Control', 'private, no-store');
      res.setHeader('Vary', 'Authorization');
      return next();
    }

    // API pubbliche: cache breve con stale-while-revalidate
    if (req.path.startsWith('/api/public/')) {
      res.setHeader('Cache-Control', 'public, max-age=60, s-maxage=300, stale-while-revalidate=600');
      return next();
    }

    // Static assets con hash: cache aggressiva
    if (req.path.match(/\.[a-f0-9]{8,}\.(js|css|png|jpg|svg|woff2)$/)) {
      res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
      return next();
    }

    // Default: no cache
    res.setHeader('Cache-Control', 'no-cache');
    next();
  };
}
```

---

## Zero-Downtime Deployments

Per un SaaS, ogni deploy deve avvenire senza interruzioni per i clienti. Esistono diverse strategie, ciascuna con trade-off specifici.

### Confronto Strategie di Deploy

| Strategia | Complessità | Rollback | Rischio | Risorse extra | Ideale per |
|---|---|---|---|---|---|
| Rolling update | Bassa | Medio (rollback graduale) | Medio | Minime (+1 pod) | Maggior parte dei SaaS |
| Blue-Green | Media | Istantaneo (switch DNS/LB) | Basso | Doppie (2x infra) | SaaS enterprise con SLA alti |
| Canary | Alta | Rapido (stop canary) | Molto basso | Minime (+10% pods) | SaaS ad alto traffico |
| Feature flags | Media | Istantaneo (toggle flag) | Molto basso | Nessuna | Rilascio graduale funzionalità |

### Blue-Green Deployment con Kubernetes

```yaml
# k8s/blue-green/blue-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server-blue
  labels:
    app: api-server
    slot: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-server
      slot: blue
  template:
    metadata:
      labels:
        app: api-server
        slot: blue
    spec:
      containers:
        - name: api-server
          image: ghcr.io/myorg/myapp:v2.3.0
          ports:
            - containerPort: 3000
---
# k8s/blue-green/green-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server-green
  labels:
    app: api-server
    slot: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-server
      slot: green
  template:
    metadata:
      labels:
        app: api-server
        slot: green
    spec:
      containers:
        - name: api-server
          image: ghcr.io/myorg/myapp:v2.4.0  # Nuova versione
          ports:
            - containerPort: 3000
---
# Il Service punta al "slot" attivo
# Per switchare: cambiare il selector da blue a green
apiVersion: v1
kind: Service
metadata:
  name: api-server
spec:
  selector:
    app: api-server
    slot: blue  # <-- Cambiare a "green" per switch
  ports:
    - port: 80
      targetPort: 3000
```

```bash
#!/bin/bash
# scripts/blue-green-switch.sh
set -euo pipefail

CURRENT_SLOT=$(kubectl get svc api-server -n production -o jsonpath='{.spec.selector.slot}')
NEW_SLOT=$([[ "$CURRENT_SLOT" == "blue" ]] && echo "green" || echo "blue")

echo "Current: $CURRENT_SLOT -> New: $NEW_SLOT"

# 1. Deploy nuova versione nel slot inattivo
kubectl set image "deployment/api-server-${NEW_SLOT}" \
  api-server="$NEW_IMAGE" -n production
kubectl rollout status "deployment/api-server-${NEW_SLOT}" -n production --timeout=300s

# 2. Smoke test sul slot inattivo (via port-forward o service interno)
kubectl port-forward "deployment/api-server-${NEW_SLOT}" 8080:3000 -n production &
PF_PID=$!
sleep 3
curl -sf http://localhost:8080/health || { kill $PF_PID; echo "Smoke test failed"; exit 1; }
kill $PF_PID

# 3. Switch traffico
kubectl patch svc api-server -n production \
  -p "{\"spec\":{\"selector\":{\"slot\":\"${NEW_SLOT}\"}}}"

echo "Switch completato: traffico ora su $NEW_SLOT"
echo "Per rollback: kubectl patch svc api-server -n production -p '{\"spec\":{\"selector\":{\"slot\":\"$CURRENT_SLOT\"}}}'"
```

### Canary Deployment con Istio

```yaml
# k8s/canary/virtual-service.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: api-server
spec:
  hosts:
    - api-server
  http:
    - route:
        - destination:
            host: api-server
            subset: stable
          weight: 90
        - destination:
            host: api-server
            subset: canary
          weight: 10
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: api-server
spec:
  host: api-server
  subsets:
    - name: stable
      labels:
        version: v2.3.0
    - name: canary
      labels:
        version: v2.4.0
```

---

## Gestione degli Ambienti

Una corretta separazione degli ambienti è fondamentale per la qualità del software e la sicurezza dei dati. Ogni SaaS dovrebbe avere almeno tre ambienti: development, staging e production.

### Matrice Ambienti

| Aspetto | Development | Staging | Production |
|---|---|---|---|
| Scopo | Sviluppo e test rapidi | Pre-produzione, QA finale | Clienti reali |
| Dati | Fixture/seed sintetici | Snapshot anonimizzato da prod | Dati reali clienti |
| Infra sizing | Minimo (1 replica, small instances) | Simile a prod (ridotto) | Full scale |
| Deploy | Automatico su push a develop | Automatico su push a main | Manuale/approvazione |
| Accesso | Tutti gli sviluppatori | Team QA + lead developers | Solo team operations |
| Monitoring | Basic (log locali) | Completo (simile a prod) | Completo + alerting |
| SSL | Self-signed o Let's Encrypt | Let's Encrypt | Certificate manager |
| DNS | dev.internal.example.com | staging.example.com | app.example.com |
| Costo mensile tipico | $50-200 | $200-1000 | $2000+ |

### Gestione Configurazione per Ambiente

```yaml
# k8s/overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: production

resources:
  - ../../base

patches:
  - target:
      kind: Deployment
      name: api-server
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
      - op: replace
        path: /spec/template/spec/containers/0/resources/requests/cpu
        value: "500m"
      - op: replace
        path: /spec/template/spec/containers/0/resources/requests/memory
        value: "1Gi"
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/cpu
        value: "2000m"
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/memory
        value: "2Gi"

configMapGenerator:
  - name: app-config
    behavior: merge
    literals:
      - LOG_LEVEL=info
      - LOG_FORMAT=json
      - RATE_LIMIT_MAX=100
      - CACHE_TTL=300
```

### Data Anonymization per Staging

```sql
-- scripts/anonymize-staging-data.sql
-- Da eseguire dopo il restore di un dump produzione in staging

BEGIN;

-- Anonimizza email utenti
UPDATE users SET
  email = 'user_' || id || '@staging.example.com',
  first_name = 'Test',
  last_name = 'User_' || id,
  phone = '+39000000' || lpad(id::text, 4, '0');

-- Rimuovi dati sensibili
UPDATE payment_methods SET
  card_last_four = '0000',
  stripe_customer_id = 'cus_staging_' || id;

-- Invalida tutti i token/sessioni
TRUNCATE TABLE sessions;
TRUNCATE TABLE api_keys;
TRUNCATE TABLE password_reset_tokens;

-- Reset webhook URLs (non inviare a endpoint reali dei clienti)
UPDATE webhooks SET
  url = 'https://httpbin.org/post',
  secret = 'staging_secret';

COMMIT;
```

---

## Ottimizzazione dei Costi Cloud

Per un SaaS, l'infrastruttura cloud è spesso la seconda voce di costo dopo gli stipendi. Ottimizzare i costi senza sacrificare performance e affidabilità è un'abilità critica.

### Framework di Ottimizzazione

| Strategia | Risparmio tipico | Complessità | Rischio |
|---|---|---|---|
| Right-sizing instances | 20-40% | Bassa | Basso |
| Reserved/Committed Use | 30-60% | Bassa | Medio (commitment) |
| Spot/Preemptible instances | 60-90% | Media | Alto (interruzioni) |
| Auto-scaling aggressivo | 20-40% | Media | Medio |
| Storage tiering | 30-50% su storage | Bassa | Basso |
| CDN per offload | 10-30% su compute | Bassa | Basso |
| Regione più economica | 10-30% | Bassa | Basso (latenza) |
| ARM instances (Graviton) | 20-30% | Media | Basso |

### Esempio: Costo Mensile Tipico SaaS (10k utenti)

```
Componente                       On-Demand    Ottimizzato    Risparmio
-------------------------------------------------------------------
EKS/GKE cluster (control plane)    $73          $73              -
Compute (3x m6i.xlarge)           $432         $173 (RI 1yr)   60%
Spot instances (background jobs)   $288         $86 (spot)      70%
RDS PostgreSQL (r6g.xlarge, HA)   $548         $329 (RI 1yr)   40%
ElastiCache Redis (r6g.large)     $230         $138 (RI 1yr)   40%
S3 storage (500 GB)                $12          $8 (IA tier)   33%
CloudFront (1 TB transfer)        $85          $85               -
NAT Gateway                       $100         $100              -
ALB                                $25          $25              -
Monitoring (Datadog/Grafana)      $200         $200              -
-------------------------------------------------------------------
TOTALE                           $1,993       $1,217           39%
```

### Tagging Strategy per Cost Allocation

```hcl
# terraform/modules/tags/main.tf
variable "required_tags" {
  type = map(string)
  default = {}
}

locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project
    Team        = var.team
    CostCenter  = var.cost_center
    ManagedBy   = "terraform"
    CreatedAt   = timestamp()
  }

  all_tags = merge(local.common_tags, var.required_tags)
}
```

### Alert su Costi

```hcl
# AWS Budget Alert (via Terraform)
resource "aws_budgets_budget" "monthly" {
  name         = "monthly-budget"
  budget_type  = "COST"
  limit_amount = "2500"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = ["ops-team@example.com"]
  }

  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type         = "FORECASTED"
    subscriber_email_addresses = ["ops-team@example.com", "cto@example.com"]
  }
}
```

---

## Best Practices

### CI/CD
- **Pipeline as code**: Mai configurare pipeline via UI; tutto nel repository
- **Build once, deploy everywhere**: Un artefatto, promosso tra ambienti
- **Fast feedback**: La pipeline deve fallire entro 10 minuti per errori comuni (lint, type check, unit test)
- **Test parallelizzati**: Usare sharding/matrix per ridurre il tempo totale
- **Secrets mai nel codice**: Usare secrets manager del CI/CD e ruotare regolarmente
- **Immutable tags**: Non usare `latest` in produzione; usare SHA commit o semantic versioning

### Infrastructure as Code
- **State remoto con locking**: Mai terraform state locale; usare S3+DynamoDB o GCS
- **Moduli riutilizzabili**: Evitare duplicazione tra ambienti
- **Plan prima di apply**: Sempre `terraform plan` e review prima di applicare
- **Drift detection**: Verificare periodicamente che l'infrastruttura reale corrisponda al codice
- **Blast radius limitato**: State file separati per componenti critici (database separato da compute)

### Monitoring e Observability
- **SLI/SLO definiti**: Definire Service Level Indicators e Objectives prima di configurare alert
- **Alert actionable**: Ogni alert deve avere un runbook associato e un'azione chiara
- **No alert fatigue**: Rimuovere alert che non portano ad azioni; regolare soglie
- **Structured logging**: JSON, sempre; con request ID, tenant ID e correlation ID
- **Retention policy**: Log 30 giorni hot, 90 giorni warm, 1 anno cold (compliance)

### Database
- **Migration sempre backward-compatible**: Mai breaking change in un singolo deploy
- **Backup testati**: Un backup non verificato non è un backup; test di restore settimanale
- **Connection pooling**: Sempre PgBouncer o equivalente davanti al database
- **Query monitoring**: Abilitare pg_stat_statements e log slow query (>1s)
- **Read replica**: Usare per query analytics/reporting, mai per transazioni critiche

### Security
- **Network segmentation**: Database e cache solo in subnet private, mai esposti
- **Least privilege IAM**: Service account con permessi minimi necessari
- **Encryption everywhere**: At rest (AES-256) e in transit (TLS 1.2+)
- **Secret rotation**: Rotazione automatica credenziali ogni 90 giorni
- **Vulnerability scanning**: Scan container images in pipeline CI/CD

---

## Troubleshooting

### Pipeline CI/CD fallisce

**Problema**: Build fallisce sporadicamente con "out of memory"

**Diagnosi**:
```bash
# Controlla resource limits del runner
docker stats --no-stream
# Per GitHub Actions: controlla i log per "killed" o OOM
```

**Soluzione**: Aumentare memory del runner, ridurre parallelismo test, o usare runner con più risorse. Per GitHub Actions, i runner hosted hanno 7 GB RAM; se non basta, usare runner self-hosted o large runner.

### Pod in CrashLoopBackOff

**Diagnosi**:
```bash
kubectl describe pod <pod-name> -n production
kubectl logs <pod-name> -n production --previous
kubectl get events -n production --sort-by='.lastTimestamp' | tail -20
```

**Cause comuni**: Crash all'avvio (configurazione mancante, secret non montato), health check troppo aggressivo (aumentare `initialDelaySeconds`), OOMKilled (aumentare memory limit).

### Latenza alta improvvisa

**Diagnosi**:
```bash
# 1. Controlla se è un problema di database
kubectl exec -it <pod> -- psql $DATABASE_URL -c \
  "SELECT query, calls, mean_exec_time, total_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# 2. Controlla CPU/memory dei pod
kubectl top pods -n production --sort-by=cpu

# 3. Controlla connessioni al database
kubectl exec -it <pod> -- psql $DATABASE_URL -c \
  "SELECT count(*), state, wait_event_type FROM pg_stat_activity GROUP BY state, wait_event_type;"
```

**Cause comuni**: Query lenta senza indice (aggiungere indice), connection pool esaurito (verificare PgBouncer stats), auto-scaling non ancora attivato (ridurre threshold HPA), garbage collection JVM/Node.js (profiling memory).

### Deploy causa errori 5xx

**Diagnosi**:
```bash
# 1. Confronta metriche prima/dopo deploy
# Su Grafana: confronta error rate negli ultimi 30 min vs 30 min precedenti

# 2. Controlla i log della nuova versione
kubectl logs -l app=api-server -n production --since=10m | jq 'select(.level=="error")'

# 3. Verifica migration
kubectl logs -l job-name=db-migration -n production
```

**Soluzione immediata**: Rollback
```bash
kubectl rollout undo deployment/api-server -n production
```

### Costi cloud in aumento inatteso

**Diagnosi**:
```bash
# AWS Cost Explorer via CLI
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Controlla risorse non terminate
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,Tags[?Key==`Name`].Value|[0]]' --output table
```

**Cause comuni**: Risorse di test non terminate, auto-scaling che non scala verso il basso (verificare `scaleDown` policy), log/backup storage che cresce senza retention policy, NAT Gateway con traffico elevato (verificare VPC flow logs).

---

## Riferimenti

- **Kubernetes**: https://kubernetes.io/docs/ — Documentazione ufficiale Kubernetes
- **Terraform**: https://developer.hashicorp.com/terraform/docs — Documentazione ufficiale Terraform
- **Prometheus**: https://prometheus.io/docs/ — Documentazione Prometheus
- **OpenTelemetry**: https://opentelemetry.io/docs/ — Standard open per observability
- **GitHub Actions**: https://docs.github.com/en/actions — Documentazione GitHub Actions
- **GitLab CI**: https://docs.gitlab.com/ee/ci/ — Documentazione GitLab CI/CD
- **AWS Well-Architected Framework**: https://aws.amazon.com/architecture/well-architected/ — Best practice architetturali AWS
- **Google Cloud Architecture Framework**: https://cloud.google.com/architecture/framework — Best practice GCP
- **The Twelve-Factor App**: https://12factor.net/ — Metodologia per applicazioni SaaS
- **SRE Book (Google)**: https://sre.google/sre-book/table-of-contents/ — Site Reliability Engineering
- **PgBouncer**: https://www.pgbouncer.org/ — Connection pooler per PostgreSQL
- **Istio**: https://istio.io/latest/docs/ — Service mesh per Kubernetes
- **OWASP DevSecOps**: https://owasp.org/www-project-devsecops-guideline/ — Sicurezza nelle pipeline CI/CD
