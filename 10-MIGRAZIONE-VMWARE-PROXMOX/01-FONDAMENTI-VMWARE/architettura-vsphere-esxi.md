# Architettura VMware vSphere e ESXi

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 1 — Fondamenti · Modulo 01.1 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** prerequisiti tecnici del corso (`../00-SYLLABUS.md` §4); nessuna esperienza vSphere richiesta, ma utile aver navigato vSphere Client almeno una volta.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. distinguere i ruoli di ESXi (hypervisor di tipo 1, microkernel proprietario) e di vCenter Server (gestione centralizzata) e di descrivere il flusso di comando vSphere Client → vCenter → ESXi;
> 2. enumerare le versioni di vSphere 6.5 → 8.0 con date di GA e finestre EOGS, e motivare perche la migrazione a Proxmox e diventata un'opzione strategica concreta dopo l'acquisizione Broadcom (2023-11);
> 3. spiegare le differenze fra modello di licensing pre- e post-Broadcom e calcolarne l'impatto economico su un parco di host realistico;
> 4. eseguire un assessment completo di un ambiente vSphere via PowerCLI (host, VM, dischi, snapshot, networking, storage, cluster, permessi);
> 5. descrivere la cascata di tecniche di memoria su ESXi (TPS → Compression → Ballooning → Swap) e leggere lo stato runtime via `esxcli`.
> **Tempo stimato:** lettura 60-90 min · lab 90-120 min
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** ESXi/vCenter 6.5 → 8.0 U3i (build 25205845, 2026-02-24), hardware version `vmx-13` → `vmx-21`, PowerCLI ≥ 12.x.

## Mappa concettuale

```
+======================================================+
|         vSphere — vista d'insieme del modulo         |
+======================================================+
|                                                      |
|   Client (HTML5 Web Client / PowerCLI / REST API)    |
|         |                                            |
|         v                                            |
|   vCenter Server Appliance (vCSA, Photon OS)         |
|     +-- SSO (vsphere.local + AD/LDAP/ADFS)           |
|     +-- PostgreSQL embedded                          |
|     +-- vpxd (orchestratore)                         |
|         |                                            |
|         v                                            |
|   ESXi Hosts (microkernel VMkernel)                  |
|     +-- User Worlds (vmx, hostd, vpxa, sfcbd, dcui)  |
|     +-- Memory: TPS -> Compression -> Balloon -> Swap|
|     +-- CPU: scheduler, EVC, ready time              |
|     +-- File VM: .vmx, .vmdk, .vswp, .nvram          |
|         |                                            |
|         v                                            |
|   VM hardware (vmx-13 .. vmx-21)                     |
|     +-- Driver paravirtuali: VMXNET3, PVSCSI         |
|     +-- VMware Tools (DA RIMUOVERE pre-V2V)          |
|     +-- Snapshot (NON sono backup; consolidare!)     |
|                                                      |
+======================================================+
```

Quattro idee da cui far discendere il resto del modulo:

1. **ESXi non e Linux.** Microkernel proprietario VMkernel: scheduling, memory manager, driver. I "comandi noti" (BusyBox shell `esxcli`, `vim-cmd`) sono interfacce verso questo microkernel, non un Linux mascherato. Trattarlo come scatola nera lucida.
2. **vCenter aggiunge le funzioni di produzione.** HA, DRS, vMotion, RBAC unificata, Content Library: nessuna vive sull'host singolo, tutte richiedono vCenter. Spegnere vCenter = perdere orchestrazione, ma le VM continuano a girare.
3. **La memoria si difende a cascata.** Sotto pressione: TPS prima (gratis e veloce), poi Compression, poi Balloon (richiede Tools nel guest), poi Swap (penalty massiva). Capire l'ordine = saper diagnosticare un host overcommitted.
4. **Tutto cio che e «VMware paravirt» va sostituito al passaggio a Proxmox.** VMXNET3, PVSCSI, VMware Tools: nessuno funziona dentro KVM. Il loro equivalente sono `virtio-net`, `virtio-scsi`, `qemu-guest-agent`. Pre-installare i driver VirtIO *nel guest Windows* prima di spegnere e una delle azioni piu importanti del modulo 09.4.

## Indice

