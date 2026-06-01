# Linux Bridge, VLAN e Bonding su Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 1 — Fondamenti · Modulo 04.1 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 02.1 (architettura Proxmox); networking L2/L3 (Ethernet, VLAN 802.1Q, MAC learning); concetti TCP/IP base; modulo 01.2 (per il confronto vSwitch ↔ Linux Bridge).
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. configurare un Linux Bridge in modo coerente con `/etc/network/interfaces`, distinguere bridge VLAN-aware (`bridge-vlan-aware yes`) e bridge "stupido" (port-group-style), e leggere lo stato con `bridge link show` e `bridge vlan show`;
> 2. configurare bonding/LACP secondo le modalita Linux (`active-backup`, `balance-rr`, `802.3ad`, `balance-tlb`, `balance-alb`) e dimensionare la scelta sulla base di throughput vs failover vs cooperazione con lo switch fisico;
> 3. eseguire VLAN trunking via subinterfaces (`eno1.10`) o via VLAN-aware bridge con `bridge-vids`, distinguere VST/VGT/EST anche su Proxmox;
> 4. comprendere quando preferire Open vSwitch (OVS) al Linux Bridge nativo (NIOC-like, OVSDB, OpenFlow), e quando usare l'SDN integrato di Proxmox;
> 5. progettare un layout di rete dedicato per cluster Proxmox a 3+ nodi (mgmt + Corosync + migrazione + VM + storage), con isolamento via VLAN e MTU coerente;
> 6. mappare ogni concetto di networking VMware (vSwitch, dvSwitch, port group, NIC teaming, NIOC) al pendant Proxmox per il modulo 07.2.
> **Tempo stimato:** lettura 90-120 min · lab 180-240 min
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** Proxmox VE 8.x con `ifupdown2` (Linux 6.x bridge driver, bonding driver, 802.1Q stack); per OVS 3.x e SDN PVE 9.x vedi callout «Approfondimento».

## Mappa concettuale

```
+======================================================+
|  Networking su Proxmox — gerarchia                   |
+======================================================+
|                                                      |
|     pNIC                                             |
|     +-------+   +-------+                            |
|     | eno1  |   | eno2  |   <- interfacce fisiche    |
|     +---+---+   +---+---+                            |
|         |           |                                |
|         +-----+-----+                                |
|               |                                      |
|         +-----v------+                               |
|         |   bond0    |   <- aggregazione opzionale   |
|         |  (802.3ad  |                               |
|         |  o active- |                               |
|         |  backup)   |                               |
|         +-----+------+                               |
|               |                                      |
|         +-----v------+                               |
|         |   vmbr0    |   <- Linux Bridge             |
|         |  (vlan-    |      (anche VLAN-aware)       |
|         |   aware)   |                               |
|         +-----+------+                               |
|               |                                      |
|     +---------+--------+                             |
|     |         |        |                             |
|  +--v--+  +--v--+  +--v--+                           |
|  | VM  |  | VM  |  |LXC  |   <- guest, taggati       |
|  +-----+  +-----+  +-----+      via VID per port     |
|                                                      |
|  Alternative parallel:                               |
|   - subinterface VLAN: eno1.10 (no bridge)           |
|   - OVS bridge: vmbr1 (stack OVS 3.x)                |
|   - SDN Proxmox: zone EVPN, zone VLAN, zone QinQ     |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **Bridge VLAN-aware vs bridge "classico".** Senza `bridge-vlan-aware yes`, il bridge passa solo frame untagged; per gestire piu VLAN servono bridge separati (uno per VLAN). Con `bridge-vlan-aware yes` + `bridge-vids 2-4094`, un solo bridge puo gestire VLAN multiple, e si fa tagging per-VM in `qm set --net0 virtio,bridge=vmbr0,tag=100`. *La preferenza in produzione e VLAN-aware*, quasi sempre.
2. **Bonding va capito caso per caso.** `active-backup` non richiede LACP sullo switch e quindi e il fallback sicuro. `802.3ad` (LACP) richiede coordinamento switch + Proxmox + xmit_hash_policy compatibile (tipicamente `layer2+3`). `balance-rr` distribuisce ma riordina pacchetti (penalita TCP). Scelta tipica produzione: 802.3ad con `xmit_hash_policy layer3+4` se lo switch lo supporta.
3. **L'isolamento di rete e via VLAN, non via bridge separati.** L'errore tipico e creare `vmbr-mgmt`, `vmbr-vm`, `vmbr-storage` come bridge separati invece di un bridge VLAN-aware con tagging per VID. Bridge separati moltiplicano la complessita di config; le VLAN si risolvono con un solo bridge + i tag.
4. **MTU coerente, sempre.** Bond, bridge, sub-interface, VM virtio: MTU del segmento *non puo* essere maggiore di quello del physical inferiore. Per jumbo frames end-to-end: NIC 9000 → bond 9000 → bridge 9000 → tag VLAN sub-iface 9000 → guest virtio 9000. Verifica: `ip link show | grep mtu`, `ping -M do -s 8972 <peer>`.
5. **OVS quando serve OpenFlow / SDN; Linux Bridge altrimenti.** OVS porta NIOC-like, OpenFlow programmability, integration con NSX-T-like (OpenStack Neutron). Costo: maggiore complessita, maggior consumo CPU. Per la maggioranza dei cluster Proxmox in PMI/mid-market, Linux Bridge VLAN-aware basta. Per multi-tenant SDN o overlay VXLAN, valutare OVS o l'SDN integrato di Proxmox.

## Indice

1. [Panoramica del Networking Proxmox](#panoramica-del-networking-proxmox)
2. [Linux Bridge: Fondamenti](#linux-bridge-fondamenti)
3. [Configurazione Linux Bridge](#configurazione-linux-bridge)
4. [VLAN su Proxmox VE](#vlan-su-proxmox-ve)
5. [NIC Bonding e Link Aggregation](#nic-bonding-e-link-aggregation)
6. [Configurazione Completa di Produzione](#configurazione-completa-di-produzione)
7. [Confronto VMware vSwitch vs Linux Bridge](#confronto-vmware-vswitch-vs-linux-bridge)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Panoramica del Networking Proxmox

### Architettura di Rete

Proxmox VE si appoggia interamente allo stack di rete Linux. Non esiste un layer di virtualizzazione proprietario come in VMware: il networking è gestito tramite componenti standard del kernel Linux (bridge, VLAN, bonding, netfilter) configurati attraverso `/etc/network/interfaces` o, dalla versione 8.x, tramite l'interfaccia SDN integrata.

Questo approccio presenta vantaggi significativi rispetto a VMware vSphere: trasparenza totale (ogni configurazione è ispezionabile con strumenti Linux standard), nessun vendor lock-in sul layer di rete, e accesso completo alla documentazione del kernel Linux per debugging avanzato.

```
┌───────────��─────────────────────────────────────────────────────────┐
│                  PROXMOX VE — NETWORKING STACK                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   VM/Container Layer                                                 │
│   ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                │
│   │ VM   │  │ VM   │  │ VM   │  │ LXC  │  │ LXC  │                │
│   │ 100  │  │ 101  │  │ 102  │  │ 200  │  │ 201  │                │
│   │ tap  │  │ tap  │  │ tap  │  │ veth │  │ veth │                │
│   └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘                │
│      │         │         │         │         │                      │
│   Virtual Network Layer                                              │
│   ┌──┴─────────┴─────────┴─────────┴─────────┴──────────────────┐  │
│   │                    Linux Bridge (vmbr0)                       │  │
│   │                                                               │  │
│   │  VLAN-aware: sì/no    STP: opzionale    MTU: configurabile   │  │
│   └──────────────────────────────┬────────────────────────────────┘  │
│                                  │                                   │
│   Physical Layer                 │                                   │
│   ┌──────────────────────────────┴────────────────────────────────┐  │
│   │              NIC Fisica (eno1) o Bond (bond0)                 │  │
│   └───────────────────────────────────────────────────────────────┘  │
│                                  │                                   │
│                          ════════╧════════                           │
│                          Switch Fisico / Rete                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Componenti Principali

