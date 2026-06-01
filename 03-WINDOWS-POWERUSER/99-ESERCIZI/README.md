# 99-ESERCIZI — Amministrazione Windows Enterprise

> **Aggiornamento:** 2026-05-23

---

## Lab

| File | Argomento | Tempo | Livello |
|------|-----------|-------|---------|
| [lab-01-forest-design.md](lab-01-forest-design.md) | Progettazione e deploy forest AD multi-tier (3 sedi) | 3-4 ore | proficient |
| [lab-02-gpo-deploy.md](lab-02-gpo-deploy.md) | Catalogo 30+ GPO enterprise e CIS Baseline | 3-4 ore | proficient |
| [lab-03-intune-policy.md](lab-03-intune-policy.md) | Compliance policy e Conditional Access con Intune | 2-3 ore | proficient |
| [lab-04-ad-dr-drill.md](lab-04-ad-dr-drill.md) | AD Forest Recovery e DR Drill completo | 3-4 ore | expert |
| [lab-05-hyper-v-cluster.md](lab-05-hyper-v-cluster.md) | Cluster Hyper-V a 3 nodi con failover e Replica | 3-4 ore | expert |

## Scenari

| File | Argomento | Tempo | Livello |
|------|-----------|-------|---------|
| [scenario-01-mimikatz-detection.md](scenario-01-mimikatz-detection.md) | Rilevamento estrazione credenziali (MITRE T1003) | 1.5-2 ore | proficient |
| [scenario-02-bitlocker-tpm-fail.md](scenario-02-bitlocker-tpm-fail.md) | Recovery BitLocker con TPM failure | 1-1.5 ore | competent |
| [scenario-03-fsmo-loss.md](scenario-03-fsmo-loss.md) | FSMO seizure da DC inaccessibile | 1.5-2 ore | proficient |
| [scenario-04-pki-root-compromise.md](scenario-04-pki-root-compromise.md) | Compromissione Root CA e re-emissione catena | 2-2.5 ore | expert |

---

## Prerequisiti

- Ambiente lab con almeno 3 VM Windows Server 2022 Evaluation
- 32 GB RAM host (per nested Hyper-V)
- Tenant Microsoft 365 Developer (per lab Intune)
- Completamento moduli Fase 1-5 del corso

## Cross-link ai moduli

| Lab/Scenario | Moduli chiave |
|-------------|---------------|
| Lab 01 | 01 (AD), 25 (AD design), 06 (rete) |
| Lab 02 | 21 (GPO), 29 (hardening), 24 (Defender) |
| Lab 03 | 26, 32 (Intune), 13, 30 (hybrid identity) |
| Lab 04 | 34 (DR), 15 (backup), 28 (PKI) |
| Lab 05 | 23 (Hyper-V), 27 (clustering), 07 (storage) |
| Scenario 01 | 29 (hardening), 05 (sicurezza), 24 (Defender) |
| Scenario 02 | 05 (sicurezza), 19 (troubleshooting) |
| Scenario 03 | 01 (AD), 25 (AD design), 34 (DR) |
| Scenario 04 | 28 (PKI), 11 (certificati), 34 (DR) |
