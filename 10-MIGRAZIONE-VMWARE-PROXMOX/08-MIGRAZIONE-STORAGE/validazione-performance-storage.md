# Validazione delle Performance Storage: Baseline, Benchmarking e Tuning

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 08.4 (chiude il cluster storage, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 03.1, 03.2 (storage Proxmox), 05.3 (capacity planning), 08.1-08.3 (conversione, cutover, strategie); concetti di percentile latency, queue depth, IOPS-vs-throughput trade-off.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. raccogliere baseline di performance pre-migrazione su VMware (vSAN performance, esxtop, vCenter perf charts) per tracciare un confronto post-migrazione misurabile;
> 2. eseguire benchmark `fio` su Proxmox con profili realistici (OLTP-like 70/30 RW 4K random, OLAP-like sequential 1M, mixed) e leggere correttamente p50/p95/p99 latency, IOPS, throughput;
> 3. confrontare le metriche pre/post-migrazione applicando il principio "compare apples to apples" (stesso workload, stessa configurazione cache, stesso queue depth);
> 4. eseguire tuning Proxmox: cache mode (`writeback`, `writethrough`, `none`), iothread per disco, NUMA pinning, ARC ZFS tuning, Ceph PG count optimization;
> 5. identificare bottleneck con metodologia USE (Brendan Gregg): saturation (queue length), utilization (% busy), errors (dmesg, iostat -e); applicarla a CPU, memoria, disco, rete;
> 6. produrre un report di validazione finale che dimostri SLO post-migrazione = SLO pre-migrazione (idealmente migliore) — input per il go-live formale.
> **Tempo stimato:** lettura 90-120 min · lab 360-480 min (include benchmark prima e dopo)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** fio ≥ 3.30, esxtop, OpenZFS 2.2/2.3, Ceph Squid 19.2, kernel 6.x.

## Mappa concettuale

```
+======================================================+
|  Performance validation — workflow                   |
+======================================================+
|                                                      |
|   STEP 1: BASELINE PRE-MIGRAZIONE (su VMware)        |
|     +-- vSphere perf charts (CPU, RAM, IOPS, NetIO)  |
|     +-- esxtop interactive ("v" mode = VM, "u" = LUN)|
|     +-- fio dentro la VM (su workload representative)|
|     +-- raccogliere p50/p95/p99 di IOPS e latency    |
|     +-- salvare baseline-VMNAME.json                 |
|         |                                            |
|         v                                            |
|   STEP 2: MIGRAZIONE (vedi moduli 06.x, 08.x)        |
|         |                                            |
|         v                                            |
|   STEP 3: BASELINE POST-MIGRAZIONE (su Proxmox)      |
|     +-- stesso fio profile della baseline pre        |
|     +-- iostat -xdz 5 in parallelo                   |
|     +-- pveperf (per FSYNC test rapido)              |
|     +-- raccogliere p50/p95/p99                      |
|         |                                            |
|         v                                            |
|   STEP 4: COMPARE                                    |
|     +-- ratio post/pre per IOPS, throughput, lat     |
|     +-- accettabile: post >= 0.9 * pre               |
|     +-- meglio: post > pre (miglioramenti)           |
|     +-- inaccettabile: post < 0.8 * pre              |
|         |                                            |
|         v                                            |
|   STEP 5 (se inaccettabile): TUNING                  |
|     +-- cache mode VM (writeback per buon HW         |
|     |   con UPS, writethrough per safety pure)       |
|     +-- iothread=1 sul disco                         |
|     +-- discard=on per LVM-Thin/ZFS                  |
|     +-- ZFS ARC: zfs_arc_max in bytes                |
|     +-- ZFS ZIL/SLOG: SSD dedicato per sync writes   |
|     +-- Ceph: pg_num adeguato (target 100 PG/OSD)    |
|     +-- Ceph BlueStore tuning                        |
|     +-- NUMA pinning per VM grandi                   |
|         |                                            |
|         v                                            |
|   STEP 6: REPORT                                     |
|     +-- delta perf per VM                            |
|     +-- giustificazione tuning applicato             |
|     +-- SLO conformity: PASS/FAIL                    |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **Baseline pre-migrazione e obbligatoria.** Senza, "le performance dopo sono brutte" e un'opinione, non un fatto. Misurare la stessa VM con stesso fio profile, stesso queue depth, stesso runtime — la baseline pre e il riferimento di tutto.
2. **fio fa quello che dici, non quello che vuoi.** I default di fio (block size 4K, single queue, single thread) producono numeri molto diversi dai workload reali. Workload OLTP DB e ~70/30 R/W mixed 4-8K random, queue depth 16-32. OLAP e sequential 1M, queue depth 8. Allinearsi ai pattern reali.
3. **Latency p99 conta piu di IOPS medio.** Una VM che ha 5000 IOPS medi ma p99 = 100 ms produce timeout applicativi. Una con 3000 IOPS medi ma p99 = 5 ms e meglio per molti workload. L'utente percepisce le code lunghe, non la media.
4. **Tuning e ultimo, non primo.** Prima validare misurando; poi, *se* il delta e inaccettabile, applicare tuning. Iniziare con tuning prima ancora di misurare e l'errore tipico — porta a configurazioni complesse senza giustificazione.
5. **Cache mode trade-off su KVM/QEMU.** `writethrough`: scrive sincrono, durabile ma lento; `writeback`: scrive in cache poi async to disk, veloce ma data loss possibile in crash; `none`: O_DIRECT al disco, performance prevedibile, no double cache. Per produzione con UPS + ECC RAM e backup robusto: `writeback` da il miglior throughput. Per minimum-risk: `writethrough`. Default Proxmox: `none` (O_DIRECT, sicuro).

## Indice
- [Panoramica](#panoramica)
- [Baseline Pre-Migrazione su VMware](#baseline-pre-migrazione-su-vmware)
- [Metriche Chiave dello Storage](#metriche-chiave-dello-storage)
- [Benchmarking con fio su Proxmox](#benchmarking-con-fio-su-proxmox)
- [Metodologia di Confronto delle Performance](#metodologia-di-confronto-delle-performance)
- [Storage Tuning su Proxmox](#storage-tuning-su-proxmox)
- [ZFS ARC Tuning](#zfs-arc-tuning)
- [Ceph PG Optimization](#ceph-pg-optimization)
- [Identificazione dei Bottleneck](#identificazione-dei-bottleneck)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

La validazione delle performance storage è la verifica obiettiva che l'ambiente Proxmox post-migrazione offra prestazioni comparabili o superiori all'ambiente VMware di origine. Senza una misurazione rigorosa, il rischio è duplice: da un lato, performance realmente degradate possono passare inosservate fino a quando non impattano gli utenti finali; dall'altro, percezioni soggettive di lentezza possono generare allarmi ingiustificati che ritardano il completamento della migrazione.

Il processo di validazione si articola in tre fasi: la raccolta del baseline pre-migrazione nell'ambiente VMware (utilizzando gli strumenti nativi come esxtop e le metriche di vCenter), il benchmarking sintetico nell'ambiente Proxmox post-migrazione (utilizzando fio come strumento standard di riferimento), e il confronto strutturato delle metriche secondo una metodologia che tenga conto delle differenze architetturali tra i due ambienti. Le metriche chiave — IOPS, throughput, latenza e queue depth — devono essere misurate sotto condizioni di carico comparabili.

Oltre alla validazione, questo documento copre il tuning post-migrazione dello storage Proxmox: la configurazione dell'I/O scheduler, la scelta del cache mode, l'abilitazione di discard/TRIM, l'ottimizzazione dell'ARC di ZFS e la configurazione dei Placement Groups di Ceph. L'obiettivo è fornire un toolkit completo per identificare e risolvere i bottleneck di performance storage che possono emergere dopo la migrazione.

---

## Baseline Pre-Migrazione su VMware

### esxtop: Raccolta Metriche in Tempo Reale

`esxtop` è lo strumento nativo di ESXi per il monitoraggio delle performance a livello host. Per lo storage, la vista "Disk Device" (premere `u`) e "Disk Adapter" (premere `d`) forniscono le metriche fondamentali.

```bash
# Connessione via SSH all'host ESXi
ssh root@esxi-01

# Avviare esxtop in modalità interattiva
esxtop

# Premere 'u' per la vista Disk Device (Virtual Machine)
# Premere 'v' per la vista Disk VM
```

Colonne chiave in esxtop per lo storage:

| Colonna | Metrica | Significato |
|---|---|---|
| CMDS/s | Commands per second | IOPS totali (read + write) |
| READS/s | Read commands/s | Read IOPS |
| WRITES/s | Write commands/s | Write IOPS |
| MBREAD/s | MB read per second | Read throughput |
| MBWRTN/s | MB written per second | Write throughput |
| LAT/rd | Read latency (ms) | Latenza media lettura |
| LAT/wr | Write latency (ms) | Latenza media scrittura |
| KAVG/rd | Kernel average read (ms) | Tempo nel kernel VMware |
| KAVG/wr | Kernel average write (ms) | Tempo nel kernel VMware |
| DAVG/rd | Device average read (ms) | Tempo nel dispositivo fisico |
| DAVG/wr | Device average write (ms) | Tempo nel dispositivo fisico |
| QAVG/rd | Queue average read | Queue depth media read |
| QAVG/wr | Queue average write | Queue depth media write |

```bash
# Raccolta in modalità batch per analisi offline
esxtop -b -d 5 -n 720 > /tmp/esxtop-baseline.csv
# -b: batch mode (output CSV)
# -d 5: intervallo 5 secondi
# -n 720: 720 campioni = 1 ora

# Trasferire il file per analisi
scp root@esxi-01:/tmp/esxtop-baseline.csv /tmp/
```

Interpretazione delle latenze:

```
Latenza Totale = GAVG = KAVG + DAVG + QAVG

DAVG (Device Average): tempo nel dispositivo storage fisico
  < 5 ms:   Eccellente (SSD/NVMe)
  5-10 ms:  Buono (SSD SATA, SAN buona)
  10-20 ms: Accettabile (HDD, SAN media)
  > 20 ms:  Problematico

KAVG (Kernel Average): tempo nel layer VMware
  < 2 ms:   Normale
  > 2 ms:   Possibile contesa risorse host (CPU, queue)

QAVG (Queue Average): tempo in attesa nella queue
  < 2 ms:   Normale
  > 2 ms:   Queue depth saturo, storage non riesce a tenere il passo
```

### vCenter Performance Charts

Per dati storici e trend a lungo termine, utilizzare i grafici di performance di vCenter:

```
vCenter → VM → Monitor → Performance → Advanced

Metriche da raccogliere (per ogni VM critica):
  Disk:
    - disk.numberReadAveraged.average (Read IOPS)
    - disk.numberWriteAveraged.average (Write IOPS)
    - disk.read.average (Read KB/s)
    - disk.write.average (Write KB/s)
    - disk.totalReadLatency.average (Read latency ms)
    - disk.totalWriteLatency.average (Write latency ms)
    - disk.maxQueueDepth.latest (Queue depth)

Periodo: ultimi 30 giorni (per catturare picchi settimanali)
Intervallo: Realtime per analisi puntuale, Daily per trend
```

Esportazione dati via PowerCLI:

```powershell
# PowerCLI: esportare metriche storage per una VM
$vm = Get-VM "VM-DB-Master"
$start = (Get-Date).AddDays(-7)
$end = Get-Date

$metrics = @(
    "disk.numberReadAveraged.average",
    "disk.numberWriteAveraged.average",
    "disk.read.average",
    "disk.write.average",
    "disk.totalReadLatency.average",
    "disk.totalWriteLatency.average"
)

$stats = Get-Stat -Entity $vm -Stat $metrics -Start $start -Finish $end -IntervalMins 5

$stats | Export-Csv -Path "C:\baseline\VM-DB-Master-storage-stats.csv" -NoTypeInformation
```

### Documentazione del Baseline

Creare un report strutturato per ogni VM critica:

```
=== BASELINE STORAGE: VM-DB-Master ===
Data raccolta:    2024-01-15 (7 giorni)
Datastore:        DS-PROD-01 (VMFS 6 su SAN FC 16Gbps)
Disco:            scsi0:0 - 500GB Thick Eager Zeroed

Metriche (media / p95 / picco):
  Read IOPS:      1,250 / 3,800 / 8,200
  Write IOPS:       850 / 2,100 / 5,500
  Read Throughput:   48 MB/s / 120 MB/s / 280 MB/s
  Write Throughput:  32 MB/s / 85 MB/s / 190 MB/s
  Read Latency:    0.8 ms / 2.1 ms / 8.5 ms
  Write Latency:   1.2 ms / 3.5 ms / 12.0 ms
  Queue Depth:       4 / 12 / 32

Pattern di I/O:
  - Workload misto 60% read / 40% write
  - Block size predominante: 8K (database)
  - Picchi giornalieri: 02:00-04:00 (backup), 09:00-11:00 (business)
  - I/O pattern: prevalentemente random
```

---

## Metriche Chiave dello Storage

### IOPS (Input/Output Operations Per Second)

Numero di operazioni di I/O completate al secondo. La metrica più utilizzata per workload random (database, virtual desktop).

```
Fattori che influenzano gli IOPS:
  - Tipo di media: HDD ~100-200, SSD SATA ~50K-100K, NVMe ~200K-1M
  - Block size: più piccolo il blocco, più IOPS possibili (ma meno throughput)
  - Profondità della queue: IOPS aumentano con queue depth fino alla saturazione
  - Read vs Write: le write sono generalmente più costose (specialmente su SSD con write amplification)
```

### Throughput (MB/s)

Volume di dati trasferiti per secondo. Metrica principale per workload sequenziali (backup, streaming, file server).

```
Relazione: Throughput (MB/s) = IOPS * Block_Size (KB) / 1024

Esempio:
  10,000 IOPS * 4 KB = ~39 MB/s  (workload random 4K)
  500 IOPS * 1 MB = ~500 MB/s    (workload sequenziale 1M)
```

### Latenza

Tempo necessario per completare una singola operazione I/O. La metrica più percepita dall'utente finale.

```
Componenti della latenza:

  Application → Guest OS → VirtIO/Driver → QEMU → Host OS → Storage
    ↑              ↑           ↑            ↑        ↑          ↑
  App delay    FS overhead  Paravirt   Emulation  I/O sched  Device
                                       overhead   + queue    latency

Soglie di accettabilità:
  < 1 ms:   Eccellente (NVMe locale, storage ben configurato)
  1-5 ms:   Buono (SSD, SAN performante)
  5-10 ms:  Accettabile (SAN media, NFS ben configurato)
  10-20 ms: Degradato (HDD, rete congestionata)
  > 20 ms:  Critico (richiede intervento immediato)
```

### Queue Depth

Numero di operazioni I/O in coda (inviate ma non ancora completate). Indica il grado di parallelismo dell'I/O.

```
Queue Depth ottimale:
  - Singolo HDD: 1-4 (dipende da NCQ)
  - SSD SATA: 4-32
  - NVMe: 32-256 (supporta migliaia)
  - SAN: dipende dal controller (tipicamente 32-256)

Queue Depth troppo basso → lo storage non è completamente utilizzato
Queue Depth troppo alto → latenza aumenta per congestione
```

---

## Benchmarking con fio su Proxmox

### Installazione e Preparazione

```bash
# Installare fio (di solito pre-installato su Proxmox)
apt install fio

# IMPORTANTE: eseguire i test dentro la VM guest, NON sull'host Proxmox
# Questo misura la catena completa: guest → VirtIO → QEMU → host → storage

# Dentro la VM Linux
apt install fio    # Debian/Ubuntu
dnf install fio    # RHEL/Rocky
```

### Test Standard: Random Read 4K

Il test fondamentale per workload database e applicativi:

```bash
fio --name=randread-4k \
    --ioengine=libaio \
    --rw=randread \
    --bs=4k \
    --numjobs=4 \
    --iodepth=32 \
    --size=4G \
    --runtime=120 \
    --time_based \
    --direct=1 \
    --group_reporting \
    --filename=/tmp/fio-test \
    --output=randread-4k.json \
    --output-format=json

# Parametri spiegati:
# --ioengine=libaio   : I/O asincrono Linux (più realistico)
# --rw=randread       : letture random
# --bs=4k             : block size 4 KB
# --numjobs=4         : 4 thread paralleli
# --iodepth=32        : 32 I/O in-flight per thread
# --size=4G           : file di test 4 GB (deve superare la RAM per evitare cache)
# --runtime=120       : durata 120 secondi
# --time_based        : esegui per tutto il runtime indipendentemente dalla size
# --direct=1          : O_DIRECT, bypassa page cache del guest OS
# --group_reporting   : risultati aggregati
```

Output significativo:

```
randread-4k: (groupid=0, jobs=4): err= 0: pid=1234
  read: IOPS=45.2k, BW=176MiB/s (185MB/s)
    slat (nsec): min=1200, max=85420, avg=2850
    clat (usec): min=120, max=12500, avg=2810, stdev=1450
     lat (usec): min=125, max=12520, avg=2813
    clat percentiles (usec):
     |  1.00th=[  400], 5.00th=[  620], 10.00th=[ 890],
     | 50.00th=[ 2540], 90.00th=[ 4620], 95.00th=[ 5800],
     | 99.00th=[ 8640], 99.50th=[ 9900], 99.99th=[12400]
   bw (  KiB/s): min=165000, max=192000, avg=180500
   iops        : min=41250, max=48000, avg=45125
  lat (usec)   : 250=0.50%, 500=3.20%, 750=5.80%, 1000=4.50%
  lat (msec)   : 2=18.00%, 4=42.00%, 10=25.50%, 20=0.50%
```

### Test Standard: Random Write 4K

```bash
fio --name=randwrite-4k \
    --ioengine=libaio \
    --rw=randwrite \
    --bs=4k \
    --numjobs=4 \
    --iodepth=32 \
    --size=4G \
    --runtime=120 \
    --time_based \
    --direct=1 \
    --group_reporting \
    --filename=/tmp/fio-test \
    --output=randwrite-4k.json \
    --output-format=json
```

### Test Standard: Mixed Random Read/Write (70/30)

Il test più rappresentativo di workload reali:

```bash
fio --name=mixed-randrw \
    --ioengine=libaio \
    --rw=randrw \
    --rwmixread=70 \
    --bs=4k \
    --numjobs=4 \
    --iodepth=32 \
    --size=4G \
    --runtime=120 \
    --time_based \
    --direct=1 \
    --group_reporting \
    --filename=/tmp/fio-test \
    --output=mixed-randrw.json \
    --output-format=json
```

### Test Sequential Read/Write (Throughput)

Per workload di backup, streaming, file server:

```bash
# Sequential read
fio --name=seqread \
    --ioengine=libaio \
    --rw=read \
    --bs=1M \
    --numjobs=1 \
    --iodepth=8 \
    --size=4G \
    --runtime=60 \
    --time_based \
    --direct=1 \
    --filename=/tmp/fio-test \
    --output=seqread.json --output-format=json

# Sequential write
fio --name=seqwrite \
    --ioengine=libaio \
    --rw=write \
    --bs=1M \
    --numjobs=1 \
    --iodepth=8 \
    --size=4G \
    --runtime=60 \
    --time_based \
    --direct=1 \
    --filename=/tmp/fio-test \
    --output=seqwrite.json --output-format=json
```

### Test Specifici per Workload Database

```bash
# Simulazione OLTP (MySQL/PostgreSQL)
fio --name=oltp \
    --ioengine=libaio \
    --rw=randrw \
    --rwmixread=75 \
    --bs=8k \
    --numjobs=8 \
    --iodepth=16 \
    --size=4G \
    --runtime=180 \
    --time_based \
    --direct=1 \
    --group_reporting \
    --filename=/tmp/fio-test \
    --output=oltp.json --output-format=json

# Simulazione OLAP (query pesanti, letture sequenziali)
fio --name=olap \
    --ioengine=libaio \
    --rw=read \
    --bs=256k \
    --numjobs=4 \
    --iodepth=8 \
    --size=4G \
    --runtime=180 \
    --time_based \
    --direct=1 \
    --group_reporting \
    --filename=/tmp/fio-test \
    --output=olap.json --output-format=json
```

### Script di Benchmark Completo

```bash
#!/bin/bash
# storage-benchmark.sh - Suite completa di benchmark storage
# Eseguire dentro la VM guest

OUTPUT_DIR="/tmp/fio-results-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTPUT_DIR"
TEST_FILE="/tmp/fio-test"
SIZE="4G"
RUNTIME=120

echo "=== Storage Benchmark Suite ==="
echo "Output directory: $OUTPUT_DIR"
echo "Test file: $TEST_FILE (size: $SIZE)"
echo "Runtime per test: ${RUNTIME}s"
echo ""

# Pre-fill test file
echo "[PREFILL] Creazione file di test..."
fio --name=prefill --ioengine=libaio --rw=write --bs=1M \
    --numjobs=1 --iodepth=8 --size=$SIZE --direct=1 \
    --filename=$TEST_FILE > /dev/null 2>&1

declare -A TESTS
TESTS[01-randread-4k]="--rw=randread --bs=4k --numjobs=4 --iodepth=32"
TESTS[02-randwrite-4k]="--rw=randwrite --bs=4k --numjobs=4 --iodepth=32"
TESTS[03-randrw-4k-70-30]="--rw=randrw --rwmixread=70 --bs=4k --numjobs=4 --iodepth=32"
TESTS[04-seqread-1M]="--rw=read --bs=1M --numjobs=1 --iodepth=8"
TESTS[05-seqwrite-1M]="--rw=write --bs=1M --numjobs=1 --iodepth=8"
TESTS[06-oltp-8k]="--rw=randrw --rwmixread=75 --bs=8k --numjobs=8 --iodepth=16"

for test_name in $(echo "${!TESTS[@]}" | tr ' ' '\n' | sort); do
    params="${TESTS[$test_name]}"
    echo "[TEST] ${test_name}..."
    fio --name="$test_name" --ioengine=libaio $params \
        --size=$SIZE --runtime=$RUNTIME --time_based --direct=1 \
        --group_reporting --filename=$TEST_FILE \
        --output="${OUTPUT_DIR}/${test_name}.json" \
        --output-format=json
    echo "  Completato."
    sleep 5  # Pausa tra i test per stabilizzare I/O
done

# Riepilogo
echo ""
echo "=== RIEPILOGO ==="
for f in "$OUTPUT_DIR"/*.json; do
    test=$(basename "$f" .json)
    iops_r=$(jq -r '.jobs[0].read.iops // 0' "$f" 2>/dev/null)
    iops_w=$(jq -r '.jobs[0].write.iops // 0' "$f" 2>/dev/null)
    bw_r=$(jq -r '.jobs[0].read.bw // 0' "$f" 2>/dev/null)
    bw_w=$(jq -r '.jobs[0].write.bw // 0' "$f" 2>/dev/null)
    lat_r=$(jq -r '.jobs[0].read.clat_ns.mean // 0' "$f" 2>/dev/null)
    lat_w=$(jq -r '.jobs[0].write.clat_ns.mean // 0' "$f" 2>/dev/null)

    printf "%-25s  R-IOPS: %8.0f  W-IOPS: %8.0f  R-BW: %6.0f KB/s  W-BW: %6.0f KB/s  R-Lat: %8.0f ns  W-Lat: %8.0f ns\n" \
        "$test" "$iops_r" "$iops_w" "$bw_r" "$bw_w" "$lat_r" "$lat_w"
done

# Cleanup
rm -f $TEST_FILE
echo ""
echo "Risultati salvati in: $OUTPUT_DIR"
```

---

## Metodologia di Confronto delle Performance

### Principi Fondamentali

1. **Condizioni comparabili**: i test su Proxmox devono replicare le condizioni del baseline VMware (stessa VM, stesso carico, stesso periodo della giornata se possibile).
2. **Test sintetici E applicativi**: i benchmark sintetici (fio) forniscono numeri confrontabili, ma il test finale deve essere con il workload applicativo reale.
3. **Metriche multiple**: non giudicare da una sola metrica. IOPS alti con latenza elevata sono peggio di IOPS medi con latenza bassa.
4. **Tolleranza accettabile**: una variazione del +/- 10% è generalmente accettabile nelle metriche di performance tra ambienti diversi.

### Tabella di Confronto

```
+--------------------+------------------+------------------+-----------+
| Metrica            | VMware Baseline  | Proxmox Misurato | Delta (%) |
+--------------------+------------------+------------------+-----------+
| Rand Read IOPS     | 42,000           | 45,200           | +7.6%     |
| Rand Write IOPS    | 18,500           | 17,800           | -3.8%     |
| Rand Read Lat (ms) | 2.5              | 2.8              | +12.0%    |
| Rand Write Lat (ms)| 3.2              | 3.5              | +9.4%     |
| Seq Read (MB/s)    | 520              | 580              | +11.5%    |
| Seq Write (MB/s)   | 380              | 410              | +7.9%     |
| Mixed R/W IOPS     | 35,000           | 38,200           | +9.1%     |
| Queue Depth avg    | 8                | 10               | +25.0%    |
+--------------------+------------------+------------------+-----------+
Criteri:
  Verde  (<= +/-10%): Comparabile, migrazione OK
  Giallo (10-20%):     Marginale, investigare
  Rosso  (> 20%):      Degradazione significativa, tuning richiesto
```

### Fattori di Aggiustamento

Alcuni fattori rendono il confronto non diretto:

```
1. Paravirtualizzazione:
   VMware (PVSCSI) vs Proxmox (VirtIO SCSI)
   - VirtIO generalmente comparabile o migliore di PVSCSI
   - Se la VM usa IDE emulato, le performance saranno molto peggiori

2. Cache mode:
   VMware gestisce il caching internamente
   Proxmox: none/writethrough/writeback hanno impatto significativo

3. I/O scheduler:
   VMware usa scheduler proprietario
   Linux host: none/mq-deadline/bfq/kyber

4. Formato disco:
   VMware: VMDK flat (raw-like)
   Proxmox: raw (comparabile), qcow2 (overhead ~5-15%)
```

---

## Storage Tuning su Proxmox

### I/O Scheduler

L'I/O scheduler del kernel Linux sull'host Proxmox influenza le performance di tutte le VM:

```bash
# Verificare lo scheduler corrente
cat /sys/block/sda/queue/scheduler
# [mq-deadline] kyber bfq none

# Raccomandazioni per tipo di dispositivo:
# NVMe:  none (noop) - il dispositivo ha il suo scheduler interno
# SSD:   none o mq-deadline
# HDD:   mq-deadline o bfq
# RAID:  mq-deadline
```

```bash
# Cambiare lo scheduler (runtime)
echo none > /sys/block/nvme0n1/queue/scheduler
echo mq-deadline > /sys/block/sda/queue/scheduler

# Rendere persistente con udev rule
cat > /etc/udev/rules.d/60-io-scheduler.rules << 'EOF'
# NVMe: nessuno scheduler (il controller interno è ottimale)
ACTION=="add|change", KERNEL=="nvme[0-9]*n[0-9]*", ATTR{queue/scheduler}="none"

# SSD SATA: none o mq-deadline
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="none"

# HDD: mq-deadline
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="mq-deadline"
EOF

udevadm control --reload-rules
udevadm trigger
```

### Cache Mode del Disco VM

Il cache mode in Proxmox controlla come QEMU gestisce il write cache:

| Mode | Dati in Write Cache Host | Sicurezza | Performance | Use Case |
|---|---|---|---|---|
| `none` | No | Massima (O_DIRECT) | Buona | Default, SAN con BBU |
| `writethrough` | Sì (read cache only) | Alta | Buona read, write come none | General purpose |
| `writeback` | Sì (read + write cache) | Rischio perdita dati | Massima | Storage con BBU/capacitor |
| `unsafe` | Sì, senza flush | Pericoloso | Massima assoluta | Solo test, MAI in produzione |
| `directsync` | No + fsync ogni write | Massima assoluta | Peggiore | Requisiti critici integrità |

```bash
# Verificare il cache mode corrente
qm config 100 | grep scsi0
# scsi0: local-lvm:vm-100-disk-0,cache=none,iothread=1

# Cambiare cache mode (VM spenta)
qm set 100 --scsi0 local-lvm:vm-100-disk-0,cache=writeback,iothread=1

# Raccomandazioni:
# Storage con protezione write-cache (BBU, capacitor): writeback
# Storage senza protezione (NVMe consumer, HDD): none o writethrough
# ZFS: none (ZFS gestisce il caching con ARC/ZIL)
# Ceph: writeback (Ceph gestisce la replica)
```

### Discard / TRIM

Discard permette al guest OS di informare lo storage che determinati blocchi non sono più in uso, fondamentale per thin provisioning:

```bash
# Abilitare discard nella configurazione VM
qm set 100 --scsi0 local-lvm:vm-100-disk-0,discard=on

# Dentro la VM Linux, verificare il supporto
lsblk -D
# NAME   DISC-ALN DISC-GRAN DISC-MAX DISC-ZERO
# sda           0       4K      2G         0

# Eseguire TRIM manuale
fstrim -av

# Configurare TRIM automatico periodico
systemctl enable --now fstrim.timer
# Esegue fstrim settimanalmente

# Per ext4, montare con opzione discard (TRIM continuo, opzionale)
# /etc/fstab:
# /dev/sda1  /  ext4  defaults,discard  0  1
# NOTA: discard continuo ha leggero overhead, fstrim periodico è preferibile
```

### VirtIO SCSI e I/O Threads

```bash
# Configurazione ottimale per performance:
qm set 100 \
    --scsihw virtio-scsi-single \
    --scsi0 local-lvm:vm-100-disk-0,iothread=1,discard=on,cache=writeback

# virtio-scsi-single: un controller SCSI per disco, massimo parallelismo
# iothread=1: thread I/O dedicato per questo disco
# Ogni disco con iothread usa un thread host separato
```

### Queue Depth e nr_requests

```bash
# Sull'host Proxmox, ottimizzare la queue depth del dispositivo
cat /sys/block/nvme0n1/queue/nr_requests
# 1024 (default NVMe)

# Per HDD/SSD SATA, potrebbe essere necessario aumentare
echo 256 > /sys/block/sda/queue/nr_requests

# Dentro la VM, verificare la queue depth vista dal guest
cat /sys/block/sda/queue/nr_requests
```

---

## ZFS ARC Tuning

### Cos'è l'ARC

L'ARC (Adaptive Replacement Cache) è il meccanismo di caching in-RAM di ZFS. Usa la RAM dell'host per cacheare i blocchi letti dallo storage, riducendo drasticamente la latenza per dati acceduti frequentemente.

```
Struttura dell'ARC:
+------------------------------------------------------+
|                    ARC (RAM)                          |
|  +------------------+  +------------------+          |
|  | MRU (Most        |  | MFU (Most        |          |
|  | Recently Used)   |  | Frequently Used) |          |
|  | Lista recente    |  | Lista frequente  |          |
|  +------------------+  +------------------+          |
|                                                      |
|  Ghost Lists (MRU Ghost, MFU Ghost):                 |
|  Metadati di blocchi evicted per decisioni future     |
+------------------------------------------------------+
         ↕
+------------------------------------------------------+
|  L2ARC (opzionale, su SSD dedicato)                  |
|  Cache di secondo livello per working set > RAM      |
+------------------------------------------------------+
         ↕
+------------------------------------------------------+
|  Storage Pool (HDD/SSD/NVMe)                         |
+------------------------------------------------------+
```

### Configurazione Dimensione ARC

```bash
# Verificare l'utilizzo corrente dell'ARC
arc_summary
# Oppure
cat /proc/spl/kstat/zfs/arcstats | grep -E "^size|^c_max|^c_min|^hits|^misses"

# Output significativo:
# size    4    8589934592   (dimensione corrente: 8 GB)
# c_max   4    16777216000  (dimensione massima: ~16 GB)
# c_min   4    1073741824   (dimensione minima: 1 GB)
# hits    4    5842901      (cache hit)
# misses  4    423810       (cache miss)
```

Calcolo dell'ARC hit ratio:

```bash
# Hit ratio = hits / (hits + misses) * 100
# > 90%: ottimo
# 80-90%: buono
# < 80%: considerare aumentare ARC o aggiungere L2ARC
```

Dimensionamento dell'ARC per Proxmox:

```
Regola pratica:
  RAM totale host:          64 GB
  - RAM per Proxmox OS:     2 GB
  - RAM per VM:            48 GB (somma di tutte le VM)
  - RAM per ZFS ARC:       14 GB (il resto)
  - RAM minima ZFS:         1 GB per TB di storage

Formula: ARC_max = RAM_totale - RAM_OS - RAM_VM - 2GB_margine
```

```bash
# Impostare il limite ARC (in byte)
# Esempio: 14 GB
echo 15032385536 > /sys/module/zfs/parameters/zfs_arc_max

# Rendere persistente
cat >> /etc/modprobe.d/zfs.conf << 'EOF'
# ZFS ARC: limitare a 14 GB (su host con 64 GB RAM)
options zfs zfs_arc_max=15032385536
options zfs zfs_arc_min=4294967296
EOF

# Aggiornare initramfs
update-initramfs -u
```

### L2ARC (Level 2 ARC)

Per working set che superano la RAM disponibile, aggiungere un SSD come L2ARC:

```bash
# Aggiungere un SSD come cache device
zpool add rpool cache /dev/sdc

# Verificare
zpool status rpool
# cache
#   sdc       ONLINE       0     0     0

# Tuning L2ARC
# Velocità di riempimento L2ARC (byte/s)
echo 524288000 > /sys/module/zfs/parameters/l2arc_write_max  # 500 MB/s

# Abilitare scrittura di dati (non solo metadati) in L2ARC
echo 1 > /sys/module/zfs/parameters/l2arc_noprefetch
```

### ZIL (ZFS Intent Log) e SLOG

Lo ZIL gestisce le synchronous write. Un SLOG (Separate Log device) su SSD veloce accelera le sync write:

```bash
# Aggiungere un SLOG (mirror per sicurezza)
zpool add rpool log mirror /dev/nvme1n1p1 /dev/nvme2n1p1

# Dimensione raccomandata del SLOG: 5-10 secondi di sync write throughput
# Esempio: se sync writes = 200 MB/s → SLOG = 1-2 GB è sufficiente
```

### Record Size per VM

```bash
# Per zvol (dischi VM), il record size è chiamato volblocksize
# Default: 8K (ottimale per database)
# Per file server: 128K

# Impostare al momento della creazione del dataset
zfs set recordsize=8K rpool/data    # Per workload database
zfs set recordsize=128K rpool/data  # Per workload general purpose

# NOTA: volblocksize è immutabile dopo la creazione dello zvol
# Pianificare prima della migrazione!
```

---

## Ceph PG Optimization

### Verifica Distribuzione PG

```bash
# Stato dei PG
ceph pg stat
# 256 pgs: 256 active+clean; 1.2 TiB data, 3.6 TiB used, 12.4 TiB / 16 TiB avail

# Distribuzione PG per OSD
ceph osd df tree
# ID  CLASS  WEIGHT   REWEIGHT  SIZE    RAW USE  DATA    OMAP  META  AVAIL    %USE
#  0  ssd    1.82     1.00000   1.82T    425G    423G    0B    2G    1.41T   22.82
#  1  ssd    1.82     1.00000   1.82T    432G    430G    0B    2G    1.40T   23.20
#  ...

# Verificare distribuzione uniforme
ceph osd utilization
# avg 23.01, min 22.50 (osd.0), max 23.80 (osd.5)
# Se la differenza max-min > 10%, il bilanciamento non è ottimale
```

### Calcolo PG Ottimale

```bash
# Formula: PG = (target_PG_per_OSD * OSD_count) / replica_size
# Target: 100-200 PG per OSD
# Arrotondare alla potenza di 2 più vicina

# Esempio pratico:
# 12 OSD, replica 3, 1 pool
# PG = (100 * 12) / 3 = 400 → 512 (potenza di 2)

# Con più pool, dividere equamente:
# Pool VM (70% dati): 256 PG
# Pool CephFS (30% dati): 128 PG

# Utilizzare il PG calculator di Ceph
ceph osd pool autoscale-status
# POOL      SIZE  TARGET SIZE  RATE  RAW CAPACITY  RATIO  TARGET RATIO  PG_NUM  NEW PG_NUM  AUTOSCALE
# vm-pool   1.2T              3.0         16.0T    0.22                 256     256         on
```

### Ottimizzazione Runtime

```bash
# Abilitare autoscale (raccomandato)
ceph osd pool set vm-pool pg_autoscale_mode on

# Se necessario, modificare manualmente
ceph osd pool set vm-pool pg_num 512
# pgp_num viene automaticamente allineato nelle versioni recenti

# Recovery tuning durante la migrazione
# Ridurre la priorità del recovery per non impattare le VM
ceph config set osd osd_recovery_max_active 1
ceph config set osd osd_recovery_sleep 0.1

# Dopo la migrazione, ripristinare per recovery più veloce
ceph config set osd osd_recovery_max_active 3
ceph config set osd osd_recovery_sleep 0
```

### BlueStore Tuning

```bash
# Verificare la configurazione BlueStore
ceph config dump | grep bluestore

# Cache size per OSD (default: auto)
ceph config set osd bluestore_cache_size_ssd 4294967296  # 4 GB per SSD
ceph config set osd bluestore_cache_size_hdd 1073741824  # 1 GB per HDD

# Block size (per allineamento con workload)
# Default: 4096 (4K) per min_alloc_size su SSD
# Verificare
ceph config get osd.0 bluestore_min_alloc_size_ssd

# WAL e DB su device separati (se non già configurati)
# Questo accelera i metadati e il journaling
# Deve essere fatto al momento della creazione dell'OSD
```

---

## Identificazione dei Bottleneck

### Metodologia Sistematica

```
Livello 1: VM Guest
  └─ Applicazione → Filesystem → Block device driver
      Strumenti: iostat, top, iotop (dentro la VM)

Livello 2: Virtualizzazione
  └─ VirtIO/SCSI → QEMU process → I/O thread
      Strumenti: qm monitor, strace qemu-process

Livello 3: Host OS
  └─ I/O scheduler → Block layer → Device driver
      Strumenti: iostat, blktrace, bpftrace (sull'host)

Livello 4: Storage Backend
  └─ LVM/ZFS/Ceph → Dispositivo fisico
      Strumenti: zpool iostat, ceph perf, smartctl
```

### Strumenti Diagnostici sull'Host Proxmox

```bash
# iostat: panoramica I/O per dispositivo
iostat -xz 1 5
# Device     r/s     w/s   rMB/s   wMB/s  rrqm/s  wrqm/s  %rrqm  %wrqm r_await w_await  aqu-sz  rareq-sz  wareq-sz  svctm  %util
# nvme0n1   4500   2800   17.58   10.94    0.00    120   0.00   4.11    0.42    0.85    3.58     4.00      4.00   0.12  89.50

# Metriche critiche:
# r_await/w_await: latenza in ms (deve essere < 5ms per SSD)
# %util: utilizzo del dispositivo (> 95% = saturo)
# aqu-sz: queue size media (alto = congestione)

# Per ZFS
zpool iostat -v rpool 1
# capacity     operations     bandwidth
# pool        alloc   free   read  write   read  write
# rpool       1.20T  14.8T  4.52K  2.81K  17.7M  11.0M
#   mirror     1.20T  14.8T  4.52K  2.81K  17.7M  11.0M
#     sda          -      -  2.26K  1.40K  8.83M  5.49M
#     sdb          -      -  2.26K  1.41K  8.85M  5.51M

# Per Ceph
ceph osd perf
# osd  commit_latency(ms)  apply_latency(ms)
#   0                   1                   2
#   1                   1                   1
# commit_latency > 10ms = disco OSD lento
# apply_latency > 20ms = OSD sovraccarico
```

### Identificazione del Collo di Bottiglia

```bash
# Passo 1: è un problema di CPU?
top -d 1
# Cercare processi qemu con alto %CPU
# Se CPU > 80% per un processo QEMU → bottleneck CPU

# Passo 2: è un problema di I/O?
iostat -xz 1
# Se %util > 95% → dispositivo saturo
# Se await > 10ms su SSD → latenza anomala

# Passo 3: è un problema di rete? (per NFS/iSCSI/Ceph)
sar -n DEV 1 5
# Se rxkB/s o txkB/s si avvicinano alla capacità del link → rete satura
# 10GbE max: ~1,250,000 KB/s

# Passo 4: è un problema di RAM/cache?
# Per ZFS
arc_summary | grep -A 5 "ARC Size"
# Se ARC hit ratio < 80% → RAM insufficiente per ARC
# Per Ceph
ceph osd perf | awk '$3 > 10 {print "Slow OSD:", $1, "commit:", $2, "apply:", $3}'

# Passo 5: è un problema del guest?
# Dentro la VM:
iostat -xz 1 5
# Se await è basso ma l'applicazione è lenta → non è un problema storage
# Verificare CPU e memoria dentro la VM
```

### Matrice Decisionale Bottleneck → Soluzione

```
+---------------------+------------------------+---------------------------+
| Sintomo             | Probabile Causa        | Soluzione                 |
+---------------------+------------------------+---------------------------+
| %util 100%, await   | Dispositivo saturo     | Upgrade storage (NVMe),   |
| alto                |                        | distribuire I/O su più    |
|                     |                        | dispositivi               |
+---------------------+------------------------+---------------------------+
| await alto, %util   | Latenza rete (NFS/     | Ottimizzare rete, jumbo   |
| basso               | iSCSI)                 | frames, separare traffico |
+---------------------+------------------------+---------------------------+
| IOPS bassi ma await | Queue depth troppo     | Aumentare iodepth nella   |
| basso               | basso                  | VM, verificare virtio     |
+---------------------+------------------------+---------------------------+
| IOPS alti ma app    | Applicazione single-   | Non è un problema storage,|
| lenta               | threaded o CPU-bound   | ottimizzare applicazione  |
+---------------------+------------------------+---------------------------+
| Write latency molto | Cache mode 'none'      | Passare a 'writeback'     |
| superiore a VMware  | senza BBU              | se storage ha BBU         |
+---------------------+------------------------+---------------------------+
| ZFS latenza spikes  | ARC troppo piccolo,    | Aumentare ARC, aggiungere |
| periodiche          | eviction frequente     | L2ARC, verificare SLOG    |
+---------------------+------------------------+---------------------------+
| Ceph latenza alta   | PG sbilanciati, OSD    | Rebalance PG, verificare  |
| non uniforme        | lenti, rete satura     | OSD slow, rete cluster    |
+---------------------+------------------------+---------------------------+
```

---

## Best Practices

- Raccogliere il baseline VMware con almeno 7 giorni di dati prima della migrazione; includere metriche di picco (p95, p99), non solo medie.
- Utilizzare `fio` con parametri identici su VMware e Proxmox per un confronto sintetico valido; documentare esattamente i parametri usati.
- Impostare l'I/O scheduler `none` (noop) per dispositivi NVMe sull'host Proxmox; il controller NVMe ha il suo scheduler ottimizzato.
- Utilizzare `virtio-scsi-single` con `iothread=1` per ogni disco VM per massimizzare il parallelismo I/O.
- Scegliere il cache mode in base alla protezione write-cache dello storage: `writeback` con BBU/capacitor, `none` senza protezione, `writethrough` come compromesso.
- Abilitare `discard=on` sui dischi VM e configurare `fstrim.timer` nel guest per mantenere l'efficienza del thin provisioning.
- Per ZFS, dimensionare l'ARC in modo che rimanga RAM sufficiente per tutte le VM; un ARC troppo grande causa memory pressure e ballooning nelle VM.
- Per Ceph, monitorare `ceph osd perf` regolarmente; un singolo OSD lento degrada le performance dell'intero pool.
- Non confrontare i numeri di fio direttamente tra VMware e Proxmox senza considerare le differenze architetturali (paravirtualizzazione, cache mode, formato disco).
- Eseguire i benchmark di validazione dentro la VM guest, non sull'host; questo misura l'intero stack di virtualizzazione.
- Mantenere un registro delle metriche di performance per ogni VM critica con misurazioni settimanali per i primi 30 giorni dopo la migrazione.
- Per ZFS zvol, impostare il `volblocksize` appropriato al workload prima della creazione (8K per database, 64K-128K per general purpose); questa proprietà è immutabile.

---

## Troubleshooting

### Problema: latenza write molto superiore su Proxmox rispetto a VMware
**Sintomi**: la latenza delle scritture su Proxmox è 3-5x superiore al baseline VMware. Le letture sono comparabili.
**Causa**: la causa più comune è il cache mode impostato su `none` (O_DIRECT) in Proxmox, mentre VMware utilizza un layer di caching interno trasparente. Con `cache=none`, ogni write va direttamente allo storage senza buffering host.
**Soluzione**:
```bash
# Verificare il cache mode
qm config 100 | grep scsi
# Cambiare a writeback (se lo storage ha protezione write-cache)
qm set 100 --scsi0 local-lvm:vm-100-disk-0,cache=writeback,iothread=1

# Se lo storage NON ha BBU, usare writethrough
qm set 100 --scsi0 local-lvm:vm-100-disk-0,cache=writethrough,iothread=1

# Riavviare la VM e ripetere il benchmark
qm stop 100 && qm start 100
```
**Prevenzione**: documentare il tipo di protezione write-cache dello storage prima della migrazione e configurare il cache mode appropriato fin dalla creazione della VM.

### Problema: performance ZFS degradate sotto carico elevato, latenza a spikes
**Sintomi**: durante picchi di I/O, la latenza ZFS aumenta improvvisamente a 50-200 ms per poi tornare normale. Il fenomeno è periodico.
**Causa**: il Transaction Group (TXG) commit di ZFS accumula le write e le fluscia periodicamente (default ogni 5 secondi o quando raggiunge una soglia). Se il volume di write è elevato, il flush causa uno spike di latenza. Inoltre, se l'ARC è troppo grande, il sistema può essere in memory pressure.
**Soluzione**:
```bash
# Ridurre l'intervallo TXG per flush più frequenti e meno impattanti
echo 3 > /sys/module/zfs/parameters/zfs_txg_timeout  # 3 secondi

# Verificare memory pressure
free -h
arc_summary | grep "ARC Size"
# Se ARC sta usando quasi tutta la RAM libera, ridurre il limite
echo 8589934592 > /sys/module/zfs/parameters/zfs_arc_max  # 8 GB

# Aggiungere SLOG per accelerare le sync write
zpool add rpool log mirror /dev/nvme1n1p1 /dev/nvme2n1p1

# Verificare la compressione — compressione elevata usa CPU
zfs get compression,compressratio rpool/data
# Se CPU è il bottleneck, passare da zstd a lz4
zfs set compression=lz4 rpool/data
```
**Prevenzione**: dimensionare l'ARC conservativamente, lasciando almeno 4 GB liberi per il kernel e i processi QEMU. Aggiungere SLOG per workload write-intensive.

### Problema: IOPS Ceph molto inferiori al previsto con NVMe
**Sintomi**: gli OSD Ceph sono su NVMe ma gli IOPS misurati sono 10-20K invece dei 100K+ attesi.
**Causa**: le cause più probabili sono: (1) il numero di PG è troppo basso, causando hotspot su pochi OSD; (2) la rete cluster è il bottleneck (1 GbE invece di 10 GbE); (3) il WAL/DB condivide lo stesso NVMe con i dati; (4) il pool ha replica 3 con min_size 2, triplicando le write.
**Soluzione**:
```bash
# Verificare PG distribution
ceph osd df tree
# Se i PG non sono distribuiti uniformemente:
ceph osd pool set vm-pool pg_num 512

# Verificare il throughput della rete cluster
iperf3 -c <altro-nodo-cluster-ip> -t 10
# Se < 1 Gbps, la rete è il bottleneck

# Verificare la latenza OSD
ceph osd perf
# commit_latency > 5ms su NVMe = anomalo

# Separare WAL/DB su dispositivo dedicato
# (richiede ri-creazione dell'OSD)
ceph-volume lvm create --data /dev/nvme0n1 --block.db /dev/nvme1n1p1
```
**Prevenzione**: utilizzare rete 10 GbE o superiore per il cluster Ceph. Calcolare i PG correttamente prima della creazione del pool. Separare WAL/DB se le write sono intensive.

### Problema: fio mostra IOPS alti ma l'applicazione è lenta
**Sintomi**: i benchmark fio nella VM mostrano performance eccellenti (50K+ IOPS) ma l'applicazione (es. database) riporta query lente.
**Causa**: il problema non è nello storage ma nell'applicazione o nella configurazione. Le cause comuni: (1) fio testa con `direct=1` (bypass cache) mentre l'applicazione usa la page cache del guest, che potrebbe essere insufficiente; (2) l'applicazione usa I/O sincrono single-threaded; (3) il workload reale ha un pattern diverso da quello testato con fio.
**Soluzione**:
```bash
# Dentro la VM, monitorare l'I/O dell'applicazione specifica
pidstat -d 1 -p $(pgrep mysqld)
# Se kB_rd/s e kB_wr/s sono bassi, il database non sta generando abbastanza I/O
# → il bottleneck è la CPU o la configurazione del database

# Profiling I/O del processo
strace -e trace=read,write,fsync -c -p $(pgrep mysqld)
# Se fsync domina, il database attende le sync write
# Soluzione: usare cache=writeback nel disco VM

# Verificare la RAM del guest
free -h
# Se il buffer/cache è basso, aumentare la RAM della VM
```
**Prevenzione**: eseguire benchmark applicativi reali (pgbench per PostgreSQL, sysbench per MySQL) oltre ai benchmark sintetici fio. Non basare le conclusioni solo sui test sintetici.

### Problema: dopo aver abilitato discard/TRIM, le performance peggiorano
**Sintomi**: dopo aver attivato `discard=on` sul disco VM, le write IOPS calano del 20-30%.
**Causa**: il discard continuo (inline TRIM) introduce overhead per ogni operazione di cancellazione nel guest. Ogni `unlink` o truncate nel filesystem guest genera un comando discard che deve attraversare l'intero stack di virtualizzazione. Su alcuni storage backend (specialmente HDD e alcuni SSD consumer), i comandi discard sono costosi.
**Soluzione**:
```bash
# Opzione 1: disabilitare discard inline, usare fstrim periodico
qm set 100 --scsi0 local-lvm:vm-100-disk-0,discard=ignore

# Dentro la VM, configurare fstrim periodico
systemctl enable --now fstrim.timer
# Esegue fstrim una volta a settimana, impatto minimo

# Opzione 2: mantenere discard ma montare con nodiscard nel guest
# e usare fstrim.timer per batch TRIM periodico
# Questo è il compromesso migliore per la maggior parte dei workload
```
**Prevenzione**: testare le performance con e senza discard prima di decidere. Per workload write-intensive, preferire fstrim periodico a discard inline.

### Problema: NVMe consumer mostra latenza alta sotto carico write sostenuto
**Sintomi**: durante write sostenute (backup, migrazione batch), la latenza dell'NVMe sale da < 1 ms a 10-50 ms.
**Causa**: gli NVMe consumer (non datacenter) hanno una cache SLC limitata. Quando il carico write supera la capacità della cache SLC, le write passano a celle TLC/QLC molto più lente. Questo fenomeno è noto come "SLC cache exhaustion" o "write cliff".
**Soluzione**:
```bash
# Monitorare la latenza in tempo reale
iostat -x 1 | grep nvme

# Ridurre il carico write simultaneo
# Limitare le conversioni batch a 1 per volta
# Usare ionice per ridurre la priorità I/O dei processi di migrazione
ionice -c 3 qemu-img convert -p -W -f vmdk -O raw source.vmdk dest.raw
# -c 3: idle I/O class, solo quando il disco non è occupato

# Se il problema è persistente in produzione, l'NVMe non è adatto
# Sostituire con un modello datacenter (Intel DC, Samsung PM/PM983, Micron 7300)
```
**Prevenzione**: utilizzare NVMe di classe datacenter per workload di produzione. Gli NVMe consumer sono accettabili per test e sviluppo ma non per carichi write sostenuti.

### Problema: performance degradate con qcow2 su LVM-thin
**Sintomi**: la VM usa un file qcow2 su LVM-thin e le performance sono significativamente inferiori rispetto a raw su LVM-thin.
**Causa**: il double indirection: qcow2 ha la sua cluster table, e LVM-thin ha il suo mapping layer. Ogni I/O deve attraversare entrambi i layer di traduzione, aumentando la latenza e riducendo gli IOPS. Inoltre, qcow2 su LVM-thin è ridondante poiché entrambi forniscono thin provisioning.
**Soluzione**:
```bash
# Convertire da qcow2 a raw (la VM deve essere spenta)
# 1. Identificare il disco
qm config 100 | grep scsi0
# scsi0: local-lvm:vm-100-disk-0

# 2. Convertire
qemu-img convert -p -W -f qcow2 -O raw \
    /dev/pve/vm-100-disk-0 /dev/pve/vm-100-disk-0-new

# 3. Rinominare (con cautela)
lvrename pve/vm-100-disk-0 vm-100-disk-0-old
lvrename pve/vm-100-disk-0-new vm-100-disk-0

# 4. Aggiornare la configurazione se necessario
# Il formato in Proxmox per LVM-thin è automaticamente raw
```
**Prevenzione**: non utilizzare qcow2 su LVM-thin o ZFS. Il formato raw è la scelta corretta per storage backend che forniscono già thin provisioning e snapshot. Usare qcow2 solo su storage directory (local) o NFS.

---

## Riferimenti

- [Proxmox VE Administration Guide — Performance Tweaks](https://pve.proxmox.com/wiki/Performance_Tweaks)
- [fio Documentation](https://fio.readthedocs.io/en/latest/)
- [fio — Flexible I/O Tester (GitHub)](https://github.com/axboe/fio)
- [VMware esxtop Documentation](https://docs.vmware.com/en/VMware-vSphere/8.0/monitoring-performance/GUID-A31DA2BE-D4DC-4F57-9B46-3CD3A2C35150.html)
- [OpenZFS — Performance Tuning](https://openzfs.github.io/openzfs-docs/Performance%20and%20Tuning/index.html)
- [OpenZFS — ARC](https://openzfs.github.io/openzfs-docs/Performance%20and%20Tuning/Module%20Parameters.html)
- [Ceph Documentation — Performance](https://docs.ceph.com/en/latest/rados/configuration/osd-config-ref/)
- [Ceph Documentation — Placement Groups](https://docs.ceph.com/en/latest/rados/operations/placement-groups/)
- [Linux Block I/O Layer](https://www.kernel.org/doc/html/latest/block/index.html)
- [QEMU Documentation — Disk Images](https://www.qemu.org/docs/master/system/images.html)
- [Linux I/O Schedulers](https://www.kernel.org/doc/html/latest/block/switching-sched.html)
- [Brendan Gregg — Linux Disk I/O Performance](https://www.brendangregg.com/linuxperf.html)
- [Proxmox Wiki — ZFS on Linux](https://pve.proxmox.com/wiki/ZFS_on_Linux)

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — `pveperf` e i suoi limiti.** `pveperf` produce numeri rapidi (CPU, FSYNC, DNS, HD seek) utili per smoke test ma *non* sono benchmark seri. FSYNC test e single-thread su un singolo file, mostra solo l'impatto del log/sync. Per validazione vera, usare fio multi-job. Esempio comando preferibile per OLTP-like:
> ```
> fio --name=oltp-test --filename=/var/lib/vz/test.bin --rw=randrw --rwmixread=70 \
>   --bs=4k --iodepth=32 --numjobs=4 --runtime=300 --time_based --group_reporting \
>   --direct=1 --ioengine=libaio
> ```
> Direct I/O bypassa il cache layer (che falserebbe i numeri).

> **Errore comune — Cache mode `writeback` per un DB senza UPS.** Sintomo: dopo crash dell'host, il DB ha pagine corrotte (Postgres `Innodb: needs recovery`). Causa: `writeback` mette in cache RAM le scritture e le ack al guest *prima* del flush al disco; al crash, le scritture in volo si perdono. Soluzione: `writeback` solo con UPS + ECC RAM + backup application-consistent recente. Per max safety: `writethrough` (lento) o `none` (default).

> **Caso reale — ZFS ARC che mangia la RAM dell'host.** Su un host Proxmox con 256 GB RAM, ZFS ARC e cresciuta a 230 GB lasciando solo 26 GB per VM. Le VM andavano in swap (perdita di performance massiva). Causa: ZFS ARC default e meta della RAM dell'host (cap 50%). Soluzione: limitare ARC con `echo "options zfs zfs_arc_max=$((32*1024*1024*1024))" > /etc/modprobe.d/zfs.conf` (32 GB max), poi `update-initramfs -u` e reboot. Verificare con `arc_summary | grep -i max`. Best practice: 16-32 GB ARC su nodi con 256 GB; oltre, rendimenti decrescenti.

---

## Esercizi

1. **Concettuale — IOPS p50 vs p99.** Spiega perche un sistema con IOPS medi 5000 e p99 latency 100 ms e *peggio* di uno con IOPS medi 3000 e p99 5 ms per un'app web. *Risposta:* l'app deve attendere il disco; con p99 100 ms, l'1% delle richieste richiede 100 ms = utenti vedono lag intermittenti. Con p99 5 ms, l'esperienza utente e consistente. Per database, l'effetto si amplifica: un OLTP con tante query brevi soffre tantissimo di tail latency alta.

2. **Lab — baseline + post + compare.** (a) Su una VM Linux su VMware, eseguire il fio OLTP-like (vedi callout). Salvare output JSON. (b) Migrare la VM a Proxmox. (c) Eseguire stesso fio. Confrontare IOPS p50/p95/p99 e latency p99. Costruire una tabella di confronto. (d) Se delta > -10%, applicare tuning (cache mode, iothread, NUMA) e rieseguire.

3. **Scenario — migrazione DB con perf -25%.** Dopo migrazione, una VM PostgreSQL mostra p99 query latency 25% peggio di pre-migrazione. Argomenta in 12 righe la procedura di troubleshooting: (a) identificare se il problema e CPU, RAM, I/O o rete (USE method); (b) tuning step by step: prima cache mode, poi iothread, poi NUMA; (c) se nessuno aiuta, considerare cambio storage backend (es. da NFS a Ceph RBD per ridurre latency). *Risposta:* iniziare con `iostat -xdz 5` e `pidstat 5` per la VM; se await > 5ms, problema disco; tune cache mode a `writeback` se UPS+ECC presenti; abilitare `iothread=1` se non gia; verificare `qm config <vmid> | grep numa` e abilitare NUMA pinning per VM grandi.

4. **Stretch — automazione benchmark + report.** Scrivere uno script Python che, dato `vmlist.csv` con `vmid,name,profile (oltp|olap|mixed)`, esegue per ogni VM: (1) connessione SSH al guest; (2) lancio fio con profilo corrispondente; (3) raccolta JSON output; (4) inserimento in DB SQLite locale; (5) generazione report HTML con grafici (matplotlib) di confronto pre/post.

## Auto-valutazione

1. Differenza fra cache mode `writeback`, `writethrough`, `none` su VM Proxmox?
2. Cosa fa `iothread=1` su un disco virtio-scsi?
3. Comando fio per simulare workload OLTP DB?
4. ZFS ARC: cosa e e come si limita?
5. Cosa fa `pveperf` e quali sono i suoi limiti?
6. USE method: cosa significa Saturation, Utilization, Errors?
7. NUMA pinning di una VM: comando e quando applicarlo?
8. Quanti PG (Placement Group) per OSD sono raccomandati su Ceph?

## Letture primarie consigliate

- fio documentation. https://fio.readthedocs.io/en/latest/
- [`OPENZFS`] OpenZFS Performance Tuning. https://openzfs.github.io/openzfs-docs/Performance%20and%20Tuning/Workload%20Tuning.html
- [`CEPH-DOCS`] Ceph — BlueStore Performance. https://docs.ceph.com/en/latest/rados/configuration/bluestore-config-ref/
- [`PVE-WIKI`] Proxmox VE Wiki — ZFS on Linux. https://pve.proxmox.com/wiki/ZFS_on_Linux
- [`BRENDAN-USE`] Brendan Gregg — USE Method. https://www.brendangregg.com/usemethod.html
- Linux Kernel — I/O Schedulers. https://www.kernel.org/doc/html/latest/block/switching-sched.html
- [`IOSTAT-MAN`] iostat(1). https://manpages.debian.org/bookworm/sysstat/iostat.1.en.html

## Collegamenti incrociati

- Modulo 03.1, 03.2 — `../03-STORAGE-AVANZATO-PROXMOX/`: backend storage.
- Modulo 05.3 — `../05-ASSESSMENT-E-PIANIFICAZIONE/dimensionamento-proxmox-capacity-planning.md`: capacity planning con baseline.
- Modulo 08.1 — `conversione-vmdk-qcow2-raw.md`: conversione VMDK.
- Modulo 09.3 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-high-io-workloads.md`: workload high-I/O specifici.
- Modulo 13.1 — `../13-MONITORAGGIO-E-OTTIMIZZAZIONE/zabbix-monitoraggio-proxmox.md`: monitoring continuo post-migrazione.
- Modulo 17.4 — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-storage-performance.md`: troubleshooting storage performance.

## Glossario locale

| Termine | Definizione |
|---|---|
| **fio (Flexible I/O Tester)** | Benchmark Linux per simulare workload I/O configurabili. |
| **IOPS** | I/O Operations Per Second — operazioni read/write per secondo. |
| **Throughput** | Dati trasferiti per unita di tempo (MB/s, GB/s). |
| **Latency p50/p95/p99** | Mediana / 95° / 99° percentile della latenza richiesta. |
| **Queue depth** | Numero di I/O outstanding contemporaneamente. |
| **Cache mode QEMU** | `writeback`, `writethrough`, `none` (O_DIRECT), `unsafe`, `directsync`. |
| **iothread** | Thread QEMU dedicato a un disco; permette I/O parallelo per disco. |
| **discard / TRIM** | Comando per liberare blocchi non usati al backend storage. |
| **ZFS ARC** | Adaptive Replacement Cache — cache RAM ZFS per metadata e data. |
| **ZIL / SLOG** | ZFS Intent Log / Separate intent LOG — SSD dedicato per sync writes. |
| **Ceph PG (Placement Group)** | Unita di distribuzione Ceph; target 100 PG/OSD. |
| **BlueStore** | Storage engine Ceph (sostituisce FileStore). |
| **`pveperf`** | Tool Proxmox per benchmark veloce CPU/FSYNC/DNS/HD. |
| **`iostat -xdz 5`** | Comando per vedere disk stats every 5 sec, con avg latency e queue. |
| **USE method** | Metodologia di Brendan Gregg: Utilization, Saturation, Errors per ogni risorsa. |
| **NUMA pinning** | Vincolare una VM a un singolo socket NUMA per latenza memoria prevedibile. |
| **`qm config <vmid> | grep numa`** | Verifica se NUMA e attivo per una VM. |
