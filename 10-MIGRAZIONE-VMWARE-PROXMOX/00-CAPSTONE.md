# Capstone — Progetto Finale del Corso

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione:** Progetto pratico finale — integra tutti i moduli del corso
> **Prerequisiti:** completamento di tutti i moduli 01-19, lettura dei case study `99-CASE-STUDY/`, completamento di almeno 3 lab in `99-ESERCIZI/`.
> **Tempo stimato:** 40-80 ore di lavoro effettivo, distribuite in 4-8 settimane.
> **Livello richiesto:** proficient (Dreyfus 4) — indicatore: capace di operare in produzione con supervisione minima.
> **Ultimo aggiornamento:** 2026-04-27

---

## Brief del progetto

Progettare, eseguire e documentare la **migrazione di un cluster VMware fittizio (15 VM eterogenee, 3 nodi ESXi) verso un cluster Proxmox a 3 nodi production-ready**, gestendo l'intero ciclo: assessment, pianificazione, costruzione del cluster Proxmox, migrazione, cutover, validazione, day-2 operations, e disaster recovery.

Lo scenario simula un'organizzazione mid-size (200 dipendenti, e-commerce + gestionale interno) che, dopo l'acquisizione Broadcom-VMware del 2023, decide di migrare a Proxmox per ridurre TCO e eliminare vendor lock-in.

---

## Architettura target da realizzare

```
SITE PRODUZIONE (target Proxmox)
+----------------------------------------------------+
|                                                    |
|  pve1 (Proxmox VE 8.x)                             |
|  + Ceph MON + 3 OSD (NVMe)                         |
|  + 5 VM produzione                                  |
|                                                    |
|  pve2 (Proxmox VE 8.x)                             |
|  + Ceph MON + 3 OSD (NVMe)                         |
|  + 5 VM produzione                                  |
|                                                    |
|  pve3 (Proxmox VE 8.x)                             |
|  + Ceph MON + 3 OSD (NVMe)                         |
|  + 5 VM produzione                                  |
|                                                    |
|  Networking:                                        |
|  - vmbr0: management (10.0.0.0/24)                  |
|  - vmbr1: cluster + Ceph (10.10.0.0/24, MTU 9000)   |
|  - vmbr2: VM produzione (VLAN-tagged)               |
|                                                    |
|  Storage:                                          |
|  - Ceph pool 'pve-rbd' (replica 3, SSD-only)        |
|  - PBS dedicato in VM                               |
|                                                    |
+----------------------------------------------------+
                        |
                        | VPN site-to-site
                        |
+----------------------------------------------------+
|  SITE DR (cold standby)                            |
|                                                    |
|  pve-dr (single node Proxmox VE 8.x)               |
|  + ZFS pool                                        |
|  + PBS sync receiver                               |
|  + read-only replicas via pve-zsync                 |
|                                                    |
+----------------------------------------------------+
```

---

## VM da migrare (workload simulato)

| VMID | Nome | OS | RAM | Disk | Ruolo |
|---|---|---|---|---|---|
| 101 | dc01 | Win Server 2022 | 8 GB | 80 GB | AD DC + DNS primary |
| 102 | dc02 | Win Server 2022 | 8 GB | 80 GB | AD DC + DNS secondary |
| 103 | exch01 | Win Server 2022 | 32 GB | 500 GB | Exchange Server |
| 104 | sql01 | Win Server 2022 | 32 GB | 1 TB | SQL Server (e-commerce DB) |
| 105 | iis01 | Win Server 2022 | 16 GB | 200 GB | IIS web frontend |
| 106 | iis02 | Win Server 2022 | 16 GB | 200 GB | IIS web frontend |
| 107 | pg01 | Linux Debian 12 | 32 GB | 500 GB | PostgreSQL gestionale |
| 108 | redis01 | Linux Debian 12 | 16 GB | 100 GB | Redis session store |
| 109 | nginx01 | Linux Debian 12 | 8 GB | 50 GB | Nginx reverse proxy |
| 110 | nginx02 | Linux Debian 12 | 8 GB | 50 GB | Nginx reverse proxy |
| 111 | gitlab01 | Linux Debian 12 | 16 GB | 500 GB | GitLab CE |
| 112 | jenkins01 | Linux Debian 12 | 8 GB | 200 GB | Jenkins CI/CD |
| 113 | zabbix01 | Linux Debian 12 | 8 GB | 100 GB | Monitoring |
| 114 | bastion01 | Linux Debian 12 | 4 GB | 30 GB | SSH bastion + VPN |
| 115 | files01 | Linux Debian 12 | 8 GB | 2 TB | SMB/NFS file server |

Totale: 224 GB RAM, 5.5 TB storage.

Gruppo HA "production": tutte le VM eccetto bastion01 e jenkins01 (resilient via altre vie).

