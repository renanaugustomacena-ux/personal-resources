# Proxmox Backup Server: Configurazione Avanzata

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 5 — Operativita post-migrazione · Modulo 11.2 (segue 11.1 backup base, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 11.1 (backup base con vzdump); modulo 03 (storage backend); concetti generali deduplicazione, encryption client-side, GDPR/compliance.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. installare e configurare un **Proxmox Backup Server (PBS)** dedicato: hardware sizing, dataset ZFS, network dedicata, datastore configuration;
> 2. integrare PBS come storage backup in Proxmox VE: aggiungere il datastore in datacenter.cfg, configurare schedulazione `backup` task, fingerprint validation;
> 3. configurare **encryption client-side** (`proxmox-backup-client encrypt`): keyfile/passphrase, gestione chiavi, recovery procedure (loss of key = loss of backup);
> 4. configurare **pruning schedule** (retention) per mantenere N daily, M weekly, K monthly, J yearly; calcolare lo spazio ottimale per la retention scelta;
> 5. configurare **verification jobs** per validare l'integrita dei backup periodicamente (default settimanale);
> 6. configurare **garbage collection** per recuperare spazio dei chunk non piu referenziati (default settimanale);
> 7. configurare **sync jobs** per replicare un datastore PBS verso un secondo PBS (offsite);
> 8. usare **Tape Backup** (PBS Tape) per backup offline su LTO-8/9, gestione library, encryption hardware/software;
> 9. monitorare PBS: API, metrics, alert su disk space, GC failures, verification failures.
> **Tempo stimato:** lettura 60-90 min · lab 360 min (PBS dedicato + integrazione + sync + tape simulation)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox Backup Server 3.x; ZFS 2.2/2.3; LTO-8/9.

## Mappa concettuale

```
+============================================================+
|     Proxmox Backup Server: architettura e features          |
+============================================================+
|                                                            |
|   COMPONENTI PBS                                           |
|   - chunk store (deduplication block-level)                |
|   - datastore (logical grouping)                           |
|   - namespaces (multi-tenancy logical)                     |
|   - backup snapshots (group:type/id/timestamp)             |
|                                                            |
|   PIPELINE BACKUP DA PVE                                   |
|   1. vzdump invoca proxmox-backup-client                   |
|   2. PBC fa chunking del disco (~4 MB chunks)              |
|   3. SHA-256 di ogni chunk                                 |
|   4. Encryption client-side (se configurata)               |
|   5. Upload chunks nuovi (deduplica con esistenti)         |
|   6. Index file per il backup snapshot                     |
|                                                            |
|   FEATURE CHIAVE                                           |
|                                                            |
|   Deduplica       chunk identici salvati una sola volta    |
|                   risparmio 60-90% su backup successivi    |
|   Compressione    zstd default su ogni chunk               |
|   Encryption      client-side AES-256-GCM, keyfile         |
|                   passphrase, owner del key non MS         |
|   Verifica        SHA-256 ogni chunk, scheduled job        |
|   GC              libera chunk orfani settimanalmente      |
|   Sync            replica verso altro PBS (offsite)        |
|   Tape            backup offline su LTO-8/9                |
|   Pruning         retention policy (N daily, M weekly...)  |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   PRUNING SCHEDULE (retention example)                     |
|                                                            |
|   keep-last:    3      mantieni gli ultimi 3 backup        |
|   keep-daily:   14     ultimi 14 giorni                    |
|   keep-weekly:  4      ultime 4 settimane                  |
|   keep-monthly: 12     ultimi 12 mesi                      |
|   keep-yearly:  2      ultimi 2 anni                       |
|                                                            |
|   Totale ~35 backup snapshot per VM nel lungo termine      |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **PBS e per Proxmox quello che Backupsy/Veeam B&R e per VMware: un sistema dedicato.** Vivere senza PBS e possibile (vzdump verso NFS basta), ma rinunci a deduplica, encryption client-side, verifica SHA-256, sync offsite, tape. PBS e gratuito, c'e poca scusa per non usarlo.
2. **Deduplica trasforma il TCO del backup.** Senza deduplica, 30 giorni di backup giornalieri di una VM 100 GB = 3 TB di storage. Con PBS dedup: 100 GB iniziali + ~5-10 GB/giorno di delta = ~250-400 GB. Risparmio 80-90%.
3. **Encryption client-side proteggge da tre minacce.** (1) Compromissione del PBS (chi rubasse il PBS non puo leggere); (2) data leak in fase di trasporto/rest; (3) compliance (GDPR, HIPAA). Costo: gestione delle chiavi (recovery!).
4. **GC e Verification jobs sono *obbligatori*.** Senza GC, lo storage cresce indefinitamente con orfani. Senza verification, un bit-rot in un chunk vecchio non viene rilevato finche non serve il restore (troppo tardi).
5. **Sync verso PBS offsite e la versione moderna del "tape offsite".** Banda accettabile, dedup mantiene il delta basso, automatic e schedulato. Per compliance veramente strict (offline air-gap), tape resta superiore.

---

## Indice

1. [Gestione Avanzata dei Datastore](#gestione-avanzata-dei-datastore)
2. [Autenticazione: Utenti e Token API](#autenticazione-utenti-e-token-api)
3. [Configurazione della Crittografia](#configurazione-della-crittografia)
4. [Pruning Schedule](#pruning-schedule)
5. [Verification Jobs](#verification-jobs)
6. [Garbage Collection](#garbage-collection)
7. [Integrazione Tape Backup](#integrazione-tape-backup)
8. [Notifiche e Alerting](#notifiche-e-alerting)
9. [Remote Sync verso PBS Secondario](#remote-sync-verso-pbs-secondario)
10. [Tuning delle Performance](#tuning-delle-performance)
11. [Manutenzione e Monitoraggio](#manutenzione-e-monitoraggio)

---

## Gestione Avanzata dei Datastore

### Struttura Interna del Datastore

Comprendere la struttura interna del datastore e fondamentale per la gestione avanzata:

```
/mnt/datastore/datastore1/
  |
  +-- .chunks/                    # Directory chunk deduplicati
  |   +-- 0000/                   # Sottodirectory basate su hash
  |   |   +-- chunk_hash.blob     # Chunk compresso/crittografato
  |   +-- 0001/
  |   +-- .../
  |   +-- ffff/
  |
  +-- vm/                         # Backup delle VM
  |   +-- 100/                    # VMID 100
  |   |   +-- 2024-03-15T02:00:00Z/
  |   |   |   +-- index.json.blob         # Indice del backup
  |   |   |   +-- drive-scsi0.img.fidx    # Indice immagine disco
  |   |   |   +-- qemu-server.conf.blob   # Configurazione VM
  |   |   +-- 2024-03-16T02:00:00Z/
  |   +-- 101/
  |
  +-- ct/                         # Backup dei container
  |   +-- 200/
  |   |   +-- 2024-03-15T02:00:00Z/
  |   |       +-- index.json.blob
  |   |       +-- pct.conf.blob
  |   |       +-- root.pxar.didx          # Indice archivio pxar
  |
  +-- host/                       # Backup host fisici
  +-- .gc-status                  # Stato garbage collection
  +-- .lock                       # File di lock
```

### Operazioni Avanzate sui Datastore

```bash
# Lista dettagliata dei datastore
proxmox-backup-manager datastore list --output-format json-pretty

# Aggiornamento configurazione datastore
proxmox-backup-manager datastore update datastore1 \
  --comment "Datastore produzione - aggiornato" \
  --gc-schedule "sat 03:00" \
  --verify-new true

# Statistiche dettagliate del datastore
proxmox-backup-client status --repository root@pam@localhost:datastore1

# Output esempio:
# Total: 4.0 TiB
# Used: 1.2 TiB (30.00%)
# Available: 2.8 TiB
# Chunk count: 305842
# Deduplication factor: 3.21

# Lista contenuto del datastore per gruppo di backup
proxmox-backup-client list --repository root@pam@localhost:datastore1

# Visualizzare snapshot specifici
proxmox-backup-client snapshot list vm/100 \
  --repository root@pam@localhost:datastore1

# Informazioni dettagliate su un backup specifico
proxmox-backup-client snapshot show vm/100/2024-03-15T02:00:00Z \
  --repository root@pam@localhost:datastore1
```

### Gestione Multi-Datastore

```bash
# Scenario: datastore separati per classe di servizio

# Datastore Tier 1 - VM critiche (SSD, retention lunga)
proxmox-backup-manager datastore create ds-tier1 \
  --path /mnt/ssd-fast/ds-tier1 \
  --gc-schedule "daily 04:00" \
  --verify-new true \
  --comment "Tier 1 - VM mission critical"

# Datastore Tier 2 - VM importanti (HDD, retention media)
proxmox-backup-manager datastore create ds-tier2 \
  --path /mnt/hdd-storage/ds-tier2 \
  --gc-schedule "sat 04:00" \
  --comment "Tier 2 - VM business critical"

# Datastore Tier 3 - VM standard (HDD, retention breve)
proxmox-backup-manager datastore create ds-tier3 \
  --path /mnt/hdd-storage/ds-tier3 \
  --gc-schedule "sun 04:00" \
  --comment "Tier 3 - VM standard e sviluppo"
```

### Monitoraggio Capacita Datastore

```bash
#!/bin/bash
# Script di monitoraggio capacita datastore
WARN_THRESHOLD=80  # Soglia warning (%)
CRIT_THRESHOLD=90  # Soglia critica (%)

for ds in $(proxmox-backup-manager datastore list --output-format json | \
  python3 -c "import sys,json; [print(d['name']) for d in json.load(sys.stdin)]"); do

  path=$(proxmox-backup-manager datastore list --output-format json | \
    python3 -c "import sys,json; [print(d['path']) for d in json.load(sys.stdin) if d['name']=='$ds']")

  usage=$(df --output=pcent "$path" | tail -1 | tr -d ' %')

  if [ "$usage" -ge "$CRIT_THRESHOLD" ]; then
    echo "CRITICO: Datastore $ds al ${usage}% - INTERVENTO IMMEDIATO"
    # Inviare notifica urgente
  elif [ "$usage" -ge "$WARN_THRESHOLD" ]; then
    echo "WARNING: Datastore $ds al ${usage}% - Pianificare espansione"
  else
    echo "OK: Datastore $ds al ${usage}%"
  fi
done
```

---

## Autenticazione: Utenti e Token API

### Realm di Autenticazione

PBS supporta due realm di autenticazione:

| Realm | Descrizione | Uso Consigliato |
|-------|-------------|-----------------|
| `pam` | Utenti locali Linux | Amministratori, accesso diretto |
| `pbs` | Utenti PBS nativi | Utenti di servizio, backup operator |

### Gestione Utenti

```bash
# Creare un utente PBS nativo
proxmox-backup-manager user create backup-operator@pbs \
  --comment "Operatore backup" \
  --password "PasswordComplessa!2024" \
  --enable true \
  --expire "2025-12-31"

# Creare un utente per monitoring (sola lettura)
proxmox-backup-manager user create monitor@pbs \
  --comment "Utente monitoring sola lettura" \
  --password "MonitorPassword!2024"

# Lista utenti
proxmox-backup-manager user list

# Aggiornare un utente
proxmox-backup-manager user update backup-operator@pbs \
  --comment "Operatore backup - Team Infrastruttura" \
  --expire "2026-12-31"

# Cambiare password
proxmox-backup-manager user change-password backup-operator@pbs

# Disabilitare un utente
proxmox-backup-manager user update backup-operator@pbs --enable false

# Eliminare un utente
proxmox-backup-manager user remove backup-operator@pbs
```

### Token API

I token API sono il metodo raccomandato per l'autenticazione automatizzata:

```bash
# Generare un token API per un utente
proxmox-backup-manager user generate-token backup-operator@pbs backup-token

# Output:
# Successfully generated token: backup-operator@pbs!backup-token
# Value: a1b2c3d4-e5f6-7890-abcd-ef0123456789
# IMPORTANTE: Salvare il valore del token immediatamente!

# Generare token per root (per automazione)
proxmox-backup-manager user generate-token root@pam automation-token

# Lista token per un utente
proxmox-backup-manager user list-tokens backup-operator@pbs

# Revocare un token
proxmox-backup-manager user delete-token backup-operator@pbs backup-token
```

### Access Control List (ACL)

```bash
# Ruoli disponibili in PBS:
# - Admin:            Accesso completo
# - Audit:            Sola lettura su tutto
# - DatastoreAdmin:   Gestione completa datastore
# - DatastoreBackup:  Creazione backup + lettura propri backup
# - DatastoreReader:  Lettura backup + ripristino
# - NoAccess:         Nessun accesso

# Assegnare ruolo a un utente per un datastore specifico
proxmox-backup-manager acl update /datastore/datastore1 DatastoreBackup \
  --auth-id backup-operator@pbs

# Assegnare ruolo Audit per monitoring globale
proxmox-backup-manager acl update / Audit \
  --auth-id monitor@pbs

# Assegnare ruolo a un token API
proxmox-backup-manager acl update /datastore/ds-tier1 DatastoreBackup \
  --auth-id backup-operator@pbs!backup-token

# Visualizzare ACL
proxmox-backup-manager acl list

# Rimuovere ACL
proxmox-backup-manager acl delete /datastore/datastore1 \
  --auth-id backup-operator@pbs
```

### Matrice Permessi Consigliata

```
+-----------------------+------------------+---------------------+-------------------+
| Utente/Token          | Datastore Prod   | Datastore Sviluppo  | Globale           |
+=======================+==================+=====================+===================+
| root@pam              | Admin            | Admin               | Admin             |
| backup-operator@pbs   | DatastoreBackup  | DatastoreBackup     | -                 |
| pve-cluster!token     | DatastoreBackup  | DatastoreBackup     | -                 |
| monitor@pbs           | -                | -                   | Audit             |
| dev-team@pbs          | -                | DatastoreReader     | -                 |
+-----------------------+------------------+---------------------+-------------------+
```

---

## Configurazione della Crittografia

### Architettura Crittografica di PBS

PBS implementa la crittografia client-side, il che significa che i dati vengono crittografati sul client (nodo PVE) prima di essere inviati al server PBS.

```
+-------------------+                    +-------------------+
|    Client PVE     |                    |     Server PBS    |
|                   |                    |                   |
| Dati VM           |                    |                   |
|    |               |                    |                   |
|    v               |                    |                   |
| Chunking          |                    |                   |
|    |               |                    |                   |
|    v               |                    |                   |
| Compressione      |                    |                   |
|    |               |                    |                   |
|    v               |                    |                   |
| Crittografia      |    chunk cifrati   |                   |
| (AES-256-GCM)  ---|------------------>| Storage chunk     |
|    |               |                    | (dati cifrati)    |
|    v               |                    |                   |
| Encryption Key    |                    | Il server NON ha  |
| (locale)          |                    | accesso ai dati   |
+-------------------+                    +-------------------+
```

### Generazione della Encryption Key

```bash
# Generare una encryption key per il backup
proxmox-backup-client key create /etc/pve/priv/pbs-encryption-key.json

# Output:
# Encryption Key Fingerprint: ab:cd:ef:12:34:...
# ATTENZIONE: Conservare questa chiave in luogo sicuro!
# Senza questa chiave, i backup NON possono essere ripristinati!

# Visualizzare informazioni sulla chiave
proxmox-backup-client key show /etc/pve/priv/pbs-encryption-key.json

# Creare un backup della chiave (FONDAMENTALE!)
cp /etc/pve/priv/pbs-encryption-key.json /percorso/sicuro/backup-key.json

# Creare una paper key (versione stampabile della chiave)
proxmox-backup-client key paperkey /etc/pve/priv/pbs-encryption-key.json \
  --output-format text > /tmp/paperkey.txt
# STAMPARE e conservare in cassaforte
```

### Master Key per il Recupero

La master key permette al server PBS di riencrittare i dati per il recupero, anche se la chiave originale viene persa.

```bash
# Generare la master key (coppia RSA)
# Creare la chiave privata
proxmox-backup-client key create-master-key

# Questo crea due file:
# - master-public.pem   (chiave pubblica - va sul PBS)
# - master-private.pem  (chiave privata - va in CASSAFORTE OFFLINE)

# Importare la chiave pubblica master nel PBS
# (dalla web interface: Administration -> Configuration -> Master Key)
# Oppure via API

# FONDAMENTALE: la chiave privata master deve essere:
# 1. Conservata OFFLINE (non sul server)
# 2. Conservata in almeno 2 copie in luoghi diversi
# 3. Mai accessibile dalla rete
# 4. Idealmente su supporto cartaceo (paper key) in cassaforte
```

### Configurazione Crittografia nello Storage PVE

```bash
# Aggiungere la encryption key alla configurazione storage PBS in PVE
pvesm set pbs-store \
  --encryption-key /etc/pve/priv/pbs-encryption-key.json

# Verificare che la crittografia sia attiva
pvesm status --storage pbs-store

# In /etc/pve/storage.cfg apparira:
# pbs: pbs-store
#     server 10.10.10.50
#     datastore datastore1
#     username backup@pbs!pve-backup
#     encryption-key /etc/pve/priv/pbs-encryption-key.json
#     content backup
```

### Gestione delle Chiavi - Best Practices

| Chiave | Dove Conservare | Copie | Note |
|--------|----------------|-------|------|
| Encryption Key (JSON) | `/etc/pve/priv/` | 3+ copie | Backup su storage separato |
| Master Private Key | OFFLINE, cassaforte | 2+ copie | Mai sul server |
| Master Public Key | Sul server PBS | 1 copia | Caricata nella configurazione PBS |
| Paper Key | Cassaforte fisica | 2+ copie | Stampata e plastificata |

---

## Pruning Schedule

Il pruning e il processo di rimozione dei backup obsoleti secondo la retention policy configurata.

### Parametri di Pruning

```bash
# Parametri disponibili:
# --keep-last N      : mantiene gli ultimi N backup
# --keep-daily N     : mantiene 1 backup/giorno per N giorni
# --keep-weekly N    : mantiene 1 backup/settimana per N settimane
# --keep-monthly N   : mantiene 1 backup/mese per N mesi
# --keep-yearly N    : mantiene 1 backup/anno per N anni
```

### Configurazione Prune Jobs

```bash
# Creare un prune job per il datastore di produzione
proxmox-backup-manager prune-job create prune-produzione \
  --store ds-tier1 \
  --schedule "daily 05:00" \
  --keep-last 3 \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 6 \
  --keep-yearly 2 \
  --comment "Pruning giornaliero datastore produzione"

# Creare un prune job per sviluppo (retention piu breve)
proxmox-backup-manager prune-job create prune-sviluppo \
  --store ds-tier3 \
  --schedule "daily 05:30" \
  --keep-last 2 \
  --keep-daily 3 \
  --keep-weekly 2 \
  --keep-monthly 1 \
  --keep-yearly 0 \
  --comment "Pruning giornaliero datastore sviluppo"

# Lista prune jobs
proxmox-backup-manager prune-job list

# Esecuzione manuale di un prune job
proxmox-backup-manager prune-job run prune-produzione

# Simulazione pruning (dry-run) - non elimina nulla
proxmox-backup-client prune vm/100 \
  --repository root@pam@localhost:datastore1 \
  --keep-last 3 \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 6 \
  --keep-yearly 2 \
  --dry-run

# Output dry-run mostra cosa verrebbe mantenuto/eliminato:
# keep     vm/100/2024-03-20T02:00:00Z   (keep-last)
# keep     vm/100/2024-03-19T02:00:00Z   (keep-last)
# keep     vm/100/2024-03-18T02:00:00Z   (keep-last)
# keep     vm/100/2024-03-17T02:00:00Z   (keep-daily)
# remove   vm/100/2024-03-16T14:00:00Z
# keep     vm/100/2024-03-16T02:00:00Z   (keep-daily)
# ...
```

### Scenari di Retention Tipici

```
Scenario 1: Azienda standard (compliance 1 anno)
  keep-last:    3
  keep-daily:   7
  keep-weekly:  4
  keep-monthly: 12
  keep-yearly:  1
  Punti di ripristino totali: ~27

Scenario 2: Ambiente regolamentato (compliance 5 anni)
  keep-last:    5
  keep-daily:   14
  keep-weekly:  8
  keep-monthly: 24
  keep-yearly:  5
  Punti di ripristino totali: ~56

Scenario 3: Sviluppo/Test (retention minima)
  keep-last:    2
  keep-daily:   3
  keep-weekly:  1
  keep-monthly: 0
  keep-yearly:  0
  Punti di ripristino totali: ~6

Scenario 4: Database critici (granularita alta)
  keep-last:    5
  keep-daily:   14
  keep-weekly:  8
  keep-monthly: 12
  keep-yearly:  3
  Punti di ripristino totali: ~42
```

### Diagramma del Flusso di Pruning

```
Input: Lista di tutti i backup di un gruppo (es. vm/100)
  |
  v
[Ordina per data, dal piu recente al piu vecchio]
  |
  v
[Applica keep-last: marca i primi N come "keep"]
  |
  v
[Applica keep-daily: per ogni giorno, marca il piu recente non gia marcato]
  |
  v
[Applica keep-weekly: per ogni settimana, marca il piu recente non gia marcato]
  |
  v
[Applica keep-monthly: per ogni mese, marca il piu recente non gia marcato]
  |
  v
[Applica keep-yearly: per ogni anno, marca il piu recente non gia marcato]
  |
  v
[Tutti i backup NON marcati vengono eliminati]
  |
  v
Output: Backup mantenuti secondo la policy
```

---

## Verification Jobs

La verifica dei backup e un passaggio critico per garantire che i dati siano effettivamente ripristinabili.

### Tipologie di Verifica

| Tipo | Descrizione | Tempo | Risorse |
|------|-------------|-------|---------|
| Verifica indice | Controlla l'integrita degli indici | Veloce | Basse |
| Verifica chunk | Verifica checksum SHA-256 di ogni chunk | Lenta | Alte |
| Verifica completa | Verifica + decompressione + decrittografia | Molto lenta | Molto alte |

### Configurazione Verification Jobs

```bash
# Creare un job di verifica per il datastore di produzione
proxmox-backup-manager verify-job create verify-produzione \
  --store ds-tier1 \
  --schedule "wed 06:00" \
  --comment "Verifica settimanale backup produzione"

# Creare un job di verifica per nuovi backup (verifica immediata)
# Questo e configurabile nella configurazione del datastore:
proxmox-backup-manager datastore update ds-tier1 \
  --verify-new true

# Creare job di verifica per backup specifici (ultimi 7 giorni)
proxmox-backup-manager verify-job create verify-recenti \
  --store ds-tier1 \
  --schedule "daily 06:00" \
  --ignore-verified true \
  --outdated-after 7 \
  --comment "Verifica giornaliera backup ultimi 7 giorni"

# Lista verification jobs
proxmox-backup-manager verify-job list

# Esecuzione manuale
proxmox-backup-manager verify-job run verify-produzione

# Verifica manuale di un backup specifico
proxmox-backup-client verify vm/100/2024-03-20T02:00:00Z \
  --repository root@pam@localhost:datastore1
```

### Pianificazione delle Verifiche

```
+---------------------------------------------------------------+
|          Calendario Verifiche Settimanale                     |
+-------+-------------------------------------------------------+
| Lun   | Backup regolari                                       |
| Mar   | Backup regolari                                       |
| Mer   | Verifica completa ds-tier1 (06:00)                    |
| Gio   | Backup regolari                                       |
| Ven   | Verifica completa ds-tier2 (06:00)                    |
| Sab   | Garbage Collection (04:00)                            |
| Dom   | Verifica completa ds-tier3 (06:00), Full backup       |
+-------+-------------------------------------------------------+

Nota: i backup giornalieri vengono verificati automaticamente
con verify-new=true
```

---

## Garbage Collection

La garbage collection (GC) rimuove i chunk orfani dal datastore, liberando spazio disco dopo il pruning.

### Come Funziona la GC

```
Flusso Garbage Collection:

1. [Fase 1: Marking]
   - Scansiona tutti gli indici di backup esistenti
   - Marca ogni chunk referenziato come "in uso"

2. [Fase 2: Sweeping]
   - Scansiona la directory .chunks/
   - Identifica chunk NON marcati (orfani)
   - Chunk orfani piu vecchi di 24h vengono eliminati
   - Chunk orfani recenti (<24h) vengono mantenuti (sicurezza)

3. [Risultato]
   - Spazio liberato = chunk orfani eliminati
   - Integrita preservata = solo chunk non referenziati rimossi
```

### Configurazione della GC

```bash
# Impostare schedule GC per un datastore
proxmox-backup-manager datastore update datastore1 \
  --gc-schedule "sat 03:00"

# Esecuzione manuale GC
proxmox-backup-manager garbage-collection start datastore1

# Verificare stato GC
proxmox-backup-manager garbage-collection status datastore1

# Output esempio:
# Garbage Collection Status:
# Last Run: 2024-03-16 03:00:05
# Duration: 12 min 34 sec
# Chunks removed: 15234
# Bytes removed: 61.2 GiB
# Chunks remaining: 289608
# Pending chunks: 0
# Deduplication factor: 3.21
```

### Relazione tra Pruning e GC

```
Sequenza corretta:

1. Pruning:    Rimuove gli INDICI dei backup obsoleti
                (ma i chunk dati rimangono su disco)
                      |
                      v
2. GC:         Identifica chunk non piu referenziati
                da nessun indice e li rimuove
                      |
                      v
3. Spazio:     Lo spazio disco viene effettivamente liberato

IMPORTANTE: Senza GC, il pruning NON libera spazio disco!

Timeline consigliata:
  02:00 - Backup notturni
  04:00 - Pruning (elimina indici)
  05:00 - GC (libera chunk orfani)
  06:00 - Verifica integrita
```

### Schedule GC per Scenario

| Scenario | Frequenza GC | Note |
|----------|-------------|------|
| Datastore piccolo (<2 TB) | Giornaliera | GC veloce, overhead minimo |
| Datastore medio (2-20 TB) | Settimanale | Sabato/domenica notte |
| Datastore grande (>20 TB) | Settimanale | Pianificare in finestra manutenzione |
| Dopo pruning massivo | Immediata (manuale) | Per liberare spazio rapidamente |

---

## Integrazione Tape Backup

PBS supporta il backup su nastro magnetico per archiviazione a lungo termine e copie offline.

### Configurazione Tape Drive

```bash
# Identificare tape drive disponibili
proxmox-tape-manager drive scan

# Creare configurazione drive
proxmox-tape-manager drive create lto-drive0 \
  --path /dev/nst0 \
  --changer-drivenum 0

# Se presente un autoloader/library:
proxmox-tape-manager changer create tape-library \
  --path /dev/sg1

# Associare il drive alla library
proxmox-tape-manager drive update lto-drive0 \
  --changer tape-library \
  --changer-drivenum 0

# Verificare lo stato del drive
proxmox-tape-manager drive status lto-drive0
```

### Gestione Media Pool

```bash
# Creare un media pool
proxmox-tape-manager pool create monthly-archive \
  --drive lto-drive0 \
  --retention "keep 365d" \
  --encrypt true \
  --comment "Archivio mensile su nastro"

# Aggiungere media (nastri) al pool
proxmox-tape-manager media label-media --pool monthly-archive

# Inventario media
proxmox-tape-manager media list --pool monthly-archive
```

### Tape Backup Jobs

```bash
# Creare un job di backup su nastro
proxmox-tape-manager backup-job create monthly-tape-backup \
  --store datastore1 \
  --pool monthly-archive \
  --drive lto-drive0 \
  --schedule "monthly" \
  --latest-only true \
  --comment "Backup mensile su nastro LTO"

# Esecuzione manuale
proxmox-tape-manager backup-job run monthly-tape-backup

# Ripristino da nastro
proxmox-tape-manager restore tape-content \
  --drive lto-drive0 \
  --store datastore1
```

### Confronto Storage per Tape

| Generazione LTO | Capacita Nativa | Compresso | Velocita | Uso Ideale |
|-----------------|----------------|-----------|----------|------------|
| LTO-7 | 6 TB | 15 TB | 300 MB/s | Piccoli ambienti |
| LTO-8 | 12 TB | 30 TB | 360 MB/s | Medi ambienti |
| LTO-9 | 18 TB | 45 TB | 400 MB/s | Grandi ambienti |

---

## Notifiche e Alerting

### Configurazione Email

```bash
# Configurare il relay SMTP
cat > /etc/proxmox-backup/notifications.cfg << 'EOF'
sendmail: default-mail
    mailto admin@azienda.it
    mailto-user root@pam
    from-address pbs@azienda.it
    comment Notifiche PBS default
EOF

# Configurare il relay SMTP del sistema
# Se si usa un relay esterno:
cat > /etc/msmtprc << 'EOF'
defaults
auth on
tls on
tls_starttls off
logfile /var/log/msmtp.log

account default
host smtp.azienda.it
port 465
user pbs-notifications@azienda.it
password PasswordSMTP
from pbs@azienda.it
EOF

chmod 600 /etc/msmtprc

# Installare msmtp se non presente
apt install msmtp msmtp-mta -y

# Test invio email
echo "Test notifica PBS" | mail -s "PBS Test" admin@azienda.it
```

### Configurazione Notifiche per Evento

```bash
# Configurare le notifiche per datastore
proxmox-backup-manager datastore update datastore1 \
  --notify "gc=always,verify=always,sync=error"

# Opzioni di notifica:
# - always:  notifica sempre (successo e fallimento)
# - error:   notifica solo in caso di errore
# - never:   nessuna notifica

# Esempio configurazione notifiche differenziate:
# Produzione: notifica sempre per tutto
proxmox-backup-manager datastore update ds-tier1 \
  --notify "gc=always,verify=always,sync=always" \
  --notify-user root@pam

# Sviluppo: notifica solo errori
proxmox-backup-manager datastore update ds-tier3 \
  --notify "gc=error,verify=error,sync=error" \
  --notify-user root@pam
```

### Monitoraggio con Webhook (Opzionale)

```bash
#!/bin/bash
# Script hook per notifiche via webhook (Slack, Teams, etc.)
# Da inserire come post-job script

WEBHOOK_URL="https://hooks.slack.com/services/T00/B00/xxx"
JOB_STATUS="$1"  # success o failure
JOB_NAME="$2"

if [ "$JOB_STATUS" = "failure" ]; then
  COLOR="#FF0000"
  EMOJI=":x:"
else
  COLOR="#36a64f"
  EMOJI=":white_check_mark:"
fi

curl -X POST "$WEBHOOK_URL" \
  -H 'Content-type: application/json' \
  -d "{
    \"attachments\": [{
      \"color\": \"$COLOR\",
      \"title\": \"${EMOJI} PBS Backup - ${JOB_STATUS}\",
      \"text\": \"Job: ${JOB_NAME}\nServer: $(hostname)\nData: $(date)\",
      \"footer\": \"Proxmox Backup Server\"
    }]
  }"
