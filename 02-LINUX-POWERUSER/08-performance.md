# Performance Linux — Guida Completa

> **Modulo 08** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **USE methodology: Utilization, Saturation, Errors per resource.**
2. **`perf` per CPU profile; `bpftrace` per kernel trace.**
3. **`vmstat`, `iostat`, `mpstat`, `pidstat` toolset.**
4. **Brendan Gregg's flame graphs.**
5. **BPF/eBPF come strumento di osservabilità moderna del kernel.**
6. **Approccio scientifico al benchmarking: baseline → ipotesi → esperimento → misurazione.**
7. **cgroups v2 per isolamento e controllo risorse.**


## Indice

- [Panoramica](#panoramica)
- [Mappa degli Strumenti di Performance Linux](#mappa-degli-strumenti-di-performance-linux)
- [Metodologia di Analisi Performance](#metodologia-di-analisi-performance)
- [CPU: Monitoring e Tuning](#cpu-monitoring-e-tuning)
- [Memoria: Monitoring e Tuning](#memoria-monitoring-e-tuning)
- [Disco I/O: Monitoring e Tuning](#disco-io-monitoring-e-tuning)
- [Rete: Monitoring e Tuning](#rete-monitoring-e-tuning)
- [Strumenti: top, htop, atop, iotop](#strumenti-top-htop-atop-iotop)
- [sar e sysstat](#sar-e-sysstat)
- [Analisi a Livello di Processo](#analisi-a-livello-di-processo)
- [perf Deep Dive](#perf-deep-dive)
- [Flame Graph](#flame-graph)
- [strace e ltrace](#strace-e-ltrace)
- [BPF e bpftrace](#bpf-e-bpftrace)
- [cgroups v2](#cgroups-v2)
- [Benchmark e Stress Test](#benchmark-e-stress-test)
- [Tuning Avanzato del Kernel](#tuning-avanzato-del-kernel)
- [Capacity Planning](#capacity-planning)
- [Workflow di Performance Profiling](#workflow-di-performance-profiling)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Checklist per Workload Specifici](#checklist-per-workload-specifici)
- [FAQ](#faq)

---

## Panoramica

L'analisi delle performance è una disciplina fondamentale per l'amministratore di sistema. Un problema di performance può avere origine dalla CPU, dalla memoria, dal disco, dalla rete, o da una combinazione. La chiave è un approccio metodico: raccogliere dati prima di ipotizzare cause, misurare prima e dopo ogni modifica, e non ottimizzare senza prima identificare il collo di bottiglia.

### Principi Fondamentali

1. **Misurare, non indovinare**: ogni ipotesi deve essere supportata da dati. Le sensazioni ("mi sembra lento") non sono diagnostica.
2. **Conoscere il baseline**: senza sapere com'è il sistema "in salute", non si può determinare cosa è degradato.
3. **Isolare le variabili**: un solo cambiamento alla volta, misurare prima e dopo.
4. **Pensare in risorse**: CPU, memoria, disco, rete — il collo di bottiglia è sempre in una di queste (o nella loro interazione).
5. **Non ottimizzare il sistema sbagliato**: prima capire dove si perde tempo (profiling), poi ottimizzare quel punto.
6. **I numeri assoluti contano poco senza contesto**: 80% CPU su un server web sotto carico è normale; 80% CPU idle è un problema.

### Tassonomia dei Problemi di Performance

| Tipo | Sintomo | Causa tipica |
|------|---------|--------------|
| **Latenza** | Risposta lenta | Lock contention, I/O wait, GC pause |
| **Throughput** | Poche operazioni/sec | CPU bound, I/O bottleneck |
| **Saturazione** | Code lunghe, timeout | Risorsa al limite, backlog |
| **Errori** | Fallimenti sotto carico | OOM, disk full, connection refused |
| **Degradazione graduale** | Peggioramento nel tempo | Memory leak, frammentazione, log growth |
| **Jitter** | Latenza variabile | NUMA, CPU scheduling, interrupt storm |

---

## Mappa degli Strumenti di Performance Linux

Mappa concettuale basata sul lavoro di Brendan Gregg. Ogni risorsa ha strumenti di osservabilità, benchmarking e tuning.

### Osservabilità — per Risorsa

```
╔═══════════╦════════════════════════════════════════════════════════════╗
║ Risorsa   ║ Strumenti di Osservabilità                               ║
╠═══════════╬════════════════════════════════════════════════════════════╣
║ CPU       ║ top, htop, mpstat, pidstat, perf top, perf stat,         ║
║           ║ turbostat, /proc/stat, /proc/loadavg, sar -u             ║
╠═══════════╬════════════════════════════════════════════════════════════╣
║ Memoria   ║ free, vmstat, slabtop, /proc/meminfo, smem, pmap,       ║
║           ║ numastat, /proc/[pid]/smaps, sar -r, sar -S             ║
╠═══════════╬════════════════════════════════════════════════════════════╣
║ Disco     ║ iostat, iotop, blktrace, biosnoop, biolatency,          ║
║           ║ /proc/diskstats, sar -d, smartctl, ioping               ║
╠═══════════╬════════════════════════════════════════════════════════════╣
║ Rete      ║ ss, nstat, sar -n, ip -s, ethtool -S, nethogs, iftop,  ║
║           ║ tcpdump, tcplife, /proc/net/dev, /proc/net/snmp         ║
╠═══════════╬════════════════════════════════════════════════════════════╣
║ Filesystem║ df, du, opensnoop, fileslower, ext4slower,              ║
║           ║ /proc/[pid]/fdinfo, lsof                                ║
╠═══════════╬════════════════════════════════════════════════════════════╣
║ Kernel    ║ dmesg, perf, bpftrace, ftrace, /proc/sched_debug,      ║
║           ║ /proc/softirqs, /proc/interrupts                        ║
╚═══════════╩════════════════════════════════════════════════════════════╝
```

### Benchmarking — per Risorsa

```
CPU         → sysbench cpu, stress-ng --cpu, perf bench
Memoria     → sysbench memory, stress-ng --vm, mbw, stream
Disco       → fio, sysbench fileio, dd (grezzo), ioping
Rete        → iperf3, netperf, qperf, sockperf
Sistema     → phoronix-test-suite, unixbench
```

### Tuning — per Risorsa

```
CPU         → governor, taskset, nice/renice, cgroups, NUMA, IRQ affinity
Memoria     → vm.swappiness, THP, NUMA, overcommit, OOM score
Disco       → scheduler, readahead, mount options, queue depth
Rete        → sysctl net.*, ethtool offload/ring, tc, NIC tuning
Kernel      → sysctl, /sys/kernel/*, boot parameters
```

---

## Metodologia di Analisi Performance

### USE Method (Brendan Gregg)

Per ogni risorsa (CPU, memoria, disco, rete), verificare:
- **U**tilization: quanto è usata la risorsa (%)
- **S**aturation: coda di lavoro in attesa
- **E**rrors: contatori errori

#### USE Method — Tabella Completa per Risorsa

| Risorsa | Utilization | Saturation | Errors |
|---------|-------------|------------|--------|
| **CPU** | `mpstat -P ALL 1` (%usr + %sys) | `vmstat 1` (colonna r > nr_cpus), load avg | `perf stat` (cache miss), `dmesg` (MCE) |
| **Memoria** | `free -h` (used/total), `/proc/meminfo` | `vmstat 1` (si/so > 0 = swap attivo), OOM in dmesg | `dmesg \| grep -i oom`, `edac-util` (ECC) |
| **Disco** | `iostat -xz 1` (%util) | `iostat -xz 1` (avgqu-sz > 1), `iotop` | `smartctl -a` (reallocated sectors), `/sys/block/*/device/errors` |
| **Rete** | `sar -n DEV 1` (rxkB/s vs link speed), `ip -s link` | `nstat \| grep -i drop`, `ss -ti` (retrans), `netstat -s \| grep overflow` | `ethtool -S eth0 \| grep err`, `ip -s link` (errors, drops) |
| **Filesystem** | `df -h` (% uso), `df -i` (inode) | nessun indicatore diretto, monitorare latenza | `dmesg \| grep -i ext4`, errori filesystem |
| **Controller** | `iostat -xz` (totale per controller) | — | `dmesg` (ata, scsi errors) |

### Checklist Rapida (60 secondi)

```bash
uptime                     # Load average (1, 5, 15 min)
dmesg -T | tail            # Errori kernel recenti
vmstat 1 5                 # CPU, memoria, I/O, context switch
mpstat -P ALL 1 3          # CPU per core
pidstat 1 3                # CPU per processo
iostat -xz 1 3             # I/O per disco
free -h                    # Memoria
sar -n DEV 1 3             # Traffico rete
sar -n TCP,ETCP 1 3        # Connessioni TCP
top                        # Vista generale interattiva
```

### Analisi Avanzata — Workflow Esteso

Dopo la checklist da 60 secondi, approfondire l'area identificata:

```bash
# Fase 2: se il problema è CPU
perf top                           # Simboli caldi in tempo reale
perf record -g -a -- sleep 30      # Registra profilo di sistema
perf report                        # Analizza call graph

# Fase 2: se il problema è memoria
cat /proc/meminfo | grep -E 'MemTotal|MemAvailable|Buffers|Cached|SwapTotal|SwapFree|Slab|SReclaimable'
slabtop -o | head -20              # Top slab allocator
smem -t -k                         # PSS per processo

# Fase 2: se il problema è disco
sudo iotop -oPa                    # I/O cumulativo per processo
sudo biolatency                    # Distribuzione latenza I/O (BPF)
ioping -c 10 /dev/sda              # Latenza puntuale

# Fase 2: se il problema è rete
ss -ti dst <ip>                    # Dettaglio connessione TCP
nstat -z                           # Contatori TCP/IP azzerati
sudo tcpdump -i eth0 -c 100 -nn   # Cattura traffico
```

### Load Average

```bash
uptime
# 10:30:00 up 45 days, load average: 2.50, 3.10, 2.80

# Load average = media dei processi in stato R (running) + D (uninterruptible sleep)
# Interpretazione su un server con 4 CPU:
#   load < 4.0  → sistema non saturo
#   load = 4.0  → tutti i core al 100%
#   load > 4.0  → coda di processi in attesa

# Se load alto ma CPU bassa → I/O wait (processi in stato D)
# Se load alto e CPU alta → CPU bound

# Trend: confrontare 1min, 5min, 15min
# 1min > 15min → carico in aumento
# 1min < 15min → carico in diminuzione
# Tutti simili → carico stabile

# Normalizzare per numero di core:
# load_per_core = load_average / nproc
# Se load_per_core > 1.0 → saturazione

nproc  # Numero core logici
# load_avg / nproc = carico normalizzato
```

### RED Method (per servizi)

Il metodo RED (complementare a USE) è orientato ai servizi:

- **R**ate: richieste al secondo (throughput)
- **E**rrors: percentuale di richieste fallite
- **D**uration: distribuzione della latenza (p50, p95, p99)

```bash
# Esempio: monitorare un web server
# Rate
ss -s | grep estab          # Connessioni attive
journalctl -u nginx --since "5 min ago" | wc -l   # Richieste recenti

# Errors
grep -c " 5[0-9][0-9] " /var/log/nginx/access.log   # Errori 5xx

# Duration
awk '{print $NF}' /var/log/nginx/access.log | sort -n | \
  awk '{a[NR]=$1} END {print "p50="a[int(NR*0.5)], "p95="a[int(NR*0.95)], "p99="a[int(NR*0.99)]}'
```

---

## CPU: Monitoring e Tuning

### Monitoring CPU

```bash
# MONITORING
mpstat -P ALL 1             # Utilizzo per core (1 sec interval)
# %usr: user space     %sys: kernel     %iowait: attesa I/O
# %irq: hardware IRQ   %soft: software IRQ   %idle: libero

# CPU per processo
pidstat -u 1                # CPU per processo
pidstat -t -u 1             # CPU per thread

# Contare i core
nproc                       # Core logici
lscpu                       # Dettaglio completo
cat /proc/cpuinfo | grep -c "processor"  # Core logici (alternativo)

# Frequenza CPU
cat /proc/cpuinfo | grep "MHz"
watch -n1 "cat /proc/cpuinfo | grep MHz"  # Monitorare frequenza in tempo reale
turbostat --Summary --quiet --interval 1   # Intel: frequenza, C-state, potenza
```

### USE Method Applicata alla CPU

```bash
# UTILIZATION
mpstat -P ALL 1 3
# Guardare %usr + %sys per core
# Se un core è al 100% e gli altri idle → processo single-threaded
# Se tutti i core al 100% → CPU bound reale

# SATURATION
vmstat 1 5
# Colonna 'r' (run queue) > numero di core = CPU saturata
# Colonna 'b' (blocked) > 0 = processi bloccati su I/O

# Verificare con /proc/stat
cat /proc/stat | head -1
# cpu  user nice system idle iowait irq softirq steal guest guest_nice
# Calcolo: %busy = 100 - %idle

# ERRORS
# Errori CPU: Machine Check Exception (MCE)
dmesg | grep -i "mce\|machine check"
# Hardware correctable/uncorrectable errors
sudo mcelog --client         # Se mcelog è installato
# sudo edac-util -s          # ECC memory errors via EDAC
```

### Analisi Dettagliata con top

```bash
# Shortcut avanzati di top per analisi CPU
top -H                      # Mostra thread individuali
top -p PID1,PID2            # Solo processi specifici
top -bn1 -o %CPU | head -15 # Output batch ordinato per CPU

# In top interattivo:
# 1   → mostra singoli core (fondamentale per trovare imbalance)
# H   → mostra thread (per capire se un processo è multi-thread)
# f   → seleziona colonne (aggiungere nTH per num thread)
# x   → evidenzia colonna di ordinamento
# d   → cambia intervallo di refresh (default 3s → mettere 1s)
```

### Analisi CPU con perf top

```bash
# perf top: mostra in tempo reale i simboli (funzioni) che consumano più CPU
sudo perf top
# Colonne:
# Overhead  Shared Object      Symbol
# 15.20%    [kernel]            native_write_msr
#  8.50%    libc.so.6          __memmove_avx
#  3.20%    myapp              hotFunction

# Solo user space (escludere kernel)
sudo perf top --no-children -U

# Solo un processo
sudo perf top -p PID

# Con call graph (per capire chi chiama la funzione calda)
sudo perf top -g
```

### Analisi CPU con perf stat

```bash
# Statistiche hardware counters
sudo perf stat ./myapp
# Output:
#  1.523.456.789  cycles
#    892.345.678  instructions   # IPC = instructions / cycles
#     45.678.901  cache-misses   # Cache miss ratio
#        123.456  page-faults
#          1.234  context-switches

# IPC (Instructions Per Cycle): indicatore di efficienza
# IPC < 1.0 → probabilmente memory stalled (cache miss, TLB miss)
# IPC > 1.0 → buona efficienza
# IPC > 2.0 → ottimo (il processore sfrutta il pipeline)

# Contatori specifici
sudo perf stat -e cycles,instructions,cache-misses,cache-references,\
L1-dcache-load-misses,LLC-load-misses,branches,branch-misses \
./myapp

# Interpretazione cache miss:
# L1 miss → il dato non è nella cache più veloce (tipico)
# LLC (Last Level Cache) miss → il dato va preso dalla RAM (costoso)
# branch-misses → predizione rami sbagliata (codice con molti if unpredictable)

# Per un processo in esecuzione
sudo perf stat -p PID -- sleep 10
```

### TUNING CPU

```bash
# Governator CPU (per laptop/desktop)
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# performance, powersave, ondemand, schedutil
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Verificare che sia applicato
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Governor schedutil: il default su kernel recenti
# Si basa su segnali dello scheduler per decidere la frequenza
# Buon compromesso tra performance e consumo

# Process affinity (legare processo a specifici core)
taskset -c 0-3 ./myapp              # Esegui su core 0-3
taskset -pc 0-3 1234                # Cambia affinity del PID 1234
taskset -p 1234                     # Mostra affinity attuale

# Priorità
nice -n -10 ./myapp                 # Priorità alta (range: -20 a 19)
sudo renice -10 -p 1234            # Cambia priorità a processo esistente

# Real-time scheduling (per latenza minima)
sudo chrt -f 50 ./myapp            # SCHED_FIFO, priorità 50
sudo chrt -r 50 ./myapp            # SCHED_RR, priorità 50
chrt -p PID                        # Mostra policy attuale

# IRQ balancing
sudo systemctl status irqbalance   # Distribuzione interrupt tra core
cat /proc/interrupts               # Interrupt per core

# IRQ affinity manuale (per NIC ad alte prestazioni)
# Disabilitare irqbalance e assegnare IRQ a core specifici
echo 2 | sudo tee /proc/irq/IRQ_NUM/smp_affinity  # Core 1

# NUMA (Non-Uniform Memory Access)
numactl --hardware                 # Topologia NUMA
numactl --cpunodebind=0 --membind=0 ./myapp  # Bind a nodo NUMA 0
numastat                           # Statistiche allocazione NUMA
numastat -p PID                    # NUMA stats per processo
```

### Context Switch e Scheduling

```bash
# Context switch: ogni switch ha un costo (flush cache, TLB)
vmstat 1
# Colonna 'cs' = context switches al secondo
# Migliaia/sec → normale per server occupato
# Centinaia di migliaia/sec → potrebbe indicare lock contention

# Context switch per processo
pidstat -w 1
# cswch/s: voluntary context switches (I/O wait, sleep, mutex)
# nvcswch/s: non-voluntary (preemption, time slice esaurito)
# nvcswch alto → processi CPU-bound competono per core

# Dettaglio scheduling
cat /proc/PID/sched              # Statistiche scheduler per processo
cat /proc/PID/status | grep -E "voluntary|nonvoluntary"

# Scheduler latenza
cat /proc/sys/kernel/sched_latency_ns           # Target latenza (default 6ms)
cat /proc/sys/kernel/sched_min_granularity_ns   # Min time slice (default 0.75ms)

# Per workload latency-sensitive
echo 1000000 | sudo tee /proc/sys/kernel/sched_latency_ns
echo 100000 | sudo tee /proc/sys/kernel/sched_min_granularity_ns
```

---

## Memoria: Monitoring e Tuning

### Monitoring Memoria

```bash
# MONITORING
free -h                     # Vista generale
# total: RAM totale
# used: RAM usata
# free: RAM libera (non usata dal kernel)
# buff/cache: buffer + page cache (riciclabile)
# available: RAM effettivamente disponibile (free + riciclabile)

vmstat 1 5                  # Memoria + swap + I/O
# si/so: swap in/out (se > 0 costantemente → problema)

# Dettaglio
cat /proc/meminfo           # Tutte le metriche memoria
slabtop                     # Cache kernel (slab allocator)

# Per processo
ps aux --sort=-%mem | head -20              # Top 20 per memoria
pmap -x PID                                 # Mappa memoria di un processo
cat /proc/PID/status | grep -i vm           # VmRSS, VmSize, etc.
smem -t -k                                  # Memoria per processo (PSS)
```

### USE Method Applicata alla Memoria

```bash
# UTILIZATION
free -h
# Guardare "available" (non "free")
# available = free + reclaimable (buffer/cache)
# Se available < 10% del totale → memoria sotto pressione

cat /proc/meminfo | grep -E 'MemTotal|MemAvailable'
# MemAvailable / MemTotal = % memoria disponibile

# SATURATION
vmstat 1
# si (swap in) e so (swap out) > 0 = il sistema sta usando swap attivamente
# Se si/so sono costantemente > 0 → memoria saturata

# Page scan rate
sar -B 1 5
# pgscank/s (kswapd scans), pgscand/s (direct reclaim scans)
# pgscand > 0 → direct reclaim attivo = il sistema è in stress memoria

# Pressure Stall Information (PSI) — kernel 4.20+
cat /proc/pressure/memory
# some avg10=0.00 avg60=0.00 avg300=0.00 total=0
# full avg10=0.00 avg60=0.00 avg300=0.00 total=0
# some > 0 → qualche task sta aspettando memoria
# full > 0 → tutti i task stanno aspettando → grave

# ERRORS
dmesg | grep -i "oom\|out of memory"
# OOM killer attivato = memoria esaurita
# Il kernel uccide il processo con oom_score più alto

dmesg | grep -i "edac\|ecc\|memory error"
# Errori hardware sulla RAM (ECC)
```

### /proc/meminfo — Guida ai Campi

```bash
cat /proc/meminfo
# Campi critici:
# MemTotal:       totale RAM fisica
# MemFree:        RAM non usata (non include buffer/cache riciclabili)
# MemAvailable:   stima RAM disponibile (include riciclabile)
# Buffers:        cache per metadata filesystem (inode, directory)
# Cached:         page cache (contenuti file)
# SwapTotal:      dimensione swap configurata
# SwapFree:       swap non usata
# SwapCached:     pagine swap che sono anche in RAM (ottimizzazione)
# Active:         pagine usate di recente (difficili da reclamare)
# Inactive:       pagine non usate di recente (candidate per reclaim)
# Dirty:          pagine modificate non ancora scritte su disco
# Writeback:      pagine in fase di scrittura su disco
# Slab:           cache strutture dati del kernel
# SReclaimable:   slab riciclabile (es. dentry cache, inode cache)
# SUnreclaim:     slab non riciclabile
# Shmem:          shared memory (tmpfs, shm)
# Mapped:         pagine mappate in address space di processi
# CommitLimit:    totale memoria committable (RAM + swap)
# Committed_AS:   memoria richiesta (committed) da tutti i processi
# HugePages_Total: huge pages allocate
# HugePages_Free:  huge pages libere
```

### smem — Analisi Memoria Avanzata

```bash
# smem distingue tra RSS, PSS, USS
sudo apt install smem

smem -t -k                  # Tutti i processi con PSS
# USS (Unique Set Size):    memoria usata solo da questo processo
# PSS (Proportional Set Size): memoria proporzionale (shared divisa equamente)
# RSS (Resident Set Size):  memoria residente (include shared contata per intero)
# PSS è la metrica più utile per capire il consumo reale

smem -t -k -s pss           # Ordinato per PSS
smem -t -k -P nginx         # Solo processi nginx
smem -u -t -k               # Raggruppato per utente

# Confronto RSS vs PSS:
# 10 processi nginx condividono 50MB di librerie
# RSS di ogni processo include quei 50MB (sembra che usino 50MB ciascuno)
# PSS divide equamente: 50MB/10 = 5MB ciascuno (più realistico)
```

### pmap — Mappa Memoria di un Processo

```bash
pmap PID                    # Mappa base
pmap -x PID                 # Mappa estesa (RSS, Dirty per mapping)
pmap -XX PID                # Tutti i dettagli disponibili

# Interpretazione:
# [heap]:     allocazione dinamica (malloc)
# [stack]:    stack del thread
# [anon]:     mapping anonimi (mmap senza file)
# libc.so:   libreria condivisa mappata
# Dirty > 0 sulla heap = dati modificati in RAM

# Trovare il mapping più grande
pmap -x PID | sort -k3 -n -r | head -20
```

### Analisi Memory Leak con valgrind

```bash
sudo apt install valgrind

# Memcheck: trova memory leak, use-after-free, buffer overflow
valgrind --leak-check=full --show-leak-kinds=all \
  --track-origins=yes ./myapp

# Output:
# LEAK SUMMARY:
#   definitely lost: 1,234 bytes in 10 blocks    ← LEAK CONFERMATO
#   indirectly lost: 5,678 bytes in 5 blocks      ← RAGGIUNGIBILE solo da blocchi persi
#   possibly lost: 200 bytes in 2 blocks           ← POTENZIALE LEAK
#   still reachable: 50,000 bytes in 100 blocks    ← Non leak, ma non freed

# Massif: profilo allocazione memoria nel tempo
valgrind --tool=massif ./myapp
ms_print massif.out.PID

# Callgrind: profilo CPU (call graph)
valgrind --tool=callgrind ./myapp
callgrind_annotate callgrind.out.PID
# Visualizzare con KCachegrind: kcachegrind callgrind.out.PID
```

### TUNING Memoria

```bash
# TUNING
# Swap
sudo sysctl vm.swappiness=10               # Meno swap (default 60)
# vm.swappiness controlla il bilanciamento tra swappare pagine anonime
# e reclamare page cache. Range 0-200 (kernel 5.8+), 0 = swap solo per evitare OOM
# Valori consigliati:
# Database: 1-10 (minimizzare swap)
# Server generico: 10-30
# Desktop: 60 (default)

# vm.overcommit_memory
sudo sysctl vm.overcommit_memory
# 0 = heuristic overcommit (default): kernel stima se c'è abbastanza memoria
# 1 = always overcommit: malloc non fallisce mai (pericoloso, OOM killer decide dopo)
# 2 = no overcommit: malloc fallisce se commit > CommitLimit
# Per database: 0 o 2 (mai 1)

# vm.overcommit_ratio (usato solo con overcommit_memory=2)
# CommitLimit = (RAM * overcommit_ratio / 100) + Swap
sudo sysctl vm.overcommit_ratio=80

# Drop caches (per diagnostica, NON come fix)
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
# 1=pagecache, 2=dentries+inodes, 3=tutto

# Transparent Huge Pages (THP)
cat /sys/kernel/mm/transparent_hugepage/enabled
# Per database: spesso conviene disabilitare
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
# THP può causare latency spike dovuti a compaction/splitting

# Huge Pages statiche (per database grandi)
# Calcolo: shared_buffers_MB / 2 = numero huge pages
echo 1024 | sudo tee /proc/sys/vm/nr_hugepages
grep Huge /proc/meminfo  # Verificare allocazione

# OOM score (priorità di kill)
cat /proc/PID/oom_score              # Score attuale (0-1000)
echo -1000 | sudo tee /proc/PID/oom_score_adj  # Proteggi dal OOM killer
echo 1000 | sudo tee /proc/PID/oom_score_adj   # Primo a essere killato

# vm.min_free_kbytes: memoria minima libera
sudo sysctl vm.min_free_kbytes
# Default calcolato dal kernel. Aumentare su server con alto I/O
# per evitare che il kernel entri in direct reclaim sotto pressione
sudo sysctl -w vm.min_free_kbytes=131072  # 128MB riservati

# NUMA tuning
# Verificare se i processi allocano memoria nel nodo NUMA locale
numastat -p PID
# numa_miss alto → memoria allocata nel nodo sbagliato
# Soluzione: numactl --membind o numactl --preferred
```

### vm.dirty_* — Tuning Writeback

```bash
# Controlla quanto il kernel bufferizza le scritture prima di flush su disco

# vm.dirty_ratio: % di RAM dopo cui un processo in scrittura
# viene bloccato e forzato a fare flush (default 20)
sudo sysctl vm.dirty_ratio=15

# vm.dirty_background_ratio: % di RAM dopo cui il kernel
# inizia il writeback in background (default 10)
sudo sysctl vm.dirty_background_ratio=5

# vm.dirty_expire_centisecs: dopo quanti centesimi di secondo
# le pagine dirty vengono considerate "vecchie" e flushate (default 3000 = 30s)
sudo sysctl vm.dirty_expire_centisecs=1500  # 15 secondi

# vm.dirty_writeback_centisecs: ogni quanti centesimi di secondo
# il thread di writeback si sveglia (default 500 = 5s)
sudo sysctl vm.dirty_writeback_centisecs=500

# Monitorare pagine dirty
grep -E "Dirty|Writeback" /proc/meminfo
# Dirty alto → molte pagine in attesa di flush
# Writeback alto → flush in corso

# Per database (minimizzare perdita dati in caso di crash):
# vm.dirty_ratio=5
# vm.dirty_background_ratio=2
# vm.dirty_expire_centisecs=500

# Per throughput di scrittura (batch jobs):
# vm.dirty_ratio=40
# vm.dirty_background_ratio=20
# vm.dirty_expire_centisecs=6000
```

---

## Disco I/O: Monitoring e Tuning

### Monitoring Disco I/O

```bash
# MONITORING
iostat -xz 1 3              # I/O per dispositivo
# r/s, w/s:      letture/scritture al secondo
# rkB/s, wkB/s:  KB letti/scritti al secondo
# await:         latenza media (ms) — se alta = disco saturo
# r_await/w_await: latenza separata per lettura e scrittura
# %util:         utilizzo — se ~100% = disco saturo
# avgqu-sz:      profondità media coda (queue depth)
# avgrq-sz:      dimensione media richiesta (settori)

# Per processo
sudo iotop                  # Top per I/O (richiede: apt install iotop)
sudo iotop -o               # Solo processi con I/O attivo
pidstat -d 1                # I/O per processo

# Latenza disco
sudo biolatency             # BPF-based (se disponibile)
ioping /dev/sda             # Latenza singola richiesta I/O
ioping -c 10 -s 4k /dev/sda # 10 richieste da 4K

# /proc/diskstats — statistiche raw
cat /proc/diskstats
# Campo 4: letture completate
# Campo 7: tempo lettura (ms)
# Campo 8: scritture completate
# Campo 11: tempo scrittura (ms)
# Campo 13: tempo I/O totale (ms)
```

### USE Method Applicata al Disco

```bash
# UTILIZATION
iostat -xz 1
# %util: percentuale di tempo con almeno una richiesta in corso
# ATTENZIONE: su dischi con coda parallela (SSD/NVMe), %util può essere
# fuorviante — un SSD può servire molte richieste in parallelo,
# quindi %util=100% non significa necessariamente saturazione

# SATURATION
iostat -xz 1
# avgqu-sz (average queue size): richieste in coda
# Per HDD: avgqu-sz > 1 = saturazione
# Per SSD: avgqu-sz > queue_depth del dispositivo = saturazione
# await alto con %util alto → coda piena → saturazione

# ERRORS
dmesg | grep -iE "i/o error|ata|scsi|blk"
smartctl -a /dev/sda | grep -E "Reallocated|Pending|Uncorrectable"
# Reallocated_Sector_Ct > 0 → settori riallocati (disco in degrado)
# Current_Pending_Sector > 0 → settori in attesa di riallocazione
```

### blktrace — Trace I/O a Livello Block

```bash
# blktrace traccia ogni richiesta I/O a livello block device
sudo apt install blktrace

# Cattura trace (genera file in directory corrente)
sudo blktrace -d /dev/sda -o trace -w 30   # 30 secondi

# Analisi con blkparse
blkparse -i trace -o trace_parsed.txt

# Statistiche aggregate
sudo btt -i trace.blktrace.0

# Output btt:
# Q2Q (queue to queue): tempo tra richieste successive
# Q2C (queue to complete): latenza totale dalla richiesta al completamento
# D2C (dispatch to complete): tempo effettivo del device
# Q2D (queue to dispatch): tempo in coda

# Visualizzazione con iowatcher
sudo iowatcher -t trace.blktrace.0 -o trace.svg
```

### TUNING Disco I/O

```bash
# Scheduler I/O
cat /sys/block/sda/queue/scheduler
# mq-deadline: buono per HDD — ordina le richieste per minimizzare seek
# none/noop: buono per SSD/NVMe — nessun riordinamento (il device è già veloce)
# bfq: buono per desktop — Budget Fair Queueing, equità tra processi
# kyber: per SSD — latency target based
echo mq-deadline | sudo tee /sys/block/sda/queue/scheduler

# Read-ahead
cat /sys/block/sda/queue/read_ahead_kb
echo 256 | sudo tee /sys/block/sda/queue/read_ahead_kb   # Per lettura sequenziale
# Read-ahead grande (256-2048) → buono per lettura sequenziale (video, backup)
# Read-ahead piccolo (8-32) → buono per random I/O (database)

# Queue depth (nr_requests)
cat /sys/block/sda/queue/nr_requests
echo 256 | sudo tee /sys/block/sda/queue/nr_requests
# Più richieste in coda → più throughput (ma potenzialmente più latenza)

# Mount options per performance
# noatime: non aggiornare access time (RACCOMANDATO per quasi tutti i workload)
# relatime: aggiorna atime solo se mtime > atime (default Linux moderno)
# nobarrier: disabilita write barrier (pericoloso senza BBU/cache con batteria)
# data=writeback: ext4, più veloce ma meno sicuro (risk di metadata inconsistency)
# data=journal: ext4, più lento ma dati e metadata nel journal (massima sicurezza)
# discard: SSD TRIM in linea (alternativa: fstrim periodico)
# commit=60: ext4, intervallo commit journal (default 5s, aumentare per throughput)

# Esempio fstab con tuning
# /dev/sda1 / ext4 defaults,noatime,commit=30 0 1
# /dev/nvme0n1p1 /data xfs defaults,noatime,logbufs=8 0 2

# SMART (salute disco)
sudo smartctl -a /dev/sda           # Tutti i dati SMART
sudo smartctl -H /dev/sda           # Health check rapido
sudo smartctl -t short /dev/sda     # Test rapido (~2 minuti)
sudo smartctl -t long /dev/sda      # Test completo (~ore)

# SSD: verificare TRIM
sudo fstrim -v /                    # TRIM manuale
# Periodic TRIM è preferibile a mount con discard
sudo systemctl enable --now fstrim.timer  # TRIM settimanale
```

### fio — Benchmark Disco Avanzato

```bash
sudo apt install fio

# Throughput sequenziale (lettura)
fio --name=seq-read --rw=read --bs=1M --size=1G \
  --numjobs=1 --runtime=30 --time_based --group_reporting

# Throughput sequenziale (scrittura)
fio --name=seq-write --rw=write --bs=1M --size=1G \
  --numjobs=1 --runtime=30 --time_based --group_reporting

# IOPS random (4K, tipico database)
fio --name=rand-read-4k --rw=randread --bs=4k --size=1G \
  --numjobs=4 --iodepth=32 --runtime=30 --time_based --group_reporting

# IOPS random write
fio --name=rand-write-4k --rw=randwrite --bs=4k --size=1G \
  --numjobs=4 --iodepth=32 --runtime=30 --time_based --group_reporting

# Mixed (come database reale: 70% read, 30% write)
fio --name=mixed --rw=randrw --rwmixread=70 --bs=4k --size=1G \
  --numjobs=4 --iodepth=32 --runtime=30 --time_based --group_reporting

# Latency test (un singolo I/O alla volta)
fio --name=latency --rw=randread --bs=4k --size=256M \
  --numjobs=1 --iodepth=1 --runtime=30 --time_based \
  --lat_percentiles=1 --group_reporting

# Interpretazione output fio:
# bw: bandwidth (throughput) in KB/s o MB/s
# iops: operazioni I/O al secondo
# lat (usec/msec): latenza
#   avg: media
#   clat percentiles: p50, p95, p99
# slat: submission latency (tempo per sottomettere la richiesta)
# clat: completion latency (tempo dal submit al complete)
# lat: total latency = slat + clat

# Profilo predefinito per simulare workload specifici
fio --name=oltp --filename=/dev/sda --direct=1 --rw=randrw \
  --rwmixread=70 --bs=8k --iodepth=64 --numjobs=8 \
  --runtime=60 --time_based --group_reporting
```

---

## Rete: Monitoring e Tuning

### Monitoring Rete

```bash
# MONITORING
sar -n DEV 1 3              # Traffico per interfaccia
ss -s                       # Statistiche socket
ss -tuln                    # Porte in ascolto
nstat                       # Statistiche protocollo
cat /proc/net/dev           # Statistiche raw

# Per processo
ss -tunap                   # Connessioni con PID
nethogs                     # Bandwidth per processo (apt install nethogs)
iftop -i eth0               # Bandwidth per connessione
```

### USE Method Applicata alla Rete

```bash
# UTILIZATION
ip -s link show eth0
# RX bytes, TX bytes → confrontare con capacità link
ethtool eth0 | grep Speed   # Velocità link (es. 1000Mb/s)
# Calcolo: (RX+TX bytes/sec * 8) / link_speed_bps = % utilization

sar -n DEV 1 5
# rxkB/s, txkB/s → confrontare con link speed
# 1Gbps = ~125 MB/s = 125000 KB/s max teorico

# SATURATION
nstat | grep -i drop
# TcpExtListenDrops: connessioni droppate sulla listen queue
# TcpExtListenOverflows: listen queue overflow
# IpInDiscards, IpOutDiscards: pacchetti scartati

ss -ltn
# Recv-Q > 0 sulla listen socket = connessioni in attesa di accept()
# Se Recv-Q si avvicina al backlog → saturazione

# Drop sul NIC
ip -s link show eth0 | grep -A1 "RX\|TX"
# dropped > 0 → il kernel o il NIC non riesce a tenere il passo
ethtool -S eth0 | grep -i "drop\|miss\|err"

# Buffer overrun
cat /proc/net/softnet_stat
# Colonna 2 (dropped): pacchetti persi per backlog pieno
# Colonna 3 (time_squeeze): CPU non ha avuto tempo di processare

# ERRORS
ethtool -S eth0 | grep -iE "err|crc|collision|timeout"
ip -s link show eth0     # errors, dropped, overruns, carrier
# errors > 0 → problemi hardware (cavo, SFP, NIC)
# carrier > 0 → link flap
```

### ss — Analisi Dettagliata Socket

```bash
# Socket TCP attivi con dettagli
ss -ti
# Mostra per ogni connessione:
# rto: retransmission timeout
# rtt: round-trip time (latenza)
# cwnd: congestion window
# retrans: ritrasmissioni
# bytes_acked, bytes_received
# delivery_rate: throughput effettivo

# Socket in stato TIME_WAIT (dopo chiusura connessione)
ss -tan state time-wait | wc -l
# Troppi TIME_WAIT → configurare tcp_tw_reuse

# Socket in stato ESTABLISHED con slow start
ss -ti state established | grep -c "cwnd:[0-9] "
# cwnd piccolo = connessione appena partita o dopo congestione

# Connessioni per stato
ss -tan | awk '{print $1}' | sort | uniq -c | sort -rn
# Distribuzione: ESTAB, TIME-WAIT, CLOSE-WAIT, SYN-SENT

# CLOSE-WAIT alto → il server non chiude connessioni (bug applicativo)
# SYN-SENT alto → timeout verso server remoti
# FIN-WAIT-2 alto → peer non chiude (half-closed)
```

### nstat — Contatori Protocollo

```bash
nstat -z    # Mostra tutti i contatori (anche quelli a zero)
nstat -s    # Formato esteso con descrizione

# Contatori importanti:
# TcpRetransSegs          — ritrasmissioni TCP (rete lossy)
# TcpExtTCPLostRetransmit — segmenti persi e ritrasmessi
# TcpExtListenDrops       — connessioni droppate sulla listen queue
# TcpExtListenOverflows   — overflow della listen queue
# TcpExtTCPAbortOnTimeout — connessioni abortite per timeout
# TcpExtTCPAbortOnMemory  — connessioni abortite per mancanza memoria
# IpInDiscards            — pacchetti IP scartati
# UdpInErrors             — errori UDP

# Monitorare in tempo reale (delta ogni 2 secondi)
nstat -n 2
```

### iperf3 — Benchmark Rete

```bash
# iperf3 per misurare throughput e latenza di rete

# Server
iperf3 -s                           # Avvia server (porta 5201)

# Client — test throughput
iperf3 -c server_ip -t 30           # Test 30 secondi
iperf3 -c server_ip -R              # Reverse (download dal server)
iperf3 -c server_ip -P 4            # 4 stream paralleli

# Client — test UDP (per misurare jitter e packet loss)
iperf3 -c server_ip -u -b 100M     # UDP 100Mbps
iperf3 -c server_ip -u -b 1G       # UDP 1Gbps

# Client — test con dimensione specifica
iperf3 -c server_ip -l 8192        # 8K block size (default)
iperf3 -c server_ip -M 1460        # MSS specifico

# Interpretazione output:
# Interval  Transfer  Bitrate
# 0-1 sec   112 MB    940 Mbits/sec
# Jitter (UDP): variazione della latenza
# Lost/Total: pacchetti persi / totali
```

### tc — Traffic Control e Traffic Shaping

```bash
# tc permette di controllare il traffico in uscita

# Visualizzare configurazione attuale
tc qdisc show dev eth0
tc class show dev eth0
tc filter show dev eth0

# Aggiungere latenza (simulare rete lenta per test)
sudo tc qdisc add dev eth0 root netem delay 100ms
# Latenza 100ms con variazione 20ms (distribuzione normale)
sudo tc qdisc add dev eth0 root netem delay 100ms 20ms distribution normal

# Simulare packet loss
sudo tc qdisc add dev eth0 root netem loss 1%

# Rate limiting (limitare banda)
sudo tc qdisc add dev eth0 root tbf rate 10mbit burst 32kbit latency 400ms

# Rimuovere tutte le regole
sudo tc qdisc del dev eth0 root

# HTB (Hierarchical Token Bucket) per traffic shaping avanzato
sudo tc qdisc add dev eth0 root handle 1: htb default 30
sudo tc class add dev eth0 parent 1: classid 1:1 htb rate 100mbit ceil 100mbit
sudo tc class add dev eth0 parent 1:1 classid 1:10 htb rate 80mbit ceil 100mbit
sudo tc class add dev eth0 parent 1:1 classid 1:30 htb rate 20mbit ceil 50mbit
# Classe 1:10 → 80Mbps garantiti, burst fino a 100Mbps
# Classe 1:30 → 20Mbps garantiti, burst fino a 50Mbps
```

### TUNING Rete

```bash
# Buffer di rete
sudo sysctl -w net.core.rmem_max=16777216
sudo sysctl -w net.core.wmem_max=16777216
sudo sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"
sudo sysctl -w net.ipv4.tcp_wmem="4096 87380 16777216"
# tcp_rmem/tcp_wmem: min default max (bytes)
# min: minimo per socket (4KB)
# default: dimensione iniziale (87KB → 131072 per reti veloci)
# max: massimo per socket (16MB per reti 10Gbps+)

# TCP window scaling
sudo sysctl -w net.ipv4.tcp_window_scaling=1
# Necessario per finestre > 64KB (reti ad alta banda)

# TCP congestion control
sysctl net.ipv4.tcp_congestion_control
# reno: classico, conservativo
# cubic: default Linux, buono per reti moderne
# bbr: Google BBR, ottimo per reti con packet loss
sudo sysctl -w net.ipv4.tcp_congestion_control=bbr
# BBR richiede: modprobe tcp_bbr
sudo modprobe tcp_bbr

# Backlog
sudo sysctl -w net.core.somaxconn=65535
sudo sysctl -w net.core.netdev_max_backlog=5000
# somaxconn: lunghezza massima listen queue (importante per server web)
# netdev_max_backlog: coda pacchetti in ingresso per CPU

# TCP keepalive
sudo sysctl -w net.ipv4.tcp_keepalive_time=300    # Primo probe dopo 300s (default 7200)
sudo sysctl -w net.ipv4.tcp_keepalive_intvl=30    # Intervallo tra probe (default 75)
sudo sysctl -w net.ipv4.tcp_keepalive_probes=5    # Tentativi (default 9)

# TCP TIME_WAIT
sudo sysctl -w net.ipv4.tcp_tw_reuse=1     # Riusa TIME_WAIT per nuove connessioni in uscita
# tcp_tw_recycle: RIMOSSO dal kernel 4.12 (causava problemi con NAT)

# SYN flood protection
sudo sysctl -w net.ipv4.tcp_syncookies=1    # Protezione SYN flood (default: 1)
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=4096  # SYN backlog

# conntrack (firewall stateful)
sudo sysctl -w net.netfilter.nf_conntrack_max=1000000
# Se server con molte connessioni, il default (65536) può essere basso
# Monitorare: cat /proc/sys/net/netfilter/nf_conntrack_count

# Offload (hardware NIC)
ethtool -k eth0                    # Lista offload attivi
sudo ethtool -K eth0 tso on       # TCP segmentation offload
sudo ethtool -K eth0 gro on       # Generic receive offload
sudo ethtool -K eth0 gso on       # Generic segmentation offload

# Ring buffer NIC
ethtool -g eth0                    # Buffer attuali
sudo ethtool -G eth0 rx 4096      # Aumenta buffer RX
sudo ethtool -G eth0 tx 4096      # Aumenta buffer TX

# RSS (Receive Side Scaling) — distribuzione RX su più code/CPU
ethtool -l eth0                    # Numero code supportate
sudo ethtool -L eth0 combined 8   # Attiva 8 code
```

---

## Strumenti: top, htop, atop, iotop

### top

```bash
top
# Comandi interattivi:
# 1     = mostra singoli core
# P     = ordina per CPU
# M     = ordina per memoria
# T     = ordina per tempo CPU
# c     = mostra comando completo
# k     = kill un processo
# r     = renice un processo
# H     = mostra thread
# f     = seleziona campi da mostrare
# W     = salva configurazione
# q     = esci

# Batch mode (per script)
top -bn1 | head -20                # Una iterazione, output testo

# Header top — interpretazione:
# us: user CPU (applicazioni)
# sy: system CPU (kernel, syscall)
# ni: nice (processi con priorità alterata)
# id: idle
# wa: I/O wait (CPU idle in attesa di I/O)
# hi: hardware interrupts
# si: software interrupts
# st: steal time (hypervisor ha rubato CPU — rilevante in VM/cloud)

# wa alto (>5%) → disco lento o I/O bound
# sy alto (>20%) → troppi syscall, context switch, o kernel overhead
# st alto (>5%) → la VM non riceve abbastanza CPU dall'host
```

### htop

```bash
htop
# Vantaggi su top: navigazione, scroll, tree view, filtri
# F1=Help  F2=Setup  F3=Search  F4=Filter  F5=Tree  F6=Sort
# F9=Kill  F10=Quit
# Spazio=tag  U=untag  K=kill tagged

# Setup (F2): colori, layout, campi, ordinamento

# htop mostra anche:
# Barre per CPU, memoria, swap con colore:
# Verde: user  Rosso: kernel  Blu: low priority  Giallo: IRQ
# Memoria: Verde=used  Blu=buffer  Arancione/Giallo=cache
```

### atop

```bash
# atop — monitoring avanzato con storico
sudo apt install atop
atop                        # Interattivo (CPU, memoria, disco, rete)
# Tasti: c=CPU  m=MEM  d=DISK  n=NET  g=generic
# atop salva log ogni 10 minuti in /var/log/atop/

# Replay storico
atop -r /var/log/atop/atop_20240115  # Leggi log specifico
# t = avanti nel tempo    T = indietro

# atop è unico perché:
# - Registra OGNI processo (anche quelli short-lived)
# - Mantiene storico su disco (fondamentale per post-mortem)
# - Mostra disk/network per processo
# - Evidenzia in rosso le risorse sature

# Configurare intervallo di campionamento
# /etc/default/atop → INTERVAL=60 (secondi)
```

### iotop

```bash
sudo iotop                  # I/O per processo (come top per I/O)
sudo iotop -o               # Solo processi con I/O attivo
sudo iotop -a               # Cumulativo (totale dall'avvio)
sudo iotop -P               # Solo processi (non thread)
# Colonne: DISK READ, DISK WRITE, SWAPIN, IO

# iotop richiede CONFIG_TASK_IO_ACCOUNTING nel kernel
# Se non funziona: alternativa con pidstat -d 1
```

---

## sar e sysstat

sar (System Activity Reporter) raccoglie e riporta statistiche di sistema. Parte del pacchetto sysstat.

```bash
sudo apt install sysstat
# Abilitare raccolta dati: /etc/default/sysstat → ENABLED="true"
sudo systemctl enable --now sysstat

# sar raccoglie dati ogni 10 minuti (configurabile in /etc/cron.d/sysstat)
# Dati salvati in /var/log/sysstat/ o /var/log/sa/

# CPU
sar -u 1 5                  # CPU utilizzo (1 sec, 5 volte)
sar -u -f /var/log/sysstat/sa15   # CPU del giorno 15 del mese

# MEMORIA
sar -r 1 5                  # Memoria
sar -S 1 5                  # Swap

# DISCO
sar -d 1 5                  # I/O per dispositivo
sar -b 1 5                  # I/O totale (trasferimenti/sec)

# RETE
sar -n DEV 1 5              # Traffico per interfaccia
sar -n TCP 1 5              # Statistiche TCP
sar -n SOCK 1 5             # Socket in uso

# LOAD
sar -q 1 5                  # Load average e run queue

# STORICO (giorno specifico)
sar -u -f /var/log/sysstat/sa$(date +%d -d yesterday)  # Ieri
sar -r -s 08:00:00 -e 12:00:00    # Solo dalle 8 alle 12

# Combinare metriche per analisi temporale
sar -u -r -d -n DEV -f /var/log/sysstat/sa$(date +%d) | head -100

# Esportare in formato compatibile con grafici
sadf -d /var/log/sysstat/sa$(date +%d) -- -u -r > perf_data.csv
# sadf -g per output SVG (grafico)
sadf -g /var/log/sysstat/sa$(date +%d) -- -u > cpu_graph.svg
```

---

## Analisi a Livello di Processo

### /proc/[pid]/* — Filesystem Virtuale del Processo

```bash
# Ogni processo ha una directory in /proc/PID/ con informazioni dettagliate

# Status generale
cat /proc/PID/status
# Name:    nome processo
# State:   R (running), S (sleeping), D (disk sleep), Z (zombie), T (stopped)
# Pid:     PID
# PPid:    PID del parent
# Threads: numero thread
# VmPeak:  picco memoria virtuale
# VmSize:  memoria virtuale attuale
# VmRSS:   memoria residente (fisica)
# VmSwap:  memoria in swap
# voluntary_ctxt_switches:    context switch volontari (I/O, sleep)
# nonvoluntary_ctxt_switches: context switch forzati (preemption)

# Mappa memoria dettagliata
cat /proc/PID/maps         # Tutte le mappature (librerie, heap, stack, anon)
cat /proc/PID/smaps        # Come maps ma con dettaglio RSS, PSS, Dirty per segmento
cat /proc/PID/smaps_rollup # Sommario di smaps (kernel 4.14+)

# File descriptor aperti
ls -la /proc/PID/fd        # Lista fd
ls -la /proc/PID/fd | wc -l  # Conteggio fd aperti
cat /proc/PID/limits       # Limiti per il processo (incluso max open files)

# I/O statistics
cat /proc/PID/io
# rchar: bytes letti (include page cache hit)
# wchar: bytes scritti
# read_bytes: bytes letti dal disco (I/O reale)
# write_bytes: bytes scritti sul disco
# cancelled_write_bytes: scritture cancellate (es. file rimosso prima del flush)

# Linea di comando
cat /proc/PID/cmdline | tr '\0' ' '   # Comando completo

# Ambiente
cat /proc/PID/environ | tr '\0' '\n'  # Variabili d'ambiente

# Working directory
readlink /proc/PID/cwd

# Eseguibile
readlink /proc/PID/exe

# Scheduling
cat /proc/PID/sched        # Statistiche scheduler dettagliate
# nr_switches: context switch totali
# exec_runtime: tempo CPU totale (ns)
# wait_sum: tempo in attesa di CPU (ns)
# wait_max: massimo tempo di attesa singolo (ns)

# NUMA info
cat /proc/PID/numa_maps    # Allocazione memoria per nodo NUMA
```

### lsof — Files Aperti da un Processo

```bash
lsof -p PID                # Tutti i file aperti dal processo
lsof -p PID | wc -l        # Conteggio file aperti
lsof -p PID | grep -E "REG|DIR"   # Solo file regolari e directory
lsof -p PID | grep "TCP\|UDP"     # Solo connessioni di rete
lsof -p PID | grep deleted        # File cancellati ma ancora aperti (leak spazio disco)

# File più grandi aperti
lsof -p PID | awk '{print $7, $9}' | sort -n -r | head -10

# Trovare chi usa un file
lsof /var/log/syslog
lsof +D /tmp               # Tutti i file aperti sotto /tmp (ricorsivo)
```

### cgroups Resource Limits

```bash
# Visualizzare cgroup di un processo
cat /proc/PID/cgroup

# Limiti memoria del cgroup (cgroups v2)
cat /sys/fs/cgroup/system.slice/service_name.service/memory.max
cat /sys/fs/cgroup/system.slice/service_name.service/memory.current
cat /sys/fs/cgroup/system.slice/service_name.service/memory.stat

# Limiti CPU del cgroup
cat /sys/fs/cgroup/system.slice/service_name.service/cpu.max
# "200000 100000" = 200ms ogni 100ms = 2 core massimi
cat /sys/fs/cgroup/system.slice/service_name.service/cpu.stat

# I/O limits
cat /sys/fs/cgroup/system.slice/service_name.service/io.stat
cat /sys/fs/cgroup/system.slice/service_name.service/io.max
```

---

## perf Deep Dive

### Installazione e Setup

```bash
sudo apt install linux-tools-common linux-tools-$(uname -r)

# Verificare che perf funzioni
perf --version

# Abilitare perf per utenti non-root (per debug)
sudo sysctl kernel.perf_event_paranoid=1
# -1 = nessuna restrizione (non raccomandato in produzione)
#  0 = permetti user space events senza CAP_SYS_ADMIN
#  1 = permetti user space events (default)
#  2 = solo conteggio eventi (no sampling)
```

### perf stat — Contatori Hardware

```bash
# CPU profiling
sudo perf stat ./myapp              # Statistiche esecuzione
sudo perf top                       # Top per simboli kernel/user
sudo perf record -g ./myapp         # Registra profilo con call graph
sudo perf report                    # Analizza profilo registrato

# Conteggio eventi
sudo perf stat -e cache-misses,cache-references,instructions,cycles ./myapp

# Contatori dettagliati con interpretazione
sudo perf stat -d ./myapp
# task-clock (msec):   tempo CPU usato
# context-switches:    numero di context switch
# cpu-migrations:      migrazioni tra core
# page-faults:         page fault (minor + major)
# cycles:              cicli CPU
# instructions:        istruzioni eseguite
# IPC = instructions / cycles
# branches:            branch instructions
# branch-misses:       predizioni sbagliate
# L1-dcache-load-misses: cache L1 data miss
# LLC-load-misses:     Last Level Cache miss (→ accesso RAM)

# Profilo con intervallo di confidenza
sudo perf stat -r 5 ./myapp        # Ripeti 5 volte, mostra deviazione standard

# Per un processo in esecuzione
sudo perf record -g -p PID -- sleep 30  # Profila PID per 30 secondi
```

### perf record e perf report

```bash
# Registrare un profilo di sistema completo
sudo perf record -g -a -- sleep 30       # Tutto il sistema per 30 secondi
# -g: call graph (stack trace)
# -a: tutti i CPU
# --: separatore tra opzioni perf e comando

# Registrare un processo specifico
sudo perf record -g -p PID -- sleep 10

# Registrare con frequenza specifica
sudo perf record -g -F 99 -a -- sleep 30
# -F 99: 99 Hz (campioni al secondo) — evita bias da timer (non usare 100Hz)

# Registrare con stack dwarf (per linguaggi con frame pointer omesso)
sudo perf record -g --call-graph dwarf -p PID -- sleep 10
# Necessario per Go, Rust, binari compilati con -fomit-frame-pointer

# Analizzare il profilo
sudo perf report
# Interfaccia TUI interattiva:
# Enter: espandi call graph
# +: espandi figlio
# e: espandi tutto
# →/←: navigazione call chain
# a: annota (mostra codice sorgente con istruzioni assembly)
# /: cerca un simbolo

# Output in testo
sudo perf report --stdio           # Output non interattivo
sudo perf report --stdio --sort=dso,symbol  # Raggruppato per libreria e simbolo
```

### perf annotate — Profilo a Livello di Istruzione

```bash
# Mostra il codice sorgente/assembly con i campioni per riga
sudo perf annotate -s symbol_name

# Esempio output:
#  Percent │  Disassembly of function
#   15.20  │  mov    %rax,0x8(%rsp)
#    8.30  │  callq  some_function
#    0.50  │  test   %eax,%eax
# Il 15.20% del tempo è speso su quella istruzione mov

# Annotazione da file registrato
sudo perf record -g ./myapp
sudo perf annotate -i perf.data
```

### perf trace — System Call Tracing

```bash
# Come strace ma con overhead molto inferiore (usa perf subsystem)
sudo perf trace ./myapp              # System call trace
sudo perf trace -s                   # Statistiche syscall aggregate
sudo perf trace -p PID               # Attach a processo

# Solo specifiche syscall
sudo perf trace -e openat,read,write ./myapp

# Con latenza per syscall
sudo perf trace --duration 10 -p PID  # Solo syscall che durano > 10ms

# Confronto overhead:
# strace: 20-100x rallentamento (ptrace-based)
# perf trace: 1-5x rallentamento (kernel-based)
```

---

## Flame Graph

### Concetti

Un flame graph è una visualizzazione dello stack trace aggregato:
- Asse X: ampiezza proporzionale al tempo (o conteggio) speso in quella funzione
- Asse Y: profondità dello stack (dal basso = entry point, verso l'alto = foglia)
- Il colore è casuale (non ha significato)
- Funzioni larghe in alto = dove il tempo viene effettivamente speso (hot path)

### Generare Flame Graph da perf

```bash
# Generare flame graph da perf
sudo perf record -g -a -- sleep 30   # Registra tutto il sistema per 30s
sudo perf script > out.perf

# Con FlameGraph tools (git clone https://github.com/brendangregg/FlameGraph)
./stackcollapse-perf.pl out.perf > out.folded
./flamegraph.pl out.folded > flamegraph.svg
# Aprire flamegraph.svg nel browser

# Con titolo e colori personalizzati
./flamegraph.pl --title "CPU Flame Graph - $(hostname) $(date +%Y-%m-%d)" \
  --colors hot out.folded > flamegraph.svg
```

### CPU Flame Graph

```bash
# Registrare con frequenza ottimale (99 Hz per evitare bias)
sudo perf record -F 99 -g -a -- sleep 30
sudo perf script | ./stackcollapse-perf.pl | ./flamegraph.pl > cpu_flame.svg

# Solo un processo
sudo perf record -F 99 -g -p PID -- sleep 30
sudo perf script | ./stackcollapse-perf.pl | ./flamegraph.pl > process_flame.svg

# Con filtro per thread name
sudo perf script | grep -A1000 "thread_name" | \
  ./stackcollapse-perf.pl | ./flamegraph.pl > thread_flame.svg
```

### Off-CPU Flame Graph

```bash
# Off-CPU: mostra dove il processo aspetta (I/O, lock, sleep)
# Complementare al CPU flame graph

# Con bpftrace (metodo moderno)
sudo bpftrace -e '
  kprobe:finish_task_switch {
    @start[tid] = nsecs;
  }
  kretprobe:finish_task_switch /@start[tid]/ {
    @off[kstack, ustack, comm] = sum(nsecs - @start[tid]);
    delete(@start[tid]);
  }
  END { clear(@start); }
' > offcpu.txt

# Con offcputime (BCC tool)
sudo /usr/share/bcc/tools/offcputime -df -p PID 30 > offcpu.stacks
./flamegraph.pl --color=io --title "Off-CPU" offcpu.stacks > offcpu_flame.svg
```

### Memory Flame Graph

```bash
# Flame graph delle allocazioni memoria
sudo perf record -e page-faults -g -a -- sleep 30
sudo perf script | ./stackcollapse-perf.pl | \
  ./flamegraph.pl --color=mem --title "Page Faults" > mem_flame.svg

# Con malloc tracing (BCC tool)
sudo /usr/share/bcc/tools/memleak -p PID -a 30 > memleak.stacks
# Mostra dove la memoria viene allocata e non liberata
```

### I/O Flame Graph

```bash
# Flame graph delle operazioni I/O
# Registra block I/O events
sudo perf record -e block:block_rq_insert -g -a -- sleep 30
sudo perf script | ./stackcollapse-perf.pl | \
  ./flamegraph.pl --color=io --title "Block I/O" > io_flame.svg
```

### Differential Flame Graph

```bash
# Confrontare due profili (prima e dopo una modifica)
sudo perf record -F 99 -g -a -o before.data -- sleep 30
# ... applicare la modifica ...
sudo perf record -F 99 -g -a -o after.data -- sleep 30

perf script -i before.data | ./stackcollapse-perf.pl > before.folded
perf script -i after.data | ./stackcollapse-perf.pl > after.folded

./difffolded.pl before.folded after.folded | \
  ./flamegraph.pl --title "Differential" > diff_flame.svg
# Rosso = peggiorato (più tempo speso)
# Blu = migliorato (meno tempo speso)
```

---

## strace e ltrace

### strace (system call trace)

```bash
# Tracciare un comando
strace ls /tmp                      # Tutte le syscall
strace -c ls /tmp                   # Statistiche per syscall
strace -e trace=open,read,write ls /tmp  # Solo specifiche syscall
strace -e trace=network curl example.com  # Solo syscall di rete
strace -e trace=file ls /tmp        # Solo syscall su file

# Tracciare processo in esecuzione
sudo strace -p PID                  # Attach a processo
sudo strace -fp PID                 # Con tutti i thread (fork)

# Output
strace -o output.txt ls /tmp       # Salva su file
strace -t ls /tmp                  # Con timestamp
strace -T ls /tmp                  # Con tempo syscall (durata)
strace -yy ls /tmp                 # Decodifica file descriptor

# Filtri comuni
strace -e trace=open,openat cat /etc/passwd  # Quali file apre
strace -e trace=connect curl example.com     # Connessioni di rete

# Conteggio syscall (sommario senza trace completo)
strace -c -S time ./myapp          # Ordinato per tempo totale
# % time   seconds  usecs/call  calls  errors syscall
# 45.20    0.123    15          8192          write
# 30.10    0.082    10          8192          read
# → il 45% del tempo è speso in write()

# Trace con filtro su errori
strace -Z ./myapp                  # Mostra solo syscall che falliscono (errno != 0)

# Trace di rete dettagliato
strace -e trace=%network -s 1024 -p PID
# -s 1024: mostra fino a 1024 bytes di dati (default 32)
```

### ltrace (library call trace)

```bash
ltrace ./myapp                      # Trace chiamate a librerie
ltrace -c ./myapp                   # Statistiche
ltrace -e malloc+free ./myapp       # Solo malloc/free
ltrace -e strlen+strcmp ./myapp     # Solo funzioni stringa

# Combinare con strace per vista completa
# strace → syscall (kernel interface)
# ltrace → library calls (es. malloc prima che diventi mmap/brk)
```

---

## BPF e bpftrace

### Introduzione a BPF/eBPF

BPF (Berkeley Packet Filter) esteso (eBPF) è la tecnologia di osservabilità più potente del kernel Linux moderno. Permette di eseguire codice sicuro nel kernel, agganciandosi a migliaia di punti di osservazione senza modificare il kernel o riavviare.

### Installazione

```bash
# BCC tools (compilati, pronti all'uso)
sudo apt install bpfcc-tools linux-headers-$(uname -r)
# I tool BCC sono installati in /usr/share/bcc/tools/
# oppure disponibili come comandi (es. biosnoop-bpfcc)

# bpftrace (linguaggio di scripting per BPF)
sudo apt install bpftrace
```

### BCC Tools — Strumenti Essenziali

```bash
# === DISCO ===

# biosnoop: traccia ogni richiesta I/O con latenza
sudo biosnoop-bpfcc
# TIME      COMM         PID  DISK  T SECTOR    BYTES  LAT(ms)
# 0.000     mysqld       1234 sda   R 12345678  4096   0.52
# Mostra ESATTAMENTE quale processo fa quale I/O e con quale latenza

# biolatency: distribuzione latenza I/O come istogramma
sudo biolatency-bpfcc
#     usecs       : count    distribution
#       0 -> 1    : 0       |                            |
#       2 -> 3    : 15      |**                          |
#       4 -> 7    : 89      |*************               |
#       8 -> 15   : 245     |************************************|
#      16 -> 31   : 120     |*****************           |

# ext4slower / xfs-slower: operazioni filesystem lente
sudo ext4slower-bpfcc 1    # Operazioni ext4 > 1ms

# === RETE ===

# tcplife: connessioni TCP con durata e bytes
sudo tcplife-bpfcc
# PID    COMM     LADDR          LPORT RADDR          RPORT TX_KB RX_KB MS
# 1234   nginx    10.0.0.1       80    192.168.1.5    54321 15    2     450
# Mostra vita e traffico di ogni connessione TCP

# tcpconnect: nuove connessioni TCP in uscita
sudo tcpconnect-bpfcc
# PID    COMM         SADDR          DADDR          DPORT
# 5678   curl         10.0.0.1       93.184.216.34  80

# tcpaccept: connessioni TCP accettate
sudo tcpaccept-bpfcc

# tcpretrans: ritrasmissioni TCP
sudo tcpretrans-bpfcc
# Ogni ritrasmissione indica packet loss o congestione

# === PROCESSI ===

# execsnoop: trace di ogni exec() (nuovi processi)
sudo execsnoop-bpfcc
# PCOMM    PID    PPID   RET ARGS
# bash     1234   1000   0   /bin/ls -la /tmp
# Fondamentale per trovare processi short-lived che consumano risorse

# opensnoop: trace di ogni open() (file aperti)
sudo opensnoop-bpfcc
# PID    COMM      FD ERR PATH
# 1234   nginx      7   0 /var/www/index.html
# Utile per capire quali file vengono acceduti

# === MEMORIA ===

# memleak: trova memory leak (allocazioni non liberate)
sudo /usr/share/bcc/tools/memleak -p PID
# Mostra stack trace delle allocazioni non liberate

# cachestat: hit/miss ratio della page cache
sudo cachestat-bpfcc
# HITS   MISSES  DIRTIES  HITRATIO  BUFFERS_MB  CACHED_MB
# 12345  456     89       96.4%     128         4096
# Hit ratio basso → I/O frequente verso il disco

# === CPU/SCHEDULING ===

# runqlat: latenza della run queue (tempo in attesa di CPU)
sudo runqlat-bpfcc
# Istogramma del tempo che i processi aspettano prima di ottenere CPU
# Latenza alta = CPU saturata

# cpudist: distribuzione tempo CPU per processo
sudo cpudist-bpfcc
# Mostra per quanto tempo ogni processo usa la CPU prima di cedere

# profile: profilo CPU di tutto il sistema
sudo profile-bpfcc -F 99 30    # 99 Hz per 30 secondi
# Utile per generare flame graph senza perf
```

### bpftrace — One-Liner Essenziali

```bash
# Contare syscall per processo
sudo bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }'

# Istogramma latenza read()
sudo bpftrace -e '
  tracepoint:syscalls:sys_enter_read { @start[tid] = nsecs; }
  tracepoint:syscalls:sys_exit_read /@start[tid]/ {
    @us = hist((nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
  }'

# Top file aperti
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_openat {
  @[str(args.filename)] = count(); }'

# Tracciare signal (kill, SIGTERM, etc.)
sudo bpftrace -e 'tracepoint:signal:signal_deliver {
  printf("PID %d received signal %d\n", pid, args.sig); }'

# Tracciare OOM killer
sudo bpftrace -e 'kprobe:oom_kill_process {
  printf("OOM kill: %s (pid %d)\n", comm, pid); }'

# Latenza DNS (getaddrinfo)
sudo bpftrace -e '
  uprobe:/lib/x86_64-linux-gnu/libc.so.6:getaddrinfo { @start[tid] = nsecs; }
  uretprobe:/lib/x86_64-linux-gnu/libc.so.6:getaddrinfo /@start[tid]/ {
    printf("DNS lookup: %d us\n", (nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
  }'

# Top processi per context switch
sudo bpftrace -e 'tracepoint:sched:sched_switch {
  @[args.prev_comm] = count(); }'

# Tracciare page fault
sudo bpftrace -e 'software:page-faults:1 { @[comm, kstack] = count(); }'

# Monitorare allocazione memoria heap (brk)
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_brk {
  printf("%s (pid %d) brk to %p\n", comm, pid, args.brk); }'

# Contare TCP retransmit per remote address
sudo bpftrace -e 'kprobe:tcp_retransmit_skb {
  @retrans[ntop(((struct sock *)arg0)->__sk_common.skc_daddr)] = count(); }'
```

---

## cgroups v2

### Concetti

cgroups (control groups) v2 è il meccanismo del kernel Linux per limitare, monitorare e isolare le risorse (CPU, memoria, I/O, rete) di gruppi di processi. È alla base di systemd, container (Docker/Podman), e orchestratori (Kubernetes).

### Verifica e Struttura

```bash
# Verificare cgroups v2
mount | grep cgroup2
# Se montato: cgroup2 on /sys/fs/cgroup type cgroup2

# Gerarchia cgroups
ls /sys/fs/cgroup/
# cgroup.controllers     — controller disponibili
# cgroup.subtree_control — controller attivi per i figli
# system.slice/          — servizi systemd
# user.slice/            — sessioni utente

# Controller disponibili
cat /sys/fs/cgroup/cgroup.controllers
# cpu io memory pids

# Vedere cgroup di un processo
cat /proc/PID/cgroup
# 0::/user.slice/user-1000.slice/session-1.scope
```

### Limiti Memoria con cgroups v2

```bash
# Creare un cgroup
sudo mkdir /sys/fs/cgroup/myapp

# Attivare controller
echo "+memory +cpu +io +pids" | sudo tee /sys/fs/cgroup/cgroup.subtree_control

# Limite memoria: 512MB
echo 536870912 | sudo tee /sys/fs/cgroup/myapp/memory.max

# Limite memoria con margine soft (il kernel inizia a reclamare)
echo 402653184 | sudo tee /sys/fs/cgroup/myapp/memory.high  # 384MB soft limit

# Limite swap
echo 0 | sudo tee /sys/fs/cgroup/myapp/memory.swap.max  # No swap

# Aggiungere processo al cgroup
echo PID | sudo tee /sys/fs/cgroup/myapp/cgroup.procs

# Monitorare uso memoria
cat /sys/fs/cgroup/myapp/memory.current    # Uso attuale
cat /sys/fs/cgroup/myapp/memory.stat       # Statistiche dettagliate
cat /sys/fs/cgroup/myapp/memory.events     # Eventi (oom, oom_kill, max, high)
```

### Limiti CPU con cgroups v2

```bash
# Limite CPU: 200ms ogni 100ms = 2 core massimi
echo "200000 100000" | sudo tee /sys/fs/cgroup/myapp/cpu.max
# Formato: $MAX $PERIOD (microsecondi)
# "200000 100000" = 200ms/100ms = 2 CPU max
# "50000 100000"  = 50ms/100ms  = 0.5 CPU max (50%)
# "max 100000"    = nessun limite

# Peso CPU (priorità relativa, non limite assoluto)
echo 100 | sudo tee /sys/fs/cgroup/myapp/cpu.weight
# Range 1-10000, default 100
# 200 = doppia priorità rispetto a 100

# Monitorare
cat /sys/fs/cgroup/myapp/cpu.stat
# usage_usec: tempo CPU usato (microsecondi)
# user_usec: tempo user space
# system_usec: tempo kernel
# nr_periods: numero periodi
# nr_throttled: periodi con throttling
# throttled_usec: tempo di throttling totale
```

### Limiti I/O con cgroups v2

```bash
# Limite I/O per dispositivo
# Formato: major:minor tipo=valore
# Trovare major:minor del disco
lsblk -d -o NAME,MAJ:MIN
# sda  8:0

# Limite read/write bandwidth
echo "8:0 rbps=52428800 wbps=10485760" | sudo tee /sys/fs/cgroup/myapp/io.max
# rbps=50MB/s, wbps=10MB/s

# Limite IOPS
echo "8:0 riops=1000 wiops=500" | sudo tee /sys/fs/cgroup/myapp/io.max
# 1000 read IOPS, 500 write IOPS

# Peso I/O (priorità relativa)
echo "8:0 200" | sudo tee /sys/fs/cgroup/myapp/io.weight
# Range 1-10000, default 100

# Monitorare
cat /sys/fs/cgroup/myapp/io.stat
# 8:0 rbytes=12345 wbytes=67890 rios=100 wios=50 dbytes=0 dios=0
```

### Limiti PID con cgroups v2

```bash
# Limite numero processi/thread (fork bomb protection)
echo 100 | sudo tee /sys/fs/cgroup/myapp/pids.max

# Monitorare
cat /sys/fs/cgroup/myapp/pids.current   # Processi attuali
```

### systemd Integration

```bash
# systemd usa nativamente cgroups v2 per ogni servizio

# Impostare limiti via systemd (persistenti)
sudo systemctl edit myapp.service
# [Service]
# MemoryMax=512M
# MemoryHigh=384M
# CPUQuota=200%
# IOWriteBandwidthMax=/dev/sda 10M
# TasksMax=100

# Verificare limiti attivi
systemctl show myapp.service | grep -E "Memory|CPU|IO|Tasks"

# Vedere risorse usate
systemd-cgtop                        # Top per cgroup (come top ma per servizi)
systemctl status myapp.service       # Include CPU e memoria

# Limite transitorio (non persistente)
sudo systemd-run --scope -p MemoryMax=256M -p CPUQuota=50% ./myapp
```

---

## Benchmark e Stress Test

### Metodologia di Benchmarking

```
Un benchmark valido richiede:
1. DEFINIRE l'obiettivo: cosa si misura? (throughput, latenza, IOPS)
2. ISOLARE le variabili: controllare tutte le condizioni
3. WARM-UP: eseguire il test una volta prima di registrare (cache, JIT, etc.)
4. RIPETERE: almeno 3-5 run per avere deviazione standard
5. BASELINE: confrontare con un riferimento noto
6. DOCUMENTARE: hardware, software, parametri, versioni, data
```

### Errori Comuni nel Benchmarking

```
1. Benchmarking con cache calde vs fredde (risultati non riproducibili)
   → Flush cache: sync && echo 3 > /proc/sys/vm/drop_caches

2. Non considerare il warm-up (JIT, page cache, connection pool)
   → Aggiungere fase di warm-up prima della misurazione

3. Usare medie senza percentili
   → Riportare sempre: media, p50, p95, p99, p99.9, max

4. Benchmark troppo breve (non cattura GC, compaction, flush)
   → Almeno 60 secondi per workload steady-state

5. Saturare la rete del benchmark tool stesso
   → Misurare risorse del tool di benchmark, non solo del target

6. Non controllare interferenze (cron, backup, aggiornamenti)
   → Eseguire durante finestra pulita, monitorare risorse di sistema

7. Coordinata omission: non contare le richieste non inviate
   → Usare tool che corregge (wrk2, hdr_histogram)

8. Confrontare risultati tra hardware diverso
   → Documentare ESATTAMENTE l'hardware per ogni run
```

### CPU Benchmark

```bash
sudo apt install stress-ng sysbench

stress-ng --cpu 4 --timeout 60s    # Stress 4 core per 60s
stress-ng --cpu 4 --cpu-method matrixprod --metrics-brief --timeout 60s
sysbench cpu run                    # Benchmark CPU
sysbench cpu --threads=4 --time=30 run  # 4 thread per 30 secondi

# Benchmark specifici
# Integer performance
stress-ng --cpu 0 --cpu-method int64 --metrics-brief --timeout 30s

# Floating point
stress-ng --cpu 0 --cpu-method double --metrics-brief --timeout 30s

# Context switch benchmark
stress-ng --context 4 --timeout 30s --metrics-brief
```

### Memory Benchmark

```bash
# MEMORIA
stress-ng --vm 2 --vm-bytes 1G --timeout 60s  # Stress 2GB RAM
sysbench memory run
sysbench memory --memory-block-size=1K --memory-total-size=10G --threads=4 run

# Bandwidth memoria
sudo apt install mbw
mbw 256              # Test bandwidth memoria con 256MB
# Mostra: MEMCPY, DUMB, MCBLOCK bandwidth in MiB/s

# STREAM benchmark (standard per bandwidth memoria)
# Misura: Copy, Scale, Add, Triad operations
# Compilare: gcc -O3 -march=native -fopenmp stream.c -o stream
# Download: https://www.cs.virginia.edu/stream/
```

### Disco I/O Benchmark

```bash
# fio (flexible I/O tester)
sudo apt install fio

# Lettura sequenziale
fio --name=seqread --rw=read --bs=1M --size=1G --numjobs=1 --runtime=30

# Scrittura random
fio --name=randwrite --rw=randwrite --bs=4k --size=1G --numjobs=4 --runtime=30

# Mixed read/write (come database)
fio --name=mixed --rw=randrw --rwmixread=70 --bs=4k --size=1G --numjobs=4 --runtime=30

# sysbench per disco
sysbench fileio --file-total-size=2G prepare
sysbench fileio --file-total-size=2G --file-test-mode=rndrw run
sysbench fileio --file-total-size=2G cleanup

# dd — test grezzo (solo per stima rapida)
# Scrittura sequenziale
dd if=/dev/zero of=/tmp/testfile bs=1M count=1024 conv=fdatasync
# Lettura sequenziale
dd if=/tmp/testfile of=/dev/null bs=1M
# ATTENZIONE: dd non è un benchmark affidabile. Usare fio.
```

### Rete Benchmark

```bash
# RETE
iperf3 -s                          # Avvia server
iperf3 -c server_ip -t 30          # Test 30 secondi
iperf3 -c server_ip -R             # Reverse (download)
iperf3 -c server_ip -P 4           # 4 stream paralleli

# netperf (alternativa più sofisticata)
sudo apt install netperf
netserver                            # Avvia server
netperf -H server_ip -l 30          # TCP stream test 30s
netperf -H server_ip -t TCP_RR      # TCP request/response (latenza)
netperf -H server_ip -t UDP_STREAM  # UDP throughput

# HTTP benchmark
sudo apt install wrk
wrk -t4 -c100 -d30s http://localhost:8080/
# -t4: 4 thread
# -c100: 100 connessioni
# -d30s: durata 30 secondi
# Output: Latency (avg, stdev, max, +/- stdev), Req/sec, Transfer/sec
```

### Suite di Benchmark Completa

```bash
# BENCHMARK COMPLETO
sudo apt install phoronix-test-suite
phoronix-test-suite benchmark pts/disk  # Benchmark disco
phoronix-test-suite benchmark pts/cpu   # Benchmark CPU
phoronix-test-suite benchmark pts/memory # Benchmark memoria
phoronix-test-suite benchmark pts/network # Benchmark rete

# UnixBench (benchmark classico)
# git clone https://github.com/kdlucas/byte-unixbench
# cd byte-unixbench/UnixBench && make && ./Run
```

---

## Tuning Avanzato del Kernel

### TCP Stack Tuning Completo

```bash
# === BUFFER ===
# Buffer massimi per socket (globali)
net.core.rmem_max = 16777216          # 16MB max receive buffer
net.core.wmem_max = 16777216          # 16MB max send buffer
net.core.rmem_default = 262144        # 256KB default receive
net.core.wmem_default = 262144        # 256KB default send

# Buffer TCP per socket (min, default, max)
net.ipv4.tcp_rmem = 4096 131072 16777216
net.ipv4.tcp_wmem = 4096 131072 16777216
# Il kernel auto-tuna tra default e max in base alla rete

# === CONNESSIONI ===
# Listen queue
net.core.somaxconn = 65535            # Max pending connections (default 4096)
net.ipv4.tcp_max_syn_backlog = 65535  # SYN queue size

# TIME_WAIT
net.ipv4.tcp_tw_reuse = 1            # Riusa TIME_WAIT per connessioni uscenti
net.ipv4.tcp_fin_timeout = 30         # Timeout FIN-WAIT-2 (default 60)
net.ipv4.tcp_max_tw_buckets = 2000000 # Max TIME_WAIT sockets

# === PERFORMANCE ===
# Congestion control
net.ipv4.tcp_congestion_control = bbr # Google BBR
net.core.default_qdisc = fq           # Fair queueing (richiesto da BBR)

# Fast Open (TFO) — reduce latenza connessione
net.ipv4.tcp_fastopen = 3             # 1=client, 2=server, 3=both

# Window scaling
net.ipv4.tcp_window_scaling = 1       # Finestre > 64KB
net.ipv4.tcp_timestamps = 1           # Necessario per window scaling

# === SECURITY ===
# SYN cookies
net.ipv4.tcp_syncookies = 1           # Protezione SYN flood

# Backlog di ingresso
net.core.netdev_max_backlog = 10000   # Coda pacchetti per CPU (default 1000)
net.core.netdev_budget = 600          # NAPI budget

# === KEEPALIVE ===
net.ipv4.tcp_keepalive_time = 300     # Primo probe dopo 5 min
net.ipv4.tcp_keepalive_intvl = 30     # Intervallo tra probe
net.ipv4.tcp_keepalive_probes = 5     # Tentativi

# === APPLICARE ===
sudo sysctl -p /etc/sysctl.d/99-tcp-tuning.conf
```

### Filesystem Tuning

```bash
# === vm.dirty_* (vedi sezione Memoria per dettagli) ===
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.dirty_expire_centisecs = 1500
vm.dirty_writeback_centisecs = 500

# === VFS cache ===
vm.vfs_cache_pressure = 50           # Default 100
# < 100: il kernel tiene dentries/inodes in cache più a lungo (buono per molti file)
# > 100: il kernel li rilascia prima (buono per poca RAM)
# 50: buon valore per server file/database

# === readahead ===
# Per workload sequenziale (backup, video, data pipeline)
blockdev --getra /dev/sda            # Valore attuale (in settori di 512 bytes)
sudo blockdev --setra 2048 /dev/sda  # 1MB readahead (2048 * 512 = 1MB)

# Per workload random (database)
sudo blockdev --setra 32 /dev/sda   # 16KB readahead

# === ext4 specific ===
# Journal mode
# data=ordered (default): metadata journal, data flushed before metadata commit
# data=writeback: solo metadata journal (più veloce, rischio dati inconsistenti)
# data=journal: dati e metadata nel journal (più lento, massima sicurezza)

# Creare con opzioni ottimizzate
mkfs.ext4 -E stride=16,stripe-width=64 -O dir_index,extent /dev/sda1
# stride/stripe-width: per RAID

# === XFS specific ===
# XFS è generalmente migliore per grandi file e alto throughput
# Opzioni mount
# logbufs=8: più buffer per il journal (default 8, max 8)
# allocsize=64k: dimensione allocazione (per file grandi)
# nobarrier: se il controller ha BBU
```

### Scheduler Tuning

```bash
# === CPU scheduler ===
# Completly Fair Scheduler (CFS) — default Linux

# Latenza target: tempo dopo cui CFS rischedula
kernel.sched_latency_ns = 6000000         # 6ms (default)
kernel.sched_min_granularity_ns = 750000  # 750us min time slice

# Per server (più throughput, meno preemption)
kernel.sched_latency_ns = 24000000
kernel.sched_min_granularity_ns = 3000000
kernel.sched_wakeup_granularity_ns = 4000000

# Per desktop/latency-sensitive
kernel.sched_latency_ns = 4000000
kernel.sched_min_granularity_ns = 500000

# NUMA balancing automatico
kernel.numa_balancing = 1                  # Abilita (default)
# Il kernel migra automaticamente le pagine al nodo NUMA del processo

# === I/O scheduler === (vedi sezione Disco)
# Per ogni disco:
cat /sys/block/sda/queue/scheduler
echo mq-deadline > /sys/block/sda/queue/scheduler  # HDD
echo none > /sys/block/nvme0n1/queue/scheduler     # NVMe
```

### Parametri Kernel Completi per Server

```bash
# /etc/sysctl.d/99-server-tuning.conf

# === MEMORIA ===
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.dirty_expire_centisecs = 1500
vm.vfs_cache_pressure = 50
vm.min_free_kbytes = 131072
vm.overcommit_memory = 0
vm.zone_reclaim_mode = 0

# === RETE ===
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 10000
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 131072 16777216
net.ipv4.tcp_wmem = 4096 131072 16777216
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535

# === FILE SYSTEM ===
fs.file-max = 2097152
fs.nr_open = 2097152
fs.inotify.max_user_watches = 524288

# === KERNEL ===
kernel.pid_max = 4194304
kernel.threads-max = 4194304

# Applicare
sudo sysctl -p /etc/sysctl.d/99-server-tuning.conf
```

---

## Capacity Planning

### Monitoraggio Trend

```bash
# Raccogliere dati storici con sar (sysstat)
# Configurazione in /etc/cron.d/sysstat → raccolta ogni 10 minuti
# Dati in /var/log/sysstat/saDD (DD = giorno del mese)

# Esportare dati per analisi
sadf -d /var/log/sysstat/sa$(date +%d) -- -u -r -d -n DEV > performance.csv

# Script per raccogliere metriche chiave giornaliere
#!/bin/bash
DATE=$(date +%Y-%m-%d)
echo "$DATE,$(free -m | awk '/^Mem:/{print $3}'),$(df -BG / | awk 'NR==2{print $3}'),\
$(uptime | awk -F'load average:' '{print $2}' | cut -d, -f1 | tr -d ' ')" >> /var/log/capacity.csv

# Analisi trend con sar storico
# CPU trend dell'ultimo mese
for day in $(seq 1 31); do
  FILE="/var/log/sysstat/sa$(printf '%02d' $day)"
  [ -f "$FILE" ] && sar -u -f "$FILE" | tail -1
done
```

### Metriche per Capacity Planning

```
Per ogni risorsa, tracciare:

CPU:
- Utilizzo medio e picco (p95) per ora/giorno
- Load average normalizzato (load / nproc)
- Trend: cresce? A che velocità?
- Proiezione: quando raggiunge il 70%? (soglia di azione)

MEMORIA:
- MemAvailable nel tempo
- Swap usage trend
- RSS totale dei processi principali
- Trend di crescita (memory leak → crescita lineare)

DISCO:
- Spazio usato e tasso di crescita
- IOPS e throughput nel tempo
- %util e await trend
- Proiezione: quando il disco è pieno?

RETE:
- Bandwidth utilizzata vs capacità
- Connessioni concorrenti nel tempo
- Error rate trend
```

### Forecasting

```
Approccio semplice:

1. Raccogliere almeno 30 giorni di dati
2. Calcolare tasso di crescita giornaliero/settimanale
3. Proiezione lineare: valore_futuro = valore_attuale + (tasso * giorni)
4. Aggiungere margine (20-30%) per picchi

Esempio:
- Disco: 500GB usati, crescita 2GB/giorno
- Disco totale: 1TB
- Spazio rimanente: 500GB
- Tempo prima di full: 500 / 2 = 250 giorni
- Con margine 20%: azione quando 800GB usati → (800-500)/2 = 150 giorni
```

### Right-Sizing

```
Server sovradimensionato (spreco di costi):
- CPU avg < 10% per settimane
- RAM available > 70%
- Disco usato < 30%

Server sottodimensionato (rischio performance):
- CPU avg > 70%
- Swap attivamente usato
- Disco %util > 80% regolarmente
- Rete > 60% della capacità

Regole pratiche:
- CPU: target 40-60% utilizzo medio, capacità per gestire picchi al 80%
- RAM: target 60-70% utilizzata (il resto per page cache)
- Disco: non superare 80% spazio, %util sotto 70% per HDD
- Rete: non superare 70% della capacità link
```

---

## Workflow di Performance Profiling

### Approccio Sistematico: dal Sintomo alla Causa

```
FASE 1: TRIAGE (60 secondi)
┌─────────────────────────────────────────────────────┐
│ uptime → dmesg -T | tail → vmstat 1 5               │
│ mpstat -P ALL 1 3 → pidstat 1 3 → iostat -xz 1 3   │
│ free -h → sar -n DEV 1 3 → top                      │
└─────────────────────────────────────────────────────┘
    │
    ├── CPU alta? ──→ FASE 2A: CPU Analysis
    ├── I/O wait alto? ──→ FASE 2B: Disk Analysis
    ├── Memoria bassa? ──→ FASE 2C: Memory Analysis
    ├── Rete saturata? ──→ FASE 2D: Network Analysis
    └── Nessuno chiaro? ──→ FASE 2E: Process Analysis

FASE 2A: CPU ANALYSIS
┌─────────────────────────────────────────────────────┐
│ pidstat -u 1 → identificare processo                 │
│ perf top -p PID → funzioni calde                     │
│ perf record -g -p PID -- sleep 30                    │
│ perf report → call graph                             │
│ Flame graph → visualizzazione                        │
│ strace -cp PID → se syscall heavy                    │
└─────────────────────────────────────────────────────┘

FASE 2B: DISK ANALYSIS
┌─────────────────────────────────────────────────────┐
│ iostat -xz 1 → quale disco è saturo                  │
│ iotop -o → quale processo fa I/O                     │
│ biosnoop → trace I/O individuali                     │
│ biolatency → distribuzione latenza                   │
│ strace -e trace=file -p PID → file aperti            │
│ lsof -p PID → file descriptor                        │
└─────────────────────────────────────────────────────┘

FASE 2C: MEMORY ANALYSIS
┌─────────────────────────────────────────────────────┐
│ free -h → conferma                                   │
│ cat /proc/meminfo → dettaglio                        │
│ smem -t -k → PSS per processo                        │
│ pmap -x PID → mappa memoria                          │
│ valgrind → se sospetto memory leak                   │
│ slabtop → se kernel cache grande                     │
└─────────────────────────────────────────────────────┘

FASE 2D: NETWORK ANALYSIS
┌─────────────────────────────────────────────────────┐
│ ss -s → statistiche generali                         │
│ ss -ti → dettaglio connessioni TCP                   │
│ nstat → contatori errori/retransmit                  │
│ ethtool -S eth0 → errori NIC                         │
│ tcpdump → cattura traffico se necessario             │
│ iperf3 → benchmark se sospetto hardware              │
└─────────────────────────────────────────────────────┘

FASE 2E: PROCESS ANALYSIS
┌─────────────────────────────────────────────────────┐
│ cat /proc/PID/status → stato processo                │
│ cat /proc/PID/io → I/O statistics                    │
│ strace -c -p PID → syscall profile                   │
│ perf trace -p PID → syscall con meno overhead        │
│ /proc/PID/sched → scheduling stats                   │
│ execsnoop → processi short-lived                     │
└─────────────────────────────────────────────────────┘

FASE 3: ROOT CAUSE
┌─────────────────────────────────────────────────────┐
│ Confermare l'ipotesi con dati aggiuntivi             │
│ Verificare se il problema è riproducibile            │
│ Controllare che il fix non introduca side effects    │
│ Documentare causa e soluzione                        │
└─────────────────────────────────────────────────────┘
```

---

## Best Practices

1. **Baseline prima di tutto**: registrare le performance normali (baseline) prima che ci sia un problema. Senza baseline, non si può determinare cosa è "lento"
2. **USE method**: per ogni risorsa controllare Utilization, Saturation, Errors. Approccio sistematico > intuizione
3. **Una variabile alla volta**: quando si fa tuning, cambiare un parametro alla volta e misurare l'effetto. Cambiamenti multipli rendono impossibile capire cosa ha funzionato
4. **Monitoraggio continuo**: installare sysstat (sar) e atop su ogni server di produzione. I dati storici sono fondamentali per diagnosticare problemi intermittenti
5. **Non ottimizzare prematuramente**: prima identificare il collo di bottiglia reale. Ottimizzare la CPU quando il disco è il problema non migliora nulla
6. **Documentare ogni modifica**: annotare ogni parametro sysctl, ogni mount option, ogni tuning applicato. Con il motivo e l'effetto misurato
7. **Usare percentili, non medie**: la media nasconde i problemi. Riportare p50, p95, p99, p99.9 per le metriche di latenza
8. **Monitorare le code, non solo l'utilizzo**: un disco al 60% ma con una coda di 10 richieste è più problematico di uno al 90% con coda 1
9. **Attenzione alla coordinata omission**: nei benchmark, se il tool non invia richieste quando il server è lento, i risultati sono ottimistici
10. **Testare il tuning sotto carico reale**: i parametri sysctl ottimali variano enormemente con il workload. Non applicare "tuning guides" alla cieca
11. **Conoscere i limiti del hardware**: SSD SATA ha limiti diversi da NVMe. 1Gbps ha limiti diversi da 10Gbps
12. **Non ignorare gli errori**: un disco con 5 errori SMART è un disco che sta morendo, non un disco "quasi sano"

---

## Troubleshooting

### Problema 1: "Sistema lento, load average alto"

```bash
# Diagnosi
uptime                      # Confermare load alto
vmstat 1 5                  # CPU (us/sy) vs I/O (wa)?

# Se CPU bound (us+sy alto, wa basso):
pidstat -u 1                # Processo colpevole
perf top -p PID             # Funzione calda
strace -c -p PID            # Syscall profile

# Se I/O bound (wa alto):
iotop -o                    # Processo con I/O
iostat -xz 1                # Disco saturo
```

### Problema 2: "Memoria piena, sistema in swap"

```bash
# Diagnosi
free -h                     # Conferma swap attivo
vmstat 1 5                  # Colonne si/so > 0?
ps aux --sort=-%mem | head  # Top consumer

# Se cache alta ma available ok → normale (Linux usa RAM libera come cache)
# Se swap attivo → servono più RAM o c'è un memory leak

# Trovare memory leak
smem -t -k -s pss           # PSS crescente nel tempo = leak
cat /proc/PID/smaps_rollup  # RSS, PSS, Swap per processo
# Monitorare nel tempo:
watch -n10 'cat /proc/PID/status | grep -E "VmRSS|VmSwap"'
```

### Problema 3: "I/O wait alto"

```bash
# Diagnosi
iostat -xz 1                # %util ~100%, await alto → disco saturo
iotop -o                    # Processo colpevole
biosnoop                    # Dettaglio ogni I/O

# Soluzioni:
# 1. I/O scheduler: mq-deadline per HDD, none per SSD
# 2. Spostare workload su disco più veloce
# 3. Ottimizzare query database (meno I/O random)
# 4. Aggiungere cache applicativa (Redis, memcached)
# 5. Aumentare RAM → più page cache → meno I/O disco
# 6. Verificare readahead: troppo alto per random I/O, troppo basso per sequenziale
```

### Problema 4: "Processo usa 100% CPU"

```bash
# Diagnosi
top -H -p PID               # Quale thread?
strace -c -p PID            # Syscall profile
perf record -g -p PID -- sleep 10
perf report                 # Call graph

# Se infinite loop:
perf top -p PID             # Funzione calda in tempo reale
# Flame graph per visualizzare

# Se syscall heavy:
strace -T -e trace=read,write -p PID  # Tempo per syscall
# read/write molto frequenti = I/O inefficiente (buffer troppo piccolo)
```

### Problema 5: "Latenza di rete alta"

```bash
# Diagnosi
mtr target_ip               # Dove si perde tempo (hop per hop)
ss -ti dst target_ip         # Statistiche TCP (retransmit, rtt, cwnd)
ethtool -S eth0 | grep -i err  # Errori NIC

# Verificare MTU
ping -M do -s 1472 target_ip  # Test MTU (1472 + 28 header = 1500)

# Verificare duplex/speed
ethtool eth0 | grep -E "Speed|Duplex"
# Half duplex = problema

# TCP tuning per alta latenza (WAN)
# Aumentare buffer TCP e abilitare BBR
```

### Problema 6: "Connessioni refused / timeout sul web server"

```bash
# Diagnosi
ss -ltn                     # Listen queue: Recv-Q vs Send-Q
# Recv-Q > 0 → connessioni in attesa di accept()
# Se Recv-Q si avvicina a Send-Q → backlog pieno

nstat | grep -i "listen"    # ListenOverflows, ListenDrops
# ListenOverflows > 0 → connessioni perse

# Fix
sudo sysctl -w net.core.somaxconn=65535
# Configurare il web server per usare un backlog grande:
# nginx: listen 80 backlog=65535;
# Apache: ListenBackLog 65535
```

### Problema 7: "Server diventa lento dopo ore/giorni"

```bash
# Diagnosi: confrontare stato attuale con baseline

# Memory leak?
smem -t -k -s pss            # PSS crescente?
cat /proc/PID/status | grep VmRSS  # Confrontare con valore iniziale

# Log file crescita?
du -sh /var/log/*             # Log enormi?
lsof +D /var/log | sort -k7 -n -r | head  # File aperti grandi

# File descriptor leak?
ls /proc/PID/fd | wc -l       # Confrontare con valore iniziale
# Se cresce nel tempo → fd leak (connessioni non chiuse)

# Connection leak?
ss -tan | awk '{print $1}' | sort | uniq -c | sort -rn
# CLOSE-WAIT crescente → l'applicazione non chiude le connessioni

# Frammentazione memoria?
cat /proc/buddyinfo            # Distribuzione free pages
# Pochi blocchi grandi → frammentazione
echo 1 | sudo tee /proc/sys/vm/compact_memory  # Compattazione manuale
```

### Problema 8: "OOM killer uccide processi"

```bash
# Diagnosi
dmesg | grep -i "oom\|killed process"
# [ ] Out of memory: Killed process 1234 (myapp) total-vm:4096kB...

# Capire perché
cat /proc/meminfo | grep -E "MemTotal|MemAvailable|CommitLimit|Committed_AS"
# Committed_AS > CommitLimit → overcommit

# Proteggere un processo dal OOM
echo -1000 | sudo tee /proc/PID/oom_score_adj
# Rendere sacrificabile un processo meno importante
echo 1000 | sudo tee /proc/PID_LESS_IMPORTANT/oom_score_adj

# Prevenzione
# 1. Più RAM
# 2. cgroups con memory.max per limitare singoli servizi
# 3. vm.overcommit_memory=2 (no overcommit)
# 4. Monitoraggio proattivo della memoria
```

### Problema 9: "Disco pieno improvvisamente"

```bash
# File grandi
du -sh /* | sort -h | tail -10
du -sh /var/log/* | sort -h | tail -10

# File cancellati ma ancora aperti (spazio non rilasciato)
lsof +L1 | grep deleted
# Se un processo tiene aperto un file cancellato, lo spazio non è liberato
# Fix: riavviare il processo, o troncare il fd:
# > /proc/PID/fd/FD_NUMBER  (se il file è un log)

# Inode esauriti (spazio libero ma "no space left")
df -i
# Se IUsed è al 100% → troppi file piccoli
# Fix: trovare ed eliminare file inutili
find /tmp -type f -mtime +30 | head -20
```

### Problema 10: "CPU steal time alto (VM/Cloud)"

```bash
# Diagnosi
top    # st% alto nella riga CPU

mpstat -P ALL 1 5
# %steal > 5% → l'hypervisor sta rubando CPU a questa VM

# Cause:
# 1. Overcommit CPU sull'host (troppe VM, poca CPU fisica)
# 2. Noisy neighbor (altra VM sullo stesso host usa troppa CPU)
# 3. CPU throttling dal provider cloud

# Fix:
# 1. Migrare a un host meno carico
# 2. Passare a istanza dedicata (no overcommit)
# 3. Contattare il provider cloud
# 4. Ottimizzare il workload per usare meno CPU
```

### Problema 11: "NUMA imbalance"

```bash
# Diagnosi
numastat
# Se node0 ha molte allocazioni e node1 poche → imbalance
numastat -p PID
# numa_miss alto → allocazioni nel nodo sbagliato

# Fix
numactl --cpunodebind=0 --membind=0 ./myapp  # Bind a nodo 0
# Per processi già in esecuzione: migrare le pagine
sudo migratepages PID 1 0  # Da nodo 1 a nodo 0
```

### Problema 12: "Latenza intermittente / jitter"

```bash
# Cause comuni:
# 1. GC pause (Java, Go, Python)
# 2. CPU frequency scaling
# 3. IRQ storm
# 4. Background I/O (fsync, journal commit)
# 5. NUMA remote access

# Diagnosi
# Verificare C-state (CPU power states)
turbostat --quiet --interval 1
# C1, C6 → CPU va in sleep tra i task, risveglio ha latenza

# Disabilitare C-state per latenza minima
echo 0 | sudo tee /sys/devices/system/cpu/cpu*/cpuidle/state*/disable

# Verificare frequency scaling
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq
# Frequenza variabile → usare governor "performance"

# Verificare IRQ distribution
cat /proc/interrupts | head -5
# Se un core riceve molti più IRQ → irqbalance non funziona
```

### Problema 13: "Fork bomb / troppi processi"

```bash
# Diagnosi
ps aux | wc -l               # Numero processi
pstree -p | head -50          # Albero processi

# Limite processi per utente
ulimit -u                     # Limite attuale
cat /proc/PID/limits | grep "Max processes"

# Fix immediato: kill dell'albero
pkill -u problematic_user     # Kill tutti i processi dell'utente

# Prevenzione con cgroups
echo 500 | sudo tee /sys/fs/cgroup/user.slice/user-1000.slice/pids.max

# Prevenzione con limits.conf
# /etc/security/limits.conf
# username  hard  nproc  500
```

### Problema 14: "SSD performance degradata nel tempo"

```bash
# Diagnosi
smartctl -a /dev/sda | grep -E "Wear_Leveling|Media_Wearout|Percentage_Used"
# Wear > 90% → SSD vicino a fine vita

# TRIM non configurato?
sudo fstrim -v /
# Se recupera molto spazio → TRIM non era attivo

# Fix
sudo systemctl enable --now fstrim.timer  # TRIM periodico
# Verificare mount option: nessun "discard" necessario con fstrim.timer
```

### Problema 15: "Kernel panic / MCE (Machine Check Exception)"

```bash
# Diagnosi
dmesg | grep -i "mce\|machine check\|hardware error"
mcelog --client                # Se disponibile

# MCE può indicare:
# - RAM difettosa (ECC errors)
# - CPU overheating
# - Errori bus

# Verificare temperatura
sensors                        # Se lm-sensors installato
cat /sys/class/thermal/thermal_zone*/temp

# Fix: problema hardware, sostituire componente difettoso
```

### Problema 16: "Applicazione Java lenta (GC pause)"

```bash
# Diagnosi
# Verificare GC activity
jstat -gc PID 1000            # GC stats ogni secondo
# FGC (Full GC count) e FGCT (Full GC time) crescono → problema

# GC log
# Abilitare: -Xlog:gc*:file=gc.log:time,level,tags
# Analizzare con GCViewer o GCEasy

# Fix:
# 1. Aumentare heap (-Xmx)
# 2. Cambiare GC algorithm (G1, ZGC, Shenandoah)
# 3. Ridurre allocation rate
# 4. Ottimizzare object lifetime
```

### Problema 17: "Database lento (PostgreSQL/MySQL)"

```bash
# Diagnosi
iostat -xz 1                  # Disco saturo?
free -h                       # Shared buffers in cache?

# PostgreSQL
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity WHERE state != 'idle';"
sudo -u postgres psql -c "SELECT * FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;"
# n_dead_tup alto → serve VACUUM

# Query lente
# PostgreSQL: pg_stat_statements, auto_explain
# MySQL: slow_query_log, performance_schema

# Fix comuni:
# 1. Più RAM per buffer cache (shared_buffers, innodb_buffer_pool_size)
# 2. Indici mancanti (EXPLAIN ANALYZE)
# 3. VACUUM/ANALYZE (PostgreSQL)
# 4. Disabilitare THP (echo never > .../transparent_hugepage/enabled)
# 5. vm.swappiness=1 (evitare swap del buffer pool)
# 6. Ottimizzare checkpoint/WAL (checkpoint_completion_target)
```

### Problema 18: "Container Docker/Podman lento"

```bash
# Diagnosi
docker stats                  # CPU, MEM, NET, I/O per container
docker inspect --format '{{.HostConfig.Memory}}' container_name

# Verificare limiti cgroup
cat /sys/fs/cgroup/system.slice/docker-CONTAINER_ID.scope/memory.current
cat /sys/fs/cgroup/system.slice/docker-CONTAINER_ID.scope/cpu.stat
# nr_throttled > 0 → CPU throttling

# I/O overlay filesystem
# L'overlay FS ha overhead. Per I/O intensivo:
# 1. Usare volume mount (bind mount) per dati
# 2. Usare tmpfs per dati temporanei
# 3. Usare storage driver ottimale (overlay2)

# Network
# bridge networking ha overhead. Per performance:
# 1. --network=host (nessun overhead, ma nessun isolamento)
# 2. macvlan per performance con isolamento
```

### Problema 19: "Errori "Too many open files""

```bash
# Diagnosi
ulimit -n                     # Limite file aperti per processo
cat /proc/PID/limits | grep "Max open files"
ls /proc/PID/fd | wc -l       # File aperti attuali

# Fix temporaneo
ulimit -n 65536               # Per la sessione corrente

# Fix permanente
# /etc/security/limits.conf
# *  soft  nofile  65536
# *  hard  nofile  65536

# systemd service
# [Service]
# LimitNOFILE=65536

# Limite globale del sistema
sudo sysctl -w fs.file-max=2097152
cat /proc/sys/fs/file-nr      # (in_uso, riservati, massimo)
```

### Problema 20: "Rete lenta tra due host nella stessa LAN"

```bash
# Diagnosi
iperf3 -c peer_ip             # Bandwidth test
ping -c 100 peer_ip | tail -3 # Packet loss e jitter

# Verificare duplex mismatch
ethtool eth0 | grep -E "Speed|Duplex"
# Half duplex su un link full duplex → performance terribili

# Verificare errori
ethtool -S eth0 | grep -iE "err|drop|collision|crc"
# CRC errors → cavo difettoso o SFP
# Collision → half duplex

# Verificare MTU
ip link show eth0 | grep mtu
# MTU mismatch causa frammentazione

# Verificare offload
ethtool -k eth0 | grep -E "generic-receive|tcp-segmentation"
# Se disabilitati e il workload è pesante → abilitare

# Fix:
# 1. Forzare speed/duplex: ethtool -s eth0 speed 1000 duplex full
# 2. Sostituire cavo
# 3. Verificare switch port config
```

### Problema 21: "Scritture su disco molto lente (ext4)"

```bash
# Diagnosi
iostat -xz 1                  # await e %util

# Verificare journal mode
mount | grep sda1
# data=ordered → ogni scrittura aspetta il journal

# Verificare barrier
# Se il controller ha BBU (Battery Backup Unit):
mount -o remount,nobarrier /dev/sda1 /mount_point

# Verificare vm.dirty_*
sysctl vm.dirty_ratio vm.dirty_background_ratio
# dirty_ratio troppo basso → flush troppo frequente

# Fix:
# 1. noatime mount option (eliminare scritture inutili)
# 2. Journal mode writeback (se accettabile): tune2fs -o journal_data_writeback
# 3. Ottimizzare dirty_ratio per il workload
# 4. Verificare allineamento partizione (per SSD)
```

---

## Checklist per Workload Specifici

### Checklist Server Web (Nginx/Apache)

```
[ ] net.core.somaxconn >= 65535
[ ] net.ipv4.tcp_tw_reuse = 1
[ ] net.ipv4.tcp_fin_timeout = 30
[ ] net.core.netdev_max_backlog >= 5000
[ ] fs.file-max >= 2097152
[ ] worker_processes = auto (nginx) o adeguato
[ ] keepalive_timeout configurato
[ ] gzip/brotli abilitati
[ ] access log buffered (non synchronous)
[ ] static files con sendfile e tcp_nopush
[ ] TLS session cache abilitata
[ ] HTTP/2 abilitato
[ ] Monitorare: connessioni attive, latenza p99, error rate
```

### Checklist Server Database

```
[ ] vm.swappiness = 1 (o al massimo 10)
[ ] THP disabilitato (transparent_hugepage = never)
[ ] I/O scheduler: mq-deadline (HDD) o none (SSD)
[ ] noatime su filesystem dati
[ ] vm.dirty_ratio = 5-15 (bilanciare durabilità vs performance)
[ ] vm.dirty_background_ratio = 2-5
[ ] Huge Pages statiche configurate (se supportate dal DB)
[ ] Buffer pool dimensionato (60-80% RAM disponibile)
[ ] WAL/binlog su disco separato (se possibile)
[ ] TRIM/fstrim configurato per SSD
[ ] Monitorare: query lente, lock wait, buffer hit ratio, replication lag
[ ] vm.overcommit_memory != 1 (evitare OOM imprevedibile)
[ ] Checkpoint tuning (non troppo frequente, non troppo raro)
```

### Checklist Container / Kubernetes

```
[ ] cgroups v2 abilitati
[ ] Memory limits impostati (non lasciare unbounded)
[ ] CPU limits impostati (attenzione al throttling)
[ ] Resource requests = uso tipico, limits = picco accettabile
[ ] Liveness/readiness probe configurate
[ ] Storage: volume mount per dati, non overlay
[ ] Network: CNI plugin performance testato
[ ] DNS: cache locale (NodeLocal DNS)
[ ] Log: non scrivere su stdout se alto volume (usare sidecar o agente)
[ ] Monitorare: restart count, OOMKilled events, CPU throttling
[ ] Kernel: file-max, inotify.max_user_watches aumentati
[ ] PID limits configurati (fork bomb protection)
```

### Checklist Server Generico (Hardening Performance)

```
[ ] sysstat (sar) installato e abilitato
[ ] atop installato con log retention
[ ] NTP sincronizzato (chrony o systemd-timesyncd)
[ ] I/O scheduler appropriato per tipo di disco
[ ] Filesystem mount con noatime
[ ] vm.swappiness adeguato al workload
[ ] TCP tuning applicato (buffer, congestion, backlog)
[ ] ulimits adeguati (nofile, nproc)
[ ] Log rotation configurata
[ ] Monitoraggio proattivo (Prometheus, Grafana, o equivalente)
[ ] Baseline di performance documentata
[ ] Procedure di escalation documentate
```

### Checklist Applicazioni Real-Time e Low-Latency

Per applicazioni che richiedono latenza predicibile e bassa (trading, audio processing, sistemi di controllo industriale, gaming server), il tuning standard non e sufficiente. Servono interventi specifici per eliminare le fonti di jitter.

```
[ ] Kernel PREEMPT_RT (real-time) o CONFIG_PREEMPT=y (low-latency)
[ ] CPU isolation con isolcpus= per dedicare core all'applicazione
[ ] IRQ affinity: spostare tutti gli interrupt dai core isolati
[ ] Disabilitare frequency scaling: governor = performance
[ ] Disabilitare C-states profondi: idle=poll o max_cstate=1
[ ] Disabilitare THP (Transparent Huge Pages)
[ ] Disabilitare NUMA balancing automatico: numa_balancing=0
[ ] Pinning dei thread applicativi con taskset o cgroups cpuset
[ ] Memory locking: mlockall() per evitare page fault
[ ] Pre-fault dello stack: allocare e toccare tutte le pagine all'avvio
[ ] Timer resolution: CONFIG_HZ=1000 o tickless (NO_HZ_FULL)
[ ] RCU callback offloading: rcu_nocbs= per i core isolati
[ ] Network: busy polling (net.core.busy_poll, net.core.busy_read)
[ ] Network: kernel bypass con DPDK o AF_XDP per ultra-low-latency
[ ] Disabilitare watchdog NMI: nmi_watchdog=0
[ ] Monitorare: cyclictest per misurare jitter del kernel
```

**Diagnostica jitter con cyclictest:**

```bash
# Installare rt-tests
apt install rt-tests    # Debian/Ubuntu
dnf install rt-tests    # Fedora/RHEL

# Test di base: misurare la latenza di scheduling su tutti i core
cyclictest -m -p 90 -i 200 -l 100000 -a

# Output:
# T: 0 ( 1234) P:90 I:200 C: 100000 Min:      1 Act:    2 Avg:    2 Max:   15
# Min/Avg/Max in microsecondi. Max < 50μs = buon sistema RT
# Max > 1000μs = problemi seri di jitter

# Test sotto carico (eseguire in parallelo):
stress-ng --cpu 4 --io 2 --vm 2 --timeout 60s &
cyclictest -m -p 90 -i 200 -l 500000 -a
```

**Isolamento CPU completo:**

```bash
# /etc/default/grub — parametri kernel
GRUB_CMDLINE_LINUX="isolcpus=2,3 nohz_full=2,3 rcu_nocbs=2,3 \
  irqaffinity=0,1 nosoftlockup intel_idle.max_cstate=1 \
  processor.max_cstate=1 idle=poll"

# Dopo update-grub e reboot, verificare:
cat /sys/devices/system/cpu/isolated      # Deve mostrare 2,3
taskset -cp 1                             # PID 1 non deve usare core 2,3

# Spostare tutti gli IRQ dai core isolati:
for irq in /proc/irq/*/smp_affinity_list; do
    echo "0,1" > "$irq" 2>/dev/null
done

# Spostare i servizi di sistema dai core isolati:
systemctl set-property -- system.slice AllowedCPUs=0,1
```

La differenza tra un sistema non ottimizzato e uno ottimizzato per latenza puo essere di ordini di grandezza: da picchi di jitter di 10+ millisecondi a worst-case di 10-50 microsecondi con un kernel PREEMPT_RT correttamente configurato. Il costo e una riduzione del throughput complessivo: i core isolati sono dedicati esclusivamente all'applicazione critica e non partecipano al bilanciamento generale del carico.

### Metodologia di Capacity Planning Quantitativa

Il capacity planning non e un'arte ma una disciplina ingegneristica basata su modelli matematici. L'obiettivo e determinare **quando** le risorse attuali raggiungeranno la saturazione e **quanto** bisogna aggiungere per sostenere la crescita prevista.

**Fase 1 — Raccolta del baseline:**

```bash
# Raccogliere dati per almeno 4 settimane (includere cicli settimanali)
# Configurare sar per retention estesa:
# /etc/sysstat/sysstat — HISTORY=90

# Estrarre metriche aggregate:
# CPU: picco e media giornaliera
sar -u -f /var/log/sysstat/sa$(date -d "7 days ago" +%d) | \
  awk '/Average/ {print "CPU avg:", 100-$NF "%"}'

# Memoria: trend di utilizzo
sar -r -f /var/log/sysstat/sa$(date -d "7 days ago" +%d) | \
  awk '/Average/ {print "MEM used:", $4/(1024*1024) "GB"}'

# Disco: IOPS e throughput
sar -d -f /var/log/sysstat/sa$(date -d "7 days ago" +%d) | \
  awk '/Average.*dev/ {print $2, "tps:", $3, "await:", $8 "ms"}'
```

**Fase 2 — Modellazione della crescita:**

La proiezione piu semplice e la regressione lineare sul trend delle metriche chiave. Per workload con crescita organica (utenti, dati, transazioni), il modello lineare e spesso sufficiente per orizzonti di 3-6 mesi.

```
Esempio: CPU utilization trend

Settimana 1: 45% medio, 72% picco
Settimana 2: 47% medio, 75% picco
Settimana 3: 49% medio, 78% picco
Settimana 4: 51% medio, 80% picco

Tasso di crescita: +2% / settimana (picco)
Soglia di allarme: 85%
Soglia critica: 90%
Settimane alla soglia di allarme: (85 - 80) / 2 = 2.5 settimane
Settimane alla soglia critica: (90 - 80) / 2 = 5 settimane

Azione: capacity upgrade entro 2 settimane
```

**Fase 3 — Dimensionamento:**

| Risorsa | Formula di dimensionamento | Note |
|---------|---------------------------|------|
| CPU | core_necessari = tps_target / tps_per_core * 1.3 | Il fattore 1.3 e il margine per picchi |
| RAM | ram_totale = working_set + buffer_pool + os_overhead + 20% | Il 20% e per crescita e cache |
| Disco IOPS | iops_necessari = iops_picco * 1.5 | Il fattore 1.5 copre burst I/O |
| Rete | banda = throughput_picco * 2 | Headroom per burst e overhead protocollo |

Il capacity planning deve essere un processo continuo, non un esercizio una tantum. Le metriche di utilizzo devono essere monitorate con alert sulla soglia dell'80% di utilizzo picco per ogni risorsa critica. Quando una risorsa supera costantemente l'80% di utilizzo nei periodi di picco, l'intervento di upgrade deve essere gia pianificato e schedulato — aspettare il 90% o oltre significa operare in zona di rischio dove un picco imprevisto puo causare degradazione del servizio o downtime.

---

## FAQ

### 1. Qual è la differenza tra "free" e "available" nell'output di `free`?

`free` è la RAM non usata dal kernel per nessuno scopo. `available` include `free` più la memoria in buffer/cache che il kernel può reclamare se necessario. Su un sistema sano, `free` può essere molto basso (il kernel usa la RAM come cache), ma `available` dovrebbe essere adeguato. Guardare sempre `available`, non `free`.

### 2. Il load average è 8.0 su un server con 4 core. È un problema?

Sì. Il load average normalizzato è 8/4 = 2.0, ovvero il doppio della capacità. Significa che in media 4 processi stanno usando la CPU e 4 sono in coda. Verificare con `vmstat 1`: se la colonna `r` è costantemente > 4, serve più CPU o bisogna ottimizzare i processi. Se il load è dovuto a I/O wait (`wa` alto in `top`), il problema è il disco, non la CPU.

### 3. Come capisco se il problema è CPU-bound o I/O-bound?

Usare `vmstat 1 5`. Se `us + sy` è alto e `wa` è basso → CPU-bound. Se `wa` è alto → I/O-bound. Se la colonna `b` (blocked) è alta → processi bloccati su I/O. Anche `top` mostra `%wa` nella riga di sommario CPU.

### 4. Quando devo preoccuparmi dello swap?

Avere swap configurata è buona pratica. Lo swap diventa problematico quando è usato attivamente: `vmstat 1` con `si/so` costantemente > 0 indica che il sistema sta continuamente spostando pagine tra RAM e disco. Questo degrada le performance. La soluzione è più RAM, ottimizzare i processi, o ridurre il carico.

### 5. Cosa significa %steal in top?

`%steal` (st) indica che il CPU virtuale è in attesa perché l'hypervisor ha assegnato quel tempo a un'altra VM. È rilevante solo in ambienti virtualizzati (VM cloud, KVM, Xen). Se `st` è costantemente > 5%, la VM non riceve abbastanza CPU dall'host fisico. Soluzioni: migrare a un host meno carico, passare a istanze dedicate, o ottimizzare il workload.

### 6. Come faccio un flame graph in 3 comandi?

```bash
sudo perf record -F 99 -g -a -- sleep 30
sudo perf script | /path/to/stackcollapse-perf.pl | /path/to/flamegraph.pl > flame.svg
firefox flame.svg
```

### 7. Differenza tra perf e strace?

`strace` traccia solo le syscall (interfaccia user→kernel) e usa ptrace, con overhead alto (20-100x). `perf` può fare lo stesso (`perf trace`) con overhead molto minore (1-5x) perché opera a livello kernel. Inoltre, `perf` può profilare anche funzioni user space, cache miss, branch miss, e molti altri eventi hardware. Usare `strace` per diagnostica rapida; `perf` per profiling serio.

### 8. Devo disabilitare Transparent Huge Pages (THP)?

Dipende dal workload. THP è benefico per applicazioni con grandi allocazioni lineari (calcolo scientifico, HPC). È problematico per database (PostgreSQL, MongoDB, Redis) perché le operazioni di compaction e splitting delle huge pages causano latency spike imprevedibili. Regola: se il workload è sensibile alla latenza, disabilitare THP.

### 9. Che congestion control TCP usare: cubic o bbr?

`cubic` è il default Linux ed è ottimo per reti con bassa perdita di pacchetti. `bbr` (Google) è migliore su reti con packet loss (internet, WAN, mobile) perché si basa su modello di bandwidth anziché su packet loss come segnale di congestione. Per server web/API esposti a Internet, BBR è generalmente la scelta migliore. Per LAN ad alta velocità, cubic è sufficiente.

### 10. Come monitoro la performance senza installare nulla?

Tutti questi strumenti sono generalmente presenti su ogni sistema Linux:

```bash
# CPU
cat /proc/stat
cat /proc/loadavg
top -bn1

# Memoria
cat /proc/meminfo
cat /proc/swaps

# Disco
cat /proc/diskstats

# Rete
cat /proc/net/dev
cat /proc/net/tcp
ss -s

# Processi
cat /proc/PID/status
cat /proc/PID/io
cat /proc/PID/sched
ls /proc/PID/fd | wc -l
```

### 11. Qual è il rapporto tra RSS, PSS e USS?

RSS (Resident Set Size) include la memoria condivisa contata per intero per ogni processo. Se 10 processi condividono 50MB di librerie, RSS di ogni processo include quei 50MB. PSS (Proportional Set Size) divide equamente la memoria condivisa: ogni processo conta 5MB. USS (Unique Set Size) conta solo la memoria privata del processo. Per il capacity planning, PSS è la metrica più affidabile.

### 12. Come interpreto l'IPC (Instructions Per Cycle)?

IPC indica quante istruzioni il processore completa per ciclo di clock. IPC < 1.0 suggerisce che il processore è spesso in stallo (cache miss, TLB miss, branch misprediction). IPC > 1.0 indica buona efficienza. IPC > 2.0 è ottimo. Si misura con `perf stat`: IPC = instructions / cycles. Un IPC basso spesso si risolve ottimizzando l'accesso alla memoria (layout dati, NUMA, cache-friendly algorithms).

### 13. Che differenza c'è tra biosnoop (BCC) e iotop?

`iotop` mostra il throughput I/O aggregato per processo (KB/s letti/scritti). `biosnoop` (BCC tool basato su BPF) traccia ogni singola richiesta I/O con la sua latenza, il settore, la dimensione, e il processo. `biosnoop` è molto più dettagliato e utile per diagnosticare problemi di latenza. `iotop` è sufficiente per identificare "chi fa più I/O".

### 14. Come dimensiono i buffer TCP per una rete 10Gbps?

La regola è: buffer_size >= bandwidth * RTT (Bandwidth-Delay Product). Per 10Gbps con 1ms RTT: BDP = 10Gbps * 1ms = 10Mbit = 1.25MB. Per 10Gbps con 50ms RTT (WAN): BDP = 10Gbps * 50ms = 500Mbit = 62.5MB. Configurare `tcp_rmem/tcp_wmem` con max almeno uguale al BDP. Per LAN: `net.ipv4.tcp_rmem = "4096 131072 16777216"`. Per WAN ad alta velocità: `net.ipv4.tcp_rmem = "4096 131072 67108864"`.

### 15. Quando usare bpftrace vs BCC tools?

I BCC tools sono strumenti pronti all'uso per task specifici (biosnoop per I/O, tcplife per TCP, execsnoop per exec). Usarli quando esiste un tool per il problema. `bpftrace` è un linguaggio di scripting per creare tool personalizzati al volo. Usarlo quando nessun BCC tool copre il caso d'uso, o quando serve un one-liner rapido per esplorare un comportamento specifico del sistema.

### 16. Come verifico che il tuning sysctl sia stato applicato correttamente?

```bash
# Verificare un singolo parametro
sysctl net.core.somaxconn
# Output: net.core.somaxconn = 65535

# Verificare tutti i parametri modificati
sysctl -a | grep -E "somaxconn|swappiness|dirty_ratio|tcp_rmem"

# Verificare che persista al reboot
# I file in /etc/sysctl.d/*.conf sono applicati al boot
# Verificare: sysctl -p /etc/sysctl.d/99-tuning.conf
```

### 17. PSI (Pressure Stall Information) — come usarlo?

```bash
# PSI è disponibile dal kernel 4.20+
cat /proc/pressure/cpu
cat /proc/pressure/memory
cat /proc/pressure/io

# "some" = qualche task è in stallo (percentuale del tempo)
# "full" = tutti i task sono in stallo (percentuale del tempo)
# avg10, avg60, avg300 = medie su 10s, 60s, 300s

# Interpretazione:
# some avg10=25.00 → il 25% del tempo almeno un task aspetta questa risorsa
# full avg10=10.00 → il 10% del tempo TUTTI i task aspettano → critico

# PSI è il segnale più diretto di pressione sulle risorse
# Più affidabile di load average per capire se il sistema è sotto stress
```
