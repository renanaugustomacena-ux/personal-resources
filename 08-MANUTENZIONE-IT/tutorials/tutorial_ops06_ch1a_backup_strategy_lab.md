# Tutorial: Strategia di Backup e Verifica — Protezione Dati Hands-On Lab

> **Documento di riferimento:** `06-backup-disaster-recovery.md` (sezioni 2-3: Strategia di Backup e Verifica Backup)
> **Dominio:** Protezione Dati — Backup Operations
> **Ambito:** Regola 3-2-1-1-0, tipi di backup (full/incrementale/differenziale), backup per tipo di sistema (file server, AD, DB, VM), scheduling GFS, strumenti (rsync, BorgBackup, Windows Server Backup, mysqldump), test di restore, monitoraggio
> **Durata lab:** 4-5 ore
> **Livello:** Intermedio — richiede ops03a (Windows Server) e ops03b (Linux)
> **Prerequisiti:** DC-LAB-01, SRV-LINUX-01 operativi; almeno 5 GB spazio libero su SRV-LINUX-01
> **Ambiente:** SRV-LINUX-01 (rsync, BorgBackup, mysqldump, GLPI), DC-LAB-01 (Windows Server Backup, System State)

---

## Lab Environment Setup

```bash
# Su SRV-LINUX-01 — prepara directory backup lab
echo "=== SETUP DIRECTORY BACKUP LAB ==="
sudo mkdir -p /backup/{lab-local,lab-archive,lab-test-restore,borg-repo}
sudo chown -R lab-admin:lab-admin /backup
df -h /backup

echo ""
echo "Verifica strumenti:"
command -v rsync   && rsync --version | head -1 || echo "rsync: da installare"
command -v borgbackup 2>/dev/null || command -v borg 2>/dev/null && borg --version || echo "borg: da installare (apt install borgbackup)"
command -v mysqldump && mysqldump --version | head -1 || echo "mysqldump: non disponibile standalone (usa docker)"
```

```powershell
# Su DC-LAB-01 — verifica Windows Server Backup
Get-WindowsFeature -Name Windows-Server-Backup | Select-Object Name, InstallState
# Se non installata: Install-WindowsFeature Windows-Server-Backup
```

---

## PART A: FONDAMENTI — Proteggere i Dati Prima del Disastro

> Un backup è come un'assicurazione sulla vita: non sai quando ne avrai bisogno, ma quando ne hai bisogno è già troppo tardi per farsela. La differenza tra sopravvivere a un disastro IT e non sopravviverci dipende quasi interamente dalla qualità della strategia di backup. Non dal backup più recente — dalla strategia: come è strutturato, quanto è testato, dove sono le copie, come si ripristina sotto pressione.

---

### Concetto A1: La Regola 3-2-1-1-0 — Lo Standard Moderno di Protezione

> **Analogia.** Immagina di avere un documento importante. Lo tieni in un cassetto a casa (copia 1). Fai una fotocopia e la metti in ufficio (copia 2, supporto diverso, posizione diversa). Dai una copia al tuo avvocato in un'altra città (copia offsite). Fai una fotocopia che metti in una cassetta di sicurezza che nemmeno tu puoi aprire per un anno (copia immutabile). E una volta all'anno verifichi che tutte le copie siano ancora leggibili (zero errori). Questa è la regola 3-2-1-1-0 applicata ai documenti fisici.

**La regola spiegata in dettaglio:**

```
3 COPIE DEI DATI:
  Copia 0: dati di produzione (l'originale)
  Copia 1: backup primario (NAS locale, disco backup)
  Copia 2: backup secondario (cloud, altro sito)
  
  Probabilità matematica di perdita con 3 copie indipendenti:
  Se prob. guasto singolo disco = 1/100
  Prob. guasto contemporaneo 3 dischi = 1/1.000.000

2 SUPPORTI DIVERSI:
  Non usare solo HDD su stesso storage array
  Esempio: NAS (RAID) + cloud object storage
  Esempio: Disco locale + nastro
  Protegge da: firmware bug che corrompe tutti i dischi simili
  
1 COPIA OFFSITE:
  Fuori dall'edificio — distanza minima 50 km
  Protegge da: incendio, alluvione, furto fisico
  Nel lab: cloud (gratuito con limitazioni: BackBlaze B2, Wasabi, AWS S3)
  
1 COPIA IMMUTABILE (aggiunta per ransomware):
  Non modificabile/cancellabile per periodo definito
  Neanche da un admin con credenziali compromesse!
  Implementazioni:
    → Object Lock S3 (WORM mode su bucket AWS/MinIO)
    → BorgBackup in append-only mode
    → Nastri offline in caveau
    → Veeam Hardened Repository (Linux con accesso limitato)
  
  PERCHÉ È CRITICO: il ransomware moderno cerca e cifra anche i backup!
  Se il backup è scrivibile dalle stesse credenziali admin → a rischio
  
0 ERRORI (restore verificati):
  "Un backup non testato non è un backup"
  Test mensile: verifica ripristino file singoli
  Test trimestrale: ripristino completo di un sistema
  Senza test: scopri che il backup era corrotto durante il disastro
```

---

### Concetto A2: Tipi di Backup — Scegliere la Strategia Giusta

> **Analogia.** Quando scatti foto di una stanza che cambia nel tempo, hai diverse opzioni. Puoi fotografare tutta la stanza ogni giorno (full backup — costoso in storage e tempo). Oppure fotografarla una volta alla settimana e poi solo le parti che cambiano (incrementale — veloce ma complicato il restore). O fotografarla una volta e poi fare foto di tutto ciò che è cambiato dall'inizio (differenziale — via di mezzo). La "synthetic full" è come rielaborare digitalmente le foto parziali per ricostruire l'immagine completa senza re-fotografare.

**Confronto tipi di backup:**

```
FULL BACKUP:
  Cosa copia: TUTTO (ogni file, ogni dato)
  Spazio: massimo (100% dei dati)
  Tempo backup: lungo (ore per sistemi grandi)
  Tempo restore: VELOCE (un solo archivio)
  Rischio: basso (ogni backup è autonomo)
  Quando usarlo: settimanale/mensile per archivio a lungo termine

INCREMENTALE:
  Cosa copia: solo modifiche dall'ULTIMO backup (qualsiasi tipo)
  Spazio: minimo (solo delta quotidiano, tipicamente 1-5%)
  Tempo backup: BREVISSIMO
  Tempo restore: LENTO (serve full + ogni incrementale in sequenza)
  Rischio: ALTO (se un incrementale è corrotto, tutti i successivi sono inutili)
  Quando usarlo: backup giornalieri con snapshot full settimanale

DIFFERENZIALE:
  Cosa copia: solo modifiche dall'ULTIMO FULL
  Spazio: medio (cresce nel tempo fino al prossimo full)
  Tempo backup: medio (cresce nel tempo)
  Tempo restore: medio (full + un solo differenziale)
  Rischio: basso (dipende solo dal full)
  Quando usarlo: se serve velocità di restore ma finestra backup è limitata

SYNTHETIC FULL:
  Cosa fa: combina full + incrementali → crea nuovo full SUL SERVER BACKUP
  Vantaggio: non carica la rete/produzione, veloce
  Risultato: equivalente a un full backup completo
  Usato da: Veeam, Proxmox Backup Server
  Quando usarlo: ambienti virtualizzati con molto storage di backup

SCHEMA GFS (Grandfather-Father-Son):
  Son (figlio):   backup giornaliero incrementale, retention 7-14 giorni
  Father (padre): backup settimanale full, retention 4-5 settimane
  Grandfather:    backup mensile full, retention 12 mesi
  Annuale:        backup annuale, retention 3-10 anni (compliance)
```

---

### Concetto A3: Backup per Tipo di Sistema — Ogni Sistema Ha le Sue Regole

> **Perché mi interessa?** Un backup "semplice" di una VM spenta va bene. Ma un backup di un server di database ATTIVO può catturare transazioni incomplete, risultando in un backup inconsistente. Capire le tecnologie specifiche di ogni tipo di sistema garantisce backup che possono essere ripristinati correttamente.

**File Server — VSS e Agent-based:**

```
PROBLEMA: l'utente ha aperto documento.docx e lo sta modificando
          Se copio il file in questo momento, cattura uno stato inconsistente!

SOLUZIONE: Volume Shadow Copy Service (VSS)
  1. Chiede a tutte le app di "flusharsi" su disco
  2. Crea snapshot point-in-time del volume
  3. Il backup legge dallo snapshot (stato consistente)
  4. Le app riprendono normalmente
  
  Windows: VSS nativo integrato
  Linux: LVM snapshot o filesystem snapshot (btrfs/ZFS)
  
COSA INCLUDERE nel backup file server:
  ✓ Condivisioni utente e dipartimentali
  ✓ Configurazione condivisioni (permessi NTFS, DFS)
  ✓ Home directory utenti
  ✗ Pagefile, temp, cache (non necessari)
```

**Database — Consistenza Transazionale:**

```
PROBLEMA: database ha transazioni in corso
          Un backup "raw" cattura stato inconsistente (metà transazione scritta)
          
SOLUZIONI per tipo DB:
  
  MySQL/MariaDB:
    → mysqldump --single-transaction: snapshot InnoDB consistente
    → XtraBackup: hot backup fisico senza lock
    → Binary logs: point-in-time recovery
    
  PostgreSQL:
    → pg_dump: backup logico (SQL)
    → pg_basebackup: backup fisico consistente
    → WAL archiving: point-in-time recovery
    
  SQL Server:
    → BACKUP DATABASE: backup nativo consistente
    → Transaction log backup: ogni 15-30 min per RPO basso
    
GLPI nel lab (MariaDB in Docker):
  docker exec [container] mysqldump --single-transaction glpi > backup.sql
  
RPO (Recovery Point Objective) → quanto vecchi possono essere i dati ripristinati:
  Full giornaliero:           RPO = 24 ore
  Full + transaction log 15m: RPO = 15 minuti
  Replica sincrona:           RPO = 0 (zero perdita dati)
```

