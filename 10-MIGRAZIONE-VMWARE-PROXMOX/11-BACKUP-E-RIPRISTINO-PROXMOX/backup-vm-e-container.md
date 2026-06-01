# Backup di VM e Container in Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 5 — Operativita post-migrazione · Modulo 11.1 (apre la sezione backup, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 02 (architettura Proxmox); modulo 03 (storage backend); modulo 10.1 (HA Manager — interazioni con backup); concetti generali di RTO/RPO, 3-2-1 backup rule, immutability/WORM.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. configurare backup di VM e container con `vzdump` (modalita `snapshot`, `suspend`, `stop`) e comprenderne le implicazioni su consistenza e downtime;
> 2. progettare una **strategia di backup** (locazione, retention, schedulazione, classi di criticita) basata su RTO/RPO definiti per workload;
> 3. configurare hook script (`/etc/vzdump-hook.sh`) per quiesce di database (PostgreSQL `pg_start_backup` / `pg_stop_backup`, MySQL `FLUSH TABLES WITH READ LOCK`, applicazioni custom);
> 4. usare il QEMU Guest Agent (`qm set --agent enabled=1`) per coerenza filesystem (`fsfreeze`/`fsthaw`) durante backup live;
> 5. impostare retention policy e gestione spazio (storage di destinazione, alert su occupazione, cleanup automatico);
> 6. implementare la regola 3-2-1-1-0 (3 copie, 2 supporti diversi, 1 offsite, 1 immutabile, 0 errori in test restore);
> 7. testare i restore mensilmente (drill di disaster recovery), misurando RTO effettivo vs target.
> **Tempo stimato:** lettura 60-90 min · lab 240 min (configurare backup + restore drill end-to-end)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; vzdump (incluso in pve-manager); QEMU Guest Agent 9.x.

## Mappa concettuale

```
+============================================================+
|     Backup Proxmox: modalita e flusso                       |
+============================================================+
|                                                            |
|   MODALITA vzdump                                          |
|                                                            |
|   snapshot   live, no downtime, snapshot LVM/qcow2/ZFS     |
|              richiede storage che supporta snapshot        |
|              consistenza filesystem via fsfreeze (qga)     |
|                                                            |
|   suspend    pause della VM brevemente per dump            |
|              fallback se snapshot non possibile            |
|              downtime di pochi secondi                     |
|                                                            |
|   stop       stop completo della VM, dump, riavvio         |
|              downtime = durata del dump (puo essere ore!)  |
|              ultima risorsa, solo per scenari controllati  |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   PIPELINE BACKUP                                          |
|                                                            |
|   1. vzdump invoca pre-script (se hook configurato)        |
|      → quiesce DB / app                                    |
|   2. snapshot del disco (snapshot mode)                    |
|      → coerenza crash-consistent o app-consistent (qga)    |
|   3. dump del snapshot a destinazione                      |
|      → vma format (default) o pbs (se PBS storage)         |
|      → compressione: zstd (default), gzip, lzo, none       |
|      → optional: bandwidth limit                           |
|   4. cleanup snapshot                                      |
|   5. invoca post-script (se hook configurato)              |
|      → restore stato app (es. pg_stop_backup)              |
|   6. retention policy: rimuovi backup vecchi               |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   3-2-1-1-0 RULE                                           |
|                                                            |
|   3 copie     primary + 2 backup (es. PBS local + offsite) |
|   2 supporti  disco + tape, o disco locale + cloud         |
|   1 offsite   geographically separato (incendio/disastro)  |
|   1 immutabile WORM, S3 Object Lock, tape WORM             |
|   0 errori    test restore periodici, 0 fallimenti         |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Backup non testato = niente backup.** "Abbiamo backup" senza test di restore documentati = falsa sicurezza. Mensile mandatory: prendi un backup random, restore su VM throwaway, valida che si avvii e funzioni.
2. **RTO e RPO sono numeri, non aspirazioni.** RTO = "in quanto tempo la VM e di nuovo up dopo un disastro?". RPO = "quanto recente deve essere il backup utilizzato?". Definire prima, poi adattare la strategia: backup orari = RPO 1h, backup giornalieri = RPO 24h.
3. **Modalita `snapshot` con qemu-guest-agent e lo standard.** Per VM Linux/Windows con qga installato: `vzdump --mode snapshot` produce backup application-consistent (filesystem freeze, niente "dirty FS" al restore). Senza qga: solo crash-consistent (come power loss).
4. **Hook script per database = obbligatorio per RPO basso.** Senza hook, un dump di un DB attivo cattura WAL/binlog parziali → restore richiede recovery che puo fallire. Con hook (`pg_start_backup` o `--single-transaction`), backup e application-consistent al 100%.
5. **Retention senza pianificazione fa esplodere lo storage.** "Tieni tutto" = TB/mese in piu. Definire retention per criticita: critici (giornaliero per 30 giorni + settimanale per 12 settimane + mensile per 12 mesi); standard (giornaliero per 14 giorni + settimanale per 4 settimane); test/dev (giornaliero per 7 giorni).

---

## Indice

1. [Introduzione a vzdump](#introduzione-a-vzdump)
2. [Modalita di Backup: Snapshot, Suspend, Stop](#modalita-di-backup-snapshot-suspend-stop)
3. [Compressione: zstd, lz4, gzip](#compressione-zstd-lz4-gzip)
4. [Limiti di Banda e Risorse](#limiti-di-banda-e-risorse)
5. [Esclusione Path e Pattern](#esclusione-path-e-pattern)
6. [Hook Scripts: Pre e Post Backup](#hook-scripts-pre-e-post-backup)
7. [Scheduling via GUI e Cron](#scheduling-via-gui-e-cron)
8. [Selezione dello Storage di Backup](#selezione-dello-storage-di-backup)
9. [Monitoraggio dei Job di Backup](#monitoraggio-dei-job-di-backup)
10. [Notifiche Email](#notifiche-email)
11. [Backup di Container LXC](#backup-di-container-lxc)
12. [Scenari Operativi e Best Practices](#scenari-operativi-e-best-practices)

---

## Introduzione a vzdump

`vzdump` e lo strumento nativo di Proxmox VE per la creazione di backup di macchine virtuali KVM e container LXC. E integrato direttamente nel sistema e puo inviare i backup a diversi tipi di storage, incluso Proxmox Backup Server (PBS).

### Sintassi Base

```bash
vzdump <vmid> [opzioni]

