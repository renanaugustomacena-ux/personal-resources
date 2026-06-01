# Security Monitoring for Virtual Infrastructure — SIEM Integration, Threat Detection, and Alerting

> **Course module:** VMware → Proxmox VE Migration
> **Position in track:** Phase 10 — Security Operations · Module 32
> **Prerequisites:** modules 01-02 (VMware/Proxmox fundamentals); module 12 (security & compliance); module 13 (monitoring & optimization); module 20 (hypervisor hardening); module 23 (forensics); familiarity with syslog protocols (RFC 5424/5425), Elasticsearch/OpenSearch, Prometheus data model, YAML/JSON configuration, Linux systemd, shell scripting.
> **Learning objectives.** Upon completion of this module the student will be able to:
> 1. design a **multi-layer monitoring architecture** covering hypervisor, VM, network, storage, and management planes;
> 2. configure **log collection and forwarding** from ESXi, vCenter, and Proxmox VE environments to centralized aggregation platforms;
> 3. integrate hypervisor telemetry into **SIEM platforms** (Wazuh, Elastic SIEM, Splunk) with proper normalization and correlation;
> 4. author **threat detection rules** targeting virtual infrastructure attacks — VM escape, privilege escalation, lateral movement, cryptomining, data exfiltration;
> 5. implement **network monitoring** for virtual switches including east-west traffic analysis, VLAN hopping detection, and encrypted traffic fingerprinting;
> 6. monitor **storage and backup** integrity, detecting ransomware indicators and unauthorized replication;
> 7. design **alerting and response** workflows with severity classification, alert fatigue reduction, and automated containment;
> 8. build **dashboards and visualization** in Grafana and Kibana for operational and security audiences;
> 9. deploy a **complete monitoring stack** in a lab environment and validate detection with simulated attacks.
> **Estimated time:** reading 150-200 min · lab deployment 8-16 hours · tuning and validation 2-4 weeks ongoing
> **Level:** proficient → expert (Dreyfus 4 → 5)
> **Last updated:** 2026-05-07
> **Reference versions:** Proxmox VE 8.x; VMware ESXi 7.0/8.0; vCenter 7.0/8.0; Wazuh 4.8+; Elasticsearch 8.x; Grafana 10.x+; Prometheus 2.50+; rsyslog 8.x; Filebeat 8.x

---

## Concept Map

```
+=====================================================================+
|     Security Monitoring for Virtual Infrastructure                   |
+=====================================================================+
|                                                                     |
|   DATA SOURCES                    COLLECTION LAYER                   |
|   +-------------------+          +-------------------------+        |
|   | Hypervisor Logs   |--------->| rsyslog / syslog-ng     |        |
|   | VM OS Logs        |--------->| Filebeat / Wazuh Agent  |        |
|   | Network Flows     |--------->| NetFlow / sFlow         |        |
|   | API Events        |--------->| Custom collectors       |        |
|   | Storage Metrics   |--------->| Prometheus exporters    |        |
|   +-------------------+          +-------------------------+        |
|                                           |                         |
|                                           v                         |
|                             +---------------------------+           |
|                             |   NORMALIZATION LAYER     |           |
|                             |   ECS / CEF / LEEF        |           |
|                             +---------------------------+           |
|                                           |                         |
|                                           v                         |
|   ANALYSIS & DETECTION               VISUALIZATION                  |
|   +-------------------+          +-------------------------+        |
|   | Wazuh SIEM        |          | Grafana Dashboards      |        |
|   | Elastic SIEM      |          | Kibana Security         |        |
|   | Splunk ES         |          | Custom Alerts UI        |        |
|   | Correlation Rules |          +-------------------------+        |
|   | ML Anomaly Detect |                                             |
|   +-------------------+                                             |
|            |                                                        |
|            v                                                        |
|   +-------------------+                                             |
|   | RESPONSE LAYER    |                                             |
|   | Automated actions |                                             |
|   | Runbook execution |                                             |
|   | Escalation procs  |                                             |
|   +-------------------+                                             |
+=====================================================================+
```

---

## 1. Monitoring Architecture for Virtual Environments

### 1.1 Monitoring Layers

A virtual infrastructure comprises distinct layers, each generating security-relevant telemetry. Failing to monitor any layer creates blind spots an attacker will exploit.

| Layer | Components | Data Types | Threat Examples |
|-------|-----------|------------|-----------------|
| Hardware/Firmware | BMC/IPMI, TPM, PCIe devices | Hardware events, attestation logs | Supply chain implants, firmware rootkits |
| Hypervisor | ESXi vmkernel, KVM/QEMU processes, Proxmox services | System logs, process metrics, kernel messages | VM escape, kernel exploitation |
| Management Plane | vCenter, pveproxy, Proxmox GUI/API | API audit logs, authentication events, task logs | Admin account compromise, unauthorized configuration |
| Virtual Network | vSwitch, OVS, SDN controllers | Flow records, packet captures, ARP tables | VLAN hopping, ARP spoofing, lateral movement |
| Storage | VMFS, ZFS, Ceph, iSCSI/NFS | I/O metrics, access logs, replication status | Ransomware, data exfiltration via storage |
| Guest VM | OS logs, application logs, EDR telemetry | syslog, Windows EventLog, process monitoring | Traditional malware, privilege escalation |

### 1.2 Data Sources

**Logs** — Structured and unstructured text records of events. Primary source for security investigation.

- ESXi: `/var/log/vmkernel.log`, `/var/log/hostd.log`, `/var/log/vpxa.log`, `/var/log/auth.log`
- Proxmox: systemd journal (`journalctl`), `/var/log/pveproxy/access.log`, `/var/log/pve/tasks/`
- vCenter: vpxd task/event database, SSO logs, alarm history

**Metrics** — Time-series numerical data for anomaly detection.

- CPU utilization per VM (sudden spikes → cryptomining)
- Network throughput per vNIC (sudden bursts → exfiltration)
- Disk IOPS patterns (random small writes → ransomware encryption)
- Memory pressure and ballooning events

**Flows** — Network connection metadata without full packet capture.

- NetFlow v9/IPFIX from virtual switches
- sFlow from physical switches with VM awareness
- Connection records from OVS (Open vSwitch)

**Events** — Discrete state changes in the management plane.

- VM lifecycle: create, clone, migrate, snapshot, delete
- Permission changes: role assignment, group membership
- Configuration: network, storage, cluster settings

### 1.3 Collection Architecture — Agent-Based vs Agentless

| Approach | Agent-Based | Agentless |
|----------|------------|-----------|
| Deployment | Install collector on each host | Remote collection via APIs/syslog |
| Coverage | Deep OS-level visibility | Limited to exposed interfaces |
| Resource cost | CPU/RAM on monitored hosts | Network bandwidth for polling |
| Security | Agent is additional attack surface | No software on hypervisor |
| Reliability | Survives network partitions (local buffer) | Fails if connectivity lost |
| Examples | Wazuh agent, Filebeat, node_exporter | vCenter API polling, SNMP, remote syslog |

**Recommended hybrid approach:**

1. **Agent on hypervisor hosts** (Wazuh agent, node_exporter) — provides real-time file integrity monitoring, rootkit detection, and deep system metrics.
2. **Agentless for management plane** — poll vCenter/Proxmox API for events without additional software in the control path.
3. **Syslog forwarding** — hypervisor native syslog to central collector as a network-level backup.
4. **Guest agents** — Full EDR/monitoring agent inside VMs (treated as traditional endpoints).

### 1.4 Centralized Monitoring Design

```
                    ┌─────────────────────────────────────────────┐
                    │          MONITORING CLUSTER (HA)            │
                    │                                             │
                    │  ┌─────────┐  ┌──────────┐  ┌──────────┐  │
                    │  │ Wazuh   │  │ Elastic  │  │ Prometheus│  │
                    │  │ Manager │  │ Cluster  │  │ + Thanos  │  │
                    │  └────┬────┘  └─────┬────┘  └─────┬────┘  │
                    │       │             │              │        │
                    │       └─────────────┼──────────────┘        │
                    │                     │                        │
                    │              ┌──────┴──────┐                │
                    │              │   Grafana   │                │
                    │              │   (viz)     │                │
                    │              └─────────────┘                │
                    └─────────────────────────────────────────────┘
                                       ▲
                                       │ (TLS encrypted)
                    ┌──────────────────┼──────────────────────────┐
                    │    LOG/METRIC AGGREGATION TIER              │
                    │                                             │
                    │  ┌───────────┐  ┌──────────┐  ┌─────────┐ │
                    │  │  rsyslog  │  │ Logstash │  │  Kafka   │ │
                    │  │  relay    │  │  /Vector │  │  (buffer)│ │
                    │  └───────────┘  └──────────┘  └─────────┘ │
                    └─────────────────────────────────────────────┘
                                       ▲
                                       │
         ┌─────────────┬──────────────┼──────────────┬─────────────┐
         │             │              │              │             │
    ┌────┴───┐   ┌────┴───┐   ┌─────┴────┐   ┌────┴───┐   ┌────┴───┐
    │ ESXi   │   │ ESXi   │   │ Proxmox  │   │ Proxmox│   │ vCenter│
    │ Host 1 │   │ Host 2 │   │ Node 1   │   │ Node 2 │   │ Server │
    └────────┘   └────────┘   └──────────┘   └────────┘   └────────┘
```

**Design principles:**

1. **Separation of concerns** — Monitoring infrastructure MUST NOT run on the monitored hypervisors. Dedicate separate physical or virtual infrastructure for monitoring.
2. **Buffer and replay** — Insert a message queue (Kafka, Redis Streams) between collectors and analytics to absorb spikes and enable replay during maintenance.
3. **Encryption in transit** — All log forwarding uses TLS 1.3. Mutual TLS (mTLS) for agent-to-manager communication.
4. **Network segmentation** — Monitoring traffic on a dedicated management VLAN/network, isolated from production traffic.

### 1.5 High Availability for Monitoring Infrastructure

Monitoring must survive the failure of any single component:

| Component | HA Strategy |
|-----------|-------------|
| Wazuh Manager | Active-passive cluster with shared filesystem or Wazuh cluster mode (manager + workers) |
| Elasticsearch | Multi-node cluster (minimum 3 masters, 2+ data nodes), cross-datacenter replication |
| Prometheus | Dual independent Prometheus servers scraping same targets + Thanos for global view |
| Grafana | Multiple instances behind load balancer, shared PostgreSQL for dashboards |
| rsyslog relay | Active-active pair with RELP protocol and disk-assisted queues |
| Kafka | Multi-broker cluster (minimum 3), replication factor ≥ 2 |

### 1.6 Retention and Storage Planning

| Data Type | Hot (fast query) | Warm (compressed) | Cold (archive) | Total |
|-----------|-----------------|-------------------|----------------|-------|
| Security logs (auth, changes) | 30 days | 90 days | 7 years (compliance) | 7 years |
| Performance metrics | 15 days (full resolution) | 90 days (downsampled 5m) | 1 year (1h resolution) | 1 year |
| Network flows | 7 days | 30 days | 90 days | 90 days |
| Full packet captures | 24 hours | 7 days (filtered) | N/A | 7 days |
| Audit logs (management plane) | 90 days | 1 year | 7 years | 7 years |

**Storage sizing formula:**

```
Daily_ingest_GB = (hosts × avg_eps × avg_event_size_bytes × 86400) / (1024^3)
Hot_storage_GB = Daily_ingest_GB × hot_retention_days × (1 + replication_factor)
```

For a 20-host Proxmox cluster generating ~500 EPS average with 800 byte average event size:
- Daily ingest: ~33 GB/day
- 30-day hot storage with RF=1: ~2 TB
- Plan for 3-5x growth headroom.

---

## 2. ESXi and vCenter Monitoring

### 2.1 Syslog Configuration and Forwarding

ESXi hosts must be configured to forward logs to a remote syslog server. This is both a security requirement (logs survive host compromise) and an operational necessity.

**Configure syslog forwarding via esxcli:**

```bash
# Set remote syslog target (TCP with TLS preferred)
esxcli system syslog config set \
  --loghost="ssl://siem.internal.corp:6514,udp://backup-syslog.internal.corp:514"

# Set log level
esxcli system syslog config set --logdir-unique=true

# Reload syslog daemon
esxcli system syslog reload

# Verify configuration
esxcli system syslog config get

# Open firewall for syslog
esxcli network firewall ruleset set --ruleset-id=syslog --enabled=true
esxcli network firewall refresh
```

**Configure via vCenter (at scale via Host Profile):**

1. Navigate to Host → Configure → System → Advanced System Settings
2. Set `Syslog.global.logHost` to `ssl://siem.internal.corp:6514`
3. Set `Syslog.global.logDirUnique` to `true`
4. Apply as Host Profile for cluster-wide enforcement

**rsyslog receiver configuration for ESXi logs:**

```conf
# /etc/rsyslog.d/10-esxi-receiver.conf

# Load TLS module
module(load="imtcp")
module(load="imtls" StreamDriver.Name="gtls"
       StreamDriver.Mode="1"
       StreamDriver.AuthMode="x509/fingerprint")

# TLS input on port 6514
input(type="imtcp" port="6514"
      StreamDriver.Name="gtls"
      StreamDriver.Mode="1"
      StreamDriver.AuthMode="x509/fingerprint"
      StreamDriver.PermittedPeer=["SHA1:XX:XX:XX..."])

# Template for ESXi logs
template(name="ESXiLogFormat" type="string"
  string="/var/log/esxi/%HOSTNAME%/%PROGRAMNAME%-%$YEAR%-%$MONTH%-%$DAY%.log")

# Rule: route ESXi logs to per-host files and forward to Elasticsearch
if $fromhost-ip startswith '10.10.20.' then {
    action(type="omfile" dynaFile="ESXiLogFormat"
           FileCreateMode="0640" DirCreateMode="0750")
    action(type="omfwd" Target="logstash.internal.corp" Port="5044"
           Protocol="tcp" Template="RSYSLOG_SyslogProtocol23Format")
    stop
}
```

### 2.2 Key Log Files and Their Security Relevance

| Log File | Path on ESXi | Security Relevance |
|----------|-------------|-------------------|
| vmkernel.log | /var/log/vmkernel.log | Kernel-level events; storage errors; network drops; potential exploitation |
| hostd.log | /var/log/hostd.log | Host management agent; VM operations; authentication |
| vpxa.log | /var/log/vpxa.log | vCenter agent communication; task execution |
| auth.log | /var/log/auth.log | SSH/shell authentication; PAM events |
| vobd.log | /var/log/vobd.log | VMware Observation Broker; correlates cross-component events |
| shell.log | /var/log/shell.log | ESXi Shell commands executed (CRITICAL — detect unauthorized shell use) |
| fdm.log | /var/log/fdm.log | Fault Domain Manager; HA state changes |
| vsantraces | /var/log/vsantraces/ | vSAN distributed storage events |

**Critical events to monitor:**

```
# Unauthorized Shell access
grep -i "SSH session was opened\|UserLogin\|UserLogout" /var/log/auth.log

# VM operations (create, delete, clone, export)
grep "VmCreatedEvent\|VmRemovedEvent\|VmClonedEvent\|VmExportedEvent" /var/log/hostd.log

# Configuration changes
grep "vim.option.OptionManager\|HostConfigChangedEvent" /var/log/vpxa.log

# Permission modifications
grep "RoleAddedEvent\|RoleRemovedEvent\|PermissionAddedEvent" /var/log/vpxa.log
```

### 2.3 vCenter Event Collection

vCenter maintains a comprehensive event database accessible via SOAP/REST API and the MOB (Managed Object Browser).

**Key event categories:**

