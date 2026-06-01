# Lab 05 — Cluster Hyper-V a 3 Nodi con Failover

> **Modulo di riferimento:** [23-hyper-v-guida-completa.md](../23-hyper-v-guida-completa.md), [27-failover-clustering-guida.md](../27-failover-clustering-guida.md), [07-storage-windows.md](../07-storage-windows.md)
> **Tempo stimato:** 3-4 ore
> **Livello:** advanced
> **Prerequisiti:** 3 server Windows Server 2022 (fisici o VM nested), rete con almeno 4 NIC per nodo (o VLAN), storage condiviso (iSCSI target o S2D), completamento moduli 03, 07, 23
> **Ultimo aggiornamento:** 2026-05-23

---

## Obiettivo

Costruire un cluster Hyper-V a 3 nodi con storage condiviso, configurare Cluster Shared Volumes, eseguire live migration e quick migration, simulare failover automatico, configurare Cluster-Aware Updating e Hyper-V Replica verso un sito secondario simulato.

> **Riferimento ufficiale:** [Microsoft Learn — Failover Clustering](https://learn.microsoft.com/en-us/windows-server/failover-clustering/failover-clustering-overview)
> **Riferimento Hyper-V:** [Microsoft Learn — Hyper-V on Windows Server](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/hyper-v-on-windows-server)

---

## Ambiente

### Nodi del cluster

| Ruolo | Hostname | IP Management | IP Live Migration | IP Cluster | IP Storage |
|-------|----------|---------------|-------------------|------------|------------|
| Nodo 1 | HV-NODE01 | 10.0.1.11 | 10.0.2.11 | 10.0.3.11 | 10.0.4.11 |
| Nodo 2 | HV-NODE02 | 10.0.1.12 | 10.0.2.12 | 10.0.3.12 | 10.0.4.12 |
| Nodo 3 | HV-NODE03 | 10.0.1.13 | 10.0.2.13 | 10.0.3.13 | 10.0.4.13 |

### Infrastruttura di supporto

| Ruolo | Hostname | IP | Note |
|-------|----------|----|------|
| DC / DNS | DC01 | 10.0.1.10 | Active Directory, DNS |
| iSCSI Target | STORAGE01 | 10.0.4.10 | iSCSI target con 3 LUN |
| Replica target (sito 2) | HV-REPLICA01 | 10.0.5.20 | Stand-alone Hyper-V |

### Reti

| Rete | Subnet | VLAN | Scopo |
|------|--------|------|-------|
| Management | 10.0.1.0/24 | 10 | Gestione, RDP, dominio |
| Live Migration | 10.0.2.0/24 | 20 | Traffico live migration (dedicata) |
| Cluster (heartbeat) | 10.0.3.0/24 | 30 | Comunicazione intra-cluster |
| Storage | 10.0.4.0/24 | 40 | iSCSI / SMB storage |

- Dominio: `lab.local`
- Tutti i nodi uniti al dominio
- Snapshot di tutte le VM **prima di iniziare**
- Se si usa nested virtualization, abilitare: `Set-VMProcessor -VMName <nome> -ExposeVirtualizationExtensions $true`

---

## Parte 1 — Prerequisiti e Infrastruttura (30 min)

### 1.1 Configurare le reti su tutti i nodi

Eseguire su ciascun nodo (HV-NODE01, HV-NODE02, HV-NODE03). Adattare gli IP per ogni nodo.

```powershell
# Rinominare le interfacce di rete per chiarezza
Get-NetAdapter | Format-Table Name, InterfaceDescription, Status, MacAddress

# Assegnare nomi descrittivi (adattare in base all'ordine delle NIC)
Rename-NetAdapter -Name "Ethernet"   -NewName "Management"
Rename-NetAdapter -Name "Ethernet 2" -NewName "LiveMigration"
Rename-NetAdapter -Name "Ethernet 3" -NewName "Cluster"
Rename-NetAdapter -Name "Ethernet 4" -NewName "Storage"

# Configurare IP — esempio per NODE01 (cambiare per NODE02/03)
New-NetIPAddress -InterfaceAlias "Management"    -IPAddress 10.0.1.11 -PrefixLength 24 -DefaultGateway 10.0.1.1
New-NetIPAddress -InterfaceAlias "LiveMigration" -IPAddress 10.0.2.11 -PrefixLength 24
New-NetIPAddress -InterfaceAlias "Cluster"       -IPAddress 10.0.3.11 -PrefixLength 24
New-NetIPAddress -InterfaceAlias "Storage"       -IPAddress 10.0.4.11 -PrefixLength 24

# DNS solo sull'interfaccia Management
Set-DnsClientServerAddress -InterfaceAlias "Management" -ServerAddresses 10.0.1.10

# Disabilitare registrazione DNS sulle interfacce non-management
Set-DnsClient -InterfaceAlias "LiveMigration" -RegisterThisConnectionsAddress $false
Set-DnsClient -InterfaceAlias "Cluster"       -RegisterThisConnectionsAddress $false
Set-DnsClient -InterfaceAlias "Storage"       -RegisterThisConnectionsAddress $false
```

### 1.2 Verificare connettivita' tra i nodi

```powershell
# Da NODE01, testare tutte le reti verso NODE02 e NODE03
$nodes = @("10.0.1.12","10.0.1.13")  # Management
$nodes | ForEach-Object { Test-Connection $_ -Count 2 }

$nodes = @("10.0.2.12","10.0.2.13")  # Live Migration
$nodes | ForEach-Object { Test-Connection $_ -Count 2 }

$nodes = @("10.0.3.12","10.0.3.13")  # Cluster
$nodes | ForEach-Object { Test-Connection $_ -Count 2 }

$nodes = @("10.0.4.12","10.0.4.13")  # Storage
$nodes | ForEach-Object { Test-Connection $_ -Count 2 }
```

### 1.3 Configurare iSCSI target server (STORAGE01)

```powershell
# Su STORAGE01: installare il ruolo iSCSI Target
Install-WindowsFeature FS-iSCSITarget-Server -IncludeManagementTools

# Creare i dischi virtuali per il cluster
# LUN 1: Quorum witness (1 GB)
New-IscsiVirtualDisk -Path "D:\iSCSI\Quorum.vhdx" -SizeBytes 1GB

# LUN 2: CSV per VM (100 GB)
New-IscsiVirtualDisk -Path "D:\iSCSI\CSV01.vhdx" -SizeBytes 100GB

# LUN 3: CSV aggiuntivo (100 GB)
New-IscsiVirtualDisk -Path "D:\iSCSI\CSV02.vhdx" -SizeBytes 100GB

# Creare il target iSCSI
New-IscsiServerTarget -TargetName "hv-cluster-target" `
    -InitiatorIds @(
        "IPAddress:10.0.4.11",
        "IPAddress:10.0.4.12",
        "IPAddress:10.0.4.13"
    )

# Mappare i dischi virtuali al target
Add-IscsiVirtualDiskTargetMapping -TargetName "hv-cluster-target" -Path "D:\iSCSI\Quorum.vhdx"
Add-IscsiVirtualDiskTargetMapping -TargetName "hv-cluster-target" -Path "D:\iSCSI\CSV01.vhdx"
Add-IscsiVirtualDiskTargetMapping -TargetName "hv-cluster-target" -Path "D:\iSCSI\CSV02.vhdx"

# Verificare la configurazione
Get-IscsiServerTarget
```

**Output atteso:**

```
TargetName      : hv-cluster-target
Status          : Connected
LunMappings     : {0, 1, 2}
InitiatorIds    : {IPAddress:10.0.4.11, IPAddress:10.0.4.12, IPAddress:10.0.4.13}
```

### 1.4 Connettere i nodi al target iSCSI

Eseguire su tutti e 3 i nodi:

```powershell
# Avviare il servizio iSCSI Initiator
Start-Service MSiSCSI
Set-Service MSiSCSI -StartupType Automatic

# Configurare il portale iSCSI
New-IscsiTargetPortal -TargetPortalAddress 10.0.4.10 -TargetPortalPortNumber 3260

# Scoprire i target disponibili
Get-IscsiTarget

# Connettere al target
Connect-IscsiTarget -NodeAddress "iqn.1991-05.com.microsoft:storage01-hv-cluster-target" `
    -TargetPortalAddress 10.0.4.10 `
    -IsPersistent $true

# Verificare la connessione
Get-IscsiSession
```

**Output atteso:**

```
AuthenticationType : NONE
InitiatorNodeAddress : iqn.1991-05.com.microsoft:hv-node01
InitiatorPortalAddress : 10.0.4.11
IsConnected : True
IsDataDigest : False
IsDiscovered : True
IsPersistent : True
TargetNodeAddress : iqn.1991-05.com.microsoft:storage01-hv-cluster-target
```

### 1.5 Inizializzare i dischi (solo su NODE01)

```powershell
# Visualizzare i nuovi dischi
Get-Disk | Where-Object { $_.PartitionStyle -eq 'RAW' }

# Inizializzare e formattare — SOLO da un nodo (gli altri vedranno i volumi automaticamente)
# Disco 1: Quorum (1 GB)
$quorumDisk = Get-Disk | Where-Object { $_.Size -eq 1GB -and $_.PartitionStyle -eq 'RAW' }
$quorumDisk | Initialize-Disk -PartitionStyle GPT
$quorumDisk | New-Partition -UseMaximumSize -AssignDriveLetter |
    Format-Volume -FileSystem NTFS -NewFileSystemLabel "Quorum" -Confirm:$false

# Disco 2: CSV01 (100 GB)
$csv01 = Get-Disk | Where-Object { $_.Size -eq 100GB -and $_.PartitionStyle -eq 'RAW' } | Select-Object -First 1
$csv01 | Initialize-Disk -PartitionStyle GPT
$csv01 | New-Partition -UseMaximumSize -AssignDriveLetter |
    Format-Volume -FileSystem NTFS -NewFileSystemLabel "CSV01" -Confirm:$false

# Disco 3: CSV02 (100 GB)
$csv02 = Get-Disk | Where-Object { $_.Size -eq 100GB -and $_.PartitionStyle -eq 'RAW' } | Select-Object -First 1
$csv02 | Initialize-Disk -PartitionStyle GPT
$csv02 | New-Partition -UseMaximumSize -AssignDriveLetter |
    Format-Volume -FileSystem NTFS -NewFileSystemLabel "CSV02" -Confirm:$false

# Verificare
Get-Volume | Where-Object { $_.FileSystemLabel -match "Quorum|CSV" }
```

### 1.6 Creare record DNS per il cluster

```powershell
# Su DC01: creare il record A per il cluster name
Add-DnsServerResourceRecordA -ZoneName "lab.local" -Name "HV-CLUSTER" -IPv4Address 10.0.1.20

# Verificare
Resolve-DnsName HV-CLUSTER.lab.local
```

---

## Parte 2 — Installazione Failover Clustering (30 min)

### 2.1 Installare ruoli su tutti i nodi

```powershell
# Eseguire su tutti e 3 i nodi (oppure via remoting)
$nodes = @("HV-NODE01", "HV-NODE02", "HV-NODE03")

foreach ($node in $nodes) {
    Invoke-Command -ComputerName $node -ScriptBlock {
        Install-WindowsFeature Failover-Clustering -IncludeManagementTools
        Install-WindowsFeature Hyper-V -IncludeManagementTools -Restart
    }
}

# I nodi si riavvieranno dopo l'installazione di Hyper-V
```

Dopo il riavvio, verificare:

```powershell
foreach ($node in $nodes) {
    Invoke-Command -ComputerName $node -ScriptBlock {
        Get-WindowsFeature Failover-Clustering, Hyper-V |
            Select-Object Name, InstallState
    }
}
```

**Output atteso (per ogni nodo):**

```
Name                   InstallState
----                   ------------
Failover-Clustering    Installed
Hyper-V                Installed
```

### 2.2 Validazione pre-cluster

```powershell
# Eseguire il test di validazione completo
# Questo identifica problemi PRIMA della creazione del cluster
Test-Cluster -Node HV-NODE01, HV-NODE02, HV-NODE03 -Include "Inventory", "Network", "Storage", "System Configuration"

# Il report HTML viene salvato in: C:\Users\<user>\AppData\Local\Temp\
# Verificare la path esatta dall'output
```

**Output atteso:**

```
WARNING: Cluster validation found some warnings or errors.
     Testing has completed successfully. The report can be found at:
     C:\Users\Administrator\AppData\Local\Temp\Validation Report 2026.05.23 At 14.30.12.htm
```

> **Troubleshooting:** Se il test di storage fallisce:
> - Verificare che i dischi iSCSI siano visibili da tutti i nodi: `Get-Disk` su ogni nodo
> - Verificare che MPIO sia configurato (se necessario): `Get-MSDSMSupportedHW`
> - Verificare le connessioni iSCSI: `Get-IscsiSession` su ogni nodo

### 2.3 Creare il cluster

```powershell
# Creare il failover cluster con IP statico
New-Cluster -Name "HV-CLUSTER" `
    -Node HV-NODE01, HV-NODE02, HV-NODE03 `
    -StaticAddress 10.0.1.20 `
    -NoStorage  # Aggiungere lo storage in fase separata

# Verificare la creazione
Get-Cluster | Format-List Name, Domain, SharedVolumesRoot
```

**Output atteso:**

```
Name              : HV-CLUSTER
Domain            : lab.local
SharedVolumesRoot : C:\ClusterStorage
```

```powershell
# Verificare i nodi del cluster
Get-ClusterNode | Format-Table Name, State, NodeWeight

# Output atteso:
# Name         State   NodeWeight
# ----         -----   ----------
# HV-NODE01    Up      1
# HV-NODE02    Up      1
# HV-NODE03    Up      1
```

### 2.4 Configurare il Cloud Witness (o File Share Witness)

**Opzione A — Cloud Witness (Azure):**

```powershell
# Richiede un Azure Storage Account
# Set-ClusterQuorum -CloudWitness `
#     -AccountName "hvclusterwitness" `
#     -AccessKey "<chiave di accesso storage>" `
#     -Endpoint "core.windows.net"
```

**Opzione B — File Share Witness (lab):**

```powershell
# Su DC01: creare una share per il quorum witness
New-Item -Path "C:\ClusterWitness" -ItemType Directory
New-SmbShare -Name "ClusterWitness" -Path "C:\ClusterWitness" `
    -FullAccess "lab\HV-CLUSTER$", "lab\Domain Admins"

# Configurare il quorum con File Share Witness
Set-ClusterQuorum -NodeAndFileShareMajority "\\DC01\ClusterWitness"

# Verificare la configurazione quorum
Get-ClusterQuorum | Format-List
```

**Output atteso:**

```
Cluster          : HV-CLUSTER
QuorumResource   : File Share Witness (\\DC01\ClusterWitness)
QuorumType       : NodeAndFileShareMajority
```

> **Nota:** Con 3 nodi + File Share Witness, il cluster tollera la perdita di 1 nodo mantenendo il quorum (3/4 voti = maggioranza).

---

## Parte 3 — Configurazione Storage Condiviso (30 min)

### 3.1 Aggiungere i dischi al cluster

```powershell
# Aggiungere tutti i dischi iSCSI disponibili al cluster
Get-ClusterAvailableDisk | Add-ClusterDisk

# Verificare i dischi del cluster
Get-ClusterResource -ResourceType "Physical Disk" |
    Format-Table Name, State, OwnerNode
```

**Output atteso:**

```
Name              State    OwnerNode
----              -----    ---------
Cluster Disk 1    Online   HV-NODE01
Cluster Disk 2    Online   HV-NODE01
Cluster Disk 3    Online   HV-NODE01
```

### 3.2 Configurare il Disk Witness per il quorum

```powershell
# Opzione alternativa alla File Share Witness:
# Usare il disco da 1 GB come disk witness
# Set-ClusterQuorum -NodeAndDiskMajority "Cluster Disk 1"

# Se si usa File Share Witness (come in 2.4), saltare questo passo
```

### 3.3 Convertire i dischi in Cluster Shared Volumes (CSV)

```powershell
# Convertire i dischi da 100 GB in CSV
# Identificare i dischi corretti per nome/dimensione
$csvDisks = Get-ClusterResource -ResourceType "Physical Disk" |
    Where-Object { $_.Name -ne "Cluster Disk 1" }  # Escludere il quorum disk

foreach ($disk in $csvDisks) {
    Add-ClusterSharedVolume -Name $disk.Name
    Write-Host "Convertito in CSV: $($disk.Name)"
}

# Verificare i CSV
Get-ClusterSharedVolume | Format-Table Name, State, OwnerNode
```

**Output atteso:**

```
Name              State    OwnerNode
----              -----    ---------
Cluster Disk 2    Online   HV-NODE01
Cluster Disk 3    Online   HV-NODE01
```

```powershell
# Verificare i mount point
Get-ClusterSharedVolume | Select-Object -ExpandProperty SharedVolumeInfo |
    Select-Object FriendlyVolumeName, @{N='FreeSpaceGB';E={[math]::Round($_.Partition.FreeSpace/1GB,2)}}
```

I CSV saranno accessibili su tutti i nodi sotto `C:\ClusterStorage\Volume1`, `C:\ClusterStorage\Volume2`.

### 3.4 Configurare Storage QoS Policy

```powershell
# Creare policy QoS per limitare IOPS (protezione contro VM rumorose)
New-StorageQosPolicy -Name "Standard-VM" `
    -PolicyType Dedicated `
    -MinimumIops 100 `
    -MaximumIops 1000

New-StorageQosPolicy -Name "Critical-VM" `
    -PolicyType Dedicated `
    -MinimumIops 500 `
    -MaximumIops 5000

# Verificare le policy
Get-StorageQosPolicy | Format-Table Name, PolicyType, MinimumIops, MaximumIops
```

**Output atteso:**

```
Name          PolicyType MinimumIops MaximumIops
----          ---------- ----------- -----------
Standard-VM   Dedicated  100         1000
Critical-VM   Dedicated  500         5000
```

> **Nota:** Storage QoS con policy centralizzate richiede un Scale-Out File Server (SOFS) o Storage Spaces Direct. Con iSCSI base, le policy sono per-VM.

---

## Parte 4 — Configurazione Hyper-V nel Cluster (30 min)

### 4.1 Aggiungere il ruolo Hyper-V al cluster

```powershell
# Il ruolo Hyper-V viene automaticamente riconosciuto dal cluster
# Verificare che sia disponibile
Get-ClusterResourceType | Where-Object { $_.Name -like "*Virtual*" }
```

### 4.2 Configurare le impostazioni Hyper-V su ogni nodo

```powershell
# Configurare il percorso predefinito per le VM su CSV
$nodes = @("HV-NODE01", "HV-NODE02", "HV-NODE03")

foreach ($node in $nodes) {
    Invoke-Command -ComputerName $node -ScriptBlock {
        Set-VMHost -VirtualMachinePath "C:\ClusterStorage\Volume1\VMs" `
                   -VirtualHardDiskPath "C:\ClusterStorage\Volume1\VHDs"
    }
}

