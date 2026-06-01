# Syllabus — Amministrazione Windows Enterprise (AD/GPO/Intune)

> **Lingua:** italiano · **Aggiornamento:** 2026-05-23
> **Versioni:** Windows Server 2019/2022/2025; PowerShell 7.5+; Hyper-V Win Server 2025; Intune (current); Entra ID (ex Azure AD).
> **Moduli:** 34 + 2 case study + scaffolding
> **Tempo stimato:** 18-22 settimane (studio part-time) + 4-6 settimane capstone

---

## Identità

**"Amministrazione Windows enterprise"** — AD/GPO/Intune deep dive. Forest design, multi-forest trust, BitLocker recovery, PSRemoting over SSH, Hyper-V security, PKI/certificate, DR plan AD/PKI.

**Target:** competent → proficient → expert. Capace di progettare forest AD, implementare GPO + Intune, gestire PKI enterprise, e documentare DR plan completo.

## Prerequisiti

Linux fluent (corso 02); Windows Server fundamentals; Microsoft 365 admin basics.

## Obiettivi di Apprendimento

Al completamento del corso, lo studente sarà in grado di:

1. Progettare e implementare forest Active Directory multi-dominio con FSMO placement e replica ottimizzata.
2. Configurare Group Policy avanzate: ADMX 2019/2022/Intune mapping, MS16-072 mitigation, preference items.
3. Gestire PKI Windows enterprise: CA hierarchy, template, auto-enrollment, OCSP, CRL, certificate-based auth.
4. Amministrare Hyper-V: vSwitch security (MAC spoofing protection, VLAN isolation), live migration, Shielded VMs.
5. Implementare Failover Clustering: split-brain prevention, quorum models, CSV, Storage Spaces Direct.
6. Configurare Intune MDM/MAM per endpoint moderno: compliance policy, conditional access, app protection.
7. Progettare Hybrid Identity: Entra Connect, PHS/PTA/federation, risk-based Conditional Access, MFA recovery.
8. Gestire trust tra forest e migrazione AD cross-forest.
9. Pianificare e testare DR per AD e PKI: forest recovery, backup offline, restore drill.
10. Sviluppare script PowerShell avanzati: PSRemoting over SSH, JEA, Pester, moduli custom.
11. Hardenizzare Windows Server secondo CIS Benchmark: Credential Guard, WDAC, audit policy.
12. Gestire IIS come web server/reverse proxy enterprise con TLS hardening e ARR.

## Struttura del Corso

### Fase 1 — Fondamenti (settimane 1-3)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 01 | [Active Directory](01-active-directory.md) | Domain, forest, DC, FSMO, replica, DNS integrato |
| 02 | [PowerShell](02-powershell.md) | Cmdlet, pipeline, oggetti, provider, remoting base |
| 04 | [Registry](04-registry.md) | Hive, chiavi, GPO→registry, troubleshooting |
| 03 | [Ruoli server](03-ruoli-server.md) | DHCP, DNS, File Server, Print, WSUS, WDS |

### Fase 2 — Sicurezza (settimane 4-7)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 05 | [Sicurezza Windows](05-sicurezza-windows.md) | BitLocker, Credential Guard, firewall, audit |
| 08 | [Permessi e accesso](08-permessi-e-accesso.md) | NTFS, share, delegazione, inheritance |
| 11 | [Servizi certificati](11-servizi-certificati.md) | AD CS, CA, template, enrollment |
| 24 | [Defender endpoint](24-windows-defender-endpoint-security.md) | WDAC, ASR, Controlled Folder Access, EDR |
| 28 | [PKI certificati](28-pki-certificati-guida-completa.md) | CA hierarchy, CRL/OCSP, template, hardening |
| 29 | [Hardening Windows Server](29-windows-server-hardening.md) | CIS Benchmark, STIG, audit policy, GPO hardening |

### Fase 3 — Network e Storage (settimane 8-9)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 06 | [Rete Windows](06-rete-windows.md) | TCP/IP, DNS, DHCP, NLB, NIC teaming |
| 07 | [Storage Windows](07-storage-windows.md) | Dischi, Storage Spaces, DFS, iSCSI, dedup |
| 18 | [Driver e compatibilità](18-driver-compatibilita.md) | Driver signing, compatibilità, troubleshooting |

