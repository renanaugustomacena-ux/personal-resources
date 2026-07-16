# Tutorial: Storage e Database Operations — Hands-On Lab

> **Documento di riferimento:** `04-servizi-infrastruttura.md` (sezioni Manutenzione Storage e Manutenzione Database)
> **Dominio:** Infrastruttura — Dati e Persistenza
> **Ambito:** Gestione disco (LVM, SMART, quota, deduplicazione), performance storage (iostat, IOPS, latenza), manutenzione MariaDB (VACUUM, indici, slow query, binary log, buffer pool), SQL Server concepts
> **Durata lab:** 4-5 ore
> **Livello:** Intermedio-Avanzato — richiede ops03a (Windows Server), ops03b (Linux)
> **Prerequisiti:** SRV-LINUX-01 con MariaDB via Docker (GLPI stack), DC-LAB-01 con dischi accessibili
> **Ambiente:** SRV-LINUX-01 (MariaDB + disco Linux), DC-LAB-01 (Windows disk management)
> **Nota lab:** Useremo il database MariaDB già presente con GLPI per gli esercizi pratici.

---

## Lab Environment Setup

```bash
# Su SRV-LINUX-01 — verifica pre-lab

echo "=== VERIFICA PRE-LAB STORAGE/DB ==="

# Spazio disco disponibile
echo "[Disco]"
df -h | grep -E "Filesystem|/$|/var"

# MariaDB accessibile (dentro il container GLPI)
echo "[MariaDB]"
if docker ps 2>/dev/null | grep -q "mariadb\|db"; then
    echo "[OK] Container database in esecuzione"
    docker ps --format "{{.Names}}\t{{.Image}}\t{{.Status}}" | grep -E "db|maria|mysql"
else
    echo "[WARN] Container database non attivo — avviare con: cd ~/glpi-docker && docker compose up -d"
fi

# iostat disponibile?
if command -v iostat &>/dev/null; then
    echo "[OK] iostat disponibile"
else
    echo "[INFO] iostat non installato — installare con: sudo apt install -y sysstat"
fi
```

---

## PART A: FONDAMENTI — Storage e Database come Fondamenta dei Dati

> Un'azienda senza dati è come una biblioteca senza libri. Lo storage è l'edificio della biblioteca, il database è il sistema di catalogazione. Puoi avere l'edificio più bello del mondo (storage velocissimo) ma se il catalogo è corrotto (database corrotto), non trovi niente. E se l'edificio brucia senza un backup, hai perso tutto. Storage e database vanno gestiti insieme come un ecosistema.

---

### Concetto A1: Storage — Dove Vivono i Dati

> **Analogia.** Lo storage è come un magazzino aziendale. Ci sono diversi tipi di scaffali: scaffali in metallo resistentissimi con accesso immediato (SSD NVMe — Tier 1), scaffali in legno robusti (HDD 15K — Tier 2), e archivi nel seminterrato (SATA lenti — Tier 3). I documenti più usati stanno sui scaffali in metallo, le fatture degli ultimi 3 anni in legno, i dati storici nel seminterrato.

**I 3 livelli dello Storage Tiering:**

```
TIER 1 — SSD/NVMe (accesso frequente)
  IOPS: > 100.000    Latenza: < 1ms    Throughput: > 500 MB/s
  Usato per: database attivi, VM di produzione, app critiche
  Costo: alto

TIER 2 — SAS/HDD veloci (accesso moderato)
  IOPS: > 200        Latenza: < 5ms    Throughput: > 150 MB/s
  Usato per: file server, archivi recenti, backup primario
  Costo: medio

TIER 3 — SATA/Object Storage (accesso raro)
  IOPS: > 100        Latenza: < 10ms   Throughput: > 100 MB/s
  Usato per: backup storici, archivi, log vecchi
  Costo: basso
```

**RAID — protezione contro i guasti disco:**

```
RAID 0 — Striping (NO protezione)
  2+ dischi → capacità raddoppiata, velocità raddoppiata
  Se 1 disco muore → TUTTI i dati persi
  Uso: caching temporaneo, mai per dati importanti

RAID 1 — Mirroring
  2 dischi identici → se 1 muore, l'altro continua
  Capacità: metà del totale (2×1TB = 1TB usabile)
  Uso: boot OS, dati critici non voluminosi

RAID 5 — Striping con parità distribuita
  3+ dischi → tolleranza 1 disco
  Capacità: (N-1) × dim. disco (3×1TB = 2TB usabile)
  Uso: file server, NAS aziendali

RAID 6 — Doppia parità
  4+ dischi → tolleranza 2 dischi
  Uso: storage critico dove RAID 5 non basta
  
RAID 10 — Mirror + Stripe
  4+ dischi → velocità + protezione (1 disco per coppia)
  Uso: database ad alto carico
```

**Thin Provisioning — il rischio dell'overcommitment:**

```
Scenario: SAN con 10 TB fisici
  VM1 allocata: 2 TB (thin)
  VM2 allocata: 2 TB (thin)
  VM3 allocata: 2 TB (thin)
  ...
  Totale allocato: 12 TB > 10 TB fisici

Funziona finché non tutti usano lo spazio contemporaneamente.
Se lo spazio fisico si esaurisce → CORRUZIONE DATI per tutte le VM!

Soglie di allarme thin provisioning:
  Warning:   utilizzo fisico > 70%
  Critico:   utilizzo fisico > 85%
  Emergenza: utilizzo fisico > 95% — agisci IMMEDIATAMENTE
```

---

### Concetto A2: Performance Storage — Capire IOPS, Latenza e Throughput

> **Analogia.** Immagina un ristorante. IOPS è il numero di piatti serviti al minuto (quante operazioni al secondo). La latenza è quanto tempo passa dall'ordine alla consegna (quanto velocemente risponde il disco). Il throughput è il volume totale di cibo servito (quanti MB/s trasferiti). Un ristorante può avere alta capacità totale (throughput) ma servire un piatto alla volta con attesa di 20 minuti (alta latenza, bassi IOPS).

**I 3 indicatori chiave delle performance storage:**

```
IOPS — Input/Output Operations Per Second
  Conta le operazioni disco, non i byte
  Critico per: database OLTP, VM, log files
  Troppo basso → query lente, login lenti, timeout

Latenza — tempo di risposta per operazione
  Misurata in millisecondi (ms)
  Critico per: qualsiasi applicazione interattiva
  Alta latenza → utenti percepiscono lentezza immediata
  Disk Queue Length > 2 (Windows) → disco saturo

Throughput — byte trasferiti al secondo (MB/s)
  Critico per: backup, ripristino, trasferimenti grandi file
  Meno critico per database OLTP (tante piccole operazioni)
```

**Diagnosi di un problema di performance storage:**

```
Sintomi: query database lente, login AD lento, file copy lento
         applicazioni che sembrano "congelarsi" sporadicamente
         
Strumenti di diagnosi:
  Linux: iostat -xz 5 3
         %util colonna → se > 90%: disco saturo
         await colonna → tempo medio attesa in ms
         
  Windows: Get-Counter "\PhysicalDisk(*)\Avg. Disk Queue Length"
           Avg Disk Queue Length > 2 → disco saturo
           Get-Counter "\PhysicalDisk(*)\Avg. Disk sec/Read"
```

**Snapshot — la "macchina del tempo" per lo storage:**

```
Uno snapshot è una fotografia dello stato del disco in un momento preciso.
NON è un backup! — stesso disco fisico, stesso rischio di guasto.

Snapshot è utile per:
  - Salvare lo stato prima di un aggiornamento (rollback rapido)
  - Creare una copia coerente del DB per il backup
  - Test di patch in produzione (rollback se fallisce)

Anti-pattern pericoloso:
  "Uso gli snapshot come backup"
  → Se il disco fisico si guasta: snapshot e dati ENTRAMBI persi
  → Gli snapshot devono sempre accompagnare un backup reale
```

---

### Concetto A3: Database — Come Funzionano Internamente

> **Analogia.** Un database è come un ufficio con archivisti specializzati. Il catalogo (schema) definisce come sono organizzate le pratiche (tabelle). Ogni volta che arriva una nuova pratica (INSERT) o si modifica una esistente (UPDATE), l'archivista prima scrive il cambio su un libro mastro (transaction log/WAL), poi aggiorna gli archivi fisici (datafile). Se l'ufficio chiude improvvisamente (crash), il libro mastro permette di ricostruire tutto al riapertura.

**ACID — le 4 proprietà fondamentali di un database:**

```
A — Atomicity (Atomicità)
    Una transazione è tutto o niente.
    Se trasferisci €100 da A a B:
    → prelevo da A: OK
    → accredito su B: ERRORE (server crash)
    → la transazione è annullata: A riottienes €100
    Senza atomicità: €100 spariti nel nulla.

C — Consistency (Consistenza)
    Il database passa da uno stato valido a un altro stato valido.
    Non può violare i vincoli (chiave primaria, foreign key, CHECK).

I — Isolation (Isolamento)
    Transazioni concorrenti non si "vedono" a metà esecuzione.
    T1 e T2 in parallelo: il risultato è come se fossero sequenziali.

D — Durability (Durabilità)
    Una transazione confermata (COMMIT) sopravvive ai crash.
    Garantita dal Write-Ahead Log (WAL) / Transaction Log.
```

**Transaction Log / WAL — il libro mastro del database:**

```
Prima di modificare i dati nel datafile, il database scrive
SEMPRE prima nel log (Write-Ahead Log):

1. BEGIN TRANSACTION
2. Log: "sto per aggiornare riga 1234 da A a B"
3. Aggiorna il datafile in memoria (buffer)
4. Log: "COMMITTED"
5. Flush in background su disco

In caso di crash tra step 2 e 4:
→ Al riavvio, il database legge il log
→ Trova operazioni non committed
→ Le annulla (rollback) → consistenza garantita

Problema se il log cresce troppo:
  SQL Server: backup del transaction log (ogni ora in produzione)
  MariaDB: binary logs con expire_logs_days
  PostgreSQL: WAL archiving
```

**Indici — acceleratori delle query:**