| Category | Example Events | Detection Use |
|----------|---------------|---------------|
| Authentication | UserLoginSessionEvent, UserLogoutSessionEvent, BadUsernameSessionEvent | Brute force, credential stuffing |
| VM Lifecycle | VmCreatedEvent, VmRemovedEvent, VmMigratedEvent, VmClonedEvent | Unauthorized operations |
| Permission | RoleAddedEvent, PermissionAddedEvent, PermissionRemovedEvent | Privilege escalation |
| Task | TaskEvent (power operations, snapshot, reconfigure) | Change tracking |
| Alarm | AlarmCreatedEvent, AlarmRemovedEvent, AlarmStatusChangedEvent | Alarm suppression by attacker |
| Datastore | DatastoreFileMovedEvent, DatastoreFileDeletedEvent | Data destruction/exfiltration |

**PowerCLI script for security event extraction:**

```powershell
# Connect to vCenter
Connect-VIServer -Server vcenter.internal.corp -Credential $cred

# Get security-relevant events from last 24 hours
$startTime = (Get-Date).AddHours(-24)

# Authentication failures
Get-VIEvent -Start $startTime -MaxSamples 10000 | Where-Object {
    $_.GetType().Name -match "BadUsernameSessionEvent|NoPermissionEvent|InvalidLogin"
} | Select-Object CreatedTime, UserName, FullFormattedMessage |
  Export-Csv -Path "auth_failures_$(Get-Date -Format yyyyMMdd).csv" -NoTypeInformation

# Permission changes
Get-VIEvent -Start $startTime -MaxSamples 10000 | Where-Object {
    $_.GetType().Name -match "Permission|Role"
} | Select-Object CreatedTime, UserName, FullFormattedMessage |
  Export-Csv -Path "permission_changes_$(Get-Date -Format yyyyMMdd).csv" -NoTypeInformation

# VM export/clone operations (potential data theft)
Get-VIEvent -Start $startTime -MaxSamples 10000 | Where-Object {
    $_.GetType().Name -match "VmClonedEvent|VmExportedEvent|VmCreatedEvent"
} | ForEach-Object {
    [PSCustomObject]@{
        Time    = $_.CreatedTime
        User    = $_.UserName
        VM      = $_.Vm.Name
        Event   = $_.GetType().Name
        Message = $_.FullFormattedMessage
    }
} | Export-Csv -Path "vm_operations_$(Get-Date -Format yyyyMMdd).csv" -NoTypeInformation

# Disconnect
Disconnect-VIServer -Confirm:$false
```

### 2.4 ESXi Performance Counters for Security

Performance counters are not traditionally viewed as security data, but anomalies in them often indicate compromise:

| Counter | Normal Range | Security Anomaly | Possible Cause |
|---------|-------------|------------------|----------------|
| cpu.ready.summation | < 5% | Sustained > 20% | Cryptominer consuming all CPU, noisy neighbor attack |
| mem.swapped.average | 0 | Large sudden increase | Memory pressure from unauthorized VMs or memory scraping |
| net.bytesRx/Tx.average | Baseline ± 2σ | 10x baseline sustained | Data exfiltration, DDoS participation |
| disk.commandsAveraged | Baseline ± 2σ | Random pattern + high latency | Ransomware encryption |
| cpu.costop.summation | 0 for most VMs | Non-zero on critical VMs | SMP scheduling interference (potential DoS) |

### 2.5 vRealize Log Insight / Aria Operations for Logs

VMware's native log analytics (now Aria Operations for Logs) provides:

- Pre-built content packs for vSphere security events
- Machine learning-based anomaly detection on log rates
- Interactive dashboards for authentication, change, and compliance
- Webhook and SNMP alerting

**Integration with external SIEM:** Configure Aria Operations for Logs to forward normalized events via syslog (CEF format) or webhook to your SIEM platform for unified correlation with non-VMware data.

---

## 3. Proxmox Monitoring

### 3.1 Systemd Journal Collection

Proxmox VE runs on Debian with systemd. All service logs flow through the journal.

**Configure persistent journal with security-relevant settings:**

```ini
# /etc/systemd/journald.conf.d/security.conf
[Journal]
Storage=persistent
Compress=yes
SystemMaxUse=4G
MaxRetentionSec=30day
ForwardToSyslog=yes
Seal=yes
# Seal provides FSS (Forward Secure Sealing) for tamper evidence
```

**Forward journal to remote syslog:**

```conf
# /etc/rsyslog.d/50-proxmox-forward.conf
module(load="imjournal" StateFile="imjournal.state" Ratelimit.Interval="0")

# Template for structured output
template(name="ProxmoxJSON" type="list") {
    constant(value="{")
    constant(value="\"@timestamp\":\"")    property(name="timereported" dateFormat="rfc3339")
    constant(value="\",\"host\":\"")       property(name="hostname")
    constant(value="\",\"program\":\"")    property(name="programname")
    constant(value="\",\"severity\":\"")   property(name="syslogseverity-text")
    constant(value="\",\"message\":\"")    property(name="msg" format="json")
    constant(value="\"}")
    constant(value="\n")
}

# Forward all Proxmox-related logs
if ($programname startswith 'pve' or
    $programname == 'corosync' or
    $programname == 'qemu-system' or
    $programname == 'pvedaemon' or
    $programname == 'pmxcfs' or
    $programname startswith 'ceph') then {
    action(type="omfwd"
           Target="siem.internal.corp"
           Port="5514"
           Protocol="tcp"
           Template="ProxmoxJSON"
           queue.type="LinkedList"
           queue.size="50000"
           queue.filename="proxmox_fwd"
           queue.saveonshutdown="on"
           action.resumeRetryCount="-1")
}
```

### 3.2 pveproxy/pvedaemon/corosync Log Analysis

**pveproxy** (API/Web GUI gateway):

```bash
# Authentication events
journalctl -u pveproxy --since "1 hour ago" | grep -i "authentication\|login\|failed\|ticket"

# Key patterns:
# "authentication failure" → failed login attempt
# "successful auth for user" → successful authentication
# "permission denied" → authorization failure
# "new ticket for" → session token issued
```

**pvedaemon** (cluster management daemon):

```bash
# VM operations
journalctl -u pvedaemon --since "1 hour ago" | grep -i "qmcreate\|qmdestroy\|vzdump\|qmclone\|qmmigrate"

# Storage changes
journalctl -u pvedaemon --since "1 hour ago" | grep -i "storage\|volume\|disk"

# User/permission changes
journalctl -u pvedaemon --since "1 hour ago" | grep -i "useradd\|userdel\|roleadd\|aclmod"
```

**corosync** (cluster communication):

```bash
# Cluster membership changes (critical — node addition/removal)
journalctl -u corosync --since "1 hour ago" | grep -i "member\|joined\|left\|quorum"

# Communication failures (potential network partition or attack)
journalctl -u corosync --since "1 hour ago" | grep -i "failed\|retransmit\|token lost"
```

### 3.3 Task Log Monitoring

Proxmox records all administrative actions as tasks:

```bash
# List recent tasks via API
pvesh get /cluster/tasks --limit 50 --output-format json | \
  jq '.[] | select(.status != "OK") | {node, type, user, status, starttime}'

# Monitor task directory for new operations
inotifywait -m -r /var/log/pve/tasks/ -e create -e modify | while read dir action file; do
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) TASK_EVENT: ${dir}${file} ${action}"
done
```

**Security-critical task types to monitor:**

| Task Type | Description | Alert Level |
|-----------|-------------|-------------|
| qmcreate | New VM creation | MEDIUM (outside change window = HIGH) |
| qmdestroy | VM deletion | HIGH |
| qmclone | VM cloning | HIGH (potential data theft) |
| vzdump | Backup creation | MEDIUM (verify authorized) |
| qmmigrate | Live migration | MEDIUM (unexpected = HIGH) |
| ha-manager | HA state change | HIGH (unexpected) |
| aptupdate/aptdist | Package operations | MEDIUM |

### 3.4 QEMU Process Monitoring

Each VM runs as a QEMU process. Monitoring these processes provides visibility into VM behavior at the hypervisor level:

```bash
#!/bin/bash
# /usr/local/bin/pve-qemu-monitor.sh
# Monitor QEMU processes for anomalies

while true; do
    for pid in $(pgrep -f "qemu-system"); do
        vm_id=$(cat /proc/$pid/cmdline | tr '\0' '\n' | grep -oP '(?<=-id )\d+' | head -1)
        
        # CPU usage (detect cryptomining)
        cpu_pct=$(ps -p $pid -o %cpu= | tr -d ' ')
        
        # Memory usage
        mem_rss=$(ps -p $pid -o rss= | tr -d ' ')
        
        # Open file descriptors (detect data exfiltration channels)
        fd_count=$(ls /proc/$pid/fd 2>/dev/null | wc -l)
        
        # Network connections from QEMU process
        net_conns=$(ss -tnp | grep "pid=$pid" | wc -l)
        
        # Alert on anomalies
        if (( $(echo "$cpu_pct > 95" | bc -l) )); then
            logger -t "pve-security" -p auth.warning \
              "ALERT: VM $vm_id (PID $pid) CPU usage ${cpu_pct}% - possible cryptominer"
        fi
        
        if (( fd_count > 500 )); then
            logger -t "pve-security" -p auth.warning \
              "ALERT: VM $vm_id (PID $pid) excessive FDs: $fd_count - investigate"
        fi
    done
    sleep 30
done
```

### 3.5 Proxmox Metrics — Graphite/InfluxDB Export

Proxmox has built-in metric server support:

```conf
# /etc/pve/status.cfg

# InfluxDB export
influxdb: influxdb-security
    server 10.10.30.50
    port 8086
    organization proxmox-monitoring
    bucket pve-metrics
    token AUTH_TOKEN_HERE
    influxdbproto http
    max-body-size 25000000
    verify-certificate 1

# Graphite export (alternative)
graphite: graphite-security
    server 10.10.30.51
    port 2003
    path proxmox
    proto tcp
```

### 3.6 Custom Monitoring with pvesh API

```bash
#!/bin/bash
# /usr/local/bin/pve-security-collector.sh
# Custom security metric collector using Proxmox API

PVE_API="https://localhost:8006/api2/json"
TOKEN="PVEAPIToken=monitor@pve!security-token=UUID-TOKEN-HERE"

# Collect cluster status
cluster_status=$(curl -sk -H "Authorization: $TOKEN" "$PVE_API/cluster/status")

# Check for unexpected nodes
expected_nodes=("pve01" "pve02" "pve03")
current_nodes=$(echo "$cluster_status" | jq -r '.data[] | select(.type=="node") | .name')

for node in $current_nodes; do
    if [[ ! " ${expected_nodes[*]} " =~ " $node " ]]; then
        logger -t "pve-security" -p auth.crit \
          "CRITICAL: Unexpected node '$node' in cluster!"
    fi
done

# Check running VMs against inventory
running_vms=$(curl -sk -H "Authorization: $TOKEN" "$PVE_API/cluster/resources?type=vm" | \
  jq -r '.data[] | select(.status=="running") | .vmid')

# Check for VMs not in approved inventory
while IFS= read -r vmid; do
    if ! grep -q "^$vmid$" /etc/pve/approved-vms.list 2>/dev/null; then
        logger -t "pve-security" -p auth.warning \
          "WARNING: VM $vmid running but not in approved inventory"
    fi
done <<< "$running_vms"

# Check for permission changes
curl -sk -H "Authorization: $TOKEN" "$PVE_API/access/acl" | \
  jq '.data' > /tmp/current_acl.json

if [ -f /var/lib/pve-security/previous_acl.json ]; then
    if ! diff -q /tmp/current_acl.json /var/lib/pve-security/previous_acl.json > /dev/null 2>&1; then
        diff /var/lib/pve-security/previous_acl.json /tmp/current_acl.json | \
          logger -t "pve-security" -p auth.warning
    fi
fi
cp /tmp/current_acl.json /var/lib/pve-security/previous_acl.json
```

### 3.7 Prometheus Integration

**pve-exporter** provides Prometheus metrics from Proxmox API:

```yaml
# prometheus.yml - scrape configuration
scrape_configs:
  - job_name: 'pve'
    static_configs:
      - targets:
        - pve01.internal.corp
        - pve02.internal.corp
        - pve03.internal.corp
    metrics_path: /pve
    params:
      module: [default]
      cluster: ['1']
      node: ['1']
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: pve-exporter.internal.corp:9221

  - job_name: 'node-exporter-pve'
    static_configs:
      - targets:
        - pve01.internal.corp:9100
        - pve02.internal.corp:9100
        - pve03.internal.corp:9100
    relabel_configs:
      - source_labels: [__address__]
        regex: '(.*):\d+'
        target_label: instance
```

**node_exporter textfile collector for custom security metrics:**

```bash
#!/bin/bash
# /usr/local/bin/pve-security-textfile.sh
# Runs via cron every minute, writes Prometheus textfile metrics

TEXTFILE_DIR="/var/lib/node_exporter/textfile"
OUTPUT="${TEXTFILE_DIR}/pve_security.prom"

# Count failed login attempts in last 5 minutes
failed_logins=$(journalctl -u pveproxy --since "5 minutes ago" 2>/dev/null | \
  grep -c "authentication failure" || echo 0)

# Count active SSH sessions
ssh_sessions=$(who | wc -l)

# Count running VMs
running_vms=$(qm list 2>/dev/null | grep running | wc -l)

# Count running containers
running_cts=$(pct list 2>/dev/null | grep running | wc -l)

# Cluster quorum status (1=quorate, 0=not)
quorum=$(pvecm status 2>/dev/null | grep -c "Quorate:.*Yes" || echo 0)

cat > "${OUTPUT}.tmp" <<EOF
# HELP pve_security_failed_logins Failed login attempts in last 5 minutes
# TYPE pve_security_failed_logins gauge
pve_security_failed_logins $failed_logins
# HELP pve_security_ssh_sessions Active SSH sessions
# TYPE pve_security_ssh_sessions gauge
pve_security_ssh_sessions $ssh_sessions
# HELP pve_security_running_vms Number of running VMs
# TYPE pve_security_running_vms gauge
pve_security_running_vms $running_vms
# HELP pve_security_running_containers Number of running containers
# TYPE pve_security_running_containers gauge
pve_security_running_containers $running_cts
# HELP pve_security_cluster_quorum Cluster quorum status
# TYPE pve_security_cluster_quorum gauge
pve_security_cluster_quorum $quorum
EOF

mv "${OUTPUT}.tmp" "$OUTPUT"
```

---

## 4. SIEM Integration

### 4.1 Log Forwarding Architecture

```
                  ┌──────────────────────────────────────────┐
                  │              SIEM TIER                    │
                  │  Wazuh Manager ←→ Elasticsearch          │
                  └────────────────────┬─────────────────────┘
                                       │
                              ┌────────┴────────┐
                              │   Logstash /    │
                              │   Vector        │
                              │   (normalize)   │
                              └────────┬────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
              ┌─────┴─────┐    ┌──────┴─────┐    ┌──────┴─────┐
              │  rsyslog   │    │  Filebeat  │    │   Wazuh    │
              │  (UDP/TCP) │    │  (files)   │    │   Agent    │
              └─────┬─────┘    └──────┬─────┘    └──────┬─────┘
                    │                 │                  │
              ESXi syslog      PVE log files      PVE host agent
```

**rsyslog forwarding configuration (Proxmox host):**

```conf
# /etc/rsyslog.d/60-siem-forward.conf

# Load output modules
module(load="omrelp")  # Reliable Event Logging Protocol

# Define RELP action for guaranteed delivery
action(type="omrelp"
       Target="siem.internal.corp"
       Port="2514"
       Template="RSYSLOG_SyslogProtocol23Format"
       queue.type="LinkedList"
       queue.size="100000"
       queue.filename="siem_fwd_queue"
       queue.maxDiskSpace="1g"
       queue.saveOnShutdown="on"
       queue.highWatermark="80000"
       queue.lowWatermark="60000"
       action.resumeRetryCount="-1"
       action.reportSuspension="on"
       action.reportSuspensionContinuation="on")
```

