# Dimensionamento Proxmox VE e Capacity Planning

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 2 — Assessment · Modulo 05.3 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 05.1 (inventario) e 05.2 (criticita); concetti di overcommit, NUMA, KSM, capacity planning queueing; familiarita con `fio`, `iostat`.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. tradurre i requisiti CPU/RAM/storage di un parco macchine VMware in dimensionamento di un cluster Proxmox target, considerando i diversi rapporti di overcommit ammessi (CPU 4:1 conservativo, 8:1 ambizioso; RAM 1:1 strict, 1.2:1 con balloon e KSM);
> 2. dimensionare un nodo Proxmox per workload misto (memorizzando NUMA boundary, latenze accesso memoria) e un cluster a 3-5-7 nodi con capacity per N+1 (perdita di un nodo) e N+2 (perdita di due);
> 3. scegliere il backend storage piu adeguato a partire dai requisiti di IOPS, throughput, latenza, capacity, e budget (LVM-Thin singolo nodo / NFS centralizzato / Ceph hyperconverged / SAN dedicato);
> 4. raccogliere baseline di performance pre-migrazione (`fio` su workload di test, `iostat` su workload reali, vSAN performance dashboards) e definire SLO mirati post-migrazione;
> 5. costruire un foglio di calcolo (o script Python) che, dato l'inventario CSV, produce 2-3 proposte di dimensionamento con BOM hardware + stima di prezzo;
> 6. argomentare i trade-off di scelte specifiche (es. "5 nodi medi vs 3 nodi grandi", "Ceph all-NVMe vs NFS su NAS", "DDR4 ECC vs DDR5 ECC", "EPYC vs Xeon-SP per virt density").
> **Tempo stimato:** lettura 90-120 min · spreadsheet/lab 240 min
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** Proxmox VE 8.x e 9.x; CPU EPYC Genoa (Zen 4) / Bergamo / Turin (Zen 5), Xeon Sapphire Rapids / Emerald Rapids / Granite Rapids; DDR5-5600 ECC RDIMM; NVMe Gen 4/5; Ceph Quincy (17), Reef (18), Squid (19); ZFS 2.2/2.3.

## Mappa concettuale

```
+======================================================+
|  Capacity planning — sintesi dei vettori             |
+======================================================+
|                                                      |
|   COMPUTE (CPU + RAM)                                |
|     - vCPU richiesti (somma cores VM, 0.7..1.0 idle) |
|     - overcommit ratio (4:1 cons, 8:1 ambitious)     |
|     - NUMA: socket count, channels, per-socket RAM   |
|     - KSM gain (~20-30% su workload simili)          |
|         |                                            |
|         v                                            |
|   STORAGE                                            |
|     - Capacity con margine 30% per snapshot/growth   |
|     - IOPS p99 di lavoro (somma per VM)              |
|     - Throughput sequenziale (backup, video, ETL)    |
|     - Latenza target (p99 < 5 ms transactional)      |
|     - Backend: LVM-Thin / ZFS / NFS / Ceph / SAN     |
|         |                                            |
|         v                                            |
|   NETWORK                                            |
|     - Banda VM (somma traffico a regime)             |
|     - Banda storage (NFS/iSCSI/Ceph)                 |
|     - Banda Corosync (latenza < 5 ms RTT)            |
|     - Banda migration (10-25-100 GbE)                |
|         |                                            |
|         v                                            |
|   RESILIENZA                                         |
|     - N+1 (perdere 1 nodo): capacity = N/(N-1)       |
|     - N+2 (perdere 2 nodi): capacity = N/(N-2)       |
|     - Budget per fault domain (rack, zona, sala)     |
|         |                                            |
|         v                                            |
|   OUTPUT                                             |
|     - 2-3 proposte: economy / balanced / premium     |
|     - BOM hardware + costi (capex+opex)              |
|     - Razionale: motivazione per ogni scelta         |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **Overcommit non e gratis ma di solito conviene.** CPU overcommit 4:1 (`pCPU * 4 = vCPU`) e safe per workload tipici; 8:1 funziona per workload mostly-idle (web, dev, lab); 1:1 e per workload ad alta utilizzazione (DB, HPC, real-time). RAM overcommit con balloon + KSM e fattibile (~1.2:1) ma lascia margine: la swap su SSD costa, su HDD e morte.
2. **NUMA e la regola dei 6:1.** Su CPU multi-socket, una VM con vCPU > pCPU per-socket (tipicamente 24-64 in epoche moderne) attraversa il QPI/Infinity Fabric con costo di latenza ~80-120 ns. Per VM "grandi" (DB, in-memory cache), pinnare a un socket (CPU pinning + memory binding) o usare nodi single-socket (densita minore ma performance prevedibili).
3. **KSM funziona per "VM uguali".** Page sharing su Linux KVM e efficace quando si hanno molte VM con stessa OS (es. 50 worker Linux uguali): risparmio 20-30% RAM tipico. Inutile per VM eterogenee. Costo: ~5% CPU (`/etc/default/qemu-kvm` knob `KSM_RUN`). Su Proxmox e attivo di default.
4. **IOPS si dimensionano sui p99, non sui mediani.** Un DB che fa 500 IOPS medi puo richiedere 5000 IOPS p99 in fase di checkpoint. Backup notturni per cluster Ceph richiedono fino a 10x del traffico tipico. Capacity = peak, non average. Strumento: `fio --rw=randrw --bs=4k --iodepth=32 --runtime=300 --rwmixread=70` per profilo "OLTP-like".
5. **Resilienza N+1 vs N+2 e budget.** N+1 = capacity utile = (N-1)/N → per cluster 3 nodi, 67% utile (perdita di un nodo, gli altri due reggono). N+2 = (N-2)/N → cluster a 5 nodi al 60% utile, ma resiste a 2 fault. Per produzione T0/T1 mission-critical, N+2; per resto, N+1 sufficiente. Su Ceph: `replication=3` minimum, replication=2 sconsigliato per produzione.

## Indice
- [Panoramica](#panoramica)
- [Sizing CPU: da VMware a Proxmox](#sizing-cpu-da-vmware-a-proxmox)
- [Sizing RAM: Analisi e Proiezione](#sizing-ram-analisi-e-proiezione)
- [Sizing Storage: Capacity Planning](#sizing-storage-capacity-planning)
- [Rapporti di Overcommit: VMware vs Proxmox](#rapporti-di-overcommit-vmware-vs-proxmox)
- [Dimensionamento Cluster e Nodi](#dimensionamento-cluster-e-nodi)
- [Capacity Planning Storage: Ceph, NFS, iSCSI](#capacity-planning-storage-ceph-nfs-iscsi)
- [Raccolta Baseline di Performance](#raccolta-baseline-di-performance)
- [Esempi di Calcolo Completi](#esempi-di-calcolo-completi)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

Il dimensionamento dell'ambiente Proxmox di destinazione è una delle decisioni più impattanti dell'intero progetto di migrazione. Un errore in questa fase si traduce in problemi di performance post-migrazione (sottodimensionamento) o in spreco di budget (sovradimensionamento). L'obiettivo è tradurre i dati raccolti durante l'assessment VMware in specifiche hardware concrete per i nodi Proxmox.

La sfida principale sta nel fatto che VMware e Proxmox hanno architetture di virtualizzazione diverse con caratteristiche di performance e gestione delle risorse differenti. VMware vSphere utilizza uno scheduler CPU proprietario (NUMA-aware), un memory manager con transparent page sharing e balloon driver, e un sistema di storage con VAAI offloading. Proxmox VE si basa su KVM/QEMU con lo scheduler Linux CFS, utilizza KSM (Kernel Same-page Merging) per il memory sharing, e offre un'ampia scelta di backend storage incluso Ceph nativo. Queste differenze devono essere considerate nel sizing.

Questo documento fornisce formule, tabelle di riferimento e esempi concreti per calcolare il dimensionamento di CPU, RAM, storage e numero di nodi del cluster Proxmox, partendo dai dati dell'inventario VMware e dalle metriche di performance raccolte durante l'assessment.

---

## Sizing CPU: da VMware a Proxmox

### Raccolta dei Dati di Partenza

Il sizing CPU parte dai seguenti dati raccolti nell'assessment:

```powershell
# Estrazione dati CPU rilevanti per il sizing
Get-VM | Where-Object PowerState -eq "PoweredOn" | ForEach-Object {
    $vm = $_
    $cpuStats = Get-Stat -Entity $vm -Stat "cpu.usage.average" -Start (Get-Date).AddDays(-30) -IntervalMins 60
    $cpuAvg = ($cpuStats | Measure-Object -Property Value -Average).Average
    $cpuP95 = ($cpuStats | Sort-Object Value | Select-Object -Skip ([math]::Floor($cpuStats.Count * 0.95)) -First 1).Value

    [PSCustomObject]@{
        VMName        = $vm.Name
        vCPU          = $vm.NumCpu
        CpuAvgPercent = [math]::Round($cpuAvg, 1)
        CpuP95Percent = [math]::Round($cpuP95, 1)
        CpuEffective  = [math]::Round($vm.NumCpu * $cpuAvg / 100, 2)  # vCPU effettivamente utilizzate
        CpuPeakEff    = [math]::Round($vm.NumCpu * $cpuP95 / 100, 2)
    }
} | Export-Csv -Path "C:\Reports\cpu_sizing_data.csv" -NoTypeInformation
```

### Metriche Chiave per il Sizing CPU

| Metrica | Definizione | Uso nel Sizing |
|---------|-------------|---------------|
| vCPU allocate (totale) | Somma di tutte le vCPU configurate su tutte le VM | Requisito massimo teorico |
| vCPU effettive (media) | vCPU × utilizzo medio % | Dimensionamento base |
| vCPU effettive (P95) | vCPU × utilizzo al 95° percentile | Dimensionamento raccomandato |
| pCPU totali host VMware | Core fisici totali dei server VMware | Riferimento per confronto |
| Rapporto vCPU:pCPU corrente | vCPU totali / pCPU totali | Baseline overcommit attuale |

### Formula di Sizing CPU

```
pCPU_necessari = (vCPU_totali × Utilizzo_P95 / 100) × Fattore_Crescita × Fattore_Overhead_KVM
                 ─────────────────────────────────────────────────────────────────────────────
                                        Target_Overcommit_Ratio

