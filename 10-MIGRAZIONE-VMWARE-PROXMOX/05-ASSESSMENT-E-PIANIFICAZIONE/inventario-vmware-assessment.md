# Inventario VMware e Assessment dell'Infrastruttura

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 2 — Assessment · Modulo 05.1 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 01.1 e 01.2 (per sapere *cosa* censire); PowerShell + PowerCLI installati; lettura SSH/CLI ESXi; concetti base di SQL/CSV.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. condurre un inventario completo e ripetibile di un ambiente vSphere (host, VM, storage, networking, cluster, permessi, snapshot, RDM, passthrough), producendo artefatti CSV/JSON con schema fisso;
> 2. usare i tre strumenti complementari — PowerCLI, RVTools, VMware vSphere API — sapendo quale e adatto a quale tipo di indagine;
> 3. estendere lo script di estrazione automatizzata per includere metadati custom (tag, custom attributes, note di business) e mantenerlo idempotente;
> 4. trasformare l'inventario grezzo in input concreto per il modulo 05.2 (analisi dipendenze) e 05.3 (sizing target Proxmox);
> 5. classificare le VM secondo dimensioni operative (criticita, owner, finestra di downtime, application tier), fornendo lo "schema di tagging" che alimentera il piano di migrazione a wave;
> 6. produrre il documento di "as-is architecture" con elenco assets, deviazioni dalle best practice (snapshot vecchi, VM con HW version obsoleta, datastore quasi pieni) e raccomandazioni di pre-migrazione.
> **Tempo stimato:** lettura 60-90 min · lab 240-360 min (sull'ambiente vSphere effettivo da censire)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** PowerCLI ≥ 13.x (PowerShell Core 7.x cross-platform), RVTools 4.x+, vSphere API 8.x.

## Mappa concettuale

```
+======================================================+
|  Assessment VMware — pipeline                        |
+======================================================+
|                                                      |
|   FONTI                                              |
|   +----------+ +----------+ +-----------+            |
|   | vCenter  | | ESXi SSH | | RVTools   |            |
|   | (API/    | | (esxcli) | | (lettura  |            |
|   |  PowerCLI)+----+-----+- |  XLSX/CSV)|            |
|   +-----+----+     |        +-----+-----+            |
|         |          |              |                  |
|         +----+-----+----+---------+                  |
|              |          |                            |
|              v          v                            |
|   ESTRAZIONE                                         |
|     Script PowerCLI (idempotente, taggato)           |
|         |                                            |
|         v                                            |
|   ARTEFATTI CSV/JSON                                 |
|     host-inventory.csv                               |
|     vm-inventory.csv                                 |
|     vm-disks.csv                                     |
|     vm-snapshots.csv                                 |
|     portgroups.csv                                   |
|     dvswitches.csv                                   |
|     datastores.csv                                   |
|     cluster-config.csv                               |
|     permissions.csv                                  |
|         |                                            |
|         v                                            |
|   ANALISI DERIVATA                                   |
|     - 05.2 Dipendenze e criticita                    |
|     - 05.3 Sizing target Proxmox                     |
|     - 05.4 Timeline e rischio                        |
|         |                                            |
|         v                                            |
|   DOCUMENTO "AS-IS ARCHITECTURE"                    |
|     + raccomandazioni pre-migrazione                 |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **Inventario ripetibile, non solo accurato.** L'estrazione deve essere automatizzata e idempotente: si deve poter rieseguire ogni 7-14 giorni durante il periodo di migrazione per sincronizzarsi con i cambi (nuove VM, snapshot creati ad hoc, datastore aggiunti). Lo schema CSV stabile permette diff incrementali.
2. **Tre strumenti, tre angolazioni.** PowerCLI per estrazioni custom e logica complessa; RVTools per snapshot rapido in formato XLSX/CSV (quando manca tempo per lo script); vSphere API REST per integrazioni con altri sistemi (ITSM, CMDB).
3. **Le custom attributes / tags vanno catturati.** Spesso il meta-business (owner, ambiente, costcenter, downtime window) vive solo come tag o custom attribute in vCenter. Senza estrarli, il piano di migrazione perde la classificazione che permette il wave planning.
4. **Snapshot vecchi sono pre-condizione di blocco alla migrazione.** Snapshot > 7-14 giorni vanno consolidati *prima* di iniziare la migrazione: virt-v2v puo lavorare su un VMDK con snapshot ma trasferisce il base disk, perdendo il delta. Includere `vm-snapshots.csv` con flag "stale=true" per snapshot > 7 gg e parte dell'output di assessment.
5. **L'inventario non e solo "quante VM ho".** Include: HW version, ToolsStatus, IP, dipendenze applicative (tier 1-2-3), dipendenze infrastrutturali (DNS, AD, NTP), backup current state, RDM, passthrough HW, snapshot, vApp ordering, custom kernel parameters per Linux, Windows roles installed. La completezza qui = qualita del piano di migrazione.

## Indice
- [Panoramica](#panoramica)
- [Strumenti per la Raccolta dell'Inventario](#strumenti-per-la-raccolta-dellinventario)
- [Raccolta Metadati delle Virtual Machine](#raccolta-metadati-delle-virtual-machine)
- [Inventario Datastore e Storage](#inventario-datastore-e-storage)
- [Inventario Cluster e Host ESXi](#inventario-cluster-e-host-esxi)
- [Inventario Networking](#inventario-networking)
- [Script di Estrazione Automatizzata](#script-di-estrazione-automatizzata)
- [Documentazione dell'Architettura Corrente](#documentazione-dellarchitettura-corrente)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

La fase di inventario rappresenta il fondamento critico di qualsiasi progetto di migrazione da VMware a Proxmox VE. Senza una fotografia accurata e completa dell'infrastruttura esistente, ogni decisione successiva — dal dimensionamento del nuovo ambiente alla pianificazione delle wave di migrazione — poggia su basi instabili. L'obiettivo di questa fase è raccogliere, catalogare e validare ogni componente dell'ambiente VMware: virtual machine, datastore, cluster, networking, policy di backup e configurazioni specifiche.

Un assessment rigoroso consente di identificare non solo le risorse allocate, ma soprattutto quelle effettivamente consumate. La differenza tra provisioned e consumed è spesso significativa negli ambienti VMware maturi, dove il thin provisioning e l'overcommit sono pratiche consolidate. Comprendere questi delta è essenziale per dimensionare correttamente l'ambiente Proxmox di destinazione ed evitare sia il sovradimensionamento (spreco di budget) sia il sottodimensionamento (problemi di performance post-migrazione).

Questo documento copre gli strumenti principali — PowerCLI e RVTools — gli script di automazione per l'estrazione dei dati, le metriche chiave da raccogliere per ogni VM e le tecniche per documentare l'architettura corrente in modo strutturato e riutilizzabile nelle fasi successive del progetto.

---

## Strumenti per la Raccolta dell'Inventario

### VMware PowerCLI

PowerCLI è il modulo PowerShell ufficiale di VMware per l'automazione e la gestione dell'infrastruttura vSphere. È lo strumento più potente e flessibile per l'estrazione di dati inventariali, poiché consente accesso programmatico a tutte le API di vCenter Server.

#### Installazione e Configurazione

```powershell
# Installazione del modulo PowerCLI da PowerShell Gallery
Install-Module -Name VMware.PowerCLI -Scope CurrentUser -Force

# Configurazione per ignorare certificati self-signed (ambienti lab/interni)
Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false

# Configurazione per non partecipare al CEIP (Customer Experience Improvement Program)
Set-PowerCLIConfiguration -ParticipateInCeip $false -Confirm:$false

# Connessione al vCenter Server
Connect-VIServer -Server vcenter.dominio.local -User administrator@vsphere.local -Password 'P@ssw0rd'
```

**Nota di sicurezza**: in ambiente di produzione, evitare di inserire credenziali in chiaro negli script. Utilizzare `Get-Credential` o un vault per la gestione dei secret:

```powershell
# Approccio sicuro con credential store
New-VICredentialStoreItem -Host vcenter.dominio.local -User administrator@vsphere.local -Password 'P@ssw0rd'
Connect-VIServer -Server vcenter.dominio.local
```

#### Comandi Fondamentali di Inventario

```powershell
# Lista di tutte le VM con proprietà base
Get-VM | Select-Object Name, PowerState, NumCpu, MemoryGB, ProvisionedSpaceGB, UsedSpaceGB, Guest, Folder

# Dettaglio completo di una singola VM
Get-VM -Name "web-server-01" | Get-View | Select-Object -ExpandProperty Config

# Lista di tutti gli host ESXi
Get-VMHost | Select-Object Name, ConnectionState, PowerState, NumCpu, CpuTotalMhz, CpuUsageMhz, MemoryTotalGB, MemoryUsageGB

# Lista di tutti i datastore
Get-Datastore | Select-Object Name, Type, CapacityGB, FreeSpaceGB, State

# Lista di tutti i cluster
Get-Cluster | Select-Object Name, HAEnabled, HAFailoverLevel, DrsEnabled, DrsAutomationLevel
```

### RVTools

RVTools è un'applicazione Windows gratuita sviluppata da Rob de Veij che si connette a vCenter Server (o direttamente a un host ESXi) e genera un report Excel completo dell'intera infrastruttura. È particolarmente utile per ottenere rapidamente una visione d'insieme senza scrivere codice.

#### Utilizzo di RVTools

1. Scaricare RVTools da https://www.robware.net/rvtools/
2. Installare ed eseguire l'applicazione
3. Inserire hostname/IP del vCenter, credenziali e porta (default 443)
4. Attendere il completamento della scansione
5. Esportare in formato Excel (.xlsx) o CSV

#### Tab Principali di RVTools

| Tab | Contenuto | Rilevanza per Migrazione |
|-----|-----------|--------------------------|
| vInfo | Nome VM, OS, CPU, RAM, Tools status, power state | **Critica** — base dell'inventario |
| vCPU | Dettaglio CPU per VM, socket, core | **Alta** — sizing CPU |
| vMemory | RAM allocata e consumed per VM | **Alta** — sizing memoria |
| vDisk | Dischi virtuali, dimensione, thin/thick, controller | **Critica** — sizing storage |
| vNetwork | NIC virtuali, MAC, port group, tipo adapter | **Alta** — mapping rete |
| vHost | Dettagli host ESXi, modello, CPU, RAM, versione | **Alta** — confronto hardware |
| vDatastore | Capacità, spazio libero, tipo, VM residenti | **Alta** — capacity planning |
| vSnapshot | Snapshot attivi, dimensione, età | **Critica** — cleanup pre-migrazione |
| vHealth | Problemi rilevati, warning, configurazioni anomale | **Media** — remediation |

#### Export da Linea di Comando

RVTools supporta l'esecuzione da command line per automazione:

```cmd
REM Export completo in Excel
"C:\Program Files (x86)\RVTools\RVTools.exe" -s vcenter.dominio.local -u administrator@vsphere.local -p P@ssw0rd -c ExportAll2xlsx -d "C:\Reports\rvtools_export.xlsx"

REM Export singolo tab in CSV
"C:\Program Files (x86)\RVTools\RVTools.exe" -s vcenter.dominio.local -u administrator@vsphere.local -p P@ssw0rd -c ExportVInfo2csv -d "C:\Reports\vinfo.csv"
```

### Confronto tra Strumenti

| Caratteristica | PowerCLI | RVTools |
|----------------|----------|---------|
| Flessibilità | Massima (scriptabile) | Limitata (report predefiniti) |
| Curva di apprendimento | Media-alta | Bassa |
| Automazione | Completa | Parziale (CLI) |
| Dati real-time performance | Sì (Get-Stat) | No |
| Export personalizzati | Sì | No |
| Costo | Gratuito | Gratuito |
| Requisiti | PowerShell 5.1+ | Windows + .NET |

---

## Raccolta Metadati delle Virtual Machine

Per ogni VM dell'ambiente è necessario raccogliere un set completo di metadati che serviranno nelle fasi successive di sizing, wave planning e migrazione effettiva.

### Metadati Essenziali per VM

#### Configurazione Compute

```powershell
# Estrazione dettagliata CPU e RAM per tutte le VM
Get-VM | ForEach-Object {
    $vm = $_
    $view = $vm | Get-View
    [PSCustomObject]@{
        Name            = $vm.Name
        PowerState      = $vm.PowerState
        NumCPU          = $vm.NumCpu
        NumCoresPerSocket = $view.Config.Hardware.NumCoresPerSocket
        NumSockets      = $vm.NumCpu / $view.Config.Hardware.NumCoresPerSocket
        MemoryGB        = $vm.MemoryGB
        CpuReservationMhz = $view.Config.CpuAllocation.Reservation
        MemReservationMB  = $view.Config.MemoryAllocation.Reservation
        CpuLimitMhz     = $view.Config.CpuAllocation.Limit
        MemLimitMB       = $view.Config.MemoryAllocation.Limit
        CpuHotAdd       = $view.Config.CpuHotAddEnabled
        MemHotAdd       = $view.Config.MemoryHotAddEnabled
        HardwareVersion = $view.Config.Version
        GuestOS         = $view.Config.GuestFullName
        GuestOSId       = $view.Config.GuestId
    }
} | Export-Csv -Path "C:\Reports\vm_compute.csv" -NoTypeInformation
```

#### Configurazione Storage

```powershell
# Dettaglio dischi virtuali per ogni VM
Get-VM | ForEach-Object {
    $vm = $_
    $vm | Get-HardDisk | ForEach-Object {
        [PSCustomObject]@{
            VMName          = $vm.Name
            DiskName        = $_.Name
            CapacityGB      = [math]::Round($_.CapacityGB, 2)
            StorageFormat   = $_.StorageFormat   # Thin, Thick, EagerZeroedThick
            DiskType        = $_.DiskType         # Flat, RawPhysical, RawVirtual
            Filename        = $_.Filename
            Datastore       = ($_.Filename -split ']')[0].TrimStart('[')
            Controller      = $_.ExtensionData.ControllerKey
            UnitNumber      = $_.ExtensionData.UnitNumber
            Persistence     = $_.Persistence
        }
    }
} | Export-Csv -Path "C:\Reports\vm_disks.csv" -NoTypeInformation
```

#### Stato VMware Tools

Lo stato di VMware Tools è particolarmente rilevante per la migrazione: VM con Tools non installati o obsoleti potrebbero avere problemi di quiescing durante la conversione dei dischi.

```powershell
# Report stato VMware Tools
Get-VM | ForEach-Object {
    $vm = $_
    $view = $vm | Get-View
    [PSCustomObject]@{
        VMName          = $vm.Name
        ToolsStatus     = $view.Guest.ToolsStatus          # toolsOk, toolsOld, toolsNotInstalled, toolsNotRunning
        ToolsVersion    = $view.Guest.ToolsVersion
        ToolsVersionStatus = $view.Guest.ToolsVersionStatus # guestToolsCurrent, guestToolsNeedUpgrade, guestToolsNotInstalled
        ToolsRunningStatus = $view.Guest.ToolsRunningStatus # guestToolsRunning, guestToolsNotRunning
        GuestHostname   = $view.Guest.HostName
        GuestIP         = $view.Guest.IpAddress
        GuestOS         = $view.Guest.GuestFullName
    }
} | Export-Csv -Path "C:\Reports\vm_tools.csv" -NoTypeInformation
```

Classificazione degli stati VMware Tools e implicazioni:

| ToolsStatus | Significato | Impatto Migrazione |
|-------------|-------------|-------------------|
| `toolsOk` | Installati e aggiornati | Nessuno — situazione ideale |
| `toolsOld` | Installati ma versione obsoleta | Basso — funzionano ma aggiornare prima se possibile |
| `toolsNotInstalled` | Non installati | Medio — nessun quiescing, verificare driver |
| `toolsNotRunning` | Installati ma non in esecuzione | Medio — verificare stato servizio nel guest OS |

### Configurazione Networking per VM

```powershell
# Dettaglio NIC virtuali per ogni VM
Get-VM | ForEach-Object {
    $vm = $_
    $vm | Get-NetworkAdapter | ForEach-Object {
        [PSCustomObject]@{
            VMName          = $vm.Name
            AdapterName     = $_.Name
            AdapterType     = $_.Type           # e1000, e1000e, vmxnet3, etc.
            NetworkName     = $_.NetworkName
            MacAddress      = $_.MacAddress
            MacType         = if($_.ExtensionData.AddressType -eq "Manual"){"Static"}else{"Dynamic"}
            Connected       = $_.ConnectionState.Connected
            StartConnected  = $_.ConnectionState.StartConnected
            WakeOnLan       = $_.WakeOnLanEnabled
        }
    }
} | Export-Csv -Path "C:\Reports\vm_network.csv" -NoTypeInformation
```

**Nota importante**: il tipo di adapter è critico. Le VM con adapter `vmxnet3` (paravirtualizzato VMware) dovranno passare a `virtio` in Proxmox per performance ottimali. Le VM con `e1000` o `e1000e` possono mantenere lo stesso tipo anche in Proxmox, ma con performance inferiori.

### Snapshot e Backup

```powershell
# Inventario snapshot attivi
Get-VM | Get-Snapshot | ForEach-Object {
    [PSCustomObject]@{
        VMName      = $_.VM.Name
        SnapshotName = $_.Name
        Description = $_.Description
        Created     = $_.Created
        AgeDays     = (New-TimeSpan -Start $_.Created -End (Get-Date)).Days
        SizeGB      = [math]::Round($_.SizeGB, 2)
        IsCurrent   = $_.IsCurrent
        ParentSnapshot = $_.ParentSnapshot
    }
} | Export-Csv -Path "C:\Reports\vm_snapshots.csv" -NoTypeInformation
```

---

## Inventario Datastore e Storage

### Raccolta Informazioni Datastore

```powershell
# Inventario completo datastore
Get-Datastore | ForEach-Object {
    $ds = $_
    $dsView = $ds | Get-View
    [PSCustomObject]@{
        Name                = $ds.Name
        Type                = $ds.Type                  # VMFS, NFS, vSAN
        FileSystemVersion   = $dsView.Info.Vmfs.Version  # VMFS 5, VMFS 6
        CapacityGB          = [math]::Round($ds.CapacityGB, 2)
        FreeSpaceGB         = [math]::Round($ds.FreeSpaceGB, 2)
        UsedSpaceGB         = [math]::Round($ds.CapacityGB - $ds.FreeSpaceGB, 2)
        UsedPercent         = [math]::Round((($ds.CapacityGB - $ds.FreeSpaceGB) / $ds.CapacityGB) * 100, 1)
        State               = $ds.State
        Accessible          = $dsView.Summary.Accessible
        MultipleHostAccess  = $dsView.Summary.MultipleHostAccess
        VMCount             = ($ds | Get-VM).Count
        DatacenterName      = ($ds | Get-Datacenter).Name
    }
} | Export-Csv -Path "C:\Reports\datastores.csv" -NoTypeInformation
```

### Mappatura VM-Datastore

Per ogni VM è fondamentale sapere su quali datastore risiedono i suoi file (vmdk, vmx, swap, log):

```powershell
# Mappatura VM → Datastore
Get-VM | ForEach-Object {
    $vm = $_
    $datastores = ($vm | Get-Datastore).Name -join "; "
    [PSCustomObject]@{
        VMName      = $vm.Name
        Datastores  = $datastores
        UsedSpaceGB = [math]::Round($vm.UsedSpaceGB, 2)
        ProvisionedGB = [math]::Round($vm.ProvisionedSpaceGB, 2)
        ThinRatio   = if($vm.ProvisionedSpaceGB -gt 0){
                        [math]::Round($vm.UsedSpaceGB / $vm.ProvisionedSpaceGB * 100, 1)
                      } else { 0 }
    }
} | Export-Csv -Path "C:\Reports\vm_datastore_map.csv" -NoTypeInformation
```

### Analisi Thin Provisioning

Il rapporto tra spazio provisioned e spazio effettivamente utilizzato è un dato fondamentale per il capacity planning dell'ambiente Proxmox:

```
+------------------------------------------------------------------+
|  Datastore: DS-PROD-01 (VMFS 6)                                |
|  Capacità fisica: 2 TB                                          |
|                                                                  |
|  +-----------+------------+-----------+--------+                |
|  | VM        | Provisioned| Used      | Thin%  |                |
|  +-----------+------------+-----------+--------+                |
|  | web-01    | 200 GB     | 85 GB     | 42.5%  |                |
|  | db-01     | 500 GB     | 320 GB    | 64.0%  |                |
|  | app-01    | 150 GB     | 60 GB     | 40.0%  |                |
|  | app-02    | 150 GB     | 55 GB     | 36.7%  |                |
|  +-----------+------------+-----------+--------+                |
|  Totale Provisioned: 1000 GB (overcommit: 0%)                  |
|  Totale Used:         520 GB (26% capacità fisica)              |
+------------------------------------------------------------------+
```

---

## Inventario Cluster e Host ESXi

### Dettaglio Host ESXi

```powershell
# Inventario completo host ESXi
Get-VMHost | ForEach-Object {
    $vmhost = $_
    $view = $vmhost | Get-View
    [PSCustomObject]@{
        Name              = $vmhost.Name
        ConnectionState   = $vmhost.ConnectionState
        Manufacturer      = $view.Hardware.SystemInfo.Vendor
        Model             = $view.Hardware.SystemInfo.Model
        SerialNumber      = ($view.Hardware.SystemInfo.OtherIdentifyingInfo | Where-Object {$_.IdentifierType.Key -eq "ServiceTag"}).IdentifierValue
        ESXiVersion       = $vmhost.Version
        ESXiBuild         = $vmhost.Build
        CpuModel          = $vmhost.ProcessorType
        CpuSockets        = $view.Hardware.CpuInfo.NumCpuPackages
        CpuCoresTotal     = $view.Hardware.CpuInfo.NumCpuCores
        CpuThreadsTotal   = $view.Hardware.CpuInfo.NumCpuThreads
        CpuTotalMhz       = $vmhost.CpuTotalMhz
        CpuUsageMhz       = $vmhost.CpuUsageMhz
        CpuUsagePercent   = [math]::Round(($vmhost.CpuUsageMhz / $vmhost.CpuTotalMhz) * 100, 1)
        MemoryTotalGB     = [math]::Round($vmhost.MemoryTotalGB, 2)
        MemoryUsageGB     = [math]::Round($vmhost.MemoryUsageGB, 2)
        MemoryUsagePercent = [math]::Round(($vmhost.MemoryUsageGB / $vmhost.MemoryTotalGB) * 100, 1)
        VMCount           = ($vmhost | Get-VM).Count
        DatastoreCount    = ($vmhost | Get-Datastore).Count
        NicCount          = ($vmhost | Get-VMHostNetworkAdapter -Physical).Count
        VMotionEnabled    = ($vmhost | Get-VMHostNetworkAdapter -VMKernel | Where-Object {$_.VMotionEnabled}).Count -gt 0
        MaintenanceMode   = $vmhost.ExtensionData.Runtime.InMaintenanceMode
    }
} | Export-Csv -Path "C:\Reports\esxi_hosts.csv" -NoTypeInformation
```

### Configurazione Cluster

```powershell
# Dettaglio cluster con policy HA e DRS
Get-Cluster | ForEach-Object {
    $cluster = $_
    $view = $cluster | Get-View
    $hosts = $cluster | Get-VMHost
    $vms = $cluster | Get-VM
    [PSCustomObject]@{
        ClusterName         = $cluster.Name
        DatacenterName      = ($cluster | Get-Datacenter).Name
        HostCount           = $hosts.Count
        VMCount             = $vms.Count
        TotalCpuGhz        = [math]::Round(($hosts | Measure-Object -Property CpuTotalMhz -Sum).Sum / 1000, 2)
        TotalMemoryGB       = [math]::Round(($hosts | Measure-Object -Property MemoryTotalGB -Sum).Sum, 2)
        HAEnabled           = $cluster.HAEnabled
        HAAdmissionControl  = $cluster.HAAdmissionControlEnabled
        HAFailoverLevel     = $cluster.HAFailoverLevel
        HARestartPriority   = $view.Configuration.DasConfig.DefaultVmSettings.RestartPriority
        DRSEnabled          = $cluster.DrsEnabled
        DRSAutomationLevel  = $cluster.DrsAutomationLevel
        EVCMode             = $cluster.EVCMode
        VsanEnabled         = $view.ConfigurationEx.VsanConfigInfo.Enabled
    }
} | Export-Csv -Path "C:\Reports\clusters.csv" -NoTypeInformation
```

---

## Inventario Networking

### Virtual Switch e Port Group

```powershell
# Inventario vSwitch standard
Get-VMHost | ForEach-Object {
    $vmhost = $_
    $vmhost | Get-VirtualSwitch -Standard | ForEach-Object {
        $vs = $_
        [PSCustomObject]@{
            HostName    = $vmhost.Name
            SwitchName  = $vs.Name
            NumPorts    = $vs.NumPorts
            NumPortsAvailable = $vs.NumPortsAvailable
            Mtu         = $vs.Mtu
            NicNames    = ($vs.Nic -join ", ")
            PortGroups  = (($vs | Get-VirtualPortGroup).Name -join ", ")
        }
    }
} | Export-Csv -Path "C:\Reports\vswitches.csv" -NoTypeInformation

# Inventario Distributed Switch (se presenti)
Get-VDSwitch | ForEach-Object {
    $vds = $_
    [PSCustomObject]@{
        Name            = $vds.Name
        Version         = $vds.Version
        NumUplinkPorts  = $vds.NumUplinkPorts
        Mtu             = $vds.Mtu
        PortGroupCount  = ($vds | Get-VDPortgroup).Count
        HostCount       = ($vds | Get-VMHost).Count
        ContactName     = $vds.ContactName
    }
} | Export-Csv -Path "C:\Reports\dvswitch.csv" -NoTypeInformation
```

### VLAN Mapping

```powershell
# Mappatura completa VLAN
Get-VirtualPortGroup | ForEach-Object {
    [PSCustomObject]@{
        PortGroupName = $_.Name
        VLanId        = $_.VLanId
        SwitchName    = $_.VirtualSwitchName
        VMCount       = (Get-VM | Get-NetworkAdapter | Where-Object {$_.NetworkName -eq $_.Name}).Count
    }
} | Sort-Object VLanId | Export-Csv -Path "C:\Reports\vlan_map.csv" -NoTypeInformation
```

---

## Script di Estrazione Automatizzata

### Script Completo di Assessment

Il seguente script PowerCLI esegue un assessment completo e genera un report consolidato:

```powershell
#Requires -Modules VMware.PowerCLI
<#
.SYNOPSIS
    Script di assessment completo per migrazione VMware → Proxmox
.DESCRIPTION
    Raccoglie inventario VM, host, datastore, network e genera report CSV e sommario HTML.
.PARAMETER vCenterServer
    FQDN o IP del vCenter Server
.PARAMETER OutputPath
    Cartella di destinazione per i report
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$vCenterServer,

    [Parameter(Mandatory=$false)]
    [string]$OutputPath = "C:\MigrationAssessment"
)

