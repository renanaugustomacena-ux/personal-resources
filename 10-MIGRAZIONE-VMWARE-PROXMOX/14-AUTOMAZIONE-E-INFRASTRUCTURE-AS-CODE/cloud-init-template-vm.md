# Cloud-init e Template VM su Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 5 — Operativita post-migrazione · Modulo 14.1 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** Proxmox cluster operativo; cloud-init concepts (user-data, meta-data, network-config); YAML basics; familiarita con cloud images Debian/Ubuntu/CentOS.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. creare **template VM** Proxmox da cloud images ufficiali (debian-12-genericcloud-amd64.qcow2, ubuntu-22.04-server-cloudimg-amd64.img); applicare hardening (no SSH password, fail2ban, auto-updates security);
> 2. configurare **cloud-init drive** in Proxmox (`qm set --ide2 storage:cloudinit`) e popolare user-data, meta-data, network-config via snippet o variabili Proxmox built-in;
> 3. eseguire **deploy automatizzato** di nuove VM tramite clone di template + cloud-init customization (IP, hostname, SSH keys, packages);
> 4. integrare con **firma digitale e supply-chain provenance** (sigstore/cosign per template signing, SBOM CycloneDX);
> 5. gestire un **template lifecycle**: build periodico, signing, distribution, rotation;
> 6. confrontare con **VMware Guest Customization Specification** (limited, GUI-driven) vs cloud-init (powerful, code-driven, vendor-agnostic).
> **Tempo stimato:** lettura 60-90 min · lab 240-300 min (template + clone + cloud-init customization)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; cloud-init 23.x/24.x; cloudbase-init 1.1+ (Windows); cosign 2.x.

## Mappa concettuale

```
+============================================================+
|     Cloud-init template flow                                |
+============================================================+
|                                                            |
|   1. BUILD TEMPLATE                                        |
|      - Download cloud image: wget debian-12-genericcloud   |
|      - qm create + qm importdisk                           |
|      - qm set --scsihw virtio-scsi-single                  |
|      - qm set --ide2 storage:cloudinit                     |
|      - hardening: install qemu-guest-agent, fail2ban, etc  |
|      - qm template <VMID> (read-only template)             |
|                                                            |
|   2. CLONE + CUSTOMIZE                                     |
|      qm clone <template-id> <new-vmid> --name web01        |
|      qm set --ipconfig0 ip=10.0.1.10/24,gw=10.0.1.1        |
|      qm set --sshkey ~/.ssh/id_ed25519.pub                 |
|      qm set --ciuser admin --cipassword <hash>             |
|      qm set --cicustom user=local:snippets/web-config.yml  |
|      qm start <new-vmid>                                   |
|                                                            |
|   3. CLOUD-INIT SU FIRST BOOT                              |
|      - VM legge configdrive da ide2                         |
|      - Apply network config                                |
|      - Add SSH keys                                        |
|      - Run user-data (packages, scripts)                   |
|      - Mark "instance done", non re-applica                |
|                                                            |
|   SECURITY: TEMPLATE SIGNING (extra)                       |
|   - cosign sign-blob template.qcow2 → cosign.sig           |
|   - sbom: cyclonedx-py / syft                              |
|   - distribution: artifact registry con verify obbligatoria |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Cloud-init e infinitamente piu potente di Guest Customization Spec.** GCS supporta hostname + IP + qualche script. Cloud-init: full system config, packages, users, FS, services, scripts, condizionali, drop-in.
2. **Template signing previene supply-chain attacks.** Senza signing, un attaccante che compromette il artifact registry puo iniettare backdoor in ogni nuova VM. cosign + verify mandatory in CI/CD pipeline.
3. **Hardening al template, non al deploy.** Ogni VM derivata dal template eredita la baseline. Hardening da fare 1 volta, non 100 volte.
4. **Cloud-init runs once.** `instance-id` cambia → cloud-init ri-runs (es. clone). Per re-config dopo deploy iniziale, NON modificare cloud-init e aspettare; usare config management (Ansible) o `cloud-init clean` + reboot.

---

## Introduzione

Cloud-init è lo standard de facto per l'inizializzazione automatica delle istanze cloud e delle macchine virtuali. Sviluppato originariamente da Canonical per Ubuntu, è oggi supportato da tutte le principali distribuzioni Linux e, tramite cloudbase-init, anche da Windows. Su Proxmox VE, cloud-init permette di personalizzare le VM al primo avvio: configurazione di rete, creazione utenti, installazione pacchetti, esecuzione script e molto altro.

Nel contesto della migrazione da VMware, cloud-init sostituisce le "Guest Customization Specification" di vCenter, offrendo un approccio più flessibile e standardizzato. Questo documento illustra come preparare immagini cloud-init per diverse distribuzioni, creare template ottimizzati su Proxmox, utilizzare snippet personalizzati per configurazioni avanzate e implementare il deploy massivo di VM.

---

## Concetti Fondamentali di Cloud-init

### Fasi di Esecuzione

Cloud-init opera in quattro fasi distinte durante il boot:

1. **Generator** - Determina se cloud-init deve essere eseguito
2. **Local** (cloud-init-local) - Configura il datasource locale e la rete
3. **Network** (cloud-init) - Recupera i metadati e applica la configurazione di rete
4. **Config** (cloud-config) - Esegue i moduli di configurazione (utenti, pacchetti, file)
5. **Final** (cloud-final) - Esegue gli script finali e i comandi personalizzati

### Tipi di Dati Cloud-init

| Tipo | Descrizione | Uso Principale |
|---|---|---|
| **meta-data** | Metadati dell'istanza (hostname, instance-id) | Identità della VM |
| **user-data** | Configurazione personalizzata dall'utente | Script, pacchetti, file |
| **vendor-data** | Configurazione dal provider dell'infrastruttura | Configurazione base comune |
| **network-config** | Configurazione di rete | IP, gateway, DNS |

### Datasource NoCloud (Usato da Proxmox)

Proxmox utilizza il datasource **NoCloud**, che fornisce i dati cloud-init tramite un disco virtuale (formato ISO o drive CDROM) contenente i file di configurazione.

---

## Preparazione Immagini Cloud-init

### Ubuntu Server 22.04 / 24.04

```bash
# Scaricare l'immagine cloud ufficiale di Ubuntu
wget https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img

