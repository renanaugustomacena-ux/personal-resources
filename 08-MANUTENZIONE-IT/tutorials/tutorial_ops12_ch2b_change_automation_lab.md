# Tutorial: Change Automation e Validation — Hands-On Lab

> **Documento di riferimento:** `23-change-automation-validation.md`
> **Dominio:** Operations Advanced
> **Ambito:** ITIL v4 Change Enablement, pipeline di validazione, GitHub Actions, soak test, rollback automatico, GitOps
> **Durata lab:** 8-10 ore (suddivise in sessioni da 2-3 ore)
> **Livello:** Da intermedio (Parte A-B) ad avanzato (Parte C)
> **Prerequisiti:** `tutorial_ops09_ch1b_change_release_management_lab.md` (Change Management base), `tutorial_ops07_ch1a_monitoring_setup_lab.md` (Prometheus/Grafana), conoscenza base YAML e Git
> **Ambiente:** Solo lab isolato — mai su sistemi di produzione

---

## Lab Environment Setup

### Requisiti Hardware

| Componente | Minimo | Raccomandato |
|---|---|---|
| RAM host | 8 GB | 16 GB |
| CPU host | 4 core | 8 core |
| Storage | 30 GB liberi | 60 GB liberi |

### VM necessarie

```
Lab Change Automation
=====================
VM1  Ubuntu 22.04 — GitLab CE o Gitea (self-hosted Git + CI/CD)
     IP: 192.168.56.10
     RAM: 4 GB, 2 vCPU

VM2  Ubuntu 22.04 — Prometheus + Grafana + Alertmanager
     IP: 192.168.56.11
     RAM: 3 GB, 2 vCPU

VM3  Ubuntu 22.04 — Applicazione target dei deploy (ambiente staging)
     IP: 192.168.56.12
     RAM: 2 GB, 2 vCPU

HOST  Windows/Linux — Browser, VS Code, terminali
```

### Struttura directory lab

```bash
# Su host/VM1
mkdir -p ~/change_lab/{templates,scripts,policies,pipelines,runbooks}
cd ~/change_lab
git init
git remote add origin http://192.168.56.10:3000/lab/change-automation.git
```

### Gitea setup rapido (alternativa leggera a GitLab)

```bash
# Su VM1 — installazione Gitea
wget -O /tmp/gitea https://dl.gitea.com/gitea/1.22.1/gitea-1.22.1-linux-amd64
sudo chmod +x /tmp/gitea && sudo mv /tmp/gitea /usr/local/bin/
sudo useradd --system --shell /bin/bash --home-dir /var/lib/gitea gitea
sudo mkdir -p /var/lib/gitea /etc/gitea
sudo chown gitea:gitea /var/lib/gitea /etc/gitea

sudo tee /etc/systemd/system/gitea.service <<'EOF'
[Unit]
Description=Gitea Git Server
After=network.target

[Service]
User=gitea
WorkingDirectory=/var/lib/gitea
ExecStart=/usr/local/bin/gitea web --config /etc/gitea/app.ini
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload && sudo systemctl enable --now gitea
# Accedi a http://192.168.56.10:3000 per completare l'installazione
```

### Installazione Ansible (per pre-validation)

```bash
# Su VM1 (runner CI/CD)
sudo apt update && sudo apt install -y ansible python3-pip
pip3 install ansible-lint jmespath
ansible --version

# Configura inventory lab
sudo mkdir -p /etc/ansible
sudo tee /etc/ansible/hosts <<'EOF'
[lab-staging]
192.168.56.12 ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/lab_key

[lab-monitoring]
192.168.56.11 ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/lab_key
EOF

# Genera chiave SSH lab
ssh-keygen -t ed25519 -f ~/.ssh/lab_key -N ""
ssh-copy-id -i ~/.ssh/lab_key.pub ubuntu@192.168.56.12
```

---

## PART A: FONDAMENTI — Capire il Perché e il Cosa

### Concetto A1: Cosa si Intende per "Change" in ITIL v4

**Analogia.** Hai un appartamento. Comprare nuovi mobili (aggiunta di feature) è un change. Ridipingere le pareti mentre ci abiti (aggiornamento in produzione con utenti connessi) è un change con rischio. Spostare i muri portanti (modifica infrastruttura core) è un change ad alto rischio che richiede autorizzazione del condominio. ITIL chiama tutto questo "change", ma non lo tratta tutto allo stesso modo.

**Definizione precisa:**

```
Change = aggiunta, modifica o rimozione di qualsiasi elemento
         che potrebbe avere un effetto sui servizi IT

NON è un change:
- Operazioni pianificate (backup, manutenzione schedulata)
- Correzione di configurazioni errate mai intenzionali
- Ripristino di emergenza a ultima versione stabile
```

**I 3 tipi di change (ITIL v4):**

| Tipo | Descrizione | Approvazione | Velocità |
|---|---|---|---|
| **Standard** | Preapprovato, basso rischio, procedura nota | Automatica (pre-autorizzata) | Immediata |
| **Normal** | Segue il processo completo CAB | CAB settimanale | 7-14 giorni |
| **Emergency** | Cambiamento urgente per risolvere incidente | ECAB (Emergency CAB) | 1-4 ore |

**Decisione: quale tipo scegliere?**

```
È in catalogo dei change standard? → SÌ → Standard change
        ↓ NO
Il servizio è in outage critico? → SÌ → Emergency change
        ↓ NO
→ Normal change
```

**ITIL v4 vs DevOps — due culture, stesso obiettivo:**

```
ITIL v4 Change Enablement          DevOps Change Management
─────────────────────────          ─────────────────────────
Focus: ridurre rischio             Focus: velocizzare delivery
Approvazione: CAB board            Approvazione: pipeline automatica
Frequenza: batch settimanale       Frequenza: continua (10+ deploy/giorno)
Documentazione: RFC formale        Documentazione: PR review
Rollback: manuale                  Rollback: automatico in pipeline

La sintesi moderna: pipeline automation PER ITIL → automatizza le evidenze ITIL
```

---

### Concetto A2: Standard Change — Automazione del Basso Rischio

**Analogia.** In un hotel, la pulizia giornaliera delle camere non richiede l'approvazione del direttore ogni mattina — è una procedura standard, preapprovata, eseguita migliaia di volte. Lo stesso principio si applica ai change IT ripetitivi: li preapprovi una volta, li automatizzi, li registri.

**Criteri per un change standard:**

