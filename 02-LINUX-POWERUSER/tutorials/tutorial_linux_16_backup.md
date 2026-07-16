# Tutorial Linux 16 — Backup: rsync, tar, borgbackup, restic, snapshot

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** strategie backup, rsync, borgbackup, restic, LVM snapshot, validazione
> **Prerequisiti:** `tutorial_linux_06_storage.md`, `tutorial_linux_10_ssh_avanzato.md`
> **Durata stimata:** 12-16 ore

---

## Mappa concettuale

```
Backup Linux
│
├── Strategie
│   ├── 3-2-1: 3 copie, 2 media, 1 offsite
│   ├── Full / Incrementale / Differenziale
│   └── RPO e RTO
│
├── rsync — sincronizzazione efficiente
│   ├── Locale, remoto (SSH), --link-dest incremental
│   └── Esclusioni, preserva permessi
│
├── tar — archivio compresso
│   ├── tar czf — crea
│   ├── Incrementale con --listed-incremental
│   └── Split per file grandi
│
├── borgbackup — backup deduplicato
│   ├── init, create, list, extract, check
│   ├── Deduplicazione blocchi
│   └── Cifratura AES-256
│
├── restic — moderno, cloud-native
│   ├── Repository: locale, S3, B2, SFTP
│   ├── Deduplicazione e compressione
│   └── Forget / prune policy
│
└── Test e validazione
    ├── Restore test mensile
    ├── Checksum verifica
    └── Alert su fallimento
```

---

# Parte A — rsync

---

## A1. rsync: sincronizzazione directory

```bash
# Sintassi base
rsync [opzioni] sorgente/ destinazione/
# NOTA: trailing slash su sorgente = copia contenuto (non la directory stessa)

# Opzioni fondamentali
# -a (--archive): preserva permessi, proprietario, timestamp, symlink, ricorsivo
# -v: verbose
# -z: comprimi durante trasferimento (utile su rete lenta)
# -P: progresso + resume partial transfers
# -n (--dry-run): simula senza eseguire
# --delete: rimuove file in destinazione non più in sorgente
# --exclude: esclude pattern

# Backup locale
rsync -av --delete /home/mario/ /backup/mario/
rsync -av --delete --exclude='.cache' --exclude='*.tmp' /home/ /backup/home/

# Backup remoto via SSH
rsync -avz --delete -e "ssh -p 2222" /var/www/ mario@backup.esempio.it:/backup/www/

# Backup con esclusioni multiple
rsync -av --delete \
    --exclude='.git' \
    --exclude='node_modules/' \
    --exclude='*.log' \
    --exclude='.cache/' \
    --exclude='__pycache__/' \
    /home/mario/progetti/ /backup/progetti/

# File di esclusioni
cat > /etc/backup-excludes.txt << 'EOF'
.cache
.local/share/Trash
*.tmp
*.log
node_modules/
__pycache__/
.git
EOF
rsync -av --exclude-from=/etc/backup-excludes.txt /home/ /backup/

# Progress per file grandi
rsync -avP --delete /var/lib/postgresql/ /backup/postgres/
```

> **Analogia:** rsync è come un corriere efficiente che conosce già cosa c'è al destinatario. Invece di portare tutto da capo, confronta checksum e trasporta solo le differenze. `--delete` è la pulizia: rimuove dalla destinazione ciò che non c'è più nella sorgente, mantenendo le due copie identiche.

---

## A2. Backup incrementale con rsync --link-dest

```bash
# Tecnica: hard link per file non modificati
# Risultato: ogni backup sembra completo ma occupa solo lo spazio delle differenze

BACKUP_DIR="/backup/home"
SORGENTE="/home/mario"
DATA=$(date +%Y-%m-%d_%H%M%S)
ULTIMO_LINK=$(ls -1d "$BACKUP_DIR"/20* 2>/dev/null | tail -1)

if [ -n "$ULTIMO_LINK" ]; then
    # Usa hard link per file invariati
    rsync -av --delete \
        --link-dest="$ULTIMO_LINK" \
        "$SORGENTE/" \
        "$BACKUP_DIR/$DATA/"
else
    # Prima backup: full copy
    rsync -av "$SORGENTE/" "$BACKUP_DIR/$DATA/"
fi

# Rimuovi backup più vecchi di 30 giorni
find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +30 -exec rm -rf {} \;

# Quanto spazio occupano i backup? (hard link contati una volta)
du -sh "$BACKUP_DIR"
```

---

# Parte B — borgbackup

---

## B1. borg: backup deduplicato e cifrato

```bash
# Installazione
apt install borgbackup
# oppure
pip install borgbackup

# Inizializza repository cifrato
borg init --encryption=repokey-blake2 /backup/borg-repo
# Salva la passphrase in posto sicuro!
# Salva anche: borg key export /backup/borg-repo > chiave-backup.txt

# Imposta variabili d'ambiente (no password in history)
export BORG_PASSPHRASE="la-mia-passphrase-segreta"
export BORG_REPO="/backup/borg-repo"

# Crea backup
borg create \
    --verbose \
    --stats \
    --show-rc \
    --compression lz4 \
    --exclude-caches \
    --exclude '/home/*/.cache' \
    --exclude '/home/*/.local/share/Trash' \
    "${BORG_REPO}::home-{now:%Y-%m-%d_%H:%M:%S}" \
    /home/

# Lista backup
borg list "${BORG_REPO}"
# home-2024-01-15_02:00:00  Mon, 2024-01-15 02:00:00
# home-2024-01-16_02:00:01  Tue, 2024-01-16 02:00:01

# Info backup specifico
borg info "${BORG_REPO}::home-2024-01-15_02:00:00"

# Estrai file (restore)
cd /tmp
borg extract "${BORG_REPO}::home-2024-01-15_02:00:00" home/mario/documento.pdf
# oppure tutto:
borg extract "${BORG_REPO}::home-2024-01-15_02:00:00"

# Monta backup come filesystem
borg mount "${BORG_REPO}::home-2024-01-15_02:00:00" /mnt/borg
ls /mnt/borg/home/mario/
borg umount /mnt/borg

# Prune — rimuovi backup vecchi
borg prune \
    --verbose \
    --stats \
    --keep-daily 7 \       # mantieni 7 backup giornalieri
    --keep-weekly 4 \      # mantieni 4 settimanali
    --keep-monthly 12 \    # mantieni 12 mensili
    "${BORG_REPO}"

# Compatta repository
borg compact "${BORG_REPO}"

# Verifica integrità
borg check --verbose "${BORG_REPO}"
```