# Verificare l'integrità
wget https://cloud-images.ubuntu.com/noble/current/SHA256SUMS
sha256sum -c SHA256SUMS --ignore-missing

# Installare le dipendenze per la personalizzazione delle immagini
apt install libguestfs-tools -y

# Personalizzare l'immagine (opzionale ma raccomandato)
# Installare il QEMU Guest Agent nell'immagine
virt-customize -a noble-server-cloudimg-amd64.img \
  --install qemu-guest-agent \
  --install curl,wget,vim,htop,net-tools,dnsutils,gnupg \
  --run-command 'systemctl enable qemu-guest-agent' \
  --run-command 'systemctl enable serial-getty@ttyS0.service' \
  --truncate /etc/machine-id

# Creare la VM template su Proxmox
qm create 9000 \
  --name "ubuntu-2404-cloudinit-template" \
  --description "Ubuntu 24.04 LTS Cloud-init Template" \
  --ostype l26 \
  --cpu x86-64-v2-AES \
  --cores 2 \
  --sockets 1 \
  --memory 2048 \
  --balloon 0 \
  --agent enabled=1,fstrim_cloned_disks=1 \
  --bios ovmf \
  --machine q35 \
  --efidisk0 local-zfs:1,efitype=4m,pre-enrolled-keys=0 \
  --scsihw virtio-scsi-single \
  --net0 virtio,bridge=vmbr0,firewall=1 \
  --serial0 socket \
  --vga serial0 \
  --boot order=scsi0

# Importare il disco
qm set 9000 --scsi0 local-zfs:0,import-from=/root/noble-server-cloudimg-amd64.img,iothread=1,discard=on,ssd=1

# Ridimensionare il disco a 32 GB
qm resize 9000 scsi0 32G

# Aggiungere il drive cloud-init
qm set 9000 --ide2 local-zfs:cloudinit

# Configurare cloud-init di base
qm set 9000 \
  --ciuser sysadmin \
  --cipassword "$(openssl passwd -6 'TempPassword123!')" \
  --sshkeys /root/.ssh/authorized_keys \
  --ipconfig0 ip=dhcp \
  --nameserver "10.0.1.10 10.0.1.11" \
  --searchdomain "example.local" \
  --ciupgrade 1

# Convertire in template
qm template 9000

echo "Template Ubuntu 24.04 creato con VMID 9000"
```

### Debian 12 (Bookworm)

```bash
# Scaricare l'immagine cloud Debian
wget https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.qcow2

# Personalizzare l'immagine
virt-customize -a debian-12-generic-amd64.qcow2 \
  --install qemu-guest-agent,curl,wget,vim,htop,net-tools,dnsutils,cloud-init \
  --run-command 'systemctl enable qemu-guest-agent' \
  --truncate /etc/machine-id

# Creare la VM template
qm create 9001 \
  --name "debian-12-cloudinit-template" \
  --description "Debian 12 Bookworm Cloud-init Template" \
  --ostype l26 \
  --cpu x86-64-v2-AES \
  --cores 2 \
  --sockets 1 \
  --memory 2048 \
  --agent enabled=1,fstrim_cloned_disks=1 \
  --scsihw virtio-scsi-single \
  --net0 virtio,bridge=vmbr0,firewall=1 \
  --serial0 socket \
  --boot order=scsi0

