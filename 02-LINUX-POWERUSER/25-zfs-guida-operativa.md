# ZFS su Linux: Guida Operativa — Guida Approfondita

> **Modulo 25** · **Versione:** OpenZFS 2.2/2.3 · **Aggiornamento:** 2026-05-24

## Idee guida
1. **Degraded recovery: `zpool replace` con vdev ETA math.**
2. **Scrub I/O impact: schedula in basso carico; cancellabile.**
3. **Snapshot retention policy via sanoid.**
4. **ARC tuning: `zfs_arc_max` esplicito su Linux.**
5. **`O_DIRECT` non implementato 2.1, opzionale 2.2+ (CSI).**
6. **RAIDZ expansion (OpenZFS 2.3): `zpool attach` su vdev raidz esistente.**


## Indice

- [Panoramica](#panoramica)
- [Architettura ZFS](#architettura-zfs)
- [ARC: Adaptive Replacement Cache](#arc-adaptive-replacement-cache)
- [ZIL e SLOG](#zil-e-slog)
- [L2ARC: Level 2 ARC](#l2arc-level-2-arc)
- [Installazione su Linux](#installazione-su-linux)
- [Pool: Creazione e Gestione](#pool-creazione-e-gestione)
- [Tipi di VDEV: Mirror, RAIDZ, dRAID](#tipi-di-vdev-mirror-raidz-draid)
- [Dataset e Proprietà](#dataset-e-proprietà)
- [Dataset vs Zvol](#dataset-vs-zvol)
- [Compressione](#compressione)
- [Deduplication](#deduplication)
- [Snapshot e Cloni](#snapshot-e-cloni)
- [Send/Receive per Backup e Replicazione](#sendreceive-per-backup-e-replicazione)
- [Encryption Nativa](#encryption-nativa)
- [Special VDEV e Allocation Classes](#special-vdev-e-allocation-classes)
- [Manutenzione: Scrub e Sostituzione Dischi](#manutenzione-scrub-e-sostituzione-dischi)
- [Performance Tuning Avanzato](#performance-tuning-avanzato)
- [OpenZFS su Linux: Specificità](#openzfs-su-linux-specificità)
- [ZFS su Proxmox — Pattern di Integrazione](#zfs-su-proxmox--pattern-di-integrazione)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Domande Frequenti (Q&A)](#domande-frequenti-qa)
- [Esercizi Pratici](#esercizi-pratici)
- [Riferimenti](#riferimenti)

---

## Panoramica

ZFS (Zettabyte File System) è un filesystem e volume manager combinati, originariamente sviluppato da Sun Microsystems per Solaris nel 2005 e portato su Linux tramite il progetto OpenZFS. ZFS si distingue da tutti gli altri filesystem Linux per la sua integrità dei dati garantita tramite checksum end-to-end, la capacità di auto-riparazione (self-healing), snapshot istantanei a costo zero, compressione trasparente e un modello di gestione che elimina la necessità di strumenti separati per RAID, LVM e filesystem.

Per un system administrator Linux, ZFS rappresenta un cambio di paradigma: anziché gestire dischi fisici → partizioni → RAID hardware/software → LVM → filesystem come componenti separati con i propri strumenti e le proprie failure mode, ZFS unifica tutto in un unico stack coerente. Questo non è solo più comodo — è fondamentalmente più sicuro, perché ogni livello conosce e verifica l'integrità degli altri.

L'adozione di ZFS su Linux è cresciuta significativamente grazie a OpenZFS 2.x, che ha raggiunto parità di funzionalità con la versione Solaris e introduce funzionalità come la compressione zstd, il sequential resilver e l'encryption nativa. Distribuzioni come Ubuntu offrono ZFS come opzione di installazione root fin dalla versione 19.10, e Proxmox VE lo usa come storage primario.

### Perché ZFS e non ext4/XFS + mdadm + LVM

La domanda più frequente è: perché non usare la combinazione tradizionale? La risposta sta nell'integrità end-to-end.

```
Stack tradizionale:                    Stack ZFS:
┌──────────────┐                       ┌──────────────┐
│ ext4 / XFS   │ ← Non verifica       │ ZFS          │ ← Checksum per ogni blocco
├──────────────┤   l'integrità dei     │              │   nel blocco padre.
│ LVM          │   dati letti da       │              │   Se rileva corruzione,
├──────────────┤   sotto.              │              │   auto-ripara da copia
│ mdadm        │ ← RAID non sa        │              │   ridondante.
├──────────────┤   se i dati sono      │              │   COW garantisce
│ Dischi       │   corretti, solo      │              │   consistenza atomica.
└──────────────┘   se sono presenti.   └──────────────┘
```

In un sistema tradizionale, un bit flip silenzioso su disco passa inosservato attraverso mdadm e LVM fino al filesystem, che lo serve all'applicazione come dato valido. ZFS rileva questa corruzione grazie ai checksum e, se il dato esiste su un mirror o raidz, lo ripara automaticamente. Questo fenomeno — la corruzione silenziosa dei dati (bit rot) — è documentato e misurabile: studi di CERN e NetApp stimano tassi di 1 corruzione non rilevata ogni 10^14-10^15 bit letti, sufficiente a colpire pool multi-terabyte nell'arco di mesi.

---

## Architettura ZFS

### Struttura a Livelli

```
┌──────────────────────────────────────────────────────────────┐
│                     Dataset Layer                             │
│  (filesystem, volume, snapshot, bookmark, clone)              │
│  Gestisce namespace gerarchico, proprietà ereditabili,        │
│  montaggio automatico.                                        │
├──────────────────────────────────────────────────────────────┤
│                     DSL (Dataset and Snapshot Layer)           │
│  Gestisce la relazione tra dataset, snapshot e cloni.          │
│  Mantiene il DAG (Directed Acyclic Graph) dei block pointer.  │
├──────────────────────────────────────────────────────────────┤
│                     DMU (Data Management Unit)                │
│  Modello transazionale ad oggetti. Ogni oggetto (file, dir,   │
│  metadati) è un set di blocchi gestiti tramite dnode.          │
│  Implementa il Copy-on-Write (COW) a livello di blocco.       │
├──────────────────────────────────────────────────────────────┤
│                     ARC (Adaptive Replacement Cache)           │
│  Cache di lettura in RAM. Algoritmo MRU/MFU con ghost list.   │
│  L2ARC opzionale su SSD per estendere la cache.               │
├──────────────────────────────────────────────────────────────┤
│                     ZIO (ZFS I/O Pipeline)                     │
│  Pipeline di I/O a stadi: compress → encrypt → checksum →     │
│  RAID → disk I/O. Ogni stadio è parallelizzabile.             │
├──────────────────────────────────────────────────────────────┤
│                     SPA (Storage Pool Allocator)               │
│  Gestisce lo spazio libero nel pool tramite metaslab.          │
│  Allocation classes per special vdev.                          │
├──────────────────────────────────────────────────────────────┤
│                     VDEV Layer                                 │
│  Astrazione dei dispositivi virtuali: mirror, raidz, draid,   │
│  spare, cache, log, special, dedup.                           │
├──────────────────────────────────────────────────────────────┤
│                     Physical Devices                           │
│  HDD, SSD, NVMe, file-backed, disk/by-id/*                   │
└──────────────────────────────────────────────────────────────┘
```

### Copy-on-Write (COW)

ZFS non sovrascrive mai i dati esistenti. Ogni modifica viene scritta in una nuova posizione e il puntatore viene aggiornato atomicamente nel blocco padre, fino alla radice dell'albero (uberblock). Questo garantisce consistenza anche in caso di crash.

```
Stato iniziale:          Dopo scrittura COW:
                         (blocco B modificato → B')

Uberblock ──→ Root      Uberblock' ──→ Root'
               │                        │
          ┌────┴────┐              ┌────┴────┐
          A         B              A         B'  ← nuovo blocco
          │         │              │         │
        dati      dati           dati      dati'

Il vecchio Uberblock, Root e B rimangono intatti su disco
fino a quando lo spazio non viene riciclato.
Se il sistema crasha durante la scrittura di B', l'uberblock
vecchio è ancora valido → il filesystem è sempre consistente.
```

### Transaction Groups (TXG)

Le scritture vengono raggruppate in transazioni atomiche chiamate TXG. Ogni TXG accumula modifiche per un intervallo configurabile (default 5 secondi, configurabile con `zfs_txg_timeout`), poi le committa tutte atomicamente su disco.

```bash
# Il ciclo dei TXG:
# TXG N   : aperto, accetta nuove modifiche
# TXG N-1 : in fase di quiesce (nessuna nuova modifica accettata)
# TXG N-2 : in fase di sync (scrittura su disco)
#
# Tre TXG coesistono sempre: open, quiescing, syncing

# Parametri di tuning TXG
cat /sys/module/zfs/parameters/zfs_txg_timeout
# 5  (secondi — intervallo massimo tra commit)

# In caso di write-heavy workload, ridurre per limitare la dimensione del TXG:
echo 3 > /sys/module/zfs/parameters/zfs_txg_timeout
```

### Checksum e Auto-Healing

Ogni blocco dati ha un checksum memorizzato nel blocco padre (non nel blocco stesso). La separazione tra dato e checksum è fondamentale: un blocco corrotto non può "mentire" sul proprio checksum.

```
         Parent Block
         ┌──────────────────────┐
         │ ptr_A  cksum_A       │ ← checksum di A nel parent
         │ ptr_B  cksum_B       │ ← checksum di B nel parent
         └──────────────────────┘
              │          │
        ┌─────▼────┐ ┌──▼──────┐
        │ Block A  │ │ Block B │
        │ (data)   │ │ (data)  │
        └──────────┘ └─────────┘

Se Block A è corrotto, il parent rileva il mismatch del checksum.
Se esiste una copia ridondante (mirror/raidz), ZFS ricostruisce
il blocco corretto e sovrascrive quello corrotto → self-healing.
```

Algoritmi di checksum disponibili:

| Algoritmo | Velocità | Sicurezza | Note |
|-----------|----------|-----------|------|
| `fletcher2` | Velocissimo | Bassa | Legacy, non usare |
| `fletcher4` | Molto veloce | Moderata | Default pre-2.0 |
| `sha256` | Lento | Alta | Necessario per dedup |
| `skein` | Veloce | Alta | Buon compromesso |
| `edonr` | Molto veloce | Alta | Raccomandato se disponibile |
| `blake3` | Molto veloce | Alta | OpenZFS 2.2+, raccomandato |

```bash
# Verifica algoritmo corrente
zfs get checksum tank/data
# NAME       PROPERTY  VALUE      SOURCE
# tank/data  checksum  on         default  (= fletcher4)

# Imposta checksum più robusto
zfs set checksum=blake3 tank/data

# Per la deduplication è necessario sha256 o skein
zfs set checksum=sha256 tank/data/dedup-pool
```

---

## ARC: Adaptive Replacement Cache

L'ARC è la cache di lettura primaria di ZFS, memorizzata in RAM. A differenza della semplice page cache del kernel Linux (LRU), l'ARC usa un algoritmo adattivo che bilancia automaticamente tra due strategie di caching.

### Architettura Interna dell'ARC

```
                         ARC in RAM
┌───────────────────────────────────────────────────┐
│                                                    │
│  MRU (Most Recently Used)     MFU (Most Frequently │
│  ┌─────────────────────┐      Used)                │
│  │ Blocchi acceduti     │      ┌─────────────────┐ │
│  │ di recente, forse    │      │ Blocchi acceduti│ │
│  │ non di nuovo.        │      │ spesso, alta    │ │
│  │                      │      │ probabilità di  │ │
│  │ Cattura: scan        │      │ riuso.          │ │
│  │ sequenziali, query   │      │                 │ │
│  │ one-shot.            │      │ Cattura: indici │ │
│  │                      │      │ DB, metadati    │ │
│  │                      │      │ directory.      │ │
│  └─────────────────────┘      └─────────────────┘ │
│                                                    │
│  Ghost MRU (T1)               Ghost MFU (T2)       │
│  ┌─────────────────────┐      ┌─────────────────┐ │
│  │ Metadati di blocchi  │      │ Metadati di     │ │
│  │ evicted da MRU.      │      │ blocchi evicted │ │
│  │ Se un blocco ghost   │      │ da MFU.         │ │
│  │ MRU viene ri-        │      │ Se ri-richiesto │ │
│  │ richiesto → ARC      │      │ → ARC favorisce │ │
│  │ favorisce MRU.       │      │ MFU.            │ │
│  └─────────────────────┘      └─────────────────┘ │
│                                                    │
│  L'ARC adatta il bilanciamento MRU/MFU in base     │
│  a quale ghost list riceve più hit.                 │
└───────────────────────────────────────────────────┘
```

Il meccanismo delle ghost list è ciò che rende l'ARC superiore a un semplice LRU: l'ARC "ricorda" cosa è stato evicted e usa questa informazione per decidere se favorire i dati recenti (MRU) o i dati frequenti (MFU). Questo lo rende particolarmente efficace per workload misti dove coesistono scan sequenziali e accessi random.

### Statistiche e Monitoraggio ARC

```bash
# Statistiche ARC complete
cat /proc/spl/kstat/zfs/arcstats

# Tool dedicato (installato con zfsutils-linux)
arc_summary

# Output chiave:
# ARC Size:                   7.82 GiB
# Target Size:                7.94 GiB
# Min Size (c_min):           1.00 GiB
# Max Size (c_max):           7.94 GiB
#
# ARC Efficiency:
#   Cache Hit Ratio:          97.23%
#   Cache Miss Ratio:          2.77%
#   MRU Hit Ratio:            42.31%
#   MFU Hit Ratio:            54.92%
#   Prefetch Hit Ratio:        8.14%
#   Demand Hit Ratio:         89.09%

# Monitoraggio in tempo reale
arcstat 2   # aggiornamento ogni 2 secondi
# Output:
#     time  read  miss  miss%  dmis  dm%  pmis  pm%  mmis  mm%  arcsz     c
# 14:30:01   45K   892   1.9   533  1.2   359  2.8   892  1.9  7.8G  7.9G

# Metriche chiave:
# - miss% (totale): < 5% è buono, < 2% è eccellente
# - dm% (demand miss): miss per richieste dirette (non prefetch)
# - arcsz: dimensione attuale dell'ARC
# - c: target size (l'ARC si espande/contrae verso questo valore)
```

### Tuning ARC

```bash
# ── Configurazione Persistente ──────────────────────────────
# /etc/modprobe.d/zfs.conf

# Limite massimo ARC (in byte)
# Default: ~50% della RAM totale
# Per server ZFS dedicato: fino all'80% della RAM
# Per server con altri servizi: 25-50% della RAM
options zfs zfs_arc_max=8589934592    # 8 GB
options zfs zfs_arc_min=2147483648    # 2 GB

# ── Applicazione immediata (senza reboot) ────────────────────
echo 8589934592 > /sys/module/zfs/parameters/zfs_arc_max
echo 2147483648 > /sys/module/zfs/parameters/zfs_arc_min

# ── Calcolo rapido della dimensione in byte ──────────────────
# 1 GB = 1073741824
# 2 GB = 2147483648
# 4 GB = 4294967296
# 8 GB = 8589934592
# 16 GB = 17179869184
# 32 GB = 34359738368
# python3 -c "print(int(8 * 1024**3))"  # → 8589934592

# ── Parametri ARC avanzati ───────────────────────────────────

# Proporzione ARC riservata ai metadati (0-100%)
# I metadati (dnode, indirect block) sono critici per le performance.
# Se i metadati vengono evicted, ogni operazione richiede I/O su disco.
cat /sys/module/zfs/parameters/zfs_arc_meta_limit_percent
# 75 (default: fino al 75% dell'ARC per metadati)

# Soglia sotto la quale l'ARC non scende per la pressione di memoria
cat /sys/module/zfs/parameters/zfs_arc_sys_free
# In byte — spazio che ZFS lascia libero per il kernel

# Priorità dell'ARC rispetto alla page cache del kernel
# 0 = l'ARC viene shrinkato aggressivamente sotto pressione
# 1-10 = resistenza crescente allo shrink
cat /sys/module/zfs/parameters/zfs_arc_shrinker_limit
```

### Regole Pratiche per il Tuning ARC

| Scenario | `zfs_arc_max` | Motivazione |
|----------|---------------|-------------|
| Server ZFS puro (NAS) | 80% RAM | ZFS è l'unico consumatore |
| Server con PostgreSQL | 25-30% RAM | PostgreSQL usa `shared_buffers` |
| Server con MySQL/MariaDB | 25-30% RAM | InnoDB buffer pool |
| Hypervisor Proxmox | 50% RAM | Bilancio tra VM e storage |
| Desktop workstation | 25% RAM | Lasciare spazio per applicazioni |

### Profili ARC per Workload Specifici

Oltre al semplice `zfs_arc_max`, il tuning ARC avanzato richiede la regolazione di parametri che controllano come la memoria ARC viene suddivisa internamente tra metadati, dnode e dati.

```bash
# ── Profilo: NAS / File Server con milioni di file ─────────
# I metadati (directory listing, stat) sono critici.
# Molti file piccoli → molti dnode da mantenere in ARC.
cat > /etc/modprobe.d/zfs-nas.conf <<'EOF'
options zfs zfs_arc_max=34359738368
options zfs zfs_arc_min=8589934592
options zfs zfs_arc_meta_limit_percent=85
options zfs zfs_arc_dnode_limit_percent=50
options zfs zfs_arc_sys_free=2147483648
EOF
# zfs_arc_meta_limit_percent=85: fino all'85% dell'ARC per metadati
#   (default 75%). NAS con milioni di file ha bisogno di più spazio
#   per i metadati — un miss sui metadati causa seek su HDD.
# zfs_arc_dnode_limit_percent=50: fino al 50% dello spazio metadati
#   per i dnode. I dnode rappresentano i file/directory stessi.
# zfs_arc_sys_free=2G: lascia almeno 2 GB liberi per il kernel.
#   Su server con poca RAM, questo impedisce l'OOM killer.

# ── Profilo: Database Server (PostgreSQL/MySQL) ────────────
# Il database ha il proprio buffer cache → l'ARC deve essere piccolo
# e focalizzato sui metadati ZFS.
cat > /etc/modprobe.d/zfs-database.conf <<'EOF'
options zfs zfs_arc_max=4294967296
options zfs zfs_arc_min=1073741824
options zfs zfs_arc_meta_limit_percent=90
options zfs zfs_arc_dnode_limit_percent=30
options zfs zfs_txg_timeout=3
options zfs zfs_arc_sys_free=4294967296
EOF
# zfs_arc_max=4G: piccolo, la maggior parte della RAM va al DB.
# zfs_arc_meta_limit_percent=90: quasi tutto l'ARC per metadati,
#   perché primarycache=metadata sul dataset del DB.
# zfs_txg_timeout=3: commit più frequenti → meno dati a rischio
#   in caso di crash, ma più overhead di commit.
# zfs_arc_sys_free=4G: lascia ampio spazio per shared_buffers
#   (PostgreSQL) o InnoDB buffer pool (MySQL).

# ── Profilo: Hypervisor (Proxmox/KVM) ──────────────────────
# Bilancio tra VM e storage. L'ARC serve per i metadati dei
# zvol delle VM e per la cache dei dati delle VM attive.
cat > /etc/modprobe.d/zfs-hypervisor.conf <<'EOF'
options zfs zfs_arc_max=17179869184
options zfs zfs_arc_min=4294967296
options zfs zfs_arc_meta_limit_percent=75
options zfs zfs_arc_dnode_limit_percent=25
options zfs zfs_arc_sys_free=4294967296
options zfs zvol_request_sync=0
EOF
# zfs_arc_max=16G: ~50% di 32 GB di RAM totale (esempio).
# zvol_request_sync=0: disabilita il sync forzato per zvol.
#   Le VM gestiscono il proprio sync interno (write barrier).
#   ATTENZIONE: rischio di perdita dati se il guest non fa
#   flush correttamente. Usare con guest Linux moderni.

# ── Profilo: Backup / Archivio (streaming sequenziale) ─────
# Workload dominato da letture/scritture sequenziali grandi.
# L'ARC è meno utile — i dati vengono letti una volta sola.
cat > /etc/modprobe.d/zfs-backup.conf <<'EOF'
options zfs zfs_arc_max=4294967296
options zfs zfs_arc_min=1073741824
options zfs zfs_arc_meta_limit_percent=75
options zfs zfs_prefetch_disable=0
options zfs zfs_txg_timeout=10
options zfs zfs_dirty_data_max_percent=40
EOF
# zfs_arc_max=4G: l'ARC non serve per dati sequenziali.
# zfs_prefetch_disable=0: il prefetch è utile per i pattern
#   sequenziali di backup/restore.
# zfs_txg_timeout=10: TXG più lunghi = batch più grandi =
#   throughput sequenziale migliore.
# zfs_dirty_data_max_percent=40: permette al 40% della RAM
#   di essere usata come dirty buffer (default 10%).
#   Migliora il throughput di scrittura per grandi trasferimenti.
```

### Monitoraggio Avanzato dell'ARC

```bash
# ── Distribuzione dello spazio ARC ─────────────────────────
# Usa arc_summary per una vista dettagliata
arc_summary | grep -A 20 "ARC Size"

# Metriche chiave da monitorare:
# 1. arc_meta_used vs arc_meta_limit → se meta_used è al limite,
#    i metadati vengono evicted e le operazioni su directory rallentano
# 2. arc_dnode_evicts → se alto, serve più spazio dnode in ARC
# 3. demand_data_hits vs demand_data_misses → efficacia cache dati
# 4. demand_metadata_hits vs demand_metadata_misses → efficacia metadati
# 5. mru_hits vs mfu_hits → bilanciamento tra recency e frequency

# Monitoraggio continuo con watch
watch -n 5 'arc_summary 2>/dev/null | head -40'

# Esportazione metriche per Prometheus/Grafana
# Il tool zfs_exporter (https://github.com/pdf/zfs_exporter)
# espone le metriche ARC, pool e dataset come endpoint Prometheus
```

---

## ZIL e SLOG

Il ZIL (ZFS Intent Log) e il SLOG (Separate LOG device) sono concetti distinti che vengono spesso confusi.

### ZIL: ZFS Intent Log

Il ZIL è un meccanismo di logging delle scritture sincrone. Quando un'applicazione richiede una scrittura sincrona (`fsync()`, `O_SYNC`), ZFS deve garantire che il dato sia su storage non volatile prima di confermare la scrittura.

```
Flusso di una scrittura SINCRONA:
                                                    
Applicazione                                        
    │ write() + fsync()                             
    ▼                                               
ZFS riceve la richiesta                             
    │                                               
    ├──→ Scrive nel ZIL ──→ Conferma all'app        
    │    (solo per durabilità                        
    │     in caso di crash)                         
    │                                               
    └──→ Scrive nel TXG corrente                    
         (scrittura effettiva nel pool,             
          avviene al sync del TXG)                  

In caso di crash:
- I dati nel TXG non committato sono persi
- MA i dati nel ZIL vengono "replayed" al boot
- L'applicazione ha ricevuto conferma → i dati sono salvi
```

```
Flusso di una scrittura ASINCRONA:

Applicazione
    │ write() (senza fsync)
    ▼
ZFS riceve la richiesta
    │
    └──→ Scrive nel TXG corrente ──→ Conferma all'app
         (il ZIL NON viene usato)

In caso di crash prima del sync del TXG:
- I dati nel TXG non committato sono persi
- L'applicazione ha ricevuto conferma → DATI PERSI
- Questo è il comportamento standard di tutti i filesystem
```

Il ZIL per default è allocato nel pool stesso (su HDD/SSD che compongono il pool). Questo significa che ogni `fsync()` attende la latenza del disco più lento del pool.

### SLOG: Separate LOG Device

Il SLOG è un dispositivo dedicato (tipicamente NVMe ad alta endurance) su cui viene posizionato il ZIL. Lo scopo è accelerare le scritture sincrone spostando il ZIL dai dischi lenti del pool a un dispositivo veloce.

```bash
# Aggiungi SLOG al pool (MIRROR raccomandato)
# La perdita del SLOG durante una scrittura attiva può causare perdita dati
zpool add tank log mirror /dev/nvme0n1p1 /dev/nvme1n1p1

# Verifica SLOG
zpool status tank
# NAME                     STATE     READ WRITE CKSUM
# tank                     ONLINE       0     0     0
#   mirror-0               ONLINE       0     0     0
#     sda                  ONLINE       0     0     0
#     sdb                  ONLINE       0     0     0
#   logs
#     mirror-1             ONLINE       0     0     0
#       nvme0n1p1          ONLINE       0     0     0
#       nvme1n1p1          ONLINE       0     0     0

# Rimuovi SLOG (sicuro — il ZIL torna nel pool)
zpool remove tank mirror-1
```

### Quando il SLOG è Necessario

| Workload | fsync frequenti? | SLOG utile? |
|----------|-------------------|-------------|
| Database (PostgreSQL, MySQL) | Sì, ogni commit | **Molto utile** |
| NFS server | Sì, default sync | **Molto utile** |
| iSCSI target | Sì, sync writes | **Molto utile** |
| File server Samba (SMB) | Dipende | Moderatamente utile |
| Backup / archivio | No, async | **Non necessario** |
| VM con write-through | Sì | **Molto utile** |
| VM con write-back | No | Non necessario |
| Streaming video / media | No | Non necessario |

### Requisiti per il dispositivo SLOG

```
Requisiti SLOG:
1. Bassa latenza di scrittura (< 100μs ideale)
2. Alta endurance (DWPD elevato — il SLOG viene scritto continuamente)
3. Power-loss protection (PLB/PLP) — FONDAMENTALE
   Senza PLP, un power-loss durante la scrittura del SLOG
   può corrompere il ZIL → perdita dati
4. Dimensione piccola: 8-32 GB sono sufficienti
   (il SLOG memorizza solo secondi di dati, poi il TXG committa)
5. Mirror raccomandato: la perdita del SLOG è più grave
   della perdita di un disco dati (in caso di crash attivo)

Dispositivi raccomandati:
- Intel Optane (ideale: latenza ~10μs, alta endurance)
- SSD enterprise con PLP (Samsung PM9A3, Micron 7450)
- NON usare SSD consumer (no PLP, bassa endurance)
```

---

## L2ARC: Level 2 ARC

L'L2ARC è una cache di secondo livello su SSD/NVMe che estende l'ARC oltre i limiti della RAM. I dati evicted dall'ARC vengono scritti sull'L2ARC prima di essere scartati, creando un livello intermedio tra RAM e disco.

### Architettura L2ARC

```
Gerarchia di cache:

Livello 1: ARC (RAM)          — Latenza ~100ns
    │ evict
    ▼
Livello 2: L2ARC (SSD/NVMe)   — Latenza ~100μs
    │ miss
    ▼
Livello 3: Pool dischi (HDD)   — Latenza ~5-10ms
```

### Configurazione L2ARC

```bash
# Aggiungi L2ARC al pool (NON serve mirror — la perdita dell'L2ARC
# non causa perdita dati, solo perdita della cache)
zpool add tank cache /dev/nvme0n1p3

# Verifica utilizzo L2ARC
zpool iostat -v tank
# NAME                    ALLOC   FREE  READ  WRITE
# tank                    1.23T   2.77T  342    89
#   mirror-0              1.23T   2.77T  127    89
#     sda                     -       -   64    45
#     sdb                     -       -   63    44
#   cache
#     nvme0n1p3            180G    320G  215     0

# Statistiche L2ARC dettagliate
cat /proc/spl/kstat/zfs/arcstats | grep l2_
# l2_hits                  4    12847392
# l2_misses                4    2341567
# l2_feeds                 4    892341
# l2_size                  4    193273528320
# l2_hdr_size              4    284567232

# Hit ratio L2ARC
# l2_hits / (l2_hits + l2_misses) * 100 = L2ARC hit ratio
# 12847392 / (12847392 + 2341567) * 100 = 84.6%

# Tuning L2ARC — velocità di populating
echo 209715200 > /sys/module/zfs/parameters/l2arc_write_max
# 200 MB/s — velocità massima di scrittura nell'L2ARC

echo 104857600 > /sys/module/zfs/parameters/l2arc_write_boost
# 100 MB/s — boost durante il warm-up iniziale

# Persistenza L2ARC (OpenZFS 2.0+)
# L'L2ARC sopravvive al reboot — fondamentale per evitare
# warm-up di ore dopo ogni riavvio
zpool set feature@persistent_l2arc=enabled tank

# Verifica che la feature sia abilitata
zpool get feature@persistent_l2arc tank
# NAME  PROPERTY                VALUE   SOURCE
# tank  feature@persistent_l2arc active  local
```

### Parametri L2ARC Avanzati

```bash
# ── Velocità di populating ──────────────────────────────────
# l2arc_write_max: velocità massima di scrittura nell'L2ARC
# Default: 8 MB/s — troppo lento per NVMe moderni
echo 268435456 > /sys/module/zfs/parameters/l2arc_write_max
# 256 MB/s — appropriato per SSD SATA
# Per NVMe: fino a 536870912 (512 MB/s)

# l2arc_write_boost: velocità durante il warm-up iniziale
# Attivo finché l'L2ARC non è popolato al primo ciclo
echo 536870912 > /sys/module/zfs/parameters/l2arc_write_boost
# 512 MB/s — warm-up più rapido dopo reboot

# ── Filtro dei dati cachati ─────────────────────────────────
# l2arc_headroom: profondità di ricerca nelle liste ARC
# Valore = moltiplicatore di l2arc_write_max
# Più alto = più candidati per la cache, ma più CPU
cat /sys/module/zfs/parameters/l2arc_headroom
# 2 (default)
# 0 = cerca nell'intera lista ARC (utile per L2ARC persistente)
# Impostare a 0 per massimizzare il hit rate dell'L2ARC

# l2arc_mfuonly: controlla quali dati vengono cachati in L2ARC
cat /sys/module/zfs/parameters/l2arc_mfuonly
# 0 = cacha sia MRU che MFU (default pre-2.2)
# 1 = cacha solo MFU (dati acceduti frequentemente)
#     Raccomandato per workload con scan sequenziali misti.
#     Evita di riempire l'L2ARC con dati letti una volta sola.
# 2 = cacha tutti i metadati (MRU+MFU) ma solo dati MFU
#     Buon compromesso: i metadati sono sempre utili,
#     ma i dati devono dimostrarsi "caldi" prima di entrare.
echo 2 > /sys/module/zfs/parameters/l2arc_mfuonly

# l2arc_noprefetch: controlla se i dati prefetch vanno in L2ARC
cat /sys/module/zfs/parameters/l2arc_noprefetch
# 1 = non cachare dati da prefetch (default)
#     Buono per evitare inquinamento da read-ahead
# 0 = cachare anche dati da prefetch
#     Utile per workload con pattern sequenziali ripetitivi
#     (es. backup ripetuti dello stesso dataset)

# l2arc_rebuild_enabled: persistenza L2ARC tra reboot
cat /sys/module/zfs/parameters/l2arc_rebuild_enabled
# 1 = abilitato (default OpenZFS 2.0+)
# L'L2ARC sopravvive al reboot — evita ore di warm-up
# Richiede la feature persistent_l2arc abilitata nel pool

# ── Configurazione Persistente L2ARC ───────────────────────
cat >> /etc/modprobe.d/zfs.conf <<'EOF'
options zfs l2arc_write_max=268435456
options zfs l2arc_write_boost=536870912
options zfs l2arc_headroom=0
options zfs l2arc_mfuonly=2
options zfs l2arc_noprefetch=1
options zfs l2arc_rebuild_enabled=1
EOF
```

#### Dimensionamento L2ARC per Workload

| Workload | Dimensione L2ARC | `l2arc_mfuonly` | `l2arc_noprefetch` | Note |
|----------|-------------------|-----------------|---------------------|------|
| NAS con file misti | 200-500 GB | 2 | 1 | Metadati caldi + file frequenti |
| Database (hot standby) | 100-200 GB | 1 | 1 | Solo dati acceduti spesso |
| VM / Hypervisor | 200-500 GB | 0 | 0 | Le VM hanno pattern vari |
| Media streaming | Non raccomandato | — | — | Sequenziale, nessun riuso |
| Backup/archivio | Non raccomandato | — | — | Dati letti una volta sola |
| Build server / CI | 100-300 GB | 1 | 1 | Artefatti riusati spesso |

### Quando l'L2ARC è Utile

L'L2ARC ha un costo: consuma circa 70-100 byte di ARC (RAM) per ogni blocco cachato in L2ARC. Se l'L2ARC è grande e l'ARC è piccolo, il metadata overhead può ridurre l'ARC effettivo.

| Scenario | L2ARC utile? | Ragionamento |
|----------|-------------|--------------|
| Pool HDD, ARC piccolo, working set grande | **Sì** | I dati caldi non entrano nell'ARC |
| Pool interamente SSD | **No** | L'SSD del pool è già veloce |
| ARC > working set | **No** | Tutto sta già nell'ARC |
| Molti file piccoli, accesso random | **Sì** | L2ARC accelera i metadata lookup |

---

## Installazione su Linux

### Debian/Ubuntu

```bash
# Ubuntu 20.04+ ha ZFS nei repository main
sudo apt install zfsutils-linux

# Verifica
zfs version
# zfs-2.2.x-...
# zfs-kmod-2.2.x-...

modprobe zfs
lsmod | grep zfs
```

### RHEL/Fedora

```bash
# Aggiungi il repository OpenZFS
dnf install https://zfsonlinux.org/epel/zfs-release-2-3$(rpm --eval "%{dist}").noarch.rpm

# Installa con DKMS (compila per il tuo kernel)
dnf install kernel-devel zfs

# Oppure usa kABI-tracking kmod (precompilato)
dnf install zfs-kmod zfs

# Carica il modulo
modprobe zfs
```

### Arch Linux

```bash
# Installa da AUR o dal repository extra
pacman -S zfs-dkms zfs-utils

# Oppure per kernel LTS
pacman -S zfs-linux-lts
```

### Verifica Post-Installazione

```bash
# Verifica modulo kernel
lsmod | grep zfs
# zfs                  4194304  0
# zunicode              335872  1 zfs
# zzstd                 548864  1 zfs
# zlua                  200704  1 zfs
# zavl                   16384  1 zfs
# icp                   335872  1 zfs
# spl                   131072  5 zfs,zunicode,zzstd,zlua,icp

# Verifica comandi disponibili
which zpool && which zfs && which zdb

# Stato servizi
systemctl status zfs-import-cache
systemctl status zfs-mount
systemctl status zfs.target

# Abilita servizi per auto-import al boot
systemctl enable zfs-import-cache
systemctl enable zfs-mount
systemctl enable zfs.target

# Verifica versione OpenZFS e feature supportate
zpool upgrade -v
```

---

## Pool: Creazione e Gestione

### Creazione Pool

```bash
# ── REGOLA FONDAMENTALE: usa SEMPRE /dev/disk/by-id/ ─────────
# /dev/sdX cambia tra reboot; by-id è stabile
ls -la /dev/disk/by-id/ | grep -v part

# Pool semplice con mirror (2 dischi)
zpool create tank mirror \
    /dev/disk/by-id/ata-WDC_WD4003FFBX-1234 \
    /dev/disk/by-id/ata-WDC_WD4003FFBX-5678

# Pool con raidz1 (3 dischi, tolleranza 1 guasto)
zpool create datastore raidz \
    /dev/disk/by-id/ata-ST4000NM000A-0001 \
    /dev/disk/by-id/ata-ST4000NM000A-0002 \
    /dev/disk/by-id/ata-ST4000NM000A-0003

# Pool con raidz2 (6 dischi, tolleranza 2 guasti)
zpool create archive raidz2 \
    /dev/disk/by-id/ata-ST8000VN004-{0001..0006}

# Pool con multipli vdev (raccomandato per performance)
# I/O viene distribuito tra i vdev — più vdev = più IOPS
zpool create bigpool \
    raidz /dev/disk/by-id/ata-disk-{1..3} \
    raidz /dev/disk/by-id/ata-disk-{4..6}

# Pool con mirror + SLOG + L2ARC
zpool create fastpool \
    mirror /dev/disk/by-id/ata-ssd-1 /dev/disk/by-id/ata-ssd-2 \
    mirror /dev/disk/by-id/ata-ssd-3 /dev/disk/by-id/ata-ssd-4 \
    log mirror /dev/disk/by-id/nvme-optane-1-part1 /dev/disk/by-id/nvme-optane-2-part1 \
    cache /dev/disk/by-id/nvme-cache-1-part1

# Specifica ashift (dimensione settore)
# ashift=12 → 4K settori (tutti gli HDD moderni e la maggior parte degli SSD)
# ashift=13 → 8K settori (alcuni NVMe)
# ashift=9  → 512 byte (solo dischi molto vecchi — MAI usare su dischi 4K)
# ATTENZIONE: ashift NON può essere cambiato dopo la creazione!
zpool create -o ashift=12 tank mirror /dev/disk/by-id/ata-disk-1 /dev/disk/by-id/ata-disk-2

# Opzioni utili alla creazione
zpool create \
    -o ashift=12 \
    -o autotrim=on \         # TRIM automatico per SSD
    -O compression=lz4 \     # compressione di default per tutti i dataset
    -O atime=off \           # disabilita access time (performance)
    -O xattr=sa \            # extended attributes nello system area
    -O dnodesize=auto \      # dnode sizing automatico (OpenZFS 2.0+)
    tank mirror /dev/disk/by-id/ata-disk-1 /dev/disk/by-id/ata-disk-2
```

### Gestione Pool

```bash
# Stato del pool
zpool status
zpool status tank
zpool status -v    # stato dettagliato con errori

# Lista pool con metriche chiave
zpool list
# NAME    SIZE  ALLOC   FREE  CKPOINT  EXPANDSZ   FRAG    CAP  DEDUP    HEALTH  ALTROOT
# tank   3.62T  1.23T  2.39T        -         -     8%    34%  1.00x    ONLINE  -

zpool list -v     # con dettagli per vdev

# I/O statistics
zpool iostat 2          # aggiornamento ogni 2 secondi
zpool iostat -v 2       # con dettaglio per vdev
zpool iostat -vl 2      # con dettaglio e latenza per vdev (OpenZFS 2.0+)

# Output con latenza:
# NAME              ALLOC  FREE  READ  WRITE  READ   WRITE
#                                             latency latency
# tank              1.23T  2.39T  342    89  123us   456us
#   mirror-0        1.23T  2.39T  342    89  123us   456us
#     sda               -      -  171    45  121us   453us
#     sdb               -      -  171    44  125us   459us

# Proprietà del pool
zpool get all tank
zpool set comment="Pool principale produzione - creato 2024-04-01" tank

# Esporta pool (per spostamento fisico o shutdown pulito)
zpool export tank

# Importa pool
zpool import                              # lista pool disponibili per import
zpool import tank                         # importa per nome
zpool import -d /dev/disk/by-id tank      # cerca in directory specifica
zpool import -f tank                      # forza import (se export non pulito)

# Storico comandi eseguiti sul pool
zpool history tank
# 2024-04-01.10:00:00 zpool create tank mirror sda sdb
# 2024-04-01.10:05:00 zfs create tank/data
# 2024-04-01.10:10:00 zfs set compression=lz4 tank/data

# Upgrade pool features
zpool upgrade                # mostra pool che possono essere aggiornati
zpool upgrade tank           # abilita tutte le feature disponibili
# ATTENZIONE: l'upgrade è irreversibile — il pool non sarà
# importabile da versioni precedenti di OpenZFS

# Eventi del pool (utile per monitoring)
zpool events                 # tutti gli eventi
zpool events -v              # dettagliato
zpool events -c              # cancella eventi
```

---

## Tipi di VDEV: Mirror, RAIDZ, dRAID

### Tabella Comparativa

| Tipo | Min Dischi | Tolleranza | Spazio Utile | IOPS | Resilver | Uso |
|------|-----------|------------|-------------|------|---------|-----|
| stripe | 1 | 0 dischi | 100% | N×disco | N/A | Solo test |
| mirror | 2 | N-1 dischi | 50% (2 dischi) | N×disco (lettura) | Veloce | OS, DB |
| raidz1 | 3 | 1 disco | (N-1)/N | ~1×disco (write) | Lento | Storage medio |
| raidz2 | 4+ | 2 dischi | (N-2)/N | ~1×disco (write) | Lento | NAS, archivio |
| raidz3 | 5+ | 3 dischi | (N-3)/N | ~1×disco (write) | Molto lento | Grandi array |
| draid1 | 5+ | 1 disco | Variabile | Variabile | **Molto veloce** | Grandi array |
| draid2 | 8+ | 2 dischi | Variabile | Variabile | **Molto veloce** | Grandi array |
| draid3 | 11+ | 3 dischi | Variabile | Variabile | **Molto veloce** | Grandi array |

### Mirror

Il mirror è il vdev più semplice e performante in lettura. Ogni dato è scritto su tutti i dischi del mirror. Le letture vengono distribuite tra i dischi.

```bash
# Mirror a 2 dischi (RAID1)
zpool create tank mirror /dev/disk/by-id/ata-disk-1 /dev/disk/by-id/ata-disk-2

# Mirror a 3 dischi (RAID1 triplo — tolleranza 2 guasti)
zpool create tank mirror \
    /dev/disk/by-id/ata-disk-1 \
    /dev/disk/by-id/ata-disk-2 \
    /dev/disk/by-id/ata-disk-3

# Multipli mirror (striped mirrors — come RAID10)
# Migliore combinazione di performance e ridondanza
zpool create tank \
    mirror /dev/disk/by-id/ata-disk-1 /dev/disk/by-id/ata-disk-2 \
    mirror /dev/disk/by-id/ata-disk-3 /dev/disk/by-id/ata-disk-4 \
    mirror /dev/disk/by-id/ata-disk-5 /dev/disk/by-id/ata-disk-6
# 6 dischi totali, 3 vdev mirror, 50% spazio, 3× IOPS in lettura e scrittura
```

### RAIDZ

RAIDZ distribuisce dati e parità su tutti i dischi del vdev, simile a RAID5/6 ma senza il "write hole" grazie al COW.

```bash
# raidz1: una parità (RAID5-like), tolleranza 1 guasto
zpool create tank raidz /dev/disk/by-id/ata-disk-{1..4}
# 4 dischi, 3 usabili → 75% efficienza

# raidz2: doppia parità (RAID6-like), tolleranza 2 guasti
zpool create tank raidz2 /dev/disk/by-id/ata-disk-{1..6}
# 6 dischi, 4 usabili → 67% efficienza

# raidz3: tripla parità, tolleranza 3 guasti
zpool create tank raidz3 /dev/disk/by-id/ata-disk-{1..8}
# 8 dischi, 5 usabili → 62.5% efficienza
```

**Quanti dischi per vdev raidz?** La regola pratica è che i vdev raidz funzionano meglio con un numero di dischi dati che è una potenza di 2:

| Configurazione | Dischi dati | Efficienza | Raccomandazione |
|----------------|-------------|------------|-----------------|
| raidz1 con 3 dischi | 2 | 67% | Minimo funzionale |
| raidz1 con 5 dischi | 4 | 80% | Buon rapporto |
| raidz1 con 9 dischi | 8 | 89% | Ottimo per throughput |
| raidz2 con 6 dischi | 4 | 67% | Buon rapporto |
| raidz2 con 10 dischi | 8 | 80% | Ottimo |
| raidz2 con 12 dischi | 10 | 83% | Massima efficienza pratica |

### dRAID (Distributed RAID) — OpenZFS 2.1+

dRAID è il tipo di vdev più recente, progettato per risolvere il problema principale di raidz: il tempo di resilver. In raidz, quando un disco muore, il resilver deve leggere TUTTI i dati dal vdev per ricostruire quelli del disco guasto. Con dischi da 10+ TB, questo può richiedere giorni.

dRAID distribuisce i dati e la parità in modo diverso: pre-alloca "distributed spare" che partecipano alla distribuzione dei dati, permettendo un resilver parallelo su tutti i dischi del vdev anziché sequenziale.

```
RAIDZ2 con 10 dischi — resilver:
Disco 1 ████████████  ← legge tutti i dati (10 TB per disco)
Disco 2 ████████████  ← legge tutti i dati
Disco 3 ████████████  ← legge tutti i dati
[...]
Disco 10 ████████████ ← legge tutti i dati
                       Scrive TUTTO sul disco sostitutivo
                       Tempo: ~24-48 ore per dischi 10TB

dRAID2 con 10 dischi + 1 spare — resilver:
Disco 1 ██           ← legge e scrive solo la sua porzione
Disco 2 ██           ← legge e scrive solo la sua porzione
Disco 3 ██           ← legge e scrive solo la sua porzione
[...]
Disco 10 ██          ← legge e scrive solo la sua porzione
                      Il resilver è distribuito su tutti i dischi
                      Tempo: ~2-4 ore (10× più veloce)
```

```bash
# dRAID1 con 10 dischi dati, 1 spare distribuito, 4 dischi per gruppo
zpool create tank draid1:4d:10c:1s /dev/disk/by-id/ata-disk-{1..11}
# 4d = 4 dischi dati per stripe group
# 10c = 10 dischi dati totali (figli)
# 1s = 1 spare distribuito

# dRAID2 con 20 dischi, 2 spare distribuiti, 8 dischi per gruppo
zpool create tank draid2:8d:20c:2s /dev/disk/by-id/ata-disk-{1..22}

# Dopo guasto di un disco, il resilver è AUTOMATICO
# (usa lo spare distribuito, non serve disco fisico di ricambio)
zpool status tank
# scan: resilver in progress
#     distributed resilver using 10 disks in parallel
#     ETA: 2h30m (vs 30h con raidz)
```

**Quando usare dRAID vs RAIDZ:**
- **dRAID**: pool con ≥10 dischi, dischi grandi (≥8TB), SLA stringenti sul tempo di resilver
- **RAIDZ**: pool piccoli (<10 dischi), quando la semplicità è prioritaria

### dRAID vs RAIDZ: Matrice Decisionale Dettagliata

La scelta tra dRAID e RAIDZ ha impatti significativi sul tempo di resilver, sull'efficienza dello spazio e sulla complessità operativa. La tabella seguente confronta i due approcci su scenari reali.

| Criterio | RAIDZ | dRAID |
|----------|-------|-------|
| **Numero minimo dischi utile** | 3 (raidz1) | 5+ (draid1), realisticamente 10+ |
| **Resilver — dischi 4 TB** | ~6-12 ore | ~1-2 ore |
| **Resilver — dischi 16 TB** | ~24-48 ore | ~3-6 ore |
| **Resilver — dischi 20 TB** | ~36-72 ore | ~4-8 ore |
| **Spare management** | Hot spare tradizionale (disco dedicato inattivo) | Distributed spare (capacità distribuita su tutti i dischi) |
| **Risposta al guasto** | Manuale: inserire disco fisico e avviare replace | Automatico: il distributed spare si attiva immediatamente |
| **IOPS in lettura** | Limitato dalla larghezza del singolo vdev | Comparabile, distribuito sugli stessi dischi |
| **Overhead di spazio per spare** | Disco intero dedicato (non contribuisce alla capacità) | Spazio distribuito (contribuisce alla distribuzione dei dati) |
| **Espandibilità (con OpenZFS 2.3)** | Sì, tramite `zpool attach` (RAIDZ expansion) | No, il layout è fisso alla creazione |
| **Complessità configurazione** | Semplice | Media (parametri `d:c:s` da calcolare) |

#### Matematica del Resilver: Perché dRAID è Più Veloce

Il vantaggio fondamentale di dRAID sta nella distribuzione del lavoro di ricostruzione. In un vdev RAIDZ con N dischi, quando un disco muore il resilver legge dati da N-1 dischi e scrive TUTTO su un singolo disco sostitutivo. La velocità è limitata dalla capacità di scrittura del singolo disco.

```
RAIDZ2 con 12 dischi da 16 TB:
- Dati da ricostruire: ~14.5 TB (dati + parità del disco guasto)
- Velocità scrittura disco singolo: ~180 MB/s (HDD sequenziale)
- Tempo = 14.5 TB / 180 MB/s ≈ 22 ore
- Durante il resilver: performance degradata, vulnerabilità a secondo guasto

dRAID2 con 12 dischi da 16 TB + 1 distributed spare:
- Dati da ricostruire: stessi ~14.5 TB
- Ma la scrittura è distribuita su 11 dischi rimanenti
- Velocità effettiva: ~180 MB/s × 11 ÷ (D+P) ≈ 8-10× più veloce
- Tempo ≈ 2-3 ore
- Il distributed spare è attivo immediatamente, senza intervento fisico
```

#### Scenari Pratici di Scelta

**Scegli RAIDZ quando:**
- Il pool ha meno di 10 dischi
- Prevedi di espandere il vdev aggiungendo dischi (RAIDZ expansion in OpenZFS 2.3)
- La semplicità di gestione è prioritaria
- I dischi sono piccoli (≤4 TB) e il resilver richiede poche ore
- Il budget non consente dischi spare aggiuntivi per dRAID

**Scegli dRAID quando:**
- Il pool ha 10+ dischi (idealmente 20+)
- I dischi sono grandi (≥8 TB) e il resilver RAIDZ richiederebbe >12 ore
- L'SLA richiede che il pool torni in stato non-degraded entro poche ore
- Il costo di un secondo guasto durante un resilver lungo è inaccettabile
- L'ambiente è un data center con molti shelf di dischi

```bash
# Esempio dRAID2 per un data center con 24 dischi da 20 TB
# 8 dischi dati per gruppo, 24 figli, 2 spare distribuiti
zpool create datacenter draid2:8d:24c:2s /dev/disk/by-id/ata-disk-{1..26}

# Verifica configurazione
zpool status datacenter
# Mostra il layout dRAID con i parametri scelti

# Se un disco muore, il resilver su distributed spare è automatico
# e si completa in 2-4 ore anziché 30+
# Quando il disco fisico viene sostituito, lo spare si "ricarica"
```

---

## Dataset e Proprietà

I dataset sono le unità logiche di organizzazione in ZFS. Ogni dataset può avere proprietà personalizzate che vengono ereditate dai dataset figli.

### Creazione e Gestione Dataset

```bash
# Crea un dataset (filesystem)
zfs create tank/data
zfs create tank/data/documents
zfs create tank/data/media

# Crea con proprietà
zfs create -o compression=zstd -o atime=off tank/data/logs

# Lista dataset
zfs list
zfs list -r tank          # ricorsivo sotto tank
zfs list -t all           # include snapshot
zfs list -o name,used,avail,refer,compressratio

# Rinomina
zfs rename tank/data/old tank/data/new

# Distruggi (ATTENZIONE: non reversibile)
zfs destroy tank/data/temp

# Distruggi ricorsivamente (include snapshot)
zfs destroy -r tank/data/old

# Punto di montaggio
zfs get mountpoint tank/data
zfs set mountpoint=/mnt/data tank/data

# Smonta/monta
zfs unmount tank/data
zfs mount tank/data
zfs mount -a    # monta tutti i dataset
```

### Proprietà Chiave

```bash
# Visualizza tutte le proprietà
zfs get all tank/data

# Proprietà specifiche
zfs get compression,compressratio,used,available tank/data

# ── Performance ──────────────────────────────────────────
zfs set atime=off tank/data              # disabilita access time
zfs set relatime=on tank/data            # alternativa meno aggressiva
zfs set xattr=sa tank/data               # extended attributes in system area
zfs set dnodesize=auto tank/data         # dnode sizing automatico
zfs set sync=standard tank/data          # standard | always | disabled

# ── Recordsize — critico per le performance ──────────────
# Il recordsize è la dimensione massima del blocco logico.
# Ogni file più piccolo del recordsize usa un singolo blocco.
# File più grandi vengono divisi in blocchi di recordsize.

zfs set recordsize=128K tank/data        # Default, buono per la maggior parte
zfs set recordsize=1M tank/data/media    # File grandi (video, backup)
zfs set recordsize=16K tank/data/pg      # PostgreSQL (page size 8K, ma 16K è ottimale)
zfs set recordsize=8K tank/data/mysql    # MySQL InnoDB (page size = 16K, ma 8K conviene)
zfs set recordsize=64K tank/data/mongo   # MongoDB (WiredTiger default)

# ── Quota e Reservation ─────────────────────────────────
zfs set quota=100G tank/data/users       # limite massimo (include snapshot)
zfs set refquota=10G tank/data/users/bob # limite escludendo snapshot
zfs set reservation=50G tank/data/db     # spazio garantito
zfs set refreservation=40G tank/data/db  # spazio garantito escludendo snapshot

# ── Ereditarietà ─────────────────────────────────────────
zfs inherit compression tank/data/temp   # eredita dal parent

# ── Proprietà custom ─────────────────────────────────────
# ZFS supporta proprietà custom con namespace utente (user:*)
zfs set user:backup-policy=daily tank/data/critical
zfs get user:backup-policy tank/data/critical
```

### Organizzazione Raccomandata

```
tank/
├── ROOT/                    # Sistema operativo (se ZFS root)
│   └── ubuntu/
├── data/
│   ├── documents/           # recordsize=128K, compression=zstd
│   ├── media/               # recordsize=1M, compression=off
│   ├── databases/           # recordsize=16K, compression=lz4
│   │   ├── postgresql/      # sync=standard, logbias=latency
│   │   └── mysql/           # sync=standard, primarycache=metadata
│   └── backups/             # compression=zstd-19
├── vms/                     # per VM disk (zvol)
│   ├── vm-web01/
│   └── vm-db01/
├── containers/              # per container storage
│   ├── docker/
│   └── lxd/
└── users/
    ├── alice/               # quota=50G
    └── bob/                 # quota=50G
```

---

## Dataset vs Zvol

ZFS offre due tipi di "contenitore dati": **dataset** (filesystem) e **zvol** (volume a blocchi).

### Dataset (Filesystem)

Un dataset è un filesystem ZFS completo con directory, file, permessi. È il tipo più comune.

```bash
zfs create tank/data
# Risultato: un filesystem montato su /tank/data
ls /tank/data/    # directory, file, etc.
```

### Zvol (Block Volume)

Uno zvol è un block device emulato da ZFS. Appare come `/dev/zvol/pool/name` e può essere usato per qualsiasi cosa che richieda un block device: VM disk, iSCSI target, filesystem non-ZFS.

```bash
# Crea zvol da 50 GB
zfs create -V 50G tank/volumes/vm-disk1

# Il device appare come:
ls -la /dev/zvol/tank/volumes/vm-disk1
# lrwxrwxrwx 1 root root 10 ... /dev/zvol/tank/volumes/vm-disk1 -> ../../zd0

# Formatta con un altro filesystem (esempio: ext4 per una VM)
mkfs.ext4 /dev/zvol/tank/volumes/vm-disk1

# Usa come disco per una VM (QEMU/KVM)
# <disk type='block' device='disk'>
#   <source dev='/dev/zvol/tank/volumes/vm-disk1'/>
#   <target dev='vda' bus='virtio'/>
# </disk>

# Thin provisioning (sparse zvol)
zfs create -s -V 100G tank/volumes/vm-disk2
# -s = sparse: i 100 GB non vengono allocati immediatamente
# Lo spazio viene allocato on-demand

# Proprietà specifiche zvol
zfs set volblocksize=16K tank/volumes/vm-disk1  # solo alla creazione
zfs get volsize,volblocksize,refreservation tank/volumes/vm-disk1
```

### Quando Usare Dataset vs Zvol

| Use Case | Dataset | Zvol |
|----------|---------|------|
| File storage (NAS, home) | **Sì** | No |
| Database (PostgreSQL, MySQL) | **Sì** (su dataset) | Possibile |
| VM disk (KVM, VirtualBox) | No | **Sì** |
| iSCSI target | No | **Sì** |
| Container storage | **Sì** | Possibile |
| Swap | No | **Sì** (con cautela) |

---

## Compressione

ZFS supporta compressione trasparente a livello di blocco. La compressione è quasi sempre consigliata perché riduce non solo lo spazio su disco ma anche l'I/O (meno dati da leggere/scrivere fisicamente).

### Algoritmi Disponibili

| Algoritmo | Ratio | Velocità | CPU | Uso consigliato |
|-----------|-------|----------|-----|-----------------|
| lz4 | Moderato (2-3×) | Molto alta (>2 GB/s) | Basso | Default per tutto |
| zstd (default = zstd-3) | Alto (3-5×) | Alta (~1 GB/s) | Moderato | Dati generali |
| zstd-1 | Moderato | Molto alta | Basso | Simile a lz4 ma ratio migliore |
| zstd-3 | Alto | Alta | Moderato | Default di zstd |
| zstd-7 | Molto alto | Moderata | Alto | Archivio warm |
| zstd-19 | Massimo | Bassa (~50 MB/s) | Molto alto | Archivio cold |
| gzip-1 | Moderato | Bassa | Alto | Legacy |
| gzip-9 | Alto | Molto bassa | Molto alto | Legacy, non usare |
| lzjb | Basso | Alta | Basso | Legacy, superato da lz4 |
| zle | Minimo | Altissima | Minimo | Solo dati con molti zeri |

### Configurazione e Monitoraggio

```bash
# Imposta compressione (si applica ai NUOVI dati, non retroattiva)
zfs set compression=lz4 tank/data
zfs set compression=zstd tank/data/logs
zfs set compression=zstd-19 tank/data/archive
zfs set compression=off tank/data/media

# Verifica rapporto di compressione
zfs get compressratio tank/data
# NAME       PROPERTY       VALUE  SOURCE
# tank/data  compressratio  2.43x  -

# Report dettagliato
zfs get compressratio,used,logicalused,logicalreferenced tank/data
# NAME       PROPERTY             VALUE   SOURCE
# tank/data  compressratio        2.43x   -
# tank/data  used                 45.2G   -
# tank/data  logicalused          110G    -        ← dati prima della compressione
# tank/data  logicalreferenced    108G    -

# Spazio risparmiato = logicalused - used = 110G - 45.2G = 64.8G

# Verifica algoritmo attivo e sorgente della proprietà
zfs get compression tank/data/logs
# NAME            PROPERTY     VALUE  SOURCE
# tank/data/logs  compression  zstd   local

zfs get compression tank/data/logs/app1
# NAME                  PROPERTY     VALUE  SOURCE
# tank/data/logs/app1   compression  zstd   inherited from tank/data/logs
```

### Quando Disabilitare la Compressione

La compressione dovrebbe essere disabilitata **solo** per dati già compressi o encrypted:
- File video (.mp4, .mkv, .avi)
- File audio compressi (.mp3, .flac, .aac)
- Immagini compresse (.jpg, .png, .webp)
- Archivi (.zip, .tar.gz, .7z)
- Dati encrypted a livello applicativo

Per tutti gli altri dati, `lz4` è il default raccomandato: il costo CPU è trascurabile e il beneficio in I/O è significativo. Con CPU moderne (AVX2), lz4 comprime a oltre 2 GB/s — più veloce della maggior parte degli SSD in scrittura.

---

## Deduplication

La deduplication elimina blocchi di dati identici memorizzandoli una sola volta. ZFS usa una Deduplication Table (DDT) in memoria per tracciare gli hash di ogni blocco.

### Requisiti di Memoria

La DDT richiede circa 320 byte per blocco deduplicato. Per un pool da 10 TB con recordsize 128K:
- 10 TB / 128 KB = ~83 milioni di blocchi
- 83M × 320 byte = ~26 GB di RAM solo per la DDT

Questo è il motivo per cui la dedup ZFS è sconsigliata nella stragrande maggioranza dei casi.

```bash
# Stima PRIMA di abilitare (dry-run)
zdb -S tank
# Simulated DDT histogram:
# refcnt   blocks   LSIZE   PSIZE   DSIZE   blocks   LSIZE   PSIZE   DSIZE
# ------   ------   -----   -----   -----   ------   -----   -----   -----
#      1    78.2M   9.78T   4.56T   4.56T    78.2M   9.78T   4.56T   4.56T
#      2     4.1M    512G    256G    256G     8.2M   1.00T    512G    512G
#      4     1.2M    150G     75G     75G     4.8M    600G    300G    300G
# Total    83.5M   10.4T   4.89T   4.89T    91.2M   11.4T   5.37T   5.37T
#
# dedup = 1.10 → solo 10% di duplicazione!
# In questo caso, la dedup NON conviene.

# Abilita dedup (SOLO se conviene dopo l'analisi)
zfs set dedup=on tank/data/vms

# Abilita dedup con verifica (più sicuro ma più lento)
zfs set dedup=verify tank/data/vms

# Verifica rapporto di dedup
zpool get dedupratio tank
# NAME  PROPERTY    VALUE  SOURCE
# tank  dedupratio  1.10x  -

# Statistiche DDT
zpool status -D tank
```

### Fast Dedup (OpenZFS 2.2+)

OpenZFS 2.2 introduce la "fast dedup" che migliora drasticamente le performance della deduplication:

```bash
# Fast dedup usa un log on-disk per la DDT anziché tenerla tutta in RAM
zfs set dedup=on tank/data
zpool set feature@fast_dedup=enabled tank

# La fast dedup riduce il requisito di RAM da ~320 byte/blocco
# a molto meno, perché mantiene solo un indice in RAM
# e il grosso della DDT su disco (preferibilmente su special vdev)
```

### Regola Pratica

Usa la dedup ZFS solo se TUTTE queste condizioni sono vere:
1. Hai **almeno 5 GB di RAM per ogni TB di dati**
2. I dati hanno un **tasso di duplicazione dimostrato > 2× con `zdb -S`**
3. Hai **SSD/NVMe per l'ARC** o **special vdev** per la DDT
4. Non puoi usare alternative (dedup a livello applicativo, hard link, compressione)

Nella maggior parte dei casi, la compressione zstd è una scelta migliore: offre risparmio di spazio comparabile senza i requisiti di RAM.

---

## Snapshot e Cloni

Gli snapshot sono una delle funzionalità più potenti di ZFS. Grazie al copy-on-write, uno snapshot è istantaneo e non occupa spazio aggiuntivo al momento della creazione. Occupa spazio solo quando i dati originali vengono modificati.

### Operazioni con Snapshot

```bash
# Crea snapshot
zfs snapshot tank/data@2024-04-01
zfs snapshot tank/data@before-upgrade

# Snapshot ricorsivo (include tutti i figli)
zfs snapshot -r tank/data@daily-2024-04-01

# Lista snapshot
zfs list -t snapshot
zfs list -t snapshot -r tank/data
zfs list -t snapshot -o name,used,refer,creation -s creation

# Spazio usato da uno snapshot
# "used" = spazio che verrebbe liberato distruggendo questo snapshot
# "refer" = spazio dei dati a cui lo snapshot fa riferimento
zfs list -t snapshot -o name,used,refer

# Accesso ai dati dello snapshot (directory nascosta)
ls /tank/data/.zfs/snapshot/2024-04-01/

# Copia un file dalla versione snapshot
cp /tank/data/.zfs/snapshot/before-upgrade/config.yml /tank/data/config.yml

# Rollback a uno snapshot (DISTRUGGE le modifiche successive)
zfs rollback tank/data@before-upgrade

# Rollback forzato (distrugge snapshot intermedi)
zfs rollback -r tank/data@last-known-good

# Distruggi snapshot
zfs destroy tank/data@old-snapshot

# Distruggi range di snapshot
zfs destroy tank/data@autosnap_2024-01-01%autosnap_2024-03-31

# Confronta differenze tra snapshot
zfs diff tank/data@snap1 tank/data@snap2
# Output:
# M       /tank/data/config.yml
# +       /tank/data/new-file.txt
# -       /tank/data/removed.log
# R       /tank/data/old-name.txt -> /tank/data/new-name.txt

# Bookmark (riferimento leggero a uno snapshot — per send incrementale)
# Un bookmark non occupa spazio ma permette send incrementale
# anche dopo aver distrutto lo snapshot originale
zfs bookmark tank/data@2024-04-01 tank/data#2024-04-01
zfs list -t bookmark
```

### Snapshot Automatici con Sanoid

```bash
# Installa sanoid/syncoid
apt install sanoid    # Debian/Ubuntu
dnf install sanoid    # Fedora

# Configurazione /etc/sanoid/sanoid.conf
cat <<'SANOID_CONF' > /etc/sanoid/sanoid.conf
[tank/data]
    use_template = production
    recursive = yes

[tank/data/media]
    use_template = archive
    recursive = yes

[template_production]
    frequently = 0
    hourly = 24
    daily = 30
    weekly = 4
    monthly = 12
    yearly = 2
    autosnap = yes
    autoprune = yes

[template_archive]
    frequently = 0
    hourly = 0
    daily = 7
    weekly = 4
    monthly = 6
    yearly = 1
    autosnap = yes
    autoprune = yes
SANOID_CONF

# Esecuzione (via timer systemd)
systemctl enable --now sanoid.timer

# Verifica timer
systemctl list-timers | grep sanoid
# NEXT                         LEFT       LAST                         PASSED
# Thu 2024-04-01 15:15:00 UTC  14min left Thu 2024-04-01 15:00:00 UTC  45s ago

# Esecuzione manuale
sanoid --cron

# Lista snapshot creati da sanoid
zfs list -t snapshot -o name,creation | grep autosnap
```

### Cloni

Un clone è un filesystem scrivibile creato da uno snapshot:

```bash
# Crea clone da snapshot
zfs clone tank/data@2024-04-01 tank/data-test

# Il clone è un filesystem completo ma inizialmente non occupa spazio
zfs list -o name,origin tank/data-test
# NAME             ORIGIN
# tank/data-test   tank/data@2024-04-01

# Promuovi un clone (taglia la dipendenza dallo snapshot)
zfs promote tank/data-test
# Ora il clone è indipendente e lo snapshot "originale" dipende dal clone

# Caso d'uso pratico: test di upgrade
zfs snapshot tank/data/app@pre-upgrade
zfs clone tank/data/app@pre-upgrade tank/data/app-staging
# Testa l'upgrade su app-staging (stesso dati, zero copia)
# Se OK: zfs destroy tank/data/app-staging
# Se KO: zfs rollback tank/data/app@pre-upgrade
```

---

## Send/Receive per Backup e Replicazione

`zfs send` e `zfs receive` permettono di trasmettere dataset come stream di byte, ideali per backup e replicazione.

### Send/Receive di Base

```bash
# Invia uno snapshot completo a un file
zfs send tank/data@2024-04-01 > /backup/data-20240401.zfs

# Con stima della dimensione (utile per pianificazione)
zfs send -nv tank/data@2024-04-01
# send from @ to tank/data@2024-04-01 estimated size is 45.2G

# Invia a un altro pool locale
zfs send tank/data@2024-04-01 | zfs receive backup/data

# Invia incrementale (solo le differenze tra due snapshot)
zfs send -i tank/data@2024-04-01 tank/data@2024-04-02 | zfs receive backup/data

# Invia via rete (SSH)
zfs send tank/data@2024-04-01 | ssh backup-server zfs receive rpool/backup/data

# Invia incrementale via rete
zfs send -i tank/data@2024-04-01 tank/data@2024-04-02 | \
    ssh backup-server zfs receive rpool/backup/data

# Invia compresso (raw) — mantiene la compressione originale
zfs send --compressed tank/data@2024-04-01 | \
    ssh backup-server zfs receive rpool/backup/data

# Send ricorsivo (include figli e tutti gli snapshot)
zfs send -R tank/data@2024-04-01 | zfs receive -F backup/data

# Send con resume (OpenZFS 2.0+) — riprende dopo interruzione
zfs send -t <resume_token> | ssh backup-server zfs receive rpool/backup/data
# Il resume token viene mostrato nell'errore di `zfs receive` interrotto:
# cannot receive: failed to read from stream
# partially received tank/data snapshot
# use 'zfs send -t <token>' to resume
```

### Tipi di Send

```bash
# Full send (completo)
zfs send tank/data@snap1

# Incremental send (-i = incrementale tra due snapshot)
zfs send -i tank/data@snap1 tank/data@snap2

# Incremental send da bookmark (-i con bookmark)
zfs send -i tank/data#snap1 tank/data@snap2

# Replication send (-R = ricorsivo, include tutte le proprietà e gli snapshot)
zfs send -R tank/data@snap1

# Raw send (-w = invia dati encrypted senza decifrare)
zfs send -w tank/data@snap1

# Send con compressione LZ4 lungo il pipe (non --compressed)
zfs send tank/data@snap1 | lz4 | ssh backup-server "lz4 -d | zfs receive rpool/backup/data"

# Send con progress (pv = pipe viewer)
zfs send tank/data@snap1 | pv | ssh backup-server zfs receive rpool/backup/data
# 45.2GiB 0:23:41 [32.7MiB/s]
```

### Replicazione Automatica con Syncoid

```bash
# Syncoid (parte del pacchetto sanoid) automatizza il send/receive incrementale

# Replicazione locale
syncoid tank/data backup/data

# Replicazione remota via SSH
syncoid tank/data root@backup-server:rpool/backup/data

# Replicazione ricorsiva
syncoid -r tank/data root@backup-server:rpool/backup/data

# Con compressione durante il trasferimento
syncoid --compress=zstd-fast tank/data root@backup-server:rpool/backup/data

# Senza creare snapshot intermedi (usa quelli di sanoid)
syncoid --no-sync-snap tank/data root@backup-server:rpool/backup/data

# Cron job per replicazione automatica ogni 6 ore
# /etc/cron.d/zfs-replicate
0 */6 * * * root syncoid -r --no-sync-snap tank/data root@backup-server:rpool/backup/data >> /var/log/syncoid.log 2>&1
```

### Pattern di Replicazione Avanzati

#### Pull Mode vs Push Mode

Syncoid supporta due modalità operative. La scelta ha implicazioni significative per la sicurezza.

```bash
# ── Push mode (default): il server sorgente invia al destinatario ──
# Il server di produzione ha accesso SSH al backup server.
# PRO: semplice da configurare
# CONTRO: se il server di produzione è compromesso, l'attaccante
#         ha accesso diretto al backup server
syncoid tank/data root@backup-server:rpool/backup/data

# ── Pull mode: il backup server preleva dalla sorgente ─────────
# Il backup server ha accesso SSH al server di produzione.
# PRO: il server di produzione non conosce il backup server →
#      un attaccante che compromette la produzione non può
#      cancellare i backup (difesa contro ransomware)
# CONTRO: il backup server ha accesso alla produzione
ssh backup-server "syncoid root@prod-server:tank/data rpool/backup/data"

# Pull mode con utente non-root dedicato (più sicuro)
# Sul server di produzione, crea un utente con permessi minimi:
# zfs allow -u zfsbackup send,snapshot,hold tank/data
# Sul backup server:
syncoid --no-privilege-elevation zfsbackup@prod-server:tank/data rpool/backup/data
```

#### Controllo della Banda e Compressione

```bash
# ── Limitazione della banda durante la replica ─────────────
# Utile per non saturare il link di rete durante l'orario lavorativo
syncoid --source-bwlimit=50m tank/data root@backup-server:rpool/backup/data
# 50m = 50 Mbit/s (~6 MB/s)

# ── Compressione del flusso durante il trasferimento ────────
# Riduce il traffico di rete, utile su link lenti
syncoid --compress=lz4 tank/data root@backup-server:rpool/backup/data
# Opzioni: none, gzip, lz4, pigz-fast, pigz-slow, zstd-fast, zstd-slow
# lz4 e zstd-fast sono i migliori compromessi velocità/compressione

# ── Esclusione di dataset specifici ────────────────────────
syncoid -r --exclude='tank/data/temp' --exclude='tank/data/cache' \
    tank/data root@backup-server:rpool/backup/data
```

#### Replicazione Multi-Tier (3-2-1 Backup Rule)

```bash
# Strategia 3-2-1: 3 copie, 2 media diversi, 1 offsite
#
# Tier 1: Pool primario (produzione)
#   tank/data — SSD/HDD locale
#
# Tier 2: Backup locale (diverso controller/chassis)
#   backup/data — HDD separati, stesso sito
#   Replica: ogni 4 ore con syncoid
#
# Tier 3: Backup offsite (diversa location)
#   offsite/data — cloud o data center remoto
#   Replica: ogni 24 ore con syncoid via VPN

# Crontab per replica multi-tier
# /etc/cron.d/zfs-replicate-multitier
# Tier 2 — ogni 4 ore
0 */4 * * * root syncoid -r --no-sync-snap tank/data backup/data \
    >> /var/log/syncoid-local.log 2>&1
# Tier 3 — ogni notte alle 03:00
0 3 * * * root syncoid -r --no-sync-snap --compress=zstd-fast \
    --source-bwlimit=100m tank/data root@offsite:rpool/backup/data \
    >> /var/log/syncoid-offsite.log 2>&1
```

#### Replicazione con Bookmark e Resume Token

```bash
# ── Bookmark: riferimenti leggeri per send incrementale ─────
# Un bookmark occupa zero spazio ma permette send incrementale
# anche dopo aver distrutto lo snapshot sorgente.
# Questo è fondamentale per la retention: puoi tenere pochi
# snapshot sulla sorgente ma mantenere la catena incrementale.

zfs snapshot tank/data@daily-2025-05-01
# Replica iniziale
zfs send tank/data@daily-2025-05-01 | ssh backup zfs receive rpool/backup/data

# Crea bookmark e distruggi lo snapshot (risparmia spazio)
zfs bookmark tank/data@daily-2025-05-01 tank/data#daily-2025-05-01
zfs destroy tank/data@daily-2025-05-01

# Il giorno dopo, send incrementale dal bookmark
zfs snapshot tank/data@daily-2025-05-02
zfs send -i tank/data#daily-2025-05-01 tank/data@daily-2025-05-02 | \
    ssh backup zfs receive rpool/backup/data

# ── Resume token: riprendi send interrotto ──────────────────
# Se un send viene interrotto (rete, crash), il receiver salva
# un resume token che permette di riprendere da dove si era fermato.

# Il token viene mostrato nell'errore:
# "cannot receive: failed to read from stream"
# "partially received snapshot, use -t to resume"

# Recupera il token
RESUME_TOKEN=$(ssh backup zfs get -H -o value receive_resume_token rpool/backup/data)

# Riprendi il send
zfs send -t "$RESUME_TOKEN" | ssh backup zfs receive -s rpool/backup/data

# Per send grandi (>1 TB), il resume può risparmiare ore di trasferimento
```

#### Monitoraggio e Alerting della Replicazione

```bash
#!/bin/bash
# check-replication-lag.sh — Verifica che la replica non sia troppo vecchia
set -euo pipefail

MAX_LAG_HOURS=8
REMOTE_HOST="backup-server"
REMOTE_DATASET="rpool/backup/data"
ALERT_EMAIL="admin@example.com"

# Trova l'ultimo snapshot sul destinatario
LAST_SNAP_TIME=$(ssh "$REMOTE_HOST" \
    "zfs list -t snapshot -o creation -H -r $REMOTE_DATASET -s creation" | \
    tail -1)

if [[ -z "$LAST_SNAP_TIME" ]]; then
    echo "CRITICAL: nessuno snapshot trovato su $REMOTE_HOST:$REMOTE_DATASET" | \
        mail -s "[ZFS] Replicazione mancante" "$ALERT_EMAIL"
    exit 2
fi

LAST_EPOCH=$(date -d "$LAST_SNAP_TIME" +%s)
NOW_EPOCH=$(date +%s)
LAG_HOURS=$(( (NOW_EPOCH - LAST_EPOCH) / 3600 ))

if [[ "$LAG_HOURS" -gt "$MAX_LAG_HOURS" ]]; then
    echo "WARNING: replicazione in ritardo di ${LAG_HOURS}h (max: ${MAX_LAG_HOURS}h)" | \
        mail -s "[ZFS] Replicazione in ritardo" "$ALERT_EMAIL"
    exit 1
fi

echo "[$(date -Iseconds)] Replicazione OK — lag: ${LAG_HOURS}h"
```

### Script di Backup Manuale

```bash
#!/bin/bash
# backup-zfs.sh — Backup incrementale ZFS via SSH
set -euo pipefail

SRC_DATASET="tank/data"
DST_HOST="backup-server"
DST_DATASET="rpool/backup/data"
SNAP_PREFIX="autobackup"

# Crea nuovo snapshot
NEW_SNAP="${SRC_DATASET}@${SNAP_PREFIX}-$(date +%Y%m%d-%H%M%S)"
zfs snapshot -r "$NEW_SNAP"

# Trova l'ultimo snapshot comune
LAST_COMMON=$(ssh "$DST_HOST" "zfs list -t snapshot -o name -H -r $DST_DATASET" 2>/dev/null | \
    grep "$SNAP_PREFIX" | tail -1 | sed "s|${DST_DATASET}|${SRC_DATASET}|")

if [[ -n "$LAST_COMMON" ]]; then
    echo "[$(date -Iseconds)] Invio incrementale: $LAST_COMMON → $NEW_SNAP"
    zfs send -i "$LAST_COMMON" "$NEW_SNAP" | pv | ssh "$DST_HOST" "zfs receive -F $DST_DATASET"
else
    echo "[$(date -Iseconds)] Invio completo: $NEW_SNAP"
    zfs send "$NEW_SNAP" | pv | ssh "$DST_HOST" "zfs receive -F $DST_DATASET"
fi

echo "[$(date -Iseconds)] Backup completato: $NEW_SNAP"
```

---

## Encryption Nativa

OpenZFS 2.0+ supporta la crittografia nativa dei dataset, che cifra i dati a riposo (at rest) senza richiedere LUKS o dm-crypt.

### Vantaggi dell'Encryption Nativa ZFS

- **Granularità per dataset**: ogni dataset può avere una chiave diversa
- **Snapshot e send/receive funzionano**: gli snapshot sono encrypted, il send raw (`-w`) trasferisce dati cifrati
- **Compressione prima della cifratura**: ZFS comprime i dati PRIMA di cifrarli, mantenendo l'efficienza della compressione
- **Nessun overhead di strato**: niente LUKS → LVM → ZFS, tutto integrato

### Creazione Dataset Encrypted

```bash
# Crea un dataset encrypted con passphrase
zfs create -o encryption=aes-256-gcm -o keyformat=passphrase tank/secure
# Enter new passphrase:
# Re-enter new passphrase:

# Crea con chiave da file (per automazione)
dd if=/dev/urandom of=/root/.zfs-key-tank-secure bs=32 count=1
chmod 600 /root/.zfs-key-tank-secure
zfs create -o encryption=aes-256-gcm \
    -o keyformat=raw \
    -o keylocation=file:///root/.zfs-key-tank-secure \
    tank/secure-auto

# Dataset figli ereditano l'encryption dal parent
zfs create tank/secure/documents    # encrypted con la stessa chiave del parent

# Dataset figlio con chiave diversa
zfs create -o keyformat=passphrase tank/secure/personal
# Chiede una NUOVA passphrase

# Verifica proprietà di encryption
zfs get encryption,keyformat,keylocation,keystatus tank/secure
# NAME         PROPERTY      VALUE                              SOURCE
# tank/secure  encryption    aes-256-gcm                        -
# tank/secure  keyformat     passphrase                         -
# tank/secure  keylocation   prompt                             local
# tank/secure  keystatus     available                          -
```

### Gestione Chiavi

```bash
# Carica chiave (dopo reboot, il dataset è locked)
zfs load-key tank/secure
# Enter passphrase for 'tank/secure':

# Carica tutte le chiavi
zfs load-key -a

# Scarica chiave (smonta e blocca il dataset)
zfs unload-key tank/secure

# Cambia passphrase
zfs change-key tank/secure
# Chiede vecchia passphrase, poi nuova

# Cambia da passphrase a file
zfs change-key -o keyformat=raw \
    -o keylocation=file:///root/.zfs-key-new \
    tank/secure

# Auto-mount al boot con chiave da file
# In /etc/systemd/system/zfs-load-key.service:
# [Service]
# Type=oneshot
# ExecStart=/sbin/zfs load-key -a
# ExecStartPost=/sbin/zfs mount -a
# [Install]
# WantedBy=zfs-mount.service

# Send/receive con dati encrypted (raw)
# Il receiver NON ha bisogno della chiave
zfs send -w tank/secure@snap1 | ssh backup-server zfs receive rpool/backup/secure
# I dati rimangono cifrati sul backup server
```

### Algoritmi Disponibili

| Algoritmo | Performance | Sicurezza | Note |
|-----------|-------------|-----------|------|
| `aes-256-gcm` | Alta (con AES-NI) | Molto alta | **Raccomandato** — autenticato |
| `aes-256-ccm` | Moderata | Molto alta | Alternativa, meno performante |
| `aes-128-gcm` | Molto alta | Alta | Sufficiente per la maggior parte |
| `aes-128-ccm` | Alta | Alta | Alternativa |

```bash
# Verifica supporto AES-NI (hardware acceleration)
grep -o aes /proc/cpuinfo | head -1
# aes ← se presente, AES-NI è disponibile

# Con AES-NI, l'overhead dell'encryption è <5%
# Senza AES-NI, può essere 20-30%
```

### Architettura delle Chiavi: Master Key vs Wrapping Key

La comprensione dell'architettura delle chiavi è fondamentale per valutare correttamente le garanzie di sicurezza dell'encryption ZFS.

```
Architettura chiavi ZFS encryption:

┌─────────────────────────────────────────────────────────┐
│                    User Key                              │
│  (passphrase o raw key — ciò che l'utente fornisce)      │
│  Può essere cambiata con zfs change-key                  │
└────────────────────┬────────────────────────────────────┘
                     │ PBKDF2 (se passphrase)
                     │ o uso diretto (se raw)
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Wrapping Key                            │
│  Derivata dalla user key.                                │
│  Usata per cifrare/decifrare la master key.              │
│  Cambia quando cambia la user key.                       │
└────────────────────┬────────────────────────────────────┘
                     │ AES key wrapping
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Master Key                             │
│  Generata randomicamente alla creazione del dataset.     │
│  NON cambia MAI — cifra tutti i dati del dataset.        │
│  Memorizzata su disco, cifrata dalla wrapping key.       │
│  Se compromessa → tutti i dati sono leggibili.           │
└────────────────────┬────────────────────────────────────┘
                     │ AES-GCM / AES-CCM
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Dati Cifrati                            │
│  Blocchi dati e metadati cifrati con la master key.       │
│  Snapshot, send raw e cloni ereditano la stessa           │
│  master key.                                             │
└─────────────────────────────────────────────────────────┘
```

**Implicazione critica**: `zfs change-key` cambia solo la user key e la wrapping key. La master key rimane invariata. Questo significa che:

1. Cambiare passphrase è veloce (non serve re-cifrare i dati)
2. Ma se un attaccante ha ottenuto la master key, cambiare la passphrase **non protegge i dati**
3. La master key wrapped (cifrata con la vecchia wrapping key) non viene sovrascritta su disco — è recuperabile con analisi forense per un tempo indeterminato

### PBKDF2 e Hardening della Passphrase

```bash
# pbkdf2iters controlla il numero di iterazioni PBKDF2
# per derivare la wrapping key dalla passphrase.
# Più iterazioni = più lento il brute-force, ma anche il load-key.

# Default: 350000 iterazioni
zfs get pbkdf2iters tank/secure
# NAME         PROPERTY      VALUE    SOURCE
# tank/secure  pbkdf2iters   350000   default

# Aumenta per hardware moderno (CPU veloce)
# L'obiettivo è che il load-key impieghi 1-2 secondi.
zfs change-key -o pbkdf2iters=1000000 tank/secure
# Con 1M di iterazioni su una CPU moderna, il load-key
# richiede ~1.5 secondi — accettabile per operazioni manuali.

# Verifica il tempo di derivazione
time zfs load-key tank/secure
# real    0m1.423s ← accettabile

# Per dataset caricati automaticamente al boot (keylocation=file://),
# pbkdf2iters non è rilevante perché si usa keyformat=raw.
```

### Limitazioni di Sicurezza e Procedure di Recovery

```bash
# ── Limitazione 1: change-key non ruota la master key ──────
# Se la master key è compromessa (es. attaccante ha avuto accesso
# al disco + alla passphrase per un periodo), cambiare la passphrase
# NON è sufficiente.

# Procedura corretta in caso di compromissione della master key:
# 1. Creare un nuovo dataset encrypted con nuova master key
zfs create -o encryption=aes-256-gcm -o keyformat=passphrase tank/secure-new

# 2. Copiare i dati (il send/receive con -w NON va bene
#    perché mantiene la stessa master key!)
# SBAGLIATO: zfs send -w tank/secure@snap | zfs receive tank/secure-new
# CORRETTO: copia a livello file (i dati vengono re-cifrati)
rsync -avPHX /tank/secure/ /tank/secure-new/

# 3. Oppure usa send/receive senza -w (decifra e re-cifra)
zfs send tank/secure@snap | zfs receive -o encryption=aes-256-gcm \
    -o keyformat=passphrase tank/secure-new

# 4. Se possibile, secure erase dello spazio libero
zpool trim --secure tank    # richiede supporto hardware (NVMe)
# oppure
zpool initialize tank       # sovrascrive spazio libero con zeri

# ── Limitazione 2: encrypted dataset e copies ──────────────
# Un dataset encrypted non può avere copies=3 perché lo spazio
# del terzo copy è usato per i metadati di encryption.
# copies=1 e copies=2 funzionano normalmente.

# ── Limitazione 3: block cloning e encryption ──────────────
# I blocchi encrypted non possono essere clonati (cp --reflink).
# Questo perché ogni blocco è cifrato con un IV (Initialization
# Vector) unico — condividere il blocco richiederebbe condividere
# l'IV, compromettendo la sicurezza.

# ── Limitazione 4: embedded_data e encryption ──────────────
# La feature embedded_data (dati piccoli inline nei metadati)
# non è compatibile con l'encryption. I dati piccoli vengono
# memorizzati in blocchi normali cifrati, con overhead relativo.
```

### Automazione del Key Loading con systemd

```bash
# Per dataset con keylocation=file://, l'automazione è semplice.
# Per dataset con passphrase, serve un approccio diverso.

# ── Metodo 1: File di chiave in RAM (tmpfs) ────────────────
# La chiave esiste solo in RAM, fornita al boot tramite initramfs
# o inserita manualmente dall'operatore dopo il reboot.

# ── Metodo 2: Servizio systemd per key loading ────────────
cat > /etc/systemd/system/zfs-load-keys.service <<'EOF'
[Unit]
Description=Load ZFS encryption keys
DefaultDependencies=no
Before=zfs-mount.service
After=zfs-import.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/sbin/zfs load-key -a
# -a carica tutte le chiavi disponibili (file-based)
# I dataset con keylocation=prompt vengono saltati

[Install]
WantedBy=zfs-mount.service
EOF

systemctl enable zfs-load-keys.service

# ── Metodo 3: Key su disco separato (USB di emergenza) ─────
# La chiave risiede su una USB che viene inserita solo al boot.
# Dopo il load-key, la USB viene rimossa.
zfs set keylocation=file:///mnt/usb-key/zfs-key-tank-secure tank/secure

# Script di boot: monta USB → load-key → smonta USB
cat > /usr/local/sbin/zfs-usb-key-load.sh <<'SCRIPT'
#!/bin/bash
set -euo pipefail
USBDEV="/dev/disk/by-uuid/XXXX-YYYY"
MOUNT="/mnt/usb-key"
mount -o ro "$USBDEV" "$MOUNT"
zfs load-key -a
umount "$MOUNT"
SCRIPT
chmod 700 /usr/local/sbin/zfs-usb-key-load.sh
```

---

## Special VDEV e Allocation Classes

OpenZFS 2.0+ introduce il concetto di "special vdev" e "allocation classes" che permettono di posizionare specifici tipi di dati su dispositivi dedicati.

### Special VDEV

Il special vdev è un dispositivo (tipicamente SSD/NVMe) su cui ZFS memorizza dati speciali: metadati, piccoli blocchi (< soglia configurabile), e la DDT (deduplication table).

```bash
# Aggiungi special vdev al pool
# DEVE avere la stessa ridondanza dei vdev dati!
# Se il pool usa mirror, il special deve essere mirror
zpool add tank special mirror \
    /dev/disk/by-id/nvme-samsung-1 \
    /dev/disk/by-id/nvme-samsung-2

# Verifica
zpool status tank
# NAME                     STATE     READ WRITE CKSUM
# tank                     ONLINE       0     0     0
#   mirror-0               ONLINE       0     0     0
#     sda                  ONLINE       0     0     0
#     sdb                  ONLINE       0     0     0
#   special
#     mirror-1             ONLINE       0     0     0
#       nvme-samsung-1     ONLINE       0     0     0
#       nvme-samsung-2     ONLINE       0     0     0

# Configura cosa va sul special vdev
# special_small_blocks = soglia in byte
# Blocchi più piccoli di questa soglia vanno sul special vdev
zfs set special_small_blocks=128K tank/data
# Tutti i file < 128K vanno su NVMe → accesso velocissimo ai file piccoli

# Per database: tutti i blocchi (recordsize=16K < 128K) vanno su NVMe
zfs set recordsize=16K tank/data/postgresql
zfs set special_small_blocks=128K tank/data/postgresql
# Risultato: l'intero database va su NVMe, i dati bulk su HDD
```

### Allocation Classes

Le allocation classes sono le categorie di dati che ZFS può separare sui diversi vdev:

| Classe | Tipo di Dati | Destinazione |
|--------|-------------|-------------|
| DDT | Deduplication table | special vdev (se presente) |
| Metadata | dnode, indirect blocks | special vdev (se presente) |
| Small blocks | File più piccoli di special_small_blocks | special vdev (se presente) |
| Data | Tutti gli altri dati | vdev normali |

```bash
# Verifica allocazione per classe
zpool list -v -o name,alloc,free,class
```

### Caso d'Uso: NAS Ibrido HDD + NVMe

```bash
# Crea pool con HDD per i dati e NVMe per metadati + file piccoli
zpool create nas \
    -o ashift=12 \
    -O compression=zstd \
    -O atime=off \
    raidz2 /dev/disk/by-id/ata-hdd-{1..6} \
    special mirror \
        /dev/disk/by-id/nvme-ssd-1 \
        /dev/disk/by-id/nvme-ssd-2

# Configura: file < 64K vanno su NVMe
zfs set special_small_blocks=64K nas

# Risultato:
# - Browse delle directory: istantaneo (metadati su NVMe)
# - Apertura file piccoli (documenti, config): istantanea
# - Streaming file grandi (video, backup): dalla velocità degli HDD
# - Costo: 6× HDD economici + 2× NVMe piccoli
```

### Dimensionamento del Special VDEV

Il dimensionamento corretto del special vdev è critico: se si riempie, il pool non si ferma ma l'overflow va sui vdev normali (HDD), perdendo il beneficio. Inoltre, un special vdev troppo piccolo che va in overflow introduce frammentazione.

```bash
# ── Stima dei metadati per pool esistente ──────────────────
# I metadati tipicamente occupano il 3-5% dello spazio dati totale.
# Con special_small_blocks abilitato, aggiungere lo spazio dei
# file piccoli al calcolo.

# Stima conservativa per un pool da 10 TB:
# Metadati puri: 10 TB × 5% = 500 GB
# File < 128K: dipende dal workload
#   - NAS generico: 5-15% dello spazio totale
#   - Server mail: 20-40% (molti file piccoli)
#   - Media server: 1-2% (pochi file grandi)

# Verifica la distribuzione dei file per dimensione
find /tank/data -type f -exec du -b {} + 2>/dev/null | \
    awk '{
        if ($1 < 4096) s["<4K"]++
        else if ($1 < 16384) s["4K-16K"]++
        else if ($1 < 65536) s["16K-64K"]++
        else if ($1 < 131072) s["64K-128K"]++
        else if ($1 < 1048576) s["128K-1M"]++
        else s[">1M"]++
    }
    END {
        for (k in s) printf "%s: %d file\n", k, s[k]
    }' | sort

# Regola pratica per il dimensionamento:
# special_small_blocks=128K → special vdev ≈ 10-20% della capacità pool
# special_small_blocks=64K  → special vdev ≈ 5-10% della capacità pool
# Solo metadati (no small blocks) → special vdev ≈ 3-5% della capacità pool
```

#### Comportamento in Caso di Overflow

```bash
# Se il special vdev si riempie:
# 1. I NUOVI metadati e file piccoli vanno sui vdev normali (HDD)
# 2. I dati GIA' sul special vdev restano lì
# 3. Non c'è errore o downtime — solo degradazione delle performance
# 4. Il pool non si blocca

# Monitoraggio della capacità del special vdev
zpool list -v tank | grep -A2 special
# special
#   mirror-1    200G  185G  15G    92%

# WARNING: >80% → pianificare l'espansione
# CRITICAL: >95% → overflow imminente

# Espansione del special vdev: aggiungi un'altra coppia mirror
zpool add tank special mirror \
    /dev/disk/by-id/nvme-new-1 \
    /dev/disk/by-id/nvme-new-2
# Il nuovo spazio è immediatamente disponibile

# ATTENZIONE: non puoi rimuovere un special vdev dopo l'aggiunta.
# La rimozione richiederebbe spostare tutti i metadati e i file
# piccoli sui vdev normali, operazione non supportata.
# Pianifica il dimensionamento con cura.
```

#### Dedup VDEV: Classe di Allocazione per la DDT

```bash
# OpenZFS 2.1+ supporta un vdev dedicato per la Deduplication Table.
# La DDT su HDD è il motivo principale per cui la dedup ZFS
# è storicamente lenta — la DDT richiede random I/O intensivo.

# Con un dedup vdev dedicato (NVMe), la DDT diventa gestibile:
zpool add tank dedup mirror \
    /dev/disk/by-id/nvme-dedup-1 \
    /dev/disk/by-id/nvme-dedup-2

# La DDT viene automaticamente posizionata sul dedup vdev.
# Se non esiste un dedup vdev ma esiste un special vdev,
# la DDT va sul special vdev.
# Se non esiste nessuno dei due, la DDT va sui vdev normali.

# Priorità di allocazione della DDT:
# 1. dedup vdev (se presente)
# 2. special vdev (se presente)
# 3. vdev normali (HDD — performance terribili)

# Il dedup vdev ha gli stessi requisiti del special vdev:
# - DEVE avere la stessa ridondanza dei vdev dati
# - Non può essere rimosso dopo l'aggiunta
# - Se il dedup vdev fallisce, il pool è perso
```

---

## Manutenzione: Scrub e Sostituzione Dischi

### Scrub

Lo scrub legge tutti i dati nel pool e verifica i checksum. È l'unico modo per rilevare la corruzione silente (bit rot) su blocchi non attivamente letti.

```bash
# Avvia scrub
zpool scrub tank

# Stato dello scrub
zpool status tank
# scan: scrub in progress since Mon Apr  1 02:00:01 2024
#     12.3T scanned at 456M/s, 8.7T issued at 321M/s, 15.2T total
#     0B repaired, 57.24% done, 05:42:33 to go

# Pausa scrub (OpenZFS 2.0+)
zpool scrub -p tank

# Riprendi scrub dopo pausa
zpool scrub tank

# Interrompi scrub
zpool scrub -s tank

# ── Automazione con systemd timer ────────────────────────
# Debian/Ubuntu: il pacchetto zfsutils-linux include già un timer
systemctl enable zfs-scrub-monthly@tank.timer
systemctl start zfs-scrub-monthly@tank.timer

# Timer custom: scrub settimanale
cat > /etc/systemd/system/zfs-scrub-weekly@.service <<'EOF'
[Unit]
Description=ZFS scrub weekly on %i
[Service]
Type=oneshot
ExecStart=/sbin/zpool scrub %i
EOF

cat > /etc/systemd/system/zfs-scrub-weekly@.timer <<'EOF'
[Unit]
Description=ZFS weekly scrub timer for %i
[Timer]
OnCalendar=Sun 02:00
Persistent=true
[Install]
WantedBy=timers.target
EOF

systemctl enable --now zfs-scrub-weekly@tank.timer
```

### Sequential Resilver (OpenZFS 2.0+)

Il resilver tradizionale legge i blocchi nell'ordine logico dell'albero ZFS, causando I/O random. Il sequential resilver legge i blocchi nell'ordine fisico su disco, sfruttando la lettura sequenziale degli HDD.

```bash
# Verifica se il sequential resilver è abilitato
zpool get feature@device_rebuild tank
# Se "disabled", abilitalo:
zpool set feature@device_rebuild=enabled tank

# Il sequential resilver è usato automaticamente con:
zpool replace tank /dev/disk/by-id/old /dev/disk/by-id/new

# Monitora il progresso
zpool status tank
# scan: resilver in progress since Mon Apr  1 10:30:00 2024
#     5.2T scanned at 350M/s, 3.1T issued at 280M/s, 10.0T total
#     Tipo: sequential (vs traditional)
```

### Sostituzione Disco Guasto

```bash
# Identifica il disco problematico
zpool status -v tank
# NAME                     STATE     READ WRITE CKSUM
# tank                     DEGRADED     0     0     0
#   raidz1-0               DEGRADED     0     0     0
#     /dev/disk/by-id/...  ONLINE       0     0     0
#     /dev/disk/by-id/...  FAULTED      3     1     0  too many errors
#     /dev/disk/by-id/...  ONLINE       0     0     0

# Metti offline il disco guasto (se non è già FAULTED)
zpool offline tank /dev/disk/by-id/ata-DISCO-GUASTO

# Sostituisci fisicamente il disco, poi:
zpool replace tank /dev/disk/by-id/ata-DISCO-GUASTO /dev/disk/by-id/ata-DISCO-NUOVO

# Monitora il resilver
watch -n 5 zpool status tank

# Stima tempo di resilver:
# Dimensione dati / velocità resilver = tempo
# 10 TB / 300 MB/s = ~9.5 ore (HDD sequenziale)
# Con dRAID: 10 TB / (300 MB/s × 10 dischi) = ~1 ora

# Dopo il resilver completato, verifica
zpool status tank
# scan: resilver completed after 9h23m with 0 errors

# Per un mirror, si può anche attaccare un nuovo disco
zpool attach tank /dev/disk/by-id/ata-DISCO-SANO /dev/disk/by-id/ata-DISCO-NUOVO
```

### Hot Spare

```bash
# Aggiungi spare al pool
zpool add tank spare /dev/disk/by-id/ata-spare-1

# Configurare auto-replace (lo spare viene usato automaticamente)
zpool set autoreplace=on tank

# Quando un disco fallisce, lo spare viene attivato automaticamente
# Dopo aver sostituito il disco guasto con uno nuovo:
zpool replace tank /dev/disk/by-id/ata-spare-1 /dev/disk/by-id/ata-new-disk
# Lo spare torna disponibile per il prossimo guasto
```

---

## Performance Tuning Avanzato

### Parametri del Modulo ZFS

```bash
# ── Tutti i parametri ────────────────────────────────────
# Elenco completo con valori attuali
cat /sys/module/zfs/parameters/*  # sconsigliato, usare:

# Per ogni parametro
for p in /sys/module/zfs/parameters/*; do
    echo "$(basename $p) = $(cat $p)"
done | sort

# ── Parametri chiave per il tuning ──────────────────────

# TXG timeout (secondi tra commit)
echo 5 > /sys/module/zfs/parameters/zfs_txg_timeout
# Ridurre per database (meno dati persi in caso di crash)
# Aumentare per batch write (più throughput)

# Prefetch (read-ahead)
cat /sys/module/zfs/parameters/zfs_prefetch_disable
# 0 = prefetch attivo (default, buono per sequenziale)
# 1 = prefetch disabilitato (meglio per random I/O puro)

# Limite scrub I/O (per non impattare il workload)
echo 100 > /sys/module/zfs/parameters/zfs_scrub_delay
# Default: 0 (no delay)
# Aumentare se lo scrub rallenta il workload

# Checksum per lettura (verifica integrità ad ogni read)
cat /sys/module/zfs/parameters/zfs_checksums_per_second
# Limite di verifica checksum per secondo

# ── File di configurazione persistente ───────────────────
# /etc/modprobe.d/zfs.conf
cat > /etc/modprobe.d/zfs.conf <<'EOF'
options zfs zfs_arc_max=17179869184
options zfs zfs_arc_min=4294967296
options zfs zfs_txg_timeout=5
options zfs l2arc_write_max=209715200
options zfs l2arc_noprefetch=0
EOF
# Applica al prossimo caricamento del modulo (reboot o modprobe -r zfs && modprobe zfs)
```

### Tuning per Database

```bash
# ── PostgreSQL su ZFS ────────────────────────────────────
zfs create -o recordsize=16K \
    -o compression=lz4 \
    -o atime=off \
    -o logbias=latency \
    -o primarycache=metadata \
    -o redundant_metadata=most \
    tank/data/postgresql

# logbias=latency: ottimizza per bassa latenza (sync write)
# primarycache=metadata: PostgreSQL ha il suo buffer cache (shared_buffers)
#   evita double-caching dei dati. Però i metadati ZFS in ARC servono.
# recordsize=16K: PostgreSQL usa page da 8K, ma 16K è il compromesso ottimale
#   (8K causa troppa frammentazione, 32K spreca spazio su update piccoli)

# ── MySQL/MariaDB su ZFS ────────────────────────────────
zfs create -o recordsize=16K \
    -o compression=lz4 \
    -o atime=off \
    -o logbias=latency \
    -o primarycache=metadata \
    tank/data/mysql

# InnoDB page size è 16K per default → recordsize=16K è perfetto
```

### Tuning per Virtualizzazione

```bash
# ── VM con zvol ──────────────────────────────────────────
zfs create -V 100G \
    -o volblocksize=64K \
    -o compression=lz4 \
    -o sync=standard \
    tank/vms/vm-web01

# volblocksize: 64K è un buon compromesso per workload misti
# Per VM con database interno: volblocksize=16K
# Per VM con file grandi: volblocksize=128K
```

---

## OpenZFS su Linux: Specificità

### Differenze rispetto a Solaris/FreeBSD

```bash
# ── ARC e page cache ────────────────────────────────────
# Su Linux, l'ARC compete con la page cache del kernel.
# Su FreeBSD, ZFS è parte del kernel e gestisce la cache in modo coordinato.
# Su Linux, è necessario limitare esplicitamente l'ARC per evitare
# che la pressione di memoria causi OOM killer.

# ── DKMS vs kmod ────────────────────────────────────────
# DKMS: il modulo viene compilato per ogni aggiornamento del kernel
#   Pro: compatibilità garantita
#   Contro: richiede kernel-headers, compilazione ad ogni aggiornamento

# kmod (kABI-tracking): modulo precompilato
#   Pro: nessuna compilazione
#   Contro: disponibile solo per kernel ufficiali delle distro

# ── ZFS root ─────────────────────────────────────────────
# Ubuntu supporta ZFS root dal 19.10.
# La configurazione richiede un setup specifico con:
# - Pool bpool per /boot (mirror, non encrypted)
# - Pool rpool per / (mirror o raidz, opzionalmente encrypted)
# - Partizione EFI separata (non su ZFS)

# ── Licensing ────────────────────────────────────────────
# ZFS è licenziato sotto CDDL, il kernel Linux sotto GPL.
# Le due licenze sono considerate incompatibili.
# Per questo ZFS non è incluso nel kernel Linux ma distribuito
# come modulo separato tramite DKMS o kmod.
# Questo è un problema legale/politico, non tecnico.
```

### OpenZFS 2.2: Block Cloning e Fast Dedup

OpenZFS 2.2, rilasciato nel novembre 2023, ha introdotto due feature rivoluzionarie insieme al supporto completo per Linux 6.x.

#### Block Cloning (Reflink)

Il block cloning permette la copia istantanea di blocchi di dati senza duplicazione fisica. Anziché leggere e riscrivere i dati, ZFS crea un riferimento condiviso al blocco originale. Le modifiche successive attivano il COW, creando una copia solo del blocco modificato.

```bash
# Verifica e abilita la feature
zpool get feature@block_cloning tank
# Se "disabled":
zpool set feature@block_cloning=enabled tank

# Copia con block cloning esplicito
cp --reflink=always file-sorgente file-destinazione
# Se il filesystem supporta block cloning: copia istantanea, zero I/O
# Se non supportato: il comando fallisce (non fa fallback a copia normale)

# Copia con fallback automatico
cp --reflink=auto file-sorgente file-destinazione
# coreutils 9+ usa copy_file_range() per reflink=auto
# e FICLONE per reflink=always

# Verifica che la copia sia un clone (non una copia vera)
# Il file clonato non occupa spazio aggiuntivo fino alla modifica
zfs list -o name,used,refer tank/data
# Lo spazio "used" non aumenta dopo il clone

# ── Limitazioni del block cloning ──────────────────────────
# 1. Solo blocchi interi possono essere clonati
# 2. I blocchi devono essere già scritti su disco (non in TXG aperto)
# 3. I blocchi encrypted NON possono essere clonati
#    (ogni blocco ha un IV unico per sicurezza)
# 4. Il recordsize della sorgente e della destinazione deve coincidere
# 5. La dedup e il block cloning possono interagire in modo complesso

# Caso d'uso: VM cloning istantaneo
# Clona un disco VM da 100 GB in millisecondi
cp --reflink=always /dev/zvol/tank/vms/template /dev/zvol/tank/vms/vm-new
# Il clone è istantaneo e occupa zero spazio aggiuntivo
# fino a quando la VM non inizia a scrivere dati diversi
```

#### Fast Dedup: DDT con Log On-Disk

La deduplication tradizionale di ZFS manteneva l'intera DDT (Deduplication Table) in ARC (RAM), con requisiti di memoria proibitivi. La fast dedup riprogetta la DDT con un approccio log-structured.

```bash
# La fast dedup usa un log on-disk per le entry DDT
# anziché mantenere tutto in RAM.

# Abilita fast dedup
zpool set feature@fast_dedup=enabled tank
zfs set dedup=on tank/data/vms

# Verifica che la fast dedup sia attiva
zpool get feature@fast_dedup tank
# VALUE = active (non solo enabled)

# La fast dedup funziona meglio con un special vdev:
# la DDT su NVMe ha latenza ~100μs vs ~5ms su HDD
# Senza special vdev, la DDT va su HDD → performance scarse

# Confronto requisiti RAM:
# Dedup tradizionale: ~320 byte/blocco in RAM
#   10 TB / 128K = 83M blocchi × 320 byte = 26 GB RAM
# Fast dedup: ~50-80 byte/blocco in RAM (indice)
#   10 TB / 128K = 83M blocchi × 70 byte = 5.5 GB RAM
#   + DDT log su disco (preferibilmente NVMe special vdev)

# La fast dedup è ancora costosa — usarla solo quando:
# 1. Il tasso di duplicazione è alto (>2× con zdb -S)
# 2. Esiste un special vdev NVMe per la DDT
# 3. L'alternativa (block cloning o compressione) non è sufficiente
```

### OpenZFS 2.3: RAIDZ Expansion, Direct I/O e Altro

OpenZFS 2.3, rilasciato nel gennaio 2025, è la release più significativa nella storia del progetto. La funzionalità più attesa — la RAIDZ expansion — risolve un problema che esisteva dalla nascita di ZFS.

#### RAIDZ Expansion: Aggiungere Dischi a un VDEV Esistente

Prima di OpenZFS 2.3, l'unico modo per espandere lo spazio di un pool era aggiungere un **nuovo vdev**. Non si poteva aggiungere un disco a un vdev RAIDZ esistente. Questo significava che per espandere un raidz1 con 3 dischi da 4 TB, servivano almeno 3 nuovi dischi per creare un nuovo vdev.

```bash
# ── Abilita la feature di RAIDZ expansion ──────────────────
zpool set feature@raidz_expansion=enabled tank

# ATTENZIONE: questa feature flag è irreversibile.
# Una volta abilitata (e usata), il pool non può essere
# importato da versioni di OpenZFS precedenti alla 2.3.

# ── Espandi un vdev RAIDZ aggiungendo un disco ────────────
# Esempio: pool raidz1 con 3 dischi → 4 dischi
zpool attach tank raidz1-0 /dev/disk/by-id/ata-new-disk

# ZFS avvia il processo di reshaping:
# 1. Redistribuisce i dati esistenti su 4 dischi (anziché 3)
# 2. Ricalcola la parità per i nuovi stripe
# 3. Il pool rimane ONLINE e accessibile durante tutto il processo
# 4. Il reshaping può richiedere molte ore per pool grandi

# ── Monitoraggio dell'espansione ───────────────────────────
zpool status tank
# scan: raidz expansion in progress since Thu May 15 02:00:00 2025
#     copied 10.8T in 17:02:49 with 0 errors
#     8.2T scanned at 450M/s, 5.1T issued at 280M/s, 14.5T total
#     56.2% done, 13:30:00 to go

# ── Cosa succede durante l'espansione ──────────────────────
# - Le letture funzionano normalmente
# - Le scritture funzionano ma con overhead I/O aggiuntivo
# - Il resilver ha priorità sull'espansione se un disco guasta
# - L'espansione è restartable (sopravvive al reboot)
# - Dopo il completamento, ZFS avvia un scrub automatico
#   per verificare l'integrità dei dati ribilanciati

# ── Post-espansione ───────────────────────────────────────
# Il vdev raidz1 ora ha 4 dischi:
# - Spazio utile: 3/4 della capacità totale (prima era 2/3)
# - Performance in lettura: leggermente migliore (più dischi)
# - Il livello di parità rimane invariato (raidz1 = 1 parità)

# ── Espansione incrementale: un disco alla volta ──────────
# Puoi espandere gradualmente nel tempo:
# Mese 1: raidz1 con 3 dischi da 8 TB → 16 TB utili
# Mese 3: aggiungi 1 disco → raidz1 con 4 dischi → 24 TB utili
# Mese 6: aggiungi 1 disco → raidz1 con 5 dischi → 32 TB utili
# Ogni espansione mantiene la stessa ridondanza
```

#### Direct I/O (O_DIRECT)

OpenZFS 2.3 introduce il supporto completo per Direct I/O, permettendo alle applicazioni di bypassare l'ARC per letture e scritture.

```bash
# Direct I/O bypassa l'ARC e scrive/legge direttamente su disco.
# Utile per applicazioni che gestiscono il proprio caching
# (database, motori di ricerca, workload NVMe puri).

# Configurazione per dataset
zfs set direct=always tank/data/nvme-workload
# always: tutte le I/O bypassano l'ARC
# standard: solo I/O con flag O_DIRECT bypassano l'ARC (default)
# disabled: O_DIRECT viene ignorato, tutto passa per l'ARC

# Caso d'uso: pool NVMe puro
# Su pool interamente NVMe, l'ARC aggiunge overhead senza beneficio
# perché il disco è già veloce quanto la cache.
zfs set direct=always tank/nvme-data
# Risultato: meno contesa sulla RAM, più RAM per le applicazioni

# Caso d'uso: database con proprio buffer cache
# PostgreSQL/MySQL gestiscono il proprio caching.
# Direct I/O evita il double-caching (una volta nel DB, una nell'ARC).
zfs set direct=standard tank/data/postgresql
# Le query che usano O_DIRECT bypassano l'ARC automaticamente

# Verifica la configurazione
zfs get direct tank/data/nvme-workload
# NAME                       PROPERTY  VALUE     SOURCE
# tank/data/nvme-workload    direct    always    local
```

#### Altre Feature di OpenZFS 2.3

```bash
# ── Long Filenames (fino a 1023 caratteri) ─────────────────
# Prima di OpenZFS 2.3, il limite era 255 byte (standard POSIX).
# Ora i nomi file possono essere fino a 1023 byte.
zpool set feature@longname=enabled tank
zfs set longname=on tank/data

# ── JSON Output per gli strumenti CLI ─────────────────────
# OpenZFS 2.3 aggiunge output JSON nativo per zpool e zfs,
# facilitando l'integrazione con script e monitoring.
zpool list -j
# Output JSON strutturato, parsabile con jq
zpool list -j | jq '.pools[0].name'

zpool status -j tank | jq '.pools[0].scan'
# Metriche di scrub/resilver in formato strutturato

# ── CPU Pinning ────────────────────────────────────────────
# Permette di assegnare le operazioni ZFS a core CPU specifici.
# Utile in ambienti NUMA o per isolare l'overhead ZFS.

# ── Kernel Same Page Merging (KSM) ─────────────────────────
# Integrazione con KSM del kernel Linux per ridurre
# il consumo di memoria in ambienti con molte VM simili.

# ── Verifica versione e feature disponibili ────────────────
zpool upgrade -v | head -20
# Mostra tutte le feature supportate dalla versione installata

# Feature check rapido per le novità OpenZFS 2.3
for feat in raidz_expansion block_cloning fast_dedup longname; do
    status=$(zpool get -H -o value "feature@${feat}" tank 2>/dev/null || echo "non supportata")
    echo "feature@${feat}: ${status}"
done
```

---

## ZFS su Proxmox — Pattern di Integrazione

Proxmox VE è una delle piattaforme di virtualizzazione più strettamente integrate con ZFS. ZFS è supportato come storage primario sia per l'hypervisor stesso che per le VM e i container.

### Creazione Pool: GUI vs CLI

```bash
# ── Via GUI (Datacenter → Storage → ZFS) ────────────────────
# La GUI di Proxmox crea pool con parametri ragionevoli ma limitati.
# Non supporta: special vdev, SLOG, L2ARC, dRAID, opzioni avanzate.
# Per configurazioni complesse, usare la CLI.

# ── Via CLI (raccomandato per produzione) ────────────────────
# Crea pool ottimizzato per Proxmox
zpool create -f \
    -o ashift=12 \
    -o autotrim=on \
    -O compression=lz4 \
    -O atime=off \
    -O xattr=sa \
    -O dnodesize=auto \
    -O relatime=on \
    rpool mirror \
        /dev/disk/by-id/ata-ssd-1 \
        /dev/disk/by-id/ata-ssd-2

# Registra il pool in Proxmox (storage.cfg)
pvesm add zfspool local-zfs -pool rpool/data

# Verifica
pvesm status
# Name          Type    Status  Total       Used       Avail
# local-zfs     zfspool active  3726352384  524288     3725828096
```

### Configurazione storage.cfg

```bash
# /etc/pve/storage.cfg — configurazione centralizzata del cluster
# Proxmox supporta due modalità ZFS:

# ── Modalità 1: zfspool (zvol per VM, dataset per CT) ──────
# Proxmox crea automaticamente zvol per i dischi VM
# e dataset per i rootfs dei container LXC.
cat >> /etc/pve/storage.cfg <<'EOF'

zfspool: tank-vms
    pool tank/vms
    content images,rootdir
    sparse 1
    blocksize 64k
EOF
# sparse=1: thin provisioning per zvol (raccomandato)
# blocksize=64k: volblocksize per zvol VM
# content: images = dischi VM, rootdir = rootfs container

# ── Modalità 2: dir (directory su dataset ZFS) ─────────────
# Per backup, ISO, template — contenuti che beneficiano
# della compressione e degli snapshot a livello file.
cat >> /etc/pve/storage.cfg <<'EOF'

dir: tank-backup
    path /tank/backup
    content backup,iso,vztmpl
    prune-backups keep-last=5,keep-daily=7,keep-weekly=4
EOF

# Dopo la modifica, ricarica la configurazione
systemctl restart pvedaemon
```

### Tuning ARC per Proxmox

```bash
# Proxmox con 64 GB di RAM e 20 VM:
# RAM per VM: ~40 GB (media 2 GB/VM)
# RAM per Proxmox/kernel: ~4 GB
# RAM per ARC: ~16-20 GB

cat > /etc/modprobe.d/zfs.conf <<'EOF'
options zfs zfs_arc_max=17179869184
options zfs zfs_arc_min=4294967296
options zfs zfs_arc_meta_limit_percent=75
options zfs zvol_request_sync=0
EOF

# zvol_request_sync=0: le VM Linux moderne gestiscono il flush
# internamente con write barrier. Disabilitare il sync forzato
# per zvol migliora significativamente le performance I/O delle VM.
# ATTENZIONE: verificare che il guest OS supporti i write barrier.

# Rigenera initramfs per applicare al boot
update-initramfs -u -k all

# ── Proxmox e L2ARC ───────────────────────────────────────
# Se il pool è su HDD, un L2ARC su NVMe accelera le letture VM.
# Particolarmente utile per i boot simultanei di molte VM.
zpool add rpool cache /dev/disk/by-id/nvme-cache-1

# ── Proxmox e SLOG ────────────────────────────────────────
# Utile se le VM usano sync writes (database, mail server).
zpool add rpool log mirror \
    /dev/disk/by-id/nvme-log-1-part1 \
    /dev/disk/by-id/nvme-log-2-part1
```

### Snapshot e Backup con Proxmox

```bash
# Proxmox integra gli snapshot ZFS nativamente.
# Dal GUI: VM → Snapshots → "Take Snapshot"
# Questo crea uno snapshot ZFS atomico del zvol della VM.

# Dalla CLI Proxmox:
qm snapshot 100 before-upgrade --description "Pre-upgrade snapshot"

# Lista snapshot di una VM
qm listsnapshot 100

# Rollback
qm rollback 100 before-upgrade

# ── Backup con Proxmox Backup Server (PBS) ─────────────────
# PBS usa chunking e dedup a livello applicativo.
# La combinazione ZFS + PBS offre:
# - Snapshot atomici ZFS per consistenza
# - Dedup PBS per risparmio spazio sui backup
# - Replicazione ZFS per DR locale
# - Replicazione PBS per DR offsite

# Replica ZFS tra nodi Proxmox (per HA locale)
# Dal GUI: Datacenter → Replication → Add
# Oppure dalla CLI:
pvesr create-local-job 100-0 tank/vms --schedule '*/15' --target pve-node2

# Replica con syncoid (per backup offsite non-Proxmox)
syncoid -r --no-sync-snap rpool/data root@backup-server:backup/proxmox-data
```

### Best Practices per ZFS su Proxmox

```bash
# 1. Usa mirror per il pool di sistema (rpool)
#    Il boot da raidz è possibile ma più complesso da gestire.

# 2. Pool separati per VM e dati:
#    rpool: sistema operativo Proxmox (mirror SSD)
#    tank: VM e container (mirror SSD o raidz HDD)
#    backup: backup locali (raidz HDD)

# 3. Dataset separati per VM, container e ISO:
zfs create -o recordsize=64K tank/vms        # zvol per VM
zfs create -o recordsize=128K tank/containers # rootfs container
zfs create -o compression=zstd tank/backup   # backup compressi
zfs create tank/iso                          # immagini ISO

# 4. Non usare dedup su Proxmox (tranne casi specifici)
#    Il costo RAM della dedup sottrae risorse alle VM.

# 5. Monitoraggio con Proxmox
# Il dashboard Proxmox mostra lo stato ZFS nel pannello Storage.
# Per monitoring avanzato, usa zfs_exporter + Grafana.

# 6. Attenzione alle VM Windows con write-through cache:
#    Le VM Windows con cache=none (write-through) generano
#    molte sync writes → un SLOG è quasi obbligatorio.
#    Alternativa: cache=writeback con battery-backed RAID
#    o UPS affidabile.
```

---

## Best Practices

1. **Usa sempre by-id per i dischi**: `/dev/disk/by-id/` è stabile tra reboot, `/dev/sdX` no.

2. **Imposta ashift correttamente alla creazione**: `ashift=12` per dischi 4K, `ashift=13` per NVMe. Non può essere cambiato dopo.

3. **Usa compressione lz4 o zstd su tutto**: Il costo CPU è trascurabile, il risparmio di I/O è significativo.

4. **Non usare dedup senza analisi preventiva**: Esegui `zdb -S` prima. Il costo in RAM è enorme.

5. **Esegui scrub almeno mensili**: Lo scrub è l'unico modo per rilevare bit rot prima che causi perdita dati.

6. **Non riempire il pool oltre l'80%**: Performance degrada oltre l'80%, critica oltre il 90%. La frammentazione aumenta esponenzialmente.

7. **Snapshot prima di ogni operazione rischiosa**: Gli snapshot sono istantanei e gratuiti.

8. **Replica offsite con send/receive**: Snapshot locali proteggono da errori umani ma non da guasti catastrofici.

9. **Monitora con zpool events**: Integra `zpool events -v` con il sistema di monitoring.

10. **ECC RAM è fortemente raccomandata**: RAM non-ECC può introdurre corruzione che ZFS non può rilevare.

11. **Imposta `zfs_arc_max` esplicitamente su Linux**: Il default (~50% RAM) può causare conflitti con altri servizi. Imposta in `/etc/modprobe.d/zfs.conf`.

12. **Usa SLOG in mirror per workload sync**: La perdita del SLOG durante una scrittura attiva può causare perdita dati.

13. **Non mischiare dimensioni di disco nello stesso vdev**: Usa dischi identici per vdev. Un disco da 4 TB in un mirror con un disco da 8 TB spreca 4 TB.

14. **Pianifica la capacità con `zpool list -o frag`**: La frammentazione è un indicatore chiave della salute del pool.

---

## Troubleshooting

### Problema: Pool in stato DEGRADED

**Sintomi**: `zpool status` mostra il pool come DEGRADED con uno o più dischi FAULTED o UNAVAIL.

**Causa**: Guasto disco, cavo SATA difettoso, o controller con problemi.

**Soluzione**:
```bash
# Identifica il disco problematico
zpool status -v tank

# Verifica messaggi del kernel
dmesg | grep -i "error\|fault\|reset" | tail -20

# Controlla SMART del disco
smartctl -a /dev/disk/by-id/ata-DISCO-PROBLEMATICO

# Se il disco è recuperabile, prova a riportarlo online
zpool online tank /dev/disk/by-id/...

# Se il disco è guasto, sostituiscilo
zpool replace tank /dev/disk/by-id/OLD /dev/disk/by-id/NEW

# Monitora il resilver fino al completamento
watch -n 10 zpool status tank
```

### Problema: Pool non si importa dopo reboot

**Sintomi**: Il pool non è disponibile dopo il reboot, `zpool list` non lo mostra.

**Causa**: Cache file mancante, servizio zfs non abilitato, o dischi non disponibili.

**Soluzione**:
```bash
# Scansiona per pool disponibili
zpool import

# Se il pool appare, importalo
zpool import tank

# Se non appare, specifica le directory dei dischi
zpool import -d /dev/disk/by-id

# Se ci sono conflitti (pool con stesso nome)
zpool import -D    # mostra pool distrutti/esportati

# Abilita servizi per import automatico
systemctl enable zfs-import-cache.service
systemctl enable zfs-mount.service
systemctl enable zfs.target

# Aggiorna la cache
zpool set cachefile=/etc/zfs/zpool.cache tank
```

### Problema: Performance scarse in scrittura

**Sintomi**: Le operazioni di scrittura sono molto più lente del previsto.

**Causa**: Scritture sincrone senza SLOG, pool quasi pieno, frammentazione, o ashift errato.

**Soluzione**:
```bash
# Verifica livello di riempimento (>80% = problemi)
zpool list -o name,capacity

# Verifica ashift
zdb -C tank | grep ashift

# Verifica frammentazione
zpool list -o name,frag

# Per sync write, aggiungi SLOG
zpool add tank log mirror /dev/nvme0n1p1 /dev/nvme1n1p1

# Verifica il recordsize sia appropriato per il workload
zfs get recordsize tank/data

# Verifica se la compressione sta peggiorando le cose
# (raro, ma possibile con dati già compressi)
zfs get compressratio tank/data
# Se < 1.0x, la compressione rallenta senza beneficio → disabilita
```

### Problema: ARC troppo grande, OOM killer

**Sintomi**: Il sistema Linux uccide processi (OOM killer) nonostante il pool non sia sotto carico estremo.

**Causa**: L'ARC di ZFS sta consumando tutta la RAM disponibile. Su Linux, l'ARC non risponde rapidamente alla pressione di memoria.

**Soluzione**:
```bash
# Verifica dimensione ARC attuale
arc_summary | grep "ARC Size"

# Limita l'ARC immediatamente
echo 8589934592 > /sys/module/zfs/parameters/zfs_arc_max

# Persistente
echo 'options zfs zfs_arc_max=8589934592' >> /etc/modprobe.d/zfs.conf

# Rigenera initramfs per applicare al boot
update-initramfs -u   # Debian/Ubuntu
dracut -f             # RHEL/Fedora
```

### Problema: Errori di checksum senza disco guasto

**Sintomi**: `zpool status` mostra errori CKSUM ma nessun disco FAULTED.

**Causa**: RAM difettosa, controller SATA/SAS difettoso, cavo danneggiato, o firmware del disco buggato.

**Soluzione**:
```bash
# Test RAM con memtest86+
# Se RAM non-ECC, questo è un rischio concreto

# Verifica cavi e controller
dmesg | grep -i "error\|reset\|timeout"

# Esegui scrub per forzare la riparazione
zpool scrub tank

# Se gli errori persistono dopo la sostituzione dei cavi,
# il disco potrebbe avere settori difettosi non rilevati da SMART
smartctl -a /dev/disk/by-id/ata-disco-sospetto
smartctl -t long /dev/disk/by-id/ata-disco-sospetto
```

### Problema: Snapshot consumano troppo spazio

**Sintomi**: `zfs list` mostra poco spazio disponibile, ma i dataset singoli sono piccoli.

**Causa**: Gli snapshot trattengono i blocchi vecchi. Se i dati cambiano molto, gli snapshot crescono.

**Soluzione**:
```bash
# Identifica snapshot che consumano spazio
zfs list -t snapshot -o name,used -s used | tail -20

# Distruggi snapshot vecchi
zfs destroy tank/data@old-snapshot

# Distruggi range di snapshot
zfs destroy tank/data@snap1%snap100

# Verifica la policy di retention di sanoid
cat /etc/sanoid/sanoid.conf

# Ridurre la retention se necessario:
# hourly = 12 (anziché 24)
# daily = 14 (anziché 30)
```

---

## Domande Frequenti (Q&A)

**D: ZFS richiede RAM ECC?**

ZFS funziona con RAM non-ECC, ma la raccomandazione è di usare ECC per server di produzione. Il motivo non è specifico di ZFS: QUALSIASI storage stack beneficia di ECC. La differenza è che ZFS rileva la corruzione in molti casi (checksum), mentre un filesystem tradizionale la propaga silenziosamente. Detto questo, se la RAM corrotta causa una scrittura errata che viene committata con un checksum valido calcolato sui dati già corrotti, nemmeno ZFS può proteggerti.

**D: Posso espandere un vdev raidz aggiungendo dischi?**

Sì, da OpenZFS 2.3 è possibile con `zpool attach tank raidz1-0 /dev/new-disk`. Prima di OpenZFS 2.3, l'unica opzione era aggiungere un NUOVO vdev al pool (che espande lo spazio ma non cambia la ridondanza del vdev originale).

**D: Qual è la differenza tra `used`, `referenced` e `logicalused`?**

- `used`: spazio effettivamente allocato su disco (dopo compressione e dedup), inclusi snapshot e figli
- `referenced` (refer): spazio dei dati a cui il dataset fa riferimento direttamente (senza snapshot)
- `logicalused`: spazio dei dati originali prima della compressione
- `used` - `referenced` ≈ spazio occupato da snapshot

**D: Posso convertire ext4 in ZFS senza perdere i dati?**

No. Non esiste un tool di conversione in-place. Devi creare un pool ZFS su nuovi dischi, copiare i dati (con `rsync -avPHX`), e poi riconfigurare i mount point.

**D: ZFS è sicuro per i laptop (power loss frequenti)?**

Sì. Il COW e i TXG garantiscono consistenza. Al massimo perdi gli ultimi secondi di dati non committati (come qualsiasi filesystem con journal). L'AUTOTRIM è raccomandato per SSD di laptop: `zpool set autotrim=on tank`.

**D: Come faccio il resize di un pool?**

ZFS non supporta lo shrink di un pool. Per espandere: aggiungi un vdev o sostituisci tutti i dischi di un vdev con dischi più grandi (`zpool set autoexpand=on tank` dopo la sostituzione di tutti i dischi).

**D: Posso usare ZFS con Docker?**

Sì. Docker supporta il driver di storage `zfs`. Ogni container e immagine diventa un dataset ZFS con snapshot per i layer. È più efficiente di overlay2 per workload con molti container. Configura in `/etc/docker/daemon.json`: `{"storage-driver": "zfs"}`.

**D: Come funziona il COW con la frammentazione?**

Il COW introduce frammentazione perché i dati modificati vengono scritti in nuove posizioni anziché sovrascrivere le vecchie. Questo è mitigato da: (1) metaslab allocator che cerca di allocare spazio contiguo, (2) il prefetch che anticipa le letture, (3) mantenere il pool sotto l'80% di capacità. Monitorare con `zpool list -o frag`.

---

## Esercizi Pratici

### Esercizio 1: Creazione di un Pool di Test con File

Crea un pool ZFS usando file come dispositivi di storage (utile per esercitarsi senza dischi fisici).

```bash
# Crea file sparse da usare come "dischi"
mkdir -p /tmp/zfs-lab
truncate -s 1G /tmp/zfs-lab/disk{1..6}

# Crea un pool mirror con SLOG e L2ARC
# Sperimenta con: creazione dataset, snapshot, compressione

# Al termine: zpool destroy lab && rm -rf /tmp/zfs-lab
```

**Obiettivo**: Creare un pool `lab` con un mirror, aggiungere un dataset con compressione zstd, creare file di test, fare uno snapshot, modificare i file, confrontare con `zfs diff`, e fare rollback.

### Esercizio 2: Replicazione tra Pool

Crea due pool (source e destination) con file sparse. Configura la replicazione incrementale.

**Obiettivo**: Eseguire un full send iniziale, poi send incrementali. Verificare che i dati siano identici con `diff -r`.

### Esercizio 3: Simulare un Guasto Disco

In un pool raidz1 con 3 file-dischi, simula il guasto di un disco e sostituiscilo.

```bash
# Crea pool raidz1
zpool create test raidz /tmp/zfs-lab/disk{1..3}
zfs create test/data
# Scrivi dati
dd if=/dev/urandom of=/test/data/testfile bs=1M count=100

# Simula guasto: corrompi un disco
dd if=/dev/urandom of=/tmp/zfs-lab/disk2 bs=1M count=100

# Esegui scrub → osserva gli errori riparati
# Sostituisci il disco → monitora il resilver
```

### Esercizio 4: Tuning per Database

Crea un dataset ottimizzato per PostgreSQL con recordsize=16K, compression=lz4, atime=off, logbias=latency. Installa PostgreSQL e configura il data directory sul dataset ZFS. Esegui un benchmark con pgbench e confronta con i parametri di default.

### Esercizio 5: Encryption e Send/Receive

Crea un dataset encrypted con passphrase. Aggiungi dati. Esegui un `zfs send -w` (raw) verso un pool non encrypted. Verifica che i dati sul destinatario siano effettivamente cifrati (non leggibili senza la chiave).

---

## Riferimenti

- **OpenZFS Documentation**: https://openzfs.github.io/openzfs-docs/
- **OpenZFS GitHub**: https://github.com/openzfs/zfs
- **ZFS on Linux Wiki**: https://openzfs.github.io/openzfs-docs/Getting%20Started/
- **Sanoid/Syncoid**: https://github.com/jimsalterjrs/sanoid
- **ZFS Administration Guide (Oracle)**: https://docs.oracle.com/cd/E19253-01/819-5461/
- **Jim Salter's ZFS Guide**: https://arstechnica.com/information-technology/2020/05/zfs-101-understanding-zfs-storage-and-performance/
- **OpenZFS 2.2 Release Notes**: https://github.com/openzfs/zfs/releases/tag/zfs-2.2.0
- **OpenZFS 2.3 Release Notes**: https://github.com/openzfs/zfs/releases/tag/zfs-2.3.0
- **RAIDZ Expansion Design**: https://openzfs.org/w/images/6/68/RAIDZ_Expansion_v2.pdf
- **ZFS Native Encryption (Klara)**: https://klarasystems.com/articles/openzfs-native-encryption/
- **ZFS Performance Tuning (Klara)**: https://klarasystems.com/articles/performance-tuning-arc-l2arc-slog/
- **Proxmox ZFS Best Practices**: https://pve.proxmox.com/wiki/ZFS_on_Linux
- **dRAID Documentation**: https://openzfs.github.io/openzfs-docs/Basic%20Concepts/dRAID%20Howto.html
- **ZFS Encryption**: https://openzfs.github.io/openzfs-docs/Getting%20Started/Ubuntu/Ubuntu%2020.04%20Root%20on%20ZFS.html
- `man zpool`, `man zfs`, `man zdb`, `man zfs-send`, `man zfs-receive`