# Esempi base:
vzdump 100                            # Backup VM 100, storage e modo default
vzdump 100 101 102                    # Backup multiplo
vzdump --all                           # Backup di tutte le VM e CT del nodo
vzdump --all --exclude 105,110         # Tutte tranne 105 e 110
vzdump --pool production               # Tutte le VM del pool "production"
```

### Formato dei File di Backup

| Storage Target | Formato File | Estensione | Descrizione |
|---------------|-------------|-----------|-------------|
| PBS | Chunk-based | .pxar.didx, .img.fidx | Deduplicato, incrementale |
| Directory/NFS | Archivio compresso | .vma.zst, .vma.gz, .vma.lzo | File singolo per backup |
| Directory (CT) | Archivio tar | .tar.zst, .tar.gz | Archivio container |

### Flusso di Esecuzione vzdump

```
vzdump avviato
      |
      v
[Pre-freeze hooks / QEMU guest agent freeze]
      |
      v
[Creazione snapshot disco (in-memory bitmap)]
      |
      v
[Pre-backup hooks eseguiti]
      |
      v
[Lettura dati dallo snapshot]
      |
      v
[Compressione (zstd/lz4/gzip)]
      |
      v
[Invio a storage target (PBS/NFS/locale)]
      |
      v
[Rimozione snapshot temporaneo]
      |
      v
[Post-backup hooks eseguiti]
      |
      v
[Notifica email (se configurata)]
      |
      v
vzdump completato
```

---

## Modalita di Backup: Snapshot, Suspend, Stop

### Modalita Snapshot (Raccomandata)

La modalita snapshot e la scelta predefinita e raccomandata per la maggior parte degli scenari. Utilizza il meccanismo di snapshot live di QEMU per creare una copia consistente del disco senza interrompere la VM.

```bash
# Backup in modalita snapshot
vzdump 100 --mode snapshot --storage pbs-store --compress zstd

# Con QEMU Guest Agent per consistenza filesystem
vzdump 100 --mode snapshot --storage pbs-store --compress zstd
# Il guest agent esegue automaticamente fs-freeze/fs-thaw
```

**Requisiti per la modalita snapshot:**

- QEMU Guest Agent installato e attivo nella VM (raccomandato)
- Storage che supporta snapshot (tutti i tipi in Proxmox)

```bash
# Verificare che il QEMU Guest Agent sia attivo nella VM
qm agent 100 ping

# Se non risponde, installare nella VM:
# Debian/Ubuntu:
#   apt install qemu-guest-agent
#   systemctl enable --now qemu-guest-agent
#
# RHEL/CentOS:
#   yum install qemu-guest-agent
#   systemctl enable --now qemu-guest-agent
#
# Windows:
#   Installare VirtIO Guest Tools (include il QEMU Guest Agent)
```

### Modalita Suspend

La modalita suspend sospende brevemente la VM in RAM durante la creazione dello snapshot. Garantisce consistenza del filesystem ma causa un breve downtime.

```bash
# Backup in modalita suspend
vzdump 100 --mode suspend --storage pbs-store --compress zstd
```

| Caratteristica | Dettaglio |
|---------------|----------|
| Downtime | Breve (secondi, proporzionale alla RAM) |
| Consistenza | Garantita (VM sospesa) |
| Caso d'uso | VM senza guest agent, applicazioni sensibili |
| Impatto | Connessioni di rete possono cadere |

### Modalita Stop

La modalita stop spegne completamente la VM, esegue il backup, e la riavvia. Garantisce la massima consistenza ma causa il downtime maggiore.

```bash
# Backup in modalita stop
vzdump 100 --mode stop --storage pbs-store --compress zstd
```

| Caratteristica | Dettaglio |
|---------------|----------|
| Downtime | Significativo (minuti) |
| Consistenza | Massima (shutdown pulito) |
| Caso d'uso | VM critiche senza guest agent, database |
| Impatto | Servizi non disponibili durante il backup |

### Confronto Modalita di Backup

```
                     Snapshot          Suspend           Stop
                    +---------+       +---------+       +---------+
Downtime:           | Nessuno |       | Breve   |       | Lungo   |
                    +---------+       +---------+       +---------+
Consistenza FS:     | Con GA* |       | Si      |       | Si      |
                    +---------+       +---------+       +---------+
Consistenza App:    | Con GA* |       | Parziale|       | Si      |
                    +---------+       +---------+       +---------+
Velocita backup:    | Normale |       | Normale |       | Veloce  |
                    +---------+       +---------+       +---------+
Raccomandato per:   | Prod.   |       | Legacy  |       | DB      |
                    +---------+       +---------+       +---------+