qm set 9001 --scsi0 local-zfs:0,import-from=/root/debian-12-generic-amd64.qcow2,iothread=1,discard=on,ssd=1
qm resize 9001 scsi0 32G
qm set 9001 --ide2 local-zfs:cloudinit
qm set 9001 --ipconfig0 ip=dhcp

qm template 9001
```

### CentOS Stream 9 / Rocky Linux 9 / AlmaLinux 9

```bash
# Scaricare l'immagine cloud Rocky Linux 9
wget https://download.rockylinux.org/pub/rocky/9/images/x86_64/Rocky-9-GenericCloud.latest.x86_64.qcow2

# Personalizzare l'immagine
virt-customize -a Rocky-9-GenericCloud.latest.x86_64.qcow2 \
  --install qemu-guest-agent,curl,wget,vim-enhanced,htop,net-tools,bind-utils \
  --run-command 'systemctl enable qemu-guest-agent' \
  --selinux-relabel \
  --truncate /etc/machine-id

# Creare la VM template
qm create 9002 \
  --name "rocky-9-cloudinit-template" \
  --description "Rocky Linux 9 Cloud-init Template" \
  --ostype l26 \
  --cpu x86-64-v2-AES \
  --cores 2 \
  --sockets 1 \
  --memory 2048 \
  --agent enabled=1,fstrim_cloned_disks=1 \
  --scsihw virtio-scsi-single \
  --net0 virtio,bridge=vmbr0,firewall=1 \
  --serial0 socket \
  --boot order=scsi0

qm set 9002 --scsi0 local-zfs:0,import-from=/root/Rocky-9-GenericCloud.latest.x86_64.qcow2,iothread=1,discard=on,ssd=1
qm resize 9002 scsi0 32G
qm set 9002 --ide2 local-zfs:cloudinit

qm template 9002
```

### Windows Server 2022 con Cloudbase-init

La preparazione di un template Windows richiede diversi passaggi aggiuntivi.

```bash
# Fase 1: Creare la VM per l'installazione di Windows
qm create 9010 \
  --name "win2022-cloudinit-template" \
  --description "Windows Server 2022 Cloud-init Template" \
  --ostype win11 \
  --cpu host \
  --cores 4 \
  --sockets 1 \
  --memory 8192 \
  --bios ovmf \
  --machine q35 \
  --efidisk0 local-zfs:1,efitype=4m,pre-enrolled-keys=1 \
  --tpmstate0 local-zfs:1,version=v2.0 \
  --scsihw virtio-scsi-single \
  --scsi0 local-zfs:64,iothread=1,discard=on,ssd=1 \
  --ide0 local:iso/windows-server-2022.iso,media=cdrom \
  --ide2 local:iso/virtio-win.iso,media=cdrom \
  --net0 virtio,bridge=vmbr0,firewall=1 \
  --agent enabled=1 \
  --boot order='ide0;scsi0'

# Fase 2: Installare Windows e i driver VirtIO dalla ISO
# (Procedura manuale tramite console VNC/SPICE)
# - Durante l'installazione, caricare i driver VirtIO da D:\vioscsi\2k22\amd64
# - Dopo l'installazione, installare tutti i driver VirtIO
# - Installare il QEMU Guest Agent da D:\guest-agent\qemu-ga-x86_64.msi

# Fase 3: Installare Cloudbase-init dentro Windows
# (Eseguire in PowerShell come Administrator dentro la VM Windows)
```

```powershell
# === Eseguire dentro la VM Windows ===

# Scaricare e installare Cloudbase-init
$cloudbaseInitUrl = "https://github.com/cloudbase/cloudbase-init/releases/download/1.1.5/CloudbaseInitSetup_1_1_5_x64.msi"
Invoke-WebRequest -Uri $cloudbaseInitUrl -OutFile "C:\CloudbaseInitSetup.msi"

# Installazione silenziosa
msiexec /i "C:\CloudbaseInitSetup.msi" /qn /l*v "C:\cloudbase-init-install.log"

# Configurare cloudbase-init
$configPath = "C:\Program Files\Cloudbase Solutions\Cloudbase-Init\conf\cloudbase-init.conf"

@"
[DEFAULT]
username=Admin
groups=Administrators
inject_user_password=true
config_drive_raw_hhd=true
config_drive_cdrom=true
config_drive_vfat=true
bsdtar_path=C:\Program Files\Cloudbase Solutions\Cloudbase-Init\bin\bsdtar.exe
mtools_path=C:\Program Files\Cloudbase Solutions\Cloudbase-Init\bin\
verbose=true
debug=true
logdir=C:\Program Files\Cloudbase Solutions\Cloudbase-Init\log\
logfile=cloudbase-init.log
default_log_levels=comtypes=INFO,suds=INFO,iso8601=WARN,requests=WARN
logging_serial_port_settings=
mtu_use_dhcp_config=true
ntp_use_dhcp_config=true
local_scripts_path=C:\Program Files\Cloudbase Solutions\Cloudbase-Init\LocalScripts\
check_latest_version=true