# Verificare su ogni nodo
foreach ($node in $nodes) {
    Invoke-Command -ComputerName $node -ScriptBlock {
        Get-VMHost | Select-Object Name, VirtualMachinePath, VirtualHardDiskPath
    }
}
```

### 4.3 Configurare Live Migration

```powershell
# Configurare su ogni nodo
foreach ($node in $nodes) {
    Invoke-Command -ComputerName $node -ScriptBlock {
        # Abilitare Live Migration
        Enable-VMMigration

        # Configurare autenticazione Kerberos (richiede AD, piu' sicura di CredSSP)
        Set-VMMigrationNetwork 10.0.2.0 -NewSubnet 255.255.255.0

        # Impostare rete dedicata per Live Migration
        Set-VMHost -VirtualMachineMigrationAuthenticationType Kerberos

        # Performance: compressione (default) vs SMB Direct
        Set-VMHost -VirtualMachineMigrationPerformanceOption Compression

        # Numero massimo di migrazioni simultanee
        Set-VMHost -MaximumVirtualMachineMigrations 2

        # Numero massimo di storage migration simultanee
        Set-VMHost -MaximumStorageMigrations 2
    }
}

# Verificare configurazione
foreach ($node in $nodes) {
    Invoke-Command -ComputerName $node -ScriptBlock {
        Get-VMHost | Select-Object Name,
            VirtualMachineMigrationEnabled,
            VirtualMachineMigrationAuthenticationType,
            VirtualMachineMigrationPerformanceOption,
            MaximumVirtualMachineMigrations
    }
}
```

**Output atteso (per nodo):**

```
Name                                    : HV-NODE01
VirtualMachineMigrationEnabled          : True
VirtualMachineMigrationAuthenticationType : Kerberos
VirtualMachineMigrationPerformanceOption : Compression
MaximumVirtualMachineMigrations         : 2
```

> **Kerberos vs CredSSP:** Kerberos e' la scelta corretta per ambienti con AD. CredSSP richiede la delega esplicita delle credenziali e ha implicazioni di sicurezza maggiori. Con Kerberos, configurare la Constrained Delegation nel dominio:
>
> ```powershell
> # Su DC01, per ogni coppia di nodi:
> $nodeAccounts = @("HV-NODE01$", "HV-NODE02$", "HV-NODE03$")
> foreach ($source in $nodeAccounts) {
>     foreach ($target in $nodeAccounts) {
>         if ($source -ne $target) {
>             $targetObj = Get-ADComputer ($target -replace '\$$','')
>             Set-ADComputer ($source -replace '\$$','') -Add @{
>                 'msDS-AllowedToDelegateTo' = @(
>                     "Microsoft Virtual System Migration Service/$($targetObj.DNSHostName)",
>                     "cifs/$($targetObj.DNSHostName)"
>                 )
>             }
>         }
>     }
> }
> ```

### 4.4 Configurare regole di anti-affinity

```powershell
# Le regole di anti-affinity impediscono a VM critiche di risiedere sullo stesso nodo
# Creare un gruppo di anti-affinity per i DC
New-ClusterAffinityRule -Name "DC-AntiAffinity" -RuleType AntiAffinity

