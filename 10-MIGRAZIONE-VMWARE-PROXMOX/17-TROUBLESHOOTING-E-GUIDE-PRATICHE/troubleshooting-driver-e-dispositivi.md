# Troubleshooting Driver e Dispositivi

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 7 — Day-2 operations · Modulo 17.2 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 09.4 (Windows VM migration); concetti VirtIO, BSOD codes, Linux kernel modules.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. diagnosticare BSOD Windows post-migrazione (0x7B INACCESSIBLE_BOOT_DEVICE, 0x50, 0xA);
> 2. risolvere driver mancanti/conflict via offline registry edit (`hivex`, `chntpw`) o Windows Recovery Environment;
> 3. troubleshooting driver Linux (kernel module non caricato, virtio-net non riconosciuto, dispositivi `Unknown` in `lspci`);
> 4. usare strumenti diagnostici: `dmesg`, `journalctl -k`, `lspci -vv`, `lsmod`, `pnputil` (Windows).
> **Tempo stimato:** lettura 60 min · uso reattivo durante migrazione
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27

## Idee guida

1. **BSOD 0x7B = driver vioscsi non installato pre-migrazione.** Il fix piu comune: offline registry edit per impostare `Start=0` su vioscsi/viostor.
2. **Linux post-migrazione e quasi sempre un'esperienza pulita.** Il kernel ha modulare driver loading; raramente serve intervento. Eccezioni: dispositivi PCI passthrough con drivers proprietari.
3. **dmesg al primo boot e oro.** Salvare `dmesg > /tmp/first-boot-dmesg.log` immediatamente dopo il primo avvio post-migrazione: contiene la storia completa del bring-up dei device.

---

## Indice

