# Architettura e Installazione di Proxmox VE

Guida tecnica completa all'architettura, ai requisiti hardware, all'installazione e alla
configurazione post-installazione di Proxmox Virtual Environment per ambienti di produzione.

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 1 — Fondamenti · Modulo 02.1 (gemello speculare di 01.1, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 01.1 (architettura vSphere/ESXi) per il confronto; conoscenza Linux solida (filesystem, systemd, package APT, networking ifupdown2/iproute2); LVM concettuale.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. descrivere lo stack tecnologico Proxmox VE (Debian → kernel PVE → KVM/QEMU + LXC + Corosync → API + Web UI) e contrastarlo con il microkernel proprietario ESXi;
> 2. dimensionare l'hardware di un nodo o di un cluster Proxmox per workload realistici (PMI, mid-market, enterprise) tenendo conto di memoria/cpu/storage backing/rete dedicata;
> 3. installare Proxmox VE da ISO ufficiale (verifica SHA-256 inclusa), scegliendo correttamente fra ext4, XFS e ZFS RAID al momento dell'installazione;
> 4. completare la configurazione post-installazione critica: rete (bridge, VLAN, bonding), repository APT (no-subscription vs enterprise), aggiornamenti sicuri, storage backend principali;
> 5. costruire un cluster Proxmox a 3 nodi e leggere lo stato di Corosync (quorum, link, transport knet);
> 6. gestire il modello di licensing Proxmox (Community vs Standard vs Premium) e capire l'effetto pratico della scelta sul ciclo aggiornamenti.
> **Tempo stimato:** lettura 90-120 min · lab 180-240 min (installazione e cluster a 3 nodi)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** Proxmox VE 8.x (kernel 6.x); per i delta in **Proxmox VE 9.x** (rilasciato 2025-11-19) vedi callout «Approfondimento — Proxmox VE 9.x» in fondo al modulo.

## Mappa concettuale

```
+======================================================+
|  Proxmox VE — vista d'insieme del modulo             |
+======================================================+
|                                                      |
|   USER LAYER                                         |
|   +--------------+  +-----------+  +--------------+ |
|   | Web UI :8006 |  | REST API  |  | CLI: qm/pct/ | |
|   |  (pveproxy)  |  |  (pveproxy|  |  pvesh/pvecm | |
|   +-------+------+  | /api2)    |  +------+-------+ |
|           |         +-----+-----+         |         |
|           +-----+---------+---------------+         |
|                 v                                   |
|   ORCHESTRATOR LAYER                                |
|   +-------------+  +-------------+  +-----------+   |
|   | pvedaemon   |  | pveproxy    |  | pmxcfs    |   |
|   |  (RPC)      |  |  (HTTPS)    |  |  (FUSE on |   |
|   |             |  |             |  |  Corosync)|   |
|   +------+------+  +------+------+  +-----+-----+   |
|          |                |                 |       |
|          v                v                 v       |
|   COMPUTE / CLUSTER LAYER                           |
|   +-----------+  +-----------+  +---------------+   |
|   | QEMU/KVM  |  | LXC       |  | Corosync +    |   |
|   |  (qm,VM)  |  |  (pct,CT) |  |  pve-ha-mgr   |   |
|   +-----+-----+  +-----+-----+  +-------+-------+   |
|         |              |                |           |
|         v              v                v           |
|   KERNEL LAYER                                      |
|   +------------------------------------------+      |
|   | pve-kernel (Linux 6.x + KVM + ZFS +      |      |
|   | AppArmor + patch PVE)                    |      |
|   +------------------------------------------+      |
|                                                      |
|   STORAGE PLUGIN LAYER                              |
|   +---------+ +---------+ +-------+ +---------+     |
|   |  dir    | | LVM /   | |  ZFS  | | NFS /   |     |
|   |         | | LVM-Thin| |       | | CIFS /  |     |
|   |         | |         | | BTRFS | | iSCSI / |     |
|   |         | |         | |       | | RBD/CephFS|   |
|   +---------+ +---------+ +-------+ +---------+     |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **Proxmox VE e Debian con un kernel speciale.** Tutto il resto (cluster, GUI, storage plugin) e Perl + sistemd + Linux conventionali. Diversamente da ESXi non c'e nulla di proprietario "sotto". Per debugging e troubleshooting, ogni strumento Linux e disponibile (`strace`, `bpftrace`, `dmesg`, `journalctl`, ecc.).
2. **`pmxcfs` e l'invenzione chiave.** E un filesystem distribuito (FUSE) montato in `/etc/pve` che usa Corosync come transport e SQLite come backing locale. Garantisce che la configurazione del cluster sia coerente su tutti i nodi *e* leggibile/scrivibile come file di testo. Senza quorum, `/etc/pve` diventa **read-only** (e questa e la prima diagnosi che un operatore deve fare quando "non posso piu modificare nulla").
3. **Il cluster non protegge da solo le VM.** Corosync + pmxcfs garantiscono solo *coerenza configurativa*. La protezione operativa (riavvio VM su altro nodo) la da `pve-ha-manager` con il fencing. La differenza e netta: cluster funzionante ≠ HA configurata.
4. **Il modello licenza non blocca le feature.** Tutte le funzionalita sono disponibili anche con la repo no-subscription. La differenza fra Community Subscription e le edizioni Standard/Premium e nei *repo* (test/no-subscription vs enterprise) e nel supporto. Per produzione critica, abbonarsi e una scelta operativa, non funzionale.
5. **L'installazione "default" e gia produttiva.** ext4 + LVM-Thin sul disco principale, `pve-no-subscription` repo, network bridge `vmbr0` su `eno1` — sono scelte ragionevoli che non vanno demolite alla prima installazione. Ottimizzare dopo aver capito i workload.

---

## Indice

1. Architettura Proxmox VE
2. Requisiti Hardware
3. Installazione
4. Configurazione di Rete Post-Installazione
5. Storage Configuration
6. Gestione Licenze e Repository

---

## 1. Architettura Proxmox VE

### 1.1 Panoramica del Stack Tecnologico

Proxmox VE e una piattaforma di virtualizzazione open-source di tipo 1 (bare-metal)
costruita su una base Debian GNU/Linux stabile. A differenza di VMware ESXi, che utilizza
un microkernel proprietario (VMkernel), Proxmox VE opera su un sistema operativo Linux
completo, offrendo accesso diretto a tutto l'ecosistema di strumenti e pacchetti Debian.

```
+------------------------------------------------------------------+
|                     PROXMOX VE - STACK ARCHITETTURALE            |
+------------------------------------------------------------------+
|                                                                  |
|  +-------------------+  +-------------------+  +--------------+  |
|  |   Web UI (8006)   |  |   API REST (443)  |  |   CLI Tools  |  |
|  |   pveproxy        |  |   pveproxy/API2   |  |  qm/pct/pvesh|  |
|  +--------+----------+  +--------+----------+  +------+-------+  |
|           |                      |                     |          |
|           +----------+-----------+---------------------+          |
|                      |                                            |
|           +----------v-----------+                                |
|           |   PVE API Daemon     |                                |
|           |   (pvedaemon)        |                                |
|           +----------+-----------+                                |
|                      |                                            |
|     +----------------+------------------+                         |
|     |                |                  |                         |
|  +--v---+      +-----v------+    +------v-------+                 |
|  | QEMU |      |    LXC     |    |  Corosync    |                 |
|  | /KVM |      | Container  |    |  + pve-ha    |                 |
|  +--+---+      |  Engine    |    |  (Cluster)   |                 |
|     |          +-----+------+    +--------------+                 |
|     |                |                                            |
|  +--v----------------v------------------------------------------+ |
|  |              PVE Kernel (pve-kernel)                         | |
|  |         Linux Kernel con patch specifiche PVE                | |
|  |         KVM module + ZFS module + AppArmor                   | |
|  +--------------------------------------------------------------+ |
|                                                                  |
|  +--------------------------------------------------------------+ |
|  |              Hardware (CPU, RAM, Storage, NIC)                | |
|  +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
```

### 1.2 Base Debian

Proxmox VE e costruito su Debian stable (attualmente Debian 12 Bookworm per PVE 8.x).
Questo significa che:

- Il sistema di pacchetti e APT (dpkg/apt-get/apt)
- La struttura del filesystem segue lo standard FHS di Debian
- Tutti i pacchetti Debian standard sono disponibili
- Il sistema init e systemd
- I tool di rete sono quelli standard Debian (ifupdown2, iproute2)

La scelta di Debian come base offre stabilita a lungo termine, ampio supporto hardware
e un ecosistema di pacchetti maturo. Rispetto a ESXi, dove l'installazione di software
aggiuntivo richiede VIB e procedure complesse, su Proxmox VE basta un `apt install`.

### 1.3 Kernel PVE (pve-kernel)

Proxmox utilizza un kernel Linux custom basato sulla versione Ubuntu HWE (Hardware
Enablement) con patch aggiuntive:

| Componente              | Dettaglio                                         |
|-------------------------|---------------------------------------------------|
| Base kernel             | Linux kernel (serie 6.x per PVE 8.x)             |
| Moduli KVM              | kvm, kvm_intel, kvm_amd precaricati               |
| ZFS                     | OpenZFS integrato nel kernel (non DKMS)           |
| AppArmor                | Profili di sicurezza per container LXC            |
| Patch aggiuntive        | Fix specifici per virtualizzazione e storage      |
| Firma                   | Kernel firmato per Secure Boot (opzionale)        |

Verificare la versione del kernel:

```bash
# Versione kernel attuale
uname -r
# Output esempio: 6.8.12-5-pve

# Kernel PVE disponibili
apt list --installed 2>/dev/null | grep pve-kernel

# Informazioni dettagliate moduli KVM
lsmod | grep kvm
# kvm_intel   xxxxx  0
# kvm         xxxxx  1 kvm_intel
```

### 1.4 KVM Hypervisor

KVM (Kernel-based Virtual Machine) e il modulo del kernel Linux che trasforma il sistema
in un hypervisor di tipo 1. QEMU lavora in coppia con KVM per fornire l'emulazione
hardware completa.

Differenze chiave rispetto a VMware:

| Aspetto                 | VMware ESXi              | Proxmox VE (KVM/QEMU)     |
|-------------------------|--------------------------|----------------------------|
| Hypervisor type         | Tipo 1 (microkernel)     | Tipo 1 (kernel Linux)      |
| Emulazione HW           | Proprietaria             | QEMU (open-source)         |
| CPU virtualization      | VMware HV                | KVM (kernel module)        |
| Paravirtualizzazione    | VMware Tools / PVSCSI    | VirtIO drivers             |
| Format disco            | VMDK                     | raw, qcow2, vmdk           |
| Licenza                 | Proprietaria             | AGPL v3 + sottoscrizioni   |
| GPU passthrough         | vDGA / vSGA / vGPU       | VFIO / IOMMU               |
| Live migration          | vMotion                  | Online Migration           |

### 1.5 LXC Container Engine

Proxmox VE integra nativamente il supporto per container Linux (LXC), offrendo una
virtualizzazione leggera a livello di sistema operativo. I container condividono il kernel
dell'host ma hanno filesystem, processi e stack di rete isolati.

```
   VM (KVM/QEMU)                    Container (LXC)
+------------------+            +------------------+
| App   App   App  |            | App   App   App  |
+------------------+            +------------------+
| Guest OS Kernel  |            | (Shared Kernel)  |
+------------------+            |                  |
| Virtual Hardware |            | cgroups/namespaces|
+------------------+            +------------------+
| QEMU + KVM       |            | LXC Runtime      |
+------------------+            +------------------+
| Host Kernel      |            | Host Kernel       |
+------------------+            +------------------+
```

Gestione container tramite CLI:

```bash
# Elenco container
pct list

# Stato di un container
pct status 100

# Configurazione container
pct config 100

# Start/stop
pct start 100
pct stop 100
pct shutdown 100
```

### 1.6 Corosync e Cluster Communication

Corosync e il layer di comunicazione cluster in Proxmox VE. Gestisce la membership dei
nodi, il quorum e la messaggistica tra i nodi del cluster.

```
+----------+          Corosync           +----------+
|  Node 1  | <-------(multicast/-------> |  Node 2  |
| pve-node1|          unicast)           | pve-node2|
+----+-----+                            +----+-----+
     |              +----------+              |
     +------------> |  Node 3  | <------------+
                    | pve-node3|
                    +----------+
                         |
                    Quorum: 2/3
                    (maggioranza)
```

Componenti cluster:

| Servizio        | Porta  | Funzione                                       |
|-----------------|--------|------------------------------------------------|
| Corosync        | 5405   | Comunicazione cluster, quorum                  |
| pve-cluster     | -      | pmxcfs (Proxmox Cluster File System)           |
| pve-ha-manager  | -      | High Availability manager                      |
| pve-ha-lrm      | -      | Local Resource Manager per HA                  |

Comandi cluster essenziali:

```bash
# Stato cluster
pvecm status

# Nodi nel cluster
pvecm nodes

# Quorum attuale
pvecm expected 1    # ATTENZIONE: solo in emergenza

# Informazioni dettagliate
pvecm status -v
```

### 1.7 Web UI e pveproxy

L'interfaccia web di Proxmox VE e accessibile sulla porta 8006 (HTTPS) ed e servita
dal daemon pveproxy. Questa interfaccia consente la gestione completa dell'infrastruttura:
VM, container, storage, rete, cluster, backup.

```
Browser (https://pve-host:8006)
        |
        v
+-------+--------+
|    pveproxy     |  (Porta 8006, TLS)
|  (web server)   |
+-------+--------+
        |
        v
+-------+--------+
|   PVE API2     |  (Framework Perl ExtJS-based)
|   /api2/json   |
+-------+--------+
        |
        v
+-------+--------+
|  pvedaemon     |  (Backend privilegiato)
+----------------+
```

### 1.8 API REST

L'API REST di Proxmox VE e completa e documentata. Ogni operazione disponibile nella
web UI e accessibile anche tramite API. L'autenticazione avviene tramite ticket o
API token.

```bash
# Ottenere un ticket di autenticazione
curl -k -d "username=root@pam&password=YOURPASSWORD" \
    https://pve-host:8006/api2/json/access/ticket

# Usare pvesh (CLI wrapper per API)
pvesh get /nodes
pvesh get /nodes/pve-node1/status
pvesh get /cluster/resources --type vm

# Creare un API token
pvesh create /access/users/root@pam/token/mytoken \
    --privsep 0

# Elenco storage disponibili
pvesh get /nodes/pve-node1/storage

# Elenco VM su un nodo
pvesh get /nodes/pve-node1/qemu
```

### 1.9 CLI Tools (qm, pct, pvesh, pvesm)

Proxmox VE fornisce tool CLI specializzati per ogni componente:

| Tool     | Funzione                         | Esempio                          |
|----------|----------------------------------|----------------------------------|
| qm       | Gestione VM KVM                  | `qm list`, `qm start 100`       |
| pct      | Gestione container LXC           | `pct list`, `pct start 200`     |
| pvesh    | Interfaccia CLI per API REST     | `pvesh get /nodes`               |
| pvesm    | Gestione storage                 | `pvesm status`, `pvesm list`     |
| pvecm    | Gestione cluster                 | `pvecm status`                   |
| ha-manager| Gestione High Availability      | `ha-manager status`              |
| vzdump   | Backup VM e container            | `vzdump 100 --mode snapshot`     |
| qmrestore| Restore backup VM                | `qmrestore backup.vma 100`      |
| pveam    | Gestione template                | `pveam available`                |
| pveum    | Gestione utenti e permessi       | `pveum user list`                |
| pvenode  | Operazioni nodo                  | `pvenode cert info`              |

### 1.10 Licenza e Modello di Sottoscrizione

Proxmox VE e distribuito sotto licenza GNU AGPL v3. Il codice sorgente e interamente
disponibile. Il modello commerciale si basa su sottoscrizioni opzionali che forniscono
accesso al repository enterprise stabile e supporto tecnico.

```
+------------------------------------------------------------------+
|              MODELLO LICENZA PROXMOX VE                          |
+------------------------------------------------------------------+
|                                                                  |
|  +--------------------+    +----------------------------------+  |
|  | Open Source (AGPL)  |    | Sottoscrizione (opzionale)      |  |
|  |                    |    |                                  |  |
|  | - Codice completo  |    | - Repository Enterprise         |  |
|  | - Tutte le funzioni|    | - Supporto tecnico              |  |
|  | - No limiti VM     |    | - Aggiornamenti testati         |  |
|  | - Community repo   |    | - Accesso Customer Portal       |  |
|  +--------------------+    +----------------------------------+  |
|                                                                  |
+------------------------------------------------------------------+
```

Tier di sottoscrizione (per socket CPU, per anno):

| Tier        | Supporto            | Tempo Risposta  | Note                         |
|-------------|---------------------|-----------------|------------------------------|
| Community   | Solo community      | N/A             | Gratuito, repo no-subscription|
| Basic       | Business hours      | 1 giorno lav.   | Accesso repo enterprise      |
| Standard    | Business hours      | 4 ore lav.      | Report bug prioritario       |
| Premium     | 24/7                | 1 ora           | Accesso remoto, consulenza   |

Importante: tutte le funzionalita sono identiche indipendentemente dal tier.
La sottoscrizione non sblocca funzionalita aggiuntive, fornisce solo supporto
e accesso al repository enterprise (con pacchetti piu testati e stabili).

---

## 2. Requisiti Hardware

### 2.1 Processore (CPU)

La virtualizzazione hardware e un requisito obbligatorio. Senza le estensioni VT-x
(Intel) o AMD-V (AMD), KVM non puo funzionare e Proxmox VE operera solo con
container LXC.

| Requisito                | Minimo                    | Consigliato                  |
|--------------------------|---------------------------|------------------------------|
| Architettura             | x86_64 (64-bit)           | x86_64 (64-bit)             |
| Virtualizzazione HW      | VT-x o AMD-V             | VT-x / AMD-V + EPT/RVI     |
| IOMMU                    | Non richiesto             | VT-d / AMD-Vi (passthrough) |
| Core                     | 2 core                   | 8+ core per host produzione |
| Generazione              | -                         | Intel Xeon Scalable / EPYC  |
| AES-NI                   | Non richiesto             | Consigliato (encryption)    |

Verificare il supporto alla virtualizzazione:

```bash
# Verificare VT-x / AMD-V
grep -E '(vmx|svm)' /proc/cpuinfo | head -1

# Verificare IOMMU
dmesg | grep -i -e DMAR -e IOMMU

# Numero di core e thread
lscpu | grep -E '^(CPU\(s\)|Thread|Core|Socket)'

# Flag CPU rilevanti
grep -o -E '(vmx|svm|ept|vpid|npt|lm|aes)' /proc/cpuinfo | sort -u

# Verificare AES-NI
grep aes /proc/cpuinfo | head -1
```

### 2.2 IOMMU per GPU/Device Passthrough

Per passare dispositivi fisici direttamente alle VM (GPU, controller RAID, NIC),
IOMMU deve essere abilitato nel BIOS/UEFI e nel kernel.

```bash
# Abilitare IOMMU nel GRUB (Intel)
# Modificare /etc/default/grub:
GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt"

# Abilitare IOMMU nel GRUB (AMD)
GRUB_CMDLINE_LINUX_DEFAULT="quiet amd_iommu=on iommu=pt"

# Aggiornare GRUB
update-grub

# Riavviare e verificare
dmesg | grep -e DMAR -e IOMMU
# Output atteso: DMAR: IOMMU enabled

# Verificare gruppi IOMMU
find /sys/kernel/iommu_groups/ -maxdepth 3 -type l | \
    sort -t '/' -k 5 -n
```

### 2.3 Memoria RAM

| Requisito                | Minimo                    | Consigliato                  |
|--------------------------|---------------------------|------------------------------|
| RAM totale               | 2 GB                      | 64+ GB per produzione       |
| Tipo                     | DDR4                      | DDR4/DDR5 ECC               |
| Per host Proxmox OS      | ~1 GB                     | 2-4 GB riservati per OS     |
| Per Ceph (se usato)      | +2 GB per OSD             | +4 GB per OSD               |
| Per ZFS (se usato)       | +1 GB per TB di storage   | +2 GB per TB (ARC cache)    |

Nota critica su ECC: la RAM ECC (Error-Correcting Code) e fortemente consigliata
per ambienti di produzione, specialmente con ZFS. ZFS mantiene dati in cache nella
RAM (ARC) e corruzione della RAM puo propagarsi ai dati su disco.

```bash
# Verificare se la RAM e ECC
dmidecode -t memory | grep -i "error correction"
# Output: Error Correction Type: Multi-bit ECC

# Memoria totale e disponibile
free -h

# Dettaglio DIMM installate
dmidecode -t memory | grep -E '(Size|Type|Speed|Locator):' | \
    grep -v "No Module"
```

### 2.4 Storage

| Componente               | Minimo                    | Consigliato                  |
|--------------------------|---------------------------|------------------------------|
| Boot drive               | 32 GB                     | 128+ GB SSD/NVMe            |
| VM storage               | Dipende dal carico        | NVMe SSD per prestazioni    |
| Backup storage           | Dipende dalla retention   | HDD o NAS dedicato          |
| Ceph OSD                 | SSD da 100+ GB per OSD   | NVMe dedicati per Ceph      |

Layout disco consigliato:

```
+------------------------------------------------------------------+
|              LAYOUT STORAGE CONSIGLIATO                          |
+------------------------------------------------------------------+
|                                                                  |
|  Boot Drive (SSD/NVMe 128+ GB)                                  |
|  +----------------------------------------------------------+   |
|  | / (root)   | /var/log | swap | LVM-Thin per VM locali    |   |
|  | 30 GB      | 10 GB   | 8 GB | resto                     |   |
|  +----------------------------------------------------------+   |
|                                                                  |
|  VM Storage (NVMe SSD pool)                                     |
|  +----------------------------------------------------------+   |
|  | ZFS Mirror o RAID-Z1 per storage VM ad alte prestazioni   |   |
|  +----------------------------------------------------------+   |
|                                                                  |
|  Backup Storage (HDD o NAS)                                     |
|  +----------------------------------------------------------+   |
|  | NFS/CIFS share o HDD locali per backup vzdump             |   |
|  +----------------------------------------------------------+   |
|                                                                  |
+------------------------------------------------------------------+
```

### 2.5 Rete

| Interfaccia              | Funzione                  | Banda Minima                 |
|--------------------------|---------------------------|------------------------------|
| NIC 1 (management)       | Web UI, API, SSH          | 1 Gbps                      |
| NIC 2 (VM traffic)       | Traffico VM               | 1-10 Gbps                   |
| NIC 3 (storage)          | Ceph, NFS, iSCSI          | 10+ Gbps                    |
| NIC 4 (Corosync)         | Cluster communication     | 1 Gbps (dedicato)           |

```
+------------------------------------------------------------------+
|              SCHEMA RETE CONSIGLIATO                             |
+------------------------------------------------------------------+
|                                                                  |
|  +--------+   +--------+   +--------+   +--------+              |
|  | NIC 1  |   | NIC 2  |   | NIC 3  |   | NIC 4  |             |
|  | eno1   |   | eno2   |   | ens1f0 |   | ens1f1 |             |
|  +---+----+   +---+----+   +---+----+   +---+----+             |
|      |            |            |            |                    |
|  +---v----+   +---v----+   +---v----+   +---v----+              |
|  | vmbr0  |   | vmbr1  |   | bond0  |   |Corosync|             |
|  | Mgmt   |   | VM Net |   | Storage|   | Link   |             |
|  | Bridge |   | Bridge |   | Bond   |   |        |             |
|  +--------+   +--------+   +--------+   +--------+             |
|  10.0.0.x     VLAN trunk   10.10.0.x    Link-local             |
|                                                                  |
+------------------------------------------------------------------+
```

### 2.6 Impostazioni BIOS/UEFI

Impostazioni obbligatorie e consigliate nel BIOS/UEFI:

| Impostazione             | Valore                    | Note                         |
|--------------------------|---------------------------|------------------------------|
| Intel VT-x / AMD-V       | Enabled                  | Obbligatorio per KVM         |
| Intel VT-d / AMD-Vi      | Enabled                  | Obbligatorio per passthrough |
| Intel EPT / AMD RVI      | Enabled                  | Prestazioni memoria guest    |
| ACS Override             | Enabled (se disponibile) | Separazione gruppi IOMMU     |
| UEFI Boot                | Enabled                  | Consigliato per Secure Boot  |
| Hyper-Threading          | Enabled                  | Consigliato per densita VM   |
| C-States                 | Disabled o limitati      | Latenza prevedibile          |
| Turbo Boost              | Enabled                  | Prestazioni singolo core     |
| SR-IOV                   | Enabled (se supportato)  | Virtual Function NIC         |
| Boot da USB              | Enabled (per install)    | Temporaneo per installazione |

---

## 3. Installazione

### 3.1 Download e Verifica ISO

Scaricare l'ISO ufficiale dal sito Proxmox e verificarne l'integrita:

```bash
# Download ISO (esempio per PVE 8.x)
wget https://www.proxmox.com/en/downloads/proxmox-virtual-environment/iso

# Verificare checksum SHA256
sha256sum proxmox-ve_8.x-x.iso
# Confrontare con il valore pubblicato sul sito ufficiale

# Verificare firma GPG
wget https://www.proxmox.com/en/downloads/proxmox-virtual-environment/iso/sha256sums.asc
gpg --verify sha256sums.asc

# Creare USB bootable (Linux)
dd bs=1M conv=fdatasync if=proxmox-ve_8.x-x.iso of=/dev/sdX status=progress

# Creare USB bootable (alternativa con Etcher o Ventoy)
# Ventoy e consigliato: supporta multiple ISO sulla stessa USB
```

### 3.2 Installazione Step-by-Step

Il processo di installazione di Proxmox VE e guidato da un wizard grafico:

```
+------------------------------------------------------------------+
|              FLUSSO INSTALLAZIONE PROXMOX VE                     |
+------------------------------------------------------------------+
|                                                                  |
|  1. Boot da USB/DVD                                              |
|     |                                                            |
|     v                                                            |
|  2. Selezionare "Install Proxmox VE (Graphical)"                |
|     |                                                            |
|     v                                                            |
|  3. Accettare EULA                                               |
|     |                                                            |
|     v                                                            |
|  4. Selezionare disco di destinazione                            |
|     +---> Opzioni avanzate disco (ext4, xfs, ZFS, Btrfs)        |
|     |     +---> ZFS RAID level (single, mirror, RAID10,          |
|     |     |     RAIDZ-1, RAIDZ-2, RAIDZ-3)                      |
|     |     +---> hdsize, swapsize, maxroot, maxvz, minfree        |
|     |                                                            |
|     v                                                            |
|  5. Paese, timezone, layout tastiera                             |
|     |                                                            |
|     v                                                            |
|  6. Password root e email amministratore                         |
|     |                                                            |
|     v                                                            |
|  7. Configurazione rete                                          |
|     +---> Management interface                                   |
|     +---> Hostname (FQDN)                                        |
|     +---> IP address (statico)                                   |
|     +---> Gateway                                                |
|     +---> DNS server                                             |
|     |                                                            |
|     v                                                            |
|  8. Riepilogo e conferma                                         |
|     |                                                            |
|     v                                                            |
|  9. Installazione e reboot                                       |
|                                                                  |
+------------------------------------------------------------------+
```

### 3.3 Opzioni Disco ZFS durante l'Installazione

Se si seleziona ZFS come filesystem, il wizard offre opzioni avanzate:

| Parametro    | Default      | Descrizione                                      |
|--------------|--------------|--------------------------------------------------|
| hdsize       | Intero disco | Dimensione totale utilizzata dal disco            |
| swapsize     | 8 GB         | Dimensione partizione swap                       |
| maxroot      | Illimitato   | Dimensione massima filesystem root               |
| maxvz        | Illimitato   | Dimensione massima per dati (local-lvm)          |
| minfree      | 16 GB        | Spazio libero minimo (ZFS necessita spazio libero)|
| compress     | on (lz4)     | Compressione ZFS                                 |
| checksum     | on           | Verifica integrita dati                          |
| ashift       | 12           | Allineamento settore (12 = 4K, 13 = 8K)         |

Livelli RAID ZFS disponibili:

| RAID Level   | Dischi Minimi | Ridondanza       | Capacita Utilizzabile        |
|--------------|---------------|-------------------|------------------------------|
| single       | 1             | Nessuna           | 100%                         |
| mirror       | 2             | 1 disco           | 50%                          |
| RAID10       | 4             | 1 per mirror      | 50%                          |
| RAIDZ-1      | 3             | 1 disco           | (N-1)/N                      |
| RAIDZ-2      | 4             | 2 dischi          | (N-2)/N                      |
| RAIDZ-3      | 5             | 3 dischi          | (N-3)/N                      |

### 3.4 Post-Installazione: Repository

Dopo l'installazione, configurare i repository APT e correttamente la priorita
e il primo passo fondamentale.

```bash
# ============================================================
# CONFIGURAZIONE REPOSITORY PER UTENTI SENZA SOTTOSCRIZIONE
# ============================================================

# 1. Disabilitare il repository enterprise (richiede sottoscrizione)
mv /etc/apt/sources.list.d/pve-enterprise.list \
   /etc/apt/sources.list.d/pve-enterprise.list.disabled

# In alternativa, commentare la riga:
# deb https://enterprise.proxmox.com/debian/pve bookworm pve-enterprise

# 2. Aggiungere il repository no-subscription
cat > /etc/apt/sources.list.d/pve-no-subscription.list << 'EOF'
deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription
EOF

# 3. Verificare il repository Debian base
cat /etc/apt/sources.list
# Deve contenere:
# deb http://ftp.debian.org/debian bookworm main contrib
# deb http://ftp.debian.org/debian bookworm-updates main contrib
# deb http://security.debian.org/debian-security bookworm-security main contrib

# 4. Aggiornare il sistema
apt update && apt full-upgrade -y

# 5. Riavviare se il kernel e stato aggiornato
# Verificare:
pveversion -v
```

Per utenti con sottoscrizione enterprise:

```bash
# ============================================================
# CONFIGURAZIONE REPOSITORY PER UTENTI CON SOTTOSCRIZIONE
# ============================================================

# Il repository enterprise e gia configurato in:
# /etc/apt/sources.list.d/pve-enterprise.list

# Verificare che contenga:
# deb https://enterprise.proxmox.com/debian/pve bookworm pve-enterprise

# Configurare la chiave di sottoscrizione tramite web UI:
# Datacenter -> Subscription -> Upload Key

# Aggiornare
apt update && apt full-upgrade -y
```

### 3.5 Post-Installazione: Primo Accesso

```bash
# Accedere alla web UI
# Browser: https://<IP-ADDRESS>:8006
# Username: root
# Realm: Linux PAM standard realm

# Rimuovere popup sottoscrizione (opzionale, solo no-subscription)
# Questo popup appare ad ogni login se non si ha una sottoscrizione attiva
# E un semplice avviso, non limita funzionalita

# Verificare stato del sistema
pveversion -v
# Output esempio:
# proxmox-ve: 8.x.x
# pve-manager: 8.x.x
# pve-kernel: 6.x.x-x-pve
# qemu-server: 8.x.x
# lxc-pve: 6.x.x

# Verificare servizi
systemctl status pvedaemon
systemctl status pveproxy
systemctl status pve-cluster
```

### 3.6 Certificato SSL

Proxmox VE genera un certificato self-signed durante l'installazione. Per produzione
e consigliato configurare un certificato valido:

```bash
# Opzione 1: Let's Encrypt (ACME) tramite web UI
# Datacenter -> ACME -> Register Account
# Node -> Certificates -> ACME -> Add Domain -> Order Certificate

# Opzione 2: Let's Encrypt via CLI
pvenode acme account register default \
    mail@example.com --directory https://acme-v02.api.letsencrypt.org/directory

pvenode config set --acme domains=pve.example.com
pvenode acme cert order

# Opzione 3: Certificato custom
# Caricare tramite web UI: Node -> Certificates -> Upload Custom Certificate
# Oppure copiare manualmente:
cp custom.pem /etc/pve/local/pveproxy-ssl.pem
cp custom.key /etc/pve/local/pveproxy-ssl.key
systemctl restart pveproxy

# Verificare certificato attuale
pvenode cert info
openssl x509 -in /etc/pve/local/pveproxy-ssl.pem -text -noout | \
    grep -E '(Subject|Issuer|Not After)'
```

---

## 4. Configurazione di Rete Post-Installazione

### 4.1 File di Configurazione Principale

La configurazione di rete in Proxmox VE e gestita tramite il file standard Debian
`/etc/network/interfaces`. Proxmox utilizza `ifupdown2` che supporta il reload
della configurazione senza reboot.

```bash
# Configurazione di rete di default dopo installazione
cat /etc/network/interfaces
```

Esempio di configurazione base:

```
# /etc/network/interfaces
auto lo
iface lo inet loopback

# Interfaccia fisica (non configurata direttamente)
iface eno1 inet manual

# Bridge per management e VM
auto vmbr0
iface vmbr0 inet static
    address 10.0.0.10/24
    gateway 10.0.0.1
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
```

### 4.2 Bridge Configuration (vmbr0, vmbr1, ...)

I bridge Linux sono l'equivalente dei vSwitch di VMware. Ogni bridge connette
interfacce fisiche e interfacce virtuali delle VM/container.

```
+------------------------------------------------------------------+
|              BRIDGE NETWORKING                                   |
+------------------------------------------------------------------+
|                                                                  |
|  +--------+   +--------+   +--------+                            |
|  | VM 100 |   | VM 101 |   | CT 200 |                           |
|  | vnet0  |   | vnet0  |   | eth0   |                           |
|  +---+----+   +---+----+   +---+----+                            |
|      |            |            |                                  |
|  +---v------------v------------v----+                             |
|  |           vmbr0 (bridge)         |                             |
|  +---+------------------------------+                             |
|      |                                                            |
|  +---v----+                                                       |
|  |  eno1  |  (interfaccia fisica)                                |
|  +--------+                                                       |
|      |                                                            |
|  [Switch fisico / Rete]                                          |
|                                                                  |
+------------------------------------------------------------------+
```

Aggiungere un secondo bridge per rete VM dedicata:

```
# Secondo bridge su interfaccia fisica separata
auto vmbr1
iface vmbr1 inet manual
    bridge-ports eno2
    bridge-stp off
    bridge-fd 0

# Bridge interno (senza interfaccia fisica, solo VM-to-VM)
auto vmbr2
iface vmbr2 inet manual
    bridge-ports none
    bridge-stp off
    bridge-fd 0
```

### 4.3 Bonding (Link Aggregation)

Il bonding combina multiple interfacce fisiche per ridondanza e/o throughput:

```
# Bonding LACP (802.3ad) con bridge
auto bond0
iface bond0 inet manual
    bond-slaves eno1 eno2
    bond-miimon 100
    bond-mode 802.3ad
    bond-xmit-hash-policy layer3+4

auto vmbr0
iface vmbr0 inet static
    address 10.0.0.10/24
    gateway 10.0.0.1
    bridge-ports bond0
    bridge-stp off
    bridge-fd 0
```

Modi di bonding disponibili:

| Modo           | Nome                | Richiede Switch Config | Uso Tipico             |
|----------------|---------------------|------------------------|------------------------|
| balance-rr (0) | Round-robin          | No                     | Test                   |
| active-backup (1)| Active-backup      | No                     | Ridondanza semplice    |
| balance-xor (2)| XOR                 | No                     | Bilanciamento base     |
| broadcast (3)  | Broadcast            | No                     | Fault tolerance        |
| 802.3ad (4)    | LACP                 | Si (LACP)              | Produzione consigliato |
| balance-tlb (5)| Adaptive TX LB       | No                     | Bilanciamento TX       |
| balance-alb (6)| Adaptive LB          | No                     | Bilanciamento TX+RX    |

### 4.4 VLAN Configuration

Le VLAN permettono di segmentare il traffico di rete sullo stesso bridge:

```
# Opzione 1: VLAN-aware bridge (consigliato)
auto vmbr0
iface vmbr0 inet static
    address 10.0.0.10/24
    gateway 10.0.0.1
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 2-4094

# Con VLAN-aware bridge, le VLAN si assegnano direttamente
# nella configurazione VM/container (tag VLAN nella scheda di rete)
```

```
# Opzione 2: VLAN tradizionale (interfaccia VLAN separata)
auto eno1.100
iface eno1.100 inet manual

auto vmbr100
iface vmbr100 inet static
    address 10.100.0.10/24
    bridge-ports eno1.100
    bridge-stp off
    bridge-fd 0
```

Confronto approcci VLAN:

| Aspetto                  | VLAN-aware bridge       | VLAN tradizionale        |
|--------------------------|-------------------------|--------------------------|
| Scalabilita              | Alta (un bridge)        | Bassa (un bridge/VLAN)   |
| Configurazione           | Semplificata            | Verbosa                  |
| Assegnazione VLAN        | Per-VM nella config VM  | Per-bridge               |
| Trunk support            | Nativo                  | Manuale                  |
| Compatibilita OVS        | No (alternativa)        | No (alternativa)         |
| Consigliato              | Si                      | Solo casi legacy         |

### 4.5 IPv4 e IPv6

```
# Dual-stack IPv4 + IPv6
auto vmbr0
iface vmbr0 inet static
    address 10.0.0.10/24
    gateway 10.0.0.1
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0

iface vmbr0 inet6 static
    address 2001:db8::10/64
    gateway 2001:db8::1
```

### 4.6 Gestione DNS

```bash
# DNS e configurato in /etc/resolv.conf
# Ma in Proxmox e gestito tramite /etc/hosts e web UI

# Verificare configurazione DNS
cat /etc/resolv.conf
# search example.com
# nameserver 10.0.0.1

# Il file /etc/hosts deve contenere il FQDN corretto
cat /etc/hosts
# 10.0.0.10 pve-node1.example.com pve-node1

# ATTENZIONE: Non usare 127.0.1.1 per il hostname
# Proxmox richiede che il hostname risolva all'IP reale del nodo
```

### 4.7 Open vSwitch come Alternativa

Open vSwitch (OVS) e un'alternativa ai bridge Linux standard, utile per
configurazioni di rete complesse, SDN e integrazione con sistemi di
orchestrazione:

```bash
# Installare Open vSwitch
apt install openvswitch-switch

# Esempio configurazione OVS in /etc/network/interfaces
auto vmbr0
iface vmbr0 inet static
    address 10.0.0.10/24
    gateway 10.0.0.1
    ovs_type OVSBridge
    ovs_ports eno1
    up ovs-vsctl set Bridge vmbr0 stp_enable=false

allow-vmbr0 eno1
iface eno1 inet manual
    ovs_bridge vmbr0
    ovs_type OVSPort
```

### 4.8 Applicare Modifiche di Rete

```bash
# Con ifupdown2 (default in Proxmox VE 7+)
# Reload senza reboot:
ifreload -a

# Verificare configurazione attiva
ip addr show
ip route show
bridge link show

# Controllare stato bridge
brctl show      # Legacy
bridge link     # Moderno

# Test connettivita
ping -c 3 gateway_ip
```

---

## 5. Storage Configuration

### 5.1 Panoramica Storage in Proxmox VE

Proxmox VE supporta un'ampia varieta di backend storage, sia locali che condivisi.
Lo storage e gestito tramite il file `/etc/pve/storage.cfg` e il tool `pvesm`.

```
+------------------------------------------------------------------+
|              TIPI DI STORAGE PROXMOX VE                          |
+------------------------------------------------------------------+
|                                                                  |
|  LOCALE                          CONDIVISO                       |
|  +----------------------+        +----------------------+        |
|  | Directory (dir)      |        | NFS                  |        |
|  | LVM                  |        | CIFS/SMB             |        |
|  | LVM-Thin             |        | iSCSI                |        |
|  | ZFS (local)          |        | iSCSI + LVM          |        |
|  | ZFS over iSCSI       |        | Ceph RBD             |        |
|  | BTRFS                |        | CephFS               |        |
|  +----------------------+        | GlusterFS            |        |
|                                  | Proxmox Backup Server|        |
|                                  +----------------------+        |
|                                                                  |
+------------------------------------------------------------------+
```

### 5.2 Storage Content Types

Ogni storage puo contenere diversi tipi di contenuto. La configurazione
determina quali tipi sono abilitati per ciascun storage:

| Content Type | Codice     | Descrizione                                    |
|--------------|------------|------------------------------------------------|
| Disk images  | images     | Immagini disco VM (raw, qcow2, vmdk)           |
| ISO images   | iso        | File ISO per installazione OS                  |
| Container    | rootdir    | Root filesystem per container LXC              |
| Templates    | vztmpl     | Template per container LXC                     |
| Backups      | backup     | File backup vzdump                             |
| Snippets     | snippets   | File ausiliari (cloud-init, hook scripts)      |

Compatibilita storage/content:

| Storage Type | images | iso | rootdir | vztmpl | backup | snippets |
|-------------|--------|-----|---------|--------|--------|----------|
| Directory   |   X    |  X  |    X    |   X    |   X    |    X     |
| LVM         |   X    |     |    X    |        |        |          |
| LVM-Thin    |   X    |     |    X    |        |        |          |
| ZFS         |   X    |     |    X    |        |        |          |
| NFS         |   X    |  X  |    X    |   X    |   X    |    X     |
| CIFS        |   X    |  X  |    X    |   X    |   X    |    X     |
| Ceph RBD    |   X    |     |    X    |        |        |          |
| CephFS      |   X    |  X  |    X    |   X    |   X    |    X     |
| iSCSI       |   X    |     |         |        |        |          |
| PBS         |        |     |         |        |   X    |          |

### 5.3 Storage Locale: LVM e LVM-Thin

LVM e configurato di default durante l'installazione se si sceglie ext4 o xfs
come filesystem.

```bash
# Verificare volume group esistenti
vgs
# VG        #PV #LV #SN Attr   VSize    VFree
# pve         1   3   0 wz--n- 200.00g  10.00g

# Verificare logical volume
lvs
# LV            VG  Attr       LSize
# data          pve twi-a-t--- 150.00g
# root          pve -wi-ao----  30.00g
# swap          pve -wi-ao----   8.00g

# Aggiungere un nuovo disco come LVM-Thin
# 1. Creare Physical Volume
pvcreate /dev/sdb

# 2. Creare Volume Group
vgcreate vg-storage /dev/sdb

# 3. Creare Thin Pool
lvcreate -l 100%FREE -T vg-storage/thinpool

# 4. Aggiungere a Proxmox via CLI
pvesm add lvmthin local-ssd -vgname vg-storage -thinpool thinpool \
    --content images,rootdir

# Oppure via web UI:
# Datacenter -> Storage -> Add -> LVM-Thin
```

### 5.4 Storage Locale: ZFS

ZFS e la scelta consigliata per storage locale di produzione, grazie a integrita
dati, snapshot, compressione e RAID software.

```bash
# Creare un pool ZFS mirror (dopo installazione)
zpool create -f -o ashift=12 tank mirror /dev/sdb /dev/sdc

# Creare un dataset per VM
zfs create tank/vm-data

# Abilitare compressione
zfs set compression=lz4 tank/vm-data

# Aggiungere a Proxmox
pvesm add zfspool local-zfs -pool tank/vm-data \
    --content images,rootdir

# Verificare stato pool ZFS
zpool status
zpool list

# Verificare dataset
zfs list

# Impostare quota
zfs set quota=500G tank/vm-data

# Abilitare deduplicazione (attenzione: richiede molta RAM)
# zfs set dedup=on tank/vm-data
# AVVERTENZA: la dedup richiede ~5 GB RAM per TB di dati
```

### 5.5 Storage Locale: Directory

Lo storage di tipo directory e il piu semplice: usa una directory del filesystem
per salvare file immagine, ISO, backup.

```bash
# Creare una directory storage
mkdir -p /mnt/storage/pve

# Montare un disco (se necessario)
# Aggiungere a /etc/fstab:
# /dev/sdd1  /mnt/storage  ext4  defaults  0  2

# Aggiungere a Proxmox
pvesm add dir local-dir --path /mnt/storage/pve \
    --content iso,backup,vztmpl,snippets

# Verificare
pvesm status
```

### 5.6 Storage Condiviso: NFS

NFS e la soluzione piu comune per storage condiviso tra nodi Proxmox.

```bash
# Aggiungere storage NFS
pvesm add nfs nfs-share \
    --server 10.0.0.50 \
    --export /volume1/proxmox \
    --content images,iso,backup,vztmpl,snippets \
    --options vers=3

# Verificare montaggio
pvesm status
df -h | grep nfs

# NFS v4 (se supportato dal server)
pvesm add nfs nfs4-share \
    --server 10.0.0.50 \
    --export /volume1/proxmox \
    --content images,iso,backup,vztmpl \
    --options vers=4.2
```

### 5.7 Storage Condiviso: CIFS/SMB

```bash
# Aggiungere storage CIFS
pvesm add cifs smb-share \
    --server 10.0.0.50 \
    --share proxmox \
    --username pve-user \
    --password \
    --content backup,iso,vztmpl

# Con dominio specifico
pvesm add cifs smb-share \
    --server 10.0.0.50 \
    --share proxmox \
    --username pve-user \
    --domain MYDOMAIN \
    --content backup,iso
```

### 5.8 Storage Condiviso: iSCSI

```bash
# Aggiungere target iSCSI
pvesm add iscsi iscsi-storage \
    --portal 10.10.0.50 \
    --target iqn.2024-01.com.example:pve-storage

# iSCSI con LVM sopra (per thin provisioning)
pvesm add iscsidirect iscsi-direct \
    --portal 10.10.0.50 \
    --target iqn.2024-01.com.example:pve-storage

# Verificare sessioni iSCSI
iscsiadm -m session
```

### 5.9 Storage Condiviso: Ceph RBD

Ceph e integrato nativamente in Proxmox VE e fornisce storage distribuito,
replicato e auto-riparante.

```bash
# Prerequisito: Ceph cluster configurato
# (la configurazione Ceph e trattata nel modulo Storage Avanzato)

# Aggiungere Ceph RBD pool
pvesm add rbd ceph-pool \
    --pool vm-pool \
    --content images,rootdir \
    --monhost 10.10.0.1,10.10.0.2,10.10.0.3

# Verificare
pvesm status
ceph -s
```

### 5.10 Gestione Storage via CLI

```bash
# Elenco storage configurati
pvesm status

# Output esempio:
# Name           Type     Status   Total      Used     Available  %
# local          dir      active   30.00 GB   5.22 GB  23.16 GB   17.4%
# local-lvm      lvmthin  active  150.00 GB  10.00 GB 140.00 GB    6.7%
# nfs-share      nfs      active    2.00 TB 500.00 GB   1.50 TB   24.4%

# Elenco contenuto di uno storage
pvesm list local
pvesm list local --content iso
pvesm list local-lvm --content images

# Allocare un volume
pvesm alloc local-lvm 100 vm-100-disk-0 32G

# Liberare un volume
pvesm free local-lvm:vm-100-disk-0

# Scaricare un template container
pvesm download local debian-12-standard_12.0-1_amd64.tar.zst \
    --url http://download.proxmox.com/images/system/...

# Scaricare una ISO
pvesm download local debian-12.5.0-amd64-netinst.iso \
    --url https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/...
```

### 5.11 File storage.cfg

La configurazione storage e salvata in `/etc/pve/storage.cfg`, un file
condiviso tra tutti i nodi del cluster tramite pmxcfs:

```
# /etc/pve/storage.cfg (esempio)

dir: local
    path /var/lib/vz
    content iso,vztmpl,backup,snippets
    maxfiles 3

lvmthin: local-lvm
    thinpool data
    vgname pve
    content images,rootdir

nfs: nfs-backup
    export /volume1/pve-backup
    path /mnt/pve/nfs-backup
    server 10.0.0.50
    content backup
    maxfiles 5
    options vers=3

zfspool: local-zfs
    pool tank/vm-data
    content images,rootdir
    sparse 1
```

---

## 6. Gestione Licenze e Repository

### 6.1 Panoramica Repository

Proxmox VE utilizza il sistema di pacchetti Debian APT. Esistono tre repository
principali:

```
+------------------------------------------------------------------+
|              REPOSITORY PROXMOX VE                               |
+------------------------------------------------------------------+
|                                                                  |
|  +---------------------------+                                   |
|  | pve-enterprise            |  Richiede sottoscrizione          |
|  | (enterprise.proxmox.com)  |  Pacchetti testati e stabili      |
|  | Consigliato: produzione   |  Aggiornamenti conservativi       |
|  +---------------------------+                                   |
|                                                                  |
|  +---------------------------+                                   |
|  | pve-no-subscription       |  Gratuito, nessuna sottoscrizione |
|  | (download.proxmox.com)    |  Pacchetti ragionevolmente stabili|
|  | Consigliato: homelab/test |  Aggiornamenti piu frequenti      |
|  +---------------------------+                                   |
|                                                                  |
|  +---------------------------+                                   |
|  | pvetest                   |  Gratuito, pacchetti di test       |
|  | (download.proxmox.com)    |  Non usare in produzione          |
|  | Solo per testing          |  Puo contenere bug                |
|  +---------------------------+                                   |
|                                                                  |
+------------------------------------------------------------------+
```

### 6.2 Configurazione Dettagliata Repository

```bash
# ============================================================
# REPOSITORY ENTERPRISE (richiede sottoscrizione attiva)
# ============================================================
# File: /etc/apt/sources.list.d/pve-enterprise.list
cat > /etc/apt/sources.list.d/pve-enterprise.list << 'EOF'
deb https://enterprise.proxmox.com/debian/pve bookworm pve-enterprise
EOF

# Repository Ceph enterprise (se Ceph e in uso)
cat > /etc/apt/sources.list.d/ceph.list << 'EOF'
deb https://enterprise.proxmox.com/debian/ceph-reef bookworm enterprise
EOF

# ============================================================
# REPOSITORY NO-SUBSCRIPTION (gratuito)
# ============================================================
# File: /etc/apt/sources.list.d/pve-no-subscription.list
cat > /etc/apt/sources.list.d/pve-no-subscription.list << 'EOF'
deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription
EOF

# Repository Ceph no-subscription
cat > /etc/apt/sources.list.d/ceph.list << 'EOF'
deb http://download.proxmox.com/debian/ceph-reef bookworm no-subscription
EOF

# ============================================================
# REPOSITORY TEST (solo per testing)
# ============================================================
# File: /etc/apt/sources.list.d/pvetest.list
cat > /etc/apt/sources.list.d/pvetest.list << 'EOF'
deb http://download.proxmox.com/debian/pve bookworm pvetest
EOF
```

### 6.3 Procedura di Aggiornamento

```bash
# Aggiornamento standard
apt update
apt list --upgradable
apt full-upgrade -y

# Verificare versione dopo aggiornamento
pveversion -v

# Aggiornamento con verifica pre-upgrade
# (disponibile dalla web UI: Node -> Updates -> Upgrade)

# Verificare se e necessario un reboot
# (dopo aggiornamento kernel)
if [ "$(uname -r)" != "$(ls -t /boot/vmlinuz-* | head -1 | \
    sed 's|/boot/vmlinuz-||')" ]; then
    echo "REBOOT NECESSARIO: kernel aggiornato"
else
    echo "Nessun reboot necessario"
fi

# Reboot programmato (se in cluster, migrare prima le VM)
# 1. Migrare VM dal nodo
# 2. Reboot
shutdown -r +1 "Reboot per aggiornamento kernel"
```

### 6.4 Gestione Sottoscrizione

```bash
# Verificare stato sottoscrizione via CLI
pvesubscription get

# Output se non sottoscritto:
# status: notfound
# message: There is no subscription key

# Attivare sottoscrizione via CLI
pvesubscription set YOUR-SUBSCRIPTION-KEY

# Attivare via web UI:
# Datacenter -> Subscription -> Upload Subscription Key

# Verificare validita
pvesubscription get
# status: active
# serverid: ...
# productname: Proxmox VE Standard
# regdate: 2024-01-01 00:00:00
# nextduedate: 2025-01-01 00:00:00
```

### 6.5 Confronto Tier di Sottoscrizione

| Caratteristica              | Community | Basic    | Standard | Premium  |
|-----------------------------|-----------|----------|----------|----------|
| Prezzo (per socket/anno)    | Gratuito  | ~110 EUR | ~350 EUR | ~750 EUR |
| Tutte le funzionalita       | Si        | Si       | Si       | Si       |
| Repository enterprise       | No        | Si       | Si       | Si       |
| Supporto tecnico            | Community | Si       | Si       | Si       |
| Orario supporto             | -         | Bus. hrs | Bus. hrs | 24/7     |
| Tempo risposta              | -         | 1 gg lav | 4 ore    | 1 ora    |
| Numero ticket               | -         | Illim.   | Illim.   | Illim.   |
| Accesso remoto supporto     | -         | No       | No       | Si       |
| Consulenza                  | -         | No       | No       | Si       |
| Bug report prioritario      | -         | No       | Si       | Si       |

### 6.6 Best Practice per Ambienti di Produzione

Per ambienti di produzione, le raccomandazioni sono:

1. **Sottoscrizione attiva**: almeno tier Standard per ambienti critici
2. **Repository enterprise**: pacchetti piu testati, minor rischio di regressioni
3. **Aggiornamenti pianificati**: non aggiornare in produzione senza test
4. **Finestra di manutenzione**: pianificare aggiornamenti con migrazione VM
5. **Ambiente di test**: avere un nodo/cluster di test con repository no-subscription
   per validare aggiornamenti prima di applicarli in produzione

```bash
# Workflow aggiornamento produzione consigliato:
#
# 1. Aggiornare ambiente di test (no-subscription repo)
# 2. Verificare funzionalita per 1-2 settimane
# 3. Pianificare finestra di manutenzione
# 4. Migrare VM dal nodo da aggiornare
# 5. Aggiornare il nodo (enterprise repo)
# 6. Verificare funzionalita
# 7. Migrare VM di nuovo al nodo
# 8. Ripetere per ogni nodo del cluster
```

---

## Riferimenti

- Documentazione ufficiale Proxmox VE: https://pve.proxmox.com/pve-docs/
- Wiki Proxmox: https://pve.proxmox.com/wiki/
- Forum Proxmox: https://forum.proxmox.com/
- Repository sorgente: https://git.proxmox.com/
- Proxmox VE API Reference: https://pve.proxmox.com/pve-docs/api-viewer/

---

*Documento parte della suite di documentazione per la migrazione VMware-to-Proxmox.*
*Sezione: 02-FONDAMENTI-PROXMOX-VE*

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — Proxmox VE 9.x.** Il 2025-11-19 e stato rilasciato Proxmox VE **9.1**, basato su Debian 13 «Trixie» (13.2), kernel Linux 6.17.x, QEMU 10.1.2, LXC 6.0.5, ZFS 2.3.4, Ceph «Squid» 19.2.3. Deltas significativi rispetto a 8.x rilevanti per chi pianifica una migrazione: (a) **LVM con snapshots come volume chain** (gli snapshot LVM ora vivono in un volume separato, non come overlay del LV genitore, riducendo la perdita di performance storica); (b) aggiornamento di `pveproxy` a TLS 1.3 di default; (c) cambi nei nomi delle interfacce per chi usa systemd v257; (d) Ceph Squid sostituisce Reef. Per migrazioni nuove e raccomandato pianificare direttamente su 9.x se la finestra temporale lo permette; per migrazioni in corso che usano gia 8.x, l'aggiornamento 8 → 9 e supportato e documentato sul wiki ufficiale. Riferimento: [`PVE-ROADMAP`] `https://pve.proxmox.com/wiki/Roadmap` (verificato 2026-04-26).

> **Errore comune — `bridge-vlan-aware yes` mancante.** Su un nodo con NIC singola, dimenticare `bridge-vlan-aware yes` significa che il bridge non puo gestire frame 802.1Q tagged: tutte le VM finiscono nella VLAN nativa dell'uplink. Sintomo: la VM si vede a livello L2 ma non ha gateway (perche il traffico non viene taggato verso lo switch fisico). Soluzione: aggiungere `bridge-vlan-aware yes` e `bridge-vids 2-4094` in `/etc/network/interfaces` e `ifreload -a`. Verifica: `bridge vlan show` deve listare le VLAN registrate sul bridge.

> **Caso reale — Repository enterprise senza sottoscrizione = `apt update` rotto.** Un'installazione di lab in cui non si disabilita `pve-enterprise.list` produce un errore HTTP 401 ad ogni `apt update`. Conseguenza: in produzione, se per errore si abilita la repo enterprise senza la sottoscrizione attiva, non si ricevono *piu nemmeno* gli aggiornamenti no-subscription perche `apt` interrompe in errore. Diagnosi: `cat /var/log/apt/history.log` o `journalctl -u apt-daily.service`. Best practice: scriptare la disabilitazione della repo enterprise come step 1 del provisioning automatico.

---

## Esercizi

1. **Concettuale — `pmxcfs` read-only.** Spiegare con parole proprie cosa accade in `/etc/pve` quando il cluster perde quorum, e perche e un comportamento "by design" e non un bug. *Risposta attesa:* senza quorum, la maggior parte dei nodi non puo coordinare le scritture in modo sicuro; per evitare scritture divergenti, `pmxcfs` smonta in lettura. La GUI segnala "cluster not ready - no quorum?". Si ripristina ricostituendo il quorum (riavvio dei nodi mancanti o, in emergenza, `pvecm expected 1` per forzarlo su un singolo nodo isolato).

2. **Lab — installare cluster a 3 nodi.** Installare Proxmox VE 8.2+ (o 9.1 se disponibile) su 3 host (fisici, VM annidate, o mini-PC). Configurare la rete come da §4 con bridge `vmbr0` e VLAN dedicate per management/migration/storage. Eseguire `pvecm create lab-cluster` sul primo nodo, `pvecm add 10.10.10.11` sui successivi. Verifica: `pvecm status` su ciascun nodo deve mostrare `Quorate: Yes`, `Total votes: 3`, `Expected votes: 3`. Produrre l'output e archiviare come prova milestone M1 (vedi `../00-SYLLABUS.md` §6).

3. **Scenario — installazione su 2 dischi, ZFS RAID1.** Hai 2 SSD identici da 480 GB. Argomenta in 10 righe la scelta fra (a) installare Proxmox con ZFS RAID1 sull'intero disco, (b) installare con ext4 su un solo disco e usare il secondo come storage VM separato. *Risposta attesa:* ZFS RAID1 alla installazione e robusto e ti da resilienza al disco subito, ma toglie un disco "libero" per separare gli storage; ext4+secondo disco e piu semplice e flessibile ma non protegge dal singolo guasto disco di sistema. Per produzione, ZFS RAID1 e di solito la scelta migliore; per lab, dipende dall'obiettivo dell'esercitazione (ZFS-focus → ZFS RAID1 al boot; storage management → ext4 + secondo disco).

4. **Stretch — automatizzare il provisioning.** Scrivere uno script bash che, dato un nodo Proxmox appena installato, esegua: (1) disabilitazione repo enterprise; (2) abilitazione repo no-subscription e `ceph-no-subscription` se presente; (3) `apt update && apt full-upgrade -y`; (4) installazione di tool aggiuntivi (`htop`, `tmux`, `qemu-guest-agent`, `proxmox-backup-client`); (5) configurazione di `/etc/pve` minimale (template VM se applicabile). Riferimento per i pacchetti disponibili: [`PVE-ADMIN`] capitolo "Package Repositories".

## Auto-valutazione

1. Cosa contiene `/etc/pve` e cosa lo monta? Cosa accade se Corosync smette di rispondere?
2. Differenza fra `pveproxy` e `pvedaemon` (porta, ruolo, transport).
3. Comando per verificare la versione completa del nodo Proxmox.
4. Tre tipi di storage nativi a Proxmox e per ognuno: thin provisioning si/no, snapshot si/no, shared cluster si/no.
5. Cosa fanno `qm list`, `pct list`, `pvecm status`, `pvesm status` in una frase ciascuno.
6. Perche un cluster a 2 nodi e "problematico" e quali workaround esistono (`expected_votes`, witness QDevice).
7. Cosa succede al boot di un nodo Proxmox con fencing configurato e nessun quorum disponibile?
8. Sequenza minima di comandi per disattivare la repository enterprise e abilitare la no-subscription.

(Le risposte stanno nel modulo, sezioni §1, §3, §4, §5, §6.)

## Letture primarie consigliate

- [`PVE-ADMIN`] Proxmox VE Administration Guide. https://pve.proxmox.com/pve-docs/pve-admin-guide.html — riferimento tecnico definitivo per ogni concetto del modulo.
- [`PVE-WIKI`] Proxmox VE Wiki — Main Page. https://pve.proxmox.com/wiki/Main_Page — articoli operativi e how-to.
- [`PVE-CLUSTER`] Proxmox VE Wiki — Cluster Manager. https://pve.proxmox.com/wiki/Cluster_Manager — Corosync, pmxcfs, quorum.
- [`PVE-API`] Proxmox VE API Viewer. https://pve.proxmox.com/pve-docs/api-viewer/ — API REST interattiva.
- [`PVE-ROADMAP`] Proxmox VE Roadmap. https://pve.proxmox.com/wiki/Roadmap — versioni e novita storiche.
- [`COROSYNC-DOCS`] Corosync Project. https://corosync.github.io/corosync/ — documentazione del livello cluster.
- [`KRONOSNET`] Kronosnet (knet). https://kronosnet.org/ — il transport piu recente di Corosync usato da Proxmox.
- Debian Reference (debian.org) — base distro: https://www.debian.org/doc/manuals/debian-reference/

## Collegamenti incrociati

- Modulo 01.1 — `../01-FONDAMENTI-VMWARE/architettura-vsphere-esxi.md`: il pendant VMware dello stesso strato architetturale.
- Modulo 02.2 — `gestione-vm-container-proxmox.md`: prosegue da qui — gestire VM (qm) e container (pct).
- Modulo 03.1, 03.2 — `../03-STORAGE-AVANZATO-PROXMOX/`: storage backend approfonditi (LVM, LVM-Thin, NFS, iSCSI, ZFS, Ceph).
- Modulo 04.1 — `../04-NETWORKING-AVANZATO-PROXMOX/linux-bridge-vlan-bonding.md`: networking avanzato (bridge VLAN-aware, OVS, bonding, SDN).
- Modulo 10.1 — `../10-CLUSTER-HA-PROXMOX-POST-MIGRAZIONE/ha-manager-regole-e-gruppi.md`: HA post-installazione (regole, gruppi, fencing).
- Modulo 14.1 — `../14-AUTOMAZIONE-E-INFRASTRUCTURE-AS-CODE/cloud-init-template-vm.md`: cloud-init templates per VM (provisioning industrializzato).
- Modulo 17.1 — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-cluster-proxmox.md`: troubleshooting cluster Proxmox.

## Glossario locale

| Termine | Definizione |
|---|---|
| **pve-kernel** | Kernel Linux custom Proxmox basato su Ubuntu HWE, con KVM + ZFS + AppArmor + patch PVE. |
| **pmxcfs** | Proxmox Cluster Filesystem — FUSE filesystem in `/etc/pve` con backend SQLite locale e Corosync come transport. |
| **pveproxy** | Reverse-proxy HTTPS Proxmox, espone Web UI e REST API sulla 8006/443. |
| **pvedaemon** | Demone RPC di Proxmox; orchestratore dei task locali sul nodo. |
| **pve-ha-manager** | Gestore HA: monitora le risorse, decide failover, coordina con il fencing watchdog. |
| **`qm` / `pct` / `pvesh` / `pvecm` / `pvesm`** | CLI principali: VM / container / API client / cluster manager / storage manager. |
| **VMID** | Identificativo numerico univoco di una VM o container nel cluster (range 100..999999). |
| **Corosync** | Cluster engine: membership, messaging, totem-token; trasporto knet di default. |
| **Kronosnet (knet)** | Transport multipath cifrato di Corosync (sostituisce udpu). Permette piu link Corosync con failover. |
| **Quorum** | Maggioranza assoluta `(N/2)+1` dei voti: sotto questo soglia, `pmxcfs` diventa read-only. |
| **QDevice** | Voto esterno (un host non-cluster) che funge da tie-breaker in cluster a 2 nodi. |
| **Watchdog** | Modulo del kernel (softdog o hardware iTCO/IPMI) che reboot il nodo se il pve-ha-crm non rinfresca il timeout. |
| **VAAI lato Proxmox** | Termine improprio: Proxmox non ha VAAI ma usa offload Linux nativi (BLKZEROOUT, FALLOC_FL_PUNCH_HOLE) sui plugin che li supportano. |
| **subscription / no-subscription / pvetest** | Tre repo APT principali: `pve-enterprise` (a pagamento, stable), `pve-no-subscription` (gratis, leggermente meno stabile), `pvetest` (testing branch). |