**Virtual Machine — Backup a livello Hypervisor:**

```
APPROCCIO MODERNO: backup della VM come unità
  Backup: hypervisor cattura snapshot VM → copia su repository backup
  
  VMware: vSphere CBT (Changed Block Tracking) → solo blocchi modificati
  Hyper-V: RCT (Resilient Change Tracking) → simile a CBT
  Proxmox: dirty bitmap → incrementale a livello di blocco
  VirtualBox: VBoxManage snapshot (per lab, non per produzione)
  
  PRO:
  → Agentless (nessun software da installare nella VM)
  → Application-consistent con script pre/post-freeze
  → Instant VM recovery (avvia VM direttamente dal backup)
  
  ANTI-PATTERN DA EVITARE:
  → Snapshot della VM usato come BACKUP: gli snapshot crescono indefinitamente,
    risiedono sullo stesso disco dei dati — NON proteggono da guasto storage!
  → Snapshot > 7 giorni: degrada le prestazioni IO della VM
```

**Active Directory — Criticità Speciali:**

```
AD è IL sistema più critico: senza AD, NIENTE funziona
(autenticazione, GPO, DNS, DHCP, autorizzazioni file)

BACKUP SYSTEM STATE (include):
  → NTDS.DIT: database AD con tutti gli oggetti
  → SYSVOL: GPO, script di logon
  → Registry: configurazione di sistema
  → Certificati
  
RESTORE MODALITÀ:
  → Non-autoritativo: ripristina DC, lascia che la replica AD
    sincronizzi con altri DC → usato per guasto hardware singolo DC
  → Autoritativo: forza la sincronizzazione dell'oggetto ripristinato
    verso tutti gli altri DC → usato per cancellazione accidentale di oggetti
    
AD Recycle Bin (cestino AD):
  → Deve essere abilitato PRIMA di aver bisogno!
  → Enable-ADOptionalFeature -Identity "Recycle Bin Feature"
  → Oggetti cancellati recuperabili per 180 giorni
```

---

### Concetto A4: Scheduling e Retention — Quanto e Per Quanto Tempo

> **Analogia.** Un medico non conserva gli esami del paziente in modo casuale: conserva i risultati recenti in cartella facilmente accessibile, gli esami dell'anno scorso in archivio, quelli di 5 anni fa in archivio morto. E li butta via dopo il periodo legale. La retention dei backup funziona allo stesso modo: i backup recenti devono essere velocemente accessibili, quelli storici devono esistere per compliance, ma conservare troppo costa e crea rischi (dati GDPR non cancellati).

**Schema GFS nel dettaglio:**

```
RETENTION OPERATIVA:
  Giornaliero (Son):   7 giorni  → ripristino rapido da errori recenti
  Settimanale (Father): 4 settimane → ripristino di una settimana fa
  Mensile (Grandfather): 12 mesi → ripristino di un mese fa
  Annuale:              3-10 anni → compliance fiscale/legale

RETENTION PER TIPO DI DATO (normativa italiana):
  Documenti contabili/fiscali → 10 anni (Codice Civile art. 2220)
  Email aziendali             → 3-5 anni (policy interna)
  Dati personali (GDPR)       → solo per la durata necessaria
                                 + obbligatoria eliminazione su richiesta
  Configurazioni di sistema   → versionate in Git (retention indefinita)
  Log di sistema              → 12-24 mesi

CALCOLO STORAGE NECESSARIO:
  10 TB dati produzione, full settimanale, incrementale giornaliero
  Retention GFS 12 mesi, deduplication 60%, compressione 40%
  
  52 full * 10 TB = 520 TB lordi
  260 incrementali * 0.5 TB = 130 TB lordi
  Totale lordo = 650 TB
  Dopo dedup (60%): 260 TB
  Dopo compressione (40%): 156 TB
  + margine 20% = ~187 TB storage necessario
```

---

### Concetto A5: Strumenti di Backup — dal Lab all'Enterprise

```
NEL LAB (gratuiti, open source):
  rsync:      semplice, universale, per file backup su Linux
              PRO: ovunque disponibile, nessuna dipendenza
              CONTRO: no deduplication, no encryption nativa
              
  BorgBackup: backup deduplicato, crittografato, su Linux
              PRO: deduplica eccellente, crittografia forte, incrementali efficienti
              CONTRO: solo CLI, learning curve
              
  Windows     nativo in Windows Server
  Server      PRO: gratuito, bare metal, System State
  Backup:     CONTRO: funzionalità limitate, no dedup

  mysqldump:  backup logico MySQL/MariaDB
              Adatto per DB < 50 GB, non per ambienti ad alto carico

IN PRODUZIONE (a pagamento):
  Veeam B&R:  leader per VMware/Hyper-V
              CBT, SureBackup, Instant Recovery
              Community Edition gratuita fino a 10 workload
              
  Proxmox     nativo per Proxmox VE, open source
  Backup      deduplication, crittografia, incrementale blocco
  Server:     
  
  XtraBackup: hot backup MySQL/MariaDB senza lock
```

---
---

## PART B: OPERAZIONI — Implementare e Verificare Backup nel Lab

---

### Esercizio B1: rsync — Backup File Server Linux con Verifica Integrità

**Obiettivo.** Implementare un backup rsync di `/etc` e `/var/lib/glpi` su SRV-LINUX-01 con rotazione giornaliera, verifica checksum, e log strutturato.

**Background.** rsync è il coltellino svizzero del backup su Linux. È installato praticamente ovunque, trasferisce solo le differenze (delta), e può usare SSH per backup remoti sicuri. Per un sysadmin Linux, saper usare rsync è fondamentale. Le sue limitazioni (no deduplication, no encryption nativa) lo rendono adatto per backup locali su directory, non per archivi di lungo termine.

**Step 1 — Primo backup rsync:**

```bash
# Su SRV-LINUX-01 come lab-admin
# Crea struttura directory di destinazione
BACKUP_DIR="/backup/lab-local"
TODAY=$(date +%Y%m%d_%H%M%S)
DEST="${BACKUP_DIR}/${TODAY}"

mkdir -p "$DEST"
echo "Directory backup: $DEST"

# Backup /etc (configurazioni di sistema)
echo ""
echo "=== BACKUP /etc ==="
rsync -avhP \
    --stats \
    --log-file="${BACKUP_DIR}/rsync_${TODAY}.log" \
    --exclude="*.pid" \
    --exclude="/etc/mtab" \
    /etc/ \
    "${DEST}/etc/"

echo ""
echo "=== RISULTATO BACKUP /etc ==="
du -sh "${DEST}/etc"
echo "File nel log:"
tail -10 "${BACKUP_DIR}/rsync_${TODAY}.log"
```

**Spiegazione parametri rsync:**

```
rsync -avhP --stats ...

  -a  → archive mode: preserva permessi, ownership, timestamp, link simbolici
  -v  → verbose: mostra ogni file copiato
  -h  → human-readable: dimensioni in KB/MB invece di bytes
  -P  → --partial + --progress: mostra progresso e può riprendere
  --stats → statistiche finali (file copiati, bytes trasferiti, velocità)
  --log-file → salva output in file log
  --exclude → esclude pattern specifici
  
  FONTE: /etc/       ← nota lo slash finale! rsync copia il CONTENUTO
  DEST:  ${DEST}/etc/ ← (senza slash finale: copia la directory stessa)
```

**Step 2 — Backup GLPI (database + file applicativi):**

```bash
# Backup dati GLPI (se GLPI è installato)
echo "=== BACKUP GLPI ==="

# Trova il container MariaDB di GLPI
GLPI_CONTAINER=$(docker ps --filter "name=glpi" --format "{{.Names}}" 2>/dev/null | head -1)

if [[ -n "$GLPI_CONTAINER" ]]; then
    echo "Container GLPI trovato: $GLPI_CONTAINER"
    
    # Backup database MariaDB (dentro il container)
    MYSQL_PASS=$(docker exec "$GLPI_CONTAINER" printenv MYSQL_ROOT_PASSWORD 2>/dev/null || echo "")
    
    if [[ -n "$MYSQL_PASS" ]]; then
        echo "Esecuzione mysqldump..."
        docker exec "$GLPI_CONTAINER" \
            mysqldump --single-transaction --routines --triggers \
            -uroot -p"$MYSQL_PASS" glpi 2>/dev/null | \
            gzip > "${DEST}/glpi_db_${TODAY}.sql.gz"
        
        DB_SIZE=$(du -sh "${DEST}/glpi_db_${TODAY}.sql.gz" | awk '{print $1}')
        echo "[OK] DB backup: ${DEST}/glpi_db_${TODAY}.sql.gz ($DB_SIZE)"
    else
        echo "[WARN] Password MySQL non trovata — skip DB backup"
    fi
else
    echo "[INFO] Container GLPI non trovato — creazione backup di esempio"
    # Crea file di test per simulare il backup
    echo "GLPI DB backup simulation - $(date)" | \
        gzip > "${DEST}/glpi_db_${TODAY}.sql.gz"
    echo "[OK] File di test creato per l'esercizio"
fi

# Backup file GLPI (configurazioni, upload, log)
GLPI_DATA="/var/lib/glpi"
if [[ -d "$GLPI_DATA" ]]; then
    rsync -avh --stats \
        --exclude="*.tmp" \
        "$GLPI_DATA/" \
        "${DEST}/glpi_files/"
    echo "[OK] File GLPI copiati"
else
    mkdir -p "${DEST}/glpi_files"
    echo "GLPI data simulation" > "${DEST}/glpi_files/placeholder.txt"
    echo "[INFO] /var/lib/glpi non trovato — file placeholder creato"
fi
```