```
✅ Eseguito molte volte prima (>10 esecuzioni documentate)
✅ Procedura chiaramente documentata (SOP)
✅ Rollback collaudato e automatizzabile
✅ Impatto limitato (non tocca componenti critici)
✅ Non richiede downtime o può essere pianificato

Esempi validi:
- Aggiornamento patch di sicurezza OS (WSUS/apt-get)
- Restart controllato di un servizio non critico
- Modifica configurazione nginx (vhost)
- Rotazione chiave API applicativa
- Aggiornamento certificato TLS

Esempi NON validi per standard:
- Prima modifica a un database di produzione
- Change su sistemi di pagamento
- Modifica ACL firewall
- Aggiornamento major version (es: PostgreSQL 14 → 15)
```

---

### Concetto A3: Normal Change — Il Processo RFC

**Analogia.** Vuoi ristrutturare il bagno. Devi presentare un progetto al condominio (RFC = Request for Change), ottenere il voto in assemblea (CAB review), pianificare i lavori senza disturbare i vicini (change window), e avere il numero del muratore di emergenza pronto (rollback plan). Non è burocrazia per il gusto di farlo — è gestione del rischio condiviso.

**Componenti del RFC normale:**

```
RFC (Request for Change):
  ├── Descrizione change (cosa cambia e perché)
  ├── Risk assessment (probabilità × impatto, 1-25)
  ├── Test evidence (è stato testato in staging?)
  ├── Impacted services (CIs nel CMDB)
  ├── Change window (quando eseguire, non in ore di punta)
  ├── Rollback plan (come tornare indietro, in quanto tempo)
  └── Validazione post-change (come verificare il successo)
```

**Risk Assessment Matrix:**

```
         IMPATTO
         1        2        3        4        5
       ┌────────┬────────┬────────┬────────┬────────┐
     5 │  5(L)  │  10(M) │  15(H) │  20(H) │  25(C) │
     4 │  4(L)  │   8(M) │  12(M) │  16(H) │  20(H) │
P    3 │  3(L)  │   6(M) │   9(M) │  12(M) │  15(H) │
R    2 │  2(L)  │   4(L) │   6(M) │   8(M) │  10(M) │
O    1 │  1(L)  │   2(L) │   3(L) │   4(L) │   5(L) │
B    └────────┴────────┴────────┴────────┴────────┘
A    
B    L(1-4)=Low, M(5-12)=Medium, H(13-19)=High, C(20-25)=Critical
     Critical → Emergency CAB obbligatorio prima del normal
```

---

### Concetto A4: Emergency Change — Velocità con Controllo

**Analogia.** Tuo figlio ha una reazione allergica grave. Non chiedi un secondo parere medico, non aspetti l'ambulanza programmata, non compili i moduli assicurativi prima: usi l'EpiPen e chiami il 118. Poi documenti tutto. L'emergency change funziona esattamente così: agisci, documenti dopo, ma non agisci mai senza l'equivalente dell'"EpiPen approvato" — il ECAB ha preapprovato il tipo di azione.

**5 criteri per qualificare come emergency:**

```
TUTTI e 5 devono essere veri:
1. ⚡ C'è un incidente attivo che impatta utenti in produzione
2. ⚡ Il change risolve l'incidente direttamente
3. ⚡ Ogni ora di ritardo ha impatto finanziario/reputazionale quantificabile
4. ⚡ Non è possibile aspettare il prossimo CAB regolare
5. ⚡ Il rollback è possibile se il change peggiora la situazione

NON è emergency:
- "Il cliente CEO è scocciato" (non è un outage tecnico)
- "Non ho voglia di passare dal CAB normale"
- "Siamo quasi in produzione, è urgente"
```

**Processo ECAB (Emergency Change Advisory Board):**

```
1. Incident Manager dichiara major incident P1/P2
2. Change Manager notifica ECAB (3-5 persone max)
3. ECAB: 15 minuti per decisione via call/Slack
4. Se approvato: esecuzione immediata con registrazione live
5. Post-incident: RFC retroattivo entro 48 ore + PIR (Post-Implementation Review)
```

---

### Concetto A5: Il CAB e la Pipeline di Validazione

**Analogia.** Il CAB (Change Advisory Board) è come il consiglio di sicurezza di un aeroporto: non pilota gli aerei, ma approva se un aereo può decollare (e quando, e con quale piano di emergenza). Ogni runway è una "change window". La pipeline di validazione è il preflight check automatico che fa il pilota prima che il CAB veda anche solo la richiesta.

**Struttura CAB:**

```
Ruoli nel CAB:
  Change Manager      — conduce la riunione, voto finale
  IT Operations Lead  — verifica impatto infrastruttura
  Security Lead       — verifica implicazioni di sicurezza
  Business Owner      — verifica impatto servizio
  Sviluppatore/Dev    — spiega le modifiche tecniche
  (opzionale) Audit   — per change compliance-sensitive

Frequenza: settimanale (es. martedì 10:00-11:30)
Formato moderno: async-first via Git PR + call solo per controversi
Metriche CAB:
  Change Success Rate   ≥ 95% (change completati senza incidenti)
  Emergency Ratio       ≤ 10% (emergency/totali)
  Lead Time Review      ≤ 5 giorni lavorativi
```

**Pipeline di validazione — da submit a close:**

```
SUBMIT → CLASSIFY → AUTHORIZE → SCHEDULE → EXECUTE → SMOKE → SOAK → CLOSE
   ↓         ↓          ↓            ↓          ↓        ↓       ↓
Ticket   Standard/   CAB/ECAB   Change     Ansible/  Test   15-30  Metriche
RFC      Normal/     Approval   Window     Pipeline  basic  min    OK → chiudi
         Emergency                         runs      pass   monitor
                                                            
                                                   ↓ FAIL
                                             AUTO-ROLLBACK
                                             + Incident ticket
```

---

## PART B: OPERAZIONI — Costruire e Configurare

### Esercizio B1: Creare un Standard Change Template

**Obiettivo.** Documentare un change standard in formato YAML, pronto per l'esecuzione automatica.

