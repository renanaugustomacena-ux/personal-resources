# Hyper-V — Guida Approfondita

> **Modulo 23** · **Aggiornamento:** 2026-05-23

### Obiettivi di Apprendimento

Al termine di questo modulo sarai in grado di:

1. Descrivere l'architettura interna di Hyper-V (partizione root, child partitions, VMBus, VSP/VSC, enlightenments) e le differenze rispetto a hypervisor di tipo 2
2. Progettare e configurare topologie di rete virtualizzate con virtual switch esterni/interni/privati, SET, VLAN tagging, port mirroring e MAC spoofing protection
3. Dimensionare correttamente risorse di CPU, memoria e storage per carichi di produzione, applicando Dynamic Memory, NUMA topology e Storage QoS
4. Implementare scenari di alta disponibilità con Live Migration, Failover Clustering, Cluster Shared Volumes e Hyper-V Replica
5. Configurare Shielded VMs, vTPM e Guarded Fabric per la protezione crittografica delle macchine virtuali
6. Automatizzare il provisioning, il monitoraggio e il backup di infrastrutture Hyper-V tramite PowerShell
7. Diagnosticare e risolvere le 15 problematiche più comuni in ambienti Hyper-V di produzione

### Prerequisiti

| Requisito | Modulo di riferimento |
|-----------|----------------------|
| Active Directory: struttura dominio, account computer, Kerberos delegation | [01-active-directory.md](01-active-directory.md) |
| PowerShell: cmdlet, pipeline, scripting base e avanzato | [02-powershell.md](02-powershell.md), [22-powershell-scripting-avanzato.md](22-powershell-scripting-avanzato.md) |
| Ruoli Windows Server: installazione feature, Server Manager | [03-ruoli-server.md](03-ruoli-server.md) |
| Sicurezza Windows: BitLocker, TPM, policy di sicurezza | [05-sicurezza-windows.md](05-sicurezza-windows.md) |
| Networking Windows: NIC teaming, VLAN, DNS, firewall | [06-rete-windows.md](06-rete-windows.md) |
| Storage Windows: volumi, ReFS, NTFS, iSCSI, SMB | [07-storage-windows.md](07-storage-windows.md) |

> **Tempo stimato:** 4-5 ore (lettura + esercizi)
> **Livello:** Proficient

### Mappa Concettuale

```
                        ┌───────────────────────────────┐
                        │       HYPER-V (Modulo 23)     │
                        └──────────────┬────────────────┘
                                       │
         ┌─────────────────────────────┼──────────────────────────────┐
         │                             │                              │
┌────────▼────────┐          ┌─────────▼─────────┐         ┌─────────▼─────────┐
│  ARCHITETTURA   │          │   RISORSE COMPUTE  │         │    NETWORKING     │
│                 │          │                     │         │                   │
│ Type 1 Hyper.   │          │ CPU: vCPU, NUMA,    │         │ vSwitch: Ext/Int/ │
│ Root Partition  │          │   Compatibility     │         │   Private         │
│ Child Partitions│          │ RAM: Dynamic Mem,   │         │ SET Teaming       │
│ VMBus           │          │   Smart Paging      │         │ VLAN Tagging      │
│ VSP / VSC       │          │ Storage: VHDX,      │         │ Port Mirroring    │
│ Enlightenments  │          │   QoS, Shared VHDX  │         │ MAC Spoofing Prot │
│ SLAT (EPT/RVI)  │          │ Checkpoint: Std/    │         │ Bandwidth Mgmt    │
└────────┬────────┘          │   Production        │         └─────────┬─────────┘
         │                   └─────────┬───────────┘                   │
         │                             │                               │
         └─────────────────────────────┼───────────────────────────────┘
                                       │
         ┌─────────────────────────────┼──────────────────────────────┐
         │                             │                              │
┌────────▼────────┐          ┌─────────▼─────────┐         ┌─────────▼─────────┐
│  ALTA DISPON.   │          │    SICUREZZA       │         │   OPERAZIONI      │
│                 │          │                     │         │                   │
│ Live Migration  │          │ Shielded VMs        │         │ PowerShell Mgmt   │
│ Failover Cluster│          │ vTPM / TPM          │         │ Backup / DR       │
│ CSV             │          │ Guarded Fabric      │         │ Monitoring        │
│ Hyper-V Replica │          │ HGS                 │         │ Resource Metering │
│ DR Planning     │          │ Secure Boot Gen2    │         │ Container Integr. │
│ Extended Replica│          │ Attestation Modes   │         │ Nested Virt.      │
└─────────────────┘          └─────────────────────┘         └───────────────────┘
```

---

## Idee guida
1. **vSwitch security: MAC spoofing protection via `Set-VMNetworkAdapter`.**
2. **VLAN isolation: trunk + access mode.**
3. **Port mirroring for IDS/monitoring.**
4. **Live migration via SMB 3 multi-channel.**