**Filebeat configuration for Proxmox:**

```yaml
# /etc/filebeat/filebeat.yml
filebeat.inputs:
  - type: log
    id: pve-access
    enabled: true
    paths:
      - /var/log/pveproxy/access.log
    fields:
      log_type: pve_access
      environment: production
    fields_under_root: true

  - type: log
    id: pve-tasks
    enabled: true
    paths:
      - /var/log/pve/tasks/active
    fields:
      log_type: pve_task
    fields_under_root: true
    multiline.pattern: '^\d{4}-\d{2}-\d{2}'
    multiline.negate: true
    multiline.match: after

  - type: journald
    id: pve-services
    enabled: true
    include_matches:
      - _SYSTEMD_UNIT=pveproxy.service
      - _SYSTEMD_UNIT=pvedaemon.service
      - _SYSTEMD_UNIT=corosync.service
      - _SYSTEMD_UNIT=pve-cluster.service
      - _SYSTEMD_UNIT=ceph-mon@*.service
      - _SYSTEMD_UNIT=ceph-osd@*.service
    fields:
      log_type: pve_systemd
    fields_under_root: true

output.elasticsearch:
  hosts: ["https://es01.internal.corp:9200", "https://es02.internal.corp:9200"]
  protocol: "https"
  ssl.certificate_authorities: ["/etc/filebeat/ca.crt"]
  ssl.certificate: "/etc/filebeat/filebeat.crt"
  ssl.key: "/etc/filebeat/filebeat.key"
  index: "filebeat-pve-%{+yyyy.MM.dd}"

processors:
  - add_host_metadata:
      when.not.contains.tags: forwarded
  - add_cloud_metadata: ~
  - dissect:
      when:
        equals:
          log_type: pve_access
      tokenizer: '%{client_ip} - %{user} [%{timestamp}] "%{method} %{uri} %{http_version}" %{status_code} %{bytes}'
      field: "message"
      target_prefix: "pve.access"
```

### 4.2 Log Normalization — ECS/CEF/LEEF

**Elastic Common Schema (ECS) mapping for Proxmox events:**

```json
{
  "ecs.version": "8.11.0",
  "event.kind": "event",
  "event.category": ["authentication"],
  "event.type": ["start"],
  "event.action": "user-login",
  "event.outcome": "failure",
  "event.module": "proxmox",
  "event.dataset": "proxmox.auth",
  "@timestamp": "2026-05-07T14:23:01.000Z",
  "source.ip": "10.10.5.42",
  "user.name": "admin@pve",
  "user.domain": "pve",
  "host.name": "pve01",
  "host.ip": ["10.10.20.1"],
  "service.name": "pveproxy",
  "observer.type": "hypervisor",
  "observer.vendor": "Proxmox",
  "observer.product": "Proxmox VE",
  "observer.version": "8.2.4"
}
```

**CEF (Common Event Format) mapping for VMware events:**

```
CEF:0|VMware|vCenter|8.0|AUTH_FAILURE|Authentication Failure|7|
  src=10.10.5.42 duser=admin@vsphere.local
  dhost=vcenter.internal.corp msg=Login failed: invalid credentials
  rt=May 07 2026 14:23:01 cat=Authentication
  cs1Label=EventType cs1=BadUsernameSessionEvent
  cs2Label=SessionId cs2=52f3a1b2-xxxx
```

**Logstash normalization pipeline:**

```ruby
# /etc/logstash/conf.d/20-proxmox-normalize.conf
filter {
  if [log_type] == "pve_access" {
    grok {
      match => {
        "message" => "%{IP:source.ip} - %{DATA:user.name} \[%{HTTPDATE:event.timestamp}\] \"%{WORD:http.request.method} %{URIPATHPARAM:url.path} HTTP/%{NUMBER:http.version}\" %{NUMBER:http.response.status_code} %{NUMBER:http.response.body.bytes}"
      }
    }

    # Classify security events
    if [http.response.status_code] == "401" or [http.response.status_code] == "403" {
      mutate {
        add_field => {
          "[event.category]" => "authentication"
          "[event.type]" => "start"
          "[event.outcome]" => "failure"
          "[event.kind]" => "alert"
        }
      }
    }

    # Detect sensitive API endpoints
    if [url.path] =~ /access\/ticket|access\/acl|access\/users|access\/roles/ {
      mutate {
        add_field => { "[event.category]" => "iam" }
      }
    }

    if [url.path] =~ /nodes\/.*\/qemu\/.*\/(clone|destroy|migrate)/ {
      mutate {
        add_field => {
          "[event.category]" => "configuration"
          "[event.kind]" => "event"
          "security.alert_level" => "high"
        }
      }
    }

    # Add ECS fields
    mutate {
      add_field => {
        "[observer.type]" => "hypervisor"
        "[observer.vendor]" => "Proxmox"
        "[observer.product]" => "Proxmox VE"
        "[event.module]" => "proxmox"
        "[event.dataset]" => "proxmox.access"
      }
    }
  }
}
```

### 4.3 Correlation Rules for Virtual Infrastructure

Correlation rules combine multiple individual events to detect complex attack patterns:

| Rule Name | Logic | Severity |
|-----------|-------|----------|
| VM Escape Attempt | Guest kernel panic + unexpected hypervisor process + new network connections from host | CRITICAL |
| Unauthorized VM Export | VM clone/export by non-automation account + outside change window | HIGH |
| Credential Stuffing | > 10 failed logins from same IP within 5 minutes across management interfaces | HIGH |
| Cryptomining | VM CPU > 95% sustained + new outbound connections to mining pools | HIGH |
| Lateral Movement | Sequential SSH connections from newly compromised VM to other VMs within minutes | HIGH |
| Data Exfiltration | VM network egress > 3σ above baseline + connection to external IP not in allowlist | HIGH |
| Privilege Escalation | New admin role assignment + immediate VM operations by that user | CRITICAL |
| Alarm Suppression | Multiple alarms disabled + subsequent unauthorized operations | HIGH |

### 4.4 Wazuh Integration

**Wazuh agent installation on Proxmox host:**

```bash
# Install Wazuh agent
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | gpg --dearmor -o /usr/share/keyrings/wazuh.gpg
echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" | \
  tee /etc/apt/sources.list.d/wazuh.list
apt-get update && apt-get install -y wazuh-agent

# Configure agent
cat > /var/ossec/etc/ossec.conf <<'AGENT_CONF'
<ossec_config>
  <client>
    <server>
      <address>wazuh-manager.internal.corp</address>
      <port>1514</port>
      <protocol>tcp</protocol>
    </server>
    <enrollment>
      <enabled>yes</enabled>
      <agent_name>pve01</agent_name>
      <groups>proxmox,hypervisors,production</groups>
    </enrollment>
  </client>

  <!-- File Integrity Monitoring for critical PVE paths -->
  <syscheck>
    <frequency>300</frequency>
    <directories check_all="yes" realtime="yes">/etc/pve</directories>
    <directories check_all="yes" realtime="yes">/etc/network/interfaces</directories>
    <directories check_all="yes" realtime="yes">/etc/corosync</directories>
    <directories check_all="yes">/etc/ssh</directories>
    <directories check_all="yes">/usr/bin,/usr/sbin</directories>
    <directories check_all="yes">/var/lib/pve-cluster</directories>
    <!-- Ignore frequently changing files -->
    <ignore>/etc/pve/.members</ignore>
    <ignore>/etc/pve/.vmlist</ignore>
    <ignore>/etc/pve/nodes/*/lrm_status</ignore>
  </syscheck>

  <!-- Log collection -->
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/syslog</location>
  </localfile>
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/auth.log</location>
  </localfile>
  <localfile>
    <log_format>json</log_format>
    <location>/var/log/pveproxy/access.log</location>
    <label key="log_type">pve_access</label>
  </localfile>
  <localfile>
    <log_format>command</log_format>
    <command>pvesh get /cluster/tasks --limit 20 --output-format json 2>/dev/null</command>
    <frequency>60</frequency>
    <alias>pve_tasks</alias>
  </localfile>
  <localfile>
    <log_format>command</log_format>
    <command>qm list 2>/dev/null | tail -n +2 | awk '{print $1,$2,$3}'</command>
    <frequency>120</frequency>
    <alias>pve_vm_list</alias>
  </localfile>

  <!-- Active Response -->
  <active-response>
    <command>firewall-drop</command>
    <location>local</location>
    <rules_id>100200,100201</rules_id>
    <timeout>3600</timeout>
  </active-response>
</ossec_config>
AGENT_CONF

systemctl enable wazuh-agent && systemctl start wazuh-agent
```

**Custom Wazuh decoders for Proxmox:**

```xml
<!-- /var/ossec/etc/decoders/proxmox_decoders.xml -->
<decoder name="pveproxy-access">
  <parent>web-accesslog</parent>
  <prematch>pveproxy</prematch>
  <regex>^(\S+) - (\S+) \[\S+ \S+\] "(\S+) (\S+) \S+" (\d+) (\d+)</regex>
  <order>srcip,user,protocol,url,id,extra_data</order>
</decoder>

<decoder name="pve-auth-failure">
  <prematch>authentication failure</prematch>
  <regex offset="after_prematch">; logname=(\S*) uid=(\d+) .* rhost=(\S+)\s*user=(\S*)</regex>
  <order>extra_data,id,srcip,user</order>
</decoder>

<decoder name="pve-task">
  <program_name>pvedaemon</program_name>
  <prematch>starting task UPID:</prematch>
  <regex offset="after_prematch">(\S+):(\w+):(\S+):(\S+):(\S+):(\S+):</regex>
  <order>extra_data,action,id,user,status,url</order>
</decoder>

<decoder name="pve-cluster-join">
  <program_name>corosync</program_name>
  <prematch>Member joined:</prematch>
  <regex offset="after_prematch">(\d+)\s+\((\S+)\)</regex>
  <order>id,extra_data</order>
</decoder>

<decoder name="pve-vm-operation">
  <program_name>pvedaemon</program_name>
  <prematch>VM \d+</prematch>
  <regex>VM (\d+) - (\w+): user=(\S+)</regex>
  <order>id,action,user</order>
</decoder>
```

**Custom Wazuh rules for Proxmox:**

```xml
<!-- /var/ossec/etc/rules/proxmox_rules.xml -->
<group name="proxmox,">

  <!-- Authentication Rules -->
  <rule id="100200" level="10">
    <if_sid>5503</if_sid>
    <match>pveproxy</match>
    <description>Proxmox: Multiple authentication failures from same source</description>
    <mitre>
      <id>T1110</id>
    </mitre>
    <group>authentication_failures,pve,</group>
  </rule>

  <rule id="100201" level="12" frequency="10" timeframe="120">
    <if_matched_sid>100200</if_matched_sid>
    <same_source_ip/>
    <description>Proxmox: Brute force attack against management interface</description>
    <mitre>
      <id>T1110.001</id>
    </mitre>
    <group>authentication_failures,pve,brute_force,</group>
  </rule>

  <!-- VM Operation Rules -->
  <rule id="100210" level="8">
    <decoded_as>pve-vm-operation</decoded_as>
    <match>destroy|qmdestroy</match>
    <description>Proxmox: VM destroyed - $(id) by user $(user)</description>
    <mitre>
      <id>T1485</id>
    </mitre>
    <group>pve,vm_operations,</group>
  </rule>

  <rule id="100211" level="10">
    <decoded_as>pve-vm-operation</decoded_as>
    <match>clone|qmclone</match>
    <description>Proxmox: VM cloned - $(id) by user $(user) - potential data exfiltration</description>
    <mitre>
      <id>T1074.001</id>
    </mitre>
    <group>pve,vm_operations,data_exfiltration,</group>
  </rule>

  <rule id="100212" level="12">
    <decoded_as>pve-vm-operation</decoded_as>
    <match>clone|export</match>
    <time>6 pm - 6 am</time>
    <description>Proxmox: VM clone/export outside business hours - HIGH RISK</description>
    <mitre>
      <id>T1074.001</id>
      <id>T1048</id>
    </mitre>
    <group>pve,vm_operations,after_hours,</group>
  </rule>

  <!-- Cluster Security Rules -->
  <rule id="100220" level="14">
    <decoded_as>pve-cluster-join</decoded_as>
    <description>Proxmox: New node joined cluster - verify authorization</description>
    <mitre>
      <id>T1098</id>
    </mitre>
    <group>pve,cluster,critical,</group>
  </rule>

  <!-- File Integrity Rules -->
  <rule id="100230" level="12">
    <if_sid>550,553,554</if_sid>
    <match>/etc/pve/user.cfg|/etc/pve/acl.cfg</match>
    <description>Proxmox: Permission/user configuration modified</description>
    <mitre>
      <id>T1098</id>
      <id>T1078</id>
    </mitre>
    <group>pve,fim,privilege_escalation,</group>
  </rule>

  <rule id="100231" level="14">
    <if_sid>550,553,554</if_sid>
    <match>/etc/pve/corosync.conf|/etc/pve/storage.cfg</match>
    <description>Proxmox: Critical cluster configuration modified</description>
    <mitre>
      <id>T1565.001</id>
    </mitre>
    <group>pve,fim,critical,</group>
  </rule>

  <!-- Network Configuration Changes -->
  <rule id="100240" level="10">
    <if_sid>550,553,554</if_sid>
    <match>/etc/network/interfaces|/etc/pve/sdn</match>
    <description>Proxmox: Network configuration changed - verify authorization</description>
    <mitre>
      <id>T1599</id>
    </mitre>
    <group>pve,fim,network_change,</group>
  </rule>

  <!-- Snapshot Operations -->
  <rule id="100250" level="6">
    <decoded_as>pve-vm-operation</decoded_as>
    <match>snapshot</match>
    <description>Proxmox: VM snapshot operation by $(user)</description>
    <group>pve,vm_operations,</group>
  </rule>

  <rule id="100251" level="10">
    <if_sid>100250</if_sid>
    <time>6 pm - 6 am</time>
    <description>Proxmox: VM snapshot outside business hours - investigate</description>
    <mitre>
      <id>T1074.001</id>
    </mitre>
    <group>pve,vm_operations,after_hours,</group>
  </rule>

</group>
```

### 4.5 Elastic SIEM — Index Templates and Detection Rules

**Index template for Proxmox logs:**

```json
PUT _index_template/proxmox-logs
{
  "index_patterns": ["proxmox-*"],
  "template": {
    "settings": {
      "number_of_shards": 2,
      "number_of_replicas": 1,
      "index.lifecycle.name": "proxmox-ilm-policy",
      "index.lifecycle.rollover_alias": "proxmox-logs"
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "event.action": { "type": "keyword" },
        "event.category": { "type": "keyword" },
        "event.outcome": { "type": "keyword" },
        "event.severity": { "type": "integer" },
        "source.ip": { "type": "ip" },
        "user.name": { "type": "keyword" },
        "host.name": { "type": "keyword" },
        "observer.product": { "type": "keyword" },
        "pve.vm.id": { "type": "integer" },
        "pve.vm.name": { "type": "keyword" },
        "pve.task.type": { "type": "keyword" },
        "pve.task.status": { "type": "keyword" },
        "pve.node": { "type": "keyword" },
        "pve.cluster": { "type": "keyword" },
        "url.path": { "type": "keyword" },
        "http.response.status_code": { "type": "short" },
        "threat.technique.id": { "type": "keyword" },
        "threat.tactic.name": { "type": "keyword" }
      }
    }
  },
  "priority": 200
}
```

**Elastic SIEM detection rules (TOML format for elastic/detection-rules):**