| Componente | Funzione | Equivalente VMware |
|---|---|---|
| Linux Bridge (`vmbr0`) | Switch virtuale L2 | vSwitch Standard |
| `tap` device | Porta virtuale per VM KVM | vNIC (vmxnet3) |
| `veth` pair | Porta virtuale per container LXC | N/A |
| VLAN sub-interface | Segregazione traffico L2 | Port Group con VLAN ID |
| Bond (`bond0`) | Aggregazione NIC fisiche | NIC Teaming |
| OVS Bridge | Switch virtuale avanzato | dvSwitch (Distributed) |
| Proxmox SDN | Networking software-defined | NSX-T |

### File di Configurazione Principale

Tutta la configurazione di rete Proxmox risiede in un unico file:

```
/etc/network/interfaces
```

Questo file viene letto dal servizio `networking` al boot e può essere ricaricato a caldo (con alcune limitazioni) dalla GUI Proxmox o con `ifreload -a` (pacchetto `ifupdown2`, installato di default).

**Nota critica**: Proxmox usa `ifupdown2` al posto del classico `ifupdown`. Questo è importante perché `ifupdown2` supporta il reload a caldo delle interfacce senza restart completo del networking, funzionalità essenziale in produzione.

```bash
# Verificare che ifupdown2 sia installato
dpkg -l | grep ifupdown2

# Ricaricare la configurazione di rete senza downtime
ifreload -a

# Visualizzare la configurazione corrente
cat /etc/network/interfaces

# Visualizzare lo stato delle interfacce
ip -br link show
ip -br addr show
```

---

## Linux Bridge: Fondamenti

### Cos'è un Linux Bridge

Un Linux Bridge è uno switch Ethernet virtuale implementato nel kernel Linux (modulo `bridge`). Opera a livello 2 (data link) dello stack OSI: apprende MAC address, inoltra frame Ethernet tra le porte connesse, e supporta STP (Spanning Tree Protocol) per la prevenzione di loop.

In Proxmox, ogni bridge (`vmbr0`, `vmbr1`, etc.) è equivalente a un **vSwitch Standard** in VMware ESXi. Le VM si connettono al bridge tramite interfacce `tap` (tunnel application), mentre i container LXC usano coppie `veth` (virtual Ethernet).

```
┌─────────────────────────────────────────────────────────────┐
│                LINUX BRIDGE — FUNZIONAMENTO                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frame Ethernet in ingresso                                  │
│          │                                                   │
│          ▼                                                   │
│  ┌───────────────────────────┐                               │
│  │  1. Learning              │  Impara MAC sorgente +        │
│  │     (MAC Table Update)    │  porta di ingresso            │
│  └───────────┬───────────────┘                               │
│              │                                               │
│              ▼                                               │
│  ┌───────────────────────────┐                               │
│  │  2. Lookup                │  Cerca MAC destinazione       │
│  │     (FDB — Forwarding DB) │  nella tabella                │
│  └───────────┬───────────────┘                               │
│              │                                               │
│        ┌─────┴─────┐                                        │
│        │           │                                        │
│    MAC noto    MAC ignoto                                    │
│        │           │                                        │
│        ▼           ▼                                        │
│  ┌──────────┐  ┌──────────┐                                 │
│  │ Forward  │  │  Flood   │  Invia su tutte le porte        │
│  │ (unicast)│  │(broadcast│  (tranne quella di ingresso)    │
│  └──────────┘  └──────────┘                                 │
│                                                              │
│  FDB (Forwarding Database):                                  │
│  ┌────────────────────────────────────────────┐              │
│  │  MAC Address       │ Porta      │ Aging    │              │
│  │  aa:bb:cc:dd:ee:01 │ tap100i0   │ 120s     │              │
│  │  aa:bb:cc:dd:ee:02 │ tap101i0   │ 85s      │              │
│  │  aa:bb:cc:dd:ee:03 │ eno1       │ 200s     │              │
│  └────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### Bridge vs NAT

Proxmox supporta due modalità di connessione per le VM:

| Modalità | Descrizione | Quando usarla |
|---|---|---|
| **Bridge** (default) | VM connessa direttamente al bridge L2, IP nella stessa subnet della rete fisica | Produzione, server, accesso diretto alla rete |
| **NAT** | VM dietro NAT del host Proxmox, IP privato, traffico mascherato | Lab isolati, test, ambienti senza IP disponibili |

**In produzione si usa sempre il bridge**. NAT introduce latenza, complessità nel port forwarding, e impedisce comunicazioni dirette in ingresso verso la VM.

---

## Configurazione Linux Bridge

### Bridge Base (Post-Installazione)

Dopo l'installazione di Proxmox VE, il sistema crea automaticamente un bridge `vmbr0` collegato alla prima NIC fisica:

```ini
# /etc/network/interfaces — Configurazione default post-installazione

auto lo
iface lo inet loopback

# NIC fisica — NON ha indirizzo IP assegnato
auto eno1
iface eno1 inet manual

# Bridge — ha l'indirizzo IP del host Proxmox
auto vmbr0
iface vmbr0 inet static
    address 10.10.10.11/24
    gateway 10.10.10.1
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
```

| Parametro | Significato | Valore consigliato |
|---|---|---|
| `bridge-ports` | NIC fisiche connesse al bridge | NIC di management |
| `bridge-stp` | Spanning Tree Protocol | `off` per single-uplink, `on` per topologie ridondanti |
| `bridge-fd` | Forward delay (secondi) | `0` se STP è off |

**Nota importante**: la NIC fisica (`eno1`) è configurata come `inet manual` — non ha IP proprio. L'indirizzo IP viene assegnato al bridge `vmbr0`. Questo è analogo a come in VMware l'IP di management è sul VMkernel port (`vmk0`), non sulla NIC fisica.

### Creare un Secondo Bridge (Rete VM Separata)

Scenario comune: separare il traffico di management dal traffico delle VM.

```ini
# Bridge per management (già esistente)
auto vmbr0
iface vmbr0 inet static
    address 10.10.10.11/24
    gateway 10.10.10.1
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0

