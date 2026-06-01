# Live Migration Interna al Cluster Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 4 — Cluster HA post-migrazione · Modulo 10.2 (segue 10.1 HA Manager, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 10.1 (HA Manager, CRM/LRM); modulo 02 (architettura cluster, pmxcfs, corosync); modulo 03 (storage condiviso vs locale, ZFS replication); modulo 04 (rete: VLAN dedicate, jumbo frames, bonding); concetti generali di live migration (memory pre-copy, dirty page tracking, downtime).
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. spiegare l'algoritmo **memory pre-copy** di QEMU live migration: setup → memory pre-copy iterativo (RAM target sempre piu allineata alla source) → stop-and-copy (downtime breve, copia delta + state CPU/device) → resume sul target;
> 2. configurare la **rete di migrazione**: rete dedicata (`migration_network` in `/etc/pve/datacenter.cfg`), MTU 9000 con jumbo frames validati, bonding LACP per ridondanza, criteria SSH come trust;
> 3. eseguire migrazioni con `qm migrate <VMID> <target>` (offline) e `qm migrate <VMID> <target> --online` (live), con flag avanzati (`--with-local-disks`, `--targetstorage`, `--bwlimit`);
> 4. controllare la **bandwidth** della migrazione: `migration_max_bandwidth` globale o `--bwlimit` per-migrazione (in KB/s); calcolo: VM 32 GB RAM con 100 MB/s rete = ~330s teorici (~5 min) per la pre-copy iniziale;
> 5. interpretare la metrica **dirty page rate**: pagine RAM modificate al secondo dal workload; se dirty rate > bandwidth disponibile, la migrazione *non converge* (pre-copy infinita) → richiede `--with-local-disks` con saturazione, oppure stop-and-copy diretto, oppure aumento bandwidth;
> 6. gestire la **convergenza forzata**: parametri `migration_downtime` (downtime massimo accettabile, default 100ms) e `migration_converge` (auto-convergence, throttling del guest per ridurre dirty rate); trade-off: downtime piu alto = converge piu facile, ma piu visibile all'utente;
> 7. eseguire **live migration con storage locale** (Storage Migration): `--with-local-disks`, copia parallela del disco + memoria; tempo dominato dal disco; richiede storage target sufficiente; rischio di out-of-space → fail in mid-migration;
> 8. configurare `secure migration network` (encryption tramite SSH tunnel automatico per traffico migration via rete pubblica); trade-off CPU vs sicurezza; alternative: rete dedicata privata con encryption disabilitabile per perf max (`migration_type=insecure` su LAN trusted);
> 9. risolvere problemi comuni: CPU model mismatch (`--cpu host` impedisce live migration cross-CPU; usare baseline `kvm64` o `x86-64-v2/v3` per portabilita), mancanza di storage condiviso, timeout ssh.
> **Tempo stimato:** lettura 60-90 min · lab 240-360 min (cluster 3 nodi, vari scenari di migrazione)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; QEMU 7.x → 10.x; pve-ha-manager 4.x; corosync 3.1.x.

## Mappa concettuale