**Step 3 — Calcola checksum per verifica integrità:**

```bash
echo "=== CALCOLO CHECKSUM (SHA256) ==="
CHECKSUM_FILE="${DEST}/CHECKSUMS.sha256"

# Calcola SHA256 di ogni file nel backup
find "${DEST}" -type f -not -name "CHECKSUMS.sha256" | \
    sort | \
    xargs sha256sum 2>/dev/null > "$CHECKSUM_FILE"

echo "Checksum calcolati:"
wc -l "$CHECKSUM_FILE" | awk '{print $1, "file verificati"}'
echo ""
echo "Esempio checksum:"
head -3 "$CHECKSUM_FILE"

echo ""
echo "=== VERIFICA CHECKSUM ==="
if sha256sum --check "$CHECKSUM_FILE" 2>/dev/null | grep -q "FAILED"; then
    echo "[ERRORE] Alcuni file sono corrotti!" 
    sha256sum --check "$CHECKSUM_FILE" 2>/dev/null | grep "FAILED"
else
    echo "[OK] Tutti i file integri"
fi

echo ""
echo "=== RIEPILOGO BACKUP ==="
du -sh "${DEST}"
echo "Location: ${DEST}"
echo "Log: ${BACKUP_DIR}/rsync_${TODAY}.log"
echo "Checksum: ${CHECKSUM_FILE}"
```

**Checkpoint di verifica B1:**
- [ ] Backup di `/etc` completato correttamente
- [ ] File di log rsync creato con statistiche
- [ ] File CHECKSUMS.sha256 creato
- [ ] Verifica checksum restituisce OK

---

### Esercizio B2: BorgBackup — Backup Deduplicato e Crittografato

**Obiettivo.** Configurare BorgBackup per backup incrementali, deduplicati e crittografati di `/home` e `/etc` su SRV-LINUX-01.

**Background.** BorgBackup rappresenta lo stato dell'arte del backup open source su Linux. La sua deduplication a livello di blocco variabile è eccellente: in un backup tipico di server simili, raggiunge rapporti 10:1 o superiori. La crittografia è end-to-end: i dati sono cifrati prima di lasciare il client, il server di destinazione non può leggere il contenuto. Il repository è immutabile in modalità append-only: anche se un attaccante compromette le credenziali SSH, non può cancellare i backup esistenti.

**Step 1 — Installa e inizializza BorgBackup:**

```bash
# Installa borgbackup
sudo apt install -y borgbackup 2>/dev/null || sudo apt install -y borgbackup
borg --version

# Inizializza il repository (con crittografia repokey)
BORG_REPO="/backup/borg-repo"

echo "Inizializzazione repository Borg..."
echo ""
echo "NOTA: scegli una passphrase sicura! La perdi → perdi l'accesso ai backup"

# In lab usiamo passphrase semplice, in produzione usare password manager
export BORG_PASSPHRASE="LabBackup2024Sicuro!"

borg init --encryption=repokey "$BORG_REPO"
echo "[OK] Repository Borg inizializzato in $BORG_REPO"
echo ""
echo "Esporta la chiave del repository (CONSERVA IN LUOGO SICURO):"
borg key export "$BORG_REPO" /backup/borg-repo-key.txt
echo "Chiave salvata in /backup/borg-repo-key.txt"
```

**Step 2 — Primo backup:**

```bash
export BORG_PASSPHRASE="LabBackup2024Sicuro!"
BORG_REPO="/backup/borg-repo"
ARCHIVE_NAME="lab-backup-$(date +%Y%m%d_%H%M%S)"

echo "=== BACKUP BORG — $ARCHIVE_NAME ==="

borg create \
    --verbose \
    --filter AME \
    --list \
    --stats \
    --show-rc \
    --compression lz4 \
    --exclude-caches \
    --exclude '/home/*/.cache' \
    --exclude '/home/*/Downloads' \
    --exclude '*.tmp' \
    "${BORG_REPO}::${ARCHIVE_NAME}" \
    /etc \
    /home \
    2>&1 | tail -20

echo ""
echo "=== ARCHIVI NEL REPOSITORY ==="
borg list "$BORG_REPO"
```

**Step 3 — Crea secondo backup e osserva la deduplication:**

```bash
export BORG_PASSPHRASE="LabBackup2024Sicuro!"
BORG_REPO="/backup/borg-repo"

# Crea un file di test per simulare modifiche
echo "File di test modificato alle $(date)" >> /tmp/test-change.txt
cp /tmp/test-change.txt /etc/backup-test.txt
echo "File modificato aggiunto in /etc"

# Secondo backup (incrementale per Borg = solo blocchi nuovi)
ARCHIVE2="lab-backup-$(date +%Y%m%d_%H%M%S)-2"
echo ""
echo "=== SECONDO BACKUP BORG (deve essere molto più veloce) ==="

borg create \
    --verbose \
    --stats \
    --compression lz4 \
    "${BORG_REPO}::${ARCHIVE2}" \
    /etc /home \
    2>&1 | grep -E "Duration|Original|Compressed|Deduplicated|Number of files"

echo ""
echo "=== STATISTICHE DEDUPLICA ==="
borg info "$BORG_REPO"
```

**Output atteso (primo vs secondo backup):**
```
PRIMO BACKUP:
  Duration: 5.21 seconds
  Number of files: 1847
  Original size: 45.23 MB
  Compressed size: 18.12 MB
  Deduplicated: 18.12 MB      ← tutto nuovo, nessuna dedup

SECONDO BACKUP (solo modifiche):
  Duration: 0.89 seconds      ← molto più veloce!
  Number of files: 1848
  Original size: 45.23 MB
  Compressed size: 18.12 MB
  Deduplicated: 0.003 MB      ← quasi tutto già presente nel repo!
```

**Step 4 — Test di restore:**

```bash
export BORG_PASSPHRASE="LabBackup2024Sicuro!"
BORG_REPO="/backup/borg-repo"

echo "=== TEST RESTORE DA BORG ==="

# Lista archivi disponibili
echo "Archivi disponibili:"
borg list "$BORG_REPO"

# Ottieni nome primo archivio
FIRST_ARCHIVE=$(borg list "$BORG_REPO" --short | head -1)
echo ""
echo "Ripristino archivio: $FIRST_ARCHIVE"

# Restore in directory separata (non sovrascrive i dati live!)
RESTORE_DIR="/backup/lab-test-restore/borg-restore"
mkdir -p "$RESTORE_DIR"

# Restore di /etc/hostname come test
cd "$RESTORE_DIR"
borg extract --list "${BORG_REPO}::${FIRST_ARCHIVE}" etc/hostname
echo ""
echo "File ripristinato:"
cat "$RESTORE_DIR/etc/hostname"
echo ""
echo "[OK] Test restore completato"
echo "Contenuto della directory di restore:"
ls -la "$RESTORE_DIR/etc/"

# Pulizia file di test
sudo rm -f /etc/backup-test.txt 2>/dev/null || true
```

**Step 5 — Configura policy di retention:**

```bash
export BORG_PASSPHRASE="LabBackup2024Sicuro!"
BORG_REPO="/backup/borg-repo"

echo "=== POLITICA DI RETENTION BORG ==="
echo "Questo comando esegue il pruning senza eliminare nulla (dry-run):"

borg prune \
    --list \
    --dry-run \
    --keep-daily 7 \
    --keep-weekly 4 \
    --keep-monthly 12 \
    "$BORG_REPO"

echo ""
echo "In produzione, rimuovi --dry-run per applicare la retention"
echo "Esempio crontab settimanale:"
echo "  0 2 * * 0 BORG_PASSPHRASE='...' borg prune --keep-daily 7 --keep-weekly 4 $BORG_REPO"
```

**Checkpoint di verifica B2:**
- [ ] Repository Borg inizializzato con crittografia repokey
- [ ] Chiave repository esportata e salvata
- [ ] Primo backup creato con statistiche deduplication
- [ ] Secondo backup dimostra la deduplication (dimensione molto minore)
- [ ] Test restore di un file singolo riuscito

---

### Esercizio B3: Backup Active Directory — System State su DC-LAB-01

**Obiettivo.** Configurare e testare il backup del System State di Active Directory su DC-LAB-01 usando Windows Server Backup.

**Background.** Active Directory è il servizio più critico in un ambiente Windows. Senza AD: nessun utente può autenticarsi, i computer non trovano le policy GPO, i servizi AD-joined non funzionano. Il backup del System State include il database AD (NTDS.DIT), SYSVOL, il registro di sistema — tutto ciò che serve per ripristinare un Domain Controller.

**Step 1 — Installa Windows Server Backup:**

```powershell
# Su DC-LAB-01 come Administrator

# Verifica se già installato
$feature = Get-WindowsFeature -Name Windows-Server-Backup
if ($feature.InstallState -ne "Installed") {
    Write-Host "Installando Windows Server Backup..."
    Install-WindowsFeature -Name Windows-Server-Backup
    Write-Host "[OK] Windows Server Backup installato"
} else {
    Write-Host "[OK] Windows Server Backup già installato"
}

# Import del modulo
Import-Module WindowsServerBackup
Write-Host "Versione: $(Get-WBPolicy -ErrorAction SilentlyContinue | Out-Null; 'WSB disponibile')"
```