# Bridge per traffico VM su seconda NIC fisica
auto eno2
iface eno2 inet manual

auto vmbr1
iface vmbr1 inet manual
    bridge-ports eno2
    bridge-stp off
    bridge-fd 0
```

`vmbr1` non ha indirizzo IP sul host perché è dedicato esclusivamente al traffico delle VM. Le VM connesse a `vmbr1` comunicano tra loro e con la rete fisica collegata a `eno2`, ma l'host Proxmox non partecipa a quella subnet.

### Bridge Interno (Senza NIC Fisica)

Per creare una rete isolata tra VM senza accesso alla rete fisica:

```ini
# Bridge interno — nessuna porta fisica
auto vmbr99
iface vmbr99 inet manual
    bridge-ports none
    bridge-stp off
    bridge-fd 0
```

Questo è equivalente a un **vSwitch VMware senza uplink fisici**: le VM connesse comunicano solo tra loro. Utile per segmenti di rete interni (es. backend database non esposto).

### Creare Bridge dalla GUI Proxmox

1. **Datacenter → Node → System → Network**
2. **Create → Linux Bridge**
3. Compilare:
   - Name: `vmbr1`
   - Bridge ports: `eno2` (o lasciare vuoto per bridge interno)
   - VLAN aware: selezionare se si usano VLAN
   - IP Address / CIDR: opzionale (solo se il host deve avere un IP su questa rete)
4. **Apply Configuration** (esegue `ifreload -a`)

### Comandi Diagnostici per Bridge

```bash
# === STATO BRIDGE ===
# Elenco bridge e porte connesse
bridge link show

# Dettaglio specifico bridge
bridge link show dev vmbr0

# Forwarding Database (tabella MAC)
bridge fdb show br vmbr0

# Statistiche bridge
ip -s link show vmbr0

# === STATO INTERFACCE ===
# Tutte le interfacce con stato e IP
ip -br addr show

# Solo interfacce UP
ip -br link show up

# Dettaglio singola interfaccia
ip -d link show vmbr0

# === VERIFICA CONNETTIVITÀ ===
# Dalla prospettiva dell'host
ping -c 3 10.10.10.1

# Verificare ARP table
ip neigh show dev vmbr0

# Verificare routing
ip route show

# === STP (se abilitato) ===
bridge stp show
brctl showstp vmbr0    # richiede bridge-utils
```

---

## VLAN su Proxmox VE

### Concetti VLAN nella Migrazione

In VMware, le VLAN sono gestite tramite **Port Group** configurati sul vSwitch con un VLAN ID. Le VM vengono assegnate al Port Group che corrisponde alla VLAN desiderata.

In Proxmox, ci sono due approcci per le VLAN, con uno decisamente superiore all'altro:

| Approccio | Descrizione | Raccomandato |
|---|---|---|
| **VLAN-aware bridge** | Un singolo bridge gestisce tutte le VLAN; il VLAN tag è impostato per-VM | **Sì** (default dalla 7.x) |
| **Legacy (un bridge per VLAN)** | Un bridge separato per ogni VLAN, con sub-interface | No (legacy, più complesso) |

### VLAN-Aware Bridge (Metodo Raccomandato)

Il VLAN-aware bridge è l'equivalente moderno di un **dvSwitch VMware con trunk VLAN**. Un singolo bridge gestisce il trunking e ogni VM specifica il proprio VLAN tag nella configurazione della sua interfaccia di rete.

```
┌─────────────────────────────────────────────────────────────────────┐
│              VLAN-AWARE BRIDGE — ARCHITETTURA                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   VM 100         VM 101         VM 102         VM 103                │
│   VLAN 10        VLAN 20        VLAN 10        VLAN 30               │
│   ┌──────┐       ┌──────┐       ┌──────┐       ┌──────┐             │
│   │ eth0 │       │ eth0 │       │ eth0 │       │ eth0 │             │
│   │tag=10│       │tag=20│       │tag=10│       │tag=30│             │
│   └──┬───┘       └──┬───┘       └──┬───┘       └──┬───┘             │
│      │              │              │              │                   │
│   ┌──┴──────────────┴──────────────┴──────────────┴──────────────┐  │
│   │                                                               │  │
│   │              vmbr0 (VLAN-aware bridge)                        │  │
│   │                                                               │  │
│   │  bridge-vlan-aware yes                                        │  │
│   │  bridge-vids 2-4094 (accetta tutti i VLAN tag)               │  │
│   │                                                               │  │
│   │  Il bridge aggiunge/rimuove tag 802.1Q in base               │  │
│   │  alla configurazione per-VM                                   │  │
│   │                                                               │  │
│   └──────────────────────────┬────────────────────────────────────┘  │
│                              │ trunk (tagged: 10,20,30)              │
│                              │                                       │
│   ┌──────────────────────────┴────────────────────────────────────┐  │
│   │                    eno1 (NIC fisica)                           │  │
│   └───────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                     ═════════╧═════════                               │
│                     Switch Fisico                                     │
│                     (porta trunk: VLAN 10,20,30)                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Configurazione `/etc/network/interfaces`**:

```ini
auto eno1
iface eno1 inet manual

auto vmbr0
iface vmbr0 inet static
    address 10.10.10.11/24
    gateway 10.10.10.1
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 2-4094
```

Il parametro chiave è `bridge-vlan-aware yes`. Con questa opzione:
- Il bridge gestisce il tagging/untagging 802.1Q
- Ogni VM specifica il suo VLAN tag nella configurazione hardware → Network
- La NIC fisica deve essere collegata a una **porta trunk** sullo switch fisico
- `bridge-vids 2-4094` permette tutti i VLAN ID (restringere in produzione)

**Assegnare VLAN tag a una VM** (GUI o CLI):

```bash
# Via qm (CLI)
qm set 100 -net0 virtio,bridge=vmbr0,tag=10
qm set 101 -net0 virtio,bridge=vmbr0,tag=20

# Verificare configurazione VM
qm config 100 | grep net
# net0: virtio=AA:BB:CC:DD:EE:01,bridge=vmbr0,tag=10
```

Dalla GUI: **VM → Hardware → Network Device → VLAN Tag**.

### Proxmox Host su una VLAN Specifica

Se il management IP dell'host Proxmox deve risiedere su una VLAN specifica (es. VLAN 10 management):

```ini
auto eno1
iface eno1 inet manual

auto vmbr0
iface vmbr0 inet static
    address 10.10.10.11/24
    gateway 10.10.10.1
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 2-4094
    bridge-pvid 10
```

`bridge-pvid 10` imposta il **PVID** (Port VLAN ID) del bridge — il traffico untagged in ingresso/uscita viene associato alla VLAN 10. Questo è equivalente alla **native VLAN** sullo switch fisico.

### Restringere i VLAN ID Ammessi

In produzione, non è consigliabile accettare tutti i VLAN (2-4094). Limitare ai VLAN effettivamente utilizzati:

```ini
auto vmbr0
iface vmbr0 inet static
    address 10.10.10.11/24
    gateway 10.10.10.1
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 10 20 30 40 100
    bridge-pvid 10
```

