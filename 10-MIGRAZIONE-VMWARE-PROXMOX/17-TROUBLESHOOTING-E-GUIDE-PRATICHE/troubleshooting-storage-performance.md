# Troubleshooting Storage Performance

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 7 — Day-2 operations · Modulo 17.4 (chiude troubleshooting, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 03 (storage backend Proxmox), modulo 09.3 (high-I/O VM); fluenza con `iostat`, `iotop`, `fio`, `arcstat`.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. diagnosticare degrado prestazioni storage post-migrazione: confrontare `fio` baseline VMware vs Proxmox, identificare delta;
> 2. risolvere causes comuni: cache mode errato (`writeback` invece di `none`), iothread mancante, formato qcow2 invece di raw, scheduler I/O subottimale, ARC ZFS sotto-dimensionato, latency Ceph;
> 3. usare strumenti diagnostici: `iostat -xdmz`, `iotop -b -o`, `arcstat`, `ceph osd perf`, `qm config <VMID>`.
> **Tempo stimato:** lettura 60 min · uso reattivo durante incident
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27

## Idee guida

1. **Il primo step e *misurare* il delta vs baseline.** Senza baseline VMware, "lento" e soggettivo. Con baseline → fio post-migration → delta percentuale → decisioni informate.
2. **Le cause sono spesso configurazioni VM, non backend.** `cache=writeback` invece di `none`, qcow2 invece di raw, missing iothread: 60% dei problemi storage sono qui.
3. **Per Ceph, il backend stesso puo essere il problema.** Un OSD lento, network jumbo-mismatch, replica deep-scrub in corso degradano tutto il cluster. `ceph osd perf` + `ceph -s` per identify.

---

## Indice

1. [Panoramica Problemi di Performance Storage](#panoramica)
2. [Alta Latenza e IOPS Bassi](#alta-latenza)
3. [Disk Cache: Configurazione Corretta](#disk-cache)
4. [VirtIO vs IDE: Gap di Prestazioni](#virtio-vs-ide)
5. [Ceph Slow Ops](#ceph-slow-ops)
6. [ZFS: ARC e SLOG Issues](#zfs-issues)
7. [NFS Performance Problems](#nfs-performance)
8. [Benchmarking con fio](#benchmarking-fio)
9. [Identificare i Bottleneck](#identificare-bottleneck)
10. [Tuning per Storage Backend](#tuning-per-backend)
11. [Confronto Prestazioni Pre/Post Migrazione](#confronto-prestazioni)

---

## Panoramica Problemi di Performance Storage {#panoramica}

Le prestazioni dello storage sono spesso il fattore piu critico nelle performance complessive di una VM. Dopo una migrazione da VMware a Proxmox, e normale osservare differenze nelle prestazioni dello storage dovute a:

- **Controller disco diverso**: PVSCSI di VMware vs VirtIO SCSI di Proxmox
- **Cache policy diversa**: VMware gestisce la cache internamente, Proxmox offre piu opzioni
- **Storage backend diverso**: VMFS vs ZFS/LVM/Ceph
- **I/O scheduler diverso**: VMware usa il proprio scheduler, Linux usa mq-deadline, none, kyber
- **Formato disco diverso**: VMDK (flat/sparse) vs qcow2/raw

### Metriche di Riferimento

| Metrica | Definizione | Target HDD | Target SSD | Target NVMe |
|---|---|---|---|---|
| IOPS (Read) | Operazioni I/O al secondo in lettura | 100-200 | 10,000-50,000 | 100,000-500,000 |
| IOPS (Write) | Operazioni I/O al secondo in scrittura | 100-200 | 10,000-50,000 | 100,000-300,000 |
| Latenza (Read) | Tempo per completare una operazione di lettura | < 10ms | < 0.5ms | < 0.1ms |
| Latenza (Write) | Tempo per completare una operazione di scrittura | < 10ms | < 0.5ms | < 0.1ms |
| Throughput (Seq Read) | MB/s in lettura sequenziale | 100-200 | 500-550 | 2,000-7,000 |
| Throughput (Seq Write) | MB/s in scrittura sequenziale | 100-200 | 400-500 | 1,500-5,000 |

---

## Alta Latenza e IOPS Bassi {#alta-latenza}

### Diagnostica Rapida

```bash
# Dal nodo Proxmox: verificare I/O del disco fisico
iostat -xm 1 5
# Colonne importanti:
# %util - utilizzo del disco (>80% indica saturazione)
# await - latenza media delle operazioni (ms)
# r_await / w_await - latenza lettura/scrittura separate
# r/s, w/s - IOPS lettura/scrittura

# Esempio output problematico:
# Device    r/s    w/s   rMB/s  wMB/s  r_await  w_await  %util
# sda      15.00  250.00  0.12   2.50   5.20    85.30    99.80
# -> w_await alto (85ms) e %util al 100% = disco saturato

# Verificare le operazioni I/O per processo
iotop -o -b -n 3
# Mostra quali processi stanno generando I/O

# Verificare la coda I/O
cat /sys/block/sda/queue/nr_requests
cat /sys/block/sda/queue/scheduler
```

### Cause Comuni di Alta Latenza

**Causa 1: Disco fisico saturato**

```bash
# Verificare quante VM condividono lo stesso disco/storage
pvesm status
lvs  # Per LVM
zpool iostat -v 1 5  # Per ZFS
ceph osd perf  # Per Ceph

# Soluzione: distribuire le VM su storage diversi
# o aggiungere storage piu veloce
```

**Causa 2: I/O Scheduler non ottimale**

```bash
# Verificare lo scheduler corrente
cat /sys/block/sda/queue/scheduler
# Per SSD/NVMe: dovrebbe essere [none] o [mq-deadline]
# Per HDD: dovrebbe essere [mq-deadline]

# Cambiare lo scheduler
echo "none" > /sys/block/sda/queue/scheduler  # Per SSD/NVMe
echo "mq-deadline" > /sys/block/sda/queue/scheduler  # Per HDD

# Rendere permanente
# In /etc/udev/rules.d/60-ioschedulers.rules:
# SSD/NVMe:
ACTION=="add|change", KERNEL=="sd[a-z]*|nvme[0-9]*n[0-9]*", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="none"
# HDD:
ACTION=="add|change", KERNEL=="sd[a-z]*", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="mq-deadline"
```

**Causa 3: Formato disco non ottimale**

```bash
# Verificare il formato del disco VM
qm config <vmid> | grep -E "scsi|ide|sata|virtio"
# Se mostra format=qcow2, potrebbe essere meno performante di raw

# Convertire qcow2 a raw (su LVM-Thin o Ceph)
qemu-img convert -f qcow2 -O raw \
    /var/lib/vz/images/<vmid>/vm-<vmid>-disk-0.qcow2 \
    /var/lib/vz/images/<vmid>/vm-<vmid>-disk-0.raw

# Su LVM-Thin, usare direttamente raw:
# Il formato raw e gia il default su LVM-Thin
```

---

## Disk Cache: Configurazione Corretta {#disk-cache}

### Opzioni di Cache in Proxmox

| Modalita Cache | Descrizione | Sicurezza Dati | Performance | Uso Consigliato |
|---|---|---|---|---|
| `none` (Default) | Nessuna cache host, O_DIRECT | Alta | Buona | Storage con propria cache (Ceph, ZFS, HW RAID) |
| `directsync` | Scritture sincrone, no cache | Massima | Bassa | Quando la sicurezza dei dati e prioritaria |
| `writethrough` | Cache in lettura, scritture sincrone | Alta | Media | Uso generale sicuro |
| `writeback` | Cache completa, scritture asincrone | Bassa (rischio) | Alta | Solo con UPS e battery-backed RAID |
| `unsafe` | Ignora flush, cache completa | Minima | Massima | Solo per test, MAI in produzione |

### Configurare la Cache

```bash
# Verificare la cache attuale
qm config <vmid> | grep -E "scsi|ide|sata|virtio"
# Esempio: scsi0: local-lvm:vm-100-disk-0,size=50G
# Se non c'e "cache=", il default e "none"

# Impostare la cache
qm set <vmid> -scsi0 local-lvm:vm-100-disk-0,size=50G,cache=writeback
qm set <vmid> -scsi0 local-lvm:vm-100-disk-0,size=50G,cache=writethrough
qm set <vmid> -scsi0 local-lvm:vm-100-disk-0,size=50G,cache=none

# Raccomandazioni per storage backend:
# ZFS: cache=none (ZFS ha il proprio ARC)
# Ceph/RBD: cache=writeback (Ceph gestisce la consistenza)
# LVM su HDD con BBU RAID: cache=writeback
# LVM su SSD senza BBU: cache=writethrough o none
# NFS: cache=none
# Local directory (qcow2): cache=writeback con cautela
```

### Impatto della Cache sulle Prestazioni

```bash
# Test con diverse modalita di cache (usando fio dentro la VM)

# Test con cache=none (baseline)
fio --name=test --ioengine=libaio --direct=1 --bs=4k \
    --rw=randwrite --size=1G --numjobs=4 --runtime=30 \
    --group_reporting --filename=/tmp/fiotest

# Confrontare i risultati IOPS e latenza tra le diverse modalita
# Tipicamente:
# unsafe > writeback > none > writethrough > directsync
```

### io_uring e iothread

```bash
# Abilitare io_uring per migliori prestazioni (Proxmox 7+)
qm set <vmid> -scsi0 local-lvm:vm-100-disk-0,size=50G,iothread=1,aio=io_uring

# Oppure per aio native (buon default):
qm set <vmid> -scsi0 local-lvm:vm-100-disk-0,size=50G,iothread=1,aio=native

# Verificare che iothread sia supportato con il controller:
# Richiede scsihw=virtio-scsi-single per iothread per disco
qm set <vmid> -scsihw virtio-scsi-single
```

---

## VirtIO vs IDE: Gap di Prestazioni {#virtio-vs-ide}

### Confronto Prestazioni

Il gap di prestazioni tra VirtIO e IDE/SATA puo essere molto significativo:

| Operazione | IDE | SATA | VirtIO Block | VirtIO SCSI |
|---|---|---|---|---|
| Random Read 4K IOPS | 3,000-5,000 | 5,000-8,000 | 30,000-80,000 | 30,000-80,000 |
| Random Write 4K IOPS | 2,000-4,000 | 4,000-6,000 | 25,000-60,000 | 25,000-60,000 |
| Sequential Read MB/s | 100-200 | 200-400 | 500-2,000+ | 500-2,000+ |
| Sequential Write MB/s | 80-150 | 150-300 | 400-1,500+ | 400-1,500+ |
| CPU Overhead | Alto | Medio | Basso | Basso |
| Queue Depth Max | 1 | 32 | 256 | 256 |

### Migrazione da IDE/SATA a VirtIO

```bash
# 1. Verificare che i driver VirtIO siano installati nel guest
# 2. Spegnere la VM
qm stop <vmid>

# 3. Cambiare il controller e il bus del disco
# Da IDE:
qm set <vmid> -delete ide0
qm set <vmid> -scsihw virtio-scsi-single
qm set <vmid> -scsi0 local-lvm:vm-<vmid>-disk-0,size=50G,iothread=1
qm set <vmid> -boot order=scsi0

# Da SATA:
qm set <vmid> -delete sata0
qm set <vmid> -scsihw virtio-scsi-single
qm set <vmid> -scsi0 local-lvm:vm-<vmid>-disk-0,size=50G,iothread=1
qm set <vmid> -boot order=scsi0

# 4. Avviare e verificare
qm start <vmid>
```

### VirtIO SCSI vs VirtIO Block

```bash
# VirtIO SCSI (consigliato):
# - Supporta SCSI commands (TRIM/UNMAP, SCSI reservation)
# - Supporta piu dischi per controller
# - Supporta iothread
# - Hot-plug/unplug dei dischi
qm set <vmid> -scsihw virtio-scsi-single
qm set <vmid> -scsi0 local-lvm:vm-<vmid>-disk-0,iothread=1,discard=on

# VirtIO Block:
# - Leggermente meno overhead per disco singolo
# - Non supporta SCSI commands
# - Buono per scenari semplici
qm set <vmid> -virtio0 local-lvm:vm-<vmid>-disk-0
```

---

## Ceph Slow Ops {#ceph-slow-ops}

### Diagnostica

```bash
# Verificare lo stato del cluster Ceph
ceph status
ceph health detail

# Identificare slow ops
ceph daemon osd.0 dump_ops_in_flight
ceph daemon osd.0 perf dump | jq '.osd.op_latency'

# Verificare le performance degli OSD
ceph osd perf
# Output:
# osd  commit_latency(ms)  apply_latency(ms)
# 0    1                    2
# 1    45                   87    <- Questo OSD e lento

# Verificare lo stato dei dischi fisici sottostanti
ceph osd tree
smartctl -a /dev/sdX  # Per l'OSD lento
```

### Cause e Soluzioni

**Causa 1: OSD su disco lento o difettoso**

```bash
# Identificare il disco fisico dell'OSD lento
ceph osd find <osd-id>

# Verificare le metriche del disco
smartctl -a /dev/sdX | grep -E "Reallocated|Current_Pending|Offline_Uncorrectable"
iostat -xm /dev/sdX 1 5

# Se il disco e difettoso, sostituirlo:
ceph osd out osd.<id>
# Attendere il rebalancing
ceph osd crush remove osd.<id>
ceph auth del osd.<id>
ceph osd rm osd.<id>
# Sostituire il disco fisico e creare un nuovo OSD
```

**Causa 2: Rete Ceph saturata o con problemi**

```bash
# Ceph necessita di una rete dedicata (cluster network)
# Verificare la configurazione
cat /etc/ceph/ceph.conf | grep network

# [global]
# public_network = 10.0.0.0/24
# cluster_network = 10.0.1.0/24  # Rete separata per replication

# Verificare il traffico sulla rete cluster
iftop -i ens19  # Interfaccia della rete cluster

# Verificare latenza tra i nodi
ping -c 100 <altro-nodo-cluster-ip> | tail -1
# Se la latenza e > 1ms, potrebbe esserci un problema di rete
```

**Causa 3: Numero insufficiente di PG (Placement Groups)**

```bash
# Verificare i PG
ceph osd pool ls detail | grep pg_num

# Calcolare il numero ottimale di PG
# Formula: (OSDs * 100) / replicas / numero_pool
# Esempio: 12 OSD, 3 repliche, 3 pool = (12*100)/3/3 = 133 -> 128 (power of 2)

# Aumentare PG se necessario
ceph osd pool set <pool-name> pg_num 128
ceph osd pool set <pool-name> pgp_num 128
```

**Causa 4: Recovery/Backfill in corso**

```bash
# Verificare se c'e recovery in corso
ceph status | grep -E "recovery|backfill"

# Limitare l'impatto del recovery sulle prestazioni
ceph tell osd.* injectargs --osd-recovery-max-active 1
ceph tell osd.* injectargs --osd-recovery-sleep 0.5
ceph tell osd.* injectargs --osd-max-backfills 1
```

---

## ZFS: ARC e SLOG Issues {#zfs-issues}

### Diagnostica ZFS Performance

```bash
# Stato del pool
zpool status
zpool iostat -v 1 5

# Statistiche ARC (Adaptive Replacement Cache)
arc_summary
# Oppure:
cat /proc/spl/kstat/zfs/arcstats | grep -E "^hits|^misses|^size|^c_max"

# Metriche importanti:
# ARC hit ratio: dovrebbe essere > 90%
# ARC size: quantita di RAM usata per cache
# L2ARC hit ratio: se presente L2ARC (SSD cache)

# Statistiche ZIL/SLOG
zpool iostat -v 1 5 | grep -E "log|special"
```

### Problemi ARC

```bash
# Problema: ARC troppo piccolo
# Verificare il limite ARC
cat /sys/module/zfs/parameters/zfs_arc_max
# In bytes. Se 0, il default e meta della RAM

# Impostare il limite ARC (esempio: 16 GB)
echo "16384000000" > /sys/module/zfs/parameters/zfs_arc_max

# Rendere permanente
echo "options zfs zfs_arc_max=16384000000" > /etc/modprobe.d/zfs.conf
update-initramfs -u

# Problema: ARC hit ratio basso
# Indica che i dati richiesti non sono in cache
# Soluzioni:
# 1. Aumentare la RAM disponibile per ARC
# 2. Aggiungere L2ARC (SSD come cache di secondo livello)
zpool add <pool> cache /dev/sdX

# Problema: troppa RAM consumata da ARC
# Ridurre il limite ARC
echo "8589934592" > /sys/module/zfs/parameters/zfs_arc_max  # 8 GB
```

### Problemi SLOG (ZFS Intent Log)

```bash
# Il SLOG accelera le scritture sincrone
# Senza SLOG, le scritture sincrone vanno direttamente sui dischi del pool

# Verificare se e presente un SLOG
zpool status | grep log

# Aggiungere un SLOG (SSD/NVMe dedicato)
zpool add <pool> log /dev/nvme0n1p1

# Per HA, usare SLOG mirrorato:
zpool add <pool> log mirror /dev/nvme0n1p1 /dev/nvme1n1p1

# Problemi comuni SLOG:
# 1. SLOG pieno: il dispositivo SLOG e troppo piccolo
#    Soluzione: minimo 8-16 GB, enterprise NVMe consigliato
# 2. SLOG lento: SSD consumer con bassa write endurance
#    Soluzione: usare SSD/NVMe con alta write endurance (DWPD > 3)
# 3. SLOG fallito: il dispositivo SLOG si e guastato
zpool status | grep FAULTED
# Rimuovere e sostituire:
zpool remove <pool> <slog-device>
zpool add <pool> log /dev/nuovo-slog
```

### Tuning ZFS per VM

```bash
# Impostazioni ottimali per storage VM
zfs set atime=off <pool>/<dataset>          # Disabilitare access time
zfs set compression=lz4 <pool>/<dataset>     # Compressione LZ4 (quasi gratis)
zfs set sync=standard <pool>/<dataset>       # Default, usa SLOG se presente
zfs set primarycache=all <pool>/<dataset>    # Cache tutto in ARC
zfs set recordsize=64k <pool>/<dataset>      # Buon compromesso per VM
# Per database: recordsize=16k o 8k

# Verificare le impostazioni
zfs get all <pool>/<dataset> | grep -E "atime|compress|sync|primarycache|recordsize"
```

---

## NFS Performance Problems {#nfs-performance}

### Diagnostica NFS

```bash
# Verificare i mount NFS
mount | grep nfs
nfsstat -c  # Statistiche client NFS
nfsstat -s  # Statistiche server NFS (sul server)

# Verificare latenza NFS
time dd if=/dev/zero of=/mnt/nfs-share/testfile bs=1M count=100
time dd if=/mnt/nfs-share/testfile of=/dev/null bs=1M count=100

# Verificare la versione NFS
nfsstat -m
# NFSv4.1/4.2 e consigliato per prestazioni

# Verificare i parametri di mount
mount | grep nfs
# Opzioni importanti: rw,relatime,vers=4.2,rsize=1048576,wsize=1048576,
#                     hard,proto=tcp,timeo=600,retrans=2
```

### Ottimizzazione NFS

```bash
# Opzioni di mount ottimali per storage VM
# In /etc/fstab:
nfs-server:/export/vmdata /mnt/pve/nfs-vm nfs4 \
    rsize=1048576,wsize=1048576,hard,intr,noatime,proto=tcp,async 0 0

# Oppure nella configurazione Proxmox storage:
# In /etc/pve/storage.cfg:
# nfs: nfs-storage
#     export /export/vmdata
#     path /mnt/pve/nfs-vm
#     server nfs-server
#     content images,iso,vztmpl,backup
#     options vers=4.2,rsize=1048576,wsize=1048576

# Sul server NFS: tuning kernel
# Aumentare i thread NFS
echo 32 > /proc/fs/nfsd/threads
# Rendere permanente: modificare /etc/default/nfs-kernel-server
# RPCNFSDCOUNT=32

# Tuning NFS server
cat > /etc/sysctl.d/nfs-tuning.conf << 'EOF'
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.netdev_max_backlog = 30000
sunrpc.tcp_slot_table_entries = 128
EOF
sysctl -p /etc/sysctl.d/nfs-tuning.conf
```

---

## Benchmarking con fio {#benchmarking-fio}

### Installazione fio

```bash
# Debian/Ubuntu
apt install fio

# RHEL/CentOS
yum install fio

# Windows (download da GitHub)
# https://github.com/axboe/fio/releases
```

### Test Standard per VM

```bash
# === TEST 1: Random Read 4K (simula database read) ===
fio --name=randread \
    --ioengine=libaio \
    --direct=1 \
    --bs=4k \
    --rw=randread \
    --size=4G \
    --numjobs=4 \
    --runtime=60 \
    --group_reporting \
    --filename=/tmp/fio-test-file

# === TEST 2: Random Write 4K (simula database write) ===
fio --name=randwrite \
    --ioengine=libaio \
    --direct=1 \
    --bs=4k \
    --rw=randwrite \
    --size=4G \
    --numjobs=4 \
    --runtime=60 \
    --group_reporting \
    --filename=/tmp/fio-test-file

# === TEST 3: Sequential Read (simula backup/lettura file grandi) ===
fio --name=seqread \
    --ioengine=libaio \
    --direct=1 \
    --bs=1M \
    --rw=read \
    --size=4G \
    --numjobs=1 \
    --runtime=60 \
    --group_reporting \
    --filename=/tmp/fio-test-file

# === TEST 4: Sequential Write (simula scrittura log/backup) ===
fio --name=seqwrite \
    --ioengine=libaio \
    --direct=1 \
    --bs=1M \
    --rw=write \
    --size=4G \
    --numjobs=1 \
    --runtime=60 \
    --group_reporting \
    --filename=/tmp/fio-test-file

# === TEST 5: Mixed Read/Write 70/30 (simula workload tipico) ===
fio --name=mixed \
    --ioengine=libaio \
    --direct=1 \
    --bs=4k \
    --rw=randrw \
    --rwmixread=70 \
    --size=4G \
    --numjobs=4 \
    --runtime=60 \
    --group_reporting \
    --filename=/tmp/fio-test-file

# Pulizia
rm -f /tmp/fio-test-file
```

### Interpretazione Risultati fio

```
# Esempio output fio:
# randwrite: (groupid=0, jobs=4): err= 0: pid=1234
#   write: IOPS=45.2k, BW=176MiB/s (185MB/s)
#     slat (usec): min=1, max=1500, avg=3.50, stdev=5.20
#     clat (usec): min=20, max=25000, avg=85.30, stdev=120.50
#      lat (usec): min=22, max=25500, avg=88.80, stdev=122.30
#     clat percentiles (usec):
#      |  1.00th=[   35],  5.00th=[   42], 10.00th=[   48],
#      | 20.00th=[   56], 30.00th=[   63], 40.00th=[   70],
#      | 50.00th=[   78], 60.00th=[   86], 70.00th=[   95],
#      | 80.00th=[  108], 90.00th=[  133], 95.00th=[  165],
#      | 99.00th=[  310], 99.50th=[  420], 99.90th=[ 1500],
#      | 99.95th=[ 2500], 99.99th=[ 5000]

# Metriche chiave:
# IOPS: 45,200 (operazioni al secondo)
# BW: 176 MiB/s (throughput)
# clat avg: 85.30 usec (latenza media di completamento)
# clat p99: 310 usec (latenza al 99esimo percentile)
# slat: submission latency (tempo per inviare l'I/O al kernel)
# clat: completion latency (tempo dal kernel al completamento)
# lat: latenza totale (slat + clat)
```

### Script di Benchmark Completo

```bash
#!/bin/bash
# storage-benchmark.sh
# Eseguire dentro la VM per confronto pre/post migrazione

TESTDIR=${1:-/tmp}
TESTFILE="$TESTDIR/fio-benchmark"
RESULTS="$TESTDIR/benchmark-results-$(date +%Y%m%d-%H%M%S).txt"

echo "=== Storage Benchmark ===" | tee $RESULTS
echo "Data: $(date)" | tee -a $RESULTS
echo "Directory test: $TESTDIR" | tee -a $RESULTS
echo "" | tee -a $RESULTS

for TEST in "randread" "randwrite" "read" "write" "randrw"; do
    BS="4k"
    EXTRA=""
    if [ "$TEST" = "read" ] || [ "$TEST" = "write" ]; then
        BS="1M"
    fi
    if [ "$TEST" = "randrw" ]; then
        EXTRA="--rwmixread=70"
    fi

    echo "--- Test: $TEST (bs=$BS) ---" | tee -a $RESULTS
    fio --name=$TEST \
        --ioengine=libaio \
        --direct=1 \
        --bs=$BS \
        --rw=$TEST \
        --size=2G \
        --numjobs=4 \
        --runtime=30 \
        --group_reporting \
        --filename=$TESTFILE \
        $EXTRA 2>&1 | grep -E "IOPS|BW|lat.*avg" | tee -a $RESULTS
    echo "" | tee -a $RESULTS
done

rm -f $TESTFILE
echo "Risultati salvati in: $RESULTS"
```

---

## Identificare i Bottleneck {#identificare-bottleneck}

### iostat - Analisi I/O dei Dischi

```bash
# Monitoraggio continuo
iostat -xmz 2

# Interpretazione colonne principali:
# rrqm/s, wrqm/s: richieste merge al secondo (I/O merging)
# r/s, w/s: IOPS lettura/scrittura
# rMB/s, wMB/s: throughput lettura/scrittura
# avgrq-sz: dimensione media delle richieste (in settori)
# avgqu-sz: lunghezza media della coda I/O
# await: latenza media totale (ms)
# r_await, w_await: latenza media lettura/scrittura
# svctm: service time (deprecato, non affidabile)
# %util: percentuale di utilizzo del disco

# Regole d'oro:
# %util > 80%: disco probabilmente saturato
# await > 10ms su SSD: possibile problema
# avgqu-sz > 1: coda di I/O presente
```

### dstat - Monitoraggio Risorse Integrato

```bash
# Installazione
apt install dstat  # Debian/Ubuntu

# Monitoraggio completo
dstat -cdnmgy --disk-util 5

# Solo I/O disco con dettaglio
dstat -D sda,sdb --disk-tps --disk-util 2

# CPU + Disco + Rete
dstat -c -d -n 2
```

### iotop - I/O per Processo

```bash
# Mostrare solo processi con I/O attivo
iotop -o

# Ordinare per I/O in scrittura
iotop -o -a

# Batch mode (per scripting)
iotop -b -o -n 5 --delay=2

# Identificare quale VM genera piu I/O
# I processi kvm/qemu mostrano il VMID nel nome
iotop -o | grep kvm
```

### blktrace - Tracciamento I/O Dettagliato

```bash
# Per analisi approfondita a livello di blocco
blktrace -d /dev/sda -o /tmp/sda-trace &
# Attendere 30 secondi
kill %1
blkparse -i /tmp/sda-trace -d /tmp/sda-trace.bin
btt -i /tmp/sda-trace.bin

# Mostra latenze dettagliate per ogni fase dell'I/O:
# Q2Q: tempo tra richieste
# D2C: tempo dal dispatch al completamento
# Q2C: tempo totale dalla richiesta al completamento
```

---

## Tuning per Storage Backend {#tuning-per-backend}

### LVM-Thin

```bash
# Verificare lo spazio disponibile
lvs -a -o+seg_monitor
# Monitorare l'uso del thin pool
lvs -o lv_name,data_percent,metadata_percent <vg>/<thin-pool>

# Tuning LVM-Thin
# Aumentare le dimensioni del metadata pool se necessario
lvextend --poolmetadatasize +1G <vg>/<thin-pool>

# Abilitare il TRIM/discard
qm set <vmid> -scsi0 local-lvm:vm-<vmid>-disk-0,discard=on
# Nel guest Linux:
fstrim -av

# Monitorare la frammentazione
# Controllare la segmentazione delle LV
lvs --segments <vg>/<lv-name>
```

### ZFS

```bash
# Tuning ZFS per VM workload
# recordsize: per database usare 8k-16k, per file generici 128k
zfs set recordsize=64k rpool/data

# Compressione (quasi sempre vantaggiosa)
zfs set compression=lz4 rpool/data

# ARC tuning
echo "options zfs zfs_arc_max=17179869184" >> /etc/modprobe.d/zfs.conf  # 16GB

# TRIM automatico
zpool set autotrim=on rpool

# Monitorare la frammentazione
zpool status -v
zpool get fragmentation rpool
# Frammentazione > 50% inizia a degradare le performance
```

### Ceph RBD

```bash
# Tuning pool Ceph per VM
ceph osd pool set <pool> size 3           # Repliche (default)
ceph osd pool set <pool> min_size 2       # Minimo per I/O
ceph osd pool set <pool> pg_num 128       # Placement groups

# Abilitare RBD cache (nel client)
# In /etc/ceph/ceph.conf:
[client]
rbd_cache = true
rbd_cache_size = 67108864         # 64 MB
rbd_cache_max_dirty = 50331648    # 48 MB
rbd_cache_target_dirty = 33554432 # 32 MB
rbd_cache_writethrough_until_flush = true

# TRIM/discard per Ceph
qm set <vmid> -scsi0 ceph-pool:vm-<vmid>-disk-0,discard=on

# Monitorare le prestazioni RBD
rbd perf image iolatency <pool>/<image>
rbd perf image iops <pool>/<image>
```

---

## Confronto Prestazioni Pre/Post Migrazione {#confronto-prestazioni}

### Metodologia di Confronto

Per un confronto valido, e necessario eseguire gli stessi test con gli stessi parametri su entrambe le piattaforme.

```bash
# 1. PRE-MIGRAZIONE (su VMware)
# Eseguire il benchmark dentro la VM
./storage-benchmark.sh /tmp

# 2. POST-MIGRAZIONE (su Proxmox)
# Eseguire lo stesso benchmark
./storage-benchmark.sh /tmp

# 3. Confrontare i risultati
# Creare un report di confronto
```

### Template Report di Confronto

```
=== Report Confronto Prestazioni Storage ===
VM: [nome-vm]
Data Test VMware: [data]
Data Test Proxmox: [data]

Configurazione VMware:
- Storage: VMFS 6 su [tipo-disco]
- Controller: [PVSCSI/LSI]
- Datastore: [nome]

Configurazione Proxmox:
- Storage: [ZFS/LVM/Ceph] su [tipo-disco]
- Controller: [VirtIO SCSI/VirtIO Block]
- Cache: [none/writeback/writethrough]

Risultati:
                    VMware      Proxmox     Delta
Random Read 4K:     [IOPS]      [IOPS]      [+/-  %]
Random Write 4K:    [IOPS]      [IOPS]      [+/-  %]
Seq Read:           [MB/s]      [MB/s]      [+/-  %]
Seq Write:          [MB/s]      [MB/s]      [+/-  %]
Mixed 70/30:        [IOPS]      [IOPS]      [+/-  %]
Latenza Read p99:   [usec]      [usec]      [+/-  %]
Latenza Write p99:  [usec]      [usec]      [+/-  %]

Note:
- [Eventuali anomalie o osservazioni]
- [Azioni correttive se le prestazioni sono peggiori]
```

### Valori Accettabili di Degradazione

Una leggera differenza nelle prestazioni e normale e accettabile. Valori di riferimento:

- **Differenza < 5%**: Eccellente, nessuna azione necessaria
- **Differenza 5-15%**: Accettabile, verificare configurazione cache e controller
- **Differenza 15-30%**: Richiede investigazione, possibile problema di configurazione
- **Differenza > 30%**: Problema significativo, richiede tuning o cambio di approccio

Se le prestazioni sono significativamente peggiori, verificare in ordine:
1. Controller disco (VirtIO vs IDE/SATA)
2. Modalita cache
3. Formato disco (raw vs qcow2)
4. Storage backend (tipo e configurazione)
5. I/O scheduler dell'host
6. Risorse condivise con altre VM

---

## Letture primarie consigliate

- iostat(1) — sysstat. https://man7.org/linux/man-pages/man1/iostat.1.html (retrieved 2026-04-27).
- fio — Flexible I/O Tester. https://fio.readthedocs.io/en/latest/ (retrieved 2026-04-27).
- OpenZFS — Performance Tuning. https://openzfs.github.io/openzfs-docs/Performance%20and%20Tuning/Workload%20Tuning.html (retrieved 2026-04-27).
- Ceph — Troubleshooting OSDs. https://docs.ceph.com/en/latest/rados/troubleshooting/troubleshooting-osd/ (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 09.3 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-high-io-workloads.md`: fundamentals high-I/O.
- Modulo 03.x — `../03-STORAGE-AVANZATO-PROXMOX/`: backend storage details.
- Modulo 13.x — `../13-MONITORAGGIO-E-OTTIMIZZAZIONE/zabbix-monitoraggio-proxmox.md`: monitoring per detection precoce.