```

---

## Remote Sync verso PBS Secondario

### Architettura Remote Sync

```
+-------------------+          Sync           +-------------------+
| PBS Primario      |    (Push o Pull mode)   | PBS Secondario    |
| (on-premise)      |<======================>| (offsite/DR)      |
|                   |                          |                   |
| datastore1        |     chunk cifrati       | datastore1-sync   |
| - vm/100          |  ===================>   | - vm/100          |
| - vm/101          |      solo i chunk       | - vm/101          |
| - ct/200          |      modificati         | - ct/200          |
+-------------------+                          +-------------------+
```

### Configurazione Remoti

```bash
# Sul PBS primario: aggiungere il PBS remoto
proxmox-backup-manager remote create pbs-offsite \
  --host pbs-dr.dominio.com \
  --port 8007 \
  --auth-id sync-user@pbs!sync-token \
  --password "TOKEN_VALUE_REMOTO" \
  --fingerprint "ab:cd:ef:..." \
  --comment "PBS DR site per offsite backup"

# Verificare la connessione al remoto
proxmox-backup-manager remote list

# Test connettivita
proxmox-backup-client list --repository sync-user@pbs!sync-token@pbs-dr.dominio.com:datastore1
```

### Sync Jobs

```bash
# Creare un sync job (PULL mode - PBS secondario scarica dal primario)
# Eseguire sul PBS SECONDARIO:
proxmox-backup-manager sync-job create sync-produzione \
  --store local-datastore \
  --remote pbs-primario \
  --remote-store datastore1 \
  --schedule "daily 22:00" \
  --remove-vanished true \
  --comment "Sync notturno da PBS primario"