### Legacy VLAN (Un Bridge per VLAN)

**Sconsigliato per nuove installazioni**, ma documentato per completezza e per comprendere ambienti legacy.

In questo approccio, si creano sub-interface VLAN sulla NIC fisica e un bridge per ciascuna:

```ini
auto eno1
iface eno1 inet manual

# VLAN 10 — Management
auto eno1.10
iface eno1.10 inet manual

auto vmbr10
iface vmbr10 inet static
    address 10.10.10.11/24
    gateway 10.10.10.1
    bridge-ports eno1.10
    bridge-stp off
    bridge-fd 0

# VLAN 20 — Server
auto eno1.20
iface eno1.20 inet manual

auto vmbr20
iface vmbr20 inet manual
    bridge-ports eno1.20
    bridge-stp off
    bridge-fd 0

# VLAN 30 — Storage
auto eno1.30
iface eno1.30 inet manual

auto vmbr30
iface vmbr30 inet manual
    bridge-ports eno1.30
    bridge-stp off
    bridge-fd 0
```

**Problema**: con 20 VLAN servono 20 bridge e 20 sub-interface. Difficile da gestire e da mantenere. Il VLAN-aware bridge elimina completamente questa complessità.

### Comandi Diagnostici VLAN

```bash
# Verificare VLAN-aware su un bridge
bridge vlan show

# Output esempio:
# port              vlan-id
# eno1              1 PVID Egress Untagged
#                   10
#                   20
#                   30
# vmbr0             1 PVID Egress Untagged
#                   10
#                   20
#                   30
# tap100i0          10 PVID Egress Untagged
# tap101i0          20 PVID Egress Untagged

# Verificare tagging su interfaccia
bridge vlan show dev eno1

# Verificare sub-interface VLAN (legacy)
cat /proc/net/vlan/config

# Catturare traffico VLAN con tcpdump
tcpdump -i eno1 -e -nn vlan 10
tcpdump -i vmbr0 -e -nn vlan

# Statistiche VLAN
ip -s link show eno1.10    # solo legacy
```

---

## NIC Bonding e Link Aggregation

### Panoramica

Il NIC bonding (chiamato anche **NIC teaming** in VMware, **link aggregation** in ambito networking, **EtherChannel** in Cisco, **Port Channel** in terminologia generica) aggrega più NIC fisiche in un'unica interfaccia logica per:

1. **Ridondanza** — se una NIC fallisce, il traffico continua sull'altra
2. **Bandwidth aggregation** — (solo con alcune modalità) somma la banda disponibile
3. **Load balancing** — distribuzione del traffico tra le NIC

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NIC BONDING — ARCHITETTURA                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                    vmbr0 (bridge)                             │  │
│   └─────────────────────────┬────────────────────────────────────┘  │
│                             │                                        │
│   ┌─────────────────────────┴────────────────────────────────────┐  │
│   │                    bond0 (bonding)                            │  │
│   │                                                               │  │
│   │  Mode: 802.3ad (LACP)                                        │  │
│   │  Hash: layer3+4 (src/dst IP + port)                          │  │
│   │  LACPDU rate: fast (1s)                                       │  │
│   └──────────────┬────────────────────┬──────────────────────────┘  │
│                  │                    │                               │
│   ┌──────────────┴──────┐  ┌─────────┴──────────────┐               │
│   │    eno1 (slave)     │  │    eno2 (slave)        │               │
│   │    1 Gbps / UP      │  │    1 Gbps / UP         │               │
│   └──────────┬──────────┘  └──────────┬─────────────┘               │
│              │                        │                              │
│       ══════╧════════════════════════╧══════                        │
│       Switch (LAG / Port Channel configurato)                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Modalità di Bonding

Linux supporta 7 modalità di bonding. Le più rilevanti per Proxmox:

| Mode | Nome | Requisiti Switch | Failover | Bandwidth | Uso Tipico |
|---|---|---|---|---|---|
| **0** | balance-rr | Etherchannel statico | Sì | Aggregata | Lab, non per produzione (riordino pacchetti) |
| **1** | active-backup | Nessuno | Sì | Singola NIC | **Produzione senza LACP** — scelta più sicura |
| **2** | balance-xor | Etherchannel statico | Sì | Aggregata | Alternativa a LACP |
| **3** | broadcast | Nessuno | Sì | Singola NIC | Scenari fault-tolerance specializzati |
| **4** | 802.3ad (LACP) | **LACP sullo switch** | Sì | Aggregata | **Produzione con switch managed** — scelta ottimale |
| **5** | balance-tlb | Nessuno | Sì | TX aggregata | Senza supporto switch LACP |
| **6** | balance-alb | Nessuno | Sì | Aggregata (con limiti) | Senza supporto switch, migliore di mode 1 |

**Raccomandazione per produzione**:
- Se lo switch supporta LACP: **mode 4 (802.3ad)** — aggregazione reale con negoziazione
- Se lo switch NON supporta LACP: **mode 1 (active-backup)** — failover semplice e affidabile

### Confronto con VMware NIC Teaming

| Aspetto | VMware NIC Teaming | Linux Bonding |
|---|---|---|
| Configurazione | Per-vSwitch (GUI/PowerCLI) | `/etc/network/interfaces` |
| Failover detection | Beacon probing + link status | MII monitoring (link) + ARP monitoring |
| Load balancing | Route based on originating virtual port / IP hash / Physical NIC load | mode 0-6 (più opzioni) |
| LACP | Solo su dvSwitch (Enterprise Plus) | mode 4, disponibile ovunque |
| Notify switches | Sì (RARP on failover) | Sì (gratuitous ARP) |

**Nota migrazione**: VMware NIC Teaming con "Route based on originating virtual port" non ha un equivalente diretto. Il più simile in Linux è `mode 1` (active-backup) per semplicità o `mode 4` (LACP) per aggregazione effettiva.

### Configurazione Bonding + Bridge

#### Mode 1 (Active-Backup) — Senza LACP

```ini
# /etc/network/interfaces

auto eno1
iface eno1 inet manual

auto eno2
iface eno2 inet manual

# Bond con failover attivo-passivo
auto bond0
iface bond0 inet manual
    bond-slaves eno1 eno2
    bond-miimon 100
    bond-mode active-backup
    bond-primary eno1

# Bridge collegato al bond
auto vmbr0
iface vmbr0 inet static
    address 10.10.10.11/24
    gateway 10.10.10.1
    bridge-ports bond0
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 10 20 30
```

| Parametro Bond | Significato |
|---|---|
| `bond-slaves` | NIC fisiche aggregate |
| `bond-miimon` | Intervallo monitoraggio link (ms) — 100ms è standard |
| `bond-mode` | Modalità bonding |
| `bond-primary` | NIC preferita come attiva (mode 1) |

#### Mode 4 (802.3ad LACP) — Con Switch Managed