---

## B2. Script borg completo

```bash
#!/usr/bin/env bash
# /opt/scripts/backup-borg.sh

set -euo pipefail

export BORG_PASSPHRASE="$(cat /etc/backup/borg-passphrase)"
export BORG_REPO="mario@backup.esempio.it:/backup/borg-repo"
SORGENTI=("/home" "/etc" "/var/www" "/opt")

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Crea backup
log "Avvio backup..."
borg create \
    --compression auto,lz4 \
    --exclude-caches \
    --exclude '/home/*/.cache' \
    --exclude '/home/*/.local/share/Trash' \
    "${BORG_REPO}::sistema-{now:%Y-%m-%d_%H:%M}" \
    "${SORGENTI[@]}"
log "Backup completato"

# Prune
log "Pulizia backup vecchi..."
borg prune \
    --keep-daily 7 \
    --keep-weekly 4 \
    --keep-monthly 12 \
    "${BORG_REPO}"

# Compatta
borg compact "${BORG_REPO}"
log "Fine."
```

---

# Parte C — restic

---

## C1. restic: backup cloud-native

```bash
# Installazione
apt install restic
# oppure:
curl -L https://github.com/restic/restic/releases/latest/download/restic_linux_amd64.bz2 | bzcat > /usr/local/bin/restic
chmod +x /usr/local/bin/restic

# Repository locale
restic init --repo /backup/restic-repo

# Repository S3 (AWS, MinIO, Backblaze B2)
export AWS_ACCESS_KEY_ID="chiave"
export AWS_SECRET_ACCESS_KEY="segreto"
export RESTIC_PASSWORD="passphrase"
restic init --repo s3:s3.amazonaws.com/mio-bucket/restic

# Backup
restic -r /backup/restic-repo backup /home /etc /var/www
restic -r /backup/restic-repo backup --tag server1 --tag daily /home

# Lista snapshot
restic -r /backup/restic-repo snapshots

# Restore
restic -r /backup/restic-repo restore latest --target /tmp/restore/
restic -r /backup/restic-repo restore abc12345 --target /tmp/restore/ --include /home/mario

# Monta come filesystem
restic -r /backup/restic-repo mount /mnt/restic

# Policy retention e pulizia
restic -r /backup/restic-repo forget \
    --keep-last 10 \
    --keep-daily 7 \
    --keep-weekly 4 \
    --keep-monthly 12 \
    --prune

# Verifica integrità
restic -r /backup/restic-repo check
restic -r /backup/restic-repo check --read-data   # legge tutti i dati
```

---

# Parte D — Test e validazione

---

## D1. Testare il restore

```bash
# Test mensile obbligatorio — backup che non si testano non esistono

# Strategia: restore su directory temporanea, verifica checksum
test_restore() {
    local REPO="$1"
    local TEST_DIR="/tmp/restore-test-$(date +%Y%m%d)"
    local SORGENTE="/etc/nginx"
    local CHECKSUM_ORIG="/tmp/checksums-originali.md5"
    local CHECKSUM_REST="/tmp/checksums-restaurati.md5"

    echo "=== Test restore del $(date) ==="

    # Calcola checksum originali
    find "$SORGENTE" -type f -exec md5sum {} \; | sort > "$CHECKSUM_ORIG"

    # Restore
    mkdir -p "$TEST_DIR"
    restic -r "$REPO" restore latest --target "$TEST_DIR" --include "$SORGENTE"

    # Verifica checksum
    find "$TEST_DIR$SORGENTE" -type f -exec md5sum {} \; | \
        sed "s|$TEST_DIR||" | sort > "$CHECKSUM_REST"

    if diff "$CHECKSUM_ORIG" "$CHECKSUM_REST" > /dev/null; then
        echo "✓ Test restore SUPERATO"
    else
        echo "✗ Test restore FALLITO!"
        diff "$CHECKSUM_ORIG" "$CHECKSUM_REST"
        exit 1
    fi

    rm -rf "$TEST_DIR"
}

test_restore "/backup/restic-repo"
```

---

# Parte E — Riepilogo

## Confronto strumenti

| Strumento | Dedup | Cifratura | Cloud | Complessità |
|---|---|---|---|---|
| rsync | No | No (via SSH) | Via SSH | Bassa |
| tar | No | Opzionale | Manuale | Bassa |
| borgbackup | Sì | Sì (AES-256) | Via SSH | Media |
| restic | Sì | Sì (AES-256) | S3, B2, Azure | Media |

## Regola 3-2-1

- **3** copie dei dati
- **2** media diversi (es. disco locale + NAS)
- **1** copia offsite (cloud o sede diversa)

## Prossimi passi

- `tutorial_linux_17_web_server.md` — nginx configurazione produzione
- `tutorial_linux_25_zfs.md` — ZFS per backup avanzati con snapshot