```
Senza indice — "full table scan":
  SELECT * FROM tickets WHERE user_id = 42;
  → Il database legge TUTTE le righe e cerca il match
  → 1 milione di righe = 1 milione di letture disco
  → LENTO per tabelle grandi

Con indice su user_id:
  → Il database usa l'indice (come un indice di un libro)
  → Va direttamente alle righe con user_id = 42
  → 100 righe trovate = 100 letture
  → VELOCE

Frammentazione degli indici nel tempo:
  INSERT/UPDATE/DELETE → l'indice si frammenta
  Frammentazione 10-30%: REORGANIZE (operazione online, non blocca)
  Frammentazione > 30%: REBUILD (più efficiente, può bloccare in edizioni base)

Come misurare la frammentazione (MariaDB):
  SELECT TABLE_NAME, DATA_FREE, DATA_LENGTH
  FROM information_schema.TABLES
  WHERE DATA_FREE > 0;
```

---

### Concetto A4: MariaDB/MySQL vs SQL Server vs PostgreSQL

> **Perché mi interessa?** Nel nostro lab abbiamo MariaDB (usato da GLPI). In produzione vedrai SQL Server (ambienti Windows/Microsoft), PostgreSQL (ambienti Linux enterprise), o MySQL/MariaDB (web application, LAMP stack). I concetti sono simili, ma i comandi sono diversi.

| Aspetto | MariaDB/MySQL | SQL Server | PostgreSQL |
|---|---|---|---|
| Licenza | Open Source (GPL) | Commerciale | Open Source (MIT-like) |
| OS | Linux/Windows | Windows (anche Linux) | Linux/Windows |
| Storage engine | InnoDB (default) | Proprietario | Proprietario |
| VACUUM equivalente | `OPTIMIZE TABLE` | Auto-manutenzione | `VACUUM ANALYZE` |
| Log | Binary Log | Transaction Log | WAL |
| Buffer pool | `innodb_buffer_pool_size` | Buffer Pool | `shared_buffers` |
| Slow query | `slow_query_log` | Query Store | `pg_stat_statements` |
| Nel lab | **MariaDB** (GLPI) | Concetti in Part A | Concetti in Part A |

---

### Concetto A5: Monitoraggio Storage e Database — Le Metriche da Osservare

> **Perché mi interessa?** I problemi di storage e database si manifestano spesso in modo silenzioso: le query iniziano a rallentare del 10%, poi del 20%, poi del 50%, finché un giorno l'applicazione è inutilizzabile. Monitorare le metriche giuste permette di intercettare i problemi prima che gli utenti se ne accorgano.

**Storage — metriche critiche:**

| Metrica | Tool | Warning | Critico |
|---|---|---|---|
| Spazio disco libero | `df -h` | < 20% libero | < 10% libero |
| %util disco | `iostat -x` | > 70% | > 90% |
| Await (latenza I/O) | `iostat -x` | > 20ms | > 50ms |
| Disk Queue Length | PerfMon (Win) | > 2 | > 5 |
| SMART status | `smartctl -H` | SMART WARNING | FAILED → sostituzione immediata |

**Database — metriche critiche:**

| Metrica | Tool | Warning | Critico |
|---|---|---|---|
| Buffer Pool Hit Rate | `SHOW STATUS` | < 99% | < 95% |
| Query lente (>1s) | Slow Query Log | > 10/giorno | > 100/giorno |
| Connessioni attive | `SHOW STATUS` | > 70% max_conn | > 90% max_conn |
| Dimensione binary log | `SHOW BINARY LOGS` | > 10 GB | > 50 GB |
| Frammentazione tabelle | `information_schema` | > 30% | > 50% |
| Ultimo backup riuscito | msdb.backupset | > 24h | > 48h |

---
---

## PART B: OPERAZIONI — Monitorare Storage e Database in Produzione

> **Obiettivo generale.** Alla fine di questa sezione sarai in grado di: verificare lo stato dello storage su entrambe le piattaforme (Linux e Windows), identificare problemi di performance disco, connetterti e interrogare il database MariaDB di GLPI, eseguire operazioni di manutenzione (ottimizzazione tabelle, pulizia log binari, analisi slow query), e interpretare le metriche di salute del database.

---

### Esercizio B1: Monitoraggio Disco su SRV-LINUX-01

**Obiettivo.** Acquisire una visione completa dello stato dello storage su Linux: spazio, utilizzo LVM (se presente), performance I/O in tempo reale.

**Background.** Un sistemista IT riceve una segnalazione: "GLPI si è rallentato dalle 14:00". Prima di toccare il database, bisogna escludere che il problema sia a livello storage. Questo esercizio simula il processo di diagnosi.

**Step 1 — Panoramica spazio disco.**

```bash
# Su SRV-LINUX-01

echo "=== 1. SPAZIO DISCO OVERVIEW ==="
df -h

# Output più leggibile con tipo filesystem
df -hT

# Quali filesystem occupano più spazio? (ordinati per utilizzo)
df -h | sort -k5 -rh | head -10
```

**Output atteso:**
```
Filesystem     Type      Size  Used Avail Use% Mounted on
/dev/sda1      ext4       20G   8.2G   11G  44% /
tmpfs          tmpfs     1.9G     0  1.9G   0% /dev/shm
/dev/sda2      ext4       10G   4.1G  5.4G  43% /var
```

**Step 2 — Dove sta tutto lo spazio su /var?**

```bash
# /var contiene log, Docker images, GLPI data — può crescere molto
echo "=== 2. ANALISI /var ==="

# Top 10 cartelle più grandi sotto /var
sudo du -h /var --max-depth=2 2>/dev/null | sort -rh | head -15

# Quanto occupano i container Docker?
echo ""
echo "=== Spazio Docker ==="
docker system df 2>/dev/null || echo "[INFO] Docker non accessibile"

# Log di sistema — possono crescere senza controllo
echo ""
echo "=== Log di Sistema ==="
sudo du -sh /var/log/*  2>/dev/null | sort -rh | head -10
```

**Step 3 — Stato dei block device (lsblk).**

```bash
echo "=== 3. BLOCK DEVICES ==="
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL

# Con informazioni estese
lsblk -d -o NAME,SIZE,ROTA,SCHED,TRAN,MODEL
# ROTA: 1=HDD (rotante), 0=SSD
# SCHED: scheduler I/O (mq-deadline, kyber, bfq, none)
```

**Step 4 — LVM: Logical Volume Manager (se presente).**

```bash
echo "=== 4. LVM STATUS (se presente) ==="

# Controlla se LVM è in uso
if command -v lvs &>/dev/null; then
    echo "--- Physical Volumes ---"
    sudo pvs --units g

    echo ""
    echo "--- Volume Groups ---"
    sudo vgs --units g

    echo ""
    echo "--- Logical Volumes ---"
    sudo lvs --units g
else
    echo "[INFO] LVM non installato o non in uso su questo sistema"
    echo "       Nel lab VirtualBox il disco è diretto (non LVM)"
fi

# Alternativa: verifica partizioni standard
echo ""
echo "--- Partizioni del disco principale ---"
sudo fdisk -l /dev/sda 2>/dev/null | grep -E "Device|/dev/sda"
```

**Step 5 — Performance I/O in tempo reale (iostat).**

```bash
echo "=== 5. PERFORMANCE I/O ==="

# Installa sysstat se mancante
if ! command -v iostat &>/dev/null; then
    echo "Installazione sysstat..."
    sudo apt install -y sysstat
fi

# iostat: 5 campionamenti da 3 secondi
echo "Campionamento I/O per 15 secondi..."
iostat -xz 3 5

# Interpretazione colonne chiave:
# %util    → se > 90%, il disco è saturo
# await    → latenza media in ms (warning > 20ms, critico > 50ms)
# r/s w/s  → read/write IOPS
# rkB/s    → throughput lettura in KB/s
```

**Output atteso e interpretazione:**

```
Device            r/s     w/s    rkB/s    wkB/s   await  %util
sda              0.50    2.30     8.50    18.40    8.23   1.20

# Questo sistema è IDLE (uso normale del lab)
# In produzione con database attivo:
# sda              150     80    2400     640      3.50   45.0   ← normale
# sda             1200    600   19200    4800     48.50   98.0   ← DISCO SATURO!
```

**Step 6 — Verifica SMART (salute disco fisico).**

```bash
echo "=== 6. SMART STATUS ==="

# Installa smartmontools se mancante
if ! command -v smartctl &>/dev/null; then
    sudo apt install -y smartmontools
fi

# Status generale (VirtualBox: disco virtuale non ha SMART reale)
sudo smartctl -H /dev/sda 2>/dev/null

# Nota: su VirtualBox il SMART restituisce errori perché è un disco virtuale
# In produzione su hardware reale:
# sudo smartctl -a /dev/sda | grep -E "PASSED|FAILED|Hours|Reallocated|Pending|Uncorrectable"
echo "[INFO] Su VirtualBox SMART non è disponibile — su hardware fisico mostrerebbe la salute del disco"
```

**Checkpoint B1:**
- [ ] `df -h` mostra spazio disponibile su tutte le partizioni
- [ ] `lsblk` identifica i block device del sistema
- [ ] `iostat -x` mostra le metriche di performance I/O
- [ ] Comprendi le colonne `%util` e `await`

---

### Esercizio B2: Monitoraggio Disco su DC-LAB-01 (Windows)

**Obiettivo.** Eseguire l'equivalente Windows dell'analisi storage di B1: spazio disco, performance, log eventi rilevanti.

**Background.** Un file server Windows con pochi GB liberi su C: è un'emergenza — il sistema operativo può smettere di funzionare correttamente se lo spazio di sistema si esaurisce (paging file, log Windows, aggiornamenti). Su DC-LAB-01 c'è anche il database Active Directory (NTDS.dit) che cresce nel tempo.

**Step 1 — Su DC-LAB-01: spazio disco e alert.**

```powershell
# Su DC-LAB-01 (PowerShell come Administrator)

Write-Host "=== ANALISI STORAGE DC-LAB-01 ===" -ForegroundColor Cyan

# Tutti i dischi con spazio libero e percentuale
$dischi = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -ne $null }
foreach ($d in $dischi) {
    $totale    = [math]::Round(($d.Used + $d.Free) / 1GB, 2)
    $usato     = [math]::Round($d.Used / 1GB, 2)
    $libero    = [math]::Round($d.Free / 1GB, 2)
    $percLibero = [math]::Round(($d.Free / ($d.Used + $d.Free)) * 100, 1)
    
    $stato = if ($percLibero -lt 10) { "CRITICO" } elseif ($percLibero -lt 20) { "WARNING" } else { "OK" }
    
    Write-Host "Drive $($d.Name): Totale=$totale`GB Usato=$usato`GB Libero=$libero`GB ($percLibero% libero) [$stato]"
}
```

**Step 2 — Top cartelle per dimensione su C:.**

```powershell
Write-Host "`n=== TOP CARTELLE SU C:\ ===" -ForegroundColor Cyan

