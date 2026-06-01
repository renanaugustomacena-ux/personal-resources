# Guida allo Studio — Windows Power User

## Indice

- [Piano di Studio](#piano-di-studio)
- [Ambiente di Laboratorio](#ambiente-di-laboratorio)
- [Glossario Termini Windows](#glossario-termini-windows)
- [Risorse Consigliate](#risorse-consigliate)

---

## Piano di Studio

### Percorso Formativo Completo

Questo percorso copre l'amministrazione Windows Server e Client a livello avanzato, dalla gestione di Active Directory all'automazione con PowerShell, dalla sicurezza enterprise al troubleshooting avanzato.

### Fase 1: Fondamenti Infrastruttura (Settimane 1-4)

| Modulo | Argomento | Priorità |
|--------|-----------|----------|
| 01 | Active Directory — Domini, foreste, GPO, Kerberos, LDAP | Critica |
| 02 | PowerShell — Cmdlet, pipeline, scripting, remoting, DSC | Critica |
| 03 | Ruoli Server — DNS, DHCP, IIS, Hyper-V, RDS, WSUS | Alta |
| 04 | Registry — Architettura, hive, modifiche, deploy via GPO | Alta |

### Fase 2: Sicurezza e Rete (Settimane 5-8)

| Modulo | Argomento | Priorità |
|--------|-----------|----------|
| 05 | Sicurezza Windows — Defender, BitLocker, AppLocker, LAPS | Critica |
| 06 | Rete Windows — TCP/IP, DNS resolution, NIC avanzate | Alta |
| 07 | Storage Windows — Storage Spaces, ReFS, iSCSI, dedup | Alta |
| 08 | Permessi e Accesso — NTFS, ereditarietà, ACL, DAC | Critica |

### Fase 3: Gestione Enterprise (Settimane 9-12)

| Modulo | Argomento | Priorità |
|--------|-----------|----------|
| 09 | Monitoraggio Performance — PerfMon, Event Viewer, WAC | Alta |
| 10 | Gestione Aggiornamenti — WSUS, WUfB, patch management | Alta |
| 11 | Servizi Certificati — PKI, AD CS, template, enrollment | Media |
| 12 | Endpoint Management — SCCM/MECM, Intune, Autopilot | Alta |

### Fase 4: Identità Ibrida e Scripting (Settimane 13-16)

| Modulo | Argomento | Priorità |
|--------|-----------|----------|
| 13 | Azure AD e Identità Ibrida — Entra ID, Connect, MFA | Alta |
| 14 | Batch Scripting — CMD, robocopy, schtasks, WMIC | Media |
| 15 | Backup e Ripristino — WSB, VSS, BMR, DR planning | Critica |
| 16 | Profili e Servizi — Roaming, FSLogix, folder redirection | Media |

### Fase 5: Avanzato e Troubleshooting (Settimane 17-20)

| Modulo | Argomento | Priorità |
|--------|-----------|----------|
| 17 | WSL — Windows Subsystem for Linux, WSL2, sviluppo | Media |
| 18 | Driver e Compatibilità — Device Manager, shim, WDAC | Media |
| 19 | Troubleshooting — BSOD, boot, AD, DNS, performance | Critica |
| 20 | Guide Pratiche — Deployment dominio, migrazione, hardening | Alta |

### Certificazioni Correlate

| Certificazione | Focus | Livello |
|---------------|-------|---------|
| AZ-800 | Administering Windows Server Hybrid Core Infrastructure | Intermedio |
| AZ-801 | Configuring Windows Server Hybrid Advanced Services | Avanzato |
| AZ-104 | Azure Administrator | Intermedio |
| SC-300 | Identity and Access Administrator | Avanzato |
| MD-102 | Endpoint Administrator | Intermedio |

---

## Ambiente di Laboratorio

### Setup Consigliato

**Requisiti hardware minimi:**
- CPU: 4+ core (8 consigliati per lab multi-VM)
- RAM: 16 GB minimo (32 GB consigliati)
- Disco: 256 GB SSD (512 GB consigliati)
- Virtualizzazione hardware abilitata (VT-x/AMD-V)

### Architettura Lab

```
Lab Network (192.168.10.0/24)
├── DC01 (Windows Server 2022) — Domain Controller, DNS, DHCP
│   RAM: 4 GB | Disco: 60 GB | IP: 192.168.10.10
├── DC02 (Windows Server 2022) — DC secondario, replica
│   RAM: 4 GB | Disco: 60 GB | IP: 192.168.10.11
├── SRV01 (Windows Server 2022) — File Server, IIS, WSUS
│   RAM: 4 GB | Disco: 100 GB | IP: 192.168.10.20
├── CA01 (Windows Server 2022) — Certification Authority
│   RAM: 2 GB | Disco: 40 GB | IP: 192.168.10.25
├── CLIENT01 (Windows 11 Pro) — Workstation dominio
│   RAM: 4 GB | Disco: 60 GB | DHCP
└── LINUX01 (Ubuntu Server) — Per test interoperabilità
    RAM: 2 GB | Disco: 40 GB | IP: 192.168.10.50
```

### Piattaforme di Virtualizzazione

**Hyper-V (consigliato per lab Windows):**
```powershell
# Abilitare Hyper-V su Windows 10/11 Pro
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
# Riavvio necessario

# Creare switch virtuale interno
New-VMSwitch -SwitchName "LabNetwork" -SwitchType Internal
New-NetIPAddress -InterfaceAlias "vEthernet (LabNetwork)" -IPAddress 192.168.10.1 -PrefixLength 24
```

**Alternative:** VirtualBox (gratuito, cross-platform), VMware Workstation Pro, Proxmox VE.

### ISO Necessarie

- Windows Server 2022 Evaluation (180 giorni): Microsoft Evaluation Center
- Windows 11 Enterprise Evaluation (90 giorni): Microsoft Evaluation Center
- Windows Admin Center: download gratuito da Microsoft

### Esercizi Pratici per Ogni Fase

**Fase 1:** Installare DC01 e DC02, promuovere a Domain Controller, creare struttura OU, utenti e gruppi, applicare 5 GPO di base.

**Fase 2:** Configurare BitLocker su CLIENT01, implementare LAPS, configurare Windows Firewall via GPO, creare storage pool su SRV01.

**Fase 3:** Configurare WSUS su SRV01, abilitare audit policy avanzate, installare Windows Admin Center, configurare alerting via Event Viewer.

**Fase 4:** Installare AD CS su CA01, emettere certificati auto-enrollment, configurare backup Windows Server Backup, testare bare-metal recovery.

**Fase 5:** Analizzare un BSOD con WinDbg, risolvere problemi di replica AD, ottimizzare performance di un server lento, documentare una procedura di disaster recovery completa.

---

## Glossario Termini Windows

### Active Directory e Identità

| Termine | Descrizione |
|---------|-------------|
| **AD DS** | Active Directory Domain Services — servizio di directory per gestione identità e risorse |
| **DC** | Domain Controller — server che ospita il database AD e autentica utenti |
| **Forest** | Foresta — confine di sicurezza massimo in AD, contiene uno o più domini |
| **Domain** | Dominio — unità amministrativa e di sicurezza in AD |
| **OU** | Organizational Unit — container logico per organizzare oggetti AD |
| **GPO** | Group Policy Object — insieme di impostazioni applicate a utenti/computer |
| **Kerberos** | Protocollo di autenticazione basato su ticket usato in AD |
| **LDAP** | Lightweight Directory Access Protocol — protocollo per query AD |
| **SPN** | Service Principal Name — identificativo univoco per servizi in AD |
| **UPN** | User Principal Name — formato user@domain.com per login |
| **FSMO** | Flexible Single Master Operations — ruoli speciali per operazioni single-master |
| **GC** | Global Catalog — DC che contiene un subset di attributi di tutti gli oggetti della foresta |
| **Trust** | Relazione di fiducia tra domini per consentire accesso cross-domain |
| **Schema** | Definizione degli oggetti e attributi memorizzabili in AD |
| **SYSVOL** | Cartella replicata contenente script di logon e GPO |

### PowerShell e Automazione

| Termine | Descrizione |
|---------|-------------|
| **Cmdlet** | Comando nativo PowerShell nel formato Verb-Noun |
| **Pipeline** | Meccanismo per passare oggetti tra cmdlet con `\|` |
| **PSSession** | Sessione PowerShell remota (WinRM) |
| **DSC** | Desired State Configuration — gestione configurazione dichiarativa |
| **Module** | Pacchetto di cmdlet, funzioni e risorse PowerShell |
| **PSGallery** | Repository online di moduli PowerShell |
| **WinRM** | Windows Remote Management — protocollo per remoting |
| **JEA** | Just Enough Administration — endpoint con permessi limitati |
| **CIM/WMI** | Common Information Model / Windows Management Instrumentation |

### Sicurezza

| Termine | Descrizione |
|---------|-------------|
| **BitLocker** | Crittografia disco integrata in Windows |
| **LAPS** | Local Administrator Password Solution — password admin locali gestite da AD |
| **AppLocker** | Controllo applicazioni tramite regole whitelist/blacklist |
| **WDAC** | Windows Defender Application Control — successore moderno di AppLocker |
| **Credential Guard** | Isolamento credenziali tramite virtualizzazione |
| **DPAPI** | Data Protection API — crittografia dati utente |
| **NTLM** | NT LAN Manager — protocollo autenticazione legacy |
| **ACL** | Access Control List — lista di permessi su un oggetto |
| **DACL** | Discretionary ACL — permessi di accesso |
| **SACL** | System ACL — regole di audit |
| **SID** | Security Identifier — identificativo unico per ogni security principal |

### Infrastruttura

| Termine | Descrizione |
|---------|-------------|
| **WSUS** | Windows Server Update Services — server aggiornamenti locale |
| **WDS** | Windows Deployment Services — deploy immagini OS via rete |
| **SCCM/MECM** | System Center Configuration Manager / Microsoft Endpoint Configuration Manager |
| **Intune** | Servizio cloud Microsoft per gestione endpoint (MDM/MAM) |
| **WAC** | Windows Admin Center — console web di gestione server |
| **ADCS** | Active Directory Certificate Services — PKI integrata |
| **DFS** | Distributed File System — namespace e replica file distribuita |
| **NPS** | Network Policy Server — server RADIUS per autenticazione rete |
| **RDS** | Remote Desktop Services — accesso remoto desktop/applicazioni |
| **Storage Spaces** | Tecnologia software-defined storage di Windows |
| **ReFS** | Resilient File System — filesystem moderno per Windows Server |
| **Failover Clustering** | Alta disponibilità tramite cluster di server |
| **Hyper-V** | Hypervisor nativo Microsoft per virtualizzazione |

### Rete

| Termine | Descrizione |
|---------|-------------|
| **WINS** | Windows Internet Name Service — risoluzione nomi NetBIOS (legacy) |
| **NetBIOS** | Network Basic Input/Output System — protocollo rete legacy Windows |
| **SMB** | Server Message Block — protocollo condivisione file Windows |
| **CIFS** | Common Internet File System — implementazione Microsoft di SMB |
| **NIC Teaming** | Aggregazione schede di rete per throughput/ridondanza |

---

## Risorse Consigliate

### Documentazione Ufficiale
- Microsoft Learn (learn.microsoft.com) — Percorsi formativi gratuiti
- Windows Server Documentation
- PowerShell Documentation (docs.microsoft.com/powershell)

### Libri
- "Windows Server 2022 Inside Out" — Orin Thomas
- "Learn PowerShell in a Month of Lunches" — Travis Plunk, James Petty
- "PowerShell for Sysadmins" — Adam Bertram
- "Active Directory: Designing, Deploying, and Running AD" — Brian Desmond

### Strumenti
- Windows Admin Center (WAC) — Console gestione web
- RSAT (Remote Server Administration Tools) — Strumenti gestione remota
- Sysinternals Suite — Strumenti avanzati troubleshooting (Process Explorer, ProcMon, AutoRuns)
- WinDbg — Debugger per analisi crash dump