# PUSH mode - PBS primario invia al secondario
# Eseguire sul PBS PRIMARIO:
proxmox-backup-manager sync-job create push-offsite \
  --store datastore1 \
  --remote pbs-offsite \
  --remote-store ds-sync \
  --schedule "daily 22:00" \
  --remove-vanished false \
  --comment "Push notturno verso PBS offsite"

# Esecuzione manuale sync
proxmox-backup-manager sync-job run sync-produzione

# Monitorare lo stato del sync
proxmox-backup-manager sync-job list
```

### Confronto Push vs Pull

| Caratteristica | Push Mode | Pull Mode |
|---------------|-----------|-----------|
| Iniziatore | PBS primario | PBS secondario |
| Firewall | Primario -> Secondario (porta 8007) | Secondario -> Primario (porta 8007) |
| Caso d'uso | Quando il primario ha connettivita limitata | Quando il secondario e il "collector" |
| Sicurezza | Secondario espone porta | Primario espone porta |
| Preferito per offsite | No (il primario deve raggiungere l'esterno) | Si (il secondario nell'offsite avvia la connessione) |

---

## Tuning delle Performance

### Parametri di Ottimizzazione

```bash
# Chunk size (default 4 MiB - generalmente ottimale)
# Non modificare a meno che non si abbiano esigenze specifiche