```yaml
# templates/sc001_nginx_vhost_update.yaml
# Standard Change: Aggiornamento configurazione nginx (vhost)
# Pre-approvato da CAB il: 2025-01-15
# Valido per: ambienti staging e produzione

id: SC-001
name: nginx-vhost-configuration-update
version: "2.1"
approved_by: "CAB-2025-01-15"
valid_until: "2026-01-15"
risk_level: Low
risk_score: 3

preconditions:
  - "Il servizio nginx è in stato 'active (running)'"
  - "Il file di configurazione passa 'nginx -t' senza errori"
  - "Il change è eseguito fuori dall'orario di punta (08:00-19:00)"
  - "Un backup della configurazione attuale esiste"

steps:
  - id: step1
    name: "Backup configurazione attuale"
    command: "sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak.$(date +%Y%m%d_%H%M%S)"
    rollback: "Non richiesto (backup già presente)"
    timeout_sec: 10
    
  - id: step2
    name: "Deploy nuova configurazione"
    command: "sudo cp {source_config} /etc/nginx/nginx.conf && sudo nginx -t"
    rollback: "sudo cp /etc/nginx/nginx.conf.bak.{timestamp} /etc/nginx/nginx.conf"
    timeout_sec: 30
    
  - id: step3
    name: "Reload nginx"
    command: "sudo systemctl reload nginx"
    rollback: "sudo systemctl reload nginx"
    timeout_sec: 15
    
validation:
  - check: "curl -s -o /dev/null -w '%{http_code}' http://localhost/ | grep -q '200\\|301'"
    description: "HTTP response code è 200 o 301"
    on_failure: "Auto-rollback immediato"
  
  - check: "sudo systemctl is-active nginx"
    description: "nginx è in stato active"
    on_failure: "Auto-rollback immediato"

rollback_procedure:
  trigger: "Qualsiasi validazione fallisce"
  steps:
    - "sudo cp /etc/nginx/nginx.conf.bak.{timestamp} /etc/nginx/nginx.conf"
    - "sudo nginx -t && sudo systemctl reload nginx"
  max_rollback_time_minutes: 5

schedule:
  allowed_days: [Monday, Tuesday, Wednesday, Thursday, Friday]
  allowed_hours: "08:00-18:00"
  not_during: ["ultimo venerdì del mese", "freeze natalizio 24-26 dicembre"]
  freeze_check_command: "cat /etc/change-freeze 2>/dev/null || echo 'no-freeze'"

post_change:
  monitor_duration_minutes: 15
  success_criteria:
    - "nginx process running"
    - "HTTP 200 on health endpoint"
    - "No 5xx errors in last 5 minutes (Prometheus)"
  close_ticket: automatic
  record_in_cmdb: true
```

---

### Esercizio B2: RFC per Normal Change — YAML Completo

**Obiettivo.** Scrivere un RFC formale in formato YAML per un change di media complessità.

```yaml
# templates/rfc_2025_047_postgres_upgrade.yaml
# RFC Normal Change: Upgrade PostgreSQL 14 → 15

rfc_id: RFC-2025-047
title: "Upgrade PostgreSQL 14 → 15 su server db-prod-01"
requestor: "ops-team@example.it"
date_submitted: "2025-03-10"
target_window: "2025-03-22 02:00-05:00 CET (sabato notte)"

description: |
  Aggiornamento major di PostgreSQL dalla versione 14.12 alla 15.6
  per ricevere supporto sicurezza esteso e miglioramenti performance.
  Il motore SQL rimane compatibile; nessuna modifica applicativa richiesta.

motivation:
  - "PostgreSQL 14 entra in End-of-Life nel novembre 2025"
  - "PostgreSQL 15 introduce parallel query improvements stimati -20% latenza"
  - "Richiesta audit sicurezza Q1 2025 (SOC 2 Type II preparation)"

risk_assessment:
  probability: 2   # Unlikely: migrazione già eseguita in staging 3 volte
  impact: 5        # Critical: database primario, downtime = outage applicazione
  score: 10        # Medium (10 = 2×5)
  
  risk_factors:
    - "pg_upgrade richiede 45-90 minuti per 500 GB database"
    - "Schema check automatico potrebbe rilevare incompatibilità sconosciute"
    - "Rollback richiede restore da backup (non istantaneo)"
  
  mitigations:
    - "pg_upgrade --check eseguito su staging: NESSUN errore"
    - "Snapshot VM eseguito T-1h dalla finestra"
    - "Backup completo con pg_dump prima dell'upgrade"
    - "Replica read-only promote-to-primary come fallback"

impacted_services:
  - ci: "db-prod-01"
    cmdb_id: "CI-2847"
    criticality: "Critical"
    services_affected: ["auth-service", "billing-api", "reporting-service"]

test_evidence:
  staging_test_date: "2025-03-08"
  staging_result: "SUCCESS"
  upgrade_duration_minutes: 62
  post_upgrade_checks: "ALL PASSED"
  application_regression_tests: "PASSED (247/247)"

phases:
  - id: phase1
    name: "Preparazione"
    duration_minutes: 30
    steps:
      - "Notifica downtime a utenti tramite status page"
      - "Snapshot VM db-prod-01"
      - "pg_dump database principale → /backup/postgres/2025-03-22_pre_upgrade.dump"
      - "Ferma applicazioni consumer (auth, billing, reporting)"
      - "Verifica replica read-only in sync (lag < 1s)"
    
  - id: phase2
    name: "Upgrade"
    duration_minutes: 90
    steps:
      - "sudo systemctl stop postgresql@14-main"
      - "sudo apt install postgresql-15 postgresql-15-contrib"
      - "sudo -u postgres /usr/lib/postgresql/15/bin/pg_upgrade --old-datadir=/var/lib/postgresql/14/main --new-datadir=/var/lib/postgresql/15/main --old-bindir=/usr/lib/postgresql/14/bin --new-bindir=/usr/lib/postgresql/15/bin"
      - "sudo systemctl start postgresql@15-main"
    
  - id: phase3
    name: "Validazione"
    duration_minutes: 30
    steps:
      - "Esecuzione test funzionali database"
      - "Riavvio applicazioni consumer"
      - "Smoke test applicativo (login, ordine test, generazione report)"
      - "Monitoraggio latenza query 15 minuti"

backout_plan:
  trigger: "Qualsiasi errore in phase2 o phase3, o latenza query > 2x baseline in fase soak"
  duration_estimate_minutes: 45
  steps:
    - "sudo systemctl stop postgresql@15-main"
    - "sudo systemctl start postgresql@14-main"
    - "Verifica integrità dati dal pg_dump pre-upgrade"
    - "Riavvio applicazioni puntando a v14"
  decision_authority: "On-call senior DBA"
  decision_deadline_minutes: 20

communication:
  announcement_t_minus: "48h via email + status page"
  in_progress_update: "Ogni 30 minuti su canale Slack #it-changes"
  completion: "Email + status page verde entro 30 min dalla fine"
  on_backout: "Comunicazione immediata CEO/CTO"

cab_review:
  scheduled: "2025-03-17 10:00 CET"
  required_approvals: ["Change Manager", "IT Ops Lead", "Security Lead", "Billing App Owner"]
  pre_read_deadline: "2025-03-15 18:00 CET"
```

---

### Esercizio B3: Script Notifica ECAB per Emergency Change