Dove:
  vCPU_totali          = somma vCPU di tutte le VM da migrare
  Utilizzo_P95         = utilizzo CPU al 95° percentile (media pesata su tutte le VM)
  Fattore_Crescita     = 1.15 - 1.30 (15-30% crescita prevista nei prossimi 2-3 anni)
  Fattore_Overhead_KVM = 1.02 - 1.05 (overhead di virtualizzazione KVM, generalmente più basso di ESXi)
  Target_Overcommit    = rapporto vCPU:pCPU desiderato (tipicamente 2:1 - 4:1)
```

### Tabella di Riferimento Overcommit CPU

| Tipo di Workload | Overcommit Consigliato | Note |
|------------------|----------------------|------|
| Database (OLTP) | 1:1 - 1.5:1 | CPU-intensive, latenza critica |
| Application Server | 2:1 - 3:1 | Burst periodici, idle frequente |
| Web Server | 3:1 - 4:1 | I/O bound più che CPU bound |
| Desktop VDI | 4:1 - 6:1 | Utilizzo molto variabile |
| Sviluppo/Test | 4:1 - 8:1 | Tolleranza alta alla contesa |
| Batch/ETL | 1:1 - 2:1 | CPU-intensive durante esecuzione |

### Confronto Scheduler: VMware vs KVM

```
VMware vSphere (CPU Scheduler)          KVM / Proxmox (Linux CFS)
┌──────────────────────────┐           ┌──────────────────────────┐
│ • NUMA-aware scheduling  │           │ • NUMA-aware (con tuning)│
│ • SMP co-scheduling      │           │ • CFS (Completely Fair   │
│ • Credit-based fairness  │           │   Scheduler)             │
│ • CPU affinity (DRS)     │           │ • CPU pinning (taskset)  │
│ • Latency sensitivity    │           │ • CPU type passthrough   │
│ • vCPU hot-add           │           │ • vCPU hot-plug          │
│ • Power management       │           │ • cpufreq governors      │
│                          │           │                          │
│ Overhead: ~2-5%          │           │ Overhead: ~1-3%          │
│ (VMkernel + vmm)         │           │ (KVM module + QEMU)      │
└──────────────────────────┘           └──────────────────────────┘
```

KVM ha generalmente un overhead di virtualizzazione CPU leggermente inferiore a ESXi per workload compute-intensive, grazie alla minor complessità dell'hypervisor. Tuttavia, ESXi ha uno scheduler NUMA più sofisticato out-of-the-box, mentre su Proxmox il tuning NUMA va configurato manualmente per ottenere performance ottimali.

---

## Sizing RAM: Analisi e Proiezione

### Raccolta Dati RAM

```powershell
# Estrazione dati memoria per sizing
Get-VM | Where-Object PowerState -eq "PoweredOn" | ForEach-Object {
    $vm = $_
    $memStats = Get-Stat -Entity $vm -Stat "mem.usage.average" -Start (Get-Date).AddDays(-30) -IntervalMins 60
    $memAvg = ($memStats | Measure-Object -Property Value -Average).Average
    $memMax = ($memStats | Measure-Object -Property Value -Maximum).Maximum

    # Active memory è più accurata di usage per il sizing
    $memActive = Get-Stat -Entity $vm -Stat "mem.active.average" -Start (Get-Date).AddDays(-30) -IntervalMins 60
    $memActiveAvg = ($memActive | Measure-Object -Property Value -Average).Average  # in KB
    $memActiveMax = ($memActive | Measure-Object -Property Value -Maximum).Maximum

    [PSCustomObject]@{
        VMName           = $vm.Name
        ConfiguredGB     = $vm.MemoryGB
        UsageAvgPercent  = [math]::Round($memAvg, 1)
        UsageMaxPercent  = [math]::Round($memMax, 1)
        ActiveAvgGB      = [math]::Round($memActiveAvg / 1MB, 2)
        ActiveMaxGB      = [math]::Round($memActiveMax / 1MB, 2)
        EffectiveAvgGB   = [math]::Round($vm.MemoryGB * $memAvg / 100, 2)
        EffectiveMaxGB   = [math]::Round($vm.MemoryGB * $memMax / 100, 2)
    }
} | Export-Csv -Path "C:\Reports\ram_sizing_data.csv" -NoTypeInformation
```

### Formula di Sizing RAM

La RAM è la risorsa più critica nel sizing perché, a differenza della CPU, l'overcommit di memoria ha conseguenze severe (swapping, ballooning, compression, e in casi estremi OOM kill).

```
RAM_fisica_necessaria = RAM_VM_totale × Fattore_Utilizzo × Fattore_Crescita + RAM_Overhead_Host
                        ─────────────────────────────────────────────────────────────────────
                                            Target_Overcommit_RAM