```
+============================================================+
|     QEMU Live Migration — pre-copy + convergence           |
+============================================================+
|                                                            |
|   FASE 1: SETUP (~1-3s)                                    |
|   - SSH dal source al target                               |
|   - Avvio QEMU target in stato "incoming"                  |
|   - Apertura connessione di migration                      |
|                                                            |
|   FASE 2: PRE-COPY ITERATIVA (durata variabile)            |
|   - Iter 0: copia tutta la RAM (es. 32 GB)                 |
|   - Mark dirty bit per pagine modificate durante iter 0    |
|   - Iter 1: copia solo pagine dirty di iter 0              |
|   - Iter 2: copia solo pagine dirty di iter 1              |
|   - ... finche dirty pages residue convergono              |
|                                                            |
|   Convergenza:                                             |
|   - dirty_rate < bandwidth → converge naturale             |
|   - dirty_rate > bandwidth → NON converge → action:        |
|     a) aumentare bandwidth                                 |
|     b) auto-convergence (throttle CPU guest)               |
|     c) tollerare downtime piu alto                         |
|     d) migrate cold (offline)                              |
|                                                            |
|   FASE 3: STOP-AND-COPY (downtime, ~50-500ms target)       |
|   - Pausa il guest sul source                              |
|   - Copia ultimi dirty + state CPU/device                  |
|   - Invio segnale "ready" al target                        |
|                                                            |
|   FASE 4: RESUME (~50-200ms)                               |
|   - Target avvia il guest                                  |
|   - Source spegne il guest                                 |
|   - Ack al CRM, pmxcfs aggiorna placement                  |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   FATTORI CRITICI                                          |
|                                                            |
|   bandwidth      banda effettiva rete migration            |
|   dirty_rate     pagine modificate/s dal workload          |
|   ram_size       totale RAM VM da copiare                  |
|   downtime_max   soglia per stop-and-copy (default 100ms)  |
|                                                            |
|   Tempo totale tipico (rete 10 GbE, VM idle):              |
|     ~1.25 GB/s effettivi → 32 GB in ~25s + setup + final   |
|                                                            |
|   Tempo totale (rete 1 GbE, VM idle):                      |
|     ~125 MB/s → 32 GB in ~270s (~4.5 min)                  |
|                                                            |
|   Tempo (rete 10 GbE, VM con dirty_rate=500 MB/s):         |
|     pre-copy ~25s + iter additional ~varia + final ~150ms  |
|     totale ~30-60s                                         |
|                                                            |
|   Tempo (rete 10 GbE, VM con dirty_rate=2 GB/s):           |
|     dirty_rate > bandwidth → no convergence                |
|     servira auto-convergence (throttling) o downtime piu   |
|     alto                                                   |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   COMANDI ESSENZIALI                                       |
|                                                            |
|   qm migrate 100 pve2 --online       live migration        |
|   qm migrate 100 pve2 --online --with-local-disks          |
|     storage-migrazione completa                            |
|   qm migrate 100 pve2 --bwlimit 100000  100 MB/s cap       |
|   qm migrate 100 pve2 --targetstorage local-lvm:zfspool    |
|     mapping storage source->target                         |
|                                                            |
|   /etc/pve/datacenter.cfg:                                 |
|   migration: type=secure,network=10.0.10.0/24              |
|   bwlimit: migration=200000                                |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Live migration *non e magia*: e copia di RAM su rete in modo intelligente.** Conoscere il calcolo `RAM size / bandwidth = tempo minimo` permette di stimare se la migrazione completera nei limiti accettabili. Una VM da 256 GB su rete 1 GbE: 256 GB / 125 MB/s = ~2050s ≈ 34 min — non e un problema, e fisica.
2. **Dirty page rate decide tra "facile" e "impossibile".** Un DB OLTP con 5K TPS e ~500 MB/s di dirty page rate. Su rete 10 GbE (~1.25 GB/s) la migrazione converge ma ci mette piu tempo. Su rete 1 GbE (125 MB/s < 500 MB/s dirty) NON converge mai senza throttling.
3. **`--cpu host` e nemico della live migration cross-CPU.** Su cluster con CPU eterogenei (es. Intel Xeon Gen 9 + Gen 11), una VM creata con `host` non puo migrare se le feature CPU mismatch. Per cluster mixed: usare `kvm64` (lowest common) o `x86-64-v2/v3` (baseline standard). Per cluster omogenei: `host` per perf max, accettando la limitazione.
4. **Storage condiviso semplifica tutto.** Live migration con shared storage (Ceph, NFS, iSCSI shared LVM) copia solo RAM. Live migration con local storage (`--with-local-disks`) copia RAM + disco — molto piu lento e rischioso. Dove possibile, design del cluster con shared storage.
5. **`migration_type=insecure` e accettabile su rete dedicata privata.** Lo SSH tunnel cifrato aggiunge ~10-20% di CPU overhead e puo limitare la bandwidth. Se la rete di migrazione e una VLAN dedicata isolata, disabilitare encryption e legittimo. Mai su rete pubblica o condivisa.
6. **Convergenza forzata ha un costo invisibile.** L'auto-convergence di QEMU mette throttling sul guest (rallenta la CPU della VM) per ridurre il dirty rate. Risultato: la VM converge, ma per gli ultimi secondi il workload e degradato. Per servizi latency-sensitive (DB OLTP, real-time control), preferire downtime piu alto o cold migration.
7. **Validare la rete di migration prima di farne dipendere la produzione.** `iperf3` end-to-end, `ping -M do -s 8972` per jumbo frames, test di migrazione su VM throwaway. La performance reale di una rete "10 GbE" puo essere 5 GbE per cattivo cabling, MTU mismatch, o switch firmware buggy.

---

## Introduzione

La live migration (migrazione a caldo) permette di spostare una macchina virtuale in esecuzione da un nodo fisico a un altro senza interruzione del servizio. In Proxmox VE, questa funzionalita e equivalente a VMware vMotion ed e un componente essenziale per la manutenzione del cluster, il bilanciamento del carico e la continuita operativa.

Questo documento copre tutti gli aspetti della live migration in Proxmox VE: dalla configurazione della rete di migrazione alle opzioni avanzate, dalla stima del downtime alla risoluzione dei problemi, includendo script per migrazioni di massa e il confronto dettagliato con VMware vMotion.

---

## Architettura della Live Migration

### Come Funziona la Live Migration

```
+------------------------------------------------------------------+
|              FASI DELLA LIVE MIGRATION                           |
+------------------------------------------------------------------+
|                                                                  |
|  FASE 1: Pre-copy (trasferimento memoria)                       |
|  +-------------------+          +-------------------+            |
|  | Nodo Sorgente     |          | Nodo Destinazione |            |
|  | VM 100 (running)  | -------> | VM 100 (memoria)  |            |
|  | RAM: 8 GB         | copia    | RAM: riceve dati  |            |
|  +-------------------+ iniziale +-------------------+            |
|                                                                  |
|  FASE 2: Iterative copy (pagine sporche)                        |
|  +-------------------+          +-------------------+            |
|  | Nodo Sorgente     |          | Nodo Destinazione |            |
|  | VM 100 (running)  | -------> | VM 100 (memoria)  |            |
|  | Dirty pages       | re-copy  | Aggiorna pagine   |            |
|  +-------------------+          +-------------------+            |
|  (ripetuta fino a convergenza delle dirty pages)                |
|                                                                  |
|  FASE 3: Stop-and-copy (downtime minimo)                        |
|  +-------------------+          +-------------------+            |
|  | Nodo Sorgente     |          | Nodo Destinazione |            |
|  | VM 100 (PAUSED)   | -------> | VM 100 (ultime    |            |
|  | Stop scritture    | ultime   | pagine + stato    |            |
|  |                   | pagine   | CPU)              |            |
|  +-------------------+          +-------------------+            |
|                                                                  |
|  FASE 4: Attivazione sul nodo destinazione                      |
|  +-------------------+          +-------------------+            |
|  | Nodo Sorgente     |          | Nodo Destinazione |            |
|  | VM 100 (stopped)  |          | VM 100 (RUNNING!) |            |
|  | Risorse liberate  |          | Operativa         |            |
|  +-------------------+          +-------------------+            |
|                                                                  |
+------------------------------------------------------------------+
```

### Requisiti per la Live Migration

| Requisito | Dettaglio |
|-----------|-----------|
| CPU compatibile | Stessa famiglia CPU o tipo CPU configurato nella VM |
| Storage accessibile | Storage condiviso o replicazione attiva |
| Rete di migrazione | Connettivita tra i nodi (dedicata raccomandata) |
| RAM sufficiente | Il nodo destinazione deve avere RAM libera sufficiente |
| Quorum | Il cluster deve avere quorum |
| Firewall | Porte 60000-60050 TCP aperte tra i nodi |

---

## Configurazione della Rete di Migrazione

### Impostazione in datacenter.cfg

La rete di migrazione si configura nel file `/etc/pve/datacenter.cfg`:

```bash
# Visualizzare la configurazione corrente
cat /etc/pve/datacenter.cfg

# Aggiungere/modificare la configurazione della migrazione
# Formato: migration: <tipo>,network=<CIDR>[,bandwidth=<limit>]

# Configurazione raccomandata per produzione:
cat >> /etc/pve/datacenter.cfg << 'EOF'
migration: secure,network=10.10.40.0/24
EOF

# Opzioni disponibili:
# migration: secure         - Migrazione crittografata via SSH tunnel (default)
# migration: insecure       - Migrazione senza crittografia (piu veloce)
#   network=10.10.40.0/24   - Rete dedicata per il traffico di migrazione
#   bandwidth=0              - Nessun limite di banda (0 = illimitato)
#   bandwidth=500            - Limite a 500 MiB/s
```

### Tipi di Migrazione: Secure vs Insecure

```
+------------------------------------------------------------------+
| SECURE (default)                                                 |
+------------------------------------------------------------------+
| - Traffico crittografato via SSH tunnel                          |
| - Piu lenta a causa dell'overhead crittografico                  |
| - Sicura anche su reti non fidate                                |
| - CPU usage: significativo per la crittografia                   |
| - Banda effettiva: ~50-70% della banda disponibile              |
|                                                                  |
| Raccomandata quando:                                             |
| - La rete di migrazione e condivisa con altro traffico           |
| - Requisiti di sicurezza stringenti                              |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
| INSECURE                                                         |
+------------------------------------------------------------------+
| - Traffico in chiaro (QEMU direct)                               |
| - Molto piu veloce (nessun overhead crittografico)               |
| - Sicura SOLO su rete dedicata e isolata                         |
| - CPU usage: minimo                                              |
| - Banda effettiva: ~90-95% della banda disponibile              |
|                                                                  |
| Raccomandata quando:                                             |
| - La rete di migrazione e dedicata e fisicamente isolata         |
| - Performance di migrazione e critica                            |
| - Si migrano molte VM contemporaneamente                        |
+------------------------------------------------------------------+
```

### Configurazione di Rete su Ogni Nodo

```bash
# Esempio di configurazione /etc/network/interfaces per la rete di migrazione