**Obiettivo.** Scrivere lo script bash per notificare immediatamente l'ECAB e avviare il processo di emergency change.

```bash
#!/usr/bin/env bash
# scripts/ecab_notify.sh
# Notifica ECAB e crea RFC di emergenza

set -euo pipefail

INCIDENT_ID="${1:?Usage: $0 <INCIDENT_ID> <CHANGE_DESCRIPTION>}"
CHANGE_DESC="${2:?}"

SLACK_WEBHOOK="${SLACK_ECAB_WEBHOOK:?Variabile SLACK_ECAB_WEBHOOK non impostata}"
PAGERDUTY_TOKEN="${PAGERDUTY_TOKEN:?Variabile PAGERDUTY_TOKEN non impostata}"
PAGERDUTY_SERVICE="${PAGERDUTY_ECAB_SERVICE_ID:?}"

TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
RFC_ID="ERFC-${TIMESTAMP}"
ON_CALL_ENGINEER="$(cat /etc/on-call-roster.json | python3 -c 'import sys,json; r=json.load(sys.stdin); print(r["current"]["name"])')"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# 1. Crea RFC di emergenza
RFC_FILE="/var/change-records/emergency/${RFC_ID}.yaml"
mkdir -p "$(dirname "${RFC_FILE}")"

cat > "${RFC_FILE}" <<YAML
rfc_id: ${RFC_ID}
type: emergency
incident_id: ${INCIDENT_ID}
description: "${CHANGE_DESC}"
requested_by: "$(whoami)@$(hostname)"
timestamp: "$(date -Iseconds)"
status: PENDING_ECAB_APPROVAL
on_call_engineer: "${ON_CALL_ENGINEER}"
YAML
log "RFC emergenza creato: ${RFC_FILE}"

# 2. Notifica Slack ECAB
SLACK_PAYLOAD=$(cat <<JSON
{
  "text": "🚨 *EMERGENCY CHANGE REQUEST* 🚨",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*RFC:* ${RFC_ID}\n*Incident:* ${INCIDENT_ID}\n*Change:* ${CHANGE_DESC}\n*Richiesto da:* $(whoami)\n*On-call:* ${ON_CALL_ENGINEER}"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "⏱️ *Risposta richiesta entro 15 minuti*\nApprova: :white_check_mark: | Blocca: :x:"
      }
    }
  ]
}
JSON
)

curl -s -X POST -H 'Content-type: application/json' \
    --data "${SLACK_PAYLOAD}" "${SLACK_WEBHOOK}"
log "Notifica Slack ECAB inviata"

# 3. Crea incident PagerDuty per ECAB
PD_PAYLOAD=$(cat <<JSON
{
  "routing_key": "${PAGERDUTY_TOKEN}",
  "event_action": "trigger",
  "payload": {
    "summary": "ECAB APPROVAL REQUIRED: ${RFC_ID} — ${CHANGE_DESC}",
    "severity": "critical",
    "source": "change-management",
    "custom_details": {
      "rfc_id": "${RFC_ID}",
      "incident_id": "${INCIDENT_ID}",
      "on_call": "${ON_CALL_ENGINEER}"
    }
  },
  "dedup_key": "${RFC_ID}"
}
JSON
)

PD_RESP=$(curl -s -X POST -H 'Content-Type: application/json' \
    --data "${PD_PAYLOAD}" \
    "https://events.pagerduty.com/v2/enqueue")
log "PagerDuty event: $(echo ${PD_RESP} | python3 -c 'import sys,json; r=json.load(sys.stdin); print(r.get("status","unknown"))')"

log "=== ECAB notificato. RFC: ${RFC_ID} ==="
log "In attesa di approvazione (max 15 minuti)"
```

---

### Esercizio B4: Pipeline GitHub Actions con Risk Scoring Automatico

**Obiettivo.** Configurare una pipeline GitHub Actions (o Gitea Actions) che calcola il risk score automaticamente e richiede approvazione umana solo sopra soglia.