# Le VM verranno aggiunte a questo gruppo nella Parte 5

# Verificare le regole esistenti
Get-ClusterAffinityRule
```

### 4.5 Configurare preferred owner

```powershell
# Dopo aver creato le VM (Parte 5), impostare il nodo preferito
# Esempio: le VM di produzione preferiscono NODE01, quelle di test NODE03

# Queste configurazioni verranno applicate nella Parte 5 dopo la creazione delle VM
```

---

## Parte 5 — Deploy VM e Test di Migrazione (30 min)

### 5.1 Creare le VM di test sul cluster

```powershell
# Creare directory su CSV
New-Item -Path "C:\ClusterStorage\Volume1\VMs" -ItemType Directory -Force
New-Item -Path "C:\ClusterStorage\Volume1\VHDs" -ItemType Directory -Force

# VM 1: Web Server (su NODE01)
New-VM -Name "WEB-SRV01" `
    -MemoryStartupBytes 2GB `
    -NewVHDPath "C:\ClusterStorage\Volume1\VHDs\WEB-SRV01.vhdx" `
    -NewVHDSizeBytes 40GB `
    -Generation 2 `
    -SwitchName "Management" `
    -Path "C:\ClusterStorage\Volume1\VMs" `
    -ComputerName HV-NODE01

Set-VM -Name "WEB-SRV01" -ProcessorCount 2 -DynamicMemory -MemoryMinimumBytes 512MB -MemoryMaximumBytes 4GB -ComputerName HV-NODE01

# VM 2: Database Server (su NODE01)
New-VM -Name "DB-SRV01" `
    -MemoryStartupBytes 4GB `
    -NewVHDPath "C:\ClusterStorage\Volume1\VHDs\DB-SRV01.vhdx" `
    -NewVHDSizeBytes 80GB `
    -Generation 2 `
    -SwitchName "Management" `
    -Path "C:\ClusterStorage\Volume1\VMs" `
    -ComputerName HV-NODE01