Dove:
  RAM_VM_totale        = somma RAM configurata di tutte le VM
  Fattore_Utilizzo     = utilizzo medio o P95 come percentuale (es. 0.75 se utilizzo medio è 75%)
  Fattore_Crescita     = 1.15 - 1.30
  RAM_Overhead_Host    = 4-8 GB per nodo (Proxmox OS + Ceph OSD se applicabile)
  Target_Overcommit    = rapporto desiderato (1:1 raccomandato per produzione)
```

### Gestione della Memoria: VMware vs Proxmox

| Meccanismo | VMware ESXi | Proxmox/KVM |
|------------|-------------|-------------|
| Page sharing | TPS (Transparent Page Sharing) — disabilitato di default dal 2014 per motivi di sicurezza su pagine large | KSM (Kernel Same-page Merging) — attivo, risparmio tipico 5-15% |
| Balloon driver | vmballoon — integrato in VMware Tools | virtio-balloon — integrato in QEMU guest agent |
| Memory compression | vSphere compression — prima dello swap | zswap / zram — configurabile su Linux host |
| Swap | .vswp file — performance molto degradata | Swap su disco — altrettanto degradato |
| Overcommit management | Resource pools, shares, limits, reservations | cgroups, memory limits in Proxmox config |
| NUMA awareness | Automatico e sofisticato | Manuale via configurazione NUMA topology |

**Raccomandazione chiave**: per workload di produzione, pianificare con overcommit RAM 1:1 o al massimo 1.2:1. L'overcommit RAM è molto più pericoloso dell'overcommit CPU: mentre la contesa CPU causa rallentamento, la contesa RAM causa swapping che può rendere le VM inutilizzabili.

### Calcolo RAM con KSM

KSM (Kernel Same-page Merging) può recuperare memoria significativa quando molte VM eseguono lo stesso OS:

```
Risparmio_KSM_stimato = Num_VM_stesso_OS × RAM_media_per_VM × Fattore_KSM

Fattori KSM tipici:
  - VM con stesso OS e stesse applicazioni:  15-25% risparmio
  - VM con stesso OS, applicazioni diverse:   5-15% risparmio
  - VM con OS diversi:                        2-5% risparmio
```

**Attenzione**: non fare affidamento su KSM come parte del dimensionamento base. KSM è un bonus che migliora l'efficienza, non una garanzia. Il sizing deve funzionare anche senza KSM.

---

## Sizing Storage: Capacity Planning

### Analisi dello Storage VMware Corrente

```powershell
# Riepilogo storage per il sizing
$vmDisks = Get-VM | Get-HardDisk
$storageReport = [PSCustomObject]@{
    TotalVMDKCount      = $vmDisks.Count
    TotalProvisionedTB  = [math]::Round(($vmDisks | Measure-Object -Property CapacityGB -Sum).Sum / 1024, 2)
    TotalUsedTB         = [math]::Round((Get-VM | Measure-Object -Property UsedSpaceGB -Sum).Sum / 1024, 2)
    ThinProvisionedCount = ($vmDisks | Where-Object StorageFormat -eq "Thin").Count
    ThickProvisionedCount = ($vmDisks | Where-Object StorageFormat -ne "Thin").Count
    AverageThinRatio    = [math]::Round(
        ((Get-VM | Measure-Object -Property UsedSpaceGB -Sum).Sum /
         (Get-VM | Measure-Object -Property ProvisionedSpaceGB -Sum).Sum) * 100, 1)
}
$storageReport | Format-List
```

### Formula di Sizing Storage

```
Storage_necessario = Storage_Usato_Attuale × Fattore_Crescita × Fattore_Overhead_FS + Storage_Snapshot + Storage_Backup
                     ──────────────────────────────────────────────────────────────────────────────────────────────────
                                                        (1 - Replica_Overhead)

Componenti:
  Storage_Usato_Attuale  = spazio effettivamente utilizzato dalle VM (non provisioned)
  Fattore_Crescita       = 1.20 - 1.50 (crescita storage tipicamente più aggressiva)
  Fattore_Overhead_FS    = 1.05 - 1.15 (overhead filesystem: ext4 ~5%, XFS ~3%, ZFS ~10-15%)
  Storage_Snapshot       = 15-30% dello storage VM per snapshot/backup locali
  Storage_Backup         = secondo policy di retention
  Replica_Overhead       = 0 se non replicato, percentuale di overhead per replica (Ceph: fattore replica)
```

### Confronto Format Disco: VMware vs Proxmox

| Formato VMware | Equivalente Proxmox | Note |
|---------------|---------------------|------|
| Thin Provisioned VMDK | qcow2 (default) | qcow2 supporta thin provisioning nativo, snapshot, encryption |
| Thick Lazy Zeroed | raw (prealloc=off) | Performance migliori, nessun overhead COW |
| Thick Eager Zeroed | raw (prealloc=full) | Performance massime, tutto lo spazio allocato |
| VMDK su NFS | qcow2 o raw su NFS | Dipende dal backend NFS |
| VMDK su VMFS | raw o qcow2 su LVM/Ceph/ZFS | Dipende dallo storage backend Proxmox |
| RDM Physical | Device passthrough (/dev/sdX) | Mapping diretto del LUN |
| RDM Virtual | virtio-scsi + raw device | Richiede configurazione manuale |

### Confronto Performance I/O

```
Latenza tipica per operazione di I/O (4K random read):

VMware VMFS su FC SAN:          ~0.5-1.5 ms
VMware VMFS su iSCSI:           ~1.0-3.0 ms
VMware NFS v3:                  ~1.0-4.0 ms
VMware vSAN (all-flash):        ~0.2-0.8 ms