```yaml
# pipelines/change-pipeline.yml
name: Change Management Pipeline

on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, labeled]
  workflow_dispatch:
    inputs:
      rfc_file:
        description: 'Path al file RFC'
        required: true

env:
  PROMETHEUS_URL: "http://192.168.56.11:9090"
  STAGING_HOST:   "192.168.56.12"
  SOAK_DURATION:  "15"  # minuti

jobs:
  # ─── FASE 1: Classify e Risk Score ───
  classify_and_score:
    name: "1. Classifica e Risk Score"
    runs-on: ubuntu-latest
    outputs:
      change_type: ${{ steps.classify.outputs.change_type }}
      risk_score:  ${{ steps.classify.outputs.risk_score }}
      requires_cab: ${{ steps.classify.outputs.requires_cab }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Classifica change e calcola risk score
        id: classify
        run: |
          RFC_FILE=$(find . -name 'rfc_*.yaml' | head -1)
          if [ -z "${RFC_FILE}" ]; then
            RFC_FILE="templates/sc001_nginx_vhost_update.yaml"
          fi
          
          # Leggi risk score dal file RFC
          RISK_SCORE=$(python3 -c "
          import yaml, sys
          with open('${RFC_FILE}') as f:
              doc = yaml.safe_load(f)
          score = doc.get('risk_assessment', {}).get('score', 5)
          print(score)
          ")
          
          # Determina tipo change
          CHANGE_TYPE="normal"
          if python3 -c "
          import yaml
          with open('${RFC_FILE}') as f:
              doc = yaml.safe_load(f)
          print(doc.get('id', '').startswith('SC-'))
          " | grep -q "True"; then
            CHANGE_TYPE="standard"
          fi
          
          REQUIRES_CAB="false"
          if [ "${RISK_SCORE}" -ge 10 ] || [ "${CHANGE_TYPE}" = "normal" ]; then
            REQUIRES_CAB="true"
          fi
          
          echo "change_type=${CHANGE_TYPE}"  >> $GITHUB_OUTPUT
          echo "risk_score=${RISK_SCORE}"    >> $GITHUB_OUTPUT
          echo "requires_cab=${REQUIRES_CAB}" >> $GITHUB_OUTPUT
          
          echo "=== Change Classification ==="
          echo "Tipo:        ${CHANGE_TYPE}"
          echo "Risk Score:  ${RISK_SCORE}"
          echo "CAB Review:  ${REQUIRES_CAB}"

  # ─── FASE 2: Validazione Statica ───
  static_validation:
    name: "2. Validazione Statica"
    runs-on: ubuntu-latest
    needs: classify_and_score
    steps:
      - uses: actions/checkout@v4
      
      - name: Installa tool validazione
        run: |
          pip install yamllint ansible-lint checkov
          
      - name: YAML Lint
        run: yamllint -d relaxed templates/ || true
        
      - name: Ansible Lint (se presente playbook)
        run: |
          if ls *.yml 2>/dev/null | head -1; then
            ansible-lint *.yml --no-cache || true
          fi
          
      - name: Checkov security scan (IaC)
        run: |
          checkov -d . --framework ansible --quiet --compact || true
          echo "✅ Static validation completata"

  # ─── FASE 3: CAB Approval Gate ───
  cab_approval:
    name: "3. CAB Approval"
    runs-on: ubuntu-latest
    needs: [classify_and_score, static_validation]
    if: needs.classify_and_score.outputs.requires_cab == 'true'
    environment:
      name: cab-review
      # "cab-review" environment in GitHub deve avere required_reviewers configurati
      # In lab: skip questa fase, simula approvazione
    steps:
      - name: Segnala attesa CAB
        run: |
          echo "⏳ Change richiede approvazione CAB"
          echo "Risk Score: ${{ needs.classify_and_score.outputs.risk_score }}"
          echo "CAB review schedulata — in attesa di approvazione..."

  # ─── FASE 4: Pre-Change Validation ───
  pre_change_validation:
    name: "4. Pre-Change Validation"
    runs-on: ubuntu-latest
    needs: [classify_and_score, static_validation]
    if: needs.classify_and_score.outputs.change_type == 'standard' || success()
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.LAB_SSH_KEY }}" > ~/.ssh/lab_key
          chmod 600 ~/.ssh/lab_key
          
      - name: Verifica salute staging pre-change
        run: |
          echo "=== Baseline Metrics Pre-Change ==="
          
          # Verifica raggiungibilità
          ssh -i ~/.ssh/lab_key -o StrictHostKeyChecking=no ubuntu@${STAGING_HOST} \
            "systemctl is-active nginx && echo 'nginx: OK'"
          
          # Salva baseline Prometheus
          BASELINE_CPU=$(curl -s "${PROMETHEUS_URL}/api/v1/query" \
            --data-urlencode 'query=avg(rate(node_cpu_seconds_total{mode!="idle",instance="192.168.56.12:9100"}[5m]))*100' \
            | python3 -c 'import sys,json; r=json.load(sys.stdin); vals=r["data"]["result"]; print(vals[0]["value"][1] if vals else "N/A")')
          
          echo "CPU baseline: ${BASELINE_CPU}%"
          echo "${BASELINE_CPU}" > /tmp/baseline_cpu.txt

  # ─── FASE 5: Esecuzione ───
  execute:
    name: "5. Esecuzione Change"
    runs-on: ubuntu-latest
    needs: pre_change_validation
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.LAB_SSH_KEY }}" > ~/.ssh/lab_key
          chmod 600 ~/.ssh/lab_key
          
      - name: Esegui change (Ansible playbook)
        run: |
          echo "=== Inizio esecuzione change ==="
          echo "Timestamp: $(date -Iseconds)"
          
          # In lab: simula deploy nginx config aggiornata
          ssh -i ~/.ssh/lab_key -o StrictHostKeyChecking=no ubuntu@${STAGING_HOST} \
            "sudo nginx -t && echo 'Config valida — reload' && sudo systemctl reload nginx"
          
          echo "=== Change eseguito ==="

  # ─── FASE 6: Smoke Test ───
  smoke_test:
    name: "6. Smoke Test"
    runs-on: ubuntu-latest
    needs: execute
    steps:
      - name: Smoke test basico
        run: |
          echo "=== Smoke Test ==="
          
          HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            "http://${STAGING_HOST}/" --connect-timeout 10)
          
          if [[ "${HTTP_CODE}" == "200" || "${HTTP_CODE}" == "301" || "${HTTP_CODE}" == "302" ]]; then
            echo "✅ HTTP response: ${HTTP_CODE}"
          else
            echo "❌ HTTP response: ${HTTP_CODE} — SMOKE TEST FAILED"
            exit 1
          fi
          
          echo "✅ Smoke test passato"

  # ─── FASE 7: Soak Test ───
  soak_test:
    name: "7. Soak Test (${{ env.SOAK_DURATION }}min)"
    runs-on: ubuntu-latest
    needs: smoke_test
    steps:
      - uses: actions/checkout@v4
      
      - name: Installa dipendenze soak
        run: pip install requests pyyaml
        
      - name: Esegui soak test
        run: |
          python3 scripts/soak_test.py \
            --host "${STAGING_HOST}" \
            --prometheus "${PROMETHEUS_URL}" \
            --duration "${SOAK_DURATION}"

  # ─── FASE 8: Close ───
  close_change:
    name: "8. Close Change"
    runs-on: ubuntu-latest
    needs: soak_test
    if: success()
    steps:
      - name: Registra completamento
        run: |
          echo "✅ Change completato con successo"
          echo "Timestamp: $(date -Iseconds)"
          echo "Status: COMPLETED_SUCCESSFULLY"
          echo "Soak duration: ${SOAK_DURATION} minuti"

  # ─── AUTO-ROLLBACK ───
  auto_rollback:
    name: "Auto-Rollback"
    runs-on: ubuntu-latest
    needs: [smoke_test, soak_test]
    if: failure()
    steps:
      - uses: actions/checkout@v4
      
      - name: Esegui rollback automatico
        run: |
          echo "⚠️ Fallimento rilevato — avvio rollback automatico"
          echo "Timestamp rollback: $(date -Iseconds)"
          
          # Rollback nginx
          ssh -i ~/.ssh/lab_key -o StrictHostKeyChecking=no ubuntu@${STAGING_HOST} \
            "sudo cp \$(ls -t /etc/nginx/nginx.conf.bak.* | head -1) /etc/nginx/nginx.conf && \
             sudo nginx -t && sudo systemctl reload nginx && \
             echo 'Rollback completato'"
          
          echo "🔴 CHANGE FALLITO — ROLLBACK ESEGUITO — Aprire incident ticket"
          exit 1
```

---

### Esercizio B5: Soak Test Python con Soglie

**Obiettivo.** Implementare lo script soak test che monitora le metriche durante il periodo post-change.