```ini
auto eno1
iface eno1 inet manual

auto eno2
iface eno2 inet manual

# Bond LACP
auto bond0
iface bond0 inet manual
    bond-slaves eno1 eno2
    bond-miimon 100
    bond-mode 802.3ad
    bond-lacp-rate fast
    bond-xmit-hash-policy layer3+4

# Bridge collegato al bond
auto vmbr0
iface vmbr0 inet static
    address 10.10.10.11/24
    gateway 10.10.10.1
    bridge-ports bond0
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 10 20 30
    bridge-pvid 10
```

| Parametro LACP | Significato | Valore consigliato |
|---|---|---|
| `bond-lacp-rate` | Frequenza invio LACPDU | `fast` (1s) per failover rapido, `slow` (30s) per meno overhead |
| `bond-xmit-hash-policy` | Algoritmo distribuzione traffico | `layer3+4` (IP + porta) per distribuzione ottimale |

**Configurazione lato switch** (esempio Cisco):

```
! Configurazione switch Cisco per LACP
interface range GigabitEthernet0/1-2
  channel-group 1 mode active
  !
interface Port-channel1
  switchport mode trunk
  switchport trunk allowed vlan 10,20,30
  switchport trunk native vlan 10
```

### Bonding con Dual Switch (Failover Cross-Switch)

Per massima resilienza, collegare ogni NIC a uno switch diverso:

```
┌──────────┐     ┌──────────┐
│ Switch A │     │ Switch B │
└────┬─────┘     └────┬─────┘
     │                │
   eno1             eno2
     │                │
┌────┴────────────────┴────┐
│        bond0             │
│   mode: active-backup    │
│   (LACP non possibile    │
│    senza MLAG/vPC)       │
└──────────┬───────────────┘
           │
      ┌────┴────┐
      │  vmbr0  │
      └─────────┘
```

Con switch diversi, **non usare LACP** (mode 4) a meno che gli switch supportino MLAG/vPC/MC-LAG (multi-chassis link aggregation). Usare `active-backup` (mode 1).

### Comandi Diagnostici Bonding

```bash
# === STATO BOND ===
# Stato completo del bond
cat /proc/net/bonding/bond0

# Output chiave:
# Bonding Mode: IEEE 802.3ad Dynamic link aggregation
# MII Status: up
# Aggregator ID: 1
# Slave Interface: eno1
#   MII Status: up
#   Speed: 1000 Mbps
#   Aggregator ID: 1
# Slave Interface: eno2
#   MII Status: up
#   Speed: 1000 Mbps
#   Aggregator ID: 1

# Stato sintetico
ip -br link show type bond
ip -br link show master bond0

# Statistiche per-slave
ip -s link show eno1
ip -s link show eno2

# === LACP (mode 4) ===
# Stato LACP
cat /proc/net/bonding/bond0 | grep -A 5 "802.3ad"

# Verificare LACPDU
tcpdump -i eno1 -e -nn ether proto 0x8809

# === TEST FAILOVER ===
# Disabilitare uno slave (simulare guasto NIC)
ip link set eno2 down

# Verificare che il bond sia ancora UP
cat /proc/net/bonding/bond0 | grep "MII Status"

# Ripristinare
ip link set eno2 up
```

---

## Configurazione Completa di Produzione

### Scenario: Server con 4 NIC, Management + VM + Storage Separati

Questa configurazione rappresenta un setup enterprise realistico per un nodo Proxmox cluster:

```
┌─────────────────────────────────────────────────────────────────────┐
│                CONFIGURAZIONE PRODUCTION-GRADE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  bond0 (LACP) ── vmbr0 (VLAN-aware)                                │
│  ├── eno1 ──┐                                                       │
│  └── eno2 ──┘    ├── PVID 10: Management (10.10.10.0/24)           │
│                  ├── VLAN 20: VM Production (10.10.20.0/24)         │
│                  ├── VLAN 30: VM Development (10.10.30.0/24)        │
│                  └── VLAN 40: DMZ (10.10.40.0/24)                   │
│                                                                      │
│  bond1 (LACP) ── vmbr1 (storage dedicato)                           │
│  ├── eno3 ──┐                                                       │
│  └── eno4 ──┘    └── 10.10.50.0/24 (storage network — NFS/iSCSI)  │
│                                                                      │
│  vmbr99 (interno) ── rete inter-VM isolata (nessuna NIC fisica)     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

```ini
# /etc/network/interfaces — CONFIGURAZIONE PRODUZIONE
# Nodo: pve1.lab.local
# Data: 2026-04-11

# === LOOPBACK ===
auto lo
iface lo inet loopback

# === NIC FISICHE ===
auto eno1
iface eno1 inet manual

auto eno2
iface eno2 inet manual

auto eno3
iface eno3 inet manual

auto eno4
iface eno4 inet manual

# === BOND 0: Management + VM Traffic (LACP) ===
auto bond0
iface bond0 inet manual
    bond-slaves eno1 eno2
    bond-miimon 100
    bond-mode 802.3ad
    bond-lacp-rate fast
    bond-xmit-hash-policy layer3+4

# === BRIDGE 0: Management + VM (VLAN-aware) ===
auto vmbr0
iface vmbr0 inet static
    address 10.10.10.11/24
    gateway 10.10.10.1
    bridge-ports bond0
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 10 20 30 40
    bridge-pvid 10

# === BOND 1: Storage Network (LACP) ===
auto bond1
iface bond1 inet manual
    bond-slaves eno3 eno4
    bond-miimon 100
    bond-mode 802.3ad
    bond-lacp-rate fast
    bond-xmit-hash-policy layer3+4
    mtu 9000

# === BRIDGE 1: Storage (no VLAN, jumbo frames) ===
auto vmbr1
iface vmbr1 inet static
    address 10.10.50.11/24
    bridge-ports bond1
    bridge-stp off
    bridge-fd 0
    mtu 9000

# === BRIDGE INTERNO (isolato, no NIC fisica) ===
auto vmbr99
iface vmbr99 inet manual
    bridge-ports none
    bridge-stp off
    bridge-fd 0

# === DNS ===
# Configurato in /etc/resolv.conf o /etc/hosts
# nameserver gestito dalla GUI: Datacenter → DNS
```

### Jumbo Frames (MTU 9000)

La rete storage beneficia di jumbo frames per ridurre l'overhead dei pacchetti durante trasferimenti bulk (NFS, iSCSI, Ceph, migration traffic):

```bash
# Verificare MTU corrente
ip link show bond1 | grep mtu
ip link show vmbr1 | grep mtu

# Test MTU end-to-end (dal host Proxmox al NAS/SAN)
ping -M do -s 8972 10.10.50.1
# -M do = don't fragment
# -s 8972 = payload (8972 + 28 byte header = 9000 MTU)
# Se timeout → jumbo frames non supportato end-to-end

