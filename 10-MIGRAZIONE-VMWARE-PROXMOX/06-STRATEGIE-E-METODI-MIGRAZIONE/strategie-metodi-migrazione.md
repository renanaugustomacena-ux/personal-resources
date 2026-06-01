# Strategie e Metodi di Migrazione VMware → Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 06.1 (apre la fase operativa, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** Fase 1 e Fase 2 complete; modulo 05.2 (classificazione tier e wave); modulo 05.3 (sizing target).
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. distinguere le 4 strategie principali (cold, warm, live/minimal-downtime, application-level) e scegliere la giusta per ogni VM sulla base del downtime ammesso, dimensione disco, criticita e capacita applicativa;
> 2. eseguire una **cold migration** end-to-end per una VM Linux e una Windows Server, includendo pre-installazione driver VirtIO, rimozione VMware Tools e import su Proxmox;
> 3. impostare una **warm migration** con copia bulk + delta sync (rsync block-level con `--inplace --no-whole-file` o `qemu-img convert` ripetuti);
> 4. progettare una **live migration** con DNS-based cutover o database log shipping, calcolando i tempi di TTL DNS, RPO replica e drain delle connessioni TCP;
> 5. usare strumenti commerciali (Veeam, NAKIVO, Carbonite, PlateSpin) confrontandoli con il toolchain open (virt-v2v, qemu-img, rsync, Clonezilla);
> 6. produrre uno **script batch** di conversione VMDK → qcow2/raw con logging strutturato, retry policy e validazione output (size, checksum).
> **Tempo stimato:** lettura 90-120 min · lab 360-480 min (eseguendo le 4 strategie su VM di test diverse)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** virt-v2v ≥ 2.x, qemu-img 8.x+ (con `-p -W` per progress + parallel), `rsync` 3.2+ (con `--inplace`), VirtIO Windows drivers `virtio-win-stable`.

## Mappa concettuale

```
+======================================================+
|  Le 4 strategie di migrazione                        |
+======================================================+
|                                                      |
|       COLD            WARM            LIVE     APP-LV|
|       ----            ----            ----     ------|
|  Downtime: ALTO   |  MEDIO        |  MIN    |  VAR  |
|  Complessita:LOW  |  MED          |  HIGH   |  MED  |
|  Tool: qemu-img   |  rsync block  |  DNS    |  DB    |
|        virt-v2v   |  CBT-like     |  cutover|  AG/    |
|                   |               |  DB     |  Repl   |
|                   |               |  shipping|       |
|                                                      |
|  CRITERI DI SCELTA                                   |
|     +-- downtime ammesso (ore -> sec)                |
|     +-- dimensione disco                             |
|     +-- tipo applicazione (stateless / stateful)     |
|     +-- skill team (cold semplice, live difficile)   |
|     +-- finestra notturna disponibile                |
|                                                      |
|  PER OGNI STRATEGIA                                  |
|     1. PREPARAZIONE                                  |
|        +-- pre-install VirtIO (Windows)              |
|        +-- pre-config initramfs (Linux)              |
|        +-- rimuovere snapshot stale                  |
|        +-- rimuovere VMware Tools                    |
|        +-- backup applicativo                        |
|     2. ESECUZIONE                                    |
|        +-- export / convert / import                 |
|        +-- sync delta                                |
|        +-- cutover                                   |
|     3. VALIDAZIONE                                   |
|        +-- boot OK + IP corretto                     |
|        +-- servizi up + health check                 |
|        +-- backup nuovo + monitoring                 |
|     4. ROLLBACK PLAN                                 |
|        +-- power-on origine VMware (held)            |
|        +-- DNS revert (TTL basso)                    |
|        +-- verifica integrita dati                   |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **La scelta della strategia non e tecnica, e di rischio.** Cold e la piu sicura (downtime ammesso = no rischio sull'applicazione viva). Live e la piu rischiosa (cutover puntuale + dipendenza dalla replica nativa). Per produzione critica, *partire sempre da cold e considerare warm/live solo se il downtime non e ammesso*.
2. **Pre-install VirtIO o BSOD.** Per Windows, l'iniezione VirtIO al boot via `virt-v2v` puo fallire (firme driver, registry corrotto). La pratica robusta e *pre-installare* i driver VirtIO sulla VM Windows mentre e ancora viva su VMware (`pnputil.exe /add-driver D:\... /install`), poi spegnere. Lo stesso vale per `qemu-guest-agent`.
3. **Linux deve avere `virtio_*` in initramfs.** Su VMware il boot usa LSI/PVSCSI, quindi `virtio_blk`, `virtio_net`, `virtio_scsi`, `virtio_pci` non sono in `/etc/initramfs-tools/modules` (Debian/Ubuntu) o `/etc/dracut.conf.d/` (RHEL/Fedora). Senza questi nel initramfs, il kernel post-migrazione non vede il disco e va in `dracut emergency shell`. *Aggiungerli prima di spegnere* e *rigenerare initramfs* e step non opzionale.
4. **Snapshot stale = data loss potenziale al cold/v2v.** virt-v2v esporta il base disk dello snapshot chain attuale, NON il delta. Se la VM ha snapshot vecchi non consolidati, le modifiche fatte nel delta possono non essere migrate. Procedura corretta: consolidare *tutti* gli snapshot prima di iniziare, verificare con `vim-cmd vmsvc/snapshot.get <vmid>` che l'output sia vuoto.
5. **DNS TTL basso 24-48 ore prima e regola d'oro per cutover.** TTL = 60 s significa che dopo lo switch DNS, il traffico converge in <2 min. Se TTL = 300 s, in 5 min. Se TTL = 3600 s, in *un'ora*. Pianificare il TTL drop almeno 24 h prima del cutover (per propagare nei resolver intermedi) e ripristinare TTL normale 24 h dopo.

## Indice

1. [Overview degli Approcci di Migrazione](#1-overview-degli-approcci-di-migrazione)
2. [Cold Migration (Offline)](#2-cold-migration-offline)
3. [Warm Migration (Semi-Online)](#3-warm-migration-semi-online)
4. [Live/Minimal Downtime Migration](#4-liveminimal-downtime-migration)
5. [virt-v2v — Conversione Automatizzata](#5-virt-v2v--conversione-automatizzata)
6. [qemu-img convert — Deep Dive](#6-qemu-img-convert--deep-dive)
7. [Clonezilla per Migrazione](#7-clonezilla-per-migrazione)
8. [Tool Commerciali a Confronto](#8-tool-commerciali-a-confronto)
9. [Migrazione Incrementale con rsync](#9-migrazione-incrementale-con-rsync)
10. [Migrazione di Applicazioni Stateful](#10-migrazione-di-applicazioni-stateful)

---

## 1. Overview degli Approcci di Migrazione

### Classificazione delle Strategie

```
┌─────────────────────────────────────────────────────────────────┐
│                    STRATEGIE DI MIGRAZIONE                      │
├──────────────┬──────────────┬───────────────┬──────────────────┤
│  COLD (P2V)  │    WARM      │  LIVE/ONLINE  │  APPLICATION     │
│              │              │               │  LEVEL           │
├──────────────┼──────────────┼───────────────┼──────────────────┤
│ VM spenta    │ Copia iniziale│ Replica       │ Reinstall OS     │
│ Export VMDK  │ + sync incr. │ continua      │ + migra dati     │
│ Convert      │ + cutover    │ + DNS switch  │ + riconfigura    │
│ Import       │ breve        │               │                  │
├──────────────┼──────────────┼───────────────┼──────────────────┤
│ Downtime:    │ Downtime:    │ Downtime:     │ Downtime:        │
│ ALTO         │ MEDIO        │ MINIMO        │ VARIABILE        │
│ (ore)        │ (minuti)     │ (secondi)     │ (dipende app)    │
├──────────────┼──────────────┼───────────────┼──────────────────┤
│ Complessità: │ Complessità: │ Complessità:  │ Complessità:     │
│ BASSA        │ MEDIA        │ ALTA          │ MEDIA-ALTA       │
└──────────────┴──────────────┴───────────────┴──────────────────┘
```

### Matrice Decisionale

| Criterio | Cold | Warm | Live | App-Level |
|----------|------|------|------|-----------|
| Downtime tollerabile > 4h | **Ideale** | OK | Overkill | OK |
| Downtime < 30min | No | **Ideale** | OK | Dipende |
| Downtime < 1min | No | No | **Ideale** | Possibile |
| Dimensione disco > 2TB | Lento | **Ideale** | Complesso | N/A |
| VM con stato complesso | **Ideale** | OK | Rischioso | No |
| Database production | No | Possibile | Rischioso | **Ideale** |
| Skill team basico | **Ideale** | OK | No | Dipende |

### Workflow Decisionale

```
VM da migrare
    │
    ├── Downtime accettabile? ──(SI, ore)──→ COLD MIGRATION
    │
    ├── Downtime < 30min? ─────(SI)────────→ WARM MIGRATION
    │       └── Disco > 500GB? ─(SI)──────→ rsync incrementale
    │
    ├── Near-zero downtime? ───(SI)────────→ LIVE MIGRATION
    │       ├── Database? ─────(SI)────────→ Replica nativa DB
    │       └── Stateless? ────(SI)────────→ DNS-based cutover
    │
    └── Applicazione nota? ────(SI)────────→ APP-LEVEL
            └── Re-deploy possibile? ──────→ Fresh install + data
