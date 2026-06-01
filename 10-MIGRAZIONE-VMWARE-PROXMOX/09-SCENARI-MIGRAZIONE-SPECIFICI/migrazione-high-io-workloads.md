# Migrazione di Workload ad Alto I/O da VMware a Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 09.3 (segue 09.2 DB-specifico, generalizza ai workload high-IOPS, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 02 (architettura Proxmox: storage backend, controller dischi, virtio-scsi); modulo 03 (LVM-thin, ZFS, Ceph deep-dive); modulo 04 (linux-bridge, jumbo frames, bonding); modulo 08 (conversione dischi, cache modes, raw vs qcow2); concetti fondamentali di scheduling I/O Linux (mq-deadline, none, BFQ).
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. costruire un **profilo I/O di riferimento** del workload sorgente VMware combinando `esxtop` (DAVG/cmd, GAVG/cmd, KAVG/cmd), `vscsiStats` (istogramma block size + outstanding I/O) e metriche dall'interno del guest (`iostat -xdz`, `iotop`, `atop`); convertire il profilo in budget di prestazioni misurabili (IOPS, throughput, p99) per la VM Proxmox;
> 2. scegliere il **backend storage Proxmox** appropriato in base al budget I/O: local NVMe + LVM-thin per OLTP estremo (200K-500K IOPS, < 0.3 ms), local NVMe + ZFS mirror per OLTP con protezione (150K-400K IOPS, 0.1-0.3 ms), Ceph SSD/NVMe per HA (20K-150K IOPS, 0.5-3 ms), iSCSI all-flash per integrazione SAN (50K-200K IOPS), NFS per file server (5K-30K IOPS); calcolare l'overhead di rete + replica per Ceph (replica 3 su 10 GbE → ~400 MB/s teorico per client);
> 3. configurare la **VM ottimale per high-I/O**: `virtio-scsi-single` (un controller per disco, no contention iothread), `iothread=1` per ogni disco, `cache=none` (mai `writeback` in produzione), formato `raw` su LVM (mai `qcow2` per high-IOPS), `--balloon 0`, `--cpu host`, `--numa 1` con `--numa0 cpus=...,hostnodes=...,policy=bind`;
> 4. allineare la VM al **NUMA node** corretto (verificare con `numactl --hardware` e `cat /sys/block/nvme0n1/device/numa_node`), pinnare il processo QEMU + iothread ai core locali, e quantificare il guadagno: ~90% in piu di latenza per accesso remoto vs locale (tipicamente 80 ns vs 150 ns);
> 5. configurare la **rete di storage** per Ceph/iSCSI/NFS: NIC dedicate con MTU 9000, bonding LACP (`bond-mode 802.3ad` + `xmit-hash-policy layer3+4`), validazione end-to-end con `ping -M do -s 8972` (no fragmentation);
> 6. tuning **kernel I/O**: scheduler `none` per NVMe, `mq-deadline` per SSD SATA/HDD; `vm.swappiness = 10`, `vm.dirty_ratio = 10`, `vm.dirty_background_ratio = 5` per workload DB; THP `never` per database; `vm.vfs_cache_pressure = 50`; `read_ahead_kb` e `nr_requests` per workload sequenziali;
> 7. eseguire **benchmark fio comparativi** (random 8K R/W mix 70/30, sequential 1M R/W, latency single-thread 4K) su VMware *e* Proxmox con profili identici, parsare l'output JSON, e applicare i criteri di accettazione: IOPS Proxmox ≥ 90% VMware (ottimale ≥ 100%), latenza p99 ≤ 120% VMware (ottimale ≤ 100%);
> 8. monitorare post-migrazione con `iostat -xdmz`, `iotop -b -o`, `atop`, e Prometheus + node_exporter; riconoscere i pattern di latency spike periodici (writeback dirty pages, ZFS scrub, Ceph deep-scrub, CPU steal time elevato) e applicare mitigazioni mirate.
> **Tempo stimato:** lettura 90-120 min · lab 480-720 min (per profilare un workload reale, configurare il backend, eseguire benchmark comparativi)
> **Livello:** competent → expert (Dreyfus 3 → 4 → 5 sui temi di tuning kernel/NUMA)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; QEMU/KVM 7.x → 10.x; kernel 6.1/6.6/6.12 LTS; ZFS 2.1/2.2/2.3; Ceph Quincy 17.2 / Reef 18.2 / Squid 19.2; fio 3.x.

## Mappa concettuale

```
+============================================================+
|     Workload high-I/O — pipeline di scelta e validazione   |
+============================================================+
|                                                            |
|   1. PROFILA IL WORKLOAD VMware                            |
|      esxtop -b -d 5 -n 720      DAVG/GAVG/KAVG             |
|      vscsiStats -p all          istogramma block size      |
|      iostat -xdm 5 720          dal guest, baseline        |
|      atop -w baseline.raw       trend nel tempo            |
|      → IOPS, MB/s, p99 latenza                             |
|                                                            |
|   2. CLASSIFICA E DECIDI BACKEND                           |
|      Latency-bound  ─► local NVMe LVM-thin / ZFS mirror    |
|      Throughput-bnd ─► local NVMe / Ceph NVMe (25GbE+)     |
|      HA-required    ─► Ceph (accetta latenza superiore)    |
|      File serving   ─► NFS / iSCSI                         |
|                                                            |
|      Confronto IOPS/latency tipici (4K random):            |
|        local NVMe LVM-thin   200-500K IOPS  / < 0.1ms      |
|        local NVMe ZFS mirror 150-400K IOPS  / 0.1-0.3ms    |
|        Ceph NVMe             50-150K IOPS   / 0.3-1ms      |
|        Ceph SSD              20-80K IOPS    / 0.5-3ms      |
|        iSCSI all-flash       50-200K IOPS   / 0.2-1ms      |
|        NFS NAS               5-30K IOPS     / 1-10ms       |
|                                                            |
|   3. CONFIGURA VM                                          |
|      --scsihw virtio-scsi-single                           |
|      scsi*: iothread=1, cache=none, format=raw, discard=on |
|      --balloon 0    (no swap del DB buffer pool)           |
|      --cpu host     (SIMD, AVX, AES-NI, CRC32)             |
|      --numa 1 + numa0 cpus=...,hostnodes=...,policy=bind   |
|      separa OS / dati / WAL su disk fisici differenti      |
|                                                            |
|   4. CPU PIN + NUMA ALIGN                                  |
|      cat /sys/block/<dev>/device/numa_node                 |
|      numactl --hardware                                    |
|      taskset -apc 0-7 $QEMU_PID  (post-start hookscript)   |
|      ~90% piu latenza accesso remoto NUMA                  |
|                                                            |
|   5. KERNEL TUNING                                         |
|      I/O scheduler:  NVMe=none, SSD=mq-deadline            |
|      vm.swappiness=10                                      |
|      vm.dirty_ratio=10, vm.dirty_background_ratio=5        |
|      THP=never (per DB)                                    |
|      udev rule per persistenza                             |
|                                                            |
|   6. RETE STORAGE (per Ceph/iSCSI/NFS)                     |
|      NIC dedicate, MTU 9000                                |
|      bond LACP layer3+4                                    |
|      ping -M do -s 8972 per validare jumbo end-to-end      |
|                                                            |
|   7. BENCHMARK fio                                         |
|      profilo 1: random 8K r/w mix 70/30, qd=32, jobs=8     |
|      profilo 2: seq 1M r/w, qd=16, jobs=4                  |
|      profilo 3: latency single 4K, qd=1, jobs=1            |
|      criterio go/no-go: IOPS Proxmox >= 90% VMware,        |
|                          p99 <= 120% VMware                |
|                                                            |
|   8. MONITORA + ALLARMI                                    |
|      iostat / iotop / atop / Prometheus node_exporter      |
|      alert: latency p99 > soglia, %util > 95%, IOPS drop   |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Senza un profilo I/O VMware non puoi validare il successo.** "Le prestazioni sembrano OK" non e una metrica. IOPS medi, latenza p99, block size dominante: questi vanno catturati prima del cutover, altrimenti non saprai mai se Proxmox ti ha portato a un livello inferiore di servizio.
2. **Lo storage backend e il fattore principale; la VM e il fattore secondario.** Una VM perfettamente configurata su Ceph SSD non raggiungera mai i 200K IOPS di un local NVMe. La domanda iniziale e: che livello di prestazioni mi serve, e che backend lo permette? La VM si configura *dopo* aver scelto il backend.
3. **`cache=writeback` "veloce" e una bomba a tempo.** I benchmark sembrano migliori del 30-40%, ma il primo crash o power loss del nodo Proxmox produce dati corrotti che il guest pensava fossero su disco. Nessun motore di DB sopravvive a questo. Per workload critici: `cache=none` o `cache=directsync`, fine della discussione.
4. **NUMA e PCIe locality non sono "ottimizzazioni avanzate", sono la base.** Un NVMe collegato al socket 1 e una VM pinnata al socket 0 = ~90% di latenza in piu su ogni operazione. La GUI di Proxmox non rivela queste cose: si verifica con `numactl --hardware` + `lspci -vv` + `cat /sys/block/.../device/numa_node`.
5. **Ceph eccelle in scalabilita e HA, non in prestazioni single-VM.** Replica 3 su 10 GbE → throughput per-client capped a ~400 MB/s. Per workload sequenziali pesanti (analytics, video, backup), Ceph e una scelta architetturale, non di performance: si paga in prestazioni cio che si guadagna in resilienza.
6. **`fio` con gli stessi profili e l'unico arbitro affidabile.** Ogni metrica raccolta su VMware deve avere il suo gemello su Proxmox. Profili diversi = confronto privo di significato. Il go/no-go della migrazione si decide su numeri, non su impressioni.
7. **I latency spike sono quasi sempre kernel writeback o background ops.** `vm.dirty_ratio=10` riduce dramaticamente il rischio. ZFS scrub e Ceph deep-scrub vanno *schedulati* in finestra di basso carico, non lasciati al default.

## Indice
- [Panoramica](#panoramica)
- [Caratteristiche dei Workload ad Alto I/O](#caratteristiche-dei-workload-ad-alto-io)
- [Profilazione I/O Pre-Migrazione su VMware](#profilazione-io-pre-migrazione-su-vmware)
- [Selezione del Backend Storage su Proxmox](#selezione-del-backend-storage-su-proxmox)
- [Configurazione VM Ottimale per Alto I/O](#configurazione-vm-ottimale-per-alto-io)
- [CPU Pinning e NUMA Awareness](#cpu-pinning-e-numa-awareness)
- [Configurazione Rete per Storage: 10GbE e Jumbo Frames](#configurazione-rete-per-storage-10gbe-e-jumbo-frames)
- [Kernel Tuning per I/O Intensive Workloads](#kernel-tuning-per-io-intensive-workloads)
- [Benchmarking con fio: Confronto VMware vs Proxmox](#benchmarking-con-fio-confronto-vmware-vs-proxmox)
- [Monitoraggio Post-Migrazione](#monitoraggio-post-migrazione)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

I workload ad alto I/O rappresentano la categoria di macchine virtuali più sensibile alle prestazioni dello storage e alla configurazione dell'hypervisor. Database transazionali, sistemi di analytics in tempo reale, server di file serving ad alta concorrenza, piattaforme di video editing e rendering, e applicazioni di machine learning con accesso intensivo ai dataset sono tutti esempi di carichi di lavoro in cui le prestazioni I/O determinano direttamente le prestazioni percepite dall'utente finale e la capacità di throughput del sistema.

La migrazione di questi workload da VMware vSphere a Proxmox VE richiede una pianificazione attenta perché le due piattaforme gestiscono lo storage virtualizzato in modo fondamentalmente diverso. VMware utilizza VMFS o vSAN come layer di astrazione dello storage, con il driver PVSCSI ottimizzato per il proprio hypervisor. Proxmox VE, basato su KVM/QEMU, offre una gamma più ampia di backend storage (LVM, ZFS, Ceph, NFS, iSCSI) e di controller virtuali (VirtIO SCSI, VirtIO Block), ciascuno con caratteristiche di prestazione distinte. La scelta sbagliata del backend o della configurazione può risultare in una degradazione significativa delle prestazioni, mentre la scelta corretta può spesso eguagliare o superare le prestazioni VMware.

Questo documento fornisce una metodologia completa per la migrazione dei workload ad alto I/O: dalla profilazione delle prestazioni sull'ambiente VMware esistente, alla selezione e configurazione ottimale dello storage su Proxmox, fino al benchmarking comparativo e al monitoraggio continuo post-migrazione. L'obiettivo è garantire che le prestazioni I/O sulla nuova piattaforma siano pari o superiori a quelle dell'ambiente originale.

---

## Caratteristiche dei Workload ad Alto I/O

### Metriche Fondamentali

| Metrica | Definizione | Tipico per DB | Tipico per File Server | Tipico per Analytics |
|---|---|---|---|---|
| IOPS | Operazioni I/O al secondo | 10K-100K+ | 1K-10K | 5K-50K |
| Throughput | MB/s sequenziale | 200-500 MB/s | 500-2000 MB/s | 1000-5000 MB/s |
| Latenza media | Tempo medio per operazione | < 1ms | < 5ms | < 2ms |
| Latenza p99 | 99° percentile latenza | < 5ms | < 20ms | < 10ms |
| Profilo I/O | Rapporto read/write | 70/30 | 80/20 | 90/10 |
| Block size | Dimensione tipica dell'operazione | 4K-8K | 64K-1M | 128K-1M |
| Pattern | Sequenziale vs random | Random | Misto | Sequenziale |
| Queue depth | Profondità della coda I/O | 16-64 | 4-16 | 32-128 |

### Classificazione dei Workload

```
                    Latenza sensibile ◄────────────────────► Throughput sensibile
                    (piccoli blocchi, random)                (grandi blocchi, seq)

