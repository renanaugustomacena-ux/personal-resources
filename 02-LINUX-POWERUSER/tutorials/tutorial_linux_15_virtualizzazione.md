# Tutorial Linux 15 — Virtualizzazione: KVM/QEMU, libvirt, virt-manager

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** KVM, QEMU, libvirt CLI, cloud-init, GPU passthrough, nested virtualization
> **Prerequisiti:** `tutorial_linux_14_containerizzazione.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Virtualizzazione Linux
│
├── Hardware virtualization
│   ├── Intel VT-x / AMD-V
│   ├── /dev/kvm
│   └── iommu (PCI passthrough)
│
├── KVM (Kernel-based Virtual Machine)
│   ├── Modulo kernel (kvm, kvm_intel/kvm_amd)
│   └── Hypervisor tipo 1 integrato
│
├── QEMU
│   ├── Emulazione hardware
│   ├── Virtio (paravirtualizzazione)
│   └── SPICE/VNC per accesso grafico
│
├── libvirt — API unificata
│   ├── virsh — CLI
│   ├── virt-manager — GUI
│   ├── virt-install — crea VM
│   └── /etc/libvirt/qemu/
│
└── Casi d'uso avanzati
    ├── cloud-init — provisioning automatico
    ├── GPU passthrough
    ├── Nested virtualization (VM dentro VM)
    └── Snapshot e cloning
```

---

# Parte A — Setup KVM

---

## A1. Verifica e installazione

```bash
# Verifica supporto hardware
grep -E "(vmx|svm)" /proc/cpuinfo
# vmx = Intel VT-x, svm = AMD-V
# Se vuoto: virtualizzazione non supportata o disabilitata in BIOS

# IOMMU per PCI passthrough
dmesg | grep -e DMAR -e IOMMU
# Se assente: abilita intel_iommu=on o amd_iommu=on in GRUB

# Verifica KVM
kvm-ok
# KVM acceleration can be used

ls -la /dev/kvm
# crw-rw---- 1 root kvm 10, 232 /dev/kvm

# Installazione Ubuntu/Debian
apt install -y \
    qemu-kvm \
    libvirt-daemon-system \
    libvirt-clients \
    bridge-utils \
    virt-manager \
    virtinst \
    libosinfo-bin

# Aggiungi utente al gruppo kvm e libvirt
usermod -aG kvm,libvirt $USER
# Rilogga per applicare

# Avvia e abilita libvirtd
systemctl enable --now libvirtd

# Verifica
virsh version
virsh nodeinfo
```

---

## A2. Crea prima VM con virt-install

```bash
# Scarica immagine cloud Ubuntu
wget -O /var/lib/libvirt/images/ubuntu-22.04-server-cloudimg-amd64.img \
    https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img

# Espandi immagine a 20GB
qemu-img resize /var/lib/libvirt/images/ubuntu-22.04-server-cloudimg-amd64.img 20G

# VM con cloud-init (no installer interattivo)
# 1. Crea user-data
cat > /tmp/user-data << 'EOF'
#cloud-config
hostname: ubuntu-vm
users:
  - name: mario
    groups: sudo
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ssh-ed25519 AAAA... mario@laptop
packages:
  - nginx
  - htop
runcmd:
  - systemctl enable --now nginx
EOF

# 2. Crea meta-data
cat > /tmp/meta-data << 'EOF'
instance-id: ubuntu-vm-001
local-hostname: ubuntu-vm
EOF

# 3. Crea ISO cloud-init
genisoimage -output /tmp/cloud-init.iso -volid cidata -joliet -rock \
    /tmp/user-data /tmp/meta-data

# 4. Crea VM
virt-install \
    --name ubuntu-vm \
    --ram 2048 \
    --vcpus 2 \
    --os-variant ubuntu22.04 \
    --disk /var/lib/libvirt/images/ubuntu-22.04-server-cloudimg-amd64.img,bus=virtio \
    --disk /tmp/cloud-init.iso,device=cdrom \
    --network bridge=virbr0,model=virtio \
    --graphics none \
    --console pty,target_type=serial \
    --noautoconsole \
    --import

# Monitora avvio
virsh console ubuntu-vm    # Ctrl+] per uscire
```

> **Analogia:** KVM è come avere un secondo computer dentro il primo, ma condividono la stessa CPU fisica grazie alle istruzioni di virtualizzazione hardware. libvirt è il responsabile della sala server virtuale — gestisce le VM come il management del datacenter gestisce i server fisici. `virsh` è il pannello di controllo CLI, `virt-manager` è la sua versione grafica.

---

# Parte B — virsh: gestione VM da CLI

---

## B1. Operazioni quotidiane virsh

```bash
# Lista VM
virsh list              # VM in esecuzione
virsh list --all        # tutte (anche spente)

# Avvia/ferma
virsh start ubuntu-vm
virsh shutdown ubuntu-vm    # ACPI shutdown (elegante)
virsh destroy ubuntu-vm     # forza stop (come staccare la spina)
virsh reboot ubuntu-vm
virsh suspend ubuntu-vm     # pause
virsh resume ubuntu-vm

# Autostart al boot
virsh autostart ubuntu-vm
virsh autostart ubuntu-vm --disable

# Info e risorse
virsh dominfo ubuntu-vm
virsh domstats ubuntu-vm
virsh dommemstat ubuntu-vm

# Console
virsh console ubuntu-vm
# Uscita: Ctrl+]

# Modifica XML configurazione
virsh edit ubuntu-vm        # apre XML in $EDITOR

# Dump XML
virsh dumpxml ubuntu-vm > ubuntu-vm.xml
virsh define ubuntu-vm.xml  # ricrea VM da XML

# Snapshot
virsh snapshot-create-as ubuntu-vm --name "pre-upgrade" \
    --description "Prima dell'upgrade a 24.04"
virsh snapshot-list ubuntu-vm
virsh snapshot-revert ubuntu-vm pre-upgrade
virsh snapshot-delete ubuntu-vm pre-upgrade
```

