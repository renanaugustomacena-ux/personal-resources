# Indice — Amministrazione Windows Enterprise

> **Corso:** Amministrazione Windows enterprise (AD/GPO/Intune)
> **Aggiornamento:** 2026-05-23
> **Moduli:** 34 + 2 case study + scaffolding
> **Percorso consigliato:** vedi [00-SYLLABUS.md](00-SYLLABUS.md)

---

## File di Scaffolding

| File | Scopo | Stato |
|------|-------|-------|
| [00-SYLLABUS.md](00-SYLLABUS.md) | Percorso formativo, fasi, prerequisiti, capstone | stable |
| [00-INDEX.md](00-INDEX.md) | Questo file — indice completo | stable |
| [00-GLOSSARIO.md](00-GLOSSARIO.md) | Glossario termini introdotti nel corso | stable |
| [00-BIBLIOGRAFIA.md](00-BIBLIOGRAFIA.md) | Fonti primarie consolidate | stable |
| [00-CAPSTONE.md](00-CAPSTONE.md) | Progetto finale: brief, deliverable, rubric | stable |
| [00-guida-allo-studio.md](00-guida-allo-studio.md) | Guida allo studio originale (legacy) | base |

---

## Moduli del Corso

### Fase 1 — Fondamenti

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 01 | [active-directory.md](01-active-directory.md) | AD DS, domain/forest, DC, FSMO, replica, DNS integrato, OU | stable |
| 02 | [powershell.md](02-powershell.md) | Cmdlet, pipeline, oggetti, provider, remoting, scripting base | stable |
| 04 | [registry.md](04-registry.md) | Hive, chiavi, valori, GPO→registry mapping, troubleshooting | stable |
| 03 | [ruoli-server.md](03-ruoli-server.md) | DHCP, DNS, File Server, Print, WSUS, WDS, ruoli e feature | stable |

### Fase 2 — Sicurezza

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 05 | [sicurezza-windows.md](05-sicurezza-windows.md) | BitLocker, Credential Guard, Windows Firewall, audit, UAC | stable |
| 08 | [permessi-e-accesso.md](08-permessi-e-accesso.md) | NTFS, share permissions, delegazione, inheritance, effective access | stable |
| 11 | [servizi-certificati.md](11-servizi-certificati.md) | AD CS, CA configuration, template base, enrollment | stable |
| 24 | [windows-defender-endpoint-security.md](24-windows-defender-endpoint-security.md) | WDAC, AppLocker, ASR rules, Controlled Folder Access, EDR | stable |
| 28 | [pki-certificati-guida-completa.md](28-pki-certificati-guida-completa.md) | CA hierarchy, CRL/OCSP, template avanzati, AD CS hardening, ESC attacks | stable |
| 29 | [windows-server-hardening.md](29-windows-server-hardening.md) | CIS Benchmark, STIG, credential protection, audit policy, GPO hardening | stable |

### Fase 3 — Network e Storage

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 06 | [rete-windows.md](06-rete-windows.md) | TCP/IP, DNS client/server, DHCP, NLB, NIC teaming, IPsec | stable |
| 07 | [storage-windows.md](07-storage-windows.md) | Dischi, Storage Spaces, DFS, iSCSI, dedup, ReFS | stable |
| 18 | [driver-compatibilita.md](18-driver-compatibilita.md) | Driver signing, compatibilità, Device Manager, troubleshooting | stable |

### Fase 4 — Operations

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 09 | [monitoraggio-performance.md](09-monitoraggio-performance.md) | Performance Monitor, Resource Monitor, WMI queries, Data Collector | stable |
| 10 | [gestione-aggiornamenti.md](10-gestione-aggiornamenti.md) | WSUS, WUFB, ring deployment, patch rollback, KB management | stable |
| 15 | [backup-ripristino.md](15-backup-ripristino.md) | Windows Server Backup, VSS, bare metal restore, DPM/MABS | stable |
| 16 | [profili-e-servizi.md](16-profili-e-servizi.md) | User profiles, servizi Windows, scheduled tasks, startup | stable |
| 19 | [troubleshooting.md](19-troubleshooting.md) | Event Viewer, diagnostica avanzata, alberi decisionali, scenari | stable |
| 20 | [guide-pratiche.md](20-guide-pratiche.md) | Procedure operative, checklist, runbook, best practice | stable |
| 14 | [batch-scripting.md](14-batch-scripting.md) | CMD, batch file, automazione legacy, migrazione a PowerShell | stable |

### Fase 5 — Advanced

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 21 | [group-policy-guida-completa.md](21-group-policy-guida-completa.md) | ADMX, WMI filter, loopback, preference items, security filtering | stable |
| 22 | [powershell-scripting-avanzato.md](22-powershell-scripting-avanzato.md) | PSRemoting SSH, JEA, Pester, moduli, DSC, security | stable |
| 23 | [hyper-v-guida-completa.md](23-hyper-v-guida-completa.md) | vSwitch, live migration, Replica, Shielded VMs, nested virt | stable |
| 25 | [active-directory-design-avanzato.md](25-active-directory-design-avanzato.md) | Forest design, tier model, ESAE, FSMO placement, sites/replication | stable |
| 27 | [failover-clustering-guida.md](27-failover-clustering-guida.md) | Quorum, CSV, Storage Spaces Direct, CAU, multi-site cluster | stable |
| 31 | [iis-web-server-guida-completa.md](31-iis-web-server-guida-completa.md) | HTTP.sys, app pool, ARR, TLS/SNI, URL rewrite, hardening | stable |

### Fase 6 — Cloud e Endpoint

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 12 | [endpoint-management.md](12-endpoint-management.md) | SCCM/MECM, deployment, imaging, software distribution | stable |
| 13 | [azure-ad-identita-ibrida.md](13-azure-ad-identita-ibrida.md) | Entra ID, sync base, SSO, conditional access intro | stable |
| 26 | [intune-gestione-moderna.md](26-intune-gestione-moderna.md) | MDM, compliance policy, conditional access, app management | stable |
| 30 | [identita-ibrida-azure-ad-dettaglio.md](30-identita-ibrida-azure-ad-dettaglio.md) | Entra Connect, PHS/PTA/federation, CA risk-based, MFA recovery | stable |
| 32 | [intune-mdm-mam.md](32-intune-mdm-mam.md) | App protection policy, configuration profiles, Autopilot | stable |
| 33 | [multi-forest-ad-trust.md](33-multi-forest-ad-trust.md) | Trust types, cross-forest migration, SID history, selective auth | stable |
| 34 | [disaster-recovery-ad-pki.md](34-disaster-recovery-ad-pki.md) | AD forest recovery, CA backup/restore, DR drill, runbook | stable |

### Fase 7 — WSL Bridge

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 17 | [wsl.md](17-wsl.md) | WSL 2, networking, filesystem, sviluppo, integrazione Windows | stable |

---

## Materiale Supplementare

### Case Study

| File | Argomento |
|------|-----------|
| [99-CASE-STUDY/storm-0558-microsoft-key.md](99-CASE-STUDY/storm-0558-microsoft-key.md) | Compromissione chiave MSA Microsoft — token forgery e impatto cloud |
| [99-CASE-STUDY/notpetya-active-directory.md](99-CASE-STUDY/notpetya-active-directory.md) | NotPetya 2017: distruzione AD via supply chain, caso Maersk |

### Esercizi Extra

| Directory | Contenuto |
|-----------|-----------|
| [99-ESERCIZI/](99-ESERCIZI/) | Lab e scenari pratici per modulo |