Set-VM -Name "DB-SRV01" -ProcessorCount 4 -DynamicMemory -MemoryMinimumBytes 2GB -MemoryMaximumBytes 8GB -ComputerName HV-NODE01

# VM 3: Domain Controller di test (su NODE02)
New-VM -Name "DC-TEST01" `
    -MemoryStartupBytes 2GB `
    -NewVHDPath "C:\ClusterStorage\Volume1\VHDs\DC-TEST01.vhdx" `
    -NewVHDSizeBytes 40GB `
    -Generation 2 `
    -SwitchName "Management" `
    -Path "C:\ClusterStorage\Volume1\VMs" `
    -ComputerName HV-NODE02

# VM 4: Domain Controller di test 2 (su NODE03)
New-VM -Name "DC-TEST02" `
    -MemoryStartupBytes 2GB `
    -NewVHDPath "C:\ClusterStorage\Volume1\VHDs\DC-TEST02.vhdx" `
    -NewVHDSizeBytes 40GB `
    -Generation 2 `
    -SwitchName "Management" `
    -Path "C:\ClusterStorage\Volume1\VMs" `
    -ComputerName HV-NODE03
```

### 5.2 Registrare le VM come risorse del cluster

```powershell
# Aggiungere ogni VM come ruolo del cluster (alta disponibilita')
Add-ClusterVirtualMachineRole -VirtualMachine "WEB-SRV01"
Add-ClusterVirtualMachineRole -VirtualMachine "DB-SRV01"
Add-ClusterVirtualMachineRole -VirtualMachine "DC-TEST01"
Add-ClusterVirtualMachineRole -VirtualMachine "DC-TEST02"

