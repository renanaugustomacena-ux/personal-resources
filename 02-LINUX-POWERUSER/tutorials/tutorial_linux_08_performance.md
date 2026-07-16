# Tutorial Linux 08 — Performance: top, htop, vmstat, iostat, perf, sar

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** monitoraggio CPU/RAM/I-O, bottleneck analysis, tuning, benchmarking
> **Prerequisiti:** `tutorial_linux_07_kernel.md`
> **Durata stimata:** 12-16 ore

---

## Mappa concettuale

```
Performance Linux
│
├── CPU
│   ├── top / htop — processi in tempo reale
│   ├── mpstat — per-CPU stats
│   ├── perf — profiling kernel/user
│   └── load average — media carico
│
├── Memoria
│   ├── free — RAM/swap overview
│   ├── vmstat — paging, swapping
│   ├── smem — memoria per processo (precisa)
│   └── /proc/meminfo
│
├── I/O Disco
│   ├── iostat — throughput, latenza
│   ├── iotop — processi che usano I/O
│   ├── blktrace — trace I/O
│   └── fio — benchmark disco
│
├── Rete
│   ├── iftop / nethogs — uso rete per processo
│   ├── sar -n — statistiche rete storiche
│   └── ethtool — statistiche NIC
│
└── Storico con sar (sysstat)
    ├── sar -u CPU
    ├── sar -r RAM
    ├── sar -b I/O
    └── sar -n DEV rete
```

---

# Parte A — CPU e load

---

## A1. top e htop

```bash
# top — monitor classico
top
# Intestazione:
# top - 10:00:00 up 5 days, load average: 0.52, 0.48, 0.45
# Tasks: 120 total, 1 running
# %Cpu(s): 5.2 us, 2.1 sy, 0.0 ni, 91.5 id, 0.8 wa, 0.0 hi, 0.4 si
# MiB Mem: 15900.0 total, 8234.5 free, 4532.1 used, 3133.4 buff/cache
# MiB Swap: 2048.0 total, 1900.0 free, 148.0 used

# Colonne CPU:
# us = user (codice applicazione)
# sy = system (kernel)
# wa = I/O wait (attesa disco — se alto c'è un problema I/O)
# si = software interrupt (rete)
# id = idle

# Comandi interattivi in top:
# 1 — mostra CPU per core
# M — ordina per memoria
# P — ordina per CPU (default)
# T — ordina per runtime
# k — kill un processo (chiede PID)
# u — filtra per utente
# q — esci

# htop — versione moderna (apt install htop)
htop
# F5 = tree view (gerarchia processi)
# F6 = ordina per colonna
# F9 = kill con scelta segnale
# F3/F4 = cerca e filtra

# Interpretare load average:
# 3 valori: 1 min, 5 min, 15 min
# Valore ideale: < numero CPU
# 4 CPU: load 4.0 = piena capacità, 8.0 = sovraccarico

# Numero CPU logiche
nproc
cat /proc/cpuinfo | grep "^processor" | wc -l
```

> **Analogia:** Il load average è come la fila allo sportello di una banca. Se hai 4 sportelli (CPU) e il numero medio di persone in fila è 4, tutti vengono serviti subito. Se è 8, metà deve aspettare. Se è 0.5, gli sportelli sono per lo più vuoti. Il valore "wa" (I/O wait) è come uno sportellista che aspetta che arrivi un documento dall'archivio — è occupato ma non sta elaborando.

---

## A2. Analisi per core con mpstat

```bash
# mpstat da sysstat
apt install sysstat

# Statistiche per core ogni 2 secondi
mpstat -P ALL 2

# Solo CPU 0 e 1
mpstat -P 0,1 1 5

# Confronto su 4 core (output esempio):
# CPU    %usr   %sys   %iowait  %idle
# all    15.2    8.1      0.5   76.2
# 0      60.1    5.2      0.1   34.6   ← core sovraccarico
# 1       2.1    1.0      0.2   96.7
# 2       3.5    8.9      0.3   87.3
# 3       5.1   17.3      1.4   76.2

# Problema visibile: core 0 al 60% user mentre gli altri sono liberi
# → processo single-threaded, non usa multipli core
```

---

## A3. perf: profiling kernel

```bash
# apt install linux-tools-$(uname -r) linux-tools-generic

# CPU cycles per programma
perf stat ls -la /usr/bin

# Profiling di un processo (10 secondi)
perf record -g -p $(pgrep nginx) -- sleep 10
perf report

# Syscall tracing
perf trace -p $(pgrep python3)

# Top functions a caldo
perf top

# Flamegraph (richiede FlameGraph tool)
perf record -g myapp
perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl > out.svg
```

---

# Parte B — Memoria

---

## B1. vmstat e free

