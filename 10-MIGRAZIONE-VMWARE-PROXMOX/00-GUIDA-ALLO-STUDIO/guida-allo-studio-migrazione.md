# Guida allo Studio — Migrazione VMware → Proxmox VE

## Indice

1. [Panoramica del Percorso di Studio](#1-panoramica-del-percorso-di-studio)
2. [Struttura del Corso](#2-struttura-del-corso)
3. [Roadmap di Apprendimento](#3-roadmap-di-apprendimento)
4. [Ambiente di Laboratorio](#4-ambiente-di-laboratorio)
5. [Prerequisiti Tecnici](#5-prerequisiti-tecnici)
6. [Glossario VMware vs Proxmox](#6-glossario-vmware-vs-proxmox)
7. [Risorse Esterne](#7-risorse-esterne)

---

## 1. Panoramica del Percorso di Studio

### Obiettivi del Corso

Questo percorso formativo prepara professionisti IT alla pianificazione, esecuzione
e gestione completa di migrazioni da VMware vSphere/ESXi a Proxmox VE in ambienti
di produzione enterprise. Al completamento, lo studente sara in grado di:

```
┌─────────────────────────────────────────────────────────────────┐
│                   OBIETTIVI FORMATIVI                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CONOSCENZE (sapere)                                             │
│  ├── Architettura VMware vSphere e Proxmox VE                   │
│  ├── Storage: VMFS/vSAN → LVM/LVM-Thin/ZFS/Ceph                │
│  ├── Networking: vSwitch/NSX → Linux Bridge/OVS/SDN             │
│  ├── HA/Cluster: vSphere HA/DRS → Proxmox HA/Corosync          │
│  └── Backup: vSphere Data Protection → PBS                      │
│                                                                  │
│  COMPETENZE (saper fare)                                         │
│  ├── Eseguire assessment infrastruttura VMware esistente         │
│  ├── Pianificare e dimensionare cluster Proxmox target           │
│  ├── Migrare VM con cold/warm/live migration                     │
│  ├── Convertire dischi VMDK → qcow2/raw                          │
│  ├── Configurare HA, backup, monitoring post-migrazione          │
│  └── Automatizzare operazioni con API e IaC                      │
│                                                                  │
│  ATTITUDINI (saper essere)                                       │
│  ├── Valutare trade-off tecnici ed economici                     │
│  ├── Comunicare con stakeholder business e tecnici               │
│  ├── Gestire rischi e pianificare rollback                        │
│  └── Documentare procedure operative ripetibili                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Destinatari

| Ruolo | Rilevanza | Sezioni Prioritarie |
|-------|-----------|---------------------|
| System Administrator | Alta | 01-08, 10-11, 16-17 |
| Infrastructure Engineer | Alta | Tutte |
| Network Engineer | Media | 04, 07, 12 |
| Storage Engineer | Media | 03, 08 |
| DevOps/SRE | Media-Alta | 13, 14, 16 |
| IT Manager / CTO | Bassa-Media | 05, 15 |
| Security Engineer | Media | 12 |

### Prerequisiti

```
Prerequisiti — Livello Richiesto
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Linux System Administration    ████████░░  80%  (CRITICO)
  ├── CLI: bash, file system, permessi, systemd
  ├── Package management (apt, dnf)
  ├── Gestione servizi e log (journalctl)
  └── Scripting bash base

  Networking TCP/IP               ██████░░░░  60%  (IMPORTANTE)
  ├── IPv4/IPv6, subnetting, routing
  ├── VLAN, bonding/LAG
  ├── DNS, DHCP, firewall (iptables/nftables)
  └── Concetti: bridge, NAT, overlay

  Storage Concepts                ██████░░░░  60%  (IMPORTANTE)
  ├── Block vs file vs object storage
  ├── RAID livelli (0, 1, 5, 6, 10)
  ├── LVM base (PV, VG, LV)
  └── NFS, iSCSI concetti

  Virtualizzazione Base          █████░░░░░  50%  (UTILE)
  ├── Concetti: hypervisor tipo 1 e 2
  ├── Esperienza VMware o KVM base
  └── QEMU/libvirt familiarita opzionale

  VMware vSphere (esistente)     ████░░░░░░  40%  (UTILE)
  ├── Navigazione vSphere Client
  ├── Gestione base VM, datastore
  └── Familiarita con ESXi CLI opzionale
```

### Durata Stimata

| Modalita di Studio | Durata Totale | Ore/Settimana | Settimane |
|---------------------|---------------|---------------|-----------|
| Full-time intensivo | 120-160 ore | 40 | 3-4 |
| Part-time dedicato | 120-160 ore | 15-20 | 6-10 |
| Autoapprendimento serale | 120-160 ore | 8-10 | 12-16 |
| Solo lab pratico (skip teoria) | 60-80 ore | 20 | 3-4 |

---

## 2. Struttura del Corso

### Mappa Generale delle Sezioni

```
┌─────────────────────────────────────────────────────────────────────┐
│                 PERCORSO MIGRAZIONE VMware → Proxmox VE             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  FASE 1: FONDAMENTI                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ 00 Guida Studio  │  │ 01 Fondamenti    │  │ 02 Fondamenti    │   │
│  │    (questo doc)  │  │    VMware        │  │    Proxmox VE    │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
│  ┌──────────────────┐  ┌──────────────────┐                         │
│  │ 03 Storage       │  │ 04 Networking    │                         │
│  │    Avanzato      │  │    Avanzato      │                         │
│  └──────────────────┘  └──────────────────┘                         │
│            │                                                         │
│            ▼                                                         │
│  FASE 2: ASSESSMENT                                                  │
│  ┌──────────────────┐                                                │
│  │ 05 Assessment e  │                                                │
│  │    Pianificazione│                                                │
│  └──────────────────┘                                                │
│            │                                                         │
│            ▼                                                         │
│  FASE 3: MIGRAZIONE                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ 06 Strategie e   │  │ 07 Migrazione    │  │ 08 Migrazione    │   │
│  │    Metodi        │  │    Networking    │  │    Storage       │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
│  ┌──────────────────┐                                                │
│  │ 09 Scenari       │                                                │
│  │    Specifici     │                                                │
│  └──────────────────┘                                                │
│            │                                                         │
│            ▼                                                         │
│  FASE 4: POST-MIGRAZIONE                                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ 10 Cluster e HA  │  │ 11 Backup e      │  │ 12 Sicurezza e   │   │
│  │    Post-Migr.    │  │    Ripristino    │  │    Compliance    │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
│            │                                                         │
│            ▼                                                         │
│  FASE 5: OPERATIONS                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ 13 Monitoraggio  │  │ 14 Automazione   │  │ 15 Aspetti       │   │
│  │    e Ottimizz.   │  │    e IaC         │  │    Business      │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
│  ┌──────────────────┐  ┌──────────────────┐                         │
│  │ 16 Procedure     │  │ 17 Troubleshoot. │                         │
│  │    e Runbook     │  │    e Guide       │                         │
│  └──────────────────┘  └──────────────────┘                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Descrizione Dettagliata delle Sezioni

#### FASE 1 — Fondamenti (Sezioni 00-04)

| Sezione | Titolo | Contenuto Chiave | Ore Stimate |
|---------|--------|------------------|-------------|
| 00 | Guida allo Studio | Panoramica, roadmap, glossario, lab setup | 2-3 |
| 01 | Fondamenti VMware | Architettura ESXi/vCenter, VMFS, vSwitch, HA/DRS, licensing | 10-14 |
| 02 | Fondamenti Proxmox VE | KVM/QEMU, architettura cluster, web GUI, storage/network base | 10-14 |
| 03 | Storage Avanzato Proxmox | LVM, LVM-Thin, ZFS, Ceph, NFS, iSCSI, Proxmox Backup Server | 12-16 |
| 04 | Networking Avanzato Proxmox | Linux Bridge, OVS, VLAN, bonding, SDN, firewall Proxmox | 10-14 |

**Obiettivo fase**: Costruire comprensione solida di entrambe le piattaforme prima
di affrontare la migrazione. Non saltare questa fase.

#### FASE 2 — Assessment (Sezione 05)

| Sezione | Titolo | Contenuto Chiave | Ore Stimate |
|---------|--------|------------------|-------------|
| 05 | Assessment e Pianificazione | Inventario VMware, analisi dipendenze, sizing Proxmox, timeline, risk assessment | 8-12 |

**Obiettivo fase**: Mappare l'infrastruttura VMware esistente e definire il piano
di migrazione dettagliato.

#### FASE 3 — Migrazione (Sezioni 06-09)

| Sezione | Titolo | Contenuto Chiave | Ore Stimate |
|---------|--------|------------------|-------------|
| 06 | Strategie e Metodi | Cold/Warm/Live migration, virt-v2v, qemu-img, tool commerciali | 14-18 |
| 07 | Migrazione Networking | Mappatura vSwitch → Linux Bridge, VLAN migration, IP planning | 8-12 |
| 08 | Migrazione Storage | VMDK → qcow2, datastore migration, shared storage cutover | 8-12 |
| 09 | Scenari Specifici | Windows Server, database, applicazioni stateful, cluster app | 10-14 |

**Obiettivo fase**: Eseguire le migrazioni effettive con competenza e sicurezza.

#### FASE 4 — Post-Migrazione (Sezioni 10-12)

| Sezione | Titolo | Contenuto Chiave | Ore Stimate |
|---------|--------|------------------|-------------|
| 10 | Cluster e HA | Configurazione HA, fencing/STONITH, live migration interna, bilanciamento | 10-14 |
| 11 | Backup e Ripristino | Proxmox Backup Server, vzdump, retention policy, disaster recovery | 8-12 |
| 12 | Sicurezza e Compliance | SSL/TLS, LDAP/AD auth, firewall, hardening, audit | 8-12 |

**Obiettivo fase**: Stabilizzare l'ambiente Proxmox e garantire resilienza e
conformita.

#### FASE 5 — Operations (Sezioni 13-17)

| Sezione | Titolo | Contenuto Chiave | Ore Stimate |
|---------|--------|------------------|-------------|
| 13 | Monitoraggio e Ottimizzazione | Zabbix, Grafana, performance tuning, capacity planning | 8-10 |
| 14 | Automazione e IaC | API Proxmox, Terraform, Ansible, Cloud-Init, template VM | 10-14 |
| 15 | Aspetti Business e Cliente | Business case, TCO, presentazione stakeholder, change management | 6-8 |
| 16 | Procedure Operative e Runbook | Runbook migrazione batch, procedure operative standard, checklist | 8-10 |
| 17 | Troubleshooting e Guide Pratiche | Debug networking, storage, cluster, driver, scenari comuni | 10-14 |

**Obiettivo fase**: Operare l'infrastruttura Proxmox in modo efficiente e
automatizzato nel lungo termine.

---

## 3. Roadmap di Apprendimento

### Timeline Settimanale Consigliata (Part-time, ~15 ore/settimana)

```
Settimana   Sezione    Attivita                                   Ore
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sett. 1     00 + 01    Guida studio, architettura VMware          14-16
                       Lab: installare VMware ESXi evaluation

Sett. 2     01         Fondamenti VMware: storage, network, HA     14-16
                       Lab: creare VM, configurare vSwitch

Sett. 3     02         Fondamenti Proxmox VE: installazione        14-16
                       Lab: installare Proxmox, creare prime VM

Sett. 4     02 + 03    Proxmox avanzato, LVM, LVM-Thin            14-16
                       Lab: configurare storage LVM e ZFS

Sett. 5     03 + 04    Storage condiviso, networking Proxmox       14-16
                       Lab: NFS/iSCSI, bridge, VLAN, bonding

Sett. 6     04 + 05    Networking avanzato, assessment planning    14-16
                       Lab: OVS, SDN, inventario VMware

Sett. 7     06         Strategie migrazione, cold/warm migration   14-16
                       Lab: prima migrazione cold con qemu-img

Sett. 8     06 + 07    virt-v2v, migrazione networking             14-16
                       Lab: migrare VM con virt-v2v, VLAN mapping

Sett. 9     08 + 09    Migrazione storage, scenari specifici       14-16
                       Lab: migrare Windows Server, database VM

Sett. 10    10         Cluster HA post-migrazione                  14-16
                       Lab: cluster 3 nodi, HA, fencing

Sett. 11    11 + 12    Backup (PBS), sicurezza, LDAP/SSL           14-16
                       Lab: PBS setup, backup schedule, cert TLS

Sett. 12    13 + 14    Monitoring (Zabbix), automazione (API)      14-16
                       Lab: Zabbix agent, API script, Terraform

Sett. 13    15 + 16    Business case, runbook operativi            10-14
                       Esercizio: scrivere runbook per caso reale

Sett. 14    17         Troubleshooting, revisione generale         14-16
                       Lab: simulare e risolvere failure scenari
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                       TOTALE STIMATO                             ~200 ore
```

### Percorso Accelerato (Full-time, 4 settimane)

```
Settimana   Focus                    Sezioni    Ore
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sett. 1     Fondamenti               00-04      40
Sett. 2     Assessment + Migrazione  05-09      40
Sett. 3     Post-Migrazione          10-12      35
Sett. 4     Operations + Review      13-17      35-40
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                     TOTALE     ~155 ore
```

### Percorso per Ruolo Specifico

```
SYSTEM ADMINISTRATOR (focus operativo):
Sett. 1-2:  01, 02          → Fondamenti
Sett. 3-4:  03, 04          → Storage e networking
Sett. 5-6:  06, 07, 08      → Migrazione pratica
Sett. 7-8:  10, 11, 16, 17  → HA, backup, runbook, troubleshooting

INFRASTRUCTURE ENGINEER (percorso completo):
Seguire la roadmap completa di 14 settimane

DEVOPS / SRE (focus automazione):
Sett. 1:    02              → Fondamenti Proxmox
Sett. 2:    03, 04          → Storage e networking
Sett. 3:    06              → Strategie migrazione
Sett. 4-5:  13, 14          → Monitoring e automazione
Sett. 6:    16              → Runbook operativi

IT MANAGER (focus strategico):
Sett. 1:    00, 01 (overview), 02 (overview)
Sett. 2:    05, 15          → Assessment e business case
Sett. 3:    06 (overview), 16 → Strategie e procedure
```

### Milestone e Verifiche di Apprendimento

| Milestone | Dopo Sezione | Verifica Pratica |
|-----------|--------------|------------------|
| M1 — Fondamenti | 02 | Installare Proxmox, creare 3 VM (Linux, Windows, container LXC) |
| M2 — Storage/Net | 04 | Configurare ZFS mirror, VLAN trunking, Linux Bridge con bonding |
| M3 — Prima Migrazione | 06 | Migrare una VM da VMware a Proxmox con cold migration |
| M4 — Migrazione Completa | 09 | Migrare 5+ VM (mix Windows/Linux) con metodi diversi |
| M5 — Cluster HA | 10 | Cluster 3 nodi funzionante con HA, testare failover |
| M6 — Production Ready | 12 | Backup funzionante, SSL configurato, LDAP integrato |
| M7 — Day-2 Operations | 17 | Monitoring attivo, almeno 2 runbook scritti, troubleshooting simulato |

---

## 4. Ambiente di Laboratorio

### 4.1 Requisiti Hardware Minimi

```
┌─────────────────────────────────────────────────────────────────┐
│              CONFIGURAZIONE LAB — 3 OPZIONI                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  OPZIONE A: Server fisico singolo (nested virtualization)       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  CPU:     Intel i7/Xeon o AMD Ryzen 7 (8+ core)            ││
│  │           VT-x/AMD-V + VT-d/AMD-Vi OBBLIGATORIO            ││
│  │  RAM:     64 GB minimo (32 GB limite inferiore)             ││
│  │  Disco:   SSD 500 GB + HDD 1 TB (o SSD 1 TB unico)        ││
│  │  Rete:    2x NIC Gigabit (1x management + 1x VM traffic)   ││
│  │  Note:    Nested virt. ha overhead ~10-15%                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  OPZIONE B: 3 mini-PC (cluster reale)                           │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  3x Mini-PC (es. Intel NUC, Beelink, MinisForum)           ││
│  │  CPU:     Intel i5/i7 o AMD Ryzen 5 per nodo               ││
│  │  RAM:     16-32 GB per nodo (48-96 GB totali)              ││
│  │  Disco:   SSD NVMe 256 GB + SSD SATA 500 GB per nodo      ││
│  │  Rete:    1x NIC Gigabit per nodo + switch managed         ││
│  │  Switch:  Switch managed con supporto VLAN (es. TP-Link)   ││
│  │  Costo:   ~800-1500 EUR per 3 nodi                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  OPZIONE C: Cloud / VPS (per chi non ha hardware)               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Provider che supportano nested virtualization:              ││
│  │  - Hetzner Dedicated Server (consigliato)                   ││
│  │  - OVH Bare Metal                                           ││
│  │  - Scaleway Elastic Metal                                   ││
│  │  Spec:    64 GB RAM, 8 core, 500 GB SSD                    ││
│  │  Costo:   ~50-100 EUR/mese                                 ││
│  │  Note:    VPS standard NON supporta nested virt.            ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Architettura Lab Consigliata

```
┌──────────────────────────────────────────────────────────────────────┐
│                         LAB ARCHITECTURE                              │
│                                                                       │
│    Management Network: 10.10.10.0/24 (VLAN 10)                       │
│    VM Network:         10.10.20.0/24 (VLAN 20)                       │
│    Storage Network:    10.10.30.0/24 (VLAN 30)                       │
│    Migration Network:  10.10.40.0/24 (VLAN 40)                       │
│                                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │  Proxmox 1  │  │  Proxmox 2  │  │  Proxmox 3  │                  │
│  │  (pve1)     │  │  (pve2)     │  │  (pve3)     │                  │
│  │ .10.10.11   │  │ .10.10.12   │  │ .10.10.13   │                  │
│  │ 16-32GB RAM │  │ 16-32GB RAM │  │ 16-32GB RAM │                  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │
│         │                │                │                           │
│         └────────────────┼────────────────┘                           │
│                          │                                            │
│              ┌───────────┴───────────┐                                │
│              │   Switch Managed      │                                │
│              │   VLAN 10,20,30,40    │                                │
│              └───────────┬───────────┘                                │
│                          │                                            │
│         ┌────────────────┼────────────────┐                           │
│         │                │                │                           │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐                  │
│  │  ESXi Lab   │  │  NAS/NFS    │  │  Workstation│                  │
│  │ (sorgente)  │  │  (storage)  │  │  (client)   │                  │
│  │ .10.10.20   │  │ .10.30.50   │  │ .10.10.100  │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.3 Installazione Proxmox VE — Step by Step

**Step 1: Download e preparazione media**

```bash
# Scaricare ISO Proxmox VE dal sito ufficiale
# https://www.proxmox.com/en/downloads/proxmox-virtual-environment/iso

# Verificare checksum SHA256
sha256sum proxmox-ve_8.x-x.iso

# Creare USB bootable (Linux)
dd if=proxmox-ve_8.x-x.iso of=/dev/sdX bs=4M status=progress conv=fdatasync

# Creare USB bootable (alternativa con Ventoy)
# 1. Installare Ventoy su USB
# 2. Copiare ISO nella partizione Ventoy
```

**Step 2: Installazione Proxmox su ogni nodo**

```
Sequenza installazione:
1. Boot da USB → selezionare "Install Proxmox VE"
2. Accettare EULA
3. Selezionare disco target
   └── Opzione raccomandata per lab:
       Filesystem: ext4 (semplice) o ZFS RAID1 (se 2 dischi)
       hdsize: lasciare default o ridurre per riservare spazio
4. Paese, timezone, layout tastiera
5. Password root e email amministratore
6. Configurazione rete:
   Management Interface: selezionare NIC principale
   Hostname (FQDN):     pve1.lab.local
   IP Address:           10.10.10.11/24
   Gateway:              10.10.10.1
   DNS Server:           10.10.10.1 (o 8.8.8.8)
7. Conferma e installazione
8. Ripetere per pve2 (.12) e pve3 (.13)
```

**Step 3: Configurazione post-installazione**

```bash
# Accedere via SSH o console
ssh root@10.10.10.11

# Disabilitare repository enterprise (per lab senza licenza)
sed -i 's/^deb/# deb/' /etc/apt/sources.list.d/pve-enterprise.list

# Aggiungere repository no-subscription (per lab/test)
echo "deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription" \
  > /etc/apt/sources.list.d/pve-no-subscription.list

# Aggiornare il sistema
apt update && apt full-upgrade -y

# Verificare stato del nodo
pvesh get /nodes/$(hostname)/status

# Accedere alla web GUI
# https://10.10.10.11:8006
# Login: root / password impostata durante installazione
```

**Step 4: Creare cluster (su pve1)**

```bash
# Sul primo nodo — creare il cluster
pvecm create lab-cluster

# Verificare stato cluster
pvecm status

# Sul secondo nodo — unirsi al cluster
pvecm add 10.10.10.11

# Sul terzo nodo — unirsi al cluster
pvecm add 10.10.10.11

# Verificare cluster completo (da qualsiasi nodo)
pvecm status
pvecm nodes
```

### 4.4 VMware ESXi Lab — Evaluation License

```
VMware ESXi Evaluation (60 giorni):
1. Scaricare ESXi ISO da VMware (richiede account Broadcom)
   https://support.broadcom.com/
2. Installare su hardware fisico o nested (su Proxmox stesso)
3. La evaluation license include tutte le funzionalita

Nested ESXi su Proxmox (per lab senza hardware dedicato):
┌────────────────────────────────────────────────────────┐
│ Proxmox Host                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │ VM: ESXi-Lab (ID 200)                            │  │
│  │   CPU:   4 cores, type=host (OBBLIGATORIO)       │  │
│  │   RAM:   16 GB                                    │  │
│  │   Disco: 100 GB (virtio-scsi o SATA)             │  │
│  │   Net:   virtio, model=vmxnet3 NON supportato    │  │
│  │   Args:  -cpu host,+vmx (abilitare nested virt)  │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

```bash
# Configurazione VM per nested ESXi su Proxmox
# File: /etc/pve/qemu-server/200.conf

agent: 0
bios: ovmf
boot: order=scsi0;ide2
cores: 4
cpu: host
efidisk0: local-lvm:vm-200-disk-0,efitype=4m,size=4M
ide2: local:iso/VMware-VMvisor-Installer-8.x.iso,media=cdrom
machine: q35
memory: 16384
name: esxi-lab
net0: e1000=AA:BB:CC:DD:EE:01,bridge=vmbr0,firewall=0
numa: 0
ostype: other
scsi0: local-lvm:vm-200-disk-1,size=100G,ssd=1
scsihw: lsi
smbios1: uuid=xxxxx
vmgenid: xxxxx
args: -cpu host,+vmx
```

### 4.5 Rete di Test — Configurazione Switch e VLAN

```bash
# Su ogni nodo Proxmox — configurare /etc/network/interfaces

auto lo
iface lo inet loopback

# Interface fisica
auto eno1
iface eno1 inet manual

# Bridge management (VLAN 10) — accesso diretto (untagged)
auto vmbr0
iface vmbr0 inet static
    address 10.10.10.11/24
    gateway 10.10.10.1
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0

# Bridge VM traffic (VLAN 20)
auto vmbr0.20
iface vmbr0.20 inet manual

auto vmbr1
iface vmbr1 inet manual
    bridge-ports vmbr0.20
    bridge-stp off
    bridge-fd 0

# Bridge storage (VLAN 30, opzionale se NFS/iSCSI)
auto vmbr0.30
iface vmbr0.30 inet static
    address 10.10.30.11/24

# Per lab con interfaccia singola, usare VLAN-aware bridge:
# auto vmbr0
# iface vmbr0 inet static
#     address 10.10.10.11/24
#     gateway 10.10.10.1
#     bridge-ports eno1
#     bridge-stp off
#     bridge-fd 0
#     bridge-vlan-aware yes
#     bridge-vids 2-4094
```

### 4.6 VM di Test da Preparare

| VM | OS | Scopo | RAM | Disco | Note |
|----|-----|-------|-----|-------|------|
| test-linux-01 | Debian 12 | Migrazione base Linux | 2 GB | 20 GB | Server LAMP |
| test-linux-02 | Rocky Linux 9 | Migrazione RHEL-like | 2 GB | 20 GB | Con LVM interno |
| test-win-01 | Windows Server 2022 | Migrazione Windows | 4 GB | 40 GB | Con AD/DNS role |
| test-db-01 | Debian 12 + PostgreSQL | Migrazione database | 4 GB | 30 GB | Con dati di test |
| test-web-01 | Ubuntu 22.04 | Migrazione web server | 2 GB | 20 GB | Nginx + app |

```
Creare queste VM su ESXi-Lab, installare i servizi, popolare con
dati di test. Queste VM serviranno come sorgente per gli esercizi
di migrazione nelle sezioni 06-09.
```

---

## 5. Prerequisiti Tecnici

### 5.1 Checklist Competenze Richieste

```
LINUX SYSTEM ADMINISTRATION (CRITICO — non procedere senza queste)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Navigazione filesystem Linux (cd, ls, find, locate)
□ Gestione file e permessi (chmod, chown, umask, ACL)
□ Editor di testo CLI (vim o nano, sufficiente uno)
□ Gestione pacchetti (apt su Debian/Ubuntu, dnf su RHEL/Rocky)
□ Gestione servizi con systemd (systemctl start/stop/enable/status)
□ Gestione processi (ps, top, htop, kill, nice)
□ Log di sistema (journalctl, /var/log/*)
□ Cron jobs e task scheduling (crontab -e, systemd timers)
□ Utenti e gruppi (useradd, usermod, /etc/passwd, /etc/shadow)
□ SSH: login, chiavi, config, tunneling base
□ Bash scripting base: variabili, loop, condizioni, pipe, redirect
□ Disk management: fdisk/parted, mkfs, mount, fstab, df, lsblk
```

```
NETWORKING TCP/IP (IMPORTANTE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Modello OSI e TCP/IP stack
□ IPv4 addressing e subnetting (CIDR notation)
□ Routing: ip route, default gateway, static routes
□ DNS: record A, AAAA, CNAME, MX, PTR; risoluzione e troubleshooting
□ DHCP: concetti client/server, lease, reservation
□ VLAN: concetti 802.1Q, trunk vs access port
□ Bonding/LACP: concetti, modalita (802.3ad, active-backup)
□ Firewall: iptables o nftables base, concetti chain/table/rule
□ NAT: SNAT, DNAT, masquerading
□ Strumenti: ping, traceroute, ss/netstat, tcpdump, nmap
□ Bridge networking: concetto di bridge, tap interface
```

```
STORAGE (IMPORTANTE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Block vs file vs object storage: differenze e use case
□ RAID: livelli 0, 1, 5, 6, 10 — pro/contro di ciascuno
□ LVM base: concetti PV → VG → LV, comandi pvcreate/vgcreate/lvcreate
□ Filesystem: ext4, XFS — concetti, mkfs, mount, resize
□ NFS: concetti client/server, /etc/exports, mount NFS
□ iSCSI: concetti initiator/target, LUN
□ Concetti SAN vs NAS
□ I/O performance: IOPS, throughput, latency
```

```
VIRTUALIZZAZIONE (UTILE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Hypervisor tipo 1 (bare-metal) vs tipo 2 (hosted)
□ CPU virtualization: VT-x/AMD-V, vCPU, overcommit
□ Memory virtualization: ballooning, KSM, overcommit
□ Disk virtualization: formati immagine (vmdk, qcow2, raw)
□ Network virtualization: vNIC, virtual switch
□ Concetti: snapshot, clone, template, migration
□ Paravirtualizzazione: VirtIO driver
```

### 5.2 Autovalutazione

Per ogni area, assegnare un punteggio da 1 a 5:

```
┌──────────────────────────┬───┬───┬───┬───┬───┬──────────────────┐
│ Competenza               │ 1 │ 2 │ 3 │ 4 │ 5 │ Azione           │
├──────────────────────────┼───┼───┼───┼───┼───┼──────────────────┤
│ Linux CLI e admin        │   │   │   │   │   │ 1-2: studiare    │
│ Bash scripting           │   │   │   │   │   │      prima di    │
│ Networking TCP/IP        │   │   │   │   │   │      iniziare    │
│ Storage e filesystem     │   │   │   │   │   │                  │
│ LVM                      │   │   │   │   │   │ 3: procedere con │
│ Firewall (iptables/nft)  │   │   │   │   │   │    attenzione    │
│ Virtualizzazione base    │   │   │   │   │   │                  │
│ VMware vSphere           │   │   │   │   │   │ 4-5: OK          │
│ KVM/QEMU                 │   │   │   │   │   │                  │
│ ZFS                      │   │   │   │   │   │                  │
├──────────────────────────┼───┼───┼───┼───┼───┼──────────────────┤
│ 1 = Mai usato                                                    │
│ 2 = Familiarita teorica                                          │
│ 3 = Uso occasionale                                              │
│ 4 = Uso regolare                                                 │
│ 5 = Esperto                                                      │
└──────────────────────────────────────────────────────────────────┘
```

### 5.3 Risorse per Colmare Gap

| Area con Gap | Risorsa Consigliata | Tipo | Durata |
|--------------|---------------------|------|--------|
| Linux CLI | "The Linux Command Line" — William Shotts | Libro (gratis online) | 20-30 ore |
| Linux Admin | LPIC-1 study material (101 + 102) | Certificazione | 40-60 ore |
| Bash Scripting | "Advanced Bash-Scripting Guide" — Mendel Cooper | Guida online | 15-20 ore |
| Networking | "TCP/IP Illustrated Vol. 1" — W. Richard Stevens | Libro | 30-40 ore |
| Networking pratico | Laboratorio GNS3 o Packet Tracer | Lab | 10-15 ore |
| Storage/LVM | Red Hat Storage Administration Guide | Documentazione | 10-15 ore |
| RAID | "RAID levels explained" — kernel.org | Documentazione | 3-5 ore |
| Virtualizzazione | "Mastering KVM Virtualization" — Humble Devassy | Libro | 20-30 ore |
| VMware base | VMware vSphere Documentation Center | Documentazione | 15-20 ore |

---

## 6. Glossario VMware vs Proxmox

### 6.1 Tabella Comparativa Principale

```
┌──────────────────────────────────────────────────────────────────┐
│               MAPPATURA CONCETTI VMware → Proxmox VE             │
├───────────────────────┬──────────────────────────────────────────┤
│  CONCETTO VMWARE      │  EQUIVALENTE PROXMOX VE                 │
├───────────────────────┼──────────────────────────────────────────┤
│                       │                                          │
│  COMPUTE              │                                          │
│  ESXi Host            │  Proxmox VE Node                        │
│  vCenter Server       │  Proxmox Cluster (pvecm) + Web GUI      │
│  vSphere Client       │  Proxmox Web GUI (porta 8006)           │
│  VMware VM            │  QEMU/KVM VM (qm)                       │
│  VMware Tools         │  QEMU Guest Agent (qemu-ga)             │
│  vApp                 │  Pool di risorse                         │
│  Resource Pool        │  Pool                                    │
│  ---                  │  LXC Container (pct) [no equiv. VMware] │
│                       │                                          │
│  STORAGE              │                                          │
│  VMFS Datastore       │  LVM / LVM-Thin / Directory             │
│  VMDK (thick/thin)    │  qcow2 / raw image                      │
│  vSAN                 │  Ceph (integrato) / ZFS                  │
│  NFS Datastore        │  NFS Storage (identico)                  │
│  iSCSI Datastore      │  iSCSI Storage (identico)               │
│  Content Library      │  Template + ISO Storage                  │
│  Storage vMotion      │  Move Disk (qm move_disk)               │
│  Storage Profile      │  Storage configuration per-pool          │
│                       │                                          │
│  NETWORKING           │                                          │
│  vSwitch (Standard)   │  Linux Bridge (vmbr)                    │
│  vDS (Distributed)    │  OVS (Open vSwitch) / SDN               │
│  Port Group           │  Bridge + VLAN tag                       │
│  VMkernel Port        │  Management interface / VLAN interface   │
│  NSX                  │  SDN (VXLAN/VLAN) + OVS                 │
│  NIC Teaming          │  Linux Bonding (bond)                    │
│                       │                                          │
│  HA / CLUSTER         │                                          │
│  vSphere HA           │  Proxmox HA (ha-manager)                │
│  vSphere DRS          │  Nessun equivalente nativo diretto       │
│  vSphere FT           │  CEPH replication + HA (diverso)        │
│  vMotion              │  Live Migration (qm migrate --online)   │
│  Admission Control    │  HA resource configuration               │
│  Host Isolation       │  Fencing / STONITH                       │
│  Cluster (vSphere)    │  Proxmox Cluster (Corosync + pmxcfs)    │
│                       │                                          │
│  BACKUP               │                                          │
│  VADP (API backup)    │  vzdump / Proxmox Backup Server (PBS)   │
│  Snapshot             │  Snapshot (qm snapshot)                  │
│  vSphere Replication  │  PBS remote sync / ZFS send/receive      │
│                       │                                          │
│  SICUREZZA            │                                          │
│  vCenter SSO          │  Proxmox auth realms (PAM, LDAP, AD)    │
│  vSphere Roles        │  PVE Roles + Permissions                │
│  VM Encryption        │  LUKS disk encryption                    │
│  Distributed Firewall │  Proxmox Firewall (host + VM level)     │
│                       │                                          │
│  AUTOMAZIONE          │                                          │
│  vSphere API (SOAP)   │  Proxmox REST API (JSON)                │
│  PowerCLI             │  pvesh / curl / Proxmox SDK (Python)    │
│  vRealize / Aria      │  Terraform + Ansible                    │
│  OVF/OVA              │  VM config (.conf) + disk image          │
│  Guest Customization  │  Cloud-Init                              │
│                       │                                          │
│  LICENSING            │                                          │
│  ESXi Free (limiti)   │  Proxmox VE Free (completo, no support) │
│  vSphere Standard     │  Proxmox Community Subscription          │
│  vSphere Enterprise+  │  Proxmox Standard/Premium Subscription   │
│  vSAN License         │  Ceph/ZFS incluso (no licenza extra)    │
│  NSX License          │  SDN/OVS incluso (no licenza extra)     │
│                       │                                          │
└───────────────────────┴──────────────────────────────────────────┘
```

### 6.2 Comandi Equivalenti

| Operazione | VMware CLI (esxcli/PowerCLI) | Proxmox CLI |
|------------|------------------------------|-------------|
| Listare VM | `vim-cmd vmsvc/getallvms` | `qm list` |
| Stato VM | `vim-cmd vmsvc/power.getstate <vmid>` | `qm status <vmid>` |
| Avviare VM | `vim-cmd vmsvc/power.on <vmid>` | `qm start <vmid>` |
| Spegnere VM | `vim-cmd vmsvc/power.shutdown <vmid>` | `qm shutdown <vmid>` |
| Force stop | `vim-cmd vmsvc/power.off <vmid>` | `qm stop <vmid>` |
| Creare snapshot | `vim-cmd vmsvc/snapshot.create <vmid>` | `qm snapshot <vmid> <name>` |
| Listare datastore | `esxcli storage filesystem list` | `pvesm status` |
| Info host | `esxcli system version get` | `pveversion -v` |
| Listare network | `esxcli network vswitch standard list` | `ip link show` / `cat /etc/network/interfaces` |
| Cluster status | PowerCLI: `Get-Cluster` | `pvecm status` |
| Listare container | N/A | `pct list` |
| Info storage | `esxcli storage vmfs extent list` | `pvesm status` / `zpool status` / `lvs` |
| Backup VM | VADP-based (Veeam, etc.) | `vzdump <vmid> --storage <target>` |

### 6.3 Concetti Senza Equivalente Diretto

| Concetto VMware | Situazione in Proxmox | Alternativa |
|-----------------|----------------------|-------------|
| vSphere DRS (Dynamic Resource Scheduler) | Non esiste in Proxmox nativo | Script custom con API; progetti community (pve-drs) |
| vSphere FT (Fault Tolerance) | Non supportato | HA + Ceph replication per resilienza simile |
| vApp | Non esiste come oggetto | Usare Pool + tag per raggruppare |
| Content Library | Non esiste come servizio | Template VM + ISO storage, sync manuale o script |
| Storage I/O Control (SIOC) | Non nativo | cgroups blkio, ionice, I/O scheduling |
| Network I/O Control (NIOC) | Non nativo | Traffic shaping con tc, OVS QoS |
| Host Profiles | Non esiste | Ansible/Terraform per configurazione consistente |
| vSphere Tags | Non esiste (tag semplici in 8.x) | Note field, tag community script |

| Concetto Proxmox | Situazione in VMware | Note |
|-------------------|---------------------|------|
| LXC Container | Non esiste | Proxmox supporta container OS-level oltre a VM |
| ZFS nativo | Non nativo (vSAN diverso) | ZFS integrato in Proxmox con snapshot, compression, send/receive |
| Proxmox Backup Server | Non equivalente diretto | PBS e un prodotto separato ottimizzato per Proxmox |
| SDN (Software Defined Networking) | NSX (licenza separata) | SDN Proxmox incluso, basato su EVPN/VXLAN |
| Ceph integrato | vSAN (licenza separata) | Ceph hyper-converged incluso in Proxmox |

### 6.4 Formati Disco

| Formato | Piattaforma | Thin Provisioning | Snapshot | Note |
|---------|-------------|-------------------|----------|------|
| VMDK (thick eager) | VMware | No | Si (COW) | Spazio pre-allocato, best performance |
| VMDK (thick lazy) | VMware | Parziale | Si | Spazio riservato ma non azzerato |
| VMDK (thin) | VMware | Si | Si | Cresce on-demand |
| qcow2 | Proxmox/KVM | Si (default) | Si (interno) | Formato nativo QEMU, feature-rich |
| raw | Proxmox/KVM | No (a meno di LVM-Thin) | Dipende storage | Massima performance, minimo overhead |
| VHD/VHDX | Hyper-V | Si (VHDX) | Si | Non usato in Proxmox |

```
Conversione formati:
  VMDK → qcow2:   qemu-img convert -f vmdk -O qcow2 disk.vmdk disk.qcow2
  VMDK → raw:      qemu-img convert -f vmdk -O raw disk.vmdk disk.raw
  qcow2 → raw:     qemu-img convert -f qcow2 -O raw disk.qcow2 disk.raw
  raw → qcow2:     qemu-img convert -f raw -O qcow2 disk.raw disk.qcow2
```

---

## 7. Risorse Esterne

### 7.1 Documentazione Ufficiale Proxmox

| Risorsa | URL | Contenuto |
|---------|-----|-----------|
| Proxmox VE Wiki | https://pve.proxmox.com/wiki/ | Documentazione principale, guide, how-to |
| Proxmox VE Admin Guide | https://pve.proxmox.com/pve-docs/pve-admin-guide.html | Manuale completo (PDF disponibile) |
| Proxmox API Reference | https://pve.proxmox.com/pve-docs/api-viewer/ | Documentazione REST API interattiva |
| Proxmox Backup Server | https://pbs.proxmox.com/docs/ | Documentazione PBS |
| Proxmox Forum | https://forum.proxmox.com/ | Community support, discussioni |
| Proxmox Bugtracker | https://bugzilla.proxmox.com/ | Segnalazione bug, feature request |
| Proxmox Git | https://git.proxmox.com/ | Codice sorgente Proxmox |
| Proxmox Training | https://www.proxmox.com/en/training | Corsi ufficiali e certificazione |

### 7.2 Documentazione VMware

| Risorsa | URL | Contenuto |
|---------|-----|-----------|
| VMware Docs | https://docs.vmware.com/ | Documentazione prodotti VMware |
| VMware vSphere Docs | https://docs.vmware.com/en/VMware-vSphere/ | Documentazione vSphere specifica |
| VMware Compatibility Guide | https://www.vmware.com/resources/compatibility/search.php | HCL hardware compatibilita |
| VMware Knowledge Base | https://knowledge.broadcom.com/ | Articoli KB e troubleshooting |
| VMDK Specification | Virtual Disk Format (VMDK) spec | Formato disco VMware |

### 7.3 Documentazione Tecnica di Supporto

| Risorsa | URL / Riferimento | Contenuto |
|---------|-------------------|-----------|
| KVM Documentation | https://www.linux-kvm.org/page/Documents | Documentazione kernel KVM |
| QEMU Documentation | https://www.qemu.org/docs/master/ | Manuale QEMU completo |
| libvirt / virt-v2v | https://libguestfs.org/virt-v2v.1.html | Tool conversione VM |
| ZFS on Linux | https://openzfs.github.io/openzfs-docs/ | Documentazione OpenZFS |
| Ceph Documentation | https://docs.ceph.com/en/latest/ | Documentazione Ceph ufficiale |
| Open vSwitch | https://docs.openvswitch.org/ | Documentazione OVS |
| Corosync | https://corosync.github.io/corosync/ | Cluster engine documentazione |
| Linux Bridge | kernel.org networking docs | Bridge networking Linux |

### 7.4 Libri Consigliati

```
PROXMOX VE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. "Mastering Proxmox" — 4th Edition
   Autore: Wasim Ahmed
   Editore: Packt Publishing
   Focus: Amministrazione Proxmox VE completa
   Livello: Intermedio-Avanzato

2. "Proxmox VE Administration Guide" — Official
   Autore: Proxmox Server Solutions GmbH
   Focus: Manuale ufficiale PDF
   Livello: Tutti i livelli
   Nota: Disponibile gratuitamente sul sito Proxmox

VIRTUALIZZAZIONE E KVM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. "Mastering KVM Virtualization" — 2nd Edition
   Autore: Humble Devassy Chirammal, et al.
   Editore: Packt Publishing
   Focus: KVM/QEMU/libvirt in profondita
   Livello: Avanzato

STORAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. "FreeBSD Mastery: ZFS" / "FreeBSD Mastery: Advanced ZFS"
   Autore: Michael W. Lucas, Allan Jude
   Focus: ZFS approfondito (concetti applicabili a OpenZFS/Linux)
   Livello: Intermedio-Avanzato

5. "Learning Ceph" — 2nd Edition
   Autore: Anthony D'Atri, Vaibhav Bhembre, Karan Singh
   Editore: Packt Publishing
   Focus: Ceph storage cluster
   Livello: Intermedio

LINUX ADMINISTRATION (prerequisiti)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
6. "The Linux Command Line" — 2nd Edition
   Autore: William Shotts
   Focus: CLI Linux completa
   Livello: Principiante-Intermedio
   Nota: Disponibile gratuitamente su linuxcommand.org

7. "UNIX and Linux System Administration Handbook" — 5th Edition
   Autore: Evi Nemeth, et al.
   Focus: Amministrazione di sistema completa
   Livello: Intermedio-Avanzato

NETWORKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
8. "TCP/IP Illustrated, Volume 1" — 2nd Edition
   Autore: W. Richard Stevens, Kevin Fall
   Focus: Protocolli TCP/IP in dettaglio
   Livello: Intermedio-Avanzato
```

### 7.5 Community e Forum

| Risorsa | Tipo | Utilita |
|---------|------|---------|
| Proxmox Forum (forum.proxmox.com) | Forum ufficiale | Supporto community, best practice, troubleshooting |
| Reddit r/Proxmox | Community | Discussioni, consigli, esperienze utenti |
| Reddit r/homelab | Community | Setup lab, hardware consigliato |
| Proxmox Discord / Matrix | Chat | Supporto real-time |
| ServerFault (StackExchange) | Q&A | Domande tecniche server/virtualization |
| Proxmox YouTube Channel | Video | Tutorial e webinar ufficiali |
| Blog "Proxmox VE" (pvecli.xuan.cz) | Blog | Guide pratiche community |

### 7.6 Tool e Utility Utili

| Tool | Scopo | URL/Installazione |
|------|-------|-------------------|
| `qemu-img` | Conversione e gestione immagini disco | `apt install qemu-utils` |
| `virt-v2v` | Conversione VM da VMware a KVM | `apt install virt-v2v` |
| `ovftool` | Export/import OVA/OVF (VMware) | Download da VMware/Broadcom |
| `govc` | CLI client per vSphere API | https://github.com/vmware/govmomi |
| `pvesh` | CLI per Proxmox REST API | Incluso in Proxmox VE |
| `vzdump` | Backup VM e container Proxmox | Incluso in Proxmox VE |
| `proxmox-backup-client` | Client per Proxmox Backup Server | `apt install proxmox-backup-client` |
| `zpool` / `zfs` | Gestione ZFS storage | Incluso in Proxmox VE |
| `ceph` | Gestione Ceph cluster | `pveceph install` |
| `terraform` | Infrastructure as Code | https://www.terraform.io/ |
| `ansible` | Configuration management e automazione | `apt install ansible` |
| `Zabbix` | Monitoring infrastructure | https://www.zabbix.com/ |

### 7.7 Matrice Risorse per Sezione

| Sezione | Risorse Primarie | Risorse Secondarie |
|---------|------------------|--------------------|
| 01 Fondamenti VMware | VMware Docs, KB Broadcom | "Mastering VMware vSphere" |
| 02 Fondamenti Proxmox | PVE Admin Guide, PVE Wiki | "Mastering Proxmox", Forum |
| 03 Storage Avanzato | PVE Wiki (Storage), OpenZFS docs | ZFS book, Ceph docs |
| 04 Networking Avanzato | PVE Wiki (Network), OVS docs | "TCP/IP Illustrated" |
| 05 Assessment | VMware KB, PVE sizing guide | Forum Proxmox (casi reali) |
| 06 Strategie Migrazione | virt-v2v man page, PVE Wiki | Forum, Reddit r/Proxmox |
| 07 Migrazione Networking | PVE Wiki (Network), OVS docs | Linux Bridge docs |
| 08 Migrazione Storage | qemu-img docs, PVE Wiki | ZFS/LVM man pages |
| 09 Scenari Specifici | Forum Proxmox, Reddit | Blog community |
| 10 Cluster e HA | PVE Admin Guide (HA), Corosync docs | "Mastering Proxmox" (cap. HA) |
| 11 Backup e Ripristino | PBS docs, PVE Wiki (Backup) | Forum Proxmox |
| 12 Sicurezza | PVE Wiki (Auth), OWASP | Security hardening guides |
| 13 Monitoraggio | Zabbix docs, PVE Wiki | Grafana docs |
| 14 Automazione | PVE API Reference, Terraform docs | Ansible docs |
| 15 Business | N/A (competenze trasversali) | Case study online |
| 16 Procedure Operative | PVE Wiki, Runbook templates | ITIL/ITSM reference |
| 17 Troubleshooting | PVE Forum, Bugzilla Proxmox | Kernel logs, dmesg docs |

---

## Best Practice per lo Studio

1. **Seguire l'ordine delle fasi** — Le sezioni sono progettate con dipendenze
   progressive. Saltare i fondamenti compromette la comprensione delle fasi
   successive

2. **Laboratorio pratico obbligatorio** — Ogni sezione richiede pratica hands-on.
   La sola lettura non e sufficiente per acquisire competenza operativa

3. **Documentare tutto** — Tenere un quaderno di lab con comandi eseguiti,
   output osservato, errori incontrati e soluzioni trovate

4. **Verificare le milestone** — Completare ogni milestone pratica prima di
   procedere alla fase successiva

5. **Usare ambienti isolati** — Mai esercitarsi su sistemi di produzione.
   Il lab deve essere completamente isolato

6. **Partecipare alla community** — Il forum Proxmox e una risorsa preziosa
   per chiarire dubbi e confrontare approcci

7. **Ripetere le migrazioni** — Eseguire ogni tipo di migrazione almeno 3 volte
   prima di considerarla padroneggiata

8. **Aggiornare le competenze** — Proxmox VE rilascia major version ogni 1-2
   anni. Verificare la documentazione per le novita della versione corrente