# Verificare le VM nel cluster
Get-ClusterGroup | Where-Object { $_.GroupType -eq 'VirtualMachine' } |
    Format-Table Name, State, OwnerNode
```

**Output atteso:**

```
Name        State   OwnerNode
----        -----   ---------
WEB-SRV01   Off     HV-NODE01
DB-SRV01    Off     HV-NODE01
DC-TEST01   Off     HV-NODE02
DC-TEST02   Off     HV-NODE03
```

### 5.3 Applicare regole di anti-affinity e preferred owner

```powershell
# Aggiungere i DC al gruppo anti-affinity (non devono risiedere sullo stesso nodo)
Add-ClusterGroupToAffinityRule -Groups "DC-TEST01","DC-TEST02" -Name "DC-AntiAffinity"

# Configurare preferred owner per ogni VM
Set-ClusterOwnerNode -Group "WEB-SRV01"  -Owners HV-NODE01, HV-NODE02
Set-ClusterOwnerNode -Group "DB-SRV01"   -Owners HV-NODE01, HV-NODE03
Set-ClusterOwnerNode -Group "DC-TEST01"  -Owners HV-NODE02, HV-NODE01
Set-ClusterOwnerNode -Group "DC-TEST02"  -Owners HV-NODE03, HV-NODE02

# Verificare
Get-ClusterOwnerNode -Group "WEB-SRV01" | Select-Object -ExpandProperty OwnerNodes
Get-ClusterAffinityRule
```

### 5.4 Avviare le VM

```powershell
# Avviare tutte le VM del cluster
Get-ClusterGroup | Where-Object { $_.GroupType -eq 'VirtualMachine' } |
    Start-ClusterGroup

# Verificare lo stato
Get-ClusterGroup | Where-Object { $_.GroupType -eq 'VirtualMachine' } |
    Format-Table Name, State, OwnerNode
```

### 5.5 Test Live Migration

```powershell
# Live Migration: sposta la VM senza downtime (la VM resta accesa)
# Migrare WEB-SRV01 da NODE01 a NODE02
Move-ClusterVirtualMachineRole -Name "WEB-SRV01" -Node HV-NODE02 -MigrationType Live

# Misurare il tempo di migrazione
$sw = [System.Diagnostics.Stopwatch]::StartNew()
Move-ClusterVirtualMachineRole -Name "DB-SRV01" -Node HV-NODE02 -MigrationType Live
$sw.Stop()
Write-Host "Live Migration completata in: $($sw.Elapsed.TotalSeconds) secondi"

# Verificare la nuova posizione
Get-ClusterGroup | Where-Object { $_.GroupType -eq 'VirtualMachine' } |
    Format-Table Name, State, OwnerNode
```

**Output atteso:**

```
Live Migration completata in: 12.4 secondi

Name        State    OwnerNode
----        -----    ---------
WEB-SRV01   Online   HV-NODE02
DB-SRV01    Online   HV-NODE02
DC-TEST01   Online   HV-NODE02
DC-TEST02   Online   HV-NODE03
```

> **Troubleshooting Live Migration:**
> - **Errore Kerberos:** Verificare la Constrained Delegation (Parte 4.3)
> - **Timeout:** Verificare la connettivita' sulla rete LiveMigration (10.0.2.0/24)
> - **Incompatibilita' processore:** Abilitare `Set-VMProcessor -CompatibilityForMigrationEnabled $true`

### 5.6 Test Quick Migration

```powershell
# Quick Migration: salva lo stato della VM, la sposta, poi la riprende
# Comporta breve downtime ma e' piu' affidabile con grandi quantita' di RAM

Move-ClusterVirtualMachineRole -Name "WEB-SRV01" -Node HV-NODE03 -MigrationType Quick

# Verificare
Get-ClusterGroup -Name "WEB-SRV01" | Format-Table Name, State, OwnerNode
```

### 5.7 Test Storage Migration

```powershell
# Spostare una VM tra CSV (senza downtime)
Move-VMStorage -VMName "WEB-SRV01" `
    -DestinationStoragePath "C:\ClusterStorage\Volume2\VMs\WEB-SRV01" `
    -ComputerName (Get-ClusterGroup -Name "WEB-SRV01").OwnerNode

# Verificare la nuova posizione dei file
Get-VM -Name "WEB-SRV01" -ComputerName (Get-ClusterGroup -Name "WEB-SRV01").OwnerNode |
    Select-Object -ExpandProperty HardDrives |
    Select-Object Path
```

---

## Parte 6 — Test di Failover (30 min)

### 6.1 Simulare il guasto di un nodo

```powershell
# Verificare lo stato attuale
Get-ClusterNode | Format-Table Name, State
Get-ClusterGroup | Where-Object { $_.GroupType -eq 'VirtualMachine' } |
    Format-Table Name, State, OwnerNode

