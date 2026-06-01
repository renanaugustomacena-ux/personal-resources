# Indice del Corso — Migrazione VMware → Proxmox VE

> **Tipo:** indice operativo del corso (file di navigazione)
> **Tipo modulo:** scaffolding di corso, non contenuto didattico
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento del corso:** Proxmox VE 8.x (con note di transizione a 9.x), VMware vSphere/ESXi 8.0 GA → 8.0 U3i (P08), virt-v2v 2.x, qemu-img 8.x+
> **Lingua:** italiano

Questo file e l'indice navigabile del corso. Per la struttura formale, gli obiettivi di apprendimento e il percorso didattico, vedi `00-SYLLABUS.md`. Per la guida storica originale, vedi `00-GUIDA-ALLO-STUDIO/guida-allo-studio-migrazione.md` (preservata integralmente).

## Stato dei moduli

Legenda stato:
- `[stable]` — modulo letto, completo, con scaffolding didattico applicato (frontmatter + esercizi + auto-valutazione + letture primarie + collegamenti incrociati + glossario locale)
- `[base]` — contenuto tecnico originale completo, in attesa dello scaffolding didattico
- `[draft]` — contenuto in espansione (depth additions in corso)
- `[needs-review]` — modulo da rileggere per coerenza interna o aggiornamento