```python
# scripts/soak_test.py
import argparse
import time
import sys
import requests
from dataclasses import dataclass

@dataclass
class ThresholdCheck:
    name: str
    query: str
    operator: str   # '<' | '>' | '<='
    threshold: float
    unit: str = ""

# Soglie di successo post-change
THRESHOLDS: list[ThresholdCheck] = [
    ThresholdCheck(
        name="CPU Media",
        query='avg(rate(node_cpu_seconds_total{mode!="idle",instance=~"INSTANCE.*"}[5m]))*100',
        operator='<', threshold=80, unit="%"
    ),
    ThresholdCheck(
        name="RAM Usata",
        query='(1 - node_memory_MemAvailable_bytes{instance=~"INSTANCE.*"} / node_memory_MemTotal_bytes) * 100',
        operator='<', threshold=85, unit="%"
    ),
    ThresholdCheck(
        name="HTTP 5xx Rate",
        query='sum(rate(http_requests_total{job="lab-app",code=~"5.."}[5m])) / sum(rate(http_requests_total{job="lab-app"}[5m])) * 100',
        operator='<', threshold=0.1, unit="%"
    ),
]

def query_prometheus(base_url: str, promql: str) -> float | None:
    try:
        resp = requests.get(f"{base_url}/api/v1/query",
                           params={"query": promql}, timeout=10)
        resp.raise_for_status()
        results = resp.json()['data']['result']
        return float(results[0]['value'][1]) if results else None
    except Exception as e:
        print(f"  ⚠️  Query error: {e}")
        return None

def check_thresholds(prometheus_url: str, instance: str) -> tuple[bool, list[str]]:
    failures = []
    for t in THRESHOLDS:
        q = t.query.replace("INSTANCE", instance)
        value = query_prometheus(prometheus_url, q)
        
        if value is None:
            print(f"  ⚠️  {t.name}: dati non disponibili (skip)")
            continue
        
        if t.operator == '<' and value >= t.threshold:
            msg = f"❌ {t.name}: {value:.2f}{t.unit} >= {t.threshold}{t.unit} (soglia superata)"
            failures.append(msg)
            print(f"  {msg}")
        elif t.operator == '>' and value <= t.threshold:
            msg = f"❌ {t.name}: {value:.2f}{t.unit} <= {t.threshold}{t.unit} (sotto soglia)"
            failures.append(msg)
            print(f"  {msg}")
        else:
            print(f"  ✅ {t.name}: {value:.2f}{t.unit} (soglia: {t.operator}{t.threshold}{t.unit})")
    
    return len(failures) == 0, failures

def main():
    parser = argparse.ArgumentParser(description='Soak test post-change')
    parser.add_argument('--host',       required=True)
    parser.add_argument('--prometheus', required=True)
    parser.add_argument('--duration',   type=int, default=15, help='Minuti di soak')
    parser.add_argument('--interval',   type=int, default=60,  help='Secondi tra check')
    args = parser.parse_args()
    
    check_interval = args.interval
    total_checks = (args.duration * 60) // check_interval
    
    print(f"\n=== Soak Test Avviato ===")
    print(f"Host:     {args.host}")
    print(f"Duration: {args.duration} min ({total_checks} check ogni {check_interval}s)")
    
    all_ok = True
    for check_num in range(1, total_checks + 1):
        elapsed_min = (check_num * check_interval) // 60
        print(f"\n[{check_num}/{total_checks}] Check {elapsed_min}min/{args.duration}min — {time.strftime('%H:%M:%S')}")
        
        ok, failures = check_thresholds(args.prometheus, args.host.replace('.', '.') + ':9100')
        
        if not ok:
            all_ok = False
            print(f"\n🔴 SOAK TEST FALLITO al check {check_num}")
            for f in failures:
                print(f"  {f}")
            sys.exit(1)
        
        if check_num < total_checks:
            time.sleep(check_interval)
    
    if all_ok:
        print(f"\n✅ Soak test completato: {args.duration} minuti — TUTTE le soglie rispettate")
        sys.exit(0)

if __name__ == '__main__':
    main()
```

---

### Esercizio B6: Pre-Change Validation Ansible

**Obiettivo.** Creare un playbook Ansible che verifica i prerequisiti prima di ogni change.

```yaml
# scripts/pre_change_validation.yml
---
- name: "Pre-Change Validation"
  hosts: "{{ target_host | default('lab-staging') }}"
  gather_facts: true
  vars:
    max_cpu_pct: 70
    max_ram_pct: 80
    min_disk_free_gb: 5
    required_services: "{{ services | default(['nginx', 'prometheus-node-exporter']) }}"

  tasks:
    - name: "Verifica servizi richiesti attivi"
      ansible.builtin.systemd:
        name: "{{ item }}"
      register: svc_status
      loop: "{{ required_services }}"
      
    - name: "Fallisci se servizi non attivi"
      ansible.builtin.fail:
        msg: "Servizio {{ item.name }} non è in stato active (stato: {{ item.status.ActiveState }})"
      loop: "{{ svc_status.results }}"
      when: item.status.ActiveState != 'active'

    - name: "Verifica CPU non in saturazione"
      ansible.builtin.command: >
        python3 -c "
        import subprocess, re
        out = subprocess.check_output(['top', '-bn1'], text=True)
        idle = float(re.search(r'(\d+\.\d+)\s+id', out).group(1))
        cpu_used = 100 - idle
        print(f'{cpu_used:.1f}')
        if cpu_used > {{ max_cpu_pct }}:
            exit(1)
        "
      register: cpu_check
      changed_when: false
      failed_when: cpu_check.rc != 0
      
    - name: "Log CPU pre-change"
      ansible.builtin.debug:
        msg: "CPU pre-change: {{ cpu_check.stdout }}% (soglia: {{ max_cpu_pct }}%)"

    - name: "Verifica spazio disco sufficiente"
      ansible.builtin.assert:
        that: "item.size_available > (min_disk_free_gb | int * 1024 * 1024 * 1024)"
        fail_msg: >
          Disco {{ item.mount }} ha solo
          {{ (item.size_available / 1024**3) | round(1) }} GB liberi
          (richiesti {{ min_disk_free_gb }} GB)
      loop: "{{ ansible_mounts | selectattr('mount', 'equalto', '/') | list }}"
      
    - name: "Esegui backup configurazione corrente"
      ansible.builtin.copy:
        src: "/etc/nginx/nginx.conf"
        dest: "/etc/nginx/nginx.conf.bak.{{ ansible_date_time.iso8601_basic_short }}"
        remote_src: true
        backup: false
      when: "'nginx' in required_services"

    - name: "Verifica sintassi nginx (dry-run)"
      ansible.builtin.command: nginx -t
      register: nginx_test
      changed_when: false
      when: "'nginx' in required_services"
      
    - name: "Report pre-change validation"
      ansible.builtin.debug:
        msg: |
          === PRE-CHANGE VALIDATION REPORT ===
          Host:        {{ inventory_hostname }}
          Timestamp:   {{ ansible_date_time.iso8601 }}
          CPU attuale: {{ cpu_check.stdout }}%
          Stato:       TUTTI I CHECK SUPERATI — Change autorizzato
```

