# Multi-Site Disaster Recovery su Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 8 — Continuita di servizio · Modulo 19 (nuovo, vedi `00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 10 (HA cluster), 11 (backup PBS), 12 (sicurezza), 13 (monitoring), 18 (cutover); concetti DR (RTO/RPO geo, network latency tra siti, asynchronous replication, BCP), familiarita con CDN, GeoDNS, Anycast.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. distinguere **Disaster Recovery** (DR — perdita totale di un sito, recovery su altro sito) da **High Availability** (HA — singolo guasto interno al sito);
> 2. progettare topologie multi-site Proxmox: active/passive (DR site cold/warm), active/active (sincrono o asincrono), stretched cluster (sconsigliato);
> 3. configurare **storage replication** tra siti: ZFS async replication (`zfs send | zfs receive`), Ceph multi-site/RBD mirroring (`rbd-mirror` daemon), PBS sync verso secondo PBS;
> 4. gestire **network DR**: VPN/MPLS site-to-site, BGP per IP pubblici migrabili, GeoDNS (Route 53, Cloudflare) per fallover endpoint;
> 5. eseguire **DR drill** annuali con failover effettivo, tempi misurati, post-mortem;
> 6. calcolare **RTO/RPO geografici** realistici (RTO 1-4h tipico per active/passive Proxmox; RPO 1-15 min con Ceph mirroring async, 0 con sync ma con costo latenza);
> 7. mappare requisiti compliance (DORA, EBA Guidelines, NIS2 directive 2025) a feature Proxmox e gap.
> **Tempo stimato:** lettura 90-120 min · pianificazione DR program 4-12 settimane · drill execution 24-48h
> **Livello:** proficient → expert (Dreyfus 4 → 5)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; ZFS 2.2/2.3; Ceph Quincy/Reef/Squid; PBS 3.x; NIS2 directive 2022/2555 (recepimento 2024-10).

---

## Mappa concettuale

```
+============================================================+
|     Multi-site DR: topologie e flussi                       |
+============================================================+
|                                                            |
|   TOPOLOGIA 1: ACTIVE/PASSIVE COLD                         |
|                                                            |
|   Site A (production)        Site B (DR cold)              |
|   +------------+              +------------+               |
|   | Proxmox    |              | Proxmox    |               |
|   | + storage  |              | + storage  |               |
|   | + workload |              | (no VM     |               |
|   |            |              |  running)  |               |
|   +-----+------+              +-----^------+               |
|         |                           |                      |
|         | replication async         |                      |
|         | (PBS sync, ZFS send/recv) |                      |
|         |                           |                      |
|         +---------------------------+                      |
|                                                            |
|   RTO: 4-12h (manuale boot delle VM su Site B)            |
|   RPO: 5-30 min (frequenza replication)                    |
|   Cost: minimo (HW Site B in idle)                         |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   TOPOLOGIA 2: ACTIVE/PASSIVE WARM                         |
|                                                            |
|   Site A (production)        Site B (DR warm)              |
|   +------------+              +------------+               |
|   | Proxmox    | ────────────►| Proxmox    |               |
|   | + workload |  Ceph        | + workload |               |
|   | RUNNING    |  multi-site  | RUNNING    |               |
|   +------------+  RBD mirror  +------------+               |
|                                Mode: read-only o limited   |
|                                                            |
|   RTO: 30 min - 2h (DNS cutover + promote)                 |
|   RPO: 1-15 min (async Ceph mirror)                        |
|   Cost: medio (HW Site B in low utilization)               |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   TOPOLOGIA 3: ACTIVE/ACTIVE                               |
|                                                            |
|   Site A                      Site B                       |
|   +------------+              +------------+               |
|   | Proxmox    | ◄────────────►| Proxmox    |              |
|   | LB attivo  |  Ceph sync   | LB attivo  |               |
|   |            |  (geo)       |            |               |
|   +------------+              +------------+               |
|                                                            |
|   RTO: < 5 min (DNS GeoDNS auto-fallover)                  |
|   RPO: 0 (sync replication)                                |
|   Cost: alto (HW raddoppiato + low-latency network)        |
|   Vincolo: latency Site A <-> Site B < 5ms (limite Ceph)   |
|                                                            |
|------------------------------------------------------------|
|                                                            |
|   TOPOLOGIA 4: STRETCHED CLUSTER (sconsigliato)            |
|                                                            |
|   Single Proxmox cluster spanning two sites.               |
|   Corosync richiede latenza < 5ms; in caso contrario       |
|   diagnose sbagliate, fence loop, split-brain.             |
|   Adatto solo per metro distance (< 50km, fibra dark).     |
|                                                            |
+============================================================+
```

## Idee guida del modulo

1. **DR e BCP, non solo backup.** Backup ti permette di restore. DR ti permette di ricominciare a operare. Sono problemi diversi: backup ha RPO, DR ha RTO + RPO + business continuity plan.
2. **RTO/RPO definiscono la topologia, non viceversa.** RTO 4h = active/passive cold sufficiente. RTO 5min = active/active obbligatorio. Inutile costruire sync replication se il business accetta 4h di outage.
3. **Async replication ha overhead operativo accettabile.** ZFS send/recv via cron, Ceph RBD mirror async, PBS sync: tutti operano in background, no impatto su workload primario.
4. **Drill annuale e mandatory.** "Abbiamo DR pronto" senza drill = falsa sicurezza. Il drill rivela: documentazione obsoleta, credenziali scadute, dipendenze nascoste, RTO real vs target.
5. **NIS2 e DORA cambiano il gioco compliance.** NIS2 (recepito UE 2024-10) richiede prove di resilience operativa per servizi essenziali. DR diventa obbligo regolatorio, non discretionary.

---

## Indice

