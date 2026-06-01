# 99-ESERCIZI — Lab e Scenari (Operations IT)

## Lab

### Lab 01 — SLO definition + monitoring

Per servizio web: definisci 3 SLI (latency, error rate, availability), 3 SLO realistici, error budget mensile. Implementa dashboard + multi-burn-rate alert.

### Lab 02 — CMDB pulito

Setup GLPI; importa 50 asset via CSV; configura auto-discovery agent; reconcile; documenta orphan cleanup procedure.

### Lab 03 — Incident drill end-to-end

Simulato: detection → mitigation → postmortem blameless → action items → follow-up. Misura MTTR, MTTD, comms quality.

### Lab 04 — Restore drill

Random VM da backup; restore su environment isolato; valida applicativo; misura RTO.

### Lab 05 — Change automation pipeline

Standard change: patch security weekly. Pipeline: pre-validation → execute → smoke → soak → close (or rollback).

## Scenari

- `scenario-01-cmdb-drift.md` — CMDB non aggiornato; 30% CI obsoleti.
- `scenario-02-slo-violazione.md` — SLO violato 3 mesi consecutivi.
- `scenario-03-postmortem-blame.md` — Postmortem trasforma in blame session; recovery culturale.
- `scenario-04-emergency-change.md` — Emergency change senza review introduce regressione.

## Scenario 01 — CMDB drift

**Sintomi**: durante incident, CMDB indica server X dipendente da DB Y, ma in realta dipende da Z (modificato 6 mesi fa).

**Da risolvere**: discovery + reconcile mensile; alert su modifica non-tracked (Ansible diff vs CMDB).

## Scenario 02 — SLO violazione

**Sintomi**: SLO 99.9% definito, attuale 99.5% per 3 mesi consecutivi.

**Da risolvere**: error budget exhausted → policy: blocca deploy non critici fino a recovery; postmortem corpus per identificare pattern; tactical fixes.

## Scenario 03 — Blame session

**Sintomi**: postmortem diventa "chi ha fatto X?". Il team non parla piu apertamente.

**Da risolvere**: facilitator esterno, refresh rules blameless, esempio dal management.

## Scenario 04 — Emergency change regression

**Sintomi**: emergency change fixa bug critico, ma introduce regressione altrove.

**Da risolvere**: post-emergency review obbligatorio; smoke test anche per emergency; rollback plan documentato.