metadata_services=cloudbaseinit.metadata.services.configdrive.ConfigDriveService
plugins=cloudbaseinit.plugins.common.mtu.MTUPlugin,cloudbaseinit.plugins.common.sethostname.SetHostNamePlugin,cloudbaseinit.plugins.windows.createuser.CreateUserPlugin,cloudbaseinit.plugins.common.setuserpassword.SetUserPasswordPlugin,cloudbaseinit.plugins.common.sshpublickeys.SetUserSSHPublicKeysPlugin,cloudbaseinit.plugins.windows.extendvolumes.ExtendVolumesPlugin,cloudbaseinit.plugins.common.userdata.UserDataPlugin,cloudbaseinit.plugins.common.networkconfig.NetworkConfigPlugin
"@ | Out-File -FilePath $configPath -Encoding ASCII

# Impostare il servizio cloudbase-init
Set-Service -Name cloudbase-init -StartupType Automatic

# Eseguire Sysprep con cloudbase-init
# ATTENZIONE: Questo spegnerà la VM!
& "C:\Program Files\Cloudbase Solutions\Cloudbase-Init\conf\Unattend.xml"
& "C:\Windows\System32\Sysprep\sysprep.exe" /generalize /oobe /shutdown /unattend:"C:\Program Files\Cloudbase Solutions\Cloudbase-Init\conf\Unattend.xml"
```

```bash
# Fase 4: Dopo lo spegnimento, convertire in template
# Rimuovere i media di installazione
qm set 9010 --delete ide0
qm set 9010 --delete ide2

# Aggiungere il drive cloud-init
qm set 9010 --ide2 local-zfs:cloudinit

# Configurare il boot order
qm set 9010 --boot order=scsi0

# Convertire in template
qm template 9010
```

---

## Configurazione Cloud-init su Proxmox

### Configurazione di Base tramite CLI

```bash
# Configurazione utente e autenticazione
qm set <vmid> --ciuser sysadmin
qm set <vmid> --cipassword "$(openssl passwd -6 'MyPassword!')"
qm set <vmid> --sshkeys /path/to/authorized_keys

# Configurazione di rete - IP statico
qm set <vmid> --ipconfig0 ip=10.0.1.100/24,gw=10.0.1.1

# Configurazione di rete - DHCP
qm set <vmid> --ipconfig0 ip=dhcp

# Configurazione di rete - Interfacce multiple
qm set <vmid> --ipconfig0 ip=10.0.1.100/24,gw=10.0.1.1
qm set <vmid> --ipconfig1 ip=10.0.2.100/24

# DNS
qm set <vmid> --nameserver "10.0.1.10 10.0.1.11"
qm set <vmid> --searchdomain "example.local"

# Aggiornamento automatico dei pacchetti al primo avvio
qm set <vmid> --ciupgrade 1

# Tipo di cloud-init (nocloud è il default per Linux)
qm set <vmid> --citype nocloud

# Visualizzare la configurazione cloud-init attuale
qm cloudinit dump <vmid> user
qm cloudinit dump <vmid> network
qm cloudinit dump <vmid> meta
```

### Configurazione Avanzata con Custom Snippet

Proxmox supporta snippet cloud-init personalizzati che permettono configurazioni molto più avanzate rispetto ai parametri base.

#### Preparazione dello Storage per gli Snippet

```bash
# Abilitare il tipo di contenuto "snippets" su uno storage
pvesm set local --content images,rootdir,vztmpl,iso,snippets,backup

# Creare la directory per gli snippet (se necessario)
mkdir -p /var/lib/vz/snippets
```

#### Snippet User-data Personalizzato

```yaml
# /var/lib/vz/snippets/user-data-webserver.yml
#cloud-config

# Configurazione hostname
hostname: ${hostname}
fqdn: ${hostname}.example.local
manage_etc_hosts: true

# Creazione utenti
users:
  - name: sysadmin
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: [adm, sudo, docker]
    shell: /bin/bash
    lock_passwd: false
    ssh_authorized_keys:
      - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIExample... admin@company

  - name: deploy
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: [docker]
    shell: /bin/bash
    ssh_authorized_keys:
      - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDeploy... deploy@ci

# Configurazione SSH
ssh_pwauth: false
disable_root: true

# Aggiornamento pacchetti
package_update: true
package_upgrade: true
package_reboot_if_required: true

# Installazione pacchetti
packages:
  - qemu-guest-agent
  - curl
  - wget
  - vim
  - htop
  - iotop
  - net-tools
  - dnsutils
  - gnupg
  - apt-transport-https
  - ca-certificates
  - software-properties-common
  - unattended-upgrades
  - fail2ban
  - ufw
  - nginx

# Configurazione timezone e locale
timezone: Europe/Rome
locale: it_IT.UTF-8