*GA = QEMU Guest Agent installato e funzionante
```

### Tabella Decisionale per la Scelta della Modalita

| Scenario | Guest Agent | Modalita Consigliata | Motivazione |
|----------|-------------|---------------------|-------------|
| Web server Linux | Si | snapshot | Zero downtime, GA garantisce consistenza |
| Database MySQL/PostgreSQL | Si | snapshot + hook pre-backup | GA + dump DB prima del backup |
| Windows Server | Si (VirtIO tools) | snapshot | VirtIO GA supporta VSS |
| Legacy Linux (senza GA) | No | suspend | Breve downtime, consistenza FS |
| Appliance chiusa | No | stop | Unico modo per garantire consistenza |
| VM di sviluppo | Opzionale | snapshot | Downtime non critico |

---

## Compressione: zstd, lz4, gzip

### Confronto Algoritmi di Compressione

```bash
# Backup con zstd (default, raccomandato)
vzdump 100 --compress zstd --storage pbs-store

# Backup con lz4 (velocita massima)
vzdump 100 --compress lz4 --storage pbs-store

# Backup con gzip (compatibilita massima)
vzdump 100 --compress gzip --storage pbs-store

# Backup senza compressione (sconsigliato)
vzdump 100 --compress 0 --storage pbs-store
```

| Algoritmo | Rapporto Compressione | Velocita Compressione | Velocita Decompressione | CPU Usage | Consigliato Per |
|-----------|----------------------|----------------------|------------------------|-----------|----------------|
| **zstd** | Molto buono (~3:1) | Veloce | Molto veloce | Medio | Default, migliore compromesso |
| **lz4** | Buono (~2.5:1) | Molto veloce | Estremamente veloce | Basso | Backup frequenti, risorse CPU limitate |
| **gzip** | Buono (~3:1) | Lenta | Lenta | Alto | Compatibilita, archivi a lungo termine |
| **nessuna** | 1:1 | N/A | N/A | Nessuno | Storage abbondante, rete veloce |

### Benchmark Indicativo

```
Scenario: VM con disco 100 GB, dati 60 GB effettivi

Algoritmo    | Dimensione Backup | Tempo Backup | Tempo Restore
-------------|-------------------|--------------|---------------
zstd         | ~22 GB            | 8 min        | 5 min
lz4          | ~26 GB            | 5 min        | 3 min
gzip         | ~21 GB            | 15 min       | 10 min
nessuna      | ~60 GB            | 6 min        | 6 min

Nota: i valori dipendono fortemente dal tipo di dati,
dall'hardware e dalla velocita dello storage
```

### Configurazione Default della Compressione

```bash
# Impostare compressione default in /etc/vzdump.conf
cat >> /etc/vzdump.conf << 'EOF'
# Compressione default per tutti i backup
compress: zstd
EOF
```

---

## Limiti di Banda e Risorse

### Bandwidth Limiting

```bash
# Limitare la banda di backup (in KiB/s)
vzdump 100 --bwlimit 100000 --storage pbs-store --mode snapshot
# 100000 KiB/s = ~100 MB/s

# Impostare limite di banda globale in /etc/vzdump.conf
cat >> /etc/vzdump.conf << 'EOF'
bwlimit: 100000
EOF
```

### Priorita I/O

```bash
# Impostare priorita I/O bassa per i backup
vzdump 100 --ionice 7 --storage pbs-store

# ionice values:
# 0 = nessuna priorita (default del sistema)
# 7 = priorita piu bassa (best effort)
# 8 = idle (solo quando nessun altro processo usa I/O)

# Configurazione globale
cat >> /etc/vzdump.conf << 'EOF'
ionice: 7
EOF
```

### Limiti di Parallelismo

```bash
# Limitare il numero di backup paralleli
# In /etc/vzdump.conf:
cat >> /etc/vzdump.conf << 'EOF'
maxpar: 2
EOF

# Con maxpar=2, vzdump eseguira al massimo 2 backup contemporaneamente
# Le altre VM saranno messe in coda
```

### Configurazione Completa /etc/vzdump.conf

```bash
cat > /etc/vzdump.conf << 'EOF'
# Configurazione globale vzdump

# Storage di backup default
storage: pbs-store

# Modalita di backup default
mode: snapshot

# Compressione
compress: zstd

# Limiti di risorse
bwlimit: 100000     # 100 MB/s
ionice: 7           # Priorita I/O bassa
maxpar: 2           # Max 2 backup paralleli

# Notifiche
mailnotification: failure
mailto: admin@azienda.it

# Note template per i backup
notes-template: {{guestname}} - Backup automatico {{cluster}}

# Protezione backup (numero max backup protetti per VM su PBS)
# protected: 3

# Pigz threads per compressione gzip parallela (se si usa gzip)
pigz: 4

# Lock timeout (secondi)
lockwait: 180
EOF
```

### Tabella Limiti Consigliati per Scenario

| Scenario | bwlimit (KiB/s) | ionice | maxpar | Note |
|----------|-----------------|--------|--------|------|
| Backup notturno (fuori orario) | 0 (illimitato) | 0 | 4 | Massima velocita |
| Backup diurno (ore lavorative) | 50000 (~50 MB/s) | 7 | 1 | Impatto minimo |
| Rete dedicata 10G | 0 (illimitato) | 3 | 4 | Rete separata |
| Rete condivisa 1G | 50000 (~50 MB/s) | 7 | 2 | Non saturare la rete |

---

## Esclusione Path e Pattern

### Esclusione per Container LXC

Per i container LXC, e possibile escludere percorsi specifici dal backup:

```bash
# Escludere percorsi specifici
vzdump 200 --exclude-path /var/cache --exclude-path /tmp \
  --storage pbs-store --mode snapshot

# Escludere con pattern
vzdump 200 --exclude-path "/var/log/*.log" \
  --storage pbs-store --mode snapshot