```

---

## 2. Cold Migration (Offline)

### 2.1 Procedura Generale

```
VMware ESXi/vCenter              Proxmox VE
┌──────────────┐                ┌──────────────┐
│  VM (spenta) │                │  Storage     │
│  ┌────────┐  │   1.Export     │  destination │
│  │ VMDK   │──┼───────────────→│              │
│  └────────┘  │   2.Convert    │  ┌────────┐  │
│              │───────────────→│  │ qcow2  │  │
│              │   3.Import     │  └────────┘  │
│              │───────────────→│  4.Config VM │
└──────────────┘                └──────────────┘
```

### 2.2 Cold Migration — Windows Server

**Step 1: Preparazione su VMware**

```powershell
# Nella VM Windows, PRIMA di spegnere:

# Installare VirtIO drivers (CRITICO per evitare BSOD)
# Scaricare virtio-win ISO da: https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/
# Montare ISO e installare:
pnputil.exe /add-driver D:\vioscsi\2k22\amd64\*.inf /install
pnputil.exe /add-driver D:\NetKVM\2k22\amd64\*.inf /install
pnputil.exe /add-driver D:\Balloon\2k22\amd64\*.inf /install
pnputil.exe /add-driver D:\viostor\2k22\amd64\*.inf /install
pnputil.exe /add-driver D:\qxldod\2k22\amd64\*.inf /install

# Rimuovere VMware Tools
"C:\Program Files\VMware\VMware Tools\VMwareToolsUpgrader.exe" /remove

# Disinstallare componenti VMware da Programmi e Funzionalità

# Pulire e spegnere
ipconfig /flushdns
shutdown /s /t 0
```

**Step 2: Export VMDK da ESXi**

```bash
# Via SSH su ESXi
cd /vmfs/volumes/datastore1/WindowsServer/

# Identificare file VMDK
ls -lh *.vmdk

# Copia via SCP verso host Proxmox
scp WindowsServer-flat.vmdk root@proxmox:/tmp/migration/

# Alternativa: ovftool su workstation
ovftool vi://root@esxi/WindowsServer /tmp/WindowsServer.ova
```

**Step 3: Conversione e Import su Proxmox**

```bash
# Sul nodo Proxmox
# Conversione VMDK → qcow2
qemu-img convert -f vmdk -O qcow2 -p \
  /tmp/migration/WindowsServer-flat.vmdk \
  /tmp/migration/WindowsServer.qcow2

