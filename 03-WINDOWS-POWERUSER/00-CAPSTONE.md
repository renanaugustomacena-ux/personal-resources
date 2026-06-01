# Capstone — Amministrazione Windows Enterprise

> **Tempo stimato:** 40-60 ore in 4-6 settimane
> **Livello:** proficient → expert
> **Prerequisiti:** completamento di tutti i moduli del corso (Fasi 1-7)
> **Aggiornamento:** 2026-05-23

---

## Scenario

Sei il system administrator senior di un'azienda media (500 utenti, 3 sedi) che sta standardizzando la propria infrastruttura Windows. Il tuo compito è progettare e implementare un ambiente Active Directory enterprise-grade con gestione moderna degli endpoint, PKI interna, alta disponibilità e un piano di disaster recovery documentato e testato.

---

## Deliverable

### D1 — Forest Design e Active Directory (10-12 ore)

1. **Forest design document** con:
   - Singola forest, dominio root + child domain (o giustificazione single-domain)
   - OU structure con modello di delegazione (tier 0/1/2)
   - Sites e replication topology per 3 sedi (HQ + 2 branch)
   - FSMO placement e giustificazione
   - RODC per branch office con Password Replication Policy
   - DNS integrato con forwarder e conditional forwarder

2. **Implementazione su lab** (3+ DC, 2+ client):
   - Forest funzionale level Windows Server 2022
   - Sites e subnet configurati
   - Replication verificata con `repadmin /replsummary`
   - `dcdiag /v` senza errori

### D2 — Group Policy e Hardening (8-10 ore)

1. **Catalogo GPO** (minimo 30 policy) organizzato per:
   - Security baseline (CIS Benchmark Level 1)
   - Desktop configuration (wallpaper, start menu, drive mapping)
   - Software restriction (AppLocker o WDAC)
   - Audit policy (Advanced Audit Policy Configuration)
   - Ogni GPO con rationale documentato

2. **Hardening Windows Server** secondo CIS Benchmark:
   - Firewall rules
   - Service hardening
   - Credential Guard abilitato
   - LAPS deployato su tutti i client
   - Protected Users group per admin Tier 0
   - SMBv1 disabilitato, SMB signing enforced

### D3 — PKI e Certificati (6-8 ore)

1. **Infrastruttura PKI two-tier**:
   - Root CA offline (standalone)
   - Issuing CA enterprise (joined al dominio)
   - CRL Distribution Point (CDP) via HTTP + LDAP
   - OCSP Responder configurato

2. **Certificate template** personalizzati per:
   - Computer auto-enrollment
   - Web server (IIS)
   - Smart card logon (opzionale)
   - Code signing

3. **Hardening AD CS** contro ESC1-ESC8:
   - Review template permissions
   - Manager approval per template sensibili
   - Audit trail configurato

### D4 — Intune e Hybrid Identity (6-8 ore)

1. **Entra Connect** configurato con:
   - Password Hash Sync + Seamless SSO
   - OU filtering
   - Device writeback
   - Staging mode documentato

2. **Intune policies**:
   - Compliance policy (BitLocker, antivirus, firewall, OS version)
   - Configuration profiles (Wi-Fi, VPN, certificati)
   - Conditional Access: richiedere compliance per accesso risorse

3. **Autopilot deployment** (se possibile):
   - Profile configurato
   - OOBE personalizzato
   - User-driven join documentato

### D5 — Hyper-V e Alta Disponibilità (6-8 ore)

1. **Cluster Hyper-V** a 3 nodi con:
   - Failover Clustering configurato
   - Cloud Witness (o File Share Witness)
   - CSV (Cluster Shared Volumes)
   - Live migration funzionante
   - Anti-affinity rules per VM critiche

2. **VM di test** con:
   - Hyper-V Replica verso secondo sito (simulato)
   - Checkpoint policy: production only
   - Resource metering attivo

### D6 — DR Plan e Automazione (6-8 ore)