```toml
# proxmox_brute_force.toml
[rule]
name = "Proxmox Management Interface Brute Force"
description = "Detects multiple failed authentication attempts against Proxmox management interfaces within a short timeframe."
risk_score = 73
severity = "high"
type = "threshold"
index = ["proxmox-*", "filebeat-pve-*"]
language = "kuery"
query = '''
event.category: "authentication" AND event.outcome: "failure" AND observer.product: "Proxmox VE"
'''
timestamp_override = "@timestamp"

[rule.threshold]
field = ["source.ip"]
value = 10

[rule.threshold.cardinality]
field = "user.name"
value = 3

[[rule.threat]]
framework = "MITRE ATT&CK"

[[rule.threat.technique]]
id = "T1110"
name = "Brute Force"

[rule.threat.tactic]
id = "TA0006"
name = "Credential Access"
```

```toml
# proxmox_unauthorized_vm_clone.toml
[rule]
name = "Proxmox VM Clone Outside Change Window"
description = "Detects VM clone operations outside of approved change windows, which may indicate data exfiltration."
risk_score = 85
severity = "high"
type = "query"
index = ["proxmox-*"]
language = "kuery"
query = '''
pve.task.type: "qmclone" AND NOT user.name: ("automation@pve" OR "backup@pve") AND NOT @timestamp >= "06:00" AND NOT @timestamp <= "22:00"
'''

[[rule.threat]]
framework = "MITRE ATT&CK"

[[rule.threat.technique]]
id = "T1074"
name = "Data Staged"

[[rule.threat.technique.subtechnique]]
id = "T1074.001"
name = "Local Data Staging"

[rule.threat.tactic]
id = "TA0009"
name = "Collection"
```

**Elasticsearch query for detecting cryptomining indicators:**

```json
GET proxmox-*/_search
{
  "query": {
    "bool": {
      "must": [
        { "range": { "@timestamp": { "gte": "now-1h" } } },
        { "range": { "pve.vm.cpu_percent": { "gte": 95 } } }
      ],
      "should": [
        { "match": { "network.destination.port": "3333" } },
        { "match": { "network.destination.port": "4444" } },
        { "match": { "network.destination.port": "8333" } },
        { "wildcard": { "dns.question.name": "*pool*" } },
        { "wildcard": { "dns.question.name": "*miner*" } },
        { "wildcard": { "dns.question.name": "*xmr*" } }
      ],
      "minimum_should_match": 1
    }
  },
  "aggs": {
    "by_vm": {
      "terms": { "field": "pve.vm.id", "size": 20 },
      "aggs": {
        "avg_cpu": { "avg": { "field": "pve.vm.cpu_percent" } },
        "destinations": {
          "terms": { "field": "destination.ip", "size": 10 }
        }
      }
    }
  }
}
```

### 4.6 Splunk — Technology Add-Ons

**Splunk TA for VMware** provides pre-built:
- Input configurations for vCenter API polling
- CIM-compliant field extractions
- Pre-built dashboards for VMware security

**Custom sourcetype for Proxmox:**

```conf
# $SPLUNK_HOME/etc/apps/TA-proxmox/default/props.conf
[pve:access]
DATETIME_CONFIG = 
TIME_PREFIX = \[
TIME_FORMAT = %d/%b/%Y:%H:%M:%S %z
MAX_TIMESTAMP_LOOKAHEAD = 40
SHOULD_LINEMERGE = false
LINE_BREAKER = ([\r\n]+)
category = Web
description = Proxmox VE API access logs
EXTRACT-pve_access = ^(?P<src_ip>\d+\.\d+\.\d+\.\d+)\s+-\s+(?P<user>[^\s]+)\s+\[(?P<timestamp>[^\]]+)\]\s+"(?P<http_method>\w+)\s+(?P<uri_path>[^\s]+)\s+[^"]+"\s+(?P<status>\d+)\s+(?P<bytes>\d+)

[pve:task]
DATETIME_CONFIG =
TIME_FORMAT = %s
SHOULD_LINEMERGE = true
LINE_BREAKER = ([\r\n]+)UPID
EXTRACT-pve_task = UPID:(?P<node>[^:]+):(?P<pid>[^:]+):(?P<pstart>[^:]+):(?P<starttime>[^:]+):(?P<tasktype>[^:]+):(?P<taskid>[^:]+):(?P<user>[^:]+):
category = Virtualization

[pve:auth]
SHOULD_LINEMERGE = false
LINE_BREAKER = ([\r\n]+)
TIME_FORMAT = %b %d %H:%M:%S
category = Authentication
```

```conf
# $SPLUNK_HOME/etc/apps/TA-proxmox/default/transforms.conf
[pve_task_type_lookup]
filename = pve_task_types.csv
match_type = WILDCARD(task_type)
```

---

## 5. Threat Detection Rules

### 5.1 Unauthorized VM Operations

Detection of VM operations that occur outside approved change windows or by unauthorized users represents one of the highest-value detection capabilities for virtual infrastructure.

**Rule: VM Creation Outside Change Window**

```yaml
# Wazuh rule (XML representation as YAML for clarity)
rule_id: 100300
level: 12
description: "VM created outside approved change window (Mon-Fri 09:00-17:00)"
match_criteria:
  - action: "qmcreate|VmCreatedEvent"
  - time_exclusion: "Mon-Fri 09:00-17:00"
  - user_exclusion: ["automation@pve", "terraform@pve"]
mitre_techniques: ["T1578.002"]
response: "Alert SOC + capture VM configuration snapshot"
```

**Rule: VM Export/Download Detection**

```yaml
rule_id: 100301
level: 14
description: "VM disk exported or downloaded - potential data exfiltration"
match_criteria:
  - action: "vzdump|VmExportedEvent|download"
  - uri_pattern: "/api2/json/nodes/.*/vzdump|/api2/json/nodes/.*/storage/.*/download"
  - user_exclusion: ["backup-service@pve"]
mitre_techniques: ["T1048.002", "T1567"]
response: "Alert SOC immediately + block network egress from source"
```

### 5.2 Privilege Escalation Detection

```xml
<!-- Wazuh rule for detecting privilege escalation in Proxmox -->
<rule id="100310" level="14">
  <if_sid>100230</if_sid>
  <match>Administrator|PVEAdmin</match>
  <description>Proxmox: Administrative role assigned - privilege escalation risk</description>
  <mitre>
    <id>T1078.004</id>
    <id>T1098</id>
  </mitre>
  <group>pve,privilege_escalation,critical,</group>
</rule>

<rule id="100311" level="12">
  <if_sid>100310</if_sid>
  <if_fts/>
  <description>Proxmox: First-time admin role assignment for user - verify authorization</description>
  <group>pve,privilege_escalation,</group>
</rule>

<!-- Detect role creation followed by immediate VM operations -->
<rule id="100312" level="14" frequency="2" timeframe="300">
  <if_matched_sid>100310</if_matched_sid>
  <same_user/>
  <description>Proxmox: User granted admin role and immediately performed VM operations</description>
  <mitre>
    <id>T1078</id>
    <id>T1098</id>
  </mitre>
  <group>pve,privilege_escalation,lateral_movement,critical,</group>
</rule>
```

### 5.3 Brute Force Against Management Interfaces

**Prometheus alerting rule:**

```yaml
# /etc/prometheus/rules/pve-security.yml
groups:
  - name: proxmox_security
    rules:
      - alert: PVEBruteForceDetected
        expr: |
          rate(pve_security_failed_logins[5m]) > 2
        for: 2m
        labels:
          severity: high
          team: security
        annotations:
          summary: "Brute force attack detected on {{ $labels.instance }}"
          description: |
            More than 10 failed login attempts per 5 minutes on Proxmox management interface.
            Instance: {{ $labels.instance }}
            Current rate: {{ $value }} failures/second
          runbook_url: "https://wiki.internal.corp/runbooks/pve-brute-force"

      - alert: PVESSHBruteForce
        expr: |
          increase(node_systemd_unit_state{name="sshd.service",state="failed"}[5m]) > 0
          and
          rate(node_textfile_pve_security_failed_logins[5m]) > 1
        for: 1m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "SSH brute force combined with API brute force on {{ $labels.instance }}"
          description: "Coordinated attack targeting both SSH and API interfaces."
```

### 5.4 Anomalous VM Behavior

**Cryptomining detection (Prometheus + alerting):**

```yaml
      - alert: PVECryptominingIndicator
        expr: |
          (
            pve_guest_info{status="running"} == 1
            and
            avg_over_time(pve_cpu_usage_ratio[30m]) > 0.95
          )
          unless
          (
            pve_guest_info{name=~".*compute.*|.*batch.*|.*render.*"}
          )
        for: 30m
        labels:
          severity: high
          team: security
        annotations:
          summary: "Possible cryptomining in VM {{ $labels.id }} ({{ $labels.name }})"
          description: |
            VM {{ $labels.name }} (ID: {{ $labels.id }}) on node {{ $labels.node }}
            has sustained >95% CPU usage for 30+ minutes.
            Not in compute/batch exclusion list.
            Investigate for unauthorized cryptocurrency mining.

      - alert: PVEDataExfiltrationIndicator
        expr: |
          (
            rate(pve_guest_net_out_bytes[5m]) > 
            (avg_over_time(pve_guest_net_out_bytes[7d]) + 3 * stddev_over_time(pve_guest_net_out_bytes[7d]))
          )
          and
          rate(pve_guest_net_out_bytes[5m]) > 10485760
        for: 10m
        labels:
          severity: high
          team: security
        annotations:
          summary: "Unusual network egress from VM {{ $labels.id }} ({{ $labels.name }})"
          description: |
            VM {{ $labels.name }} network output exceeds 3 standard deviations above 7-day average.
            Current rate: {{ $value | humanize }}B/s
            Possible data exfiltration. Investigate destination IPs.
```

### 5.5 Snapshot Operations Outside Policy

```xml
<!-- Wazuh rule -->
<rule id="100320" level="10">
  <decoded_as>pve-vm-operation</decoded_as>
  <match>snapshot</match>
  <regex>user=(?!backup@pve|automation@pve)</regex>
  <description>Proxmox: Manual snapshot by non-service account $(user)</description>
  <mitre>
    <id>T1074.001</id>
  </mitre>
  <group>pve,vm_operations,snapshot,</group>
</rule>

<!-- Excessive snapshots (possible pre-exfiltration staging) -->
<rule id="100321" level="12" frequency="5" timeframe="600">
  <if_matched_sid>100320</if_matched_sid>
  <same_user/>
  <description>Proxmox: User creating excessive snapshots - possible data staging</description>
  <mitre>
    <id>T1074.001</id>
    <id>T1005</id>
  </mitre>
  <group>pve,vm_operations,data_staging,</group>
</rule>
```

### 5.6 Configuration Changes

**Firewall rule modification detection:**

```xml
<rule id="100330" level="10">
  <if_sid>550,553,554</if_sid>
  <match>/etc/pve/firewall|/etc/pve/nodes/.*/host.fw</match>
  <description>Proxmox: Firewall configuration modified</description>
  <mitre>
    <id>T1562.004</id>
  </mitre>
  <group>pve,fim,firewall_change,</group>
</rule>

<!-- Firewall disabled entirely -->
<rule id="100331" level="14">
  <if_sid>100330</if_sid>
  <match>enable: 0|enable:0</match>
  <description>Proxmox: Firewall DISABLED - critical security control removed</description>
  <mitre>
    <id>T1562.004</id>
  </mitre>
  <group>pve,fim,firewall_disabled,critical,</group>
</rule>
```

### 5.7 Lateral Movement Between VMs

Detecting lateral movement in virtual environments requires correlating events across multiple VMs and the hypervisor layer:

```json
// Elasticsearch query: detect sequential connections from compromised VM
GET proxmox-*,filebeat-*/_search
{
  "query": {
    "bool": {
      "must": [
        { "range": { "@timestamp": { "gte": "now-1h" } } },
        { "term": { "event.category": "network_traffic" } },
        { "terms": { "destination.port": [22, 3389, 5985, 445, 135] } }
      ],
      "filter": [
        {
          "script": {
            "script": {
              "source": "doc['source.ip'].value.startsWith('10.10.')",
              "lang": "painless"
            }
          }
        }
      ]
    }
  },
  "aggs": {
    "by_source": {
      "terms": { "field": "source.ip", "size": 50 },
      "aggs": {
        "unique_destinations": {
          "cardinality": { "field": "destination.ip" }
        },
        "destination_list": {
          "terms": { "field": "destination.ip", "size": 20 }
        },
        "time_span": {
          "stats": { "field": "@timestamp" }
        }
      }
    }
  }
}
```

**Alert logic:** If a single source IP connects to > 5 unique internal IPs on management ports within 30 minutes, and that source IP is a VM (not a jump host), flag as lateral movement.

---

## 6. Network Monitoring in Virtual Environments

### 6.1 Virtual Switch Monitoring

**Detecting promiscuous mode activation (ESXi):**

```powershell
# PowerCLI: Check for VMs with promiscuous mode enabled
Get-VirtualSwitch | Get-SecurityPolicy | Where-Object {
    $_.AllowPromiscuous -eq $true
} | ForEach-Object {
    Write-Warning "ALERT: Promiscuous mode enabled on vSwitch: $($_.VirtualSwitch.Name)"
}

# Check port groups
Get-VDPortgroup | Get-VDSecurityPolicy | Where-Object {
    $_.AllowPromiscuous -eq $true -or
    $_.MacChanges -eq $true -or
    $_.ForgedTransmits -eq $true
} | Select-Object @{N='PortGroup';E={$_.VDPortgroup.Name}},
    AllowPromiscuous, MacChanges, ForgedTransmits
```

**Proxmox bridge monitoring:**

```bash
#!/bin/bash
# /usr/local/bin/pve-bridge-security-check.sh

# Check for interfaces in promiscuous mode
for iface in $(ls /sys/class/net/); do
    flags=$(cat /sys/class/net/$iface/flags 2>/dev/null)
    if [ -n "$flags" ]; then
        # IFF_PROMISC = 0x100
        if (( (flags & 0x100) != 0 )); then
            logger -t "pve-security" -p auth.warning \
              "ALERT: Interface $iface is in promiscuous mode"
        fi
    fi
done

# Check for unexpected bridge members
for bridge in $(brctl show 2>/dev/null | grep -oP '^vmbr\d+'); do
    members=$(brctl show $bridge | tail -n +2 | awk '{print $NF}')
    for member in $members; do
        # Verify each member is a known tap/veth device
        if [[ ! "$member" =~ ^(tap|veth|fwbr|fwpr|fwln|eth|bond|eno) ]]; then
            logger -t "pve-security" -p auth.crit \
              "CRITICAL: Unexpected interface '$member' on bridge '$bridge'"
        fi
    done
done

# Detect new bridge creation
current_bridges=$(brctl show 2>/dev/null | grep -oP '^\w+' | sort)
if [ -f /var/lib/pve-security/known_bridges ]; then
    new_bridges=$(comm -13 /var/lib/pve-security/known_bridges <(echo "$current_bridges"))
    if [ -n "$new_bridges" ]; then
        logger -t "pve-security" -p auth.crit \
          "CRITICAL: New bridge(s) detected: $new_bridges"
    fi
fi
echo "$current_bridges" > /var/lib/pve-security/known_bridges
```

### 6.2 Traffic Analysis — NetFlow/sFlow

**OVS (Open vSwitch) NetFlow/sFlow configuration for Proxmox:**

```bash
# Enable sFlow on OVS bridge (if using OVS instead of Linux bridge)
ovs-vsctl -- --id=@sflow create sflow agent=eth0 \
  target=\"10.10.30.60:6343\" header=128 \
  sampling=256 polling=10 -- set bridge br0 sflow=@sflow

# Enable IPFIX (NetFlow v10) for more detailed flow data
ovs-vsctl -- --id=@ipfix create IPFIX targets=\"10.10.30.60:4739\" \
  obs_domain_id=1 obs_point_id=1 cache_active_timeout=60 \
  -- set Bridge br0 ipfix=@ipfix
```