# Configurazione NTP
ntp:
  enabled: true
  servers:
    - ntp1.example.local
    - ntp2.example.local
    - pool.ntp.org

# Scrittura file di configurazione
write_files:
  # Configurazione sysctl per sicurezza
  - path: /etc/sysctl.d/99-security.conf
    content: |
      net.ipv4.ip_forward = 0
      net.ipv4.conf.all.send_redirects = 0
      net.ipv4.conf.default.send_redirects = 0
      net.ipv4.conf.all.accept_redirects = 0
      net.ipv4.conf.default.accept_redirects = 0
      net.ipv4.conf.all.log_martians = 1
      net.ipv4.conf.default.log_martians = 1
      net.ipv4.icmp_echo_ignore_broadcasts = 1
      net.ipv4.tcp_syncookies = 1
    permissions: '0644'

  # Configurazione SSH hardening
  - path: /etc/ssh/sshd_config.d/99-hardening.conf
    content: |
      PermitRootLogin no
      PasswordAuthentication no
      PubkeyAuthentication yes
      X11Forwarding no
      MaxAuthTries 3
      AllowUsers sysadmin deploy
      ClientAliveInterval 300
      ClientAliveCountMax 2
      Protocol 2
    permissions: '0600'

  # Configurazione fail2ban
  - path: /etc/fail2ban/jail.local
    content: |
      [DEFAULT]
      bantime = 3600
      findtime = 600
      maxretry = 3
      backend = systemd

      [sshd]
      enabled = true
      port = 22
      logpath = %(sshd_log)s
    permissions: '0644'

  # Script di primo avvio personalizzato
  - path: /opt/scripts/first-boot.sh
    content: |
      #!/bin/bash
      set -euo pipefail
      LOG="/var/log/first-boot.log"

      echo "$(date) - Inizio script di primo avvio" >> "$LOG"

      # Abilitare servizi
      systemctl enable --now qemu-guest-agent
      systemctl enable --now fail2ban

      # Configurare firewall UFW
      ufw default deny incoming
      ufw default allow outgoing
      ufw allow 22/tcp comment 'SSH'
      ufw allow 80/tcp comment 'HTTP'
      ufw allow 443/tcp comment 'HTTPS'
      ufw --force enable

      # Applicare sysctl
      sysctl --system

      # Riavviare SSH
      systemctl restart sshd

      echo "$(date) - Script di primo avvio completato" >> "$LOG"
    permissions: '0755'

# Comandi da eseguire all'avvio (in ordine)
runcmd:
  - [ systemctl, enable, --now, qemu-guest-agent ]
  - [ /opt/scripts/first-boot.sh ]
  - [ systemctl, restart, sshd ]

# Messaggio finale
final_message: |
  Cloud-init completato per $INSTANCE_ID
  Versione cloud-init: $CLOUD_INIT_VERSION
  Timestamp: $TIMESTAMP
  Uptime: $UPTIME
```

#### Snippet Vendor-data

```yaml
# /var/lib/vz/snippets/vendor-data-base.yml
#cloud-config

# Vendor-data viene applicato prima di user-data
# Ideale per configurazioni comuni a tutte le VM

# Configurazione base del sistema
timezone: Europe/Rome
locale: it_IT.UTF-8

# NTP
ntp:
  enabled: true
  servers:
    - ntp1.example.local
    - ntp2.example.local

# Pacchetti base comuni a tutte le VM
packages:
  - qemu-guest-agent
  - curl
  - wget
  - vim
  - htop

# Abilitare il QEMU Guest Agent
runcmd:
  - [ systemctl, enable, --now, qemu-guest-agent ]

# Configurazione automatica degli aggiornamenti di sicurezza
apt:
  conf: |
    APT::Periodic::Update-Package-Lists "1";
    APT::Periodic::Unattended-Upgrade "1";
    APT::Periodic::AutocleanInterval "7";
```

#### Applicare gli Snippet a una VM

```bash
# Utilizzare snippet personalizzati per user-data e vendor-data
qm set <vmid> --cicustom "user=local:snippets/user-data-webserver.yml,vendor=local:snippets/vendor-data-base.yml"

# Solo user-data personalizzato
qm set <vmid> --cicustom "user=local:snippets/user-data-webserver.yml"

# Solo vendor-data personalizzato
qm set <vmid> --cicustom "vendor=local:snippets/vendor-data-base.yml"

# Network config personalizzato
qm set <vmid> --cicustom "network=local:snippets/network-config.yml"

# Verificare la configurazione
qm cloudinit dump <vmid> user
qm cloudinit dump <vmid> vendor
```

#### Snippet Network Config (v2)

```yaml
# /var/lib/vz/snippets/network-config-bonding.yml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      match:
        macaddress: "BC:24:11:AA:BB:CC"
    eth1:
      dhcp4: false
      match:
        macaddress: "BC:24:11:AA:BB:DD"

  bonds:
    bond0:
      interfaces: [eth0, eth1]
      parameters:
        mode: 802.3ad
        lacp-rate: fast
        mii-monitor-interval: 100
      addresses:
        - 10.0.1.100/24
      routes:
        - to: default
          via: 10.0.1.1
      nameservers:
        addresses: [10.0.1.10, 10.0.1.11]
        search: [example.local]
