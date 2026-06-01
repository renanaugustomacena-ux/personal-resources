# Mapping vSwitch VMware verso Linux Bridge Proxmox

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 07.2 (segue 07.1, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 01.2 (vSwitch/dvSwitch VMware), 04.1 (Linux Bridge/VLAN/bonding), 07.1 (IP planning).
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. tradurre un dvSwitch o vSwitch standard di un cluster VMware in una configurazione Linux Bridge VLAN-aware (o OVS) equivalente sul cluster Proxmox target;
> 2. mappare ogni dvPortGroup VMware (con il suo VLAN ID) a un'opzione `tag=N` per il device `--net0 ... bridge=vmbr0,tag=N` sulla VM Proxmox;
> 3. tradurre il NIC Teaming VMware (Originating Port ID, Source MAC Hash, IP Hash) nelle modalita Linux bonding (`active-backup`, `balance-xor`, `802.3ad`/LACP) con le loro implicazioni sullo switch fisico;
> 4. configurare MTU e jumbo frames coerenti end-to-end (NIC ↔ bond ↔ bridge ↔ VLAN sub-iface ↔ VM virtio), validando con `ping -M do -s 8972`;
> 5. produrre un file `/etc/network/interfaces` Proxmox completo per un nodo di produzione, con bridge management, bridge VM VLAN-aware, bridge storage, bonding LACP e gestione MTU;
> 6. mappare uplink fisici e segmentazione di rete (mgmt, VM, storage, migration, Corosync) per separare i traffici critici e produrre layout coerenti con il dimensionamento di 05.3.
> **Tempo stimato:** lettura 60-90 min · lab 180-240 min
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** vSphere 7.0/8.0 dvSwitch v8.0; Proxmox VE 8.x con `ifupdown2`; OVS 3.x (opzionale).

## Mappa concettuale

```
+======================================================+
|  vSwitch VMware → Linux Bridge: traduzione lato a lato|
+======================================================+
|                                                      |
|   VMware                       Proxmox               |
|   ------                       -------               |
|   pNIC: vmnic0/1            pNIC: eno1/eno2          |
|         |                          |                  |
|         v                          v                  |
|   vSwitch / dvSwitch        Linux Bridge VLAN-aware   |
|         |                   (vmbr0 con bridge-vids)   |
|         v                          |                  |
|   Port Group (VLAN 100)            v                  |
|         |                   --net0 ...,bridge=vmbr0,  |
|         v                       tag=100               |
|   VM (uplink: vmnic0)              |                  |
|                                    v                  |
|                             VM virtio (tag visto)     |
|                                                      |
|   --- NIC Teaming VMware ---  ---- Linux Bonding ---  |
|                                                      |
|   Origin Port ID (default)  → Default = no bonding,  |
|     ↑ no LACP needed          oppure mode 1 (active- |
|                              backup) per failover    |
|                                                      |
|   IP Hash (req LACP)        → mode 4 (802.3ad) +     |
|     ↑ requires LAG          xmit_hash_policy         |
|                              layer3+4 + LAG sullo    |
|                              switch                  |
|                                                      |
|   Source MAC Hash           → mode 2 (balance-xor)   |
|                              con xmit_hash_policy    |
|                              layer2                  |
|                                                      |
|   Explicit Failover         → mode 1 (active-backup) |
|     Order                                            |
|                                                      |
|   --- MTU end-to-end ---                             |
|                                                      |
|   VMware MTU su vSwitch     →  ip link set <iface>    |
|                                  mtu 9000             |
|     deve essere < o uguale     deve essere coerente   |
|     dei pNIC                   pNIC + bond + bridge   |
|                                + VLAN + virtio guest  |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **Mapping concettuale, non automatico.** Non esiste un tool che converta `dvswitches.csv` in `/etc/network/interfaces` automaticamente. La traduzione e *manuale* e va fatta a partire dall'inventario di 05.1, applicando le equivalenze concettuali. L'esercizio 4 di questo modulo propone uno script per accelerare.
2. **VLAN-aware bridge e l'unica scelta sensata.** Il pendant di un dvSwitch con N port group e *un* `vmbr0` VLAN-aware con `bridge-vids 1-4094`, non N bridge separati. Bridge separati moltiplicano la complessita per zero benefici.
3. **Bonding mode 4 (802.3ad) richiede LAG sullo switch.** Senza LAG, lo switch fisico ricicla i frame fra le porte producendo MAC flap. Per chi non controlla lo switch fisico (cloud provider, datacenter colocato), default a `active-backup` (mode 1) e sicuro.
4. **MTU coerente o problemi sottili.** Il problema piu insidioso e MTU mismatch su uno solo dei tier (NIC OK, bond OK, ma bridge dimenticato a 1500): grosso traffico viene drop, piccolo passa, sintomo "alcune cose funzionano altre no". Verifica obbligatoria post-config: `ping -M do -s 8972 <peer>` deve passare sia da host a host, sia da VM a VM.
5. **Separazione dei traffici via VLAN, non via bridge.** Un solo `vmbr0` VLAN-aware con `bridge-vids` per management (10), VM (20), storage (30), migration (40) e Corosync (11) e piu manutenibile di 5 bridge separati. L'unica eccezione: Corosync raccomanda *rete fisicamente separata* per latenza ultra-bassa, quindi tipicamente ha la sua interface `eno2` dedicata senza bridge.

## Indice
- [Panoramica](#panoramica)
- [Architettura di Rete VMware: vSwitch Standard e Distributed](#architettura-di-rete-vmware-vswitch-standard-e-distributed)
- [Architettura di Rete Proxmox: Linux Bridge e Open vSwitch](#architettura-di-rete-proxmox-linux-bridge-e-open-vswitch)
- [Metodologia di Mapping: Port Group verso Bridge+VLAN](#metodologia-di-mapping-port-group-verso-bridgevlan)
- [NIC Teaming VMware verso Linux Bonding](#nic-teaming-vmware-verso-linux-bonding)
- [Configurazione MTU e Jumbo Frames](#configurazione-mtu-e-jumbo-frames)
- [Configurazione /etc/network/interfaces](#configurazione-etcnetworkinterfaces)
- [Uplink Mapping e Segmentazione di Rete](#uplink-mapping-e-segmentazione-di-rete)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

La migrazione dell'infrastruttura di rete da VMware a Proxmox VE rappresenta una delle fasi più critiche dell'intero processo di transizione. Mentre VMware utilizza un modello di networking virtualizzato proprietario basato su vSwitch Standard (vSS) e vSwitch Distributed (vDS), Proxmox si appoggia interamente sullo stack di rete nativo di Linux, in particolare Linux Bridge e, opzionalmente, Open vSwitch (OVS). Comprendere le differenze architetturali tra questi due approcci è fondamentale per pianificare un mapping corretto e garantire la continuità dei servizi di rete durante e dopo la migrazione.

Il vSwitch VMware astrae la complessità della rete fisica attraverso concetti come port group, uplink, NIC teaming policy e traffic shaping, tutti gestiti tramite l'interfaccia vSphere Client o vCenter. In Proxmox, gli stessi obiettivi si raggiungono attraverso la configurazione diretta di bridge Linux, VLAN tagging nativo del kernel, bonding interfaces e regole di rete standard. Questo approccio offre maggiore trasparenza e controllo, ma richiede una conoscenza più approfondita del networking Linux.

Questo documento fornisce una metodologia strutturata per mappare ogni componente di rete VMware nel corrispondente equivalente Proxmox, con esempi di configurazione concreti, diagrammi e strategie per gestire la transizione minimizzando il downtime. L'obiettivo è fornire all'ingegnere di migrazione una guida operativa completa, dalla fase di inventario alla validazione post-migrazione.

---

## Architettura di Rete VMware: vSwitch Standard e Distributed

### vSwitch Standard (vSS)

Il vSwitch Standard è l'elemento base del networking VMware ESXi. Ogni host ESXi può ospitare fino a 4096 porte distribuite tra più vSwitch Standard. Un vSS è locale al singolo host e non condivide la configurazione con altri host nel cluster.

Componenti principali del vSS:

| Componente | Descrizione |
|---|---|
| **Uplink (vmnic)** | Interfaccia fisica connessa allo switch fisico |
| **Port Group** | Gruppo logico di porte con policy di rete comuni |
| **VMkernel Port** | Interfaccia di rete per servizi ESXi (management, vMotion, iSCSI, NFS) |
| **VLAN ID** | Tag 802.1Q assegnato al port group |
| **NIC Teaming Policy** | Failover order, load balancing, link status detection |
| **Traffic Shaping** | Bandwidth limiting in uscita (solo egress su vSS) |
| **Security Policy** | Promiscuous mode, MAC changes, forged transmits |

La struttura tipica di un vSS si presenta come segue:

```
┌──────────────────────────────────────────────────┐
│                  vSwitch Standard                  │
│                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │
│  │  Port Group   │  │  Port Group   │  │ VMkernel│ │
│  │  "VM Network" │  │  "Storage"    │  │  Mgmt   │ │
│  │  VLAN 100     │  │  VLAN 200     │  │ VLAN 10 │ │
│  └──────┬───────┘  └──────┬───────┘  └────┬────┘ │
│         │                  │               │       │
│  ┌──────┴──────────────────┴───────────────┴────┐ │
│  │              NIC Teaming Policy               │ │
│  │         (Active-Standby / Load-Based)         │ │
│  └──────┬──────────────────────────┬────────────┘ │
│         │                          │               │
│     ┌───┴───┐                  ┌───┴───┐          │
│     │vmnic0 │                  │vmnic1 │          │
│     └───┬───┘                  └───┬───┘          │
└─────────┼──────────────────────────┼──────────────┘
          │                          │
     Physical NIC 0            Physical NIC 1
```

### vSwitch Distributed (vDS)

Il vDS estende il concetto di vSwitch a livello di cluster vCenter. La configurazione è centralizzata e replicata automaticamente su tutti gli host membri. Funzionalità aggiuntive rispetto al vSS includono:

- **Network I/O Control (NIOC)**: allocazione di bandwidth per tipo di traffico con shares e reservation
- **Port mirroring**: cattura del traffico per diagnostica
- **Traffic shaping bidirezionale**: ingress ed egress
- **NetFlow/IPFIX**: esportazione di flow per analisi
- **Link Aggregation Group (LAG)**: supporto LACP nativo
- **Private VLAN (PVLAN)**: isolamento a livello Layer 2
- **Health check**: verifica automatica di VLAN trunking e MTU

Ogni port group distribuito può avere policy di override per singola porta, consentendo una granularità di configurazione non disponibile su vSS.

### Inventario della Configurazione VMware

Prima di iniziare il mapping, è necessario esportare la configurazione di rete completa. Utilizzare i seguenti comandi PowerCLI:

```powershell
# Esportare configurazione vSwitch Standard per tutti gli host
Get-VMHost | Get-VirtualSwitch -Standard | Select-Object VMHost, Name, Nic, MTU |
    Export-Csv -Path "vss_inventory.csv" -NoTypeInformation

# Esportare port group con VLAN
Get-VMHost | Get-VirtualPortGroup | Select-Object VMHost, VirtualSwitchName,
    Name, VLanId | Export-Csv -Path "portgroup_inventory.csv" -NoTypeInformation

# Esportare NIC teaming policy
Get-VMHost | Get-VirtualSwitch -Standard | Get-NicTeamingPolicy |
    Select-Object VirtualSwitch, ActiveNic, StandbyNic, LoadBalancingPolicy,
    NetworkFailoverDetectionPolicy | Export-Csv -Path "teaming_inventory.csv" -NoTypeInformation

# Esportare vDS configuration
Get-VDSwitch | Select-Object Name, NumUplinkPorts, Mtu, LinkDiscoveryProtocol,
    Version | Export-Csv -Path "vds_inventory.csv" -NoTypeInformation

# Esportare distributed port group
Get-VDSwitch | Get-VDPortgroup | Select-Object VDSwitch, Name, VlanConfiguration,
    PortBinding | Export-Csv -Path "vds_portgroup_inventory.csv" -NoTypeInformation
```

---

## Architettura di Rete Proxmox: Linux Bridge e Open vSwitch

### Linux Bridge

Il Linux Bridge è il meccanismo di networking predefinito in Proxmox VE. Implementato nel kernel Linux, fornisce funzionalità di switching Layer 2 con supporto nativo per VLAN 802.1Q, Spanning Tree Protocol (STP) e MAC address learning.

In Proxmox, ogni bridge è definito nel file `/etc/network/interfaces` e tipicamente prende il nome `vmbr0`, `vmbr1`, ecc. Un bridge può avere uno o più membri (port) che possono essere interfacce fisiche, bond interface, o VLAN sub-interface.

```
┌──────────────────────────────────────────────────┐
│                   Proxmox Host                     │
│                                                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │  VM 100  │  │  VM 101  │  │  VM 102  │          │
│  │ vnet0    │  │ vnet0    │  │ vnet0    │          │
│  │ tag=100  │  │ tag=100  │  │ tag=200  │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
│       │              │              │               │
│  ┌────┴──────────────┴──────────────┴────────────┐ │
│  │              vmbr0 (VLAN-aware bridge)          │ │
│  │         bridge-vlan-aware yes                   │ │
│  │         bridge-vids 2-4094                      │ │
│  │         bridge-ports bond0                      │ │
│  └──────────────────┬───────────────────────────┘ │
│                     │                              │
│  ┌──────────────────┴───────────────────────────┐ │
│  │              bond0 (802.3ad LACP)             │ │
│  │         bond-slaves eno1 eno2                 │ │
│  └──────┬──────────────────────────┬────────────┘ │
│         │                          │               │
│     ┌───┴───┐                  ┌───┴───┐          │
│     │ eno1  │                  │ eno2  │          │
│     └───┬───┘                  └───┬───┘          │
└─────────┼──────────────────────────┼──────────────┘
          │                          │
     Physical NIC 0            Physical NIC 1
```

### VLAN-Aware Bridge vs Traditional Bridge

Proxmox supporta due modalità di gestione VLAN:

**Traditional Bridge (pre-VLAN-aware)**: si crea un bridge separato per ogni VLAN. Questo approccio richiede la definizione di sub-interface VLAN dedicate e un bridge per ciascuna.

```
# Traditional: un bridge per VLAN
auto eno1.100
iface eno1.100 inet manual

auto vmbr100
iface vmbr100 inet manual
    bridge-ports eno1.100
    bridge-stp off
    bridge-fd 0

auto eno1.200
iface eno1.200 inet manual

auto vmbr200
iface vmbr200 inet manual
    bridge-ports eno1.200
    bridge-stp off
    bridge-fd 0
```

**VLAN-Aware Bridge**: un singolo bridge gestisce tutte le VLAN. Il tag VLAN viene assegnato alla singola interfaccia VM nella configurazione della VM stessa. Questo è l'approccio raccomandato.

```
# VLAN-aware: un solo bridge per tutte le VLAN
auto vmbr0
iface vmbr0 inet manual
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 2-4094
```

### Open vSwitch (OVS)

Open vSwitch è un'alternativa al Linux Bridge che offre funzionalità avanzate quali:

- Supporto LACP nativo con negoziazione
- Port mirroring e SPAN
- NetFlow, sFlow, IPFIX
- QoS e traffic shaping
- Programmabilità via OpenFlow
- Supporto GRE, VXLAN, Geneve tunneling

L'installazione di OVS su Proxmox richiede:

```bash
apt update && apt install -y openvswitch-switch
systemctl enable --now openvswitch-switch
```

Esempio di configurazione OVS in `/etc/network/interfaces`:

```
auto vmbr0
iface vmbr0 inet manual
    ovs_type OVSBridge
    ovs_ports eno1 eno2
    ovs_options tag=10
    up ovs-vsctl set Bridge vmbr0 stp_enable=false
```

La scelta tra Linux Bridge e OVS dipende dai requisiti specifici. Per la maggior parte delle migrazioni da VMware, il Linux Bridge VLAN-aware è sufficiente e più semplice da gestire. OVS è preferibile quando si necessita di funzionalità avanzate come port mirroring, tunneling o integrazione con SDN controller.

---

## Metodologia di Mapping: Port Group verso Bridge+VLAN

### Tabella di Mapping

Il primo passo operativo è costruire una tabella di corrispondenza tra i port group VMware e la configurazione Proxmox target. Esempio:

| VMware Port Group | VLAN | vSwitch | Funzione | Proxmox Bridge | VLAN Tag | Note |
|---|---|---|---|---|---|---|
| Management Network | 10 | vSwitch0 | Host management | vmbr0 | 10 | IP statico host |
| VM_Production | 100 | vSwitch0 | VM produzione | vmbr0 | 100 | VLAN-aware |
| VM_Development | 110 | vSwitch0 | VM sviluppo | vmbr0 | 110 | VLAN-aware |
| vMotion | 20 | vSwitch1 | Live migration | vmbr1 | 20 | Rete dedicata |
| iSCSI_A | 30 | vSwitch2 | Storage path A | vmbr2 | 30 | Jumbo frames |
| iSCSI_B | 31 | vSwitch2 | Storage path B | vmbr2 | 31 | Jumbo frames |
| Backup | 40 | vSwitch0 | Backup traffic | vmbr0 | 40 | - |

### Regole di Mapping

1. **vSwitch con uplink fisici dedicati**: ogni vSwitch VMware che utilizza NIC fisiche separate dovrebbe mappare a un bridge Proxmox separato con il proprio bonding.

2. **vSwitch con uplink condivisi**: se più port group condividono gli stessi uplink su un unico vSwitch, possono convergere su un singolo VLAN-aware bridge in Proxmox.

3. **VMkernel port**: i VMkernel port per management, vMotion e storage si traducono in indirizzi IP assegnati direttamente al bridge Proxmox o a VLAN sub-interface del bridge.

4. **Port group senza VLAN (VLAN 0)**: si mappano al bridge Proxmox senza tag, utilizzando il native VLAN (PVID) configurato sullo switch fisico.

### Processo Step-by-Step

```
Fase 1: Inventario VMware
    │
    ├── Elenco completo vSwitch (Standard + Distributed)
    ├── Elenco port group con VLAN ID
    ├── Mapping uplink fisici per vSwitch
    ├── NIC teaming policy per vSwitch/port group
    └── MTU per vSwitch
    │
Fase 2: Design Proxmox
    │
    ├── Definire numero di bridge necessari
    ├── Definire bonding mode per ogni bridge
    ├── Assegnare VLAN al bridge (VLAN-aware) o creare bridge separati
    ├── Pianificare indirizzamento IP per servizi host
    └── Definire MTU per ogni bridge
    │
Fase 3: Configurazione Switch Fisico
    │
    ├── Verificare trunk VLAN sulle porte uplink
    ├── Configurare LACP se necessario
    ├── Verificare native VLAN
    └── Abilitare jumbo frames se richiesto
    │
Fase 4: Implementazione Proxmox
    │
    ├── Configurare /etc/network/interfaces
    ├── Applicare configurazione (ifreload -a)
    ├── Verificare connettività per ogni VLAN
    └── Documentare configurazione finale
```

---

## NIC Teaming VMware verso Linux Bonding

### Mapping delle Policy di Teaming

VMware offre diverse policy di NIC teaming nel vSwitch. Ciascuna ha un equivalente nel bonding Linux:

| VMware NIC Teaming Policy | Linux Bonding Mode | Parametri |
|---|---|---|
| Route based on originating virtual port ID | `balance-rr` (mode 0) oppure `balance-xor` (mode 2) | Approssimazione; non esiste equivalente esatto |
| Route based on IP hash | `balance-xor` (mode 2) con `xmit_hash_policy layer3+4` | Richiede switch configurato in port-channel statico |
| Route based on source MAC hash | `balance-xor` (mode 2) con `xmit_hash_policy layer2` | Switch in port-channel statico |
| Route based on physical NIC load | `balance-alb` (mode 6) | Non richiede configurazione switch |
| Use explicit failover order | `active-backup` (mode 1) | Non richiede configurazione switch |
| LACP (solo vDS) | `802.3ad` (mode 4) | Richiede LACP sullo switch fisico |

### Configurazione Linux Bonding

#### Mode 1: Active-Backup (Equivalente Failover Order)

Questa è la configurazione più semplice e sicura, ideale per la fase di migrazione:

```
auto bond0
iface bond0 inet manual
    bond-slaves eno1 eno2
    bond-mode active-backup
    bond-miimon 100
    bond-primary eno1
```

Parametri chiave:
- `bond-miimon 100`: verifica link ogni 100ms (equivalente a "Link Status Only" in VMware)
- `bond-primary eno1`: definisce l'interfaccia attiva preferita

#### Mode 4: 802.3ad LACP

Configurazione raccomandata per ambienti di produzione con switch che supportano LACP:

```
auto bond0
iface bond0 inet manual
    bond-slaves eno1 eno2
    bond-mode 802.3ad
    bond-miimon 100
    bond-lacp-rate fast
    bond-xmit-hash-policy layer3+4
```

Configurazione corrispondente sullo switch Cisco:

```
interface Port-channel1
  switchport mode trunk
  switchport trunk allowed vlan 10,20,30,100,110,200

interface GigabitEthernet0/1
  channel-group 1 mode active

interface GigabitEthernet0/2
  channel-group 1 mode active
```

#### Mode 6: Adaptive Load Balancing

Utile quando non è possibile modificare la configurazione dello switch fisico:

```
auto bond0
iface bond0 inet manual
    bond-slaves eno1 eno2
    bond-mode balance-alb
    bond-miimon 100
```

Questo mode non richiede alcuna configurazione speciale sullo switch fisico poiché il bilanciamento avviene interamente lato host tramite manipolazione degli ARP reply.

### Verifica del Bonding

```bash
# Stato del bond
cat /proc/net/bonding/bond0

# Verifica LACP (mode 4)
cat /proc/net/bonding/bond0 | grep -A 5 "802.3ad"

# Statistiche per slave
cat /proc/net/bonding/bond0 | grep -A 10 "Slave Interface"

# Test failover (disattivare temporaneamente uno slave)
ip link set eno2 down
# Verificare che il traffico continui su eno1
ping -c 5 <gateway>
ip link set eno2 up
```

---

## Configurazione MTU e Jumbo Frames

### MTU in VMware vs Proxmox

In VMware, l'MTU viene configurato a livello di vSwitch e si propaga a tutti i port group. In Proxmox, l'MTU deve essere configurato esplicitamente su ogni livello dello stack: interfaccia fisica, bond, VLAN sub-interface e bridge.

**Regola fondamentale**: l'MTU deve essere configurato dal basso verso l'alto. L'interfaccia fisica deve avere un MTU uguale o superiore a quello del bridge che la utilizza.

```
Interfaccia fisica (eno1): MTU 9000
        │
    Bond (bond0): MTU 9000
        │
    Bridge (vmbr0): MTU 9000
        │
    VM vNIC: MTU 9000 (configurato nel guest OS)
```

### Configurazione Jumbo Frames

Esempio completo per una rete storage con jumbo frames (MTU 9000):

```
# Interfacce fisiche dedicate allo storage
auto eno3
iface eno3 inet manual
    mtu 9000

auto eno4
iface eno4 inet manual
    mtu 9000

# Bond per storage
auto bond1
iface bond1 inet manual
    bond-slaves eno3 eno4
    bond-mode 802.3ad
    bond-miimon 100
    bond-lacp-rate fast
    bond-xmit-hash-policy layer3+4
    mtu 9000

# Bridge storage con jumbo frames
auto vmbr1
iface vmbr1 inet static
    address 10.0.30.11/24
    bridge-ports bond1
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 30-31
    mtu 9000
```

### Verifica MTU End-to-End

Verificare che l'intero path supporti jumbo frames senza frammentazione:

```bash
# Test MTU dal host Proxmox verso lo storage target
# -M do = don't fragment, -s = payload size
# Per MTU 9000: payload = 9000 - 28 (IP+ICMP headers) = 8972
ping -M do -s 8972 -c 5 <storage_ip>

# Se il test fallisce, ridurre progressivamente fino a trovare l'MTU effettivo
ping -M do -s 8000 -c 3 <storage_ip>

# Verificare MTU su ogni interfaccia
ip -d link show eno3 | grep mtu
ip -d link show bond1 | grep mtu
ip -d link show vmbr1 | grep mtu
```

---

## Configurazione /etc/network/interfaces

### Esempio Completo: Migrazione da Ambiente VMware Tipico

Scenario VMware originale:
- vSwitch0: vmnic0 + vmnic1, port groups: Management (VLAN 10), VM_Prod (VLAN 100), VM_Dev (VLAN 110)
- vSwitch1: vmnic2 + vmnic3, port group: vMotion (VLAN 20)
- vSwitch2: vmnic4 + vmnic5, port groups: iSCSI_A (VLAN 30), iSCSI_B (VLAN 31), MTU 9000

Configurazione Proxmox equivalente:

```
# /etc/network/interfaces
# Proxmox VE Network Configuration
# Migrato da VMware ESXi - [DATA]

# === Loopback ===
auto lo
iface lo inet loopback

# =============================================================
# RETE MANAGEMENT + VM (equivalente vSwitch0)
# =============================================================

# Interfacce fisiche (ex vmnic0, vmnic1)
auto eno1
iface eno1 inet manual

auto eno2
iface eno2 inet manual

# Bond - equivalente NIC teaming active-standby di vSwitch0
auto bond0
iface bond0 inet manual
    bond-slaves eno1 eno2
    bond-mode active-backup
    bond-miimon 100
    bond-primary eno1

# Bridge principale VLAN-aware
# Sostituisce: Management Network (VLAN 10), VM_Prod (100), VM_Dev (110)
auto vmbr0
iface vmbr0 inet static
    address 10.0.10.11/24
    gateway 10.0.10.1
    bridge-ports bond0
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 10 100 110 40
    bridge-pvid 10

# =============================================================
# RETE MIGRAZIONE (equivalente vSwitch1 - vMotion)
# =============================================================

auto eno3
iface eno3 inet manual

auto eno4
iface eno4 inet manual

auto bond1
iface bond1 inet manual
    bond-slaves eno3 eno4
    bond-mode 802.3ad
    bond-miimon 100
    bond-lacp-rate fast
    bond-xmit-hash-policy layer3+4

auto vmbr1
iface vmbr1 inet static
    address 10.0.20.11/24
    bridge-ports bond1
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 20

# =============================================================
# RETE STORAGE (equivalente vSwitch2 - iSCSI)
# =============================================================

auto eno5
iface eno5 inet manual
    mtu 9000

auto eno6
iface eno6 inet manual
    mtu 9000

auto bond2
iface bond2 inet manual
    bond-slaves eno5 eno6
    bond-mode 802.3ad
    bond-miimon 100
    bond-lacp-rate fast
    bond-xmit-hash-policy layer3+4
    mtu 9000

auto vmbr2
iface vmbr2 inet static
    address 10.0.30.11/24
    bridge-ports bond2
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 30 31
    mtu 9000
```

### Applicare la Configurazione

```bash
# Verificare la sintassi PRIMA di applicare
ifquery --check --all

# Applicare senza riavviare (richiede ifupdown2)
ifreload -a

# Verificare che tutti i bridge siano attivi
bridge link show

# Verificare VLAN membership
bridge vlan show

# Verificare indirizzi IP
ip -4 addr show
```

**ATTENZIONE**: se si commette un errore nella configurazione di rete e si applica con `ifreload -a`, si può perdere la connettività remota all'host. Utilizzare sempre una console fisica, IPMI/iLO/iDRAC o un cron job di rollback:

```bash
# Rollback automatico: ripristina la configurazione precedente dopo 60 secondi
# a meno che non venga cancellato manualmente
cp /etc/network/interfaces /etc/network/interfaces.backup
(sleep 60 && cp /etc/network/interfaces.backup /etc/network/interfaces && ifreload -a) &
echo "Rollback pianificato in 60 secondi. Per annullare: kill $!"
```

---

## Uplink Mapping e Segmentazione di Rete

### Segmentazione Tipica

Un'infrastruttura VMware ben progettata segmenta il traffico su reti fisiche o logiche separate. Questa segmentazione deve essere preservata in Proxmox.

| Tipo di Traffico | VMware Mechanism | Proxmox Equivalent | VLAN Tipica | Requisiti |
|---|---|---|---|---|
| **Management** | VMkernel port su vSwitch0 | IP su vmbr0 con PVID | 10 | HA, accesso SSH, web UI |
| **VM Traffic** | Port group su vSwitch0 | VLAN tag su vmbr0 | 100-199 | Banda variabile |
| **Live Migration** | VMkernel vMotion su vSwitch1 | IP su vmbr1 | 20 | Bassa latenza, alta banda |
| **Storage** | VMkernel iSCSI/NFS su vSwitch2 | IP su vmbr2 | 30-39 | Jumbo frames, multipath |
| **Backup** | Port group dedicato | VLAN tag su vmbr0 | 40 | Banda sostenuta |
| **Replication** | VMkernel replication | IP su vmbr1 o dedicato | 25 | Coexistence replication |

### Design con NIC Limitate

Se il server ha solo 2 o 4 NIC fisiche, è necessario consolidare il traffico su meno bridge:

**2 NIC fisiche (eno1, eno2)**:

```
auto bond0
iface bond0 inet manual
    bond-slaves eno1 eno2
    bond-mode active-backup
    bond-miimon 100

auto vmbr0
iface vmbr0 inet static
    address 10.0.10.11/24
    gateway 10.0.10.1
    bridge-ports bond0
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 10 20 30 100 110 200
    bridge-pvid 10
```

In questo scenario tutto il traffico transita su un unico bridge VLAN-aware. La separazione avviene esclusivamente a livello VLAN sullo switch fisico. È fondamentale configurare QoS sullo switch per prioritizzare il traffico di management e storage.

**4 NIC fisiche (eno1-eno4)**:

```
# Bond per management + VM (eno1 + eno2)
auto bond0
iface bond0 inet manual
    bond-slaves eno1 eno2
    bond-mode active-backup
    bond-miimon 100

auto vmbr0
iface vmbr0 inet static
    address 10.0.10.11/24
    gateway 10.0.10.1
    bridge-ports bond0
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 10 20 100 110 200
    bridge-pvid 10

# Bond per storage (eno3 + eno4)
auto bond1
iface bond1 inet manual
    bond-slaves eno3 eno4
    bond-mode 802.3ad
    bond-miimon 100
    bond-lacp-rate fast
    mtu 9000

auto vmbr1
iface vmbr1 inet static
    address 10.0.30.11/24
    bridge-ports bond1
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 30 31
    mtu 9000
```

### Verifiche di Connettività Post-Configurazione

Dopo aver completato la configurazione, verificare sistematicamente ogni segmento:

```bash
# 1. Verifica management
ping -c 3 10.0.10.1  # Gateway

# 2. Verifica storage (con jumbo frames)
ping -M do -s 8972 -c 3 10.0.30.1

# 3. Verifica raggiungibilità tra nodi Proxmox
ping -c 3 10.0.10.12  # Altro nodo
ping -c 3 10.0.20.12  # Migration network

# 4. Verifica VLAN tagging con tcpdump
tcpdump -i bond0 -e vlan -c 20

# 5. Verifica bridge forwarding
bridge fdb show dev vmbr0 | head -20
```

---

## Best Practices

- **Utilizzare sempre VLAN-aware bridge** in Proxmox: semplifica la gestione e riduce il numero di bridge necessari. Un singolo bridge con `bridge-vlan-aware yes` può sostituire decine di bridge tradizionali.

- **Iniziare con active-backup (mode 1)** per il bonding durante la fase di migrazione. Passare a 802.3ad (mode 4) solo dopo aver verificato la corretta configurazione LACP sullo switch fisico. Un errore LACP può causare la perdita completa di connettività.

- **Mantenere la stessa segmentazione di rete** dell'ambiente VMware originale. Non è il momento di riprogettare la rete durante una migrazione. La consolidazione o ristrutturazione può avvenire in una fase successiva.

- **Documentare ogni mapping** in una tabella di corrispondenza VMware → Proxmox. Questa tabella è il riferimento principale per la configurazione delle VM migrate.

- **Configurare il rollback automatico** prima di ogni modifica al file `/etc/network/interfaces`, specialmente quando si lavora da remoto. Un errore di configurazione può rendere l'host irraggiungibile.

- **Testare la connettività per ogni VLAN** dopo la configurazione, includendo test con jumbo frames dove applicabile. Non dare per scontato che la VLAN sia raggiungibile solo perché il bridge è attivo.

- **Preservare l'MTU esistente**: se VMware usava jumbo frames per storage o vMotion, configurare lo stesso MTU in Proxmox. Un mismatch MTU causa degradazione delle performance o errori di connettività difficili da diagnosticare.

- **Utilizzare ifupdown2** invece del classico ifupdown: supporta `ifreload -a` per applicare modifiche senza riavvio, fondamentale per un ambiente di produzione.

- **Non mischiare Linux Bridge e OVS** sullo stesso host senza una chiara separazione delle interfacce fisiche. L'interazione tra i due può causare comportamenti imprevedibili.

- **Etichettare i bridge con commenti** nel file di configurazione (`#`) indicando a quale vSwitch VMware e port group corrispondono. Questo facilita la tracciabilità durante e dopo la migrazione.

- **Verificare la configurazione dello switch fisico** prima di iniziare: trunk port, allowed VLAN list, native VLAN, LACP. La maggior parte dei problemi di rete post-migrazione deriva da configurazioni errate sullo switch fisico, non su Proxmox.

---

## Troubleshooting

### Problema: VM Non Raggiungibile dopo Migrazione
**Sintomi**: la VM migrata si avvia correttamente in Proxmox ma non risponde al ping né ai servizi di rete. L'interfaccia di rete nel guest mostra "connected" ma nessun traffico passa.
**Causa**: VLAN ID mancante o errato nella configurazione della VM Proxmox. Il bridge potrebbe non avere la VLAN nel range `bridge-vids`, oppure il tag VLAN non è stato assegnato all'interfaccia di rete della VM.
**Soluzione**: verificare con `bridge vlan show` che la VLAN sia presente sul bridge. Controllare la configurazione della VM in `/etc/pve/qemu-server/<vmid>.conf` e assicurarsi che la riga `net0` contenga il parametro `tag=<VLAN_ID>`. Esempio: `net0: virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0,tag=100`.
**Prevenzione**: prima di migrare ogni VM, verificare il VLAN ID nel port group VMware e configurare il corrispondente tag nella definizione della NIC virtuale Proxmox.

### Problema: Bonding Non Funzionante con LACP
**Sintomi**: il bond in mode 802.3ad è attivo ma solo uno slave trasporta traffico. Il file `/proc/net/bonding/bond0` mostra "Partner MAC" come 00:00:00:00:00:00 per uno o più slave.
**Causa**: lo switch fisico non ha LACP configurato sulle porte corrispondenti, oppure le porte sono in channel-group con modalità `on` (statico) invece di `active` (LACP).
**Soluzione**: verificare la configurazione dello switch. Per Cisco: `show etherchannel summary` e `show lacp neighbor`. Le porte devono essere in `mode active`. Correggere lo switch e poi verificare con `cat /proc/net/bonding/bond0` che il "Partner MAC" sia valorizzato e "Aggregator ID" sia lo stesso per tutti gli slave.
**Prevenzione**: concordare la configurazione LACP con il team di networking prima della migrazione. Testare il bonding prima di spostare il traffico di produzione.

### Problema: Jumbo Frames Non Funzionano
**Sintomi**: il ping con payload 8972 fallisce (`ping -M do -s 8972` restituisce "message too long" o packet loss), ma il ping standard (MTU 1500) funziona correttamente.
**Causa**: l'MTU non è configurato correttamente su tutti i componenti del path: interfaccia fisica, bond, bridge, switch fisico, destinazione. Un singolo componente con MTU 1500 causa frammentazione o drop dei pacchetti.
**Soluzione**: verificare l'MTU su ogni livello con `ip link show <interface> | grep mtu`. Verificare lo switch fisico con `show interface <port> | include MTU`. Assicurarsi che l'MTU sia 9000 (o il valore desiderato) su: interfacce fisiche, bond, bridge, porte dello switch, e sull'interfaccia della destinazione.
**Prevenzione**: configurare l'MTU dal basso verso l'alto (fisica → bond → bridge) e verificare con test ping end-to-end prima di migrare il traffico storage.

### Problema: Perdita di Connettività Dopo ifreload
**Sintomi**: dopo aver eseguito `ifreload -a`, l'host Proxmox diventa irraggiungibile via SSH e web UI.
**Causa**: errore di sintassi o errore logico nel file `/etc/network/interfaces`. Potenziali cause: indirizzo IP errato, gateway mancante, bridge-ports che punta a un'interfaccia inesistente, bond-slaves con nomi errati.
**Soluzione**: accedere tramite console fisica, IPMI, iLO o iDRAC. Ripristinare il file di backup: `cp /etc/network/interfaces.backup /etc/network/interfaces && ifreload -a`. Se non esiste backup, correggere manualmente e riapplicare.
**Prevenzione**: eseguire sempre `ifquery --check --all` prima di applicare. Creare un backup del file e pianificare un rollback automatico con il cron job descritto nella sezione di configurazione.

### Problema: Traffic Loop con STP Disabilitato
**Sintomi**: tempesta broadcast sulla rete, CPU del host al 100% per soft IRQ, switch fisici che segnalano loop.
**Causa**: se due bridge Proxmox sono collegati allo stesso segmento di rete (per esempio durante una migrazione), e STP è disabilitato (`bridge-stp off`), si crea un loop Layer 2.
**Soluzione**: abilitare immediatamente STP sui bridge coinvolti: `brctl stp vmbr0 on`. Poi modificare `/etc/network/interfaces` aggiungendo `bridge-stp on` e applicare con `ifreload -a`.
**Prevenzione**: durante la migrazione, quando coesistono host VMware e Proxmox sullo stesso segmento, considerare l'abilitazione di STP. In alternativa, assicurarsi che non ci siano path ridondanti tra bridge diversi sullo stesso host.

### Problema: MAC Address Conflict tra VMware e Proxmox
**Sintomi**: connettività intermittente della VM migrata. ARP table sullo switch mostra il MAC della VM su due porte diverse (la porta dell'host VMware e quella dell'host Proxmox).
**Causa**: la VM originale su VMware è ancora attiva (non spenta) mentre la copia migrata è già avviata su Proxmox. Entrambe le istanze hanno lo stesso MAC address.
**Soluzione**: spegnere immediatamente la VM sull'ambiente sorgente (VMware). Verificare con `show mac address-table address <MAC>` sullo switch che il MAC sia appreso solo sulla porta dell'host Proxmox. Forzare il refresh ARP sul default gateway: `clear arp-cache` (su router Cisco).
**Prevenzione**: seguire una procedura rigorosa di cutover: spegnere la VM su VMware PRIMA di avviarla su Proxmox. Non eseguire mai due istanze della stessa VM contemporaneamente.

---

## Riferimenti

- [Proxmox VE Network Configuration - Documentazione Ufficiale](https://pve.proxmox.com/wiki/Network_Configuration)
- [Linux Bridge - Kernel Documentation](https://www.kernel.org/doc/html/latest/networking/bridge.html)
- [Linux Bonding Driver - Kernel Documentation](https://www.kernel.org/doc/Documentation/networking/bonding.txt)
- [Open vSwitch Documentation](https://docs.openvswitch.org/en/latest/)
- [VMware vSphere Networking Guide](https://docs.vmware.com/en/VMware-vSphere/7.0/vsphere-esxi-vcenter-server-703-networking-guide.pdf)
- [IEEE 802.1Q - VLAN Tagging Standard](https://standards.ieee.org/standard/802_1Q-2018.html)
- [IEEE 802.3ad - Link Aggregation](https://standards.ieee.org/standard/802_3ad-2000.html)
- [ifupdown2 - Documentazione](https://github.com/CumulusNetworks/ifupdown2)
- [Proxmox VE VLAN-Aware Bridge](https://pve.proxmox.com/wiki/Network_Configuration#_vlan_aware_bridge)

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — Open vSwitch quando serve.** OVS sostituisce Linux Bridge quando si vuole: (a) NIOC-like QoS per flussi (token-bucket per dvPortGroup mapping); (b) port mirroring per network monitoring; (c) integrazione con OVN per overlay (VXLAN, Geneve); (d) OpenFlow programmability. Setup tipico Proxmox+OVS: pacchetto `openvswitch-switch`, sostituisci `vmbr0` con `OVSBridge` in `/etc/network/interfaces`. Costo: maggior complessita, ~5-10% CPU overhead, debugging piu complesso. Per la maggior parte dei cluster Proxmox in PMI, *non vale*. Per multi-tenant SDN o overlay, si.

> **Errore comune — `bridge-vids` tropo permissive.** Configurare `bridge-vids 2-4094` su `vmbr0` permette a chiunque crei una VM con `tag=N` di usare *qualsiasi* VLAN, anche quelle non ammesse dalla policy. Best practice: `bridge-vids 10,20,30,40` per limitare alle VLAN effettivamente in uso. Cambiamenti di policy si fanno con un edit + `ifreload -a`.

> **Caso reale — Migrazione di NIC teaming `IP Hash` senza switch LAG.** Un cluster con dvSwitch in NIC teaming `Route based on IP hash` e stato migrato a Proxmox con bonding `802.3ad` (LACP), ma gli switch fisici non avevano LAG configurati. Per qualche minuto la rete sembrava OK (i frame trovavano comunque la strada), poi MAC flap massivo e perdita totale di connettivita. Soluzione: ridiscendere a bonding mode `active-backup` per il momento, e contattare il team networking per configurare LAG. Lezione: prima di scegliere mode 4, *verificare* che lo switch sia configurato. Comando di check: `ovs-appctl bond/show` su OVS o `cat /proc/net/bonding/bond0` su Linux.

---

## Esercizi

1. **Concettuale — traduzione port group.** Dato un dvPortGroup VMware "PG-Web" con VLAN 100 e NIC teaming "Originating port ID", produrre la configurazione equivalente Proxmox: (a) bridge config; (b) device VM `--net0`; (c) bonding (se necessario). *Risposta:* (a) `vmbr0` VLAN-aware con `bridge-vids 100`; (b) `--net0 virtio,bridge=vmbr0,tag=100`; (c) opzionale `bond0 mode 1` se 2+ NIC.

2. **Lab — `/etc/network/interfaces` produzione.** Configurare un nodo Proxmox per un cluster a 3 nodi con: 2x10 GbE per management+VM (LACP), 2x25 GbE per storage+migration (LACP), 1x1 GbE per Corosync (no bond). VLAN: 10 mgmt, 20 VM, 30 storage, 40 migration, 11 corosync. MTU 9000 su storage e migration. Produrre il file completo, validarlo con `ifreload -a -n` (dry-run), poi applicarlo.

3. **Scenario — switch single-vendor mixed.** Hai 2 switch Cisco e 2 switch HP per uplinks, e vuoi LAG cross-switch (2 verso Cisco, 2 verso HP) per resilienza. Argomenta in 8 righe la fattibilita: con LACP standard, lo switch deve essere lo stesso o usare MLAG/VPC tra coppie. *Risposta:* LACP cross-switch funziona solo se i due switch hanno MLAG/VPC (Cisco vPC, Arista MLAG, HP IRF) altrimenti gli switch vedono LACP partner mismatch. Soluzione fattibile: 2 LAG separati, uno per coppia (active-active backup) o un master/slave fra i due LAG. Oppure passare a mode 1 (active-backup) per perdita di throughput ma resilienza cross-vendor.

4. **Stretch — script di traduzione automatica.** Scrivere uno script Python che legge `dvswitches.csv` + `portgroups.csv` (output del modulo 05.1) e produce: (a) un file `proxmox-network-config.txt` con le stanze `auto/iface` per ogni VLAN; (b) un file `qm-tag-mapping.csv` con righe `vmid, dvportgroup, vlan_id, proxmox_tag`. Manualmente il sysadmin verifica e applica.

## Auto-valutazione

1. Differenza fra Linux Bridge "classico" e Linux Bridge VLAN-aware?
2. Comando per attivare un singolo file `interfaces.d/foo` senza riavviare la rete?
3. NIC Teaming "IP Hash" VMware mappa a quale Linux bonding mode?
4. MTU 9000 (jumbo frames): quale comando lo testa attraversando un peer remoto?
5. Cosa fa `ifreload -a -n` (dry-run) e perche e utile prima del deploy?
6. Quando OVS ha senso vs Linux Bridge nativo?
7. Quante VLAN puo gestire un singolo bridge VLAN-aware (massimo teorico)?
8. Cosa fa il flag `mtu 9000` in `/etc/network/interfaces` e su quale livello agisce (bridge / VLAN sub-iface / NIC)?

## Letture primarie consigliate

- [`PVE-WIKI`] Proxmox VE Wiki — Network Configuration. https://pve.proxmox.com/wiki/Network_Configuration
- [`LINUX-BRIDGE`] Linux Foundation — Bridge. https://wiki.linuxfoundation.org/networking/bridge
- [`BONDING`] Linux Ethernet Bonding driver howto (kernel.org). https://www.kernel.org/doc/Documentation/networking/bonding.txt
- [`IEEE-802.1AX`] IEEE 802.1AX — Link Aggregation. https://standards.ieee.org/ieee/802.1AX/4940/
- [`IEEE-802.1Q`] IEEE 802.1Q — VLANs. https://standards.ieee.org/ieee/802.1Q/6844/
- ifupdown2 documentation. https://github.com/CumulusNetworks/ifupdown2
- [`OVS-DOCS`] Open vSwitch Documentation. https://docs.openvswitch.org/en/latest/
- VMware vSphere Networking Guide. https://docs.vmware.com/en/VMware-vSphere/

## Collegamenti incrociati

- Modulo 01.2 — `../01-FONDAMENTI-VMWARE/vmware-networking-storage.md`: vSwitch source side.
- Modulo 04.1 — `../04-NETWORKING-AVANZATO-PROXMOX/linux-bridge-vlan-bonding.md`: target side, deep dive Linux Bridge.
- Modulo 07.1 — `ip-planning-dns-dhcp-firewall.md`: planning IP/DNS che precede questo mapping.
- Modulo 07.3 — `migrazione-vlan-e-segmentazione.md`: deep dive VLAN migration.
- Modulo 17.3 — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-networking-post-migrazione.md`: troubleshooting specifico.

## Glossario locale

| Termine | Definizione |
|---|---|
| **vSwitch** | VMware Virtual Switch (Standard, locale all'host). |
| **dvSwitch** | Distributed vSwitch VMware (gestito da vCenter, esteso fra host). |
| **dvPortGroup** | Port group sul dvSwitch (con VLAN ID, policy, NIOC). |
| **Linux Bridge** | Bridge L2 software del kernel Linux. |
| **VLAN-aware bridge** | Linux Bridge configurato per gestire frame 802.1Q tagged su un solo bridge per VLAN multiple. |
| **`bridge-vids`** | Lista VLAN ID accettate da un bridge VLAN-aware (es. `2-4094` o `10,20,30`). |
| **`bridge-pvid`** | Default VLAN per frame untagged (Port VLAN ID). |
| **NIC Teaming** | Aggregazione di piu NIC fisiche in un'interfaccia logica (VMware terminology). |
| **Linux Bonding** | Equivalente Linux di NIC Teaming, modulo `bonding` del kernel. |
| **Mode 0..6** | Modalita Linux bonding: 0 balance-rr, 1 active-backup, 2 balance-xor, 3 broadcast, 4 802.3ad (LACP), 5 balance-tlb, 6 balance-alb. |
| **`xmit_hash_policy`** | Algoritmo di hash per distribuire frame su bond slave: `layer2`, `layer2+3`, `layer3+4`. |
| **LAG / LACP** | Link Aggregation Group / LACP (IEEE 802.3ad). |
| **MLAG / VPC** | Multi-chassis LAG (Arista) / Virtual Port Channel (Cisco) — LAG cross-switch. |
| **MTU** | Maximum Transmission Unit; default Ethernet 1500, jumbo 9000. |
| **`ifreload -a -n`** | Dry-run: mostra cosa applicherebbe `ifreload -a` senza eseguirlo. |
| **`bridge link show`** | Comando per vedere bridge e relativo stato porte. |
| **`bridge vlan show`** | Comando per vedere VLAN registrate su un bridge VLAN-aware. |
| **OVSBridge** | Direttiva di `ifupdown2` per istanziare un bridge Open vSwitch. |
