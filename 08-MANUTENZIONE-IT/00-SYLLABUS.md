# Syllabus — Operations IT (ITIL v4 in Pratica)

> **Lingua:** italiano
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni:** ITIL 4 Foundation; CMDB GLPI/SnipeIT; cablaggio TIA-568.2-D (2024); ITIL Practitioner roles.

## 1. Identita del corso

**"Operations IT — ITIL v4 in pratica"** — gestione operativa quotidiana di infrastruttura IT (no startup/cloud-native lens, qui parla la realta enterprise/PA/PMI italiana). Service request triage, incident management, problem management, change enablement, capacity planning, postmortem culture.

**Target competenza:** competent → proficient (Dreyfus 3 → 4). Capace di triage incident, scrivere RCA blameless, dimensionare capacity, gestire CMDB con dedup, applicare 3-2-1-1-0 backup rule.

## 2. Prerequisiti

- Linux/Windows admin basics (vedi corsi 02, 03).
- Concetti rete e storage (vedi corsi 04, 06 trasversalmente).
- Familiarita con ticketing systems (Zendesk, Freshservice, Jira Service Management).

## 3. Obiettivi di apprendimento

1. Distinguere Service Request, Incident, Problem, Change e applicare ITIL v4 vocabolario corretto.
2. Costruire un CMDB pulito (dedup, CI relationship validation, orphan cleanup).
3. Capacity planning con Little's Law, p95/p99, queue theory.
4. SLO + multi-window/multi-burn-rate alerting.
5. Postmortem blameless: facilitare, scrivere, chiudere action item.
6. 3-2-1-1-0 backup rule, restore drill cadence.
7. Cablaggio strutturato TIA-568 (per chi opera anche in fisico).
8. Hardware lifecycle e refresh planning.

## 4. Struttura

### Fase 1 — Fondamenti (1-2 settimane)
- 01: Framework e metodologie (ITIL, COBIT, ISO 20000)
- 02: Manutenzione preventiva
- 12: ITIL 4 deep dive

### Fase 2 — Servizi e sicurezza (3-5 settimane)
- 03: Gestione sistemi operativi
- 04: Servizi infrastruttura
- 05: Sicurezza operativa
- 06: Backup + DR

### Fase 3 — Monitoring e incident (settimane 6-7)
- 07: Monitoraggio incidenti
- 11: Troubleshooting generale
- 21: Postmortem culture

### Fase 4 — Asset e capacity (settimane 8-10)
- 08: Gestione asset
- 13: CMDB GLPI/SnipeIT
- 15: Capacity planning
- 16: Hardware lifecycle
- 22 (NEW): SLO/SLI quantificazione
- 23 (NEW): Change automation validation

### Fase 5 — Procedure e fisico (settimane 11-12)
- 09: Procedure operative
- 10: Pianificazione e reportistica
- 18: Cablaggio strutturato TIA-568

### Fase 6 — Capstone (settimane 13-14)
- `00-CAPSTONE.md`: SLO + CMDB + change automation per servizio simulato.

## 5. Capstone

Per un servizio simulato (e-commerce midsize): definire SLO realistici, popolare CMDB, automatizzare change validation, simulare incident + postmortem completo, calcolare capacity per Black Friday peak.

## 6. Cadenza

| Mode | Hours/week | Weeks |
|---|---|---|
| Full-time | 30-40 | 4 |
| Part-time | 8-10 | 14-16 |
| Self-paced | 4-6 | 24+ |