Proxmox LVM-thin su local SSD:  ~0.1-0.5 ms
Proxmox Ceph (all-flash, 3x):   ~0.5-2.0 ms
Proxmox ZFS su local SSD:       ~0.2-1.0 ms
Proxmox NFS v4.1:               ~1.0-4.0 ms
Proxmox iSCSI (LIO):            ~0.5-2.0 ms
```

---

## Rapporti di Overcommit: VMware vs Proxmox

### Definizione e Confronto

L'overcommit è la pratica di allocare alle VM più risorse di quelle fisicamente disponibili, facendo affidamento sul fatto che non tutte le VM utilizzeranno il 100% delle risorse contemporaneamente.

```
Overcommit Ratio = Risorse_Allocate_Totali_VM / Risorse_Fisiche_Disponibili

Esempio: 200 vCPU allocate su host con 48 pCPU → ratio 4.17:1
```

### Tabella Comparativa Overcommit

| Risorsa | VMware (tipico) | VMware (aggressivo) | Proxmox (raccomandato) | Proxmox (massimo) |
|---------|-----------------|--------------------|-----------------------|-------------------|
| CPU | 3:1 - 5:1 | 8:1 - 10:1 | 2:1 - 4:1 | 6:1 - 8:1 |
| RAM | 1.2:1 - 1.5:1 | 2:1 | 1:1 - 1.2:1 | 1.5:1 |
| Storage (thin) | 1.5:1 - 2:1 | 3:1 - 4:1 | 1.5:1 - 2:1 | 2.5:1 |

**Perché i rapporti raccomandati differiscono?**

VMware vSphere ha meccanismi di gestione dell'overcommit più maturi e collaudati — in particolare per la memoria — con TPS, balloon driver e compression che lavorano in cascata. Proxmox/KVM ha meccanismi equivalenti (KSM, virtio-balloon), ma l'ecosistema è meno "guidato" nell'orchestrazione automatica di questi meccanismi. Per questo motivo, si raccomandano rapporti più conservativi su Proxmox, specialmente per la RAM.

### Calcolo dell'Overcommit Corrente VMware

```powershell
# Calcolo overcommit ratio corrente per cluster VMware
Get-Cluster | ForEach-Object {
    $cluster = $_
    $hosts = $cluster | Get-VMHost
    $vms = $cluster | Get-VM | Where-Object PowerState -eq "PoweredOn"

    $pCPU = ($hosts | Measure-Object -Property NumCpu -Sum).Sum  # core fisici (con HT)
    $pRAM = ($hosts | Measure-Object -Property MemoryTotalGB -Sum).Sum

    $vCPU = ($vms | Measure-Object -Property NumCpu -Sum).Sum
    $vRAM = ($vms | Measure-Object -Property MemoryGB -Sum).Sum

    [PSCustomObject]@{
        Cluster      = $cluster.Name
        Hosts        = $hosts.Count
        VMs          = $vms.Count
        pCPU         = $pCPU
        vCPU         = $vCPU
        CpuOvercommit = "$([math]::Round($vCPU / $pCPU, 2)):1"
        pRAM_GB      = [math]::Round($pRAM, 0)
        vRAM_GB      = [math]::Round($vRAM, 0)
        RamOvercommit = "$([math]::Round($vRAM / $pRAM, 2)):1"
    }
}
```

---

## Dimensionamento Cluster e Nodi

### Regola N+1 e Quorum

Un cluster Proxmox deve essere dimensionato per tollerare il failure di almeno un nodo (N+1) mantenendo tutti i workload operativi.

```
Nodi_necessari = ceil(Risorse_Totali_Necessarie / Risorse_Per_Nodo) + Nodi_Ridondanza

Dove:
  Nodi_Ridondanza = almeno 1 (N+1)
                    2 per ambienti mission-critical (N+2)
```

#### Requisiti di Quorum

Il cluster Proxmox utilizza Corosync per il clustering e richiede un quorum per operare:

| Nodi Totali | Quorum | Nodi che Possono Fallire | Note |
|-------------|--------|--------------------------|------|
| 2 | 2 | 0 (senza QDevice) | **Non raccomandato** senza QDevice |
| 2 + QDevice | 2 | 1 | QDevice su terzo host leggero |
| 3 | 2 | 1 | Configurazione minima raccomandata |
| 4 | 3 | 1 | Nessun vantaggio rispetto a 3 nodi |
| 5 | 3 | 2 | Buono per ambienti critici |
| 6 | 4 | 2 | Nessun vantaggio rispetto a 5 |
| 7 | 4 | 3 | Configurazione ampia |

**Regola pratica**: utilizzare sempre un numero dispari di nodi (3, 5, 7) per il quorum ottimale. Se si hanno nodi pari, aggiungere un QDevice.

```
Cluster a 3 nodi con N+1:

  ┌─────────┐  ┌─────────┐  ┌─────────┐
  │ Nodo 1  │  │ Nodo 2  │  │ Nodo 3  │
  │ 48C/512G│  │ 48C/512G│  │ 48C/512G│
  │         │  │         │  │         │
  │ Carico: │  │ Carico: │  │ Carico: │
  │ 66% max │  │ 66% max │  │ 66% max │
  └────┬────┘  └────┬────┘  └────┬────┘
       │            │            │
       └────────────┼────────────┘
                    │
              Corosync Ring
              (quorum: 2/3)

  Se Nodo 3 fallisce:
  ┌─────────┐  ┌─────────┐  ┌─────────┐
  │ Nodo 1  │  │ Nodo 2  │  │ Nodo 3  │
  │ Carico: │  │ Carico: │  │  XXXXX  │
  │ 100%    │  │ 100%    │  │  DOWN   │
  └─────────┘  └─────────┘  └─────────┘
  Quorum mantenuto (2/3). VM di Nodo 3 ridistribuite su 1 e 2.
```

### Formula Dimensionamento Nodi

```
Per un cluster N+1 a 3 nodi, ogni nodo deve avere:

  CPU_per_nodo  = (vCPU_totali_necessarie / (N_nodi - 1)) / Target_Overcommit
  RAM_per_nodo  = (vRAM_totale_necessaria / (N_nodi - 1)) / Target_Overcommit_RAM + Overhead_Host

Esempio:
  vCPU totali: 400
  vRAM totale: 1200 GB
  Nodi: 3 (N+1, quindi capacity per 2)
  Overcommit CPU: 3:1
  Overcommit RAM: 1:1

  CPU_per_nodo = (400 / 2) / 3 = ~67 core fisici → server dual-socket con CPU 32+ core
  RAM_per_nodo = (1200 / 2) / 1 + 8 = 608 GB → arrotondare a 640 GB o 768 GB
```

---

## Capacity Planning Storage: Ceph, NFS, iSCSI

### Ceph Nativo in Proxmox

Ceph è la soluzione di storage distribuito integrata nativamente in Proxmox, ed è spesso la scelta preferita per ambienti iperconvergenti.

#### Sizing Ceph

```
Capacità_Raw_Ceph = Capacità_Utile_Necessaria × Fattore_Replica × Fattore_Overhead

Dove:
  Fattore_Replica = 3 per replica 3x (raccomandato), 2 per replica 2x (minimo)
  Fattore_Overhead = 1.10 - 1.15 (BlueStore overhead, metadati, journaling)

