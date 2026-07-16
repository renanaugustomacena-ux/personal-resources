# Tutorial Linux 25 — ZFS: Guida Operativa Completa

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** ZFS pool, dataset, snapshot, clone, scrub, send/receive, RAIDZ
> **Prerequisiti:** `tutorial_linux_06_storage.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
ZFS
│
├── Pool (zpool)
│   ├── RAIDZ1/2/3 — striping con parity
│   ├── Mirror — mirroring
│   └── stripe — no ridondanza
│
├── Dataset (zfs)
│   ├── filesystem — dataset montabile
│   ├── volume (zvol) — block device
│   └── snapshot — punto nel tempo
│
├── Funzionalità
│   ├── Copy-on-Write (CoW)
│   ├── Deduplicazione
│   ├── Compressione (lz4, zstd)
│   ├── Encryption (AES-256)
│   └── Self-healing
│
└── Operazioni
    ├── scrub — verifica integrità
    ├── send/receive — backup/migrazione
    ├── snapshot + rollback
    └── zpool replace (hot spare)
```

---

# Parte A — Installazione e pool

---

## A1. Installazione ZFS

```bash
# Ubuntu
apt install zfsutils-linux
# Verifica
modprobe zfs
dmesg | grep zfs

# RHEL/Fedora
dnf install https://zfsonlinux.org/epel/zfs-release-2-3$(rpm --eval "%{dist}").noarch.rpm
dnf install zfs
/sbin/modprobe zfs
```

---

## A2. Creare pool

```bash
# Pool su un singolo disco (no ridondanza, test/sviluppo)
zpool create tank /dev/sdb

# Mirror (come RAID-1)
zpool create tank mirror /dev/sdb /dev/sdc

# RAIDZ1 (parity singola — come RAID-5, min 3 dischi)
zpool create tank raidz1 /dev/sdb /dev/sdc /dev/sdd

# RAIDZ2 (doppia parity — come RAID-6, min 4 dischi)
zpool create tank raidz2 /dev/sdb /dev/sdc /dev/sdd /dev/sde

# RAIDZ3 (tripla parity — max tolleranza guasti)
zpool create tank raidz3 /dev/sdb /dev/sdc /dev/sdd /dev/sde /dev/sdf /dev/sdg

# Pool con hot spare
zpool create tank raidz2 /dev/sdb /dev/sdc /dev/sdd /dev/sde spare /dev/sdf

# Pool con cache (SSD L2ARC) e log (ZIL su SSD)
zpool create tank raidz2 /dev/sdb /dev/sdc /dev/sdd \
    cache /dev/nvme0n1p1 \       # L2ARC: cache lettura su SSD
    log /dev/nvme0n1p2            # ZIL: log sincrono su SSD

# Stato pool
zpool status
zpool status tank
zpool list

# Proprietà pool
zpool get all tank
zpool set autoexpand=on tank      # espandi automaticamente quando disco viene rimpiazzato
zpool set autoreplace=on tank     # rimpiazza automaticamente hot spare
```

> **Analogia:** Un pool ZFS è come un cassetto di sicurezza virtuale che conosce l'integrità di ogni singolo documento (checksum). RAIDZ2 è come un sistema con due copie di riserva: puoi perdere due "cassetti fisici" (dischi) e tutti i documenti sono ancora al sicuro. La magia del Copy-on-Write è che ogni modifica crea una nuova versione senza distruggere quella vecchia — come scrivere su un nuovo foglio piuttosto che cancellare quello esistente.

---

# Parte B — Dataset e filesystem

---

## B1. Creare dataset