# Annotare quale nodo ospita quali VM
$preFailoverState = Get-ClusterGroup |
    Where-Object { $_.GroupType -eq 'VirtualMachine' } |
    Select-Object Name, OwnerNode

# Simulare il guasto di NODE02 (fermarlo in modo brusco)
Stop-ClusterNode -Name HV-NODE02 -ErrorAction SilentlyContinue

# Attendere il failover automatico (tipicamente 5-15 secondi)
Start-Sleep -Seconds 20

# Verificare lo stato post-failover
Get-ClusterNode | Format-Table Name, State
Get-ClusterGroup | Where-Object { $_.GroupType -eq 'VirtualMachine' } |
    Format-Table Name, State, OwnerNode
```

**Output atteso:**

```
Name         State
----         -----
HV-NODE01    Up
HV-NODE02    Down
HV-NODE03    Up

Name        State    OwnerNode
----        -----    ---------
WEB-SRV01   Online   HV-NODE01      ← failover automatico
DB-SRV01    Online   HV-NODE01      ← failover automatico
DC-TEST01   Online   HV-NODE01      ← failover automatico da NODE02
DC-TEST02   Online   HV-NODE03      ← invariato
```

> Le VM che erano su NODE02 sono state spostate automaticamente sui nodi rimanenti secondo le regole di preferred owner e anti-affinity.

### 6.2 Ripristinare il nodo e verificare failback

```powershell
# Riavviare NODE02
Start-ClusterNode -Name HV-NODE02

# Verificare che il nodo rientri nel cluster
Get-ClusterNode | Format-Table Name, State

# Output atteso: tutti e 3 i nodi = Up
# Le VM NON tornano automaticamente al nodo originale (default: no auto-failback)
```

### 6.3 Test Drain Roles (manutenzione pianificata)

```powershell
# Scenario: manutenzione su NODE01 — spostare tutte le VM altrove

# Mettere il nodo in pausa con drain
Suspend-ClusterNode -Name HV-NODE01 -Drain -Wait

# Verificare che tutte le VM siano migrate
Get-ClusterGroup | Where-Object { $_.GroupType -eq 'VirtualMachine' } |
    Format-Table Name, State, OwnerNode

# NODE01 deve essere in stato Paused
Get-ClusterNode -Name HV-NODE01 | Select-Object Name, State, DrainStatus
```

**Output atteso:**

```
Name       State   DrainStatus
----       -----   -----------
HV-NODE01  Paused  Completed
```

```powershell
# Dopo la manutenzione, ripristinare il nodo
Resume-ClusterNode -Name HV-NODE01

# Opzionalmente, riportare le VM sul nodo preferito
Get-ClusterGroup | Where-Object { $_.GroupType -eq 'VirtualMachine' } |
    ForEach-Object {
        $preferredOwner = (Get-ClusterOwnerNode -Group $_.Name).OwnerNodes | Select-Object -First 1
        if ($preferredOwner -and $_.OwnerNode -ne $preferredOwner.Name) {
            Move-ClusterVirtualMachineRole -Name $_.Name -Node $preferredOwner.Name -MigrationType Live
            Write-Host "Spostata $($_.Name) su $($preferredOwner.Name)"
        }
    }
```

### 6.4 Test Cluster-Aware Updating (CAU)

```powershell
# Installare il ruolo CAU (se non gia' presente)
Add-CauClusterRole -ClusterName HV-CLUSTER -Force `
    -DaysOfWeek Tuesday `
    -IntervalWeeks 2 `
    -MaxRetriesPerNode 3 `
    -RequireAllNodesOnline

# Verificare la configurazione
Get-CauClusterRole -ClusterName HV-CLUSTER

# Eseguire un test manuale di CAU (non installa aggiornamenti, solo simulazione)
Test-CauSetup -ClusterName HV-CLUSTER

# Avviare un run CAU manuale
Invoke-CauRun -ClusterName HV-CLUSTER -Force -MaxRetriesPerNode 2

# Monitorare il progresso
Get-CauRun -ClusterName HV-CLUSTER | Format-Table NodeName, NodeStatus, CurrentActivity
```

**Output atteso (Get-CauRun):**

```
NodeName     NodeStatus  CurrentActivity
--------     ----------  ---------------
HV-NODE01    Waiting     Waiting to be updated
HV-NODE02    InProgress  Installing updates
HV-NODE03    Completed   Successfully updated
```

> **Comportamento CAU:** Aggiorna un nodo alla volta. Per ogni nodo:
> 1. Drain delle VM (Live Migration verso altri nodi)
> 2. Installa aggiornamenti
> 3. Riavvia se necessario
> 4. Resume del nodo
> 5. Passa al nodo successivo

---

## Parte 7 — Hyper-V Replica verso Sito Secondario (30 min)

### 7.1 Preparare il server replica (HV-REPLICA01)

```powershell
# Su HV-REPLICA01 (stand-alone, sito 2):
# Installare Hyper-V
Install-WindowsFeature Hyper-V -IncludeManagementTools -Restart

# Dopo il riavvio, abilitare Hyper-V Replica come server di destinazione
Set-VMReplicationServer -ReplicationEnabled $true `
    -AllowedAuthenticationType Kerberos `
    -ReplicationAllowedFromAnyServer $false `
    -DefaultStorageLocation "D:\Replicas"

# Autorizzare il cluster come sorgente
New-VMReplicationAuthorizationEntry -AllowedPrimaryServer "*.lab.local" `
    -ReplicaStorageLocation "D:\Replicas" `
    -TrustGroup "lab-cluster"

# Verificare configurazione
Get-VMReplicationServer
```

**Output atteso:**

```
RepEnabled AllowedAuth     DefaultStoreLoc
---------- -----------     ---------------
True       Kerberos        D:\Replicas
```

### 7.2 Configurare il firewall per la replica

```powershell
# Su HV-REPLICA01:
Enable-NetFirewallRule -DisplayName "Hyper-V Replica HTTP Listener (TCP-In)"

# Se si usa HTTPS (raccomandato per WAN):
# Enable-NetFirewallRule -DisplayName "Hyper-V Replica HTTPS Listener (TCP-In)"

# Verificare
Get-NetFirewallRule -DisplayName "*Hyper-V Replica*" |
    Select-Object DisplayName, Enabled, Direction
```