OLTP Database       ████████████░░░░░░░░
(MySQL, PostgreSQL)

Key-Value Store     ██████████░░░░░░░░░░
(Redis persistent)

OLAP / Analytics    ░░░░░░░░░████████████
(ClickHouse, Spark)

File Server         ░░░░░░████████░░░░░░
(SMB, NFS)

Video Editing       ░░░░░░░░░░░█████████
(Rendering)

Logging/SIEM        ░░░░░░░░░░████████░░
(Elasticsearch)

Backup Server       ░░░░░░░░░░░░████████
(Veeam, Bacula)
```

---

## Profilazione I/O Pre-Migrazione su VMware

### esxtop: Raccolta delle Metriche I/O

`esxtop` è lo strumento nativo di VMware per la profilazione delle prestazioni I/O a livello hypervisor. È essenziale raccogliere queste metriche per stabilire il baseline.

```bash
# Connettersi via SSH all'host ESXi

# Modalità interattiva: premere 'u' per disk device, 'd' per disk adapter
esxtop

# Modalità batch per raccolta dati nel tempo (ogni 5 secondi per 1 ora)
esxtop -b -d 5 -n 720 > /tmp/esxtop_io_$(date +%Y%m%d).csv

# Metriche chiave da osservare:
# CMDS/s    = IOPS totali (read + write)
# READS/s   = IOPS in lettura
# WRITES/s  = IOPS in scrittura
# MBREAD/s  = Throughput lettura in MB/s
# MBWRTN/s  = Throughput scrittura in MB/s
# DAVG/cmd  = Latenza media del dispositivo (ms) - la più importante
# KAVG/cmd  = Latenza media del kernel VMware (ms)
# GAVG/cmd  = Latenza totale guest-percepita (ms)
# QAVG/cmd  = Latenza dovuta alla coda (ms)
```

### vscsiStats: Profilo Dettagliato degli I/O

```bash
# Abilitare il tracking dettagliato per una VM specifica
VMID=$(vim-cmd vmsvc/getallvms | grep "VM-NAME" | awk '{print $1}')
vscsiStats -s -w $VMID

# Raccogliere dati per almeno 30 minuti durante il carico di picco
sleep 1800

# Generare il report con l'istogramma delle dimensioni I/O
vscsiStats -p all -w $VMID > /tmp/vscsi_histogram.txt

# Fermare il tracking
vscsiStats -x -w $VMID
```

L'output di `vscsiStats` fornisce la distribuzione delle dimensioni dei blocchi I/O, che è fondamentale per configurare correttamente lo storage su Proxmox (allineamento, block size del filesystem, pool record size di ZFS).

### Raccolta Metriche dall'Interno della VM

```bash
# Linux: iostat (sysstat package)
iostat -xdm 5 720 > /tmp/iostat_baseline.txt

# Metriche chiave:
# r/s, w/s       = IOPS read/write
# rMB/s, wMB/s   = Throughput
# r_await, w_await = Latenza media (ms)
# aqu-sz         = Queue depth media
# %util          = Percentuale di utilizzo del device

# Linux: iotop (per identificare i processi I/O intensive)
iotop -b -d 5 -t -o --iter=720 > /tmp/iotop_baseline.txt

# Linux: atop con registrazione
atop -w /tmp/atop_baseline.raw 5 720
# Replay successivo:
atop -r /tmp/atop_baseline.raw
```

### Creazione del Profilo I/O di Riferimento

Raccogliere i dati durante i seguenti periodi:
1. **Carico normale** (giorno lavorativo tipico, 8 ore)
2. **Carico di picco** (momento di massimo utilizzo, 2-4 ore)
3. **Operazioni batch** (backup, manutenzione notturna, 4-8 ore)

Sintetizzare in una tabella di riferimento:

```
PROFILO I/O: VM-DATABASE-PROD
Periodo: 07-11 Aprile 2026

                    Media     Picco     p99