# Compressione: zstd offre il miglior rapporto velocita/compressione
# lz4 per massima velocita, gzip per massima compressione

# Limiti di banda per operazioni di backup (in KiB/s)
# Configurabile in /etc/pve/storage.cfg (lato PVE):
# pbs: pbs-store
#     ...
#     max-protected-backups 5

# Tuning ZFS per il datastore PBS
zfs set recordsize=64k pbs-store/datastore1
zfs set compression=lz4 pbs-store/datastore1
zfs set atime=off pbs-store/datastore1
zfs set primarycache=all pbs-store/datastore1
zfs set secondarycache=all pbs-store/datastore1

# ARC size per ZFS (se PBS e dedicato)
echo "options zfs zfs_arc_max=4294967296" > /etc/modprobe.d/zfs.conf
# 4 GB di ARC - regolare in base alla RAM disponibile
```

### Monitoraggio Performance

```bash
# Monitorare I/O durante il backup
iostat -xz 5

# Monitorare traffico rete
nload -m ens19

# Monitorare utilizzo CPU
htop

# Log dei task PBS
journalctl -u proxmox-backup.service -f

# Verifica tempi di backup dall'interfaccia web:
# Datastore -> Content -> selezionare VM -> colonna "Duration"
```

---

## Manutenzione e Monitoraggio

### Operazioni di Manutenzione Periodica

| Operazione | Frequenza | Comando | Note |
|-----------|-----------|---------|------|
| Aggiornamento PBS | Mensile | `apt update && apt upgrade` | Pianificare in finestra manutenzione |
| Verifica spazio disco | Giornaliera | `df -h /mnt/datastore/` | Automatizzare con script |
| Controllo log errori | Giornaliera | `journalctl -p err -u proxmox-backup*` | Integrare nel monitoring |
| Verifica stato GC | Settimanale | `proxmox-backup-manager gc status` | Verificare che lo spazio venga liberato |
| Test ripristino | Mensile | Ripristino VM di test | Documentare risultati |
| Verifica certificati | Mensile | `proxmox-backup-manager cert info` | Rinnovare prima della scadenza |
| Review retention | Trimestrale | Analisi spazio vs policy | Regolare se necessario |

### Script di Health Check

```bash
#!/bin/bash
# PBS Health Check Script
# Eseguire giornalmente via cron