Per Erasure Coding (EC):
  Fattore_EC = (k + m) / k
  Esempio: EC 4+2 → fattore 1.5 (più efficiente di replica 3x ma non adatto a RBD per VM)
```

**Esempio Ceph sizing**:

```
Dati dall'assessment VMware:
  Storage usato effettivo: 15 TB
  Crescita prevista 2 anni: 30%
  Tipo: replica 3x

Calcolo:
  Utile con crescita: 15 TB × 1.30 = 19.5 TB
  Raw necessario:     19.5 TB × 3 = 58.5 TB
  Con overhead:       58.5 TB × 1.12 = 65.5 TB
  Arrotondato:        66 TB raw

Distribuzione su 3 nodi:
  22 TB raw per nodo
  Con SSD NVMe da 3.84 TB: 6 dischi per nodo
  Con SSD SATA da 7.68 TB: 3 dischi per nodo
```

#### Configurazione Minima Ceph per Proxmox

| Componente | Minimo | Raccomandato | Note |
|-----------|--------|--------------|------|
| Nodi (MON + OSD) | 3 | 5+ | Numero dispari per quorum MON |
| OSD per nodo | 1 | 3-6 | Bilanciare performance e capacità |
| RAM per OSD | 2 GB | 4-5 GB | BlueStore usa meno RAM di FileStore |
| CPU per OSD | 1 core | 2 core | Importante per recovery e scrubbing |
| Network OSD | 10 GbE | 25 GbE | Rete dedicata (cluster network) |
| DB/WAL device | Stesso OSD | NVMe separato | Migliora latenza significativamente |
| Tipo OSD (produzione) | SSD SATA | NVMe | HDD solo per archive/backup |

#### Rete Ceph

```
┌──────────┐    Public Network (10.0.0.0/24)    ┌──────────┐
│  Nodo 1  │◄──────────── 10 GbE ──────────────►│  Nodo 2  │
│  3× OSD  │                                     │  3× OSD  │
│  MON+MGR │    Cluster Network (10.0.1.0/24)   │  MON     │
│          │◄──────────── 25 GbE ──────────────►│          │
└─────┬────┘                                     └────┬─────┘
      │              ┌──────────┐                      │
      │              │  Nodo 3  │                      │
      └──────────────┤  3× OSD  ├──────────────────────┘
         (entrambe   │  MON+MGR │   (entrambe
          le reti)   └──────────┘    le reti)

Public Network:  traffico client (VM I/O) + MON communication
Cluster Network: replica OSD, recovery, scrubbing (traffico intenso)
```

### NFS Storage

Per ambienti che utilizzano già NAS/NFS:

```
Sizing NFS per Proxmox:
  - Protocollo: NFSv4.1 (raccomandato per performance e sicurezza)
  - MTU: 9000 (jumbo frame) se supportato
  - Bandwidth necessaria: IOPS_totali × Block_size_medio
  - Latenza target: < 2 ms per workload normali, < 1 ms per database

Esempio:
  50 VM con I/O medio di 500 IOPS ciascuna, block size 8K
  Bandwidth = 50 × 500 × 8K = 200 MB/s → 2 Gbps sustained
  Con overhead protocollo: 2 Gbps × 1.2 = 2.4 Gbps
  Raccomandazione: 10 GbE minimo, 2× 10 GbE con bonding per ridondanza
```

### iSCSI Storage

```
Sizing iSCSI per Proxmox:
  - Multipath: obbligatorio per produzione (dm-multipath)
  - MTU: 9000 (jumbo frame) se possibile
  - CHAP authentication: abilitare per sicurezza
  - iSER (iSCSI Extensions for RDMA): se disponibile, riduce latenza

Configurazione LUN:
  - 1 LUN per VM (approccio diretto) → semplice ma meno flessibile
  - LUN grandi con LVM-thin sopra → più flessibile, thin provisioning
```

---

## Raccolta Baseline di Performance

### Metriche da Raccogliere

Prima della migrazione, raccogliere una baseline di performance su VMware per validare le performance post-migrazione su Proxmox:

```powershell
# Baseline completa: CPU, RAM, Disk, Network per 7 giorni (campionamento orario)
$period = 7
$start = (Get-Date).AddDays(-$period)

Get-VM | Where-Object PowerState -eq "PoweredOn" | ForEach-Object {
    $vm = $_
    $stats = @{
        CpuUsage    = Get-Stat -Entity $vm -Stat "cpu.usage.average" -Start $start -IntervalMins 60
        MemUsage    = Get-Stat -Entity $vm -Stat "mem.usage.average" -Start $start -IntervalMins 60
        DiskRead    = Get-Stat -Entity $vm -Stat "disk.read.average" -Start $start -IntervalMins 60
        DiskWrite   = Get-Stat -Entity $vm -Stat "disk.write.average" -Start $start -IntervalMins 60
        NetRx       = Get-Stat -Entity $vm -Stat "net.received.average" -Start $start -IntervalMins 60
        NetTx       = Get-Stat -Entity $vm -Stat "net.transmitted.average" -Start $start -IntervalMins 60
    }

    [PSCustomObject]@{
        VMName           = $vm.Name
        CpuAvg           = [math]::Round(($stats.CpuUsage | Measure-Object Value -Average).Average, 1)
        CpuP95           = [math]::Round(($stats.CpuUsage | Sort-Object Value | Select-Object -Skip ([math]::Floor($stats.CpuUsage.Count * 0.95)) -First 1).Value, 1)
        MemAvg           = [math]::Round(($stats.MemUsage | Measure-Object Value -Average).Average, 1)
        MemMax           = [math]::Round(($stats.MemUsage | Measure-Object Value -Maximum).Maximum, 1)
        DiskReadKBps     = [math]::Round(($stats.DiskRead | Measure-Object Value -Average).Average, 0)
        DiskWriteKBps    = [math]::Round(($stats.DiskWrite | Measure-Object Value -Average).Average, 0)
        DiskReadMaxKBps  = [math]::Round(($stats.DiskRead | Measure-Object Value -Maximum).Maximum, 0)
        DiskWriteMaxKBps = [math]::Round(($stats.DiskWrite | Measure-Object Value -Maximum).Maximum, 0)
        NetRxKBps        = [math]::Round(($stats.NetRx | Measure-Object Value -Average).Average, 0)
        NetTxKBps        = [math]::Round(($stats.NetTx | Measure-Object Value -Average).Average, 0)
    }
} | Export-Csv -Path "C:\Reports\performance_baseline.csv" -NoTypeInformation
```

### Criteri di Validazione Post-Migrazione

| Metrica | Tolleranza Accettabile | Azione se Fuori Tolleranza |
|---------|----------------------|---------------------------|
| CPU usage | ±10% rispetto a baseline | Verificare CPU pinning, NUMA |
| Latenza I/O | +20% max | Verificare storage backend, driver virtio |
| Throughput I/O | -10% max | Verificare queue depth, I/O scheduler |
| Network throughput | ±5% | Verificare driver NIC, MTU |
| Boot time | +30% max | Verificare BIOS/UEFI settings |

---

## Esempi di Calcolo Completi

### Scenario: Azienda Media (127 VM)

**Dati dall'assessment VMware:**

```
Ambiente VMware corrente:
  Cluster: 1 (CL-PROD)
  Host ESXi: 4 × Dell R740xd
    - 2× Intel Xeon Gold 6248R (24C/48T) = 48 core / 96 thread per host
    - 768 GB RAM per host
    - 192 core fisici totali, 384 thread
    - 3072 GB RAM totale

  VM totali: 127 (112 accese, 15 spente)
  vCPU allocate totali: 468
  vRAM allocata totale: 1840 GB

  Overcommit corrente:
    CPU: 468/192 = 2.44:1 (basato su core, 1.22:1 basato su thread)
    RAM: 1840/3072 = 0.60:1 (nessun overcommit RAM)

  Storage:
    SAN iSCSI: 4 datastore VMFS6
    Provisioned totale: 28 TB
    Used totale: 12.5 TB
    Thin ratio: 44.6%

  Performance medie (30 giorni):
    CPU utilizzo medio cluster: 35%
    CPU utilizzo P95: 62%
    RAM utilizzo medio: 58%
    RAM utilizzo P95: 74%
    IOPS medio aggregato: 15000
    IOPS P95: 28000