IOPS Read:          12,340    45,200    38,500
IOPS Write:          5,670    22,100    18,300
Throughput Read:     48 MB/s  176 MB/s  150 MB/s
Throughput Write:    22 MB/s   86 MB/s   72 MB/s
Latenza Read:        0.4 ms   1.2 ms    2.8 ms
Latenza Write:       0.6 ms   1.8 ms    4.2 ms
Block Size medio:    8 KB
Pattern:             85% random, 15% sequenziale
Queue Depth media:   24
```

Questo profilo è il target da raggiungere o superare su Proxmox.

---

## Selezione del Backend Storage su Proxmox

### Confronto dei Backend Storage

| Backend | IOPS Random 4K | Throughput Seq | Latenza | Ridondanza | Complessità | Caso d'Uso |
|---|---|---|---|---|---|---|
| Local NVMe + LVM | 200K-500K+ | 3000+ MB/s | < 0.1ms | Nessuna | Bassa | DB critici, massime perf |
| Local SSD + LVM | 50K-100K | 500-1500 MB/s | 0.1-0.5ms | Nessuna | Bassa | DB, app general purpose |
| Local NVMe + ZFS | 150K-400K | 2000+ MB/s | 0.1-0.3ms | Mirror/RAIDZ | Media | DB con protezione dati |
| Ceph (SSD OSDs) | 20K-80K | 200-800 MB/s | 0.5-3ms | Replicato | Alta | Cloud-like, HA, scalabile |
| Ceph (NVMe OSDs) | 50K-150K | 500-2000 MB/s | 0.3-1ms | Replicato | Alta | HA con buone prestazioni |
| iSCSI (all-flash SAN) | 50K-200K | 500-3000 MB/s | 0.2-1ms | Dipende dalla SAN | Media | Infrastrutture esistenti |
| NFS (NAS) | 5K-30K | 100-500 MB/s | 1-10ms | Dipende dal NAS | Bassa | File server, non per DB |

### Diagramma Decisionale

```
                    ┌──────────────────────────┐
                    │ Il workload richiede      │
                    │ > 50K IOPS random 4K?     │
                    └────────────┬─────────────┘
                           ┌─────┴─────┐
                          Sì           No
                           │            │
                           ▼            ▼
                    ┌──────────┐  ┌──────────────────┐
                    │ Richiede │  │ Richiede HA      │
                    │ HA?      │  │ integrato?       │
                    └────┬─────┘  └────────┬─────────┘
                    ┌────┴────┐       ┌────┴────┐
                   Sì        No     Sì        No
                    │         │      │         │
                    ▼         ▼      ▼         ▼
              ┌──────────┐ ┌─────┐ ┌─────┐ ┌──────────┐
              │ NVMe SAN │ │Local│ │Ceph │ │ Local    │
              │ iSCSI    │ │NVMe │ │ SSD │ │ SSD/LVM  │
              │ o Ceph   │ │ LVM │ │     │ │ o ZFS    │
              │ NVMe     │ │     │ │     │ │          │
              └──────────┘ └─────┘ └─────┘ └──────────┘
```

### Local NVMe con LVM-thin

La configurazione con le prestazioni più elevate. Adatta per database OLTP e workload che richiedono la latenza più bassa possibile.

```bash
# Creare un volume group su NVMe
pvcreate /dev/nvme0n1
vgcreate nvme-vg /dev/nvme0n1

# Creare un thin pool (ottimo per thin provisioning)
lvcreate -l 95%VG --thinpool nvme-thin nvme-vg

# Aggiungere lo storage a Proxmox
pvesm add lvmthin nvme-lvm --vgname nvme-vg --thinpool nvme-thin --content images,rootdir
```

### ZFS su NVMe: Prestazioni con Protezione

```bash
# Mirror ZFS su due NVMe (ridondanza + prestazioni lettura)
zpool create -f -o ashift=12 \
  -O atime=off \
  -O compression=lz4 \
  -O recordsize=8K \
  nvme-zfs mirror /dev/nvme0n1 /dev/nvme1n1

# Il recordsize dipende dal workload:
# 8K per database (PostgreSQL default page = 8KB)
# 16K per MySQL/InnoDB (default page = 16KB)
# 128K per file server e workload sequenziali

# Creare il dataset per le VM
zfs create nvme-zfs/vm-data

# Aggiungere a Proxmox
pvesm add zfspool nvme-zfs --pool nvme-zfs/vm-data --content images,rootdir
```

### Ceph con SSD OSDs

Per ambienti che richiedono alta disponibilità integrata e scalabilità:

```bash
# Creare gli OSD su SSD (su ogni nodo del cluster)
ceph-volume lvm create --data /dev/sdb
ceph-volume lvm create --data /dev/sdc

# Creare un pool dedicato per i workload I/O intensive
ceph osd pool create high-io-pool 128 128
ceph osd pool set high-io-pool size 2          # Replica 2 per latenza ridotta
ceph osd pool set high-io-pool min_size 1
ceph osd pool application enable high-io-pool rbd

# Creare una regola CRUSH che forza il placement su SSD
ceph osd crush rule create-replicated ssd-rule default host ssd

# Applicare la regola al pool
ceph osd pool set high-io-pool crush_rule ssd-rule

# Aggiungere a Proxmox
pvesm add rbd ceph-highio --pool high-io-pool --content images
```

---

## Configurazione VM Ottimale per Alto I/O

### Parametri della VM

```bash
qm create 400 \
  --name HIGH-IO-VM \
  --memory 65536 \
  --balloon 0 \
  --cores 16 \
  --sockets 1 \
  --cpu host \
  --numa 1 \
  --scsihw virtio-scsi-single \
  --net0 virtio,bridge=vmbr0 \
  --ostype l26 \
  --agent enabled=1

# Disco OS (storage standard)
qm set 400 --scsi0 local-lvm:50,iothread=1,discard=on

# Disco dati ad alto I/O (storage NVMe)
qm set 400 --scsi1 nvme-lvm:500,iothread=1,cache=none,discard=on

# Disco WAL/log separato (se database)
qm set 400 --scsi2 nvme-lvm:100,iothread=1,cache=none,discard=on
```

### VirtIO SCSI con iothread

Il controller `virtio-scsi-single` crea un controller SCSI dedicato per ogni disco, con un iothread separato. Questo elimina la contesa tra dischi ed è essenziale per workload ad alto I/O.

```
virtio-scsi-pci (singolo controller, multipli dischi) — NON raccomandato per alto I/O
┌─────────────────────────┐
│  VirtIO SCSI Controller │
│  (1 iothread condiviso) │
│    ├── scsi0 (OS)       │
│    ├── scsi1 (Data)     │  ← Contesa!
│    └── scsi2 (WAL)      │
└─────────────────────────┘

virtio-scsi-single (un controller per disco) — RACCOMANDATO
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│ SCSI Controller 0 │  │ SCSI Controller 1 │  │ SCSI Controller 2 │
│ (iothread 0)      │  │ (iothread 1)      │  │ (iothread 2)      │
│  └── scsi0 (OS)   │  │  └── scsi1 (Data) │  │  └── scsi2 (WAL)  │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

### Cache Mode

| Modalità | Uso | Sicurezza Dati | Performance |
|---|---|---|---|
| `none` | Database, qualsiasi workload critico | Alta (write-through) | Buona |
| `directsync` | Database con requisito ACID rigoroso | Massima (sync write) | Media |
| `writeback` | Workload non critici, temp data | Bassa (dati in cache) | Alta |
| `writethrough` | Compromesso sicurezza/performance | Alta | Media |
| `unsafe` | Solo test/dev, MAI in produzione | Nessuna | Massima |

Per workload database in produzione: **sempre `cache=none`** o `cache=directsync`. Mai `writeback` o `unsafe`.

### Formato Disco

```bash
# RAW: prestazioni massime, nessun overhead
qm set 400 --scsi1 nvme-lvm:500,format=raw,iothread=1,cache=none

# qcow2: supporta snapshot, thin provisioning, ma overhead I/O
# NON raccomandato per workload ad alto I/O
```

Il formato raw su LVM-thin combina le prestazioni del raw con il thin provisioning a livello di volume manager.

---

## CPU Pinning e NUMA Awareness

### NUMA: Perché è Importante per l'I/O

Su sistemi multi-socket, ogni CPU ha la propria memoria locale. L'accesso alla memoria remota (di un altro socket) introduce latenza aggiuntiva. Per workload I/O intensive, dove il buffer del database e le strutture I/O risiedono in memoria, l'allineamento NUMA è critico.

```
┌────────────────────────┐   ┌────────────────────────┐
│     NUMA Node 0        │   │     NUMA Node 1        │
│  CPU cores 0-7         │   │  CPU cores 8-15        │
│  Local RAM: 64 GB      │   │  Local RAM: 64 GB      │
│  NVMe 0 (PCIe slot 0)  │   │  NVMe 1 (PCIe slot 1)  │
│                        │   │                        │
│  Accesso locale: ~80ns │   │  Accesso locale: ~80ns │
└────────┬───────────────┘   └───────────────┬────────┘
         │                                   │
         │    Accesso remoto: ~150ns (+90%)   │
         └───────────────────────────────────┘
```

### Verificare la Topologia NUMA

```bash
# Sul nodo Proxmox
numactl --hardware

# Output tipico su un sistema dual-socket:
# available: 2 nodes (0-1)
# node 0 cpus: 0 1 2 3 4 5 6 7
# node 0 size: 65536 MB
# node 1 cpus: 8 9 10 11 12 13 14 15
# node 1 size: 65536 MB
# node distances:
# node   0   1
#   0:  10  21
#   1:  21  10

# Verificare a quale NUMA node è collegato il dispositivo NVMe
cat /sys/block/nvme0n1/device/numa_node
# Output: 0 (il NVMe è sul NUMA node 0)
```

### Configurazione NUMA per la VM

```bash
# Abilitare NUMA awareness
qm set 400 --numa 1

# Pinnare la VM al NUMA node dove risiede lo storage NVMe
# Se NVMe è su NUMA node 0 (cores 0-7):
qm set 400 --numa0 cpus=0-7,hostnodes=0,memory=65536,policy=bind
```