# Bond ad alta velocita per migrazione
auto bond2
iface bond2 inet manual
    bond-slaves enp130s0f0 enp130s0f1
    bond-miimon 100
    bond-mode 802.3ad
    bond-xmit-hash-policy layer3+4

# VLAN di migrazione sul bond
auto bond2.40
iface bond2.40 inet static
    address 10.10.40.11/24    # .11 per nodo1, .12 per nodo2, etc.
    mtu 9000                   # Jumbo frame per performance

# Verificare la connettivita della rete di migrazione
ping -c 5 -M do -s 8972 10.10.40.12
# -M do: non frammentare (verifica jumbo frame end-to-end)
# -s 8972: payload 8972 + 28 header = 9000 bytes MTU
```

---

## Comandi di Migrazione

### qm migrate: Opzioni Complete

```bash
# Sintassi base
qm migrate <vmid> <target> [opzioni]

# ============================================================
# Migrazione ONLINE (live migration)
# ============================================================

# Migrazione live base
qm migrate 100 pve2 --online

# Migrazione live con limite di banda
qm migrate 100 pve2 --online --migration_bandwidth 500
# Limite: 500 MiB/s

# Migrazione live con rete specifica (override datacenter.cfg)
qm migrate 100 pve2 --online --migration_network 10.10.40.0/24

# Migrazione live con tipo specifico
qm migrate 100 pve2 --online --migration_type insecure

# Migrazione live con target storage (per migrare anche i dischi)
qm migrate 100 pve2 --online --targetstorage local-lvm

# Migrazione live con mapping storage specifico
qm migrate 100 pve2 --online --targetstorage "local-lvm:ceph-pool,local:local"

# ============================================================
# Migrazione OFFLINE (VM spenta)
# ============================================================

# Migrazione offline (la VM deve essere spenta)
qm migrate 100 pve2

# Migrazione offline con storage diverso
qm migrate 100 pve2 --targetstorage ceph-pool

# ============================================================
# Migrazione con storage locale (richiede replicazione o --with-local-disks)
# ============================================================

# Se la VM ha dischi su storage locale (non condiviso):
qm migrate 100 pve2 --online --with-local-disks

# Questo trasferisce anche i dischi locali durante la migrazione
# ATTENZIONE: molto piu lento, dipende dalla dimensione dei dischi
```

### Migrazione dei Container (pct migrate)

```bash
# Migrazione live di un container
pct migrate 200 pve2 --online

# Migrazione offline di un container
pct migrate 200 pve2

# Migrazione con restart (simile a live ma con breve interruzione)
pct migrate 200 pve2 --restart

# Opzioni specifiche per container:
# --timeout <seconds>   - Timeout per il trasferimento (default 180)
# --online              - Migrazione live (richiede storage condiviso)
```

---

## Requisiti Storage per la Migrazione

### Storage Condiviso (Ceph, NFS, iSCSI)

```
Storage condiviso: Il caso piu semplice

+-------------------+          +-------------------+
| Nodo Sorgente     |          | Nodo Destinazione |
| VM 100            |          | VM 100            |
|   |               |          |   |               |
+---+---------------+          +---+---------------+
    |                              |
    v                              v
+------------------------------------------+
|         STORAGE CONDIVISO                |
|         (Ceph / NFS / iSCSI)            |
|                                          |
|  vm-100-disk-0.raw                       |
|  vm-100-disk-1.raw                       |
+------------------------------------------+

Durante la migrazione:
- Solo la RAM e lo stato CPU vengono trasferiti
- I dischi sono gia accessibili da entrambi i nodi
- Migrazione veloce: dipende solo dalla quantita di RAM
```

### Storage Locale con Replicazione ZFS

```
Storage locale con replicazione:

+-------------------+          +-------------------+
| Nodo Sorgente     |          | Nodo Destinazione |
| VM 100            |          | VM 100 (replica)  |
|                   |          |                   |
| zpool: vmpool     |  replica | zpool: vmpool     |
|  vm-100-disk-0    | -------> |  vm-100-disk-0    |
|  (originale)      | ZFS send |  (snapshot)       |
+-------------------+          +-------------------+

Requisiti:
1. Replicazione ZFS configurata (pvesr) per la VM
2. La replica deve essere aggiornata (sincronizzata)
3. Durante la migrazione, viene inviata una replica incrementale finale
4. Il downtime e leggermente maggiore (per la sincronizzazione finale)
```

```bash
# Configurare la replicazione prima della migrazione
pvesr create-local-job 100-0 pve2 --schedule '*/15'

# Verificare che la replica sia aggiornata
pvesr status
# Se l'ultimo sync e recente, la migrazione sara veloce

# Forzare una sincronizzazione prima della migrazione
pvesr schedule-now 100-0

# Ora la migrazione puo procedere
qm migrate 100 pve2 --online
```

### Storage Locale Senza Replicazione (--with-local-disks)

```bash
# Se non c'e ne storage condiviso ne replicazione:
qm migrate 100 pve2 --online --with-local-disks

# Questo trasferisce i dischi via rete durante la migrazione
# MOLTO piu lento - dipende dalla dimensione dei dischi e dalla banda

# Stima tempo per disco da 100 GB su rete 10 Gbps:
# 100 GB / (10 Gbps / 8) = 100 / 1.25 = ~80 secondi (teorico)
# Con overhead: ~120-180 secondi

# Stima tempo per disco da 100 GB su rete 25 Gbps:
# 100 GB / (25 Gbps / 8) = 100 / 3.125 = ~32 secondi (teorico)
# Con overhead: ~45-60 secondi
```

---

## Stima del Downtime di Migrazione

### Fattori che Influenzano il Downtime

```
+------------------------------------------------------------------+
|              FATTORI DI DOWNTIME                                 |
+------------------------------------------------------------------+
|                                                                  |
| 1. Dimensione RAM della VM                                       |
|    - Piu RAM = piu dati da trasferire                           |
|    - Prima iterazione: trasferimento completo                    |
|                                                                  |
| 2. Dirty page rate (velocita di modifica memoria)               |
|    - VM con alta attivita di scrittura in RAM = piu iterazioni  |
|    - Database, application server = high dirty rate              |
|    - Web server statici = low dirty rate                         |
|                                                                  |
| 3. Banda della rete di migrazione                                |
|    - 10 Gbps: ~1 GB/s effettivo                                |
|    - 25 Gbps: ~2.5 GB/s effettivo                              |
|    - Con crittografia (secure): -30-50%                         |
|                                                                  |
| 4. Tipo di storage                                               |
|    - Condiviso: solo RAM da trasferire                          |
|    - Locale con replica: RAM + delta finale                     |
|    - Locale senza replica: RAM + TUTTI i dischi                 |
|                                                                  |
| 5. Carico CPU sul nodo sorgente e destinazione                  |
|    - CPU saturo = migrazione piu lenta                          |
|                                                                  |
+------------------------------------------------------------------+
```

### Tabella delle Stime di Downtime

```
+------------------+------------------+------------------+------------------+
| RAM VM           | 10 Gbps          | 25 Gbps          | Note             |
|                  | (downtime)       | (downtime)       |                  |
+------------------+------------------+------------------+------------------+
| 2 GB             | < 100 ms         | < 50 ms          | Quasi impercett. |
| 4 GB             | < 200 ms         | < 100 ms         | Minimo           |
| 8 GB             | 100-500 ms       | < 200 ms         | Accettabile      |
| 16 GB            | 200 ms - 1 sec   | 100-500 ms       | OK per la magg.  |
| 32 GB            | 500 ms - 2 sec   | 200 ms - 1 sec   | Pianificare      |
| 64 GB            | 1-5 sec          | 500 ms - 2 sec   | Attenzione       |
| 128 GB           | 2-10 sec         | 1-5 sec          | Off-peak         |
| 256 GB           | 5-30 sec         | 2-10 sec         | Manutenzione     |
+------------------+------------------+------------------+------------------+

