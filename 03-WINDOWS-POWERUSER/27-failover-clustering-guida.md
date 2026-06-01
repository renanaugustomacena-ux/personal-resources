---
Modulo del corso: "Windows Power User per ingegneri di sistema"
Prerequisiti:
  - Amministrazione Windows Server intermedia (Server Manager, AD DS, DNS, DHCP)
  - Familiarità con PowerShell per la gestione dei server (Modulo 02 — PowerShell)
  - Conoscenza base di networking Windows (Modulo 06 — Rete Windows)
  - Esperienza con storage Windows (Modulo 07 — Storage Windows)
  - Comprensione di Hyper-V (Modulo 23 — Hyper-V Guida Completa)
  - Conoscenza base di Active Directory e Group Policy (Modulo 01, Modulo 21)
  - Modulo 07 — Storage Windows (SAN, iSCSI, SMB 3.x, Storage Spaces)
  - Modulo 15 — Backup e Ripristino (strategie di backup e restore)
  - Modulo 29 — Windows Server Hardening (hardening dei nodi)
Obiettivi:
  1. Comprendere l'architettura interna del Failover Clustering — Cluster Service, RHS, cluster database, heartbeat e interconnect
  2. Configurare e gestire tutti i modelli di quorum (Node Majority, Disk Witness, File Share Witness, Cloud Witness) con dynamic quorum e forced quorum
  3. Prevenire e risolvere scenari di split-brain attraverso quorum arbitration, fencing logico e stretched cluster design
  4. Implementare e ottimizzare Cluster Shared Volumes — I/O diretto, I/O reindirizzato, CSV cache e BitLocker su CSV
  5. Progettare reti cluster multi-livello (client, heartbeat, live migration, storage) con cross-subnet e multi-site clustering
  6. Distribuire Storage Spaces Direct con tier cache/capacità, fault domain, mirror/parity e pool management
  7. Automatizzare aggiornamenti zero-downtime con Cluster-Aware Updating in modalità self-updating e remote-updating
  8. Configurare ruoli cluster specifici — Hyper-V HA, Scale-Out File Server, SQL Always On AG, DHCP, Generic Service
  9. Gestire affinità, anti-affinità, preferred/possible owners, dipendenze e priorità dei gruppi cluster
  10. Eseguire cluster validation completa, diagnostica avanzata, backup/restore della configurazione e OS rolling upgrade
Tempo stimato: 22-30 ore
Livello: proficient
Ultimo aggiornamento: 2026-05-23
Versioni di riferimento: Windows Server 2022, Windows Server 2025, PowerShell FailoverClusters module, Windows Admin Center 2.x
---

# Failover Clustering (WSFC) — Guida Approfondita

> **Modulo 27** · **Aggiornamento:** 2026-05-23

## Idee guida
1. **Quorum: Node Majority, Node + Disk, Node + File Share.**
2. **Split-brain prevention: witness configuration.**
3. **Cloud Witness (Azure) per geo-redundant clusters.**
4. **Cluster validation (`Test-Cluster`) prima del production.**
5. **CSV Direct I/O per performance; Redirected I/O è sintomo di problema.**
6. **S2D elimina la SAN; richiede RDMA e almeno 2 nodi.**
7. **CAU per patching zero-downtime: drain → patch → reboot → resume.**
8. **Kerberos CNO/VCO: oggetti computer in AD per ogni cluster e ruolo.**

## Mappa Concettuale

```
                          ┌─────────────────────────────────┐
                          │   WINDOWS FAILOVER CLUSTERING   │
                          │          (WSFC)                 │
                          └───────────────┬─────────────────┘
                                          │
          ┌───────────────────────────────┼───────────────────────────────┐
          │                               │                               │
   ┌──────▼──────┐                ┌───────▼───────┐               ┌──────▼──────┐
   │  CLUSTER    │                │   STORAGE     │               │  NETWORKING │
   │  CORE       │                │   & VOLUMES   │               │  & SITES    │
   └──────┬──────┘                └───────┬───────┘               └──────┬──────┘
          │                               │                              │
  ┌───────┼───────┐              ┌────────┼────────┐            ┌────────┼────────┐
  │       │       │              │        │        │            │        │        │
  ▼       ▼       ▼              ▼        ▼        ▼            ▼        ▼        ▼
Cluster  RHS    Quorum         CSV      S2D     Storage       Client  Heart-   Live
Service  .exe   Manager        (CSVFS)  (HCI)   Replica       Net     beat     Migration
clussvc  Res.   Witness                                        10G     Net      Net
         DLLs   Models                                                RDMA     SMB 3.x
  │       │       │              │        │        │            │        │        │
  ▼       ▼       ▼              ▼        ▼        ▼            ▼        ▼        ▼
Fail-   Health  Node Maj.     Direct   Cache    Sync/        Cross-  Multi-   Cluster
over    Detect  Disk Wit.     I/O      Tier     Async        Subnet  Site     Network
Mgr     Look-  File Share    Redir.   Capacity  Replica      Delay   Fault    Priority
        Alive  Cloud Wit.    I/O      Mirror    Partner      Thresh  Domain
Database Isit   Dynamic Q.   Cache    Parity    ship
  │               │              │        │                          │
  ▼               ▼              ▼        ▼                          ▼
CLUSTER ROLES                 MANAGEMENT                   OPERATIONS
Hyper-V VM                    PowerShell Module            Validation (Test-Cluster)
File Server / SOFS            Windows Admin Center         CAU (patching)
SQL Always On AG              System Center                OS Rolling Upgrade
DHCP / Print                  Performance Monitor          Backup & DR
Generic Svc/App               Cluster Events/Logs          Security (CNO/VCO/RBAC)
```


## Indice

