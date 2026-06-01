# Virtualizzazione Linux — Guida Completa

> **Modulo 15** · **Aggiornamento:** 2026-05-24

## Idee guida
1. **KVM + QEMU foundation; libvirt management layer.**
2. **virt-manager per UI; `virsh` per CLI.**
3. **Proxmox VE = libvirt-free Debian-based hypervisor (vedi corso 10).**
4. **LXD/Incus per system container.**
5. **Type 1 hypervisor = bare-metal; Type 2 = hosted. KVM è Type 1.**
6. **virtio = paravirtualizzazione ad alte performance; sempre preferirlo.**
7. **GPU passthrough (VFIO) sblocca carichi GPU-intensive nelle VM.**


## Indice

- [Panoramica](#panoramica)
- [Tipi di Virtualizzazione](#tipi-di-virtualizzazione)
- [Type 1 vs Type 2 — Confronto Approfondito](#type-1-vs-type-2--confronto-approfondito)
- [KVM/QEMU: Architettura e Fondamenti](#kvmqemu-architettura-e-fondamenti)
- [QEMU 9.x e libvirt 10.x — Novità 2024-2025](#qemu-9x-e-libvirt-10x--novità-2024-2025)
- [libvirt: Architettura e Domain XML](#libvirt-architettura-e-domain-xml)
- [virsh — Riferimento Completo](#virsh--riferimento-completo)
- [virt-manager (GUI)](#virt-manager-gui)
- [Creazione VM Avanzata](#creazione-vm-avanzata)
- [Formati Disco QEMU: qcow2, raw, vmdk](#formati-disco-qemu-qcow2-raw-vmdk)
- [Networking VM](#networking-vm)
- [Open vSwitch — Fondamenti](#open-vswitch--fondamenti)
- [Storage VM](#storage-vm)
- [Performance Tuning KVM](#performance-tuning-kvm)
- [Migrazione Live](#migrazione-live)
- [Snapshot e Backup VM](#snapshot-e-backup-vm)
- [GPU Passthrough (VFIO)](#gpu-passthrough-vfio)
- [Cloud-init: Provisioning Automatizzato](#cloud-init-provisioning-automatizzato)
- [Vagrant: Ambienti Riproducibili](#vagrant-ambienti-riproducibili)
- [Virtualizzazione Nidificata](#virtualizzazione-nidificata)
- [Kata Containers e MicroVM](#kata-containers-e-microvm)
- [Sicurezza delle VM](#sicurezza-delle-vm)
- [Proxmox VE](#proxmox-ve)
- [Confronto: KVM vs Proxmox vs VMware vs Hyper-V](#confronto-kvm-vs-proxmox-vs-vmware-vs-hyper-v)
- [VDI — Virtual Desktop Infrastructure con Linux](#vdi--virtual-desktop-infrastructure-con-linux)
- [Setup KVM da Zero — Passo per Passo](#setup-kvm-da-zero--passo-per-passo)
- [Best Practices](#best-practices)
- [Troubleshooting — 25+ Problemi Comuni](#troubleshooting--25-problemi-comuni)
- [FAQ — 18 Domande Frequenti](#faq--18-domande-frequenti)

---

## Panoramica

La virtualizzazione permette di eseguire più sistemi operativi su un singolo host fisico. KVM (Kernel-based Virtual Machine) è l'hypervisor integrato nel kernel Linux, combinato con QEMU per l'emulazione hardware. libvirt è il layer di gestione standard, con virsh (CLI) e virt-manager (GUI). Proxmox VE è una piattaforma completa di virtualizzazione basata su KVM e LXC.

### Concetti Fondamentali

| Termine | Definizione |
|---|---|
| **Hypervisor** | Software che crea e gestisce le macchine virtuali. Astrae l'hardware fisico |
| **Host** | La macchina fisica su cui gira l'hypervisor |
| **Guest** | Il sistema operativo virtualizzato (la VM) |
| **vCPU** | CPU virtuale assegnata alla VM. Mappata su thread fisici del processore |
| **Paravirtualizzazione** | Il guest sa di essere virtualizzato e usa driver ottimizzati (virtio) |
| **Full virtualization** | Il guest non sa di essere virtualizzato. L'hardware è emulato completamente |
| **Thin provisioning** | Lo spazio disco è allocato on-demand, non pre-allocato |
| **Overcommit** | Assegnare più risorse virtuali di quelle fisiche disponibili |
| **IOMMU** | Unità hardware (Intel VT-d / AMD-Vi) che permette il passthrough diretto di dispositivi PCI |
| **SR-IOV** | Single Root I/O Virtualization — permette a un dispositivo PCI di apparire come multipli |

### Evoluzione della Virtualizzazione su Linux

```text
Timeline:
2003 — Xen: primo hypervisor Linux enterprise
2006 — Intel VT-x / AMD-V: supporto hardware alla virtualizzazione
2007 — KVM: merge nel kernel Linux (2.6.20)
2008 — libvirt diventa lo standard de facto per la gestione
2010 — VirtIO standardizzato (paravirtualizzazione I/O)
2012 — VFIO: framework per GPU/device passthrough
2014 — Proxmox VE adotta ZFS e Ceph nativamente
2018 — Cloud-init diventa lo standard per il provisioning VM
2020 — Incus (fork di LXD) per container di sistema
2024 — KVM supporta Confidential Computing (SEV-SNP, TDX)
```

---

## Tipi di Virtualizzazione

### Classificazione Generale

```text
Virtualizzazione
├── Hardware (Hypervisor)
│   ├── Type 1 — Bare-metal
│   │   ├── KVM (Linux kernel)
│   │   ├── Xen
│   │   ├── VMware ESXi
│   │   └── Microsoft Hyper-V
│   └── Type 2 — Hosted
│       ├── VirtualBox
│       ├── VMware Workstation / Fusion
│       └── QEMU (senza KVM)
├── Container (OS-level)
│   ├── LXC / LXD / Incus
│   ├── Docker
│   ├── Podman
│   └── systemd-nspawn
├── Paravirtualizzazione
│   ├── VirtIO (I/O paravirtualizzato)
│   └── Xen PV (Xen paravirtualizzato)
└── Application
    ├── Wine
    ├── QEMU user-mode
    └── Darling (macOS su Linux)
```

### Type 1 — Bare-metal Hypervisor

L'hypervisor gira direttamente sull'hardware, senza un sistema operativo intermedio. Massima performance e isolamento.

**KVM** — Modulo del kernel Linux. L'host Linux stesso è l'hypervisor.
- Vantaggi: integrato nel kernel, performance nativa, enorme community, gratuito
- Svantaggi: richiede Linux come host, gestione meno user-friendly di vSphere

**Xen** — Hypervisor indipendente. Il Dom0 (domain privilegiato) gestisce le VM.
- Vantaggi: isolamento forte (microkernel), usato da AWS (Nitro derivato da Xen)
- Svantaggi: complessità architetturale, community più piccola di KVM

**VMware ESXi** — Hypervisor proprietario enterprise.
- Vantaggi: ecosistema maturo (vSphere, vCenter, vSAN), supporto enterprise
- Svantaggi: licenze costose, vendor lock-in, chiusura del free tier nel 2024

**Microsoft Hyper-V** — Hypervisor integrato in Windows Server.
- Vantaggi: integrazione nativa Windows, supporto Microsoft
- Svantaggi: performance Linux guest inferiori a KVM, licenze Windows

### Type 2 — Hosted Hypervisor

L'hypervisor gira come applicazione su un sistema operativo esistente. Più semplice da usare, performance inferiori.

**VirtualBox** — Open source (Oracle), cross-platform.
- Vantaggi: gratuito, facile da usare, funziona su Linux/Windows/macOS
- Svantaggi: performance inferiori a KVM, problemi con kernel update
- Caso d'uso: sviluppo, test, laboratorio

**VMware Workstation / Fusion** — Prodotto commerciale desktop.
- Vantaggi: buona performance, snapshot avanzati, compatibilità ESXi
- Svantaggi: a pagamento (gratuito per uso personale dal 2024)

**QEMU senza KVM** — Emulazione software pura (no accelerazione hardware).
- Vantaggi: può emulare architetture diverse (ARM su x86, RISC-V, MIPS)
- Svantaggi: molto lento, solo per cross-compilation e test embedded

---

## Type 1 vs Type 2 — Confronto Approfondito

| Caratteristica | Type 1 (KVM, Xen, ESXi) | Type 2 (VirtualBox, Workstation) |
|---|---|---|
| **Posizione** | Direttamente sull'hardware | Sopra un OS host |
| **Performance** | Near-native (1-5% overhead) | 10-30% overhead |
| **Overhead memoria** | Minimo | Significativo (host OS + hypervisor) |
| **Isolamento** | Forte (hardware-level) | Debole (dipende dall'host OS) |
| **Scalabilità** | Centinaia di VM per host | 5-10 VM tipico |
| **Caso d'uso** | Produzione, datacenter, cloud | Sviluppo, test, desktop |
| **Gestione** | CLI/API/web (virsh, vSphere) | GUI desktop |
| **Boot** | Boot diretto o con kernel host | Richiede OS host avviato |
| **Supporto GPU passthrough** | VFIO completo | Limitato |
| **Live migration** | Sì (nativa) | No / limitata |
| **Costo** | KVM/Xen gratuiti; ESXi a pagamento | VirtualBox gratuito; Workstation a pagamento |

### Quando usare Type 1

- Server di produzione
- Cloud infrastructure (OpenStack, Proxmox, oVirt)
- Workload ad alta performance
- Ambienti multi-tenant
- Conformità e sicurezza (isolamento hardware)

### Quando usare Type 2

- Sviluppo locale e test
- Laboratorio didattico
- Esecuzione occasionale di un OS diverso
- Cross-platform testing
- Demo e PoC rapidi

---

## KVM/QEMU: Architettura e Fondamenti

### Architettura Interna

```text
┌──────────────────────────────────────────────────┐
│                    User Space                     │
│  ┌─────────┐  ┌─────────┐  ┌──────────────────┐ │
│  │  virsh   │  │virt-mgr │  │  QEMU process    │ │
│  │  (CLI)   │  │ (GUI)   │  │  (per ogni VM)   │ │
│  └────┬─────┘  └────┬────┘  └───────┬──────────┘ │
│       │              │              │             │
│  ┌────▼──────────────▼──────────────┘             │
│  │           libvirt daemon                       │
│  │       (libvirtd / virtqemud)                   │
│  └──────────────────┬────────────────────────────┘│
├─────────────────────┼────────────────────────────┤
│                Kernel Space                       │
│  ┌──────────────────▼────────────────────────────┐│
│  │              KVM module                        ││
│  │    /dev/kvm — interfaccia ioctl               ││
│  │    Gestisce: vCPU, memoria, interrupts        ││
│  └──────────────────┬────────────────────────────┘│
├─────────────────────┼────────────────────────────┤
│              Hardware (CPU)                       │
│  ┌──────────────────▼────────────────────────────┐│
│  │  Intel VT-x / AMD-V (ring -1)                ││
│  │  VMX root mode (host) / VMX non-root (guest)  ││
│  │  EPT / NPT (nested page tables)              ││
│  └───────────────────────────────────────────────┘│
└──────────────────────────────────────────────────┘
```

### Come Funziona KVM

1. **KVM** è un modulo del kernel (`kvm.ko`, `kvm_intel.ko` o `kvm_amd.ko`)
2. Espone `/dev/kvm` — un character device con interfaccia ioctl
3. Ogni VM è un processo QEMU nello user-space
4. QEMU usa `/dev/kvm` per delegare l'esecuzione CPU all'hardware
5. Le istruzioni privilegiate del guest causano un **VM-exit** → KVM le gestisce → **VM-entry** di ritorno
6. EPT (Intel) / NPT (AMD) gestiscono la traduzione degli indirizzi di memoria senza overhead software

### QEMU: Ruolo e Funzionalità

QEMU da solo è un emulatore completo. Con KVM, QEMU delega l'esecuzione CPU all'hardware e gestisce:

- **Emulazione dispositivi**: scheda video (VGA/virtio-gpu), scheda di rete (e1000, virtio-net), controller disco (IDE, AHCI, virtio-blk, virtio-scsi), USB, seriale, audio
- **Firmware**: SeaBIOS (BIOS legacy), OVMF/AAVMF (UEFI), OpenSBI (RISC-V)
- **Monitor QEMU**: interfaccia di controllo (accessibile via socket o stdio)
- **Machine types**: pc (i440FX), q35 (ICH9, PCIe nativo), virt (ARM)

### Prerequisiti e Installazione

```bash
# Verificare supporto hardware virtualizzazione
grep -Ec '(vmx|svm)' /proc/cpuinfo    # > 0 = supportato
# vmx = Intel VT-x, svm = AMD-V

# Verificare che KVM sia utilizzabile
ls -la /dev/kvm                        # Deve esistere
# Se manca: BIOS → abilitare VT-x/AMD-V

# Verificare IOMMU (necessario per GPU passthrough)
dmesg | grep -i iommu

lsmod | grep kvm                       # Moduli caricati

# ── Installazione su Debian/Ubuntu ──────────────────
sudo apt install qemu-kvm libvirt-daemon-system \
  libvirt-clients virtinst bridge-utils virt-manager \
  qemu-utils ovmf

# ── Installazione su RHEL/Fedora ────────────────────
sudo dnf install qemu-kvm libvirt virt-install virt-manager \
  qemu-img edk2-ovmf

# ── Installazione su Arch Linux ─────────────────────
sudo pacman -S qemu-full libvirt virt-manager virt-install \
  dnsmasq bridge-utils edk2-ovmf

# Aggiungere utente ai gruppi necessari
sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER
# Logout/login necessario per applicare i gruppi

# Abilitare e avviare il servizio
sudo systemctl enable --now libvirtd
sudo systemctl enable --now virtlogd

# Verificare
virsh list --all                       # Deve funzionare senza errori
sudo systemctl status libvirtd
virsh uri                              # Deve mostrare qemu:///system
```

### Connessioni QEMU/libvirt

```bash
# Connessione di sistema (root, accesso completo a rete e storage)
virsh -c qemu:///system list --all

# Connessione utente (no bridge, no storage system-wide)
virsh -c qemu:///session list --all

# Connessione remota via SSH
virsh -c qemu+ssh://user@host/system list --all

# Connessione remota via TLS
virsh -c qemu+tls://host/system list --all

# Variabile d'ambiente per default
export LIBVIRT_DEFAULT_URI="qemu:///system"
```

---

## QEMU 9.x e libvirt 10.x — Novità 2024-2025

### QEMU 9.0 (Aprile 2024)

QEMU 9.0 introduce miglioramenti significativi per migrazione, I/O e architetture emergenti:

**Migrazione mapped-ram**: nuovo formato di migrazione a file con indice strutturato. La memoria viene scritta con offset noti, permettendo seek diretto alle pagine dirty. Risultato: migrazione a file fino a **2× più veloce** e compatibilità con backup multifd paralleli.

**virtio-blk multiqueue**: supporto nativo per code I/O multiple su dispositivi virtio-blk, distribuendo il carico su più vCPU. Prestazioni I/O random migliorano linearmente con il numero di code (testato fino a 8 code su NVMe).

**RISC-V**: emulazione migliorata delle estensioni Vector, supporto per il profilo RVA22, e boot UEFI tramite EDK2 per RISC-V.

### QEMU 9.1 (Agosto 2024)

**Compressione offload IAA/UADK**: la migrazione multifd supporta l'offload della compressione su acceleratori hardware Intel IAA (In-Memory Analytics Accelerator) e Huawei UADK. Su hardware supportato, la compressione non impatta più la CPU host.

**Post-copy failure recovery**: migliorato il meccanismo di recupero in caso di fallimento durante la migrazione post-copy. QEMU 9.1 tenta automaticamente la riconnessione del canale di migrazione e la ripresa del trasferimento pagine, riducendo il rischio di VM irrecuperabili.

**VIRTIO_F_NOTIFICATION_DATA**: feature flag VirtIO che permette al guest di includere dati aggiuntivi nelle notifiche al device, riducendo il numero di MMIO exit. Impatto misurabile su workload I/O intensivi con molte code VirtIO.

```bash
# Verificare versione QEMU
qemu-system-x86_64 --version

# Verificare feature supportate
qemu-system-x86_64 -device virtio-net-pci,help 2>&1 | grep -i notification

# Query capability migrazione
virsh qemu-monitor-command vm_name '{"execute": "query-migrate-capabilities"}' --pretty
```

### QEMU 9.2 (Dicembre 2024)

**Emulazione AWS Nitro Enclaves**: supporto sperimentale per l'emulazione del modello di enclave Nitro, permettendo sviluppo e test locale di applicazioni enclave senza hardware AWS.

**virtio-gpu Venus (Vulkan 3D)**: accelerazione 3D tramite il backend Venus che espone un'interfaccia Vulkan nativa al guest. Prestazioni grafiche 3D significativamente migliorate rispetto al precedente virgl (OpenGL), con supporto per applicazioni Vulkan 1.3.

**Device model sperimentali in Rust**: primi device model QEMU scritti in Rust (PL011 UART per ARM), con l'obiettivo di migliorare la sicurezza della memoria nell'emulazione device. Il framework qemu-rs permette di scrivere nuovi device in Rust mantenendo compatibilità con il codice C esistente.

### libvirt 10.x — Novità 2024-2025

**Auto IOMMU EIM per >255 vCPU**: libvirt 10.x abilita automaticamente Extended Interrupt Mode (EIM) nell'IOMMU virtuale quando la VM supera 255 vCPU, eliminando un'intera categoria di errori di configurazione per VM di grandi dimensioni.

**Driver Cloud Hypervisor**: supporto nativo per Cloud Hypervisor come hypervisor backend, affiancando QEMU e Xen. Permette di gestire VM Cloud Hypervisor con `virsh` e le API libvirt standard.

**Reti forward mode='open'**: nuovo modo di forwarding di rete che permette configurazioni personalizzate senza che libvirt gestisca iptables/nftables. Utile per integrazioni con CNI Kubernetes e SDN esterni.

```xml
<!-- Rete open mode (libvirt 10.x) -->
<network>
  <name>k8s-net</name>
  <forward mode='open'/>
  <bridge name='br-k8s'/>
</network>
```

**Snapshot UEFI interni**: risolto il supporto per snapshot interni di VM con firmware UEFI (OVMF). Le variabili NVRAM vengono ora incluse correttamente nello snapshot, permettendo rollback completo dello stato UEFI.

**Hyper-V virttype**: supporto per la gestione di VM Hyper-V, permettendo a libvirt di orchestrare hypervisor Microsoft tramite le stesse API.

```bash
# Verificare versione libvirt
virsh version --daemon

# Elencare hypervisor supportati
virsh capabilities | grep -A2 "type"

# Verificare supporto Cloud Hypervisor
virsh -c ch:///system list --all 2>/dev/null && echo "CH supportato"
```

---

## libvirt: Architettura e Domain XML

### Architettura libvirt

```text
┌──────────────────────────────────────────────┐
│                  Client Layer                │
│   virsh │ virt-manager │ oVirt │ OpenStack   │
│   Cockpit │ Ansible │ Terraform │ API custom │
└──────────────────┬───────────────────────────┘
                   │ libvirt API (C, Python, Go)
┌──────────────────▼───────────────────────────┐
│              libvirt Daemon                   │
│  ┌─────────────────────────────────────────┐ │
│  │  Driver QEMU/KVM    (virtqemud)         │ │
│  │  Driver LXC         (virtlxcd)          │ │
│  │  Driver Storage      (virtstoraged)     │ │
│  │  Driver Network      (virtnetworkd)     │ │
│  │  Driver Interface    (virtinterfaced)    │ │
│  │  Driver Secrets      (virtsecretd)      │ │
│  │  Driver Node Device  (virtnodedevd)     │ │
│  └─────────────────────────────────────────┘ │
│  Configurazioni: /etc/libvirt/               │
│  Domain XML: /etc/libvirt/qemu/              │
│  Log: /var/log/libvirt/qemu/                 │
└──────────────────────────────────────────────┘
```

### Demoni Modulari (libvirt 9.0+)

Le distribuzioni recenti usano demoni separati al posto del monolitico `libvirtd`:

```bash
# Demoni modulari (preferiti)
sudo systemctl enable --now virtqemud.socket
sudo systemctl enable --now virtnetworkd.socket
sudo systemctl enable --now virtstoraged.socket
sudo systemctl enable --now virtnodedevd.socket

# Oppure il demone monolitico (legacy)
sudo systemctl enable --now libvirtd.socket
```

### Domain XML — Struttura Completa

Il domain XML definisce completamente una VM. Ogni aspetto è configurabile.

```xml
<domain type='kvm'>
  <!-- Identità della VM -->
  <name>web-server-01</name>
  <uuid>a1b2c3d4-e5f6-7890-abcd-ef1234567890</uuid>
  <title>Web Server Produzione</title>
  <description>Server web con nginx e PostgreSQL</description>

  <!-- Memoria -->
  <memory unit='GiB'>8</memory>           <!-- Massima -->
  <currentMemory unit='GiB'>4</currentMemory>  <!-- Corrente (balloon) -->
  <memoryBacking>
    <hugepages>
      <page size='2048' unit='KiB'/>      <!-- Hugepages 2MB -->
    </hugepages>
    <locked/>                              <!-- Blocca in RAM (no swap) -->
  </memoryBacking>

  <!-- CPU -->
  <vcpu placement='static'>4</vcpu>
  <cpu mode='host-passthrough' check='none'>
    <topology sockets='1' dies='1' cores='2' threads='2'/>
    <numa>
      <cell id='0' cpus='0-3' memory='8' unit='GiB'/>
    </numa>
  </cpu>

  <!-- CPU Pinning (assegna vCPU a core fisici specifici) -->
  <cputune>
    <vcpupin vcpu='0' cpuset='2'/>
    <vcpupin vcpu='1' cpuset='3'/>
    <vcpupin vcpu='2' cpuset='6'/>
    <vcpupin vcpu='3' cpuset='7'/>
    <emulatorpin cpuset='0-1'/>
  </cputune>

  <!-- Boot e Firmware -->
  <os>
    <type arch='x86_64' machine='pc-q35-8.2'>hvm</type>
    <loader readonly='yes' type='pflash'>/usr/share/OVMF/OVMF_CODE_4M.fd</loader>
    <nvram>/var/lib/libvirt/qemu/nvram/web-server-01_VARS.fd</nvram>
    <boot dev='hd'/>
    <boot dev='cdrom'/>
  </os>

  <!-- Feature hardware -->
  <features>
    <acpi/>
    <apic/>
    <vmport state='off'/>
    <kvm>
      <hidden state='on'/>               <!-- Nasconde KVM da guest (anti-detect) -->
    </kvm>
  </features>

  <!-- Clock -->
  <clock offset='utc'>
    <timer name='rtc' tickpolicy='catchup'/>
    <timer name='pit' tickpolicy='delay'/>
    <timer name='hpet' present='no'/>
  </clock>

  <!-- Power management -->
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>destroy</on_crash>

  <!-- Dispositivi -->
  <devices>
    <!-- Emulazione -->
    <emulator>/usr/bin/qemu-system-x86_64</emulator>

    <!-- Disco principale (virtio-scsi per performance) -->
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='none' io='native' discard='unmap'/>
      <source file='/var/lib/libvirt/images/web-server-01.qcow2'/>
      <target dev='sda' bus='scsi'/>
      <address type='drive' controller='0' bus='0' target='0' unit='0'/>
    </disk>

    <!-- Controller SCSI (virtio-scsi) -->
    <controller type='scsi' model='virtio-scsi'>
      <driver queues='4'/>               <!-- Multi-queue -->
    </controller>

    <!-- Rete (virtio con multiqueue) -->
    <interface type='bridge'>
      <source bridge='br0'/>
      <model type='virtio'/>
      <driver name='vhost' queues='4'/>   <!-- vhost + multiqueue -->
    </interface>

    <!-- Console seriale -->
    <serial type='pty'>
      <target port='0'/>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console>

    <!-- Grafica (SPICE o VNC) -->
    <graphics type='spice' autoport='yes'>
      <listen type='address' address='127.0.0.1'/>
    </graphics>

    <!-- Video -->
    <video>
      <model type='virtio' heads='1' primary='yes'/>
    </video>

    <!-- Guest agent (comunicazione host-guest) -->
    <channel type='unix'>
      <target type='virtio' name='org.qemu.guest_agent.0'/>
    </channel>

    <!-- RNG (random number generator) -->
    <rng model='virtio'>
      <backend model='random'>/dev/urandom</backend>
    </rng>

    <!-- Balloon (ridimensionamento memoria dinamico) -->
    <memballoon model='virtio'>
      <stats period='10'/>
    </memballoon>
  </devices>
</domain>
```

### Operazioni su Domain XML

```bash
# Esportare XML di una VM
virsh dumpxml vm_name > vm_name.xml

# Importare/definire VM da XML
virsh define vm_name.xml

# Modificare XML in editor
virsh edit vm_name
# IMPORTANTE: virsh edit valida l'XML prima di applicarlo.
# Non modificare i file XML direttamente in /etc/libvirt/qemu/

# Confrontare configurazioni
diff <(virsh dumpxml vm1) <(virsh dumpxml vm2)
```

---

## virsh — Riferimento Completo

virsh è il client CLI per libvirt, lo strumento principale per la gestione delle VM.

### Stato e Informazioni

```bash
# STATO
virsh list                              # VM in esecuzione
virsh list --all                        # Tutte (incluse ferme)
virsh list --state-running              # Solo in esecuzione
virsh list --state-shutoff              # Solo ferme
virsh dominfo vm_name                   # Info VM
virsh domblklist vm_name                # Dischi
virsh domiflist vm_name                 # Interfacce di rete
virsh vcpucount vm_name                 # CPU assegnate
virsh vcpuinfo vm_name                  # Mapping vCPU → pCPU
virsh dommemstat vm_name                # Statistiche memoria
virsh domstats vm_name                  # Statistiche complete
virsh domstate vm_name --reason         # Stato con motivazione
virsh domtime vm_name                   # Orario del guest (richiede agent)
```

### Ciclo di Vita

```bash
# CICLO DI VITA
virsh start vm_name                     # Avvia
virsh shutdown vm_name                  # Shutdown gentile (ACPI)
virsh destroy vm_name                   # Forza spegnimento (come staccare corrente)
virsh reboot vm_name                    # Riavvia
virsh reset vm_name                     # Reset hardware (come premere reset)
virsh suspend vm_name                   # Sospendi (pausa in RAM)
virsh resume vm_name                    # Riprendi da pausa
virsh save vm_name /path/save_file      # Salva stato su disco (hibernate)
virsh restore /path/save_file           # Ripristina da stato salvato
virsh managedsave vm_name               # Save automatico nel path di default
virsh autostart vm_name                 # Avvio automatico con l'host
virsh autostart --disable vm_name
virsh create vm_name.xml                # Avvia da XML (transiente, non definita)

# CONSOLE
virsh console vm_name                   # Console seriale
# Escape: Ctrl+]
# Il guest deve avere la console seriale configurata (console=ttyS0 nel kernel)

# ELIMINARE
virsh undefine vm_name                  # Rimuovi definizione
virsh undefine vm_name --remove-all-storage  # + elimina dischi
virsh undefine vm_name --nvram          # + elimina NVRAM (UEFI)
virsh undefine vm_name --managed-save   # + elimina stato salvato
virsh undefine vm_name --snapshots-metadata  # + elimina metadata snapshot
```

### Modifica Configurazione

```bash
# MODIFICA CONFIGURAZIONE
virsh edit vm_name                      # Modifica XML (apre editor)
virsh dumpxml vm_name                   # Dump XML completo
virsh dumpxml vm_name > vm_backup.xml   # Backup configurazione
virsh define vm_backup.xml              # Ripristina da XML

# RISORSE A CALDO (hotplug)
virsh setvcpus vm_name 4 --live         # Cambia CPU (se hotplug abilitato)
virsh setvcpus vm_name 4 --config       # Cambia per prossimo avvio
virsh setvcpus vm_name 4 --live --config  # Entrambi
virsh setmem vm_name 4G --live          # Cambia memoria (balloon)
virsh setmaxmem vm_name 8G --config     # Massima memoria (riavvio necessario)

# METADATA
virsh desc vm_name "Descrizione della VM"
virsh metadata vm_name --uri http://example.com/ns --key custom \
  --set "<custom><tag>value</tag></custom>"
```

### Monitoraggio

```bash
# Monitoraggio risorse
virsh domstats --cpu-total --balloon --block --interface  # Tutte le VM
virsh domstats vm_name --cpu-total      # CPU di una VM
virsh dommemstat vm_name                # Memoria dettagliata
virsh domblkstat vm_name vda            # I/O disco
virsh domifstat vm_name vnet0           # I/O rete

# CPU reale utilizzata
virsh cpu-stats vm_name --total

# Evento di dominio (monitoraggio in tempo reale)
virsh event --domain vm_name --event lifecycle  # Eventi ciclo di vita
virsh event --all                       # Tutti gli eventi
```

---

## virt-manager (GUI)

```bash
# Avviare virt-manager
virt-manager                            # GUI locale

# Connessione remota via SSH
virt-manager -c qemu+ssh://user@server/system

# virt-viewer (solo console grafica della VM)
virt-viewer vm_name
virt-viewer --connect qemu+ssh://user@server/system vm_name

# remote-viewer (SPICE client, supporta USB redirect)
remote-viewer spice://host:5900
```

### Funzionalità virt-manager

- Creazione VM con wizard grafico
- Console grafica (VNC/SPICE) e seriale
- Gestione snapshot
- Monitoraggio risorse in tempo reale (CPU, memoria, disco, rete)
- Aggiunta/rimozione hardware a caldo
- Gestione reti e storage pool
- Connessione a host remoti via SSH

---

## Creazione VM Avanzata

### virt-install (CLI)

```bash
# VM da ISO (UEFI, virtio, bridge)
sudo virt-install \
  --name ubuntu-server \
  --ram 4096 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/ubuntu.qcow2,size=40,format=qcow2,bus=virtio \
  --os-variant ubuntu22.04 \
  --network bridge=br0,model=virtio \
  --graphics vnc,listen=0.0.0.0 \
  --cdrom /var/lib/libvirt/images/ubuntu-22.04-server.iso \
  --boot uefi

# VM RHEL/Fedora con kickstart
sudo virt-install \
  --name rhel-server \
  --ram 4096 \
  --vcpus 4 \
  --disk path=/var/lib/libvirt/images/rhel.qcow2,size=60,format=qcow2 \
  --os-variant rhel9.0 \
  --network bridge=br0 \
  --location /var/lib/libvirt/images/rhel-9.0-dvd.iso \
  --initrd-inject /path/to/ks.cfg \
  --extra-args "inst.ks=file:/ks.cfg console=ttyS0" \
  --boot uefi \
  --nographics

# VM con cloud-init (senza ISO, boot diretto)
sudo virt-install \
  --name web-server \
  --ram 2048 \
  --vcpus 2 \
  --import \
  --disk path=/var/lib/libvirt/images/web.qcow2 \
  --os-variant ubuntu22.04 \
  --network bridge=br0 \
  --cloud-init root-password-generate=on \
  --noautoconsole

# VM Windows con driver virtio
sudo virt-install \
  --name win11 \
  --ram 8192 \
  --vcpus 4 \
  --disk path=/var/lib/libvirt/images/win11.qcow2,size=80,bus=virtio \
  --disk path=/path/to/virtio-win.iso,device=cdrom \
  --cdrom /path/to/Win11.iso \
  --os-variant win11 \
  --network bridge=br0,model=virtio \
  --graphics spice \
  --video qxl \
  --boot uefi \
  --tpm backend.type=emulator,backend.version=2.0,model=tpm-crb \
  --features kvm.hidden.state=on

# VM con macchina q35 e PCIe
sudo virt-install \
  --name test-q35 \
  --ram 4096 \
  --vcpus 2 \
  --machine q35 \
  --disk path=/var/lib/libvirt/images/test.qcow2,size=30 \
  --os-variant generic \
  --network network=default \
  --boot uefi

# Clonare VM
virt-clone --original ubuntu-server --name ubuntu-clone --auto-clone

# Lista varianti OS supportate
osinfo-query os | grep ubuntu
osinfo-query os | grep -i windows
virt-install --osinfo list              # Alternativa moderna
```

---

## Formati Disco QEMU: qcow2, raw, vmdk

### Confronto Formati

| Formato | Thin Prov. | Snapshot | Compressione | Crittografia | Performance | Uso |
|---|---|---|---|---|---|---|
| **qcow2** | Sì | Sì (interne) | Sì (zlib/zstd) | Sì (LUKS) | Buona | Standard Linux |
| **raw** | No | No | No | No | Massima | I/O intensivo, database |
| **vmdk** | Sì | No (in KVM) | No | No | Media | Migrazione da VMware |
| **vdi** | Sì | No | No | No | Media | Migrazione da VirtualBox |
| **vhdx** | Sì | No | No | No | Media | Migrazione da Hyper-V |
| **qed** | Sì | No | No | No | Buona | Deprecato |

### qcow2 — Il Formato Standard

```bash
# Creare disco qcow2
qemu-img create -f qcow2 disk.qcow2 50G

# Creare con preallocation (migliore performance, disco non sparse)
qemu-img create -f qcow2 -o preallocation=metadata disk.qcow2 50G
qemu-img create -f qcow2 -o preallocation=full disk.qcow2 50G

# Creare con compressione cluster
qemu-img create -f qcow2 -o cluster_size=65536 disk.qcow2 50G

# Creare con crittografia LUKS
qemu-img create -f qcow2 --object secret,id=sec0,data=mypassword \
  -o encrypt.format=luks,encrypt.key-secret=sec0 disk_encrypted.qcow2 50G

# Info disco
qemu-img info disk.qcow2
qemu-img info --output=json disk.qcow2  # Formato JSON

# Verifica integrità
qemu-img check disk.qcow2
qemu-img check -r all disk.qcow2        # Ripara errori

# Ridimensionare
qemu-img resize disk.qcow2 +20G         # Aumentare
qemu-img resize --shrink disk.qcow2 30G  # Ridurre (ATTENZIONE: dati persi!)
```

### Backing Files (Template con overlay)

I backing file permettono di creare immagini che condividono una base comune (copy-on-write):

```bash
# Creare immagine base (template)
qemu-img create -f qcow2 base-ubuntu.qcow2 20G
# ... installare OS, configurare, spegnere ...

# Creare overlay che usa la base come backing file
qemu-img create -f qcow2 -b base-ubuntu.qcow2 -F qcow2 vm1.qcow2
qemu-img create -f qcow2 -b base-ubuntu.qcow2 -F qcow2 vm2.qcow2
qemu-img create -f qcow2 -b base-ubuntu.qcow2 -F qcow2 vm3.qcow2

# Ogni overlay occupa solo lo spazio delle differenze dalla base!
# IMPORTANTE: la base NON deve essere modificata dopo aver creato gli overlay

# Verificare backing chain
qemu-img info --backing-chain vm1.qcow2

# Appiattire overlay (rendere indipendente dalla base)
qemu-img convert -O qcow2 vm1.qcow2 vm1_standalone.qcow2

# Rebasing (cambiare il backing file)
qemu-img rebase -b new_base.qcow2 -F qcow2 vm1.qcow2
```

### Conversione tra Formati

```bash
# Da VMware a KVM
qemu-img convert -f vmdk -O qcow2 disk.vmdk disk.qcow2

# Da VirtualBox a KVM
qemu-img convert -f vdi -O qcow2 disk.vdi disk.qcow2

# Da Hyper-V a KVM
qemu-img convert -f vhdx -O qcow2 disk.vhdx disk.qcow2

# Da qcow2 a raw (massima performance)
qemu-img convert -f qcow2 -O raw disk.qcow2 disk.raw

# Conversione con compressione
qemu-img convert -c -f qcow2 -O qcow2 disk.qcow2 disk_compressed.qcow2

# Conversione con progress bar
qemu-img convert -p -f vmdk -O qcow2 large_disk.vmdk large_disk.qcow2
```

### Snapshot a Livello di Immagine

```bash
# Creare snapshot nell'immagine qcow2
qemu-img snapshot -c snap1 disk.qcow2

# Listare snapshot
qemu-img snapshot -l disk.qcow2

# Applicare snapshot (revert)
qemu-img snapshot -a snap1 disk.qcow2

# Eliminare snapshot
qemu-img snapshot -d snap1 disk.qcow2
```

---

## Networking VM

### Modalità di Rete — Panoramica

```text
Modalità Rete KVM/libvirt
├── NAT (default)
│   └── VM → virbr0 (bridge virtuale) → iptables MASQUERADE → Internet
│       Guest accessibile solo dall'host (senza port forwarding)
├── Bridge
│   └── VM → br0 (bridge fisico) → switch/rete fisica
│       Guest ha IP sulla LAN, visibile da tutti
├── Isolata
│   └── VM → virbr1 (bridge senza NAT/routing)
│       Solo comunicazione tra VM sulla stessa rete
├── macvtap
│   └── VM → macvtap device → NIC fisica direttamente
│       No bridge necessario, ma host non può comunicare con guest
├── Passthrough (SR-IOV)
│   └── VM → VF (Virtual Function) della NIC → rete diretta
│       Massima performance, quasi bare-metal
└── Open vSwitch
    └── VM → OVS bridge → VLAN, tunneling, SDN
        Enterprise/datacenter, SDN controller integrazione
```

### NAT (Default)

```bash
# NAT (default): VM accede a internet tramite NAT dell'host
# Le VM non sono raggiungibili dall'esterno senza port forwarding
virsh net-list --all                    # Liste reti
virsh net-info default                  # Info rete default (NAT)
virsh net-dhcp-leases default           # Lease DHCP attivi

# Avviare rete default se fermata
virsh net-start default
virsh net-autostart default

# Port forwarding (iptables manuale)
# Esempio: host:2222 → guest:22
sudo iptables -t nat -A PREROUTING -p tcp --dport 2222 \
  -j DNAT --to-destination 192.168.122.100:22
sudo iptables -A FORWARD -p tcp -d 192.168.122.100 --dport 22 \
  -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT
```

### Bridge — Configurazione Completa

```bash
# BRIDGE: VM collegata direttamente alla rete fisica
# La VM ottiene un IP dalla rete LAN

# ── Con netplan (Ubuntu Server) ─────────────────────
cat > /etc/netplan/01-bridge.yaml << 'YAML'
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: no
  bridges:
    br0:
      interfaces: [eth0]
      dhcp4: yes
      parameters:
        stp: false
        forward-delay: 0
YAML
sudo netplan apply

# ── Con NetworkManager ──────────────────────────────
sudo nmcli connection add type bridge con-name br0 ifname br0
sudo nmcli connection add type ethernet con-name br0-slave ifname eth0 master br0
sudo nmcli connection modify br0 ipv4.method auto
sudo nmcli connection up br0
sudo nmcli connection down "Wired connection 1"  # Disattiva vecchia connessione

# ── Con systemd-networkd ────────────────────────────
# /etc/systemd/network/br0.netdev
cat > /etc/systemd/network/br0.netdev << 'EOF'
[NetDev]
Name=br0
Kind=bridge
EOF

# /etc/systemd/network/br0.network
cat > /etc/systemd/network/br0.network << 'EOF'
[Match]
Name=br0
[Network]
DHCP=yes
EOF

# /etc/systemd/network/eth0.network
cat > /etc/systemd/network/eth0.network << 'EOF'
[Match]
Name=eth0
[Network]
Bridge=br0
EOF

sudo systemctl restart systemd-networkd

# Verificare
ip link show br0
bridge link show
```

### Rete Isolata

```bash
# RETE ISOLATA: solo comunicazione tra VM (no accesso esterno)
virsh net-define isolated.xml
virsh net-start isolated
virsh net-autostart isolated
```

```xml
<!-- /tmp/isolated.xml -->
<network>
  <name>isolated</name>
  <bridge name="virbr1"/>
  <ip address="10.10.10.1" netmask="255.255.255.0">
    <dhcp>
      <range start="10.10.10.100" end="10.10.10.200"/>
    </dhcp>
  </ip>
</network>
```

### macvtap

```bash
# macvtap: collega la VM direttamente alla NIC senza bridge
# Nota: l'host NON può comunicare con il guest via macvtap!

# In virt-install:
sudo virt-install \
  --name test-macvtap \
  --ram 2048 \
  --vcpus 2 \
  --disk path=/var/lib/libvirt/images/test.qcow2,size=20 \
  --os-variant generic \
  --network type=direct,source=eth0,source.mode=bridge,model=virtio
```

```xml
<!-- In domain XML -->
<interface type='direct'>
  <source dev='eth0' mode='bridge'/>
  <model type='virtio'/>
</interface>
<!-- Modi macvtap: bridge, vepa, private, passthrough -->
```

### Rete Personalizzata con Routing

```xml
<!-- Rete con routing (no NAT, richiede route statica sul router) -->
<network>
  <name>routed-net</name>
  <forward mode='route'/>
  <bridge name='virbr2'/>
  <ip address='10.20.30.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='10.20.30.100' end='10.20.30.200'/>
    </dhcp>
  </ip>
</network>
```

---

## Open vSwitch — Fondamenti

Open vSwitch (OVS) è un switch virtuale enterprise-grade con supporto per VLAN, tunneling, e SDN.

```bash
# Installazione
sudo apt install openvswitch-switch      # Debian/Ubuntu
sudo dnf install openvswitch             # RHEL/Fedora

# Creare bridge OVS
sudo ovs-vsctl add-br ovsbr0

# Aggiungere porta fisica
sudo ovs-vsctl add-port ovsbr0 eth0

# Verificare
sudo ovs-vsctl show

# VLAN: assegnare porta a VLAN
sudo ovs-vsctl set port vnet0 tag=100   # VM nella VLAN 100
sudo ovs-vsctl set port vnet1 tag=200   # VM nella VLAN 200

# Trunk port (multiple VLAN)
sudo ovs-vsctl set port eth0 trunks=100,200,300

# Tunneling VXLAN tra host
sudo ovs-vsctl add-port ovsbr0 vxlan0 \
  -- set interface vxlan0 type=vxlan options:remote_ip=10.0.0.2 options:key=1000

# Flow rules
sudo ovs-ofctl dump-flows ovsbr0        # Mostra regole
sudo ovs-ofctl add-flow ovsbr0 "in_port=1,actions=output:2"

# Statistiche
sudo ovs-ofctl dump-ports ovsbr0
```

### Integrazione OVS con libvirt

```xml
<!-- Definire rete OVS in libvirt -->
<network>
  <name>ovs-network</name>
  <forward mode='bridge'/>
  <bridge name='ovsbr0'/>
  <virtualport type='openvswitch'/>
</network>
```

```xml
<!-- Interface VM su OVS con VLAN -->
<interface type='bridge'>
  <source bridge='ovsbr0'/>
  <virtualport type='openvswitch'>
    <parameters profileid='vm-profile'/>
  </virtualport>
  <vlan>
    <tag id='100'/>
  </vlan>
  <model type='virtio'/>
</interface>
```

---

## Storage VM

### Storage Pool — Tipi Supportati

| Tipo | Backend | Caso d'uso |
|---|---|---|
| **dir** | Directory locale | Default, semplice |
| **logical** | LVM | Performance, thin provisioning |
| **netfs** | NFS/GlusterFS | Storage condiviso per migrazione |
| **iscsi** | iSCSI target | SAN enterprise |
| **rbd** | Ceph RBD | Storage distribuito, HA |
| **zfs** | ZFS pool | Snapshot CoW, deduplication |
| **disk** | Disco intero | Accesso raw, massima performance |

### Gestione Storage Pool

```bash
# Lista pool
virsh pool-list --all
virsh pool-list --details               # Con capacità e allocazione

# ── Pool Directory ──────────────────────────────────
virsh pool-define-as mypool dir --target /var/lib/libvirt/images/mypool
virsh pool-build mypool
virsh pool-start mypool
virsh pool-autostart mypool

# ── Pool LVM ────────────────────────────────────────
# Prerequisito: VG già creato (pvcreate, vgcreate)
virsh pool-define-as lvmpool logical \
  --source-name vg_vms --target /dev/vg_vms
virsh pool-start lvmpool
virsh pool-autostart lvmpool

# ── Pool NFS ────────────────────────────────────────
virsh pool-define-as nfspool netfs \
  --source-host 10.0.0.5 --source-path /export/vms \
  --target /mnt/nfs-vms
virsh pool-build nfspool
virsh pool-start nfspool
virsh pool-autostart nfspool

# ── Pool Ceph RBD ───────────────────────────────────
virsh pool-define-as cephpool rbd \
  --source-host mon1.example.com,mon2.example.com \
  --source-name libvirt-pool \
  --auth-type ceph --auth-username libvirt \
  --secret-uuid a1b2c3d4-xxxx-yyyy-zzzz-000000000000
virsh pool-start cephpool
virsh pool-autostart cephpool

# ── Pool iSCSI ──────────────────────────────────────
virsh pool-define-as iscsipool iscsi \
  --source-host 10.0.0.10 \
  --source-dev iqn.2024-01.com.example:storage.target1 \
  --target /dev/disk/by-path
virsh pool-start iscsipool

# Creare volume nel pool
virsh vol-create-as mypool vm-disk.qcow2 50G --format qcow2
virsh vol-create-as lvmpool vm-lv 50G    # LV nel VG

# Info
virsh pool-info mypool
virsh vol-list mypool
virsh vol-info vm-disk.qcow2 --pool mypool

# Eliminare
virsh vol-delete vm-disk.qcow2 --pool mypool
virsh pool-destroy mypool               # Ferma pool
virsh pool-undefine mypool              # Elimina definizione
```

### Aggiungere Disco a VM

```bash
# Creare e attaccare disco (a caldo)
virsh vol-create-as default data-disk.qcow2 20G --format qcow2
virsh attach-disk vm_name /var/lib/libvirt/images/data-disk.qcow2 vdb \
  --driver qemu --subdriver qcow2 --persistent

# Attaccare disco con bus virtio-scsi
virsh attach-disk vm_name /var/lib/libvirt/images/data-disk.qcow2 sdb \
  --driver qemu --subdriver qcow2 --targetbus scsi --persistent

# Staccare disco
virsh detach-disk vm_name vdb --persistent

# Aggiungere CDROM
virsh change-media vm_name sda --insert /path/to/image.iso
virsh change-media vm_name sda --eject
```

---

## Performance Tuning KVM

### CPU Tuning

#### CPU Pinning

Assegnare vCPU a core fisici specifici per eliminare la migrazione tra core e migliorare le prestazioni della cache.

```bash
# Vedere la topologia CPU dell'host
lscpu
lstopo                                   # Richiede hwloc
numactl --hardware                       # Topologia NUMA

# Pinning via virsh (runtime)
virsh vcpupin vm_name 0 2                # vCPU 0 → pCPU 2
virsh vcpupin vm_name 1 3                # vCPU 1 → pCPU 3
virsh emulatorpin vm_name 0-1            # Thread emulatore su pCPU 0-1

# Verificare pinning
virsh vcpupin vm_name
```

```xml
<!-- Nel domain XML (persistente) -->
<cputune>
  <vcpupin vcpu='0' cpuset='2'/>
  <vcpupin vcpu='1' cpuset='3'/>
  <vcpupin vcpu='2' cpuset='6'/>
  <vcpupin vcpu='3' cpuset='7'/>
  <emulatorpin cpuset='0-1'/>
  <!-- IOThread pinning (per I/O dedicato) -->
  <iothreadpin iothread='1' cpuset='4'/>
  <iothreadpin iothread='2' cpuset='5'/>
</cputune>
<iothreads>2</iothreads>
```

#### CPU Model e Feature

```xml
<!-- host-passthrough: espone il modello CPU esatto dell'host al guest -->
<!-- Massima performance, ma impedisce migrazione tra CPU diverse -->
<cpu mode='host-passthrough' check='none' migratable='off'/>

<!-- host-model: libvirt sceglie il modello più vicino -->
<!-- Buona performance, permette migrazione tra host simili -->
<cpu mode='host-model' check='partial'/>

<!-- Custom: specifica modello e feature esatti -->
<cpu mode='custom' match='exact'>
  <model fallback='forbid'>Skylake-Server-v2</model>
  <feature policy='require' name='avx2'/>
  <feature policy='require' name='aes'/>
</cpu>
```

### Memoria — Hugepages

Le hugepages (2MB o 1GB) riducono la TLB pressure e migliorano le prestazioni per VM con molta RAM.

```bash
# ── Hugepages 2MB ───────────────────────────────────

# Verificare hugepages correnti
cat /proc/meminfo | grep Huge
# HugePages_Total:       0
# HugePages_Free:        0
# Hugepagesize:       2048 kB

# Allocare 4096 hugepages da 2MB = 8GB
echo 4096 | sudo tee /proc/sys/vm/nr_hugepages

# Persistente al boot
echo 'vm.nr_hugepages = 4096' | sudo tee /etc/sysctl.d/hugepages.conf
sudo sysctl --system

# Montare hugetlbfs (se non già montato)
sudo mount -t hugetlbfs hugetlbfs /dev/hugepages
# Oppure in /etc/fstab:
# hugetlbfs /dev/hugepages hugetlbfs defaults 0 0

# ── Hugepages 1GB (massima performance) ────────────
# Richiede boot parameter: hugepagesz=1G hugepages=8
# In GRUB: /etc/default/grub
# GRUB_CMDLINE_LINUX="... hugepagesz=1G hugepages=8"
# sudo update-grub && reboot

# ── Hugepages per nodo NUMA ────────────────────────
echo 2048 | sudo tee /sys/devices/system/node/node0/hugepages/hugepages-2048kB/nr_hugepages
echo 2048 | sudo tee /sys/devices/system/node/node1/hugepages/hugepages-2048kB/nr_hugepages
```

```xml
<!-- Nel domain XML -->
<memoryBacking>
  <hugepages>
    <page size='2048' unit='KiB'/>
  </hugepages>
  <locked/>          <!-- Impedisce swap della memoria della VM -->
  <nosharepages/>    <!-- Disabilita KSM per questa VM (isolamento) -->
</memoryBacking>
```

### NUMA Topology

Per host multi-socket, allineare la topologia NUMA della VM a quella dell'host.

```xml
<!-- VM con topologia NUMA esplicita -->
<cpu mode='host-passthrough'>
  <topology sockets='1' dies='1' cores='4' threads='2'/>
  <numa>
    <cell id='0' cpus='0-3' memory='4' unit='GiB'/>
    <cell id='1' cpus='4-7' memory='4' unit='GiB'/>
  </numa>
</cpu>

<!-- Associare memoria NUMA all'host -->
<numatune>
  <memory mode='strict' nodeset='0'/>     <!-- Forza allocazione su nodo NUMA 0 -->
</numatune>
```

### Disco — VirtIO e I/O Tuning

```xml
<!-- Disco con virtio-scsi (multi-queue, TRIM/UNMAP supportato) -->
<disk type='file' device='disk'>
  <driver name='qemu' type='qcow2'
          cache='none'           
          io='native'            
          discard='unmap'        
          iothread='1'/>
  <source file='/var/lib/libvirt/images/vm.qcow2'/>
  <target dev='sda' bus='scsi'/>
</disk>

<!-- Controller virtio-scsi multi-queue -->
<controller type='scsi' model='virtio-scsi'>
  <driver queues='4' iothread='1'/>
</controller>
```

**Opzioni cache disco:**

| Cache | Descrizione | Quando |
|---|---|---|
| `none` | I/O diretto, no cache host | **Consigliato**: migliore per produzione |
| `writethrough` | Letture cached, scritture dirette | Sicuro ma più lento |
| `writeback` | Letture e scritture cached | Performance ma rischio dati in crash |
| `directsync` | I/O diretto + sincrono | Massima sicurezza, minima performance |
| `unsafe` | Nessun flush | Solo per test, mai in produzione |

**Opzioni io:**

| IO | Descrizione |
|---|---|
| `native` | AIO del kernel Linux. Richiede `cache='none'` |
| `threads` | Thread pool user-space. Funziona con qualsiasi cache |
| `io_uring` | API I/O moderna del kernel. Migliore performance (kernel 5.1+) |

### Rete — VirtIO e vhost

```xml
<!-- Rete con vhost-net e multiqueue -->
<interface type='bridge'>
  <source bridge='br0'/>
  <model type='virtio'/>
  <driver name='vhost' queues='4' txmode='iothread'/>
</interface>
```

### SR-IOV — Accesso Diretto alla NIC

SR-IOV permette alla VM di accedere direttamente a una Virtual Function (VF) della NIC, bypassando il kernel host.

```bash
# Verificare supporto SR-IOV
lspci -v | grep -i sr-iov

# Abilitare VF (esempio: Intel X710)
echo 4 | sudo tee /sys/class/net/ens3f0/device/sriov_numvfs

# Verificare VF create
lspci | grep "Virtual Function"
ip link show ens3f0                      # VF visibili

# Assegnare VF alla VM (nodedev)
virsh nodedev-list --cap net
virsh nodedev-dumpxml pci_0000_03_02_0   # Info VF
```

```xml
<!-- Assegnare VF nel domain XML -->
<interface type='hostdev' managed='yes'>
  <source>
    <address type='pci' domain='0x0000' bus='0x03' slot='0x02' function='0x0'/>
  </source>
</interface>
```

### VirtIO — Architettura e Tuning Avanzato

VirtIO è lo standard de facto per I/O paravirtualizzato in KVM. A differenza dell'emulazione hardware (es. e1000, IDE), VirtIO usa un'interfaccia cooperativa guest-host che elimina il trap overhead dell'emulazione.

```text
Emulazione completa (e1000)          VirtIO
┌──────────────┐                    ┌──────────────┐
│  Guest OS    │                    │  Guest OS    │
│  ┌────────┐  │                    │  ┌────────┐  │
│  │ Driver │  │                    │  │ VirtIO │  │
│  │ e1000  │  │                    │  │ driver │  │
│  └───┬────┘  │                    │  └───┬────┘  │
│──────┼───────│                    │──────┼───────│
│  QEMU emula  │                    │  Virtqueue   │
│  registro    │ ← VM exit/entry   │  (ring buf)  │ ← notifica diretta
│  per registro│   (lento)          │  condiviso   │   (veloce)
└──────────────┘                    └──────────────┘
```

#### VirtIO Device Types

| Device | Funzione | Parametro QEMU |
|--------|---------|---------------|
| **virtio-net** | Rete | `-netdev ... -device virtio-net-pci` |
| **virtio-blk** | Block storage | `-drive ... -device virtio-blk-pci` |
| **virtio-scsi** | SCSI controller | `-device virtio-scsi-pci` |
| **virtio-gpu** | GPU 2D/3D | `-device virtio-gpu-pci` |
| **virtio-fs** | File sharing (sostituto 9p) | `-device vhost-user-fs-pci` |
| **virtio-mem** | Memory hotplug granulare | `-device virtio-mem-pci` |
| **virtio-balloon** | Memory ballooning | `-device virtio-balloon-pci` |

#### Multiqueue VirtIO (QEMU 9.x)

Per NIC ad alta velocità (10 Gbps+), virtio-net multiqueue distribuisce il carico su più code, ciascuna gestita da un vCPU diverso:

```xml
<!-- Domain XML: virtio-net con 4 code -->
<interface type='bridge'>
  <source bridge='br0'/>
  <model type='virtio'/>
  <driver name='vhost' queues='4'/>  <!-- Multiqueue -->
</interface>

<!-- virtio-blk multiqueue (QEMU 9.0+) -->
<disk type='file' device='disk'>
  <driver name='qemu' type='qcow2' queues='4'/>
  <source file='/var/lib/libvirt/images/vm.qcow2'/>
  <target dev='vda' bus='virtio'/>
</disk>
```

```bash
# Nel guest: abilitare multiqueue (dopo boot)
ethtool -L eth0 combined 4

# Verificare code attive
ethtool -l eth0
```

#### vDPA — Data Path Acceleration

**vDPA** (virtio Data Path Acceleration) è un framework che combina la portabilità di VirtIO con le prestazioni di SR-IOV. Il data path passa direttamente dall'hardware al guest (come SR-IOV), ma l'interfaccia rimane VirtIO standard, permettendo migrazione live.

```text
Confronto throughput rete (benchmark 2024-2025):

Metodo              │ Throughput    │ Latenza    │ Migrazione Live
────────────────────┼───────────────┼────────────┼────────────────
VirtIO (base)       │ 3-5 Gbps     │ ~50 µs     │ Sì
VirtIO (tuned)      │ 9+ Gbps      │ ~25 µs     │ Sì
SR-IOV (VFIO)       │ 9.4 Gbps     │ ~10 µs     │ No (device state)
vDPA                │ 9+ Gbps      │ ~15 µs     │ Sì (switchover)
```

**Nota**: VirtIO mal configurato (senza vhost, senza multiqueue, con backend userspace) può scendere a 3-4 Gbps. Con vhost-net kernel, multiqueue e interrupt coalescing, raggiunge throughput paragonabile a SR-IOV.

#### SR-IOV — Configurazione Avanzata

```bash
# Workflow completo SR-IOV

# 1. Verificare supporto hardware
lspci -v -s $(lspci | grep -i ethernet | awk '{print $1}') | grep -i "sr-iov"

# 2. Abilitare IOMMU (già nel boot: intel_iommu=on o amd_iommu=on)
dmesg | grep -i iommu

# 3. Creare Virtual Functions
echo 8 | sudo tee /sys/class/net/enp4s0/device/sriov_numvfs

# 4. Verificare VF create
ip link show enp4s0
# enp4s0: ... vf 0 MAC 00:00:00:00:00:00, vf 1 MAC ...

# 5. Impostare MAC e VLAN per VF
ip link set enp4s0 vf 0 mac 52:54:00:aa:bb:01 vlan 100
ip link set enp4s0 vf 1 mac 52:54:00:aa:bb:02 vlan 200

# 6. Bind VF a vfio-pci
echo "0000:03:02.0" | sudo tee /sys/bus/pci/devices/0000:03:02.0/driver/unbind
echo "vfio-pci" | sudo tee /sys/bus/pci/devices/0000:03:02.0/driver_override
echo "0000:03:02.0" | sudo tee /sys/bus/pci/drivers/vfio-pci/bind

# 7. Persistenza VF al boot (/etc/udev/rules.d/68-sriov.rules)
# ACTION=="add", SUBSYSTEM=="net", KERNELS=="0000:04:00.0", \
#   ATTR{device/sriov_numvfs}="8"
```

### Kernel Samepage Merging (KSM)

KSM deduplicata le pagine di memoria identiche tra VM. Utile per molte VM con lo stesso OS.

```bash
# Stato KSM
cat /sys/kernel/mm/ksm/run              # 1 = attivo
cat /sys/kernel/mm/ksm/pages_shared     # Pagine condivise
cat /sys/kernel/mm/ksm/pages_sharing    # Pagine risparmiate

# Attivare KSM
echo 1 | sudo tee /sys/kernel/mm/ksm/run

# Configurare frequenza di scansione
echo 200 | sudo tee /sys/kernel/mm/ksm/sleep_millisecs  # Intervallo scan
echo 1000 | sudo tee /sys/kernel/mm/ksm/pages_to_scan   # Pagine per scan
```

> **Nota sicurezza**: KSM può esporre a side-channel timing attack (es. FLUSH+RELOAD). Disabilitare su host multi-tenant non fidati.

### Tuning Avanzato — Huge Pages, NUMA e CPU Pinning in Profondità

#### Huge Pages: 2 MB vs 1 GB

Le huge pages riducono drasticamente i TLB miss eliminando milioni di entry nella page table. Per VM con molta memoria (>16 GB), le **1 GB huge pages** sono superiori alle 2 MB:

```bash
# Huge Pages 2 MB — allocazione dinamica (può frammentarsi)
echo 4096 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# Huge Pages 1 GB — DEVONO essere riservate al boot (no frammentazione)
# /etc/default/grub:
# GRUB_CMDLINE_LINUX="hugepagesz=1G hugepages=32 default_hugepagesz=1G"
# Riserva 32 GB in pagine da 1 GB

# Verificare allocazione
grep -i huge /proc/meminfo
# HugePages_Total:     32
# HugePages_Free:      28
# HugePages_Rsvd:       4
# Hugepagesize:    1048576 kB

# Montare hugetlbfs
mount -t hugetlbfs -o pagesize=1G none /dev/hugepages1G

# Domain XML per 1 GB huge pages
# <memoryBacking>
#   <hugepages>
#     <page size='1' unit='GiB'/>
#   </hugepages>
#   <locked/>
# </memoryBacking>
```

**Impatto prestazionale**: con 1 GB huge pages, una VM da 64 GB usa 64 entry TLB invece di 32.768 (2 MB pages) o 16.777.216 (4 KB pages). Il guadagno è misurabile su workload memory-intensive: database, caching (Redis/Memcached), analisi dati.

#### NUMA-Aware VM Placement

L'allineamento NUMA è **critico** per le prestazioni. Accedere a memoria di un nodo NUMA remoto costa 50-100% in più di latenza rispetto alla memoria locale.

```bash
# Topologia NUMA dell'host
numactl --hardware
# node 0 cpus: 0 1 2 3 4 5 6 7 16 17 18 19 20 21 22 23
# node 0 size: 65335 MB
# node 1 cpus: 8 9 10 11 12 13 14 15 24 25 26 27 28 29 30 31
# node 1 size: 65335 MB
# node distances:
# node   0   1
#   0:  10  21
#   1:  21  10

# Verificare distribuzione NUMA per VM in esecuzione
virsh numatune vm_name
numastat -c qemu
```

```xml
<!-- Domain XML: VM pinned al nodo NUMA 0 -->
<vcpu placement='static'>8</vcpu>
<cputune>
  <vcpupin vcpu='0' cpuset='0'/>
  <vcpupin vcpu='1' cpuset='1'/>
  <vcpupin vcpu='2' cpuset='2'/>
  <vcpupin vcpu='3' cpuset='3'/>
  <vcpupin vcpu='4' cpuset='4'/>
  <vcpupin vcpu='5' cpuset='5'/>
  <vcpupin vcpu='6' cpuset='6'/>
  <vcpupin vcpu='7' cpuset='7'/>
  <emulatorpin cpuset='16,17'/>  <!-- Thread emulatore su HT dello stesso nodo -->
</cputune>
<numatune>
  <memory mode='strict' nodeset='0'/>  <!-- Memoria SOLO dal nodo 0 -->
</numatune>
<memoryBacking>
  <hugepages>
    <page size='1' unit='GiB' nodeset='0'/>  <!-- Huge pages dal nodo NUMA 0 -->
  </hugepages>
  <locked/>
</memoryBacking>
```

**Regola aurea**: mai assegnare vCPU di nodi NUMA diversi alla stessa VM. Se la VM necessita più risorse di un nodo, creare una topologia NUMA guest che rispecchi l'host:

```xml
<!-- VM con 2 nodi NUMA guest (16 vCPU, 128 GB) -->
<cpu mode='host-passthrough'>
  <topology sockets='2' dies='1' cores='4' threads='2'/>
  <numa>
    <cell id='0' cpus='0-7' memory='64' unit='GiB'/>
    <cell id='1' cpus='8-15' memory='64' unit='GiB'/>
  </numa>
</cpu>
```

#### I/O Tuning Avanzato

```bash
# io_uring per I/O asincrono (QEMU 6.0+, raccomandato con kernel 5.15+)
# Domain XML:
# <driver name='qemu' type='qcow2' io='io_uring'/>

# Confronto backend I/O:
# threads  → pool di thread, compatibilità massima, overhead context switch
# native   → Linux AIO (libaio), buone prestazioni, richiede O_DIRECT
# io_uring → asincrono moderno, migliori prestazioni, meno syscall

# Disk cache modes e impatto:
# none       → O_DIRECT, no cache host (consigliato per produzione con battery-backed RAID)
# writeback  → cache host, flush espliciti (buono con journaling FS)
# writethrough → scritture sincrone (più sicuro, più lento)
# unsafe     → no flush, no sync (SOLO test, rischio perdita dati)
```

---

## Migrazione Live

La migrazione live sposta una VM in esecuzione da un host a un altro senza downtime.

### Prerequisiti

```text
Requisiti per migrazione live:
1. Stessa architettura CPU (o modello CPU compatibile)
2. Storage condiviso (NFS, Ceph, iSCSI, GlusterFS)
   — oppure migrazione con copia disco (--copy-storage-all)
3. Rete tra gli host (libvirt su entrambi)
4. libvirtd attivo su entrambi gli host
5. Accesso SSH senza password tra gli host
6. Stessa versione di libvirt (consigliato)
7. Il nome della VM non deve già esistere sul destination host
```

### Migrazione con Storage Condiviso

```bash
# Migrazione live base
virsh migrate --live vm_name qemu+ssh://dest_host/system

# Con opzioni avanzate
virsh migrate --live --persistent --undefinesource \
  vm_name qemu+ssh://dest_host/system

# Con banda dedicata
virsh migrate --live --persistent \
  --bandwidth 1000 \
  vm_name qemu+ssh://dest_host/system

# Tunnel tramite libvirt (no connessione QEMU diretta)
virsh migrate --live --p2p --tunnelled \
  vm_name qemu+ssh://dest_host/system

# Monitorare progresso
virsh domjobinfo vm_name
# Mostra: data transferred, remaining, memory bandwidth, etc.

# Cancellare migrazione in corso
virsh domjobabort vm_name
```

### Migrazione senza Storage Condiviso (Copy-Storage)

```bash
# Copia completa del disco durante la migrazione
virsh migrate --live --copy-storage-all vm_name qemu+ssh://dest_host/system

# Solo blocchi modificati (richiede immagine pre-copiata sulla destinazione)
virsh migrate --live --copy-storage-inc vm_name qemu+ssh://dest_host/system

# Con opzioni complete
virsh migrate --live --persistent --undefinesource \
  --copy-storage-all --bandwidth 500 \
  vm_name qemu+ssh://dest_host/system
```

### Migrazione Offline (Cold)

```bash
# Spegni, migra definizione, avvia
virsh shutdown vm_name
virsh dumpxml vm_name > vm_name.xml
scp vm_name.xml dest_host:/tmp/
scp /var/lib/libvirt/images/vm_name.qcow2 dest_host:/var/lib/libvirt/images/
# Sulla destinazione:
# virsh define /tmp/vm_name.xml
# virsh start vm_name
```

### Post-Copy Migration

La post-copy migration trasferisce le pagine di memoria on-demand dopo aver spostato la vCPU. Riduce il tempo di convergenza.

```bash
# Avviare migrazione con post-copy
virsh migrate --live --postcopy vm_name qemu+ssh://dest_host/system

# Switchare a post-copy durante una migrazione pre-copy
virsh migrate-postcopy vm_name
```

> **Rischio**: in post-copy, se la connessione tra i due host si interrompe, la VM diventa irrecuperabile (pagine distribuite tra source e destination).

### Considerazioni Performance Migrazione

```text
Fattori che influenzano la durata:
─ Dimensione memoria della VM (determinante principale)
─ Banda di rete tra gli host
─ Dirty rate: quante pagine la VM modifica al secondo
─ Convergenza: se il dirty rate supera la banda, la migrazione non converge

Soluzioni per VM con alto dirty rate:
─ Aumentare la banda di rete (10Gbps+, bonding)
─ RDMA (InfiniBand, RoCE) per trasferimento zero-copy
─ Auto-converge: rallenta la vCPU per ridurre il dirty rate
─ Post-copy: trasferisce le pagine on-demand
─ Compressione XBZRLE: comprime le pagine dirty
```

```bash
# Abilitare auto-converge (rallenta CPU per convergere)
virsh migrate --live --auto-converge vm_name qemu+ssh://dest_host/system

# Abilitare compressione XBZRLE
virsh migrate --live --compressed vm_name qemu+ssh://dest_host/system
```

### Migrazione Multifd — Trasferimento Parallelo

QEMU 9.x potenzia la migrazione **multifd** (multi-file-descriptor): la memoria viene trasferita su canali TCP paralleli, saturando link 10/25/100 Gbps. Senza multifd, un singolo thread TCP è il collo di bottiglia (~3-5 Gbps max).

```bash
# Migrazione con multifd (8 canali paralleli)
virsh migrate --live --parallel --parallel-connections 8 \
  vm_name qemu+ssh://dest_host/system

# Monitor QEMU: abilitare multifd con compressione zstd
# (qemu monitor o QMP)
# migrate_set_parameter multifd-channels 8
# migrate_set_parameter multifd-compression zstd

# Monitorare progresso migrazione
virsh domjobinfo vm_name
# Output include: Data processed, Data remaining, Memory bandwidth,
# Dirty rate, Downtime, Setup time

# Dirty rate stimato (prima di migrare, per valutare fattibilità)
virsh domdirtyrate-calc vm_name 1    # Calcola dirty rate per 1 secondo
virsh domstats vm_name --dirtyrate   # Leggere risultato
```

### Strategie di Convergenza

Quando il dirty rate supera la banda di migrazione, la VM non converge mai. Tre strategie:

| Strategia | Meccanismo | Pro | Contro |
|-----------|-----------|-----|--------|
| **Auto-converge** | Throttle CPU guest progressivo | Garantisce convergenza | Degrada prestazioni guest |
| **Post-copy** | Trasferisce pagine on-demand dopo switch | Downtime minimo garantito | Se la rete cade, VM corrotta su entrambi i nodi |
| **XBZRLE** | Compressione delta pagine dirty | Riduce banda necessaria | Overhead CPU host, meno efficace con workload random |

```bash
# Post-copy migration (QEMU 9.x con recovery migliorato)
# Fase 1: pre-copy iniziale
virsh migrate --live --postcopy vm_name qemu+ssh://dest/system

# In caso di fallimento post-copy, QEMU 9.1+ tenta recovery automatico
# riconnettendo il canale e riprendendo il trasferimento

# Auto-converge con parametri fini
virsh migrate --live --auto-converge vm_name qemu+ssh://dest/system
# Parametri tunabili via QMP:
# migrate_set_parameter cpu-throttle-initial 20    # % throttle iniziale
# migrate_set_parameter cpu-throttle-increment 10  # incremento per step
# migrate_set_parameter max-cpu-throttle 80        # limite massimo
```

### Mapped-RAM Migration (QEMU 9.0+)

QEMU 9.0 introduce **mapped-ram**: la memoria viene scritta in un formato strutturato con indice, eliminando la necessità di parsing sequenziale. Vantaggi:

- Migrazione a file fino a **2× più veloce** (seek diretto alle pagine sporche)
- Compatibile con backup paralleli (multifd + file)
- Supporto snapshot live più efficiente

```bash
# Migrazione a file con mapped-ram (via QMP)
# migrate_set_parameter multifd-channels 4
# migrate -d "exec:cat > /path/vm-state.bin"
# Il formato mapped-ram è auto-detected se il target è file
```

### Best Practices Migrazione Live

**Pre-requisiti**:
- CPU compatibile tra sorgente e destinazione (stessa famiglia o `host-model` con feature matching)
- Storage condiviso o migrazione con `--copy-storage-all` per storage locale
- Latenza di rete < 5ms tra i nodi (stessa LAN, no WAN senza ottimizzazione)
- Banda di rete > dirty rate della VM (tipicamente 1-10 Gbps)

**Checklist operativa**:
```bash
# 1. Verificare compatibilità CPU
virsh cpu-compare /etc/libvirt/qemu/vm_name.xml   # Sul nodo destinazione

# 2. Verificare connettività
virsh uri --connect qemu+ssh://dest/system

# 3. Calcolare dirty rate e stimare tempo
virsh domdirtyrate-calc vm_name 3
# Se dirty_rate > banda_rete: usare auto-converge o post-copy

# 4. Impostare max downtime accettabile (millisecondi)
virsh migrate-setmaxdowntime vm_name 500

# 5. Impostare bandwidth limit (MiB/s, 0 = illimitato)
virsh migrate-setspeed vm_name 0

# 6. Migrare con monitoraggio
virsh migrate --live --persistent --undefinesource \
  --parallel --parallel-connections 8 \
  --auto-converge --verbose \
  vm_name qemu+ssh://dest/system

# 7. Verificare post-migrazione
virsh list --all   # Su entrambi i nodi
virsh dominfo vm_name   # Sul nodo destinazione
```

**Troubleshooting migrazione**:
- **"migration failed: cannot find domain"**: verificare che il dominio non esista già sulla destinazione
- **"unable to connect"**: controllare firewall (TCP 49152-49215 per QEMU direct), SELinux, e permessi SSH
- **"postcopy migration failed"**: rete interrotta durante post-copy; la VM potrebbe essere irrecuperabile — usare auto-converge in ambienti con rete instabile
- **Migrazione lenta**: verificare che multifd sia attivo, controllare dirty rate, considerare throttling I/O intensivo nella VM prima della migrazione

---

## Snapshot e Backup VM

### Snapshot

```bash
# Snapshot interno (integrato nel file qcow2)
virsh snapshot-create-as vm_name snap1 "Prima dell'aggiornamento"

# Lista snapshot
virsh snapshot-list vm_name
virsh snapshot-list vm_name --tree       # Vista ad albero
virsh snapshot-info vm_name snap1        # Info dettagliate

# Ripristinare
virsh snapshot-revert vm_name snap1

# Eliminare
virsh snapshot-delete vm_name snap1

# Snapshot con memoria (stato completo — come hibernate)
virsh snapshot-create-as vm_name snap_mem --memspec snapshot=internal

# Snapshot esterno (file separati — per backup)
virsh snapshot-create-as vm_name snap_ext \
  --diskspec vda,snapshot=external,file=/var/lib/libvirt/snapshots/vm_snap.qcow2 \
  --disk-only

# Snapshot con quiesce (filesystem consistente, richiede guest agent)
virsh snapshot-create-as vm_name snap_quiesce \
  --disk-only --quiesce

# Snapshot corrente
virsh snapshot-current vm_name
```

### Backup VM

```bash
# BACKUP COMPLETO (VM spenta)
# 1. Backup XML
virsh dumpxml vm_name > vm_name.xml

# 2. Copia disco
cp /var/lib/libvirt/images/vm_name.qcow2 /backup/

# BACKUP A CALDO (VM in esecuzione)
# 1. Snapshot esterno
virsh snapshot-create-as vm_name backup_snap --disk-only --quiesce

# 2. Copia il disco originale (ora è read-only)
cp /var/lib/libvirt/images/vm_name.qcow2 /backup/

# 3. Commit e merge dello snapshot
virsh blockcommit vm_name vda --active --pivot

# 4. Elimina il file snapshot
rm /var/lib/libvirt/snapshots/vm_name.backup_snap.qcow2

# BACKUP INCREMENTALE (libvirt 6.0+, checkpoint-based)
# 1. Creare checkpoint (bitmap dei blocchi modificati)
virsh checkpoint-create-as vm_name chk1

# 2. Backup incrementale via NBD
virsh backup-begin vm_name --backupxml backup.xml

# RESTORE
# 1. Copia il disco nella posizione corretta
# 2. Definisci la VM dall'XML
virsh define vm_name.xml
virsh start vm_name
```

### Script di Backup Automatizzato

```bash
#!/usr/bin/env bash
# backup-vms.sh — Backup a caldo di tutte le VM in esecuzione
set -euo pipefail

BACKUP_DIR="/backup/vms/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

for VM in $(virsh list --name); do
    echo "[$(date +%T)] Backup: $VM"

    # 1. Backup XML
    virsh dumpxml "$VM" > "$BACKUP_DIR/${VM}.xml"

    # 2. Snapshot esterno per frozen del disco
    virsh snapshot-create-as "$VM" backup_snap \
        --disk-only --quiesce --no-metadata 2>/dev/null || \
    virsh snapshot-create-as "$VM" backup_snap \
        --disk-only --no-metadata

    # 3. Copia disco originale (read-only durante snapshot)
    DISK=$(virsh domblklist "$VM" --details | awk '/file.*disk/ {print $4; exit}')
    cp "$DISK" "$BACKUP_DIR/"

    # 4. Commit e pivot al disco originale
    DEV=$(virsh domblklist "$VM" --details | awk '/file.*disk/ {print $3; exit}')
    virsh blockcommit "$VM" "$DEV" --active --pivot --delete

    echo "[$(date +%T)] Completato: $VM"
done

# Pulizia backup vecchi (> 7 giorni)
find /backup/vms/ -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +
```

---

## GPU Passthrough (VFIO)

Il GPU passthrough permette a una VM di usare direttamente una GPU fisica, con performance native. Necessario per gaming in VM, machine learning, VDI.

### Prerequisiti

```text
Requisiti GPU Passthrough:
1. CPU con IOMMU: Intel VT-d o AMD-Vi
2. Motherboard con supporto IOMMU
3. GPU dedicata (non quella usata dall'host per il display)
4. Kernel con VFIO supportato (standard in kernel moderni)
5. GPU nello stesso gruppo IOMMU senza altri dispositivi condivisi
   (oppure ACS override patch)
```

### Configurazione Passo per Passo

```bash
# ── STEP 1: Abilitare IOMMU nel BIOS ───────────────
# Entrare nel BIOS → abilitare VT-d (Intel) o IOMMU (AMD)

# ── STEP 2: Abilitare IOMMU nel kernel ─────────────
# /etc/default/grub
# Intel:
# GRUB_CMDLINE_LINUX="... intel_iommu=on iommu=pt"
# AMD:
# GRUB_CMDLINE_LINUX="... amd_iommu=on iommu=pt"
sudo update-grub
sudo reboot

# ── STEP 3: Verificare IOMMU ───────────────────────
dmesg | grep -e DMAR -e IOMMU
# Deve mostrare "IOMMU enabled"

# ── STEP 4: Identificare la GPU e il suo gruppo IOMMU ──
lspci -nn | grep -i nvidia
# Esempio output: 01:00.0 VGA compatible controller [0300]: NVIDIA ... [10de:2684]
# Esempio output: 01:00.1 Audio device [0403]: NVIDIA ... [10de:22ba]

# Verificare gruppo IOMMU
find /sys/kernel/iommu_groups/ -type l | sort -t/ -k6 -n | \
  while read -r line; do
    group=$(echo "$line" | awk -F/ '{print $6}')
    device=$(basename "$line")
    echo "IOMMU Group $group: $(lspci -nns "$device")"
  done

# TUTTI i dispositivi dello stesso gruppo IOMMU devono essere passati alla VM
# o isolati con VFIO

# ── STEP 5: Caricare driver VFIO ───────────────────
# /etc/modprobe.d/vfio.conf
cat > /etc/modprobe.d/vfio.conf << 'EOF'
options vfio-pci ids=10de:2684,10de:22ba
softdep nvidia pre: vfio-pci
softdep nouveau pre: vfio-pci
EOF

# /etc/modules-load.d/vfio.conf
cat > /etc/modules-load.d/vfio.conf << 'EOF'
vfio
vfio_iommu_type1
vfio_pci
EOF

# Rigenerare initramfs
sudo update-initramfs -u    # Debian/Ubuntu
sudo dracut -f              # RHEL/Fedora

sudo reboot

# ── STEP 6: Verificare che VFIO ha catturato la GPU ──
lspci -nnk -s 01:00
# Kernel driver in use: vfio-pci    ← CORRETTO
# Se mostra nvidia/nouveau → VFIO non ha funzionato

# ── STEP 7: Assegnare GPU alla VM ──────────────────
# Via virt-install:
sudo virt-install \
  --name gpu-vm \
  --ram 16384 \
  --vcpus 8 \
  --disk path=/var/lib/libvirt/images/gpu-vm.qcow2,size=100 \
  --os-variant ubuntu22.04 \
  --network bridge=br0 \
  --host-device 01:00.0 \
  --host-device 01:00.1 \
  --features kvm.hidden.state=on \
  --boot uefi

# Via virsh (dopo la creazione della VM):
virsh attach-device vm_name --file gpu-device.xml --persistent
```

```xml
<!-- gpu-device.xml -->
<hostdev mode='subsystem' type='pci' managed='yes'>
  <source>
    <address domain='0x0000' bus='0x01' slot='0x00' function='0x0'/>
  </source>
</hostdev>

<!-- Nascondere KVM dalla GPU (anti-detect per driver NVIDIA) -->
<features>
  <kvm>
    <hidden state='on'/>
  </kvm>
</features>
```

### Looking Glass (Display senza latenza)

Per vedere l'output della GPU passata senza un monitor fisico:

```bash
# Host: creare shared memory per Looking Glass
# /etc/tmpfiles.d/10-looking-glass.conf
echo 'f /dev/shm/looking-glass 0660 user kvm -' | \
  sudo tee /etc/tmpfiles.d/10-looking-glass.conf

# Aggiungere al domain XML della VM:
# <shmem name='looking-glass'>
#   <model type='ivshmem-plain'/>
#   <size unit='M'>128</size>
# </shmem>

# Guest: installare Looking Glass Host
# Host: installare Looking Glass Client
# looking-glass-client -S    # Avvia client
```

---

## Cloud-init: Provisioning Automatizzato

Cloud-init è lo standard per la configurazione automatica delle VM al primo boot. Supportato da quasi tutte le immagini cloud.

### Architettura Cloud-init

```text
Cloud-init data sources:
┌─────────────────────────────────────────────────┐
│               Cloud-init in VM                   │
│  1. Cerca datasource (config drive, NoCloud, ...) │
│  2. Legge meta-data (hostname, network, ssh key) │
│  3. Legge user-data (script, cloud-config YAML)  │
│  4. Esegue moduli di configurazione              │
│  5. Segnala completamento                        │
└─────────────────────────────────────────────────┘

Datasource per KVM/libvirt: NoCloud
─ meta-data e user-data forniti via ISO o disco
```

### Creare Immagine Cloud-init

```bash
# ── user-data (YAML cloud-config) ──────────────────
cat > user-data << 'EOF'
#cloud-config
hostname: web-server-01
fqdn: web-server-01.example.com
manage_etc_hosts: true

users:
  - name: admin
    groups: sudo
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ssh-ed25519 AAAA... user@host
    lock_passwd: false

# Password (hash generato con: mkpasswd -m sha-512)
chpasswd:
  expire: false
  users:
    - name: admin
      password: $6$rounds=4096$...

# Pacchetti da installare
packages:
  - nginx
  - postgresql
  - fail2ban
  - ufw

# Comandi da eseguire al primo boot
runcmd:
  - systemctl enable --now nginx
  - ufw allow 22/tcp
  - ufw allow 80/tcp
  - ufw allow 443/tcp
  - ufw --force enable

# Configurazione SSH
ssh_pwauth: false
disable_root: true

# Scrivi file
write_files:
  - path: /etc/nginx/sites-available/default
    content: |
      server {
          listen 80;
          server_name _;
          root /var/www/html;
          index index.html;
      }
    permissions: '0644'

# Resize filesystem al boot
growpart:
  mode: auto
  devices: ['/']
  ignore_growroot_disabled: false

# Poweroff o reboot dopo configurazione
power_state:
  mode: reboot
  message: "Cloud-init configurazione completata. Riavvio..."
  timeout: 30
  condition: true
EOF

# ── meta-data ───────────────────────────────────────
cat > meta-data << 'EOF'
instance-id: web-server-01
local-hostname: web-server-01
EOF

# ── network-config (opzionale) ──────────────────────
cat > network-config << 'EOF'
version: 2
ethernets:
  ens3:
    dhcp4: false
    addresses:
      - 10.0.0.100/24
    routes:
      - to: default
        via: 10.0.0.1
    nameservers:
      addresses:
        - 8.8.8.8
        - 8.8.4.4
EOF

# ── Creare ISO NoCloud ──────────────────────────────
genisoimage -output cidata.iso -volid cidata -joliet -rock \
  user-data meta-data network-config
# Alternativa con cloud-localds (dal pacchetto cloud-image-utils):
# cloud-localds cidata.iso user-data meta-data --network-config network-config

# ── Scaricare immagine cloud e creare VM ────────────
wget https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img

# Creare copia dell'immagine come disco VM
qemu-img create -f qcow2 -b jammy-server-cloudimg-amd64.img -F qcow2 web.qcow2
qemu-img resize web.qcow2 40G

# Creare VM con cloud-init
sudo virt-install \
  --name web-server-01 \
  --ram 4096 \
  --vcpus 2 \
  --import \
  --disk path=web.qcow2 \
  --disk path=cidata.iso,device=cdrom \
  --os-variant ubuntu22.04 \
  --network bridge=br0 \
  --noautoconsole

# Verificare cloud-init nel guest
cloud-init status --wait                 # Attende completamento
cloud-init query instanceid              # ID istanza
cat /var/log/cloud-init-output.log       # Log
```

### Data Source NoCloud — Provisioning Offline

NoCloud è il data source più usato per ambienti on-premise e laboratorio. Fornisce i dati cloud-init tramite un disco ISO montato alla VM, senza bisogno di un metadata server di rete.

```bash
# Struttura file per NoCloud
mkdir -p /tmp/cidata
cat > /tmp/cidata/meta-data << 'EOF'
instance-id: iid-local01
local-hostname: server-db-01
network-interfaces: |
  auto eth0
  iface eth0 inet static
    address 192.168.122.50
    netmask 255.255.255.0
    gateway 192.168.122.1
    dns-nameservers 8.8.8.8 1.1.1.1
EOF

cat > /tmp/cidata/user-data << 'EOF'
#cloud-config
hostname: server-db-01
fqdn: server-db-01.lab.local
manage_etc_hosts: true

users:
  - name: deploy
    gecos: Deploy User
    groups: [sudo, docker]
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ssh-ed25519 AAAA... deploy@workstation
    lock_passwd: true

  - name: monitor
    gecos: Monitoring User
    groups: []
    shell: /bin/bash
    ssh_authorized_keys:
      - ssh-ed25519 AAAA... monitor@nagios

package_update: true
package_upgrade: true
packages:
  - qemu-guest-agent
  - htop
  - tmux
  - fail2ban
  - unattended-upgrades

write_files:
  - path: /etc/sysctl.d/99-tuning.conf
    content: |
      vm.swappiness=10
      net.core.somaxconn=65535
      net.ipv4.tcp_max_syn_backlog=65535
    permissions: '0644'

  - path: /etc/security/limits.d/99-nofile.conf
    content: |
      * soft nofile 65535
      * hard nofile 65535
    permissions: '0644'

runcmd:
  - systemctl enable --now qemu-guest-agent
  - systemctl enable --now fail2ban
  - sysctl --system
  - timedatectl set-timezone Europe/Rome

final_message: "Cloud-init completato in $UPTIME secondi"

power_state:
  mode: reboot
  message: "Riavvio post-provisioning"
  timeout: 30
  condition: true
EOF

# Generare ISO NoCloud
genisoimage -output /tmp/cidata.iso -volid cidata \
  -joliet -rock /tmp/cidata/meta-data /tmp/cidata/user-data

# Alternativa con cloud-localds (pacchetto cloud-image-utils)
cloud-localds cidata.iso user-data.yaml meta-data.yaml
```

### Network Config v2

Cloud-init supporta la configurazione di rete v2 (Netplan-style), più flessibile del formato v1:

```yaml
# network-config (file separato nella ISO NoCloud)
version: 2
ethernets:
  eth0:
    match:
      macaddress: "52:54:00:aa:bb:cc"
    addresses:
      - 192.168.122.50/24
    routes:
      - to: default
        via: 192.168.122.1
    nameservers:
      addresses: [8.8.8.8, 1.1.1.1]
      search: [lab.local]
  eth1:
    match:
      macaddress: "52:54:00:aa:bb:dd"
    addresses:
      - 10.0.0.50/24
```

### Template Cloud-init per Proxmox e libvirt

```bash
# Creare template VM con cloud-init (libvirt)
# 1. Scaricare cloud image
wget https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img

# 2. Ridimensionare disco
qemu-img resize noble-server-cloudimg-amd64.img 50G

# 3. Creare VM template
virt-install --name template-ubuntu24 \
  --memory 2048 --vcpus 2 \
  --disk noble-server-cloudimg-amd64.img,bus=virtio \
  --disk cidata.iso,device=cdrom \
  --os-variant ubuntu24.04 \
  --network bridge=br0,model=virtio \
  --graphics none --noautoconsole --import

# 4. Clonare dal template per nuove VM
virt-clone --original template-ubuntu24 \
  --name web-server-01 \
  --file /var/lib/libvirt/images/web-server-01.qcow2

# Template Proxmox con cloud-init integrato
qm create 9000 --name template-ubuntu24 --memory 2048 --cores 2 \
  --net0 virtio,bridge=vmbr0 --scsihw virtio-scsi-single
qm set 9000 --scsi0 local-lvm:0,import-from=/tmp/noble-server-cloudimg-amd64.img
qm set 9000 --ide2 local-lvm:cloudinit
qm set 9000 --boot order=scsi0
qm set 9000 --serial0 socket --vga serial0
qm set 9000 --ipconfig0 ip=dhcp
qm template 9000

# Clonare in Proxmox (full clone)
qm clone 9000 101 --name web-01 --full
qm set 101 --ipconfig0 ip=192.168.1.101/24,gw=192.168.1.1
qm set 101 --sshkeys /root/.ssh/authorized_keys
qm start 101
```

### Troubleshooting Cloud-init

```bash
# Dentro la VM — diagnostica
cloud-init status --long          # Stato dettagliato con errori
cloud-init schema --system        # Validare configurazione corrente
cloud-init query userdata         # Visualizzare user-data ricevuto
journalctl -u cloud-init          # Log systemd

# Re-eseguire cloud-init (dopo modifica config)
sudo cloud-init clean --logs      # Pulire stato
sudo cloud-init init              # Re-inizializzare
sudo cloud-init modules --mode config
sudo cloud-init modules --mode final

# Problemi comuni:
# - "instance-id" invariato → cloud-init non ri-esegue (cambiare instance-id)
# - ISO non montata → verificare device cdrom nella VM
# - YAML invalido → validare con: python3 -c "import yaml; yaml.safe_load(open('user-data'))"
```

---

## Vagrant: Ambienti Riproducibili

Vagrant gestisce il ciclo di vita delle VM tramite un file di configurazione dichiarativo (Vagrantfile).

### Installazione e Concetti

```bash
# Installazione Vagrant
# Debian/Ubuntu (da repo HashiCorp):
wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install vagrant

# Plugin per libvirt (KVM backend)
vagrant plugin install vagrant-libvirt

# Plugin per VirtualBox (alternativa)
# VirtualBox deve essere installato separatamente
```

### Vagrantfile — Esempi

```ruby
# ── Vagrantfile semplice ────────────────────────────
Vagrant.configure("2") do |config|
  config.vm.box = "generic/ubuntu2204"
  config.vm.hostname = "dev-server"
  config.vm.network "private_network", ip: "192.168.56.10"
  config.vm.synced_folder "./data", "/vagrant_data"

  config.vm.provider "libvirt" do |lv|
    lv.memory = 4096
    lv.cpus = 2
    lv.driver = "kvm"
  end

  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get install -y nginx
    systemctl enable --now nginx
  SHELL
end
```

```ruby
# ── Multi-machine environment ───────────────────────
Vagrant.configure("2") do |config|

  # Database server
  config.vm.define "db" do |db|
    db.vm.box = "generic/ubuntu2204"
    db.vm.hostname = "db-server"
    db.vm.network "private_network", ip: "192.168.56.11"
    db.vm.provider "libvirt" do |lv|
      lv.memory = 4096
      lv.cpus = 2
    end
    db.vm.provision "shell", inline: <<-SHELL
      apt-get update
      apt-get install -y postgresql
      systemctl enable --now postgresql
    SHELL
  end

  # Web server
  config.vm.define "web" do |web|
    web.vm.box = "generic/ubuntu2204"
    web.vm.hostname = "web-server"
    web.vm.network "private_network", ip: "192.168.56.12"
    web.vm.network "forwarded_port", guest: 80, host: 8080
    web.vm.provider "libvirt" do |lv|
      lv.memory = 2048
      lv.cpus = 2
    end
    web.vm.provision "shell", inline: <<-SHELL
      apt-get update
      apt-get install -y nginx
    SHELL
  end

  # Load balancer
  config.vm.define "lb" do |lb|
    lb.vm.box = "generic/ubuntu2204"
    lb.vm.hostname = "lb-server"
    lb.vm.network "private_network", ip: "192.168.56.13"
    lb.vm.network "forwarded_port", guest: 80, host: 80
    lb.vm.provider "libvirt" do |lv|
      lv.memory = 1024
      lv.cpus = 1
    end
    lb.vm.provision "ansible" do |ansible|
      ansible.playbook = "playbook.yml"
    end
  end
end
```

### Comandi Vagrant

```bash
# Ciclo di vita
vagrant init generic/ubuntu2204         # Crea Vagrantfile
vagrant up                              # Crea e avvia VM
vagrant up --provider=libvirt           # Specifica provider
vagrant halt                            # Ferma VM
vagrant destroy                         # Elimina VM
vagrant reload                          # Riavvia con nuova config
vagrant suspend                         # Sospendi
vagrant resume                          # Riprendi

# Accesso
vagrant ssh                             # SSH nella VM (default)
vagrant ssh db                          # SSH in VM specifica (multi-machine)

# Provisioning
vagrant provision                       # Riesegui provisioning
vagrant provision --provision-with shell  # Solo un provisioner

# Stato
vagrant status                          # Stato VM
vagrant global-status                   # Tutte le VM Vagrant nel sistema

# Box
vagrant box list                        # Box scaricate
vagrant box add generic/ubuntu2204      # Scarica box
vagrant box remove generic/ubuntu2204   # Rimuovi box
vagrant box update                      # Aggiorna box

# Snapshot
vagrant snapshot save snap1             # Crea snapshot
vagrant snapshot restore snap1          # Ripristina
vagrant snapshot list                   # Lista
vagrant snapshot delete snap1           # Elimina
```

---

## Virtualizzazione Nidificata

La virtualizzazione nidificata permette di eseguire un hypervisor (KVM) dentro una VM. Utile per test, sviluppo, CI/CD.

### Configurazione

```bash
# ── Verificare supporto ────────────────────────────
# Intel:
cat /sys/module/kvm_intel/parameters/nested
# Y = abilitato

# AMD:
cat /sys/module/kvm_amd/parameters/nested
# 1 = abilitato

# ── Abilitare (se non attivo) ──────────────────────
# Intel:
sudo modprobe -r kvm_intel
sudo modprobe kvm_intel nested=1
# Persistente:
echo 'options kvm_intel nested=1' | sudo tee /etc/modprobe.d/kvm-nested.conf

# AMD:
sudo modprobe -r kvm_amd
sudo modprobe kvm_amd nested=1
echo 'options kvm_amd nested=1' | sudo tee /etc/modprobe.d/kvm-nested.conf
```

```xml
<!-- La VM che ospiterà KVM deve avere host-passthrough -->
<cpu mode='host-passthrough' check='none'>
  <feature policy='require' name='vmx'/>  <!-- Intel -->
</cpu>
```

### Casi d'Uso

- **Test infrastruttura**: provare Proxmox, OpenStack, oVirt dentro VM
- **CI/CD**: pipeline che richiedono KVM (es. Android emulator, Packer builds)
- **Formazione**: laboratori di virtualizzazione senza hardware dedicato
- **Cloud**: istanze cloud con supporto nested (GCP, Azure supportano nativamente)

### Impatto sulle Performance

```text
Livello di nesting  │  Overhead CPU  │  Overhead I/O  │  Usabilità
────────────────────┼────────────────┼────────────────┼──────────────
L0 (bare metal)     │  0%            │  0%            │  Produzione
L1 (prima VM)       │  1-5%          │  5-15%         │  Produzione
L2 (VM in VM)       │  15-30%        │  30-50%        │  Test/Dev
L3+ (ulteriore)     │  50%+          │  70%+          │  Non consigliato
```

> **Nota**: la virtualizzazione nidificata oltre L2 è sconsigliata per qualsiasi workload di produzione.

---

## Kata Containers e MicroVM

### Kata Containers — Isolamento Hardware per Container

Kata Containers combina la velocità dei container con l'isolamento hardware delle VM. Ogni container (o pod Kubernetes) gira in una VM leggera dedicata con kernel proprio, eliminando la superficie d'attacco del kernel condiviso tipica dei container tradizionali.

```text
Container tradizionale             Kata Container
┌─────────────────────┐           ┌─────────────────────┐
│  App A  │  App B    │           │  ┌─────┐  ┌─────┐  │
│─────────┤───────────│           │  │VM+A │  │VM+B │  │
│    Kernel condiviso  │           │  │kern │  │kern │  │
│    (singolo)         │           │  └──┬──┘  └──┬──┘  │
│─────────────────────│           │─────┼────────┼─────│
│      Host OS         │           │   KVM / Hypervisor  │
└─────────────────────┘           └─────────────────────┘

Rischio: escape kernel =           Isolamento: ogni container
compromissione totale              ha kernel separato
```

#### Architettura e Runtime

Kata supporta tre VMM (Virtual Machine Monitor) intercambiabili:

| VMM | Boot | Memoria minima | Caso d'Uso |
|-----|------|---------------|------------|
| **QEMU** | ~500ms | ~128 MB | Compatibilità massima, device emulation completa |
| **Cloud Hypervisor** | ~150ms | ~30 MB | Default raccomandato, buon bilanciamento prestazioni/funzionalità |
| **Firecracker** | <125ms | ~5 MB overhead | Serverless, massima densità, funzionalità minime |

```bash
# Installazione Kata Containers (Ubuntu/Debian)
sudo apt-get install -y kata-containers

# Verificare supporto hardware
kata-runtime check

# Configurare containerd per usare Kata
# /etc/containerd/config.toml
# [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata]
#   runtime_type = "io.containerd.kata.v2"

# Kubernetes: usare RuntimeClass
# apiVersion: node.k8s.io/v1
# kind: RuntimeClass
# metadata:
#   name: kata
# handler: kata
```

#### Kata vs Container Tradizionali — Confronto

```text
Aspetto              │ Container (runc) │ Kata Container    │ VM Tradizionale
─────────────────────┼──────────────────┼───────────────────┼─────────────────
Avvio                │ <100ms           │ 150-500ms         │ 5-30s
Overhead memoria     │ ~1 MB            │ 30-128 MB         │ 256 MB+
Isolamento           │ Namespace+cgroup │ VM hardware       │ VM hardware
Kernel               │ Condiviso        │ Dedicato          │ Dedicato
Compatibilità OCI    │ Nativa           │ Completa          │ No
Orchestrazione K8s   │ Nativa           │ Via RuntimeClass  │ KubeVirt
Density (per host)   │ Centinaia        │ Decine-centinaia  │ Decine
```

### Firecracker — MicroVM per Serverless

Firecracker è un VMM scritto in Rust (~50.000 righe) sviluppato da AWS. Utilizzato in produzione per AWS Lambda e Fargate, è progettato per workload serverless con densità estrema: fino a 4.000 microVM per host.

```bash
# Avvio microVM Firecracker (API REST)
# 1. Scaricare binary
curl -L https://github.com/firecracker-microvm/firecracker/releases/download/v1.10.1/firecracker-v1.10.1-x86_64.tgz | tar xz

# 2. Avviare Firecracker con socket API
./firecracker --api-sock /tmp/firecracker.socket

# 3. Configurare kernel e rootfs
curl --unix-socket /tmp/firecracker.socket -X PUT \
  http://localhost/boot-source \
  -H 'Content-Type: application/json' \
  -d '{"kernel_image_path": "./vmlinux", "boot_args": "console=ttyS0 reboot=k panic=1"}'

curl --unix-socket /tmp/firecracker.socket -X PUT \
  http://localhost/drives/rootfs \
  -H 'Content-Type: application/json' \
  -d '{"drive_id": "rootfs", "path_on_host": "./rootfs.ext4", "is_root_device": true, "is_read_only": false}'

# 4. Avviare la microVM
curl --unix-socket /tmp/firecracker.socket -X PUT \
  http://localhost/actions \
  -H 'Content-Type: application/json' \
  -d '{"action_type": "InstanceStart"}'
```

**Caratteristiche chiave di Firecracker**:
- Device model minimale: solo virtio-net, virtio-block, serial, keyboard
- Rate limiter integrato per I/O e rete per microVM
- Snapshot e restore per avvio istantaneo (pre-boot snapshot)
- Jailer per hardening con seccomp, cgroup e chroot
- Nessun supporto GPU, USB, PCI passthrough (by design, per ridurre superficie d'attacco)

### Cloud Hypervisor — Alternativa Moderna

Cloud Hypervisor (progetto Linux Foundation, scritto in Rust) si posiziona tra QEMU e Firecracker: supporta PCI passthrough, VFIO, vDPA e hotplug, mantenendo una codebase snella. È il VMM default raccomandato per Kata Containers dalla versione 3.x.

```bash
# Avvio VM con Cloud Hypervisor
cloud-hypervisor \
  --kernel vmlinux \
  --disk path=rootfs.raw \
  --cpus boot=4 \
  --memory size=2G,hotplug_size=8G \
  --net tap=tap0,mac=AA:BB:CC:DD:EE:FF \
  --api-socket /tmp/ch.socket

# Hotplug CPU a caldo
ch-remote --api-socket /tmp/ch.socket resize --cpus 8

# Hotplug memoria
ch-remote --api-socket /tmp/ch.socket resize --memory 4G
```

### Quando Usare Cosa

| Scenario | Scelta Raccomandata |
|----------|-------------------|
| Multi-tenancy non fidato | Kata Containers + Cloud Hypervisor |
| Serverless / FaaS ad alta densità | Firecracker |
| CI/CD pipeline isolate | Kata Containers |
| VM tradizionali con gestione completa | KVM/QEMU + libvirt |
| Laboratorio e sviluppo | Container tradizionali (runc) |
| Edge computing con risorse limitate | Firecracker o Cloud Hypervisor diretto |

### Benchmark e Sizing MicroVM

La scelta del VMM impatta direttamente la densità raggiungibile per host. Benchmark su hardware tipico (Xeon, 256 GB RAM, NVMe):

```text
VMM              │ VM/host (2 vCPU, 512 MB)  │ Boot medio │ Mem overhead/VM
─────────────────┼───────────────────────────┼────────────┼────────────────
Firecracker      │ ~400                       │ <125ms     │ ~5 MB
Cloud Hypervisor │ ~250                       │ ~150ms     │ ~30 MB
QEMU (microvm)   │ ~150                       │ ~300ms     │ ~50 MB
QEMU (full)      │ ~80                        │ ~500ms     │ ~128 MB
```

**QEMU microvm machine type**: QEMU offre il machine type `microvm` che disabilita l'emulazione di device legacy (PCI bus, ACPI, USB), riducendo l'overhead. Non è leggero come Firecracker ma mantiene l'ecosistema QEMU completo:

```bash
# Avvio QEMU con machine type microvm
qemu-system-x86_64 -M microvm \
  -enable-kvm -cpu host -m 512 -smp 2 \
  -kernel vmlinux -append "console=ttyS0 root=/dev/vda rw" \
  -drive id=rootfs,file=rootfs.img,format=raw,if=none \
  -device virtio-blk-device,drive=rootfs \
  -netdev tap,id=net0,ifname=tap0,script=no \
  -device virtio-net-device,netdev=net0 \
  -nographic -nodefaults -no-user-config \
  -serial stdio
```

### Integrazione MicroVM con Kubernetes

L'integrazione più matura è via **Kata Containers + containerd**:

```yaml
# RuntimeClass Kubernetes per Kata
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata-fc          # Kata con Firecracker
handler: kata-fc
overhead:
  podFixed:
    memory: "130Mi"      # Overhead fisso per pod
    cpu: "250m"
scheduling:
  nodeSelector:
    katacontainers.io/kata-runtime: "true"
---
# Pod con isolamento hardware
apiVersion: v1
kind: Pod
metadata:
  name: secure-workload
spec:
  runtimeClassName: kata-fc
  containers:
    - name: app
      image: registry.example.com/app:v1.2
      resources:
        limits:
          memory: "256Mi"
          cpu: "500m"
```

**KubeVirt** offre un approccio alternativo per VM tradizionali in Kubernetes, gestendo il ciclo di vita completo (creazione, migrazione live, snapshot) tramite CRD Kubernetes. Adatto quando servono VM complete (Windows, appliance) orchestrate con lo stesso tooling dei container.

---

## Sicurezza delle VM

### Isolamento

```text
Livelli di isolamento:
1. Hardware: IOMMU, SR-IOV, CPU (no hyperthreading tra VM)
2. Kernel: KVM module, namespaces, cgroups, seccomp
3. QEMU: sandbox, SELinux/AppArmor, restrizione syscall
4. Rete: VLAN, firewall, segmentazione
5. Storage: permessi, crittografia, separazione pool
```

### Hardening Hypervisor

```bash
# ── SELinux / AppArmor ─────────────────────────────
# Verificare che sVirt sia attivo (SELinux)
ps -eZ | grep qemu
# Ogni VM ha un contesto SELinux diverso (svirt_t)

# AppArmor (Ubuntu): profili in /etc/apparmor.d/libvirt/
ls /etc/apparmor.d/libvirt/

# ── QEMU Sandbox ───────────────────────────────────
# /etc/libvirt/qemu.conf
# security_driver = "selinux"     # o "apparmor"
# security_default_confined = 1
# security_require_confined = 1

# ── Limitare risorse con cgroups ───────────────────
virsh schedinfo vm_name                  # Parametri scheduler
virsh blkiotune vm_name --weight 500     # Peso I/O (100-1000)
virsh memtune vm_name --hard-limit 4194304  # Limite memoria (KiB)

# ── QEMU come utente non-root ─────────────────────
# /etc/libvirt/qemu.conf
# user = "qemu"
# group = "qemu"
# dynamic_ownership = 1
```

### Hardening Guest

```bash
# ── Installare e abilitare qemu-guest-agent ────────
# Nel guest:
sudo apt install qemu-guest-agent        # Debian/Ubuntu
sudo dnf install qemu-guest-agent        # RHEL/Fedora
sudo systemctl enable --now qemu-guest-agent

# ── Disabilitare servizi non necessari ─────────────
# Nel guest: minimizzare la superficie di attacco
sudo systemctl disable --now avahi-daemon
sudo systemctl disable --now cups

# ── Aggiornamenti automatici di sicurezza ──────────
# Ubuntu:
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Crittografia VM

```xml
<!-- Disco crittografato con LUKS (nel domain XML) -->
<disk type='file' device='disk'>
  <driver name='qemu' type='qcow2'/>
  <source file='/var/lib/libvirt/images/encrypted.qcow2'>
    <encryption format='luks'>
      <secret type='passphrase' uuid='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'/>
    </encryption>
  </source>
  <target dev='vda' bus='virtio'/>
</disk>
```

```bash
# Creare secret in libvirt
cat > secret.xml << 'EOF'
<secret ephemeral='no' private='yes'>
  <uuid>xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx</uuid>
  <description>LUKS passphrase for VM disk</description>
</secret>
EOF
virsh secret-define secret.xml
virsh secret-set-value xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx "$(echo -n 'passphrase' | base64)"
```

### Confidential Computing

Le tecnologie di Confidential Computing proteggono i dati in uso (in memoria) da accessi non autorizzati, incluso l'hypervisor.

```text
Tecnologia          │  Vendor  │  Protezione
────────────────────┼──────────┼──────────────────────────
AMD SEV             │  AMD     │  Crittografia memoria VM
AMD SEV-ES          │  AMD     │  + Crittografia registri CPU
AMD SEV-SNP         │  AMD     │  + Integrity attestation
Intel TDX           │  Intel   │  Trust Domain con attestation
```

---

## Proxmox VE

Proxmox VE è una piattaforma di virtualizzazione enterprise open source basata su Debian, KVM e LXC.

```bash
# Installazione: da ISO dedicata (proxmox-ve_*.iso)
# Interfaccia web: https://proxmox-ip:8006

# CLI (qm per VM, pct per container LXC)
qm list                                # Lista VM
qm start 100                           # Avvia VM 100
qm stop 100                            # Ferma
qm shutdown 100                        # Shutdown ACPI
qm status 100                          # Stato VM

qm create 101 --memory 4096 --cores 2 --name web-server \
  --net0 virtio,bridge=vmbr0 --scsi0 local-lvm:32

qm set 101 --ide2 local:iso/ubuntu-22.04-server.iso,media=cdrom
qm set 101 --boot order=ide2

pct list                                # Lista container LXC
pct start 200
pct enter 200                           # Shell nel container
pct exec 200 -- apt update             # Eseguire comando nel container

# Storage
pvesm status                            # Storage disponibili
pvesm list local                        # Contenuto storage
pvesm alloc local-lvm 101 vm-101-disk-1 32G  # Allocare disco

# Backup
vzdump 100 --storage local --mode snapshot  # Backup VM 100
vzdump 100 --storage local --mode snapshot --compress zstd
qmrestore /var/lib/vz/dump/vzdump-qemu-100-*.vma 101  # Restore

# Cluster
pvecm status                            # Stato cluster
pvecm create cluster1                   # Crea cluster
pvecm add 10.0.0.2                      # Aggiungi nodo
pvecm nodes                             # Lista nodi

# HA (High Availability)
ha-manager status                       # Stato HA
ha-manager add vm:100 --group ha-group  # Aggiungere VM a HA
ha-manager set vm:100 --state started   # Stato desiderato
```

### Proxmox — Storage Backend

```text
Backend          │  Tipo         │  Snapshot  │  Clone    │  Caso d'uso
─────────────────┼───────────────┼────────────┼───────────┼─────────────────
LVM              │  Block        │  No        │  No       │  Base, semplice
LVM-thin         │  Block        │  Sì        │  Sì       │  Default consigliato
ZFS              │  Block+File   │  Sì        │  Sì       │  Dedup, compressione
Ceph (RBD)       │  Distribuito  │  Sì        │  Sì       │  HA, cluster
NFS/CIFS         │  File (rete)  │  qcow2     │  qcow2    │  Storage condiviso
GlusterFS        │  Distribuito  │  qcow2     │  qcow2    │  Distribuito semplice
Directory        │  File         │  qcow2     │  qcow2    │  Test, piccoli deploy
```

### Proxmox VE 8.x — Gestione Cluster Avanzata

Proxmox VE 8.x (basato su Debian 12 Bookworm con kernel 6.x) introduce un modello cluster multi-master senza single point of failure.

#### Architettura Cluster

```text
┌─────────────────────────────────────────────────────────────┐
│                    Proxmox Cluster                          │
│                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  Nodo 1  │◄──►│  Nodo 2  │◄──►│  Nodo 3  │             │
│   │ Corosync │    │ Corosync │    │ Corosync │             │
│   │  pmxcfs  │    │  pmxcfs  │    │  pmxcfs  │             │
│   │ pve-ha   │    │ pve-ha   │    │ pve-ha   │             │
│   └──────────┘    └──────────┘    └──────────┘             │
│        │               │               │                    │
│        └───────────────┼───────────────┘                    │
│                        │                                    │
│              ┌─────────┴─────────┐                          │
│              │   Storage Condiv. │                          │
│              │  Ceph / NFS / iSCSI│                         │
│              └───────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

**Corosync** gestisce la comunicazione inter-nodo con il protocollo Totem Single Ring Ordering. Ogni nodo ha voto nel quorum; con 3 nodi serve la maggioranza (2/3) per operare. **pmxcfs** replica la configurazione `/etc/pve` su tutti i nodi via Corosync, eliminando la necessità di un database centrale.

```bash
# Creare cluster
pvecm create nome-cluster

# Aggiungere nodo al cluster (dal nuovo nodo)
pvecm add IP_NODO_ESISTENTE

# Stato cluster
pvecm status

# Nodi e quorum
pvecm nodes
pvecm expected 2    # Forzare quorum (SOLO emergenza con dati coerenti)
```

#### HA Manager e Fencing

L'HA manager di Proxmox utilizza un modello master-worker. Il nodo con il lock CRM diventa HA manager e monitora le risorse. Il **fencing basato su watchdog** (`softdog` o hardware IPMI) garantisce l'isolamento del nodo guasto: se un nodo non aggiorna il watchdog entro il timeout (default 60s), viene forzato al riavvio.

```bash
# Configurare risorsa HA
ha-manager set vm:100 --state started --group ha-group-1 --max_relocate 2 --max_restart 3

# Stato risorse HA
ha-manager status

# Gruppi HA (preferenze nodo)
# /etc/pve/ha/groups.cfg
group: ha-group-1
    nodes node1:2,node2:1,node3:1    # Priorità: node1 preferito
    restricted 0                       # 0 = può girare ovunque se necessario
    nofailback 0                       # 0 = torna al nodo preferito quando disponibile
```

**Requisiti HA**:
- Minimo 3 nodi per quorum affidabile
- Storage condiviso (Ceph RBD, NFS, iSCSI)
- Rete dedicata per Corosync (separata dal traffico VM)
- Watchdog hardware (IPMI) consigliato per produzione; `softdog` accettabile in ambienti non critici

#### SDN (Software-Defined Networking) in Proxmox

Proxmox 8.x integra un framework SDN completo accessibile dalla GUI e dalla CLI. Le **zone** definiscono il tipo di isolamento di rete:

| Tipo Zona | Protocollo | Caso d'Uso |
|-----------|-----------|------------|
| **Simple** | Bridge locale | Rete isolata per nodo singolo |
| **VLAN** | 802.1Q | Segregazione classica, fino a 4094 reti |
| **QinQ** | 802.1ad | VLAN stacking per provider/tenant |
| **VXLAN** | UDP overlay | Overlay L2 su L3, fino a 16M segmenti |
| **EVPN** | BGP + VXLAN | Routing distribuito L3, multi-datacenter |

```bash
# Creare zona VXLAN
pvesh create /cluster/sdn/zones --zone vxzone1 --type vxlan \
  --peers "10.0.0.1,10.0.0.2,10.0.0.3" --mtu 1450

# Creare VNet nella zona
pvesh create /cluster/sdn/vnets --vnet vnet100 --zone vxzone1 --tag 100

# Creare subnet
pvesh create /cluster/sdn/vnets/vnet100/subnets \
  --subnet 10.100.0.0/24 --gateway 10.100.0.1

# Applicare configurazione SDN
pvesh set /cluster/sdn
```

**EVPN** è la scelta raccomandata per ambienti multi-datacenter: utilizza BGP per annunciare le rotte MAC/IP tra i nodi, eliminando il flooding BUM (Broadcast, Unknown unicast, Multicast) tipico di VXLAN puro.

#### Proxmox Backup Server (PBS)

PBS è il companion dedicato per backup incrementali con deduplicazione a livello di chunk. Opera su chunk da 4 MB con hashing SHA-256 per deduplicazione, compressione zstd e crittografia AES-256-GCM opzionale lato client.

```bash
# Backup VM da Proxmox VE verso PBS
vzdump 100 --storage pbs-store --mode snapshot --compress zstd

# Backup pianificato (crontab o GUI → Datacenter → Backup)
# Ogni notte alle 02:00, retention: 7 daily, 4 weekly, 6 monthly
vzdump 100 101 102 --storage pbs-store --mode snapshot \
  --compress zstd --schedule "02:00" \
  --prune-backups keep-daily=7,keep-weekly=4,keep-monthly=6

# Verificare integrità backup (da PBS)
proxmox-backup-client verify --repository user@pbs:datastore1

# Garbage collection (pulizia chunk orfani)
proxmox-backup-manager garbage-collection run datastore1
```

Il **pruning** automatico con politiche di retention (daily/weekly/monthly/yearly) previene la crescita incontrollata dello storage. La **verifica periodica** (`verify`) controlla l'integrità di ogni chunk e segnala corruzione.

#### Best Practices Proxmox Produzione

**Rete**:
- Rete dedicata Corosync (almeno 1 Gbps, meglio 10 Gbps) separata dal traffico VM
- Bonding LACP (802.3ad) per ridondanza uplink
- Jumbo frame (MTU 9000) su storage network Ceph/iSCSI

**Storage**:
- Ceph per HA nativo: 3 OSD minimi, pool replicato con size=3, min_size=2
- SSD/NVMe per journal e metadata Ceph; HDD per capacity tier
- ZFS per nodi singoli: mirror o raidz2 con `ashift=12` per SSD

**HA e Quorum**:
- Sempre 3+ nodi (o 2 nodi + QDevice esterno per quorum a 2)
- Testare failover regolarmente con `ha-manager migrate`
- Non superare 32 nodi per cluster (limite raccomandato Corosync)

**Backup**:
- PBS dedicato su hardware separato
- Verifica automatica settimanale dei backup
- Replica offsite per disaster recovery (PBS → PBS remoto via sync job)

---

## Confronto: KVM vs Proxmox vs VMware vs Hyper-V

| Caratteristica | KVM (libvirt) | Proxmox VE | VMware vSphere | Hyper-V |
|---|---|---|---|---|
| **Licenza** | GPL (gratuito) | AGPL (gratuito, sub. opzionale) | Proprietario ($$$$) | Incluso in Win Server |
| **Base** | Kernel Linux | Debian + KVM + LXC | ESXi (proprietario) | Windows kernel |
| **GUI** | virt-manager, Cockpit | Web UI integrata | vCenter (web) | Hyper-V Manager, WAC |
| **CLI** | virsh, virt-install | qm, pct, pvesm | esxcli, PowerCLI | PowerShell |
| **Container** | No (separato: LXD) | LXC integrato | No | No (Docker separato) |
| **HA** | Manuale (Pacemaker) | Integrato | vSphere HA | Failover Clustering |
| **Storage** | Qualsiasi + libvirt pool | LVM, ZFS, Ceph, NFS | vSAN, VMFS, NFS | CSV, SMB, iSCSI |
| **Live migration** | virsh migrate | Web UI + CLI | vMotion | Live Migration |
| **Backup** | Script manuali | vzdump integrato | Veeam, VADP | Windows Server Backup |
| **Networking** | Bridge, OVS, SR-IOV | Bridge, OVS, SDN | vDS, NSX | vSwitch, SET |
| **GPU passthrough** | VFIO | VFIO (via CLI) | DirectPath I/O | DDA |
| **API** | libvirt API | REST API | vSphere API | WMI, REST |
| **Curva apprend.** | Alta | Media | Media-Alta | Media |
| **Scala** | Illimitata | Cluster fino a 32 nodi | vCenter: 2000 host | 64 nodi cluster |
| **Community** | Enorme | Grande, attiva | Enterprise (forum) | Microsoft community |

### Quando scegliere cosa

```text
KVM puro (libvirt):
─ Massimo controllo e personalizzazione
─ Integrazione con Ansible/Terraform
─ Ambienti cloud (OpenStack, CloudStack)
─ Quando il team conosce Linux a fondo

Proxmox VE:
─ SMB/PMI senza budget per VMware
─ Cluster piccoli-medi (2-16 nodi)
─ Necessità di LXC + KVM insieme
─ Web UI senza componenti aggiuntivi

VMware vSphere:
─ Enterprise con requisiti di supporto
─ Ecosistema esistente VMware
─ vSAN per storage iperconvergente
─ NSX per networking avanzato

Hyper-V:
─ Ambiente prevalentemente Windows
─ Licenze Windows Server già possedute
─ Integrazione Active Directory
─ Azure hybrid (Azure Arc)
```

---

## VDI — Virtual Desktop Infrastructure con Linux

VDI fornisce desktop virtualizzati accessibili da thin client o browser.

### Stack VDI Open Source

```text
Componenti VDI Linux:
┌─────────────────────────────────────────────────┐
│  Client (thin client, browser, software)         │
│  Protocolli: SPICE, RDP (xrdp), VNC, PCoIP      │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Connection Broker                               │
│  Apache Guacamole, oVirt, Proxmox VE             │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Hypervisor                                      │
│  KVM + libvirt, Proxmox, oVirt                   │
│  Desktop VM (Ubuntu Desktop, Fedora Workstation) │
└─────────────────────────────────────────────────┘
```

### Apache Guacamole (VDI via Browser)

```bash
# Guacamole: accesso remoto via browser (HTML5)
# Supporta: RDP, VNC, SSH, SFTP, Kubernetes
# Nessun client da installare

# Installazione con Docker Compose
cat > docker-compose.yml << 'EOF'
services:
  guacd:
    image: guacamole/guacd
    restart: always

  guacamole:
    image: guacamole/guacamole
    restart: always
    ports:
      - "8080:8080"
    environment:
      GUACD_HOSTNAME: guacd
      POSTGRESQL_HOSTNAME: postgres
      POSTGRESQL_DATABASE: guacamole_db
      POSTGRESQL_USER: guacamole_user
      POSTGRESQL_PASSWORD: "${GUAC_DB_PASS}"
    depends_on:
      - guacd
      - postgres

  postgres:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_DB: guacamole_db
      POSTGRES_USER: guacamole_user
      POSTGRES_PASSWORD: "${GUAC_DB_PASS}"
    volumes:
      - ./init:/docker-entrypoint-initdb.d
      - pg_data:/var/lib/postgresql/data

volumes:
  pg_data:
EOF
```

### SPICE (Simple Protocol for Independent Computing Environments)

```bash
# SPICE: protocollo ottimizzato per desktop virtuali
# Feature: USB redirect, audio, clipboard, multi-monitor

# Configurare VM con SPICE (domain XML):
# <graphics type='spice' autoport='yes'>
#   <listen type='address' address='0.0.0.0'/>
#   <streaming mode='filter'/>
#   <image compression='auto_glz'/>
# </graphics>
# <video>
#   <model type='qxl' ram='65536' vram='65536' heads='2'/>
# </video>

# Client SPICE
remote-viewer spice://host:5900
virt-viewer --connect qemu:///system vm_name

# USB redirect (da client a VM)
# In remote-viewer: menu → USB device selection
```

---

## Setup KVM da Zero — Passo per Passo

### Ubuntu Server 22.04 / 24.04

```bash
# ── STEP 1: Verificare hardware ────────────────────
grep -Ec '(vmx|svm)' /proc/cpuinfo
# Se 0: abilitare VT-x/AMD-V nel BIOS

egrep -c ' lm ' /proc/cpuinfo
# Se > 0: CPU a 64 bit (necessario)

# ── STEP 2: Installare pacchetti ───────────────────
sudo apt update
sudo apt install -y \
  qemu-kvm \
  libvirt-daemon-system \
  libvirt-clients \
  virtinst \
  bridge-utils \
  virt-manager \
  qemu-utils \
  ovmf \
  cloud-image-utils \
  guestfs-tools

# ── STEP 3: Verificare servizi ─────────────────────
sudo systemctl status libvirtd
sudo systemctl enable --now libvirtd

# ── STEP 4: Configurare utente ─────────────────────
sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER
# LOGOUT E LOGIN necessario

# ── STEP 5: Verificare funzionamento ───────────────
virsh list --all                         # Nessun errore
virsh net-list --all                     # Rete 'default' presente
virsh pool-list --all                    # Pool 'default' presente

# Se la rete default non è attiva:
virsh net-start default
virsh net-autostart default

# ── STEP 6: Configurare bridge (produzione) ────────
# /etc/netplan/01-bridge.yaml
cat > /tmp/bridge.yaml << 'YAML'
network:
  version: 2
  renderer: networkd
  ethernets:
    ens33:                               # Sostituire con la propria NIC
      dhcp4: no
  bridges:
    br0:
      interfaces: [ens33]
      dhcp4: yes
      parameters:
        stp: false
        forward-delay: 0
YAML
sudo cp /tmp/bridge.yaml /etc/netplan/01-bridge.yaml
sudo netplan apply

# ── STEP 7: Prima VM di test ───────────────────────
# Scaricare immagine cloud
wget -O /var/lib/libvirt/images/jammy-cloud.img \
  https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img

# Creare disco da immagine cloud
sudo qemu-img create -f qcow2 \
  -b /var/lib/libvirt/images/jammy-cloud.img -F qcow2 \
  /var/lib/libvirt/images/test-vm.qcow2 20G

# Creare VM con cloud-init
sudo virt-install \
  --name test-vm \
  --ram 2048 \
  --vcpus 2 \
  --import \
  --disk /var/lib/libvirt/images/test-vm.qcow2 \
  --os-variant ubuntu22.04 \
  --network network=default \
  --cloud-init root-password-generate=on \
  --noautoconsole

# Verificare
virsh list
virsh console test-vm                    # Ctrl+] per uscire
```

### RHEL 9 / Rocky Linux 9 / AlmaLinux 9

```bash
# ── STEP 1: Verificare hardware ────────────────────
grep -Ec '(vmx|svm)' /proc/cpuinfo

# ── STEP 2: Installare ─────────────────────────────
sudo dnf install -y @virtualization-hypervisor @virtualization-client \
  @virtualization-platform @virtualization-tools

# Oppure pacchetti singoli:
sudo dnf install -y qemu-kvm libvirt virt-install virt-manager \
  qemu-img edk2-ovmf guestfs-tools

# ── STEP 3: Abilitare servizi ──────────────────────
sudo systemctl enable --now libvirtd

# ── STEP 4: Configurare utente ─────────────────────
sudo usermod -aG libvirt $USER

# ── STEP 5: Verificare ─────────────────────────────
virt-host-validate                       # Verifica completa del supporto
virsh list --all

# ── STEP 6: Bridge con nmcli ───────────────────────
sudo nmcli connection add type bridge con-name br0 ifname br0
sudo nmcli connection add type ethernet slave-type bridge \
  con-name br0-port1 ifname ens192 master br0
sudo nmcli connection modify br0 ipv4.method auto
sudo nmcli connection up br0

# ── STEP 7: Firewall per libvirt ───────────────────
sudo firewall-cmd --permanent --zone=libvirt --add-service=libvirt
sudo firewall-cmd --reload
```

---

## Best Practices

1. **qcow2 per flessibilità**: usare qcow2 come formato disco standard. Supporta snapshot, thin provisioning e compressione. Raw solo per workload I/O-intensive
2. **Bridge per produzione**: usare bridged networking per VM di produzione. NAT va bene solo per sviluppo/test
3. **Snapshot prima delle modifiche**: sempre creare snapshot prima di aggiornamenti, cambiamenti di configurazione, o test. Rollback istantaneo in caso di problemi
4. **Non abusare degli snapshot**: gli snapshot accumulati degradano le performance I/O. Dopo il test, fare commit o eliminare
5. **Backup regolari**: automatizzare il backup delle VM (XML + disco). Verificare periodicamente il restore
6. **Risorse appropriate**: non over-allocare CPU e RAM. Il vCPU:pCPU ratio consigliato è 2:1 per workload misti
7. **Monitorare l'host**: un host sovraccarico degrada tutte le VM. Monitorare CPU, memoria, I/O e rete dell'hypervisor
8. **VirtIO ovunque**: usare sempre driver virtio per disco (virtio-scsi o virtio-blk) e rete (virtio-net). Mai IDE o e1000 in produzione
9. **cache=none per dischi**: in produzione, usare `cache='none'` con `io='native'` per i dischi. Evita double-caching e garantisce data integrity
10. **Hugepages per VM grandi**: VM con 8GB+ di RAM beneficiano significativamente delle hugepages (2MB o 1GB)
11. **CPU pinning per workload sensibili alla latenza**: database, applicazioni real-time. Evitare per VM generiche (riduce flessibilità scheduler)
12. **UEFI per VM moderne**: usare OVMF (UEFI) al posto di SeaBIOS per Secure Boot, GPT, e compatibilità moderna
13. **Guest agent sempre**: installare `qemu-guest-agent` in tutte le VM per shutdown pulito, freeze filesystem, e monitoraggio
14. **Separare storage pool**: pool diversi per OS disk, data disk, ISO, backup. Permette politiche diverse
15. **Documentare le VM**: usare `virsh desc` e tag XML per documentare lo scopo di ogni VM
16. **Testare il disaster recovery**: simulare periodicamente il restore di backup e la migrazione tra host

---

## Troubleshooting — 25+ Problemi Comuni

**"VM non si avvia: 'failed to initialize KVM'"** → KVM non è abilitato. Verificare: `grep -Ec '(vmx|svm)' /proc/cpuinfo` (deve essere > 0). Nel BIOS: abilitare VT-x/AMD-V. Verificare modulo: `lsmod | grep kvm`, se mancante: `sudo modprobe kvm_intel` o `kvm_amd`.

**"VM lenta (I/O)"** → Verificare il driver disco nella VM: usare `virtio` (non IDE). `virsh edit vm` → `<disk>` deve avere `<driver name='qemu' type='qcow2'/>` e `<target dev='vda' bus='virtio'/>`. Installare guest agent: `apt install qemu-guest-agent`.

**"Rete nella VM non funziona"** → `virsh domiflist vm` per verificare rete assegnata. Per bridge: il bridge esiste sull'host? `ip link show br0`. La VM ha il driver virtio? Per NAT: `virsh net-list` → la rete default è attiva?

**"Migrazione live fallisce"** → Cause: CPU incompatibili (usare `--copy-storage-all` con `--unsafe` o configurare CPU model `host-model`), storage non condiviso, rete tra host bloccata, permessi SSH.

**"VM non si avvia: 'cannot access storage file'"** → Permessi. Verificare: `ls -la /var/lib/libvirt/images/disco.qcow2`. L'utente `libvirt-qemu` (o `qemu`) deve avere accesso in lettura/scrittura. Fix: `sudo chown libvirt-qemu:kvm /var/lib/libvirt/images/disco.qcow2` oppure `sudo chmod 660 /var/lib/libvirt/images/disco.qcow2`. Se AppArmor blocca: `sudo aa-complain /usr/sbin/libvirtd`.

**"Errore 'permission denied' su /dev/kvm'"** → L'utente non è nel gruppo `kvm`. Fix: `sudo usermod -aG kvm $USER && newgrp kvm`. Verificare permessi: `ls -la /dev/kvm` (deve essere crw-rw---- root:kvm).

**"VM si avvia ma lo schermo è nero in virt-manager"** → Il driver video potrebbe non essere supportato. Provare: `virsh edit vm` → cambiare `<model type='qxl'/>` a `<model type='virtio'/>` o `<model type='vga'/>`. Per VM Windows: installare gli SPICE guest tools.

**"Cannot access storage: pool 'default' not found"** → Il pool storage non è attivo. Fix: `virsh pool-start default && virsh pool-autostart default`. Se non esiste: `virsh pool-define-as default dir --target /var/lib/libvirt/images && virsh pool-build default && virsh pool-start default && virsh pool-autostart default`.

**"Network 'default' is not active"** → `virsh net-start default && virsh net-autostart default`. Se la rete non esiste, ricrearla: `virsh net-define /usr/share/libvirt/networks/default.xml && virsh net-start default && virsh net-autostart default`.

**"VM molto lenta (CPU)"** → Verificare che KVM sia effettivamente usato (non emulazione QEMU pura): `virsh dumpxml vm | grep -i "domain type"` deve mostrare `kvm`, non `qemu`. Verificare CPU overcommit: se troppe vCPU rispetto ai core fisici, le VM si contendono la CPU.

**"Snapshot non funziona: 'unsupported configuration'"** → Gli snapshot interni richiedono formato qcow2. Un disco raw non supporta snapshot. Convertire: `qemu-img convert -f raw -O qcow2 disk.raw disk.qcow2`. Aggiornare il domain XML.

**"Disco pieno nell'host"** → Thin provisioning: il disco qcow2 cresce fino a raggiungere la dimensione massima. Monitorare: `qemu-img info --output=json disk.qcow2 | jq '.["actual-size"]'`. Se ci sono molti snapshot, consolidarli: `virsh blockcommit vm_name vda --active --pivot`.

**"VM non risponde a virsh shutdown"** → Il guest non ha ACPI abilitato, oppure non ha un handler per ACPI power button. Fix: `virsh destroy vm_name` (forza spegnimento). Per prevenire: installare `acpid` nel guest.

**"Errore 'operation not supported: QEMU binary does not support UEFI'"** → Il pacchetto OVMF non è installato. Fix: `sudo apt install ovmf` (Debian/Ubuntu) o `sudo dnf install edk2-ovmf` (RHEL). Verificare: `ls /usr/share/OVMF/`.

**"VM con Windows molto lenta"** → Driver virtio non installati. Scaricare ISO virtio-win da Fedora e installare i driver nella VM: rete (NetKVM), disco (vioscsi/viostor), balloon (balloon), display (qxl/virtio-gpu). `wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso`.

**"Live migration: 'Timed out during operation'"** → Il dirty rate della VM supera la banda di rete. Soluzioni: aumentare la banda (`--bandwidth`), usare `--auto-converge` (rallenta la vCPU), passare a post-copy (`--postcopy`), o usare compressione (`--compressed`).

**"Errore VFIO: 'failed to set up IOMMU'"** → IOMMU non abilitato. Verificare: `dmesg | grep -i iommu`. Nel GRUB: `intel_iommu=on iommu=pt` (Intel) o `amd_iommu=on iommu=pt` (AMD). Riavviare dopo `update-grub`.

**"GPU passthrough: 'device is in use'"** → Il driver dell'host (nvidia, nouveau, amdgpu) sta usando la GPU. Configurare VFIO per catturarla prima: `/etc/modprobe.d/vfio.conf` con `softdep nvidia pre: vfio-pci`. Rigenerare initramfs e riavviare.

**"Errore: 'Unable to find security driver'"** → Mismatch tra il driver di sicurezza configurato in `/etc/libvirt/qemu.conf` e quello disponibile nel sistema. Su Ubuntu (AppArmor): `security_driver = "apparmor"`. Su RHEL (SELinux): `security_driver = "selinux"`.

**"VM non ottiene IP dalla rete bridge"** → Il bridge non ha la NIC fisica come slave. Verificare: `bridge link show`. Se il bridge è vuoto: `sudo nmcli connection modify br0-slave connection.slave-type bridge connection.master br0 && sudo nmcli connection up br0`. Verificare anche che il firewall dell'host non blocchi il traffico bridge: `sudo sysctl net.bridge.bridge-nf-call-iptables=0`.

**"Errore 'XML error: missing domain type'"** → Il file XML è corrotto o manca l'attributo `type` nel tag `<domain>`. Deve essere `<domain type='kvm'>`. Verificare con: `xmllint --noout vm.xml`.

**"qemu-img: Cannot grow image which has snapshots"** → Non si può ridimensionare un'immagine con snapshot attivi. Eliminare gli snapshot prima: `qemu-img snapshot -d snap_name disk.qcow2`, poi ridimensionare.

**"VM usa troppa RAM dell'host"** → Balloon driver non installato o non funzionante. Nel guest: `lsmod | grep virtio_balloon`. Se mancante: `sudo modprobe virtio_balloon`. Nel domain XML: `<memballoon model='virtio'/>`. Impostare la memoria corrente inferiore alla massima: `virsh setmem vm_name 4G --live`.

**"Errore 'Unable to read from monitor'"** → Il processo QEMU è crashato. Controllare i log: `cat /var/log/libvirt/qemu/vm_name.log`. Cause comuni: memoria insufficiente sull'host (OOM killer), disco pieno, bug QEMU. Se OOM: aumentare la RAM host o ridurre le VM.

**"Cloud-init non si esegue nella VM"** → Verificare che il datasource sia corretto. L'ISO cloud-init deve avere volume label `cidata`. Verificare: `isoinfo -d -i cidata.iso | grep "Volume id"`. Se diverso, ricreare con: `genisoimage -output cidata.iso -volid cidata -joliet -rock user-data meta-data`.

**"Errore durante clone: 'Disk images are in use'"** → La VM sorgente è in esecuzione. Per clonare, la VM deve essere spenta: `virsh shutdown vm_name` poi `virt-clone --original vm_name --name clone_name --auto-clone`.

---

## FAQ — 18 Domande Frequenti

**Q1: KVM è Type 1 o Type 2?**
KVM è classificato come Type 1 (bare-metal). Anche se gira come modulo del kernel Linux, il kernel stesso diventa l'hypervisor. Non c'è un OS "sotto" KVM — Linux IS l'hypervisor. La distinzione è che KVM usa il kernel Linux come hypervisor diretto, non come un'applicazione che gira sopra un OS separato.

**Q2: Quante VM posso eseguire su un host?**
Dipende dalle risorse. Come regola pratica: vCPU totali ≤ 2x core fisici per workload misti, RAM totale ≤ RAM fisica (con balloon e KSM si può superare leggermente). Un server con 64 core e 256GB RAM può ospitare 30-50 VM tipiche. Il fattore limitante è spesso l'I/O disco, non CPU/RAM.

**Q3: Devo usare qcow2 o raw?**
qcow2 per il 95% dei casi: supporta snapshot, thin provisioning, compressione, crittografia. Raw solo per workload I/O-intensivi dove ogni percentuale di performance conta (database dedicati, storage server). La differenza di performance tra qcow2 e raw è circa 5-15% in I/O, trascurabile per la maggior parte dei carichi.

**Q4: Come ottengo le migliori performance per una VM?**
In ordine di impatto: 1) VirtIO per disco e rete, 2) cache=none + io=native per i dischi, 3) CPU host-passthrough, 4) Hugepages, 5) CPU pinning, 6) IOThreads, 7) virtio-scsi multiqueue. Per rete: vhost-net + multiqueue. Per GPU-intensive: GPU passthrough VFIO.

**Q5: La virtualizzazione nidificata è adatta per la produzione?**
No. L'overhead è significativo (15-30% CPU, 30-50% I/O). Va bene per test, sviluppo, CI/CD, formazione. In produzione, usare sempre bare-metal come L0.

**Q6: Come migrare VM da VMware a KVM?**
1) Spegnere la VM in VMware, 2) Esportare come OVA/OVF, 3) Convertire il disco: `qemu-img convert -f vmdk -O qcow2 disk.vmdk disk.qcow2`, 4) Creare VM con virt-install usando il disco convertito, 5) Adattare driver a virtio nel guest (potrebbe essere necessario aggiungere i driver prima della migrazione).

**Q7: È sicuro usare overcommit di memoria?**
Con cautela. KSM e balloon aiutano, ma se le VM usano effettivamente tutta la RAM allocata, l'host andrà in swap (disastroso per le performance) o l'OOM killer terminerà processi QEMU. Regola: overcommit massimo 1.3x con monitoraggio attento. Mai per workload critici.

**Q8: Come funziona il GPU passthrough?**
VFIO assegna un dispositivo PCI (GPU) direttamente alla VM, bypassando l'hypervisor. La VM ha accesso esclusivo alla GPU con performance native. Richiede IOMMU (VT-d/AMD-Vi). L'host non può usare la GPU passata. Per vedere l'output: monitor fisico collegato alla GPU, o Looking Glass per display software.

**Q9: Posso usare SPICE/VNC per accedere alle VM via rete?**
Sì. VNC: universale, qualsiasi client VNC funziona. SPICE: migliore qualità, supporta USB redirect, audio, clipboard condiviso, multi-monitor. Per accesso via browser: Apache Guacamole. Per sicurezza: tunneling SSH o VPN, mai esporre VNC/SPICE direttamente su internet.

**Q10: Come automatizzare la creazione di VM?**
Opzioni: 1) Cloud-init + immagini cloud per provisioning automatico, 2) Vagrant per ambienti riproducibili, 3) Ansible con modulo `community.libvirt`, 4) Terraform con provider libvirt, 5) Packer per creare immagini template. Per infrastruttura grande: OpenStack o Proxmox API.

**Q11: Qual è la differenza tra virsh save e snapshot?**
`virsh save`: salva lo stato completo della VM (memoria + CPU) su disco e la spegne. Come l'ibernazione. `virsh snapshot`: crea un punto di ripristino del disco (e opzionalmente della memoria) senza spegnere la VM. Gli snapshot sono per il rollback rapido, save/restore per la sospensione persistente.

**Q12: Come monitoro le performance delle VM?**
Host: `virt-top` (come htop per VM), `virsh domstats`, `virsh cpu-stats`. Guest: `qemu-guest-agent` fornisce metriche al host. Monitoring stack: Prometheus + libvirt-exporter + Grafana. Proxmox ha monitoring integrato nella web UI.

**Q13: Cosa fare se una VM è compromessa?**
1) Isolare immediatamente la VM dalla rete (staccare interfaccia o spostare su rete isolata), 2) Non spegnerla se serve analisi forense della memoria, 3) Snapshot per preservare lo stato, 4) Analisi dei log (`/var/log/libvirt/qemu/`), 5) Verificare che l'host non sia compromesso, 6) Ricostruire la VM da backup pulito dopo l'analisi.

**Q14: Come posso ridurre la dimensione di un file qcow2?**
Un qcow2 in thin provisioning non rilascia spazio automaticamente. 1) Nel guest: `fstrim -a` (TRIM) o `dd if=/dev/zero of=/tmp/zero bs=1M; rm /tmp/zero`, 2) Sull'host: `qemu-img convert -O qcow2 disk.qcow2 disk_compacted.qcow2` oppure `virt-sparsify disk.qcow2 disk_sparse.qcow2`.

**Q15: Posso eseguire macOS in una VM KVM?**
Tecnicamente possibile con il progetto OSX-KVM, ma viola l'EULA Apple a meno che l'hardware host sia Apple (Mac Pro, Mac Mini). Apple permette la virtualizzazione di macOS solo su hardware Apple. Per CI/CD macOS: considerare servizi cloud Apple-hosted (MacStadium, AWS EC2 Mac).

**Q16: Come gestisco il time drift nelle VM?**
Configurare chrony o systemd-timesyncd nel guest. Nel domain XML: `<clock offset='utc'>` con timer `rtc tickpolicy='catchup'`. Installare qemu-guest-agent per sincronizzazione host-guest. Per Windows: usare il timer hypervisor-aware (`<timer name='hypervclock' present='yes'/>`).

**Q17: Qual è il limite di dischi collegabili a una VM?**
VirtIO-blk: fino a 28 dischi (vda-vdz + vdaa, vdab). VirtIO-SCSI: fino a ~16000 dischi per controller (più pratico: multipli controller SCSI). IDE: max 4 (obsoleto). Per VM con molti dischi, usare sempre virtio-scsi.

**Q18: Come faccio il resize del disco di una VM in esecuzione?**
1) Estendere il file qcow2: `qemu-img resize disk.qcow2 +20G`, 2) Notificare la VM: `virsh blockresize vm_name /path/to/disk.qcow2 70G`, 3) Nel guest: `growpart /dev/vda 2 && resize2fs /dev/vda2` (ext4) o `growpart /dev/vda 2 && xfs_growfs /` (XFS). Per LVM nel guest: `pvresize /dev/vda2 && lvextend -l +100%FREE /dev/mapper/vg-lv && resize2fs /dev/mapper/vg-lv`.