**Linux bridge traffic monitoring with tc and eBPF:**

```bash
# Mirror traffic from vmbr0 to monitoring interface
tc qdisc add dev vmbr0 ingress
tc filter add dev vmbr0 parent ffff: protocol all u32 match u32 0 0 \
  action mirred egress mirror dev mon0

# Or use nftables for more selective mirroring
nft add table netdev mirror
nft add chain netdev mirror ingress { type filter hook ingress device vmbr0 priority 0\; }
nft add rule netdev mirror ingress dup to mon0
```

### 6.3 East-West Traffic Monitoring Challenges

East-west (VM-to-VM) traffic on the same host never traverses the physical network — it stays within the virtual switch. This creates a critical visibility gap.

**Solutions:**

| Approach | Pros | Cons |
|----------|------|------|
| Port mirroring on vSwitch | Full packet visibility | Performance impact, storage cost |
| OVS with sFlow/IPFIX | Metadata-only, low overhead | Limited payload inspection |
| Agent-based (guest EDR) | Application-layer visibility | Requires agent in every VM |
| eBPF on hypervisor bridge | Low overhead, flexible filtering | Requires kernel support, complex |
| SDN controller integration | Centralized policy + monitoring | Architectural complexity |

**eBPF-based flow monitoring (modern approach):**

```bash
# Using bpftrace to monitor inter-VM traffic on Linux bridge
bpftrace -e '
kprobe:br_forward {
    $skb = (struct sk_buff *)arg1;
    $iph = (struct iphdr *)($skb->head + $skb->network_header);
    printf("BRIDGE_FWD: %s -> %s proto=%d len=%d\n",
        ntop(AF_INET, $iph->saddr),
        ntop(AF_INET, $iph->daddr),
        $iph->protocol,
        $skb->len);
}' > /var/log/bridge-flows.log &
```

### 6.4 Encrypted Traffic Analysis — JA3/JA4 Fingerprinting

With increasing TLS adoption, payload inspection becomes impossible. JA3/JA4 fingerprinting identifies client applications by their TLS ClientHello characteristics.

**Zeek (formerly Bro) configuration for JA3 on virtual bridge:**

```bash
# Install Zeek with JA3 plugin
# /etc/zeek/local.zeek
@load protocols/ssl
@load ja3

redef LogAscii::use_json = T;
redef Site::local_nets += { 10.10.0.0/16 };

# Monitor virtual bridge interface
# zeek -i vmbr0 local.zeek
```

**JA3 fingerprint alerting:**

Known malicious JA3 fingerprints (examples — maintain updated threat intel feed):

```yaml
# Known bad JA3 hashes (Cobalt Strike, Metasploit, etc.)
malicious_ja3:
  - hash: "72a589da586844d7f0818ce684948eea"
    description: "Cobalt Strike default"
  - hash: "a0e9f5d64349fb13191bc781f81f42e1"
    description: "Metasploit Meterpreter"
  - hash: "e7d705a3286e19ea42f587b344ee6865"
    description: "Trickbot"
```

### 6.5 Micro-Segmentation Monitoring

Verifying that micro-segmentation policies are being enforced:

```bash
#!/bin/bash
# /usr/local/bin/pve-microseg-verify.sh
# Verify Proxmox SDN/firewall micro-segmentation policy enforcement

# Expected policy: Web tier VMs can only reach App tier on port 8080
# App tier VMs can only reach DB tier on port 5432

WEB_TIER="10.10.10.0/24"
APP_TIER="10.10.20.0/24"
DB_TIER="10.10.30.0/24"

# Test from monitoring host (must be in management network)
# Check for policy violations in flow data
violations=$(grep -c "SRC=$WEB_TIER.*DST=$DB_TIER" /var/log/netflows/current.log)

if [ "$violations" -gt 0 ]; then
    logger -t "pve-security" -p auth.crit \
      "POLICY VIOLATION: $violations flows from Web tier directly to DB tier"
fi

# Verify firewall rules are still active on all VMs in each tier
for vmid in $(pvesh get /cluster/resources --type vm --output-format json | \
  jq -r '.[] | select(.status=="running") | .vmid'); do
    fw_status=$(pvesh get /nodes/$(hostname)/qemu/$vmid/firewall/options --output-format json 2>/dev/null | \
      jq -r '.enable // 0')
    if [ "$fw_status" != "1" ]; then
        logger -t "pve-security" -p auth.warning \
          "WARNING: Firewall disabled on VM $vmid"
    fi
done
```

### 6.6 Detecting VLAN Hopping and ARP Spoofing

**VLAN hopping detection:**

```bash
# Detect double-tagged frames (802.1Q-in-802.1Q VLAN hopping)
tcpdump -i vmbr0 -nn 'vlan and vlan' -c 1 && \
  logger -t "pve-security" -p auth.crit "CRITICAL: Double-tagged VLAN frame detected - VLAN hopping attempt"

# Monitor for DTP frames (should never appear in virtual environment)
tcpdump -i vmbr0 -nn 'ether[20:2] == 0x2004' -c 1 && \
  logger -t "pve-security" -p auth.crit "CRITICAL: DTP frame detected on virtual bridge"
```

**ARP spoofing detection:**

```bash
#!/bin/bash
# /usr/local/bin/pve-arp-monitor.sh
# Detect ARP anomalies on virtual bridges

KNOWN_MACS="/etc/pve-security/known_mac_ip.conf"
# Format: MAC IP VMID

arp -an | while read line; do
    ip=$(echo "$line" | grep -oP '\(\K[^)]+')
    mac=$(echo "$line" | grep -oP '([0-9a-f]{2}:){5}[0-9a-f]{2}')
    iface=$(echo "$line" | awk '{print $NF}')
    
    if [ -n "$mac" ] && [ -n "$ip" ]; then
        expected_mac=$(grep "$ip" "$KNOWN_MACS" 2>/dev/null | awk '{print $1}')
        if [ -n "$expected_mac" ] && [ "$mac" != "$expected_mac" ]; then
            logger -t "pve-security" -p auth.crit \
              "ARP SPOOFING: IP $ip has MAC $mac, expected $expected_mac on $iface"
        fi
    fi
done
```

---

## 7. Storage and Backup Monitoring

### 7.1 Storage Anomaly Detection

**Unusual I/O pattern detection (possible ransomware):**

```yaml
# Prometheus alerting rules
groups:
  - name: storage_security
    rules:
      - alert: StorageRansomwareIndicator
        expr: |
          (
            rate(node_disk_writes_completed_total[5m]) > 
            2 * avg_over_time(rate(node_disk_writes_completed_total[5m])[7d:5m])
          )
          and
          (
            rate(node_disk_read_bytes_total[5m]) > 
            1.5 * avg_over_time(rate(node_disk_read_bytes_total[5m])[7d:5m])
          )
          and
          (
            node_disk_io_time_weighted_seconds_total > 0.8
          )
        for: 5m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Possible ransomware activity on {{ $labels.instance }} device {{ $labels.device }}"
          description: |
            Storage device showing pattern consistent with ransomware:
            - Elevated write operations (2x above 7-day average)
            - Elevated read operations (read-encrypt-write pattern)
            - High I/O saturation (>80%)
            Immediate investigation required.

      - alert: StorageCapacityAnomaly
        expr: |
          (
            deriv(node_filesystem_avail_bytes[1h]) < -1073741824
          )
          and
          (
            node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.2
          )
        for: 15m
        labels:
          severity: high
          team: security
        annotations:
          summary: "Rapid storage consumption on {{ $labels.instance }}:{{ $labels.mountpoint }}"
          description: |
            Storage depleting at >1GB/hour with <20% remaining.
            Could indicate: data staging for exfiltration, ransomware,
            or unauthorized VM provisioning consuming disk.
```

### 7.2 Backup Integrity Monitoring

```bash
#!/bin/bash
# /usr/local/bin/pve-backup-integrity.sh
# Monitor backup integrity and detect tampering

BACKUP_STORE="/mnt/pbs-backups"
INTEGRITY_DB="/var/lib/pve-security/backup_integrity.db"
ALERT_CMD="logger -t pve-security -p auth.crit"

# Check for missing scheduled backups
expected_vms=$(pvesh get /cluster/resources --type vm --output-format json | \
  jq -r '.[] | select(.status=="running") | .vmid' | sort)

today=$(date +%Y-%m-%d)
backed_up_today=$(find "$BACKUP_STORE" -name "*.vma*" -newer /tmp/today_marker -type f | \
  grep -oP 'qemu-\K\d+' | sort -u)

missing=$(comm -23 <(echo "$expected_vms") <(echo "$backed_up_today"))
if [ -n "$missing" ]; then
    $ALERT_CMD "BACKUP MISSING: VMs without today's backup: $missing"
fi

# Verify backup checksums haven't been modified
find "$BACKUP_STORE" -name "*.vma.zst" -mtime -1 | while read backup_file; do
    current_hash=$(sha256sum "$backup_file" | awk '{print $1}')
    stored_hash=$(grep "$backup_file" "$INTEGRITY_DB" | awk '{print $1}')
    
    if [ -n "$stored_hash" ] && [ "$current_hash" != "$stored_hash" ]; then
        $ALERT_CMD "BACKUP TAMPERED: $backup_file hash mismatch! Expected=$stored_hash Got=$current_hash"
    fi
    
    # Update integrity database
    echo "$current_hash $backup_file $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$INTEGRITY_DB"
done

# Check for unexpected backup deletions
yesterday_count=$(grep "$(date -d yesterday +%Y-%m-%d)" "$INTEGRITY_DB" | wc -l)
today_count=$(find "$BACKUP_STORE" -name "*.vma*" | wc -l)
if [ "$today_count" -lt "$((yesterday_count - 5))" ]; then
    $ALERT_CMD "BACKUP DELETION: Significant backup count decrease. Yesterday=$yesterday_count Today=$today_count"
fi
```

### 7.3 Ransomware Indicators in Storage

**Entropy-based detection:**

```python
#!/usr/bin/env python3
"""
/usr/local/bin/entropy_monitor.py
Monitor file entropy changes on backup storage to detect ransomware encryption.
High entropy (close to 8.0 for byte-level) indicates encrypted/compressed content.
Sudden entropy increase across many files = ransomware indicator.
"""

import os
import math
import json
import time
import logging
from pathlib import Path
from collections import Counter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger('entropy_monitor')

WATCH_PATH = "/mnt/shared-storage"
STATE_FILE = "/var/lib/pve-security/entropy_state.json"
ENTROPY_THRESHOLD = 7.8  # Near-maximum entropy indicates encryption
ALERT_PERCENTAGE = 20     # Alert if >20% of files show entropy increase


def calculate_entropy(filepath: str, sample_size: int = 65536) -> float:
    """Calculate Shannon entropy of file (sample first N bytes)."""
    try:
        with open(filepath, 'rb') as f:
            data = f.read(sample_size)
    except (PermissionError, FileNotFoundError):
        return -1.0

    if not data:
        return 0.0

    byte_counts = Counter(data)
    total = len(data)
    entropy = -sum(
        (count / total) * math.log2(count / total)
        for count in byte_counts.values()
        if count > 0
    )
    return entropy


def scan_directory(path: str) -> dict:
    """Scan directory and compute entropy for each file."""
    results = {}
    for root, _, files in os.walk(path):
        for fname in files[:1000]:  # Limit to prevent resource exhaustion
            fpath = os.path.join(root, fname)
            if os.path.isfile(fpath) and os.path.getsize(fpath) > 1024:
                results[fpath] = calculate_entropy(fpath)
    return results


def compare_states(previous: dict, current: dict) -> list:
    """Find files with significant entropy increase."""
    alerts = []
    for fpath, curr_entropy in current.items():
        prev_entropy = previous.get(fpath, -1)
        if prev_entropy >= 0 and curr_entropy > ENTROPY_THRESHOLD:
            if curr_entropy - prev_entropy > 1.0:
                alerts.append({
                    'file': fpath,
                    'previous_entropy': prev_entropy,
                    'current_entropy': curr_entropy,
                    'delta': curr_entropy - prev_entropy
                })
    return alerts


def main():
    # Load previous state
    previous_state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            previous_state = json.load(f)

    # Current scan
    current_state = scan_directory(WATCH_PATH)

    # Compare
    alerts = compare_states(previous_state, current_state)
    alert_ratio = len(alerts) / max(len(current_state), 1) * 100

    if alert_ratio > ALERT_PERCENTAGE:
        logger.critical(
            f"RANSOMWARE INDICATOR: {len(alerts)} files ({alert_ratio:.1f}%) "
            f"show sudden entropy increase above {ENTROPY_THRESHOLD}"
        )
        # Syslog for SIEM pickup
        os.system(
            f'logger -t pve-security -p auth.crit '
            f'"RANSOMWARE: {len(alerts)} files with entropy spike"'
        )
    elif alerts:
        logger.warning(
            f"Entropy anomaly: {len(alerts)} files affected ({alert_ratio:.1f}%)"
        )

    # Save current state
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(current_state, f)


if __name__ == '__main__':
    main()
```

### 7.4 Replication Monitoring

```yaml
# Prometheus rules for replication monitoring
groups:
  - name: replication_security
    rules:
      - alert: ReplicationLagExcessive
        expr: pve_replication_duration_seconds > 3600
        for: 5m
        labels:
          severity: high
        annotations:
          summary: "Replication lag >1h on {{ $labels.instance }}"
          description: "Excessive replication lag may indicate tampering or resource contention."

      - alert: ReplicationFailure
        expr: pve_replication_last_sync_status != 1
        for: 30m
        labels:
          severity: high
        annotations:
          summary: "Replication failure for VM {{ $labels.vmid }} on {{ $labels.instance }}"
          description: "Replication has been failing for 30+ minutes. Verify backup integrity."

      - alert: UnauthorizedReplicationTarget
        expr: |
          pve_replication_target_node != ""
          unless on(vmid)
          pve_replication_target_node{target_node=~"pve01|pve02|pve03"}
        labels:
          severity: critical
        annotations:
          summary: "VM {{ $labels.vmid }} replicating to unauthorized target {{ $labels.target_node }}"
```

### 7.5 Data Exfiltration Through Storage Channels

Attackers may use storage replication, backup exports, or shared storage as exfiltration channels:

**Detection strategies:**

1. **Monitor NFS/iSCSI mount changes** — New storage mounts indicate potential staging.
2. **Track vzdump to unexpected destinations** — Backups going to non-approved storage.
3. **Monitor Ceph client connections** — Unauthorized clients accessing shared storage.

```bash
#!/bin/bash
# Monitor for unauthorized storage access

# Check for new NFS/iSCSI/Ceph connections
current_mounts=$(mount | grep -E "nfs|iscsi|ceph|rbd" | sort)
known_mounts=$(cat /var/lib/pve-security/known_mounts 2>/dev/null)

new_mounts=$(comm -13 <(echo "$known_mounts") <(echo "$current_mounts"))
if [ -n "$new_mounts" ]; then
    logger -t "pve-security" -p auth.crit \
      "ALERT: New storage mount detected: $new_mounts"
fi
echo "$current_mounts" > /var/lib/pve-security/known_mounts

# Check for unauthorized Ceph clients
if command -v ceph &>/dev/null; then
    authorized_clients=("pve01" "pve02" "pve03" "pbs01")
    ceph_clients=$(ceph status --format json 2>/dev/null | jq -r '.osdmap.osdmap.num_in_osds // 0')
    # Additional Ceph auth audit
    ceph auth ls 2>/dev/null | grep "client\." | while read client; do
        client_name=$(echo "$client" | grep -oP 'client\.\K\S+')
        if [[ ! " ${authorized_clients[*]} " =~ " $client_name " ]]; then
            logger -t "pve-security" -p auth.warning \
              "WARNING: Unauthorized Ceph client: $client_name"
        fi
    done
fi
```

---

## 8. Alerting and Response

