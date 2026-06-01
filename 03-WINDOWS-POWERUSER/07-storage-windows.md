# Storage Windows — Guida Completa

> **Modulo 07** · **Aggiornamento:** 2026-05-22

> **Modulo del corso:** Amministrazione Windows enterprise
> **Prerequisiti:** [Rete Windows](06-rete-windows.md) · [Permessi e Accesso](08-permessi-e-accesso.md) · [PowerShell](02-powershell.md)
> **Obiettivi di apprendimento:**
> 1. Progettare e configurare Storage Spaces e Storage Spaces Direct per ambienti server
> 2. Gestire dischi, volumi e file system (NTFS, ReFS, GPT vs MBR) con GUI e PowerShell
> 3. Implementare DFS Namespace e DFS Replication per la condivisione distribuita dei dati
> 4. Configurare target iSCSI e connessioni initiator in scenari SAN
> 5. Abilitare e gestire la deduplicazione dati per ottimizzare lo spazio su disco
> **Tempo stimato:** lettura 80 min · lab 60 min
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-23

## Idee guida
1. **Storage Spaces Direct (S2D) per HCI.**
2. **ReFS > NTFS per dataset > 16TB.** Block cloning, integrity streams.
3. **Deduplication via `Enable-DedupVolume`.**
4. **SMB 3.x con encryption + signing.**
5. **GPT obbligatorio per qualsiasi nuovo disco** — MBR rimane solo per compatibilità legacy.
6. **Separare sempre OS da dati** — volumi distinti per sistema operativo, applicazioni, database, log.
7. **Monitoraggio proattivo** — allarmi prima che lo spazio finisca, non dopo.


## Indice