```bash
# Dataset (filesystem)
zfs create tank/dati
zfs create tank/backup
zfs create -p tank/web/html    # -p: crea directory intermedie

# Monta automaticamente sotto il pool
ls /tank/                      # /tank/dati, /tank/backup, /tank/web

# Proprietà dataset
zfs set mountpoint=/var/www tank/web/html
zfs set compression=lz4 tank/dati       # abilita compressione
zfs set compression=zstd tank/backup    # zstd: migliore ratio
zfs set atime=off tank/dati             # disabilita update atime
zfs set recordsize=1M tank/backup       # per file grandi (default 128K)
zfs set quota=100G tank/dati            # massimo 100GB
zfs set reservation=50G tank/dati       # garantisce 50GB

# Visulizza proprietà
zfs get all tank/dati
zfs get compression,quota,used tank/dati

# Lista dataset
zfs list
zfs list -r tank                        # ricorsivo
zfs list -t snapshot                    # solo snapshot
```

---

## B2. Snapshot

```bash
# Crea snapshot (istantaneo, nessun costo iniziale)
zfs snapshot tank/dati@2024-01-15
zfs snapshot -r tank@2024-01-15        # -r: ricorsivo (tutto il pool)

# Lista snapshot
zfs list -t snapshot
zfs list -t snapshot tank/dati

# Rollback a snapshot (distrugge modifiche posteriori)
zfs rollback tank/dati@2024-01-15
# Se ci sono snapshot più recenti:
zfs rollback -r tank/dati@2024-01-15   # -r: rimuovi snapshot più recenti

# Accedi ai file in uno snapshot (senza rollback)
ls /tank/dati/.zfs/snapshot/2024-01-15/   # cartella nascosta automatica

# Clone da snapshot (dataset basato su snapshot)
zfs clone tank/dati@2024-01-15 tank/dati-test
# Il clone condivide blocchi con l'originale → nessun spazio extra inizialmente

# Rimuovi snapshot
zfs destroy tank/dati@2024-01-15
zfs destroy -r tank@2024-01-15          # ricorsivo
zfs destroy tank/dati@2024-01-01%2024-01-31  # range (da a)

# Automatizza snapshot con cron
cat > /etc/cron.d/zfs-snapshot << 'EOF'
# Snapshot orario
0 * * * * root zfs snapshot -r tank@$(date +%Y%m%d-%H%M)
# Pulizia: mantieni solo ultimi 24
0 1 * * * root zfs list -t snapshot -H -o name | grep "tank@" | head -n -24 | xargs -r zfs destroy
EOF
```

---

# Parte C — Backup con send/receive

---

## C1. zfs send/receive

```bash
# Backup incrementale efficiente (trasferisce solo modifiche)

# --- Server Sorgente ---

# Primo backup (full)
zfs send tank/dati@2024-01-01 | ssh backup-server "zfs receive backup-pool/dati"

# Backup incrementale
zfs send -i tank/dati@2024-01-01 tank/dati@2024-01-02 \
    | ssh backup-server "zfs receive backup-pool/dati"

# Con compressione durante trasferimento
zfs send tank/dati@2024-01-02 \
    | lz4 | ssh backup-server "lz4 -d | zfs receive backup-pool/dati"

# Tutto il pool (ricorsivo)
zfs send -R tank@2024-01-15 | ssh backup-server "zfs receive -F backup-pool"

# Migrazione tra server
zfs send -Rv tank/dati@snapshot-migrazione \
    | pv -b                           # pv mostra progresso
    | ssh nuovo-server "zfs receive nuovo-pool/dati"

# --- Script backup automatico ---
#!/usr/bin/env bash
set -euo pipefail

POOL="tank"
DATASET="dati"
SNAPSHOT_NAME="auto-$(date +%Y%m%d-%H%M)"
REMOTE="backup@backup-server.it"
REMOTE_POOL="backup-pool"

# Crea nuovo snapshot
zfs snapshot "$POOL/$DATASET@$SNAPSHOT_NAME"

# Trova ultimo snapshot inviato
ULTIMO=$(zfs list -H -t snapshot -o name "$POOL/$DATASET" | \
         grep "@auto-" | head -n -1 | tail -1)

if [[ -n "$ULTIMO" ]]; then
    PREV_SNAP="${ULTIMO##*@}"
    echo "Invio incrementale da @$PREV_SNAP a @$SNAPSHOT_NAME"
    zfs send -i "$POOL/$DATASET@$PREV_SNAP" "$POOL/$DATASET@$SNAPSHOT_NAME" \
        | ssh "$REMOTE" "zfs receive -F $REMOTE_POOL/$DATASET"
else
    echo "Primo backup (full)"
    zfs send "$POOL/$DATASET@$SNAPSHOT_NAME" \
        | ssh "$REMOTE" "zfs receive $REMOTE_POOL/$DATASET"
fi

echo "Backup completato: $SNAPSHOT_NAME"
```