### 8.1 Alert Severity Classification

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| P1 — Critical | Active compromise, data loss imminent | < 15 minutes | VM escape detected, admin credentials compromised, ransomware active |
| P2 — High | Likely attack in progress | < 1 hour | Brute force succeeding, unauthorized VM export, privilege escalation |
| P3 — Medium | Suspicious activity, possible attack | < 4 hours | Failed login spikes, unusual VM operations, configuration changes |
| P4 — Low | Informational, policy violation | < 24 hours | Missing backups, minor policy deviation, informational anomalies |
| P5 — Info | Audit trail, no action | Next business day | Routine operations by authorized users, compliance check results |

### 8.2 Alert Fatigue Reduction

Alert fatigue is the primary reason security monitoring fails operationally. Apply these techniques systematically:

**Deduplication:**

```yaml
# Wazuh: Suppress duplicate alerts using same_source_ip and frequency
<rule id="100400" level="0">
  <if_sid>100200</if_sid>
  <same_source_ip/>
  <options>alert_by_email</options>
  <check_if_ignored>yes</check_if_ignored>
  <description>Deduplicated: Same source repeated auth failure</description>
</rule>
```

**Correlation-based suppression:**

```yaml
# AlertManager inhibition rules
inhibit_rules:
  # If host is down, suppress all other alerts from that host
  - source_match:
      alertname: NodeDown
    target_match_re:
      instance: '{{ $labels.instance }}'
    equal: ['instance']

  # If maintenance window active, suppress medium/low alerts
  - source_match:
      alertname: MaintenanceWindow
      severity: info
    target_match_re:
      severity: 'medium|low|info'
    equal: ['cluster']
```

**Time-based suppression:**

```yaml
# AlertManager route with time-based silencing
route:
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true
    - match:
        severity: high
      receiver: 'slack-security'
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 1h
    - match:
        severity: medium
      receiver: 'email-security'
      group_wait: 5m
      group_interval: 30m
      repeat_interval: 4h
      active_time_intervals:
        - business_hours
```

### 8.3 Notification Channels

**AlertManager configuration:**

```yaml
# /etc/alertmanager/alertmanager.yml
global:
  resolve_timeout: 5m
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'
  slack_api_url: 'https://hooks.slack.com/services/XXX/YYY/ZZZ'

receivers:
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: 'YOUR_PD_SERVICE_KEY'
        severity: 'critical'
        description: '{{ .CommonAnnotations.summary }}'
        details:
          firing: '{{ template "pagerduty.default.description" . }}'
          num_firing: '{{ .Alerts.Firing | len }}'

  - name: 'slack-security'
    slack_configs:
      - channel: '#security-alerts'
        title: '{{ .CommonAnnotations.summary }}'
        text: |
          *Alert:* {{ .CommonLabels.alertname }}
          *Severity:* {{ .CommonLabels.severity }}
          *Instance:* {{ .CommonLabels.instance }}
          *Description:* {{ .CommonAnnotations.description }}
          *Runbook:* {{ .CommonAnnotations.runbook_url }}
        send_resolved: true
        actions:
          - type: button
            text: 'Acknowledge'
            url: '{{ .ExternalURL }}/#/alerts?filter={{ .CommonLabels.alertname }}'
          - type: button
            text: 'Runbook'
            url: '{{ .CommonAnnotations.runbook_url }}'

  - name: 'email-security'
    email_configs:
      - to: 'security-team@internal.corp'
        from: 'monitoring@internal.corp'
        smarthost: 'smtp.internal.corp:587'
        auth_username: 'monitoring'
        auth_password_file: '/etc/alertmanager/smtp_password'
        require_tls: true
        headers:
          Subject: '[{{ .CommonLabels.severity | toUpper }}] {{ .CommonAnnotations.summary }}'

  - name: 'opsgenie'
    opsgenie_configs:
      - api_key: 'YOUR_OPSGENIE_KEY'
        message: '{{ .CommonAnnotations.summary }}'
        priority: '{{ if eq .CommonLabels.severity "critical" }}P1{{ else if eq .CommonLabels.severity "high" }}P2{{ else }}P3{{ end }}'
        tags: 'proxmox,security,{{ .CommonLabels.alertname }}'

time_intervals:
  - name: business_hours
    time_intervals:
      - weekdays: ['monday:friday']
        times:
          - start_time: '08:00'
            end_time: '18:00'
```

### 8.4 Automated Response Actions

**VM Isolation (Wazuh active response):**

```bash
#!/bin/bash
# /var/ossec/active-response/bin/isolate-vm.sh
# Automated VM isolation upon detection of compromise

LOCAL=$(dirname $0)
VMID="$1"
NODE=$(hostname)
LOG="/var/ossec/logs/active-responses.log"

log() {
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) isolate-vm: $*" >> "$LOG"
}

# Input validation
if ! [[ "$VMID" =~ ^[0-9]+$ ]]; then
    log "ERROR: Invalid VMID: $VMID"
    exit 1
fi

log "START: Isolating VM $VMID on node $NODE"

# Step 1: Snapshot VM state before isolation (evidence preservation)
pvesh create /nodes/$NODE/qemu/$VMID/snapshot \
  -snapname "security-isolate-$(date +%Y%m%d%H%M%S)" \
  -description "Automated security isolation snapshot" \
  -vmstate 1 2>> "$LOG"
log "Snapshot created for VM $VMID"

# Step 2: Disconnect network (set firewall to block all)
pvesh set /nodes/$NODE/qemu/$VMID/firewall/options \
  -enable 1 -policy_in DROP -policy_out DROP 2>> "$LOG"

# Step 3: Remove all firewall rules that might allow traffic
pvesh get /nodes/$NODE/qemu/$VMID/firewall/rules --output-format json | \
  jq -r '.[].pos' | while read pos; do
    pvesh delete /nodes/$NODE/qemu/$VMID/firewall/rules/$pos 2>> "$LOG"
done

# Step 4: Add explicit deny-all rules
pvesh create /nodes/$NODE/qemu/$VMID/firewall/rules \
  -action DROP -type in -enable 1 -comment "Security isolation - all inbound blocked" 2>> "$LOG"
pvesh create /nodes/$NODE/qemu/$VMID/firewall/rules \
  -action DROP -type out -enable 1 -comment "Security isolation - all outbound blocked" 2>> "$LOG"

log "COMPLETE: VM $VMID isolated. Network blocked, snapshot preserved."

# Step 5: Notify security team
curl -s -X POST "https://hooks.slack.com/services/XXX/YYY/ZZZ" \
  -H 'Content-Type: application/json' \
  -d "{\"text\":\"AUTOMATED RESPONSE: VM $VMID on $NODE has been isolated due to security alert. Snapshot taken. Manual investigation required.\"}"
```

**Account lockout (Proxmox-specific):**

```bash
#!/bin/bash
# /var/ossec/active-response/bin/lockout-pve-user.sh
# Lock Proxmox user account after brute force detection

USER="$1"
LOG="/var/ossec/logs/active-responses.log"

log() {
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) lockout-pve-user: $*" >> "$LOG"
}

# Validate user format (user@realm)
if ! [[ "$USER" =~ ^[a-zA-Z0-9._-]+@[a-zA-Z]+$ ]]; then
    log "ERROR: Invalid user format: $USER"
    exit 1
fi

# Never lock out root@pam (prevent self-lockout)
if [ "$USER" == "root@pam" ]; then
    log "REFUSED: Will not lock root@pam"
    exit 1
fi

log "Locking account: $USER"
pveum user modify "$USER" -enable 0 2>> "$LOG"

# Expire all active tickets for this user
# (Implementation depends on version - API call to invalidate sessions)

log "Account $USER locked. Manual unlock required."
```

### 8.5 Runbook Integration

**Automated runbook execution with Wazuh:**

```xml
<!-- /var/ossec/etc/ossec.conf - Active Response section -->
<active-response>
  <command>isolate-vm</command>
  <location>local</location>
  <rules_id>100220,100312</rules_id>
  <timeout>0</timeout>
</active-response>

<active-response>
  <command>lockout-pve-user</command>
  <location>local</location>
  <rules_id>100201</rules_id>
  <timeout>3600</timeout>
</active-response>

<command>
  <name>isolate-vm</name>
  <executable>isolate-vm.sh</executable>
  <extra_args>$VMID</extra_args>
  <timeout_allowed>yes</timeout_allowed>
</command>

<command>
  <name>lockout-pve-user</name>
  <executable>lockout-pve-user.sh</executable>
  <extra_args>$USER</extra_args>
  <timeout_allowed>yes</timeout_allowed>
</command>
```

### 8.6 Escalation Procedures

```
┌─────────────────────────────────────────────────────────────────┐
│                    ESCALATION MATRIX                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  P1 (Critical) - 0 min                                          │
│  ├── Automated: VM isolation + snapshot                         │
│  ├── Alert: PagerDuty (on-call security engineer)              │
│  ├── +15 min no ack: Escalate to security team lead            │
│  ├── +30 min no ack: Escalate to CISO                          │
│  └── +60 min: Invoke incident response plan                    │
│                                                                 │
│  P2 (High) - 0 min                                             │
│  ├── Alert: Slack #security-alerts + email                     │
│  ├── +30 min no ack: PagerDuty on-call                        │
│  ├── +2h no ack: Escalate to team lead                        │
│  └── +4h: Auto-create JIRA incident ticket                    │
│                                                                 │
│  P3 (Medium) - 0 min                                           │
│  ├── Alert: Slack #security-events + email                    │
│  ├── +4h no ack: Re-alert with escalated priority             │
│  └── +24h: Create investigation ticket                        │
│                                                                 │
│  P4 (Low) - Business hours only                                │
│  ├── Alert: Email digest (batched hourly)                     │
│  └── Review: Next daily standup                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Dashboard and Visualization

### 9.1 Grafana Dashboards for Virtual Infrastructure

**Grafana dashboard JSON — Security Overview:**

```json
{
  "dashboard": {
    "id": null,
    "uid": "pve-security-overview",
    "title": "Proxmox Security Overview",
    "tags": ["proxmox", "security", "production"],
    "timezone": "browser",
    "refresh": "30s",
    "time": { "from": "now-24h", "to": "now" },
    "panels": [
      {
        "id": 1,
        "title": "Failed Logins (5m rate)",
        "type": "stat",
        "gridPos": { "h": 4, "w": 4, "x": 0, "y": 0 },
        "targets": [
          {
            "expr": "sum(rate(pve_security_failed_logins[5m]))",
            "legendFormat": "Failed Logins/sec"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                { "value": 0, "color": "green" },
                { "value": 0.5, "color": "yellow" },
                { "value": 2, "color": "red" }
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "Active SSH Sessions",
        "type": "stat",
        "gridPos": { "h": 4, "w": 4, "x": 4, "y": 0 },
        "targets": [
          {
            "expr": "sum(pve_security_ssh_sessions)",
            "legendFormat": "SSH Sessions"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                { "value": 0, "color": "green" },
                { "value": 3, "color": "yellow" },
                { "value": 5, "color": "red" }
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "title": "Cluster Quorum Status",
        "type": "stat",
        "gridPos": { "h": 4, "w": 4, "x": 8, "y": 0 },
        "targets": [
          {
            "expr": "min(pve_security_cluster_quorum)",
            "legendFormat": "Quorum"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              { "type": "value", "options": { "1": { "text": "QUORATE", "color": "green" } } },
              { "type": "value", "options": { "0": { "text": "NO QUORUM", "color": "red" } } }
            ]
          }
        }
      },
      {
        "id": 4,
        "title": "VM CPU Utilization Heatmap",
        "type": "heatmap",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 4 },
        "targets": [
          {
            "expr": "pve_cpu_usage_ratio * 100",
            "legendFormat": "{{ name }}"
          }
        ],
        "options": {
          "color": {
            "scheme": "Spectral",
            "reverse": true
          }
        }
      },
      {
        "id": 5,
        "title": "Network Egress Anomalies",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 4 },
        "targets": [
          {
            "expr": "topk(5, rate(pve_guest_net_out_bytes[5m]))",
            "legendFormat": "{{ name }} ({{ id }})"
          },
          {
            "expr": "avg(rate(pve_guest_net_out_bytes[5m]))",
            "legendFormat": "Cluster Average"
          }
        ],
        "fieldConfig": {
          "overrides": [
            {
              "matcher": { "id": "byName", "options": "Cluster Average" },
              "properties": [
                { "id": "custom.lineStyle", "value": { "fill": "dash" } },
                { "id": "custom.lineWidth", "value": 2 }
              ]
            }
          ]
        }
      },
      {
        "id": 6,
        "title": "Security Events Timeline",
        "type": "logs",
        "gridPos": { "h": 8, "w": 24, "x": 0, "y": 12 },
        "datasource": "Elasticsearch",
        "targets": [
          {
            "query": "event.category:authentication OR event.category:configuration OR security.alert_level:*",
            "timeField": "@timestamp"
          }
        ]
      },
      {
        "id": 7,
        "title": "Active Alerts by Severity",
        "type": "piechart",
        "gridPos": { "h": 6, "w": 6, "x": 0, "y": 20 },
        "targets": [
          {
            "expr": "count(ALERTS{alertstate=\"firing\"}) by (severity)",
            "legendFormat": "{{ severity }}"
          }
        ]
      },
      {
        "id": 8,
        "title": "File Integrity Changes (24h)",
        "type": "stat",
        "gridPos": { "h": 4, "w": 4, "x": 12, "y": 0 },
        "datasource": "Elasticsearch",
        "targets": [
          {
            "query": "rule.groups:syscheck AND @timestamp:[now-24h TO now]",
            "metrics": [{ "type": "count" }],
            "timeField": "@timestamp"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                { "value": 0, "color": "green" },
                { "value": 10, "color": "yellow" },
                { "value": 50, "color": "red" }
              ]
            }
          }
        }
      }
    ]
  }
}
```

### 9.2 Kibana Security Dashboards

**Saved search for threat investigation:**

```json
{
  "attributes": {
    "title": "PVE Security Events - Investigation View",
    "description": "All security-relevant Proxmox events for threat hunting",
    "columns": ["@timestamp", "event.action", "user.name", "source.ip", "host.name", "event.outcome", "message"],
    "sort": [["@timestamp", "desc"]],
    "kibanaSavedObjectMeta": {
      "searchSourceJSON": {
        "query": {
          "bool": {
            "should": [
              { "term": { "event.category": "authentication" } },
              { "term": { "event.category": "configuration" } },
              { "term": { "event.category": "iam" } },
              { "exists": { "field": "threat.technique.id" } },
              { "range": { "event.severity": { "gte": 8 } } }
            ],
            "minimum_should_match": 1
          }
        },
        "filter": [
          { "range": { "@timestamp": { "gte": "now-24h" } } }
        ],
        "index": "proxmox-*"
      }
    }
  }
}
```

### 9.3 Key Metrics and KPIs

| Metric | Target | Measurement | Dashboard |
|--------|--------|-------------|-----------|
| Mean Time to Detect (MTTD) | < 5 min for P1, < 30 min for P2 | Time from event to alert | Security Operations |
| Mean Time to Respond (MTTR) | < 15 min for P1, < 1h for P2 | Time from alert to containment | Security Operations |
| Alert-to-Incident Ratio | < 10:1 (1 incident per 10 alerts) | Tuning effectiveness | Alert Quality |
| False Positive Rate | < 5% for P1/P2 | FP / total alerts | Alert Quality |
| Security Event Volume | Trend (no spike unless justified) | Daily event count | Operations |
| Compliance Score | > 95% | CIS benchmark passing rules | Compliance |
| Vulnerability Count | 0 critical, < 5 high | Open vulnerabilities | Risk |
| Backup Success Rate | > 99% | Successful / scheduled | Operations |
| Cluster Uptime | 99.99% | Measured monthly | Availability |
| Patch Lag | < 7 days for critical | Days since patch release | Risk |

### 9.4 Executive Reporting

Monthly security posture report template (data sources):

```
MONTHLY SECURITY REPORT - VIRTUAL INFRASTRUCTURE
=================================================