---

### Esercizio B7: Change Freeze — Gestione Periodi Bloccati

**Obiettivo.** Implementare un sistema di change freeze con check automatico in pipeline.

```python
# scripts/b7_change_freeze.py
# Gestisce periodi di freeze change e verifica se un change può procedere

from datetime import date, datetime
from dataclasses import dataclass, field

@dataclass
class FreezeWindow:
    name: str
    start: date
    end: date
    type: str         # hard | soft
    reason: str
    exceptions: list[str] = field(default_factory=list)

# Finestre di freeze standard (aggiorna annualmente)
FREEZE_WINDOWS: list[FreezeWindow] = [
    FreezeWindow(
        name="Natale",
        start=date(2025, 12, 24),
        end=date(2026, 1, 6),
        type="hard",
        reason="Periodo festivo — team ridotto, nessun supporto",
        exceptions=["security-emergency", "p1-outage-fix"]
    ),
    FreezeWindow(
        name="Fine Trimestre Q4",
        start=date(2025, 12, 15),
        end=date(2025, 12, 23),
        type="soft",
        reason="Chiusura fiscale — nessun change che impatta billing",
        exceptions=["security-emergency", "p1-outage-fix", "non-billing-standard"]
    ),
    FreezeWindow(
        name="Blackout Mobile Release",
        start=date(2025, 3, 1),
        end=date(2025, 3, 5),
        type="soft",
        reason="Release branch mobile — no infra changes",
        exceptions=["security-emergency"]
    ),
]

def check_freeze(
    target_date: date = None,
    change_label: str = "normal",
) -> dict:
    """Controlla se una data è in freeze e se il change è eccezione."""
    if target_date is None:
        target_date = date.today()
    
    for fw in FREEZE_WINDOWS:
        if fw.start <= target_date <= fw.end:
            is_exception = change_label in fw.exceptions
            return {
                "in_freeze":   True,
                "freeze_name": fw.name,
                "freeze_type": fw.type,
                "reason":      fw.reason,
                "allowed":     is_exception or fw.type == "soft",
                "exception":   is_exception,
                "message": (
                    f"✅ Change consentito come eccezione ({change_label})"
                    if is_exception else
                    f"⚠️  Freeze {fw.type}: {fw.name} — {fw.reason}"
                    if fw.type == "soft" else
                    f"🚫 HARD FREEZE: {fw.name} — Change non consentito"
                )
            }
    
    return {
        "in_freeze": False,
        "allowed":   True,
        "message":   f"✅ {target_date} è fuori da periodi di freeze"
    }

# Test varie date
test_cases = [
    (date(2025, 11, 15), "normal"),              # Normale
    (date(2025, 12, 20), "normal"),              # Soft freeze Q4
    (date(2025, 12, 20), "non-billing-standard"),# Eccezione soft freeze
    (date(2025, 12, 25), "normal"),              # Hard freeze Natale
    (date(2025, 12, 25), "security-emergency"),  # Eccezione hard freeze
]

for d, label in test_cases:
    result = check_freeze(d, label)
    print(f"\n{d} [{label}]")
    print(f"  {result['message']}")
    if not result['allowed']:
        print(f"  → BLOCCO PIPELINE: change non autorizzato")
```

---

## PART C: SISTEMATIZZARE — Dall'Esecuzione alla Governance

### Progetto C1: Runbook Operativo per Gestione Change

```markdown
<!-- runbooks/change-management-runbook.md -->
# Runbook: Change Management Quotidiano

## 1. Verifica Change Calendar Giornaliero (08:30 ogni mattina)

```bash
# Controlla change schedulati oggi
cat /var/change-records/scheduled/$(date +%Y-%m-%d)*.yaml 2>/dev/null || echo "Nessun change schedulato oggi"

# Verifica freeze attivi
python3 scripts/b7_change_freeze.py | grep -v "✅"
```

## 2. Processo Pre-Change (T-2h dalla finestra)

1. Re-leggi RFC e verifica che nulla sia cambiato da quando è stato approvato
2. Esegui pre-validation Ansible: `ansible-playbook scripts/pre_change_validation.yml`
3. Notifica stakeholder: "Change inizia alle HH:MM — contatto: [nome]"
4. Verifica che il backup post nel RFC sia accessibile e recente

## 3. Durante l'Esecuzione

- Apri il change record e aggiornalo man mano (evidenza per audit)
- Non deviare mai dalla procedura approvata senza nuova autorizzazione
- Ogni step completato → log con timestamp
- Se trovi qualcosa di imprevisto → STOP → consulta Change Manager

## 4. Post-Change (entro 30 minuti)

1. Smoke test → soak test (pipeline automatica o manuale da scripts/)
2. Aggiorna status change record: COMPLETED o FAILED
3. Se FAILED: attiva procedura rollback, apri incident ticket
4. Comunica completamento a stakeholder

## 5. KPI mensili da monitorare

| Metrica | Target | Azione se fuori target |
|---|---|---|
| Change Success Rate | ≥ 95% | Root cause analysis, review processo |
| Emergency Ratio | ≤ 10% | Identificare pattern, prevenzione |
| Rollback Rate | ≤ 5% | Migliorare test pre-change |
| Lead Time (submit → esecuzione) | ≤ 7gg | Snellire processo approvazione |
```

---

### Progetto C2: Script KPI Mensile Change