# Creazione cartella output
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportDir = Join-Path $OutputPath $timestamp
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null

# Connessione
Write-Host "[*] Connessione a $vCenterServer..." -ForegroundColor Cyan
$cred = Get-Credential -Message "Inserire credenziali vCenter"
Connect-VIServer -Server $vCenterServer -Credential $cred -ErrorAction Stop

try {
    # 1. Inventario VM
    Write-Host "[*] Raccolta inventario VM..." -ForegroundColor Cyan
    $vmData = Get-VM | ForEach-Object {
        $vm = $_
        $view = $vm | Get-View
        $disks = $vm | Get-HardDisk
        $nics = $vm | Get-NetworkAdapter
        [PSCustomObject]@{
            Name             = $vm.Name
            PowerState       = $vm.PowerState
            NumCPU           = $vm.NumCpu
            MemoryGB         = $vm.MemoryGB
            ProvisionedGB    = [math]::Round($vm.ProvisionedSpaceGB, 2)
            UsedGB           = [math]::Round($vm.UsedSpaceGB, 2)
            GuestOS          = $view.Config.GuestFullName
            ToolsStatus      = $view.Guest.ToolsStatus
            ToolsVersion     = $view.Guest.ToolsVersion
            IPAddress        = $view.Guest.IpAddress
            Hostname         = $view.Guest.HostName
            DiskCount        = $disks.Count
            NicCount         = $nics.Count
            NicTypes         = ($nics.Type | Sort-Object -Unique) -join ", "
            Networks         = ($nics.NetworkName | Sort-Object -Unique) -join ", "
            HWVersion        = $view.Config.Version
            Folder           = $vm.Folder.Name
            ResourcePool     = $vm.ResourcePool.Name
            VMHost           = $vm.VMHost.Name
            Cluster          = ($vm | Get-Cluster).Name
            Datacenter       = ($vm | Get-Datacenter).Name
            Notes            = $view.Config.Annotation
            SnapshotCount    = (Get-Snapshot -VM $vm -ErrorAction SilentlyContinue).Count
        }
    }
    $vmData | Export-Csv -Path "$reportDir\vm_inventory.csv" -NoTypeInformation
    Write-Host "  -> $($vmData.Count) VM catalogate" -ForegroundColor Green

    # 2. Inventario Host
    Write-Host "[*] Raccolta inventario host ESXi..." -ForegroundColor Cyan
    $hostData = Get-VMHost | ForEach-Object {
        $h = $_
        $hview = $h | Get-View
        [PSCustomObject]@{
            Name           = $h.Name
            Version        = $h.Version
            Build          = $h.Build
            Manufacturer   = $hview.Hardware.SystemInfo.Vendor
            Model          = $hview.Hardware.SystemInfo.Model
            CpuModel       = $h.ProcessorType
            CpuSockets     = $hview.Hardware.CpuInfo.NumCpuPackages
            CpuCoresTotal  = $hview.Hardware.CpuInfo.NumCpuCores
            CpuTotalMhz    = $h.CpuTotalMhz
            CpuUsageMhz    = $h.CpuUsageMhz
            MemoryTotalGB  = [math]::Round($h.MemoryTotalGB, 2)
            MemoryUsageGB  = [math]::Round($h.MemoryUsageGB, 2)
            VMCount        = ($h | Get-VM).Count
            Cluster        = ($h | Get-Cluster).Name
        }
    }
    $hostData | Export-Csv -Path "$reportDir\host_inventory.csv" -NoTypeInformation
    Write-Host "  -> $($hostData.Count) host catalogati" -ForegroundColor Green

    # 3. Inventario Datastore
    Write-Host "[*] Raccolta inventario datastore..." -ForegroundColor Cyan
    $dsData = Get-Datastore | ForEach-Object {
        $ds = $_
        [PSCustomObject]@{
            Name        = $ds.Name
            Type        = $ds.Type
            CapacityGB  = [math]::Round($ds.CapacityGB, 2)
            FreeSpaceGB = [math]::Round($ds.FreeSpaceGB, 2)
            UsedPercent = [math]::Round((($ds.CapacityGB - $ds.FreeSpaceGB) / $ds.CapacityGB) * 100, 1)
            State       = $ds.State
            VMCount     = ($ds | Get-VM).Count
        }
    }
    $dsData | Export-Csv -Path "$reportDir\datastore_inventory.csv" -NoTypeInformation

    # 4. Sommario
    Write-Host "[*] Generazione sommario..." -ForegroundColor Cyan
    $summary = @"
    ======================================
    ASSESSMENT VMWARE - SOMMARIO
    Data: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    vCenter: $vCenterServer
    ======================================
    VM Totali:          $($vmData.Count)
    VM Accese:          $(($vmData | Where-Object PowerState -eq 'PoweredOn').Count)
    VM Spente:          $(($vmData | Where-Object PowerState -eq 'PoweredOff').Count)
    Host ESXi:          $($hostData.Count)
    Datastore:          $($dsData.Count)
    CPU Totali (vCPU):  $(($vmData | Measure-Object -Property NumCPU -Sum).Sum)
    RAM Totale (GB):    $(($vmData | Measure-Object -Property MemoryGB -Sum).Sum)
    Storage Used (GB):  $([math]::Round(($vmData | Measure-Object -Property UsedGB -Sum).Sum, 2))
    Storage Prov (GB):  $([math]::Round(($vmData | Measure-Object -Property ProvisionedGB -Sum).Sum, 2))
    VM con Tools OK:    $(($vmData | Where-Object ToolsStatus -eq 'toolsOk').Count)
    VM senza Tools:     $(($vmData | Where-Object ToolsStatus -eq 'toolsNotInstalled').Count)
    VM con Snapshot:    $(($vmData | Where-Object SnapshotCount -gt 0).Count)
    ======================================
"@
    $summary | Out-File "$reportDir\summary.txt"
    Write-Host $summary -ForegroundColor Yellow

} finally {
    Disconnect-VIServer -Server $vCenterServer -Confirm:$false
}