### CPU Pinning con Hookscript

```bash
cat > /var/lib/vz/snippets/highio-cpupin.pl << 'SCRIPT'
#!/usr/bin/perl
use strict;
use warnings;

my $vmid = shift;
my $phase = shift;

if ($phase eq 'post-start') {
    my $pid = `cat /run/qemu-server/$vmid.pid`;
    chomp $pid;

    # Pinnare il processo QEMU principale ai core del NUMA node 0
    system("taskset -apc 0-7 $pid");

    # Pinnare anche gli iothread
    my @iothreads = `ls /proc/$pid/task/`;
    chomp @iothreads;
    for my $tid (@iothreads) {
        my $comm = `cat /proc/$pid/task/$tid/comm 2>/dev/null`;
        if ($comm =~ /iothread/) {
            system("taskset -pc 0-7 $tid");
        }
    }

    print "CPU pinning applied for VM $vmid\n";
}
SCRIPT

chmod +x /var/lib/vz/snippets/highio-cpupin.pl
qm set 400 --hookscript local:snippets/highio-cpupin.pl
```

---

## Configurazione Rete per Storage: 10GbE e Jumbo Frames

Per workload I/O che utilizzano storage di rete (iSCSI, NFS, Ceph), la rete di storage è un potenziale collo di bottiglia.

### Requisiti Minimi

| Workload | Banda Minima | Raccomandato | Protocollo |
|---|---|---|---|
| Ceph OSD | 10 GbE | 25 GbE | Ceph native |
| iSCSI all-flash | 10 GbE | 25 GbE | iSCSI/iSER |
| NFS | 10 GbE | 25 GbE | NFSv4.1 |
| Storage locale | N/A | N/A | N/A |

### Configurazione Jumbo Frames

Le jumbo frames (MTU 9000) riducono l'overhead del protocollo e migliorano il throughput per il traffico di storage.

```bash
# /etc/network/interfaces sul nodo Proxmox

# NIC dedicata per storage con MTU 9000
auto ens1f0
iface ens1f0 inet manual
    mtu 9000

# Bridge per storage network
auto vmbr1
iface vmbr1 inet static
    address 10.10.1.1/24
    bridge-ports ens1f0
    bridge-stp off
    bridge-fd 0
    mtu 9000

# Verificare
ip link show vmbr1 | grep mtu
# mtu 9000
```

```bash
# Verificare la connettività con jumbo frames
ping -M do -s 8972 10.10.1.2
# Se il ping funziona, le jumbo frames sono correttamente configurate
# Se fallisce, verificare switch, NIC, e tutti gli hop intermedi
```

### Dedicare NIC allo Storage

```bash
# Separare il traffico di storage dal traffico di gestione e VM
# Esempio con 4 NIC:
# ens1f0 + ens1f1: bond per management + VM traffic (vmbr0)
# ens2f0 + ens2f1: bond per storage traffic (vmbr1)

auto bond0
iface bond0 inet manual
    bond-slaves ens1f0 ens1f1
    bond-mode 802.3ad
    bond-miimon 100
    bond-xmit-hash-policy layer3+4

auto bond1
iface bond1 inet manual
    bond-slaves ens2f0 ens2f1
    bond-mode 802.3ad
    bond-miimon 100
    bond-xmit-hash-policy layer3+4
    mtu 9000
```

---

## Kernel Tuning per I/O Intensive Workloads

### I/O Scheduler

Il scheduler I/O del kernel gestisce l'ordine in cui le richieste vengono inviate al dispositivo. Per NVMe e SSD moderni, lo scheduler `none` (noop) è tipicamente ottimale perché il dispositivo ha la propria coda hardware.

```bash
# Verificare lo scheduler corrente
cat /sys/block/nvme0n1/queue/scheduler
# [none] mq-deadline kyber bfq

# Per NVMe: none (noop) è ottimale
echo none > /sys/block/nvme0n1/queue/scheduler

# Per SSD SATA: mq-deadline è un buon compromesso
echo mq-deadline > /sys/block/sda/queue/scheduler

# Per HDD: bfq per fairness, mq-deadline per throughput
echo mq-deadline > /sys/block/sdb/queue/scheduler

# Persistente: udev rule
cat > /etc/udev/rules.d/60-io-scheduler.rules << 'EOF'
# NVMe: noop
ACTION=="add|change", KERNEL=="nvme[0-9]*", ATTR{queue/scheduler}="none"
# SSD SATA: mq-deadline
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="mq-deadline"
# HDD: mq-deadline
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="mq-deadline"
EOF
udevadm control --reload-rules
```

### Parametri sysctl per I/O

```bash
# /etc/sysctl.d/99-highio.conf

# Swappiness: ridurre al minimo lo swap per workload database
vm.swappiness = 10

# Dirty pages: controllare quando il kernel scrive le pagine sporche su disco
# Per workload database (consistenza prioritaria):
vm.dirty_ratio = 10              # % di RAM prima di bloccare le scritture
vm.dirty_background_ratio = 5    # % di RAM prima di iniziare writeback async
# Per workload throughput (batch, analytics):
# vm.dirty_ratio = 40
# vm.dirty_background_ratio = 10

# Timeout per dirty pages
vm.dirty_expire_centisecs = 500   # 5 secondi (default 3000 = 30s)
vm.dirty_writeback_centisecs = 100 # Intervallo writeback: 1 secondo

# Limite VFS cache pressure
vm.vfs_cache_pressure = 50        # Ridurre la pressione sul cache degli inode

# Dimensione massima delle richieste di lettura anticipata
# Per workload sequenziali, aumentare:
# echo 256 > /sys/block/nvme0n1/queue/read_ahead_kb  # Default: 128

# Numero massimo di richieste in coda
# Per NVMe ad alte prestazioni:
# echo 1024 > /sys/block/nvme0n1/queue/nr_requests  # Default: 256
```

```bash
# Applicare immediatamente
sysctl -p /etc/sysctl.d/99-highio.conf

# Verificare
sysctl vm.swappiness vm.dirty_ratio vm.dirty_background_ratio
```

### Transparent Huge Pages (THP)

Per database come PostgreSQL e MySQL, THP può causare latency spike. È raccomandato disabilitarle:

```bash
# Verificare lo stato
cat /sys/kernel/mm/transparent_hugepage/enabled
# [always] madvise never

# Disabilitare
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag

# Persistente: creare un servizio systemd
cat > /etc/systemd/system/disable-thp.service << 'EOF'
[Unit]
Description=Disable Transparent Huge Pages
DefaultDependencies=no
After=sysinit.target local-fs.target
Before=basic.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo never > /sys/kernel/mm/transparent_hugepage/enabled && echo never > /sys/kernel/mm/transparent_hugepage/defrag'

[Install]
WantedBy=basic.target
EOF

systemctl daemon-reload
systemctl enable disable-thp
```

---

## Benchmarking con fio: Confronto VMware vs Proxmox

### Profili di Test Standardizzati

Utilizzare gli stessi profili di test su entrambe le piattaforme per un confronto valido.

```ini
# /tmp/fio-db-random.fio — Simula workload database (random 8K read/write)
[global]
ioengine=libaio
direct=1
time_based
runtime=300
group_reporting
randrepeat=0
norandommap

[random-readwrite]
bs=8k
rw=randrw
rwmixread=70
iodepth=32
numjobs=8
size=10G
filename=/data/fio-test-file
```

```ini
# /tmp/fio-seq-throughput.fio — Simula workload sequenziale (analytics, backup)
[global]
ioengine=libaio
direct=1
time_based
runtime=300
group_reporting

[sequential-read]
bs=1M
rw=read
iodepth=16
numjobs=4
size=10G
filename=/data/fio-test-file

[sequential-write]
bs=1M
rw=write
iodepth=16
numjobs=4
size=10G
filename=/data/fio-test-file2
```

```ini
# /tmp/fio-latency.fio — Test di latenza pura (single thread, low queue depth)
[global]
ioengine=libaio
direct=1
time_based
runtime=120
group_reporting

[latency-read]
bs=4k
rw=randread
iodepth=1
numjobs=1
size=1G
filename=/data/fio-test-file
percentile_list=50:90:95:99:99.9
```

### Esecuzione e Confronto

```bash
# Eseguire su VMware
fio /tmp/fio-db-random.fio --output-format=json --output=/tmp/fio-vmware-db.json
fio /tmp/fio-seq-throughput.fio --output-format=json --output=/tmp/fio-vmware-seq.json
fio /tmp/fio-latency.fio --output-format=json --output=/tmp/fio-vmware-lat.json

# Eseguire su Proxmox (stessi file!)
fio /tmp/fio-db-random.fio --output-format=json --output=/tmp/fio-proxmox-db.json
fio /tmp/fio-seq-throughput.fio --output-format=json --output=/tmp/fio-proxmox-seq.json
fio /tmp/fio-latency.fio --output-format=json --output=/tmp/fio-proxmox-lat.json
```

### Analisi dei Risultati