```

**Calcolo dimensionamento Proxmox:**

```
═══════════════════════════════════════════
  SIZING CPU
═══════════════════════════════════════════
  vCPU effettive al P95: 468 × 0.62 = 290
  Con crescita 20%:      290 × 1.20 = 348
  Overhead KVM:          348 × 1.03 = 358
  Target overcommit:     3:1

  pCPU necessari = 358 / 3 = 120 core

  Con N+1 (3 nodi, capacity per 2):
    120 / 2 = 60 core per nodo
    → Server dual-socket con CPU 32+ core
    → Esempio: 2× AMD EPYC 9354 (32C/64T) = 64 core per nodo

═══════════════════════════════════════════
  SIZING RAM
═══════════════════════════════════════════
  RAM effettiva al P95:  1840 × 0.74 = 1362 GB
  Con crescita 20%:      1362 × 1.20 = 1634 GB
  Overhead host (8 GB × 3): 24 GB
  Target overcommit:     1:1

  RAM totale = 1634 + 24 = 1658 GB

  Con N+1 (3 nodi, capacity per 2):
    1658 / 2 = 829 GB per nodo
    → Arrotondamento: 896 GB per nodo (14× 64 GB DIMM)
    → O più conservativo: 1024 GB per nodo (16× 64 GB DIMM)

═══════════════════════════════════════════
  SIZING STORAGE (Ceph replica 3x)
═══════════════════════════════════════════
  Storage usato attuale: 12.5 TB
  Con crescita 30%:      12.5 × 1.30 = 16.25 TB (utile netto)
  Replica 3x:            16.25 × 3 = 48.75 TB
  Overhead BlueStore:    48.75 × 1.12 = 54.6 TB raw

  Per nodo (3 nodi):     54.6 / 3 = 18.2 TB
  → 5× SSD NVMe 3.84 TB per nodo = 19.2 TB per nodo

  IOPS check:
    IOPS P95: 28000
    SSD NVMe tipico: 100000+ IOPS per disco
    5 OSD per nodo × 3 nodi = 15 OSD
    Replica 3x: ogni write = 3 write OSD
    IOPS scrittura effettivi: ~28000 × 0.3 (30% write) × 3 = 25200 write IOPS
    IOPS lettura:             ~28000 × 0.7 = 19600 read IOPS
    Capacità IOPS cluster:    15 × 100000 = 1.5M IOPS → ampiamente sufficiente

═══════════════════════════════════════════
  SIZING NETWORK
═══════════════════════════════════════════
  Management/VM:    2× 10 GbE (bonding LACP)
  Ceph public:      1× 25 GbE
  Ceph cluster:     1× 25 GbE
  Totale NIC:       4+ porte per nodo

═══════════════════════════════════════════
  RIEPILOGO CONFIGURAZIONE PER NODO (×3)
═══════════════════════════════════════════
  CPU:     2× AMD EPYC 9354 (32C/64T)
  RAM:     1024 GB (16× 64 GB DDR5-4800)
  Boot:    2× 480 GB SSD SATA (mirror ZFS)
  OSD:     5× 3.84 TB NVMe SSD
  NIC:     2× 10 GbE + 2× 25 GbE
  Costo stimato per nodo: €15,000 - €25,000
  Costo cluster (3 nodi): €45,000 - €75,000
```

---

## Best Practices

- **Dimensionare sempre sulla base dei dati reali, non sulle allocazioni**. L'errore più comune è replicare le allocazioni VMware (che includono anni di overprovisioning) nell'ambiente Proxmox. Usare i dati di consumo effettivo come base.
- **Utilizzare il percentile 95 (P95), non la media, per il sizing**. La media nasconde i picchi. Il P95 garantisce che il sistema gestisca il carico nel 95% del tempo senza contesa.
- **Pianificare la crescita ma non esagerare**. Un fattore di crescita del 20-30% per 2 anni è ragionevole. Fattori superiori al 50% portano a sovradimensionamento e spreco.
- **Separare la rete Ceph dalla rete VM**. Ceph genera traffico significativo di replica e recovery che può saturare la rete se condivisa con il traffico delle VM. Dedicare interfacce separate a 25 GbE per il cluster network di Ceph.
- **Testare le performance prima della migrazione di massa**. Dopo il setup del cluster Proxmox, eseguire benchmark sintetici (fio per storage, stress-ng per CPU) e confrontare con le baseline VMware.
- **Non sottostimare la RAM per Ceph OSD**. Ogni OSD BlueStore richiede 3-5 GB di RAM. Con 5 OSD per nodo, sono 15-25 GB di RAM dedicati solo a Ceph.
- **Preferire nodi omogenei**. Nodi con configurazioni diverse complicano il capacity planning e il bilanciamento dei workload. Se possibile, acquistare hardware identico per tutti i nodi.
- **Documentare tutte le assunzioni del sizing**. Ogni numero nel calcolo ha un'assunzione dietro (fattore di crescita, overcommit target, overhead). Documentarle esplicitamente per poterle rivalutare se le condizioni cambiano.
- **Prevedere un periodo di coesistenza**. Durante la migrazione, VMware e Proxmox coesisteranno. Calcolare le risorse necessarie per questa fase transitoria.

---

## Troubleshooting

### Problema: Performance CPU degradate dopo migrazione a Proxmox
**Sintomi**: VM migrate mostrano utilizzo CPU più alto del 20-30% rispetto alla baseline VMware per lo stesso workload.
**Causa**: Mancata configurazione NUMA topology, CPU type non ottimale, mancato CPU pinning per workload latency-sensitive, o mismatch tra CPU model del guest e feature fisiche disponibili.
**Soluzione**: Configurare la topologia NUMA nel file di configurazione della VM Proxmox:
```
# /etc/pve/qemu-server/<vmid>.conf
numa: 1
cpu: host                    # Espone tutte le feature CPU fisiche al guest
sockets: 2
cores: 8
# Per CPU pinning (workload critici):
affinity: 0-15               # Pinning su core 0-15
```
Verificare con `numactl --hardware` sul nodo Proxmox e con `lscpu` nel guest.
**Prevenzione**: Configurare `cpu: host` e NUMA topology per tutte le VM di produzione durante la migrazione, non dopo.

### Problema: Ceph pool pieno o near-full warning
**Sintomi**: Warning `HEALTH_WARN: 1 nearfull osd(s)` o `HEALTH_ERR: 1 full osd(s)`. Le VM non riescono a scrivere su disco.
**Causa**: Sizing storage insufficiente, crescita non prevista, sbilanciamento PG tra OSD, o snapshot che consumano spazio aggiuntivo.
**Soluzione**:
```bash
# Verificare stato cluster
ceph status
ceph osd df tree

