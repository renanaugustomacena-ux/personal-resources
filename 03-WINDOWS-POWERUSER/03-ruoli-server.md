# Ruoli Server Windows — Guida Completa

> **Modulo 03** · **Aggiornamento:** 2026-05-22

> **Modulo del corso:** Amministrazione Windows enterprise
> **Prerequisiti:** [01-active-directory.md](01-active-directory.md), [06-rete-windows.md](06-rete-windows.md), [02-powershell.md](02-powershell.md)
> **Obiettivi di apprendimento:**
> 1. Confrontare Server Core, Desktop Experience e Nano Server per scenari di produzione
> 2. Installare e configurare i ruoli principali: DNS, DHCP, File Server, IIS, RDS, Hyper-V
> 3. Gestire licenze per-core e pianificare la separazione dei ruoli
> 4. Amministrare ruoli tramite Server Manager, WAC e PowerShell
> **Tempo stimato:** lettura 40 min · lab 60 min
> **Livello:** competent
> **Ultimo aggiornamento:** 2026-05-23

## Idee guida
1. **Server Core > Desktop Experience per produzione.** Smaller attack surface.
2. **Roles + Features modular install.**
3. **`Install-WindowsFeature` PS cmdlet.**
4. **AD DS, DHCP, DNS, IIS, RDS comuni roles.**
5. **Licensing per-core: minimo 16 core per server, venduti in pack da 2.**
6. **Separazione dei ruoli: massimo 1-2 ruoli per server.**


## Indice