```

---

## Deploy Massivo da Template

### Script Bash per Deploy Batch

```bash
#!/bin/bash
# deploy-batch.sh - Deploy massivo di VM da template con cloud-init
set -euo pipefail

# Configurazione
TEMPLATE_VMID=9000
NODE="pve01"
STORAGE="local-zfs"
BRIDGE="vmbr0"
CI_USER="sysadmin"
SSH_KEY_FILE="/root/.ssh/authorized_keys"
NAMESERVERS="10.0.1.10 10.0.1.11"
SEARCH_DOMAIN="example.local"

# Colori per l'output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Funzione per deployare una singola VM
deploy_vm() {
    local vmid="$1"
    local name="$2"
    local ip="$3"
    local gateway="$4"
    local cores="${5:-2}"
    local memory="${6:-2048}"
    local disk="${7:-32G}"
    local vlan="${8:-}"
    local tags="${9:-}"

    log_info "Deploy VM ${name} (VMID: ${vmid})..."

    # Verificare che il VMID non sia già in uso
    if qm status "$vmid" &>/dev/null; then
        log_warn "VMID ${vmid} già in uso, skip."
        return 1
    fi

    # Clonare dal template
    log_info "  Clonazione dal template ${TEMPLATE_VMID}..."
    qm clone "$TEMPLATE_VMID" "$vmid" \
        --name "$name" \
        --full true \
        --storage "$STORAGE" \
        --target "$NODE"

    # Configurare le risorse
    log_info "  Configurazione risorse (CPU: ${cores}, RAM: ${memory}MB)..."
    qm set "$vmid" \
        --cores "$cores" \
        --memory "$memory" \
        --balloon "$memory" \
        --onboot 1

    # Configurare la rete
    local net_config="virtio,bridge=${BRIDGE}"
    if [ -n "$vlan" ]; then
        net_config="${net_config},tag=${vlan}"
    fi
    qm set "$vmid" --net0 "$net_config"

    # Ridimensionare il disco se necessario
    if [ "$disk" != "32G" ]; then
        log_info "  Ridimensionamento disco a ${disk}..."
        qm resize "$vmid" scsi0 "$disk"
    fi

    # Configurare cloud-init
    log_info "  Configurazione cloud-init (IP: ${ip})..."
    qm set "$vmid" \
        --ciuser "$CI_USER" \
        --sshkeys "$SSH_KEY_FILE" \
        --ipconfig0 "ip=${ip},gw=${gateway}" \
        --nameserver "$NAMESERVERS" \
        --searchdomain "$SEARCH_DOMAIN"

    # Aggiungere tag se specificati
    if [ -n "$tags" ]; then
        qm set "$vmid" --tags "$tags"
    fi

    # Avviare la VM
    log_info "  Avvio VM..."
    qm start "$vmid"

    log_info "  VM ${name} deployata con successo!"
    return 0
}

# Leggere il file CSV e deployare le VM
deploy_from_csv() {
    local csv_file="$1"
    local success=0
    local failed=0
    local skipped=0

    log_info "Lettura file CSV: ${csv_file}"

    # Saltare l'header
    tail -n +2 "$csv_file" | while IFS=',' read -r vmid name ip gateway cores memory disk vlan tags; do
        # Rimuovere spazi
        vmid=$(echo "$vmid" | tr -d ' ')
        name=$(echo "$name" | tr -d ' ')
        ip=$(echo "$ip" | tr -d ' ')
        gateway=$(echo "$gateway" | tr -d ' ')

        if deploy_vm "$vmid" "$name" "$ip" "$gateway" "$cores" "$memory" "$disk" "$vlan" "$tags"; then
            ((success++)) || true
        else
            ((failed++)) || true
        fi
    done

    echo ""
    log_info "=== Report Deploy ==="
    log_info "Successo: ${success}"
    log_warn "Falliti:  ${failed}"
}

# File CSV di esempio
create_sample_csv() {
    cat > vm-deploy-list.csv << 'EOF'
vmid,name,ip,gateway,cores,memory,disk,vlan,tags
110,prod-web01,10.0.100.10/24,10.0.100.1,4,8192,50G,100,production;webserver
111,prod-web02,10.0.100.11/24,10.0.100.1,4,8192,50G,100,production;webserver
112,prod-web03,10.0.100.12/24,10.0.100.1,4,8192,50G,100,production;webserver
210,prod-db01,10.0.200.10/24,10.0.200.1,8,32768,100G,200,production;database
211,prod-db02,10.0.200.11/24,10.0.200.1,8,32768,100G,200,production;database
310,prod-app01,10.0.150.10/24,10.0.150.1,4,16384,80G,150,production;appserver
311,prod-app02,10.0.150.11/24,10.0.150.1,4,16384,80G,150,production;appserver
EOF
    log_info "File CSV di esempio creato: vm-deploy-list.csv"
}