- [Panoramica](#panoramica)
- [Architettura del Failover Clustering](#architettura-del-failover-clustering)
  - [Componenti Fondamentali](#componenti-fondamentali)
  - [Cluster Service Internals](#cluster-service-internals)
  - [Resource Host Subsystem (RHS) e Resource DLL](#resource-host-subsystem-rhs-e-resource-dll)
  - [Cluster Database e Registry Hive](#cluster-database-e-registry-hive)
  - [Heartbeat e Health Detection](#heartbeat-e-health-detection)
- [Prerequisiti e Pianificazione](#prerequisiti-e-pianificazione)
- [Modelli di Quorum](#modelli-di-quorum)
  - [Dynamic Quorum e Dynamic Witness](#dynamic-quorum-e-dynamic-witness)
  - [Forced Quorum e Disaster Recovery del Quorum](#forced-quorum-e-disaster-recovery-del-quorum)
- [Prevenzione Split-Brain](#prevenzione-split-brain)
- [Installazione e Configurazione del Cluster](#installazione-e-configurazione-del-cluster)
- [Cluster Roles: File Server, Hyper-V, SQL](#cluster-roles-file-server-hyper-v-sql)
  - [DHCP Cluster](#dhcp-cluster)
  - [Print Server Cluster](#print-server-cluster)
  - [Generic Service e Generic Application](#generic-service-e-generic-application)
- [Cluster Shared Volumes (CSV) — Deep Dive](#cluster-shared-volumes-csv--deep-dive)
  - [I/O Diretto vs I/O Reindirizzato](#io-diretto-vs-io-reindirizzato)
  - [Metadata Server CSV](#metadata-server-csv)
  - [BitLocker su CSV](#bitlocker-su-csv)
- [Configurazione di Rete Avanzata](#configurazione-di-rete-avanzata)
  - [Cluster Network Priority e Role Assignment](#cluster-network-priority-e-role-assignment)
  - [Cross-Subnet Clustering](#cross-subnet-clustering)
- [Cluster-Aware Updating (CAU)](#cluster-aware-updating-cau)
  - [Self-Updating vs Remote-Updating Mode](#self-updating-vs-remote-updating-mode)
  - [Pre/Post Update Script e Maintenance Windows](#prepost-update-script-e-maintenance-windows)
- [Storage Spaces Direct (S2D)](#storage-spaces-direct-s2d)
  - [Cache Tier e Capacity Tier](#cache-tier-e-capacity-tier)
  - [Fault Domain e Resilienza](#fault-domain-e-resilienza)
  - [Pool Management e Manutenzione Dischi](#pool-management-e-manutenzione-dischi)
- [Affinità e Anti-Affinità](#affinità-e-anti-affinità)
- [Cluster Validation — Deep Dive](#cluster-validation--deep-dive)
- [Gestione con PowerShell](#gestione-con-powershell)
  - [Automazione e Script Operativi](#automazione-e-script-operativi)
- [Monitoraggio e Diagnostica](#monitoraggio-e-diagnostica)
  - [Cluster Events e Cluster Log](#cluster-events-e-cluster-log)
  - [Performance Monitor per Cluster](#performance-monitor-per-cluster)
  - [Integrazione System Center](#integrazione-system-center)
- [Disaster Recovery del Cluster](#disaster-recovery-del-cluster)
  - [Backup della Configurazione Cluster](#backup-della-configurazione-cluster)
  - [Rebuild del Cluster](#rebuild-del-cluster)
  - [Hyper-V Replica e Cluster](#hyper-v-replica-e-cluster)
- [Sicurezza del Cluster](#sicurezza-del-cluster)
  - [CNO e VCO — Oggetti Computer in AD](#cno-e-vco--oggetti-computer-in-ad)
  - [Kerberos Authentication e Constrained Delegation](#kerberos-authentication-e-constrained-delegation)
  - [Cluster Hardening](#cluster-hardening)
- [Migrazione e Upgrade](#migrazione-e-upgrade)
  - [Cluster OS Rolling Upgrade](#cluster-os-rolling-upgrade)
  - [Cross-Cluster Migration](#cross-cluster-migration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Stretch Cluster e Multi-Site Clustering](#stretch-cluster-e-multi-site-clustering)
- [Monitoraggio Avanzato del Cluster](#monitoraggio-avanzato-del-cluster)
  - [Tabella di Troubleshooting Rapido](#tabella-di-troubleshooting-rapido)
- [Esercizi Pratici](#esercizi-pratici)
- [Auto-valutazione](#auto-valutazione)
- [Letture Primarie](#letture-primarie)
- [Collegamenti Incrociati](#collegamenti-incrociati)
- [Glossario Locale](#glossario-locale)
- [Riferimenti](#riferimenti)

---

## Panoramica

Il Windows Server Failover Clustering (WSFC) è la tecnologia Microsoft per l'alta disponibilità dei servizi e delle applicazioni. Un cluster è un gruppo di server indipendenti (nodi) che lavorano insieme come un singolo sistema, garantendo che se un nodo fallisce, i servizi migrano automaticamente su un altro nodo con un'interruzione minima per gli utenti.

Il clustering è alla base delle architetture ad alta disponibilità per workload critici come SQL Server Always On, Hyper-V con Live Migration, File Server Scale-Out e Storage Spaces Direct. La comprensione dei meccanismi di quorum, dello storage condiviso e delle procedure di failover/failback è essenziale per qualsiasi amministratore che gestisce infrastrutture enterprise.

Questa guida copre tutti gli aspetti del Failover Clustering: dalla progettazione e i prerequisiti alla configurazione dei modelli di quorum, dalla gestione dei ruoli cluster ai Cluster Shared Volumes, dall'aggiornamento coordinato con CAU al troubleshooting delle situazioni di failure più comuni. Ogni sezione include comandi PowerShell e procedure operative per ambienti di produzione.

---

## Architettura del Failover Clustering

### Componenti Fondamentali

```
┌──────────────────────────────────────────────────────┐
│                    Cluster Service                     │
│                                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Cluster  │  │ Resource │  │ Quorum   │            │
│  │ Network  │  │ Manager  │  │ Manager  │            │
│  │ Manager  │  │(RHS.exe) │  │          │            │
│  └──────────┘  └──────────┘  └──────────┘            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Failover │  │ Database │  │ Health   │            │
│  │ Manager  │  │ Manager  │  │ Detection│            │
│  └──────────┘  └──────────┘  └──────────┘            │
├──────────────────────────────────────────────────────┤
│                     Node 1                             │
│  ┌─────────────────────────┐                          │
│  │ Cluster Role (es. VM)   │  ← IP virtuale           │
│  │ - Virtual Machine       │  ← Storage condiviso     │
│  │ - Network Name          │  ← Heartbeat network     │
│  │ - IP Address            │                          │
│  └─────────────────────────┘                          │
├─────────┬──────────────────────────────┬──────────────┤
│ Node 1  │        Shared Storage        │   Node 2     │
│ (Active)│   (SAN / iSCSI / SMB / S2D)  │  (Passive)  │
└─────────┴──────────────────────────────┴──────────────┘
```

**Cluster Service (clussvc.exe):** Il servizio core che gestisce la membership del cluster, il monitoraggio dei nodi (heartbeat), il failover dei ruoli e la gestione del database del cluster.

**Resource Host Subsystem (RHS.exe):** Processo che ospita le risorse del cluster e monitora il loro stato di salute. Se una risorsa fallisce, RHS tenta il restart; se il restart fallisce, il Failover Manager sposta il ruolo su un altro nodo.

**Heartbeat:** I nodi del cluster si scambiano messaggi heartbeat ogni secondo sulla rete di cluster (network dedicata). Se un nodo non risponde per un periodo configurabile (default: 5 secondi per nodo isolato, configurabile), viene dichiarato in failure e le sue risorse vengono migrate.

**Cluster Database:** Database distribuito che contiene la configurazione del cluster (nodi, ruoli, risorse, reti, quorum). Replicato su tutti i nodi e sul quorum witness.

### Cluster Service Internals

Il Cluster Service (`clussvc.exe`) è il cuore del failover clustering. Si avvia come servizio Windows con start automatico e opera come un singolo processo che coordina tutti gli aspetti del clustering sul nodo locale.

```
Architettura interna di clussvc.exe:

┌─────────────────────────────────────────────────────────┐
│                    clussvc.exe                            │
│                                                           │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │ Global Update  │  │ Membership    │  │ Node Manager │ │
│  │ Manager (GUM)  │  │ Engine        │  │              │ │
│  │ • Replica DB   │  │ • Join/Evict  │  │ • Node state │ │
│  │ • Ordered      │  │ • Regroup     │  │ • Heartbeat  │ │
│  │   updates      │  │ • Quorum vote │  │ • Isolation  │ │
│  └───────────────┘  └───────────────┘  └──────────────┘ │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │ Failover Mgr  │  │ Resource Mgr  │  │ Network Mgr  │ │
│  │ • Group state  │  │ • RHS process │  │ • Net state  │ │
│  │ • Move/Fail    │  │ • DLL loading │  │ • Route calc │ │
│  │ • Priority     │  │ • Health poll │  │ • Partition  │ │
│  └───────────────┘  └───────────────┘  └──────────────┘ │
│  ┌───────────────┐  ┌───────────────┐                    │
│  │ Database Mgr  │  │ Event/Log Mgr │                    │
│  │ • CLUSDB hive │  │ • ETW tracing │                    │
│  │ • Checkpoint  │  │ • Cluster log │                    │
│  │ • Restore     │  │ • WMI events  │                    │
│  └───────────────┘  └───────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

**Global Update Manager (GUM):** Garantisce che tutti gli aggiornamenti alla configurazione del cluster siano atomici e ordinati su tutti i nodi. Quando un nodo modifica la configurazione (es. aggiunta di una risorsa), il GUM propaga l'aggiornamento a tutti i nodi in modo sincrono. Se un nodo non conferma la ricezione, viene considerato in failure.

**Membership Engine:** Gestisce il processo di join e rimozione dei nodi dal cluster. Il Regroup Protocol è il meccanismo che determina la composizione del cluster dopo un evento di rete (partizione, nodo down). I nodi scambiano messaggi e votano per formare il nuovo cluster.

**Failover Manager:** Decide dove spostare i gruppi di risorse in caso di failure. Rispetta le regole di preferred owner, possible owner, anti-affinità e priorità. Il failover avviene in ordine di priorità del gruppo (0 = massima priorità).

```powershell
# Verificare lo stato del servizio cluster
Get-Service clussvc | Select-Object Name, Status, StartType

# Avviare il servizio cluster forzatamente (dopo disaster)
# ATTENZIONE: usare solo in scenari di recovery documentati
Start-Service clussvc

# Avviare il cluster forzando il quorum su un singolo nodo
# (SOLO per disaster recovery — rischio di data corruption se usato impropriamente)
net start clussvc /forcequorum

# Verificare la versione del cluster
Get-ItemProperty "HKLM:\Cluster" -Name ClusterFunctionalLevel -ErrorAction SilentlyContinue
```

### Resource Host Subsystem (RHS) e Resource DLL

RHS (`RHS.exe`) è il processo worker che ospita e monitora le risorse del cluster. Ogni nodo esegue uno o più processi RHS, ciascuno dei quali carica le Resource DLL appropriate per il tipo di risorsa.

```
Architettura RHS:

clussvc.exe                         RHS.exe (processo 1)
┌──────────┐                       ┌────────────────────────┐
│ Resource │  ← Avvia/Monitora →   │ ┌──────────────────┐  │
│ Manager  │                       │ │ Resource DLL:    │  │
│          │                       │ │ clusres.dll      │  │
│          │                       │ │ (IP, Name, Disk) │  │
│          │                       │ └──────────────────┘  │
│          │                       │ ┌──────────────────┐  │
│          │                       │ │ Resource DLL:    │  │
│          │                       │ │ vmclusres.dll    │  │
│          │                       │ │ (Hyper-V VM)     │  │
│          │                       │ └──────────────────┘  │
└──────────┘                       └────────────────────────┘

                                    RHS.exe (processo 2)
                                   ┌────────────────────────┐
                                   │ ┌──────────────────┐  │
                                   │ │ Resource DLL:    │  │
                                   │ │ clusres2.dll     │  │
                                   │ │ (Generic Svc)    │  │
                                   │ └──────────────────┘  │
                                   └────────────────────────┘
```

**Isolamento dei processi RHS:** A partire da Windows Server 2016, le risorse critiche (come le VM Hyper-V) vengono eseguite in processi RHS separati. Se una Resource DLL causa un crash, solo le risorse nello stesso processo RHS sono impattate, non l'intero cluster.

**Resource DLL principali:**

| DLL | Risorse gestite |
|-----|----------------|
| `clusres.dll` | IP Address, Network Name, Physical Disk, File Share |
| `clusres2.dll` | Generic Application, Generic Script, Generic Service |
| `vmclusres.dll` | Virtual Machine, Virtual Machine Configuration |
| `clussvc.dll` | Distributed Network Name (DNN) |
| `wsfc_res.dll` | Scale-Out File Server, Storage Pool |

```powershell
# Verificare le Resource DLL registrate
Get-ClusterResourceType | Select-Object Name, DllName, DisplayName |
    Sort-Object DllName | Format-Table -AutoSize

# Verificare se una risorsa usa un processo RHS separato
Get-ClusterResource | Select-Object Name, ResourceType, SeparateMonitor |
    Format-Table -AutoSize

# Configurare una risorsa per usare un RHS separato (isolamento)
$res = Get-ClusterResource "VM-CriticalApp"
$res.SeparateMonitor = $true

# Verificare i processi RHS attivi
Get-Process -Name RHS -ErrorAction SilentlyContinue |
    Select-Object Id, HandleCount, WorkingSet64, StartTime
```

### Cluster Database e Registry Hive

Il cluster database è un registry hive specializzato (`CLUSDB`) che contiene l'intera configurazione del cluster. Ogni nodo mantiene una copia identica, sincronizzata tramite il GUM.

```
Struttura del registry hive CLUSDB:

HKLM\Cluster\
├── Nodes\
│   ├── {GUID-Node1}\     → Nome, stato, peso del voto
│   └── {GUID-Node2}\     → Nome, stato, peso del voto
├── Groups\
│   ├── {GUID-Group1}\    → Nome, stato, preferred owner, failover policy
│   └── {GUID-Group2}\    → Nome, stato, preferred owner, failover policy
├── Resources\
│   ├── {GUID-Res1}\      → Tipo, parametri, dipendenze, monitor interval
│   └── {GUID-Res2}\      → Tipo, parametri, dipendenze, monitor interval
├── Networks\
│   ├── {GUID-Net1}\      → Indirizzo, maschera, ruolo (cluster/client)
│   └── {GUID-Net2}\      → Indirizzo, maschera, ruolo (cluster/client)
├── NetworkInterfaces\    → Mapping NIC-nodo-rete
├── ResourceTypes\        → DLL, parametri default, timeout
└── Quorum\               → Tipo, witness path, configurazione
```

```powershell
# Il file CLUSDB si trova in:
# %SystemRoot%\Cluster\CLUSDB (copia locale sul nodo)
# Il witness contiene una copia del checkpoint del database

# Esportare la configurazione del cluster (backup)
Get-ClusterResource | Export-Clixml "C:\ClusterBackup\resources.xml"
Get-ClusterGroup | Export-Clixml "C:\ClusterBackup\groups.xml"
Get-ClusterNode | Export-Clixml "C:\ClusterBackup\nodes.xml"

# Backup completo del registry hive del cluster
# (eseguire da un nodo attivo)
reg save "HKLM\Cluster" "C:\ClusterBackup\cluster-hive.dat" /y

# Verificare il checksum del database tra i nodi
Get-ClusterLog -Destination "C:\ClusterLogs" -TimeSpan 5
# Nel log, cercare "Database checksum" per confermare la consistenza
```

### Heartbeat e Health Detection

Il meccanismo di heartbeat è la base del rilevamento delle failure. I nodi si scambiano messaggi UDP sulla porta 3343 attraverso tutte le reti del cluster.

```
Heartbeat Timeline (default):

Tempo (s)  Evento
───────────────────────────────────────────────────
0          Node1 invia heartbeat a Node2
1          Node2 risponde (heartbeat OK)
1          Node1 invia heartbeat a Node2
2          Node2 risponde (heartbeat OK)
...
5          Node1 invia heartbeat a Node2
5          ✗ Node2 NON risponde
6          Node1 invia heartbeat a Node2 (retry 1)
6          ✗ Node2 NON risponde
...
10         Heartbeat mancati = SameSubnetThreshold (default 5)
10         → Node Manager: Node2 dichiarato "down"
10         → Membership Engine: avvia il Regroup Protocol
11         → Failover Manager: migra i gruppi di Node2
```

**Look-Alive e Is-Alive:** Oltre all'heartbeat tra nodi, ogni risorsa del cluster ha due meccanismi di monitoraggio:

- **Look-Alive** (check leggero, default ogni 5 secondi): Verifica rapida che la risorsa risponda. Per un IP Address, è un semplice controllo dello stack di rete. Per una VM, verifica che il processo vmwp.exe sia attivo.

- **Is-Alive** (check approfondito, default ogni 60 secondi): Verifica che la risorsa funzioni correttamente. Per un File Server, tenta un accesso alla share. Per SQL Server, esegue una query di test.

```powershell
# Verificare e modificare i parametri di heartbeat
$cluster = Get-Cluster
$cluster | Format-List SameSubnetDelay, SameSubnetThreshold,
    CrossSubnetDelay, CrossSubnetThreshold, PlumbAllCrossSubnetRoutes

# Parametri di heartbeat per nodi sulla stessa subnet
$cluster.SameSubnetDelay = 1000        # ms tra heartbeat (default: 1000)
$cluster.SameSubnetThreshold = 10      # mancati prima di failure (default: 5)

# Parametri per nodi su subnet diverse (multi-site)
$cluster.CrossSubnetDelay = 1000       # ms tra heartbeat (default: 1000)
$cluster.CrossSubnetThreshold = 20     # mancati prima di failure (default: 20)

# Verificare i parametri Look-Alive e Is-Alive di una risorsa
$res = Get-ClusterResource "Cluster IP Address"
$res | Format-List LooksAlivePollInterval, IsAlivePollInterval, RestartAction,
    RestartDelay, RestartPeriod, RestartThreshold, RetryPeriodOnFailure

# Modificare gli intervalli di monitoraggio
$res.LooksAlivePollInterval = 5000     # ms (default: 5000)
$res.IsAlivePollInterval = 60000       # ms (default: 60000)
$res.RestartThreshold = 3              # tentativi di restart prima di failover
$res.RestartPeriod = 900000            # ms — periodo per il conteggio restart (15 min)
```

---

## Prerequisiti e Pianificazione

### Requisiti Hardware e Software

- **Nodi:** Windows Server (Standard o Datacenter) con la stessa versione su tutti i nodi
- **Dominio:** Tutti i nodi devono essere membri dello stesso dominio AD (o domain trust)
- **Rete:** Minimo 2 NIC per nodo (una per il traffico client, una per il cluster heartbeat)
- **Storage:** Storage condiviso accessibile da tutti i nodi (SAN FC, iSCSI, SMB 3.0, o S2D)
- **DNS:** Risoluzione corretta di tutti i nomi dei nodi e del cluster

### Reti del Cluster

```
┌─────────────────────────────────────────────┐
│              Rete Client (Produzione)         │
│              10.0.1.0/24                      │
│                                               │
│  Node1: 10.0.1.10    Node2: 10.0.1.11       │
│  Cluster IP: 10.0.1.100                      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│          Rete Cluster (Heartbeat)             │
│          192.168.100.0/24                     │
│                                               │
│  Node1: 192.168.100.10  Node2: 192.168.100.11│
│                                               │
│  (Solo traffico cluster, no client access)    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│         Rete Storage (iSCSI/SMB)              │
│         172.16.0.0/24                         │
│                                               │
│  Node1: 172.16.0.10    Node2: 172.16.0.11    │
│  iSCSI Target: 172.16.0.100                  │
└─────────────────────────────────────────────┘
```

### Validazione Pre-Installazione

```powershell
# Eseguire il Cluster Validation Wizard (OBBLIGATORIO prima della creazione)
Test-Cluster -Node "NODE01","NODE02" -Include "Storage","Inventory","Network","System Configuration"

# Report di validazione completo
Test-Cluster -Node "NODE01","NODE02" -ReportName "C:\ClusterReports\validation"

# Validare solo specifiche categorie
Test-Cluster -Node "NODE01","NODE02" -Include "Network" -Verbose

# Verificare i risultati
# Il report HTML è generato in: C:\Users\[user]\AppData\Local\Temp\
# Cercare: Warning e Failure — i Warning vanno investigati, i Failure devono essere risolti
```

---

## Modelli di Quorum

Il quorum è il meccanismo che determina quanti nodi (e/o witness) devono essere operativi perché il cluster possa funzionare. Il quorum previene la situazione di "split-brain" dove due sottoinsiemi del cluster operano indipendentemente, potenzialmente corrompendo i dati.

### Regola del Voto

Ogni nodo ha un voto. Il witness (se configurato) ha un voto. Il cluster è operativo finché la maggioranza dei voti (>50%) è disponibile.

### Modelli

**Node Majority (nessun witness):**
- Adatto per cluster con un numero dispari di nodi
- Tollera la perdita di (N-1)/2 nodi
- Esempio: 3 nodi → tollera 1 failure, 5 nodi → tollera 2 failure

**Node and Disk Majority:**
- Un disco condiviso funge da witness aggiuntivo
- Adatto per cluster con numero pari di nodi
- Esempio: 2 nodi + 1 disk witness → tollera 1 failure

**Node and File Share Majority:**
- Una file share su un server esterno funge da witness
- Adatto per cluster geograficamente distribuiti (no storage condiviso per il witness)
- La file share può essere su qualsiasi file server accessibile dai nodi

**Cloud Witness (raccomandato da Windows Server 2016):**
- Un blob storage account Azure funge da witness
- Ideale per cluster ibridi e multi-sito
- Non richiede infrastruttura aggiuntiva on-premises

```powershell
# Configurare Cloud Witness
Set-ClusterQuorum -CloudWitness `
    -AccountName "clusterwitness" `
    -AccessKey "chiave-di-accesso-azure-storage" `
    -Endpoint "core.windows.net"

# Configurare File Share Witness
Set-ClusterQuorum -FileShareWitness "\\fileserver\ClusterWitness"

# Configurare Disk Witness
Set-ClusterQuorum -DiskWitness "Cluster Disk 3"

# Configurare Node Majority (nessun witness)
Set-ClusterQuorum -NodeMajority

# Verificare la configurazione del quorum
Get-ClusterQuorum | Select-Object Cluster, QuorumResource, QuorumType
```

### Tabella di Sopravvivenza

```
Nodi    Witness    Voti Totali    Maggioranza    Failure Tollerati
─────   ────────   ───────────    ──────────     ─────────────────
2       Sì         3              2              1 (nodo OR witness)
3       No         3              2              1 nodo
3       Sì         4              3              1 nodo + witness
4       Sì         5              3              2 (nodi/witness)
5       No         5              3              2 nodi
5       Sì         6              4              2 nodi + witness
```

### Dynamic Quorum e Dynamic Witness

A partire da Windows Server 2012 R2, il cluster utilizza il **Dynamic Quorum** per adattare automaticamente il numero di voti necessari in base ai nodi attivi. Quando un nodo viene spento in modo controllato (manutenzione, CAU), il suo voto viene rimosso dal conteggio, mantenendo il cluster operativo anche con meno nodi del previsto.

```
Dynamic Quorum — Esempio con 4 nodi + witness:

Stato iniziale: 4 nodi + witness = 5 voti, maggioranza = 3
                                    Voti Attivi  Maggioranza
1. Tutti attivi                      5            3
2. Node4 in manutenzione (drain)     4            3
   → Dynamic quorum rimuove il voto di Node4
   → Voti effettivi: 4, maggioranza: 3
3. Node3 failure                     3            2
   → Dynamic quorum ricalcola
   → Voti effettivi: 3, maggioranza: 2
4. Witness offline                   2            2
   → Dynamic quorum rimuove il witness
   → Voti effettivi: 2, maggioranza: 2
5. Node2 failure                     1            1
   → Solo Node1 attivo con il suo voto
   → Cluster operativo come nodo singolo

SENZA dynamic quorum, lo step 3 avrebbe causato
il quorum loss (2 voti su 5 < maggioranza di 3).
```

**Dynamic Witness:** Complemento del dynamic quorum. Il voto del witness viene aggiunto o rimosso automaticamente per garantire che il numero totale di voti sia dispari. In un cluster a 4 nodi con witness: se tutti i nodi sono attivi, il witness vota (5 voti, dispari). Se un nodo va offline, il witness non vota (3 voti, dispari) per evitare situazioni di pareggio.

```powershell
# Verificare lo stato del dynamic quorum
Get-Cluster | Select-Object DynamicQuorum, WitnessDynamicWeight

# Dynamic quorum è abilitato di default
# Per disabilitarlo (NON raccomandato):
(Get-Cluster).DynamicQuorum = 0

# Verificare il peso dinamico dei nodi
Get-ClusterNode | Select-Object Name, State, NodeWeight, DynamicWeight

# NodeWeight = 1 (voto statico assegnato)
# DynamicWeight = 0 o 1 (voto effettivo dopo dynamic quorum)

# Rimuovere manualmente il voto di un nodo (es. nodo in recovery lento)
(Get-ClusterNode "NODE03").NodeWeight = 0
```

### Forced Quorum e Disaster Recovery del Quorum

Il **forced quorum** è l'ultima risorsa in uno scenario di disaster dove il cluster ha perso la maggioranza dei voti. Forzare il quorum significa avviare il cluster senza la maggioranza dei nodi, con il rischio di split-brain se i nodi perduti tornano online indipendentemente.

```powershell
# Scenario: cluster a 3 nodi, 2 nodi distrutti dal disastro
# Node1 è l'unico sopravvissuto ma non ha il quorum

# 1. Avviare il cluster con forced quorum
net start clussvc /forcequorum

# Oppure via PowerShell (Windows Server 2016+)
Start-ClusterNode -Name "NODE01" -FixQuorum

# 2. IMMEDIATAMENTE dopo, impedire ai nodi fantasma di riunirsi
# Rimuovere i nodi distrutti dal cluster
Remove-ClusterNode -Name "NODE02" -Force
Remove-ClusterNode -Name "NODE03" -Force

# 3. Configurare il quorum per il nuovo stato
Set-ClusterQuorum -NodeMajority

# 4. Verificare lo stato
Get-ClusterQuorum
Get-ClusterNode | Select-Object Name, State, NodeWeight, DynamicWeight

# 5. Aggiungere nuovi nodi quando disponibili
Add-ClusterNode -Cluster "CLUSTER01" -Name "NODE04"
Add-ClusterNode -Cluster "CLUSTER01" -Name "NODE05"

# 6. Riconfigurare il quorum con witness
Set-ClusterQuorum -CloudWitness -AccountName "witnessaccount" -AccessKey "key"
```

**Prevent Quorum su nodi specifici:** In scenari multi-sito, si può configurare un nodo come "no-vote" per controllare quale sito mantiene il quorum in caso di partizione.

```powershell
# Assegnare peso zero a un nodo (non vota nel quorum)
(Get-ClusterNode "NODE-DR").NodeWeight = 0

# Verificare la distribuzione dei voti
Get-ClusterNode | Select-Object Name, State, NodeWeight, DynamicWeight |
    Format-Table -AutoSize
```

---

## Prevenzione Split-Brain

Lo split-brain è lo scenario più pericoloso per un cluster: due gruppi di nodi operano indipendentemente, ciascuno convinto di essere il cluster legittimo, potenzialmente scrivendo dati in conflitto sullo stesso storage condiviso.

### Meccanismi di Prevenzione

```
Layered Split-Brain Prevention:

Layer 1: Quorum Voting
├── Maggioranza richiesta (>50% dei voti)
├── Solo la partizione con la maggioranza rimane operativa
├── La partizione minoritaria si spegne automaticamente
└── Il witness (disco/file share/cloud) rompe il pareggio

Layer 2: Quorum Arbitration
├── Quando 2 partizioni hanno lo stesso numero di voti
├── Entrambe tentano di acquisire il witness
├── La prima che acquisisce il witness vince (wins the race)
└── La partizione perdente si spegne entro 5 secondi

Layer 3: Persistent Reservation (SCSI PR)
├── Storage condiviso usa SCSI Persistent Reservation
├── Solo il nodo con la reservation può scrivere
├── Al failover, la reservation viene trasferita
└── Nodo senza reservation: I/O bloccato a livello storage

Layer 4: Cluster Network Partitioning
├── Monitoring su TUTTE le reti del cluster
├── Se almeno UNA rete funziona, nodo considerato raggiungibile
├── Partizione dichiarata solo quando TUTTE le reti sono interrotte
└── Configurare sempre almeno 2 reti cluster indipendenti
```

```powershell
# Verificare la configurazione delle SCSI Persistent Reservation
# (automatica per dischi cluster, non richiede configurazione manuale)
Get-ClusterResource | Where-Object ResourceType -eq "Physical Disk" |
    Get-ClusterParameter | Where-Object Name -eq "DiskSignature" |
    Select-Object ClusterObject, Name, Value

# Configurare l'azione al quorum loss
# Opzioni: Shutdown (default), Stop, None (pericoloso)
(Get-Cluster).QuorumArbitrationTimeMax = 20  # secondi per l'arbitration

# Verificare che tutte le reti cluster siano operative
Get-ClusterNetwork | Select-Object Name, State, Role |
    Format-Table -AutoSize

# Verificare il numero di reti cluster (deve essere >= 2)
$clusterNets = Get-ClusterNetwork | Where-Object Role -ge 1
if ($clusterNets.Count -lt 2) {
    Write-Warning "ATTENZIONE: meno di 2 reti cluster configurate — rischio split-brain elevato"
}
```

### Cross-Subnet Clustering e Stretched Cluster

Per i cluster multi-sito (stretched cluster), la prevenzione dello split-brain richiede un witness in una terza location e parametri di heartbeat ottimizzati per le latenze WAN.

```powershell
# Configurazione anti-split-brain per stretched cluster
# Il Cloud Witness in Azure è ESSENZIALE — terza location indipendente
Set-ClusterQuorum -CloudWitness `
    -AccountName "clusterwitness3rdsite" `
    -AccessKey "azure-key" `
    -Endpoint "core.windows.net"

# Configurare route plumbing per multi-site
(Get-Cluster).PlumbAllCrossSubnetRoutes = 1

# Verificare la topologia dei siti
Get-ClusterFaultDomain | Select-Object Name, Type, ParentName |
    Format-Table -AutoSize
```

---

## Installazione e Configurazione del Cluster

```powershell
# Installare la feature Failover Clustering su tutti i nodi
Install-WindowsFeature -Name Failover-Clustering -IncludeManagementTools -Restart

# Verificare l'installazione
Get-WindowsFeature Failover-Clustering | Select-Object Name, InstallState

# Creare il cluster (dopo la validazione riuscita)
New-Cluster -Name "CLUSTER01" `
    -Node "NODE01","NODE02" `
    -StaticAddress "10.0.1.100" `
    -NoStorage  # Non aggiungere storage automaticamente

# Per cluster senza AD (Workgroup cluster, Windows Server 2016+)
New-Cluster -Name "CLUSTER01" `
    -Node "NODE01","NODE02" `
    -StaticAddress "10.0.1.100" `
    -AdministrativeAccessPoint DNS

# Aggiungere un nodo al cluster esistente
Add-ClusterNode -Cluster "CLUSTER01" -Name "NODE03"

# Rimuovere un nodo dal cluster
Remove-ClusterNode -Name "NODE03" -Force

# Configurare le reti del cluster
Get-ClusterNetwork | Format-Table Name, State, Role, Address
# Role: 0 = Neither (non usato), 1 = Cluster only (heartbeat), 3 = Client and Cluster

# Configurare una rete come solo cluster (heartbeat)
(Get-ClusterNetwork "Cluster Network 2").Role = 1

# Configurare il quorum
Set-ClusterQuorum -CloudWitness -AccountName "mywitnessaccount" `
    -AccessKey "access-key-here"
```

---

## Cluster Roles: File Server, Hyper-V, SQL

### File Server (General Purpose)

```powershell
# Aggiungere un ruolo File Server al cluster
Add-ClusterFileServerRole -Storage "Cluster Disk 1" `
    -Name "FS-Cluster" `
    -StaticAddress "10.0.1.101"

# Creare una share sul cluster
New-SmbShare -Name "SharedData" -Path "C:\ClusterStorage\Volume1\SharedData" `
    -FullAccess "CONTOSO\Domain Admins" `
    -ChangeAccess "CONTOSO\GG-Users" `
    -ScopeName "FS-Cluster"
```

### Scale-Out File Server (SOFS) per Hyper-V e SQL

```powershell
# Creare un SOFS (per workload continuously available)
Add-ClusterScaleOutFileServerRole -Name "SOFS01"

# SOFS non usa un singolo IP — tutti i nodi servono il traffico simultaneamente
# Ideale per storage di VM Hyper-V e database SQL
```

### Hyper-V Cluster

```powershell
# Prerequisiti: Hyper-V installato su tutti i nodi, storage CSV configurato

# Creare una VM altamente disponibile
New-VM -Name "SRV-APP01" -Generation 2 `
    -MemoryStartupBytes 4GB `
    -Path "C:\ClusterStorage\Volume1\VMs" `
    -NewVHDPath "C:\ClusterStorage\Volume1\VMs\SRV-APP01\OS.vhdx" `
    -NewVHDSizeBytes 80GB `
    -SwitchName "vSwitch-Prod"

# Rendere la VM altamente disponibile (aggiungere al cluster)
Add-ClusterVirtualMachineRole -VMName "SRV-APP01"

# Verificare il ruolo nel cluster
Get-ClusterGroup | Where-Object GroupType -eq "VirtualMachine" |
    Select-Object Name, State, OwnerNode
```

### SQL Server Always On Availability Groups

SQL Server utilizza WSFC come infrastruttura di base per gli Always On Availability Groups. Il cluster gestisce il failover automatico delle istanze SQL e il monitoraggio della salute.

```powershell
# Prerequisiti:
# 1. WSFC configurato con tutti i nodi SQL
# 2. SQL Server installato su ogni nodo
# 3. Database creato e di cui è stato fatto il backup
# 4. Endpoint di mirroring configurato su ogni istanza

# Creare l'Availability Group (da eseguire su SQL)
# Questo è un esempio T-SQL, non PowerShell:
# CREATE AVAILABILITY GROUP [AG-Production]
# WITH (AUTOMATED_BACKUP_PREFERENCE = SECONDARY)
# FOR DATABASE [AppDB]
# REPLICA ON
#   N'NODE01' WITH (ENDPOINT_URL = 'TCP://NODE01:5022',
#     FAILOVER_MODE = AUTOMATIC, AVAILABILITY_MODE = SYNCHRONOUS_COMMIT),
#   N'NODE02' WITH (ENDPOINT_URL = 'TCP://NODE02:5022',
#     FAILOVER_MODE = AUTOMATIC, AVAILABILITY_MODE = SYNCHRONOUS_COMMIT);
```

### DHCP Cluster

Il clustering del servizio DHCP garantisce la continuità dell'assegnazione degli indirizzi IP in caso di failure del server DHCP primario.

```powershell
# Prerequisiti: DHCP Server installato su entrambi i nodi
# Lo scope DHCP viene replicato automaticamente tra i nodi del cluster

# Aggiungere il ruolo DHCP al cluster
Add-ClusterServerRole -StaticAddress "10.0.1.102" -Name "DHCP-Cluster" `
    -Storage "Cluster Disk 2"

# Installare il servizio DHCP se non presente
Install-WindowsFeature -Name DHCP -IncludeManagementTools

# Configurare il DHCP failover (alternativa al clustering tradizionale)
# DHCP Failover è un meccanismo nativo di DHCP, non richiede WSFC
Add-DhcpServerv4Failover -Name "DHCP-HA" `
    -PartnerServer "NODE02" `
    -ScopeId "10.0.1.0" `
    -SharedSecret "s3cr3tK3y!" `
    -Mode HotStandby `
    -ServerRole Active `
    -ReservePercent 10

# Verificare lo stato del failover DHCP
Get-DhcpServerv4Failover | Format-List
```

### Print Server Cluster

```powershell
# Il Print Server cluster è supportato ma raramente usato
# in ambienti moderni (le stampanti sono gestite via print management)

Add-ClusterPrintServerRole -Name "PRINT-Cluster" `
    -StaticAddress "10.0.1.103" `
    -Storage "Cluster Disk 3"
```

### Generic Service e Generic Application

Il Generic Service e Generic Application permettono di rendere altamente disponibile qualsiasi servizio Windows o applicazione che non ha un resource type dedicato.

```powershell
# Generic Service: per servizi Windows registrati in services.msc
# Il cluster monitora il servizio e lo riavvia/failover se fallisce

# Esempio: rendere HA un servizio custom
Add-ClusterGenericServiceRole -ServiceName "MyCustomService" `
    -Name "CustomSvc-HA" `
    -StaticAddress "10.0.1.104" `
    -Storage "Cluster Disk 4" `
    -CheckpointKey "SOFTWARE\MyApp"  # Chiavi di registry da replicare

# Generic Application: per applicazioni EXE che non sono servizi Windows
Add-ClusterGenericApplicationRole -CommandLine "C:\App\myapp.exe --config cluster" `
    -Name "CustomApp-HA" `
    -StaticAddress "10.0.1.105" `
    -Storage "Cluster Disk 5" `
    -Parameters "--mode=production" `
    -CurrentDirectory "C:\App"

# Generic Script: per script personalizzati di monitoraggio
# Lo script deve implementare le funzioni: Online, Offline, LooksAlive, IsAlive
# Esempio di script resource (.vbs):
# Function Online() ... End Function
# Function Offline() ... End Function
# Function LooksAlive() ... End Function
# Function IsAlive() ... End Function

# Verificare i ruoli generici
Get-ClusterGroup | Where-Object GroupType -in "GenericService","GenericApplication" |
    Select-Object Name, State, OwnerNode, GroupType
```

---

## Cluster Shared Volumes (CSV) — Deep Dive

CSV è un filesystem distribuito che permette a tutti i nodi del cluster di accedere simultaneamente allo stesso volume. A differenza dei dischi cluster tradizionali (che possono essere montati da un solo nodo alla volta), CSV abilita l'accesso concorrente necessario per Hyper-V Live Migration e Scale-Out File Server.

```
Architettura CSV:
┌─────────────────────────────────────────────┐
│           C:\ClusterStorage\Volume1          │
│           (Mount point identico su tutti     │
│            i nodi del cluster)               │
├──────────────┬──────────────────────────────┤
│ Node1 (Owner)│ Node2 (Non-Owner)            │
│ I/O diretto  │ I/O redirected via SMB       │
│ al disco     │ al Node1 (owner)             │
│              │ (oppure I/O diretto se CSV    │
│              │  Direct I/O è supportato)     │
└──────────┬───┴────────────┬─────────────────┘
           │  SAN / iSCSI   │
           └────────────────┘
```

```powershell
# Aggiungere un disco al cluster
Get-ClusterAvailableDisk | Add-ClusterDisk

# Convertire un disco cluster in CSV
Add-ClusterSharedVolume -Name "Cluster Disk 1"

# Verificare i CSV
Get-ClusterSharedVolume | Select-Object Name, State, OwnerNode
Get-ClusterSharedVolumeState | Select-Object Name, Node, StateInfo,
    BlockRedirectedIOReason, FileSystemRedirectedIOReason

# Il mount point è sempre: C:\ClusterStorage\Volume[N]
Get-ChildItem "C:\ClusterStorage"

# Verificare lo spazio disponibile
Get-ClusterSharedVolume | ForEach-Object {
    $csv = $_
    $csvInfo = $csv.SharedVolumeInfo[0].Partition
    [PSCustomObject]@{
        Name       = $csv.Name
        Path       = $csv.SharedVolumeInfo[0].FriendlyVolumeName
        SizeGB     = [math]::Round($csvInfo.Size / 1GB, 2)
        FreeGB     = [math]::Round($csvInfo.FreeSpace / 1GB, 2)
        UsedPct    = [math]::Round(($csvInfo.UsedSpace / $csvInfo.Size) * 100, 1)
        Owner      = $csv.OwnerNode.Name
    }
}

# Spostare la ownership di un CSV (per manutenzione)
Move-ClusterSharedVolume -Name "Cluster Virtual Disk (Volume1)" -Node "NODE02"
```

### CSV Cache

CSV Cache utilizza la RAM del server come cache di lettura write-through per migliorare le prestazioni I/O, particolarmente efficace per workload con molte letture random (es. boot storm di VDI).

```powershell
# Abilitare CSV Cache (allocare 2 GB per nodo)
(Get-Cluster).BlockCacheSize = 2048  # MB

# Verificare
(Get-Cluster).BlockCacheSize

# Raccomandazione: allocare il 10-15% della RAM disponibile per la cache
# Per un nodo con 64 GB di RAM: 6-8 GB di cache (6144-8192 MB)
# Non superare il 20% della RAM per evitare pressione sulla memoria
```

### I/O Diretto vs I/O Reindirizzato

La distinzione tra Direct I/O e Redirected I/O è critica per le prestazioni CSV.

```
I/O Diretto (performance ottimale):
┌──────────┐                    ┌──────────┐
│ Node1    │                    │ Node2    │
│ (Owner)  │                    │ (Non-Own)│
│          │                    │          │
│ App ──── │── SAN/iSCSI ──────│── App    │
│    │     │                    │    │     │
│    └─ I/O diretto al disco   │    └─ I/O diretto al disco
│          │                    │    (bypassa Node1)
└──────────┘                    └──────────┘
   Entrambi i nodi accedono direttamente allo storage.

I/O Reindirizzato (performance degradata):
┌──────────┐                    ┌──────────┐
│ Node1    │                    │ Node2    │
│ (Owner)  │                    │ (Non-Own)│
│          │   ←── SMB ────     │          │
│ App ──── │── SAN/iSCSI        │ App ──── │
│    │     │                    │    │     │
│    └─ I/O al disco            │    └─ I/O via SMB a Node1
│         (tutto I/O passa      │    (latenza + overhead SMB)
│          da Node1)            │
└──────────┘                    └──────────┘
   Node2 non può raggiungere il disco, invia I/O a Node1 via rete.
```

**Cause di I/O reindirizzato:**
- **Block Redirected I/O:** Il path MPIO/iSCSI del nodo non-owner è interrotto. Lo storage non è raggiungibile dal nodo.
- **File System Redirected I/O:** Il nodo non-owner ha perso la comunicazione con il nodo owner per le operazioni di metadata NTFS/ReFS. Causa tipica: interruzione della rete cluster.

```powershell
# Diagnosi dettagliata dello stato I/O CSV
Get-ClusterSharedVolumeState | ForEach-Object {
    [PSCustomObject]@{
        VolumeName    = $_.Name
        Node          = $_.Node
        StateInfo     = $_.StateInfo
        BlockRedirect = $_.BlockRedirectedIOReason
        FSRedirect    = $_.FileSystemRedirectedIOReason
    }
} | Format-Table -AutoSize

# Stato desiderato: StateInfo = "Direct", entrambi i motivi = "None"
```

### Metadata Server CSV

Il nodo **owner** di un CSV funge da **Metadata Server** per quel volume. Tutte le operazioni di metadata del filesystem (creazione/eliminazione file, modifica permessi, estensione file) vengono coordinate dal metadata server, anche quando l'I/O dei dati è diretto.

```powershell
# Identificare il metadata server (owner) per ogni CSV
Get-ClusterSharedVolume |
    Select-Object Name, @{N="MetadataServer";E={$_.OwnerNode.Name}}, State |
    Format-Table -AutoSize

# Bilanciare la ownership dei CSV tra i nodi
# Per distribuire il carico di metadata, assegnare CSV diversi a nodi diversi
$csvs = Get-ClusterSharedVolume
$nodes = (Get-ClusterNode | Where-Object State -eq "Up").Name
$i = 0
foreach ($csv in $csvs) {
    $targetNode = $nodes[$i % $nodes.Count]
    if ($csv.OwnerNode.Name -ne $targetNode) {
        Move-ClusterSharedVolume -Name $csv.Name -Node $targetNode
        Write-Output "Moved $($csv.Name) to $targetNode"
    }
    $i++
}
```

### BitLocker su CSV

A partire da Windows Server 2019, è possibile crittografare i volumi CSV con BitLocker, proteggendo i dati at-rest sullo storage condiviso.

```powershell
# Abilitare BitLocker su un CSV
# Il protector viene distribuito automaticamente a tutti i nodi del cluster

# 1. Sospendere il CSV temporaneamente
Suspend-ClusterResource -Name "Cluster Virtual Disk (Volume1)"

# 2. Abilitare BitLocker con protector AD Account or Key
Enable-BitLocker -MountPoint "C:\ClusterStorage\Volume1" `
    -EncryptionMethod XtsAes256 `
    -UsedSpaceOnly `
    -ADAccountOrGroupProtector `
    -ADAccountOrGroup "CONTOSO\Cluster01$"

# 3. Riprendere il CSV
Resume-ClusterResource -Name "Cluster Virtual Disk (Volume1)"

# Verificare lo stato di crittografia
Get-BitLockerVolume -MountPoint "C:\ClusterStorage\Volume1" |
    Select-Object MountPoint, VolumeStatus, EncryptionMethod, ProtectionStatus
```

---

## Configurazione di Rete Avanzata

### Cluster Network Priority e Role Assignment

Il cluster assegna automaticamente le reti ai ruoli, ma la configurazione manuale è essenziale per ambienti di produzione.

```
Rete raccomandata per cluster di produzione:

┌──────────────────────────────────────────────────────────┐
│ Rete 1: Client/Management (Role = 3)                     │
│ 10.0.1.0/24 — Traffico client + gestione cluster         │
│ NIC: 10 GbE, Teaming LACP                               │
├──────────────────────────────────────────────────────────┤
│ Rete 2: Heartbeat/Cluster (Role = 1)                     │
│ 192.168.100.0/24 — Solo heartbeat e comunicazione cluster│
│ NIC: 10 GbE, dedicata, NO teaming (per isolamento)      │
├──────────────────────────────────────────────────────────┤
│ Rete 3: Live Migration (Role = 0, usata via config LM)  │
│ 192.168.200.0/24 — Traffico Live Migration               │
│ NIC: 25/100 GbE RDMA, SMB Direct                        │
├──────────────────────────────────────────────────────────┤
│ Rete 4: Storage (Role = 0, gestita separatamente)        │
│ 172.16.0.0/24 — iSCSI / SMB 3.0 / S2D                  │
│ NIC: 25/100 GbE RDMA, Jumbo Frame 9014                  │
└──────────────────────────────────────────────────────────┘
```

```powershell
# Configurare i ruoli delle reti del cluster
# Role 0 = Neither (non usata dal cluster)
# Role 1 = Cluster only (heartbeat)
# Role 3 = Cluster and Client (traffico misto)

Get-ClusterNetwork | Format-Table Name, State, Role, Address -AutoSize

# Impostare la rete heartbeat come cluster-only
(Get-ClusterNetwork "Heartbeat Network").Role = 1

# Impostare la rete storage come non-cluster (gestita separatamente)
(Get-ClusterNetwork "Storage Network").Role = 0

# Configurare la priorità delle reti cluster
# Le reti con priorità più bassa vengono provate per prime per il heartbeat
$net = Get-ClusterNetwork "Heartbeat Network"
$net.Metric = 1000  # Priorità alta (valore basso = priorità alta)

$netClient = Get-ClusterNetwork "Client Network"
$netClient.Metric = 5000  # Priorità bassa (usata come fallback)

# Configurare la rete per Live Migration
Set-VMHost -VirtualMachineMigrationPerformanceOption SMB
# Specificare la subnet per Live Migration
Set-VMHost -UseAnyNetworkForMigration $false
Add-VMMigrationNetwork "192.168.200.0" -Subnet "255.255.255.0"
```

### Cross-Subnet Clustering

Il cross-subnet clustering consente ai nodi del cluster di risiedere su subnet IP diverse, tipicamente in edifici o piani diversi dello stesso campus. A differenza dello stretched cluster (multi-sito), i nodi cross-subnet sono generalmente nello stesso datacenter con latenza < 1ms.

```powershell
# In un cluster cross-subnet, ogni risorsa IP Address
# ha un indirizzo per ogni subnet
# Il cluster pubblica l'indirizzo della subnet attiva

# Aggiungere un secondo indirizzo IP per la subnet del sito B
Add-ClusterResource -Name "Cluster IP Address - Site B" `
    -ResourceType "IP Address" -Group "Cluster Group"

# Configurare il secondo indirizzo IP
Get-ClusterResource "Cluster IP Address - Site B" |
    Set-ClusterParameter -Multiple @{
        Address   = "10.0.2.100"
        Network   = "Site B Network"
        SubnetMask = "255.255.255.0"
    }

# Il Network Name del cluster usa OR tra gli indirizzi IP
# (uno dei due è online a seconda del nodo owner)
Set-ClusterResourceDependency -Resource "Cluster Name" `
    -Dependency "([Cluster IP Address] or [Cluster IP Address - Site B])"

# Abilitare il plumbing di tutte le route cross-subnet
(Get-Cluster).PlumbAllCrossSubnetRoutes = 1

# Configurare TTL DNS basso per failover rapido cross-subnet
Get-ClusterResource "Cluster Name" |
    Set-ClusterParameter HostRecordTTL 120  # 2 minuti (default: 1200 = 20 min)
```

---

## Cluster-Aware Updating (CAU)

CAU automatizza il processo di aggiornamento dei nodi del cluster senza downtime per i servizi. CAU aggiorna un nodo alla volta, spostando i ruoli cluster sugli altri nodi prima di installare gli aggiornamenti e riavviare.

```
Flusso CAU:
1. Mettere NODE01 in manutenzione (drain roles)
2. Installare aggiornamenti su NODE01
3. Riavviare NODE01 se necessario
4. Verificare che NODE01 sia tornato operativo
5. Ripetere per NODE02, NODE03, ...
6. Riportare i ruoli sui nodi originali (opzionale)
```

```powershell
# Verificare i prerequisiti CAU
Test-CauSetup -ClusterName "CLUSTER01"

# Configurare CAU in modalità self-updating (il cluster aggiorna se stesso)
Add-CauClusterRole -ClusterName "CLUSTER01" `
    -DaysOfWeek Saturday `
    -WeeksOfMonth First `
    -MaxRetriesPerNode 3 `
    -MaxFailedNodes 1 `
    -RequireAllNodesOnline `
    -EnableFirewallRules `
    -Force

# Eseguire un aggiornamento CAU manuale
Invoke-CauRun -ClusterName "CLUSTER01" `
    -MaxRetriesPerNode 3 `
    -MaxFailedNodes 1 `
    -RequireAllNodesOnline `
    -EnableFirewallRules `
    -Force

# Monitorare lo stato dell'aggiornamento
Get-CauRun -ClusterName "CLUSTER01" | Select-Object Status, OverallRunStatus

# Verificare il report dell'ultimo aggiornamento
Get-CauReport -ClusterName "CLUSTER01" -Last 1 | Format-List
```

### Self-Updating vs Remote-Updating Mode

**Self-Updating Mode:** Il cluster aggiorna se stesso secondo una pianificazione configurata. Un ruolo CAU cluster viene installato su uno dei nodi e gestisce l'intero processo automaticamente. Ideale per cluster che non hanno un orchestratore centralizzato.

**Remote-Updating Mode:** Un server di gestione esterno (es. WAC o workstation admin) coordina l'aggiornamento. Utile quando si vogliono centralizzare gli aggiornamenti di più cluster da un punto unico.

```powershell
# Modalità Self-Updating: configurare la pianificazione
# Il ruolo CAU viene installato nel cluster
Add-CauClusterRole -ClusterName "CLUSTER01" `
    -DaysOfWeek Saturday `
    -WeeksOfMonth Second,Fourth `
    -StartDate "2026-06-01 02:00:00" `
    -MaxRetriesPerNode 3 `
    -MaxFailedNodes 1 `
    -RequireAllNodesOnline `
    -RebootTimeoutMinutes 30 `
    -EnableFirewallRules `
    -Force

# Verificare la configurazione del ruolo CAU
Get-CauClusterRole -ClusterName "CLUSTER01" | Format-List

# Modalità Remote-Updating: eseguire da una workstation di gestione
Invoke-CauRun -ClusterName "CLUSTER01" `
    -CauPluginName Microsoft.WindowsUpdatePlugin `
    -MaxRetriesPerNode 3 `
    -MaxFailedNodes 1 `
    -RequireAllNodesOnline `
    -Force

# Utilizzare plugin personalizzato (es. aggiornamenti firmware)
Invoke-CauRun -ClusterName "CLUSTER01" `
    -CauPluginName Microsoft.HotfixPlugin `
    -CauPluginArguments @{ HotfixRootFolderPath = "\\fileserver\Hotfixes" } `
    -Force
```

### Pre/Post Update Script e Maintenance Windows

Gli script pre/post update permettono di eseguire azioni personalizzate prima e dopo l'aggiornamento di ciascun nodo.

```powershell
# Configurare script pre-aggiornamento (es. backup configurazione)
# Lo script viene eseguito PRIMA del drain dei ruoli
$preScript = {
    param($NodeName)
    # Backup della configurazione del nodo
    Get-ClusterLog -Node $NodeName -Destination "\\backup\ClusterLogs\pre-update"
    # Notifica al team
    Send-MailMessage -To "infra@contoso.com" -From "cluster@contoso.com" `
        -Subject "CAU: Aggiornamento in corso su $NodeName" `
        -SmtpServer "smtp.contoso.com"
}

# Configurare script post-aggiornamento (es. verifica salute)
$postScript = {
    param($NodeName)
    # Verificare che tutti i ruoli siano tornati online
    $failed = Get-ClusterGroup | Where-Object State -ne "Online"
    if ($failed) {
        Write-Warning "Gruppi non online dopo update: $($failed.Name -join ', ')"
    }
}

# Applicare gli script al ruolo CAU
Set-CauClusterRole -ClusterName "CLUSTER01" `
    -PreUpdateScript "\\fileserver\Scripts\cau-pre-update.ps1" `
    -PostUpdateScript "\\fileserver\Scripts\cau-post-update.ps1"

# Configurare la finestra di manutenzione
# CAU non inizierà gli aggiornamenti fuori dalla finestra configurata
Set-CauClusterRole -ClusterName "CLUSTER01" `
    -StartDate "2026-06-01 02:00:00" `
    -DaysOfWeek Saturday `
    -WeeksOfMonth First,Third `
    -StopAfter "04:00:00"  # Max 4 ore per sessione
```

---

## Affinità e Anti-Affinità

Le regole di affinità e anti-affinità controllano il posizionamento dei ruoli sui nodi del cluster, garantendo la distribuzione ottimale dei workload e la separazione dei servizi incompatibili.

### Preferred e Possible Owners

```powershell
# Preferred Owners: nodi preferiti per un ruolo (ordine di preferenza)
# Il cluster tenta di posizionare il ruolo sul primo preferred owner disponibile
Set-ClusterOwnerNode -Group "VM-WebServer" -Owners "NODE01","NODE02"

# Possible Owners: nodi dove il ruolo PUÒ essere eseguito
# Se un nodo non è nei possible owners, il ruolo NON sarà mai migrato lì
# Utile per limitare le VM a nodi con hardware specifico (es. GPU)
$res = Get-ClusterResource -Name "Virtual Machine VM-WebServer"
Set-ClusterOwnerNode -Resource $res.Name -Owners "NODE01","NODE02","NODE03"

# Verificare gli owner configurati
Get-ClusterOwnerNode -Group "VM-WebServer" | Format-List
Get-ClusterResource -Name "Virtual Machine VM-WebServer" |
    Get-ClusterOwnerNode | Format-List
```

### Anti-Affinità (Cluster Group Anti-Affinity)

L'anti-affinità garantisce che due o più gruppi di risorse non vengano mai eseguiti sullo stesso nodo, per evitare che un singolo failure impatti entrambi i servizi.

```powershell
# Configurare l'anti-affinità tra due gruppi
# I gruppi con lo stesso AntiAffinityClassNames NON saranno mai sullo stesso nodo
$group1 = Get-ClusterGroup "VM-WebServer-Primary"
$group1.AntiAffinityClassNames = "WebTier"

$group2 = Get-ClusterGroup "VM-WebServer-Secondary"
$group2.AntiAffinityClassNames = "WebTier"

# Ora il cluster distribuirà automaticamente questi gruppi su nodi diversi

# Verificare le classi di anti-affinità
Get-ClusterGroup | Select-Object Name, OwnerNode, AntiAffinityClassNames |
    Where-Object AntiAffinityClassNames -ne "" | Format-Table -AutoSize

# Esempio pratico: separare i domain controller
$dc1 = Get-ClusterGroup "VM-DC01"
$dc1.AntiAffinityClassNames = "DomainController"
$dc2 = Get-ClusterGroup "VM-DC02"
$dc2.AntiAffinityClassNames = "DomainController"
```

### Dipendenze tra Risorse

```powershell
# Configurare dipendenze (una risorsa dipende da un'altra)
# La risorsa dipendente non si avvia finché le dipendenze non sono online
Add-ClusterResourceDependency -Resource "Network Name" -Provider "IP Address"

# Dipendenza complessa con OR (almeno una deve essere online)
Set-ClusterResourceDependency -Resource "Cluster Name" `
    -Dependency "([IP Address Site A] or [IP Address Site B])"

# Dipendenza complessa con AND (tutte devono essere online)
Set-ClusterResourceDependency -Resource "SQL Server" `
    -Dependency "([IP Address] and [Network Name] and [Cluster Disk 1])"

# Visualizzare le dipendenze
Get-ClusterResourceDependency -Resource "SQL Server" | Format-List

# Visualizzare l'albero completo delle dipendenze di un gruppo
Get-ClusterGroup "SQL-AG" | Get-ClusterResource |
    ForEach-Object {
        $dep = Get-ClusterResourceDependency -Resource $_.Name
        [PSCustomObject]@{
            Resource = $_.Name
            Dependencies = $dep.DependencyExpression
        }
    } | Format-Table -AutoSize
```

### Priorità dei Gruppi

```powershell
# La priorità determina l'ordine di failover quando più gruppi competono
# 0 = Massima priorità (failover per primo)
# 3000 = Minima priorità (failover per ultimo)

$critical = Get-ClusterGroup "VM-DatabaseServer"
$critical.Priority = 0  # Critico: failover immediato

$standard = Get-ClusterGroup "VM-WebServer"
$standard.Priority = 1000  # Standard

$low = Get-ClusterGroup "VM-DevTest"
$low.Priority = 3000  # Bassa priorità: failover solo se risorse disponibili

# Verificare le priorità
Get-ClusterGroup | Select-Object Name, Priority, State, OwnerNode |
    Sort-Object Priority | Format-Table -AutoSize
```

---

## Cluster Validation — Deep Dive

La validazione del cluster è un processo sistematico che verifica che hardware, software e rete siano configurati correttamente per il failover clustering. Microsoft richiede che la validazione passi senza errori per il supporto ufficiale.

### Categorie di Test

```
Test-Cluster Categories:

1. System Configuration
   ├── Versione OS identica su tutti i nodi
   ├── Hotfix e update allineati
   ├── Configurazione dei servizi identica
   └── BIOS/firmware compatibile

2. Storage Tests
   ├── Accesso a tutti i dischi condivisi da tutti i nodi
   ├── SCSI Persistent Reservation funzionante
   ├── Failover storage (simulazione)
   ├── Performance I/O durante il failover
   └── Validazione CSV (se applicabile)

3. Network Tests
   ├── Connettività tra tutti i nodi su tutte le reti
   ├── Latenza e packet loss
   ├── Risoluzione DNS corretta
   ├── Isolamento delle reti (heartbeat vs client)
   └── Validazione cross-subnet (se applicabile)

4. Inventory
   ├── Hardware identico o compatibile
   ├── Driver e firmware allineati
   ├── BIOS/UEFI settings compatibili
   └── Feature Windows installate
```

```powershell
# Validazione completa (OBBLIGATORIA prima di creare il cluster)
Test-Cluster -Node "NODE01","NODE02","NODE03" `
    -Include "Storage","Inventory","Network","System Configuration" `
    -ReportName "C:\Validation\full-validation"

# Validazione solo rete (utile per troubleshooting)
Test-Cluster -Node "NODE01","NODE02" -Include "Network" -Verbose

# Validazione solo storage (dopo modifiche alla SAN)
Test-Cluster -Node "NODE01","NODE02" -Include "Storage"

# Validazione pre-aggiunta nodo
Test-Cluster -Node "NODE01","NODE02","NODE-NUOVO" `
    -Include "Inventory","Network","System Configuration"

# Interpretazione dei risultati:
# - Passed: test superato, nessun problema
# - Warning: possibile problema, investigare ma non bloccante
# - Failed: problema critico, DEVE essere risolto prima di proseguire
# - Not Applicable: test non rilevante per la configurazione

# Aprire il report HTML generato
$reportPath = "$env:TEMP\Validation Report*.htm" | Get-ChildItem | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Start-Process $reportPath.FullName
```

---

## Gestione con PowerShell

```powershell
# Panoramica del cluster
Get-Cluster | Select-Object Name, Domain, SharedVolumesRoot
Get-ClusterNode | Select-Object Name, State, NodeWeight, DynamicWeight
Get-ClusterGroup | Select-Object Name, State, OwnerNode, GroupType
Get-ClusterResource | Select-Object Name, State, ResourceType, OwnerGroup, OwnerNode

# Spostare un ruolo su un altro nodo (failover manuale pianificato)
Move-ClusterGroup -Name "SRV-APP01" -Node "NODE02"

# Mettere un nodo in manutenzione (drain dei ruoli)
Suspend-ClusterNode -Name "NODE01" -Drain -Wait

# Riportare un nodo dalla manutenzione
Resume-ClusterNode -Name "NODE01" -Failback Immediate

# Testare il failover di un ruolo
Move-ClusterGroup -Name "SRV-APP01" -Node "NODE02"
Start-Sleep -Seconds 30
Move-ClusterGroup -Name "SRV-APP01" -Node "NODE01"  # Failback

# Configurare il failover automatico
$group = Get-ClusterGroup "SRV-APP01"
$group.AutoFailbackType = 1  # 0 = Prevent, 1 = Allow
$group.FailbackWindowStart = 2  # Ora di inizio failback (02:00)
$group.FailbackWindowEnd = 4    # Ora di fine failback (04:00)
$group.FailoverPeriod = 6       # Periodo in ore per il conteggio failover
$group.FailoverThreshold = 3    # Max failover nel periodo prima di stop

# Report completo dello stato del cluster
function Get-ClusterHealthReport {
    param([string]$ClusterName = (Get-Cluster).Name)

    $nodes = Get-ClusterNode -Cluster $ClusterName
    $groups = Get-ClusterGroup -Cluster $ClusterName
    $resources = Get-ClusterResource -Cluster $ClusterName
    $csvs = Get-ClusterSharedVolume -Cluster $ClusterName -ErrorAction SilentlyContinue
    $quorum = Get-ClusterQuorum -Cluster $ClusterName

    [PSCustomObject]@{
        ClusterName    = $ClusterName
        QuorumType     = $quorum.QuorumType
        NodesTotal     = $nodes.Count
        NodesUp        = ($nodes | Where-Object State -eq "Up").Count
        NodesDown      = ($nodes | Where-Object State -ne "Up").Count
        GroupsTotal    = $groups.Count
        GroupsOnline   = ($groups | Where-Object State -eq "Online").Count
        GroupsFailed   = ($groups | Where-Object State -eq "Failed").Count
        ResourcesTotal = $resources.Count
        ResourcesFailed = ($resources | Where-Object State -eq "Failed").Count
        CSVsTotal      = $csvs.Count
        CSVsOnline     = ($csvs | Where-Object State -eq "Online").Count
    }
}

Get-ClusterHealthReport | Format-List
```

### Automazione e Script Operativi

```powershell
# Script: Failover test automatizzato per tutti i ruoli
function Test-ClusterFailover {
    param(
        [string]$ClusterName = ".",
        [int]$WaitSeconds = 60
    )

    $groups = Get-ClusterGroup -Cluster $ClusterName |
        Where-Object { $_.State -eq "Online" -and $_.GroupType -ne "ClusterGroupType" }
    $nodes = (Get-ClusterNode -Cluster $ClusterName | Where-Object State -eq "Up").Name

    foreach ($group in $groups) {
        $originalNode = $group.OwnerNode.Name
        $targetNode = $nodes | Where-Object { $_ -ne $originalNode } | Get-Random

        Write-Output "Testing failover: $($group.Name) da $originalNode a $targetNode"

        # Failover
        Move-ClusterGroup -Name $group.Name -Node $targetNode -ErrorAction Stop
        Start-Sleep -Seconds $WaitSeconds

        # Verifica
        $state = (Get-ClusterGroup -Name $group.Name).State
        if ($state -ne "Online") {
            Write-Warning "ERRORE: $($group.Name) è in stato $state dopo il failover!"
            continue
        }

        # Failback
        Move-ClusterGroup -Name $group.Name -Node $originalNode -ErrorAction Stop
        Start-Sleep -Seconds ($WaitSeconds / 2)

        $finalState = (Get-ClusterGroup -Name $group.Name).State
        Write-Output "  Risultato: $finalState (owner: $((Get-ClusterGroup $group.Name).OwnerNode.Name))"
    }
}

# Script: Bilanciamento automatico dei gruppi tra i nodi
function Balance-ClusterGroups {
    param([string]$ClusterName = ".")

    $nodes = Get-ClusterNode -Cluster $ClusterName | Where-Object State -eq "Up"
    $groups = Get-ClusterGroup -Cluster $ClusterName |
        Where-Object State -eq "Online"

    $targetPerNode = [math]::Ceiling($groups.Count / $nodes.Count)

    $nodeLoad = @{}
    foreach ($node in $nodes) { $nodeLoad[$node.Name] = 0 }
    foreach ($group in $groups) { $nodeLoad[$group.OwnerNode.Name]++ }

    foreach ($group in $groups) {
        $currentNode = $group.OwnerNode.Name
        if ($nodeLoad[$currentNode] -gt $targetPerNode) {
            $leastLoadedNode = $nodeLoad.GetEnumerator() |
                Sort-Object Value | Select-Object -First 1

            if ($leastLoadedNode.Value -lt $targetPerNode) {
                Write-Output "Moving $($group.Name): $currentNode → $($leastLoadedNode.Key)"
                Move-ClusterGroup -Name $group.Name -Node $leastLoadedNode.Key
                $nodeLoad[$currentNode]--
                $nodeLoad[$leastLoadedNode.Key]++
            }
        }
    }
}

# Script: Export completo della configurazione del cluster per DR
function Export-ClusterConfiguration {
    param(
        [string]$ClusterName = ".",
        [string]$OutputPath = "C:\ClusterBackup\$(Get-Date -Format 'yyyyMMdd-HHmm')"
    )

    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null

    Get-Cluster -Name $ClusterName | Export-Clixml "$OutputPath\cluster.xml"
    Get-ClusterNode -Cluster $ClusterName | Export-Clixml "$OutputPath\nodes.xml"
    Get-ClusterGroup -Cluster $ClusterName | Export-Clixml "$OutputPath\groups.xml"
    Get-ClusterResource -Cluster $ClusterName | Export-Clixml "$OutputPath\resources.xml"
    Get-ClusterNetwork -Cluster $ClusterName | Export-Clixml "$OutputPath\networks.xml"
    Get-ClusterQuorum -Cluster $ClusterName | Export-Clixml "$OutputPath\quorum.xml"
    Get-ClusterSharedVolume -Cluster $ClusterName -ErrorAction SilentlyContinue |
        Export-Clixml "$OutputPath\csv.xml"

    # Export dei parametri di ogni risorsa
    Get-ClusterResource -Cluster $ClusterName | ForEach-Object {
        $params = Get-ClusterParameter -InputObject $_ -ErrorAction SilentlyContinue
        if ($params) {
            $params | Export-Csv "$OutputPath\params-$($_.Name -replace '[^\w]','_').csv" -NoTypeInformation
        }
    }

    # Export del cluster log
    Get-ClusterLog -Cluster $ClusterName -Destination $OutputPath -TimeSpan 1440

    Write-Output "Configurazione esportata in: $OutputPath"
}

# Cmdlet FailoverClusters — riferimento rapido
# Get-Command -Module FailoverClusters | Measure-Object → circa 100+ cmdlet
#
# Più usati:
# Get-Cluster, Get-ClusterNode, Get-ClusterGroup, Get-ClusterResource
# Move-ClusterGroup, Suspend-ClusterNode, Resume-ClusterNode
# Add-ClusterNode, Remove-ClusterNode
# Set-ClusterQuorum, Get-ClusterQuorum
# Test-Cluster, Get-ClusterLog
# Add-ClusterSharedVolume, Get-ClusterSharedVolume
# Invoke-CauRun, Get-CauRun
```

---

## Monitoraggio e Diagnostica

### Cluster Events e Cluster Log

Il cluster genera eventi dettagliati in due fonti principali: i canali Event Log di Windows e il Cluster Log dedicato.

```powershell
# Event Log canali del cluster:
# - Microsoft-Windows-FailoverClustering/Operational (principale)
# - Microsoft-Windows-FailoverClustering/Diagnostic (debug)
# - Microsoft-Windows-FailoverClustering-Client/Diagnostic (CSV)

# Event ID critici da monitorare:
$criticalEvents = @{
    1069 = "Risorsa cluster in stato failed"
    1135 = "Nodo rimosso dalla membership del cluster"
    1146 = "Impossibile portare online una risorsa"
    1177 = "Quorum perso"
    1205 = "Cluster service arrestato per quorum loss"
    1222 = "Risorsa Network Name fallita"
    1230 = "Risorsa Physical Disk fallita"
    1254 = "Nodo in isolamento dal cluster"
    1560 = "Quorum witness non raggiungibile"
    4870 = "CSV in redirected I/O"
    4871 = "CSV ritornato a Direct I/O"
    5120 = "CSV non accessibile — volume offline"
    5142 = "CSV timeout accesso rete"
}

# Monitorare gli eventi critici delle ultime 24 ore
$events = Get-WinEvent -LogName "Microsoft-Windows-FailoverClustering/Operational" `
    -MaxEvents 500 -ErrorAction SilentlyContinue |
    Where-Object {
        $_.LevelDisplayName -in "Error","Critical","Warning" -and
        $_.TimeCreated -gt (Get-Date).AddHours(-24)
    }

$events | Select-Object TimeCreated, LevelDisplayName, Id,
    @{N="Description";E={$criticalEvents[[int]$_.Id]}} |
    Format-Table -AutoSize -Wrap

# Generare il Cluster Log (debug dettagliato)
Get-ClusterLog -Destination "C:\ClusterDiag" -TimeSpan 60 -UseLocalTime

# Generare log con livello di dettaglio massimo
Get-ClusterLog -Destination "C:\ClusterDiag" -TimeSpan 30 `
    -UseLocalTime -Level 5  # Level 5 = massimo dettaglio

# Analizzare il log per eventi di membership
Select-String -Path "C:\ClusterDiag\NODE01_cluster.log" `
    -Pattern "regroup|membership|heartbeat|quorum" -AllMatches |
    Select-Object -First 50 LineNumber, Line
```

### Performance Monitor per Cluster

```powershell
# Contatori chiave per il monitoraggio delle performance del cluster
$clusterCounters = @(
    # CSV File System
    "\Cluster CSV File System(_Total)\Reads/sec"
    "\Cluster CSV File System(_Total)\Writes/sec"
    "\Cluster CSV File System(_Total)\Read Latency"
    "\Cluster CSV File System(_Total)\Write Latency"
    # CSV Volume Cache
    "\Cluster CSV Volume Cache(_Total)\Cache Hit %"
    "\Cluster CSV Volume Cache(_Total)\Cache Miss %"
    # Cluster Network
    "\Cluster Network Messages(_Total)\Messages Sent/sec"
    "\Cluster Network Messages(_Total)\Messages Received/sec"
    "\Cluster Network Messages(_Total)\Bytes Sent/sec"
    "\Cluster Network Messages(_Total)\Bytes Received/sec"
)

# Catturare 1 minuto di dati
$data = Get-Counter -Counter $clusterCounters -SampleInterval 5 -MaxSamples 12

# Calcolare le medie
$data.CounterSamples | Group-Object Path | ForEach-Object {
    [PSCustomObject]@{
        Counter = ($_.Name -split '\\')[-1]
        Average = [math]::Round(($_.Group.CookedValue | Measure-Object -Average).Average, 2)
        Maximum = [math]::Round(($_.Group.CookedValue | Measure-Object -Maximum).Maximum, 2)
    }
} | Format-Table -AutoSize

# Alert se la latenza CSV supera la soglia
$threshold_ms = 20
$latency = (Get-Counter "\Cluster CSV File System(_Total)\Write Latency").CounterSamples[0].CookedValue
if ($latency -gt $threshold_ms) {
    Write-Warning "CSV Write Latency: ${latency}ms (soglia: ${threshold_ms}ms)"
}
```

### Integrazione System Center

System Center Operations Manager (SCOM) e System Center Virtual Machine Manager (SCVMM) forniscono il monitoraggio centralizzato e la gestione dei cluster in ambienti enterprise multi-cluster.

```powershell
# SCOM: i Management Pack per Failover Clustering monitorano:
# - Stato dei nodi e del quorum
# - Health delle risorse e dei gruppi
# - CSV performance e redirected I/O
# - S2D health e disk status
# - Failover events e alert

# SCVMM: gestione centralizzata dei cluster Hyper-V
# - Provisioning VM su cluster
# - Live Migration tra cluster
# - Placement intelligente basato su load balancing
# - Integration con Azure per hybrid cloud

# Windows Admin Center fornisce un'alternativa gratuita per:
# - Dashboard cluster in tempo reale
# - Gestione VM e storage
# - CAU integrato
# - Integrazione Azure Monitor e Azure Backup
```

---

## Disaster Recovery del Cluster

### Backup della Configurazione Cluster

```powershell
# Backup completo della configurazione del cluster
# Metodo 1: Export via PowerShell (per ricostruzione manuale)
Export-ClusterConfiguration  # Funzione definita nella sezione PowerShell sopra

# Metodo 2: Windows Server Backup del System State
# Include il cluster hive e la configurazione
wbadmin start systemstatebackup -backupTarget:E: -quiet

# Metodo 3: Backup del registry hive (più veloce, meno completo)
reg save "HKLM\Cluster" "\\backup\cluster-hive-$(Get-Date -Format yyyyMMdd).dat" /y

# Metodo 4: Backup Authoritative del cluster (per ripristino completo)
# Eseguire su un nodo attivo del cluster
$backupPath = "\\backup\ClusterBackup\$(Get-Date -Format yyyyMMdd)"
New-Item -ItemType Directory -Path $backupPath -Force | Out-Null

# Esportare TUTTA la configurazione
Get-Cluster | ConvertTo-Json -Depth 5 | Out-File "$backupPath\cluster-config.json"
Get-ClusterNode | ConvertTo-Json -Depth 5 | Out-File "$backupPath\nodes-config.json"
Get-ClusterGroup | ForEach-Object {
    $group = $_
    $resources = Get-ClusterResource -Group $_.Name
    $params = $resources | ForEach-Object {
        @{
            ResourceName = $_.Name
            Parameters = (Get-ClusterParameter -InputObject $_ -ErrorAction SilentlyContinue)
        }
    }
    @{
        GroupName = $group.Name
        GroupType = $group.GroupType
        Priority = $group.Priority
        FailoverThreshold = $group.FailoverThreshold
        Resources = $params
    }
} | ConvertTo-Json -Depth 10 | Out-File "$backupPath\groups-detail.json"

# Programmare il backup giornaliero
# Aggiungere come Scheduled Task su un nodo del cluster
```

### Rebuild del Cluster

Procedura per ricostruire un cluster da zero dopo un disastro completo.

```powershell
# Procedura di rebuild del cluster:
#
# 1. Installare Windows Server sui nuovi nodi
# 2. Unire i nodi al dominio AD
# 3. Installare la feature Failover Clustering
Install-WindowsFeature -Name Failover-Clustering -IncludeManagementTools -Restart

# 4. Validare la configurazione
Test-Cluster -Node "NEW-NODE01","NEW-NODE02" `
    -Include "Storage","Network","System Configuration"

# 5. Creare il nuovo cluster con lo stesso nome e IP (se possibile)
New-Cluster -Name "CLUSTER01" -Node "NEW-NODE01","NEW-NODE02" `
    -StaticAddress "10.0.1.100" -NoStorage

# 6. Riconfigurare il quorum
Set-ClusterQuorum -CloudWitness -AccountName "witnessaccount" -AccessKey "key"

# 7. Aggiungere lo storage
Get-ClusterAvailableDisk | Add-ClusterDisk
Add-ClusterSharedVolume -Name "Cluster Disk 1"

# 8. Riconfigurare i ruoli (dal backup della configurazione)
# Ripristinare le VM dal backup e renderle altamente disponibili
Get-VM | Add-ClusterVirtualMachineRole

# 9. Ripristinare le reti
# (configurazione manuale basata sui dati di backup)

# 10. Verificare il cluster ricostruito
Get-ClusterNode | Select-Object Name, State
Get-ClusterGroup | Select-Object Name, State, OwnerNode
Get-ClusterSharedVolume | Select-Object Name, State
```

### Hyper-V Replica e Cluster

Hyper-V Replica fornisce la replica asincrona delle VM tra cluster, complementare al failover clustering per il disaster recovery cross-site.

```powershell
# Configurare Hyper-V Replica Broker nel cluster
# Il Broker è un ruolo cluster che gestisce la replica per il cluster intero
Add-ClusterServerRole -StaticAddress "10.0.1.110" -Name "HV-Replica-Broker"

# Abilitare la replica sul cluster
Set-VMReplicationServer -ReplicationEnabled $true `
    -AllowedAuthenticationType Kerberos `
    -KerberosAuthenticationPort 80 `
    -DefaultStorageLocation "C:\ClusterStorage\Volume-Replica"

# Configurare la replica di una VM verso il cluster DR
Enable-VMReplication -VMName "VM-CriticalApp" `
    -ReplicaServerName "DR-CLUSTER-BROKER.contoso.com" `
    -ReplicaServerPort 80 `
    -AuthenticationType Kerberos `
    -ReplicationFrequencySec 300  # Replica ogni 5 minuti

# Avviare la replica iniziale
Start-VMInitialReplication -VMName "VM-CriticalApp" `
    -DestinationPath "C:\ClusterStorage\Volume-Replica"

# In caso di disaster: failover pianificato
# (eseguire sul cluster DR)
Start-VMFailover -VMName "VM-CriticalApp" -Prepare  # Sul cluster primario
Start-VMFailover -VMName "VM-CriticalApp"            # Sul cluster DR
Complete-VMFailover -VMName "VM-CriticalApp"         # Conferma

# Verificare lo stato della replica
Get-VMReplication | Select-Object VMName, State, Health,
    ReplicationMode, FrequencySec, LastReplicationTime |
    Format-Table -AutoSize
```

---

## Sicurezza del Cluster

### CNO e VCO — Oggetti Computer in AD

Quando si crea un cluster, vengono creati oggetti computer in Active Directory:

```
Oggetti AD del Cluster:

┌──────────────────────────────────────────────┐
│ Active Directory                              │
│                                               │
│  CNO (Cluster Name Object)                    │
│  ├── CLUSTER01$ (account computer del cluster)│
│  ├── Creato automaticamente alla creazione    │
│  ├── Deve avere permessi per creare VCO       │
│  └── Risiede nella OU dei computer o custom   │
│                                               │
│  VCO (Virtual Computer Object)                │
│  ├── FS-Cluster$ (file server cluster)        │
│  ├── SQL-AG$ (SQL availability group)         │
│  ├── Creato dal CNO quando si aggiunge un ruolo│
│  └── Il CNO deve avere "Create Computer Object"│
│       nella OU target                          │
└──────────────────────────────────────────────┘
```

```powershell
# Verificare il CNO in AD
Get-ADComputer "CLUSTER01" -Properties * |
    Select-Object Name, DistinguishedName, Enabled,
    ServicePrincipalName, Created

# Pre-creare il CNO (approccio consigliato per sicurezza)
# 1. Creare l'account computer in AD
New-ADComputer -Name "CLUSTER01" -Path "OU=Cluster,DC=contoso,DC=com" -Enabled $false

# 2. Assegnare i permessi necessari
# - L'utente che crea il cluster deve avere "Full Control" sul CNO
# - Il CNO deve avere "Create Computer Objects" nella OU per creare VCO

# Verificare i VCO
Get-ADComputer -Filter { ServicePrincipalName -like "*CLUSTER01*" } |
    Select-Object Name, DistinguishedName, Enabled

# Verificare i permessi dell'OU per il CNO
$ou = "OU=Cluster,DC=contoso,DC=com"
(Get-Acl "AD:\$ou").Access |
    Where-Object IdentityReference -like "*CLUSTER01*" |
    Select-Object IdentityReference, ActiveDirectoryRights, ObjectType
```

### Kerberos Authentication e Constrained Delegation

```powershell
# I cluster usano Kerberos per l'autenticazione tra nodi e con i client
# Il CNO e i VCO registrano SPN (Service Principal Names) automaticamente

# Verificare i SPN del cluster
setspn -L CLUSTER01

# Per servizi che richiedono delegazione (es. SQL Server)
# Configurare la constrained delegation
Set-ADComputer -Identity "SQL-AG" -TrustedForDelegation $false
Set-ADComputer -Identity "SQL-AG" `
    -Add @{'msDS-AllowedToDelegateTo' = 'MSSQLSvc/NODE01.contoso.com:1433','MSSQLSvc/NODE02.contoso.com:1433'}

# Verificare la delegazione
Get-ADComputer "SQL-AG" -Properties 'msDS-AllowedToDelegateTo','TrustedForDelegation' |
    Select-Object Name, TrustedForDelegation, 'msDS-AllowedToDelegateTo'
```

### Cluster Hardening

```powershell
# Checklist di hardening per cluster di produzione

# 1. Limitare l'accesso al cluster
# Solo gli amministratori del cluster devono avere permessi
Get-ClusterAccess | Select-Object Identity, AccessControlType, ClusterRights

# Aggiungere un utente come amministratore del cluster
Grant-ClusterAccess -User "CONTOSO\ClusterAdmins" -Full

# 2. Crittografare la comunicazione del cluster
# Abilitare la crittografia SMB per il traffico cluster
Set-SmbServerConfiguration -EncryptData $true -Force

# 3. Firewalling
# Porte necessarie per il cluster:
# TCP/UDP 3343 — Cluster communication
# TCP 135 — RPC endpoint mapper
# TCP 445 — SMB (per CSV e file share)
# TCP 5985/5986 — WinRM (per gestione remota)
# UDP 3343 — Cluster heartbeat

# 4. Protezione del quorum witness
# Cloud Witness: usare un storage account con firewall Azure configurato
# File Share Witness: permessi minimi (solo il CNO in lettura/scrittura)
# Disk Witness: disco piccolo (1GB), NTFS, non condiviso con altri dati

# 5. Audit delle azioni sul cluster
# Abilitare l'auditing nel security log per gli oggetti AD del cluster
Set-ADComputer "CLUSTER01" -Replace @{
    'msDS-AllowedToActOnBehalfOfOtherIdentity' = $null
}

# 6. Verificare regolarmente le vulnerabilità
Test-Cluster -Node (Get-ClusterNode).Name `
    -Include "System Configuration" -Verbose
```

---

## Migrazione e Upgrade

### Cluster OS Rolling Upgrade

Il Cluster OS Rolling Upgrade permette di aggiornare la versione di Windows Server dei nodi del cluster senza downtime, migrando i workload nodo per nodo.

```
Processo Rolling Upgrade:

Stato iniziale:
  Node1: Windows Server 2019 ← VM attive
  Node2: Windows Server 2019 ← VM attive
  Node3: Windows Server 2019 ← VM attive
  Cluster Functional Level: 2019

Step 1: Evict + Upgrade Node3
  Node1: WS 2019 ← VM di Node3 migrate qui
  Node2: WS 2019 ← VM di Node3 migrate qui
  Node3: WS 2022 (fresh install) → rejoin cluster
  Cluster: Mixed Mode (2019 + 2022)

Step 2: Evict + Upgrade Node2
  Node1: WS 2019 ← VM migrate
  Node2: WS 2022 → rejoin cluster
  Node3: WS 2022

Step 3: Evict + Upgrade Node1
  Node1: WS 2022 → rejoin cluster
  Node2: WS 2022
  Node3: WS 2022
  Cluster: Still at WS 2019 level

Step 4: Update Cluster Functional Level
  Update-ClusterFunctionalLevel
  Cluster Functional Level: 2022 ← IRREVERSIBILE
```

```powershell
# Procedura passo per passo:

# 1. Verificare il livello funzionale attuale
Get-Cluster | Select-Object Name, ClusterFunctionalLevel

# 2. Evitare il nodo da aggiornare (drain dei ruoli)
Suspend-ClusterNode -Name "NODE03" -Drain -Wait -ForceDrain

# 3. Rimuovere il nodo dal cluster
Remove-ClusterNode -Name "NODE03" -Force

# 4. Reinstallare Windows Server (nuova versione) su NODE03
# (processo manuale di installazione del SO)

# 5. Installare Failover Clustering sul nodo aggiornato
Install-WindowsFeature -Name Failover-Clustering -IncludeManagementTools -Restart

# 6. Aggiungere il nodo al cluster (in mixed mode)
Add-ClusterNode -Cluster "CLUSTER01" -Name "NODE03"

# 7. Ripetere per ogni nodo (2 → 1)

# 8. Dopo che TUTTI i nodi sono aggiornati:
# Aggiornare il livello funzionale del cluster (IRREVERSIBILE)
Update-ClusterFunctionalLevel -Force

# 9. Verificare il nuovo livello
Get-Cluster | Select-Object Name, ClusterFunctionalLevel

# 10. Aggiornare anche il livello funzionale di S2D (se applicabile)
Update-StoragePool -FriendlyName "S2D on CLUSTER01"
```

### Cross-Cluster Migration

La migrazione di workload tra cluster diversi (es. da un cluster legacy a uno nuovo) richiede un approccio diverso.

```powershell
# Migrazione di VM tra cluster (via export/import)
# 1. Esportare la VM dal cluster sorgente
Export-VM -Name "VM-App01" -Path "\\nas\Migration"

# 2. Sul cluster destinazione, importare la VM
Import-VM -Path "\\nas\Migration\VM-App01\Virtual Machines\*.vmcx" `
    -Copy -GenerateNewId `
    -VhdDestinationPath "C:\ClusterStorage\Volume1\VMs\VM-App01" `
    -VirtualMachinePath "C:\ClusterStorage\Volume1\VMs\VM-App01"

# 3. Rendere la VM altamente disponibile nel nuovo cluster
Add-ClusterVirtualMachineRole -VMName "VM-App01"

# Migrazione live (cluster nello stesso dominio, Windows Server 2016+)
# Cross-cluster live migration via Shared Nothing
Move-VM -Name "VM-App01" `
    -DestinationHost "NEW-NODE01.contoso.com" `
    -DestinationStoragePath "C:\ClusterStorage\Volume1\VMs\VM-App01" `
    -IncludeStorage
# Poi rendere HA nel nuovo cluster:
Add-ClusterVirtualMachineRole -VMName "VM-App01"
```

---

## Storage Spaces Direct (S2D)

Storage Spaces Direct (S2D) è la soluzione hyper-converged di Microsoft che aggrega lo storage locale (dischi interni) dei nodi del cluster in un pool di storage distribuito, eliminando la necessità di una SAN esterna.

```
Architettura S2D:
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ Node 1  │  │ Node 2  │  │ Node 3  │  │ Node 4  │
│         │  │         │  │         │  │         │
│ NVMe    │  │ NVMe    │  │ NVMe    │  │ NVMe    │
│ SSD     │  │ SSD     │  │ SSD     │  │ SSD     │
│ HDD     │  │ HDD     │  │ HDD     │  │ HDD     │
└────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
     │            │            │            │
     └────────────┴────────────┴────────────┘
              RDMA Network (25-100 GbE)
                        │
              ┌─────────┴─────────┐
              │   Storage Pool     │
              │   (tutti i dischi  │
              │    aggregati)      │
              └─────────┬─────────┘
              ┌─────────┴─────────┐
              │  Virtual Disks     │
              │  (3-way mirror,    │
              │   mirror-parity)   │
              └─────────┬─────────┘
              ┌─────────┴─────────┐
              │  CSV Volumes       │
              │  (accessibili da   │
              │   tutti i nodi)    │
              └───────────────────┘
```

```powershell
# Abilitare Storage Spaces Direct (dopo aver creato il cluster)
Enable-ClusterStorageSpacesDirect -Confirm:$false

# Verificare il pool di storage
Get-StoragePool -IsPrimordial $false | Select-Object FriendlyName, HealthStatus,
    OperationalStatus, Size, AllocatedSize

# Creare un volume con 3-way mirror (resilienza: tollera 2 failure)
New-Volume -FriendlyName "VMStorage" `
    -StoragePoolFriendlyName "S2D on CLUSTER01" `
    -Size 1TB `
    -ResiliencySettingName Mirror `
    -NumberOfDataCopies 3 `
    -ProvisioningType Thin `
    -FileSystem CSVFS_ReFS

# Verificare i volumi
Get-VirtualDisk | Select-Object FriendlyName, HealthStatus, OperationalStatus,
    ResiliencySettingName, Size, FootprintOnPool

# Monitorare la salute dello storage
Get-StorageSubSystem -FriendlyName *Cluster* | Get-StorageHealthReport
```

### Cache Tier e Capacity Tier

S2D utilizza un modello a due livelli: i dischi più veloci (NVMe o SSD) fungono da cache, mentre i dischi più lenti (SSD o HDD) forniscono la capacità. La cache è trasparente e automatica.

```
Combinazioni di dischi S2D:

Configurazione        Cache Tier    Capacity Tier    Uso Tipico
──────────────────    ──────────    ─────────────    ─────────────────
All-NVMe              Nessuno*      NVMe             Performance massima
NVMe + SSD            NVMe          SSD              Bilanciato
NVMe + HDD            NVMe          HDD              Capacità con cache rapida
SSD + HDD             SSD           HDD              Economico, buone letture
All-SSD               Nessuno*      SSD              Buono per la maggior parte
All-HDD               NON supportato                 Non usare

* Con tipi di disco identici, non c'è tier separato per la cache.
  S2D usa la cache in-memory del sistema operativo.
```

```powershell
# Verificare quali dischi sono usati come cache e quali come capacità
Get-PhysicalDisk | Select-Object FriendlyName, MediaType, Usage, Size,
    HealthStatus, OperationalStatus | Sort-Object Usage, MediaType |
    Format-Table -AutoSize

# Usage: "Auto-Select" = S2D decide, "Journal" = cache, "Retired" = rimosso

# Verificare il rapporto cache/capacità
$cache = Get-PhysicalDisk | Where-Object Usage -eq "Journal"
$capacity = Get-PhysicalDisk | Where-Object Usage -eq "Auto-Select"
Write-Output "Cache disks: $($cache.Count), Capacity disks: $($capacity.Count)"
Write-Output "Cache size: $([math]::Round(($cache | Measure-Object Size -Sum).Sum / 1TB, 2)) TB"
Write-Output "Capacity size: $([math]::Round(($capacity | Measure-Object Size -Sum).Sum / 1TB, 2)) TB"

# Raccomandazione: rapporto cache/capacità = almeno il 10% della capacità totale
```

### Fault Domain e Resilienza

I fault domain definiscono i confini di failure in S2D. I dati vengono distribuiti tra i fault domain per garantire la sopravvivenza a failure simultanee.

```
Gerarchia dei Fault Domain:

Site (optional)
├── Rack (optional)
│   ├── Chassis (optional)
│   │   ├── Node1
│   │   │   ├── NVMe-01 (cache)
│   │   │   ├── SSD-01 (capacity)
│   │   │   └── SSD-02 (capacity)
│   │   └── Node2
│   │       ├── NVMe-02 (cache)
│   │       ├── SSD-03 (capacity)
│   │       └── SSD-04 (capacity)
│   └── Chassis 2
│       ├── Node3
│       └── Node4
└── Rack 2
    └── ...

Resilienza per numero di nodi:
  2 nodi:  2-way mirror                    Tollera 1 nodo
  3 nodi:  3-way mirror                    Tollera 1 nodo (2 copie rimangono)
  4+ nodi: 3-way mirror o mirror+parity    Tollera 2 nodi
  7+ nodi: mirror+parity + erasure coding  Tollera 2 nodi, più efficiente
```

```powershell
# Configurare la gerarchia dei fault domain
New-ClusterFaultDomain -Name "Rack-A" -Type Rack
New-ClusterFaultDomain -Name "Rack-B" -Type Rack

Set-ClusterFaultDomain -Name "NODE01" -Parent "Rack-A"
Set-ClusterFaultDomain -Name "NODE02" -Parent "Rack-A"
Set-ClusterFaultDomain -Name "NODE03" -Parent "Rack-B"
Set-ClusterFaultDomain -Name "NODE04" -Parent "Rack-B"

# Verificare la topologia
Get-ClusterFaultDomainXML

# Creare un volume con resilienza specifica
# 3-way mirror (per massima resilienza, 3 copie)
New-Volume -FriendlyName "CriticalData" `
    -StoragePoolFriendlyName "S2D on CLUSTER01" `
    -Size 500GB `
    -ResiliencySettingName Mirror `
    -NumberOfDataCopies 3

# Mirror-accelerated parity (migliore efficienza storage, 4+ nodi)
New-Volume -FriendlyName "ArchiveData" `
    -StoragePoolFriendlyName "S2D on CLUSTER01" `
    -Size 2TB `
    -ResiliencySettingName Parity `
    -PhysicalDiskRedundancy 2

# Verificare l'efficienza dello storage
Get-VirtualDisk | Select-Object FriendlyName, ResiliencySettingName,
    @{N="SizeGB";E={[math]::Round($_.Size/1GB,1)}},
    @{N="FootprintGB";E={[math]::Round($_.FootprintOnPool/1GB,1)}},
    @{N="Efficiency";E={
        [math]::Round($_.Size / $_.FootprintOnPool * 100, 1)
    }} | Format-Table -AutoSize
```

### Pool Management e Manutenzione Dischi

```powershell
# Sostituire un disco guasto in S2D
# 1. Identificare il disco guasto
Get-PhysicalDisk | Where-Object HealthStatus -ne "Healthy" |
    Select-Object FriendlyName, SerialNumber, HealthStatus,
    OperationalStatus, Size, SlotNumber

# 2. Ritirare il disco (S2D inizia a ricostruire i dati su altri dischi)
Set-PhysicalDisk -FriendlyName "PhysicalDisk-Guasto" -Usage Retired

# 3. Verificare lo stato della ricostruzione
Get-VirtualDisk | Select-Object FriendlyName, HealthStatus,
    OperationalStatus, @{N="RepairPct";E={$_.OperationalStatus}}

# 4. Rimuovere fisicamente il disco e inserire il sostitutivo
# S2D rileva automaticamente il nuovo disco e lo aggiunge al pool

# Aggiungere manualmente un disco al pool
$disk = Get-PhysicalDisk -CanPool $true
Add-PhysicalDisk -StoragePoolFriendlyName "S2D on CLUSTER01" -PhysicalDisks $disk

# Monitorare lo stato del pool in tempo reale
Get-StoragePool -IsPrimordial $false |
    Select-Object FriendlyName, HealthStatus, OperationalStatus,
    @{N="SizeTB";E={[math]::Round($_.Size/1TB,2)}},
    @{N="AllocatedTB";E={[math]::Round($_.AllocatedSize/1TB,2)}},
    @{N="FreePct";E={[math]::Round(($_.Size - $_.AllocatedSize) / $_.Size * 100, 1)}}

# Verificare la distribuzione dei dati per nodo
Get-StorageNode | ForEach-Object {
    $node = $_.Name
    $disks = Get-PhysicalDisk -StorageNode $_ | Where-Object Usage -ne "Retired"
    [PSCustomObject]@{
        Node = $node
        DiskCount = $disks.Count
        TotalTB = [math]::Round(($disks | Measure-Object Size -Sum).Sum / 1TB, 2)
    }
} | Format-Table -AutoSize
```

---

## Best Practices

**Usare sempre Cloud Witness per il quorum:** Il Cloud Witness è la scelta più affidabile per la maggior parte degli scenari. Non richiede infrastruttura aggiuntiva, è resiliente alle failure del datacenter e costa pochi centesimi al mese su Azure.

**Rete dedicata per il heartbeat:** Mai condividere la rete di heartbeat del cluster con il traffico client o storage. Un'interferenza sulla rete di heartbeat può causare failover spurii. Usare almeno 10 GbE per il heartbeat.

**Validare sempre prima di creare o modificare:** Il Cluster Validation Wizard (`Test-Cluster`) deve essere eseguito e passare senza errori prima di creare il cluster e prima di aggiungere nuovi nodi. I warning devono essere investigati e documentati.

**Configurare il failback automatico con cautela:** Il failback automatico (spostamento dei ruoli sul nodo originale dopo che torna online) può causare interruzioni aggiuntive. Se configurato, limitarlo a finestre di manutenzione notturne.

**Non sovraccaricare i nodi:** Pianificare la capacità in modo che ogni nodo possa ospitare il workload di un nodo aggiuntivo in caso di failure. In un cluster a 2 nodi, ogni nodo deve poter gestire il 100% del workload totale. In un cluster a 4 nodi, almeno il 33% extra per nodo.

**Usare CAU per gli aggiornamenti:** Non aggiornare mai i nodi del cluster manualmente uno alla volta. CAU automatizza il processo e garantisce che i ruoli vengano migrati correttamente prima dell'aggiornamento.

**Pianificare la capacità per N+1:** In un cluster di produzione, la capacità totale deve essere sufficiente a gestire il workload completo anche con un nodo in meno (manutenzione o failure). Questo significa che un cluster a 3 nodi dove ogni nodo è al 90% di utilizzo non ha margine per il failover. Pianificare con un massimo del 60-70% di utilizzo per nodo in un cluster a 3 nodi, garantendo che il carico possa essere ridistribuito senza degradazione.

**Monitorare costantemente:** Implementare monitoring con alert per: nodo down, failover avvenuto, risorsa failed, CSV in redirected mode, quorum degradato. Un singolo nodo down in un cluster a 2 nodi significa che il prossimo failure causerà downtime.

---

## Troubleshooting

### Problema: Nodo Si Disconnette dal Cluster Periodicamente

**Sintomi**: Un nodo viene espulso dal cluster e poi si riunisce dopo pochi minuti. Gli eventi nel Cluster Log mostrano heartbeat mancati.

**Causa**: Problemi di rete (packet loss, latenza alta, NIC failure intermittente), CPU al 100% sul nodo che impedisce l'elaborazione degli heartbeat, oppure driver NIC problematici.

**Soluzione**:

```powershell
# Analizzare il Cluster Log
Get-ClusterLog -Destination "C:\ClusterLogs" -TimeSpan 60  # Ultimi 60 minuti

# Cercare eventi di heartbeat nel log
Get-WinEvent -LogName "Microsoft-Windows-FailoverClustering/Operational" -MaxEvents 100 |
    Where-Object { $_.Id -in 1135, 1177, 1069 } |
    Select-Object TimeCreated, Id, Message | Format-Table -Wrap

# Event IDs chiave:
# 1135 = Node removed from cluster membership
# 1177 = Quorum lost
# 1069 = Resource failed

# Verificare la connettività di rete tra i nodi
Test-Connection -ComputerName "NODE02" -Count 100 |
    Where-Object { $_.StatusCode -ne 0 } | Measure-Object
# Qualsiasi packet loss è un problema per il cluster

# Aumentare la tolleranza del heartbeat (se la rete è WAN)
(Get-Cluster).SameSubnetDelay = 2000       # ms tra heartbeat (default: 1000)
(Get-Cluster).SameSubnetThreshold = 10     # heartbeat mancati prima di failure (default: 5)
(Get-Cluster).CrossSubnetDelay = 4000      # per cluster multi-site
(Get-Cluster).CrossSubnetThreshold = 20
```

### Problema: CSV in Redirected I/O Mode

**Sintomi**: Le prestazioni I/O sullo storage CSV sono drasticamente ridotte. `Get-ClusterSharedVolumeState` mostra `BlockRedirectedIOReason` diverso da "None".

**Causa**: Il nodo proprietario del CSV non è raggiungibile direttamente dallo storage, quindi l'I/O viene instradato tramite un altro nodo via SMB. Cause: path di storage interrotto, disco offline sul nodo owner, o failover in corso.

**Soluzione**:

```powershell
# Verificare lo stato di redirected I/O
Get-ClusterSharedVolumeState | Where-Object StateInfo -eq "FileSystemRedirected" |
    Select-Object Name, Node, StateInfo, BlockRedirectedIOReason

# Verificare i path di storage
mpclaim -s -d  # Mostra i path multipath

# Riparare un CSV che non torna in Direct I/O
# Spostare la ownership e ritornare
$csvName = "Cluster Virtual Disk (Volume1)"
Move-ClusterSharedVolume -Name $csvName -Node "NODE02"
Start-Sleep -Seconds 10
Move-ClusterSharedVolume -Name $csvName -Node "NODE01"

# Se il disco è offline sul nodo
Get-Disk | Where-Object { $_.OperationalStatus -eq "Offline" } | Set-Disk -IsOffline $false
```

### Problema: Failover Non Avviene — Risorsa Resta in Stato Failed

**Sintomi**: Un ruolo cluster va in stato "Failed" ma non viene migrato su un altro nodo. L'applicazione è in downtime.

**Causa**: Il ruolo ha raggiunto il limite di failover configurato (`FailoverThreshold`), oppure nessun altro nodo è in grado di ospitare il ruolo (risorse insufficienti o preferred owner non disponibile).

**Soluzione**:

```powershell
# Verificare lo stato del gruppo e i possible owners
$group = Get-ClusterGroup "RuoloFallito"
$group | Format-List Name, State, OwnerNode, FailoverPeriod, FailoverThreshold

# Verificare i possible owners
Get-ClusterOwnerNode -Group "RuoloFallito"

# Forzare il failover manualmente
Move-ClusterGroup "RuoloFallito" -Node "NODE02" -Force

# Se il ruolo resta in Failed, riavviare il servizio cluster sul nodo problematico
# e riprovare il start del gruppo
Start-ClusterGroup "RuoloFallito"

# Reset del contatore di failover
$group.FailoverThreshold = 10  # Aumentare temporaneamente
Start-ClusterGroup "RuoloFallito"
```

---

## Stretch Cluster e Multi-Site Clustering

Un stretch cluster (o cluster multi-sito) estende il failover clustering su due o più datacenter geograficamente separati, fornendo protezione contro il disastro di un intero sito. Questo approccio richiede una pianificazione attenta della latenza di rete, della replica dello storage e della configurazione del quorum.

### Requisiti di Rete

La latenza tra i siti deve essere inferiore a 5 millisecondi (round-trip) per garantire il funzionamento corretto del heartbeat del cluster e della replica sincrona dello storage. Per latenze superiori, è necessario utilizzare la replica asincrona, accettando un potenziale RPO (Recovery Point Objective) maggiore di zero.

```powershell
# Configurare i parametri di rete per stretch cluster
(Get-Cluster).CrossSubnetDelay = 4000       # ms tra heartbeat cross-subnet
(Get-Cluster).CrossSubnetThreshold = 20     # heartbeat mancati prima di failure
(Get-Cluster).SameSubnetDelay = 2000        # ms tra heartbeat same-subnet
(Get-Cluster).SameSubnetThreshold = 10      # heartbeat mancati

# Configurare i siti del cluster (Windows Server 2016+)
New-ClusterFaultDomain -Name "Sito-Roma" -Type Site -Description "Datacenter Roma"
New-ClusterFaultDomain -Name "Sito-Milano" -Type Site -Description "Datacenter Milano DR"

# Assegnare i nodi ai siti
Set-ClusterFaultDomain -Name "NODE01" -Parent "Sito-Roma"
Set-ClusterFaultDomain -Name "NODE02" -Parent "Sito-Roma"
Set-ClusterFaultDomain -Name "NODE03" -Parent "Sito-Milano"
Set-ClusterFaultDomain -Name "NODE04" -Parent "Sito-Milano"

# Verificare la topologia dei fault domain
Get-ClusterFaultDomain | Select-Object Name, Type, ParentName | Format-Table -AutoSize

# Con Storage Replica per replica sincrona tra siti
New-SRPartnership -SourceComputerName "NODE01" -SourceRGName "RG-Roma" `
    -SourceVolumeName "C:\ClusterStorage\Volume1" `
    -SourceLogVolumeName "C:\ClusterStorage\LogVol1" `
    -DestinationComputerName "NODE03" -DestinationRGName "RG-Milano" `
    -DestinationVolumeName "C:\ClusterStorage\Volume2" `
    -DestinationLogVolumeName "C:\ClusterStorage\LogVol2" `
    -ReplicationMode Synchronous

# Verificare lo stato della replica
Get-SRPartnership | Select-Object SourceComputerName, DestinationComputerName,
    ReplicationMode, ReplicationStatus
Get-SRGroup | Get-SRPartnership | Select-Object -ExpandProperty Replicas |
    Select-Object DataVolume, ReplicationStatus, ReplicationMode
```

### Quorum per Stretch Cluster

Per uno stretch cluster a 4 nodi (2 per sito), il Cloud Witness è la scelta ideale per il quorum perché risiede in una terza location (Azure), eliminando il rischio di split-brain quando un intero sito diventa irraggiungibile.

```powershell
# Configurazione quorum raccomandata per stretch cluster
Set-ClusterQuorum -CloudWitness `
    -AccountName "clusterwitness" `
    -AccessKey "azure-storage-key" `
    -Endpoint "core.windows.net"

# Configurare la preferenza di sito per il failover
# I ruoli preferiscono restare nel sito primario
$group = Get-ClusterGroup "VM-CriticalApp"
$group | Set-ClusterParameter -Name "FailoverThreshold" -Value 5
$group | Set-ClusterParameter -Name "FailoverPeriod" -Value 6

# Configurare il preferred site
Set-ClusterFaultDomain -Name "Sito-Roma" -FaultDomainType Site -PreferredSite
```

## Monitoraggio Avanzato del Cluster

Un monitoring proattivo è essenziale per prevenire downtime non pianificati. I cluster generano eventi dettagliati che devono essere centralizzati e analizzati.

```powershell
# Script di monitoring completo per cluster
function Get-ClusterHealthDashboard {
    param([string]$ClusterName = ".")

    $cluster = Get-Cluster -Name $ClusterName
    $nodes = Get-ClusterNode -Cluster $ClusterName
    $groups = Get-ClusterGroup -Cluster $ClusterName
    $resources = Get-ClusterResource -Cluster $ClusterName
    $csvs = Get-ClusterSharedVolume -Cluster $ClusterName -ErrorAction SilentlyContinue
    $networks = Get-ClusterNetwork -Cluster $ClusterName

    # Stato dei nodi
    $nodeStatus = $nodes | ForEach-Object {
        [PSCustomObject]@{
            Node        = $_.Name
            State       = $_.State
            NodeWeight  = $_.NodeWeight
            StatusInfo  = $_.StatusInformation
        }
    }

    # Stato dei gruppi
    $groupStatus = $groups | ForEach-Object {
        [PSCustomObject]@{
            Group     = $_.Name
            State     = $_.State
            Owner     = $_.OwnerNode
            Priority  = $_.Priority
            AutoStart = $_.AutoFailbackType
        }
    }

    # Spazio CSV
    $csvSpace = $csvs | ForEach-Object {
        $info = $_.SharedVolumeInfo[0].Partition
        [PSCustomObject]@{
            CSV       = $_.Name
            SizeGB    = [math]::Round($info.Size / 1GB, 1)
            FreeGB    = [math]::Round($info.FreeSpace / 1GB, 1)
            UsedPct   = [math]::Round(($info.UsedSpace / $info.Size) * 100, 1)
            Owner     = $_.OwnerNode.Name
            State     = $_.State
        }
    }

    # Stato delle reti
    $networkStatus = $networks | ForEach-Object {
        [PSCustomObject]@{
            Network  = $_.Name
            State    = $_.State
            Role     = switch ($_.Role) { 0 {"None"} 1 {"ClusterOnly"} 3 {"ClusterAndClient"} }
            Address  = $_.Address
        }
    }

    # Eventi critici recenti
    $recentEvents = Get-WinEvent -LogName "Microsoft-Windows-FailoverClustering/Operational" `
        -MaxEvents 20 -ErrorAction SilentlyContinue |
        Where-Object { $_.LevelDisplayName -in "Error","Warning" } |
        Select-Object TimeCreated, LevelDisplayName, Id, Message

    # Output aggregato
    Write-Output "=== CLUSTER HEALTH DASHBOARD ==="
    Write-Output "Cluster: $($cluster.Name)"
    Write-Output "Quorum: $((Get-ClusterQuorum).QuorumType)"
    Write-Output ""
    Write-Output "--- Nodi ---"
    $nodeStatus | Format-Table -AutoSize
    Write-Output "--- Gruppi ---"
    $groupStatus | Format-Table -AutoSize
    Write-Output "--- CSV Storage ---"
    $csvSpace | Format-Table -AutoSize
    Write-Output "--- Reti ---"
    $networkStatus | Format-Table -AutoSize
    if ($recentEvents) {
        Write-Output "--- Eventi Recenti ---"
        $recentEvents | Format-Table TimeCreated, LevelDisplayName, Id, Message -Wrap
    }
}

Get-ClusterHealthDashboard
```

### Tabella di Troubleshooting Rapido

| # | Sintomo | Causa Probabile | Soluzione |
|---|---------|-----------------|-----------|
| 1 | Nodo espulso periodicamente dal cluster | Packet loss sulla rete heartbeat, driver NIC difettoso, CPU al 100% | Verificare NIC, aggiornare driver, aumentare `SameSubnetThreshold`, dedicare NIC al heartbeat |
| 2 | CSV in Redirected I/O (Block) | Path MPIO/iSCSI interrotto sul nodo non-owner | Verificare path con `mpclaim -s -d`, riparare connettività storage, spostare ownership CSV |
| 3 | CSV in Redirected I/O (FileSystem) | Rete cluster tra nodi interrotta per metadata | Verificare connettività rete cluster, firewall porta 445/3343, riparare NIC |
| 4 | Failover non avviene, risorsa resta Failed | `FailoverThreshold` raggiunto, nessun possible owner disponibile | Aumentare `FailoverThreshold`, verificare `Get-ClusterOwnerNode`, forzare `Move-ClusterGroup -Force` |
| 5 | Quorum perso, cluster offline | Troppi nodi down, witness non raggiungibile | Riparare la connettività, `Start-ClusterNode -FixQuorum`, riconfigurare witness |
| 6 | Cloud Witness non raggiungibile | Firewall blocca HTTPS verso Azure, access key scaduta, DNS non risolve | Verificare porta 443 outbound, rigenerare access key, testare DNS per `*.core.windows.net` |
| 7 | VM non migra con Live Migration | Rete LM non configurata, versioni CPU incompatibili, Kerberos fallito | Configurare rete dedicata LM, abilitare CPU compatibility, verificare constrained delegation |
| 8 | Risorsa IP Address non va online | Conflitto IP, VLAN sbagliata, subnet mask errata | `Test-Connection`, verificare VLAN e subnet, controllare DHCP scope exclusions |
| 9 | Risorsa Network Name non va online | CNO disabilitato in AD, DNS non accessibile, permessi OU insufficienti | Abilitare l'account computer in AD, verificare DNS, assegnare permessi al CNO |
| 10 | S2D volume degradato | Disco fisico guasto, nodo offline, ricostruzione in corso | Identificare disco con `Get-PhysicalDisk`, sostituire, attendere rebuild |
| 11 | Cluster validation fallisce su storage | SCSI Persistent Reservation non funzionante, dischi non visibili da tutti i nodi | Verificare zoning SAN, multipath, SCSI PR support, firmware HBA |
| 12 | CAU fallisce, nodi non aggiornati | Prerequisiti CAU mancanti, firewall WinRM, riavvio bloccato | `Test-CauSetup`, abilitare firewall rules, verificare pending reboot |
| 13 | Performance degradate dopo failover | Nodo sovraccarico, storage redirected, CSV cache non abilitata | Bilanciare i gruppi, verificare Direct I/O, abilitare CSV cache |
| 14 | Errore "Access Denied" creando ruolo | CNO senza permessi "Create Computer Objects" nella OU | Assegnare al CNO il permesso nella OU target, pre-creare il VCO |
| 15 | Cluster service non si avvia | Database cluster corrotto, quorum irraggiungibile | Avviare con `/forcequorum`, ripristinare CLUSDB da backup, ricostruire il cluster |
| 16 | Split-brain dopo network partition | Witness nella stessa rete dei nodi, una sola rete cluster | Spostare witness in terza location (Cloud Witness), aggiungere seconda rete heartbeat |
| 17 | Disco cluster non si monta | Disk signature cambiato, filesystem corrotto | `chkdsk /f` in modalità recovery, re-importare il disco con `Import-Module FailoverClusters` |
| 18 | Heartbeat lento su cluster multi-site | Parametri cross-subnet default troppo aggressivi per la WAN | Aumentare `CrossSubnetDelay` e `CrossSubnetThreshold`, verificare latenza WAN |

### Performance Monitoring con Performance Counter

```powershell
# Contatori di performance critici per cluster
function Get-ClusterPerformanceMetrics {
    param (
        [string]$ClusterName = ".",
        [int]$DurationSeconds = 30
    )

    $counters = @(
        "\Cluster CSV File System(_Total)\Reads/sec"
        "\Cluster CSV File System(_Total)\Writes/sec"
        "\Cluster CSV File System(_Total)\Read Bytes/sec"
        "\Cluster CSV File System(_Total)\Write Bytes/sec"
        "\Cluster CSV File System(_Total)\Read Latency"
        "\Cluster CSV File System(_Total)\Write Latency"
        "\Cluster CSV Volume Cache(_Total)\Cache Hit %"
        "\Cluster CSV Volume Manager(_Total)\IO Read Bytes/sec"
        "\Cluster CSV Volume Manager(_Total)\IO Write Bytes/sec"
    )

    $nodes = (Get-ClusterNode -Cluster $ClusterName).Name

    foreach ($node in $nodes) {
        Write-Output "`n=== Performance Metrics: $node ==="
        try {
            $samples = Get-Counter -ComputerName $node -Counter $counters `
                -SampleInterval 5 -MaxSamples ($DurationSeconds / 5) -ErrorAction Stop

            foreach ($sample in $samples[-1].CounterSamples) {
                $name = ($sample.Path -split '\\')[-1]
                $value = [math]::Round($sample.CookedValue, 2)
                Write-Output "  $name : $value"
            }
        }
        catch {
            Write-Warning "Impossibile raccogliere metriche da $node : $_"
        }
    }
}

# Monitorare la latenza di Storage Replica (per stretch cluster)
function Get-StorageReplicaHealth {
    $partnerships = Get-SRPartnership -ErrorAction SilentlyContinue
    if (-not $partnerships) {
        Write-Output "Nessuna partnership Storage Replica configurata."
        return
    }

    foreach ($p in $partnerships) {
        $sourceGroup = Get-SRGroup -Name $p.SourceRGName
        $destGroup = Get-SRGroup -Name $p.DestinationRGName

        [PSCustomObject]@{
            SourceServer  = $p.SourceComputerName
            DestServer    = $p.DestinationComputerName
            Mode          = $p.ReplicationMode
            AsyncRPO      = if ($p.ReplicationMode -eq "Asynchronous") { $sourceGroup.Replicas[0].AsyncRPO } else { "N/A (Sync)" }
            LastInSyncTime = $sourceGroup.Replicas[0].LastInSyncTime
            NumOfBytesRemaining = $sourceGroup.Replicas[0].NumOfBytesRemaining
            Status        = $sourceGroup.Replicas[0].ReplicationStatus
        }
    }
}

Get-StorageReplicaHealth | Format-List
```

### Integrazione con Windows Admin Center

Windows Admin Center (WAC) offre un'interfaccia web moderna per la gestione dei cluster, con dashboard di monitoraggio in tempo reale, gestione delle VM, configurazione dello storage e integrazione con Azure per il backup e il disaster recovery.

```powershell
# Installare Windows Admin Center per la gestione del cluster
# Scaricare da https://aka.ms/wacdownload

# Dopo l'installazione, accedere via browser:
# https://wac-server:6516

# WAC fornisce:
# - Dashboard del cluster con stato in tempo reale di nodi, VM e storage
# - Creazione e gestione VM direttamente dall'interfaccia web
# - Monitoraggio performance con grafici storici
# - Gestione aggiornamenti tramite CAU integrato
# - Integrazione Azure (Azure Backup, Azure Site Recovery, Azure Monitor)
# - Alert e notifiche per eventi critici del cluster

# Registrare il cluster in Windows Admin Center via PowerShell
# (richiede il modulo WindowsAdminCenter)
$gateway = "https://wac-server:6516"

# Configurare le estensioni per Failover Clustering
# WAC → Settings → Extensions → Install "Cluster Manager"

# Per cluster S2D, l'estensione Cluster Manager mostra:
# - Pool di storage con stato di salute dei dischi fisici
# - Volumi con capacità, performance IOPS e latenza
# - Fault domain visualization per rack/chassis/nodo
# - Drive firmware update orchestration

# Monitorare gli alert dal cluster tramite Azure Monitor (hybrid)
# WAC → Azure → Register with Azure → Enable Azure Monitor
# Questo invia i log del cluster a un workspace Log Analytics
# dove possono essere analizzati con query KQL
```

---

## Esercizi Pratici

### Esercizio 1 — Cluster a 2 Nodi con Quorum Cloud Witness

Obiettivo: creare un cluster a 2 nodi con Cloud Witness, configurare reti dedicate e validare il failover.

```
Requisiti:
- 2 VM Windows Server 2022 (NODE01, NODE02) — 4 vCPU, 8 GB RAM
- Dominio AD funzionante
- 2 NIC per VM (Client: 10.0.1.0/24, Heartbeat: 192.168.100.0/24)
- 1 disco iSCSI condiviso (50 GB)
- Account Azure con storage account per Cloud Witness

Procedura:
1. Installare Failover-Clustering su entrambi i nodi
2. Eseguire Test-Cluster e risolvere eventuali Warning/Failure
3. Creare il cluster con New-Cluster (IP statico sulla rete client)
4. Configurare la rete 192.168.100.0 come Role 1 (Cluster Only)
5. Configurare Cloud Witness con Set-ClusterQuorum
6. Aggiungere il disco iSCSI come CSV
7. Creare un file di test sul CSV da entrambi i nodi (accesso concorrente)
8. Simulare il failure di NODE01 (Stop-ClusterNode)
9. Verificare che il cluster rimanga operativo (quorum mantenuto)
10. Riportare NODE01 online e verificare il rejoin

Criterio di successo:
- Validation report senza errori
- Cloud Witness funzionante
- CSV accessibile da entrambi i nodi
- Failover completato in meno di 60 secondi
```

### Esercizio 2 — Hyper-V HA con Live Migration

Obiettivo: configurare un cluster Hyper-V con VM altamente disponibili e testare Live Migration.

```
Requisiti:
- Cluster a 2 nodi dall'Esercizio 1
- Hyper-V installato su entrambi i nodi
- CSV con almeno 100 GB di spazio libero
- Rete dedicata per Live Migration (192.168.200.0/24)

Procedura:
1. Verificare che Hyper-V sia installato su entrambi i nodi
2. Configurare la rete Live Migration (192.168.200.0/24)
3. Impostare Set-VMHost -VirtualMachineMigrationPerformanceOption SMB
4. Creare una VM Generation 2 sul CSV (2 vCPU, 4 GB RAM, 40 GB disco)
5. Installare un SO guest (Windows Server Core o Ubuntu Server)
6. Rendere la VM altamente disponibile con Add-ClusterVirtualMachineRole
7. Avviare un processo continuativo nella VM (ping continuo o web server)
8. Eseguire Live Migration verso l'altro nodo
9. Verificare che il processo nella VM non si sia interrotto
10. Configurare anti-affinità tra due VM (se ne hai create due)
11. Testare il failover non pianificato (riavvio improvviso del nodo owner)
12. Verificare che la VM si riavvii sull'altro nodo

Criterio di successo:
- Live Migration senza interruzione del servizio nella VM
- Failover non pianificato con recovery automatico
- Anti-affinità rispettata
```

### Esercizio 3 — Storage Spaces Direct (Hyper-Converged)

Obiettivo: costruire un cluster S2D a 2 nodi con volumi mirror e monitorare la salute.

```
Requisiti:
- 2 VM Windows Server 2022 Datacenter (S2D richiede Datacenter)
- 4 vCPU, 16 GB RAM per nodo
- 2 NIC per nodo (Client + Storage RDMA simulato)
- 4 dischi virtuali aggiuntivi per nodo (2x SSD 50GB + 2x HDD 200GB)
  (simulare con dischi virtuali di diverso tipo)

Procedura:
1. Installare Failover-Clustering e Hyper-V su entrambi i nodi
2. Creare il cluster senza storage (New-Cluster -NoStorage)
3. Verificare che i dischi aggiuntivi siano visibili (Get-PhysicalDisk)
4. Abilitare S2D con Enable-ClusterStorageSpacesDirect
5. Verificare il pool creato (Get-StoragePool)
6. Verificare la distribuzione cache/capacità (Get-PhysicalDisk -Usage)
7. Creare un volume 2-way mirror da 100 GB
8. Creare una VM sul volume S2D e renderla HA
9. Simulare il failure di un disco (offline un disco virtuale)
10. Verificare la ricostruzione automatica dei dati
11. Monitorare con Get-StorageHealthReport e Performance Counter
12. Documentare le prestazioni I/O prima e dopo il failure

Criterio di successo:
- S2D abilitato con pool sano
- Volume mirror funzionante e accessibile
- Ricostruzione automatica dopo failure di un disco
- VM HA funzionante sul volume S2D
```

### Esercizio 4 — CAU e Cluster OS Rolling Upgrade

Obiettivo: eseguire un aggiornamento CAU pianificato e simulare un rolling upgrade.

```
Requisiti:
- Cluster a 2 nodi funzionante (da esercizi precedenti)
- Accesso a WSUS o Windows Update
- Script pre/post update preparati

Procedura:
1. Verificare i prerequisiti CAU: Test-CauSetup
2. Configurare la modalità self-updating con pianificazione settimanale
3. Creare uno script pre-update che:
   a. Esporta la configurazione del cluster
   b. Verifica che tutti i nodi siano Up
   c. Invia una notifica (output a log)
4. Creare uno script post-update che:
   a. Verifica che tutti i gruppi siano Online
   b. Verifica la versione dell'OS aggiornata
   c. Registra il risultato nel log
5. Eseguire un aggiornamento CAU manuale (Invoke-CauRun)
6. Monitorare il progresso in tempo reale (Get-CauRun)
7. Verificare il report finale (Get-CauReport)
8. (Opzionale) Simulare il rolling upgrade:
   a. Evict NODE02, reinstallare con versione successiva
   b. Rejoin NODE02 al cluster (mixed mode)
   c. Verificare che il cluster funzioni in mixed mode
   d. Non eseguire Update-ClusterFunctionalLevel (per reversibilità)

Criterio di successo:
- CAU eseguito senza downtime dei servizi
- Script pre/post eseguiti correttamente
- Report CAU senza errori
```

### Esercizio 5 — Disaster Recovery e Rebuild

Obiettivo: simulare la perdita completa di un nodo e ricostruire il cluster.

```
Requisiti:
- Cluster a 2 nodi funzionante con almeno una VM HA
- Backup della configurazione del cluster (da script Export-ClusterConfiguration)

Procedura:
1. Esportare la configurazione completa del cluster
2. Eseguire il backup delle VM con Windows Server Backup
3. Simulare il disaster: spegnere NODE02 e distruggere la VM
4. Verificare il comportamento del cluster (quorum mantenuto? failover?)
5. Rimuovere il nodo distrutto: Remove-ClusterNode -Force
6. Riconfigurare il quorum per nodo singolo
7. Creare un nuovo nodo (NODE-NEW) e aggiungerlo al cluster
8. Riconfigurare il quorum con Cloud Witness
9. Verificare che le VM siano distribuite sui nodi
10. (Opzionale) Forzare il quorum su NODE01 singolo e testare il recovery

Criterio di successo:
- Cluster operativo dopo la perdita di un nodo
- Nuovo nodo aggiunto senza interruzione
- Tutte le VM HA tornate online
- Configurazione del quorum corretta dopo il rebuild
```

---

## Auto-valutazione

### Domanda 1
Qual è la differenza tra quorum statico e dynamic quorum, e perché il dynamic quorum è abilitato per default?

<details>
<summary>Risposta</summary>

Il **quorum statico** richiede che un numero fisso di voti (maggioranza di tutti i nodi + witness configurati) sia disponibile. Se troppi nodi sono offline, anche se spenti in modo controllato, il cluster perde il quorum.

Il **dynamic quorum** adatta automaticamente il numero di voti necessari in base ai nodi attualmente attivi. Quando un nodo viene spento in modo controllato (drain + shutdown), il suo voto viene rimosso dal conteggio della maggioranza. Questo permette al cluster di sopravvivere a shutdown sequenziali che altrimenti causerebbero quorum loss.

Esempio: un cluster a 5 nodi con quorum statico tollera la perdita di 2 nodi. Con dynamic quorum, se 3 nodi vengono spenti uno alla volta in modo controllato, il cluster continua a funzionare con i 2 nodi rimanenti, perché la maggioranza viene ricalcolata a ogni step.

Il dynamic quorum è abilitato per default perché migliora significativamente la resilienza senza svantaggi. Si disabilita solo in scenari molto specifici dove si vuole un controllo esplicito sul quorum (raro).

Riferimento: Microsoft Learn, "Configure and manage quorum" — learn.microsoft.com/en-us/windows-server/failover-clustering/manage-cluster-quorum. Consultato: 2026-05-23.
</details>

### Domanda 2
Come funziona il meccanismo di prevenzione dello split-brain in WSFC e quali sono i layer di protezione?

<details>
<summary>Risposta</summary>

WSFC implementa la prevenzione dello split-brain su 4 layer:

1. **Quorum Voting**: la partizione che possiede la maggioranza dei voti (>50%) rimane operativa. La partizione minoritaria si spegne automaticamente. Il witness (disco, file share, cloud) aggiunge un voto per rompere i pareggi.

2. **Quorum Arbitration**: quando due partizioni hanno lo stesso numero di voti, entrambe tentano di acquisire il witness. La prima che lo acquisisce vince la "race", l'altra si spegne entro 5 secondi (`QuorumArbitrationTimeMax`).

3. **SCSI Persistent Reservation**: a livello di storage condiviso, solo il nodo con la reservation SCSI attiva può scrivere sul disco. Questo previene la corruzione dei dati anche se il quorum software fallisce.

4. **Cluster Network Partitioning**: il cluster monitora TUTTE le reti configurate. Un nodo è considerato in failure solo quando TUTTE le reti cluster lo riportano come irraggiungibile. Se anche una sola rete funziona, il nodo resta nella membership.

La difesa più importante è il Cloud Witness in una terza location per i cluster multi-sito: essendo in Azure, è indipendente da entrambi i siti e non può essere coinvolto in una partizione di rete tra i due datacenter.

Riferimento: Microsoft Learn, "Failover Clustering networking basics" — learn.microsoft.com/en-us/windows-server/failover-clustering/failover-clustering-networking-basics. Consultato: 2026-05-23.
</details>

### Domanda 3
Spiega la differenza tra Direct I/O e Redirected I/O nei CSV e le implicazioni sulle performance.

<details>
<summary>Risposta</summary>

**Direct I/O**: ogni nodo del cluster accede direttamente allo storage fisico (SAN, iSCSI) per le operazioni di I/O sui dati. Le operazioni di metadata (creazione file, modifica permessi, estensione) vengono coordinate dal nodo owner (metadata server) via rete cluster. Questo è il modo normale di funzionamento e offre performance ottimali.

**Block Redirected I/O**: il nodo non-owner non riesce a raggiungere lo storage fisico (path MPIO interrotto, iSCSI disconnesso). Tutto l'I/O viene inviato al nodo owner tramite SMB sulla rete cluster, che lo esegue per conto del nodo richiedente. Le performance degradano drasticamente perché tutto il traffico I/O transita sulla rete.

**File System Redirected I/O**: il nodo non-owner non riesce a comunicare con il nodo owner per le operazioni di metadata del filesystem. L'I/O dei dati può ancora essere diretto, ma le operazioni che richiedono coordinazione (apertura file, estensione, cambio permessi) vengono reindirizzate.

Implicazioni: il Redirected I/O è un sintomo, non una causa. Il troubleshooting deve concentrarsi sul ripristino della connettività storage (per Block) o della rete cluster (per FileSystem). Lasciare un CSV in Redirected I/O in produzione causa degradazione delle performance e potenziale congestione della rete cluster.

Diagnostica: `Get-ClusterSharedVolumeState` mostra `StateInfo` (Direct/BlockRedirected/FileSystemRedirected) e il motivo (`BlockRedirectedIOReason`, `FileSystemRedirectedIOReason`).

Riferimento: Microsoft Learn, "Use Cluster Shared Volumes in a failover cluster" — learn.microsoft.com/en-us/windows-server/failover-clustering/failover-cluster-csvs. Consultato: 2026-05-23.
</details>

### Domanda 4
Come funziona Storage Spaces Direct (S2D) e qual è il ruolo dei cache tier e capacity tier?

<details>
<summary>Risposta</summary>

S2D aggrega i dischi locali (interni) di più nodi del cluster in un unico pool di storage distribuito, eliminando la necessità di una SAN esterna. I dati vengono replicati tra i nodi per la resilienza.

**Cache Tier**: i dischi più veloci nel sistema (NVMe se presenti, altrimenti SSD) vengono automaticamente utilizzati come cache. La cache è write-back per le scritture (i dati vengono scritti prima sulla cache veloce, poi propagati alla capacità) e read-cache per le letture frequenti. Ogni disco cache è assegnato (binding) a un set di dischi capacità sullo stesso nodo.

**Capacity Tier**: i dischi più lenti (SSD se NVMe è usato per la cache, oppure HDD) forniscono la capacità. I dati vengono distribuiti e replicati tra i nodi secondo il tipo di resilienza configurato (mirror, parity, mirror-accelerated parity).

Combinazioni tipiche:
- NVMe (cache) + SSD (capacità): bilanciato performance/capacità
- SSD (cache) + HDD (capacità): economico, buone letture grazie alla cache SSD
- All-NVMe o All-SSD: nessun tier separato, la cache è in-memory

Il rapporto cache/capacità dovrebbe essere almeno il 10% della capacità totale. La cache S2D è trasparente: non si configura, si lascia che S2D la gestisca automaticamente in base al tipo di disco rilevato.

Riferimento: Microsoft Learn, "Understanding the cache in Storage Spaces Direct" — learn.microsoft.com/en-us/windows-server/storage/storage-spaces/understand-the-cache. Consultato: 2026-05-23.
</details>

### Domanda 5
Qual è la procedura corretta per un Cluster OS Rolling Upgrade e perché `Update-ClusterFunctionalLevel` è irreversibile?

<details>
<summary>Risposta</summary>

Procedura:
1. **Drain** un nodo (Suspend-ClusterNode -Drain): migra tutti i ruoli su altri nodi
2. **Evict** il nodo dal cluster (Remove-ClusterNode -Force)
3. **Reinstallare** Windows Server con la nuova versione (fresh install)
4. **Installare** Failover-Clustering sul nodo aggiornato
5. **Rejoin** il nodo al cluster (Add-ClusterNode): il cluster opera in **mixed mode**
6. Ripetere i passi 1-5 per ogni nodo
7. **Update-ClusterFunctionalLevel**: aggiorna il livello funzionale del cluster alla nuova versione

Il cluster in mixed mode funziona al livello funzionale della versione precedente. I nodi aggiornati operano in modalità compatibilità. Le nuove feature della versione aggiornata NON sono disponibili fino a `Update-ClusterFunctionalLevel`.

`Update-ClusterFunctionalLevel` è **irreversibile** perché:
- Modifica il formato del cluster database (CLUSDB) per supportare le nuove feature
- Aggiorna le strutture dati interne che non sono backward-compatible
- Dopo l'aggiornamento, i nodi con la versione precedente non possono più unirsi al cluster
- Non esiste un percorso di downgrade del livello funzionale

Per questo motivo, è ESSENZIALE verificare che tutto funzioni correttamente in mixed mode prima di eseguire l'aggiornamento del livello funzionale. Se qualcosa non funziona, si possono riportare i nodi alla versione precedente finché il cluster è in mixed mode.

Riferimento: Microsoft Learn, "Cluster operating system rolling upgrade" — learn.microsoft.com/en-us/windows-server/failover-clustering/cluster-operating-system-rolling-upgrade. Consultato: 2026-05-23.
</details>

### Domanda 6
Come si configura l'anti-affinità tra gruppi cluster e quando è necessaria?

<details>
<summary>Risposta</summary>

L'anti-affinità si configura assegnando lo stesso valore alla proprietà `AntiAffinityClassNames` di due o più gruppi cluster:

```powershell
$group1 = Get-ClusterGroup "VM-DC01"
$group1.AntiAffinityClassNames = "DomainController"
$group2 = Get-ClusterGroup "VM-DC02"
$group2.AntiAffinityClassNames = "DomainController"
```

Il cluster tenterà di posizionare i gruppi con lo stesso `AntiAffinityClassNames` su nodi diversi. Se non è possibile (es. un solo nodo disponibile), il cluster li posiziona sullo stesso nodo con un warning, ma non impedisce il funzionamento.

Scenari dove l'anti-affinità è necessaria:
- **Domain Controller**: due DC sullo stesso host significa che il failure dell'host perde entrambi i DC
- **Database + Replica**: il database primario e la replica non devono stare sullo stesso nodo
- **Web tier ridondante**: due istanze dello stesso web server su nodi diversi per resilienza
- **Servizi con risorse intensive**: due servizi CPU-intensive sullo stesso nodo causano contention

L'anti-affinità è un **best-effort**, non un vincolo rigido. Per vincoli rigidi, usare `Set-ClusterOwnerNode` con possible owner mutuamente esclusivi. La combinazione dei due (anti-affinità + possible owners) offre il massimo controllo.

Riferimento: Microsoft Learn, "Failover Clustering VM anti-affinity rules" — learn.microsoft.com/en-us/windows-server/failover-clustering/cluster-affinity. Consultato: 2026-05-23.
</details>

### Domanda 7
Qual è il ruolo del CNO e dei VCO in Active Directory per un failover cluster?

<details>
<summary>Risposta</summary>

**CNO (Cluster Name Object)**: è l'account computer in Active Directory che rappresenta il cluster stesso. Viene creato automaticamente quando si crea il cluster (es. `CLUSTER01$` in AD). Il CNO:
- Registra il nome del cluster nel DNS
- Autentica il cluster tramite Kerberos
- Crea i VCO quando si aggiungono ruoli al cluster
- Deve risiedere in un'OU dove ha il permesso "Create Computer Objects"

**VCO (Virtual Computer Object)**: è l'account computer creato per ogni ruolo cluster che ha un Network Name (es. `FS-CLUSTER$`, `SQL-AG$`). Il VCO:
- Registra il nome del ruolo nel DNS
- Permette l'autenticazione Kerberos per il servizio cluster
- È creato dal CNO (non dall'utente amministratore)
- Necessita che il CNO abbia i permessi nella OU target

Problemi comuni:
- Se il CNO non ha permessi nella OU, l'aggiunta di ruoli fallisce con "Access Denied"
- Se il CNO viene disabilitato in AD (per policy di sicurezza su account inattivi), il cluster perde la risoluzione DNS
- Best practice: pre-creare il CNO in una OU dedicata ai cluster con i permessi appropriati

Riferimento: Microsoft Learn, "Prestage cluster computer objects in Active Directory" — learn.microsoft.com/en-us/windows-server/failover-clustering/prestage-cluster-adds. Consultato: 2026-05-23.
</details>

### Domanda 8
Come si esegue il forced quorum e quali sono i rischi?

<details>
<summary>Risposta</summary>

Il forced quorum si esegue avviando il cluster service con il flag `/forcequorum`:

```powershell
net start clussvc /forcequorum
# Oppure
Start-ClusterNode -Name "NODE01" -FixQuorum
```

Questo forza il nodo ad avviare il cluster senza avere la maggioranza dei voti, tipicamente dopo un disaster che ha distrutto la maggioranza dei nodi.

**Rischi:**
1. **Split-brain**: se i nodi "perduti" non sono realmente distrutti ma solo isolati dalla rete, possono tornare online con la loro copia del cluster. Due cluster indipendenti operano sugli stessi dati → corruzione certa.

2. **Data loss**: se le ultime modifiche alla configurazione erano sui nodi perduti e non erano state replicate al nodo sopravvissuto, quelle modifiche sono perse.

3. **Inconsistenza**: il nodo forzato potrebbe avere una versione del CLUSDB non aggiornata.

**Mitigazioni obbligatorie dopo forced quorum:**
1. Rimuovere IMMEDIATAMENTE i nodi perduti dal cluster (`Remove-ClusterNode -Force`)
2. Verificare l'integrità dei dati sullo storage condiviso
3. Riconfigurare il quorum per il nuovo numero di nodi
4. Se possibile, aggiungere nuovi nodi per ripristinare la resilienza
5. Mai usare forced quorum come workaround per problemi di rete risolvibili

Riferimento: Microsoft Learn, "Configure and manage quorum" — learn.microsoft.com/en-us/windows-server/failover-clustering/manage-cluster-quorum. Consultato: 2026-05-23.
</details>

### Domanda 9
Spiega la differenza tra il DHCP Failover nativo e il clustering DHCP tradizionale via WSFC.

<details>
<summary>Risposta</summary>

**DHCP Failover nativo** (introdotto in Windows Server 2012):
- Meccanismo built-in nel servizio DHCP, non richiede WSFC
- Due modalità: **Hot Standby** (primario/secondario) e **Load Balance** (entrambi attivi)
- Lo scope viene replicato automaticamente tra i due server DHCP
- Non richiede storage condiviso — ogni server ha il suo database DHCP
- Supporta solo 2 server per relazione di failover
- Failover rapido: il secondario rileva la mancanza del primario e assume il lease management

**DHCP Clustering via WSFC**:
- Il servizio DHCP è un ruolo cluster gestito dal Failover Manager
- Richiede storage condiviso (disco cluster) per il database DHCP
- Solo un nodo alla volta serve le richieste (active/passive)
- Il failover avviene tramite il meccanismo standard del cluster (drain + move)
- Supporta N nodi (non limitato a 2)
- Più lento nel failover rispetto al DHCP nativo

Raccomandazione: per la maggior parte degli scenari, il **DHCP Failover nativo in modalità Load Balance** è preferibile perché è più semplice, non richiede WSFC, e offre sia HA che distribuzione del carico. Il clustering WSFC si usa quando il DHCP deve far parte di un cluster esistente per ragioni organizzative.

Riferimento: Microsoft Learn, "DHCP Failover" — learn.microsoft.com/en-us/windows-server/networking/technologies/dhcp/dhcp-failover. Consultato: 2026-05-23.
</details>

### Domanda 10
Quali sono le considerazioni di rete per un cluster multi-site (stretched cluster) e come si configura il Cloud Witness?

<details>
<summary>Risposta</summary>

**Considerazioni di rete:**
- Latenza tra siti: < 5ms RTT per replica sincrona dello storage, < 1ms per prestazioni ottimali. Con latenze superiori, usare replica asincrona (RPO > 0).
- Banda: sufficiente per la replica dello storage + heartbeat + Live Migration. La Live Migration tra siti è sconsigliata per la latenza.
- Heartbeat cross-subnet: aumentare `CrossSubnetDelay` (default 1000ms) e `CrossSubnetThreshold` (default 20) per adattarsi alla latenza WAN.
- Routing: `PlumbAllCrossSubnetRoutes = 1` per garantire connettività tra tutte le subnet del cluster.
- DNS TTL: ridurre `HostRecordTTL` a 120 secondi per failover DNS rapido cross-site.

**Configurazione Cloud Witness:**
```powershell
# 1. In Azure: creare uno storage account (Standard LRS, qualsiasi regione)
# 2. Ottenere la Access Key dello storage account
# 3. Configurare nel cluster:
Set-ClusterQuorum -CloudWitness `
    -AccountName "nomestorageaccount" `
    -AccessKey "chiave-base64" `
    -Endpoint "core.windows.net"
```

Il Cloud Witness usa Azure Blob Storage, costa pochi centesimi/mese, e risiede in una terza location indipendente da entrambi i siti — eliminando il rischio che una singola partizione di rete causi split-brain. È la scelta raccomandata per tutti i cluster multi-sito e anche per i cluster single-site con numero pari di nodi.

Riferimento: Microsoft Learn, "Deploy a Cloud Witness for a Failover Cluster" — learn.microsoft.com/en-us/windows-server/failover-clustering/deploy-cloud-witness. Consultato: 2026-05-23.
</details>

---

## Letture Primarie

| Risorsa | Tipo | Rilevanza |
|---------|------|-----------|
| Microsoft Learn: Failover Clustering Overview | Documentazione | Panoramica ufficiale completa di WSFC per Windows Server 2022/2025 |
| Microsoft Learn: Configure and Manage Cluster Quorum | Documentazione | Modelli di quorum, dynamic quorum, witness configuration, forced quorum |
| Microsoft Learn: Cluster Shared Volumes (CSV) | Documentazione | Architettura CSV, Direct I/O, Redirected I/O, CSV Cache, troubleshooting |
| Microsoft Learn: Storage Spaces Direct Overview | Documentazione | Architettura S2D, fault domain, cache tier, resilience settings, deployment |
| Microsoft Learn: Cluster-Aware Updating Overview | Documentazione | CAU self-updating e remote-updating, plugin, pre/post script |
| Microsoft Learn: Cluster OS Rolling Upgrade | Documentazione | Procedura rolling upgrade, mixed mode, Update-ClusterFunctionalLevel |
| Microsoft Learn: Prestage Cluster Computer Objects in AD | Documentazione | CNO, VCO, permessi AD per cluster, Kerberos constrained delegation |
| Microsoft Learn: Deploy a Cloud Witness | Documentazione | Cloud Witness Azure, configurazione, requisiti rete e storage account |
| Windows Server Failover Clustering PowerShell Reference | Riferimento | Documentazione completa dei cmdlet FailoverClusters module |
| "Mastering Windows Server 2022" (Jordan Krause, Packt) | Libro | Copertura pratica di WSFC, S2D, Hyper-V cluster per ambienti enterprise |
| "Windows Server 2022 Cookbook" (Mark Henderson, Packt) | Libro | Ricette operative per cluster, quorum, CSV, CAU con procedure passo-passo |
| Microsoft Learn: Troubleshoot Failover Clustering | Documentazione | Diagnostica cluster log, event ID, problemi comuni e soluzioni |

> Tutte le risorse consultate il 2026-05-23.

---

## Collegamenti Incrociati

- **Modulo 01 — Active Directory**: prerequisito per l'autenticazione Kerberos del cluster, CNO/VCO, OU e permessi
- **Modulo 02 — PowerShell**: prerequisito per il modulo FailoverClusters e l'automazione della gestione cluster
- **Modulo 06 — Rete Windows**: fondamentale per la configurazione delle reti cluster, heartbeat, VLAN dedicate
- **Modulo 07 — Storage Windows**: base per SAN, iSCSI, SMB 3.x, Storage Spaces e la comprensione dello storage condiviso
- **Modulo 15 — Backup e Ripristino**: backup della configurazione cluster, System State backup, disaster recovery
- **Modulo 21 — Group Policy**: GPO per la configurazione dei nodi del cluster, firewall rules, security settings
- **Modulo 23 — Hyper-V**: approfondimento sulle VM altamente disponibili, Live Migration, Hyper-V Replica
- **Modulo 25 — Active Directory Design Avanzato**: progettazione OU per cluster, delega amministrativa, trust
- **Modulo 28 — PKI e Certificati**: certificati per la crittografia del traffico cluster, BitLocker su CSV
- **Modulo 29 — Windows Server Hardening**: hardening dei nodi cluster, firewall, RBAC, audit
- **Modulo 30 — Identità Ibrida Azure AD**: integrazione Azure per Cloud Witness, Azure Monitor, Azure Backup
- **Modulo 34 — Disaster Recovery AD/PKI**: complemento per la pianificazione DR dell'intera infrastruttura

---

## Glossario Locale

| Termine | Definizione |
|---------|-------------|
| **CAU** | Cluster-Aware Updating — framework per aggiornare i nodi del cluster senza downtime dei servizi |
| **CLUSDB** | Cluster Database — registry hive che contiene l'intera configurazione del cluster, replicato su tutti i nodi |
| **clussvc** | Cluster Service (clussvc.exe) — servizio Windows core che gestisce membership, heartbeat, failover e database |
| **CNO** | Cluster Name Object — account computer in Active Directory che rappresenta il cluster stesso |
| **CSV** | Cluster Shared Volume — filesystem distribuito che permette l'accesso simultaneo da tutti i nodi del cluster |
| **Direct I/O** | Modalità CSV dove ogni nodo accede direttamente allo storage; performance ottimali |
| **Dynamic Quorum** | Meccanismo che adatta automaticamente il numero di voti necessari in base ai nodi attivi |
| **Fault Domain** | Confine di failure per la distribuzione dei dati in S2D (nodo, chassis, rack, sito) |
| **GUM** | Global Update Manager — componente di clussvc che replica in modo atomico gli aggiornamenti di configurazione |
| **Heartbeat** | Messaggi UDP (porta 3343) scambiati tra nodi per rilevare failure; default ogni 1 secondo |
| **Is-Alive** | Check approfondito (default 60s) che verifica il funzionamento reale di una risorsa cluster |
| **Look-Alive** | Check leggero (default 5s) che verifica rapidamente se una risorsa cluster risponde |
| **Quorum** | Meccanismo di voto che determina quanti nodi devono essere operativi per mantenere il cluster attivo |
| **Redirected I/O** | Modalità CSV dove l'I/O transita via SMB attraverso il nodo owner; indica un problema di connettività |
| **RHS** | Resource Host Subsystem (RHS.exe) — processo worker che ospita e monitora le risorse cluster |
| **S2D** | Storage Spaces Direct — soluzione hyper-converged che aggrega storage locale dei nodi in un pool distribuito |
| **SCSI PR** | SCSI Persistent Reservation — meccanismo a livello storage che impedisce scritture concorrenti non autorizzate |
| **Split-brain** | Scenario dove due partizioni del cluster operano indipendentemente, rischiando la corruzione dei dati |
| **VCO** | Virtual Computer Object — account computer in AD creato per ogni ruolo cluster con Network Name |
| **Witness** | Risorsa (disco, file share, cloud blob) che aggiunge un voto al quorum per rompere i pareggi |
| **WSFC** | Windows Server Failover Clustering — tecnologia Microsoft per l'alta disponibilità dei servizi |

---

## Riferimenti

- Microsoft Learn: Failover Clustering Overview — https://learn.microsoft.com/en-us/windows-server/failover-clustering/failover-clustering-overview
- Microsoft Learn: Cluster Quorum — https://learn.microsoft.com/en-us/windows-server/failover-clustering/manage-cluster-quorum
- Microsoft Learn: Cluster Shared Volumes — https://learn.microsoft.com/en-us/windows-server/failover-clustering/failover-cluster-csvs
- Microsoft Learn: Cluster-Aware Updating — https://learn.microsoft.com/en-us/windows-server/failover-clustering/cluster-aware-updating
- Microsoft Learn: Storage Spaces Direct — https://learn.microsoft.com/en-us/windows-server/storage/storage-spaces/storage-spaces-direct-overview
- Microsoft Learn: Troubleshoot Failover Clustering — https://learn.microsoft.com/en-us/windows-server/failover-clustering/troubleshooting-using-wer-reports
- Microsoft Learn: Deploy Cloud Witness — https://learn.microsoft.com/en-us/windows-server/failover-clustering/deploy-cloud-witness
- Microsoft Learn: Cluster OS Rolling Upgrade — https://learn.microsoft.com/en-us/windows-server/failover-clustering/cluster-operating-system-rolling-upgrade
- Microsoft Learn: Prestage Cluster Computer Objects — https://learn.microsoft.com/en-us/windows-server/failover-clustering/prestage-cluster-adds
- Microsoft Learn: FailoverClusters PowerShell Module — https://learn.microsoft.com/en-us/powershell/module/failoverclusters/
- Windows Admin Center Documentation — https://learn.microsoft.com/en-us/windows-server/manage/windows-admin-center/overview