# Configurazione esclusioni in /etc/vzdump.conf
cat >> /etc/vzdump.conf << 'EOF'
# Esclusioni globali per tutti i container
exclude-path: /tmp
exclude-path: /var/tmp
exclude-path: /var/cache
exclude-path: /var/log/*.gz
exclude-path: /var/log/*.old
EOF
```

### Esclusione per VM

Per le VM KVM, l'esclusione di percorsi non e diretta (si fa backup dell'intero disco). Tuttavia, e possibile escludere dischi specifici:

```bash
# Escludere un disco specifico dalla VM
# Prima: marcare il disco come "no-backup" nella configurazione VM
qm set 100 --scsi1 local-lvm:vm-100-disk-1,backup=0

# Il disco scsi1 non sara incluso nel backup
# Utile per dischi di dati temporanei o cache

# Verificare la configurazione
qm config 100 | grep -E '(scsi|virtio|ide|sata)[0-9]:'
```

### Esclusione di VM dal Backup

```bash
# Escludere VM specifiche dal backup globale
vzdump --all --exclude 105,110,115 --storage pbs-store

# Configurazione in /etc/vzdump.conf
cat >> /etc/vzdump.conf << 'EOF'
exclude: 105,110,115
EOF

# Oppure usare i pool per organizzare
# Backup solo del pool "production"
vzdump --pool production --storage pbs-store

# Backup solo del pool "critical"
vzdump --pool critical --storage pbs-store --mode snapshot --compress zstd
```

---

## Hook Scripts: Pre e Post Backup

### Struttura degli Hook Scripts

```bash
# Gli hook scripts vengono chiamati da vzdump in diversi momenti:
# - job-start:     inizio del job di backup completo
# - job-end:       fine del job di backup completo
# - job-abort:     abort del job
# - backup-start:  inizio backup di una singola VM/CT
# - backup-end:    fine backup di una singola VM/CT
# - backup-abort:  abort backup singola VM/CT
# - pre-stop:      prima dello stop della VM (solo mode stop)
# - pre-restart:   prima del restart della VM (dopo backup mode stop)
# - log-end:       fine della fase di log

# Configurare lo hook script in vzdump
vzdump 100 --script /usr/local/bin/vzdump-hook.sh --storage pbs-store
```

### Esempio Completo di Hook Script

```bash
#!/bin/bash
# /usr/local/bin/vzdump-hook.sh
# Hook script per vzdump con gestione database e notifiche

PHASE="$1"
MODE="$2"
VMID="$3"

LOG_FILE="/var/log/vzdump-hooks.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

log_msg() {
    echo "[$TIMESTAMP] [VMID:$VMID] [Phase:$PHASE] $1" >> "$LOG_FILE"
}

case "$PHASE" in
    job-start)
        log_msg "Inizio job di backup"
        ;;

    job-end)
        log_msg "Fine job di backup"
        ;;

    job-abort)
        log_msg "ERRORE: Job di backup abortito!"
        # Inviare notifica urgente
        echo "Backup job abortito su $(hostname)" | \
          mail -s "ALERT: Backup abort" admin@azienda.it
        ;;

    backup-start)
        log_msg "Inizio backup VM/CT $VMID (mode: $MODE)"

        # Pre-backup per database MySQL (se VM 100 e un DB server)
        if [ "$VMID" = "100" ]; then
            log_msg "Esecuzione flush tables MySQL su VM $VMID"
            # Eseguire via SSH o QEMU Guest Agent
            qm guest exec $VMID -- bash -c \
              "mysql -u root -e 'FLUSH TABLES WITH READ LOCK; SYSTEM sleep 2; UNLOCK TABLES;'" \
              2>/dev/null
            log_msg "Flush tables completato"
        fi

        # Pre-backup per PostgreSQL (se VM 101 e un DB server)
        if [ "$VMID" = "101" ]; then
            log_msg "Esecuzione checkpoint PostgreSQL su VM $VMID"
            qm guest exec $VMID -- bash -c \
              "sudo -u postgres psql -c 'CHECKPOINT;'" \
              2>/dev/null
            log_msg "Checkpoint PostgreSQL completato"
        fi
        ;;

    backup-end)
        log_msg "Fine backup VM/CT $VMID - SUCCESSO"
        ;;

    backup-abort)
        log_msg "ERRORE: Backup VM/CT $VMID abortito!"
        echo "Backup abortito per VM $VMID su $(hostname)" | \
          mail -s "ALERT: Backup $VMID abort" admin@azienda.it
        ;;

    pre-stop)
        log_msg "Pre-stop VM $VMID"
        # Operazioni prima dello shutdown (solo mode stop)
        ;;

    pre-restart)
        log_msg "Pre-restart VM $VMID"
        # Operazioni prima del restart (solo mode stop)
        ;;

    log-end)
        log_msg "Log phase completata per VM $VMID"
        ;;

    *)
        log_msg "Fase sconosciuta: $PHASE"
        ;;
esac

exit 0
```

```bash
# Rendere eseguibile
chmod +x /usr/local/bin/vzdump-hook.sh

# Configurare globalmente in /etc/vzdump.conf
cat >> /etc/vzdump.conf << 'EOF'
script: /usr/local/bin/vzdump-hook.sh
EOF
```

### Hook Script per Application-Consistent Backup

```bash
#!/bin/bash
# /usr/local/bin/vzdump-app-consistent.sh
# Hook per backup application-consistent di database

PHASE="$1"
MODE="$2"
VMID="$3"

# Mappatura VMID -> tipo applicazione
declare -A APP_MAP
APP_MAP[100]="mysql"
APP_MAP[101]="postgresql"
APP_MAP[102]="mongodb"
APP_MAP[103]="redis"

APP_TYPE="${APP_MAP[$VMID]}"

case "$PHASE" in
    backup-start)
        if [ -n "$APP_TYPE" ]; then
            case "$APP_TYPE" in
                mysql)
                    qm guest exec $VMID -- bash -c \
                      "mysqldump --all-databases --single-transaction > /tmp/pre-backup-dump.sql"
                    ;;
                postgresql)
                    qm guest exec $VMID -- bash -c \
                      "sudo -u postgres pg_dumpall > /tmp/pre-backup-dump.sql"
                    ;;
                mongodb)
                    qm guest exec $VMID -- bash -c \
                      "mongodump --out /tmp/pre-backup-dump/"
                    ;;
                redis)
                    qm guest exec $VMID -- bash -c \
                      "redis-cli BGSAVE && sleep 5"
                    ;;
            esac
        fi
        ;;

    backup-end)
        if [ -n "$APP_TYPE" ]; then
            # Pulizia file temporanei
            qm guest exec $VMID -- bash -c \
              "rm -rf /tmp/pre-backup-dump*" 2>/dev/null
        fi
        ;;
esac

exit 0
```

---

## Scheduling via GUI e Cron

### Scheduling Tramite GUI (Web Interface PVE)

```
Percorso nella GUI:
Datacenter -> Backup -> Add

Parametri disponibili nella GUI:
+---------------------------------------------------------------+
| Backup Job Configuration                                       |
+---------------------------------------------------------------+
| Node:          [Tutti i nodi / Nodo specifico]                |
| Storage:       [pbs-store]                                     |
| Schedule:      [Giornaliero / Settimanale / Personalizzato]  |
| Selection:     [Tutte le VM / Pool / Includi / Escludi]      |
| Mail to:       [admin@azienda.it]                             |
| Mail notif.:   [Sempre / Solo errori / Mai]                   |
| Compress:      [ZSTD / LZ4 / GZIP / Nessuna]                |
| Mode:          [Snapshot / Suspend / Stop]                    |
| Enabled:       [Si / No]                                      |
| Notes template:[{{guestname}} - {{cluster}}]                  |
+---------------------------------------------------------------+
```

### Schedule Tramite Datacenter Backup Jobs

I backup jobs configurati dal Datacenter -> Backup vengono salvati in `/etc/pve/jobs.cfg` e sono gestiti dal cluster:

```bash
# Visualizzare i backup jobs configurati
cat /etc/pve/jobs.cfg

# Esempio contenuto:
# vzdump: backup-daily
#     schedule daily
#     all 1
#     compress zstd
#     enabled 1
#     mailnotification failure
#     mailto admin@azienda.it
#     mode snapshot
#     notes-template {{guestname}}
#     storage pbs-store
```

### Schedule Tramite Cron (Avanzato)

Per scenari che richiedono maggiore flessibilita:

```bash
# Creare schedule personalizzati in /etc/cron.d/vzdump-custom
cat > /etc/cron.d/vzdump-custom << 'EOF'
# Backup VM critiche (Tier 1) ogni 4 ore
0 */4 * * * root vzdump 100,101,102 --storage pbs-store --mode snapshot --compress zstd --mailnotification failure --mailto admin@azienda.it 2>&1 | logger -t vzdump-tier1