### 7.3 Abilitare la replica per una VM del cluster

```powershell
# Abilitare la replica per WEB-SRV01 (da un nodo del cluster)
$vmOwner = (Get-ClusterGroup -Name "WEB-SRV01").OwnerNode

Enable-VMReplication -VMName "WEB-SRV01" `
    -ReplicaServerName "HV-REPLICA01.lab.local" `
    -ReplicaServerPort 80 `
    -AuthenticationType Kerberos `
    -RecoveryHistory 4 `
    -ReplicationFrequencySec 300 `
    -ComputerName $vmOwner

# Avviare la replica iniziale
Start-VMInitialReplication -VMName "WEB-SRV01" -ComputerName $vmOwner

# Monitorare il progresso della replica iniziale
Measure-VMReplication -VMName "WEB-SRV01" -ComputerName $vmOwner |
    Select-Object VMName, State, Health, PrimaryServerName, ReplicaServerName,
        LastReplicationTime, ReplicationFrequencySec
```

**Output atteso:**

```
VMName           : WEB-SRV01
State            : Replicating
Health           : Normal
PrimaryServerName: HV-NODE01
ReplicaServerName: HV-REPLICA01.lab.local
LastReplicationTime : 2026-05-23 15:30:00
ReplicationFrequencySec : 300
```

### 7.4 Configurare RPO e monitoraggio

```powershell
# Impostare RPO target: 15 minuti
Set-VMReplication -VMName "WEB-SRV01" `
    -ReplicationFrequencySec 300 `
    -RecoveryHistory 12 `
    -ComputerName $vmOwner

# Verificare stato della replica
Get-VMReplication -ComputerName $vmOwner |
    Format-Table VMName, State, Health, FrequencySec, LastReplicationTime
```

### 7.5 Test failover (non distruttivo)

```powershell
# Test failover: crea una VM di test sul server replica
# La VM primaria NON viene interrotta
Start-VMFailover -VMName "WEB-SRV01" -AsTest -ComputerName HV-REPLICA01

# Verificare la VM di test sul server replica
Get-VM -ComputerName HV-REPLICA01 | Format-Table Name, State

# Output atteso: "WEB-SRV01 - Test" in stato Off

# Avviare la VM di test per verifica
Start-VM -Name "WEB-SRV01 - Test" -ComputerName HV-REPLICA01

# Dopo il test, rimuovere la VM di test
Stop-VMFailover -VMName "WEB-SRV01" -ComputerName HV-REPLICA01
```

### 7.6 Planned failover (migrazione pianificata)

```powershell
# Planned failover: migrazione ordinata al sito secondario
# Richiede la VM primaria spenta o in pausa

# 1. Fermare la VM primaria
Stop-VM -Name "WEB-SRV01" -ComputerName $vmOwner

# 2. Eseguire il planned failover
Start-VMFailover -VMName "WEB-SRV01" -Prepare -ComputerName $vmOwner
Start-VMFailover -VMName "WEB-SRV01" -ComputerName HV-REPLICA01

# 3. Completare il failover
Complete-VMFailover -VMName "WEB-SRV01" -ComputerName HV-REPLICA01

# 4. Avviare la VM sul sito replica
Start-VM -Name "WEB-SRV01" -ComputerName HV-REPLICA01

# 5. Invertire la direzione della replica (per il failback futuro)
Set-VMReplication -VMName "WEB-SRV01" -Reverse -ComputerName HV-REPLICA01
```

> **Test failover vs Planned failover:**
> - **Test failover:** Non distruttivo. Crea una copia temporanea sul sito replica. La VM primaria continua a funzionare. Usare per verifiche periodiche.
> - **Planned failover:** Migrazione completa al sito secondario. La VM primaria si ferma, tutti i dati vengono sincronizzati, la VM parte sul replica. Usare per manutenzione programmata del sito primario o migrazione permanente.

---

## Parte 8 — Monitoraggio e Verifica Finale (30 min)

### 8.1 Stato complessivo del cluster

```powershell
# Nodi del cluster
Get-ClusterNode | Format-Table Name, State, NodeWeight, DynamicWeight

# Gruppi del cluster (VM)
Get-ClusterGroup | Format-Table Name, GroupType, State, OwnerNode, Priority

# Reti del cluster
Get-ClusterNetwork | Format-Table Name, State, Role, Address

# Risorse del cluster
Get-ClusterResource | Format-Table Name, ResourceType, State, OwnerNode
```

**Output atteso (Get-ClusterNetwork):**

```
Name              State  Role            Address
----              -----  ----            -------
Management        Up     ClusterAndClient 10.0.1.0/24
Live Migration    Up     None             10.0.2.0/24
Cluster           Up     Cluster          10.0.3.0/24
Storage           Up     None             10.0.4.0/24
```

### 8.2 Analisi Event Log del cluster

```powershell
# Eventi recenti del cluster (ultimi 30 minuti)
$since = (Get-Date).AddMinutes(-30)

Get-WinEvent -LogName "Microsoft-Windows-FailoverClustering/Operational" `
    -MaxEvents 50 |
    Where-Object { $_.TimeCreated -gt $since } |
    Format-Table TimeCreated, Id, LevelDisplayName, Message -Wrap

# Filtrare solo errori e warning
Get-WinEvent -LogName "Microsoft-Windows-FailoverClustering/Operational" `
    -MaxEvents 100 |
    Where-Object { $_.Level -le 3 } |
    Format-Table TimeCreated, Id, LevelDisplayName, Message -Wrap
```

> **Event ID importanti:**
> - **1069:** Risorsa cluster offline
> - **1146:** Nodo rimosso dal cluster
> - **1177:** Quorum perso
> - **1205:** Nodo aggiunto
> - **1641:** Live Migration completata
> - **21502:** VM migrata con successo

### 8.3 Performance monitoring con contatori cluster

```powershell
# Contatori performance del cluster
$counters = @(
    "\Cluster CSV File System(*)\IO Reads/sec",
    "\Cluster CSV File System(*)\IO Writes/sec",
    "\Cluster CSV File System(*)\Read Latency",
    "\Cluster CSV File System(*)\Write Latency",
    "\Hyper-V Virtual Machine Health Summary\Health Ok",
    "\Hyper-V Virtual Machine Health Summary\Health Critical"
)