Write-Host "`n[*] Report salvati in: $reportDir" -ForegroundColor Green
```

### Raccolta Metriche di Performance

Oltre all'inventario statico, è fondamentale raccogliere metriche di performance storiche per un sizing accurato:

```powershell
# Raccolta metriche CPU e RAM degli ultimi 30 giorni (media e picco)
$days = 30
$start = (Get-Date).AddDays(-$days)
$finish = Get-Date

Get-VM | Where-Object PowerState -eq "PoweredOn" | ForEach-Object {
    $vm = $_
    $cpuAvg = Get-Stat -Entity $vm -Stat "cpu.usage.average" -Start $start -Finish $finish -IntervalMins 60 |
              Measure-Object -Property Value -Average -Maximum
    $memAvg = Get-Stat -Entity $vm -Stat "mem.usage.average" -Start $start -Finish $finish -IntervalMins 60 |
              Measure-Object -Property Value -Average -Maximum

    [PSCustomObject]@{
        VMName          = $vm.Name
        vCPU            = $vm.NumCpu
        CpuAvgPercent   = [math]::Round($cpuAvg.Average, 1)
        CpuMaxPercent   = [math]::Round($cpuAvg.Maximum, 1)
        MemoryGB        = $vm.MemoryGB
        MemAvgPercent   = [math]::Round($memAvg.Average, 1)
        MemMaxPercent   = [math]::Round($memAvg.Maximum, 1)
        MemAvgUsedGB    = [math]::Round($vm.MemoryGB * $memAvg.Average / 100, 2)
        MemMaxUsedGB    = [math]::Round($vm.MemoryGB * $memAvg.Maximum / 100, 2)
    }
} | Export-Csv -Path "C:\Reports\vm_performance_${days}d.csv" -NoTypeInformation
```

---

## Documentazione dell'Architettura Corrente

### Template di Documentazione

La documentazione dell'architettura corrente dovrebbe includere:

1. **Diagramma logico dell'infrastruttura**
   - Datacenter → Cluster → Host → VM
   - Relazioni tra componenti

2. **Schema di rete**
   - VLAN e subnet
   - Port group → VLAN mapping
   - Firewall rules e segmentazione

3. **Schema storage**
   - Tipo storage (SAN FC, iSCSI, NFS, vSAN)
   - Layout LUN/volume → datastore
   - Policy di replica e DR

4. **Inventario licenze**
   - Edizione vSphere (Standard, Enterprise Plus)
   - Licenze aggiuntive (vSAN, NSX, SRM)
   - Scadenze

### Esempio di Diagramma ASCII dell'Architettura

```
┌─────────────────────────────────────────────────────────────────┐
│                       vCenter Server 8.0                        │
├────────────────────────────────┬────────────────────────────────┤
│        Datacenter: DC-PROD     │       Datacenter: DC-DR        │
│  ┌──────────────────────────┐  │  ┌──────────────────────────┐  │
│  │ Cluster: CL-PROD-01      │  │  │ Cluster: CL-DR-01        │  │
│  │ HA: Enabled (FTL=1)      │  │  │ HA: Enabled (FTL=1)      │  │
│  │ DRS: FullyAutomated      │  │  │ DRS: PartiallyAutomated  │  │
│  │                          │  │  │                          │  │
│  │ ESXi-01  ESXi-02  ESXi-03│  │  │ ESXi-DR-01   ESXi-DR-02 │  │
│  │ 48C/512G 48C/512G 48C/512│  │  │ 32C/256G     32C/256G   │  │
│  │                          │  │  │                          │  │
│  │ VM: 45   VM: 42   VM: 40 │  │  │ VM: 15       VM: 12     │  │
│  └──────────────────────────┘  │  └──────────────────────────┘  │
│                                │                                │
│  Storage:                      │  Storage:                      │
│  ├── DS-PROD-01 (VMFS6, 4TB)  │  ├── DS-DR-01 (VMFS6, 2TB)   │
│  ├── DS-PROD-02 (VMFS6, 4TB)  │  └── DS-DR-02 (VMFS6, 2TB)   │
│  └── DS-PROD-03 (NFS, 8TB)    │                                │
└────────────────────────────────┴────────────────────────────────┘
```

---

## Best Practices

- **Eseguire l'assessment durante orari di bassa attività** per ottenere dati di performance rappresentativi senza impattare l'operatività. Raccogliere metriche per almeno 30 giorni, idealmente includendo fine mese e fine trimestre.
- **Consolidare snapshot prima dell'assessment**. Snapshot vecchi e di grandi dimensioni falsano i dati di spazio utilizzato e possono causare problemi durante la migrazione. Rimuovere o consolidare tutti gli snapshot non necessari.
- **Verificare la coerenza dei dati tra strumenti diversi**. Confrontare i dati di PowerCLI con quelli di RVTools per identificare discrepanze. Se i numeri non corrispondono, investigare la causa.
- **Documentare le eccezioni**. VM con configurazioni non standard (RDM, GPU passthrough, USB passthrough, NPIV, vGPU) richiedono strategie di migrazione specifiche e devono essere identificate esplicitamente.
- **Includere le VM spente nell'inventario**. Le VM in stato PoweredOff sono spesso dimenticate ma occupano storage e potrebbero contenere servizi critici da riattivare periodicamente.
- **Raccogliere anche i dati dei template**. I template VMware dovranno essere ricreati in Proxmox e i loro dati sono necessari per la pianificazione.
- **Salvare i report in formato versionabile**. Utilizzare CSV e testo piuttosto che formati binari, e archiviare i risultati in un repository Git per tracciare l'evoluzione dell'ambiente nel tempo.
- **Validare i dati con il team applicativo**. I metadati tecnici non raccontano tutta la storia: confrontare l'inventario con il CMDB aziendale e con i team che gestiscono le applicazioni per identificare dipendenze e criticità non visibili a livello infrastrutturale.
- **Automatizzare la raccolta periodica**. Schedulare gli script di assessment con un task scheduler per avere dati aggiornati durante tutta la durata del progetto di migrazione.

---

## Troubleshooting

### Problema: PowerCLI non riesce a connettersi al vCenter
**Sintomi**: Errore `Could not connect to vCenter Server` o timeout durante `Connect-VIServer`.
**Causa**: Firewall che blocca la porta 443, certificato non attendibile, credenziali errate, o vCenter Server non raggiungibile.
**Soluzione**:
```powershell
# Verificare connettività di base
Test-NetConnection -ComputerName vcenter.dominio.local -Port 443