---

## B2. Storage e reti

```bash
# Pool storage
virsh pool-list --all
virsh pool-define-as default dir --target /var/lib/libvirt/images
virsh pool-autostart default
virsh pool-start default

# Volume
virsh vol-list default
virsh vol-create-as default disco-extra.qcow2 20G --format qcow2
virsh vol-info --pool default disco-extra.qcow2

# Aggiungi disco a VM
virsh attach-disk ubuntu-vm \
    /var/lib/libvirt/images/disco-extra.qcow2 \
    vdb --driver qemu --subdriver qcow2 --persistent

# Reti virtuali
virsh net-list --all
virsh net-info default       # rete NAT default
virsh net-dumpxml default    # vedi configurazione
virsh net-start default
virsh net-autostart default

# Crea rete bridge custom
cat > /tmp/bridge-net.xml << 'EOF'
<network>
  <name>bridge-lan</name>
  <forward mode='bridge'/>
  <bridge name='br0'/>
</network>
EOF
virsh net-define /tmp/bridge-net.xml
virsh net-start bridge-lan
virsh net-autostart bridge-lan
```

---

# Parte C — Cloning e Template

---

## C1. Clone e golden image

```bash
# Clone VM (deve essere spenta)
virsh shutdown ubuntu-vm
virt-clone \
    --original ubuntu-vm \
    --name ubuntu-vm-clone \
    --auto-clone

# Clona con disco specifico
virt-clone \
    --original ubuntu-vm \
    --name nuovo-server \
    --file /var/lib/libvirt/images/nuovo-server.qcow2

# Sysprep — rimuovi ID specifici dell'istanza (per template)
# apt install libguestfs-tools
virt-sysprep -d ubuntu-vm

# Resize disk (spenta)
qemu-img info ubuntu-vm.qcow2
qemu-img resize ubuntu-vm.qcow2 +10G
virsh start ubuntu-vm
# Dentro la VM:
# growpart /dev/vda 1
# resize2fs /dev/vda1

# Convert formati
qemu-img convert -f vmdk -O qcow2 vmware.vmdk linux.qcow2
qemu-img convert -f qcow2 -O raw immagine.qcow2 immagine.raw
```

---

# Parte D — Configurazione avanzata

---

## D1. CPU pinning e NUMA

```bash
# CPU pinning: assegna vCPU a core fisici specifici
virsh vcpuinfo ubuntu-vm
virsh vcpupin ubuntu-vm 0 4     # vCPU 0 → core fisico 4
virsh vcpupin ubuntu-vm 1 5     # vCPU 1 → core fisico 5

# In XML:
# <vcpus placement='static'>4</vcpus>
# <cputune>
#   <vcpupin vcpu='0' cpuset='4'/>
#   <vcpupin vcpu='1' cpuset='5'/>
# </cputune>

# Memory balloon
virsh setmem ubuntu-vm 4G --live     # aumenta RAM a caldo
virsh setmem ubuntu-vm 2G --live     # riduci

# Nested virtualization (VM dentro VM)
# Abilita nel modulo kernel
echo "options kvm_intel nested=1" > /etc/modprobe.d/kvm.conf
modprobe -r kvm_intel && modprobe kvm_intel

# Verifica
cat /sys/module/kvm_intel/parameters/nested
# Y

# In XML della VM host:
# <cpu mode='host-passthrough'>
#   <feature policy='require' name='vmx'/>
# </cpu>
```

---

# Parte E — Riepilogo

## Ciclo di vita VM

```bash
# Crea
virt-install --name vm1 --ram 2048 --vcpus 2 \
    --disk size=20 --cdrom /path/to/iso.iso

# Gestisci
virsh start/shutdown/reboot/destroy vm1
virsh suspend/resume vm1
virsh autostart vm1

# Snapshot
virsh snapshot-create-as vm1 "nome-snapshot"
virsh snapshot-revert vm1 "nome-snapshot"

# Clona
virt-clone --original vm1 --name vm1-clone --auto-clone

# Rimuovi
virsh shutdown vm1
virsh undefine vm1 --remove-all-storage
```

## Quick reference

| Comando | Scopo |
|---|---|
| `virsh list --all` | Tutte le VM |
| `virsh start nome` | Avvia |
| `virsh shutdown nome` | Spegni |
| `virsh console nome` | Console seriale |
| `virsh edit nome` | Modifica configurazione |
| `virsh snapshot-create-as nome snap1` | Crea snapshot |
| `virt-clone` | Clona VM |
| `qemu-img info` | Info immagine disco |

## Prossimi passi

- `tutorial_linux_16_backup.md` — rsync, borgbackup, restic
- `tutorial_linux_14_containerizzazione.md` — container vs VM