1. **AD/PKI DR procedure** documentata e testata:
   - Backup System State offline (settimanale)
   - Forest recovery procedure (scenario: tutti i DC distrutti)
   - CA recovery procedure
   - Restore drill eseguito con report

2. **PowerShell automation**:
   - Script deployment nuovi DC
   - Script health check (dcdiag, repadmin, DNS)
   - Script backup automatizzato
   - Tutti gli script con Pester test

3. **Runbook operativo** con procedure per:
   - FSMO seizure (scenario: DC primario guasto)
   - Certificate renewal e revocation
   - Entra Connect disaster recovery
   - Patch rollback (KB problematico)

### D7 — Documentazione e Demo (2-4 ore)

1. **Documento architetturale** con diagramma dell'infrastruttura
2. **Registro decisioni** (ADR): per ogni scelta progettuale
3. **Demo live** (20 minuti):
   - Forest health (dcdiag, repadmin)
   - GPO applicata (gpresult /h)
   - Certificato auto-enrolled
   - Failover VM tra nodi cluster
   - Restore drill AD (o walkthrough)

---

## Rubric di Valutazione

| Area | Peso | Pass (70%) | Distinction (90%) |
|------|------|------------|-------------------|
| **AD Design** | 20% | Forest funzionale, OU strutturate | Multi-tier, RODC, sites ottimizzati, dcdiag clean |
| **GPO/Hardening** | 20% | 20+ GPO, baseline applicata | 30+ GPO, CIS L1, LAPS, Credential Guard, WDAC |
| **PKI** | 15% | CA singola, auto-enrollment | Two-tier, OCSP, ESC hardening, CDP HTTP |
| **Intune/Hybrid** | 15% | Entra Connect + compliance base | CA risk-based, Autopilot, device writeback |
| **Hyper-V/HA** | 15% | Cluster 2+ nodi funzionante | 3 nodi, CSV, Replica, anti-affinity |
| **DR/Automazione** | 15% | Backup documentato, script base | Restore drill testato, Pester, runbook completo |

**Totale: 100%. Pass ≥ 70%, Distinction ≥ 90%.**

---

## Vincoli

- **Ambiente**: VM (Hyper-V nested, VMware Workstation, o Proxmox) con almeno 32 GB RAM host
- **Licenze**: Windows Server 2022 Evaluation (180 giorni), Windows 10/11 Enterprise Eval
- **Cloud**: tenant Microsoft 365 Developer (gratuito) per Entra ID e Intune
- **Distribuzione**: Windows Server 2022 (preferito) o 2025 Preview
- **Tempo**: 4-6 settimane a ritmo personale, stimato 40-60 ore totali

---

## Suggerimenti

1. **Parti dal forest design** — è la fondazione. Errori qui sono costosi da correggere.
2. **Documenta mentre fai** — le decisioni di design si dimenticano rapidamente.
3. **Testa il DR** — un backup non testato non è un backup. Esegui il restore drill.
4. **Usa PowerShell per tutto** — se lo fai a mano, non è ripetibile.
5. **Simula failure** — spegni un DC, rimuovi un nodo cluster, revoca un certificato. Verifica recovery.

---

## Cross-link al percorso

| Deliverable | Moduli chiave |
|-------------|---------------|
| D1 AD Design | 01, 25 (AD), 06 (rete) |
| D2 GPO/Hardening | 21 (GPO), 29 (hardening), 05 (sicurezza), 24 (Defender) |
| D3 PKI | 28 (PKI), 11 (certificati) |
| D4 Intune/Hybrid | 26, 32 (Intune), 13, 30 (hybrid identity) |
| D5 Hyper-V/HA | 23 (Hyper-V), 27 (clustering), 07 (storage) |
| D6 DR/Automazione | 34 (DR), 22 (PowerShell), 15 (backup) |
| D7 Documentazione | 19 (troubleshooting), 20 (guide pratiche) |