```python
# scripts/c2_monthly_change_kpi.py
# Calcola KPI mensili del processo di change management

import os
import yaml
from datetime import date
from pathlib import Path

RECORDS_DIR = Path('/var/change-records')

def load_records(month_year: str = None) -> list[dict]:
    """Carica tutti i record del mese specificato (YYYY-MM)."""
    records = []
    search_dir = RECORDS_DIR / 'completed' if (RECORDS_DIR / 'completed').exists() else RECORDS_DIR
    
    if not search_dir.exists():
        # Modalità lab: dati simulati
        return [
            {'type': 'standard', 'status': 'COMPLETED_SUCCESSFULLY', 'emergency': False},
            {'type': 'normal',   'status': 'COMPLETED_SUCCESSFULLY', 'emergency': False},
            {'type': 'normal',   'status': 'FAILED_ROLLBACK',        'emergency': False},
            {'type': 'emergency','status': 'COMPLETED_SUCCESSFULLY', 'emergency': True},
            {'type': 'standard', 'status': 'COMPLETED_SUCCESSFULLY', 'emergency': False},
            {'type': 'normal',   'status': 'COMPLETED_SUCCESSFULLY', 'emergency': False},
        ]
    
    for f in search_dir.glob('*.yaml'):
        with open(f) as fp:
            records.append(yaml.safe_load(fp))
    return records

def compute_kpis(records: list[dict]) -> dict:
    total = len(records)
    if total == 0:
        return {}
    
    successful   = sum(1 for r in records if 'SUCCESSFULLY' in r.get('status', ''))
    failed       = sum(1 for r in records if 'FAILED' in r.get('status', ''))
    rollbacks    = sum(1 for r in records if 'ROLLBACK' in r.get('status', ''))
    emergencies  = sum(1 for r in records if r.get('emergency') or r.get('type') == 'emergency')
    
    return {
        'total':              total,
        'successful':         successful,
        'failed':             failed,
        'rollbacks':          rollbacks,
        'emergencies':        emergencies,
        'success_rate_pct':   round(successful / total * 100, 1),
        'emergency_ratio_pct': round(emergencies / total * 100, 1),
        'rollback_rate_pct':  round(rollbacks / total * 100, 1),
    }

records = load_records()
kpis    = compute_kpis(records)

report = f"""# Change Management KPI — {date.today().strftime('%B %Y')}

| KPI | Valore | Target | Status |
|---|---|---|---|
| Change Success Rate | {kpis.get('success_rate_pct', 0):.1f}% | ≥ 95% | {'✅' if kpis.get('success_rate_pct', 0) >= 95 else '❌'} |
| Emergency Ratio | {kpis.get('emergency_ratio_pct', 0):.1f}% | ≤ 10% | {'✅' if kpis.get('emergency_ratio_pct', 0) <= 10 else '❌'} |
| Rollback Rate | {kpis.get('rollback_rate_pct', 0):.1f}% | ≤ 5% | {'✅' if kpis.get('rollback_rate_pct', 0) <= 5 else '❌'} |

## Dettaglio Volume

- Total change: {kpis.get('total', 0)}
- Completati con successo: {kpis.get('successful', 0)}
- Falliti: {kpis.get('failed', 0)}
- Rollback eseguiti: {kpis.get('rollbacks', 0)}
- Emergency change: {kpis.get('emergencies', 0)}
"""

print(report)
report_file = f"reports/change_kpi_{date.today().strftime('%Y-%m')}.md"
os.makedirs('reports', exist_ok=True)
with open(report_file, 'w') as f:
    f.write(report)
print(f"📄 Report salvato: {report_file}")
```

---

## Checklist di Validazione Lab

- [ ] **A1**: Distinzione Standard/Normal/Emergency change con decision tree
- [ ] **A2**: 5 criteri per standard change + 3 esempi validi e 3 non validi
- [ ] **A3**: RFC completo con risk matrix (probabilità × impatto) e risk score calcolato
- [ ] **A4**: 5 criteri per emergency change, comprensione ECAB 15 minuti
- [ ] **A5**: Pipeline 8-fasi (submit→close) disegnata con auto-rollback su failure
- [ ] **B1**: Standard change template YAML con preconditions, steps, validation, rollback
- [ ] **B2**: RFC normal change YAML con risk_assessment, phases e backout_plan
- [ ] **B3**: Script `ecab_notify.sh` crea RFC YAML + notifica Slack + PagerDuty
- [ ] **B4**: Pipeline GitHub Actions con classificazione, risk score, approvazione, soak
- [ ] **B5**: Script soak test Python con ThresholdCheck e loop di monitoraggio
- [ ] **B6**: Playbook Ansible pre-validation con check CPU, disco, servizi, backup
- [ ] **B7**: Sistema change freeze con FreezeWindow e check hard/soft/eccezioni
- [ ] **C1**: Runbook operativo giornaliero in formato markdown strutturato
- [ ] **C2**: Script KPI mensile genera report con 4 metriche target

---

## Appendice A: Confronto Tipi di Change

| Aspetto | Standard | Normal | Emergency |
|---|---|---|---|
| Pre-approvazione | ✅ Permanente | ❌ RFC per ogni change | ❌ Approvazione real-time |
| CAB Review | Non richiesta | Settimanale | ECAB entro 15 min |
| Test richiesti | Procedura documentata | Staging + regression | Staging se disponibile |
| Rollback | Automatico (pipeline) | Testato manuale | Manuale (best effort) |
| Documentazione | Template precompilato | RFC completo | RFC retroattivo 48h |
| Frequenza tipica | 70-80% del totale | 15-25% | <5% |
| Risk score tipico | 1-6 | 4-15 | Qualsiasi |

---

## Appendice B: Change Window Standard

| Servizio | Finestra preferita | Finestra alternativa | Note |
|---|---|---|---|
| Server database | Sabato 01:00-05:00 | Dom 00:00-04:00 | Backup completato prima |
| Web/API server | Martedì 22:00-01:00 | Mer 22:00-01:00 | Traffico minimo |
| Active Directory | Domenica 02:00-05:00 | Mai in replication peak | Coordina con replica AD |
| Rete/Firewall | Sabato 23:00-03:00 | Dom 01:00-05:00 | Tutte le app impattate |
| Standard change | Qualsiasi giorno 09:00-18:00 | — | Solo se basso traffico |
| Emergency | Qualsiasi momento | — | Approva ECAB prima |

---

## Appendice C: Mappatura ITIL 4

| Pratica ITIL 4 | Collegamento a questo tutorial |
|---|---|
| Change Enablement | Intero tutorial — tipi, RFC, CAB, pipeline |
| Deployment Management | Fase esecuzione nella pipeline |
| Service Validation and Testing | Smoke test, soak test, validazione |
| Incident Management | Emergency change scaturisce da P1/P2 |
| Problem Management | Change failure ripetuta → problem record |
| Release Management | Pipeline automatizzata = release pipeline |
| Knowledge Management | Runbook C1, template YAML riutilizzabili |

---

## Riferimenti

1. ITIL 4 Foundation — *ITIL 4 Managing Professional: Direct, Plan and Improve* (Axelos, 2019)
2. Kim, G. et al. — *The DevOps Handbook* (IT Revolution, 2016) — Cap. 12 (Change Management)
3. Kim, G. et al. — *Accelerate* (IT Revolution, 2018) — Change batch size, Lead Time
4. GitHub — *GitHub Actions Documentation* — Environments, Required Reviewers
5. Ansible — *Best Practices Guide* — Playbook structure, idempotency
6. ISACA — *COBIT 2019 Framework: Governance and Management Objectives* — BAI06 (Change)
7. Forsgren, N. — *2024 State of DevOps Report* (Google/DORA) — Change failure rate benchmarks