# Menu principale
case "${1:-}" in
    deploy)
        deploy_from_csv "${2:-vm-deploy-list.csv}"
        ;;
    single)
        deploy_vm "$2" "$3" "$4" "$5" "${6:-2}" "${7:-2048}" "${8:-32G}" "${9:-}" "${10:-}"
        ;;
    sample)
        create_sample_csv
        ;;
    *)
        echo "Uso: $0 {deploy <csv>|single <vmid> <name> <ip> <gw> [cores] [mem] [disk] [vlan] [tags]|sample}"
        ;;
esac
```

---

## Confronto con VMware Guest Customization Specification

### VMware Guest Customization

```powershell
# Esempio PowerCLI per Guest Customization
$spec = New-OSCustomizationSpec -Name "Linux-Prod" `
    -OSType Linux `
    -DnsServer "10.0.1.10","10.0.1.11" `
    -DnsSuffix "prod.example.local" `
    -Domain "prod.example.local" `
    -NamingScheme fixed `
    -NamingPrefix "vm-"

$spec | Get-OSCustomizationNicMapping | Set-OSCustomizationNicMapping `
    -IpMode UseStaticIP `
    -IpAddress "10.0.1.100" `
    -SubnetMask "255.255.255.0" `
    -DefaultGateway "10.0.1.1"

New-VM -Name "web-server" -Template "ubuntu-template" `
    -VMHost "esxi01" -Datastore "DS01" `
    -OSCustomizationSpec $spec
```

### Tabella Comparativa

| Aspetto | VMware Guest Customization | Proxmox Cloud-init |
|---|---|---|
| Standard | Proprietario VMware | Standard aperto (cloud-init) |
| Ambito | Solo VM vSphere | Multi-cloud, multi-platform |
| Requisiti Guest | VMware Tools + Perl | cloud-init installato |
| Configurazione | GUI vCenter o PowerCLI | CLI, API, snippet YAML |
| Personalizzazione | Limitata (rete, DNS, domain) | Estesa (pacchetti, file, script) |
| Script post-deploy | Limitati | Illimitati (runcmd, write_files) |
| Dipendenze Server | Richiede vCenter | Nessuna (NoCloud datasource) |
| Template | Uno per specifica | Snippet componibili |
| Windows | Sysprep integrato | Cloudbase-init |
| Costo | Licenza vCenter | Gratuito |
| Flessibilità | Media | Alta |
| Community | VMware (proprietario) | Vasta community open-source |

### Migrazione delle Customization Spec

Per migrare da VMware Guest Customization a cloud-init su Proxmox, mappare i seguenti elementi:

| VMware Spec | Cloud-init Equivalente |
|---|---|
| `ComputerName` / `NamingScheme` | `hostname` nel user-data o `--ciuser` |
| `DnsServer` | `--nameserver` o `nameservers` nel user-data |
| `DnsSuffix` | `--searchdomain` o `search` nel user-data |
| `Domain` | `fqdn` nel user-data |
| `IpAddress` / `SubnetMask` | `--ipconfig0 ip=x.x.x.x/24` |
| `DefaultGateway` | `--ipconfig0 ip=...,gw=x.x.x.x` |
| `AdminPassword` (Windows) | `--cipassword` o cloudbase-init config |
| Script post-deploy | `runcmd` o `write_files` nel user-data |

---

## Troubleshooting Cloud-init

### Verificare i Log all'Interno della VM

```bash
# Log principale di cloud-init
cat /var/log/cloud-init.log

# Output sintetico
cat /var/log/cloud-init-output.log

# Stato di cloud-init
cloud-init status --long

# Analizzare le fasi di esecuzione
cloud-init analyze show

# Visualizzare la configurazione applicata
cloud-init query --all

# Verificare i dati del datasource
cat /run/cloud-init/instance-data.json | jq .

# Forzare una nuova esecuzione di cloud-init
cloud-init clean --logs
cloud-init init --local
cloud-init init
cloud-init modules --mode config
cloud-init modules --mode final
```

### Problemi Comuni e Soluzioni

```bash
# Problema: cloud-init non si esegue dopo la clonazione
# Soluzione: Assicurarsi che machine-id sia vuoto nel template
truncate -s 0 /etc/machine-id
rm -f /var/lib/dbus/machine-id
ln -s /etc/machine-id /var/lib/dbus/machine-id

# Problema: La rete non viene configurata
# Verificare che il datasource sia corretto
cat /etc/cloud/cloud.cfg.d/90_dpkg.cfg
# Deve contenere: datasource_list: [ NoCloud, ConfigDrive, None ]