- [Panoramica](#panoramica)
- [Edizioni Windows Server](#edizioni-windows-server)
- [Server Core vs Desktop Experience vs Nano Server](#server-core-vs-desktop-experience-vs-nano-server)
- [Novità di Windows Server 2025 per i Ruoli](#novità-di-windows-server-2025-per-i-ruoli)
- [Server Manager e Windows Admin Center](#server-manager-e-windows-admin-center)
- [DNS Server](#dns-server)
- [DHCP Server](#dhcp-server)
- [File Server e DFS](#file-server-e-dfs)
- [Print Server](#print-server)
- [IIS Web Server](#iis-web-server)
- [Remote Desktop Services](#remote-desktop-services)
- [Hyper-V](#hyper-v)
- [WSUS — Aggiornamenti](#wsus--aggiornamenti)
- [WDS — Deployment Services](#wds--deployment-services)
- [NPS — Network Policy Server](#nps--network-policy-server)
- [Storage Spaces](#storage-spaces)
- [Failover Clustering](#failover-clustering)
- [Azure Arc — Gestione Ibrida dei Ruoli Server](#azure-arc--gestione-ibrida-dei-ruoli-server)
- [Best Practices e Hardening](#best-practices-e-hardening)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Checklist di Deployment per Ruolo](#checklist-di-deployment-per-ruolo)

---

## Panoramica

Windows Server è progettato attorno al concetto di ruoli: ogni ruolo aggiunge funzionalità specifiche al server. La gestione dei ruoli avviene tramite Server Manager, PowerShell o Windows Admin Center.

Un **ruolo** rappresenta una funzione primaria del server (DNS, DHCP, File Server, IIS, etc.). Una **feature** è una funzionalità di supporto che può essere aggiunta indipendentemente (Failover Clustering, .NET Framework, BitLocker, etc.).

```powershell
# Installare un ruolo
Install-WindowsFeature -Name Web-Server -IncludeManagementTools
Install-WindowsFeature -Name DNS -IncludeManagementTools
Install-WindowsFeature -Name DHCP -IncludeManagementTools

# Verificare ruoli installati
Get-WindowsFeature | Where-Object Installed -eq $true

# Elencare tutti i ruoli disponibili con stato
Get-WindowsFeature | Select-Object Name, DisplayName, InstallState | Format-Table -AutoSize

# Rimuovere un ruolo
Uninstall-WindowsFeature -Name Web-Server -Remove  # -Remove rimuove anche i binari

# Installare ruolo su server remoto
Install-WindowsFeature -Name DNS -IncludeManagementTools -ComputerName SRV02

# Installare da sorgente offline (Features on Demand)
Install-WindowsFeature -Name Web-Server -Source "D:\Sources\SxS"
```

### Differenza tra Ruoli e Feature

| Categoria | Esempi | Note |
|-----------|--------|------|
| **Ruoli** | AD DS, DNS, DHCP, IIS, File Server, Hyper-V, RDS | Funzioni primarie del server |
| **Role Services** | DFS Namespaces, DFS Replication, FSRM | Sotto-componenti di un ruolo |
| **Features** | .NET, Failover Clustering, BitLocker, SNMP | Funzionalità trasversali |

---

## Edizioni Windows Server

### Standard vs Datacenter vs Essentials

| Caratteristica | Essentials | Standard | Datacenter |
|----------------|-----------|----------|------------|
| **Utenti massimi** | 25 utenti / 50 dispositivi | Illimitati (con CAL) | Illimitati (con CAL) |
| **CAL richieste** | No | Sì | Sì |
| **VM incluse (licenza)** | 1 fisico + 1 virtuale | 2 VM per licenza | VM illimitate |
| **Storage Spaces Direct** | No | No | Sì |
| **Software-Defined Networking** | No | No | Sì |
| **Shielded VMs** | No | No | Sì |
| **Storage Replica** | No | Limitato | Completo |
| **Nano Server (container host)** | No | Sì | Sì |
| **Host Guardian Service** | No | No | Sì |
| **Network Controller** | No | No | Sì |

### Modello di Licensing per-core

A partire da Windows Server 2016, il licensing è basato su core fisici:

- **Pack da 2 core**: le licenze si acquistano in pacchetti da 2 core
- **Minimo 8 core per processore fisico**: anche se il processore ha meno core, si pagano almeno 8
- **Minimo 16 core per server**: indipendentemente dal numero di processori
- **Esempio**: server con 2 CPU da 12 core = 24 core → 12 pack da 2 core

```
Esempio di calcolo licenze:
- Server con 1 CPU da 4 core:
  Minimo 8 core/CPU → 8 core → minimo 16 core/server → 16 core
  → 8 pack da 2 core

- Server con 2 CPU da 10 core:
  10 core × 2 CPU = 20 core (supera il minimo di 16)
  → 10 pack da 2 core

- Server con 4 CPU da 16 core:
  16 × 4 = 64 core
  → 32 pack da 2 core
```

### Client Access License (CAL)

Le CAL sono richieste per Standard e Datacenter (non per Essentials):

| Tipo CAL | Descrizione | Caso d'uso |
|----------|-------------|------------|
| **User CAL** | Licenza per utente, accesso da qualsiasi dispositivo | Utenti con più dispositivi |
| **Device CAL** | Licenza per dispositivo, usabile da qualsiasi utente | Kiosk, postazioni condivise |
| **RDS CAL** | Aggiuntiva per Remote Desktop Services | Accesso desktop remoto |
| **External Connector** | Accesso illimitato da utenti esterni | Portali web pubblici |

**Regola pratica**: se gli utenti hanno più dispositivi → User CAL. Se i dispositivi sono condivisi → Device CAL.

### Scelta dell'edizione

```
Piccola azienda (< 25 utenti):
  → Essentials (nessuna CAL, gestione semplificata, limiti utenti)

Aziende medie (virtualizzazione limitata):
  → Standard (2 VM incluse per licenza, CAL necessarie)

Datacenter / Cloud privato / Alta virtualizzazione:
  → Datacenter (VM illimitate, S2D, SDN, Shielded VMs)
```

---

## Novità di Windows Server 2025 per i Ruoli

Windows Server 2025 (LTSC, disponibilità generale novembre 2024) introduce cambiamenti strutturali che impattano direttamente la gestione dei ruoli server. Questa sezione sintetizza le novità più rilevanti per l'amministratore di produzione.

### Active Directory Domain Services — Livello funzionale 10

Il nuovo livello funzionale di foresta e dominio (Windows Server 2025, detto anche *functional level 10*) abilita funzionalità impossibili con livelli precedenti:

- **Pagine database ESE da 32 KB** — il motore Extensible Storage Engine passa dalle storiche pagine da 8 KB a 32 KB. Questo consente di gestire attributi multi-valore molto più grandi (fino a ~3.200 valori per pagina contro ~800) e riduce la frammentazione del database `ntds.dit`. L'aggiornamento avviene durante il `dcpromo` di un nuovo DC su Server 2025; i DC esistenti promossi a 2025 mantengono le pagine da 8 KB fino a un rebuild manuale.

```powershell
# Verificare livello funzionale corrente
Get-ADForest | Select-Object ForestMode
Get-ADDomain | Select-Object DomainMode

# Innalzare il livello funzionale (dopo che TUTTI i DC sono Server 2025)
Set-ADForestMode -Identity "corp.contoso.com" -ForestMode Windows2025Forest
Set-ADDomainMode -Identity "corp.contoso.com" -DomainMode Windows2025Domain

# Verificare dimensione pagine ESE su un DC
# (richiede esentutl disponibile su DC)
esentutl /mh "C:\Windows\NTDS\ntds.dit" | findstr /i "Page Size"
# Output atteso su nuovo DC 2025: "Page Size: 32768"
```

- **Delegated Managed Service Accounts (dMSA)** — evoluzione dei gMSA. Un dMSA può sostituire un account di servizio tradizionale con password manuale, ereditandone i permessi e migrando la dipendenza in modo trasparente. Il Credential Guard del server gestisce il ticket Kerberos senza mai esporre la password.

```powershell
# Creare un dMSA che sostituisce un account di servizio esistente
New-ADServiceAccount -Name "dmsa-webapp" `
    -DNSHostName "dmsa-webapp.corp.contoso.com" `
    -SupersededAccount "CN=svc-webapp-old,OU=ServiceAccounts,DC=corp,DC=contoso,DC=com" `
    -CreateDelegatedServiceAccount

# Il dMSA eredita i permessi dell'account sostituito
# e Credential Guard protegge il materiale Kerberos
```

### Sicurezza LDAP Rafforzata

Server 2025 applica di default politiche che prima erano opzionali:

| Impostazione | Comportamento precedente | Server 2025 |
|---|---|---|
| LDAP signing | Negoziato (non richiesto) | **Obbligatorio** di default |
| LDAP channel binding | Disabilitato | **Abilitato** di default |
| Audit binding LDAP non sicuri | Manuale | **Sempre attivo** (Event ID 3039) |

```powershell
# Verificare stato LDAP signing policy (2 = Required)
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "LDAPServerIntegrity"

# Verificare channel binding (1 = When supported, 2 = Always)
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "LdapEnforceChannelBinding"

# Nuovi contatori performance per troubleshooting LDAP client
# Performance Monitor → NTDS → LDAP Client Sessions:
#   "LDAP Binds with Signing", "LDAP Binds with Sealing"
#   Utili per identificare client che ancora usano binding non sicuro
```

### Hotpatching — Aggiornamenti di Sicurezza senza Riavvio

Windows Server 2025 supporta *hotpatching*: le patch di sicurezza mensili vengono applicate in memoria senza richiedere un reboot del sistema operativo. Requisiti:

- Server connesso ad **Azure Arc** (anche on-premises)
- Licenza Server 2025 Standard o Datacenter
- A partire da luglio 2025 il servizio hotpatch è **gratuito** per Server 2025 (precedentemente richiedeva una sottoscrizione aggiuntiva)

```powershell
# Prerequisito: installare l'agente Azure Arc (vedi sezione Azure Arc)
# Verificare lo stato hotpatch tramite Azure Arc
az connectedmachine extension show --machine-name "SRV01" `
    --resource-group "rg-servers" --name "WindowsOSExtension"

# Verificare lo stato hotpatch localmente
Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10

# Gli hotpatch appaiono come aggiornamenti KB normali
# ma con il flag "Hotpatch" nel Windows Update log
Get-WindowsUpdateLog  # genera il log in formato ETW
```

### SMB over QUIC — Ora in Standard Edition

Precedentemente limitato a Windows Server Azure Edition, SMB over QUIC è ora disponibile in **tutte le edizioni** di Server 2025 (Standard e Datacenter). Consente l'accesso a file share tramite protocollo QUIC (UDP 443, TLS 1.3) senza VPN, ideale per lavoratori remoti.

```powershell
# Abilitare SMB over QUIC sul server (richiede certificato TLS)
New-SmbServerCertificateMapping -Name "fs01.corp.contoso.com" `
    -Thumbprint "CERT_THUMBPRINT_HERE" -StoreName "My"

# Configurare la share per accesso QUIC
Set-SmbServerConfiguration -EnableSMBQUIC $true

# Client Windows 11 22H2+ può connettersi:
# NET USE Q: \\fs01.corp.contoso.com\Share /TRANSPORT:QUIC

# Verificare connessioni QUIC attive sul server
Get-SmbSession | Where-Object TransportName -eq "QUIC" |
    Select-Object ClientComputerName, ClientUserName, NumOpens
```

### DNS — Miglioramenti di Sicurezza

Il ruolo DNS in Server 2025 continua l'evoluzione iniziata con Server 2022:

- **DNS-over-HTTPS (DoH) lato server** — supporto confermato dalla build RTM. Protegge le query DNS in transito con crittografia HTTPS.
- **Nuovi contatori di performance LDAP/DNS** — visibilità granulare su query ricorsive, latenza di risoluzione e cache hit ratio.
- **Hardening di default**: le zone integrate AD usano DNSSEC-aware signing dove il livello funzionale lo supporta.

```powershell
# Abilitare DoH sul server DNS (Server 2022+ / Server 2025)
Set-DnsServerDohConfiguration -Enabled $true `
    -CertificateThumbprint "CERT_THUMBPRINT" -ListeningAddress "10.0.0.10"

# Verificare stato DoH
Get-DnsServerDohConfiguration

# Monitorare contatori DNS in PowerShell
Get-Counter '\DNS\Total Query Received/sec', '\DNS\Recursive Queries/sec',
    '\DNS\Cache Hits/sec' -SampleInterval 5 -MaxSamples 12
```

---

## Server Core vs Desktop Experience vs Nano Server

### Confronto delle modalità di installazione

| Aspetto | Server Core | Desktop Experience | Nano Server |
|---------|-------------|-------------------|-------------|
| **GUI** | No (solo CLI, PowerShell, `sconfig`) | Completa (Start menu, MMC, etc.) | No |
| **Dimensione disco** | ~6-8 GB | ~12-15 GB | ~500 MB (container) |
| **Superficie di attacco** | Minima | Ampia | Minima |
| **Aggiornamenti/riavvii** | Meno frequenti, più rapidi | Più frequenti | Minimi (container) |
| **Ruoli supportati** | Quasi tutti (no RDS Session Host GUI) | Tutti | Solo container host |
| **Gestione** | PowerShell, RSAT, WAC, `sconfig` | Locale + remota | Docker / container |
| **RAM tipica** | 512 MB - 2 GB | 2+ GB | 256 MB |

### Server Core — Gestione

Server Core è l'opzione raccomandata per server di produzione. Nessuna GUI, ma pieno supporto PowerShell e gestione remota.

```powershell
# sconfig — menu di configurazione testuale (disponibile out of the box)
sconfig

# Operazioni comuni da sconfig:
# 1 - Domain/Workgroup join
# 2 - Computer name
# 4 - Remote management
# 6 - Windows Update settings
# 7 - Remote Desktop enable
# 8 - Network settings
# 9 - Date and time
# 12 - Log off
# 13 - Restart
# 14 - Shut down

# Abilitare WinRM per gestione remota (di solito già attivo)
Enable-PSRemoting -Force

# Connettersi da remoto via PowerShell
Enter-PSSession -ComputerName SRV-CORE01 -Credential CORP\admin

# Installare ruoli da remoto
Invoke-Command -ComputerName SRV-CORE01 -ScriptBlock {
    Install-WindowsFeature -Name DNS -IncludeManagementTools
}

# Verificare se l'installazione è Server Core
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" |
    Select-Object InstallationType
# Server Core → "Server Core"
# Desktop Experience → "Server"
```

### Conversione tra Server Core e Desktop Experience

In Windows Server 2016/2019 è possibile convertire tra le due modalità (non consigliato in produzione; meglio reinstallare):

```powershell
# Da Server Core → Desktop Experience (aggiunge GUI)
Install-WindowsFeature Server-Gui-Mgmt-Infra, Server-Gui-Shell -Restart

# Da Desktop Experience → Server Core (rimuove GUI)
Uninstall-WindowsFeature Server-Gui-Mgmt-Infra, Server-Gui-Shell -Restart

# NOTA: in Server 2022+ la conversione non è ufficialmente supportata.
# Si consiglia una reinstallazione pulita.
```

### Nano Server — Stato attuale

**Attenzione**: a partire da Windows Server 2019, Nano Server è disponibile **solo come immagine container**. Non è più un'opzione di installazione standalone.

```powershell
# Nano Server si usa come base image per container
# Esempio Dockerfile:
# FROM mcr.microsoft.com/windows/nanoserver:ltsc2022
# COPY myapp.exe C:\app\
# ENTRYPOINT ["C:\\app\\myapp.exe"]

# Verificare immagini disponibili
docker pull mcr.microsoft.com/windows/nanoserver:ltsc2022
docker images | findstr nanoserver
```

### Quando usare ciascuna opzione

| Scenario | Scelta consigliata | Motivazione |
|----------|-------------------|-------------|
| DNS / DHCP / File Server | **Server Core** | Ruoli infrastrutturali, gestione remota sufficiente |
| Domain Controller | **Server Core** | Sicurezza massima per DC |
| IIS / Web Server | **Server Core** | Meno superficie di attacco |
| RDS Session Host | **Desktop Experience** | Necessario per sessioni desktop utente |
| Server di sviluppo/test | **Desktop Experience** | GUI utile per debug |
| Applicazioni legacy GUI-dipendenti | **Desktop Experience** | Requisito dell'applicazione |
| Microservizi containerizzati | **Nano Server** | Footprint minimo, avvio rapido |
| Hyper-V host | **Server Core** | Prestazioni migliori, meno overhead |

---

## Server Manager e Windows Admin Center

### Server Manager

Server Manager è lo strumento di gestione predefinito installato con Desktop Experience. Permette la gestione locale e remota di più server.

```powershell
# Aggiungere server remoti a Server Manager
# (via GUI: Dashboard → Add Servers → Active Directory/DNS/Import)

# Via PowerShell (gestire la lista di server registrati)
# Il file si trova in:
# %APPDATA%\Microsoft\Windows\ServerManager\ServerList.xml

# Installare ruoli/feature su server remoti tramite Server Manager:
# Manage → Add Roles and Features → selezione server di destinazione

# Monitoraggio da Server Manager:
# - Dashboard: stato di tutti i server gestiti
# - Alerts: eventi critici aggregati
# - Best Practices Analyzer (BPA): verifica configurazione
```

**Limitazioni di Server Manager**: non funziona cross-forest senza trust, la UI è pesante per infrastrutture grandi, non supporta nativamente Linux.

### Windows Admin Center (WAC)

WAC è il successore moderno di Server Manager. È un'applicazione web installata su un server gateway che gestisce server, cluster e PC Windows.

```powershell
# Installazione WAC (scaricabile da microsoft.com/windows-admin-center)
# Si installa come servizio su un server gateway (non sul server gestito)

# Requisiti:
# - Windows Server 2016+ o Windows 10/11 Pro/Enterprise
# - Porta 443 (HTTPS) o personalizzata
# - Browser moderno (Edge, Chrome, Firefox)

# Dopo installazione, accesso via browser:
# https://wac-server.corp.contoso.com:443

# Funzionalità principali:
# - Dashboard centralizzato per tutti i server
# - Gestione certificati, firewall, storage, network
# - Performance Monitor integrato
# - Event Viewer remoto
# - PowerShell remoto nel browser
# - Gestione Hyper-V, Failover Cluster, Azure Stack HCI
# - Integrazione con Azure (Azure Monitor, Azure Backup, Azure Site Recovery)
# - Gestione VM individuali
# - Storage Spaces Direct monitoring
# - Updates management

# Configurare accesso WAC via GPO per controllare chi può gestire cosa:
# Computer → Administrative Templates → Windows Admin Center
```

### Confronto Server Manager vs WAC

| Aspetto | Server Manager | Windows Admin Center |
|---------|---------------|---------------------|
| **Interfaccia** | GUI desktop (MMC-like) | Web browser |
| **Accesso remoto** | RSAT necessario su workstation | Qualsiasi browser |
| **Cluster management** | Basico | Avanzato (S2D, Azure Stack HCI) |
| **Linux support** | No | Sì (connessioni SSH) |
| **Azure integration** | No | Sì |
| **Mobile access** | No | Sì (browser mobile) |
| **Estensibilità** | Snap-in MMC | Estensioni WAC |
| **Raccomandazione MS** | Manutenzione legacy | Strumento raccomandato |

### RSAT — Remote Server Administration Tools

Per gestire server da una workstation Windows 10/11 senza WAC:

```powershell
# Windows 10/11: RSAT si installa come Features on Demand
Get-WindowsCapability -Online -Name RSAT* | Select-Object Name, State

# Installare RSAT specifici
Add-WindowsCapability -Online -Name Rsat.Dns.Tools~~~~0.0.1.0
Add-WindowsCapability -Online -Name Rsat.DHCP.Tools~~~~0.0.1.0
Add-WindowsCapability -Online -Name Rsat.ActiveDirectory.DS-LDS.Tools~~~~0.0.1.0
Add-WindowsCapability -Online -Name Rsat.FileServices.Tools~~~~0.0.1.0
Add-WindowsCapability -Online -Name Rsat.GroupPolicy.Management.Tools~~~~0.0.1.0
Add-WindowsCapability -Online -Name Rsat.ServerManager.Tools~~~~0.0.1.0

# Installare tutti gli RSAT
Get-WindowsCapability -Online -Name RSAT* |
    Where-Object State -eq "NotPresent" |
    Add-WindowsCapability -Online
```

### Windows Admin Center — Workflow Operativi e Novità v2511

Windows Admin Center (WAC) versione 2511 (maggio 2025) rappresenta un salto architetturale significativo: il backend migra a **.NET 8**, migliorando prestazioni e sicurezza. Le novità principali:

**OSConfig Security Baselines** — WAC integra nativamente le baseline di sicurezza tramite il motore OSConfig. Si possono applicare profili CIS o Microsoft Security Baseline direttamente dall'interfaccia web, senza configurare GPO manualmente.

**vMode — Gestione Hyper-V su Scala**

La modalità vMode consente di gestire fino a **1.000 host Hyper-V** e **25.000 macchine virtuali** da una singola istanza WAC. È progettata per ambienti Azure Stack HCI e datacenter con alta densità di virtualizzazione.

**Integrazione Secure Boot/TPM/VBS** — Dashboard dedicata per verificare lo stato di Secure Boot, TPM 2.0 e Virtualization-Based Security (VBS) su tutti i server gestiti. Essenziale per la compliance con le baseline di sicurezza di Server 2025.

#### Workflow: Deployment di un ruolo tramite WAC

```
Procedura operativa — installare un ruolo via WAC:

1. Accedere a https://wac-server:6516 dal browser
2. Aggiungere il server: "Add" → "Servers" → inserire FQDN
3. Selezionare il server → "Roles & Features"
4. Cercare il ruolo desiderato (es. "DNS Server")
5. Selezionare → "Install" → confermare
6. WAC mostra il progresso in tempo reale
7. Al termine: verificare lo stato nella sezione "Overview"

Per Server Core (senza GUI locale):
  → WAC è lo strumento raccomandato in sostituzione di MMC
  → Tutte le operazioni di configurazione ruolo disponibili via web
```

#### Workflow: Monitoraggio centralizzato con WAC

```powershell
# WAC espone dati che prima richiedevano RDP + Performance Monitor
# Dal browser:
#   Dashboard → CPU, Memoria, Disco, Rete in tempo reale
#   Events → filtro per livello (Critical, Error, Warning)
#   Processes → equivalente di Task Manager remoto
#   Registry → editor registro remoto
#   PowerShell → console PS remota integrata nel browser

# Automazione: WAC supporta estensioni PowerShell personalizzate
# Le estensioni si installano dal feed ufficiale:
#   WAC → Settings → Extensions → Available Extensions

# Configurare WAC per gestione multi-server in un cluster:
# WAC → Add → "Server clusters" → inserire nome cluster
# Dashboard unificato per tutti i nodi del cluster
```

#### WAC vs Azure Portal per Hybrid Management

| Scenario | WAC (on-premises) | Azure Portal (cloud) |
|---|---|---|
| Latenza di gestione | Millisecondi (rete locale) | Secondi (Internet) |
| Gestione offline | Sì | No |
| Integrazione Azure Policy | Tramite Azure Arc | Nativo |
| Costo | Gratuito | Azure Arc gratuito, servizi aggiuntivi a pagamento |
| Security baselines | OSConfig integrato | Azure Policy guest configuration |
| Ideale per | Operazioni quotidiane on-prem | Governance, compliance, automazione su scala |

---

## DNS Server

### Installazione e Configurazione

```powershell
# Installare
Install-WindowsFeature DNS -IncludeManagementTools

# Creare zona forward primaria (AD-integrated)
Add-DnsServerPrimaryZone -Name "corp.contoso.com" -ReplicationScope Domain

# Creare zona reverse
Add-DnsServerPrimaryZone -NetworkID "192.168.10.0/24" -ReplicationScope Domain

# Creare zona forward secondaria (da server esterno)
Add-DnsServerSecondaryZone -Name "partner.com" -MasterServers 10.10.10.10 `
    -ZoneFile "partner.com.dns"

# Conditional Forwarder
Add-DnsServerConditionalForwarderZone -Name "external.com" -MasterServers 8.8.8.8, 8.8.4.4

# Forwarder globali
Set-DnsServerForwarder -IPAddress 8.8.8.8, 1.1.1.1

# Stub Zone (mantiene solo NS e SOA, interroga i master per il resto)
Add-DnsServerStubZone -Name "subsidiary.com" -MasterServers 10.20.30.1 `
    -ReplicationScope Domain
```

### Tipi di zona DNS

| Tipo | Descrizione | Caso d'uso |
|------|-------------|------------|
| **Primary** | Copia scrivibile della zona | Server DNS autoritativo principale |
| **Secondary** | Copia read-only, aggiornata da zone transfer | Ridondanza DNS, siti remoti |
| **Stub** | Contiene solo NS, SOA e glue records | Risoluzione delegata senza copia completa |
| **Conditional Forwarder** | Inoltra query per un dominio specifico | Risolvere domini partner/esterni |
| **AD-Integrated** | Zona salvata in Active Directory (multi-master) | Ambiente AD, replica automatica |
| **Reverse Lookup** | Risolve IP → nome (record PTR) | Diagnostica, logging, mail server verification |

### Replication Scope per zone AD-integrated

```powershell
# Le zone AD-integrated possono replicare a diversi scope:
# - Domain:   tutti i DC nel dominio
# - Forest:   tutti i DC nella foresta
# - Legacy:   compatibilità Windows 2000
# - Custom:   partizione specifica

# Cambiare scope di replica
Set-DnsServerPrimaryZone -Name "corp.contoso.com" -ReplicationScope Forest

# Creare zona con scope personalizzato
Add-DnsServerDirectoryPartition -Name "CustomDNS"
Register-DnsServerDirectoryPartition -Name "CustomDNS" -ComputerName DC01
Add-DnsServerPrimaryZone -Name "custom.contoso.com" `
    -ReplicationScope Custom -DirectoryPartitionName "CustomDNS"
```

### Gestione Record

```powershell
# Record A
Add-DnsServerResourceRecordA -ZoneName "corp.contoso.com" -Name "webapp" -IPv4Address "192.168.10.30"

# Record AAAA (IPv6)
Add-DnsServerResourceRecordAAAA -ZoneName "corp.contoso.com" -Name "webapp" `
    -IPv6Address "2001:db8::30"

# Record CNAME
Add-DnsServerResourceRecordCName -ZoneName "corp.contoso.com" -Name "www" `
    -HostNameAlias "webapp.corp.contoso.com"

# Record MX
Add-DnsServerResourceRecordMX -ZoneName "corp.contoso.com" -Name "." `
    -MailExchange "mail.corp.contoso.com" -Preference 10

# Record MX secondario (failover)
Add-DnsServerResourceRecordMX -ZoneName "corp.contoso.com" -Name "." `
    -MailExchange "mail2.corp.contoso.com" -Preference 20

# Record PTR (reverse)
Add-DnsServerResourceRecordPtr -ZoneName "10.168.192.in-addr.arpa" `
    -Name "30" -PtrDomainName "webapp.corp.contoso.com"

# Record TXT (SPF)
Add-DnsServerResourceRecord -ZoneName "corp.contoso.com" -Name "." -Txt `
    -DescriptiveText "v=spf1 mx a ~all"

# Record SRV (per servizi come SIP, XMPP, etc.)
Add-DnsServerResourceRecord -ZoneName "corp.contoso.com" -Name "_sip._tcp" -Srv `
    -DomainName "sip.corp.contoso.com" -Priority 0 -Weight 5 -Port 5060

# Record NS (delega a sottodominio)
Add-DnsServerResourceRecord -ZoneName "corp.contoso.com" -Name "branch" -NS `
    -NameServer "dns-branch.corp.contoso.com"

# Elencare record
Get-DnsServerResourceRecord -ZoneName "corp.contoso.com" | Format-Table -AutoSize

# Elencare record di un tipo specifico
Get-DnsServerResourceRecord -ZoneName "corp.contoso.com" -RRType A

# Modificare TTL di un record
$old = Get-DnsServerResourceRecord -ZoneName "corp.contoso.com" -Name "webapp" -RRType A
$new = $old.Clone()
$new.TimeToLive = [System.TimeSpan]::FromHours(1)
Set-DnsServerResourceRecord -ZoneName "corp.contoso.com" -OldInputObject $old -NewInputObject $new

# Rimuovere record
Remove-DnsServerResourceRecord -ZoneName "corp.contoso.com" -Name "old-server" -RRType A -Force
```

### DNS Scavenging

Lo scavenging rimuove automaticamente i record DNS stale (non più aggiornati dai client). Essenziale in ambienti con DHCP per evitare record orfani.

```powershell
# Abilitare aging sulla zona
Set-DnsServerZoneAging -Name "corp.contoso.com" -Aging $true `
    -RefreshInterval 7.00:00:00 -NoRefreshInterval 7.00:00:00

# Parametri:
# - NoRefreshInterval: periodo in cui il record NON può essere aggiornato (default 7 giorni)
# - RefreshInterval: periodo dopo il quale il record DEVE essere aggiornato (default 7 giorni)
# - Totale: record stale dopo NoRefresh + Refresh = 14 giorni

# Abilitare scavenging sul server
Set-DnsServerScavenging -ScavengingState $true -ScavengingInterval 7.00:00:00

# Forzare scavenging manuale
Start-DnsServerScavenging

# Verificare stato aging sui record
Get-DnsServerResourceRecord -ZoneName "corp.contoso.com" -RRType A |
    Select-Object HostName, Timestamp, TimeToLive | Format-Table -AutoSize
# Timestamp = 0 → record statico (non soggetto a scavenging)
# Timestamp > 0 → record dinamico (soggetto a scavenging)
```

### DNSSEC

DNSSEC aggiunge firme crittografiche alle risposte DNS per prevenire DNS spoofing e cache poisoning.

```powershell
# Firmare una zona con DNSSEC
Invoke-DnsServerZoneSign -ZoneName "corp.contoso.com" -SignWithDefault -Force

# Verificare stato DNSSEC della zona
Get-DnsServerDnsSecZoneSetting -ZoneName "corp.contoso.com"

# Visualizzare le chiavi di firma
Get-DnsServerSigningKey -ZoneName "corp.contoso.com"

# Aggiungere chiave di firma personalizzata (KSK - Key Signing Key)
Add-DnsServerSigningKey -ZoneName "corp.contoso.com" `
    -Type KeySigningKey -CryptoAlgorithm RsaSha256 -KeyLength 2048

# Aggiungere chiave ZSK (Zone Signing Key)
Add-DnsServerSigningKey -ZoneName "corp.contoso.com" `
    -Type ZoneSigningKey -CryptoAlgorithm RsaSha256 -KeyLength 1024

# Configurare Trust Anchor (sul server che valida)
Add-DnsServerTrustAnchor -Name "corp.contoso.com" -CryptoAlgorithm RsaSha256 `
    -KeyTag 12345 -Digest "AABBCCDD..." -DigestType Sha256

# Rimuovere firma DNSSEC
Invoke-DnsServerZoneUnsign -ZoneName "corp.contoso.com" -Force

# Verificare risoluzione DNSSEC da client
Resolve-DnsName -Name "webapp.corp.contoso.com" -DnssecOk
```

### DNS Policies

Le DNS Policies (da Server 2016+) permettono risposte DNS diverse basate su criteri (geo-location, time of day, subnet del client, etc.).

```powershell
# Creare subnet per DNS policy
Add-DnsServerClientSubnet -Name "SubnetItalia" -IPv4Subnet "192.168.10.0/24"
Add-DnsServerClientSubnet -Name "SubnetGermania" -IPv4Subnet "10.20.0.0/16"

# Creare zone scope (set di record diversi per la stessa zona)
Add-DnsServerZoneScope -ZoneName "corp.contoso.com" -Name "ScopeItalia"
Add-DnsServerZoneScope -ZoneName "corp.contoso.com" -Name "ScopeGermania"

# Aggiungere record diversi per scope diversi
Add-DnsServerResourceRecord -ZoneName "corp.contoso.com" -A -Name "intranet" `
    -IPv4Address "192.168.10.50" -ZoneScope "ScopeItalia"
Add-DnsServerResourceRecord -ZoneName "corp.contoso.com" -A -Name "intranet" `
    -IPv4Address "10.20.1.50" -ZoneScope "ScopeGermania"

# Creare policy di risoluzione
Add-DnsServerQueryResolutionPolicy -Name "PolicyItalia" `
    -Action ALLOW -ClientSubnet "EQ,SubnetItalia" `
    -ZoneScope "ScopeItalia,1" -ZoneName "corp.contoso.com"

Add-DnsServerQueryResolutionPolicy -Name "PolicyGermania" `
    -Action ALLOW -ClientSubnet "EQ,SubnetGermania" `
    -ZoneScope "ScopeGermania,1" -ZoneName "corp.contoso.com"

# Elencare policy attive
Get-DnsServerQueryResolutionPolicy -ZoneName "corp.contoso.com"

# Rimuovere policy
Remove-DnsServerQueryResolutionPolicy -Name "PolicyItalia" -ZoneName "corp.contoso.com" -Force
```

### Monitoraggio e Diagnostica DNS

```powershell
# Verificare funzionamento DNS
Resolve-DnsName -Name "webapp.corp.contoso.com" -Server 192.168.10.10
nslookup webapp.corp.contoso.com 192.168.10.10

# Analisi DNS debug logging
Set-DnsServerDiagnostics -All $true   # Attenzione: genera molto traffico I/O
# Log salvato in: %SystemRoot%\System32\dns\dns.log

# Disabilitare debug logging
Set-DnsServerDiagnostics -All $false

# DNS Analytics (Event Log)
# Event Viewer → Applications and Services → Microsoft → Windows → DNS-Server → Analytical

# Verificare cache DNS del server
Show-DnsServerCache | Select-Object HostName, RecordType, RecordData

# Svuotare cache DNS del server
Clear-DnsServerCache -Force

# Test DNS con dcdiag
dcdiag /test:dns /v /e

# Verificare zone transfer
Get-DnsServerZoneTransferPolicy -ZoneName "corp.contoso.com"

# Statistiche server DNS
Get-DnsServerStatistics | Select-Object -ExpandProperty QueryStatistics
```

### DNS — Checklist di Hardening per Produzione

La sicurezza del DNS è critica: un DNS compromesso consente redirect di tutto il traffico di rete. Applicare sistematicamente questi controlli:

#### Configurazione Sicura delle Zone

```powershell
# 1. Limitare i zone transfer SOLO ai server secondari autorizzati
Set-DnsServerPrimaryZone -Name "corp.contoso.com" `
    -SecureSecondaries TransferToSecureServers `
    -SecondaryServers "192.168.10.11", "192.168.10.12"

# 2. Disabilitare la ricorsione su server DNS autoritativi
# (un DNS autoritativo non deve risolvere query per zone esterne)
Set-DnsServerRecursion -Enable $false

# ATTENZIONE: disabilitare la ricorsione su DC/DNS integrati AD
# solo se esiste un altro DNS resolver per i client.
# I DC devono poter risolvere nomi esterni per la replica AD.

# 3. Abilitare DNSSEC su zone critiche
Invoke-DnsServerSigningKeyRollover -ZoneName "corp.contoso.com" -Force
Get-DnsServerDnsSecZoneSetting -ZoneName "corp.contoso.com"

# 4. Rate limiting per mitigare amplification attacks
Set-DnsServerResponseRateLimiting -Mode Enable `
    -ResponsesPerSec 5 -ErrorsPerSec 5 -WindowInSec 5

# 5. Bloccare query per record ANY (usati in attacchi di amplificazione)
# Questa funzionalità è disponibile tramite DNS Policy in Server 2016+
Add-DnsServerQueryResolutionPolicy -Name "BlockANY" `
    -Action DENY -QType "EQ,ANY" -PassThru
```

#### Monitoraggio e Audit DNS

```powershell
# Abilitare DNS Analytical Log (dettagliato, attenzione al volume)
Set-DnsServerDiagnostics -EnableLoggingForLocalLookupEvent $true `
    -EnableLoggingForRemoteServerEvent $true `
    -EnableLoggingForPluginDllEvent $true

# DNS Debug Logging — alternativa più leggera
dnscmd /config /logLevel 0x8000F301
dnscmd /config /logFilePath "D:\DNS\dnslog.txt"
dnscmd /config /logFileMaxSize 50000000  # 50 MB

# Monitorare query sospette (alto volume da un singolo IP)
Get-DnsServerStatistics | Select-Object -ExpandProperty QueryStatistics

# Event IDs critici da monitorare:
# 770 — zone transfer negato (tentativo non autorizzato)
# 7062 — errore di risoluzione ricorsiva
# 4013 — il DNS non riesce a caricare zone integrate AD
```

#### Checklist DNS Hardening Rapida

```
□ Zone transfer limitati a server secondari specifici
□ Ricorsione disabilitata su DNS autoritativi (se possibile)
□ DNSSEC abilitato su zone interne critiche
□ Response Rate Limiting configurato
□ DNS debug/analytical logging attivo
□ Firewall: porta 53 TCP/UDP aperta SOLO verso client e DNS secondari
□ Aggiornamenti dinamici: solo "Secure only" su zone integrate AD
□ Cache poisoning mitigation: source port randomization (default in 2025)
□ Nessun forwarder configurato verso DNS pubblici non fidati
□ DoH abilitato dove supportato per proteggere query in transito
```

---

## DHCP Server

### Installazione e Configurazione

```powershell
# Installare
Install-WindowsFeature DHCP -IncludeManagementTools

# Autorizzare in AD (obbligatorio in ambiente domain)
Add-DhcpServerInDC -DnsName "dc01.corp.contoso.com" -IPAddress 192.168.10.10

# Verificare autorizzazione
Get-DhcpServerInDC

# Post-installazione: completare configurazione security groups
# (Viene creato il gruppo "DHCP Administrators" e "DHCP Users")
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\ServerManager\Roles\12" `
    -Name "ConfigurationState" -Value 2
```

### Scope e Opzioni

```powershell
# Creare scope IPv4
Add-DhcpServerv4Scope -Name "LAN-Principale" `
    -StartRange 192.168.10.100 -EndRange 192.168.10.250 `
    -SubnetMask 255.255.255.0 -LeaseDuration 8.00:00:00 -State Active

# Opzioni scope (gateway, DNS, dominio)
Set-DhcpServerv4OptionValue -ScopeId 192.168.10.0 `
    -Router 192.168.10.1 `
    -DnsServer 192.168.10.10, 192.168.10.11 `
    -DnsDomain "corp.contoso.com"

# Opzioni specifiche aggiuntive
# Opzione 66: TFTP Server (per PXE boot)
Set-DhcpServerv4OptionValue -ScopeId 192.168.10.0 -OptionId 66 -Value "192.168.10.5"

# Opzione 67: Boot file name (per PXE)
Set-DhcpServerv4OptionValue -ScopeId 192.168.10.0 -OptionId 67 -Value "boot\x64\wdsnbp.com"

# Opzione 42: NTP Server
Set-DhcpServerv4OptionValue -ScopeId 192.168.10.0 -OptionId 42 -Value "192.168.10.10"

# Opzioni a livello server (si applicano a tutti gli scope)
Set-DhcpServerv4OptionValue -DnsDomain "corp.contoso.com" `
    -DnsServer 192.168.10.10, 192.168.10.11

# Elencare opzioni configurate
Get-DhcpServerv4OptionValue -ScopeId 192.168.10.0

# Esclusioni (range di IP non assegnati)
Add-DhcpServerv4ExclusionRange -ScopeId 192.168.10.0 `
    -StartRange 192.168.10.1 -EndRange 192.168.10.20

# Superscope (aggregare scope multipli)
Add-DhcpServerv4Superscope -SuperscopeName "Edificio-A" `
    -ScopeId 192.168.10.0, 192.168.11.0
```

### Reservation (IP fisso per MAC)

```powershell
# Creare reservation
Add-DhcpServerv4Reservation -ScopeId 192.168.10.0 `
    -IPAddress 192.168.10.50 -ClientId "AA-BB-CC-DD-EE-FF" `
    -Name "Stampante-Piano1" -Description "Stampante HP LaserJet"

# Elencare reservation
Get-DhcpServerv4Reservation -ScopeId 192.168.10.0

# Rimuovere reservation
Remove-DhcpServerv4Reservation -ScopeId 192.168.10.0 -ClientId "AA-BB-CC-DD-EE-FF"

# Convertire lease attivo in reservation
Get-DhcpServerv4Lease -ScopeId 192.168.10.0 |
    Where-Object HostName -like "*stampante*" |
    Add-DhcpServerv4Reservation
```

### MAC Filtering (Allow/Deny List)

```powershell
# Abilitare MAC filtering (Allow list, Deny list, o entrambi)
Set-DhcpServerv4FilterList -Allow $true -Deny $true

# Aggiungere MAC alla deny list (blocca dispositivi specifici)
Add-DhcpServerv4Filter -List Deny -MacAddress "AA-BB-CC-DD-EE-01" `
    -Description "Dispositivo non autorizzato"

# Aggiungere MAC alla allow list (solo questi ricevono IP)
Add-DhcpServerv4Filter -List Allow -MacAddress "AA-BB-CC-DD-EE-02" `
    -Description "Server autorizzato"

# Elencare filtri
Get-DhcpServerv4Filter -List Allow
Get-DhcpServerv4Filter -List Deny

# Rimuovere filtro
Remove-DhcpServerv4Filter -MacAddress "AA-BB-CC-DD-EE-01"

# NOTA: se Allow è attivo e Deny è attivo, il flusso è:
# 1. Se MAC è nella Deny → rifiutato
# 2. Se MAC è nella Allow → accettato
# 3. Se MAC non è in nessuna lista → rifiutato (se Allow attivo)
```

### DHCP Failover

```powershell
# Failover DHCP — due modalità:
# Hot Standby: un server attivo, l'altro in standby (siti piccoli)
# Load Balance: entrambi servono richieste (siti grandi)

# Hot Standby
Add-DhcpServerv4Failover -ComputerName DC01 -PartnerServer DC02 `
    -Name "DHCP-Failover-HS" -ScopeId 192.168.10.0 `
    -SharedSecret "S3cur3P@ss!" -Mode HotStandby `
    -ReservePercent 10 -AutoStateTransition $true `
    -StateSwitchInterval (New-TimeSpan -Minutes 60)

# Load Balance
Add-DhcpServerv4Failover -ComputerName DC01 -PartnerServer DC02 `
    -Name "DHCP-Failover-LB" -ScopeId 192.168.11.0 `
    -SharedSecret "S3cur3P@ss!" -Mode LoadBalance `
    -LoadBalancePercent 50 -AutoStateTransition $true `
    -MaxClientLeadTime (New-TimeSpan -Hours 1)

# Verificare stato failover
Get-DhcpServerv4Failover -ComputerName DC01

# Forzare replica failover
Invoke-DhcpServerv4FailoverReplication -ComputerName DC01 -Name "DHCP-Failover-HS"

# Rimuovere failover
Remove-DhcpServerv4Failover -Name "DHCP-Failover-HS" -Force
```

### DHCP Relay Agent

Quando i client DHCP si trovano su una subnet diversa dal server DHCP, serve un relay agent (DHCP Relay / IP Helper). Il relay agent inoltra le richieste broadcast DHCP al server tramite unicast.

```powershell
# Configurazione DHCP Relay su router Cisco (esempio):
# interface GigabitEthernet0/1
#   ip helper-address 192.168.10.10
#   ip helper-address 192.168.10.11

# Su Windows Server (Routing and Remote Access):
Install-WindowsFeature Routing -IncludeManagementTools

# Configurare relay agent via RRAS:
# 1. Aprire RRAS console
# 2. IPv4 → DHCP Relay Agent → Properties
# 3. Aggiungere IP del server DHCP
# 4. Aggiungere interfaccia di rete della subnet remota

# Verifica: il client su subnet remota deve ricevere IP dallo scope corretto
# Lo scope deve coprire la subnet del client, non quella del server
# Esempio: client su 10.20.30.0/24 → serve scope 10.20.30.0/24 sul server DHCP
```

### Monitoraggio e Statistiche DHCP

```powershell
# Statistiche scope
Get-DhcpServerv4ScopeStatistics -ScopeId 192.168.10.0

# Lease attivi
Get-DhcpServerv4Lease -ScopeId 192.168.10.0 |
    Select-Object IPAddress, HostName, ClientID, LeaseExpiryTime |
    Format-Table -AutoSize

# Lease specifico per hostname
Get-DhcpServerv4Lease -ScopeId 192.168.10.0 |
    Where-Object HostName -like "*WKS*"

# Statistiche server complessive
Get-DhcpServerv4Statistics

# Log DHCP: %SystemRoot%\System32\dhcp\
# - DhcpSrvLog-<giorno>.log (audit log)

# Verificare conflitti IP
Get-DhcpServerv4Lease -ScopeId 192.168.10.0 |
    Where-Object AddressState -eq "DeclinedByClient"

# Scope IPv6
Add-DhcpServerv6Scope -Prefix 2001:db8:1:: -Name "IPv6-LAN" `
    -State Active
```

### DHCP — Novità Server 2025 e Hardening

#### Miglioramenti in Windows Server 2025

Windows Server 2025 introduce affinamenti per il ruolo DHCP orientati all'affidabilità:

- **Site-aware DHCP affinity** — in ambienti multi-sito con AD Sites and Services configurato, il server DHCP predilige l'assegnazione di lease dalla scope associata al sito AD del client richiedente. Riduce la dipendenza da DHCP relay agent per il site-matching.
- **Failover migliorato** — la sincronizzazione tra partner failover è più resiliente a interruzioni di rete transitorie. Il timer *Maximum Client Lead Time (MCLT)* è configurabile con granularità maggiore.
- **Integrazione con Windows Admin Center** — WAC 2511 espone dashboard DHCP con statistiche di scope utilization, lease attivi e conflitti IP in tempo reale.

```powershell
# Configurare DHCP failover (hot-standby)
Add-DhcpServerv4Failover -Name "DHCP-Failover" `
    -PartnerServer "DHCP02.corp.contoso.com" `
    -ScopeId 192.168.10.0 `
    -SharedSecret "P@ssw0rd-Failover!" `
    -Mode HotStandby `
    -ReservePercent 10 `
    -MaxClientLeadTime (New-TimeSpan -Hours 1)

# Verificare stato failover
Get-DhcpServerv4Failover | Select-Object Name, Mode, State, PartnerServer

# Forzare sincronizzazione (dopo ripristino da failure)
Invoke-DhcpServerv4FailoverReplication -Name "DHCP-Failover" -Force
```

#### Checklist di Hardening DHCP

La sicurezza del DHCP è spesso sottovalutata. Un server DHCP compromesso può reindirizzare tutto il traffico di una rete (via gateway e DNS malevoli).

```
Regole fondamentali di sicurezza DHCP:

□ Mai installare il ruolo DHCP su un Domain Controller
    → Un DC compromesso tramite DHCP = compromissione dell'intero dominio

□ Autorizzazione in Active Directory obbligatoria
    → Solo i server DHCP autorizzati in AD possono servire lease
    → Verificare: Get-DhcpServerInDC

□ Rogue Server Detection attiva
    → Monitorare Event ID 1056, 1059 (DHCP rogue detection)
    → In ambienti enterprise: usare 802.1X per filtrare DHCP non autorizzati

□ MAC address filtering per scope critiche
    → Usare allow/deny list per limitare i client autorizzati

□ DHCP audit logging abilitato
    → Default path: %SystemRoot%\System32\dhcp\
    → Verificare: Get-DhcpServerAuditLog

□ Firewall: porte 67-68 UDP aperte SOLO sulla VLAN corretta
    → Segmentare il traffico DHCP per VLAN

□ Lease duration appropriata:
    → Reti cablate stabili: 8-24 ore
    → Wi-Fi guest: 1-4 ore
    → Reti ad alta mobilità: 30-60 minuti

□ Configurare DHCP failover (non affidarsi a un singolo server)
    → Modalità: Hot-standby (primary/secondary) o Load-balance (50/50)

□ Non distribuire opzioni DHCP pericolose senza necessità:
    → Opzione 252 (WPAD) → disabilitare se non si usa proxy autodiscovery
    → Opzione 150 (TFTP) → solo per VoIP, limitare alla VLAN corretta
```

```powershell
# Verificare server DHCP autorizzati in AD
Get-DhcpServerInDC

# Rimuovere server DHCP non autorizzato
Remove-DhcpServerInDC -DnsName "rogue-server.corp.contoso.com" `
    -IPAddress 192.168.10.99

# Abilitare e verificare audit logging
Set-DhcpServerAuditLog -Enable $true -Path "D:\DHCP\AuditLog" -MaxMBFileSize 100
Get-DhcpServerAuditLog

# Monitorare utilizzo scope (alert se > 85%)
Get-DhcpServerv4ScopeStatistics | ForEach-Object {
    $pctUsed = ($_.InUse / ($_.InUse + $_.Free)) * 100
    if ($pctUsed -gt 85) {
        Write-Warning "Scope $($_.ScopeId): $([math]::Round($pctUsed,1))% utilizzato!"
    }
}
```

---

## File Server e DFS

### File Server — Installazione e condivisioni

```powershell
# Installare ruolo
Install-WindowsFeature FS-FileServer, FS-Resource-Manager -IncludeManagementTools

# Creare condivisione SMB
New-SmbShare -Name "Shared" -Path "D:\Shares\Shared" `
    -FullAccess "Domain Admins" -ChangeAccess "Authenticated Users" `
    -Description "Condivisione principale"

# Creare condivisione con accesso read-only
New-SmbShare -Name "Docs" -Path "D:\Shares\Docs" `
    -FullAccess "Domain Admins" -ReadAccess "Domain Users"

# Enumerazione Access-Based (ABE) — utenti vedono solo ciò a cui hanno accesso
Set-SmbShare -Name "Shared" -FolderEnumerationMode AccessBased

# Elencare condivisioni
Get-SmbShare | Select-Object Name, Path, Description

# Rimuovere condivisione
Remove-SmbShare -Name "OldShare" -Force

# Configurare SMB Signing (sicurezza)
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force

# Disabilitare SMBv1 (CRITICO per sicurezza — WannaCry, EternalBlue)
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol

# Configurare SMB Encryption (SMB 3.0+)
Set-SmbServerConfiguration -EncryptData $true -Force
# Oppure per singola condivisione:
Set-SmbShare -Name "Confidential" -EncryptData $true
```

### Permessi NTFS

I permessi NTFS controllano l'accesso a file e cartelle a livello di filesystem, indipendentemente da come si accede (localmente o via rete).

```powershell
# Permessi NTFS base
# - Full Control: tutto
# - Modify: leggere, scrivere, eliminare file/sottocartelle
# - Read & Execute: leggere ed eseguire
# - List Folder Contents: elencare contenuto cartelle
# - Read: solo lettura
# - Write: creare file e scrivere dati

# Impostare permesso NTFS
$acl = Get-Acl "D:\Shares\Shared"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CORP\GG-IT-Staff", "Modify", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.AddAccessRule($rule)
Set-Acl "D:\Shares\Shared" $acl

# Rimuovere un permesso
$acl = Get-Acl "D:\Shares\Shared"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CORP\GG-OldGroup", "Modify", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.RemoveAccessRule($rule)
Set-Acl "D:\Shares\Shared" $acl

# Visualizzare permessi correnti
Get-Acl "D:\Shares\Shared" | Format-List

# Visualizzare ACL in formato leggibile
(Get-Acl "D:\Shares\Shared").Access |
    Select-Object IdentityReference, FileSystemRights, AccessControlType, IsInherited |
    Format-Table -AutoSize

# Disabilitare ereditarietà (e copiare permessi esistenti)
$acl = Get-Acl "D:\Shares\Confidential"
$acl.SetAccessRuleProtection($true, $true)  # (proteggi, copia permessi ereditati)
Set-Acl "D:\Shares\Confidential" $acl

# Disabilitare ereditarietà (e rimuovere permessi ereditati)
$acl = Get-Acl "D:\Shares\Confidential"
$acl.SetAccessRuleProtection($true, $false)  # (proteggi, NON copiare)
Set-Acl "D:\Shares\Confidential" $acl

# Ripristinare ereditarietà
$acl = Get-Acl "D:\Shares\Confidential"
$acl.SetAccessRuleProtection($false, $false)
Set-Acl "D:\Shares\Confidential" $acl
```

### Ereditarietà e Flag di propagazione

```powershell
# Flag di ereditarietà (InheritanceFlags):
# ContainerInherit → si applica alle sottocartelle
# ObjectInherit    → si applica ai file
# None             → solo a questo oggetto

# Flag di propagazione (PropagationFlags):
# None            → si applica a questo oggetto E discendenti
# InheritOnly     → NON si applica a questo oggetto, solo ai discendenti
# NoPropagateInherit → si applica solo al primo livello

# Esempio: permesso solo su sottocartelle dirette (non ricorsivo)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CORP\GG-Managers", "Read",
    "ContainerInherit", "NoPropagateInherit", "Allow")

# Esempio: permesso solo sui file dentro la cartella (non la cartella stessa)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CORP\GG-Users", "Modify",
    "ObjectInherit", "InheritOnly", "Allow")
```

### Permessi Share vs NTFS

```
Regola fondamentale:
  Permesso EFFETTIVO = il PIÙ RESTRITTIVO tra Share e NTFS

  Share: ChangeAccess (equivale a Modify)
  NTFS:  Full Control
  → Effettivo: Modify (lo Share è più restrittivo)

  Share: FullAccess
  NTFS:  Read
  → Effettivo: Read (NTFS è più restrittivo)

Best practice:
  - Impostare permessi Share ampi (Everyone: Full Control o Change)
  - Controllare accesso granulare con NTFS
  - Questo semplifica la gestione (un solo punto di controllo)
```

### Effective Access — Verificare permessi effettivi

```powershell
# Verificare permessi effettivi di un utente su un path
# (Richiede modulo NTFSSecurity o calcolo manuale)

# Metodo nativo: icacls
icacls "D:\Shares\Shared" /T  # Elencare permessi ricorsivamente

# Verificare ownership
$acl = Get-Acl "D:\Shares\Shared"
$acl.Owner

# Cambiare owner
$acl = Get-Acl "D:\Shares\Shared"
$acl.SetOwner([System.Security.Principal.NTAccount]"CORP\admin")
Set-Acl "D:\Shares\Shared" $acl

# Reset permessi ricorsivo (utile per cleanup)
icacls "D:\Shares\Shared" /reset /T /C /Q
```

### FSRM — File Server Resource Manager

FSRM permette gestione quote disco, screening file e reportistica.

```powershell
# Installare FSRM
Install-WindowsFeature FS-Resource-Manager -IncludeManagementTools

# --- QUOTE ---

# Creare quota template
New-FsrmQuotaTemplate -Name "1GB-Soft" -Size 1GB -SoftLimit `
    -Threshold (New-FsrmQuotaThreshold -Percentage 85 `
        -Action (New-FsrmAction -Type Email -MailTo "[Admin Email]" `
            -Subject "Quota al 85%" -Body "L'utente ha raggiunto l'85% della quota"))

# Applicare quota a cartella utenti (auto-apply a ogni sottocartella)
New-FsrmAutoQuota -Path "D:\Shares\Users" -Template "1GB-Soft"

# Creare quota hard (blocca scrittura al raggiungimento)
New-FsrmQuota -Path "D:\Shares\Projects" -Size 5GB

# Creare quota soft (solo avviso, non blocca)
New-FsrmQuota -Path "D:\Shares\Temp" -Size 2GB -SoftLimit

# Elencare quote
Get-FsrmQuota | Select-Object Path, Size, Usage, Template

# Rimuovere quota
Remove-FsrmQuota -Path "D:\Shares\Temp" -Confirm:$false

# --- FILE SCREENING ---

# Creare file screen (bloccare tipi file)
New-FsrmFileScreen -Path "D:\Shares\Shared" -Template "Block Executable Files"

# Creare file screen personalizzato
$fileGroup = New-FsrmFileGroup -Name "Blocca-Crypto" `
    -IncludePattern @("*.encrypted", "*.locky", "*.crypto", "*.crypt",
        "*.cerber", "*.zepto", "DECRYPT_*.*", "HELP_DECRYPT*.*")

New-FsrmFileScreen -Path "D:\Shares\Shared" `
    -IncludeGroup "Blocca-Crypto" -Active

# File screen passivo (solo log, non blocca)
New-FsrmFileScreen -Path "D:\Shares\Media" `
    -IncludeGroup "Video and Animation Files" -Active:$false

# Elencare file screen
Get-FsrmFileScreen | Select-Object Path, Active, Template

# --- REPORT ---

# Generare report su utilizzo
New-FsrmStorageReport -Name "Report-Mensile" `
    -ReportType DuplicateFiles, LargeFiles, FilesByOwner `
    -Namespace "D:\Shares" -Interactive

# Report schedulato
New-FsrmScheduledTask -Time "02:00" -Weekly Monday
```

### DFS — Distributed File System

DFS unifica condivisioni di rete distribuite su più server sotto un unico namespace logico.

```powershell
# Installare DFS
Install-WindowsFeature FS-DFS-Namespace, FS-DFS-Replication -IncludeManagementTools

# --- DFS NAMESPACES ---

# Tipi di namespace:
# Domain-based (v2): \\domain\namespace — supporta referral, failover, AD-integrated
# Standalone: \\server\namespace — singolo server, no failover

# Creare DFS Namespace (domain-based)
New-DfsnRoot -TargetPath "\\SRV01\DFSRoot" -Type DomainV2 -Path "\\corp.contoso.com\files"

# Aggiungere server namespace (ridondanza)
New-DfsnRootTarget -Path "\\corp.contoso.com\files" -TargetPath "\\SRV02\DFSRoot"

# Aggiungere folder DFS (mount point logico)
New-DfsnFolder -Path "\\corp.contoso.com\files\Shared" -TargetPath "\\SRV01\Shared"

# Aggiungere target aggiuntivo (stessa cartella su server diverso)
New-DfsnFolderTarget -Path "\\corp.contoso.com\files\Shared" -TargetPath "\\SRV02\Shared"

# Configurare priorità referral
Set-DfsnFolderTarget -Path "\\corp.contoso.com\files\Shared" `
    -TargetPath "\\SRV01\Shared" -ReferralPriorityClass SiteCostNormal

# Elencare namespace
Get-DfsnRoot | Select-Object Path, Type, State
Get-DfsnFolder -Path "\\corp.contoso.com\files\*"

# Rimuovere folder target
Remove-DfsnFolderTarget -Path "\\corp.contoso.com\files\Old" -TargetPath "\\SRV01\Old"
```

### DFS-R — DFS Replication

DFS-R replica automaticamente il contenuto tra server, usando compressione differenziale (RDC — Remote Differential Compression).

```powershell
# Creare gruppo di replica DFS-R
New-DfsReplicationGroup -GroupName "SharedRepl"
Add-DfsrMember -GroupName "SharedRepl" -ComputerName "SRV01", "SRV02"
Add-DfsReplicatedFolder -GroupName "SharedRepl" -FolderName "Shared"

# Configurare connessione bidirezionale
Add-DfsrConnection -GroupName "SharedRepl" -SourceComputerName "SRV01" `
    -DestinationComputerName "SRV02"

# Impostare membro primario e path contenuto
Set-DfsrMembership -GroupName "SharedRepl" -FolderName "Shared" `
    -ComputerName "SRV01" -ContentPath "D:\Shares\Shared" -PrimaryMember $true
Set-DfsrMembership -GroupName "SharedRepl" -FolderName "Shared" `
    -ComputerName "SRV02" -ContentPath "D:\Shares\Shared" -PrimaryMember $false

# Configurare scheduling (es. replica solo di notte)
Set-DfsrConnectionSchedule -GroupName "SharedRepl" `
    -SourceComputerName "SRV01" -DestinationComputerName "SRV02" `
    -Day Monday,Tuesday,Wednesday,Thursday,Friday `
    -BandwidthDetail Full

# Configurare staging quota (area di pre-staging per file grandi)
Set-DfsrMembership -GroupName "SharedRepl" -FolderName "Shared" `
    -ComputerName "SRV01" -StagingPathQuotaInMB 16384

# Diagnostica DFS-R
Get-DfsrState -ComputerName SRV01, SRV02
Get-DfsReplicationGroup | Get-DfsReplicatedFolder | Get-DfsrMembership
dfsrdiag pollad  # Forza polling immediato della configurazione

# Report di salute DFS-R
Write-DfsrHealthReport -GroupName "SharedRepl" -ReferenceComputerName SRV01 `
    -Path "D:\Reports"

# Backlog DFS-R (file in attesa di replica)
Get-DfsrBacklog -GroupName "SharedRepl" -FolderName "Shared" `
    -SourceComputerName SRV01 -DestinationComputerName SRV02 -Verbose

# ATTENZIONE: cartella ConflictAndDeleted
# File in conflitto vanno nella cartella ConflictAndDeletedManifest
# Monitorare dimensione e contenuto regolarmente
Get-DfsrMembership -GroupName "SharedRepl" |
    Select-Object ComputerName, ContentPath, ConflictAndDeletedPath
```

---

## Print Server

### Installazione e Configurazione

```powershell
# Installare ruolo Print Server
Install-WindowsFeature Print-Server -IncludeManagementTools

# Installare anche Internet Printing (opzionale — stampa via browser)
Install-WindowsFeature Print-Internet -IncludeManagementTools

# Installare LPD Service (per client Unix/Linux)
Install-WindowsFeature Print-LPD-Service
```

### Gestione Driver

```powershell
# Elencare driver disponibili nel driver store
Get-PrinterDriver | Select-Object Name, PrinterEnvironment

# Aggiungere driver dal driver store di Windows
Add-PrinterDriver -Name "HP Universal Printing PCL 6"

# Aggiungere driver da INF file
# (Scaricare dal produttore, estrarre, poi specificare il path)
pnputil.exe -a "C:\Drivers\HP\hpdriver.inf"
Add-PrinterDriver -Name "HP LaserJet Pro M404 PCL-6 (V4)" `
    -InfPath "C:\Drivers\HP\hpdriver.inf"

# Rimuovere driver
Remove-PrinterDriver -Name "HP Universal Printing PCL 6"

# V3 vs V4 driver:
# V3: legacy, kernel-mode (meno sicuro, più compatibile)
# V4: user-mode, più sicuro, supporta Package-Aware
# Best practice: usare V4 quando disponibile

# Elencare driver V4
Get-PrinterDriver | Where-Object MajorVersion -eq 4
```

### Porte e Stampanti

```powershell
# Creare porta TCP/IP
Add-PrinterPort -Name "IP_192.168.10.200" -PrinterHostAddress "192.168.10.200"

# Creare porta con protocollo specifico
Add-PrinterPort -Name "IP_192.168.10.201" -PrinterHostAddress "192.168.10.201" `
    -PortNumber 9100 -SNMP -SNMPCommunity "public"

# Aggiungere stampante condivisa
Add-Printer -Name "HP-Piano1" -DriverName "HP Universal Printing PCL 6" `
    -PortName "IP_192.168.10.200" -Shared -ShareName "HP-Piano1" -Published `
    -Comment "Stampante laser B/N, Piano 1, Stanza 101" `
    -Location "Edificio A, Piano 1, Stanza 101"

# Pubblicare stampante in Active Directory (se non fatto con -Published)
Set-Printer -Name "HP-Piano1" -Published $true

# Elencare stampanti
Get-Printer | Select-Object Name, DriverName, PortName, Shared, Published

# Configurare stampante predefinita per sessione
Set-Printer -Name "HP-Piano1" -Priority 1

# Rimuovere stampante
Remove-Printer -Name "HP-Piano1"

# Rimuovere porta
Remove-PrinterPort -Name "IP_192.168.10.200"
```

### Gestione Coda di Stampa

```powershell
# Elencare job in coda
Get-PrintJob -PrinterName "HP-Piano1"

# Rimuovere un job specifico
Remove-PrintJob -PrinterName "HP-Piano1" -ID 3

# Rimuovere tutti i job
Get-PrintJob -PrinterName "HP-Piano1" | Remove-PrintJob

# Sospendere/riprendere stampante
Suspend-PrintJob -PrinterName "HP-Piano1" -ID 5
Resume-PrintJob -PrinterName "HP-Piano1" -ID 5

# Riavviare job fallito
Restart-PrintJob -PrinterName "HP-Piano1" -ID 5

# Monitorare stato stampante
Get-Printer -Name "HP-Piano1" | Select-Object Name, PrinterStatus, JobCount

# Spooler service
Restart-Service Spooler
Get-Service Spooler | Select-Object Status
```

### Deploy Stampanti via Group Policy

```powershell
# Metodo 1: GPO Deployed Printers
# Computer Configuration → Policies → Windows Settings → Deployed Printers
# → Aggiungere connessione stampante: \\PrintServer\HP-Piano1

# Metodo 2: GPO Preferences
# User Configuration → Preferences → Control Panel Settings → Printers
# → New → Shared Printer → \\PrintServer\HP-Piano1
# → Tab Common → Item-level targeting (per OU, gruppo, sito)

# Metodo 3: Script di logon
# Add-Printer -ConnectionName "\\PrintServer\HP-Piano1"

# Metodo 4: PowerShell via GPO startup script
# Creare script .ps1:
#   Add-Printer -ConnectionName "\\PRINT-SRV\HP-Piano1"
#   Set-Printer -Name "\\PRINT-SRV\HP-Piano1" -Default
# Assegnare a: User Configuration → Policies → Windows Settings → Scripts → Logon

# Print Management Console (printmanagement.msc):
# Strumento GUI per gestione centralizzata di tutte le stampanti
# - Visualizzare tutte le stampanti su più server
# - Esportare/importare stampanti (migrazione server)
# - Impostare notifiche (coda piena, errori)

# Migrazione stampanti tra server
# Export
cscript.exe C:\Windows\System32\Printing_Admin_Scripts\en-US\prncnfg.vbs -g -s \\OLD-PRINT
# Oppure: Print Management → Export printers to a file

# Import
# Print Management → Import printers from a file
```

### Sicurezza Print Server

```powershell
# Limitare chi può aggiungere stampanti (GPO):
# Computer → Policies → Admin Templates → Printers
# - "Prevent users from installing printer drivers" → Enabled
# - "Point and Print Restrictions" → configurare server attendibili

# PrintNightmare (CVE-2021-34527) mitigazione:
# Disabilitare spooler su server dove non serve
Stop-Service Spooler
Set-Service Spooler -StartupType Disabled

# Oppure: limitare accesso via GPO
# "Allow Print Spooler to accept client connections" → Disabled

# Verificare stato del servizio Spooler su tutti i server
Invoke-Command -ComputerName (Get-ADComputer -Filter { OperatingSystem -like "*Server*" } |
    Select-Object -ExpandProperty Name) -ScriptBlock {
    Get-Service Spooler | Select-Object @{N='Server';E={$env:COMPUTERNAME}}, Status, StartType
}
```

---

## IIS Web Server

### Installazione e Configurazione

```powershell
# Installare IIS con moduli comuni
Install-WindowsFeature Web-Server, Web-Mgmt-Console, Web-Asp-Net45, `
    Web-Default-Doc, Web-Dir-Browsing, Web-Http-Errors, Web-Static-Content, `
    Web-Http-Logging, Web-Request-Monitor, Web-Stat-Compression, `
    Web-Filtering, Web-Windows-Auth, Web-Net-Ext45, Web-ISAPI-Ext, Web-ISAPI-Filter

# Moduli aggiuntivi utili
Install-WindowsFeature Web-Dyn-Compression   # Compressione dinamica
Install-WindowsFeature Web-Http-Redirect      # Redirect HTTP
Install-WindowsFeature Web-WebSockets         # WebSocket support
Install-WindowsFeature Web-Cert-Auth          # Autenticazione certificato
Install-WindowsFeature Web-IP-Security        # IP restrictions

Import-Module WebAdministration
Import-Module IISAdministration  # Modulo più recente (Server 2016+)
```

### Siti Web

```powershell
# Creare sito web
New-Website -Name "MyWebApp" -PhysicalPath "C:\inetpub\MyWebApp" `
    -BindingInformation "*:80:webapp.contoso.com"

# Creare sito con binding multipli
New-Website -Name "PortaleAziendale" -PhysicalPath "C:\inetpub\Portale" `
    -BindingInformation "*:80:portale.contoso.com"

# Aggiungere binding aggiuntivi
New-WebBinding -Name "PortaleAziendale" -Protocol http -Port 80 `
    -HostHeader "www.portale.contoso.com"

# Aggiungere binding HTTPS
New-WebBinding -Name "MyWebApp" -Protocol https -Port 443 `
    -HostHeader "webapp.contoso.com" -SslFlags 1

# SslFlags:
# 0 = No SNI, no certificato richiesto
# 1 = SNI (Server Name Indication) — permette più certificati sulla stessa IP:porta
# 2 = No SNI, Central Certificate Store
# 3 = SNI + Central Certificate Store

# Assegnare certificato SSL
$cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object Subject -like "*webapp*"
$binding = Get-WebBinding -Name "MyWebApp" -Protocol https
$binding.AddSslCertificate($cert.Thumbprint, "My")

# Redirect HTTP → HTTPS (nel web.config del sito)
# Richiede URL Rewrite Module installato

# Gestione siti
Get-Website | Select-Object Name, State, PhysicalPath
Get-WebBinding | Select-Object Protocol, bindingInformation
Start-Website -Name "MyWebApp"
Stop-Website -Name "MyWebApp"
Remove-Website -Name "OldSite"
```

### Application Pool

```powershell
# Creare Application Pool
New-WebAppPool -Name "MyWebApp-Pool"

# Configurare identity (account con cui gira il pool)
# Tipi: ApplicationPoolIdentity (default), LocalSystem, LocalService, NetworkService, SpecificUser
Set-ItemProperty "IIS:\AppPools\MyWebApp-Pool" -Name processModel.identityType -Value SpecificUser
Set-ItemProperty "IIS:\AppPools\MyWebApp-Pool" -Name processModel.userName -Value "corp\svc-webapp"
Set-ItemProperty "IIS:\AppPools\MyWebApp-Pool" -Name processModel.password -Value "P@ssw0rd!"

# Assegnare pool al sito
Set-ItemProperty "IIS:\Sites\MyWebApp" -Name applicationPool -Value "MyWebApp-Pool"

# Configurare runtime .NET
Set-ItemProperty "IIS:\AppPools\MyWebApp-Pool" -Name managedRuntimeVersion -Value "v4.0"
# Per .NET Core / ASP.NET Core: -Value ""  (nessun runtime managed)

# Configurare pipeline mode
Set-ItemProperty "IIS:\AppPools\MyWebApp-Pool" -Name managedPipelineMode -Value "Integrated"
# Classic = compatibilità legacy; Integrated = raccomandato

# Recycling (riavvio periodico per evitare memory leak)
Set-ItemProperty "IIS:\AppPools\MyWebApp-Pool" -Name recycling.periodicRestart.time -Value "00:00:00"
Set-ItemProperty "IIS:\AppPools\MyWebApp-Pool" -Name recycling.periodicRestart.schedule `
    -Value @{value="03:00:00"}  # Riavvio alle 3 di notte

# Configurare limiti
Set-ItemProperty "IIS:\AppPools\MyWebApp-Pool" -Name recycling.periodicRestart.memory -Value 1048576
# Memory limit in KB (1 GB)

# Rapid-Fail Protection
Set-ItemProperty "IIS:\AppPools\MyWebApp-Pool" -Name failure.rapidFailProtection -Value $true
Set-ItemProperty "IIS:\AppPools\MyWebApp-Pool" -Name failure.rapidFailProtectionMaxCrashes -Value 5

# Gestione pool
Get-WebAppPoolState -Name "MyWebApp-Pool"
Restart-WebAppPool -Name "MyWebApp-Pool"
Start-WebAppPool -Name "MyWebApp-Pool"
Stop-WebAppPool -Name "MyWebApp-Pool"

# Elencare tutti i pool
Get-ChildItem IIS:\AppPools | Select-Object Name, State
```

### SSL/TLS Configuration

```powershell
# Importare certificato PFX
$pfxPassword = ConvertTo-SecureString -String "certpass" -AsPlainText -Force
Import-PfxCertificate -FilePath "C:\Certs\webapp.pfx" -CertStoreLocation Cert:\LocalMachine\My `
    -Password $pfxPassword

# Creare certificato self-signed (solo per test)
New-SelfSignedCertificate -DnsName "webapp.contoso.com" -CertStoreLocation Cert:\LocalMachine\My

# Richiedere certificato Let's Encrypt (via win-acme — tool di terze parti)
# Scaricare da https://github.com/win-acme/win-acme
# .\wacs.exe --target iis --siteid 1 --installation iis

# Disabilitare protocolli TLS insicuri (registry)
# TLS 1.0 — disabilitare
# HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.0\Server
# Enabled = 0, DisabledByDefault = 1

# Verificare protocolli TLS abilitati
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\*\Server" -ErrorAction SilentlyContinue

# Best practice: abilitare solo TLS 1.2 e TLS 1.3
# Usare IIS Crypto (tool di Nartac Software) per configurazione semplificata
```

### URL Rewrite Module

URL Rewrite è un modulo IIS scaricabile separatamente (non installabile con `Install-WindowsFeature`). Si installa tramite Web Platform Installer o download diretto dal sito Microsoft.

```xml
<!-- web.config — Redirect HTTP → HTTPS -->
<system.webServer>
  <rewrite>
    <rules>
      <rule name="HTTP-to-HTTPS" stopProcessing="true">
        <match url="(.*)" />
        <conditions>
          <add input="{HTTPS}" pattern="off" />
        </conditions>
        <action type="Redirect" url="https://{HTTP_HOST}/{R:1}"
                redirectType="Permanent" />
      </rule>
    </rules>
  </rewrite>
</system.webServer>

<!-- Reverse Proxy con URL Rewrite + ARR -->
<system.webServer>
  <rewrite>
    <rules>
      <rule name="ReverseProxy" stopProcessing="true">
        <match url="api/(.*)" />
        <action type="Rewrite" url="http://backend-server:8080/{R:1}" />
      </rule>
    </rules>
  </rewrite>
</system.webServer>
```

### ARR — Application Request Routing

ARR è un'estensione IIS per load balancing e reverse proxy. **Non si installa con Install-WindowsFeature** — va scaricato separatamente.

```powershell
# ARR si installa tramite:
# 1. Web Platform Installer (WebPI): WebpiCmd.exe /Install /Products:ARRv3_0
# 2. Download diretto MSI dal Microsoft Download Center
# 3. Chocolatey: choco install iis-arr -y

# Dopo l'installazione, configurare via IIS Manager:
# Server → Application Request Routing Cache → Server Proxy Settings
# Abilitare "Enable proxy"

# Creare Server Farm (pool di backend server)
# IIS Manager → Server Farms → Create Server Farm
# Aggiungere server backend (es. 10.0.0.1:8080, 10.0.0.2:8080)

# Algoritmi di bilanciamento disponibili:
# - Weighted Round Robin
# - Weighted Total Traffic
# - Least Current Requests
# - Least Response Time
# - Server Variable Hash (session affinity)
# - Query String Hash
# - Request Hash

# Health check: ARR può verificare periodicamente lo stato dei backend
# Server Farm → Health Test → URL Test: http://backend/health
# Interval: 30 secondi, Timeout: 10 secondi

# Configurazione via appcmd (alternativa)
%SystemRoot%\system32\inetsrv\appcmd.exe set config -section:webFarms `
    /+"[name='myFarm']" /commit:apphost
%SystemRoot%\system32\inetsrv\appcmd.exe set config -section:webFarms `
    /+"[name='myFarm'].[address='10.0.0.1']" /commit:apphost
```

### Hardening IIS

```powershell
# Rimuovere header Server
# web.config:
# <system.webServer><security><requestFiltering removeServerHeader="true" /></security></system.webServer>

# Disabilitare directory browsing
Set-WebConfigurationProperty -Filter /system.webServer/directoryBrowse `
    -PSPath "IIS:\Sites\MyWebApp" -Name enabled -Value $false

# Custom error pages (non esporre dettagli stack trace)
Set-WebConfigurationProperty -Filter /system.webServer/httpErrors `
    -PSPath "IIS:\Sites\MyWebApp" -Name errorMode -Value "Custom"

# Logging
Set-WebConfigurationProperty -Filter /system.webServer/httpLogging `
    -PSPath "IIS:\Sites\MyWebApp" -Name dontLog -Value $false

# Request Filtering (bloccare richieste pericolose)
# Bloccare estensioni pericolose
Add-WebConfigurationProperty -PSPath "IIS:\Sites\MyWebApp" `
    -Filter "system.webServer/security/requestFiltering/fileExtensions" `
    -Name "." -Value @{fileExtension=".exe";allowed="False"}

# Limitare dimensione richiesta (30 MB max)
Set-WebConfigurationProperty -Filter "system.webServer/security/requestFiltering/requestLimits" `
    -PSPath "IIS:\Sites\MyWebApp" -Name maxAllowedContentLength -Value 31457280

# Limitare lunghezza URL
Set-WebConfigurationProperty -Filter "system.webServer/security/requestFiltering/requestLimits" `
    -PSPath "IIS:\Sites\MyWebApp" -Name maxUrl -Value 4096

# Bloccare verbi HTTP non necessari
Add-WebConfigurationProperty -PSPath "IIS:\Sites\MyWebApp" `
    -Filter "system.webServer/security/requestFiltering/verbs" `
    -Name "." -Value @{verb="TRACE";allowed="False"}

# Aggiungere security headers
# (tramite web.config o URL Rewrite outbound rules)
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Strict-Transport-Security: max-age=31536000
# Content-Security-Policy: default-src 'self'

# Rimuovere moduli IIS non necessari
Remove-WebGlobalModule -Name "WebDAVModule"
Disable-WebGlobalModule -Name "DirectoryListingModule"
```

---

## Remote Desktop Services

### Architettura RDS

```
Componenti RDS:
┌──────────────────────────────────────────────────┐
│ RD Web Access          → Portale web per accesso │
│ RD Gateway             → Accesso esterno HTTPS   │
│ RD Connection Broker   → Gestisce connessioni    │
│ RD Session Host        → Ospita sessioni desktop │
│ RD Virtualization Host → VDI (desktop virtuali)  │
│ RD Licensing           → Gestione licenze CAL    │
└──────────────────────────────────────────────────┘

Flusso di connessione tipico:
  Client → RD Gateway (HTTPS/443) → RD Connection Broker → RD Session Host
  Client → RD Web Access (browser) → RD Connection Broker → RD Session Host
```

### Installazione e Deployment

```powershell
# Installare Session Host base (singolo server)
Install-WindowsFeature RDS-RD-Server -IncludeManagementTools

# Deploy completo (scenario produzione con più ruoli)
New-RDSessionDeployment -ConnectionBroker "RDCB01.corp.contoso.com" `
    -WebAccessServer "RDWA01.corp.contoso.com" `
    -SessionHost "RDSH01.corp.contoso.com", "RDSH02.corp.contoso.com"

# Aggiungere RD Gateway
Add-RDServer -Server "RDGW01.corp.contoso.com" -Role RDS-GATEWAY `
    -ConnectionBroker "RDCB01.corp.contoso.com"

# Aggiungere RD Licensing
Add-RDServer -Server "RDLIC01.corp.contoso.com" -Role RDS-LICENSING `
    -ConnectionBroker "RDCB01.corp.contoso.com"

# Aggiungere Session Host aggiuntivi
Add-RDServer -Server "RDSH03.corp.contoso.com" -Role RDS-RD-SERVER `
    -ConnectionBroker "RDCB01.corp.contoso.com"
```

### Session Collections

```powershell
# Creare collection di sessioni
New-RDSessionCollection -CollectionName "Desktop-Produzione" `
    -SessionHost "RDSH01.corp.contoso.com", "RDSH02.corp.contoso.com" `
    -ConnectionBroker "RDCB01.corp.contoso.com" `
    -CollectionDescription "Desktop remoti per utenti produzione"

# Configurare collection
Set-RDSessionCollectionConfiguration -CollectionName "Desktop-Produzione" `
    -ConnectionBroker "RDCB01.corp.contoso.com" `
    -UserGroup "CORP\GG-RDS-Users" `
    -MaxRedirectedMonitors 2 `
    -RDEasyPrintDriverEnabled $true `
    -ClientDeviceRedirectionOptions AudioVideoPlayBack, AudioRecording, `
        SmartCard, PlugAndPlayDevice, Drive, Clipboard

# Configurare timeout sessioni
Set-RDSessionCollectionConfiguration -CollectionName "Desktop-Produzione" `
    -ConnectionBroker "RDCB01.corp.contoso.com" `
    -IdleSessionLimitMin 60 `           # Disconnetti sessione idle dopo 60 min
    -DisconnectedSessionLimitMin 480 `  # Termina sessione disconnessa dopo 8 ore
    -ActiveSessionLimitMin 0 `          # Nessun limite sessione attiva
    -BrokenConnectionAction Disconnect  # Disconnect (non Logoff) su connessione persa

# User Profile Disks (UPD)
Set-RDSessionCollectionConfiguration -CollectionName "Desktop-Produzione" `
    -ConnectionBroker "RDCB01.corp.contoso.com" `
    -EnableUserProfileDisk `
    -DiskPath "\\FS01\UPD" `
    -MaxUserProfileDiskSizeGB 20
```

### RemoteApp

```powershell
# Pubblicare applicazione come RemoteApp
New-RDRemoteApp -CollectionName "Desktop-Produzione" `
    -DisplayName "Excel" `
    -FilePath "C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE" `
    -ConnectionBroker "RDCB01.corp.contoso.com"

New-RDRemoteApp -CollectionName "Desktop-Produzione" `
    -DisplayName "SAP GUI" `
    -FilePath "C:\Program Files\SAP\FrontEnd\SAPgui\saplogon.exe" `
    -ConnectionBroker "RDCB01.corp.contoso.com" `
    -UserGroup "CORP\GG-SAP-Users"  # Limitare a gruppo specifico

# Elencare RemoteApp
Get-RDRemoteApp -ConnectionBroker "RDCB01.corp.contoso.com"

# Rimuovere RemoteApp
Remove-RDRemoteApp -CollectionName "Desktop-Produzione" `
    -Alias "excel" -ConnectionBroker "RDCB01.corp.contoso.com" -Force
```

### RD Gateway

```powershell
# RD Gateway permette accesso RDP dall'esterno via HTTPS (443)
# Senza esporre porta 3389 direttamente

# Installare certificato SSL sul Gateway
# Usare certificato pubblico (Let's Encrypt o CA pubblica)

# Configurare RD Gateway policies:
# 1. Connection Authorization Policy (CAP): chi può connettersi
#    - Membership in gruppi AD
#    - Device redirection permessa
#    - Timeout sessione

# 2. Resource Authorization Policy (RAP): a quali server può accedere
#    - Gruppo di computer AD
#    - Rete specifica
#    - Porta RDP (3389 default)

# Configurazione GPO per client:
# Computer → Admin Templates → Windows Components → Remote Desktop Services
#   → RD Gateway → Set RD Gateway server address: rdgw.contoso.com
#   → RD Gateway → Set RD Gateway authentication method: Ask for credentials

# Connessione client via mstsc.exe:
# Show Options → Advanced → Connect from anywhere → Settings
# Server name: rdgw.contoso.com
# Logon method: Ask for credentials
```

### RDS Licensing

```powershell
# Tipi di licenze RDS:
# Per User CAL: una licenza per utente, accesso da qualsiasi dispositivo
# Per Device CAL: una licenza per dispositivo, usabile da qualsiasi utente

# Installare ruolo RD Licensing
Install-WindowsFeature RDS-Licensing -IncludeManagementTools
Install-WindowsFeature RDS-Licensing-UI

# Attivare License Server
# RD Licensing Manager → Activate Server → (wizard attivazione online)

# Installare licenze CAL
# RD Licensing Manager → Install Licenses → (inserire Agreement Number)

# Configurare il license server nel deployment
Set-RDLicenseConfiguration -LicenseServer "RDLIC01.corp.contoso.com" `
    -Mode PerUser -ConnectionBroker "RDCB01.corp.contoso.com" -Force

# Verificare licenze
Get-RDLicenseConfiguration -ConnectionBroker "RDCB01.corp.contoso.com"

# Grace period: 120 giorni senza license server configurato
# Dopo: le connessioni vengono rifiutate
```

### Gestione Sessioni

```powershell
# Elencare sessioni attive
Get-RDUserSession -ConnectionBroker "RDCB01.corp.contoso.com" |
    Select-Object UserName, HostServer, SessionState, CreateTime

# Inviare messaggio a utente
Send-RDUserMessage -HostServer "RDSH01.corp.contoso.com" -UnifiedSessionID 3 `
    -MessageTitle "Manutenzione" -MessageBody "Il server verrà riavviato tra 30 minuti"

# Disconnettere utente
Disconnect-RDUser -HostServer "RDSH01.corp.contoso.com" -UnifiedSessionID 3 -Force

# Logoff utente
Invoke-RDUserLogoff -HostServer "RDSH01.corp.contoso.com" -UnifiedSessionID 3 -Force

# Impedire nuove connessioni (per manutenzione)
Set-RDSessionHost -SessionHost "RDSH01.corp.contoso.com" `
    -NewConnectionAllowed NotUntilReboot -ConnectionBroker "RDCB01.corp.contoso.com"

# Riabilitare connessioni
Set-RDSessionHost -SessionHost "RDSH01.corp.contoso.com" `
    -NewConnectionAllowed Yes -ConnectionBroker "RDCB01.corp.contoso.com"
```

---

## Hyper-V

> **→ Per un approfondimento completo su Hyper-V (networking avanzato, replica, nested virtualization, performance tuning, backup/DR), consultare il Modulo 23.**

### Installazione e Configurazione

```powershell
# Installare Hyper-V
Install-WindowsFeature Hyper-V -IncludeManagementTools -Restart

# Switch virtuali
New-VMSwitch -Name "External" -NetAdapterName "Ethernet" -AllowManagementOS $true
New-VMSwitch -Name "Internal" -SwitchType Internal
New-VMSwitch -Name "Private" -SwitchType Private

# Tipi di switch:
# External: collegato a NIC fisica, accesso alla rete esterna
# Internal: comunicazione tra VM e host (no rete esterna)
# Private:  comunicazione solo tra VM (no host, no rete esterna)

# Creare VM
New-VM -Name "SRV-TEST" -MemoryStartupBytes 4GB -NewVHDPath "D:\VMs\SRV-TEST.vhdx" `
    -NewVHDSizeBytes 60GB -Generation 2 -SwitchName "External"

# Configurare VM
Set-VM -Name "SRV-TEST" -ProcessorCount 4 -DynamicMemory `
    -MemoryMinimumBytes 2GB -MemoryMaximumBytes 8GB
Set-VMFirmware -VMName "SRV-TEST" -EnableSecureBoot On

# Montare ISO per installazione
Add-VMDvdDrive -VMName "SRV-TEST" -Path "C:\ISO\WindowsServer2022.iso"
$dvd = Get-VMDvdDrive -VMName "SRV-TEST"
Set-VMFirmware -VMName "SRV-TEST" -FirstBootDevice $dvd

# Avviare
Start-VM -Name "SRV-TEST"

# Checkpoint (snapshot)
Checkpoint-VM -Name "SRV-TEST" -SnapshotName "Pre-Config"
Restore-VMCheckpoint -VMName "SRV-TEST" -Name "Pre-Config" -Confirm:$false
Remove-VMCheckpoint -VMName "SRV-TEST" -Name "Pre-Config"
```

### Gestione VM

```powershell
# Stato
Get-VM | Select-Object Name, State, CPUUsage, MemoryAssigned, Uptime

# Live Migration (spostare VM su altro host senza downtime)
Move-VM -Name "SRV-TEST" -DestinationHost "HV02" -IncludeStorage `
    -DestinationStoragePath "D:\VMs"

# Export/Import
Export-VM -Name "SRV-TEST" -Path "D:\Backup\VMs"
Import-VM -Path "D:\Backup\VMs\SRV-TEST\Virtual Machines\*.vmcx" -Copy -GenerateNewId

# Replica (DR)
Enable-VMReplication -VMName "SRV-PROD" -ReplicaServerName "HV-DR" `
    -ReplicaServerPort 443 -AuthenticationType Kerberos `
    -ReplicationFrequencySec 300
Start-VMInitialReplication -VMName "SRV-PROD"
```

→ **Vedi Modulo 23** per: nested virtualization, SET (Switch Embedded Teaming), VLAN tagging, discrete device assignment (DDA), Storage QoS, VM shielding, Hyper-V backup strategies.

---

## WSUS — Aggiornamenti

### Installazione

```powershell
# Installare WSUS
Install-WindowsFeature UpdateServices, UpdateServices-WidDB, UpdateServices-Services `
    -IncludeManagementTools

# Alternativa: WSUS con SQL Server (per ambienti grandi)
Install-WindowsFeature UpdateServices, UpdateServices-DB, UpdateServices-Services `
    -IncludeManagementTools

# Post-installazione (inizializzare database e content directory)
& "C:\Program Files\Update Services\Tools\wsusutil.exe" postinstall CONTENT_DIR=D:\WSUS

# Post-installazione con SQL remoto
& "C:\Program Files\Update Services\Tools\wsusutil.exe" postinstall `
    SQL_INSTANCE_NAME="SQL01\WSUS" CONTENT_DIR=D:\WSUS
```

### Configurazione

```powershell
# Configurare via PowerShell
$wsus = Get-WsusServer
$wsusConfig = $wsus.GetConfiguration()

# Impostare lingua
$wsusConfig.AllUpdateLanguagesEnabled = $false
$wsusConfig.SetEnabledUpdateLanguages("en","it")
$wsusConfig.Save()

# Selezionare prodotti
Get-WsusProduct | Where-Object {
    $_.Product.Title -in @("Windows 11", "Windows Server 2022",
        "Microsoft Defender Antivirus", "Microsoft Edge",
        "Microsoft 365 Apps/Office 2019+")
} | Set-WsusProduct

# Selezionare classificazioni
Get-WsusClassification | Where-Object {
    $_.Classification.Title -in @("Critical Updates", "Security Updates",
        "Updates", "Definition Updates", "Feature Packs")
} | Set-WsusClassification

# Configurare sincronizzazione automatica
$subscription = $wsus.GetSubscription()
$subscription.SynchronizeAutomatically = $true
$subscription.SynchronizeAutomaticallyTimeOfDay = [System.TimeSpan]::FromHours(2)  # Alle 02:00
$subscription.NumberOfSynchronizationsPerDay = 1
$subscription.Save()

# Prima sincronizzazione manuale
$subscription.StartSynchronization()

# Verificare stato sincronizzazione
$subscription.GetSynchronizationStatus()
$subscription.GetLastSynchronizationInfo()
```

### Computer Groups e Approvazioni

```powershell
# Creare gruppi target
$wsus.CreateComputerTargetGroup("01-Test")
$wsus.CreateComputerTargetGroup("02-Pilota")
$wsus.CreateComputerTargetGroup("03-Produzione-Server")
$wsus.CreateComputerTargetGroup("04-Produzione-Workstation")

# Strategia di approvazione graduale:
# Settimana 1: Approvare per gruppo "01-Test"
# Settimana 2: Se nessun problema → Approvare per "02-Pilota"
# Settimana 3: Se ok → Approvare per "03-Produzione-Server"
# Settimana 4: Approvare per "04-Produzione-Workstation"

# Approvare aggiornamenti
Get-WsusUpdate -Classification "Critical Updates" -Approval Unapproved |
    Approve-WsusUpdate -Action Install -TargetGroupName "01-Test"

# Approvare aggiornamento specifico
Get-WsusUpdate -UpdateId "12345678-abcd-efgh-ijkl-123456789012" |
    Approve-WsusUpdate -Action Install -TargetGroupName "03-Produzione-Server"

# Rifiutare aggiornamenti superseded
Get-WsusUpdate -Status InstalledOrNotApplicable |
    Where-Object { $_.Update.IsSuperseded } |
    Deny-WsusUpdate

# Auto Approval Rule
# WSUS Console → Options → Automatic Approvals
# Regola: "Critical Updates" e "Security Updates" → approvare per "01-Test" automaticamente
```

### GPO per Client WSUS

```powershell
# Computer Configuration → Administrative Templates → Windows Components → Windows Update

# Impostazioni fondamentali:
# - "Specify intranet Microsoft update service location"
#   → Set: http://wsus-server:8530 (o https://wsus-server:8531)
#   → Set: http://wsus-server:8530 (statistics server)

# - "Configure Automatic Updates"
#   → 4 - Auto download and schedule the install
#   → Scheduled install day: 0 (Every day)
#   → Scheduled install time: 03:00

# - "Enable client-side targeting"
#   → Enabled: specificare nome gruppo WSUS (es. "03-Produzione-Server")

# - "Allow Automatic Updates immediate installation"
#   → Enabled (installa subito se non richiede riavvio)

# - "No auto-restart with logged on users"
#   → Enabled (per workstation — non riavviare durante orario lavoro)

# - "Reschedule Automatic Updates scheduled installations"
#   → Enabled: 15 minuti (riprova dopo riavvio)

# Verifica da client
wuauclt /detectnow     # Forza rilevamento aggiornamenti
wuauclt /reportnow     # Forza report stato al WSUS
# PowerShell (Windows 10+):
usoclient StartScan
usoclient StartInstall
```

### Manutenzione WSUS

```powershell
# Pulizia WSUS (CRITICO — il database cresce rapidamente)
# WSUS Console → Options → Server Cleanup Wizard

# Via PowerShell:
Invoke-WsusServerCleanup -CleanupObsoleteComputers `
    -CleanupObsoleteUpdates -CleanupUnneededContentFiles `
    -CompressUpdates -DeclineExpiredUpdates `
    -DeclineSupersededUpdates

# Re-indicizzare database WID (Windows Internal Database)
# Eseguire script SQL:
# USE SUSDB
# EXEC sp_MSforeachtable 'ALTER INDEX ALL ON ? REBUILD'

# Verificare dimensione content directory
Get-ChildItem D:\WSUS -Recurse | Measure-Object -Property Length -Sum |
    Select-Object @{N="SizeGB"; E={[math]::Round($_.Sum / 1GB, 2)}}

# Report: computer che non comunicano da più di 30 giorni
$wsus.GetComputerTargets() | Where-Object {
    $_.LastReportedStatusTime -lt (Get-Date).AddDays(-30)
} | Select-Object FullDomainName, LastReportedStatusTime

# Spostare WSUS content directory
& "C:\Program Files\Update Services\Tools\wsusutil.exe" movecontent "E:\WSUS" "D:\wsus_move.log"
```

---

## WDS — Deployment Services

### Installazione e Configurazione

```powershell
# Installare WDS
Install-WindowsFeature WDS -IncludeManagementTools

# Requisiti:
# - Server membro del dominio AD (o standalone)
# - DHCP server raggiungibile
# - DNS server funzionante
# - Partizione NTFS per immagini

# Inizializzare WDS
wdsutil /Initialize-Server /RemInst:"D:\RemoteInstall"

# Configurare in modalità AD-integrated
wdsutil /Initialize-Server /RemInst:"D:\RemoteInstall" /Authorize

# Verificare stato
wdsutil /Get-Server /Show:Config
```

### Gestione Immagini

```powershell
# Aggiungere boot image (necessaria per PXE boot — da ISO Windows)
Import-WdsBootImage -Path "D:\Sources\boot.wim" -NewImageName "WinPE Setup"

# Aggiungere install image (immagine del sistema operativo)
# Creare gruppo immagini
New-WdsInstallImageGroup -Name "Windows Server 2022"

Import-WdsInstallImage -ImageGroup "Windows Server 2022" `
    -Path "D:\Sources\install.wim" -ImageName "Windows Server 2022 Standard"

# Aggiungere più edizioni dalla stessa WIM
Import-WdsInstallImage -ImageGroup "Windows Server 2022" `
    -Path "D:\Sources\install.wim" -ImageName "Windows Server 2022 Datacenter"

# Elencare immagini
Get-WdsBootImage | Select-Object ImageName, Architecture
Get-WdsInstallImage | Select-Object ImageGroup, ImageName

# Rimuovere immagine
Remove-WdsInstallImage -ImageGroup "Windows Server 2022" `
    -ImageName "Windows Server 2022 Essentials"

# Capture image (per creare immagine reference da un PC configurato)
# 1. Boot da WinPE
# 2. Eseguire sysprep /generalize /oobe /shutdown
# 3. Boot da WDS → scegliere capture image
# 4. Catturare disco in file WIM
```

### PXE Boot Configuration

```powershell
# Configurare risposta PXE
wdsutil /Set-Server /AnswerClients:Known     # Solo computer pre-staged in AD
wdsutil /Set-Server /AnswerClients:All       # Tutti i client PXE
wdsutil /Set-Server /AnswerClients:None      # Nessuna risposta PXE

# Se DHCP sullo stesso server:
wdsutil /Set-Server /UseDhcpPorts:No
# Oppure configurare opzioni DHCP 66/67 (vedi sezione DHCP)

# Pre-stage computer in AD per WDS
New-ADComputer -Name "WKS-NEW-001" -SamAccountName "WKS-NEW-001$" `
    -Path "OU=Staging,DC=corp,DC=contoso,DC=com"
wdsutil /Add-Device /Device:WKS-NEW-001 /ID:AABBCCDDEEFF  # MAC address

# Configurare UEFI PXE boot
# WDS supporta sia BIOS che UEFI
# Per UEFI: boot file = boot\x64\wdsmgfw.efi
# Per BIOS: boot file = boot\x64\wdsnbp.com

# Se DHCP su server separato, configurare DHCP relay:
# Opzione 66: IP del server WDS
# Opzione 67: boot\x64\wdsmgfw.efi (UEFI) o boot\x64\wdsnbp.com (BIOS)
```

### Automated Deployment con file di risposta

```powershell
# WDS supporta file unattend.xml per automazione completa:
# 1. WDS Client Unattend (WDSClientUnattend.xml)
#    → Automatizza la scelta dell'immagine nel menu WDS
#
# 2. Image Unattend (ImageUnattend.xml per ogni immagine)
#    → Automatizza l'installazione Windows (partizioni, utente, nome PC, etc.)

# Associare file unattend a un'immagine
wdsutil /Set-Image /Image:"Windows Server 2022 Standard" `
    /ImageType:Install /ImageGroup:"Windows Server 2022" `
    /UnattendFile:"D:\Unattend\server2022-unattend.xml"

# Associare WDS client unattend
wdsutil /Set-Server /WDSClientUnattend /Architecture:x64 `
    /FilePath:"D:\Unattend\WDSClientUnattend.xml"

# Multicast (distribuzione simultanea a più client)
New-WdsMulticastTransmission -Name "Win2022-Deploy" `
    -FriendlyName "Deploy Windows Server 2022" `
    -ImageGroup "Windows Server 2022" `
    -ImageName "Windows Server 2022 Standard" `
    -TransmissionType AutoCast
# AutoCast: inizia appena un client si connette
# ScheduledCast: inizia al raggiungimento di un numero minimo di client
```

---

## NPS — Network Policy Server

NPS è l'implementazione Microsoft del protocollo RADIUS (Remote Authentication Dial-In User Service). Viene utilizzato per autenticazione centralizzata di accesso alla rete (802.1X, VPN, WiFi).

### Installazione

```powershell
# Installare NPS
Install-WindowsFeature NPAS -IncludeManagementTools

# Registrare NPS in Active Directory (necessario per leggere proprietà dial-in degli account)
netsh nps register

# oppure via PowerShell
NPS # apre la console NPS (nps.msc)
```

### RADIUS Clients

```powershell
# Aggiungere RADIUS client (switch, access point, VPN server)
# Via GUI: NPS Console → RADIUS Clients and Servers → RADIUS Clients → New

# Informazioni necessarie per ogni client RADIUS:
# - Friendly name (es. "Switch-Piano1")
# - IP address (es. 192.168.10.100)
# - Shared secret (password condivisa tra NPS e device)

# Via netsh:
netsh nps add client name="Switch-Piano1" address=192.168.10.100 `
    sharedsecret="R@d1usS3cret!" vendor="RADIUS Standard"

netsh nps add client name="AP-Conferenze" address=192.168.10.110 `
    sharedsecret="W1f1S3cret!" vendor="RADIUS Standard"

# Elencare client
netsh nps show client

# Rimuovere client
netsh nps delete client name="Switch-Piano1"
```

### Network Policies

Le Network Policies determinano chi può accedere alla rete e con quali condizioni.

```powershell
# Struttura di una Network Policy:
# 1. Condizioni (Conditions): chi si applica la policy
#    - Gruppi AD (Windows Groups)
#    - Tipo di connessione (Wireless, VPN, Wired)
#    - Orario (Day-and-time restrictions)
#    - VLAN ID
#    - MAC address
#
# 2. Vincoli (Constraints): requisiti per l'accesso
#    - Metodo di autenticazione (PEAP, EAP-TLS, MSCHAPv2)
#    - Timeout sessione
#    - Idle timeout
#
# 3. Impostazioni (Settings): cosa succede se policy match
#    - VLAN assignment
#    - Bandwidth restrictions
#    - IP filters
#    - Encryption settings

# Esempio: Policy per accesso WiFi corporate
# Condizione: membro del gruppo "GG-WiFi-Users"
# Condizione: tipo connessione = Wireless
# Vincolo: autenticazione PEAP-MSCHAPv2
# Impostazione: assegnare VLAN 100

# Esempio: Policy per 802.1X wired
# Condizione: membro del gruppo "Domain Computers"
# Condizione: Health policy = compliant
# Vincolo: EAP-TLS (certificato macchina)
# Impostazione: assegnare VLAN 10 (produzione)
# Impostazione: non compliant → VLAN 999 (quarantena)
```

### 802.1X Integration

```powershell
# 802.1X richiede:
# 1. NPS server configurato con policy
# 2. Switch/AP configurato come RADIUS client
# 3. Client con supplicant 802.1X abilitato
# 4. (Opzionale) PKI per certificati EAP-TLS

# Configurazione switch Cisco (esempio):
# aaa new-model
# aaa authentication dot1x default group radius
# aaa authorization network default group radius
# radius server NPS01
#   address ipv4 192.168.10.10 auth-port 1812 acct-port 1813
#   key R@d1usS3cret!
# interface GigabitEthernet0/1
#   dot1x port-control auto
#   authentication order dot1x mab
#   authentication fallback mab

# Configurazione WiFi enterprise (WPA2/WPA3-Enterprise):
# SSID → Security: WPA2-Enterprise
# RADIUS server: 192.168.10.10
# RADIUS secret: R@d1usS3cret!
# Authentication: PEAP-MSCHAPv2

# GPO per abilitare 802.1X sui client Windows:
# Computer → Policies → Windows Settings → Security Settings
#   → Network Access Protection → NAP Client Configuration
#   → Wired Network (IEEE 802.3) Policies
```

### Backup e Restore NPS

```powershell
# Export configurazione NPS completa
Export-NpsConfiguration -Path "C:\Backup\nps-config.xml"

# Export con chiave di crittografia
netsh nps export filename="C:\Backup\nps-config.xml" exportPSK=YES

# Import configurazione
Import-NpsConfiguration -Path "C:\Backup\nps-config.xml"

# NOTA: fare backup regolari — la configurazione NPS è complessa
# e ricrearla manualmente richiede tempo significativo
```

### NPS Logging e Accounting

```powershell
# NPS può registrare eventi di autenticazione:
# 1. File di testo locale
# 2. SQL Server (per reporting centralizzato)
# 3. Event Log

# Configurare logging su file
# NPS Console → Accounting → Configure Accounting
# → Log to a text file → Directory: D:\NPS-Logs

# Configurare logging su SQL
# NPS Console → Accounting → SQL Server Logging → Configure

# Abilitare NPS event logging dettagliato
# Event Viewer → Custom Views → Server Roles → Network Policy and Access Services
# Oppure:
auditpol /set /subcategory:"Network Policy Server" /success:enable /failure:enable
```

---

## Storage Spaces

Storage Spaces permette di aggregare dischi fisici in pool di storage e creare volumi virtuali con resilienza e flessibilità.

### Concetti

```
Architettura Storage Spaces:
┌─────────────────────────────────────────────┐
│ Volume (lettera di unità, NTFS/ReFS)       │
├─────────────────────────────────────────────┤
│ Virtual Disk (Simple / Mirror / Parity)     │
├─────────────────────────────────────────────┤
│ Storage Pool (aggregazione dischi fisici)    │
├─────────────────────────────────────────────┤
│ Dischi fisici (HDD, SSD, NVMe)             │
└─────────────────────────────────────────────┘

Tipi di resilienza:
- Simple:  striping, nessuna ridondanza (RAID-0 equivalent)
           Performance massima, zero tolleranza guasti
- Mirror:  2 o 3 copie dei dati (RAID-1 / RAID-10 equivalent)
           Tolleranza 1 o 2 guasti disco
- Parity:  striping con parità (RAID-5/6 equivalent)
           Efficienza storage migliore, performance scrittura inferiore
```

### Configurazione

```powershell
# Elencare dischi fisici disponibili (non inizializzati)
Get-PhysicalDisk | Where-Object CanPool -eq $true |
    Select-Object FriendlyName, Size, MediaType, BusType

# Creare Storage Pool
$disks = Get-PhysicalDisk | Where-Object CanPool -eq $true
New-StoragePool -FriendlyName "DataPool" `
    -StorageSubSystemFriendlyName "Windows Storage*" `
    -PhysicalDisks $disks

# Creare Virtual Disk — Simple (no ridondanza)
New-VirtualDisk -FriendlyName "TempData" -StoragePoolFriendlyName "DataPool" `
    -Size 500GB -ResiliencySettingName Simple -ProvisioningType Thin

# Creare Virtual Disk — Mirror (2-way)
New-VirtualDisk -FriendlyName "CriticalData" -StoragePoolFriendlyName "DataPool" `
    -Size 200GB -ResiliencySettingName Mirror -NumberOfDataCopies 2

# Creare Virtual Disk — Mirror (3-way, tolleranza 2 guasti)
New-VirtualDisk -FriendlyName "VeryImportant" -StoragePoolFriendlyName "DataPool" `
    -Size 100GB -ResiliencySettingName Mirror -NumberOfDataCopies 3

# Creare Virtual Disk — Parity (simile a RAID-5)
New-VirtualDisk -FriendlyName "ArchiveData" -StoragePoolFriendlyName "DataPool" `
    -Size 1TB -ResiliencySettingName Parity -ProvisioningType Thin

# Inizializzare, partizionare e formattare
$vdisk = Get-VirtualDisk -FriendlyName "CriticalData"
$vdisk | Initialize-Disk -PartitionStyle GPT
$vdisk | Get-Disk | New-Partition -UseMaximumSize -AssignDriveLetter |
    Format-Volume -FileSystem ReFS -NewFileSystemLabel "CriticalData" -Confirm:$false

# Thin Provisioning vs Fixed
# Thin: spazio allocato on-demand (sovra-allocazione possibile)
# Fixed: spazio riservato immediatamente (più prevedibile)
```

### Gestione Storage Spaces

```powershell
# Verificare stato pool
Get-StoragePool | Select-Object FriendlyName, HealthStatus, Size, AllocatedSize

# Verificare dischi nel pool
Get-StoragePool -FriendlyName "DataPool" | Get-PhysicalDisk |
    Select-Object FriendlyName, Size, HealthStatus, OperationalStatus, Usage

# Aggiungere disco al pool (espandere capacità)
$newDisk = Get-PhysicalDisk | Where-Object CanPool -eq $true | Select-Object -First 1
Add-PhysicalDisk -StoragePoolFriendlyName "DataPool" -PhysicalDisks $newDisk

# Rimuovere disco dal pool (previo rilocazione dati)
Set-PhysicalDisk -FriendlyName "OldDisk" -Usage Retired
Remove-PhysicalDisk -StoragePoolFriendlyName "DataPool" -PhysicalDisk (
    Get-PhysicalDisk -FriendlyName "OldDisk")

# Espandere virtual disk
Resize-VirtualDisk -FriendlyName "CriticalData" -Size 300GB

# Riparare virtual disk dopo guasto disco
Repair-VirtualDisk -FriendlyName "CriticalData"

# Tiered Storage (SSD come cache + HDD per capacità)
# Richiede almeno 1 SSD e 1 HDD nel pool
$ssd = Get-PhysicalDisk | Where-Object MediaType -eq SSD
$hdd = Get-PhysicalDisk | Where-Object MediaType -eq HDD

New-StorageTier -StoragePoolFriendlyName "DataPool" -FriendlyName "SSD-Tier" `
    -MediaType SSD -ResiliencySettingName Mirror
New-StorageTier -StoragePoolFriendlyName "DataPool" -FriendlyName "HDD-Tier" `
    -MediaType HDD -ResiliencySettingName Parity

New-VirtualDisk -FriendlyName "TieredVolume" -StoragePoolFriendlyName "DataPool" `
    -StorageTiers (Get-StorageTier -FriendlyName "SSD-Tier"),
                  (Get-StorageTier -FriendlyName "HDD-Tier") `
    -StorageTierSizes 50GB, 500GB
```

### Storage Spaces Direct (S2D)

S2D è la versione cluster di Storage Spaces, disponibile **solo con Datacenter edition**. Crea storage condiviso software-defined usando dischi locali dei nodi cluster.

```powershell
# Requisiti S2D:
# - Windows Server Datacenter
# - Minimo 2 nodi (raccomandato 4+)
# - Almeno 2 dischi dati per nodo (oltre al disco OS)
# - Network: 10 GbE o superiore (RDMA raccomandato)
# - Failover Clustering installato e validato

# Abilitare Storage Spaces Direct
Enable-ClusterStorageSpacesDirect -CacheState Enabled -Autoconfig:$true

# Oppure con configurazione specifica
Enable-ClusterStorageSpacesDirect -PoolFriendlyName "S2D Pool" `
    -CacheState Enabled -CacheDeviceModel "INTEL SSDSC*"

# Creare volume S2D
New-Volume -FriendlyName "VM-Storage" -StoragePoolFriendlyName "S2D*" `
    -FileSystem CSVFS_ReFS -Size 1TB -ResiliencySettingName Mirror

# Verificare stato S2D
Get-StorageSubSystem -FriendlyName "*Cluster*" | Get-StorageHealthReport
Get-ClusterPerformanceHistory

# Monitorare da Windows Admin Center:
# WAC è lo strumento raccomandato per gestione S2D (dashboard dedicato)

# NOTA: S2D è la base di Azure Stack HCI
```

---

## Failover Clustering

### Installazione e Validazione

```powershell
# Installare feature
Install-WindowsFeature Failover-Clustering -IncludeManagementTools

# Validare cluster (PRIMA di creare — obbligatorio)
Test-Cluster -Node "NODE01", "NODE02" -Include Storage, Network, Inventory

# Il report di validazione va in: C:\Users\<utente>\AppData\Local\Temp\
# Verificare che NON ci siano errori (warning accettabili, errori no)

# Creare cluster
New-Cluster -Name "CLUSTER01" -Node "NODE01", "NODE02" `
    -StaticAddress 192.168.10.100 -NoStorage

# Aggiungere storage condiviso
# (Dopo aver presentato LUN iSCSI o Shared VHDX)
Get-ClusterAvailableDisk | Add-ClusterDisk

# Cluster Shared Volumes (CSV)
Add-ClusterSharedVolume -Name "Cluster Disk 1"

# Quorum
Set-ClusterQuorum -CloudWitness -AccountName "storageaccount" `
    -AccessKey "key" -Endpoint "core.windows.net"
# Oppure: File Share Witness
Set-ClusterQuorum -FileShareWitness "\\SRV01\Witness"

# Ruoli cluster
Add-ClusterFileServerRole -Storage "Cluster Disk 2" -Name "FS-CLUSTER" `
    -StaticAddress 192.168.10.101

# Status
Get-ClusterNode | Select-Object Name, State
Get-ClusterGroup | Select-Object Name, State, OwnerNode
Get-ClusterResource | Select-Object Name, State, ResourceType
```

---

## Azure Arc — Gestione Ibrida dei Ruoli Server

Azure Arc estende i servizi di gestione di Azure ai server on-premises e multi-cloud. Con Windows Server 2025, l'integrazione è diventata un pilastro dell'amministrazione ibrida: hotpatching, Azure Policy, monitoring e automazione operativa funzionano su server fisici nel datacenter locale come fossero risorse Azure.

### Onboarding — Connettere un Server ad Azure Arc

```powershell
# Metodo 1: Script interattivo (singolo server)
# Scaricare lo script dal portale Azure:
# Azure Portal → Azure Arc → Servers → Add → "Generate script"

# Metodo 2: Installazione silenziosa (deployment di massa)
# Scaricare l'agente Azure Connected Machine
Invoke-WebRequest -Uri "https://aka.ms/azcmagent-windows" `
    -OutFile "$env:TEMP\install_windows_azcmagent.ps1"

# Eseguire l'installazione
& "$env:TEMP\install_windows_azcmagent.ps1"

# Connettere il server ad Azure Arc
azcmagent connect --resource-group "rg-servers-onprem" `
    --tenant-id "TENANT_ID" `
    --subscription-id "SUBSCRIPTION_ID" `
    --location "westeurope" `
    --tags "Env=Production,Role=FileServer"

# Verificare lo stato della connessione
azcmagent show
# Status: Connected → il server è visibile in Azure Portal

# Metodo 3: Group Policy (deployment su scala enterprise)
# Scaricare il pacchetto MSI dell'agente e distribuirlo via GPO
# L'agente si configura via registro di sistema post-installazione
```

### Azure Policy per Configuration Drift

Azure Policy applicato tramite Arc consente di rilevare e correggere automaticamente deviazioni dalla configurazione desiderata. È l'equivalente cloud-native delle GPO, ma con audit centralizzato e compliance scoring.

```powershell
# Esempi di policy utili per server con ruoli:

# 1. Verificare che Windows Defender sia abilitato su tutti i server
# Policy built-in: "Windows Defender Exploit Guard should be enabled"

# 2. Verificare che TLS 1.0/1.1 sia disabilitato
# Policy custom: guest configuration che controlla le chiavi di registro

# 3. Verificare che i ruoli non autorizzati non siano installati
# Policy custom example:
# → Condition: se "Web-Server" è installato su un server taggato "Role=DC"
# → Effect: Audit / Deny

# Verificare compliance dal server locale
azcmagent config list

# Verificare estensioni Arc installate
az connectedmachine extension list `
    --machine-name "SRV01" --resource-group "rg-servers-onprem" `
    --output table
```

### Azure Monitor e Microsoft Defender per Server Arc

```powershell
# Installare l'estensione Azure Monitor Agent (AMA) via Arc
az connectedmachine extension create `
    --machine-name "SRV01" --resource-group "rg-servers-onprem" `
    --name "AzureMonitorWindowsAgent" `
    --publisher "Microsoft.Azure.Monitor" `
    --type "AzureMonitorWindowsAgent"

# Configurare Data Collection Rules (DCR) per raccogliere:
# - Performance counters (CPU, Memoria, Disco, Rete)
# - Windows Event Log (System, Application, Security)
# - Sysmon events (se installato)
# - IIS logs, DNS debug logs, DHCP audit logs

# Microsoft Defender for Servers (Piano 2) tramite Arc:
# - Vulnerability Assessment integrato
# - Just-in-Time VM Access (anche per server fisici via Arc)
# - Adaptive Application Controls
# - File Integrity Monitoring
```

### Pipeline di Hotpatching tramite Azure Arc

Il hotpatching elimina la necessità di riavviare il server per la maggior parte degli aggiornamenti di sicurezza mensili. Il ciclo trimestrale con Server 2025 e Arc:

```
Ciclo di patching hotpatch (trimestrale):

Mese 1 (Baseline):  Cumulative Update completo → richiede riavvio
Mese 2 (Hotpatch):  Patch di sicurezza → NO riavvio
Mese 3 (Hotpatch):  Patch di sicurezza → NO riavvio
Mese 4 (Baseline):  Cumulative Update completo → richiede riavvio
...

Risultato: solo 4 riavvii obbligatori all'anno invece di 12.

Requisiti:
  □ Windows Server 2025 Standard o Datacenter
  □ Agente Azure Arc connesso e funzionante
  □ Estensione Windows OS Extension installata
  □ Server registrato per hotpatch in Azure Update Manager
```

```powershell
# Verificare idoneità al hotpatching
az connectedmachine show --name "SRV01" `
    --resource-group "rg-servers-onprem" `
    --query "properties.osProfile"

# Configurare Azure Update Manager per hotpatch
# Azure Portal → Update Manager → Machines → selezionare server
# → Settings → Hotpatch → Enable

# Monitorare lo stato degli aggiornamenti hotpatch
az connectedmachine extension show `
    --machine-name "SRV01" --resource-group "rg-servers-onprem" `
    --name "WindowsOSExtension" --query "properties.instanceView"
```

### Azure SRE Agent — Automazione Operativa (Anteprima)

Azure SRE Agent è un servizio in anteprima che automatizza operazioni di site reliability engineering per server Arc-enabled. Può diagnosticare problemi, eseguire remediation automatiche e proporre ottimizzazioni basate su pattern osservati nei dati di telemetria.

```
Scenari supportati da SRE Agent (anteprima pubblica 2025):

1. Disk space low → identifica file temporanei, log vecchi, li archivia o rimuove
2. Service failure → analizza event log, riavvia il servizio, verifica il ripristino
3. High CPU → identifica il processo, correla con deployment recenti
4. Certificate expiry → avvisa 30 giorni prima della scadenza
5. Drift detection → confronta la configurazione attuale con la baseline

Nota: SRE Agent opera in modalità "suggest and confirm" (non autonoma)
      in produzione. L'amministratore approva le azioni proposte.
```

---

## Best Practices e Hardening

### Separazione dei Ruoli

```
Regole fondamentali:
1. Un server = massimo 1-2 ruoli (ideale: 1 ruolo)
2. Domain Controller NON deve ospitare altri ruoli applicativi
   (no IIS, no SQL, no file server su un DC)
3. Eccezione: DNS su DC è accettabile (sono strettamente integrati)
4. Server DHCP e DNS possono coesistere (se non su un DC)
5. WSUS su server dedicato (database e storage intensivi)
6. Print Server su server dedicato (driver instabili possono crashare)
7. RDS Session Host: server dedicato con risorse abbondanti
```

### Principio del Minimo Privilegio

```powershell
# Service accounts: usare Managed Service Accounts (gMSA)
New-ADServiceAccount -Name "svc-webapp" -DNSHostName "svc-webapp.corp.contoso.com" `
    -PrincipalsAllowedToRetrieveManagedPassword "IIS-Servers$"
Install-ADServiceAccount -Identity "svc-webapp"

# Non usare mai Domain Admin per servizi
# Non usare mai account personali per servizi
# Creare account di servizio dedicati con permessi minimi

# Application Pool IIS: usare ApplicationPoolIdentity (default)
# oppure gMSA, MAI Domain Admin

# Audit: verificare chi ha accesso amministrativo
Get-ADGroupMember "Domain Admins" | Select-Object Name, ObjectClass
Get-ADGroupMember "Enterprise Admins" | Select-Object Name, ObjectClass
Get-ADGroupMember "Schema Admins" | Select-Object Name, ObjectClass
# Questi gruppi dovrebbero contenere il minimo numero di account
```

### Hardening del Server

```powershell
# 1. Disabilitare SMBv1
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart

# 2. Disabilitare servizi non necessari
# Spooler su server senza stampanti
Stop-Service Spooler; Set-Service Spooler -StartupType Disabled

# Xbox services, Fax, etc. (su server)
Get-Service -Name XblAuthManager, XblGameSave, XboxNetApiSvc, Fax |
    Stop-Service -PassThru | Set-Service -StartupType Disabled

# 3. Windows Firewall: attivo su tutti i profili
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

# 4. Abilitare Windows Defender (se non c'è AV di terze parti)
Set-MpPreference -DisableRealtimeMonitoring $false

# 5. Configurare NTP (per Kerberos — tolleranza massima 5 minuti)
w32tm /config /manualpeerlist:"time.windows.com" /syncfromflags:manual /reliable:yes /update

# 6. Disabilitare TLS 1.0 e 1.1 (registry)
# TLS 1.0 Server
New-Item "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.0\Server" -Force
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.0\Server" `
    -Name "Enabled" -Value 0 -PropertyType DWORD
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.0\Server" `
    -Name "DisabledByDefault" -Value 1 -PropertyType DWORD

# 7. Audit policy
auditpol /set /subcategory:"Logon" /success:enable /failure:enable
auditpol /set /subcategory:"Account Lockout" /success:enable /failure:enable
auditpol /set /subcategory:"Logoff" /success:enable
auditpol /set /subcategory:"Other Logon/Logoff Events" /success:enable /failure:enable

# 8. Bloccare account dopo tentativi falliti (GPO)
# Computer → Windows Settings → Security Settings → Account Policies → Account Lockout Policy
# Account lockout threshold: 5 invalid logon attempts
# Account lockout duration: 30 minutes
# Reset account lockout counter after: 30 minutes

# 9. Password policy (GPO)
# Minimum password length: 14 characters
# Password complexity: Enabled
# Maximum password age: 90 days
# Minimum password age: 1 day
# Enforce password history: 24 passwords
```

### Documentazione obbligatoria per ogni ruolo

```
Per ogni ruolo server installato, documentare:
1. Nome server e IP
2. Ruolo installato e versione
3. Dipendenze (altri server, servizi, database)
4. Account di servizio utilizzato
5. Porte firewall necessarie
6. Procedura di backup e restore
7. Procedura di DR (disaster recovery)
8. Contatto/responsabile
9. Data installazione e ultima modifica
10. Baseline performance (CPU, RAM, disco, rete)
```

### Monitoraggio

```powershell
# Performance Monitor: contatori chiave per ruolo
# DNS:
#   DNS → Total Query Received/sec
#   DNS → Recursive Queries/sec
#   DNS → Total Response Sent/sec

# DHCP:
#   DHCP Server → Discovers/sec
#   DHCP Server → Offers/sec
#   DHCP Server → Acks/sec

# IIS:
#   Web Service → Current Connections
#   Web Service → Total Method Requests/sec
#   ASP.NET → Requests Queued

# File Server:
#   SMB Server Shares → Current Open File Count
#   SMB Server Shares → Transferred Bytes/sec

# General:
#   Processor → % Processor Time
#   Memory → Available MBytes
#   PhysicalDisk → Avg. Disk Queue Length
#   Network Interface → Bytes Total/sec

# Configurare alert via PowerShell (Performance Counter Alert)
$counter = "\Processor(_Total)\% Processor Time"
Register-ObjectEvent -InputObject (
    New-Object System.Diagnostics.PerformanceCounter("Processor", "% Processor Time", "_Total")
) -EventName "Disposed" -Action { Write-EventLog -LogName Application -Source "Monitoring" -EventId 1001 -Message "CPU alta" }

# Windows Admin Center per monitoraggio moderno e centralizzato
```

### Backup prima di ogni modifica

```powershell
# 1. Snapshot VM (se virtualizzato)
Checkpoint-VM -Name "SRV-PROD" -SnapshotName "Pre-$(Get-Date -Format 'yyyyMMdd-HHmm')"

# 2. System State Backup (per DC, DNS, DHCP, CA)
wbadmin start systemstatebackup -backuptarget:D:\Backup

# 3. Windows Server Backup
Install-WindowsFeature Windows-Server-Backup
wbadmin start backup -backuptarget:D:\Backup -include:C: -systemstate -quiet

# 4. Export configurazione ruolo specifico
# DNS:
Export-DnsServerZone -Name "corp.contoso.com" -FileName "corp.contoso.com.dns.bak"
dnscmd /ZoneExport corp.contoso.com corp.contoso.com.dns.bak

# DHCP:
Export-DhcpServer -File "C:\Backup\dhcp-export.xml" -Leases

# NPS:
Export-NpsConfiguration -Path "C:\Backup\nps-config.xml"

# IIS:
& "$env:SystemRoot\system32\inetsrv\appcmd.exe" list config /xml > "C:\Backup\iis-config.xml"

# GPO:
Backup-GPO -All -Path "C:\Backup\GPO"
```

---

## Troubleshooting

### DNS

**"DNS non risolve dopo installazione"** → Verificare che le zone siano create e attive, che il servizio DNS sia in esecuzione (`Get-Service DNS`), che il server punti a se stesso come DNS primario. Controllare `dcdiag /test:dns`.

**"Record DNS non si aggiornano"** → Verificare che l'aging sia abilitato sulla zona (`Get-DnsServerZoneAging`), che lo scavenging sia abilitato sul server, che il client abbia la registrazione dinamica attiva. Controllare che l'account computer abbia permessi di aggiornamento sulla zona.

**"Zone transfer fallisce"** → Verificare ACL di trasferimento zona (`Get-DnsServerZoneTransferPolicy`), che la porta TCP 53 sia aperta nel firewall, che il serial number della zona sia aggiornato. Usare `nslookup`, `set type=axfr`, e testare la connettività.

**"Risoluzione lenta"** → Verificare forwarder configurati e raggiungibili, root hints aggiornati, nessun DNS server non raggiungibile nella lista. Controllare cache del server con `Show-DnsServerCache`.

**"DNSSEC validation failure"** → Verificare trust anchor configurato correttamente, che le chiavi non siano scadute, che l'orologio del server sia sincronizzato. Controllare con `Resolve-DnsName -DnssecOk`.

### DHCP

**"DHCP non assegna IP"** → Verificare: server autorizzato in AD (`Get-DhcpServerInDC`), scope attivo, range non esaurito (`Get-DhcpServerv4ScopeStatistics`), firewall permette UDP 67/68, DHCP relay configurato se client su altra subnet.

**"IP conflicts (duplicati)"** → Verificare che non ci siano IP statici nel range DHCP, che le esclusioni siano configurate correttamente, che non ci siano due server DHCP con scope sovrapposti senza failover. Controllare `Get-DhcpServerv4Lease` per lease duplicati.

**"Client non rinnova il lease"** → Verificare raggiungibilità del server DHCP dalla subnet del client, che il lease non sia scaduto durante un'interruzione prolungata. Forzare rinnovo con `ipconfig /renew` sul client.

**"DHCP Failover out of sync"** → Forzare replica con `Invoke-DhcpServerv4FailoverReplication`, verificare connettività di rete tra i due server, controllare stato con `Get-DhcpServerv4Failover`.

### IIS

**"IIS restituisce 500 Internal Server Error"** → Abilitare detailed errors in web.config (`<httpErrors errorMode="DetailedLocalOnly"/>`), controllare Event Viewer → Application, verificare Application Pool attivo, controllare permessi sulla directory fisica.

**"Application Pool si arresta (crash loop)"** → Controllare Event Viewer per eccezioni .NET, verificare rapid-fail protection settings, controllare disponibilità RAM. L'app pool va in stop dopo 5 crash in 5 minuti (default).

**"Certificato SSL non funziona"** → Verificare che il certificato sia nello store `LocalMachine\My`, che il binding HTTPS sia configurato con il thumbprint corretto, che il certificato non sia scaduto. Controllare con `netsh http show sslcert`.

**"Binding conflict: altra applicazione usa la porta"** → `netstat -anb | findstr :80` per identificare il processo. Conflitto comune: Skype, Apache, altro servizio. Risolvere fermando il servizio conflittuale o cambiando porta.

### Hyper-V

**"VM non si avvia"** → Verificare risorse disponibili (RAM, disco), controllare Event Viewer → Hyper-V-VMMS, verificare che VHD non sia corrotto (`Test-VHD`), controllare Secure Boot per VM Gen2.

**"Live Migration fallisce"** → Verificare che entrambi gli host abbiano la stessa versione del processore (o compatibilità processore abilitata nella VM), che Kerberos delegation sia configurata, che la rete di migrazione sia raggiungibile.

**"Performance scarse nelle VM"** → Verificare che Integration Services siano installati e aggiornati, che dynamic memory sia configurata correttamente, che non ci sia overcommit di CPU/RAM sull'host. Controllare NUMA topology.

### File Server

**"Accesso negato a condivisione"** → Verificare sia i permessi Share che NTFS (il più restrittivo prevale). Controllare gruppo di appartenenza dell'utente. Usare `Get-SmbShareAccess -Name "NomeShare"` e `Get-Acl` per diagnosticare.

**"DFS-R non replica"** → Verificare stato con `Get-DfsrState`, controllare backlog con `Get-DfsrBacklog`, verificare connettività tra i membri, controllare Event Viewer → DFS Replication. Forzare polling con `dfsrdiag pollad`.

**"FSRM quota non si applica"** → Verificare che la quota sia applicata al path corretto, che il servizio FSRM sia in esecuzione, che il template sia corretto. Rigenerare con `Update-FsrmQuota`.

### WSUS

**"Client non comunica con WSUS"** → Verificare GPO applicata (`gpresult /r`), che il server WSUS sia raggiungibile (`Test-NetConnection wsus-server -Port 8530`), che il servizio WUAgent sia in esecuzione. Forzare con `wuauclt /detectnow`.

**"WSUS console lenta o errore HTTP 503"** → Il database WID è probabilmente troppo grande. Eseguire cleanup (`Invoke-WsusServerCleanup`) e re-indicizzazione del database. Verificare pool IIS `WsusPool` sia attivo e abbia memoria sufficiente.

**"Aggiornamenti non si installano"** → Verificare spazio disco, che l'aggiornamento sia approvato per il gruppo corretto, che non ci siano aggiornamenti prerequisito mancanti. Controllare `C:\Windows\WindowsUpdate.log` (o `Get-WindowsUpdateLog` su Windows 10+).

### RDS

**"Utenti non possono connettersi a RDS"** → Verificare licenze RDS valide (grace period 120 giorni), che il session host accetti connessioni, che l'utente sia membro del gruppo "Remote Desktop Users", che il firewall permetta porta 3389.

**"Sessioni RDS lente"** → Verificare risorse del session host (CPU, RAM), che User Profile Disks non siano pieni, che la rete tra client e server sia adeguata. Ridurre qualità grafica nelle impostazioni del client RDP.

**"RD Gateway connection timeout"** → Verificare certificato SSL valido sul gateway, che le policy CAP e RAP siano configurate correttamente, che la porta 443 sia raggiungibile dall'esterno.

### Print Server

**"Stampante non stampa (job bloccato)"** → Riavviare servizio Spooler (`Restart-Service Spooler`), cancellare job bloccati (`Get-PrintJob -PrinterName "HP" | Remove-PrintJob`), verificare connettività alla stampante (`Test-NetConnection 192.168.10.200 -Port 9100`).

**"Driver stampante causa crash del server"** → Isolare il driver in un processo separato (driver isolation), usare V4 driver se disponibile, disabilitare spooler su server dove non necessario (mitigazione PrintNightmare).

### NPS / RADIUS

**"Autenticazione 802.1X fallisce"** → Verificare shared secret tra NPS e switch/AP, controllare Event Viewer → Network Policy Server per dettagli errore, verificare certificato NPS valido (per PEAP), controllare membership nel gruppo AD specificato nella policy.

### Storage Spaces

**"Virtual Disk degraded"** → Un disco fisico è guasto. Identificare con `Get-PhysicalDisk | Where-Object HealthStatus -ne Healthy`, sostituire il disco, aggiungere al pool, e riparare con `Repair-VirtualDisk`.

---

## FAQ

**D: Posso installare più ruoli sullo stesso server?**
R: Tecnicamente sì, ma non è raccomandato. In produzione, limitare a 1-2 ruoli per server. Domain Controller non deve ospitare altri ruoli applicativi. Le eccezioni accettabili sono DNS su DC (strettamente integrati) e DHCP+DNS su un server non-DC.

**D: Server Core supporta tutti i ruoli?**
R: Quasi tutti. Le eccezioni principali sono i ruoli che richiedono GUI per funzionare (es. RDS Session Host con desktop completo per utenti). Server Core è l'opzione raccomandata per DNS, DHCP, File Server, Hyper-V, DC.

**D: Qual è la differenza tra Standard e Datacenter a livello di funzionalità?**
R: Datacenter aggiunge: VM illimitate, Storage Spaces Direct (S2D), Software-Defined Networking (SDN), Shielded VMs, Host Guardian Service, Network Controller. Standard è limitato a 2 VM per licenza e non ha queste feature. In ambiente con alta virtualizzazione, Datacenter costa meno per VM.

**D: Come scegliere tra User CAL e Device CAL?**
R: Se gli utenti accedono da più dispositivi (PC ufficio + laptop + tablet), convengono User CAL. Se i dispositivi sono condivisi (kiosk, postazioni turno), convengono Device CAL. Le due modalità non possono essere mischiate sullo stesso server.

**D: DHCP deve essere autorizzato in AD?**
R: Sì, in un ambiente Active Directory il server DHCP deve essere autorizzato. Questo previene server DHCP rogue che distribuiscono configurazione errata. Un DHCP non autorizzato non risponderà ai client.

**D: Come funziona il DHCP failover?**
R: Due modalità: Hot Standby (un server attivo, l'altro in attesa — per siti piccoli) e Load Balance (entrambi attivi, dividono il carico — per siti grandi). La configurazione viene replicata automaticamente tra i due server.

**D: DFS Namespace vs DFS Replication: qual è la differenza?**
R: DFS Namespace crea un percorso UNC unificato (es. `\\dominio\files`) che mappa a condivisioni su server diversi (trasparenza). DFS Replication replica automaticamente il contenuto tra server (ridondanza). Si possono usare insieme o separatamente.

**D: IIS Application Pool: perché ApplicationPoolIdentity è preferito?**
R: ApplicationPoolIdentity crea un account virtuale unico per ogni pool, con permessi minimi. Questo isola i pool tra loro: se un'applicazione viene compromessa, non può accedere alle risorse di un altro pool. Usare Domain Admin o LocalSystem per un pool è un rischio di sicurezza grave.

**D: WSUS: WID o SQL Server?**
R: WID (Windows Internal Database) è gratuito e sufficiente per ambienti con meno di ~25.000 client. SQL Server è necessario per ambienti più grandi, replica WSUS multi-server, e reporting avanzato. WID non supporta gestione remota del database.

**D: Storage Spaces vs RAID hardware: quando usare cosa?**
R: Storage Spaces è preferibile quando serve flessibilità (espansione, tiering, thin provisioning) e per ambienti S2D. RAID hardware è preferibile per performance I/O pura, compatibilità legacy, e quando il controller RAID offre BBU (Battery Backup Unit) per write-cache.

**D: WDS funziona senza Active Directory?**
R: Sì, WDS può funzionare in modalità standalone senza AD, ma perde la funzionalità di pre-staging dei computer e l'integrazione con le policy di risposta PXE basate su AD. L'autorizzazione automatica via AD non è disponibile.

**D: NPS: posso usare un unico server NPS per WiFi e VPN?**
R: Sì, un singolo NPS può gestire multiple Network Policies per scenari diversi (WiFi 802.1X, VPN, wired 802.1X). Ogni policy ha condizioni specifiche che determinano quale si applica. Per alta disponibilità, configurare due NPS con la stessa configurazione.

**D: Come migrare un ruolo da un server a un altro?**
R: Dipende dal ruolo. DNS AD-integrated: installare DNS sul nuovo server, la zona si replica automaticamente. DHCP: export/import con `Export-DhcpServer` / `Import-DhcpServer`. IIS: Web Deploy o export/import manuale. File Server: robocopy preservando ACL (`robocopy /COPYALL /MIR`). WSUS: export/import database. Print Server: export/import via Print Management Console.

**D: Nano Server è morto?**
R: No, ma è cambiato drasticamente. Da Server 2019, Nano Server esiste solo come immagine base per container Windows. Non è più un'opzione di installazione standalone. Per server leggeri senza GUI, usare Server Core.

**D: Come verificare che tutti i server siano aggiornati?**
R: Da WSUS Console → Reports → Computer Status (per ambienti WSUS). Da Windows Admin Center → Updates (per gestione moderna). Con PowerShell: `Invoke-Command -ComputerName $servers -ScriptBlock { Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 5 }`.

---

## Checklist di Deployment per Ruolo

### DNS Server

- [ ] Server membro del dominio (se AD-integrated)
- [ ] `Install-WindowsFeature DNS -IncludeManagementTools`
- [ ] Zona forward primaria creata
- [ ] Zona reverse creata
- [ ] Forwarder configurati (verso ISP o resolver pubblico)
- [ ] Aging e scavenging abilitati
- [ ] Record principali creati (A, CNAME, MX, SPF)
- [ ] Firewall: TCP/UDP 53 aperto
- [ ] Test risoluzione da client
- [ ] DNSSEC valutato (se necessario)
- [ ] Monitoraggio configurato
- [ ] Backup zona DNS eseguito

### DHCP Server

- [ ] Server membro del dominio
- [ ] `Install-WindowsFeature DHCP -IncludeManagementTools`
- [ ] Server autorizzato in AD
- [ ] Scope creato con range corretto
- [ ] Esclusioni configurate (IP riservati a server, stampanti, gateway)
- [ ] Opzioni scope: router, DNS, dominio
- [ ] Reservation per dispositivi critici
- [ ] Failover configurato (se necessario)
- [ ] DHCP relay configurato (se client su subnet diverse)
- [ ] MAC filtering valutato
- [ ] Firewall: UDP 67/68 aperto
- [ ] Test assegnazione IP da client
- [ ] Monitoraggio scope utilization

### File Server

- [ ] `Install-WindowsFeature FS-FileServer -IncludeManagementTools`
- [ ] SMBv1 disabilitato
- [ ] SMB Signing abilitato
- [ ] Condivisioni create con permessi appropriati
- [ ] Permessi NTFS configurati (granulari)
- [ ] ABE (Access-Based Enumeration) abilitato
- [ ] FSRM installato (quote, file screening)
- [ ] DFS Namespace configurato (se necessario)
- [ ] DFS-R configurato (se necessario)
- [ ] Backup condivisioni configurato
- [ ] Antivirus configurato (escludere DFS staging area)
- [ ] Monitoraggio spazio disco

### Print Server

- [ ] `Install-WindowsFeature Print-Server -IncludeManagementTools`
- [ ] Driver V4 installati (preferire V4 su V3)
- [ ] Porte TCP/IP create
- [ ] Stampanti aggiunte e condivise
- [ ] Stampanti pubblicate in AD
- [ ] GPO deploy stampanti configurata
- [ ] Spooler disabilitato su server dove non serve
- [ ] PrintNightmare mitigazioni applicate
- [ ] Monitoraggio code di stampa

### IIS Web Server

- [ ] `Install-WindowsFeature Web-Server -IncludeManagementTools`
- [ ] Moduli necessari installati (solo quelli necessari)
- [ ] Moduli non necessari rimossi
- [ ] Application Pool configurati (identity, recycling, limiti)
- [ ] Siti web creati con binding corretti
- [ ] Certificato SSL installato e configurato
- [ ] Redirect HTTP → HTTPS configurato
- [ ] Directory browsing disabilitato
- [ ] Custom error pages configurate
- [ ] Request filtering configurato
- [ ] Security headers aggiunti
- [ ] Logging abilitato
- [ ] Firewall: TCP 80/443 aperto
- [ ] Backup configurazione IIS

### Remote Desktop Services

- [ ] Architettura RDS pianificata (Session Host, Connection Broker, Gateway, Licensing)
- [ ] Session Host installato e configurato
- [ ] Connection Broker installato
- [ ] Collection create con timeout appropriati
- [ ] RemoteApp pubblicati
- [ ] RD Gateway configurato (per accesso esterno)
- [ ] Certificato SSL su Gateway
- [ ] CAP e RAP policy configurate
- [ ] RD Licensing installato e licenze attivate
- [ ] User Profile Disks configurati (se necessario)
- [ ] Firewall: TCP 3389 (interno), TCP 443 (gateway)
- [ ] GPO per client RDP configurata
- [ ] Test connessione da interno e da esterno

### WSUS

- [ ] `Install-WindowsFeature UpdateServices -IncludeManagementTools`
- [ ] Post-installazione completata
- [ ] Prodotti selezionati (solo quelli necessari)
- [ ] Classificazioni selezionate
- [ ] Sincronizzazione automatica configurata
- [ ] Gruppi target creati (Test, Pilota, Produzione)
- [ ] GPO per client configurata
- [ ] Auto-approval rules configurate (solo per Test)
- [ ] Manutenzione schedulata (cleanup, re-indicizzazione)
- [ ] Firewall: TCP 8530/8531 aperto
- [ ] Spazio disco sufficiente per content directory
- [ ] Report configurati

### WDS

- [ ] `Install-WindowsFeature WDS -IncludeManagementTools`
- [ ] Server inizializzato
- [ ] Boot image importata
- [ ] Install images importate
- [ ] Risposta PXE configurata
- [ ] Opzioni DHCP 66/67 configurate (se DHCP su server separato)
- [ ] Unattend file configurati (se automazione necessaria)
- [ ] Pre-stage computer in AD (se AnswerClients: Known)
- [ ] Firewall: UDP 67/68/69, TCP 80/443, porte dinamiche
- [ ] Test PXE boot da client

### NPS / RADIUS

- [ ] `Install-WindowsFeature NPAS -IncludeManagementTools`
- [ ] NPS registrato in AD
- [ ] RADIUS clients aggiunti (switch, AP, VPN)
- [ ] Connection Request Policies configurate
- [ ] Network Policies configurate
- [ ] Metodo autenticazione scelto (PEAP, EAP-TLS)
- [ ] Certificato NPS installato (per PEAP/EAP-TLS)
- [ ] Logging/accounting configurato
- [ ] Firewall: UDP 1812/1813 aperto
- [ ] Test autenticazione da client
- [ ] Backup configurazione NPS eseguito

### Storage Spaces

- [ ] Dischi fisici identificati e disponibili
- [ ] Storage Pool creato
- [ ] Virtual Disk creati con resilienza appropriata
- [ ] Volumi formattati (NTFS o ReFS)
- [ ] Tiered storage configurato (se SSD + HDD)
- [ ] Monitoraggio salute pool e dischi
- [ ] Hot spare disco configurato (se possibile)
- [ ] Backup dati configurato
- [ ] Piano sostituzione disco documentato

### Hyper-V

- [ ] `Install-WindowsFeature Hyper-V -IncludeManagementTools -Restart`
- [ ] Switch virtuali configurati
- [ ] Path predefiniti per VM e VHD configurati
- [ ] Live Migration configurata (se cluster)
- [ ] Replica configurata (se DR necessario)
- [ ] Backup VM configurato
- [ ] Monitoraggio risorse host configurato
- [ ] → Vedi Modulo 23 per checklist approfondita

## Esercizi

1. Confrontare Server Core e Desktop Experience: elencare almeno 5 differenze operative e spiegare in quali scenari Server Core è preferibile.
2. In un lab Windows Server, installare il ruolo DHCP con PowerShell (`Install-WindowsFeature`), configurare uno scope per la rete 10.0.0.0/24, e verificare il lease da un client.
3. Un server DNS non risolve più i nomi interni dopo un aggiornamento. I client ricevono SERVFAIL. Descrivere la procedura di troubleshooting passo-passo.
4. Progettare l'infrastruttura server per una PMI con 200 dipendenti, 2 sedi: definire quali ruoli installare, su quanti server, con quale edizione Windows Server e motivare le scelte di licensing.

## Auto-valutazione

<details><summary>1. Qual è la differenza tra un ruolo e una feature in Windows Server?</summary>
Un ruolo è una funzione primaria del server (DNS, DHCP, AD DS, IIS). Una feature è una funzionalità aggiuntiva che supporta uno o più ruoli (es. .NET Framework, Failover Clustering, RSAT). I ruoli definiscono lo scopo del server, le feature lo completano. Riferimento: sezione «Panoramica».
</details>

<details><summary>2. Quanti core minimi richiede la licenza Windows Server per-core?</summary>
Minimo 16 core per server fisico, venduti in pack da 2 core. Se il server ha meno di 16 core, si pagano comunque 16. Per Datacenter edition, la licenza copre VM illimitate sullo stesso host. Riferimento: sezione «Edizioni Windows Server».
</details>

<details><summary>3. Perché si consiglia massimo 1-2 ruoli per server?</summary>
Separare i ruoli riduce la superficie di attacco, semplifica il troubleshooting, evita conflitti tra servizi, e consente aggiornamenti e riavvii indipendenti. L'eccezione comune è combinare DNS + AD DS sullo stesso DC. Riferimento: sezione «Idee guida».
</details>

<details><summary>4. Cosa offre Windows Admin Center rispetto a Server Manager?</summary>
WAC è un'interfaccia web moderna, supporta gestione remota di Server Core, integra diagnostica avanzata, e funziona cross-browser. Server Manager è la console MMC classica, richiede Desktop Experience sul management server. Riferimento: sezione «Server Manager e Windows Admin Center».
</details>

<details><summary>5. Qual è la differenza tra DFS-N e DFS-R?</summary>
DFS-N (Namespace) crea un percorso UNC virtuale unificato per condivisioni distribuite. DFS-R (Replication) replica il contenuto tra server. Possono funzionare insieme o separatamente. Riferimento: sezione «File Server e DFS».
</details>

<details><summary>6. Come si sceglie tra NTFS e ReFS per un volume Storage Spaces?</summary>
NTFS è maturo, supporta deduplication, quotas, e boot. ReFS offre resilienza superiore con auto-repair, integrità dei dati, e ottimizzazione per workload Hyper-V e backup, ma non supporta boot, compressione, né quotas. Riferimento: sezione «Storage Spaces».
</details>

## Letture primarie consigliate

- Microsoft Learn — Windows Server Roles and Features: <https://learn.microsoft.com/en-us/windows-server/administration/server-core/server-core-roles-and-services> (consultato: 2026-05-23)
- Microsoft Learn — DHCP Server: <https://learn.microsoft.com/en-us/windows-server/networking/technologies/dhcp/dhcp-top> (consultato: 2026-05-23)
- Microsoft Learn — DNS Server: <https://learn.microsoft.com/en-us/windows-server/networking/dns/dns-top> (consultato: 2026-05-23)
- Microsoft Learn — Windows Admin Center: <https://learn.microsoft.com/en-us/windows-server/manage/windows-admin-center/overview> (consultato: 2026-05-23)
- Microsoft Learn — Storage Spaces Direct: <https://learn.microsoft.com/en-us/windows-server/storage/storage-spaces/storage-spaces-direct-overview> (consultato: 2026-05-23)

## Collegamenti incrociati

- [01-active-directory.md](01-active-directory.md) — AD DS come ruolo server principale
- [02-powershell.md](02-powershell.md) — Automazione installazione ruoli
- [23-hyper-v-guida-completa.md](23-hyper-v-guida-completa.md) — Hyper-V approfondito
- [07-storage-windows.md](07-storage-windows.md) — Storage avanzato e ReFS
- [31-iis-web-server-guida-completa.md](31-iis-web-server-guida-completa.md) — IIS approfondito

## Glossario locale

| Termine | Definizione |
|---------|-------------|
| Server Core | Installazione Windows Server senza GUI desktop, solo CLI e PowerShell |
| WAC | Windows Admin Center — interfaccia web per gestione remota di server |
| DHCP Scope | Intervallo di indirizzi IP assegnabili da un server DHCP, con opzioni associate |
| DFS-N | Distributed File System Namespace — percorso UNC virtuale per condivisioni distribuite |
| DFS-R | Distributed File System Replication — replica contenuti tra server member |
| WSUS | Windows Server Update Services — gestione centralizzata aggiornamenti |
| WDS | Windows Deployment Services — deployment OS via rete (PXE boot) |
| NPS | Network Policy Server — implementazione RADIUS Microsoft per 802.1X e VPN |
| Storage Pool | Aggregazione di dischi fisici in un pool logico gestito da Storage Spaces |
| ReFS | Resilient File System — filesystem ottimizzato per integrità dati e grandi volumi |