```bash
# free — panoramica memoria
free -h
#               total   used   free  shared  buff/cache  available
# Mem:          15.5G   4.4G   8.2G    1.2G        2.9G      10.4G
# Swap:          2.0G   148M   1.9G

# Nota: "available" è più utile di "free"
# available = free + cache recuperabile immediatamente

# vmstat — stats memoria, swap, CPU, I/O
vmstat 2             # ogni 2 secondi
vmstat 2 10          # 10 campioni ogni 2 secondi

# Output:
# procs: r=runnable (in coda CPU), b=blocked (attesa I/O)
# memory: swpd, free, buff, cache
# swap: si=swap-in, so=swap-out (se > 0: problema RAM)
# io: bi=block-in, bo=block-out (blocchi disco)
# system: in=interrupts, cs=context-switches (alto = overhead)
# cpu: us sy id wa st

# Segnali di problema:
# so > 0 continuamente → RAM insufficiente, swap attivo
# wa > 20% → bottleneck I/O disco
# cs molto alto → overhead context switching (troppi thread?)
# r > numero CPU → CPU saturation

# /proc/meminfo per dettagli
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable|Cached|Buffers|Slab"
```

---

## B2. Identificare processi "memory hungry"

```bash
# ps con sorting memoria
ps aux --sort=-%mem | head -20
ps -o pid,user,%mem,rss,vsz,comm --sort=-%mem | head -20

# smem — memoria reale (esclude shared)
# apt install smem
smem --no-header -s rss -r | head -20
smem -t -k           # totale, unità K

# pmap — mappa memoria di un processo
pmap -x $(pgrep python3)
# Address    Kbytes     RSS   Dirty Mode  Mapping
# 00400000     2044    1680       0 r-x-- python3

# Calcola memoria effettivamente usata
# RSS = Resident Set Size (fisica)
# VSZ = Virtual Size (include mmap, potenziale)
# PSS = Proportional Set Size (condivisa proporzionalmente)
```

---

# Parte C — I/O disco

---

## C1. iostat

```bash
# iostat — statistiche I/O
iostat                    # snapshot
iostat -x 2              # extended ogni 2 secondi
iostat -x -d 2 sda sdb  # solo sda e sdb

# Colonne importanti:
# %util = utilizzo dispositivo (100% = saturo)
# await = latenza media richiesta (ms) — ideale <10ms per SSD
# r_await / w_await = latenza separata read/write
# r/s, w/s = operazioni per secondo
# rMB/s, wMB/s = throughput

# Segnali di problema:
# %util > 80% per SSD → sotto carico
# %util > 50% per HDD → probabilmente saturo
# await > 100ms → attesa I/O elevata

# iotop — top per I/O (come top ma per disco)
apt install iotop
iotop               # interattivo
iotop -ao           # solo processi con I/O attivo

# fio — benchmark disco
apt install fio

# Test throughput lettura sequenziale
fio --name=read-test \
    --rw=read \
    --bs=1M \
    --numjobs=1 \
    --size=4G \
    --runtime=30 \
    --time_based \
    --output-format=normal

# Test IOPS random 4K (simula database)
fio --name=random-rw \
    --rw=randrw \
    --bs=4k \
    --numjobs=4 \
    --size=1G \
    --runtime=30 \
    --time_based \
    --iodepth=32
```

---

# Parte D — Dati storici con sar

---

## D1. sysstat e sar

```bash
# Abilita raccolta dati (ogni 10 minuti)
systemctl enable --now sysstat

# /etc/default/sysstat
# ENABLED="true"

# sar — system activity reporter
# CPU
sar -u 2 5         # ogni 2s, 5 campioni
sar -u             # storico oggi
sar -u -f /var/log/sysstat/sa15   # storico 15 del mese

# RAM
sar -r 2 5         # ogni 2s, 5 campioni
sar -r --human     # con unità human-readable

# I/O
sar -b 2 5
sar -d 2 5         # per dispositivo

# Rete
sar -n DEV 2 5     # statistiche interfacce
sar -n EDEV 2 5    # errori interfaccia

# Swap
sar -S 2 5

# Tutto insieme per un'ora fa
sar -A 1 60

# Report su file
sar -A > /tmp/report-sar-$(date +%Y%m%d).txt
```

---

# Parte E — Riepilogo

## Checklist diagnostica performance

```bash
# CPU saturata?
top          # %us + %sy vicino a 100%
vmstat 1     # r > numero CPU

# Memoria esaurita?
free -h      # available quasi zero
vmstat 1     # so > 0 (swap out attivo)

# Disco lento?
iostat -x 1  # %util > 80%, await > 50ms
iotop        # quale processo causa I/O

# Rete lenta?
iftop        # traffico per connessione
sar -n DEV 1 # statistiche interfaccia

# Strumenti per scenario
```

## Quick commands

| Scenario | Comando |
|---|---|
| CPU alta, quale processo? | `top -o %CPU` / `htop` |
| Memoria alta, quale processo? | `ps aux --sort=-%mem` |
| I/O alto, quale processo? | `iotop -ao` |
| Network alto, quale processo? | `nethogs eth0` |
| Dati storici CPU ieri | `sar -u -f /var/log/sysstat/sa$(date -d yesterday +%d)` |
| Latenza disco? | `iostat -x 1 \| grep await` |
| Swap attivo? | `vmstat 1 \| awk '{print $7, $8}'` |

## Prossimi passi

- `tutorial_linux_09_gestione_processi.md` — ps, strace, lsof, segnali
- `tutorial_linux_20_monitoring.md` — Prometheus + Grafana