# Problema: Il disco cloud-init non viene montato
# Verificare che il drive IDE sia presente
qm config <vmid> | grep ide2
# Se mancante, aggiungerlo:
qm set <vmid> --ide2 local-zfs:cloudinit

# Problema: Le chiavi SSH non vengono applicate
# Verificare il formato delle chiavi
qm cloudinit dump <vmid> user | grep ssh
# Le chiavi devono essere in formato OpenSSH standard

# Problema: Windows cloudbase-init non funziona
# Verificare i log dentro Windows
# C:\Program Files\Cloudbase Solutions\Cloudbase-Init\log\cloudbase-init.log
```

---

## Conclusione

Cloud-init rappresenta il meccanismo standard per l'inizializzazione automatica delle VM su Proxmox VE, sostituendo le Guest Customization Specification di VMware con un approccio più flessibile, potente e indipendente dal vendor. La combinazione di template pre-configurati e snippet cloud-init personalizzati permette di implementare un sistema di deploy rapido e riproducibile, dalla singola VM al deploy massivo di intere infrastrutture. La possibilità di utilizzare user-data, vendor-data e network-config come componenti separati e componibili offre un livello di flessibilità che va ben oltre le capacità delle customization spec di VMware.

---

## Approfondimenti — note del 2026-04-27

> **Approfondimento — `cosign` per template signing.** Per supply-chain provenance: (1) build template, esporta come qcow2; (2) `cosign sign-blob --output-signature template.sig template.qcow2`; (3) caricare template + sig su artifact registry; (4) deploy script verifica la sig prima di clonare: `cosign verify-blob --signature template.sig --certificate template.crt template.qcow2`; (5) se sig invalida, abortire. Per signing automatico in CI: usare keyless signing con OIDC (no chiavi long-lived). Fonte: [sigstore/cosign — Documentation](https://docs.sigstore.dev/cosign/overview/), retrieved 2026-04-27.

---

## Esercizi

1. **Lab — build template Debian 12 hardened.** Da cloud image ufficiale: import su Proxmox, install qemu-guest-agent + fail2ban + unattended-upgrades, configure SSH key-only, set qm template. Documenta ogni step.
2. **Lab — clone + cloud-init multi-VM.** Da un template, deploy 5 VM con IP sequenziali (10.0.1.10-14), hostname web01-05, ssh key dell'utente. Misurare il tempo totale.
3. **Stretch — cosign signing pipeline.** Configurare GitLab CI o GitHub Actions per build automatica + cosign signing + push to artifact registry. Documenta ogni step.

## Auto-valutazione

1. Cosa contiene `user-data` vs `meta-data` cloud-init?
2. `qm template <VMID>` cosa fa?
3. Quando cloud-init ri-esegue al boot? (instance-id check)
4. cosign vs gpg signature: differenza pratica.
5. Differenza fra cloud-init e VMware Guest Customization Spec.

## Letture primarie consigliate

- cloud-init Documentation. https://cloudinit.readthedocs.io/en/latest/ (retrieved 2026-04-27).
- Proxmox VE Wiki — Cloud-Init Support. https://pve.proxmox.com/wiki/Cloud-Init_Support (retrieved 2026-04-27).
- sigstore/cosign Documentation. https://docs.sigstore.dev/cosign/overview/ (retrieved 2026-04-27).
- CycloneDX SBOM specification. https://cyclonedx.org/specification/overview/ (retrieved 2026-04-27).
- Debian Cloud Images. https://cloud.debian.org/images/cloud/ (retrieved 2026-04-27).
- Ubuntu Cloud Images. https://cloud-images.ubuntu.com/ (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 14.2 — `proxmox-api-automazione-script.md`: API per orchestrare clone+customize.
- Modulo 12.3 — `../12-SICUREZZA-E-COMPLIANCE/sicurezza-compliance.md`: hardening baseline.

## Glossario locale

| Termine | Definizione |
|---|---|
| **cloud-init** | Standard de facto per init automatica VM cloud. |
| **cloudbase-init** | Implementazione cloud-init per Windows. |
| **user-data** | Config/script eseguiti dal cloud-init al primo boot. |
| **meta-data** | Metadata istanza (instance-id, hostname). |
| **network-config** | Configurazione rete cloud-init. |
| **Cloud image** | Immagine OS pre-configurata per cloud (small, no init). |
| **`qm template`** | Marca una VM come template read-only. |
| **`qm clone`** | Crea nuova VM da template. |
| **Snippet (Proxmox)** | File caricato in storage `local:snippets/` per cloud-init custom. |
| **cosign** | Tool sigstore per firma digitale di artefatti. |
| **SBOM** | Software Bill of Materials. |
| **GCS (VMware)** | Guest Customization Spec; analogo legacy di cloud-init. |