LOG_FILE="/var/log/pbs-healthcheck.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "=== PBS Health Check - $DATE ===" >> "$LOG_FILE"

# 1. Servizi
for svc in proxmox-backup.service proxmox-backup-proxy.service; do
  if systemctl is-active --quiet "$svc"; then
    echo "OK: $svc attivo" >> "$LOG_FILE"
  else
    echo "ERRORE: $svc NON attivo!" >> "$LOG_FILE"
    systemctl restart "$svc"
    echo "AZIONE: tentativo di restart $svc" >> "$LOG_FILE"
  fi
done

# 2. Spazio disco
for ds_path in /mnt/datastore/*/; do
  usage=$(df --output=pcent "$ds_path" 2>/dev/null | tail -1 | tr -d ' %')
  if [ -n "$usage" ] && [ "$usage" -ge 90 ]; then
    echo "CRITICO: $ds_path al ${usage}%!" >> "$LOG_FILE"
  elif [ -n "$usage" ] && [ "$usage" -ge 80 ]; then
    echo "WARNING: $ds_path al ${usage}%" >> "$LOG_FILE"
  else
    echo "OK: $ds_path al ${usage:-N/A}%" >> "$LOG_FILE"
  fi
done

# 3. Errori recenti
ERRORS=$(journalctl -p err -u proxmox-backup.service --since "24 hours ago" --no-pager 2>/dev/null | wc -l)
if [ "$ERRORS" -gt 0 ]; then
  echo "WARNING: $ERRORS errori nelle ultime 24 ore" >> "$LOG_FILE"
else
  echo "OK: nessun errore nelle ultime 24 ore" >> "$LOG_FILE"
fi

echo "=== Fine Health Check ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
```

---

## Riferimenti

- Documentazione ufficiale PBS Administration Guide: https://pbs.proxmox.com/docs/administration-guide.html
- PBS Tape Backup: https://pbs.proxmox.com/docs/tape-backup.html
- PBS Encryption: https://pbs.proxmox.com/docs/backup-client.html#encryption
- PBS API Reference: https://pbs.proxmox.com/docs/api-viewer/

---

## Approfondimenti — note del 2026-04-27

> **Approfondimento — PBS hardware sizing.** Per PBS dedicato: CPU 4-8 core (GC e verify sono CPU-bound per SHA-256), RAM ~1 GB per ogni TB di chunk store (per cache metadata + ZFS ARC), storage NVMe SSD per chunk store recente + HDD per archive long-term, network 10 GbE o piu per ridurre tempo dei backup grandi. Esempio sizing per un cluster Proxmox 100 TB allocati con backup giornaliero retention 3 mesi: PBS con ~50 TB usable (deduplica 4-5x), 32 GB RAM, 8 core, 10 GbE. Fonte: [PBS Administration Guide — Hardware Requirements](https://pbs.proxmox.com/docs/installation.html#system-requirements), retrieved 2026-04-27.

> **Errore comune — Encryption keyfile perso = backup persi.** Sintomo: durante un disaster recovery test, il restore fallisce con "decryption failed". Causa: il keyfile di encryption client-side era stato salvato solo localmente sul Proxmox VE node che era stato distrutto nel disastro, e nessun backup del keyfile esisteva. Soluzione preventiva: gestire i keyfile di PBS come si gestiscono le chiavi master del PKI: copia in vault offline (KeePass + USB encrypted), stampa cartacea dell'hash + recovery procedure, distribuzione tra 2-3 referenti chiave. Documentare nel runbook DR la procedura per recuperare il keyfile prima di tentare restore. Fonte: [PBS — Encryption Best Practices](https://pbs.proxmox.com/docs/backup-client.html#encryption), retrieved 2026-04-27.

---

## Esercizi

1. **Concettuale — sizing PBS.** Calcola lo storage necessario per: cluster Proxmox con 30 VM, totale 5 TB allocato, backup giornaliero, retention "14 daily + 4 weekly + 12 monthly". Assumere deduplica ~5x, compressione ~2x.

2. **Lab — PBS standalone + encryption + sync.** (a) Installare PBS in una VM dedicata; (b) creare datastore con encryption keyfile; (c) configurare backup di una VM Proxmox verso PBS; (d) configurare un secondo PBS e attivare sync job tra i due; (e) testare restore da entrambi.

3. **Stretch — runbook DR con tape offsite.** Documentare la procedura completa di disaster recovery che usa: PBS primario (live), PBS sync (offsite), tape LTO-9 (mensile, offline). Per ogni livello: RTO/RPO atteso, procedura di restore step-by-step, validazione finale.

## Auto-valutazione

1. Differenza fra deduplica e compressione in PBS.
2. Cos'e la garbage collection in PBS e perche e necessaria?
3. Encryption client-side: chi possiede la chiave e cosa succede se viene persa?
4. Pruning schedule "keep-daily 14, keep-weekly 4, keep-monthly 12": quanti backup vengono mantenuti totali?
5. Sync job tra due PBS: quale traffico passa sulla rete (incremental vs full)?
6. Tape backup PBS: quale algoritmo di encryption usa l'hardware LTO-9?
7. Verification job: cosa fa esattamente e con quale frequenza schedularlo?

## Letture primarie consigliate

- Proxmox Backup Server — Administration Guide. https://pbs.proxmox.com/docs/administration-guide.html (retrieved 2026-04-27).
- PBS — Backup Client documentation. https://pbs.proxmox.com/docs/backup-client.html (retrieved 2026-04-27).
- PBS — Tape Backup. https://pbs.proxmox.com/docs/tape-backup.html (retrieved 2026-04-27).
- PBS — API reference. https://pbs.proxmox.com/docs/api-viewer/ (retrieved 2026-04-27).
- PBS — Encryption documentation. https://pbs.proxmox.com/docs/backup-client.html#encryption (retrieved 2026-04-27).
- LTO Consortium — LTO-9 specifications. https://www.lto.org/technology/ (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 11.1 — `backup-vm-e-container.md`: backup base con vzdump.
- Modulo 12.x — `../12-SICUREZZA-E-COMPLIANCE/sicurezza-compliance.md`: encryption e compliance.

## Glossario locale

| Termine | Definizione |
|---|---|
| **PBS** | Proxmox Backup Server; sistema dedicato per backup Proxmox. |
| **Datastore (PBS)** | Storage logico dove risiedono i chunk + index. |
| **Chunk** | Unita di backup PBS (~4 MB), identificata da SHA-256. |
| **Deduplica chunk-level** | Stesso chunk salvato una sola volta indipendentemente dai backup. |
| **Index file** | Metadata di un backup snapshot: lista di chunk SHA-256 + ordine. |
| **Pruning** | Rimozione di backup snapshot per retention policy. |
| **Garbage Collection** | Rimozione di chunk non piu referenziati da nessun backup. |
| **Verification job** | Validazione SHA-256 di tutti i chunk di un datastore. |
| **Sync job** | Replica di un datastore verso un secondo PBS (offsite). |
| **Tape Backup** | Backup offline su LTO; PBS supporta nativamente LTO-8/9. |
| **Namespace (PBS)** | Multi-tenancy logica all'interno di un datastore. |
| **Encryption keyfile** | File con chiave AES-256-GCM per encryption client-side. |
| **`proxmox-backup-client`** | CLI client per backup verso PBS (anche da Linux generico). |