---

# Parte D — Manutenzione e sicurezza

---

## D1. Scrub e sostituzione disco

```bash
# Scrub — verifica integrità completa (legge tutti i dati)
zpool scrub tank

# Stato scrub
zpool status tank
# scrub: scrub in progress since Mon Jan 15 02:00:00 2024
#   5.32G scanned, 1.28G issued, 512G total
#   0 repaired, 0 errors

# Pianifica scrub mensile
echo "0 2 1 * * root zpool scrub tank" > /etc/cron.d/zfs-scrub

# Sostituzione disco guasto
# 1. Vedi disco guasto
zpool status
# sdc: FAULTED - too many errors

# 2. Sostituisci (può avvenire a caldo su RAIDZ)
zpool replace tank /dev/sdc /dev/sdg
# Ricostruzione automatica (resilver)

# 3. Monitorizza resilver
zpool status tank
# scan: resilver in progress 14% done, 0:32:54 to go
```

---

## D2. Crittografia ZFS (nativa)

```bash
# Dataset cifrato
zfs create -o encryption=aes-256-gcm \
           -o keylocation=prompt \
           -o keyformat=passphrase \
           tank/segreti

# Load chiave dopo reboot
zfs load-key tank/segreti    # chiede passphrase
zfs mount tank/segreti

# Con chiave da file
zfs create -o encryption=aes-256-gcm \
           -o keylocation=file:///etc/zfs/tank-segreti.key \
           -o keyformat=raw \
           tank/segreti
# Genera chiave: dd if=/dev/urandom bs=32 count=1 > /etc/zfs/tank-segreti.key
# chmod 400 /etc/zfs/tank-segreti.key
```

---

# Parte E — Riepilogo

## Comandi essenziali

| Operazione | Comando |
|---|---|
| Crea pool RAIDZ2 | `zpool create tank raidz2 sdb sdc sdd sde` |
| Stato pool | `zpool status` |
| Crea dataset | `zfs create tank/dati` |
| Abilita compressione | `zfs set compression=lz4 tank/dati` |
| Crea snapshot | `zfs snapshot tank/dati@nome` |
| Lista snapshot | `zfs list -t snapshot` |
| Rollback | `zfs rollback tank/dati@nome` |
| Send/receive | `zfs send tank/dati@snap \| ssh srv "zfs receive pool/dati"` |
| Scrub | `zpool scrub tank` |
| Sostituisci disco | `zpool replace tank /dev/sdc /dev/sdg` |

## ZFS vs LVM+ext4

| Aspetto | LVM+ext4 | ZFS |
|---|---|---|
| Checksum dati | No | Sì (ogni blocco) |
| Snapshot | Sì (CoW) | Sì (CoW, più efficiente) |
| Compressione | No | Sì (in-line) |
| Deduplica | No | Sì |
| RAID | LVM+mdadm | Nativo RAIDZ |
| Send/receive | No | Sì |
| Complessità | Media | Alta |

## Prossimi passi

- `tutorial_linux_26_docker.md` — Docker operativo
- `tutorial_linux_06_storage.md` — LVM (alternativa ZFS)