# Ignorare certificati self-signed
Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false

# Verificare versione PowerCLI compatibile
Get-Module VMware.PowerCLI -ListAvailable
```
**Prevenzione**: Documentare la versione di vCenter e la versione minima di PowerCLI richiesta. Mantenere aggiornato il modulo PowerCLI.

### Problema: RVTools restituisce dati incompleti o vuoti
**Sintomi**: Alcune tab di RVTools sono vuote o contengono meno VM del previsto.
**Causa**: L'account utilizzato non ha permessi sufficienti su tutti gli oggetti vCenter, oppure la versione di RVTools non è compatibile con la versione di vSphere.
**Soluzione**: Utilizzare un account con ruolo `Read-Only` a livello di root del vCenter. Verificare la compatibilità della versione di RVTools con la versione di vSphere dalla documentazione ufficiale.
**Prevenzione**: Creare un account di servizio dedicato all'assessment con permessi di sola lettura su tutti gli oggetti del vCenter.

### Problema: Get-Stat restituisce errori o nessun dato
**Sintomi**: Errore `The metric counter is not valid or is not available on the server` oppure risultati vuoti.
**Causa**: Le statistiche di performance potrebbero non essere configurate a livello di vCenter, oppure il livello di raccolta statistiche è troppo basso (Level 1 di default raccoglie solo metriche aggregate).
**Soluzione**:
```powershell
# Verificare il livello di statistiche configurato
Get-StatInterval

