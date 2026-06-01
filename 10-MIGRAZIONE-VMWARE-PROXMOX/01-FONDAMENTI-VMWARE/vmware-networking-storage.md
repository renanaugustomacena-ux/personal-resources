# VMware vSphere Networking e Storage

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 1 — Fondamenti · Modulo 01.2 (segue 01.1, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 01.1 (architettura vSphere/ESXi); conoscenza di Layer 2/3, VLAN 802.1Q, MTU, iSCSI/NFS basics.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. distinguere Standard vSwitch (per-host) e Distributed vSwitch (cluster-wide), identificando le funzionalita esclusive del dvSwitch (NIOC, port mirroring, NetFlow/IPFIX, LACP, PVLAN);
> 2. configurare e leggere lo stato di vSwitch, port group, VMkernel port, uplink e NIC teaming via `esxcli` e PowerCLI, e documentare tutte le combinazioni VLAN tagging mode (VST / EST / VGT);
> 3. spiegare i concetti di VMFS (versioni, locking SCSI-2/SCSI-3, ATS), multipath (NMP/PSP, RR/MRU/Fixed) e descrivere come gli RDM differiscono da un VMDK su VMFS;
> 4. enumerare i protocolli di accesso allo storage (FC, FCoE, iSCSI software/hardware, NFS v3/v4.1, NVMe-oF) con i loro vincoli operativi (autenticazione CHAP, jumbo frames, dipendenza dalla rete);
> 5. ricostruire l'architettura vSAN (disk groups, cache vs capacity tier, witness, fault domains) e mappare ogni concetto al piu vicino equivalente Proxmox (Ceph hyperconverged, ZFS replicato);
> 6. produrre la mappatura concreta di rete e storage VMware → Proxmox in vista del piano di migrazione.
> **Tempo stimato:** lettura 90-120 min · lab 120-180 min
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** vSphere 7.0 / 8.0 (con dvSwitch v8.0.0), VMFS-6, NFS 4.1, iSCSI software adapter, vSAN 7/8 OSA + ESA.

## Mappa concettuale

```
+======================================================+
|     vSphere Networking & Storage — visione macro     |
+======================================================+
|                                                      |
|   NETWORKING                          STORAGE        |
|   +-------------------+               +------------+ |
|   | Standard vSwitch  |               | Datastore  | |
|   |  per-host         |               | (VMFS/NFS/ | |
|   +-------------------+               |  vSAN/vVol)| |
|            |                          +-----+------+ |
|            v                                |        |
|   +-------------------+               +-----v------+ |
|   | Distributed vSw.  |               | Multipath  | |
|   |  cluster-wide     |               |  (NMP)     | |
|   |  + NIOC + LACP    |               |  RR/MRU/   | |
|   |  + PortMirror     |               |  Fixed     | |
|   +-------------------+               +-----+------+ |
|            |                                |        |
|            v                                v        |
|   +-------------------+               +------------+ |
|   | NSX (Software-    |               | FC/FCoE/   | |
|   |  Defined Network) |               | iSCSI/NFS/ | |
|   |  VXLAN, micro-seg |               | NVMe-oF    | |
|   +-------------------+               +------------+ |
|            |                                         |
|            +------ HCI -----+                        |
|                             v                        |
|                       +------------+                 |
|                       |   vSAN     |  <-- target di  |
|                       | OSA / ESA  |     migrazione: |
|                       | disk groups|     Ceph        |
|                       | witness    |                 |
|                       +------------+                 |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **vSS = locale, dvSwitch = di cluster.** Tutto cio che e gestito dal vCenter (NIOC, port mirroring, LACP, NetFlow) vive solo sul dvSwitch. La perdita del vCenter non distrugge le VM ma blocca i cambi di configurazione di rete.
2. **VLAN tagging: VST e la norma.** EST esiste per integrarsi con switch fisici legacy; VGT (VLAN ID 4095) si usa solo quando la VM stessa fa il tagging (firewall, router virtuali). Sapere riconoscere quale modalita e in uso evita errori di mapping in migrazione.
3. **VMFS non e un filesystem di rete.** E un cluster filesystem distribuito che usa SCSI reservations / ATS sopra una LUN condivisa. Su Proxmox l'analogo (LVM su LUN condivisa) **non supporta snapshot** se non con LVM-Thin (e LVM-Thin non e cluster-shared); l'equivalenza non e perfetta — vedi modulo 03.1 e 08.2.
4. **Multipath e separato dal protocollo.** NMP (Native Multipath Plugin) astrae FC/iSCSI/FCoE; le PSP (RR, MRU, Fixed) decidono come distribuire l'I/O su piu path. Su Linux/Proxmox l'equivalente e `multipath-tools` con policy analoghe — cambia il file di configurazione (`multipath.conf`), non il principio.
5. **vSAN ≈ Ceph hyperconverged.** Disk group (cache + capacity) ≈ OSD device classes; witness ≈ MON di tie-break; fault domain ≈ failure domain CRUSH map. Conoscere la mappatura semplifica il dimensionamento Ceph nel modulo 03.1.

## Indice

1. [vSphere Networking](#vsphere-networking)
2. [vSphere Storage](#vsphere-storage)
3. [vSAN](#vsan)
4. [Confronto con Proxmox](#confronto-con-proxmox)

---

## vSphere Networking

### Architettura di Rete vSphere

Il networking in vSphere e basato su switch virtuali che operano a Layer 2. Esistono due tipi principali: Standard vSwitch (locale al singolo host) e Distributed vSwitch (gestito centralmente da vCenter e condiviso tra host).

```
+=====================================================================+
|                 vSphere Networking Overview                          |
+=====================================================================+
|                                                                      |
|   Physical Network                                                   |
|   +--------------------+  +--------------------+                     |
|   | Physical Switch    |  | Physical Switch    |                     |
|   | (ToR / Aggregation)|  | (ToR / Aggregation)|                     |
|   +-----+---------+----+  +----+---------+-----+                     |
|         |         |             |         |                           |
|   +-----v---------v-------------v---------v------+                   |
|   |    vmnic0   vmnic1       vmnic2   vmnic3     |                   |
|   |    (pNIC)   (pNIC)       (pNIC)   (pNIC)     |  <-- Uplinks      |
|   +-----+----------+------------+--------+-------+                   |
|         |          |            |        |                            |
|   +-----v----------v-----+ +---v--------v--------+                   |
|   |  Standard vSwitch 0  | | Standard vSwitch 1  |                   |
|   |                       | |                     |                   |
|   | +------------------+  | | +------------------+|                   |
|   | | PG: Management   |  | | | PG: vMotion      ||                   |
|   | | VLAN: 10         |  | | | VLAN: 20         ||                   |
|   | | VMkernel: vmk0   |  | | | VMkernel: vmk1   ||                   |
|   | +------------------+  | | +------------------+|                   |
|   | +------------------+  | | +------------------+|                   |
|   | | PG: VM Network   |  | | | PG: iSCSI        ||                   |
|   | | VLAN: 100        |  | | | VLAN: 30         ||                   |
|   | | VM ports         |  | | | VMkernel: vmk2   ||                   |
|   | +------------------+  | | +------------------+|                   |
|   +------------------------+ +---------------------+                  |
|                                                                      |
+=====================================================================+
```

### Standard vSwitch (vSS)

Lo Standard vSwitch e locale al singolo host ESXi. Ogni host gestisce il proprio vSwitch indipendentemente. La configurazione non e sincronizzata tra host, creando rischio di inconsistenze.

**Componenti dello Standard vSwitch**:

| Componente | Descrizione |
|---|---|
| vSwitch | Switch virtuale Layer 2 con porte |
| Port Group | Raggruppamento logico di porte con policy comuni |
| VMkernel Port | Porta per il traffico del VMkernel (mgmt, vMotion, iSCSI, NFS, vSAN) |
| Uplink | Collegamento a NIC fisica (vmnicN) |
| Security Policy | Promiscuous mode, MAC address changes, Forged transmits |
| Traffic Shaping | Average bandwidth, peak bandwidth, burst size |
| NIC Teaming | Policy di load balancing e failover per gli uplink |

```bash
# === GESTIONE VSWITCH STANDARD VIA ESXCLI ===

# Creare un nuovo vSwitch
esxcli network vswitch standard add --vswitch-name=vSwitch1

# Configurare MTU (jumbo frames)
esxcli network vswitch standard set --mtu=9000 --vswitch-name=vSwitch1

# Aggiungere un uplink
esxcli network vswitch standard uplink add \
    --uplink-name=vmnic2 --vswitch-name=vSwitch1

# Creare un port group
esxcli network vswitch standard portgroup add \
    --portgroup-name="VM-Production" --vswitch-name=vSwitch1

# Configurare VLAN su un port group
esxcli network vswitch standard portgroup set \
    --portgroup-name="VM-Production" --vlan-id=100

# Creare un VMkernel port (management)
esxcli network ip interface add \
    --interface-name=vmk0 --portgroup-name="Management Network"

# Configurare IP su VMkernel port
esxcli network ip interface ipv4 set \
    --interface-name=vmk0 --ipv4=10.0.1.100 --netmask=255.255.255.0 \
    --type=static

# Abilitare servizi su VMkernel port
esxcli network ip interface tag add --interface-name=vmk1 --tagname=VMotion

# Lista vSwitch con dettagli
esxcli network vswitch standard list

# Lista port group
esxcli network vswitch standard portgroup list

# Policy di sicurezza del port group
esxcli network vswitch standard portgroup policy security set \
    --portgroup-name="VM-Production" \
    --allow-promiscuous=false \
    --allow-mac-change=false \
    --allow-forged-transmits=false
```

### NIC Teaming Policies

Le policy di NIC teaming determinano come il traffico viene distribuito tra gli uplink e come avviene il failover:

```
+-------------------------------------------------------------------+
|                    NIC Teaming Policies                            |
+-------------------------------------------------------------------+
|                                                                    |
|  1. ROUTE BASED ON ORIGINATING PORT ID (default)                  |
|  +------+------+------+------+                                     |
|  | VM1  | VM2  | VM3  | VM4  |                                     |
|  +--+---+--+---+--+---+--+---+                                     |
|     |      |      |      |                                         |
|     |      +------+------+---> vmnic0                              |
|     +------------------------> vmnic1                              |
|                                                                    |
|  Algoritmo: Ogni porta del vSwitch e associata a un uplink.       |
|  Pro: Semplice, nessuna configurazione switch fisico.             |
|  Contro: Una VM usa un solo uplink alla volta.                    |
|                                                                    |
|  ---                                                               |
|                                                                    |
|  2. ROUTE BASED ON IP HASH                                        |
|  +------+------+------+------+                                     |
|  | VM1  | VM2  | VM3  | VM4  |                                     |
|  +--+---+--+---+--+---+--+---+                                     |
|     |      |      |      |                                         |
|     +--+---+--+---+--+---+------> Hash(src_ip, dst_ip)            |
|        |      |      |                                             |
|        v      v      v                                             |
|     vmnic0  vmnic1  vmnic0                                         |
|                                                                    |
|  Algoritmo: Hash di IP sorgente e destinazione.                   |
|  Pro: Distribuzione migliore. Una VM puo usare piu uplink.        |
|  Contro: RICHIEDE 802.3ad / LACP sullo switch fisico.             |
|                                                                    |
|  ---                                                               |
|                                                                    |
|  3. ROUTE BASED ON SOURCE MAC HASH                                |
|  +------+------+------+------+                                     |
|  | VM1  | VM2  | VM3  | VM4  |                                     |
|  | MAC-A| MAC-B| MAC-C| MAC-D|                                     |
|  +--+---+--+---+--+---+--+---+                                     |
|     |      |      |      |                                         |
|     +--+---+      +--+---+-----> Hash(src_mac)                    |
|        |             |                                             |
|        v             v                                             |
|     vmnic0        vmnic1                                           |
|                                                                    |
|  Algoritmo: Hash del MAC sorgente.                                |
|  Pro: Nessuna configurazione switch fisico.                       |
|  Contro: Una VM usa un solo uplink (come originating port).       |
|                                                                    |
|  ---                                                               |
|                                                                    |
|  4. EXPLICIT FAILOVER ORDER                                       |
|  +------+------+------+------+                                     |
|  | VM1  | VM2  | VM3  | VM4  |                                     |
|  +--+---+--+---+--+---+--+---+                                     |
|     |      |      |      |                                         |
|     +------+------+------+-----> vmnic0 (ACTIVE)                  |
|                                  vmnic1 (STANDBY)                  |
|                                                                    |
|  Algoritmo: Tutto il traffico su un uplink. Failover manuale.    |
|  Pro: Controllo totale, separazione traffico.                     |
|  Contro: Nessun load balancing.                                   |
|                                                                    |
+-------------------------------------------------------------------+
```

### Distributed vSwitch (dvSwitch)

Il dvSwitch e gestito centralmente da vCenter e si estende su piu host. Fornisce funzionalita avanzate non disponibili con lo Standard vSwitch:

```
+=====================================================================+
|                  Distributed vSwitch Architecture                    |
+=====================================================================+
|                                                                      |
|  vCenter Server                                                      |
|  +----------------------------------------------------------------+ |
|  |  dvSwitch: "dvs-production" (Control Plane)                    | |
|  |                                                                  | |
|  |  +--------------------+  +--------------------+                 | |
|  |  | dvPortGroup:       |  | dvPortGroup:       |                 | |
|  |  | "dvPG-Web"         |  | "dvPG-Database"    |                 | |
|  |  | VLAN: 100          |  | VLAN: 200          |                 | |
|  |  | Policy: teaming,   |  | Policy: teaming,   |                 | |
|  |  |   security, NIOC   |  |   security, NIOC   |                 | |
|  |  +--------------------+  +--------------------+                 | |
|  |                                                                  | |
|  |  Uplink Port Group: "dvUplinks"                                 | |
|  |  +----------------------------------------------------+        | |
|  |  | Uplink1 | Uplink2 | Uplink3 | Uplink4              |        | |
|  |  +----------------------------------------------------+        | |
|  +----------------------------------------------------------------+ |
|                    |                     |                            |
|         +----------v---------+ +---------v----------+                |
|         |   Host Proxy Switch | | Host Proxy Switch  |               |
|         |   (ESXi Host A)     | | (ESXi Host B)      |               |
|         |                     | |                     |               |
|         | vmnic0 -> Uplink1   | | vmnic0 -> Uplink1   |              |
|         | vmnic1 -> Uplink2   | | vmnic1 -> Uplink2   |              |
|         |                     | |                     |               |
|         | +------+ +------+   | | +------+ +------+   |              |
|         | | VM1  | | VM2  |   | | | VM3  | | VM4  |   |              |
|         | +------+ +------+   | | +------+ +------+   |              |
|         +---------------------+ +---------------------+              |
|                                                                      |
+=====================================================================+
```

**Funzionalita esclusive del dvSwitch**:

| Funzionalita | Descrizione |
|---|---|
| Network I/O Control (NIOC) | QoS per tipo di traffico |
| Port Mirroring | SPAN/RSPAN per analisi traffico |
| NetFlow/IPFIX | Esportazione flussi per analisi |
| LACP | Link Aggregation Control Protocol |
| Private VLAN | Isolamento Layer 2 avanzato |
| Port Binding | Static, dynamic, ephemeral |
| Health Check | Verifica configurazione rete |
| Network Resource Pool | Pool risorse rete per tenant |
| Traffic Filtering | ACL su porta dvSwitch |

```powershell
# === POWERCLI: GESTIONE DVSWITCH ===

# Creare un dvSwitch
New-VDSwitch -Name "dvs-production" -Location (Get-Datacenter "DC-Milano") `
    -Mtu 9000 -NumUplinkPorts 4 -Version "8.0.0"

# Aggiungere host al dvSwitch
$dvs = Get-VDSwitch "dvs-production"
$vmhost = Get-VMHost "esxi-prod-01.lab.local"
Add-VDSwitchVMHost -VDSwitch $dvs -VMHost $vmhost

# Assegnare uplink fisici
$vmhostNetAdapter = Get-VMHostNetworkAdapter -VMHost $vmhost -Physical -Name "vmnic2"
Add-VDSwitchPhysicalNetworkAdapter -DistributedSwitch $dvs `
    -VMHostPhysicalNic $vmhostNetAdapter -Confirm:$false

# Creare dvPortGroup
New-VDPortgroup -Name "dvPG-Web" -VDSwitch $dvs `
    -VlanId 100 -NumPorts 128 -PortBinding "Static"

# Creare dvPortGroup con VLAN trunk
New-VDPortgroup -Name "dvPG-Trunk" -VDSwitch $dvs `
    -VlanTrunkRange "100-200" -NumPorts 64

# Configurare NIC teaming su dvPortGroup
$dvpg = Get-VDPortgroup "dvPG-Web"
$dvpg | Get-VDUplinkTeamingPolicy |
    Set-VDUplinkTeamingPolicy -LoadBalancingPolicy "LoadBalanceIP" `
    -EnableFailback $true -NotifySwitches $true

# Esportare configurazione dvSwitch (backup)
Export-VDSwitch -VDSwitch $dvs -Destination "C:\dvs-backup" -Force

# Importare configurazione dvSwitch (restore)
# Import-VDSwitch -BackupPath "C:\dvs-backup\dvs-production.zip" `
#     -Location (Get-Datacenter "DC-Milano")

# Inventario dvSwitch completo
Get-VDSwitch | ForEach-Object {
    $dvs = $_
    Write-Host "dvSwitch: $($dvs.Name)" -ForegroundColor Cyan
    Write-Host "  Version: $($dvs.Version)"
    Write-Host "  MTU: $($dvs.Mtu)"
    Write-Host "  NIOC: $($dvs.ExtensionData.Config.NetworkResourceManagementEnabled)"
    Write-Host "  Uplinks: $($dvs.NumUplinkPorts)"
    Write-Host "  Hosts:"
    $dvs | Get-VMHost | ForEach-Object {
        Write-Host "    - $($_.Name)"
    }
    Write-Host "  Port Groups:"
    $dvs | Get-VDPortgroup | ForEach-Object {
        Write-Host "    - $($_.Name) [VLAN: $($_.VlanConfiguration)]"
    }
}
```

### VLAN Tagging Modes

VMware supporta tre modalita di VLAN tagging:

```
+-------------------------------------------------------------------+
|                    VLAN Tagging Modes                              |
+-------------------------------------------------------------------+
|                                                                    |
|  1. VST - Virtual Switch Tagging (piu comune)                    |
|  +----------------------------------------------------------+    |
|  |  vSwitch / dvSwitch                                       |    |
|  |  +------------------+                                      |   |
|  |  | Port Group       |                                      |   |
|  |  | VLAN ID: 100     |  <-- Tag applicato dal vSwitch      |   |
|  |  | VM invia frame   |                                      |   |
|  |  | SENZA tag        |                                      |   |
|  |  +------------------+                                      |   |
|  |         |                                                  |   |
|  |         v                                                  |   |
|  |  Frame: [dst][src][802.1Q VLAN=100][payload]               |   |
|  |         |                                                  |   |
|  |  +------v-------+                                          |   |
|  |  |   vmnic0     | ----> Switch fisico (trunk port)         |   |
|  |  +--------------+                                          |   |
|  +----------------------------------------------------------+    |
|                                                                    |
|  2. EST - External Switch Tagging                                 |
|  +----------------------------------------------------------+    |
|  |  vSwitch / dvSwitch                                       |    |
|  |  +------------------+                                      |   |
|  |  | Port Group       |                                      |   |
|  |  | VLAN ID: 0 (none)|  <-- Nessun tagging dal vSwitch     |   |
|  |  | VM invia frame   |                                      |   |
|  |  | SENZA tag        |                                      |   |
|  |  +------------------+                                      |   |
|  |         |                                                  |   |
|  |         v                                                  |   |
|  |  Frame: [dst][src][payload]  (no 802.1Q)                   |   |
|  |         |                                                  |   |
|  |  +------v-------+                                          |   |
|  |  |   vmnic0     | ----> Switch fisico (ACCESS port)        |   |
|  |  +--------------+       applica VLAN esternamente          |   |
|  +----------------------------------------------------------+    |
|                                                                    |
|  3. VGT - Virtual Guest Tagging                                  |
|  +----------------------------------------------------------+    |
|  |  vSwitch / dvSwitch                                       |    |
|  |  +------------------+                                      |   |
|  |  | Port Group       |                                      |   |
|  |  | VLAN ID: 4095    |  <-- VLAN trunk mode                |   |
|  |  | VM invia frame   |                                      |   |
|  |  | CON tag 802.1Q   |  <-- Guest gestisce le VLAN         |   |
|  |  +------------------+                                      |   |
|  |         |                                                  |   |
|  |         v                                                  |   |
|  |  Frame: [dst][src][802.1Q VLAN=N][payload]                 |   |
|  |         (tag inserito dalla VM guest)                      |   |
|  |         |                                                  |   |
|  |  +------v-------+                                          |   |
|  |  |   vmnic0     | ----> Switch fisico (trunk port)         |   |
|  |  +--------------+                                          |   |
|  +----------------------------------------------------------+    |
|                                                                    |
+-------------------------------------------------------------------+
```

### Traffic Shaping

Il traffic shaping controlla la larghezza di banda per port group:

```bash
# Standard vSwitch: solo traffic shaping in uscita (outbound)
esxcli network vswitch standard portgroup policy shaping set \
    --portgroup-name="VM-Production" \
    --enabled=true \
    --avg-bandwidth=100000       # 100 Mbps average
    --peak-bandwidth=200000      # 200 Mbps peak
    --burst-size=819200          # 800 KB burst

# dvSwitch: traffic shaping bidirezionale (ingress + egress)
```

```powershell
# PowerCLI: Traffic shaping su dvPortGroup (bidirezionale)
$dvpg = Get-VDPortgroup "dvPG-Web"

# Egress (outbound dal guest)
$dvpg | Get-VDTrafficShapingPolicy -Direction Out |
    Set-VDTrafficShapingPolicy -Enabled:$true `
    -AverageBandwidth 100000 -PeakBandwidth 200000 -BurstSize 819200

# Ingress (inbound verso il guest)
$dvpg | Get-VDTrafficShapingPolicy -Direction In |
    Set-VDTrafficShapingPolicy -Enabled:$true `
    -AverageBandwidth 100000 -PeakBandwidth 200000 -BurstSize 819200
```

### Network I/O Control (NIOC)

NIOC e disponibile solo su dvSwitch e fornisce QoS basata su classi di traffico:

```
+-------------------------------------------------------------------+
|                    Network I/O Control v3                          |
+-------------------------------------------------------------------+
|                                                                    |
|  10 GbE Physical NIC (vmnic0)                                     |
|  +--------------------------------------------------------------+ |
|  |                                                               | |
|  |  System Traffic Types (shares / reservation / limit):         | |
|  |                                                               | |
|  |  +--------------+  Shares: 50  | Reservation: 1 Gbps         | |
|  |  | Management   |  Limit: none |                              | |
|  |  +--------------+              |                              | |
|  |                                |                              | |
|  |  +--------------+  Shares: 100 | Reservation: 2 Gbps         | |
|  |  | vMotion      |  Limit: 5 Gbps                             | |
|  |  +--------------+              |                              | |
|  |                                |                              | |
|  |  +--------------+  Shares: 50  | Reservation: 1 Gbps         | |
|  |  | iSCSI / NFS  |  Limit: none |                              | |
|  |  +--------------+              |                              | |
|  |                                |                              | |
|  |  +--------------+  Shares: 50  | Reservation: 500 Mbps       | |
|  |  | vSAN         |  Limit: none |                              | |
|  |  +--------------+              |                              | |
|  |                                |                              | |
|  |  +--------------+  Shares: 100 | Reservation: 2 Gbps         | |
|  |  | VM Traffic   |  Limit: none |                              | |
|  |  +--------------+              |                              | |
|  |                                                               | |
|  +--------------------------------------------------------------+ |
|                                                                    |
|  Quando la banda e sufficiente: tutti i tipi ricevono cio        |
|  di cui hanno bisogno.                                            |
|  Quando c'e contention: le share determinano la priorita         |
|  relativa, le reservation garantiscono il minimo.                |
|                                                                    |
+-------------------------------------------------------------------+
```

### Jumbo Frames

I jumbo frame (MTU 9000) migliorano il throughput per traffico storage e vMotion riducendo l'overhead dei pacchetti:

```
Standard Frame vs Jumbo Frame:

Standard (MTU 1500):
+------+------+---------+----------+-----+
| Pre  | Dst  |   Src   | 802.1Q   | FCS |
| 8B   | 6B   |   6B    | 4B       | 4B  |  Overhead: ~28 byte
+------+------+---------+----------+-----+
|            Payload: 1500 byte           |  Efficienza: 98.2%
+-----------------------------------------+

Jumbo (MTU 9000):
+------+------+---------+----------+-----+
| Pre  | Dst  |   Src   | 802.1Q   | FCS |
| 8B   | 6B   |   6B    | 4B       | 4B  |  Overhead: ~28 byte
+------+------+---------+----------+-----+
|            Payload: 9000 byte           |  Efficienza: 99.7%
+-----------------------------------------+

Throughput improvement: ~3-5% per traffico bulk (iSCSI, NFS, vMotion)
```

Configurazione end-to-end richiesta (OGNI elemento della catena deve supportare MTU 9000):

```bash
# 1. Switch fisico: configurare MTU 9000 su tutte le porte trunk

# 2. vSwitch
esxcli network vswitch standard set --mtu=9000 --vswitch-name=vSwitch1

# 3. VMkernel port
esxcli network ip interface set --mtu=9000 --interface-name=vmk1

# 4. Verifica con ping
vmkping -s 8972 -d 10.0.20.100
# (8972 + 28 byte header = 9000 MTU)
# Se fallisce: qualche elemento nella catena non supporta jumbo
```

---

## vSphere Storage

### VMFS (Virtual Machine File System)

VMFS e il filesystem cluster proprietario VMware, progettato per supportare accesso concorrente da piu host ESXi allo stesso datastore su storage condiviso.

```
+=====================================================================+
|                    VMFS Architecture                                 |
+=====================================================================+
|                                                                      |
|  ESXi Host A            ESXi Host B            ESXi Host C          |
|  +-----------+          +-----------+          +-----------+         |
|  | VMFS      |          | VMFS      |          | VMFS      |         |
|  | Driver    |          | Driver    |          | Driver    |         |
|  +-----+-----+         +-----+-----+          +-----+-----+        |
|        |                      |                      |               |
|        +----------------------+----------------------+               |
|                               |                                      |
|        +----------------------v----------------------+               |
|        |        Shared Storage (SAN / iSCSI)         |               |
|        |                                              |               |
|        |  +------------------------------------------+|               |
|        |  |  VMFS Datastore: "DS-Production-01"      ||               |
|        |  |                                          ||               |
|        |  |  Metadata:                               ||               |
|        |  |  - Superblock                            ||               |
|        |  |  - Resource bitmap                       ||               |
|        |  |  - File descriptor table                 ||               |
|        |  |                                          ||               |
|        |  |  On-Disk Locking:                        ||               |
|        |  |  - ATS (Atomic Test & Set) - hardware    ||               |
|        |  |  - SCSI reservations - fallback          ||               |
|        |  |                                          ||               |
|        |  |  Directories:                            ||               |
|        |  |  /web-server-01/                         ||               |
|        |  |    web-server-01.vmx                     ||               |
|        |  |    web-server-01-flat.vmdk                ||               |
|        |  |  /db-server-01/                          ||               |
|        |  |    db-server-01.vmx                      ||               |
|        |  |    db-server-01-flat.vmdk                ||               |
|        |  +------------------------------------------+|               |
|        +----------------------------------------------+              |
|                                                                      |
+=====================================================================+
```

### Versioni VMFS

| Caratteristica | VMFS 5 | VMFS 6 |
|---|---|---|
| Introdotto con | vSphere 5.0 | vSphere 6.5 |
| Max datastore size | 64 TB | 64 TB |
| Max file size | 62 TB | 62 TB |
| Block size | 1 MB (fisso) | 1 MB (fisso) |
| Sub-block size | 8 KB | 64 KB |
| Automatic UNMAP | No (manuale) | Si (background) |
| Max extents | 32 | 32 |
| Max host per datastore | 64 | 64 |
| SE Sparse (snapshot) | Si | Si |
| ATS-Only locking | Opzionale | Default |
| 512e drive support | Limitato | Completo |
| 4Kn drive support | No | No (ESXi 7.0+: sperimentale) |

```bash
# Verificare versione VMFS
esxcli storage filesystem list
# Mount Point          Volume Name    UUID                                 Mounted  Type   Size
# /vmfs/volumes/xxxx   DS-Prod-01     60a13b2c-7f8e9d01-abcd-123456789abc true     VMFS-6 2.0T

# Creare un datastore VMFS 6
esxcli storage vmfs extent add \
    --device-name=naa.600508b4000c4a78000100000043 \
    --volume-label="DS-New-01"

# Verificare locking mode
vmkfstools -Ph /vmfs/volumes/DS-Prod-01/
# VMFS-6.82 (ATS-only) file system
# ...

# UNMAP automatico (VMFS 6): recupero spazio su thin-provisioned LUN
esxcli storage vmfs reclaim config get --volume-label="DS-Prod-01"
# Reclaim Granularity: 1048576 Bytes
# Reclaim Priority: low
```

### NFS Datastores

ESXi supporta NFS per l'accesso a storage condiviso via rete IP:

| Caratteristica | NFS v3 | NFS v4.1 |
|---|---|---|
| Supporto ESXi | 5.x+ | 6.0+ |
| Autenticazione | AUTH_SYS (IP-based) | Kerberos (krb5, krb5i, krb5p) |
| Multipathing | N/A (usa NIC teaming) | Session trunking (nativo) |
| Locking | Nessuno (ESXi gestisce internamente) | Mandatory locking (NFS standard) |
| Protocollo | TCP | TCP |
| IPv6 | Si | Si |
| Max datastore size | Limitato dal NFS server | Limitato dal NFS server |
| Delegations | No | Si |

```bash
# Montare un datastore NFS v3
esxcli storage nfs add \
    --host=10.0.30.100 \
    --share=/exports/vmware-ds01 \
    --volume-name="NFS-DS-01"

# Montare un datastore NFS v4.1
esxcli storage nfs41 add \
    --hosts=10.0.30.100 \
    --share=/exports/vmware-ds02 \
    --volume-name="NFS41-DS-02"

# Lista datastore NFS
esxcli storage nfs list
esxcli storage nfs41 list

# Statistiche NFS
esxcli storage nfs stats get
```

```powershell
# PowerCLI: Montare NFS su tutti gli host del cluster
$cluster = Get-Cluster "CL-Production"
$cluster | Get-VMHost | ForEach-Object {
    New-Datastore -Nfs -VMHost $_ -Name "NFS-Shared-01" `
        -Path "/exports/vmware" -NfsHost "10.0.30.100"
}
```

### iSCSI Storage

ESXi supporta iSCSI con software initiator (integrato nel VMkernel) o hardware initiator (HBA dedicata):

```
+-------------------------------------------------------------------+
|                    iSCSI Architecture in ESXi                     |
+-------------------------------------------------------------------+
|                                                                    |
|  ESXi Host                                                         |
|  +--------------------------------------------------------------+ |
|  |                                                               | |
|  |  VMFS Datastore                                               | |
|  |       |                                                       | |
|  |  PSA (Pluggable Storage Architecture)                         | |
|  |       |                                                       | |
|  |  +----v-------------+  +--------------------+                 | |
|  |  | Software iSCSI   |  | Hardware iSCSI     |                 | |
|  |  | Initiator        |  | HBA (if present)   |                 | |
|  |  | (vmhba64)        |  | (vmhba1)           |                 | |
|  |  +----+-------------+  +----+---------------+                 | |
|  |       |                      |                                 | |
|  |  +----v----+            +----v----+                            | |
|  |  | VMkernel|            | HBA     |                            | |
|  |  | vmk2    |            | Port    |                            | |
|  |  | (iSCSI) |            |         |                            | |
|  |  +---------+            +---------+                            | |
|  +------+----------------------------+--------------------------+ |
|         |                            |                             |
|    +----v----+                  +----v----+                        |
|    | vmnic2  |                  | HBA NIC |                        |
|    +---------+                  +---------+                        |
|         |                            |                             |
|    +----v----------------------------v----+                        |
|    |         IP Network                   |                        |
|    |    (VLAN dedicata, MTU 9000)         |                        |
|    +------------------+-------------------+                        |
|                       |                                            |
|    +------------------v-------------------+                        |
|    |         iSCSI Target                 |                        |
|    |     (Storage Array / NAS)            |                        |
|    |                                      |                        |
|    |  Target IQN:                         |                        |
|    |  iqn.2024-01.com.storage:target-01   |                        |
|    |                                      |                        |
|    |  LUN 0: 500 GB                       |                        |
|    |  LUN 1: 1 TB                         |                        |
|    |  LUN 2: 2 TB                         |                        |
|    +--------------------------------------+                        |
+-------------------------------------------------------------------+
```

```bash
# === CONFIGURAZIONE iSCSI SOFTWARE INITIATOR ===

# Abilitare iSCSI software adapter
esxcli iscsi software set --enabled=true

# Verificare adapter
esxcli iscsi adapter list
# Adapter  Driver  State   UID              Description
# vmhba64  iscsi_vmk online iscsi.vmhba64    iSCSI Software Adapter

# Configurare IQN dell'initiator
esxcli iscsi adapter set --adapter=vmhba64 \
    --name=iqn.1998-01.com.vmware:esxi-prod-01

# Aggiungere target
esxcli iscsi adapter discovery sendtarget add \
    --adapter=vmhba64 --address=10.0.30.200

# Configurare CHAP
esxcli iscsi adapter auth chap set \
    --adapter=vmhba64 --direction=uni \
    --authname=esxi-initiator --secret=S3cur3P@ss! --level=required

# Port binding (legare adapter iSCSI a VMkernel port specifico)
esxcli iscsi networkportal add \
    --adapter=vmhba64 --nic=vmk2

# Riscan dopo configurazione
esxcli storage core adapter rescan --adapter=vmhba64

# Verificare sessioni attive
esxcli iscsi session list

# Verificare LUN scoperte
esxcli storage core device list
```

### Multipathing

La PSA (Pluggable Storage Architecture) gestisce il multipath per dispositivi block storage:

```
+-------------------------------------------------------------------+
|                    Multipathing Policies                           |
+-------------------------------------------------------------------+
|                                                                    |
|  1. FIXED (VMW_PSP_FIXED)                                        |
|  Usa un path preferito. Failover su path alternativo.             |
|  Failback automatico al path preferito.                           |
|                                                                    |
|  ESXi ---(Path A - PREFERRED / Active)---> Storage                |
|       ---(Path B - Standby)--------------->                        |
|                                                                    |
|  2. MRU - Most Recently Used (VMW_PSP_MRU)                       |
|  Usa l'ultimo path funzionante. NO failback automatico.           |
|  Default per storage ALUA (Active/Standby).                       |
|                                                                    |
|  ESXi ---(Path A - Active)---------------> Storage                |
|       ---(Path B - standby, usato se A fail)-->                   |
|                                                                    |
|  3. ROUND ROBIN (VMW_PSP_RR)                                     |
|  Distribuisce I/O tra tutti i path attivi.                        |
|  Migliore per performance.                                        |
|                                                                    |
|  ESXi ---(Path A - Active)--+             Storage                 |
|       ---(Path B - Active)--+--> Round     |                      |
|       ---(Path C - Active)--+    Robin --> Target                 |
|       ---(Path D - Active)--+                                     |
|                                                                    |
+-------------------------------------------------------------------+
```

```bash
# Verificare policy multipath per un dispositivo
esxcli storage nmp device list --device=naa.600508b4000c4a78

# Cambiare policy
esxcli storage nmp device set \
    --device=naa.600508b4000c4a78 \
    --psp=VMW_PSP_RR

# Configurare round-robin con IOPS threshold
esxcli storage nmp psp roundrobin deviceconfig set \
    --device=naa.600508b4000c4a78 \
    --type=iops --iops=1

# Verificare tutti i path
esxcli storage nmp path list

# Stato path specifico
esxcli storage core path list --device=naa.600508b4000c4a78
```

### Fibre Channel

Fibre Channel e il protocollo storage SAN enterprise tradizionale:

```
+-------------------------------------------------------------------+
|                    Fibre Channel SAN                               |
+-------------------------------------------------------------------+
|                                                                    |
|  ESXi Host                                                         |
|  +-------------------+    +-------------------+                   |
|  | FC HBA            |    | FC HBA            |                   |
|  | vmhba1            |    | vmhba2            |                   |
|  | WWPN:             |    | WWPN:             |                   |
|  | 20:00:00:25:b5:01 |    | 20:00:00:25:b5:02 |                   |
|  +--------+----------+    +--------+----------+                   |
|           |                         |                              |
|  +--------v----------+    +--------v----------+                   |
|  | FC Switch (Fabric)|    | FC Switch (Fabric)|                   |
|  | (Fabric A)        |    | (Fabric B)        |                   |
|  | Zoning:           |    | Zoning:           |                   |
|  | ESXi -> Storage   |    | ESXi -> Storage   |                   |
|  +--------+----------+    +--------+----------+                   |
|           |                         |                              |
|  +--------v-------------------------v----------+                   |
|  |            Storage Array                     |                  |
|  |  +--------+  +--------+  +--------+         |                  |
|  |  | SP-A   |  | SP-B   |  | SP-C   |         |                  |
|  |  | Port 0 |  | Port 0 |  | Port 0 |         |                  |
|  |  +--------+  +--------+  +--------+         |                  |
|  |                                              |                  |
|  |  LUN Masking:                                |                  |
|  |  LUN 0 -> esxi-prod-01 (WWPN mapping)       |                  |
|  |  LUN 1 -> esxi-prod-01, esxi-prod-02        |                  |
|  +----------------------------------------------+                  |
+-------------------------------------------------------------------+
```

```bash
# Lista HBA Fibre Channel
esxcli storage core adapter list | grep -i fc

# Dettagli HBA FC
esxcli storage san fc list

# Verificare WWPN
esxcli storage san fc list | grep PortName

# Riscan per scoprire nuove LUN
esxcli storage core adapter rescan --all
```

### RDM (Raw Device Mapping)

RDM fornisce accesso diretto a una LUN SAN da dentro una VM, bypassando VMFS:

| Tipo | Descrizione | Uso |
|---|---|---|
| Physical RDM | Accesso diretto SCSI. VM vede il LUN nativo. | Microsoft Clustering, Oracle RAC |
| Virtual RDM | Mediato da VMkernel. Supporta snapshot e vMotion. | Applicazioni che necessitano identity LUN |

```bash
# Creare un RDM (via vmkfstools)
vmkfstools -z /vmfs/devices/disks/naa.600508b4000c4a78 \
    /vmfs/volumes/DS-Prod-01/vm-name/rdm-disk.vmdk

# Creare un Virtual RDM
vmkfstools -r /vmfs/devices/disks/naa.600508b4000c4a78 \
    /vmfs/volumes/DS-Prod-01/vm-name/rdm-disk.vmdk
```

**Nota migrazione**: I RDM devono essere convertiti in dischi regolari (qcow2 o raw) durante la migrazione a Proxmox. Non esiste un equivalente diretto, ma Proxmox supporta passthrough di interi dischi/partizioni per casi simili.

### Storage DRS

Storage DRS bilancia automaticamente il carico I/O e lo spazio tra datastore in un cluster:

```
+-------------------------------------------------------------------+
|                    Storage DRS Cluster                             |
+-------------------------------------------------------------------+
|                                                                    |
|  Datastore Cluster: "DSC-Production"                              |
|  +--------------------------------------------------------------+ |
|  |                                                               | |
|  |  +----------------+  +----------------+  +----------------+  | |
|  |  | DS-Prod-01     |  | DS-Prod-02     |  | DS-Prod-03     |  | |
|  |  | Capacity: 2 TB |  | Capacity: 2 TB |  | Capacity: 2 TB |  | |
|  |  | Used: 75%      |  | Used: 40%      |  | Used: 60%      |  | |
|  |  | I/O Latency:   |  | I/O Latency:   |  | I/O Latency:   |  | |
|  |  | 12 ms          |  | 5 ms           |  | 8 ms           |  | |
|  |  +----------------+  +----------------+  +----------------+  | |
|  |                                                               | |
|  |  Storage DRS Actions:                                         | |
|  |  - Space Balancing: Soglia 80% utilizzo                      | |
|  |  - I/O Balancing:   Soglia 15 ms latency                     | |
|  |  - Automation Level: Fully Automated / Manual                 | |
|  |  - Affinity Rules:  Keep VMDKs Together / Separate            | |
|  |                                                               | |
|  +--------------------------------------------------------------+ |
|                                                                    |
|  Storage vMotion: migra VMDK tra datastore in real-time           |
|  senza downtime per la VM.                                        |
|                                                                    |
+-------------------------------------------------------------------+
```

### Storage I/O Control (SIOC)

SIOC previene che una singola VM monopolizzi le risorse I/O di un datastore condiviso:

```bash
# Abilitare SIOC su un datastore
# (solo via vSphere Client o PowerCLI, non esxcli)
```

```powershell
# PowerCLI: Abilitare SIOC
$ds = Get-Datastore "DS-Prod-01"
$ds | Set-Datastore -StorageIOControlEnabled $true

# Configurare soglia di latenza (default 30 ms)
$ds.ExtensionData.ConfigureDatastoreIORM(
    (New-Object VMware.Vim.StorageIORMConfigSpec -Property @{
        Enabled = $true
        CongestionThresholdMode = "automatic"
    })
)

# Configurare IOPS shares per VM (come CPU/Memory shares)
# Tramite disk settings della VM: Shares = Low/Normal/High/Custom
```

### VAAI (vStorage APIs for Array Integration)

VAAI scarica operazioni dal host ESXi allo storage array per migliorare le performance:

| Primitiva VAAI | Operazione | Beneficio |
|---|---|---|
| Full Copy (XCOPY) | Clone / Storage vMotion | Lo storage copia internamente, non via ESXi |
| Block Zeroing (Write Same) | Provisioning thick eager-zeroed | Lo storage scrive zeri internamente |
| Hardware Assisted Locking (ATS) | VMFS locking | Lock atomico senza SCSI reservation |
| Thin Provisioning Stun | Datastore thin out-of-space | Pausa VM invece di crash |
| UNMAP | Recupero spazio thin | Notifica lo storage dei blocchi non usati |

```bash
# Verificare supporto VAAI per un dispositivo
esxcli storage core device vaai status get

# Verificare feature specifiche
esxcli storage core device list --device=naa.600508b4000c4a78 | grep -i vaai

# Verificare VAAI a livello globale
esxcli system settings advanced list -o /DataMover/HardwareAcceleratedMove
esxcli system settings advanced list -o /DataMover/HardwareAcceleratedInit
esxcli system settings advanced list -o /VMFS3/HardwareAcceleratedLocking
```

---

## vSAN

### Architettura vSAN

VMware vSAN e una soluzione di storage hyperconverged (HCI) integrata in ESXi. Aggrega lo storage locale di piu host ESXi in un datastore condiviso distribuito.

```
+=====================================================================+
|                    vSAN Architecture                                 |
+=====================================================================+
|                                                                      |
|  vSAN Cluster (minimo 3 host, raccomandato 4+)                     |
|                                                                      |
|  +------------------+  +------------------+  +------------------+   |
|  |   ESXi Host 1    |  |   ESXi Host 2    |  |   ESXi Host 3    |  |
|  |                   |  |                   |  |                   |  |
|  |  Disk Group 1:    |  |  Disk Group 1:    |  |  Disk Group 1:    |  |
|  |  +------+         |  |  +------+         |  |  +------+         |  |
|  |  | SSD  | Cache    |  |  | SSD  | Cache    |  |  | SSD  | Cache    |  |
|  |  | 400G | Tier     |  |  | 400G | Tier     |  |  | 400G | Tier     |  |
|  |  +------+         |  |  +------+         |  |  +------+         |  |
|  |  +------+------+  |  |  +------+------+  |  |  +------+------+  |  |
|  |  | HDD  | HDD  |  |  |  | HDD  | HDD  |  |  |  | HDD  | HDD  |  |  |
|  |  | 2 TB | 2 TB |  |  |  | 2 TB | 2 TB |  |  |  | 2 TB | 2 TB |  |  |
|  |  | Cap. | Cap. |  |  |  | Cap. | Cap. |  |  |  | Cap. | Cap. |  |  |
|  |  +------+------+  |  |  +------+------+  |  |  +------+------+  |  |
|  |                   |  |                   |  |                   |  |
|  |  CMMDS | CLOM     |  |  CMMDS | CLOM     |  |  CMMDS | CLOM     |  |
|  |  DOM   | LSOM     |  |  DOM   | LSOM     |  |  DOM   | LSOM     |  |
|  +------------------+  +------------------+  +------------------+   |
|           |                     |                     |              |
|           +---------------------+---------------------+              |
|                                 |                                    |
|                    vSAN Network (10 GbE dedicata)                   |
|                    (VMkernel port con vSAN traffic)                  |
|                                                                      |
|  vSAN Datastore: "vsanDatastore"                                    |
|  (distribuito su tutti gli host, object-based)                      |
|                                                                      |
+=====================================================================+
```

### Componenti vSAN

| Componente | Acronimo | Funzione |
|---|---|---|
| CMMDS | Cluster Monitoring, Membership and Directory Services | Cluster membership, object directory |
| CLOM | Cluster Level Object Manager | Placement e compliance degli oggetti |
| DOM | Distributed Object Manager | I/O path per gli oggetti |
| LSOM | Local Log-Structured Object Manager | I/O locale su disco |
| RDT | Reliable Datagram Transport | Protocollo di rete vSAN |

### Disk Groups

In vSAN Original Storage Architecture (OSA):

```
+-------------------------------------------------------------------+
|                    Disk Group Structure                            |
+-------------------------------------------------------------------+
|                                                                    |
|  Disk Group (max 5 per host):                                     |
|  +--------------------------------------------------------------+ |
|  |                                                               | |
|  |  Cache Tier (1 disco SSD/NVMe per disk group):               | |
|  |  +------------------+                                        | |
|  |  |   SSD / NVMe     |                                        | |
|  |  |   400 GB          |                                       | |
|  |  |                   |                                        | |
|  |  |   70% Read Cache  |                                       | |
|  |  |   30% Write Buffer|                                       | |
|  |  +------------------+                                        | |
|  |                                                               | |
|  |  Capacity Tier (1-7 dischi per disk group):                  | |
|  |  +--------+ +--------+ +--------+ +--------+                | |
|  |  |  HDD   | |  HDD   | |  HDD   | |  SSD   |               | |
|  |  |  2 TB  | |  2 TB  | |  2 TB  | |  2 TB  |               | |
|  |  +--------+ +--------+ +--------+ +--------+                | |
|  |                                                               | |
|  +--------------------------------------------------------------+ |
|                                                                    |
|  vSAN ESA (Express Storage Architecture, vSAN 8+):               |
|  - Elimina il concetto di disk group                              |
|  - Tutti i dischi NVMe in un single storage pool                  |
|  - Nessuna separazione cache/capacity                             |
|  - Performance superiori                                          |
|                                                                    |
+-------------------------------------------------------------------+
```

### Storage Policy-Based Management (SPBM)

vSAN utilizza policy di storage per definire il livello di protezione e le caratteristiche di ogni VM object:

```
+-------------------------------------------------------------------+
|                    vSAN Storage Policies                           |
+-------------------------------------------------------------------+
|                                                                    |
|  Policy: "Production-FTT1-RAID1"                                  |
|  +--------------------------------------------------------------+ |
|  |  Availability:                                                | |
|  |    Failures to Tolerate (FTT) = 1                             | |
|  |    Failure Tolerance Method = RAID-1 (Mirroring)              | |
|  |    -> Ogni oggetto ha 2 copie + 1 witness                    | |
|  |    -> Overhead storage: 2x                                   | |
|  |                                                               | |
|  |  Performance:                                                 | |
|  |    Stripe Width = 1 (default)                                 | |
|  |    IOPS Limit = 0 (unlimited)                                 | |
|  |    Object Space Reservation = 0% (thin)                      | |
|  |                                                               | |
|  |  Advanced:                                                    | |
|  |    Force Provisioning = No                                    | |
|  |    Disable Object Checksum = No                               | |
|  +--------------------------------------------------------------+ |
|                                                                    |
|  Distribuzione oggetti con FTT=1 / RAID-1:                       |
|                                                                    |
|  Host A           Host B           Host C                         |
|  +--------+       +--------+       +--------+                    |
|  | Object |       | Object |       | Witness|                    |
|  | Copy 1 |       | Copy 2 |       |  (< 2MB|                    |
|  +--------+       +--------+       | metadat|                    |
|                                     +--------+                    |
|                                                                    |
+-------------------------------------------------------------------+

+-------------------------------------------------------------------+
|  Combinazioni FTT comuni:                                         |
|                                                                    |
|  FTT | Method  | Min Hosts | Overhead | Tolleranza              |
|  ----|---------|-----------|----------|--------------------------|
|   0  |  None   |     1     |   1x     | Nessun failure           |
|   1  | RAID-1  |     3     |   2x     | 1 host failure           |
|   1  | RAID-5  |     4     |  1.33x   | 1 host failure           |
|   2  | RAID-1  |     5     |   3x     | 2 host failure           |
|   2  | RAID-6  |     6     |  1.5x    | 2 host failure           |
|   3  | RAID-1  |     7     |   4x     | 3 host failure           |
|                                                                    |
+-------------------------------------------------------------------+
```

```powershell
# PowerCLI: Creare una policy vSAN
New-SpbmStoragePolicy -Name "Production-FTT1-RAID1" `
    -Description "Production VMs with RAID-1 FTT=1" `
    -AnyOfRuleSets (
        New-SpbmRuleSet -AllOfRules @(
            New-SpbmRule -Capability (
                Get-SpbmCapability -Name "VSAN.hostFailuresToTolerate"
            ) -Value 1,
            New-SpbmRule -Capability (
                Get-SpbmCapability -Name "VSAN.replicaPreference"
            ) -Value "RAID-1 (Mirroring) - Performance"
        )
    )

# Assegnare policy a una VM
$vm = Get-VM "web-server-01"
$policy = Get-SpbmStoragePolicy "Production-FTT1-RAID1"
Set-SpbmEntityConfiguration -Configuration (
    Get-SpbmEntityConfiguration -VM $vm
) -StoragePolicy $policy

# Verificare compliance
Get-SpbmEntityConfiguration -VM (Get-VM) |
    Select-Object Entity, StoragePolicy, ComplianceStatus
```

### Failure Domains

I failure domain isolano i failure a livello di rack, fila, o sala:

```
+-------------------------------------------------------------------+
|                    Failure Domains                                 |
+-------------------------------------------------------------------+
|                                                                    |
|  Rack A (FD-A)      Rack B (FD-B)      Rack C (FD-C)            |
|  +-------------+    +-------------+    +-------------+            |
|  | Host-A1     |    | Host-B1     |    | Host-C1     |            |
|  | Host-A2     |    | Host-B2     |    | Host-C2     |            |
|  +-------------+    +-------------+    +-------------+            |
|                                                                    |
|  Con FTT=1 / RAID-1:                                             |
|  Object Copy 1 -> FD-A (Rack A)                                  |
|  Object Copy 2 -> FD-B (Rack B)                                  |
|  Witness        -> FD-C (Rack C)                                  |
|                                                                    |
|  Un intero rack puo andare offline senza perdita di dati.        |
|                                                                    |
+-------------------------------------------------------------------+
```

### Stretched Cluster

vSAN Stretched Cluster estende un singolo cluster vSAN su due siti fisici:

```
+=====================================================================+
|                    vSAN Stretched Cluster                            |
+=====================================================================+
|                                                                      |
|  Site A (Preferred)          Site B (Secondary)                     |
|  +-------------------+      +-------------------+                   |
|  | Host-A1           |      | Host-B1           |                   |
|  | Host-A2           |      | Host-B2           |                   |
|  | Host-A3           |      | Host-B3           |                   |
|  +-------------------+      +-------------------+                   |
|           |                          |                               |
|           |    <= 5 ms RTT           |                               |
|           |    >= 10 Gbps link       |                               |
|           +----------+---------------+                               |
|                      |                                               |
|              +-------v--------+                                      |
|              |  Witness Host  |                                      |
|              |  (Site C)      |                                      |
|              |  No data, solo |                                      |
|              |  quorum voting |                                      |
|              +----------------+                                      |
|                                                                      |
|  Distribuzione dati (FTT=1 RAID-1):                                |
|  Copy 1 -> Site A                                                    |
|  Copy 2 -> Site B                                                    |
|  Witness -> Site C                                                   |
|                                                                      |
|  In caso di failure Site A: VMs failover su Site B                  |
|  In caso di failure Site B: VMs continuano su Site A                |
|  In caso di partizione rete: Preferred Site (A) mantiene quorum     |
|                                                                      |
+=====================================================================+
```

### Deduplication e Compression

vSAN supporta deduplication e compression sulla capacity tier:

```
+-------------------------------------------------------------------+
|               Dedup & Compression (vSAN 6.2+)                     |
+-------------------------------------------------------------------+
|                                                                    |
|  1. Dati scritti nel write buffer (cache SSD)                     |
|                                                                    |
|  2. De-staging verso capacity tier:                               |
|     +---> Deduplication (per disk group, block-level)             |
|     |     Blocchi identici -> singola copia + reference           |
|     |                                                              |
|     +---> Compression (LZ4)                                       |
|           Blocchi rimanenti compressi                              |
|                                                                    |
|  Savings tipici: 2x - 7x (dipende dal workload)                  |
|                                                                    |
|  Vincoli:                                                          |
|  - Solo all-flash vSAN (non ibrido)                               |
|  - Abilitato per cluster (non per VM)                             |
|  - Overhead CPU: 5-15%                                            |
|  - Non disabilitabile senza ricostruzione disk group              |
|                                                                    |
+-------------------------------------------------------------------+
```

### Maintenance Mode vSAN

Quando un host vSAN entra in maintenance mode, e necessario scegliere come gestire i dati:

| Opzione | Descrizione | Tempo | Uso |
|---|---|---|---|
| Ensure Accessibility | Dati accessibili ma non pienamente protetti | Veloce | Patch rapide, reboot |
| Full Data Migration | Migra TUTTI i dati su altri host | Lento | Rimozione host, sostituzione disco |
| No Data Migration | Nessuna azione sui dati | Immediato | Solo se FTT > N failures attuali |

```powershell
# PowerCLI: Maintenance mode con opzioni vSAN
$vmhost = Get-VMHost "esxi-prod-01.lab.local"

# Ensure Accessibility (default, piu rapido)
Set-VMHost -VMHost $vmhost -State Maintenance `
    -VsanDataMigrationMode EnsureObjectAccessibility

# Full Data Migration (completa, lenta)
Set-VMHost -VMHost $vmhost -State Maintenance `
    -VsanDataMigrationMode Full

# Verificare stato resync vSAN
Get-VsanObject -Cluster "CL-Production" |
    Where-Object { $_.Health -ne "Healthy" }
```

### Comandi vSAN via esxcli

```bash
# Stato cluster vSAN
esxcli vsan cluster get

# Lista disk group
esxcli vsan storage list

# Health check
esxcli vsan health cluster list

# Performance diagnostics
esxcli vsan perf stats get

# Informazioni rete vSAN
esxcli vsan network list

# Verificare unicast agents
esxcli vsan cluster unicastagent list
```

---

## Confronto con Proxmox

### Mapping Networking VMware - Proxmox

La seguente tabella mappa i concetti di networking VMware ai corrispondenti in Proxmox VE:

```
+=====================================================================+
|            NETWORKING: VMware vSphere -> Proxmox VE                  |
+=====================================================================+
|                                                                      |
| VMware                      | Proxmox VE                            |
| =========================== | ===================================== |
| Standard vSwitch            | Linux Bridge (vmbr0, vmbr1, ...)      |
| Distributed vSwitch (dvS)   | Open vSwitch (OVS Bridge)             |
| Port Group                  | Bridge VLAN / OVS Port                |
| VMkernel Port               | IP su bridge / VLAN interface          |
| vmnic (uplink)              | Physical NIC (ens18, enp3s0, ...)     |
| NIC Teaming                 | Linux Bonding (bond0, bond1, ...)     |
| LACP                        | bond mode 4 (802.3ad)                 |
| Active/Standby              | bond mode 1 (active-backup)           |
| IP Hash                     | bond mode 4 (802.3ad) + xmit hash     |
| VLAN Tagging (VST)          | bridge vlan filtering / VLAN iface    |
| VLAN Trunk (VGT, 4095)      | vlan-aware bridge + trunk             |
| Traffic Shaping             | tc (traffic control) / OVS QoS       |
| NIOC                        | tc classes / OVS QoS                  |
| Jumbo Frames (MTU 9000)     | MTU su interface + bridge             |
| dvSwitch Port Mirroring     | OVS mirror ports                      |
| NetFlow/IPFIX               | OVS sFlow / nProbe                    |
| Private VLAN                | OVS Port Security / ebtables          |
| NSX                         | OVS + SDN (Proxmox VE SDN zones)     |
|                              |                                       |
+=====================================================================+
```

### Dettaglio Mapping Networking

```
+-------------------------------------------------------------------+
|  VMware Standard vSwitch    -->    Proxmox Linux Bridge            |
+-------------------------------------------------------------------+
|                                                                    |
|  VMware:                          Proxmox:                        |
|  +------------------+            +------------------+              |
|  | vSwitch0         |            | vmbr0            |              |
|  | MTU: 1500        |            | MTU: 1500        |              |
|  |                  |            |                  |              |
|  | PG: Management   |            | IP: 10.0.1.100  |              |
|  |   VLAN: none     |            |   /24            |              |
|  |   vmk0: mgmt     |            |                  |              |
|  |                  |            | bridge-ports:     |              |
|  | PG: VM Network   |            |   ens18          |              |
|  |   VLAN: 100      |            |                  |              |
|  |                  |            | bridge-vlan-aware:|              |
|  | Uplink: vmnic0   |            |   yes            |              |
|  +------------------+            +------------------+              |
|                                                                    |
|  /etc/network/interfaces (Proxmox):                               |
|                                                                    |
|  auto vmbr0                                                        |
|  iface vmbr0 inet static                                          |
|      address 10.0.1.100/24                                        |
|      gateway 10.0.1.1                                             |
|      bridge-ports ens18                                            |
|      bridge-stp off                                                |
|      bridge-fd 0                                                   |
|      bridge-vlan-aware yes                                         |
|      bridge-vids 2-4094                                            |
|                                                                    |
+-------------------------------------------------------------------+
```

```
+-------------------------------------------------------------------+
|  VMware NIC Teaming    -->    Proxmox Linux Bonding                |
+-------------------------------------------------------------------+
|                                                                    |
|  VMware:                          Proxmox:                        |
|  vSwitch con 2 uplink            bond0 con 2 slave               |
|  vmnic0 + vmnic1                 ens18 + ens19                    |
|                                                                    |
|  Policy VMware:                   Mode Linux:                     |
|  Route based on port -> N/A       mode 1 (active-backup)         |
|  IP Hash             -> OK        mode 4 (802.3ad/LACP)          |
|  Source MAC hash     -> simile    mode 2 (balance-xor)           |
|  Explicit failover   -> OK        mode 1 (active-backup)         |
|                                                                    |
|  /etc/network/interfaces (Proxmox):                               |
|                                                                    |
|  auto bond0                                                        |
|  iface bond0 inet manual                                          |
|      bond-slaves ens18 ens19                                       |
|      bond-miimon 100                                               |
|      bond-mode 802.3ad                                             |
|      bond-xmit-hash-policy layer3+4                               |
|                                                                    |
|  auto vmbr0                                                        |
|  iface vmbr0 inet static                                          |
|      address 10.0.1.100/24                                        |
|      gateway 10.0.1.1                                             |
|      bridge-ports bond0                                            |
|      bridge-stp off                                                |
|      bridge-fd 0                                                   |
|                                                                    |
+-------------------------------------------------------------------+
```

### Mapping Storage VMware - Proxmox

```
+=====================================================================+
|             STORAGE: VMware vSphere -> Proxmox VE                    |
+=====================================================================+
|                                                                      |
| VMware                      | Proxmox VE                            |
| =========================== | ===================================== |
| VMFS Datastore              | LVM / LVM-Thin / Directory            |
| NFS Datastore               | NFS storage (identico)                |
| iSCSI LUN -> VMFS           | LVM su iSCSI / iSCSI diretto         |
| Fibre Channel LUN -> VMFS   | LVM su FC LUN                         |
| vSAN                        | Ceph (RBD)                            |
| VMDK (thick)                | raw (LVM) / qcow2                     |
| VMDK (thin)                 | qcow2 / LVM-Thin                      |
| RDM                         | Disk passthrough / LVM                |
| Storage DRS                 | N/A (manuale / script)                |
| Storage vMotion              | Migrazione disco online               |
| VAAI                        | N/A (non necessario con LVM/Ceph)     |
| SIOC                        | cgroup I/O limits                     |
| Datastore Cluster           | Ceph pool / LVM VG multipli           |
| Content Library              | Proxmox storage templates             |
| vVol                        | N/A                                   |
| SPBM (policy-based)         | Ceph CRUSH rules / pool settings      |
| Snapshot (delta VMDK)        | qcow2 snapshot / LVM-Thin snapshot    |
| Linked Clone                | qcow2 backing file                    |
| Fault Tolerance disk         | N/A (HA con Ceph replication)         |
|                              |                                       |
+=====================================================================+
```

### Dettaglio Mapping Storage

```
+-------------------------------------------------------------------+
|  VMware VMFS Datastore    -->    Proxmox LVM / LVM-Thin           |
+-------------------------------------------------------------------+
|                                                                    |
|  VMware VMFS:                     Proxmox LVM:                    |
|  - Filesystem proprietario       - LVM standard Linux             |
|  - Cluster-aware (multi-host)    - Non cluster-aware              |
|  - File VMDK nel filesystem      - LV raw per ogni disco VM      |
|  - Max 64 TB                     - Max: dimensione VG             |
|  - On-disk locking (ATS)         - N/A (locale)                   |
|                                                                    |
|  Proxmox LVM-Thin:                                                |
|  - Thin provisioning nativo      - Equivalente VMDK thin          |
|  - Snapshot CoW                  - Equivalente snapshot VMware    |
|  - Overcommit possibile          - Come thin on VMFS              |
|                                                                    |
+-------------------------------------------------------------------+

+-------------------------------------------------------------------+
|  VMware vSAN    -->    Proxmox Ceph                               |
+-------------------------------------------------------------------+
|                                                                    |
|  VMware vSAN:                     Proxmox Ceph:                   |
|  - HCI (integrato in ESXi)       - HCI (integrato in Proxmox)    |
|  - Disk groups (OSA)             - OSD per disco                  |
|  - Cache + Capacity tier         - BlueStore (no tier separati)   |
|  - SPBM policies                 - CRUSH rules + pool settings   |
|  - Object-based                  - Object-based (RADOS)          |
|  - Replica / Erasure Coding      - Replica / Erasure Coding      |
|  - 10 GbE minimo                 - 10 GbE minimo                 |
|  - Licenza Enterprise / VCF      - Incluso (open-source)         |
|  - Witness per stretched         - Mon per quorum                 |
|  - Dedup + Compression           - Compression (BlueStore)       |
|  - vSAN ESA (8.0+)               - Ceph Reef/Squid               |
|                                                                    |
|  Confronto protezione:                                            |
|  vSAN FTT=1 RAID-1   ==  Ceph replica size=3, min_size=2        |
|  vSAN FTT=1 RAID-5   ==  Ceph Erasure Coding k=2,m=1            |
|  vSAN FTT=2 RAID-1   ==  Ceph replica size=5, min_size=3        |
|  vSAN FTT=2 RAID-6   ==  Ceph Erasure Coding k=4,m=2            |
|                                                                    |
+-------------------------------------------------------------------+
```

### Tabella Comparativa Completa

| Caratteristica | VMware vSphere | Proxmox VE |
|---|---|---|
| **NETWORKING** | | |
| Switch virtuale base | Standard vSwitch | Linux Bridge |
| Switch distribuito | Distributed vSwitch | Open vSwitch |
| Configurazione | GUI / PowerCLI | /etc/network/interfaces + GUI |
| VLAN | Port Group VLAN ID | bridge vlan filtering |
| NIC Teaming | 4 policy + failover | Linux bonding (7 modi) |
| QoS | NIOC (dvSwitch only) | tc / cgroup |
| SDN | NSX (licenza separata) | Proxmox SDN (integrato) |
| Firewall | NSX / ESXi firewall | pve-firewall (nftables) |
| Load Balancer | NSX LB | N/A (HAProxy esterno) |
| Complessita config | Media-Alta | Bassa-Media |
| **STORAGE** | | |
| Filesystem cluster | VMFS | GlusterFS / Ceph |
| HCI | vSAN | Ceph (integrato) |
| Formato disco VM | VMDK | qcow2 / raw |
| Thin provisioning | VMDK thin | qcow2 / LVM-Thin |
| Snapshot | Delta VMDK chain | qcow2 internal / LVM snap |
| Storage condiviso | NFS / iSCSI / FC | NFS / iSCSI / FC / Ceph |
| Deduplica | vSAN only | Ceph compression |
| Costo licenza storage | Enterprise+ / VCF | Incluso |
| Policy-based storage | SPBM + vSAN | Ceph CRUSH rules |
| Storage migration online | Storage vMotion | pvesm / qm move_disk |

### Guida alla Decisione Storage Post-Migrazione

```
+-------------------------------------------------------------------+
|           Decision Tree: Storage Post-Migrazione                   |
+-------------------------------------------------------------------+
|                                                                    |
|  Quanti host Proxmox?                                             |
|  |                                                                 |
|  +-- 1 host (standalone)                                          |
|  |   |                                                             |
|  |   +-- Storage locale?                                          |
|  |   |   +-- Si -> LVM o LVM-Thin (raccomandato)                 |
|  |   |   +-- ZFS se servono snapshot + compressione              |
|  |   |                                                             |
|  |   +-- Storage condiviso esistente?                             |
|  |       +-- NFS server -> NFS storage                            |
|  |       +-- iSCSI target -> LVM su iSCSI                        |
|  |                                                                 |
|  +-- 2 host (senza HA completo)                                   |
|  |   +-- NFS/iSCSI condiviso -> Migrazione online possibile      |
|  |   +-- Storage locale -> No migrazione online                   |
|  |                                                                 |
|  +-- 3+ host (cluster con HA)                                    |
|      |                                                             |
|      +-- Avevi vSAN?                                              |
|      |   +-- Si -> Ceph (equivalente funzionale)                  |
|      |   |   Minimo 3 nodi, 10 GbE dedicata, SSD per OSD         |
|      |   |                                                         |
|      |   +-- No -> Dipende dall'infrastruttura                    |
|      |       +-- SAN esistente -> NFS / iSCSI / FC               |
|      |       +-- Solo storage locale -> Ceph                      |
|      |                                                             |
|      +-- Budget?                                                   |
|          +-- Basso -> NFS (semplice, economico)                   |
|          +-- Medio -> iSCSI + LVM (buone performance)            |
|          +-- Alto  -> Ceph (max resilienza, performance)          |
|                                                                    |
+-------------------------------------------------------------------+
```

### Conversione Formati Disco

```bash
# === CONVERSIONE VMDK -> QCOW2/RAW (per Proxmox) ===

# VMDK monolitico -> qcow2 (thin)
qemu-img convert -f vmdk -O qcow2 vm-disk.vmdk vm-disk.qcow2

# VMDK -> raw (per LVM)
qemu-img convert -f vmdk -O raw vm-disk.vmdk vm-disk.raw

# VMDK sparse (vmdk + flat) -> qcow2
qemu-img convert -f vmdk -O qcow2 vm-disk.vmdk vm-disk.qcow2

# Importare disco in Proxmox
qm importdisk 100 vm-disk.qcow2 local-lvm --format qcow2

# Verificare formato e dimensioni
qemu-img info vm-disk.vmdk
# image: vm-disk.vmdk
# file format: vmdk
# virtual size: 100G
# disk size: 42G
# cluster_size: 65536

# Conversione con compressione
qemu-img convert -f vmdk -O qcow2 -c vm-disk.vmdk vm-disk-compressed.qcow2

# Conversione batch di tutti i VMDK in una directory
for vmdk in *.vmdk; do
    name="${vmdk%.vmdk}"
    echo "Converting: $vmdk -> ${name}.qcow2"
    qemu-img convert -f vmdk -O qcow2 -p "$vmdk" "${name}.qcow2"
done
```

### Checklist Networking e Storage Pre-Migrazione

```
+===================================================================+
|       CHECKLIST NETWORKING E STORAGE PRE-MIGRAZIONE               |
+===================================================================+
|                                                                    |
|  NETWORKING:                                                       |
|  [ ] Documentare tutti i vSwitch e dvSwitch                       |
|  [ ] Documentare tutti i port group e VLAN                        |
|  [ ] Documentare VMkernel ports (mgmt, vMotion, iSCSI, vSAN)    |
|  [ ] Documentare NIC teaming / LACP                              |
|  [ ] Documentare MTU (standard vs jumbo)                          |
|  [ ] Documentare NIOC settings (se dvSwitch)                     |
|  [ ] Documentare traffic shaping                                  |
|  [ ] Documentare firewall rules (ESXi + NSX se presente)         |
|  [ ] Mappare ogni configurazione VMware -> Proxmox               |
|  [ ] Verificare compatibilita driver NIC con Proxmox             |
|  [ ] Pianificare schema IP per i nodi Proxmox                    |
|  [ ] Pianificare rete dedicata per Ceph/Corosync (se cluster)    |
|                                                                    |
|  STORAGE:                                                          |
|  [ ] Documentare tutti i datastore (tipo, dimensione, uso)       |
|  [ ] Documentare tutti i VMDK (tipo, dimensione per VM)          |
|  [ ] Identificare RDM e pianificare conversione                   |
|  [ ] Consolidare tutti gli snapshot VM                            |
|  [ ] Documentare multipath policies                               |
|  [ ] Documentare iSCSI targets e CHAP                            |
|  [ ] Documentare NFS mounts e permessi                            |
|  [ ] Documentare FC zoning e LUN masking                          |
|  [ ] Documentare vSAN config (se presente)                       |
|  [ ] Pianificare storage target su Proxmox                        |
|  [ ] Calcolare spazio necessario per conversione VMDK            |
|  [ ] Pianificare metodo di trasferimento dati                     |
|  [ ] Stimare tempi di copia per ogni VM                           |
|  [ ] Testare conversione VMDK su VM campione                     |
|                                                                    |
+===================================================================+
```

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — vSAN OSA vs ESA.** Il modulo descrive principalmente l'architettura OSA (Original Storage Architecture) introdotta con vSAN 5.5, basata su disk group (1 cache + 1..7 capacity per host). Da vSAN 8.0 esiste anche **ESA (Express Storage Architecture)** — niente disk group, tutti i device NVMe lavorano in pool unico con codifica RAID-5/6 erasure coding via "log-structured" filesystem. Le due architetture coesistono e devono essere scelte all'abilitazione del cluster. Riferimento: [`VM-DOCS`] — pagina vSAN 8 OSA/ESA architecture (cercare "vSAN ESA" su `https://docs.vmware.com/en/VMware-vSphere/`).

> **Errore comune — IP Hash teaming senza LACP sullo switch fisico.** La policy "Route based on IP hash" e seducente perche sembra distribuire meglio il traffico, ma **richiede** che lo switch fisico abbia un Link Aggregation Group (LAG) statico o LACP corrispondente. Senza, lo switch vede MAC duplicati dallo stesso host arrivare da porte diverse, e il MAC table flaps ogni pochi millisecondi: la rete si comporta in modo erratico, le sessioni TCP cadono. Diagnosi tipica: log dello switch con `MAC flap detected` o `host moved between ports`. Per chi non controlla lo switch fisico, **scegliere "Route based on originating port ID"** (default) e non c'e mai il dubbio. Su Proxmox l'equivalente fragile e `bond-mode 802.3ad` senza LACP sullo switch — stesso sintomo.

> **Caso reale — Migrazione di un host con LUN FC condivise: ATS heartbeat e fencing.** Quando un host ESXi che monta una VMFS condivisa va offline brutalmente, gli altri host nel cluster aspettano la scadenza dell'ATS heartbeat lock (~16 s) per rilevare che il proprietario di una metadata transaction non risponde. Solo dopo possono prendersi il lock. In una migrazione con cutover stretto, conoscere questa finestra evita di interpretare un timeout di 16 s come fault: e fisiologico. Sul lato Proxmox, il `pmxcfs` ha un meccanismo simile (Corosync token timeout ~3-5 s di default), trattato nel modulo 17.1.

---

## Esercizi

1. **Concettuale — VST vs VGT.** Spiegare perche, su un firewall virtuale come pfSense o un router NSX-T edge, e tipico configurare il port group in **VGT** (VLAN ID 4095) e non in VST. *Risposta attesa:* il guest fa tagging multiplo internamente e il vSwitch deve passare i frame 802.1Q intatti senza spogliarli. Il vSwitch in VST li spoglierebbe pensando di filtrare per VLAN del port group, rompendo il routing inter-VLAN.
2. **Lab — assessment networking via PowerCLI.** Sul lab vSphere, eseguire i blocchi PowerCLI per estrarre `dvswitches.csv` e `portgroups.csv` (il modulo li introduce nei §dvSwitch). Aggiungere un'estrazione personalizzata che produca, per ogni dvPortGroup, il livello di shared service NIOC (es. `VirtualMachine`, `vMotion`, `iSCSI`) e l'eventuale traffic shaping. Salvare in `nioc-portgroups.csv`. *Verifica:* la somma delle shares VirtualMachine deve corrispondere a quanto configurato nel cluster (default 50 shares).
3. **Scenario — RDM in modalita physical.** Hai 4 VM con disco RDM physical (passthrough completo SCSI), tipicamente cluster Microsoft con shared storage. Argomentare in massimo 15 righe come pianificare la loro migrazione, sapendo che il pendant Proxmox non e un RDM ma SCSI passthrough con `qm set <vmid> --scsiX <storage>:<vol>,iothread=1` oppure `--scsi0 /dev/disk/by-id/...,backup=0` per pass-through diretto. *Risposta attesa:* (a) per cluster MSCS, considerare se passare a una soluzione Always On Availability Group (preferibile) o se tenere il pass-through diretto; (b) sequenza di backup applicativo + offline → conversione → import; (c) riprogettare l'eventuale persistent reservation (SCSI-3 PR) — non garantita su tutti i backend Proxmox.
4. **Stretch — confronto NIOC vs cgroups blkio.** Tracciare un parallelismo concettuale fra NIOC (Network I/O Control) e SIOC (Storage I/O Control) lato VMware, e gli strumenti Linux equivalenti (`tc` per il rate-limiting di rete, `cgroup` v2 IO controller). Indicare quali feature di NIOC non hanno equivalente diretto su Linux (es. shares relative, reservation per resource pool). Riferimento: [`PVE-WIKI`] — articolo "Network Configuration".

## Auto-valutazione

1. Differenza fondamentale fra Standard vSwitch e Distributed vSwitch: dove vive la control plane? Cosa succede se vCenter va offline?
2. Quale comando `esxcli` mostra le port group standard di un vSwitch?
3. Cosa rappresenta una "uplink port group" di un dvSwitch?
4. Tre policy di NIC teaming e per ciascuna: richiede o no configurazione LACP/LAG sullo switch fisico?
5. Cos'e VMFS-6 e quali sono le sue feature principali (lock type, max VMDK size, max LUN size)?
6. Cosa fa l'ATS heartbeat e quale e la sua frequenza tipica?
7. Differenza fra RDM virtual mode e RDM physical mode (cosa cambia per snapshot, vMotion, SCSI reservation)?
8. Quali sono i due tier di un disk group vSAN OSA e qual e il rapporto tipico fra essi?

(Tutte le risposte sono nel modulo. Se piu di 3 risposte mancano, rileggere le sezioni Networking, Storage, vSAN.)

## Letture primarie consigliate

- [`VM-DOCS`] VMware vSphere Documentation. https://docs.vmware.com/en/VMware-vSphere/ — sezioni "vSphere Networking" e "vSphere Storage".
- [`VM-COMPAT`] VMware Compatibility Guide. https://www.vmware.com/resources/compatibility/search.php — verificare che NIC e HBA del nuovo cluster Proxmox siano supportati anche da Linux (i driver native Linux sono spesso meglio mantenuti dei driver "VMware certified").
- KB Broadcom "vSAN OSA vs ESA architecture comparison". Cercare su `https://knowledge.broadcom.com/`.
- [`PVE-STORAGE`] Proxmox VE Wiki — Storage. https://pve.proxmox.com/wiki/Storage — tabella backend supportati Proxmox, da confrontare lato a lato con la VMware.
- [`IEEE-802.1Q`] IEEE 802.1Q — Virtual Bridged Local Area Networks. https://standards.ieee.org/ieee/802.1Q/6844/
- [`IEEE-802.1AX`] IEEE 802.1AX — Link Aggregation. https://standards.ieee.org/ieee/802.1AX/4940/
- [`OVS-DOCS`] Open vSwitch Documentation — per pianificare l'eventuale uso di OVS lato Proxmox come pendant del dvSwitch. https://docs.openvswitch.org/en/latest/

## Collegamenti incrociati

- Modulo 01.1 — `architettura-vsphere-esxi.md`: il pezzo precedente (compute), questo file e il pezzo gemello (network + storage).
- Modulo 03.1 — `../03-STORAGE-AVANZATO-PROXMOX/lvm-e-lvm-thin-proxmox.md`: pendant Proxmox di VMFS via LVM e LVM-Thin (con i loro limiti di shared cluster).
- Modulo 03.2 — `../03-STORAGE-AVANZATO-PROXMOX/nfs-iscsi-storage-condiviso.md`: pendant di NFS/iSCSI sul cluster Proxmox.
- Modulo 04.1 — `../04-NETWORKING-AVANZATO-PROXMOX/linux-bridge-vlan-bonding.md`: pendant del networking VMware sul Linux Bridge / OVS.
- Modulo 07.2 — `../07-MIGRAZIONE-NETWORKING/mapping-vswitch-linux-bridge.md`: il mapping operativo vSwitch/dvSwitch → Linux Bridge / OVS, in pratica.
- Modulo 08.1 — `../08-MIGRAZIONE-STORAGE/conversione-vmdk-qcow2-raw.md`: la conversione del formato disco da VMDK a qcow2/raw, con tabelle di performance.

## Glossario locale

| Termine | Definizione |
|---|---|
| **vSS / vSwitch standard** | Switch virtuale L2 locale a un singolo host ESXi. Non sincronizzato fra host. |
| **dvSwitch / VDS** | Distributed vSwitch — switch virtuale gestito centralmente da vCenter, esteso su piu host. |
| **dvPortGroup** | Port group definito sul dvSwitch (VLAN, policy, NIOC, port binding). |
| **VMkernel port (vmk)** | Interfaccia di rete per il traffico di sistema dell'host (mgmt, vMotion, iSCSI, NFS, vSAN). |
| **NIOC** | Network I/O Control — QoS lato dvSwitch sui tipi di traffico, in shares relative. |
| **SIOC** | Storage I/O Control — QoS lato datastore VMFS. Limita IOPS/throughput per VM in caso di contention. |
| **VST / EST / VGT** | Modalita di tagging VLAN: vSwitch tagging / External (switch fisico) / Virtual Guest (la VM tagga). |
| **PVLAN** | Private VLAN — isolamento L2 avanzato (Promiscuous / Community / Isolated). |
| **VMFS-6** | Cluster filesystem VMware sopra LUN condivise. ATS-only locking, max VMDK 62 TB, max LUN 64 TB. |
| **ATS** | Atomic Test & Set — primitiva SCSI VAAI usata da VMFS per il locking distribuito. |
| **NMP / PSP** | Native Multipath Plugin / Path Selection Policy (RR, MRU, Fixed). |
| **RDM** | Raw Device Mapping — VMDK speciale che mappa direttamente una LUN al guest. Modi virtual / physical. |
| **VAAI** | vStorage APIs for Array Integration — offloading di operazioni storage all'array (zero, copy, ATS). |
| **vVol** | Virtual Volumes — granularita per-VM su array supportati, sostituisce VMFS in alcuni scenari. |
| **vSAN OSA** | Original Storage Architecture — disk group (cache + capacity), pre-vSAN 8. |
| **vSAN ESA** | Express Storage Architecture — pool unico NVMe, log-structured, da vSAN 8. |
| **Witness host** | Host esterno (anche VM) che fornisce un voto di tie-break in un cluster vSAN stretched. |
| **Fault domain** | Insieme di host che condividono un single point of failure (rack, alimentazione); vSAN evita di mettere repliche dentro lo stesso fault domain. |