# Backup giornaliero tutte le VM (02:00)
0 2 * * * root vzdump --all --storage pbs-store --mode snapshot --compress zstd --maxpar 2 --bwlimit 100000 --mailnotification failure --mailto admin@azienda.it 2>&1 | logger -t vzdump-daily

# Backup settimanale full con nota (domenica 01:00)
0 1 * * 0 root vzdump --all --storage pbs-store --mode snapshot --compress zstd --notes-template "Full settimanale - {{guestname}} - {{cluster}}" --mailnotification always --mailto admin@azienda.it 2>&1 | logger -t vzdump-weekly

# Backup container di sviluppo (solo lun-ven, 23:00)
0 23 * * 1-5 root vzdump --pool development --storage pbs-store --mode snapshot --compress lz4 --mailnotification failure --mailto dev-team@azienda.it 2>&1 | logger -t vzdump-dev
EOF
```

### Formato Schedule nel GUI PVE

```
Formati supportati per lo scheduling in PVE:
- daily HH:MM           -> ogni giorno all'ora specificata
- mon,wed,fri HH:MM     -> giorni specifici
- */2:00                 -> ogni 2 ore
- sat 03:00             -> ogni sabato alle 03:00
- 1,15 02:00            -> il 1o e il 15 di ogni mese

Esempi:
  "daily 02:00"          -> ogni giorno alle 02:00
  "mon..fri 02:00"       -> dal lunedi al venerdi alle 02:00
  "sat 01:00"            -> ogni sabato alle 01:00
  "01 03:00"             -> il primo di ogni mese alle 03:00
```

---

## Selezione dello Storage di Backup

### Tipi di Storage Supportati per il Backup

| Tipo Storage | Content Type | Deduplicazione | Incrementale | Note |
|-------------|-------------|---------------|-------------|------|
| PBS | backup | Si (nativa) | Si (chunk-level) | Scelta raccomandata |
| NFS | backup | No | No | Compatibile, semplice |
| CIFS/SMB | backup | No | No | Compatibile, Windows-friendly |
| Directory locale | backup | No | No | Per test o piccoli ambienti |
| GlusterFS | backup | No | No | Distribuito |

### Configurazione Storage di Backup Multipli

```bash
# Storage PBS (primario)
pvesm add pbs pbs-primary \
  --server 10.10.10.50 \
  --datastore datastore1 \
  --username backup@pbs!pve-token \
  --password "TOKEN" \
  --fingerprint "xx:xx:..." \
  --content backup

# Storage NFS (secondario/legacy)
pvesm add nfs backup-nfs \
  --server 192.168.1.100 \
  --export /backup/proxmox \
  --content backup \
  --options vers=4.1

