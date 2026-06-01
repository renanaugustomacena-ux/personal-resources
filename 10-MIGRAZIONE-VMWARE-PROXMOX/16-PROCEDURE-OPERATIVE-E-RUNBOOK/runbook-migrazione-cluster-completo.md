# Runbook: Migrazione Completa del Cluster VMware a Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 6 — Operativa · Modulo 16.2 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 16.1 (runbook batch), 18 (cutover runbook); esperienza in migrazione batch su >= 30 VM.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. orchestrare la migrazione completa di un cluster (50-200 VM) con timing realistico, gestione delle dipendenze applicative, comunicazione con stakeholder;
> 2. coordinare wave migration (test/dev → non-critical → critical) e cutover finale.
> **Tempo stimato:** lettura 60 min + esecuzione settimane/mesi
> **Livello:** proficient → expert (Dreyfus 4 → 5)
> **Ultimo aggiornamento:** 2026-04-27

## Idee guida

1. **Migrazione cluster intero e progetto, non operazione singola.** Mesi di pianificazione, multi-team coordination, comunicazione interna costante.
2. **Wave-based de-risk.** Mai migrazione "big bang". Test/dev wave 1 valida la metodologia; wave critical e l'ultima.
3. **Decommissioning VMware solo dopo 4-8 settimane di stabilita post-migrazione.** Mantenere vSphere acceso e licenziato come safety net.

---

| Campo | Valore |
|-------|--------|
| **Documento** | RB-MIG-003 |
| **Versione** | 1.0 |
| **Data creazione** | 2026-03-24 |
| **Ultima modifica** | 2026-03-24 |
| **Autore** | Team Infrastruttura |
| **Classificazione** | Uso interno — Riservato |
| **Durata complessiva stimata** | 4-8 settimane |

---

## Indice