**Step 2 — Crea policy di backup System State:**

```powershell
# Crea directory di destinazione backup (su disco locale per lab)
$backupDest = "E:\Backup\SystemState"
if (-not (Test-Path $backupDest)) {
    # Nel lab usiamo C:\ dato che E:\ potrebbe non esistere
    $backupDest = "C:\Backup\SystemState"
    New-Item -ItemType Directory -Path $backupDest -Force | Out-Null
}
Write-Host "Directory backup: $backupDest"

# Avvia backup System State manuale (più veloce del backup completo per il lab)
Write-Host ""
Write-Host "=== AVVIO BACKUP SYSTEM STATE ==="
Write-Host "Questo può richiedere 10-20 minuti..."

$job = Start-WBBackup -BackupTarget $backupDest -SystemState -AllCritical -ErrorAction SilentlyContinue

if ($job) {
    Write-Host "[OK] Job di backup avviato"
    # Monitora il progresso
    while ($job.GetRunningStatus() -eq "Running") {
        Write-Host "  In corso... $($job.GetJobStatus())"
        Start-Sleep -Seconds 30
    }
    Write-Host "Stato finale: $($job.GetResult())"
} else {
    Write-Host "[INFO] Avvio backup via wbadmin (metodo alternativo)..."
    # Metodo alternativo tramite wbadmin
    Write-Host "Comando equivalente (eseguire in cmd Administrator):"
    Write-Host "  wbadmin start systemstatebackup -backupTarget:C:\Backup -quiet"
}
```

**Step 3 — Verifica backup e lista versioni:**

```powershell
# Verifica backup completati
Write-Host "=== VERSIONI BACKUP DISPONIBILI ==="
$versions = Get-WBBackupSet -ErrorAction SilentlyContinue
if ($versions) {
    $versions | Select-Object BackupTime, BackupTarget, VolumeList | Format-Table -AutoSize
} else {
    Write-Host "Nessuna versione trovata tramite Get-WBBackupSet"
    Write-Host "Verifica con: wbadmin get versions"
    wbadmin get versions 2>&1 | head -20
}

# Verifica NTDS.DIT (database AD)
$ntdsPath = "C:\Windows\NTDS\ntds.dit"
if (Test-Path $ntdsPath) {
    $ntdsSize = [math]::Round((Get-Item $ntdsPath).Length / 1MB, 2)
    Write-Host ""
    Write-Host "Database AD (NTDS.DIT): $ntdsSize MB"
    Write-Host "Ultima modifica: $((Get-Item $ntdsPath).LastWriteTime)"
} else {
    Write-Host "NTDS.DIT non trovato in percorso standard"
}

# Snapshot del database AD (metodo alternativo per analisi offline)
Write-Host ""
Write-Host "=== SNAPSHOT NTDS (per analisi offline) ==="
Write-Host "Comando: ntdsutil 'activate instance ntds' 'ifm' 'create full C:\IFM' quit quit"
Write-Host "(Non eseguire in lab senza controllare spazio disponibile)"
```

**Step 4 — Comprendere il Restore AD:**

```powershell
# Questa sezione è TEORICA — non eseguire in lab produttivo
# Mostra i comandi che useresti in un'emergenza reale

Write-Host "=== SCENARI DI RESTORE AD (TEORIA) ==="
Write-Host ""
Write-Host "SCENARIO 1: Cancellazione accidentale di un oggetto AD"
Write-Host "  1. Verifica AD Recycle Bin:"
Write-Host "     Get-ADObject -Filter {isDeleted -eq `$true} -IncludeDeletedObjects"
Write-Host "  2. Ripristina dal cestino:"
Write-Host "     Restore-ADObject -Identity '<GUID dell oggetto cancellato>'"
Write-Host ""
Write-Host "SCENARIO 2: Corruzione database AD (grave)"
Write-Host "  1. Riavvia DC in Directory Services Restore Mode (DSRM)"
Write-Host "     (F8 al boot o bcdedit /set {bootmgr} safeboot dsrepair)"
Write-Host "  2. Ripristina System State:"
Write-Host "     wbadmin start systemstaterecovery -version:[version_id] -quiet"
Write-Host "  3. Se restore AUTORITATIVO (forza propagazione):"
Write-Host "     ntdsutil 'authoritative restore' 'restore object DN=...' quit quit"
Write-Host ""
Write-Host "REGOLA: Test il restore PRIMA di averne bisogno!"

# Verifica AD Recycle Bin (se abilitato)
$recycleBin = Get-ADOptionalFeature -Filter {Name -eq "Recycle Bin Feature"} -ErrorAction SilentlyContinue
if ($recycleBin.EnabledScopes.Count -gt 0) {
    Write-Host ""
    Write-Host "[OK] AD Recycle Bin: ABILITATO — oggetti cancellati recuperabili"
} else {
    Write-Host ""
    Write-Host "[WARN] AD Recycle Bin: NON abilitato"
    Write-Host "  Abilita con: Enable-ADOptionalFeature -Identity 'Recycle Bin Feature' -Scope ForestOrConfigurationSet -Target (Get-ADForest)"
}
```

**Checkpoint di verifica B3:**
- [ ] Windows Server Backup installato
- [ ] Comprensione dei contenuti del System State (NTDS.DIT, SYSVOL)
- [ ] Backup avviato o conoscenza del comando alternativo (wbadmin)
- [ ] AD Recycle Bin verificato
- [ ] Scenari di restore compresi (autoritativo vs non-autoritativo)

---

### Esercizio B4: Test di Restore — La Parte più Importante

**Obiettivo.** Eseguire un test di restore verificato da BorgBackup e documentare i risultati con il formato corretto.

**Background.** "Un backup non testato non è un backup." Questa non è una frase motivazionale — è una verità statistica: circa il 30% dei restore fallisce per backup corrotti, incompleti, o procedure non documentate. Il test di restore scopre questi problemi PRIMA del disastro, non durante.

**Step 1 — Test restore BorgBackup (file multipli):**

```bash
# Su SRV-LINUX-01
export BORG_PASSPHRASE="LabBackup2024Sicuro!"
BORG_REPO="/backup/borg-repo"
RESTORE_DIR="/backup/lab-test-restore/full-restore-$(date +%Y%m%d_%H%M%S)"

echo "=== TEST RESTORE — $(date '+%Y-%m-%d %H:%M:%S') ===" | tee /tmp/restore-report.txt

mkdir -p "$RESTORE_DIR"

# Lista archivi disponibili
echo "" | tee -a /tmp/restore-report.txt
echo "Archivi disponibili:" | tee -a /tmp/restore-report.txt
borg list "$BORG_REPO" | tee -a /tmp/restore-report.txt

# Usa il primo archivio per il test
ARCHIVE=$(borg list "$BORG_REPO" --short | head -1)
echo "" | tee -a /tmp/restore-report.txt
echo "Archivio selezionato per il test: $ARCHIVE" | tee -a /tmp/restore-report.txt
echo "Directory di restore: $RESTORE_DIR" | tee -a /tmp/restore-report.txt

# Misura il tempo di restore
START_TIME=$(date +%s)

cd "$RESTORE_DIR"
borg extract \
    --list \
    "${BORG_REPO}::${ARCHIVE}" \
    etc/hosts \
    etc/hostname \
    etc/passwd \
    2>&1 | tee -a /tmp/restore-report.txt

END_TIME=$(date +%s)
RESTORE_SECONDS=$((END_TIME - START_TIME))
```

**Step 2 — Valida i dati ripristinati:**

```bash
echo "" | tee -a /tmp/restore-report.txt
echo "=== VALIDAZIONE DATI RIPRISTINATI ===" | tee -a /tmp/restore-report.txt

VALIDATION_OK=true

# Verifica /etc/hosts
if diff "$RESTORE_DIR/etc/hosts" /etc/hosts > /dev/null 2>&1; then
    echo "[OK] /etc/hosts: identico all'originale" | tee -a /tmp/restore-report.txt
else
    echo "[INFO] /etc/hosts: differenze rilevate (normale se modifica avvenuta dopo il backup)" | tee -a /tmp/restore-report.txt
fi

# Verifica /etc/hostname
RESTORED_HOSTNAME=$(cat "$RESTORE_DIR/etc/hostname" 2>/dev/null)
CURRENT_HOSTNAME=$(hostname)
echo "Hostname ripristinato: $RESTORED_HOSTNAME" | tee -a /tmp/restore-report.txt
echo "Hostname attuale:      $CURRENT_HOSTNAME"   | tee -a /tmp/restore-report.txt
if [[ "$RESTORED_HOSTNAME" == "$CURRENT_HOSTNAME" ]]; then
    echo "[OK] Hostname corrispondente" | tee -a /tmp/restore-report.txt
else
    echo "[WARN] Hostname diverso — potrebbe essere corretto se il sistema è stato rinominato" | tee -a /tmp/restore-report.txt
fi

# Verifica /etc/passwd (conta gli utenti)
ORIGINAL_USERS=$(wc -l < /etc/passwd)
RESTORED_USERS=$(wc -l < "$RESTORE_DIR/etc/passwd")
echo "Utenti /etc/passwd originale: $ORIGINAL_USERS" | tee -a /tmp/restore-report.txt
echo "Utenti /etc/passwd backup:    $RESTORED_USERS" | tee -a /tmp/restore-report.txt