# Il MTU deve essere coerente su TUTTO il percorso:
# NIC → bond → bridge → switch → destinazione
```

**Attenzione**: impostare `mtu 9000` su NIC, bond E bridge. Se anche uno solo degli anelli non supporta jumbo frames, si verificheranno packet loss silenziosi o frammentazione.

---

## Confronto VMware vSwitch vs Linux Bridge

### Mapping Concettuale Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│           VMware vSphere             →     Proxmox VE               │
├──────────────────────────────────────┬──────────────────────────────┤
│                                      │                              │
│  vSwitch Standard                    │  Linux Bridge (vmbr0)        │
│  ├── Port Group "Management"         │  ├── PVID (native VLAN)      │
│  ├── Port Group "VLAN 20"            │  ├── VM tag=20               │
│  ├── Port Group "VLAN 30"            │  ├── VM tag=30               │
│  └── NIC Teaming                     │  └── bond (mode 1/4)         │
│                                      │                              │
│  dvSwitch (Distributed)              │  OVS Bridge / Proxmox SDN   │
│  ├── Distributed Port Group          │  ├── VNet (SDN)              │
│  ├── NIOC (Network I/O Control)      │  ├── tc (traffic control)    │
│  ├── NetFlow/IPFIX                   │  ├── OVS sFlow               │
│  └── LACP                            │  └── bond mode 4 (LACP)     │
│                                      │                              │
│  VMkernel Port (vmk0, vmk1...)       │  IP su bridge (vmbr0)        │
│  ├── Management                      │  ├── address su vmbr0        │
│  ├── vMotion                         │  ├── Migration network       │
│  ├── vSAN                            │  ├── Corosync ring           │
│  └── iSCSI / NFS                     │  └── Storage network         │
│                                      │                              │
│  NSX-T / NSX-V                       │  Proxmox SDN + OVS          │
│  ├── Logical Switch                  │  ├── Zone VXLAN/EVPN        │
│  ├── Distributed Firewall            │  ├── Proxmox Firewall        │
│  └── Micro-segmentation             │  └── nftables / Security     │
│                                      │      Groups                  │
│                                      │                              │
└──────────────────────────────────────┴──────────────────────────────┘
```

### Differenze Operative Chiave

| Aspetto | VMware | Proxmox |
|---|---|---|
| **Configurazione** | GUI vSphere Client, PowerCLI | `/etc/network/interfaces`, GUI, API |
| **Persistenza** | Database vCenter | File testo `/etc/network/interfaces` |
| **Apply changes** | Immediato (rischio lock-out) | `ifreload -a` con possibilità di rollback |
| **Rete management** | VMkernel port dedicato | IP diretto sul bridge |
| **VLAN** | Port Group con VLAN ID | VLAN-aware bridge + tag per VM |
| **Trunk** | Port Group VLAN 4095 (all) | `bridge-vids` con lista esplicita |
| **NIC teaming** | Per-vSwitch, policy-based | Bond Linux, per-bond |
| **Monitoring** | vCenter Performance charts | `ip`, `bridge`, `ethtool`, `tcpdump` |
| **Firewall** | NSX DFW (licenza) | Integrato, gratuito (nftables) |
| **Max porte** | 4088 per vSwitch | Nessun limite pratico |

---

## Best Practices

### Networking Proxmox in Produzione

1. **Separare management e VM traffic** — Usare bond + VLAN-aware bridge con PVID per management e VLAN tag per le VM. Mai mescolare traffico critico su un bridge senza VLAN.

2. **Separare storage traffic** — Dedicare NIC fisiche (e bond) alla rete storage. Il traffico NFS/iSCSI/Ceph compete con il traffico VM se condivide la stessa NIC. Usare jumbo frames (MTU 9000) sulla rete storage.

3. **Usare LACP dove possibile** — Mode 4 con `xmit-hash-policy layer3+4` fornisce la distribuzione migliore. Se lo switch non supporta LACP, usare `active-backup` (mode 1), mai `balance-rr` (mode 0) in produzione.

4. **VLAN-aware bridge sempre** — Non creare bridge legacy per ogni VLAN. Un singolo VLAN-aware bridge con `bridge-vids` è più pulito, più performante, e più facile da gestire.

5. **Restringere bridge-vids** — Non usare `2-4094` in produzione. Elencare esplicitamente i VLAN ID necessari.

6. **Coerenza MTU** — Se si usano jumbo frames, verificare che MTU 9000 sia configurato su NIC, bond, bridge, switch, e dispositivo di destinazione. Un singolo anello con MTU 1500 causa problemi difficili da diagnosticare.

7. **Monitorare il bonding** — Implementare alert per bond degradation (uno slave down). Il bond continua a funzionare, ma senza ridondanza.

8. **Documentare la configurazione** — Il file `/etc/network/interfaces` È la documentazione. Aggiungere commenti per spiegare la funzione di ogni componente.

9. **Backup pre-modifica** — Prima di modificare `/etc/network/interfaces`:
   ```bash
   cp /etc/network/interfaces /etc/network/interfaces.bak.$(date +%Y%m%d%H%M)
   ```

10. **Testare con ifreload** — Dopo modifiche, usare `ifreload -a` anziché riavviare il servizio networking. Se qualcosa va storto con accesso remoto, un reboot ripristina la configurazione precedente (a meno che non sia stata applicata).

### Checklist Pre-Migrazione Networking

```
┌───────────────────────────────────────────────────────────────────┐
│          CHECKLIST NETWORKING PRE-MIGRAZIONE                       │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  [ ] Inventario VLAN VMware completato (ID, nome, subnet, uso)   │
│  [ ] Mappatura vSwitch/dvSwitch → bridge Proxmox definita         │
│  [ ] NIC Teaming policy documentata e tradotta in bond mode       │
│  [ ] Porte switch fisiche configurate come trunk                  │
│  [ ] VLAN ammesse sulle porte trunk corrispondono a bridge-vids  │
│  [ ] MTU coerente su tutto il percorso (standard o jumbo)        │
│  [ ] IP management Proxmox verificato raggiungibile              │
│  [ ] DNS risolve i nomi dei nodi Proxmox                          │
│  [ ] Rete storage separata e funzionante                          │
│  [ ] Rete cluster/Corosync pianificata (separata o condivisa)    │
│  [ ] Firewall regole pianificate per traffico inter-VM            │
│  [ ] Test di connettività da ogni VLAN verificato                 │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Problema: VM Non Raggiunge la Rete

```bash
# 1. Verificare che il bridge sia UP
ip link show vmbr0
# Deve mostrare: state UP

# 2. Verificare che la NIC fisica sia collegata al bridge
bridge link show
# Deve mostrare eno1 (o bond0) come membro di vmbr0

# 3. Verificare che la VM sia connessa al bridge corretto
qm config <vmid> | grep net
# Verificare bridge=vmbr0 e tag corretto

# 4. Verificare VLAN tag
bridge vlan show
# Il tap device della VM deve avere il VLAN corretto come PVID

# 5. Verificare traffico sul bridge
tcpdump -i vmbr0 -e -nn host <IP_VM>
# Se nessun traffico → problema nella VM o nella connessione al bridge

# 6. Verificare traffico sulla NIC fisica
tcpdump -i eno1 -e -nn vlan <VLAN_ID>
# Se traffico presente qui ma non sul bridge → problema bridge
# Se traffico assente → problema switch fisico o cablaggio
```

### Problema: Bond Degradato (Uno Slave Down)

```bash
# Verificare stato bond
cat /proc/net/bonding/bond0

