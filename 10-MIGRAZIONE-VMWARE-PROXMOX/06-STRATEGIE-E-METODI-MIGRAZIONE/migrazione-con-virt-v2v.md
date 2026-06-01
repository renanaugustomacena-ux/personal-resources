# Migrazione con virt-v2v

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 06.2 (segue 06.1, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 06.1 (strategie); concetti libvirt e KVM/QEMU; Linux command line solida.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. installare e verificare `virt-v2v` + `libguestfs-tools` + `virtio-win` su un host conversion (Debian, Ubuntu, RHEL/Rocky);
> 2. eseguire conversioni con i 3 modi di input principali — `-i vmx`, `-i ova`, `-i disk`, `-i libvirt` — comprendendo i loro vincoli (richiede vCenter access? richiede file locale? richiede libvirt domain.xml?);
> 3. configurare i 4 modi di output — `-o local`, `-o qemu`, `-o libvirt`, `-o glance` — scegliendo il piu adeguato all'integrazione con Proxmox;
> 4. forzare l'iniezione di driver VirtIO per Windows (`--install virtio-win`) e capire come virt-v2v rilevi e ripari il bootloader Linux (GRUB);
> 5. diagnosticare i 5-7 errori piu frequenti (OS detection failed, VirtIO drivers missing, NTFS dirty, root partition non trovata, errore SSL su vCenter, free space exhaustion);
> 6. costruire uno script di batch conversion con logging strutturato, parallelismo limitato, retry su transient errors, validazione output post-conversione.
> **Tempo stimato:** lettura 60-90 min · lab 240-360 min (per fare 4-5 conversioni reali end-to-end)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** virt-v2v 2.x (libguestfs 1.50+); virtio-win-stable; libguestfs richiede `supermin` e cache pre-built.

## Mappa concettuale

```
+======================================================+
|  virt-v2v: pipeline di conversione                   |
+======================================================+
|                                                      |
|   INPUT MODE (-i)                                    |
|   +--+---+----+----+--------+                        |
|   |vmx|ova|disk|libvirt|...|                         |
|   +-^-+-^-+--^-+--^----+                             |
|     |   |    |    +- richiede domain.xml libvirt     |
|     |   |    +-- file locale .raw / .vmdk            |
|     |   +-- archivio TAR con OVF + VMDK              |
|     +-- vCenter (vpx://) o ESXi (esx://)             |
|         |                                            |
|         v                                            |
|   PROCESSING                                         |
|     1. Inspection: rileva OS, partizioni, fs        |
|     2. Conversion: rimuove VMware Tools             |
|     3. Driver injection: VirtIO scsi/net/blk/balloon|
|     4. Bootloader fix: GRUB / Windows boot config   |
|     5. initramfs/dracut update                      |
|     6. Network reconfig: vmxnet3 → virtio          |
|         |                                            |
|         v                                            |
|   OUTPUT MODE (-o)                                   |
|   +-----+-----+--------+-------+                     |
|   |local|qemu |libvirt |glance |                     |
|   +-^---+-^---+--^-----+--^----+                     |
|     |    |    |      +-- OpenStack image            |
|     |    |    +-- libvirt domain define             |
|     |    +-- write a directory + libvirt XML        |
|     +-- write only disks to a path                  |
|         |                                            |
|         v                                            |
|   POST-CONVERSION (manuale)                          |
|     - qm create (con i metadati corretti)           |
|     - qm importdisk (per portare il qcow2)          |
|     - qm set --scsi0 ...                             |
|     - qm start                                       |
|         |                                            |
|         v                                            |
|   VERIFICA                                           |
|     - boot ok (dracut shell?)                        |
|     - rete ok (DHCP / static)                        |
|     - servizi up                                     |
|     - qemu-guest-agent attivo                        |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **virt-v2v fa solo la conversione tecnica.** Non gestisce inventory, non gestisce wave, non gestisce DNS cutover. E un *tool*, non un *processo*. Il processo lo costruisci attorno (modulo 06.1).
2. **`-i vmx` con `-ic vpx://` e il piu comodo per piccoli numeri.** Si collega al vCenter, scarica VMDK in streaming, converte. Non serve OVA intermedio. Limite: per VM molto grandi (TB), la rete instabile lo rompe e ricominci da zero.
3. **`-i ova` e il piu robusto.** `ovftool` esporta OVA, virt-v2v converte localmente. Due step ma ognuno isolato — se uno fallisce, riprendi da li. Per VM grandi e l'approccio raccomandato.
4. **VirtIO injection automatica funziona ~90% delle volte.** Il 10% che fallisce: Windows con registry corrotto, Linux con root partition non standard (LVM dentro LUKS dentro partition), kernel custom con moduli built-in. In questi casi: pre-installare manualmente i driver *prima* della conversione, poi virt-v2v si limita a riconoscerli.
5. **Il post-convert non e finito.** virt-v2v produce un qcow2 + (se `-o libvirt`) un domain.xml. Per Proxmox serve il passaggio *manuale*: `qm create` + `qm importdisk` + `qm set --scsi0 ...,iothread=1,discard=on` + `qm set --net0 virtio,bridge=vmbr0`. Lo script di automation va costruito per fare questi step.

## Panoramica di virt-v2v

**virt-v2v** è uno strumento open-source sviluppato da Red Hat per convertire macchine virtuali da hypervisor proprietari (VMware, Hyper-V) verso piattaforme basate su KVM/libvirt. È il tool di riferimento nel mondo Linux/Red Hat per le migrazioni V2V (Virtual-to-Virtual) e V2P (Virtual-to-Physical).

Il tool gestisce automaticamente:
- Conversione del formato disco (VMDK -> qcow2/raw)
- Rimozione dei VMware Tools / Hyper-V Integration Services
- Iniezione dei driver VirtIO nel guest OS
- Riconfigurazione del bootloader (GRUB)
- Aggiornamento di initramfs/initrd con i moduli VirtIO
- Riconfigurazione delle interfacce di rete

### Piattaforme Sorgente Supportate

| Sorgente | Metodo di Input | Note |
|----------|----------------|------|
| VMware ESXi/vCenter | `-i vmx` (file VMX locale) | Richiede accesso ai file della VM |
| VMware vCenter | `-ic vpx://` (connessione diretta) | Connessione diretta via API |
| VMware ESXi | `-ic esx://` (connessione diretta) | Connessione diretta all'host |
| Hyper-V | `-i disk` (file VHDX) | Conversione da disco |
| Xen | `-ic xen+ssh://` | Connessione via SSH |
| File OVA/OVF | `-i ova` | Import da archivio OVA |
| Disco generico | `-i disk` | Qualsiasi file disco supportato |

### Piattaforme di Destinazione Supportate

| Destinazione | Flag di Output | Note |
|-------------|---------------|------|
| Directory locale | `-o local` | File qcow2/raw + XML libvirt |
| libvirt locale | `-o libvirt` | Import diretto in libvirt |
| QEMU diretto | `-o qemu` | Generazione script qemu-system |
| oVirt/RHV | `-o rhv-upload` | Upload diretto a RHV Manager |
| OpenStack | `-o openstack` | Upload a Glance |
| Kubevirt | `-o kubevirt` | Export per Kubernetes |

> **Nota importante per Proxmox VE:** virt-v2v non ha un output mode nativo per Proxmox. Si utilizza tipicamente `-o local` per generare i file disco e XML, poi si importano manualmente in Proxmox con `qm importdisk`.

---

## Installazione di virt-v2v

### Conversion Host — Requisiti

Il **conversion host** è la macchina su cui virt-v2v viene eseguito. Deve avere:

- Sistema operativo: RHEL 8/9, CentOS Stream 8/9, Fedora 38+, Rocky Linux 8/9, o AlmaLinux 8/9
- RAM: almeno 2 GB liberi (più per VM Windows)
- Spazio disco: almeno 2x la dimensione del disco della VM da convertire
- Accesso di rete verso VMware vCenter/ESXi e Proxmox

> **Attenzione:** virt-v2v su Debian/Ubuntu NON è ufficialmente supportato da Red Hat e potrebbe presentare problemi, specialmente con le VM Windows. Si consiglia di usare una distribuzione RHEL-based come conversion host.

### Installazione su RHEL/CentOS/Rocky 8/9

```bash
# Installare virt-v2v e le dipendenze
dnf install -y virt-v2v

# Questo installa anche:
# - libguestfs (libreria per l'accesso ai filesystem guest)
# - libguestfs-tools (strumenti aggiuntivi)
# - qemu-img (conversione formati disco)
# - nbdkit (Network Block Device kit)
# - virtio-win (driver VirtIO per Windows, su RHEL/CentOS)

# Verificare l'installazione
virt-v2v --version
# Output: virt-v2v 2.x.x

# Verificare che libguestfs funzioni correttamente
libguestfs-test-tool
# Deve completarsi senza errori

# Installare i driver VirtIO per Windows (se non già presenti)
dnf install -y virtio-win
# I driver vengono installati in /usr/share/virtio-win/

# Verificare la presenza dell'ISO VirtIO
ls -la /usr/share/virtio-win/virtio-win*.iso
```

### Installazione su Fedora

```bash
# Fedora ha spesso la versione più recente di virt-v2v
dnf install -y virt-v2v virtio-win libguestfs-tools

# Verificare
virt-v2v --version
```

### Installazione su Debian/Ubuntu (Non Ufficiale)

```bash
# ATTENZIONE: Supporto limitato, specialmente per VM Windows
apt install -y virt-v2v libguestfs-tools qemu-utils

# I driver VirtIO per Windows NON sono inclusi in Debian/Ubuntu
# Scaricarli manualmente:
mkdir -p /usr/share/virtio-win/
wget -O /usr/share/virtio-win/virtio-win.iso \
  https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso

# Impostare la variabile d'ambiente per virt-v2v
export VIRTIO_WIN=/usr/share/virtio-win/virtio-win.iso
```

### Configurazione dell'Ambiente

```bash
# Impostare la directory temporanea per file grandi
# virt-v2v necessita di spazio temporaneo pari alla dimensione del disco VM
export TMPDIR=/path/to/large/temp/directory
# OPPURE
export LIBGUESTFS_CACHEDIR=/path/to/large/temp/directory

# Per VM Windows, specificare la posizione dei driver VirtIO
export VIRTIO_WIN=/usr/share/virtio-win/virtio-win.iso

# Disabilitare il check del modulo KVM (se eseguito in una VM)
export LIBGUESTFS_BACKEND=direct

# Per debug verbose
export LIBGUESTFS_DEBUG=1
export LIBGUESTFS_TRACE=1
```

---

## Conversione da VMware — Metodi di Input

### Metodo 1: Input da File VMX Locale (-i vmx)

Questo metodo richiede che i file della VM (VMX + VMDK) siano accessibili localmente o tramite mount.

```bash
# 1. Copiare o montare i file della VM VMware

# Opzione A: Montare il datastore VMware via NFS
mkdir -p /mnt/vmware-datastore
mount -t nfs esxi-host:/vmfs/volumes/datastore1 /mnt/vmware-datastore

# Opzione B: Copiare i file con SCP
mkdir -p /tmp/vm-export/WebServer
scp root@esxi-host:/vmfs/volumes/datastore1/WebServer/* /tmp/vm-export/WebServer/

# 2. Eseguire virt-v2v con input VMX

# Per output in directory locale:
virt-v2v \
  -i vmx /mnt/vmware-datastore/WebServer/WebServer.vmx \
  -o local -os /tmp/converted-vms/ \
  -of qcow2

# Spiegazione dei flag:
# -i vmx          = input da file VMX
# -o local        = output in directory locale
# -os /tmp/...    = directory di output
# -of qcow2       = formato disco di output (qcow2)

# Per VM Windows con iniezione driver VirtIO:
virt-v2v \
  -i vmx /mnt/vmware-datastore/WinServer/WinServer.vmx \
  -o local -os /tmp/converted-vms/ \
  -of qcow2 \
  --root first

# --root first = seleziona automaticamente la prima partizione Windows trovata
```

### Metodo 2: Connessione Diretta a vCenter (-ic vpx://)

Questo è il metodo più comodo quando si ha accesso diretto al vCenter Server.

```bash
# Formato URI vCenter:
# vpx://user@vcenter-host/Datacenter/esxi-host/vm-name

# Conversione diretta da vCenter
virt-v2v \
  -ic 'vpx://administrator@vsphere.local@vcenter.example.com/DC1/esxi-host1.example.com?no_verify=1' \
  -it vddk \
  -io vddk-libdir=/opt/vmware-vix-disklib-distrib \
  -io vddk-thumbprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx \
  "WebServer-VM" \
  -o local -os /tmp/converted-vms/ \
  -of qcow2

# Spiegazione dei flag:
# -ic vpx://...   = URI di connessione al vCenter
# ?no_verify=1    = ignora il certificato SSL
# -it vddk        = usa VMware VDDK per il trasferimento (più veloce)
# -io vddk-libdir = percorso delle librerie VDDK
# -io vddk-thumbprint = thumbprint SSL dell'host ESXi
# "WebServer-VM"  = nome della VM su VMware
# -o local        = output locale
# -os /tmp/...    = directory di output
# -of qcow2       = formato output

# NOTA: La VM deve essere SPENTA su VMware prima dell'esecuzione
```

#### Installazione di VMware VDDK (Virtual Disk Development Kit)

```bash
# Il VDDK accelera significativamente il trasferimento dei dischi da VMware
# Download: https://developer.vmware.com/tools/vddk

# 1. Scaricare il VDDK (richiede account VMware)
# File: VMware-vix-disklib-8.0.x-xxxxxxx.x86_64.tar.gz

# 2. Estrarre
tar xzf VMware-vix-disklib-8.0.x-*.tar.gz -C /opt/

# 3. Verificare
ls /opt/vmware-vix-disklib-distrib/lib64/

# 4. Ottenere il thumbprint SSL dell'host ESXi
openssl s_client -connect esxi-host:443 < /dev/null 2>/dev/null | \
  openssl x509 -fingerprint -sha1 -noout
# Output: SHA1 Fingerprint=XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX
```

### Metodo 3: Connessione Diretta a ESXi (-ic esx://)

```bash
# Per connessione diretta a un host ESXi (senza vCenter)
virt-v2v \
  -ic 'esx://root@esxi-host.example.com?no_verify=1' \
  "WebServer-VM" \
  -o local -os /tmp/converted-vms/ \
  -of qcow2

# Con password via variabile d'ambiente
export LIBGUESTFS_BACKEND=direct
echo 'your-password' > /tmp/esxi-password
chmod 600 /tmp/esxi-password

virt-v2v \
  -ic 'esx://root@esxi-host.example.com?no_verify=1' \
  -ip /tmp/esxi-password \
  "WebServer-VM" \
  -o local -os /tmp/converted-vms/ \
  -of qcow2

rm -f /tmp/esxi-password
```

### Metodo 4: Input da File OVA (-i ova)

```bash
# Da file OVA esportato da VMware
virt-v2v \
  -i ova /path/to/WebServer.ova \
  -o local -os /tmp/converted-vms/ \
  -of qcow2

# Se l'OVA contiene più dischi, virt-v2v li converte tutti

# Per OVF (directory con file separati):
virt-v2v \
  -i ova /path/to/WebServer/ \
  -o local -os /tmp/converted-vms/ \
  -of qcow2
```

---

## Opzioni di Output

### Output Locale (-o local)

```bash
# Output più comune per migrazione verso Proxmox
virt-v2v -i vmx /path/to/vm.vmx \
  -o local \
  -os /tmp/converted/ \
  -of qcow2

# Risultato nella directory /tmp/converted/:
# - WebServer-sda    (file disco qcow2)
# - WebServer.xml    (definizione libvirt XML)

# Il file XML contiene informazioni utili sulla configurazione originale
# ma non è direttamente usabile da Proxmox

# Formati di output disponibili:
# -of qcow2   = QEMU Copy-On-Write v2 (consigliato per Proxmox con directory storage)
# -of raw      = Raw disk image (consigliato per ZFS/LVM storage)
```

### Output libvirt (-o libvirt)

```bash
# Import diretto in libvirt locale (utile se si usa Proxmox con libvirt)
virt-v2v -i vmx /path/to/vm.vmx \
  -o libvirt \
  -os qemu:///system \
  -of qcow2

# La VM viene registrata automaticamente in libvirt
virsh list --all
# Dovreste vedere la VM convertita nella lista
```

### Output QEMU (-o qemu)

```bash
# Genera uno script bash che avvia la VM con qemu-system
virt-v2v -i vmx /path/to/vm.vmx \
  -o qemu \
  -os /tmp/converted/ \
  -of qcow2

# Risultato: /tmp/converted/WebServer.sh
# Lo script contiene il comando qemu-system-x86_64 completo
# Utile per test rapido prima dell'import in Proxmox
```

---

## Conversione di VM Windows

La conversione delle VM Windows è più complessa rispetto a Linux e richiede attenzione particolare all'iniezione dei driver VirtIO.

### Prerequisiti per VM Windows

```bash
# Verificare che i driver VirtIO siano disponibili
ls /usr/share/virtio-win/
# Output:
# virtio-win-0.1.240.iso
# virtio-win.iso -> virtio-win-0.1.240.iso
# guest-agent/
# drivers/

# OPPURE se installati manualmente:
export VIRTIO_WIN=/var/lib/vz/template/iso/virtio-win-0.1.240.iso
```

### Conversione Windows Step-by-Step

```bash
# === Conversione di Windows Server da VMware ===

# 1. Assicurarsi che la VM Windows sia spenta su VMware

# 2. Eseguire virt-v2v
virt-v2v \
  -ic 'vpx://administrator@vsphere.local@vcenter.local/DC1/esxi-host1?no_verify=1' \
  -it vddk \
  -io vddk-libdir=/opt/vmware-vix-disklib-distrib \
  -io vddk-thumbprint=XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX \
  "WinServer2019" \
  -o local -os /tmp/converted/ \
  -of qcow2

# virt-v2v eseguirà automaticamente:
# a. Download del disco VMDK
# b. Rilevamento del sistema operativo Windows
# c. Rimozione di VMware Tools
# d. Iniezione dei driver VirtIO:
#    - viostor (storage controller)
#    - NetKVM (network adapter)
#    - Balloon (memory balloon)
#    - vioserial (serial port)
#    - pvpanic (panic device)
#    - qxldod (display driver)
# e. Configurazione del registro di Windows per il boot con VirtIO
# f. Installazione del QEMU Guest Agent
# g. Conversione del formato disco

# 3. Verificare il risultato
ls -la /tmp/converted/
qemu-img info /tmp/converted/WinServer2019-sda

# 4. Importare in Proxmox
scp /tmp/converted/WinServer2019-sda root@proxmox:/tmp/
ssh root@proxmox "qm importdisk 300 /tmp/WinServer2019-sda local-lvm"
```

### Gestione delle Versioni di Windows

```bash
# virt-v2v rileva automaticamente la versione di Windows
# e seleziona i driver VirtIO corretti

# Versioni supportate:
# - Windows Server 2012 R2
# - Windows Server 2016
# - Windows Server 2019
# - Windows Server 2022
# - Windows 10
# - Windows 11

# Per forzare la selezione della root partition Windows:
virt-v2v ... --root /dev/sda2

# Per specificare manualmente la versione Windows (raro):
virt-v2v ... --root first

# Se virt-v2v non rileva correttamente il tipo di OS:
virt-v2v ... --root first 2>&1 | grep -i "windows"
```

---

## Conversione di VM Linux

Le VM Linux sono generalmente più semplici da convertire perché i driver VirtIO sono inclusi nel kernel Linux.

```bash
# Conversione base di una VM Linux
virt-v2v \
  -i vmx /mnt/vmware-ds/LinuxServer/LinuxServer.vmx \
  -o local -os /tmp/converted/ \
  -of qcow2

# virt-v2v eseguirà automaticamente:
# a. Download e conversione del disco
# b. Rilevamento della distribuzione Linux
# c. Rimozione di open-vm-tools (VMware Tools per Linux)
# d. Verifica che i driver VirtIO siano nel kernel
# e. Rigenerazione di initramfs/initrd con moduli VirtIO
# f. Riconfigurazione di GRUB
# g. Aggiornamento di fstab (se necessario)
# h. Riconfigurazione delle interfacce di rete

# Distribuzioni Linux supportate:
# - RHEL/CentOS/Rocky/Alma 7, 8, 9
# - Debian 10, 11, 12
# - Ubuntu 20.04, 22.04, 24.04
# - Fedora (ultime 3 versioni)
# - SUSE/openSUSE
# - Oracle Linux
```

---

## Workflow Completo: Da VMware a Proxmox con virt-v2v

### Passo 1: Preparazione

```bash
# Sul conversion host (RHEL/CentOS/Rocky):

# Verificare spazio disponibile
df -h /tmp/converted/
# Deve avere almeno 2x la dimensione del disco VM

# Verificare la connettività verso vCenter
curl -k https://vcenter.local/sdk
# Deve restituire il WSDL di vCenter

# Verificare la connettività verso Proxmox
ssh root@proxmox-host "pvesm status"
```

### Passo 2: Conversione

```bash
# Eseguire la conversione con output verbose
virt-v2v -v -x \
  -ic 'vpx://administrator@vsphere.local@vcenter.local/DC1/esxi-host1?no_verify=1' \
  -ip /tmp/vcenter-password \
  "TargetVM" \
  -o local -os /tmp/converted/ \
  -of qcow2 \
  2>&1 | tee /var/log/virt-v2v-TargetVM.log

# Flag di debug:
# -v  = verbose
# -x  = trace (libxml2)
```

### Passo 3: Trasferimento a Proxmox

```bash
# Trasferire il disco convertito al server Proxmox
rsync -avP --progress \
  /tmp/converted/TargetVM-sda \
  root@proxmox-host:/tmp/vm-import/

# Per dischi molto grandi, usare compressione:
rsync -avzP --progress \
  /tmp/converted/TargetVM-sda \
  root@proxmox-host:/tmp/vm-import/
```

### Passo 4: Import in Proxmox

```bash
# Sul server Proxmox:

# Creare la VM
qm create 300 \
  --name "TargetVM" \
  --memory 4096 \
  --cores 4 \
  --cpu host \
  --bios seabios \
  --scsihw virtio-scsi-pci \
  --net0 virtio,bridge=vmbr0 \
  --ostype l26 \
  --agent enabled=1

# Importare il disco
qm importdisk 300 /tmp/vm-import/TargetVM-sda local-lvm

# Collegare il disco
qm set 300 --scsi0 local-lvm:vm-300-disk-0

# Impostare il boot
qm set 300 --boot order=scsi0

# Avviare
qm start 300
```

### Passo 5: Validazione

```bash
# Verificare che la VM si avvii correttamente
qm status 300

# Verificare il guest agent
qm agent 300 ping

# Verificare la rete
qm agent 300 network-get-interfaces

# Accedere alla console
# Proxmox Web UI > VM 300 > Console
```

---

## Script di Batch Conversion

```bash
#!/bin/bash
# batch-virt-v2v.sh - Conversione batch di VM da VMware
# Utilizzo: ./batch-virt-v2v.sh <file-lista-vm>

set -euo pipefail

# === CONFIGURAZIONE ===
VCENTER_URI="vpx://administrator@vsphere.local@vcenter.local/DC1/esxi-host1?no_verify=1"
VCENTER_PASSWORD_FILE="/tmp/vcenter-password"
VDDK_DIR="/opt/vmware-vix-disklib-distrib"
VDDK_THUMBPRINT="XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX"
OUTPUT_DIR="/tmp/converted"
PROXMOX_HOST="root@proxmox-node1"
PROXMOX_STORAGE="local-lvm"
LOG_DIR="/var/log/virt-v2v-batch"
START_VMID=300

# === FUNZIONI ===
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/batch.log"
}

convert_vm() {
    local VM_NAME=$1
    local VMID=$2
    local OS_TYPE=$3  # l26 o win11
    local MEMORY=$4
    local CORES=$5

    log "--- Inizio conversione: $VM_NAME ---"

    # Creare directory di output
    local VM_OUTPUT="$OUTPUT_DIR/$VM_NAME"
    mkdir -p "$VM_OUTPUT"

    # Eseguire virt-v2v
    log "Esecuzione virt-v2v per $VM_NAME..."
    if virt-v2v -v \
        -ic "$VCENTER_URI" \
        -ip "$VCENTER_PASSWORD_FILE" \
        -it vddk \
        -io vddk-libdir="$VDDK_DIR" \
        -io vddk-thumbprint="$VDDK_THUMBPRINT" \
        "$VM_NAME" \
        -o local -os "$VM_OUTPUT" \
        -of qcow2 \
        2>&1 | tee "$LOG_DIR/$VM_NAME.log"; then

        log "Conversione completata: $VM_NAME"
    else
        log "ERRORE: Conversione fallita per $VM_NAME"
        return 1
    fi

    # Trasferire a Proxmox
    log "Trasferimento a Proxmox: $VM_NAME..."
    rsync -avP "$VM_OUTPUT/${VM_NAME}-sda" \
        "$PROXMOX_HOST:/tmp/vm-import/"

    # Creare e importare su Proxmox
    log "Creazione VM su Proxmox: VMID=$VMID..."
    ssh "$PROXMOX_HOST" bash << REMOTE
qm create $VMID \
  --name "$VM_NAME" \
  --memory $MEMORY \
  --cores $CORES \
  --cpu host \
  --bios seabios \
  --scsihw virtio-scsi-pci \
  --net0 virtio,bridge=vmbr0 \
  --ostype $OS_TYPE \
  --agent enabled=1

qm importdisk $VMID /tmp/vm-import/${VM_NAME}-sda $PROXMOX_STORAGE
qm set $VMID --scsi0 $PROXMOX_STORAGE:vm-${VMID}-disk-0
qm set $VMID --boot order=scsi0
rm -f /tmp/vm-import/${VM_NAME}-sda
REMOTE

    # Pulizia locale
    rm -rf "$VM_OUTPUT"

    log "--- Migrazione completata: $VM_NAME (VMID: $VMID) ---"
}

# === MAIN ===
mkdir -p "$LOG_DIR" "$OUTPUT_DIR"

VMID=$START_VMID
while IFS=',' read -r VM_NAME OS_TYPE MEMORY CORES; do
    [[ -z "$VM_NAME" || "$VM_NAME" =~ ^# ]] && continue

    if convert_vm "$VM_NAME" "$VMID" "$OS_TYPE" "$MEMORY" "$CORES"; then
        log "SUCCESS: $VM_NAME -> VMID $VMID"
    else
        log "FAILED: $VM_NAME"
    fi

    VMID=$((VMID + 1))
done < "$1"

log "=== Batch conversion completata ==="
```

File CSV di input:

```csv
# nome_vm,os_type,memory_mb,cores
web-server-01,l26,4096,4
app-server-01,l26,8192,8
win-dc-01,win11,4096,4
win-sql-01,win11,16384,8
linux-db-01,l26,16384,8
```

---

## Troubleshooting Errori Comuni

### Errore: "No operating system was found"

```bash
# Causa: virt-v2v non riesce a rilevare il sistema operativo
# Soluzione 1: Specificare la root partition manualmente
virt-v2v ... --root /dev/sda2

# Soluzione 2: Verificare il filesystem con guestfish
guestfish --ro -a /tmp/converted/disk.vmdk <<EOF
run
list-filesystems
mount /dev/sda2 /
ls /
cat /etc/os-release
EOF
```

### Errore: "VDDK library not found"

```bash
# Causa: le librerie VDDK non sono nel percorso corretto

# Verificare il percorso
ls /opt/vmware-vix-disklib-distrib/lib64/libvixDiskLib.so

# Se il file esiste ma non viene trovato:
export LD_LIBRARY_PATH=/opt/vmware-vix-disklib-distrib/lib64:$LD_LIBRARY_PATH

# Verificare la versione di VDDK sia compatibile con la versione di ESXi
# ESXi 7.x richiede VDDK 7.x o 8.x
# ESXi 8.x richiede VDDK 8.x
```

### Errore: "Authentication failure" con vCenter

```bash
# Causa: credenziali errate o formato URI sbagliato

# Formato corretto dell'URI:
# vpx://user@domain@vcenter-host/Datacenter/ESXi-host?no_verify=1

# Per utenti con caratteri speciali nel nome:
# Encodare i caratteri speciali nell'URL
# @ in username -> %40
# \ in username -> %5c (per domain\user)

# Esempio con dominio:
# vpx://DOMAIN%5Cusername@vcenter.local/DC1/esxi1?no_verify=1

# Verificare la connessione con curl:
curl -k 'https://administrator%40vsphere.local:password@vcenter.local/sdk'
```

### Errore: "Windows firstboot scripts failed"

```bash
# Causa: i driver VirtIO non sono stati installati correttamente durante la conversione

# Soluzione 1: Verificare che l'ISO VirtIO sia accessibile
ls -la /usr/share/virtio-win/virtio-win*.iso
export VIRTIO_WIN=/usr/share/virtio-win/virtio-win.iso

# Soluzione 2: Usare una versione specifica dell'ISO VirtIO
virt-v2v ... \
  --key VIRTIO_WIN=/path/to/specific/virtio-win-0.1.240.iso

# Soluzione 3: Se la conversione è completata ma i driver non funzionano:
# Avviare la VM con controller IDE temporaneo su Proxmox
# Installare manualmente i driver VirtIO dal CD-ROM
# Poi switchare a controller VirtIO/SCSI
```

### Errore: "Inspection of the guest failed"

```bash
# Causa: libguestfs non riesce ad ispezionare il guest

# Soluzione 1: Verificare che libguestfs funzioni
libguestfs-test-tool

# Soluzione 2: Usare il backend diretto
export LIBGUESTFS_BACKEND=direct

# Soluzione 3: Aggiornare libguestfs
dnf update libguestfs

# Soluzione 4: Ispezionare manualmente il disco
virt-inspector -a /path/to/disk.vmdk
```

### Errore: "Disk is too large for conversion host"

```bash
# Causa: spazio insufficiente per la conversione

# Soluzione 1: Usare una directory temporanea con più spazio
export TMPDIR=/mnt/large-storage/tmp

# Soluzione 2: Usare output su rete (NFS mount) per evitare la doppia copia
mkdir -p /mnt/nfs-output
mount -t nfs proxmox:/var/lib/vz/images /mnt/nfs-output

virt-v2v ... -o local -os /mnt/nfs-output/

# Soluzione 3: Usare thin provisioning con qcow2
virt-v2v ... -of qcow2
# qcow2 occupa solo lo spazio effettivamente utilizzato
```

### Errore: Conversione Lenta

```bash
# Causa: trasferimento non ottimizzato

# Soluzione 1: Usare VDDK per il trasferimento (molto più veloce di HTTPS)
virt-v2v ... \
  -it vddk \
  -io vddk-libdir=/opt/vmware-vix-disklib-distrib \
  -io vddk-thumbprint=XX:XX:XX:XX

# Soluzione 2: Usare NDB (Network Block Device) con nbdkit
# virt-v2v 2.x usa automaticamente nbdkit per migliorare le performance

# Soluzione 3: Per dischi con molto spazio vuoto, usare sparsify
# Dopo la conversione:
virt-sparsify --in-place /tmp/converted/VM-sda
```

---

## Limitazioni di virt-v2v

### Limitazioni Generali

| Limitazione | Dettaglio | Workaround |
|-------------|----------|------------|
| Nessun output nativo Proxmox | Non esiste `-o proxmox` | Usare `-o local` + `qm importdisk` |
| VM deve essere spenta | Non supporta conversione di VM attive | Pianificare un downtime |
| Singola VM alla volta | Non supporta conversione parallela nativa | Usare script batch con processi paralleli |
| UEFI Secure Boot Windows | Supporto limitato per Secure Boot | Disabilitare Secure Boot prima della conversione |
| Dischi RDM (Raw Device Mapping) | Non supporta dischi RDM | Convertire RDM a VMDK prima della migrazione |
| GPU passthrough | Non gestisce le configurazioni GPU | Riconfigurare manualmente dopo la conversione |
| SR-IOV network | Non migra configurazioni SR-IOV | Riconfigurare manualmente |

### Limitazioni per Windows

```
- Windows Server 2008 e precedenti: supporto molto limitato
- Dischi dinamici Windows: non supportati
- BitLocker: il disco deve essere decrittato prima della conversione
- Windows con boot da SAN: non supportato
- Licenze OEM: potrebbero richiedere riattivazione dopo la migrazione
- Antivirus con protezione kernel: potrebbero bloccare l'iniezione driver
  Consiglio: disabilitare l'antivirus prima della conversione
```

### Limitazioni per Linux

```
- Kernel custom compilati senza moduli VirtIO: conversione parziale
  Fix: compilare i moduli VirtIO prima della conversione
- Filesystem non comuni (ZFS, Btrfs con subvolume complessi): supporto limitato
- SELinux enforcing: potrebbe causare problemi post-conversione
  Fix: impostare SELinux in permissive prima della conversione, poi
  rigenerare i label con: fixfiles -F relabel
```

---

## Alternative a virt-v2v

Se virt-v2v non è adatto per il proprio scenario, le alternative includono:

| Tool | Tipo | Pro | Contro |
|------|------|-----|--------|
| qemu-img convert | CLI gratuito | Semplice, veloce, universale | Nessuna iniezione driver |
| Clonezilla | Live ISO gratuito | Block-level, affidabile | Nessuna automazione |
| NAKIVO | Commerciale | Supporto nativo Proxmox | Licenza costosa |
| Veeam | Commerciale | Feature complete | Licenza costosa |
| Manual conversion | Nessun tool | Controllo totale | Molto tempo e competenze |

---

## Best Practice

1. **Usare sempre una distribuzione RHEL-based** come conversion host per virt-v2v
2. **Installare VDDK** per velocizzare i trasferimenti da VMware di 3-5x
3. **Testare la conversione** su VM non critiche prima di procedere con la produzione
4. **Verificare i log** (`/var/log/virt-v2v-*.log`) in caso di errori
5. **Pre-installare i driver VirtIO** su Windows prima della conversione quando possibile
6. **Consolidare gli snapshot** VMware prima della conversione
7. **Allocare spazio temporaneo sufficiente** (2x dimensione disco) sul conversion host
8. **Mantenere aggiornato** virt-v2v e libguestfs per avere il miglior supporto
9. **Documentare il mapping** tra VMID VMware e VMID Proxmox
10. **Parallelizzare con cautela**: eseguire massimo 2-3 conversioni simultanee per evitare saturazione I/O

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — `virt-v2v-in-place`.** Esiste un comando minore `virt-v2v-in-place` che converte un VMDK gia copiato sul target *senza* riconvertire l'immagine intera. E utile quando hai gia trasferito il disco con `rsync` o `qemu-img convert` e vuoi solo ri-iniettare i driver VirtIO e fixare il bootloader. Tipica linea: `virt-v2v-in-place -i libvirtxml domain.xml`. Riferimento: man page `virt-v2v-in-place(1)` su `https://libguestfs.org/`.

> **Errore comune — "inspection could not detect OS".** Sintomo: virt-v2v fallisce subito sul disco con questo messaggio. Cause: (a) il VMDK e parziale o corrotto; (b) l'OS guest e crittato (LUKS, BitLocker); (c) e un disco dati senza OS; (d) e un layout LVM/ZFS dentro partizione sconosciuto a libguestfs. Soluzione: provare `virt-inspector -a disk.vmdk` per debug. Per crittato: rimuovere la cifratura prima della migrazione, oppure migrare manualmente via qemu-img + ricreare la VM con OS reinstallato.

> **Caso reale — Driver VirtIO mancante per Windows Server 2008 R2.** virt-v2v 2.x non include piu i driver virtio-win firmati per OS legacy come Windows Server 2003/2008. Sintomo: BSOD `0x0000007B INACCESSIBLE_BOOT_DEVICE` al primo boot. Soluzione: scaricare manualmente la versione legacy di `virtio-win-stable.iso` (o build custom) e usare il flag `--install /path/to/virtio-win-legacy.iso`. Per Windows Server 2003 e prima, considerare invece la migrazione via Clonezilla bit-per-bit + driver VirtIO installati a mano dopo, oppure (meglio) reinstallare l'OS supportato e migrare i dati e la app.

---

## Esercizi

1. **Concettuale — input mode mistery.** Per ogni scenario, scegliere il flag `-i` corretto: (a) hai accesso SSH al vCenter ma non ad ESXi diretto; (b) hai un file `.ova` esportato in precedenza; (c) hai un disco VMDK isolato senza OVF; (d) hai una VM Hyper-V con file `.vhdx`. *Risposte:* (a) `-i vmx -ic vpx://...`; (b) `-i ova file.ova`; (c) `-i disk file.vmdk`; (d) `-i disk file.vhdx` (virt-v2v auto-detect formato).

2. **Lab — conversione completa di una VM Linux + script qm.** Esportare via `ovftool` una VM Debian 12 da VMware verso `/tmp/vm.ova`. Convertirla con `virt-v2v -i ova /tmp/vm.ova -o local -os /tmp/output -of qcow2`. Quindi eseguire script Bash che (a) legge il `vm.xml` generato per estrarre RAM e CPU; (b) `qm create <next-id> --memory <X> --cores <Y> --cpu host --net0 virtio,bridge=vmbr0 --scsihw virtio-scsi-single`; (c) `qm importdisk <id> /tmp/output/vm-disk1.qcow2 local-lvm`; (d) `qm set <id> --scsi0 local-lvm:vm-<id>-disk-0,iothread=1,discard=on --boot order=scsi0 --agent enabled=1`; (e) `qm start`. Documentare tempi.

3. **Scenario — VirtIO injection fallita per registry corrotto.** Una VM Windows Server 2019 da migrare risulta con BSOD post-conversione. Ipotesi: il registry e stato corrotto da una crash dell'host VMware in passato, e virt-v2v non riesce a iniettare i driver VirtIO perche non puo modificare il registry corrotto. Argomenta in 10 righe come procedere: (a) eseguire chkdsk sul VMDK source pre-conversione; (b) avviare la VM su VMware in safe mode, riparare il registry, poi rifare la conversione; (c) come fallback, montare il disk convertito su una VM Linux con `guestmount` e iniettare manualmente i driver/edit registry con `virt-win-reg`.

4. **Stretch — batch parallelism con flock.** Estendere lo script di batch del modulo per supportare parallelismo controllato via `flock`: massimo 2 conversioni in parallelo, nuove conversioni in coda. Output JSON line-delimited per integrazione con strumenti di pipeline. Aggiungere logica di "skip if already done" per ripartenza idempotente.

## Auto-valutazione

1. Pacchetto Debian/Ubuntu da installare per avere `virt-v2v` + driver VirtIO Windows?
2. Differenza fra `-i vmx` e `-i ova` come modalita di input?
3. Cosa fa il flag `--root first` e quando serve?
4. Quale comando di virt-v2v si usa per convertire una VM gia esportata in OVA?
5. virt-v2v installa automaticamente `qemu-guest-agent`? Se si, sempre? Se no, come si forza?
6. Che differenza c'e tra `-o local` e `-o qemu` come output mode?
7. Come si forza l'iniezione di un driver virtio-win specifico (es. `viostor` per Windows 2008)?
8. Cosa fa `virt-inspector -a disk.vmdk`?

## Letture primarie consigliate

- [`V2V-MAN`] virt-v2v(1). https://libguestfs.org/virt-v2v.1.html
- [`V2V-INPUT`] virt-v2v-input-vmware(1). https://libguestfs.org/virt-v2v-input-vmware.1.html
- [`V2V-OUTPUT`] virt-v2v-output-local(1). https://libguestfs.org/virt-v2v-output-local.1.html
- virt-inspector(1). https://libguestfs.org/virt-inspector.1.html
- virt-win-reg(1) — modificare registry Windows da Linux. https://libguestfs.org/virt-win-reg.1.html
- guestmount(1) — montare un disco VM da Linux. https://libguestfs.org/guestmount.1.html
- VirtIO Windows drivers (virtio-win). https://github.com/virtio-win/virtio-win-pkg-scripts
- [`PVE-MIGRATE-V2V`] Proxmox Wiki — Migration of servers. https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE

## Collegamenti incrociati

- Modulo 06.1 — `strategie-metodi-migrazione.md`: il quadro generale delle strategie.
- Modulo 06.3 — `live-migration-minimo-downtime.md`: live-migration come alternativa per workload zero-downtime.
- Modulo 08.1 — `../08-MIGRAZIONE-STORAGE/conversione-vmdk-qcow2-raw.md`: deep dive su qemu-img (alternativa a virt-v2v per disco-only).
- Modulo 09.4 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-windows-server-vm.md`: applicazione concreta su Windows Server.
- Modulo 17.2 — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-driver-e-dispositivi.md`: troubleshooting BSOD post-conversione.

## Glossario locale

| Termine | Definizione |
|---|---|
| **virt-v2v** | Tool Red Hat di conversione V2V; lavora su libguestfs e supermin. |
| **libguestfs** | Libreria + utility per accedere a immagini disco di VM da una macchina host. |
| **supermin** | Tool che costruisce un mini ambiente Linux dentro la macchina che esegue libguestfs. |
| **`-i vmx`** | Input mode: file VMX o connessione vCenter/ESXi via `-ic`. |
| **`-i ova`** | Input mode: archivio OVA (TAR con OVF + VMDK). |
| **`-i disk`** | Input mode: file disco generico (VMDK, VHD, VHDX, qcow2, raw). |
| **`-i libvirt`** | Input mode: VM gia definita in libvirt locale o remoto. |
| **`-o local`** | Output mode: scrivi disco e XML libvirt in una directory. |
| **`-o qemu`** | Output mode: produci script di lancio `qemu-system-x86_64`. |
| **`-o libvirt`** | Output mode: define la VM dentro libvirt locale. |
| **`--install`** | Forza l'iniezione di un driver/package specifico (es. `--install virtio-win`). |
| **`--root first`** | Quando virt-v2v non sa quale partizione e root, prendi la prima. |
| **`virt-inspector`** | Diagnostica: esamina un'immagine e riporta OS, partizioni, applicazioni. |
| **`virt-win-reg`** | Modifica chiavi del registry Windows dentro un'immagine disco offline. |
| **`guestmount`** | Monta filesystem di un'immagine disco su una directory dell'host. |
| **VDDK** | VMware Virtual Disk Development Kit — usato da Veeam/altro per accedere VMDK in modo nativo VMware. virt-v2v non lo richiede. |