# Storage directory locale (emergenza)
pvesm add dir backup-local \
  --path /mnt/backup-locale \
  --content backup \
  --shared 0

# Verificare tutti gli storage di backup
pvesm status | grep backup
```

### Selezione dello Storage per Tipo di VM

```bash
# VM critiche -> PBS primario
vzdump 100,101,102 --storage pbs-primary --mode snapshot --compress zstd

# VM standard -> NFS
vzdump 110,111,112 --storage backup-nfs --mode snapshot --compress zstd

# Container di test -> directory locale
vzdump 200,201 --storage backup-local --mode snapshot --compress lz4
```

---

## Monitoraggio dei Job di Backup

### Monitoraggio da Web Interface

```
Percorso: Datacenter -> Backup -> [selezionare job] -> Last Run / Status

Oppure: Node -> Task Log -> filtrare per "vzdump"

Informazioni visualizzate:
- Stato (Running/OK/Error/Warning)
- Data e ora inizio/fine
- Durata
- Dimensione backup
- Velocita di trasferimento
- Rapporto di compressione
- Rapporto di deduplicazione (con PBS)
```

### Monitoraggio da CLI

```bash
# Lista task recenti di backup su un nodo
pvesh get /nodes/$(hostname)/tasks --typefilter vzdump --limit 20

# Stato di un task specifico
pvesh get /nodes/$(hostname)/tasks/UPID/status

# Log di un task specifico
pvesh get /nodes/$(hostname)/tasks/UPID/log

# Monitorare i task in esecuzione
watch -n 5 'pvesh get /nodes/$(hostname)/tasks --typefilter vzdump --status running 2>/dev/null'
```

### Script di Monitoraggio Automatico

```bash
#!/bin/bash
# /usr/local/bin/backup-monitor.sh
# Monitoraggio stato backup giornaliero

REPORT_FILE="/tmp/backup-report-$(date +%Y%m%d).txt"
DATE=$(date '+%Y-%m-%d')
HOSTNAME=$(hostname)

echo "=== Report Backup $DATE - Nodo: $HOSTNAME ===" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Contatori
TOTAL=0
SUCCESS=0
FAILED=0
WARNING=0

# Analizzare i task delle ultime 24 ore
for task in $(pvesh get /nodes/$HOSTNAME/tasks \
  --typefilter vzdump \
  --since $(date -d '24 hours ago' +%s) \
  --output-format json 2>/dev/null | \
  python3 -c "import sys,json; [print(t['upid']) for t in json.load(sys.stdin)]" 2>/dev/null); do

  STATUS=$(pvesh get /nodes/$HOSTNAME/tasks/$task/status \
    --output-format json 2>/dev/null | \
    python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null)

  TOTAL=$((TOTAL + 1))
  case "$STATUS" in
    OK|ok) SUCCESS=$((SUCCESS + 1)) ;;
    *error*|*Error*) FAILED=$((FAILED + 1)) ;;
    *) WARNING=$((WARNING + 1)) ;;
  esac
done

echo "Riepilogo:" >> "$REPORT_FILE"
echo "  Totale job:     $TOTAL" >> "$REPORT_FILE"
echo "  Completati:     $SUCCESS" >> "$REPORT_FILE"
echo "  Falliti:        $FAILED" >> "$REPORT_FILE"
echo "  Warning:        $WARNING" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Spazio storage
echo "Spazio storage backup:" >> "$REPORT_FILE"
pvesm status 2>/dev/null | grep -E "(pbs|backup)" >> "$REPORT_FILE"

# Inviare report
if [ "$FAILED" -gt 0 ]; then
    SUBJECT="[ERRORE] Report Backup $DATE - $FAILED falliti"
else
    SUBJECT="[OK] Report Backup $DATE - $SUCCESS/$TOTAL completati"
fi

mail -s "$SUBJECT" admin@azienda.it < "$REPORT_FILE"
```

---

## Notifiche Email

### Configurazione delle Notifiche

```bash
# Configurazione nel job di backup via GUI:
# Datacenter -> Backup -> Edit -> Mail to / Mail notification

# Opzioni di notifica:
# always  - Notifica per ogni backup (successo e fallimento)
# failure - Notifica solo in caso di errore (raccomandato)
# never   - Nessuna notifica

# Via CLI:
vzdump --all --storage pbs-store \
  --mailnotification failure \
  --mailto admin@azienda.it,team@azienda.it

# Configurazione globale in /etc/vzdump.conf:
cat >> /etc/vzdump.conf << 'EOF'
mailnotification: failure
mailto: admin@azienda.it
EOF
```

### Configurazione SMTP del Nodo PVE

```bash
# Proxmox VE usa postfix per l'invio email
# Configurare come relay verso il mail server aziendale

# Impostare il relay host
postconf -e "relayhost = smtp.azienda.it:587"
postconf -e "smtp_use_tls = yes"
postconf -e "smtp_sasl_auth_enable = yes"
postconf -e "smtp_sasl_security_options = noanonymous"
postconf -e "smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd"

# Configurare le credenziali
echo "smtp.azienda.it:587 pve-notifications@azienda.it:password" > /etc/postfix/sasl_passwd
chmod 600 /etc/postfix/sasl_passwd
postmap /etc/postfix/sasl_passwd

# Riavviare postfix
systemctl restart postfix

# Test invio email
echo "Test notifica backup PVE" | mail -s "PVE Test" admin@azienda.it
```

### Formato Notifica Email

```
Subject: vzdump backup status (node1) : OK

Contenuto tipico di una notifica vzdump:

+---------------------------------------------------------------+
| vzdump backup status                                           |
+---------------------------------------------------------------+
| Job ID:       backup-daily                                    |
| Node:         node1                                            |
| Status:       OK                                               |
+---------------------------------------------------------------+