# Per dati dettagliati, verificare che almeno Level 2 sia configurato
# (da vSphere Client: vCenter > Configure > General > Statistics)

# Utilizzare intervalli di campionamento supportati
Get-Stat -Entity (Get-VM "web-01") -Stat "cpu.usage.average" -Start (Get-Date).AddDays(-1) -IntervalMins 20
```
**Prevenzione**: Prima di iniziare l'assessment, verificare e se necessario aumentare il livello di raccolta statistiche di vCenter (Level 2 o superiore) almeno 30 giorni prima della raccolta dati.

### Problema: Script di assessment molto lento su ambienti grandi
**Sintomi**: Lo script impiega ore per completarsi su ambienti con centinaia di VM.
**Causa**: Ogni chiamata PowerCLI esegue una query API separata. Su ambienti grandi, l'overhead di rete e l'elaborazione lato vCenter diventano significativi.
**Soluzione**: Utilizzare `Get-View` con filtri per ridurre il numero di chiamate API, e parallelizzare dove possibile:
```powershell
# Approccio ottimizzato con Get-View (singola chiamata API)
$vmViews = Get-View -ViewType VirtualMachine -Property Name, Config, Guest, Runtime, Summary
# Elaborare i dati localmente anziché fare chiamate successive
$vmViews | ForEach-Object {
    [PSCustomObject]@{
        Name       = $_.Name
        NumCPU     = $_.Config.Hardware.NumCPU
        MemoryMB   = $_.Config.Hardware.MemoryMB
        GuestOS    = $_.Config.GuestFullName
        PowerState = $_.Runtime.PowerState
    }
}
```
**Prevenzione**: Per ambienti con più di 200 VM, utilizzare sempre l'approccio `Get-View` con proprietà specifiche anziché i cmdlet di alto livello come `Get-VM`.

### Problema: Discrepanza tra spazio reported e spazio effettivo su datastore
**Sintomi**: La somma dello spazio utilizzato dalle VM non corrisponde allo spazio occupato sul datastore.
**Causa**: File orfani (vmdk non associati a VM), file di swap delle VM, log, file .vswp, snapshot delta non visibili.
**Soluzione**:
```powershell
# Ricerca file orfani su datastore
$ds = Get-Datastore "DS-PROD-01"
$dsPath = $ds.DatastoreBrowserPath
$searchSpec = New-Object VMware.Vim.HostDatastoreBrowserSearchSpec
$searchSpec.MatchPattern = @("*.vmdk", "*.vswp", "*.log")
$browser = Get-View $ds.ExtensionData.Browser
$result = $browser.SearchDatastoreSubFolders($dsPath, $searchSpec)
```
**Prevenzione**: Eseguire regolarmente scansioni per file orfani e includere questa verifica nell'assessment.

### Problema: VM con RDM (Raw Device Mapping) non rilevate correttamente
**Sintomi**: Le VM con dischi RDM mostrano dimensioni di disco errate o pari a zero nell'inventario.
**Causa**: I dischi RDM (sia physical mode che virtual mode) non sono file VMDK standard e richiedono una gestione speciale durante la raccolta dati.
**Soluzione**:
```powershell
# Identificare VM con RDM
Get-VM | Get-HardDisk | Where-Object {$_.DiskType -like "Raw*"} | Select-Object @{N="VM";E={$_.Parent.Name}}, Name, DiskType, ScsiCanonicalName, DeviceName, CapacityGB
```
**Prevenzione**: Identificare tutte le VM con RDM all'inizio dell'assessment e documentarle come casi speciali che richiederanno una strategia di migrazione dedicata (conversione a disco virtuale o ricreazione del mapping su Proxmox).

---

## Riferimenti

- VMware PowerCLI Documentation: https://developer.vmware.com/docs/powercli/
- VMware PowerCLI Cmdlet Reference: https://developer.vmware.com/docs/powercli/latest/products/vmwarevsphereandvsan/
- RVTools Official Site: https://www.robware.net/rvtools/
- VMware vSphere API Reference: https://developer.vmware.com/apis/vsphere-automation/latest/
- VMware Compatibility Guide: https://www.vmware.com/resources/compatibility/search.php
- Proxmox VE Migration Documentation: https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE
- PowerShell Gallery — VMware.PowerCLI: https://www.powershellgallery.com/packages/VMware.PowerCLI/

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — PowerCLI 13.x cross-platform.** Da PowerCLI 13.0 (2023) la suite e completamente cross-platform via PowerShell Core 7.x: si installa con `Install-Module VMware.PowerCLI -Scope CurrentUser` su Linux/macOS/Windows. Differenze pratiche: alcuni cmdlet legacy (es. quelli che usano CIM/WSMan) potrebbero non funzionare su Linux; la maggior parte delle operazioni di assessment si. Per un assessment "from scratch", installare PowerCLI 13.x su una workstation Linux dedicata e schedulare con `cron` lo script di re-inventory settimanale.

> **Errore comune — `Connect-VIServer` con certificati self-signed.** Sintomo: `Connect-VIServer` fallisce con errore SSL trust. Soluzione (solo per environment di assessment, NON per integrazione produzione): `Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false`. Per produzione: importare il CA del vCenter come trusted nello store delle certificate di sistema della macchina che esegue lo script.

> **Caso reale — Custom Attributes persi nell'export CSV.** Un assessment ha estratto correttamente l'inventario VM ma omesso i Custom Attributes (campo "Owner" usato dal team operativo per assegnare le VM ai responsabili). Conseguenza: il wave planning per ottenere approvazioni dai owner ha richiesto un secondo round di estrazione. Soluzione: nel template di estrazione, aggiungere sempre `@{N='CustomAttributes';E={ ($_ | Get-Annotation | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join ';' }}`. Lezione: ogni metadato che vive in vCenter come tag/annotation/custom attribute potenzialmente serve nel piano. Estrarli tutti, filtrarli dopo.

---

## Esercizi

1. **Concettuale — PowerCLI vs RVTools vs API.** Scegliere lo strumento giusto per ognuno: (a) snapshot rapido di tutta l'infrastruttura per riunione di stato in 30 min; (b) estrazione settimanale schedulata in CI; (c) integrazione di alcuni dati VM in un sistema ITSM via REST; (d) check di compliance con regola "nessuna VM con HW version < vmx-15". *Risposte:* (a) RVTools (XLSX one-shot, GUI-friendly); (b) PowerCLI scriptato + cron; (c) vSphere API REST diretta; (d) PowerCLI script.

2. **Lab — assessment integrale di un cluster di test.** Connect-VIServer al lab, eseguire i blocchi PowerCLI dal modulo che generano i CSV. Aggiungere un blocco custom che estrae per ogni VM: `CustomAttributes`, `Tags`, `LastBackupDate` (se l'ambiente ha Veeam/altro che lo registra come annotation). Salvare in `assessment-$(date +%Y%m%d).zip`. *Verifica:* lo zip contiene almeno 8 CSV con righe coerenti (#VM identico tra `vm-inventory.csv` e `vm-disks.csv` come "almeno N righe per N VM con dischi").

3. **Scenario — assessment con vCenter offline.** Il vCenter e fuori uso da 3 giorni e non si puo recuperare in tempo. Devi pianificare comunque la migrazione. Argomenta in massimo 12 righe come procedere con assessment usando solo gli host ESXi (`esxcli` e `vim-cmd vmsvc/getallvms`), e quali informazioni *non* riusciresti a ricostruire (clusters, DRS rules, dvSwitches, vApp). *Risposta attesa:* via SSH su ciascun host, eseguire script che produce JSON locale; aggregare i JSON; informazioni mancanti includono cluster-level (HA/DRS settings), dvSwitch (config sta in vCenter), tags vCenter (sta nel DB del vCenter). Ricostruire dvSwitch da `esxcfg-vswitch` e `esxcfg-vmknic` lato host (parziale).

4. **Stretch — script di diff incrementale.** Scrivere uno script Python che, dati due inventory zip a distanza di una settimana, produca un report `diff-report.md` con: VM nuove, VM cancellate, VM con nuovi snapshot, VM con HW version cambiata, datastore con utilization > +10%, port group nuovi/cancellati. Da usare per tracking del "drift" durante il periodo di migrazione.

## Auto-valutazione

1. Differenza fra `Get-VM | Select Name` e `Get-View -ViewType VirtualMachine -Property Name` — quando preferire l'uno o l'altro?
2. Cosa contiene `ExtensionData.Guest.ToolsVersionStatus` e quali valori puo assumere?
3. Quale comando `esxcli` lista lo storage filesystem e i datastore associati?
4. Differenza fra Custom Attribute e Tag in vCenter (storage, cardinality, hierarchy)?
5. Come si esporta un dvSwitch completo (config + portgroup) per backup/audit?
6. Quale campo di un VMDK indica thick eager-zeroed vs thin?
7. Comando per listare tutti gli snapshot orfani (snapshot file presenti su datastore ma non riferiti da nessuna VM)?
8. Cos'e RVTools e in quale formato esporta i dati?

## Letture primarie consigliate

- VMware PowerCLI Documentation. https://developer.vmware.com/docs/powercli/
- VMware PowerCLI Cmdlet Reference (latest). https://developer.vmware.com/docs/powercli/latest/products/vmwarevsphereandvsan/
- RVTools Official Site. https://www.robware.net/rvtools/
- vSphere Automation API. https://developer.vmware.com/apis/vsphere-automation/latest/
- [`VM-COMPAT`] VMware Compatibility Guide. https://www.vmware.com/resources/compatibility/search.php
- [`PVE-MIGRATE-V2V`] Proxmox VE — Migration of servers to Proxmox VE. https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE

## Collegamenti incrociati

- Modulo 01.1 — `../01-FONDAMENTI-VMWARE/architettura-vsphere-esxi.md`: introduce gli oggetti vSphere che qui si censiscono.
- Modulo 01.2 — `../01-FONDAMENTI-VMWARE/vmware-networking-storage.md`: networking e storage da inventariare.
- Modulo 05.2 — `analisi-dipendenze-e-criticita.md`: prossimo modulo, consuma gli output di questo per costruire il grafo di dipendenze.
- Modulo 05.3 — `dimensionamento-proxmox-capacity-planning.md`: usa l'inventario per dimensionare il cluster target.
- Modulo 05.4 — `timeline-e-risk-assessment.md`: usa l'inventario per la valutazione rischio e wave planning.
- Modulo 06.1 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/strategie-metodi-migrazione.md`: la classificazione VM dell'inventario alimenta la scelta cold/warm/live.

## Glossario locale

| Termine | Definizione |
|---|---|
| **PowerCLI** | Suite PowerShell di moduli VMware per script e automazione vSphere. |
| **`Connect-VIServer`** | Cmdlet PowerCLI per stabilire la sessione con un vCenter o ESXi. |
| **`Get-View`** | Cmdlet che ritorna l'oggetto raw `ManagedObjectReference` (piu veloce di `Get-VM` per query massive). |
| **vSphere API** | API SOAP/REST esposta da vCenter; sostituita progressivamente dalla vSphere Automation API REST. |
| **Custom Attribute** | Campo testo personalizzato a livello vCenter (`Set-Annotation`); cardinalita libera. |
| **Tag (vSphere)** | Tassonomia gerarchica (Category → Tag); piu vincolata di un Custom Attribute, supporta multi-tag per oggetto. |
| **`vim-cmd`** | CLI legacy ESXi che dialoga con `hostd` per query e operazioni. |
| **RVTools** | Tool community-maintained che produce un export XLSX/CSV multi-foglio dell'intero ambiente vSphere. |
| **Stale snapshot** | Snapshot piu vecchio della soglia operativa (tipicamente 7-14 giorni) che va consolidato prima della migrazione. |
| **Orphan snapshot** | File `.vmsd` o `-deltaXXX.vmdk` presenti sul datastore ma non riferiti da nessuna VM (residuo di operazioni fallite). |
| **`Get-Annotation`** | Cmdlet PowerCLI per leggere Custom Attributes; restituisce coppie `Name=Value`. |
| **`-View` vs cmdlet diretto** | Le `Get-View` sono ~10x piu veloci per query massive; i cmdlet `Get-VM` sono piu ergonomici. |