1. EXECUTIVE SUMMARY
   - Overall risk rating: [LOW/MEDIUM/HIGH/CRITICAL]
   - Key changes from previous month
   - Top 3 risks requiring attention

2. METRICS SNAPSHOT
   - Total security events: [from Elasticsearch count]
   - Confirmed incidents: [from incident tracker]
   - MTTD/MTTR trends: [from Grafana time-series]
   - Compliance score: [from CIS scan results]
   
3. THREAT LANDSCAPE
   - Attack attempts blocked: [from Wazuh/firewall logs]
   - New vulnerabilities affecting infrastructure: [from CVE feeds]
   - Threat intelligence indicators matched: [from SIEM correlation]

4. INFRASTRUCTURE CHANGES
   - New VMs deployed: [from PVE task logs]
   - Permission changes: [from FIM]
   - Network configuration changes: [from change management]
   - Patch status: [from vulnerability scanner]

5. RECOMMENDATIONS
   - [Prioritized list based on risk]
```

### 9.5 Operational vs Security Dashboards

| Aspect | Operational Dashboard | Security Dashboard |
|--------|----------------------|-------------------|
| Primary audience | SysAdmin, DevOps | SOC analyst, Security engineer |
| Refresh rate | 10-30 seconds | 30-60 seconds |
| Time range default | Last 1-6 hours | Last 24 hours |
| Key focus | Uptime, performance, capacity | Threats, anomalies, compliance |
| Alert threshold | SLA-based | Risk-based |
| Data sources | Prometheus metrics | SIEM events + metrics |
| Color coding | Capacity gradients | Severity (green/yellow/orange/red) |
| Drill-down | To VM/host details | To event investigation |

---

## 10. Lab: Complete Monitoring Stack

### 10.1 Lab Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LAB ENVIRONMENT                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  MONITORING VM (4 vCPU, 16GB RAM, 200GB disk)       │   │
│  │                                                     │   │
│  │  ┌──────────┐ ┌─────────────┐ ┌───────────────┐   │   │
│  │  │ Wazuh    │ │ Elasticsearch│ │ Grafana       │   │   │
│  │  │ Manager  │ │ (single node)│ │ + Prometheus  │   │   │
│  │  │ + Agent  │ │ + Kibana     │ │               │   │   │
│  │  └──────────┘ └─────────────┘ └───────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│                         │ (monitoring network)              │
│                         │                                   │
│  ┌──────────────────────┼──────────────────────────────┐   │
│  │  PROXMOX HOST (target)                              │   │
│  │                                                     │   │
│  │  ┌─────────────┐  ┌──────────┐  ┌──────────────┐   │   │
│  │  │ Wazuh Agent │  │ node_exp │  │ pve-exporter │   │   │
│  │  └─────────────┘  └──────────┘  └──────────────┘   │   │
│  │                                                     │   │
│  │  ┌─────────────┐  ┌──────────┐  ┌──────────────┐   │   │
│  │  │ VM: web-01  │  │ VM: db-01│  │ VM: attacker │   │   │
│  │  │ (target)    │  │ (target) │  │ (Kali/attack)│   │   │
│  │  └─────────────┘  └──────────┘  └──────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 Deploy: Monitoring Stack

**Step 1: Deploy Wazuh (Docker Compose on monitoring VM):**

```yaml
# docker-compose-wazuh.yml
version: '3.8'

services:
  wazuh-manager:
    image: wazuh/wazuh-manager:4.8.0
    hostname: wazuh-manager
    restart: always
    ports:
      - "1514:1514"    # Agent communication
      - "1515:1515"    # Agent enrollment
      - "514:514/udp"  # Syslog
      - "55000:55000"  # API
    environment:
      INDEXER_URL: "https://wazuh-indexer:9200"
      INDEXER_USERNAME: "admin"
      INDEXER_PASSWORD: "${WAZUH_INDEXER_PASSWORD}"
      FILEBEAT_SSL_VERIFICATION_MODE: "full"
    volumes:
      - wazuh_api_configuration:/var/ossec/api/configuration
      - wazuh_etc:/var/ossec/etc
      - wazuh_logs:/var/ossec/logs
      - wazuh_queue:/var/ossec/queue
      - wazuh_var_multigroups:/var/ossec/var/multigroups
      - wazuh_integrations:/var/ossec/integrations
      - wazuh_active_response:/var/ossec/active-response/bin
      - wazuh_agentless:/var/ossec/agentless
      - wazuh_wodles:/var/ossec/wodles
      - ./custom-rules:/var/ossec/etc/rules/custom
      - ./custom-decoders:/var/ossec/etc/decoders/custom

  wazuh-indexer:
    image: wazuh/wazuh-indexer:4.8.0
    hostname: wazuh-indexer
    restart: always
    ports:
      - "9200:9200"
    environment:
      OPENSEARCH_JAVA_OPTS: "-Xms2g -Xmx2g"
    volumes:
      - wazuh-indexer-data:/var/lib/wazuh-indexer

  wazuh-dashboard:
    image: wazuh/wazuh-dashboard:4.8.0
    hostname: wazuh-dashboard
    restart: always
    ports:
      - "443:5601"
    environment:
      INDEXER_USERNAME: "admin"
      INDEXER_PASSWORD: "${WAZUH_INDEXER_PASSWORD}"
      WAZUH_API_URL: "https://wazuh-manager:55000"
    depends_on:
      - wazuh-indexer
      - wazuh-manager

volumes:
  wazuh_api_configuration:
  wazuh_etc:
  wazuh_logs:
  wazuh_queue:
  wazuh_var_multigroups:
  wazuh_integrations:
  wazuh_active_response:
  wazuh_agentless:
  wazuh_wodles:
  wazuh-indexer-data:
```

**Step 2: Deploy Prometheus + Grafana:**

```yaml
# docker-compose-monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.51.0
    hostname: prometheus
    restart: always
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./prometheus/rules/:/etc/prometheus/rules/
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'

  alertmanager:
    image: prom/alertmanager:v0.27.0
    hostname: alertmanager
    restart: always
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml

  grafana:
    image: grafana/grafana:10.4.0
    hostname: grafana
    restart: always
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: "${GRAFANA_ADMIN_PASSWORD}"
      GF_INSTALL_PLUGINS: "grafana-piechart-panel,grafana-worldmap-panel"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning/:/etc/grafana/provisioning/
      - ./grafana/dashboards/:/var/lib/grafana/dashboards/

  pve-exporter:
    image: prompve/prometheus-pve-exporter:latest
    hostname: pve-exporter
    restart: always
    ports:
      - "9221:9221"
    volumes:
      - ./pve-exporter/pve.yml:/etc/pve-exporter/pve.yml
    command:
      - '--config.file=/etc/pve-exporter/pve.yml'

volumes:
  prometheus_data:
  grafana_data:
```

**pve-exporter configuration:**

```yaml
# pve-exporter/pve.yml
default:
  user: monitoring@pve
  token_name: "prometheus"
  token_value: "UUID-TOKEN-HERE"
  verify_ssl: true
```

### 10.3 Configure: Log Collection

**Install Wazuh agent on Proxmox host:**

```bash
#!/bin/bash
# lab-setup-pve-agent.sh

set -euo pipefail

WAZUH_MANAGER="10.10.100.10"
AGENT_NAME="pve-lab-01"

# Install agent
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | gpg --dearmor -o /usr/share/keyrings/wazuh.gpg
echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" > \
  /etc/apt/sources.list.d/wazuh.list
apt-get update && apt-get install -y wazuh-agent

# Configure
sed -i "s/MANAGER_IP/$WAZUH_MANAGER/" /var/ossec/etc/ossec.conf

# Install node_exporter
useradd --no-create-home --shell /bin/false node_exporter || true
curl -sL "https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz" | \
  tar xz --strip-components=1 -C /usr/local/bin/ node_exporter-1.7.0.linux-amd64/node_exporter

# Create textfile directory
mkdir -p /var/lib/node_exporter/textfile

# Systemd service
cat > /etc/systemd/system/node_exporter.service <<'EOF'
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
User=node_exporter
ExecStart=/usr/local/bin/node_exporter \
  --collector.textfile.directory=/var/lib/node_exporter/textfile \
  --collector.systemd \
  --collector.processes \
  --web.listen-address=:9100
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now node_exporter wazuh-agent

# Install security monitoring scripts
mkdir -p /usr/local/bin /var/lib/pve-security
# (copy monitoring scripts from previous sections here)

# Cron for custom metrics
cat > /etc/cron.d/pve-security-metrics <<'EOF'
* * * * * root /usr/local/bin/pve-security-textfile.sh
*/5 * * * * root /usr/local/bin/pve-security-collector.sh
*/15 * * * * root /usr/local/bin/pve-bridge-security-check.sh
EOF

echo "Setup complete. Agent should register with Wazuh manager at $WAZUH_MANAGER"
```

**Configure rsyslog forwarding on Proxmox host:**

```bash
# Deploy rsyslog configuration
cat > /etc/rsyslog.d/60-wazuh-forward.conf <<'EOF'
# Forward security-relevant logs to monitoring stack
module(load="imjournal" StateFile="imjournal.state")

template(name="WazuhJSON" type="list") {
    constant(value="{")
    constant(value="\"timestamp\":\"")  property(name="timereported" dateFormat="rfc3339")
    constant(value="\",\"hostname\":\"") property(name="hostname")
    constant(value="\",\"program\":\"")  property(name="programname")
    constant(value="\",\"severity\":\"") property(name="syslogseverity-text")
    constant(value="\",\"facility\":\"") property(name="syslogfacility-text")
    constant(value="\",\"message\":\"")  property(name="msg" format="json")
    constant(value="\"}\n")
}

# Security log forwarding
if ($syslogfacility-text == 'auth' or
    $syslogfacility-text == 'authpriv' or
    $programname startswith 'pve' or
    $programname == 'corosync' or
    $programname == 'sshd') then {
    action(type="omfwd"
           Target="10.10.100.10"
           Port="514"
           Protocol="tcp"
           Template="WazuhJSON"
           queue.type="LinkedList"
           queue.filename="wazuh_fwd"
           queue.size="10000"
           queue.saveonshutdown="on"
           action.resumeRetryCount="-1")
}
EOF

systemctl restart rsyslog
```

### 10.4 Create: Detection Rules

Deploy the custom rules created in sections 4 and 5:

```bash
#!/bin/bash
# lab-deploy-rules.sh
# Deploy detection rules to Wazuh manager

WAZUH_DIR="/var/ossec"
RULES_DIR="$WAZUH_DIR/etc/rules"
DECODERS_DIR="$WAZUH_DIR/etc/decoders"

# Create custom decoders
cat > "$DECODERS_DIR/0500-proxmox-decoders.xml" <<'EOF'
<!-- Proxmox VE Custom Decoders -->
<decoder name="pveproxy-auth">
  <program_name>pveproxy</program_name>
  <prematch>authentication</prematch>
  <regex offset="after_prematch">\s(\w+)\sfor\s'(\S+)'\sfrom\s(\S+)</regex>
  <order>status,user,srcip</order>
</decoder>

<decoder name="pve-task-start">
  <program_name>pvedaemon</program_name>
  <prematch>starting task UPID:</prematch>
  <regex>UPID:(\S+):(\w+):(\w+):(\w+):(\w+):(\S*):(\S+):</regex>
  <order>dstuser,extra_data,id,status,action,url,user</order>
</decoder>

<decoder name="pve-corosync-member">
  <program_name>corosync</program_name>
  <prematch>Member</prematch>
  <regex>Member\s(\w+):\s(\S+)\s\((\S+)\)</regex>
  <order>action,id,extra_data</order>
</decoder>
EOF

# Create custom rules (consolidated from section 4.4)
cat > "$RULES_DIR/0900-proxmox-rules.xml" <<'EOF'
<group name="proxmox,">

  <rule id="100200" level="5">
    <decoded_as>pveproxy-auth</decoded_as>
    <match>failure</match>
    <description>Proxmox: Authentication failure for $(user) from $(srcip)</description>
    <mitre>
      <id>T1110</id>
    </mitre>
    <group>authentication_failures,pve,</group>
  </rule>

  <rule id="100201" level="12" frequency="10" timeframe="120">
    <if_matched_sid>100200</if_matched_sid>
    <same_source_ip/>
    <description>Proxmox: Brute force attack from $(srcip)</description>
    <mitre>
      <id>T1110.001</id>
    </mitre>
    <group>authentication_failures,pve,brute_force,</group>
  </rule>

  <rule id="100210" level="10">
    <decoded_as>pve-task-start</decoded_as>
    <match>qmdestroy|vzdestroy</match>
    <description>Proxmox: VM/CT destroyed by $(user)</description>
    <mitre>
      <id>T1485</id>
    </mitre>
    <group>pve,vm_operations,destructive,</group>
  </rule>

  <rule id="100211" level="12">
    <decoded_as>pve-task-start</decoded_as>
    <match>qmclone|vzclone</match>
    <description>Proxmox: VM/CT cloned by $(user) - verify authorization</description>
    <mitre>
      <id>T1074.001</id>
    </mitre>
    <group>pve,vm_operations,clone,</group>
  </rule>

  <rule id="100220" level="14">
    <decoded_as>pve-corosync-member</decoded_as>
    <match>joined</match>
    <description>Proxmox: New node joined cluster</description>
    <mitre>
      <id>T1098</id>
    </mitre>
    <group>pve,cluster,membership_change,</group>
  </rule>

  <rule id="100230" level="12">
    <if_sid>550,553,554</if_sid>
    <match>/etc/pve/user.cfg|/etc/pve/acl.cfg</match>
    <description>Proxmox: User/ACL configuration modified</description>
    <mitre>
      <id>T1098</id>
    </mitre>
    <group>pve,fim,iam_change,</group>
  </rule>

  <rule id="100240" level="10">
    <if_sid>550,553,554</if_sid>
    <match>/etc/pve/firewall</match>
    <description>Proxmox: Firewall configuration modified</description>
    <mitre>
      <id>T1562.004</id>
    </mitre>
    <group>pve,fim,firewall_change,</group>
  </rule>

  <rule id="100250" level="8">
    <decoded_as>pve-task-start</decoded_as>
    <match>qmsnapshot</match>
    <time>6 pm - 6 am</time>
    <description>Proxmox: VM snapshot outside business hours by $(user)</description>
    <mitre>
      <id>T1074.001</id>
    </mitre>
    <group>pve,vm_operations,after_hours,</group>
  </rule>

</group>
EOF

# Verify rules syntax
$WAZUH_DIR/bin/wazuh-analysisd -t 2>&1 | tail -5

# Restart Wazuh manager to load new rules
systemctl restart wazuh-manager