echo "" | tee -a /tmp/restore-report.txt
echo "=== REPORT DI TEST RESTORE ===" | tee -a /tmp/restore-report.txt
echo "Data test:            $(date '+%Y-%m-%d %H:%M:%S')" | tee -a /tmp/restore-report.txt
echo "Backup usato:         $ARCHIVE" | tee -a /tmp/restore-report.txt
echo "Tempo di restore:     ${RESTORE_SECONDS} secondi" | tee -a /tmp/restore-report.txt
echo "Eseguito da:          $(whoami) su $(hostname)" | tee -a /tmp/restore-report.txt
echo "Esito validazione:    $([[ $VALIDATION_OK == true ]] && echo SUCCESSO || echo FALLIMENTO)" | tee -a /tmp/restore-report.txt

echo ""
echo "Report salvato in /tmp/restore-report.txt"
cat /tmp/restore-report.txt
```

**Step 3 — Simulazione di restore database (scenario disaster):**

```bash
echo ""
echo "=== SIMULAZIONE RESTORE DATABASE GLPI ==="
echo "Scenario: database GLPI corrotto — ripristina da backup mysqldump"

# Usa il backup creato in B1 o crea un dump di test
BACKUP_SQL=$(find /backup/lab-local -name "*.sql.gz" 2>/dev/null | head -1)

if [[ -n "$BACKUP_SQL" ]]; then
    echo "Backup trovato: $BACKUP_SQL"
    echo "Dimensione: $(du -sh "$BACKUP_SQL" | awk '{print $1}')"
    
    # Decomprime e verifica il contenuto (non esegue restore reale)
    echo ""
    echo "Verifica contenuto del backup SQL:"
    zcat "$BACKUP_SQL" 2>/dev/null | grep -E "^CREATE TABLE|^-- Table" | head -10
    echo ""
    echo "Il backup contiene struttura valida. In caso di restore reale:"
    echo "  zcat $BACKUP_SQL | docker exec -i [container] mysql -uroot -p[pwd] glpi"
else
    echo "[INFO] Nessun backup SQL trovato — simulazione con dati fittizi"
    echo "Procedura di restore database:"
    echo "  1. Stop applicazione (GLPI)"
    echo "  2. Drop database corrotto: DROP DATABASE glpi;"
    echo "  3. Create database vuoto: CREATE DATABASE glpi;"
    echo "  4. Restore: zcat glpi_backup.sql.gz | mysql -u root -p glpi"
    echo "  5. Verify: SELECT COUNT(*) FROM glpi.glpi_tickets;"
    echo "  6. Start applicazione e verifica funzionale"
fi
```

**Checkpoint di verifica B4:**
- [ ] Test restore BorgBackup completato con successo
- [ ] Report di restore generato con: data, backup usato, tempo, esito
- [ ] Validazione dati: almeno /etc/hostname verificato
- [ ] Comprensione della procedura di restore database

---

### Esercizio B5: Monitoraggio Backup — Non Lasciare Fallire il Backup in Silenzio

**Obiettivo.** Configurare un sistema di monitoraggio per i backup che avvisi quando un job fallisce, lo spazio è in esaurimento, o un backup non è stato eseguito nelle ultime 24 ore.

**Step 1 — Crea script di monitoraggio backup:**

```bash
# Su SRV-LINUX-01

cat > /tmp/check_backup_health.sh << 'SCRIPT'
#!/usr/bin/env bash
# Monitoraggio semplice dei backup
BACKUP_DIR="/backup/lab-local"
BORG_REPO="/backup/borg-repo"

echo "=== BACKUP HEALTH CHECK — $(date '+%Y-%m-%d %H:%M:%S') ==="
ISSUES=0

# 1. Verifica ultimo backup rsync
echo ""
echo "1. Ultimo backup rsync:"
LAST_BACKUP=$(find "$BACKUP_DIR" -maxdepth 1 -mindepth 1 -type d | sort | tail -1)
if [[ -n "$LAST_BACKUP" ]]; then
    BACKUP_DATE=$(stat -c %Y "$LAST_BACKUP")
    HOURS_AGO=$(( ($(date +%s) - BACKUP_DATE) / 3600 ))
    echo "   Ultimo backup: $LAST_BACKUP ($HOURS_AGO ore fa)"
    if [[ "$HOURS_AGO" -gt 25 ]]; then
        echo "   [WARN] Backup più vecchio di 25 ore!"
        ((ISSUES++))
    else
        echo "   [OK] Backup recente"
    fi
else
    echo "   [WARN] Nessun backup trovato in $BACKUP_DIR"
    ((ISSUES++))
fi

# 2. Verifica spazio backup
echo ""
echo "2. Spazio storage backup:"
USAGE=$(df "$BACKUP_DIR" | awk 'NR==2 {print $5}' | tr -d '%')
echo "   Utilizzo: ${USAGE}%"
if [[ "$USAGE" -gt 85 ]]; then
    echo "   [CRIT] Spazio critico!"
    ((ISSUES++))
elif [[ "$USAGE" -gt 75 ]]; then
    echo "   [WARN] Spazio in esaurimento"
    ((ISSUES++))
else
    echo "   [OK] Spazio sufficiente"
fi

# 3. Verifica repository Borg
echo ""
echo "3. Repository Borg:"
if [[ -d "$BORG_REPO" ]]; then
    BORG_COUNT=$(BORG_PASSPHRASE="LabBackup2024Sicuro!" borg list "$BORG_REPO" 2>/dev/null | wc -l)
    echo "   Archivi disponibili: $BORG_COUNT"
    if [[ "$BORG_COUNT" -eq 0 ]]; then
        echo "   [WARN] Nessun archivio Borg"
        ((ISSUES++))
    else
        echo "   [OK] Repository Borg intatto"
    fi
else
    echo "   [INFO] Repository Borg non configurato"
fi

echo ""
echo "=== RIEPILOGO: $ISSUES problemi rilevati ==="
exit $ISSUES
SCRIPT

chmod +x /tmp/check_backup_health.sh
bash /tmp/check_backup_health.sh
```

**Step 2 — Configura alert automatico:**

```bash
# Pianifica controllo backup con cron (ogni mattina alle 08:00)
CRON_LINE="0 8 * * * root /tmp/check_backup_health.sh >> /var/log/backup_health.log 2>&1"

echo "Aggiungi questa linea a /etc/crontab per monitoraggio automatico:"
echo "$CRON_LINE"

