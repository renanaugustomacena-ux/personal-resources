# Gestione VM, Container e Operazioni in Proxmox VE

Guida tecnica completa alla creazione e gestione di macchine virtuali KVM, container LXC,
snapshot, backup, template, migrazione e limiti risorse in Proxmox VE, con confronto
diretto alle operazioni equivalenti in VMware.

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 1 — Fondamenti · Modulo 02.2 (segue 02.1, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 02.1 (architettura e installazione Proxmox); conoscenza di QEMU/KVM concettuale; LXC concettuale (cgroups, namespaces).
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. creare e configurare una VM KVM via Web UI e CLI (`qm create`), scegliendo le opzioni corrette per CPU type, machine type, BIOS (SeaBIOS vs OVMF), SCSI controller, bus disco, cache mode, discard, iothread;
> 2. distinguere VM KVM da container LXC, identificando per ciascuno i casi d'uso, le limitazioni di sicurezza/isolamento e le primitive di management (`qm` vs `pct`);
> 3. operare snapshot a livello hypervisor (con consapevolezza del cost-of-snapshot in qcow2 vs ZFS) e configurare backup `vzdump` con modalita `snapshot` / `suspend` / `stop` e con compressione e crittografia opzionali;
> 4. costruire e mantenere un template VM riutilizzabile (con cloud-init injection) e gestire i clone full/linked;
> 5. eseguire migrazioni online e offline fra nodi del cluster, leggendo i tempi di copy/precopy/post-copy e diagnosticando problemi di affinity (CPU type, storage shared);
> 6. configurare limiti di risorse (CPU shares, memory ballooning, IO limits) e capire come Proxmox interagisce con i cgroups Linux v2.
> **Tempo stimato:** lettura 90-120 min · lab 240-360 min (creazione, snapshot, backup, restore, migrazione, template)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** Proxmox VE 8.x con QEMU 8.x e LXC 5.x; per QEMU 10.1 e LXC 6.0.5 in PVE 9.x vedi callout «Approfondimento».

## Mappa concettuale

```
+======================================================+
|  Operazioni quotidiane su Proxmox — VM e Container   |
+======================================================+
|                                                      |
|   CREAZIONE                                          |
|   +-----------+        +-----------+                 |
|   |  qm create|        |  pct create|                |
|   |  (KVM VM) |        |  (LXC CT)  |                |
|   +-----+-----+        +-----+-----+                 |
|         |                    |                       |
|         v                    v                       |
|   CONFIG (cpu type, bus, cache, agent, balloon...)   |
|         |                    |                       |
|         v                    v                       |
|   STORAGE BACKEND                                    |
|   +----------+ +-----------+ +-----+ +---------+     |
|   |LVM/Thin  | | qcow2 dir | | ZFS | | Ceph RBD|     |
|   +----------+ +-----------+ +-----+ +---------+     |
|         |                                            |
|         v                                            |
|   SNAPSHOT (qcow2 internal | ZFS native | LVM-Thin)  |
|         |                                            |
|         v                                            |
|   BACKUP (vzdump --mode snapshot|suspend|stop)       |
|     +--> Storage locale  /  PBS  /  NFS  /  CIFS     |
|         |                                            |
|         v                                            |
|   TEMPLATE + CLONE (full / linked) + cloud-init      |
|         |                                            |
|         v                                            |
|   MIGRAZIONE                                         |
|     - online (precopy QEMU live)                     |
|     - offline (`qm migrate <vmid> <target>`)         |
|     - tra storage diversi (`--with-local-disks`)     |
|         |                                            |
|         v                                            |
|   LIMITI                                             |
|     - CPU: shares, units, weight (cgroups)           |
|     - RAM: ballooning, hard limit                    |
|     - I/O: bps_read/write_rd, iops_total/burst       |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **VM ≠ Container, per Proxmox.** `qm` lavora su VM piene (kernel del guest, hardware emulato), `pct` su LXC (kernel condiviso con l'host, namespace + cgroup). Stesso framework di gestione, *modello di sicurezza profondamente diverso*: i container LXC unprivileged sono adeguati per molto, ma per workload non fidati o per database con disk-fence, la VM resta la scelta giusta.
2. **`cpu host` semplifica la migrazione fra nodi identici, ma non fra CPU diverse.** Imitando l'EVC di VMware, Proxmox non offre "EVC mode" automatico: per migrazione fra CPU di generazioni differenti, scegliere `kvm64` o `x86-64-v2-AES` come baseline esplicito.
3. **Snapshot non e backup. Sempre.** Lo snapshot e un'operazione interna allo storage (qcow2 internal, ZFS dataset, LVM-Thin). Non protegge da corruzione storage, ransomware sul filesystem dell'host, errori operatore tipo `qm destroy`. Il backup *deve* andare su storage *separato* (PBS, NFS off-host, S3 via tool ausiliario).
4. **`vzdump --mode snapshot` non equivale a "snapshot di VMware".** E uno snapshot QEMU live (per VM KVM) o uno snapshot ZFS/LVM-thin (a seconda dello storage), poi un dump dei contenuti. Il guest non si ferma se ha l'agent attivo (`--mode snapshot` con qemu-guest-agent → fsfreeze → consistency applicativo). Chi configura backup senza l'agent ottiene snapshot crash-consistent, non application-consistent.
5. **Migrazione online ha vincoli stretti.** CPU type *uguale o compatibile* fra source e target, storage *condiviso* o `--with-local-disks` (che copia anche il disco), versione di QEMU compatibile. Diagnosi fallita migrazione: tipicamente CPU feature flag mismatch (`-cpu host` su Skylake → Ice Lake fallisce se Source ha `--enforce`).

---

## Indice

1. Creazione e Gestione VM (KVM)
2. Gestione Disco VM
3. Container LXC
4. Snapshot e Backup
5. Template e Cloning
6. Migrazione tra Nodi
7. Risorse e Limiti
8. Confronto con VMware

---

## 1. Creazione e Gestione VM (KVM)

### 1.1 Creazione VM tramite Web UI

La creazione di una VM tramite wizard nella web UI segue un flusso a schede:

```
+------------------------------------------------------------------+
|              WIZARD CREAZIONE VM - WEB UI                        |
+------------------------------------------------------------------+
|                                                                  |
|  Tab 1: General                                                  |
|  +---> Node, VM ID, Name, Resource Pool                         |
|                                                                  |
|  Tab 2: OS                                                       |
|  +---> ISO image, Guest OS type (Linux/Windows/Other)            |
|                                                                  |
|  Tab 3: System                                                   |
|  +---> BIOS (SeaBIOS/OVMF), Machine (i440fx/q35),               |
|  |     SCSI Controller, Qemu Agent, TPM                         |
|                                                                  |
|  Tab 4: Disks                                                    |
|  +---> Storage, Disk size, Bus (VirtIO/SCSI/IDE/SATA),          |
|  |     Cache, Discard, IO Thread                                |
|                                                                  |
|  Tab 5: CPU                                                      |
|  +---> Sockets, Cores, Type (host/kvm64/x86-64-v2-AES),         |
|  |     NUMA                                                     |
|                                                                  |
|  Tab 6: Memory                                                   |
|  +---> RAM (MB), Ballooning min/max                              |
|                                                                  |
|  Tab 7: Network                                                  |
|  +---> Bridge, Model (VirtIO/e1000/vmxnet3), VLAN tag,           |
|  |     Firewall, Rate limit                                     |
|                                                                  |
|  Tab 8: Confirm                                                  |
|  +---> Riepilogo, Start after created                            |
|                                                                  |
+------------------------------------------------------------------+
```

### 1.2 Creazione VM tramite CLI (qm create)

```bash
# Creazione VM base Linux
qm create 100 \
    --name linux-server \
    --ostype l26 \
    --memory 4096 \
    --cores 2 \
    --sockets 1 \
    --cpu host \
    --net0 virtio,bridge=vmbr0 \
    --scsihw virtio-scsi-single \
    --scsi0 local-lvm:32,iothread=1,discard=on \
    --ide2 local:iso/debian-12.5.0-amd64-netinst.iso,media=cdrom \
    --boot order=scsi0\;ide2 \
    --agent 1

# Creazione VM Windows
qm create 101 \
    --name windows-server \
    --ostype win11 \
    --memory 8192 \
    --cores 4 \
    --sockets 1 \
    --cpu host \
    --bios ovmf \
    --machine q35 \
    --efidisk0 local-lvm:1,efitype=4m,pre-enrolled-keys=1 \
    --tpmstate0 local-lvm:1,version=v2.0 \
    --net0 virtio,bridge=vmbr0 \
    --scsihw virtio-scsi-single \
    --scsi0 local-lvm:64,iothread=1,discard=on \
    --ide2 local:iso/windows-server-2022.iso,media=cdrom \
    --ide3 local:iso/virtio-win.iso,media=cdrom \
    --boot order=scsi0\;ide2 \
    --agent 1

# Avviare la VM
qm start 100

# Visualizzare configurazione
qm config 100

# Elenco tutte le VM
qm list
```

### 1.3 Opzioni CPU

Il tipo di CPU determina quali istruzioni sono esposte al guest OS:

| CPU Type          | Descrizione                           | Uso Consigliato              |
|-------------------|---------------------------------------|------------------------------|
| host              | Passa tutte le flag CPU reali         | Massime prestazioni, no migr.|
| kvm64             | CPU generica 64-bit minima            | Massima compatibilita        |
| x86-64-v2         | Baseline moderna (SSE4, POPCNT)       | Bilanciamento perf/compat    |
| x86-64-v2-AES     | v2 + AES-NI                          | Consigliato per produzione   |
| x86-64-v3         | AVX2, BMI, FMA                       | Workload HPC                |
| x86-64-v4         | AVX-512                              | HPC specifico                |
| qemu64            | Legacy QEMU default                  | Compatibilita legacy         |
| Cascadelake-Server| Emula Intel Cascadelake               | Cluster Intel misto          |
| EPYC              | Emula AMD EPYC                        | Cluster AMD misto            |

```bash
# Impostare tipo CPU
qm set 100 --cpu host

# Impostare tipo CPU con flag specifiche
qm set 100 --cpu host,flags=+aes

# Verificare CPU type attuale
qm config 100 | grep cpu

# NOTA: per live migration, tutti i nodi devono avere CPU compatibili.
# Con --cpu host, la migrazione funziona solo tra CPU identiche.
# Per cluster eterogenei, usare x86-64-v2-AES o un modello specifico.
```

### 1.4 BIOS: SeaBIOS vs OVMF (UEFI)

| Aspetto                | SeaBIOS (Legacy BIOS)    | OVMF (UEFI)                 |
|------------------------|--------------------------|------------------------------|
| Boot mode              | Legacy BIOS              | UEFI                        |
| Secure Boot            | No                       | Si (con pre-enrolled-keys)  |
| TPM 2.0               | Si (emulato)             | Si (emulato)                |
| Richiesto per          | Compatibilita legacy     | Windows 11, Secure Boot     |
| Disco aggiuntivo       | No                       | Si (efidisk0)               |
| Machine type consigliato| i440fx                  | q35                         |

```bash
# VM con UEFI + Secure Boot + TPM 2.0
qm set 100 \
    --bios ovmf \
    --machine q35 \
    --efidisk0 local-lvm:1,efitype=4m,pre-enrolled-keys=1 \
    --tpmstate0 local-lvm:1,version=v2.0
```

### 1.5 Machine Type: i440fx vs q35

| Aspetto                | i440fx                   | q35                          |
|------------------------|--------------------------|------------------------------|
| Chipset emulato        | Intel 440FX (1996)       | Intel Q35 (2007)             |
| PCI                    | PCI convenzionale        | PCIe nativo                 |
| GPU passthrough        | Limitato                 | Pieno supporto              |
| Hotplug PCI            | Limitato                 | Completo                    |
| IOMMU guest            | No                       | Si                          |
| Consigliato per        | Legacy, compatibilita    | Nuove VM, passthrough       |
| Default Proxmox        | Si (fino a PVE 8.x)     | No (diventa default futuro) |

```bash
# Cambiare machine type
qm set 100 --machine q35

# ATTENZIONE: cambiare machine type su una VM esistente
# puo richiedere reinstallazione driver nel guest OS
```

### 1.6 Disk Bus Types

| Bus Type         | Driver Guest   | Prestazioni | Compatibilita | Consigliato      |
|------------------|----------------|-------------|---------------|------------------|
| VirtIO Block     | virtio-blk     | Ottima      | Linux nativo  | Linux semplice   |
| VirtIO SCSI      | virtio-scsi    | Ottima      | Linux/Windows | Produzione       |
| IDE              | Nativo         | Bassa       | Universale    | Compatibilita    |
| SATA             | AHCI           | Media       | Universale    | UEFI boot legacy |

```bash
# VirtIO SCSI con IO thread (consigliato per produzione)
qm set 100 --scsihw virtio-scsi-single
qm set 100 --scsi0 local-lvm:32,iothread=1,discard=on,ssd=1

# IDE (per compatibilita o CD-ROM)
qm set 100 --ide0 local-lvm:32

# SATA
qm set 100 --sata0 local-lvm:32
```

### 1.7 VirtIO Drivers per Windows

Le VM Windows richiedono l'installazione manuale dei driver VirtIO per ottenere
prestazioni ottimali su disco, rete e memoria (balloon).

```bash
# Scaricare ISO VirtIO drivers
wget -P /var/lib/vz/template/iso/ \
    https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso

# Durante installazione Windows:
# 1. Montare virtio-win.iso come secondo CD-ROM (ide3)
# 2. Al momento della selezione disco, cliccare "Load driver"
# 3. Navigare a: D:\vioscsi\w11\amd64\ (per SCSI)
# 4. Installare anche: D:\NetKVM\w11\amd64\ (per rete VirtIO)
# 5. Post-installazione: installare virtio-win-guest-tools.exe
#    (include QEMU Guest Agent, balloon driver, ecc.)
```

```
+------------------------------------------------------------------+
|       DRIVER VIRTIO DA INSTALLARE IN WINDOWS                    |
+------------------------------------------------------------------+
|                                                                  |
| Driver          | Percorso ISO              | Funzione           |
| ================|===========================|=================== |
| vioscsi         | vioscsi\w11\amd64         | SCSI controller    |
| NetKVM          | NetKVM\w11\amd64          | Rete VirtIO        |
| Balloon         | Balloon\w11\amd64         | Memory ballooning  |
| viostor         | viostor\w11\amd64         | Block storage      |
| vioserial       | vioserial\w11\amd64       | Serial port        |
| qxldod          | qxldod\w11\amd64          | Display (QXL)      |
| pvpanic         | pvpanic\w11\amd64         | Panic notification |
| vioinput        | vioinput\w11\amd64        | Input device       |
| viogpudo        | viogpudo\w11\amd64        | GPU (VirtIO-GPU)   |
| Guest Agent     | guest-agent\              | QEMU Agent         |
|                                                                  |
+------------------------------------------------------------------+
```

### 1.8 Cloud-Init

Cloud-init permette la configurazione automatica di VM al primo boot
(hostname, SSH keys, rete, utenti):

```bash
# Aggiungere disco cloud-init alla VM
qm set 100 --ide2 local-lvm:cloudinit

# Configurare cloud-init
qm set 100 \
    --ciuser admin \
    --cipassword $(openssl passwd -6 "password") \
    --sshkeys ~/.ssh/authorized_keys \
    --ipconfig0 ip=10.0.0.50/24,gw=10.0.0.1 \
    --nameserver 10.0.0.1 \
    --searchdomain example.com

# Rigenerare immagine cloud-init
qm cloudinit update 100

# Visualizzare configurazione cloud-init
qm cloudinit dump 100 user
qm cloudinit dump 100 network
qm cloudinit dump 100 meta
```

### 1.9 Serial Console

Per VM headless o debug senza VNC:

```bash
# Aggiungere porta seriale
qm set 100 --serial0 socket

# Connettersi alla console seriale
qm terminal 100

# Nel guest Linux, abilitare console seriale:
# systemctl enable serial-getty@ttyS0.service
# systemctl start serial-getty@ttyS0.service

# Oppure aggiungere al GRUB del guest:
# GRUB_CMDLINE_LINUX="console=tty0 console=ttyS0,115200n8"
# update-grub
```

### 1.10 QEMU Guest Agent

Il QEMU Guest Agent permette comunicazione bidirezionale tra host e guest:

```bash
# Abilitare nella configurazione VM
qm set 100 --agent 1

# Nel guest Linux:
apt install qemu-guest-agent
systemctl enable qemu-guest-agent
systemctl start qemu-guest-agent

# Nel guest Windows:
# Installare virtio-win-guest-tools.exe (include QEMU GA)

# Verificare che l'agent risponda
qm agent 100 ping

# Ottenere informazioni dal guest
qm agent 100 get-osinfo
qm agent 100 network-get-interfaces

# Freeze filesystem (per snapshot consistenti)
qm agent 100 fsfreeze-freeze
qm agent 100 fsfreeze-thaw
```

---

## 2. Gestione Disco VM

### 2.1 Formati Disco

| Formato  | Thin Provisioning | Snapshot | Prestazioni | Note                        |
|----------|-------------------|----------|-------------|-----------------------------|
| raw      | No (su dir)       | No       | Massime     | Default su LVM/ZFS          |
| qcow2    | Si                | Si       | Buone       | Default su directory/NFS    |
| vmdk     | Si                | No       | Buone       | Compatibilita VMware        |

```bash
# Verificare formato disco di una VM
qm config 100 | grep -E '(scsi|virtio|ide|sata)[0-9]'

# Output esempio:
# scsi0: local-lvm:vm-100-disk-0,iothread=1,size=32G
# ide2: local:iso/debian-12.iso,media=cdrom
```

Nota: su storage LVM-Thin e ZFS, il formato e sempre raw ma il thin provisioning
e gestito dal layer storage sottostante. Su storage directory o NFS, qcow2
e il formato consigliato per il supporto snapshot integrato.

### 2.2 Resize Disco

```bash
# Aumentare dimensione disco (solo aumento, mai riduzione)
qm resize 100 scsi0 +20G

# Impostare dimensione specifica
qm resize 100 scsi0 50G

# NOTA: dopo il resize, e necessario estendere la partizione
# e il filesystem nel guest OS:

# Linux guest (con LVM):
# pvresize /dev/sda3
# lvextend -l +100%FREE /dev/mapper/vg-root
# resize2fs /dev/mapper/vg-root       # ext4
# xfs_growfs /                         # xfs

# Linux guest (senza LVM, con GPT):
# growpart /dev/sda 3
# resize2fs /dev/sda3

# Windows guest:
# Disk Management -> Extend Volume
# Oppure: diskpart -> select volume X -> extend
```

### 2.3 Hot-Plug Disco

```bash
# Aggiungere disco a VM accesa (hot-plug)
qm set 100 --scsi1 local-lvm:10,iothread=1

# Il disco appare immediatamente nel guest OS
# Linux: lsblk mostra il nuovo disco
# Windows: Disk Management mostra nuovo disco

# Rimuovere disco a caldo (hot-unplug)
# Prima: smontare nel guest
# Poi: qm unlink 100 --idlist scsi1

# NOTA: hot-plug richiede bus VirtIO SCSI o SATA.
# IDE non supporta hot-plug.
```

### 2.4 Migrazione Disco tra Storage

```bash
# Spostare disco VM da uno storage a un altro
qm disk move 100 scsi0 target-storage

# Con eliminazione sorgente dopo la copia
qm disk move 100 scsi0 target-storage --delete 1

# Spostare a caldo (VM accesa, richiede guest agent)
qm disk move 100 scsi0 target-storage

# Verificare risultato
qm config 100 | grep scsi0
```

### 2.5 Import Disco

Importare dischi da file esterni e fondamentale nella migrazione da VMware:

```bash
# Importare un disco VMDK (da migrazione VMware)
qm disk import 100 /path/to/vmware-disk.vmdk local-lvm

# Il comando restituisce il nome del nuovo volume:
# Successfully imported disk as 'unused0:local-lvm:vm-100-disk-1'

# Collegare il disco importato alla VM
qm set 100 --scsi1 local-lvm:vm-100-disk-1

# Importare con formato specifico
qm disk import 100 /path/to/disk.vmdk local-lvm --format raw

# Importare da un'immagine qcow2
qm disk import 100 /path/to/disk.qcow2 local-zfs

# Convertire formato durante import (usando qemu-img direttamente)
qemu-img convert -f vmdk -O raw /path/to/disk.vmdk /path/to/disk.raw
qm disk import 100 /path/to/disk.raw local-lvm
```

### 2.6 Detach e Remove Disco

```bash
# Scollegare un disco (diventa "unused")
qm unlink 100 --idlist scsi1

# Il disco appare come unused nella configurazione:
# qm config 100
# unused0: local-lvm:vm-100-disk-1

# Ricollegare un disco unused
qm set 100 --scsi1 local-lvm:vm-100-disk-1

# Eliminare definitivamente un disco unused
qm set 100 --delete unused0

# Eliminare un disco e rimuovere dati
qm set 100 --delete scsi1
# oppure
pvesm free local-lvm:vm-100-disk-1
```

---

## 3. Container LXC

### 3.1 Differenze VM vs Container

```
+------------------------------------------------------------------+
|              VM (KVM) vs CONTAINER (LXC)                         |
+------------------------------------------------------------------+
|                                                                  |
|  VM KVM                           Container LXC                  |
|  +--------------------------+     +--------------------------+   |
|  | Applicazione             |     | Applicazione             |   |
|  +--------------------------+     +--------------------------+   |
|  | Librerie / Runtime       |     | Librerie / Runtime       |   |
|  +--------------------------+     +--------------------------+   |
|  | Guest OS completo        |     | (Nessun kernel guest)    |   |
|  | (kernel proprio)         |     |                          |   |
|  +--------------------------+     +--------------------------+   |
|  | Hardware virtuale        |     | Namespace + cgroups      |   |
|  | (QEMU emulazione)        |     | (isolamento kernel host) |   |
|  +--------------------------+     +--------------------------+   |
|  | KVM (kernel module)       |     | LXC runtime              |   |
|  +--------------------------+     +--------------------------+   |
|  | Host Kernel              |     | Host Kernel (condiviso)  |   |
|  +--------------------------+     +--------------------------+   |
|                                                                  |
+------------------------------------------------------------------+
```

| Aspetto                | VM KVM                    | Container LXC                |
|------------------------|---------------------------|------------------------------|
| Isolamento             | Forte (hardware virtuale) | Medio (namespace kernel)     |
| Overhead                | Maggiore (~2-5% CPU)     | Minimo (~1%)                 |
| Startup time           | 10-60 secondi             | 1-3 secondi                  |
| RAM overhead           | Kernel guest + overhead   | Solo processi                |
| Kernel                 | Proprio (qualsiasi OS)    | Condiviso con host           |
| OS supportati          | Linux, Windows, BSD, ...  | Solo Linux                   |
| Snapshot               | Live + offline            | Offline (o con freeze)       |
| Live migration         | Si                        | Si (con limitazioni)         |
| GPU passthrough        | Si (VFIO)                 | Limitato                     |
| Docker dentro          | Si (nativo)               | Si (nesting)                 |
| Sicurezza              | Elevata                   | Buona (unprivileged)         |

### 3.2 Download Template

```bash
# Elenco template disponibili
pveam available

# Filtrare per distribuzione
pveam available --section system | grep debian
pveam available --section system | grep ubuntu
pveam available --section system | grep alpine

# Scaricare template
pveam download local debian-12-standard_12.7-1_amd64.tar.zst

# Elenco template scaricati
pveam list local

# Aggiornare elenco template disponibili
pveam update
```

### 3.3 Creazione Container

```bash
# Container unprivileged (consigliato per sicurezza)
pct create 200 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
    --hostname debian-ct \
    --memory 2048 \
    --swap 512 \
    --cores 2 \
    --rootfs local-lvm:8 \
    --net0 name=eth0,bridge=vmbr0,ip=10.0.0.200/24,gw=10.0.0.1 \
    --nameserver 10.0.0.1 \
    --searchdomain example.com \
    --password \
    --unprivileged 1 \
    --features nesting=1 \
    --start 1

# Container privileged (necessario per alcuni casi speciali)
pct create 201 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
    --hostname privileged-ct \
    --memory 4096 \
    --cores 4 \
    --rootfs local-lvm:16 \
    --net0 name=eth0,bridge=vmbr0,ip=dhcp \
    --unprivileged 0 \
    --start 1
```

### 3.4 Privileged vs Unprivileged Container

| Aspetto                 | Privileged               | Unprivileged               |
|-------------------------|--------------------------|----------------------------|
| UID mapping             | root=0 (reale)           | root=100000 (mappato)      |
| Sicurezza               | Minore (root reale)      | Maggiore (root mappato)    |
| Accesso hardware        | Completo                 | Limitato                   |
| NFS mount               | Si                       | Problematico (UID mapping) |
| Docker/nesting          | Si                       | Si (con nesting=1)         |
| Default consigliato     | No                       | Si                         |
| Escape risk             | Maggiore                 | Minore                     |

```bash
# Verificare se un container e privileged o unprivileged
pct config 200 | grep unprivileged
# unprivileged: 1   -> unprivileged
# unprivileged: 0   -> privileged (o assente = privileged)
```

### 3.5 Configurazione Risorse Container

```bash
# Modificare risorse
pct set 200 --memory 4096
pct set 200 --swap 1024
pct set 200 --cores 4

# Aggiungere mount point
pct set 200 --mp0 local-lvm:10,mp=/data

# Mount point bind (directory host -> container)
pct set 200 --mp1 /mnt/host-data,mp=/shared,ro=1

# Configurazione rete
pct set 200 --net0 name=eth0,bridge=vmbr0,ip=10.0.0.200/24,gw=10.0.0.1
pct set 200 --net1 name=eth1,bridge=vmbr1,ip=10.1.0.200/24

# DNS
pct set 200 --nameserver "10.0.0.1 10.0.0.2"
pct set 200 --searchdomain example.com
```

### 3.6 Nesting e FUSE

Nesting permette di eseguire container dentro container (utile per Docker):

```bash
# Abilitare nesting
pct set 200 --features nesting=1

# Abilitare FUSE (per mount filesystem in userspace)
pct set 200 --features nesting=1,fuse=1

# Abilitare keyctl (necessario per alcuni software)
pct set 200 --features nesting=1,keyctl=1

# Docker in container LXC unprivileged:
# 1. Abilitare nesting
pct set 200 --features nesting=1

# 2. Dentro il container:
# apt install docker.io
# systemctl enable docker
# systemctl start docker
# docker run hello-world
```

### 3.7 Operazioni Container

```bash
# Start / Stop / Restart
pct start 200
pct stop 200          # Forza stop
pct shutdown 200      # Shutdown graceful
pct reboot 200

# Accesso console
pct enter 200         # Shell diretta
pct console 200       # Console login

# Eseguire comando nel container
pct exec 200 -- apt update
pct exec 200 -- ls -la /

# Push/Pull file
pct push 200 /local/file /container/path
pct pull 200 /container/path /local/file

# Stato
pct status 200

# Configurazione
pct config 200

# Elenco container
pct list
```

---

## 4. Snapshot e Backup

### 4.1 Snapshot

Gli snapshot catturano lo stato di una VM o container in un punto nel tempo.

```
+------------------------------------------------------------------+
|              SNAPSHOT: CATENA DIPENDENZE                          |
+------------------------------------------------------------------+
|                                                                  |
|  [Base Image]                                                    |
|       |                                                          |
|       +---> [Snapshot 1: "pre-update"]                           |
|       |          |                                                |
|       |          +---> [Snapshot 2: "post-update"]               |
|       |          |          |                                     |
|       |          |          +---> [Current State]                |
|       |          |                                                |
|       |          +---> (alternativo se rollback a snap 1)        |
|       |                                                          |
+------------------------------------------------------------------+
```

```bash
# ============================================================
# SNAPSHOT VM (KVM)
# ============================================================

# Creare snapshot (VM accesa - live snapshot)
qm snapshot 100 pre-update --description "Prima dell'aggiornamento OS"

# Creare snapshot con inclusione RAM (VM state)
qm snapshot 100 pre-update --vmstate 1 \
    --description "Stato completo con RAM"

# Elenco snapshot
qm listsnapshot 100

# Output esempio:
# `-> pre-update            (Prima dell'aggiornamento OS)
#   `-> post-update         (Dopo aggiornamento riuscito)
#     `-> current           (Stato attuale)

# Rollback a snapshot
qm rollback 100 pre-update
# ATTENZIONE: il rollback elimina tutti gli snapshot successivi

# Eliminare snapshot
qm delsnapshot 100 post-update

# ============================================================
# SNAPSHOT CONTAINER (LXC)
# ============================================================

# Creare snapshot container (container fermo o con freeze)
pct snapshot 200 pre-update --description "Prima aggiornamento"

# Elenco snapshot
pct listsnapshot 200

# Rollback
pct rollback 200 pre-update

# Eliminare snapshot
pct delsnapshot 200 pre-update
```

Nota: gli snapshot live su storage LVM-Thin o ZFS sono quasi istantanei
grazie al copy-on-write. Su storage directory con qcow2, la catena di
snapshot puo degradare le prestazioni I/O.

### 4.2 Backup con vzdump

vzdump e il tool di backup integrato in Proxmox VE. Supporta tre modalita:

| Modalita  | VM Accesa | Consistenza      | Downtime | Descrizione                  |
|-----------|-----------|------------------|----------|------------------------------|
| stop      | No        | Massima          | Si       | Spegne VM, backup, riaccende |
| suspend   | Parziale  | Buona            | Breve    | Sospende RAM, backup, resume |
| snapshot  | Si        | Buona (con agent)| No       | Snapshot live, backup in bg  |

```bash
# Backup in modalita snapshot (consigliata per produzione)
vzdump 100 --mode snapshot --storage nfs-backup \
    --compress zstd --notes-template "Backup giornaliero"

# Backup in modalita stop
vzdump 100 --mode stop --storage nfs-backup --compress zstd

# Backup container
vzdump 200 --mode snapshot --storage nfs-backup --compress zstd

# Backup multipli
vzdump 100 101 102 200 201 --mode snapshot \
    --storage nfs-backup --compress zstd --mailto admin@example.com

# Backup di tutte le VM/container del nodo
vzdump --all --mode snapshot --storage nfs-backup \
    --compress zstd --mailnotification failure

# Opzioni di compressione:
# --compress 0      (nessuna compressione)
# --compress gzip   (lenta, buona compressione)
# --compress lzo    (veloce, compressione media)
# --compress zstd   (veloce, buona compressione - consigliato)
```

### 4.3 Restore

```bash
# Restore VM da backup
qmrestore /mnt/pve/nfs-backup/dump/vzdump-qemu-100-*.vma.zst 100

# Restore con nuovo VMID
qmrestore /mnt/pve/nfs-backup/dump/vzdump-qemu-100-*.vma.zst 150

# Restore su storage specifico
qmrestore /mnt/pve/nfs-backup/dump/vzdump-qemu-100-*.vma.zst 100 \
    --storage local-lvm

# Restore container
pct restore 200 /mnt/pve/nfs-backup/dump/vzdump-lxc-200-*.tar.zst

# Restore con nuovo VMID e storage
pct restore 250 /mnt/pve/nfs-backup/dump/vzdump-lxc-200-*.tar.zst \
    --storage local-lvm

# Restore sovrascrivendo VM esistente
qmrestore /mnt/pve/nfs-backup/dump/vzdump-qemu-100-*.vma.zst 100 --force
```

### 4.4 Scheduling Backup

I backup schedulati si configurano tramite web UI o file di configurazione:

```bash
# File di configurazione backup schedulato
# /etc/pve/jobs.cfg

# Esempio contenuto:
# vzdump: backup-daily
#     enabled 1
#     schedule daily
#     storage nfs-backup
#     mailnotification failure
#     mailto admin@example.com
#     mode snapshot
#     compress zstd
#     all 1
#     exclude 999
#     notes-template {{guestname}} - Backup giornaliero

# Tramite web UI:
# Datacenter -> Backup -> Add
# Selezionare: schedule, storage, mode, VM/container, retention

# Retention policy (quanti backup mantenere):
# --prune-backups keep-daily=7,keep-weekly=4,keep-monthly=6

# Esempio backup schedulato via vzdump con cron
# (alternativa al sistema integrato)
# /etc/cron.d/vzdump-schedule
# 0 2 * * * root vzdump --all --mode snapshot \
#     --storage nfs-backup --compress zstd \
#     --prune-backups keep-daily=7,keep-weekly=4,keep-monthly=3 \
#     --mailto admin@example.com --mailnotification failure
```

### 4.5 Storage per Backup

```bash
# Proxmox Backup Server (PBS) - soluzione dedicata consigliata
pvesm add pbs pbs-storage \
    --server 10.0.0.60 \
    --datastore main \
    --username backup@pbs \
    --password \
    --content backup \
    --fingerprint AA:BB:CC:...

# Vantaggi PBS rispetto a vzdump su NFS:
# - Deduplicazione incrementale
# - Verifica integrita backup
# - Encryption
# - Garbage collection
# - Supporto prune avanzato
# - Restore singoli file da backup
```

---

## 5. Template e Cloning

### 5.1 Convertire VM in Template

Un template e una VM immutabile usata come base per creare cloni:

```bash
# Prerequisiti:
# 1. VM spenta
# 2. Rimuovere configurazioni specifiche (IP, hostname, SSH keys)
# 3. Nel guest Linux: eseguire cleanup
#    - apt clean
#    - truncate -s 0 /etc/machine-id
#    - rm -f /etc/ssh/ssh_host_*
#    - cloud-init clean (se installato)
#    - history -c

# Convertire VM in template
qm template 100

# NOTA: la conversione e irreversibile tramite CLI.
# La VM diventa read-only e non puo piu essere avviata direttamente.
# I dischi vengono convertiti in formato base (read-only).

# Verificare
qm config 100
# template: 1
```

### 5.2 Linked Clone vs Full Clone

```
+------------------------------------------------------------------+
|              LINKED CLONE vs FULL CLONE                          |
+------------------------------------------------------------------+
|                                                                  |
|  LINKED CLONE                    FULL CLONE                      |
|  +--------------------+         +--------------------+           |
|  | Clone VM           |         | Clone VM           |           |
|  | (delta changes)    |         | (copia completa)   |           |
|  +--------+-----------+         +--------------------+           |
|           |                              |                       |
|           v                              v                       |
|  +--------+-----------+         +--------------------+           |
|  | Template           |         | Disco indipendente |           |
|  | (base, read-only)  |         | (nessuna dipendenza)|          |
|  +--------------------+         +--------------------+           |
|                                                                  |
|  Vantaggi:                      Vantaggi:                        |
|  - Creazione istantanea         - Indipendenza completa          |
|  - Spazio disco minimo          - Migrabile liberamente          |
|  - Efficiente per molti cloni   - Nessuna dipendenza template    |
|                                                                  |
|  Svantaggi:                     Svantaggi:                       |
|  - Dipende dal template         - Tempo di creazione lungo       |
|  - Non migrabile facilmente     - Spazio disco completo          |
|  - Template non eliminabile     - Meno efficiente per molti cloni|
|                                                                  |
+------------------------------------------------------------------+
```

```bash
# Full clone da template
qm clone 100 110 --name cloned-vm --full

# Linked clone da template
qm clone 100 111 --name linked-vm

# Full clone con storage di destinazione specifico
qm clone 100 112 --name full-clone --full --storage local-zfs

# Clone con nuova configurazione
qm clone 100 113 --name custom-clone --full
qm set 113 --memory 8192 --cores 4
qm set 113 --ipconfig0 ip=10.0.0.113/24,gw=10.0.0.1

# Clone container
pct clone 200 210 --hostname cloned-ct --full
pct clone 200 211 --hostname linked-ct
```

### 5.3 Cloud-Init Template

Workflow consigliato per creare template cloud-init:

```bash
# 1. Scaricare immagine cloud (esempio: Debian cloud)
wget https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.qcow2

# 2. Creare VM
qm create 9000 --name debian12-cloud-template \
    --ostype l26 \
    --memory 2048 \
    --cores 2 \
    --cpu host \
    --net0 virtio,bridge=vmbr0 \
    --scsihw virtio-scsi-single \
    --agent 1

# 3. Importare disco cloud
qm disk import 9000 debian-12-generic-amd64.qcow2 local-lvm

# 4. Collegare disco
qm set 9000 --scsi0 local-lvm:vm-9000-disk-0,discard=on,iothread=1

# 5. Aggiungere disco cloud-init
qm set 9000 --ide2 local-lvm:cloudinit

# 6. Configurare boot
qm set 9000 --boot order=scsi0

# 7. Configurare cloud-init defaults
qm set 9000 \
    --ciuser admin \
    --sshkeys ~/.ssh/id_ed25519.pub \
    --ipconfig0 ip=dhcp

# 8. Convertire in template
qm template 9000

# 9. Clonare e personalizzare
qm clone 9000 120 --name prod-server --full
qm set 120 --ipconfig0 ip=10.0.0.120/24,gw=10.0.0.1
qm set 120 --memory 4096 --cores 4
qm start 120
```

### 5.4 Automazione con Packer

Packer (HashiCorp) puo automatizzare la creazione di template Proxmox:

```bash
# Installare Packer
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o \
    /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
    https://apt.releases.hashicorp.com bookworm main" > \
    /etc/apt/sources.list.d/hashicorp.list
apt update && apt install packer

# Esempio file Packer HCL (debian-template.pkr.hcl):
#
# source "proxmox-iso" "debian" {
#   proxmox_url              = "https://pve:8006/api2/json"
#   username                 = "root@pam"
#   password                 = "password"
#   node                     = "pve-node1"
#   iso_file                 = "local:iso/debian-12.iso"
#   iso_checksum             = "sha256:..."
#   vm_id                    = 9001
#   vm_name                  = "debian12-packer"
#   template_description     = "Debian 12 template built by Packer"
#   os                       = "l26"
#   memory                   = 2048
#   cores                    = 2
#   cpu_type                 = "host"
#   scsi_controller          = "virtio-scsi-single"
#   disks {
#     type         = "scsi"
#     disk_size    = "20G"
#     storage_pool = "local-lvm"
#   }
#   network_adapters {
#     bridge = "vmbr0"
#     model  = "virtio"
#   }
#   cloud_init              = true
#   cloud_init_storage_pool = "local-lvm"
#
#   boot_command = ["..."]
#   ssh_username = "root"
#   ssh_password = "packer"
#   ssh_timeout  = "20m"
# }
#
# build {
#   sources = ["source.proxmox-iso.debian"]
#   provisioner "shell" {
#     inline = [
#       "apt-get update",
#       "apt-get install -y qemu-guest-agent cloud-init",
#       "systemctl enable qemu-guest-agent",
#       "cloud-init clean",
#     ]
#   }
# }

# Eseguire Packer
# packer init .
# packer build debian-template.pkr.hcl
```

---

## 6. Migrazione tra Nodi

### 6.1 Live Migration (Online)

La live migration sposta una VM accesa da un nodo all'altro senza downtime
percepibile (equivalente a VMware vMotion):

```
+------------------------------------------------------------------+
|              LIVE MIGRATION                                      |
+------------------------------------------------------------------+
|                                                                  |
|  Nodo Sorgente                    Nodo Destinazione              |
|  +-----------------+              +-----------------+            |
|  | VM 100 (running)|  =========>  | VM 100 (running)|           |
|  |                 |  1. Copia RAM|                 |            |
|  |                 |  2. Iterativa|                 |            |
|  |                 |  3. Switch   |                 |            |
|  +-----------------+              +-----------------+            |
|         |                                |                       |
|  +------v------+                  +------v------+                |
|  | Storage     |                  | Storage     |                |
|  | (shared o   |  <============>  | (shared o   |                |
|  |  locale)    |  Storage migr.   |  locale)    |                |
|  +-------------+                  +-------------+                |
|                                                                  |
+------------------------------------------------------------------+
```

Requisiti per live migration:

| Requisito                 | Obbligatorio | Note                              |
|---------------------------|--------------|-----------------------------------|
| Cluster configurato       | Si           | Nodi nello stesso cluster PVE     |
| CPU compatibile           | Si           | Stesso vendor, compatibilita flag |
| Rete tra nodi             | Si           | Bassa latenza, alta banda         |
| Storage condiviso         | No*          | *Con local storage: migra anche i dischi |
| Stessa versione PVE       | Consigliato  | Versioni diverse possono fallire  |
| Bridge di rete identici   | Si           | Stesso nome bridge su entrambi    |
| QEMU Guest Agent          | Consigliato  | Per freeze filesystem             |

```bash
# Migrazione live (storage condiviso)
qm migrate 100 pve-node2 --online

# Migrazione live con storage locale (migra anche dischi)
qm migrate 100 pve-node2 --online --with-local-disks \
    --targetstorage local-lvm

# Verificare stato migrazione
# La web UI mostra il progresso in tempo reale
# Via CLI, il comando qm migrate mostra output dettagliato

# Migrazione container live
pct migrate 200 pve-node2 --online
# NOTA: la migrazione live container richiede che il container
# usi storage condiviso o il flag --restart per riavvio rapido
```

### 6.2 Offline Migration

```bash
# Migrazione offline VM (VM spenta)
qm migrate 100 pve-node2

# Migrazione offline con target storage
qm migrate 100 pve-node2 --targetstorage local-zfs

# Migrazione offline container
pct migrate 200 pve-node2

# La migrazione offline e piu semplice e affidabile:
# - Non richiede storage condiviso
# - Non richiede CPU compatibile
# - Funziona sempre se i nodi sono nel cluster
```

### 6.3 Storage Migration (senza cambio nodo)

```bash
# Spostare tutti i dischi di una VM su altro storage (stesso nodo)
# Usare qm disk move per ogni disco

qm disk move 100 scsi0 local-zfs
qm disk move 100 scsi1 local-zfs
qm disk move 100 efidisk0 local-zfs

# Oppure, per spostare una VM su altro nodo con cambio storage:
qm migrate 100 pve-node2 --targetstorage local-zfs --online \
    --with-local-disks
```

### 6.4 Requisiti e Troubleshooting Migrazione

```bash
# Verificare compatibilita CPU tra nodi
# Sul nodo sorgente:
grep -m1 'model name' /proc/cpuinfo
grep -o -E '(vmx|svm|sse4|avx|aes)' /proc/cpuinfo | sort -u

# Sul nodo destinazione (stesso comando)
# I flag CPU del destinazione devono essere un superset del sorgente
# (quando si usa --cpu host)

# Verificare connettivita cluster
pvecm status
pvecm nodes

# Verificare che i bridge di rete esistano sul nodo destinazione
ssh pve-node2 'cat /etc/network/interfaces | grep "auto vmbr"'

# Verificare storage disponibile sul nodo destinazione
pvesh get /nodes/pve-node2/storage --content images

# Errori comuni:
# - "can't migrate VM with local disks" -> usare --with-local-disks
# - "CPU model not supported" -> usare CPU type non-host
# - "bridge vmbr1 not found" -> creare bridge sul target
# - "not enough memory" -> liberare RAM sul target
```

---

## 7. Risorse e Limiti

### 7.1 CPU Limits

Proxmox VE offre controllo granulare sull'allocazione CPU:

| Parametro   | Descrizione                          | Default | Esempio               |
|-------------|--------------------------------------|---------|-----------------------|
| sockets     | Numero socket CPU virtuali           | 1       | `--sockets 2`         |
| cores       | Core per socket                      | 1       | `--cores 4`           |
| vcpus       | vCPU attive (hotplug)                | =cores  | `--vcpus 2`           |
| cpulimit    | Limite utilizzo CPU (0=no limit)     | 0       | `--cpulimit 2`        |
| cpuunits    | Peso relativo scheduling CPU         | 1024    | `--cpuunits 2048`     |

```bash
# Esempio: VM con 4 core ma limitata a max 2 CPU fisiche
qm set 100 --cores 4 --cpulimit 2

# La VM vede 4 core ma non puo usare piu di 200% CPU totale
# (equivalente a 2 core fisici al 100%)

# Peso relativo: VM con cpuunits=2048 ottiene il doppio di CPU
# rispetto a una VM con cpuunits=1024 quando c'e contesa
qm set 100 --cpuunits 2048
qm set 101 --cpuunits 1024

# vCPU hotplug: avviare con 2 vCPU, espandere fino a 8
qm set 100 --cores 8 --vcpus 2
# Poi nel guest: echo 1 > /sys/devices/system/cpu/cpu2/online
# Oppure dalla web UI: aumentare vcpus
```

```
+------------------------------------------------------------------+
|              CPU ALLOCATION EXAMPLE                              |
+------------------------------------------------------------------+
|                                                                  |
|  Host fisico: 16 core                                            |
|                                                                  |
|  VM 100: cores=4, cpulimit=2, cpuunits=2048                     |
|  +----+----+----+----+                                           |
|  | C0 | C1 | C2 | C3 |  <-- 4 core visibili                    |
|  +----+----+----+----+      ma max 2 core fisici usabili        |
|                              peso doppio in contesa              |
|                                                                  |
|  VM 101: cores=2, cpulimit=0, cpuunits=1024                     |
|  +----+----+                                                     |
|  | C0 | C1 |  <-- 2 core, nessun limite                         |
|  +----+----+      peso standard in contesa                      |
|                                                                  |
|  VM 102: cores=8, cpulimit=4, cpuunits=1024                     |
|  +----+----+----+----+----+----+----+----+                       |
|  | C0 | C1 | C2 | C3 | C4 | C5 | C6 | C7 |                    |
|  +----+----+----+----+----+----+----+----+                       |
|  8 core visibili, max 4 core fisici                              |
|                                                                  |
+------------------------------------------------------------------+
```

### 7.2 Memory (Balloon)

Il memory ballooning permette allocazione dinamica della RAM:

```bash
# Memoria fissa (no ballooning)
qm set 100 --memory 8192 --balloon 0

# Memoria con ballooning
qm set 100 --memory 8192 --balloon 2048
# La VM puo usare da 2048 MB a 8192 MB
# Il balloon driver nel guest rilascia/richiede RAM dinamicamente

# Impostare memoria minima e massima
qm set 100 --memory 16384 --balloon 4096
# Max: 16 GB, Min: 4 GB

# NOTA: il ballooning richiede:
# - Linux: driver virtio_balloon (incluso nel kernel)
# - Windows: VirtIO balloon driver installato
# - QEMU Guest Agent attivo (per riport accurato)

# Per container LXC
pct set 200 --memory 4096
pct set 200 --swap 1024
```

### 7.3 Disk I/O Limits

```bash
# Limitare I/O disco (MB/s)
qm set 100 --scsi0 local-lvm:32,mbps_rd=100,mbps_wr=50

# Limitare IOPS
qm set 100 --scsi0 local-lvm:32,iops_rd=1000,iops_wr=500

# Limiti con burst
qm set 100 --scsi0 local-lvm:32,\
mbps_rd=100,mbps_rd_max=200,\
mbps_wr=50,mbps_wr_max=100,\
iops_rd=1000,iops_rd_max=2000,\
iops_wr=500,iops_wr_max=1000

# Burst length (durata burst in secondi)
# mbps_rd_max_length=10  (burst per 10 secondi)
```

### 7.4 Network Rate Limits

```bash
# Limitare banda di rete (MB/s)
qm set 100 --net0 virtio,bridge=vmbr0,rate=100
# Limite: 100 MB/s

# Container
pct set 200 --net0 name=eth0,bridge=vmbr0,rate=50
# Limite: 50 MB/s

# Per limitazione piu granulare, usare traffic shaping
# con tc (traffic control) sull'host
```

### 7.5 NUMA

NUMA (Non-Uniform Memory Access) e importante per VM large su server
multi-socket:

```bash
# Abilitare NUMA
qm set 100 --numa 1

# Configurazione NUMA con topologia specifica
qm set 100 --numa 1 \
    --numa0 cpus=0-3,memory=4096 \
    --numa1 cpus=4-7,memory=4096

# Verificare topologia NUMA dell'host
numactl --hardware
# node 0: cpus: 0 1 2 3 4 5 6 7
# node 1: cpus: 8 9 10 11 12 13 14 15

# NUMA e consigliato quando:
# - Server multi-socket
# - VM con molti core (>8)
# - VM con molta RAM (>32 GB)
# - Workload sensibili alla latenza memoria
```

### 7.6 Riepilogo Limiti per Container

```bash
# CPU container
pct set 200 --cores 4        # Numero core
pct set 200 --cpulimit 2     # Limite CPU (come percentuale)
pct set 200 --cpuunits 1024  # Peso relativo

# Memoria container
pct set 200 --memory 4096    # RAM in MB
pct set 200 --swap 1024      # Swap in MB

# Disco container
pct resize 200 rootfs 20G    # Resize rootfs
pct set 200 --rootfs local-lvm:20  # Imposta rootfs

# Rete container
pct set 200 --net0 name=eth0,bridge=vmbr0,rate=50
```

---

## 8. Confronto con VMware

### 8.1 Operazioni Comuni: VMware vs Proxmox

```
+------------------------------------------------------------------+
|     TABELLA CONFRONTO OPERAZIONI VMware vs Proxmox VE            |
+------------------------------------------------------------------+
```

#### Creazione VM

| Operazione               | VMware vSphere            | Proxmox VE                   |
|--------------------------|---------------------------|------------------------------|
| GUI                      | vSphere Client wizard     | Web UI wizard (porta 8006)   |
| CLI                      | govc / PowerCLI           | qm create                   |
| API                      | vSphere API (SOAP/REST)   | REST API /api2/json          |
| Template deploy          | Deploy from template      | qm clone <template-id>      |
| OVF/OVA import           | Deploy OVF Template       | qm importovf                |
| Cloud image              | Content Library           | qm disk import + cloud-init |

```bash
# VMware PowerCLI:
# New-VM -Name "server01" -Template "debian-template" \
#     -VMHost "esxi01" -Datastore "ds01"

# Proxmox CLI equivalente:
qm clone 9000 100 --name server01 --full --storage local-lvm
qm set 100 --ipconfig0 ip=10.0.0.100/24,gw=10.0.0.1
qm start 100
```

#### Snapshot

| Operazione               | VMware vSphere            | Proxmox VE                   |
|--------------------------|---------------------------|------------------------------|
| Creare snapshot          | Snapshot Manager          | qm snapshot <vmid> <name>   |
| Con memoria              | Include memory state      | qm snapshot --vmstate 1     |
| Elencare snapshot        | Snapshot Manager tree     | qm listsnapshot <vmid>      |
| Rollback                 | Revert to snapshot        | qm rollback <vmid> <name>   |
| Eliminare                | Delete snapshot           | qm delsnapshot <vmid> <name>|
| Consolidare              | Consolidate disks         | Non necessario (automatico) |
| Snapshot tree             | Si (ramificato)          | Si (lineare)                |

```bash
# VMware PowerCLI:
# New-Snapshot -VM "server01" -Name "pre-update" -Memory

# Proxmox CLI equivalente:
qm snapshot 100 pre-update --vmstate 1 --description "Pre aggiornamento"
```

#### Clone

| Operazione               | VMware vSphere            | Proxmox VE                   |
|--------------------------|---------------------------|------------------------------|
| Full clone               | Clone to VM               | qm clone <id> <newid> --full|
| Linked clone             | Clone (linked)            | qm clone <id> <newid>       |
| Instant clone            | Instant Clone (vSphere 7+)| Non disponibile             |
| Customization spec       | Guest Customization       | Cloud-init                  |

```bash
# VMware PowerCLI:
# New-VM -Name "clone01" -VM "server01" -LinkedClone \
#     -ReferenceSnapshot "base"

# Proxmox CLI equivalente:
qm clone 100 110 --name clone01
```

#### Migrazione

| Operazione               | VMware vSphere            | Proxmox VE                   |
|--------------------------|---------------------------|------------------------------|
| Live migration           | vMotion                   | qm migrate --online         |
| Storage migration        | Storage vMotion           | qm disk move / qm migrate   |
| Cross-vCenter migration  | Cross-vCenter vMotion     | Non disponibile (1 cluster) |
| Cold migration           | Cold Migration            | qm migrate (offline)        |
| DRS (auto-migrazione)    | DRS / SDRS                | HA (parziale, no auto-balance)|
| Requisito storage        | Shared (per vMotion)      | Shared o local-to-local     |

```bash
# VMware PowerCLI:
# Move-VM -VM "server01" -Destination "esxi02" -VMotionPriority High

# Proxmox CLI equivalente:
qm migrate 100 pve-node2 --online

# Con migrazione storage locale:
qm migrate 100 pve-node2 --online --with-local-disks \
    --targetstorage local-lvm
```

#### Backup e Restore

| Operazione               | VMware vSphere            | Proxmox VE                   |
|--------------------------|---------------------------|------------------------------|
| Backup nativo            | VADP (API per 3rd party)  | vzdump (integrato)          |
| Backup solution          | Veeam, Commvault, etc.    | vzdump + PBS (integrato)    |
| Backup mode              | CBT (Changed Block Track.)| stop, suspend, snapshot     |
| Incrementale             | Via VADP + 3rd party      | PBS (incrementale nativo)   |
| Backup scheduling        | 3rd party tool            | Integrato nella web UI      |
| Restore                  | 3rd party tool            | qmrestore / pct restore    |
| File-level restore       | 3rd party tool            | PBS (nativo)                |

```bash
# VMware (con Veeam):
# Configurazione tramite Veeam Backup console

# Proxmox CLI equivalente:
vzdump 100 --mode snapshot --storage pbs-storage --compress zstd
qmrestore /path/to/backup.vma.zst 100
```

### 8.2 Confronto Funzionalita Infrastrutturali

| Funzionalita             | VMware vSphere            | Proxmox VE                   |
|--------------------------|---------------------------|------------------------------|
| Hypervisor               | ESXi (proprietario)       | KVM + QEMU (open-source)    |
| Container nativi         | No (richiede VM)          | LXC integrato               |
| Cluster management       | vCenter Server            | Integrato (no server extra)  |
| HA                       | vSphere HA                | pve-ha-manager              |
| Load balancing           | DRS                       | Non integrato (manuale)      |
| Distributed switch       | VDS (Enterprise Plus)     | OVS / SDN (integrato)       |
| Shared storage           | VMFS, vSAN                | ZFS, Ceph, NFS, iSCSI       |
| HCI (hyper-converged)    | vSAN (licenza extra)      | Ceph (integrato, gratuito)   |
| Web UI                   | vSphere Client (HTML5)    | Web UI (porta 8006)          |
| API                      | SOAP + REST               | REST (completa)              |
| CLI                      | esxcli, govc, PowerCLI    | qm, pct, pvesh, pvesm       |
| Licenza                  | Per CPU, per funzionalita | AGPL v3 (tutte le funzioni)  |
| Costo base               | Elevato                   | Gratuito                     |
| Supporto                 | Incluso nella licenza     | Sottoscrizione opzionale     |

### 8.3 Confronto Prezzi (Indicativo)

```
+------------------------------------------------------------------+
|     CONFRONTO COSTI ANNUALI (2 server, 2 socket ciascuno)       |
+------------------------------------------------------------------+
|                                                                  |
|  VMware vSphere (prima Broadcom)                                |
|  +----------------------------------------------------------+   |
|  | vSphere Standard: ~$4,000/socket x 4 = ~$16,000/anno     |   |
|  | vCenter Standard: ~$8,000 (una tantum + supporto)         |   |
|  | vSAN Standard: ~$2,500/socket x 4 = ~$10,000/anno         |   |
|  | Backup (Veeam): ~$1,500/socket = ~$6,000/anno             |   |
|  | TOTALE ANNUALE: ~$40,000+                                 |   |
|  +----------------------------------------------------------+   |
|                                                                  |
|  VMware vSphere (dopo acquisizione Broadcom, bundle VCF)        |
|  +----------------------------------------------------------+   |
|  | VMware Cloud Foundation: ~$100,000+ (bundle obbligatorio) |   |
|  | Licenze per core, non piu per socket                      |   |
|  | Prezzi variabili, contattare Broadcom                      |   |
|  +----------------------------------------------------------+   |
|                                                                  |
|  Proxmox VE                                                     |
|  +----------------------------------------------------------+   |
|  | Software: GRATUITO (tutte le funzionalita)                |   |
|  | Ceph (HCI): INCLUSO                                       |   |
|  | Backup (vzdump): INCLUSO                                  |   |
|  | PBS (incrementale): GRATUITO                               |   |
|  | Sottoscrizione Standard (opzionale):                      |   |
|  |   ~350 EUR/socket x 4 = ~1,400 EUR/anno                  |   |
|  | TOTALE ANNUALE: 0 EUR - 1,400 EUR                         |   |
|  +----------------------------------------------------------+   |
|                                                                  |
+------------------------------------------------------------------+
```

### 8.4 Mappatura Terminologia

| VMware Term              | Proxmox VE Term                                     |
|--------------------------|------------------------------------------------------|
| ESXi host                | Proxmox VE node                                     |
| vCenter Server           | Cluster (integrato, no server separato)              |
| Datacenter               | Datacenter (in web UI)                               |
| Cluster                  | Cluster (Corosync-based)                             |
| Resource Pool            | Pool                                                 |
| vSwitch                  | Linux Bridge (vmbr0)                                 |
| VDS (Distributed Switch) | OVS / SDN                                            |
| Port Group               | Bridge + VLAN tag                                    |
| Datastore (VMFS)         | Storage (LVM, ZFS, dir)                              |
| Content Library          | Storage (iso, vztmpl content types)                  |
| VMDK                     | raw / qcow2 (qm disk import per VMDK)               |
| VM Hardware Version      | Machine type (i440fx, q35)                           |
| VMware Tools             | QEMU Guest Agent + VirtIO drivers                    |
| PVSCSI                   | VirtIO SCSI                                          |
| VMXNET3                  | VirtIO NIC                                           |
| vMotion                  | Online Migration (qm migrate --online)               |
| Storage vMotion          | Disk Move (qm disk move)                             |
| Snapshot Manager         | Snapshot (qm snapshot / pct snapshot)                |
| HA / DRS                 | pve-ha-manager (no auto-balance)                     |
| vSAN                     | Ceph (integrato)                                     |
| NSX                      | SDN (Proxmox SDN, integrato)                         |
| VADP (backup API)        | vzdump + PBS                                         |
| OVF/OVA                  | qm importovf                                        |
| Linked Clone             | Linked Clone (qm clone senza --full)                |
| Instant Clone            | Non disponibile                                      |
| Fault Tolerance          | Non disponibile (HA come alternativa)                |
| vGPU                     | VFIO GPU passthrough / mediated devices (mdev/SR-IOV)|

### 8.5 Guida Rapida per Amministratori VMware

Per chi arriva da VMware, questa tabella mappa i task quotidiani:

```
+------------------------------------------------------------------+
|     CHEAT SHEET: DA VMware A Proxmox VE                          |
+------------------------------------------------------------------+
|                                                                  |
| TASK                  | VMware                | Proxmox           |
| ======================|=======================|================== |
| Accesso management    | vSphere Client        | https://host:8006 |
| SSH all'host          | ssh root@esxi         | ssh root@pve      |
| Lista VM              | govc vm.info          | qm list           |
| Avviare VM            | govc vm.power -on     | qm start 100      |
| Spegnere VM           | govc vm.power -off    | qm stop 100       |
| Console VM            | VMRC / Web Console    | noVNC / SPICE     |
| Stato host            | esxcli system ...     | pveversion -v     |
| Lista datastore       | esxcli storage ...    | pvesm status      |
| Upload ISO            | Datastore browser     | pvesm download    |
| Creare snapshot       | Snapshot Manager      | qm snapshot       |
| Backup VM             | Veeam / VADP          | vzdump            |
| Migrare VM            | vMotion               | qm migrate --online|
| Monitoraggio          | vCenter perf charts   | Web UI + Grafana  |
| Log eventi            | vCenter events        | journalctl / syslog|
| Aggiornare host       | VUM / Lifecycle Mgr   | apt update/upgrade|
|                                                                  |
+------------------------------------------------------------------+
```

---

## Riferimenti

- Documentazione ufficiale Proxmox VE: https://pve.proxmox.com/pve-docs/
- QEMU/KVM Documentation: https://www.qemu.org/docs/master/
- LXC Documentation: https://linuxcontainers.org/lxc/
- Wiki Proxmox (Migration): https://pve.proxmox.com/wiki/Migration
- VirtIO Drivers Windows: https://github.com/virtio-win/virtio-win-pkg-scripts
- Proxmox Backup Server: https://pbs.proxmox.com/docs/
- Packer Proxmox Builder: https://developer.hashicorp.com/packer/plugins/builders/proxmox

---

*Documento parte della suite di documentazione per la migrazione VMware-to-Proxmox.*
*Sezione: 02-FONDAMENTI-PROXMOX-VE*

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — QEMU 10.1 e LXC 6 in Proxmox VE 9.x.** Proxmox VE 9.x integra QEMU 10.1.2 (vs QEMU 8.x in PVE 8.x). Cambiamenti rilevanti per la gestione delle VM: (a) miglioramenti al protocollo di migrazione live (precopy + postcopy hybrid stabilizzato); (b) supporto piu maturo per `virtio-fs` (filesystem condiviso host-guest a basso overhead); (c) `migrate-set-parameters` accetta valori per `multifd-channels` di default, riducendo i tempi di migrazione su rete 10/25 GbE. Per i container, LXC 6.0.5 introduce miglior supporto a cgroup v2 e gestione delle network namespace ottimizzata. Per progetti nuovi, valutare di partire direttamente con PVE 9.x; per cluster 8.x in produzione, l'aggiornamento e descritto sul wiki Proxmox.

> **Errore comune — `cpu: host` e migrazione fra generazioni di CPU diverse.** Impostare `--cpu host` espone tutte le feature flag della CPU del nodo source. Quando si migra a un nodo con CPU di generazione anteriore (es. Skylake → Cascade Lake va, ma Ice Lake → Skylake puo fallire se Ice Lake espone instruction set non presenti in Skylake), QEMU si rifiuta di accettare la VM. Sintomo: `Failed to start VM: cpu feature 'avx512vbmi2' not available`. Soluzione: usare un baseline esplicito (`x86-64-v2-AES` o `x86-64-v3`) che e il minimo comune denominatore noto, oppure pin di CPU type compatibile con tutti i nodi del cluster. Per cluster eterogenei, definire una "EVC-like" baseline al momento del cluster bootstrap.

> **Caso reale — Backup `--mode snapshot` senza qemu-guest-agent.** Una VM PostgreSQL aveva backup `vzdump` schedulati notturni in `--mode snapshot`. Il restore di test mostrava periodicamente DB in stato "needs recovery" (WAL non applicati). Causa: `--mode snapshot` senza agent attivo produce un dump crash-consistent — equivalente a uno spegnimento brutale della VM. PostgreSQL si recupera, ma e un rischio non necessario per un DB transazionale. Soluzione: installare `qemu-guest-agent` nel guest (`apt install qemu-guest-agent`), abilitare l'agent nella config Proxmox (`qm set <vmid> --agent enabled=1,fstrim_cloned_disks=1`), e da quel momento `--mode snapshot` esegue `fsfreeze` prima dello snapshot, ottenendo backup *application-consistent*. Lezione: per ogni VM con DB, file server, o app stateful, l'agent non e opzionale.

---

## Esercizi

1. **Concettuale — VM o LXC?** Per ciascuno dei seguenti workload, scegliere VM KVM o container LXC e motivare in 2 righe: (a) Postgres single-instance da 50 GB di dati; (b) microservizio Node.js stateless dietro reverse proxy; (c) GitLab CI runner che builda Docker images; (d) Active Directory Domain Controller; (e) NGINX edge gateway; (f) Plex Media Server con transcoding HW; (g) un servizio di rete che richiede `iptables` con regole proprie (interface bridge in route mode). *Risposte attese (sintesi):* (a) VM (kernel-fence, snapshot indipendente); (b) LXC (basso overhead); (c) VM (per via di Docker-in-Container — possibile in LXC unprivileged ma fragile); (d) VM (Microsoft non supporta AD in container); (e) LXC (stateless, leggero); (f) VM (passthrough GPU); (g) VM (LXC unprivileged ha limiti sulle netfilter rules in alcuni scenari).

2. **Lab — creazione VM via CLI e import disco.** Creare via `qm create` una VM Linux basata su Debian 12, attaccare un disco ISO di installazione, fare boot e installare il guest. Quindi installare qemu-guest-agent e abilitare la consistency applicativa. Misurare il tempo di start della VM (`time qm start`). Confrontare con il tempo di start di un container LXC analogo (`pct create` + `pct start`). Documentare la differenza e attribuirla alle ragioni architetturali (BIOS, kernel boot, init).

3. **Scenario — backup application-consistent vs crash-consistent.** Un DB MySQL e in produzione su Proxmox. Documenta in massimo 12 righe: (a) come configurare il backup application-consistent via `vzdump --mode snapshot` + `qemu-guest-agent`; (b) come testare l'effettiva consistenza eseguendo il restore in un sandbox separato; (c) cosa fare se il guest non ha l'agent (es. una vecchia distro RHEL 5 che non lo supporta) — risposta accettabile: `--mode suspend` per congelare la CPU senza fsfreeze, oppure orchestrare un dump SQL pre-snapshot. *Verifica restore:* `mysqlcheck --all-databases --check` non deve segnalare `corrupt` o `Innodb: needs recovery`.

4. **Stretch — template + cloud-init di provisioning.** Costruire un template VM Debian 12 con cloud-init installato, importare l'immagine `debian-12-genericcloud-amd64.qcow2`, configurare `qm set <vmid> --ide2 <storage>:cloudinit`, marcare come template (`qm template <vmid>`). Quindi fare `qm clone <template-vmid> <new-vmid>`, impostare `qm set <new-vmid> --ipconfig0 ip=10.10.20.50/24,gw=10.10.20.1` + `--ciuser admin --cipassword <hash> --sshkey ~/.ssh/id_ed25519.pub` e far partire. Verificare che la nuova VM abbia ricevuto IP e SSH key al primo boot. Dettagli in modulo 14.1.

## Auto-valutazione

1. Differenza fra `iothread=1` e `iothread=0` su un disco virtio-scsi — cosa cambia in termini di code QEMU e vCPU pinning?
2. Cosa fa `discard=on` su un disco e in quale scenario produce piu beneficio (qcow2/sparse, LVM-Thin, ZFS)?
3. Differenza fra SeaBIOS e OVMF — quale serve per Secure Boot, Windows 11 con TPM, EFI vars persistenti?
4. Differenza fra `qm migrate --online` e `qm migrate <vmid> <target> --with-local-disks` — quando uno e necessario sull'altro?
5. Cosa fa il flag `--mode snapshot` in `vzdump` e cosa produce esattamente quando il guest ha l'agent qemu-guest-agent attivo?
6. Differenza tra full clone e linked clone su ZFS / LVM-Thin / qcow2 — quando ciascuno e raccomandato?
7. Quali sono i tre livelli di resource limit applicabili ad una VM e quali primitive del kernel li implementano (cgroup v2 controllers)?
8. Container LXC privileged vs unprivileged: quale UID mapping implementa l'isolamento, e quali capability sono droppate di default?

## Letture primarie consigliate

- [`PVE-ADMIN`] Proxmox VE Administration Guide — capitoli "QEMU/KVM Virtual Machines", "Linux Containers", "Backup & Restore", "Storage". https://pve.proxmox.com/pve-docs/pve-admin-guide.html
- [`QEMU-DOCS`] QEMU Documentation — sezione "System emulation". https://www.qemu.org/docs/master/
- [`QEMU-IMG`] qemu-img(1) — formati disco e operazioni. https://www.qemu.org/docs/master/tools/qemu-img.html
- [`KVM-DOCS`] Linux KVM Documentation. https://www.linux-kvm.org/page/Documents
- LXC Documentation. https://linuxcontainers.org/lxc/documentation/
- Linux cgroup v2 documentation (kernel.org). https://docs.kernel.org/admin-guide/cgroup-v2.html
- VirtIO Drivers Windows. https://github.com/virtio-win/virtio-win-pkg-scripts
- [`PBS-DOCS`] Proxmox Backup Server Documentation. https://pbs.proxmox.com/docs/

## Collegamenti incrociati

- Modulo 02.1 — `architettura-installazione-proxmox.md`: il modulo precedente, infrastruttura del nodo.
- Modulo 03.1 — `../03-STORAGE-AVANZATO-PROXMOX/lvm-e-lvm-thin-proxmox.md`: storage backend per il disco delle VM.
- Modulo 03.2 — `../03-STORAGE-AVANZATO-PROXMOX/nfs-iscsi-storage-condiviso.md`: NFS/iSCSI come storage condiviso, prerequisito per migrazione live senza `--with-local-disks`.
- Modulo 06.1, 06.2, 06.3 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/`: strategie di migrazione (cold/warm/live, virt-v2v).
- Modulo 09.4 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-windows-server-vm.md`: applicazione concreta a Windows Server.
- Modulo 10.3 — `../10-CLUSTER-HA-PROXMOX-POST-MIGRAZIONE/live-migration-proxmox-interna.md`: live migration interna a Proxmox post-migrazione.
- Modulo 11.1 — `../11-BACKUP-E-RIPRISTINO-PROXMOX/backup-vm-e-container.md`: backup operativo con vzdump e PBS.
- Modulo 14.1 — `../14-AUTOMAZIONE-E-INFRASTRUCTURE-AS-CODE/cloud-init-template-vm.md`: cloud-init e template VM industriali.

## Glossario locale

| Termine | Definizione |
|---|---|
| **VMID** | Identificativo numerico univoco di una VM o container nel cluster. Range tipico per VM 100-999, riservato cluster-wide. |
| **machine type** | Specifica il chipset emulato. `pc-i440fx` (semplice, classico) vs `pc-q35` (PCIe nativo, raccomandato per Windows 10/11 e GPU passthrough). |
| **BIOS** | `seabios` (legacy) vs `ovmf` (UEFI; richiede `efidisk0` per persistenza vars). |
| **`scsihw`** | Controller SCSI emulato: `lsi`, `lsi53c810`, `megasas`, `pvscsi`, `virtio-scsi-single` (consigliato per multi-queue per disk). |
| **`iothread=1`** | Dedica un thread QEMU separato per il disco, evitando blocchi sul vCPU thread principale. |
| **`discard=on`** | Inoltra TRIM/UNMAP dal guest allo storage backend per recuperare spazio (vale su qcow2 sparse, LVM-Thin, ZFS). |
| **virtio-scsi / virtio-blk** | Driver paravirtualizzato per disco. virtio-scsi e piu flessibile (multipath, PR), virtio-blk piu leggero (legacy). |
| **virtio-net** | Driver paravirtualizzato per rete (sostituisce VMXNET3 di VMware). |
| **`qm`** | CLI VM Proxmox: `qm create/start/stop/migrate/clone/template/destroy`. |
| **`pct`** | CLI container LXC Proxmox: `pct create/start/exec/...`. |
| **vzdump mode** | `snapshot` (live, con/senza agent), `suspend` (sospende la VM, breve downtime), `stop` (ferma la VM, downtime maggiore). |
| **qemu-guest-agent** | Daemon nel guest che permette `fsfreeze` per backup application-consistent, `qm guest exec` per comandi remoti, fstrim, ipv. |
| **template** | VM marcata come tale (`qm template`); non avviabile, usata come base per clone full o linked. |
| **linked clone** | Clone che condivide il disco base con il template, salvando solo i delta in un overlay (qcow2/ZFS). |
| **CPU type** | `host` (espone tutte le feature, blocca migrazione fra CPU diverse) vs `kvm64` / `x86-64-v2-AES` / `x86-64-v3` (baseline, portabile). |
| **NUMA** | Quando attivato (`--numa 1`), QEMU rispetta la topologia NUMA della macchina fisica per migliori performance memoria. |
| **balloon** | Memoria minima vs massima allocabile. Permette al kernel host di recuperare RAM dalla VM se non utilizzata. |