```bash
# Script di confronto rapido
#!/bin/bash
for platform in vmware proxmox; do
  echo "=== ${platform^^} ==="
  echo "--- Random 8K R/W ---"
  jq '.jobs[0].read.iops, .jobs[0].write.iops, .jobs[0].read.lat_ns.mean/1000000, .jobs[0].write.lat_ns.mean/1000000' /tmp/fio-${platform}-db.json

  echo "--- Sequential ---"
  jq '.jobs[0].read.bw/1024, .jobs[1].write.bw/1024' /tmp/fio-${platform}-seq.json

  echo "--- Latency (us) ---"
  jq '.jobs[0].read.clat_ns.percentile | .["50.000000"]/1000, .["99.000000"]/1000, .["99.900000"]/1000' /tmp/fio-${platform}-lat.json
done
```

### Criteri di Accettazione

| Metrica | Accettabile | Ottimale |
|---|---|---|
| IOPS random | >= 90% di VMware | >= 100% di VMware |
| Throughput sequenziale | >= 90% di VMware | >= 100% di VMware |
| Latenza media | <= 110% di VMware | <= 100% di VMware |
| Latenza p99 | <= 120% di VMware | <= 100% di VMware |

Se le prestazioni Proxmox sono inferiori al 90% di VMware, investigare la configurazione dello storage, il driver VirtIO, la cache mode, e il kernel tuning prima di procedere con la migrazione dei workload di produzione.

---

## Monitoraggio Post-Migrazione

### Strumenti di Monitoraggio I/O

```bash
# iostat: monitoraggio continuo delle prestazioni disco
iostat -xdmz 5 | tee /var/log/iostat-post-migration.log

# Colonne chiave:
# r/s, w/s      = IOPS
# rMB/s, wMB/s  = Throughput
# r_await, w_await = Latenza media (target: < baseline VMware)
# aqu-sz        = Queue depth (se cresce, il disco è saturo)
# %util         = Saturazione (>95% = collo di bottiglia)

# iotop: identificare i processi con più I/O
iotop -b -o -d 5

# atop: visione complessiva del sistema con storico
atop -d 5

# Proxmox: metriche VM dalla command line
qm monitor 400 -c "info block"
qm monitor 400 -c "info blockstats"
```

### Monitoraggio con Prometheus e Grafana

```bash
# Installare node_exporter sul guest per metriche dettagliate
apt install prometheus-node-exporter

# Abilitare i collector per disco
cat > /etc/default/prometheus-node-exporter << 'EOF'
ARGS="--collector.diskstats --collector.filesystem --collector.netdev"
EOF

systemctl restart prometheus-node-exporter
```

Query Prometheus utili per il monitoraggio I/O:

```promql
# IOPS per device
rate(node_disk_reads_completed_total{device="sda"}[5m])
rate(node_disk_writes_completed_total{device="sda"}[5m])

# Latenza media
rate(node_disk_read_time_seconds_total{device="sda"}[5m]) / rate(node_disk_reads_completed_total{device="sda"}[5m])

# Queue depth
node_disk_io_now{device="sda"}

# Throughput
rate(node_disk_read_bytes_total{device="sda"}[5m])
rate(node_disk_written_bytes_total{device="sda"}[5m])

# % Utilizzo
rate(node_disk_io_time_seconds_total{device="sda"}[5m]) * 100
```

### Alert Raccomandati

```yaml
# alerting_rules.yml
groups:
  - name: io_alerts
    rules:
      - alert: HighDiskLatency
        expr: rate(node_disk_read_time_seconds_total[5m]) / rate(node_disk_reads_completed_total[5m]) > 0.005
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Disk read latency > 5ms on {{ $labels.instance }}"

      - alert: DiskSaturation
        expr: rate(node_disk_io_time_seconds_total[5m]) > 0.95
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk saturation > 95% on {{ $labels.instance }}"

      - alert: IOPSDegraded
        expr: rate(node_disk_reads_completed_total[5m]) + rate(node_disk_writes_completed_total[5m]) < 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "IOPS dropped below baseline on {{ $labels.instance }}"
```

---

## Best Practices

- **Profilare le prestazioni I/O su VMware prima della migrazione** — senza un baseline, non è possibile validare che Proxmox offra prestazioni equivalenti
- **Utilizzare local NVMe con LVM-thin** per workload che richiedono la latenza più bassa e gli IOPS più alti; Ceph solo quando HA è un requisito non negoziabile
- **Scegliere il formato raw** per tutti i dischi dati di workload ad alto I/O; il qcow2 aggiunge overhead misurabile
- **Configurare `virtio-scsi-single` con `iothread=1`** per ogni disco — un controller e un thread I/O dedicati eliminano la contesa
- **Impostare `cache=none`** per workload database e qualsiasi applicazione che gestisce la propria cache; `directsync` per i casi in cui è richiesta la garanzia di sync write
- **Disabilitare il memory ballooning** per tutte le VM con workload I/O intensive
- **Allineare la VM al NUMA node** dove risiede il dispositivo storage fisico per minimizzare la latenza di accesso alla memoria
- **Separare il traffico di storage** su NIC dedicate con jumbo frames (MTU 9000) per storage di rete
- **Impostare `vm.swappiness = 10`** e configurare i parametri dirty page appropriati per il tipo di workload
- **Disabilitare Transparent Huge Pages** all'interno delle VM che eseguono database
- **Eseguire benchmark fio con profili identici** su VMware e Proxmox e non procedere se la degradazione supera il 10%
- **Monitorare continuamente** con iostat, iotop, e Prometheus/Grafana per almeno 7 giorni dopo la migrazione
- **Separare i dischi fisicamente**: OS su uno storage, dati su NVMe, WAL/log su un NVMe separato se disponibile

---

## Troubleshooting

### Problema: IOPS Significativamente Inferiori su Proxmox

**Sintomi**: I benchmark fio su Proxmox mostrano IOPS random 4K inferiori del 30% o più rispetto a VMware. Le applicazioni risultano più lente. `iostat` mostra latenza elevata.

**Causa**: Molteplici cause possibili: controller disco non VirtIO SCSI (usando IDE o SATA emulato), mancanza di iothread, formato qcow2 anziché raw, cache mode errata, I/O scheduler non ottimale, o backend storage con prestazioni insufficienti.

**Soluzione**: Verificare sistematicamente ogni livello:
```bash
# 1. Verificare il controller
qm config 400 | grep scsihw
# Deve essere: virtio-scsi-single

# 2. Verificare iothread
qm config 400 | grep scsi
# Deve includere: iothread=1

# 3. Verificare il formato disco
qm config 400 | grep scsi
# Preferire raw su LVM

# 4. Verificare la cache mode
# Deve essere: cache=none per DB

# 5. Verificare lo scheduler nel guest
cat /sys/block/sda/queue/scheduler
# Per SSD/NVMe virtualizzato: none

# 6. Benchmark dello storage nativo (senza VM)
fio --name=test --ioengine=libaio --direct=1 --bs=4k --iodepth=32 --rw=randread --size=1G --filename=/dev/nvme0n1p1
```

**Prevenzione**: Configurare tutti i parametri di ottimizzazione prima dell'importazione dei dati. Eseguire benchmark sullo storage nativo Proxmox per stabilire il tetto massimo raggiungibile.

---

### Problema: Latency Spike Periodici

**Sintomi**: La latenza I/O è normalmente accettabile ma mostra spike periodici (ogni 30-60 secondi) dove la latenza aumenta di 10-100x. Le applicazioni sperimentano timeout intermittenti.

**Causa**: I dirty page writeback del kernel causa flush periodici di grandi quantità di dati su disco, saturando temporaneamente la banda I/O. Può anche essere causato da ZFS che esegue scrub/trim, Ceph recovery, o operazioni di background dell'hypervisor.

**Soluzione**: Ridurre `vm.dirty_ratio` e `vm.dirty_background_ratio` per forzare writeback più frequenti e più piccoli:
```bash
sysctl -w vm.dirty_ratio=10
sysctl -w vm.dirty_background_ratio=5
sysctl -w vm.dirty_expire_centisecs=500
```
Se su ZFS, verificare che non ci sia uno scrub in corso (`zpool status`). Se su Ceph, verificare lo stato del cluster (`ceph -s`).

**Prevenzione**: Configurare i parametri dirty page appropriati al momento del setup. Programmare gli scrub ZFS e i deep-scrub Ceph durante le ore di basso carico. Monitorare la latenza p99 con alerting.

---

### Problema: Throughput Sequenziale Limitato su Ceph

**Sintomi**: Le operazioni sequenziali (backup, import dati, rebuild indici) sono molto più lente su Ceph rispetto allo storage locale VMware. Il throughput è limitato a 200-400 MB/s quando i dischi locali supportano 2000+ MB/s.

**Causa**: Ceph introduce overhead di rete e di replica per ogni operazione I/O. Con replica 3 su una rete 10GbE, il throughput effettivo per client è limitato dalla banda di rete: 10 Gbps / 3 repliche = ~400 MB/s teorico, meno nella pratica.

**Soluzione**: Per workload che richiedono throughput sequenziale elevato, considerare: upgrade della rete a 25GbE o superiore, riduzione del fattore di replica a 2 (accettando minor ridondanza), o spostamento dei dati più critici su storage locale NVMe. Per operazioni batch temporanee, abilitare il caching locale.