# Cercare "MII Status: down" su uno slave
# Cause comuni:
# - Cavo scollegato
# - Porta switch disabilitata
# - Speed/duplex mismatch

# Verificare log
journalctl -u networking --since "1 hour ago" | grep bond
dmesg | grep -i "link down\|link up"

# Verificare parametri NIC
ethtool eno1    # speed, duplex, link detected
ethtool eno2
```

### Problema: VLAN Non Funziona

```bash
# 1. Verificare che il bridge sia VLAN-aware
ip -d link show vmbr0 | grep vlan_filtering
# Deve mostrare: vlan_filtering 1

# 2. Verificare VLAN ammesse
bridge vlan show dev vmbr0
bridge vlan show dev eno1
# Il VLAN ID deve essere presente su ENTRAMBI

# 3. Verificare configurazione switch
# La porta switch collegata a eno1 deve essere in modalità trunk
# con i VLAN corretti ammessi

# 4. Test con tcpdump
tcpdump -i eno1 -e -nn vlan <VLAN_ID>
# Se non si vedono pacchetti tagged → switch non invia quel VLAN

# 5. Verificare PVID (native VLAN)
bridge vlan show | grep PVID
# Il PVID deve corrispondere alla native VLAN dello switch
```

### Problema: Performance di Rete Degradata

```bash
# 1. Verificare speed/duplex NIC
ethtool eno1 | grep -i "speed\|duplex"
# Speed: 1000Mb/s, Duplex: Full — atteso
# Se 100Mb/s o Half → autonegotiation fallita o cavo Cat5

# 2. Verificare errori NIC
ethtool -S eno1 | grep -i "error\|drop\|collision"
# Errori significativi indicano problemi fisici

# 3. Verificare ring buffer
ethtool -g eno1
# Se rx/tx sono al massimo e ci sono drop → aumentare
ethtool -G eno1 rx 4096 tx 4096

# 4. Verificare CPU softirq (rete satura)
mpstat -P ALL 1 5
# %soft alto su una CPU → traffico di rete che satura un core

# 5. Benchmark rete
iperf3 -s              # su un nodo
iperf3 -c 10.10.10.12  # dall'altro nodo
# Aspettarsi ~940 Mbps su 1G, ~9.4 Gbps su 10G

# 6. Verificare MTU mismatch (causa packet loss silenziosa)
ping -M do -s 1472 <destinazione>    # MTU 1500
ping -M do -s 8972 <destinazione>    # MTU 9000
```

### Problema: Connettività Persa Dopo Modifica Interfaces

```bash
# Se hai accesso fisico o IPMI/iDRAC/iLO:

# 1. Ripristinare backup
cp /etc/network/interfaces.bak.<timestamp> /etc/network/interfaces

# 2. Riavviare networking
systemctl restart networking

# 3. Se non hai backup, configurazione minimale di emergenza:
cat > /etc/network/interfaces << 'EOF'
auto lo
iface lo inet loopback

auto eno1
iface eno1 inet manual

auto vmbr0
iface vmbr0 inet static
    address 10.10.10.11/24
    gateway 10.10.10.1
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
EOF

systemctl restart networking
```

**Prevenzione**: prima di modifiche rischiose su nodi remoti, schedulare un ripristino automatico:

```bash
# Schedulare ripristino tra 5 minuti (se la nuova config funziona, cancellare)
cp /etc/network/interfaces /etc/network/interfaces.new
cp /etc/network/interfaces.bak /etc/network/interfaces.safety

echo "cp /etc/network/interfaces.safety /etc/network/interfaces && systemctl restart networking" | at now + 5 min

# Applicare la nuova configurazione
cp /etc/network/interfaces.new /etc/network/interfaces
ifreload -a

# Se tutto funziona, cancellare il ripristino schedulato
atrm $(atq | tail -1 | awk '{print $1}')
```

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — SDN integrato di Proxmox VE.** Da PVE 7.x e disponibile (in `pve-manager` con plugin `pve-sdn`) un sottosistema SDN che permette di definire **zone** (VLAN, QinQ, VXLAN, EVPN), **vnet** (network logiche tra zone), e **subnets** (IPAM, DHCP). E il pendant funzionale di NSX-T per i casi di multi-tenant overlay e routing distribuito. In PVE 9.x e considerato production-ready per la maggior parte degli use case. Configurazione persistente in `/etc/pve/sdn/`. Limiti: non sostituisce un firewall stateful avanzato, l'integrazione BGP per EVPN richiede `frr` configurato sui nodi. Riferimento: [`PVE-SDN`] `https://pve.proxmox.com/wiki/Software-Defined_Network`.

> **Errore comune — bonding `802.3ad` senza LACP sullo switch.** Sintomi: connettivita instabile, ping che falliscono ogni pochi secondi, log dello switch che riportano `MAC flapping`. Causa: il bonding mode 4 (LACP) richiede che lo switch fisico sia configurato con un Link Aggregation Group attivo che dialoga con il LACPDU del bond. Senza, lo switch vede MAC duplicati su porte diverse e fa flapping. Soluzione: o configurare LACP sullo switch (Cisco `channel-group X mode active`, MikroTik bonding LACP, ecc.), oppure passare a `active-backup` (mode 1) che non richiede coordinamento switch. Verifica stato bond: `cat /proc/net/bonding/bond0` deve mostrare `LACP Active: on` e `Slave Status: success`.

> **Caso reale — `bridge-vids 2-4094` su bridge VLAN-aware con switch fisico in access mode.** Un cluster con bridge VLAN-aware aveva alcune VLAN inattese che apparivano sulle VM senza tag. Causa: lo switch fisico era in modalita access su una VLAN nativa diversa, e il bridge VLAN-aware passava i frame untagged sulla VLAN interna 1 (default) anziche sulla VLAN nativa configurata. Soluzione: configurare in `/etc/network/interfaces` `bridge-pvid <native-vlan-id>` per allineare la VLAN nativa lato Proxmox a quella dello switch. Verifica: `bridge vlan show` deve mostrare `PVID Egress Untagged` corrispondente.

---

## Esercizi

