# Conversione Dischi Virtuali: VMDK verso qcow2 e raw

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 08.1 (apre il cluster storage, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 03.1, 03.2 (storage Proxmox); modulo 06.2 (virt-v2v); concetti formati disco (sparse, thick, thin), CoW, fiemap.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. distinguere le 3 varianti VMDK (descriptor + flat singolo, descriptor + split a 2 GB, monolithic), e i 3 sub-tipi VMware (thick eager-zeroed, thick lazy-zeroed, thin) leggendo l'header con `qemu-img info`;
> 2. scegliere il formato target Proxmox piu appropriato — qcow2 (snapshot interni, thin), raw (massima performance, no snapshot del file ma del backend), LVM-Thin (thin native), ZFS (CoW + snapshot atomico) — sulla base di workload e backend;
> 3. eseguire conversioni con `qemu-img convert` ottimizzate (`-p` progress, `-W` parallel, `-S` sparse, `-c` compress, `-o preallocation=` per LVM/raw);
> 4. ottimizzare le performance di conversione (flag `-W -m N`, choice di cache mode, isolare temp dir su SSD diverso);
> 5. validare il post-convert con: `qemu-img check`, `qemu-img info`, MD5/SHA-256 sul filesystem montato (NON sul disco a livello di byte — i metadati cambiano), boot test;
> 6. gestire le implicazioni di thick → thin (recupero spazio sparse, fstrim post-import) e thin → thick (preallocation se serve performance prevedibile);
> 7. troubleshootare i problemi tipici: "split VMDK file descriptor mancante", "VMDK locked", "spazio temporaneo esaurito", "checksum mismatch dopo convert".
> **Tempo stimato:** lettura 90-120 min · lab 240-360 min
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** qemu-img 8.x+, QEMU 8.x/9.x/10.x; VMware VMDK spec v9; LVM 2.03+; OpenZFS 2.2/2.3.

## Mappa concettuale

```
+======================================================+
|  Conversione disco VMDK → Proxmox: pipeline          |
+======================================================+
|                                                      |
|   SOURCE                                             |
|     +-- VMDK descriptor (.vmdk testuale)            |
|     +-- VMDK flat (-flat.vmdk binario)               |
|     +-- (opzionale) split a 2 GB: -s001.vmdk, ...    |
|         |                                            |
|         v                                            |
|   PRE-CHECK                                          |
|     +-- qemu-img info disk.vmdk                     |
|         (formato, virtual size, allocated)          |
|     +-- consolidare snapshot VMware                 |
|     +-- verificare spazio temp dir (>= virt size)   |
|         |                                            |
|         v                                            |
|   QEMU-IMG CONVERT                                   |
|     +-- -p progress                                  |
|     +-- -W -m N: parallel I/O (N threads)           |
|     +-- -S 4k: sparse hole detection                |
|     +-- -O qcow2 / -O raw / -O luks                 |
|     +-- -o preallocation=metadata|falloc|full       |
|     +-- -o cluster_size=64K (qcow2 default 64K)     |
|     +-- -t writeback / writethrough / none          |
|         |                                            |
|         v                                            |
|   POST-CONVERT VALIDATION                            |
|     +-- qemu-img check disk.qcow2                   |
|     +-- qemu-img info disk.qcow2                    |
|     +-- mount + checksum filesystem (sample)        |
|     +-- boot test (qm start)                        |
|         |                                            |
|         v                                            |
|   IMPORT IN PROXMOX                                  |
|     +-- qm importdisk <vmid> file.qcow2 <storage>   |
|     +-- qm set --scsi0 ...,iothread=1,discard=on    |
|     +-- qm start                                     |
|     +-- (se thin) fstrim -av nel guest              |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **VMDK e un descriptor + dati. Sempre.** Il file `.vmdk` testuale (anche se si chiama come il dato) e *solo descrittore*; punta al `-flat.vmdk` o ai split. Se manca il descriptor, qemu-img puo ancora convertire ma serve specificare `-f raw` (trattando il flat come binario lineare).
2. **Split VMDK a 2 GB e una scelta storica.** VMware spezza i flat ogni 2 GB su FAT32 datastore (limite). Su VMFS moderno spesso non serve. Per la conversione qemu-img legge automaticamente i split via il descriptor. Se i split sono presenti senza descriptor: `cat *-s*.vmdk > flat.vmdk; qemu-img convert -f raw -O qcow2 flat.vmdk dest.qcow2`.
3. **`-W -m N` parallel I/O e gratis.** `-W` (out-of-order writes) + `-m N` (N coroutines parallele) accelera fino a 3x su NVMe. Default e single-thread, troppo lento per dischi grandi.
4. **`preallocation` cambia tutto sulle performance.** Per qcow2: `metadata` (default, allocazione lazy ma metadata pre-allocati), `falloc` (pre-alloca via fallocate, sparse), `full` (pre-alloca completa, non sparse). Per raw su LVM: la pre-allocazione e a livello LVM (`lvcreate -L size`). `full` per workload mission-critical che non vogliono spike di latenza durante grow; `metadata` per la maggioranza.
5. **Thick → thin: spazio recuperato dopo import + fstrim.** Una conversione thick-eager → qcow2 sparse riduce dimensioni sul disco se i blocchi azzerati sono molti. Per recuperare *davvero*, serve `fstrim -av` *dentro al guest* dopo l'import — manda TRIM/UNMAP allo storage, che marka i blocchi liberi come ri-allocabili. Su LVM-Thin: `lvs` mostra `Data%` ridotto.

## Indice
- [Panoramica](#panoramica)
- [Anatomia del Formato VMDK](#anatomia-del-formato-vmdk)
- [Formati Disco in Proxmox VE](#formati-disco-in-proxmox-ve)
- [Preparazione alla Conversione](#preparazione-alla-conversione)
- [qemu-img convert: Guida Approfondita](#qemu-img-convert-guida-approfondita)
- [Gestione dei File Sparse](#gestione-dei-file-sparse)
- [Ottimizzazione delle Performance di Conversione](#ottimizzazione-delle-performance-di-conversione)
- [Stima dei Tempi di Conversione](#stima-dei-tempi-di-conversione)
- [Verifica Post-Conversione](#verifica-post-conversione)
- [Implicazioni Thick-to-Thin](#implicazioni-thick-to-thin)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

La conversione dei dischi virtuali rappresenta uno dei passaggi più critici nella migrazione da VMware a Proxmox VE. Il formato VMDK (Virtual Machine Disk), proprietario di VMware, deve essere trasformato in un formato compatibile con l'ecosistema KVM/QEMU su cui si basa Proxmox. La scelta del formato di destinazione — qcow2, raw, oppure un volume gestito da LVM-thin o ZFS — influenza direttamente le performance, l'efficienza dello storage e le funzionalità disponibili come snapshot e thin provisioning.

Questa guida analizza in profondità le varianti del formato VMDK, i formati supportati da Proxmox, e l'utilizzo avanzato dello strumento `qemu-img` per eseguire conversioni affidabili e performanti. Ogni passaggio è documentato con comandi reali, flag spiegati, e strategie di ottimizzazione che riducono i tempi di migrazione in ambienti enterprise con decine o centinaia di macchine virtuali.

È fondamentale comprendere che la conversione non è un semplice cambio di estensione: i metadati del disco, la struttura di allocazione dei blocchi, la gestione degli snapshot e la compressione cambiano radicalmente tra i formati. Un errore in questa fase può risultare in dischi corrotti, performance degradate o perdita di dati. Per questo motivo, la verifica post-conversione è altrettanto importante quanto la conversione stessa.

---

## Anatomia del Formato VMDK

### Varianti VMDK

VMware utilizza diverse varianti del formato VMDK, ciascuna ottimizzata per scenari specifici. Comprendere queste varianti è essenziale per pianificare la conversione corretta.

#### monolithicSparse

Il tipo più comune per le VM create su VMware Workstation e Fusion. Il disco è contenuto in un singolo file `.vmdk` che cresce dinamicamente man mano che la VM scrive dati. La struttura interna utilizza una grain table con granularità tipica di 64 KB.

```
Struttura file monolithicSparse:
+------------------+
| VMDK Header      |  (settore 0-1)
+------------------+
| Grain Directory  |  (puntatori alle grain tables)
+------------------+
| Grain Tables     |  (mapping blocchi logici → offset fisici)
+------------------+
| Grain Data       |  (blocchi dati effettivi, 64KB ciascuno)
+------------------+
```

Il file descriptor è incorporato nel file binario stesso. La dimensione su disco è inferiore alla dimensione logica del disco virtuale poiché i blocchi non scritti non occupano spazio.

#### monolithicFlat

Disco a provisioning thick in un singolo file. L'intero spazio dichiarato viene allocato immediatamente sul filesystem host. Utilizzato quando si richiedono performance prevedibili e si vuole evitare la frammentazione causata dalla crescita dinamica.

Il file `.vmdk` descrittore è separato dal file `-flat.vmdk` che contiene i dati effettivi:

```
vm-disk.vmdk          → file descrittore (pochi KB, testo)
vm-disk-flat.vmdk     → file dati (dimensione completa del disco)
```

#### vmfsSparse (VMFS Sparse)

Utilizzato sugli ESXi datastore VMFS per gli snapshot delle VM. Ogni snapshot genera un file `-delta.vmdk` che contiene solo i blocchi modificati rispetto al parent disk. La chain degli snapshot forma una struttura ad albero:

```
base-disk.vmdk
  └── base-disk-000001.vmdk  (snapshot 1, delta)
        └── base-disk-000002.vmdk  (snapshot 2, delta)
              └── base-disk-000003.vmdk  (snapshot 3, delta - attivo)
```

La granularità dei blocchi delta su VMFS è di 512 byte, il che può causare una significativa frammentazione e degradazione delle performance con snapshot multipli.

#### vmfsFlat (VMFS Flat / Thick)

Il formato standard per i dischi su datastore VMFS negli ambienti ESXi di produzione. Esistono due sotto-varianti:

- **Thick Provision Eager Zeroed**: tutti i blocchi vengono scritti con zeri alla creazione. Massime performance, nessun overhead di allocazione runtime.
- **Thick Provision Lazy Zeroed**: lo spazio è riservato ma i blocchi vengono azzerati solo al primo accesso in scrittura. Creazione più veloce, leggero overhead al primo write.

#### twoGbMaxExtentSparse e twoGbMaxExtentFlat

Varianti legacy dove il disco viene suddiviso in extent da massimo 2 GB ciascuno. Originariamente necessarie per filesystem FAT32. Oggi raramente utilizzate in produzione ma possono essere incontrate in ambienti legacy.

```
vm-disk-s001.vmdk, vm-disk-s002.vmdk, ... (sparse)
vm-disk-f001.vmdk, vm-disk-f002.vmdk, ... (flat)
```

### Identificazione del Tipo VMDK

Per identificare il tipo di VMDK, esaminare il file descrittore:

```bash
# Su ESXi
cat /vmfs/volumes/datastore1/vm-name/vm-disk.vmdk | head -20

# Output tipico:
# ddb.virtualHWVersion = "19"
# ddb.geometry.cylinders = "20805"
# createType="vmfsSparse"
```

Oppure utilizzare `vmkfstools` su ESXi:

```bash
vmkfstools -D /vmfs/volumes/datastore1/vm-name/vm-disk-flat.vmdk
```

Da un host Linux con accesso ai file:

```bash
qemu-img info vm-disk.vmdk
# image: vm-disk.vmdk
# file format: vmdk
# virtual size: 100 GiB (107374182400 bytes)
# disk size: 42.3 GiB
# cluster_size: 65536
# Format specific information:
#     cid: 1234abcd
#     parent cid: ffffffff
#     create type: monolithicSparse
#     extents:
#         [0]:
#             virtual size: 107374182400
#             filename: vm-disk.vmdk
```

---

## Formati Disco in Proxmox VE

### qcow2 (QEMU Copy-On-Write v2)

Formato nativo di QEMU con funzionalità avanzate:

| Caratteristica | Dettaglio |
|---|---|
| Thin provisioning | Nativo, i blocchi non scritti non occupano spazio |
| Snapshot | Interni al file, creazione istantanea |
| Compressione | Supportata per blocco (zlib, zstd) |
| Encryption | LUKS integrato |
| Backing files | Catena di immagini copy-on-write |
| Cluster size | Default 64 KB, configurabile (512B - 2MB) |
| Preallocation | off, metadata, falloc, full |

Il formato qcow2 è ideale per storage basato su filesystem (directory locali, NFS) dove si desidera snapshot e thin provisioning senza dipendere da funzionalità del layer storage sottostante.

### raw

Formato più semplice possibile: mapping 1:1 tra offset nel file e offset sul disco virtuale. Nessun overhead di metadati, nessuna funzionalità avanzata intrinseca.

| Caratteristica | Dettaglio |
|---|---|
| Thin provisioning | Solo tramite sparse files del filesystem host |
| Snapshot | Non supportato nel formato, richiede LVM/ZFS |
| Performance | Massime, zero overhead di traduzione |
| Complessità | Nulla, debugging facilitato |

Il formato raw è preferibile quando lo storage backend fornisce già le funzionalità necessarie: LVM-thin per thin provisioning e snapshot, ZFS per compressione e snapshot, Ceph RBD per replica e thin provisioning.

### LVM-thin Provisioned Volumes

In Proxmox, quando si utilizza LVM-thin come storage backend, il disco della VM è un logical volume thin-provisioned. Il formato del contenuto è raw, ma le funzionalità di thin provisioning e snapshot sono gestite da LVM:

```
+-----------------------------------+
| LVM Thin Pool (es. data/thinpool) |
|  +-----------------------------+  |
|  | LV: vm-100-disk-0 (raw)    |  |
|  | LV: vm-101-disk-0 (raw)    |  |
|  +-----------------------------+  |
+-----------------------------------+
```

### ZFS zvol

Su storage ZFS, i dischi delle VM sono zvol (ZFS volumes), dispositivi a blocchi gestiti da ZFS:

```bash
# Struttura tipica
rpool/data/vm-100-disk-0    # zvol per VM 100
rpool/data/vm-101-disk-0    # zvol per VM 101
```

ZFS fornisce compressione trasparente (lz4, zstd), snapshot, cloni e replica nativa. Il formato del contenuto è raw.

### Matrice di Confronto

```
+------------------+----------+--------+----------+---------+----------+
| Funzionalità     | qcow2    | raw    | LVM-thin | ZFS     | Ceph RBD |
+------------------+----------+--------+----------+---------+----------+
| Thin provision   | Sì       | No*    | Sì       | Sì      | Sì       |
| Snapshot         | Sì       | No     | Sì       | Sì      | Sì       |
| Compressione     | Sì       | No     | No       | Sì      | No**     |
| Live migration   | Sì       | Sì     | No***    | No***   | Sì       |
| Performance I/O  | Buona    | Ottima | Ottima   | Ottima  | Buona    |
| Overhead CPU     | Basso    | Nullo  | Nullo    | Basso   | Basso    |
+------------------+----------+--------+----------+---------+----------+
* Sparse files su ext4/xfs possono simulare thin provisioning
** Compressione lato OSD possibile con BlueStore
*** Richiede shared storage (Ceph, NFS, iSCSI) per live migration
```

---

## Preparazione alla Conversione

### Pulizia degli Snapshot VMware

Prima di convertire un disco VMDK, è **obbligatorio** consolidare tutti gli snapshot. La conversione di un disco con snapshot attivi può risultare in un'immagine incompleta o corrotta.

Su vSphere Client:

1. Selezionare la VM → Snapshots → Manage Snapshots
2. Cliccare "Delete All" per consolidare l'intera catena

Da CLI su ESXi:

```bash
# Elencare gli snapshot
vim-cmd vmsvc/snapshot.get <vmid>

# Rimuovere tutti gli snapshot (consolidamento)
vim-cmd vmsvc/snapshot.removeall <vmid>

# Verificare che non esistano più file delta
ls -la /vmfs/volumes/datastore1/vm-name/*-delta.vmdk
# Non deve restituire risultati
```

Se la consolidazione fallisce (evento noto come "stale snapshot"), procedere manualmente:

```bash
# Verificare la catena di snapshot nel descrittore
cat vm-disk-000002.vmdk | grep parentFileNameHint

# Consolidare manualmente con vmkfstools
vmkfstools -i vm-disk-000002.vmdk vm-disk-consolidated.vmdk -d thin
```

### Spegnimento Pulito della VM

Per garantire la coerenza del filesystem:

```bash
# Dentro la VM (Linux)
sync && sync && sync
fstrim -av    # Se supportato, rilascia blocchi non utilizzati
shutdown -h now

# Dentro la VM (Windows)
# Eseguire Optimize-Volume su tutti i drive
Optimize-Volume -DriveLetter C -ReTrim -Verbose
# Poi spegnimento normale
```

### Esportazione del VMDK

Da ESXi, copiare i file VMDK al host Proxmox:

```bash
# Dal host Proxmox, scaricare via SCP
scp root@esxi-host:/vmfs/volumes/datastore1/vm-name/vm-disk.vmdk /tmp/
scp root@esxi-host:/vmfs/volumes/datastore1/vm-name/vm-disk-flat.vmdk /tmp/

# IMPORTANTE: per monolithicFlat/vmfsFlat servono ENTRAMBI i file
# Il file descrittore (.vmdk) e il file dati (-flat.vmdk)
```

Alternativa con `ovftool` per esportare l'intera VM come OVA:

```bash
ovftool vi://root@esxi-host/vm-name /tmp/vm-name.ova

# Estrarre i VMDK dall'OVA
tar xvf vm-name.ova
# Produce: vm-name.ovf, vm-name-disk1.vmdk, vm-name.mf
```

---

## qemu-img convert: Guida Approfondita

### Sintassi Base

```bash
qemu-img convert [opzioni] -f <formato_sorgente> -O <formato_destinazione> \
    <file_sorgente> <file_destinazione>
```

### Flag Essenziali

#### -p (Progress)

Mostra una barra di progresso durante la conversione. Indispensabile per dischi di grandi dimensioni:

```bash
qemu-img convert -p -f vmdk -O qcow2 source.vmdk dest.qcow2
# (12.34/100%)
```

#### -f (Format)

Specifica il formato sorgente. Se omesso, `qemu-img` tenta il rilevamento automatico. Si raccomanda di specificarlo sempre esplicitamente per evitare falsi rilevamenti:

```bash
# Esplicito (raccomandato)
qemu-img convert -f vmdk -O qcow2 source.vmdk dest.qcow2

# Auto-detect (rischioso con file corrotti o ambigui)
qemu-img convert -O qcow2 source.vmdk dest.qcow2
```

#### -O (Output Format)

Il formato di destinazione. Valori comuni: `qcow2`, `raw`, `vmdk`, `vdi`, `vpc`.

#### -W (Out-of-Order Writes / Parallel Writes)

Flag critico per le performance. Abilita la scrittura parallela e out-of-order, permettendo a `qemu-img` di non dover attendere il completamento di ogni write prima di iniziare il successivo:

```bash
# Senza -W: scritture sequenziali, lente
qemu-img convert -p -f vmdk -O qcow2 source.vmdk dest.qcow2

# Con -W: scritture parallele, significativamente più veloce
qemu-img convert -p -W -f vmdk -O qcow2 source.vmdk dest.qcow2
```

L'incremento di performance con `-W` è tipicamente del 30-200% a seconda dello storage sottostante. Su SSD e NVMe il beneficio è massimo. **Attenzione**: `-W` può mascherare errori di scrittura poiché non verifica l'ordine di completamento. Usare sempre la verifica post-conversione.

#### -c (Compress)

Abilita la compressione per il formato di destinazione (solo qcow2). Ogni cluster viene compresso individualmente con zlib:

```bash
qemu-img convert -p -W -c -f vmdk -O qcow2 source.vmdk dest-compressed.qcow2
```

Considerazioni sulla compressione:

| Aspetto | Impatto |
|---|---|
| Dimensione file | Riduzione 40-70% per OS tipici |
| Velocità scrittura | Più lenta durante la conversione |
| Velocità lettura runtime | Leggero overhead di decompressione |
| CPU durante conversione | Uso significativo, 1 core al 100% |
| Snapshot | I blocchi compressi vengono decompressi alla prima modifica |

**Nota critica**: i cluster compressi in qcow2 non possono essere modificati in-place. Ogni scrittura su un cluster compresso causa la riscrittura dell'intero cluster in forma non compressa. Per dischi di VM in produzione attiva, la compressione qcow2 è sconsigliata. Preferire la compressione a livello di storage (ZFS lz4/zstd).

#### -m (Parallel Workers)

Specifica il numero di coroutine parallele per la conversione. Default: 8.

```bash
# 16 worker paralleli
qemu-img convert -p -W -m 16 -f vmdk -O qcow2 source.vmdk dest.qcow2
```

Valori raccomandati:

| Storage Type | Workers (-m) |
|---|---|
| HDD singolo | 4 |
| RAID HDD | 8 |
| SSD SATA | 8-16 |
| NVMe | 16-32 |
| Storage di rete (NFS) | 4-8 |

Aumentare oltre il valore ottimale non migliora le performance e può peggiorarle per contesa I/O.

#### -o (Output Options)

Opzioni specifiche del formato di destinazione:

```bash
# qcow2 con preallocation dei metadati e cluster size personalizzato
qemu-img convert -p -W -f vmdk -O qcow2 \
    -o preallocation=metadata,cluster_size=2M,compat=1.1,lazy_refcounts=on \
    source.vmdk dest.qcow2

# raw con preallocation completa
qemu-img convert -p -W -f vmdk -O raw \
    -o preallocation=full \
    source.vmdk dest.raw
```

Opzioni qcow2 significative:

| Opzione | Valori | Descrizione |
|---|---|---|
| preallocation | off, metadata, falloc, full | Livello di pre-allocazione |
| cluster_size | 512, 1k, 2k, ..., 2M | Dimensione cluster |
| compat | 0.10, 1.1 | Versione formato qcow2 |
| lazy_refcounts | on, off | Refcount update lazy (performance) |

### Conversioni per Diversi Target Storage

#### Verso directory locale (qcow2)

```bash
qemu-img convert -p -W -f vmdk -O qcow2 \
    /tmp/vm-disk.vmdk \
    /var/lib/vz/images/100/vm-100-disk-0.qcow2
```

#### Verso directory locale (raw)

```bash
qemu-img convert -p -W -f vmdk -O raw \
    /tmp/vm-disk.vmdk \
    /var/lib/vz/images/100/vm-100-disk-0.raw
```

#### Verso LVM-thin

```bash
# 1. Determinare la dimensione virtuale
qemu-img info /tmp/vm-disk.vmdk | grep "virtual size"
# virtual size: 100 GiB (107374182400 bytes)

# 2. Creare il logical volume thin
lvcreate -V 100G --thin -n vm-100-disk-0 pve/data

# 3. Convertire direttamente nel LV
qemu-img convert -p -W -f vmdk -O raw \
    /tmp/vm-disk.vmdk \
    /dev/pve/vm-100-disk-0
```

#### Verso ZFS zvol

```bash
# 1. Creare il zvol
zfs create -V 100G -s rpool/data/vm-100-disk-0
# -s = sparse/thin provisioned zvol

# 2. Convertire
qemu-img convert -p -W -f vmdk -O raw \
    /tmp/vm-disk.vmdk \
    /dev/zvol/rpool/data/vm-100-disk-0
```

#### Importazione diretta con qm

Proxmox fornisce il comando `qm` che semplifica il processo:

```bash
# Importa il disco e lo assegna alla VM 100
qm importdisk 100 /tmp/vm-disk.vmdk local-lvm --format raw

# Per qcow2 su storage directory
qm importdisk 100 /tmp/vm-disk.vmdk local --format qcow2
```

Dopo l'importazione, il disco appare come "unused" nella configurazione della VM e deve essere collegato manualmente:

```bash
# Verificare il disco importato
qm config 100 | grep unused
# unused0: local-lvm:vm-100-disk-0

# Collegare come disco SCSI
qm set 100 --scsi0 local-lvm:vm-100-disk-0
```

---

## Gestione dei File Sparse

### Cosa Sono i File Sparse

Un file sparse è un file il cui spazio logico è maggiore dello spazio fisico occupato su disco. I blocchi contenenti solo zeri non vengono allocati fisicamente:

```bash
# Creare un file sparse di 10GB che occupa quasi zero spazio
truncate -s 10G sparse-file.raw

# Verificare
ls -lh sparse-file.raw        # 10G (dimensione logica)
du -h sparse-file.raw          # 0   (dimensione fisica)
du --apparent-size -h sparse-file.raw  # 10G (dimensione apparente)
```

### Preservare la Sparseness durante la Conversione

Durante la conversione con `qemu-img convert`, i blocchi zero nel VMDK sorgente vengono automaticamente omessi nel file di destinazione, producendo un file sparse se il filesystem lo supporta:

```bash
# La conversione produce un file sparse per default
qemu-img convert -f vmdk -O raw source.vmdk dest.raw

# Verificare la sparseness
qemu-img info dest.raw
# disk size: 42.3 GiB    (spazio fisico)
# virtual size: 100 GiB   (spazio logico)
```

### Rischi con Copia e Trasferimento

Operazioni come `cp`, `scp` e `rsync` possono non preservare la sparseness:

```bash
# SBAGLIATO: cp senza --sparse espande il file
cp source.raw dest.raw  # Il file potrebbe espandersi a dimensione piena

# CORRETTO: preservare la sparseness
cp --sparse=always source.raw dest.raw

# CORRETTO: rsync con supporto sparse
rsync --sparse source.raw dest.raw

# CORRETTO: scp NON supporta sparse, usare dd con conv=sparse
dd if=source.raw of=dest.raw bs=4M conv=sparse status=progress
```

### TRIM e Discard Pre-Conversione

Per massimizzare la sparseness del disco convertito, eseguire TRIM/discard nella VM sorgente prima dello spegnimento:

```bash
# Linux guest
fstrim -av
# /: 45.2 GiB (48534388736 bytes) trimmed on /dev/sda1
# /var: 12.1 GiB (12994174976 bytes) trimmed on /dev/sda2

# Windows guest (PowerShell come Administrator)
Optimize-Volume -DriveLetter C -ReTrim -Verbose
Optimize-Volume -DriveLetter D -ReTrim -Verbose
```

Per guest che non supportano TRIM, azzerare lo spazio libero:

```bash
# Linux guest - azzerare lo spazio libero
dd if=/dev/zero of=/tmp/zero.fill bs=1M status=progress || true
rm -f /tmp/zero.fill
sync

# Windows guest - usare SDelete di Sysinternals
sdelete64.exe -z C:
```

---

## Ottimizzazione delle Performance di Conversione

### Pipeline Ottimale

La configurazione ottimale combina tutti i flag di performance:

```bash
qemu-img convert -p -W -m 16 -f vmdk -O qcow2 \
    -o preallocation=metadata,lazy_refcounts=on \
    source.vmdk dest.qcow2
```

### Impatto del Storage Sorgente e Destinazione

La velocità di conversione è determinata dal componente più lento nella catena:

```
Source Storage → [Read] → qemu-img → [Write] → Destination Storage
    ↑                                               ↑
 Bottleneck se HDD                          Bottleneck se HDD
 o storage di rete lento                    o storage di rete lento
```

Strategie per massimizzare il throughput:

1. **Storage locale per sorgente e destinazione**: copiare prima il VMDK su disco locale, poi convertire verso disco locale, infine spostare il risultato
2. **RAM disk per conversioni piccole**: per dischi fino a pochi GB, usare `/dev/shm` o tmpfs
3. **Separare i dispositivi I/O**: sorgente su un disco, destinazione su un altro

```bash
# Esempio: sorgente su SSD, destinazione su NVMe
# Copiare VMDK su SSD locale
rsync --sparse root@esxi:/vmfs/volumes/ds1/vm/disk.vmdk /ssd-temp/

# Convertire da SSD a NVMe
qemu-img convert -p -W -m 16 -f vmdk -O raw \
    /ssd-temp/disk.vmdk /nvme-storage/vm-100-disk-0.raw
```

### Conversioni in Batch

Per migrazioni con molte VM, automatizzare con uno script:

```bash
#!/bin/bash
# batch-convert.sh - Conversione batch VMDK -> qcow2

SOURCE_DIR="/mnt/vmware-export"
DEST_DIR="/var/lib/vz/images"
LOG_FILE="/var/log/vmdk-conversion.log"
PARALLEL_JOBS=2   # Conversioni simultanee

convert_disk() {
    local src="$1"
    local vmid="$2"
    local disk_num="$3"
    local dest="${DEST_DIR}/${vmid}/vm-${vmid}-disk-${disk_num}.qcow2"

    mkdir -p "${DEST_DIR}/${vmid}"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] START: ${src} -> ${dest}" >> "$LOG_FILE"

    time qemu-img convert -p -W -m 8 -f vmdk -O qcow2 \
        -o preallocation=metadata,lazy_refcounts=on \
        "$src" "$dest" 2>&1 | tee -a "$LOG_FILE"

    local rc=$?
    if [ $rc -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: ${dest}" >> "$LOG_FILE"
        # Verifica
        qemu-img check "$dest" >> "$LOG_FILE" 2>&1
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] FAILED: ${src} (rc=${rc})" >> "$LOG_FILE"
    fi
    return $rc
}

export -f convert_disk
export DEST_DIR LOG_FILE

# Elenco delle conversioni: sorgente vmid disk_num
cat <<'JOBS' | xargs -P $PARALLEL_JOBS -L 1 bash -c 'convert_disk "$@"' _
/mnt/vmware-export/web-server/web-server.vmdk 100 0
/mnt/vmware-export/db-server/db-server.vmdk 101 0
/mnt/vmware-export/db-server/db-server_1.vmdk 101 1
/mnt/vmware-export/app-server/app-server.vmdk 102 0
JOBS
```

---

## Stima dei Tempi di Conversione

### Fattori Determinanti

Il tempo di conversione dipende da:

1. **Dimensione effettiva dei dati** (non la dimensione virtuale per dischi thin)
2. **Velocità I/O dello storage sorgente** (read throughput)
3. **Velocità I/O dello storage destinazione** (write throughput)
4. **Formato di destinazione** (raw è più veloce, qcow2 con compressione più lento)
5. **CPU disponibile** (rilevante solo con compressione)

### Tabella di Stima

```
+---------------------+----------+-----------+-----------+
| Scenario            | 100 GB   | 500 GB    | 1 TB      |
|                     | (effett.)| (effett.) | (effett.) |
+---------------------+----------+-----------+-----------+
| HDD→HDD raw        | ~17 min  | ~83 min   | ~167 min  |
| HDD→HDD qcow2      | ~20 min  | ~100 min  | ~200 min  |
| SSD→SSD raw         | ~4 min   | ~19 min   | ~38 min   |
| SSD→SSD qcow2      | ~5 min   | ~24 min   | ~48 min   |
| NVMe→NVMe raw      | ~1.5 min | ~7 min    | ~15 min   |
| NVMe→NVMe qcow2    | ~2 min   | ~10 min   | ~20 min   |
| 10GbE NFS→local SSD| ~8 min   | ~42 min   | ~83 min   |
| qcow2 compresso    | +30-80%  | +30-80%   | +30-80%   |
+---------------------+----------+-----------+-----------+

Basi di calcolo:
- HDD sequenziale: ~100 MB/s
- SSD SATA: ~450 MB/s
- NVMe: ~1200 MB/s (conservativo)
- 10GbE: ~1000 MB/s teorico, ~800 MB/s reale
- qcow2 overhead: ~20% rispetto a raw
- Compressione: +30-80% tempo aggiuntivo
```

### Formula Approssimativa

```
Tempo (secondi) = Dati_effettivi (GB) / min(Read_MB/s, Write_MB/s) * 1024 * overhead_formato

Dove overhead_formato:
  raw    = 1.0
  qcow2  = 1.2
  qcow2 -c = 1.6 - 2.0
```

---

## Verifica Post-Conversione

### qemu-img info

Verifica i metadati del disco convertito:

```bash
qemu-img info dest.qcow2
# image: dest.qcow2
# file format: qcow2
# virtual size: 100 GiB (107374182400 bytes)
# disk size: 42.3 GiB
# cluster_size: 65536
# Format specific information:
#     compat: 1.1
#     compression type: zlib
#     lazy refcounts: true
#     refcount bits: 16
#     corrupt: false
```

Verificare che:
- `virtual size` corrisponda al disco originale
- `file format` sia quello atteso
- `corrupt: false`

### qemu-img check

Esegue una verifica di integrità strutturale (solo per qcow2):

```bash
qemu-img check dest.qcow2
# No errors were found on the image.
# 684032/1638400 = 41.75% allocated, 0.00% fragmented, 0.00% compressed clusters
# Image end offset: 44836225024

# Con riparazione (se necessario)
qemu-img check -r all dest.qcow2
```

### Verifica del Checksum dei Dati

Per una verifica completa che i dati siano identici:

```bash
# Calcolare checksum del contenuto raw sorgente
qemu-img convert -f vmdk -O raw source.vmdk /dev/stdout | md5sum
# a1b2c3d4e5f6...  -

# Calcolare checksum del contenuto raw destinazione
qemu-img convert -f qcow2 -O raw dest.qcow2 /dev/stdout | md5sum
# a1b2c3d4e5f6...  -

# I due hash DEVONO essere identici
```

### Verifica di Boot

Il test finale e più significativo è l'avvio della VM:

```bash
# Creare una VM di test in Proxmox
qm create 999 --name test-conversion --memory 2048 --cores 2 \
    --scsi0 local:100/vm-100-disk-0.qcow2 \
    --boot order=scsi0 --ostype l26

# Avviare e verificare
qm start 999
# Monitorare la console via VNC/SPICE o serial console
```

---

## Implicazioni Thick-to-Thin

### Cosa Cambia

Quando si converte un disco VMware thick provisioned in un formato thin (qcow2 senza preallocation=full, LVM-thin, ZFS sparse zvol), il comportamento di allocazione cambia fondamentalmente:

```
VMware Thick Eager Zeroed:
[Blocco1][Blocco2][Blocco3][Blocco4][Blocco5]  ← Tutto pre-allocato
  Dati    Dati    Zeri     Zeri     Dati

Dopo conversione a qcow2 thin:
[Blocco1][Blocco2]                  [Blocco5]  ← Solo blocchi con dati
  Dati    Dati                       Dati
           └── Blocchi zero non allocati
```

### Rischi del Thin Provisioning

1. **Over-commitment**: la somma delle dimensioni virtuali può superare lo spazio fisico
2. **Crescita improvvisa**: un workload che scrive massivamente può esaurire lo storage
3. **Frammentazione**: la crescita dinamica causa frammentazione su storage basato su file

### Monitoraggio Obbligatorio

Configurare alert per l'utilizzo dello storage:

```bash
# Alert quando il thin pool LVM supera l'80%
cat >> /etc/cron.d/thinpool-monitor << 'EOF'
*/5 * * * * root lvs --noheadings -o data_percent pve/data | awk '{if ($1+0 > 80) system("echo \"ALERT: Thin pool at " $1 "%\" | mail -s \"Storage Alert\" admin@example.com")}'
EOF

# Alert per ZFS
zpool list -H -o cap rpool | tr -d '%' | awk '{if ($1+0 > 80) print "ALERT: ZFS pool at "$1"%"}'
```

---

## Best Practices

- Consolidare **sempre** gli snapshot VMware prima della conversione; non convertire mai dischi con snapshot attivi poiché il risultato sarà incompleto.
- Eseguire `fstrim` o azzeramento dello spazio libero nella VM sorgente prima dello spegnimento per massimizzare l'efficienza del thin provisioning nel disco convertito.
- Utilizzare sempre i flag `-p -W` in `qemu-img convert` per avere progresso visibile e scritture parallele; aggiungere `-m 16` su storage veloci.
- Specificare sempre `-f vmdk` esplicitamente; non affidarsi al rilevamento automatico del formato che potrebbe fallire con file parzialmente corrotti.
- Preferire il formato raw su LVM-thin o ZFS dove lo storage backend fornisce già snapshot, thin provisioning e compressione; qcow2 è preferibile solo su storage directory o NFS.
- Non utilizzare la compressione qcow2 (`-c`) per dischi di VM in produzione attiva; preferire la compressione a livello di storage (ZFS lz4).
- Verificare ogni conversione con `qemu-img check` (per qcow2) e confronto checksum prima di eliminare i file sorgente.
- Mantenere i VMDK originali fino al completamento della verifica di boot sulla VM migrata e conferma del corretto funzionamento applicativo.
- Per conversioni batch, limitare il parallelismo a 2-3 conversioni simultanee per evitare saturazione I/O dello storage.
- Documentare dimensione sorgente, dimensione convertita, tempo impiegato e checksum per ogni disco convertito in un registro di migrazione.
- Monitorare attivamente l'utilizzo dello storage thin-provisioned dopo la migrazione per prevenire condizioni di spazio esaurito.
- Utilizzare `qm importdisk` quando possibile poiché gestisce automaticamente il naming e la registrazione del disco nella configurazione della VM.

---

## Troubleshooting

### Problema: qemu-img fallisce con "Could not open VMDK: Invalid extent lines"
**Sintomi**: la conversione termina immediatamente con errore relativo alle extent lines nel file descrittore VMDK.
**Causa**: il file descrittore `.vmdk` contiene riferimenti a extent files con percorsi non validi, tipicamente quando i file sono stati spostati da un datastore VMware senza aggiornare il descrittore. Può anche verificarsi con VMDK creati da versioni molto vecchie di VMware.
**Soluzione**: aprire il file descrittore `.vmdk` con un editor di testo e correggere i percorsi degli extent. I percorsi possono essere relativi (solo nome file) o assoluti:
```bash
# Visualizzare il descrittore
cat vm-disk.vmdk
# Cercare la linea: RW 209715200 VMFS "vm-disk-flat.vmdk"
# Verificare che il file referenziato esista nello stesso percorso
ls -la vm-disk-flat.vmdk
# Se il nome non corrisponde, editare il descrittore
```
**Prevenzione**: copiare sempre tutti i file relativi a un disco VMDK nella stessa directory. Per monolithicFlat, servono il file descrittore e il file `-flat.vmdk`. Per dischi con extent multipli, servono tutti i file extent.

### Problema: conversione lentissima, velocità sotto i 10 MB/s
**Sintomi**: la conversione procede ma a una velocità molto inferiore a quella attesa dallo storage hardware.
**Causa**: molteplici possibili cause. Le più comuni: (1) il flag `-W` non è stato specificato, causando scritture sequenziali; (2) lo storage di rete (NFS/iSCSI) ha latenza elevata; (3) il disco sorgente ha frammentazione estrema causata da snapshot VMware non consolidati; (4) I/O scheduler inappropriato.
**Soluzione**: aggiungere i flag `-W -m 16`. Se il sorgente è su rete, copiare prima localmente. Verificare con `iostat -x 1` che il dispositivo non sia a collo di bottiglia per `await` elevato:
```bash
iostat -x 1 5
# Se await > 20ms su SSD, investigare il controller/driver
# Se %util > 95%, il dispositivo è saturo

# Verificare l'I/O scheduler
cat /sys/block/sda/queue/scheduler
# Cambiare a none/noop per SSD/NVMe
echo none > /sys/block/sda/queue/scheduler
```
**Prevenzione**: testare la velocità di I/O sequenziale prima di iniziare le conversioni con `dd if=/dev/zero of=/tmp/test bs=1M count=1024 oflag=direct`.

### Problema: il disco convertito ha dimensione zero o molto piccola
**Sintomi**: dopo la conversione, il file di destinazione esiste ma ha dimensione di pochi KB o zero byte.
**Causa**: il file sorgente VMDK era il solo descrittore senza il file dati associato. Per i formati vmfsFlat e monolithicFlat, il file `.vmdk` è solo un descrittore di pochi KB; i dati reali sono nel file `-flat.vmdk`.
**Soluzione**: verificare con `qemu-img info` il file sorgente. Se riporta una virtual size di zero o dimensioni non coerenti, individuare il file dati corretto:
```bash
qemu-img info source.vmdk
# Se virtual size è 0 o disk size è pochi KB:
# Cercare il file -flat.vmdk associato
ls -la *flat.vmdk *-delta.vmdk
```
**Prevenzione**: utilizzare sempre `qemu-img info` sul file sorgente prima di iniziare la conversione per verificare che le dimensioni siano coerenti.

### Problema: "No space left on device" durante la conversione
**Sintomi**: la conversione fallisce a metà con errore ENOSPC.
**Causa**: lo spazio disponibile sulla destinazione è insufficiente. Per conversioni verso raw, serve spazio pari alla dimensione virtuale del disco. Per qcow2 senza preallocation, serve spazio pari alla dimensione effettiva dei dati più overhead metadati.
**Soluzione**: verificare lo spazio disponibile prima di iniziare:
```bash
# Spazio richiesto
qemu-img info source.vmdk | grep -E "virtual size|disk size"

# Spazio disponibile
df -h /var/lib/vz/images/
# oppure
lvs -o+lv_size,data_percent pve/data
```
**Prevenzione**: calcolare lo spazio necessario prima della conversione. Per raw, riservare il 100% della dimensione virtuale. Per qcow2, riservare almeno il 110% della dimensione dati effettiva.

### Problema: la VM non si avvia dopo la conversione, errore "no bootable device"
**Sintomi**: il disco è stato convertito con successo e la verifica con `qemu-img check` non rileva errori, ma la VM non esegue il boot.
**Causa**: non si tratta di un errore di conversione ma di configurazione della VM. Le cause più comuni: (1) il firmware è impostato su BIOS ma il disco originale usa GPT/UEFI, o viceversa; (2) il controller disco è diverso (IDE vs SCSI vs VirtIO); (3) il disco è stato collegato alla porta sbagliata (es. scsi1 invece di scsi0).
**Soluzione**: verificare la configurazione del boot:
```bash
# Controllare se il disco originale è GPT o MBR
qemu-img convert -f qcow2 -O raw dest.qcow2 /dev/stdout | fdisk -l /dev/stdin
# Se GPT → usare OVMF/UEFI firmware
# Se MBR → usare SeaBIOS

# Configurare correttamente la VM
qm set 100 --bios ovmf --efidisk0 local-lvm:1,format=raw  # Per UEFI
# oppure
qm set 100 --bios seabios  # Per BIOS/MBR
```
**Prevenzione**: documentare il tipo di firmware (BIOS/UEFI) e il tipo di controller disco di ogni VM prima della migrazione.

### Problema: corruzione dati dopo conversione, filesystem non montabile
**Sintomi**: la VM si avvia ma il filesystem riporta errori, oppure `fsck` trova corruzione.
**Causa**: la VM sorgente non era spenta correttamente al momento della copia del VMDK. Se la VM era in esecuzione o in stato suspended, il contenuto del disco potrebbe essere inconsistente. In alternativa, la catena di snapshot non è stata consolidata correttamente.
**Soluzione**: se possibile, tornare alla sorgente, spegnere la VM pulitamente, consolidare gli snapshot, e ripetere la conversione. Se il VMDK originale non è più disponibile, tentare la riparazione:
```bash
# Montare il disco con qemu-nbd
modprobe nbd max_part=16
qemu-nbd -c /dev/nbd0 /var/lib/vz/images/100/vm-100-disk-0.qcow2

# Eseguire fsck
fsck -y /dev/nbd0p1

# Disconnettere
qemu-nbd -d /dev/nbd0
```
**Prevenzione**: spegnere sempre la VM con shutdown pulito (non power off). Verificare che non esistano snapshot attivi prima della copia. Usare il confronto checksum per validare la conversione.

### Problema: performance I/O degradate dopo la conversione
**Sintomi**: la VM migrata presenta latenza I/O significativamente superiore e IOPS inferiori rispetto all'ambiente VMware.
**Causa**: molteplici fattori possibili. I più comuni: (1) il cache mode del disco è impostato su `none` (sicuro ma lento) invece di `writeback`; (2) il driver disco nella VM non è VirtIO ma emula IDE/AHCI; (3) il formato qcow2 ha frammentazione elevata; (4) il controller SCSI non è VirtIO SCSI.
**Soluzione**: ottimizzare la configurazione della VM:
```bash
# Cambiare cache mode
qm set 100 --scsi0 local-lvm:vm-100-disk-0,cache=writeback

# Verificare il driver SCSI
qm config 100 | grep scsihw
# Impostare VirtIO SCSI
qm set 100 --scsihw virtio-scsi-single --scsi0 local-lvm:vm-100-disk-0,iothread=1

# Per qcow2 frammentato, defragmentare
qemu-img convert -p -W -f qcow2 -O qcow2 \
    -o preallocation=metadata old.qcow2 new.qcow2
mv new.qcow2 old.qcow2
```
**Prevenzione**: utilizzare VirtIO driver nella VM sorgente prima della migrazione. Scegliere il formato disco e cache mode appropriato in base al workload.

---

## Riferimenti

- [QEMU Documentation — qemu-img](https://www.qemu.org/docs/master/tools/qemu-img.html)
- [Proxmox VE Administration Guide — Storage](https://pve.proxmox.com/pve-docs/chapter-pvesm.html)
- [VMware VMDK Specification (Virtual Disk Format 5.0)](https://www.vmware.com/app/vmdk/?src=vmdk)
- [qcow2 Format Specification](https://github.com/qemu/qemu/blob/master/docs/interop/qcow2.txt)
- [Proxmox Wiki — Migration of servers to Proxmox VE](https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE)
- [Proxmox Wiki — qm importdisk](https://pve.proxmox.com/pve-docs/qm.1.html)
- [Linux Kernel — Sparse Files](https://www.kernel.org/doc/html/latest/filesystems/fiemap.html)
- [VMware KB — Consolidating snapshots](https://knowledge.broadcom.com/external/article?legacyId=1023145)
- [QEMU Block Layer Documentation](https://www.qemu.org/docs/master/system/qemu-block-drivers.html)

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — `qemu-img convert -W` e backend SSD vs HDD.** Su NVMe Gen4/5, `qemu-img convert -W -m 8` puo saturare la banda dello storage in scrittura (~5-7 GB/s su Gen4). Su SATA SSD e ~500 MB/s. Su HDD spinning, `-W` non aiuta (i dischi rotanti sono seek-bound, multi-thread aumenta seek): preferire `-W` solo se source e target sono entrambi flash. Verifica throughput reale: `iostat -xdz 5` durante la conversione.

> **Errore comune — Conversione che riempie il filesystem temporaneo `/tmp`.** Conversione di un VMDK 2 TB su un host con `/tmp` su filesystem da 50 GB → conversione fallisce a meta. Soluzione: usare `-T none` per disabilitare temp file, oppure scrivere direttamente sul target storage (`qemu-img convert -O qcow2 disk.vmdk /var/lib/vz/images/100/vm-100-disk-0.qcow2`), oppure montare un disco dedicato grande in `/tmp` solo per la conversione.

> **Caso reale — Disk corruption sottile dopo conversione.** Dopo conversione VMDK → qcow2 + import in Proxmox, una VM PostgreSQL ha mostrato corrutezza casuale dopo qualche giorno. Causa: il VMDK source aveva blocchi non azzerati nelle aree "thin" (residui di dati di una VM precedente). qemu-img ha copiato anche quelli, e PostgreSQL ha usato quelle aree come pagine "vergini" — quindi blocchi con dati casuali. Soluzione preventiva: dopo la conversione, montare il filesystem nel guest e fare `fstrim -v /` o (per Linux ext4 con discard) montare con `-o discard` per zero-fill durante uso. Per produzione critica, considerare `qemu-img convert ... && qemu-img amend -o lazy_refcounts=on,extended_l2=on,...` per ottimizzare la struttura qcow2.

---

## Esercizi

1. **Concettuale — quale formato target?** Per ognuno: (a) DB OLTP ad alta intensita scrittura random; (b) web server stateless con disco 50 GB; (c) file server con 4 TB di dati statici; (d) lab di sviluppo con snapshot frequenti. *Risposte:* (a) raw su LVM-Thin (snapshot opzionali a livello LVM, no doppia indirezione qcow2); (b) qcow2 (snapshot facili); (c) raw su ZFS (snapshot + compression); (d) qcow2 (snapshot interni, comodo per snapshot tree).

2. **Lab — conversione + import + fstrim.** Esportare un VMDK 50 GB da una VM Linux di test su VMware. Convertire con `qemu-img convert -p -W -m 4 -O qcow2 disk.vmdk disk.qcow2`. Misurare il tempo. Importare con `qm importdisk` su LVM-Thin Proxmox. Bootare la VM. Eseguire `fstrim -v /` nel guest. Misurare lo spazio occupato in `lvs` prima e dopo trim.

3. **Scenario — VMDK split 2 GB senza descriptor.** Hai un disco VMDK split (10 file `.vmdk-s001.vmdk` ... `s010.vmdk`) ma il descriptor `.vmdk` e corrotto/perso. Argomenta in 8 righe come ricostruire la conversione: (a) `cat *.vmdk-s*.vmdk > combined.raw`; (b) `qemu-img convert -f raw -O qcow2 combined.raw output.qcow2`; (c) verificare con `qemu-img info` la virtual size; (d) bootare in modalita rescue e verificare partition table.

4. **Stretch — script di conversione idempotente con resume.** Scrivere uno script che, dato un input VMDK e un output path, esegue conversione interrompibile e ripristinabile: (a) scrive un file `.in-progress` con metadata; (b) se il file esiste e l'output e parziale, fa `qemu-img check` e decide se riprendere o ricominciare; (c) usa `nice -n 19 ionice -c 3` per non saturare lo storage del nodo.

## Auto-valutazione

1. Differenza fra qcow2 e raw — vantaggi e svantaggi di ciascuno?
2. `-O qcow2 -o preallocation=metadata`: cosa cambia rispetto al default?
3. Cosa fa `-W -m 8` in `qemu-img convert` e quando aiuta?
4. Comando per controllare l'integrita di un file qcow2?
5. Differenza fra fstrim nel guest e `qemu-img convert -S 4k` lato host?
6. Cosa succede se il source VMDK ha snapshot non consolidati e si fa convert?
7. Come si converte un VMDK split senza descriptor?
8. Quale strumento — qemu-img o virt-v2v — preferire per migrazione e perche?

## Letture primarie consigliate

- [`QEMU-IMG`] qemu-img(1) man page. https://www.qemu.org/docs/master/tools/qemu-img.html
- QEMU Block Drivers documentation. https://www.qemu.org/docs/master/system/qemu-block-drivers.html
- QEMU qcow2 format specification (sources). https://gitlab.com/qemu-project/qemu/-/blob/master/docs/interop/qcow2.txt
- VMware Virtual Disk Format (VMDK) specification (Broadcom). https://kb.vmware.com/s/article/1018434 (verificare URL aggiornato post-Broadcom)
- KB Broadcom — Consolidating snapshots before migration. https://knowledge.broadcom.com/external/article?legacyId=1023145
- Linux Kernel — Sparse Files (fiemap). https://www.kernel.org/doc/html/latest/filesystems/fiemap.html
- [`PVE-STORAGE`] Proxmox VE Wiki — Storage. https://pve.proxmox.com/wiki/Storage

## Collegamenti incrociati

- Modulo 03.1 — `../03-STORAGE-AVANZATO-PROXMOX/lvm-e-lvm-thin-proxmox.md`: backend LVM-Thin per import.
- Modulo 06.2 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/migrazione-con-virt-v2v.md`: virt-v2v come alternativa orchestrata a qemu-img diretto.
- Modulo 08.2 — `shared-storage-cutover-nfs-iscsi.md`: cutover NFS/iSCSI shared.
- Modulo 08.3 — `strategie-migrazione-datastore.md`: strategie globali datastore.
- Modulo 08.4 — `validazione-performance-storage.md`: validazione performance post-import.
- Modulo 09.4 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-windows-server-vm.md`: applicazione concreta.

## Glossario locale

| Termine | Definizione |
|---|---|
| **VMDK** | Virtual Machine Disk format (VMware). Ha descriptor + dati. |
| **`-flat.vmdk`** | File binario monolitico contenente i dati (senza header). |
| **VMDK split** | Variante che spezza il flat in chunk di 2 GB (compatibilita FAT32). |
| **qcow2** | QEMU Copy-On-Write v2. Snapshot interni, thin provisioning, compressione. |
| **raw** | Formato disco puro, byte-per-byte uguale al disco virtuale. Massima performance. |
| **Sparse file** | File con "hole" — regioni di byte zero non scritti su disco. Recuperate al filesystem level. |
| **fiemap** | Linux ioctl per leggere la mappa fisica dei blocchi (sparse vs allocato). |
| **`qemu-img info`** | Comando per leggere metadata di un disco virtuale. |
| **`qemu-img check`** | Verifica integrita strutturale (refcount table, cluster, snapshot chain). |
| **`qemu-img convert`** | Conversione disco; lato copia + traduzione formato. |
| **`-p`** | Progress on stdout. |
| **`-W`** | Out-of-order writes (parallel). Richiede `-m N`. |
| **`-m N`** | N coroutines parallele (default 8 su qemu-img recenti). |
| **`-S K`** | Sparse hole detection ogni K byte (default 4096, allineato block size). |
| **`-c`** | Compressione (solo qcow2). |
| **`-o preallocation=...`** | Modalita di preallocation: `off` (default), `metadata`, `falloc`, `full`. |
| **`-t cache`** | Cache mode in scrittura: `writeback`, `writethrough`, `none` (O_DIRECT). |
| **fstrim** | Comando Linux per inviare TRIM/UNMAP al backend storage, recuperando blocchi non usati. |
| **TRIM/UNMAP** | Comando SCSI/ATA che marca blocchi come liberi (per SSD wear leveling e thin storage reclaim). |
| **Thick eager-zeroed** | VMDK pre-allocato e azzerato. Massima performance, no oversubscription. |
| **Thick lazy-zeroed** | VMDK pre-allocato ma azzerato on-write. |
| **Thin** | VMDK che cresce on-demand, sparse. |