**Prevenzione**: Valutare realisticamente la banda di rete disponibile rispetto ai requisiti di throughput prima di scegliere Ceph. Lo storage locale è sempre più veloce per singola VM; Ceph eccelle in scalabilità e HA, non in prestazioni raw per singolo nodo.

---

### Problema: CPU Steal Time Elevato che Impatta l'I/O

**Sintomi**: All'interno della VM, `top` mostra un valore elevato di `%st` (steal time). Le prestazioni I/O sono degradate anche se lo storage è veloce. La latenza delle operazioni I/O è inconsistente.

**Causa**: Overcommit delle CPU sul nodo Proxmox. La VM non riceve i cicli CPU necessari per processare le interruzioni I/O, causando ritardo nella gestione delle operazioni completate. Il problema è esacerbato quando più VM ad alto I/O competono per le stesse CPU fisiche.

**Soluzione**: Ridurre l'overcommit CPU sul nodo. Implementare CPU pinning per le VM ad alto I/O. Verificare che il nodo non sia sovraccarico:
```bash
# Sul nodo Proxmox
mpstat -P ALL 5
# Nessun core deve essere costantemente al 100%

# Verificare il rapporto vCPU totali / core fisici
# Raccomandato per alto I/O: <= 1.5:1
```

**Prevenzione**: Non sovrascrivere le CPU per VM ad alto I/O. Utilizzare CPU pinning per garantire l'accesso dedicato ai core. Separare le VM ad alto I/O su nodi dedicati se possibile.

---

### Problema: Degradazione Prestazioni con ZFS senza ARC Sufficiente

**Sintomi**: Le prestazioni I/O su ZFS sono buone inizialmente ma degradano nel tempo. `arcstat` mostra un hit ratio basso. Le operazioni random read sono particolarmente lente.

**Causa**: L'ARC (Adaptive Replacement Cache) di ZFS non ha memoria sufficiente perché le VM occupano la maggior parte della RAM del nodo. ZFS necessita di RAM per l'ARC; senza di essa, ogni read va direttamente al disco.

**Soluzione**: Riservare memoria adeguata per l'ARC:
```bash
# Verificare la dimensione ARC corrente
arcstat 5

# Impostare un minimo per l'ARC (esempio: 16 GB)
echo 17179869184 > /sys/module/zfs/parameters/zfs_arc_min
# Impostare il massimo
echo 34359738368 > /sys/module/zfs/parameters/zfs_arc_max

# Persistente in /etc/modprobe.d/zfs.conf:
options zfs zfs_arc_min=17179869184
options zfs zfs_arc_max=34359738368
```
Regola: ARC dovrebbe avere almeno 1 GB per ogni 1 TB di dati sul pool, con un minimo di 8-16 GB.

**Prevenzione**: Calcolare la memoria necessaria per l'ARC ZFS prima di allocare la RAM alle VM. La formula è: RAM nodo = RAM totale VM + ARC ZFS (min 16 GB) + RAM OS Proxmox (2-4 GB).

---

### Problema: NVMe Non Raggiunge le Prestazioni Specificate

**Sintomi**: I benchmark fio su NVMe locale mostrano IOPS o throughput significativamente inferiori alle specifiche del produttore. Il dispositivo dovrebbe supportare 500K IOPS random 4K ma ne raggiunge solo 100K.

**Causa**: Parametri di test non ottimali (iodepth troppo basso, numjobs insufficienti), power management del NVMe attivo, scheduler I/O non ottimale, oppure il NVMe è collegato a un slot PCIe con larghezza di banda insufficiente (x1 o x2 anziché x4).

**Soluzione**: Verificare il collegamento PCIe:
```bash
# Verificare la larghezza di banda PCIe
lspci -vv -s $(lspci | grep -i nvme | awk '{print $1}') | grep -i width
# Deve mostrare: LnkSta: Speed 8GT/s, Width x4 (per PCIe 3.0)

# Disabilitare il power management del NVMe
echo 0 > /sys/block/nvme0n1/device/power/autosuspend_delay_ms
nvme set-feature /dev/nvme0n1 -f 2 -v 0  # Disable APST

# Verificare lo scheduler
cat /sys/block/nvme0n1/queue/scheduler
# Deve essere: [none]
```

**Prevenzione**: Verificare il collegamento PCIe del NVMe durante l'installazione hardware. Disabilitare il power management APST per workload di produzione. Utilizzare i parametri di test fio corretti (iodepth >= 32, numjobs >= 4 per saturare un NVMe moderno).

---

## Riferimenti