# Analisi dimensioni cartelle principali (livello 1)
$cartelle = @("C:\Windows", "C:\Program Files", "C:\Users", "C:\Windows\Logs", 
              "C:\Windows\SoftwareDistribution")

foreach ($c in $cartelle) {
    if (Test-Path $c) {
        try {
            $dim = (Get-ChildItem -Path $c -Recurse -ErrorAction SilentlyContinue |
                    Measure-Object -Property Length -Sum).Sum
            $dimGB = [math]::Round($dim / 1GB, 2)
            Write-Host "$c : $dimGB GB"
        } catch {
            Write-Host "$c : (errore accesso)"
        }
    }
}

# Windows Update cache — può occupare molto spazio
Write-Host "`n[INFO] SoftwareDistribution/Download = cache Windows Update (pulizia sicura se Windows Update è idle)"
```

**Step 3 — Performance disco con PerfMon (PowerShell).**

```powershell
Write-Host "`n=== PERFORMANCE DISCO (30 secondi) ===" -ForegroundColor Cyan

# Campiona Disk Queue Length ogni 5 secondi per 30 secondi
$contatori = @(
    "\PhysicalDisk(*)\Avg. Disk Queue Length",
    "\PhysicalDisk(*)\Avg. Disk sec/Read",
    "\PhysicalDisk(*)\Avg. Disk sec/Write",
    "\PhysicalDisk(*)\Disk Reads/sec",
    "\PhysicalDisk(*)\Disk Writes/sec"
)

Write-Host "Campionamento in corso (6 iterazioni × 5s = 30 secondi)..."
for ($i = 1; $i -le 6; $i++) {
    $vals = Get-Counter -Counter $contatori -SampleInterval 5 -MaxSamples 1 -ErrorAction SilentlyContinue
    foreach ($sample in $vals.CounterSamples) {
        if ($sample.CookedValue -gt 0) {
            Write-Host "[$i] $($sample.Path.Split('\')[-1]): $([math]::Round($sample.CookedValue, 4))"
        }
    }
    Write-Host "---"
}

Write-Host "`n[INTERPRETAZIONE]"
Write-Host "Avg. Disk Queue Length > 2 → disco saturo (bottleneck I/O)"
Write-Host "Avg. Disk sec/Read     > 0.02s (20ms) → latenza alta"
```

**Step 4 — NTDS.dit e log Active Directory.**

```powershell
Write-Host "`n=== DATABASE ACTIVE DIRECTORY ===" -ForegroundColor Cyan

# Posizione e dimensione del database AD
$ntdsPath = "C:\Windows\NTDS\"
if (Test-Path $ntdsPath) {
    Get-ChildItem -Path $ntdsPath | Select-Object Name, 
        @{Name="Size_MB"; Expression={[math]::Round($_.Length / 1MB, 2)}},
        LastWriteTime | Format-Table -AutoSize
}

# ntds.dit → database AD
# edb.log  → transaction log AD (come WAL)
# edb.chk  → checkpoint file (fino a dove i log sono applicati al DB)

Write-Host "`n[INFO] ntds.dit → database AD (cresce con utenti/computer/oggetti)"
Write-Host "[INFO] edb.log → transaction log (ruotato automaticamente da AD DS)"
```

**Step 5 — Event log: errori di disco negli ultimi 7 giorni.**

```powershell
Write-Host "`n=== EVENTI DISCO (ultimi 7 giorni) ===" -ForegroundColor Cyan

$eventi = Get-WinEvent -FilterHashtable @{
    LogName   = "System"
    Id        = @(7, 11, 15, 51)  # Errori disco controller
    StartTime = (Get-Date).AddDays(-7)
} -ErrorAction SilentlyContinue

if ($eventi) {
    Write-Host "TROVATI $($eventi.Count) eventi disco!" -ForegroundColor Yellow
    $eventi | Select-Object TimeCreated, Id, Message | Format-Table -AutoSize -Wrap
} else {
    Write-Host "[OK] Nessun errore disco negli ultimi 7 giorni"
}

# Event ID 7  = errore lettura/scrittura disco
# Event ID 11 = controller disco: errore
# Event ID 15 = Device not ready
# Event ID 51 = Page fault su device non pronto
```

**Checkpoint B2:**
- [ ] `Get-PSDrive` mostra spazio libero su C: con categoria OK/WARNING/CRITICO
- [ ] File NTDS.dit identificato e dimensione nota
- [ ] Performance disco campionata con Get-Counter
- [ ] Event log System controllato per errori disco

---

### Esercizio B3: Connessione e Stato Base di MariaDB (GLPI)

**Obiettivo.** Connettersi al database MariaDB usato da GLPI, verificare lo stato del motore, visualizzare le tabelle e comprendere la struttura.

**Background.** Il database di GLPI è il cuore del sistema ITSM. Tutti i ticket, gli asset, gli utenti, le soluzioni sono qui. Sapere come "guardare dentro" il database è fondamentale per diagnosi avanzate, export dati, verifica integrità.

**Step 1 — Identificare il container MariaDB.**

```bash
# Su SRV-LINUX-01

echo "=== IDENTIFICAZIONE CONTAINER DATABASE ==="
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

# Cerca il container con "db" o "mariadb" nel nome
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria|mysql" | head -1)
echo "Container identificato: $DB_CONTAINER"

# Ispeziona le variabili d'ambiente (credenziali DB)
echo ""
echo "=== CREDENZIALI DATABASE ==="
docker inspect "$DB_CONTAINER" 2>/dev/null | \
    python3 -c "import sys,json; env=json.load(sys.stdin)[0]['Config']['Env']; [print(e) for e in env if 'MYSQL_\|MARIADB_' in e.upper() or 'PASSWORD' in e.upper() or 'USER' in e.upper() or 'DATABASE' in e.upper()]" \
    2>/dev/null || \
docker inspect "$DB_CONTAINER" | grep -A50 '"Env"' | grep -E "MYSQL_|MARIADB_|DATABASE|PASSWORD|USER"
```

**Step 2 — Connessione al database.**

```bash
# Connessione al container MariaDB
# Le credenziali tipiche di GLPI Docker sono nelle env vars del container

# Metodo 1: Usa variabile d'ambiente (più sicuro)
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)
echo "Connessione a container: $DB_CONTAINER"

# Esegui mysql all'interno del container (trova le credenziali nelle env vars)
docker exec -it "$DB_CONTAINER" bash -c '
    echo "=== VERSIONE MARIADB ==="
    mysql --user="$MYSQL_USER" --password="$MYSQL_PASSWORD" --database="$MYSQL_DATABASE" \
        -e "SELECT VERSION();" 2>/dev/null || \
    mysql --user="$MARIADB_USER" --password="$MARIADB_PASSWORD" --database="$MARIADB_DATABASE" \
        -e "SELECT VERSION();" 2>/dev/null || \
    mysql -u root --password="$MYSQL_ROOT_PASSWORD" -e "SELECT VERSION();" 2>/dev/null
'

# Metodo 2: Connessione diretta con credenziali note (comune per GLPI)
echo ""
echo "=== CONNESSIONE DIRETTA ==="
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi -e "SELECT 'Connesso a GLPI DB' AS Status;" 2>/dev/null || \
docker exec "$DB_CONTAINER" mysql -u root --password=Password1 -e "SHOW DATABASES;" 2>/dev/null || \
echo "[INFO] Adatta le credenziali al tuo setup — controlla docker-compose.yml per le password configurate"
```

**Step 3 — Esplora il database GLPI.**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

# Questo script aggrega tutte le query esplorative
docker exec "$DB_CONTAINER" bash << 'MYSQL_SCRIPT'
# Tenta connessione con credenziali comuni GLPI
MYSQL_CMD="mysql -u glpi --password=glpi glpi"

echo "=== DATABASE E TABELLE ==="
$MYSQL_CMD -e "SHOW DATABASES;" 2>/dev/null || \
    mysql -u root --password=rootpassword -e "SHOW DATABASES;" 2>/dev/null

echo ""
echo "=== TABELLE IN GLPI ==="
$MYSQL_CMD -e "SHOW TABLES;" 2>/dev/null | head -30

echo ""
echo "=== DIMENSIONE TABELLE (top 10) ==="
$MYSQL_CMD -e "
SELECT TABLE_NAME, 
       ROUND(DATA_LENGTH/1024/1024, 2) AS 'Data_MB',
       ROUND(INDEX_LENGTH/1024/1024, 2) AS 'Index_MB',
       TABLE_ROWS AS 'Righe_stimate'
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'glpi'
ORDER BY DATA_LENGTH DESC 
LIMIT 10;" 2>/dev/null

echo ""
echo "=== QUANTI TICKET CI SONO? ==="
$MYSQL_CMD -e "SELECT COUNT(*) AS 'Totale Ticket', 
    SUM(CASE WHEN status=1 THEN 1 ELSE 0 END) AS 'Nuovi',
    SUM(CASE WHEN status=2 THEN 1 ELSE 0 END) AS 'In_attesa',
    SUM(CASE WHEN status=6 THEN 1 ELSE 0 END) AS 'Chiusi'
FROM glpi_tickets;" 2>/dev/null

MYSQL_SCRIPT
```

**Output atteso:**

```
=== DIMENSIONE TABELLE (top 10) ===
TABLE_NAME                    Data_MB   Index_MB   Righe_stimate
glpi_logs                     5.23      1.02       12450
glpi_tickets                  2.10      0.85       143
glpi_items_tickets            0.45      0.22       210
glpi_ticketfollowups          0.38      0.18       189
...

=== QUANTI TICKET CI SONO? ===
Totale Ticket  Nuovi  In_attesa  Chiusi
143            12     8          98
```

**Checkpoint B3:**
- [ ] Container database identificato con `docker ps`
- [ ] Connessione a MariaDB riuscita
- [ ] `SHOW TABLES` mostra le tabelle di GLPI
- [ ] Dimensione tabelle visualizzata da `information_schema`

---

### Esercizio B4: Salute del Motore MariaDB — Status e Buffer Pool

**Obiettivo.** Interrogare le variabili di stato di MariaDB per valutare la salute complessiva del motore: connessioni, buffer pool hit rate, query stats.

**Background.** Il buffer pool di InnoDB (il motore di storage predefinito di MariaDB/MySQL) è come la RAM del database: più dati riesce a tenere in memoria, meno deve leggere dal disco. Un buffer pool hit rate sotto il 99% indica che il database sta leggendo troppo dal disco — bisogna aumentare `innodb_buffer_pool_size` o ottimizzare le query.