## Indice
- [Panoramica](#panoramica)
- [Architettura dell'Hypervisor](#architettura-dellhypervisor)
- [Enlightenments e Hypercalls](#enlightenments-e-hypercalls)
- [Installazione e Prerequisiti](#installazione-e-prerequisiti)
- [Creazione Macchine Virtuali: Gen1 vs Gen2](#creazione-macchine-virtuali-gen1-vs-gen2)
- [Virtual Switch: External, Internal, Private](#virtual-switch-external-internal-private)
- [Virtual Switch — Configurazione Avanzata](#virtual-switch--configurazione-avanzata)
- [Storage Virtuale: VHD e VHDX](#storage-virtuale-vhd-e-vhdx)
- [Storage — Ottimizzazione Avanzata](#storage--ottimizzazione-avanzata)
- [Gestione della Memoria](#gestione-della-memoria)
- [Configurazione CPU](#configurazione-cpu)
- [Checkpoint: Standard e Production](#checkpoint-standard-e-production)
- [Live Migration](#live-migration)
- [Live Migration — Tuning Avanzato](#live-migration--tuning-avanzato)
- [Failover Clustering e Hyper-V](#failover-clustering-e-hyper-v)
- [Hyper-V Replica](#hyper-v-replica)
- [Hyper-V Replica — Configurazione Avanzata](#hyper-v-replica--configurazione-avanzata)
- [Nested Virtualization](#nested-virtualization)
- [Sicurezza Avanzata: Shielded VMs e Guarded Fabric](#sicurezza-avanzata-shielded-vms-e-guarded-fabric)
- [Integrazione Container](#integrazione-container)
- [Gestione con PowerShell](#gestione-con-powershell)
- [Automazione e Provisioning con PowerShell](#automazione-e-provisioning-con-powershell)
- [Monitoraggio Prestazioni](#monitoraggio-prestazioni)
- [Monitoraggio Avanzato e Health Check](#monitoraggio-avanzato-e-health-check)
- [Disaster Recovery con Hyper-V](#disaster-recovery-con-hyper-v)
- [Confronto con VMware e Proxmox](#confronto-con-vmware-e-proxmox)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Esercizi Pratici](#esercizi-pratici)
- [Autovalutazione](#autovalutazione)
- [Cross-link ai Moduli Correlati](#cross-link-ai-moduli-correlati)
- [Riferimenti](#riferimenti)
- [Glossario Locale](#glossario-locale)

---

## Panoramica

Hyper-V è l'hypervisor di tipo 1 (bare-metal) sviluppato da Microsoft, integrato in Windows Server e nelle edizioni Pro/Enterprise/Education di Windows 10/11. A differenza degli hypervisor di tipo 2 (come VirtualBox), Hyper-V si inserisce direttamente tra l'hardware fisico e il sistema operativo, trasformando il sistema operativo host stesso in una partizione virtuale privilegiata. Questo approccio architetturale garantisce prestazioni significativamente superiori e un isolamento più robusto tra le macchine virtuali.

La piattaforma Hyper-V ha subito un'evoluzione costante dalla sua introduzione in Windows Server 2008, raggiungendo un livello di maturità che la rende competitiva con VMware vSphere in ambienti enterprise. Le funzionalità chiave includono Live Migration per lo spostamento di VM senza downtime, Hyper-V Replica per il disaster recovery, Shielded VMs per la protezione crittografica delle VM, e un'integrazione profonda con System Center e Azure per la gestione ibrida.

Questa guida copre l'architettura interna di Hyper-V, la configurazione delle macchine virtuali e delle reti, le funzionalità avanzate di alta disponibilità e replica, la gestione tramite PowerShell e il monitoraggio delle prestazioni, fornendo una base completa per l'implementazione e la gestione di infrastrutture virtualizzate Microsoft.

---

## Architettura dell'Hypervisor

### Hypervisor di Tipo 1

Hyper-V è un hypervisor thin-layer che viene caricato prima del sistema operativo. Quello che appare come il "sistema operativo host" è in realtà la **partizione parent** (o root partition), una macchina virtuale privilegiata che ha accesso diretto all'hardware e gestisce le partizioni figlio (child partitions, ovvero le VM guest).

```
┌───────────────────────────────────────────────────┐
│                    Hardware Fisico                  │
│  (CPU, RAM, NIC, Storage, GPU)                     │
├───────────────────────────────────────────────────┤
│              Hyper-V Hypervisor                     │
│  (Microkernel: scheduling, memory management,      │
│   partition isolation, interrupt virtualization)    │
├──────────┬──────────┬──────────┬──────────────────┤
│ Parent   │ Child    │ Child    │ Child            │
│ Partition│ Part. 1  │ Part. 2  │ Part. 3          │
│          │          │          │                  │
│ Windows  │ Windows  │ Linux    │ Windows          │
│ Server   │ Server   │ Ubuntu   │ 11               │
│ 2022     │ 2019     │ 22.04   │                  │
│          │          │          │                  │
│ VMBus    │ VMBus    │ VMBus    │ VMBus            │
│ Provider │ Consumer │ Consumer │ Consumer         │
│          │          │          │                  │
│ VSP      │ VSC      │ VSC      │ VSC              │
│ (drivers)│ (synth)  │ (synth)  │ (synth)          │
└──────────┴──────────┴──────────┴──────────────────┘
```

### Componenti Chiave

**VMBus (Virtual Machine Bus):** Canale di comunicazione ad alta velocità tra la partizione parent e le partizioni figlio. Utilizza memoria condivisa per minimizzare l'overhead della virtualizzazione I/O.

**VSP (Virtualization Service Provider):** Driver nella partizione parent che gestiscono l'accesso all'hardware fisico (rete, storage, video). Il VSP riceve le richieste dalle partizioni figlio e le inoltra ai driver hardware reali.

**VSC (Virtualization Service Consumer):** Driver sintetici nella partizione figlio che comunicano con i VSP tramite VMBus. I driver sintetici sono significativamente più performanti dei driver emulati perché eliminano il layer di emulazione hardware.

**Integration Services:** Pacchetto di driver e servizi installati nel guest OS che abilitano le funzionalità avanzate: time synchronization, heartbeat, data exchange (KVP), shutdown integrato, volume shadow copy per backup. I sistemi operativi moderni (Windows 10+, Ubuntu 18.04+, RHEL 7+) includono già gli Integration Services nel kernel.

### SLAT e Virtualizzazione Hardware

Hyper-V richiede **SLAT (Second Level Address Translation)** — implementata come EPT (Extended Page Tables) su Intel e RVI (Rapid Virtualization Indexing) su AMD. SLAT permette all'hypervisor di tradurre gli indirizzi di memoria guest in indirizzi fisici senza l'overhead delle shadow page tables, migliorando drasticamente le prestazioni.

```powershell
# Verificare il supporto hardware per Hyper-V
systeminfo | Select-String "Hyper-V"

# Verifica dettagliata
Get-CimInstance Win32_Processor | Select-Object Name, VirtualizationFirmwareEnabled,
    SecondLevelAddressTranslationExtensions, VMMonitorModeExtensions
```

---

## Enlightenments e Hypercalls

Le **enlightenments** sono ottimizzazioni specifiche che il guest OS può sfruttare quando è consapevole di girare su Hyper-V. A differenza della paravirtualizzazione completa (dove l'intero kernel è modificato), le enlightenments sono estensioni chirurgiche che eliminano le operazioni più costose della virtualizzazione classica.

### Tipologie di Enlightenment

**Hypercalls:** Chiamate dirette dal guest OS all'hypervisor, analoghe alle syscall verso il kernel. Il guest OS usa l'istruzione `VMCALL` (Intel) o `VMMCALL` (AMD) per richiedere servizi all'hypervisor senza passare per l'emulazione hardware.

**Synthetic Interrupts:** Le interruzioni tradizionali (APIC emulato) richiedono VM-exit costose. Le synthetic interrupts utilizzano il SynIC (Synthetic Interrupt Controller), un'interfaccia paravirtualizzata che riduce drasticamente il numero di VM-exit per la gestione degli interrupt.

**APIC Virtualization:** L'Advanced Programmable Interrupt Controller virtualizzato elimina la necessità di emulare l'hardware APIC. Su processori Intel con APICv (o AMD AVIC), molte operazioni APIC vengono gestite direttamente in hardware senza VM-exit.

**Enlightened VMCS (Virtual Machine Control Structure):** Quando Hyper-V gira in nested virtualization, l'hypervisor L1 può usare un VMCS enlightened che riduce il costo delle transizioni VM-entry/VM-exit nell'hypervisor L2.

**Reference TSC (Time Stamp Counter):** Il guest OS accede a un TSC di riferimento condiviso tramite una pagina di memoria mappata, eliminando le VM-exit per la lettura del timestamp — operazione frequentissima nei workload moderni.

### Verifica delle Enlightenments Attive

```powershell
# Verificare le enlightenments attive su una VM (dalla partizione parent)
Get-VMProcessor -VMName "SRV-APP01" | Select-Object `
    ExposeVirtualizationExtensions,
    EnableHostResourceProtection

# Verificare dal guest OS (Windows)
# CPUID leaf 0x40000003 espone le enlightenment flags
Get-CimInstance -Namespace root\wmi -ClassName Msvm_SummaryInformation -ErrorAction SilentlyContinue |
    Select-Object Name, NumberOfProcessors

# Verificare le enlightenments dal guest Linux
# dmesg | grep -i hyperv
# cat /sys/devices/hyperv/vmbus/version
```

### Impatto sulle Prestazioni

Le enlightenments sono particolarmente rilevanti per workload con elevato I/O o frequenti context switch. L'overhead della virtualizzazione con enlightenments attive si riduce tipicamente al 2-5%, rispetto al 10-15% senza.

| Operazione | Senza Enlightenments | Con Enlightenments | Miglioramento |
|-----------|---------------------|-------------------|---------------|
| Timer interrupt | VM-exit + emulazione | SynIC diretto | ~10x |
| TLB flush | Full flush + VM-exit | Hypercall mirato | ~5x |
| Spinlock acquire | Busy-wait cieco | Hypercall + yield | ~3x |
| TSC read | VM-exit | Pagina TSC mappata | ~50x |

---

## Installazione e Prerequisiti

### Prerequisiti Hardware

- CPU a 64 bit con supporto alla virtualizzazione (Intel VT-x o AMD-V)
- SLAT (EPT o RVI)
- Minimo 4 GB di RAM (raccomandati 8 GB+ per il host, più RAM dedicata alle VM)
- Virtualizzazione abilitata nel BIOS/UEFI
- DEP (Data Execution Prevention) abilitato nel BIOS

### Installazione su Windows Server

```powershell
# Installare il ruolo Hyper-V con gli strumenti di gestione
Install-WindowsFeature -Name Hyper-V -IncludeManagementTools -Restart

# Verificare l'installazione
Get-WindowsFeature Hyper-V | Select-Object Name, InstallState

# Installare solo gli strumenti di gestione (su una workstation admin)
Install-WindowsFeature -Name RSAT-Hyper-V-Tools -IncludeAllSubFeature
```

### Installazione su Windows 10/11

```powershell
# Abilitare Hyper-V su Windows client
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart

# Oppure tramite DISM
dism /Online /Enable-Feature /FeatureName:Microsoft-Hyper-V /All

# Verificare
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V | Select-Object State
```

### Configurazione Iniziale del Host

```powershell
# Configurare il percorso predefinito per le VM
Set-VMHost -VirtualMachinePath "D:\Hyper-V\VMs" -VirtualHardDiskPath "D:\Hyper-V\VHDs"

# Configurare il NUMA spanning (disabilitare per prestazioni ottimali)
Set-VMHost -NumaSpanningEnabled $false

# Configurare le Live Migration (se in cluster o standalone)
Set-VMHost -MaximumVirtualMachineMigrations 2 `
    -MaximumStorageMigrations 2 `
    -VirtualMachineMigrationAuthenticationType Kerberos `
    -VirtualMachineMigrationPerformanceOption SMBTransport

# Abilitare Enhanced Session Mode (per connessioni RDP-like alla console VM)
Set-VMHost -EnableEnhancedSessionMode $true

# Verificare la configurazione
Get-VMHost | Format-List *
```

---

## Creazione Macchine Virtuali: Gen1 vs Gen2

### Generazione 1

Le VM di Generazione 1 emulano hardware legacy: BIOS tradizionale, controller IDE per il boot, controller SCSI per storage aggiuntivo, scheda di rete legacy (emulata). Supportano un'ampia gamma di sistemi operativi guest, inclusi quelli più vecchi.

### Generazione 2

Le VM di Generazione 2 utilizzano firmware UEFI, Secure Boot, boot da controller SCSI (più veloce), supporto nativo per dischi VHDX di grandi dimensioni, e non hanno hardware emulato legacy. Sono raccomandate per tutti i sistemi operativi moderni.

| Caratteristica | Gen 1 | Gen 2 |
|---------------|-------|-------|
| Firmware | BIOS | UEFI |
| Secure Boot | No | Sì |
| Boot da SCSI | No | Sì |
| Boot PXE | NIC legacy | NIC sintetica |
| VHDX > 2 TB boot | No | Sì |
| Hot Add/Remove vNIC | No | Sì |
| Hot Resize VHDX | No | Sì |
| OS Supportati | Tutti | 64-bit moderni |
| Linux Boot | Sì | Sì (con template Secure Boot appropriato) |

```powershell
# Creare una VM Generation 2
$vmParams = @{
    Name               = "SRV-APP01"
    Generation         = 2
    MemoryStartupBytes = 4GB
    SwitchName         = "vSwitch-External"
    NewVHDPath         = "D:\Hyper-V\VHDs\SRV-APP01-OS.vhdx"
    NewVHDSizeBytes    = 80GB
    Path               = "D:\Hyper-V\VMs"
}
$vm = New-VM @vmParams

# Configurare la VM
Set-VM -Name "SRV-APP01" -ProcessorCount 4 -DynamicMemory `
    -MemoryMinimumBytes 2GB -MemoryMaximumBytes 8GB `
    -AutomaticStartAction StartIfRunning `
    -AutomaticStopAction ShutDown `
    -AutomaticStartDelay 60 `
    -Notes "Application server per ERP - Ambiente Produzione"

# Configurare Secure Boot per Linux
Set-VMFirmware -VMName "SRV-APP01" -SecureBootTemplate MicrosoftUEFICertificateAuthority

# Aggiungere disco dati
$dataVhdPath = "D:\Hyper-V\VHDs\SRV-APP01-Data.vhdx"
New-VHD -Path $dataVhdPath -SizeBytes 200GB -Dynamic
Add-VMHardDiskDrive -VMName "SRV-APP01" -Path $dataVhdPath -ControllerType SCSI

# Montare ISO per installazione OS
Add-VMDvdDrive -VMName "SRV-APP01" -Path "D:\ISO\WinServer2022.iso"
$dvd = Get-VMDvdDrive -VMName "SRV-APP01"
Set-VMFirmware -VMName "SRV-APP01" -FirstBootDevice $dvd

# Abilitare TPM virtuale (necessario per Windows 11 e BitLocker)
Set-VMKeyProtector -VMName "SRV-APP01" -NewLocalKeyProtector
Enable-VMTPM -VMName "SRV-APP01"

# Avviare la VM
Start-VM -Name "SRV-APP01"
```

---

## Virtual Switch: External, Internal, Private

I virtual switch di Hyper-V gestiscono la connettività di rete delle macchine virtuali. Esistono tre tipologie fondamentali con caratteristiche diverse.

### External Virtual Switch

Collega le VM alla rete fisica attraverso una NIC fisica del host. Le VM possono comunicare con la rete esterna, con altre VM e con il host.

```
┌─────────────────────────────────────────┐
│           Rete Fisica (LAN)             │
└────────────────┬────────────────────────┘
                 │ NIC Fisica (es. Intel I350)
┌────────────────┴────────────────────────┐
│         vSwitch External                 │
├──────┬──────┬──────┬────────────────────┤
│ VM1  │ VM2  │ VM3  │ Management OS vNIC │
└──────┴──────┴──────┴────────────────────┘
```

```powershell
# Creare un External Virtual Switch
New-VMSwitch -Name "vSwitch-Prod" -NetAdapterName "Ethernet0" `
    -AllowManagementOS $true -Notes "Switch di produzione - VLAN Trunk"

# Con NIC teaming (SET - Switch Embedded Teaming)
New-VMSwitch -Name "vSwitch-SET" -NetAdapterName "NIC1","NIC2" `
    -EnableEmbeddedTeaming $true -AllowManagementOS $true
```

### Internal Virtual Switch

Permette la comunicazione tra le VM e il host, ma non con la rete fisica esterna. Utile per creare reti di management o di servizio isolate.

```powershell
# Creare un Internal Switch
New-VMSwitch -Name "vSwitch-Internal" -SwitchType Internal

# Configurare un IP sul host per la rete interna
$adapter = Get-NetAdapter | Where-Object Name -like "*vSwitch-Internal*"
New-NetIPAddress -InterfaceIndex $adapter.ifIndex -IPAddress "172.16.0.1" `
    -PrefixLength 24
```

### Private Virtual Switch

Le VM possono comunicare solo tra loro. Il host non ha accesso alla rete. Ideale per ambienti di laboratorio e test isolati.

```powershell
# Creare un Private Switch
New-VMSwitch -Name "vSwitch-Lab" -SwitchType Private
```

### VLAN Tagging

```powershell
# Assegnare una VLAN a una VM
Set-VMNetworkAdapterVlan -VMName "SRV-APP01" -Access -VlanId 100

# Configurare trunk (per VM che devono gestire più VLAN, es. router virtuale)
Set-VMNetworkAdapterVlan -VMName "SRV-ROUTER" -Trunk -NativeVlanId 1 `
    -AllowedVlanIdList "100,200,300"

# Verificare la configurazione VLAN
Get-VMNetworkAdapterVlan -VMName "SRV-APP01"
```

### Bandwidth Management

```powershell
# Abilitare la gestione della bandwidth sul virtual switch
Set-VMSwitch -Name "vSwitch-Prod" -DefaultFlowMinimumBandwidthWeight 50

# Configurare limiti per VM specifica
Set-VMNetworkAdapter -VMName "SRV-APP01" -MinimumBandwidthWeight 30
Set-VMNetworkAdapter -VMName "SRV-BACKUP" -MaximumBandwidth 1000000000  # 1 Gbps max
```

---

## Virtual Switch — Configurazione Avanzata

### Switch Embedded Teaming (SET)

SET è l'alternativa moderna al NIC Teaming tradizionale (LBFO) per ambienti Hyper-V. A differenza del LBFO, SET è integrato direttamente nel virtual switch e supporta RDMA, SDN e funzionalità avanzate non disponibili con il teaming classico.

```
┌─────────────────────────────────────────────────────┐
│                    Rete Fisica                       │
└──────────┬──────────────────────┬───────────────────┘
           │ NIC1 (10GbE)         │ NIC2 (10GbE)
┌──────────┴──────────────────────┴───────────────────┐
│          vSwitch-SET (Embedded Teaming)              │
│  Load Balancing: Hyper-V Port / Dynamic             │
│  Failover: Active-Active                            │
├──────┬──────┬──────┬──────┬─────────────────────────┤
│ VM1  │ VM2  │ VM3  │ VM4  │ Management OS vNIC      │
│VLAN  │VLAN  │VLAN  │VLAN  │ + Live Migration vNIC   │
│ 100  │ 100  │ 200  │ 200  │ + Cluster vNIC          │
└──────┴──────┴──────┴──────┴─────────────────────────┘
```

```powershell
# Creare un SET con due NIC 10GbE
New-VMSwitch -Name "vSwitch-SET" `
    -NetAdapterName "NIC1-10GbE","NIC2-10GbE" `
    -EnableEmbeddedTeaming $true `
    -AllowManagementOS $true `
    -MinimumBandwidthMode Weight

# Configurare l'algoritmo di load balancing
Set-VMSwitchTeam -Name "vSwitch-SET" -LoadBalancingAlgorithm Dynamic

# Verificare la configurazione SET
Get-VMSwitchTeam -Name "vSwitch-SET" | Select-Object Name, NetAdapterInterfaceDescription,
    TeamingMode, LoadBalancingAlgorithm

# Aggiungere vNIC separate per management, migration e cluster
Add-VMNetworkAdapter -ManagementOS -SwitchName "vSwitch-SET" -Name "Management"
Add-VMNetworkAdapter -ManagementOS -SwitchName "vSwitch-SET" -Name "LiveMigration"
Add-VMNetworkAdapter -ManagementOS -SwitchName "vSwitch-SET" -Name "Cluster"

# Assegnare VLAN alle vNIC del management OS
Set-VMNetworkAdapterVlan -ManagementOS -VMNetworkAdapterName "Management" -Access -VlanId 10
Set-VMNetworkAdapterVlan -ManagementOS -VMNetworkAdapterName "LiveMigration" -Access -VlanId 20
Set-VMNetworkAdapterVlan -ManagementOS -VMNetworkAdapterName "Cluster" -Access -VlanId 30

# Configurare bandwidth weight per traffico prioritario
Set-VMNetworkAdapter -ManagementOS -Name "LiveMigration" -MinimumBandwidthWeight 40
Set-VMNetworkAdapter -ManagementOS -Name "Cluster" -MinimumBandwidthWeight 10
```

### Port Mirroring

Il port mirroring consente di copiare il traffico di rete di una VM verso una VM di monitoraggio (IDS, sniffer, SIEM). È essenziale per il security monitoring senza agenti inline.

```powershell
# Configurare la VM sorgente come "Source" del mirroring
Set-VMNetworkAdapter -VMName "SRV-WEB01" -PortMirroring Source

# Configurare la VM di monitoraggio come "Destination"
Set-VMNetworkAdapter -VMName "SRV-IDS01" -PortMirroring Destination

# Verificare la configurazione
Get-VMNetworkAdapter -VMName "SRV-WEB01" | Select-Object VMName, PortMirroringMode
Get-VMNetworkAdapter -VMName "SRV-IDS01" | Select-Object VMName, PortMirroringMode

# Disabilitare il mirroring
Set-VMNetworkAdapter -VMName "SRV-WEB01" -PortMirroring None
```

### MAC Spoofing Protection

La protezione MAC spoofing impedisce alle VM di inviare frame con un indirizzo MAC diverso da quello assegnato. È abilitata per default e dovrebbe essere disabilitata solo quando strettamente necessario (nested virtualization, NLB, bridge software).

```powershell
# Verificare lo stato della protezione MAC su tutte le VM
Get-VM | Get-VMNetworkAdapter | Select-Object VMName, MacAddress,
    MacAddressSpoofing, DhcpGuard, RouterGuard | Format-Table -AutoSize

# Abilitare protezioni avanzate su una VM
Set-VMNetworkAdapter -VMName "SRV-APP01" `
    -MacAddressSpoofing Off `
    -DhcpGuard On `
    -RouterGuard On

# DHCP Guard: impedisce alla VM di rispondere come DHCP server
# Router Guard: impedisce alla VM di annunciarsi come router (RA)
```

### Extended Port ACL

Le Extended Port ACL forniscono un firewall a livello di virtual switch, applicabile per singola VM o per l'intero switch.

```powershell
# Bloccare tutto il traffico in ingresso verso la VM tranne HTTP/HTTPS/RDP
Add-VMNetworkAdapterExtendedAcl -VMName "SRV-WEB01" -Direction Inbound `
    -Action Allow -LocalPort 80 -Protocol TCP -Weight 10
Add-VMNetworkAdapterExtendedAcl -VMName "SRV-WEB01" -Direction Inbound `
    -Action Allow -LocalPort 443 -Protocol TCP -Weight 10
Add-VMNetworkAdapterExtendedAcl -VMName "SRV-WEB01" -Direction Inbound `
    -Action Allow -LocalPort 3389 -Protocol TCP -Weight 10
Add-VMNetworkAdapterExtendedAcl -VMName "SRV-WEB01" -Direction Inbound `
    -Action Deny -Weight 1

# Elencare le ACL configurate
Get-VMNetworkAdapterExtendedAcl -VMName "SRV-WEB01" | Format-Table -AutoSize
```

---

## Storage Virtuale: VHD e VHDX

### Formato VHDX

Il formato VHDX, introdotto con Hyper-V 3.0, è il successore del VHD con miglioramenti significativi:

| Caratteristica | VHD | VHDX |
|---------------|-----|------|
| Dimensione massima | 2 TB | 64 TB |
| Dimensione settore | 512 bytes | 4 KB (allineato) |
| Protezione corruzione | Limitata | Logging interno |
| Resize online | No | Sì |
| Large sector support | No | Sì (4K native) |

### Tipi di Disco Virtuale

```powershell
# Disco dinamico (cresce su richiesta, più efficiente nello spazio)
New-VHD -Path "D:\VHDs\dynamic.vhdx" -SizeBytes 200GB -Dynamic

# Disco fisso (allocazione completa, prestazioni migliori)
New-VHD -Path "D:\VHDs\fixed.vhdx" -SizeBytes 200GB -Fixed

# Disco differencing (figlio di un disco parent, per template)
New-VHD -Path "D:\VHDs\child.vhdx" -ParentPath "D:\VHDs\template-ws2022.vhdx" -Differencing

# Verificare le informazioni di un disco
Get-VHD -Path "D:\VHDs\dynamic.vhdx" | Select-Object VhdType, FileSize, Size, MinimumSize

# Compattare un disco dinamico (recuperare spazio)
Optimize-VHD -Path "D:\VHDs\dynamic.vhdx" -Mode Full

# Ridimensionare un disco (online, senza spegnere la VM per VHDX su SCSI)
Resize-VHD -Path "D:\VHDs\dynamic.vhdx" -SizeBytes 300GB

# Convertire da VHD a VHDX
Convert-VHD -Path "D:\VHDs\old.vhd" -DestinationPath "D:\VHDs\new.vhdx" -VHDType Dynamic
```

---

## Storage — Ottimizzazione Avanzata

### Storage Quality of Service (QoS)

Storage QoS consente di limitare e garantire IOPS per singola VM o per gruppi di VM, prevenendo il fenomeno del "noisy neighbor" dove una VM con I/O intensivo degrada le prestazioni delle altre.

```powershell
# Configurare limiti IOPS su un disco virtuale
Set-VMHardDiskDrive -VMName "SRV-DEV01" -ControllerType SCSI -ControllerNumber 0 `
    -ControllerLocation 0 -MaximumIOPS 500

# Configurare IOPS minimi garantiti
Set-VMHardDiskDrive -VMName "SRV-SQL01" -ControllerType SCSI -ControllerNumber 0 `
    -ControllerLocation 0 -MinimumIOPS 1000 -MaximumIOPS 5000

# Verificare le policy QoS configurate
Get-VMHardDiskDrive -VMName "SRV-SQL01" | Select-Object VMName, Path,
    MaximumIOPS, MinimumIOPS

# Monitorare gli IOPS attuali per VM
Get-VM | Where-Object State -eq Running | ForEach-Object {
    $vmName = $_.Name
    Get-VMHardDiskDrive -VMName $vmName | ForEach-Object {
        [PSCustomObject]@{
            VM   = $vmName
            Disk = Split-Path $_.Path -Leaf
            MaxIOPS = $_.MaximumIOPS
            MinIOPS = $_.MinimumIOPS
        }
    }
} | Format-Table -AutoSize
```

### Shared VHDX per Guest Clustering

Lo Shared VHDX (e il più recente VHD Set — `.vhds`) consente a più VM di accedere contemporaneamente allo stesso disco virtuale. È utilizzato per il guest clustering (cluster Windows all'interno delle VM) senza la necessità di storage condiviso fisico (iSCSI/FC) a livello guest.

```powershell
# Creare un VHD Set (formato raccomandato per shared disk, sostituisce Shared VHDX)
New-VHD -Path "C:\ClusterStorage\Volume1\SharedDisk.vhds" -SizeBytes 100GB -Fixed

# Aggiungere il disco condiviso a entrambe le VM del guest cluster
# Il disco deve essere su un CSV o SMB share
Add-VMHardDiskDrive -VMName "SQL-NODE01" `
    -Path "C:\ClusterStorage\Volume1\SharedDisk.vhds" `
    -ControllerType SCSI -SupportPersistentReservations

Add-VMHardDiskDrive -VMName "SQL-NODE02" `
    -Path "C:\ClusterStorage\Volume1\SharedDisk.vhds" `
    -ControllerType SCSI -SupportPersistentReservations
```

### ReFS e Integrazione VHDX

ReFS (Resilient File System) offre vantaggi specifici per lo storage Hyper-V grazie al **block cloning** — la capacità di copiare blocchi logici senza spostare dati fisici.

**Vantaggi di ReFS per Hyper-V:**

- **Creazione istantanea di dischi fissi:** Su ReFS, `New-VHD -Fixed` completa in secondi anziché minuti perché i blocchi vengono allocati tramite metadata operation senza scrivere zeri.
- **Merge checkpoint veloce:** La rimozione di un checkpoint (merge dell'.avhdx nel parent) usa block cloning, riducendo il tempo da minuti a secondi per dischi di grandi dimensioni.
- **Integrity streams:** Protezione opzionale contro la corruzione silenziosa dei dati (bit rot) su volumi non ridondati.

```powershell
# Verificare il filesystem del volume di storage
Get-Volume | Where-Object DriveLetter -eq "D" | Select-Object DriveLetter, FileSystemType, Size

# Formattare un volume come ReFS (per storage Hyper-V dedicato)
# Format-Volume -DriveLetter E -FileSystem ReFS -AllocationUnitSize 64KB -NewFileSystemLabel "HV-Storage"

# Verificare la velocità di creazione di un disco fisso su ReFS
Measure-Command { New-VHD -Path "E:\VHDs\test-fixed.vhdx" -SizeBytes 100GB -Fixed }
# Su ReFS: ~1-3 secondi. Su NTFS: ~2-5 minuti per 100GB.
```

---

## Gestione della Memoria

### Dynamic Memory

Dynamic Memory consente a Hyper-V di regolare la quantità di memoria assegnata a una VM in tempo reale, basandosi sulla domanda effettiva. Il meccanismo utilizza il **ballooning driver** (Integration Services) per recuperare memoria non utilizzata dalle VM e riallocarla dove serve.

```
Dynamic Memory — Flusso di allocazione:

                ┌──────────────────────────────────┐
                │        Physical RAM (128 GB)      │
                └──────────┬───────────────────────┘
                           │
            ┌──────────────┼──────────────────┐
            │              │                  │
    ┌───────▼───────┐ ┌────▼────────┐ ┌───────▼───────┐
    │   VM-SQL01    │ │  VM-WEB01   │ │  VM-DEV01     │
    │               │ │             │ │               │
    │ Startup: 4 GB │ │ Startup: 2GB│ │ Startup: 2 GB │
    │ Min:     2 GB │ │ Min:    1GB │ │ Min:     1 GB │
    │ Max:    32 GB │ │ Max:    8GB │ │ Max:     8 GB │
    │ Buffer:   20% │ │ Buffer: 20% │ │ Buffer:   20% │
    │ Weight:  8000 │ │ Weight: 5000│ │ Weight:  2000 │
    │               │ │             │ │               │
    │ Actual:  16GB │ │ Actual: 3GB │ │ Actual:  2 GB │
    │ Demand:  13GB │ │ Demand: 2GB │ │ Demand:  1 GB │
    └───────────────┘ └─────────────┘ └───────────────┘
```

```powershell
# Configurare Dynamic Memory con parametri ottimali
Set-VM -Name "SRV-SQL01" -DynamicMemory `
    -MemoryStartupBytes 4GB `
    -MemoryMinimumBytes 2GB `
    -MemoryMaximumBytes 32GB

# Configurare il buffer e il peso della memoria
Set-VMMemory -VMName "SRV-SQL01" -Buffer 20 -Priority 8000

# Buffer = % di memoria addizionale mantenuta oltre la domanda attuale
# Priority (Weight) = 0-10000, determina chi riceve memoria in caso di contesa

# Monitorare l'allocazione dinamica in tempo reale
Get-VM | Where-Object {$_.State -eq "Running" -and $_.DynamicMemoryEnabled} |
    Select-Object Name,
        @{N='StartupMB';E={[math]::Round($_.MemoryStartup/1MB)}},
        @{N='AssignedMB';E={[math]::Round($_.MemoryAssigned/1MB)}},
        @{N='DemandMB';E={[math]::Round($_.MemoryDemand/1MB)}},
        @{N='MinMB';E={[math]::Round($_.MemoryMinimum/1MB)}},
        @{N='MaxMB';E={[math]::Round($_.MemoryMaximum/1MB)}},
        MemoryStatus |
    Format-Table -AutoSize
```

### Smart Paging

Quando una VM viene riavviata e la Startup Memory è superiore alla Minimum Memory, potrebbe non esserci sufficiente RAM fisica disponibile. In questo scenario, Hyper-V utilizza lo **Smart Paging** — un file di paging temporaneo su disco che consente alla VM di avviarsi. Lo Smart Paging viene usato solo durante il boot e rilasciato non appena il balloon driver nel guest OS prende il controllo.

```powershell
# Configurare il percorso per i file di smart paging (usare SSD)
Set-VM -Name "SRV-APP01" -SmartPagingFilePath "D:\Hyper-V\SmartPaging"

# Verificare la configurazione
Get-VM -Name "SRV-APP01" | Select-Object Name, SmartPagingFilePath, SmartPagingFileInUse
```

**Best practice:** Posizionare i file di smart paging su SSD. Lo smart paging su HDD causa tempi di avvio della VM estremamente lenti (minuti anziché secondi).

### Topologia NUMA

NUMA (Non-Uniform Memory Access) è l'architettura di memoria dei server moderni multi-socket. Ogni socket CPU ha la propria "bank" di memoria locale. L'accesso alla memoria locale è veloce, l'accesso alla memoria di un altro socket (remote NUMA) è più lento (1.5-2x di latenza).

```powershell
# Visualizzare la topologia NUMA dell'host
Get-VMHostNumaNode | Select-Object NodeId, ProcessorsAvailability,
    MemoryTotal, MemoryAvailable | Format-Table -AutoSize

# Verificare l'assegnazione NUMA delle VM
Get-VM | Where-Object State -eq Running |
    Get-VMProcessor | Select-Object VMName,
        @{N='vCPUs';E={$_.Count}},
        MaximumCountPerNumaNode,
        MaximumCountPerNumaSocket | Format-Table -AutoSize

# Configurare i limiti NUMA per una VM (allineare vCPU e memoria a un nodo NUMA)
Set-VMProcessor -VMName "SRV-SQL01" `
    -MaximumCountPerNumaNode 8 `
    -MaximumCountPerNumaSocket 1

# Disabilitare NUMA spanning sull'host (raccomandato per SQL Server e workload latency-sensitive)
Set-VMHost -NumaSpanningEnabled $false

# Quando NUMA spanning è disabilitato:
# - Ogni VM è confinata a un singolo nodo NUMA
# - La latenza di memoria è prevedibile e bassa
# - La VM non può avere più vCPU o RAM di un singolo nodo NUMA
```

---

## Configurazione CPU

### Dimensionamento vCPU

Il rapporto vCPU:pCPU determina il livello di overcommit della CPU. Hyper-V non sovrascrive la CPU in modo aggressivo come VMware — ogni vCPU viene schedulata su un pCPU fisico reale tramite lo scheduler dell'hypervisor.

| Rapporto vCPU:pCPU | Scenario | Rischio |
|---------------------|---------|---------|
| 1:1 | Produzione critica, database | Nessuno |
| 2:1 | Produzione standard | Basso |
| 4:1 | Sviluppo, test | Medio |
| 8:1+ | VDI, laboratorio | Alto |

```powershell
# Calcolare il rapporto vCPU:pCPU attuale
$pCPU = (Get-CimInstance Win32_Processor | Measure-Object NumberOfLogicalProcessors -Sum).Sum
$vCPU = (Get-VM | Where-Object State -eq Running | Measure-Object ProcessorCount -Sum).Sum
$ratio = [math]::Round($vCPU / $pCPU, 1)
Write-Output "pCPU totali: $pCPU | vCPU totali: $vCPU | Rapporto: ${ratio}:1"

# Configurare il numero di processori virtuali
Set-VMProcessor -VMName "SRV-APP01" -Count 4
```

### Resource Controls (Reserve, Limit, Weight)

```powershell
# Riservare il 50% di un core fisico per la VM (garantito)
Set-VMProcessor -VMName "SRV-SQL01" -Reserve 50

# Limitare la VM all'80% della capacità CPU (tetto massimo)
Set-VMProcessor -VMName "SRV-DEV01" -Maximum 80

# Configurare il peso relativo (0-10000, default 100)
# In caso di contesa CPU, la VM con peso maggiore riceve più tempo CPU
Set-VMProcessor -VMName "SRV-SQL01" -RelativeWeight 200
Set-VMProcessor -VMName "SRV-DEV01" -RelativeWeight 50

# Configurazione tipica per un database server critico
Set-VMProcessor -VMName "SRV-SQL01" `
    -Count 8 `
    -Reserve 30 `
    -Maximum 100 `
    -RelativeWeight 200 `
    -MaximumCountPerNumaNode 8 `
    -MaximumCountPerNumaSocket 1 `
    -EnableHostResourceProtection $true
```

### CPU Compatibility Mode

Il Processor Compatibility Mode limita il set di istruzioni CPU esposto alla VM al sottoinsieme comune tra processori di generazioni diverse. È necessario per la Live Migration tra host con CPU di famiglie diverse (es. Haswell → Skylake).

```powershell
# Abilitare Processor Compatibility Mode
Set-VMProcessor -VMName "SRV-APP01" -CompatibilityForMigrationEnabled $true

# Impatto: la VM non potrà utilizzare le istruzioni più recenti del processore
# (es. AVX-512 non sarà disponibile se il processore più vecchio nel cluster non lo supporta)

# Verificare lo stato
Get-VMProcessor -VMName "SRV-APP01" | Select-Object VMName,
    CompatibilityForMigrationEnabled, Count, Reserve, Maximum, RelativeWeight
```

### Hardware Thread Count per Core

Su processori con Hyper-Threading (SMT), è possibile controllare quanti thread hardware vengono esposti per core virtuale.

```powershell
# Esporre 2 thread hardware per core (con SMT abilitato sull'host)
Set-VMProcessor -VMName "SRV-APP01" -HwThreadCountPerCore 2

# Disabilitare HT per la VM (1 thread per core, mitiga side-channel attacks)
Set-VMProcessor -VMName "SRV-SECURE01" -HwThreadCountPerCore 1
```

---

## Checkpoint: Standard e Production

I checkpoint (precedentemente noti come snapshot) catturano lo stato di una VM in un punto specifico nel tempo.

### Standard Checkpoint

Cattura lo stato della VM inclusa la memoria RAM. Quando si ripristina, la VM ritorna esattamente allo stato in cui si trovava, inclusi i processi in esecuzione. Non è application-consistent — le applicazioni (specialmente i database) potrebbero trovarsi in uno stato inconsistente.

### Production Checkpoint

Utilizza VSS (Volume Shadow Copy Service) su Windows o `fsfreeze` su Linux per creare un checkpoint application-consistent. Non cattura la memoria RAM ma garantisce che i dati su disco siano coerenti. È il tipo predefinito e raccomandato per ambienti di produzione.

```powershell
# Configurare il tipo di checkpoint (Production è il default)
Set-VM -Name "SRV-APP01" -CheckpointType Production

# Per ambienti di sviluppo/test, Standard può essere utile
Set-VM -Name "DEV-TEST01" -CheckpointType Standard

# Creare un checkpoint
Checkpoint-VM -Name "SRV-APP01" -SnapshotName "Pre-Update-$(Get-Date -Format 'yyyyMMdd')"

# Elencare i checkpoint di una VM
Get-VMCheckpoint -VMName "SRV-APP01" | Select-Object Name, CreationTime, ParentCheckpointName

# Ripristinare un checkpoint
Restore-VMCheckpoint -Name "Pre-Update-20260412" -VMName "SRV-APP01" -Confirm:$false

# Rimuovere un checkpoint (merge dei dati nel disco parent)
Remove-VMCheckpoint -VMName "SRV-APP01" -Name "Pre-Update-20260412"

# Rimuovere TUTTI i checkpoint
Get-VMCheckpoint -VMName "SRV-APP01" | Remove-VMCheckpoint
```

**Attenzione critica:** I checkpoint **non sono backup**. Non proteggono dalla perdita del disco fisico. I file di checkpoint (.avhdx) sono dischi differencing che dipendono dal disco parent: se il parent viene corrotto, anche i checkpoint sono persi. Inoltre, i checkpoint accumulati degradano le prestazioni I/O perché ogni operazione di lettura deve attraversare la catena di differencing.

---

## Live Migration

La Live Migration permette di spostare una VM in esecuzione da un host Hyper-V a un altro senza downtime percepibile dagli utenti. Il processo trasferisce la memoria, lo stato del processore e i dispositivi della VM all'host di destinazione in modo trasparente.

### Prerequisiti

- Entrambi gli host devono essere nello stesso dominio AD (o trust)
- Storage condiviso (SAN, SMB 3.0) oppure Live Migration con Storage Migration
- Stessa versione di Hyper-V (o versione superiore sulla destinazione)
- Processori compatibili (stessa famiglia o con Processor Compatibility Mode abilitato)
- Rete dedicata per la migrazione (raccomandato)
- Kerberos delegation configurata (o CredSSP per ambienti semplici)

### Configurazione

```powershell
# Abilitare Live Migration sull'host
Enable-VMMigration

# Configurare le impostazioni di migrazione
Set-VMHost -MaximumVirtualMachineMigrations 2 `
    -MaximumStorageMigrations 2 `
    -VirtualMachineMigrationAuthenticationType Kerberos `
    -UseAnyNetworkForMigration $false

# Aggiungere la rete dedicata per la migrazione
Add-VMMigrationNetwork -Subnet "10.0.100.0/24" -Priority 1

# Eseguire una Live Migration
Move-VM -Name "SRV-APP01" -DestinationHost "HVHOST02.contoso.com"

# Live Migration con storage migration (sposta VM e dischi)
Move-VM -Name "SRV-APP01" -DestinationHost "HVHOST02.contoso.com" `
    -DestinationStoragePath "D:\Hyper-V\VMs\SRV-APP01" `
    -IncludeStorage

# Storage-only migration (spostare solo i dischi, stessa VM)
Move-VMStorage -VMName "SRV-APP01" -DestinationStoragePath "E:\NewStorage\SRV-APP01"

# Abilitare Processor Compatibility Mode (per migrazione tra CPU diverse)
Set-VMProcessor -VMName "SRV-APP01" -CompatibilityForMigrationEnabled $true
```

### Fasi della Live Migration

```
Fase 1: Setup
- Verifica prerequisiti
- Creazione VM placeholder sulla destinazione

Fase 2: Transfer (Memory Pre-Copy)
- Copia delle pagine di memoria (iterazioni multiple)
- Ogni iterazione copia solo le pagine "dirty" (modificate)
- Le iterazioni continuano fino a poche pagine rimaste

Fase 3: Blackout (millisecondi)
- VM viene messa in pausa sulla sorgente
- Ultime pagine dirty + stato CPU trasferiti
- VM viene avviata sulla destinazione
- Connessioni di rete aggiornate (gratuitous ARP)

Fase 4: Cleanup
- Risorse rilasciate sulla sorgente
- VM rimossa dalla sorgente
```

---

## Live Migration — Tuning Avanzato

### Opzioni di Trasporto

Hyper-V offre tre modalità di trasporto per la Live Migration, ognuna con caratteristiche di prestazione diverse:

| Modalità | Come funziona | Quando usare |
|---------|--------------|-------------|
| **TCP** | Trasferimento via TCP standard | Reti < 10 Gbps, compatibilità massima |
| **Compression** | Compressione in-memory prima del trasferimento | Reti lente, VM con molta memoria "comprimibile" (OS idle) |
| **SMB** | Trasferimento via SMB 3.0 con RDMA (se disponibile) | Reti 10+ Gbps con NIC RDMA (RoCE/iWARP) |

```powershell
# Impostare la modalità di trasporto
Set-VMHost -VirtualMachineMigrationPerformanceOption SMB          # Raccomandato con RDMA
Set-VMHost -VirtualMachineMigrationPerformanceOption Compression  # Reti lente
Set-VMHost -VirtualMachineMigrationPerformanceOption TCPIP        # Default, compatibilità

# Aumentare il numero di migrazioni simultanee (default: 2)
Set-VMHost -MaximumVirtualMachineMigrations 4

# Verificare la configurazione corrente
Get-VMHost | Select-Object VirtualMachineMigrationEnabled,
    VirtualMachineMigrationPerformanceOption,
    VirtualMachineMigrationAuthenticationType,
    MaximumVirtualMachineMigrations,
    MaximumStorageMigrations
```

### Kerberos vs CredSSP

| Aspetto | Kerberos (Constrained Delegation) | CredSSP |
|---------|----------------------------------|---------|
| Sicurezza | Alta (nessuna credenziale trasmessa) | Media (credenziali delegate) |
| Configurazione | Complessa (AD delegation) | Semplice |
| Multi-hop | Sì | No (solo 1 hop) |
| Raccomandazione | Produzione, cluster | Lab, test |

```powershell
# Configurare Kerberos constrained delegation (dal DC, una volta per coppia di host)
# HVHOST01 deve poter delegare a HVHOST02 e viceversa
# Servizio: Microsoft Virtual System Migration Service + CIFS

# Verificare la delegation configurata
Get-ADComputer -Identity "HVHOST01" -Properties msDS-AllowedToDelegateTo |
    Select-Object -ExpandProperty msDS-AllowedToDelegateTo

# Configurare CredSSP come fallback (meno sicuro, più semplice)
Enable-WSManCredSSP -Role Client -DelegateComputer "HVHOST02.contoso.com" -Force
Enable-WSManCredSSP -Role Server -Force  # Sul server di destinazione
Set-VMHost -VirtualMachineMigrationAuthenticationType CredSSP
```

### Stima del Tempo di Migrazione

```powershell
# Stimare il tempo di migrazione basandosi sulla RAM assegnata e la bandwidth
function Get-MigrationEstimate {
    param(
        [string]$VMName,
        [int]$NetworkSpeedGbps = 10
    )
    $vm = Get-VM -Name $VMName
    $memGB = [math]::Round($vm.MemoryAssigned / 1GB, 1)
    $networkMBps = ($NetworkSpeedGbps * 1000) / 8  # Conversione in MB/s
    $overhead = 1.3  # 30% overhead per dirty pages e protocollo
    $estimateSeconds = ($memGB * 1024 / $networkMBps) * $overhead
    [PSCustomObject]@{
        VM = $VMName
        MemoryGB = $memGB
        NetworkGbps = $NetworkSpeedGbps
        EstimateSeconds = [math]::Round($estimateSeconds, 0)
        EstimateReadable = [TimeSpan]::FromSeconds($estimateSeconds).ToString("mm\:ss")
    }
}
Get-MigrationEstimate -VMName "SRV-SQL01" -NetworkSpeedGbps 10
```

---

## Failover Clustering e Hyper-V

Il Failover Clustering di Windows Server è il fondamento dell'alta disponibilità per Hyper-V in ambienti di produzione. Un cluster Hyper-V consente la migrazione automatica delle VM in caso di guasto hardware, manutenzione pianificata e bilanciamento del carico.

### Architettura del Cluster Hyper-V

```
┌──────────────────────────────────────────────────────────────┐
│                    Failover Cluster                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  HVHOST01    │  │  HVHOST02    │  │  HVHOST03    │       │
│  │              │  │              │  │              │       │
│  │ VM-SQL01     │  │ VM-WEB01     │  │ VM-APP01     │       │
│  │ VM-DC01      │  │ VM-WEB02     │  │ VM-APP02     │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│              ┌─────────────▼─────────────┐                   │
│              │  Cluster Shared Volumes    │                   │
│              │  (CSV)                     │                   │
│              │                            │                   │
│              │  C:\ClusterStorage\Vol1\   │                   │
│              │  C:\ClusterStorage\Vol2\   │                   │
│              └───────────────────────────┘                   │
│                            │                                 │
│              ┌─────────────▼─────────────┐                   │
│              │  Shared Storage            │                   │
│              │  (SAN iSCSI/FC/SMB 3.0)   │                   │
│              └───────────────────────────┘                   │
└──────────────────────────────────────────────────────────────┘
```

### Cluster Shared Volumes (CSV)

I CSV consentono a tutti i nodi del cluster di accedere simultaneamente allo stesso volume di storage. Ogni nodo vede il CSV come `C:\ClusterStorage\VolumeN\`. Un solo nodo alla volta è il "coordinator" del volume per le operazioni di metadati, ma tutti i nodi possono leggere e scrivere i file VHDX contemporaneamente tramite direct I/O.

```powershell
# Aggiungere un disco cluster come CSV
Add-ClusterSharedVolume -Name "Cluster Disk 1"

# Verificare i CSV
Get-ClusterSharedVolume | Select-Object Name, State, OwnerNode,
    @{N='FreeSpaceGB';E={[math]::Round(($_.SharedVolumeInfo.Partition.FreeSpace)/1GB, 1)}},
    @{N='SizeGB';E={[math]::Round(($_.SharedVolumeInfo.Partition.Size)/1GB, 1)}}

# Spostare la ownership del CSV su un altro nodo
Move-ClusterSharedVolume -Name "Cluster Virtual Disk (CSV-Data)" -Node "HVHOST02"
```

### Configurazione VM ad Alta Disponibilità

```powershell
# Rendere una VM altamente disponibile nel cluster
Add-ClusterVirtualMachineRole -VMName "SRV-SQL01"

# Configurare il proprietario preferito (dove la VM dovrebbe girare normalmente)
Set-ClusterOwnerNode -Resource "SRV-SQL01" -Owners "HVHOST01","HVHOST02"

# Configurare la priorità di avvio (High = parte per prima dopo un failover)
(Get-ClusterGroup "SRV-SQL01").Priority = 3000  # 0=Low, 1000=Medium, 2000=High, 3000=Highest

# Configurare il VM Monitoring (riavvia la VM se un servizio critico si ferma)
Add-ClusterVMMonitoredItem -VirtualMachine "SRV-SQL01" -Service "MSSQLSERVER"
Add-ClusterVMMonitoredItem -VirtualMachine "SRV-SQL01" -Service "SQLSERVERAGENT"

# Verificare i servizi monitorati
Get-ClusterVMMonitoredItem -VirtualMachine "SRV-SQL01"
```

### Quorum e Witness

Il quorum determina quanti nodi devono essere online perché il cluster resti operativo. Il witness (disco o cloud) fornisce un voto aggiuntivo per risolvere scenari di split-brain.

```powershell
# Configurare Cloud Witness (raccomandato per cluster moderni)
Set-ClusterQuorum -CloudWitness `
    -AccountName "clusterwitness" `
    -AccessKey "AZURE_STORAGE_KEY_HERE"

# Verificare la configurazione del quorum
Get-ClusterQuorum | Select-Object Cluster, QuorumResource, QuorumType
```

### Drain on Shutdown e Manutenzione

```powershell
# Abilitare il drain automatico delle VM prima dello shutdown del nodo
(Get-ClusterNode "HVHOST01").DrainOnShutdown = 1

# Mettere un nodo in manutenzione (drain manuale)
Suspend-ClusterNode -Name "HVHOST01" -Drain -Wait

# Verificare che tutte le VM siano state spostate
Get-ClusterGroup | Where-Object OwnerNode -eq "HVHOST01" | Select-Object Name, State

# Ripristinare il nodo dopo la manutenzione
Resume-ClusterNode -Name "HVHOST01" -Failback Immediate
```

---

## Hyper-V Replica

Hyper-V Replica è un meccanismo di replica asincrona che mantiene una copia della VM su un host secondario per scopi di disaster recovery. A differenza della Live Migration, Hyper-V Replica non richiede storage condiviso e può funzionare attraverso connessioni WAN.

```powershell
# Abilitare Hyper-V Replica sul server di destinazione (Replica Server)
Set-VMReplicationServer -ReplicationEnabled $true `
    -AllowedAuthenticationType Kerberos `
    -ReplicationAllowedFromAnyServer $false `
    -DefaultStorageLocation "D:\Hyper-V\Replicas"

# Aggiungere un server autorizzato a replicare
New-VMReplicationAuthorizationEntry -AllowedPrimaryServer "HVHOST01.contoso.com" `
    -ReplicaStorageLocation "D:\Hyper-V\Replicas" `
    -TrustGroup "Default"

# Configurare la replica su una VM specifica (dal server primario)
Enable-VMReplication -VMName "SRV-APP01" `
    -ReplicaServerName "HVHOST-DR.contoso.com" `
    -ReplicaServerPort 80 `
    -AuthenticationType Kerberos `
    -ReplicationFrequencySec 300 `
    -RecoveryHistory 12 `
    -VSSSnapshotFrequencyHour 4

# Avviare la replica iniziale
Start-VMInitialReplication -VMName "SRV-APP01" -DestinationPath "D:\InitialReplica"

# Monitorare lo stato della replica
Get-VMReplication | Select-Object VMName, State, Health, PrimaryServer,
    ReplicaServer, LastReplicationTime, ReplicationFrequencySec |
    Format-Table -AutoSize

# Failover manuale pianificato
Start-VMFailover -VMName "SRV-APP01" -Prepare  # Sul server primario
Start-VMFailover -VMName "SRV-APP01"            # Sul replica server
Complete-VMFailover -VMName "SRV-APP01"          # Conferma il failover

# Test failover (non impatta la produzione)
Start-VMFailover -VMName "SRV-APP01" -AsTest
# Dopo il test
Stop-VMFailover -VMName "SRV-APP01"
```

---

## Hyper-V Replica — Configurazione Avanzata

### Autenticazione Basata su Certificati

Per la replica attraverso WAN o reti non trusted, l'autenticazione basata su certificati (HTTPS sulla porta 443) è necessaria al posto di Kerberos.

```powershell
# Sul Replica Server: configurare HTTPS
Set-VMReplicationServer -ReplicationEnabled $true `
    -AllowedAuthenticationType Certificate `
    -CertificateThumbprint "ABC123DEF456..." `
    -DefaultStorageLocation "D:\Hyper-V\Replicas" `
    -ReplicationAllowedFromAnyServer $false

# Il certificato deve essere:
# - Emesso da una CA trusted da entrambi i server
# - Con Enhanced Key Usage: Server Authentication + Client Authentication
# - Il Subject o SAN deve corrispondere al FQDN del server

# Configurare la replica con certificato (dal server primario)
Enable-VMReplication -VMName "SRV-APP01" `
    -ReplicaServerName "hvhost-dr.contoso.com" `
    -ReplicaServerPort 443 `
    -AuthenticationType Certificate `
    -CertificateThumbprint "ABC123DEF456..." `
    -ReplicationFrequencySec 300
```

### Extended Replication (Replica a Catena)

L'Extended Replication consente di replicare una VM su un terzo sito, creando una catena di replica: Primario → Replica → Extended Replica. Utile per scenari di DR multi-sito.

```
Flusso Extended Replication:

┌──────────────┐    Replica (5 min)    ┌──────────────┐    Extended (15 min)   ┌──────────────┐
│ HVHOST-PROD  │ ──────────────────▶   │ HVHOST-DR    │ ──────────────────▶    │ HVHOST-DR2   │
│ (Sito A)     │                       │ (Sito B)     │                        │ (Sito C)     │
│              │                       │              │                        │              │
│ SRV-APP01    │                       │ SRV-APP01    │                        │ SRV-APP01    │
│ (Primary)    │                       │ (Replica)    │                        │ (Ext.Replica)│
└──────────────┘                       └──────────────┘                        └──────────────┘
```

```powershell
# Abilitare Extended Replication (dal Replica Server, verso il terzo sito)
Enable-VMReplication -VMName "SRV-APP01" `
    -ReplicaServerName "hvhost-dr2.contoso.com" `
    -ReplicaServerPort 443 `
    -AuthenticationType Certificate `
    -CertificateThumbprint "XYZ789..." `
    -ReplicationFrequencySec 900  # Extended replica: minimo 5 min (300s), max 15 min (900s)

# Verificare lo stato della catena di replica
Get-VMReplication -VMName "SRV-APP01" | Select-Object VMName,
    ReplicationMode, ReplicationState, ReplicationHealth,
    PrimaryServerName, ReplicaServerName, FrequencySec
```

### Recovery Points e RPO

```powershell
# Configurare la cronologia dei recovery points
Set-VMReplication -VMName "SRV-APP01" `
    -RecoveryHistory 24 `              # Numero di recovery points da mantenere
    -VSSSnapshotFrequencyHour 4        # Application-consistent snapshot ogni 4 ore

# Durante il failover, scegliere il recovery point
$recoveryPoints = Get-VMReplicationCheckpoint -VMName "SRV-APP01"
$recoveryPoints | Select-Object CreationTime, SnapshotType | Format-Table

# Failover a un punto specifico
Start-VMFailover -VMName "SRV-APP01" `
    -VMRecoveryCheckpoint $recoveryPoints[2]  # Terzo punto di ripristino
```

---

## Nested Virtualization

La nested virtualization permette di eseguire Hyper-V all'interno di una VM Hyper-V. Questo è utile per laboratori di formazione, ambienti CI/CD con container Windows e testing di scenari di clustering.

```powershell
# Abilitare la nested virtualization su una VM (la VM deve essere spenta)
Set-VMProcessor -VMName "LAB-HOST01" -ExposeVirtualizationExtensions $true

# Requisiti:
# - VM Generation 2
# - Almeno 4 GB di RAM (raccomandata memoria statica, non dinamica)
# - Host con Windows Server 2016+ o Windows 10 1607+
# - MAC Address Spoofing abilitato per le VM interne

# Abilitare MAC spoofing sulla NIC della VM host
Set-VMNetworkAdapter -VMName "LAB-HOST01" -MacAddressSpoofing On
```

### Docker su Hyper-V

Docker Desktop su Windows utilizza Hyper-V per eseguire il daemon Linux (tramite WSL2 o Hyper-V backend). In ambienti server, i Windows containers possono utilizzare l'isolamento Hyper-V per un isolamento più robusto rispetto all'isolamento di processo.

```powershell
# Installare Docker su Windows Server con supporto Hyper-V isolation
Install-WindowsFeature -Name Containers -Restart
# Dopo il reboot, installare Docker EE/Moby

# Eseguire un container Windows con isolamento Hyper-V
# docker run --isolation=hyperv mcr.microsoft.com/windows/servercore:ltsc2022 cmd

# Verificare l'isolamento del container
# docker inspect --format='{{.HostConfig.Isolation}}' <container-id>
```

### Scenari di Utilizzo della Nested Virtualization

| Scenario | Descrizione | RAM raccomandata |
|---------|------------|-----------------|
| Lab Hyper-V | Testare clustering, Live Migration senza hardware fisico | 32+ GB nella VM L1 |
| CI/CD | Pipeline di test che richiedono VM temporanee | 16+ GB nella VM L1 |
| Formazione | Ambienti didattici self-contained per studenti | 16+ GB nella VM L1 |
| Container Hyper-V | Windows containers con isolamento Hyper-V | 8+ GB nella VM L1 |

### Limitazioni della Nested Virtualization

- **Prestazioni:** L'hypervisor L2 subisce un overhead aggiuntivo del 10-20% rispetto alla virtualizzazione diretta.
- **Dynamic Memory:** Non supportata per la VM L1 quando le estensioni di virtualizzazione sono esposte. Usare memoria statica.
- **GPU Passthrough:** DDA (Discrete Device Assignment) non è disponibile per VM annidate.
- **Produzione:** La nested virtualization non è raccomandata per carichi di lavoro di produzione a causa dell'overhead cumulativo.

---

## Sicurezza Avanzata: Shielded VMs e Guarded Fabric

### Architettura Guarded Fabric

La Guarded Fabric è un'infrastruttura di sicurezza che garantisce che le VM Shielded possano girare solo su host attestati e autorizzati. I componenti principali sono:

```
┌──────────────────────────────────────────────────────────┐
│                Host Guardian Service (HGS)                │
│                                                          │
│  ┌────────────────────┐  ┌────────────────────────────┐  │
│  │ Attestation Service │  │ Key Protection Service     │  │
│  │                    │  │ (KPS)                      │  │
│  │ Verifica identità  │  │ Rilascia chiavi per        │  │
│  │ e integrità degli  │  │ sbloccare il vTPM          │  │
│  │ Guarded Host       │  │ della Shielded VM          │  │
│  └────────────────────┘  └────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────┘
                            │ Attestation + Key Release
                            │
┌───────────────────────────▼──────────────────────────────┐
│                    Guarded Host (Hyper-V)                  │
│                                                          │
│   ┌──────────────────────────────────────────────────┐   │
│   │              Shielded VM                          │   │
│   │                                                  │   │
│   │  ┌──────────┐  ┌──────────────────────────────┐  │   │
│   │  │  vTPM    │  │  Encrypted VHDX (BitLocker)  │  │   │
│   │  │          │  │                              │  │   │
│   │  │ Chiavi   │  │  OS + Dati cifrati           │  │   │
│   │  │ sealed   │  │  Accessibili solo con        │  │   │
│   │  │ to HGS   │  │  vTPM sbloccato              │  │   │
│   │  └──────────┘  └──────────────────────────────┘  │   │
│   │                                                  │   │
│   │  Protezioni attive:                              │   │
│   │  ✗ Console access bloccato                       │   │
│   │  ✗ PowerShell Direct bloccato                    │   │
│   │  ✗ VM export bloccato                            │   │
│   │  ✗ Live dump disabilitato                        │   │
│   │  ✗ Memoria non ispezionabile dall'host admin     │   │
│   └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Modalità di Attestation

| Modalità | Sicurezza | Requisiti | Uso raccomandato |
|---------|-----------|-----------|-----------------|
| **TPM Attestation** | Massima | TPM 2.0, UEFI Secure Boot, code integrity policy su ogni host | Produzione, compliance |
| **Host Key Attestation** | Alta | Chiave crittografica per host, nessun TPM richiesto | Produzione senza TPM |
| **Admin-trusted** (deprecato) | Media | Appartenenza a un gruppo AD | Solo lab/dev |

```powershell
# Installare HGS (su un server dedicato, non sugli host Hyper-V)
Install-WindowsFeature HostGuardianServiceRole -IncludeManagementTools -Restart

# Inizializzare HGS (TPM attestation)
Initialize-HgsServer -HgsServiceName "hgs" `
    -TrustTpm `
    -SigningCertificateThumbprint "SIGN_CERT_THUMBPRINT" `
    -EncryptionCertificateThumbprint "ENC_CERT_THUMBPRINT"

# Registrare un Guarded Host (dall'host Hyper-V)
# 1. Raccogliere l'identifier TPM
(Get-PlatformIdentifier).InternalEndorsementKey | Out-File "C:\host01-ek.txt"

# 2. Registrare sull'HGS
Add-HgsAttestationTpmHost -Name "HVHOST01" -Path "C:\host01-ek.txt"

# Verificare l'attestation dall'host
Get-HgsClientConfiguration
```

### Provisioning di una Shielded VM

```powershell
# Configurare il Key Protector per una nuova Shielded VM
$owner = New-HgsGuardian -Name "VMOwner" -GenerateCertificates
$guardian = Get-HgsGuardian -Name "UntrustedGuardian"
$kp = New-HgsKeyProtector -Owner $owner -Guardian $guardian -AllowUntrustedRoot

# Creare la VM con protezione
$vm = New-VM -Name "SHIELDED-APP01" -Generation 2 -MemoryStartupBytes 4GB
Set-VMKeyProtector -VM $vm -KeyProtector $kp.RawData
Set-VMSecurityPolicy -VM $vm -Shielded  # Attiva tutte le protezioni
Enable-VMTPM -VM $vm

# Verificare lo stato di protezione
Get-VMSecurityPolicy -VMName "SHIELDED-APP01"
Get-VMSecurity -VMName "SHIELDED-APP01" | Select-Object Shielded, TpmEnabled,
    KsdEnabled, VirtualizationBasedSecurityOptOut
```

---

## Integrazione Container

### Container Windows vs Hyper-V Isolation

Windows supporta due modalità di isolamento per i container:

| Aspetto | Process Isolation | Hyper-V Isolation |
|---------|------------------|-------------------|
| Isolamento | Namespace + job objects (condivide kernel host) | VM leggera dedicata per container |
| Overhead | Minimo (~2-5 MB per container) | Significativo (~100-200 MB per container) |
| Sicurezza | Isolamento a livello processo | Isolamento a livello hardware |
| Versione kernel | Deve corrispondere all'host | Può differire dall'host |
| Uso | Sviluppo, ambienti trusted | Multi-tenant, untrusted workload |

```
Container Isolation — Confronto:

PROCESS ISOLATION                    HYPER-V ISOLATION
┌──────────────────────┐            ┌──────────────────────┐
│    Host OS Kernel     │            │    Host OS Kernel     │
│                      │            │                      │
│  ┌────┐ ┌────┐ ┌────┐│            │  ┌──────────────────┐│
│  │ C1 │ │ C2 │ │ C3 ││            │  │  Utility VM (L)  ││
│  │    │ │    │ │    ││            │  │  ┌────┐          ││
│  │ NS │ │ NS │ │ NS ││            │  │  │ C1 │ Kernel   ││
│  └────┘ └────┘ └────┘│            │  │  └────┘ dedicato ││
│  Kernel condiviso     │            │  └──────────────────┘│
│  Stessa versione OS   │            │  ┌──────────────────┐│
└──────────────────────┘            │  │  Utility VM (L)  ││
                                    │  │  ┌────┐          ││
                                    │  │  │ C2 │ Kernel   ││
                                    │  │  └────┘ dedicato ││
                                    │  └──────────────────┘│
                                    └──────────────────────┘
```

### Configurazione Container su Windows Server

```powershell
# Installare la feature Container
Install-WindowsFeature -Name Containers -Restart

# Installare il runtime container (containerd o Docker)
# Per ambienti moderni: containerd + nerdctl
# Per compatibilità: Docker (Moby)

# Verificare che Hyper-V sia disponibile per l'isolamento
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V | Select-Object State

# Eseguire un container Windows con isolamento Hyper-V
# docker run --isolation=hyperv -it mcr.microsoft.com/windows/servercore:ltsc2022 cmd

# Eseguire un container Windows con isolamento processo (default su Server)
# docker run --isolation=process -it mcr.microsoft.com/windows/servercore:ltsc2022 cmd

# Kubernetes su Hyper-V: i nodi worker Windows usano containerd con HNS (Host Networking Service)
# per la rete container. Hyper-V isolation è supportato come RuntimeClass.
```

### Quando Usare Hyper-V Isolation

- **Multi-tenant:** Quando container di tenant diversi girano sullo stesso host
- **Versioni kernel diverse:** Container basato su Windows Server 2019 LTSC che deve girare su host Windows Server 2022
- **Compliance:** Requisiti normativi che richiedono isolamento hardware
- **Untrusted code:** Esecuzione di codice di terze parti o build CI/CD non verificate

---

## Gestione con PowerShell

```powershell
# Inventario completo delle VM
Get-VM | Select-Object Name, State, CPUUsage, MemoryAssigned,
    @{N='UptimeHours';E={$_.Uptime.TotalHours}},
    @{N='DiskGB';E={(Get-VHD -VMId $_.VMId | Measure-Object FileSize -Sum).Sum / 1GB}},
    Status | Format-Table -AutoSize

# Snapshot dello stato di tutte le VM per report
$vmReport = Get-VM | ForEach-Object {
    $vm = $_
    $vhds = Get-VHD -VMId $vm.VMId -ErrorAction SilentlyContinue

    [PSCustomObject]@{
        Name          = $vm.Name
        State         = $vm.State
        Generation    = $vm.Generation
        vCPUs         = $vm.ProcessorCount
        MemoryMB      = [math]::Round($vm.MemoryAssigned / 1MB)
        DynamicMemory = $vm.DynamicMemoryEnabled
        Uptime        = $vm.Uptime.ToString("dd\.hh\:mm")
        Checkpoints   = (Get-VMCheckpoint -VMName $vm.Name).Count
        DiskCount     = $vhds.Count
        DiskSizeGB    = [math]::Round(($vhds | Measure-Object Size -Sum).Sum / 1GB, 1)
        DiskUsedGB    = [math]::Round(($vhds | Measure-Object FileSize -Sum).Sum / 1GB, 1)
        ReplicaState  = $vm.ReplicationState
    }
}

$vmReport | Export-Csv "C:\Reports\VM-Inventory.csv" -NoTypeInformation

# Operazioni bulk
# Spegnere tutte le VM con graceful shutdown
Get-VM | Where-Object State -eq "Running" | Stop-VM -Force:$false

# Avviare tutte le VM con start automatico configurato
Get-VM | Where-Object AutomaticStartAction -ne "Nothing" | Start-VM

# Esportare una VM (per backup o migrazione offline)
Export-VM -Name "SRV-APP01" -Path "D:\Exports"

# Importare una VM
$importPath = "D:\Exports\SRV-APP01\Virtual Machines\*.vmcx"
Import-VM -Path (Get-ChildItem $importPath).FullName -Copy -GenerateNewId
```

---

## Automazione e Provisioning con PowerShell

### Script di Provisioning Multi-VM

```powershell
function New-HyperVServer {
    <#
    .SYNOPSIS
        Provisioning automatizzato di VM Hyper-V da template.
    .DESCRIPTION
        Crea una nuova VM Generation 2 a partire da un disco VHDX template,
        configurando CPU, memoria, rete, TPM e note.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$VMName,

        [ValidateRange(1, 64)]
        [int]$ProcessorCount = 4,

        [long]$MemoryStartup = 4GB,
        [long]$MemoryMinimum = 2GB,
        [long]$MemoryMaximum = 8GB,

        [string]$SwitchName = "vSwitch-Prod",
        [int]$VlanId = 0,

        [string]$TemplatePath = "D:\Templates\WS2022-Template.vhdx",
        [long]$OSDiskSize = 80GB,
        [long]$DataDiskSize = 0,

        [string]$VMPath = "D:\Hyper-V\VMs",
        [string]$VHDPath = "D:\Hyper-V\VHDs",

        [string]$Notes = ""
    )

    # Validazione
    if (-not (Test-Path $TemplatePath)) {
        throw "Template non trovato: $TemplatePath"
    }
    if (Get-VM -Name $VMName -ErrorAction SilentlyContinue) {
        throw "VM '$VMName' esiste già"
    }

    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] Provisioning di $VMName..."

    # Creare il disco OS dal template (differencing per risparmio spazio)
    $osDisk = Join-Path $VHDPath "$VMName-OS.vhdx"
    New-VHD -Path $osDisk -ParentPath $TemplatePath -Differencing | Out-Null
    Write-Output "  Disco OS creato: $osDisk"

    # Creare la VM
    $vm = New-VM -Name $VMName -Generation 2 -MemoryStartupBytes $MemoryStartup `
        -SwitchName $SwitchName -VHDPath $osDisk -Path $VMPath

    # Configurare CPU e memoria
    Set-VM -VM $vm -ProcessorCount $ProcessorCount -DynamicMemory `
        -MemoryMinimumBytes $MemoryMinimum -MemoryMaximumBytes $MemoryMaximum `
        -AutomaticStartAction StartIfRunning `
        -AutomaticStopAction ShutDown `
        -Notes $Notes

    # Configurare VLAN se specificata
    if ($VlanId -gt 0) {
        Set-VMNetworkAdapterVlan -VM $vm -Access -VlanId $VlanId
    }

    # Abilitare vTPM
    Set-VMKeyProtector -VM $vm -NewLocalKeyProtector
    Enable-VMTPM -VM $vm

    # Configurare Secure Boot
    Set-VMFirmware -VM $vm -SecureBootTemplate MicrosoftWindows

    # Aggiungere disco dati se richiesto
    if ($DataDiskSize -gt 0) {
        $dataDisk = Join-Path $VHDPath "$VMName-Data.vhdx"
        New-VHD -Path $dataDisk -SizeBytes $DataDiskSize -Dynamic | Out-Null
        Add-VMHardDiskDrive -VM $vm -Path $dataDisk -ControllerType SCSI
        Write-Output "  Disco dati creato: $dataDisk ($([math]::Round($DataDiskSize/1GB))GB)"
    }

    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] $VMName pronto. Avviare con Start-VM."
    return $vm
}

# Esempio: provisioning di un batch di server
$servers = @(
    @{ VMName="SRV-WEB01"; ProcessorCount=2; MemoryMaximum=4GB; VlanId=100; Notes="Web frontend" }
    @{ VMName="SRV-WEB02"; ProcessorCount=2; MemoryMaximum=4GB; VlanId=100; Notes="Web frontend" }
    @{ VMName="SRV-APP01"; ProcessorCount=4; MemoryMaximum=16GB; VlanId=200; Notes="App server" }
    @{ VMName="SRV-SQL01"; ProcessorCount=8; MemoryMaximum=32GB; VlanId=300; DataDiskSize=500GB; Notes="Database" }
)

foreach ($s in $servers) {
    New-HyperVServer @s
}
```

### Report Periodico Automatizzato

```powershell
function Send-HyperVReport {
    <#
    .SYNOPSIS
        Genera e invia via email un report HTML dello stato delle VM.
    #>
    [CmdletBinding()]
    param(
        [string]$SmtpServer = "smtp.contoso.com",
        [string]$To = "infra-team@contoso.com",
        [string]$From = "hyperv-report@contoso.com"
    )

    $hostInfo = Get-VMHost
    $vms = Get-VM | ForEach-Object {
        $vm = $_
        [PSCustomObject]@{
            Nome           = $vm.Name
            Stato          = $vm.State
            vCPU           = $vm.ProcessorCount
            'CPU %'        = $vm.CPUUsage
            'RAM (MB)'     = [math]::Round($vm.MemoryAssigned / 1MB)
            'Uptime'       = $vm.Uptime.ToString("dd\.hh\:mm")
            Checkpoints    = (Get-VMCheckpoint -VMName $vm.Name -ErrorAction SilentlyContinue).Count
            Replica        = $vm.ReplicationState
        }
    }

    $htmlBody = $vms | ConvertTo-Html -Title "Report Hyper-V - $(Get-Date -Format 'yyyy-MM-dd')" `
        -PreContent "<h2>Host: $($hostInfo.ComputerName)</h2>" | Out-String

    Send-MailMessage -To $To -From $From -Subject "Hyper-V Report $(Get-Date -Format 'yyyy-MM-dd')" `
        -Body $htmlBody -BodyAsHtml -SmtpServer $SmtpServer
}

# Registrare come scheduled task per esecuzione quotidiana
# $action = New-ScheduledTaskAction -Execute "powershell.exe" `
#     -Argument "-NoProfile -File C:\Scripts\Send-HyperVReport.ps1"
# $trigger = New-ScheduledTaskTrigger -Daily -At "07:00"
# Register-ScheduledTask -Action $action -Trigger $trigger `
#     -TaskName "HyperV-DailyReport" -User "SYSTEM"
```

---

## Monitoraggio Prestazioni

```powershell
# Contatori Hyper-V in Performance Monitor
$counters = @(
    "\Hyper-V Hypervisor Logical Processor(_Total)\% Total Run Time"
    "\Hyper-V Hypervisor Virtual Processor(_Total)\% Total Run Time"
    "\Hyper-V Dynamic Memory Balancer(*)\Available Memory"
    "\Hyper-V Virtual Switch(*)\Bytes/sec"
    "\Hyper-V Virtual Storage Device(*)\Read Bytes/sec"
    "\Hyper-V Virtual Storage Device(*)\Write Bytes/sec"
)

Get-Counter -Counter $counters -SampleInterval 5 -MaxSamples 10

# Monitoraggio CPU per VM
Get-VM | Where-Object State -eq "Running" | ForEach-Object {
    $vm = $_
    $cpuUsage = (Get-Counter "\Hyper-V Hypervisor Virtual Processor($($vm.Name):Hv VP *)\% Total Run Time" -ErrorAction SilentlyContinue).CounterSamples |
        Measure-Object CookedValue -Average

    [PSCustomObject]@{
        VM         = $vm.Name
        vCPUs      = $vm.ProcessorCount
        AvgCPU     = [math]::Round($cpuUsage.Average, 1)
        MemoryMB   = [math]::Round($vm.MemoryAssigned / 1MB)
    }
} | Sort-Object AvgCPU -Descending | Format-Table -AutoSize

# Monitoraggio memoria con Dynamic Memory
Get-VM | Where-Object {$_.State -eq "Running" -and $_.DynamicMemoryEnabled} |
    Select-Object Name,
        @{N='AssignedMB';E={[math]::Round($_.MemoryAssigned/1MB)}},
        @{N='DemandMB';E={[math]::Round($_.MemoryDemand/1MB)}},
        @{N='MinMB';E={[math]::Round($_.MemoryMinimum/1MB)}},
        @{N='MaxMB';E={[math]::Round($_.MemoryMaximum/1MB)}},
        MemoryStatus |
    Format-Table -AutoSize
```

---

## Monitoraggio Avanzato e Health Check

### Event Log Channels per Hyper-V

Hyper-V scrive eventi in diversi canali del Windows Event Log. Conoscere i canali giusti è essenziale per il troubleshooting.

| Canale Event Log | Contiene |
|-----------------|---------|
| `Microsoft-Windows-Hyper-V-VMMS-Admin` | Errori del servizio di gestione VM (vmms.exe) |
| `Microsoft-Windows-Hyper-V-Worker-Admin` | Errori dei processi worker delle VM |
| `Microsoft-Windows-Hyper-V-VMSP-Admin` | Errori del Virtual Machine Storage Plugin |
| `Microsoft-Windows-Hyper-V-VmSwitch-Operational` | Eventi del virtual switch |
| `Microsoft-Windows-Hyper-V-Config-Admin` | Modifiche alla configurazione delle VM |
| `Microsoft-Windows-Hyper-V-SynthNic-Admin` | Errori della NIC sintetica |
| `Microsoft-Windows-Hyper-V-StorageVSP-Admin` | Errori dello storage VSP |

```powershell
# Query degli errori recenti dai canali Hyper-V
$channels = @(
    "Microsoft-Windows-Hyper-V-VMMS-Admin",
    "Microsoft-Windows-Hyper-V-Worker-Admin",
    "Microsoft-Windows-Hyper-V-Config-Admin"
)

foreach ($channel in $channels) {
    $events = Get-WinEvent -LogName $channel -MaxEvents 10 -ErrorAction SilentlyContinue |
        Where-Object Level -le 3  # Warning (3) ed Error (2) e Critical (1)
    if ($events) {
        Write-Output "`n=== $channel ==="
        $events | Select-Object TimeCreated, LevelDisplayName, Id, Message |
            Format-Table -Wrap
    }
}
```

### Data Collector Set per Performance Monitor

```powershell
# Creare un Data Collector Set dedicato a Hyper-V
$counterList = @(
    "\Hyper-V Hypervisor Logical Processor(_Total)\% Total Run Time"
    "\Hyper-V Hypervisor Virtual Processor(*)\% Total Run Time"
    "\Hyper-V Dynamic Memory Balancer(*)\Available Memory"
    "\Hyper-V Dynamic Memory Balancer(*)\Average Pressure"
    "\Hyper-V Virtual Switch(*)\Bytes/sec"
    "\Hyper-V Virtual Switch(*)\Dropped Packets Outgoing/sec"
    "\Hyper-V Virtual Storage Device(*)\Read Bytes/sec"
    "\Hyper-V Virtual Storage Device(*)\Write Bytes/sec"
    "\Hyper-V Virtual Storage Device(*)\Latency"
    "\Hyper-V Hypervisor Root Virtual Processor(_Total)\% Total Run Time"
)

# Creare il Data Collector Set via logman
$counterFile = "C:\PerfLogs\hyperv-counters.txt"
$counterList | Out-File $counterFile -Encoding ASCII
# logman create counter "Hyper-V Monitoring" -cf $counterFile -si 30 -o "C:\PerfLogs\HV" -f bincirc -max 512
```

### Script di Health Check Completo

```powershell
function Test-HyperVHealth {
    <#
    .SYNOPSIS
        Verifica lo stato di salute dell'host Hyper-V e delle VM.
    #>
    [CmdletBinding()]
    param()

    $results = @()

    # 1. Stato dell'host
    $hostInfo = Get-VMHost
    $cpuCount = (Get-CimInstance Win32_Processor | Measure-Object NumberOfLogicalProcessors -Sum).Sum
    $totalRAM = [math]::Round((Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize / 1MB, 1)
    $freeRAM = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)

    $results += [PSCustomObject]@{
        Check  = "Host CPU"
        Status = if ($cpuCount -ge 4) { "OK" } else { "WARNING" }
        Detail = "$cpuCount logical processors"
    }
    $results += [PSCustomObject]@{
        Check  = "Host RAM"
        Status = if (($freeRAM / $totalRAM) -gt 0.1) { "OK" } else { "CRITICAL" }
        Detail = "Totale: ${totalRAM}GB, Libera: ${freeRAM}GB ($([math]::Round($freeRAM/$totalRAM*100))%)"
    }

    # 2. Servizi Hyper-V
    $services = @("vmms", "vmcompute")
    foreach ($svc in $services) {
        $service = Get-Service -Name $svc -ErrorAction SilentlyContinue
        $results += [PSCustomObject]@{
            Check  = "Servizio $svc"
            Status = if ($service.Status -eq "Running") { "OK" } else { "CRITICAL" }
            Detail = $service.Status
        }
    }

    # 3. VM con problemi
    $problemVMs = Get-VM | Where-Object { $_.Status -ne "Operating normally" -and $_.State -eq "Running" }
    $results += [PSCustomObject]@{
        Check  = "VM con anomalie"
        Status = if ($problemVMs.Count -eq 0) { "OK" } else { "WARNING" }
        Detail = if ($problemVMs) { ($problemVMs.Name -join ", ") } else { "Nessuna" }
    }

    # 4. Checkpoint vecchi (>48h)
    $oldCheckpoints = Get-VM | Get-VMCheckpoint -ErrorAction SilentlyContinue |
        Where-Object { $_.CreationTime -lt (Get-Date).AddHours(-48) }
    $results += [PSCustomObject]@{
        Check  = "Checkpoint >48h"
        Status = if ($oldCheckpoints.Count -eq 0) { "OK" } else { "WARNING" }
        Detail = if ($oldCheckpoints) { "$($oldCheckpoints.Count) checkpoint obsoleti" } else { "Nessuno" }
    }

    # 5. Rapporto vCPU:pCPU
    $totalvCPU = (Get-VM | Where-Object State -eq Running | Measure-Object ProcessorCount -Sum).Sum
    $ratio = if ($cpuCount -gt 0) { [math]::Round($totalvCPU / $cpuCount, 1) } else { 0 }
    $results += [PSCustomObject]@{
        Check  = "Rapporto vCPU:pCPU"
        Status = if ($ratio -le 4) { "OK" } elseif ($ratio -le 8) { "WARNING" } else { "CRITICAL" }
        Detail = "${ratio}:1 ($totalvCPU vCPU / $cpuCount pCPU)"
    }

    # 6. Replica Health
    $unhealthyReplica = Get-VMReplication -ErrorAction SilentlyContinue |
        Where-Object Health -ne "Normal"
    $results += [PSCustomObject]@{
        Check  = "Replica Health"
        Status = if (-not $unhealthyReplica) { "OK" } else { "WARNING" }
        Detail = if ($unhealthyReplica) { ($unhealthyReplica | ForEach-Object { "$($_.VMName): $($_.Health)" }) -join ", " } else { "Tutte normali" }
    }

    # Output
    $results | Format-Table -AutoSize
    $criticals = ($results | Where-Object Status -eq "CRITICAL").Count
    if ($criticals -gt 0) {
        Write-Warning "$criticals check CRITICAL trovati — intervento immediato richiesto"
    }
}

Test-HyperVHealth
```

---

## Disaster Recovery con Hyper-V

### Strategia di Backup per VM

Il backup delle macchine virtuali Hyper-V è un aspetto critico della pianificazione del disaster recovery. Hyper-V si integra con il Volume Shadow Copy Service (VSS) per consentire backup application-consistent delle VM in esecuzione, senza necessità di spegnimento.

```powershell
# Verificare lo stato degli Integration Services per il backup
Get-VMIntegrationService -VMName "SRV-APP01" | Where-Object Name -eq "VSS" |
    Select-Object Name, Enabled, PrimaryStatusDescription

# Abilitare il servizio VSS Integration se disabilitato
Enable-VMIntegrationService -VMName "SRV-APP01" -Name "VSS"

# Esportare una VM (backup completo con stato)
$backupPath = "D:\Backups\$(Get-Date -Format 'yyyy-MM-dd')"
New-Item -Path $backupPath -ItemType Directory -Force
Export-VM -Name "SRV-APP01" -Path $backupPath

# Esportare tutte le VM in esecuzione
Get-VM | Where-Object State -eq "Running" | ForEach-Object {
    $vmBackupPath = Join-Path $backupPath $_.Name
    Write-Output "Esportazione di $($_.Name)..."
    Export-VM -Name $_.Name -Path $vmBackupPath
    Write-Output "Completata: $($_.Name)"
}

# Script di backup automatizzato con retention
function Invoke-VMBackup {
    [CmdletBinding()]
    param(
        [string[]]$VMNames,
        [string]$BackupRoot = "D:\Backups",
        [int]$RetentionDays = 14
    )

    $today = Get-Date -Format "yyyy-MM-dd"
    $backupPath = Join-Path $BackupRoot $today

    # Creare la cartella di backup
    New-Item -Path $backupPath -ItemType Directory -Force | Out-Null

    foreach ($vmName in $VMNames) {
        $vm = Get-VM -Name $vmName -ErrorAction SilentlyContinue
        if (-not $vm) {
            Write-Warning "VM $vmName non trovata, skip"
            continue
        }

        Write-Output "[$(Get-Date -Format 'HH:mm:ss')] Inizio backup: $vmName"
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

        try {
            # Production checkpoint prima dell'export per consistenza
            $checkpoint = Checkpoint-VM -Name $vmName `
                -SnapshotName "Backup-$today" -Passthru
            Export-VM -Name $vmName -Path $backupPath
            Remove-VMCheckpoint -VMCheckpoint $checkpoint
            $stopwatch.Stop()
            Write-Output "[$(Get-Date -Format 'HH:mm:ss')] Backup completato: $vmName ($([math]::Round($stopwatch.Elapsed.TotalMinutes, 1)) min)"
        }
        catch {
            Write-Error "Errore nel backup di $vmName : $_"
        }
    }

    # Cleanup: rimuovere backup più vecchi della retention
    Get-ChildItem $BackupRoot -Directory |
        Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-$RetentionDays) } |
        ForEach-Object {
            Write-Output "Rimozione backup obsoleto: $($_.Name)"
            Remove-Item $_.FullName -Recurse -Force
        }
}

# Eseguire il backup
Invoke-VMBackup -VMNames @("SRV-DC01", "SRV-APP01", "SRV-SQL01") -RetentionDays 7
```

### Confronto Soluzioni di Backup

| Soluzione | Tipo | Granularità | VSS Integration | Costo |
|-----------|------|------------|----------------|-------|
| **Windows Server Backup** | Nativo | VM-level, volume-level | Sì | Gratuito (incluso) |
| **Export-VM** | Nativo | VM-level | No (full state) | Gratuito |
| **DPM / MABS** | Microsoft | Item-level (file, SQL, Exchange) | Sì | Licenza SC |
| **Veeam B&R** | Third-party | Item-level, instant recovery | Sì | Licenza Veeam |
| **Altaro** | Third-party | VM-level, CDP, offsite | Sì | Licenza Altaro |

**Production Checkpoints vs Standard Checkpoints per il backup:**

I Production Checkpoints utilizzano il VSS writer nel guest per creare un punto di coerenza applicativa. Il flusso è: trigger VSS → writers applicativi (SQL, Exchange, AD) eseguono flush/freeze → snapshot del disco → writers eseguono thaw. Il risultato è un backup da cui le applicazioni possono ripartire senza recovery.

I Standard Checkpoints salvano anche lo stato della RAM, ma il risultato è uno stato "frozen in time" — utile per il debug ma non per il ripristino applicativo, perché le applicazioni non hanno avuto modo di completare le transazioni in-flight.

### Shielded VMs

Le Shielded VMs forniscono protezione crittografica per le macchine virtuali, impedendo l'accesso non autorizzato ai dati e allo stato della VM anche da parte degli amministratori dell'host Hyper-V. Sono progettate per ambienti multi-tenant e scenari ad alta sicurezza dove l'host potrebbe essere compromesso.

```
Architettura Shielded VM:
┌─────────────────────────────────────┐
│   Host Guardian Service (HGS)        │
│   - Attestation Service              │
│   - Key Protection Service           │
└──────────────────┬──────────────────┘
                   │
            Attestation
                   │
┌──────────────────┴──────────────────┐
│   Guarded Host (Hyper-V)             │
│                                      │
│   ┌──────────────────────────────┐   │
│   │ Shielded VM                   │   │
│   │ - vTPM (Virtual TPM)          │   │
│   │ - BitLocker encryption        │   │
│   │ - Secure Boot enforced        │   │
│   │ - Console access blocked      │   │
│   │ - Live Dump disabled          │   │
│   └──────────────────────────────┘   │
└──────────────────────────────────────┘

Protezioni fornite:
- I dischi VHDX sono cifrati con BitLocker (vTPM)
- L'accesso alla console della VM è bloccato
- Il fabric admin non può leggere la memoria della VM
- La VM può girare solo su host attestati
- L'export della VM è bloccato
```

### Resource Metering

Il Resource Metering permette di tracciare il consumo di risorse delle VM per scopi di chargeback e capacity planning.

```powershell
# Abilitare il resource metering su una VM
Enable-VMResourceMetering -VMName "SRV-APP01"

# Abilitare su tutte le VM
Get-VM | Enable-VMResourceMetering

# Raccogliere le metriche
$metrics = Measure-VM -Name "SRV-APP01"
$metrics | Select-Object VMName,
    @{N='AvgCPU_MHz';E={$_.AvgCPU}},
    @{N='AvgMemory_MB';E={$_.AvgRAM}},
    @{N='MaxMemory_MB';E={$_.MaxRAM}},
    @{N='DiskAlloc_GB';E={[math]::Round($_.TotalDisk / 1GB, 2)}},
    @{N='NetInbound_GB';E={[math]::Round($_.NetworkMeteredTrafficReport.InboundTraffic / 1GB, 2)}},
    @{N='NetOutbound_GB';E={[math]::Round($_.NetworkMeteredTrafficReport.OutboundTraffic / 1GB, 2)}}

# Report per tutte le VM
Get-VM | Where-Object ResourceMeteringEnabled | Measure-VM |
    Select-Object VMName, AvgCPU, AvgRAM, MaxRAM, TotalDisk |
    Sort-Object AvgCPU -Descending | Format-Table -AutoSize

# Resettare i contatori
Reset-VMResourceMetering -VMName "SRV-APP01"
```

---

## Confronto con VMware e Proxmox

| Aspetto | Hyper-V | VMware vSphere | Proxmox VE |
|---------|---------|----------------|------------|
| **Licenza** | Incluso in Windows Server; Hyper-V Server gratuito (EOL) | ESXi gratuito (limitato); vSphere con licenza | Open source (GPL); supporto a pagamento |
| **Hypervisor** | Tipo 1 (microkernel) | Tipo 1 (monolitico ESXi) | Tipo 1 (KVM + QEMU) |
| **Gestione** | Hyper-V Manager, SCVMM, WAC | vCenter Server | Web UI integrata |
| **Container** | Windows Containers, WSL2 | vSphere with Tanzu | LXC + Docker nativo |
| **Max VM per host** | 1024 | 1024 | Limite pratico |
| **Max RAM per host** | 24 TB | 24 TB | Limite hardware |
| **Max vCPU per VM** | 240 (Gen2) | 768 | 288+ |
| **Storage** | VHDX, SMB 3.0, iSCSI, FC | VMFS, vSAN, NFS | ZFS, Ceph, LVM, NFS, iSCSI |
| **HA/Clustering** | WSFC + CSV | vSphere HA + DRS | HA Cluster integrato |
| **Replica DR** | Hyper-V Replica integrata | vSphere Replication (add-on) | Replica integrata |
| **Backup nativo** | Limitato (VSS integration) | Non incluso (Veeam/Nakivo) | vzdump + PBS |
| **GPU Passthrough** | DDA (Discrete Device Assignment) | vGPU (NVIDIA GRID) | GPU Passthrough, vGPU |
| **Costo TCO** | Medio (licenza Windows Server) | Alto (licenze vSphere) | Basso (open source) |
| **Curva apprendimento** | Media (familiarità Windows) | Alta (ecosistema complesso) | Media (Linux knowledge) |
| **Integrazione cloud** | Nativa con Azure | VMware Cloud on AWS | Non nativa |

**Quando scegliere Hyper-V:** Infrastrutture prevalentemente Windows, integrazione con Azure, budget limitato per le licenze hypervisor (incluso in Windows Server), team con competenze Windows.

**Quando scegliere VMware:** Ambienti enterprise eterogenei, requisiti di funzionalità avanzate (DRS, vSAN), team con competenze VMware, ecosistema di third-party tools maturo.

**Quando scegliere Proxmox:** Budget molto limitato, team con competenze Linux, necessità di container LXC nativi, storage ZFS/Ceph, ambienti di laboratorio e formazione.

---

## Best Practices

**Separare le reti:** Utilizzare NIC e virtual switch dedicati per traffico di management, traffico delle VM, Live Migration e cluster heartbeat. Non mescolare traffico di produzione con traffico di gestione.

**Usare Generation 2 per VM nuove:** A meno che non sia necessario supportare sistemi operativi legacy, creare sempre VM di Generation 2 per beneficiare di UEFI, Secure Boot e prestazioni migliori.

**Preferire dischi fissi per produzione:** I dischi dinamici sono convenienti per il risparmio di spazio ma hanno overhead di prestazioni a causa della necessità di allocare spazio durante la scrittura. Per VM di produzione con I/O intensivo, usare dischi fissi.

**Limitare i checkpoint:** I checkpoint non sono backup. Non lasciare checkpoint attivi per più di 24-48 ore in produzione: la catena di differencing degrada le prestazioni e complica il merge. Usare Production Checkpoints e rimuoverli dopo la validazione delle modifiche.

**Dimensionare la memoria con Dynamic Memory:** Abilitare Dynamic Memory per la maggior parte delle VM, configurando Startup Memory, Minimum Memory e Maximum Memory in modo appropriato. Riservare memoria statica solo per workload con requisiti specifici (SQL Server, Exchange).

**Aggiornare gli Integration Services:** Assicurarsi che tutti i guest OS abbiano Integration Services aggiornati per garantire prestazioni ottimali e compatibilità con le funzionalità dell'host.

**Pianificare la capacità:** Monitorare regolarmente l'utilizzo di CPU, memoria, storage e rete del host per evitare l'overcommit. Un rapporto vCPU:pCPU superiore a 4:1 richiede attenzione, e superiore a 8:1 è un rischio per la maggior parte dei workload.

---

## Troubleshooting

### Problema: VM Non Si Avvia — "The virtual machine could not be started"

**Sintomi**: La VM resta nello stato "Off" dopo il tentativo di avvio. L'evento log mostra errori relativi a risorse o configurazione.

**Causa**: Le cause più comuni includono: memoria insufficiente sul host, disco VHDX mancante o corrotto, virtual switch eliminato o rinominato, conflitto di porta su serial/COM, o configurazione Secure Boot incompatibile.

**Soluzione**:

```powershell
# Verificare la memoria disponibile sul host
Get-VMHostNumaNode | Select-Object NodeId, MemoryTotal, MemoryAvailable

# Verificare che i dischi esistano
Get-VMHardDiskDrive -VMName "SRV-APP01" | ForEach-Object {
    [PSCustomObject]@{
        Path   = $_.Path
        Exists = Test-Path $_.Path
    }
}

# Verificare che il virtual switch esista
(Get-VMNetworkAdapter -VMName "SRV-APP01").SwitchName |
    ForEach-Object { Get-VMSwitch -Name $_ -ErrorAction SilentlyContinue }

# Disabilitare temporaneamente Secure Boot per diagnostica
Set-VMFirmware -VMName "SRV-APP01" -EnableSecureBoot Off
```

### Problema: Prestazioni I/O Scadenti nella VM

**Sintomi**: Le operazioni su disco nella VM sono significativamente più lente del previsto. Le applicazioni mostrano latenza elevata.

**Causa**: Disco dinamico frammentato, catena di checkpoint profonda, controller IDE (Gen1) invece di SCSI, antivirus sul host che scansiona i file VHDX, storage fisico sottodimensionato.

**Soluzione**:

```powershell
# Verificare il tipo di disco e la profondità della catena
Get-VHD -VMId (Get-VM "SRV-APP01").VMId | Select-Object VhdType, ParentPath, FragmentationPercentage

# Verificare se ci sono checkpoint
Get-VMCheckpoint -VMName "SRV-APP01" | Measure-Object

# Ottimizzare il disco
Stop-VM -Name "SRV-APP01"
Optimize-VHD -Path "D:\VHDs\SRV-APP01-OS.vhdx" -Mode Full

# Convertire da dinamico a fisso per prestazioni migliori
Convert-VHD -Path "D:\VHDs\old-dynamic.vhdx" -DestinationPath "D:\VHDs\new-fixed.vhdx" -VHDType Fixed

# Escludere la cartella VHD dall'antivirus (Windows Defender)
Add-MpPreference -ExclusionPath "D:\Hyper-V\VHDs"
Add-MpPreference -ExclusionExtension "vhdx","avhdx","vhd","vsv","bin","vmgs","vmrs"
```

### Problema: Live Migration Fallisce

**Sintomi**: La Live Migration si avvia ma fallisce durante il trasferimento, restituendo errori di autenticazione o compatibilità.

**Causa**: Kerberos delegation non configurata correttamente, processori incompatibili tra gli host, rete di migrazione non raggiungibile, o CredSSP richiesto ma non abilitato.

**Soluzione**:

```powershell
# Verificare la configurazione di migrazione su entrambi gli host
Get-VMHost | Select-Object VirtualMachineMigrationEnabled,
    VirtualMachineMigrationAuthenticationType,
    MaximumVirtualMachineMigrations

# Verificare la compatibilità processore
Compare-VM -Name "SRV-APP01" -DestinationHost "HVHOST02" | Select-Object -ExpandProperty Incompatibilities

# Abilitare Processor Compatibility Mode
Set-VMProcessor -VMName "SRV-APP01" -CompatibilityForMigrationEnabled $true

# Configurare Kerberos constrained delegation (su DC, per ogni host)
# L'account computer HVHOST01$ deve poter delegare a HVHOST02$ per il servizio Microsoft Virtual System Migration Service
```

### Problema: BSOD nella VM (Blue Screen)

**Sintomi**: La VM va in crash con un BSOD. Il guest OS mostra un bug check code. La VM si riavvia automaticamente o resta in stato "Saved".

**Causa**: Driver incompatibili nel guest, Integration Services obsoleti, memoria insufficiente (OOM killer), corruzione del filesystem guest.

**Soluzione**:

```powershell
# Configurare il dump automatico della memoria guest per analisi
# (Dentro la VM: System Properties → Startup and Recovery → Write debugging information)

# Verificare la versione degli Integration Services
Get-VM | Select-Object Name, IntegrationServicesVersion, IntegrationServicesState

# Se la VM è in stato Saved dopo il crash, forzare lo spegnimento
Stop-VM -Name "SRV-APP01" -TurnOff

# Verificare l'Event Viewer dell'host per errori correlati
Get-WinEvent -LogName "Microsoft-Windows-Hyper-V-Worker-Admin" -MaxEvents 20 |
    Where-Object { $_.Message -like "*SRV-APP01*" } |
    Select-Object TimeCreated, LevelDisplayName, Message | Format-Table -Wrap
```

### Problema: Integration Services Non Funzionano

**Sintomi**: Time sync non funziona, heartbeat mancante, shutdown integrato non disponibile, backup VSS fallisce.

**Causa**: Integration Services disabilitati, versione incompatibile, driver sintetici non installati nel guest (guest OS molto vecchio o Linux senza `hv_*` kernel modules).

**Soluzione**:

```powershell
# Verificare lo stato di tutti gli Integration Services
Get-VMIntegrationService -VMName "SRV-APP01" |
    Select-Object Name, Enabled, PrimaryStatusDescription | Format-Table

# Abilitare tutti gli Integration Services
Get-VMIntegrationService -VMName "SRV-APP01" |
    Where-Object Enabled -eq $false |
    Enable-VMIntegrationService

# Per Linux: verificare che i moduli kernel siano caricati
# lsmod | grep hv_
# Moduli necessari: hv_vmbus, hv_storvsc, hv_netvsc, hv_utils, hv_balloon
```

### Problema: VLAN Non Funziona — VM Non Ha Connettività

**Sintomi**: La VM è connessa al virtual switch ma non riesce a comunicare con la rete. DHCP non assegna un IP, il ping verso il gateway fallisce.

**Causa**: VLAN ID errato sulla VM, VLAN ID non configurato sulla porta trunk dello switch fisico, Native VLAN mismatch, VLAN non propagata su tutti gli switch.

**Soluzione**:

```powershell
# Verificare la configurazione VLAN della VM
Get-VMNetworkAdapterVlan -VMName "SRV-APP01"

# Verificare la configurazione VLAN del virtual switch (management OS)
Get-VMNetworkAdapterVlan -ManagementOS

# Rimuovere e riconfigurare la VLAN
Set-VMNetworkAdapterVlan -VMName "SRV-APP01" -Untagged
Set-VMNetworkAdapterVlan -VMName "SRV-APP01" -Access -VlanId 100

# Testare la connettività dalla VM
# Test-Connection -ComputerName 10.100.0.1 -Count 3  (dal guest)

# Verificare sullo switch fisico che la VLAN sia allowed sul trunk
# (operazione sulla CLI dello switch — fuori dall'ambito PowerShell)
```

### Problema: Hyper-V Replica Health Warning

**Sintomi**: La replica mostra stato "Warning" o "Critical". La replica non è aggiornata, il delta di replica supera la soglia.

**Causa**: Rete tra i server sovraccarica o instabile, disco lento sul replica server, frequenza di replica troppo aggressiva per la bandwidth disponibile, firewall che blocca le porte.

**Soluzione**:

```powershell
# Verificare lo stato dettagliato della replica
Get-VMReplication | Select-Object VMName, State, Health, Mode,
    LastReplicationTime, ReplicationFrequencySec,
    @{N='LagMinutes';E={[math]::Round(((Get-Date) - $_.LastReplicationTime).TotalMinutes, 1)}}

# Resincronizzare una replica in stato critico
Resume-VMReplication -VMName "SRV-APP01"

# Se la resync non funziona, rimuovere e riconfigurare la replica
Remove-VMReplication -VMName "SRV-APP01"
# Poi riconfigurare con Enable-VMReplication

# Verificare la connettività e le porte
Test-NetConnection -ComputerName "HVHOST-DR.contoso.com" -Port 80   # Kerberos
Test-NetConnection -ComputerName "HVHOST-DR.contoso.com" -Port 443  # Certificate
```

### Problema: Merge del Checkpoint Bloccato — Disco in Stato "Merging"

**Sintomi**: Dopo la rimozione di un checkpoint, il merge del disco .avhdx nel parent procede lentamente o sembra bloccato. Le prestazioni I/O della VM sono degradate.

**Causa**: Checkpoint molto grande (accumulo di settimane di operazioni), storage fisico lento, alta attività I/O sulla VM che compete con il merge.

**Soluzione**:

```powershell
# Verificare lo stato dei merge in corso
Get-VM | Where-Object Status -like "*Merging*" | Select-Object Name, Status

# Verificare la dimensione dei file AVHDX (checkpoint disk)
Get-VM -Name "SRV-APP01" | Get-VMHardDiskDrive | ForEach-Object {
    $vhd = Get-VHD -Path $_.Path
    [PSCustomObject]@{
        Path     = $_.Path
        Type     = $vhd.VhdType
        SizeGB   = [math]::Round($vhd.FileSize / 1GB, 2)
        Parent   = $vhd.ParentPath
    }
}

# Il merge è un'operazione online — non interromperla
# Se lo storage è lento, considerare lo spostamento dello storage su SSD/NVMe prima di operazioni di merge future
# In futuro, usare ReFS per merge istantanei (block cloning)
```

### Problema: Memory Pressure — VM Lente per Mancanza di RAM

**Sintomi**: Le VM con Dynamic Memory mostrano stato "Warning" o "Low". Le applicazioni nella VM sono lente, il sistema fa swapping eccessivo.

**Causa**: L'host non ha sufficiente RAM per soddisfare la domanda di tutte le VM. Il priority weight delle VM non è configurato correttamente. Il buffer è troppo basso.

**Soluzione**:

```powershell
# Identificare le VM sotto pressione di memoria
Get-VM | Where-Object {$_.State -eq "Running" -and $_.DynamicMemoryEnabled} |
    Select-Object Name,
        @{N='AssignedMB';E={[math]::Round($_.MemoryAssigned/1MB)}},
        @{N='DemandMB';E={[math]::Round($_.MemoryDemand/1MB)}},
        @{N='Pressure';E={
            if ($_.MemoryAssigned -gt 0) {
                [math]::Round(($_.MemoryDemand / $_.MemoryAssigned) * 100, 1)
            } else { "N/A" }
        }},
        MemoryStatus |
    Sort-Object { $_.MemoryStatus } | Format-Table -AutoSize

# Aumentare il priority weight per le VM critiche
Set-VMMemory -VMName "SRV-SQL01" -Priority 8000  # Riceverà memoria per prima
Set-VMMemory -VMName "SRV-DEV01" -Priority 2000  # Cedrà memoria per prima

# Verificare la RAM totale disponibile sull'host
Get-VMHostNumaNode | Select-Object NodeId,
    @{N='TotalGB';E={[math]::Round($_.MemoryTotal/1GB, 1)}},
    @{N='AvailGB';E={[math]::Round($_.MemoryAvailable/1GB, 1)}}
```

### Problema: Nested Virtualization Non Funziona

**Sintomi**: L'installazione di Hyper-V all'interno di una VM fallisce. Il guest OS non rileva il supporto alla virtualizzazione hardware.

**Causa**: `ExposeVirtualizationExtensions` non abilitato sulla VM L1, VM non è Generation 2, Dynamic Memory abilitata (incompatibile), host con versione di Hyper-V precedente a Windows Server 2016.

**Soluzione**:

```powershell
# Verificare i prerequisiti
$vm = Get-VM -Name "LAB-HOST01"
$proc = Get-VMProcessor -VMName "LAB-HOST01"
[PSCustomObject]@{
    VM          = $vm.Name
    Generation  = $vm.Generation
    DynMemory   = $vm.DynamicMemoryEnabled
    VirtExt     = $proc.ExposeVirtualizationExtensions
    MACSpoof    = (Get-VMNetworkAdapter -VMName "LAB-HOST01").MacAddressSpoofing
} | Format-List

# Correggere: spegnere la VM e abilitare le estensioni
Stop-VM -Name "LAB-HOST01"
Set-VMProcessor -VMName "LAB-HOST01" -ExposeVirtualizationExtensions $true
Set-VMNetworkAdapter -VMName "LAB-HOST01" -MacAddressSpoofing On
# Disabilitare Dynamic Memory (incompatibile con nested virt)
Set-VM -Name "LAB-HOST01" -StaticMemory -MemoryStartupBytes 16GB
Start-VM -Name "LAB-HOST01"
```

### Problema: Cluster Failover in Loop — VM Continua a Spostarsi

**Sintomi**: Una VM si sposta ripetutamente tra i nodi del cluster. Il failover avviene, la VM si riavvia, poi si sposta di nuovo.

**Causa**: Il VM Monitoring ha rilevato un servizio che non riesce a partire, ma il failover non risolve il problema. Risorse insufficienti su entrambi i nodi. Quorum instabile.

**Soluzione**:

```powershell
# Verificare gli eventi del cluster
Get-ClusterLog -Destination "C:\Logs" -TimeSpan 60  # Ultimi 60 minuti

# Verificare i servizi monitorati e il loro stato
Get-ClusterVMMonitoredItem -VirtualMachine "SRV-APP01"

# Disabilitare temporaneamente il VM Monitoring per fermare il loop
Remove-ClusterVMMonitoredItem -VirtualMachine "SRV-APP01" -Service "ProblematicService"

# Verificare lo stato del quorum
Get-ClusterQuorum | Select-Object QuorumType, QuorumResource

# Verificare i nodi del cluster
Get-ClusterNode | Select-Object Name, State, DrainStatus
```

### Problema: vSwitch Connectivity Loss — Host Perde la Rete

**Sintomi**: Dopo la creazione di un External vSwitch, l'host perde la connettività di rete. Le VM funzionano ma il management OS non è raggiungibile.

**Causa**: `AllowManagementOS` impostato a `$false` durante la creazione dello switch. La NIC fisica è stata assegnata al vSwitch senza creare una vNIC per il management OS.

**Soluzione**:

```powershell
# Se si ha accesso locale (console/IPMI/iDRAC):
# Abilitare il management OS sul vSwitch esistente
Set-VMSwitch -Name "vSwitch-Prod" -AllowManagementOS $true

# Verificare che la vNIC del management OS abbia un IP
Get-NetAdapter | Where-Object InterfaceDescription -like "*Hyper-V*"
Get-NetIPAddress -InterfaceAlias "vEthernet (vSwitch-Prod)"

# Se l'IP è mancante, riconfigurarlo
New-NetIPAddress -InterfaceAlias "vEthernet (vSwitch-Prod)" `
    -IPAddress "10.0.1.50" -PrefixLength 24 -DefaultGateway "10.0.1.1"
Set-DnsClientServerAddress -InterfaceAlias "vEthernet (vSwitch-Prod)" `
    -ServerAddresses "10.0.1.10","10.0.1.11"
```

### Problema: Secure Boot Blocca l'Avvio di Linux

**Sintomi**: Una VM Generation 2 con Linux non si avvia. Il firmware UEFI mostra "Secure Boot Failed" o la VM resta in un loop di avvio.

**Causa**: Il template Secure Boot non è corretto. Le VM Windows usano `MicrosoftWindows`, le VM Linux devono usare `MicrosoftUEFICertificateAuthority`.

**Soluzione**:

```powershell
# Verificare il template Secure Boot attuale
Get-VMFirmware -VMName "SRV-LINUX01" | Select-Object SecureBoot, SecureBootTemplate

# Cambiare al template corretto per Linux
Set-VMFirmware -VMName "SRV-LINUX01" -SecureBootTemplate MicrosoftUEFICertificateAuthority

# Se il problema persiste con distribuzioni non firmate, disabilitare Secure Boot
Set-VMFirmware -VMName "SRV-LINUX01" -EnableSecureBoot Off
```

### Problema: vTPM Error — "Key protector not found"

**Sintomi**: La VM non si avvia con errore relativo al key protector o al TPM virtuale. Succede tipicamente dopo il ripristino di una VM da backup o dopo lo spostamento dei file di configurazione.

**Causa**: Il key protector è legato all'host specifico (local key protector). Quando i file della VM vengono spostati su un altro host, il key protector originale non è disponibile.

**Soluzione**:

```powershell
# Verificare lo stato della sicurezza della VM
Get-VMSecurity -VMName "SRV-APP01" | Select-Object TpmEnabled, KsdEnabled, Shielded

# Ricreare il key protector locale (perde la chiave precedente — BitLocker dovrà essere riconfigurato nel guest)
Set-VMKeyProtector -VMName "SRV-APP01" -NewLocalKeyProtector

# Ri-abilitare il vTPM
Enable-VMTPM -VMName "SRV-APP01"
```

### Problema: Storage Migration Timeout

**Sintomi**: La migrazione dello storage di una VM fallisce con timeout. Il processo inizia ma non completa.

**Causa**: Disco VHDX di grandi dimensioni, rete SMB lenta, alta attività I/O nella VM durante la migrazione, file lock su antivirus o backup.

**Soluzione**:

```powershell
# Verificare la dimensione dei dischi da migrare
Get-VMHardDiskDrive -VMName "SRV-APP01" | ForEach-Object {
    [PSCustomObject]@{
        Path = $_.Path
        SizeGB = [math]::Round((Get-VHD -Path $_.Path).FileSize / 1GB, 1)
    }
} | Format-Table

# Eseguire la migrazione con monitoraggio
$job = Move-VMStorage -VMName "SRV-APP01" -DestinationStoragePath "E:\NewStorage" -AsJob
$job | Get-Job | Select-Object State, PercentComplete

# Se lo storage di destinazione è via SMB, verificare la connettività
Test-NetConnection -ComputerName "STORAGE-SRV" -Port 445

# Aumentare la concorrenza di storage migration (default: 2)
Set-VMHost -MaximumStorageMigrations 4
```

### Problema: Alto Utilizzo CPU di vmms.exe o vmwp.exe

**Sintomi**: Il processo `vmms.exe` (Virtual Machine Management Service) o `vmwp.exe` (VM Worker Process) consuma CPU anomala sull'host.

**Causa**: `vmms.exe` alto: troppe VM, WMI queries frequenti da tool di monitoraggio, operazioni di replica/checkpoint simultanee. `vmwp.exe` alto: è il processo worker della specifica VM — indica che la VM stessa sta usando molta CPU.

**Soluzione**:

```powershell
# Identificare quale VM corrisponde a quale vmwp.exe
Get-Process vmwp | ForEach-Object {
    $proc = $_
    $vmId = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
    [PSCustomObject]@{
        PID    = $proc.Id
        CPU    = [math]::Round($proc.CPU, 1)
        MemMB  = [math]::Round($proc.WorkingSet64 / 1MB)
        VMInfo = $vmId
    }
} | Sort-Object CPU -Descending | Format-Table

# Ridurre il polling di WMI da tool esterni
# Aumentare l'intervallo di polling nei tool di monitoraggio (>60 secondi)

# Verificare se ci sono operazioni bulk in corso
Get-VM | Where-Object Status -ne "Operating normally" | Select-Object Name, Status
```

### Tabella Riepilogativa Troubleshooting

| # | Problema | Causa Tipica | Cmdlet Diagnostico |
|---|---------|-------------|-------------------|
| 1 | VM non si avvia | RAM host insufficiente, VHDX mancante | `Get-VMHostNumaNode`, `Get-VMHardDiskDrive` |
| 2 | I/O scadenti | Checkpoint accumulati, disco dinamico | `Get-VMCheckpoint`, `Get-VHD` |
| 3 | Live Migration fallisce | Kerberos delegation, CPU incompatibili | `Compare-VM`, `Get-VMHost` |
| 4 | BSOD nella VM | Integration Services obsoleti, RAM | `Get-VM -Property IntegrationServicesVersion` |
| 5 | Integration Services KO | Servizi disabilitati, moduli mancanti | `Get-VMIntegrationService` |
| 6 | VLAN non funziona | VLAN ID errato, trunk mancante | `Get-VMNetworkAdapterVlan` |
| 7 | Replica Warning | Rete instabile, disco lento | `Get-VMReplication` |
| 8 | Checkpoint merge bloccato | AVHDX grande, storage lento | `Get-VHD`, verifica stato "Merging" |
| 9 | Memory Pressure | RAM host esaurita, weight errato | `Get-VM -Property MemoryStatus` |
| 10 | Nested Virt non funziona | VirtExt non esposto, DynMem attiva | `Get-VMProcessor -Property Expose*` |
| 11 | Cluster failover loop | VM Monitoring + servizio guasto | `Get-ClusterVMMonitoredItem` |
| 12 | Host perde rete | AllowManagementOS = false | `Get-VMSwitch`, `Set-VMSwitch` |
| 13 | Secure Boot blocca Linux | Template sbagliato | `Get-VMFirmware` |
| 14 | vTPM key error | Key protector non portabile | `Get-VMSecurity`, `Set-VMKeyProtector` |
| 15 | Storage migration timeout | VHDX grande, rete SMB lenta | `Get-VMHardDiskDrive`, `Get-VHD` |
| 16 | vmms.exe CPU alta | WMI polling, operazioni bulk | `Get-Process vmms`, `Get-VM` |

---

## Esercizi Pratici

### Esercizio 1: Progettazione di una Rete Virtualizzata

**Scenario:** L'azienda ha tre ambienti: Produzione (VLAN 100), Sviluppo (VLAN 200) e Management (VLAN 10). Il server Hyper-V ha due NIC da 10 GbE.

**Compito:**
1. Creare un virtual switch SET con entrambe le NIC
2. Creare vNIC per il management OS separate per management, live migration e cluster
3. Configurare le VLAN appropriate su ogni vNIC del management OS
4. Creare una VM di test e assegnarla alla VLAN 100
5. Verificare la configurazione con i cmdlet appropriati

**Soluzione attesa:**

```powershell
# 1. Creare il SET
New-VMSwitch -Name "vSwitch-Main" -NetAdapterName "NIC1","NIC2" `
    -EnableEmbeddedTeaming $true -AllowManagementOS $false -MinimumBandwidthMode Weight

# 2. Creare le vNIC
Add-VMNetworkAdapter -ManagementOS -SwitchName "vSwitch-Main" -Name "Mgmt"
Add-VMNetworkAdapter -ManagementOS -SwitchName "vSwitch-Main" -Name "LiveMig"
Add-VMNetworkAdapter -ManagementOS -SwitchName "vSwitch-Main" -Name "Cluster"

# 3. Assegnare le VLAN
Set-VMNetworkAdapterVlan -ManagementOS -VMNetworkAdapterName "Mgmt" -Access -VlanId 10
Set-VMNetworkAdapterVlan -ManagementOS -VMNetworkAdapterName "LiveMig" -Access -VlanId 20
Set-VMNetworkAdapterVlan -ManagementOS -VMNetworkAdapterName "Cluster" -Access -VlanId 30

# 4. Creare una VM di test
New-VM -Name "TEST-VLAN" -Generation 2 -MemoryStartupBytes 2GB -SwitchName "vSwitch-Main" `
    -NewVHDPath "D:\VHDs\TEST-VLAN.vhdx" -NewVHDSizeBytes 40GB
Set-VMNetworkAdapterVlan -VMName "TEST-VLAN" -Access -VlanId 100

# 5. Verificare
Get-VMSwitch | Format-Table Name, SwitchType, EmbeddedTeamingEnabled
Get-VMNetworkAdapterVlan -ManagementOS | Format-Table VMNetworkAdapterName, AccessVlanId
Get-VMNetworkAdapterVlan -VMName "TEST-VLAN"
```

### Esercizio 2: Implementare Hyper-V Replica tra Due Host

**Scenario:** Due host Hyper-V standalone (HVHOST01 e HVHOST02) nello stesso dominio. Configurare la replica Kerberos per la VM "SRV-APP01" con frequenza di 5 minuti e 12 recovery points.

**Compito:**
1. Abilitare la replica sul server di destinazione (HVHOST02)
2. Autorizzare HVHOST01 a replicare
3. Configurare la replica sulla VM dal server primario
4. Avviare la replica iniziale
5. Verificare lo stato della replica
6. Eseguire un test failover

**Criteri di valutazione:**
- Frequenza di replica corretta (300 secondi)
- Recovery history configurato (12 punti)
- VSS snapshot ogni 4 ore
- Test failover eseguito e completato senza impatto sulla produzione

### Esercizio 3: Script di Capacity Planning

**Scenario:** Scrivere uno script PowerShell che generi un report di capacity planning per l'host Hyper-V. Il report deve includere:
- CPU: rapporto vCPU:pCPU, percentuale di utilizzo media
- RAM: totale, assegnata, libera, percentuale di utilizzo
- Storage: spazio disco per volume, percentuale di utilizzo
- VM: elenco completo con risorse assegnate
- Alert: evidenziare le metriche che superano le soglie (CPU >70%, RAM >85%, Storage >80%)

**Output atteso:** File CSV + messaggio di riepilogo a console con eventuali warning.

**Traccia della soluzione:**

```powershell
function Get-HVCapacityReport {
    param(
        [string]$OutputPath = "C:\Reports",
        [int]$CpuThreshold = 70,
        [int]$RamThreshold = 85,
        [int]$StorageThreshold = 80
    )

    $warnings = @()

    # --- CPU ---
    $physCores = (Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
    $totalVCpus = (Get-VM | Where-Object State -eq 'Running' | Measure-Object -Property ProcessorCount -Sum).Sum
    $vcpuRatio  = if ($physCores -gt 0) { [math]::Round($totalVCpus / $physCores, 2) } else { 0 }
    $cpuUsage   = [math]::Round((Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 2 -MaxSamples 3 |
        Select-Object -ExpandProperty CounterSamples | Measure-Object CookedValue -Average).Average, 1)

    if ($cpuUsage -gt $CpuThreshold) {
        $warnings += "CPU usage $cpuUsage% exceeds threshold $CpuThreshold%"
    }

    # --- RAM ---
    $os = Get-CimInstance Win32_OperatingSystem
    $totalRamGB   = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
    $freeRamGB    = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
    $assignedRamGB = [math]::Round((Get-VM | Where-Object State -eq 'Running' |
        Measure-Object -Property MemoryAssigned -Sum).Sum / 1GB, 1)
    $ramUsagePct  = [math]::Round((($totalRamGB - $freeRamGB) / $totalRamGB) * 100, 1)

    if ($ramUsagePct -gt $RamThreshold) {
        $warnings += "RAM usage $ramUsagePct% exceeds threshold $RamThreshold%"
    }

    # --- Storage ---
    $volumes = Get-Volume | Where-Object { $_.DriveLetter -and $_.Size -gt 0 } | ForEach-Object {
        $usedPct = [math]::Round((($_.Size - $_.SizeRemaining) / $_.Size) * 100, 1)
        if ($usedPct -gt $StorageThreshold) {
            $warnings += "Volume $($_.DriveLetter): usage $usedPct% exceeds threshold $StorageThreshold%"
        }
        [PSCustomObject]@{
            Drive    = "$($_.DriveLetter):"
            SizeGB   = [math]::Round($_.Size / 1GB, 1)
            FreeGB   = [math]::Round($_.SizeRemaining / 1GB, 1)
            UsedPct  = $usedPct
        }
    }

    # --- VM Inventory ---
    $vmData = Get-VM | ForEach-Object {
        [PSCustomObject]@{
            Name      = $_.Name
            State     = $_.State
            vCPUs     = $_.ProcessorCount
            MemoryMB  = [math]::Round($_.MemoryAssigned / 1MB)
            DynMem    = $_.DynamicMemoryEnabled
            Uptime    = $_.Uptime.ToString("dd\.hh\:mm")
        }
    }

    # --- Output ---
    if (-not (Test-Path $OutputPath)) { New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null }
    $vmData | Export-Csv "$OutputPath\VM-Capacity-$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation

    Write-Host "`n=== CAPACITY REPORT ===" -ForegroundColor Cyan
    Write-Host "CPU:     vCPU:pCPU = ${totalVCpus}:${physCores} (ratio $vcpuRatio)  |  Usage: $cpuUsage%"
    Write-Host "RAM:     Total ${totalRamGB}GB  |  Assigned ${assignedRamGB}GB  |  Free ${freeRamGB}GB  |  Usage: $ramUsagePct%"
    $volumes | Format-Table -AutoSize | Out-String | Write-Host
    Write-Host "VMs:     $(($vmData | Measure-Object).Count) total, $(($vmData | Where-Object State -eq 'Running' | Measure-Object).Count) running"

    if ($warnings.Count -gt 0) {
        Write-Host "`n⚠ WARNINGS:" -ForegroundColor Yellow
        $warnings | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    } else {
        Write-Host "`n✓ All metrics within thresholds." -ForegroundColor Green
    }
}

Get-HVCapacityReport -OutputPath "C:\Reports" -CpuThreshold 70 -RamThreshold 85 -StorageThreshold 80
```

### Esercizio 4: Disaster Recovery Drill

**Scenario:** Simulare un disaster recovery completo:
1. Creare una VM di test con un'applicazione web semplice (IIS)
2. Configurare la replica verso un secondo host
3. Attendere che la replica sia sincronizzata
4. Eseguire un planned failover
5. Verificare che l'applicazione web sia accessibile dal replica server
6. Eseguire il reverse replication per tornare all'host originale

**Criteri di valutazione:**
- Zero data loss durante il planned failover
- Downtime inferiore a 2 minuti
- Applicazione web funzionante dopo il failover
- Reverse replication configurata correttamente

### Esercizio 5: Deployment di una Shielded VM con vTPM

**Scenario:** L'azienda deve proteggere una VM contenente dati sensibili (PCI-DSS compliance). L'infrastruttura Hyper-V è composta da un HGS (Host Guardian Service) server e due guarded host.

**Compito:**
1. Verificare che il Guarded Host soddisfi i requisiti di attestation (Host Key mode)
2. Creare un template disk (VHDX) firmato con il certificato appropriato
3. Generare il Shielding Data File (PDK) contenente:
   - Volume Signature Catalog del template disk
   - Owner Guardian (certificato del proprietario)
   - Lista dei guardiani autorizzati (HGS)
   - Chiave di risposta unattend per la specializzazione
4. Deployare la Shielded VM usando il Shielding Data File
5. Verificare che il vTPM sia attivo e BitLocker sia funzionante
6. Tentare l'accesso alla console Enhanced Session e verificare che sia bloccata

**Traccia della soluzione:**

```powershell
# 1. Verificare attestation del guarded host
Get-HgsClientConfiguration
# Output atteso: IsHostGuarded = True, AttestationStatus = Passed

# 2. Creare il template disk firmato
$cert = Get-Item Cert:\LocalMachine\My\<THUMBPRINT_CERTIFICATO>
Protect-TemplateDisk -Path "D:\Templates\Win2022-Template.vhdx" `
    -TemplateName "Windows Server 2022 Shielded" `
    -Version "1.0.0.0" `
    -Certificate $cert

# 3. Generare il Volume Signature Catalog
Save-VolumeSignatureCatalog -TemplateDiskPath "D:\Templates\Win2022-Template.vhdx" `
    -VolumeSignatureCatalogPath "D:\Templates\Win2022-VSC.vsc"

# 4. Creare il Shielding Data File (PDK)
$owner = New-HgsGuardian -Name "OwnerGuardian" -GenerateCertificates
$hgsGuardian = Get-HgsGuardian -Name "HGS-Guardian"

New-ShieldingDataFile -ShieldingDataFilePath "D:\ShieldedVMs\Win2022-Shielded.pdk" `
    -Owner $owner `
    -Guardian @($hgsGuardian) `
    -VolumeIDQualifier (New-VolumeIDQualifier -VolumeSignatureCatalogFilePath "D:\Templates\Win2022-VSC.vsc" `
        -VersionRule Equals) `
    -AnswerFile "D:\Templates\unattend-shielded.xml" `
    -Policy Shielded

# 5. Deployare la VM
$vm = New-VM -Name "SRV-SHIELDED-01" -Generation 2 -MemoryStartupBytes 4GB `
    -VHDPath "D:\VMs\SRV-SHIELDED-01.vhdx" -SwitchName "vSwitch-Prod"
Initialize-ShieldedVM -VM $vm -ShieldingDataFilePath "D:\ShieldedVMs\Win2022-Shielded.pdk"

# 6. Verificare vTPM e stato sicurezza
Get-VMSecurity -VMName "SRV-SHIELDED-01"
# Output atteso: TpmEnabled = True, Shielded = True, EncryptStateAndVmMigrationTraffic = True

Get-VMKeyProtector -VMName "SRV-SHIELDED-01" | Format-List
```

**Criteri di valutazione:**
- Attestation del guarded host completata con successo
- Shielding Data File creato con Owner Guardian + HGS Guardian
- VM avviata in stato "Shielded"
- vTPM attivo e funzionante (Get-VMSecurity mostra TpmEnabled = True)
- Enhanced Session bloccata — la console mostra solo una schermata nera con il messaggio che il video remoto non è supportato

---

## Autovalutazione

<details>
<summary>1. Qual è la differenza tra un hypervisor di Tipo 1 e di Tipo 2? In quale categoria rientra Hyper-V e perché?</summary>

Un hypervisor di **Tipo 1** (bare-metal) viene eseguito direttamente sull'hardware fisico, prima del sistema operativo. Un hypervisor di **Tipo 2** (hosted) viene eseguito come un'applicazione all'interno di un sistema operativo host (esempio: VirtualBox, VMware Workstation).

Hyper-V è un hypervisor di **Tipo 1**: si inserisce tra l'hardware e il sistema operativo. Ciò che sembra essere il "sistema operativo host" è in realtà la **partizione parent** (root partition), che è essa stessa una macchina virtuale privilegiata che gira sopra l'hypervisor. Questo design garantisce isolamento hardware-level e prestazioni superiori rispetto al Tipo 2.
</details>

<details>
<summary>2. Cosa sono le enlightenments in Hyper-V e quale impatto hanno sulle prestazioni?</summary>

Le **enlightenments** sono ottimizzazioni specifiche che un guest OS può sfruttare quando è consapevole di essere virtualizzato su Hyper-V. Includono: **hypercalls** (chiamate dirette all'hypervisor), **synthetic interrupts** (SynIC, che riducono le VM-exit per la gestione degli interrupt), **APIC virtualization** (gestione hardware degli interrupt senza VM-exit), e **Reference TSC** (accesso al timestamp senza VM-exit).

L'impatto è significativo: l'overhead della virtualizzazione si riduce dal 10-15% (senza enlightenments) al 2-5% (con enlightenments attive). L'operazione più impattata è la lettura del TSC, che migliora di circa 50x con le enlightenments.
</details>

<details>
<summary>3. Quando è preferibile usare dischi VHDX fissi rispetto a dinamici? Qual è il vantaggio di ReFS per lo storage Hyper-V?</summary>

I **dischi fissi** sono preferibili per VM di **produzione con I/O intensivo** (database, file server), perché lo spazio è pre-allocato e non c'è overhead di allocazione durante la scrittura. I **dischi dinamici** sono adatti per sviluppo, test e VM con I/O moderato, dove il risparmio di spazio è più importante delle prestazioni pure.

**ReFS** offre vantaggi specifici per Hyper-V grazie al **block cloning**: la creazione di dischi fissi è istantanea (secondi anziché minuti per centinaia di GB), il merge dei checkpoint è quasi istantaneo, e gli integrity streams proteggono dalla corruzione silenziosa dei dati.
</details>

<details>
<summary>4. Spiega il flusso della Dynamic Memory: cosa sono Startup Memory, Minimum, Maximum, Buffer e Priority? Come interagiscono in uno scenario di memory pressure?</summary>

- **Startup Memory**: RAM assegnata all'avvio della VM.
- **Minimum Memory**: soglia minima sotto la quale l'hypervisor non ridurrà la RAM, anche sotto pressione.
- **Maximum Memory**: tetto massimo di RAM assegnabile alla VM.
- **Buffer**: percentuale di RAM aggiuntiva mantenuta oltre la domanda reale (es. 20% = se la domanda è 4 GB, vengono assegnati 4.8 GB).
- **Priority (Weight)**: valore 0-10000 che determina la priorità in caso di contesa.

In uno scenario di **memory pressure**: il balancer dell'hypervisor inizia a recuperare RAM dalle VM con priority più bassa, tramite il balloon driver. Le VM con priority alta mantengono la RAM più a lungo. Se la pressione è estrema, le VM raggiungono il Minimum Memory e non possono essere ridotte ulteriormente — a quel punto il guest OS inizia a fare paging internamente.
</details>

<details>
<summary>5. Quali sono le tre modalità di trasporto per la Live Migration? Quando scegliere SMB rispetto a Compression?</summary>

Le tre modalità sono:
- **TCP**: trasferimento standard, compatibilità massima. Per reti < 10 Gbps.
- **Compression**: comprime la memoria in-RAM prima del trasferimento. Ideale per reti lente — riduce il volume di dati a scapito di CPU sull'host.
- **SMB**: trasferimento via SMB 3.0 con supporto opzionale RDMA. Per reti 10+ Gbps.

**Scegliere SMB** quando si dispone di NIC con supporto RDMA (RoCE o iWARP) su reti 10/25/40 Gbps — il trasferimento bypassa la CPU e va direttamente dalla RAM alla rete. **Scegliere Compression** quando la rete è il collo di bottiglia (1 Gbps o WAN) e il guest OS ha molta memoria "fredda" (facilmente comprimibile). L'uso di CPU per la compressione è generalmente preferibile all'attesa di trasferimento su reti lente.
</details>

<details>
<summary>6. Cos'è un Cluster Shared Volume (CSV) e perché è necessario per il Failover Clustering con Hyper-V?</summary>

Un **CSV (Cluster Shared Volume)** è un volume di storage condiviso accessibile simultaneamente da tutti i nodi di un cluster Windows. Ogni nodo vede il CSV come `C:\ClusterStorage\VolumeN\`.

È necessario perché il Failover Clustering di Hyper-V richiede che i file della VM (VHDX, configurazione, stato) siano accessibili da qualsiasi nodo che potrebbe ospitare la VM dopo un failover. Senza CSV, ogni nodo vedrebbe solo il proprio storage locale e il failover richiederebbe anche la migrazione dello storage (molto più lento). Con CSV, il failover è quasi istantaneo: il nuovo nodo proprietario prende il coordinamento del volume e avvia la VM usando gli stessi file VHDX sullo storage condiviso.
</details>

<details>
<summary>7. Qual è la differenza tra Hyper-V Replica e Live Migration? Quando usare l'uno piuttosto che l'altro?</summary>

**Live Migration** sposta una VM in esecuzione da un host a un altro in tempo reale, con downtime impercettibile (millisecondi). Richiede che gli host siano nello stesso dominio, con CPU compatibili e storage condiviso (o shared-nothing migration). È usata per manutenzione pianificata e bilanciamento del carico.

**Hyper-V Replica** è una replica asincrona della VM su un host secondario, pensata per il disaster recovery. Non richiede storage condiviso, funziona attraverso WAN, e può usare autenticazione basata su certificati. La replica è periodica (30s, 5m, 15m) e il failover ha un RPO definito dalla frequenza di replica.

**Usa Live Migration** per: manutenzione host, bilanciamento carico, aggiornamenti senza downtime (stesso datacenter).
**Usa Replica** per: DR cross-site, protezione da disastri, failover su un sito secondario.
</details>

<details>
<summary>8. Cos'è una Shielded VM e quali protezioni fornisce? In quale scenario è indispensabile?</summary>

Una **Shielded VM** è una VM protetta crittograficamente che impedisce l'accesso non autorizzato ai dati anche da parte degli amministratori dell'host Hyper-V. Le protezioni includono: dischi VHDX cifrati con BitLocker (tramite vTPM), console access bloccato, PowerShell Direct disabilitato, export della VM bloccato, memoria non ispezionabile dall'host admin.

La Shielded VM richiede una **Guarded Fabric**: un Host Guardian Service (HGS) che attesta l'identità e l'integrità degli host Hyper-V. Solo gli host attestati possono ricevere le chiavi per sbloccare il vTPM e avviare la Shielded VM.

È **indispensabile** in scenari **multi-tenant** (hosting provider, cloud privato) dove l'amministratore dell'infrastruttura non deve poter accedere ai dati dei tenant, e in ambienti con **requisiti di compliance** stringenti (HIPAA, PCI-DSS, classificato governativo).
</details>

<details>
<summary>9. Quali sono le differenze tra Process Isolation e Hyper-V Isolation per i container Windows?</summary>

**Process Isolation** condivide il kernel dell'host con il container. L'isolamento è a livello di namespace e job objects (simile ai container Linux). L'overhead è minimo (~2-5 MB per container), ma il container deve avere la stessa versione kernel dell'host e l'isolamento è meno robusto.

**Hyper-V Isolation** crea una VM leggera (utility VM) dedicata per ogni container, con un kernel separato. L'overhead è maggiore (~100-200 MB per container), ma l'isolamento è a livello hardware. Il container può avere una versione kernel diversa dall'host.

**Process Isolation** per: ambienti trusted, sviluppo, microservizi interni, massime prestazioni.
**Hyper-V Isolation** per: ambienti multi-tenant, codice untrusted, compliance, versioni kernel diverse.
</details>

<details>
<summary>10. Come si diagnostica un problema di connettività di rete in una VM Hyper-V? Elenca i 5 passi principali.</summary>

1. **Verificare il virtual switch**: `Get-VMSwitch` — lo switch esiste? È del tipo corretto (External/Internal/Private)?
2. **Verificare la connessione VM-switch**: `Get-VMNetworkAdapter -VMName "VM"` — la VM è connessa allo switch? Lo switch è attivo?
3. **Verificare la VLAN**: `Get-VMNetworkAdapterVlan -VMName "VM"` — la VLAN è corretta? Corrisponde alla VLAN configurata sullo switch fisico?
4. **Verificare le protezioni**: `Get-VMNetworkAdapter -VMName "VM" | Select MacAddressSpoofing, DhcpGuard, RouterGuard` — le protezioni stanno bloccando il traffico legittimo?
5. **Verificare il livello fisico**: `Get-NetAdapter | Where InterfaceDescription -like "*Hyper-V*"` — la NIC del management OS ha un IP? La NIC fisica sottostante è up?

Se tutti i livelli sono corretti, il problema è probabilmente nello switch fisico (trunk VLAN non configurato, porta in errore) o nel guest OS (firewall, IP statico errato, DNS).
</details>

---

## Cross-link ai Moduli Correlati

| Modulo | Relazione con Hyper-V |
|--------|----------------------|
| [01-active-directory.md](01-active-directory.md) | Kerberos delegation per Live Migration, domain join degli host, account computer per cluster |
| [02-powershell.md](02-powershell.md) | Cmdlet base per la gestione delle VM |
| [05-sicurezza-windows.md](05-sicurezza-windows.md) | BitLocker per Shielded VMs, TPM, policy di sicurezza host |
| [06-rete-windows.md](06-rete-windows.md) | NIC teaming, VLAN, DNS per il networking delle VM |
| [07-storage-windows.md](07-storage-windows.md) | ReFS, iSCSI, SMB 3.0 per lo storage delle VM |
| [09-monitoraggio-performance.md](09-monitoraggio-performance.md) | Performance Monitor, contatori Hyper-V, baseline |
| [15-backup-ripristino.md](15-backup-ripristino.md) | Windows Server Backup, VSS, strategie di backup VM |
| [17-wsl.md](17-wsl.md) | WSL2 utilizza un kernel Linux su Hyper-V, coesistenza |
| [19-troubleshooting.md](19-troubleshooting.md) | Metodologie generali di troubleshooting applicabili a Hyper-V |
| [21-group-policy-guida-completa.md](21-group-policy-guida-completa.md) | GPO per configurazione host Hyper-V, policy di sicurezza |
| [22-powershell-scripting-avanzato.md](22-powershell-scripting-avanzato.md) | Scripting avanzato per automazione Hyper-V |
| [24-windows-defender-endpoint-security.md](24-windows-defender-endpoint-security.md) | Esclusioni antivirus per VHDX, protezione host |

---

## Riferimenti

- Microsoft Docs: Hyper-V Technology Overview — https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/hyper-v-technology-overview — Consultato: 2026-05-23
- Microsoft Docs: Hyper-V Architecture — https://learn.microsoft.com/en-us/virtualization/hyper-v-on-windows/reference/hyper-v-architecture — Consultato: 2026-05-23
- Microsoft Docs: Live Migration — https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/manage/live-migration-overview — Consultato: 2026-05-23
- Microsoft Docs: Hyper-V Replica — https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/manage/set-up-hyper-v-replica — Consultato: 2026-05-23
- Microsoft Docs: Nested Virtualization — https://learn.microsoft.com/en-us/virtualization/hyper-v-on-windows/user-guide/nested-virtualization — Consultato: 2026-05-23
- Microsoft Docs: Generation 2 VM — https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/plan/should-i-create-a-generation-1-or-2-virtual-machine-in-hyper-v — Consultato: 2026-05-23
- Microsoft Docs: Shielded VMs and Guarded Fabric — https://learn.microsoft.com/en-us/windows-server/security/guarded-fabric-shielded-vm/guarded-fabric-and-shielded-vms — Consultato: 2026-05-23
- Microsoft Docs: Failover Clustering — https://learn.microsoft.com/en-us/windows-server/failover-clustering/failover-clustering-overview — Consultato: 2026-05-23
- Microsoft Docs: Hyper-V Virtual Switch — https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v-virtual-switch/hyper-v-virtual-switch — Consultato: 2026-05-23
- Microsoft Docs: Windows Containers — https://learn.microsoft.com/en-us/virtualization/windowscontainers/ — Consultato: 2026-05-23
- Microsoft Docs: Hyper-V PowerShell Module — https://learn.microsoft.com/en-us/powershell/module/hyper-v/ — Consultato: 2026-05-23
- Microsoft Docs: Storage Quality of Service — https://learn.microsoft.com/en-us/windows-server/storage/storage-qos/storage-qos-overview — Consultato: 2026-05-23

---

## Glossario Locale

| Termine | Definizione |
|---------|-------------|
| **AVHDX** | Automatic Virtual Hard Disk eXtended — file disco differencing creato dai checkpoint. Contiene solo le modifiche rispetto al disco parent |
| **CSV** (Cluster Shared Volume) | Volume di storage condiviso accessibile simultaneamente da tutti i nodi di un Failover Cluster, montato in `C:\ClusterStorage\` |
| **DDA** (Discrete Device Assignment) | Tecnologia di GPU passthrough che assegna un dispositivo PCIe fisico direttamente a una VM, bypassando l'hypervisor per l'I/O del dispositivo |
| **Dynamic Memory** | Funzionalità che regola automaticamente la RAM assegnata a una VM in base alla domanda effettiva, tramite il balloon driver |
| **Enlightenment** | Ottimizzazione paravirtualizzata che il guest OS sfrutta quando è consapevole di girare su Hyper-V, riducendo l'overhead della virtualizzazione |
| **EPT** (Extended Page Tables) | Implementazione Intel della SLAT. Gestisce la traduzione degli indirizzi di memoria guest → fisici in hardware |
| **Guarded Fabric** | Infrastruttura di sicurezza composta da HGS e Guarded Host che garantisce l'esecuzione delle Shielded VMs solo su host attestati |
| **HGS** (Host Guardian Service) | Servizio che attesta l'identità e l'integrità degli host Hyper-V e rilascia le chiavi per sbloccare le Shielded VMs |
| **Hypervisor** | Software thin-layer che si interpone tra l'hardware fisico e i sistemi operativi, gestendo l'allocazione delle risorse e l'isolamento tra le partizioni |
| **Live Migration** | Spostamento di una VM in esecuzione da un host a un altro senza downtime percepibile, tramite trasferimento iterativo della memoria |
| **Nested Virtualization** | Capacità di eseguire un hypervisor all'interno di una VM, abilitando scenari di laboratorio e container Hyper-V |
| **NUMA** (Non-Uniform Memory Access) | Architettura di memoria dei server multi-socket dove ogni socket ha la propria bank di RAM locale con latenza di accesso inferiore |
| **Partizione Parent (Root)** | La partizione privilegiata in Hyper-V che ha accesso diretto all'hardware fisico e ospita i VSP. È il "sistema operativo host" |
| **Partizione Figlio (Child)** | Una macchina virtuale guest che accede all'hardware tramite i driver sintetici (VSC) e il VMBus |
| **SET** (Switch Embedded Teaming) | Tecnologia di NIC teaming integrata nel virtual switch di Hyper-V, alternativa moderna al LBFO con supporto RDMA e SDN |
| **Shielded VM** | VM protetta crittograficamente con vTPM, BitLocker, console bloccata, che può essere eseguita solo su host attestati |
| **SLAT** (Second Level Address Translation) | Tecnologia CPU (EPT su Intel, RVI su AMD) che traduce in hardware gli indirizzi di memoria guest in indirizzi fisici |
| **Smart Paging** | File di paging temporaneo su disco usato durante l'avvio di una VM quando la Startup Memory supera la RAM fisica disponibile |
| **Storage QoS** | Quality of Service per lo storage che consente di limitare e garantire IOPS per VM, prevenendo il "noisy neighbor" |
| **VHDX** | Virtual Hard Disk eXtended — formato disco virtuale con supporto fino a 64 TB, settori 4K, logging interno e resize online |
| **VMBus** | Virtual Machine Bus — canale di comunicazione ad alta velocità tra partizione parent e partizioni figlio, basato su memoria condivisa |
| **VSC** (Virtualization Service Consumer) | Driver sintetici nella partizione figlio che comunicano con i VSP tramite VMBus |
| **VSP** (Virtualization Service Provider) | Driver nella partizione parent che gestiscono l'accesso all'hardware fisico per conto delle partizioni figlio |
| **vTPM** | Virtual Trusted Platform Module — emulazione software del chip TPM che consente BitLocker, Secure Boot e attestation nelle VM |
