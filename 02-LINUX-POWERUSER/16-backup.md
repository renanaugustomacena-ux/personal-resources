# Backup Linux — Guida Completa

> **Modulo 16** · **Aggiornamento:** 2026-05-24

## Idee guida
1. **Restic, BorgBackup: dedup + encryption client-side.**
2. **rsync per simple transfer, no dedup.**
3. **3-2-1-1-0 rule.**
4. **Restore drill mensile mandatory.**


## Indice

- [Panoramica](#panoramica)
- [Strategia di Backup](#strategia-di-backup)
- [rsync: Guida Completa](#rsync-guida-completa)
- [BorgBackup: Deduplicazione](#borgbackup-deduplicazione)
- [Restic: Backup Cloud](#restic-backup-cloud)
- [tar e Compressione](#tar-e-compressione)
- [Duplicity: Backup Cifrato Incrementale](#duplicity-backup-cifrato-incrementale)
- [Snapshot: LVM, ZFS, Btrfs](#snapshot-lvm-zfs-btrfs)
- [Backup di Database](#backup-di-database)
- [Backup a Livello di Filesystem](#backup-a-livello-di-filesystem)
- [Cloud Backup con rclone](#cloud-backup-con-rclone)
- [Proxmox Backup Server per Workload Misti](#proxmox-backup-server-per-workload-misti)
- [Automazione Backup](#automazione-backup)
- [Verifica dei Backup](#verifica-dei-backup)
- [Sicurezza dei Backup](#sicurezza-dei-backup)
- [Disaster Recovery Planning](#disaster-recovery-planning)
- [Bare Metal Recovery](#bare-metal-recovery)
- [Matrice Decisionale](#matrice-decisionale)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Panoramica

Il backup è l'ultima linea di difesa contro la perdita di dati: guasti hardware, errori umani, ransomware, disastri naturali. Una strategia di backup solida copre: cosa backuppare, dove conservare, con quale frequenza, per quanto tempo, e soprattutto: come verificare che il restore funzioni. Linux offre strumenti eccellenti: rsync per sincronizzazione, BorgBackup per deduplicazione locale, Restic per backup cloud-native, e snapshot LVM/ZFS/Btrfs per recovery point istantanei.

Un backup che non è stato testato con un restore è solo una speranza. Il costo di un sistema di backup va misurato non in gigabyte salvati, ma in ore di downtime evitate e in dati che si riescono effettivamente a recuperare.

### Cosa backuppare — Priorità

| Priorità | Dati | Motivazione |
|---|---|---|
| **Critica** | Database di produzione, configurazioni, certificati/chiavi | Irrecuperabili o costosi da ricreare |
| **Alta** | Home directory utenti, codice sorgente, documenti | Alto valore, difficili da ricostruire |
| **Media** | Log di sistema, metriche, immagini VM | Utili per troubleshooting e compliance |
| **Bassa** | Cache, file temporanei, build artifact | Rigenerabili facilmente |

### Cosa NON backuppare

```
/proc           # filesystem virtuale del kernel
/sys            # filesystem virtuale hardware
/dev            # device nodes (rigenerati dal kernel)
/run            # dati runtime volatili
/tmp            # file temporanei
/var/cache      # cache rigenerabile
/var/tmp        # temporanei persistenti
*.iso           # immagini scaricabili
node_modules/   # rigenerato da npm install
.cache/         # cache applicazioni
__pycache__/    # bytecode Python compilato
```

---

## Strategia di Backup

### Regola 3-2-1

```
3 copie dei dati (originale + 2 backup)
2 supporti diversi (disco locale + cloud/nastro/NAS)
1 copia offsite (in una posizione geografica diversa)
```

### Regola 3-2-1-1-0 (evoluzione)

La versione estesa aggiunge due requisiti fondamentali per ambienti di produzione:

```
3 copie dei dati
2 supporti diversi
1 copia offsite
1 copia air-gapped o immutabile (non raggiungibile da ransomware)
0 errori verificati (ogni backup testato con restore automatico)
```

La copia **air-gapped** è fisicamente scollegata dalla rete. Può essere un disco USB in cassaforte, un nastro LTO, o un bucket S3 con Object Lock abilitato (WORM — Write Once Read Many). È l'unico backup che resiste a un ransomware che compromette l'intera rete.

La condizione **0 errori** significa che ogni backup viene verificato automaticamente: `borg check`, `restic check --read-data`, o restore di prova su un ambiente di test. Un backup mai verificato ha un tasso di successo stimato intorno al 50%.

### Tipi di Backup

| Tipo | Descrizione | Pro | Contro |
|---|---|---|---|
| Full | Copia completa ogni volta | Restore semplice | Lento, molto spazio |
| Incremental | Solo dati cambiati dall'ultimo backup (qualsiasi tipo) | Veloce, poco spazio | Restore complesso (serve la catena) |
| Differential | Solo dati cambiati dall'ultimo full | Restore più semplice dell'incremental | Cresce nel tempo |
| Snapshot | Punto-nel-tempo del filesystem | Istantaneo | Non è un backup vero (stesso disco) |
| Synthetic Full | Full ricostruito da full precedente + incrementali | Full senza caricare la sorgente | Richiede logica lato repository |

#### Backup Sintetico (Synthetic Full)

Il backup sintetico crea un full backup combinando il full precedente con tutti gli incrementali successivi, senza accedere alla sorgente originale. Vantaggio: la sorgente non subisce carico I/O durante la creazione del full. BorgBackup e Restic implementano questo concetto intrinsecamente grazie alla deduplicazione a livello di chunk — ogni "backup" è effettivamente un synthetic full, poiché referenzia i blocchi già presenti nel repository.

```
Timeline backup tradizionale:
  Lun: Full (100GB)  →  Mar: Incr (2GB)  →  Mer: Incr (3GB)  →  Gio: Incr (1GB)
  Restore giovedì: Full + Incr_mar + Incr_mer + Incr_gio (4 operazioni)

Timeline con synthetic full:
  Lun: Full (100GB)  →  Mar: Incr (2GB)  →  Mer: Incr (3GB)  →  Gio: Synthetic Full (100GB, costruito lato repository)
  Restore giovedì: SyntheticFull_gio (1 operazione)
```

### RPO e RTO

- **RPO** (Recovery Point Objective): quanti dati posso permettermi di perdere? (es. 1 ora = backup ogni ora)
- **RTO** (Recovery Time Objective): quanto tempo per tornare operativi? (es. 4 ore)

#### Definire RPO e RTO per scenari reali

| Scenario | RPO tipico | RTO tipico | Strategia backup |
|---|---|---|---|
| Blog personale | 24 ore | 48 ore | Backup giornaliero, restore manuale |
| E-commerce | 1 ora | 4 ore | Replica DB + backup orario + failover |
| Trading finanziario | < 1 minuto | < 15 minuti | Replica sincrona + HA attivo/passivo |
| Archivio documenti | 24 ore | 8 ore | Backup giornaliero con dedup |
| CI/CD pipeline | 4 ore | 2 ore | Config as code + backup artifact store |
| Cartelle cliniche | 1 ora | 1 ora | Replica + backup crittografato + audit log |

#### Calcolo dei costi di downtime

```
Costo downtime = (Ricavo orario) × (Ore di RTO) + (Costo reputazionale)

Esempio: e-commerce con 10.000€/giorno di fatturato
  Ricavo orario = 10.000 / 24 ≈ 416€/ora
  RTO 4 ore = 416 × 4 = 1.664€ di perdita diretta
  + perdita clienti stimata: 5-15% del fatturato settimanale
```

### Retention Policy — Modello GFS (Grandfather-Father-Son)

```
Giornaliero (Son):       mantieni 7 giorni
Settimanale (Father):    mantieni 4 settimane
Mensile (Grandfather):   mantieni 12 mesi
Annuale:                 mantieni 2-7 anni (requisiti compliance)
```

---

## rsync: Guida Completa

rsync è lo strumento standard per sincronizzazione e backup incrementale su Linux. Usa un algoritmo delta-transfer che trasmette solo le differenze tra sorgente e destinazione.

### Funzionamento interno

rsync divide i file in blocchi (block size predefinito = dimensione del file / numero di blocchi), calcola checksum rolling (Adler-32) e hash forte (MD5 o xxHash) per ogni blocco, e trasmette solo i blocchi modificati. Questo lo rende estremamente efficiente per file grandi con piccole modifiche.

### Flag fondamentali

```bash
# SINCRONIZZAZIONE BASE
rsync -av source/ dest/              # Archive + verbose
rsync -avz source/ user@server:/dest/  # Via SSH con compressione

# OPZIONI FONDAMENTALI
# -a  archive (ricorsivo + permessi + date + link + proprietario + gruppo)
#     equivale a: -rlptgoD
# -v  verbose
# -z  compressione durante trasferimento
# -P  progress + partial (riprende trasferimenti interrotti)
# -n  dry run (simula)
# --delete  cancella file in dest che non esistono in source (mirror)

# OPZIONI AVANZATE — RIFERIMENTO COMPLETO
# -r  ricorsivo (incluso in -a)
# -l  preserva symlink (incluso in -a)
# -p  preserva permessi (incluso in -a)
# -t  preserva timestamp (incluso in -a)
# -g  preserva gruppo (incluso in -a)
# -o  preserva proprietario (incluso in -a, richiede root)
# -D  preserva device e special file (incluso in -a)
# -H  preserva hard link (NON incluso in -a)
# -A  preserva ACL (NON incluso in -a)
# -X  preserva extended attributes (NON incluso in -a)
# -S  gestione efficiente file sparsi
# -x  non attraversare filesystem boundary (mount point)
# --numeric-ids  non mappare UID/GID per nome (utile cross-system)
# --inplace  aggiorna file direttamente (no file temporaneo)
# --append  aggiungi dati a file più corti (utile per log)
# --append-verify  come --append ma verifica i dati esistenti con checksum
# -c  checksum (verifica con hash invece di timestamp/dimensione — lento)
# -u  update: salta file più recenti nella destinazione
# -W  whole file: disabilita delta-transfer (più veloce su rete veloce locale)
# --compress-level=N  livello compressione 0-9 (default 6)
# --info=progress2  mostra progresso globale (non per-file)
# --stats  statistiche alla fine del trasferimento
# --log-file=FILE  scrivi log su file
# --itemize-changes  mostra dettaglio di ogni modifica (>f+++++++++)
```

### Mirror completo

```bash
# MIRROR COMPLETO (source → dest identici)
rsync -avz --delete source/ dest/

# ATTENZIONE: la trailing slash su source/ è significativa
# rsync -av source/ dest/   → contenuto di source → dentro dest
# rsync -av source  dest/   → directory source → dentro dest (crea dest/source/)

# Mirror con cancellazione sicura: prima cancella, poi trasferisci
rsync -avz --delete-before source/ dest/

# Mirror con cancellazione ritardata: trasferisci prima, cancella dopo
rsync -avz --delete-after source/ dest/

# Mirror con cancellazione in un file separato (non cancella nulla)
rsync -avz --delete --backup --backup-dir=/backup/deleted source/ dest/
```

### Pattern di esclusione

```bash
# BACKUP CON ESCLUSIONI
rsync -avz \
  --exclude='*.log' \
  --exclude='.cache' \
  --exclude='node_modules' \
  --exclude-from='/etc/rsync-exclude.txt' \
  source/ dest/

# PATTERN DI ESCLUSIONE AVANZATI
# *     → qualsiasi stringa (non attraversa /)
# **    → qualsiasi stringa (attraversa /)
# ?     → singolo carattere
# [abc] → classe di caratteri

# Esempio file di esclusione: /etc/rsync-exclude.txt
# *.log
# *.tmp
# *.swp
# .git/
# .cache/
# __pycache__/
# node_modules/
# .env
# *.pyc
# .DS_Store
# Thumbs.db
# /var/cache/**
# /var/tmp/**

# INCLUDE + EXCLUDE combinati (include solo certi tipi)
rsync -avz \
  --include='*/' \
  --include='*.conf' \
  --include='*.yaml' \
  --exclude='*' \
  /etc/ /backup/configs/
# Risultato: copia solo file .conf e .yaml preservando la struttura directory

# FILTRI (sintassi unificata)
rsync -avz \
  --filter='- *.log' \
  --filter='- .cache/' \
  --filter='+ *.conf' \
  source/ dest/
```

### Backup incrementale con --link-dest

```bash
# BACKUP CON HARD LINK (backup incrementale efficiente)
rsync -avz --link-dest=/backup/latest source/ /backup/$(date +%Y%m%d)/
ln -sfn /backup/$(date +%Y%m%d) /backup/latest
# --link-dest: i file invariati sono hard link alla copia precedente → spazio risparmiato

# Meccanismo: rsync confronta source con la directory indicata da --link-dest.
# Se un file è identico (stesso contenuto, permessi, timestamp), crea un hard link
# invece di copiare. L'hard link non occupa spazio aggiuntivo su disco.
#
# Dopo 30 giorni di backup giornalieri con 5% di file modificati/giorno:
#   Spazio senza --link-dest: 30 × 100GB = 3TB
#   Spazio con --link-dest:   100GB + 29 × 5GB = 245GB (risparmio ~92%)
```

### Trasferimento via SSH

```bash
# VIA SSH CON PORTA SPECIFICA
rsync -avz -e "ssh -p 2222" source/ user@server:/dest/

# SSH con chiave specifica
rsync -avz -e "ssh -i ~/.ssh/backup_key -o StrictHostKeyChecking=yes" \
  source/ user@server:/dest/

# SSH con cifratura veloce (AES hardware-accelerato)
rsync -avz -e "ssh -c aes128-gcm@openssh.com" source/ user@server:/dest/

# SSH con compressione disabilitata (se la rete è veloce)
rsync -av -e "ssh -o Compression=no" source/ user@server:/dest/

# Tunnel tramite jump host / bastion
rsync -avz -e "ssh -J jumpuser@bastion" source/ user@target:/dest/
```

### Controllo bandwidth e trasferimenti parziali

```bash
# LIMITARE BANDWIDTH
rsync -avz --bwlimit=5000 source/ dest/   # 5MB/s

# BACKUP FILE GRANDI (parziale + progress)
rsync -avzP bigfile.iso user@server:/backup/
# -P equivale a --partial --progress
# --partial: mantieni file parziale se il trasferimento si interrompe
# Al prossimo avvio, rsync riprende da dove si era fermato

# PRESERVARE ACL E XATTR
rsync -avzAX source/ dest/

# TIMEOUT per connessioni instabili
rsync -avz --timeout=300 --contimeout=60 source/ user@server:/dest/
# --timeout=300     → timeout I/O (5 minuti senza dati → abort)
# --contimeout=60   → timeout connessione iniziale
```

### Script rsync per Backup Giornaliero

```bash
#!/bin/bash
# /usr/local/bin/daily-backup.sh
set -euo pipefail

SRC="/srv/data/"
DEST="/backup/data"
DATE=$(date +%Y%m%d-%H%M)
LATEST="$DEST/latest"
CURRENT="$DEST/$DATE"
LOG="/var/log/backup/rsync-$DATE.log"

mkdir -p "$CURRENT" "$(dirname "$LOG")"

rsync -avz --delete \
  --link-dest="$LATEST" \
  --exclude-from=/etc/backup-exclude.txt \
  "$SRC" "$CURRENT" \
  2>&1 | tee "$LOG"

# Aggiorna il link "latest"
ln -sfn "$CURRENT" "$LATEST"

# Pulizia backup vecchi (>30 giorni)
find "$DEST" -maxdepth 1 -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completato: $CURRENT"
```

### Script rsync avanzato con notifica e verifica

```bash
#!/bin/bash
# /usr/local/bin/rsync-backup-advanced.sh
set -euo pipefail

# --- Configurazione ---
SRC="/srv/data/"
DEST="/backup/data"
REMOTE="user@backup-server:/mnt/backup/data"
DATE=$(date +%Y%m%d-%H%M%S)
LATEST="$DEST/latest"
CURRENT="$DEST/$DATE"
LOG="/var/log/backup/rsync-$DATE.log"
LOCK="/var/run/rsync-backup.lock"
MAILTO="admin@example.com"

# --- Funzioni ---
cleanup() {
    rm -f "$LOCK"
}
trap cleanup EXIT

send_alert() {
    local subject="$1"
    local body="$2"
    echo "$body" | mail -s "[BACKUP] $subject" "$MAILTO" 2>/dev/null || true
}

# --- Lock per evitare esecuzioni parallele ---
if [ -f "$LOCK" ]; then
    PID=$(cat "$LOCK")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Backup già in esecuzione (PID $PID)" >&2
        exit 1
    fi
    rm -f "$LOCK"
fi
echo $$ > "$LOCK"

mkdir -p "$CURRENT" "$(dirname "$LOG")"

echo "=== Backup locale iniziato: $(date --iso-8601=seconds) ===" | tee "$LOG"

# --- Backup locale con --link-dest ---
if rsync -avz --delete \
    --link-dest="$LATEST" \
    --exclude-from=/etc/backup-exclude.txt \
    --stats \
    --log-file="$LOG" \
    "$SRC" "$CURRENT"; then

    ln -sfn "$CURRENT" "$LATEST"
    echo "=== Backup locale completato: $(date --iso-8601=seconds) ===" | tee -a "$LOG"
else
    send_alert "ERRORE backup locale" "rsync locale fallito. Vedi $LOG"
    exit 1
fi

# --- Copia offsite ---
echo "=== Copia offsite iniziata ===" | tee -a "$LOG"
if rsync -avz --delete \
    --bwlimit=10000 \
    -e "ssh -i /root/.ssh/backup_key -o StrictHostKeyChecking=yes" \
    "$CURRENT/" "$REMOTE/$DATE/"; then
    echo "=== Copia offsite completata ===" | tee -a "$LOG"
else
    send_alert "ERRORE copia offsite" "rsync offsite fallito. Vedi $LOG"
fi

# --- Pulizia vecchi backup (>30 giorni locale, >90 giorni remoto) ---
find "$DEST" -maxdepth 1 -type d -mtime +30 ! -name "latest" -exec rm -rf {} \;

# --- Report ---
BACKUP_SIZE=$(du -sh "$CURRENT" | cut -f1)
send_alert "OK — $DATE" "Backup completato. Dimensione: $BACKUP_SIZE"
```

---

## BorgBackup: Deduplicazione

BorgBackup è uno strumento di backup con deduplicazione, compressione e crittografia. Ideale per backup locali e su rete.

### Architettura

```
Repository (directory su disco/NAS/SSH)
  └── Archives (singoli backup, immutabili una volta creati)
       └── Chunks (blocchi di dati deduplicati, compressi, cifrati)
            └── Index (mappatura chunk → posizione nel repository)
```

**Deduplicazione**: Borg spezza i file in chunk di dimensione variabile (content-defined chunking, CDC). Ogni chunk viene hashato (HMAC-SHA256). Se il chunk esiste già nel repository, viene referenziato senza duplicazione. Questo funziona a livello di blocco, non di file — se due file condividono sezioni identiche, anche quelle sezioni vengono deduplicate.

**Rapporto di deduplicazione tipico**: repository con backup giornalieri di un server → rapporto 10:1 — 20:1 (10-20x meno spazio rispetto a backup full individuali).

### Installazione e setup

```bash
# Installazione
sudo apt install borgbackup          # Debian/Ubuntu
sudo dnf install borgbackup          # Fedora/RHEL
pip install borgbackup               # PyPI (ultima versione)

# INIZIALIZZARE REPOSITORY
borg init --encryption=repokey /backup/borg-repo
# repokey: password + chiave nel repo (la chiave è cifrata con la password)
# keyfile: password + chiave locale (~/.config/borg/keys/) — più sicuro
# none: senza crittografia
# repokey-blake2: usa BLAKE2b (più veloce di SHA256)
# authenticated: no crittografia, ma integrità verificata (HMAC)
# authenticated-blake2: come sopra con BLAKE2b

# Repository remoto (via SSH)
borg init --encryption=repokey user@server:/backup/borg-repo

# ESPORTARE LA CHIAVE (CRITICO per repokey — senza chiave, niente restore)
borg key export /backup/borg-repo /root/borg-key-export.txt
# Conservare questa chiave IN UN LUOGO SICURO SEPARATO dal repository
```

### Creare backup

```bash
# CREARE BACKUP
borg create \
  /backup/borg-repo::$(hostname)-$(date +%Y%m%d-%H%M) \
  /etc /home /srv /var/lib \
  --exclude '/home/*/.cache' \
  --exclude '*.tmp' \
  --compression zstd,3 \
  --stats

# LIVELLI DI COMPRESSIONE
# --compression none          → nessuna compressione
# --compression lz4           → velocissima, rapporto basso
# --compression zstd,1-22     → buon bilanciamento (3 = default consigliato)
# --compression zlib,1-9      → classica, bilanciata
# --compression lzma,0-9      → massima compressione, lentissima

# BACKUP CON ESCLUSIONE AVANZATA
borg create \
  /backup/borg-repo::server-$(date +%Y%m%d) \
  /etc /home /srv /var/lib /var/log \
  --exclude-caches \
  --exclude '/home/*/.cache' \
  --exclude '/home/*/Downloads' \
  --exclude '*.pyc' \
  --exclude '*/__pycache__' \
  --exclude '*/node_modules' \
  --exclude '*/vendor' \
  --exclude '*.log' \
  --exclude-if-present .nobackup \
  --compression zstd,6 \
  --stats --progress \
  --checkpoint-interval 600

# --exclude-caches      → salta directory con CACHEDIR.TAG
# --exclude-if-present  → salta directory che contengono il file indicato
# --checkpoint-interval → checkpoint ogni N secondi (resume dopo interruzione)
```

### Operazioni su archivi

```bash
# LISTA BACKUP
borg list /backup/borg-repo

# INFORMAZIONI DETTAGLIATE
borg info /backup/borg-repo
borg info /backup/borg-repo::backup-name

# STATISTICHE DEL REPOSITORY
borg info /backup/borg-repo
# Mostra: Original size, Deduplicated size, Unique chunks, Total chunks

# DIFFERENZE TRA DUE ARCHIVI
borg diff /backup/borg-repo::backup-20260520 backup-20260521
# Mostra file aggiunti, modificati, rimossi tra due backup

# RINOMINARE ARCHIVIO
borg rename /backup/borg-repo::vecchio-nome nuovo-nome
```

### Restore

```bash
# RESTORE
# Restore completo
borg extract /backup/borg-repo::backup-name

# Restore directory specifica
borg extract /backup/borg-repo::backup-name home/user/documents

# Restore file specifico
borg extract /backup/borg-repo::backup-name etc/nginx/nginx.conf

# Restore con esclusione (restore tutto TRANNE)
borg extract /backup/borg-repo::backup-name --exclude '*.log'

# Restore in posizione diversa
cd /tmp/restore && borg extract /backup/borg-repo::backup-name

# STDOUT (pipe verso altro comando)
borg extract --stdout /backup/borg-repo::backup-name etc/passwd | less

# Montare backup come filesystem (esplorazione)
mkdir /mnt/borg
borg mount /backup/borg-repo::backup-name /mnt/borg
ls /mnt/borg/
# Navigare, copiare singoli file, esplorare
cp /mnt/borg/home/user/important.doc /tmp/
borg umount /mnt/borg

# Montare TUTTI gli archivi (navigabili per nome)
borg mount /backup/borg-repo /mnt/borg
ls /mnt/borg/
# backup-20260520/  backup-20260521/  backup-20260522/
```

### Pruning e manutenzione

```bash
# PULIZIA (retention policy)
borg prune \
  /backup/borg-repo \
  --keep-daily=7 \
  --keep-weekly=4 \
  --keep-monthly=6 \
  --keep-yearly=2 \
  --stats

# Opzioni di retention
# --keep-within=30d    → mantieni tutto degli ultimi 30 giorni
# --keep-last=N        → mantieni gli ultimi N archivi
# --keep-daily=N       → N archivi giornalieri
# --keep-weekly=N      → N archivi settimanali
# --keep-monthly=N     → N archivi mensili
# --keep-yearly=N      → N archivi annuali

# Dry run (simula senza cancellare)
borg prune --dry-run --list --stats /backup/borg-repo \
  --keep-daily=7 --keep-weekly=4

# Compattare (liberare spazio dopo prune)
borg compact /backup/borg-repo
# IMPORTANTE: prune marca gli archivi per la cancellazione,
# compact libera effettivamente lo spazio su disco

# VERIFICA INTEGRITÀ
borg check /backup/borg-repo                # Verifica metadati + struttura
borg check --verify-data /backup/borg-repo  # Verifica anche i dati (lento)
borg check --repair /backup/borg-repo       # Tenta riparazione (ULTIMO RESORT)
```

### Monitoring BorgBackup

```bash
# Monitoring con script wrapper
#!/bin/bash
# /usr/local/bin/borg-monitor.sh

REPO="/backup/borg-repo"
ALERT_HOURS=26  # Alert se ultimo backup > 26 ore fa

# Ultimo backup timestamp
LAST_BACKUP=$(borg list "$REPO" --last 1 --format '{time}' 2>/dev/null)
if [ -z "$LAST_BACKUP" ]; then
    echo "CRITICAL: Nessun backup trovato nel repository"
    exit 2
fi

LAST_EPOCH=$(date -d "$LAST_BACKUP" +%s)
NOW_EPOCH=$(date +%s)
HOURS_AGO=$(( (NOW_EPOCH - LAST_EPOCH) / 3600 ))

if [ "$HOURS_AGO" -gt "$ALERT_HOURS" ]; then
    echo "WARNING: Ultimo backup $HOURS_AGO ore fa ($LAST_BACKUP)"
    exit 1
fi

# Dimensione repository
REPO_SIZE=$(borg info "$REPO" --json 2>/dev/null | \
  python3 -c "import sys,json; d=json.load(sys.stdin); \
  print(d['cache']['stats']['unique_csize'])" 2>/dev/null)

echo "OK: Ultimo backup $HOURS_AGO ore fa. Repo size: $REPO_SIZE bytes"
exit 0
```

```ini
# Integrazione con Prometheus (textfile collector)
# /etc/cron.d/borg-metrics
*/15 * * * * root /usr/local/bin/borg-metrics.sh > \
  /var/lib/prometheus/node-exporter/borg.prom
```

### BorgBackup 2.0 — Architettura e Migrazione

BorgBackup 2.0 (detto "Borg2") è una riscrittura architetturale significativa. A maggio 2026 è ancora in fase beta (2.0.0b20, rilasciata il 15 marzo 2026), ma i cambiamenti sono sostanziali e vanno compresi per pianificare la migrazione futura.

#### Cambiamenti architetturali

```
Borg 1.x → Borg 2.0 — Differenze chiave

┌─────────────────────┬──────────────────────┬──────────────────────────┐
│ Aspetto              │ Borg 1.x             │ Borg 2.0                 │
├─────────────────────┼──────────────────────┼──────────────────────────┤
│ Formato repository   │ v1                   │ v2 (default, incompatibile)│
│ Struttura chiavi     │ enc_key + enc_hmac_key│ crypt_key (unificata)    │
│ Nomi archivi         │ Devono essere unici  │ Possono essere identici  │
│ CLI syntax           │ borg create REPO::   │ borg -r REPO create      │
│ Chunker              │ buzhash (32-bit)     │ buzhash64 (64-bit, opz.) │
│ Compressione default │ lz4                  │ zstd,3                   │
│ Repo v1 supporto     │ Lettura/scrittura    │ Solo lettura (transfer)  │
└─────────────────────┴──────────────────────┴──────────────────────────┘
```

**Formato repository v2**: il nuovo formato non è retrocompatibile. I repository creati con Borg 2.0 non possono essere letti da Borg 1.x. I repository v1 possono essere aperti in sola lettura da Borg 2.0, esclusivamente per operazioni di trasferimento.

**Crittografia semplificata**: la struttura a doppia chiave (`enc_key` + `enc_hmac_key`) è stata unificata in un singolo `crypt_key`. Questo semplifica l'implementazione interna e riduce la superficie di attacco crittografica.

**Nomi archivi non univoci**: in Borg 2.0, gli archivi non devono più avere nomi unici. È anzi **raccomandato** usare lo stesso nome per tutti i backup della stessa serie (ad esempio `daily`) — Borg internamente li distingue tramite timestamp e ID. Questo rende i pattern di naming molto più semplici e il pruning più efficiente.

**Chunker buzhash64**: il nuovo chunker sperimentale usa hash a 64 bit invece di 32 bit per la decisione di chunking. Le performance sono comparabili al buzhash classico, ma il rischio di collisioni è drasticamente inferiore su repository molto grandi.

#### Migrazione da Borg 1.x a Borg 2.0

```bash
# MIGRAZIONE — Processo in 4 fasi

# 1. Aggiornare Borg 1.x all'ultima versione 1.4.x
# Assicurarsi che il repository v1 sia in buono stato
borg check /backup/borg-v1-repo

# 2. Installare Borg 2.0 (beta — solo ambienti di test a maggio 2026)
pip install borgbackup==2.0.0b20

# 3. Creare il nuovo repository v2
borg -r /backup/borg-v2-repo rcreate --encryption=repokey-aes-ocb
# Nota: la sintassi CLI è cambiata — borg -r <REPO> <COMANDO>
# rcreate sostituisce init in Borg 2.0

# 4. Trasferire gli archivi dal repository v1 al v2
borg -r /backup/borg-v2-repo transfer \
  --other-repo=/backup/borg-v1-repo \
  --upgrader=From12To20
# --upgrader=From12To20 converte il formato degli archivi durante il trasferimento
# Il processo rilegge e riscrive tutti i chunk — può richiedere molto tempo

# VERIFICARE il nuovo repository dopo il trasferimento
borg -r /backup/borg-v2-repo rlist        # Lista archivi
borg -r /backup/borg-v2-repo check        # Verifica integrità

# ATTENZIONE: mantenere il repository v1 come fallback
# fino alla verifica completa del v2
```

#### Nuova sintassi CLI

```bash
# Borg 1.x (vecchia sintassi — ANCORA SUPPORTATA in 1.4.x)
borg create /backup/repo::archive-name /etc /home
borg list /backup/repo
borg info /backup/repo::archive-name
borg check /backup/repo

# Borg 2.0 (nuova sintassi — OBBLIGATORIA)
borg -r /backup/repo create --stats /etc /home
borg -r /backup/repo rlist              # list → rlist per repository
borg -r /backup/repo rinfo              # info → rinfo per repository
borg -r /backup/repo check

# Il repository si specifica con -r (o --repo) PRIMA del comando.
# Nomi archivi non più nella sintassi REPO::NOME,
# vengono generati automaticamente o specificati con --name.

# Creare backup con nome esplicito
borg -r /backup/repo create --name daily /etc /home /srv

# Compressione con il nuovo default zstd
borg -r /backup/repo create --compression zstd,6 /etc /home
```

> **Stato attuale (maggio 2026)**: Borg 2.0 è in beta. Per ambienti di produzione, continuare a usare Borg 1.4.x. Pianificare la migrazione per quando Borg 2.0 raggiungerà lo stato stabile. Non ci sarà un percorso di aggiornamento in-place — la migrazione richiede `borg transfer`.

---

## Restic: Backup Cloud

Restic è ottimizzato per backup verso storage cloud (S3, B2, Azure Blob, GCS) con deduplicazione e crittografia.

### Architettura e backend

Restic supporta numerosi backend di storage, tutti con la stessa interfaccia:

| Backend | Sintassi | Uso tipico |
|---|---|---|
| Locale | `-r /path/to/repo` | Disco locale, NAS montato |
| SFTP | `-r sftp:user@host:/path` | Server SSH remoto |
| Amazon S3 | `-r s3:s3.amazonaws.com/bucket` | AWS cloud |
| S3 compatibile | `-r s3:https://minio.local/bucket` | MinIO, Wasabi |
| Backblaze B2 | `-r b2:bucket-name:/path` | Economico, cold storage |
| Azure Blob | `-r azure:container:/path` | Microsoft cloud |
| Google Cloud | `-r gs:bucket:/path` | Google cloud |
| Rest Server | `-r rest:https://host:8000/` | Server dedicato restic |

### Inizializzazione

```bash
# Installazione
sudo apt install restic          # Debian/Ubuntu — spesso non ultima versione
restic self-update               # Auto-aggiornamento (se installato da binary)

# INIZIALIZZARE REPOSITORY
# Locale
restic -r /backup/restic-repo init

# Amazon S3
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
restic -r s3:s3.amazonaws.com/bucket-name init

# S3 compatibile (MinIO, Wasabi)
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
restic -r s3:https://minio.internal:9000/backup-bucket init

# Backblaze B2
export B2_ACCOUNT_ID=xxx
export B2_ACCOUNT_KEY=xxx
restic -r b2:bucket-name:/path init

# SFTP
restic -r sftp:user@server:/backup/restic-repo init

# Rest Server (server dedicato per restic)
restic -r rest:https://backup.example.com:8000/repo1 init

# Google Cloud Storage
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
restic -r gs:bucket-name:/path init

# Azure Blob Storage
export AZURE_ACCOUNT_NAME=xxx
export AZURE_ACCOUNT_KEY=xxx
restic -r azure:container-name:/path init
```

### Rest Server

```bash
# rest-server: backend HTTP dedicato per restic, ottimizzato per performance

# Installazione
go install github.com/restic/rest-server/cmd/rest-server@latest

# Avvio base
rest-server --path /srv/restic-repos --listen :8000

# Avvio con TLS e autenticazione
rest-server \
  --path /srv/restic-repos \
  --listen :8000 \
  --tls \
  --tls-cert /etc/ssl/certs/backup.pem \
  --tls-key /etc/ssl/private/backup.key \
  --htpasswd-file /etc/restic/htpasswd

# Creare utente per htpasswd
htpasswd -B -c /etc/restic/htpasswd backup-user

# Modalità append-only (protezione anti-ransomware)
rest-server --path /srv/restic-repos --append-only
# In questa modalità, i client possono creare backup ma NON cancellare.
# Il prune deve essere eseguito sul server stesso.
```

### Creare backup e snapshot

```bash
# CREARE BACKUP
export RESTIC_PASSWORD="password-sicura"
export RESTIC_REPOSITORY="/backup/restic-repo"
# Meglio: usare RESTIC_PASSWORD_FILE o RESTIC_PASSWORD_COMMAND
export RESTIC_PASSWORD_FILE="/etc/restic/password"
export RESTIC_PASSWORD_COMMAND="gpg --quiet --decrypt /etc/restic/password.gpg"

restic backup /etc /home /srv \
  --exclude-file=/etc/restic-exclude.txt \
  --tag server1

# BACKUP CON TAG MULTIPLI
restic backup /var/lib/postgresql \
  --tag database --tag postgresql --tag production

# BACKUP DA STDIN (pipe)
pg_dumpall | restic backup --stdin --stdin-filename postgresql-all.sql

# BACKUP CON ESCLUSIONE PATTERN
restic backup /home \
  --exclude='*.log' \
  --exclude='.cache' \
  --exclude='node_modules' \
  --exclude-caches \
  --exclude-if-present .nobackup

# LISTA SNAPSHOT
restic snapshots
restic snapshots --tag server1
restic snapshots --latest 5
restic snapshots --host webserver
restic snapshots --json   # Output JSON per scripting

# DETTAGLIO SNAPSHOT
restic stats                          # Statistiche globali
restic stats latest                   # Statistiche ultimo snapshot
restic cat snapshot <snapshot-id>     # Metadati JSON dello snapshot

# DIFFERENZE TRA SNAPSHOT
restic diff abc123 def456
```

### Restore

```bash
# RESTORE
restic restore latest --target /tmp/restore
restic restore abc123 --target /tmp/restore --include /etc/nginx

# Restore con esclusione
restic restore latest --target /tmp/restore --exclude '*.log'

# Restore singolo file
restic dump latest /etc/nginx/nginx.conf > /tmp/nginx.conf

# MOUNT (FUSE)
mkdir /mnt/restic
restic mount /mnt/restic
# Navigare tra snapshot come directory:
# /mnt/restic/snapshots/latest/
# /mnt/restic/snapshots/2026-05-20T02:00:00/
# /mnt/restic/hosts/webserver/
# /mnt/restic/tags/production/
```

### Forget, prune e manutenzione

```bash
# PULIZIA — due fasi: forget (marca) + prune (cancella)
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune

# Solo forget (marca snapshot per cancellazione, non libera spazio)
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6

# Solo prune (libera spazio dei dati non più referenziati)
restic prune

# Prune con limite di spazio recuperato (per evitare I/O eccessivo)
restic prune --max-repack-size 5G

# VERIFICA
restic check                 # Verifica struttura e metadati
restic check --read-data     # Verifica anche i dati (lento, legge tutto)
restic check --read-data-subset=5%  # Verifica 5% dei dati (compromesso)

# RIPARARE INDICE (se check segnala problemi)
restic repair index
restic repair snapshots

# UNLOCK (se un backup è stato interrotto e il lock rimane)
restic unlock
restic unlock --remove-all   # Rimuovi TUTTI i lock (attenzione!)

# CACHE
restic cache --cleanup       # Pulisci cache locale
```

### Scripting Restic

```bash
#!/bin/bash
# /usr/local/bin/restic-backup.sh
set -euo pipefail

export RESTIC_REPOSITORY="s3:s3.amazonaws.com/company-backup"
export RESTIC_PASSWORD_FILE="/etc/restic/password"
export AWS_ACCESS_KEY_ID="$(cat /etc/restic/aws-key-id)"
export AWS_SECRET_ACCESS_KEY="$(cat /etc/restic/aws-secret-key)"

HOSTNAME=$(hostname)
LOG="/var/log/backup/restic-$(date +%Y%m%d).log"
LOCK="/var/run/restic-backup.lock"

exec > >(tee -a "$LOG") 2>&1

# Lock
exec 200>"$LOCK"
flock -n 200 || { echo "Backup già in esecuzione"; exit 1; }

echo "=== Restic backup: $(date --iso-8601=seconds) ==="

# Backup
restic backup \
  /etc /home /srv /var/lib \
  --tag "$HOSTNAME" \
  --tag production \
  --exclude-file=/etc/restic/exclude.txt \
  --verbose

# Retention
restic forget \
  --tag "$HOSTNAME" \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 12 \
  --keep-yearly 2 \
  --prune

# Verifica (un check completo alla settimana, subset gli altri giorni)
DAY_OF_WEEK=$(date +%u)
if [ "$DAY_OF_WEEK" -eq 7 ]; then
    restic check --read-data
else
    restic check --read-data-subset=2%
fi

echo "=== Backup completato: $(date --iso-8601=seconds) ==="
```

### Restic 0.17 e 0.18 — Novità

Restic 0.17 (luglio 2024) e 0.18 (marzo 2025) hanno introdotto miglioramenti significativi in compressione, verifica, e gestione degli snapshot.

#### Compressione e Repository Version 2

```bash
# REPOSITORY FORMAT VERSION 2
# La compressione è disponibile SOLO con repository format version 2.
# Nuovi repository sono creati in v2 per default da restic 0.14+.

# Modalità di compressione disponibili:
#   auto     → comprime con zstd (default per repo v2)
#   off      → nessuna compressione
#   max      → compressione massima (zstd livello più alto, più lento)

# Inizializzare repo con compressione esplicita
restic -r /backup/repo init --repository-version 2

# Backup con compressione massima (archivi a lungo termine)
restic -r /backup/repo backup /srv/data --compression max

# Backup senza compressione (dati già compressi: video, immagini)
restic -r /backup/repo backup /srv/media --compression off

# Backup con compressione automatica (default — raccomandato)
restic -r /backup/repo backup /etc /home --compression auto

# Migrare un repository da v1 a v2 (abilita compressione)
restic -r /backup/repo migrate upgrade_repo_v2
# Dopo la migrazione, i NUOVI dati saranno compressi.
# I dati esistenti rimangono non compressi fino al prossimo prune/repack.

# Ricomprimere dati esistenti dopo la migrazione
restic -r /backup/repo prune --repack-uncompressed
# ATTENZIONE: questa operazione riscrive tutti i pack non compressi.
# Può richiedere molto tempo e I/O intenso su repository grandi.
```

#### Snapshot Rewriting e Repair

```bash
# REWRITE — Modificare snapshot esistenti (restic 0.17+)

# Riscrivere snapshot cambiando hostname
restic -r /backup/repo rewrite --new-host nuovo-hostname latest

# Riscrivere snapshot cambiando il timestamp
restic -r /backup/repo rewrite --new-time "2026-05-20T02:00:00" abc123

# Riscrivere snapshot escludendo file (es. rimuovere dati sensibili)
restic -r /backup/repo rewrite --exclude '*.secret' --exclude '/tmp/**' latest
# Le statistiche dello snapshot vengono aggiornate di conseguenza.

# REPAIR PACKS — Riparazione file di pack danneggiati (restic 0.17+)
# Gestisce file di pack troncati o corrotti
restic -r /backup/repo repair packs
# Identifica pack danneggiati e li ricostruisce dove possibile.
# I dati irrecuperabili vengono rimossi dall'indice.

# REPAIR INDEX — Ricostruisce l'indice con split corretto
restic -r /backup/repo repair index
# Da restic 0.17.1+: l'indice viene correttamente suddiviso
# in file più piccoli (fix del bug che creava un singolo indice enorme)

# repair index con lettura completa di tutti i pack
restic -r /backup/repo repair index --read-all-packs
```

#### Novità restic 0.18

```bash
# DUMP con compressione ZIP DEFLATE (restic 0.18+)
# Il comando dump ora comprime gli archivi ZIP, riducendo la dimensione
restic -r /backup/repo dump latest /etc/nginx/ --archive zip > nginx-config.zip

# Feature flag per repository
# restic 0.18 introduce feature flag che permettono
# di abilitare nuove funzionalità in modo granulare
restic -r /backup/repo cat config    # Visualizza feature flag attivi

# CHECK con subset rotativo — strategia raccomandata
# Lunedì-Sabato: verifica un subset diverso ogni giorno
restic -r /backup/repo check --read-data-subset=1/6   # Lunedì
restic -r /backup/repo check --read-data-subset=2/6   # Martedì
# ... fino a 6/6 — ogni settimana l'intero repository viene verificato

# Domenica: check strutturale completo
restic -r /backup/repo check

# EXIT CODE addizionali (restic 0.17+)
# Exit code 0 = successo
# Exit code 1 = errore generico
# Exit code 3 = repository ha problemi (check)
# Exit code 10 = repository bloccato
# Exit code 11 = nessuno snapshot trovato (forget/snapshots)
# Utile per scripting: distinguere tra errori e condizioni specifiche
```

---

## tar e Compressione

### Operazioni base

```bash
# CREARE ARCHIVIO
tar czf backup.tar.gz /etc /home     # gzip
tar cjf backup.tar.bz2 /etc /home    # bzip2 (più compresso, più lento)
tar cJf backup.tar.xz /etc /home     # xz (massima compressione)
tar c --zstd -f backup.tar.zst /etc  # zstd (veloce + buona compressione)

# ESTRARRE
tar xzf backup.tar.gz -C /tmp/restore
tar xjf backup.tar.bz2 -C /tmp/restore

# LISTA CONTENUTO
tar tzf backup.tar.gz
tar tzf backup.tar.gz | grep nginx   # Cercare file specifico

# ESTRARRE FILE SPECIFICO
tar xzf backup.tar.gz etc/nginx/nginx.conf -C /tmp/restore

# PRESERVARE TUTTO (permessi, ACL, xattr, SELinux context)
tar --acls --xattrs --selinux -czf backup.tar.gz /srv/data
```

### Confronto algoritmi di compressione

| Algoritmo | Flag tar | Rapporto | Velocità compr. | Velocità decompr. | RAM | Uso tipico |
|---|---|---|---|---|---|---|
| gzip | `-z` | Medio | Media | Veloce | Bassa | Default, compatibilità universale |
| bzip2 | `-j` | Buono | Lenta | Lenta | Media | Archivi dove serve compressione migliore |
| xz | `-J` | Ottimo | Molto lenta | Media | Alta | Distribuzione software, archivi a lungo termine |
| zstd | `--zstd` | Buono-Ottimo | Molto veloce | Molto veloce | Media | Backup quotidiani, bilanciamento ideale |
| lz4 | `--use-compress-program=lz4` | Basso | Velocissima | Velocissima | Bassa | Dove la velocità è prioritaria |

```bash
# Benchmark reale su dataset tipico (10GB dati misti):
# gzip:   compressione 2.5GB, tempo 2m30s, decompr. 45s
# bzip2:  compressione 2.1GB, tempo 8m, decompr. 3m
# xz:     compressione 1.8GB, tempo 15m, decompr. 1m30s
# zstd:   compressione 2.2GB, tempo 30s, decompr. 10s    ← raccomandato
# zstd -19: compressione 1.9GB, tempo 12m, decompr. 10s  ← massima compressione zstd

# ZSTD CON LIVELLO PERSONALIZZATO
tar -c --zstd -f backup.tar.zst /srv/data                    # livello 3 (default)
tar -c --use-compress-program='zstd -T0 -6' -f backup.tar.zst /srv/data
# -T0 = usa tutti i core disponibili
# -6  = livello compressione (1=veloce, 19=max, 22=ultra)
```

### Backup incrementale con tar

```bash
# BACKUP INCREMENTALE CON tar
# Full (crea lo snapshot file per tracciare lo stato del filesystem)
tar czf /backup/full-$(date +%Y%m%d).tar.gz \
  -g /backup/snapshot.snar /srv/data

# Incrementale (usa lo snapshot file per tracciare i cambiamenti)
tar czf /backup/incr-$(date +%Y%m%d).tar.gz \
  -g /backup/snapshot.snar /srv/data

# RESTORE incrementale (applicare in ordine cronologico)
cd /tmp/restore
tar xzf /backup/full-20260501.tar.gz -g /dev/null
tar xzf /backup/incr-20260502.tar.gz -g /dev/null
tar xzf /backup/incr-20260503.tar.gz -g /dev/null
# -g /dev/null durante il restore: applica i dati senza aggiornare lo snapshot

# ATTENZIONE: il file .snar tiene traccia dello stato.
# Non perdere il file .snar! Senza di esso, il prossimo tar -g farà un full.
# Backup anche il file .snar stesso.
```

### Archivi split (suddivisione)

```bash
# CREARE ARCHIVIO SPLIT (per limitazioni filesystem o upload)
tar czf - /srv/data | split -b 2G - /backup/data-$(date +%Y%m%d).tar.gz.

# Risultato: data-20260522.tar.gz.aa, data-20260522.tar.gz.ab, etc.

# RICOSTRUIRE E ESTRARRE
cat /backup/data-20260522.tar.gz.* | tar xzf - -C /tmp/restore

# SPLIT CON VERIFICA (checksum per ogni parte)
tar czf - /srv/data | split -b 2G --additional-suffix=.part \
  --filter='tee >(sha256sum > "$FILE.sha256") > "$FILE"' \
  - /backup/data-

# VERIFICARE INTEGRITÀ PARTI
cd /backup && sha256sum -c *.sha256
```

### Compressione standalone

```bash
# COMPRESSIONE STANDALONE
gzip file                            # → file.gz (rimuove originale)
gzip -k file                         # Mantiene originale
gunzip file.gz                       # Decomprimi
zstd file                            # → file.zst (veloce)
zstd -d file.zst                     # Decomprimi
xz file                              # → file.xz (massima compressione)
xz -d file.xz

# COMPRESSIONE MULTI-THREAD
pigz file                            # gzip parallelo
pigz -k -p 4 file                    # Mantieni originale, 4 thread
pbzip2 file                          # bzip2 parallelo
xz -T0 file                          # xz con tutti i core
zstd -T0 file                        # zstd con tutti i core

# COMPRESSIONE CON INTEGRITÀ
gzip -k file && md5sum file.gz > file.gz.md5
zstd --check file                    # verifica integrità automatica
```

---

## Duplicity: Backup Cifrato Incrementale

Duplicity produce backup cifrati con GPG verso storage remoto. Supporta full e incrementali con una catena di volumi cifrati.

### Concetti base

```
Volume: file cifrato di dimensione fissa (default 25MB)
Full backup: tutti i dati divisi in volumi cifrati
Incremental: solo i delta rispetto al full precedente
Manifest: indice dei file e dei volumi che li contengono
Signature: hash dei blocchi per calcolo delta (come rsync)
```

### Installazione e configurazione

```bash
# Installazione
sudo apt install duplicity python3-boto3    # Debian/Ubuntu
sudo dnf install duplicity python3-boto3    # Fedora/RHEL

# Generare chiave GPG per cifratura (se non ne hai una)
gpg --full-generate-key
# Tipo: RSA, 4096 bit, scadenza: 2 anni
# Annotare l'ID della chiave (es. ABC123DEF456)

# Esportare la chiave pubblica (per restore su altri sistemi)
gpg --export --armor ABC123DEF456 > backup-key.pub.asc
gpg --export-secret-keys --armor ABC123DEF456 > backup-key.priv.asc
# Conservare backup-key.priv.asc in luogo SICURO e SEPARATO
```

### Backup verso destinazioni

```bash
# BACKUP LOCALE
duplicity /srv/data file:///backup/duplicity

# BACKUP VERSO S3
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
export PASSPHRASE="passphrase-gpg"

duplicity \
  --encrypt-key ABC123DEF456 \
  --full-if-older-than 30D \
  --volsize 200 \
  --exclude-filelist /etc/duplicity/exclude.txt \
  /srv/data \
  s3://s3.amazonaws.com/bucket-name/backup/

# BACKUP VERSO GCS
duplicity \
  --encrypt-key ABC123DEF456 \
  /srv/data \
  gs://bucket-name/backup/

# BACKUP VERSO SFTP
duplicity \
  --encrypt-key ABC123DEF456 \
  /srv/data \
  sftp://user@server//backup/duplicity/

# BACKUP VERSO RSYNC (via SSH)
duplicity \
  --encrypt-key ABC123DEF456 \
  /srv/data \
  rsync://user@server//backup/duplicity/

# OPZIONI IMPORTANTI
# --full-if-older-than 30D  → forza full se ultimo full > 30 giorni
# --volsize 200             → dimensione volume in MB
# --asynchronous-upload     → upload in parallelo alla compressione
# --encrypt-key             → chiave GPG per cifratura
# --sign-key                → chiave GPG per firma
# --no-encryption           → disabilita cifratura (non raccomandato)
```

### Restore e verifica

```bash
# RESTORE COMPLETO
export PASSPHRASE="passphrase-gpg"
duplicity restore \
  s3://s3.amazonaws.com/bucket-name/backup/ \
  /tmp/restore/

# RESTORE SPECIFICO (file o directory)
duplicity restore \
  --file-to-restore etc/nginx/nginx.conf \
  s3://s3.amazonaws.com/bucket-name/backup/ \
  /tmp/nginx.conf

# RESTORE A UN PUNTO NEL TEMPO
duplicity restore \
  --time 3D \
  s3://s3.amazonaws.com/bucket-name/backup/ \
  /tmp/restore/
# --time 3D = 3 giorni fa
# --time 2026-05-20T14:00:00 = timestamp specifico

# LISTA BACKUP
duplicity collection-status \
  s3://s3.amazonaws.com/bucket-name/backup/

# LISTA FILE in un backup
duplicity list-current-files \
  s3://s3.amazonaws.com/bucket-name/backup/

# VERIFICA INTEGRITÀ
duplicity verify \
  s3://s3.amazonaws.com/bucket-name/backup/ \
  /srv/data

# PULIZIA VECCHI BACKUP
duplicity remove-older-than 90D --force \
  s3://s3.amazonaws.com/bucket-name/backup/

duplicity remove-all-but-n-full 3 --force \
  s3://s3.amazonaws.com/bucket-name/backup/

# PULIZIA BACKUP INCOMPLETI
duplicity cleanup --force \
  s3://s3.amazonaws.com/bucket-name/backup/
```

---

## Snapshot: LVM, ZFS, Btrfs

### LVM Snapshot — Backup consistente

Gli snapshot LVM creano una copia point-in-time del volume logico. Fondamentali per backup consistenti di database e applicazioni che scrivono continuamente.

```bash
# WORKFLOW COMPLETO: snapshot → backup → cleanup

# 1. Verificare spazio disponibile nel Volume Group
sudo vgs
sudo lvs

# 2. Creare snapshot (richiede spazio libero nel VG)
sudo lvcreate -s -L 5G -n snap_data /dev/vg/lv_data
# -s         → snapshot
# -L 5G      → spazio per le modifiche durante il backup
# Il volume originale continua a funzionare normalmente.
# Lo snapshot cattura lo stato al momento della creazione.

# ATTENZIONE: lo snapshot usa spazio per le modifiche al volume originale.
# Se il volume originale cambia molto durante il backup, lo snapshot
# può esaurire lo spazio e diventare invalido. Dimensionare adeguatamente.

# 3. Montare (read-only per backup)
sudo mount -o ro /dev/vg/snap_data /mnt/snapshot

# 4. Backup dallo snapshot (dati consistenti)
tar czf /backup/data-$(date +%Y%m%d).tar.gz /mnt/snapshot/
# oppure con rsync
rsync -avz /mnt/snapshot/ /backup/data/
# oppure con borg
borg create /backup/borg::data-$(date +%Y%m%d) /mnt/snapshot/

# 5. Cleanup
sudo umount /mnt/snapshot
sudo lvremove -f /dev/vg/snap_data

# MONITORARE UTILIZZO SNAPSHOT
sudo lvs -o lv_name,lv_size,data_percent,snap_percent
# Se snap_percent raggiunge 100%, lo snapshot diventa invalido!
```

### Snapshot per database consistenti

```bash
# WORKFLOW: database consistente via LVM snapshot

# 1. Flush e lock il database (PostgreSQL)
psql -c "SELECT pg_start_backup('lvm-snapshot', true);"

# 2. Creare snapshot
sudo lvcreate -s -L 10G -n snap_pgdata /dev/vg/lv_pgdata

# 3. Rilasciare il lock
psql -c "SELECT pg_stop_backup();"

# 4. Montare e backuppare lo snapshot
sudo mount -o ro /dev/vg/snap_pgdata /mnt/snapshot
tar czf /backup/pgdata-$(date +%Y%m%d).tar.gz /mnt/snapshot/

# 5. Cleanup
sudo umount /mnt/snapshot
sudo lvremove -f /dev/vg/snap_pgdata

# Per MySQL/MariaDB:
mysql -e "FLUSH TABLES WITH READ LOCK;"
sudo lvcreate -s -L 10G -n snap_mysql /dev/vg/lv_mysql
mysql -e "UNLOCK TABLES;"
# ... montare, backuppare, cleanup come sopra
```

### ZFS Snapshot

```bash
# Snapshot istantaneo
sudo zfs snapshot tank/data@$(date +%Y%m%d)

# Snapshot ricorsivo (tutti i dataset figli)
sudo zfs snapshot -r tank@$(date +%Y%m%d)

# Lista snapshot
sudo zfs list -t snapshot

# Rollback (ATTENZIONE: distruttivo, riporta il dataset allo stato dello snapshot)
sudo zfs rollback tank/data@20260520

# Clonare snapshot (crea dataset scrivibile dallo snapshot)
sudo zfs clone tank/data@20260520 tank/data-clone

# Backup via send/receive
sudo zfs send tank/data@20240115 | gzip > /backup/zfs-20240115.gz
sudo zfs send tank/data@20240115 | ssh backup-server "zfs receive backup/data"

# Incrementale
sudo zfs send -i tank/data@20240115 tank/data@20240116 | \
  ssh backup-server "zfs receive backup/data"

# Pulizia snapshot vecchi
sudo zfs list -t snapshot -o name -H | while read snap; do
    SNAP_DATE=$(echo "$snap" | grep -oP '\d{8}')
    if [ -n "$SNAP_DATE" ]; then
        SNAP_EPOCH=$(date -d "$SNAP_DATE" +%s 2>/dev/null || echo 0)
        CUTOFF_EPOCH=$(date -d "30 days ago" +%s)
        if [ "$SNAP_EPOCH" -lt "$CUTOFF_EPOCH" ]; then
            echo "Rimuovo: $snap"
            sudo zfs destroy "$snap"
        fi
    fi
done
```

### Btrfs Snapshot

```bash
# Snapshot read-only
sudo btrfs subvolume snapshot -r /mnt/data /mnt/snapshots/data-$(date +%Y%m%d)

# Backup via send/receive
sudo btrfs send /mnt/snapshots/data-20240115 | \
  ssh backup-server "btrfs receive /mnt/backup/"

# Incrementale (richiede snapshot padre presente su entrambi i sistemi)
sudo btrfs send -p /mnt/snapshots/data-20240115 /mnt/snapshots/data-20240116 | \
  ssh backup-server "btrfs receive /mnt/backup/"

# Lista subvolume
sudo btrfs subvolume list /mnt/data

# Cancellare snapshot
sudo btrfs subvolume delete /mnt/snapshots/data-20240115
```

---

## Backup di Database

### PostgreSQL

#### pg_dump — Backup logico

```bash
# Dump singolo database (formato custom, compresso)
pg_dump -Fc -Z 6 -f /backup/mydb-$(date +%Y%m%d).dump mydb

# Dump singolo database (formato plain SQL)
pg_dump -f /backup/mydb-$(date +%Y%m%d).sql mydb

# Dump tutti i database
pg_dumpall -f /backup/all-databases-$(date +%Y%m%d).sql

# Dump solo schema (struttura)
pg_dump --schema-only -f /backup/mydb-schema.sql mydb

# Dump solo dati
pg_dump --data-only -f /backup/mydb-data.sql mydb

# Dump tabella specifica
pg_dump -t nome_tabella -Fc -f /backup/tabella.dump mydb

# Dump con compressione parallela (PostgreSQL 16+)
pg_dump -Fd -j 4 -f /backup/mydb-dir mydb
# -Fd = directory format (un file per tabella)
# -j 4 = 4 job paralleli

# RESTORE
pg_restore -d mydb /backup/mydb-20260520.dump
pg_restore -d mydb --clean --if-exists /backup/mydb-20260520.dump
# --clean → DROP oggetti prima di CREATE
# --if-exists → non errore se l'oggetto non esiste

# Restore con formato directory (parallelo)
pg_restore -d mydb -j 4 /backup/mydb-dir

# Restore da plain SQL
psql mydb < /backup/mydb-20260520.sql
```

#### pg_basebackup — Backup fisico

```bash
# Backup fisico completo (copia i file del data directory)
pg_basebackup -D /backup/pg-base-$(date +%Y%m%d) \
  -Ft -z -P -X stream \
  -h localhost -U replicator
# -D     → directory destinazione
# -Ft    → formato tar
# -z     → compressione gzip
# -P     → progress bar
# -X stream → includi WAL durante il backup (consistenza garantita)

# Con compressione avanzata (PostgreSQL 15+)
pg_basebackup -D /backup/pg-base \
  --compress=zstd:6 \
  -Ft -P -X stream

# Configurare l'utente replicator
# In pg_hba.conf:
# host replication replicator 10.0.0.0/24 scram-sha-256
# In postgresql.conf:
# wal_level = replica
# max_wal_senders = 5
```

#### WAL Archiving e Point-In-Time Recovery (PITR)

```bash
# CONFIGURAZIONE WAL ARCHIVING
# In postgresql.conf:
# wal_level = replica
# archive_mode = on
# archive_command = 'test ! -f /backup/wal/%f && cp %p /backup/wal/%f'
# archive_timeout = 300  # forza archiviazione ogni 5 minuti

# Archive command più robusto
# archive_command = 'rsync -a %p backup-server:/backup/wal/%f'

# Archive command con compressione
# archive_command = 'gzip < %p > /backup/wal/%f.gz'

# POINT-IN-TIME RECOVERY (PITR)
# 1. Fermare PostgreSQL
sudo systemctl stop postgresql

# 2. Spostare (non cancellare!) il data directory corrente
sudo mv /var/lib/postgresql/16/main /var/lib/postgresql/16/main.old

# 3. Restore il base backup
sudo tar xzf /backup/pg-base-20260520/base.tar.gz -C /var/lib/postgresql/16/main

# 4. Creare il file di recovery
cat > /var/lib/postgresql/16/main/recovery.signal << 'EOF'
EOF

# In postgresql.conf (o postgresql.auto.conf):
# restore_command = 'cp /backup/wal/%f %p'
# recovery_target_time = '2026-05-22 14:30:00'
# recovery_target_action = 'promote'

# 5. Avviare PostgreSQL (eseguirà il recovery)
sudo systemctl start postgresql

# 6. Verificare
psql -c "SELECT pg_is_in_recovery();"  # Deve restituire false (recovery completato)
```

### MySQL / MariaDB

#### mysqldump — Backup logico

```bash
# Dump singolo database
mysqldump --single-transaction --routines --triggers \
  -u root -p mydb > /backup/mydb-$(date +%Y%m%d).sql

# Dump tutti i database
mysqldump --single-transaction --routines --triggers --events \
  --all-databases -u root -p > /backup/all-$(date +%Y%m%d).sql

# Dump con compressione
mysqldump --single-transaction mydb | gzip > /backup/mydb-$(date +%Y%m%d).sql.gz

# --single-transaction  → snapshot consistente per InnoDB (no lock)
# --routines            → include stored procedure e functions
# --triggers            → include trigger
# --events              → include eventi schedulati
# --master-data=2       → include posizione binlog (per replica)
# --set-gtid-purged=OFF → per compatibilità in ambienti senza GTID

# RESTORE
mysql -u root -p mydb < /backup/mydb-20260520.sql
gunzip < /backup/mydb-20260520.sql.gz | mysql -u root -p mydb

# Restore database con nome diverso
mysql -u root -p -e "CREATE DATABASE mydb_restore;"
mysql -u root -p mydb_restore < /backup/mydb-20260520.sql
```

#### Percona XtraBackup — Backup fisico

```bash
# Installazione
sudo apt install percona-xtrabackup-80    # MySQL 8.0

# FULL BACKUP
xtrabackup --backup --target-dir=/backup/xtra-full \
  --user=root --password='xxx'

# Preparare il backup (applicare i log)
xtrabackup --prepare --target-dir=/backup/xtra-full

# INCREMENTAL BACKUP
# Primo incrementale (basato sul full)
xtrabackup --backup --target-dir=/backup/xtra-incr1 \
  --incremental-basedir=/backup/xtra-full \
  --user=root --password='xxx'

# Secondo incrementale (basato sul primo incrementale)
xtrabackup --backup --target-dir=/backup/xtra-incr2 \
  --incremental-basedir=/backup/xtra-incr1 \
  --user=root --password='xxx'

# RESTORE (applicare incrementali al full, poi restore)
# 1. Preparare il full
xtrabackup --prepare --apply-log-only --target-dir=/backup/xtra-full
# 2. Applicare incrementale 1
xtrabackup --prepare --apply-log-only --target-dir=/backup/xtra-full \
  --incremental-dir=/backup/xtra-incr1
# 3. Applicare ultimo incrementale (senza --apply-log-only)
xtrabackup --prepare --target-dir=/backup/xtra-full \
  --incremental-dir=/backup/xtra-incr2
# 4. Restore
sudo systemctl stop mysql
sudo mv /var/lib/mysql /var/lib/mysql.old
xtrabackup --copy-back --target-dir=/backup/xtra-full
sudo chown -R mysql:mysql /var/lib/mysql
sudo systemctl start mysql
```

---

## Backup a Livello di Filesystem

### dd — Copia blocco per blocco

```bash
# CLONARE DISCO INTERO
sudo dd if=/dev/sda of=/backup/sda.img bs=64K status=progress
# if = input file (sorgente)
# of = output file (destinazione)
# bs = block size (64K è un buon compromesso)
# status=progress = mostra progresso

# CLONARE CON COMPRESSIONE
sudo dd if=/dev/sda bs=64K status=progress | gzip -c > /backup/sda.img.gz
sudo dd if=/dev/sda bs=64K status=progress | zstd -T0 > /backup/sda.img.zst

# RESTORE DA IMMAGINE
sudo dd if=/backup/sda.img of=/dev/sdb bs=64K status=progress
gunzip -c /backup/sda.img.gz | sudo dd of=/dev/sdb bs=64K status=progress

# CLONARE SOLO PARTIZIONE
sudo dd if=/dev/sda1 of=/backup/sda1.img bs=64K status=progress

# CREARE CHECKSUM DELL'IMMAGINE
sha256sum /backup/sda.img > /backup/sda.img.sha256

# ATTENZIONE dd:
# - Copia TUTTO, incluso spazio libero → immagini grandi
# - Non si può fare restore su disco più piccolo
# - Nessuna verifica integrità integrata
# - Se il filesystem è montato e in uso, il backup può essere inconsistente
# - Per dischi grandi, usare partclone che è molto più efficiente
```

### partclone — Clone intelligente

```bash
# Installazione
sudo apt install partclone

# BACKUP PARTIZIONE (solo blocchi usati, molto più veloce di dd)
sudo partclone.ext4 -c -s /dev/sda1 -o /backup/sda1.img
# -c = clone
# -s = source
# -o = output

# Con compressione
sudo partclone.ext4 -c -s /dev/sda1 | gzip > /backup/sda1.pcl.gz

# RESTORE
sudo partclone.ext4 -r -s /backup/sda1.img -o /dev/sda1
gunzip -c /backup/sda1.pcl.gz | sudo partclone.ext4 -r -s - -o /dev/sda1

# Filesystem supportati
# partclone.ext4    → ext2/3/4
# partclone.ntfs    → NTFS
# partclone.fat32   → FAT32
# partclone.btrfs   → Btrfs
# partclone.xfs     → XFS
# partclone.dd      → qualsiasi (come dd, meno efficiente)
```

### Clonezilla — Bare metal completo

```bash
# Clonezilla è un'interfaccia completa sopra partclone + dd + altri strumenti.
# Si avvia da USB/PXE e clona interi dischi o partizioni.

# Modalità di utilizzo:
# 1. Avviare da USB Clonezilla Live
# 2. Scegliere modalità:
#    - device-image:  disco/partizione → file immagine
#    - device-device: disco → disco (clone diretto)
# 3. Scegliere sorgente e destinazione
# 4. Opzioni di compressione e verifica

# Uso da riga di comando (modalità non interattiva)
# Salvare immagine disco
sudo ocs-sr -q2 -c -j2 -z5p -i 4096 -sfsck -senc -p poweroff \
  savedisk backup-$(date +%Y%m%d) sda
# -q2        → priorità partclone
# -z5p       → compressione zstd parallela
# -sfsck     → skip filesystem check
# -senc      → skip crittografia
# -p poweroff → spegni dopo il completamento

# Restore immagine
sudo ocs-sr -e1 auto -c -r -j2 -p reboot \
  restoredisk backup-20260520 sda
```

---

## Cloud Backup con rclone

rclone è il "rsync per il cloud": supporta 40+ provider di storage con un'interfaccia unificata.

### Configurazione

```bash
# Installazione
curl -s https://rclone.org/install.sh | sudo bash
# Nota: verificare la firma prima di eseguire in produzione

# Configurazione interattiva
rclone config
# Segue wizard: nome remote, tipo provider, credenziali

# CONFIGURAZIONE MANUALE — /root/.config/rclone/rclone.conf
# (esempio per più backend)

# [s3-backup]
# type = s3
# provider = AWS
# access_key_id = AKIAXXXXXXXX
# secret_access_key = xxxxxxxx
# region = eu-west-1
# storage_class = STANDARD_IA

# [b2-archive]
# type = b2
# account = xxxxxxxxxxxx
# key = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# [gcs-backup]
# type = google cloud storage
# project_number = 123456789
# service_account_file = /etc/rclone/gcs-service-account.json
# location = EU

# [azure-backup]
# type = azureblob
# account = storageaccountname
# key = xxxxxxxx

# [sftp-nas]
# type = sftp
# host = nas.internal
# user = backup
# key_file = /root/.ssh/backup_key

# [crypt-s3]
# type = crypt
# remote = s3-backup:bucket/encrypted
# password = *** (offuscata da rclone config)
# password2 = *** (salt)
```

### Operazioni di backup

```bash
# SYNC (mirror source → dest, cancella file non presenti in source)
rclone sync /srv/data s3-backup:my-bucket/data --progress

# COPY (copia senza cancellare dalla destinazione)
rclone copy /srv/data s3-backup:my-bucket/data --progress

# BACKUP CIFRATO (usando backend crypt)
rclone sync /srv/data crypt-s3: --progress
# Il backend crypt cifra file name + contenuto prima dell'upload

# CON LIMITAZIONE BANDWIDTH
rclone sync /srv/data s3-backup:bucket/data \
  --bwlimit 50M \
  --progress

# CON ESCLUSIONI
rclone sync /home s3-backup:bucket/home \
  --exclude '*.log' \
  --exclude '.cache/**' \
  --exclude 'node_modules/**' \
  --exclude-from /etc/rclone/exclude.txt

# TRASFERIMENTI PARALLELI
rclone sync /srv/data s3-backup:bucket/data \
  --transfers 8 \
  --checkers 16 \
  --progress

# VERIFICA
rclone check /srv/data s3-backup:bucket/data
rclone check --one-way /srv/data s3-backup:bucket/data  # solo sorgente → dest

# LISTA FILE REMOTI
rclone ls s3-backup:bucket/data
rclone lsl s3-backup:bucket/data       # con date e dimensioni
rclone size s3-backup:bucket/data      # dimensione totale

# MOUNT COME FILESYSTEM (FUSE)
rclone mount s3-backup:bucket /mnt/s3 --daemon
# Utile per navigare e restore di singoli file

# RESTORE
rclone copy s3-backup:bucket/data/important.doc /tmp/restore/
rclone sync s3-backup:bucket/data /srv/data-restore --progress
```

### Script rclone per backup automatizzato

```bash
#!/bin/bash
# /usr/local/bin/rclone-backup.sh
set -euo pipefail

REMOTE="crypt-s3"
SRC="/srv/data"
DEST="$REMOTE:backup/$(hostname)/data"
LOG="/var/log/backup/rclone-$(date +%Y%m%d).log"
LOCK="/var/run/rclone-backup.lock"

exec > >(tee -a "$LOG") 2>&1

exec 200>"$LOCK"
flock -n 200 || { echo "Backup già in esecuzione"; exit 1; }

echo "=== rclone backup: $(date --iso-8601=seconds) ==="

rclone sync "$SRC" "$DEST" \
  --transfers 4 \
  --checkers 8 \
  --bwlimit "08:00,10M 23:00,100M" \
  --exclude-from /etc/rclone/exclude.txt \
  --log-file="$LOG" \
  --log-level INFO \
  --stats 60s \
  --stats-one-line

# Verificare integrità
rclone check --one-way "$SRC" "$DEST" 2>&1 | tail -5

echo "=== Completato: $(date --iso-8601=seconds) ==="

# --bwlimit con orari: 10MB/s durante il giorno, 100MB/s di notte
```

### rclone — Cifratura e Backend Avanzati

rclone supporta cifratura client-side trasparente tramite il backend `crypt`, che si sovrappone a qualsiasi altro backend. La cifratura è zero-knowledge: il provider cloud non vede mai dati o nomi file in chiaro.

#### Backend crypt — Architettura

```
┌────────────────────┐
│  rclone sync/copy  │     Operazioni normali
└────────┬───────────┘
         │
┌────────▼───────────┐
│  Backend crypt     │     Cifra nomi file + contenuto
│  XSalsa20+Poly1305 │     Chiave derivata dalla password
└────────┬───────────┘
         │
┌────────▼───────────┐
│  Backend reale     │     S3, B2, SFTP, GCS, Azure...
│  (trasporto)       │     Vede solo dati cifrati
└────────────────────┘
```

**Algoritmo**: XSalsa20 per la cifratura del contenuto, Poly1305 per l'autenticazione (integrità). I nomi file vengono cifrati con EME (ECB-Mix-ECB) o offuscati con una funzione deterministica.

```bash
# CONFIGURARE BACKEND CRYPT

# Creare il backend base (es. S3)
# [s3-raw]
# type = s3
# provider = AWS
# access_key_id = AKIA...
# secret_access_key = ...
# region = eu-west-1

# Creare il backend crypt SOPRA il backend S3
rclone config
# Nome: s3-crypt
# Tipo: crypt
# Remote: s3-raw:my-backup-bucket/encrypted
# Password: [generata automaticamente — rclone config la offusca]
# Password2 (salt): [generata automaticamente]

# BEST PRACTICE: wrappare il crypt attorno a un percorso SPECIFICO
# nel bucket, non alla radice. Questo permette di avere dati
# cifrati e non cifrati nello stesso bucket se necessario.
#
# CORRETTO:  remote = s3-raw:bucket/encrypted-data
# RISCHIOSO: remote = s3-raw:bucket  (tutto il bucket diventa cifrato)

# Modalità cifratura nomi file:
# "standard" — cifra completamente (nomi illeggibili sul cloud)
# "obfuscate" — offusca (reversibile, meno sicuro, nomi più corti)
# "off" — nomi file in chiaro (solo contenuto cifrato)

# UTILIZZO — identico a operazioni normali
rclone sync /srv/data s3-crypt: --progress
rclone ls s3-crypt:               # Vedi nomi file originali
rclone ls s3-raw:my-backup-bucket/encrypted  # Vedi nomi cifrati
```

#### Cifratura server-side (SSE) per S3

```bash
# SSE-S3 — AWS gestisce le chiavi (AES-256)
# In rclone.conf:
# [s3-sse]
# type = s3
# server_side_encryption = AES256

# SSE-KMS — Usa AWS Key Management Service
# [s3-kms]
# type = s3
# server_side_encryption = aws:kms
# sse_kms_key_id = arn:aws:kms:eu-west-1:123456:key/abcdef

# SSE-C — Chiave fornita dal cliente
# rclone --s3-sse-customer-algorithm AES256 \
#   --s3-sse-customer-key BASE64_KEY \
#   sync /data s3-sse:bucket/

# COMBINARE client-side (crypt) e server-side (SSE)
# È possibile e raccomandato per massima protezione:
# - crypt cifra PRIMA dell'upload (il provider non vede nulla)
# - SSE cifra a riposo sul server (protezione aggiuntiva)
```

#### Cifratura Backblaze B2

```bash
# B2 supporta cifratura server-side con chiavi gestite da Backblaze
# Abilitare la cifratura di default sul bucket:
# b2 update-bucket --default-server-side-encryption SSE-B2 my-bucket

# Per rclone: la cifratura server-side B2 è trasparente.
# Aggiungere cifratura client-side con crypt per zero-knowledge:

# [b2-raw]
# type = b2
# account = xxxx
# key = xxxx

# [b2-crypt]
# type = crypt
# remote = b2-raw:backup-bucket/encrypted
# password = *** (offuscata)
# password2 = *** (salt)
```

#### Strategia multi-backend con rclone

```bash
# STRATEGIA 3-2-1 con rclone — tre destinazioni diverse

# Backup 1: S3 cifrato (copia primaria cloud)
rclone sync /srv/data s3-crypt: --transfers 8

# Backup 2: B2 cifrato (copia secondaria cloud, provider diverso)
rclone sync /srv/data b2-crypt: --transfers 4 --bwlimit 20M

# Backup 3: NAS SFTP locale (copia on-premise)
rclone sync /srv/data sftp-nas:backup/data --transfers 4

# SICUREZZA rclone.conf
# Il file di configurazione contiene credenziali (offuscate, non cifrate).
# Proteggere con permessi restrittivi:
chmod 600 ~/.config/rclone/rclone.conf

# Cifrare il file di configurazione con password
rclone config --config /secure/rclone.conf
export RCLONE_CONFIG=/secure/rclone.conf
export RCLONE_CONFIG_PASS="password-del-config"

# ATTENZIONE: se la password del backend crypt viene persa,
# i dati cifrati sono irrecuperabili. Non esiste "reset password"
# perché la chiave di cifratura è derivata direttamente dalla password.
# Conservare la password in almeno 2 posti sicuri separati.
```

---

## Proxmox Backup Server per Workload Misti

Proxmox Backup Server (PBS) è una soluzione di backup enterprise open-source progettata per ambienti virtualizzati, ma utilizzabile anche per backup di host Linux standalone. PBS offre deduplicazione a livello di chunk, cifratura client-side, verifica integrata e un'interfaccia web per la gestione.

### Architettura PBS

```
┌─────────────────────────────────────────────────┐
│              Proxmox Backup Server              │
│                                                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│  │ Datastore │  │ Datastore │  │ Datastore │  │
│  │ (HDD/SSD) │  │ (NFS)     │  │ (ZFS)     │  │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  │
│        │              │              │          │
│  ┌─────▼──────────────▼──────────────▼─────┐   │
│  │         Dedup Engine (SHA-256)           │   │
│  │    Chunk 1-4 MiB, content-defined       │   │
│  │    Rapporto tipico: 6:1 — 12:1          │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  Web UI (:8007)  │  API REST  │  CLI client    │
└─────────────────────────────────────────────────┘
         ▲              ▲              ▲
         │              │              │
    ┌────┘    ┌─────────┘    ┌─────────┘
    │         │              │
┌───┴───┐ ┌──┴────┐ ┌───────┴────────┐
│ PVE   │ │ Linux │ │ Linux remoto   │
│ host  │ │ host  │ │ (qualsiasi)    │
└───────┘ └───────┘ └────────────────┘
```

**Datastore**: directory su disco (HDD, SSD, ZFS) dove PBS archivia i backup. Ogni VM o host viene suddiviso in chunk di 1-4 MiB con chunking content-defined (simile a Borg). I chunk sono indicizzati per SHA-256 e archiviati una sola volta. Rapporti di deduplicazione tipici: 10 TB logici in 1-2 TB fisici dopo alcune settimane.

**Formato pxar**: PBS usa il formato `.pxar` (Proxmox Archive) per i file archive. È POSIX-compliant e content-addressable — i dati vengono suddivisi in chunk a dimensione variabile, ciascuno hashato e caricato solo se non già presente sul server.

### Installazione e Configurazione PBS

```bash
# PBS è disponibile come ISO dedicata o come pacchetto su Debian
# Versione corrente: PBS 4.2 (basato su Debian 13, solo x86_64)

# Installazione su Debian esistente
echo "deb http://download.proxmox.com/debian/pbs bookworm pbs-no-subscription" \
  > /etc/apt/sources.list.d/pbs.list
wget https://enterprise.proxmox.com/debian/proxmox-release-bookworm.gpg \
  -O /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg
apt update && apt install proxmox-backup-server

# Accedere alla Web UI: https://pbs-host:8007
# Creare un datastore dalla UI: Datastore → Add Datastore
# Specificare: nome, percorso su disco, retention policy

# DATASTORE su ZFS (raccomandato per integrità dati)
zpool create backup-pool mirror /dev/sdb /dev/sdc
# Creare datastore puntando a /backup-pool/datastore1
```

### proxmox-backup-client su Host Linux Standalone

```bash
# Installare il client su qualsiasi distribuzione Linux
# Debian/Ubuntu:
apt install proxmox-backup-client

# Per altre distribuzioni: compilare da sorgente o usare il binario statico
# https://pbs.proxmox.com/docs/backup-client.html

# CONFIGURAZIONE
export PBS_REPOSITORY="user@pam@pbs-server:datastore1"
export PBS_PASSWORD="password"
# Oppure usare un API token (raccomandato per automazione)
export PBS_REPOSITORY="user@pam!token-name@pbs-server:datastore1"

# BACKUP DI DIRECTORY
proxmox-backup-client backup \
  etc.pxar:/etc \
  home.pxar:/home \
  srv.pxar:/srv \
  --repository backup-user@pbs-server:store1

# BACKUP CON CIFRATURA CLIENT-SIDE
# Generare chiave di cifratura
proxmox-backup-client key create --kdf scrypt /etc/pbs-encryption-key.json

# Backup cifrato (il server non vede i dati in chiaro)
proxmox-backup-client backup \
  root.pxar:/ \
  --keyfile /etc/pbs-encryption-key.json \
  --repository user@pam@pbs-server:store1 \
  --exclude /proc --exclude /sys --exclude /dev \
  --exclude /run --exclude /tmp --exclude /var/cache

# ESCLUSIONI con .pxarexclude
# Creare file .pxarexclude nelle directory da escludere:
# /home/.pxarexclude:
# .cache/
# Downloads/
# node_modules/
# *.log

# NAMESPACE per organizzare i backup
# I namespace raggruppano backup logicamente (es. per team, progetto, ambiente)
proxmox-backup-client backup \
  data.pxar:/srv/data \
  --repository user@pam@pbs-server:store1 \
  --ns production/webservers
```

### Restore e Verifica da PBS

```bash
# LISTA SNAPSHOT
proxmox-backup-client snapshot list \
  --repository user@pam@pbs-server:store1

# RESTORE COMPLETO
proxmox-backup-client restore \
  etc.pxar /tmp/restore-etc \
  --repository user@pam@pbs-server:store1

# RESTORE FILE SPECIFICO (via mount FUSE)
mkdir /mnt/pbs-restore
proxmox-backup-client mount \
  etc.pxar /mnt/pbs-restore \
  --repository user@pam@pbs-server:store1
# Copiare i file necessari da /mnt/pbs-restore/
cp /mnt/pbs-restore/nginx/nginx.conf /tmp/
fusermount -u /mnt/pbs-restore

# VERIFICA INTEGRITÀ
# PBS ha verifica integrata nella Web UI: Datastore → Verify
# Da CLI:
proxmox-backup-client snapshot list \
  --repository user@pam@pbs-server:store1 \
  --output-format json | python3 -c "
import sys, json
for s in json.load(sys.stdin):
    print(f\"{s['backup-id']} — verificato: {s.get('verify-state', 'mai')}\")"

# GARBAGE COLLECTION (analogo a borg compact)
# Dalla Web UI: Datastore → Garbage Collection → Run Now
# Rimuove chunk non più referenziati dopo la pulizia degli snapshot
```

### PBS per Workload Misti

```bash
# PBS eccelle nel consolidare backup da fonti eterogenee:
#
# 1. VM Proxmox VE (QEMU/KVM) → vzdump integrato
# 2. Container LXC → vzdump integrato
# 3. Host Linux standalone → proxmox-backup-client
# 4. File server → proxmox-backup-client con pxar
#
# Vantaggi rispetto a Borg/Restic per ambienti misti:
# - Un'unica interfaccia web per tutti i backup
# - Dedup cross-backup tra VM e host diversi
# - Verifica integrata schedulabile dalla UI
# - Sync/push tra datastore (replicazione offsite)
# - Gestione namespace per organizzazione logica
#
# Limitazioni:
# - Solo x86_64 per il server
# - Client ufficiale solo per Linux
# - Meno backend cloud rispetto a Restic (primariamente locale/SSH)
# - Push sync richiede PBS anche sulla destinazione
```

---

## Automazione Backup

### Script Completo con BorgBackup

```bash
#!/bin/bash
# /usr/local/bin/borg-backup.sh
set -euo pipefail

export BORG_REPO="/backup/borg"
export BORG_PASSPHRASE="$(cat /etc/borg-passphrase)"

HOSTNAME=$(hostname)
DATE=$(date +%Y%m%d-%H%M)
LOG="/var/log/backup/borg-$DATE.log"

exec > >(tee -a "$LOG") 2>&1

echo "=== Backup started: $DATE ==="

# Backup
borg create \
  --stats --progress --compression zstd,3 \
  "::${HOSTNAME}-${DATE}" \
  /etc /home /srv /var/lib \
  --exclude '/home/*/.cache' \
  --exclude '*/node_modules' \
  --exclude '*.tmp'

# Pulizia
borg prune \
  --keep-daily=7 \
  --keep-weekly=4 \
  --keep-monthly=12 \
  --keep-yearly=2 \
  --stats

borg compact

# Verifica
borg check --last 1

echo "=== Backup completed: $(date) ==="
```

### Systemd Timer

```ini
# /etc/systemd/system/borg-backup.service
[Unit]
Description=BorgBackup
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/borg-backup.sh
Nice=19
IOSchedulingClass=idle
# Hardening
ProtectSystem=full
PrivateTmp=true
NoNewPrivileges=true
```

```ini
# /etc/systemd/system/borg-backup.timer
[Unit]
Description=BorgBackup Timer

[Timer]
OnCalendar=*-*-* 02:00:00
RandomizedDelaySec=30min
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# Abilitare e avviare
sudo systemctl enable --now borg-backup.timer

# Verificare stato
sudo systemctl list-timers --all | grep borg
sudo systemctl status borg-backup.timer
sudo systemctl status borg-backup.service   # ultimo run

# Esecuzione manuale
sudo systemctl start borg-backup.service

# Log
sudo journalctl -u borg-backup.service --since today
```

### Cron — Scheduling tradizionale

```bash
# CRONTAB per backup multipli
# /etc/cron.d/backup-schedule

# Backup dati ogni 6 ore
0 */6 * * * root /usr/local/bin/borg-backup.sh >> /var/log/backup/cron.log 2>&1

# Backup database ogni ora
0 * * * * root /usr/local/bin/db-backup.sh >> /var/log/backup/db-cron.log 2>&1

# Sync offsite giornaliero alle 3 di notte
0 3 * * * root /usr/local/bin/rclone-backup.sh >> /var/log/backup/rclone.log 2>&1

# Verifica integrità settimanale (domenica alle 5)
0 5 * * 0 root /usr/local/bin/backup-verify.sh >> /var/log/backup/verify.log 2>&1

# Pulizia log vecchi (mensile)
0 0 1 * * root find /var/log/backup -name '*.log' -mtime +90 -delete

# ANACRON per sistemi non sempre accesi
# /etc/anacrontab
1  5  backup-daily   /usr/local/bin/borg-backup.sh
7  10 backup-weekly  /usr/local/bin/backup-verify.sh
30 15 backup-monthly /usr/local/bin/backup-full-verify.sh
# periodo_giorni  ritardo_minuti  identificatore  comando
```

### borgmatic — Automazione Dichiarativa per BorgBackup

borgmatic è un framework di automazione che wrappa BorgBackup in un singolo file di configurazione YAML. Gestisce create, prune, compact, check, e hook per database e monitoring — eliminando la necessità di script bash personalizzati.

#### Installazione e configurazione iniziale

```bash
# Installazione
pip install borgmatic              # PyPI (raccomandato)
sudo apt install borgmatic         # Debian/Ubuntu (versione potenzialmente datata)

# Generare configurazione di esempio
borgmatic config generate
# Crea /etc/borgmatic/config.yaml con tutti i campi commentati

# Validare la configurazione
borgmatic config validate

# Eseguire un backup manuale
borgmatic create --verbosity 1

# Eseguire tutte le operazioni: create + prune + compact + check
borgmatic
```

#### Configurazione YAML completa

```yaml
# /etc/borgmatic/config.yaml

# --- Sorgenti ---
source_directories:
  - /etc
  - /home
  - /srv
  - /var/lib

exclude_patterns:
  - '*.pyc'
  - '*/__pycache__'
  - '*/node_modules'
  - '*/vendor'
  - '*/.cache'
  - '*.log'
  - '*.tmp'

exclude_caches: true
exclude_if_present:
  - .nobackup

# --- Repository ---
repositories:
  - path: /backup/borg
    label: locale
  - path: ssh://backup-user@nas.internal/./borg-repo
    label: nas

# --- Crittografia e compressione ---
encryption_passcommand: "cat /etc/borgmatic/passphrase"
# Alternativa: encryption_passphrase (meno sicuro, in chiaro nel YAML)

compression: zstd,3
# Opzioni: none, lz4, zstd,1-22, zlib,1-9, lzma,0-9

# --- Retention ---
keep_daily: 7
keep_weekly: 4
keep_monthly: 12
keep_yearly: 2

# --- Opzioni avanzate ---
checkpoint_interval: 600       # Checkpoint ogni 10 minuti
# relocated_repo_access_is_ok: true  # Se il repo viene spostato

# --- Storage ---
# archive_name_format: '{hostname}-{now:%Y%m%d-%H%M%S}'
```

#### Hook per database

```yaml
# --- Database hooks ---
# borgmatic esegue il dump PRIMA del backup e include il dump nell'archivio.
# Il dump viene eliminato dopo il backup.

postgresql_databases:
  - name: app_production
    hostname: localhost
    port: 5432
    username: postgres
    # password: (preferire .pgpass o variabile d'ambiente)
    format: custom           # custom = pg_dump -Fc (raccomandato)
    # options: "--no-owner"  # opzioni aggiuntive per pg_dump

  - name: all               # "all" esegue pg_dumpall
    hostname: localhost
    username: postgres

mysql_databases:
  - name: wordpress
    hostname: localhost
    username: root
    password: "${MYSQL_ROOT_PASSWORD}"   # Variabile d'ambiente
    options: "--single-transaction --routines --triggers"

  - name: all               # "all" esegue mysqldump --all-databases

sqlite_databases:
  - name: app_sqlite
    path: /srv/app/database.sqlite3

# RESTORE database da borgmatic
# borgmatic restore --archive latest --database app_production
# borgmatic restore --archive latest --database all
```

#### Hook per monitoring e notifiche

```yaml
# --- Monitoring hooks ---

# Healthchecks.io — Dead man's switch
# Se borgmatic non pinga entro l'intervallo configurato, Healthchecks avvisa.
healthchecks:
  ping_url: "https://hc-ping.com/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  send_logs: true            # Invia i log del backup come corpo del ping
  # ping_body_limit: 100000  # Limite dimensione log inviato (byte)
  states:
    - start                  # Pinga all'inizio
    - finish                 # Pinga alla fine
    - fail                   # Pinga in caso di errore

# ntfy — Push notification self-hosted
ntfy:
  topic: backup-alerts
  server: "https://ntfy.example.com"
  # Autenticazione (una delle due):
  # username: backup-monitor
  # password: "${NTFY_PASSWORD}"
  access_token: "${NTFY_TOKEN}"
  start:
    title: "Backup iniziato"
    message: "borgmatic ha iniziato il backup su {repository}"
    tags: "borgmatic,hourglass_flowing_sand"
    priority: default
  finish:
    title: "Backup completato"
    message: "borgmatic ha completato il backup su {repository}"
    tags: "borgmatic,white_check_mark"
    priority: default
  fail:
    title: "ERRORE backup"
    message: "borgmatic ha fallito il backup su {repository}"
    tags: "borgmatic,skull"
    priority: max
  states:
    - start
    - finish
    - fail

# --- Command hooks ---
# Comandi eseguiti in fasi specifiche del backup

before_backup:
  - echo "Inizio backup: $(date --iso-8601=seconds)"
  # - /usr/local/bin/pre-backup-checks.sh

after_backup:
  - echo "Backup completato: $(date --iso-8601=seconds)"

on_error:
  - echo "ERRORE durante il backup!" | mail -s "[BACKUP] Errore" admin@example.com
```

#### Esecuzione e integrazione systemd

```bash
# COMANDI borgmatic

# Backup completo (create + prune + compact + check)
borgmatic --verbosity 1

# Solo create
borgmatic create --stats --list --verbosity 1

# Solo prune
borgmatic prune --stats --list

# Solo compact
borgmatic compact

# Solo check
borgmatic check --verbosity 1

# Restore
borgmatic restore --archive latest
borgmatic restore --archive latest --database app_production

# Lista archivi
borgmatic rlist          # Borg 2.x syntax
borgmatic list           # Borg 1.x syntax

# Info repository
borgmatic rinfo          # Borg 2.x syntax
borgmatic info           # Borg 1.x syntax

# CONFIGURAZIONE MULTIPLA
# borgmatic può usare più file YAML in /etc/borgmatic.d/
# Ogni file è un profilo di backup indipendente
borgmatic -c /etc/borgmatic.d/servers.yaml create
borgmatic -c /etc/borgmatic.d/databases.yaml create
```

```ini
# /etc/systemd/system/borgmatic.service
[Unit]
Description=borgmatic backup
After=network-online.target
Wants=network-online.target
# Condizione: non eseguire se un altro borgmatic è in corso
ConditionACPower=true

[Service]
Type=oneshot
ExecStart=/usr/local/bin/borgmatic --verbosity -1 --syslog-verbosity 1
# Hardening
Nice=19
IOSchedulingClass=idle
ProtectSystem=full
PrivateTmp=true
NoNewPrivileges=true
LockPersonality=true
```

```ini
# /etc/systemd/system/borgmatic.timer
[Unit]
Description=borgmatic backup timer

[Timer]
OnCalendar=*-*-* 03:00:00
RandomizedDelaySec=30min
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# Abilitare il timer
sudo systemctl enable --now borgmatic.timer
sudo systemctl list-timers --all | grep borgmatic
```

### Monitoring e alerting

```bash
#!/bin/bash
# /usr/local/bin/backup-monitor.sh
# Verifica che i backup siano stati eseguiti nelle ultime N ore

set -euo pipefail

MAILTO="admin@example.com"
ALERT_HOURS=26

check_borg() {
    local repo="$1"
    local name="$2"
    export BORG_PASSPHRASE="$(cat /etc/borg-passphrase)"

    LAST=$(borg list "$repo" --last 1 --format '{time}' 2>/dev/null)
    if [ -z "$LAST" ]; then
        echo "CRITICAL: $name — nessun backup trovato"
        return 2
    fi

    HOURS=$(( ($(date +%s) - $(date -d "$LAST" +%s)) / 3600 ))
    if [ "$HOURS" -gt "$ALERT_HOURS" ]; then
        echo "WARNING: $name — ultimo backup $HOURS ore fa"
        return 1
    fi

    echo "OK: $name — ultimo backup $HOURS ore fa"
    return 0
}

check_restic() {
    local repo="$1"
    local name="$2"
    export RESTIC_PASSWORD_FILE="/etc/restic/password"
    export RESTIC_REPOSITORY="$repo"

    LAST=$(restic snapshots --latest 1 --json 2>/dev/null | \
      python3 -c "import sys,json;s=json.load(sys.stdin);print(s[0]['time'][:19])" 2>/dev/null)
    if [ -z "$LAST" ]; then
        echo "CRITICAL: $name — nessun snapshot trovato"
        return 2
    fi

    HOURS=$(( ($(date +%s) - $(date -d "$LAST" +%s)) / 3600 ))
    if [ "$HOURS" -gt "$ALERT_HOURS" ]; then
        echo "WARNING: $name — ultimo snapshot $HOURS ore fa"
        return 1
    fi

    echo "OK: $name — ultimo snapshot $HOURS ore fa"
    return 0
}

# --- Eseguire i check ---
ERRORS=0
REPORT=""

RESULT=$(check_borg "/backup/borg" "Borg principale") || ERRORS=$((ERRORS+1))
REPORT+="$RESULT\n"

RESULT=$(check_restic "s3:s3.amazonaws.com/backup" "Restic S3") || ERRORS=$((ERRORS+1))
REPORT+="$RESULT\n"

# Verificare spazio disco
DISK_USAGE=$(df /backup --output=pcent | tail -1 | tr -d ' %')
if [ "$DISK_USAGE" -gt 85 ]; then
    REPORT+="WARNING: Disco backup al ${DISK_USAGE}%\n"
    ERRORS=$((ERRORS+1))
fi

# Report
echo -e "$REPORT"
if [ "$ERRORS" -gt 0 ]; then
    echo -e "$REPORT" | mail -s "[BACKUP] $ERRORS problemi rilevati" "$MAILTO"
    exit 1
fi
```

```ini
# Prometheus exporter per metriche backup
# /var/lib/prometheus/node-exporter/backup.prom
# (generato da script cron ogni 15 minuti)

# HELP backup_last_success_timestamp_seconds Timestamp ultimo backup riuscito
# TYPE backup_last_success_timestamp_seconds gauge
backup_last_success_timestamp_seconds{job="borg",host="web1"} 1716336000
backup_last_success_timestamp_seconds{job="restic",host="web1"} 1716336000

# HELP backup_size_bytes Dimensione ultimo backup
# TYPE backup_size_bytes gauge
backup_size_bytes{job="borg",host="web1"} 5368709120

# HELP backup_duration_seconds Durata ultimo backup
# TYPE backup_duration_seconds gauge
backup_duration_seconds{job="borg",host="web1"} 1234
```

---

## Verifica dei Backup

Un backup non verificato è un backup che potenzialmente non esiste. La verifica deve essere automatizzata e regolare.

### Verifiche di integrità

```bash
# BORG — Verifica struttura e dati
borg check /backup/borg-repo                    # Verifica metadati
borg check --verify-data /backup/borg-repo      # Verifica anche contenuto dei chunk

# RESTIC — Verifica con subset per non sovraccaricare
restic check                                     # Struttura e indice
restic check --read-data                         # Legge tutti i dati (lento)
restic check --read-data-subset=5%               # Legge il 5% dei dati

# TAR — Verificare archivio
tar -tzf backup.tar.gz > /dev/null               # Lista: se fallisce, è corrotto
gzip -t backup.tar.gz                            # Test integrità gzip

# DUPLICITY — Verificare backup remoto contro sorgente
duplicity verify s3://bucket/backup/ /srv/data

# CHECKSUM — Verificare integrità file
sha256sum /backup/backup-20260520.tar.gz > /backup/backup-20260520.sha256
sha256sum -c /backup/backup-20260520.sha256      # Verificare
```

### Restore testing automatizzato

```bash
#!/bin/bash
# /usr/local/bin/backup-restore-test.sh
# Eseguire settimanalmente per verificare che i backup siano effettivamente ripristinabili
set -euo pipefail

RESTORE_DIR="/tmp/backup-restore-test-$$"
LOG="/var/log/backup/restore-test-$(date +%Y%m%d).log"
ERRORS=0

exec > >(tee -a "$LOG") 2>&1
trap "rm -rf $RESTORE_DIR" EXIT

mkdir -p "$RESTORE_DIR"
echo "=== Restore test: $(date --iso-8601=seconds) ==="

# --- Test 1: Borg restore file critici ---
echo "Test 1: Borg restore /etc/passwd..."
export BORG_PASSPHRASE="$(cat /etc/borg-passphrase)"
borg extract /backup/borg-repo::$(borg list /backup/borg-repo --last 1 --format '{archive}') \
  etc/passwd --stdout > "$RESTORE_DIR/passwd" 2>/dev/null

if diff -q /etc/passwd "$RESTORE_DIR/passwd" > /dev/null 2>&1; then
    echo "  PASS: /etc/passwd ripristinato correttamente"
else
    echo "  FAIL: /etc/passwd non corrisponde!"
    ERRORS=$((ERRORS+1))
fi

# --- Test 2: Restic restore directory ---
echo "Test 2: Restic restore /etc/nginx/..."
export RESTIC_PASSWORD_FILE="/etc/restic/password"
export RESTIC_REPOSITORY="/backup/restic-repo"
restic restore latest --target "$RESTORE_DIR/restic" --include /etc/nginx 2>/dev/null

if [ -d "$RESTORE_DIR/restic/etc/nginx" ]; then
    FILE_COUNT=$(find "$RESTORE_DIR/restic/etc/nginx" -type f | wc -l)
    echo "  PASS: Nginx config ripristinata ($FILE_COUNT file)"
else
    echo "  FAIL: Directory nginx non trovata nel restore"
    ERRORS=$((ERRORS+1))
fi

# --- Test 3: Database restore ---
echo "Test 3: PostgreSQL dump restore test..."
DUMP_FILE=$(ls -t /backup/pg-dumps/mydb-*.dump 2>/dev/null | head -1)
if [ -n "$DUMP_FILE" ]; then
    # Creare database temporaneo per test
    createdb backup_test_restore 2>/dev/null || true
    if pg_restore -d backup_test_restore "$DUMP_FILE" 2>/dev/null; then
        TABLE_COUNT=$(psql -t -c "SELECT count(*) FROM information_schema.tables \
          WHERE table_schema='public'" backup_test_restore)
        echo "  PASS: Database ripristinato ($TABLE_COUNT tabelle)"
    else
        echo "  FAIL: pg_restore fallito"
        ERRORS=$((ERRORS+1))
    fi
    dropdb backup_test_restore 2>/dev/null || true
fi

# --- Report ---
echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "=== TUTTI I TEST PASSATI ==="
else
    echo "=== $ERRORS TEST FALLITI — INDAGARE IMMEDIATAMENTE ==="
    echo "Risultati" | mail -s "[BACKUP] Restore test: $ERRORS errori" admin@example.com
fi
```

### Verifica Automatizzata Continua

La verifica non deve essere un'operazione manuale occasionale. Deve essere integrata nel ciclo di backup come operazione schedulata con monitoring indipendente.

#### Strategia di check rotativo

```bash
#!/bin/bash
# /usr/local/bin/backup-integrity-check.sh
# Eseguire quotidianamente con cron o systemd timer
set -euo pipefail

LOG="/var/log/backup/integrity-$(date +%Y%m%d).log"
HEALTHCHECK_URL="https://hc-ping.com/xxxxxxxx-check"
DAY_OF_WEEK=$(date +%u)  # 1=Lunedì ... 7=Domenica

exec > >(tee -a "$LOG") 2>&1
echo "=== Integrity check: $(date --iso-8601=seconds) ==="

# --- Borg: check settimanale con verify-data, giornaliero strutturale ---
export BORG_PASSPHRASE="$(cat /etc/borg-passphrase)"
BORG_REPO="/backup/borg"

if [ "$DAY_OF_WEEK" -eq 7 ]; then
    echo "[Borg] Verifica completa con --verify-data"
    borg check --verify-data "$BORG_REPO"
else
    echo "[Borg] Verifica strutturale"
    borg check "$BORG_REPO"
fi

# --- Restic: subset rotativo (1/7 al giorno = 100% in una settimana) ---
export RESTIC_PASSWORD_FILE="/etc/restic/password"
export RESTIC_REPOSITORY="s3:s3.amazonaws.com/backup-bucket"

echo "[Restic] Verifica subset $DAY_OF_WEEK/7"
restic check --read-data-subset="$DAY_OF_WEEK/7"

# --- Verifica hash post-restore per file campione ---
RESTORE_TMP=$(mktemp -d)
trap "rm -rf $RESTORE_TMP" EXIT

# Estrarre un file campione dal backup e confrontare con l'originale
SAMPLE_FILE="/etc/hostname"
restic dump latest "$SAMPLE_FILE" > "$RESTORE_TMP/hostname-restored" 2>/dev/null

if diff -q "$SAMPLE_FILE" "$RESTORE_TMP/hostname-restored" > /dev/null 2>&1; then
    echo "[Restore verify] PASS: $SAMPLE_FILE corrisponde"
else
    echo "[Restore verify] FAIL: $SAMPLE_FILE NON corrisponde!"
    echo "ERRORE restore" | mail -s "[BACKUP] Hash mismatch" admin@example.com
fi

# --- Ping dead man's switch ---
curl -fsS -m 10 --retry 3 "$HEALTHCHECK_URL" > /dev/null 2>&1 || true
echo "=== Check completato: $(date --iso-8601=seconds) ==="
```

#### Metriche Prometheus per backup

```bash
#!/bin/bash
# /usr/local/bin/backup-metrics-exporter.sh
# Genera metriche in formato Prometheus textfile collector
# Schedulare ogni 15 minuti con cron

PROM_FILE="/var/lib/prometheus/node-exporter/backup_status.prom"
TMP_FILE="${PROM_FILE}.tmp"

export BORG_PASSPHRASE="$(cat /etc/borg-passphrase)"
export RESTIC_PASSWORD_FILE="/etc/restic/password"

cat > "$TMP_FILE" << 'HEADER'
# HELP backup_last_success_timestamp Timestamp UTC dell'ultimo backup riuscito
# TYPE backup_last_success_timestamp gauge
# HELP backup_repository_size_bytes Dimensione del repository in byte
# TYPE backup_repository_size_bytes gauge
# HELP backup_archive_count Numero di archivi nel repository
# TYPE backup_archive_count gauge
# HELP backup_check_ok 1 se l'ultimo check è passato, 0 se fallito
# TYPE backup_check_ok gauge
HEADER

# Metriche Borg
BORG_LAST=$(borg list /backup/borg --last 1 --format '{time}' 2>/dev/null)
BORG_EPOCH=$(date -d "$BORG_LAST" +%s 2>/dev/null || echo 0)
BORG_SIZE=$(borg info /backup/borg --json 2>/dev/null | \
  python3 -c "import sys,json;print(json.load(sys.stdin)['cache']['stats']['unique_csize'])" \
  2>/dev/null || echo 0)
BORG_COUNT=$(borg list /backup/borg --format '{archive}{NL}' 2>/dev/null | wc -l)
BORG_CHECK=$(borg check /backup/borg 2>/dev/null && echo 1 || echo 0)

echo "backup_last_success_timestamp{tool=\"borg\",repo=\"locale\"} $BORG_EPOCH" >> "$TMP_FILE"
echo "backup_repository_size_bytes{tool=\"borg\",repo=\"locale\"} $BORG_SIZE" >> "$TMP_FILE"
echo "backup_archive_count{tool=\"borg\",repo=\"locale\"} $BORG_COUNT" >> "$TMP_FILE"
echo "backup_check_ok{tool=\"borg\",repo=\"locale\"} $BORG_CHECK" >> "$TMP_FILE"

# Metriche Restic
export RESTIC_REPOSITORY="s3:s3.amazonaws.com/backup-bucket"
RESTIC_LAST=$(restic snapshots --latest 1 --json 2>/dev/null | \
  python3 -c "import sys,json;s=json.load(sys.stdin);print(s[0]['time'][:19])" 2>/dev/null)
RESTIC_EPOCH=$(date -d "$RESTIC_LAST" +%s 2>/dev/null || echo 0)
RESTIC_COUNT=$(restic snapshots --json 2>/dev/null | \
  python3 -c "import sys,json;print(len(json.load(sys.stdin)))" 2>/dev/null || echo 0)
RESTIC_CHECK=$(restic check 2>/dev/null && echo 1 || echo 0)

echo "backup_last_success_timestamp{tool=\"restic\",repo=\"s3\"} $RESTIC_EPOCH" >> "$TMP_FILE"
echo "backup_archive_count{tool=\"restic\",repo=\"s3\"} $RESTIC_COUNT" >> "$TMP_FILE"
echo "backup_check_ok{tool=\"restic\",repo=\"s3\"} $RESTIC_CHECK" >> "$TMP_FILE"

mv "$TMP_FILE" "$PROM_FILE"
```

```yaml
# Alertmanager rule di esempio per backup scaduto
# /etc/prometheus/rules/backup-alerts.yml
groups:
  - name: backup
    rules:
      - alert: BackupStale
        expr: time() - backup_last_success_timestamp > 93600  # 26 ore
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Backup scaduto per {{ $labels.tool }} su {{ $labels.repo }}"
          description: "L'ultimo backup è più vecchio di 26 ore."

      - alert: BackupCheckFailed
        expr: backup_check_ok == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Verifica integrità fallita per {{ $labels.tool }}"
          description: "borg check o restic check ha riportato errori."

      - alert: BackupDiskFull
        expr: node_filesystem_avail_bytes{mountpoint="/backup"} / node_filesystem_size_bytes{mountpoint="/backup"} < 0.15
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Disco backup sotto il 15% di spazio libero"
```

---

## Sicurezza dei Backup

### Cifratura at rest

```bash
# BORG — Cifratura di default
borg init --encryption=repokey-blake2 /backup/borg    # AES-256-CTR + BLAKE2b HMAC
# La password deve essere complessa (>20 caratteri, generata casualmente)
# Esportare la chiave: borg key export /backup/borg /secure/borg-key.txt

# RESTIC — Cifratura obbligatoria
# Restic cifra SEMPRE con AES-256-CTR + Poly1305.
# La password del repository è la chiave di cifratura.
# Nessuna opzione per disabilitare la cifratura.

# DUPLICITY — Cifratura GPG
# Usa GPG per cifrare ogni volume del backup.
# Chiave asimmetrica (RSA/Ed25519) = più sicuro
# Passphrase simmetrica = più semplice

# RCLONE — Backend crypt
# Cifra nomi file (obfuscation o encryption) e contenuto (XSalsa20 + Poly1305)
rclone config   # Creare backend "crypt" che wrappa un altro backend

# TAR + GPG — Cifratura manuale
tar czf - /srv/data | gpg --symmetric --cipher-algo AES256 \
  --batch --passphrase-file /etc/backup/gpg-pass \
  -o /backup/data-$(date +%Y%m%d).tar.gz.gpg

# Restore
gpg --decrypt --batch --passphrase-file /etc/backup/gpg-pass \
  /backup/data-20260520.tar.gz.gpg | tar xzf - -C /tmp/restore

# TAR + OpenSSL — Alternativa
tar czf - /srv/data | openssl enc -aes-256-cbc -pbkdf2 -iter 100000 \
  -pass file:/etc/backup/ssl-pass -out /backup/data-encrypted.tar.gz.enc

# Restore
openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 \
  -pass file:/etc/backup/ssl-pass \
  -in /backup/data-encrypted.tar.gz.enc | tar xzf - -C /tmp/restore
```

### Cifratura in transito

```bash
# SSH (rsync, borg, restic sftp) — cifrato di default
# S3/GCS/Azure — usare HTTPS (default per tutti i client moderni)
# Rest server — TLS obbligatorio in produzione

# Verificare che rsync usi SSH cifrato
rsync -avz -e "ssh -c aes256-gcm@openssh.com" source/ user@server:/dest/

# Verificare connessione TLS verso S3
# I client AWS, rclone, restic usano HTTPS per default.
# Verificare che non sia stato disabilitato:
# AWS_CLI: --no-verify-ssl NON deve essere usato
# rclone: --no-check-certificate NON deve essere usato
```

### Controllo accessi

```bash
# PRINCIPIO: minimo privilegio per l'utente di backup

# Creare utente dedicato per backup
sudo useradd -r -s /usr/sbin/nologin -d /backup backup-user

# Permessi repository Borg
sudo chown -R backup-user:backup-user /backup/borg
sudo chmod 700 /backup/borg

# SSH con chiave dedicata e restrizioni
# In /home/backup-user/.ssh/authorized_keys:
# command="borg serve --restrict-to-repository /backup/borg --append-only",
#   restrict ssh-ed25519 AAAA... backup@client

# --restrict-to-repository → accesso solo a quel repo
# --append-only → il client può solo aggiungere, non cancellare
# restrict → disabilita port forwarding, X11, ecc.

# Restic rest-server in modalità append-only
rest-server --path /backup/restic --append-only
# I client possono creare snapshot ma NON eseguire forget/prune.
# Il prune deve essere eseguito localmente sul server.

# IMMUTABILITÀ — S3 Object Lock (protezione anti-ransomware)
# Configurare in AWS:
# aws s3api put-object-lock-configuration \
#   --bucket my-backup-bucket \
#   --object-lock-configuration '{
#     "ObjectLockEnabled": "Enabled",
#     "Rule": {"DefaultRetention": {"Mode": "COMPLIANCE", "Days": 30}}
#   }'
# COMPLIANCE mode: nemmeno root/account owner può cancellare prima della scadenza
# GOVERNANCE mode: può essere bypassato con permesso speciale

# SEPARAZIONE CREDENZIALI
# Le credenziali di backup non devono essere le stesse dell'applicazione.
# Un ransomware che compromette l'applicazione non deve poter cancellare i backup.
# Usare account/IAM role separati con permessi minimi.
```

### Backup Immutabili con MinIO e S3 Object Lock

L'immutabilità dei backup è la difesa definitiva contro il ransomware: nemmeno un attaccante con credenziali di amministratore può cancellare o modificare i dati durante il periodo di retention. MinIO implementa S3 Object Lock (WORM — Write Once Read Many) on-premise, permettendo lo stesso livello di protezione di AWS S3 senza dipendere da un provider cloud.

#### Deployment MinIO con Object Lock

```bash
# Installazione MinIO su Linux
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Avvio con Object Lock abilitato (necessario dal primo avvio)
export MINIO_ROOT_USER="minioadmin"
export MINIO_ROOT_PASSWORD="password-sicura-minimo-16-caratteri"
minio server /data/minio --console-address ":9001"
# Object Lock è supportato nativamente — non richiede flag speciali

# Installare il client MinIO (mc)
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc && sudo mv mc /usr/local/bin/

# Configurare alias
mc alias set myminio https://minio.internal:9000 minioadmin password-sicura
```

#### Creare bucket con Object Lock

```bash
# CREARE BUCKET CON OBJECT LOCK
mc mb myminio/backup-immutable --with-lock
# --with-lock abilita versioning + Object Lock sul bucket
# ATTENZIONE: Object Lock può essere abilitato SOLO alla creazione del bucket
# Non è possibile abilitarlo successivamente su un bucket esistente

# IMPOSTARE RETENTION POLICY DEFAULT
mc retention set --default COMPLIANCE 30d myminio/backup-immutable
# Ogni oggetto scritto in questo bucket sarà immutabile per 30 giorni
# COMPLIANCE: nemmeno root/minioadmin può cancellare prima della scadenza
# GOVERNANCE: può essere bypassato da utenti con permesso speciale

# MODALITÀ A CONFRONTO
#
# COMPLIANCE:
#   - Nessuno può cancellare/modificare durante la retention
#   - Nemmeno l'amministratore MinIO
#   - Ideale per: backup anti-ransomware, requisiti normativi
#   - IRREVERSIBILE: una volta impostata, non si può ridurre il periodo
#
# GOVERNANCE:
#   - Gli utenti con s3:BypassGovernanceRetention possono bypassare
#   - Utile per: test, ambienti non regolamentati
#   - Si può rimuovere o ridurre il periodo

# Verificare configurazione
mc retention info myminio/backup-immutable
mc ls myminio/backup-immutable --versions  # Mostra le versioni degli oggetti
```

#### Restic verso MinIO con Object Lock

```bash
# Restic supporta nativamente S3 compatibile → MinIO funziona senza modifiche

export AWS_ACCESS_KEY_ID="backup-user"
export AWS_SECRET_ACCESS_KEY="password-backup-user"
export RESTIC_REPOSITORY="s3:https://minio.internal:9000/backup-immutable"
export RESTIC_PASSWORD_FILE="/etc/restic/password"

# Inizializzare il repository nel bucket con Object Lock
restic init

# Eseguire backup — gli oggetti scritti sono protetti dalla retention
restic backup /etc /home /srv \
  --tag production \
  --exclude-file=/etc/restic/exclude.txt

# ATTENZIONE con prune/forget:
# Se il bucket ha Object Lock in COMPLIANCE mode, restic NON può
# cancellare i pack file prima della scadenza della retention.
# Strategia: impostare la retention Object Lock uguale o inferiore
# alla retention policy di restic.
#
# Esempio: Object Lock 30 giorni, restic --keep-daily=7 --keep-weekly=4
# Dopo il forget+prune, i pack non più referenziati rimangono nel bucket
# per la durata residua dell'Object Lock, poi vengono rimossi
# dalle regole di lifecycle del bucket.
```

#### Borg con storage immutabile

```bash
# Borg non supporta nativamente S3/MinIO, ma la protezione
# si ottiene combinando SSH append-only + storage immutabile.

# Approccio 1: Borg SSH append-only + rsync verso MinIO
# Il client Borg scrive in append-only su un server intermedio.
# Un cron job su quel server sincronizza verso MinIO con mc mirror:

# /usr/local/bin/borg-to-minio.sh
#!/bin/bash
set -euo pipefail
mc mirror --overwrite --remove \
  /backup/borg/ myminio/backup-immutable/borg/
# Gli oggetti su MinIO sono protetti da Object Lock

# Approccio 2: Borg + rclone mount di MinIO
# Meno raccomandato: rclone mount ha limitazioni di performance
# e non è ideale per le operazioni random I/O di Borg
```

#### Policy IAM per utente backup

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::backup-immutable",
        "arn:aws:s3:::backup-immutable/*"
      ]
    },
    {
      "Effect": "Deny",
      "Action": [
        "s3:DeleteObject",
        "s3:DeleteBucket",
        "s3:PutBucketPolicy",
        "s3:PutObjectRetention"
      ],
      "Resource": [
        "arn:aws:s3:::backup-immutable",
        "arn:aws:s3:::backup-immutable/*"
      ]
    }
  ]
}
```

```bash
# Creare la policy su MinIO
mc admin policy create myminio backup-write-only /tmp/backup-policy.json

# Creare utente con la policy
mc admin user add myminio backup-agent "password-agente"
mc admin policy attach myminio backup-write-only --user backup-agent

# L'utente backup-agent può scrivere e leggere, ma NON cancellare.
# Object Lock aggiunge un secondo livello: anche se le credenziali
# dell'utente admin vengono compromesse, i dati rimangono immutabili
# durante il periodo di retention COMPLIANCE.
```

#### Verifica stato immutabilità

```bash
# Verificare che Object Lock sia attivo
mc retention info myminio/backup-immutable

# Verificare retention su un oggetto specifico
mc retention info myminio/backup-immutable/data/abc123/config

# Tentare cancellazione (deve fallire con errore)
mc rm myminio/backup-immutable/data/abc123/config
# Errore atteso: Object locked, cannot be deleted

# Verificare versioning (Object Lock richiede versioning abilitato)
mc version info myminio/backup-immutable
# Output: "myminio/backup-immutable versioning is enabled"
```

---

## Disaster Recovery Planning

### Documentazione del piano DR

Un piano di disaster recovery deve rispondere a queste domande:

```
1. COSA proteggiamo? (inventario asset e dati)
2. DA COSA proteggiamo? (scenari di rischio)
3. COME recuperiamo? (procedure passo-passo)
4. CHI è responsabile? (ruoli e contatti)
5. QUANTO velocemente? (RTO/RPO per ogni servizio)
6. DOVE recuperiamo? (sito alternativo, cloud, bare metal)
```

### Template Runbook DR

```markdown
# Runbook: Disaster Recovery — [Nome Servizio]
# Versione: 1.0 | Ultima revisione: 2026-05-22 | Owner: Team Ops

## Informazioni Servizio
- Servizio: web app di produzione
- RTO: 4 ore | RPO: 1 ora
- Criticità: ALTA
- Dipendenze: PostgreSQL, Redis, NFS storage

## Contatti
- On-call primario: +39 xxx | nome@example.com
- On-call secondario: +39 xxx
- Escalation: CTO +39 xxx

## Procedure di Recovery

### Scenario 1: Guasto singolo server
1. Provisioning nuovo server (Ansible playbook: deploy-web.yml)
2. Restore configurazione: borg extract borg-repo::latest etc/
3. Restore dati applicazione: borg extract borg-repo::latest srv/
4. Restore database: pg_restore da ultimo dump
5. Aggiornare DNS / load balancer
6. Verificare funzionalità
7. Tempo stimato: 2 ore

### Scenario 2: Guasto datacenter
1. Attivare infrastruttura DR nel sito secondario
2. Restore da backup offsite (S3/restic)
3. Verificare replica database (streaming replication)
4. Switch DNS
5. Tempo stimato: 4 ore

### Scenario 3: Ransomware
1. ISOLARE immediatamente i sistemi compromessi (scollegare dalla rete)
2. Identificare il vettore di attacco
3. Verificare integrità backup (sono stati compromessi?)
4. Restore da copia air-gapped/immutabile
5. Cambiare TUTTE le credenziali
6. Tempo stimato: 8-24 ore

## Checklist Post-Recovery
- [ ] Tutti i servizi rispondono
- [ ] Dati integri (count tabelle, checksum file critici)
- [ ] Monitoring attivo
- [ ] Backup ripresi normalmente
- [ ] Incident report scritto entro 48 ore
```

### Testing del piano DR

```bash
# DRILL TRIMESTRALE (minimo)
# 1. Scegliere uno scenario dal runbook
# 2. Simulare su ambiente di test
# 3. Cronometrare le operazioni
# 4. Documentare problemi e deviazioni
# 5. Aggiornare il runbook

# TABLETOP EXERCISE (simulazione senza toccare i sistemi)
# Riunione: "È successo X. Cosa facciamo?"
# Ogni partecipante descrive le proprie azioni.
# Identificare gap nel processo.

# RESTORE DRILL AUTOMATIZZATO (mensile)
# Vedi sezione "Verifica dei Backup" → script di restore test
```

---

## Bare Metal Recovery

Il bare metal recovery ricostruisce un sistema completo partendo da hardware vuoto.

### Processo completo

```
1. PREPARAZIONE (PRIMA del disastro)
   a. Documentare: layout dischi, partizioni, LVM, RAID, bootloader
   b. Salvare: /etc/fstab, lsblk output, pvs/vgs/lvs, fdisk -l
   c. Backup: MBR/GPT, configurazione bootloader, initramfs
   d. Testare: almeno un restore completo su hardware di test

2. RECOVERY (DOPO il disastro)
   a. Avviare da media di recovery (USB Clonezilla, rescue ISO)
   b. Ricreare layout dischi (partizioni, RAID, LVM)
   c. Restore filesystem da backup
   d. Reinstallare bootloader
   e. Verificare e riavviare
```

### Documentazione pre-disastro

```bash
#!/bin/bash
# /usr/local/bin/save-system-info.sh
# Eseguire periodicamente per salvare info critiche per bare metal recovery

OUT="/backup/system-info/$(hostname)"
mkdir -p "$OUT"

# Layout dischi
lsblk -f > "$OUT/lsblk.txt"
fdisk -l > "$OUT/fdisk.txt" 2>/dev/null
blkid > "$OUT/blkid.txt"
cat /etc/fstab > "$OUT/fstab.txt"

# LVM (se presente)
pvs > "$OUT/pvs.txt" 2>/dev/null
vgs > "$OUT/vgs.txt" 2>/dev/null
lvs > "$OUT/lvs.txt" 2>/dev/null
vgcfgbackup -f "$OUT/vg-backup-%s" 2>/dev/null

# RAID (se presente)
cat /proc/mdstat > "$OUT/mdstat.txt" 2>/dev/null
mdadm --detail --scan > "$OUT/mdadm.txt" 2>/dev/null

# Bootloader
cp /etc/default/grub "$OUT/grub-default.txt" 2>/dev/null

# Network
ip addr > "$OUT/ip-addr.txt"
ip route > "$OUT/ip-route.txt"
cat /etc/hostname > "$OUT/hostname.txt"
cp /etc/hosts "$OUT/hosts.txt"
cp -r /etc/netplan "$OUT/netplan/" 2>/dev/null
cp -r /etc/sysconfig/network-scripts "$OUT/network-scripts/" 2>/dev/null

# Pacchetti installati
dpkg --get-selections > "$OUT/dpkg-selections.txt" 2>/dev/null
rpm -qa > "$OUT/rpm-list.txt" 2>/dev/null

# Backup MBR (primi 512 byte) — solo per dischi MBR
dd if=/dev/sda of="$OUT/mbr-sda.bin" bs=512 count=1 2>/dev/null

# Backup tabella partizioni GPT
sgdisk --backup="$OUT/gpt-sda.bin" /dev/sda 2>/dev/null

# Kernel e moduli
uname -a > "$OUT/uname.txt"
lsmod > "$OUT/lsmod.txt"

echo "Informazioni sistema salvate in $OUT"
```

### Recovery step-by-step

```bash
# 1. AVVIARE DA MEDIA DI RECOVERY
# USB con distribuzione live (es. Ubuntu Server, SystemRescue)

# 2. RICREARE LAYOUT DISCHI (consultare documenti salvati)
# Esempio: disco con GPT, partizione EFI, LVM per root e home

parted /dev/sda mklabel gpt
parted /dev/sda mkpart primary fat32 1MiB 513MiB    # EFI
parted /dev/sda set 1 esp on
parted /dev/sda mkpart primary ext4 513MiB 1537MiB  # /boot
parted /dev/sda mkpart primary 1537MiB 100%          # LVM

# LVM
pvcreate /dev/sda3
vgcreate vg0 /dev/sda3
lvcreate -L 30G -n root vg0
lvcreate -L 50G -n home vg0
lvcreate -L 8G -n swap vg0

# Formattare
mkfs.fat -F32 /dev/sda1
mkfs.ext4 /dev/sda2
mkfs.ext4 /dev/vg0/root
mkfs.ext4 /dev/vg0/home
mkswap /dev/vg0/swap

# 3. MONTARE E RESTORE
mount /dev/vg0/root /mnt
mkdir -p /mnt/boot /mnt/home /mnt/boot/efi
mount /dev/sda2 /mnt/boot
mount /dev/sda1 /mnt/boot/efi
mount /dev/vg0/home /mnt/home

# Restore da Borg
export BORG_PASSPHRASE="password"
cd /mnt && borg extract /backup/borg-repo::ultimo-backup

# 4. REINSTALLARE BOOTLOADER
# chroot nel sistema ripristinato
mount --bind /dev /mnt/dev
mount --bind /proc /mnt/proc
mount --bind /sys /mnt/sys
chroot /mnt

# Dentro chroot:
grub-install /dev/sda          # BIOS/MBR
# oppure
grub-install --target=x86_64-efi --efi-directory=/boot/efi  # UEFI
update-grub

# Rigenerare initramfs
update-initramfs -u -k all     # Debian/Ubuntu
dracut --regenerate-all --force  # RHEL/Fedora

exit  # uscire da chroot

# 5. SMONTARE E RIAVVIARE
umount -R /mnt
reboot

# 6. POST-RECOVERY
# Verificare che tutti i servizi partano
# Verificare rete, DNS, NTP
# Verificare che i backup ripartano
# Aggiornare documentazione se qualcosa è cambiato
```

---

## Matrice Decisionale

### Confronto strumenti per caso d'uso

| Criterio | rsync | BorgBackup | Restic | Duplicity | tar | rclone |
|---|---|---|---|---|---|---|
| Deduplicazione | No | Sì (chunk) | Sì (chunk) | No | No | No |
| Cifratura | No (solo SSH) | Sì (AES-256) | Sì (AES-256) | Sì (GPG) | No (+ GPG) | Sì (XSalsa20) |
| Cloud nativo | No | No (solo SSH) | Sì (S3, B2, GCS, Azure) | Sì (S3, GCS, SFTP) | No | Sì (40+ backend) |
| Compressione | Trasferimento | lz4/zstd/zlib/lzma | No | gzip | gzip/bzip2/xz/zstd | No |
| Velocità backup | Veloce | Medio | Medio | Lento | Lento (full) | Veloce |
| Velocità restore | Veloce | Medio | Medio | Lento | Veloce | Veloce |
| Complessità | Bassa | Media | Bassa | Media | Bassa | Media |
| Restore singolo file | Sì | Sì (mount FUSE) | Sì (mount FUSE) | Sì | Sì | Sì |
| Immutabilità append-only | No | Sì | Sì (rest-server) | No | No | No |

### Quando usare cosa

| Scenario | Strumento raccomandato | Motivazione |
|---|---|---|
| Sync tra server (no history) | rsync | Semplice, veloce, nessun overhead |
| Backup server con retention | BorgBackup | Dedup eccellente, compressione, locale/SSH |
| Backup verso cloud | Restic | Backend multipli, dedup, setup semplice |
| Backup cifrato verso S3 legacy | Duplicity | GPG maturo, full + incrementali |
| Archivio singolo, distribuzione | tar + zstd | Universale, nessuna dipendenza |
| Sync dati verso cloud (no dedup) | rclone | 40+ backend, cifratura opzionale |
| Clone disco / bare metal | Clonezilla / partclone | Veloce, block-level |
| Database PostgreSQL PITR | pg_basebackup + WAL | Recovery point-in-time preciso |
| Database MySQL con downtime zero | XtraBackup | Hot backup InnoDB |
| Snapshot istantaneo (ZFS) | zfs send/receive | Nativo, incrementale, velocissimo |

### Costo storage comparativo

```
Esempio: 500GB di dati, 5% modifica giornaliera, retention 30 giorni

rsync (--link-dest):
  500GB base + 30 × 25GB delta = 1.25TB
  (hard link → spazio effettivo ~575GB se pochi file cambiano)

BorgBackup:
  500GB deduplicato → ~50-80GB repository tipico
  (dedup chunk-level: rapporto 10:1 o migliore)

Restic:
  Simile a Borg: ~50-80GB

tar full + incrementali:
  500GB full + 30 × 25GB incrementali = 1.25TB
  (nessuna dedup, ogni full è indipendente)

Duplicity:
  500GB full cifrato + incrementali → ~550-700GB
  (volumi GPG, overhead cifratura)
```

---

## Best Practices

1. **3-2-1 come minimo**: 3 copie, 2 supporti, 1 offsite. Per dati critici: 3-2-1-1-0 (+ 1 copia air-gapped + 0 errori verificati)
2. **Testare il restore regolarmente**: un backup mai testato è un backup che non esiste. Almeno trimestralmente, fare un restore completo su un sistema di test
3. **Crittografare i backup**: specialmente quelli offsite e cloud. BorgBackup e Restic criptano di default
4. **Deduplicazione**: usare BorgBackup o Restic per risparmiare spazio. La deduplicazione a livello di blocco riduce lo storage del 70-90%
5. **Monitorare i backup**: alert se un backup non viene eseguito o fallisce. Un backup silenziosamente fallito per settimane è un disastro
6. **Retention policy chiara**: definire per quanto tempo mantenere ogni tipo di backup. Automatizzare la pulizia con prune/forget
7. **Snapshot ≠ backup**: gli snapshot proteggono da errori e permettono rollback rapido, ma sono sullo stesso disco. Un guasto al disco perde sia i dati che gli snapshot
8. **Separare le credenziali**: l'utente/ruolo che esegue i backup deve avere permessi minimi. Il ransomware che compromette l'app non deve poter cancellare i backup
9. **Documentare il processo di recovery**: un backup senza runbook di restore è pericoloso — sotto stress, gli errori manuali sono frequenti
10. **Backup delle chiavi di cifratura**: se perdi la chiave GPG o la password del repository Borg/Restic, i backup sono irrecuperabili. Conservare le chiavi in almeno 2 posti separati e sicuri
11. **Append-only dove possibile**: configurare Borg con `--append-only` via SSH e Restic con rest-server `--append-only` per proteggere i backup dalla cancellazione
12. **Verificare dopo ogni modifica**: se cambi script, retention policy, o destinazione, verificare immediatamente che il backup funzioni e che il restore sia possibile
13. **Non backuppare il rumore**: escludere cache, temporanei, log rotati, build artifact. Riduce tempo, spazio e costi
14. **Versionare gli script di backup**: gli script di backup sono infrastruttura critica — devono essere sotto version control
15. **Pianificare la capacità**: monitorare la crescita del repository e proiettare quando lo storage sarà pieno

---

## Troubleshooting

**"Backup troppo lento"** → `rsync --bwlimit` per non saturare la rete. Verificare: I/O del disco sorgente (`iostat`), rete (`iperf3`), compressione (usare `zstd` che è veloce). Per la prima esecuzione: considerare backup iniziale via disco fisico per grandi dataset.

**"Spazio backup esaurito"** → `borg prune` o `restic forget --prune` per applicare la retention policy. Verificare che il prune sia automatizzato. Per BorgBackup: `borg compact` dopo prune per liberare effettivamente lo spazio.

**"Restore fallisce"** → Per BorgBackup: `borg check --verify-data` per verificare integrità. Per rsync: verificare che i permessi dell'utente permettano la scrittura nella destinazione. Per tar: file corrotto? `tar -tzf file.tar.gz` per verificare.

**"rsync: permission denied"** → L'utente non ha permessi sulla destinazione. Per backup come root via SSH: configurare SSH con chiave per root (o usare `--rsync-path="sudo rsync"` se l'utente remoto ha sudo).

**"borg: Repository already locked"** → Un backup precedente è stato interrotto. Verificare che non ci siano processi borg attivi (`pgrep borg`), poi: `borg break-lock /backup/borg-repo`. Non usare break-lock se un backup è effettivamente in corso.

**"restic: unable to open config file"** → Il repository non esiste o le credenziali sono errate. Verificare: `RESTIC_REPOSITORY`, `RESTIC_PASSWORD_FILE`, credenziali cloud (`AWS_ACCESS_KEY_ID`, ecc.). Testare con `restic snapshots`.

**"rsync: connection unexpectedly closed"** → Problemi di rete o timeout SSH. Soluzioni: `--timeout=300`, usare `screen`/`tmux` per sessioni lunghe, `-P` per riprendere trasferimenti interrotti. Verificare log SSH sul server (`/var/log/auth.log`).

**"borg: Data integrity error"** → Chunk corrotto nel repository. Prima: `borg check --verify-data` per identificare il problema. Se riparabile: `borg check --repair` (ultimo resort, può perdere dati). Se non riparabile: restore dall'ultimo backup integro e ricostruire il repository.

**"Backup incrementale diventa un full"** → Per tar: il file `.snar` è stato perso o corrotto. Ricrearlo significa ripartire da un full. Per rsync con `--link-dest`: la directory `latest` non esiste o il symlink è rotto. Verificare il link con `readlink -f /backup/latest`.

**"Duplicity: GnuPG error"** → La chiave GPG non è nel keyring. Importare con `gpg --import key.asc`. Verificare che la passphrase sia corretta. Se la chiave è scaduta: `gpg --edit-key KEY_ID` → `expire` → impostare nuova scadenza.

**"restic: pack ID does not match"** → Indice corrotto o file di pack danneggiato. Eseguire `restic repair index` per ricostruire l'indice. Se il problema persiste: `restic check --read-data` per identificare pack corrotti.

**"rclone: too many requests"** → Rate limiting dal provider cloud. Ridurre i trasferimenti paralleli: `--transfers 2 --checkers 4`. Per Backblaze B2: aggiungere `--b2-hard-delete=false`. Per Google Drive: `--drive-pacer-min-sleep 100ms`.

**"Backup database inconsistente"** → Il backup è stato eseguito durante scritture. Soluzioni: `pg_dump --single-transaction` per PostgreSQL, `mysqldump --single-transaction` per MySQL/InnoDB, o usare snapshot LVM prima del backup.

**"LVM snapshot pieno e invalido"** → Lo snapshot ha esaurito lo spazio allocato per le modifiche. Il volume originale continua a funzionare, ma lo snapshot è perso. Soluzioni: allocare più spazio (`-L 10G` invece di `5G`), ridurre il tempo di backup, usare `lvs` per monitorare `snap_percent`.

**"Restore su disco più piccolo"** → `dd` non permette restore su disco più piccolo. Usare `partclone` che copia solo i blocchi usati. Alternativa: restore su disco uguale/più grande, poi ridurre la partizione con `resize2fs` (ext4) o equivalente.

**"Backup via SSH lentissimo"** → La cifratura SSH ha overhead. Soluzioni: usare cifratura veloce (`-c aes128-gcm@openssh.com`), disabilitare compressione SSH se rsync comprime già (`-o Compression=no`), verificare che la CPU non sia il collo di bottiglia (`htop`).

**"Errore: No space left on device durante restore"** → Lo spazio su disco non è sufficiente per il restore completo. Verificare con `df -h`. Se necessario: restore parziale (solo i file critici), montare storage aggiuntivo, o pulire file non necessari.

**"borg compact non libera spazio"** → `compact` libera spazio solo dopo `prune`. Verificare che `prune` sia stato eseguito e che ci siano archivi marcati per la cancellazione. Usare `borg list` per verificare gli archivi rimasti.

**"Cron non esegue il backup"** → Verificare: il cron daemon è attivo (`systemctl status cron`), il file crontab è sintatticamente corretto (`crontab -l`), lo script ha permessi di esecuzione, le variabili d'ambiente necessarie sono definite nello script (cron ha un ambiente minimale, non carica `.bashrc`).

**"Restic backup molto lento su S3"** → Cause: latenza di rete, troppi small file (overhead per-file su S3), chunk size non ottimale. Soluzioni: `--pack-size 64` per ridurre il numero di pack, `--read-concurrency 4`, verificare che il bucket S3 sia nella stessa regione del server.

**"Permission denied dopo restore"** → UID/GID del sistema di restore non corrispondono a quelli del backup. Soluzioni: `rsync --numeric-ids` durante il backup, oppure `chown -R` dopo il restore, oppure verificare `/etc/passwd` e `/etc/group` corrispondano.

---

## FAQ

**D: Quanto spesso devo fare il backup?**
R: Dipende dall'RPO. Regola pratica: dati che cambiano spesso → backup orario o più frequente. Configurazioni → giornaliero. Archivi statici → settimanale. Database di produzione → almeno orario + WAL archiving continuo.

**D: Borg o Restic? Quale scegliere?**
R: BorgBackup: se il target è locale o SSH, se serve compressione integrata, se vuoi il massimo controllo. Restic: se il target è cloud (S3, B2, Azure, GCS), se vuoi setup più semplice, se servono backend multipli. Entrambi offrono dedup e cifratura eccellenti.

**D: rsync è sufficiente come sistema di backup?**
R: rsync è uno strumento di sincronizzazione, non un sistema di backup completo. Con `--link-dest` può funzionare come backup incrementale, ma non offre deduplicazione a livello di blocco, cifratura, o gestione della retention come Borg/Restic. Per uso personale semplice è adeguato; per produzione, preferire Borg o Restic.

**D: Come proteggo i backup dal ransomware?**
R: Tre livelli: (1) Copia air-gapped (disco offline, nastro LTO); (2) Append-only su server di backup (Borg `--append-only`, Restic rest-server `--append-only`); (3) Object Lock su S3 (WORM). Le credenziali di backup devono essere separate da quelle dell'applicazione.

**D: Posso usare gli snapshot (LVM/ZFS/Btrfs) come unico backup?**
R: No. Gli snapshot risiedono sullo stesso storage dei dati originali. Un guasto al disco, al controller RAID, o un ransomware che compromette il sistema perde sia i dati che gli snapshot. Gli snapshot sono utili per recovery rapido da errori umani, ma servono backup offsite per protezione completa.

**D: Come faccio backup di container Docker?**
R: (1) Volumi Docker: backuppare la directory dei volumi (`/var/lib/docker/volumes/`). (2) Database in container: `docker exec` + `pg_dump` / `mysqldump`. (3) Configurazione: è nel Dockerfile e docker-compose.yml (version control). (4) Immagini: `docker save` oppure push su registry. Non backuppare il layer filesystem del container — è effimero.

**D: Quanto spazio devo prevedere per i backup?**
R: Regola empirica senza dedup: 3-5x la dimensione dei dati originali (per mantenere 30 giorni di retention con backup giornalieri). Con dedup (Borg/Restic): 1.5-2x i dati originali per 30 giorni tipici, grazie a rapporti di dedup 10:1 o migliori.

**D: Come verifico che un backup sia davvero funzionante?**
R: (1) Check integrità automatico (`borg check`, `restic check`); (2) Restore test automatizzato settimanale su ambiente di test; (3) Restore drill completo trimestrale con cronometro. Se non testi il restore, il backup è solo una speranza.

**D: Devo cifrare i backup anche su storage locale?**
R: Sì, se i backup contengono dati sensibili (PII, credenziali, dati finanziari). Un disco rubato o un accesso non autorizzato al server di backup espone tutti i dati. Con Borg e Restic la cifratura è a costo zero in termini di complessità.

**D: Come gestisco il backup di un database molto grande (>1TB)?**
R: pg_basebackup + WAL archiving per PostgreSQL (backup fisico incrementale). XtraBackup per MySQL. Evitare pg_dump/mysqldump per database grandi (troppo lento, lock potenziali). Considerare replica di lettura dedicata al backup per non impattare la produzione.

**D: Cosa succede se perdo la password del repository Borg/Restic?**
R: I dati sono irrecuperabili. Non esiste "reset password" — la password È la chiave di cifratura. Soluzioni preventive: (1) Salvare la password in un password manager; (2) Esportare la chiave Borg (`borg key export`) e conservarla separatamente; (3) Conservare una copia cartacea in cassaforte.

**D: Meglio systemd timer o cron per schedulare i backup?**
R: Systemd timer: logging integrato nel journal, gestione dipendenze (After=network.target), `Persistent=true` per esecuzione recuperata dopo downtime, controllo risorse (Nice, IOSchedulingClass). Cron: più semplice, universale, non richiede file .service separato. Per sistemi moderni con systemd, i timer sono preferibili.

**D: Come riduco il tempo della prima esecuzione di Borg/Restic?**
R: La prima esecuzione è sempre un full — non c'è modo di evitarlo. Strategie: (1) Escludere dati non necessari; (2) Usare compressione veloce (lz4 o zstd livello 1); (3) Per backup remoto su rete lenta: fare il primo backup su disco locale, copiare il repository via disco fisico, poi continuare gli incrementali via rete.

**D: Posso usare rclone come unico sistema di backup?**
R: rclone è un tool di sincronizzazione, non di backup. Non offre versioning, dedup, o restore point-in-time. Può essere usato come TRASPORTO per copiare i backup (di Borg, Restic, tar) verso il cloud, o come sync per dati dove serve solo una copia aggiornata. Per backup vero: Borg/Restic + rclone per il trasporto.

**D: Come gestisco backup di file molto grandi che cambiano spesso (VM, database file)?**
R: (1) Borg/Restic con dedup a livello di chunk: solo i blocchi modificati vengono salvati; (2) LVM/ZFS snapshot prima del backup per consistenza; (3) Per VM: backup a livello di hypervisor (Proxmox vzdump, libvirt snapshot) che usa snapshot e changed block tracking; (4) Per database: sempre backup logico o fisico dedicato, mai backup del file raw in uso.

**D: Esiste un modo per testare la velocità di restore prima di un'emergenza?**
R: Sì: (1) `borg extract --dry-run` simula il restore senza scrivere nulla — misura il throughput di lettura dal repository; (2) Restore parziale su `/tmp` e cronometrare; (3) `restic stats` mostra dimensioni per stimare i tempi; (4) Pianificare un restore drill completo almeno una volta e misurare il tempo reale — è l'unico dato affidabile.