# Verifica monitoraggio storage
echo ""
echo "=== SOGLIE DI UTILIZZO STORAGE ==="
df -h /backup | awk 'NR==1{print "  ",$0} NR==2{
    usage=substr($5,1,length($5)-1)
    if (usage+0 > 85) print "  [CRIT] "$0
    else if (usage+0 > 75) print "  [WARN] "$0
    else print "  [OK]   "$0
}'
```

**Checkpoint di verifica B5:**
- [ ] Script di monitoraggio backup eseguito senza errori
- [ ] Stato backup e spazio disco correttamente valutati
- [ ] Comprensione delle soglie di alert (75% warn, 85% crit)

---
---

## PART C: SISTEMATIZZARE — Automazione, SOP e Governance del Backup

---

### Progetto C1: SOP-BACKUP-001 — Verifica Giornaliera del Backup

**Obiettivo.** Creare una procedura operativa standard per la verifica giornaliera del backup, eseguibile in 10 minuti da qualsiasi operatore IT senza bisogno di accedere ai dettagli tecnici di ogni sistema.

---

**SOP-BACKUP-001: Verifica Giornaliera Backup**

```
Documento: SOP-BACKUP-001
Titolo:    Verifica Giornaliera Stato Backup
Versione:  1.0
Owner:     IT Operations — Team Infrastruttura
Frequenza: Ogni giorno lavorativo, entro le 09:00
Tempo:     10-15 minuti
```

**Prerequisiti:**
- Accesso a SRV-LINUX-01 (SSH) e DC-LAB-01 (RDP/console)
- Credenziali lab-admin (Linux) e Administrator (Windows)
- Accesso alla directory `/backup/lab-local` su SRV-LINUX-01

---

**Checklist Verifica Giornaliera:**

```
[ ] PARTE 1: BACKUP LINUX (SRV-LINUX-01)

    1.1 Controlla ultimo backup rsync:
        ls -lth /backup/lab-local/ | head -5
        → PASS se: directory con data di oggi o ieri presente
        → FAIL se: ultima directory ha data > 2 giorni fa

    1.2 Verifica integrità ultimo backup:
        LAST=$(ls -td /backup/lab-local/*/ | head -1)
        [[ -f "${LAST}/CHECKSUMS.sha256" ]] && echo "Checksum presente" || echo "MANCANTE!"
        → PASS se: file CHECKSUMS.sha256 presente
        → FAIL se: file assente (backup incompleto)

    1.3 Controlla repository Borg:
        BORG_PASSPHRASE="..." borg list /backup/borg-repo 2>/dev/null | tail -3
        → PASS se: almeno 1 archivio presente, ultimo entro 24h
        → FAIL se: nessun archivio o ultimo > 24h

    1.4 Verifica spazio backup:
        df -h /backup | awk 'NR==2{print $5}'
        → PASS se: utilizzo < 75%
        → WARN se: utilizzo 75-85%
        → CRIT se: utilizzo > 85% → escalation immediata

[ ] PARTE 2: BACKUP WINDOWS (DC-LAB-01)

    2.1 Controlla Windows Server Backup (PowerShell):
        Get-WBBackupSet | Sort-Object BackupTime | Select -Last 1 -ExpandProperty BackupTime
        → PASS se: ultimo backup < 24h fa
        → FAIL se: nessun backup o ultimo > 24h
        → Alternativa: Visualizzatore eventi → Log di Windows → Backup → ultimi eventi

    2.2 Verifica Event ID 4 (backup completato):
        Get-WinEvent -LogName "Microsoft-Windows-Backup" | 
          Where-Object {$_.Id -eq 4 -and $_.TimeCreated -gt (Get-Date).AddDays(-1)} |
          Select -First 1
        → PASS se: event ID 4 presente nelle ultime 24h
        → FAIL se: event ID 5 (errore) o assenza eventi

[ ] PARTE 3: ESCALATION E DOCUMENTAZIONE

    3.1 Se tutti i check sono PASS:
        → Firma checklist
        → Archivia nella cartella /backup/reports/daily/
        → Nessun'altra azione necessaria

    3.2 Se anche un solo check è FAIL:
        → Apri ticket GLPI con urgenza Alta
        → Categoria: Infrastruttura → Backup
        → Notifica responsabile IT entro 30 minuti
        → Non chiudere il turno senza risoluzione o workaround documentato

    3.3 Se CRIT (spazio > 85%):
        → Notifica immediata (telefono, non solo email)
        → Avvia pulizia backup scaduti: esegui retention policy
        → Se dopo pulizia ancora > 85%: escalation responsabile storage
```

---

### Progetto C2: Script di Automazione — backup_health.sh

**Script di controllo automatico dello stato dei backup per SRV-LINUX-01.**

```bash
#!/usr/bin/env bash
# backup_health.sh — Controllo automatico stato backup
# Versione: 1.0
# Frequenza: Ogni mattina alle 08:30 tramite cron

set -euo pipefail

# ─── CONFIGURAZIONE ───────────────────────────────────────────────
BACKUP_DIR="/backup/lab-local"
BORG_REPO="/backup/borg-repo"
BORG_PASSPHRASE="${BORG_PASSPHRASE:-}"
MAX_BACKUP_AGE_HOURS=25
WARN_DISK_PCT=75
CRIT_DISK_PCT=85
REPORT_DIR="/backup/reports/daily"
LOG_FILE="/var/log/backup_health.log"
JSON_OUTPUT=false

# ─── PARSE ARGOMENTI ──────────────────────────────────────────────
[[ "${1:-}" == "--json" ]] && JSON_OUTPUT=true

# ─── INIZIALIZZAZIONE ─────────────────────────────────────────────
mkdir -p "$REPORT_DIR"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
HOSTNAME_FQDN=$(hostname -f 2>/dev/null || hostname)
ISSUES=()
WARNINGS=()
STATUS="OK"
declare -A CHECK_RESULTS

log() {
    echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# ─── CHECK 1: ULTIMO BACKUP RSYNC ─────────────────────────────────
check_rsync_backup() {
    log "CHECK 1: Ultimo backup rsync..."

    if [[ ! -d "$BACKUP_DIR" ]]; then
        ISSUES+=("RSYNC: directory $BACKUP_DIR non esistente")
        CHECK_RESULTS["rsync"]="CRIT"
        return
    fi

    LAST_BACKUP=$(find "$BACKUP_DIR" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sort | tail -1)

    if [[ -z "$LAST_BACKUP" ]]; then
        ISSUES+=("RSYNC: nessun backup trovato in $BACKUP_DIR")
        CHECK_RESULTS["rsync"]="CRIT"
        return
    fi

    BACKUP_EPOCH=$(stat -c %Y "$LAST_BACKUP" 2>/dev/null || echo 0)
    NOW_EPOCH=$(date +%s)
    AGE_HOURS=$(( (NOW_EPOCH - BACKUP_EPOCH) / 3600 ))

    if [[ "$AGE_HOURS" -gt "$MAX_BACKUP_AGE_HOURS" ]]; then
        ISSUES+=("RSYNC: ultimo backup ${AGE_HOURS}h fa (soglia: ${MAX_BACKUP_AGE_HOURS}h)")
        CHECK_RESULTS["rsync"]="WARN"
    else
        log "  [OK] Ultimo backup rsync: $AGE_HOURS ore fa"
        CHECK_RESULTS["rsync"]="OK"
        CHECK_RESULTS["rsync_path"]="$LAST_BACKUP"
        CHECK_RESULTS["rsync_age_hours"]="$AGE_HOURS"
    fi

    # Verifica checksum se presente
    CHECKSUM_FILE="${LAST_BACKUP}/CHECKSUMS.sha256"
    if [[ -f "$CHECKSUM_FILE" ]]; then
        if sha256sum --check "$CHECKSUM_FILE" --quiet 2>/dev/null; then
            log "  [OK] Integrità checksum verificata"
            CHECK_RESULTS["rsync_integrity"]="OK"
        else
            ISSUES+=("RSYNC: checksum fallito per backup $LAST_BACKUP")
            CHECK_RESULTS["rsync_integrity"]="CRIT"
        fi
    else
        WARNINGS+=("RSYNC: file CHECKSUMS.sha256 assente in $LAST_BACKUP")
        CHECK_RESULTS["rsync_integrity"]="MISSING"
    fi
}

# ─── CHECK 2: REPOSITORY BORG ─────────────────────────────────────
check_borg_backup() {
    log "CHECK 2: Repository Borg..."

    if ! command -v borg &>/dev/null; then
        WARNINGS+=("BORG: borgbackup non installato")
        CHECK_RESULTS["borg"]="SKIPPED"
        return
    fi

    if [[ ! -d "$BORG_REPO" ]]; then
        WARNINGS+=("BORG: repository $BORG_REPO non trovato (non configurato?)")
        CHECK_RESULTS["borg"]="SKIPPED"
        return
    fi

    BORG_LIST=$(BORG_PASSPHRASE="$BORG_PASSPHRASE" borg list "$BORG_REPO" 2>/dev/null || echo "")

    if [[ -z "$BORG_LIST" ]]; then
        ISSUES+=("BORG: repository vuoto o non leggibile")
        CHECK_RESULTS["borg"]="CRIT"
        return
    fi

    BORG_COUNT=$(echo "$BORG_LIST" | wc -l)
    LAST_BORG=$(echo "$BORG_LIST" | tail -1)
    log "  [OK] Repository Borg: $BORG_COUNT archivi, ultimo: $(echo "$LAST_BORG" | awk '{print $1, $2, $3}')"
    CHECK_RESULTS["borg"]="OK"
    CHECK_RESULTS["borg_count"]="$BORG_COUNT"
}

# ─── CHECK 3: SPAZIO DISCO ────────────────────────────────────────
check_disk_space() {
    log "CHECK 3: Spazio disco backup..."

    if ! df "$BACKUP_DIR" &>/dev/null; then
        WARNINGS+=("DISK: impossibile leggere utilizzo $BACKUP_DIR")
        CHECK_RESULTS["disk"]="UNKNOWN"
        return
    fi

    DISK_PCT=$(df "$BACKUP_DIR" | awk 'NR==2 {sub(/%/,"",$5); print $5}')
    DISK_AVAIL=$(df -h "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    log "  Utilizzo disco: ${DISK_PCT}% (libero: $DISK_AVAIL)"
    CHECK_RESULTS["disk_pct"]="$DISK_PCT"
    CHECK_RESULTS["disk_avail"]="$DISK_AVAIL"

    if [[ "$DISK_PCT" -ge "$CRIT_DISK_PCT" ]]; then
        ISSUES+=("DISK: utilizzo CRITICO ${DISK_PCT}% (soglia: ${CRIT_DISK_PCT}%)")
        CHECK_RESULTS["disk"]="CRIT"
    elif [[ "$DISK_PCT" -ge "$WARN_DISK_PCT" ]]; then
        WARNINGS+=("DISK: utilizzo ALTO ${DISK_PCT}% (soglia warn: ${WARN_DISK_PCT}%)")
        CHECK_RESULTS["disk"]="WARN"
    else
        log "  [OK] Spazio disco sufficiente: ${DISK_PCT}%"
        CHECK_RESULTS["disk"]="OK"
    fi
}

# ─── ESEGUI CHECK ─────────────────────────────────────────────────
log "=========================================="
log "BACKUP HEALTH CHECK — $TIMESTAMP"
log "Host: $HOSTNAME_FQDN"
log "=========================================="

check_rsync_backup
check_borg_backup
check_disk_space

# ─── CALCOLA STATUS FINALE ────────────────────────────────────────
if [[ "${#ISSUES[@]}" -gt 0 ]]; then
    STATUS="CRITICAL"
elif [[ "${#WARNINGS[@]}" -gt 0 ]]; then
    STATUS="WARNING"
fi

# ─── OUTPUT ───────────────────────────────────────────────────────
if [[ "$JSON_OUTPUT" == true ]]; then
    # Output JSON per integrazione con sistemi di monitoraggio
    cat << EOF
{
  "timestamp": "$TIMESTAMP",
  "hostname": "$HOSTNAME_FQDN",
  "status": "$STATUS",
  "issues_count": ${#ISSUES[@]},
  "warnings_count": ${#WARNINGS[@]},
  "checks": {
    "rsync": "${CHECK_RESULTS[rsync]:-UNKNOWN}",
    "rsync_integrity": "${CHECK_RESULTS[rsync_integrity]:-UNKNOWN}",
    "borg": "${CHECK_RESULTS[borg]:-UNKNOWN}",
    "disk": "${CHECK_RESULTS[disk]:-UNKNOWN}",
    "disk_pct": "${CHECK_RESULTS[disk_pct]:-0}"
  },
  "issues": $(printf '%s\n' "${ISSUES[@]:-}" | jq -R . | jq -s .),
  "warnings": $(printf '%s\n' "${WARNINGS[@]:-}" | jq -R . | jq -s .)
}
EOF
else
    log ""
    log "=========================================="
    log "RIEPILOGO: STATUS = $STATUS"
    log "  Issues:   ${#ISSUES[@]}"
    log "  Warnings: ${#WARNINGS[@]}"

    for issue in "${ISSUES[@]}"; do
        log "  [ISSUE]  $issue"
    done
    for warn in "${WARNINGS[@]}"; do
        log "  [WARN]   $warn"
    done
    log "=========================================="
fi

# ─── SALVA REPORT ─────────────────────────────────────────────────
REPORT_FILE="${REPORT_DIR}/backup_health_$(date +%Y%m%d).txt"
{
    echo "=== BACKUP HEALTH REPORT ==="
    echo "Timestamp: $TIMESTAMP"
    echo "Host:      $HOSTNAME_FQDN"
    echo "Status:    $STATUS"
    echo ""
    echo "Issues: ${#ISSUES[@]}"
    for i in "${ISSUES[@]}"; do echo "  - $i"; done
    echo "Warnings: ${#WARNINGS[@]}"
    for w in "${WARNINGS[@]}"; do echo "  - $w"; done
    echo ""
    echo "Check Details:"
    for k in "${!CHECK_RESULTS[@]}"; do
        echo "  $k = ${CHECK_RESULTS[$k]}"
    done
} > "$REPORT_FILE"

# Exit code: 0=OK, 1=WARNING, 2=CRITICAL
case "$STATUS" in
    "OK")       exit 0 ;;
    "WARNING")  exit 1 ;;
    *)          exit 2 ;;
esac
```

**Installazione e configurazione cron:**

```bash
# Copia lo script in posizione permanente
sudo cp /tmp/backup_health.sh /usr/local/bin/backup_health.sh
sudo chmod +x /usr/local/bin/backup_health.sh

# Crea directory report
sudo mkdir -p /backup/reports/daily
sudo chown lab-admin:lab-admin /backup/reports/daily

# Aggiungi a crontab (08:30 ogni giorno lavorativo)
CRON_ENTRY="30 8 * * 1-5 lab-admin BORG_PASSPHRASE='LabBackup2024Sicuro!' /usr/local/bin/backup_health.sh >> /var/log/backup_health.log 2>&1"
echo ""
echo "Aggiungi questa voce a /etc/crontab:"
echo "$CRON_ENTRY"
echo ""
echo "Test manuale:"
echo "  sudo -u lab-admin BORG_PASSPHRASE='LabBackup2024Sicuro!' /usr/local/bin/backup_health.sh"
echo "  sudo -u lab-admin /usr/local/bin/backup_health.sh --json | python3 -m json.tool"
```

---

### Progetto C3: Script PowerShell — backup_status.ps1

**Script di verifica backup per DC-LAB-01 (Windows Server Backup + Event Log).**

```powershell
<#
.SYNOPSIS
    Verifica stato backup Windows Server su DC-LAB-01
.DESCRIPTION
    Controlla: Windows Server Backup, Event Log, disco destinazione
.PARAMETER Json
    Output in formato JSON per integrazione con sistemi di monitoraggio
.EXAMPLE
    .\backup_status.ps1
    .\backup_status.ps1 -Json
#>

[CmdletBinding()]
param(
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ─── INIZIALIZZAZIONE ─────────────────────────────────────────────
$Timestamp   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$Hostname    = $env:COMPUTERNAME
$MaxAgeHours = 25
$Issues      = [System.Collections.Generic.List[string]]::new()
$Warnings    = [System.Collections.Generic.List[string]]::new()
$CheckResults = @{}
$OverallStatus = "OK"

function Write-Log {
    param([string]$Message)
    if (-not $Json) {
        Write-Host "[$((Get-Date -Format 'HH:mm:ss'))] $Message"
    }
}

# ─── CHECK 1: WINDOWS SERVER BACKUP ──────────────────────────────
function Test-WindowsServerBackup {
    Write-Log "CHECK 1: Windows Server Backup..."

    $wsbFeature = Get-WindowsFeature -Name Windows-Server-Backup -ErrorAction SilentlyContinue
    if ($wsbFeature.InstallState -ne "Installed") {
        $Warnings.Add("WSB: Windows Server Backup non installato")
        $CheckResults["wsb"] = "SKIPPED"
        return
    }

    try {
        Import-Module WindowsServerBackup -ErrorAction Stop
        $backupSets = Get-WBBackupSet -ErrorAction Stop | Sort-Object BackupTime

        if ($null -eq $backupSets -or $backupSets.Count -eq 0) {
            $Issues.Add("WSB: nessun backup completato trovato")
            $CheckResults["wsb"] = "CRIT"
            return
        }

        $lastBackup = $backupSets | Select-Object -Last 1
        $ageHours   = [math]::Round(((Get-Date) - $lastBackup.BackupTime).TotalHours, 1)

        Write-Log "  Ultimo backup: $($lastBackup.BackupTime) ($ageHours ore fa)"
        $CheckResults["wsb_last_backup"] = "$($lastBackup.BackupTime)"
        $CheckResults["wsb_age_hours"]   = "$ageHours"

        if ($ageHours -gt $MaxAgeHours) {
            $Issues.Add("WSB: ultimo backup ${ageHours}h fa (soglia: ${MaxAgeHours}h)")
            $CheckResults["wsb"] = "WARN"
        } else {
            Write-Log "  [OK] Backup recente"
            $CheckResults["wsb"] = "OK"
        }
    } catch {
        $Warnings.Add("WSB: errore lettura backup set: $_")
        $CheckResults["wsb"] = "UNKNOWN"
    }
}

# ─── CHECK 2: EVENT LOG BACKUP ────────────────────────────────────
function Test-BackupEventLog {
    Write-Log "CHECK 2: Event Log backup (ultime 24h)..."

    $cutoff = (Get-Date).AddHours(-25)

    # Event ID 4 = backup completato con successo (Windows Server Backup)
    $successEvents = Get-WinEvent -FilterHashtable @{
        LogName   = "Microsoft-Windows-Backup"
        Id        = 4
        StartTime = $cutoff
    } -ErrorAction SilentlyContinue

    # Event ID 5 = backup fallito
    $failEvents = Get-WinEvent -FilterHashtable @{
        LogName   = "Microsoft-Windows-Backup"
        Id        = 5
        StartTime = $cutoff
    } -ErrorAction SilentlyContinue

    $successCount = if ($successEvents) { $successEvents.Count } else { 0 }
    $failCount    = if ($failEvents)    { $failEvents.Count    } else { 0 }

    Write-Log "  Backup completati (ID 4): $successCount | Falliti (ID 5): $failCount"
    $CheckResults["eventlog_success"] = "$successCount"
    $CheckResults["eventlog_failed"]  = "$failCount"

    if ($failCount -gt 0) {
        $Issues.Add("EVENTLOG: $failCount backup falliti nelle ultime 25 ore")
        $CheckResults["eventlog"] = "CRIT"
    } elseif ($successCount -eq 0) {
        $Warnings.Add("EVENTLOG: nessun evento backup nelle ultime 25 ore")
        $CheckResults["eventlog"] = "WARN"
    } else {
        Write-Log "  [OK] Backup completato senza errori"
        $CheckResults["eventlog"] = "OK"
    }
}

# ─── CHECK 3: SPAZIO DISCO BACKUP ────────────────────────────────
function Test-BackupDisk {
    Write-Log "CHECK 3: Spazio disco..."

    $backupDrive = "C:"  # Adatta al drive effettivo del backup

    try {
        $disk = Get-PSDrive -Name ($backupDrive -replace ':','') -ErrorAction Stop
        $usedPct = [math]::Round(($disk.Used / ($disk.Used + $disk.Free)) * 100, 1)
        $freeGB  = [math]::Round($disk.Free / 1GB, 1)

        Write-Log "  Disco $backupDrive: ${usedPct}% usato, ${freeGB} GB liberi"
        $CheckResults["disk_pct"]  = "$usedPct"
        $CheckResults["disk_free"] = "${freeGB}GB"

        if ($usedPct -gt 85) {
            $Issues.Add("DISK: utilizzo CRITICO ${usedPct}% su $backupDrive")
            $CheckResults["disk"] = "CRIT"
        } elseif ($usedPct -gt 75) {
            $Warnings.Add("DISK: utilizzo ALTO ${usedPct}% su $backupDrive")
            $CheckResults["disk"] = "WARN"
        } else {
            Write-Log "  [OK] Spazio sufficiente"
            $CheckResults["disk"] = "OK"
        }
    } catch {
        $Warnings.Add("DISK: impossibile leggere spazio su $backupDrive")
        $CheckResults["disk"] = "UNKNOWN"
    }
}

# ─── ESEGUI CHECK ─────────────────────────────────────────────────
Write-Log "=========================================="
Write-Log "BACKUP HEALTH CHECK (Windows) — $Timestamp"
Write-Log "Host: $Hostname"
Write-Log "=========================================="

Test-WindowsServerBackup
Test-BackupEventLog
Test-BackupDisk

# ─── STATUS FINALE ────────────────────────────────────────────────
if ($Issues.Count -gt 0)       { $OverallStatus = "CRITICAL" }
elseif ($Warnings.Count -gt 0) { $OverallStatus = "WARNING"  }

# ─── OUTPUT ───────────────────────────────────────────────────────
if ($Json) {
    [ordered]@{
        timestamp      = $Timestamp
        hostname       = $Hostname
        status         = $OverallStatus
        issues_count   = $Issues.Count
        warnings_count = $Warnings.Count
        checks         = $CheckResults
        issues         = $Issues.ToArray()
        warnings       = $Warnings.ToArray()
    } | ConvertTo-Json -Depth 4
} else {
    Write-Log ""
    Write-Log "=========================================="
    Write-Log "RIEPILOGO: STATUS = $OverallStatus"
    Write-Log "  Issues:   $($Issues.Count)"
    Write-Log "  Warnings: $($Warnings.Count)"
    $Issues   | ForEach-Object { Write-Log "  [ISSUE]  $_" }
    $Warnings | ForEach-Object { Write-Log "  [WARN]   $_" }
    Write-Log "=========================================="
}

# Exit code: 0=OK, 1=WARNING, 2=CRITICAL
switch ($OverallStatus) {
    "OK"       { exit 0 }
    "WARNING"  { exit 1 }
    default    { exit 2 }
}
```

**Pianificazione task su Windows (Task Scheduler):**

```powershell
# Crea Scheduled Task per backup_status.ps1
$scriptPath = "C:\Scripts\backup_status.ps1"

# Crea directory scripts
New-Item -ItemType Directory -Path "C:\Scripts" -Force | Out-Null

# Salva lo script
# (copia il contenuto dello script nel file $scriptPath)

# Crea Scheduled Task: ogni giorno alle 08:30
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
              -Argument "-NonInteractive -ExecutionPolicy Bypass -File `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At "08:30"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask `
    -TaskName "BackupHealthCheck" `
    -Action   $action `
    -Trigger  $trigger `
    -Settings $settings `
    -RunLevel Highest `
    -Description "Verifica giornaliera stato backup" `
    -Force

Write-Host "[OK] Task 'BackupHealthCheck' creato"
Write-Host "Esegui manualmente: Start-ScheduledTask -TaskName 'BackupHealthCheck'"
```

---

### Progetto C4: Integrazione ITIL — Backup come Pratica di Service Continuity

**Connessione tra le operazioni di backup e il framework ITIL v4.**

```
ITIL v4 PRACTICE: IT Service Continuity Management (ITSCM)
  → Garantisce che il business possa continuare anche dopo eventi disruptivi
  → Il backup è il FONDAMENTO dell'ITSCM

COLLEGAMENTO DIRETTO:

  Pratica ITIL           | Implementazione Backup Lab
  ─────────────────────────────────────────────────────────
  Service Continuity    | 3-2-1-1-0 rule, test restore
  Management            | RTO/RPO documentati per ogni sistema
                        | DRP aggiornato e testato almeno 2x/anno
  ─────────────────────────────────────────────────────────
  Availability          | Monitoraggio backup job giornaliero
  Management            | Metriche: % backup completati, RTO misurato
                        | KPI: "Backup success rate > 99%"
  ─────────────────────────────────────────────────────────
  Change Management     | Modifiche alla strategia backup → Change Request
                        | Test restore dopo ogni change significativo
                        | Approvazione formale prima di modificare policy
  ─────────────────────────────────────────────────────────
  Configuration         | Ogni sistema con backup → CI in CMDB
  Management (CMDB)     | Attributi CI: backup_policy, rto, rpo, last_backup
                        | Relazione: CI → Backup Repository (CI)
  ─────────────────────────────────────────────────────────
  Incident Management   | Backup failure → Incident P2 (impact=High)
                        | Restore riuscito → aggiornare CMDB e incident
                        | Ransomware → Major Incident, attiva DRP


REGISTRAZIONE IN GLPI (Configuration Item Backup):

  Nome CI:          BACKUP-SRV-LINUX-01-BORG
  Tipo:             Backup Repository
  Host:             SRV-LINUX-01
  Tool:             BorgBackup 1.2.x
  Retention:        GFS (7d/4w/12m)
  RTO Target:       4h
  RPO Target:       24h
  Last Test:        [data del test di restore]
  Test Result:      [PASS/FAIL + tempo misurato]
  Owner:            IT Operations
  Nota:             Crittografia repokey, passphrase in vault


SLA INTERNI PER BACKUP (esempio):

  Sistema        | RTO Target | RPO Target | Test Freq | Retention
  ──────────────────────────────────────────────────────────────────
  GLPI (DB)      |    4h      |    24h     | Mensile   | 30gg+12m
  /etc Linux     |    2h      |    24h     | Trimestrale| 14gg+4w
  DC-LAB-01 AD   |    8h      |    24h     | Mensile   | 30gg+12m
  File condivisi |    4h      |    24h     | Mensile   | 7gg+4w+12m
```

---

## Checklist di Validazione Lab — ops06a

```
FONDAMENTI (Part A):
  [ ] A1: Sai spiegare la regola 3-2-1-1-0 e perché l'1 immutabile protegge dal ransomware
  [ ] A2: Sai distinguere Full/Incrementale/Differenziale con esempi di quando usare ciascuno
  [ ] A3: Sai perché mysqldump --single-transaction è necessario per DB attivi
  [ ] A4: Sai cos'è il System State AD e cosa contiene NTDS.DIT
  [ ] A5: Sai calcolare la differenza tra RTO e RPO con un esempio reale

OPERAZIONI (Part B):
  [ ] B1: Backup rsync di /etc completato con file di log e CHECKSUMS.sha256
  [ ] B2: Repository Borg inizializzato, secondo backup dimostra deduplication
  [ ] B3: Windows Server Backup installato, comprensione del contenuto System State
  [ ] B4: Test restore BorgBackup completato con report scritto (data, archivio, tempo, esito)
  [ ] B5: Script backup_health.sh eseguito senza errori, status OK

SISTEMATIZZARE (Part C):
  [ ] C1: SOP-BACKUP-001 letta e capita, checklist completata almeno una volta
  [ ] C2: Script backup_health.sh installato in /usr/local/bin con cron configurato
  [ ] C3: Script backup_status.ps1 copiato su DC-LAB-01
  [ ] C4: Creato almeno 1 CI Backup in GLPI con RTO/RPO documentati
```

---

## Appendice A: Comandi di Riferimento Rapido

```bash
# ─── RSYNC ────────────────────────────────────────────────────────
# Backup base con log
rsync -avh --stats --log-file=/backup/rsync.log /sorgente/ /destinazione/

# Backup con esclusioni
rsync -avh --exclude="*.tmp" --exclude="/proc" /etc/ /backup/etc/

# Verifica senza copiare (dry-run)
rsync -avhn /sorgente/ /destinazione/

# ─── BORGBACKUP ───────────────────────────────────────────────────
export BORG_PASSPHRASE="tuapassphrase"

# Inizializza repository
borg init --encryption=repokey /backup/borg-repo

# Crea archivio
borg create --stats --compression lz4 /backup/borg-repo::backup-$(date +%Y%m%d) /etc /home

# Lista archivi
borg list /backup/borg-repo

# Info repository (statistiche deduplication)
borg info /backup/borg-repo

# Estrai file singolo
cd /restore && borg extract /backup/borg-repo::nome-archivio etc/hostname

# Retention (GFS)
borg prune --keep-daily 7 --keep-weekly 4 --keep-monthly 12 /backup/borg-repo

# ─── MYSQLDUMP ────────────────────────────────────────────────────
# Backup consistente (InnoDB)
mysqldump --single-transaction --routines --triggers -uroot -p nomedb > backup.sql

# Backup con compressione
mysqldump --single-transaction -uroot -p nomedb | gzip > backup.sql.gz

# Restore
mysql -uroot -p nomedb < backup.sql
zcat backup.sql.gz | mysql -uroot -p nomedb

# Via Docker (GLPI)
docker exec glpi-db mysqldump --single-transaction -uroot -p"pwd" glpi | gzip > glpi.sql.gz
```

```powershell
# ─── WINDOWS SERVER BACKUP ────────────────────────────────────────
# Installa
Install-WindowsFeature Windows-Server-Backup

# Lista backup
Get-WBBackupSet | Sort-Object BackupTime | Format-Table BackupTime, BackupTarget

# Event log backup
Get-WinEvent -FilterHashtable @{LogName="Microsoft-Windows-Backup"; Id=4} | Select -Last 5

# Verifica AD Recycle Bin
Get-ADOptionalFeature -Filter {Name -eq "Recycle Bin Feature"}

# wbadmin (backup da cmd)
# wbadmin start systemstatebackup -backupTarget:C:\Backup -quiet
```

---

## Appendice B: Tabella Comparativa Strumenti Backup

```
Strumento       | Tipo         | OS       | Dedup | Encrypt | Costo   | Caso d'uso
─────────────────────────────────────────────────────────────────────────────────────
rsync           | File         | Linux    | No    | No*     | Free    | Backup file semplici
BorgBackup      | File/Archive | Linux    | Sì    | Sì AES  | Free    | Backup Linux ottimale
WSB             | Full/SysState| Windows  | No    | No      | Incluso | System State, bare metal
mysqldump       | DB logico    | Any      | No    | No      | Free    | MySQL/MariaDB piccoli
XtraBackup      | DB fisico    | Linux    | No    | No      | Free    | MySQL/MariaDB grandi
Veeam CE        | VM           | VMware   | Sì    | Sì      | Free*   | Fino a 10 workload
PBS             | VM           | Proxmox  | Sì    | Sì      | Free    | Ambienti Proxmox

*rsync: encryption via SSH per trasferimenti remoti
*Veeam Community Edition: gratuito fino a 10 workload, funzioni limitate
```

---

## Riferimenti

- `06-backup-disaster-recovery.md` — sezioni 2 (strategia) e 3 (verifica backup)
- BorgBackup documentation: https://borgbackup.readthedocs.io/
- Veeam Backup Best Practices: veeam.com/documentation
- NIST SP 800-34: Contingency Planning Guide for Federal Information Systems
- ISO 22301: Business Continuity Management System
- **Tutorial successivo:** `tutorial_ops06_ch1b_disaster_recovery_bcp_lab.md`