# Raccogliere un campione di 10 secondi
Get-Counter -Counter $counters -SampleInterval 2 -MaxSamples 5 |
    ForEach-Object {
        $_.CounterSamples | Format-Table Path, CookedValue
    }
```

### 8.4 Script di health check completo

```powershell
# Salvare come C:\Scripts\Cluster-HealthCheck.ps1
$ErrorActionPreference = 'Continue'
$results = @()

Write-Host "=== CLUSTER HEALTH CHECK ===" -ForegroundColor Cyan
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host ""

# 1. Nodi
Write-Host "--- NODI ---" -ForegroundColor Yellow
$nodeStatus = Get-ClusterNode
$nodeStatus | Format-Table Name, State, NodeWeight
$allNodesUp = ($nodeStatus | Where-Object State -ne "Up").Count -eq 0
$results += [PSCustomObject]@{Check="Tutti i nodi Up"; Result=if($allNodesUp){"PASS"}else{"FAIL"}}

# 2. Quorum
Write-Host "--- QUORUM ---" -ForegroundColor Yellow
$quorum = Get-ClusterQuorum
Write-Host "Tipo: $($quorum.QuorumType)"
Write-Host "Risorsa: $($quorum.QuorumResource)"
$results += [PSCustomObject]@{Check="Quorum configurato"; Result=if($quorum.QuorumType){"PASS"}else{"FAIL"}}

# 3. CSV
Write-Host "--- CLUSTER SHARED VOLUMES ---" -ForegroundColor Yellow
$csvStatus = Get-ClusterSharedVolume
$csvStatus | Select-Object Name, State, OwnerNode | Format-Table
$allCsvOnline = ($csvStatus | Where-Object State -ne "Online").Count -eq 0
$results += [PSCustomObject]@{Check="Tutti i CSV Online"; Result=if($allCsvOnline){"PASS"}else{"FAIL"}}

# 4. VM
Write-Host "--- VIRTUAL MACHINES ---" -ForegroundColor Yellow
$vmGroups = Get-ClusterGroup | Where-Object GroupType -eq "VirtualMachine"
$vmGroups | Format-Table Name, State, OwnerNode
$allVmOnline = ($vmGroups | Where-Object State -ne "Online").Count -eq 0
$results += [PSCustomObject]@{Check="Tutte le VM Online"; Result=if($allVmOnline){"PASS"}else{"FAIL"}}

# 5. Reti
Write-Host "--- RETI CLUSTER ---" -ForegroundColor Yellow
$netStatus = Get-ClusterNetwork
$netStatus | Format-Table Name, State, Role
$allNetsUp = ($netStatus | Where-Object State -ne "Up").Count -eq 0
$results += [PSCustomObject]@{Check="Tutte le reti Up"; Result=if($allNetsUp){"PASS"}else{"FAIL"}}

# 6. Replica (se configurata)
Write-Host "--- HYPER-V REPLICA ---" -ForegroundColor Yellow
$replicaStatus = Get-VMReplication -ErrorAction SilentlyContinue
if ($replicaStatus) {
    $replicaStatus | Format-Table VMName, State, Health, LastReplicationTime
    $replicaHealthy = ($replicaStatus | Where-Object Health -ne "Normal").Count -eq 0
    $results += [PSCustomObject]@{Check="Replica Health Normal"; Result=if($replicaHealthy){"PASS"}else{"WARN"}}
} else {
    Write-Host "Nessuna replica configurata"
}

# Riepilogo
Write-Host ""
Write-Host "=== RIEPILOGO ===" -ForegroundColor Cyan
$results | Format-Table Check, Result
$failCount = ($results | Where-Object Result -eq "FAIL").Count
if ($failCount -eq 0) {
    Write-Host "CLUSTER HEALTHY" -ForegroundColor Green
} else {
    Write-Host "ATTENZIONE: $failCount check falliti" -ForegroundColor Red
}
```

### 8.5 Verifica finale: checklist operativa

```
================================================================
     CHECKLIST VERIFICA CLUSTER HYPER-V
================================================================

INFRASTRUTTURA
[  ] 3 nodi online e nel cluster
[  ] 4 reti cluster configurate (Management, LiveMigration, Cluster, Storage)
[  ] Quorum configurato con witness
[  ] DNS del cluster risolve correttamente

STORAGE
[  ] LUN iSCSI connesse da tutti i nodi
[  ] CSV online e accessibili
[  ] Storage QoS policy applicate

HYPER-V
[  ] Live Migration funzionante (Kerberos)
[  ] Quick Migration funzionante
[  ] Storage Migration funzionante
[  ] Anti-affinity rules applicate
[  ] Preferred owner configurato

FAILOVER
[  ] Failover automatico testato (Stop-ClusterNode)
[  ] Drain node testato (Suspend-ClusterNode -Drain)
[  ] CAU configurato e testato
[  ] Tempo di failover entro i target

REPLICA
[  ] Hyper-V Replica attiva
[  ] Test failover eseguito con successo
[  ] Planned failover testato
[  ] RPO verificato (< 15 min)

MONITORAGGIO
[  ] Event log cluster senza errori critici
[  ] Performance counters entro soglie
[  ] Health check script funzionante
================================================================
```

---

## Risorse

| Risorsa | URL |
|---------|-----|
| Failover Clustering Overview | https://learn.microsoft.com/en-us/windows-server/failover-clustering/failover-clustering-overview |
| Hyper-V on Windows Server | https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/hyper-v-on-windows-server |
| Cluster Shared Volumes | https://learn.microsoft.com/en-us/windows-server/failover-clustering/failover-cluster-csvs |
| Hyper-V Live Migration | https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/manage/live-migration-overview |
| Hyper-V Replica | https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/manage/set-up-hyper-v-replica |
| Cluster-Aware Updating | https://learn.microsoft.com/en-us/windows-server/failover-clustering/cluster-aware-updating |
| Test-Cluster cmdlet | https://learn.microsoft.com/en-us/powershell/module/failoverclusters/test-cluster |
| Cluster Quorum | https://learn.microsoft.com/en-us/windows-server/failover-clustering/manage-cluster-quorum |