# Creare VM vuota
qm create 200 \
  --name WindowsServer \
  --memory 8192 \
  --cores 4 \
  --cpu host \
  --net0 virtio,bridge=vmbr0 \
  --bios ovmf \
  --machine q35 \
  --efidisk0 local-lvm:1,efitype=4m,pre-enrolled-keys=1 \
  --scsihw virtio-scsi-single \
  --ostype win11

# Importare disco
qm importdisk 200 /tmp/migration/WindowsServer.qcow2 local-lvm

# Collegare disco alla VM
qm set 200 --scsi0 local-lvm:vm-200-disk-1,iothread=1,discard=on

# Impostare boot order
qm set 200 --boot order=scsi0

# Aggiungere CD-ROM con VirtIO ISO (backup)
qm set 200 --ide2 local:iso/virtio-win.iso,media=cdrom

# Avviare
qm start 200
```

### 2.3 Cold Migration — Linux Server

**Step 1: Preparazione su VMware**

```bash
# Nella VM Linux, PRIMA di spegnere

# Verificare moduli VirtIO
lsmod | grep virtio
# Se mancanti, caricarli
modprobe virtio_blk virtio_net virtio_scsi virtio_pci

# Aggiungere a initramfs (Debian/Ubuntu)
echo -e "virtio_blk\nvirtio_net\nvirtio_scsi\nvirtio_pci" >> /etc/initramfs-tools/modules
update-initramfs -u

# RHEL/CentOS
echo 'add_drivers+=" virtio_blk virtio_net virtio_scsi virtio_pci "' > /etc/dracut.conf.d/virtio.conf
dracut -f

# Verificare fstab — sostituire riferimenti device specifici con UUID
blkid
# Aggiornare /etc/fstab con UUID= invece di /dev/sdX

# Verificare GRUB per riferimenti a device VMware
cat /boot/grub/grub.cfg | grep -i vmware

# Rimuovere open-vm-tools
apt remove open-vm-tools open-vm-tools-desktop  # Debian/Ubuntu
yum remove open-vm-tools                        # RHEL/CentOS

# Installare qemu-guest-agent
apt install qemu-guest-agent   # Debian/Ubuntu
yum install qemu-guest-agent   # RHEL/CentOS

# Spegnere
shutdown -h now
```

**Step 2-3: Export, conversione e import identici alla procedura Windows** (con differenze nella configurazione VM)

```bash
# Configurazione VM per Linux
qm create 201 \
  --name LinuxServer \
  --memory 4096 \
  --cores 2 \
  --cpu host \
  --net0 virtio,bridge=vmbr0 \
  --bios ovmf \
  --machine q35 \
  --efidisk0 local-lvm:1,efitype=4m \
  --scsihw virtio-scsi-single \
  --ostype l26 \
  --agent enabled=1
```

---

## 3. Warm Migration (Semi-Online)

### 3.1 Concetto

La warm migration riduce il downtime eseguendo la copia bulk dei dati con la VM ancora in esecuzione, poi sincronizzando solo i delta prima del cutover finale.

```
Tempo ──────────────────────────────────────────────────►

FASE 1: Initial Sync          FASE 2: Delta Sync    FASE 3: Cutover
(VM running su VMware)        (VM running)           (breve stop)
┌──────────────────────┐      ┌──────────┐          ┌────────┐
│ Copia completa disco │      │ Solo diff │          │ Stop VM│
│ (background)         │      │ (veloce)  │          │ Final  │
│ ████████████████████ │      │ ██        │          │ sync   │
│ Ore / giorni         │      │ Minuti    │          │ Start  │
└──────────────────────┘      └──────────┘          └────────┘
                                                     ↑
                                                     │ Downtime
                                                     │ effettivo
                                                     │ (minuti)
```

### 3.2 Implementazione con qemu-img + rsync

```bash
# FASE 1: Snapshot VMware + copia iniziale
# Su VMware, creare snapshot della VM (senza spegnere)
# Esportare disco base

# Su host intermedio o Proxmox
qemu-img convert -f vmdk -O qcow2 -p \
  /tmp/base-disk.vmdk /tmp/vm-disk.qcow2

# FASE 2: Preparare delta
# Rimuovere snapshot su VMware (consolida i cambiamenti)
# Re-esportare il disco aggiornato
# Usare qemu-img rebase o rsync block-level

# FASE 3: Cutover
# Spegnere VM su VMware
# Sincronizzazione finale (solo blocchi modificati)
rsync -avP --inplace /tmp/final-disk.qcow2 root@proxmox:/var/lib/vz/images/200/

# Avviare su Proxmox
qm start 200
```

### 3.3 Warm Migration con CBT (Changed Block Tracking)

```bash
# Abilitare CBT su VMware (via PowerCLI)
$vm = Get-VM -Name "TargetVM"
$spec = New-Object VMware.Vim.VirtualMachineConfigSpec
$spec.ChangeTrackingEnabled = $true
$vm.ExtensionData.ReconfigVM($spec)

# Esportare blocchi modificati dopo snapshot
# Richiede VMware API / VDDK
# Tool come Veeam o script custom possono estrarre solo delta
```

---

## 4. Live/Minimal Downtime Migration

### 4.1 Approccio DNS-Based Cutover

```
                        DNS TTL = 300s (5min)
                              │
  Prima:  app.example.com ──→ 10.0.1.100 (VMware)
  Dopo:   app.example.com ──→ 10.0.1.200 (Proxmox)

Timeline:
  T-24h:  Ridurre TTL a 60s
  T-4h:   Sync finale dati
  T-0:    Cambiare record DNS
  T+5m:   Traffico migra verso Proxmox
  T+24h:  Ripristinare TTL normale