**Step 1 — Variabili di stato InnoDB.**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

docker exec "$DB_CONTAINER" bash << 'MYSQL_HEALTH'
MYSQL_CMD="mysql -u glpi --password=glpi glpi"

echo "=== 1. VERSIONE E UPTIME ==="
$MYSQL_CMD -e "
SELECT VERSION() AS Versione,
       SEC_TO_TIME(@@global.uptime) AS Uptime_HH_MM_SS,
       @@hostname AS Hostname;" 2>/dev/null

echo ""
echo "=== 2. BUFFER POOL HIT RATE ==="
$MYSQL_CMD -e "
SELECT 
    VARIABLE_NAME, VARIABLE_VALUE 
FROM information_schema.GLOBAL_STATUS 
WHERE VARIABLE_NAME IN (
    'Innodb_buffer_pool_reads',
    'Innodb_buffer_pool_read_requests',
    'Innodb_buffer_pool_pages_total',
    'Innodb_buffer_pool_pages_free'
);" 2>/dev/null

# Calcola il hit rate manualmente
$MYSQL_CMD -e "
SELECT 
    @@innodb_buffer_pool_size / 1024 / 1024 AS 'Buffer_Pool_MB',
    ROUND(
        (1 - (
            (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads') /
            (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests')
        )) * 100, 4
    ) AS 'Hit_Rate_%';" 2>/dev/null

echo "[INFO] Hit Rate > 99% = ottimale, < 95% = aumentare innodb_buffer_pool_size"

MYSQL_HEALTH
```

**Step 2 — Connessioni attive e max configurato.**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi glpi -e "
SELECT 
    @@max_connections AS 'Max_Connessioni',
    (SELECT COUNT(*) FROM information_schema.PROCESSLIST) AS 'Connessioni_Attive',
    (SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS 
     WHERE VARIABLE_NAME = 'Max_used_connections') AS 'Massimo_Storico',
    ROUND(
        (SELECT COUNT(*) FROM information_schema.PROCESSLIST) / @@max_connections * 100, 1
    ) AS 'Utilizzo_%';" 2>/dev/null

echo ""
echo "[INTERPRETAZIONE]"
echo "Utilizzo < 70%: normale"
echo "Utilizzo > 70%: pianifica incremento max_connections"
echo "Utilizzo > 90%: CRITICO — nuovi client rifiutati"
```

**Step 3 — Query in esecuzione (PROCESSLIST).**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi glpi -e "
SHOW FULL PROCESSLIST;" 2>/dev/null

# In produzione con carico, potresti vedere:
# | Id | User  | Host      | db   | Command | Time | State       | Info           |
# | 12 | glpi  | app:52841 | glpi | Query   | 45   | Sending data| SELECT * FROM  |
# Time > 30 secondi → query lenta, potrebbe bloccare altri client
```

**Checkpoint B4:**
- [ ] Buffer Pool hit rate calcolato (su lab vuoto sarà ~100% o NULL — normale)
- [ ] Connessioni attive vs max_connections verificate
- [ ] `SHOW FULL PROCESSLIST` eseguito

---

### Esercizio B5: Manutenzione Tabelle — Frammentazione e OPTIMIZE TABLE

**Obiettivo.** Identificare le tabelle frammentate in MariaDB ed eseguire OPTIMIZE TABLE per defragmentarle, equivalente del VACUUM di PostgreSQL.

**Background.** Ogni DELETE o UPDATE in MariaDB lascia "spazi vuoti" nelle pagine InnoDB — come un libro con molte pagine strappate. Lo spazio viene riutilizzato per nuovi insert, ma se ci sono molti delete senza nuovi insert, lo spazio non viene rilasciato al sistema operativo. `OPTIMIZE TABLE` ricostruisce la tabella fisicamente, recupera spazio e riordina le pagine per accesso sequenziale più veloce.

**Step 1 — Identificare tabelle frammentate.**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi glpi -e "
SELECT 
    TABLE_NAME,
    ROUND(DATA_LENGTH / 1024 / 1024, 2) AS 'Dati_MB',
    ROUND(INDEX_LENGTH / 1024 / 1024, 2) AS 'Indici_MB',
    ROUND(DATA_FREE / 1024 / 1024, 2) AS 'Frammentazione_MB',
    TABLE_ROWS AS 'Righe_stimate',
    ROUND(DATA_FREE / (DATA_LENGTH + INDEX_LENGTH + 1) * 100, 1) AS 'Frammento_%'
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'glpi'
    AND DATA_FREE > 0
ORDER BY DATA_FREE DESC
LIMIT 15;" 2>/dev/null

echo ""
echo "[SOGLIE AZIONE]"
echo "Frammento_% < 30%:  OK — non necessario intervenire"
echo "Frammento_% > 30%:  Pianifica OPTIMIZE TABLE"  
echo "Frammento_% > 50%:  Esegui OPTIMIZE TABLE urgente"
```

**Step 2 — OPTIMIZE TABLE su tabelle candidate.**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

echo "=== OPTIMIZE TABLE — Defragmentazione ==="
echo "Nota: su tabelle grandi questa operazione può richiedere minuti e lock la tabella"
echo "In produzione pianificare nella finestra di manutenzione notturna"
echo ""

# Ottimizza le 3 tabelle log più grandi (tipicamente le più frammentate in GLPI)
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi glpi -e "
OPTIMIZE TABLE glpi_logs;" 2>/dev/null

# Poi controlla di nuovo la frammentazione
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi glpi -e "
SELECT TABLE_NAME, 
       ROUND(DATA_FREE / 1024 / 1024, 2) AS 'Frammentazione_MB_dopo'
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'glpi' AND TABLE_NAME = 'glpi_logs';" 2>/dev/null

echo ""
echo "[BEST PRACTICE] Script OPTIMIZE ALL TABLES (per manutenzione programmata):"
cat << 'SCRIPT'
# Genera e esegue OPTIMIZE su tutte le tabelle con frammentazione > 30%
mysql -u glpi -pglpi glpi << 'EOF'
SELECT CONCAT('OPTIMIZE TABLE `', TABLE_NAME, '`;')
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'glpi'
    AND DATA_FREE / (DATA_LENGTH + INDEX_LENGTH + 1) > 0.30
    AND DATA_FREE > 0;
EOF
SCRIPT
```

**Step 3 — ANALYZE TABLE per aggiornare le statistiche degli indici.**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

echo "=== ANALYZE TABLE — Aggiorna statistiche indici ==="
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi glpi -e "
ANALYZE TABLE glpi_tickets, glpi_items, glpi_users;" 2>/dev/null

echo ""
echo "[QUANDO ESEGUIRE]"
echo "- Dopo import massivo di dati"
echo "- Dopo OPTIMIZE TABLE"
echo "- Se l'ottimizzatore sceglie piani di query inefficienti"
echo "- Mensile su tabelle ad alto turnover (ticket chiusi, log)"
```

**Checkpoint B5:**
- [ ] `information_schema.TABLES` interrogato per frammentazione
- [ ] OPTIMIZE TABLE eseguito su almeno una tabella
- [ ] ANALYZE TABLE eseguito per aggiornare le statistiche

---

### Esercizio B6: Slow Query Log — Trovare le Query Lente

**Obiettivo.** Abilitare e analizzare il slow query log di MariaDB per identificare le query che rallentano l'applicazione.

**Background.** Il 90% dei problemi di performance su un'applicazione web con database sono causati da poche query lente. Il slow query log è lo strumento che le identifica automaticamente: ogni query che supera la soglia configurata viene registrata con tempo di esecuzione, piano di query e testo completo. In produzione è abilitato permanentemente con soglia 1 secondo.

**Step 1 — Verificare e abilitare il slow query log.**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

echo "=== CONFIGURAZIONE SLOW QUERY LOG ==="
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi glpi -e "
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';
SHOW VARIABLES LIKE 'log_queries_not_using_indexes';" 2>/dev/null

echo ""
echo "=== ABILITAZIONE (runtime — senza riavvio) ==="
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi -e "
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;
SET GLOBAL log_queries_not_using_indexes = 'ON';
SHOW VARIABLES LIKE 'slow_query_log%';" 2>/dev/null

echo ""
echo "[INFO] Queste impostazioni valgono fino al prossimo riavvio del container"
echo "[PRODUZIONE] Aggiungere in /etc/mysql/mariadb.conf.d/50-server.cnf:"
echo "  slow_query_log      = 1"
echo "  slow_query_log_file = /var/log/mysql/slow.log"
echo "  long_query_time     = 1"
echo "  log_queries_not_using_indexes = 1"
```

**Step 2 — Generare artificialmente una query lenta per test.**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

echo "=== GENERAZIONE QUERY LENTE DI TEST ==="

# Crea una query che dura almeno 2 secondi (SLEEP)
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi glpi -e "
-- Questa query dura intenzionalmente 2 secondi
SELECT SLEEP(2) AS test_slow_query_1;
SELECT SLEEP(1.5) AS test_slow_query_2;" 2>/dev/null

echo "Query di test eseguite — ora controlliamo il log"
```

**Step 3 — Analizzare il slow query log.**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

echo "=== ANALISI SLOW QUERY LOG ==="

# Trova il file di log
SLOW_LOG=$(docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi glpi \
    -se "SELECT @@slow_query_log_file;" 2>/dev/null)
echo "File slow query log: $SLOW_LOG"

# Leggi le ultime query lente
if [ -n "$SLOW_LOG" ]; then
    docker exec "$DB_CONTAINER" tail -50 "$SLOW_LOG" 2>/dev/null | \
    grep -A 10 "Query_time\|SELECT\|UPDATE\|DELETE\|INSERT" | head -50
else
    echo "[INFO] File log non accessibile direttamente — usa mysqldumpslow"
fi

echo ""
echo "=== STATISTICHE SLOW QUERY ==="
# Conta le query nel log (se accessibile)
docker exec "$DB_CONTAINER" bash -c \
    "grep -c 'Query_time' \"$SLOW_LOG\" 2>/dev/null && echo 'query lente trovate'" 2>/dev/null || \
    echo "[INFO] Il log slow query dipende dalla configurazione del container"

echo ""
echo "=== STRUMENTO mysqldumpslow (analisi aggregata) ==="
echo "# In ambienti con log slow query su file:"
echo "# mysqldumpslow -s t -t 10 /var/log/mysql/slow.log"
echo "# -s t = ordina per tempo totale"
echo "# -t 10 = mostra top 10 query"
```

**Step 4 — EXPLAIN: capire il piano di esecuzione.**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

echo "=== EXPLAIN — Piano di Esecuzione Query ==="

# Analizza una query reale su GLPI
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi glpi -e "
-- Analisi query che cerca ticket per stato
EXPLAIN SELECT id, name, status, date_creation 
FROM glpi_tickets 
WHERE status = 1 
ORDER BY date_creation DESC 
LIMIT 10;" 2>/dev/null

echo ""
echo "[INTERPRETAZIONE EXPLAIN]"
echo "type = 'ALL'        → full table scan (LENTO senza indice)"
echo "type = 'ref'        → usa un indice (VELOCE)"
echo "type = 'const'      → accesso diretto (MOLTO VELOCE)"
echo "rows = N            → quante righe stima di scansionare"
echo "Extra = 'Using index' → query coperta da indice (ottimale)"
echo ""
echo "Se type='ALL' su tabella grande → considera aggiungere un indice:"
echo "CREATE INDEX idx_tickets_status ON glpi_tickets(status);"
```

**Checkpoint B6:**
- [ ] Slow query log abilitato con `SET GLOBAL slow_query_log = 'ON'`
- [ ] Query di test eseguite con SLEEP()
- [ ] EXPLAIN eseguito su una query reale
- [ ] Comprendi la differenza tra `type=ALL` (scan) e `type=ref` (indice)

---

### Esercizio B7: Binary Log — Gestione e Pulizia

**Obiettivo.** Verificare lo stato dei binary log di MariaDB, comprendere il loro ruolo nel recovery point-in-time, e gestire la pulizia per evitare che occupino tutto il disco.

**Background.** I binary log di MariaDB registrano ogni modifica ai dati (INSERT, UPDATE, DELETE) in ordine cronologico. Sono essenziali per due motivi: (1) replica database — il replica server li legge per mantenere la sincronizzazione, (2) point-in-time recovery — dopo un crash, si può ripristinare il backup e poi "riapplicare" i binary log fino al momento esatto del problema. Però se non gestiti, crescono indefinitamente e riempiono il disco.

**Step 1 — Stato dei binary log.**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

echo "=== BINARY LOG STATUS ==="
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi -e "
SHOW VARIABLES LIKE 'log_bin%';
SHOW VARIABLES LIKE 'binlog_expire_logs_seconds';
SHOW VARIABLES LIKE 'expire_logs_days';" 2>/dev/null

echo ""
echo "=== LISTA BINARY LOG ATTUALI ==="
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi -e "
SHOW BINARY LOGS;" 2>/dev/null || echo "[INFO] Binary log non abilitati in questo setup"

echo ""
echo "=== DIMENSIONE TOTALE BINARY LOG ==="
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi -e "
SELECT 
    COUNT(*) AS 'Numero_File',
    ROUND(SUM(File_size) / 1024 / 1024, 2) AS 'Dimensione_Totale_MB'
FROM information_schema.FILES
WHERE FILE_TYPE = 'LOG';" 2>/dev/null || \
docker exec "$DB_CONTAINER" bash -c \
    "ls -lh /var/lib/mysql/mysql-bin.* 2>/dev/null | awk '{sum += \$5} END {print \"Totale: \" sum/1024/1024 \" MB\"}'" 2>/dev/null || \
    echo "[INFO] Binary log su disco non visibili da dentro il container"
```

**Step 2 — Pulizia sicura dei binary log.**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

echo "=== PULIZIA BINARY LOG ==="

echo "METODO 1: Elimina log più vecchi di 7 giorni"
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi -e "
-- NON ESEGUIRE se hai replica attiva senza verificare la posizione del replica!
-- PURGE BINARY LOGS BEFORE DATE_SUB(NOW(), INTERVAL 7 DAY);
SELECT 'Comando PURGE commentato per sicurezza — decommenta in produzione dopo verifica' AS Info;" 2>/dev/null

echo ""
echo "METODO 2: Elimina fino a un file specifico"
echo "# PURGE BINARY LOGS TO 'mysql-bin.000010';"

echo ""
echo "METODO 3: Configurazione automatica (raccomandato)"
echo "# In /etc/mysql/mariadb.conf.d/50-server.cnf:"
echo "# expire_logs_days = 7          (versioni vecchie)"
echo "# binlog_expire_logs_seconds = 604800  (7 giorni, versioni nuove)"

echo ""
echo "[ATTENZIONE] Prima di purge con replica:"
echo "# Verifica posizione del replica: SHOW SLAVE STATUS\\G"
echo "# Log in uso dal replica non devono essere eliminati!"

echo ""
echo "=== CONFIGURAZIONE EXPIRE AUTOMATICA (demo) ==="
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi -e "
-- In produzione: imposta expire automatica
-- SET GLOBAL binlog_expire_logs_seconds = 604800; -- 7 giorni
-- SHOW VARIABLES LIKE 'binlog_expire%';
SELECT 'Su questo lab: verifica se binary log sono abilitati' AS Info;" 2>/dev/null
```

**Step 3 — Master status e posizione corrente nel log.**

```bash
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)

echo "=== POSIZIONE CORRENTE NEL BINARY LOG ==="
docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi -e "
SHOW MASTER STATUS;" 2>/dev/null

echo ""
echo "[INTERPRETAZIONE]"
echo "File     → nome del file binary log corrente"
echo "Position → posizione corrente nel file (crescono con ogni operazione DML)"
echo ""
echo "In recovery: 'Ripristina backup del 01:00, poi applica binary log"
echo "             da posizione 107894 (punto ultimo backup) a posizione 445812"  
echo "             (un minuto prima del crash) — perdi solo 1 minuto di dati'"
```

**Checkpoint B7:**
- [ ] `SHOW BINARY LOGS` eseguito (anche se disabilitati nel lab)
- [ ] Compreso il ruolo dei binary log per point-in-time recovery
- [ ] Conosci il comando `PURGE BINARY LOGS BEFORE` e quando NON usarlo
- [ ] `SHOW MASTER STATUS` eseguito

---

### Esercizio B8: Report di Salute Storage + DB Integrato

**Obiettivo.** Creare un report di salute unificato che combina metriche storage e database, da usare come base per il check settimanale.

**Background.** In produzione, il check di salute storage+DB è parte della routine settimanale. Lo scopo non è fare azioni correttive (quelle si fanno nella finestra di manutenzione), ma identificare trend preoccupanti: spazio che cresce più del solito, hit rate che scende sotto il 99%, slow query che aumentano. Questo esercizio crea un report puntuale da cui partire per l'automazione nella Part C.

```bash
# Su SRV-LINUX-01 — report integrato storage + database

echo "=============================================="
echo "  REPORT SALUTE STORAGE + DATABASE"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Host: $(hostname)"
echo "=============================================="

echo ""
echo "--- [1] STORAGE LINUX ---"
df -h | grep -E "^/dev" | while IFS= read -r line; do
    uso=$(echo "$line" | awk '{print $5}' | tr -d '%')
    fs=$(echo "$line"  | awk '{print $1}')
    mnt=$(echo "$line" | awk '{print $6}')
    if [ "$uso" -ge 90 ]; then
        echo "[CRITICO] $fs ($mnt): ${uso}% utilizzato"
    elif [ "$uso" -ge 75 ]; then
        echo "[WARNING] $fs ($mnt): ${uso}% utilizzato"
    else
        echo "[OK]      $fs ($mnt): ${uso}% utilizzato"
    fi
done

echo ""
echo "--- [2] I/O PERFORMANCE (campione 5s) ---"
if command -v iostat &>/dev/null; then
    iostat -dxz 5 1 | grep -E "Device|^sd|^vd|^nvme" | grep -v "Device" | while IFS= read -r line; do
        util=$(echo "$line" | awk '{print $NF}' | cut -d. -f1)
        dev=$(echo "$line"  | awk '{print $1}')
        await=$(echo "$line" | awk '{print $10}')
        if [ "${util:-0}" -ge 90 ]; then
            echo "[CRITICO] /dev/$dev: util=${util}% await=${await}ms — DISCO SATURO"
        elif [ "${util:-0}" -ge 70 ]; then
            echo "[WARNING] /dev/$dev: util=${util}% await=${await}ms"
        else
            echo "[OK]      /dev/$dev: util=${util}% await=${await}ms"
        fi
    done
else
    echo "[INFO] iostat non disponibile — installa sysstat"
fi

echo ""
echo "--- [3] DATABASE MARIADB ---"
DB_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "db|maria" | head -1)
if [ -n "$DB_CONTAINER" ] && docker ps --format "{{.Names}}" | grep -q "$DB_CONTAINER"; then
    # Connessione e metriche chiave
    docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi glpi -se "
SELECT 
    CONCAT('[OK]      MariaDB UP | Version: ', VERSION(),
           ' | Uptime: ', SEC_TO_TIME(@@global.uptime)) AS Status;" 2>/dev/null || \
        echo "[CRITICO] Database non raggiungibile"

    # Connessioni
    docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi glpi -se "
SELECT CONCAT(
    CASE WHEN cnt/@@max_connections > 0.9 THEN '[CRITICO] ' 
         WHEN cnt/@@max_connections > 0.7 THEN '[WARNING] ' 
         ELSE '[OK]      ' END,
    'Connessioni: ', cnt, '/', @@max_connections, 
    ' (', ROUND(cnt/@@max_connections*100,1), '%)'
) FROM (SELECT COUNT(*) cnt FROM information_schema.PROCESSLIST) t;" 2>/dev/null

    # Frammentazione tabelle
    FRAG=$(docker exec "$DB_CONTAINER" mysql -u glpi --password=glpi glpi -se "
    SELECT COUNT(*) FROM information_schema.TABLES 
    WHERE TABLE_SCHEMA='glpi' AND DATA_FREE/(DATA_LENGTH+INDEX_LENGTH+1) > 0.3 
    AND DATA_FREE > 0;" 2>/dev/null)
    if [ "${FRAG:-0}" -gt 0 ]; then
        echo "[WARNING] Tabelle con frammentazione > 30%: $FRAG (pianifica OPTIMIZE TABLE)"
    else
        echo "[OK]      Frammentazione tabelle: entro soglia"
    fi
else
    echo "[CRITICO] Container database non in esecuzione!"
fi

echo ""
echo "--- [4] DIMENSIONE VOLUMI DOCKER ---"
docker system df 2>/dev/null || echo "[INFO] Docker non accessibile"

echo ""
echo "=============================================="
echo "Fine report — $(date '+%H:%M:%S')"
echo "=============================================="
```

**Checkpoint B8:**
- [ ] Report completo eseguito senza errori
- [ ] Ogni sezione produce output interpretabile
- [ ] Identificato almeno un elemento da monitorare nel tuo lab

---
---

## PART C: SISTEMATIZZARE — Dalla Diagnosi alla Governance Storage/DB

---

### SOP-STG-001: Manutenzione Storage e Database

```
DOCUMENTO: SOP-STG-001 v1.0
TITOLO:    Procedura Operativa Standard — Manutenzione Storage e Database
AMBITO:    Infrastruttura di Produzione (Server Linux + Windows)
TRIGGER:   Schedulato (settimanale/mensile) o su incidente
OWNER:     Team IT Operations
```

**1. Pre-condizioni**

```
Accesso SSH a SRV-LINUX-01 come lab-admin
Accesso RDP a DC-LAB-01 come Administrator
Docker in esecuzione su SRV-LINUX-01
Credenziali database MariaDB disponibili
```

**2. Procedura Storage Check Settimanale (15 min)**

```
STEP 1: Controllo spazio disco Linux
  Eseguire: df -h
  → Alert se qualsiasi partizione > 75% → aprire ticket Priority 2
  → Alert se qualsiasi partizione > 90% → aprire ticket Priority 1 IMMEDIATAMENTE
  Azione se critico: identificare top consumer con du -sh /var/* e /home/*

STEP 2: Controllo spazio disco Windows (DC-LAB-01)
  Eseguire: Get-PSDrive -PSProvider FileSystem
  → Alert C: < 20% libero → indagare Windows Update cache / pagefile
  Azione: pulizia C:\Windows\SoftwareDistribution\Download (solo se Windows Update idle)
  
STEP 3: Verifica I/O performance
  Linux: iostat -xz 5 3 → %util > 70% = indagare processo causa
  Windows: Get-Counter "\PhysicalDisk(*)\Avg. Disk Queue Length" → > 2 = indagare
  
STEP 4: Registra metriche in GLPI (Knowledge Base o ticket padre mensile)
```

**3. Procedura Database Maintenance Mensile (30 min)**

```
STEP 1: Backup pre-manutenzione
  docker exec [db-container] mysqldump -u root -p[password] --all-databases \
      > /backup/db-before-maintenance-$(date +%Y%m%d).sql
  VERIFICARE che il file esista e abbia dimensione > 0

STEP 2: Verifica salute motore
  Buffer Pool Hit Rate → deve essere > 99%
  Connessioni attive vs max_connections → deve essere < 70%
  
STEP 3: Identificazione tabelle frammentate
  Query information_schema.TABLES (DATA_FREE > 0)
  Tabelle con frammentazione > 30% → lista per OPTIMIZE
  
STEP 4: Finestra manutenzione (fuori orario lavorativo)
  Per ogni tabella con frammentazione > 30%:
    OPTIMIZE TABLE nome_tabella;
    ANALYZE TABLE nome_tabella;
  
STEP 5: Pulizia binary log
  Verificare che non ci sia replica attiva (SHOW SLAVE STATUS)
  PURGE BINARY LOGS BEFORE DATE_SUB(NOW(), INTERVAL 7 DAY);
  Verificare spazio disco recuperato
  
STEP 6: Slow query review
  Controllare mysqldumpslow output degli ultimi 7 giorni
  Query con tempo > 5s: aprire ticket miglioramento performance
  
STEP 7: Documentazione
  Registrare in GLPI: dimensioni tabelle prima/dopo, spazio recuperato, 
  slow query identificate, azioni intraprese
```

**4. Escalation**

```
Disco > 90%:           Ticket P1 immediato → manager IT
DB non raggiungibile:  Seguire IRP-DB-001 (Incident Response DB)
Hit rate < 95%:        Ticket P2 → analisi memory configuration
Corruzione dati:       STOP operazioni → backup immediato → DBA
```

---

### Script C1: storage_db_health.sh — Monitoraggio Automatico

```bash
#!/usr/bin/env bash
# storage_db_health.sh — Check settimanale storage e database
# Schedulare: crontab -e → 0 8 * * 1 /opt/scripts/storage_db_health.sh >> /var/log/storage_db_health.log 2>&1
# Requisiti: sysstat, docker, accesso MariaDB

set -euo pipefail

# ─── CONFIGURAZIONE ───────────────────────────────────────────────────────────
SCRIPT_NAME="storage_db_health"
LOG_FILE="/var/log/${SCRIPT_NAME}.log"
REPORT_FILE="/tmp/${SCRIPT_NAME}_$(date +%Y%m%d_%H%M%S).txt"

DISK_WARN_PCT=75
DISK_CRIT_PCT=90
IO_UTIL_WARN=70
IO_UTIL_CRIT=90
IO_AWAIT_WARN=20
IO_AWAIT_CRIT=50
DB_CONN_WARN_PCT=70
DB_HIT_RATE_WARN=99.0
DB_HIT_RATE_CRIT=95.0
DB_FRAG_WARN_PCT=30

DB_CONTAINER="${DB_CONTAINER:-$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E 'db|maria' | head -1)}"
DB_USER="${DB_USER:-glpi}"
DB_PASS="${DB_PASS:-glpi}"
DB_NAME="${DB_NAME:-glpi}"

# ─── FUNZIONI UTILITY ─────────────────────────────────────────────────────────
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'; NC='\033[0m'

STATUS_OVERALL="OK"
ISSUES=()

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
ok()   { echo -e "${GREEN}[OK]${NC}      $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}    $*"; STATUS_OVERALL="WARNING"; ISSUES+=("WARN: $*"); }
crit() { echo -e "${RED}[CRITICO]${NC} $*"; STATUS_OVERALL="CRITICAL"; ISSUES+=("CRIT: $*"); }
info() { echo -e "          $*"; }

db_query() {
    local q="$1"
    docker exec "$DB_CONTAINER" mysql -u "$DB_USER" --password="$DB_PASS" "$DB_NAME" \
        -se "$q" 2>/dev/null
}

# ─── HEADER ───────────────────────────────────────────────────────────────────
{
echo "========================================================"
echo "  STORAGE + DATABASE HEALTH REPORT"
echo "  Host: $(hostname) | Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================================"
echo ""

# ─── SEZIONE 1: SPAZIO DISCO ──────────────────────────────────────────────────
echo "━━━ [1] SPAZIO DISCO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
df -h --output=source,target,size,used,avail,pcent | grep -E "^Filesystem|^/dev" | \
while IFS= read -r line; do
    if echo "$line" | grep -q "Filesystem"; then
        echo "$line"
        continue
    fi
    pcent=$(echo "$line" | awk '{print $NF}' | tr -d '%')
    fs=$(echo "$line"    | awk '{print $1}')
    mnt=$(echo "$line"   | awk '{print $2}')
    avail=$(echo "$line" | awk '{print $5}')
    if [ "${pcent:-0}" -ge "$DISK_CRIT_PCT" ]; then
        crit "DISCO $fs ($mnt): ${pcent}% utilizzato — solo $avail liberi"
    elif [ "${pcent:-0}" -ge "$DISK_WARN_PCT" ]; then
        warn "DISCO $fs ($mnt): ${pcent}% utilizzato — solo $avail liberi"
    else
        ok "DISCO $fs ($mnt): ${pcent}% utilizzato — $avail liberi"
    fi
done
echo ""

# ─── SEZIONE 2: PERFORMANCE I/O ───────────────────────────────────────────────
echo "━━━ [2] PERFORMANCE I/O ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v iostat &>/dev/null; then
    # Campiona per 5 secondi
    iostat -dxz 5 1 2>/dev/null | grep -E "^sd|^vd|^nvme|^xvd|^hd" | \
    while IFS= read -r line; do
        device=$(echo "$line" | awk '{print $1}')
        await=$(echo "$line"  | awk '{print $10}' 2>/dev/null || echo "0")
        util=$(echo "$line"   | awk '{print $NF}' 2>/dev/null || echo "0")
        
        # Confronta float (bash non supporta float nativamente)
        if awk "BEGIN {exit !($util >= $IO_UTIL_CRIT)}"; then
            crit "/dev/$device: util=${util}% await=${await}ms — DISCO SATURO"
        elif awk "BEGIN {exit !($util >= $IO_UTIL_WARN)}"; then
            warn "/dev/$device: util=${util}% await=${await}ms"
        else
            ok "/dev/$device: util=${util}% await=${await}ms"
        fi
    done
else
    info "[SKIP] iostat non disponibile — installare sysstat"
fi
echo ""

# ─── SEZIONE 3: DATABASE MARIADB ──────────────────────────────────────────────
echo "━━━ [3] DATABASE MARIADB ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -z "$DB_CONTAINER" ]; then
    crit "Nessun container database trovato"
elif ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    crit "Container '$DB_CONTAINER' non in esecuzione"
else
    # Versione e uptime
    DB_VERSION=$(db_query "SELECT VERSION();" 2>/dev/null || echo "N/A")
    DB_UPTIME=$(db_query "SELECT SEC_TO_TIME(@@global.uptime);" 2>/dev/null || echo "N/A")
    ok "MariaDB UP | Versione: $DB_VERSION | Uptime: $DB_UPTIME"

    # Buffer Pool Hit Rate
    READS=$(db_query "SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='Innodb_buffer_pool_reads';" 2>/dev/null || echo "")
    REQS=$(db_query  "SELECT VARIABLE_VALUE FROM information_schema.GLOBAL_STATUS WHERE VARIABLE_NAME='Innodb_buffer_pool_read_requests';" 2>/dev/null || echo "")
    
    if [ -n "$READS" ] && [ -n "$REQS" ] && [ "${REQS:-0}" -gt 0 ]; then
        HIT_RATE=$(awk "BEGIN {printf \"%.4f\", (1 - ($READS / $REQS)) * 100}")
        if awk "BEGIN {exit !($HIT_RATE < $DB_HIT_RATE_CRIT)}"; then
            crit "Buffer Pool Hit Rate: ${HIT_RATE}% — aumentare innodb_buffer_pool_size"
        elif awk "BEGIN {exit !($HIT_RATE < $DB_HIT_RATE_WARN)}"; then
            warn "Buffer Pool Hit Rate: ${HIT_RATE}%"
        else
            ok "Buffer Pool Hit Rate: ${HIT_RATE}%"
        fi
    else
        info "Buffer Pool Hit Rate: N/A (database quasi idle — normale in lab)"
    fi

    # Connessioni
    MAX_CONN=$(db_query "SELECT @@max_connections;" 2>/dev/null || echo "0")
    CUR_CONN=$(db_query "SELECT COUNT(*) FROM information_schema.PROCESSLIST;" 2>/dev/null || echo "0")
    if [ "${MAX_CONN:-0}" -gt 0 ]; then
        CONN_PCT=$(awk "BEGIN {printf \"%d\", ($CUR_CONN / $MAX_CONN) * 100}")
        if [ "$CONN_PCT" -ge 90 ]; then
            crit "Connessioni: $CUR_CONN/$MAX_CONN (${CONN_PCT}%) — nuovi client possono essere rifiutati"
        elif [ "$CONN_PCT" -ge "$DB_CONN_WARN_PCT" ]; then
            warn "Connessioni: $CUR_CONN/$MAX_CONN (${CONN_PCT}%)"
        else
            ok "Connessioni: $CUR_CONN/$MAX_CONN (${CONN_PCT}%)"
        fi
    fi

    # Tabelle frammentate
    FRAG_TABLES=$(db_query "
        SELECT COUNT(*) FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA='$DB_NAME' 
            AND DATA_FREE / (DATA_LENGTH + INDEX_LENGTH + 1) > $DB_FRAG_WARN_PCT/100.0
            AND DATA_FREE > 0;" 2>/dev/null || echo "0")
    if [ "${FRAG_TABLES:-0}" -gt 5 ]; then
        warn "Tabelle frammentate (>${DB_FRAG_WARN_PCT}%): $FRAG_TABLES — pianifica OPTIMIZE TABLE"
    elif [ "${FRAG_TABLES:-0}" -gt 0 ]; then
        info "Tabelle con frammentazione: $FRAG_TABLES (sotto soglia azione)"
    else
        ok "Frammentazione tabelle: entro soglia"
    fi

    # Dimensione database
    DB_SIZE=$(db_query "
        SELECT ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2)
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = '$DB_NAME';" 2>/dev/null || echo "N/A")
    ok "Dimensione database '$DB_NAME': ${DB_SIZE} MB"

    # Binary log
    BINLOG_STATUS=$(db_query "SELECT IF(@@log_bin=1, 'ENABLED', 'DISABLED');" 2>/dev/null || echo "N/A")
    if [ "$BINLOG_STATUS" = "ENABLED" ]; then
        BINLOG_COUNT=$(db_query "SHOW BINARY LOGS;" 2>/dev/null | wc -l)
        ok "Binary log: $BINLOG_STATUS ($BINLOG_COUNT file)"
    else
        info "Binary log: $BINLOG_STATUS"
    fi
fi
echo ""

# ─── SEZIONE 4: DOCKER VOLUMES ────────────────────────────────────────────────
echo "━━━ [4] DOCKER VOLUMES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v docker &>/dev/null; then
    docker system df 2>/dev/null | grep -v "^$" || echo "Docker non accessibile"
fi
echo ""

# ─── SOMMARIO ─────────────────────────────────────────────────────────────────
echo "========================================================"
echo "STATO COMPLESSIVO: $STATUS_OVERALL"
if [ ${#ISSUES[@]} -gt 0 ]; then
    echo ""
    echo "PROBLEMI RILEVATI:"
    for issue in "${ISSUES[@]}"; do
        echo "  → $issue"
    done
fi
echo ""
echo "Fine report: $(date '+%H:%M:%S')"
echo "========================================================"

} | tee "$REPORT_FILE"

log "Health check completato — Status: $STATUS_OVERALL — Report: $REPORT_FILE"
exit 0
```

**Deploy dello script:**

```bash
# Su SRV-LINUX-01
sudo mkdir -p /opt/scripts
sudo nano /opt/scripts/storage_db_health.sh
# incolla il contenuto dello script

sudo chmod +x /opt/scripts/storage_db_health.sh

# Test manuale
sudo /opt/scripts/storage_db_health.sh

# Schedulazione (ogni lunedì alle 08:00)
sudo crontab -e
# Aggiungere:
# 0 8 * * 1 /opt/scripts/storage_db_health.sh >> /var/log/storage_db_health_weekly.log 2>&1

# Verifica cron
sudo crontab -l | grep storage
```

---

### Script C2: db_maintenance.sh — Manutenzione Database Mensile

```bash
#!/usr/bin/env bash
# db_maintenance.sh — Manutenzione mensile MariaDB
# Eseguire nella finestra di manutenzione: 0 2 1 * * /opt/scripts/db_maintenance.sh
# Prerequisiti: mysqldump accessibile, cartella /backup/ montata

set -euo pipefail

DB_CONTAINER="${DB_CONTAINER:-$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E 'db|maria' | head -1)}"
DB_USER="${DB_USER:-glpi}"
DB_PASS="${DB_PASS:-glpi}"
DB_NAME="${DB_NAME:-glpi}"
BACKUP_DIR="/backup/db_maintenance"
LOG="/var/log/db_maintenance.log"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
db()  { docker exec "$DB_CONTAINER" mysql -u "$DB_USER" --password="$DB_PASS" "$DB_NAME" -se "$@" 2>/dev/null; }
db_root() { docker exec "$DB_CONTAINER" mysql -u root --password="$DB_ROOT_PASS" -se "$@" 2>/dev/null; }

log "=== INIZIO MANUTENZIONE DB MENSILE ==="

# STEP 1: Backup di sicurezza pre-manutenzione
log "STEP 1: Backup pre-manutenzione..."
mkdir -p "$BACKUP_DIR"
docker exec "$DB_CONTAINER" mysqldump \
    -u "$DB_USER" --password="$DB_PASS" \
    --single-transaction --quick --lock-tables=false \
    "$DB_NAME" > "${BACKUP_DIR}/${DB_NAME}_premaint_${TIMESTAMP}.sql"

BACKUP_SIZE=$(stat -c%s "${BACKUP_DIR}/${DB_NAME}_premaint_${TIMESTAMP}.sql" 2>/dev/null || echo 0)
if [ "$BACKUP_SIZE" -lt 1000 ]; then
    log "ERRORE: Backup troppo piccolo (${BACKUP_SIZE} bytes) — ABORT"
    exit 1
fi
log "Backup OK: ${BACKUP_DIR}/${DB_NAME}_premaint_${TIMESTAMP}.sql (${BACKUP_SIZE} bytes)"

# STEP 2: Stato prima della manutenzione
log "STEP 2: Stato pre-manutenzione..."
FRAG_PRE=$(db "SELECT ROUND(SUM(DATA_FREE)/1024/1024, 2) FROM information_schema.TABLES WHERE TABLE_SCHEMA='$DB_NAME' AND DATA_FREE > 0;")
SIZE_PRE=$(db "SELECT ROUND(SUM(DATA_LENGTH+INDEX_LENGTH)/1024/1024, 2) FROM information_schema.TABLES WHERE TABLE_SCHEMA='$DB_NAME';")
log "Pre: Dimensione=${SIZE_PRE}MB, Frammentazione=${FRAG_PRE}MB"

# STEP 3: Identifica tabelle da ottimizzare (frammentazione > 30%)
log "STEP 3: Identificazione tabelle da ottimizzare..."
TABLES_TO_OPTIMIZE=$(db "
SELECT TABLE_NAME 
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA='$DB_NAME'
    AND DATA_FREE/(DATA_LENGTH+INDEX_LENGTH+1) > 0.30 
    AND DATA_FREE > 0
ORDER BY DATA_FREE DESC;")

if [ -z "$TABLES_TO_OPTIMIZE" ]; then
    log "Nessuna tabella con frammentazione > 30% — skip OPTIMIZE"
else
    OPTIMIZE_COUNT=$(echo "$TABLES_TO_OPTIMIZE" | wc -l)
    log "Tabelle da ottimizzare: $OPTIMIZE_COUNT"

    # STEP 4: OPTIMIZE TABLE
    log "STEP 4: OPTIMIZE TABLE..."
    while IFS= read -r table; do
        [ -z "$table" ] && continue
        log "  Ottimizzazione: $table"
        db "OPTIMIZE TABLE \`$table\`;"
        db "ANALYZE TABLE \`$table\`;"
    done <<< "$TABLES_TO_OPTIMIZE"
fi

# STEP 5: Pulizia binary log (solo se NON c'è replica)
log "STEP 5: Pulizia binary log..."
REPLICA_STATUS=$(db "SHOW SLAVE STATUS;" 2>/dev/null || echo "")
if [ -n "$REPLICA_STATUS" ]; then
    log "SKIP: Replica attiva — non purgare binary log senza verificare posizione replica"
else
    BINLOG_ENABLED=$(db "SELECT @@log_bin;")
    if [ "${BINLOG_ENABLED:-0}" -eq 1 ]; then
        BEFORE=$(docker exec "$DB_CONTAINER" mysql -u "$DB_USER" --password="$DB_PASS" \
            -se "SHOW BINARY LOGS;" 2>/dev/null | wc -l)
        db "PURGE BINARY LOGS BEFORE DATE_SUB(NOW(), INTERVAL 7 DAY);"
        AFTER=$(docker exec "$DB_CONTAINER" mysql -u "$DB_USER" --password="$DB_PASS" \
            -se "SHOW BINARY LOGS;" 2>/dev/null | wc -l)
        log "Binary log: da $BEFORE a $AFTER file (eliminati $((BEFORE - AFTER)) file)"
    else
        log "Binary log non abilitati — skip"
    fi
fi

# STEP 6: Stato dopo manutenzione
log "STEP 6: Stato post-manutenzione..."
FRAG_POST=$(db "SELECT ROUND(SUM(DATA_FREE)/1024/1024, 2) FROM information_schema.TABLES WHERE TABLE_SCHEMA='$DB_NAME' AND DATA_FREE > 0;" || echo "0")
SIZE_POST=$(db "SELECT ROUND(SUM(DATA_LENGTH+INDEX_LENGTH)/1024/1024, 2) FROM information_schema.TABLES WHERE TABLE_SCHEMA='$DB_NAME';")
RECOVERED=$(awk "BEGIN {printf \"%.2f\", ${FRAG_PRE:-0} - ${FRAG_POST:-0}}")
log "Post: Dimensione=${SIZE_POST}MB, Frammentazione=${FRAG_POST}MB"
log "Spazio frammentazione recuperato: ${RECOVERED}MB"

# STEP 7: Pulizia backup vecchi (mantieni ultimi 3 mesi)
log "STEP 7: Pulizia backup di manutenzione vecchi..."
find "$BACKUP_DIR" -name "${DB_NAME}_premaint_*.sql" -mtime +90 -delete 2>/dev/null
log "Backup più vecchi di 90 giorni eliminati"

log "=== MANUTENZIONE COMPLETATA — Spazio recuperato: ${RECOVERED}MB ==="
```

---

### Integrazione con ITIL: Cosa Abbiamo Imparato

**Quale pratica ITIL stiamo applicando?**

| Pratica ITIL | Come si manifesta in questo tutorial |
|---|---|
| **Capacity Management** | Monitoraggio spazio disco, trend crescita DB, pianificazione espansione |
| **Availability Management** | Hit rate buffer pool, I/O performance, nessun bottleneck storage |
| **Continual Improvement** | OPTIMIZE TABLE mensile, slow query review, riduzione debt tecnico |
| **Monitoring and Event Mgmt** | Script automatici, soglie, alerting → prevenzione incidenti |
| **Change Management** | Finestra manutenzione, backup pre-manutenzione, rollback plan |

**Il ciclo virtuoso storage/database:**

```
Monitoraggio continuo
      │
      ▼
Identificazione anomalia (spazio >80%, query lenta, hit rate calo)
      │
      ▼
Pianificazione intervento (ticket P2, finestra manutenzione)
      │
      ▼
Azione correttiva (OPTIMIZE, pulizia log, espansione storage)
      │
      ▼
Verifica efficacia (metriche prima/dopo)
      │
      ▼
Documentazione in GLPI + aggiornamento SOP
      │
      └──── torna a monitoraggio continuo
```

**Come scala a 500 server?**

```
In lab:  Esegui df -h e SHOW STATUS manualmente su 2-3 server
         → Funziona, ma non scala

Con 50+ server → strumenti centrali:
  Storage: Prometheus node_exporter → Grafana dashboard
           Alert: alert quando filesystem > 80%
           
  Database: mysqld_exporter → Grafana + Prometheus
            Metriche: buffer pool hit rate, slow queries/sec,
                      connections, replication lag
                      
  Database centralizzato: 
    - AWS RDS / Azure Database: metriche built-in
    - PostgreSQL: pg_stat_statements per slow queries
    - SQL Server: DMV + Query Store per analisi
    
Con 500+ server → policy automatica:
    Terraform/Ansible per configurazione storage standard
    GitOps per backup policies
    Runbook automation per OPTIMIZE TABLE
```

---

### Checklist di Validazione Lab

**Part A — Fondamenti:**
- [ ] Sai spiegare la differenza tra IOPS, Latenza e Throughput con esempi concreti
- [ ] Conosci le soglie thin provisioning: warning 70%, critico 85%, emergenza 95%
- [ ] Sai spiegare ACID con l'esempio del bonifico bancario
- [ ] Comprendi il ruolo del WAL/Transaction Log nel crash recovery
- [ ] Sai la differenza tra `OPTIMIZE TABLE` (MariaDB) e `VACUUM ANALYZE` (PostgreSQL)

**Part B — Operazioni:**
- [ ] `df -h` e `du -sh` usati per analisi spazio su Linux
- [ ] `lsblk` mostra la struttura block device del sistema
- [ ] `iostat -xz 5 3` campionato con comprensione di `%util` e `await`
- [ ] `Get-PSDrive` eseguito su DC-LAB-01 con classificazione WARNING/CRITICO
- [ ] Connessione a MariaDB via `docker exec` riuscita
- [ ] `information_schema.TABLES` interrogato per frammentazione e dimensione
- [ ] Buffer Pool Hit Rate calcolato
- [ ] `OPTIMIZE TABLE` eseguito su almeno una tabella
- [ ] `EXPLAIN` usato per analizzare un piano di query
- [ ] Binary log stati verificati con `SHOW BINARY LOGS`
- [ ] Report integrato B8 eseguito senza errori

**Part C — Sistematizzare:**
- [ ] SOP-STG-001 letta e compresa
- [ ] `storage_db_health.sh` deployato in `/opt/scripts/` e testato
- [ ] `db_maintenance.sh` letto e compreso il flusso backup → ottimizza → purge → verifica
- [ ] Connessione tra questo lavoro e le pratiche ITIL identificata
- [ ] Sai spiegare come questo processo si scala con Prometheus/mysqld_exporter

---

### Appendice A: Comandi Essenziali Storage

```bash
# LINUX STORAGE
df -h                        # Spazio per filesystem
df -hT                       # Con tipo filesystem
du -sh /var/*                # Top consumatori in /var
lsblk -o NAME,SIZE,ROTA,FSTYPE,MOUNTPOINT  # Block devices
iostat -xz 5 3               # Performance I/O (installa sysstat)
iostat -dxz 1 | grep -v "^$"# Monitoring continuo
smartctl -H /dev/sda         # SMART status disco fisico
sudo pvs; sudo vgs; sudo lvs # LVM status (se in uso)
cat /proc/mounts             # Mount points attivi
findmnt --real               # Struttura mount points

# WINDOWS STORAGE (PowerShell)
Get-PSDrive -PSProvider FileSystem       # Spazio tutti i drive
Get-Disk                                 # Dischi fisici
Get-Partition                            # Partizioni
Get-Volume                               # Volumi e spazio
Get-Counter "\PhysicalDisk(*)\*"         # Contatori PerfMon
Optimize-Volume -DriveLetter C -Analyze  # Analisi frammentazione NTFS
Optimize-Volume -DriveLetter C -Defrag   # Deframmentazione (solo HDD)

# DOCKER STORAGE
docker system df             # Spazio usato da Docker
docker volume ls             # Lista volumi
docker volume inspect nome   # Dettaglio volume
docker system prune -f       # Pulizia immagini/container non usati (ATTENZIONE)
```

---

### Appendice B: Comandi Essenziali MariaDB/MySQL

```sql
-- STATO MOTORE
SHOW STATUS LIKE 'Innodb_buffer%';       -- Buffer pool stats
SHOW VARIABLES LIKE 'innodb_buffer%';   -- Configurazione buffer pool
SHOW STATUS LIKE 'Connections';          -- Statistiche connessioni
SHOW STATUS LIKE 'Slow_queries';         -- Contatore slow queries
SHOW FULL PROCESSLIST;                   -- Processi attivi
SHOW SLAVE STATUS\G                      -- Stato replica (se configurata)
SHOW MASTER STATUS;                      -- Posizione nel binary log

-- ANALISI DATABASE
SELECT TABLE_NAME, 
       ROUND(DATA_LENGTH/1024/1024,2) Data_MB,
       ROUND(DATA_FREE/1024/1024,2) Frag_MB
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'glpi' ORDER BY DATA_FREE DESC;

-- MANUTENZIONE
OPTIMIZE TABLE nome_tabella;             -- Deframmentazione + rebuild indici
ANALYZE TABLE nome_tabella;              -- Aggiorna statistiche indici
REPAIR TABLE nome_tabella;               -- Ripara tabella corrotta (MyISAM)
CHECK TABLE nome_tabella;                -- Verifica integrità tabella

-- BINARY LOG
SHOW BINARY LOGS;                        -- Lista file log
SHOW BINLOG EVENTS IN 'mysql-bin.000001' LIMIT 20;  -- Contenuto log
PURGE BINARY LOGS BEFORE DATE_SUB(NOW(), INTERVAL 7 DAY);  -- Pulizia

-- SLOW QUERY
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;          -- Soglia in secondi
SET GLOBAL log_queries_not_using_indexes = 'ON';
-- Analisi: mysqldumpslow -s t -t 10 /var/log/mysql/slow.log

-- EXPLAIN
EXPLAIN SELECT * FROM glpi_tickets WHERE status = 1;
EXPLAIN FORMAT=JSON SELECT * FROM glpi_tickets WHERE status = 1;  -- Dettaglio
```

---

### Appendice C: Soglie di Riferimento

```
STORAGE — Linux (iostat):
  %util (utilizzo disco):   Normal < 70%   Warning 70-90%   Critical > 90%
  await (latenza I/O ms):   Normal < 20ms  Warning 20-50ms  Critical > 50ms
  
STORAGE — Windows (PerfMon):
  Avg Disk Queue Length:    Normal < 1     Warning 1-2      Critical > 2
  Avg Disk sec/Read:        Normal < 15ms  Warning 15-30ms  Critical > 30ms

DISCO — Spazio libero:
  Partizione sistema:       Normal > 25%   Warning 15-25%   Critical < 15%
  Partizione dati:          Normal > 20%   Warning 10-20%   Critical < 10%
  
THIN PROVISIONING:
  Utilizzo fisico:          Normal < 70%   Warning 70-85%   Critical/Emergency > 85%

DATABASE (MariaDB/MySQL):
  Buffer Pool Hit Rate:     Normal > 99%   Warning 95-99%   Critical < 95%
  Connessioni attive:       Normal < 70%   Warning 70-90%   Critical > 90% max_conn
  Frammentazione tabelle:   Normal < 30%   Warning 30-50%   Critical > 50%
  Slow queries/hour:        Normal < 10    Warning 10-100   Critical > 100
  Uptime dopo crash:        OK > 7 giorni  Warning < 2gg    Investigate crash logs
  
DATABASE (SQL Server — concetti):
  Buffer Pool Hit Rate:     Normal > 99%
  Page Life Expectancy:     Normal > 300s  Warning < 300s
  Index Fragmentation:      REORGANIZE 10-30%  REBUILD > 30%
  
RAID — sostituzione disco:
  SMART PASSED → operativo
  SMART WARNING → ordina disco sostitutivo SUBITO
  SMART FAILED → sostituzione immediata (sistema degradato)
  Rebuild in corso → MASSIMA PRIORITÀ — secondo guasto = perdita totale
```

---

### Riferimenti

- MariaDB Knowledge Base: Slow Query Log e OPTIMIZE TABLE
- MySQL 8.0 Reference: InnoDB Buffer Pool
- `04-servizi-infrastruttura.md` §Storage e §Database (documento sorgente)
- iostat(1) man page — interpretazione colonne `%util` e `await`
- ITIL 4: Capacity and Performance Management
- Tutorial prerequisiti: `tutorial_ops03b` (Linux Server), `tutorial_ops04_ch1a` (DNS/DHCP/NTP)
- Tutorial correlati: `tutorial_ops06_ch1a` (Backup Strategy) — backup database
