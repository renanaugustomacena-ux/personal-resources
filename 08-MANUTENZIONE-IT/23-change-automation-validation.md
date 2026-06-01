# Change Automation e Validation — Pipeline ITIL v4

> **Modulo:** Operations IT · Modulo 23 (NEW)
> **Prerequisiti:** Moduli 01, 12; CI/CD basics.
> **Obiettivi:** automatizzare standard change; validation post-change; rollback automatico; change calendar.
> **Tempo:** 60 min · lab 240 min · **Livello:** proficient · **Aggiornamento:** 2026-04-27

## Idee guida

1. **Standard change pre-approved + automatizzato.** No CAB ogni volta.
2. **Validation gate post-change: smoke test + soak test 30 min.**
3. **Auto-rollback se validation fallisce.** Senza, scoperta tardiva.
4. **Change calendar = freeze window visibility.** Mobile release, peak season, ecc.
5. **Infrastructure as Code e il prerequisito.** Senza IaC, il change management resta manuale e soggetto a errori umani. Terraform, Ansible, Puppet devono essere i veicoli primari per ogni modifica infrastrutturale.
6. **Ogni change deve essere tracciabile, auditabile, reversibile.** La compliance non e un add-on: e un requisito architetturale della pipeline.
7. **Il rischio si quantifica, non si intuisce.** Matrice di rischio con scoring numerico, non valutazione a sentimento.

## Indice