Note: I valori dipendono fortemente dal dirty page rate della VM.
VM con alto I/O di memoria avranno downtime maggiori.
La migrazione "insecure" e circa 30-50% piu veloce della "secure".
```

### Monitorare la Migrazione in Corso

```bash
# Dalla riga di comando, monitorare il progresso
# (il task ID viene mostrato quando si avvia la migrazione)
qm migrate 100 pve2 --online

# Il progresso viene mostrato nel log:
# starting migration of VM 100 to node 'pve2'
# phase 1 - scan disk volumes
# phase 2 - start VM on remote node
# starting QEMU on remote node
# phase 3 - live migration
# migration: ram-total 8589934592 migration: ram-transferred 2147483648 ...
# migration: ram-remaining 1073741824 ...
# migration: status: active, transferred 7516192768, remaining 1073741824
# migration: status: completed
# migration finished successfully (duration 00:00:12)

# Dalla GUI:
# Task log visibile in Datacenter -> Task Log
# Oppure sulla VM specifica -> Task Log

# Monitorare la banda di migrazione in tempo reale
iftop -i bond2.40 -f "port 60000 or port 60001"

# Monitorare il traffico sulla rete di migrazione
nload bond2.40
```

---

## Troubleshooting delle Migrazioni Fallite

### Errori Comuni e Soluzioni

```bash
# ============================================================
# ERRORE: "can't migrate VM with local disks and no shared storage"
# ============================================================
# Causa: La VM ha dischi su storage locale non replicato
# Soluzione 1: Configurare la replicazione
pvesr create-local-job 100-0 pve2 --schedule '*/15'
# Attendere almeno una sincronizzazione completa
pvesr status

# Soluzione 2: Usare --with-local-disks
qm migrate 100 pve2 --online --with-local-disks

# Soluzione 3: Spostare i dischi su storage condiviso prima della migrazione
qm move-disk 100 scsi0 ceph-pool

# ============================================================
# ERRORE: "migration timed out"
# ============================================================
# Causa: La VM scrive in RAM piu velocemente di quanto la rete possa trasferire
# Soluzione 1: Aumentare la banda di migrazione (rete piu veloce)
# Soluzione 2: Ridurre il carico della VM prima della migrazione
# Soluzione 3: Usare migrazione insecure (piu veloce)
qm migrate 100 pve2 --online --migration_type insecure

# ============================================================
# ERRORE: "QEMU Live migration not possible: incompatible CPU"
# ============================================================
# Causa: CPU diverso tra sorgente e destinazione
# Soluzione 1: Configurare il tipo CPU nella VM come "x86-64-v2-AES" o simile
qm set 100 --cpu x86-64-v2-AES

# Soluzione 2: Usare "host" solo se i CPU sono identici
qm set 100 --cpu host
# ATTENZIONE: "host" espone tutte le feature CPU e impedisce la migrazione
# tra CPU diversi. Usare un tipo generico per massima compatibilita.

# Tipi CPU raccomandati per migrazione:
# x86-64-v2-AES : compatibile con CPU moderni, buone performance
# x86-64-v3     : richiede AVX2, piu restrittivo
# x86-64-v4     : richiede AVX-512, molto restrittivo
# kvm64         : massima compatibilita, performance ridotte
# host          : massime performance, nessuna compatibilita migrazione

# ============================================================
# ERRORE: "unable to connect to remote QEMU"
# ============================================================
# Causa: Problemi di rete o firewall sulle porte di migrazione
# Verifica:
# Porte necessarie: TCP 60000-60050 tra i nodi
nmap -p 60000-60050 10.10.40.12

# Verificare connettivita sulla rete di migrazione
ping -c 5 10.10.40.12

# Controllare il firewall
iptables -L -n | grep 60000

# ============================================================
# ERRORE: "not enough memory on target node"
# ============================================================
# Causa: Il nodo destinazione non ha RAM libera sufficiente
# Verifica:
ssh pve2 'free -g'
ssh pve2 'pvesh get /nodes/pve2/status | grep memory'

# Soluzione: Liberare RAM migrando altre VM o aggiungendo RAM

# ============================================================
# ERRORE: "VM uses a local device (passthrough)"
# ============================================================
# Causa: La VM ha un dispositivo PCI/USB in passthrough
# Il passthrough hardware impedisce la live migration

# Soluzione 1: Rimuovere il passthrough prima della migrazione
qm set 100 --delete hostpci0

# Soluzione 2: Usare migrazione offline (stop + start)
qm shutdown 100
qm migrate 100 pve2
qm start 100

# Soluzione 3: Usare mediated devices (vGPU) se supportati
```

### Log di Troubleshooting

```bash
# Log dettagliato della migrazione
journalctl -u pvedaemon --since "10 minutes ago" | grep -i "migrate\|migration"

# Log del task specifico (dalla GUI: Task Log)
# I log dei task sono in /var/log/pve/tasks/

# Log QEMU della VM durante la migrazione
tail -f /var/log/pve/qemu-server/100.log

# Abilitare il debug per le migrazioni
# (temporaneo, per troubleshooting)
qm migrate 100 pve2 --online 2>&1 | tee /tmp/migration-debug.log
```

---

## Script per Migrazioni di Massa

### Script Base: Migrare Tutte le VM da un Nodo

```bash
#!/bin/bash
# /usr/local/bin/migrate-all-from-node.sh
# Migra tutte le VM e CT da un nodo verso gli altri nodi del cluster

SOURCE_NODE="pve1"
TARGET_NODE="pve2"    # Nodo destinazione preferito
MIGRATION_TYPE="online"
BANDWIDTH=0           # 0 = illimitato

echo "=== Migrazione di massa da $SOURCE_NODE a $TARGET_NODE ==="
echo "Data: $(date)"
echo ""

# Elenco VM in esecuzione sul nodo sorgente
VMS=$(pvesh get /nodes/$SOURCE_NODE/qemu --output-format json 2>/dev/null | \
    python3 -c "import sys,json; [print(v['vmid']) for v in json.loads(sys.stdin.read()) if v.get('status')=='running']")