# Verificare utilizzo pool
ceph df detail

# Se un singolo OSD è pieno, ribilanciare
ceph osd reweight-by-utilization

# In emergenza, alzare temporaneamente la soglia
ceph osd set-full-ratio 0.97
ceph osd set-nearfull-ratio 0.90
```
**Prevenzione**: Monitorare proattivamente lo spazio Ceph con alert al 70% e 80%. Pianificare expansion prima di raggiungere l'85%.

### Problema: Latenza I/O elevata su Ceph
**Sintomi**: Latenza I/O delle VM superiore a 5-10 ms, significativamente peggiore della baseline VMware.
**Causa**: Rete cluster saturata, OSD su disco lento (SATA vs NVMe), mancanza di WAL/DB dedicato, cluster in recovery/rebalancing.
**Soluzione**: Verificare la rete cluster (`ceph osd perf`), controllare lo stato dei dischi (`smartctl`), verificare se il cluster è in recovery (`ceph -s`). Se la rete cluster è saturata, migrare a interfacce più veloci. Se gli OSD sono lenti, spostare WAL/DB su NVMe dedicato.
**Prevenzione**: Dimensionare la rete cluster adeguatamente (25 GbE minimo per produzione), utilizzare NVMe per gli OSD, e dedicare dispositivi separati per WAL/DB.

### Problema: Nodo Proxmox esaurisce la RAM fisica
**Sintomi**: Il nodo inizia a swappare, le VM rallentano drasticamente, possibili OOM kill di processi.
**Causa**: Overcommit RAM eccessivo, memory leak in una VM, crescita non pianificata, Ceph OSD che consumano più RAM del previsto.
**Soluzione**: Identificare le VM con consumo anomalo (`qm monitor <vmid>` → `info balloon`), ridistribuire VM su altri nodi con `qm migrate`, configurare memory limits nelle VM. In emergenza, aumentare lo swap temporaneamente.
**Prevenzione**: Non superare un overcommit RAM di 1.2:1 per workload di produzione. Monitorare il consumo RAM reale (non solo allocato) con Proxmox metrics o strumenti esterni.

### Problema: Quorum perso dopo failure di un nodo
**Sintomi**: Il cluster Proxmox diventa read-only o non responsivo. Le VM non possono essere avviate o migrate.
**Causa**: In un cluster a 3 nodi, la perdita di 2 nodi causa perdita del quorum. In un cluster a 2 nodi senza QDevice, la perdita di 1 nodo causa perdita del quorum.
**Soluzione**:
```bash
# Forzare il quorum (solo in emergenza, rischio split-brain)
pvecm expected 1

# Verificare stato corosync
pvecm status

