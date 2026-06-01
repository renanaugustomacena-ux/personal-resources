# IIS Web Server — Guida Approfondita

> **Modulo del corso:** Windows per ingegneri di sistema
> **Posizione nel percorso:** [00-SYLLABUS.md](00-SYLLABUS.md) → Modulo 31
> **Prerequisiti:** [06-rete-windows.md](06-rete-windows.md) (TCP/IP, DNS), [05-sicurezza-windows.md](05-sicurezza-windows.md) (ACL, permessi), [22-powershell-scripting-avanzato.md](22-powershell-scripting-avanzato.md) (modulo WebAdministration), [11-servizi-certificati.md](11-servizi-certificati.md) (PKI, certificati X.509)
> **Obiettivi di apprendimento:**
> 1. Padroneggiare l'architettura IIS: HTTP.sys, W3SVC, WAS, application pool e pipeline di elaborazione delle richieste
> 2. Configurare application pool con identità, recycling, rapid-fail protection e CPU throttling per isolamento e stabilità
> 3. Implementare security hardening completo: request filtering, security headers, TLS 1.3, HSTS e restrizioni IP
> 4. Configurare ARR come reverse proxy e load balancer con health monitoring e URL affinity
> 5. Ospitare applicazioni ASP.NET Core (in-process/out-of-process) e PHP (FastCGI) su IIS di produzione
> 6. Gestire certificati SSL/TLS con SNI, Centralized Certificate Store e automazione Let's Encrypt
> 7. Implementare logging avanzato (W3C, FREB), compressione HTTP e output caching per performance ottimali
> 8. Progettare architetture IIS ad alta disponibilità con shared configuration, NLB e ARR farm
> **Tempo stimato:** lettura 90 min · lab 180 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-05-23
> **Versioni di riferimento:** IIS 10.0 (Windows Server 2019/2022/2025), URL Rewrite 2.1, ARR 3.0, ASP.NET Core Module v2

> **Modulo 31** · **Aggiornamento:** 2026-05-23

## Mappa concettuale

```
                        ┌──────────────────────┐
                        │      Client HTTP     │
                        │  (Browser, API, CLI) │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │      HTTP.sys        │
                        │   (Kernel-mode)      │
                        │  SSL/TLS termination │
                        │  Response caching    │
                        │  Request queuing     │
                        └──────────┬───────────┘
               ┌───────────────────┼───────────────────┐
               ▼                   ▼                   ▼
        ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
        │   W3SVC     │    │    WAS      │    │   FTP Svc    │
        │ (Config,    │    │ (Lifecycle, │    │ (FTPS, user  │
        │  monitoring)│    │  pooling)   │    │  isolation)  │
        └──────┬──────┘    └──────┬──────┘    └──────────────┘
               └─────────┬────────┘
                         ▼
        ┌────────────────────────────────────────────────┐
        │            Application Pool (w3wp.exe)         │
        │                                                │
        │  ┌──────────┐ ┌──────────┐ ┌────────────────┐ │
        │  │ Modules  │ │ Handlers │ │ Config System  │ │
        │  │(Auth,    │ │(Static,  │ │(applicationHost│ │
        │  │ Compress,│ │ ASPNET,  │ │ .config,       │ │
        │  │ Rewrite, │ │ FastCGI, │ │ web.config)    │ │
        │  │ Logging) │ │ ISAPI)   │ │                │ │
        │  └──────────┘ └──────────┘ └────────────────┘ │
        └───────┬──────────────┬───────────────┬────────┘
                ▼              ▼               ▼
          ┌──────────┐  ┌──────────┐   ┌──────────────┐
          │ ASP.NET  │  │   PHP    │   │   Static     │
          │ Core     │  │ (FastCGI)│   │   Content    │
          │ (ANCM v2)│  │          │   │              │
          └──────────┘  └──────────┘   └──────────────┘
                │              │
     ┌──────────┴──────┐      │
     ▼                 ▼      │
  In-Process      Out-of-     │
  (w3wp.exe)      Process     │
                  (dotnet.exe/│
                   Kestrel)   │
                              │
        ┌─────────────────────┘
        ▼
  ┌───────────────────────────────────────┐
  │        Estensioni / Integrazioni      │
  ├───────────┬───────────┬───────────────┤
  │ URL       │ ARR       │ Compression   │
  │ Rewrite   │ (Reverse  │ (Static +     │
  │ (Inbound/ │  Proxy,   │  Dynamic,     │
  │  Outbound)│  LB, Farm)│  Gzip/Brotli) │
  ├───────────┼───────────┼───────────────┤
  │ SSL/TLS   │ Logging   │ Output Cache  │
  │ (SNI, CCS,│ (W3C,     │ (Kernel-mode +│
  │  HSTS,    │  FREB,    │  User-mode)   │
  │  TLS 1.3) │  Custom)  │               │
  └───────────┴───────────┴───────────────┘
```

## Idee guida
1. **`appcmd` + PowerShell `WebAdministration` module.**
2. **Application Pool isolation + identity separation.**
3. **HSTS + TLS 1.3 mandatory.**
4. **HTTP/2 + HTTP/3 (Win Server 2025).**