CTS=$(pvesh get /nodes/$SOURCE_NODE/lxc --output-format json 2>/dev/null | \
    python3 -c "import sys,json; [print(v['vmid']) for v in json.loads(sys.stdin.read()) if v.get('status')=='running']")

echo "VM da migrare: $VMS"
echo "CT da migrare: $CTS"
echo ""

# Migrare le VM
for VMID in $VMS; do
    echo "[$(date '+%H:%M:%S')] Migrazione VM $VMID verso $TARGET_NODE..."
    qm migrate $VMID $TARGET_NODE --$MIGRATION_TYPE --migration_bandwidth $BANDWIDTH 2>&1
    if [ $? -eq 0 ]; then
        echo "[$(date '+%H:%M:%S')] VM $VMID migrata con successo"
    else
        echo "[$(date '+%H:%M:%S')] ERRORE: migrazione VM $VMID fallita!"
    fi
    echo ""
done

# Migrare i CT
for CTID in $CTS; do
    echo "[$(date '+%H:%M:%S')] Migrazione CT $CTID verso $TARGET_NODE..."
    pct migrate $CTID $TARGET_NODE --$MIGRATION_TYPE 2>&1
    if [ $? -eq 0 ]; then
        echo "[$(date '+%H:%M:%S')] CT $CTID migrato con successo"
    else
        echo "[$(date '+%H:%M:%S')] ERRORE: migrazione CT $CTID fallita!"
    fi
    echo ""
done

echo "=== Migrazione completata ==="
echo "Verifica finale:"
echo "VM rimanenti su $SOURCE_NODE:"
qm list | grep -v "VMID"
echo ""
echo "CT rimanenti su $SOURCE_NODE:"
pct list
```

### Script Avanzato: Migrazione Bilanciata

```bash
#!/bin/bash
# /usr/local/bin/migrate-balanced.sh
# Distribuisce le VM equamente tra i nodi disponibili

SOURCE_NODE="pve1"
TARGET_NODES=("pve2" "pve3")  # Nodi destinazione
PARALLEL=2                     # Migrazioni parallele

echo "=== Migrazione bilanciata da $SOURCE_NODE ==="

# Raccogliere le VM
mapfile -t VMS < <(pvesh get /nodes/$SOURCE_NODE/qemu --output-format json 2>/dev/null | \
    python3 -c "import sys,json; [print(v['vmid']) for v in json.loads(sys.stdin.read()) if v.get('status')=='running']")