- [Panoramica](#panoramica)
- [Gestione Dischi e Volumi](#gestione-dischi-e-volumi)
  - [MBR vs GPT](#mbr-vs-gpt)
  - [Dischi Base vs Dischi Dinamici](#dischi-base-vs-dischi-dinamici)
  - [Disk Management GUI](#disk-management-gui)
  - [diskpart — Gestione da Linea di Comando](#diskpart--gestione-da-linea-di-comando)
  - [PowerShell — Gestione Dischi e Partizioni](#powershell--gestione-dischi-e-partizioni)
- [NTFS — Deep Dive](#ntfs--deep-dive)
  - [Architettura MFT](#architettura-mft)
  - [Attributi dei File NTFS](#attributi-dei-file-ntfs)
  - [Compressione NTFS](#compressione-ntfs)
  - [Crittografia EFS](#crittografia-efs)
  - [Hard Link](#hard-link)
  - [Symbolic Link](#symbolic-link)
  - [Junction Point](#junction-point)
  - [Alternate Data Streams (ADS)](#alternate-data-streams-ads)
- [ReFS — Resilient File System](#refs--resilient-file-system)
  - [Architettura ReFS](#architettura-refs)
  - [Confronto NTFS vs ReFS](#confronto-ntfs-vs-refs)
  - [Casi d'uso e Limitazioni](#casi-duso-e-limitazioni)
- [Storage Spaces](#storage-spaces)
  - [Fondamenti e Gerarchia](#fondamenti-e-gerarchia)
  - [Tipi di Resilienza](#tipi-di-resilienza)
  - [Thin Provisioning](#thin-provisioning)
  - [Tiered Storage](#tiered-storage)
  - [Configurazione Completa](#configurazione-completa)
- [Storage Spaces Direct (S2D)](#storage-spaces-direct-s2d)
  - [Architettura S2D](#architettura-s2d)
  - [Requisiti Hardware e Software](#requisiti-hardware-e-software)
  - [Deployment S2D](#deployment-s2d)
  - [Monitoraggio e Manutenzione S2D](#monitoraggio-e-manutenzione-s2d)
- [iSCSI](#iscsi)
  - [iSCSI Target](#iscsi-target-server-che-espone-lun)
  - [iSCSI Initiator](#iscsi-initiator-client-che-connette-lun)
  - [MPIO — Multipath I/O](#mpio--multipath-io)
  - [Autenticazione CHAP](#autenticazione-chap)
- [Fibre Channel](#fibre-channel)
  - [Configurazione HBA](#configurazione-hba)
  - [Zoning e LUN Mapping](#zoning-e-lun-mapping)
- [SMB File Share](#smb-file-share)
  - [NTFS vs Share Permissions](#ntfs-vs-share-permissions)
  - [Access Based Enumeration (ABE)](#access-based-enumeration-abe)
  - [SMB 3.x — Funzionalità Avanzate](#smb-3x--funzionalità-avanzate)
- [DFS — Distributed File System](#dfs--distributed-file-system)
  - [DFS Namespaces](#dfs-namespaces)
  - [DFS Replication](#dfs-replication)
  - [Troubleshooting DFS](#troubleshooting-dfs)
- [Deduplicazione Dati](#deduplicazione-dati)
  - [Configurazione Deduplicazione](#configurazione-deduplicazione)
  - [Impostazioni per Workload](#impostazioni-per-workload)
  - [Monitoraggio e Ottimizzazione](#monitoraggio-e-ottimizzazione-dedup)
- [Data Tiering e SSD Caching](#data-tiering-e-ssd-caching)
- [Storage Monitoring](#storage-monitoring)
  - [Performance Monitor — Contatori Storage](#performance-monitor--contatori-storage)
  - [Storage Reports e FSRM](#storage-reports-e-fsrm)
  - [Get-StorageHealth e Diagnostica](#get-storagehealth-e-diagnostica)
- [Disk Quotas](#disk-quotas)
  - [Quote NTFS Native](#quote-ntfs-native)
  - [Quote FSRM](#quote-fsrm)
  - [Soft vs Hard Limits](#soft-vs-hard-limits)
- [Backup Storage](#backup-storage)
  - [Windows Server Backup](#windows-server-backup)
  - [Azure Backup Integration](#azure-backup-integration)
- [PowerShell Storage Cmdlets — Riferimento](#powershell-storage-cmdlets--riferimento)
- [Storage Migration Service](#storage-migration-service)
- [Best Practices](#best-practices)
- [Storage Design Checklist](#storage-design-checklist)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)

---

## Panoramica

Windows Server offre un ecosistema storage completo: dalla gestione base dei dischi a soluzioni software-defined come Storage Spaces e S2D. NTFS rimane il filesystem principale, affiancato da ReFS per workload specifici. Deduplicazione, iSCSI e Storage Migration completano il quadro per scenari enterprise.

Lo stack storage di Windows si articola su più livelli:

```
┌──────────────────────────────────────────────────────────────┐
│                    Applicazioni / VM                         │
├──────────────────────────────────────────────────────────────┤
│ File System:  NTFS │ ReFS │ CSVFS_NTFS │ CSVFS_ReFS         │
├──────────────────────────────────────────────────────────────┤
│ Volumi / Partizioni  │  Disk Quotas  │  Deduplicazione      │
├──────────────────────────────────────────────────────────────┤
│ Storage Spaces / S2D │ Dischi Dinamici │ RAID Hardware       │
├──────────────────────────────────────────────────────────────┤
│ Protocolli:  SMB 3.x  │  iSCSI  │  Fibre Channel  │  NVMe  │
├──────────────────────────────────────────────────────────────┤
│ Trasporto: Ethernet │ RDMA (RoCE/iWARP) │ FC │ SAS │ NVMe   │
├──────────────────────────────────────────────────────────────┤
│ Hardware: HDD │ SSD SATA │ SSD NVMe │ Persistent Memory     │
└──────────────────────────────────────────────────────────────┘
```

Componenti chiave:
- **Gestione Dischi** — MBR/GPT, partizioni, volumi, disk management/diskpart/PowerShell
- **File System** — NTFS (MFT, compressione, EFS, link) e ReFS (integrità, block cloning)
- **Storage Spaces** — Pool software-defined con resilienza (mirror, parity)
- **S2D** — Hyper-converged infrastructure con dischi locali distribuiti
- **Protocolli** — iSCSI, Fibre Channel, SMB 3.x con encryption
- **DFS** — Namespace unificato e replica distribuita
- **Deduplicazione** — Riduzione spazio per file server e backup
- **Monitoraggio** — Performance Monitor, FSRM, health cmdlets

---

## Gestione Dischi e Volumi

### MBR vs GPT

```
┌──────────────────────────────┬──────────────────────────────────┐
│          MBR                 │            GPT                   │
│   (Master Boot Record)       │  (GUID Partition Table)          │
├──────────────────────────────┼──────────────────────────────────┤
│ Max 4 partizioni primarie    │ Max 128 partizioni (Windows)     │
│ (o 3 primarie + 1 estesa)   │ Tutte primarie                   │
├──────────────────────────────┼──────────────────────────────────┤
│ Max 2 TB per disco           │ Max 18 EB (exabyte)              │
├──────────────────────────────┼──────────────────────────────────┤
│ Boot: solo BIOS (CSM)       │ Boot: UEFI nativo                │
├──────────────────────────────┼──────────────────────────────────┤
│ Partition table in settore 0 │ Partition table con backup       │
│ (nessun backup)             │ alla fine del disco               │
├──────────────────────────────┼──────────────────────────────────┤
│ Nessun checksum             │ CRC32 su header e partition table │
├──────────────────────────────┼──────────────────────────────────┤
│ Compatibilità: tutti i SO   │ Compatibilità: SO moderni (Vista+│
│ inclusi legacy              │ Server 2008+, Linux 2.6+)        │
├──────────────────────────────┼──────────────────────────────────┤
│ Settore boot: 512 byte MBR  │ Protective MBR + ESP (EFI System │
│ con codice bootstrap        │ Partition) per bootloader         │
└──────────────────────────────┴──────────────────────────────────┘
```

**Regola:** usare GPT per qualsiasi disco nuovo. MBR solo se imposto da hardware o SO legacy.

Struttura interna GPT:
- **LBA 0** — Protective MBR (compatibilità con strumenti legacy)
- **LBA 1** — Header GPT primario (contiene GUID del disco, posizione partition table, CRC32)
- **LBA 2-33** — Partition Entry Array (128 entry, 128 byte ciascuna)
- **LBA -33 to -2** — Backup Partition Entry Array
- **LBA -1** — Backup GPT Header

```powershell
# Verificare stile partizione di tutti i dischi
Get-Disk | Select-Object Number, FriendlyName, PartitionStyle, Size, OperationalStatus

# Convertire MBR → GPT (disco VUOTO, distrugge tutti i dati)
Set-Disk -Number 1 -PartitionStyle GPT

# Convertire MBR → GPT senza perdita dati (Windows 10 1703+ / Server 2019+)
# Solo per disco di sistema — utilizzare il tool mbr2gpt:
# mbr2gpt /validate /disk:0
# mbr2gpt /convert /disk:0   # eseguire da WinPE o fase preboot
```

### Dischi Base vs Dischi Dinamici

```
┌──────────────────────────────┬──────────────────────────────────┐
│       Disco Base             │        Disco Dinamico            │
├──────────────────────────────┼──────────────────────────────────┤
│ Partizioni primarie/estese   │ Volumi (simple, spanned,         │
│                              │ striped, mirrored, RAID-5)       │
├──────────────────────────────┼──────────────────────────────────┤
│ Gestito da partition table   │ Gestito da LDM database          │
│ (MBR o GPT)                 │ (ultimo 1 MB del disco)           │
├──────────────────────────────┼──────────────────────────────────┤
│ Boot supportato              │ Boot supportato (con limitazioni)│
├──────────────────────────────┼──────────────────────────────────┤
│ Compatibile con tutti i SO   │ Solo Windows (no dual-boot Linux)│
├──────────────────────────────┼──────────────────────────────────┤
│ Non supporta spanning o      │ Supporta spanning/striping/      │
│ striping tra dischi          │ mirroring tra dischi dinamici     │
├──────────────────────────────┼──────────────────────────────────┤
│ Consigliato per:             │ Consigliato per:                 │
│ - Boot disk                  │ - Legacy: spanning/mirroring     │
│ - Qualsiasi uso moderno      │ - Nota: Storage Spaces è la      │
│ - Server e workstation       │   sostituzione moderna           │
└──────────────────────────────┴──────────────────────────────────┘
```

**Nota:** Microsoft sconsiglia i dischi dinamici nelle installazioni moderne. Storage Spaces fornisce funzionalità equivalenti (mirroring, spanning) con gestione migliore. I dischi dinamici rimangono per retrocompatibilità.

Tipi di volumi su disco dinamico:

| Tipo | Descrizione | Dischi minimi | Equivalente RAID |
|------|-------------|---------------|------------------|
| Simple | Volume singolo su un disco | 1 | — |
| Spanned | Concatenazione di più dischi | 2 | JBOD |
| Striped | Striping I/O su più dischi | 2 | RAID 0 |
| Mirrored | Copia su 2 dischi | 2 | RAID 1 |
| RAID-5 | Striping + parità distribuita | 3 | RAID 5 |

```powershell
# Conversione da base a dinamico (irreversibile senza perdita dati)
# ATTENZIONE: operazione a senso unico
Convert-Disk -Number 1 -DynamicDisk   # non esiste come cmdlet nativo
# Usare Disk Management GUI o diskpart: "convert dynamic"

# Verificare tipo disco
Get-Disk | Select-Object Number, FriendlyName, PartitionStyle, @{
    Name='Type'; Expression={if($_.IsClustered){'Clustered'}elseif($_.IsSystem){'System'}else{'Standard'}}
}
```

### Disk Management GUI

Disk Management (`diskmgmt.msc`) è lo strumento grafico nativo per la gestione storage:

```
Operazioni disponibili:
├── Dischi
│   ├── Inizializzazione (MBR/GPT)
│   ├── Online / Offline
│   ├── Conversione Base ↔ Dinamico
│   ├── Proprietà disco
│   └── Rescan dischi
├── Volumi / Partizioni
│   ├── Creazione partizione (primaria, estesa, logica)
│   ├── Formattazione (NTFS, ReFS, exFAT, FAT32)
│   ├── Assegnazione lettera / mount point
│   ├── Estensione volume
│   ├── Riduzione volume (shrink)
│   ├── Eliminazione volume
│   └── Proprietà volume (quota, shadow copy, sicurezza)
├── Dischi Dinamici (legacy)
│   ├── Creazione volumi simple/spanned/striped/mirrored/RAID-5
│   ├── Riparazione mirror
│   └── Rimozione mirror
└── VHD / VHDX
    ├── Creazione VHD
    ├── Attach / Detach VHD
    └── Compattazione / Espansione VHD
```

Accesso rapido:
- `Win+X` → Disk Management
- `diskmgmt.msc` da Run o PowerShell
- `compmgmt.msc` → Storage → Disk Management
- Server Manager → File and Storage Services → Volumes → Disks

### diskpart — Gestione da Linea di Comando

`diskpart` è lo strumento CLI legacy per la gestione dischi. Richiede privilegi elevati.

```cmd
:: Avviare diskpart
diskpart

:: Elencare dischi
list disk

:: Selezionare disco
select disk 1

:: Mostrare dettagli disco selezionato
detail disk

:: Elencare partizioni del disco selezionato
list partition

:: Inizializzare disco come GPT
clean               :: ATTENZIONE: cancella tutto il disco
convert gpt

:: Creare partizione primaria
create partition primary size=102400    :: 100 GB
:: Oppure con tutto lo spazio disponibile:
create partition primary

:: Formattare
format fs=ntfs label="Data" quick unit=65536   :: 64K allocation unit

:: Assegnare lettera
assign letter=D

:: Mount point (senza lettera)
assign mount="C:\Mounts\Data"

:: Estendere partizione
select volume 2
extend size=51200    :: Estendi di 50 GB

:: Ridurre partizione
select volume 2
shrink desired=51200 minimum=10240   :: Riduci di 50 GB, minimo 10 GB

:: Disco offline / online
select disk 1
offline disk
online disk
attributes disk clear readonly

:: Convertire MBR ↔ GPT (disco vuoto)
select disk 1
clean
convert gpt
:: convert mbr    :: per tornare a MBR

:: Lavorare con VHD
create vdisk file="C:\VMs\disk01.vhdx" maximum=200000 type=expandable
select vdisk file="C:\VMs\disk01.vhdx"
attach vdisk
create partition primary
format fs=ntfs label="VHD-Data" quick
assign letter=V
detach vdisk

:: Pulire disco completamente (zero-fill)
select disk 1
clean all    :: ATTENZIONE: sovrascrive ogni settore con zeri

:: Uscire
exit
```

Comandi diskpart per SAN:
```cmd
:: Configurare policy SAN (per dischi SAN/iSCSI)
diskpart
san                          :: Mostra policy corrente
san policy=OnlineAll         :: Porta online automaticamente tutti i dischi
san policy=OfflineShared     :: Default: offline per dischi condivisi (cluster)
san policy=OfflineInternal   :: Offline per dischi interni (raro)
```

### PowerShell — Gestione Dischi e Partizioni

```powershell
# ═══════════════════════════════════════════════════════════
# ELENCARE DISCHI E INFORMAZIONI
# ═══════════════════════════════════════════════════════════

# Tutti i dischi
Get-Disk | Select-Object Number, FriendlyName, Size, PartitionStyle,
    OperationalStatus, HealthStatus, BusType, MediaType

# Disco specifico con dettagli
Get-Disk -Number 1 | Format-List *

# Dischi fisici (per Storage Spaces)
Get-PhysicalDisk | Select-Object FriendlyName, Size, MediaType, BusType,
    HealthStatus, OperationalStatus, Usage, CanPool

# ═══════════════════════════════════════════════════════════
# INIZIALIZZAZIONE E PARTIZIONI
# ═══════════════════════════════════════════════════════════

# Inizializzare disco nuovo
Initialize-Disk -Number 1 -PartitionStyle GPT

# Creare partizione con lettera
New-Partition -DiskNumber 1 -UseMaximumSize -DriveLetter D

# Creare partizione con dimensione specifica
New-Partition -DiskNumber 1 -Size 100GB -DriveLetter E

# Partizione senza lettera (mount point)
New-Partition -DiskNumber 1 -UseMaximumSize
Add-PartitionAccessPath -DiskNumber 1 -PartitionNumber 2 -AccessPath "C:\Mounts\Data"

# ═══════════════════════════════════════════════════════════
# FORMATTAZIONE
# ═══════════════════════════════════════════════════════════

# NTFS con allocation unit 4K (default, uso generale)
Format-Volume -DriveLetter D -FileSystem NTFS -NewFileSystemLabel "Data"

# NTFS con allocation unit 64K (SQL Server, I/O grossi)
Format-Volume -DriveLetter D -FileSystem NTFS -NewFileSystemLabel "SQL-Data" `
    -AllocationUnitSize 65536

# ReFS (solo Server)
Format-Volume -DriveLetter E -FileSystem ReFS -NewFileSystemLabel "ReFS-Data"

# Formattazione completa (non quick, verifica settori)
Format-Volume -DriveLetter D -FileSystem NTFS -NewFileSystemLabel "Data" -Full

# ═══════════════════════════════════════════════════════════
# RIDIMENSIONAMENTO
# ═══════════════════════════════════════════════════════════

# Estendere partizione al massimo
$maxSize = (Get-PartitionSupportedSize -DriveLetter D).SizeMax
Resize-Partition -DriveLetter D -Size $maxSize

# Ridurre partizione
$minSize = (Get-PartitionSupportedSize -DriveLetter D).SizeMin
Resize-Partition -DriveLetter D -Size ($minSize + 50GB)

# ═══════════════════════════════════════════════════════════
# VOLUMI E STATO
# ═══════════════════════════════════════════════════════════

# Elencare volumi
Get-Volume | Select-Object DriveLetter, FileSystemLabel, FileSystem,
    Size, SizeRemaining, HealthStatus

# Elencare partizioni
Get-Partition | Select-Object DiskNumber, PartitionNumber, DriveLetter,
    Size, Type, IsSystem, IsBoot

# Disco offline/online
Set-Disk -Number 1 -IsOffline $false
Set-Disk -Number 1 -IsReadOnly $false

# Conversione MBR ↔ GPT (disco vuoto)
Set-Disk -Number 1 -PartitionStyle GPT

# ═══════════════════════════════════════════════════════════
# PIPELINE: DISCO NUOVO IN UN COMANDO
# ═══════════════════════════════════════════════════════════

# Inizializza + partiziona + formatta in pipeline
Get-Disk -Number 1 | Initialize-Disk -PartitionStyle GPT -PassThru |
    New-Partition -UseMaximumSize -DriveLetter D |
    Format-Volume -FileSystem NTFS -NewFileSystemLabel "Data" -AllocationUnitSize 4096
```

---

## NTFS — Deep Dive

### Architettura MFT

La **Master File Table (MFT)** è la struttura dati centrale di NTFS. Ogni file e directory sul volume ha almeno un record nella MFT.

```
Struttura MFT:
┌──────────────────────────────────────────────────────────┐
│ MFT Record 0:  $MFT          (la MFT stessa)            │
│ MFT Record 1:  $MFTMirr      (backup dei primi 4 record)│
│ MFT Record 2:  $LogFile      (journal delle transazioni) │
│ MFT Record 3:  $Volume       (info volume: label, ver.)  │
│ MFT Record 4:  $AttrDef      (definizioni attributi)     │
│ MFT Record 5:  . (root dir)  (directory radice)          │
│ MFT Record 6:  $Bitmap       (cluster allocation bitmap) │
│ MFT Record 7:  $Boot         (boot sector + BPB)         │
│ MFT Record 8:  $BadClus      (cluster difettosi)         │
│ MFT Record 9:  $Secure       (security descriptors)      │
│ MFT Record 10: $UpCase       (tabella conversione maius.)│
│ MFT Record 11: $Extend       (directory estensioni)      │
│ MFT Record 12-15: riservati                              │
│ MFT Record 16+: file e directory utente                  │
└──────────────────────────────────────────────────────────┘

Ogni record MFT:
┌──────────────────────────────────────────────────────────┐
│ Header (42 byte):                                        │
│   Signature "FILE"                                       │
│   Offset primo attributo                                 │
│   Flags (in-use, directory)                              │
│   Bytes usati / allocati                                 │
│   Base record reference                                  │
│   Next attribute ID                                      │
├──────────────────────────────────────────────────────────┤
│ Attributo 1: $STANDARD_INFORMATION                       │
│ Attributo 2: $FILE_NAME                                  │
│ Attributo 3: $DATA (o $INDEX_ROOT se directory)          │
│ Attributo N: ...                                         │
│ End marker: 0xFFFFFFFF                                   │
└──────────────────────────────────────────────────────────┘

Dimensione record MFT: 1 KB (default), 2 KB o 4 KB configurabile.
```

File piccoli (< ~700 byte) possono essere **resident** — i dati risiedono direttamente nel record MFT, senza cluster separati. Questo è estremamente efficiente per file di configurazione piccoli.

```powershell
# Informazioni MFT e volume NTFS
fsutil fsinfo ntfsinfo D:
# Output include:
#   MFT Zone Size, MFT Valid Data Length, Total Clusters,
#   Bytes Per Cluster, Bytes Per MFT Record, etc.

# Dimensione corrente della MFT
fsutil volume filelayout D:\$MFT

# Verificare frammentazione MFT
# Una MFT frammentata causa performance scadenti
# Defrag della MFT (richiede reboot):
defrag D: /X    # Consolida la MFT free space zone

# Zone MFT: Windows riserva ~12.5% del volume per crescita MFT
# Modificare la zona (0=min, 4=max):
fsutil behavior set mftzone 2
```

### Attributi dei File NTFS

Ogni file NTFS è un insieme di attributi (attribute streams). Gli attributi principali:

| ID Tipo | Nome Attributo | Descrizione |
|---------|---------------|-------------|
| 0x10 | $STANDARD_INFORMATION | Timestamp (creazione, modifica, accesso, entry), flags, owner, security ID |
| 0x20 | $ATTRIBUTE_LIST | Lista attributi se il file usa più record MFT |
| 0x30 | $FILE_NAME | Nome file (Win32 e/o DOS 8.3), parent directory ref, timestamp ridondante |
| 0x40 | $OBJECT_ID | GUID univoco del file (opzionale) |
| 0x50 | $SECURITY_DESCRIPTOR | ACL inline (usato raramente, normalmente in $Secure) |
| 0x60 | $VOLUME_NAME | Label del volume (solo su $Volume) |
| 0x70 | $VOLUME_INFORMATION | Versione NTFS, flags dirty (solo su $Volume) |
| 0x80 | $DATA | Contenuto del file (unnamed = stream principale) |
| 0x90 | $INDEX_ROOT | Root del B+ tree per directory (sempre resident) |
| 0xA0 | $INDEX_ALLOCATION | Nodi non-root del B+ tree di directory |
| 0xB0 | $BITMAP | Bitmap per cluster allocati o indici directory |
| 0xC0 | $REPARSE_POINT | Dati reparse (symbolic link, junction, mount point) |
| 0xD0 | $EA_INFORMATION | Dimensione Extended Attributes |
| 0xE0 | $EA | Extended Attributes (compatibilità OS/2) |

```powershell
# Visualizzare attributi di un file con fsutil
fsutil file queryfilenamebyid D: 0x000000000000002e

# Informazioni attributi (timestamp, dimensione)
(Get-Item "D:\file.txt").GetType().GetProperties() | ForEach-Object {
    "$($_.Name): $($_.GetValue((Get-Item 'D:\file.txt')))"
}

# Timestamp dettagliati
$file = Get-Item "D:\file.txt"
$file.CreationTime          # Timestamp creazione
$file.LastWriteTime         # Ultima modifica
$file.LastAccessTime        # Ultimo accesso
$file.Attributes            # Flag: Archive, ReadOnly, Hidden, System, Compressed, Encrypted

# Nomi 8.3 (short name)
fsutil 8dot3name query D:
# Disabilitare nomi 8.3 (performance migliori, meno attacco surface):
fsutil 8dot3name set D: 1    # 1 = disabilita sul volume
# Nota: i nomi 8.3 esistenti rimangono finché non si esegue:
fsutil 8dot3name strip /s /v D:
```

### Compressione NTFS

La compressione NTFS opera a livello di cluster, comprimendo unità di 16 cluster (compression unit).

```
Funzionamento:
┌──────────────────────────────────────────────┐
│ File originale: 16 cluster (64 KB con 4K AU) │
│ [C1][C2][C3][C4][C5][C6][C7][C8]....[C16]   │
│                                              │
│ Dopo compressione (se riduce):               │
│ [Compressed data: 9 cluster][Sparse: 7 virt] │
│                                              │
│ Se i dati non si comprimono sufficientemente: │
│ [C1][C2][C3]...[C16] (non compressi)         │
└──────────────────────────────────────────────┘

Pro:
✓ Trasparente alle applicazioni
✓ Risparmio significativo su file di testo, log, documenti
✓ Configurabile per file/cartella/volume

Contro:
✗ Overhead CPU per compressione/decompressione in tempo reale
✗ Frammentazione aumentata
✗ Incompatibile con EFS sullo stesso file
✗ Non raccomandato per file > 30 GB o database attivi
✗ Non funziona con allocation unit > 4 KB
```

```powershell
# Comprimere una cartella ricorsivamente
Compact /c /s:"D:\Archivio"

# Decomprimere
Compact /u /s:"D:\Archivio"

# Verificare stato compressione
Compact /q "D:\Archivio"

# Comprimere un singolo file
Compact /c "D:\Logs\app.log"

# PowerShell: impostare attributo compressione
$item = Get-Item "D:\Archivio"
$item.Attributes = $item.Attributes -bor [System.IO.FileAttributes]::Compressed

# Verificare risparmio su tutto il volume
Compact /s /q D:\
# Output: XX files, XX bytes stored in YY bytes. Compression ratio ZZ:1

# Compressione su nuovi file (eredità attributo)
# Se la cartella è compressa, i nuovi file creati al suo interno
# ereditano l'attributo di compressione

# NOTA: Allocation Unit Size > 4096 (4K) disabilita la compressione NTFS.
# Per SQL Server (64K AUS) la compressione NTFS non è utilizzabile.
```

### Crittografia EFS

Encrypting File System (EFS) fornisce crittografia a livello file, trasparente per l'utente che possiede la chiave.

```
Architettura EFS:
┌──────────────────────────────────────────────────────┐
│ Utente A cripta file.txt                             │
│                                                      │
│ 1. Windows genera FEK (File Encryption Key) simm.   │
│    AES-256 per crittografare il contenuto            │
│                                                      │
│ 2. FEK viene crittografata con la chiave pubblica    │
│    del certificato EFS dell'utente                   │
│                                                      │
│ 3. FEK crittografata → campo DDF (Data Decryption    │
│    Field) nell'attributo $LOGGED_UTILITY_STREAM      │
│                                                      │
│ 4. (Opzionale) FEK crittografata anche con chiave    │
│    pubblica del DRA (Data Recovery Agent) →           │
│    campo DRF (Data Recovery Field)                   │
└──────────────────────────────────────────────────────┘

Prerequisiti:
- Volume NTFS (non funziona su ReFS, FAT, exFAT)
- Certificato EFS per l'utente (generato automaticamente al primo uso)
- NON compatibile con compressione NTFS sullo stesso file
- NON usabile su file di sistema o boot volume
```

```powershell
# Crittografare cartella
cipher /e "D:\Confidential"

# Crittografare ricorsivamente
cipher /e /s:"D:\Confidential"

# Decrittografare
cipher /d "D:\Confidential"
cipher /d /s:"D:\Confidential"

# Visualizzare stato crittografia
cipher "D:\Confidential"
# U = non crittografato, E = crittografato

# Wipe dello spazio libero (sovrascrive dati eliminati)
cipher /w:D:\

# Backup della chiave EFS dell'utente corrente
cipher /x "C:\Backup\EFS-Key-Backup"
# Genera un file .pfx protetto da password

# Visualizzare certificato EFS
cipher /r:EFSrecovery    # Genera certificato + chiave DRA
# Genera EFSrecovery.cer (pubblico) e EFSrecovery.pfx (privato)

# Aggiungere DRA (Data Recovery Agent) via Group Policy:
# Computer Configuration → Windows Settings → Security Settings
# → Public Key Policies → Encrypting File System → Add Data Recovery Agent

# Verificare informazioni EFS su un file
cipher /c "D:\Confidential\secret.docx"
# Mostra: utenti autorizzati, recovery agent, thumbprint certificato

# ATTENZIONE: se si perde il certificato EFS e non c'è DRA,
# i file crittografati sono IRRECUPERABILI. Sempre configurare DRA
# e fare backup dei certificati.
```

### Hard Link

Un hard link è un puntatore diretto al record MFT di un file. Più nomi possono puntare allo stesso file fisico.

```
Caratteristiche:
- Stesso volume NTFS obbligatorio
- Solo file (non directory, per evitare cicli)
- Il file viene eliminato solo quando l'ultimo hard link viene rimosso
- Tutti i link condividono gli stessi dati, attributi, timestamp
- Nessun overhead di spazio (puntano allo stesso record MFT)
- Massimo 1024 hard link per file

Struttura:
              MFT Record 1234
              ┌──────────────┐
File A.txt ──→│  $DATA       │←── File B.txt (hard link)
              │  (contenuto) │
              │  Link count:2│
              └──────────────┘
```

```powershell
# Creare hard link
New-Item -ItemType HardLink -Path "D:\LinkB.txt" -Target "D:\FileA.txt"

# Con cmd:
# mklink /H "D:\LinkB.txt" "D:\FileA.txt"

# Con fsutil:
# fsutil hardlink create "D:\LinkB.txt" "D:\FileA.txt"

# Elencare hard link di un file (trovare tutti i nomi che puntano allo stesso record)
fsutil hardlink list "D:\FileA.txt"

# Contare hard link
(Get-Item "D:\FileA.txt").LinkType    # restituisce "HardLink" se ha link
```

### Symbolic Link

Un symbolic link (symlink) è un puntatore al percorso di un altro file o directory. Funziona come un "shortcut" a livello filesystem.

```
Caratteristiche:
- Può attraversare volumi e drive diversi
- Può puntare a file E directory
- Può puntare a percorsi di rete (UNC)
- Se il target viene eliminato, il symlink diventa "dangling" (broken)
- Richiede privilegio SeCreateSymbolicLinkPrivilege
  (default: Administrators; Developer Mode abilita per tutti)
- Occupa spazio minimo (solo il percorso target)

Struttura:
Symlink.txt ──→ Reparse Point ($REPARSE_POINT attribute)
                    │
                    └── Target: "D:\Original\File.txt"
                        Tag: IO_REPARSE_TAG_SYMLINK (0xA000000C)
```

```powershell
# Symlink a file
New-Item -ItemType SymbolicLink -Path "D:\link.txt" -Target "D:\Original\file.txt"

# Symlink a directory
New-Item -ItemType SymbolicLink -Path "D:\LinkDir" -Target "D:\Original\Directory"

# Con cmd:
# mklink "D:\link.txt" "D:\Original\file.txt"            # file
# mklink /D "D:\LinkDir" "D:\Original\Directory"         # directory

# Verificare un symlink
Get-Item "D:\link.txt" | Select-Object Name, LinkType, Target
# LinkType: SymbolicLink, Target: D:\Original\file.txt

# Elencare tutti i symlink in una directory
Get-ChildItem "D:\" -Recurse | Where-Object { $_.LinkType -eq 'SymbolicLink' }

# Rimuovere symlink (non elimina il target)
Remove-Item "D:\link.txt"
```

### Junction Point

Un junction point è un tipo di reparse point che reindirizza una directory a un'altra directory sullo stesso volume o diverso (ma sempre locale).

```
Caratteristiche:
- Solo directory (non file)
- Solo percorsi locali (no UNC/rete)
- Non richiede privilegi elevati (a differenza dei symlink)
- Risoluzione lato server (il client non vede il reindirizzamento)
- Usato internamente da Windows per:
  - Documents and Settings → Users
  - Application Data → AppData\Roaming

Differenza chiave da symlink:
┌────────────────────┬────────────────┬──────────────────┐
│                    │ Junction Point │ Directory Symlink │
├────────────────────┼────────────────┼──────────────────┤
│ Solo directory     │ Sì             │ No (anche file)  │
│ Cross-volume       │ Sì (locale)    │ Sì (anche rete)  │
│ Richiede admin     │ No             │ Sì*              │
│ Risoluzione        │ Server-side    │ Client-side      │
│ Reparse tag        │ MOUNT_POINT    │ SYMLINK          │
└────────────────────┴────────────────┴──────────────────┘
* Developer Mode elimina il requisito admin per i symlink
```

```powershell
# Creare junction
New-Item -ItemType Junction -Path "C:\Data" -Target "D:\Archivio\Data"

# Con cmd:
# mklink /J "C:\Data" "D:\Archivio\Data"

# Verificare junction
Get-Item "C:\Data" | Select-Object Name, LinkType, Target

# Elencare tutte le junction in C:\Users
Get-ChildItem "C:\Users" -Force | Where-Object { $_.LinkType -eq 'Junction' }

# Rimuovere junction (NON elimina il contenuto della directory target)
Remove-Item "C:\Data" -Force
# ATTENZIONE: Non usare Remove-Item -Recurse su una junction!
# Cancellerebbe il contenuto della directory target.
# Usare solo Remove-Item senza -Recurse, oppure cmd: rmdir "C:\Data"
```

### Alternate Data Streams (ADS)

NTFS supporta stream di dati multipli per file. Lo stream principale (unnamed) contiene i dati normali. Stream aggiuntivi (named) possono contenere metadati arbitrari.

```
Uso legittimo:
- Zone Identifier: Windows segna i file scaricati da Internet con
  Zone.Identifier ADS (Mark of the Web)
- Riepilogo documento: proprietà come Titolo, Autore
- Macintosh resource fork (compatibilità legacy)

Rischio sicurezza:
- Malware può nascondere codice in ADS (non visibile con dir o Explorer)
- Dati sensibili possono essere nascosti in ADS
- Le scansioni antivirus devono controllare gli ADS
```

```powershell
# Visualizzare ADS di un file
Get-Item "D:\downloaded-file.exe" -Stream *

# Leggere contenuto di un ADS specifico
Get-Content "D:\downloaded-file.exe" -Stream Zone.Identifier
# Output tipico:
# [ZoneTransfer]
# ZoneId=3        # 3 = Internet

# Creare un ADS personalizzato
Set-Content "D:\file.txt" -Stream "NoteSegrete" -Value "Contenuto nascosto"

# Leggere ADS personalizzato
Get-Content "D:\file.txt" -Stream "NoteSegrete"

# Rimuovere ADS (es. sbloccare file scaricato)
Remove-Item "D:\downloaded-file.exe" -Stream Zone.Identifier
# Oppure:
Unblock-File "D:\downloaded-file.exe"

# Elencare TUTTI i file con ADS in una directory
Get-ChildItem "D:\" -Recurse | ForEach-Object {
    $streams = Get-Item $_.FullName -Stream * -ErrorAction SilentlyContinue |
               Where-Object { $_.Stream -ne ':$DATA' }
    if ($streams) {
        [PSCustomObject]@{
            Path = $_.FullName
            Streams = ($streams.Stream -join ', ')
        }
    }
}

# Con cmd: elencare ADS
# dir /R "D:\file.txt"

# Con sysinternals streams.exe:
# streams.exe -s D:\
```

---

## ReFS — Resilient File System

### Architettura ReFS

ReFS (Resilient File System) è il filesystem di nuova generazione di Microsoft, progettato per integrità dei dati, scalabilità e performance per workload specifici.

```
Architettura interna ReFS:
┌──────────────────────────────────────────────────────────┐
│ ReFS usa B+ tree per TUTTE le strutture:                 │
│                                                          │
│ ┌────────────────┐                                       │
│ │   Object Table │ (equivalente della MFT di NTFS)       │
│ │   (B+ tree)    │                                       │
│ └───────┬────────┘                                       │
│         │                                                │
│    ┌────┴─────┐                                          │
│    │          │                                          │
│ ┌──┴──┐   ┌──┴──┐                                       │
│ │Dir  │   │Dir  │   Directory table (B+ tree per dir)    │
│ │Table│   │Table│                                        │
│ └──┬──┘   └─────┘                                       │
│    │                                                     │
│ ┌──┴──────────┐                                          │
│ │ File extents│  Mappatura cluster → dati                │
│ │ (B+ tree)   │                                          │
│ └─────────────┘                                          │
│                                                          │
│ Allocator:                                               │
│ - Large cluster: default 64 KB (vs 4 KB NTFS)           │
│ - Allocation bitmap gerarchica                           │
│                                                          │
│ Integrità:                                               │
│ - Checksum su metadati (sempre attivo, CRC64)            │
│ - Checksum su dati (opzionale, integrity streams)        │
│ - Allocate-on-write (COW): nuove scritture su cluster    │
│   nuovi, metadati vecchi aggiornati atomicamente         │
│ - No journal ($LogFile): COW rende il journal superfluo  │
└──────────────────────────────────────────────────────────┘
```

Funzionalità chiave:
- **Block cloning** — copia logica di range di cluster senza I/O fisico. Accelera operazioni Hyper-V (merge checkpoint, copia VHDX)
- **Sparse VDL** — consente ai file di inizializzare solo le regioni scritte, senza azzerare tutto
- **Integrity streams** — checksum CRC64 su ogni blocco dati, con rilevamento corruzione
- **Proactive error correction** — con Storage Spaces, ReFS può auto-riparare dati corrotti usando la copia mirror
- **Scalabilità** — volumi fino a 35 PB, file fino a 16 EB teorici

```powershell
# Formattare come ReFS
Format-Volume -DriveLetter E -FileSystem ReFS -NewFileSystemLabel "ReFS-Data"

# ReFS con SetIntegrityInformation (default OFF per dati)
Format-Volume -DriveLetter E -FileSystem ReFS -SetIntegrityStreams $true

# Abilitare integrity streams su una cartella
Set-FileIntegrity -FileName "E:\Critical" -Enable $true

# Verificare stato integrità
Get-FileIntegrity "E:\Critical"

# Informazioni volume ReFS
Get-Volume -DriveLetter E | Format-List FileSystem, FileSystemLabel,
    HealthStatus, Size, SizeRemaining, AllocationUnitSize
```

### Confronto NTFS vs ReFS

| Feature | NTFS | ReFS |
|---------|------|------|
| Boot volume | Si | No |
| Compressione nativa | Si | No |
| Crittografia EFS | Si | No |
| BitLocker | Si | Si |
| Deduplicazione | Si | Si (Server 2019+) |
| Quotas NTFS | Si | No |
| Hard link | Si | No |
| Symbolic link | Si | Si |
| Short names (8.3) | Si | No |
| Integrity streams | No | Si |
| Block cloning | No | Si |
| Sparse VDL | No | Si |
| Max volume | 256 TB | 35 PB |
| Max file | 256 TB | 16 EB (teorico) |
| Allocation unit default | 4 KB | 64 KB |
| Journal transazionale | Si ($LogFile) | No (usa COW) |
| Self-healing con Storage Spaces | No | Si |
| Named streams (ADS) | Si | Si |
| Object ID | Si | Si |
| Extended attributes | Si | No |
| Cluster size supportati | 512B-64KB | 4KB-64KB |

### Casi d'uso e Limitazioni

```
USARE ReFS quando:
✓ Hyper-V: VHDX storage con block cloning per merge checkpoint
✓ Storage Spaces / S2D: auto-repair con mirror
✓ Backup target: protezione integrità dati di backup
✓ Dataset molto grandi (> 64 TB)
✓ Workload che beneficiano di block cloning (copia VM)

NON usare ReFS quando:
✗ Boot volume (non supportato)
✗ Serve compressione nativa (usare NTFS)
✗ Serve EFS (usare NTFS + EFS o BitLocker)
✗ Serve compatibilità con tool legacy che richiedono NTFS
✗ Serve quota NTFS nativa (usare NTFS + FSRM)
✗ Windows client (ReFS supportato solo su Server)
✗ Applicazioni che richiedono hard link
```

---

## Storage Spaces

### Fondamenti e Gerarchia

```
Storage Spaces è la tecnologia software-defined storage di Windows
che permette di creare pool di dischi con resilienza integrata.

Gerarchia:
Physical Disks → Storage Pool → Virtual Disk (con resilienza) → Volume

┌─────────────────────────────────────────────────────────────────┐
│                        Storage Pool                             │
│   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│   │Disk1│ │Disk2│ │Disk3│ │Disk4│ │Disk5│ │Disk6│ │Disk7│   │
│   │ SSD │ │ SSD │ │ HDD │ │ HDD │ │ HDD │ │ HDD │ │ Hot │   │
│   │     │ │     │ │     │ │     │ │     │ │     │ │Spare│   │
│   └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘   │
│      │       │       │       │       │       │       │       │
│      └───────┴───────┴───────┴───────┴───────┴───────┘       │
│                              │                                 │
│   ┌──────────────────────────┴────────────────────────────┐    │
│   │              Virtual Disk "VMStorage"                  │    │
│   │    Resilienza: Mirror, Parity, o Simple                │    │
│   │    Provisioning: Thin o Fixed                          │    │
│   └──────────────────────┬────────────────────────────────┘    │
│                          │                                     │
│   ┌──────────────────────┴────────────────────────────────┐    │
│   │              Volume (NTFS o ReFS)                      │    │
│   │              Lettera drive o mount point                │    │
│   └───────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Tipi di Resilienza

```
Tipi di resilienza Storage Spaces:

Simple (Striping)
├── Nessuna protezione da guasti disco
├── Performance I/O massime (striping su tutti i dischi)
├── Spazio utilizzabile = 100% della capacità dei dischi
├── Minimo 1 disco
└── Uso: dati temporanei, cache, scratch space

Mirror (Two-Way)
├── Copia su 2 dischi (equivalente RAID 1/10)
├── Tolleranza: 1 guasto disco
├── Spazio utilizzabile = 50% della capacità totale
├── Minimo 2 dischi
├── Read performance buona (può leggere da entrambe le copie)
└── Uso: OS, database, dati critici

Mirror (Three-Way)
├── Copia su 3 dischi
├── Tolleranza: 2 guasti disco simultanei
├── Spazio utilizzabile = 33% della capacità totale
├── Minimo 5 dischi (per fault domain isolation in S2D)
├── Massima protezione
└── Uso: dati mission-critical, S2D, Hyper-V

Parity (Single)
├── Striping con parità distribuita (equivalente RAID 5)
├── Tolleranza: 1 guasto disco
├── Spazio utilizzabile = (N-1)/N della capacità
├── Minimo 3 dischi
├── Write penalty significativo (read-modify-write)
└── Uso: archivio, backup, dati sequenziali read-heavy

Dual Parity
├── Doppia parità distribuita (equivalente RAID 6)
├── Tolleranza: 2 guasti disco simultanei
├── Spazio utilizzabile = (N-2)/N della capacità
├── Minimo 7 dischi
├── Write penalty più alto del single parity
└── Uso: grandi archivi, backup a lungo termine, cold storage
```

### Thin Provisioning

```
Fixed Provisioning:
- Lo spazio viene allocato immediatamente dal pool
- Il virtual disk occupa subito la dimensione specificata
- Performance prevedibili
- Uso: workload production con requisiti I/O certi

Thin Provisioning:
- Lo spazio viene allocato on-demand man mano che i dati vengono scritti
- Si può creare un virtual disk più grande dello spazio fisico disponibile
  (overprovisioning)
- Risparmio di spazio iniziale
- ATTENZIONE: monitorare attentamente lo spazio fisico disponibile nel pool
- Se il pool esaurisce lo spazio, i virtual disk vanno offline
- Uso: ambienti di test, storage con crescita graduale
```

```powershell
# Thin provisioning — il volume sembra 2TB ma usa solo lo spazio effettivo
New-VirtualDisk -StoragePoolFriendlyName "DataPool" -FriendlyName "ThinDisk" `
    -ResiliencySettingName Mirror -Size 2TB -ProvisioningType Thin

# Fixed provisioning — alloca subito tutto lo spazio
New-VirtualDisk -StoragePoolFriendlyName "DataPool" -FriendlyName "FixedDisk" `
    -ResiliencySettingName Mirror -Size 500GB -ProvisioningType Fixed

# Verificare provisioning e spazio reale
Get-VirtualDisk | Select-Object FriendlyName, ProvisioningType,
    @{N='Size_GB';E={[math]::Round($_.Size/1GB,2)}},
    @{N='FootprintOnPool_GB';E={[math]::Round($_.FootprintOnPool/1GB,2)}}
```

### Tiered Storage

Storage Tiers permette di combinare SSD e HDD nello stesso virtual disk, con promozione automatica dei dati più acceduti verso il tier SSD.

```
Architettura Tiered Storage:
┌──────────────────────────────────────────────────┐
│              Virtual Disk (Tiered)                │
│                                                  │
│  ┌──────────────────┐  ┌──────────────────────┐  │
│  │   SSD Tier       │  │     HDD Tier         │  │
│  │   (Performance)  │  │     (Capacity)       │  │
│  │                  │  │                      │  │
│  │  Dati "hot"      │  │  Dati "cold"         │  │
│  │  Accesso freq.   │  │  Accesso raro        │  │
│  │  100 GB          │  │  900 GB              │  │
│  └──────────────────┘  └──────────────────────┘  │
│                                                  │
│  Write-Back Cache (opzionale):                   │
│  SSD dedicato per buffer scritture               │
└──────────────────────────────────────────────────┘

Schedulazione:
- Task schedulato (default 1:00 AM) analizza pattern di accesso
- File/blocchi acceduti frequentemente → promossi a SSD tier
- File/blocchi raramente acceduti → demossi a HDD tier
- Pin di file specifici al tier SSD per performance garantite
```

```powershell
# Creare tier SSD e HDD
New-StorageTier -StoragePoolFriendlyName "DataPool" -FriendlyName "SSD-Tier" `
    -MediaType SSD
New-StorageTier -StoragePoolFriendlyName "DataPool" -FriendlyName "HDD-Tier" `
    -MediaType HDD

# Creare virtual disk tiered
$ssdTier = Get-StorageTier -FriendlyName "SSD-Tier"
$hddTier = Get-StorageTier -FriendlyName "HDD-Tier"
New-VirtualDisk -StoragePoolFriendlyName "DataPool" -FriendlyName "TieredDisk" `
    -StorageTiers $ssdTier, $hddTier `
    -StorageTierSizes 100GB, 900GB `
    -ResiliencySettingName Mirror `
    -WriteCacheSize 5GB    # Write-back cache di 5 GB

# Pinnare un file al tier SSD (performance garantite)
Set-FileStorageTier -FilePath "E:\Database\critical.mdf" `
    -DesiredStorageTierFriendlyName "SSD-Tier"

# Verificare tier corrente di un file
Get-FileStorageTier -FilePath "E:\Database\critical.mdf"

# Vedere statistiche tier
Get-StorageTierSupportedSize -FriendlyName "SSD-Tier"

# Forzare ottimizzazione tier manualmente
Optimize-StorageTier -CimSession . -RunOnce
# Normalmente è schedulato automaticamente via Task Scheduler:
# \Microsoft\Windows\Storage Tiers Management\Storage Tiers Optimization
```

### Configurazione Completa

```powershell
# ═══════════════════════════════════════════════════════════
# WORKFLOW COMPLETO: STORAGE SPACES
# ═══════════════════════════════════════════════════════════

# 1. Verificare dischi disponibili (non inizializzati, non partizionati)
Get-PhysicalDisk | Where-Object CanPool -eq $true |
    Select-Object FriendlyName, Size, MediaType, BusType, HealthStatus

# 2. Creare Storage Pool
$disks = Get-PhysicalDisk | Where-Object CanPool -eq $true
New-StoragePool -FriendlyName "DataPool" `
    -StorageSubsystemFriendlyName "Windows Storage*" `
    -PhysicalDisks $disks

# 3. Verificare pool creato
Get-StoragePool -FriendlyName "DataPool" | Format-List *

# 4. Creare Virtual Disk — Mirror (2 copie)
New-VirtualDisk -StoragePoolFriendlyName "DataPool" -FriendlyName "MirroredDisk" `
    -ResiliencySettingName Mirror -Size 500GB -ProvisioningType Thin `
    -NumberOfColumns 1 -NumberOfDataCopies 2

# Oppure: Parity (single)
New-VirtualDisk -StoragePoolFriendlyName "DataPool" -FriendlyName "ParityDisk" `
    -ResiliencySettingName Parity -Size 1TB -ProvisioningType Thin

# Oppure: Three-way mirror (3 copie, richiede 5+ dischi)
New-VirtualDisk -StoragePoolFriendlyName "DataPool" -FriendlyName "3WayMirror" `
    -ResiliencySettingName Mirror -Size 200GB -NumberOfDataCopies 3

# 5. Inizializzare e formattare
Get-VirtualDisk -FriendlyName "MirroredDisk" | Get-Disk |
    Initialize-Disk -PartitionStyle GPT -PassThru |
    New-Partition -UseMaximumSize -DriveLetter E |
    Format-Volume -FileSystem NTFS -NewFileSystemLabel "Mirror-Data"

# ═══════════════════════════════════════════════════════════
# GESTIONE POOL E DISCHI
# ═══════════════════════════════════════════════════════════

# Stato dischi nel pool
Get-StoragePool -FriendlyName "DataPool" | Get-PhysicalDisk |
    Select-Object FriendlyName, Size, MediaType, HealthStatus,
    OperationalStatus, Usage

# Aggiungere disco al pool
$newDisk = Get-PhysicalDisk | Where-Object CanPool -eq $true
Add-PhysicalDisk -StoragePoolFriendlyName "DataPool" -PhysicalDisks $newDisk

# Designare disco come hot spare
Set-PhysicalDisk -FriendlyName "PhysicalDisk7" -Usage HotSpare

# Rimuovere disco dal pool (prima ritirare)
Set-PhysicalDisk -FriendlyName "OldDisk" -Usage Retired
# I dati vengono spostati automaticamente su altri dischi
# Dopo completamento:
Remove-PhysicalDisk -StoragePoolFriendlyName "DataPool" `
    -PhysicalDisks (Get-PhysicalDisk -FriendlyName "OldDisk")

# Riparare virtual disk (dopo sostituzione disco guasto)
Repair-VirtualDisk -FriendlyName "MirroredDisk"

# Verificare stato riparazione
Get-VirtualDisk -FriendlyName "MirroredDisk" |
    Select-Object FriendlyName, HealthStatus, OperationalStatus,
    @{N='RepairPct';E={$_.OperationalStatus}}

# ═══════════════════════════════════════════════════════════
# MONITORAGGIO STORAGE SPACES
# ═══════════════════════════════════════════════════════════

# Salute complessiva
Get-StoragePool | Select-Object FriendlyName, HealthStatus, OperationalStatus,
    @{N='Size_TB';E={[math]::Round($_.Size/1TB,2)}},
    @{N='AllocatedPct';E={[math]::Round(($_.AllocatedSize/$_.Size)*100,1)}}

Get-VirtualDisk | Select-Object FriendlyName, HealthStatus, OperationalStatus,
    ResiliencySettingName, ProvisioningType,
    @{N='Size_GB';E={[math]::Round($_.Size/1GB,2)}}

Get-PhysicalDisk | Select-Object FriendlyName, MediaType, HealthStatus,
    @{N='Size_GB';E={[math]::Round($_.Size/1GB,2)}},
    @{N='Reliability';E={$_.OperationalStatus}}
```

---

## Storage Spaces Direct (S2D)

### Architettura S2D

```
S2D crea storage condiviso da dischi locali di più server in un cluster.
Elimina la necessità di storage SAN/NAS condiviso — ogni nodo contribuisce
i propri dischi locali a un pool distribuito.

Topologia S2D:
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│     Node 1      │ │     Node 2      │ │     Node 3      │
│ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │
│ │ NVMe (cache)│ │ │ │ NVMe (cache)│ │ │ │ NVMe (cache)│ │
│ │ SSD (cap.)  │ │ │ │ SSD (cap.)  │ │ │ │ SSD (cap.)  │ │
│ │ HDD (cap.)  │ │ │ │ HDD (cap.)  │ │ │ │ HDD (cap.)  │ │
│ └─────────────┘ │ │ └─────────────┘ │ │ └─────────────┘ │
│  Software       │ │  Software       │ │  Software       │
│  Storage Bus    │ │  Storage Bus    │ │  Storage Bus    │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                    Network (RDMA preferito)
                    10 GbE minimo, 25/100 GbE consigliato
                             │
               ┌─────────────┴─────────────┐
               │   Unified Storage Pool    │
               │      (distribuito)        │
               │                           │
               │  ┌───────────────────┐    │
               │  │ CSV Volumes       │    │
               │  │ (NTFS o ReFS)     │    │
               │  │ C:\ClusterStorage │    │
               │  └───────────────────┘    │
               └───────────────────────────┘

Componenti software:
┌─────────────────────────────────────────────────────────┐
│  Software Storage Bus Layer                              │
│  ├── Cache Manager: NVMe/SSD come read/write cache      │
│  ├── Software Bus: aggregazione dischi remoti            │
│  ├── Health Service: monitoraggio, alerting              │
│  └── Storage Pool: pool unificato di tutti i dischi      │
│                                                          │
│  Cache behavior:                                         │
│  ┌──────────────────────────────────────────┐            │
│  │ Se NVMe + SSD:  NVMe = cache             │            │
│  │ Se NVMe + HDD:  NVMe = cache             │            │
│  │ Se SSD + HDD:   SSD = cache              │            │
│  │ Se solo SSD:    nessun cache tier         │            │
│  │ Se solo HDD:    nessun cache tier         │            │
│  │ Se solo NVMe:   nessun cache tier         │            │
│  └──────────────────────────────────────────┘            │
│                                                          │
│  Cache read/write binding:                               │
│  - Ogni disco capacity è bindato a 1-2 dischi cache      │
│  - Write cache: write-back (scritte prima su cache)      │
│  - Read cache: dati letti frequentemente promossi        │
└─────────────────────────────────────────────────────────┘
```

### Requisiti Hardware e Software

```
Requisiti Software:
├── Windows Server 2016 Datacenter o successivo
├── Failover Clustering feature
├── Hyper-V role (se hyperconverged)
└── Nodi: minimo 2, massimo 16 nodi per cluster

Requisiti Hardware per nodo:
├── CPU: x86-64, minimo 2 core
├── RAM: minimo 4 GB + 1 GB per ogni TB di cache
├── Network: minimo 10 GbE (consigliato 25/100 GbE con RDMA)
│   ├── RDMA: RoCE v2 o iWARP
│   └── Minimo 2 NIC per nodo (ridondanza + separazione traffico)
├── Dischi:
│   ├── Minimo 2 dischi capacity per nodo
│   ├── Tutti i nodi devono avere configurazione identica (o molto simile)
│   ├── Dischi SAS, SATA o NVMe (NO USB, NO RAID controller)
│   ├── Cache tier: tutti NVMe o tutti SSD (non mescolare)
│   └── JBOD enclosure supportato (SAS attached)
├── Boot: SSD/NVMe o M.2 dedicato per OS (non usare dischi del pool)
└── Firmware: HBA in modalità HBA/passthrough (non RAID)

Modelli di deployment:
┌─────────────────────┬───────────────────────────────────┐
│ Hyperconverged      │ Compute + Storage sugli stessi    │
│                     │ nodi. Hyper-V + S2D sul cluster.  │
│                     │ Più semplice, meno hardware.      │
├─────────────────────┼───────────────────────────────────┤
│ Disaggregated       │ Storage cluster separato da        │
│ (converged)         │ compute cluster. S2D fornisce     │
│                     │ storage via SMB3/CSV al cluster   │
│                     │ Hyper-V separato.                 │
└─────────────────────┴───────────────────────────────────┘
```

### Deployment S2D

```powershell
# ═══════════════════════════════════════════════════════════
# DEPLOYMENT S2D — STEP BY STEP
# ═══════════════════════════════════════════════════════════

# Prerequisito: cluster già creato con Failover Clustering
# Prerequisito: networking configurato (RDMA, vSwitch, ecc.)

# 1. Validare cluster
Test-Cluster -Node Node1, Node2, Node3 -Include "Storage Spaces Direct",
    "Inventory", "Network", "System Configuration"

# 2. Pulire eventuali dati residui sui dischi
# ATTENZIONE: distrugge TUTTI i dati sui dischi dei nodi
Invoke-Command -ComputerName Node1, Node2, Node3 -ScriptBlock {
    Get-Disk | Where-Object Number -ne 0 | Clear-Disk -RemoveData -Confirm:$false
}

# 3. Abilitare S2D sul cluster
Enable-ClusterStorageSpacesDirect -CacheState Enabled -Confirm:$false

# 4. Verificare pool creato
Get-StoragePool | Where-Object IsPrimordial -eq $false

# 5. Creare volume CSV con ReFS e mirror
New-Volume -StoragePoolFriendlyName "S2D on ClusterName" `
    -FriendlyName "VM-Storage" `
    -FileSystem CSVFS_ReFS `
    -Size 1TB `
    -ResiliencySettingName Mirror

# Volume con three-way mirror (richiede 5+ nodi per fault domain)
New-Volume -StoragePoolFriendlyName "S2D on ClusterName" `
    -FriendlyName "Critical-VMs" `
    -FileSystem CSVFS_ReFS `
    -Size 500GB `
    -ResiliencySettingName Mirror `
    -NumberOfDataCopies 3

# Volume parity (archivio, backup)
New-Volume -StoragePoolFriendlyName "S2D on ClusterName" `
    -FriendlyName "Archive" `
    -FileSystem CSVFS_ReFS `
    -Size 2TB `
    -ResiliencySettingName Parity

# 6. Il volume appare come CSV in C:\ClusterStorage\
Get-ClusterSharedVolume | Select-Object Name, State,
    @{N='Path';E={$_.SharedVolumeInfo.FriendlyVolumeName}}
```

### Monitoraggio e Manutenzione S2D

```powershell
# ═══════════════════════════════════════════════════════════
# HEALTH E MONITORAGGIO S2D
# ═══════════════════════════════════════════════════════════

# Report salute completo
Get-StorageSubSystem *cluster* | Get-StorageHealthReport

# Stato dischi fisici
Get-PhysicalDisk | Select-Object FriendlyName, MediaType, Size,
    HealthStatus, OperationalStatus, Usage |
    Sort-Object HealthStatus

# Stato virtual disk
Get-VirtualDisk | Select-Object FriendlyName, OperationalStatus,
    HealthStatus, ResiliencySettingName,
    @{N='Size_TB';E={[math]::Round($_.Size/1TB,2)}},
    @{N='Footprint_TB';E={[math]::Round($_.FootprintOnPool/1TB,2)}}

# Job di riparazione in corso
Get-StorageJob | Select-Object Name, JobState, PercentComplete, ElapsedTime

# Allarmi e fault
Get-StorageSubSystem *cluster* | Debug-StorageSubSystem
Get-HealthFault

# Performance in tempo reale
Get-ClusterPerf -ClusterNodeName Node1 | Where-Object {
    $_.MetricId -like "*IOPS*" -or $_.MetricId -like "*Latency*"
}

# ═══════════════════════════════════════════════════════════
# MANUTENZIONE S2D
# ═══════════════════════════════════════════════════════════

# Mettere nodo in manutenzione (drain + pause)
Suspend-ClusterNode -Name Node1 -Drain Wait

# Dopo manutenzione
Resume-ClusterNode -Name Node1

# Sostituire disco guasto:
# 1. Identificare disco guasto
Get-PhysicalDisk | Where-Object HealthStatus -ne "Healthy"

# 2. Rimuovere logicamente il disco
$faultDisk = Get-PhysicalDisk | Where-Object HealthStatus -ne "Healthy"
Set-PhysicalDisk -InputObject $faultDisk -Usage Retired

# 3. Sostituire fisicamente il disco

# 4. Il nuovo disco viene rilevato automaticamente e aggiunto al pool
# La ricostruzione inizia automaticamente

# Verificare ricostruzione
Get-VirtualDisk | Where-Object OperationalStatus -eq "InService"
Get-StorageJob | Where-Object Name -like "*Repair*"
```

---

## iSCSI

### iSCSI Target (Server che espone LUN)

```powershell
# ═══════════════════════════════════════════════════════════
# iSCSI TARGET — SERVER
# ═══════════════════════════════════════════════════════════

# Installare ruolo
Install-WindowsFeature FS-iSCSITarget-Server -IncludeManagementTools

# Creare target con IQN degli initiator autorizzati
New-IscsiServerTarget -TargetName "ClusterStorage" `
    -InitiatorIds @(
        "IQN:iqn.1991-05.com.microsoft:node01.corp.contoso.com",
        "IQN:iqn.1991-05.com.microsoft:node02.corp.contoso.com"
    )

# Creare virtual disk (LUN) — file VHDX
New-IscsiVirtualDisk -Path "D:\iSCSI\ClusterDisk01.vhdx" -Size 500GB
New-IscsiVirtualDisk -Path "D:\iSCSI\ClusterDisk02.vhdx" -Size 200GB

# Creare LUN a dimensione fissa (pre-allocata, performance migliori)
New-IscsiVirtualDisk -Path "D:\iSCSI\FixedDisk.vhdx" -Size 100GB -UseFixed

# Assegnare LUN al target
Add-IscsiVirtualDiskTargetMapping -TargetName "ClusterStorage" `
    -Path "D:\iSCSI\ClusterDisk01.vhdx" -Lun 0
Add-IscsiVirtualDiskTargetMapping -TargetName "ClusterStorage" `
    -Path "D:\iSCSI\ClusterDisk02.vhdx" -Lun 1

# Gestione
Get-IscsiServerTarget
Get-IscsiVirtualDisk

# Modificare target (aggiungere initiator)
Set-IscsiServerTarget -TargetName "ClusterStorage" `
    -InitiatorIds @(
        "IQN:iqn.1991-05.com.microsoft:node01.corp.contoso.com",
        "IQN:iqn.1991-05.com.microsoft:node02.corp.contoso.com",
        "IQN:iqn.1991-05.com.microsoft:node03.corp.contoso.com"
    )

# Rimuovere mapping LUN
Remove-IscsiVirtualDiskTargetMapping -TargetName "ClusterStorage" `
    -Path "D:\iSCSI\ClusterDisk02.vhdx"

# Rimuovere target
Remove-IscsiServerTarget -TargetName "ClusterStorage"
```

### iSCSI Initiator (Client che connette LUN)

```powershell
# ═══════════════════════════════════════════════════════════
# iSCSI INITIATOR — CLIENT
# ═══════════════════════════════════════════════════════════

# Avviare servizio iSCSI initiator
Start-Service MSiSCSI
Set-Service MSiSCSI -StartupType Automatic

# Configurare IQN dell'initiator (opzionale, default auto-generato)
# iscsicli NodeName iqn.1991-05.com.microsoft:myserver.corp.contoso.com

# Configurare portal (indirizzo del target server)
New-IscsiTargetPortal -TargetPortalAddress 192.168.10.30
# Con porta custom:
New-IscsiTargetPortal -TargetPortalAddress 192.168.10.30 -TargetPortalPortNumber 3260

# Elencare target disponibili
Get-IscsiTarget
# Output: NodeAddress, IsConnected

# Connettersi al target
Connect-IscsiTarget -NodeAddress "iqn.1991-05.com.microsoft:storage-clusterstorage" `
    -IsPersistent $true

# Connessione con IP specifico dell'initiator (multi-NIC)
Connect-IscsiTarget -NodeAddress "iqn.1991-05.com.microsoft:storage-clusterstorage" `
    -InitiatorPortalAddress 192.168.10.10 `
    -TargetPortalAddress 192.168.10.30 `
    -IsPersistent $true

# Verificare sessioni attive
Get-IscsiSession | Select-Object TargetNodeAddress, IsConnected,
    IsPersistent, NumberOfConnections, SessionIdentifier

# Verificare connessioni
Get-IscsiConnection | Select-Object ConnectionIdentifier,
    TargetAddress, InitiatorAddress, InitiatorPortalAddress

# Dopo la connessione, il disco iSCSI appare come disco locale
# Inizializzare e formattare come qualsiasi disco
Get-Disk | Where-Object BusType -eq "iSCSI"

# Disconnettersi
Disconnect-IscsiTarget -NodeAddress "iqn.1991-05.com.microsoft:storage-clusterstorage"

# Rimuovere portal
Remove-IscsiTargetPortal -TargetPortalAddress 192.168.10.30
```

### MPIO — Multipath I/O

```powershell
# MPIO fornisce ridondanza di percorso e bilanciamento carico per
# connessioni iSCSI (e Fibre Channel).

# Installare feature MPIO
Install-WindowsFeature Multipath-IO -IncludeManagementTools
# Richiede REBOOT

# Abilitare MPIO per iSCSI
Enable-MSDSMAutomaticClaim -BusType iSCSI
# Richiede REBOOT

# Verificare MPIO configurato
Get-MSDSMSupportedHW
Get-MPIOSetting

# Configurare policy di bilanciamento
# Opzioni: FOO (Fail Over Only), RR (Round Robin),
#          LQD (Least Queue Depth), LB (Least Blocks),
#          WP (Weighted Paths), RRWS (Round Robin with Subset)
Set-MSDSMGlobalDefaultLoadBalancePolicy -Policy RR

# Verificare percorsi MPIO di un disco
mpclaim -s -d    # Mostra tutti i dischi MPIO e percorsi

# Visualizzare stato MPIO per disco specifico
Get-MSDSMSupportedHW | Format-List

# Configurare percorsi per target iSCSI:
# 1. Connettersi al target da NIC 1
Connect-IscsiTarget -NodeAddress "iqn...." `
    -InitiatorPortalAddress 192.168.10.10 `
    -TargetPortalAddress 192.168.10.30 `
    -IsMultipathEnabled $true -IsPersistent $true

# 2. Aggiungere secondo percorso da NIC 2
Connect-IscsiTarget -NodeAddress "iqn...." `
    -InitiatorPortalAddress 192.168.11.10 `
    -TargetPortalAddress 192.168.11.30 `
    -IsMultipathEnabled $true -IsPersistent $true

# Verificare che il disco MPIO abbia 2 percorsi
mpclaim -s -d
# Dovrebbe mostrare 2 path per il disco
```

### Autenticazione CHAP

```powershell
# CHAP (Challenge Handshake Authentication Protocol) aggiunge
# autenticazione alla connessione iSCSI.

# ═══════════════ SUL TARGET (SERVER) ═══════════════

# Configurare CHAP sul target
Set-IscsiServerTarget -TargetName "ClusterStorage" `
    -EnableChap $true `
    -Chap (New-Object PSCredential("iqn.1991-05.com.microsoft:node01",
        (ConvertTo-SecureString "S3cretCHAP!Pass12" -AsPlainText -Force)))

# Configurare Reverse CHAP (mutual authentication)
# Il target si autentica anche verso l'initiator
Set-IscsiServerTarget -TargetName "ClusterStorage" `
    -EnableReverseChap $true `
    -ReverseChap (New-Object PSCredential("iqn.target",
        (ConvertTo-SecureString "R3verseS3cret!456" -AsPlainText -Force)))

# ═══════════════ SULL'INITIATOR (CLIENT) ═══════════════

# Connettersi con CHAP
Connect-IscsiTarget -NodeAddress "iqn.1991-05.com.microsoft:storage-clusterstorage" `
    -AuthenticationType OneWayCHAP `
    -ChapUsername "iqn.1991-05.com.microsoft:node01" `
    -ChapSecret "S3cretCHAP!Pass12" `
    -IsPersistent $true

# Connessione con Mutual CHAP
Connect-IscsiTarget -NodeAddress "iqn.1991-05.com.microsoft:storage-clusterstorage" `
    -AuthenticationType MutualCHAP `
    -ChapUsername "iqn.1991-05.com.microsoft:node01" `
    -ChapSecret "S3cretCHAP!Pass12" `
    -IsPersistent $true

# NOTA SICUREZZA: CHAP usa hash debole (MD5).
# Per ambienti ad alta sicurezza, usare IPsec in aggiunta a CHAP.
# iSCSI su rete dedicata/VLAN isolata è raccomandato comunque.
```

---

## Fibre Channel

### Configurazione HBA

Fibre Channel (FC) è un protocollo di trasporto ad alte prestazioni per storage SAN. Richiede hardware dedicato: HBA (Host Bus Adapter) nel server, switch FC, e storage array FC.

```
Architettura Fibre Channel:
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Server 1 │     │ FC Switch│     │ Storage  │
│ ┌──────┐ │     │ (Fabric) │     │ Array    │
│ │ HBA  │─┼─────┤          ├─────┤          │
│ │ Port │ │     │ Zone A   │     │ Port 1   │
│ └──────┘ │     │          │     │          │
│ ┌──────┐ │     │          │     │          │
│ │ HBA  │─┼─────┤          ├─────┤ Port 2   │
│ │ Port │ │     │ Zone B   │     │          │
│ └──────┘ │     └──────────┘     │ LUN 0    │
└──────────┘                      │ LUN 1    │
                                  │ LUN 2    │
                                  └──────────┘

Topologie FC:
├── Point-to-Point: connessione diretta server-storage
├── Arbitrated Loop (FC-AL): anello condiviso (legacy, raro)
└── Switched Fabric: switch FC dedicato (standard enterprise)

Velocità FC:
├── 8 Gbps (8GFC)
├── 16 Gbps (16GFC)
├── 32 Gbps (32GFC)
└── 64 Gbps (64GFC, più recente)
```

```powershell
# Verificare HBA installati nel server
Get-InitiatorPort | Where-Object ConnectionType -eq "Fibre Channel"
# Output: NodeAddress (WWNN), PortAddress (WWPN), OperationalStatus

# Informazioni dettagliate sulle porte FC
Get-InitiatorPort | Select-Object NodeAddress, PortAddress,
    ConnectionType, OperationalStatus, InstanceName

# WWPN (World Wide Port Name) è l'identificatore unico della porta HBA
# Formato: xx:xx:xx:xx:xx:xx:xx:xx (8 byte esadecimali)
# Necessario per configurare zoning e LUN masking sullo storage array

# Con fcinfo.exe (tool legacy):
# fcinfo /details

# Visualizzare dischi FC connessi
Get-Disk | Where-Object BusType -eq "Fibre Channel" |
    Select-Object Number, FriendlyName, Size, OperationalStatus

# Configurare MPIO per FC (stessa procedura di iSCSI)
Enable-MSDSMAutomaticClaim -BusType "Fibre Channel"
# Richiede REBOOT

# Dopo configurazione zoning sullo switch e LUN masking sull'array:
# 1. Eseguire rescan dischi
Update-HostStorageCache

# 2. I nuovi LUN appariranno come dischi
Get-Disk | Where-Object BusType -eq "Fibre Channel"

# 3. Inizializzare e formattare
Initialize-Disk -Number 2 -PartitionStyle GPT
```

### Zoning e LUN Mapping

```
Zoning FC — Configurato sullo switch FC (non su Windows):
Il zoning limita quali dispositivi possono comunicare sulla fabric.

Tipi di zoning:
├── Soft Zoning (basato su WWPN)
│   ├── Più flessibile (non dipende dalla porta fisica)
│   ├── Un dispositivo spostato su altra porta mantiene l'accesso
│   └── Standard attuale, raccomandato
├── Hard Zoning (basato su porta dello switch)
│   ├── Più sicuro (legato alla porta fisica)
│   ├── Se il dispositivo si sposta, perde l'accesso
│   └── Usato in ambienti ad altissima sicurezza
└── Mixed Zoning: combinazione (evitare se possibile)

Best practices zoning:
1. Una zona per ogni coppia initiator-target port
2. Non raggruppare più di un initiator per zona (per isolamento)
3. Usare alias per WWPN (leggibilità)
4. Documentare ogni zona con scopo e proprietario

LUN Masking — Configurato sullo storage array:
Il LUN masking limita quali initiator (WWPN) possono accedere a quali LUN.

Workflow tipico:
1. Annotare WWPN di ogni HBA port del server Windows
   (Get-InitiatorPort | Where-Object ConnectionType -eq "Fibre Channel")
2. Configurare zoning sullo switch FC per permettere comunicazione
   tra WWPN del server e porta dello storage
3. Configurare LUN masking sullo storage array:
   mappare i WWPN del server ai LUN specifici
4. Eseguire rescan sul server Windows:
   Update-HostStorageCache
5. Inizializzare i nuovi dischi che appaiono in Windows
```

---

## SMB File Share

### NTFS vs Share Permissions

```
Due livelli di permessi controllano l'accesso ai file condivisi via SMB:

1. Share Permissions (Permessi di condivisione):
   - Applicati SOLO all'accesso di rete (via \\server\share)
   - NON applicati all'accesso locale
   - Granularità limitata: Read, Change, Full Control
   - Applicati alla root dello share, ereditati in basso

2. NTFS Permissions (Permessi del filesystem):
   - Applicati sia all'accesso locale che di rete
   - Granularità fine: Read, Write, Execute, Modify, Full Control,
     Special permissions (attributi, permessi, ownership...)
   - Ereditarietà configurabile per file/cartella/sottocartella

Regola di combinazione:
┌──────────────────────────────────────────────────────────┐
│ Accesso di rete = INTERSEZIONE (più restrittivo) tra     │
│ Share Permissions e NTFS Permissions                     │
│                                                          │
│ Esempio:                                                 │
│ Share Permission: Read                                   │
│ NTFS Permission:  Full Control                           │
│ Risultato accesso rete: Read (il più restrittivo vince)  │
│                                                          │
│ Accesso locale = Solo NTFS Permissions (share ignorato)  │
└──────────────────────────────────────────────────────────┘

Best practice:
- Share permissions: impostare "Everyone → Full Control"
  (o "Authenticated Users → Change" come baseline)
- Controllare l'accesso effettivo SOLO con NTFS permissions
- Motivo: NTFS permissions sono più granulari e applicabili
  sia in locale che in rete. Gestire due livelli complica
  la troubleshooting.
```

```powershell
# ═══════════════════════════════════════════════════════════
# CREAZIONE SMB SHARE
# ═══════════════════════════════════════════════════════════

# Creare share di base
New-SmbShare -Name "SharedData" -Path "D:\SharedData" `
    -FullAccess "CORP\Domain Admins" `
    -ChangeAccess "CORP\Data-Writers" `
    -ReadAccess "CORP\Data-Readers" `
    -Description "Condivisione dati dipartimento"

# Share con Everyone Full Control (controllo accesso solo via NTFS)
New-SmbShare -Name "Projects" -Path "D:\Projects" `
    -FullAccess "Everyone" `
    -Description "Progetti — accesso controllato da NTFS"

# Modificare permessi share esistente
Grant-SmbShareAccess -Name "SharedData" -AccountName "CORP\NewGroup" `
    -AccessRight Change -Force

# Revocare accesso
Revoke-SmbShareAccess -Name "SharedData" -AccountName "CORP\OldGroup" -Force

# Elencare share
Get-SmbShare | Select-Object Name, Path, Description, CurrentUsers

# Elencare permessi di uno share
Get-SmbShareAccess -Name "SharedData"

# ═══════════════════════════════════════════════════════════
# NTFS PERMISSIONS (ACL)
# ═══════════════════════════════════════════════════════════

# Visualizzare ACL
Get-Acl "D:\SharedData" | Format-List

# Visualizzare ACL in formato leggibile
(Get-Acl "D:\SharedData").Access | Select-Object IdentityReference,
    FileSystemRights, AccessControlType, IsInherited, InheritanceFlags

# Aggiungere permesso NTFS
$acl = Get-Acl "D:\SharedData"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CORP\Data-Writers",
    "Modify",
    "ContainerInherit,ObjectInherit",
    "None",
    "Allow"
)
$acl.AddAccessRule($rule)
Set-Acl "D:\SharedData" $acl

# Rimuovere ereditarietà e copiare permessi espliciti
$acl = Get-Acl "D:\SharedData"
$acl.SetAccessRuleProtection($true, $true)  # ($disableInheritance, $copyPermissions)
Set-Acl "D:\SharedData" $acl

# Impostare proprietario
$acl = Get-Acl "D:\SharedData"
$acl.SetOwner([System.Security.Principal.NTAccount]"CORP\Admin")
Set-Acl "D:\SharedData" $acl

# Con icacls (cmd):
# icacls "D:\SharedData" /grant "CORP\Data-Writers:(OI)(CI)M"
# icacls "D:\SharedData" /remove "CORP\OldGroup"
# icacls "D:\SharedData" /inheritance:d    # Disabilita ereditarietà
# icacls "D:\SharedData" /reset /T         # Reset ACL ricorsivo
```

### Access Based Enumeration (ABE)

```
ABE nasconde agli utenti i file e le cartelle a cui non hanno
permesso di accesso. Senza ABE, un utente vede tutti i file
nello share ma riceve "Access Denied" quando tenta di aprire
quelli non autorizzati. Con ABE, vede solo ciò a cui ha accesso.

Benefici:
✓ Riduce confusione utente
✓ Riduce chiamate all'help desk
✓ Sicurezza per oscurità (complementare, non sostitutiva)
✓ Interfaccia più pulita per l'utente

Considerazioni:
✗ Leggero overhead di performance (verifica ACL su ogni enumarazione)
✗ Non un sostituto per ACL corrette
✗ Funziona solo per accesso di rete (non locale sul server)
```

```powershell
# Abilitare ABE su uno share
Set-SmbShare -Name "SharedData" -FolderEnumerationMode AccessBased -Force

# Verificare ABE
Get-SmbShare -Name "SharedData" | Select-Object Name, FolderEnumerationMode

# Disabilitare ABE
Set-SmbShare -Name "SharedData" -FolderEnumerationMode Unrestricted -Force

# ABE alla creazione dello share
New-SmbShare -Name "HR-Data" -Path "D:\HR" `
    -FullAccess "CORP\HR-Admins" `
    -ReadAccess "CORP\HR-Staff" `
    -FolderEnumerationMode AccessBased
```

### SMB 3.x — Funzionalità Avanzate

```powershell
# ═══════════════════════════════════════════════════════════
# SMB ENCRYPTION E SIGNING
# ═══════════════════════════════════════════════════════════

# Abilitare encryption su share specifico (SMB 3.0+)
Set-SmbShare -Name "Confidential" -EncryptData $true -Force

# Abilitare encryption globale su tutto il server
Set-SmbServerConfiguration -EncryptData $true -Force

# Richiedere signing per tutte le connessioni
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force

# Verificare configurazione
Get-SmbServerConfiguration | Select-Object EncryptData,
    RequireSecuritySignature, EnableSMB1Protocol, EnableSMB2Protocol

# ═══════════════════════════════════════════════════════════
# SMB — ALTRE CONFIGURAZIONI
# ═══════════════════════════════════════════════════════════

# Disabilitare SMBv1 (SICUREZZA: SMBv1 è vulnerabile a EternalBlue/WannaCry)
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol

# Verificare versione SMB in uso
Get-SmbConnection | Select-Object ServerName, ShareName, Dialect

# Sessioni SMB attive
Get-SmbSession | Select-Object ClientComputerName, ClientUserName,
    NumOpens, SecondsExists, Dialect

# File aperti
Get-SmbOpenFile | Select-Object ClientComputerName, ClientUserName,
    Path, ShareRelativePath

# Chiudere sessione o file aperto
Close-SmbSession -SessionId 1234 -Force
Close-SmbOpenFile -FileId 5678 -Force

# Continuosly Available Share (per Hyper-V over SMB, SQL over SMB)
New-SmbShare -Name "HyperV-Storage" -Path "D:\VMs" `
    -FullAccess "CORP\HyperV-Nodes$" `
    -ContinuouslyAvailable $true `
    -EncryptData $true

# Bandwidth limits (QoS per SMB)
# Limitare bandwidth per categoria di traffico
Set-SmbBandwidthLimit -Category Default -BytesPerSecond 500MB
Set-SmbBandwidthLimit -Category VirtualMachine -BytesPerSecond 1GB
Set-SmbBandwidthLimit -Category LiveMigration -BytesPerSecond 750MB

Get-SmbBandwidthLimit
```

---

## DFS — Distributed File System

### DFS Namespaces

DFS Namespace fornisce un percorso UNC virtuale unificato (`\\domain\namespace`) che mappa a share fisici su server diversi. Gli utenti vedono una struttura logica, non i percorsi reali.

```
Architettura DFS Namespace:
┌──────────────────────────────────────────────────────────────┐
│ Utente accede a: \\corp.contoso.com\Public\HR               │
│                                                              │
│ DFS risolve a:                                               │
│                                                              │
│ \\corp.contoso.com\Public   (namespace root)                 │
│ ├── \HR         → \\FileServer1\HR-Share                     │
│ ├── \Finance    → \\FileServer2\Finance-Share                │
│ ├── \Projects   → \\FileServer3\Projects-Share               │
│ └── \Archive    → \\FileServer4\Archive-Share                │
│                                                              │
│ L'utente non sa su quale server risiedono fisicamente i dati │
│                                                              │
│ Tipi di namespace:                                           │
│ ├── Domain-based: \\dominio\namespace (replicato in AD)      │
│ │   ├── Failover automatico tra namespace server             │
│ │   ├── Limitato a ~5000 folder con target                   │
│ │   └── Richiede Active Directory                            │
│ └── Standalone: \\server\namespace                           │
│     ├── Nessun failover automatico (SPOF)                    │
│     ├── Nessun limite folder target                          │
│     └── Non richiede AD                                      │
└──────────────────────────────────────────────────────────────┘
```

```powershell
# ═══════════════════════════════════════════════════════════
# INSTALLAZIONE E CONFIGURAZIONE DFS NAMESPACES
# ═══════════════════════════════════════════════════════════

# Installare ruolo DFS
Install-WindowsFeature FS-DFS-Namespace, FS-DFS-Replication -IncludeManagementTools
# Installa anche RSAT-DFS-Mgmt-Con

# Creare namespace domain-based
New-DfsnRoot -TargetPath "\\FileServer1\DFSRoot" `
    -Path "\\corp.contoso.com\Public" `
    -Type DomainV2    # V2 = Windows Server 2008 mode (consigliato)

# Aggiungere cartelle al namespace
New-DfsnFolder -Path "\\corp.contoso.com\Public\HR" `
    -TargetPath "\\FileServer1\HR-Share"

New-DfsnFolder -Path "\\corp.contoso.com\Public\Finance" `
    -TargetPath "\\FileServer2\Finance-Share"

# Aggiungere target aggiuntivo (failover/load balancing)
New-DfsnFolderTarget -Path "\\corp.contoso.com\Public\HR" `
    -TargetPath "\\FileServer2\HR-Share-Replica"

# Verificare namespace
Get-DfsnRoot -Path "\\corp.contoso.com\Public"
Get-DfsnFolder -Path "\\corp.contoso.com\Public\*"
Get-DfsnFolderTarget -Path "\\corp.contoso.com\Public\HR"

# Configurare ordinamento referral (priorità target)
Set-DfsnFolderTarget -Path "\\corp.contoso.com\Public\HR" `
    -TargetPath "\\FileServer1\HR-Share" `
    -ReferralPriorityClass GlobalHigh

# Rimuovere folder dal namespace
Remove-DfsnFolder -Path "\\corp.contoso.com\Public\OldFolder"

# Rimuovere target specifico
Remove-DfsnFolderTarget -Path "\\corp.contoso.com\Public\HR" `
    -TargetPath "\\FileServer2\HR-Share-Replica"
```

### DFS Replication

DFS Replication (DFS-R) replica file tra server, mantenendo i contenuti sincronizzati. Usa compressione differenziale (RDC — Remote Differential Compression) per trasferire solo i delta.

```
Architettura DFS Replication:
┌──────────────────────────────────────────────────────────────┐
│                  Replication Group                            │
│                                                              │
│  ┌────────────┐    RDC (delta)    ┌────────────┐            │
│  │ Member A   │ ←───────────────→ │ Member B   │            │
│  │ FS1:\HR    │                   │ FS2:\HR    │            │
│  └────────────┘                   └────────────┘            │
│        ↑                                ↑                   │
│        │          RDC (delta)           │                   │
│        └──────────────┐  ┌──────────────┘                   │
│                       ↓  ↓                                  │
│                 ┌────────────┐                               │
│                 │ Member C   │                               │
│                 │ FS3:\HR    │                               │
│                 └────────────┘                               │
│                                                              │
│ Topologia:                                                   │
│ ├── Hub and Spoke: un server centrale, repliche in spoke     │
│ ├── Full Mesh: tutti replicano con tutti                     │
│ └── Custom: connessioni specifiche tra coppie                │
│                                                              │
│ Caratteristiche:                                             │
│ ├── RDC: trasferisce solo i byte cambiati (non file interi)  │
│ ├── Compressione cross-file: rileva blocchi simili tra file   │
│ ├── Scheduling: replica in finestre temporali specifiche     │
│ ├── Bandwidth throttling: limita banda usata dalla replica   │
│ ├── Conflict resolution: file con timestamp più recente vince│
│ └── Staging: area temporanea per file in fase di replica     │
└──────────────────────────────────────────────────────────────┘
```

```powershell
# ═══════════════════════════════════════════════════════════
# CONFIGURAZIONE DFS REPLICATION
# ═══════════════════════════════════════════════════════════

# Creare replication group
New-DfsReplicationGroup -GroupName "HR-Replication" |
    New-DfsReplicatedFolder -FolderName "HR-Data" |
    Add-DfsrMember -ComputerName "FileServer1", "FileServer2"

# Aggiungere connessione tra i member
Add-DfsrConnection -GroupName "HR-Replication" `
    -SourceComputerName "FileServer1" `
    -DestinationComputerName "FileServer2"

# Impostare percorso locale della cartella replicata
Set-DfsrMembership -GroupName "HR-Replication" -FolderName "HR-Data" `
    -ComputerName "FileServer1" -ContentPath "D:\HR-Data" `
    -PrimaryMember $true    # Primo membro = sorgente iniziale

Set-DfsrMembership -GroupName "HR-Replication" -FolderName "HR-Data" `
    -ComputerName "FileServer2" -ContentPath "D:\HR-Data-Replica"

# Configurare staging quota (area temporanea, default 4 GB)
Set-DfsrMembership -GroupName "HR-Replication" -FolderName "HR-Data" `
    -ComputerName "FileServer1" -StagingPathQuotaInMB 16384  # 16 GB

# Configurare scheduling (replica solo in orari specifici)
Set-DfsrConnectionSchedule -GroupName "HR-Replication" `
    -SourceComputerName "FileServer1" `
    -DestinationComputerName "FileServer2" `
    -Day Monday,Tuesday,Wednesday,Thursday,Friday `
    -BandwidthDetail Full    # O: 16kbps, 64kbps, 128kbps, 256kbps, 512kbps, etc.

# Verificare stato replication group
Get-DfsReplicationGroup
Get-DfsReplicatedFolder -GroupName "HR-Replication"
Get-DfsrMember -GroupName "HR-Replication"

# Report salute replica
Get-DfsrBacklog -GroupName "HR-Replication" -FolderName "HR-Data" `
    -SourceComputerName "FileServer1" -DestinationComputerName "FileServer2"
# Output: numero di file in attesa di replica (backlog)

# Report diagnostico completo
Write-DfsrHealthReport -GroupName "HR-Replication" `
    -ReferenceComputerName "FileServer1" -Path "C:\Reports"
```

### Troubleshooting DFS

```powershell
# ═══════════════════════════════════════════════════════════
# DIAGNOSTICA E RISOLUZIONE PROBLEMI DFS
# ═══════════════════════════════════════════════════════════

# Verificare stato namespace
dfsdiag /TestDCs /Domain:corp.contoso.com
dfsdiag /TestSites /Machine:FileServer1
dfsdiag /TestDFSConfig /DFSRoot:\\corp.contoso.com\Public
dfsdiag /TestDFSIntegrity /DFSRoot:\\corp.contoso.com\Public

# Backlog replica (file non ancora replicati)
Get-DfsrBacklog -GroupName "HR-Replication" -FolderName "HR-Data" `
    -SourceComputerName "FileServer1" -DestinationComputerName "FileServer2" `
    -Verbose
# Backlog alto = replica lenta o bloccata

# Stato connessione DFS-R
Get-DfsrConnectionSchedule -GroupName "HR-Replication" `
    -SourceComputerName "FileServer1" `
    -DestinationComputerName "FileServer2"

# Log eventi DFS-R
Get-WinEvent -LogName "DFS Replication" -MaxEvents 50 |
    Select-Object TimeCreated, Id, LevelDisplayName, Message

# Conflitti di replica (file con modifiche concorrenti)
# I file in conflitto vanno nella cartella ConflictAndDeleted
Get-DfsrConflictInfo -GroupName "HR-Replication" -FolderName "HR-Data" `
    -ComputerName "FileServer1"

# Forzare replica immediata
Sync-DfsReplicationGroup -GroupName "HR-Replication" -SourceComputerName "FileServer1" `
    -DestinationComputerName "FileServer2" -DurationInMinutes 15

# Reset del database DFS-R su un member (ultima risorsa)
# ATTENZIONE: forza re-sync completa
# Suspend-DfsReplicationGroup -GroupName "HR-Replication" -ComputerName "FileServer2"
# Rimuovere contenuto database in:
# C:\System Volume Information\DFSR\...
# Resume-DfsReplicationGroup -GroupName "HR-Replication" -ComputerName "FileServer2"
```

---

## Deduplicazione Dati

### Configurazione Deduplicazione

La deduplicazione elimina blocchi di dati duplicati, risparmiando spazio disco. Opera a livello di sub-file (blocchi di dimensione variabile, tipicamente 32-128 KB).

```
Funzionamento:
┌──────────────────────────────────────────────────────────┐
│ File originali:                                          │
│ FileA.docx: [A1][A2][A3][A4][A5]                       │
│ FileB.docx: [B1][A2][B3][A4][B5]                       │
│ FileC.docx: [C1][A2][C3][A4][C5]                       │
│ Blocchi totali: 15                                       │
│                                                          │
│ Dopo deduplicazione:                                     │
│ Chunk Store: [A1][A2][A3][A4][A5][B1][B3][B5][C1][C3][C5]│
│ Blocchi unici: 11 (A2 e A4 appaiono una volta sola)     │
│                                                          │
│ FileA → pointer: A1, A2, A3, A4, A5                     │
│ FileB → pointer: B1, A2, B3, A4, B5                     │
│ FileC → pointer: C1, A2, C3, A4, C5                     │
│                                                          │
│ Risparmio: ~27% (in pratica, molto più alto per file     │
│ simili come documenti Office, VM, backup)                │
└──────────────────────────────────────────────────────────┘
```

```powershell
# Installare feature
Install-WindowsFeature FS-Data-Deduplication -IncludeManagementTools

# Abilitare su un volume
Enable-DedupVolume -Volume "D:" -UsageType Default

# Configurare parametri
Set-DedupVolume -Volume "D:" -MinimumFileAgeDays 3 `
    -MinimumFileSize 32768  # 32 KB minimum

# Esclusioni (cartelle)
Set-DedupVolume -Volume "D:" -ExcludeFolder "D:\Database", "D:\Temp"

# Esclusioni (tipi file)
Set-DedupVolume -Volume "D:" -ExcludeFileType ".bak", ".vhdx", ".mp4"
```

### Impostazioni per Workload

```powershell
# ═══════════════════════════════════════════════════════════
# USAGE TYPE — OTTIMIZZAZIONE PER WORKLOAD
# ═══════════════════════════════════════════════════════════

# DEFAULT — File Server generale
Enable-DedupVolume -Volume "D:" -UsageType Default
# - MinimumFileAgeDays: 3
# - Ottimizzazione in background con priorità bassa
# - Ideale per: documenti, home folder, share di progetto

# HYPER-V — VDI (Virtual Desktop Infrastructure)
Enable-DedupVolume -Volume "E:" -UsageType HyperV
# - MinimumFileAgeDays: 3
# - Ottimizzato per file VHD/VHDX
# - Esclude automaticamente file in uso attivo dalle VM
# - NOTA: usare SOLO per VDI, non per VM server generiche

# BACKUP — Target di backup
Enable-DedupVolume -Volume "F:" -UsageType Backup
# - MinimumFileAgeDays: 0 (dedup immediata)
# - Priorità più alta per ottimizzazione
# - Ottimizzato per pattern di backup (molte versioni simili)
# - Ideale per: DPM, VEEAM, Windows Server Backup target

# Verificare configurazione corrente
Get-DedupVolume | Select-Object Volume, Enabled, UsageType,
    MinimumFileAgeDays, MinimumFileSize,
    @{N='SavedSpace_GB';E={[math]::Round($_.SavedSpace/1GB,2)}},
    @{N='SavingsRate';E={$_.SavingsRate}}

# ═══════════════════════════════════════════════════════════
# SCHEDULING OTTIMIZZAZIONE
# ═══════════════════════════════════════════════════════════

# Schedule personalizzato (ottimizzazione notturna)
Set-DedupSchedule -Name "NightlyOptimization" -Type Optimization `
    -Days Monday,Tuesday,Wednesday,Thursday,Friday `
    -Start "22:00" -DurationHours 6 -Priority Normal

# Schedule garbage collection (pulizia chunk non referenziati)
Set-DedupSchedule -Name "WeeklyGC" -Type GarbageCollection `
    -Days Saturday -Start "03:00" -DurationHours 4 -Priority Normal

# Schedule scrubbing (verifica integrità)
Set-DedupSchedule -Name "WeeklyScrub" -Type Scrubbing `
    -Days Sunday -Start "03:00" -DurationHours 4 -Priority Normal

# Visualizzare schedule
Get-DedupSchedule

# Forzare ottimizzazione manuale
Start-DedupJob -Volume "D:" -Type Optimization -Full
```

### Monitoraggio e Ottimizzazione Dedup

```powershell
# Stato e statistiche
Get-DedupStatus -Volume "D:" | Select-Object Volume,
    @{N='SavedSpace_GB';E={[math]::Round($_.SavedSpace/1GB,2)}},
    OptimizedFilesCount, InPolicyFilesCount,
    OptimizedFilesSavingsRate, LastOptimizationTime

# Dettagli completi
Get-DedupVolume -Volume "D:" | Format-List *

# Monitoraggio job in corso
Get-DedupJob | Select-Object Volume, Type, Progress, State

# Verifica integrità chunk store
Start-DedupJob -Volume "D:" -Type Scrubbing

# Report metadati dedup
Get-DedupMetadata -Volume "D:" | Select-Object Volume,
    DataChunkCount, DataContainerCount, DataStoreSize,
    UnoptimizedSize, OptimizedSize, SavingsPercent

# Quando la dedup NON funziona bene:
# - File già compressi (ZIP, JPEG, MP4, criptati): rapporto dedup molto basso
# - Database attivi: I/O overhead, escludere con ExcludeFolder
# - File < MinimumFileSize: ignorati dalla dedup
# - File < MinimumFileAgeDays: non ancora processati
```

---

## Data Tiering e SSD Caching

```
Strategie di tiering storage su Windows Server:

1. Storage Spaces Tiers (descritto nella sezione Storage Spaces)
   - Tier SSD + Tier HDD nello stesso virtual disk
   - Promozione/demozione automatica basata su access pattern
   - Task schedulato analizza e sposta blocchi

2. Write-Back Cache (Storage Spaces)
   - SSD dedicato come buffer di scrittura
   - Le scritture vanno prima sulla cache SSD
   - Vengono flushate sui dischi capacity in background
   - Riduce latenza write significativamente

3. Storage Spaces Direct Cache
   - NVMe come cache per SSD/HDD capacity
   - SSD come cache per HDD capacity
   - Cache automatica read + write
   - Binding 1:1 o 1:2 tra cache e capacity disk

4. ReadyBoost (solo client, non server)
   - USB flash drive come cache di lettura
   - Non rilevante per ambienti server
```

```powershell
# Configurazione Write-Back Cache (Storage Spaces)
# Dimensione consigliata: 2-5% della capacità del virtual disk

# Impostare cache durante creazione virtual disk
New-VirtualDisk -StoragePoolFriendlyName "DataPool" -FriendlyName "CachedDisk" `
    -ResiliencySettingName Mirror -Size 1TB `
    -ProvisioningType Thin -WriteCacheSize 10GB

# Modificare cache su virtual disk esistente
Set-VirtualDisk -FriendlyName "CachedDisk" -WriteCacheSize 20GB

# Verificare dimensione cache
Get-VirtualDisk -FriendlyName "CachedDisk" |
    Select-Object FriendlyName, WriteCacheSize

# Configurazione S2D Cache (automatica se tipi di disco misti)
# Cache binding: visualizzare quale disco cache serve quale capacity
Get-PhysicalDisk | Select-Object FriendlyName, MediaType, Usage,
    @{N='Size_GB';E={[math]::Round($_.Size/1GB,2)}}
# Usage = "Journal" o "Auto-Select" = cache
# Usage = "Auto-Select" (capacity) per dischi capacity
```

---

## Storage Monitoring

### Performance Monitor — Contatori Storage

```
Contatori chiave per monitoraggio storage:

Physical Disk:
├── % Disk Time               → Percentuale tempo disco occupato
├── % Idle Time                → Tempo inattivo (basso = disco saturo)
├── Avg. Disk sec/Read         → Latenza media lettura
├── Avg. Disk sec/Write        → Latenza media scrittura
├── Avg. Disk Queue Length     → Coda I/O media (alto = collo di bottiglia)
├── Disk Reads/sec             → IOPS lettura
├── Disk Writes/sec            → IOPS scrittura
├── Disk Bytes/sec             → Throughput totale
├── Current Disk Queue Length  → Coda I/O istantanea
└── Split IO/Sec               → I/O frammentati (frammentazione disco)

Logical Disk:
├── % Free Space               → Spazio libero percentuale
├── Free Megabytes             → Spazio libero assoluto
├── Avg. Disk sec/Transfer     → Latenza media I/O
└── Disk Transfers/sec         → IOPS totali

Soglie di allarme:
┌──────────────────────────┬──────────────────────────────────┐
│ Metrica                  │ Soglia di allarme                │
├──────────────────────────┼──────────────────────────────────┤
│ Avg Disk sec/Read        │ > 15 ms (HDD), > 5 ms (SSD)     │
│ Avg Disk sec/Write       │ > 15 ms (HDD), > 5 ms (SSD)     │
│ Avg Disk Queue Length    │ > 2 per spindle/disco            │
│ % Free Space             │ < 20% warning, < 10% critical   │
│ % Disk Time              │ > 80% sostenuto = bottleneck     │
└──────────────────────────┴──────────────────────────────────┘
```

```powershell
# Raccogliere contatori performance con PowerShell
Get-Counter '\PhysicalDisk(*)\Avg. Disk sec/Read',
    '\PhysicalDisk(*)\Avg. Disk sec/Write',
    '\PhysicalDisk(*)\Avg. Disk Queue Length',
    '\PhysicalDisk(*)\Disk Reads/sec',
    '\PhysicalDisk(*)\Disk Writes/sec'

# Monitoraggio continuo (campione ogni 5 secondi, 60 campioni)
Get-Counter '\PhysicalDisk(*)\Avg. Disk sec/Read',
    '\PhysicalDisk(*)\Avg. Disk sec/Write' `
    -SampleInterval 5 -MaxSamples 60

# Spazio libero su tutti i volumi
Get-Volume | Where-Object DriveLetter | Select-Object DriveLetter,
    FileSystemLabel, FileSystem,
    @{N='Size_GB';E={[math]::Round($_.Size/1GB,2)}},
    @{N='Free_GB';E={[math]::Round($_.SizeRemaining/1GB,2)}},
    @{N='FreePct';E={[math]::Round(($_.SizeRemaining/$_.Size)*100,1)}}

# Alert spazio basso (script per monitoring)
Get-Volume | Where-Object {$_.DriveLetter -and $_.Size -gt 0} | ForEach-Object {
    $freePct = ($_.SizeRemaining / $_.Size) * 100
    if ($freePct -lt 10) {
        Write-Warning "CRITICAL: Volume $($_.DriveLetter): ha solo $([math]::Round($freePct,1))% libero"
    } elseif ($freePct -lt 20) {
        Write-Warning "WARNING: Volume $($_.DriveLetter): ha $([math]::Round($freePct,1))% libero"
    }
}

# Esportare contatori in CSV per analisi
Get-Counter '\PhysicalDisk(*)\*' -SampleInterval 10 -MaxSamples 360 |
    Export-Counter -Path "C:\Logs\DiskPerf.csv" -FileFormat CSV -Force
```

### Storage Reports e FSRM

```powershell
# ═══════════════════════════════════════════════════════════
# FSRM — FILE SERVER RESOURCE MANAGER
# ═══════════════════════════════════════════════════════════

# Installare FSRM
Install-WindowsFeature FS-Resource-Manager -IncludeManagementTools

# FSRM fornisce:
# - Quota management (soft/hard)
# - File screening (blocco tipi file)
# - Storage reports
# - File classification
# - File management tasks (azioni automatiche su file)

# Generare report storage on-demand
New-FsrmStorageReport -Name "DiskUsageReport" `
    -Namespace "D:\" `
    -ReportType DuplicateFiles, LargeFiles, FilesByOwner `
    -LargeFileMinimum 100MB `
    -Interactive

# Tipi di report disponibili:
# - DuplicateFiles: file duplicati
# - FilesByFileGroup: file per gruppo (es. audio, video, documenti)
# - FilesByOwner: spazio per proprietario
# - FileScreenAudit: violazioni file screen
# - LargeFiles: file sopra la soglia
# - LeastRecentlyAccessed: file non acceduti da lungo tempo
# - MostRecentlyAccessed: file acceduti recentemente
# - QuotaUsage: utilizzo quota

# Schedulare report ricorrente
New-FsrmScheduledTask -Time "03:00" -Monthly 1 |
    New-FsrmStorageReport -Name "MonthlyReport" `
        -Namespace "D:\" `
        -ReportType FilesByOwner, LargeFiles

# File Screening — bloccare tipi di file
New-FsrmFileScreen -Path "D:\SharedData" `
    -Template "Block Audio and Video Files"

# File Screen personalizzato
New-FsrmFileGroup -Name "Executable Files" -IncludePattern "*.exe","*.msi","*.bat","*.cmd"
New-FsrmFileScreen -Path "D:\SharedData" `
    -IncludeGroup "Executable Files" -Active   # Active = hard block
```

### Get-StorageHealth e Diagnostica

```powershell
# ═══════════════════════════════════════════════════════════
# DIAGNOSTICA STORAGE
# ═══════════════════════════════════════════════════════════

# Health Report (Storage Spaces / S2D)
Get-StorageSubSystem | Get-StorageHealthReport

# Stato di tutti i subsystem
Get-StorageSubSystem | Select-Object FriendlyName, HealthStatus,
    OperationalStatus, Model, Manufacturer

# Stato dischi con errori SMART (Self-Monitoring, Analysis and Reporting Technology)
Get-PhysicalDisk | Select-Object FriendlyName, MediaType,
    HealthStatus, OperationalStatus,
    @{N='Size_GB';E={[math]::Round($_.Size/1GB,2)}},
    @{N='Reliability';E={
        $counters = $_ | Get-StorageReliabilityCounter
        if ($counters) { "Wear: $($counters.Wear)%, Errors: $($counters.ReadErrorsTotal)" }
        else { "N/A" }
    }}

# Contatori affidabilità dettagliati per disco
Get-PhysicalDisk | ForEach-Object {
    $disk = $_
    $rel = $_ | Get-StorageReliabilityCounter
    if ($rel) {
        [PSCustomObject]@{
            Disk = $disk.FriendlyName
            Temperature = $rel.Temperature
            Wear = $rel.Wear
            ReadErrorsTotal = $rel.ReadErrorsTotal
            WriteErrorsTotal = $rel.WriteErrorsTotal
            PowerOnHours = $rel.PowerOnHours
        }
    }
}

# Verificare integrità NTFS
# chkdsk D: /scan   # Scan online (non blocca il volume)
# chkdsk D: /f      # Fix errori (richiede volume offline o reboot per C:)
# chkdsk D: /r      # Repair + verifica settori difettosi (lungo)
# chkdsk D: /v      # Verbose

# PowerShell equivalente:
Repair-Volume -DriveLetter D -Scan              # Solo scan
Repair-Volume -DriveLetter D -SpotFix           # Fix online (Server 2012+)
Repair-Volume -DriveLetter D -OfflineScanAndFix # Fix offline

# Verificare integrità ReFS
Repair-Volume -DriveLetter E -Scan    # ReFS ha auto-repair con Storage Spaces

# Storage Diagnostic Log
Get-StorageDiagnosticInfo -StorageSubSystemFriendlyName "Windows Storage*" `
    -DestinationPath "C:\Logs\StorageDiag" -IncludeLiveDump
```

---

## Disk Quotas

### Quote NTFS Native

Le quote NTFS native sono gestite a livello di volume e tracciano l'utilizzo per utente.

```powershell
# Abilitare tracciamento quota su un volume
fsutil quota track D:

# Impostare quota per utente
# Parametri: volume, hard limit (byte), warning level (byte), utente
fsutil quota modify D: 5368709120 4294967296 corp\mrossi
# Warning: 4 GB, Limit: 5 GB

# Impostare quota di default per tutti i nuovi utenti
fsutil quota defaults D: 5368709120 4294967296
# Warning: 4 GB, Limit: 5 GB per tutti i nuovi utenti

# Verificare quota di un utente
fsutil quota query D: corp\mrossi

# Elencare tutte le quote
fsutil quota query D:

# Abilitare enforcement (hard limit)
fsutil quota enforce D:

# Disabilitare enforcement (solo tracking/warning)
fsutil quota disable D:

# Verificare stato
fsutil quota violations    # Mostra violazioni recenti

# Limitazioni quote NTFS native:
# - Granularità: intero volume (non per cartella)
# - Basate su ownership del file (non su posizione)
# - Non supportano quote per cartella
# - Non supportano notifiche email
# → Per esigenze avanzate: usare FSRM Quotas
```

### Quote FSRM

File Server Resource Manager (FSRM) offre quote più flessibili: per cartella, con notifiche, report, e automazione.

```powershell
# Installare FSRM
Install-WindowsFeature FS-Resource-Manager -IncludeManagementTools

# ═══════════════════════════════════════════════════════════
# QUOTA TEMPLATE (modello riutilizzabile)
# ═══════════════════════════════════════════════════════════

# Creare template quota
New-FsrmQuotaTemplate -Name "10GB User Limit" `
    -Size 10GB `
    -SoftLimit:$false   # Hard limit

# Template con soglie di notifica
$action85 = New-FsrmAction -Type Event -EventType Warning `
    -Body "Quota al 85% per [Source Io Owner] su [Quota Path]"
$action95 = New-FsrmAction -Type Event -EventType Warning `
    -Body "Quota al 95% per [Source Io Owner] su [Quota Path]"
$actionFull = New-FsrmAction -Type Event -EventType Error `
    -Body "Quota PIENA per [Source Io Owner] su [Quota Path]"

$threshold85 = New-FsrmQuotaThreshold -Percentage 85 -Action $action85
$threshold95 = New-FsrmQuotaThreshold -Percentage 95 -Action $action95
$thresholdFull = New-FsrmQuotaThreshold -Percentage 100 -Action $actionFull

New-FsrmQuotaTemplate -Name "10GB with Alerts" `
    -Size 10GB -SoftLimit:$false `
    -Threshold $threshold85, $threshold95, $thresholdFull

# ═══════════════════════════════════════════════════════════
# APPLICARE QUOTA
# ═══════════════════════════════════════════════════════════

# Quota su cartella singola
New-FsrmQuota -Path "D:\Users\mrossi" -Template "10GB User Limit"

# Auto-apply quota (applica automaticamente a tutte le sottocartelle)
New-FsrmAutoQuota -Path "D:\Users" -Template "10GB User Limit"
# Ogni nuova sottocartella di D:\Users riceve la quota automaticamente

# Quota diretta (senza template)
New-FsrmQuota -Path "D:\Projects\BigProject" -Size 50GB -SoftLimit:$false

# ═══════════════════════════════════════════════════════════
# GESTIONE QUOTE
# ═══════════════════════════════════════════════════════════

# Elencare quote attive
Get-FsrmQuota | Select-Object Path, Size, Usage, Template,
    @{N='UsagePct';E={[math]::Round(($_.Usage/$_.Size)*100,1)}}

# Modificare quota
Set-FsrmQuota -Path "D:\Users\mrossi" -Size 20GB

# Rimuovere quota
Remove-FsrmQuota -Path "D:\Users\mrossi"

# Report utilizzo quote
Get-FsrmQuota | Where-Object {($_.Usage / $_.Size) -gt 0.8} |
    Select-Object Path, @{N='Size_GB';E={[math]::Round($_.Size/1GB,2)}},
    @{N='Usage_GB';E={[math]::Round($_.Usage/1GB,2)}},
    @{N='UsagePct';E={[math]::Round(($_.Usage/$_.Size)*100,1)}}
```

### Soft vs Hard Limits

```
┌──────────────────────────────────────────────────────────┐
│ SOFT LIMIT                                               │
│ ├── L'utente PUÒ superare la quota                       │
│ ├── Vengono generate notifiche (event log, email, ecc.)  │
│ ├── Utile per: monitoraggio, pianificazione capacità     │
│ └── L'utente non viene bloccato nella scrittura          │
│                                                          │
│ HARD LIMIT                                               │
│ ├── L'utente NON PUÒ superare la quota                   │
│ ├── Scritture oltre il limite falliscono con errore      │
│ ├── Vengono generate notifiche                           │
│ ├── Utile per: enforcement reale, controllo costi        │
│ └── L'utente riceve "Disk full" quando raggiunge limite  │
└──────────────────────────────────────────────────────────┘

Best practice:
1. Iniziare con soft limit per capire i pattern di utilizzo
2. Passare a hard limit dopo aver stabilito soglie realistiche
3. Configurare notifiche a 85% e 95% per prevenire sorprese
4. Auto-apply quota su cartelle home/utente per gestione automatica
5. Usare FSRM (non NTFS native) per esigenze per-cartella e notifiche
```

---

## Backup Storage

### Windows Server Backup

```powershell
# Installare Windows Server Backup
Install-WindowsFeature Windows-Server-Backup -IncludeManagementTools

# ═══════════════════════════════════════════════════════════
# BACKUP COMPLETO DEL SERVER (BARE METAL RECOVERY)
# ═══════════════════════════════════════════════════════════

# Backup una tantum — server completo su disco dedicato
$backupPolicy = New-WBPolicy
$backupTarget = New-WBBackupTarget -Disk (Get-WBDisk | Where-Object {
    $_.FriendlyName -like "*Backup*"
})
Add-WBBackupTarget -Policy $backupPolicy -Target $backupTarget
Add-WBBareMetalRecovery -Policy $backupPolicy   # Include system state
Start-WBBackup -Policy $backupPolicy

# ═══════════════════════════════════════════════════════════
# BACKUP SCHEDULATO
# ═══════════════════════════════════════════════════════════

# Policy per backup schedulato
$policy = New-WBPolicy

# Aggiungere volumi da backuppare
$volume = Get-WBVolume -AllVolumes | Where-Object MountPoint -eq "D:\"
Add-WBVolume -Policy $policy -Volume $volume

# Aggiungere target (disco dedicato)
$target = New-WBBackupTarget -Disk (Get-WBDisk)[0]
Add-WBBackupTarget -Policy $policy -Target $target

# Oppure: target rete
$cred = Get-Credential
$target = New-WBBackupTarget -NetworkPath "\\BackupServer\Backups" -Credential $cred
Add-WBBackupTarget -Policy $policy -Target $target

# Schedulare (ogni giorno alle 21:00 e alle 06:00)
Set-WBSchedule -Policy $policy -Schedule "21:00","06:00"

# Abilitare bare metal recovery
Add-WBBareMetalRecovery -Policy $policy

# Abilitare system state
Add-WBSystemState -Policy $policy

# Applicare policy
Set-WBPolicy -Policy $policy -Force

# ═══════════════════════════════════════════════════════════
# GESTIONE E RECOVERY
# ═══════════════════════════════════════════════════════════

# Verificare policy corrente
Get-WBPolicy

# Elencare backup disponibili
Get-WBBackupSet

# Stato ultimo backup
Get-WBSummary

# Recovery di file/cartelle
$backup = Get-WBBackupSet | Sort-Object BackupTime -Descending | Select-Object -First 1
Start-WBFileRecovery -BackupSet $backup -SourcePath "D:\Data\ImportantFile.xlsx" `
    -TargetPath "C:\Recovered" -Recursive

# Recovery volume completo
Start-WBVolumeRecovery -BackupSet $backup -VolumeInBackup (
    $backup.Volume | Where-Object MountPoint -eq "D:\"
) -Force

# Recovery system state
Start-WBSystemStateRecovery -BackupSet $backup -Force

# ═══════════════════════════════════════════════════════════
# SHADOW COPY (VSS) — VERSIONI PRECEDENTI
# ═══════════════════════════════════════════════════════════

# Configurare shadow copy storage
vssadmin add shadowstorage /for=D: /on=D: /maxsize=20%

# Creare shadow copy manuale
vssadmin create shadow /for=D:

# Elencare shadow copy
vssadmin list shadows /for=D:

# Eliminare shadow copy
vssadmin delete shadows /for=D: /oldest

# Schedulare shadow copy automatici via Task Scheduler:
# Azione: vssadmin create shadow /for=D:
# Trigger: ogni giorno alle 07:00 e 12:00

# PowerShell: creare VSS snapshot
$shadow = (Get-WmiObject -List Win32_ShadowCopy).Create("D:\","ClientAccessible")
```

### Azure Backup Integration

```powershell
# Azure Backup estende il backup on-premise al cloud.
# Richiede: Azure subscription, Recovery Services vault,
# MARS agent (Microsoft Azure Recovery Services)

# Workflow configurazione:
# 1. Creare Recovery Services vault in Azure Portal
# 2. Scaricare MARS agent dal vault
# 3. Installare l'agent sul server on-premise
# 4. Registrare il server con il vault usando le credenziali scaricate

# Dopo installazione MARS agent, la configurazione è via GUI:
# Microsoft Azure Backup → Schedule Backup / Recover Data

# Vantaggi Azure Backup:
# - Retention a lungo termine (anni) senza gestione tape
# - Crittografia at-rest e in-transit (AES-256)
# - Geo-ridondanza (LRS, GRS, RA-GRS)
# - Ripristino granulare (file, cartelle, volumi, system state)
# - Integrazione con Azure Site Recovery per DR

# Azure Backup per Hyper-V / VM:
# - Azure Backup Server (MABS): backup VM complete
# - Integrazione con System Center DPM
# - Backup application-consistent (SQL, Exchange, SharePoint)

# Monitoraggio via PowerShell (richiede modulo Az.RecoveryServices):
# Get-AzRecoveryServicesBackupJob -VaultId $vault.ID | Select-Object *
# Get-AzRecoveryServicesBackupItem -VaultId $vault.ID -Container $container `
#     -WorkloadType AzureVM

# Costi: pagamento per istanza protetta + storage consumato
# Retention: configurabile da 7 giorni a 99 anni
# RPO: dipende dalla frequenza di backup (minimo 1/giorno per MARS)
```

---

## PowerShell Storage Cmdlets — Riferimento

```powershell
# ═══════════════════════════════════════════════════════════
# RIFERIMENTO RAPIDO CMDLETS STORAGE
# ═══════════════════════════════════════════════════════════

# --- DISCHI ---
Get-Disk                        # Elencare tutti i dischi
Get-Disk -Number 1              # Disco specifico
Initialize-Disk                 # Inizializzare disco (GPT/MBR)
Clear-Disk                      # Pulire disco (rimuove partizioni)
Set-Disk                        # Modificare proprietà (offline, readonly)
Update-Disk                     # Aggiornare info disco

# --- PARTIZIONI ---
Get-Partition                   # Elencare partizioni
New-Partition                   # Creare partizione
Remove-Partition                # Eliminare partizione
Resize-Partition                # Ridimensionare
Set-Partition                   # Modificare proprietà
Get-PartitionSupportedSize      # Dimensioni min/max supportate
Add-PartitionAccessPath         # Aggiungere mount point

# --- VOLUMI ---
Get-Volume                      # Elencare volumi
Format-Volume                   # Formattare
Optimize-Volume                 # Deframmentare / TRIM (SSD)
Repair-Volume                   # Verificare/riparare filesystem
Set-Volume                      # Modificare proprietà

# --- PHYSICAL DISK ---
Get-PhysicalDisk                # Elencare dischi fisici
Set-PhysicalDisk                # Modificare (Usage, Description)
Get-StorageReliabilityCounter   # Contatori SMART / affidabilità

# --- STORAGE POOL ---
Get-StoragePool                 # Elencare pool
New-StoragePool                 # Creare pool
Remove-StoragePool              # Eliminare pool
Set-StoragePool                 # Modificare pool
Add-PhysicalDisk                # Aggiungere disco al pool
Remove-PhysicalDisk             # Rimuovere disco dal pool

# --- VIRTUAL DISK ---
Get-VirtualDisk                 # Elencare virtual disk
New-VirtualDisk                 # Creare virtual disk
Remove-VirtualDisk              # Eliminare virtual disk
Set-VirtualDisk                 # Modificare (WriteCacheSize)
Repair-VirtualDisk              # Riparare (dopo guasto disco)
Resize-VirtualDisk              # Ridimensionare

# --- STORAGE TIER ---
Get-StorageTier                 # Elencare tier
New-StorageTier                 # Creare tier (SSD/HDD)
Set-StorageTier                 # Modificare tier
Get-FileStorageTier             # Tier di un file
Set-FileStorageTier             # Pinnare file a un tier
Optimize-StorageTier            # Forzare ottimizzazione

# --- DEDUPLICAZIONE ---
Enable-DedupVolume              # Abilitare dedup
Disable-DedupVolume             # Disabilitare dedup
Get-DedupVolume                 # Stato configurazione
Set-DedupVolume                 # Modificare parametri
Get-DedupStatus                 # Statistiche risparmio
Start-DedupJob                  # Avviare job manuale
Get-DedupJob                    # Job in corso
Get-DedupSchedule               # Schedule configurati
Set-DedupSchedule               # Modificare schedule
Get-DedupMetadata               # Metadati chunk store

# --- iSCSI TARGET ---
New-IscsiServerTarget           # Creare target
Get-IscsiServerTarget           # Elencare target
Set-IscsiServerTarget           # Modificare target
Remove-IscsiServerTarget        # Eliminare target
New-IscsiVirtualDisk            # Creare LUN
Get-IscsiVirtualDisk            # Elencare LUN
Remove-IscsiVirtualDisk         # Eliminare LUN
Add-IscsiVirtualDiskTargetMapping    # Mappare LUN a target
Remove-IscsiVirtualDiskTargetMapping # Rimuovere mapping

# --- iSCSI INITIATOR ---
New-IscsiTargetPortal           # Configurare portal
Get-IscsiTarget                 # Elencare target disponibili
Connect-IscsiTarget             # Connettersi a target
Disconnect-IscsiTarget          # Disconnettersi
Get-IscsiSession                # Sessioni attive
Get-IscsiConnection             # Connessioni attive

# --- SMB ---
New-SmbShare                    # Creare share
Get-SmbShare                    # Elencare share
Set-SmbShare                    # Modificare share
Remove-SmbShare                 # Eliminare share
Get-SmbShareAccess              # Permessi share
Grant-SmbShareAccess            # Aggiungere permesso
Revoke-SmbShareAccess           # Rimuovere permesso
Get-SmbSession                  # Sessioni attive
Get-SmbOpenFile                 # File aperti
Close-SmbSession                # Chiudere sessione
Close-SmbOpenFile               # Chiudere file
Get-SmbServerConfiguration      # Configurazione server
Set-SmbServerConfiguration      # Modificare configurazione

# --- DFS ---
New-DfsnRoot                    # Creare namespace
New-DfsnFolder                  # Aggiungere folder
New-DfsnFolderTarget            # Aggiungere target a folder
Get-DfsnRoot                    # Stato namespace
Get-DfsnFolder                  # Elencare folder
New-DfsReplicationGroup         # Creare replication group
Add-DfsrMember                  # Aggiungere member
Add-DfsrConnection              # Aggiungere connessione
Set-DfsrMembership              # Configurare membership
Get-DfsrBacklog                 # Backlog replica

# --- FSRM ---
New-FsrmQuota                   # Creare quota
New-FsrmQuotaTemplate           # Creare template quota
New-FsrmAutoQuota               # Auto-apply quota
Get-FsrmQuota                   # Elencare quote
New-FsrmFileScreen              # Creare file screen
New-FsrmStorageReport           # Creare report
```

---

## Storage Migration Service

```powershell
# SMS migra dati, share, configurazione e identità da server legacy a nuovi server.
# Supporta migrazione da: Windows Server 2003+, Linux (Samba), NetApp FAS

# Installare (sul server orchestratore, es. Windows Admin Center)
Install-WindowsFeature SMS-Proxy -IncludeManagementTools

# Workflow SMS:
# ┌──────────────────────────────────────────────────────────┐
# │ 1. INVENTARIO                                            │
# │    Scansiona il server sorgente:                         │
# │    - Share e relative configurazioni                     │
# │    - Permessi NTFS e share permissions                   │
# │    - Configurazione di rete (IP, DNS)                    │
# │    - Ruoli e feature installati                          │
# │                                                          │
# │ 2. TRASFERIMENTO                                         │
# │    Copia dati dal sorgente alla destinazione:            │
# │    - Transfer differenziale (solo blocchi modificati)    │
# │    - Mantiene tutti i metadati (permessi, timestamp)     │
# │    - Supporta file aperti (VSS snapshot)                 │
# │    - Ri-eseguibile per sincronizzazione incrementale     │
# │                                                          │
# │ 3. CUTOVER                                               │
# │    Sposta identità dal sorgente alla destinazione:       │
# │    - Il server destinazione assume nome e IP del sorgente│
# │    - Il server sorgente viene rinominato                 │
# │    - Zero downtime per gli utenti finali                 │
# │    - Tutti gli share e UNC path rimangono invariati      │
# └──────────────────────────────────────────────────────────┘

# La gestione è tramite Windows Admin Center (WAC) — interfaccia GUI
# WAC → Storage Migration Service → Nuovo job

# Vantaggi:
# - Zero downtime per gli utenti (cutover trasparente)
# - Mantiene permessi NTFS, share permissions, audit settings
# - Supporta file aperti
# - Trasferimento incrementale (delta sync)
# - Supporto Linux sorgente (Samba share)

# PowerShell (cmdlets disponibili con modulo StorageMigrationService):
# Get-SmsJob, Start-SmsJob, Get-SmsState
# Tipicamente gestito via WAC
```

---

## Best Practices

1. **GPT per tutti i nuovi dischi**: MBR è legacy. GPT supporta > 2TB, ha backup partition table, e CRC32 su header. Unica eccezione: hardware che richiede MBR (BIOS senza UEFI).

2. **Allocation unit size appropriata**: 4K per uso generale e file server. 64K per SQL Server, Hyper-V (VHDX), Exchange, e workload con I/O grandi. Non usare 64K se serve compressione NTFS.

3. **Storage Spaces per ridondanza**: preferire mirror software a RAID hardware per flessibilità, gestibilità PowerShell, e indipendenza da vendor HBA. RAID hardware mantiene vantaggio in performance write con battery-backed cache.

4. **Deduplicazione dove possibile**: file server, VDI, e backup target beneficiano enormemente. Escludere database attivi e file già compressi.

5. **Monitorare spazio disco**: alert proattivi quando spazio < 20% (warning) e < 10% (critico). Includere shadow copy storage nel calcolo. Verificare thin-provisioned pool per evitare esaurimento.

6. **Separare OS e dati**: sistema operativo su C:, dati e applicazioni su volumi separati. Facilita backup, recovery, e gestione indipendente.

7. **ReFS per Hyper-V e backup**: performance migliori grazie a block cloning per merge checkpoint e copia VHDX. Integrity streams per protezione dati di backup.

8. **SMB encryption per dati sensibili**: abilitare encryption su share con dati confidenziali. Disabilitare SMBv1 ovunque.

9. **DFS Namespace per scalabilità**: usare namespace domain-based per presentare share da server multipli come struttura unica e gestire failover trasparente.

10. **Backup 3-2-1**: tre copie dei dati, su due supporti diversi, una copia off-site. Combinare Windows Server Backup locale con Azure Backup per off-site.

11. **MPIO per percorsi ridondanti**: configurare multipath per iSCSI e Fibre Channel. Testare failover periodicamente.

12. **Quote preventive**: implementare quote FSRM su cartelle utente e share condivisi per prevenire esaurimento spazio. Iniziare con soft limit per capire i pattern.

13. **Disabilitare nomi 8.3**: su volumi dati dove non servono per ridurre overhead MFT e migliorare performance enumerazione directory.

14. **Encryption at rest**: BitLocker per volumi con dati sensibili. EFS solo se serve granularità per-file e l'infrastruttura certificati è gestita (DRA configurato, backup chiavi).

15. **Documentare layout storage**: mappare dischi fisici → pool → virtual disk → volume → lettera/mount point. Essenziale per troubleshooting e disaster recovery.

---

## Storage Design Checklist

```
Checklist per progettazione storage Windows Server:

REQUISITI
□ Capacità totale richiesta (con crescita prevista 12-24 mesi)
□ IOPS richiesti per workload (database, file server, VM, ecc.)
□ Throughput richiesto (MB/s sequenziale)
□ Latenza massima accettabile (ms)
□ RPO/RTO per disaster recovery
□ Compliance / retention requirements
□ Budget disponibile

HARDWARE
□ Tipo disco scelto (NVMe / SSD SATA / SAS HDD / SATA HDD)
□ Interfaccia: SAS, SATA, NVMe, FC, iSCSI
□ HBA configurato in modalità passthrough (non RAID per Storage Spaces)
□ RAID hardware con BBU se non si usa Storage Spaces
□ Network per iSCSI: 10 GbE minimo, VLAN dedicata, MPIO
□ Network per S2D: 10/25 GbE con RDMA (RoCE v2 o iWARP)

LAYOUT
□ Disco OS separato dai dati
□ Stile partizione: GPT per tutti i dischi nuovi
□ File system: NTFS per general purpose, ReFS per Hyper-V/backup
□ Allocation unit size appropriata (4K generale, 64K SQL/VM)
□ Mount point definiti (lettere drive o C:\Mounts\...)
□ Thin provisioning solo dove monitoraggio è garantito

RESILIENZA
□ Tipo di resilienza scelto (mirror, parity, dual parity)
□ Hot spare configurato (Storage Spaces)
□ MPIO configurato (iSCSI / FC)
□ Test di failover eseguito

FILE SYSTEM
□ Compressione NTFS solo dove appropriata (log, archivio)
□ Nomi 8.3 disabilitati sui volumi dati
□ Deduplicazione abilitata dove beneficia (file server, backup)
□ Integrity streams su ReFS per dati critici

ACCESSO
□ Share SMB creati con permessi corretti
□ ABE abilitato su share multi-utente
□ SMBv1 disabilitato
□ Encryption SMB su share sensibili
□ DFS Namespace configurato (se multi-server)
□ DFS Replication configurata (se serve replica)

QUOTE E LIMITI
□ Quote FSRM su cartelle utente
□ File screening su share (blocco tipi indesiderati)
□ Soglie notifica a 85% e 95%

MONITORAGGIO
□ Alert spazio disco < 20% warning, < 10% critico
□ Contatori performance configurati (latenza, queue length)
□ Health check periodici (Get-PhysicalDisk, Get-VirtualDisk)
□ Report FSRM schedulati (mensili)

BACKUP
□ Policy backup configurata (Windows Server Backup)
□ Backup off-site (Azure Backup o tape)
□ Shadow Copy configurato per volumi utente
□ Test di restore eseguito e documentato
□ Retention adeguata alla policy aziendale

SICUREZZA
□ BitLocker su volumi con dati sensibili
□ DRA configurato per EFS (se usato)
□ Audit access configurato su cartelle critiche
□ ACL verificate (principio del minimo privilegio)

DOCUMENTAZIONE
□ Mappa: disco fisico → pool → virtual disk → volume → path
□ Diagramma rete storage (iSCSI, FC, SMB)
□ Procedure di recovery documentate
□ Contatti vendor per supporto hardware
```

---

## Troubleshooting

**"Disco non visibile dopo aggiunta"** → Aprire Disk Management o `Get-Disk`. Il disco potrebbe essere Offline (`Set-Disk -IsOffline $false`) o Read-Only (`Set-Disk -IsReadOnly $false`). Su cluster, il disco potrebbe essere riservato. Verificare anche la policy SAN: `diskpart` → `san` per vedere se i dischi vengono portati online automaticamente. Se BusType è iSCSI o FC, verificare che il target sia raggiungibile.

**"Storage Space degradato"** → `Get-VirtualDisk` mostra HealthStatus diverso da Healthy. Identificare il disco guasto: `Get-PhysicalDisk | Where-Object HealthStatus -ne Healthy`. Sostituire il disco fisico guasto, aggiungere il nuovo disco al pool (`Add-PhysicalDisk`), e avviare la riparazione (`Repair-VirtualDisk`). Monitorare con `Get-StorageJob`.

**"Dedup non riduce lo spazio"** → Verificare `MinimumFileAgeDays` (file troppo recenti non vengono deduplicati). Controllare che il job di ottimizzazione sia in esecuzione (`Get-DedupJob`). Verificare tipo di file: binari casuali come video, immagini compresse e file crittografati non si deduplicano. Verificare esclusioni con `Get-DedupVolume`.

**"iSCSI disconnessione frequente"** → Verificare connettività di rete stabile. Configurare MPIO per multipath. Controllare che il servizio MSiSCSI sia in esecuzione. Verificare firewall (porta TCP 3260). Se CHAP è abilitato, verificare credenziali. Aumentare timeout: `iscsicli` → impostare LoginTimeout e LogoutTimeout.

**"NTFS: 'The file or directory is corrupted and unreadable'"** → Eseguire `chkdsk /f` (richiede volume offline o reboot per C:) o `Repair-Volume -DriveLetter X -SpotFix`. Verificare integrità hardware disco con `Get-PhysicalDisk` e `Get-StorageReliabilityCounter`. Se errori SMART frequenti, pianificare sostituzione disco.

**"Disco pieno improvvisamente"** → Verificare shadow copy storage (`vssadmin list shadowstorage`): può consumare fino al limite configurato. Verificare file di log cresciuti senza rotazione. Cercare file grandi: `Get-ChildItem D:\ -Recurse | Sort-Object Length -Descending | Select-Object -First 20`. Verificare se la deduplicazione è in backlog.

**"ReFS: performance scadenti"** → ReFS ha overhead maggiore di NTFS per operazioni su file piccoli. Verificare che allocation unit sia 64K (default ReFS). Per workload con molti file piccoli, NTFS è più appropriato. Verificare che integrity streams non sia abilitato su dati che non lo richiedono (aggiunge overhead I/O).

**"Storage Spaces: Cannot create virtual disk"** → Verificare che i dischi siano `CanPool = True` (`Get-PhysicalDisk`). I dischi devono essere non inizializzati e non partizionati. Dischi con partizioni o dati esistenti non sono poolable: `Clear-Disk -RemoveData` prima. Verificare anche che il numero di dischi sia sufficiente per il tipo di resilienza scelto.

**"SMB: Access Denied"** → Verificare ENTRAMBI i livelli di permesso: share permissions (`Get-SmbShareAccess`) e NTFS permissions (`Get-Acl`). Il risultato è l'intersezione (più restrittivo). Verificare che l'utente sia membro dei gruppi corretti. Se ABE è attivo, la cartella potrebbe non essere visibile. Testare con `Test-Path \\server\share\folder`.

**"DFS: cartella non visibile nel namespace"** → Verificare che il target server sia raggiungibile. Verificare che lo share esista sul target. `Get-DfsnFolderTarget` per verificare i target configurati. Verificare referral: `dfsutil /pktinfo`. Se il problema è solo su un client, `dfsutil cache flush` e `klist purge` per pulire cache Kerberos.

**"DFS Replication: backlog elevato"** → `Get-DfsrBacklog` per quantificare. Verificare larghezza di banda disponibile. Controllare schedule DFS-R (potrebbe essere limitato a finestre temporali). Verificare staging quota: se troppo piccola, causa re-staging continuo. Controllare event log `DFS Replication` per errori.

**"MFT frammentata: performance enumerazione lente"** → `defrag D: /A` per analisi frammentazione. MFT frammentata causa lentezza nell'apertura di cartelle con molti file. `defrag D: /X` per consolidare MFT free space zone. Disabilitare nomi 8.3 (`fsutil 8dot3name set D: 1`) per ridurre crescita MFT.

**"EFS: impossibile aprire file crittografati"** → L'utente ha perso il certificato EFS. Se DRA è configurato, usare il certificato DRA per recovery. Se non c'è DRA e non c'è backup del certificato, i dati sono irrecuperabili. Verificare certificati: `cipher /c filename`. Per prevenire: configurare DRA via Group Policy e fare backup dei certificati EFS.

**"Quota FSRM: utente non bloccato nonostante hard limit"** → Verificare che la quota sia attiva (`Get-FsrmQuota -Path ...`). Verificare che sia hard limit (`SoftLimit = $false`). Se l'utente è proprietario di file in sottocartelle non coperte dalla quota auto-apply, lo spazio potrebbe non essere conteggiato. Le quote NTFS native e FSRM sono indipendenti: verificare quale è attiva.

**"MPIO: failover non funziona"** → Verificare che MPIO sia installato e configurato per il bus type corretto (`Get-MSDSMSupportedHW`). Richiede reboot dopo `Enable-MSDSMAutomaticClaim`. Verificare che entrambi i percorsi siano attivi: `mpclaim -s -d`. Testare failover disconnettendo un percorso.

**"Fibre Channel: LUN non visibili"** → Verificare WWPN con `Get-InitiatorPort`. Verificare zoning sullo switch FC (WWPN del server in zona con porta storage). Verificare LUN masking sullo storage array (WWPN autorizzato ad accedere al LUN). Eseguire `Update-HostStorageCache` per rescan. Se i LUN appaiono come offline, configurare policy SAN: `diskpart` → `san policy=OnlineAll`.

**"Thin provisioning: volume offline"** → Il pool ha esaurito lo spazio fisico. Aggiungere dischi al pool immediatamente (`Add-PhysicalDisk`). Dopo aggiunta spazio, il virtual disk dovrebbe tornare online. Per prevenire: monitorare attentamente `AllocatedSize` vs `Size` del pool. Configurare alert quando `AllocatedSize > 80% Size`.

**"Performance I/O degradate"** → Verificare con Performance Monitor: `Avg. Disk Queue Length > 2` per disco = collo di bottiglia. `Avg. Disk sec/Read > 15ms` (HDD) o `> 5ms` (SSD) = latenza alta. Verificare frammentazione (`defrag /A`). Verificare allineamento partizioni. Verificare che antivirus non stia scansionando I/O in real-time su volumi ad alto throughput.

**"Cluster Shared Volume (CSV): redirect mode"** → Il CSV è in redirected mode quando il nodo owner non può comunicare direttamente con lo storage. Verificare network storage: latenza, errori, disconnessioni. `Get-ClusterSharedVolumeState` per verificare. Redirected mode causa tutto il traffico I/O attraverso il nodo owner via network, con performance ridotte.

**"S2D: nodo non contribuisce storage"** → Verificare che il nodo sia nel cluster e attivo. Verificare che i dischi locali siano visibili: `Get-PhysicalDisk -CimSession NodeName`. Verificare che S2D sia abilitato: `Get-ClusterStorageSpacesDirect`. Controllare event log del nodo per errori storage bus.

**"BitLocker + Storage Spaces: problemi"** → BitLocker va applicato sul volume finale, non sui dischi fisici del pool. Abilitare BitLocker dopo la creazione del virtual disk e del volume. Per S2D, usare BitLocker con CSV.

---

## FAQ — Domande Frequenti

**D: Quando usare ReFS invece di NTFS?**
R: ReFS è preferibile per volumi Hyper-V (block cloning accelera merge checkpoint), Storage Spaces Direct (auto-repair con mirror), backup target (integrity streams proteggono i dati). NTFS resta necessario per boot volume, quando serve compressione nativa, EFS, o hard link.

**D: Storage Spaces è un sostituto di RAID hardware?**
R: Sì, per la maggior parte degli scenari. Storage Spaces offre resilienza software (mirror, parity) con gestione PowerShell, indipendenza da vendor hardware, e funzionalità avanzate (tiering, thin provisioning). RAID hardware mantiene un vantaggio in write performance con controller dotati di battery-backed write cache (BBWC) e offload hardware. Per S2D, è obbligatorio HBA in passthrough mode (niente RAID controller).

**D: Quanti dischi servono per ogni tipo di resilienza?**
R: Simple: 1 minimo. Two-way mirror: 2 minimo. Three-way mirror: 3 minimo (5 in S2D per fault domain isolation). Single parity: 3 minimo. Dual parity: 7 minimo. Il numero effettivo dipende anche dalla dimensione dei dati e dallo spazio richiesto.

**D: Cosa succede se il pool thin-provisioned esaurisce lo spazio?**
R: I virtual disk vanno offline e le scritture falliscono. Soluzione immediata: aggiungere dischi al pool. Prevenzione: monitorare `AllocatedSize` del pool e configurare alert proattivi. Non over-provisioning eccessivo senza monitoraggio.

**D: NTFS permissions o share permissions — quale gestire?**
R: Controllare l'accesso tramite NTFS permissions e impostare share permissions a "Everyone → Full Control" (o "Authenticated Users → Change"). Motivo: NTFS permissions sono più granulari, funzionano sia in locale che in rete, e sono più semplici da troubleshootare con un solo livello effettivo.

**D: Come scegliere l'allocation unit size?**
R: 4 KB (default): file server generale, documenti, uso misto. 64 KB: SQL Server, Exchange, Hyper-V VHDX, workload con I/O grandi e sequenziali. Nota: allocation unit > 4K disabilita la compressione NTFS. Non si può cambiare senza riformattare.

**D: La deduplicazione rallenta il server?**
R: L'overhead è minimo in condizioni normali. L'ottimizzazione è schedulata in background con priorità bassa. La lettura di file deduplicati ha un leggero overhead (re-assemblaggio blocchi dal chunk store). Per workload ad alte IOPS (database), escludere quei volumi dalla dedup. Non abilitare su volumi con file crittografati o già compressi.

**D: iSCSI o Fibre Channel — quale scegliere?**
R: iSCSI: costo inferiore (usa Ethernet esistente), configurazione più semplice, adeguato per PMI e workload non estremi. Fibre Channel: latenza più bassa e deterministica, throughput più alto (16/32/64 Gbps), standard enterprise per database mission-critical e SAN grandi. Per nuove installazioni, considerare NVMe-oF per le massime prestazioni.

**D: Come migrare da MBR a GPT senza perdere dati?**
R: Per il disco di sistema: usare `mbr2gpt /validate /disk:0` e `mbr2gpt /convert /disk:0` (da WinPE o preboot, Windows 10 1703+ / Server 2019+). Per dischi dati: backup dei dati, `Clean` + `Convert GPT` in diskpart, ripristino. Non esiste conversione in-place lossless per dischi dati via strumenti built-in.

**D: DFS Namespace standalone o domain-based?**
R: Domain-based (DomainV2): consigliato. Failover automatico tra namespace server multipli, configurazione replicata in AD, massima disponibilità. Standalone: solo se non c'è Active Directory o se serve un namespace con più di ~5000 folder target (limite domain-based).

**D: Come dimensionare la staging area DFS-R?**
R: La staging area deve essere almeno pari alla dimensione dei 32 file più grandi nella cartella replicata (approssimazione). Se troppo piccola, i file grandi vengono continuamente ri-staged, rallentando la replica. Monitorare con contatori performance e aumentare se necessario via `Set-DfsrMembership -StagingPathQuotaInMB`.

**D: Shadow Copy è un sostituto del backup?**
R: No. Shadow Copy protegge da cancellazioni accidentali e permette "Previous Versions", ma risiede sullo stesso volume (o sullo stesso server). Non protegge da guasto hardware, ransomware che critta l'intero volume, o disastro fisico. Usare Shadow Copy come complemento al backup, non come sostituto.

**D: Come verificare lo stato di salute dei dischi SSD?**
R: `Get-PhysicalDisk | Get-StorageReliabilityCounter` fornisce: Wear (percentuale usura), Temperature, ReadErrorsTotal, WriteErrorsTotal, PowerOnHours. Per SSD enterprise, wear < 80% è normale. Se Wear supera la soglia indicata dal produttore, pianificare la sostituzione. Il HealthStatus del disco cambia a "Warning" o "Unhealthy" automaticamente.

**D: Posso usare BitLocker con Storage Spaces?**
R: Sì, ma applicare BitLocker sul volume finale (dopo creazione virtual disk e formattazione), non sui dischi fisici del pool. Per S2D con CSV, BitLocker è supportato. Non abilitare BitLocker sui singoli dischi fisici prima di creare il pool, poiché Storage Spaces richiede accesso diretto ai dischi.

**D: Come gestire il cutover in Storage Migration Service con downtime zero?**
R: SMS gestisce il cutover automaticamente: rinomina il server sorgente, assegna nome e IP del sorgente al server destinazione. Gli utenti che usano UNC path basati sul nome del server non notano il cambio. Il downtime effettivo è limitato al tempo di rinomina DNS e propagazione (tipicamente secondi-minuti). Testare il cutover in un ambiente lab prima dell'esecuzione in produzione.

**D: Qual è il limite di dimensione della MFT e come influisce sulle performance?**
R: La MFT cresce automaticamente man mano che si creano file. Windows riserva ~12.5% del volume per la crescita MFT (configurabile con `fsutil behavior set mftzone`). Se la zona riservata si esaurisce, la MFT si frammenta, causando lentezza nell'enumerazione directory (specialmente con centinaia di migliaia di file). Soluzioni: deframmentare la MFT con `defrag /X`, disabilitare nomi 8.3 per ridurre dimensione record, e considerare volumi separati per directory con milioni di file.

---

## Esercizi

1. Spiega la differenza tra Storage Spaces e Storage Spaces Direct: quando useresti l'uno e quando l'altro in un'infrastruttura enterprise?
2. **Lab:** Crea un pool di Storage Spaces con almeno 3 dischi virtuali (VHD), configura un virtual disk con layout Mirror e formattalo in ReFS. Verifica la resilienza rimuovendo un disco dal pool.
3. Un file server da 10 TB contiene prevalentemente documenti Office e file di log ripetitivi. Progetta una strategia di deduplicazione: quali volumi abiliteresti, quali escluderesti, e quale risparmio stimi?
4. Ricerca e documenta le differenze tra SMB 3.0, 3.02 e 3.1.1 in termini di crittografia, firma e multichannel. Quale versione minima consiglieresti per un ambiente enterprise moderno e perche?

## Auto-valutazione

<details><summary>1. Qual e la differenza principale tra GPT e MBR?</summary>
GPT supporta fino a 128 partizioni e dischi oltre 2 TB, usa una tabella di partizione ridondante e checksum CRC32. MBR e limitato a 4 partizioni primarie e 2 TB. GPT e obbligatorio per UEFI boot e consigliato per ogni nuovo disco — vedi sezione [MBR vs GPT](#mbr-vs-gpt).
</details>

<details><summary>2. Cosa fa il cmdlet Enable-DedupVolume e quali workload non sono adatti?</summary>
Abilita la deduplicazione su un volume NTFS/ReFS. Non adatto per: database ad alte IOPS, volumi con file gia crittografati (EFS), volumi di boot del sistema operativo, e CSV in modalita reindirizzata — vedi sezione Deduplicazione.
</details>

<details><summary>3. Qual e il vantaggio principale di ReFS rispetto a NTFS per dataset grandi?</summary>
ReFS supporta integrity streams (rilevamento corruzione automatica), block cloning (copie istantanee), e non ha i limiti pratici di NTFS sulla dimensione MFT. Ideale per Hyper-V, backup e volumi > 16 TB — vedi sezione ReFS.
</details>

<details><summary>4. Come funziona DFS Replication e come si dimensiona la staging area?</summary>
DFS-R replica file tra server usando compressione differenziale remota (RDC). La staging area deve contenere almeno i 32 file piu grandi della cartella replicata. Se sottodimensionata, i file vengono continuamente ri-staged, degradando le prestazioni — vedi sezione DFS.
</details>

<details><summary>5. Che differenza c'e tra un iSCSI target e un iSCSI initiator?</summary>
Il target espone lo storage (LUN) sulla rete; l'initiator e il client che si connette al target e presenta il LUN come disco locale. Windows Server include sia il ruolo iSCSI Target che l'iSCSI Initiator — vedi sezione iSCSI.
</details>

<details><summary>6. Shadow Copy puo sostituire il backup?</summary>
No. Shadow Copy risiede sullo stesso volume e protegge da cancellazioni accidentali, ma non da guasti hardware, ransomware sull'intero volume o disastri fisici. Va usato come complemento al backup, mai come sostituto — vedi FAQ finale.
</details>

<details><summary>7. Come si verifica lo stato di salute dei dischi SSD via PowerShell?</summary>
Con `Get-PhysicalDisk | Get-StorageReliabilityCounter` si ottengono Wear, Temperature, ReadErrorsTotal, WriteErrorsTotal, PowerOnHours. Un Wear < 80% e nella norma; superata la soglia del produttore, pianificare la sostituzione — vedi FAQ finale.
</details>

## Letture primarie consigliate

- Microsoft Learn — Storage in Windows Server: <https://learn.microsoft.com/windows-server/storage/> (consultato: 2026-05-23)
- Microsoft Learn — Storage Spaces Direct overview: <https://learn.microsoft.com/windows-server/storage/storage-spaces/storage-spaces-direct-overview> (consultato: 2026-05-23)
- Microsoft Learn — DFS Namespaces and DFS Replication: <https://learn.microsoft.com/windows-server/storage/dfs-namespaces/dfs-overview> (consultato: 2026-05-23)
- Microsoft Learn — Data Deduplication overview: <https://learn.microsoft.com/windows-server/storage/data-deduplication/overview> (consultato: 2026-05-23)
- Microsoft Learn — iSCSI Target Server: <https://learn.microsoft.com/windows-server/storage/iscsi/iscsi-target-server> (consultato: 2026-05-23)

## Collegamenti incrociati

- [Rete Windows](06-rete-windows.md) — SMB multichannel, DNS per DFS, configurazione NIC teaming
- [Permessi e Accesso](08-permessi-e-accesso.md) — ACL NTFS, condivisioni, quota utente
- [Backup e Ripristino](15-backup-ripristino.md) — Windows Server Backup, snapshot VSS
- [Failover Clustering](27-failover-clustering-guida.md) — CSV, Storage Spaces Direct in cluster
- [PowerShell](02-powershell.md) — cmdlet Storage, automazione gestione dischi

## Glossario locale

| Termine | Definizione |
|---------|-------------|
| Storage Spaces | Tecnologia di virtualizzazione storage che aggrega dischi fisici in pool e crea virtual disk con resilienza (mirror, parity) |
| Storage Spaces Direct (S2D) | Evoluzione di Storage Spaces per cluster hyper-converged, usa dischi locali dei nodi senza SAN esterna |
| ReFS | Resilient File System: file system progettato per integrità dati, grandi volumi e block cloning |
| MFT | Master File Table: struttura dati NTFS che contiene i metadati di ogni file e directory del volume |
| Deduplicazione | Processo di eliminazione dei blocchi dati duplicati su un volume per risparmiare spazio disco |
| DFS | Distributed File System: namespace virtuale che unifica condivisioni di rete e replica file tra server |
| iSCSI | Internet Small Computer Systems Interface: protocollo che trasporta comandi SCSI su rete TCP/IP |
| SMB | Server Message Block: protocollo per la condivisione di file, stampanti e named pipe su rete Windows |
| GPT | GUID Partition Table: schema di partizionamento moderno che sostituisce MBR, supporta dischi > 2 TB |
| CSV | Cluster Shared Volume: volume condiviso tra nodi di un failover cluster per accesso simultaneo |