# Dopo il ripristino dei nodi, ripristinare il quorum normale
pvecm expected <numero_nodi_originale>
```
**Prevenzione**: Utilizzare sempre almeno 3 nodi. Per cluster a 2 nodi, configurare un QDevice. Per ambienti critici, utilizzare 5 nodi.

---

## Riferimenti

- Proxmox VE Administration Guide — Cluster Manager: https://pve.proxmox.com/pve-docs/pve-admin-guide.html#chapter_pvecm
- Proxmox VE — Ceph Documentation: https://pve.proxmox.com/pve-docs/pve-admin-guide.html#chapter_pveceph
- Ceph Documentation — Hardware Recommendations: https://docs.ceph.com/en/latest/start/hardware-recommendations/
- Red Hat — KVM Performance Tuning: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_and_managing_virtualization/optimizing-virtual-machine-performance-in-rhel_configuring-and-managing-virtualization
- VMware vSphere Resource Management Guide: https://docs.vmware.com/en/VMware-vSphere/8.0/vsphere-resource-management/GUID-98BD5A8A-260A-494F-BAAE-74781F5C4B87.html
- Linux Kernel — KSM Documentation: https://www.kernel.org/doc/html/latest/admin-guide/mm/ksm.html
- fio — Flexible I/O Tester: https://fio.readthedocs.io/en/latest/

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — DDR5 ECC RDIMM su EPYC Genoa/Bergamo/Turin.** Le piattaforme server moderne (2023+) sono passate a DDR5-4800/5600 ECC RDIMM con vantaggi misurabili in throughput per VM density. Su EPYC Bergamo (128 core Zen 4c per socket) la regola pratica e ~16 GB RAM per core fisico (2 TB per socket); su Turin (Zen 5, 192 core) il rapporto e simile ma con efficienza energetica migliore. Per cluster Proxmox a densita alta, valutare 2-socket EPYC Bergamo/Turin con 1-2 TB RAM per nodo. Costo: la differenza 256 GB DDR4 → 256 GB DDR5 e ~20-30% sul ticket RAM. ROI: su 100+ VM per nodo, throughput aggregato giustifica. Riferimento: AMD EPYC official datasheet, ServerHome benchmarks.

> **Errore comune — dimensionamento "media + 20%".** Il calcolo "media CPU * 1.2" non tiene conto della varianza: workload con peak orari (es. ETL notturno, batch giornaliero) richiede capacity per il peak, non per la media. La formula corretta e `capacity = peak_p99 + safety_margin (10-20%)`. Per workload con varianza alta, considerare cluster multipli (uno per workload class) anziche cluster mostro con sovrastima.

> **Caso reale — Ceph all-flash ma CPU underprovisioned.** Un cluster Ceph all-NVMe con 3 nodi (8-core CPU ciascuno) ha mostrato latenze p99 > 50 ms su workload random write 4K, contro target di 5 ms. Causa: Ceph OSD all-flash satura le CPU (ogni OSD usa 4-6 thread, 8 OSD per nodo = 32-48 thread, vs 16 thread CPU). Soluzione: dual-socket nodi con 32+ core ciascuno; in alternativa, ridurre OSD per nodo o passare a mid-range NVMe (meno IOPS ma ratio CPU:OSD meglio bilanciato). Lezione: Ceph all-flash *richiede* CPU robusta, non si scappa.

---

## Esercizi

1. **Concettuale — overcommit cap.** Per un cluster Proxmox di 3 nodi 32-core (96 core totali, no SMT), spiegare in 5 righe quale e l'overcommit massimo per CPU "safe" assumendo che (a) i workload sono web app a basso utilizzo, (b) sono DB OLTP ad alta utilizzazione. *Risposta:* (a) 8:1 → 768 vCPU totali allocabili, ragionevole con monitoring per ready time < 5%; (b) 2:1 → 192 vCPU, perche DB sono CPU-bound e ready time > 5% degrada le query.

2. **Lab — baseline `fio` su VM esistente.** Su una VM VMware in produzione (che andra migrata), eseguire `fio --name=oltp --rw=randrw --bs=4k --iodepth=32 --runtime=300 --rwmixread=70 --size=10G` e raccogliere IOPS p50/p95/p99 e latenza. Ripetere lo stesso `fio` sulla VM dopo migrazione su Proxmox (stesso storage tier). Confrontare. Documentare in `baseline-perf-VMNAME.md`. Goal: validare che il dimensionamento Proxmox preserva o migliora le metriche.

3. **Scenario — sizing per 80 VM eterogenee.** Dato un parco di 80 VM con totale: 240 vCPU, 720 GB RAM, 24 TB storage utilizzato (su 36 TB allocato), media 200 IOPS per VM con peak 2000 IOPS per le top 5. Proporre 3 dimensionamenti del cluster Proxmox target: (a) economy (3 nodi, NFS centralizzato), (b) balanced (3 nodi Ceph all-flash), (c) premium (5 nodi Ceph hybrid + 100 GbE). Per ognuno: BOM hardware (CPU, RAM, dischi, NIC), capex stimato (range), pro/contro, risk profile.

4. **Stretch — script di sizing automatico.** Scrivere uno script Python che legge `vm-inventory.csv` (modulo 05.1), calcola somme + p99 per CPU/RAM/IOPS/throughput, e produce 3 proposte di sizing applicando le regole di overcommit di questo modulo. Output: `sizing-proposals.md` con tabelle markdown leggibili. Bonus: aggiungere un campo "rationale" per ogni decisione (es. "scelti 3 nodi 64-core per overcommit 4:1 su 240 vCPU + margine N+1").

## Auto-valutazione

1. Cosa significa "overcommit ratio 4:1" per la CPU e quando e ragionevole?
2. KSM: cosa fa, quale risparmio tipico, quale costo CPU?
3. NUMA: come si verifica la topologia su un nodo Proxmox e quando va vincolata una VM a un singolo socket?
4. Differenza fra `iostat -xdz` e `fio` per misurare performance disco — quando l'uno e l'altro?
5. Capacity per N+1 vs N+2: formule e quando si applica una vs l'altra?
6. Replication factor di Ceph: minimum produzione e perche?
7. Cosa fa `qm config <vmid> | grep numa` e cosa indica `numa: 1`?
8. DDR4 vs DDR5 ECC: differenze di latenza e throughput in ambito server, cosa scegliere?

## Letture primarie consigliate

- [`PVE-ADMIN`] Proxmox VE Administration Guide — capitolo "QEMU/KVM" (sezione NUMA, KSM). https://pve.proxmox.com/pve-docs/pve-admin-guide.html
- [`CEPH-DOCS`] Ceph — Hardware Recommendations. https://docs.ceph.com/en/latest/start/hardware-recommendations/
- Red Hat — KVM Performance Tuning. https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_and_managing_virtualization/optimizing-virtual-machine-performance-in-rhel_configuring-and-managing-virtualization
- VMware vSphere Resource Management Guide. https://docs.vmware.com/en/VMware-vSphere/8.0/vsphere-resource-management/GUID-98BD5A8A-260A-494F-BAAE-74781F5C4B87.html
- Linux Kernel — KSM Documentation. https://www.kernel.org/doc/html/latest/admin-guide/mm/ksm.html
- fio — Flexible I/O Tester. https://fio.readthedocs.io/en/latest/
- Brendan Gregg — USE Method (per identificare bottleneck). https://www.brendangregg.com/usemethod.html

## Collegamenti incrociati

- Modulo 05.1 — `inventario-vmware-assessment.md`: input dei volumi totali da dimensionare.
- Modulo 05.2 — `analisi-dipendenze-e-criticita.md`: input della classificazione per applicare margini differenti per tier.
- Modulo 05.4 — `timeline-e-risk-assessment.md`: timeline di approvvigionamento hardware.
- Modulo 03.1 — `../03-STORAGE-AVANZATO-PROXMOX/lvm-e-lvm-thin-proxmox.md`: backend LVM-Thin.
- Modulo 03.2 — `../03-STORAGE-AVANZATO-PROXMOX/nfs-iscsi-storage-condiviso.md`: backend NFS/iSCSI.
- Modulo 13.1 — `../13-MONITORAGGIO-E-OTTIMIZZAZIONE/zabbix-monitoraggio-proxmox.md`: monitoring delle metriche dimensionate.
- Modulo 17.4 — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-storage-performance.md`: troubleshooting performance.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Overcommit ratio** | Rapporto vCPU:pCPU (o vRAM:pRAM) ammesso per un cluster. CPU 4:1, RAM 1.2:1 sono valori conservativi. |
| **NUMA** | Non-Uniform Memory Access — architettura multi-socket dove ogni CPU ha la sua memoria locale; cross-socket costa latenza. |
| **NUMA boundary** | Numero di vCPU per VM oltre il quale la VM tocca piu socket → degrada. |
| **CPU pinning** | Assegnazione esplicita di vCPU a pCPU specifici (`taskset`, `cpu-pinning` Proxmox). |
| **Memory binding** | Vincolo memoria di una VM a un socket NUMA specifico. |
| **KSM (Kernel Same-page Merging)** | Deduplicazione di pagine RAM identiche fra VM. Risparmio 20-30% per VM omogenee. |
| **Balloon driver** | Driver virtio-balloon che permette al host di recuperare RAM da una VM. |
| **N+1 / N+2** | Resilienza: cluster regge la perdita di 1 / 2 nodi senza interruzione. |
| **Replication factor** | In Ceph: numero di copie di ogni oggetto. Min 3 per produzione. |
| **IOPS p99** | Numero di IOPS che il 99% delle richieste riesce a completare entro la latenza target. |
| **Latenza p99** | Latenza max sotto la quale stanno il 99% delle richieste. |
| **fio** | Tool di benchmark I/O Linux, granulare e configurabile. |
| **`pveperf`** | Tool Proxmox per benchmark veloce di CPU, FSYNC, DNS, regex (run di sintesi). |
| **DDR5 ECC RDIMM** | DDR5 con Error-Correcting Code, registered, per server. Latenza CL40-46 a 4800-5600 MT/s. |
| **EPYC Genoa/Bergamo/Turin** | Codename CPU AMD Zen 4 / Zen 4c / Zen 5 (2022-2024). |
| **Xeon Sapphire/Emerald/Granite Rapids** | Codename CPU Intel Xeon-SP 4th/5th/6th gen (2023-2025). |