1. [Obiettivo e Ambito](#1-obiettivo-e-ambito)
2. [Architettura Sorgente e Destinazione](#2-architettura-sorgente-e-destinazione)
3. [Approccio a Fasi (Phased Approach)](#3-approccio-a-fasi)
4. [Fase 0: Preparazione Infrastruttura Proxmox](#4-fase-0-preparazione-infrastruttura-proxmox)
5. [Fase 1: Pilot — Migrazione Pilota](#5-fase-1-pilot)
6. [Fase 2: Wave 1 — VM Non Critiche](#6-fase-2-wave-1)
7. [Fase 3: Wave 2 — VM di Produzione](#7-fase-3-wave-2)
8. [Fase 4: Migrazione Finale e Servizi Core](#8-fase-4-migrazione-finale)
9. [Ordine di Decomposizione Cluster VMware](#9-ordine-decomposizione-cluster-vmware)
10. [Sequenza di Build Cluster Proxmox](#10-sequenza-build-cluster-proxmox)
11. [Strategia di Migrazione Storage](#11-strategia-migrazione-storage)
12. [Piano di Cutover Rete](#12-piano-cutover-rete)
13. [Riconfigurazione High Availability](#13-riconfigurazione-high-availability)
14. [Decommissioning Finale VMware](#14-decommissioning-finale-vmware)
15. [Timeline Completa con Checkpoint](#15-timeline-completa-con-checkpoint)
16. [Risk Management](#16-risk-management)
17. [Governance e Comunicazione](#17-governance-e-comunicazione)

---

## 1. Obiettivo e Ambito

### 1.1 Obiettivo

Questo runbook descrive la procedura completa per migrare l'intero cluster VMware vSphere (host ESXi, VM, storage, configurazione di rete e HA) verso un nuovo cluster Proxmox VE. La migrazione viene eseguita in fasi progressive per minimizzare il rischio e garantire la continuità operativa.

### 1.2 Ambito della Migrazione

| Componente | Sorgente (VMware) | Destinazione (Proxmox) |
|-----------|-------------------|----------------------|
| Hypervisor | ESXi 7.0/8.0 | Proxmox VE 8.x |
| Management | vCenter Server | Proxmox Web UI + CLI |
| Cluster | vSphere HA/DRS | Proxmox HA (corosync) |
| Storage | vSAN / FC SAN / NFS | Ceph / ZFS / NFS / LVM-thin |
| Networking | vDS / vSS | Linux Bridge / OVS |
| Backup | Veeam / vSphere Replication | Proxmox Backup Server |
| Monitoring | vROps | Prometheus + Grafana / Zabbix |

### 1.3 Presupposti

- Il cluster Proxmox VE è stato installato e configurato (oppure verrà configurato nella Fase 0)
- L'hardware per i nodi Proxmox è disponibile (nuovi server o riutilizzo degli stessi post-decomissioning VMware)
- La rete fisica (switch, VLAN, routing) è già predisposta o sarà configurata nella Fase 0
- Il team è stato formato su Proxmox VE

### 1.4 Vincoli

- Downtime massimo accettabile per singola VM: definito per ogni VM nella matrice di impatto
- Nessuna perdita di dati (RPO = 0 per il cutover)
- Il vecchio ambiente VMware deve restare disponibile per rollback per almeno 14 giorni dopo la migrazione completa

---

## 2. Architettura Sorgente e Destinazione

### 2.1 Inventario Cluster VMware Sorgente

```
Cluster VMware vSphere:
├── vCenter Server: vcenter.dominio.local
├── Datacenter: DC-Principale
├── Cluster: CL-PROD-01
│   ├── Host ESXi 1: esxi-01.dominio.local (Dell R740, 256GB RAM, 40 cores)
│   ├── Host ESXi 2: esxi-02.dominio.local (Dell R740, 256GB RAM, 40 cores)
│   ├── Host ESXi 3: esxi-03.dominio.local (Dell R740, 256GB RAM, 40 cores)
│   └── [Host ESXi N]: ...
├── Storage:
│   ├── Datastore-SSD-01 (vSAN / SAN LUN) — X TB
│   ├── Datastore-SSD-02 (vSAN / SAN LUN) — X TB
│   └── Datastore-NFS-01 (NFS) — X TB
├── Networking:
│   ├── vDS-Prod (VLAN 100-199)
│   ├── vDS-Mgmt (VLAN 10)
│   └── vDS-Storage (VLAN 20)
└── VM Totali: XX VM (YY TB disco totale)
```

### 2.2 Architettura Target Cluster Proxmox

```
Cluster Proxmox VE:
├── Nodo 1: pve-01.dominio.local
├── Nodo 2: pve-02.dominio.local
├── Nodo 3: pve-03.dominio.local
├── [Nodo N]: ...
├── Storage:
│   ├── Ceph Pool (replicazione 3x) — oppure
│   ├── ZFS Pool (mirror/raidz) — oppure
│   ├── LVM-thin su SSD locali — oppure
│   └── NFS/iSCSI condiviso
├── Networking:
│   ├── vmbr0 (Management — VLAN 10)
│   ├── vmbr1 (VM Traffic — trunk VLAN 100-199)
│   ├── vmbr2 (Storage — VLAN 20) [se Ceph]
│   └── Corosync ring (dedicato)
├── Backup:
│   └── Proxmox Backup Server (PBS)
└── HA:
    └── Proxmox HA (corosync + pve-ha-manager)
```

---

## 3. Approccio a Fasi

### 3.1 Panoramica delle Fasi

```
Settimana 1-2: FASE 0 — Preparazione Infrastruttura
    ├── Build cluster Proxmox
    ├── Configurazione storage
    ├── Configurazione rete
    └── Setup backup e monitoring

Settimana 2-3: FASE 1 — PILOT
    ├── 2-3 VM non critiche (dev/test)
    ├── Validazione procedura end-to-end
    └── Lessons learned e aggiustamenti

Settimana 3-4: FASE 2 — WAVE 1
    ├── VM di sviluppo e staging
    ├── VM di servizi interni non critici
    └── ~30-40% delle VM totali

Settimana 4-6: FASE 3 — WAVE 2
    ├── VM di produzione non critiche
    ├── VM di produzione critiche (batch dedicati)
    └── ~50-60% delle VM totali

Settimana 6-8: FASE 4 — MIGRAZIONE FINALE
    ├── Servizi core (DC, DNS, DHCP, NTP)
    ├── VM rimanenti
    ├── Decommissioning VMware
    └── Chiusura progetto
```

### 3.2 Criteri di Avanzamento tra Fasi

| Da Fase | A Fase | Criteri per Avanzare |
|---------|--------|---------------------|
| Fase 0 → Fase 1 | Pilot | Cluster Proxmox operativo, backup funzionante, rete configurata |
| Fase 1 → Fase 2 | Wave 1 | Pilot completato con successo, nessun problema critico, runbook validato |
| Fase 2 → Fase 3 | Wave 2 | Wave 1 completata, tutte le VM stabili per 48h, nessun rollback |
| Fase 3 → Fase 4 | Finale | Wave 2 completata, VM produzione stabili per 72h, approvazione management |

### 3.3 Gate Review (Revisione di Fase)

Alla fine di ogni fase, condurre una gate review:

| Elemento della Review | Dettaglio |
|----------------------|-----------|
| Partecipanti | Migration Lead, IT Manager, Owner Applicativi, CTO |
| Durata | 1 ora |
| Agenda | Risultati fase, problemi, lessons learned, piano fase successiva |
| Output | Decisione GO/NO-GO per fase successiva |
| Documentazione | Verbale della revisione, action items |

---

## 4. Fase 0: Preparazione Infrastruttura Proxmox

**Durata stimata: 1-2 settimane**

### 4.1 Preparazione Hardware

Per ogni nodo Proxmox (vedere SOP-COMM-001 per la procedura dettagliata):

| Step | Attività | Tempo | Stato |
|------|----------|-------|-------|
| 1 | Installazione fisica server nel rack | 2h | ☐ |
| 2 | Configurazione BIOS/UEFI (VT-x, VT-d, IOMMU) | 30 min | ☐ |
| 3 | Configurazione IPMI/iDRAC/iLO | 30 min | ☐ |
| 4 | Aggiornamento firmware | 1h | ☐ |
| 5 | Cablaggio rete (min 2x 10GbE + 1x IPMI) | 1h | ☐ |
| 6 | Verifica cablaggio e link | 30 min | ☐ |

### 4.2 Installazione Proxmox VE

```bash
# Procedura di installazione per ogni nodo
# 1. Boot da USB/PXE con Proxmox VE ISO
# 2. Selezionare disco di installazione (preferibilmente SSD dedicato)
# 3. Configurare:
#    - Filesystem: ext4 o ZFS (mirror per il sistema)
#    - Hostname: pve-01.dominio.local
#    - IP management: 10.0.10.11/24
#    - Gateway: 10.0.10.1
#    - DNS: 10.0.10.2

# Post-installazione — su ogni nodo:

# Configurare i repository
cat > /etc/apt/sources.list.d/pve-no-subscription.list <<EOF
deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription
EOF

# Oppure se si ha la subscription:
# cat > /etc/apt/sources.list.d/pve-enterprise.list <<EOF
# deb https://enterprise.proxmox.com/debian/pve bookworm pve-enterprise
# EOF

# Aggiornare il sistema
apt update && apt full-upgrade -y

# Installare utilità
apt install -y libguestfs-tools qemu-utils htop iotop iftop tmux
```

### 4.3 Creazione Cluster Proxmox

```bash
# Sul primo nodo (pve-01) — Creare il cluster
pvecm create CLUSTER-PROD

# Verificare
pvecm status

# Sul secondo nodo (pve-02) — Unirsi al cluster
pvecm add 10.0.10.11  # IP del primo nodo

# Sul terzo nodo (pve-03) — Unirsi al cluster
pvecm add 10.0.10.11

# Verificare il cluster
pvecm status
pvecm nodes
```

### 4.4 Configurazione Storage

#### Opzione A: Ceph (Distributed Storage)

```bash
# Installare Ceph su tutti i nodi
pveceph install

# Inizializzare Ceph (sul primo nodo)
pveceph init --network 10.0.20.0/24  # Rete storage dedicata

# Creare i monitor (su 3 nodi)
pveceph mon create  # Eseguire su pve-01, pve-02, pve-03

# Creare gli OSD (su ogni nodo, per ogni disco dati)
pveceph osd create /dev/sdb  # Disco dati 1
pveceph osd create /dev/sdc  # Disco dati 2
# Ripetere per ogni nodo

# Creare il pool
pveceph pool create vm-pool --pg_autoscale_mode on --size 3 --min_size 2

# Verificare
ceph -s
ceph osd tree
```

#### Opzione B: ZFS (Local Storage con replica)

```bash
# Su ogni nodo — Creare il pool ZFS
zpool create -f rpool mirror /dev/sdb /dev/sdc

# Creare il dataset per le VM
zfs create rpool/data

# Registrare lo storage in Proxmox
pvesm add zfspool local-zfs --pool rpool/data --content images,rootdir
```

#### Opzione C: LVM-thin (Local Storage)

```bash
# Su ogni nodo — Creare il volume group
pvcreate /dev/sdb
vgcreate vg-data /dev/sdb

# Creare il thin pool
lvcreate -l 95%VG --type thin-pool -n data vg-data

# Registrare lo storage in Proxmox
pvesm add lvmthin local-lvm-data --vgname vg-data --thinpool data --content images,rootdir
```

### 4.5 Configurazione Rete

```bash
# Configurazione di rete su ogni nodo Proxmox
# Editare /etc/network/interfaces

# === Esempio configurazione con bonding e VLAN ===

auto lo
iface lo inet loopback

# Bond per il traffico di management e VM
auto bond0
iface bond0 inet manual
    bond-slaves eno1 eno2
    bond-miimon 100
    bond-mode 802.3ad
    bond-xmit-hash-policy layer3+4

# Bridge management (VLAN 10)
auto vmbr0
iface vmbr0 inet static
    address 10.0.10.11/24
    gateway 10.0.10.1
    bridge-ports bond0.10
    bridge-stp off
    bridge-fd 0

# Bridge VM traffic (trunk VLAN 100-199)
auto vmbr1
iface vmbr1 inet manual
    bridge-ports bond0
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 100-199

# Bond per storage (se Ceph)
auto bond1
iface bond1 inet manual
    bond-slaves ens1f0 ens1f1
    bond-miimon 100
    bond-mode 802.3ad

# Bridge storage (VLAN 20)
auto vmbr2
iface vmbr2 inet static
    address 10.0.20.11/24
    bridge-ports bond1.20
    bridge-stp off
    bridge-fd 0

# Rete Corosync (dedicata)
auto ens2f0
iface ens2f0 inet static
    address 10.0.30.11/24
```

### 4.6 Configurazione Backup (Proxmox Backup Server)

```bash
# Installare e configurare Proxmox Backup Server su un server dedicato
# Oppure usare un datastore NFS/CIFS

# Aggiungere PBS come storage in Proxmox
pvesm add pbs pbs-backup \
  --server pbs.dominio.local \
  --username backup@pbs \
  --password XXXXXX \
  --datastore ds1 \
  --fingerprint XX:XX:XX:...

# Creare job di backup
# (Da Web UI: Datacenter > Backup > Add)
```

### 4.7 Configurazione Monitoring

```bash
# Esempio con Prometheus + Grafana

# Installare Prometheus PVE Exporter su ogni nodo
pip install prometheus-pve-exporter

# Configurare il job Prometheus
# scrape_configs:
#   - job_name: 'proxmox'
#     static_configs:
#       - targets: ['pve-01:9221', 'pve-02:9221', 'pve-03:9221']
```

### 4.8 Checklist Fine Fase 0

| # | Verifica | Stato |
|---|----------|-------|
| 1 | Tutti i nodi Proxmox installati e aggiornati | ☐ |
| 2 | Cluster Proxmox operativo (pvecm status OK) | ☐ |
| 3 | Storage configurato e funzionante | ☐ |
| 4 | Rete configurata (bridge, VLAN, bonding) | ☐ |
| 5 | Proxmox Backup Server operativo | ☐ |
| 6 | Primo backup test completato | ☐ |
| 7 | Monitoring operativo | ☐ |
| 8 | HA abilitata e testata (con VM di test) | ☐ |
| 9 | Driver VirtIO ISO caricato su tutti i nodi | ☐ |
| 10 | Documentazione infrastruttura aggiornata | ☐ |

---

## 5. Fase 1: Pilot — Migrazione Pilota

**Durata stimata: 3-5 giorni**

### 5.1 Selezione VM Pilot

Selezionare 2-3 VM con le seguenti caratteristiche:

- Non critiche per il business (ambiente dev/test)
- Rappresentative dell'ambiente (almeno 1 Linux e 1 Windows)
- Dimensione disco contenuta (< 100 GB)
- Senza dipendenze complesse
- Owner disponibile per validazione rapida

| VM Pilot | OS | Disco | VLAN | Owner | Stato |
|----------|----|----|------|-------|-------|
| dev-web-01 | Ubuntu 22.04 | 30 GB | 50 | Team Dev | ☐ |
| dev-db-01 | Rocky 9 | 50 GB | 50 | Team Dev | ☐ |
| test-win-01 | Win Server 2022 | 80 GB | 50 | Team QA | ☐ |

### 5.2 Esecuzione Pilot

Seguire il runbook RB-MIG-001 (Migrazione Singola VM) per ogni VM del pilot.

**Obiettivi specifici del pilot**:

1. Validare il processo end-to-end
2. Misurare i tempi reali di ogni fase
3. Identificare problemi non previsti
4. Testare la procedura di rollback (deliberatamente su almeno 1 VM)
5. Validare backup e restore su Proxmox
6. Validare il monitoring

### 5.3 Test Specifici del Pilot

```bash
# Test 1: Migrazione VM Linux
# → Seguire RB-MIG-001 completo
# → Tempo effettivo: ____

# Test 2: Migrazione VM Windows
# → Seguire RB-MIG-001 completo con sezione Windows
# → Tempo effettivo: ____

# Test 3: Rollback deliberato
# → Migrare una VM, validarla, poi eseguire il rollback
# → Verificare che la VM VMware torni operativa
# → Tempo rollback effettivo: ____

# Test 4: Backup e Restore su Proxmox
# → Eseguire backup della VM migrata via PBS
# → Eliminare la VM
# → Ripristinare la VM dal backup
# → Verificare che funzioni
# → Tempo backup: ____ | Tempo restore: ____

# Test 5: HA Failover
# → Abilitare HA per la VM pilot
# → Simulare il failure di un nodo (reboot forzato)
# → Verificare che la VM venga avviata su un altro nodo
# → Tempo di failover: ____

# Test 6: Live Migration
# → Migrare la VM da un nodo Proxmox all'altro (live)
# → Verificare downtime: ____
```

### 5.4 Revisione Pilot (Gate Review)

| Criterio | Risultato | Accettabile? |
|----------|-----------|-------------|
| Tutte le VM pilot migrate con successo | ☐ Sì ☐ No | |
| Tempi di migrazione in linea con le stime | ☐ Sì ☐ No | |
| Nessun problema critico irrisolto | ☐ Sì ☐ No | |
| Procedura di rollback testata e funzionante | ☐ Sì ☐ No | |
| Backup e restore funzionanti | ☐ Sì ☐ No | |
| HA funzionante | ☐ Sì ☐ No | |
| Owner applicativi soddisfatti | ☐ Sì ☐ No | |
| Runbook aggiornato con lessons learned | ☐ Sì ☐ No | |

**Decisione**: ☐ Procedere con Wave 1 | ☐ Ripetere pilot con aggiustamenti

---

## 6. Fase 2: Wave 1 — VM Non Critiche

**Durata stimata: 1-2 settimane**

### 6.1 Composizione Wave 1

| Batch | VM Incluse | Weekend/Sera | Operatori |
|-------|-----------|-------------|-----------|
| BATCH-W1-01 | VM sviluppo (5 VM) | Sera feriale | 2 |
| BATCH-W1-02 | VM test/QA (5 VM) | Sera feriale | 2 |
| BATCH-W1-03 | VM staging (5 VM) | Weekend | 2 |
| BATCH-W1-04 | VM utility interne (5 VM) | Sera feriale | 2 |

### 6.2 Pianificazione Dettagliata Wave 1

```
Settimana 3:
  Lunedì:    Pre-check BATCH-W1-01 (VM sviluppo)
  Martedì:   Migrazione BATCH-W1-01 (sera 19:00-23:00)
  Mercoledì: Validazione BATCH-W1-01 + Pre-check BATCH-W1-02
  Giovedì:   Migrazione BATCH-W1-02 (sera 19:00-23:00)
  Venerdì:   Validazione BATCH-W1-02 + Stabilizzazione

Settimana 4:
  Lunedì:    Pre-check BATCH-W1-03 (VM staging)
  Martedì:   Review stato Wave 1
  Sabato:    Migrazione BATCH-W1-03 (mattina 08:00-14:00)
  Domenica:  Buffer / fix
  Lunedì:    Validazione BATCH-W1-03 + Pre-check BATCH-W1-04
  Martedì:   Migrazione BATCH-W1-04 (sera 19:00-23:00)
  Mercoledì: Validazione BATCH-W1-04
  Giovedì:   Gate Review Wave 1
```

### 6.3 Esecuzione Wave 1

Per ogni batch della Wave 1, seguire il runbook RB-MIG-002 (Migrazione Batch).

### 6.4 Monitoraggio Stabilità Post-Wave 1

Dopo la Wave 1, monitorare per almeno 48 ore:

```bash
# Verificare tutte le VM migrate della Wave 1
for VMID in $(cat /etc/pve/.vmlist | jq -r 'keys[]'); do
    echo "VMID: $VMID — $(qm status $VMID)"
done

# Verificare uptime
for IP in $(cat wave1-ips.txt); do
    echo -n "$IP: "; ssh admin@$IP "uptime" 2>/dev/null || echo "UNREACHABLE"
done

# Verificare backup completati
pvesh get /cluster/backup-info/not-backed-up
```

---

## 7. Fase 3: Wave 2 — VM di Produzione

**Durata stimata: 2-3 settimane**

### 7.1 Composizione Wave 2

La Wave 2 include le VM di produzione, organizzate per criticità crescente:

| Batch | Tipo VM | Criticità | Finestra | Operatori |
|-------|---------|-----------|----------|-----------|
| BATCH-W2-01 | Produzione — servizi web secondari | Media | Weekend | 3 |
| BATCH-W2-02 | Produzione — application server | Media-Alta | Weekend | 3 |
| BATCH-W2-03 | Produzione — database secondari | Alta | Weekend | 3 |
| BATCH-W2-04 | Produzione — servizi core (mail, file) | Alta | Weekend | 3 |
| BATCH-W2-05 | Produzione — ERP/CRM | Critica | Weekend dedicato | 4 |

### 7.2 Requisiti Aggiuntivi per VM di Produzione

| Requisito | Dettaglio |
|-----------|----------|
| Change Request approvato | Per ogni batch, CR approvato dal CAB |
| Backup verificato | Backup completo + test di restore |
| Rollback plan testato | Procedura di rollback validata nel pilot |
| Owner sign-off pre-migrazione | Conferma scritta dall'owner applicativo |
| Piano di comunicazione | Notifica a tutti gli utenti impattati |
| Supporto vendor | Conferma disponibilità supporto applicativo |
| Finestra di manutenzione estesa | Weekend per VM critiche |
| Monitoraggio dedicato | Alert per le prime 72 ore post-migrazione |

### 7.3 Procedura Speciale per VM Critiche (ERP, Database)

Per le VM con criticità "Critica":

```
1. PRE-MIGRAZIONE (Settimana precedente)
   ├── Full backup + test restore
   ├── Snapshot VMware come safety net
   ├── Pre-copia del disco (se possibile)
   ├── Dry run della procedura (su ambiente di test se disponibile)
   └── Conferma finestra da CTO

2. MIGRAZIONE (Weekend dedicato)
   ├── Venerdì sera: Freeze degli applicativi, ultimo backup
   ├── Sabato mattina: Migrazione effettiva
   ├── Sabato pomeriggio: Validazione tecnica e applicativa
   ├── Domenica: Buffer per fix + validazione estesa
   └── Lunedì mattina: Go-live verification

3. POST-MIGRAZIONE (Prima settimana)
   ├── Monitoraggio intensivo (alert su ogni anomalia)
   ├── Stand-by del team (reperibilità 24/7)
   ├── Daily check con owner applicativo
   ├── Performance comparison con baseline
   └── Rollback possibile fino a venerdì (5 giorni)
```

### 7.4 Monitoraggio Stabilità Post-Wave 2

Periodo di osservazione: 72 ore minimo per VM critiche.

```bash
# Script monitoraggio continuo VM critiche
#!/bin/bash

CRITICAL_VMS=(
    "300:erp-server:192.168.100.50"
    "301:db-oracle:192.168.100.51"
    "302:mail-server:192.168.100.52"
)

LOG_FILE="/var/log/migration-monitoring.log"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    for VM_ENTRY in "${CRITICAL_VMS[@]}"; do
        IFS=':' read -r VMID NAME IP <<< "$VM_ENTRY"

        # Check VM status
        STATUS=$(qm status $VMID | awk '{print $2}')

        # Check ping
        PING_OK=$(ping -c 1 -W 2 $IP > /dev/null 2>&1 && echo "OK" || echo "FAIL")

        # Log
        echo "$TIMESTAMP | $NAME ($VMID) | Status: $STATUS | Ping: $PING_OK" >> $LOG_FILE

        # Alert se problemi
        if [ "$STATUS" != "running" ] || [ "$PING_OK" != "OK" ]; then
            echo "ALERT: $NAME non raggiungibile!" | mail -s "ALERT Migration Monitor" admin@dominio.local
        fi
    done
    sleep 60
done
```

---

## 8. Fase 4: Migrazione Finale e Servizi Core

**Durata stimata: 1-2 settimane**

### 8.1 Servizi Core da Migrare per Ultimi

| Servizio | VM | Motivo | Strategia |
|----------|----|----|-----------|
| Domain Controller | dc-01, dc-02 | Tutti i servizi dipendono da AD/DNS | Migrare uno alla volta, mantenere almeno 1 DC attivo |
| DNS Server | dns-01, dns-02 | Risoluzione nomi per tutte le VM | Migrare uno alla volta |
| DHCP Server | dhcp-01 | Assegnazione IP automatica | Migrare fuori orario |
| NTP Server | ntp-01 | Sincronizzazione orario | Verificare che i nodi Proxmox usino NTP esterno |
| Monitoring Server | mon-01 | Monitorare la migrazione stessa | Migrare per ultimo |
| vCenter Server | vcenter | Non migrare — decommissionare | Decommission dopo che tutte le VM sono migrate |

### 8.2 Procedura Migrazione Domain Controller

```
ATTENZIONE: La migrazione dei Domain Controller richiede estrema cautela.
Procedura speciale — NON seguire il runbook standard.

Prerequisiti:
- Almeno 2 DC nel dominio
- Replicazione AD funzionante e verificata
- FSMO roles identificate

Procedura:
1. Verificare la salute di AD
   repadmin /replsummary
   dcdiag /v
   netdom query fsmo

2. Migrare DC-02 (non detentore dei ruoli FSMO)
   - Seguire runbook singola VM
   - Verificare replicazione AD post-migrazione
   - Attendere 24 ore

3. Trasferire i ruoli FSMO a DC-02 (ora su Proxmox)
   ntdsutil
   > roles
   > connections
   > connect to server DC-02
   > quit
   > transfer naming master
   > transfer infrastructure master
   > transfer PDC
   > transfer RID master
   > transfer schema master

4. Migrare DC-01
   - Seguire runbook singola VM
   - Verificare replicazione AD
   - Verificare tutti i ruoli FSMO

5. Validazione finale
   repadmin /replsummary
   dcdiag /v
   nslookup dominio.local
```

### 8.3 Checklist Migrazione Finale

| # | Attività | Stato |
|---|----------|-------|
| 1 | Tutti i DC migrati e replicazione OK | ☐ |
| 2 | DNS funzionante da Proxmox | ☐ |
| 3 | DHCP funzionante (se applicabile) | ☐ |
| 4 | Monitoring operativo da Proxmox | ☐ |
| 5 | Nessuna VM rimasta su VMware (escluso vCenter) | ☐ |
| 6 | Tutti i backup funzionanti su PBS | ☐ |
| 7 | HA configurata per tutte le VM critiche | ☐ |
| 8 | 72 ore di stabilità osservate | ☐ |

---

## 9. Ordine di Decomposizione Cluster VMware

### 9.1 Ordine di Rimozione Host ESXi

L'ordine di decomposizione del cluster VMware segue una logica inversa rispetto alla migrazione:

```
Fase 1 (dopo Wave 1):
  └── Host ESXi con più capacità libera → Manutenzione mode → Rimuovere da cluster
      (Ridurre il cluster VMware man mano che le VM vengono migrate)

Fase 2 (dopo Wave 2):
  └── Host ESXi rimanenti (tranne 1-2 per rollback) → Manutenzione mode

Fase 3 (dopo migrazione finale):
  └── Ultimi host ESXi → Spegnere
  └── vCenter Server → Spegnere (non migrare)
```

### 9.2 Procedura Riduzione Cluster VMware

```powershell
# 1. Mettere l'host in Maintenance Mode
# (vCenter migrerà automaticamente le VM rimaste via DRS)
Set-VMHost -VMHost esxi-03.dominio.local -State Maintenance

# 2. Verificare che non ci siano più VM sull'host
Get-VMHost esxi-03.dominio.local | Get-VM

# 3. Rimuovere l'host dal cluster
# Da vCenter: Right-click host > Remove from Inventory
# Oppure:
Remove-VMHost -VMHost esxi-03.dominio.local -Confirm:$false

# 4. Rimuovere i datastore (se non condivisi)
# 5. Spegnere il server fisico
```

---

## 10. Sequenza di Build Cluster Proxmox

### 10.1 Se si Riutilizzano gli Stessi Server

Se i server VMware vengono riutilizzati come nodi Proxmox:

```
Fase 1: Installare Proxmox su server nuovi/dedicati (min 3 nodi)
         ├── pve-01 (nuovo hardware o server disponibile)
         ├── pve-02
         └── pve-03

Fase 2: Migrare VM sui 3 nodi Proxmox iniziali

Fase 3: Quando un host ESXi viene liberato:
         ├── Reinstallare come nodo Proxmox
         ├── Unire al cluster Proxmox
         ├── Aggiungere storage (Ceph OSD)
         └── Ribilanciare le VM

Fase 4: Ripetere Fase 3 per ogni host ESXi liberato

Fase 5: Cluster Proxmox finale con tutti i nodi
```

### 10.2 Aggiunta Incrementale Nodi Proxmox

```bash
# Quando un nuovo nodo è pronto:

# 1. Installare Proxmox VE (come descritto nella Fase 0)

# 2. Configurare la rete (copiare la configurazione dagli altri nodi)

# 3. Unire al cluster
pvecm add 10.0.10.11  # IP del primo nodo

# 4. Se Ceph: Aggiungere OSD
pveceph osd create /dev/sdb
pveceph osd create /dev/sdc

# 5. Verificare lo stato del cluster
pvecm status
ceph -s  # Se Ceph

# 6. Abilitare il nodo per HA
ha-manager groupnode add pve-new --node pve-new
```

---

## 11. Strategia di Migrazione Storage

### 11.1 Mapping Storage VMware → Proxmox

| Storage VMware | Tipo | Dimensione | Storage Proxmox | Tipo | Note |
|---------------|------|-----------|----------------|------|------|
| Datastore-SSD-01 | vSAN / SAN | X TB | ceph-pool / local-zfs | Ceph / ZFS | Per VM I/O intensive |
| Datastore-SSD-02 | vSAN / SAN | X TB | ceph-pool / local-zfs | Ceph / ZFS | Per VM I/O intensive |
| Datastore-NFS-01 | NFS | X TB | nfs-share | NFS | Per ISO, template, backup |
| Datastore-Archive | NFS/iSCSI | X TB | nfs-archive | NFS | Per dati freddi |

### 11.2 Considerazioni sulla Capacità

```bash
# Calcolare lo spazio necessario su Proxmox

# Spazio occupato su VMware (effettivo, non provisioned)
# PowerCLI:
Get-VM | Select-Object Name, @{N="UsedGB";E={[math]::Round($_.UsedSpaceGB,2)}} | Sort-Object UsedGB -Descending

# Spazio necessario su Proxmox:
# - Se Ceph con replicazione 3x: Spazio effettivo * 3
# - Se ZFS mirror: Spazio effettivo * 2
# - Se LVM-thin: Spazio effettivo * 1.2 (20% overhead)
# - Aggiungere 30% di margine per crescita
```

### 11.3 Migrazione Dati Condivisi (NFS)

Se le VM accedono a datastore NFS condivisi:

```bash
# Opzione 1: Mantenere lo stesso NFS server
# → Montare lo stesso NFS su Proxmox
pvesm add nfs nfs-shared --server nfs-server.dominio.local --export /export/vm-data --content images

# Opzione 2: Migrare i dati NFS
rsync -avP --progress /mnt/old-nfs/ /mnt/new-nfs/
```

---

## 12. Piano di Cutover Rete

### 12.1 Strategia di Rete

Due approcci possibili:

**Approccio A: Stessa Rete (raccomandato)**
- Le VM Proxmox mantengono gli stessi IP
- I bridge Proxmox sono configurati sulle stesse VLAN
- Nessun cambiamento di routing necessario
- Il cutover è trasparente per la rete

**Approccio B: Nuova Rete (se necessario per coesistenza)**
- Le VM Proxmox ricevono nuovi IP (temporaneamente)
- Routing tra vecchia e nuova rete
- DNS update necessario
- Cutover più complesso

### 12.2 Verifica Configurazione di Rete Pre-Cutover

```bash
# Su ogni nodo Proxmox — Verificare la configurazione dei bridge

# Verificare le VLAN
bridge vlan show dev bond0

# Verificare il trunk
bridge -d vlan show

# Test di connettività da una VM Proxmox verso risorse nella stessa VLAN
# (usare una VM di test)
qm start 999  # VM di test
qm guest exec 999 -- ping -c 3 gateway_ip
qm guest exec 999 -- ping -c 3 dns_server
qm guest exec 999 -- ping -c 3 vm_vmware_test
```

### 12.3 Procedura di Cutover per Servizi con Load Balancer

```
Per servizi dietro load balancer:

1. Migrare i backend server su Proxmox (uno alla volta)
2. Verificare che il load balancer raggiunga i backend sui nuovi nodi
3. NON cambiare la configurazione del load balancer se gli IP non cambiano
4. Se gli IP cambiano:
   a. Aggiungere i nuovi backend al pool
   b. Verificare il traffico
   c. Rimuovere i vecchi backend dal pool
```

---

## 13. Riconfigurazione High Availability

### 13.1 Mapping HA VMware → Proxmox

| Feature VMware | Equivalente Proxmox |
|---------------|-------------------|
| vSphere HA | Proxmox HA (pve-ha-manager) |
| DRS (load balancing) | Nessun equivalente diretto (manuale o script) |
| Admission Control | Configurabile via ha-manager |
| VM Restart Priority | HA Group priority |
| Host Isolation Response | Fencing (hardware watchdog) |

### 13.2 Configurazione HA su Proxmox

```bash
# Abilitare HA per una VM
ha-manager add vm:$VMID --state started --max_restart 3 --max_relocate 2

# Creare un HA group (opzionale, per vincolare VM a determinati nodi)
ha-manager groupadd prod-group --node pve-01,pve-02,pve-03 --restricted 1 --nofailback 0

# Assegnare la VM al gruppo
ha-manager set vm:$VMID --group prod-group

# Verificare la configurazione HA
ha-manager status
ha-manager config
```

### 13.3 Test HA Post-Migrazione

```bash
# Test 1: Simulare il failure di un nodo
# Sul nodo da "crashare":
echo b > /proc/sysrq-trigger  # ATTENZIONE: crash immediato

# Verificare che le VM vengano avviate sugli altri nodi
# (Da un altro nodo)
ha-manager status
# Le VM dovrebbero risultare "started" su un altro nodo entro 2-5 minuti

# Test 2: Verificare fencing
# Controllare che il nodo fallito venga fenced correttamente
# e che non si verifichi split-brain
pvecm status
```

### 13.4 Configurazione Fencing

```bash
# Configurare il watchdog hardware (raccomandato per produzione)
# Verificare che il watchdog sia disponibile
ls -la /dev/watchdog*

# Abilitare il fencing
# Su ogni nodo, verificare /etc/default/pve-ha-manager:
# WATCHDOG_MODULE=softdog  # o ipmi_watchdog per hardware watchdog
```

---

## 14. Decommissioning Finale VMware

### 14.1 Prerequisiti per il Decommissioning

| # | Prerequisito | Stato |
|---|-------------|-------|
| 1 | Tutte le VM migrate e validate su Proxmox | ☐ |
| 2 | 14 giorni di stabilità osservati | ☐ |
| 3 | Nessun rollback necessario negli ultimi 7 giorni | ☐ |
| 4 | Tutti gli owner applicativi hanno dato il sign-off | ☐ |
| 5 | Backup funzionante per tutte le VM su Proxmox | ☐ |
| 6 | HA testata e funzionante | ☐ |
| 7 | Documentazione completa e aggiornata | ☐ |
| 8 | Approvazione CTO per il decommissioning | ☐ |

### 14.2 Procedura di Decommissioning

Vedere il documento SOP-DEC-001 (sop-decommissioning-host-vmware.md) per la procedura dettagliata.

Sequenza:

```
1. Spegnere tutte le VM VMware rimaste (dovrebbero essere solo le copie di backup)
2. Rimuovere gli host dal cluster VMware
3. Spegnere vCenter Server
4. Rilasciare le licenze VMware (da Broadcom portal)
5. Rilasciare lo storage (LUN, vSAN)
6. Rilasciare gli IP di management VMware
7. Aggiornare DNS e DHCP
8. Rimuovere dal monitoring
9. Documentare il decommissioning
10. Fisicamente: riutilizzare i server come nodi Proxmox o decommissionare
```

---

## 15. Timeline Completa con Checkpoint

### 15.1 Gantt ad Alto Livello

```
Settimana  1 ████████ Fase 0: Preparazione Infrastruttura
Settimana  2 ████████ Fase 0: Completamento + Inizio Fase 1
              ▲ CHECKPOINT 1: Infrastruttura Proxmox pronta

Settimana  3 ████████ Fase 1: Pilot (migrazione + validazione)
              ▲ CHECKPOINT 2: Pilot completato, Gate Review

Settimana  4 ████████ Fase 2: Wave 1 — Batch 1-2
Settimana  5 ████████ Fase 2: Wave 1 — Batch 3-4 + Stabilizzazione
              ▲ CHECKPOINT 3: Wave 1 completata, Gate Review

Settimana  6 ████████ Fase 3: Wave 2 — Batch 1-2 (Prod non critiche)
Settimana  7 ████████ Fase 3: Wave 2 — Batch 3-4 (Prod critiche)
Settimana  8 ████████ Fase 3: Wave 2 — Batch 5 (ERP/CRM) + Stabilizzazione
              ▲ CHECKPOINT 4: Wave 2 completata, Gate Review

Settimana  9 ████████ Fase 4: Migrazione servizi core + DC
Settimana 10 ████████ Fase 4: Stabilizzazione + Decommissioning VMware
              ▲ CHECKPOINT 5: Migrazione completa

Settimana 11-12 ████ Periodo di osservazione (14 giorni)
              ▲ CHECKPOINT 6: Decommissioning VMware completato
              ▲ PROGETTO CHIUSO
```

### 15.2 Checkpoint Dettagliati

| # | Checkpoint | Settimana | Criteri di Superamento | Approvatore |
|---|-----------|-----------|----------------------|-------------|
| CP1 | Infrastruttura Proxmox pronta | 2 | Cluster operativo, storage e rete OK, backup OK | IT Manager |
| CP2 | Pilot completato | 3 | 3 VM migrate e validate, rollback testato | Migration Lead |
| CP3 | Wave 1 completata | 5 | Tutte le VM non critiche migrate, 48h stabilità | IT Manager |
| CP4 | Wave 2 completata | 8 | Tutte le VM produzione migrate, 72h stabilità | CTO |
| CP5 | Migrazione completa | 10 | Tutte le VM migrate, servizi core OK, 0 VM su VMware | CTO |
| CP6 | Decommissioning completato | 12 | VMware spento, licenze rilasciate, server riutilizzati | IT Manager |

---

## 16. Risk Management

### 16.1 Registro dei Rischi

| ID | Rischio | Probabilità | Impatto | Score | Mitigazione |
|----|---------|-------------|---------|-------|-------------|
| R01 | Corruzione dati durante la conversione del disco | Bassa | Critico | Alto | Verificare checksum, mantenere backup VMware |
| R02 | Incompatibilità driver post-migrazione | Media | Alto | Alto | Test pilot, driver VirtIO pre-iniettati |
| R03 | Performance degradate su Proxmox | Media | Alto | Alto | Benchmark pre/post, tuning CPU/disk |
| R04 | Failure dello storage Ceph durante migrazione | Bassa | Critico | Alto | Replicazione 3x, monitoring Ceph, OSD spare |
| R05 | Rete non funzionante post-migrazione | Media | Critico | Critico | Test rete pre-migrazione, bridge e VLAN verificati |
| R06 | Rollback necessario per VM critica | Media | Alto | Alto | Procedura testata nel pilot, VM VMware preservate |
| R07 | Superamento della finestra di manutenzione | Media | Medio | Medio | Buffer 30%, rollback deadline definiti |
| R08 | Perdita di licenze software (license tied to hardware/MAC) | Bassa | Medio | Medio | Inventario licenze, preservare MAC address |
| R09 | Team non sufficientemente formato | Media | Alto | Alto | Training pre-progetto, pilot come formazione pratica |
| R10 | Problemi con Ceph in produzione | Bassa | Critico | Alto | Sizing corretto, monitoring, documentazione |

### 16.2 Piano di Contingenza

Per ogni rischio ad alto impatto, definire un piano di contingenza:

| Rischio | Piano di Contingenza |
|---------|---------------------|
| R01 | Restore da backup VMware, retry migrazione con metodo alternativo |
| R05 | Rollback VM su VMware, troubleshoot rete, ripianificare |
| R06 | Procedura rollback testata (vedi RB-MIG-001 sez. 14) |

---

## 17. Governance e Comunicazione

### 17.1 Struttura di Governance

```
Steering Committee (decisioni strategiche)
├── CTO
├── IT Manager
└── Responsabile Operazioni

Migration Team (esecuzione)
├── Migration Lead (coordinamento)
├── Operatori Migrazione (2-3 persone)
├── Network Engineer
├── Storage Engineer
└── DBA (per VM database)

Stakeholders
├── Owner Applicativi (validazione funzionale)
├── Security Team (verifica compliance)
├── Help Desk (supporto utenti)
└── Management (aggiornamenti stato)
```

### 17.2 Piano di Comunicazione

| Comunicazione | Frequenza | Destinatari | Canale | Responsabile |
|--------------|-----------|-------------|--------|-------------|
| Status Report Progetto | Settimanale | Steering Committee | Email + Meeting | Migration Lead |
| Aggiornamento Tecnico | Giornaliero (durante wave) | Migration Team | Chat/Standup | Migration Lead |
| Notifica Pre-Batch | T-7 giorni | Utenti impattati | Email | Communication Lead |
| Status Durante Batch | Ogni 2 ore | Stakeholders | Email + Chat | Migration Lead |
| Notifica Post-Batch | Al completamento | Utenti impattati | Email | Communication Lead |
| Gate Review | Fine di ogni fase | Steering Committee | Meeting | Migration Lead |
| Report Finale | Fine progetto | Tutti | Email + Presentazione | Migration Lead |

### 17.3 Template Status Report Settimanale

```
PROGETTO: Migrazione VMware → Proxmox VE
REPORT SETTIMANALE — Settimana N (GG/MM - GG/MM)
════════════════════════════════════════════════

STATO GENERALE: 🟢 On Track / 🟡 At Risk / 🔴 Delayed

PROGRESSI:
- VM migrate questa settimana: X
- VM totali migrate: X/Y (XX%)
- Fase corrente: Wave N
- Batch completati: X/Y

PROSSIME ATTIVITÀ:
- [Attività 1]
- [Attività 2]

RISCHI/PROBLEMI:
- [Rischio/Problema 1 — Mitigazione]

DECISIONI RICHIESTE:
- [Decisione 1]

PROSSIMA MILESTONE: [Descrizione — Data]
```

---

**Fine del documento — RB-MIG-003 v1.0**

---

## Esercizi

1. **Stretch — pianificare migrazione cluster reale o simulato.** Su carta, pianifica timeline completa per cluster ipotetico 5 nodi VMware → Proxmox: dipendenze, wave plan, communication plan, rollback plan.

## Collegamenti incrociati

- Modulo 16.1 — `runbook-migrazione-batch.md`: building block batch.
- Modulo 18 — `../18-PRODUCTION-CUTOVER-RUNBOOK.md`: runbook di cutover.
- Modulo 19 — `../19-MULTI-SITE-DR-PROXMOX.md`: DR multi-site post-migrazione.