1. [Framework di Change Management](#1-framework-di-change-management)
2. [Tipologie di Change](#2-tipologie-di-change)
3. [Il Processo CAB](#3-il-processo-cab)
4. [Pipeline di Validazione Automatizzata](#4-pipeline-di-validazione-automatizzata)
5. [Pre-Change Validation](#5-pre-change-validation)
6. [Post-Change Verification](#6-post-change-verification)
7. [Strategie di Deployment](#7-strategie-di-deployment)
8. [Rollback Automation](#8-rollback-automation)
9. [Change Risk Assessment Matrix](#9-change-risk-assessment-matrix)
10. [CI/CD e Change Management Integration](#10-cicd-e-change-management-integration)
11. [GitOps per Infrastructure Changes](#11-gitops-per-infrastructure-changes)
12. [Terraform Plan/Apply Validation](#12-terraform-planapply-validation)
13. [Ansible Check Mode e Validazione](#13-ansible-check-mode-e-validazione)
14. [Configuration Drift Detection](#14-configuration-drift-detection)
15. [Change Freeze e Maintenance Windows](#15-change-freeze-e-maintenance-windows)
16. [Compliance e Audit Trail](#16-compliance-e-audit-trail)
17. [Troubleshooting](#17-troubleshooting)
18. [FAQ](#18-faq)
19. [Esercizi e Laboratori](#19-esercizi-e-laboratori)
20. [Auto-valutazione](#20-auto-valutazione)
21. [Letture e Riferimenti](#21-letture-e-riferimenti)
22. [Collegamenti Incrociati](#22-collegamenti-incrociati)
23. [Glossario Locale](#23-glossario-locale)

---

## 1. Framework di Change Management

### 1.1 ITIL v4 — Change Enablement

ITIL v4 ha rinominato "Change Management" in "Change Enablement" per enfatizzare il ruolo abilitante piuttosto che il controllo burocratico. Il focus si sposta dal gate-keeping alla facilitazione del flusso di valore, mantenendo il controllo del rischio.

**Principi fondamentali di Change Enablement in ITIL v4:**

| Principio | Descrizione | Impatto operativo |
|-----------|-------------|-------------------|
| Massimizzare il throughput | Ridurre il lead time delle change senza aumentare il rischio | Pipeline automatizzate per standard change |
| Risk-based approach | Investire effort di governance proporzionale al rischio | Standard change senza CAB, emergency con fast-track |
| Automate where possible | Eliminare attivita manuali ripetitive | CI/CD, IaC, automated testing |
| Shift left validation | Validare il prima possibile nel ciclo | Pre-commit hooks, linting, policy as code |
| Continuous improvement | Misurare e ottimizzare il processo stesso | Metriche di change success rate, lead time |

**Il ciclo di vita di un change in ITIL v4:**

```
1. Change Initiation
   └── RFC (Request for Change) creato
       ├── Descrizione del change
       ├── Justification (business case)
       ├── Risk assessment
       ├── Implementation plan
       ├── Backout/rollback plan
       └── Test plan

2. Change Classification
   └── Tipo determinato (standard / normal / emergency)
       └── Se standard → pre-approved, pipeline automatica
       └── Se normal → valutazione CAB
       └── Se emergency → fast-track con review post-implementazione

3. Change Authorization
   └── Standard: automatica (pre-approved model)
   └── Normal: CAB o change authority designata
   └── Emergency: ECAB o on-call change authority

4. Change Implementation
   └── Esecuzione secondo implementation plan
   └── Monitoring attivo durante implementazione
   └── Validation gates automatizzati

5. Change Review
   └── Post-Implementation Review (PIR)
   └── Aggiornamento CMDB
   └── Lessons learned
   └── Metriche registrate
```

### 1.2 DevOps Change Management

Il change management DevOps non sostituisce ITIL ma lo complementa, accelerando il flusso mantenendo il controllo. La differenza fondamentale e che in DevOps il change e embedded nel pipeline, non un processo esterno.

**Confronto ITIL tradizionale vs DevOps:**

| Aspetto | ITIL tradizionale | DevOps | Ibrido raccomandato |
|---------|-------------------|--------|---------------------|
| Frequenza change | Settimanale/mensile | Multipla al giorno | Risk-based frequency |
| Approvazione | CAB settimanale | Peer review nel PR | Automated + peer review |
| Documentazione | RFC formale | Commit message + PR | Structured PR template |
| Testing | Manuale pre-deploy | Automatizzato nel pipeline | Fully automated |
| Rollback | Manuale, documentato | Automatico | Automated con alerting |
| Lead time | Giorni/settimane | Minuti/ore | Ore per normal, minuti per standard |
| Audit trail | Ticket system | Git history | Git + ticket integration |

**I Quattro Pilastri del DevOps Change Management:**

1. **Everything as Code**: infrastruttura, configurazione, policy, test — tutto versionato in Git.
2. **Pipeline as Gatekeeper**: il pipeline CI/CD sostituisce l'approvazione manuale per standard change, con gate automatizzati (test, security scan, compliance check).
3. **Observability-Driven Validation**: la validazione post-change si basa su metriche, non su checklist manuali. SLI/SLO monitorati in tempo reale.
4. **Blameless Culture**: il fallimento di un change non e colpa di chi lo ha eseguito ma del processo che non lo ha intercettato. Post-mortem blameless obbligatorio.

### 1.3 Framework ADKAR per il Change Organizzativo

Quando si introduce l'automazione del change management, il cambiamento tecnico e solo meta dell'equazione. Il framework ADKAR gestisce il lato umano:

| Fase | Descrizione | Azioni concrete |
|------|-------------|-----------------|
| **Awareness** | Perche cambiare | Presentare metriche di change failure rate, lead time attuale |
| **Desire** | Volonta di partecipare | Mostrare riduzione di toil, meno weekend on-call |
| **Knowledge** | Come cambiare | Training su IaC, CI/CD, Git workflow |
| **Ability** | Capacita di implementare | Lab pratici, pair programming, mentoring |
| **Reinforcement** | Sostenere il cambiamento | Metriche visibili, celebration of success, feedback loop |

---

## 2. Tipologie di Change

### 2.1 Standard Change

Una standard change e una modifica pre-approvata, a basso rischio, ben documentata e ripetitiva. La pre-approvazione avviene una sola volta: il modello di change viene valutato dal CAB, e tutte le istanze successive vengono eseguite senza ulteriore approvazione.

**Caratteristiche di una standard change:**

- Procedura documentata e testata
- Rischio basso e ben compreso
- Esito prevedibile
- Rollback definito e testato
- Trigger ben definito (schedule, evento, richiesta)
- Impatto limitato e contenuto

**Esempi tipici:**

| Standard Change | Frequenza | Automazione |
|-----------------|-----------|-------------|
| Patch di sicurezza OS (non-critical) | Settimanale | Ansible playbook schedulato |
| Aggiornamento certificati TLS | Trimestrale | Certbot + cron |
| Aggiunta utente a gruppo AD | On-demand | PowerShell runbook |
| Scaling orizzontale app server | On-demand | Terraform + auto-scaling |
| Rotazione log archivi | Giornaliera | logrotate configurato |
| Deploy applicativo in staging | Multiplo/giorno | CI/CD pipeline |
| Aggiornamento regole firewall (whitelist IP) | On-demand | Ansible + Git approval |
| Backup configuration device di rete | Giornaliera | RANCID/Oxidized |

**Template per definire una standard change:**

```yaml
# standard-change-template.yaml
standard_change:
  id: "SC-2026-047"
  name: "Ubuntu Security Patch - Non-Critical"
  description: |
    Applicazione automatica di patch di sicurezza classificate
    come non-critical su server Ubuntu LTS in ambiente di produzione.
  owner: "team-platform"
  risk_level: "low"
  risk_score: 2  # scala 1-25

  preconditions:
    - "Server in maintenance window"
    - "Backup completato nelle ultime 24h"
    - "Nessun deployment applicativo in corso"
    - "Health check tutti i servizi green"

  procedure:
    - step: "Pre-validation"
      command: "ansible-playbook pre-check.yml"
      timeout: "5m"
      rollback_on_fail: false

    - step: "Apply patches"
      command: "ansible-playbook patch-ubuntu.yml"
      timeout: "30m"
      rollback_on_fail: true

    - step: "Reboot if required"
      command: "ansible-playbook reboot-if-needed.yml"
      timeout: "15m"
      rollback_on_fail: true

    - step: "Post-validation"
      command: "ansible-playbook post-check.yml"
      timeout: "10m"
      rollback_on_fail: true

  rollback:
    procedure: "ansible-playbook rollback-patch.yml"
    max_time: "15m"
    notification: "pagerduty-channel-ops"

  validation:
    smoke_test: "ansible-playbook smoke-test.yml"
    soak_period: "30m"
    soak_checks:
      - "CPU usage < 80%"
      - "Memory usage < 85%"
      - "HTTP 5xx rate < 0.1%"
      - "Response time p99 < 500ms"

  schedule:
    window: "Tuesday 02:00-06:00 UTC"
    blackout_periods:
      - "2026-12-20 to 2027-01-05"  # holiday freeze
      - "2026-11-25 to 2026-11-30"  # Black Friday

  approval:
    type: "pre-approved"
    approved_by: "CAB-2026-03-15"
    review_date: "2026-09-15"  # revisione semestrale
```

### 2.2 Normal Change

Una normal change richiede valutazione e approvazione formale prima dell'esecuzione. Il livello di scrutinio dipende dal rischio e dall'impatto.

**Sotto-categorie di normal change:**

| Categoria | Rischio | Approvazione | Lead time tipico |
|-----------|---------|--------------|------------------|
| Minor | Basso-medio | Change manager | 1-3 giorni |
| Significant | Medio-alto | CAB | 3-7 giorni |
| Major | Alto | CAB + senior management | 1-4 settimane |

**Workflow di una normal change:**

```
RFC Submitted
  │
  ├── Change Manager Review (1 giorno)
  │   ├── Completezza RFC
  │   ├── Risk assessment iniziale
  │   └── Classificazione rischio
  │
  ├── Technical Review (1-3 giorni)
  │   ├── Implementation plan review
  │   ├── Backout plan review
  │   ├── Test plan review
  │   └── CMDB impact analysis
  │
  ├── CAB Review (se required)
  │   ├── Risk/impact discussion
  │   ├── Schedule coordination
  │   ├── Resource allocation
  │   └── Approval/rejection/deferral
  │
  ├── Implementation
  │   ├── Pre-implementation checklist
  │   ├── Execution
  │   ├── Validation
  │   └── Rollback if needed
  │
  └── Post-Implementation Review
      ├── Success/failure determination
      ├── CMDB update
      ├── Lessons learned
      └── Metrics recording
```

**Esempio RFC strutturato per normal change:**

```yaml
# rfc-normal-change.yaml
rfc:
  id: "RFC-2026-0892"
  title: "Migrazione database PostgreSQL 15 → 17"
  type: "normal"
  category: "significant"
  priority: "medium"

  requester:
    name: "Marco Rossi"
    team: "Platform Engineering"
    date: "2026-05-01"

  description: |
    Migrazione del cluster PostgreSQL primario dalla versione 15.6
    alla versione 17.2 per beneficiare di miglioramenti di performance
    (incremental backup, parallel query improvements) e supporto LTS esteso.

  business_justification: |
    PostgreSQL 15 raggiunge EOL a novembre 2027. La migrazione anticipata
    riduce il rischio di operare su versione non supportata e abilita
    feature di performance che riducono i costi infrastrutturali del 15%.

  risk_assessment:
    likelihood: 2        # 1-5
    impact: 4            # 1-5
    risk_score: 8        # likelihood × impact
    risk_level: "medium" # 1-4 low, 5-9 medium, 10-16 high, 17-25 critical
    mitigations:
      - "Replica read-only mantenuta su PG15 per 48h post-migrazione"
      - "Backup completo pre-migrazione con point-in-time recovery testato"
      - "Migrazione eseguita su staging 7 giorni prima della produzione"
      - "Query regression test con pgbench e workload reale replayato"

  implementation_plan:
    phases:
      - phase: "Preparation"
        duration: "3 giorni"
        tasks:
          - "Setup PG17 replica"
          - "Esecuzione test suite su staging"
          - "Backup completo + verifica restore"

      - phase: "Migration"
        duration: "4 ore"
        window: "Sabato 02:00-06:00 UTC"
        tasks:
          - "Stop applicazioni (maintenance page)"
          - "Final WAL sync"
          - "pg_upgrade --link"
          - "Analyze statistiche"
          - "Riavvio applicazioni"
          - "Smoke test"

      - phase: "Validation"
        duration: "48 ore"
        tasks:
          - "Monitoring performance"
          - "Query regression check"
          - "Applicazione health check"

  backout_plan: |
    Se la migrazione fallisce o la validazione mostra regressioni:
    1. Stop applicazioni
    2. Switch DNS al cluster PG15 (ancora attivo come standby)
    3. Riavvio applicazioni
    4. Tempo stimato di rollback: 15 minuti

  test_plan:
    - "Unit test applicativi su staging con PG17"
    - "pgbench: throughput >= 95% del baseline PG15"
    - "Query regression: nessuna query con regressione > 20%"
    - "Backup/restore test su PG17"

  affected_cis:
    - "CI-DB-PROD-01 (PostgreSQL Primary)"
    - "CI-DB-PROD-02 (PostgreSQL Replica)"
    - "CI-APP-PROD-* (Application Servers)"

  schedule:
    requested_date: "2026-05-18"
    window: "02:00-06:00 UTC"
    blackout_check: "nessun conflitto"
```

### 2.3 Emergency Change

Una emergency change bypassa il normale processo di approvazione CAB a causa dell'urgenza. E riservata a situazioni in cui il ritardo causerebbe danni significativi al business o alla sicurezza.

**Criteri per classificare un change come emergency:**

1. Vulnerabilita di sicurezza attivamente sfruttata (CVE critico con exploit in-the-wild)
2. Outage in corso che impatta servizi critici di business
3. Data breach in atto che richiede contenimento immediato
4. Violazione di compliance che richiede remediation immediata
5. Degradazione severa delle performance che impatta SLA contrattuali

**Workflow emergency change:**

```
Incident/Security Alert
  │
  ├── On-Call Engineer valuta urgenza
  │   └── Conferma necessita emergency change
  │
  ├── ECAB convocato (telefono/chat)
  │   ├── Minimo: 1 change authority + 1 technical SME
  │   ├── Approvazione verbale registrata
  │   └── Tempo target: < 15 minuti
  │
  ├── Implementazione immediata
  │   ├── Documentazione minima pre-execute
  │   ├── Change eseguito
  │   └── Validation essenziale
  │
  └── Post-Implementation (entro 5 giorni lavorativi)
      ├── RFC retroattivo compilato
      ├── Full documentation completata
      ├── CAB review retrospettiva
      ├── Root cause analysis
      └── Valutazione: poteva essere evitata?
```

**Script di notifica ECAB:**

```bash
#!/usr/bin/env bash
# ecab-notify.sh — Notifica ECAB per emergency change
set -euo pipefail

CHANGE_ID="${1:?Uso: ecab-notify.sh <CHANGE_ID> <SEVERITY> <DESCRIPTION>}"
SEVERITY="${2:?Severity richiesta: critical|high}"
DESCRIPTION="${3:?Descrizione richiesta}"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Canali di notifica
SLACK_WEBHOOK="${ECAB_SLACK_WEBHOOK:?ECAB_SLACK_WEBHOOK non configurato}"
PAGERDUTY_KEY="${ECAB_PAGERDUTY_KEY:?ECAB_PAGERDUTY_KEY non configurato}"

# Notifica Slack
curl -sf -X POST "$SLACK_WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d "$(cat <<PAYLOAD
{
  "text": ":rotating_light: EMERGENCY CHANGE REQUEST",
  "blocks": [
    {
      "type": "header",
      "text": {"type": "plain_text", "text": "Emergency Change: ${CHANGE_ID}"}
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*Severity:* ${SEVERITY}"},
        {"type": "mrkdwn", "text": "*Timestamp:* ${TIMESTAMP}"},
        {"type": "mrkdwn", "text": "*Description:* ${DESCRIPTION}"}
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "ECAB members: confermate approvazione rispondendo con :white_check_mark:"
      }
    }
  ]
}
PAYLOAD
)" || echo "WARN: Slack notification failed"

# PagerDuty incident
curl -sf -X POST "https://events.pagerduty.com/v2/enqueue" \
  -H 'Content-Type: application/json' \
  -d "$(cat <<PAYLOAD
{
  "routing_key": "${PAGERDUTY_KEY}",
  "event_action": "trigger",
  "payload": {
    "summary": "ECAB Required: ${CHANGE_ID} - ${DESCRIPTION}",
    "severity": "${SEVERITY}",
    "source": "change-management",
    "timestamp": "${TIMESTAMP}",
    "custom_details": {
      "change_id": "${CHANGE_ID}",
      "type": "emergency"
    }
  }
}
PAYLOAD
)" || echo "WARN: PagerDuty notification failed"

echo "[${TIMESTAMP}] ECAB notification sent for ${CHANGE_ID}"
```

---

## 3. Il Processo CAB

### 3.1 Struttura e Composizione del CAB

Il Change Advisory Board (CAB) e un organo consultivo che valuta le normal change per rischio, impatto e scheduling. Non e un organo decisionale: la decisione finale spetta alla Change Authority designata, che puo essere il Change Manager o un senior manager a seconda del rischio.

**Composizione tipica del CAB:**

| Ruolo | Responsabilita | Presenza |
|-------|---------------|----------|
| Change Manager | Facilita il meeting, decisioni finali | Obbligatoria |
| Service Owner(s) | Valuta impatto sui servizi | Per i servizi impattati |
| Technical SME | Valuta fattibilita tecnica | Per la tecnologia coinvolta |
| Security Representative | Valuta rischi di sicurezza | Obbligatoria |
| Release Manager | Coordina con release schedule | Quando applicabile |
| Business Representative | Valuta impatto business | Per change significative |
| Operations Lead | Valuta impatto operativo | Obbligatoria |

### 3.2 Agenda CAB Strutturata

```
CAB Meeting Agenda — Cadenza: settimanale (Mercoledi 10:00)

1. Review change implementate dalla scorsa sessione (10 min)
   - Successi
   - Fallimenti e root cause
   - Change failed → azione correttiva

2. Review emergency change (5 min)
   - Ogni emergency change dall'ultimo CAB
   - Validazione retrospettiva
   - Azioni per prevenire recurrence

3. Normal change in coda per approvazione (30 min)
   - Per ogni RFC:
     a. Presentazione (requester, 3 min)
     b. Risk assessment review
     c. Implementation plan review
     d. Backout plan review
     e. Schedule conflict check
     f. Decisione: Approve / Reject / Defer / Request More Info

4. Change calendar review (10 min)
   - Upcoming maintenance windows
   - Freeze periods
   - Conflitti di scheduling

5. Metriche e trend (5 min)
   - Change success rate
   - Emergency change ratio
   - Mean lead time
   - Backlog
```

### 3.3 CAB Virtuale e Asincrono

Per organizzazioni DevOps-mature, il CAB tradizionale sincrono e un collo di bottiglia. L'alternativa e il CAB asincrono:

**Modello CAB Asincrono via Git:**

```yaml
# .github/PULL_REQUEST_TEMPLATE/change-request.md
---
name: Change Request
about: RFC per normal change
---

## Change Summary
<!-- Descrizione concisa del change -->

## Risk Assessment
- **Likelihood:** <!-- 1-5 -->
- **Impact:** <!-- 1-5 -->
- **Risk Score:** <!-- L × I -->
- **Risk Level:** <!-- low/medium/high/critical -->

## Implementation Plan
<!-- Step-by-step con tempi stimati -->

## Backout Plan
<!-- Come rollback se fallisce -->

## Test Plan
<!-- Come validare il successo -->

## Affected CIs
<!-- Configuration items impattati -->

## Schedule
- **Requested Window:** <!-- data e orario -->
- **Blackout Check:** <!-- conferma nessun conflitto -->

## Approvals Required
- [ ] Change Manager: @change-manager
- [ ] Security: @security-team
- [ ] Service Owner: @service-owner
```

**Vantaggi del CAB asincrono:**

1. I reviewer possono valutare quando hanno tempo, non in un meeting forzato
2. La discussione e documentata permanentemente nel PR
3. L'approvazione e tracciabile (Git blame, review approval)
4. Si elimina il bottleneck del meeting settimanale
5. Il pipeline puo enforcecare le approvazioni come gate

### 3.4 Metriche CAB

| Metrica | Target | Critico | Calcolo |
|---------|--------|---------|---------|
| Change Success Rate | > 95% | < 85% | (Change riuscite / Change totali) × 100 |
| Emergency Change Ratio | < 10% | > 25% | (Emergency / Totali) × 100 |
| Mean Lead Time (standard) | < 1h | > 24h | Media dal submit all'esecuzione |
| Mean Lead Time (normal) | < 5 giorni | > 15 giorni | Media dal RFC all'esecuzione |
| CAB Backlog | < 10 RFC | > 30 RFC | RFC in attesa di revisione |
| Change-related Incidents | < 5% | > 15% | Incidenti causati da change / totali |
| Failed Change MTTR | < 30 min | > 2h | Tempo medio per rollback |

---

## 4. Pipeline di Validazione Automatizzata

### 4.1 Architettura della Pipeline

La pipeline di validazione automatizzata e il cuore del change management moderno. Ogni change, indipendentemente dal tipo, attraversa una serie di gate automatizzati che verificano sicurezza, conformita e correttezza prima e dopo l'esecuzione.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHANGE VALIDATION PIPELINE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │  Submit   │──▶│ Classify │──▶│Authorize │──▶│ Schedule │    │
│  │   RFC     │   │  Change  │   │  Change  │   │  Window  │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│                                                      │          │
│                                                      ▼          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │  Close   │◀──│   Soak   │◀──│  Smoke   │◀──│ Execute  │    │
│  │  Change  │   │   Test   │   │   Test   │   │  Change  │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│       ▲              │              │              │             │
│       │         FAIL │         FAIL │         FAIL │             │
│       │              ▼              ▼              ▼             │
│       │         ┌──────────────────────────────────────┐        │
│       │         │         AUTO-ROLLBACK                 │        │
│       │         │   + Alert + Incident Creation         │        │
│       │         └──────────────────────────────────────┘        │
│       │                         │                                │
│       └─────────────────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Pipeline tipica

```
Submit change request
  → Auto-classify: standard / normal / emergency
  → If standard:
       → Pre-validation (lint, test, security scan)
       → Schedule (off-peak window)
       → Execute via Ansible/script
       → Smoke test 5min
       → Soak test 30min monitoring
       → If all green: close
       → If fail: auto-rollback + page IC
  → If normal: queue per CAB
  → If emergency: page IC immediately
```

### 4.3 Implementazione Pipeline con GitHub Actions

```yaml
# .github/workflows/change-pipeline.yml
name: Infrastructure Change Pipeline

on:
  push:
    branches: [main]
    paths:
      - 'infrastructure/**'
      - 'ansible/**'
      - 'terraform/**'

permissions:
  contents: read
  pull-requests: write
  issues: write

env:
  CHANGE_ID: "CHG-${{ github.run_number }}"
  TF_VAR_environment: "production"

jobs:
  classify:
    name: "Classify Change"
    runs-on: ubuntu-latest
    outputs:
      change_type: ${{ steps.classify.outputs.type }}
      risk_score: ${{ steps.classify.outputs.risk }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Classify change type and risk
        id: classify
        run: |
          CHANGED_FILES=$(git diff --name-only HEAD~1)
          RISK=0
          TYPE="standard"

          # File critici aumentano il rischio
          if echo "$CHANGED_FILES" | grep -q "terraform/modules/networking"; then
            RISK=$((RISK + 10))
            TYPE="normal"
          fi
          if echo "$CHANGED_FILES" | grep -q "terraform/modules/database"; then
            RISK=$((RISK + 8))
            TYPE="normal"
          fi
          if echo "$CHANGED_FILES" | grep -q "ansible/roles/security"; then
            RISK=$((RISK + 6))
          fi
          if echo "$CHANGED_FILES" | grep -q "ansible/roles/patching"; then
            RISK=$((RISK + 2))
          fi

          # Numero di file modificati
          FILE_COUNT=$(echo "$CHANGED_FILES" | wc -l)
          if [ "$FILE_COUNT" -gt 20 ]; then
            RISK=$((RISK + 5))
            TYPE="normal"
          fi

          echo "type=${TYPE}" >> "$GITHUB_OUTPUT"
          echo "risk=${RISK}" >> "$GITHUB_OUTPUT"
          echo "Change classified as: ${TYPE}, risk score: ${RISK}"

  pre-validate:
    name: "Pre-Change Validation"
    needs: classify
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Lint Terraform
        run: |
          terraform fmt -check -recursive infrastructure/
          terraform validate infrastructure/

      - name: Lint Ansible
        run: |
          pip install ansible-lint
          ansible-lint ansible/

      - name: Security scan
        run: |
          # Checkov per Terraform
          pip install checkov
          checkov -d infrastructure/ --framework terraform \
            --output json --output-file checkov-report.json

          # Verifica nessun finding critico
          CRITICAL=$(jq '[.results.failed_checks[]
            | select(.severity == "CRITICAL")] | length' \
            checkov-report.json)
          if [ "$CRITICAL" -gt 0 ]; then
            echo "CRITICAL security findings: $CRITICAL"
            exit 1
          fi

      - name: Policy check (OPA)
        run: |
          # Open Policy Agent per compliance
          terraform plan -out=tfplan infrastructure/
          terraform show -json tfplan > tfplan.json
          opa eval --data policies/ --input tfplan.json \
            "data.terraform.deny[msg]" --format pretty

      - name: CMDB impact check
        run: |
          # Verifica CI impattati
          python3 scripts/cmdb-impact-check.py \
            --changes "$(git diff --name-only HEAD~1)" \
            --cmdb-api "$CMDB_API_URL"

  execute:
    name: "Execute Change"
    needs: [classify, pre-validate]
    if: needs.classify.outputs.change_type == 'standard'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Check maintenance window
        run: |
          CURRENT_HOUR=$(date -u +%H)
          CURRENT_DOW=$(date -u +%u)
          # Maintenance window: Mar-Gio 02:00-06:00 UTC
          if [ "$CURRENT_DOW" -lt 2 ] || [ "$CURRENT_DOW" -gt 4 ]; then
            echo "ERRORE: fuori dalla maintenance window"
            exit 1
          fi
          if [ "$CURRENT_HOUR" -lt 2 ] || [ "$CURRENT_HOUR" -ge 6 ]; then
            echo "ERRORE: fuori dall'orario consentito"
            exit 1
          fi

      - name: Create snapshot/checkpoint
        run: |
          ansible-playbook ansible/playbooks/create-checkpoint.yml \
            -e "change_id=$CHANGE_ID"

      - name: Execute change
        id: execute
        run: |
          ansible-playbook ansible/playbooks/apply-change.yml \
            -e "change_id=$CHANGE_ID" \
            -e "@changes/current-change-vars.yml"

      - name: Smoke test
        id: smoke
        run: |
          ansible-playbook ansible/playbooks/smoke-test.yml \
            -e "change_id=$CHANGE_ID" \
            --timeout 300  # 5 minuti

      - name: Soak test (30 min monitoring)
        id: soak
        run: |
          python3 scripts/soak-test.py \
            --duration 1800 \
            --check-interval 30 \
            --prometheus-url "$PROMETHEUS_URL" \
            --thresholds config/soak-thresholds.yml \
            --change-id "$CHANGE_ID"

  rollback:
    name: "Auto-Rollback"
    needs: execute
    if: failure()
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Execute rollback
        run: |
          ansible-playbook ansible/playbooks/rollback-change.yml \
            -e "change_id=$CHANGE_ID"

      - name: Verify rollback
        run: |
          ansible-playbook ansible/playbooks/smoke-test.yml \
            -e "change_id=$CHANGE_ID" \
            -e "rollback_verification=true"

      - name: Create incident
        run: |
          python3 scripts/create-incident.py \
            --change-id "$CHANGE_ID" \
            --severity "high" \
            --description "Auto-rollback triggered for $CHANGE_ID"

      - name: Notify
        run: |
          python3 scripts/notify-teams.py \
            --channel "#ops-alerts" \
            --message "ROLLBACK executed for $CHANGE_ID"
```

### 4.4 Script di Soak Test

```python
#!/usr/bin/env python3
"""soak-test.py — Monitoraggio soak test post-change.

Interroga Prometheus per verificare che le metriche rimangano
entro le soglie definite per tutta la durata del soak period.
"""

import argparse
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests
import yaml


@dataclass(frozen=True)
class ThresholdCheck:
    name: str
    query: str
    operator: str  # lt, gt, le, ge, eq
    value: float
    severity: str  # critical, warning


def load_thresholds(path: str) -> list[ThresholdCheck]:
    with open(path) as f:
        raw = yaml.safe_load(f)
    return [ThresholdCheck(**t) for t in raw["thresholds"]]


def query_prometheus(url: str, query: str) -> float | None:
    resp = requests.get(
        f"{url}/api/v1/query",
        params={"query": query},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("data", {}).get("result", [])
    if not results:
        return None
    return float(results[0]["value"][1])


OPS = {
    "lt": lambda a, b: a < b,
    "gt": lambda a, b: a > b,
    "le": lambda a, b: a <= b,
    "ge": lambda a, b: a >= b,
    "eq": lambda a, b: a == b,
}


def evaluate(check: ThresholdCheck, actual: float | None) -> bool:
    if actual is None:
        print(f"  WARN: nessun dato per '{check.name}'")
        return check.severity != "critical"
    op = OPS[check.operator]
    passed = op(actual, check.value)
    status = "PASS" if passed else f"FAIL ({actual} vs {check.operator} {check.value})"
    print(f"  [{status}] {check.name}: {actual}")
    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description="Soak test post-change")
    parser.add_argument("--duration", type=int, required=True, help="Durata in secondi")
    parser.add_argument("--check-interval", type=int, default=30, help="Intervallo check")
    parser.add_argument("--prometheus-url", required=True)
    parser.add_argument("--thresholds", required=True, help="File YAML soglie")
    parser.add_argument("--change-id", required=True)
    args = parser.parse_args()

    thresholds = load_thresholds(args.thresholds)
    start = time.monotonic()
    failures = 0
    critical_failures = 0
    iteration = 0

    print(f"Soak test avviato per change {args.change_id}")
    print(f"Durata: {args.duration}s, intervallo: {args.check_interval}s")
    print(f"Soglie caricate: {len(thresholds)}")

    while time.monotonic() - start < args.duration:
        iteration += 1
        ts = datetime.now(tz=timezone.utc).isoformat()
        print(f"\n--- Iterazione {iteration} [{ts}] ---")

        for check in thresholds:
            actual = query_prometheus(args.prometheus_url, check.query)
            if not evaluate(check, actual):
                failures += 1
                if check.severity == "critical":
                    critical_failures += 1

        if critical_failures > 0:
            print(f"\nSOAK TEST FAILED: {critical_failures} critical failure(s)")
            sys.exit(1)

        time.sleep(args.check_interval)

    if failures > 3:
        print(f"\nSOAK TEST WARNING: {failures} warning failure(s) totali")
        sys.exit(1)

    print(f"\nSOAK TEST PASSED: {iteration} iterazioni completate senza failure critici")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

**File soglie per soak test:**

```yaml
# config/soak-thresholds.yml
thresholds:
  - name: "CPU Usage"
    query: 'avg(100 - (rate(node_cpu_seconds_total{mode="idle"}[5m]) * 100))'
    operator: "lt"
    value: 80
    severity: "critical"

  - name: "Memory Usage"
    query: '(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100'
    operator: "lt"
    value: 85
    severity: "critical"

  - name: "HTTP 5xx Rate"
    query: 'sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100'
    operator: "lt"
    value: 0.1
    severity: "critical"

  - name: "Response Time p99"
    query: 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))'
    operator: "lt"
    value: 0.5
    severity: "critical"

  - name: "Disk Usage"
    query: '(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100'
    operator: "lt"
    value: 90
    severity: "warning"

  - name: "Error Log Rate"
    query: 'sum(rate(log_messages_total{level="error"}[5m]))'
    operator: "lt"
    value: 10
    severity: "warning"

  - name: "Connection Pool Saturation"
    query: 'sum(pg_stat_activity_count) / sum(pg_settings_max_connections) * 100'
    operator: "lt"
    value: 80
    severity: "warning"
```

---

## 5. Pre-Change Validation

### 5.1 Checklist di Pre-Validation

La pre-validation e l'insieme di controlli automatizzati eseguiti prima di applicare qualsiasi change all'infrastruttura. L'obiettivo e intercettare problemi prima che raggiungano la produzione.

**Categorie di check:**

| Categoria | Check | Strumento | Bloccante |
|-----------|-------|-----------|-----------|
| Sintassi | Terraform fmt/validate | terraform | Si |
| Sintassi | Ansible lint | ansible-lint | Si |
| Sintassi | YAML/JSON schema validation | yamllint, jsonschema | Si |
| Sicurezza | Secret detection | gitleaks, trufflehog | Si |
| Sicurezza | IaC security scan | checkov, tfsec | Si (critical) |
| Sicurezza | CVE check dipendenze | trivy, grype | Si (critical/high) |
| Policy | Compliance check | OPA/Rego, Sentinel | Si |
| Policy | Cost estimation | infracost | No (warning) |
| Ambiente | Health check target host | custom script | Si |
| Ambiente | Backup recente verificato | custom script | Si |
| Ambiente | Maintenance window valida | custom script | Si |
| Ambiente | Nessun deploy in corso | deployment lock | Si |
| CMDB | CI impattati identificati | CMDB API | No (warning) |
| CMDB | Dipendenze verificate | CMDB API | No (warning) |

### 5.2 Pre-Validation Ansible Playbook

```yaml
# ansible/playbooks/pre-check.yml
---
- name: Pre-Change Validation
  hosts: "{{ target_hosts }}"
  gather_facts: true
  become: false

  vars:
    min_disk_free_gb: 10
    min_memory_free_mb: 512
    max_cpu_load_percent: 80
    max_uptime_days: 365
    required_backup_age_hours: 24

  tasks:
    # === Connectivity ===
    - name: Verify SSH connectivity
      ansible.builtin.ping:

    - name: Verify sudo access
      ansible.builtin.command: sudo -n true
      changed_when: false

    # === Disk Space ===
    - name: Check disk space
      ansible.builtin.shell: |
        df -BG / | tail -1 | awk '{print $4}' | tr -d 'G'
      register: disk_free
      changed_when: false

    - name: Fail if disk space insufficient
      ansible.builtin.fail:
        msg: >
          Spazio disco insufficiente: {{ disk_free.stdout }}GB liberi,
          richiesti {{ min_disk_free_gb }}GB
      when: disk_free.stdout | int < min_disk_free_gb

    # === Memory ===
    - name: Check available memory
      ansible.builtin.shell: |
        free -m | awk '/^Mem:/ {print $7}'
      register: mem_available
      changed_when: false

    - name: Fail if memory insufficient
      ansible.builtin.fail:
        msg: >
          Memoria insufficiente: {{ mem_available.stdout }}MB disponibili,
          richiesti {{ min_memory_free_mb }}MB
      when: mem_available.stdout | int < min_memory_free_mb

    # === CPU Load ===
    - name: Check CPU load average
      ansible.builtin.shell: |
        nproc_val=$(nproc)
        load=$(awk '{print $1}' /proc/loadavg)
        awk "BEGIN {printf \"%.0f\", ($load / $nproc_val) * 100}"
      register: cpu_load
      changed_when: false

    - name: Fail if CPU overloaded
      ansible.builtin.fail:
        msg: "CPU load troppo alto: {{ cpu_load.stdout }}%"
      when: cpu_load.stdout | int > max_cpu_load_percent

    # === Services Health ===
    - name: Check critical services running
      ansible.builtin.systemd:
        name: "{{ item }}"
      register: service_status
      loop: "{{ critical_services | default(['sshd']) }}"

    - name: Verify services are active
      ansible.builtin.fail:
        msg: "Servizio {{ item.item }} non attivo"
      when: item.status.ActiveState != 'active'
      loop: "{{ service_status.results }}"
      loop_control:
        label: "{{ item.item }}"

    # === Backup Verification ===
    - name: Check last backup timestamp
      ansible.builtin.shell: |
        if [ -f /var/log/backup-last-success ]; then
          cat /var/log/backup-last-success
        else
          echo "0"
        fi
      register: last_backup
      changed_when: false

    - name: Verify backup recency
      ansible.builtin.fail:
        msg: "Backup troppo vecchio o assente. Ultimo backup: {{ last_backup.stdout }}"
      when: >
        last_backup.stdout == "0" or
        ((ansible_date_time.epoch | int) - (last_backup.stdout | int)) > (required_backup_age_hours * 3600)

    # === Network ===
    - name: Verify DNS resolution
      ansible.builtin.command: nslookup "{{ dns_test_hostname | default('dns.google') }}"
      changed_when: false

    - name: Verify NTP sync
      ansible.builtin.shell: |
        timedatectl show -p NTPSynchronized --value
      register: ntp_sync
      changed_when: false

    - name: Fail if NTP not synchronized
      ansible.builtin.fail:
        msg: "NTP non sincronizzato. Clock drift puo causare problemi."
      when: ntp_sync.stdout != "yes"

    # === Pending Changes ===
    - name: Check for pending reboot
      ansible.builtin.stat:
        path: /var/run/reboot-required
      register: reboot_required

    - name: Warn if reboot pending
      ansible.builtin.debug:
        msg: "WARNING: reboot pendente su {{ inventory_hostname }}"
      when: reboot_required.stat.exists

    # === Summary ===
    - name: Pre-validation summary
      ansible.builtin.debug:
        msg: |
          Pre-validation completata per {{ inventory_hostname }}:
          - Disco libero: {{ disk_free.stdout }}GB
          - Memoria disponibile: {{ mem_available.stdout }}MB
          - CPU load: {{ cpu_load.stdout }}%
          - NTP sync: {{ ntp_sync.stdout }}
          - Reboot pendente: {{ reboot_required.stat.exists }}
```

### 5.3 Pre-Validation con Open Policy Agent

Open Policy Agent (OPA) consente di definire policy dichiarative che vengono evaluate automaticamente contro il piano di change. Questo garantisce compliance senza intervento manuale.

```rego
# policies/change-validation.rego
package terraform.change_validation

import rego.v1

# Nega change che rimuovono risorse di produzione senza approvazione
deny contains msg if {
    some resource in input.resource_changes
    resource.change.actions[_] == "delete"
    contains(resource.address, "prod")
    not input.metadata.cab_approved
    msg := sprintf(
        "Eliminazione risorsa di produzione '%s' richiede approvazione CAB",
        [resource.address],
    )
}

# Nega security group con accesso 0.0.0.0/0
deny contains msg if {
    some resource in input.resource_changes
    resource.type == "aws_security_group_rule"
    resource.change.after.cidr_blocks[_] == "0.0.0.0/0"
    resource.change.after.type == "ingress"
    msg := sprintf(
        "Security group '%s' non puo avere ingress da 0.0.0.0/0",
        [resource.address],
    )
}

# Nega istanze senza tag obbligatori
deny contains msg if {
    some resource in input.resource_changes
    resource.type == "aws_instance"
    required_tags := {"Environment", "Owner", "CostCenter", "ChangeID"}
    provided_tags := {tag | some tag, _ in resource.change.after.tags}
    missing := required_tags - provided_tags
    count(missing) > 0
    msg := sprintf(
        "Istanza '%s' manca tag obbligatori: %v",
        [resource.address, missing],
    )
}

# Nega database pubblicamente accessibili
deny contains msg if {
    some resource in input.resource_changes
    resource.type == "aws_db_instance"
    resource.change.after.publicly_accessible == true
    msg := sprintf(
        "Database '%s' non puo essere pubblicamente accessibile",
        [resource.address],
    )
}

# Warning per change durante freeze period
warn contains msg if {
    freeze_periods := [
        {"start": "2026-12-20", "end": "2027-01-05", "reason": "Holiday Freeze"},
        {"start": "2026-11-25", "end": "2026-11-30", "reason": "Black Friday"},
    ]
    some period in freeze_periods
    time.now_ns() >= time.parse_rfc3339_ns(concat("", [period.start, "T00:00:00Z"]))
    time.now_ns() <= time.parse_rfc3339_ns(concat("", [period.end, "T23:59:59Z"]))
    msg := sprintf("Change durante freeze period: %s", [period.reason])
}
```

---

## 6. Post-Change Verification

### 6.1 Struttura della Verifica Post-Change

La verifica post-change si articola in tre fasi sequenziali, ciascuna con criteri di successo specifici. Se una fase fallisce, si attiva il rollback automatico.

| Fase | Durata | Scopo | Criteri di successo |
|------|--------|-------|---------------------|
| **Immediate Check** | 0-30 secondi | Verifica che il change sia stato applicato | Servizio raggiungibile, processo attivo |
| **Smoke Test** | 1-5 minuti | Funzionalita core operative | Endpoint principali rispondono, login funziona |
| **Soak Test** | 15-60 minuti | Stabilita sotto carico reale | Metriche entro soglie, no regressioni |

### 6.2 Smoke Test Playbook

```yaml
# ansible/playbooks/smoke-test.yml
---
- name: Post-Change Smoke Test
  hosts: "{{ target_hosts }}"
  gather_facts: false
  become: false

  vars:
    smoke_test_timeout: 300  # 5 minuti
    health_endpoints: []
    expected_services: []

  tasks:
    # === Service Checks ===
    - name: Verify target services are running
      ansible.builtin.systemd:
        name: "{{ item }}"
      register: service_checks
      loop: "{{ expected_services }}"
      until: service_checks is not failed
      retries: 10
      delay: 5

    # === Port Checks ===
    - name: Verify listening ports
      ansible.builtin.wait_for:
        host: "{{ inventory_hostname }}"
        port: "{{ item.port }}"
        timeout: 30
        state: started
      loop: "{{ expected_ports | default([]) }}"
      loop_control:
        label: "{{ item.name }}:{{ item.port }}"

    # === HTTP Health Checks ===
    - name: Verify HTTP health endpoints
      ansible.builtin.uri:
        url: "{{ item.url }}"
        method: GET
        status_code: "{{ item.expected_status | default(200) }}"
        timeout: 10
        validate_certs: "{{ item.validate_certs | default(true) }}"
      register: health_results
      loop: "{{ health_endpoints }}"
      loop_control:
        label: "{{ item.name }}"
      retries: 5
      delay: 10
      until: health_results is not failed

    # === Database Connectivity ===
    - name: Verify database connectivity
      ansible.builtin.command: >
        pg_isready -h {{ db_host | default('localhost') }}
        -p {{ db_port | default(5432) }}
        -U {{ db_user | default('app') }}
      changed_when: false
      when: check_database | default(false)

    # === Log Error Check ===
    - name: Check for new errors in logs
      ansible.builtin.shell: |
        journalctl --since "5 minutes ago" -p err --no-pager -q | wc -l
      register: error_count
      changed_when: false

    - name: Warn if errors detected
      ansible.builtin.debug:
        msg: "WARNING: {{ error_count.stdout }} errori nel log negli ultimi 5 minuti"
      when: error_count.stdout | int > 0

    - name: Fail if excessive errors
      ansible.builtin.fail:
        msg: "Troppi errori post-change: {{ error_count.stdout }}"
      when: error_count.stdout | int > 50

    # === Custom Application Checks ===
    - name: Run application-specific smoke tests
      ansible.builtin.script: "scripts/app-smoke-test.sh"
      register: app_smoke
      when: app_smoke_script is defined

    # === Summary ===
    - name: Smoke test result
      ansible.builtin.debug:
        msg: |
          Smoke test completato per {{ inventory_hostname }}:
          - Servizi verificati: {{ expected_services | length }}
          - Health endpoint verificati: {{ health_endpoints | length }}
          - Errori rilevati: {{ error_count.stdout }}
          - Risultato: PASS
```

### 6.3 Monitoring-Based Verification con Prometheus

```python
#!/usr/bin/env python3
"""post-change-verify.py — Verifica post-change basata su Prometheus.

Confronta le metriche attuali con il baseline pre-change per
identificare regressioni statisticamente significative.
"""

import argparse
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests


@dataclass(frozen=True)
class MetricComparison:
    name: str
    query: str
    max_deviation_percent: float
    direction: str  # "higher_is_worse" | "lower_is_worse"


COMPARISONS = [
    MetricComparison(
        name="HTTP Latency p99",
        query='histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))',
        max_deviation_percent=20,
        direction="higher_is_worse",
    ),
    MetricComparison(
        name="Error Rate",
        query='sum(rate(http_requests_total{status=~"5.."}[5m]))',
        max_deviation_percent=50,
        direction="higher_is_worse",
    ),
    MetricComparison(
        name="Throughput",
        query='sum(rate(http_requests_total[5m]))',
        max_deviation_percent=30,
        direction="lower_is_worse",
    ),
    MetricComparison(
        name="CPU Usage",
        query='avg(100 - rate(node_cpu_seconds_total{mode="idle"}[5m]) * 100)',
        max_deviation_percent=25,
        direction="higher_is_worse",
    ),
]


def query_prometheus(url: str, query: str, ts: float | None = None) -> float | None:
    params = {"query": query}
    if ts:
        params["time"] = str(ts)
    resp = requests.get(f"{url}/api/v1/query", params=params, timeout=10)
    resp.raise_for_status()
    results = resp.json().get("data", {}).get("result", [])
    if not results:
        return None
    return float(results[0]["value"][1])


def compare(
    baseline: float, current: float, comp: MetricComparison
) -> tuple[bool, float]:
    if baseline == 0:
        return True, 0.0
    deviation = ((current - baseline) / baseline) * 100
    if comp.direction == "higher_is_worse":
        passed = deviation <= comp.max_deviation_percent
    else:
        passed = deviation >= -comp.max_deviation_percent
    return passed, deviation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prometheus-url", required=True)
    parser.add_argument("--baseline-offset", type=int, default=3600,
                        help="Secondi prima del change per baseline")
    parser.add_argument("--change-timestamp", type=float, required=True,
                        help="Epoch timestamp del change")
    args = parser.parse_args()

    baseline_ts = args.change_timestamp - args.baseline_offset
    current_ts = time.time()
    failures = []

    print("Post-Change Metric Comparison")
    print(f"Baseline: {datetime.fromtimestamp(baseline_ts, tz=timezone.utc).isoformat()}")
    print(f"Current:  {datetime.fromtimestamp(current_ts, tz=timezone.utc).isoformat()}")
    print("-" * 60)

    for comp in COMPARISONS:
        baseline_val = query_prometheus(args.prometheus_url, comp.query, baseline_ts)
        current_val = query_prometheus(args.prometheus_url, comp.query, current_ts)

        if baseline_val is None or current_val is None:
            print(f"  SKIP: {comp.name} - dati insufficienti")
            continue

        passed, deviation = compare(baseline_val, current_val, comp)
        status = "PASS" if passed else "FAIL"
        print(
            f"  [{status}] {comp.name}: "
            f"baseline={baseline_val:.4f}, current={current_val:.4f}, "
            f"deviation={deviation:+.1f}% (max={comp.max_deviation_percent}%)"
        )
        if not passed:
            failures.append(comp.name)

    if failures:
        print(f"\nVERIFICATION FAILED: regressioni in {failures}")
        sys.exit(1)
    print("\nVERIFICATION PASSED")


if __name__ == "__main__":
    main()
```

---

## 7. Strategie di Deployment

### 7.1 Canary Deployment per Infrastruttura

Il canary deployment applica il change a un sottoinsieme ridotto dell'infrastruttura, monitora i risultati, e solo se positivi estende il change al resto. E la strategia piu sicura per change infrastrutturali ad alto rischio.

**Fasi del canary deployment:**

```
Fase 1: Canary (5% del fleet)
  ├── Applica change a 1-2 server
  ├── Monitora per 30-60 minuti
  ├── Confronta metriche canary vs baseline
  └── Se OK → procedi a Fase 2
      Se KO → rollback canary, stop

Fase 2: Expansion (25% del fleet)
  ├── Applica change a 25% dei server
  ├── Monitora per 30-60 minuti
  ├── Verifica metriche aggregate
  └── Se OK → procedi a Fase 3
      Se KO → rollback 25%, stop

Fase 3: Majority (75% del fleet)
  ├── Applica change a 75% dei server
  ├── Monitora per 15-30 minuti
  └── Se OK → procedi a Fase 4
      Se KO → rollback 75%, stop

Fase 4: Complete (100% del fleet)
  ├── Applica change ai server rimanenti
  ├── Soak test finale (30 min)
  └── Close change
```

**Implementazione canary con Ansible:**

```yaml
# ansible/playbooks/canary-deploy.yml
---
- name: Canary Deployment - Phase 1
  hosts: "{{ target_group }}"
  serial: "5%"
  max_fail_percentage: 0

  pre_tasks:
    - name: Remove from load balancer
      ansible.builtin.uri:
        url: "{{ lb_api }}/pools/{{ lb_pool_id }}/members/{{ inventory_hostname }}"
        method: DELETE
        headers:
          Authorization: "Bearer {{ lb_token }}"
      delegate_to: localhost

    - name: Wait for connections to drain
      ansible.builtin.pause:
        seconds: 30

  roles:
    - role: apply-change
      vars:
        change_id: "{{ change_id }}"

  post_tasks:
    - name: Run smoke test
      ansible.builtin.include_tasks: tasks/smoke-test.yml

    - name: Re-add to load balancer
      ansible.builtin.uri:
        url: "{{ lb_api }}/pools/{{ lb_pool_id }}/members"
        method: POST
        body_format: json
        body:
          address: "{{ inventory_hostname }}"
          port: "{{ app_port }}"
        headers:
          Authorization: "Bearer {{ lb_token }}"
      delegate_to: localhost

    - name: Wait for canary soak
      ansible.builtin.pause:
        minutes: 30
      run_once: true

    - name: Verify canary metrics
      ansible.builtin.script: scripts/canary-verify.sh
      delegate_to: localhost
      run_once: true
      register: canary_result

    - name: Fail if canary unhealthy
      ansible.builtin.fail:
        msg: "Canary verification fallita: {{ canary_result.stdout }}"
      when: canary_result.rc != 0
```

### 7.2 Blue-Green Deployment

Il blue-green deployment mantiene due ambienti identici (blue = attivo, green = standby). Il change viene applicato all'ambiente standby, testato, e poi il traffico viene switchato.

**Architettura:**

```
             ┌──────────────┐
             │ Load Balancer │
             │   / DNS       │
             └──────┬───────┘
                    │
          ┌─────────┴─────────┐
          │                   │
    ┌─────▼─────┐      ┌─────▼─────┐
    │   BLUE    │      │   GREEN   │
    │  (Active) │      │ (Standby) │
    │           │      │           │
    │ App v1.0  │      │ App v1.1  │
    │ Config A  │      │ Config B  │
    │           │      │           │
    └───────────┘      └───────────┘
```

**Terraform per blue-green:**

```hcl
# infrastructure/blue-green/main.tf

variable "active_environment" {
  description = "Ambiente attualmente attivo: blue o green"
  type        = string
  default     = "blue"

  validation {
    condition     = contains(["blue", "green"], var.active_environment)
    error_message = "active_environment deve essere 'blue' o 'green'."
  }
}

variable "deploy_version" {
  description = "Versione da deployare nell'ambiente standby"
  type        = string
}

locals {
  standby_environment = var.active_environment == "blue" ? "green" : "blue"
}

# Blue environment
module "blue" {
  source = "./modules/app-environment"

  environment_name = "blue"
  instance_count   = var.active_environment == "blue" ? var.production_instances : var.standby_instances
  app_version      = var.active_environment == "blue" ? var.current_version : var.deploy_version
  instance_type    = var.instance_type
  subnet_ids       = var.private_subnet_ids
}

# Green environment
module "green" {
  source = "./modules/app-environment"

  environment_name = "green"
  instance_count   = var.active_environment == "green" ? var.production_instances : var.standby_instances
  app_version      = var.active_environment == "green" ? var.current_version : var.deploy_version
  instance_type    = var.instance_type
  subnet_ids       = var.private_subnet_ids
}

# Load balancer target group assignment
resource "aws_lb_listener_rule" "app" {
  listener_arn = var.lb_listener_arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = var.active_environment == "blue" ? module.blue.target_group_arn : module.green.target_group_arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}

# Output per verifica
output "active_environment" {
  value = var.active_environment
}

output "standby_environment" {
  value = local.standby_environment
}

output "active_target_group" {
  value = var.active_environment == "blue" ? module.blue.target_group_arn : module.green.target_group_arn
}
```

### 7.3 Rolling Update

Il rolling update aggiorna i server uno alla volta (o in batch), mantenendo sempre una percentuale minima di server operativi. E il compromesso tra sicurezza del canary e velocita del blue-green.

**Parametri critici:**

| Parametro | Descrizione | Valore tipico |
|-----------|-------------|---------------|
| `max_unavailable` | Massimi server non disponibili contemporaneamente | 1 o 25% |
| `max_surge` | Server aggiuntivi temporanei durante update | 1 o 25% |
| `min_ready_seconds` | Tempo minimo in stato ready prima di procedere | 30s |
| `progress_deadline` | Timeout per dichiarare l'update fallito | 600s |

**Ansible rolling update:**

```yaml
# ansible/playbooks/rolling-update.yml
---
- name: Rolling Update
  hosts: app_servers
  serial: 1  # un server alla volta
  max_fail_percentage: 0  # zero tolerance

  pre_tasks:
    - name: Pre-flight health check
      ansible.builtin.uri:
        url: "http://{{ inventory_hostname }}:{{ app_port }}/health"
        status_code: 200
      register: pre_health
      failed_when: pre_health.status != 200

    - name: Graceful removal from load balancer
      ansible.builtin.uri:
        url: "{{ lb_api }}/deregister"
        method: POST
        body_format: json
        body:
          instance: "{{ inventory_hostname }}"
      delegate_to: localhost

    - name: Wait for in-flight requests to complete
      ansible.builtin.pause:
        seconds: "{{ drain_timeout | default(30) }}"

  tasks:
    - name: Apply update
      ansible.builtin.include_role:
        name: apply-change

  post_tasks:
    - name: Wait for service ready
      ansible.builtin.uri:
        url: "http://{{ inventory_hostname }}:{{ app_port }}/health"
        status_code: 200
      register: post_health
      retries: 30
      delay: 5
      until: post_health.status == 200

    - name: Re-register in load balancer
      ansible.builtin.uri:
        url: "{{ lb_api }}/register"
        method: POST
        body_format: json
        body:
          instance: "{{ inventory_hostname }}"
      delegate_to: localhost

    - name: Stabilization period
      ansible.builtin.pause:
        seconds: "{{ stabilization_seconds | default(60) }}"

    - name: Verify no errors post-update
      ansible.builtin.shell: |
        journalctl -u "{{ app_service }}" --since "2 minutes ago" -p err --no-pager -q | wc -l
      register: recent_errors
      changed_when: false

    - name: Fail if errors detected
      ansible.builtin.fail:
        msg: "{{ recent_errors.stdout }} errori rilevati post-update su {{ inventory_hostname }}"
      when: recent_errors.stdout | int > 5
```

---

## 8. Rollback Automation

### 8.1 Principi di Rollback

Un rollback efficace deve essere:

1. **Automatico**: triggerato da condizioni misurabili, non da decisioni umane in panico
2. **Testato**: il rollback plan deve essere testato con la stessa rigorosita del change
3. **Veloce**: il tempo di rollback deve essere una frazione del tempo di implementazione
4. **Idempotente**: eseguire il rollback multiplo volte non deve causare danni
5. **Completo**: deve ripristinare stato, dati, configurazione, DNS, tutto

### 8.2 Strategie di Rollback per Tipo di Change

| Tipo di Change | Strategia Rollback | Tempo target | Complessita |
|----------------|-------------------|--------------|-------------|
| Config file update | Restore da backup/git revert | < 2 min | Bassa |
| Package update | Downgrade package | < 5 min | Media |
| OS patch | Snapshot restore | < 10 min | Media |
| Database migration | Reverse migration script | < 15 min | Alta |
| Network change | Config restore | < 5 min | Media |
| DNS change | TTL-based revert | TTL-dependent | Bassa |
| Blue-green deploy | Switch traffic back | < 1 min | Bassa |
| Terraform change | terraform apply (precedente) | < 10 min | Media |
| Kubernetes deploy | kubectl rollout undo | < 2 min | Bassa |

### 8.3 Rollback Playbook Universale

```yaml
# ansible/playbooks/rollback-change.yml
---
- name: Automated Rollback
  hosts: "{{ target_hosts }}"
  gather_facts: true
  become: true

  vars:
    rollback_timeout: 900  # 15 minuti max
    notification_channel: "#ops-incidents"

  tasks:
    - name: Start rollback timer
      ansible.builtin.set_fact:
        rollback_start: "{{ ansible_date_time.epoch }}"

    - name: Notify rollback start
      ansible.builtin.uri:
        url: "{{ slack_webhook }}"
        method: POST
        body_format: json
        body:
          text: ":warning: ROLLBACK avviato per change {{ change_id }} su {{ inventory_hostname }}"
      delegate_to: localhost

    # === Determine rollback strategy ===
    - name: Check for snapshot
      ansible.builtin.stat:
        path: "/var/backups/change-snapshots/{{ change_id }}"
      register: snapshot_exists

    - name: Check for git-managed config
      ansible.builtin.stat:
        path: "/etc/change-managed/.git"
      register: git_managed

    # === Snapshot-based rollback ===
    - name: Restore from snapshot
      when: snapshot_exists.stat.exists
      block:
        - name: Stop affected services
          ansible.builtin.systemd:
            name: "{{ item }}"
            state: stopped
          loop: "{{ affected_services | default([]) }}"

        - name: Restore snapshot
          ansible.builtin.shell: |
            rsync -a --delete \
              "/var/backups/change-snapshots/{{ change_id }}/" \
              "{{ restore_target | default('/') }}"
          changed_when: true

        - name: Start services
          ansible.builtin.systemd:
            name: "{{ item }}"
            state: started
          loop: "{{ affected_services | default([]) }}"

    # === Git-based rollback ===
    - name: Git revert
      when: git_managed.stat.exists and not snapshot_exists.stat.exists
      block:
        - name: Revert last commit
          ansible.builtin.command:
            chdir: /etc/change-managed
            cmd: "git revert --no-edit HEAD"
          changed_when: true

        - name: Apply reverted config
          ansible.builtin.command: |
            ansible-playbook /etc/change-managed/apply.yml
          changed_when: true

    # === Package rollback ===
    - name: Package downgrade
      when: rollback_type | default('') == 'package'
      block:
        - name: Downgrade package
          ansible.builtin.apt:
            name: "{{ package_name }}={{ previous_version }}"
            state: present
            force: true
          when: ansible_os_family == "Debian"

    # === Verify rollback ===
    - name: Post-rollback smoke test
      ansible.builtin.include_tasks: tasks/smoke-test.yml

    - name: Calculate rollback duration
      ansible.builtin.set_fact:
        rollback_duration: "{{ (ansible_date_time.epoch | int) - (rollback_start | int) }}"

    - name: Notify rollback complete
      ansible.builtin.uri:
        url: "{{ slack_webhook }}"
        method: POST
        body_format: json
        body:
          text: >
            :white_check_mark: ROLLBACK completato per change {{ change_id }}
            su {{ inventory_hostname }} in {{ rollback_duration }}s
      delegate_to: localhost

    - name: Fail if rollback too slow
      ansible.builtin.fail:
        msg: "Rollback completato ma ha richiesto {{ rollback_duration }}s (target: {{ rollback_timeout }}s)"
      when: rollback_duration | int > rollback_timeout
```

### 8.4 Database Rollback Strategy

Il rollback di change a database e il piu complesso perche i dati possono essere stati modificati dopo la migrazione. Strategie:

**Approccio Expand-Contract (raccomandato):**

```sql
-- Fase 1: EXPAND (forward migration)
-- Aggiunge nuova colonna senza rimuovere la vecchia
ALTER TABLE users ADD COLUMN email_verified boolean DEFAULT false;

-- Fase 2: MIGRATE DATA
-- Popola la nuova colonna con dati esistenti
UPDATE users SET email_verified = (verification_date IS NOT NULL);

-- Fase 3: SWITCH (applicazione usa nuova colonna)
-- Deploy applicativo che legge da email_verified

-- Fase 4: CONTRACT (cleanup)
-- Solo dopo conferma che tutto funziona
ALTER TABLE users DROP COLUMN verification_date;
```

**Rollback della Fase 1 o 2**: semplice `DROP COLUMN email_verified`

**Rollback della Fase 3**: switch applicativo alla vecchia colonna

**Rollback della Fase 4**: non possibile senza backup — questo e il motivo per cui Contract si esegue solo dopo validazione completa.

---

## 9. Change Risk Assessment Matrix

### 9.1 Il Modello di Rischio

Il rischio di un change si calcola come prodotto di due fattori: la probabilita che qualcosa vada storto (likelihood) e l'impatto se effettivamente fallisce (impact).

**Risk Score = Likelihood × Impact**

**Scala Likelihood (1-5):**

| Score | Livello | Descrizione | Esempi |
|-------|---------|-------------|--------|
| 1 | Molto basso | Change eseguito >50 volte senza incidenti | Patch automatico settimanale |
| 2 | Basso | Change ben documentato, procedura stabile | Aggiunta utente AD |
| 3 | Medio | Change eseguito poche volte, qualche incognita | Upgrade versione middleware |
| 4 | Alto | Change mai eseguito o con precedenti di fallimento | Migrazione database major version |
| 5 | Molto alto | Change complesso, molte dipendenze, no precedenti | Migrazione datacenter |

**Scala Impact (1-5):**

| Score | Livello | Descrizione | Esempi |
|-------|---------|-------------|--------|
| 1 | Minimo | Nessun impatto utente, interno solo | Tool di sviluppo interno |
| 2 | Basso | Impatto su singolo team, workaround disponibile | Wiki interna temporaneamente down |
| 3 | Medio | Impatto su multipli team o servizi non-critici | Servizio di reporting non disponibile |
| 4 | Alto | Impatto su servizi critici, utenti esterni impattati | E-commerce degradato |
| 5 | Critico | Outage totale, perdita dati, violazione compliance | Database di produzione corrotto |

### 9.2 Matrice di Rischio

```
          IMPACT
          1     2     3     4     5
    ┌─────┬─────┬─────┬─────┬─────┐
  1 │  1  │  2  │  3  │  4  │  5  │
    ├─────┼─────┼─────┼─────┼─────┤
L 2 │  2  │  4  │  6  │  8  │ 10  │
I   ├─────┼─────┼─────┼─────┼─────┤
K 3 │  3  │  6  │  9  │ 12  │ 15  │
E   ├─────┼─────┼─────┼─────┼─────┤
L 4 │  4  │  8  │ 12  │ 16  │ 20  │
I   ├─────┼─────┼─────┼─────┼─────┤
H 5 │  5  │ 10  │ 15  │ 20  │ 25  │
    └─────┴─────┴─────┴─────┴─────┘

Risk Level:
  1-4   = LOW      → Standard change (se pre-approved model esiste)
  5-9   = MEDIUM   → Normal change, Change Manager approval
  10-16 = HIGH     → Normal change, full CAB review
  17-25 = CRITICAL → Normal change, CAB + Senior Management
```

### 9.3 Fattori di Mitigazione

Ogni mitigazione riduce il risk score di un valore specifico. Il risk score effettivo e il risk score base meno le mitigazioni applicate (minimo 1).

| Mitigazione | Riduzione Risk | Evidenza richiesta |
|-------------|---------------|-------------------|
| Change eseguito con successo in staging | -2 | Log del test in staging |
| Rollback plan testato | -2 | Evidenza del test di rollback |
| Canary deployment pianificato | -2 | Pipeline canary configurata |
| Backup verificato < 24h | -1 | Timestamp del backup |
| Monitoring automatizzato attivo | -1 | Dashboard configurata |
| Change eseguito >10 volte prima | -1 | Storico delle change |
| SME disponibile durante implementazione | -1 | Conferma reperibilita |
| Maintenance window confermata | -1 | Calendar entry |

**Esempio di calcolo:**

```
Change: Migrazione PostgreSQL 15 → 17
  Base Likelihood: 4 (mai eseguito in prod)
  Base Impact: 4 (servizio critico)
  Base Risk Score: 16 (HIGH)

  Mitigazioni:
  - Testato in staging:         -2
  - Rollback plan testato:      -2
  - Backup verificato:          -1
  - SME disponibile:            -1

  Adjusted Risk Score: 16 - 6 = 10 (MEDIUM-HIGH)
  → Richiede comunque full CAB review
```

---

## 10. CI/CD e Change Management Integration

### 10.1 Il Ponte tra CI/CD e ITSM

L'integrazione tra pipeline CI/CD e il sistema di change management ITSM (ServiceNow, Jira Service Management, etc.) e il punto di congiunzione tra velocita DevOps e governance ITIL.

**Architettura di integrazione:**

```
Developer → Git Push → CI Pipeline
                          │
                          ├── Build
                          ├── Test
                          ├── Security Scan
                          ├── Quality Gate
                          │
                          ▼
                    ┌─────────────┐
                    │  ITSM API   │
                    │ (ServiceNow │
                    │  / JSM)     │
                    └──────┬──────┘
                           │
                 ┌─────────┴─────────┐
                 │                   │
           Standard?            Normal?
                 │                   │
           Auto-approve        Queue for CAB
                 │                   │
           CD Pipeline          Wait approval
                 │                   │
                 ▼                   ▼
            Deploy ◄─────────── CD Pipeline
                 │
            Validate
                 │
            Close Change
```

### 10.2 ServiceNow Integration via API

```python
#!/usr/bin/env python3
"""servicenow_change.py — Integrazione CI/CD con ServiceNow Change Management."""

import os
import sys
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class ChangeRequest:
    short_description: str
    description: str
    change_type: str  # standard, normal, emergency
    category: str
    risk: str
    impact: str
    assignment_group: str
    ci_affected: list[str]
    implementation_plan: str
    backout_plan: str
    test_plan: str


class ServiceNowClient:
    def __init__(self, instance: str, username: str, password: str) -> None:
        self.base_url = f"https://{instance}.service-now.com/api/now"
        self.auth = (username, password)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_change(self, cr: ChangeRequest) -> dict:
        payload = {
            "short_description": cr.short_description,
            "description": cr.description,
            "type": cr.change_type,
            "category": cr.category,
            "risk": cr.risk,
            "impact": cr.impact,
            "assignment_group": cr.assignment_group,
            "implementation_plan": cr.implementation_plan,
            "backout_plan": cr.backout_plan,
            "test_plan": cr.test_plan,
        }
        resp = requests.post(
            f"{self.base_url}/table/change_request",
            json=payload,
            auth=self.auth,
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["result"]

    def get_change_status(self, change_number: str) -> str:
        resp = requests.get(
            f"{self.base_url}/table/change_request",
            params={"sysparm_query": f"number={change_number}", "sysparm_fields": "state"},
            auth=self.auth,
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()
        results = resp.json().get("result", [])
        if not results:
            raise ValueError(f"Change {change_number} non trovato")
        return results[0]["state"]

    def close_change(self, sys_id: str, success: bool, notes: str) -> None:
        state = "3" if success else "4"  # 3=closed, 4=closed_incomplete
        payload = {
            "state": state,
            "close_code": "successful" if success else "unsuccessful",
            "close_notes": notes,
        }
        resp = requests.patch(
            f"{self.base_url}/table/change_request/{sys_id}",
            json=payload,
            auth=self.auth,
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()


def main() -> None:
    instance = os.environ["SNOW_INSTANCE"]
    username = os.environ["SNOW_USERNAME"]
    password = os.environ["SNOW_PASSWORD"]

    client = ServiceNowClient(instance, username, password)

    cr = ChangeRequest(
        short_description=os.environ.get("CHANGE_TITLE", "Automated deployment"),
        description=os.environ.get("CHANGE_DESC", ""),
        change_type=os.environ.get("CHANGE_TYPE", "standard"),
        category="Software",
        risk=os.environ.get("CHANGE_RISK", "low"),
        impact=os.environ.get("CHANGE_IMPACT", "low"),
        assignment_group=os.environ.get("CHANGE_GROUP", "Platform Engineering"),
        ci_affected=os.environ.get("CHANGE_CIS", "").split(","),
        implementation_plan=os.environ.get("CHANGE_IMPL_PLAN", ""),
        backout_plan=os.environ.get("CHANGE_BACKOUT_PLAN", ""),
        test_plan=os.environ.get("CHANGE_TEST_PLAN", ""),
    )

    result = client.create_change(cr)
    print(f"Change creato: {result['number']}")
    print(f"Sys ID: {result['sys_id']}")


if __name__ == "__main__":
    main()
```

---

## 11. GitOps per Infrastructure Changes

### 11.1 Principi GitOps

GitOps e un paradigma operativo dove Git e la single source of truth per lo stato desiderato dell'infrastruttura. Ogni change all'infrastruttura avviene tramite commit in Git, e un operatore automatizzato riconcilia lo stato reale con lo stato dichiarato.

**I quattro principi GitOps (OpenGitOps):**

1. **Declarative**: l'intero sistema e descritto dichiarativamente (Terraform, Kubernetes YAML, Ansible)
2. **Versioned and Immutable**: lo stato desiderato e versionato in Git, immutabile (ogni change e un nuovo commit)
3. **Pulled Automatically**: un agente software applica automaticamente lo stato desiderato (ArgoCD, Flux, Atlantis)
4. **Continuously Reconciled**: l'agente monitora continuamente e corregge drift tra stato desiderato e reale

### 11.2 GitOps Workflow per Infrastructure

```
Developer propone change
      │
      ▼
  Branch + PR
      │
      ├── Pre-merge checks (CI):
      │   ├── terraform fmt
      │   ├── terraform validate
      │   ├── terraform plan (su staging)
      │   ├── checkov / tfsec
      │   ├── OPA policy check
      │   ├── infracost diff
      │   └── CMDB impact check
      │
      ├── Peer review (code):
      │   ├── Architectural review
      │   └── Security review
      │
      ├── Change approval (ITSM):
      │   ├── Auto per standard change
      │   └── CAB per normal change
      │
      ▼
  Merge to main
      │
      ▼
  GitOps Operator (Atlantis/Flux)
      │
      ├── terraform plan (produzione)
      ├── Manual approval (per change critiche)
      ├── terraform apply
      ├── Post-apply validation
      └── ITSM change closure
```

### 11.3 Atlantis per Terraform GitOps

Atlantis e un server GitOps specifico per Terraform. Ascolta webhook dai PR e esegue `terraform plan` e `terraform apply` automaticamente.

```yaml
# atlantis.yaml (nella root del repo)
version: 3

automerge: false
delete_source_branch_on_merge: true

projects:
  - name: networking
    dir: infrastructure/networking
    workspace: production
    terraform_version: v1.9.0
    autoplan:
      when_modified:
        - "**/*.tf"
        - "**/*.tfvars"
      enabled: true
    apply_requirements:
      - approved
      - mergeable
    workflow: standard

  - name: compute
    dir: infrastructure/compute
    workspace: production
    terraform_version: v1.9.0
    autoplan:
      when_modified:
        - "**/*.tf"
        - "**/*.tfvars"
      enabled: true
    apply_requirements:
      - approved
      - mergeable
    workflow: standard

  - name: database
    dir: infrastructure/database
    workspace: production
    terraform_version: v1.9.0
    autoplan:
      when_modified:
        - "**/*.tf"
        - "**/*.tfvars"
      enabled: true
    apply_requirements:
      - approved
      - mergeable
    workflow: high-risk  # workflow con approvazioni aggiuntive

workflows:
  standard:
    plan:
      steps:
        - run: terraform fmt -check -recursive
        - run: checkov -d . --framework terraform --compact
        - init
        - plan:
            extra_args: ["-out", "tfplan"]
        - run: |
            terraform show -json tfplan > tfplan.json
            opa eval --data /policies/ --input tfplan.json \
              "data.terraform.deny[msg]" --format pretty
        - run: infracost diff --path tfplan.json --format json
    apply:
      steps:
        - apply

  high-risk:
    plan:
      steps:
        - run: terraform fmt -check -recursive
        - run: checkov -d . --framework terraform --compact
        - init
        - plan:
            extra_args: ["-out", "tfplan"]
        - run: |
            terraform show -json tfplan > tfplan.json
            opa eval --data /policies/ --input tfplan.json \
              "data.terraform.deny[msg]" --format pretty
            opa eval --data /policies/ --input tfplan.json \
              "data.terraform.warn[msg]" --format pretty
        - run: infracost diff --path tfplan.json --format json
    apply:
      steps:
        - run: echo "ATTENZIONE: applicazione change ad alto rischio. Verificare il plan."
        - apply
```

---

## 12. Terraform Plan/Apply Validation

### 12.1 Il Workflow Terraform Sicuro

Terraform e lo strumento IaC piu diffuso per infrastruttura cloud. Il suo workflow `plan` → `apply` si integra naturalmente nel change management: il `plan` e l'equivalente dell'RFC (mostra cosa cambiera), l'`apply` e l'implementazione.

**Validation chain completa:**

```
terraform fmt -check
    │
    ▼
terraform validate
    │
    ▼
terraform plan -out=tfplan
    │
    ├── Analisi del plan:
    │   ├── Risorse create/modificate/distrutte
    │   ├── Cambiamenti che forzano recreate
    │   └── Drift detection
    │
    ▼
Security scan (checkov/tfsec)
    │
    ▼
Policy check (OPA/Sentinel)
    │
    ▼
Cost estimation (infracost)
    │
    ▼
Human/automated approval
    │
    ▼
terraform apply tfplan
    │
    ▼
Post-apply validation
```

### 12.2 Script di Validazione del Plan

```bash
#!/usr/bin/env bash
# terraform-plan-validator.sh — Analizza e valida un terraform plan
set -euo pipefail

PLAN_FILE="${1:?Uso: terraform-plan-validator.sh <plan.json>}"
MAX_DESTROYS="${MAX_DESTROYS:-0}"
MAX_CHANGES="${MAX_CHANGES:-50}"

echo "=== Terraform Plan Validator ==="
echo "Analyzing: ${PLAN_FILE}"
echo

# Conta risorse per azione
CREATES=$(jq '[.resource_changes[] | select(.change.actions[] == "create")] | length' "$PLAN_FILE")
UPDATES=$(jq '[.resource_changes[] | select(.change.actions[] == "update")] | length' "$PLAN_FILE")
DESTROYS=$(jq '[.resource_changes[] | select(.change.actions[] == "delete")] | length' "$PLAN_FILE")
REPLACES=$(jq '[.resource_changes[]
  | select(.change.actions | contains(["delete","create"]))] | length' "$PLAN_FILE")
NO_OP=$(jq '[.resource_changes[] | select(.change.actions[] == "no-op")] | length' "$PLAN_FILE")
TOTAL=$((CREATES + UPDATES + DESTROYS + REPLACES))

echo "Summary:"
echo "  Create:  ${CREATES}"
echo "  Update:  ${UPDATES}"
echo "  Destroy: ${DESTROYS}"
echo "  Replace: ${REPLACES}"
echo "  No-op:   ${NO_OP}"
echo "  Total changes: ${TOTAL}"
echo

# Check: troppi destroys
if [ "$DESTROYS" -gt "$MAX_DESTROYS" ]; then
    echo "BLOCKED: ${DESTROYS} risorse da distruggere (max: ${MAX_DESTROYS})"
    echo "Risorse in eliminazione:"
    jq -r '.resource_changes[]
      | select(.change.actions[] == "delete")
      | "  - \(.address)"' "$PLAN_FILE"
    exit 1
fi

# Check: troppi cambiamenti totali
if [ "$TOTAL" -gt "$MAX_CHANGES" ]; then
    echo "WARNING: ${TOTAL} cambiamenti totali (max raccomandato: ${MAX_CHANGES})"
    echo "Considerare di suddividere in change piu piccole."
fi

# Check: risorse critiche modificate
CRITICAL_RESOURCES=$(jq -r '.resource_changes[]
  | select(.change.actions != ["no-op"])
  | select(
      .type == "aws_db_instance" or
      .type == "aws_rds_cluster" or
      .type == "aws_vpc" or
      .type == "aws_subnet" or
      .type == "aws_route_table" or
      .type == "aws_iam_role" or
      .type == "aws_iam_policy" or
      .type == "aws_kms_key" or
      .type == "aws_s3_bucket"
    )
  | .address' "$PLAN_FILE")

if [ -n "$CRITICAL_RESOURCES" ]; then
    echo "ATTENTION: Risorse critiche modificate:"
    echo "$CRITICAL_RESOURCES" | sed 's/^/  - /'
    echo "Queste richiedono review aggiuntivo."
fi

# Check: force replacement (recreate)
if [ "$REPLACES" -gt 0 ]; then
    echo
    echo "WARNING: ${REPLACES} risorse saranno ricreate (force replacement):"
    jq -r '.resource_changes[]
      | select(.change.actions | contains(["delete","create"]))
      | "  - \(.address)"' "$PLAN_FILE"
    echo "Questo potrebbe causare downtime."
fi

echo
echo "Validation completed."
exit 0
```

### 12.3 Terraform State Locking e Concurrency

```hcl
# backend.tf — Backend con state locking
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "production/infrastructure.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:eu-west-1:123456789:key/xxx"
    dynamodb_table = "terraform-state-lock"
  }
}

# La tabella DynamoDB per il locking
# (da creare una tantum, non gestita dallo stesso state)
#
# resource "aws_dynamodb_table" "terraform_lock" {
#   name         = "terraform-state-lock"
#   billing_mode = "PAY_PER_REQUEST"
#   hash_key     = "LockID"
#
#   attribute {
#     name = "LockID"
#     type = "S"
#   }
#
#   tags = {
#     Name    = "Terraform State Lock"
#     Purpose = "Prevent concurrent terraform apply"
#   }
# }
```

---

## 13. Ansible Check Mode e Validazione

### 13.1 Check Mode (Dry Run)

Ansible check mode (`--check`) simula l'esecuzione del playbook senza apportare modifiche reali. E l'equivalente del `terraform plan` per la configuration management.

**Uso corretto del check mode:**

```bash
# Dry run completo
ansible-playbook playbook.yml --check --diff

# Dry run con output dettagliato
ansible-playbook playbook.yml --check --diff -v

# Dry run su un sottoinsieme di host
ansible-playbook playbook.yml --check --diff --limit "web-servers"

# Dry run con tag specifici
ansible-playbook playbook.yml --check --diff --tags "security,patching"
```

**Limitazioni del check mode:**

| Limitazione | Descrizione | Workaround |
|-------------|-------------|------------|
| Moduli non idempotenti | `command`, `shell`, `raw` non supportano check mode | Usare `check_mode: false` con `changed_when` |
| Dipendenze tra task | Un task che dipende dal risultato di un precedente fallira | Usare `register` con valori di fallback |
| State esterno | Check mode non interroga API esterne | Mock dei dati o `when: not ansible_check_mode` |
| Handler | I handler non vengono eseguiti in check mode | Testare handler separatamente |

### 13.2 Diff Mode

Il diff mode (`--diff`) mostra le differenze esatte che verranno applicate ai file. Combinato con check mode, fornisce un preview completo del change.

```yaml
# Esempio output diff mode:
#
# TASK [Update nginx config] ****
# --- before: /etc/nginx/nginx.conf
# +++ after: /etc/nginx/nginx.conf
# @@ -42,7 +42,7 @@
#      server {
#          listen 80;
# -        worker_connections 1024;
# +        worker_connections 2048;
#      }
```

### 13.3 Validazione Ansible Playbook

```yaml
# ansible/playbooks/validate-playbook.yml
---
# Meta-playbook che valida un altro playbook prima dell'esecuzione
- name: Validate Ansible Playbook
  hosts: localhost
  gather_facts: false

  vars:
    target_playbook: ""  # da specificare con -e
    target_inventory: ""

  tasks:
    - name: Verify playbook file exists
      ansible.builtin.stat:
        path: "{{ target_playbook }}"
      register: playbook_file

    - name: Fail if playbook not found
      ansible.builtin.fail:
        msg: "Playbook non trovato: {{ target_playbook }}"
      when: not playbook_file.stat.exists

    - name: Syntax check
      ansible.builtin.command: >
        ansible-playbook {{ target_playbook }}
        --syntax-check
        -i {{ target_inventory }}
      changed_when: false

    - name: Lint check
      ansible.builtin.command: >
        ansible-lint {{ target_playbook }}
      changed_when: false
      failed_when: false  # warning only
      register: lint_result

    - name: Report lint warnings
      ansible.builtin.debug:
        msg: "Lint warnings:\n{{ lint_result.stdout }}"
      when: lint_result.rc != 0

    - name: Dry run (check mode)
      ansible.builtin.command: >
        ansible-playbook {{ target_playbook }}
        --check --diff
        -i {{ target_inventory }}
      changed_when: false
      register: check_result

    - name: Report changes that would be made
      ansible.builtin.debug:
        msg: "{{ check_result.stdout }}"
```

### 13.4 Ansible Vault per Secret in Change Management

```bash
# Creare un vault per i segreti della change pipeline
ansible-vault create group_vars/production/vault.yml

# Contenuto tipico:
# vault_db_password: "..."
# vault_api_token: "..."
# vault_ssl_key: "..."

# Eseguire playbook con vault
ansible-playbook change-playbook.yml \
  --vault-password-file /path/to/vault-password

# In CI/CD, il vault password viene da environment variable
echo "$ANSIBLE_VAULT_PASSWORD" > /tmp/vault-pass
ansible-playbook change-playbook.yml \
  --vault-password-file /tmp/vault-pass
# Il file viene cancellato dal CI cleanup
```

---

## 14. Configuration Drift Detection

### 14.1 Cos'e il Configuration Drift

Il configuration drift si verifica quando lo stato reale di un sistema diverge dallo stato desiderato definito nel codice. Le cause principali sono:

1. **Modifiche manuali** (SSH e modifica diretta di file di configurazione)
2. **Automazione parziale** (alcuni componenti gestiti da IaC, altri no)
3. **Processi di emergency change** che bypassano IaC
4. **Software che auto-modifica** la propria configurazione
5. **Aggiornamenti automatici** del sistema operativo

### 14.2 Detection con Terraform

```bash
#!/usr/bin/env bash
# drift-detect-terraform.sh — Rileva drift di configurazione con Terraform
set -euo pipefail

WORKSPACE="${1:?Uso: drift-detect-terraform.sh <workspace>}"
REPORT_FILE="/var/log/drift-reports/terraform-${WORKSPACE}-$(date -u +%Y%m%d).json"

mkdir -p /var/log/drift-reports

echo "Drift detection per workspace: ${WORKSPACE}"

cd "infrastructure/${WORKSPACE}"

# Refresh state senza applicare cambiamenti
terraform refresh -input=false 2>/dev/null

# Plan per vedere differenze
terraform plan -detailed-exitcode -out=driftplan 2>/dev/null
EXIT_CODE=$?

case $EXIT_CODE in
  0)
    echo "NO DRIFT: stato reale corrisponde al codice"
    echo '{"drift": false, "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}' > "$REPORT_FILE"
    ;;
  1)
    echo "ERROR: terraform plan fallito"
    exit 1
    ;;
  2)
    echo "DRIFT DETECTED!"
    terraform show -json driftplan > "$REPORT_FILE"

    # Estrai risorse driftate
    DRIFTED=$(jq -r '.resource_changes[]
      | select(.change.actions != ["no-op"])
      | "\(.address): \(.change.actions | join(", "))"' "$REPORT_FILE")

    echo "Risorse con drift:"
    echo "$DRIFTED"

    # Notifica
    curl -sf -X POST "$SLACK_WEBHOOK" \
      -H 'Content-Type: application/json' \
      -d "{\"text\": \":warning: Configuration drift detected in ${WORKSPACE}:\n\`\`\`${DRIFTED}\`\`\`\"}" \
      || true
    ;;
esac

rm -f driftplan
```

### 14.3 Detection con Ansible

```yaml
# ansible/playbooks/drift-detect.yml
---
- name: Configuration Drift Detection
  hosts: all
  gather_facts: true
  become: true

  vars:
    drift_report_dir: "/var/log/drift-reports"
    expected_configs:
      - path: /etc/ssh/sshd_config
        checksum_source: "templates/sshd_config.j2"
      - path: /etc/nginx/nginx.conf
        checksum_source: "templates/nginx.conf.j2"

  tasks:
    - name: Create report directory
      ansible.builtin.file:
        path: "{{ drift_report_dir }}"
        state: directory
        mode: "0755"
      delegate_to: localhost
      run_once: true

    # === File checksum drift ===
    - name: Check file checksums
      ansible.builtin.stat:
        path: "{{ item.path }}"
        checksum_algorithm: sha256
      register: file_checksums
      loop: "{{ expected_configs }}"
      loop_control:
        label: "{{ item.path }}"

    - name: Get expected checksums
      ansible.builtin.stat:
        path: "{{ item.checksum_source }}"
        checksum_algorithm: sha256
      register: expected_checksums
      loop: "{{ expected_configs }}"
      loop_control:
        label: "{{ item.path }}"
      delegate_to: localhost

    - name: Report file drift
      ansible.builtin.debug:
        msg: >
          DRIFT: {{ item.0.item.path }} on {{ inventory_hostname }}
          (actual: {{ item.0.stat.checksum | default('missing') }},
           expected: {{ item.1.stat.checksum | default('missing') }})
      loop: "{{ file_checksums.results | zip(expected_checksums.results) | list }}"
      loop_control:
        label: "{{ item.0.item.path }}"
      when: >
        item.0.stat.checksum | default('') != item.1.stat.checksum | default('')

    # === Package version drift ===
    - name: Check installed package versions
      ansible.builtin.package_facts:
        manager: auto

    - name: Report unexpected packages
      ansible.builtin.debug:
        msg: "DRIFT: pacchetto non gestito '{{ item }}' trovato su {{ inventory_hostname }}"
      loop: "{{ ansible_facts.packages.keys() | list | difference(managed_packages | default([])) }}"
      when: managed_packages is defined and item not in managed_packages

    # === Service state drift ===
    - name: Check expected services
      ansible.builtin.systemd:
        name: "{{ item.name }}"
      register: service_state
      loop: "{{ expected_services | default([]) }}"

    - name: Report service drift
      ansible.builtin.debug:
        msg: >
          DRIFT: servizio {{ item.item.name }} su {{ inventory_hostname }}
          e {{ item.status.ActiveState }} (atteso: {{ item.item.expected_state | default('active') }})
      loop: "{{ service_state.results }}"
      loop_control:
        label: "{{ item.item.name }}"
      when: >
        item.status.ActiveState != (item.item.expected_state | default('active'))

    # === Firewall rules drift ===
    - name: Capture current iptables rules
      ansible.builtin.command: iptables-save
      register: current_iptables
      changed_when: false

    - name: Compare with expected rules
      ansible.builtin.copy:
        content: "{{ current_iptables.stdout }}"
        dest: "{{ drift_report_dir }}/iptables-{{ inventory_hostname }}.current"
        mode: "0644"
      delegate_to: localhost
      changed_when: false
```

### 14.4 Drift Detection Scheduling

```bash
# /etc/cron.d/drift-detection
# Drift detection giornaliera alle 06:00 UTC
0 6 * * * ops-user /opt/change-management/scripts/drift-detect-terraform.sh production >> /var/log/drift-detect.log 2>&1
0 6 * * * ops-user /opt/change-management/scripts/drift-detect-terraform.sh staging >> /var/log/drift-detect.log 2>&1
30 6 * * * ops-user ansible-playbook /opt/change-management/ansible/playbooks/drift-detect.yml >> /var/log/drift-detect.log 2>&1
```

---

## 15. Change Freeze e Maintenance Windows

### 15.1 Change Freeze Policy

Un change freeze (o code freeze) e un periodo durante il quale le change non-emergency sono proibite. Lo scopo e proteggere la stabilita del sistema durante periodi critici per il business.

**Tipi di freeze:**

| Tipo | Durata tipica | Scopo | Change consentite |
|------|--------------|-------|-------------------|
| **Holiday freeze** | 2-4 settimane | Proteggere periodo festivo | Solo emergency |
| **Peak season freeze** | 1-2 settimane | Black Friday, Cyber Monday | Solo emergency |
| **Release freeze** | 1-3 giorni | Pre-release major | Solo bug fix critici |
| **Audit freeze** | 1-5 giorni | Audit di compliance | Nessuna |
| **Partial freeze** | Variabile | Proteggere componenti specifici | Change su altri componenti |

### 15.2 Implementazione Change Freeze

```yaml
# config/change-freeze-calendar.yml
freeze_periods:
  - name: "Holiday Freeze 2026"
    start: "2026-12-20T00:00:00Z"
    end: "2027-01-05T23:59:59Z"
    type: "full"
    allowed_changes:
      - "emergency"
    reason: "Periodo festivo — ridurre rischio di outage"
    approved_by: "VP Engineering"
    notification:
      warn_days_before: 14
      channels:
        - "#engineering"
        - "#ops"

  - name: "Black Friday 2026"
    start: "2026-11-25T00:00:00Z"
    end: "2026-11-30T23:59:59Z"
    type: "full"
    allowed_changes:
      - "emergency"
    reason: "Peak traffic period"
    approved_by: "CTO"
    notification:
      warn_days_before: 21
      channels:
        - "#engineering"
        - "#ops"
        - "#business"

  - name: "Q3 Audit"
    start: "2026-09-15T00:00:00Z"
    end: "2026-09-19T23:59:59Z"
    type: "audit"
    allowed_changes: []
    reason: "SOC2 audit — nessuna modifica consentita"
    approved_by: "CISO"

  - name: "Database Subsystem Freeze"
    start: "2026-06-01T00:00:00Z"
    end: "2026-06-07T23:59:59Z"
    type: "partial"
    allowed_changes:
      - "emergency"
      - "standard"
    frozen_components:
      - "database"
      - "data-pipeline"
    reason: "Migrazione data warehouse in corso"
    approved_by: "Data Platform Lead"

maintenance_windows:
  - name: "Weekly Maintenance"
    schedule: "RRULE:FREQ=WEEKLY;BYDAY=TU;BYHOUR=2"
    duration_hours: 4
    timezone: "UTC"
    allowed_changes:
      - "standard"
      - "normal"
    notification:
      warn_hours_before: 24

  - name: "Monthly Extended Maintenance"
    schedule: "RRULE:FREQ=MONTHLY;BYSETPOS=1;BYDAY=SA;BYHOUR=0"
    duration_hours: 8
    timezone: "UTC"
    allowed_changes:
      - "standard"
      - "normal"
      - "major"
    notification:
      warn_days_before: 7
```

### 15.3 Enforcement Automatico del Freeze

```python
#!/usr/bin/env python3
"""freeze-check.py — Verifica se un change e consentito nel periodo corrente."""

import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


def load_freeze_calendar(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def is_in_freeze(
    now: datetime, freeze_periods: list[dict]
) -> tuple[bool, str | None]:
    for period in freeze_periods:
        start = datetime.fromisoformat(period["start"])
        end = datetime.fromisoformat(period["end"])
        if start <= now <= end:
            return True, period["name"]
    return False, None


def is_change_allowed(
    change_type: str,
    freeze_period: dict | None,
    component: str | None = None,
) -> bool:
    if freeze_period is None:
        return True

    allowed = freeze_period.get("allowed_changes", [])
    if change_type not in allowed:
        return False

    frozen_components = freeze_period.get("frozen_components", [])
    if frozen_components and component in frozen_components:
        return False

    return True


def main() -> None:
    change_type = sys.argv[1] if len(sys.argv) > 1 else "normal"
    component = sys.argv[2] if len(sys.argv) > 2 else None
    calendar_path = sys.argv[3] if len(sys.argv) > 3 else "config/change-freeze-calendar.yml"

    calendar = load_freeze_calendar(calendar_path)
    now = datetime.now(tz=timezone.utc)

    in_freeze, period_name = is_in_freeze(now, calendar.get("freeze_periods", []))

    if not in_freeze:
        print(f"OK: nessun freeze attivo. Change '{change_type}' consentito.")
        sys.exit(0)

    period = next(
        p for p in calendar["freeze_periods"] if p["name"] == period_name
    )

    if is_change_allowed(change_type, period, component):
        print(
            f"OK: freeze '{period_name}' attivo, ma change '{change_type}' "
            f"e nella lista consentita."
        )
        sys.exit(0)

    print(
        f"BLOCKED: freeze '{period_name}' attivo "
        f"({period['start']} — {period['end']}). "
        f"Change '{change_type}' non consentito. "
        f"Motivo: {period['reason']}"
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## 16. Compliance e Audit Trail

### 16.1 Requisiti di Audit Trail

Un audit trail completo per il change management deve rispondere alle seguenti domande per ogni change:

- **Chi** ha richiesto, approvato e implementato il change?
- **Cosa** e stato modificato esattamente?
- **Quando** e stato richiesto, approvato, implementato, validato?
- **Perche** il change era necessario (business justification)?
- **Come** e stato implementato (procedura, strumenti)?
- **Risultato**: successo o fallimento? Se fallimento, cosa e stato fatto?

### 16.2 Struttura dell'Audit Record

```json
{
  "change_record": {
    "id": "CHG-2026-04892",
    "type": "normal",
    "category": "significant",
    "risk_score": 10,

    "requester": {
      "name": "Marco Rossi",
      "email": "marco.rossi@company.com",
      "team": "Platform Engineering",
      "timestamp": "2026-05-01T10:30:00Z"
    },

    "description": "Migrazione PostgreSQL 15 → 17",
    "business_justification": "EOL PG15, performance improvements",

    "approval_chain": [
      {
        "approver": "Laura Bianchi",
        "role": "Change Manager",
        "decision": "approved",
        "timestamp": "2026-05-02T09:15:00Z",
        "notes": "Risk assessment reviewed"
      },
      {
        "approver": "CAB",
        "role": "Change Advisory Board",
        "decision": "approved",
        "timestamp": "2026-05-05T10:00:00Z",
        "notes": "Approved with condition: staging validation first"
      }
    ],

    "implementation": {
      "implementer": "Giuseppe Verdi",
      "start_time": "2026-05-18T02:00:00Z",
      "end_time": "2026-05-18T04:30:00Z",
      "steps_executed": [
        {"step": "Pre-validation", "status": "success", "timestamp": "2026-05-18T02:05:00Z"},
        {"step": "Backup", "status": "success", "timestamp": "2026-05-18T02:15:00Z"},
        {"step": "pg_upgrade", "status": "success", "timestamp": "2026-05-18T03:00:00Z"},
        {"step": "Analyze", "status": "success", "timestamp": "2026-05-18T03:20:00Z"},
        {"step": "Smoke test", "status": "success", "timestamp": "2026-05-18T03:30:00Z"},
        {"step": "Soak test", "status": "success", "timestamp": "2026-05-18T04:00:00Z"}
      ],
      "artifacts": {
        "terraform_plan": "s3://audit-trail/CHG-2026-04892/tfplan.json",
        "ansible_log": "s3://audit-trail/CHG-2026-04892/ansible.log",
        "test_results": "s3://audit-trail/CHG-2026-04892/test-results.xml",
        "monitoring_snapshot": "s3://audit-trail/CHG-2026-04892/grafana-snapshot.png"
      }
    },

    "validation": {
      "smoke_test": {"status": "pass", "timestamp": "2026-05-18T03:30:00Z"},
      "soak_test": {"status": "pass", "duration_minutes": 30, "timestamp": "2026-05-18T04:00:00Z"},
      "metric_comparison": {
        "latency_p99_before": 0.150,
        "latency_p99_after": 0.120,
        "error_rate_before": 0.001,
        "error_rate_after": 0.0008
      }
    },

    "result": "success",
    "cmdb_updates": [
      {"ci": "CI-DB-PROD-01", "field": "version", "old": "15.6", "new": "17.2"},
      {"ci": "CI-DB-PROD-02", "field": "version", "old": "15.6", "new": "17.2"}
    ],

    "post_implementation_review": {
      "reviewer": "Laura Bianchi",
      "date": "2026-05-20T10:00:00Z",
      "outcome": "successful",
      "lessons_learned": "Pianificare 1h extra per analyze su grandi database",
      "process_improvements": "Aggiungere stima tempo analyze al template RFC"
    }
  }
}
```

### 16.3 Compliance Framework Mapping

| Requisito Compliance | Come il Change Management lo soddisfa |
|---------------------|--------------------------------------|
| **SOC2 CC8.1** | Change management process documentato e implementato |
| **SOC2 CC6.1** | Separazione dei ruoli (requester ≠ approver ≠ implementer) |
| **ISO 27001 A.12.1.2** | Change management per sistemi informativi |
| **ISO 27001 A.14.2.2** | Change control per sviluppo software |
| **PCI-DSS 6.5.6** | Change control per componenti di sistema |
| **GDPR Art. 32** | Processo per testare e valutare misure di sicurezza |
| **ITIL Change Enablement** | Framework completo per gestione change |

### 16.4 Log Retention per Audit

```yaml
# config/audit-retention.yml
retention_policy:
  change_records:
    hot_storage: "90 days"     # Accesso rapido, query frequenti
    warm_storage: "1 year"     # Investigation, trend analysis
    cold_storage: "7 years"    # Compliance, legal
    format: "JSON"
    encryption: "AES-256-GCM"
    integrity: "SHA-256 hash chain"

  approval_logs:
    retention: "7 years"
    immutable: true
    format: "JSON with digital signature"

  implementation_artifacts:
    terraform_plans: "3 years"
    ansible_logs: "1 year"
    test_results: "1 year"
    monitoring_snapshots: "90 days"

  git_history:
    retention: "indefinite"
    note: "Git e immutabile per design; non eliminare mai branch merged"

  access_controls:
    read_audit: ["auditors", "compliance", "management"]
    write_audit: ["change-management-system"]  # solo sistema automatico
    delete_audit: []  # nessuno puo eliminare record di audit
```

---

## 17. Troubleshooting

### T1. Il pipeline di validazione pre-change fallisce su `terraform validate`

**Sintomi**: `Error: Missing required argument` o `Error: Unsupported attribute` durante terraform validate nel pipeline CI.

**Causa**: variabili non passate durante la validazione, oppure versione di Terraform diversa tra locale e CI.

**Soluzione**:
1. Verificare che il CI usi la stessa versione di Terraform specificata in `required_version`:
   ```bash
   terraform version
   grep required_version versions.tf
   ```
2. Assicurarsi che tutte le variabili abbiano valori default o siano passate via `-var-file`:
   ```bash
   terraform validate -var-file=environments/production.tfvars
   ```
3. Controllare che il backend sia inizializzato con `-backend=false` per validazione pura:
   ```bash
   terraform init -backend=false
   terraform validate
   ```

### T2. Ansible check mode mostra cambiamenti quando non dovrebbero esserci

**Sintomi**: `--check` riporta `changed` su task che dovrebbero essere idempotenti.

**Causa**: moduli `command`/`shell` senza `changed_when`, oppure template con variabili dinamiche (timestamp, UUID).

**Soluzione**:
1. Aggiungere `changed_when: false` ai task di sola lettura
2. Rimuovere valori dinamici dai template (generare timestamp nel task, non nel template)
3. Usare `creates`/`removes` per i moduli command:
   ```yaml
   - name: Esegui solo se output non esiste
     ansible.builtin.command: generate-config.sh
     args:
       creates: /etc/app/config.generated
   ```

### T3. Il soak test fallisce intermittentemente

**Sintomi**: il soak test passa a volte e fallisce altre, senza cambiamenti nel codice.

**Causa**: soglie troppo strette, baseline instabile, o fenomeni esterni (batch job, cron task).

**Soluzione**:
1. Aumentare la tolleranza delle soglie del 10-20%
2. Escludere i periodi noti di batch processing dalle finestre di soak test
3. Usare medie mobili invece di valori istantanei:
   ```yaml
   # Invece di:
   query: 'rate(http_requests_total{status=~"5.."}[1m])'
   # Usare:
   query: 'avg_over_time(rate(http_requests_total{status=~"5.."}[5m])[10m:])'
   ```
4. Implementare un warmup period di 5 minuti prima di iniziare a valutare le soglie

### T4. Rollback automatico non si attiva

**Sintomi**: il change fallisce ma il rollback non viene eseguito.

**Causa**: il job di rollback dipende dal job di execute con condizione `if: failure()`, ma il job di execute non ha fallito correttamente (exit code 0 nonostante il problema).

**Soluzione**:
1. Verificare che tutti gli step del job di execute abbiano `set -e` (bash) o `set -euo pipefail`
2. Verificare che gli smoke test restituiscano exit code non-zero in caso di failure
3. Aggiungere un timeout esplicito al job:
   ```yaml
   execute:
     timeout-minutes: 30
   ```
4. Aggiungere health check espliciti che falliscono con exit code 1

### T5. Configuration drift rilevato ma non comprensibile

**Sintomi**: il drift detection report mostra differenze, ma non e chiaro cosa sia cambiato e perche.

**Causa**: lo state file di Terraform contiene metadata che cambiano (last modified, etag) o risorse gestite da altri processi.

**Soluzione**:
1. Usare `ignore_changes` in Terraform per attributi gestiti esternamente:
   ```hcl
   lifecycle {
     ignore_changes = [tags["LastModified"], metadata]
   }
   ```
2. Separare le risorse gestite da IaC da quelle gestite manualmente
3. Aggiungere contesto al report di drift (chi ha modificato, quando, da dove)

### T6. Il CAB e un collo di bottiglia — lead time troppo alto

**Sintomi**: lead time per normal change > 15 giorni, backlog CAB > 30 RFC.

**Causa**: troppo poche sessioni CAB, troppo poche standard change pre-approvate, o processo eccessivamente burocratico.

**Soluzione**:
1. Analizzare le change degli ultimi 6 mesi: quali potevano essere standard change?
2. Creare standard change model per le 10 change piu frequenti
3. Implementare CAB asincrono via PR per change a basso rischio (score < 5)
4. Aggiungere una sessione CAB extra settimanale (anche 15 minuti)
5. Delegare le change con risk score < 9 al Change Manager senza CAB

### T7. Emergency change troppo frequenti

**Sintomi**: emergency change ratio > 25%.

**Causa**: change classificate come emergency per evitare il processo CAB, oppure problemi sistemici che generano emergenze reali.

**Soluzione**:
1. Audit retrospettivo: per ogni emergency change, era davvero un'emergenza?
2. Implementare criteri formali per emergency change (vedi sezione 2.3)
3. Richiedere post-CAB review obbligatorio per ogni emergency change
4. Tracciare il trend e presentarlo al management come indicatore di maturita del processo

### T8. Il canary deployment non rileva regressioni

**Sintomi**: il canary viene promosso a 100% ma poi si rilevano problemi.

**Causa**: traffico canary insufficiente per rilevare problemi rari, o metriche monitorate non complete.

**Soluzione**:
1. Aumentare la percentuale canary (da 5% a 10-15%)
2. Aumentare la durata del soak canary (da 30 min a 2-4 ore)
3. Aggiungere metriche applicative custom oltre a CPU/memory/latency
4. Confrontare distribuzioni statistiche, non solo medie (KL divergence, KS test)
5. Includere metriche di business (conversion rate, cart abandonment) nel canary check

### T9. Terraform state lock bloccato

**Sintomi**: `Error: Error acquiring the state lock` anche quando nessun altro sta eseguendo terraform.

**Causa**: un precedente `terraform apply` e stato interrotto (kill, timeout, rete) lasciando il lock in DynamoDB.

**Soluzione**:
1. Verificare che nessuno stia realmente eseguendo terraform:
   ```bash
   aws dynamodb get-item --table-name terraform-state-lock \
     --key '{"LockID":{"S":"company-terraform-state/production/infrastructure.tfstate"}}'
   ```
2. Se confermato che il lock e orfano, rimuoverlo:
   ```bash
   terraform force-unlock <LOCK_ID>
   ```
3. Prevenire: aggiungere timeout al CI e gestire graceful shutdown

### T10. GitOps operator (Atlantis/Flux) fuori sync

**Sintomi**: le change committate in Git non vengono applicate automaticamente.

**Causa**: webhook non funzionante, operator crashato, o rate limiting dell'API Git.

**Soluzione**:
1. Verificare i log dell'operator:
   ```bash
   kubectl logs -n atlantis deployment/atlantis --tail=100
   ```
2. Verificare che i webhook siano configurati e funzionanti (GitHub settings → Webhooks)
3. Verificare la connettivita dell'operator verso il cloud provider (credenziali, network policy)
4. Trigger manuale di riconciliazione:
   ```bash
   # Flux
   flux reconcile source git flux-system
   # ArgoCD
   argocd app sync <app-name>
   ```

### T11. Blue-green switch causa errori 502

**Sintomi**: durante lo switch del traffico da blue a green, si verificano errori 502 per alcuni secondi.

**Causa**: il target group green non ha terminato l'health check del load balancer, oppure le connessioni al blue vengono terminate bruscamente.

**Soluzione**:
1. Pre-warm il target group green prima dello switch:
   ```bash
   # Registrare le istanze green nel TG e attendere che siano healthy
   aws elbv2 describe-target-health --target-group-arn "$GREEN_TG_ARN"
   ```
2. Usare connection draining sul blue TG (default 300s)
3. Implementare lo switch gradualmente (weighted routing):
   ```hcl
   # 90% blue, 10% green → 50/50 → 10/90 → 0/100
   action {
     type = "forward"
     forward {
       target_group { arn = module.blue.target_group_arn; weight = 90 }
       target_group { arn = module.green.target_group_arn; weight = 10 }
     }
   }
   ```

### T12. Il change freeze viene ignorato

**Sintomi**: change vengono eseguite durante un periodo di freeze.

**Causa**: il freeze check non e integrato come gate bloccante nel pipeline, o ci sono pipeline alternative.

**Soluzione**:
1. Integrare `freeze-check.py` come primo step di ogni pipeline di deployment
2. Bloccare i merge su `main` durante il freeze (branch protection rule)
3. Aggiungere un webhook che rifiuta i PR merge durante il freeze
4. Monitorare con alerting: se un change viene eseguito durante freeze, generare incident

### T13. Audit trail incompleto

**Sintomi**: durante un audit, non e possibile ricostruire la catena completa di una change.

**Causa**: alcuni step non sono loggati, o i log sono in sistemi diversi non correlati.

**Soluzione**:
1. Usare un `change_id` univoco che attraversa tutti i sistemi (Git, CI, ITSM, monitoring)
2. Centralizzare i log in un sistema unico (ELK, Loki, Splunk) con correlation ID
3. Automatizzare la creazione dell'audit record (non dipendere da input manuale)
4. Implementare un check periodico di completezza dell'audit trail

### T14. Metriche di change management non affidabili

**Sintomi**: la change success rate riportata non corrisponde alla percezione del team.

**Causa**: change fallite non vengono registrate come tali (chiuse come "successful" dopo rollback), oppure la definizione di "successo" non e uniforme.

**Soluzione**:
1. Definire formalmente "change successful": il change ha raggiunto l'obiettivo senza rollback e senza incidenti correlati entro 48h
2. Automatizzare la determinazione di successo/fallimento basandosi su:
   - Rollback eseguito? → failure
   - Incident correlato entro 48h? → failure
   - Smoke/soak test fallito? → failure
3. Review mensile delle metriche con il team

### T15. Le standard change pre-approvate diventano obsolete

**Sintomi**: una standard change pre-approvata fallisce perche la procedura non e piu valida (cambio di infrastruttura, nuova versione OS, etc.).

**Causa**: mancanza di revisione periodica dei modelli di standard change.

**Soluzione**:
1. Implementare una revisione semestrale obbligatoria di tutte le standard change
2. Aggiungere un campo `review_date` al template con alert automatico
3. Eseguire un dry run (Ansible check mode) mensile di tutti i playbook standard change
4. Dopo ogni failure di standard change, aggiornare il modello immediatamente

### T16. Rollback database fallisce per schema incompatibility

**Sintomi**: dopo il rollback del codice applicativo, il database ha lo schema nuovo che non e compatibile con la versione precedente del codice.

**Causa**: la migrazione database non e backward-compatible (es. colonna rimossa che il codice vecchio ancora usa).

**Soluzione**:
1. Adottare il pattern Expand-Contract (sezione 8.4):
   - Mai rimuovere colonne nella stessa release che smette di usarle
   - Fase 1: aggiungi nuova colonna, il codice scrive su entrambe
   - Fase 2: il codice legge dalla nuova colonna
   - Fase 3: rimuovi la vecchia colonna (release successiva)
2. Testare il rollback dell'applicazione con lo schema migrato in staging
3. Mantenere backward compatibility per almeno 1 release

---

## 18. FAQ

### F1. Qual e la differenza tra change management e release management?

**Change management** gestisce la valutazione, approvazione e tracciamento di qualsiasi modifica all'infrastruttura o ai servizi IT. **Release management** gestisce la pianificazione, scheduling e coordinamento di gruppi di change correlate che formano una release. Una release contiene una o piu change; una change puo o meno far parte di una release. In pratica: il change management risponde a "possiamo fare questo change?"; il release management risponde a "quando e come consegniamo questo insieme di change agli utenti?".

### F2. Ogni modifica deve passare dal CAB?

No. Solo le normal change richiedono il CAB. Le standard change sono pre-approvate e non necessitano di CAB per ogni istanza. Le emergency change passano da un ECAB ridotto (tipicamente 2 persone) con review retrospettiva. L'obiettivo e che >70% delle change siano standard (automatizzate), riducendo il carico sul CAB.

### F3. Come si decide se una change e standard o normal?

Una change puo essere classificata come standard se soddisfa tutti i seguenti criteri: (1) la procedura e documentata e testata, (2) il rischio e basso e ben compreso, (3) l'esito e prevedibile, (4) esiste un rollback definito e testato, (5) il trigger e ben definito. Se anche uno solo di questi criteri non e soddisfatto, la change e normal. Il CAB valida la classificazione standard durante la creazione del modello.

### F4. Cosa fare se un change freeze impedisce un fix urgente?

Le emergency change sono consentite anche durante i freeze period. La procedura rimane la stessa: ECAB rapido, implementazione, review retrospettiva. Tuttavia, la soglia per classificare come emergency durante un freeze e piu alta: deve essere un problema che causa danno attivo e immediato al business, non un "nice to have" urgente.

### F5. Come integrare il change management con Kubernetes?

Kubernetes ha un proprio meccanismo di change management: i deployment controller, con rolling update, readiness/liveness probe, e `kubectl rollout undo`. L'integrazione avviene a livello di pipeline CI/CD: il commit nel repo Git attiva la pipeline, che crea il change record in ITSM, esegue il deployment su Kubernetes, monitora il rollout, e chiude il change record. Per change critiche (nuova versione major, schema change), il PR serve come RFC per il CAB asincrono.

### F6. Qual e il rischio di automatizzare troppo il change management?

Il rischio principale e la perdita di oversight umano su change che richiedono giudizio. L'automazione e ideale per standard change (ripetitive, a basso rischio). Per normal e emergency change, l'automazione deve supportare (pre-validation, post-validation, rollback automatico) ma non sostituire la decisione umana di approvazione. Un secondo rischio e la fragilita: se la pipeline si rompe, il team deve poter operare manualmente.

### F7. Come gestire change che coinvolgono multipli team?

Change cross-team richiedono coordinamento aggiuntivo: (1) un change coordinator dedicato (spesso il Change Manager), (2) un piano di implementazione con dipendenze inter-team esplicite, (3) un canale di comunicazione condiviso durante l'implementazione, (4) smoke test che verificano le interfacce tra i sistemi dei diversi team. Il CAB e il punto naturale di coordinamento per queste change.

### F8. Come misurare il ROI dell'automazione del change management?

Metriche chiave per il ROI: (1) riduzione del lead time medio per change (da giorni a ore/minuti), (2) riduzione delle change fallite (target < 5%), (3) riduzione del MTTR per rollback (da ore a minuti), (4) riduzione delle ore-uomo spese in processi manuali (RFC compilazione, CAB meeting, implementazione manuale), (5) riduzione degli incidenti causati da change. Confrontare queste metriche pre-automazione e post-automazione per quantificare il saving.

### F9. Come gestire change su sistemi legacy senza IaC?

Per sistemi legacy non gestiti da IaC: (1) documentare la procedura manuale in modo rigoroso (step-by-step con screenshot), (2) creare script wrapper che automatizzano almeno la pre-validation e post-validation, (3) creare backup/snapshot manuali ma verificati prima del change, (4) pianificare la migrazione graduale verso IaC (infra-as-code per i componenti nuovi, wrapping graduale dei legacy). Il change management si applica comunque: RFC, approvazione, implementazione documentata, validation.

### F10. Quanto dura un change freeze tipico?

Dipende dal contesto: holiday freeze 2-4 settimane (dicembre-gennaio), peak season 1-2 settimane, release freeze 1-3 giorni, audit freeze 3-5 giorni. Un freeze troppo lungo (>4 settimane) e controproducente: accumula change che poi vengono fatte tutte insieme post-freeze, aumentando il rischio. Meglio freeze piu brevi e piu frequenti.

### F11. Come evitare che il rollback causi piu danni del change originale?

(1) Testare il rollback con la stessa rigorosita del change (in staging, con dati realistici), (2) implementare il rollback come idempotente (eseguirlo due volte non causa danni), (3) avere smoke test anche per il rollback, (4) se il rollback e piu rischioso del change (es. rollback di database con dati mutati), documentarlo nel risk assessment e pianificare un fix-forward come alternativa.

### F12. Qual e il rapporto ideale tra standard, normal ed emergency change?

Un processo maturo tipicamente ha: >70% standard change (automatizzate), 20-25% normal change (CAB), <10% emergency change. Se le emergency superano il 15%, il processo ha un problema sistemico (troppe emergenze reali o troppa classificazione abusiva). Se le standard sono sotto il 50%, c'e spazio per automatizzare di piu.

### F13. Come gestire il change management in ambienti multi-cloud?

(1) Un unico sistema ITSM centralizzato per tutti i cloud, (2) Terraform come abstraction layer per gestire risorse su AWS, Azure, GCP con lo stesso workflow, (3) policy OPA condivise che si applicano a tutti i cloud provider, (4) monitoring unificato (Prometheus, Datadog) per la validazione post-change, (5) team di piattaforma responsabile del processo cross-cloud, team applicativi responsabili delle change specifiche.

### F14. Come formare il team sul nuovo processo di change management?

(1) Workshop iniziale di 4 ore con hands-on lab, (2) pair-programming sulle prime 10 change con un esperto, (3) documentazione chiara e accessibile (non un PDF di 200 pagine), (4) office hours settimanali per domande, (5) metriche visibili per mostrare il progresso, (6) celebrare i successi (prima standard change completamente automatizzata, prima settimana con 0 change fallite).

### F15. Il change management si applica anche ai cambiamenti di configurazione applicativa?

Si, se il cambiamento impatta il comportamento del servizio in produzione. Un feature flag che abilita una nuova feature e una change. Un aggiornamento del timeout di un endpoint e una change. La classificazione come standard o normal dipende dal rischio e dall'impatto, non dal tipo di artefatto modificato. Eccezione: modifiche a variabili di configurazione che non impattano il comportamento runtime (es. label cosmetico) possono essere escluse dal processo se il team lo decide.

### F16. Come gestire i conflitti di scheduling tra change di team diversi?

Il change calendar e lo strumento primario: ogni change approvata viene registrata nel calendario con orario, durata stimata, componenti impattati. Il Change Manager verifica i conflitti prima di approvare. In caso di conflitto: (1) change sugli stessi componenti non possono sovrapporsi, (2) change su componenti indipendenti possono essere parallele, (3) in caso di contesa sullo stesso slot, la change con risk score piu alto ha precedenza (piu tempo e attenzione richiesti), (4) change ricorrenti (standard) hanno slot riservati.

### F17. Come automatizzare il workflow del CAB riducendo i meeting?

Il CAB tradizionale con meeting settimanale e un collo di bottiglia: accumula RFC, introduce latenza e spesso degenera in sessioni di rubber-stamping dove i membri approvano change che non hanno avuto tempo di analizzare. L'automazione del workflow CAB non elimina la governance ma la rende asincrona ed evidence-based.

**Modello di CAB asincrono:**

1. **RFC come Pull Request**: ogni RFC viene creata come PR in un repository Git dedicato (`change-requests/`), con template YAML strutturato che include risk score, implementation plan, rollback plan e test plan.

2. **Validation automatica pre-review**: il pipeline CI sulla PR esegue automaticamente: (a) calcolo del risk score basato su regole OPA, (b) verifica che il rollback plan sia testabile, (c) controllo conflitti con change calendar, (d) verifica che i test di validazione esistano e siano eseguibili.

3. **Routing intelligente**: in base al risk score calcolato, la RFC viene instradata automaticamente:
   - Risk score 1-5: approvazione automatica (standard change).
   - Risk score 6-12: approvazione singola del Change Manager (review asincrona sulla PR).
   - Risk score 13-20: approvazione di due reviewer (Change Manager + owner del componente impattato).
   - Risk score 21-25: CAB sincrono obbligatorio (meeting dedicato).

4. **Timeboxing**: se una RFC non riceve review entro 48 ore lavorative, viene escalata automaticamente. Se il reviewer approva con commenti, il richiedente ha 24 ore per indirizzarli.

```yaml
# .github/workflows/change-request-review.yml
name: Change Request Validation
on:
  pull_request:
    paths: ['rfc/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Calcola risk score
        run: |
          SCORE=$(python scripts/risk_scorer.py rfc/${{ github.event.pull_request.title }}.yaml)
          echo "RISK_SCORE=$SCORE" >> $GITHUB_ENV

      - name: Verifica rollback plan
        run: |
          python scripts/validate_rollback.py rfc/${{ github.event.pull_request.title }}.yaml

      - name: Controlla conflitti calendario
        run: |
          python scripts/calendar_conflict_check.py --date "$(yq .schedule.date rfc/*.yaml)"

      - name: Assegna reviewer basato su risk score
        if: env.RISK_SCORE > 5
        uses: actions/github-script@v7
        with:
          script: |
            const score = parseInt(process.env.RISK_SCORE);
            const reviewers = score <= 12
              ? ['change-manager']
              : ['change-manager', 'component-owner'];
            await github.rest.pulls.requestReviewers({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
              reviewers: reviewers
            });
```

Questo modello riduce i meeting CAB del 70-80%: solo le change ad alto rischio (score 21+) richiedono una discussione sincrona. Il Change Manager mantiene la governance attraverso la review asincrona delle RFC a rischio medio, mentre le standard change fluiscono senza intervento umano.

### F18. Come misurare l'efficacia del processo di change management?

Le **DORA metrics** (DevOps Research and Assessment) forniscono il framework di riferimento per misurare l'efficacia del change management nel contesto DevOps. Le quattro metriche chiave, applicate specificamente al change management:

| Metrica DORA | Applicazione al Change Management | Target Elite | Target High |
|---|---|---|---|
| **Deployment Frequency** | Numero di change applicate in produzione per periodo | On-demand (multiplo/giorno) | Settimanale-mensile |
| **Lead Time for Changes** | Tempo dalla creazione della RFC al deploy in produzione | < 1 ora | 1 giorno - 1 settimana |
| **Change Failure Rate** | Percentuale di change che causano degradazione del servizio | 0-15% | 16-30% |
| **Time to Restore** | Tempo medio per ripristinare il servizio dopo una change fallita | < 1 ora | < 1 giorno |

**Metriche operative complementari:**

- **Standard change ratio**: percentuale di change classificate come standard sul totale. Target: >70%. Indica il livello di automazione e maturita del processo.
- **CAB cycle time**: tempo medio tra la sottomissione della RFC e l'approvazione del CAB. Target: <2 giorni lavorativi per normal change a rischio medio.
- **Change collision rate**: percentuale di change che causano conflitti con altre change pianificate nello stesso periodo. Target: <5%.
- **Rollback success rate**: percentuale di rollback eseguiti con successo entro il tempo previsto. Target: >95%.
- **Unauthorized change rate**: numero di change applicate senza seguire il processo formale. Target: 0.

**Dashboard di visualizzazione:**

La dashboard del change management deve essere visibile a tutta l'organizzazione IT, non solo al team di operations. Le metriche devono essere aggiornate in tempo reale (o al massimo con 15 minuti di ritardo) e includere trend settimanali e mensili. L'analisi dei trend e piu importante dei valori assoluti: un change failure rate del 20% che scende costantemente e un segnale positivo, mentre un 10% che cresce merita investigazione immediata. La correlazione tra deployment frequency e change failure rate e particolarmente importante: se la frequenza aumenta ma il failure rate resta stabile o diminuisce, il processo sta migliorando; se entrambi crescono, il processo sta deteriorando e richiede un intervento strutturale.

**Alert automatici sulle metriche:**

I threshold per gli alert devono essere definiti in modo progressivo: warning quando una metrica si avvicina al limite accettabile, critical quando lo supera. Ad esempio, il change failure rate deve generare un warning al 20% (calcolato su rolling window di 30 giorni) e un alert critical al 30%. Il CAB cycle time deve generare un warning quando supera i 3 giorni lavorativi per le normal change a rischio medio, segnalando un potenziale collo di bottiglia nel processo di approvazione. La unauthorized change rate e una metrica binaria: qualsiasi valore diverso da zero richiede investigazione immediata, poiche indica un breakdown nel processo di governance che puo avere implicazioni di compliance. Ogni alert deve essere collegato a un runbook che descrive le azioni correttive specifiche per quel tipo di deviazione dalla norma.

---

## 19. Esercizi e Laboratori

### Esercizio 1 — Pipeline standard change

**Obiettivo**: per la change "patch Ubuntu security update", costruire una pipeline completamente automatica che si esegue settimanalmente.

**Passi**:
1. Creare un playbook Ansible per pre-validation (disk, memory, backup check)
2. Creare un playbook per l'applicazione della patch (`apt update && apt upgrade -y`)
3. Creare un playbook per smoke test (servizi critici attivi, porte in ascolto)
4. Creare uno script di soak test (CPU, memory, error rate per 30 minuti)
5. Creare un playbook di rollback (apt downgrade dei pacchetti aggiornati)
6. Orchestrare tutto con un workflow GitHub Actions o un cron job
7. Testare in un ambiente di staging con VM

### Esercizio 2 — Auto-rollback

**Obiettivo**: se la validation post-change fallisce, il rollback si esegue automaticamente in meno di 5 minuti.

**Passi**:
1. Simulare un change che introduce un errore (es. configurazione nginx errata)
2. Il smoke test deve rilevare il failure (porta 80 non risponde)
3. Il rollback deve essere triggerato automaticamente
4. Verificare che il rollback ripristini lo stato funzionante
5. Misurare il tempo totale di rollback (target < 5 minuti)

### Esercizio 3 — Change calendar UI

**Obiettivo**: creare una vista che mostra tutti gli upcoming change e le freeze window.

**Passi**:
1. Definire un file YAML con maintenance windows e freeze periods
2. Creare uno script che genera un calendario HTML/terminale
3. Integrare con il sistema di notifica (Slack/email)
4. Aggiungere check automatico: la pipeline rifiuta i deploy durante freeze

### Esercizio 4 — Risk assessment automatizzato

**Obiettivo**: dato un PR con change infrastrutturali, calcolare automaticamente il risk score.

**Passi**:
1. Analizzare i file modificati nel PR (git diff)
2. Assegnare peso a ogni file/directory in base alla criticita
3. Contare il numero di risorse Terraform create/distrutte
4. Calcolare il risk score composito
5. Commentare il PR con il risk score e la classificazione
6. Bloccare il merge se il risk score richiede CAB approval non ancora ottenuta

### Esercizio 5 — Drift detection e remediation

**Obiettivo**: implementare un sistema di drift detection che rileva e corregge automaticamente le deviazioni dalla configurazione desiderata.

**Passi**:
1. Creare un playbook Ansible di drift detection (file checksum, service state, package versions)
2. Schedulare l'esecuzione giornaliera
3. Generare un report con le differenze trovate
4. Per i drift classificati come "auto-remediable", applicare automaticamente la correzione
5. Per i drift non auto-remediabili, generare un alert e creare un ticket

---

## 20. Auto-valutazione

1. Standard vs normal change: criteri di classificazione.
2. Validation gate: cosa includere.
3. Auto-rollback: criterio di attivazione.
4. Change calendar: scopo e componenti.
5. Spiegare il workflow completo di una emergency change, incluso il post-review.
6. Descrivere come integrare un pipeline CI/CD con un ITSM (ServiceNow/JSM).
7. Cosa significa "shift left validation" e come si implementa?
8. Come funziona il canary deployment per infrastruttura? Differenze con il canary applicativo.
9. Cos'e il configuration drift e come si rileva con Terraform e Ansible?
10. Come calcolare il risk score di una change e quali mitigazioni lo riducono?
11. Descrivere il pattern Expand-Contract per rollback-safe database migrations.
12. Quali metriche del CAB indicano un processo sano vs uno disfunzionale?
13. Come funziona Atlantis come GitOps operator per Terraform?
14. Quali sono i rischi di un change freeze troppo lungo?
15. Come garantire un audit trail completo e immutabile per ogni change?

---

## 21. Letture e Riferimenti

### Primarie

- ITIL 4 — Change Enablement Practice Guide, AXELOS.
- Atlassian — Change Management Best Practices. https://www.atlassian.com/itsm/change-management
- DORA — Accelerate: The Science of Lean Software and DevOps (Forsgren, Humble, Kim).
- OpenGitOps Principles — https://opengitops.dev/

### Strumenti

- Terraform Documentation — https://developer.hashicorp.com/terraform/docs
- Ansible Documentation — https://docs.ansible.com/
- Checkov (IaC Security Scanner) — https://www.checkov.io/
- Open Policy Agent — https://www.openpolicyagent.org/
- Atlantis (Terraform GitOps) — https://www.runatlantis.io/
- Infracost (Cloud Cost Estimation) — https://www.infracost.io/

### Framework e Standard

- ITIL 4 Foundation — Change Enablement.
- ISO/IEC 20000-1 — Service Management System.
- ISO 27001 — Information Security Management (A.12.1.2, A.14.2.2).
- SOC 2 Type II — Change Management Controls (CC8.1).
- PCI-DSS v4.0 — Requirement 6.5.6.

---

## 22. Collegamenti Incrociati

- Modulo 01 — `01-framework-metodologie.md`.
- Modulo 06 — `06-backup-disaster-recovery.md` (backup pre-change).
- Modulo 07 — `07-monitoraggio-incidenti.md` (monitoraggio post-change).
- Modulo 09 — `09-procedure-operative.md` (procedure standard).
- Modulo 12 — `12-itil4-deep-dive-pratiche.md` (ITIL change enablement).
- Modulo 21 — `21-postmortem-culture-blameless.md` (post-mortem per change fallite).
- Modulo 22 — `22-slo-sli-quantificazione.md` (SLI/SLO per soak test).
- Modulo 24 — `24-vulnerability-management-patch-ops.md` (patching come standard change).

---

## 23. Glossario Locale

| Termine | Definizione |
|---|---|
| **Standard change** | Change pre-approvata, a basso rischio, ripetitiva. Non richiede CAB per ogni istanza. |
| **Normal change** | Change che richiede valutazione e approvazione formale (Change Manager o CAB). |
| **Emergency change** | Change urgente che bypassa il normale processo CAB, con review retrospettiva obbligatoria. |
| **CAB** | Change Advisory Board — organo consultivo che valuta normal change per rischio e impatto. |
| **ECAB** | Emergency CAB — versione ridotta del CAB per approvazione rapida di emergency change. |
| **RFC** | Request for Change — documento formale che descrive una proposed change. |
| **Validation gate** | Check automatizzato post-implementazione per verificare il successo del change. |
| **Auto-rollback** | Inversione automatica del change se i validation gate falliscono. |
| **Change calendar** | Vista consolidata di tutti gli upcoming change, maintenance window e freeze period. |
| **Change freeze** | Periodo durante il quale le change non-emergency sono proibite. |
| **Maintenance window** | Finestra temporale designata per l'esecuzione di change pianificate. |
| **Canary deployment** | Strategia di deployment che applica il change a un sottoinsieme ridotto prima di estenderlo. |
| **Blue-green deployment** | Strategia con due ambienti identici; il traffico viene switchato dopo la validazione. |
| **Rolling update** | Aggiornamento sequenziale dei server uno alla volta, mantenendo disponibilita. |
| **Configuration drift** | Divergenza tra lo stato reale di un sistema e lo stato desiderato definito nel codice. |
| **IaC** | Infrastructure as Code — gestione dell'infrastruttura tramite codice versionato. |
| **GitOps** | Paradigma dove Git e la single source of truth per lo stato dell'infrastruttura. |
| **Soak test** | Test prolungato post-change per verificare stabilita sotto carico reale. |
| **Smoke test** | Test rapido post-change per verificare funzionalita core. |
| **PIR** | Post-Implementation Review — revisione formale dopo l'implementazione di un change. |
| **Expand-Contract** | Pattern di migrazione database backward-compatible in fasi: aggiungi, migra, rimuovi. |
| **Risk score** | Valore numerico (1-25) = Likelihood × Impact per quantificare il rischio di un change. |
| **Change authority** | Persona o organo con potere di approvazione per una specifica categoria di change. |
| **OPA** | Open Policy Agent — motore di policy dichiarative per enforcement automatizzato. |
| **Atlantis** | Server GitOps per Terraform che esegue plan/apply automaticamente da PR. |