```

### 4.2 Database Log Shipping

```
VMware (Source)                    Proxmox (Target)
┌──────────────┐                  ┌──────────────┐
│  DB Primary  │ ──── WAL/Log ──→ │  DB Standby  │
│  (attivo)    │    streaming      │  (replica)   │
└──────────────┘                  └──────────────┘
        │                                │
   Al cutover:                     Promuovi a
   Stop applicazioni               Primary
   Verifica sync completo
   Redirect connessioni
```

**PostgreSQL Streaming Replication:**

```bash
# Sul target (Proxmox)
# postgresql.conf
primary_conninfo = 'host=10.0.1.100 port=5432 user=replicator'
restore_command = 'cp /var/lib/postgresql/archive/%f %p'

# Cutover
# Sul source: SELECT pg_switch_wal();
# Verifica: SELECT pg_last_wal_receive_lsn() sul target
# Promuovi: pg_ctl promote -D /var/lib/postgresql/data
```

**MySQL Replication:**

```sql
-- Sul target
CHANGE MASTER TO MASTER_HOST='10.0.1.100',
  MASTER_USER='repl_user', MASTER_PASSWORD='secure_pass',
  MASTER_AUTO_POSITION=1;
START SLAVE;

-- Cutover: STOP SLAVE; RESET SLAVE ALL;
```

### 4.3 Application-Level Replication Tools

| Applicazione | Metodo | Downtime Stimato |
|-------------|--------|-----------------|
| Active Directory | Promuovi nuovo DC, replica, trasferisci FSMO | < 5 min |
| SQL Server | Always On AG / Log Shipping | < 1 min |
| PostgreSQL | Streaming Replication + pg_promote | < 30 sec |
| MySQL/MariaDB | GTID Replication | < 1 min |
| Exchange | DAG con mailbox move | Seamless |
| File Server | DFS-R o rsync continuo | < 5 min |

---

## 5. virt-v2v — Conversione Automatizzata

### 5.1 Installazione

```bash
# Debian/Ubuntu
apt install virt-v2v libguestfs-tools

# RHEL/CentOS
yum install virt-v2v

# Verificare
virt-v2v --version
virt-v2v 2.x.x
```

### 5.2 Conversione Diretta da VMware

```bash
# Conversione da vCenter (richiede credenziali)
virt-v2v -i vmx \
  -ic 'vpx://administrator@vsphere.local@vcenter.lab/Datacenter/esxi-host?no_verify=1' \
  "VMName" \
  -o local -os /var/lib/vz/images/ \
  -of qcow2

# Da file VMDK locale
virt-v2v -i disk /path/to/disk.vmdk \
  -o local -os /tmp/output/ \
  -of qcow2

# Da OVA
virt-v2v -i ova /path/to/export.ova \
  -o local -os /tmp/output/ \
  -of qcow2
```

### 5.3 Opzioni Importanti

```bash
# Output diretto su Proxmox (via qemu)
virt-v2v -i ova vm.ova \
  -o qemu \
  -os /var/lib/vz/images/300/ \
  -of qcow2 \
  --root first \
  -v          # verbose per debug

# Forzare VirtIO driver injection per Windows
virt-v2v -i ova win-vm.ova \
  -o local -os /tmp/ \
  -of qcow2 \
  --install virtio-win

# Specificare la root partition
virt-v2v -i disk /path/to/disk.vmdk \
  --root /dev/sda2 \
  -o local -os /tmp/
```

### 5.4 Cosa Fa virt-v2v Automaticamente

- Rilevamento OS guest
- Rimozione VMware Tools / drivers
- Iniezione driver VirtIO (scsi, net, balloon)
- Riconfigurazione bootloader (GRUB)
- Aggiornamento initramfs/initrd
- Riconfigurazione rete (da vmxnet3 a virtio)
- Fix registry Windows per boot controller

### 5.5 Batch Conversion Script

```bash
#!/bin/bash
# batch-v2v.sh — Conversione batch di OVA files

INPUT_DIR="/tmp/ova-exports"
OUTPUT_DIR="/var/lib/vz/images"
LOG_DIR="/var/log/migration"
mkdir -p "$LOG_DIR"