### Fase 4 — Operations (settimane 10-13)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 09 | [Monitoraggio performance](09-monitoraggio-performance.md) | Performance Monitor, Resource Monitor, WMI |
| 10 | [Gestione aggiornamenti](10-gestione-aggiornamenti.md) | WSUS, WUFB, ring deployment, rollback |
| 15 | [Backup e ripristino](15-backup-ripristino.md) | Windows Server Backup, VSS, bare metal, DPM |
| 16 | [Profili e servizi](16-profili-e-servizi.md) | User profiles, servizi Windows, scheduled tasks |
| 19 | [Troubleshooting](19-troubleshooting.md) | Event Viewer, diagnostica, alberi decisionali |
| 20 | [Guide pratiche](20-guide-pratiche.md) | Procedure operative, checklist, runbook |
| 14 | [Batch scripting](14-batch-scripting.md) | CMD, batch file, automazione legacy |

### Fase 5 — Advanced (settimane 14-17)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 21 | [GPO completa](21-group-policy-guida-completa.md) | ADMX, WMI filter, loopback, preference items |
| 22 | [PowerShell scripting avanzato](22-powershell-scripting-avanzato.md) | PSRemoting SSH, JEA, Pester, moduli, DSC |
| 23 | [Hyper-V completa](23-hyper-v-guida-completa.md) | vSwitch, live migration, Replica, Shielded VMs |
| 25 | [AD design avanzato](25-active-directory-design-avanzato.md) | Forest design, tier model, ESAE, FSMO, sites |
| 27 | [Failover clustering](27-failover-clustering-guida.md) | Quorum, CSV, S2D, CAU, multi-site |
| 31 | [IIS web server](31-iis-web-server-guida-completa.md) | App pool, ARR, TLS, URL rewrite, hardening |

### Fase 6 — Cloud e Endpoint (settimane 18-20)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 12 | [Endpoint management](12-endpoint-management.md) | SCCM, deployment, imaging |
| 13 | [Azure AD identità ibrida](13-azure-ad-identita-ibrida.md) | Entra ID, sync, SSO |
| 26 | [Intune gestione moderna](26-intune-gestione-moderna.md) | MDM, compliance, conditional access |
| 30 | [Identità ibrida dettaglio](30-identita-ibrida-azure-ad-dettaglio.md) | Entra Connect, PHS/PTA, CA risk-based |
| 32 | [Intune MDM/MAM](32-intune-mdm-mam.md) | App protection, configuration profiles, autopilot |
| 33 | [Multi-forest AD trust](33-multi-forest-ad-trust.md) | Trust types, migration, SID history |
| 34 | [DR AD/PKI](34-disaster-recovery-ad-pki.md) | Forest recovery, CA backup, restore drill |

### Fase 7 — WSL Bridge (settimana 21)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 17 | [WSL](17-wsl.md) | WSL 2, integrazione, networking, sviluppo |

### Fase 8 — Capstone (settimane 22-26)

Vedi [00-CAPSTONE.md](00-CAPSTONE.md) per il brief completo.

## Capstone

Forest AD multi-dominio + GPO enterprise + Intune deployment + DR plan documentato. Include: multi-tier hardening, PSRemoting over SSH, Hyper-V cluster con fencing, Entra Connect hybrid identity, PKI two-tier con OCSP. Dettagli in [00-CAPSTONE.md](00-CAPSTONE.md).

---

## Materiale Supplementare

| Risorsa | Scopo |
|---------|-------|
| [00-INDEX.md](00-INDEX.md) | Indice completo con sinossi |
| [00-GLOSSARIO.md](00-GLOSSARIO.md) | Glossario termini del corso |
| [00-BIBLIOGRAFIA.md](00-BIBLIOGRAFIA.md) | Fonti primarie consolidate |
| [00-CAPSTONE.md](00-CAPSTONE.md) | Progetto finale: brief, deliverable, rubric |
| [00-guida-allo-studio.md](00-guida-allo-studio.md) | Guida allo studio originale (legacy) |
| [99-CASE-STUDY/](99-CASE-STUDY/) | Case study: NotPetya, Storm-0558 |
| [99-ESERCIZI/](99-ESERCIZI/) | Esercizi aggiuntivi per modulo |

---

## Valutazione

| Componente | Peso |
|------------|------|
| Capstone: AD Forest Design | 20% |
| Capstone: GPO + Hardening CIS | 20% |
| Capstone: PKI + Certificate Management | 15% |
| Capstone: Intune + Hybrid Identity | 15% |
| Capstone: Hyper-V + Failover Clustering | 15% |
| Capstone: DR Plan + Restore Drill | 15% |

**Pass ≥ 70%, Distinction ≥ 90%.** Vedi [00-CAPSTONE.md](00-CAPSTONE.md) per la rubric dettagliata.