1. **Concettuale — bonding mode trade-off.** Per ognuno di questi scenari, scegliere il bonding mode piu appropriato e motivare in 2 righe: (a) link 2x1 GbE verso un switch managed che supporta LACP, throughput e failover bilanciato; (b) link 2x10 GbE verso 2 switch separati (no MLAG/VPC), failover puro; (c) link 2x25 GbE verso uno switch single con LACP e MLAG. *Risposte:* (a) `802.3ad` con `xmit_hash_policy layer3+4`; (b) `active-backup` (l'unico che non richiede coordinamento tra switch); (c) `802.3ad`.

2. **Lab — bridge VLAN-aware con 3 VLAN.** Su un nodo Proxmox, configurare `vmbr0` con `bridge-vlan-aware yes` e `bridge-vids 10,20,30`. Creare 3 VM, una per VLAN, configurando `--net0 virtio,bridge=vmbr0,tag=10/20/30`. Verificare con `bridge vlan show` che le VID siano registrate, e con `ping` cross-VLAN che NON passi (default Proxmox e isolamento L2 fra VLAN).

3. **Scenario — separazione traffico cluster.** Disegnare lo schema di rete (con IP/24 e VLAN) per un cluster Proxmox a 3 nodi con: management `10.10.10.0/24`, Corosync `10.10.11.0/24` (rete separata fisicamente!), migrazione `10.10.20.0/24`, VM `10.10.30.0/24`, storage iSCSI `10.10.40.0/24`. Quante NIC fisiche minimo servono per garantire isolamento? *Risposta minima:* 2 NIC fisiche con VLAN trunk e bridge VLAN-aware (1 dedicata Corosync per latenza bassa, 1 condivisa con VLAN); idealmente 3+ NIC (Corosync separato + bond per VM/storage + management).

4. **Stretch — migrazione vSwitch → Linux Bridge.** Prendere il dump CSV `dvswitches.csv` + `portgroups.csv` (modulo 01.2) di un cluster vSphere reale o di esempio. Scrivere uno script Python che produca le stanze `/etc/network/interfaces` corrispondenti per un nodo Proxmox: bridge VLAN-aware con i `bridge-vids` di tutte le VLAN trovate; per ogni dvPortGroup, mappare il VLAN ID al `tag=` del comando `qm set`. Riferimento per la sintassi: [`PVE-WIKI`] "Network Configuration".

## Auto-valutazione

1. Differenza fra `bridge-stp on` e `bridge-stp off` — quale e il default su Proxmox e perche?
2. Cosa significa `bridge-vids 2-4094` e cosa cambia se manca?
3. Comando per applicare le modifiche a `/etc/network/interfaces` senza riavviare il nodo?
4. Differenza tra `bonding mode 1` (active-backup) e `mode 4` (802.3ad) in termini di requisiti switch.
5. Come si configura un sub-VLAN trunk se non si usa VLAN-aware bridge?
6. Cosa fa il flag `firewall=1` su un'interfaccia VM e dove vivono le regole?
7. Differenza tra bridge "classico" e bridge OVS (Open vSwitch) per l'utente che fa networking?
8. Comando per verificare quali VLAN sono attualmente registrate sul bridge VLAN-aware?

## Letture primarie consigliate

- [`PVE-WIKI`] Proxmox VE Wiki — Network Configuration. https://pve.proxmox.com/wiki/Network_Configuration
- [`PVE-SDN`] Proxmox VE Wiki — Software-Defined Network. https://pve.proxmox.com/wiki/Software-Defined_Network
- [`LINUX-BRIDGE`] Linux Foundation — Linux Bridge. https://wiki.linuxfoundation.org/networking/bridge
- [`BONDING`] Linux Ethernet Bonding driver howto (kernel.org). https://www.kernel.org/doc/Documentation/networking/bonding.txt
- [`IEEE-802.1Q`] IEEE 802.1Q — VLANs. https://standards.ieee.org/ieee/802.1Q/6844/
- [`IEEE-802.1AX`] IEEE 802.1AX — Link Aggregation. https://standards.ieee.org/ieee/802.1AX/4940/
- [`OVS-DOCS`] Open vSwitch Documentation. https://docs.openvswitch.org/en/latest/
- [`IPROUTE2`] iproute2 documentation. https://wiki.linuxfoundation.org/networking/iproute2

## Collegamenti incrociati

- Modulo 01.2 — `../01-FONDAMENTI-VMWARE/vmware-networking-storage.md`: pendant VMware (vSwitch, dvSwitch, port group).
- Modulo 02.1 — `../02-FONDAMENTI-PROXMOX-VE/architettura-installazione-proxmox.md`: configurazione di rete in fase di installazione.
- Modulo 03.2 — `../03-STORAGE-AVANZATO-PROXMOX/nfs-iscsi-storage-condiviso.md`: rete dedicata storage, MTU 9000.
- Modulo 07.1 — `../07-MIGRAZIONE-NETWORKING/ip-planning-dns-dhcp-firewall.md`: pianificazione IP/DNS/firewall in migrazione.
- Modulo 07.2 — `../07-MIGRAZIONE-NETWORKING/mapping-vswitch-linux-bridge.md`: mapping operativo vSwitch → Linux Bridge.
- Modulo 07.3 — `../07-MIGRAZIONE-NETWORKING/migrazione-vlan-e-segmentazione.md`: migrazione VLAN e segmentazione.
- Modulo 17.3 — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-networking-post-migrazione.md`: troubleshooting networking post-migrazione.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Linux Bridge** | Bridge L2 software del kernel Linux (modulo `bridge`). Implementa MAC learning e forwarding. |
| **`vmbr0`** | Convenzione Proxmox: bridge "Virtual Machine BRidge 0", quello principale per VM. |
| **`bridge-vlan-aware`** | Modalita bridge che permette di gestire frame 802.1Q tagged su un solo bridge per VLAN multiple. |
| **`bridge-vids`** | Lista o range di VLAN ID accettate dal bridge VLAN-aware. |
| **`bridge-pvid`** | Port VLAN ID — VLAN nativa per frame untagged in un bridge VLAN-aware. |
| **`bonding mode 0..6`** | Modalita Linux bonding: 0 balance-rr, 1 active-backup, 2 balance-xor, 3 broadcast, 4 802.3ad (LACP), 5 balance-tlb, 6 balance-alb. |
| **`xmit_hash_policy`** | Algoritmo di hash che determina come distribuire i frame sui slave bond: `layer2`, `layer2+3`, `layer3+4`, `encap2+3`, `encap3+4`. |
| **LACP** | Link Aggregation Control Protocol (IEEE 802.3ad / 802.1AX). Frame `LACPDU` ogni 1-30 s. |
| **VLAN 802.1Q** | Standard IEEE che definisce frame Ethernet "tagged" con un campo VID a 12 bit (0-4095, 0 e 4095 riservati, validi 1-4094). |
| **VST / EST / VGT** | Tagging sul vSwitch / sullo switch fisico / nel guest (VID 4095 = trunk completo al guest). |
| **`ifupdown2`** | Implementazione Debian di `ifup`/`ifdown` con supporto avanzato (templates, dependency resolution); default su Proxmox. |
| **`ifreload`** | Comando di `ifupdown2` che applica le modifiche a `/etc/network/interfaces` senza interrompere altre interfacce. |
| **OVS (Open vSwitch)** | Bridge software programmabile con OpenFlow, OVSDB, NIOC-like; pacchetto Debian `openvswitch-switch`. |
| **SDN PVE** | Software-Defined Network integrato di Proxmox: zone, vnet, subnets, IPAM. Plugin `pve-sdn`. |
| **EVPN / VXLAN** | Overlay L2-over-L3 con BGP control plane. Disponibili come zone di SDN PVE. |
| **MTU 9000 (jumbo frames)** | Frame Ethernet di 9000 byte, riduce overhead per traffico storage e backup. Coerenza end-to-end obbligatoria. |