for ova in "$INPUT_DIR"/*.ova; do
    vmname=$(basename "$ova" .ova)
    echo "[$(date)] Converting: $vmname"

    virt-v2v -i ova "$ova" \
      -o local -os "$OUTPUT_DIR/$vmname/" \
      -of qcow2 \
      -v 2>&1 | tee "$LOG_DIR/${vmname}.log"

    if [ $? -eq 0 ]; then
        echo "[$(date)] SUCCESS: $vmname"
    else
        echo "[$(date)] FAILED: $vmname" >> "$LOG_DIR/failures.log"
    fi
done
```

### 5.6 Troubleshooting virt-v2v

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| `inspection could not detect OS` | Disco criptato o FS sconosciuto | Usare `--root` manuale |
| `VirtIO drivers not found` | Package virtio-win mancante | `apt install virtio-win` |
| `unable to mount filesystem` | NTFS dirty | `ntfsfix /dev/sdX` prima |
| `not enough space` | Disco output pieno | Verificare spazio con `df -h` |
| Windows BSOD 0x7B | Driver storage non iniettati | Installare VirtIO pre-migrazione |

---

## 6. qemu-img convert — Deep Dive

### 6.1 Sintassi Completa

```bash
qemu-img convert [OPTIONS] SOURCE DEST

# Opzioni principali
#   -f FMT        formato sorgente (vmdk, raw, qcow2, vdi, vhd, vpc)
#   -O FMT        formato destinazione
#   -p             mostra progresso
#   -c             compressione (solo qcow2)
#   -o OPTIONS     opzioni formato (preallocation, cluster_size, etc.)
#   -S SIZE        sparse detection size
#   -t CACHE       cache mode (none, writeback, writethrough)
#   -T SRC_CACHE   source cache mode
```

### 6.2 Conversioni Comuni

```bash
# VMDK → qcow2 (più comune)
qemu-img convert -f vmdk -O qcow2 -p disk.vmdk disk.qcow2

# VMDK → qcow2 con compressione
qemu-img convert -f vmdk -O qcow2 -c -p disk.vmdk disk-compressed.qcow2

# VMDK → raw (per LVM/ZFS)
qemu-img convert -f vmdk -O raw -p disk.vmdk disk.raw

# qcow2 con preallocation (migliori performance)
qemu-img convert -f vmdk -O qcow2 -p \
  -o preallocation=metadata,lazy_refcounts=on \
  disk.vmdk disk.qcow2

# Con cluster size ottimizzato
qemu-img convert -f vmdk -O qcow2 -p \
  -o cluster_size=2M \
  disk.vmdk disk.qcow2
```

### 6.3 Gestione Split VMDK

```bash
# VMware spesso crea VMDK divisi in file da 2GB
# disk-s001.vmdk, disk-s002.vmdk, ... disk-s00N.vmdk
# Il file descriptor è: disk.vmdk

# qemu-img gestisce automaticamente i split VMDK tramite il descriptor
qemu-img convert -f vmdk -O qcow2 -p disk.vmdk output.qcow2

# Se il descriptor è corrotto, ricostruire:
cat disk-s*.vmdk > disk-flat.vmdk
qemu-img convert -f raw -O qcow2 -p disk-flat.vmdk output.qcow2
```

### 6.4 Estrazione da OVA

```bash
# OVA è un archivio TAR contenente OVF + VMDK
tar xvf vm-export.ova
# Risultato:
#   vm-export.ovf
#   vm-export-disk1.vmdk
#   vm-export.mf (manifest)

# Conversione del VMDK estratto
qemu-img convert -f vmdk -O qcow2 -p \
  vm-export-disk1.vmdk vm-disk.qcow2

# Info sul disco
qemu-img info vm-export-disk1.vmdk
```

### 6.5 Batch Conversion Script Avanzato

```bash
#!/bin/bash
# batch-convert.sh — Conversione batch con parallelismo

SRC_DIR="/tmp/vmdk-exports"
DST_DIR="/var/lib/vz/images"
PARALLEL=2  # conversioni simultanee
LOG="/var/log/batch-convert.log"

convert_disk() {
    local src="$1"
    local name=$(basename "$src" .vmdk)
    local dst="$DST_DIR/${name}.qcow2"

    echo "[$(date)] START: $name" >> "$LOG"

    qemu-img convert -f vmdk -O qcow2 -p \
      -o preallocation=metadata \
      "$src" "$dst" 2>&1

    if [ $? -eq 0 ]; then
        echo "[$(date)] DONE: $name ($(du -sh "$dst" | cut -f1))" >> "$LOG"
    else
        echo "[$(date)] FAIL: $name" >> "$LOG"
        return 1
    fi
}

export -f convert_disk
export DST_DIR LOG

find "$SRC_DIR" -name "*-flat.vmdk" -o -name "*.vmdk" ! -name "*-delta*" | \
  xargs -P "$PARALLEL" -I {} bash -c 'convert_disk "$@"' _ {}

echo "Conversione completata. Vedi $LOG"
```

### 6.6 Tabella Performance Formati

| Formato | Thin Provisioning | Snapshot | Compressione | I/O Performance |
|---------|:-:|:-:|:-:|:-:|
| raw | No | No | No | Migliore |
| qcow2 | Si | Si | Si | Buona |
| vmdk | Si | Si | No | Buona (VMware) |
| vdi | Si | Si | No | Media |

---

## 7. Clonezilla per Migrazione

### 7.1 Quando Usare Clonezilla

- VM con configurazioni disco complesse (multi-partition, LVM)
- Necessità di clonazione bit-per-bit fedele
- Migrazione di appliance dove virt-v2v fallisce
- Boot UEFI/Secure Boot con layout GPT complesso

### 7.2 Disk-to-Image

```bash
# 1. Boot Clonezilla Live sulla VM VMware (ISO)
# 2. Selezionare: device-image → local_dev o ssh_server
# 3. Salvare immagine su share NFS/SSH

# Comando diretto (expert mode)
/usr/sbin/ocs-sr -q2 -c -j2 -z5p -i 4096 -sfsck \
  -senc -p poweroff savedisk \
  "VMName-$(date +%Y%m%d)" sda

# Con compressione zstd (veloce)
/usr/sbin/ocs-sr -q2 -c -j2 -z6p -i 4096 \
  savedisk "image-name" sda
```

### 7.3 Restore su Proxmox

```bash
# 1. Creare VM su Proxmox con disco raw/qcow2
# 2. Boot Clonezilla ISO sulla VM Proxmox
# 3. Montare share con immagine
# 4. Restore

/usr/sbin/ocs-sr -g auto -e1 auto -e2 -r -j2 -c -scr -p reboot \
  restoredisk "image-name" sda
```

### 7.4 Network Cloning (Multicast)

```bash
# Server (sorgente — su VMware)
drbl-ocs -b -g auto -e1 auto -e2 -r -x -j2 -sc -p reboot \
  startdisk multicast_restore "image-name" sda

# Client (target — su Proxmox)
# Boot PXE da server Clonezilla
```

### 7.5 Gestione UEFI

```bash
# Clonezilla preserva la tabella GPT e la partizione EFI
# Assicurarsi che la VM Proxmox sia configurata con:
qm set VMID --bios ovmf --efidisk0 local-lvm:1,efitype=4m

# Se il boot fallisce dopo restore, ricostruire EFI entry:
# Boot da live Linux
efibootmgr -c -d /dev/sda -p 1 -L "Linux" -l '\EFI\ubuntu\shimx64.efi'
```

---

## 8. Tool Commerciali a Confronto

### 8.1 Matrice Comparativa

| Caratteristica | Veeam B&R | NAKIVO | Carbonite Migrate | PlateSpin |
|---------------|-----------|--------|-------------------|-----------|
| **Licenza** | Per-socket/VM | Per-VM | Per-VM | Per-VM |
| **Costo stimato** | $$$ | $$ | $$$ | $$$$ |
| **V2V VMware→KVM** | Si (via restore) | Si | Si (nativo) | Si |
| **Incremental sync** | CBT-based | CBT-based | Block-level | Block-level |
| **Windows support** | Eccellente | Buono | Eccellente | Eccellente |
| **Linux support** | Buono | Buono | Buono | Buono |
| **Cutover automatico** | No | No | Si | Si |
| **GUI** | Si | Si (web) | Si | Si |
| **Free tier** | Community Ed. (10 VM) | Trial 15gg | No | No |
| **Proxmox nativo** | Restore su KVM | No | No | No |

### 8.2 Veeam Backup & Replication

```
Workflow Veeam per migrazione:
1. Backup VM da vCenter (con CBT)
2. Restore "to different location" su host KVM/Proxmox
3. Veeam converte automaticamente disco e driver

Pro: ✓ Già presente in molti ambienti VMware
     ✓ Community Edition gratuita per 10 VM
     ✓ Conversione driver automatica
Con: ✗ Non supporta Proxmox nativamente
     ✗ Richiede host KVM intermediario
     ✗ Configurazione VM manuale post-restore
```

### 8.3 Approccio Consigliato per PMI

Per ambienti < 50 VM, il metodo open-source è spesso sufficiente:

```
Raccomandazione:
┌─────────────────────────────────────────────┐
│  < 10 VM:  qemu-img + configurazione manuale│
│  10-30 VM: virt-v2v batch script            │
│  30-50 VM: virt-v2v + Ansible automation    │
│  > 50 VM:  Valutare tool commerciale        │
└─────────────────────────────────────────────┘
```

---

## 9. Migrazione Incrementale con rsync

### 9.1 Block-Level Sync con rsync

```bash
# Metodo: convertire il disco una volta, poi sincronizzare
# solo i blocchi modificati usando rsync su file raw

# Step 1: Conversione iniziale (VM running)
# Snapshot VMware → export VMDK → convert to raw
qemu-img convert -f vmdk -O raw -p disk.vmdk disk.raw

# Step 2: Trasferimento iniziale
rsync -avP --progress disk.raw root@proxmox:/var/lib/vz/images/200/

# Step 3: Sync incrementali (ripetere N volte)
# Ogni sync è più veloce perché trasferisce solo blocchi modificati
rsync -avP --inplace --no-whole-file \
  disk.raw root@proxmox:/var/lib/vz/images/200/disk.raw

# Step 4: Cutover finale
# Spegnere VM su VMware
# Ultima sync (pochi blocchi)
rsync -avP --inplace --no-whole-file \
  disk.raw root@proxmox:/var/lib/vz/images/200/disk.raw

# Avviare su Proxmox
```

### 9.2 Con LVM Snapshots (Linux Guest)

```bash
# Dentro la VM Linux su VMware

# Step 1: Creare snapshot LVM
lvcreate -L 10G -s -n snap_root /dev/vg0/root

# Step 2: Sync iniziale del filesystem
rsync -aAXHv --progress --delete \
  / root@proxmox-vm:/  \
  --exclude={/dev/*,/proc/*,/sys/*,/tmp/*,/run/*,/mnt/*,/media/*}

# Step 3: Rimuovere snapshot, crearne uno nuovo
lvremove /dev/vg0/snap_root
lvcreate -L 10G -s -n snap_root /dev/vg0/root

# Step 4: Sync incrementale
rsync -aAXHv --progress --delete \
  / root@proxmox-vm:/ \
  --exclude={/dev/*,/proc/*,/sys/*,/tmp/*,/run/*,/mnt/*,/media/*}

# Step 5: Cutover
# Stop servizi, sync finale, aggiornare GRUB e fstab, reboot da Proxmox
```

### 9.3 Stima Tempi di Sync

| Dimensione Disco | Banda 1Gbps | Banda 10Gbps | Delta Tipico (1%) |
|-----------------|-------------|-------------|-------------------|
| 100 GB | ~15 min | ~90 sec | ~9 sec |
| 500 GB | ~70 min | ~7 min | ~42 sec |
| 1 TB | ~140 min | ~14 min | ~84 sec |
| 2 TB | ~280 min | ~28 min | ~168 sec |

---

## 10. Migrazione di Applicazioni Stateful

### 10.1 Database Server

```
Strategia: Replica nativa → Promuovi → Redirect

SQL Server (Always On / Log Shipping):
1. Installare SQL Server su VM Proxmox
2. Configurare Log Shipping: VMware → Proxmox
3. Monitorare ritardo replica
4. Cutover: stop app → final log restore → online DB
5. Aggiornare connection string

PostgreSQL:
1. pg_basebackup dal source
2. Configurare streaming replication
3. Monitorare pg_stat_replication
4. pg_ctl promote sul target

MySQL/MariaDB:
1. mysqldump --master-data + replica GTID
2. START SLAVE sul target
3. Verificare Seconds_Behind_Master = 0
4. STOP SLAVE → applicazioni puntano al nuovo
```

### 10.2 File Server

```bash
# Windows File Server (multi-stage robocopy)
# Stage 1: copia bulk (VM running, può richiedere ore)
robocopy \\source\share \\target\share /MIR /COPY:DATSOU /MT:16 /R:1 /W:1 /LOG:C:\robocopy1.log

# Stage 2: sync delta (ripetere giornalmente)
robocopy \\source\share \\target\share /MIR /COPY:DATSOU /MT:16 /R:1 /W:1 /LOG:C:\robocopy2.log

# Stage 3: cutover (fuori orario, con permessi)
robocopy \\source\share \\target\share /MIR /COPY:DATSO /SEC /MT:16 /LOG:C:\robocopy-final.log

# Linux File Server
rsync -aAXHv --progress --delete /source/ /target/
```

### 10.3 Domain Controller

```
⚠ MAI clonare o convertire direttamente un Domain Controller!

Procedura corretta:
1. Creare nuova VM Windows su Proxmox
2. Join al dominio
3. Promuovere a Domain Controller (dcpromo / Install-ADDSDomainController)
4. Attendere replica completa AD
   repadmin /replsummary
   repadmin /showrepl
5. Trasferire ruoli FSMO al nuovo DC
   Move-ADDirectoryServerOperationMasterRole -Identity "newDC" -OperationMasterRole 0,1,2,3,4
6. Verificare funzionalità
   dcdiag /v
   nltest /dsgetdc:domain.local
7. Demote il vecchio DC su VMware
8. Rimuovere metadata del vecchio DC se necessario
```

### 10.4 Mail Server

```bash
# Exchange: usare Database Availability Group (DAG)
# 1. Installare Exchange su nuova VM Proxmox
# 2. Aggiungere al DAG esistente
# 3. Spostare mailbox: New-MoveRequest -Identity user@domain.com -TargetDatabase "DB-Proxmox"
# 4. Aggiornare record MX
# 5. Aggiornare SPF, DKIM, DMARC

# Zimbra
# 1. Installare Zimbra su nuova VM
# 2. Export/Import mailbox
zmmailbox -z -m user@domain.com getRestURL "//?fmt=tgz" > /backup/user.tgz
zmmailbox -z -m user@domain.com postRestURL "//?fmt=tgz" /backup/user.tgz
# 3. Aggiornare DNS
```

### 10.5 Checklist Post-Migrazione Applicazioni Stateful

```
□ Verificare integrità dati (checksum, record count)
□ Testare tutte le connessioni client
□ Verificare backup funzionante sulla nuova piattaforma
□ Aggiornare monitoring e alerting
□ Aggiornare documentazione (IP, hostname, path)
□ Aggiornare procedure di DR
□ Mantenere VM VMware spenta per 2 settimane (rollback)
□ Decommissionare VM VMware dopo periodo di osservazione
```

---

## Best Practice Generali

1. **Testare sempre in ambiente non-production** prima della migrazione reale
2. **Documentare ogni step** eseguito per garantire ripetibilità
3. **Avere un piano di rollback** chiaro per ogni VM migrata
4. **Migrare in wave** (gruppi) ordinati per criticità crescente
5. **Validare i backup** della VM sorgente prima di iniziare
6. **Comunicare i downtime** pianificati a tutti gli stakeholder
7. **Monitorare attivamente** le prime 48 ore post-migrazione
8. **Non decommissionare** la sorgente VMware per almeno 2 settimane

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — virt-v2v `-i vmx -ic vpx://` direct.** virt-v2v puo collegarsi direttamente al vCenter senza passaggio intermedio via OVA: `virt-v2v -i vmx -ic 'vpx://administrator@vsphere.local@vcenter.lab/Datacenter/host?no_verify=1' "VMName" -o local -os /var/lib/vz/images/ -of qcow2`. Vantaggio: niente export OVA pesante, conversione streaming. Svantaggio: collegamento attivo a vCenter durante tutta la conversione (ore per dischi grandi), eventuale rete instabile rompe tutto. Per dischi > 500 GB raccomandato comunque l'export OVA prima e conversione locale.

> **Errore comune — `qemu-img convert` su disco origine VMware in scrittura.** Lanciare `qemu-img convert` su un VMDK *montato* da una VM running su ESXi produce risultati corrotti (i blocchi cambiano durante la lettura). Soluzione: o spegnere la VM (cold), o esportare prima con `ovftool` su una copia statica, o usare snapshot VMware come "punto consistente" (`Snapshot.create`) e leggere dallo snapshot. virt-v2v gestisce la sincronizzazione automaticamente quando si usa input `vpx://`.

> **Caso reale — UUID disk drift dopo conversione.** Dopo `qemu-img convert` da VMDK a qcow2, una VM Linux non riusciva a montare i filesystem `/home` e `/var`. Causa: `/etc/fstab` referenziava `/dev/sda2` e `/dev/sda3`, ma su Proxmox con `virtio-scsi-single` i dischi diventano `/dev/sda` (root) ma anche reordering. Soluzione: usare UUID in `/etc/fstab` (`blkid` per ottenere gli UUID) prima della conversione. Stessa cura per Windows: il registry `HKLM\SYSTEM\MountedDevices` mappa i drive letter a signature disco; `virt-v2v` lo aggiusta, `qemu-img` da solo no.

---

## Esercizi

1. **Concettuale — scelta strategia per 4 VM.** Scegliere la strategia (cold/warm/live/app) e motivare in 2 righe per: (a) Postgres 200 GB, downtime ammesso 30 min weekend; (b) web server stateless dietro load balancer, downtime ammesso 0 (deve restare online); (c) file server 800 GB con SMB, downtime ammesso 4 ore notturne; (d) cluster MSSQL Always On Availability Group, downtime ammesso < 1 min. *Risposte:* (a) cold (semplicita, finestra ampia); (b) blue-green con load balancer (di fatto live application-level: si crea la VM su Proxmox, si include nel pool, si rimuove da VMware); (c) warm (rsync block-level + cutover SMB); (d) app-level Always On (aggiungere replica su Proxmox, sync, fail-over, rimuovere replica VMware).

2. **Lab — cold migration completa di una VM Linux.** Su una VM Debian 12 di test su VMware, eseguire la procedura completa: pre-config initramfs con virtio modules, rimozione open-vm-tools, installazione qemu-guest-agent, shutdown. Export VMDK via `ovftool`. Conversione `qemu-img convert -f vmdk -O qcow2 -p`. Creazione VM su Proxmox con `qm create` + `qm importdisk` + `qm set --scsi0 ...`. Boot e verifica IP, SSH, `qemu-ga --version`. Documentare tempi e anomalie.

3. **Scenario — DNS TTL drop tra cutover.** Hai una VM web con record A `app.example.com` e TTL 3600 s, e devi fare cutover in 48 ore. Argomenta in 8 righe la sequenza: (a) abbassare TTL adesso (T-48h), aspettare propagazione, (b) eseguire migrazione, (c) cambio IP DNS al cutover, (d) cosa fare se ci sono client che hanno cached il vecchio IP per piu di 60 s. *Risposta attesa:* (a) abbassare a 60 s, (b)+(c) come descritto; (d) il rollback DNS non basta, serve mantenere il vecchio IP raggiungibile per 5-10 min con un proxy che inoltra al nuovo, oppure mantenere l'host vecchio acceso mappando i client residui via firewall NAT. Il rischio "client cached" non si elimina con TTL, si mitiga.

4. **Stretch — script batch conversione con retry.** Scrivere uno script bash che, dato un directory `/tmp/ova-exports/` con N file `.ova`, esegua per ognuno: (a) extract; (b) `qemu-img convert -f vmdk -O qcow2`; (c) check checksum SHA-256 input vs output (logico, non bit-per-bit); (d) `qm importdisk` + `qm set` con VMID auto-assegnato; (e) log strutturato JSON `migration-batch.jsonl`; (f) retry 3x con backoff esponenziale su singolo failure; (g) email finale con summary. Riferimento: capitolo "Batch Conversion Script" del modulo.

## Auto-valutazione

1. Quattro strategie di migrazione e per ognuna: downtime tipico, complessita, tool principale.
2. Pre-step necessari per cold migration di una VM Linux Debian 12 (3 azioni minime).
3. Pre-step necessari per cold migration di una VM Windows Server 2022 (3 azioni minime).
4. Differenza fra `qemu-img convert -O qcow2 -c` e `-O qcow2 -o preallocation=metadata` — quando l'una vs l'altra?
5. Cos'e CBT (Changed Block Tracking) di VMware e come si abilita?
6. Quali database supportano replica nativa per cutover live (PostgreSQL, MySQL, SQL Server, Exchange)?
7. Differenza tra rsync `-aP` e rsync `-aP --inplace --no-whole-file` per warm migration?
8. Decommissioning del cluster VMware: dopo quanto tempo dall'ultima wave migrata?

## Letture primarie consigliate

- [`V2V-MAN`] virt-v2v(1) man page. https://libguestfs.org/virt-v2v.1.html
- [`V2V-INPUT`] virt-v2v input modes. https://libguestfs.org/virt-v2v-input-vmware.1.html
- [`QEMU-IMG`] qemu-img(1). https://www.qemu.org/docs/master/tools/qemu-img.html
- [`PVE-MIGRATE-V2V`] Proxmox VE — Migration of servers. https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE
- VirtIO Windows drivers. https://github.com/virtio-win/virtio-win-pkg-scripts
- rsync man page. https://download.samba.org/pub/rsync/rsync.1
- Clonezilla. https://clonezilla.org/
- [`PG-REPL`] PostgreSQL Streaming Replication. https://www.postgresql.org/docs/current/warm-standby.html#STREAMING-REPLICATION
- [`MYSQL-REPL`] MySQL Replication. https://dev.mysql.com/doc/refman/8.0/en/replication.html

## Collegamenti incrociati

- Modulo 06.2 — `migrazione-con-virt-v2v.md`: deep dive sul tool virt-v2v.
- Modulo 06.3 — `live-migration-minimo-downtime.md`: deep dive sulle strategie live e DNS-based.
- Modulo 07.1 — `../07-MIGRAZIONE-NETWORKING/ip-planning-dns-dhcp-firewall.md`: pianificazione IP/DNS per il cutover.
- Modulo 08.1 — `../08-MIGRAZIONE-STORAGE/conversione-vmdk-qcow2-raw.md`: deep dive su qemu-img.
- Modulo 09.1, 09.2, 09.3, 09.4 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/`: applicazione delle strategie a workload specifici.
- Modulo 16.2 — `../16-PROCEDURE-OPERATIVE-E-RUNBOOK/runbook-migrazione-cluster-completo.md`: runbook completo eseguibile.
- Modulo 17.2 — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-driver-e-dispositivi.md`: troubleshooting BSOD/no-boot post-migrazione.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Cold migration** | VM spenta, export → convert → import → boot. Downtime alto, rischio basso. |
| **Warm migration** | Bulk copy con VM running, poi delta sync, poi cutover breve. Downtime medio. |
| **Live migration (DNS-based)** | Replica continua + cambio DNS; downtime quasi zero per stateless. Per stateful, replica DB. |
| **App-level migration** | Replica nativa dell'applicazione (Postgres replication, AD replication, Always On AG, DAG). |
| **CBT (Changed Block Tracking)** | Feature VMware che traccia i blocchi modificati dall'ultimo backup; usato da Veeam/etc. |
| **VirtIO drivers** | Driver paravirtualizzati per disco/rete/balloon su KVM. Sostituiscono PVSCSI/VMXNET3. |
| **`pnputil.exe`** | CLI Windows per add/remove driver dallo store del sistema. |
| **initramfs** | Initial RAM filesystem caricato dal bootloader prima del kernel pieno; deve avere i driver storage del nuovo target. |
| **`dracut`** | Tool RHEL/Fedora per generare initramfs. |
| **`update-initramfs`** | Tool Debian/Ubuntu per generare initramfs. |
| **OVF/OVA** | Open Virtualization Format (descrittore) / Open Virtualization Appliance (archivio TAR). |
| **`ovftool`** | CLI VMware per export/import OVF/OVA. |
| **`govc`** | CLI Go alternativo per vSphere API (no PowerShell required). |
| **TTL DNS** | Time To Live di un record DNS, in secondi. Per cutover, abbassare a 60 s 24-48 h prima. |
| **FIN_WAIT2** | Stato TCP dopo il close di una sessione; il drain di FIN_WAIT2 puo richiedere fino a 2 * MSL (60 s default). |
| **Drain delle connessioni** | Periodo prima del cutover in cui non si accettano nuove connessioni e si aspettano le esistenti a chiudersi. |