TOTAL=${#VMS[@]}
TARGETS=${#TARGET_NODES[@]}
PER_TARGET=$((TOTAL / TARGETS))
REMAINDER=$((TOTAL % TARGETS))

echo "Totale VM: $TOTAL"
echo "Nodi destinazione: ${TARGET_NODES[*]}"
echo "VM per nodo: ~$PER_TARGET"
echo ""

INDEX=0
for i in "${!TARGET_NODES[@]}"; do
    TARGET="${TARGET_NODES[$i]}"
    COUNT=$PER_TARGET
    if [ $i -lt $REMAINDER ]; then
        COUNT=$((COUNT + 1))
    fi

    echo "--- Migrando $COUNT VM verso $TARGET ---"
    for j in $(seq 1 $COUNT); do
        if [ $INDEX -lt $TOTAL ]; then
            VMID="${VMS[$INDEX]}"
            echo "[$(date '+%H:%M:%S')] qm migrate $VMID $TARGET --online"
            qm migrate $VMID $TARGET --online &

            # Controllare il numero di migrazioni parallele
            while [ $(jobs -r | wc -l) -ge $PARALLEL ]; do
                sleep 5
            done

            INDEX=$((INDEX + 1))
        fi
    done
done

# Attendere il completamento di tutte le migrazioni
wait
echo ""
echo "=== Tutte le migrazioni completate ==="
```

### Script con Verifica Pre-Migrazione

```bash
#!/bin/bash
# /usr/local/bin/safe-migrate.sh
# Migrazione con verifiche pre e post

VMID=$1
TARGET=$2

if [ -z "$VMID" ] || [ -z "$TARGET" ]; then
    echo "Uso: $0 <vmid> <target-node>"
    exit 1
fi

echo "=== Pre-flight check per VM $VMID verso $TARGET ==="

# 1. Verificare che la VM esista e sia running
STATUS=$(qm status $VMID 2>/dev/null | awk '{print $2}')
if [ "$STATUS" != "running" ]; then
    echo "ERRORE: VM $VMID non e in esecuzione (stato: $STATUS)"
    exit 1
fi
echo "[OK] VM $VMID e in esecuzione"

# 2. Verificare che il nodo destinazione sia online
TARGET_STATUS=$(pvesh get /nodes/$TARGET/status --output-format json 2>/dev/null | \
    python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('uptime',0))")
if [ "$TARGET_STATUS" = "0" ] || [ -z "$TARGET_STATUS" ]; then
    echo "ERRORE: Nodo $TARGET non raggiungibile"
    exit 1
fi
echo "[OK] Nodo $TARGET e online"

# 3. Verificare RAM disponibile
VM_RAM=$(qm config $VMID | grep "^memory:" | awk '{print $2}')
TARGET_FREE_RAM=$(pvesh get /nodes/$TARGET/status --output-format json 2>/dev/null | \
    python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(int((d['memory']['total']-d['memory']['used'])/1048576))")
echo "RAM VM: ${VM_RAM} MB | RAM libera su $TARGET: ${TARGET_FREE_RAM} MB"
if [ "$TARGET_FREE_RAM" -lt "$VM_RAM" ]; then
    echo "ERRORE: RAM insufficiente su $TARGET"
    exit 1
fi
echo "[OK] RAM sufficiente"

# 4. Verificare connettivita rete di migrazione
MIGRATION_NET=$(grep migration /etc/pve/datacenter.cfg 2>/dev/null | grep -oP 'network=\K[0-9.]+')
if [ -n "$MIGRATION_NET" ]; then
    echo "Rete di migrazione: $MIGRATION_NET"
fi
echo "[OK] Verifiche pre-migrazione superate"

# 5. Eseguire la migrazione
echo ""
echo "=== Avvio migrazione VM $VMID -> $TARGET ==="
START_TIME=$(date +%s)

qm migrate $VMID $TARGET --online 2>&1
RESULT=$?

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ $RESULT -eq 0 ]; then
    echo ""
    echo "=== Migrazione completata con successo ==="
    echo "Durata: ${DURATION} secondi"

    # Verifica post-migrazione
    NEW_STATUS=$(qm status $VMID 2>/dev/null | awk '{print $2}')
    echo "Stato VM dopo migrazione: $NEW_STATUS"
else
    echo ""
    echo "=== ERRORE: Migrazione fallita ==="
    echo "Codice di uscita: $RESULT"
    exit 1
fi
```

---

## Confronto con VMware vMotion

### Tabella Comparativa

```
+------------------------------------------+-------------------------------------------+
| VMware vMotion                           | Proxmox Live Migration                    |
+------------------------------------------+-------------------------------------------+
| Rete vMotion dedicata (VMkernel)         | Rete migrazione in datacenter.cfg         |
| Crittografia opzionale (vSphere 6.5+)   | Secure (default) o insecure              |
| vMotion multi-NIC (round-robin)          | Bond NIC per aggregazione                 |
| vMotion cross-vSwitch                    | Migrazione cross-bridge supportata        |
| Storage vMotion (disco live)             | qm move-disk (non live su storage div.)  |
| Cross-vCenter vMotion (vSphere 7+)      | Non supportato nativamente               |
| Enhanced vMotion Compatibility (EVC)     | CPU type nella config VM                  |
| vMotion notification hooks               | Nessun hook nativo                        |
| Concurrent vMotion limit (8/host)        | Nessun limite nativo (configurabile)      |
| Long Distance vMotion (< 150ms RTT)     | Possibile ma non ottimizzato              |
+------------------------------------------+-------------------------------------------+

Performance a confronto (10 Gbps, VM 8GB RAM):
+------------------------------------------+-------------------------------------------+
| VMware vMotion                           | Proxmox Live Migration                    |
+------------------------------------------+-------------------------------------------+
| Downtime tipico: 50-200 ms              | Downtime tipico: 100-500 ms              |
| Trasferimento: 3-5 secondi              | Trasferimento: 5-10 secondi              |
| Con crittografia: +20% overhead         | Secure mode: +30-50% overhead            |
+------------------------------------------+-------------------------------------------+
```

### Funzionalita Mancanti Rispetto a vMotion

```
Funzionalita VMware senza equivalente diretto in Proxmox:

1. Storage vMotion live (cambio storage a caldo tra datastore diversi)
   - Proxmox: qm move-disk funziona ma richiede VM ferma per storage diversi
   - Workaround: usare Ceph dove lo storage e gia condiviso

2. Cross-cluster migration
   - VMware: vMotion tra cluster diversi (stesso vCenter)
   - Proxmox: Non supportato. Richiede export/import

3. vMotion notification API
   - VMware: notifiche pre/post vMotion per applicazioni
   - Proxmox: Nessun hook nativo (script wrapper possibile)

4. Concurrent vMotion control
   - VMware: limite configurabile per host
   - Proxmox: Nessun controllo nativo (gestire manualmente)

5. Network-aware migration
   - VMware: DRS network-aware placement
   - Proxmox: Nessuna awareness automatica
```

---

## Ottimizzazione delle Performance di Migrazione

### Tuning della Rete

```bash
# Ottimizzare i parametri di rete per le migrazioni

# Aumentare i buffer TCP
sysctl -w net.core.rmem_max=67108864
sysctl -w net.core.wmem_max=67108864
sysctl -w net.ipv4.tcp_rmem="4096 87380 33554432"
sysctl -w net.ipv4.tcp_wmem="4096 65536 33554432"

# Rendere persistente
cat >> /etc/sysctl.d/99-migration-tuning.conf << 'EOF'
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
net.ipv4.tcp_rmem = 4096 87380 33554432
net.ipv4.tcp_wmem = 4096 65536 33554432
net.core.netdev_max_backlog = 30000
net.ipv4.tcp_congestion_control = bbr
EOF

sysctl -p /etc/sysctl.d/99-migration-tuning.conf

# Verificare che jumbo frame funzionino end-to-end
ping -c 5 -M do -s 8972 10.10.40.12
```

### Tuning QEMU per Migrazione

```bash
# Parametri QEMU per la migrazione (in /etc/pve/qemu-server/<vmid>.conf)

# Abilitare XBZRLE per VM con alta dirty rate
# (compressione incrementale della memoria)
# Aggiungere nel file di configurazione VM:
# args: -global migration.x-xbzrle-cache-size=536870912

# Per VM con molta RAM (>64GB), considerare multithread migration
# (disponibile in QEMU recenti)
```

---

## Migrazione e HA Manager

### Interazione tra Migrazione e HA

```bash
# Se una VM e gestita dall'HA Manager:

# Metodo CORRETTO: usare ha-manager migrate
ha-manager migrate vm:100 pve2
# Questo informa l'HA Manager che la migrazione e intenzionale

# Metodo ERRATO: usare qm migrate direttamente
qm migrate 100 pve2 --online
# Funziona ma l'HA Manager potrebbe tentare di "correggere" la situazione
# spostando la VM indietro al nodo preferito (se nofailback=0)

# Per migrazioni di massa con HA:
# 1. Temporaneamente impostare le VM in stato "ignored"
ha-manager set vm:100 --state ignored
# 2. Migrare
qm migrate 100 pve2 --online
# 3. Reimpostare lo stato
ha-manager set vm:100 --state started
```

---

## Conclusioni

La live migration in Proxmox VE e uno strumento maturo e affidabile per lo spostamento a caldo delle macchine virtuali. Sebbene non offra tutte le funzionalita avanzate di VMware vMotion (come Storage vMotion live o cross-cluster migration), copre tutti i casi d'uso principali per la gestione quotidiana di un cluster.

La chiave per migrazioni veloci e affidabili risiede nella configurazione corretta della rete dedicata, nell'uso di storage condiviso (o replicazione ZFS), e nella scelta appropriata del tipo di CPU per le VM. Gli script di migrazione di massa e le procedure di verifica pre/post migrazione rendono le operazioni di manutenzione prevedibili e sicure.

---

## Approfondimenti — note del 2026-04-27

> **Approfondimento — `migration_max_bandwidth` e `bwlimit`: due livelli di throttling.** In `/etc/pve/datacenter.cfg` esiste `bwlimit: migration=200000` (KB/s = 200 MB/s) come limite globale per tutte le migrazioni. Il flag `--bwlimit` su una singola `qm migrate` puo *abbassare* ulteriormente questo limite per quella migrazione (utile per migrazioni in orario di punta), ma non puo *superarlo*. Per workload critici che richiedono migrazione veloce, lasciare il bwlimit globale alto (es. 80% banda nominale rete) e abbassare per migrazioni "background". Verificare la velocita effettiva durante migrazione: `qm monitor <VMID> -c "info migrate"` mostra bandwidth corrente, dirty pages, status. Fonte: [Proxmox VE Admin Guide — datacenter.cfg](https://pve.proxmox.com/pve-docs/chapter-pvecm.html#_separate_cluster_network_after_installation), retrieved 2026-04-27.

> **Approfondimento — Dirty page rate calcolo pratico.** Per stimare se una VM convergera in live migration: (1) durante carico tipico, su Proxmox host eseguire `qm monitor <VMID> -c "x-debug-block-dirty-bitmap-sha256 ..."` (comando avanzato non sempre esposto), oppure piu semplicemente avviare una migrazione di prova con `qm migrate ... --online --bwlimit 100000` (100 MB/s deliberatamente basso) e osservare in `qm monitor <VMID> -c "info migrate"` il campo `dirty pages rate` (in pagine 4K/s); (2) convertire pagine/s a MB/s: `pages/s * 4096 / 1e6`; (3) confrontare con la bandwidth disponibile. Esempio: VM con 30000 dirty pages/s = 30000 * 4096 / 1e6 = ~123 MB/s di dirty rate; per convergere su rete 1 GbE (~125 MB/s), serve bandwidth ≥ ~150 MB/s effettivi. Fonte: [QEMU live migration internals](https://www.linux-kvm.org/page/Migration), retrieved 2026-04-27.

> **Approfondimento — `auto-converge` e `compress` per workload write-heavy.** QEMU 5.0+ ha `auto-converge` per default, che applica throttle CPU progressivo al guest se il dirty rate impedisce la convergenza. Proxmox 7.x+ lo abilita automaticamente. Per fine-tuning: `qm monitor <VMID> -c "migrate-set-parameters cpu-throttle-initial 20"` (inizia con 20% throttle), `cpu-throttle-increment 10` (aumenta del 10% per iterazione). Per workload con RAM molto comprimibile (DB con dati ripetitivi, sparse data): abilitare `compress` per ridurre la bandwidth richiesta del 30-60%, al costo di CPU usage piu alto sul source: `migrate-set-capabilities compress on`. Trade-off CPU vs network: se la rete e la bottleneck e CPU c'e, abilitare compress. Fonte: [QEMU Wiki — Migration features](https://wiki.qemu.org/Features/Migration), retrieved 2026-04-27.

> **Errore comune — Live migration di VM con `--cpu host` su cluster mixed.** Sintomo: `qm migrate 100 pve2 --online` fallisce immediatamente con errore "this host doesn't support requested CPU type" o silently durante boot della VM target. Causa: la VM era stata creata su pve1 con CPU Intel Xeon Gen 11 (con AVX-512); pve2 ha Xeon Gen 9 (senza AVX-512). Soluzione tattica: spegnere la VM, modificare il CPU type a `kvm64` o `x86-64-v2`, accettare la perdita di alcune feature, riavviare, riprovare migrate. Soluzione strategica: per cluster eterogenei, definire un baseline CPU comune in fase di acquisto hardware (es. tutti i nodi devono supportare AVX2 → `x86-64-v3` come default); documentare nei runbook che `--cpu host` e accettabile solo su cluster con hardware identico. Fonte: [QEMU x86 CPU models](https://www.qemu.org/docs/master/system/i386/cpu.html), retrieved 2026-04-27.

> **Errore comune — `--with-local-disks` su storage di destinazione quasi pieno.** Sintomo: `qm migrate 100 pve2 --online --with-local-disks` parte, copia il 70% del disco (~140 GB su un disco di 200 GB), poi fallisce con "no space left on device" sul target. Risultato peggiore: la VM e in stato "migrating" ma con disco parziale sul target e RAM ancora sul source — recovery manuale richiesto. Soluzione: verificare *prima* `pvesm status` sul target storage; richiedere ≥ 110% della dimensione VM (margine per snapshot, qcow2 overhead). Soluzione preventiva: hookscript `pre-migrate` che valida lo spazio target e aborta se < 110%. Fonte: [Proxmox VE Wiki — Storage Migration](https://pve.proxmox.com/wiki/Storage_Migration), retrieved 2026-04-27.

> **Caso reale — Cluster Proxmox 8 nodi, manutenzione kernel via rolling live migration.** Un cluster di produzione (8 nodi pve1-pve8, 200 VM totali) richiedeva upgrade kernel 6.5 → 6.8 con riavvio di ogni nodo. Procedura adottata: (1) `pvecm status` per verificare quorum (8/8); (2) per ogni nodo, in sequenza: marca il nodo "in manutenzione" via flag custom; live-migrate tutte le VM su altri nodi (`qm migrate <VMID> <target> --online`); attendi `qm status <VMID>` su tutti i target = `running`; aggiorna kernel; reboot; attendi rejoin cluster; ribilancia (live-migrate alcune VM indietro per distribuire carico); passa al nodo successivo. Tempo totale: ~6h per 8 nodi (~45 min/nodo, dominato da live migration di VM grandi). Risultato: zero downtime applicativo, zero alert. Lezione: live migration e *la* feature che permette manutenzione kernel/firmware in ambienti di produzione 24/7. Senza HA + live migration, ogni reboot richiede manutenzione programmata e applicativa. Fonte: case study interno; metodologia [Proxmox VE — Updates and upgrades guide](https://pve.proxmox.com/wiki/Upgrade_from_7_to_8), retrieved 2026-04-27.

> **Caso reale — VM Veeam Repository (40 GB RAM) non convergeva su rete 10 GbE.** Una VM Veeam Repository, durante un job di backup attivo (write throughput 1.5 GB/s), non convergeva in live migration: il dirty rate era ~800 MB/s e la bandwidth effettiva (rete 10 GbE) ~1 GB/s, ma overhead SSH cifrato + fragmentation MTU non-jumbo riducevano la bandwidth utile a ~700 MB/s < dirty rate. Soluzione: (1) `migration_type=insecure` (rete migration era VLAN dedicata isolata) → bandwidth da 700 → 950 MB/s; (2) MTU 9000 abilitato e validato → bandwidth da 950 → 1.15 GB/s; (3) attivato `compress` capability → riduzione 25% pagine trasferite. Risultato: convergenza in ~90s con downtime finale di 200ms (vs no convergenza prima). Lezione: per VM con dirty rate prossimi alla bandwidth, ogni ottimizzazione di rete conta. Fonte: case study interno; metodologia [QEMU performance tuning](https://wiki.qemu.org/Features/Migration), retrieved 2026-04-27.

---

## Esercizi

1. **Concettuale — calcolo del tempo di migrazione.** Per ognuno, stimare il tempo totale di live migration: (a) VM 8 GB RAM, dirty rate 50 MB/s, rete 1 GbE; (b) VM 64 GB RAM, dirty rate 200 MB/s, rete 10 GbE; (c) VM 256 GB RAM, dirty rate 800 MB/s, rete 25 GbE; (d) VM 32 GB RAM con disk 500 GB local-storage (caso `--with-local-disks`), rete 10 GbE storage + 10 GbE migration. Argomenta in 4-6 righe per ognuno, evidenziando se la migrazione converge naturalmente o richiede intervento.

2. **Lab — misurare bandwidth e dirty rate effettivi.** Su un cluster di test, creare una VM Linux con stress applicato (`stress-ng --vm 4 --vm-bytes 70% --timeout 600s`); avviare `qm migrate <VMID> <target> --online --bwlimit 50000` (50 MB/s artificialmente basso); in parallelo aprire `qm monitor <VMID> -c "info migrate"` ogni 5 secondi e registrare: bandwidth corrente, dirty pages rate, dirty pages totali. Tracciare un grafico delle 3 metriche nel tempo. Atteso: vedere come il dirty rate satura la bandwidth e la migrazione non converge, fino a quando l'auto-converge attiva il throttling.

3. **Scenario — pianificazione manutenzione cluster 6 nodi.** Hai un cluster con 6 nodi e 80 VM totali; ogni nodo ha 256 GB RAM con 80% di occupazione (~205 GB allocati per nodo, distribuiti su ~13 VM/nodo). Devi fare manutenzione su 1 nodo alla volta. Argomenta in 12-15 righe: (a) calcolo del tempo per spostare le 13 VM del nodo in manutenzione (assumere RAM media 16 GB, dirty rate medio 100 MB/s, rete 10 GbE dedicata); (b) ordine di migrazione (prima VM piccole o grandi? perche?); (c) target nodes (uniformemente distribuiti o concentrati?); (d) come gestire una VM che non converge (es. DB OLTP); (e) tempo totale stimato per il rolling maintenance dei 6 nodi.

4. **Stretch — script bulk migration con validazione pre/post.** Scrivere uno script Bash o Python che, dato un nodo source e un target: (1) lista tutte le VM running sul source; (2) per ognuna, verifica preconditions (storage condiviso? CPU type compatibile? target ha banda RAM/disk sufficiente?); (3) esegue `qm migrate ... --online`; (4) attende completion (timeout 30 min); (5) valida post: VM running su target, IP raggiungibile, guest agent risponde; (6) emette report finale (success/fail/skipped per ogni VM). Bonus: parallelizzare le migrazioni indipendenti (cap a 3 simultaneamente per non saturare la rete).

5. **Stretch — validazione SLA live migration.** Definire e validare uno SLA: "la live migration di qualsiasi VM nel cluster deve completare in ≤ 5 min con downtime ≤ 200ms". (a) Identificare le VM "rischiose" (RAM grande, dirty rate alto); (b) test sintetico: per le 3 VM piu grandi, eseguire 5 live migration consecutive registrando tempo totale e downtime (`qm monitor` durante la migrazione, oppure ping al guest da un client esterno con `ping -i 0.01`); (c) calcolare media e p99 dei tempi; (d) per le VM che non rispettano lo SLA, proporre azioni: aumento bandwidth dedicata, abilitazione compress, riduzione RAM, finestra di manutenzione esclusiva.

## Auto-valutazione

1. Spiega l'algoritmo memory pre-copy in 4 fasi (setup, pre-copy, stop-and-copy, resume).
2. Differenza pratica tra `qm migrate` (offline) e `qm migrate --online`.
3. Quando una migrazione "non converge"? Cosa intervieni per farla convergere?
4. Cosa fa `auto-converge` di QEMU e qual e il costo per il workload?
5. Come si configura una rete dedicata di migrazione in `/etc/pve/datacenter.cfg`?
6. `migration_type=secure` vs `insecure`: quando usare l'uno o l'altro?
7. Effetto di `--cpu host` sulla portabilita della VM tra nodi con CPU diverse.
8. Cosa fa `--with-local-disks` e quando e necessario?
9. Calcola il tempo minimo per migrare una VM da 64 GB su rete 10 GbE (ignorando dirty rate).
10. Comando per limitare la bandwidth di una migrazione a 50 MB/s.
11. Come monitorare in tempo reale lo stato di una live migration in corso?
12. Quale e la differenza tra storage condiviso e ZFS replicated per la live migration?

## Letture primarie consigliate

- Proxmox VE Admin Guide — Cluster Manager (live migration). https://pve.proxmox.com/pve-docs/chapter-pvecm.html (retrieved 2026-04-27).
- Proxmox VE Admin Guide — Migration. https://pve.proxmox.com/pve-docs/chapter-qm.html#qm_migration (retrieved 2026-04-27).
- Proxmox VE Wiki — Migration of servers to Proxmox VE. https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE (retrieved 2026-04-27).
- Proxmox VE Wiki — Storage Migration. https://pve.proxmox.com/wiki/Storage_Migration (retrieved 2026-04-27).
- QEMU Wiki — Migration features. https://wiki.qemu.org/Features/Migration (retrieved 2026-04-27).
- linux-kvm.org — Migration. https://www.linux-kvm.org/page/Migration (retrieved 2026-04-27).
- QEMU — x86 CPU models. https://www.qemu.org/docs/master/system/i386/cpu.html (retrieved 2026-04-27).
- VMware — vSphere vMotion (per confronto). https://docs.vmware.com/en/VMware-vSphere/8.0/com.vmware.vsphere.vcenterhost.doc/GUID-FE2B516E-7366-4978-B75C-64BF0AC676EB.html (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 10.1 — `ha-manager-regole-e-gruppi.md`: HA Manager coordina le migrazioni automatiche.
- Modulo 10.3 — `fencing-e-stonith.md`: fencing e prerequisito per migrazioni HA-driven.
- Modulo 10.4 — `bilanciamento-carico-vm.md`: live migration e lo strumento per il rebalancing.
- Modulo 04 — `../04-NETWORKING-AVANZATO-PROXMOX/linux-bridge-vlan-bonding.md`: bonding LACP + jumbo per migration network.
- Modulo 06.3 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/live-migration-minimo-downtime.md`: principi generali di live migration applicati al cutover VMware → Proxmox.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Live migration** | Spostamento di una VM running tra nodi senza interruzione percepibile. |
| **Pre-copy** | Algoritmo: copia RAM iterativamente finche dirty rate < bandwidth. |
| **Post-copy** | Algoritmo alternativo: stop guest, fai resume sul target, RAM pages copiate on-demand. |
| **Dirty page rate** | Pagine RAM modificate al secondo dal workload. |
| **Stop-and-copy phase** | Fase finale: pause guest, copy delta + state, resume sul target. |
| **`migration_max_bandwidth`** | Limite globale bandwidth migrazione in `/etc/pve/datacenter.cfg`. |
| **`bwlimit`** | Per-migration override del limite bandwidth (in KB/s). |
| **`migration_type=secure`** | Migrazione cifrata via SSH tunnel (default). |
| **`migration_type=insecure`** | Migrazione non cifrata; accettabile su rete dedicata isolata. |
| **`migration_network`** | Rete dedicata per traffico di migrazione (es. VLAN privata 10 GbE). |
| **`auto-converge`** | Feature QEMU: throttle CPU guest per ridurre dirty rate. |
| **`compress`** | Feature QEMU: comprime pagine RAM trasferite (CPU vs banda trade-off). |
| **`--with-local-disks`** | Migra anche dischi local-storage (RAM + disk copy). |
| **`--targetstorage`** | Mapping di storage source→target durante migrazione. |
| **`--bwlimit`** | Override bandwidth per singola migrazione. |
| **`info migrate` (qm monitor)** | Comando QEMU per status migrazione corrente. |
| **`-c "migrate-set-parameters ..."`** | Comando QEMU per modificare parametri migrazione runtime. |
| **`migration_downtime`** | Soglia downtime accettabile per stop-and-copy (default 100ms). |
| **vMotion** | Equivalente VMware di live migration; concetti analoghi. |
| **Storage vMotion** | Spostamento di disco VMware a caldo (Proxmox: `--with-local-disks` o `--targetstorage`). |