---

## Deliverables richiesti

### 1. Assessment & Planning Document (10-15 pagine)

Cosa includere:
- Inventario VMware (15 VM con dettagli).
- Dependency map (chi dipende da chi).
- Risk register (tech + business).
- Proposed Proxmox architecture con diagram.
- Migration plan a wave (3-4 wave, timing).
- Timeline (gantt o equivalente).
- Cost analysis: VMware 3 anni post-Broadcom vs Proxmox 3 anni.
- Sponsor approval section.

### 2. Cluster Proxmox costruito

Validazione:
- `pvecm status` → 3 voti, Quorate.
- `ceph -s` → HEALTH_OK.
- `ha-manager status` → 1 VM test successfully migrated.
- `proxmox-backup-server` → 1 backup test eseguito + restore verificato.
- Networking: jumbo frames validate (`ping -M do -s 8972`).

### 3. Migration esecuzione

- Tutte le 15 VM migrate operative su Proxmox.
- Nessun BSOD irrecuperabile.
- AD trust integrita: `dcdiag /v` clean.
- Database integrita: row counts match.
- Performance: TPS DB e IOPS storage entro 110% baseline VMware.

### 4. Cutover Runbook v1.0

Documento operativo del cutover finale, in stile production-ready (vedi `18-PRODUCTION-CUTOVER-RUNBOOK.md`).

### 5. DR setup + drill report

- Configurazione ZFS replication tra Site Produzione e Site DR.
- Esecuzione DR drill end-to-end.
- Report: RTO misurato, RPO misurato, gap identificati, action items.

### 6. Day-2 operations

- 1 settimana di monitoring post-cutover documentato.
- Backup runs verificati su PBS.
- Almeno 1 incident gestito (anche simulato).
- Post-mortem report di un incident.

### 7. Final presentation (30 min)

Audience: CIO + IT Director (simulati).
Contenuto:
- Risultati: TCO saving, RTO, RPO, uptime.
- Lessons learned.
- Roadmap futura (next 12 mesi).
- Q&A.

---

## Rubric di valutazione

| Categoria | Peso | Criteri di eccellenza | Criteri minimi |
|---|---|---|---|
| **Pianificazione** | 15% | Risk register dettagliato, dependency map verificata, timeline realistica | Documento esistente, dipendenze identificate |
| **Costruzione cluster** | 20% | Production-ready (HA, Ceph, PBS, networking dedicato, jumbo, hardening) | Cluster funzionante a 3 nodi |
| **Migrazione esecuzione** | 25% | Tutte 15 VM, performance >= 100% baseline, zero data loss | 12+ VM migrate, performance >= 90% |
| **Runbook qualita** | 10% | Esecutore terzo puo seguirlo da zero senza guida | Operativo, completo |
| **DR drill** | 15% | RTO < 4h, RPO < 30 min, post-mortem rigoroso | RTO < 8h, RPO < 1h |
| **Day-2 ops** | 10% | Incident gestiti con RCA + action items | Monitoring attivo, backup testati |
| **Presentazione** | 5% | Tecnico-business equilibrato, dati concreti | Coverage completa |

**Soglia di passaggio**: ≥ 70% complessivo.
**Distinzione**: ≥ 90% complessivo.

---

## Risorse di supporto

- Tutti i moduli del corso (01-19).
- Case study Broadcom (`99-CASE-STUDY/broadcom-vmware-2024.md`).
- Lab e scenari (`99-ESERCIZI/`).
- Glossario folder (`00-GLOSSARIO.md`).
- Bibliografia (`00-BIBLIOGRAFIA.md`).
- Hardware: l'esercizio puo essere eseguito su 3 server fisici, 3 VM nested, o cluster cloud (es. Hetzner dedicated).

---

## Domande di review (auto-valutazione finale)

1. Quale e stato il rischio piu sottovalutato nel tuo plan iniziale e perche?
2. Quale modulo del corso e stato piu utile e quale meno?
3. Se dovessi rifare il progetto, cosa cambieresti?
4. Il tuo cutover runbook e sufficiente per un team che non ha mai fatto migrazione? Argomenta.
5. Quale e l'RTO realistico raggiunto e cosa lo limita?
6. Quale capability del corso ti senti meno solido e su cui investiresti formazione aggiuntiva?

---

## Successo del Capstone = competenza dimostrata

Il Capstone non e un test "sapere": e un test "operare". Completare il progetto al 70%+ con un terzo che valida l'output significa, in termini Dreyfus, aver raggiunto **proficient** sulla migrazione VMware → Proxmox. Da li, l'expert level si sviluppa con esperienze multiple in produzione, contributi open-source al progetto Proxmox, e progetti di scala maggiore (50+ nodi, multi-region, compliance regolamentate).
