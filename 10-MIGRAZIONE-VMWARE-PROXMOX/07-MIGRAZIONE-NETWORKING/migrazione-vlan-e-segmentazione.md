# Migrazione VLAN e Segmentazione di Rete da VMware a Proxmox

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 07.3 (chiude il cluster networking, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 07.1 e 07.2; concetti VLAN 802.1Q, PVLAN (Private VLAN); concetti di isolamento L2 e segmentazione di sicurezza.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. tradurre i 3 modi di tagging VMware (VST, EST, VGT) nei loro pendant Proxmox e capire quando va usato VGT (= VLAN ID 4095 = trunk al guest) per VM specifiche (firewall virtuale, NSX-T edge, router);
> 2. configurare un bridge VLAN-aware con `bridge-vids` selettivi (whitelist), invece di `2-4094` permissive, e validare con `bridge vlan show`;
> 3. configurare lo switch fisico (Cisco/Arista/HP/MikroTik) come trunk port verso il nodo Proxmox, native VLAN, allowed VLAN list;
> 4. assegnare VLAN per VM (`--net0 ...,tag=N`) e per gruppi di VM tramite **alias** e **IPSet** del Proxmox Firewall;
> 5. migrare configurazioni di **Private VLAN** (Promiscuous/Community/Isolated) da VMware verso una soluzione Proxmox SDN (zone EVPN o VLAN-aware con regole firewall) — limitazioni e workaround;
> 6. validare l'isolamento di rete con test concreti (ping cross-VLAN deve fallire; tcpdump deve confermare separazione; VLAN hopping attack via double-tagging deve essere bloccato).
> **Tempo stimato:** lettura 60-90 min · lab 240 min
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** Proxmox VE 8.x (`ifupdown2`); Cisco IOS 15.x/IOS-XE 17.x; Arista EOS 4.x; MikroTik RouterOS 7.x.

## Mappa concettuale

```
+======================================================+
|  VLAN tagging modes — translation                    |
+======================================================+
|                                                      |
|  VMware Mode    | Proxmox Equivalent                 |
|  ----------     | ------------------                 |
|  VST            | Bridge VLAN-aware + tag=N         |
|  (vSwitch tags) | sul --net0 della VM                |
|                 |                                    |
|  EST            | Switch fisico tagga                |
|  (External tag) | bridge "trasparente" no VLAN       |
|                 | (raro in Proxmox; non consigliato) |
|                 |                                    |
|  VGT            | tag=4095 (= trunk completo)        |
|  (VID 4095)     | Bridge VLAN-aware con bridge-vids  |
|                 | passa tutto al guest               |
|                 |                                    |
|                                                      |
|  Private VLAN modes:                                 |
|  Primary VLAN: 100                                   |
|    +-- Promiscuous Port (PG-Web)                     |
|    |    Sees: all (incl. isolated, community)        |
|    +-- Community VLAN: 101                           |
|    |    Members talk among themselves + promiscuous  |
|    +-- Isolated VLAN: 102                            |
|         Members talk only to promiscuous            |
|                                                      |
|  Proxmox PVLAN: native non supportato dal Linux      |
|  Bridge VLAN-aware standard.                         |
|  Workaround:                                         |
|    A. Use SDN zone EVPN/VXLAN (PVE 8.x SDN)         |
|    B. Use OVS con OpenFlow rules                     |
|    C. Use Proxmox Firewall rules per simulare      |
|       isolamento (community = bidir; isolated =     |
|       only-to-prom; promiscuous = no rule)          |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **VST e VGT coprono il 99% dei casi.** EST esiste come retrocompatibilita per ambienti dove lo switch fisico tagga prima dell'host (es. data center legacy con architettura "L2 puro"). Su Proxmox moderno, VST (bridge VLAN-aware + tag) e la norma; VGT serve solo per appliance virtuali (firewall, router) che fanno tagging multiplo internamente.
2. **Whitelist e meglio di permissive.** `bridge-vids 10,20,30,40` e auto-documenting. `bridge-vids 2-4094` significa "qualsiasi VLAN, anche quelle che non hai mai voluto". In ambienti multi-tenant, la whitelist e una difesa contro errori di configurazione VM.
3. **Switch fisico come trunk: native VLAN diversa da default.** Sul lato switch, `switchport trunk native vlan X` e configurabile per `X` diverso da 1; la VLAN nativa e quella per i frame untagged. *Coerenza con Proxmox*: se imposti native VLAN = 99 sul switch, sul Proxmox `bridge-pvid 99` deve corrispondere.
4. **PVLAN traduzione e meno netta.** Le PVLAN VMware (Promiscuous/Community/Isolated) non hanno equivalente diretto su Linux Bridge VLAN-aware. Soluzioni: (a) SDN Proxmox con zone EVPN/VXLAN per overlay multi-tenant; (b) OVS con flow rules; (c) Proxmox Firewall rules per simulare via filtraggio L3 (con limiti sul vero L2 isolation).
5. **Test di isolamento e step obbligatorio.** Dopo migrazione, fare tre test: (a) ping cross-VLAN deve *fallire* per VM su VLAN diverse senza routing autorizzato; (b) `tcpdump -ni vmbr0 vlan` su un nodo deve mostrare *solo* frame con i VID consentiti; (c) test VLAN hopping (Q-in-Q double-tagging): un attacco da VM A su VLAN 10 che invia frame double-tagged 10/20 deve *non raggiungere* VLAN 20.

## Indice
- [Panoramica](#panoramica)
- [VLAN Tagging in VMware: VST, EST e VGT](#vlan-tagging-in-vmware-vst-est-e-vgt)
- [VLAN 802.1Q in Proxmox: Bridge VLAN-Aware](#vlan-8021q-in-proxmox-bridge-vlan-aware)
- [Configurazione Trunk Port sugli Switch Fisici](#configurazione-trunk-port-sugli-switch-fisici)
- [Assegnazione VLAN per VM in Proxmox](#assegnazione-vlan-per-vm-in-proxmox)
- [Migrazione Private VLAN (PVLAN)](#migrazione-private-vlan-pvlan)
- [Validazione dell'Isolamento di Rete](#validazione-dellisolamento-di-rete)
- [Test di Connettività VLAN](#test-di-connettività-vlan)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

La corretta migrazione delle VLAN dall'ambiente VMware a Proxmox VE è un prerequisito critico per garantire la continuità operativa delle VM e il mantenimento delle policy di sicurezza di rete. VMware implementa il VLAN tagging attraverso tre modalità distinte — Virtual Switch Tagging (VST), External Switch Tagging (EST) e Virtual Guest Tagging (VGT) — ciascuna con implicazioni diverse sulla configurazione degli switch fisici e delle VM. Proxmox, basandosi sullo standard 802.1Q implementato nel kernel Linux, offre un modello più diretto ma che richiede una comprensione precisa di come i tag VLAN vengono gestiti a ogni livello dello stack.

Questo documento analizza in dettaglio il processo di migrazione delle VLAN, coprendo il mapping tra le modalità VMware e le corrispondenti configurazioni Proxmox, la configurazione dei bridge VLAN-aware, l'interazione con gli switch fisici, e le strategie per gestire casi complessi come le Private VLAN. Ogni sezione include configurazioni concrete, comandi di verifica e procedure di validazione per garantire che la segmentazione di rete sia preservata integralmente durante la transizione.

Un errore nella migrazione delle VLAN può avere conseguenze gravi: VM che perdono connettività, traffico che attraversa segmenti non autorizzati, violazione delle policy di sicurezza. Per questo motivo, la validazione sistematica post-migrazione è una fase imprescindibile, non opzionale. Il documento dedica ampio spazio alle procedure di test e verifica, includendo script di automazione per la validazione massiva.

---

## VLAN Tagging in VMware: VST, EST e VGT

VMware ESXi supporta tre modalità di VLAN tagging, ciascuna delle quali determina dove nella catena di rete avviene l'inserimento e la rimozione del tag 802.1Q.

### Virtual Switch Tagging (VST) — Modalità Predefinita

In VST, il vSwitch ESXi inserisce il tag VLAN sui frame in uscita dalla VM e lo rimuove sui frame in ingresso. La VM non vede mai il tag 802.1Q; dal punto di vista del guest, il traffico è untagged.

```
┌─────────────┐
│     VM      │  Frame untagged
│  (guest OS) │  La VM non è consapevole della VLAN
└──────┬──────┘
       │ untagged
┌──────┴──────────────────────────┐
│        vSwitch ESXi             │
│  Port Group: "Production"       │
│  VLAN ID: 100                   │
│                                 │
│  Il vSwitch aggiunge tag=100    │
│  ai frame in uscita e rimuove   │
│  tag=100 dai frame in ingresso  │
└──────┬──────────────────────────┘
       │ tagged (VLAN 100)
┌──────┴──────┐
│ Switch Fisico│  Trunk port: VLAN 100 allowed
└─────────────┘
```

Configurazione VMware (PowerCLI):
```powershell
# Port group con VLAN ID = 100 → modalità VST
Get-VirtualPortGroup -Name "Production" | Set-VirtualPortGroup -VLanId 100
```

In Proxmox, la modalità VST corrisponde all'assegnazione del `tag=<VLAN_ID>` sulla NIC virtuale della VM nel file di configurazione:

```
# /etc/pve/qemu-server/100.conf
net0: virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0,tag=100
```

### External Switch Tagging (EST)

In EST, il vSwitch VMware non esegue alcun tagging. Il port group ha VLAN ID = 0 (nessuna VLAN). Il tag viene gestito interamente dallo switch fisico tramite access port o native VLAN.

```
┌─────────────┐
│     VM      │  Frame untagged
└──────┬──────┘
       │ untagged
┌──────┴──────────────────────────┐
│        vSwitch ESXi             │
│  Port Group: "Default"          │
│  VLAN ID: 0 (nessuno)           │
│                                 │
│  Nessun tagging                 │
└──────┬──────────────────────────┘
       │ untagged
┌──────┴──────┐
│ Switch Fisico│  Access port: VLAN 100
│              │  (lo switch aggiunge il tag)
└─────────────┘
```

In Proxmox, l'EST si replica semplicemente non specificando il tag sulla NIC della VM:

```
# /etc/pve/qemu-server/101.conf
net0: virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0
```

Lo switch fisico deve avere la porta configurata come access port nella VLAN corretta, esattamente come nell'ambiente VMware.

### Virtual Guest Tagging (VGT)

In VGT, il tagging avviene all'interno della VM stessa. Il guest OS invia frame con tag 802.1Q, e il vSwitch li passa allo switch fisico senza modificarli. Il port group VMware ha VLAN ID = 4095, che è il valore speciale che abilita il passthrough di tutti i tag VLAN.

```
┌──────────────────────┐
│     VM (guest OS)     │
│  eth0.100 (VLAN 100) │  Frame tagged dal guest
│  eth0.200 (VLAN 200) │
└──────┬───────────────┘
       │ tagged (VLAN 100, 200)
┌──────┴──────────────────────────┐
│        vSwitch ESXi             │
│  Port Group: "Trunk"            │
│  VLAN ID: 4095 (pass-through)   │
│                                 │
│  Tutti i tag passano invariati  │
└──────┬──────────────────────────┘
       │ tagged
┌──────┴──────┐
│ Switch Fisico│  Trunk port: VLAN 100, 200 allowed
└─────────────┘
```

In Proxmox, per abilitare VGT, la VM viene connessa al bridge senza tag e il bridge deve essere VLAN-aware. La VM gestirà autonomamente il tagging nel guest OS:

```
# /etc/pve/qemu-server/102.conf
# Nessun tag = la VM può taggare autonomamente
net0: virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0
```

Per limitare le VLAN che la VM può utilizzare (equivalente alla trunk VLAN list sullo switch), è possibile usare le regole firewall di Proxmox o, con OVS, configurare il trunking esplicito.

### Tabella Riepilogativa di Mapping

| VMware Mode | VLAN ID nel Port Group | Chi fa il tagging | Proxmox Equivalent | Configurazione VM |
|---|---|---|---|---|
| **VST** | 1-4094 | vSwitch | VLAN-aware bridge + tag | `tag=<ID>` sulla NIC |
| **EST** | 0 | Switch fisico | Bridge senza tag | Nessun tag sulla NIC |
| **VGT** | 4095 | Guest OS | Bridge senza tag + guest tagging | Nessun tag; VLAN nel guest |

---

## VLAN 802.1Q in Proxmox: Bridge VLAN-Aware

### Abilitazione del Bridge VLAN-Aware

Il bridge VLAN-aware è il meccanismo raccomandato per gestire le VLAN in Proxmox. Utilizza il sottosistema `bridge vlan` del kernel Linux per gestire il tagging 802.1Q in modo efficiente e scalabile.

Configurazione base in `/etc/network/interfaces`:

```
auto vmbr0
iface vmbr0 inet static
    address 10.0.10.11/24
    gateway 10.0.10.1
    bridge-ports bond0
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 2-4094
    bridge-pvid 1
```

Parametri chiave:

| Parametro | Descrizione | Valori |
|---|---|---|
| `bridge-vlan-aware` | Abilita il filtraggio VLAN sul bridge | `yes` / `no` |
| `bridge-vids` | Lista delle VLAN ammesse sul bridge | Range (es. `2-4094`) o lista (es. `10 20 100`) |
| `bridge-pvid` | Port VLAN ID: VLAN assegnata ai frame untagged in ingresso | Singolo ID (default: 1) |

### Funzionamento Interno del VLAN Filtering

Quando `bridge-vlan-aware yes` è attivo, il kernel Linux mantiene una tabella VLAN per ogni porta del bridge. Ogni frame in ingresso viene classificato in base al tag 802.1Q o al PVID (se untagged). Il frame viene inoltrato solo alle porte che hanno quella VLAN nella loro lista `bridge-vids`.

```
                   Frame in ingresso
                          │
                   ┌──────┴───────┐
                   │ Ha tag 802.1Q?│
                   └──┬────────┬──┘
                  Sì  │        │  No
                      │        │
              ┌───────┴──┐  ┌──┴──────────┐
              │Tag = VLAN │  │Assegna PVID │
              │del frame  │  │della porta  │
              └───────┬──┘  └──┬──────────┘
                      │        │
              ┌───────┴────────┴──────┐
              │  VLAN è nell'elenco    │
              │  bridge-vids della     │
              │  porta di ingresso?    │
              └──┬────────────────┬───┘
                Sì│               │No
                  │               │
          ┌───────┴──┐      ┌────┴────┐
          │ Inoltra a │      │ DROP    │
          │ porte con │      │         │
          │ stessa    │      └─────────┘
          │ VLAN      │
          └──────────┘
```

### Configurazione con VLAN Specifiche

Per ambienti di produzione, è buona pratica limitare le VLAN ammesse al set effettivamente utilizzato:

```
auto vmbr0
iface vmbr0 inet static
    address 10.0.10.11/24
    gateway 10.0.10.1
    bridge-ports bond0
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 10 20 30 100 110 200 300
    bridge-pvid 10
```

### Assegnazione dell'IP dell'Host a una VLAN Specifica

L'indirizzo IP del host Proxmox (per management) viene assegnato direttamente al bridge. Il PVID (`bridge-pvid`) determina su quale VLAN il traffico del host viene taggato. In alternativa, si può creare una VLAN sub-interface del bridge:

```
# Metodo 1: IP direttamente sul bridge con PVID
auto vmbr0
iface vmbr0 inet static
    address 10.0.10.11/24
    gateway 10.0.10.1
    bridge-ports bond0
    bridge-vlan-aware yes
    bridge-vids 10 100 200
    bridge-pvid 10

# Metodo 2: IP su VLAN sub-interface del bridge
auto vmbr0
iface vmbr0 inet manual
    bridge-ports bond0
    bridge-vlan-aware yes
    bridge-vids 10 100 200

auto vmbr0.10
iface vmbr0.10 inet static
    address 10.0.10.11/24
    gateway 10.0.10.1
```

Il metodo 2 è più esplicito e consente di avere indirizzi IP su più VLAN contemporaneamente:

```
auto vmbr0.10
iface vmbr0.10 inet static
    address 10.0.10.11/24
    gateway 10.0.10.1

auto vmbr0.20
iface vmbr0.20 inet static
    address 10.0.20.11/24
```

### Bridge Multipli vs Bridge Singolo VLAN-Aware

| Criterio | Bridge Multipli (Traditional) | Bridge Singolo VLAN-Aware |
|---|---|---|
| Complessità configurazione | Alta (un bridge per VLAN) | Bassa (un solo bridge) |
| Scalabilità | Limitata (max ~4096 bridge) | Alta (tutte le VLAN su un bridge) |
| Performance | Overhead per bridge multipli | Migliore (singolo datapath) |
| Isolamento | Fisico (bridge separati) | Logico (VLAN filtering) |
| Gestione VM | Selezionare il bridge corretto | Assegnare il tag VLAN |
| Compatibilità OVS | Non applicabile | Non applicabile |
| Caso d'uso ideale | Reti con requisiti di isolamento fisico | Maggior parte delle migrazioni |

---

## Configurazione Trunk Port sugli Switch Fisici

### Principi Generali

Lo switch fisico deve essere configurato per passare i frame tagged 802.1Q verso le porte connesse agli host Proxmox. La configurazione è identica a quella utilizzata per gli host VMware ESXi, a condizione che le stesse VLAN siano richieste.

Punti critici da verificare:
1. **Trunk mode**: la porta deve essere in modalità trunk (802.1Q)
2. **Allowed VLAN list**: tutte le VLAN utilizzate dalle VM devono essere nella lista
3. **Native VLAN**: la VLAN untagged deve corrispondere al PVID configurato su Proxmox
4. **Spanning Tree**: verificare che il PortFast/Edge port sia configurato per evitare ritardi

### Cisco IOS / IOS-XE

```
interface GigabitEthernet0/1
  description "Proxmox Host 1 - bond0 member"
  switchport mode trunk
  switchport trunk encapsulation dot1q
  switchport trunk allowed vlan 10,20,30,100,110,200,300
  switchport trunk native vlan 10
  spanning-tree portfast trunk
  no shutdown
```

Verifica:
```
show interfaces GigabitEthernet0/1 switchport
show interfaces GigabitEthernet0/1 trunk
show vlan brief
```

### Cisco Nexus (NX-OS)

```
interface Ethernet1/1
  description Proxmox Host 1 - bond0 member
  switchport
  switchport mode trunk
  switchport trunk allowed vlan 10,20,30,100,110,200,300
  switchport trunk native vlan 10
  spanning-tree port type edge trunk
  no shutdown
```

### Juniper JunOS

```
set interfaces ge-0/0/0 description "Proxmox Host 1"
set interfaces ge-0/0/0 unit 0 family ethernet-switching port-mode trunk
set interfaces ge-0/0/0 unit 0 family ethernet-switching vlan members [ Management Production Development Storage Migration ]
set interfaces ge-0/0/0 native-vlan-id 10
```

### HP/Aruba ProCurve

```
interface 1
  name "Proxmox Host 1 - bond0"
  tagged vlan 20,30,100,110,200,300
  untagged vlan 10
  spanning-tree admin-edge-port
  exit
```

### Verifica del Trunking dal Lato Proxmox

Dopo aver configurato lo switch, verificare dal host Proxmox che i frame tagged vengano ricevuti correttamente:

```bash
# Catturare traffico tagged sull'interfaccia fisica
tcpdump -i eno1 -e -nn vlan -c 30

# Output atteso: frame con tag 802.1Q visibili
# 12:34:56.789 AA:BB:CC:DD:EE:FF > FF:FF:FF:FF:FF:FF, ethertype 802.1Q (0x8100),
# vlan 100, p 0, ethertype ARP, ...

# Verificare VLAN membership sul bridge
bridge vlan show
# Output atteso:
# port    vlan ids
# bond0    10 PVID Egress Untagged
#          20
#          30
#          100
#          110
#          200

# Verificare che il bridge stia apprendendo MAC sulle VLAN corrette
bridge fdb show br vmbr0 | grep -v permanent
```

---

## Assegnazione VLAN per VM in Proxmox

### Tramite Web UI

Nella web UI di Proxmox (https://host:8006):
1. Selezionare la VM → Hardware → Network Device
2. Nel campo **Bridge** selezionare il bridge VLAN-aware (es. `vmbr0`)
3. Nel campo **VLAN Tag** inserire l'ID VLAN (es. `100`)
4. Fare clic su OK

### Tramite CLI

```bash
# Assegnare VLAN 100 alla NIC net0 della VM 100
qm set 100 -net0 virtio,bridge=vmbr0,tag=100

# Assegnare VLAN 200 a una seconda NIC
qm set 100 -net1 virtio,bridge=vmbr0,tag=200

# Rimuovere il tag VLAN (traffico untagged)
qm set 100 -net0 virtio,bridge=vmbr0

# Verificare la configurazione
qm config 100 | grep net
```

### Tramite File di Configurazione

```bash
# /etc/pve/qemu-server/100.conf
# VM con due NIC su VLAN diverse
net0: virtio=A2:B4:C6:D8:E0:F2,bridge=vmbr0,firewall=1,tag=100
net1: virtio=A2:B4:C6:D8:E0:F3,bridge=vmbr0,firewall=1,tag=200
```

### Migrazione Massiva delle VLAN

Per migrare molte VM mantenendo le stesse VLAN, è utile uno script che legga l'inventario VMware e configuri automaticamente le VM Proxmox:

```bash
#!/bin/bash
# migrate_vlans.sh
# Input: CSV con formato "vmid,vlan_id"
# Esempio: 100,100
#          101,110
#          102,200

CSV_FILE="vm_vlan_mapping.csv"
BRIDGE="vmbr0"

while IFS=',' read -r vmid vlan_id; do
    # Ignora header e righe vuote
    [[ "$vmid" == "vmid" ]] && continue
    [[ -z "$vmid" ]] && continue

    echo "Configurando VM $vmid con VLAN $vlan_id su bridge $BRIDGE"

    # Leggi la configurazione attuale della NIC
    current_net=$(qm config "$vmid" 2>/dev/null | grep "^net0:")
    if [[ -z "$current_net" ]]; then
        echo "  ATTENZIONE: VM $vmid non trovata o senza net0"
        continue
    fi

    # Estrai il MAC address dalla configurazione corrente
    mac=$(echo "$current_net" | grep -oP '[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}')

    # Applica la nuova configurazione
    qm set "$vmid" -net0 "virtio=$mac,bridge=$BRIDGE,tag=$vlan_id,firewall=1"

    if [[ $? -eq 0 ]]; then
        echo "  OK: VM $vmid configurata su VLAN $vlan_id"
    else
        echo "  ERRORE: impossibile configurare VM $vmid"
    fi
done < "$CSV_FILE"
```

---

## Migrazione Private VLAN (PVLAN)

### Concetti Private VLAN in VMware

Le Private VLAN (PVLAN) sono una funzionalità disponibile esclusivamente sul vDS (vSwitch Distributed) che permette un isolamento più granulare all'interno di una singola VLAN primaria. VMware supporta tre tipi di porta PVLAN:

| Tipo Porta PVLAN | Comportamento | Caso d'Uso |
|---|---|---|
| **Promiscuous** | Comunica con tutte le porte (isolated e community) | Router, gateway, servizi condivisi |
| **Isolated** | Comunica solo con porte promiscuous, non con altre isolated o community | VM che non devono comunicare tra loro |
| **Community** | Comunica con porte promiscuous e con altre porte nella stessa community, non con isolated o altre community | Gruppi di VM che devono comunicare tra loro ma essere isolati da altri gruppi |

Esempio di configurazione PVLAN VMware:

```
Primary VLAN: 100
  ├── Promiscuous: VLAN 100 (gateway, DNS, servizi condivisi)
  ├── Isolated: VLAN 101 (VM web server isolati)
  └── Community 1: VLAN 102 (cluster app server)
  └── Community 2: VLAN 103 (cluster database)
```

### Sfide della Migrazione PVLAN

Proxmox con Linux Bridge **non supporta nativamente** le Private VLAN. Questo è uno dei gap funzionali più significativi nella migrazione da un vDS VMware avanzato. Le opzioni disponibili sono:

#### Opzione 1: Conversione PVLAN in VLAN Standard (Raccomandata)

Convertire ogni secondary VLAN in una VLAN standard con routing inter-VLAN controllato tramite firewall:

```
PVLAN VMware                    →    VLAN Standard Proxmox
─────────────────────────────────────────────────────────
Primary 100 (Promiscuous)       →    VLAN 100 (servizi condivisi)
Secondary 101 (Isolated)        →    VLAN 101 (web servers)
Secondary 102 (Community 1)     →    VLAN 102 (app servers)
Secondary 103 (Community 2)     →    VLAN 103 (databases)
```

L'isolamento precedentemente fornito dal PVLAN viene implementato tramite regole firewall Proxmox:

```bash
# /etc/pve/firewall/cluster.fw
# Bloccare comunicazione tra VLAN 101 (ex-isolated) instances
[RULES]
# Permettere VLAN 101 → VLAN 100 (servizi condivisi)
IN ACCEPT -source 10.0.101.0/24 -dest 10.0.100.0/24 -log nolog
# Permettere VLAN 100 → VLAN 101
IN ACCEPT -source 10.0.100.0/24 -dest 10.0.101.0/24 -log nolog
# Bloccare VLAN 101 → VLAN 101 (isolamento tra peers)
IN DROP -source 10.0.101.0/24 -dest 10.0.101.0/24 -log nolog
# Permettere VLAN 102 ↔ VLAN 100
IN ACCEPT -source 10.0.102.0/24 -dest 10.0.100.0/24 -log nolog
IN ACCEPT -source 10.0.100.0/24 -dest 10.0.102.0/24 -log nolog
# Permettere comunicazione intra-community VLAN 102
IN ACCEPT -source 10.0.102.0/24 -dest 10.0.102.0/24 -log nolog
```

#### Opzione 2: Open vSwitch con PVLAN

OVS supporta le PVLAN. Se la funzionalità è critica e la conversione in VLAN standard non è accettabile:

```bash
# Creare bridge OVS
ovs-vsctl add-br vmbr0

# Configurare PVLAN
# Primary VLAN 100, Isolated secondary 101
ovs-vsctl set port vm100-port0 tag=100 \
    other_config:qinq-ethtype=802.1Q

# Configurare porta promiscuous
ovs-vsctl set port gateway-port tag=100 \
    trunks=100,101,102,103 \
    vlan_mode=native-untagged

# Configurare porta isolated
ovs-vsctl set port vm-isolated-port tag=101 \
    vlan_mode=dot1q-tunnel
```

**Nota**: il supporto PVLAN in OVS è complesso e non ben integrato con l'interfaccia Proxmox. La conversione in VLAN standard (Opzione 1) è fortemente raccomandata per semplicità e manutenibilità.

#### Opzione 3: ebtables per Isolamento Layer 2

Per replicare il comportamento "isolated" senza PVLAN, si possono usare regole ebtables che impediscono la comunicazione diretta tra VM sulla stessa VLAN:

```bash
# Bloccare traffico diretto tra VM isolated sulla stessa VLAN
# Permettere solo traffico verso il gateway (MAC del router)
ebtables -A FORWARD -i veth101i0 -o veth101i1 -j DROP
ebtables -A FORWARD -i veth101i1 -o veth101i0 -j DROP
# Permettere traffico verso il gateway
ebtables -A FORWARD -i veth101i0 -d 00:AA:BB:CC:DD:EE -j ACCEPT
```

Questo approccio è fragile e non scalabile. Utilizzarlo solo come soluzione temporanea.

---

## Validazione dell'Isolamento di Rete

### Matrice di Test di Isolamento

Dopo la migrazione, è fondamentale verificare che l'isolamento di rete sia preservato. Creare una matrice di test che copra tutte le combinazioni VLAN:

| Sorgente → Destinazione | VLAN 100 | VLAN 110 | VLAN 200 | VLAN 10 (mgmt) |
|---|---|---|---|---|
| **VLAN 100** (Produzione) | PASS (intra-VLAN) | BLOCK | BLOCK | BLOCK |
| **VLAN 110** (Sviluppo) | BLOCK | PASS (intra-VLAN) | BLOCK | BLOCK |
| **VLAN 200** (DMZ) | BLOCK | BLOCK | PASS (intra-VLAN) | BLOCK |
| **VLAN 10** (Management) | PASS (via router) | PASS (via router) | PASS (via router) | PASS |

### Script di Validazione Automatizzato

```bash
#!/bin/bash
# validate_vlan_isolation.sh
# Esegue test di connettività tra VM su VLAN diverse
# Richiede: VM di test con IP noto su ciascuna VLAN

declare -A VLAN_TEST_IPS
VLAN_TEST_IPS[100]="10.0.100.10"
VLAN_TEST_IPS[110]="10.0.110.10"
VLAN_TEST_IPS[200]="10.0.200.10"
VLAN_TEST_IPS[10]="10.0.10.11"

# Matrice di risultati attesi: "PASS" o "BLOCK"
declare -A EXPECTED
EXPECTED["100-100"]="PASS"
EXPECTED["100-110"]="BLOCK"
EXPECTED["100-200"]="BLOCK"
EXPECTED["100-10"]="BLOCK"
EXPECTED["110-100"]="BLOCK"
EXPECTED["110-110"]="PASS"
EXPECTED["110-200"]="BLOCK"
EXPECTED["110-10"]="BLOCK"

VLANS=(100 110 200 10)
RESULTS_FILE="/tmp/vlan_isolation_results_$(date +%Y%m%d_%H%M%S).txt"

echo "=== Test di Isolamento VLAN ===" | tee "$RESULTS_FILE"
echo "Data: $(date)" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

PASS_COUNT=0
FAIL_COUNT=0

for src_vlan in "${VLANS[@]}"; do
    for dst_vlan in "${VLANS[@]}"; do
        key="${src_vlan}-${dst_vlan}"
        expected="${EXPECTED[$key]}"
        [[ -z "$expected" ]] && continue

        dst_ip="${VLAN_TEST_IPS[$dst_vlan]}"

        # Ping con timeout breve
        if ping -c 2 -W 1 "$dst_ip" &>/dev/null; then
            result="REACHABLE"
        else
            result="UNREACHABLE"
        fi

        # Valutare se il risultato è corretto
        if [[ "$expected" == "PASS" && "$result" == "REACHABLE" ]]; then
            status="OK"
            ((PASS_COUNT++))
        elif [[ "$expected" == "BLOCK" && "$result" == "UNREACHABLE" ]]; then
            status="OK"
            ((PASS_COUNT++))
        else
            status="FAIL"
            ((FAIL_COUNT++))
        fi

        printf "VLAN %-4s → VLAN %-4s | Atteso: %-5s | Risultato: %-12s | %s\n" \
            "$src_vlan" "$dst_vlan" "$expected" "$result" "$status" | tee -a "$RESULTS_FILE"
    done
done

echo "" | tee -a "$RESULTS_FILE"
echo "Riepilogo: $PASS_COUNT OK, $FAIL_COUNT FAIL" | tee -a "$RESULTS_FILE"

if [[ $FAIL_COUNT -gt 0 ]]; then
    echo "ATTENZIONE: $FAIL_COUNT test falliti! Verificare la configurazione." | tee -a "$RESULTS_FILE"
    exit 1
fi
```

### Verifica con tcpdump

Per un'analisi più dettagliata, catturare il traffico sul bridge e verificare che i frame VLAN siano correttamente isolati:

```bash
# Catturare traffico su una specifica VLAN
tcpdump -i vmbr0 -e -nn vlan 100 -c 50

# Catturare traffico tra due IP specifici
tcpdump -i vmbr0 -e -nn host 10.0.100.10 and host 10.0.110.10

# Se il secondo comando mostra traffico, l'isolamento inter-VLAN è compromesso

# Verificare che non ci sia traffico untagged imprevisto
tcpdump -i vmbr0 -e -nn 'not vlan' -c 20
```

### Verifica con arping

Per testare la raggiungibilità Layer 2 all'interno della stessa VLAN:

```bash
# Verificare raggiungibilità L2 sulla VLAN 100
arping -I vmbr0.100 10.0.100.10 -c 3

# Se arping risponde, la connettività L2 è funzionante
# Se non risponde, verificare: VLAN tagging, MAC learning, switch fisico
```

---

## Test di Connettività VLAN

### Procedura di Test Completa

Per ogni VLAN migrata, eseguire la seguente sequenza di test:

```
Test 1: Connettività Layer 2 (ARP)
    │
    ├── arping verso gateway della VLAN
    ├── arping verso altra VM sulla stessa VLAN
    └── Verifica MAC learning: bridge fdb show | grep <MAC>
    │
Test 2: Connettività Layer 3 (IP)
    │
    ├── ping verso gateway
    ├── ping verso DNS server
    ├── ping verso altra VM stessa VLAN
    └── ping con dimensione MTU (jumbo se applicabile)
    │
Test 3: Connettività Servizi (Layer 4-7)
    │
    ├── DNS resolution (nslookup/dig)
    ├── HTTP/HTTPS verso servizi interni
    ├── Connessione database
    └── Servizi specifici dell'applicazione
    │
Test 4: Isolamento Inter-VLAN
    │
    ├── Ping verso VM su VLAN diversa (deve fallire se non routato)
    ├── Tentativo di ARP verso subnet diversa
    └── Verifica che il routing inter-VLAN passi dal firewall
```

### Tool di Diagnostica Avanzata

```bash
# Verifica completa dello stato bridge e VLAN
bridge -d vlan show

# Output dettagliato con flag:
# port    vlan ids
# bond0    10 PVID Egress Untagged
#          20
#          100
#          110
# veth100i0 100 PVID Egress Untagged   ← VM 100, tag=100

# Statistiche per VLAN (kernel 4.19+)
bridge -s vlan show

# Verifica MAC address table per VLAN
bridge fdb show br vmbr0 vlan 100

# Traceroute per verificare il path di routing inter-VLAN
traceroute -n 10.0.110.10
# Il primo hop deve essere il gateway/firewall, non un percorso diretto

# Verifica ARP table dell'host
ip neigh show dev vmbr0
```

### Monitoring Continuo Post-Migrazione

Dopo aver completato la migrazione delle VLAN, è consigliabile monitorare il traffico per alcuni giorni per identificare anomalie:

```bash
# Contare frame per VLAN nell'arco di 60 secondi
timeout 60 tcpdump -i bond0 -e -nn vlan 2>/dev/null | \
    grep -oP 'vlan \d+' | sort | uniq -c | sort -rn

# Monitorare broadcast storm (elevato numero di broadcast)
timeout 30 tcpdump -i vmbr0 -e -nn broadcast -c 1000 2>/dev/null | wc -l
# Se il conteggio è vicino a 1000 in 30 secondi, potrebbe esserci un loop

# Log delle VLAN sconosciute (frame con tag non in bridge-vids)
journalctl -k | grep -i "vlan.*filtered"
```

---

## Best Practices

- **Utilizzare bridge VLAN-aware** come standard. La modalità traditional (un bridge per VLAN) è mantenuta per retrocompatibilità ma aggiunge complessità inutile.

- **Limitare `bridge-vids` alle VLAN effettivamente necessarie** anziché usare il range completo `2-4094`. Questo riduce la superficie di attacco e previene la propagazione di traffico inatteso.

- **Mantenere gli stessi VLAN ID** dell'ambiente VMware durante la migrazione. Cambiare VLAN ID aggiunge complessità e rischio di errore senza benefici.

- **Documentare ogni VLAN** con: ID, nome descrittivo, subnet, gateway, funzione, VM associate. Questa documentazione è il contratto tra team network e team virtualizzazione.

- **Verificare la configurazione trunk sullo switch fisico** prima di migrare ogni VLAN. Il problema più comune è una VLAN mancante nella allowed list dello switch.

- **Testare l'isolamento inter-VLAN** dopo la migrazione. Non assumere che l'isolamento sia preservato solo perché le VLAN sono configurate correttamente.

- **Convertire le PVLAN in VLAN standard** con regole firewall piuttosto che tentare di replicare il comportamento PVLAN su Proxmox. La complessità aggiuntiva delle PVLAN non giustifica il rischio operativo.

- **Utilizzare il PVID corretto** per il traffico di management dell'host. Un PVID errato può rendere l'host irraggiungibile.

- **Configurare il firewall Proxmox per VM** (`firewall=1` nella configurazione NIC) per aggiungere un ulteriore livello di isolamento oltre a quello fornito dalle VLAN.

- **Pianificare la migrazione VLAN per VLAN**, non tutte contemporaneamente. Migrare prima le VLAN di sviluppo/test, poi le VLAN di produzione, validando ogni passaggio.

- **Mantenere uno switch di test** o un ambiente lab dove poter verificare le configurazioni trunk e VLAN prima di applicarle in produzione.

- **Utilizzare la nomenclatura delle VLAN** in modo coerente. Aggiungere commenti nel file `/etc/network/interfaces` che mappano ogni VLAN ID al nome del port group VMware originale.

---

## Troubleshooting

### Problema: VM Non Riceve Traffico sulla VLAN Corretta
**Sintomi**: la VM è accesa e l'interfaccia di rete nel guest è up, ma non riceve risposte ARP né ping. Altre VM sulla stessa VLAN funzionano correttamente.
**Causa**: il tag VLAN nella configurazione della VM non corrisponde alla VLAN effettiva, oppure il tag è stato omesso e il traffico viene inviato sulla VLAN nativa (PVID) del bridge anziché sulla VLAN corretta.
**Soluzione**: verificare la configurazione della VM con `qm config <vmid> | grep net`. Assicurarsi che il parametro `tag=<VLAN_ID>` sia presente e corretto. Verificare con `bridge vlan show` che la porta della VM abbia la VLAN corretta. Se la VLAN è assente, aggiornare con `qm set <vmid> -net0 virtio,bridge=vmbr0,tag=<VLAN_ID>`.
**Prevenzione**: creare il file CSV di mapping VLAN dall'inventario VMware e utilizzare lo script di migrazione massiva per configurare tutte le VM in modo consistente.

### Problema: Bridge VLAN-Aware Non Filtra Correttamente
**Sintomi**: le VM su VLAN diverse possono comunicare direttamente tra loro a livello Layer 2, bypassando il router/firewall.
**Causa**: `bridge-vlan-aware yes` non è impostato o non è stato applicato dopo la modifica. Il bridge opera in modalità tradizionale senza filtraggio VLAN.
**Soluzione**: verificare con `bridge vlan show`. Se l'output mostra "PVID Egress Untagged" su tutte le VLAN per tutte le porte, il filtraggio è attivo. Se l'output non mostra informazioni VLAN, il bridge non è VLAN-aware. Aggiungere `bridge-vlan-aware yes` in `/etc/network/interfaces` e applicare con `ifreload -a`. Verificare con `cat /sys/class/net/vmbr0/bridge/vlan_filtering` che il valore sia `1`.
**Prevenzione**: verificare sempre il flag `vlan_filtering` dopo la configurazione iniziale del bridge.

### Problema: VLAN Mancante sullo Switch Fisico
**Sintomi**: una specifica VLAN non funziona su Proxmox, mentre tutte le altre VLAN funzionano correttamente. Il bridge mostra la VLAN configurata, ma `tcpdump` non cattura frame tagged per quella VLAN sulle interfacce fisiche.
**Causa**: la VLAN non è nella lista delle allowed VLAN sulla trunk port dello switch fisico, oppure la VLAN non è stata creata sul dominio VTP/VLAN database dello switch.
**Soluzione**: sullo switch, verificare con `show interfaces trunk` (Cisco) che la VLAN sia nella lista "Vlans allowed and active in management domain". Se assente, aggiungerla: `switchport trunk allowed vlan add <VLAN_ID>`. Verificare che la VLAN esista: `show vlan id <VLAN_ID>`. Se non esiste, crearla: `vlan <VLAN_ID>` / `name <description>`.
**Prevenzione**: prima della migrazione, confrontare la lista VLAN configurate su VMware con quelle ammesse sulle trunk port dello switch verso i nuovi host Proxmox.

### Problema: Traffico Untagged sulla VLAN Sbagliata
**Sintomi**: l'host Proxmox è raggiungibile ma con un indirizzo IP nella subnet sbagliata, oppure le VM senza VLAN tag finiscono su una VLAN diversa da quella prevista.
**Causa**: mismatch tra il `bridge-pvid` configurato sul bridge Proxmox e la native VLAN configurata sullo switch fisico. Il PVID determina quale VLAN viene assegnata ai frame untagged.
**Soluzione**: verificare il PVID del bridge con `bridge vlan show` (cercare il flag "PVID"). Verificare la native VLAN sullo switch con `show interfaces trunk` (cercare "Native vlan"). I due valori devono corrispondere. Correggere uno dei due per allinearli.
**Prevenzione**: documentare la native VLAN dello switch e configurare il `bridge-pvid` di conseguenza. Se si utilizza la VLAN 10 per il management, sia il PVID che la native VLAN devono essere 10.

### Problema: Performance Degradata su VLAN Specifica
**Sintomi**: throughput ridotto o latenza elevata su una sola VLAN, mentre le altre funzionano normalmente.
**Causa**: possibile mismatch MTU su quella specifica VLAN, oppure broadcast storm isolata a quella VLAN (ad esempio, un loop su un segmento collegato alla stessa VLAN su un altro switch).
**Soluzione**: verificare con `ethtool -S eno1 | grep -i error` se ci sono errori sull'interfaccia fisica. Controllare il tasso di broadcast con `tcpdump -i vmbr0 -e vlan <ID> broadcast -c 100` e misurare quanti frame broadcast al secondo ci sono. Se sono eccessivi (>1000/s), cercare il loop. Verificare MTU con `ping -M do -s 1472 <dest>` sulla VLAN problematica.
**Prevenzione**: monitorare il traffico broadcast per VLAN dopo la migrazione. Configurare storm control sullo switch fisico.

### Problema: VGT (Guest Tagging) Non Funziona
**Sintomi**: una VM configurata per taggare internamente (VGT, ex VLAN 4095 su VMware) non riesce a comunicare dopo la migrazione a Proxmox. Le sub-interface VLAN nel guest sono configurate ma non ricevono traffico.
**Causa**: la VM è collegata al bridge con un tag esplicito, che sovrascrive i tag generati dal guest. In VGT, la NIC della VM non deve avere un tag assegnato da Proxmox.
**Soluzione**: rimuovere il parametro `tag=` dalla configurazione NIC della VM: `qm set <vmid> -net0 virtio,bridge=vmbr0` (senza tag). Verificare che il bridge sia VLAN-aware e che le VLAN utilizzate dal guest siano nel range `bridge-vids`.
**Prevenzione**: identificare le VM che utilizzano VGT (VLAN 4095) durante l'inventario VMware e trattarle separatamente nel piano di migrazione.

### Problema: MAC Address Flapping sul Bridge
**Sintomi**: log del kernel con messaggi tipo `bridge: vmbr0: received packet on bond0 with own address as source address`. Connettività intermittente per alcune VM.
**Causa**: due porte del bridge vedono lo stesso MAC address, causando un conflitto nella FDB (Forwarding Database). Tipicamente accade quando la stessa VM è attiva sia su VMware che su Proxmox, o quando un loop crea duplicazione di frame.
**Soluzione**: verificare con `bridge fdb show br vmbr0 | grep <MAC>` se lo stesso MAC appare su porte diverse. Se la VM è duplicata, spegnere l'istanza VMware. Se c'è un loop, abilitare STP: `brctl stp vmbr0 on`.
**Prevenzione**: seguire una procedura di cutover rigorosa: spegnere su VMware prima di avviare su Proxmox. Monitorare la FDB durante la migrazione.

---

## Riferimenti

- [Proxmox VE Network Configuration - VLAN](https://pve.proxmox.com/wiki/Network_Configuration#_vlan_802_1q)
- [Linux Bridge VLAN Filtering - Kernel Documentation](https://www.kernel.org/doc/html/latest/networking/bridge.html#vlan-filtering)
- [IEEE 802.1Q - VLAN Standard](https://standards.ieee.org/standard/802_1Q-2018.html)
- [VMware vSphere Networking - VLAN Configuration](https://docs.vmware.com/en/VMware-vSphere/7.0/vsphere-esxi-vcenter-server-703-networking-guide.pdf)
- [Open vSwitch VLAN Configuration](https://docs.openvswitch.org/en/latest/howto/vlan/)
- [Proxmox Firewall Documentation](https://pve.proxmox.com/wiki/Firewall)
- [ifupdown2 - Bridge VLAN-Aware](https://docs.nvidia.com/networking-ethernet-software/ifupdown2/Bridge-VLAN-Aware/)
- [Cisco PVLAN Configuration Guide](https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst3750/software/release/15-0_2_se/configuration/guide/scg3750/swpvlan.html)
- [RFC 5765 - Security Implications of Network Address Translation](https://www.rfc-editor.org/rfc/rfc5765)

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — SDN Proxmox per multi-tenant overlay.** Il sottosistema SDN di Proxmox (in PVE 8.x) introduce **zone** (VLAN, QinQ, VXLAN, EVPN) che permettono multi-tenancy avanzato senza dipendere da NSX o OVS+OVN. Esempi di zone: `vlan` (isolated VLAN per tenant), `qinq` (double-tagged per overlap di range VLAN tra tenant), `vxlan` (overlay L2-over-UDP), `evpn` (BGP control plane EVPN per cluster multi-site). Ogni zone definisce **vnet** (network logiche) e **subnets** (con IPAM e DHCP integrati). Configurazione persistente in `/etc/pve/sdn/`. Per migrare un ambiente PVLAN VMware avanzato, valutare zone `vxlan` + `evpn` come pendant moderno. Riferimento: [`PVE-SDN`].

> **Errore comune — Native VLAN inconsistente fra Proxmox e switch.** Sintomo: alcune VM "vedono" frame untagged dell'altra VLAN nativa, o niente. Causa: `bridge-pvid` su Proxmox e `switchport trunk native vlan` su switch hanno valori diversi. Best practice: scegliere una VLAN nativa esplicita (mai 1, e la default insicura), es. 99, e *configurarla coerentemente* su tutti i nodi e tutti gli switch fisici. Verifica: `bridge vlan show` deve mostrare PVID 99 untagged.

> **Caso reale — VLAN hopping attack su switch misconfigured.** In un test di sicurezza pre-migrazione, una VM in VLAN 10 ha inviato frame double-tagged (outer 10, inner 20) verso lo switch fisico. Lo switch ha rimosso il tag esterno (10 = native) e propagato il frame con il tag interno (20) — VLAN hopping riuscito. Causa: `switchport trunk native vlan 10` faceva untagging di frame con VID = native. Soluzione preventiva, sia VMware che Proxmox: (a) non usare la native VLAN per VM, riservarla a management; (b) forzare tagging coerente con `vlan dot1q tag native` su Cisco; (c) evitare di accettare frame con tag double anche sul bridge Linux (`bridge link set dev eth0 vlan_filtering 1` e `--double-tag` non gestito di default).

---

## Esercizi

1. **Concettuale — VST/EST/VGT casi d'uso.** Per ognuno, scegliere il modo: (a) VM web standard nella VLAN 100; (b) VM pfSense firewall che gestisce 5 VLAN internamente; (c) VM legacy in un data center dove lo switch fisico tagga prima del server. *Risposte:* (a) VST `tag=100`; (b) VGT `tag=4095` per passare tutti i tag al guest; (c) EST = nessun tag su Proxmox, switch tagga.

2. **Lab — bridge VLAN-aware con whitelist.** Configurare `vmbr0` con `bridge-vids 10,20,30,40,99`. Creare 4 VM, una per VLAN, e una VM con `tag=50`. Verificare che la VM con `tag=50` non comunichi (frame droppato dal bridge). Output: `bridge vlan show`.

3. **Scenario — PVLAN VMware → Proxmox SDN.** Hai una configurazione PVLAN VMware con: Primary VLAN 100, Community VLAN 101 (membri: 5 VM), Isolated VLAN 102 (membri: 10 VM). Argomenta in 12 righe come tradurre questo in Proxmox SDN. *Risposta attesa:* (a) creare zone VLAN `pvlan-prim` con vnet sotto-rete 100; (b) per Community: una sub-zona logica con vnet `community-101`, regole firewall che permettono comunicazione fra membri e verso promiscuous; (c) per Isolated: vnet `isolated-102`, regole firewall che permettono *solo* verso promiscuous. Limitazione: Linux bridge non fa true L2 isolation come PVLAN VMware; alcune comunicazioni broadcast/multicast potrebbero "leak" e richiedono blocco extra in firewall.

4. **Stretch — switch trunk port config.** Per Cisco IOS, scrivere la config di una porta trunk verso un nodo Proxmox: native VLAN 99, allowed VLAN 10,20,30,40,99, BPDU guard + portfast trunk + storm-control broadcast 1%. Documentare ogni linea. *Risposta:*
   ```
   interface GigabitEthernet0/1
    description Proxmox-Node-pve1-trunk
    switchport mode trunk
    switchport trunk encapsulation dot1q
    switchport trunk native vlan 99
    switchport trunk allowed vlan 10,20,30,40,99
    spanning-tree portfast trunk
    spanning-tree bpduguard enable
    storm-control broadcast level pps 1000
   ```

## Auto-valutazione

1. Cosa significa VST, EST, VGT in VMware e quale e il pendant Proxmox?
2. Perche `tag=4095` e VGT e quando usarlo?
3. Differenza fra `bridge-vids` e `bridge-pvid`?
4. Come si configura una porta trunk Cisco IOS verso un host Proxmox?
5. Cos'e VLAN hopping e quale config sullo switch lo blocca?
6. Tre tipi di Private VLAN VMware: cosa fanno e come si comportano (Promiscuous/Community/Isolated)?
7. Perche PVLAN non ha equivalente diretto su Linux Bridge VLAN-aware?
8. SDN Proxmox: tipi di zone disponibili?

## Letture primarie consigliate

- [`PVE-SDN`] Proxmox VE Wiki — Software-Defined Network. https://pve.proxmox.com/wiki/Software-Defined_Network
- [`IEEE-802.1Q`] IEEE 802.1Q — VLAN. https://standards.ieee.org/ieee/802.1Q/6844/
- ifupdown2 — Bridge VLAN-Aware. https://docs.nvidia.com/networking-ethernet-software/ifupdown2/Bridge-VLAN-Aware/
- Cisco PVLAN Configuration Guide. https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst3750/software/release/15-0_2_se/configuration/guide/scg3750/swpvlan.html
- VLAN Hopping Attack overview (NIST SP 800-115 — Network Penetration Testing). https://csrc.nist.gov/pubs/sp/800/115/final
- VMware NSX-T Documentation. https://docs.vmware.com/en/VMware-NSX/index.html

## Collegamenti incrociati

- Modulo 04.1 — `../04-NETWORKING-AVANZATO-PROXMOX/linux-bridge-vlan-bonding.md`: bridge VLAN-aware basics.
- Modulo 07.1 — `ip-planning-dns-dhcp-firewall.md`: planning IP/DNS.
- Modulo 07.2 — `mapping-vswitch-linux-bridge.md`: mapping vSwitch ↔ Linux Bridge.
- Modulo 12.1 — `../12-SICUREZZA-E-COMPLIANCE/sicurezza-compliance.md`: sicurezza generale post-migrazione (firewall, audit).
- Modulo 17.3 — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-networking-post-migrazione.md`: troubleshooting VLAN-related issues.

## Glossario locale

| Termine | Definizione |
|---|---|
| **VST (Virtual Switch Tagging)** | vSwitch tagga frame con il VID del port group; VM riceve untagged. |
| **EST (External Switch Tagging)** | Switch fisico tagga; vSwitch non tagga; VM riceve untagged. |
| **VGT (Virtual Guest Tagging)** | Trunk completo al guest; VID 4095 = "passa tutto". VM riceve frame con tag 802.1Q. |
| **Bridge VLAN-aware (Proxmox)** | Linux Bridge che gestisce frame tagged 802.1Q senza richiedere bridge separati per ogni VLAN. |
| **`bridge-vids`** | Whitelist VLAN ID accettate dal bridge. |
| **`bridge-pvid`** | Default VLAN per frame untagged ricevuti sul bridge. |
| **PVLAN** | Private VLAN — isolamento L2 avanzato dentro una primary VLAN. Modi: Promiscuous/Community/Isolated. |
| **Native VLAN** | VLAN per frame untagged su un trunk port (tipicamente VLAN 1 di default; raccomandato cambiare). |
| **VLAN hopping** | Attacco L2 che permette di superare l'isolamento VLAN tramite frame double-tagged o switch impersonation. |
| **`switchport mode trunk`** | Cisco: configura la porta come trunk 802.1Q. |
| **`switchport trunk allowed vlan`** | Cisco: lista VLAN ammesse sul trunk. |
| **`switchport trunk native vlan`** | Cisco: VLAN nativa per frame untagged. |
| **BPDU guard** | Funzione switch che disabilita una porta se riceve BPDU (per impedire loop accidentali su porte access/trunk). |
| **Storm control** | Limite di broadcast/multicast/unicast traffic per porta switch (anti-DoS L2). |
| **SDN zone (Proxmox)** | Astrazione SDN: VLAN/QinQ/VXLAN/EVPN. |
| **vnet (Proxmox SDN)** | Network logica dentro una zone. |
| **EVPN** | Ethernet VPN — BGP control plane per overlay L2 sopra L3 (RFC 7432). |
| **VXLAN** | Virtual eXtensible LAN — overlay L2-over-UDP (RFC 7348). |