| # | Modulo | File | Linee | Stato |
|---|---|---|---|---|
| 00 | Guida allo Studio (storica) | `00-GUIDA-ALLO-STUDIO/guida-allo-studio-migrazione.md` | 1031 | base |
| 01.1 | Architettura vSphere e ESXi | `01-FONDAMENTI-VMWARE/architettura-vsphere-esxi.md` | 651 | stable |
| 01.2 | VMware Networking e Storage | `01-FONDAMENTI-VMWARE/vmware-networking-storage.md` | 1702 | stable |
| 02.1 | Architettura e Installazione Proxmox | `02-FONDAMENTI-PROXMOX-VE/architettura-installazione-proxmox.md` | 1563 | stable |
| 02.2 | Gestione VM e Container Proxmox | `02-FONDAMENTI-PROXMOX-VE/gestione-vm-container-proxmox.md` | 1719 | stable |
| 03.1 | LVM e LVM-Thin Proxmox | `03-STORAGE-AVANZATO-PROXMOX/lvm-e-lvm-thin-proxmox.md` | 1049 | stable |
| 03.2 | NFS e iSCSI Storage Condiviso | `03-STORAGE-AVANZATO-PROXMOX/nfs-iscsi-storage-condiviso.md` | 1234 | stable |
| 04.1 | Linux Bridge, VLAN, Bonding | `04-NETWORKING-AVANZATO-PROXMOX/linux-bridge-vlan-bonding.md` | 1244 | stable |
| 05.1 | Inventario VMware (Assessment) | `05-ASSESSMENT-E-PIANIFICAZIONE/inventario-vmware-assessment.md` | 927 | stable |
| 05.2 | Analisi Dipendenze e Criticita | `05-ASSESSMENT-E-PIANIFICAZIONE/analisi-dipendenze-e-criticita.md` | 884 | stable |
| 05.3 | Dimensionamento Proxmox (Capacity Planning) | `05-ASSESSMENT-E-PIANIFICAZIONE/dimensionamento-proxmox-capacity-planning.md` | 886 | stable |
| 05.4 | Timeline e Risk Assessment | `05-ASSESSMENT-E-PIANIFICAZIONE/timeline-e-risk-assessment.md` | 869 | stable |
| 06.1 | Strategie e Metodi di Migrazione | `06-STRATEGIE-E-METODI-MIGRAZIONE/strategie-metodi-migrazione.md` | 1031 | stable |
| 06.2 | Migrazione con virt-v2v | `06-STRATEGIE-E-METODI-MIGRAZIONE/migrazione-con-virt-v2v.md` | 1004 | stable |
| 06.3 | Live Migration a Minimo Downtime | `06-STRATEGIE-E-METODI-MIGRAZIONE/live-migration-minimo-downtime.md` | 998 | stable |
| 07.1 | IP Planning, DNS, DHCP, Firewall | `07-MIGRAZIONE-NETWORKING/ip-planning-dns-dhcp-firewall.md` | 1168 | stable |
| 07.2 | Mapping vSwitch ↔ Linux Bridge | `07-MIGRAZIONE-NETWORKING/mapping-vswitch-linux-bridge.md` | 933 | stable |
| 07.3 | Migrazione VLAN e Segmentazione | `07-MIGRAZIONE-NETWORKING/migrazione-vlan-e-segmentazione.md` | 987 | stable |
| 08.1 | Conversione VMDK ↔ qcow2 ↔ raw | `08-MIGRAZIONE-STORAGE/conversione-vmdk-qcow2-raw.md` | 1099 | stable |
| 08.2 | Shared Storage Cutover (NFS/iSCSI) | `08-MIGRAZIONE-STORAGE/shared-storage-cutover-nfs-iscsi.md` | 1028 | stable |
| 08.3 | Strategie Migrazione Datastore | `08-MIGRAZIONE-STORAGE/strategie-migrazione-datastore.md` | 1001 | stable |
| 08.4 | Validazione Performance Storage | `08-MIGRAZIONE-STORAGE/validazione-performance-storage.md` | 1324 | stable |
| 09.1 | Migrazione Applicazioni Stateful | `09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-applicazioni-stateful.md` | 994 | stable |
| 09.2 | Migrazione Database (PostgreSQL/MySQL) | `09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-database-postgresql-mysql.md` | 1094 | stable |
| 09.3 | Migrazione High-I/O Workloads | `09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-high-io-workloads.md` | 1314 | stable |
| 09.4 | Migrazione Windows Server VM | `09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-windows-server-vm.md` | 1192 | stable |
| 10.1 | HA Manager — Regole e Gruppi | `10-CLUSTER-HA-PROXMOX-POST-MIGRAZIONE/ha-manager-regole-e-gruppi.md` | 1056 | stable |
| 10.2 | Live Migration Interna a Proxmox | `10-CLUSTER-HA-PROXMOX-POST-MIGRAZIONE/live-migration-proxmox-interna.md` | 1108 | stable |
| 10.3 | Fencing e STONITH | `10-CLUSTER-HA-PROXMOX-POST-MIGRAZIONE/fencing-e-stonith.md` | 1006 | stable |
| 10.4 | Bilanciamento di Carico VM | `10-CLUSTER-HA-PROXMOX-POST-MIGRAZIONE/bilanciamento-carico-vm.md` | 992 | stable |
| 11.1 | Backup VM e Container (vzdump) | `11-BACKUP-E-RIPRISTINO-PROXMOX/backup-vm-e-container.md` | 1149 | stable |
| 11.2 | Configurazione Proxmox Backup Server | `11-BACKUP-E-RIPRISTINO-PROXMOX/proxmox-backup-server-configurazione.md` | 1126 | stable |
| 12.1 | Certificati SSL/TLS Proxmox | `12-SICUREZZA-E-COMPLIANCE/certificati-ssl-tls-proxmox.md` | 884 | stable |
| 12.2 | Autenticazione LDAP / AD | `12-SICUREZZA-E-COMPLIANCE/autenticazione-ldap-ad-proxmox.md` | 921 | stable |
| 12.3 | Sicurezza e Compliance Proxmox | `12-SICUREZZA-E-COMPLIANCE/sicurezza-compliance.md` | 956 | stable |
| 13.1 | Monitoraggio con Zabbix | `13-MONITORAGGIO-E-OTTIMIZZAZIONE/zabbix-monitoraggio-proxmox.md` | 1185 | stable |
| 14.1 | Cloud-Init Template per VM | `14-AUTOMAZIONE-E-INFRASTRUCTURE-AS-CODE/cloud-init-template-vm.md` | 970 | stable |
| 14.2 | API Proxmox e Script di Automazione | `14-AUTOMAZIONE-E-INFRASTRUCTURE-AS-CODE/proxmox-api-automazione-script.md` | 1547 | stable |
| 15.1 | Presentazione Cliente / Business Case | `15-ASPETTI-BUSINESS-E-CLIENTE/presentazione-cliente-business-case.md` | 891 | stable |
| 16.1 | Runbook Migrazione Batch | `16-PROCEDURE-OPERATIVE-E-RUNBOOK/runbook-migrazione-batch.md` | 1056 | stable |
| 16.2 | Runbook Migrazione Cluster Completo | `16-PROCEDURE-OPERATIVE-E-RUNBOOK/runbook-migrazione-cluster-completo.md` | 1170 | stable |
| 17.1 | Troubleshooting Cluster Proxmox | `17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-cluster-proxmox.md` | 1003 | stable |
| 17.2 | Troubleshooting Driver e Dispositivi | `17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-driver-e-dispositivi.md` | 1000 | stable |
| 17.3 | Troubleshooting Networking Post-Migrazione | `17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-networking-post-migrazione.md` | 1054 | stable |
| 17.4 | Troubleshooting Storage Performance | `17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-storage-performance.md` | 893 | stable |
| 18 | **Production Cutover Runbook** (nuovo) | `18-PRODUCTION-CUTOVER-RUNBOOK.md` | 343 | stable |
| 19 | **Multi-Site DR Proxmox** (nuovo) | `19-MULTI-SITE-DR-PROXMOX.md` | 357 | stable |