- [Topologie DR](#topologie-dr)
- [RTO/RPO Design e Calcolo](#rtorpo-design-e-calcolo)
- [Storage replication patterns](#storage-replication)
- [Network DR patterns](#network-dr)
- [WAN Replication e Ottimizzazione](#wan-replication-e-ottimizzazione)
- [Ceph Stretch Cluster (metro-distance)](#ceph-stretch-cluster)
- [DR drill methodology](#dr-drill)
- [Automated DR Testing](#automated-dr-testing)
- [Compliance: NIS2, DORA, EBA Guidelines](#compliance)
- [Failover playbook](#failover-playbook)
- [Failback playbook](#failback-playbook)
- [Runbook Templates](#runbook-templates)
- [DNS Failover](#dns-failover)
- [Cost analysis](#cost-analysis)
- [Troubleshooting](#troubleshooting)
- [Esercizi](#esercizi)

---

## Topologie DR

### Active/passive cold

Pattern semplice, costo minimo. Site B accende le VM solo durante un disastro Site A.

Componenti:
- Storage replication async (PBS sync, ZFS send/recv).
- Network: VPN site-to-site IPsec o MPLS.
- DNS: TTL bassi (300s) per record critici; aggiornare manualmente al failover.

Pro: cost-effective, manuale = controllabile.
Contro: RTO alto (4-12h), errore umano possibile.

**Architettura dettagliata:**

```
Site A (Primary — Milano)                  Site B (DR Cold — Roma)
+=============================+            +=============================+
| Proxmox Cluster (3 nodi)    |            | Proxmox Cluster (3 nodi)    |
| +--------+ +--------+      |            | +--------+ +--------+      |
| | node-a1| | node-a2|      |            | | node-b1| | node-b2|      |
| | 64C    | | 64C    |      |            | | 64C    | | 64C    |      |
| | 512G   | | 512G   |      |            | | 512G   | | 512G   |      |
| +--------+ +--------+      |            | +--------+ +--------+      |
| +--------+                  |            | +--------+                  |
| | node-a3|   VM running     |            | | node-b3|   VM spente     |
| | 64C    |   120 VM         |            | | 64C    |   0 VM active   |
| | 512G   |                  |            | | 512G   |                  |
| +--------+                  |            | +--------+                  |
|                             |            |                             |
| +--------+                  |            | +--------+                  |
| | PBS-A  |---repl async---->|            | | PBS-B  | store replicate  |
| | 20 TB  |  ogni 15 min    |---VPN----->| | 20 TB  | pronto restore   |
| +--------+                  |            | +--------+                  |
+=============================+            +=============================+

VPN IPsec/WireGuard: 100 Mbps - 1 Gbps
Latenza: 10-50 ms (irrilevante per async)
```

**Procedura di attivazione cold DR:**

```bash
# 1. Verificare che PBS-B abbia tutti i backup recenti
proxmox-backup-client list --repository pbs-b.example.com:main

# 2. Per ogni VM critica, restore su Site B
proxmox-backup-client restore vm/<VMID>/2026-05-22T03:00:00Z \
  --repository pbs-b.example.com:main \
  vm.conf /tmp/restore/

# 3. Importare la configurazione VM su Proxmox Site B
qmrestore /tmp/restore/vzdump-qemu-<VMID>-*.vma.zst <VMID-nuovo> \
  --storage local-lvm

# 4. Aggiustare la rete (se subnet diverse)
qm set <VMID-nuovo> --net0 virtio,bridge=vmbr0,tag=100

# 5. Avviare in ordine: infra → DB → app → web
qm start <VMID-dns>
qm start <VMID-db>
qm start <VMID-app>
qm start <VMID-web>
```

### Active/passive warm

Site B ha le VM accese (read-only o limited functionality) per ridurre RTO.

Componenti:
- Ceph RBD mirror in async mode.
- Application-aware fallover (DB read-replica → primary, etc.).
- DNS automatico GeoDNS.

Pro: RTO < 1h.
Contro: cost medio, complessita applicativa (read-only handling).

**Dettaglio architetturale warm standby:**

```
Site A (Primary)                          Site B (Warm Standby)
+================================+        +================================+
| Proxmox + Ceph Cluster         |        | Proxmox + Ceph Cluster         |
|                                |        |                                |
| Ceph Pool: rbd-prod            |        | Ceph Pool: rbd-dr              |
|   rbd-mirror daemon active --->|------->|   rbd-mirror daemon active     |
|   (image mode: snapshot)       |  WAN   |   (peer: site-a)               |
|                                |        |                                |
| VM-db-01: PostgreSQL primary   |        | VM-db-01-dr: read-replica      |
| VM-app-01: Tomcat active       |        | VM-app-01-dr: standby warm     |
| VM-web-01: NGINX active        |        | VM-web-01-dr: NGINX standby    |
+================================+        +================================+

Failover: promote RBD images su Site B → boot VM → DNS cutover
RTO reale misurato: 15-45 min (con automazione)
RPO: 5-15 min (snapshot interval Ceph mirror)
```

**Configurazione PostgreSQL streaming replication cross-site:**

```bash
# Site A — postgresql.conf (primary)
wal_level = replica
max_wal_senders = 5
wal_keep_size = 1GB
synchronous_standby_names = ''  # async per cross-WAN

# Site A — pg_hba.conf
host replication repl_user 10.20.0.0/24 scram-sha-256

# Site B — recovery setup
sudo -u postgres pg_basebackup \
  -h site-a-db.example.com -D /var/lib/postgresql/16/main \
  -U repl_user -P -Xs -R

# Site B — postgresql.conf (standby)
primary_conninfo = 'host=site-a-db.example.com port=5432 user=repl_user password=*** sslmode=require'
hot_standby = on
hot_standby_feedback = on
```

### Active/active sincrono

Entrambi i siti servono traffico, replication sincrona.

Componenti:
- Ceph stretched cluster con CRUSH rules per separare repliche tra siti.
- Network low-latency (< 5ms).
- Load balancing globale (GeoDNS, GSLB).

Pro: RTO < 5min, RPO 0.
Contro: cost massimo, latenza network e single-point-of-design.

**Vincoli stringenti per active/active:**

| Requisito | Valore | Conseguenza violazione |
|---|---|---|
| Latenza RTT inter-site | < 5 ms | Ceph timeout, write penalty |
| Bandwidth inter-site | >= 10 Gbps dedicated | Replication lag, RPO > 0 |
| Jitter | < 1 ms | Ceph OSD flapping |
| Packet loss | < 0.01% | Recovery storms |
| MTU | 9000 (jumbo frame) | Throughput degradato |
| Clock sync | NTP < 1 ms drift | Split-brain risk |

**Calcolo bandwidth necessario per sync replication:**

```
BW_sync = Write_IOPS × Block_Size × Replication_Factor_Cross_Site

Esempio:
  Write IOPS medio:       3000
  Block size medio:       8 KB
  Repliche cross-site:    1 (la terza replica va sull'altro sito)

  BW_sync = 3000 × 8 KB = 24 MB/s = 192 Mbps sustained
  Con overhead Ceph:      192 × 1.3 = ~250 Mbps
  Con headroom per burst: 250 × 3 = ~750 Mbps
  Raccomandazione:        1 Gbps dedicated (minimo)
                          10 Gbps per ambienti con >100 VM
```

### Stretched cluster (sconsigliato per > 50km)

Singolo cluster Proxmox spanning due siti. Corosync token timeout (default 10s) tollera fino a ~5ms di latenza one-way. Oltre, falsi positivi → cluster instabile.

**Perche e sconsigliato — analisi tecnica:**

```
Corosync timeout chain (default values):
  token:        10000 ms  (tempo massimo per ricevere token)
  token_retransmit: 4800 ms
  consensus:    12000 ms
  join:         3000 ms

Latenza WAN tipica:
  Same city (fibra dark):     0.5 - 2 ms     → OK
  50 km (fibra lit):          2 - 5 ms        → borderline
  100 km:                     5 - 10 ms       → instabile
  Cross-region (500+ km):     20 - 80 ms      → non fattibile

Problema: con 10ms RTT, un token round-trip a 3 nodi impiega
  3 × 10 ms = 30 ms per round. Con jitter WAN (±5 ms),
  il token puo arrivare in ritardo → false positive →
  fencing del nodo remoto → VM killed senza motivo.
```

**Se proprio devi (metro-distance < 30km):**

```bash
# Aumentare i timeout Corosync per tollerare latenza metro
# /etc/pve/corosync.conf (da modificare SOLO con pvecm)
pvecm updatecerts

# Editare manualmente con attenzione:
# totem {
#   token: 15000
#   token_retransmits_before_loss_const: 20
#   consensus: 18000
#   join: 5000
# }

# Verificare stato dopo modifica
corosync-cfgtool -s
pvecm status
```

---

## RTO/RPO Design e Calcolo

### Framework RTO/RPO

```
                    RPO
                    |
        0    5min  15min  1h    4h    24h
        |-----|------|-----|-----|------|
        |     |      |     |     |      |
RTO     |     |      |     |     |      |
  < 5m  | A/A |      |     |     |      |  ← Ceph sync + GeoDNS
  15m   |     | Warm |     |     |      |  ← Ceph async + automation
  1h    |     |      | Warm|     |      |  ← PBS sync + scripted failover
  4h    |     |      |     | Cold|      |  ← PBS sync + manual failover
  24h   |     |      |     |     | Cold |  ← Backup tape + manual
  72h   |     |      |     |     |      | Cold  ← Offsite backup only
```

### Calcolo RTO realistico per topologia

**Active/passive cold — breakdown temporale:**

```
Componente                                    Tempo
─────────────────────────────────────────────────────
Detection (monitoring alert → human ack)      5-30 min
Decision (declare disaster, authorize)        10-30 min
Comunicazione (war room, stakeholder)         5-15 min
PBS restore (20 VM × 100GB media)             60-180 min
  → throughput restore: ~500 MB/s per stream
  → 20 × 100 GB = 2 TB / 500 MB/s = ~67 min
  → con parallelismo 4 stream: ~17 min transfer
  → overhead config/boot: 3-5 min per VM
  → totale: 17 + (20 × 4 min) = ~97 min
Network cutover (DNS, VPN routing)            10-30 min
Smoke test (critical paths)                   15-30 min
Open production traffic                       5-10 min
─────────────────────────────────────────────────────
TOTALE STIMATO                                2-6 h
TOTALE CON IMPREVISTI (+50%)                  3-9 h
TARGET DICHIARABILE (conservativo)            4-12 h
```

**Active/passive warm — breakdown temporale:**

```
Componente                                    Tempo
─────────────────────────────────────────────────────
Detection (automated health check)            1-5 min
Decision (auto o semi-auto)                   5-15 min
Ceph RBD promote (per ogni image)             1-3 min
  → rbd mirror image promote <pool>/<image>
DB promote (PostgreSQL: pg_promote)           1-2 min
Application restart (gia warm)                2-5 min
DNS cutover (GeoDNS, TTL 60s)                 1-5 min
Smoke test                                    5-10 min
─────────────────────────────────────────────────────
TOTALE STIMATO                                15-45 min
TARGET DICHIARABILE                           30 min - 2h
```

### Calcolo RPO per tecnologia di replication

| Tecnologia | RPO tipico | RPO worst-case | Note |
|---|---|---|---|
| Ceph RBD mirror (snapshot, 5min) | 5 min | 10 min | Il worst-case e 2× interval se lo snapshot avviene subito prima del disastro |
| Ceph RBD mirror (journal) | ~0 (near-sync) | 5-30 sec | Journal mode deprecato; snapshot mode preferito da Pacific+ |
| ZFS send/recv (cron 15min) | 15 min | 30 min | Worst case: disaster durante il send |
| PBS sync (schedule 2h) | 2h | 4h | Backup-level RPO, non storage-level |
| PBS sync (schedule 15min) | 15 min | 30 min | Possibile ma costoso in banda |
| Ceph sync replication | 0 | 0 | Solo metro-distance (< 5ms RTT) |

### Matrice RTO/RPO → Costo indicativo

```
RTO\RPO    0 (zero)    5 min       15 min      1 h         4 h
─────────────────────────────────────────────────────────────────
< 5 min    €€€€€       -           -           -           -
           A/A sync    n/a         n/a         n/a         n/a
           (3x prod)

30 min     €€€€        €€€         -           -           -
           A/A sync    Warm+Ceph   n/a         n/a         n/a
           (2.5x)      (2.2x)

1-2 h      -           €€€         €€          -           -
                       Warm+Ceph   Warm+PBS    n/a         n/a
                       (2.2x)      (2x)

4-12 h     -           -           €€          €           €
                                   Cold+ZFS    Cold+PBS    Cold+PBS
                                   (1.7x)      (1.5x)     (1.3x)
```

---

## Storage replication

### ZFS send/receive (per ZFS pool)

**Configurazione completa ZFS replication cross-site:**

```bash
# ============================================================
# Site A (source): setup iniziale
# ============================================================

# 1. Creare snapshot iniziale full
zfs snapshot -r rpool/data@dr-init-$(date +%Y%m%d)

# 2. Send iniziale full verso Site B (prima volta, puo essere lento)
zfs send -Rv rpool/data@dr-init-20260522 | \
  ssh -c aes256-gcm@openssh.com dr-site.example.com \
  "zfs receive -Fduv rpool/data"

# Nota: -R = recursive, -v = verbose
# Nota: -F su receive = force rollback del target a ultimo snapshot
# Nota: -c aes256-gcm = cipher veloce per throughput alto

# 3. Verificare che il receive sia riuscito
ssh dr-site.example.com "zfs list -t snapshot rpool/data"
```

**Script di replication incrementale schedulato:**

```bash
#!/bin/bash
# /usr/local/bin/zfs-dr-replicate.sh
# Eseguire via cron ogni 15 minuti
# crontab -e → */15 * * * * /usr/local/bin/zfs-dr-replicate.sh >> /var/log/zfs-dr.log 2>&1

set -euo pipefail

POOL="rpool/data"
REMOTE="dr-site.example.com"
REMOTE_USER="root"
SSH_KEY="/root/.ssh/dr_replication_ed25519"
SSH_OPTS="-i $SSH_KEY -c aes256-gcm@openssh.com -o ConnectTimeout=10"
LOCK_FILE="/var/run/zfs-dr-replicate.lock"
LOG_TAG="zfs-dr"
RETENTION_HOURS=48

# Evitare esecuzioni parallele
exec 200>"$LOCK_FILE"
flock -n 200 || { logger -t "$LOG_TAG" "ERROR: altra istanza in esecuzione"; exit 1; }

SNAP_NAME="dr-$(date +%Y%m%d-%H%M%S)"
PREV_SNAP=$(zfs list -H -t snapshot -o name -s creation "$POOL" 2>/dev/null | grep "dr-" | tail -1 | cut -d@ -f2)

if [ -z "$PREV_SNAP" ]; then
    logger -t "$LOG_TAG" "ERROR: nessun snapshot precedente dr-* trovato. Eseguire full send iniziale."
    exit 1
fi

# Creare nuovo snapshot
zfs snapshot -r "${POOL}@${SNAP_NAME}"
logger -t "$LOG_TAG" "Snapshot creato: ${POOL}@${SNAP_NAME}"

# Inviare delta incrementale
START_TIME=$(date +%s)
zfs send -Ri "@${PREV_SNAP}" "${POOL}@${SNAP_NAME}" | \
  ssh $SSH_OPTS "${REMOTE_USER}@${REMOTE}" \
  "zfs receive -Fduv $POOL" 2>&1 | logger -t "$LOG_TAG"

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
logger -t "$LOG_TAG" "Replication completata in ${ELAPSED}s"

# Pulizia snapshot vecchi (> RETENTION_HOURS)
CUTOFF=$(date -d "${RETENTION_HOURS} hours ago" +%Y%m%d-%H%M%S)
zfs list -H -t snapshot -o name "$POOL" | grep "dr-" | while read SNAP; do
    SNAP_TS=$(echo "$SNAP" | grep -oP 'dr-\K[0-9-]+')
    if [[ "$SNAP_TS" < "$CUTOFF" ]]; then
        # Non cancellare lo snapshot piu recente prima del corrente (serve come base)
        if [ "$SNAP" != "${POOL}@${PREV_SNAP}" ]; then
            zfs destroy "$SNAP"
            logger -t "$LOG_TAG" "Snapshot rimosso: $SNAP"
        fi
    fi
done

# Pulizia snapshot remoti (stessa logica)
ssh $SSH_OPTS "${REMOTE_USER}@${REMOTE}" \
  "zfs list -H -t snapshot -o name $POOL | grep 'dr-'" | while read SNAP; do
    SNAP_TS=$(echo "$SNAP" | grep -oP 'dr-\K[0-9-]+')
    if [[ "$SNAP_TS" < "$CUTOFF" ]] && [ "$(echo "$SNAP" | cut -d@ -f2)" != "$PREV_SNAP" ]; then
        ssh $SSH_OPTS "${REMOTE_USER}@${REMOTE}" "zfs destroy $SNAP"
        logger -t "$LOG_TAG" "Snapshot remoto rimosso: $SNAP"
    fi
done

logger -t "$LOG_TAG" "Ciclo completato."
```

**Monitoraggio ZFS replication health:**

```bash
#!/bin/bash
# /usr/local/bin/zfs-dr-check.sh
# Verifica che la replication sia aggiornata

POOL="rpool/data"
REMOTE="dr-site.example.com"
MAX_LAG_MINUTES=30

# Ultimo snapshot locale
LOCAL_LATEST=$(zfs list -H -t snapshot -o name,creation -s creation "$POOL" | \
  grep "dr-" | tail -1)
LOCAL_TS=$(echo "$LOCAL_LATEST" | awk '{print $2, $3, $4, $5, $6}')

# Ultimo snapshot remoto
REMOTE_LATEST=$(ssh "$REMOTE" \
  "zfs list -H -t snapshot -o name,creation -s creation $POOL | grep 'dr-' | tail -1")
REMOTE_TS=$(echo "$REMOTE_LATEST" | awk '{print $2, $3, $4, $5, $6}')

# Confrontare
LOCAL_EPOCH=$(date -d "$LOCAL_TS" +%s 2>/dev/null || echo 0)
REMOTE_EPOCH=$(date -d "$REMOTE_TS" +%s 2>/dev/null || echo 0)
LAG_MIN=$(( (LOCAL_EPOCH - REMOTE_EPOCH) / 60 ))

echo "Local latest:  $LOCAL_LATEST"
echo "Remote latest: $REMOTE_LATEST"
echo "Lag: ${LAG_MIN} minuti"

if [ "$LAG_MIN" -gt "$MAX_LAG_MINUTES" ]; then
    echo "ALERT: replication lag ${LAG_MIN} min > threshold ${MAX_LAG_MINUTES} min"
    # Inviare alert (Zabbix, mail, Slack)
    exit 2
fi
echo "OK: replication entro soglia."
exit 0
```

### Ceph RBD mirror

**Setup completo Ceph RBD mirroring tra due cluster:**

```bash
# ============================================================
# Site A: cluster Ceph primario
# ============================================================

# 1. Abilitare il mirroring sul pool
ceph osd pool create rbd-prod 128 128
rbd pool init rbd-prod
rbd mirror pool enable rbd-prod image

# 2. Creare utente per il peering
ceph auth get-or-create client.rbd-mirror-peer \
  mon 'profile rbd-mirror-peer' \
  osd 'profile rbd' \
  -o /etc/ceph/ceph.client.rbd-mirror-peer.keyring

# 3. Ottenere il token di bootstrap per il peering
rbd mirror pool peer bootstrap create \
  --site-name site-a rbd-prod > /tmp/bootstrap-token-site-a

# ============================================================
# Site B: cluster Ceph DR
# ============================================================

# 1. Creare pool corrispondente
ceph osd pool create rbd-prod 128 128
rbd pool init rbd-prod
rbd mirror pool enable rbd-prod image

# 2. Importare il token di bootstrap dal Site A
rbd mirror pool peer bootstrap import \
  --site-name site-b \
  --direction rx-only \
  rbd-prod /tmp/bootstrap-token-site-a

# 3. Avviare il daemon rbd-mirror
systemctl enable --now ceph-rbd-mirror@admin.service

# 4. Verificare il peering
rbd mirror pool info rbd-prod
rbd mirror pool status rbd-prod
```

**Abilitare il mirroring per singole immagini RBD:**

```bash
# Per ogni VM da proteggere, abilitare il mirror sull'immagine disco
# Modalita snapshot (raccomandata da Ceph Pacific 16+)

# Listare le immagini del pool
rbd ls rbd-prod

# Abilitare mirror snapshot per una specifica immagine
rbd mirror image enable rbd-prod/vm-100-disk-0 snapshot

# Configurare l'intervallo di snapshot (default: 5 minuti)
rbd mirror snapshot schedule add --pool rbd-prod --image vm-100-disk-0 5m

# Verificare lo stato del mirror per l'immagine
rbd mirror image status rbd-prod/vm-100-disk-0

# Output atteso:
# vm-100-disk-0:
#   global_id:   ...
#   state:       up+replaying
#   description: replaying, ...
#   last_update: 2026-05-22 10:30:15

# Verificare stato di TUTTE le immagini
rbd mirror pool status rbd-prod --verbose
```

**Failover Ceph RBD mirror (promote su Site B):**

```bash
# ============================================================
# Failover: promuovere le immagini su Site B
# ============================================================

# 1. (Opzionale) Se Site A e ancora raggiungibile, demote prima
# Su Site A:
rbd mirror image demote rbd-prod/vm-100-disk-0

# 2. Su Site B: promote le immagini
rbd mirror image promote rbd-prod/vm-100-disk-0

# Se Site A NON e raggiungibile (disaster reale):
rbd mirror image promote --force rbd-prod/vm-100-disk-0
# --force: promuove anche se il demote non e avvenuto
# ATTENZIONE: possibile perdita dati fino all'ultimo snapshot

# 3. Verificare che l'immagine sia ora primary
rbd mirror image status rbd-prod/vm-100-disk-0
# state: up+stopped (primary)

# 4. Creare/aggiornare la config VM su Proxmox Site B
qm create 100 \
  --name vm-web-01-dr \
  --memory 4096 \
  --cores 4 \
  --scsi0 rbd-prod:vm-100-disk-0 \
  --net0 virtio,bridge=vmbr0 \
  --boot order=scsi0 \
  --ostype l26

qm start 100
```

**Script di failover automatizzato per tutte le VM protette:**

```bash
#!/bin/bash
# /usr/local/bin/ceph-dr-failover.sh
# Eseguire SOLO dopo decisione formale di disaster declaration

set -euo pipefail

POOL="rbd-prod"
SITE_B_PROXMOX="proxmox-b1.example.com"
LOG="/var/log/dr-failover-$(date +%Y%m%d-%H%M%S).log"

echo "=== DR FAILOVER START: $(date -Iseconds) ===" | tee "$LOG"

# Lista immagini da promuovere
IMAGES=$(rbd mirror pool status "$POOL" --format json | \
  jq -r '.images[] | select(.state == "up+replaying") | .name')

TOTAL=$(echo "$IMAGES" | wc -l)
echo "Immagini da promuovere: $TOTAL" | tee -a "$LOG"

PROMOTED=0
FAILED=0

for IMG in $IMAGES; do
    echo "Promoting: $POOL/$IMG" | tee -a "$LOG"
    if rbd mirror image promote --force "$POOL/$IMG" 2>>"$LOG"; then
        PROMOTED=$((PROMOTED + 1))
        echo "  OK" | tee -a "$LOG"
    else
        FAILED=$((FAILED + 1))
        echo "  FAILED" | tee -a "$LOG"
    fi
done

echo "" | tee -a "$LOG"
echo "=== RISULTATO ===" | tee -a "$LOG"
echo "Promoted: $PROMOTED / $TOTAL" | tee -a "$LOG"
echo "Failed:   $FAILED / $TOTAL" | tee -a "$LOG"
echo "=== DR FAILOVER END: $(date -Iseconds) ===" | tee -a "$LOG"

if [ "$FAILED" -gt 0 ]; then
    echo "ATTENZIONE: $FAILED immagini non promosse. Intervento manuale necessario."
    exit 1
fi
```

### PBS sync to remote PBS

**Configurazione completa PBS-to-PBS sync:**

```bash
# ============================================================
# Su PBS Site B (destination): configurare il remote
# ============================================================

# 1. Creare un API token su PBS Site A per l'autenticazione
# PBS Site A → GUI → Configuration → Access Control → API Token
# Oppure CLI:
proxmox-backup-manager user create sync-user@pbs \
  --comment "Account per sync DR"
proxmox-backup-manager acl update / SyncOperator \
  --auth-id sync-user@pbs
proxmox-backup-manager user generate-token sync-user@pbs sync-token

# 2. Su PBS Site B: aggiungere il remote
proxmox-backup-manager remote create site-a-remote \
  --host pbs-site-a.example.com \
  --port 8007 \
  --auth-id sync-user@pbs!sync-token \
  --password "<token-secret>" \
  --fingerprint "SHA256:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# 3. Verificare la connessione al remote
proxmox-backup-manager remote list

# 4. Creare un sync job (pull da Site A verso Site B)
proxmox-backup-manager sync-job create dr-pull-sync \
  --remote site-a-remote \
  --remote-store main \
  --store dr-store \
  --schedule "0/15 * * * *" \
  --remove-vanished true \
  --comment "DR sync ogni 15 minuti da Site A"

# 5. Verificare lo stato dei sync job
proxmox-backup-manager sync-job list
proxmox-backup-manager sync-job status dr-pull-sync

# 6. Eseguire manualmente un sync (per test)
proxmox-backup-manager sync-job run dr-pull-sync
```

**Monitoraggio sync job PBS:**

```bash
# Verificare che il sync sia aggiornato
proxmox-backup-client list \
  --repository pbs-site-b.example.com:dr-store \
  --output-format json | \
  jq '.[] | {backup_type, backup_id, last_backup: .["backup-time"]}'

# Controllare i log del sync job
journalctl -u proxmox-backup-proxy -g "sync-job" --since "1 hour ago"
```

---

## Network DR

### VPN site-to-site

Per traffico replication + management. WireGuard o IPsec. MTU 1380-1420 per WireGuard sopra Internet.

**Configurazione WireGuard site-to-site per DR:**

```bash
# ============================================================
# Site A: Proxmox node (gateway VPN)
# ============================================================

# 1. Installare WireGuard
apt install wireguard

# 2. Generare keypair
wg genkey | tee /etc/wireguard/site-a.key | wg pubkey > /etc/wireguard/site-a.pub
chmod 600 /etc/wireguard/site-a.key

# 3. Configurazione /etc/wireguard/wg-dr.conf
cat > /etc/wireguard/wg-dr.conf << 'EOF'
[Interface]
Address = 10.255.0.1/30
PrivateKey = <contenuto-site-a.key>
ListenPort = 51820
MTU = 1420
PostUp = iptables -A FORWARD -i wg-dr -j ACCEPT; iptables -t nat -A POSTROUTING -o vmbr0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg-dr -j ACCEPT; iptables -t nat -D POSTROUTING -o vmbr0 -j MASQUERADE

[Peer]
# Site B
PublicKey = <public-key-site-b>
AllowedIPs = 10.255.0.2/32, 10.20.0.0/16
Endpoint = site-b-public-ip:51820
PersistentKeepalive = 25
EOF

# 4. Abilitare e avviare
systemctl enable --now wg-quick@wg-dr

# 5. Verificare
wg show wg-dr
ping 10.255.0.2

# 6. Aggiungere route per la subnet DR
ip route add 10.20.0.0/16 via 10.255.0.2 dev wg-dr
```

**Throughput WireGuard tipico:**

```
Hardware           | Singola connessione | Parallelo (4 stream)
────────────────────────────────────────────────────────────────
1 core Xeon@3GHz   | ~2.5 Gbps          | ~4 Gbps
4 core EPYC@2.5GHz | ~4 Gbps            | ~8 Gbps
Con AES-NI + ChaCha | ~6 Gbps           | ~10 Gbps
```

### BGP / Anycast

Per IP pubblici migrabili: announce stesso IP da entrambi i siti, modificare BGP weight per controllare routing.

Requisiti:
- AS number proprio o IP block transferable (PI address space).
- Peering con ISP (multi-homed).
- BGP daemon: BIRD 2.x o FRRouting (FRR).

**Configurazione BIRD 2 per failover BGP:**

```
# /etc/bird/bird.conf — Site A
router id 192.0.2.1;

protocol bgp uplink_isp1 {
    local as 64512;
    neighbor 198.51.100.1 as 65001;
    
    ipv4 {
        import filter {
            accept;
        };
        export filter {
            # Annunciare il blocco PI
            if net = 203.0.113.0/24 then {
                bgp_local_pref = 200;   # Preferenza alta (primary)
                accept;
            }
            reject;
        };
    };
}

# In caso di failover, Site B annuncia con local_pref 100 (lower)
# → traffico va a Site A finche e UP
# → se Site A down, ISP converge su Site B in 30-90 secondi
```

### GeoDNS

Cloudflare Load Balancing, AWS Route 53 con health check, NS1: routing based su health check + geolocation. TTL 30-60s per fast failover.

**Configurazione Route 53 failover:**

```json
{
  "Comment": "DR failover record",
  "Changes": [
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "app.example.com",
        "Type": "A",
        "SetIdentifier": "primary-site-a",
        "Failover": "PRIMARY",
        "TTL": 60,
        "ResourceRecords": [{"Value": "203.0.113.10"}],
        "HealthCheckId": "hc-site-a-12345"
      }
    },
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "app.example.com",
        "Type": "A",
        "SetIdentifier": "secondary-site-b",
        "Failover": "SECONDARY",
        "TTL": 60,
        "ResourceRecords": [{"Value": "198.51.100.20"}]
      }
    }
  ]
}
```

**Configurazione Cloudflare Load Balancing con health check:**

```
Pool "primary":
  Origin: site-a-vip.example.com (203.0.113.10)
  Weight: 1
  Health Check: HTTPS GET /health → 200 OK
  Health Check interval: 30s
  Threshold: 2 failures → mark unhealthy

Pool "secondary":
  Origin: site-b-vip.example.com (198.51.100.20)
  Weight: 1
  Health Check: same

Steering Policy: failover (primary → secondary)
TTL: 30s
```

---

## WAN Replication e Ottimizzazione

### Bandwidth planning per WAN replication

```
Dati di replication da trasferire:
  Change rate giornaliero:  5% dello storage utile (tipico)
  Storage utile:            10 TB
  Dati da replicare/giorno: 500 GB

  Per finestra di replication continua (24h):
    500 GB / 86400 s = ~5.8 MB/s = ~46 Mbps sustained

  Per finestra notturna (8h):
    500 GB / 28800 s = ~17.4 MB/s = ~139 Mbps sustained

  Con overhead protocollo (SSH, ZFS stream headers):
    +10-15%

  Raccomandazione banda minima:
    Replication continua: 100 Mbps dedicated
    Replication notturna: 200 Mbps dedicated
```

### Ottimizzazione SSH per throughput elevato

```bash
# /root/.ssh/config — tuning per transfer DR
Host dr-site.example.com
    Ciphers aes256-gcm@openssh.com
    MACs hmac-sha2-256-etm@openssh.com
    Compression no
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ControlMaster auto
    ControlPath /tmp/ssh-%r@%h:%p
    ControlPersist 600
    # Disabilitare StrictHostKeyChecking solo per DR automation
    # (le chiavi sono gia verificate)
    StrictHostKeyChecking accept-new
```

### Compressione e deduplica per ZFS send

```bash
# ZFS send con compressione (riduce banda WAN)
zfs send -Ri @prev rpool/data@latest | \
  zstd -3 -T4 | \
  ssh dr-site "zstd -d | zfs receive -Fduv rpool/data"

# Misurare il rapporto di compressione
zfs send -nvi @prev rpool/data@latest 2>&1 | tail -5
# Mostra: estimated stream size, compressible ratio

# Per banda molto limitata (< 50 Mbps), usare mbuffer per smoothing
zfs send -Ri @prev rpool/data@latest | \
  mbuffer -s 128k -m 1G | \
  ssh dr-site "mbuffer -s 128k -m 1G | zfs receive -Fduv rpool/data"
```

---

## Ceph Stretch Cluster

### Architettura Ceph stretch cluster (metro-distance only)

**Requisito fondamentale: latenza < 2ms RTT fra i siti. Massimo 5ms con tuning aggressivo.**

```
Site A (data center 1)         Site B (data center 2)       Tiebreaker
+====================+         +====================+       +========+
| OSD × 6            |         | OSD × 6            |       | MON    |
| MON × 1            |         | MON × 1            |       | (solo  |
| MGR × 1            |◄─fiber─►| MGR × 1            |◄─────►| quorum)|
|                    |  <2ms   |                    |       +========+
+====================+         +====================+
                                                            Site C
Regola CRUSH:                                               (cloud VM
  root site-a                                                o terzo
    rack r1-a                                                sito)
      osd.0, osd.1, osd.2
  root site-b
    rack r1-b
      osd.3, osd.4, osd.5

Pool rule: min_size=4, size=4 (2 repliche per sito)
```

**Configurazione CRUSH map per stretch cluster:**

```bash
# 1. Definire bucket per i siti
ceph osd crush add-bucket site-a datacenter
ceph osd crush add-bucket site-b datacenter
ceph osd crush move site-a root=default
ceph osd crush move site-b root=default

# 2. Spostare gli OSD nei rispettivi siti
ceph osd crush move osd.0 datacenter=site-a
ceph osd crush move osd.1 datacenter=site-a
ceph osd crush move osd.2 datacenter=site-a
ceph osd crush move osd.3 datacenter=site-b
ceph osd crush move osd.4 datacenter=site-b
ceph osd crush move osd.5 datacenter=site-b

# 3. Creare CRUSH rule per stretch
ceph osd crush rule create-replicated stretch-rule default datacenter

# 4. Abilitare stretch mode
ceph mon enable_stretch_mode \
  --tiebreaker-mon=mon-site-c \
  --dividing-bucket=datacenter \
  --crush-rule=stretch-rule

# 5. Verificare
ceph osd crush rule dump stretch-rule
ceph mon dump | grep stretch
```

---

## DR drill

### Annual full drill

**Pianificazione drill (T-4 settimane prima):**

| Settimana | Attivita |
|---|---|
| T-4 | Kick-off meeting. Definire scope, team, obiettivi misurabili. |
| T-3 | Aggiornare il runbook DR. Verificare accessi, credenziali, chiavi. |
| T-2 | Pre-drill check: replication up-to-date, PBS sync OK, rete VPN stable. |
| T-1 | Comunicazione a tutti gli stakeholder. Conferma finestra weekend. |
| T-0 | Esecuzione drill (sabato-domenica). |
| T+1 | Post-mortem, report, aggiornamento documentazione. |

**Esecuzione drill dettagliata (1-2 giorni):**

```
DAY 1 — FAILOVER

T+0:00  Annuncio: "Questo e un DRILL, non un disastro reale."
        War room aperto (fisico o Teams/Zoom).
        Cutover Lead apre il runbook e inizia cronometro.

T+0:05  SIMULAZIONE: "Site A non raggiungibile."
        Spegnere VPN Site A → Site B (simulazione).
        NON spegnere realmente Site A in produzione (per drill).
        Alternativa: bloccare accesso network a Site A con firewall rule.

T+0:10  Detection: monitoring rileva outage.
        Verificare che gli alert partano correttamente.
        Tempo di detection: _____ minuti (misurare).

T+0:15  Decision: Cutover Lead dichiara disaster.
        Sponsor conferma.
        Comms Lead notifica stakeholder: "Drill in corso."

T+0:20  FAILOVER STORAGE:
        - Ceph: promote RBD images su Site B
        - ZFS: verificare ultimo snapshot disponibile
        - PBS: verificare ultimo backup disponibile
        Tempo storage failover: _____ minuti.

T+0:40  FAILOVER NETWORK:
        - GeoDNS: switch health check
        - VPN: attivare routing verso Site B
        - Verificare connettivita endpoint
        Tempo network failover: _____ minuti.

T+0:50  BOOT VM SU SITE B:
        Ordine: DNS/AD → DB → App → Web → Monitoring
        Per ogni VM: boot + basic health check (ping + porta)
        Tempo boot: _____ minuti.

T+1:30  SMOKE TEST:
        - Login utenti test
        - Transazione end-to-end
        - API health check
        - Verifica dati (ultimo record pre-failover)
        Risultato: PASS / FAIL per ogni test.

T+2:00  SOAK TEST (4-8h):
        Lasciare le VM in esecuzione su Site B.
        Monitorare metriche: CPU, RAM, I/O, latenza app.
        Eseguire transazioni sintetiche continue.

T+8:00  END OF DAY 1:
        Riepilogo: RTO misurato = _____ minuti.
        RPO misurato = _____ minuti.
        Issue rilevati: _____.

DAY 2 — FAILBACK

T+0:00  FAILBACK:
        Ripristinare Site A come primario.
        Replicare delta da Site B → Site A.
        Tempo failback: _____ minuti.

T+2:00  VALIDAZIONE POST-FAILBACK:
        Verificare che Site A sia operativo.
        Verificare che la replication verso Site B sia ripartita.
        Eseguire smoke test su Site A.

T+4:00  POST-MORTEM:
        Riunione con tutto il team drill.
        Template: vedi sezione "DR Drill Report Template" sotto.

T+5:00  CLEANUP:
        Rimuovere regole firewall di simulazione.
        Verificare che tutto sia tornato a stato normale.
        Spegnere VM di test su Site B.
```

### Quarterly partial drill

Esecuzione (4-8h):
1. Failover *singola* applicazione critica (es. CRM) a Site B.
2. Validate.
3. Failback.

Costo basso, esercizio frequente del processo.

**Checklist partial drill:**

```
PARTIAL DR DRILL — CHECKLIST
═════════════════════════════

App target: _______________
VM coinvolte: _______________
Owner app: _______________

PRE-DRILL:
□ Replication storage aggiornata (< 15 min lag)
□ VM DR-ready su Site B (config presente)
□ Rete VPN funzionante
□ DNS TTL ridotto a 60s (almeno 2h prima)
□ Stakeholder notificati
□ Finestra di manutenzione comunicata

DRILL EXECUTION:
□ T+0: Avvio drill
□ T+5: Storage failover completato
□ T+10: VM avviata su Site B
□ T+15: Smoke test passato
□ T+30: DNS switchover
□ T+60: Traffico reale su Site B per 1h
□ T+120: Failback avviato
□ T+150: Site A ripristinato
□ T+180: Replication ripartita

POST-DRILL:
□ RTO misurato: _____ min
□ RPO misurato: _____ min
□ Issue trovati: _____
□ Runbook aggiornato: □ Si □ No
□ Report archiviato: □ Si □ No
```

### DR Drill Report Template

```
DR DRILL REPORT
═══════════════

Data drill:          _______________
Tipo:                □ Full  □ Partial
App/scope:           _______________
Partecipanti:        _______________

METRICHE MISURATE:
  RTO target:        _____ min
  RTO misurato:      _____ min
  RTO delta:         _____ min (positivo = peggio del target)
  RPO target:        _____ min
  RPO misurato:      _____ min (ultimo dato pre-disaster)
  
TIMELINE FAILOVER:
  Detection time:    _____ min
  Decision time:     _____ min
  Storage failover:  _____ min
  Network failover:  _____ min
  VM boot + test:    _____ min
  Total RTO:         _____ min

ISSUE RILEVATI:
  #  Descrizione               Severita   Stato    Owner   Scadenza
  1  _________________________  CRITICAL   OPEN     ___     ___
  2  _________________________  HIGH       OPEN     ___     ___
  3  _________________________  MEDIUM     OPEN     ___     ___

LEZIONI APPRESE:
  1. _______________________________________________________________
  2. _______________________________________________________________
  3. _______________________________________________________________

AZIONI CORRETTIVE:
  #  Azione                    Owner    Scadenza   Stato
  1  _________________________  ___      ___        ___
  2  _________________________  ___      ___        ___

RUNBOOK UPDATE NECESSARIO: □ Si □ No
PROSSIMO DRILL PIANIFICATO: _______________

Firma Cutover Lead: _______________  Data: _______________
Firma Sponsor:      _______________  Data: _______________
```

---

## Automated DR Testing

### Concetto di DR test automatizzato

Test DR automatizzati integrati nella pipeline CI/CD o schedulati come cron job permettono di verificare la salute della replication e la capacita di failover senza intervento umano.

```bash
#!/bin/bash
# /usr/local/bin/dr-auto-test.sh
# Eseguire settimanalmente via cron
# 0 3 * * 0 /usr/local/bin/dr-auto-test.sh

set -euo pipefail

REPORT_FILE="/var/log/dr-auto-test/report-$(date +%Y%m%d).json"
mkdir -p "$(dirname "$REPORT_FILE")"

TESTS_PASSED=0
TESTS_FAILED=0
RESULTS=()

# === TEST 1: Replication lag ===
check_replication_lag() {
    local MAX_LAG=1800  # 30 minuti in secondi
    local LAG
    
    # Per ZFS
    LOCAL_SNAP_TS=$(zfs list -H -t snapshot -o creation -s creation rpool/data | \
      grep "dr-" | tail -1 | xargs -I{} date -d "{}" +%s)
    REMOTE_SNAP_TS=$(ssh dr-site "zfs list -H -t snapshot -o creation -s creation rpool/data | \
      grep 'dr-' | tail -1" | xargs -I{} date -d "{}" +%s)
    
    LAG=$((LOCAL_SNAP_TS - REMOTE_SNAP_TS))
    
    if [ "$LAG" -lt "$MAX_LAG" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        RESULTS+=("{\"test\": \"replication_lag\", \"status\": \"PASS\", \"lag_seconds\": $LAG}")
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        RESULTS+=("{\"test\": \"replication_lag\", \"status\": \"FAIL\", \"lag_seconds\": $LAG, \"max\": $MAX_LAG}")
    fi
}

# === TEST 2: PBS sync job status ===
check_pbs_sync() {
    local LAST_SYNC
    LAST_SYNC=$(ssh pbs-dr "proxmox-backup-manager sync-job status dr-pull-sync --output-format json" | \
      jq -r '.last_run_state')
    
    if [ "$LAST_SYNC" = "ok" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        RESULTS+=("{\"test\": \"pbs_sync\", \"status\": \"PASS\"}")
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        RESULTS+=("{\"test\": \"pbs_sync\", \"status\": \"FAIL\", \"last_state\": \"$LAST_SYNC\"}")
    fi
}

# === TEST 3: VPN connectivity ===
check_vpn() {
    if ping -c 3 -W 5 10.255.0.2 > /dev/null 2>&1; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        RESULTS+=("{\"test\": \"vpn_connectivity\", \"status\": \"PASS\"}")
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        RESULTS+=("{\"test\": \"vpn_connectivity\", \"status\": \"FAIL\"}")
    fi
}

# === TEST 4: Site B Proxmox cluster health ===
check_site_b_cluster() {
    local STATUS
    STATUS=$(ssh dr-node-b1 "pvecm status 2>/dev/null | grep -c 'Quorum:.*Yes'" || echo "0")
    
    if [ "$STATUS" = "1" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        RESULTS+=("{\"test\": \"site_b_cluster\", \"status\": \"PASS\"}")
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        RESULTS+=("{\"test\": \"site_b_cluster\", \"status\": \"FAIL\"}")
    fi
}

# === TEST 5: DNS failover readiness ===
check_dns_failover() {
    local PRIMARY_IP="203.0.113.10"
    local RESOLVED
    RESOLVED=$(dig +short app.example.com @8.8.8.8)
    
    if [ "$RESOLVED" = "$PRIMARY_IP" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        RESULTS+=("{\"test\": \"dns_primary\", \"status\": \"PASS\", \"resolved\": \"$RESOLVED\"}")
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        RESULTS+=("{\"test\": \"dns_primary\", \"status\": \"FAIL\", \"resolved\": \"$RESOLVED\"}")
    fi
}

# Eseguire tutti i test
check_replication_lag
check_pbs_sync
check_vpn
check_site_b_cluster
check_dns_failover

# Generare report JSON
cat > "$REPORT_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "tests_total": $((TESTS_PASSED + TESTS_FAILED)),
  "tests_passed": $TESTS_PASSED,
  "tests_failed": $TESTS_FAILED,
  "overall_status": "$([ $TESTS_FAILED -eq 0 ] && echo 'PASS' || echo 'FAIL')",
  "results": [$(IFS=','; echo "${RESULTS[*]}")]
}
EOF

# Alert se fallito
if [ "$TESTS_FAILED" -gt 0 ]; then
    # Integrare con il vostro sistema di alerting
    # Esempio: Slack webhook
    curl -s -X POST "$SLACK_WEBHOOK_URL" \
      -H 'Content-type: application/json' \
      -d "{\"text\": \"DR Auto-Test FAILED: $TESTS_FAILED/$((TESTS_PASSED + TESTS_FAILED)) tests failed. Report: $REPORT_FILE\"}" \
      || true
fi

echo "DR Auto-Test completato: $TESTS_PASSED passed, $TESTS_FAILED failed"
```

---

## Compliance

### NIS2 directive (UE 2022/2555, recepimento 2024-10)

Requisiti chiave:
- Servizi essenziali (energia, salute, finanza, infrastruttura digitale): documentare BCP.
- Incident reporting: 24h early warning, 72h initial report.
- DR drill annuale documentato.
- Penalty: fino a 10M€ o 2% del fatturato.

**Mappatura NIS2 → feature Proxmox:**

| Requisito NIS2 | Feature Proxmox | Gap / Note |
|---|---|---|
| Business continuity plan | Cluster HA, PBS, ZFS replication | Documentare il BCP separatamente (non e una feature software) |
| Incident detection | Proxmox alerts + Zabbix/Grafana | Integrare con SIEM per compliance |
| DR testing | DR drill manuale + automated tests | Documentare risultati per audit |
| Encryption at rest | LUKS su disco, Ceph encryption | Abilitare encryption per dati sensibili |
| Encryption in transit | TLS per GUI/API, IPsec/WG per replication | Verificare che TUTTI i flussi siano cifrati |
| Access control | PVE RBAC, 2FA TOTP | Integrare con LDAP/AD per audit trail |
| Audit logging | Proxmox task log, syslog | Centralizzare con log server dedicato |
| Supply chain security | Repository ufficiali Proxmox | Verificare GPG signatures degli aggiornamenti |

**Checklist NIS2 per infrastruttura Proxmox:**

```
NIS2 COMPLIANCE CHECKLIST — PROXMOX DR
═══════════════════════════════════════

GOVERNANCE:
□ BCP documentato e approvato dal management
□ DR plan documentato con RTO/RPO per ogni servizio
□ Responsabile BCP nominato
□ Revisione annuale del BCP

TECHNICAL:
□ Replication storage configurata e monitorata
□ Backup offsite (PBS sync) operativo
□ Encryption at rest abilitata (LUKS/dm-crypt)
□ Encryption in transit per tutti i flussi di replication
□ 2FA abilitato per tutti gli admin
□ RBAC configurato (principio del least privilege)
□ Audit log centralizzato e conservato >= 12 mesi
□ Patching regolare (< 30 giorni per CVE critiche)

TESTING:
□ DR drill annuale eseguito e documentato
□ DR drill results: RTO/RPO entro target
□ Penetration test annuale dell'infrastruttura
□ Vulnerability scan trimestrale

INCIDENT RESPONSE:
□ Processo di incident response documentato
□ Contact list aggiornata (24/7)
□ Template per notifica autorita (24h + 72h)
□ Post-mortem template e processo
```

### DORA (UE 2022/2554, applicabile 2025-01-17)

Per servizi finanziari:
- ICT third-party risk management.
- DR + cyber resilience testing (annuale, esteso a critical providers).
- Incident classification + reporting.

**Requisiti DORA specifici per DR:**

| Articolo DORA | Requisito | Come soddisfarlo con Proxmox |
|---|---|---|
| Art. 11 | ICT business continuity management | BCP + DR plan + drill annuale |
| Art. 12 | DR policies | Documentazione RTO/RPO per servizio |
| Art. 23 | Major incident reporting | 4h initial notification, 72h intermediate, 1 month final |
| Art. 24 | Threat-led penetration testing (TLPT) | Pentest annuale infrastruttura DR |
| Art. 28 | ICT third-party risk | Contratto Proxmox (subscription) con SLA |
| Art. 26 | Digital operational resilience testing | DR drill + failover test + recovery test |

### EBA Guidelines (per banche)

Requisiti specifici BCM/DR per istituzioni finanziarie EU. In aggiunta a DORA:
- Maximum tolerable downtime (MTD) per ogni servizio critico.
- Recovery testing almeno annuale, con scenari multi-failure.
- Documentazione delle alternative (es. procedure manuali in caso di IT totalmente non disponibile).

---

## Failover playbook

```
T+0:   Detection del disastro Site A.
       Trigger: monitoring health check fallito per >= 3 min consecutivi.
       OPPURE: comunicazione diretta (chiamata dal NOC Site A, ISP, ecc.).
       
T+5:   Decision: declare disaster (Sponsor + Cutover Lead).
       Criteri:
         - Site A irraggiungibile da >= 2 percorsi di rete indipendenti
         - OPPURE conferma fisica di evento (incendio, alluvione, ecc.)
         - OPPURE outage ISP/DC confermato con ETA recovery > RTO target

T+10:  Comms Lead: notify stakeholders. War room aperto.
       Template:
         "DISASTER DECLARED. Site A non operativo.
          DR failover in corso. ETA restore: <RTO target>.
          War room: <link/room>. Prossimo update: T+30."

T+15:  Network Lead:
       - GeoDNS: rimuovere Site A dal pool (o health check failover auto)
       - BGP: withdraw announcement da Site A (se BGP)
       - VPN: verificare routing verso Site B
       
T+20:  Storage Lead:
       - Ceph: rbd mirror image promote --force per tutte le immagini DR
       - ZFS: verificare ultimo snapshot disponibile, montare
       - PBS: se necessario, restore VM da backup

T+35:  App Lead:
       - Boot VM su Site B in ordine:
         1. DNS/AD (5 min)
         2. Database (5 min + recovery time)
         3. Application servers (5 min)
         4. Web servers / load balancers (2 min)
         5. Monitoring (2 min)
       
T+45:  Smoke test critical paths:
       □ DNS resolution funzionante
       □ Login utente test
       □ Transazione end-to-end
       □ API health check
       □ Dati verificati (ultimo record = RPO accettabile)

T+60:  Decision: open production traffic.
       GO criteria: tutti smoke test PASS.
       NO-GO: rollback investigation.

T+90:  Open production traffic.
       Comms Lead: "Servizi ripristinati su Site B."

T+120: First-hour validation. Stable? Continue. Else escalate.
       Metriche: latenza, error rate, throughput vs baseline.
```

## Failback playbook

```
PREREQUISITO: Site A ripristinato e validato.

T+0:   Site A restored. Validate health:
       □ Hardware funzionante
       □ Proxmox cluster operativo (pvecm status)
       □ Storage (Ceph/ZFS) healthy
       □ Network connettivita OK
       □ Monitoring attivo

T+1h:  Avviare replication inversa: Site B → Site A.
       # Per Ceph RBD mirror:
       rbd mirror image demote rbd-prod/<image>  # su Site B
       rbd mirror image promote rbd-prod/<image> # su Site A
       # Attendere sync completa

T+4h:  Verificare che la replication abbia sincronizzato tutti i delta.
       rbd mirror pool status rbd-prod --verbose
       # Tutti gli image devono essere in stato "up+replaying" su Site B

T+24h: Scheduling failback in maintenance window.
       Comunicare a stakeholder: finestra di manutenzione per failback.
       TTL DNS ridotto a 60s.

T+M:   (Maintenance window) Esecuzione failback:
       Procedura = reverse del failover playbook:
       1. Drain traffic da Site B (load balancer, GeoDNS)
       2. Stop VM su Site B (graceful)
       3. Final sync delta
       4. Start VM su Site A
       5. Smoke test
       6. DNS cutover verso Site A
       7. Validazione

T+M+4h: Riattivare replication normale Site A → Site B.
         Verificare con monitoring che tutto sia stabile.

T+M+7d: Post-failback report. Documentare lezioni apprese.
```

---

## Runbook Templates

### Runbook DR Failover — Template compilabile

```
RUNBOOK: DR FAILOVER
═══════════════════════

Versione: 1.0
Ultima revisione: _______________
Approvato da: _______________

1. SCOPE
   Questo runbook copre il failover di produzione da Site A a Site B
   per i seguenti servizi: _______________

2. PREREQUISITI
   □ VPN Site A ↔ Site B funzionante
   □ Replication aggiornata (lag < ___ min)
   □ Site B cluster healthy
   □ DNS TTL ridotto a 60s (almeno 2h prima, se pianificato)
   □ Credenziali DR verificate

3. CONTATTI
   Cutover Lead:     _______________ Tel: _______________
   Network Lead:     _______________ Tel: _______________
   Storage Lead:     _______________ Tel: _______________
   App Lead:         _______________ Tel: _______________
   Comms Lead:       _______________ Tel: _______________
   Sponsor:          _______________ Tel: _______________
   ISP primario:     _______________ Tel: _______________
   ISP backup:       _______________ Tel: _______________

4. STEP-BY-STEP
   (compilare con i comandi specifici del proprio ambiente)

   Step 1: Declare disaster
   Comando: _______________
   Verifica: _______________
   Tempo stimato: ___ min

   Step 2: Network failover
   Comando: _______________
   Verifica: _______________
   Tempo stimato: ___ min

   Step 3: Storage failover
   Comando: _______________
   Verifica: _______________
   Tempo stimato: ___ min

   Step 4: VM boot
   Ordine: _______________
   Comandi: _______________
   Verifica: _______________
   Tempo stimato: ___ min

   Step 5: Smoke test
   Test: _______________
   Criterio PASS: _______________
   Criterio FAIL → azione: _______________

   Step 6: Open traffic
   Comando: _______________
   Verifica: _______________

5. ROLLBACK (se failover fallisce)
   _______________________________________________

6. POST-FAILOVER MONITORING
   Dashboard: _______________
   Alert critici da verificare: _______________
   On-call 24h: _______________
```

---

## DNS Failover

### Strategie DNS per DR

| Strategia | TTL | Failover time | Automazione | Costo |
|---|---|---|---|---|
| Manuale (cambio record A) | 300s | 5-15 min + TTL | Nessuna | Gratuito |
| GeoDNS health check | 30-60s | 30-90 sec | Completa | Provider fee |
| BGP Anycast | N/A (layer 3) | 30-90 sec | Completa | AS number + peering |
| GSLB (load balancer globale) | 30s | 15-60 sec | Completa | GSLB license |

### Riduzione TTL pre-DR (se pianificato)

```bash
# 48h prima del DR drill o cutover pianificato:
# Ridurre TTL da 3600s a 60s

# Cloudflare API
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"type":"A","name":"app.example.com","content":"203.0.113.10","ttl":60}'

# Verificare la propagazione
dig +short app.example.com @8.8.8.8
dig +short app.example.com @1.1.1.1
# Il TTL nei resolver publici si ridurra gradualmente fino a 60s
```

### Health check per DNS automatico

```bash
# Script health check endpoint (da deployare su Site A e Site B)
# Servito su porta 8080 come endpoint /health

#!/bin/bash
# /usr/local/bin/dr-health-endpoint.sh
# Eseguire via systemd o cron + simple HTTP server

# Controlla la salute locale
check_health() {
    # 1. Proxmox cluster OK?
    pvecm status 2>/dev/null | grep -q "Quorum:.*Yes" || return 1
    
    # 2. Storage OK?
    ceph -s 2>/dev/null | grep -q "HEALTH_OK\|HEALTH_WARN" || \
    zpool status rpool 2>/dev/null | grep -q "state: ONLINE" || return 1
    
    # 3. VM critiche running?
    qm status 100 2>/dev/null | grep -q "running" || return 1
    qm status 101 2>/dev/null | grep -q "running" || return 1
    
    return 0
}

if check_health; then
    echo "HTTP/1.1 200 OK"
    echo "Content-Type: text/plain"
    echo ""
    echo "healthy"
else
    echo "HTTP/1.1 503 Service Unavailable"
    echo "Content-Type: text/plain"
    echo ""
    echo "unhealthy"
fi
```

---

## Cost analysis

| Topologia | HW cost vs Site A | Network cost | Operational cost | Total relative |
|---|---|---|---|---|
| Cold passive | 60-80% | 1x VPN | low (drill 2-4h/q) | 1.7x prod |
| Warm passive | 100% | 1x VPN + monitoring | medium | 2.2x prod |
| Active/active | 100% | 1x dedicated low-latency | high (skill, ops) | 2.5x prod |
| Stretched | n/a | dark fiber | very high | 3x prod |

### Analisi TCO dettagliata (3 anni)

```
SCENARIO: 30 VM produzione, 15 TB storage

═══ OPZIONE 1: COLD PASSIVE (PBS sync) ═══

Hardware Site B:
  3 nodi Proxmox (spec ridotta):    €30,000
  Storage NVMe (15 TB raw):         €12,000
  Networking (switch, NIC):         €3,000
  Subtotale HW:                     €45,000

Ongoing annuale:
  Connettivita VPN (100 Mbps):      €3,600/anno
  Proxmox subscription:             €3,000/anno
  Energia + cooling:                €6,000/anno
  DR drill (2gg/anno team):         €4,000/anno
  Subtotale annuale:                €16,600/anno

TCO 3 anni:                        €45,000 + (€16,600 × 3) = €94,800

═══ OPZIONE 2: WARM PASSIVE (Ceph mirror) ═══

Hardware Site B:
  3 nodi Proxmox (full spec):       €60,000
  Ceph OSD (45 TB raw, 3x repl):   €25,000
  Networking (25 GbE + switch):     €8,000
  Subtotale HW:                     €93,000

Ongoing annuale:
  Connettivita dedicata (1 Gbps):   €12,000/anno
  Proxmox subscription:             €6,000/anno
  Energia + cooling:                €12,000/anno
  Operational overhead:             €10,000/anno
  DR drill:                         €4,000/anno
  Subtotale annuale:                €44,000/anno

TCO 3 anni:                        €93,000 + (€44,000 × 3) = €225,000

═══ OPZIONE 3: ACTIVE/ACTIVE (Ceph sync) ═══

Hardware Site B:
  3 nodi Proxmox (full spec):       €60,000
  Ceph OSD (45 TB raw):            €25,000
  Networking (100 GbE + switch):    €20,000
  Subtotale HW:                     €105,000

Ongoing annuale:
  Dark fiber / DWDM (10 Gbps):     €48,000/anno
  Proxmox subscription:             €6,000/anno
  Energia + cooling:                €15,000/anno
  Operational overhead:             €25,000/anno
  Subtotale annuale:                €94,000/anno

TCO 3 anni:                        €105,000 + (€94,000 × 3) = €387,000
```

### Formula per giustificare l'investimento DR

```
ROI_DR = (Costo_Downtime_Annuale × Probabilita_Disaster) / Costo_DR_Annuale

Dove:
  Costo_Downtime_Annuale = RTO_senza_DR × Costo_Per_Ora_Downtime
  Probabilita_Disaster   = 0.05 - 0.15 per anno (a seconda del risk profile)
  Costo_DR_Annuale       = TCO_DR / 3

Esempio:
  Senza DR: RTO = 72h, costo downtime = €5,000/h
  Costo downtime potenziale = 72 × €5,000 = €360,000
  Con probabilita 10%: Expected Loss = €36,000/anno
  
  Con DR (cold passive): RTO = 8h
  Costo downtime residuo = 8 × €5,000 × 10% = €4,000/anno
  Risparmio = €36,000 - €4,000 = €32,000/anno
  Costo DR annuale = €94,800 / 3 = €31,600/anno
  
  ROI = €32,000 / €31,600 = 1.01x (breakeven in 3 anni)
  
  Per aziende con costo downtime > €10,000/h: ROI significativamente positivo.
```

---

## Troubleshooting

### Problema: Ceph RBD mirror bloccato in stato "unknown"
**Sintomi**: `rbd mirror image status` mostra stato "up+unknown" o "up+error" su Site B. La replication non avanza.
**Causa**: Connettivita di rete intermittente tra i cluster Ceph, credenziali di peering scadute, clock skew tra i siti, o pool con configurazione incompatibile.
**Soluzione**:
```bash
# 1. Verificare connettivita
ceph --cluster site-b ping mon.site-a

# 2. Verificare credenziali
ceph auth get client.rbd-mirror-peer
rbd mirror pool info rbd-prod

# 3. Verificare clock sync
chronyc tracking  # su entrambi i siti

# 4. Riavviare il daemon rbd-mirror
systemctl restart ceph-rbd-mirror@admin.service
journalctl -u ceph-rbd-mirror@admin.service -f

# 5. Se persistente: rimuovere e ricreare il peering
rbd mirror pool peer remove rbd-prod <peer-uuid>
rbd mirror pool peer bootstrap import --site-name site-b \
  --direction rx-only rbd-prod /tmp/bootstrap-token
```
**Prevenzione**: Monitorare lo stato del mirror con alert automatici. Verificare NTP sync settimanalmente. Testare la connettivita peering mensilmente.

### Problema: ZFS send/recv fallisce a meta
**Sintomi**: Lo stream ZFS si interrompe durante il trasferimento con errore "broken pipe" o "connection reset". Lo snapshot incrementale non puo ripartire da dove si era fermato.
**Causa**: Connessione SSH instabile su WAN, timeout SSH, buffer di rete insufficiente, out-of-space su destinazione.
**Soluzione**:
```bash
# 1. Verificare lo spazio su destinazione
ssh dr-site "zfs list -o space rpool/data"

# 2. Usare resume token (ZFS 2.0+)
# Se il receive era interrotto, ZFS salva un resume token
ssh dr-site "zfs get receive_resume_token rpool/data"
# Se presente:
zfs send -t <resume-token> | ssh dr-site "zfs receive -s rpool/data"

# 3. Per connessioni instabili, usare mbuffer
zfs send -Ri @prev rpool/data@latest | \
  mbuffer -s 128k -m 1G -O dr-site:9090 &
# Su Site B:
mbuffer -s 128k -m 1G -I 9090 | zfs receive -Fduv rpool/data

# 4. Aumentare buffer SSH
# /etc/ssh/sshd_config su Site B:
# MaxStartups 10:30:60
# TCPKeepAlive yes
```
**Prevenzione**: Usare resume send/recv per tutti i trasferimenti WAN. Monitorare la connettivita VPN con ping continuo. Dimensionare la banda VPN per il trasferimento.

### Problema: GeoDNS failover non avviene automaticamente
**Sintomi**: Site A e down ma il DNS continua a risolvere all'IP di Site A. Gli utenti non vengono reindirizzati a Site B.
**Causa**: Health check non configurato o non funzionante, TTL DNS troppo alto ancora in cache, health check endpoint non raggiungibile dal provider GeoDNS, firewall che blocca il health check.
**Soluzione**:
```bash
# 1. Verificare la configurazione dell'health check sul provider
# Cloudflare: Dashboard → Load Balancing → Health Checks
# Route 53: Console → Health Checks

# 2. Verificare che l'endpoint health check sia raggiungibile
curl -v https://app.example.com/health

# 3. Verificare TTL corrente
dig +ttlid app.example.com @8.8.8.8

# 4. Se il TTL e alto, forzare il cambio manuale
# e ridurre il TTL per il futuro
```
**Prevenzione**: Testare il failover DNS almeno trimestralmente. Mantenere TTL a 60s per record critici. Monitorare gli health check dal lato provider.

### Problema: Failover riuscito ma applicazione non funziona su Site B
**Sintomi**: Le VM sono avviate su Site B, la rete funziona, ma l'applicazione restituisce errori. Database OK, ma applicazione in errore.
**Causa**: Configurazioni hardcoded (IP, hostname), certificati SSL scaduti o legati a hostname specifico, licenze software legate a hardware/MAC, dipendenze esterne non raggiungibili da Site B, DNS interno non aggiornato.
**Soluzione**:
```bash
# 1. Verificare risoluzione DNS interna
nslookup app-server.internal.local

# 2. Verificare certificati
openssl s_client -connect app.example.com:443 2>/dev/null | openssl x509 -noout -dates

# 3. Verificare connettivita alle dipendenze esterne
curl -v https://api-esterna.example.com/health

# 4. Verificare le configurazioni dell'applicazione
grep -r "site-a\|10\.10\." /opt/app/config/
```
**Prevenzione**: Eliminare configurazioni hardcoded. Usare hostname DNS ovunque. Gestire certificati wildcard o SAN che includono entrambi i siti. Documentare tutte le dipendenze esterne nel DR plan.

### Problema: PBS sync job fallisce silenziosamente
**Sintomi**: Il sync job PBS non produce errori visibili ma i backup su Site B sono vecchi di giorni. Nessun alert ricevuto.
**Causa**: Il sync job e schedulato ma il processo fallisce internamente (errore di rete, spazio insufficiente, timeout) senza generare un alert esterno.
**Soluzione**:
```bash
# 1. Controllare log PBS
journalctl -u proxmox-backup-proxy --since "24 hours ago" | grep -i "sync\|error\|fail"

# 2. Verificare stato dei sync job
proxmox-backup-manager sync-job list
proxmox-backup-manager sync-job status dr-pull-sync

# 3. Eseguire manualmente
proxmox-backup-manager sync-job run dr-pull-sync 2>&1

# 4. Verificare spazio su datastore
proxmox-backup-manager datastore list
```
**Prevenzione**: Implementare monitoring esterno per l'eta del backup piu recente. Alert se ultimo sync > 2× interval. Testare restore mensilmente.

### Problema: Split-brain dopo stretched cluster partition
**Sintomi**: Entrambi i siti pensano di essere il primario. VM in esecuzione su entrambi i siti con lo stesso IP. Corruzione dati possibile.
**Causa**: Partizione di rete tra i due siti senza tiebreaker funzionante. Corosync perde il quorum su un lato ma l'altro continua a operare.
**Soluzione**:
```bash
# EMERGENZA: identificare il sito con i dati piu recenti
# Confrontare timestamp di ultimo write su storage

# 1. Su entrambi i siti: fermare TUTTO
systemctl stop pve-cluster pveproxy pvedaemon corosync

# 2. Identificare il sito primario (dati piu recenti)
# Confrontare transaction ID Ceph o ZFS snapshot timestamp

# 3. Sul sito secondario: rimuovere dal cluster
pvecm delnode <nome-nodo-secondario>

# 4. Sul sito primario: ripristinare il quorum
pvecm expected <numero-nodi-rimasti>

# 5. Ricostruire il sito secondario da zero come DR site separato
```
**Prevenzione**: NON usare stretched cluster per distanze > 30 km. Sempre avere un tiebreaker funzionante. Preferire cluster separati + replication asincrona.

### Problema: Replication lag cresce progressivamente
**Sintomi**: Il lag di replication (ZFS o Ceph) aumenta costantemente nel tempo. Da 5 minuti a 30 minuti in una settimana.
**Causa**: Crescita del change rate dei dati, banda WAN insufficiente, degradazione delle performance storage, coda di sync job su PBS.
**Soluzione**:
```bash
# 1. Misurare il change rate effettivo
zfs get -p written rpool/data  # bytes scritti dall'ultimo snapshot
# Se il written tra snapshot supera la banda disponibile nel periodo, il lag crescera

# 2. Calcolare se la banda e sufficiente
# Change rate: 500 MB ogni 15 min
# Banda disponibile: 100 Mbps = 12.5 MB/s
# Tempo per trasferire: 500 MB / 12.5 MB/s = 40 sec → OK
# Se change rate cresce a 2 GB: 2000 / 12.5 = 160 sec → problema se > 900 sec (15 min)

# 3. Aumentare la banda o ridurre la frequenza
# Oppure: abilitare compressione nel send
zfs send -c -Ri @prev rpool/data@latest | ssh ...
```
**Prevenzione**: Monitorare trend del change rate. Dimensionare la banda WAN per 3× il change rate medio. Alert se lag > 2× l'intervallo di snapshot.

---

## Esercizi

1. **Concettuale — DR design.** Per ognuno: scegli topologia + giustifica. (a) E-commerce small (orders/day=500, 5 VM); (b) hospital EMR (zero data loss accettato, RTO 5min); (c) banking core (DORA compliance); (d) startup SaaS B2B (10K MAU); (e) GovTech servizio essenziale NIS2.

2. **Lab — ZFS replication tra due Proxmox.** Setup 2 nodi Proxmox in lab; configura ZFS send/recv tra di loro ogni 15 min; simula failover (spegni Site A, monta replica su Site B); misura RTO. Documenta.

3. **Stretch — DR drill simulato.** Per un cluster di test, esegui un full DR drill: declare, failover, validation, failback. Misura tutti i tempi, identifica gap nel runbook, aggiorna documentazione.

4. **Lab — Ceph RBD mirror setup.** Su due cluster Ceph separati (anche single-node), configurare RBD mirroring in modalita snapshot con intervallo 5 minuti. Scrivere dati sul primario, attendere la replica, promuovere il secondario, verificare che i dati siano presenti.

5. **Scenario — Calcolo banda WAN.** Un'azienda ha 50 VM con change rate giornaliero totale di 200 GB. Calcolare la banda minima necessaria per: (a) replication continua 24h, (b) replication notturna 8h, (c) replication ogni 15 minuti. Includere overhead protocollo 15%.

6. **Lab — PBS sync cross-site.** Configurare due PBS server (anche sullo stesso host con porte diverse). Creare un sync job che replica da PBS-A a PBS-B ogni 15 minuti. Simulare un restore dal PBS-B e misurare il tempo.

7. **Scenario — TCO comparison.** Per un parco di 20 VM, 5 TB storage, RTO target 2h, RPO target 30min: calcolare il TCO triennale delle opzioni cold passive, warm passive e active/active. Quale raccomandare? Giustificare.

8. **Stretch — Automated DR test script.** Scrivere uno script Bash che verifica: (a) replication lag < 30 min, (b) VPN up, (c) Site B cluster healthy, (d) PBS sync OK, (e) DNS failover configurato. Output: JSON report con PASS/FAIL per ogni test. Integrare con Zabbix o Prometheus per alerting.

## Auto-valutazione

1. Differenza fra HA e DR.
2. Quando active/passive cold e accettabile e quando no?
3. Stretched cluster: vincoli e perche e sconsigliato?
4. Ceph RBD mirror modalita snapshot vs journal: differenza.
5. NIS2: quando e applicabile alla tua organizzazione?
6. DR drill annuale: cosa va misurato e documentato?
7. GeoDNS vs BGP Anycast: quando usare uno o l'altro.
8. Come si calcola il RPO worst-case per ZFS send/recv con cron ogni 15 min?
9. Quali sono i requisiti di latenza per Ceph stretched cluster?
10. DORA Art. 11: cosa richiede per il business continuity management?
11. Come si promuove un'immagine RBD mirror in caso di disaster con Site A irraggiungibile?
12. Quale e il costo relativo (multiplier) tipico per ciascuna topologia DR?
13. Come si verifica che la replication PBS sia aggiornata?
14. Perche il failback richiede una maintenance window pianificata e non si fa immediatamente?
15. Quali test automatizzati si possono eseguire settimanalmente per verificare la readiness DR?

## Approfondimenti — note del 2026-04-27

> **Approfondimento — pve-zsync vs ZFS send manuale.** Proxmox VE include `pve-zsync`, un tool integrato per replication ZFS fra nodi dello stesso cluster. Per replication cross-cluster (DR multi-site), `pve-zsync` non e supportato: bisogna usare `zfs send/receive` direttamente via SSH. La differenza chiave: `pve-zsync` integra con il cluster Proxmox e gestisce automaticamente la rotazione degli snapshot e la configurazione delle VM; `zfs send/recv` trasferisce solo i dati, la configurazione VM va gestita separatamente (backup config via PBS o script custom). Per DR serio, combinare ZFS send (dati) + PBS sync (config + metadata).

> **Errore comune — DR testato solo con piccoli dataset.** Un DR drill con 3 VM da 10 GB non e rappresentativo di un failover di 50 VM da 500 GB. Il tempo di restore scala non linearmente: con molte VM si saturano I/O, rete, e CPU. Testare sempre con volumi realistici, idealmente >= 50% del parco reale.

> **Caso reale — VPN WireGuard con MTU sbagliato.** Un'azienda ha configurato WireGuard site-to-site per DR replication ZFS. La MTU di default di WireGuard (1420) non era compatibile con il path MTU del provider Internet (che imponeva 1400 per via di GRE tunneling intermedio). Risultato: frammentazione, perdita pacchetti intermittente, replication ZFS che falliva dopo 2-3 GB trasferiti. Soluzione: `MTU = 1380` nella config WireGuard + `ping -s 1352 -M do dr-site` per verificare il path MTU effettivo.

> **Approfondimento — DRBD come alternativa per singole VM critiche.** Per VM singole ad altissima criticita (es. database con RPO 0 e RTO < 5 min), DRBD (Distributed Replicated Block Device) offre replication sincrona a livello di blocco tra due nodi. Su Proxmox, DRBD non e integrato nativamente ma e configurabile manualmente. Vantaggi: RPO 0 senza Ceph, funziona punto-punto. Svantaggi: scala male (1 VM per coppia DRBD), non e gestito dalla GUI Proxmox, complessita operativa. Usare solo quando Ceph sync non e fattibile (ad esempio per un singolo database critico su due siti metro-distance senza Ceph).

> **Caso reale — NIS2 audit con evidenza DR insufficiente.** Un operatore di infrastruttura digitale (ISP) e stato sottoposto a verifica NIS2 nel Q1 2026. L'auditor ha richiesto: (1) BCP documentato, (2) DR plan con RTO/RPO per ogni servizio critico, (3) evidenza di DR drill eseguito nell'ultimo anno con report firmato. L'azienda aveva (1) e (2) ma non (3): il drill era stato "pianificato ma rinviato". Risultato: non-conformita con raccomandazione di adeguamento entro 90 giorni, pena sanzione. Lezione: il drill va eseguito, non solo pianificato. Calendarizzarlo come impegno fisso, non differibile.

> **Approfondimento — Ceph RBD mirror vs Ceph stretch cluster: quando quale.** Due pattern diversi per due problemi diversi. RBD mirror = replication asincrona tra cluster Ceph indipendenti, RPO > 0, funziona su qualsiasi distanza. Stretch cluster = singolo cluster Ceph con OSD distribuiti su due siti, RPO 0, richiede latenza < 2ms. Regola pratica: se i siti sono nella stessa citta e connessi con fibra dark (latenza < 1ms), stretch cluster e fattibile. Altrimenti, RBD mirror. La maggior parte dei deployment reali usa RBD mirror perche le condizioni per stretch cluster sono difficili da soddisfare.

## Letture primarie consigliate

- NIS2 Directive (EU) 2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj (retrieved 2026-04-27).
- DORA Regulation (EU) 2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj (retrieved 2026-04-27).
- ISO/IEC 27031:2011 — ICT readiness for business continuity. https://www.iso.org/standard/44374.html (retrieved 2026-04-27).
- Proxmox VE — Storage Replication (`pve-zsync`). https://pve.proxmox.com/wiki/PVE-zsync (retrieved 2026-04-27).
- Ceph Documentation — RBD Mirroring. https://docs.ceph.com/en/latest/rbd/rbd-mirroring/ (retrieved 2026-04-27).
- Ceph Documentation — Stretch Clusters. https://docs.ceph.com/en/latest/rados/operations/stretch-mode/ (retrieved 2026-04-27).
- ZFS — `zfs-send(8)` man page. https://openzfs.github.io/openzfs-docs/man/8/zfs-send.8.html (retrieved 2026-04-27).
- AWS Route 53 — Health Check + Failover Routing. https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover.html (retrieved 2026-04-27).
- Cloudflare Load Balancing. https://developers.cloudflare.com/load-balancing/ (retrieved 2026-04-27).
- WireGuard — Official Documentation. https://www.wireguard.com/ (retrieved 2026-04-27).
- BIRD Internet Routing Daemon. https://bird.network.cz/ (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 10 — `10-CLUSTER-HA-PROXMOX-POST-MIGRAZIONE/`: HA come prerequisito.
- Modulo 11.2 — `11-BACKUP-E-RIPRISTINO-PROXMOX/proxmox-backup-server-configurazione.md`: PBS sync.
- Modulo 18 — `18-PRODUCTION-CUTOVER-RUNBOOK.md`: cutover come operazione singola; DR e cutover sotto pressione.
- Modulo 12.3 — `12-SICUREZZA-E-COMPLIANCE/sicurezza-compliance.md`: framework compliance.
- Modulo 13.x — `13-MONITORAGGIO-E-OTTIMIZZAZIONE/zabbix-monitoraggio-proxmox.md`: monitoring multi-site.

## Glossario locale

| Termine | Definizione |
|---|---|
| **DR (Disaster Recovery)** | Recovery operations dopo perdita totale di un sito. |
| **HA (High Availability)** | Resilienza interna a un singolo sito. |
| **BCP (Business Continuity Plan)** | Piano olistico per continuita operations. |
| **RTO (Recovery Time Objective)** | Tempo target per ripristino. |
| **RPO (Recovery Point Objective)** | Quantita massima di dati persi (in tempo). |
| **Active/passive cold** | Site DR offline; manual failover. |
| **Active/passive warm** | Site DR running ma in standby. |
| **Active/active** | Entrambi i siti servono produzione. |
| **Stretched cluster** | Singolo cluster su 2+ siti (vincoli stretti). |
| **Async replication** | Replica con delay; performance friendly, RPO > 0. |
| **Sync replication** | Replica simultanea; RPO 0 ma latency cost. |
| **`zfs send/receive`** | Tool ZFS per replication snapshot-based. |
| **Ceph RBD mirror** | Feature Ceph per cross-cluster RBD replication. |
| **PBS sync** | Replication tra due Proxmox Backup Server. |
| **GeoDNS** | DNS routing geo-aware per failover. |
| **BGP Anycast** | Stesso IP annunciato da multipli siti. |
| **DR drill** | Esercizio pianificato di failover. |
| **NIS2** | EU directive 2022/2555 su cybersecurity. |
| **DORA** | EU regulation 2022/2554 su DORA financial sector. |
| **EBA Guidelines** | European Banking Authority requisiti BCM. |
| **Failback** | Ritorno a Site A dopo recovery. |
| **Tiebreaker** | Nodo leggero (MON only) per garantire quorum in stretch cluster. |
| **CRUSH map** | Mappa di distribuzione dati in Ceph; controlla placement di repliche per fault domain. |
| **BIRD** | BGP routing daemon open-source. |
| **WireGuard** | VPN moderna, performante, con crittografia ChaCha20/Poly1305. |
| **Path MTU** | Massima dimensione pacchetto senza frammentazione su un percorso di rete. |
| **mbuffer** | Tool per buffering di stream su rete; smoothing del throughput. |
| **Resume send** | Feature ZFS 2.0+ per riprendere un send/recv interrotto. |
| **GSLB** | Global Server Load Balancing; distribuzione traffico multi-site. |
| **Dark fiber** | Fibra ottica dedicata, non condivisa con altri clienti. Latenza minima. |
| **Change rate** | Quantita di dati modificati per unita di tempo. Determina la banda necessaria per replication. |