Dettagli per VM:
+------+----------------+--------+----------+-----------+
| VMID | Nome           | Status | Durata   | Dimensione|
+======+================+========+==========+===========+
| 100  | web-server-01  | OK     | 5m 23s   | 12.3 GB   |
| 101  | db-server-01   | OK     | 8m 45s   | 25.1 GB   |
| 102  | app-server-01  | OK     | 4m 12s   | 8.7 GB    |
| 200  | dns-container  | OK     | 0m 45s   | 1.2 GB    |
+------+----------------+--------+----------+-----------+
```

---

## Backup di Container LXC

### Peculiarita del Backup Container

Il backup dei container LXC differisce da quello delle VM:

```bash
# Backup container - il filesystem viene archiviato come .pxar (su PBS)
# o come .tar (su directory/NFS)
vzdump 200 --storage pbs-store --mode snapshot --compress zstd

# Container supportano tutte le modalita di backup
vzdump 200 --mode snapshot   # Raccomandato
vzdump 200 --mode suspend    # Breve freeze
vzdump 200 --mode stop       # Shutdown, backup, restart
```

### Esclusioni Specifiche per Container

```bash
# Escludere percorsi inutili dal backup container
vzdump 200 --mode snapshot --storage pbs-store \
  --exclude-path /tmp \
  --exclude-path /var/tmp \
  --exclude-path /var/cache \
  --exclude-path /var/log/*.gz \
  --exclude-path /var/log/journal

# In /etc/vzdump.conf per esclusioni globali:
# exclude-path: /tmp
# exclude-path: /var/tmp
# exclude-path: /var/cache/apt/archives
```

### Bind Mount e Backup Container

```bash
# I bind mount vengono inclusi nel backup SOLO se configurati correttamente
# Verificare i mount point nella configurazione del container
pct config 200

# Esempio output:
# mp0: /mnt/shared-data,mp=/shared,backup=1
# mp1: /mnt/scratch,mp=/scratch,backup=0

# mp0 con backup=1 -> incluso nel backup
# mp1 con backup=0 -> escluso dal backup

# Modificare la configurazione di backup per un mount point
pct set 200 --mp1 /mnt/scratch,mp=/scratch,backup=0
```

---

## Scenari Operativi e Best Practices

### Scenario 1: Backup Pre-Aggiornamento

```bash
# Prima di un aggiornamento critico, eseguire backup immediato
vzdump 100 --storage pbs-store --mode snapshot --compress zstd \
  --notes-template "Pre-aggiornamento $(date +%Y-%m-%d) - {{guestname}}"

# Verificare che il backup sia stato completato
proxmox-backup-client list --repository backup@pbs!token@pbs-server:datastore1 | \
  grep "vm/100"
```

### Scenario 2: Backup Selettivo per Pool

```bash
# Creare pool per organizzare le VM
pvesh create /pools --poolid production
pvesh create /pools --poolid development
pvesh create /pools --poolid database

# Assegnare VM ai pool
pvesh set /pools/production --vms 100,101,102
pvesh set /pools/database --vms 110,111
pvesh set /pools/development --vms 120,121,122

# Backup per pool con parametri diversi
# Produzione: ogni 4 ore, compressione zstd
vzdump --pool production --storage pbs-store --mode snapshot --compress zstd

# Database: giornaliero, con hook per consistency
vzdump --pool database --storage pbs-store --mode snapshot --compress zstd \
  --script /usr/local/bin/vzdump-db-hook.sh

# Sviluppo: giornaliero, compressione rapida
vzdump --pool development --storage pbs-store --mode snapshot --compress lz4
```

### Scenario 3: Migrazione Backup tra Storage

```bash
# Ripristinare da uno storage per salvare su un altro
# (utile per migrare backup da NFS a PBS)

# 1. Identificare il backup da migrare
vzdump --list --storage backup-nfs

# 2. Ripristinare la VM temporaneamente
qmrestore /mnt/backup-nfs/dump/vzdump-qemu-100-2024_03_15-02_00_00.vma.zst 999 \
  --storage local-lvm

# 3. Eseguire backup su PBS
vzdump 999 --storage pbs-store --mode stop --compress zstd

# 4. Rimuovere la VM temporanea
qm destroy 999 --purge
```

### Best Practices Riepilogative

| Best Practice | Dettaglio |
|--------------|----------|
| Usare sempre modalita snapshot | A meno che non sia strettamente necessario suspend/stop |
| Installare QEMU Guest Agent | Su tutte le VM per backup consistenti |
| Usare compressione zstd | Miglior rapporto velocita/compressione |
| Limitare parallelismo | maxpar=2 per non sovraccaricare lo storage |
| Rete dedicata per backup | Separare traffico backup dalla produzione |
| Testare i ripristini | Almeno mensile, documentare i risultati |
| Monitorare lo spazio | Alert automatici per soglie critiche |
| Usare hook scripts | Per database e applicazioni stateful |
| Notifiche failure-only | Per evitare alert fatigue |
| Proteggere backup critici | Usare il flag "protected" su PBS |

---

## Riferimenti

- Documentazione vzdump: https://pve.proxmox.com/wiki/Backup_and_Restore
- Man page vzdump: `man vzdump`
- Configurazione /etc/vzdump.conf: https://pve.proxmox.com/wiki/Backup_and_Restore#vzdump_configuration
- QEMU Guest Agent: https://pve.proxmox.com/wiki/Qemu-guest-agent

---

## Approfondimenti — note del 2026-04-27

> **Approfondimento — `vzdump` modes a confronto.** `snapshot` (default per VM): usa `qemu-img` snapshot interno o LVM/ZFS snapshot esterno; downtime ~0; richiede storage compatibile. `suspend`: ferma temporaneamente la VM via QEMU monitor (downtime di alcuni secondi); fallback safe per qualsiasi storage. `stop`: spegnimento completo + dump + riavvio (downtime = durata dump, puo essere ore); usata solo per VM critiche dove e accettabile. Per i container LXC: `snapshot` se storage supporta, altrimenti `suspend`. Performance tip: mode snapshot con backend ZFS e ~3x piu veloce di LVM snapshot perche ZFS e copy-on-write nativo. Fonte: [Proxmox VE Wiki — Backup and Restore](https://pve.proxmox.com/wiki/Backup_and_Restore), retrieved 2026-04-27.

> **Caso reale — Backup PostgreSQL senza hook = restore failure.** Un cluster PG14 con scritture continue era backuppato con `vzdump --mode snapshot` senza hook script. Restore mensile di test: la VM si avvia, ma PostgreSQL non parte: errore "PANIC: WAL page magic mismatch". Causa: lo snapshot del disco era crash-consistent ma non application-consistent; il WAL aveva pagine semi-scritte. Soluzione: aggiungere hook script `/etc/vzdump-postgresql.sh` che esegue `pg_start_backup('vzdump')` prima dello snapshot e `pg_stop_backup()` dopo; configurare in `/etc/vzdump.conf` con `script: /etc/vzdump-postgresql.sh`. Risultato: i nuovi backup sono application-consistent, restore funziona. Lezione: per ogni DB non gestire backup come un disco generico — c'e sempre un hook richiesto. Fonte: [PostgreSQL — Continuous Archiving](https://www.postgresql.org/docs/current/continuous-archiving.html), retrieved 2026-04-27.

---

## Esercizi

1. **Concettuale — RTO/RPO.** Definisci RTO e RPO per: (a) DB transazionale e-commerce; (b) file server interno; (c) ambiente test/dev; (d) DC Active Directory. Per ognuno: target numerico + strategia di backup conseguente.

2. **Lab — backup + restore drill.** Su una VM Linux con dati creati al T0, configurare backup snapshot via PBS o storage locale; al T+1h modificare i dati; al T+24h fare un restore del backup originale e validare che i dati al T+1h siano scomparsi e quelli al T0 siano restored. Misurare il tempo totale (RTO).

3. **Stretch — hook PostgreSQL pre/post backup.** Scrivere uno script che integra con `vzdump` per: pre-backup `pg_start_backup`, snapshot, post-backup `pg_stop_backup`, archive del WAL su S3, verifica integrita. Documentare ogni step e gestione errori.

## Auto-valutazione

1. Differenza fra modalita snapshot, suspend e stop di vzdump.
2. Cosa fa il QEMU Guest Agent durante un backup snapshot e perche e raccomandato?
3. RTO vs RPO: definizioni e impatto sulla strategia di backup.
4. Regola 3-2-1-1-0: cosa significa ogni numero?
5. Quando un backup e crash-consistent vs application-consistent?
6. Perche i backup non testati sono "niente backup"?
7. Hook script `/etc/vzdump-hook.sh`: quali fasi del backup intercetta e a cosa serve?

## Letture primarie consigliate

- Proxmox VE Wiki — Backup and Restore. https://pve.proxmox.com/wiki/Backup_and_Restore (retrieved 2026-04-27).
- vzdump(1) man page. https://pve.proxmox.com/pve-docs/vzdump.1.html (retrieved 2026-04-27).
- Proxmox VE Wiki — Qemu-guest-agent. https://pve.proxmox.com/wiki/Qemu-guest-agent (retrieved 2026-04-27).
- PostgreSQL — Continuous Archiving and Point-in-Time Recovery. https://www.postgresql.org/docs/current/continuous-archiving.html (retrieved 2026-04-27).
- NIST SP 800-34 Rev 1 — Contingency Planning Guide. https://csrc.nist.gov/pubs/sp/800/34/r1/final (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 11.2 — `proxmox-backup-server-configurazione.md`: PBS come storage di backup avanzato.
- Modulo 09.2 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-database-postgresql-mysql.md`: integrazione backup con DB.
- Modulo 10.1 — `../10-CLUSTER-HA-PROXMOX-POST-MIGRAZIONE/ha-manager-regole-e-gruppi.md`: backup di VM HA-managed.

## Glossario locale

| Termine | Definizione |
|---|---|
| **vzdump** | Tool Proxmox per backup di VM e container. |
| **Modalita snapshot** | Backup live tramite snapshot del disco; default consigliato. |
| **Modalita suspend** | Backup con pausa breve della VM. |
| **Modalita stop** | Backup con spegnimento completo della VM. |
| **Crash-consistent** | Backup come power loss: filesystem ok ma applicazioni potenzialmente in stato inconsistente. |
| **Application-consistent** | Backup con quiesce dell'applicazione: filesystem + app coerenti. |
| **`fsfreeze` / `fsthaw`** | Funzioni QEMU Guest Agent per congelare/scongelare il filesystem. |
| **RTO** | Recovery Time Objective; tempo massimo per ripristino dopo disastro. |
| **RPO** | Recovery Point Objective; quantita di dati (in tempo) che si puo perdere. |
| **3-2-1-1-0 rule** | Best practice backup: 3 copie, 2 supporti, 1 offsite, 1 immutable, 0 errori test. |
| **Hook script** | Script eseguito da vzdump pre/post backup per quiesce app. |
| **Retention policy** | Regole per quanti backup conservare e per quanto tempo. |
| **WORM** | Write-Once-Read-Many; storage immutabile (Object Lock S3, tape WORM). |
| **VMA format** | Formato proprietario Proxmox per backup di VM. |