echo "Rules deployed and Wazuh manager restarted."
```

**Deploy Prometheus alerting rules:**

```yaml
# prometheus/rules/pve-security.yml
groups:
  - name: pve_security_alerts
    interval: 30s
    rules:
      - alert: PVEBruteForce
        expr: rate(pve_security_failed_logins[5m]) > 2
        for: 2m
        labels:
          severity: high
          service: proxmox
        annotations:
          summary: "Brute force detected on {{ $labels.instance }}"
          description: "Failed login rate: {{ $value }}/s on {{ $labels.instance }}"
          runbook_url: "https://wiki.internal.corp/runbooks/pve-brute-force"

      - alert: PVECryptomining
        expr: |
          pve_cpu_usage_ratio > 0.95
          unless on(id) pve_guest_info{name=~".*compute.*"}
        for: 30m
        labels:
          severity: high
          service: proxmox
        annotations:
          summary: "Possible cryptomining: {{ $labels.name }} ({{ $labels.id }})"

      - alert: PVENetworkAnomaly
        expr: |
          rate(pve_guest_net_out_bytes[5m]) > 
          (avg_over_time(pve_guest_net_out_bytes[7d]) + 3 * stddev_over_time(pve_guest_net_out_bytes[7d]))
        for: 10m
        labels:
          severity: high
          service: proxmox
        annotations:
          summary: "Network egress anomaly: {{ $labels.name }}"

      - alert: PVEClusterQuorumLost
        expr: pve_security_cluster_quorum == 0
        for: 0m
        labels:
          severity: critical
          service: proxmox
        annotations:
          summary: "Proxmox cluster quorum LOST on {{ $labels.instance }}"
          description: "Cluster has lost quorum. Possible network partition or node failure."

      - alert: PVEUnexpectedSSH
        expr: pve_security_ssh_sessions > 2
        for: 5m
        labels:
          severity: medium
          service: proxmox
        annotations:
          summary: "Multiple SSH sessions on {{ $labels.instance }}"
          description: "{{ $value }} active SSH sessions. Normal is 0-1."

  - name: pve_storage_alerts
    rules:
      - alert: PVEStorageRansomware
        expr: |
          (rate(node_disk_writes_completed_total{job="node-exporter-pve"}[5m]) > 
           2 * avg_over_time(rate(node_disk_writes_completed_total{job="node-exporter-pve"}[5m])[7d:5m]))
          and
          (rate(node_disk_read_bytes_total{job="node-exporter-pve"}[5m]) > 
           1.5 * avg_over_time(rate(node_disk_read_bytes_total{job="node-exporter-pve"}[5m])[7d:5m]))
        for: 5m
        labels:
          severity: critical
          service: proxmox
        annotations:
          summary: "Ransomware indicators on {{ $labels.instance }}"
          description: "Read-encrypt-write pattern detected. IMMEDIATE ACTION REQUIRED."
```

### 10.5 Test: Trigger Alerts with Simulated Attacks

**Attack simulation script (run from "attacker" VM):**

```bash
#!/bin/bash
# lab-attack-simulation.sh
# Simulate common attacks to validate detection
# Run from attacker VM in the lab environment

PVE_HOST="10.10.100.1"
PVE_API="https://$PVE_HOST:8006"
TARGET_VM_IP="10.10.100.20"

echo "=== ATTACK SIMULATION SUITE ==="
echo "Target: $PVE_HOST"
echo "Starting at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# --- Test 1: Brute Force Attack ---
echo "[TEST 1] Brute force against Proxmox API..."
for i in $(seq 1 25); do
    curl -sk -X POST "$PVE_API/api2/json/access/ticket" \
      -d "username=admin@pve&password=wrong_pass_$i" \
      > /dev/null 2>&1
    sleep 0.5
done
echo "[TEST 1] Complete. Expected alert: PVEBruteForce / rule 100201"
echo ""
sleep 5

# --- Test 2: SSH Brute Force ---
echo "[TEST 2] SSH brute force against Proxmox host..."
for i in $(seq 1 15); do
    sshpass -p "wrong_password_$i" ssh -o StrictHostKeyChecking=no \
      -o ConnectTimeout=3 "testuser@$PVE_HOST" exit 2>/dev/null
done
echo "[TEST 2] Complete. Expected alert: SSH brute force"
echo ""
sleep 5

# --- Test 3: Simulated Cryptomining (CPU stress on target VM) ---
echo "[TEST 3] CPU stress on target VM (simulating cryptominer)..."
ssh -o StrictHostKeyChecking=no "root@$TARGET_VM_IP" \
  "stress-ng --cpu 0 --timeout 120s &" 2>/dev/null
echo "[TEST 3] Running for 120s. Expected alert: PVECryptomining (after 30m threshold)"
echo ""

# --- Test 4: Network Exfiltration Simulation ---
echo "[TEST 4] Simulated data exfiltration (large outbound transfer)..."
ssh -o StrictHostKeyChecking=no "root@$TARGET_VM_IP" \
  "dd if=/dev/urandom bs=1M count=500 | nc -w 5 $PVE_HOST 9999" 2>/dev/null &
echo "[TEST 4] Running. Expected alert: PVENetworkAnomaly"
echo ""

# --- Test 5: Port Scanning (lateral movement recon) ---
echo "[TEST 5] Port scan from compromised VM..."
ssh -o StrictHostKeyChecking=no "root@$TARGET_VM_IP" \
  "nmap -sS -p 22,80,443,3389,5985,8006 10.10.100.0/24 -T4" 2>/dev/null
echo "[TEST 5] Complete. Expected alert: Lateral movement indicators"
echo ""

# --- Test 6: ARP Spoofing ---
echo "[TEST 6] ARP spoofing attempt..."
ssh -o StrictHostKeyChecking=no "root@$TARGET_VM_IP" \
  "arpspoof -i eth0 -t 10.10.100.1 10.10.100.254" 2>/dev/null &
ARP_PID=$!
sleep 10
kill $ARP_PID 2>/dev/null
echo "[TEST 6] Complete. Expected alert: ARP spoofing detection"
echo ""

echo "=== SIMULATION COMPLETE ==="
echo "Ended at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""
echo "Verification steps:"
echo "  1. Check Wazuh dashboard for triggered alerts"
echo "  2. Check Prometheus/Alertmanager for firing alerts"
echo "  3. Check Grafana security dashboard for event spikes"
echo "  4. Verify alert notification delivery (Slack, email, PagerDuty)"
```

### 10.6 Tune: Reduce False Positives

After running the simulation, review alerts and apply tuning:

**Tuning methodology:**

```
1. COLLECT: Run monitoring for 1-2 weeks in production-like environment
2. REVIEW: Export all triggered alerts, categorize as:
   - True Positive (TP): Real security event, correct detection
   - False Positive (FP): Benign activity incorrectly flagged
   - True Negative (TN): Benign activity correctly ignored
   - False Negative (FN): Attack not detected (found via red team/simulation)
3. TUNE: For each FP category:
   - Add exclusions for known good behavior
   - Adjust thresholds based on baseline data
   - Add time-based context (business hours, maintenance windows)
   - Whitelist service accounts performing authorized operations
4. VALIDATE: Re-run attack simulations to ensure TPs still detected
5. ITERATE: Monthly tuning cycle
```

**Example tuning entries:**

```xml
<!-- Wazuh: Suppress alerts for backup service account -->
<rule id="100299" level="0">
  <if_sid>100211</if_sid>
  <match>user=backup-svc@pve</match>
  <time>1 am - 5 am</time>
  <description>Suppressed: Authorized backup clone during backup window</description>
</rule>

<!-- Suppress: Known maintenance automation -->
<rule id="100298" level="0">
  <if_sid>100240</if_sid>
  <match>user=ansible@pve|user=terraform@pve</match>
  <description>Suppressed: Authorized automation modifying firewall</description>
</rule>
```

**Prometheus recording rules for baseline calculation:**

```yaml
# prometheus/rules/pve-baselines.yml
groups:
  - name: pve_baselines
    interval: 5m
    rules:
      # 7-day rolling average CPU per VM
      - record: pve:cpu_usage_avg7d:ratio
        expr: avg_over_time(pve_cpu_usage_ratio[7d])

      # 7-day rolling average network egress per VM
      - record: pve:net_out_avg7d:bytes_per_second
        expr: avg_over_time(rate(pve_guest_net_out_bytes[5m])[7d:5m])

      # Standard deviation for anomaly detection
      - record: pve:net_out_stddev7d:bytes_per_second
        expr: stddev_over_time(rate(pve_guest_net_out_bytes[5m])[7d:5m])

      # Failed login baseline
      - record: pve:failed_logins_avg7d:rate5m
        expr: avg_over_time(rate(pve_security_failed_logins[5m])[7d:5m])
```

### 10.7 Build: Security Dashboard

**Complete Grafana dashboard provisioning:**

```yaml
# grafana/provisioning/dashboards/dashboard.yml
apiVersion: 1

providers:
  - name: 'Security Dashboards'
    orgId: 1
    folder: 'Security'
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

**Grafana datasource provisioning:**

```yaml
# grafana/provisioning/datasources/datasource.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true

  - name: Elasticsearch
    type: elasticsearch
    access: proxy
    url: https://wazuh-indexer:9200
    database: "wazuh-alerts-*"
    basicAuth: true
    basicAuthUser: admin
    secureJsonData:
      basicAuthPassword: "${WAZUH_INDEXER_PASSWORD}"
    jsonData:
      timeField: "timestamp"
      esVersion: "7.10.2"
      logMessageField: "rule.description"
      logLevelField: "rule.level"
    editable: true

  - name: Alertmanager
    type: alertmanager
    access: proxy
    url: http://alertmanager:9093
    jsonData:
      implementation: prometheus
    editable: true
```

**Final validation checklist:**

```
LAB VALIDATION CHECKLIST
========================

[ ] Infrastructure
    [ ] Wazuh Manager running and accessible on port 55000
    [ ] Elasticsearch/OpenSearch indices receiving data
    [ ] Prometheus scraping all targets (check /targets)
    [ ] Grafana accessible with all datasources connected
    [ ] AlertManager configured with notification channels

[ ] Data Collection
    [ ] Wazuh agent on PVE host: agent status = active
    [ ] Syslog forwarding from PVE to Wazuh: verify events in dashboard
    [ ] Prometheus metrics from node_exporter: verify in Grafana
    [ ] Prometheus metrics from pve-exporter: verify VM data
    [ ] Custom textfile metrics: pve_security_* metrics visible

[ ] Detection Rules
    [ ] Wazuh rules loaded without syntax errors (wazuh-analysisd -t)
    [ ] Prometheus alerting rules loaded (check /rules in Prometheus UI)
    [ ] AlertManager routes configured and testable

[ ] Attack Simulation Results
    [ ] Brute force: Alert triggered within 2 minutes
    [ ] SSH brute force: Alert triggered
    [ ] CPU anomaly: Alert triggered (after threshold period)
    [ ] Network anomaly: Alert triggered within 10 minutes
    [ ] Port scan: Logged as suspicious activity

[ ] Alerting & Response
    [ ] Slack notification received for test alert
    [ ] Email notification received
    [ ] PagerDuty incident created (if configured)
    [ ] Automated response (VM isolation) functionally tested

[ ] Dashboards
    [ ] Security overview dashboard shows real-time data
    [ ] Failed login count reflects simulation data
    [ ] Network traffic panel shows anomaly period
    [ ] Alert timeline shows triggered rules
```

---

## Appendix A: Complete File Reference

| File/Config | Purpose | Section |
|-------------|---------|---------|
| `/etc/rsyslog.d/10-esxi-receiver.conf` | ESXi syslog receiver | 2.1 |
| `/etc/rsyslog.d/50-proxmox-forward.conf` | PVE journal forwarding | 3.1 |
| `/etc/rsyslog.d/60-siem-forward.conf` | RELP-based SIEM forwarding | 4.1 |
| `/etc/filebeat/filebeat.yml` | Filebeat PVE inputs | 4.1 |
| `/etc/logstash/conf.d/20-proxmox-normalize.conf` | Event normalization | 4.2 |
| `/var/ossec/etc/decoders/proxmox_decoders.xml` | Wazuh custom decoders | 4.4 |
| `/var/ossec/etc/rules/proxmox_rules.xml` | Wazuh detection rules | 4.4 |
| `/etc/prometheus/prometheus.yml` | Prometheus scrape config | 3.7 |
| `/etc/prometheus/rules/pve-security.yml` | Alerting rules | 5.3, 10.4 |
| `/etc/alertmanager/alertmanager.yml` | Alert routing & notifications | 8.3 |
| `/usr/local/bin/pve-security-textfile.sh` | Custom Prometheus metrics | 3.7 |
| `/usr/local/bin/pve-security-collector.sh` | API-based security collector | 3.6 |
| `/usr/local/bin/pve-qemu-monitor.sh` | QEMU process anomaly detection | 3.4 |
| `/usr/local/bin/pve-bridge-security-check.sh` | Bridge security monitoring | 6.1 |
| `/usr/local/bin/pve-arp-monitor.sh` | ARP spoofing detection | 6.6 |
| `/usr/local/bin/pve-backup-integrity.sh` | Backup integrity verification | 7.2 |
| `/usr/local/bin/entropy_monitor.py` | Ransomware entropy detection | 7.3 |
| `/var/ossec/active-response/bin/isolate-vm.sh` | Automated VM isolation | 8.4 |
| `/var/ossec/active-response/bin/lockout-pve-user.sh` | Account lockout | 8.4 |

## Appendix B: MITRE ATT&CK Mapping

| Technique ID | Name | Detection Rule(s) | Data Source |
|-------------|------|-------------------|-------------|
| T1110 | Brute Force | 100200, 100201 | Auth logs, API access logs |
| T1110.001 | Password Guessing | 100201 | Failed login events |
| T1078 | Valid Accounts | 100312 | Permission changes + operations |
| T1078.004 | Cloud Accounts | 100310 | Admin role assignments |
| T1098 | Account Manipulation | 100220, 100230 | FIM on user.cfg/acl.cfg |
| T1485 | Data Destruction | 100210 | VM destroy operations |
| T1074.001 | Local Data Staging | 100211, 100250 | Clone/snapshot operations |
| T1048 | Exfiltration Over Alternative Protocol | Network anomaly rules | NetFlow, egress metrics |
| T1562.004 | Disable/Modify Firewall | 100240, 100330, 100331 | FIM on firewall configs |
| T1565.001 | Stored Data Manipulation | 100231 | FIM on cluster configs |
| T1578.002 | Create Cloud Instance | 100300 | VM creation events |
| T1599 | Network Boundary Bridging | 100240 | Network config changes |

## Appendix C: Maintenance Schedule

| Task | Frequency | Owner | Automation |
|------|-----------|-------|------------|
| Review and tune alert thresholds | Weekly (first 3 months), then monthly | Security Engineer | Manual |
| Update detection rules | Monthly or upon new threat intel | Security Engineer | CI/CD pipeline |
| Rotate monitoring credentials | 90 days | Security Engineer | Vault auto-rotation |
| Verify backup of monitoring data | Weekly | SysAdmin | Automated check |
| Test alert delivery (all channels) | Monthly | SOC Lead | Synthetic alert injection |
| Review SIEM correlation rules | Quarterly | Security Architect | Manual + red team validation |
| Capacity planning for log storage | Quarterly | Infrastructure Lead | Prometheus capacity alerts |
| Full stack DR test | Semi-annually | Team | Planned exercise |
| Threat model review | Annually or upon architecture change | Security Architect | Manual |

---

## Summary

Security monitoring of virtual infrastructure demands a multi-layered approach that treats the hypervisor as both a critical asset and a unique vantage point. Unlike traditional endpoint monitoring, virtual infrastructure monitoring must cover:

1. **The hypervisor itself** — as a high-value target whose compromise means total environment compromise.
2. **The management plane** — where a single stolen credential can control hundreds of VMs.
3. **Inter-VM traffic** — invisible to physical network monitoring devices.
4. **Storage operations** — where bulk data theft can occur through legitimate backup mechanisms.

The monitoring stack described in this module (Wazuh + Elasticsearch + Prometheus + Grafana) provides comprehensive coverage across all layers while remaining open-source and operationally sustainable. Key success factors:

- **Detection rules mapped to MITRE ATT&CK** ensure coverage against known attack patterns.
- **Automated response** contains threats in seconds rather than hours.
- **Alert tuning** prevents alert fatigue from rendering the entire system ineffective.
- **Continuous validation** through regular red team exercises confirms detection capability.

The lab exercise in section 10 provides a concrete, reproducible deployment that can serve as the foundation for production monitoring. Start with the core detection rules, validate with simulated attacks, tune aggressively in the first 90 days, and iterate monthly thereafter.