## File del corso (scaffolding)

| File | Scopo | Stato |
|---|---|---|
| `00-INDEX.md` | Questo file. Indice navigabile e tracker di stato | stable |
| `00-SYLLABUS.md` | Struttura formale del corso, prerequisiti, percorso, assessment | stable |
| `00-BIBLIOGRAFIA.md` | Hub centrale delle fonti primarie citate dai moduli | stable |
| `00-GLOSSARIO.md` | Glossario terminologico del corso | stable |
| `00-CAPSTONE.md` | Progetto pratico finale di fine corso | stable |

## Cartelle ausiliarie

| Cartella | Contenuto | Stato |
|---|---|---|
| `99-ESERCIZI/` | Laboratori, scenari, problemi extra non in-line | stable (README + 7 scenari) |
| `99-CASE-STUDY/` | Analisi di incidenti reali e post-mortem | stable (Broadcom 2024) |

## Conteggio finale

- **Moduli scaffolded:** 44 / 44 in scope (esclusi `00-GUIDA-ALLO-STUDIO/` storico, preservato).
- **Nuovi moduli creati:** 2 (18, 19).
- **Files di corso:** 5 (INDEX, SYLLABUS, BIBLIOGRAFIA, GLOSSARIO, CAPSTONE).
- **Folders ausiliarie:** 2 (99-ESERCIZI, 99-CASE-STUDY).
- **Linee totali stimate:** ~50 000.

## Roadmap di lavoro su questo corso

1. ~~Scaffolding di corso (`00-INDEX`, `00-SYLLABUS`, `00-BIBLIOGRAFIA`)~~ — completato.
2. ~~Pass di approfondimento didattico modulo per modulo (01-17)~~ — completato 2026-04-27.
3. ~~Creazione moduli nuovi `18` e `19`~~ — completato 2026-04-27.
4. ~~Popolamento `99-ESERCIZI/` e `99-CASE-STUDY/`~~ — completato 2026-04-27 (README + scenari + Broadcom case study; ulteriori case study aggiungibili in futuro).
5. ~~Stesura `00-CAPSTONE.md` e `00-GLOSSARIO.md`~~ — completato 2026-04-27.
6. **Auto-revisione finale**: leggere 3 moduli a campione come uno studente nuovo; segnalare ogni passaggio ancora ambiguo. *(In corso, da completare in iterazione successiva.)*
7. **Aggiungere case study addizionali** (proposte): Atlassian off-VMware, AT&T-Broadcom lawsuit deep-dive, Hetzner+Proxmox migration patterns.
8. **Espansione `99-ESERCIZI/`**: dettagliare i 3 lab e 4 scenari listati nel README come file completi singoli con step-by-step.

## Cartella e modulo "non in scope" (preservato)

- `00-GUIDA-ALLO-STUDIO/guida-allo-studio-migrazione.md` — guida storica originale del corso, preservata integralmente come documento di archivio. Il contenuto e gia rappresentato e migliorato in `00-SYLLABUS.md`. Mantenuta per riferimento storico.