1. [Architettura VMware vSphere](#architettura-vmware-vsphere)
2. [ESXi Hypervisor](#esxi-hypervisor)
3. [vCenter Server](#vcenter-server)
4. [Gestione VM in vSphere](#gestione-vm-in-vsphere)
5. [vSphere Permissions](#vsphere-permissions)
6. [Inventario e Assessment](#inventario-e-assessment)

---

## Architettura VMware vSphere

### Panoramica della Piattaforma

VMware vSphere e la piattaforma di virtualizzazione enterprise piu diffusa al mondo. Comprendere la sua architettura in profondita e il prerequisito fondamentale per pianificare una migrazione corretta verso Proxmox VE.

vSphere non e un singolo prodotto, ma un ecosistema di componenti integrati che cooperano per fornire virtualizzazione di compute, storage e networking a livello enterprise.

```
+=====================================================================+
|                    VMware vSphere Ecosystem                          |
+=====================================================================+
|                                                                      |
|   +-------------------+     +-----------------------------------+   |
|   |   vSphere Client  |     |     vCenter Server Appliance      |   |
|   |   (HTML5 / FLEX)  |---->|           (vCSA)                  |   |
|   |   Browser-based   |     |                                   |   |
|   +-------------------+     |  +----------+  +---------------+  |   |
|                             |  |   SSO    |  |   vCenter DB  |  |   |
|   +-------------------+     |  | (PSC)    |  |  (PostgreSQL) |  |   |
|   |   PowerCLI        |---->|  +----------+  +---------------+  |   |
|   |   (Automation)    |     |  +----------+  +---------------+  |   |
|   +-------------------+     |  | vpxd     |  |  Inventory    |  |   |
|                             |  | service  |  |  Service      |  |   |
|   +-------------------+     |  +----------+  +---------------+  |   |
|   |   REST API        |---->|                                   |   |
|   |   (vSphere API)   |     +-----------------------------------+   |
|   +-------------------+              |        |        |            |
|                              +-------+        |        +------+     |
|                              |                |               |     |
|   +----------v---------+  +---------v------+  +------v------+      |
|   |     ESXi Host 1    |  |   ESXi Host 2  |  | ESXi Host N |      |
|   | +----+ +----+      |  | +----+ +----+  |  | +----+      |      |
|   | | VM | | VM |      |  | | VM | | VM |  |  | | VM |      |      |
|   | +----+ +----+      |  | +----+ +----+  |  | +----+      |      |
|   +--------------------+  +-----------------+  +-------------+      |
+=====================================================================+
```

**ESXi** e l'hypervisor bare-metal di tipo 1, installato direttamente sull'hardware. **vCenter Server** e il componente di gestione centralizzata (vMotion, DRS, HA). **vSphere Client** e l'interfaccia web HTML5 (il thick client C# e stato deprecato dalla 6.5).

### Versioni di vSphere

| Versione | Release | Novita Principali | Fine Supporto |
|---|---|---|---|
| vSphere 6.5 | Nov 2016 | vCSA nativo, HTML5 Client | Oct 2022 (EOGS) |
| vSphere 6.7 | Apr 2018 | HTML5 feature-complete | Oct 2022 (EOGS) |
| vSphere 7.0 | Apr 2020 | Tanzu, vDS 7.0 | Apr 2025 (EOGS) |
| vSphere 7.0 U3 | Oct 2021 | vTPM, NVMe over TCP | Apr 2025 (EOGS) |
| vSphere 8.0 | Oct 2022 | DPU support, lifecycle mgmt | TBD |
| vSphere 8.0 U2 | Sep 2023 | GPU passthrough migliorato | TBD |
| vSphere 8.0 U3 | Jun 2024 | Configuration management | TBD |

### Modello di Licensing e Impatto Broadcom

Il licensing VMware e stato radicalmente modificato dopo l'acquisizione da parte di Broadcom (novembre 2023).

**Modello pre-Broadcom (licenze perpetue)**:

| Edizione | Caratteristiche | Prezzo Indicativo |
|---|---|---|
| Essentials | Fino a 3 host, gestione base | ~500 USD |
| Essentials Plus | + HA, vMotion, Data Protection | ~4.500 USD |
| Standard | Per-CPU, vMotion, HA, Storage vMotion | ~1.100 USD/CPU |
| Enterprise Plus | DRS, dvSwitch, Storage DRS, NIOC | ~3.500 USD/CPU |
| ROBO Standard | Per-VM, fino a 25 VM per host | ~600 USD/25 VM |
| ROBO Advanced | + DRS, Cross-vCenter vMotion | ~1.200 USD/25 VM |

**Modello post-Broadcom (subscription only, 2024+)**:

| Bundle | Contenuto | Note |
|---|---|---|
| VMware Cloud Foundation (VCF) | vSphere + vSAN + NSX + Aria | Pricing per core, full stack |
| VMware vSphere Foundation (VVF) | vSphere + vSAN | Senza NSX/Aria |
| VMware vSphere Standard (VSS) | Solo vSphere | Pricing per core |
| vSphere Essentials Plus Kit (VVEP) | PMI, fino a 96 core | Solo subscription |

**Impatto**: eliminazione licenze perpetue, discontinuita prodotti standalone, riduzione canale partner, aumenti costi 2x-10x per molti clienti. Questi fattori hanno accelerato l'interesse verso Proxmox VE.

---

## ESXi Hypervisor

### Architettura Bare-Metal

ESXi e un hypervisor di tipo 1 con un microkernel proprietario (VMkernel), non basato su Linux:

```
+=====================================================================+
|                    ESXi Architecture Stack                           |
+=====================================================================+
|  +-----+ +-----+ +-----+ +-----+                                    |
|  | VM1 | | VM2 | | VM3 | | VMn |   <-- Guest VMs                   |
|  +--+--+ +--+--+ +--+--+ +--+--+                                    |
|     |       |       |       |                                        |
|  +--v-------v-------v-------v----+                                   |
|  |    VMX / VMM Processes        |  <-- User Worlds (vmx, vmx-vcpu) |
|  +---------------------------------------+                           |
|  |  CIM Agents | hostd | vpxa | dcui    |  <-- Mgmt User Worlds    |
|  +=======================================+                           |
|  |            VMkernel                    |                           |
|  |  CPU Scheduler | Memory Mgr | Drivers |                           |
|  |  VMFS Driver | Network Stack | SCSI   |                           |
|  +=======================================+                           |
|  |           Hardware (x86_64)            |                           |
|  +----------------------------------------+                          |
+=====================================================================+
```

| Processo User World | Funzione |
|---|---|
| `vmx` / `vmx-vcpu-N` | Processo principale VM / thread per ogni vCPU |
| `hostd` | Host management daemon (API, web) |
| `vpxa` | vCenter agent |
| `sfcbd` | CIM broker per monitoraggio hardware |
| `dcui` | Direct Console User Interface |
| `rhttpproxy` | Reverse proxy HTTPS |

### Boot Process e DCUI

ESXi puo avviare da disco locale, USB, SD card, SAN boot (iSCSI/FC), PXE/Auto Deploy. Il boot process e: POST -> Boot Loader -> VMkernel init -> User World init (hostd, vpxa) -> DCUI disponibile (Alt+F2).

**Nota critica**: ESXi su SD/USB ha problemi noti dalla 7.0 U3c+ per aumento dei log su media non-volatile. VMware raccomanda storage persistente dalla 8.x.

La DCUI (F2) permette: configurazione password root, rete di management, restart servizi, lockdown mode, visualizzazione log.

### Memory Management

ESXi attiva tecniche progressive di ottimizzazione memoria in base alla pressione:

```
Pressione BASSA ---------------------------------> Pressione ALTA

+----------+    +-------------+    +-----------+    +--------+
|   TPS    | -> | Compression | -> | Ballooning | -> |  Swap  |
+----------+    +-------------+    +-----------+    +--------+
```

- **TPS** (Transparent Page Sharing): deduplica pagine identiche. Inter-VM disabilitato di default dalla 6.0 (rischio side-channel). Solo intra-VM attivo.
- **Compression**: pagine inattive compresse in cache RAM. Piu veloce dello swap.
- **Ballooning**: balloon driver (vmmemctl in VMware Tools) forza il guest a paginare internamente, liberando pagine fisiche.
- **Swap**: ultima risorsa. Pagine scritte su file .vswp nel datastore. Performance gravemente degradate.

### CPU Scheduler

| Concetto | Descrizione |
|---|---|
| pCPU / vCPU | CPU fisica (core/thread) / CPU virtuale assegnata alla VM |
| Ready time | Tempo che una vCPU attende per essere schedulata (%RDY > 5% = problema) |
| CPU reservation | Risorse CPU garantite |
| CPU limit / shares | Limite massimo / peso relativo per priorita |

### Comandi esxcli Essenziali

```bash
# === SISTEMA ===
esxcli system version get          # Versione ESXi
esxcli system hostname get         # Hostname
esxcli hardware cpu global get     # CPU info (sockets, cores, threads)
esxcli hardware memory get         # Memoria totale e statistiche

# === NETWORKING ===
esxcli network nic list                       # NIC fisiche
esxcli network vswitch standard list          # vSwitch
esxcli network ip interface list              # VMkernel interfaces
esxcli network ip route ipv4 list             # Routing
esxcli network firewall ruleset list          # Firewall rules

# === STORAGE ===
esxcli storage core device list               # Dispositivi storage
esxcli storage filesystem list                # Datastore VMFS
esxcli storage core adapter list              # HBA adapter
esxcli storage nmp device list                # Multipath info
esxcli iscsi adapter list                     # iSCSI adapters

# === MANUTENZIONE ===
esxcli system maintenanceMode set --enable true   # Maintenance mode on
esxcli software vib list                          # VIB installati
esxcli software profile get                       # Profilo immagine

# === VM ===
esxcli vm process list                            # VM in esecuzione
esxcli vm process kill --type=force --world-id=N  # Force kill VM

# === SYSLOG ===
esxcli system syslog config set --loghost='udp://syslog.lab.local:514'
esxcli system syslog reload
```

---

## vCenter Server

### vCenter Server Appliance (vCSA)

Dalla 6.5, il vCenter su Windows e deprecato. La vCSA e una VM basata su Photon OS con tutti i servizi integrati: vpxd, SSO (vmware-stsd), PostgreSQL embedded, content library, SPBM.

| Deployment Size | Hosts | VM | vCPU | RAM | Storage |
|---|---|---|---|---|---|
| Tiny | fino a 10 | fino a 100 | 2 | 14 GB | 579 GB |
| Small | fino a 100 | fino a 1.000 | 4 | 21 GB | 694 GB |
| Medium | fino a 400 | fino a 4.000 | 8 | 30 GB | 908 GB |
| Large | fino a 2.000 | fino a 35.000 | 16 | 41 GB | 1.505 GB |
| X-Large | fino a 2.500 | fino a 45.000 | 24 | 58 GB | 2.093 GB |

```bash
# Gestione servizi vCSA
ssh root@vcenter.lab.local
service-control --status                     # Stato tutti i servizi
service-control --restart vmware-vpxd        # Riavviare vpxd
# VAMI: https://vcenter.lab.local:5480
# Client: https://vcenter.lab.local/ui
```

### Single Sign-On e Identity Sources

SSO gestisce l'autenticazione per tutta la piattaforma. Dominio predefinito: `vsphere.local`. Account admin: `administrator@vsphere.local`. Identity sources supportate: vsphere.local (built-in), Active Directory, LDAP/LDAPS, OpenLDAP, ADFS (federation).

### Inventario vCenter

```
vCenter Server (vcenter.lab.local)
+-- Datacenter: "DC-Milano"
|   +-- [Cluster: "CL-Production"]
|   |   +-- ESXi Host: esxi-prod-01  ->  VM: web-server-01, app-server-01
|   |   +-- ESXi Host: esxi-prod-02  ->  VM: db-server-01, db-server-02
|   |   +-- [Resource Pool: "RP-Web"]
|   |   +-- [vApp: "3-Tier Application"]
|   +-- [Cluster: "CL-Development"]
|   +-- [Folder: "Templates"]
+-- Datacenter: "DC-Roma"
    +-- [Cluster: "CL-DR"]
```

| Oggetto | Descrizione | Equivalente Proxmox |
|---|---|---|
| Datacenter | Container logico top-level | Datacenter (concetto) |
| Cluster | Gruppo di host per HA/DRS | Cluster Proxmox |
| Resource Pool | Suddivisione risorse | Pool di risorse |
| Folder | Organizzazione logica | Tag / Pool |
| vApp | Gruppo VM con ordine di avvio | N/A (scripting) |

### vCenter HA e Enhanced Linked Mode

**vCenter HA**: cluster active/passive/witness per proteggere vCenter (non le VM). Replica PostgreSQL streaming, failover 5-10 minuti, IP di management migra al nuovo active.

**Enhanced Linked Mode**: collega piu vCenter (stesso dominio SSO) per inventario unificato, cross-vCenter vMotion, ruoli condivisi. Fino a 15 vCenter in linked mode (vSphere 8.0).

---

## Gestione VM in vSphere

### VM Hardware Versions

| HW Version | vSphere | Max vCPU | Max RAM | Novita |
|---|---|---|---|---|
| vmx-13 | 6.5 | 128 | 6 TB | NVMe, UEFI Secure Boot |
| vmx-14 | 6.7 | 128 | 6 TB | NVDIMM, PMEM |
| vmx-17 | 7.0 | 256 | 24 TB | vTPM, Watchdog timer |
| vmx-19 | 7.0 U2 | 768 | 24 TB | WDDM GPU |
| vmx-20 | 8.0 | 768 | 24 TB | vGPU profiles, passthrough |
| vmx-21 | 8.0 U2 | 768 | 24 TB | DPU offloading |

### File della VM e VMX

Ogni VM e composta da file nel datastore: `.vmx` (configurazione testo), `.vmdk` (descriptor disco), `-flat.vmdk` (dati disco), `.nvram` (BIOS/UEFI), `.vmsd` (metadata snapshot), `.vswp` (swap in running), `.log` (log).

```ini
# Parametri chiave del file VMX
virtualHW.version = "20"
displayName = "web-server-01"
guestOS = "ubuntu64Guest"
memSize = "8192"
numvcpus = "4"
scsi0.virtualDev = "pvscsi"
ethernet0.virtualDev = "vmxnet3"
firmware = "efi"
uefi.secureBoot.enabled = "TRUE"
```

### Tipi di VMDK

| Tipo | Allocazione Spazio | Zeri | Performance | Uso |
|---|---|---|---|---|
| Thick Eager-Zeroed | Immediata | Scritti alla creazione | Migliore | Database, FT |
| Thick Lazy-Zeroed | Immediata | On-demand | Buona | Uso generale |
| Thin Provisioned | On-demand (cresce) | N/A | Buona | Dev, overcommit |

```bash
# Verificare tipo provisioning
vmkfstools -D /vmfs/volumes/datastore1/vm/vm.vmdk

# Convertire thin a thick
vmkfstools -i source.vmdk dest.vmdk -d eagerzeroedthick

# Clonare VMDK
vmkfstools -i source.vmdk clone.vmdk -d thin
```

### VMware Tools

Driver e agent installati nel guest OS per performance e funzionalita avanzate: SVGA driver, VMXNET3 (rete paravirtualizzata), PVSCSI (storage paravirtualizzato), memory balloon, guest customization, quiesced snapshots, time sync.

**Nota migrazione**: VMware Tools DEVE essere disinstallato o sostituito con QEMU Guest Agent dopo la migrazione. Driver PVSCSI e VMXNET3 non sono compatibili con KVM.

### OVF/OVA e Conversione

```bash
# Esportare VM come OVA
ovftool vi://root@esxi-host/vm-name /tmp/vm-name.ova

# Convertire per Proxmox
tar xvf vm-name.ova
qemu-img convert -f vmdk -O qcow2 vm-name-disk1.vmdk vm-name.qcow2
```

### Snapshot Management

Gli snapshot catturano lo stato della VM tramite delta disk chain. Ogni scrittura va nel delta corrente; le letture attraversano la catena fino al disco base.

**Regole critiche**: snapshot NON sono backup; non mantenere oltre 24-72 ore; catene lunghe degradano I/O; consolidare TUTTI gli snapshot PRIMA della migrazione.

```bash
vim-cmd vmsvc/snapshot.get <vmid>                           # Lista snapshot
vim-cmd vmsvc/snapshot.removeall <vmid>                     # Rimuovi tutti
```

### Cloning e vMotion

| Tipo Clone | Descrizione | Storage |
|---|---|---|
| Full Clone | Copia completa indipendente | 100% spazio |
| Linked Clone | Condivide base disk | Solo delta |
| Instant Clone | Fork VM in running | Copy-on-write |

**vMotion** requisiti: CPU compatibili (stesso vendor/EVC), shared storage o Storage vMotion, rete vMotion dedicata (raccomandato 10 Gbps), latenza < 100ms.

---

## vSphere Permissions

### Modello di Autorizzazione

vSphere usa RBAC con ereditarieta: Permission = User/Group + Role + Object + Propagate. I permessi si ereditano dal padre ai figli nella gerarchia dell'inventario.

### Ruoli Predefiniti

| Ruolo | Descrizione |
|---|---|
| Administrator | Accesso completo a tutto |
| Read-Only | Solo visualizzazione |
| No Access | Nessun accesso (override ereditarieta) |
| No Cryptography Administrator | Come Admin senza crypto |
| Network Administrator | Gestione reti |
| Virtual Machine Power User | Power on/off, console, snapshot |
| Virtual Machine User | Solo console e interazione |

```powershell
# Creare ruolo personalizzato
New-VIRole -Name "VM-Operator" -Privilege (
    Get-VIPrivilege -Id @(
        "VirtualMachine.Interact.PowerOn",
        "VirtualMachine.Interact.PowerOff",
        "VirtualMachine.Interact.ConsoleInteract",
        "VirtualMachine.State.CreateSnapshot",
        "VirtualMachine.State.RemoveSnapshot"
    )
)

# Assegnare ruolo
New-VIPermission -Entity (Get-Cluster "CL-Production") `
    -Principal "DOMAIN\vm-operators" -Role "VM-Operator" -Propagate:$true

# Esportare permessi (pre-migrazione)
Get-VIPermission | Select-Object `
    @{N='Entity';E={$_.Entity.Name}},
    @{N='Principal';E={$_.Principal}},
    @{N='Role';E={$_.Role}},
    @{N='Propagate';E={$_.Propagate}} |
    Export-Csv -Path "vsphere-permissions.csv" -NoTypeInformation
```

---

## Inventario e Assessment

### Obiettivi dell'Assessment Pre-Migrazione

Prima di migrare, documentare completamente: inventario host (hw, versioni), inventario VM (risorse, OS, dipendenze), networking (vSwitch, VLAN, IP), storage (datastore, VMDK), cluster (HA, DRS, resource pool), permessi, backup.

### Comandi PowerCLI per Inventario Completo

```powershell
# Connessione
Connect-VIServer -Server vcenter.lab.local -User administrator@vsphere.local

# === HOST ===
Get-VMHost | Select-Object Name,
    @{N='Version';E={$_.Version}},
    @{N='Build';E={$_.Build}},
    @{N='Model';E={$_.Model}},
    @{N='CPUCores';E={$_.ExtensionData.Hardware.CpuInfo.NumCpuCores}},
    @{N='CPUThreads';E={$_.ExtensionData.Hardware.CpuInfo.NumCpuThreads}},
    @{N='MemoryGB';E={[math]::Round($_.MemoryTotalGB,2)}},
    @{N='MemoryUsedGB';E={[math]::Round($_.MemoryUsageGB,2)}} |
    Export-Csv -Path "host-inventory.csv" -NoTypeInformation

# === VM COMPLETO ===
Get-VM | Select-Object Name,
    @{N='PowerState';E={$_.PowerState}},
    @{N='GuestOS';E={$_.ExtensionData.Config.GuestFullName}},
    @{N='NumCPU';E={$_.NumCpu}},
    @{N='MemoryGB';E={$_.MemoryGB}},
    @{N='HWVersion';E={$_.HardwareVersion}},
    @{N='VMHost';E={$_.VMHost.Name}},
    @{N='Cluster';E={$_.VMHost.Parent.Name}},
    @{N='ToolsStatus';E={$_.ExtensionData.Guest.ToolsStatus}},
    @{N='IPAddress';E={$_.Guest.IPAddress -join ','}},
    @{N='UsedSpaceGB';E={[math]::Round($_.UsedSpaceGB,2)}},
    @{N='ProvisionedSpaceGB';E={[math]::Round($_.ProvisionedSpaceGB,2)}},
    @{N='Firmware';E={$_.ExtensionData.Config.Firmware}},
    @{N='UUID';E={$_.ExtensionData.Config.Uuid}} |
    Export-Csv -Path "vm-inventory.csv" -NoTypeInformation

# === DISCHI VM ===
Get-VM | ForEach-Object {
    $vmName = $_.Name
    $_ | Get-HardDisk | Select-Object `
        @{N='VM';E={$vmName}},
        @{N='CapacityGB';E={[math]::Round($_.CapacityGB,2)}},
        @{N='StorageFormat';E={$_.StorageFormat}},
        @{N='Filename';E={$_.Filename}},
        @{N='Datastore';E={$_.Filename -replace '\[([^\]]+)\].*','$1'}}
} | Export-Csv -Path "vm-disks.csv" -NoTypeInformation

# === SNAPSHOT (CRITICO: rimuovere prima della migrazione) ===
Get-VM | Get-Snapshot | Select-Object `
    @{N='VM';E={$_.VM.Name}}, Name, Created,
    @{N='SizeGB';E={[math]::Round($_.SizeGB,2)}} |
    Export-Csv -Path "vm-snapshots.csv" -NoTypeInformation

# === NETWORKING ===
Get-VMHost | ForEach-Object {
    $h = $_.Name
    $_ | Get-VirtualPortGroup | Select-Object `
        @{N='Host';E={$h}}, Name, VLanId, VirtualSwitchName
} | Export-Csv -Path "portgroups.csv" -NoTypeInformation

Get-VDSwitch | Select-Object Name, Version, Mtu,
    @{N='NumUplinks';E={$_.NumUplinkPorts}},
    @{N='NIOC';E={$_.ExtensionData.Config.NetworkResourceManagementEnabled}} |
    Export-Csv -Path "dvswitches.csv" -NoTypeInformation

# === STORAGE ===
Get-Datastore | Select-Object Name, Type,
    @{N='CapacityGB';E={[math]::Round($_.CapacityGB,2)}},
    @{N='FreeSpaceGB';E={[math]::Round($_.FreeSpaceGB,2)}},
    @{N='PercentUsed';E={
        [math]::Round(($_.CapacityGB - $_.FreeSpaceGB) / $_.CapacityGB * 100, 1)
    }},
    @{N='VMFSVersion';E={$_.FileSystemVersion}} |
    Export-Csv -Path "datastores.csv" -NoTypeInformation

# === CLUSTER ===
Get-Cluster | Select-Object Name,
    @{N='HAEnabled';E={$_.HAEnabled}},
    @{N='DrsEnabled';E={$_.DrsEnabled}},
    @{N='DrsAutomationLevel';E={$_.DrsAutomationLevel}},
    @{N='EVCMode';E={$_.EVCMode}},
    @{N='NumHosts';E={($_ | Get-VMHost).Count}},
    @{N='NumVMs';E={($_ | Get-VM).Count}} |
    Export-Csv -Path "cluster-config.csv" -NoTypeInformation
```

### Checklist Pre-Migrazione

```
+===================================================================+
|              CHECKLIST ASSESSMENT PRE-MIGRAZIONE                   |
+===================================================================+
|                                                                    |
|  [ ] Inventario host ESXi (hardware, versioni, configurazioni)    |
|  [ ] Inventario VM (risorse, OS, IP, dipendenze)                  |
|  [ ] Mappatura networking (vSwitch, VLAN, IP ranges)              |
|  [ ] Mappatura storage (datastore, LUN, NFS mounts)              |
|  [ ] Snapshot VM documentati e piano per rimozione                |
|  [ ] VMware Tools versioni documentate                            |
|  [ ] Configurazione HA/DRS documentata                            |
|  [ ] Resource Pool e limiti documentati                           |
|  [ ] Permessi e ruoli esportati                                    |
|  [ ] Licenze correnti e scadenze documentate                      |
|  [ ] Backup correnti verificati e policy documentata              |
|  [ ] Dipendenze tra VM mappate (app tiers, DB links)             |
|  [ ] RDM identificati e piano conversione                         |
|  [ ] GPU/USB passthrough identificato                              |
|  [ ] Affinity / Anti-affinity rules documentate                   |
|  [ ] Ordine avvio VM (vApp / startup order) documentato           |
|  [ ] Performance baseline raccolta (CPU, RAM, I/O, rete)         |
|                                                                    |
+===================================================================+
```

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — Lifecycle ESXi 8.0 al 2026-04-26.** La famiglia 8.0 ha ricevuto patch fino a `8.0.3 P08` (build `25205845`, 2026-02-24). Non esiste una `8.1`: Broadcom ha consolidato gli aggiornamenti dentro la linea 8.0.x. Il modello "Update N" e stato sostituito da "Px" patch release. Riferimento: [`VM-LIFECYCLE`] `https://knowledge.broadcom.com/external/article?legacyId=2143832`.

> **Errore comune — VMware Tools "PowerCLI dice ToolsOK ma sono vecchi".** Il campo `ExtensionData.Guest.ToolsStatus` risponde `toolsOk` finche i Tools rispondono allo heartbeat, indipendentemente dalla loro versione. Per rilevare versioni datate, usare `ExtensionData.Guest.ToolsVersion` e confrontarla con `ToolsVersionStatus` (`guestToolsCurrent` / `guestToolsNeedUpgrade`). In pre-migrazione, allineare prima i Tools — un guest con Tools obsoleti spesso ha anche driver di rete non firmati, e l'iniezione VirtIO con `virt-v2v` puo fallire o produrre rete non funzionante.

> **Caso reale — CVE-2024-37085 (ESXi AD authentication bypass, sfruttato dal 2024-07).** Una vulnerabilita di autenticazione su ESXi 7.0/8.0 permetteva di ottenere privilegi amministrativi creando in Active Directory un gruppo chiamato `ESX Admins` e iscrivendovi un account compromesso. Sfruttata da gruppi ransomware (Storm-0506/Akira) per cifrare datastore VMFS in pochi minuti dopo il primo accesso. Conseguenza pratica per il corso: 1) hardenizzare l'integrazione ESXi↔AD prima della migrazione e disattivare l'auth AD non rigorosamente necessaria; 2) considerare una finestra di migrazione *piu corta* per gli host ancora esposti come uno dei criteri di prioritizzazione delle wave (modulo 05). Riferimento: avvisi Microsoft Threat Intelligence e Broadcom KB su `CVE-2024-37085`. Vedi anche `../99-CASE-STUDY/cve-2024-37085-esxi-ad-bypass.md` (in preparazione).

---

## Esercizi

1. **Concettuale — TPS Inter-VM.** Spiegare con parole proprie perche TPS Inter-VM e disabilitato di default da vSphere 6.0 e quale tipo di attacco (con quale primitiva di lettura) ha motivato la decisione. *Suggerimento:* il side-channel sfrutta la latenza di accesso alla pagina condivisa per inferirne il contenuto. Riferimenti: KB Broadcom 2080735 e Suzaki et al., "Memory Deduplication as a Threat to the Guest OS" (EuroSec 2011).
2. **Lab — assessment minimo via PowerCLI.** In un lab vSphere connesso (Connect-VIServer su un vCenter di test), eseguire i blocchi PowerCLI riportati nel modulo per generare:
   - `host-inventory.csv`
   - `vm-inventory.csv`
   - `vm-disks.csv`
   - `vm-snapshots.csv`
   - `portgroups.csv`
   - `dvswitches.csv`
   - `datastores.csv`
   - `cluster-config.csv`

   Verificare che il numero di righe in `vm-inventory.csv` corrisponda a `(Get-VM).Count`. Verificare inoltre che ogni VM abbia almeno un disco in `vm-disks.csv` (un orphan-VM senza dischi e una VM da indagare prima della migrazione).

3. **Scenario — upgrade hardware version pre-migrazione.** Hai 12 VM con `HW Version vmx-14` su vSphere 6.7. Devi migrarle a Proxmox VE 8.x. Argomenta in massimo 10 righe se conviene, prima della migrazione, eseguire un upgrade dell'hardware version a `vmx-19/20`, oppure se conviene migrare cosi come sono. *Risposta attesa:* l'upgrade di hardware version e irreversibile (non si torna indietro senza ripristino da backup) e non porta benefici alla migrazione perche `qemu-img` / `virt-v2v` leggono il VMDK, non l'envelope hardware. Quindi non eseguirlo. Concentrarsi piuttosto su (a) rimozione di tutti gli snapshot, (b) pre-installazione dei driver VirtIO se Windows, (c) audit dei `ToolsVersionStatus`.
4. **Stretch — EVC baseline mista.** Costruire una matrice di compatibilita CPU per EVC mode su due cluster: uno con Intel Skylake-SP, uno misto Skylake / Cascade Lake / Ice Lake. Indicare il livello EVC piu basso comune e quale instruction set esso espone (AVX-512? VPCLMULQDQ?). Specificare se sono ammessi vMotion fra Skylake-SP e Ice Lake con baseline `Skylake`. Riferimento: VMware KB sugli EVC baselines per generazione (cercare "EVC modes by processor generation").

## Auto-valutazione

Rispondere senza riguardare il modulo. La risposta deve essere precisa, non solo «direzionale».

1. Quali sono i tre processi user-world principali su un host ESXi e cosa fa ciascuno?
2. In quale sezione (rispetto a questo file) viene introdotto il concetto di "ready time" e quale soglia indica saturazione CPU?
3. Quale comando `esxcli` mostra la versione e il build di ESXi?
4. Da quale versione di vSphere il vCenter su Windows e deprecato e che VM ne prende il posto (nome del prodotto, OS sottostante, db embedded)?
5. Cosa rappresenta la sigla `vmx-21` e in quale versione di vSphere e introdotta?
6. Tre file fondamentali che compongono una VM nel datastore e cosa contiene ciascuno.
7. Spiegare in 2 righe perche `VMware Tools` deve essere rimosso prima della migrazione a Proxmox e che cosa lo sostituisce.
8. Dimensione tipica di una vCSA "Medium" in CPU/RAM/storage e fino a quanti host puo gestire?

(Le risposte si trovano dentro il modulo: §ESXi Hypervisor, §vCenter Server, §Gestione VM. Se piu di 3 risposte non emergono in 5 minuti, rileggere la sezione corrispondente prima di procedere al modulo 01.2.)

## Letture primarie consigliate

- [`VM-DOCS`] VMware vSphere Documentation. https://docs.vmware.com/en/VMware-vSphere/ — pagina di ingresso ufficiale.
- [`VM-LIFECYCLE`] ESXi 8.0 build numbers and versions. https://knowledge.broadcom.com/external/article?legacyId=2143832
- [`VM-OVF`] OVF specification (DMTF DSP0243). https://www.dmtf.org/standards/ovf
- KB Broadcom 2080735 — Disabling Transparent Page Sharing salt (Inter-VM TPS, side-channel). https://knowledge.broadcom.com/external/article?legacyId=2080735
- VMware KB sui requisiti di storage persistente per ESXi (cambiamenti 7.0 U3c+). Cercare "ESXi system storage" su `https://knowledge.broadcom.com/`.
- CVE-2024-37085 — ESXi Active Directory authentication bypass. Pagina ufficiale VMSA su `https://www.broadcom.com/support/vmware-security-advisories`.
- Suzaki, Iijima, Yagi, Artho, "Memory Deduplication as a Threat to the Guest OS", EuroSec 2011 — paper di riferimento sul side-channel TPS.

Tutti gli ID `VM-*` e `PVE-*` sono consolidati in `../00-BIBLIOGRAFIA.md`.

## Collegamenti incrociati

- Modulo 01.2 — `../01-FONDAMENTI-VMWARE/vmware-networking-storage.md`: prosegue con vSwitch standard, vDS, VMFS, vSAN, NFS/iSCSI lato VMware.
- Modulo 02.1 — `../02-FONDAMENTI-PROXMOX-VE/architettura-installazione-proxmox.md`: la stessa storia raccontata dal lato Proxmox (KVM, pmxcfs, Corosync, web GUI 8006).
- Modulo 05.1 — `../05-ASSESSMENT-E-PIANIFICAZIONE/inventario-vmware-assessment.md`: estende gli output PowerCLI di questo modulo per pianificare il dimensionamento target.
- Modulo 06.1 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/strategie-metodi-migrazione.md`: prima destinazione operativa dopo i fondamenti.
- Modulo 09.4 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-windows-server-vm.md`: applicazione concreta della rimozione VMware Tools + iniezione VirtIO.
- Modulo 12.1 — `../12-SICUREZZA-E-COMPLIANCE/sicurezza-compliance.md`: il post-migrazione lato sicurezza (auth, audit, certificati).
- Modulo 17.1 — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-cluster-proxmox.md`: troubleshooting Corosync/quorum dal lato target.

## Glossario locale

| Termine | Definizione (in questo modulo) |
|---|---|
| **VMkernel** | Microkernel proprietario di ESXi che esegue scheduling CPU, memoria, driver. *Non e Linux*. |
| **User World** | Processo userspace su ESXi (es. `vmx`, `hostd`, `vpxa`, `sfcbd`, `dcui`). |
| **vCSA** | vCenter Server Appliance — VM Linux (Photon OS) con tutti i servizi vCenter integrati, da vSphere 6.5+. |
| **PSC** | Platform Services Controller, contiene SSO. Dalla 7.0 e sempre embedded nel vCenter. |
| **TPS** | Transparent Page Sharing — deduplicazione di pagine RAM identiche; Inter-VM disabilitato di default da 6.0 per side-channel. |
| **Ballooning** | Driver `vmmemctl` (in VMware Tools) che forza il guest a paginare per liberare RAM fisica all'host. |
| **EVC** | Enhanced vMotion Compatibility — livello CPU baseline che maschera istruzioni avanzate per consentire vMotion fra generazioni di CPU diverse. |
| **HW Version** | `vmx-NN` — versione dell'hardware virtuale; controlla feature massime (vCPU, RAM, dispositivi). Irreversibile in upgrade. |
| **VMDK** | Formato disco VMware. File descriptor (`.vmdk`) + dato `-flat.vmdk` (o split a 2 GB). |
| **PVSCSI / VMXNET3** | Driver paravirtualizzati VMware. *Non compatibili con KVM* — vanno sostituiti con VirtIO al passaggio a Proxmox. |
| **vMotion** | Migrazione live di VM fra host ESXi (intra-cluster). Equivalente Proxmox: `qm migrate --online`. |
| **EOGS** | End of General Support — fine del supporto regolare (patch ordinarie). Per vSphere 6.5/6.7 e ottobre 2022. |
| **Lockdown mode** | Modalita ESXi che disabilita l'accesso diretto all'host: tutto deve passare via vCenter. Strict / Normal / Disabled. |