- [Proxmox VE Wiki — Performance Tweaks](https://pve.proxmox.com/wiki/Performance_Tweaks)
- [Proxmox VE Wiki — ZFS on Linux](https://pve.proxmox.com/wiki/ZFS_on_Linux)
- [Proxmox VE Wiki — Ceph Server](https://pve.proxmox.com/wiki/Deploy_Hyper-Converged_Ceph_Cluster)
- [fio Documentation](https://fio.readthedocs.io/en/latest/)
- [Red Hat — KVM I/O Performance](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/configuring_and_managing_virtualization/optimizing-virtual-machine-i-o-performance_optimizing-virtual-machine-performance-in-rhel)
- [Linux Kernel — Block Layer Documentation](https://www.kernel.org/doc/html/latest/block/index.html)
- [VMware — esxtop Documentation](https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.vsphere.monitoring.doc/GUID-D89E8267-C74A-4D43-B5E0-A325F740FC0C.html)
- [ZFS on Linux — Performance Tuning](https://openzfs.github.io/openzfs-docs/Performance%20and%20Tuning/Workload%20Tuning.html)
- [Ceph Documentation — Performance](https://docs.ceph.com/en/latest/rados/configuration/bluestore-config-ref/)
- [Prometheus — Node Exporter](https://prometheus.io/docs/guides/node-exporter/)
- [QEMU Documentation — Block Layer](https://www.qemu.org/docs/master/system/qemu-block-drivers.html)

---

## Approfondimenti — note del 2026-04-27

> **Approfondimento — qcow2 vs raw, numeri concreti su NVMe.** Misurazioni 2024-2025 (vari workload `fio` 4K random read/write, qd=32, jobs=8) tipicamente mostrano: **raw su LVM-thin** raggiunge il ~100% delle prestazioni del dispositivo (es. NVMe Samsung PM983: ~480K IOPS read 4K); **raw su file ext4/xfs** ~95-98%; **qcow2 con `cluster_size=64K` e preallocazione `metadata`** ~85-92% in random; **qcow2 thin (no preallocazione)** crolla a 60-75% sotto carico misto perche ogni write su cluster non allocato richiede metadata fetch + allocate. Il qcow2 ha valore quando si vogliono snapshot live, dirty bitmap per backup incrementale o thin provisioning portabile fuori da LVM. Per workload high-I/O in produzione: raw su LVM-thin e la scelta standard. Fonte: [QEMU qcow2 v3 spec](https://github.com/qemu/qemu/blob/master/docs/interop/qcow2.txt) + [Proxmox VE Wiki — Storage](https://pve.proxmox.com/wiki/Storage), retrieved 2026-04-27.

> **Approfondimento — `iostat -xdz` vs `-xdmz` vs `-xdmt`.** Per profilare correttamente: `iostat -xdmz 5 720` raccoglie ogni 5 sec per 1h (720 campioni), formato MB/s, salta device a zero attivita (`-z`). I campi cruciali oltre IOPS/throughput: `r_await` e `w_await` (latenza media di completamento read/write in ms — se sale sopra il baseline VMware, hai un problema), `aqu-sz` (queue depth media — se cresce monotona, il device e saturo e accumula richieste), `%util` (percentuale di tempo con almeno 1 richiesta in volo — > 95% in continuo = saturazione, ma su NVMe multi-coda e una metrica meno significativa rispetto a SATA/SAS). Aggiungere `-t` per timestamp assoluti. Esempio di analisi rapida: `awk 'NR>2 {sum+=$10; n++} END {print "avg r_await:", sum/n, "ms"}' iostat.log`. Fonte: [iostat(1) sysstat manpage](https://man7.org/linux/man-pages/man1/iostat.1.html), retrieved 2026-04-27.

> **Approfondimento — p99 latency targets per categoria.** Riferimenti utili: OLTP DB (PG/MySQL su NVMe locale): p99 read 4K < 1 ms, p99 write 4K < 2 ms, p99 fsync < 5 ms (commit critical). Cache key-value (Redis persistente): p99 < 0.5 ms (Redis fa snapshot async, le scritture sono raramente sync). OLAP analytics (ClickHouse, Spark): p99 sequential 1M < 50 ms su SSD, < 20 ms su NVMe. File server SMB/NFS: p99 read 64K < 10 ms (utenti percepiscono sopra ~50 ms). Logging/SIEM (Elasticsearch ingest): p99 write < 5 ms (la coda di indice non deve riempirsi). Backup target (Veeam, Bacula, PBS): throughput sequenziale > tempo finestra; latency e secondaria. Questi numeri sono benchmark di riferimento, non SLA contrattuali; il vero target e "uguale o migliore di VMware". Fonti: [Percona blog — MySQL benchmarks](https://www.percona.com/blog/category/benchmarks/), [Brendan Gregg — Systems Performance 2nd ed.](https://www.brendangregg.com/systems-performance-2nd-edition-book.html), retrieved 2026-04-27.

> **Errore comune — `--numa 1` senza `numa0 cpus=...,hostnodes=...,policy=bind`.** Sintomo: la VM si avvia e funziona, ma le prestazioni sono incoerenti, peggiorano col tempo, o variano da una sessione all'altra. Causa: `--numa 1` espone la topologia NUMA al guest, ma senza `policy=bind` lo scheduler kernel del nodo Proxmox e libero di migrare il processo QEMU tra NUMA node, causando memoria cross-NUMA dopo che il DB ha caricato il buffer pool. Soluzione: aggiungere esplicitamente `qm set <VMID> --numa0 cpus=0-7,hostnodes=0,memory=<MB>,policy=bind`; per VM grandi che spannano piu socket, usare numa0 + numa1 con `interleave` come fallback. Verifica dentro la VM con `numactl --hardware` (deve vedere il layout coerente con i pin). Fonte: [Proxmox VE Wiki — NUMA](https://pve.proxmox.com/wiki/Performance_Tweaks#NUMA), retrieved 2026-04-27.

> **Errore comune — Disabilitare THP nel guest, ma lasciarlo attivo nel nodo Proxmox.** Sintomo: il DB nel guest e configurato con `transparent_hugepage=never`, ma le latency spike continuano. Causa: il kernel del nodo Proxmox sta facendo defrag/khugepaged sulle pagine sottostanti la VM. Soluzione: disabilitare THP *sia* nel nodo *sia* nei guest critici. Su Proxmox: aggiungere `transparent_hugepage=never` ai parametri kernel in `/etc/default/grub` (`GRUB_CMDLINE_LINUX_DEFAULT="quiet transparent_hugepage=never"`), `update-grub`, riavviare. Verificare: `cat /sys/kernel/mm/transparent_hugepage/enabled` deve mostrare `always madvise [never]`. Per le huge pages esplicite (PostgreSQL `huge_pages=on`), configurare `vm.nr_hugepages` separatamente: questo non e in conflitto con la disabilitazione del THP. Fonte: [Linux kernel — Transparent Hugepage Support](https://www.kernel.org/doc/html/latest/admin-guide/mm/transhuge.html), retrieved 2026-04-27.

> **Caso reale — Migrazione cluster 12 VM Veeam Repository da VMFS a Ceph: throughput in calo del 60%.** Un cluster di repository Veeam (12 VM, ognuna con 20 TB di backup data) e stato migrato da VMFS su array iSCSI a Ceph RBD. Pre-migrazione: 1.8 GB/s sequential write per VM. Post-migrazione: 700 MB/s. Investigazione: rete Ceph 10 GbE (1.25 GB/s teorico), replica 3 → throughput per-client effettivo ~400 MB/s teorico. Il numero osservato (700 MB/s) era *piu alto* del teorico replica-3 perche i backup avevano alta compressione side-effect cache, ma comunque ben sotto le aspettative. Soluzione adottata: (a) ridotto replica factor a 2 (accettato il rischio per dati di backup, presenti anche su tape); (b) upgrade della rete Ceph a 25 GbE; (c) re-test → 1.4 GB/s. Lezione: per workload throughput-bound, la matematica banda/replica vince sempre sull'ottimizzazione VM. Calcolare *prima* di scegliere il backend. Fonte: case study interno (anonimizzato); riferimento metodologico [Red Hat Ceph Storage — Network Bandwidth](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/), retrieved 2026-04-27.

> **Caso reale — `kworker` al 100% causa CPU steal sul guest.** Una VM Linux migrata su Proxmox mostrava `%st = 25-40%` in `top`, con prestazioni I/O degradate del 30%. Il nodo Proxmox stesso aveva un `kworker/u32:5` al 100% di CPU. Causa: cluster Ceph con un OSD lento (un disco con bad sector latente non ancora marcato fail) stava ritardando le operazioni di rebalance, scaricando il carico sul nodo. Diagnosi: `ceph -s` mostrava `recovery i/o` continuo; `ceph osd perf` rivelava un OSD con `apply_latency_ms` 10x superiore agli altri. Soluzione: marcare l'OSD `out` (`ceph osd out <id>`), sostituire il disco fisico, ricreare l'OSD, ribilanciare. Lezione: prestazioni I/O sul guest possono essere causate da condizioni del cluster sottostante, non dalla VM o dal nodo Proxmox specifico. Diagnosi sempre dall'alto (cluster) verso il basso (singola VM). Fonte: [Ceph Documentation — Troubleshooting OSDs](https://docs.ceph.com/en/latest/rados/troubleshooting/troubleshooting-osd/), retrieved 2026-04-27.

---

## Esercizi

1. **Concettuale — caratterizza il workload.** Per ognuno, indica il profilo I/O dominante (latency-bound vs throughput-bound), il backend Proxmox raccomandato e il livello di replica/ridondanza, motivando in 4-5 righe: (a) PostgreSQL 16 OLTP con 5K TPS picco e dataset 200 GB; (b) ClickHouse cluster a 4 nodi per analytics su 10 TB di dati log; (c) Redis 7 con AOF persistence per session store, 100K req/s; (d) Repository Veeam, 50 TB di backup giornalieri con retention 90 giorni; (e) Microsoft Exchange 2019, 500 utenti, 30 GB media mailbox.

2. **Lab — profilare un workload reale e tradurlo in budget Proxmox.** Su una VM (anche piccola, 2 vCPU 4 GB RAM su un host di test), eseguire un workload sintetico (`stress-ng --hdd 4 --hdd-bytes 5G --timeout 300s` oppure `pgbench` su un PostgreSQL test). Raccogliere in parallelo: (a) `iostat -xdmz 5 60 > workload.iostat`; (b) `iotop -b -o -d 5 -n 12 > workload.iotop`; (c) snapshot di `cat /proc/diskstats` ogni 30s. Produrre un riepilogo (tabella) con: IOPS medio/picco/p99, throughput medio/picco, latenza r_await/w_await medio/p99, queue depth media. Convertire il riepilogo in requisiti per la VM Proxmox: backend minimo, configurazione disco, cache mode, iothread.

3. **Scenario — Ceph performance budget.** Hai un cluster Ceph con 6 nodi, 8 OSD SSD per nodo (totale 48 OSD), rete 25 GbE dedicata, replica 3, MTU 9000. Calcola la banda teorica per-client (ignorando overhead): (a) banda di rete singolo client; (b) penalita di replica; (c) IOPS attesi per OSD (assumendo SSD da 50K IOPS random 4K); (d) IOPS attesi per cluster; (e) effetto del fattore di replica sul throughput per-client. Quale workload del modulo (vedi tabella in §1) e adatto e quale no? Argomenta in 10-15 righe.

4. **Lab — benchmark fio comparativi.** Eseguire i 3 profili fio del modulo (db-random.fio, seq-throughput.fio, latency.fio) su due ambienti: (a) un disco locale (SATA SSD o NVMe) montato direttamente; (b) lo stesso disco esposto a una VM Proxmox via virtio-scsi-single con cache=none, iothread=1, format=raw. Calcolare il delta percentuale (Proxmox vs nativo) per: IOPS random, throughput sequenziale, latenza p50, latenza p99. Atteso: IOPS Proxmox ≥ 95% nativo, p99 ≤ 110% nativo. Se non rientra, individuare la causa (governor CPU, scheduler I/O, cache mode, iothread mancante).

5. **Stretch — hookscript NUMA-aware automatico.** Estendere l'hookscript del modulo per: (1) leggere automaticamente il `numa_node` del primo disco scsi della VM; (2) leggere `numactl --hardware` per ottenere la lista di core di quel NUMA node; (3) applicare `taskset -apc <cores>` al QEMU PID + iothread; (4) impostare la affinity di interrupt sulle code virtio (`smp_affinity` di `/proc/irq/...`); (5) loggare in `/var/log/highio-pin/<vmid>.log` il risultato. Bonus: rilevare hot-add di nuovi dischi e ri-applicare il pinning sui nuovi iothread.

6. **Stretch — Grafana dashboard high-I/O VM.** Creare una dashboard Grafana (file JSON) con: (a) IOPS read/write per device (5 min rate); (b) throughput MB/s; (c) latenza media e p99 (calcolata da `node_disk_read_time_seconds_total / node_disk_reads_completed_total`); (d) queue depth (`node_disk_io_now`); (e) %util; (f) heatmap di latenza per identificare spike; (g) annotazioni per eventi di scrub ZFS o deep-scrub Ceph (via API o webhook). Esportare il dashboard JSON e documentare le query Prometheus utilizzate.

## Auto-valutazione

1. Quali sono le 4 metriche `esxtop` da raccogliere come baseline I/O e cosa misurano (DAVG, KAVG, GAVG, QAVG)?
2. Qual e la differenza pratica fra `virtio-scsi-pci` e `virtio-scsi-single` per workload high-I/O?
3. Quando `cache=writeback` e accettabile e quando invece e categoricamente vietato? Motiva.
4. Per un disco NVMe locale, quale I/O scheduler Linux e ottimale e perche?
5. Calcola il numero di huge pages 2 MB necessarie per `shared_buffers = 16 GB` su PostgreSQL.
6. Cosa fa `--numa 1` senza `numa0 cpus=...,policy=bind` e perche e insufficiente?
7. Differenza tra `vm.dirty_ratio` e `vm.dirty_background_ratio`. Quale impatto sulla latenza I/O?
8. Quale comando valida che la rete tra due nodi supporti jumbo frames end-to-end senza fragmentation?
9. Su Ceph con replica 3 e rete 10 GbE, qual e il throughput sequenziale teorico per singolo client e perche?
10. Spiega il significato di `aqu-sz` in `iostat`: come si interpreta un valore di 50 vs 5 vs 200 su un NVMe?
11. Cosa succede se il `cat /sys/block/nvme0n1/device/numa_node` ritorna 1 ma la VM e pinnata ai core 0-7 del NUMA node 0?
12. Su NVMe, perche disabilitare APST (Autonomous Power State Transitions) per workload di produzione?

## Letture primarie consigliate

- Brendan Gregg — *Systems Performance: Enterprise and the Cloud, 2nd ed.* (Pearson, 2020). ISBN 978-0136820154 (cap. 9 *Disks*, cap. 10 *Networking*).
- Linux kernel documentation — Block Layer. https://www.kernel.org/doc/html/latest/block/index.html (retrieved 2026-04-27).
- Linux kernel documentation — Transparent Hugepage Support. https://www.kernel.org/doc/html/latest/admin-guide/mm/transhuge.html (retrieved 2026-04-27).
- Linux kernel documentation — HugeTLB Pages. https://www.kernel.org/doc/html/latest/admin-guide/mm/hugetlbpage.html (retrieved 2026-04-27).
- Linux kernel documentation — VM sysctl. https://www.kernel.org/doc/html/latest/admin-guide/sysctl/vm.html (retrieved 2026-04-27).
- iostat(1) — sysstat. https://man7.org/linux/man-pages/man1/iostat.1.html (retrieved 2026-04-27).
- Red Hat — Optimizing Virtual Machine I/O Performance. https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/configuring_and_managing_virtualization/optimizing-virtual-machine-i-o-performance_optimizing-virtual-machine-performance-in-rhel (retrieved 2026-04-27).
- QEMU — Block Device Drivers Documentation. https://www.qemu.org/docs/master/system/qemu-block-drivers.html (retrieved 2026-04-27).
- QEMU — qcow2 v3 specification. https://github.com/qemu/qemu/blob/master/docs/interop/qcow2.txt (retrieved 2026-04-27).
- Proxmox VE Wiki — Performance Tweaks. https://pve.proxmox.com/wiki/Performance_Tweaks (retrieved 2026-04-27).
- Proxmox VE Wiki — Storage. https://pve.proxmox.com/wiki/Storage (retrieved 2026-04-27).
- Proxmox VE Wiki — ZFS on Linux. https://pve.proxmox.com/wiki/ZFS_on_Linux (retrieved 2026-04-27).
- OpenZFS Documentation — Workload Tuning. https://openzfs.github.io/openzfs-docs/Performance%20and%20Tuning/Workload%20Tuning.html (retrieved 2026-04-27).
- Ceph Documentation — Performance and Tuning. https://docs.ceph.com/en/latest/rados/configuration/bluestore-config-ref/ (retrieved 2026-04-27).
- VMware esxtop documentation — vSphere 8.0. https://docs.vmware.com/en/VMware-vSphere/8.0/com.vmware.vsphere.monitoring.doc/GUID-D89E8267-C74A-4D43-B5E0-A325F740FC0C.html (retrieved 2026-04-27).
- VMware vscsiStats — Knowledge Base. https://knowledge.broadcom.com/external/article/305316/using-vscsistats-to-analyze-virtual-mach.html (retrieved 2026-04-27).
- fio — Flexible I/O Tester documentation. https://fio.readthedocs.io/en/latest/ (retrieved 2026-04-27).
- Prometheus Node Exporter — disk metrics. https://github.com/prometheus/node_exporter (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 09.2 — `migrazione-database-postgresql-mysql.md`: il DB e l'esempio canonico di workload latency-bound.
- Modulo 09.1 — `migrazione-applicazioni-stateful.md`: applicazioni stateful spesso hanno componenti high-I/O (Redis persistent, Elasticsearch).
- Modulo 03.1 — `../03-STORAGE-AVANZATO-PROXMOX/lvm-e-lvm-thin-proxmox.md`: backend LVM-thin per high-IOPS.
- Modulo 03.2 — `../03-STORAGE-AVANZATO-PROXMOX/nfs-iscsi-storage-condiviso.md`: backend NFS/iSCSI, trade-off rete.
- Modulo 04.1 — `../04-NETWORKING-AVANZATO-PROXMOX/linux-bridge-vlan-bonding.md`: bonding + jumbo frames per storage network.
- Modulo 06.3 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/live-migration-minimo-downtime.md`: strategia di cutover che si applica anche ai workload high-IOPS dopo profile match.
- Modulo 08.1 — `../08-MIGRAZIONE-STORAGE/conversione-vmdk-qcow2-raw.md`: conversione formato dischi, motivazione raw vs qcow2.
- Modulo 08.4 — `../08-MIGRAZIONE-STORAGE/validazione-performance-storage.md`: framework di validazione fio.
- Modulo 13.x — `../13-MONITORAGGIO-E-OTTIMIZZAZIONE/zabbix-monitoraggio-proxmox.md`: monitoring continuo post-cutover.
- Modulo 17.x — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-storage-performance.md`: diagnosi problemi storage post-migrazione.

## Glossario locale

| Termine | Definizione |
|---|---|
| **IOPS** | Input/Output Operations Per Second; metrica primaria per workload random. |
| **Throughput** | MB/s effettivi; metrica primaria per workload sequenziali. |
| **Latency p99** | Latenza che copre il 99% delle operazioni; metrica chiave per UX. |
| **Queue depth (`aqu-sz`)** | Numero medio di richieste I/O in volo verso un device. |
| **`%util`** | Percentuale di tempo in cui un device ha avuto almeno 1 richiesta in volo. |
| **DAVG/cmd (esxtop)** | Latenza media del dispositivo fisico, misurata sotto il driver storage VMware. |
| **KAVG/cmd (esxtop)** | Latenza aggiunta dal kernel VMware (storage stack ESXi). |
| **GAVG/cmd (esxtop)** | Latenza percepita dal guest (DAVG + KAVG). |
| **QAVG/cmd (esxtop)** | Latenza dovuta alla coda nel kernel VMware. |
| **vscsiStats** | Tool ESXi per istogrammi dettagliati di block size, latenza, outstanding I/O per VM. |
| **virtio-scsi-single** | Controller Proxmox che crea un controller SCSI dedicato per ogni disco; permette iothread separati. |
| **iothread** | Thread dedicato in QEMU per gestire l'I/O di un singolo disco; riduce contention. |
| **`cache=none`** | Modalita disco senza host page cache; obbligatoria per high-I/O critico. |
| **`cache=directsync`** | Cache none + ogni write e implicitamente sync; per workload con requisiti ACID estremi. |
| **`cache=writeback`** | Host page cache attiva con writeback async; pericoloso in caso di crash. |
| **raw (formato disco)** | Formato senza overhead, IOPS diretti al backend. |
| **qcow2** | Formato QEMU con supporto snapshot, thin provisioning; overhead ~5-15% su high-I/O. |
| **LVM-thin** | Volume manager Linux con thin provisioning; backend ad alta performance per Proxmox. |
| **ZFS ARC** | Adaptive Replacement Cache di ZFS; cache in RAM per pagine recentemente accedute. |
| **ZFS recordsize** | Dimensione dei blocchi logici ZFS; allineare al block size dominante del workload. |
| **Ceph RBD** | RADOS Block Device; presentazione di volumi Ceph come block device. |
| **Ceph deep-scrub** | Verifica integrita periodica di tutti i blocchi degli OSD; impatto I/O significativo. |
| **NUMA (Non-Uniform Memory Access)** | Architettura multi-socket con memoria locale e remota. |
| **NUMA node** | Insieme di core CPU + memoria locale + dispositivi PCIe locali. |
| **CPU pinning** | Vincolare un processo (es. QEMU) a uno specifico set di core. |
| **Jumbo frames** | Frame Ethernet con MTU 9000 (vs 1500 default); riduce overhead per traffico storage. |
| **Bond LACP (802.3ad)** | Aggregazione link Ethernet con negoziazione attiva LACP. |
| **`xmit-hash-policy layer3+4`** | Policy bond che distribuisce flussi in base a IP+porta; favorisce uso bilanciato dei link. |
| **CPU steal time (`%st`)** | Percentuale di tempo in cui il guest pensa di aver perso CPU per altri tenant; indica overcommit. |
| **THP (Transparent Hugepage)** | Feature kernel che promuove page 4K a hugepage 2M dinamicamente; spesso dannoso per DB. |
| **`vm.swappiness`** | Tendenza del kernel a usare swap; basso (10) per server, alto (60) per desktop. |
| **`vm.dirty_ratio`** | % RAM con pagine sporche prima che il processo scrivente sia bloccato. |
| **`vm.dirty_background_ratio`** | % RAM con pagine sporche oltre il quale il kernel inizia writeback async. |
| **APST (NVMe)** | Autonomous Power State Transitions; risparmio energetico NVMe; disabilitare in produzione. |
| **fio** | Flexible I/O Tester; benchmark de facto per workload I/O Linux. |