## Indice
- [Panoramica](#panoramica)
- [Installazione e Ruoli](#installazione-e-ruoli)
- [Architettura IIS — Deep Dive](#architettura-iis--deep-dive)
- [Application Pool: Identità, Recycling, Limiti](#application-pool-identità-recycling-limiti)
- [Siti, Binding e Virtual Directory](#siti-binding-e-virtual-directory)
- [URL Rewrite](#url-rewrite)
- [Certificati SSL/TLS](#certificati-ssltls)
- [Autenticazione](#autenticazione)
- [Autorizzazione](#autorizzazione)
- [Logging e Diagnostica](#logging-e-diagnostica)
- [Compressione HTTP](#compressione-http)
- [Performance Tuning](#performance-tuning)
- [Security Hardening](#security-hardening)
- [ARR come Reverse Proxy](#arr-come-reverse-proxy)
- [Hosting ASP.NET Core su IIS](#hosting-aspnet-core-su-iis)
- [Hosting PHP su IIS](#hosting-php-su-iis)
- [FTP e FTPS](#ftp-e-ftps)
- [Gestione IIS con PowerShell](#gestione-iis-con-powershell)
- [Alta Disponibilità](#alta-disponibilità)
- [Migrazione IIS](#migrazione-iis)
- [IIS con Windows Containers](#iis-con-windows-containers)
- [Migrazione da Apache/Nginx a IIS](#migrazione-da-apachenginx-a-iis)
- [Best Practices](#best-practices)
- [Troubleshooting — 20+ Problemi Comuni](#troubleshooting--20-problemi-comuni)
- [Deployment Automatizzato con Web Deploy e PowerShell](#deployment-automatizzato-con-web-deploy-e-powershell)
- [Monitoraggio e Alerting in Produzione](#monitoraggio-e-alerting-in-produzione)
- [Certificati Let's Encrypt con Win-ACME](#certificati-lets-encrypt-con-win-acme)
- [Esercizi](#esercizi)
- [Auto-valutazione](#auto-valutazione)
- [Letture primarie consigliate](#letture-primarie-consigliate)
- [Collegamenti incrociati](#collegamenti-incrociati)
- [Glossario locale](#glossario-locale)

---

## Panoramica

Internet Information Services (IIS) è il web server di Microsoft integrato in Windows Server, utilizzato per ospitare siti web, applicazioni web ASP.NET/ASP.NET Core, servizi WCF/Web API e contenuti statici. IIS è un componente fondamentale dell'infrastruttura Microsoft, utilizzato anche internamente da numerosi servizi come Exchange (OWA), SharePoint, WSUS e AD FS.

L'architettura modulare di IIS, introdotta con la versione 7.0, permette di installare solo i componenti necessari, riducendo la superficie di attacco e il consumo di risorse. Ogni funzionalità — autenticazione, compressione, caching, logging, URL rewriting — è implementata come modulo indipendente che può essere aggiunto o rimosso.

IIS 10.0 (incluso in Windows Server 2016/2019/2022 e Windows 10/11) supporta HTTP/2, SNI (Server Name Indication) per HTTPS multi-sito su singolo IP, HSTS, configurazione centralizzata per web farm, e integrazione con Application Request Routing (ARR) per scenari di reverse proxy e load balancing. Questa guida copre ogni aspetto di IIS dalla configurazione base alla security hardening, fornendo le competenze per implementare e gestire web server di produzione robusti e sicuri.

---

## Installazione e Ruoli

```powershell
# Installazione base di IIS
Install-WindowsFeature -Name Web-Server -IncludeManagementTools

# Installazione completa con tutte le funzionalità comuni
$features = @(
    "Web-Server",                    # Web Server (IIS)
    "Web-Common-Http",               # Common HTTP Features
    "Web-Default-Doc",               # Default Document
    "Web-Dir-Browsing",              # Directory Browsing
    "Web-Http-Errors",               # HTTP Errors
    "Web-Static-Content",            # Static Content
    "Web-Http-Redirect",             # HTTP Redirection
    "Web-Health",                    # Health and Diagnostics
    "Web-Http-Logging",              # HTTP Logging
    "Web-Log-Libraries",             # Logging Tools
    "Web-Request-Monitor",           # Request Monitor
    "Web-Http-Tracing",              # Tracing (Failed Request Tracing)
    "Web-Performance",               # Performance
    "Web-Stat-Compression",          # Static Content Compression
    "Web-Dyn-Compression",           # Dynamic Content Compression
    "Web-Security",                  # Security
    "Web-Filtering",                 # Request Filtering
    "Web-Windows-Auth",              # Windows Authentication
    "Web-Basic-Auth",                # Basic Authentication
    "Web-App-Dev",                   # Application Development
    "Web-Net-Ext45",                 # .NET Extensibility 4.5+
    "Web-Asp-Net45",                 # ASP.NET 4.5+
    "Web-ISAPI-Ext",                 # ISAPI Extensions
    "Web-ISAPI-Filter",              # ISAPI Filters
    "Web-WebSockets",               # WebSocket Protocol
    "Web-Mgmt-Tools",               # Management Tools
    "Web-Mgmt-Console",             # IIS Management Console
    "Web-Scripting-Tools",           # IIS Management Scripts and Tools
    "Web-Mgmt-Service"              # Management Service (remote management)
)

Install-WindowsFeature -Name $features -IncludeManagementTools

# Verificare le funzionalità installate
Get-WindowsFeature Web-* | Where-Object Installed | Select-Object Name, InstallState

# Installare i moduli aggiuntivi (URL Rewrite, ARR)
# Scaricare da https://www.iis.net/downloads
# URL Rewrite: iis-url-rewrite-module
# ARR: application-request-routing
```

### Architettura di IIS

```
┌──────────────────────────────────────────────────┐
│                    HTTP.sys                         │
│           (Kernel-mode HTTP listener)              │
│     - Riceve le richieste HTTP/HTTPS               │
│     - Routing a coda richieste del sito            │
│     - Response caching in kernel mode              │
│     - SSL/TLS termination                          │
│     - Bandwidth throttling                          │
├──────────────────────────────────────────────────┤
│            W3SVC (World Wide Web Service)           │
│     - Gestione delle configurazioni                │
│     - Monitoraggio application pool                │
│     - Forwarding richieste ai worker process       │
├──────────────────────────────────────────────────┤
│              WAS (Windows Activation Service)       │
│     - Gestione del ciclo di vita application pool  │
│     - Start/stop worker process                    │
│     - Health monitoring                            │
├─────────────┬────────────┬────────────────────────┤
│ w3wp.exe    │ w3wp.exe   │ w3wp.exe               │
│ (App Pool 1)│ (App Pool 2)│ (App Pool 3)           │
│             │            │                        │
│ Site A      │ Site B     │ Site C                  │
│ ASP.NET     │ PHP        │ Static files            │
│             │            │                        │
│ Modules:    │ Modules:   │ Modules:               │
│ -Auth       │ -Auth      │ -StaticFile            │
│ -Compress   │ -FastCGI   │ -Compress              │
│ -URLRewrite │ -Logging   │ -Logging               │
└─────────────┴────────────┴────────────────────────┘
```

---

## Architettura IIS — Deep Dive

### HTTP.sys — Kernel-Mode HTTP Listener

HTTP.sys è il driver kernel-mode che opera come front-end per tutte le richieste HTTP/HTTPS in IIS. Operando a livello kernel, HTTP.sys fornisce prestazioni significativamente superiori rispetto a un listener user-mode, poiché evita il context switch tra kernel e user space per operazioni frequenti come il caching e il routing delle richieste.

Le responsabilità principali di HTTP.sys includono:

| Funzione | Descrizione |
|----------|-------------|
| **Ricezione richieste** | Ascolta su porte registrate, accetta connessioni TCP, effettua il parsing degli header HTTP |
| **Request queuing** | Ogni application pool ha una coda di richieste kernel-mode; HTTP.sys instrada le richieste alla coda corretta basandosi sull'URL prefix |
| **Kernel-mode response cache** | Le risposte marcate come cacheable vengono servite direttamente dal kernel senza coinvolgere il worker process |
| **SSL/TLS termination** | La crittografia e decrittografia TLS avviene in kernel mode tramite SChannel |
| **Bandwidth throttling** | Limita la banda per sito direttamente a livello kernel |
| **Connection management** | Gestisce keep-alive, connection timeout, HTTP/2 multiplexing |
| **Logging kernel-mode** | Può scrivere log direttamente dal kernel per massima performance |

```powershell
# Verificare le URL registrate in HTTP.sys
netsh http show urlacl

# Verificare la cache kernel-mode di HTTP.sys
netsh http show cachestate

# Verificare i parametri di SSL/TLS
netsh http show sslcert

# Verificare i timeout di HTTP.sys
netsh http show timeout

# Configurare timeout personalizzati
netsh http add timeout timeouttype=idleconnectiontimeout value=120
netsh http add timeout timeouttype=headerwaittimeout value=30
```

### WAS — Windows Process Activation Service

WAS (Windows Process Activation Service) gestisce il ciclo di vita degli application pool e dei worker process. È l'evoluzione del vecchio WWW Service monolitico, progettato per separare la gestione dei processi dalla gestione HTTP.

Responsabilità di WAS:

- **Configuration management:** Legge la configurazione da `applicationHost.config` e la propaga ai worker process
- **Process management:** Avvia, arresta e ricicla i worker process (`w3wp.exe`) secondo le policy configurate
- **Health monitoring:** Monitora la salute dei worker process tramite ping periodici e rapid-fail protection
- **On-demand activation:** Avvia i worker process solo quando arriva la prima richiesta (a meno che non sia configurato `startMode=AlwaysRunning`)
- **Protocol listener adaptation:** Supporta listener non-HTTP (net.tcp, net.pipe, net.msmq) per servizi WCF

```powershell
# Verificare lo stato del servizio WAS
Get-Service WAS, W3SVC | Select-Object Name, Status, StartType

# Riavviare WAS (riavvia tutti gli application pool)
Restart-Service WAS -Force

# Verificare il configuration store
Get-Content "$env:SystemRoot\System32\inetsrv\config\applicationHost.config" |
    Select-String "<applicationPools>" -Context 0,5
```

### W3SVC — World Wide Web Publishing Service

W3SVC lavora in tandem con WAS e HTTP.sys per coordinare il funzionamento del web server:

- **HTTP listener adapter:** Registra le URL in HTTP.sys basandosi sulla configurazione dei siti
- **Performance monitoring:** Espone i contatori di performance per il monitoraggio
- **Configuration change notification:** Notifica WAS quando la configurazione cambia, permettendo la riconfigurazione senza riavvio

### Request Pipeline — Ciclo di Vita della Richiesta

In IIS 7+ la pipeline di elaborazione è composta da moduli nativi e managed che intervengono in sequenza su ogni richiesta. La Integrated Pipeline Mode (raccomandata) unifica la pipeline nativa IIS con la pipeline ASP.NET, permettendo ai moduli managed di intervenire su tutte le richieste, non solo quelle ASP.NET.

```
Richiesta HTTP in arrivo
       │
       ▼
┌─────────────────────────────────────────────────┐
│ HTTP.sys → Routing alla coda dell'App Pool      │
└──────────────────────┬──────────────────────────┘
                       │
       ┌───────────────▼───────────────┐
       │   w3wp.exe (Worker Process)   │
       │                               │
       │   1. BeginRequest             │
       │   2. AuthenticateRequest      │  ← Windows Auth, Basic Auth
       │   3. AuthorizeRequest         │  ← URL Authorization, IP Restrict
       │   4. ResolveRequestCache      │  ← Output Cache lookup
       │   5. MapRequestHandler        │  ← Static File, ASPNET, FastCGI
       │   6. AcquireRequestState      │
       │   7. PreExecuteRequestHandler │  ← URL Rewrite (inbound)
       │   8. ExecuteRequestHandler    │  ← Handler execution
       │   9. UpdateRequestCache       │  ← Output Cache store
       │  10. LogRequest               │  ← W3C Logging
       │  11. EndRequest               │
       │                               │
       │   Outbound: URL Rewrite       │  ← Outbound rules
       │   Outbound: Compression       │  ← Gzip/Brotli
       │   Outbound: Custom Headers    │  ← Security headers
       └───────────────┬───────────────┘
                       │
                       ▼
              Risposta al client
```

```powershell
# Elencare tutti i moduli nativi e managed installati
Get-WebConfiguration "system.webServer/modules" |
    Select-Object -ExpandProperty Collection |
    Format-Table Name, Type -AutoSize

# Elencare gli handler configurati
Get-WebConfiguration "system.webServer/handlers" |
    Select-Object -ExpandProperty Collection |
    Format-Table Name, Path, Verb, Modules -AutoSize

# Verificare la pipeline mode dell'application pool
Get-ItemProperty "IIS:\AppPools\*" managedPipelineMode |
    Format-Table PSChildName, managedPipelineMode
```

### Configuration System — applicationHost.config

IIS utilizza un sistema di configurazione gerarchico basato su file XML. La configurazione è distribuita su tre livelli:

| File | Percorso | Scope |
|------|----------|-------|
| `applicationHost.config` | `%SystemRoot%\System32\inetsrv\config\` | Server-level: siti, app pool, moduli globali |
| `administration.config` | `%SystemRoot%\System32\inetsrv\config\` | Delegazione di configurazione, feature delegation |
| `web.config` | Root del sito / applicazione | Per-sito/per-app: override delle impostazioni delegate |
| `machine.config` | `%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\Config\` | Impostazioni .NET Framework globali |

```powershell
# Backup della configurazione completa di IIS
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupName = "IIS-Backup-$timestamp"
Backup-WebConfiguration -Name $backupName

# Elencare i backup disponibili
Get-WebConfiguration -Filter "/system.applicationHost/configHistory" |
    Select-Object -ExpandProperty Collection

# Ripristinare un backup
Restore-WebConfiguration -Name $backupName

# Verificare la feature delegation
Get-WebConfiguration "/system.webServer/*" -Metadata |
    Where-Object { $_.Metadata.effectiveOverrideMode -eq "Deny" } |
    Select-Object SectionPath, @{N='Override';E={$_.Metadata.effectiveOverrideMode}}
```

---

## Application Pool: Identità, Recycling, Limiti

L'Application Pool è il contenitore di isolamento per le applicazioni web in IIS. Ogni application pool esegue in un processo worker separato (`w3wp.exe`), garantendo che un crash o un problema di sicurezza in un'applicazione non impatti le altre.

### Identità dell'Application Pool

L'identità determina l'account Windows sotto cui il worker process viene eseguito:

| Identità | Uso | Rischio |
|----------|-----|---------|
| ApplicationPoolIdentity | Default, raccomandato. Account virtuale univoco per pool. | Basso |
| NetworkService | Account built-in con accesso di rete. | Medio |
| LocalService | Account built-in senza accesso di rete. | Basso |
| LocalSystem | Massimi privilegi. MAI usare in produzione. | Critico |
| Custom Account | Account di dominio specifico. Per accesso a risorse di rete. | Medio |

```powershell
# Importare il modulo IIS
Import-Module WebAdministration

# Creare un nuovo application pool
New-WebAppPool -Name "AppPool-ContosoWeb"

# Configurare l'identità
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "processModel.identityType" -Value "ApplicationPoolIdentity"

# Per identità personalizzata (account di dominio)
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "processModel.identityType" -Value "SpecificUser"
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "processModel.userName" -Value "CONTOSO\svc-web"
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "processModel.password" -Value "P@ssw0rd"

# Configurare la versione .NET
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "managedRuntimeVersion" -Value "v4.0"
# Per ASP.NET Core / No Managed Code:
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "managedRuntimeVersion" -Value ""

# Configurare la pipeline mode
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "managedPipelineMode" -Value "Integrated"
```

### Recycling

Il recycling riavvia periodicamente il worker process per prevenire memory leak e garantire stabilità.

```powershell
# Configurare il recycling
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "recycling.periodicRestart.time" -Value "29:00:00"  # Ogni 29 ore (evitare pattern prevedibili)

# Recycling basato sulla memoria
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "recycling.periodicRestart.privateMemory" -Value 1048576  # 1 GB in KB

# Configurare la schedule di recycling (orari specifici)
# Rimuovere il recycling time-based e usare schedule
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "recycling.periodicRestart.time" -Value "00:00:00"
Add-WebConfiguration "/system.applicationHost/applicationPools/add[@name='AppPool-ContosoWeb']/recycling/periodicRestart/schedule" -Value @{value="03:00:00"}

# Abilitare il logging degli eventi di recycling
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "recycling.logEventOnRecycle" -Value "Time,Memory,PrivateMemory,Schedule,Requests,IsapiUnhealthy,OnDemand,ConfigChange"
```

### Limiti di CPU e Memoria

```powershell
# Limitare l'uso CPU (percentuale, azione: Throttle o KillW3wp)
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "cpu.limit" -Value 80000  # 80% (espresso in 1/1000 di %)
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "cpu.action" -Value "Throttle"
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "cpu.resetInterval" -Value "00:05:00"

# Configurare il numero massimo di worker process (Web Garden)
# ATTENZIONE: Web Garden causa problemi con session state in-process
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "processModel.maxProcesses" -Value 1  # Default: 1

# Configurare l'idle timeout
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "processModel.idleTimeout" -Value "00:20:00"
# Per applicazioni che non devono mai fermarsi:
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "processModel.idleTimeout" -Value "00:00:00"

# Configurare il rapid fail protection
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "failure.rapidFailProtection" -Value $true
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "failure.rapidFailProtectionInterval" -Value "00:05:00"
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "failure.rapidFailProtectionMaxCrashes" -Value 5

# Configurare l'azione automatica su failure
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "failure.autoShutdownExe" -Value "C:\Scripts\alert-apppool-crash.cmd"
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "failure.autoShutdownParams" -Value "AppPool-ContosoWeb"
```

---

## Siti, Binding e Virtual Directory

```powershell
# Creare un nuovo sito web
New-Website -Name "ContosoWeb" `
    -PhysicalPath "D:\WebSites\ContosoWeb" `
    -ApplicationPool "AppPool-ContosoWeb" `
    -HostHeader "www.contoso.com" `
    -Port 443 `
    -Ssl `
    -SslFlags 1  # 1 = SNI

# Aggiungere un binding aggiuntivo
New-WebBinding -Name "ContosoWeb" -Protocol "http" -HostHeader "www.contoso.com" -Port 80
New-WebBinding -Name "ContosoWeb" -Protocol "https" -HostHeader "api.contoso.com" -Port 443 -SslFlags 1

# Configurare il redirect HTTP → HTTPS
# Richiede URL Rewrite Module installato
$site = "IIS:\Sites\ContosoWeb"
Add-WebConfigurationProperty -PSPath $site `
    -Filter "system.webServer/rewrite/rules" `
    -Name "." -Value @{
        name = "HTTP to HTTPS Redirect"
        patternSyntax = "Wildcard"
        stopProcessing = "true"
        match = @{ url = "*" }
        conditions = @{
            logicalGrouping = "MatchAll"
            trackAllCaptures = "false"
        }
        action = @{
            type = "Redirect"
            url = "https://{HTTP_HOST}/{R:0}"
            redirectType = "Permanent"  # 301
        }
    }

# Creare una virtual directory
New-WebVirtualDirectory -Site "ContosoWeb" -Name "downloads" `
    -PhysicalPath "E:\FileShares\Downloads"

# Creare un'applicazione (sotto-applicazione con proprio web.config)
New-WebApplication -Site "ContosoWeb" -Name "api" `
    -PhysicalPath "D:\WebSites\ContosoAPI" `
    -ApplicationPool "AppPool-ContosoAPI"

# Elencare tutti i siti con binding
Get-Website | ForEach-Object {
    $site = $_
    Get-WebBinding -Name $site.Name | ForEach-Object {
        [PSCustomObject]@{
            SiteName = $site.Name
            State    = $site.State
            Protocol = $_.protocol
            Binding  = $_.bindingInformation
            SslFlags = $_.sslFlags
            AppPool  = $site.applicationPool
        }
    }
} | Format-Table -AutoSize
```

---

## URL Rewrite

Il modulo URL Rewrite è fondamentale per la gestione degli URL, il redirect e la riscrittura delle richieste.

```xml
<!-- web.config esempio con regole URL Rewrite -->
<system.webServer>
    <rewrite>
        <rules>
            <!-- Redirect HTTP a HTTPS -->
            <rule name="HTTPS Redirect" stopProcessing="true">
                <match url="(.*)" />
                <conditions>
                    <add input="{HTTPS}" pattern="^OFF$" />
                </conditions>
                <action type="Redirect" url="https://{HTTP_HOST}/{R:1}"
                        redirectType="Permanent" />
            </rule>

            <!-- Redirect da www a non-www (o viceversa) -->
            <rule name="Canonical Domain" stopProcessing="true">
                <match url="(.*)" />
                <conditions>
                    <add input="{HTTP_HOST}" pattern="^contoso\.com$" />
                </conditions>
                <action type="Redirect" url="https://www.contoso.com/{R:1}"
                        redirectType="Permanent" />
            </rule>

            <!-- URL amichevoli per SPA (Angular/React) -->
            <rule name="SPA Fallback" stopProcessing="true">
                <match url=".*" />
                <conditions logicalGrouping="MatchAll">
                    <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
                    <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
                    <add input="{REQUEST_URI}" pattern="^/api/" negate="true" />
                </conditions>
                <action type="Rewrite" url="/index.html" />
            </rule>

            <!-- Bloccare file sensibili -->
            <rule name="Block Sensitive Files" stopProcessing="true">
                <match url="(web\.config|\.env|\.git|\.svn)" />
                <action type="CustomResponse" statusCode="404" />
            </rule>
        </rules>

        <!-- Outbound rules (modificare le risposte) -->
        <outboundRules>
            <rule name="Remove Server Header">
                <match serverVariable="RESPONSE_SERVER" pattern=".*" />
                <action type="Rewrite" value="" />
            </rule>
        </outboundRules>
    </rewrite>
</system.webServer>
```

### Redirect vs Rewrite — Differenze Chiave

| Aspetto | Redirect | Rewrite |
|---------|----------|---------|
| **Tipo azione** | `Redirect` (301/302/307/308) | `Rewrite` |
| **Lato** | Client-side: il browser riceve la risposta e fa una nuova richiesta | Server-side: IIS modifica l'URL internamente |
| **URL nel browser** | Cambia | Non cambia |
| **SEO** | 301 trasferisce il ranking al nuovo URL | Trasparente ai motori di ricerca |
| **Uso tipico** | HTTP→HTTPS, dominio canonico, URL legacy | Reverse proxy (ARR), SPA fallback, URL amichevoli |
| **Performance** | Round trip aggiuntivo | Nessun round trip aggiuntivo |

### Server Variables e Back References

Le regole URL Rewrite possono utilizzare server variables per condizioni e azioni:

```xml
<!-- Esempi di server variables utili -->
<!--
    {HTTPS}              = ON|OFF
    {HTTP_HOST}          = www.contoso.com
    {SERVER_PORT}        = 443
    {REQUEST_URI}        = /api/v1/users?id=42
    {URL}                = /api/v1/users  (senza query string)
    {QUERY_STRING}       = id=42
    {REMOTE_ADDR}        = 10.0.1.50
    {HTTP_USER_AGENT}    = Mozilla/5.0 ...
    {HTTP_X_FORWARDED_FOR} = IP originale dietro proxy
    {REQUEST_FILENAME}   = D:\WebSites\ContosoWeb\api\v1\users
-->

<!-- Back references: {R:0} = intero match, {R:1} = primo gruppo cattura -->
<!-- Condition back references: {C:0} = intero match condizione, {C:1} = primo gruppo -->

<!-- Esempio: rewrite con condition back reference -->
<rule name="Subdomain Routing" stopProcessing="true">
    <match url="(.*)" />
    <conditions>
        <add input="{HTTP_HOST}" pattern="^([a-z]+)\.contoso\.com$" />
    </conditions>
    <!-- {C:1} = subdomain catturato dalla condizione -->
    <action type="Rewrite" url="/tenants/{C:1}/{R:1}" />
</rule>
```

### Rewrite Maps e Regole Avanzate

Le **Rewrite Maps** sono tabelle di lookup chiave-valore integrate nel modulo URL Rewrite che permettono di gestire migliaia di redirect senza scrivere una regola per ciascuno. Sono fondamentali durante le migrazioni di siti web, il re-branding degli URL e la gestione di vanity URL per campagne marketing.

```xml
<!-- Definizione della Rewrite Map in applicationHost.config o web.config -->
<rewrite>
  <rewriteMaps>
    <rewriteMap name="OldToNewUrls" defaultValue="">
      <add key="/vecchio-prodotto-123" value="/catalogo/prodotto-123" />
      <add key="/chi-siamo-old" value="/azienda/chi-siamo" />
      <add key="/promo-estate-2024" value="/offerte/estate" />
      <!-- Migliaia di entries gestibili tramite importazione da file -->
    </rewriteMap>
  </rewriteMaps>

  <rules>
    <!-- Regola che utilizza la Rewrite Map -->
    <rule name="Redirect da Mappa" stopProcessing="true">
      <match url="(.*)" />
      <conditions>
        <add input="{OldToNewUrls:{REQUEST_URI}}" pattern="(.+)" />
      </conditions>
      <action type="Redirect" url="{C:1}" redirectType="Permanent" />
    </rule>
  </rules>
</rewrite>
```

**Importazione massiva di Rewrite Maps da CSV** — per migrazioni con centinaia o migliaia di URL, è possibile generare la mappa tramite PowerShell:

```powershell
# Importare URL mappings da un file CSV nel formato: OldUrl,NewUrl
$csv = Import-Csv "C:\Migration\url-mappings.csv"
$mapXml = $csv | ForEach-Object {
    "      <add key=`"$($_.OldUrl)`" value=`"$($_.NewUrl)`" />"
}
$mapXml | Out-File "C:\Migration\rewritemap-entries.xml" -Encoding UTF8
# Copiare le entries generate nel blocco <rewriteMap> del web.config
```

**Regole di Outbound Rewrite** — il modulo URL Rewrite non gestisce solo le richieste in ingresso ma può anche riscrivere il corpo delle risposte in uscita. Questo è utile per modificare link assoluti generati dall'applicazione dietro un reverse proxy o per iniettare tag di tracking:

```xml
<outboundRules>
  <rule name="Riscrivi link interni in uscita" preCondition="IsHTML">
    <match filterByTags="A, Area, Base, Form, Frame, Head, IFrame, Img, Input, Link, Script"
           pattern="http://server-interno:8080/(.*)" />
    <action type="Rewrite" value="https://www.contoso.com/{R:1}" />
  </rule>
  <preConditions>
    <preCondition name="IsHTML">
      <add input="{RESPONSE_CONTENT_TYPE}" pattern="^text/html" />
    </preCondition>
  </preConditions>
</outboundRules>
```

**Pattern avanzati con Negative Lookahead** — escludere determinati percorsi dal rewrite senza creare regole di esclusione separate:

```xml
<rule name="SPA Fallback con esclusioni" stopProcessing="true">
  <match url="^(?!api/)(?!static/)(?!\.well-known/)(.*)$" />
  <conditions>
    <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
    <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
  </conditions>
  <action type="Rewrite" url="/index.html" />
</rule>
```

**Custom Rewrite Providers** — per scenari complessi (lookup in database, logica personalizzata), IIS supporta provider custom implementati in .NET che possono essere registrati come fonti di dati per le regole di rewrite. Il provider deve implementare `Microsoft.Web.Iis.Rewrite.IRewriteProvider` e viene registrato in `applicationHost.config`:

```xml
<rewrite>
  <providers>
    <provider name="DbLookupProvider"
              type="ContosoRewrite.DbLookupProvider, ContosoRewrite" />
  </providers>
</rewrite>
```

**Throttling delle regole di rewrite** — quando il numero di regole supera le 50-100, l'impatto sulle performance diventa misurabile. Best practice:

- Usare `stopProcessing="true"` su tutte le regole che non richiedono concatenamento
- Ordinare le regole dalla più frequente alla meno frequente
- Preferire Rewrite Maps a regole individuali per redirect statici
- Usare preConditions per limitare l'esecuzione delle outbound rules ai soli content-type pertinenti
- Monitorare il contatore `\Web Service(_Total)\URL Rewrite Cache Hits/sec` per verificare l'efficacia della cache delle regole

---

## Certificati SSL/TLS

```powershell
# Importare un certificato PFX nello store
$password = ConvertTo-SecureString "CertP@ss!" -AsPlainText -Force
Import-PfxCertificate -FilePath "C:\Certs\contoso.pfx" `
    -CertStoreLocation Cert:\LocalMachine\My `
    -Password $password

# Associare il certificato a un binding HTTPS
$cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object Subject -like "*contoso.com*"
$binding = Get-WebBinding -Name "ContosoWeb" -Protocol "https" -HostHeader "www.contoso.com"
$binding.AddSslCertificate($cert.Thumbprint, "My")

# Oppure con netsh (per binding IP-based)
netsh http add sslcert hostnameport=www.contoso.com:443 `
    certhash=$($cert.Thumbprint) `
    certstorename=MY `
    appid='{4dc3e181-e14b-4a21-b022-59fc669b0914}'

# Verificare i binding SSL
netsh http show sslcert

# Configurare HSTS (HTTP Strict Transport Security)
# IIS 10.0 versione 1709+ supporta HSTS nativo:
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/httpProtocol/customHeaders" `
    -Name "." -Value @{
        name = "Strict-Transport-Security"
        value = "max-age=63072000; includeSubDomains; preload"
    }

# Configurare cipher suite ordinate (TLS 1.2+ con suite forti)
$cipherOrder = @(
    "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"
    "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
    "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384"
    "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256"
    "TLS_DHE_RSA_WITH_AES_256_GCM_SHA384"
    "TLS_DHE_RSA_WITH_AES_128_GCM_SHA256"
)
$cipherString = $cipherOrder -join ","
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Cryptography\Configuration\SSL\00010002" `
    -Name "Functions" -Value $cipherString
```

### Hardening TLS via Registro SChannel

La configurazione TLS in Windows Server avviene a livello di sistema operativo tramite il provider SChannel (Secure Channel), i cui parametri risiedono nel registro di sistema sotto `HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL`. Ogni modifica richiede il riavvio del servizio HTTP o del server.

**Disabilitare protocolli obsoleti (SSL 2.0, SSL 3.0, TLS 1.0, TLS 1.1):**

```powershell
# Funzione per disabilitare un protocollo sia lato Server che Client
function Disable-SChannelProtocol {
    param([string]$Protocol)
    $basePath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\$Protocol"
    foreach ($side in @("Server", "Client")) {
        $path = "$basePath\$side"
        if (-not (Test-Path $path)) {
            New-Item -Path $path -Force | Out-Null
        }
        Set-ItemProperty -Path $path -Name "Enabled" -Value 0 -Type DWord
        Set-ItemProperty -Path $path -Name "DisabledByDefault" -Value 1 -Type DWord
    }
    Write-Host "[OK] $Protocol disabilitato (Server + Client)"
}

# Disabilitare tutti i protocolli legacy
Disable-SChannelProtocol -Protocol "SSL 2.0"
Disable-SChannelProtocol -Protocol "SSL 3.0"
Disable-SChannelProtocol -Protocol "TLS 1.0"
Disable-SChannelProtocol -Protocol "TLS 1.1"

# Abilitare esplicitamente TLS 1.2
$tls12Path = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.2"
foreach ($side in @("Server", "Client")) {
    $path = "$tls12Path\$side"
    if (-not (Test-Path $path)) { New-Item -Path $path -Force | Out-Null }
    Set-ItemProperty -Path $path -Name "Enabled" -Value 1 -Type DWord
    Set-ItemProperty -Path $path -Name "DisabledByDefault" -Value 0 -Type DWord
}
```

**TLS 1.3 su Windows Server 2022/2025** — TLS 1.3 è supportato nativamente a partire da Windows Server 2022 ed è abilitato per default. Non richiede configurazione SChannel aggiuntiva, ma è necessario verificare che le applicazioni (in particolare reverse proxy e middleware) supportino il protocollo. IIS 10.0 versione 1809+ negozia TLS 1.3 automaticamente quando il client lo supporta. Le cipher suite TLS 1.3 (TLS_AES_256_GCM_SHA384, TLS_AES_128_GCM_SHA256, TLS_CHACHA20_POLY1305_SHA256) non sono configurabili tramite l'ordine delle cipher suite tradizionali — vengono sempre preferite quando TLS 1.3 è attivo.

**Disabilitare cipher suite deboli:**

```powershell
# Disabilitare cipher suite con algoritmi obsoleti
$weakCiphers = @(
    "TLS_RSA_WITH_AES_256_GCM_SHA384"       # No forward secrecy (RSA key exchange)
    "TLS_RSA_WITH_AES_128_GCM_SHA256"       # No forward secrecy
    "TLS_RSA_WITH_AES_256_CBC_SHA256"       # CBC mode + no PFS
    "TLS_RSA_WITH_AES_128_CBC_SHA256"       # CBC mode + no PFS
    "TLS_RSA_WITH_3DES_EDE_CBC_SHA"         # 3DES deprecato (Sweet32)
)

foreach ($cipher in $weakCiphers) {
    try {
        Disable-TlsCipherSuite -Name $cipher -ErrorAction Stop
        Write-Host "[OK] Disabilitata: $cipher"
    } catch {
        Write-Host "[SKIP] Non presente: $cipher"
    }
}

# Verificare le cipher suite attive
Get-TlsCipherSuite | Format-Table Name, CipherLength, Exchange, @{
    Name = "PFS"
    Expression = { if ($_.KeyExchangeAlgorithm -match "ECDHE|DHE") { "Si" } else { "No" } }
}
```

**HSTS Preloading** — oltre alla configurazione dell'header HSTS nel web.config, per il preloading è necessario:

1. L'header HSTS deve specificare `max-age` di almeno 31536000 (1 anno)
2. Deve includere `includeSubDomains`
3. Deve includere la direttiva `preload`
4. Il dominio deve essere registrato su hstspreload.org
5. Tutti i sottodomini devono servire contenuto via HTTPS

**Certificate Pinning e Transparency** — IIS 10 su Windows Server 2019+ supporta Certificate Transparency (CT) enforcement. I log di CT verificano che i certificati siano stati pubblicati in log pubblici, prevenendo l'emissione fraudolenta. La configurazione avviene tramite Group Policy: `Computer Configuration → Administrative Templates → Windows Components → Certificate Transparency`.

**OCSP Stapling** — IIS supporta OCSP Stapling nativamente, riducendo la latenza del handshake TLS eliminando la necessità per il client di contattare il server OCSP della CA. Per verificare che sia attivo:

```powershell
# Verificare lo stato OCSP Stapling
netsh http show sslcert
# Cercare "OCSP Stapling Enabled" = true nella risposta

# Forzare il refresh della risposta OCSP cached
certutil -setreg chain\ChainCacheResyncFiletime @now
```

---

## Autenticazione

### Windows Authentication

```powershell
# Abilitare Windows Authentication per un sito
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/authentication/windowsAuthentication" `
    -Name "enabled" -Value $true

# Disabilitare Anonymous Authentication (se si usa Windows Auth)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/authentication/anonymousAuthentication" `
    -Name "enabled" -Value $false

# Configurare i provider di autenticazione (Negotiate = Kerberos + NTLM fallback)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/authentication/windowsAuthentication/providers" `
    -Name "." -Value @{ value = "Negotiate" }
```

### Basic Authentication

```powershell
# Abilitare Basic Authentication (SOLO su HTTPS!)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/authentication/basicAuthentication" `
    -Name "enabled" -Value $true
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/authentication/basicAuthentication" `
    -Name "defaultLogonDomain" -Value "CONTOSO"
```

### Forms Authentication (ASP.NET)

```xml
<!-- web.config per Forms Authentication -->
<system.web>
    <authentication mode="Forms">
        <forms loginUrl="~/Account/Login"
               timeout="30"
               slidingExpiration="true"
               requireSSL="true"
               cookieName=".ContosoAuth"
               protection="All" />
    </authentication>
    <authorization>
        <deny users="?" />
    </authorization>
</system.web>
```

---

## Autorizzazione

```powershell
# Configurare le regole di autorizzazione URL
# Bloccare una directory specifica
Add-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb/admin" `
    -Filter "system.webServer/security/authorization" `
    -Name "." -Value @{
        accessType = "Allow"
        roles = "CONTOSO\GRP-WebAdmins"
    }

Add-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb/admin" `
    -Filter "system.webServer/security/authorization" `
    -Name "." -Value @{
        accessType = "Deny"
        users = "*"
    }

# Request Filtering — bloccare estensioni pericolose
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/requestFiltering/fileExtensions" `
    -Name "." -Value @{
        fileExtension = ".exe"
        allowed = $false
    }

# Limitare la dimensione massima delle richieste (prevenire DoS)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/requestFiltering/requestLimits" `
    -Name "maxAllowedContentLength" -Value 30000000  # 30 MB

# Bloccare URL con doppio encoding (attacco directory traversal)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/requestFiltering" `
    -Name "allowDoubleEscaping" -Value $false

# IP restrictions
Add-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb/admin" `
    -Filter "system.webServer/security/ipSecurity" `
    -Name "." -Value @{
        ipAddress = "10.0.100.0"
        subnetMask = "255.255.255.0"
        allowed = $true
    }
# Deny all others
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb/admin" `
    -Filter "system.webServer/security/ipSecurity" `
    -Name "allowUnlisted" -Value $false
```

---

## Logging e Diagnostica

### W3C Logging

```powershell
# Configurare il logging W3C
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.applicationHost/sites/site[@name='ContosoWeb']/logFile" `
    -Name "logFormat" -Value "W3C"

Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.applicationHost/sites/site[@name='ContosoWeb']/logFile" `
    -Name "directory" -Value "D:\IISLogs\ContosoWeb"

# Abilitare campi aggiuntivi utili
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.applicationHost/sites/site[@name='ContosoWeb']/logFile" `
    -Name "logExtFileFlags" -Value "Date,Time,ClientIP,UserName,ServerIP,Method,UriStem,UriQuery,HttpStatus,Win32Status,BytesSent,BytesRecv,TimeTaken,ServerPort,UserAgent,Referer,HttpSubStatus"

# Configurare la rotazione dei log
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.applicationHost/sites/site[@name='ContosoWeb']/logFile" `
    -Name "period" -Value "Daily"

# Analizzare i log con PowerShell
$logPath = "D:\IISLogs\ContosoWeb\u_ex260412.log"
$entries = Import-Csv $logPath -Delimiter " " -Header @(
    "date","time","s-ip","cs-method","cs-uri-stem","cs-uri-query",
    "s-port","cs-username","c-ip","cs(User-Agent)","cs(Referer)",
    "sc-status","sc-substatus","sc-win32-status","time-taken"
) | Where-Object { $_."date" -notlike "#*" }

# Top 10 URL più lenti
$entries | Sort-Object { [int]$_."time-taken" } -Descending |
    Select-Object -First 10 "cs-uri-stem", "time-taken", "sc-status"

# Errori 500
$entries | Where-Object { $_."sc-status" -eq "500" } |
    Group-Object "cs-uri-stem" | Sort-Object Count -Descending

# Request per IP (detection DoS)
$entries | Group-Object "c-ip" | Sort-Object Count -Descending |
    Select-Object -First 20 Name, Count
```

### Failed Request Tracing (FREB)

```powershell
# Abilitare Failed Request Tracing per un sito
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/tracing/traceFailedRequests" `
    -Name "enabled" -Value $true

# Configurare le regole di tracing
# Tracciare tutte le richieste con status code 500+
Add-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/tracing/traceFailedRequests" `
    -Name "." -Value @{
        path = "*"
    }

# I file FREB vengono generati in:
# C:\inetpub\logs\FailedReqLogFiles\W3SVC[SiteID]\
# Aprire fr000001.xml nel browser per il report dettagliato
```

---

## Compressione HTTP

La compressione riduce significativamente la dimensione delle risposte HTTP, migliorando i tempi di caricamento e riducendo il consumo di banda. IIS supporta due modalità di compressione che si applicano a scenari diversi.

### Compressione Statica vs Dinamica

| Caratteristica | Compressione Statica | Compressione Dinamica |
|----------------|---------------------|-----------------------|
| **Contenuto** | File statici (HTML, CSS, JS, SVG, JSON) | Risposte generate da applicazioni (ASP.NET, PHP) |
| **Cache** | Compressa una volta, cache su disco, servita ripetutamente | Compressa ad ogni richiesta, non cacheable su disco |
| **Impatto CPU** | Minimo (una sola compressione) | Significativo su traffico elevato |
| **Installazione** | `Web-Stat-Compression` | `Web-Dyn-Compression` |
| **Raccomandazione** | Sempre abilitata | Abilitare con cautela su server CPU-bound |

```powershell
# Installare i moduli di compressione
Install-WindowsFeature Web-Stat-Compression, Web-Dyn-Compression

# Configurare la compressione statica
Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.webServer/httpCompression" `
    -Name "staticCompressionEnableCpuUsage" -Value 50    # Disabilita se CPU > 50%
Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.webServer/httpCompression" `
    -Name "staticCompressionDisableCpuUsage" -Value 90   # Riabilita se CPU < 90%

# Configurare la compressione dinamica
Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.webServer/httpCompression" `
    -Name "dynamicCompressionEnableCpuUsage" -Value 50
Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.webServer/httpCompression" `
    -Name "dynamicCompressionDisableCpuUsage" -Value 90

# Configurare la directory per i file compressi
Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.webServer/httpCompression" `
    -Name "directory" -Value "D:\IISTemp\CompressedFiles"

# Configurare il livello di compressione (0-10, default 7 per gzip)
Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.webServer/httpCompression/scheme[@name='gzip']" `
    -Name "staticCompressionLevel" -Value 9    # Max compressione per statici
Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.webServer/httpCompression/scheme[@name='gzip']" `
    -Name "dynamicCompressionLevel" -Value 4   # Bilanciato per dinamici
```

### MIME Types per la Compressione

```xml
<!-- web.config: aggiungere MIME types alla compressione -->
<system.webServer>
    <httpCompression>
        <staticTypes>
            <add mimeType="text/*" enabled="true" />
            <add mimeType="message/*" enabled="true" />
            <add mimeType="application/javascript" enabled="true" />
            <add mimeType="application/json" enabled="true" />
            <add mimeType="application/xml" enabled="true" />
            <add mimeType="application/atom+xml" enabled="true" />
            <add mimeType="application/xaml+xml" enabled="true" />
            <add mimeType="image/svg+xml" enabled="true" />
            <add mimeType="application/font-woff" enabled="true" />
            <add mimeType="application/font-woff2" enabled="true" />
            <!-- NON comprimere formati già compressi -->
            <add mimeType="image/jpeg" enabled="false" />
            <add mimeType="image/png" enabled="false" />
            <add mimeType="image/gif" enabled="false" />
            <add mimeType="application/zip" enabled="false" />
            <add mimeType="video/*" enabled="false" />
        </staticTypes>
        <dynamicTypes>
            <add mimeType="text/*" enabled="true" />
            <add mimeType="application/javascript" enabled="true" />
            <add mimeType="application/json" enabled="true" />
            <add mimeType="application/xml" enabled="true" />
        </dynamicTypes>
    </httpCompression>
</system.webServer>
```

### Brotli Compression (IIS 10 + modulo IIS Compression)

A partire da IIS 10 con il modulo IIS Compression installato separatamente, è possibile abilitare Brotli (br) che offre rapporti di compressione superiori a gzip del 15-25% per contenuti testuali.

```powershell
# Installare IIS Compression (scaricabile da iis.net)
# Verifica: il modulo aggiunge il supporto br nativo

# Verificare gli schemi di compressione disponibili
Get-WebConfiguration "system.webServer/httpCompression/scheme" |
    Select-Object -ExpandProperty Collection |
    Format-Table Name, dll

# Monitorare l'efficacia della compressione
Get-Counter @(
    "\Web Service(_Total)\Total Files Sent"
    "\Web Service(_Total)\Bytes Total/sec"
) -SampleInterval 5 -MaxSamples 3
```

---

## Performance Tuning

```powershell
# Abilitare la compressione statica e dinamica
Set-WebConfigurationProperty -PSPath "IIS:\" `
    -Filter "system.webServer/httpCompression" `
    -Name "directory" -Value "D:\IISTemp\CompressedFiles"

Enable-WebRequestTracing  # Utile per diagnosticare problemi di performance

# Configurare il caching delle risposte statiche
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/staticContent/clientCache" `
    -Name "cacheControlMode" -Value "UseMaxAge"
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/staticContent/clientCache" `
    -Name "cacheControlMaxAge" -Value "30.00:00:00"  # 30 giorni

# Output caching per contenuto dinamico
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/caching" `
    -Name "enabled" -Value $true

# Configurare il connection limit
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.applicationHost/sites/site[@name='ContosoWeb']/limits" `
    -Name "maxConnections" -Value 4294967295  # Max

# Configurare il queue length dell'application pool
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "queueLength" -Value 5000

# Monitorare le performance in tempo reale
Get-Counter @(
    "\Web Service(_Total)\Current Connections"
    "\Web Service(_Total)\Total Method Requests/sec"
    "\Web Service(_Total)\Bytes Total/sec"
    "\ASP.NET Applications(__Total__)\Requests/Sec"
    "\ASP.NET Applications(__Total__)\Request Execution Time"
    "\ASP.NET\Requests Queued"
    "\ASP.NET\Worker Process Restarts"
) -SampleInterval 5 -MaxSamples 10
```

### Output Caching — Kernel-Mode e User-Mode

IIS offre due livelli di caching delle risposte che operano in punti diversi della pipeline: **kernel-mode cache** (gestito da HTTP.sys, nello spazio kernel) e **user-mode cache** (gestito dal worker process w3wp.exe, nello spazio utente). Comprendere la distinzione è critico per ottimizzare le performance.

**Kernel-Mode Cache (HTTP.sys)** — le risposte vengono servite direttamente da HTTP.sys senza alcun coinvolgimento del worker process. Questo è il livello di cache più veloce disponibile perché:

- La risposta non attraversa la pipeline IIS (nessun modulo viene eseguito)
- Non avviene context switch da kernel a user space
- HTTP.sys può servire decine di migliaia di richieste/secondo da cache
- La latenza è nell'ordine dei microsecondi

Tuttavia, il kernel-mode cache ha limitazioni: non supporta risposte con `Set-Cookie`, autenticazione, query string di default (configurabile), o risposte generate da moduli managed che impostano header specifici.

**User-Mode Cache** — le risposte sono cachate nel worker process dopo l'esecuzione parziale della pipeline. È più flessibile del kernel-mode perché supporta variazioni per query string, header personalizzati e contenuto autenticato, ma richiede comunque l'attraversamento della pipeline IIS fino al punto di caching.

```xml
<!-- web.config — Configurazione Output Caching per tipo di contenuto -->
<system.webServer>
  <caching enabled="true" enableKernelCache="true">
    <!-- Cache kernel-mode per contenuto statico con alta frequenza -->
    <profiles>
      <add extension=".css"
           policy="CacheUntilChange"
           kernelCachePolicy="CacheUntilChange"
           location="Any" />
      <add extension=".js"
           policy="CacheUntilChange"
           kernelCachePolicy="CacheUntilChange"
           location="Any" />
      <add extension=".png"
           policy="CacheUntilChange"
           kernelCachePolicy="CacheUntilChange"
           duration="06:00:00" />

      <!-- Cache user-mode per contenuto dinamico con variazione su query string -->
      <add extension=".aspx"
           policy="CacheForTimePeriod"
           kernelCachePolicy="DontCache"
           duration="00:05:00"
           varyByQueryString="id,lang,page" />
    </profiles>
  </caching>
</system.webServer>
```

**Configurazione avanzata del Kernel Cache tramite registro:**

```powershell
# Aumentare la dimensione massima del kernel cache (default 512 MB su sistemi 64-bit)
# UriMaxUriBytes controlla la dimensione massima di un singolo URI cachabile
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\HTTP\Parameters" `
    -Name "UriMaxUriBytes" -Value 262144 -Type DWord  # 256 KB max per URI

# UriScavengerPeriod: intervallo in secondi per la pulizia delle entries scadute
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\HTTP\Parameters" `
    -Name "UriScavengerPeriod" -Value 120 -Type DWord  # Pulizia ogni 2 minuti

# Abilitare il caching delle risposte con query string nel kernel cache
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\HTTP\Parameters" `
    -Name "EnableCacheWithQueryString" -Value 1 -Type DWord
```

**Frequency Hits Threshold** — IIS non inserisce automaticamente ogni risposta nel cache. Esiste una soglia di frequenza (`frequentHitThreshold` e `frequentHitTimePeriod`) che determina quante richieste un URL deve ricevere in un intervallo di tempo prima di essere considerato per il caching:

```xml
<!-- applicationHost.config — sezione serverRuntime -->
<serverRuntime
    frequentHitThreshold="2"
    frequentHitTimePeriod="00:00:10" />
<!-- Una risorsa deve essere richiesta almeno 2 volte in 10 secondi per entrare in cache -->
```

**Monitoraggio del cache IIS:**

```powershell
# Contatori specifici per il kernel-mode cache
Get-Counter @(
    "\HTTP Service Url Cache\Current Cache Memory Usage"
    "\HTTP Service Url Cache\Current Cache URI Count"
    "\HTTP Service Url Cache\Total Cache Hits"
    "\HTTP Service Url Cache\Total Cache Misses"
    "\HTTP Service Url Cache\Cache Hit Rate"
    "\Web Service Cache\Output Cache Current Memory Usage"
    "\Web Service Cache\Output Cache Total Hits"
    "\Web Service Cache\Output Cache Total Misses"
) -SampleInterval 5 -MaxSamples 5

# Calcolare il cache hit ratio
$counters = Get-Counter @(
    "\HTTP Service Url Cache\Total Cache Hits"
    "\HTTP Service Url Cache\Total Cache Misses"
)
$hits = $counters.CounterSamples[0].CookedValue
$misses = $counters.CounterSamples[1].CookedValue
$ratio = if (($hits + $misses) -gt 0) { [math]::Round($hits / ($hits + $misses) * 100, 2) } else { 0 }
Write-Host "Kernel Cache Hit Ratio: $ratio%"
# Target: >80% per contenuto statico, >50% per contenuto dinamico
```

**Dynamic Compression e Output Caching** — l'interazione tra compressione e caching richiede attenzione. Se si utilizza `varyByHeaders="Accept-Encoding"`, IIS mantiene copie separate della risposta per ogni encoding (gzip, br, identity). Questo moltiplica l'uso di memoria del cache ma evita di comprimere la stessa risposta ripetutamente:

```xml
<caching enabled="true" enableKernelCache="true">
  <profiles>
    <add extension=".json"
         policy="CacheForTimePeriod"
         kernelCachePolicy="CacheForTimePeriod"
         duration="00:10:00"
         varyByHeaders="Accept-Encoding" />
  </profiles>
</caching>
```

---

## Security Hardening

```powershell
# Rimuovere l'header Server (nascondere la versione IIS)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/requestFiltering" `
    -Name "removeServerHeader" -Value $true

# Rimuovere l'header X-Powered-By
Remove-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/httpProtocol/customHeaders" `
    -Name "." -AtElement @{name="X-Powered-By"}

# Aggiungere security headers
$securityHeaders = @{
    "X-Content-Type-Options" = "nosniff"
    "X-Frame-Options"        = "SAMEORIGIN"
    "X-XSS-Protection"       = "1; mode=block"
    "Referrer-Policy"         = "strict-origin-when-cross-origin"
    "Content-Security-Policy" = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'self'"
    "Permissions-Policy"      = "camera=(), microphone=(), geolocation=(), payment=()"
    "Strict-Transport-Security" = "max-age=63072000; includeSubDomains; preload"
}

foreach ($header in $securityHeaders.GetEnumerator()) {
    Add-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
        -Filter "system.webServer/httpProtocol/customHeaders" `
        -Name "." -Value @{
            name  = $header.Key
            value = $header.Value
        }
}

# Request Filtering: bloccare verbi HTTP non necessari
$allowedVerbs = @("GET", "POST", "HEAD", "OPTIONS")
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/requestFiltering/verbs" `
    -Name "allowUnlisted" -Value $false

foreach ($verb in $allowedVerbs) {
    Add-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
        -Filter "system.webServer/security/requestFiltering/verbs" `
        -Name "." -Value @{ verb = $verb; allowed = $true }
}

# Rimuovere le funzionalità IIS non utilizzate
$featuresToRemove = @(
    "Web-Dir-Browsing"    # Directory Browsing (rischio information disclosure)
    "Web-DAV-Publishing"  # WebDAV (spesso non necessario)
)
Remove-WindowsFeature -Name $featuresToRemove

# Disabilitare il directory browsing (se la feature non può essere rimossa)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/directoryBrowse" `
    -Name "enabled" -Value $false

# Configurare i permessi sul filesystem
$webRoot = "D:\WebSites\ContosoWeb"
$acl = Get-Acl $webRoot
# Rimuovere permessi ereditati
$acl.SetAccessRuleProtection($true, $false)
# Solo l'app pool identity e gli admin
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
    "IIS AppPool\AppPool-ContosoWeb", "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow")))
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
    "BUILTIN\Administrators", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")))
Set-Acl $webRoot $acl
```

### Dynamic IP Restrictions

Il modulo Dynamic IP Restrictions blocca automaticamente gli IP che generano troppe richieste o connessioni simultanee, proteggendo da attacchi DDoS e brute force.

```powershell
# Installare il modulo Dynamic IP Restrictions
Install-WindowsFeature Web-IP-Security

# Configurare le restrizioni dinamiche
# Bloccare IP con troppe richieste concorrenti
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/dynamicIpSecurity/denyByConcurrentRequests" `
    -Name "enabled" -Value $true
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/dynamicIpSecurity/denyByConcurrentRequests" `
    -Name "maxConcurrentRequests" -Value 20

# Bloccare IP con troppe richieste in un intervallo di tempo
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/dynamicIpSecurity/denyByRequestRate" `
    -Name "enabled" -Value $true
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/dynamicIpSecurity/denyByRequestRate" `
    -Name "maxRequests" -Value 100
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/dynamicIpSecurity/denyByRequestRate" `
    -Name "requestIntervalInMilliseconds" -Value 10000  # 10 secondi

# Configurare il comportamento: Abort (chiude la connessione) o Deny (403)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/dynamicIpSecurity" `
    -Name "denyAction" -Value "Forbidden"  # o "AbortRequest" per chiusura silente

# Abilitare il proxy mode (usa X-Forwarded-For per IP reale dietro LB)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/dynamicIpSecurity" `
    -Name "enableProxyMode" -Value $true

# Logging degli IP bloccati
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/dynamicIpSecurity" `
    -Name "enableLoggingOnlyMode" -Value $false  # $true per solo logging senza blocco
```

### Client Certificate Authentication

Per scenari ad alta sicurezza, IIS supporta l'autenticazione tramite certificati client X.509.

```powershell
# Abilitare l'autenticazione tramite certificati client
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/access" `
    -Name "sslFlags" -Value "Ssl,SslNegotiateCert"
    # SslNegotiateCert = richiede il certificato client
    # SslRequireCert   = il certificato è obbligatorio

# Configurare il mapping certificato → account Windows
# One-to-one mapping (un certificato = un utente specifico)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/security/authentication/iisClientCertificateMappingAuthentication" `
    -Name "enabled" -Value $true
```

---

## ARR come Reverse Proxy

Application Request Routing (ARR) trasforma IIS in un reverse proxy e load balancer, permettendo di distribuire il traffico verso server backend e nascondere l'architettura interna.

```powershell
# Installare ARR (dopo aver scaricato il modulo)
# Richiede anche URL Rewrite Module

# Abilitare ARR come proxy
Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.webServer/proxy" `
    -Name "enabled" -Value $true

# Configurare il timeout del proxy
Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.webServer/proxy" `
    -Name "timeout" -Value "00:02:00"

# Preservare l'host header originale
Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.webServer/proxy" `
    -Name "preserveHostHeader" -Value $true
```

### Reverse Proxy con URL Rewrite

```xml
<!-- web.config per reverse proxy verso backend -->
<system.webServer>
    <rewrite>
        <rules>
            <!-- Proxy /api/* verso il backend API server -->
            <rule name="Reverse Proxy - API" stopProcessing="true">
                <match url="^api/(.*)" />
                <action type="Rewrite" url="http://backend-api:8080/api/{R:1}" />
                <serverVariables>
                    <set name="HTTP_X_FORWARDED_FOR" value="{REMOTE_ADDR}" />
                    <set name="HTTP_X_FORWARDED_PROTO" value="{HTTPS}" />
                    <set name="HTTP_X_FORWARDED_HOST" value="{HTTP_HOST}" />
                </serverVariables>
            </rule>

            <!-- Proxy / verso il frontend -->
            <rule name="Reverse Proxy - Frontend" stopProcessing="true">
                <match url="(.*)" />
                <conditions>
                    <add input="{REQUEST_URI}" pattern="^/api/" negate="true" />
                </conditions>
                <action type="Rewrite" url="http://frontend-web:3000/{R:1}" />
            </rule>
        </rules>
    </rewrite>
</system.webServer>
```

### Server Farm (Load Balancing)

```powershell
# Creare una server farm per load balancing
# (tramite IIS Manager → Server Farms → Create Server Farm)
# oppure via appcmd:

# Aggiungere server alla farm
appcmd set config -section:webFarms /+"[name='BackendFarm']" /commit:apphost
appcmd set config -section:webFarms /+"[name='BackendFarm'].[address='10.0.1.20']" /commit:apphost
appcmd set config -section:webFarms /+"[name='BackendFarm'].[address='10.0.1.21']" /commit:apphost
appcmd set config -section:webFarms /+"[name='BackendFarm'].[address='10.0.1.22']" /commit:apphost

# Configurare l'algoritmo di load balancing
# Opzioni: Weighted round robin, Weighted total traffic, Least current requests, Least response time, Server variable hash, Query string hash
appcmd set config -section:webFarms /[name='BackendFarm'].applicationRequestRouting.loadBalancing.algorithm:"WeightedRoundRobin" /commit:apphost

# Configurare l'health check
appcmd set config -section:webFarms /[name='BackendFarm'].applicationRequestRouting.protocol.healthCheck.url:"http://backend/health" /commit:apphost
appcmd set config -section:webFarms /[name='BackendFarm'].applicationRequestRouting.protocol.healthCheck.interval:"00:00:30" /commit:apphost
appcmd set config -section:webFarms /[name='BackendFarm'].applicationRequestRouting.protocol.healthCheck.responseMatch:"OK" /commit:apphost
```

---

## Hosting ASP.NET Core su IIS

ASP.NET Core su IIS utilizza l'ASP.NET Core Module (ANCM) versione 2, che supporta due modelli di hosting con caratteristiche di performance e isolamento molto diverse.

### In-Process vs Out-of-Process

| Caratteristica | In-Process | Out-of-Process |
|----------------|-----------|----------------|
| **Processo** | L'app gira dentro `w3wp.exe` | L'app gira in `dotnet.exe` (Kestrel), IIS funge da reverse proxy |
| **Performance** | Più veloce (~4x throughput in più) | Overhead del proxy tra IIS e Kestrel |
| **Isolamento** | Un crash dell'app può impattare il worker process | L'app è isolata; IIS resta stabile |
| **Debugging** | Più complesso (attach a w3wp.exe) | Più semplice (attach a dotnet.exe) |
| **Compatibilità** | Solo una app per application pool | Multiple app per pool (ognuna ha il suo Kestrel) |
| **Default** | Sì (dal .NET Core 3.0+) | No (da specificare esplicitamente) |

### Configurazione web.config per ASP.NET Core

```xml
<!-- web.config — In-Process (default, raccomandato per performance) -->
<configuration>
  <location path="." inheritInChildApplications="false">
    <system.webServer>
      <handlers>
        <add name="aspNetCore" path="*" verb="*"
             modules="AspNetCoreModuleV2" resourceType="Unspecified" />
      </handlers>
      <aspNetCore processPath="dotnet"
                  arguments=".\ContosoWeb.dll"
                  stdoutLogEnabled="false"
                  stdoutLogFile=".\logs\stdout"
                  hostingModel="inprocess">
        <environmentVariables>
          <environmentVariable name="ASPNETCORE_ENVIRONMENT" value="Production" />
          <environmentVariable name="DOTNET_ENVIRONMENT" value="Production" />
        </environmentVariables>
      </aspNetCore>
    </system.webServer>
  </location>
</configuration>

<!-- web.config — Out-of-Process -->
<configuration>
  <location path="." inheritInChildApplications="false">
    <system.webServer>
      <handlers>
        <add name="aspNetCore" path="*" verb="*"
             modules="AspNetCoreModuleV2" resourceType="Unspecified" />
      </handlers>
      <aspNetCore processPath="dotnet"
                  arguments=".\ContosoWeb.dll"
                  stdoutLogEnabled="false"
                  stdoutLogFile=".\logs\stdout"
                  hostingModel="outofprocess">
        <environmentVariables>
          <environmentVariable name="ASPNETCORE_ENVIRONMENT" value="Production" />
          <environmentVariable name="ASPNETCORE_FORWARDEDHEADERS_ENABLED" value="true" />
        </environmentVariables>
      </aspNetCore>
    </system.webServer>
  </location>
</configuration>
```

### Deployment ASP.NET Core su IIS

```powershell
# 1. Installare il .NET Hosting Bundle (include ANCM v2)
# Scaricare da https://dotnet.microsoft.com/download/dotnet
# Il Hosting Bundle include: .NET Runtime + ASP.NET Core Runtime + ANCM v2

# 2. Verificare l'installazione di ANCM v2
Get-WebConfiguration "system.webServer/globalModules" |
    Select-Object -ExpandProperty Collection |
    Where-Object Name -like "*AspNetCore*"

# 3. Pubblicare l'applicazione (da ambiente di build)
dotnet publish -c Release -o "C:\Build\Output\ContosoWeb" --self-contained false

# 4. Creare il sito IIS
Import-Module WebAdministration

# Application pool: No Managed Code (ANCM gestisce il runtime)
New-WebAppPool -Name "AppPool-ContosoCore"
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoCore" -Name "managedRuntimeVersion" -Value ""
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoCore" -Name "startMode" -Value "AlwaysRunning"

# Creare il sito
New-Website -Name "ContosoCore" `
    -PhysicalPath "D:\WebSites\ContosoCore" `
    -ApplicationPool "AppPool-ContosoCore" `
    -HostHeader "app.contoso.com" `
    -Port 443 -Ssl -SslFlags 1

# 5. Configurare i permessi
$acl = Get-Acl "D:\WebSites\ContosoCore"
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
    "IIS AppPool\AppPool-ContosoCore", "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow")))
Set-Acl "D:\WebSites\ContosoCore" $acl

# 6. Abilitare stdout logging per troubleshooting (disabilitare dopo)
# Creare la cartella logs
New-Item -Path "D:\WebSites\ContosoCore\logs" -ItemType Directory -Force
# Il logging si abilita impostando stdoutLogEnabled="true" nel web.config

# 7. Application Initialization (pre-warming)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoCore" `
    -Filter "system.webServer/applicationInitialization" `
    -Name "doAppInitAfterRestart" -Value $true
Add-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoCore" `
    -Filter "system.webServer/applicationInitialization" `
    -Name "." -Value @{ initializationPage = "/" }
```

---

## Hosting PHP su IIS

IIS supporta PHP tramite il protocollo FastCGI, che mantiene processi PHP persistenti (anziché avviare un nuovo processo per ogni richiesta come CGI tradizionale), offrendo performance comparabili ad Apache/Nginx.

### Installazione e Configurazione FastCGI

```powershell
# Installare i prerequisiti IIS per PHP
Install-WindowsFeature Web-CGI

# Scaricare PHP per Windows da https://windows.php.net/download/
# Estrarre in C:\PHP (es. PHP 8.3 x64 Non-Thread-Safe per FastCGI)

# Registrare PHP come handler FastCGI
Add-WebConfiguration "system.webServer/fastCgi" -PSPath "MACHINE/WEBROOT/APPHOST" -Value @{
    fullPath          = "C:\PHP\php-cgi.exe"
    maxInstances      = 10
    idleTimeout       = 300
    activityTimeout   = 70
    requestTimeout    = 90
    instanceMaxRequests = 10000
    signalBeforeTerminateSeconds = 0
    protocol          = "NamedPipe"
    flushNamedPipe    = $false
}

# Aggiungere l'handler mapping per i file .php
Add-WebConfiguration "system.webServer/handlers" -PSPath "MACHINE/WEBROOT/APPHOST" -Value @{
    name          = "PHP-FastCGI"
    path          = "*.php"
    verb          = "*"
    modules       = "FastCgiModule"
    scriptProcessor = "C:\PHP\php-cgi.exe"
    resourceType  = "Either"
}

# Aggiungere index.php come default document
Add-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.webServer/defaultDocument/files" `
    -Name "." -Value @{ value = "index.php" }
```

### Configurazione php.ini

```ini
; C:\PHP\php.ini — Impostazioni chiave per IIS in produzione

; Percorsi
extension_dir = "C:\PHP\ext"
upload_tmp_dir = "C:\PHP\temp"
session.save_path = "C:\PHP\temp\sessions"
error_log = "C:\PHP\logs\php-errors.log"

; Sicurezza
expose_php = Off
display_errors = Off
display_startup_errors = Off
log_errors = On
error_reporting = E_ALL & ~E_DEPRECATED & ~E_STRICT

; Limiti risorse
max_execution_time = 60
max_input_time = 60
memory_limit = 256M
post_max_size = 50M
upload_max_filesize = 50M
max_file_uploads = 20

; Sessioni
session.cookie_httponly = 1
session.cookie_secure = 1
session.cookie_samesite = Strict
session.use_strict_mode = 1

; OPcache (raccomandato per produzione)
opcache.enable = 1
opcache.enable_cli = 0
opcache.memory_consumption = 256
opcache.interned_strings_buffer = 16
opcache.max_accelerated_files = 20000
opcache.validate_timestamps = 0      ; Disabilitare in prod (richiede restart dopo deploy)
opcache.save_comments = 1
opcache.revalidate_freq = 0

; WinCache (opzionale, cache oggetti user)
; extension = php_wincache.dll
; wincache.ucenabled = 1
; wincache.ucachesize = 128
```

```powershell
# Verificare la configurazione PHP
& C:\PHP\php-cgi.exe -i | Select-String "Loaded Configuration File|opcache|error_log"

# Monitorare i processi FastCGI
Get-Process php-cgi -ErrorAction SilentlyContinue |
    Select-Object Id, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}}, CPU |
    Format-Table -AutoSize
```

---

## FTP e FTPS

IIS include un servizio FTP integrato per il trasferimento sicuro di file, con supporto per FTPS (FTP over SSL/TLS), isolamento utenti e integrazione con l'autenticazione Windows.

### Installazione e Configurazione del Servizio FTP

```powershell
# Installare il ruolo FTP
Install-WindowsFeature Web-Ftp-Server -IncludeAllSubFeature

# Creare un sito FTP
New-WebFtpSite -Name "ContosoFTP" `
    -PhysicalPath "D:\FTPRoot" `
    -Port 21 `
    -IPAddress "*"

# Configurare l'autenticazione
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoFTP" `
    -Filter "system.ftpServer/security/authentication/basicAuthentication" `
    -Name "enabled" -Value $true
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoFTP" `
    -Filter "system.ftpServer/security/authentication/anonymousAuthentication" `
    -Name "enabled" -Value $false

# Configurare l'autorizzazione
Add-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoFTP" `
    -Filter "system.ftpServer/security/authorization" `
    -Name "." -Value @{
        accessType  = "Allow"
        roles       = "CONTOSO\GRP-FTPUsers"
        permissions = "Read,Write"
    }
```

### FTPS — FTP over SSL/TLS

```powershell
# Associare un certificato SSL al sito FTP
$cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object Subject -like "*ftp.contoso.com*"

Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoFTP" `
    -Filter "system.ftpServer/security/ssl" `
    -Name "serverCertHash" -Value $cert.Thumbprint

# Richiedere SSL per il canale dati e di controllo
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoFTP" `
    -Filter "system.ftpServer/security/ssl" `
    -Name "controlChannelPolicy" -Value "SslRequire"
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoFTP" `
    -Filter "system.ftpServer/security/ssl" `
    -Name "dataChannelPolicy" -Value "SslRequire"

# Disabilitare SSL 3.0 e TLS 1.0/1.1 per il servizio FTP
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoFTP" `
    -Filter "system.ftpServer/security/ssl" `
    -Name "ssl128" -Value $true
```

### User Isolation e Passive Mode

```powershell
# Configurare l'isolamento utenti (ogni utente vede solo la propria cartella)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoFTP" `
    -Filter "system.ftpServer/userIsolation" `
    -Name "mode" -Value "IsolateAllDirectories"

# Struttura cartelle per user isolation:
# D:\FTPRoot\LocalUser\<username>\   → per utenti locali
# D:\FTPRoot\<domain>\<username>\    → per utenti di dominio

# Configurare il passive mode (necessario per client dietro firewall/NAT)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoFTP" `
    -Filter "system.ftpServer/firewallSupport" `
    -Name "lowDataChannelPort" -Value 49152
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoFTP" `
    -Filter "system.ftpServer/firewallSupport" `
    -Name "highDataChannelPort" -Value 49200

# Configurare l'IP esterno (per server dietro NAT/firewall)
Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.ftpServer/firewallSupport" `
    -Name "externalIp4Address" -Value "203.0.113.50"

# Aprire le porte passive sul firewall Windows
New-NetFirewallRule -DisplayName "FTP Passive Mode" `
    -Direction Inbound -Action Allow `
    -Protocol TCP -LocalPort 49152-49200
New-NetFirewallRule -DisplayName "FTP Control" `
    -Direction Inbound -Action Allow `
    -Protocol TCP -LocalPort 21
```

---

## Gestione IIS con PowerShell

### WebAdministration vs IISAdministration

IIS offre due moduli PowerShell con filosofie diverse:

| Caratteristica | `WebAdministration` | `IISAdministration` |
|----------------|--------------------|--------------------|
| **Approccio** | Provider PSDrive (`IIS:\`) | Cmdlet diretti |
| **Disponibilità** | Incluso con IIS | Installare da PowerShell Gallery |
| **Performance** | Più lento (carica intero provider) | Più veloce (accesso diretto API) |
| **Compatibilità** | IIS 7.0+ | IIS 10.0+ |
| **Pipeline** | Basato su percorsi (`IIS:\Sites\...`) | Basato su oggetti |
| **Raccomandazione** | Legacy, ampia documentazione | Preferito per nuovi script |

```powershell
# --- WebAdministration (tradizionale) ---
Import-Module WebAdministration
# Usa provider PSDrive
Get-ChildItem "IIS:\Sites"
Get-ChildItem "IIS:\AppPools"
Set-ItemProperty "IIS:\AppPools\DefaultAppPool" -Name "processModel.idleTimeout" -Value "00:20:00"

# --- IISAdministration (moderno) ---
Install-Module IISAdministration -Scope CurrentUser
Import-Module IISAdministration

# Gestione siti
Get-IISSite
Get-IISSite -Name "ContosoWeb" | Select-Object Name, State, Bindings

# Gestione application pool
Get-IISAppPool
(Get-IISAppPool -Name "AppPool-ContosoWeb").Recycle()

# Gestione configurazione (accesso diretto alla sezione)
$manager = Get-IISServerManager
$config = $manager.GetApplicationHostConfiguration()
$section = $config.GetSection("system.webServer/httpCompression")
$section.GetAttributeValue("directory")
```

### Backup e Restore della Configurazione

```powershell
# Backup completo della configurazione IIS
function Backup-IISConfiguration {
    param(
        [string]$BackupPath = "D:\Backups\IIS",
        [int]$RetentionDays = 30
    )

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupDir = Join-Path $BackupPath $timestamp

    # Creare la directory di backup
    New-Item -Path $backupDir -ItemType Directory -Force | Out-Null

    # 1. Backup della configurazione IIS nativa
    Backup-WebConfiguration -Name "Backup-$timestamp"

    # 2. Copia dei file di configurazione
    $configDir = "$env:SystemRoot\System32\inetsrv\config"
    Copy-Item "$configDir\applicationHost.config" "$backupDir\applicationHost.config"
    Copy-Item "$configDir\administration.config" "$backupDir\administration.config"
    Copy-Item "$configDir\redirection.config" "$backupDir\redirection.config" -ErrorAction SilentlyContinue

    # 3. Export dell'elenco siti e pool
    Get-Website | Export-Clixml "$backupDir\sites.xml"
    Get-ChildItem "IIS:\AppPools" | Export-Clixml "$backupDir\apppools.xml"

    # 4. Raccolta web.config di tutti i siti
    Get-Website | ForEach-Object {
        $webConfig = Join-Path $_.PhysicalPath "web.config"
        if (Test-Path $webConfig) {
            $siteBkp = Join-Path $backupDir "webconfigs\$($_.Name)"
            New-Item -Path $siteBkp -ItemType Directory -Force | Out-Null
            Copy-Item $webConfig "$siteBkp\web.config"
        }
    }

    # 5. Pulizia backup vecchi
    Get-ChildItem $BackupPath -Directory |
        Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-$RetentionDays) } |
        Remove-Item -Recurse -Force

    Write-Output "Backup completato: $backupDir"
}

# Restore della configurazione
function Restore-IISConfiguration {
    param([string]$BackupName)

    # Fermare tutti i siti e pool
    Get-Website | Stop-Website
    Get-ChildItem "IIS:\AppPools" | ForEach-Object { Stop-WebAppPool $_.Name }

    # Ripristinare la configurazione
    Restore-WebConfiguration -Name $BackupName

    # Riavviare IIS
    iisreset /restart

    Write-Output "Restore completato da backup: $BackupName"
}
```

### Scripted Site Deployment

```powershell
# Funzione completa per il deployment di un nuovo sito IIS
function New-IISSiteDeployment {
    param(
        [Parameter(Mandatory)]
        [string]$SiteName,
        [Parameter(Mandatory)]
        [string]$HostHeader,
        [string]$PhysicalPath = "D:\WebSites\$SiteName",
        [string]$CertThumbprint,
        [string]$AppPoolIdentity = "ApplicationPoolIdentity",
        [switch]$EnableCompression,
        [switch]$EnableHSTS
    )

    Import-Module WebAdministration

    $appPoolName = "AppPool-$SiteName"

    # 1. Creare la directory
    New-Item -Path $PhysicalPath -ItemType Directory -Force | Out-Null

    # 2. Creare l'application pool
    New-WebAppPool -Name $appPoolName
    Set-ItemProperty "IIS:\AppPools\$appPoolName" -Name "managedRuntimeVersion" -Value ""
    Set-ItemProperty "IIS:\AppPools\$appPoolName" -Name "processModel.identityType" -Value $AppPoolIdentity
    Set-ItemProperty "IIS:\AppPools\$appPoolName" -Name "processModel.idleTimeout" -Value "00:20:00"
    Set-ItemProperty "IIS:\AppPools\$appPoolName" -Name "recycling.periodicRestart.time" -Value "29:00:00"
    Set-ItemProperty "IIS:\AppPools\$appPoolName" -Name "startMode" -Value "AlwaysRunning"

    # 3. Creare il sito
    if ($CertThumbprint) {
        New-Website -Name $SiteName -PhysicalPath $PhysicalPath `
            -ApplicationPool $appPoolName -HostHeader $HostHeader `
            -Port 443 -Ssl -SslFlags 1
        # Binding HTTP per redirect
        New-WebBinding -Name $SiteName -Protocol "http" -HostHeader $HostHeader -Port 80
    } else {
        New-Website -Name $SiteName -PhysicalPath $PhysicalPath `
            -ApplicationPool $appPoolName -HostHeader $HostHeader -Port 80
    }

    # 4. Assegnare permessi filesystem
    $acl = Get-Acl $PhysicalPath
    $acl.SetAccessRuleProtection($true, $false)
    $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
        "IIS AppPool\$appPoolName", "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow")))
    $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
        "BUILTIN\Administrators", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")))
    Set-Acl $PhysicalPath $acl

    # 5. Security headers
    $headers = @{
        "X-Content-Type-Options"    = "nosniff"
        "X-Frame-Options"           = "SAMEORIGIN"
        "Referrer-Policy"           = "strict-origin-when-cross-origin"
        "Permissions-Policy"        = "camera=(), microphone=(), geolocation=()"
    }
    if ($EnableHSTS) {
        $headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    }
    foreach ($h in $headers.GetEnumerator()) {
        Add-WebConfigurationProperty -PSPath "IIS:\Sites\$SiteName" `
            -Filter "system.webServer/httpProtocol/customHeaders" `
            -Name "." -Value @{ name = $h.Key; value = $h.Value }
    }

    Write-Output "Sito $SiteName creato con successo su $HostHeader"
}
```

---

## Alta Disponibilità

### Shared Configuration

La Shared Configuration permette a più server IIS di condividere la stessa configurazione (`applicationHost.config`), semplificando la gestione delle web farm e garantendo coerenza tra i nodi.

```powershell
# Esportare la configurazione in una share di rete
$exportPath = "\\FileServer\IISSharedConfig"
$password = ConvertTo-SecureString "Sh@redC0nfig!" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("CONTOSO\svc-iis", $password)

# Esportare la configurazione corrente
Export-WebConfiguration -Path $exportPath -Credential $cred

# Abilitare la shared configuration su ogni server IIS della farm
Enable-SharedConfiguration -Path $exportPath `
    -Credential $cred `
    -KeyEncryptionPassword $password

# Verificare lo stato della shared configuration
Get-SharedConfiguration

# Per disabilitare (ritorno a configurazione locale)
Disable-SharedConfiguration
```

### Centralized Certificate Store (CCS)

CCS permette di gestire i certificati SSL/TLS in una posizione centralizzata, condivisa tra tutti i server della farm IIS. I certificati vengono nominati con il nome host (es. `www.contoso.com.pfx`), e IIS seleziona automaticamente il certificato corretto basandosi sul binding SNI.

```powershell
# Installare la feature CCS
Install-WindowsFeature Web-CertProvider

# Abilitare il Centralized Certificate Store
Enable-WebCentralCertProvider -CertStoreLocation "\\FileServer\CertStore" `
    -UserName "CONTOSO\svc-iis" `
    -Password "C3rtSt0re!" `
    -PrivateKeyPassword "PfxP@ss!"

# Creare un binding che usa CCS
New-WebBinding -Name "ContosoWeb" -Protocol "https" -HostHeader "www.contoso.com" `
    -Port 443 -SslFlags 3  # 3 = SNI + CCS

# I certificati nella share devono essere nominati:
# www.contoso.com.pfx
# api.contoso.com.pfx
# *.contoso.com.pfx  (per wildcard)
```

### NLB e ARR Farm — Architettura

```
                    ┌─────────────────────────────────────┐
                    │           DNS Round Robin /          │
                    │           Hardware Load Balancer     │
                    └────────────────┬────────────────────┘
                                     │
                    ┌────────────────▼────────────────────┐
              ┌─────┤     NLB Cluster (o ARR Farm)        ├─────┐
              │     │          VIP: 10.0.1.100             │     │
              │     └─────────────────────────────────────┘     │
              ▼                                                 ▼
    ┌──────────────────┐                            ┌──────────────────┐
    │   IIS Node 1     │                            │   IIS Node 2     │
    │   10.0.1.10      │                            │   10.0.1.11      │
    │                  │     Shared Configuration   │                  │
    │ applicationHost  │◄──────────────────────────►│ applicationHost  │
    │ .config (shared) │     \\FileServer\IISConfig │ .config (shared) │
    │                  │                            │                  │
    │ Certificati CCS  │◄──────────────────────────►│ Certificati CCS  │
    │                  │     \\FileServer\CertStore │                  │
    │                  │                            │                  │
    │ Contenuto web    │◄──────────────────────────►│ Contenuto web    │
    │                  │     DFS-R replication      │                  │
    └──────────────────┘                            └──────────────────┘
```

```powershell
# Configurare NLB (Network Load Balancing)
Install-WindowsFeature NLB -IncludeManagementTools

# Creare un cluster NLB
New-NlbCluster -InterfaceName "Ethernet" -ClusterName "WebFarm" `
    -ClusterPrimaryIP "10.0.1.100" -SubnetMask "255.255.255.0" `
    -OperationMode Multicast

# Aggiungere un nodo al cluster
Add-NlbClusterNode -InterfaceName "Ethernet" -NewNodeName "WEB02" `
    -NewNodeInterface "Ethernet"

# Configurare le porte (solo HTTP/HTTPS)
Add-NlbClusterPortRule -InterfaceName "Ethernet" `
    -StartPort 80 -EndPort 80 -Protocol TCP -Mode Multiple -Affinity Single
Add-NlbClusterPortRule -InterfaceName "Ethernet" `
    -StartPort 443 -EndPort 443 -Protocol TCP -Mode Multiple -Affinity Single

# Verificare lo stato del cluster
Get-NlbCluster | Get-NlbClusterNode | Format-Table Name, State, Priority

# Content Sync con DFS Replication
Install-WindowsFeature FS-DFS-Replication -IncludeManagementTools

# Creare un gruppo di replica DFS per il contenuto web
New-DfsReplicationGroup -GroupName "WebContent"
Add-DfsrMember -GroupName "WebContent" -ComputerName "WEB01","WEB02"
New-DfsReplicatedFolder -GroupName "WebContent" -FolderName "ContosoWeb"
Set-DfsrMembership -GroupName "WebContent" -FolderName "ContosoWeb" `
    -ComputerName "WEB01" -ContentPath "D:\WebSites\ContosoWeb" `
    -PrimaryMember $true
Set-DfsrMembership -GroupName "WebContent" -FolderName "ContosoWeb" `
    -ComputerName "WEB02" -ContentPath "D:\WebSites\ContosoWeb"
Add-DfsrConnection -GroupName "WebContent" `
    -SourceComputerName "WEB01" -DestinationComputerName "WEB02"
```

---

## Migrazione IIS

### Migrazione da IIS 7.x/8.x a IIS 10.0

La migrazione di configurazioni e applicazioni tra versioni di IIS richiede attenzione alla compatibilità dei moduli, ai cambiamenti di schema e alle differenze nelle funzionalità di default.

```powershell
# 1. Inventario della configurazione corrente (sul server sorgente)
function Export-IISInventory {
    param([string]$OutputPath = "C:\Migration\IIS-Inventory")

    New-Item -Path $OutputPath -ItemType Directory -Force | Out-Null

    # Esportare la configurazione completa
    Copy-Item "$env:SystemRoot\System32\inetsrv\config\applicationHost.config" `
        "$OutputPath\applicationHost.config"

    # Esportare l'elenco dei moduli installati
    Get-WebConfiguration "system.webServer/globalModules" |
        Select-Object -ExpandProperty Collection |
        Export-Csv "$OutputPath\modules.csv" -NoTypeInformation

    # Esportare i binding SSL
    netsh http show sslcert > "$OutputPath\sslcert.txt"

    # Esportare l'elenco delle feature installate
    Get-WindowsFeature Web-* | Where-Object Installed |
        Export-Csv "$OutputPath\features.csv" -NoTypeInformation

    # Esportare i certificati
    Get-ChildItem Cert:\LocalMachine\My |
        Select-Object Subject, Thumbprint, NotAfter, Issuer |
        Export-Csv "$OutputPath\certificates.csv" -NoTypeInformation

    # Esportare la lista siti con percorsi
    Get-Website | Select-Object Name, State, PhysicalPath, ApplicationPool,
        @{N='Bindings';E={(Get-WebBinding -Name $_.Name | ForEach-Object { $_.bindingInformation }) -join '; '}} |
        Export-Csv "$OutputPath\sites.csv" -NoTypeInformation

    Write-Output "Inventario esportato in $OutputPath"
}

# 2. Migrazione con Web Deploy (MSDeploy)
# Sul server sorgente: creare pacchetti per ogni sito
Get-Website | ForEach-Object {
    $siteName = $_.Name
    $packagePath = "C:\Migration\Packages\$siteName.zip"
    msdeploy.exe -verb:sync `
        -source:iisApp="$siteName" `
        -dest:package="$packagePath"
    Write-Output "Pacchetto creato: $packagePath"
}

# Sul server destinazione: installare le feature necessarie, poi importare
$features = Import-Csv "C:\Migration\IIS-Inventory\features.csv"
$features | ForEach-Object {
    Install-WindowsFeature -Name $_.Name -ErrorAction SilentlyContinue
}

# Importare i pacchetti dei siti
Get-ChildItem "C:\Migration\Packages\*.zip" | ForEach-Object {
    $siteName = $_.BaseName
    msdeploy.exe -verb:sync `
        -source:package="$($_.FullName)" `
        -dest:iisApp="$siteName"
    Write-Output "Sito importato: $siteName"
}
```

### Problemi di Compatibilità Comuni nella Migrazione

| Problema | IIS Sorgente | Soluzione |
|----------|-------------|-----------|
| Classic Pipeline Mode deprecato | IIS 6/7 | Convertire a Integrated Pipeline; aggiornare `web.config` |
| Moduli ISAPI legacy | IIS 6 | Riscrivere come moduli managed o HTTP modules |
| `metabase.xml` non supportato | IIS 6 | La configurazione migra automaticamente ad `applicationHost.config` con `appcmd migrate config` |
| ASP classico (VBScript) | IIS 6/7/8 | Installare `Web-ASP`; testare compatibilità con il runtime ASP |
| Handler mappings diversi | IIS 7.x | Verificare che tutti gli handler siano registrati nel nuovo server |
| Cipher suite order | IIS 8.x | Riconfigurare con script PowerShell; TLS 1.3 disponibile solo su Server 2022+ |
| URL Rewrite rules | IIS 7/8 | Compatibili; verificare la versione del modulo URL Rewrite |
| .NET Framework 2.0/3.5 | IIS 7 | Installare `.NET Framework 3.5 Features` come feature Windows |

---

## IIS con Windows Containers

Windows Containers permettono di eseguire IIS in ambienti containerizzati, abilitando deployment immutabili, scalabilità orizzontale rapida e consistenza tra ambienti di sviluppo, staging e produzione. A differenza dei container Linux con Nginx/Apache, i container Windows con IIS presentano caratteristiche architetturali specifiche che richiedono conoscenze dedicate.

### Immagini Base Disponibili

Microsoft fornisce diverse immagini base per IIS containerizzato, ciascuna con un diverso compromesso tra dimensione e compatibilità:

| Immagine | Dimensione | Compatibilità | Uso Tipico |
|----------|-----------|---------------|------------|
| `mcr.microsoft.com/windows/servercore/iis` | ~5 GB | Completa — .NET Framework 4.x, moduli nativi, PowerShell | Applicazioni .NET Framework legacy |
| `mcr.microsoft.com/dotnet/aspnet` | ~300 MB | Solo ASP.NET Core — nessun IIS completo | Applicazioni ASP.NET Core |
| `mcr.microsoft.com/windows/servercore` | ~4.5 GB | Base senza IIS — installazione manuale | Configurazioni IIS custom |
| `mcr.microsoft.com/windows/nanoserver` | ~300 MB | Minimale — no PowerShell, no .NET Framework | Microservizi con .NET Core |

**Allineamento versione LTSC** — i container Windows richiedono compatibilità tra la versione dell'host e l'immagine del container. Windows Server 2022 LTSC esegue container basati su LTSC 2022. Windows Server 2025 introduce Hyper-V isolation che rilassa questo vincolo.

### Dockerfile per IIS con ASP.NET Framework

```dockerfile
# escape=`
FROM mcr.microsoft.com/windows/servercore/iis:ltsc2022

# Installare features IIS aggiuntive
RUN powershell -Command `
    Install-WindowsFeature Web-Asp-Net45; `
    Install-WindowsFeature Web-Url-Authorization; `
    Install-WindowsFeature Web-IP-Security; `
    Install-WindowsFeature Web-Dyn-Compression

# Rimuovere il sito Default
RUN powershell -Command Remove-Website -Name 'Default Web Site'

# Creare la directory dell'applicazione
RUN mkdir C:\webapp

# Creare il nuovo sito IIS
RUN powershell -Command `
    New-Website -Name 'ContosoWeb' `
        -PhysicalPath 'C:\webapp' `
        -Port 80 `
        -Force

# Configurare l'Application Pool
RUN powershell -Command `
    Set-ItemProperty 'IIS:\AppPools\ContosoWeb' `
        -Name processModel.identityType -Value 'ApplicationPoolIdentity'; `
    Set-ItemProperty 'IIS:\AppPools\ContosoWeb' `
        -Name recycling.periodicRestart.time -Value '00:00:00'

# Copiare l'applicazione
COPY ./publish/ C:/webapp/

# Configurare health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 `
    CMD powershell -Command `
    try { `
        $response = Invoke-WebRequest -Uri 'http://localhost/health' -UseBasicParsing; `
        if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } `
    } catch { exit 1 }

# ServiceMonitor monitora W3SVC e termina il container se il servizio crasha
ENTRYPOINT ["C:\\ServiceMonitor.exe", "w3svc"]
```

### ServiceMonitor.exe

`ServiceMonitor.exe` è un componente fondamentale per IIS containerizzato. Docker richiede un processo foreground per mantenere vivo il container, ma i servizi Windows (incluso W3SVC) eseguono come servizi background. ServiceMonitor risolve questo problema:

- Esegue come processo foreground (PID 1 nel container)
- Monitora lo stato del servizio W3SVC
- Se W3SVC si arresta, ServiceMonitor termina → il container si ferma → l'orchestratore lo riavvia
- Propaga le variabili d'ambiente del container al processo IIS tramite injection nel Application Pool
- Disponibile su GitHub: `microsoft/IIS.ServiceMonitor`

```powershell
# Alternativa: usare uno script PowerShell come entrypoint per maggiore controllo
# entrypoint.ps1
param()

# Applicare configurazione da variabili d'ambiente
if ($env:DB_CONNECTION_STRING) {
    $webConfig = "C:\webapp\web.config"
    $xml = [xml](Get-Content $webConfig)
    $connStr = $xml.configuration.connectionStrings.add |
        Where-Object { $_.name -eq "DefaultConnection" }
    $connStr.connectionString = $env:DB_CONNECTION_STRING
    $xml.Save($webConfig)
}

# Avviare il monitoraggio del servizio IIS
& C:\ServiceMonitor.exe w3svc
```

### Logging nei Container

Nei container, i log IIS devono essere reindirizzati a stdout per essere raccolti dall'infrastruttura container (Docker, Kubernetes). Le strategie principali:

```powershell
# Opzione 1: Configurare IIS per scrivere su una Named Pipe e reindirizzare a stdout
# Nel Dockerfile:
RUN powershell -Command `
    Set-WebConfigurationProperty -PSPath 'MACHINE/WEBROOT/APPHOST' `
        -Filter 'system.applicationHost/log' `
        -Name 'centralLogFileMode' -Value 'CentralW3C'; `
    Set-WebConfigurationProperty -PSPath 'MACHINE/WEBROOT/APPHOST' `
        -Filter 'system.applicationHost/log/centralW3CLogFile' `
        -Name 'directory' -Value 'C:\inetpub\logs'

# Opzione 2: Tail del log file in background
# Aggiungere al entrypoint.ps1 prima di ServiceMonitor:
Start-Job -ScriptBlock {
    while ($true) {
        $logFile = Get-ChildItem "C:\inetpub\logs\LogFiles\W3SVC*\*.log" |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($logFile) {
            Get-Content $logFile.FullName -Wait -Tail 0
        }
        Start-Sleep -Seconds 5
    }
}
```

### Orchestrazione con Kubernetes

IIS containerizzato può essere orchestrato con Kubernetes utilizzando nodi Windows:

```yaml
# deployment-iis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: contoso-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: contoso-web
  template:
    metadata:
      labels:
        app: contoso-web
    spec:
      nodeSelector:
        kubernetes.io/os: windows
      containers:
      - name: iis
        image: contoso.azurecr.io/contoso-web:v1.2.0
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 15
        readinessProbe:
          httpGet:
            path: /ready
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 5
```

**Considerazioni per Windows Containers in produzione:**

- I container Windows Server Core sono significativamente più grandi rispetto alle immagini Linux (5+ GB vs 100 MB) — multi-stage build e layer caching sono critici
- Il tempo di avvio è maggiore (15-30 secondi vs 1-3 secondi per Linux) — configurare readinessProbe con `initialDelaySeconds` adeguato
- L'isolamento Hyper-V fornisce sicurezza equivalente alle VM tradizionali — usarlo per workload multi-tenant
- Group Managed Service Accounts (gMSA) permettono l'autenticazione Kerberos/Windows integrata nei container
- Windows Server 2025 introduce miglioramenti significativi: immagini Nano Server più piccole, supporto migliorato per process isolation, e compatibilità cross-version

---

## Migrazione da Apache/Nginx a IIS

La migrazione da web server Linux-based (Apache HTTP Server, Nginx) a IIS è un processo frequente in ambienti enterprise che standardizzano su stack Microsoft. Questa sezione copre la mappatura delle configurazioni, la conversione delle regole di rewrite e le differenze architetturali da gestire.

### Mappatura dei Concetti Fondamentali

| Concetto Apache/Nginx | Equivalente IIS | Note |
|----------------------|-----------------|------|
| `VirtualHost` | Sito (Site) con Bindings | Un binding = combinazione IP:porta:hostname |
| `.htaccess` | `web.config` (distribuito) | Il `web.config` è gerarchico e cumulativo |
| `httpd.conf` / `nginx.conf` | `applicationHost.config` | Configurazione globale del server |
| `mod_rewrite` | URL Rewrite Module | Richiede installazione separata del modulo |
| `mod_proxy` / `proxy_pass` | Application Request Routing (ARR) | Modulo separato da installare |
| `mod_ssl` | SChannel + HTTP.sys | La terminazione TLS avviene nel kernel |
| `worker` / `event` MPM | Application Pool (w3wp.exe) | Ogni pool è un processo separato |
| `php-fpm` | FastCGI Handler | IIS usa FastCGI per PHP; configurazione nel `web.config` |
| `.htpasswd` | Windows Authentication / Basic Auth | IIS usa provider di autenticazione modulari |
| `mod_headers` | HTTP Response Headers (modulo nativo) | Configurabile in `web.config` o `applicationHost.config` |
| `mod_security` | Request Filtering + IP Restrictions | Per WAF full: usare Azure WAF o prodotti terzi |
| `location {}` block (Nginx) | `<location>` nel `web.config` | Supporta path-based configuration |

### Conversione di Regole mod_rewrite

Il tool **IIS URL Rewrite** include un importatore integrato per le regole `mod_rewrite` di Apache:

1. Aprire IIS Manager → selezionare il sito → URL Rewrite
2. Pannello azioni → "Import Rules..." (Importa regole)
3. Incollare le regole `.htaccess` o caricare il file
4. L'importatore converte automaticamente la sintassi — verificare i warning per regole non convertibili

**Conversione manuale delle regole più comuni:**

```apache
# Apache .htaccess — Redirect 301
RewriteEngine On
RewriteRule ^old-page$ /new-page [R=301,L]
RewriteCond %{HTTPS} off
RewriteRule (.*) https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
```

Equivalente IIS `web.config`:

```xml
<rewrite>
  <rules>
    <rule name="Redirect Old Page" stopProcessing="true">
      <match url="^old-page$" />
      <action type="Redirect" url="/new-page" redirectType="Permanent" />
    </rule>
    <rule name="Force HTTPS" stopProcessing="true">
      <match url="(.*)" />
      <conditions>
        <add input="{HTTPS}" pattern="^OFF$" />
      </conditions>
      <action type="Redirect" url="https://{HTTP_HOST}/{R:1}" redirectType="Permanent" />
    </rule>
  </rules>
</rewrite>
```

**Conversione Nginx → IIS:**

```nginx
# Nginx — reverse proxy con header forwarding
location /api/ {
    proxy_pass http://backend-cluster:8080/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300s;
}
```

Equivalente IIS con ARR (nel `web.config` del sito frontend):

```xml
<rewrite>
  <rules>
    <rule name="Reverse Proxy to Backend" stopProcessing="true">
      <match url="^api/(.*)" />
      <action type="Rewrite" url="http://backend-cluster:8080/{R:1}" />
      <serverVariables>
        <set name="HTTP_X_FORWARDED_FOR" value="{REMOTE_ADDR}" />
        <set name="HTTP_X_FORWARDED_PROTO" value="{HTTPS}" />
        <set name="HTTP_X_REAL_IP" value="{REMOTE_ADDR}" />
      </serverVariables>
    </rule>
  </rules>
</rewrite>
```

### Migrazione dei Virtual Host

```powershell
# Script PowerShell per creare siti IIS equivalenti a VirtualHost Apache
# Input: array di oggetti con configurazione dei siti da migrare

$sites = @(
    @{
        Name = "contoso-main"
        HostHeader = "www.contoso.com"
        PhysicalPath = "D:\WebSites\ContosoMain"
        CertThumbprint = "ABC123..."
    },
    @{
        Name = "contoso-api"
        HostHeader = "api.contoso.com"
        PhysicalPath = "D:\WebSites\ContosoAPI"
        CertThumbprint = "DEF456..."
    }
)

foreach ($site in $sites) {
    # Creare la directory
    New-Item -Path $site.PhysicalPath -ItemType Directory -Force

    # Creare l'Application Pool dedicato
    New-WebAppPool -Name "Pool-$($site.Name)"
    Set-ItemProperty "IIS:\AppPools\Pool-$($site.Name)" `
        -Name processModel.identityType -Value "ApplicationPoolIdentity"
    Set-ItemProperty "IIS:\AppPools\Pool-$($site.Name)" `
        -Name managedRuntimeVersion -Value ""  # No managed code se non necessario

    # Creare il sito con binding HTTP e HTTPS
    New-Website -Name $site.Name `
        -PhysicalPath $site.PhysicalPath `
        -ApplicationPool "Pool-$($site.Name)" `
        -HostHeader $site.HostHeader `
        -Port 80

    # Aggiungere binding HTTPS con SNI
    New-WebBinding -Name $site.Name `
        -Protocol "https" `
        -Port 443 `
        -HostHeader $site.HostHeader `
        -SslFlags 1  # SNI

    # Associare il certificato
    $binding = Get-WebBinding -Name $site.Name -Protocol "https"
    $binding.AddSslCertificate($site.CertThumbprint, "My")

    Write-Host "[OK] Sito $($site.Name) creato con binding HTTP/HTTPS"
}
```

### Checklist di Migrazione

Pre-migrazione:

- [ ] Inventario completo dei siti, virtual host, alias e redirect
- [ ] Elenco di tutti i moduli Apache/Nginx in uso e i corrispondenti moduli IIS
- [ ] Export delle regole di rewrite in formato testo
- [ ] Backup dei certificati SSL con chiave privata (formato PFX)
- [ ] Documentazione delle configurazioni di autenticazione
- [ ] Elenco delle applicazioni PHP/Python/Node.js con versioni runtime
- [ ] Test di carico baseline sull'ambiente sorgente

Post-migrazione:

- [ ] Tutte le URL rispondono con gli stessi status code (200, 301, 404)
- [ ] I redirect funzionano correttamente (testare con `curl -I -L`)
- [ ] I certificati SSL sono validi e la catena è completa
- [ ] Le performance sono comparabili o migliori (latenza P95, throughput)
- [ ] I log vengono generati nel formato atteso
- [ ] L'autenticazione funziona per tutti gli utenti
- [ ] Le regole di sicurezza (IP filtering, rate limiting) sono attive
- [ ] Il monitoraggio è configurato e riceve metriche dal nuovo server

### Differenze Architetturali da Gestire

**Modello di processo** — Apache con `prefork` MPM crea un processo per richiesta; `event` MPM usa thread. Nginx usa un modello event-driven single-thread. IIS usa un pool di thread nel worker process con I/O asincrono nativo (IOCP). Il modello IIS è più simile a Nginx per efficienza, ma opera su processi multipli (uno per Application Pool).

**Configurazione gerarchica** — Apache processa `.htaccess` per ogni directory nella gerarchia. IIS processa `web.config` in modo simile ma con un modello di ereditarietà più strutturato tramite `<location>` tags in `applicationHost.config`. Il `web.config` nella directory figlia sovrascrive quello della padre per le sezioni non bloccate.

**Moduli** — Apache carica i moduli come shared objects (`.so`), Nginx compila i moduli nel binario (o usa moduli dinamici da Nginx 1.9.11+). IIS distingue tra moduli nativi (DLL C++) e moduli managed (.NET). I moduli nativi vanno registrati in `applicationHost.config`, i moduli managed nel `web.config` dell'applicazione.

**PHP** — Apache usa `mod_php` (in-process) o `php-fpm` (FastCGI). Nginx usa esclusivamente `php-fpm`. IIS usa FastCGI tramite il handler `FastCgiModule`, con configurazione simile a `php-fpm` ma gestita tramite `IIS Manager → FastCGI Settings`. La performance è comparabile quando configurato correttamente con `instanceMaxRequests`, `activityTimeout` e `requestTimeout`.

---

## Best Practices

**Un application pool per sito/applicazione:** Non condividere mai l'application pool tra siti o applicazioni diverse. L'isolamento dei processi protegge dalla propagazione di crash, memory leak e vulnerabilità di sicurezza.

**Usare ApplicationPoolIdentity:** A meno che l'applicazione non necessiti di accesso a risorse di rete specifiche, utilizzare sempre ApplicationPoolIdentity. Non usare mai LocalSystem.

**HTTPS obbligatorio:** Tutti i siti di produzione devono usare HTTPS con TLS 1.2+. Configurare HSTS per prevenire il downgrade a HTTP. Utilizzare certificati da CA pubbliche riconosciute o dalla CA enterprise interna.

**Security headers su tutti i siti:** Implementare i security headers (CSP, X-Frame-Options, X-Content-Type-Options, HSTS, Referrer-Policy, Permissions-Policy) su ogni sito. Sono il costo di implementazione più basso con il beneficio di sicurezza più alto.

**Rimuovere gli header informativi:** Rimuovere Server, X-Powered-By, X-AspNet-Version e qualsiasi altro header che riveli informazioni sull'infrastruttura. La security through obscurity non è una difesa, ma non c'è ragione di facilitare la reconnaissance.

**Log su disco separato:** Mantenere i log IIS su un disco o partizione separata dal sistema operativo e dall'applicazione. Un disco pieno di log non deve mai causare il crash del sistema.

**Monitorare le performance:** Configurare alert per metriche chiave: request queue length, tempo di risposta medio, errori 500, utilizzo CPU/memoria del worker process. Un degradamento graduale delle prestazioni è spesso il primo segnale di un problema.

**Backup della configurazione:** La configurazione di IIS risiede in `%SystemRoot%\System32\inetsrv\config\applicationHost.config`. Eseguire backup prima di ogni modifica e mantenere copie versionizzate.

---

## Troubleshooting — 20+ Problemi Comuni

### Tabella di Riferimento Rapido

| # | Problema | HTTP Status | Causa Principale | Prima Azione |
|---|----------|-------------|------------------|--------------|
| 1 | Internal Server Error | 500.0 | Eccezione non gestita nell'applicazione | FREB + Event Log Application |
| 2 | Configuration Error | 500.19 | `web.config` invalido o permessi mancanti | Validare XML + verificare ACL |
| 3 | Handler non trovato | 500.21 | Modulo mancante o pipeline mode errata | Verificare handler mapping + pipeline mode |
| 4 | App Pool si ferma | 503.0 | Rapid-fail protection attivata | Event Log System → Event ID 5012 |
| 5 | Forbidden | 403.14 | Directory listing disabilitato, no default document | Aggiungere `index.html` o default document |
| 6 | File non trovato | 404.0 | URL errato o file mancante | Verificare percorso fisico + binding |
| 7 | Not Found (estensione) | 404.3 | MIME type non registrato | Aggiungere MIME type in IIS Manager |
| 8 | Request Filtering | 404.5 | URL contiene sequenza bloccata | Verificare `requestFiltering` rules |
| 9 | TLS Handshake Failure | — | Certificato mancante, scaduto o non matching | `netsh http show sslcert` + rinnovo |
| 10 | Slow Response | — | Thread pool esaurito, I/O lento | PerfMon: `Requests Queued` + `time-taken` nei log |
| 11 | Bad Gateway | 502.3 | Backend non raggiungibile (ARR proxy) | Verificare health check + connettività backend |
| 12 | Worker Process Crash | — | Access violation, stack overflow | Procdump + analisi crash dump |
| 13 | Memory Leak | — | Consumo RAM crescente del w3wp.exe | PerfMon: `Private Bytes` + debug managed heap |
| 14 | Kerberos Auth Failure | 401.1 | SPN mancante o duplicato | `setspn -X` + `klist` |
| 15 | Request Too Large | 413 | `maxAllowedContentLength` superato | Aumentare il limite in `requestFiltering` |
| 16 | URL Rewrite Loop | — | Regola rewrite senza condizione di stop | Aggiungere `{HTTPS}` o condizione di uscita |
| 17 | SSL Certificate Mismatch | — | CN del certificato non corrisponde all'host header | Verificare binding SNI + subject del cert |
| 18 | Static File Non Servito | 404.3 | MIME type non configurato per l'estensione | Aggiungere mapping in `staticContent` |
| 19 | WebSocket Failure | — | Modulo WebSocket non installato | `Install-WindowsFeature Web-WebSockets` |
| 20 | HTTP/2 non attivo | — | Binding non HTTPS o Windows < Server 2016 | Verificare binding HTTPS + versione OS |

### Problema: HTTP 500 — Internal Server Error

**Sintomi**: Il sito restituisce errore 500 senza dettagli utili nel browser.

**Causa**: Errore nell'applicazione, nel web.config, nei permessi del filesystem o nella configurazione dell'application pool.

**Soluzione**:

```powershell
# Abilitare errori dettagliati (SOLO in sviluppo/test, MAI in produzione!)
Set-WebConfigurationProperty -PSPath "IIS:\Sites\ContosoWeb" `
    -Filter "system.webServer/httpErrors" `
    -Name "errorMode" -Value "Detailed"

# Verificare l'Event Log per errori specifici
Get-WinEvent -LogName "Application" -MaxEvents 20 |
    Where-Object { $_.ProviderName -like "*IIS*" -or $_.ProviderName -like "*ASP.NET*" } |
    Select-Object TimeCreated, LevelDisplayName, Message | Format-Table -Wrap

# Verificare i log IIS per il substatus code
# 500.0 = errore generico, 500.19 = errore di configurazione, 500.21 = handler non trovato
Get-Content "D:\IISLogs\ContosoWeb\u_ex*.log" -Tail 50 |
    Select-String " 500 "

# Abilitare Failed Request Tracing per dettagli completi
# (vedere sezione Logging)

# Verificare il web.config per errori di sintassi
$webConfig = "D:\WebSites\ContosoWeb\web.config"
try { [xml](Get-Content $webConfig); Write-Output "web.config valido" }
catch { Write-Error "web.config INVALIDO: $_" }

# Verificare i permessi
icacls "D:\WebSites\ContosoWeb"
# L'identità dell'app pool deve avere Read/Execute
```

### Problema: Application Pool Si Ferma Continuamente

**Sintomi**: L'application pool va in stato "Stopped" e il sito diventa inaccessibile. Riavviare l'app pool funziona temporaneamente ma il problema si ripete.

**Causa**: Rapid Fail Protection ha arrestato il pool dopo troppi crash del worker process, memory leak che supera il limite, o l'applicazione fa crash per un'eccezione non gestita.

**Soluzione**:

```powershell
# Verificare lo stato dell'app pool
Get-WebAppPoolState -Name "AppPool-ContosoWeb"

# Verificare gli eventi nel log System
Get-WinEvent -LogName "System" | Where-Object {
    $_.ProviderName -eq "WAS" -and $_.LevelDisplayName -eq "Error"
} | Select-Object -First 10 TimeCreated, Message

# Event ID 5011 = App pool timeout
# Event ID 5012 = App pool disabled by rapid fail protection
# Event ID 5009 = Worker process could not create

# Riavviare l'app pool
Start-WebAppPool -Name "AppPool-ContosoWeb"

# Aumentare la tolleranza del rapid fail protection
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "failure.rapidFailProtectionMaxCrashes" -Value 10

# Verificare il consumo di memoria del worker process
Get-Process w3wp | Select-Object Id,
    @{N='MemoryMB';E={[math]::Round($_.WorkingSet64/1MB)}},
    @{N='AppPool';E={
        $id = $_.Id
        (Get-WmiObject Win32_Process -Filter "ProcessId=$id").CommandLine
    }} | Format-Table -AutoSize

# Abilitare il dump automatico su crash per analisi
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "failure.autoShutdownExe" `
    -Value "C:\Windows\System32\procdump.exe"
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" -Name "failure.autoShutdownParams" `
    -Value "-accepteula -ma %1% D:\Dumps"
```

### Problema: Prestazioni Lente — Request Queuing

**Sintomi**: I tempi di risposta aumentano progressivamente. Il contatore "ASP.NET Requests Queued" mostra valori alti.

**Causa**: Il worker process non riesce a gestire il volume di richieste. Cause: thread pool esaurito, I/O lento (database, filesystem), connessioni esterne bloccanti, o insufficienza di risorse (CPU, memoria).

**Soluzione**:

```powershell
# Verificare la coda
Get-Counter "\ASP.NET\Requests Queued" -SampleInterval 2 -MaxSamples 5

# Verificare i thread disponibili
Get-Counter @(
    "\ASP.NET\Worker Process Running"
    "\.NET CLR LocksAndThreads(_Global_)\# of current logical Threads"
) -SampleInterval 2 -MaxSamples 5

# Verificare se il problema è database/IO
# Analizzare i log IIS per le richieste più lente
# Il campo time-taken mostra millisecondi

# Scalare il numero massimo di connessioni
# In machine.config o web.config:
# <system.web>
#   <processModel maxWorkerThreads="100" maxIoThreads="100" />
# </system.web>

# Considerare l'output caching per contenuti frequenti
# Considerare CDN per risorse statiche
# Considerare load balancing con ARR se singolo server è insufficiente
```

### Problema: HTTP 500.19 — Configuration Error

**Sintomi**: Il sito restituisce errore 500.19 con il messaggio "Cannot read configuration file" o "Config section is not valid".

**Causa**: File `web.config` con sintassi XML invalida, sezione di configurazione bloccata dalla feature delegation, o l'identità dell'application pool non ha permessi di lettura sul file.

**Soluzione**:

```powershell
# Validare la sintassi del web.config
$webConfig = "D:\WebSites\ContosoWeb\web.config"
try { [xml](Get-Content $webConfig); Write-Output "XML valido" }
catch { Write-Error "XML INVALIDO: $_" }

# Verificare i permessi sulla directory e sul web.config
icacls $webConfig
icacls (Split-Path $webConfig)

# Verificare la feature delegation (se la sezione è bloccata)
Get-WebConfiguration "/system.webServer/*" -Metadata |
    Where-Object { $_.Metadata.effectiveOverrideMode -eq "Deny" } |
    Select-Object SectionPath

# Sbloccare una sezione (se necessario)
Set-WebConfiguration "/system.webServer/httpErrors" -Metadata overrideMode -Value Allow `
    -PSPath "MACHINE/WEBROOT/APPHOST"
```

### Problema: HTTP 502.3 — Bad Gateway (ARR Proxy)

**Sintomi**: IIS restituisce 502.3 quando funge da reverse proxy tramite ARR. Il substatus 502.3 indica che il backend non ha risposto in tempo o non è raggiungibile.

**Causa**: Server backend non raggiungibile, timeout della connessione proxy, o errore nel backend che chiude la connessione prematuramente.

**Soluzione**:

```powershell
# Verificare la connettività verso il backend
Test-NetConnection -ComputerName "backend-api" -Port 8080

# Aumentare i timeout del proxy ARR
Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.webServer/proxy" -Name "timeout" -Value "00:05:00"

# Verificare i log del backend per errori
# Controllare che il backend risponda a richieste dirette
Invoke-WebRequest -Uri "http://backend-api:8080/health" -UseBasicParsing

# Verificare le impostazioni della server farm ARR
appcmd list config -section:webFarms

# Verificare lo stato dei nodi nella farm
# IIS Manager → Server Farms → BackendFarm → Monitoring and Management
```

### Problema: Autenticazione Kerberos Fallisce (401.1)

**Sintomi**: Windows Authentication fallisce con errore 401.1 Unauthorized. L'autenticazione funziona con NTLM ma non con Kerberos (Negotiate).

**Causa**: SPN (Service Principal Name) mancante o duplicato per l'account dell'application pool.

**Soluzione**:

```powershell
# Verificare gli SPN registrati
setspn -L "CONTOSO\svc-web"

# Verificare se ci sono SPN duplicati
setspn -X

# Registrare gli SPN corretti
# Per ApplicationPoolIdentity: SPN sulla machine account
setspn -S HTTP/www.contoso.com CONTOSO\WEB-SERVER$
setspn -S HTTP/www CONTOSO\WEB-SERVER$

# Per identità personalizzata: SPN sull'account di servizio
setspn -S HTTP/www.contoso.com CONTOSO\svc-web
setspn -S HTTP/www CONTOSO\svc-web

# Verificare il ticket Kerberos sul client
klist

# Verificare l'autenticazione Kerberos nei log IIS
# Nel campo cs-username: CONTOSO\user = autenticazione riuscita
# Campo vuoto con 401 = fallimento
```

### Problema: Certificato SSL Non Funziona con SNI

**Sintomi**: Il sito HTTPS mostra un errore di certificato (NET::ERR_CERT_COMMON_NAME_INVALID) o usa il certificato sbagliato.

**Causa**: Il binding HTTPS non è configurato con il flag SNI, oppure il certificato non ha il SAN (Subject Alternative Name) corretto.

**Soluzione**:

```powershell
# Verificare i binding HTTPS con i certificati associati
Get-WebBinding -Protocol "https" | ForEach-Object {
    $binding = $_
    $certInfo = netsh http show sslcert hostnameport="$($binding.bindingInformation)" 2>$null
    [PSCustomObject]@{
        Site       = (Get-Website | Where-Object { $_.Bindings.Collection.bindingInformation -contains $binding.bindingInformation }).Name
        Binding    = $binding.bindingInformation
        SslFlags   = $binding.sslFlags
        CertHash   = if ($certInfo) { ($certInfo | Select-String "Certificate Hash").ToString().Trim() } else { "Non trovato" }
    }
} | Format-Table -AutoSize

# Ricreare il binding con SNI abilitato (SslFlags=1)
Remove-WebBinding -Name "ContosoWeb" -Protocol "https" -HostHeader "www.contoso.com"
New-WebBinding -Name "ContosoWeb" -Protocol "https" -HostHeader "www.contoso.com" `
    -Port 443 -SslFlags 1

# Associare il certificato corretto
$cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object Subject -like "*contoso.com*"
$binding = Get-WebBinding -Name "ContosoWeb" -Protocol "https" -HostHeader "www.contoso.com"
$binding.AddSslCertificate($cert.Thumbprint, "My")

# Verificare i SAN del certificato
$cert | Select-Object -ExpandProperty Extensions |
    Where-Object { $_.Oid.FriendlyName -eq "Subject Alternative Name" } |
    ForEach-Object { $_.Format($true) }
```

### Problema: URL Rewrite Loop Infinito

**Sintomi**: Il browser mostra "ERR_TOO_MANY_REDIRECTS". Il sito continua a reindirizzare ciclicamente.

**Causa**: La regola di rewrite HTTP→HTTPS si applica anche alle richieste già HTTPS, creando un ciclo infinito. Comune quando IIS è dietro un load balancer che termina SSL.

**Soluzione**:

```xml
<!-- web.config: correggere il loop di redirect con ARR/LB -->
<system.webServer>
    <rewrite>
        <rules>
            <!-- Redirect HTTP a HTTPS (dietro load balancer) -->
            <rule name="HTTPS Redirect (behind LB)" stopProcessing="true">
                <match url="(.*)" />
                <conditions logicalGrouping="MatchAll">
                    <add input="{HTTPS}" pattern="^OFF$" />
                    <!-- Controllare anche l'header X-Forwarded-Proto -->
                    <add input="{HTTP_X_FORWARDED_PROTO}" pattern="^http$" />
                </conditions>
                <action type="Redirect" url="https://{HTTP_HOST}/{R:1}"
                        redirectType="Permanent" />
            </rule>
        </rules>
    </rewrite>
</system.webServer>
```

```powershell
# Permettere a IIS di leggere l'header X-Forwarded-Proto
# Aggiungere la server variable nelle regole URL Rewrite
Add-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" `
    -Filter "system.webServer/rewrite/allowedServerVariables" `
    -Name "." -Value @{ name = "HTTP_X_FORWARDED_PROTO" }
```

### Problema: Worker Process Crash — Debug con Procdump

**Sintomi**: L'application pool va in stato Stopped ripetutamente. Event Log mostra Event ID 5011 (A process serving application pool crashed).

**Soluzione**:

```powershell
# Configurare la raccolta automatica di crash dump
# 1. Scaricare Procdump da Sysinternals
# 2. Configurare il dump automatico su crash

# Metodo 1: tramite la proprietà failure dell'app pool
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" `
    -Name "failure.autoShutdownExe" -Value "C:\Tools\procdump.exe"
Set-ItemProperty "IIS:\AppPools\AppPool-ContosoWeb" `
    -Name "failure.autoShutdownParams" -Value "-accepteula -ma %1% D:\CrashDumps"

# Metodo 2: Windows Error Reporting (LocalDumps)
New-Item "HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\w3wp.exe" -Force
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\w3wp.exe" `
    -Name "DumpFolder" -Value "D:\CrashDumps" -Type ExpandString
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\w3wp.exe" `
    -Name "DumpType" -Value 2 -Type DWord  # 2 = Full dump
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\w3wp.exe" `
    -Name "DumpCount" -Value 5 -Type DWord

# Analizzare il dump con WinDbg
# windbg -z "D:\CrashDumps\w3wp.exe.1234.dmp"
# .loadby sos clr
# !analyze -v
# !clrstack
```

---

## Deployment Automatizzato con Web Deploy e PowerShell

### Web Deploy (MSDeploy)

Web Deploy è lo strumento standard di Microsoft per il deployment automatizzato di applicazioni web su IIS. Supporta la sincronizzazione di contenuti, configurazioni, database e certificati tra ambienti diversi, con supporto per trasformazioni di configurazione (web.config transforms) per gestire le differenze tra sviluppo, staging e produzione.

```powershell
# Installare Web Deploy sul server
# Scaricare da https://www.iis.net/downloads/microsoft/web-deploy
# oppure via Web Platform Installer

# Abilitare il Management Service per deployment remoto
Set-Service WMSVC -StartupType Automatic
Start-Service WMSVC

# Configurare il Management Service per accettare connessioni remote
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\WebManagement\Server" `
    -Name "EnableRemoteManagement" -Value 1

# Deployment da riga di comando con MSDeploy
# Sincronizzare una cartella locale con un sito IIS remoto
msdeploy.exe -verb:sync `
    -source:contentPath="C:\Build\Output\ContosoWeb" `
    -dest:contentPath="ContosoWeb",computerName="https://webserver01:8172/msdeploy.axd",userName="deployer",password="D3pl0y!",authType="basic" `
    -allowUntrusted `
    -enableRule:DoNotDeleteRule  # Non eliminare file non presenti nel source

# Creare un pacchetto di deployment
msdeploy.exe -verb:sync `
    -source:iisApp="ContosoWeb" `
    -dest:package="C:\Packages\ContosoWeb.zip"

# Deployment di un pacchetto
msdeploy.exe -verb:sync `
    -source:package="C:\Packages\ContosoWeb.zip" `
    -dest:iisApp="ContosoWeb"

# Script PowerShell per deployment zero-downtime
function Deploy-WebApplication {
    param(
        [string]$SiteName,
        [string]$SourcePath,
        [string]$BackupPath = "D:\Backups\WebDeploy"
    )

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

    # 1. Backup del sito corrente
    $backupFile = Join-Path $BackupPath "$SiteName-$timestamp.zip"
    Write-Output "Backup in corso: $backupFile"
    msdeploy.exe -verb:sync -source:iisApp="$SiteName" -dest:package="$backupFile"

    # 2. Fermare il sito (opzionale per zero-downtime con ARR)
    Stop-Website -Name $SiteName

    # 3. Deploy del nuovo contenuto
    Write-Output "Deployment in corso..."
    msdeploy.exe -verb:sync `
        -source:contentPath="$SourcePath" `
        -dest:contentPath="$SiteName" `
        -enableRule:DoNotDeleteRule

    # 4. Verificare il web.config
    $webConfig = Join-Path (Get-Website -Name $SiteName).PhysicalPath "web.config"
    try {
        [xml](Get-Content $webConfig)
        Write-Output "web.config valido"
    }
    catch {
        Write-Error "web.config INVALIDO! Rollback in corso..."
        msdeploy.exe -verb:sync -source:package="$backupFile" -dest:iisApp="$SiteName"
        Start-Website -Name $SiteName
        return
    }

    # 5. Riavviare il sito
    Start-Website -Name $SiteName

    # 6. Health check
    Start-Sleep -Seconds 5
    try {
        $response = Invoke-WebRequest "https://localhost/$SiteName/health" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Output "Deployment completato con successo!"
        } else {
            Write-Warning "Health check ha restituito status $($response.StatusCode)"
        }
    }
    catch {
        Write-Error "Health check fallito: $_"
        Write-Output "Considerare rollback manuale da: $backupFile"
    }
}
```

### Configurazione IIS tramite PowerShell DSC

```powershell
# Desired State Configuration per IIS
Configuration IISWebServer {
    param (
        [string]$SiteName = "ContosoWeb",
        [string]$PhysicalPath = "D:\WebSites\ContosoWeb",
        [string]$AppPoolName = "AppPool-ContosoWeb",
        [int]$HttpsPort = 443,
        [string]$HostHeader = "www.contoso.com"
    )

    Import-DscResource -ModuleName PSDesiredStateConfiguration
    Import-DscResource -ModuleName xWebAdministration

    Node localhost {
        # Garantire che IIS sia installato
        WindowsFeature IIS {
            Ensure = "Present"
            Name   = "Web-Server"
        }

        WindowsFeature AspNet45 {
            Ensure    = "Present"
            Name      = "Web-Asp-Net45"
            DependsOn = "[WindowsFeature]IIS"
        }

        WindowsFeature StaticCompression {
            Ensure    = "Present"
            Name      = "Web-Stat-Compression"
            DependsOn = "[WindowsFeature]IIS"
        }

        WindowsFeature DynCompression {
            Ensure    = "Present"
            Name      = "Web-Dyn-Compression"
            DependsOn = "[WindowsFeature]IIS"
        }

        # Creare la cartella del sito
        File WebSiteFolder {
            Ensure          = "Present"
            Type            = "Directory"
            DestinationPath = $PhysicalPath
        }

        # Configurare l'Application Pool
        xWebAppPool ContosoAppPool {
            Ensure                  = "Present"
            Name                    = $AppPoolName
            State                   = "Started"
            managedRuntimeVersion   = "v4.0"
            managedPipelineMode     = "Integrated"
            identityType            = "ApplicationPoolIdentity"
            idleTimeout             = "00:20:00"
            maxProcesses            = 1
            rapidFailProtection     = $true
            DependsOn               = "[WindowsFeature]IIS"
        }

        # Configurare il sito web
        xWebsite ContosoWebSite {
            Ensure          = "Present"
            Name            = $SiteName
            PhysicalPath    = $PhysicalPath
            ApplicationPool = $AppPoolName
            State           = "Started"
            BindingInfo     = @(
                MSFT_xWebBindingInformation {
                    Protocol  = "https"
                    Port      = $HttpsPort
                    HostName  = $HostHeader
                    CertificateStoreName = "My"
                    SslFlags  = "1"  # SNI
                }
            )
            DependsOn       = "[xWebAppPool]ContosoAppPool", "[File]WebSiteFolder"
        }

        # Rimuovere il Default Web Site
        xWebsite DefaultSite {
            Ensure = "Absent"
            Name   = "Default Web Site"
        }
    }
}
```

---

## Monitoraggio e Alerting in Produzione

### Dashboard di Monitoraggio IIS

```powershell
function Get-IISHealthDashboard {
    <#
    .SYNOPSIS
        Genera un dashboard di salute per tutti i siti IIS sul server.
    .DESCRIPTION
        Raccoglie metriche in tempo reale su performance, errori,
        stato dei pool e connessioni attive.
    #>
    param (
        [int]$SampleSeconds = 10
    )

    Import-Module WebAdministration

    # Stato di tutti i siti
    Write-Output "`n=== STATO SITI IIS ==="
    Get-Website | ForEach-Object {
        $bindings = (Get-WebBinding -Name $_.Name | ForEach-Object { $_.bindingInformation }) -join "; "
        [PSCustomObject]@{
            Nome     = $_.Name
            Stato    = $_.State
            AppPool  = $_.applicationPool
            Bindings = $bindings
        }
    } | Format-Table -AutoSize

    # Stato degli Application Pool
    Write-Output "`n=== STATO APPLICATION POOL ==="
    Get-ChildItem "IIS:\AppPools" | ForEach-Object {
        $pool = $_
        $workerProcess = Get-ChildItem "IIS:\AppPools\$($pool.Name)\WorkerProcesses" -ErrorAction SilentlyContinue
        [PSCustomObject]@{
            Nome     = $pool.Name
            Stato    = $pool.State
            Pipeline = $pool.managedPipelineMode
            Runtime  = if ($pool.managedRuntimeVersion) { $pool.managedRuntimeVersion } else { "No Managed" }
            PID      = if ($workerProcess) { $workerProcess.processId } else { "N/A" }
        }
    } | Format-Table -AutoSize

    # Metriche di performance
    Write-Output "`n=== METRICHE PERFORMANCE (media su $SampleSeconds secondi) ==="
    $counters = @(
        "\Web Service(_Total)\Current Connections"
        "\Web Service(_Total)\Total Method Requests/sec"
        "\Web Service(_Total)\Bytes Total/sec"
        "\ASP.NET\Requests Current"
        "\ASP.NET\Requests Queued"
        "\ASP.NET\Request Execution Time"
    )

    try {
        $samples = Get-Counter $counters -SampleInterval 2 -MaxSamples ([math]::Max(1, $SampleSeconds / 2)) -ErrorAction Stop
        $avgValues = @{}
        foreach ($sample in $samples) {
            foreach ($cs in $sample.CounterSamples) {
                if (-not $avgValues[$cs.Path]) { $avgValues[$cs.Path] = @() }
                $avgValues[$cs.Path] += $cs.CookedValue
            }
        }
        foreach ($path in $avgValues.Keys) {
            $avg = ($avgValues[$path] | Measure-Object -Average).Average
            $counterName = ($path -split '\\')[-1]
            Write-Output "  $counterName : $([math]::Round($avg, 2))"
        }
    }
    catch {
        Write-Warning "Impossibile raccogliere i contatori: $_"
    }

    # Consumo memoria dei worker process
    Write-Output "`n=== MEMORIA WORKER PROCESS ==="
    Get-Process w3wp -ErrorAction SilentlyContinue | ForEach-Object {
        $proc = $_
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.Id)").CommandLine
        $appPool = if ($cmdLine -match '-ap "(.+?)"') { $Matches[1] } else { "Sconosciuto" }
        [PSCustomObject]@{
            PID      = $proc.Id
            AppPool  = $appPool
            MemoriaMB = [math]::Round($proc.WorkingSet64 / 1MB)
            CPU_Sec  = [math]::Round($proc.CPU, 1)
            Threads  = $proc.Threads.Count
            Handles  = $proc.HandleCount
        }
    } | Format-Table -AutoSize

    # Ultime richieste con errori nei log
    Write-Output "`n=== ULTIMI ERRORI NEI LOG (500+) ==="
    $logDir = (Get-Website | Select-Object -First 1).logFile.directory -replace '%SystemDrive%', $env:SystemDrive
    $latestLog = Get-ChildItem $logDir -Recurse -Filter "u_ex*.log" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latestLog) {
        Get-Content $latestLog.FullName -Tail 200 |
            Where-Object { $_ -notlike "#*" -and $_ -match " 5\d\d " } |
            Select-Object -Last 10 | ForEach-Object { Write-Output "  $_" }
    } else {
        Write-Output "  Nessun log trovato."
    }
}

# Eseguire il dashboard
Get-IISHealthDashboard -SampleSeconds 10
```

### Script di Alerting Automatico

```powershell
# Monitorare IIS e inviare alert via webhook (Teams, Slack, PagerDuty)
function Watch-IISHealth {
    param (
        [string]$WebhookUrl,
        [int]$CheckIntervalSeconds = 60,
        [int]$QueueThreshold = 50,
        [int]$ErrorRateThreshold = 10  # errori 500 per minuto
    )

    while ($true) {
        $alerts = @()

        # Check: Application Pool fermi
        Get-ChildItem "IIS:\AppPools" | Where-Object { $_.State -ne "Started" } | ForEach-Object {
            $alerts += "CRITICAL: Application Pool '$($_.Name)' in stato $($_.State)"
            # Tentare riavvio automatico
            try { Start-WebAppPool -Name $_.Name; $alerts += "INFO: Riavviato $($_.Name)" }
            catch { $alerts += "ERROR: Impossibile riavviare $($_.Name): $_" }
        }

        # Check: Siti fermi
        Get-Website | Where-Object { $_.State -ne "Started" } | ForEach-Object {
            $alerts += "CRITICAL: Sito '$($_.Name)' in stato $($_.State)"
        }

        # Check: Request queue elevata
        try {
            $queueSample = (Get-Counter "\ASP.NET\Requests Queued" -ErrorAction Stop).CounterSamples[0].CookedValue
            if ($queueSample -gt $QueueThreshold) {
                $alerts += "WARNING: Request queue a $([math]::Round($queueSample)) (soglia: $QueueThreshold)"
            }
        } catch {}

        # Check: Memoria worker process
        Get-Process w3wp -ErrorAction SilentlyContinue | Where-Object {
            $_.WorkingSet64 -gt 2GB
        } | ForEach-Object {
            $memGB = [math]::Round($_.WorkingSet64 / 1GB, 2)
            $alerts += "WARNING: Worker process PID $($_.Id) usa $memGB GB di memoria"
        }

        # Inviare alert se presenti
        if ($alerts.Count -gt 0 -and $WebhookUrl) {
            $body = @{
                text = "IIS Alert - $env:COMPUTERNAME`n" + ($alerts -join "`n")
            } | ConvertTo-Json
            try {
                Invoke-RestMethod -Uri $WebhookUrl -Method POST -Body $body -ContentType "application/json"
            } catch {
                Write-Warning "Impossibile inviare alert: $_"
            }
        }

        if ($alerts.Count -gt 0) {
            $alerts | ForEach-Object { Write-Warning $_ }
        } else {
            Write-Output "[$(Get-Date -Format 'HH:mm:ss')] IIS Health: OK"
        }

        Start-Sleep -Seconds $CheckIntervalSeconds
    }
}
```

---

## Certificati Let's Encrypt con Win-ACME

Per ambienti dove non si dispone di una CA enterprise, Win-ACME (precedentemente letsencrypt-win-simple) automatizza l'emissione e il rinnovo dei certificati SSL/TLS gratuiti da Let's Encrypt direttamente su IIS.

```powershell
# Scaricare Win-ACME da https://www.win-acme.com/
# Estrarre in C:\Tools\win-acme

# Emissione interattiva di un certificato
# C:\Tools\win-acme\wacs.exe

# Emissione automatica (non interattiva) per un sito IIS
C:\Tools\win-acme\wacs.exe --target iis --siteid 1 `
    --installation iis --validationmode http-01 `
    --accepttos --emailaddress admin@contoso.com

# Win-ACME crea automaticamente un task schedulato per il rinnovo
# Verificare:
Get-ScheduledTask | Where-Object TaskName -like "*ACME*"

# Per certificati wildcard (richiede DNS validation):
C:\Tools\win-acme\wacs.exe --target manual --host "*.contoso.com" `
    --validation dns-01 --validationmode dns-01 `
    --dnscreatescript "C:\Scripts\CreateDnsTxtRecord.ps1" `
    --dnsdeletescript "C:\Scripts\DeleteDnsTxtRecord.ps1" `
    --installation iis --installationsiteid 1

# Verificare i certificati installati e le scadenze
Get-ChildItem Cert:\LocalMachine\My | Where-Object {
    $_.NotAfter -lt (Get-Date).AddDays(30) -and $_.NotAfter -gt (Get-Date)
} | Select-Object Subject, Thumbprint, NotAfter,
    @{N='GiorniRimanenti';E={($_.NotAfter - (Get-Date)).Days}} |
    Format-Table -AutoSize

# Script per monitorare le scadenze dei certificati
$expiringCerts = Get-ChildItem Cert:\LocalMachine\My | Where-Object {
    $_.NotAfter -lt (Get-Date).AddDays(14) -and $_.NotAfter -gt (Get-Date)
}
if ($expiringCerts) {
    $expiringCerts | ForEach-Object {
        Write-Warning "Certificato in scadenza: $($_.Subject) - Scade: $($_.NotAfter)"
    }
}
```

---

## Esercizi

### Esercizio 1 — Deployment di un Sito ASP.NET Core Sicuro

Configura un sito IIS di produzione per un'applicazione ASP.NET Core:
- Application pool con `managedRuntimeVersion=""` e `startMode=AlwaysRunning`
- Hosting model in-process con environment variable `ASPNETCORE_ENVIRONMENT=Production`
- Binding HTTPS con certificato auto-firmato e SNI abilitato
- Security headers completi (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Permissions-Policy)
- Redirect HTTP→HTTPS con URL Rewrite
- Application Initialization configurata per pre-warming
- Permessi filesystem minimi (solo ReadAndExecute per l'identità del pool)

**Criteri di successo:** Il sito risponde su HTTPS con tutti i security headers presenti (`curl -I`), il redirect HTTP→HTTPS funziona, e l'app si avvia senza errori nei log.

### Esercizio 2 — Reverse Proxy ARR con Load Balancing

Implementa un reverse proxy IIS con ARR che distribuisce il traffico tra due backend:
- Server farm con due nodi backend (possono essere IIS locali su porte diverse)
- Algoritmo di load balancing: Least Current Requests
- Health check attivo ogni 30 secondi verso `/health`
- Timeout proxy configurato a 120 secondi
- Header `X-Forwarded-For`, `X-Forwarded-Proto` e `X-Forwarded-Host` inoltrati ai backend
- URL Rewrite: `/api/*` verso i backend, tutto il resto servito localmente come contenuto statico

**Criteri di successo:** Le richieste vengono distribuite tra i backend, un nodo può essere fermato senza downtime, l'health check rileva e rimuove il nodo non disponibile.

### Esercizio 3 — Security Hardening Completo

Partendo da un'installazione IIS predefinita, implementa un hardening completo:
- Rimuovere tutte le feature IIS non necessarie (Directory Browsing, WebDAV)
- Request Filtering: bloccare estensioni `.exe`, `.bat`, `.cmd`, `.ps1`, `.vbs`
- Request Filtering: bloccare verbi HTTP non necessari (consentire solo GET, POST, HEAD, OPTIONS)
- Limitare `maxAllowedContentLength` a 30 MB
- Disabilitare il doppio encoding
- Rimuovere gli header `Server` e `X-Powered-By`
- Configurare IP restrictions: accesso all'area `/admin` solo dalla subnet 10.0.100.0/24
- Configurare TLS 1.2+ con cipher suite ordinate (disabilitare TLS 1.0, 1.1, SSL 3.0)
- Implementare HSTS con `includeSubDomains` e `preload`

**Criteri di successo:** Scansione con `nmap --script ssl-enum-ciphers` mostra solo TLS 1.2+, i security headers sono presenti, le estensioni bloccate restituiscono 404, e l'accesso a `/admin` da IP non autorizzati è negato.

### Esercizio 4 — Monitoraggio e Troubleshooting

Configura un sistema di monitoraggio completo per IIS:
- Script PowerShell che raccoglie metriche ogni 60 secondi: connessioni attive, richieste/sec, request queue, errori 500, consumo memoria w3wp
- Failed Request Tracing (FREB) abilitato per status code 500+ e richieste con tempo > 10 secondi
- Logging W3C con campi estesi (TimeTaken, BytesSent, BytesRecv, UserAgent)
- Script di analisi log che identifica: top 10 URL più lenti, distribuzione errori per status code, top 20 IP per volume di richieste
- Alert automatico (via webhook) quando: app pool si ferma, request queue > 50, memoria w3wp > 2 GB

**Criteri di successo:** Lo script di monitoraggio rileva correttamente un app pool fermato e invia l'alert, i report di analisi log producono output significativo.

### Esercizio 5 — Web Farm con Shared Configuration

Configura due server IIS in una web farm ad alta disponibilità:
- Shared Configuration esportata su una share di rete
- Centralized Certificate Store (CCS) con certificati condivisi
- DFS Replication per la sincronizzazione del contenuto web
- NLB o ARR per il bilanciamento del carico
- Verificare che una modifica alla configurazione su un nodo si propaga automaticamente all'altro
- Verificare che il contenuto web si replica correttamente

**Criteri di successo:** Entrambi i nodi servono lo stesso contenuto, la configurazione è sincronizzata, un nodo può essere riavviato senza downtime.

---

## Auto-valutazione

1. **Qual è il ruolo di HTTP.sys nell'architettura IIS e perché opera in kernel mode?**
   <details><summary>Risposta</summary>
   HTTP.sys è il driver kernel-mode che funge da listener HTTP per IIS. Opera in kernel mode per performance: gestisce la ricezione delle richieste TCP/HTTP, il routing alle code degli application pool, il caching delle risposte (kernel-mode response cache), la terminazione SSL/TLS e il bandwidth throttling senza context switch tra kernel e user space. Una risposta cachata in kernel mode viene servita senza mai coinvolgere il worker process w3wp.exe, riducendo drasticamente la latenza.
   </details>

2. **Qual è la differenza tra WAS e W3SVC e perché sono servizi separati?**
   <details><summary>Risposta</summary>
   WAS (Windows Process Activation Service) gestisce il ciclo di vita degli application pool e dei worker process: avvio, arresto, recycling, health monitoring e on-demand activation. W3SVC (World Wide Web Publishing Service) gestisce la configurazione HTTP, registra le URL in HTTP.sys e espone i contatori di performance. Sono separati perché WAS supporta anche protocolli non-HTTP (net.tcp, net.pipe, net.msmq per WCF), permettendo la stessa gestione dei processi indipendentemente dal protocollo. Prima di IIS 7.0, tutto era nel WWW Service monolitico.
   </details>

3. **Perché si raccomanda di usare ApplicationPoolIdentity anziché NetworkService o LocalSystem?**
   <details><summary>Risposta</summary>
   ApplicationPoolIdentity crea un account virtuale univoco per ogni application pool (es. `IIS AppPool\AppPool-ContosoWeb`). Questo garantisce isolamento: ogni pool ha la propria identità con permessi separati. NetworkService è un account condiviso — se due pool usano NetworkService, un'app compromessa può accedere alle risorse dell'altra. LocalSystem ha privilegi massimi ed è un rischio critico di sicurezza: un'app compromessa avrebbe controllo completo del server. ApplicationPoolIdentity segue il principio del minimo privilegio.
   </details>

4. **Qual è la differenza tra hosting in-process e out-of-process per ASP.NET Core su IIS?**
   <details><summary>Risposta</summary>
   In-process: l'applicazione ASP.NET Core gira direttamente dentro il processo w3wp.exe. La richiesta passa da HTTP.sys → w3wp.exe → ASP.NET Core Module (ANCM) → app, senza proxy intermedio. Performance ~4x superiore. Out-of-process: l'applicazione gira in un processo dotnet.exe separato con Kestrel. IIS/ANCM funge da reverse proxy verso Kestrel. Offre maggiore isolamento (un crash dell'app non impatta IIS) e permette multiple app per pool. In-process è il default da .NET Core 3.0+ ed è raccomandato per performance in produzione.
   </details>

5. **Come si differenziano la compressione statica e dinamica in IIS e quando usare ciascuna?**
   <details><summary>Risposta</summary>
   La compressione statica comprime file statici (HTML, CSS, JS) una sola volta, salva il risultato compresso su disco e lo serve ripetutamente senza ri-compressione: impatto CPU quasi nullo, va sempre abilitata. La compressione dinamica comprime le risposte generate da applicazioni ad ogni richiesta: non è cacheable su disco e ha un impatto CPU proporzionale al traffico. Abilitare la compressione dinamica solo se il server non è CPU-bound. IIS disabilita automaticamente la compressione quando la CPU supera le soglie configurate (`staticCompressionDisableCpuUsage`, `dynamicCompressionDisableCpuUsage`).
   </details>

6. **Cosa succede quando la Rapid-Fail Protection attiva lo stop di un application pool?**
   <details><summary>Risposta</summary>
   Se un worker process crasha un numero di volte (`rapidFailProtectionMaxCrashes`, default 5) entro un intervallo (`rapidFailProtectionInterval`, default 5 minuti), WAS disabilita l'application pool e lo mette in stato Stopped. Tutte le richieste verso il sito ricevono HTTP 503. Il pool resta in Stopped finché non viene riavviato manualmente (`Start-WebAppPool`) o automaticamente (se configurato un `autoShutdownExe`). L'evento viene registrato nel log System con Event ID 5012. Per diagnosticare la causa, analizzare i crash dump o gli eventi precedenti (Event ID 5011).
   </details>

7. **Come funziona la Shared Configuration di IIS e quali sono i rischi?**
   <details><summary>Risposta</summary>
   La Shared Configuration permette a più server IIS di leggere lo stesso `applicationHost.config` da una share di rete. I nodi condividono siti, binding, application pool e moduli. Rischi: (1) la share di rete diventa un single point of failure — se è irraggiungibile, IIS non può ricaricare la configurazione; (2) una modifica errata si propaga istantaneamente a tutti i nodi; (3) le credenziali per accedere alla share devono essere gestite con attenzione. Mitigazioni: rendere la share altamente disponibile (DFS, cluster), testare le modifiche su un nodo isolato prima di applicarle alla configurazione condivisa, mantenere backup della configurazione.
   </details>

8. **Qual è la differenza tra redirect e rewrite nelle regole URL Rewrite e quando usare ciascuno?**
   <details><summary>Risposta</summary>
   Redirect (tipo `Redirect`): IIS invia al client una risposta HTTP 301 o 302 con l'URL di destinazione nel header `Location`. Il browser segue il redirect e fa una nuova richiesta al nuovo URL. L'URL cambia nella barra del browser. Usare per: redirect HTTP→HTTPS, redirect da domini legacy, canonical URL. Rewrite (tipo `Rewrite`): IIS modifica internamente l'URL della richiesta prima di elaborarla, senza che il client ne sia consapevole. L'URL nella barra del browser non cambia. Usare per: reverse proxy (ARR), SPA fallback, URL amichevoli, routing interno.
   </details>

9. **Perché HTTP.sys è condiviso tra IIS e Kestrel e come coesistono?**
   <details><summary>Risposta</summary>
   HTTP.sys è il listener HTTP del kernel Windows, utilizzabile da qualsiasi applicazione. IIS registra le sue URL prefix in HTTP.sys tramite W3SVC. Un'app ASP.NET Core con Kestrel (out-of-process) non usa HTTP.sys direttamente — IIS riceve la richiesta via HTTP.sys e la proxy verso Kestrel su una porta localhost. In hosting in-process, l'app gira dentro w3wp.exe e usa HTTP.sys attraverso IIS. È possibile anche usare `UseHttpSys()` in Kestrel per binding diretto a HTTP.sys senza IIS, ma si perdono le funzionalità di gestione di IIS (recycling, health monitoring, processo management).
   </details>

10. **Come si configura IIS per servire un sito su HTTP/2 e quali sono i prerequisiti?**
    <details><summary>Risposta</summary>
    HTTP/2 è abilitato di default su IIS 10.0 (Windows Server 2016+) per le connessioni HTTPS. Prerequisiti: (1) Binding HTTPS con certificato valido — HTTP/2 su IIS richiede TLS (non funziona su HTTP plain). (2) Client che supporta ALPN (Application-Layer Protocol Negotiation) nella negoziazione TLS. (3) Windows Server 2016 o successivo. Non è necessaria alcuna configurazione aggiuntiva. Per verificare: aprire Chrome DevTools → Network → Protocol column e verificare che mostri "h2". Per disabilitare HTTP/2 (raro): `Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\HTTP\Parameters" -Name "EnableHttp2Tls" -Value 0 -Type DWord`.
    </details>

---

## Letture primarie consigliate

- **Microsoft Learn**: "IIS Administration" — https://learn.microsoft.com/en-us/iis/ (consultato: 2026-05-23)
- **Microsoft Learn**: "Host ASP.NET Core on Windows with IIS" — https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/iis/ (consultato: 2026-05-23)
- **Microsoft Learn**: "URL Rewrite Module Configuration Reference" — https://learn.microsoft.com/en-us/iis/extensions/url-rewrite-module/url-rewrite-module-configuration-reference (consultato: 2026-05-23)
- **Microsoft Learn**: "Application Request Routing Version 2 Overview" — https://learn.microsoft.com/en-us/iis/extensions/planning-for-arr/application-request-routing-version-2-overview (consultato: 2026-05-23)
- **Microsoft Learn**: "IIS 10.0 Security Improvements" — https://learn.microsoft.com/en-us/iis/get-started/whats-new-in-iis-10/iis-100-security-improvements (consultato: 2026-05-23)
- **Microsoft Learn**: "HTTP.sys web server implementation in ASP.NET Core" — https://learn.microsoft.com/en-us/aspnet/core/fundamentals/servers/httpsys (consultato: 2026-05-23)
- **Microsoft Learn**: "IIS modules with ASP.NET Core" — https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/aspnet-core-module (consultato: 2026-05-23)
- **OWASP**: "Secure Headers Project" — https://owasp.org/www-project-secure-headers/ (consultato: 2026-05-23)
- **IIS.net**: Estensioni e download ufficiali — https://www.iis.net/downloads (consultato: 2026-05-23)
- **Mozilla**: "SSL Configuration Generator" — https://ssl-config.mozilla.org/ (consultato: 2026-05-23)
- **Win-ACME**: Automazione certificati Let's Encrypt per IIS — https://www.win-acme.com/ (consultato: 2026-05-23)
- **Libro**: "Professional IIS 10" di Kenneth Schaefer et al., Wrox Press — riferimento completo per IIS 10.0
- **CIS Benchmark**: "Microsoft IIS 10 Benchmark" — https://www.cisecurity.org/benchmark/microsoft_iis (consultato: 2026-05-23)

---

## Collegamenti incrociati

- [05-sicurezza-windows.md](05-sicurezza-windows.md) — ACL, permessi NTFS, Windows Defender (permessi filesystem per IIS)
- [06-rete-windows.md](06-rete-windows.md) — TCP/IP, DNS, firewall Windows (prerequisiti di rete per IIS)
- [08-permessi-e-accesso.md](08-permessi-e-accesso.md) — NTFS permissions, share permissions (permessi sui contenuti web)
- [09-monitoraggio-performance.md](09-monitoraggio-performance.md) — Performance Monitor, contatori (monitoraggio IIS con PerfMon)
- [11-servizi-certificati.md](11-servizi-certificati.md) — PKI, CA enterprise, certificati X.509 (certificati SSL per IIS)
- [22-powershell-scripting-avanzato.md](22-powershell-scripting-avanzato.md) — Scripting avanzato (automazione IIS con PowerShell)
- [28-pki-certificati-guida-completa.md](28-pki-certificati-guida-completa.md) — PKI approfondita (gestione certificati per TLS)
- [29-windows-server-hardening.md](29-windows-server-hardening.md) — Hardening server (security baseline per server IIS)
- [27-failover-clustering-guida.md](27-failover-clustering-guida.md) — Failover Clustering (alta disponibilità IIS)
- [21-group-policy-guida-completa.md](21-group-policy-guida-completa.md) — GPO (distribuzione configurazioni IIS via policy)

---

## Glossario locale

| Termine | Definizione |
|---------|------------|
| **ANCM** | ASP.NET Core Module — modulo IIS nativo che gestisce l'hosting di applicazioni ASP.NET Core (v2 supporta in-process e out-of-process) |
| **Application Pool** | Contenitore di isolamento che esegue uno o più siti web in un processo worker separato (w3wp.exe) con identità e risorse dedicate |
| **ARR** | Application Request Routing — modulo IIS per reverse proxy, load balancing e URL affinity |
| **CCS** | Centralized Certificate Store — funzionalità IIS per gestire certificati SSL/TLS in una share di rete condivisa tra i nodi della farm |
| **FastCGI** | Protocollo per l'esecuzione di applicazioni esterne (PHP, Python) con processi persistenti, più efficiente del CGI tradizionale |
| **FREB** | Failed Request Tracing — funzionalità di diagnostica IIS che registra il tracciamento dettagliato di richieste che soddisfano criteri specifici |
| **HSTS** | HTTP Strict Transport Security — header che obbliga il browser a usare solo HTTPS per il dominio, prevenendo downgrade attacks |
| **HTTP.sys** | Driver kernel-mode di Windows che gestisce la ricezione, il routing e il caching delle richieste HTTP/HTTPS |
| **Integrated Pipeline** | Modalità della pipeline IIS che unifica i moduli nativi IIS e i moduli managed ASP.NET in un unico flusso di elaborazione |
| **Kestrel** | Web server cross-platform incluso in ASP.NET Core, usato come backend quando IIS opera in modalità out-of-process |
| **NLB** | Network Load Balancing — servizio Windows per il bilanciamento del carico a livello di rete (Layer 4) tra più server |
| **Request Filtering** | Modulo IIS di sicurezza che filtra le richieste basandosi su URL, estensioni, verbi HTTP, lunghezza e sequenze di caratteri |
| **Shared Configuration** | Funzionalità IIS che permette a più server di condividere la stessa configurazione `applicationHost.config` da una share di rete |
| **SNI** | Server Name Indication — estensione TLS che permette al client di specificare l'hostname durante l'handshake, consentendo HTTPS multi-sito su un singolo IP |
| **URL Rewrite** | Modulo IIS per la riscrittura e il redirect degli URL con regole basate su pattern matching e condizioni |
| **W3SVC** | World Wide Web Publishing Service — servizio Windows che gestisce la configurazione HTTP di IIS e l'integrazione con HTTP.sys |
| **WAS** | Windows Process Activation Service — servizio Windows che gestisce il ciclo di vita degli application pool e dei worker process |
| **Web Garden** | Configurazione di un application pool con più di un worker process, utile per scenari specifici ma problematica con session state in-process |
| **w3wp.exe** | Worker process di IIS — il processo che esegue il codice dell'applicazione web all'interno di un application pool |