1. [Panoramica dei Problemi di Driver Post-Migrazione](#panoramica)
2. [VirtIO Driver per Windows](#virtio-driver-per-windows)
3. [Installazione Driver VirtIO Pre-Migrazione su VMware](#installazione-pre-migrazione)
4. [Installazione Driver VirtIO Post-Migrazione](#installazione-post-migrazione)
5. [Red Hat VirtIO ISO: Struttura e Versioni](#red-hat-virtio-iso)
6. [Linux: Moduli VirtIO del Kernel](#linux-moduli-virtio)
7. [QEMU Guest Agent](#qemu-guest-agent)
8. [Display Driver: QXL vs VGA vs VirtIO-GPU](#display-driver)
9. [Risoluzione Problemi Specifici per Driver](#risoluzione-problemi-specifici)
10. [Automazione Installazione Driver](#automazione-installazione-driver)

---

## Panoramica dei Problemi di Driver Post-Migrazione {#panoramica}

La migrazione da VMware a Proxmox comporta un cambio radicale dell'hardware virtuale presentato al sistema operativo guest. VMware espone dispositivi specifici (vmxnet3, PVSCSI, VMware SVGA) che richiedono i VMware Tools, mentre Proxmox/KVM espone dispositivi VirtIO paravirtualizzati o dispositivi emulati standard.

I driver VirtIO sono essenziali per ottenere prestazioni ottimali su Proxmox. Senza di essi, la VM funzionera con driver emulati (IDE, e1000, VGA standard) che offrono prestazioni significativamente inferiori.

### Mappatura Dispositivi VMware -> Proxmox

| Componente | VMware | Proxmox (Emulato) | Proxmox (VirtIO) |
|---|---|---|---|
| Storage Controller | LSI Logic / PVSCSI | LSI / SATA / IDE | VirtIO SCSI / VirtIO Block |
| Network Adapter | vmxnet3 / e1000 | e1000 / rtl8139 | VirtIO Net (virtio-net-pci) |
| Display | VMware SVGA | VGA standard | QXL / VirtIO-GPU |
| Memory Balloon | VMware balloon | - | VirtIO Balloon |
| Serial Port | vmware-serial | 16550A UART | virtio-serial |
| RNG | - | - | VirtIO RNG |

---

## VirtIO Driver per Windows {#virtio-driver-per-windows}

### Driver Disponibili nell'ISO VirtIO

L'ISO `virtio-win` contiene i seguenti driver per Windows:

| Driver | Nome File | Funzione | Priorita |
|---|---|---|---|
| **viostor** | viostor.sys | Block storage driver (VirtIO block device) | Critico |
| **vioscsi** | vioscsi.sys | SCSI storage driver (VirtIO SCSI) | Critico |
| **NetKVM** | netkvm.sys | Network driver (VirtIO-net) | Alto |
| **Balloon** | balloon.sys | Memory balloon driver | Medio |
| **qxl** / **qxldod** | qxl.sys / qxldod.sys | Display driver QXL | Medio |
| **vioserial** | vioser.sys | Serial port driver | Basso |
| **viorng** | viorng.sys | Random number generator | Basso |
| **vioinput** | vioinput.sys | Input driver | Basso |
| **viofs** | viofs.sys | Filesystem sharing (virtiofs) | Opzionale |
| **pvpanic** | pvpanic.sys | PV panic device | Opzionale |
| **viogpudo** | viogpudo.sys | VirtIO-GPU display driver | Opzionale |
| **fwcfg** | fwcfg.sys | Firmware configuration | Opzionale |
| **sriov** | vioprot.sys | SR-IOV network driver | Opzionale |

### Struttura dell'ISO VirtIO

```
virtio-win.iso/
├── Balloon/
│   ├── 2k12/         # Windows Server 2012
│   ├── 2k12R2/       # Windows Server 2012 R2
│   ├── 2k16/         # Windows Server 2016
│   ├── 2k19/         # Windows Server 2019
│   ├── 2k22/         # Windows Server 2022
│   ├── 2k25/         # Windows Server 2025
│   ├── w10/           # Windows 10
│   ├── w11/           # Windows 11
│   └── w8.1/          # Windows 8.1
│       ├── amd64/     # Driver 64-bit
│       └── x86/       # Driver 32-bit (dove disponibile)
├── NetKVM/
│   └── (stessa struttura)
├── viostor/
│   └── (stessa struttura)
├── vioscsi/
│   └── (stessa struttura)
├── qxl/ o qxldod/
│   └── (stessa struttura)
├── guest-agent/
│   ├── qemu-ga-x86_64.msi    # Installer 64-bit
│   └── qemu-ga-i386.msi      # Installer 32-bit
├── virtio-win-gt-x64.msi     # Installer completo 64-bit
├── virtio-win-gt-x86.msi     # Installer completo 32-bit
└── virtio-win-guest-tools.exe # Installer GUI
```

### Scaricare l'ISO VirtIO

```bash
# Versione stabile (consigliata per produzione)
wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso

# Versione latest (piu aggiornata)
wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/latest-virtio/virtio-win.iso

# Caricare su Proxmox
scp virtio-win.iso root@proxmox:/var/lib/vz/template/iso/

# Oppure scaricare direttamente sul nodo Proxmox
cd /var/lib/vz/template/iso/
wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso
```

---

## Installazione Driver VirtIO Pre-Migrazione su VMware {#installazione-pre-migrazione}

L'approccio migliore e installare i driver VirtIO **prima** della migrazione, mentre la VM e ancora in esecuzione su VMware. Questo previene completamente i problemi di boot post-migrazione.

### Procedura per Windows su VMware

**Passo 1: Montare l'ISO VirtIO sulla VM VMware**

Su vCenter o ESXi, collegare l'ISO `virtio-win.iso` come CD-ROM alla VM.

**Passo 2: Installare tutti i driver**

```powershell
# Opzione A: Installer GUI
# Eseguire D:\virtio-win-guest-tools.exe (dove D: e il CD-ROM)
# L'installer installa tutti i driver e il QEMU Guest Agent

# Opzione B: Installer MSI (silenzioso, per automazione)
msiexec /i D:\virtio-win-gt-x64.msi /quiet /norestart

# Opzione C: Installazione manuale driver per driver
# Aprire Device Manager
# Per ogni driver: Action > Add legacy hardware > Install from disk
# Navigare alla cartella corretta sull'ISO
```

**Passo 3: Verificare che i driver siano installati**

```powershell
# PowerShell: verificare i driver VirtIO installati
Get-WindowsDriver -Online | Where-Object {$_.ProviderName -like "*Red Hat*"} |
    Select-Object Driver, ClassName, ProviderName, Date, Version

# Output atteso (esempio):
# Driver       ClassName    ProviderName     Date       Version
# ------       ---------    ------------     ----       -------
# oem5.inf     SCSIAdapter  Red Hat, Inc.    2024-01-15 100.85.104.17300
# oem6.inf     Net          Red Hat, Inc.    2024-01-15 100.85.104.17300
# oem7.inf     System       Red Hat, Inc.    2024-01-15 100.85.104.17300
```

**Passo 4: Forzare Windows a caricare i driver VirtIO al boot**

Questo passo e cruciale. Anche dopo l'installazione, Windows potrebbe non caricare i driver VirtIO al boot se non ha mai visto un dispositivo VirtIO.

```powershell
# Impostare i driver VirtIO per l'avvio automatico nel registry
# viostor (block storage)
reg add "HKLM\SYSTEM\CurrentControlSet\Services\viostor" /v Start /t REG_DWORD /d 0 /f

# vioscsi (SCSI storage)
reg add "HKLM\SYSTEM\CurrentControlSet\Services\vioscsi" /v Start /t REG_DWORD /d 0 /f

# Valori Start:
# 0 = Boot (caricato all'avvio del sistema - necessario per driver storage)
# 1 = System (caricato dal kernel)
# 2 = Automatic (caricato dal Service Control Manager)
# 3 = Manual (caricato su richiesta)
# 4 = Disabled
```

**Passo 5: Rimuovere VMware Tools (opzionale ma consigliato)**

```powershell
# Disinstallare VMware Tools prima della migrazione
# Da Pannello di Controllo > Programmi > Disinstalla VMware Tools
# Oppure:
MsiExec.exe /x {GUID-of-VMwareTools} /quiet /norestart

# Trovare il GUID:
Get-WmiObject -Class Win32_Product | Where-Object {$_.Name -like "*VMware*"} |
    Select-Object Name, IdentifyingNumber
```

### Procedura per Linux su VMware

Per Linux, i moduli VirtIO sono gia inclusi nella maggior parte dei kernel moderni. La preparazione consiste nel verificare che siano disponibili e inclusi nell'initramfs.

```bash
# Verificare i moduli VirtIO disponibili
find /lib/modules/$(uname -r) -name "virtio*" -type f

# Verificare che siano caricabili
modprobe -n -v virtio_blk
modprobe -n -v virtio_scsi
modprobe -n -v virtio_net
modprobe -n -v virtio_pci

# Aggiungere all'initramfs (Debian/Ubuntu)
cat >> /etc/initramfs-tools/modules << 'EOF'
virtio_pci
virtio_blk
virtio_scsi
virtio_net
virtio_balloon
virtio_console
EOF
update-initramfs -u -k all

# Aggiungere all'initramfs (RHEL/CentOS/Rocky)
cat > /etc/dracut.conf.d/virtio.conf << 'EOF'
add_drivers+=" virtio_pci virtio_blk virtio_scsi virtio_net virtio_balloon virtio_console "
EOF
dracut --force --regenerate-all

# Rimuovere open-vm-tools (opzionale, da fare dopo la migrazione)
# apt remove open-vm-tools open-vm-tools-desktop  # Debian/Ubuntu
# yum remove open-vm-tools open-vm-tools-desktop  # RHEL/CentOS
```

---

## Installazione Driver VirtIO Post-Migrazione {#installazione-post-migrazione}

Se i driver VirtIO non sono stati installati prima della migrazione, e necessario procedere con metodi alternativi.

### Windows: Avvio in Safe Mode

Se Windows non si avvia a causa di driver storage mancanti, procedere come segue:

**Passo 1: Configurare la VM con hardware compatibile**

```bash
# Usare controller SATA (non richiede driver aggiuntivi)
qm set <vmid> -sata0 local-lvm:vm-<vmid>-disk-0,size=50G
qm set <vmid> -delete scsi0
qm set <vmid> -boot order=sata0

# Usare scheda di rete e1000 (non richiede driver)
qm set <vmid> -net0 e1000,bridge=vmbr0

# Montare l'ISO VirtIO come CD-ROM
qm set <vmid> -ide2 local:iso/virtio-win.iso,media=cdrom
```

**Passo 2: Avviare Windows e installare i driver**

```powershell
# Dopo l'avvio, l'ISO sara visibile come CD-ROM (es. D:)
# Opzione rapida: eseguire l'installer
D:\virtio-win-guest-tools.exe

# Oppure installer silenzioso:
msiexec /i D:\virtio-win-gt-x64.msi /quiet /norestart

# Oppure installare manualmente da Device Manager:
# 1. Aprire Device Manager (devmgmt.msc)
# 2. Per dispositivi con punto esclamativo giallo:
#    Right-click > Update driver > Browse my computer
#    Selezionare D:\ e attivare "Include subfolders"
#    Windows trovera automaticamente il driver corretto
```

**Passo 3: Verificare e riconfigurare la VM**

```bash
# Dopo l'installazione dei driver, spegnere Windows
qm stop <vmid>

# Riconfigurare con VirtIO per prestazioni ottimali
qm set <vmid> -scsi0 local-lvm:vm-<vmid>-disk-0,size=50G
qm set <vmid> -delete sata0
qm set <vmid> -scsihw virtio-scsi-single
qm set <vmid> -boot order=scsi0

# Cambiare la scheda di rete a VirtIO
qm set <vmid> -net0 virtio,bridge=vmbr0

# Avviare e verificare che tutto funzioni
qm start <vmid>
```

### Windows: Recovery Environment

Se non e possibile avviare Windows nemmeno con SATA:

```bash
# Montare il DVD di installazione Windows
qm set <vmid> -ide2 local:iso/windows-server-2022.iso,media=cdrom
qm set <vmid> -boot order=ide2
```

```cmd
REM Nel Recovery Environment:
REM Prompt dei comandi

REM Caricare i driver VirtIO dal secondo CD-ROM (montare anche l'ISO VirtIO)
REM Se possibile, montare l'ISO VirtIO come secondo CD-ROM

REM Iniettare il driver con DISM
dism /image:C:\ /add-driver /driver:E:\vioscsi\2k22\amd64 /recurse
dism /image:C:\ /add-driver /driver:E:\viostor\2k22\amd64 /recurse
dism /image:C:\ /add-driver /driver:E:\NetKVM\2k22\amd64 /recurse
dism /image:C:\ /add-driver /driver:E:\Balloon\2k22\amd64 /recurse

REM Verificare
dism /image:C:\ /get-drivers /format:table
```

### Linux: Aggiungere Moduli Post-Migrazione

Se Linux non si avvia per mancanza di moduli VirtIO:

```bash
# Avviare da live CD (Ubuntu/Debian live)
# Il live CD dovrebbe avviarsi senza problemi

# Identificare le partizioni del disco migrato
lsblk -f
fdisk -l /dev/vda

# Montare il filesystem root
mount /dev/vda2 /mnt     # Adattare la partizione
mount /dev/vda1 /mnt/boot  # Se separata

# Bind mount
mount --bind /dev /mnt/dev
mount --bind /proc /mnt/proc
mount --bind /sys /mnt/sys
mount --bind /run /mnt/run

# Chroot
chroot /mnt /bin/bash

# Verificare e aggiungere moduli
# Debian/Ubuntu:
dpkg -l | grep linux-image  # Verificare il kernel installato
echo -e "virtio_pci\nvirtio_blk\nvirtio_scsi\nvirtio_net" >> /etc/initramfs-tools/modules
update-initramfs -u -k all

# RHEL/CentOS/Rocky:
rpm -qa | grep kernel  # Verificare il kernel installato
echo 'add_drivers+=" virtio_pci virtio_blk virtio_scsi virtio_net "' > /etc/dracut.conf.d/virtio.conf
dracut --force --regenerate-all

# Uscire e riavviare
exit
umount -R /mnt
reboot
```

---

## Red Hat VirtIO ISO: Struttura e Versioni {#red-hat-virtio-iso}

### Versioni dell'ISO e Compatibilita

| Versione ISO | Data | Driver Version | Windows Supportati |
|---|---|---|---|
| virtio-win-0.1.240 | 2024-01 | 100.85.104 | Win 8.1 - Win 11, Server 2012 R2 - 2025 |
| virtio-win-0.1.229 | 2023-06 | 100.83.104 | Win 8.1 - Win 11, Server 2012 R2 - 2022 |
| virtio-win-0.1.225 | 2023-03 | 100.82.104 | Win 8.1 - Win 11, Server 2012 R2 - 2022 |
| virtio-win-0.1.217 | 2022-09 | 100.80.104 | Win 7 - Win 11, Server 2008 R2 - 2022 |

### Selezione della Cartella Driver Corretta

```
Cartella nell'ISO -> Versione Windows
2k12               Windows Server 2012
2k12R2              Windows Server 2012 R2
2k16                Windows Server 2016
2k19                Windows Server 2019
2k22                Windows Server 2022
2k25                Windows Server 2025
w8                  Windows 8 (se presente)
w8.1                Windows 8.1
w10                 Windows 10
w11                 Windows 11

Sottocartella:
amd64               64-bit (la maggior parte dei sistemi moderni)
x86                 32-bit (legacy)
ARM64               ARM 64-bit (raro)
```

### Verificare la Firma dei Driver

I driver VirtIO di Red Hat sono firmati digitalmente con certificato Microsoft WHQL (Windows Hardware Quality Labs), il che significa che possono essere installati senza disabilitare la verifica delle firme.

```powershell
# Verificare la firma del driver
Get-AuthenticodeSignature "D:\viostor\w10\amd64\viostor.sys"

# Output atteso:
# Status: Valid
# SignerCertificate: CN=Microsoft Windows Hardware Compatibility Publisher
```

---

## Linux: Moduli VirtIO del Kernel {#linux-moduli-virtio}

### Moduli VirtIO Principali

| Modulo | Funzione | Dispositivo |
|---|---|---|
| `virtio_pci` | Transport PCI per VirtIO | Bus PCI |
| `virtio_blk` | Block device driver | /dev/vda, /dev/vdb... |
| `virtio_scsi` | SCSI driver | /dev/sda (via VirtIO SCSI) |
| `virtio_net` | Network driver | eth0 / ens* |
| `virtio_balloon` | Memory ballooning | Gestione memoria dinamica |
| `virtio_console` | Console seriale | /dev/hvc0 |
| `virtio_rng` | Random number generator | /dev/hwrng |
| `virtio_gpu` | GPU paravirtualizzata | Display |
| `virtio_input` | Input devices | Tastiera/Mouse |
| `virtiofs` | Filesystem sharing | Mount point condivisi |
| `virtio_ring` | VirtIO ring buffer | Infrastruttura VirtIO |
| `virtio` | Core VirtIO | Framework base |

### Verifica Stato Moduli

```bash
# Elencare tutti i moduli VirtIO caricati
lsmod | grep virtio

# Output tipico su una VM Proxmox funzionante:
# virtio_balloon         24576  0
# virtio_net             61440  0
# virtio_scsi            28672  0
# virtio_pci             28672  0
# virtio_pci_modern_dev  16384  1 virtio_pci
# virtio_pci_legacy_dev  16384  1 virtio_pci
# virtio_ring            40960  4 virtio_balloon,virtio_net,virtio_scsi,virtio_pci
# virtio                 16384  4 virtio_balloon,virtio_net,virtio_scsi,virtio_ring

# Verificare i dispositivi VirtIO rilevati
lspci | grep -i virtio

# Output tipico:
# 00:05.0 SCSI storage controller: Red Hat, Inc. Virtio SCSI
# 00:12.0 Network controller: Red Hat, Inc. Virtio network device
# 00:1a.0 Communication controller: Red Hat, Inc. Virtio console

# Verificare i dischi VirtIO
ls -la /dev/vd*        # Per VirtIO block
ls -la /dev/sd*        # Per VirtIO SCSI
```

### Caricare Moduli Mancanti

```bash
# Caricare manualmente un modulo
modprobe virtio_scsi

# Verificare che il modulo sia disponibile
modinfo virtio_scsi

# Se il modulo non esiste, verificare la configurazione kernel
grep VIRTIO /boot/config-$(uname -r)

# Configurazione minima richiesta:
# CONFIG_VIRTIO=y
# CONFIG_VIRTIO_PCI=y
# CONFIG_VIRTIO_BLK=y (o =m)
# CONFIG_SCSI_VIRTIO=m
# CONFIG_VIRTIO_NET=y (o =m)
# CONFIG_VIRTIO_BALLOON=m

# Rendere il caricamento persistente
echo "virtio_scsi" >> /etc/modules-load.d/virtio.conf
echo "virtio_net" >> /etc/modules-load.d/virtio.conf
echo "virtio_balloon" >> /etc/modules-load.d/virtio.conf
```

### Diagnostica Problemi Moduli Linux

```bash
# Errore: modulo non trovato
modprobe virtio_blk
# modprobe: FATAL: Module virtio_blk not found in directory /lib/modules/5.15.0-xxx

# Soluzione: verificare quale kernel e in esecuzione
uname -r
ls /lib/modules/

# Se il kernel installato non corrisponde, potrebbe essere necessario
# reinstallare i moduli
apt reinstall linux-modules-$(uname -r)  # Debian/Ubuntu
yum reinstall kernel-modules-$(uname -r)  # RHEL/CentOS

# Errore: modulo non si carica per dipendenze
modprobe -v virtio_scsi 2>&1
# Mostra la catena di dipendenze

# Aggiornare le dipendenze dei moduli
depmod -a
```

---

## QEMU Guest Agent {#qemu-guest-agent}

### Perche il QEMU Guest Agent e Importante

Il QEMU Guest Agent (qemu-ga) consente a Proxmox di comunicare direttamente con il sistema operativo guest, abilitando:

- **Freeze/thaw del filesystem** per snapshot consistenti
- **Ottenere informazioni** (indirizzo IP, hostname, OS version) dalla GUI Proxmox
- **Spegnimento pulito** della VM senza ACPI
- **Esecuzione comandi** dall'host al guest
- **Trim/discard** per recupero spazio su thin-provisioned storage

### Installazione su Windows

```powershell
# Metodo 1: Dal MSI nell'ISO VirtIO
msiexec /i D:\guest-agent\qemu-ga-x86_64.msi /quiet

# Metodo 2: Dall'installer completo
D:\virtio-win-guest-tools.exe
# Questo installa sia i driver che il guest agent

# Verificare che il servizio sia in esecuzione
Get-Service QEMU-GA

# Output atteso:
# Status   Name      DisplayName
# ------   ----      -----------
# Running  QEMU-GA   QEMU Guest Agent

# Se il servizio non e in esecuzione:
Start-Service QEMU-GA
Set-Service QEMU-GA -StartupType Automatic
```

### Installazione su Linux

```bash
# Debian/Ubuntu
apt update
apt install qemu-guest-agent
systemctl enable qemu-guest-agent
systemctl start qemu-guest-agent

# RHEL/CentOS/Rocky
yum install qemu-guest-agent
systemctl enable qemu-guest-agent
systemctl start qemu-guest-agent

# SUSE
zypper install qemu-guest-agent
systemctl enable qemu-guest-agent
systemctl start qemu-guest-agent

# Verificare lo stato
systemctl status qemu-guest-agent

# Verificare la comunicazione con l'host
# Dal nodo Proxmox:
qm agent <vmid> ping
qm agent <vmid> get-osinfo
qm agent <vmid> network-get-interfaces
```

### Configurazione Proxmox per il Guest Agent

```bash
# Abilitare il guest agent nella configurazione VM
qm set <vmid> -agent enabled=1

# Con opzioni aggiuntive:
qm set <vmid> -agent enabled=1,fstrim_cloned_disks=1

# Il canale seriale per il guest agent viene creato automaticamente
# Verificare che sia presente:
qm config <vmid> | grep agent

# Per il funzionamento del guest agent, la VM deve avere un canale
# virtio-serial. Proxmox lo crea automaticamente quando agent=1
```

### Troubleshooting Guest Agent

```bash
# Dal nodo Proxmox - testare la comunicazione
qm agent <vmid> ping
# Errore comune: "QEMU guest agent is not running"

# Verificare il socket
ls -la /var/run/qemu-server/<vmid>.qga

# Dal guest Linux - verificare il dispositivo seriale
ls -la /dev/virtio-ports/
# Dovrebbe mostrare org.qemu.guest_agent.0

# Verificare i log del guest agent
# Linux:
journalctl -u qemu-guest-agent --no-pager -n 50

# Windows:
# Event Viewer > Application and Services Logs > QEMU Guest Agent
# Oppure:
Get-WinEvent -LogName Application | Where-Object {$_.ProviderName -like "*QEMU*"} |
    Select-Object -First 20

# Problema: guest agent non si avvia
# Linux: verificare che il modulo virtio_console sia caricato
lsmod | grep virtio_console
modprobe virtio_console

# Riavviare il servizio
systemctl restart qemu-guest-agent
```

---

## Display Driver: QXL vs VGA vs VirtIO-GPU {#display-driver}

### Confronto Display Adapter

| Caratteristica | VGA Standard | QXL | VirtIO-GPU |
|---|---|---|---|
| Risoluzione Max | 1920x1200 | 2560x1600+ | 4K+ |
| Accelerazione 2D | No | Si | Si |
| Accelerazione 3D | No | No | Si (virgl) |
| Multi-monitor | No | Si (fino a 4) | Si |
| SPICE support | No | Ottimale | Buono |
| noVNC support | Si | Si | Si |
| Windows support | Si (nativo) | Si (con driver) | Si (con driver) |
| Linux support | Si (nativo) | Si (nativo) | Si (nativo) |
| Uso consigliato | Compatibilita | Desktop remoto | Grafica avanzata |

### Configurazione Display Adapter

```bash
# VGA Standard (massima compatibilita)
qm set <vmid> -vga std

# QXL (consigliato per desktop con SPICE)
qm set <vmid> -vga qxl
# Con memoria video personalizzata:
qm set <vmid> -vga qxl,memory=32

# VirtIO-GPU (consigliato per Linux con 3D)
qm set <vmid> -vga virtio

# VirtIO-GPU con 3D (sperimentale)
qm set <vmid> -vga virtio-gl

# Disabilitare display (server headless)
qm set <vmid> -vga none
# NOTA: perderete l'accesso alla console grafica

# SPICE con display QXL
qm set <vmid> -vga qxl
qm set <vmid> -spice1 1
```

### Installazione Driver QXL su Windows

```powershell
# Il driver QXL e incluso nell'ISO VirtIO
# Installazione dal Device Manager:
# 1. Aprire Device Manager
# 2. Espandere "Display adapters"
# 3. Right-click > Update driver
# 4. Browse > selezionare D:\qxldod\w10\amd64 (per Win 10 64-bit)

# Installazione da riga di comando:
pnputil /add-driver D:\qxldod\w10\amd64\qxldod.inf /install

# Per versioni piu vecchie (Windows 7/8):
pnputil /add-driver D:\qxl\w7\amd64\qxl.inf /install

# Verificare il driver display attivo
Get-WmiObject Win32_VideoController | Select-Object Name, DriverVersion, Status
```

### Problemi Comuni con Display

**Problema: Risoluzione bloccata a 800x600**

```bash
# Su Proxmox, aumentare la memoria video
qm set <vmid> -vga std,memory=64

# Per QXL:
qm set <vmid> -vga qxl,memory=128

# Su Windows guest: installare il driver QXL o VirtIO-GPU
# Su Linux guest: verificare che il modulo video sia caricato
lsmod | grep -E "qxl|virtio_gpu|bochs"
```

**Problema: Schermo nero con VirtIO-GPU**

```bash
# Fallback a VGA standard
qm set <vmid> -vga std

# Oppure provare QXL
qm set <vmid> -vga qxl

# Per Linux con Wayland, potrebbe essere necessario:
# Aggiungere al kernel command line: video=virtio-gpudrmfb
```

**Problema: Lag nella console noVNC**

```bash
# Ridurre la risoluzione o cambiare display adapter
qm set <vmid> -vga std

# Per SPICE (migliore per desktop remoto):
qm set <vmid> -vga qxl,memory=64
```

---

## Risoluzione Problemi Specifici per Driver {#risoluzione-problemi-specifici}

### VMware Tools Residui che Causano Conflitti

Dopo la migrazione, i VMware Tools residui possono causare instabilita.

**Windows:**

```powershell
# Disinstallare VMware Tools
# Metodo 1: da Programmi e Funzionalita
appwiz.cpl

# Metodo 2: da riga di comando
MsiExec.exe /x {GUID} /quiet
# Trovare il GUID:
Get-WmiObject Win32_Product | Where {$_.Name -like "*VMware*"}

# Metodo 3: cleanup manuale (se la disinstallazione fallisce)
# Rimuovere i servizi VMware
sc delete VMTools
sc delete vm3dservice
sc delete VMUSBArbService
sc delete VGAuthService

# Rimuovere i driver VMware
pnputil /enum-drivers | findstr /i "vmware"
pnputil /delete-driver oem<numero>.inf /uninstall /force

# Rimuovere le voci di registro
reg delete "HKLM\SOFTWARE\VMware, Inc." /f
reg delete "HKLM\SOFTWARE\WOW6432Node\VMware, Inc." /f
```

**Linux:**

```bash
# Rimuovere open-vm-tools
apt remove --purge open-vm-tools open-vm-tools-desktop  # Debian/Ubuntu
yum remove open-vm-tools open-vm-tools-desktop  # RHEL/CentOS

# Verificare che non ci siano moduli VMware residui
lsmod | grep -i vm
# Se presenti:
rmmod vmw_balloon vmw_vmci vmxnet3 vmw_pvscsi

# Bloccare il caricamento dei moduli VMware
cat > /etc/modprobe.d/blacklist-vmware.conf << 'EOF'
blacklist vmw_balloon
blacklist vmw_vmci
blacklist vmxnet3
blacklist vmw_pvscsi
blacklist vmw_vsock_vmci_transport
EOF

# Ricostruire initramfs senza moduli VMware
update-initramfs -u  # Debian/Ubuntu
dracut --force       # RHEL/CentOS
```

### Driver di Rete Non Rilevato

```bash
# Su Linux: verificare il dispositivo di rete
ip link show
lspci | grep -i net
dmesg | grep -i "net\|virtio\|eth\|ens"

# Caricare il modulo se mancante
modprobe virtio_net

# Su Windows: verificare da Device Manager
# Se il NIC ha un punto esclamativo giallo:
# Right-click > Update driver > Browse > D:\NetKVM\<version>\amd64
```

---

## Automazione Installazione Driver {#automazione-installazione-driver}

### Script PowerShell per Installazione Completa su Windows

```powershell
# install-virtio-drivers.ps1
# Eseguire come Amministratore

param(
    [string]$VirtIODrive = "D:"
)

Write-Host "=== Installazione Driver VirtIO ===" -ForegroundColor Green

# Verificare che l'ISO sia montata
if (-not (Test-Path "$VirtIODrive\virtio-win-gt-x64.msi")) {
    Write-Host "ERRORE: ISO VirtIO non trovata su $VirtIODrive" -ForegroundColor Red
    exit 1
}

# Determinare la versione di Windows
$OSVersion = (Get-WmiObject Win32_OperatingSystem).Caption
Write-Host "Sistema operativo: $OSVersion"

# Installare tutti i driver con MSI
Write-Host "Installazione driver VirtIO in corso..."
Start-Process msiexec.exe -ArgumentList "/i `"$VirtIODrive\virtio-win-gt-x64.msi`" /quiet /norestart" -Wait

# Installare il QEMU Guest Agent
Write-Host "Installazione QEMU Guest Agent..."
$GAInstaller = "$VirtIODrive\guest-agent\qemu-ga-x86_64.msi"
if (Test-Path $GAInstaller) {
    Start-Process msiexec.exe -ArgumentList "/i `"$GAInstaller`" /quiet /norestart" -Wait
}

# Verificare l'installazione
Write-Host "`n=== Verifica Driver Installati ===" -ForegroundColor Green
$drivers = Get-WindowsDriver -Online | Where-Object {$_.ProviderName -like "*Red Hat*"}
foreach ($d in $drivers) {
    Write-Host "  $($d.ClassName): $($d.Driver) - v$($d.Version)"
}

# Verificare il servizio Guest Agent
$ga = Get-Service QEMU-GA -ErrorAction SilentlyContinue
if ($ga) {
    Write-Host "`nQEMU Guest Agent: $($ga.Status)"
} else {
    Write-Host "`nATTENZIONE: QEMU Guest Agent non trovato!" -ForegroundColor Yellow
}

# Impostare driver storage per boot
Write-Host "`nImpostazione driver storage per boot..."
$services = @("viostor", "vioscsi")
foreach ($svc in $services) {
    $regPath = "HKLM:\SYSTEM\CurrentControlSet\Services\$svc"
    if (Test-Path $regPath) {
        Set-ItemProperty -Path $regPath -Name "Start" -Value 0
        Write-Host "  $svc impostato per boot start"
    }
}

Write-Host "`n=== Installazione Completata ===" -ForegroundColor Green
Write-Host "Riavviare la VM per applicare tutti i driver."
```

### Script Bash per Preparazione Linux Pre-Migrazione

```bash
#!/bin/bash
# prepare-linux-for-proxmox.sh
# Eseguire come root sulla VM Linux prima della migrazione

echo "=== Preparazione Linux per Migrazione a Proxmox ==="

# Rilevare la distribuzione
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    VERSION=$VERSION_ID
else
    echo "ERRORE: impossibile determinare la distribuzione"
    exit 1
fi

echo "Distribuzione: $DISTRO $VERSION"

# 1. Verificare moduli VirtIO
echo ""
echo "--- Verifica Moduli VirtIO ---"
MODULES="virtio_pci virtio_blk virtio_scsi virtio_net virtio_balloon"
ALL_OK=true

for mod in $MODULES; do
    if modinfo $mod &>/dev/null; then
        echo "  [OK] $mod disponibile"
    else
        echo "  [MANCANTE] $mod"
        ALL_OK=false
    fi
done

# 2. Aggiungere moduli all'initramfs
echo ""
echo "--- Aggiornamento Initramfs ---"
case $DISTRO in
    ubuntu|debian)
        for mod in $MODULES; do
            grep -q "^$mod$" /etc/initramfs-tools/modules 2>/dev/null || \
                echo "$mod" >> /etc/initramfs-tools/modules
        done
        update-initramfs -u -k all
        ;;
    centos|rhel|rocky|almalinux|fedora)
        cat > /etc/dracut.conf.d/virtio.conf << 'DRACUT'
add_drivers+=" virtio_pci virtio_blk virtio_scsi virtio_net virtio_balloon "
DRACUT
        dracut --force --regenerate-all
        ;;
    sles|opensuse*)
        cat > /etc/dracut.conf.d/virtio.conf << 'DRACUT'
force_drivers+=" virtio_pci virtio_blk virtio_scsi virtio_net virtio_balloon "
DRACUT
        dracut --force --regenerate-all
        ;;
    *)
        echo "ATTENZIONE: distribuzione $DISTRO non gestita automaticamente"
        echo "Aggiungere manualmente i moduli VirtIO all'initramfs"
        ;;
esac

# 3. Installare QEMU Guest Agent
echo ""
echo "--- Installazione QEMU Guest Agent ---"
case $DISTRO in
    ubuntu|debian)
        apt-get install -y qemu-guest-agent
        ;;
    centos|rhel|rocky|almalinux|fedora)
        yum install -y qemu-guest-agent
        ;;
    sles|opensuse*)
        zypper install -y qemu-guest-agent
        ;;
esac

# 4. Rimuovere VMware Tools (opzionale)
echo ""
echo "--- Rimozione VMware Tools ---"
case $DISTRO in
    ubuntu|debian)
        apt-get remove -y open-vm-tools open-vm-tools-desktop 2>/dev/null
        ;;
    centos|rhel|rocky|almalinux|fedora)
        yum remove -y open-vm-tools open-vm-tools-desktop 2>/dev/null
        ;;
    sles|opensuse*)
        zypper remove -y open-vm-tools open-vm-tools-desktop 2>/dev/null
        ;;
esac

# 5. Pulire regole udev per interfacce di rete
echo ""
echo "--- Pulizia Regole udev ---"
rm -f /etc/udev/rules.d/70-persistent-net.rules
rm -f /etc/udev/rules.d/75-persistent-net-generator.rules

echo ""
echo "=== Preparazione Completata ==="
echo "La VM e pronta per la migrazione a Proxmox."
echo "Dopo la migrazione, verificare che tutti i dispositivi funzionino correttamente."
```

Questi script possono essere adattati alle specifiche esigenze dell'ambiente e integrati nei runbook di migrazione per standardizzare il processo di preparazione e installazione dei driver.

---

## Letture primarie consigliate

- Microsoft Learn — Troubleshoot stop error 0x7B. https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/stop-error-0x7b-after-you-move-windows-to-a-new-hard-drive (retrieved 2026-04-27).
- libguestfs/hivex — offline Windows registry editing. https://github.com/libguestfs/hivex (retrieved 2026-04-27).
- Linux kernel — Module documentation. https://www.kernel.org/doc/html/latest/kbuild/modules.html (retrieved 2026-04-27).
- Proxmox VE Wiki — Windows VirtIO Drivers. https://pve.proxmox.com/wiki/Windows_VirtIO_Drivers (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 09.4 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-windows-server-vm.md`: pre-migration prep.
- Modulo 17.3 — `troubleshooting-networking-post-migrazione.md`: driver di rete.
