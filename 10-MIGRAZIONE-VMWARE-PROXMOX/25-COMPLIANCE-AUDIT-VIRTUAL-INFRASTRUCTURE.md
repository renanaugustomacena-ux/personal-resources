# Compliance Auditing and Security Assessment for Virtualized Infrastructure

> **Module:** Advanced Security Operations for Virtualized Environments  
> **Audience:** Senior IT infrastructure engineers, security auditors, ethical hackers assessing virtual infrastructure  
> **Prerequisites:** Working knowledge of VMware vSphere 7.x/8.x, Proxmox VE 8.x, Linux administration, network security fundamentals, familiarity with at least one compliance framework  
> **Scope:** Comprehensive audit methodology spanning VMware ESXi, vCenter Server, and Proxmox VE — covering compliance mapping, automated assessment, vulnerability management, penetration testing scoping, and continuous monitoring  
> **Last updated:** 2026-05-07  
> **Reference versions:** VMware vSphere 8.0 U3, Proxmox VE 8.2, CIS Benchmarks v1.1 (ESXi 8.0), DISA STIG vSphere 8 Release 1, PCI-DSS 4.0, NIST SP 800-125B Rev 1

---

## Table of Contents

1. [Compliance Frameworks for Virtualization](#1-compliance-frameworks-for-virtualization)
2. [CIS Benchmark Implementation](#2-cis-benchmark-implementation)
3. [VMware STIG Compliance](#3-vmware-stig-compliance)
4. [Audit Evidence Collection](#4-audit-evidence-collection)
5. [Vulnerability Assessment](#5-vulnerability-assessment)
6. [Penetration Testing Scoping](#6-penetration-testing-scoping)
7. [Access Control Audit](#7-access-control-audit)
8. [Network Security Audit](#8-network-security-audit)
9. [Backup and DR Compliance](#9-backup-and-dr-compliance)
10. [Audit Reporting and Remediation](#10-audit-reporting-and-remediation)

---

## 1. Compliance Frameworks for Virtualization

### 1.1 PCI-DSS 4.0 Applied to Hypervisors

PCI-DSS 4.0 (effective March 2024, mandatory March 2025) treats hypervisors as system components within the Cardholder Data Environment (CDE) when they host VMs that process, store, or transmit cardholder data. Four requirements carry particular weight for virtualization teams:

**Requirement 2 — Secure Configurations**

- All hypervisor defaults must be changed before deployment: default accounts, SNMP community strings, unnecessary services, sample VMs.
- Configuration standards must be documented and based on industry-accepted hardening guides (CIS, DISA STIG).
- One primary function per virtual machine — do not co-locate CDE and non-CDE workloads on the same VM.
- Applies to ESXi hosts, vCenter, Proxmox nodes, and the management interfaces themselves.

Assessment evidence required:
```
- Documented configuration standard for each hypervisor type
- Evidence that defaults were changed (PowerCLI/pvesh output showing non-default settings)
- Network scan confirming only necessary ports/services are active
- Inventory mapping VMs to their function and data classification
```

**Requirement 6 — Secure Systems and Software**

- Hypervisor patches must be applied within defined timelines (critical: 30 days after release under 4.0).
- Custom virtual appliances must follow secure development lifecycle.
- vCenter plugins, Proxmox packages from third-party repos require vulnerability assessment before deployment.
- Change control processes must cover hypervisor configuration changes.

**Requirement 10 — Log and Monitor All Access**

- All access to hypervisor management must produce audit trails: vCenter tasks/events, ESXi hostd logs, Proxmox `pveproxy` access logs.
- Logs must include: user identification, event type, date/time, success/failure, origination, resource affected.
- Log integrity mechanisms — NTP synchronization across all hypervisors, syslog forwarding to immutable SIEM.
- Review of logs daily (automated alerting satisfies this when configured per 10.4.1.1).
- Retention: 12 months minimum, 3 months immediately available.

**Requirement 11 — Test Security Regularly**

- Quarterly internal vulnerability scans must include hypervisors.
- Annual penetration test must consider the hypervisor layer if in scope.
- File integrity monitoring on hypervisor configuration files (ESXi `/etc/vmware/`, Proxmox `/etc/pve/`).
- Wireless detection — less relevant for hypervisors but management network must be assessed.

### 1.2 HIPAA Technical Safeguards for Virtualized PHI

The HIPAA Security Rule (45 CFR Part 164, Subpart C) does not prescribe technologies but mandates outcomes. For virtualized infrastructure hosting Protected Health Information (PHI):

**Access Control (§164.312(a))**

| Specification | Hypervisor Implementation |
|---|---|
| Unique user identification | Named accounts in vCenter/Proxmox — no shared `root` for operations |
| Emergency access procedure | Break-glass accounts with sealed credentials, auditable usage |
| Automatic logoff | Session timeout on vSphere Client (default 120 min — reduce to 15) and Proxmox web UI |
| Encryption and decryption | VM encryption (vSphere), LUKS volumes (Proxmox), encrypted vMotion/migration |

**Audit Controls (§164.312(b))**

- Hardware, software, and procedural mechanisms to record and examine access to ePHI.
- Hypervisor-level: all VM power operations, snapshot creation/deletion, console access, configuration changes.
- Correlation: map hypervisor events to application-layer PHI access for complete audit trail.

**Integrity Controls (§164.312(c))**

- Mechanisms to authenticate ePHI — integrity verification of VM disks, hash verification of backups containing PHI.
- Detect unauthorized alteration of VM configurations that could expose PHI.

**Transmission Security (§164.312(e))**

- Encrypted vMotion/live migration (enforce "required" in vSphere, use WireGuard/IPsec for Proxmox live migration).
- Storage traffic encryption (encrypted Ceph messenger v2, iSCSI CHAP + IPsec or dedicated VLAN).
- Management traffic encryption (TLS 1.2+ for vCenter/ESXi/Proxmox web consoles).

### 1.3 SOC 2 Type II — Availability and Security Criteria

SOC 2 Type II audits evaluate operating effectiveness over a period (typically 6–12 months). For virtual infrastructure:

**Common Criteria (CC) Relevant to Virtualization:**

- CC6.1 — Logical and physical access controls: RBAC on hypervisor, MFA for management access, physical security of hosts.
- CC6.2 — Access provisioning: Documented process for granting hypervisor access, approval workflows.
- CC6.3 — Access removal: Timely deprovisioning when personnel change roles/leave.
- CC7.1 — Detection: Monitoring and alerting on hypervisor anomalies (unusual VM creation, privilege escalation).
- CC7.2 — Incident response: Procedures specific to virtual infrastructure incidents (VM escape, hypervisor compromise).
- CC8.1 — Change management: Controlled process for hypervisor updates, configuration changes, VM deployments.

**Availability Criteria (A1):**

- A1.1 — Capacity management: Resource monitoring (CPU, memory, storage, network) with alerting before exhaustion.
- A1.2 — Recovery: Tested backup and restore procedures for VMs, hypervisor configurations, and cluster state.
- A1.3 — Testing: Regular DR testing with documented results and identified gaps.

Evidence for SOC 2 Type II spans the audit period — point-in-time screenshots are insufficient. Automated, timestamped evidence collection (covered in Section 4) is essential.

### 1.4 ISO 27001:2022 — Annex A Controls for Virtualization

ISO 27001:2022 restructured Annex A into four themes. Relevant controls for virtual infrastructure:

**Organizational Controls:**
- A.5.1 — Policies for information security: Must include virtualization-specific policies (VM lifecycle, hypervisor hardening standards).
- A.5.15 — Access control: RBAC policies for hypervisor management mapped to roles.
- A.5.23 — Information security for cloud services: If using hosted/hybrid virtualization.
- A.5.28 — Collection of evidence: Procedures for hypervisor forensic evidence preservation.

**Technological Controls:**
- A.8.5 — Secure authentication: MFA for hypervisor management interfaces.
- A.8.6 — Capacity management: Virtualization resource monitoring and alerting.
- A.8.8 — Management of technical vulnerabilities: Patch management for hypervisors.
- A.8.9 — Configuration management: Baseline configurations for hypervisors, drift detection.
- A.8.12 — Data leakage prevention: Prevent data exfiltration via VM export, snapshot theft.
- A.8.15 — Logging: Centralized logging from all hypervisor components.
- A.8.16 — Monitoring activities: SIEM integration, anomaly detection.
- A.8.20 — Network security: Virtual network segmentation, micro-segmentation.
- A.8.25 — Secure development lifecycle: Applied to infrastructure-as-code for VM provisioning.
- A.8.31 — Separation of environments: Enforce separation between dev/test/prod at hypervisor level.

### 1.5 CIS Benchmarks for VMware ESXi 7.x/8.x and Proxmox

The Center for Internet Security (CIS) publishes consensus-based hardening benchmarks:

**CIS VMware ESXi 8.0 Benchmark v1.1.0 (2024)**

Categories and control count:
| Category | Controls | Priority |
|---|---|---|
| Installation and Patching | 8 | Critical |
| Communication | 12 | High |
| Logging | 9 | High |
| Access | 15 | Critical |
| Console | 7 | Medium |
| Storage | 5 | Medium |
| vNetwork | 11 | High |

Profiles:
- Level 1: Settings that can be applied broadly with minimal functional impact.
- Level 2: Settings that may reduce functionality or require environment-specific tuning.

**CIS for Proxmox VE**

CIS does not publish a Proxmox-specific benchmark. The correct approach:
1. Apply CIS Debian 12 Benchmark to the Proxmox host OS layer.
2. Supplement with Proxmox-specific hardening (covered in Section 2.4).
3. Map NIST 800-125 controls to Proxmox features.

### 1.6 NIST SP 800-125 — Guide to Security for Full Virtualization

NIST SP 800-125 (Revision 1, 2024) provides foundational guidance:

**Key recommendations directly applicable:**

1. **Secure the hypervisor**: Treat the hypervisor as the highest-value target — compromise here means compromise of all hosted workloads.
2. **Harden the virtualization management system**: vCenter/Proxmox web management must be isolated on a management VLAN with strict access controls.
3. **Protect virtual networking**: Virtual switch configurations are as critical as physical switch configurations.
4. **Plan security for virtualized infrastructure image management**: VM templates and images require integrity verification and access control.
5. **Secure guest OS environments**: Each VM must be hardened independently — the hypervisor does not provide security to the guest.
6. **Ensure virtualization infrastructure is continuously monitored**: Real-time monitoring of hypervisor configuration changes and resource anomalies.

NIST SP 800-125B extends this with guidance on secure virtual network configuration — particularly relevant for VM-to-VM traffic isolation.

---

## 2. CIS Benchmark Implementation

### 2.1 ESXi 8.0 CIS Benchmark — Complete Walkthrough

#### 2.1.1 Installation and Patching Controls

**Control 1.1 — Verify ESXi build matches latest patch level**

Rationale: Unpatched hypervisors are the most common critical finding in virtualization audits.

Assessment (PowerCLI):
```powershell
# Connect to vCenter
Connect-VIServer -Server vcenter.corp.local -Credential (Get-Credential)

# Assess all hosts patch level
Get-VMHost | ForEach-Object {
    $esxcli = Get-EsxCli -VMHost $_ -V2
    [PSCustomObject]@{
        Host       = $_.Name
        Build      = $_.Build
        Version    = $_.Version
        PatchLevel = $esxcli.software.profile.get.Invoke().Name
        UpdateDate = $esxcli.software.profile.get.Invoke().CreationTime
    }
} | Format-Table -AutoSize
```

Remediation: Apply latest Image Profile via vLCM (vSphere Lifecycle Manager) or manual patch bundle:
```powershell
# vLCM compliance check
$cluster = Get-Cluster -Name "Production"
Test-Compliance -Entity $cluster
```

**Control 1.2 — Verify Image Profile acceptance level is PartnerSupported or higher**

```powershell
Get-VMHost | ForEach-Object {
    $esxcli = Get-EsxCli -VMHost $_ -V2
    [PSCustomObject]@{
        Host            = $_.Name
        AcceptanceLevel = $esxcli.software.acceptance.get.Invoke()
    }
}
# Expected: PartnerSupported or VMwareCertified or VMwareAccepted
# Finding: CommunitySupported = non-compliant
```

**Control 1.3 — Verify no unauthorized VIBs are installed**

```powershell
Get-VMHost | ForEach-Object {
    $esxcli = Get-EsxCli -VMHost $_ -V2
    $vibs = $esxcli.software.vib.list.Invoke()
    $unauthorized = $vibs | Where-Object { $_.AcceptanceLevel -eq "CommunitySupported" }
    if ($unauthorized) {
        Write-Warning "Host $($_.Name) has CommunitySupported VIBs:"
        $unauthorized | Select-Object Name, Version, Vendor
    }
}
```

#### 2.1.2 Communication Controls

**Control 2.1 — NTP configuration**

All ESXi hosts must synchronize time with authorized NTP sources. Time drift breaks log correlation and certificate validation.

```powershell
Get-VMHost | ForEach-Object {
    $ntpService = $_ | Get-VMHostService | Where-Object { $_.Key -eq "ntpd" }
    $ntpServers = $_ | Get-VMHostNtpServer
    [PSCustomObject]@{
        Host       = $_.Name
        NTPRunning = $ntpService.Running
        NTPPolicy  = $ntpService.Policy
        NTPServers = ($ntpServers -join ", ")
    }
}
```

Remediation:
```powershell
$ntpServers = @("10.0.1.10", "10.0.1.11")
Get-VMHost | ForEach-Object {
    $_ | Remove-VMHostNtpServer -NtpServer ($_ | Get-VMHostNtpServer) -Confirm:$false
    $_ | Add-VMHostNtpServer -NtpServer $ntpServers
    $_ | Get-VMHostService | Where-Object { $_.Key -eq "ntpd" } | Set-VMHostService -Policy "on"
    $_ | Get-VMHostService | Where-Object { $_.Key -eq "ntpd" } | Start-VMHostService -Confirm:$false
}
```

**Control 2.2 — Disable SSH unless required for maintenance**

```powershell
Get-VMHost | ForEach-Object {
    $ssh = $_ | Get-VMHostService | Where-Object { $_.Key -eq "TSM-SSH" }
    [PSCustomObject]@{
        Host       = $_.Name
        SSHRunning = $ssh.Running
        SSHPolicy  = $ssh.Policy
    }
}
# Compliant: Running=False, Policy=off
```

**Control 2.3 — Disable ESXi Shell**

```powershell
Get-VMHost | ForEach-Object {
    $shell = $_ | Get-VMHostService | Where-Object { $_.Key -eq "TSM" }
    [PSCustomObject]@{
        Host         = $_.Name
        ShellRunning = $shell.Running
        ShellPolicy  = $shell.Policy
    }
}
```

**Control 2.4 — TLS protocol enforcement**

Ensure only TLS 1.2+ is accepted:
```powershell
Get-VMHost | ForEach-Object {
    $advSetting = $_ | Get-AdvancedSetting -Name "UserVars.ESXiVPsDisabledProtocols"
    [PSCustomObject]@{
        Host              = $_.Name
        DisabledProtocols = $advSetting.Value
    }
}
# Expected value: "sslv3,tlsv1,tlsv1.1"
```

**Control 2.5 — DCUI timeout**

```powershell
Get-VMHost | Get-AdvancedSetting -Name "UserVars.DcuiTimeOut" | 
    Select-Object Entity, Value
# CIS recommends: 600 (10 minutes)
```

#### 2.1.3 Logging Controls

**Control 3.1 — Configure persistent logging**

ESXi logs must survive reboots — configure a syslog target or persistent scratch partition:

```powershell
Get-VMHost | ForEach-Object {
    $syslog = $_ | Get-AdvancedSetting -Name "Syslog.global.logHost"
    $logDir = $_ | Get-AdvancedSetting -Name "Syslog.global.logDir"
    [PSCustomObject]@{
        Host      = $_.Name
        LogHost   = $syslog.Value
        LogDir    = $logDir.Value
    }
}
# LogHost should be: "tcp://siem.corp.local:514" or "ssl://siem.corp.local:6514"
```

Remediation:
```powershell
Get-VMHost | ForEach-Object {
    $_ | Set-AdvancedSetting -Name "Syslog.global.logHost" `
         -Value "ssl://siem.corp.local:6514" -Confirm:$false
}
# Open firewall for syslog
Get-VMHost | ForEach-Object {
    $esxcli = Get-EsxCli -VMHost $_ -V2
    $esxcli.network.firewall.ruleset.set.Invoke(@{enabled=$true; rulesetid="syslog"})
}
```

**Control 3.2 — Configure log level to info**

```powershell
Get-VMHost | Get-AdvancedSetting -Name "Config.HostAgent.log.level" |
    Select-Object Entity, Value
# Expected: "info"
```

**Control 3.3 — Audit record storage capacity**

Verify sufficient space for audit logs:
```powershell
Get-VMHost | ForEach-Object {
    $esxcli = Get-EsxCli -VMHost $_ -V2
    $scratch = $_ | Get-AdvancedSetting -Name "ScratchConfig.CurrentScratchLocation"
    [PSCustomObject]@{
        Host    = $_.Name
        Scratch = $scratch.Value
    }
}
```

#### 2.1.4 Access Controls

**Control 4.1 — Verify lockdown mode is enabled**

Lockdown mode restricts management to vCenter only — direct ESXi access is blocked:

```powershell
Get-VMHost | ForEach-Object {
    [PSCustomObject]@{
        Host         = $_.Name
        LockdownMode = (Get-View $_.Id).Config.LockdownMode
    }
}
# Values: lockdownDisabled | lockdownNormal | lockdownStrict
# CIS Level 1: lockdownNormal minimum
```

**Control 4.2 — Verify DCUI access users are limited**

```powershell
Get-VMHost | ForEach-Object {
    $dcuiUsers = $_ | Get-AdvancedSetting -Name "DCUI.Access"
    [PSCustomObject]@{
        Host  = $_.Name
        Users = $dcuiUsers.Value
    }
}
# Expected: "root" only (or documented exception list)
```

**Control 4.3 — Password complexity**

```powershell
Get-VMHost | Get-AdvancedSetting -Name "Security.PasswordQualityControl" |
    Select-Object Entity, Value
# CIS recommends: "retry=3 min=disabled,disabled,disabled,disabled,15"
# This requires 15-char passwords with mixed character classes
```

**Control 4.4 — Account lockout**

```powershell
Get-VMHost | Get-AdvancedSetting -Name "Security.AccountLockFailures" |
    Select-Object Entity, Value
# CIS: 5 (lock after 5 failed attempts)

Get-VMHost | Get-AdvancedSetting -Name "Security.AccountUnlockTime" |
    Select-Object Entity, Value
# CIS: 900 (15 minutes)
```

**Control 4.5 — Active Directory integration (if applicable)**

```powershell
Get-VMHost | ForEach-Object {
    $authConfig = (Get-View $_.Id).Config.AuthenticationManagerInfo.AuthConfig
    [PSCustomObject]@{
        Host     = $_.Name
        ADJoined = ($authConfig | Where-Object { $_.GetType().Name -match "ActiveDirectory" }) -ne $null
    }
}
```

#### 2.1.5 Console Controls

**Control 5.1 — Shell timeout**

```powershell
Get-VMHost | Get-AdvancedSetting -Name "UserVars.ESXiShellInteractiveTimeOut" |
    Select-Object Entity, Value
# CIS: 900 (15 minutes)
```

**Control 5.2 — Shell session timeout**

```powershell
Get-VMHost | Get-AdvancedSetting -Name "UserVars.ESXiShellTimeOut" |
    Select-Object Entity, Value
# CIS: 900 seconds
```

**Control 5.3 — DCUI access restriction during lockdown**

When lockdown mode is Normal, DCUI remains accessible for emergency access. Strict lockdown disables it entirely. Document the justification for the chosen level.

#### 2.1.6 Storage Controls

**Control 6.1 — iSCSI CHAP authentication**

```powershell
Get-VMHost | ForEach-Object {
    $hbas = $_ | Get-VMHostHba -Type iScsi
    foreach ($hba in $hbas) {
        [PSCustomObject]@{
            Host           = $_.Name
            HBA            = $hba.Device
            ChapType       = $hba.AuthenticationProperties.ChapType
            MutualChapType = $hba.AuthenticationProperties.MutualChapType
        }
    }
}
# CIS: ChapType should not be "chapProhibited"
```

**Control 6.2 — NFS access control**

Verify NFS datastores are restricted to ESXi host IPs only at the storage array level. This is verified externally but must be documented as part of the audit.

#### 2.1.7 vNetwork Controls

**Control 7.1 — Reject forged transmits**

```powershell
Get-VMHost | ForEach-Object {
    $vSwitches = $_ | Get-VirtualSwitch -Standard
    foreach ($vs in $vSwitches) {
        [PSCustomObject]@{
            Host           = $_.Name
            vSwitch        = $vs.Name
            ForgedTransmit = $vs.ExtensionData.Spec.Policy.Security.ForgedTransmits
        }
    }
}
# CIS: ForgedTransmits = $false (Reject)
```

**Control 7.2 — Reject MAC address changes**

```powershell
Get-VMHost | Get-VirtualSwitch -Standard | ForEach-Object {
    [PSCustomObject]@{
        vSwitch          = $_.Name
        MacChanges       = $_.ExtensionData.Spec.Policy.Security.MacChanges
    }
}
# CIS: MacChanges = $false (Reject)
```

**Control 7.3 — Reject promiscuous mode**

```powershell
Get-VMHost | Get-VirtualSwitch -Standard | ForEach-Object {
    [PSCustomObject]@{
        vSwitch         = $_.Name
        PromiscuousMode = $_.ExtensionData.Spec.Policy.Security.AllowPromiscuous
    }
}
# CIS: AllowPromiscuous = $false (Reject)
```

**Control 7.4 — Limit VGT (VLAN 4095) usage**

VLAN trunking to VMs (VLAN ID 4095) should be restricted to specific use cases (nested hypervisors, virtual appliances) with documented justification.

### 2.2 Automating CIS Checks with PowerCLI

Complete automation script for CIS assessment:

```powershell
#Requires -Modules VMware.VimAutomation.Core

<#
.SYNOPSIS
    CIS ESXi 8.0 Benchmark Automated Assessment
.DESCRIPTION
    Evaluates all ESXi hosts against CIS Benchmark v1.1.0
    Generates JSON report for evidence and CSV for tracking
#>

param(
    [Parameter(Mandatory)]
    [string]$vCenterServer,
    
    [Parameter(Mandatory)]
    [PSCredential]$Credential,
    
    [string]$OutputPath = "./cis-report-$(Get-Date -Format 'yyyy-MM-dd')",
    
    [string[]]$ExcludeHosts = @()
)

# Connect
Connect-VIServer -Server $vCenterServer -Credential $Credential -ErrorAction Stop

$results = @()
$hosts = Get-VMHost | Where-Object { $_.Name -notin $ExcludeHosts }

foreach ($vmhost in $hosts) {
    $esxcli = Get-EsxCli -VMHost $vmhost -V2
    
    # Control 2.2 - SSH Disabled
    $ssh = $vmhost | Get-VMHostService | Where-Object { $_.Key -eq "TSM-SSH" }
    $results += [PSCustomObject]@{
        Host       = $vmhost.Name
        ControlID  = "2.2"
        Control    = "SSH Service Disabled"
        Status     = if (-not $ssh.Running) { "PASS" } else { "FAIL" }
        Finding    = "SSH Running: $($ssh.Running), Policy: $($ssh.Policy)"
        Severity   = "HIGH"
        Category   = "Communication"
    }
    
    # Control 2.3 - ESXi Shell Disabled
    $shell = $vmhost | Get-VMHostService | Where-Object { $_.Key -eq "TSM" }
    $results += [PSCustomObject]@{
        Host       = $vmhost.Name
        ControlID  = "2.3"
        Control    = "ESXi Shell Disabled"
        Status     = if (-not $shell.Running) { "PASS" } else { "FAIL" }
        Finding    = "Shell Running: $($shell.Running), Policy: $($shell.Policy)"
        Severity   = "HIGH"
        Category   = "Communication"
    }
    
    # Control 3.1 - Syslog Configured
    $syslog = $vmhost | Get-AdvancedSetting -Name "Syslog.global.logHost"
    $results += [PSCustomObject]@{
        Host       = $vmhost.Name
        ControlID  = "3.1"
        Control    = "Remote Syslog Configured"
        Status     = if ($syslog.Value) { "PASS" } else { "FAIL" }
        Finding    = "LogHost: $($syslog.Value)"
        Severity   = "HIGH"
        Category   = "Logging"
    }
    
    # Control 4.1 - Lockdown Mode
    $lockdown = (Get-View $vmhost.Id).Config.LockdownMode
    $results += [PSCustomObject]@{
        Host       = $vmhost.Name
        ControlID  = "4.1"
        Control    = "Lockdown Mode Enabled"
        Status     = if ($lockdown -ne "lockdownDisabled") { "PASS" } else { "FAIL" }
        Finding    = "LockdownMode: $lockdown"
        Severity   = "CRITICAL"
        Category   = "Access"
    }
    
    # Control 4.4 - Account Lockout
    $lockFailures = $vmhost | Get-AdvancedSetting -Name "Security.AccountLockFailures"
    $results += [PSCustomObject]@{
        Host       = $vmhost.Name
        ControlID  = "4.4"
        Control    = "Account Lockout Configured"
        Status     = if ($lockFailures.Value -le 5 -and $lockFailures.Value -gt 0) { "PASS" } else { "FAIL" }
        Finding    = "AccountLockFailures: $($lockFailures.Value)"
        Severity   = "HIGH"
        Category   = "Access"
    }
    
    # Control 7.1 - Forged Transmits
    $vSwitches = $vmhost | Get-VirtualSwitch -Standard -ErrorAction SilentlyContinue
    foreach ($vs in $vSwitches) {
        $forged = $vs.ExtensionData.Spec.Policy.Security.ForgedTransmits
        $results += [PSCustomObject]@{
            Host       = $vmhost.Name
            ControlID  = "7.1"
            Control    = "Reject Forged Transmits ($($vs.Name))"
            Status     = if (-not $forged) { "PASS" } else { "FAIL" }
            Finding    = "ForgedTransmits: $forged"
            Severity   = "MEDIUM"
            Category   = "vNetwork"
        }
    }
}

# Export results
$results | Export-Csv -Path "$OutputPath.csv" -NoTypeInformation
$results | ConvertTo-Json -Depth 3 | Out-File "$OutputPath.json"

# Summary
$summary = $results | Group-Object Status | Select-Object Name, Count
Write-Host "`n=== CIS Assessment Summary ===" -ForegroundColor Cyan
$summary | Format-Table -AutoSize

Write-Host "`nCritical Failures:" -ForegroundColor Red
$results | Where-Object { $_.Status -eq "FAIL" -and $_.Severity -eq "CRITICAL" } |
    Format-Table Host, ControlID, Control -AutoSize

Disconnect-VIServer -Confirm:$false
```

### 2.3 Automating CIS Checks with Chef InSpec

InSpec profile for ESXi CIS assessment (runs against ESXi via SSH or PowerCLI transport):

```ruby
# inspec.yml
name: cis-esxi-8
title: CIS VMware ESXi 8.0 Benchmark
version: 1.1.0
supports:
  - platform: vmware
  - platform: linux

# controls/communication.rb
control 'cis-esxi-2.2' do
  impact 0.7
  title 'Ensure SSH service is disabled'
  desc 'SSH should be disabled on ESXi hosts when not actively needed for maintenance.'
  tag cis_id: '2.2'
  tag cis_level: 1
  tag severity: 'high'
  
  describe command('esxcli system maintenanceMode get') do
    # If in maintenance mode, SSH may be acceptable
  end
  
  describe command('chkconfig --list | grep SSH') do
    its('stdout') { should match /off/ }
  end
end

control 'cis-esxi-2.4' do
  impact 0.8
  title 'Ensure TLS 1.2 or higher is enforced'
  desc 'Older TLS versions contain known vulnerabilities.'
  tag cis_id: '2.4'
  tag cis_level: 1
  
  describe command('esxcli system settings advanced list -o /UserVars/ESXiVPsDisabledProtocols') do
    its('stdout') { should match /sslv3,tlsv1,tlsv1.1/ }
  end
end

control 'cis-esxi-3.1' do
  impact 0.7
  title 'Ensure remote syslog is configured'
  desc 'Logs must be forwarded to a central log server for integrity and availability.'
  tag cis_id: '3.1'
  tag cis_level: 1
  
  describe command('esxcli system syslog config get') do
    its('stdout') { should match /Remote Host.*:.*\d+/ }
  end
end

control 'cis-esxi-4.1' do
  impact 0.9
  title 'Ensure lockdown mode is enabled'
  desc 'Lockdown mode forces all management through vCenter, preventing direct host access.'
  tag cis_id: '4.1'
  tag cis_level: 1
  
  describe command('vim-cmd vimsvc/auth/lockdown_is_enabled') do
    its('stdout') { should match /true/ }
  end
end

control 'cis-esxi-7.1' do
  impact 0.5
  title 'Ensure forged transmits are rejected'
  desc 'Prevents VMs from sending frames with spoofed source MAC addresses.'
  tag cis_id: '7.1'
  tag cis_level: 1
  
  describe command('esxcli network vswitch standard policy security get --vswitch-name=vSwitch0') do
    its('stdout') { should match /Forged Transmits: false/ }
  end
end
```

### 2.4 Proxmox Hardening — Mapping CIS Linux Benchmark

Since no Proxmox-specific CIS benchmark exists, map the CIS Debian 12 Benchmark to Proxmox, accounting for Proxmox-specific services:

**Ansible playbook for Proxmox CIS hardening assessment:**

```yaml
---
# playbook: proxmox-cis-audit.yml
# Maps CIS Debian 12 Benchmark to Proxmox VE 8.x
# Skips controls that would break Proxmox functionality

- name: Proxmox VE CIS Compliance Audit
  hosts: proxmox_nodes
  become: true
  gather_facts: true
  vars:
    audit_timestamp: "{{ ansible_date_time.iso8601 }}"
    report_dir: "/tmp/cis-audit-{{ audit_timestamp }}"
    
  tasks:
    - name: Create report directory
      ansible.builtin.file:
        path: "{{ report_dir }}"
        state: directory
        mode: '0700'

    # Section 1: Filesystem Configuration
    - name: "1.1.1 | Check cramfs disabled"
      ansible.builtin.shell: |
        modprobe -n -v cramfs 2>&1 | grep -q "install /bin/true" && echo "PASS" || echo "FAIL"
      register: cramfs_check
      changed_when: false

    - name: "1.1.2 | Check /tmp separate partition"
      ansible.builtin.shell: |
        findmnt /tmp > /dev/null 2>&1 && echo "PASS" || echo "FAIL"
      register: tmp_partition
      changed_when: false

    # Section 3: Network Configuration
    - name: "3.1.1 | Check IP forwarding (NOTE: Required for Proxmox NAT/routed networking)"
      ansible.builtin.shell: |
        sysctl net.ipv4.ip_forward
      register: ip_forward
      changed_when: false
      # NOTE: ip_forward=1 is EXPECTED for Proxmox — do not remediate
      
    - name: "3.2.1 | Check source route acceptance"
      ansible.builtin.shell: |
        sysctl net.ipv4.conf.all.accept_source_route
      register: source_route
      changed_when: false

    # Section 4: Access Control
    - name: "4.1.1 | Check SSH Protocol version"
      ansible.builtin.shell: |
        grep -q "^Protocol 2" /etc/ssh/sshd_config 2>/dev/null || \
        (ssh -V 2>&1 | grep -q "OpenSSH_[89]" && echo "PASS_DEFAULT") || echo "FAIL"
      register: ssh_protocol
      changed_when: false

    - name: "4.1.2 | Check SSH root login"
      ansible.builtin.shell: |
        grep -E "^PermitRootLogin" /etc/ssh/sshd_config | grep -qi "no\|prohibit-password"
      register: ssh_root
      changed_when: false
      failed_when: false

    - name: "4.1.3 | Check SSH MaxAuthTries"
      ansible.builtin.shell: |
        grep -E "^MaxAuthTries" /etc/ssh/sshd_config | awk '{print $2}'
      register: ssh_maxauth
      changed_when: false

    # Section 5: Logging and Auditing
    - name: "5.1.1 | Check auditd is installed"
      ansible.builtin.dpkg_selections:
        name: auditd
      register: auditd_installed
      failed_when: false

    - name: "5.1.2 | Check auditd is running"
      ansible.builtin.systemd:
        name: auditd
      register: auditd_status
      failed_when: false

    - name: "5.2.1 | Check journald persistence"
      ansible.builtin.shell: |
        grep -q "^Storage=persistent" /etc/systemd/journald.conf && echo "PASS" || echo "FAIL"
      register: journal_persist
      changed_when: false

    # Proxmox-specific checks (beyond CIS Debian)
    - name: "PVE.1 | Check Proxmox subscription status"
      ansible.builtin.shell: |
        pvesubscription get 2>/dev/null | grep -q "status: active" && echo "ACTIVE" || echo "NO_SUB"
      register: pve_subscription
      changed_when: false

    - name: "PVE.2 | Check Proxmox firewall enabled (datacenter level)"
      ansible.builtin.shell: |
        cat /etc/pve/firewall/cluster.fw 2>/dev/null | grep -q "enable: 1" && echo "PASS" || echo "FAIL"
      register: pve_firewall_dc
      changed_when: false

    - name: "PVE.3 | Check Proxmox firewall enabled (node level)"
      ansible.builtin.shell: |
        cat /etc/pve/nodes/{{ ansible_hostname }}/host.fw 2>/dev/null | grep -q "enable: 1" && echo "PASS" || echo "FAIL"
      register: pve_firewall_node
      changed_when: false

    - name: "PVE.4 | Check 2FA enforcement"
      ansible.builtin.shell: |
        pveum realm list --output-format json | python3 -c "
        import sys, json
        realms = json.load(sys.stdin)
        for r in realms:
            if r.get('tfa', '') == '': 
                print(f\"WARN: Realm {r['realm']} has no 2FA requirement\")
        " 2>/dev/null || echo "CHECK_MANUAL"
      register: pve_2fa
      changed_when: false

    - name: "PVE.5 | Check TLS certificate validity"
      ansible.builtin.shell: |
        openssl x509 -in /etc/pve/nodes/{{ ansible_hostname }}/pve-ssl.pem \
          -noout -dates -checkend 2592000
      register: pve_cert
      changed_when: false
      failed_when: false

    - name: "PVE.6 | Check cluster communication encryption"
      ansible.builtin.shell: |
        grep -q "crypto_cipher:" /etc/corosync/corosync.conf && echo "PASS" || echo "FAIL"
      register: corosync_crypto
      changed_when: false

    # Generate consolidated report
    - name: Generate audit report
      ansible.builtin.template:
        src: cis-report.json.j2
        dest: "{{ report_dir }}/audit-results.json"
        mode: '0600'
```

### 2.5 Remediation Scripts for Common Findings

**Proxmox sysctl hardening (CIS Debian compliant, Proxmox-aware):**

```bash
#!/usr/bin/env bash
# proxmox-sysctl-harden.sh
# Applies CIS-recommended sysctl settings while preserving Proxmox functionality
# NOTE: ip_forward is intentionally left enabled for Proxmox networking

set -euo pipefail

SYSCTL_FILE="/etc/sysctl.d/99-cis-hardening.conf"

cat > "${SYSCTL_FILE}" << 'EOF'
# CIS Debian 12 Benchmark - Network Parameters (Proxmox-adapted)
# NOTE: net.ipv4.ip_forward=1 is required for Proxmox NAT/routed VMs

# 3.2.1 - Disable source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# 3.2.2 - Disable ICMP redirect acceptance
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# 3.2.3 - Disable secure ICMP redirect acceptance
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0

# 3.2.4 - Log suspicious packets
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# 3.2.5 - Disable ICMP broadcast echo (smurf protection)
net.ipv4.icmp_echo_ignore_broadcasts = 1

# 3.2.6 - Ignore bogus ICMP responses
net.ipv4.icmp_ignore_bogus_error_responses = 1

# 3.2.7 - Enable Reverse Path Filtering
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# 3.2.8 - Enable TCP SYN Cookies
net.ipv4.tcp_syncookies = 1

# 3.2.9 - Disable IPv6 router advertisements
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0

# Memory protections
kernel.randomize_va_space = 2
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2

# File descriptor limits for Proxmox services
fs.file-max = 2097152
EOF

sysctl --system
echo "[OK] Sysctl hardening applied. Verify with: sysctl --all | grep -E 'accept_source|redirect|log_martians'"
```

---

## 3. VMware STIG Compliance

### 3.1 DISA STIG for vSphere — Overview

The Defense Information Systems Agency (DISA) publishes Security Technical Implementation Guides (STIGs) for vSphere components:

| STIG | Current Version | Controls |
|---|---|---|
| VMware vSphere 8.0 ESXi | V1R1 (2024) | ~120 controls |
| VMware vCenter 8.0 | V1R1 (2024) | ~85 controls |
| VMware vSphere 8.0 VM | V1R1 (2024) | ~45 controls |
| VMware vSphere 8.0 vNetwork (DVS) | V1R1 (2024) | ~30 controls |

Severity categories (CAT):
- **CAT I (High)**: Vulnerability that could directly result in loss of confidentiality, integrity, or availability.
- **CAT II (Medium)**: Vulnerability that could result in degradation.
- **CAT III (Low)**: Vulnerability that degrades defense-in-depth measures.

### 3.2 STIG Viewer Workflow

The assessment workflow using STIG Viewer (now replaced by Vulcan/eMASS in DoD, but STIG Viewer remains common in commercial):

1. Import the vSphere 8 STIG XCCDF into STIG Viewer.
2. Create a checklist for each host/vCenter/VM category.
3. For each Vulnerability Discussion (VulnID):
   - Document the Finding Details (what you observed).
   - Record Status: Not a Finding / Open / Not Applicable / Not Reviewed.
   - If Open: record Comments with remediation plan and timeline.
4. Export completed checklists as `.ckl` files for evidence.
5. Aggregate results into a POA&M (Plan of Action and Milestones).

### 3.3 PowerCLI STIG Compliance Scripts

Automated STIG assessment covering key CAT I and CAT II findings:

```powershell
#Requires -Modules VMware.VimAutomation.Core

<#
.SYNOPSIS
    DISA STIG Assessment for vSphere 8.0 ESXi
.DESCRIPTION
    Automates assessment of CAT I, II, and III findings for ESXi STIG V1R1.
    Produces machine-readable output for POA&M tracking.
#>

param(
    [Parameter(Mandatory)]
    [string]$vCenterServer,
    [PSCredential]$Credential,
    [string]$OutputDir = "./stig-assessment-$(Get-Date -Format 'yyyy-MM-dd')"
)

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
Connect-VIServer -Server $vCenterServer -Credential $Credential

$findings = @()

foreach ($vmhost in (Get-VMHost)) {
    $esxcli = Get-EsxCli -VMHost $vmhost -V2
    $hostView = Get-View $vmhost.Id
    
    # ESXI-80-000001 (CAT II) - Lockdown mode
    $lockdown = $hostView.Config.LockdownMode
    $findings += [PSCustomObject]@{
        VulnID      = "V-ESXI-80-000001"
        Severity    = "CAT II"
        Host        = $vmhost.Name
        Title       = "ESXi host must enable lockdown mode"
        Status      = if ($lockdown -ne "lockdownDisabled") { "NotAFinding" } else { "Open" }
        FindDetails = "LockdownMode: $lockdown"
        CheckCmd    = '(Get-View (Get-VMHost).Id).Config.LockdownMode'
    }
    
    # ESXI-80-000002 (CAT I) - SSH must be disabled
    $ssh = $vmhost | Get-VMHostService | Where-Object { $_.Key -eq "TSM-SSH" }
    $findings += [PSCustomObject]@{
        VulnID      = "V-ESXI-80-000002"
        Severity    = "CAT I"
        Host        = $vmhost.Name
        Title       = "SSH must not be running unless needed for troubleshooting"
        Status      = if (-not $ssh.Running) { "NotAFinding" } else { "Open" }
        FindDetails = "SSH Running: $($ssh.Running), Policy: $($ssh.Policy)"
        CheckCmd    = 'Get-VMHostService | Where Key -eq "TSM-SSH"'
    }
    
    # ESXI-80-000005 (CAT II) - Syslog must be configured
    $logHost = ($vmhost | Get-AdvancedSetting -Name "Syslog.global.logHost").Value
    $findings += [PSCustomObject]@{
        VulnID      = "V-ESXI-80-000005"
        Severity    = "CAT II"
        Host        = $vmhost.Name
        Title       = "ESXi must forward logs to central log server"
        Status      = if ($logHost) { "NotAFinding" } else { "Open" }
        FindDetails = "Syslog.global.logHost: $logHost"
        CheckCmd    = 'Get-AdvancedSetting -Name "Syslog.global.logHost"'
    }
    
    # ESXI-80-000010 (CAT I) - TLS enforcement
    $tlsDisabled = ($vmhost | Get-AdvancedSetting -Name "UserVars.ESXiVPsDisabledProtocols").Value
    $findings += [PSCustomObject]@{
        VulnID      = "V-ESXI-80-000010"
        Severity    = "CAT I"
        Host        = $vmhost.Name
        Title       = "ESXi must disable TLS 1.0 and 1.1"
        Status      = if ($tlsDisabled -match "tlsv1,tlsv1.1|tlsv1.1,tlsv1") { "NotAFinding" } else { "Open" }
        FindDetails = "DisabledProtocols: $tlsDisabled"
        CheckCmd    = 'Get-AdvancedSetting -Name "UserVars.ESXiVPsDisabledProtocols"'
    }
    
    # ESXI-80-000015 (CAT II) - NTP configured
    $ntpRunning = ($vmhost | Get-VMHostService | Where-Object { $_.Key -eq "ntpd" }).Running
    $ntpServers = $vmhost | Get-VMHostNtpServer
    $findings += [PSCustomObject]@{
        VulnID      = "V-ESXI-80-000015"
        Severity    = "CAT II"
        Host        = $vmhost.Name
        Title       = "ESXi must synchronize time with authoritative source"
        Status      = if ($ntpRunning -and $ntpServers) { "NotAFinding" } else { "Open" }
        FindDetails = "NTP Running: $ntpRunning, Servers: $($ntpServers -join ',')"
        CheckCmd    = 'Get-VMHostNtpServer; Get-VMHostService | Where Key -eq "ntpd"'
    }
    
    # ESXI-80-000020 (CAT II) - Password complexity
    $pwdQuality = ($vmhost | Get-AdvancedSetting -Name "Security.PasswordQualityControl").Value
    $findings += [PSCustomObject]@{
        VulnID      = "V-ESXI-80-000020"
        Severity    = "CAT II"
        Host        = $vmhost.Name
        Title       = "ESXi must enforce password complexity"
        Status      = if ($pwdQuality -match "min=.*15") { "NotAFinding" } else { "Open" }
        FindDetails = "PasswordQualityControl: $pwdQuality"
        CheckCmd    = 'Get-AdvancedSetting -Name "Security.PasswordQualityControl"'
    }
    
    # ESXI-80-000030 (CAT II) - SNMP configured securely
    $snmpEnabled = $esxcli.system.snmp.get.Invoke().Enable
    $findings += [PSCustomObject]@{
        VulnID      = "V-ESXI-80-000030"
        Severity    = "CAT II"
        Host        = $vmhost.Name
        Title       = "SNMP must be configured securely or disabled"
        Status      = if (-not $snmpEnabled) { "NotAFinding" } else { "Open" }
        FindDetails = "SNMP Enabled: $snmpEnabled"
        CheckCmd    = '(Get-EsxCli -V2).system.snmp.get.Invoke().Enable'
    }
    
    # ESXI-80-000035 (CAT II) - Forged transmits rejected on all switches
    $vSwitches = $vmhost | Get-VirtualSwitch
    foreach ($vs in $vSwitches) {
        $policy = $vs.ExtensionData.Spec.Policy.Security
        if ($policy) {
            $findings += [PSCustomObject]@{
                VulnID      = "V-ESXI-80-000035"
                Severity    = "CAT II"
                Host        = $vmhost.Name
                Title       = "Forged transmits must be rejected ($($vs.Name))"
                Status      = if (-not $policy.ForgedTransmits) { "NotAFinding" } else { "Open" }
                FindDetails = "vSwitch: $($vs.Name), ForgedTransmits: $($policy.ForgedTransmits)"
                CheckCmd    = 'Get-VirtualSwitch | Select ExtensionData.Spec.Policy.Security'
            }
        }
    }
}

# vCenter STIG checks
$vcView = Get-View ServiceInstance
$vcSettings = (Get-View $vcView.Content.Setting).Setting

# VC-80-000001 (CAT II) - Session timeout
$sessionTimeout = ($vcSettings | Where-Object { $_.Key -eq "etc.issue" }).Value
$findings += [PSCustomObject]@{
    VulnID      = "V-VC-80-000001"
    Severity    = "CAT II"
    Host        = $vCenterServer
    Title       = "vCenter session timeout must be configured"
    Status      = "ManualReview"
    FindDetails = "Check vSphere Client timeout settings in Administration > Client Configuration"
    CheckCmd    = "Manual verification required"
}

# Export
$findings | Export-Csv "$OutputDir/stig-findings.csv" -NoTypeInformation
$findings | ConvertTo-Json -Depth 5 | Out-File "$OutputDir/stig-findings.json"

# Summary
$catSummary = $findings | Group-Object Severity | ForEach-Object {
    $open = ($_.Group | Where-Object Status -eq "Open").Count
    $pass = ($_.Group | Where-Object Status -eq "NotAFinding").Count
    [PSCustomObject]@{
        Category  = $_.Name
        Total     = $_.Count
        Open      = $open
        Pass      = $pass
        Compliant = "{0:P1}" -f ($pass / [math]::Max($_.Count, 1))
    }
}

Write-Host "`n=== STIG Assessment Summary ===" -ForegroundColor Cyan
$catSummary | Format-Table -AutoSize

Write-Host "`nCAT I Open Findings (Immediate Action Required):" -ForegroundColor Red
$findings | Where-Object { $_.Severity -eq "CAT I" -and $_.Status -eq "Open" } |
    Format-Table VulnID, Host, Title -AutoSize

Disconnect-VIServer -Confirm:$false
```

### 3.4 STIG Remediation Playbooks

Ansible playbook for automated STIG remediation of common findings:

```yaml
---
# playbook: esxi-stig-remediate.yml
# Remediates common CAT I and CAT II STIG findings via PowerCLI
# Requires: community.vmware collection

- name: ESXi STIG Remediation
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    vcenter_hostname: "{{ lookup('env', 'VCENTER_HOST') }}"
    vcenter_username: "{{ lookup('env', 'VCENTER_USER') }}"
    vcenter_password: "{{ lookup('env', 'VCENTER_PASS') }}"
    validate_certs: true
    
    # STIG-compliant values
    stig_syslog_host: "ssl://siem.corp.local:6514"
    stig_ntp_servers:
      - "10.0.1.10"
      - "10.0.1.11"
    stig_password_quality: "retry=3 min=disabled,disabled,disabled,disabled,15"
    stig_account_lock_failures: 3
    stig_account_unlock_time: 900
    stig_shell_timeout: 600
    stig_dcui_timeout: 600
    
  tasks:
    - name: Get all ESXi hosts
      community.vmware.vmware_host_facts:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: "{{ validate_certs }}"
      register: esxi_hosts
      delegate_to: localhost

    - name: "STIG V-ESXI-80-000002 | Disable SSH service"
      community.vmware.vmware_host_service_manager:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: "{{ validate_certs }}"
        esxi_hostname: "{{ item }}"
        service_name: TSM-SSH
        state: stopped
        service_policy: off
      loop: "{{ groups['esxi_hosts'] }}"
      tags: [cat1, ssh]

    - name: "STIG V-ESXI-80-000005 | Configure syslog"
      community.vmware.vmware_host_config_manager:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: "{{ validate_certs }}"
        esxi_hostname: "{{ item }}"
        options:
          'Syslog.global.logHost': "{{ stig_syslog_host }}"
      loop: "{{ groups['esxi_hosts'] }}"
      tags: [cat2, logging]

    - name: "STIG V-ESXI-80-000010 | Disable weak TLS"
      community.vmware.vmware_host_config_manager:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: "{{ validate_certs }}"
        esxi_hostname: "{{ item }}"
        options:
          'UserVars.ESXiVPsDisabledProtocols': "sslv3,tlsv1,tlsv1.1"
      loop: "{{ groups['esxi_hosts'] }}"
      tags: [cat1, tls]

    - name: "STIG V-ESXI-80-000020 | Set password complexity"
      community.vmware.vmware_host_config_manager:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: "{{ validate_certs }}"
        esxi_hostname: "{{ item }}"
        options:
          'Security.PasswordQualityControl': "{{ stig_password_quality }}"
          'Security.AccountLockFailures': "{{ stig_account_lock_failures }}"
          'Security.AccountUnlockTime': "{{ stig_account_unlock_time }}"
      loop: "{{ groups['esxi_hosts'] }}"
      tags: [cat2, access]

    - name: "STIG V-ESXI-80-000025 | Set shell timeout"
      community.vmware.vmware_host_config_manager:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: "{{ validate_certs }}"
        esxi_hostname: "{{ item }}"
        options:
          'UserVars.ESXiShellInteractiveTimeOut': "{{ stig_shell_timeout }}"
          'UserVars.ESXiShellTimeOut': "{{ stig_shell_timeout }}"
          'UserVars.DcuiTimeOut': "{{ stig_dcui_timeout }}"
      loop: "{{ groups['esxi_hosts'] }}"
      tags: [cat2, console]
```

### 3.5 Exemption Documentation for Inapplicable Controls

Not all STIG controls apply to every environment. Formal exemption documentation requires:

```
STIG Exemption Documentation Template
======================================
VulnID:           V-ESXI-80-000045
Title:            ESXi host must configure bidirectional CHAP for iSCSI
Severity:         CAT II
Status:           Not Applicable

Justification:
This environment uses NFS datastores exclusively. No iSCSI storage 
adapters are configured on any ESXi host. The storage architecture 
document (REF: SA-2024-003) confirms NFS-only design.

Evidence:
- PowerCLI output showing no iSCSI HBAs: [attached]
- Storage architecture diagram: [reference]
- Date verified: 2026-05-07

Approver:         [Security Lead Name]
Approval Date:    [Date]
Review Interval:  Annual (or upon storage architecture change)
```

---

## 4. Audit Evidence Collection

### 4.1 Automated Evidence Gathering Scripts

Evidence collection must be repeatable, timestamped, and integrity-verified. The following script collects comprehensive configuration evidence:

```bash
#!/usr/bin/env bash
# evidence-collector-proxmox.sh
# Collects audit evidence from Proxmox VE nodes
# Run as root on each node or via Ansible

set -euo pipefail

EVIDENCE_DIR="/var/audit-evidence/$(date +%Y-%m-%d_%H%M%S)"
HOSTNAME=$(hostname -f)
MANIFEST="${EVIDENCE_DIR}/manifest.sha256"

mkdir -p "${EVIDENCE_DIR}"/{config,access,network,storage,logs,services}

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${EVIDENCE_DIR}/collection.log"; }

log "Starting evidence collection on ${HOSTNAME}"

# ---- Configuration Evidence ----
log "Collecting configuration evidence"

# Proxmox cluster configuration
cp -r /etc/pve/ "${EVIDENCE_DIR}/config/pve/" 2>/dev/null || log "WARN: /etc/pve not accessible"

# Node-specific configs
cp /etc/network/interfaces "${EVIDENCE_DIR}/config/network-interfaces" 2>/dev/null || true
cp /etc/hosts "${EVIDENCE_DIR}/config/hosts"
cp /etc/resolv.conf "${EVIDENCE_DIR}/config/resolv.conf"
sysctl -a > "${EVIDENCE_DIR}/config/sysctl-all.txt" 2>/dev/null
ss -tlnp > "${EVIDENCE_DIR}/config/listening-ports.txt"
systemctl list-units --type=service --state=running > "${EVIDENCE_DIR}/config/running-services.txt"
dpkg -l > "${EVIDENCE_DIR}/config/installed-packages.txt"
cat /etc/apt/sources.list /etc/apt/sources.list.d/* > "${EVIDENCE_DIR}/config/apt-sources.txt" 2>/dev/null || true

# ---- Access Control Evidence ----
log "Collecting access control evidence"

# User and group information
pveum user list --output-format json > "${EVIDENCE_DIR}/access/pveum-users.json" 2>/dev/null || true
pveum group list --output-format json > "${EVIDENCE_DIR}/access/pveum-groups.json" 2>/dev/null || true
pveum role list --output-format json > "${EVIDENCE_DIR}/access/pveum-roles.json" 2>/dev/null || true
pveum acl list --output-format json > "${EVIDENCE_DIR}/access/pveum-acls.json" 2>/dev/null || true
pveum realm list --output-format json > "${EVIDENCE_DIR}/access/pveum-realms.json" 2>/dev/null || true

# API tokens
pveum user token list --output-format json > "${EVIDENCE_DIR}/access/api-tokens.json" 2>/dev/null || true

# SSH authorized keys
for user_home in /root /home/*; do
    if [ -f "${user_home}/.ssh/authorized_keys" ]; then
        username=$(basename "${user_home}")
        cp "${user_home}/.ssh/authorized_keys" "${EVIDENCE_DIR}/access/ssh-keys-${username}.txt"
    fi
done

# PAM configuration
cp /etc/pam.d/common-auth "${EVIDENCE_DIR}/access/pam-common-auth" 2>/dev/null || true
cp /etc/pam.d/sshd "${EVIDENCE_DIR}/access/pam-sshd" 2>/dev/null || true

# ---- Network Evidence ----
log "Collecting network evidence"

ip addr show > "${EVIDENCE_DIR}/network/ip-addresses.txt"
ip route show > "${EVIDENCE_DIR}/network/routes.txt"
bridge -j link show > "${EVIDENCE_DIR}/network/bridges.json" 2>/dev/null || true
cat /etc/pve/firewall/cluster.fw > "${EVIDENCE_DIR}/network/firewall-cluster.txt" 2>/dev/null || true
cat "/etc/pve/nodes/${HOSTNAME}/host.fw" > "${EVIDENCE_DIR}/network/firewall-node.txt" 2>/dev/null || true
iptables-save > "${EVIDENCE_DIR}/network/iptables.txt" 2>/dev/null || true
nft list ruleset > "${EVIDENCE_DIR}/network/nftables.txt" 2>/dev/null || true

# ---- Storage Evidence ----
log "Collecting storage evidence"

pvesm status --output-format json > "${EVIDENCE_DIR}/storage/storage-status.json" 2>/dev/null || true
cat /etc/pve/storage.cfg > "${EVIDENCE_DIR}/storage/storage-config.txt" 2>/dev/null || true
zpool list -v > "${EVIDENCE_DIR}/storage/zpool-list.txt" 2>/dev/null || true
ceph -s > "${EVIDENCE_DIR}/storage/ceph-status.txt" 2>/dev/null || true
df -h > "${EVIDENCE_DIR}/storage/disk-usage.txt"
lsblk -f > "${EVIDENCE_DIR}/storage/block-devices.txt"

# ---- Log Samples ----
log "Collecting log samples (last 24h)"

journalctl --since "24 hours ago" -u pveproxy > "${EVIDENCE_DIR}/logs/pveproxy-24h.log" 2>/dev/null || true
journalctl --since "24 hours ago" -u pvedaemon > "${EVIDENCE_DIR}/logs/pvedaemon-24h.log" 2>/dev/null || true
journalctl --since "24 hours ago" -u corosync > "${EVIDENCE_DIR}/logs/corosync-24h.log" 2>/dev/null || true
journalctl --since "24 hours ago" -t sshd > "${EVIDENCE_DIR}/logs/sshd-24h.log" 2>/dev/null || true

# Auth log
if [ -f /var/log/auth.log ]; then
    tail -5000 /var/log/auth.log > "${EVIDENCE_DIR}/logs/auth-recent.log"
fi

# ---- Generate Integrity Manifest ----
log "Generating integrity manifest"

find "${EVIDENCE_DIR}" -type f ! -name "manifest.sha256" -exec sha256sum {} \; > "${MANIFEST}"

# Sign the manifest if GPG key available
if gpg --list-keys "audit@corp.local" &>/dev/null; then
    gpg --detach-sign --armor --default-key "audit@corp.local" "${MANIFEST}"
    log "Manifest signed with GPG"
fi

log "Evidence collection complete: ${EVIDENCE_DIR}"
echo "Total files collected: $(find "${EVIDENCE_DIR}" -type f | wc -l)"
echo "Manifest: ${MANIFEST}"
```

### 4.2 Screenshot Automation for GUI-Based Evidence

Some audit requirements demand visual evidence of GUI configuration. Automate with headless browsers:

```python
#!/usr/bin/env python3
"""
screenshot_audit.py
Automated screenshot collection for Proxmox VE GUI audit evidence.
Uses Playwright for reliable headless browser automation.
"""

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

# Configuration - load from environment in production
PROXMOX_URL = "https://proxmox.corp.local:8006"
PROXMOX_USER = "audit@pam"  # Dedicated audit account with read-only role
PROXMOX_PASS = ""  # Load from vault, never hardcode
EVIDENCE_DIR = Path(f"./gui-evidence/{datetime.now(timezone.utc).strftime('%Y-%m-%d')}")

SCREENSHOTS = [
    {"name": "datacenter-permissions", "nav": "#pveDatacenter-Permissions", "desc": "Datacenter-level permission assignments"},
    {"name": "firewall-datacenter", "nav": "#pveDatacenter-Firewall", "desc": "Datacenter firewall rules"},
    {"name": "ha-status", "nav": "#pveDatacenter-HA", "desc": "High Availability configuration"},
    {"name": "storage-config", "nav": "#pveDatacenter-Storage", "desc": "Storage configuration"},
    {"name": "replication-status", "nav": "#pveDatacenter-Replication", "desc": "Storage replication status"},
    {"name": "cluster-status", "nav": "#pveDatacenter-Summary", "desc": "Cluster summary and health"},
]


async def collect_screenshots():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,  # Self-signed certs in lab
        )
        page = await context.new_page()

        # Login
        await page.goto(PROXMOX_URL)
        await page.fill('input[name="username"]', PROXMOX_USER)
        await page.fill('input[name="password"]', PROXMOX_PASS)
        await page.click('button:has-text("Login")')
        await page.wait_for_load_state("networkidle")

        for shot in SCREENSHOTS:
            try:
                await page.click(f'[id*="{shot["nav"].lstrip("#")}"]', timeout=5000)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(1)  # Allow rendering

                filepath = EVIDENCE_DIR / f"{shot['name']}.png"
                await page.screenshot(path=str(filepath), full_page=False)

                # Calculate hash for integrity
                file_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
                manifest.append({
                    "filename": shot["name"] + ".png",
                    "description": shot["desc"],
                    "sha256": file_hash,
                    "captured_utc": datetime.now(timezone.utc).isoformat(),
                    "url": PROXMOX_URL,
                })
                print(f"[OK] {shot['name']}")
            except Exception as e:
                print(f"[FAIL] {shot['name']}: {e}")
                manifest.append({
                    "filename": shot["name"] + ".png",
                    "description": shot["desc"],
                    "error": str(e),
                    "captured_utc": datetime.now(timezone.utc).isoformat(),
                })

        await browser.close()

    # Write manifest
    manifest_path = EVIDENCE_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest written: {manifest_path}")


if __name__ == "__main__":
    asyncio.run(collect_screenshots())
```

### 4.3 Log Collection and Integrity

**Syslog forwarding with hash verification architecture:**

```
┌─────────────────┐     TLS/mTLS      ┌──────────────────┐     Immutable     ┌─────────────────┐
│   ESXi Hosts    │──────────────────→ │  Log Collector   │──────────────────→│  WORM Storage   │
│   Proxmox Nodes │                    │  (rsyslog/vector)│                   │  (S3 Object     │
│   vCenter       │                    │                  │                   │   Lock/ZFS)     │
└─────────────────┘                    └──────┬───────────┘                   └─────────────────┘
                                              │
                                              │ Hash chain
                                              ▼
                                       ┌──────────────────┐
                                       │  SIEM / Elastic  │
                                       │  (correlation +  │
                                       │   alerting)      │
                                       └──────────────────┘
```

**rsyslog configuration for integrity-preserving log collection:**

```
# /etc/rsyslog.d/50-audit-integrity.conf
# Receives logs and maintains hash chain for tamper detection

module(load="imtcp")
module(load="imrelp")  # Reliable Event Logging Protocol

# Accept TLS-encrypted syslog
input(type="imtcp" port="6514"
      ruleset="auditLogs"
      StreamDriver="gtls"
      StreamDriverMode="1"
      StreamDriverAuthMode="x509/certvalid"
      StreamDriverPermittedPeer=["*.corp.local"])

# Reliable transport option
input(type="imrelp" port="2514"
      ruleset="auditLogs"
      tls="on"
      tls.caCert="/etc/rsyslog.d/certs/ca.pem"
      tls.myCert="/etc/rsyslog.d/certs/collector.pem"
      tls.myPrivKey="/etc/rsyslog.d/certs/collector-key.pem")

ruleset(name="auditLogs") {
    # Write to file with hash per log line
    action(type="omfile"
           file="/var/log/audit-central/%HOSTNAME%/%$YEAR%-%$MONTH%-%$DAY%.log"
           fileCreateMode="0440"
           fileOwner="root"
           fileGroup="audit"
           template="RSYSLOG_SyslogProtocol23Format")
    
    # Forward to SIEM
    action(type="omfwd"
           target="siem.corp.local"
           port="514"
           protocol="tcp")
}
```

**Daily log integrity verification script:**

```bash
#!/usr/bin/env bash
# verify-log-integrity.sh
# Runs daily via cron to verify no log files were tampered with

LOG_BASE="/var/log/audit-central"
HASH_DB="/var/lib/audit/log-hashes.db"
ALERT_EMAIL="security-team@corp.local"

find "${LOG_BASE}" -name "*.log" -mtime -2 | while read -r logfile; do
    current_hash=$(sha256sum "${logfile}" | awk '{print $1}')
    stored_hash=$(sqlite3 "${HASH_DB}" "SELECT hash FROM log_hashes WHERE path='${logfile}' ORDER BY checked_at DESC LIMIT 1;")
    
    if [ -n "${stored_hash}" ] && [ "${current_hash}" != "${stored_hash}" ]; then
        echo "INTEGRITY VIOLATION: ${logfile}" | \
            mail -s "[CRITICAL] Log tampering detected" "${ALERT_EMAIL}"
    fi
    
    sqlite3 "${HASH_DB}" "INSERT INTO log_hashes (path, hash, checked_at) VALUES ('${logfile}', '${current_hash}', datetime('now'));"
done
```

### 4.4 Change Management Evidence

Capture before/after states for all changes to virtual infrastructure:

```powershell
# change-evidence.ps1
# Captures pre-change and post-change state for change management compliance

param(
    [Parameter(Mandatory)]
    [string]$ChangeTicket,
    
    [Parameter(Mandatory)]
    [ValidateSet("Pre", "Post")]
    [string]$Phase,
    
    [string]$vCenter = "vcenter.corp.local"
)

$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$outputDir = "./change-evidence/${ChangeTicket}/${Phase}_${timestamp}"
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

Connect-VIServer -Server $vCenter

# Capture host configurations
Get-VMHost | ForEach-Object {
    $hostDir = Join-Path $outputDir $_.Name
    New-Item -ItemType Directory -Path $hostDir -Force | Out-Null
    
    # Advanced settings
    $_ | Get-AdvancedSetting | Select-Object Name, Value |
        Export-Csv "$hostDir/advanced-settings.csv" -NoTypeInformation
    
    # Services
    $_ | Get-VMHostService | Select-Object Key, Label, Running, Policy |
        Export-Csv "$hostDir/services.csv" -NoTypeInformation
    
    # Network
    $_ | Get-VirtualSwitch | Select-Object Name, NumPorts, Mtu |
        Export-Csv "$hostDir/vswitches.csv" -NoTypeInformation
    
    # Firewall
    $_ | Get-VMHostFirewallException | Select-Object Name, Enabled, IncomingPorts, OutgoingPorts |
        Export-Csv "$hostDir/firewall-rules.csv" -NoTypeInformation
}

# Capture VM configurations
Get-VM | ForEach-Object {
    $vmConfig = [PSCustomObject]@{
        Name         = $_.Name
        PowerState   = $_.PowerState
        NumCPU       = $_.NumCpu
        MemoryGB     = $_.MemoryGB
        GuestOS      = $_.GuestId
        HardDisks    = ($_ | Get-HardDisk | Measure-Object).Count
        Networks     = (($_ | Get-NetworkAdapter).NetworkName -join ", ")
        Snapshots    = ($_ | Get-Snapshot | Measure-Object).Count
        Host         = $_.VMHost.Name
        Folder       = $_.Folder.Name
    }
    $vmConfig
} | Export-Csv "$outputDir/vm-inventory.csv" -NoTypeInformation

# Generate manifest
Get-ChildItem -Path $outputDir -Recurse -File | ForEach-Object {
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    "$hash  $($_.FullName)"
} | Out-File "$outputDir/manifest.sha256"

Write-Host "Change evidence captured: $outputDir"
Disconnect-VIServer -Confirm:$false
```

### 4.5 Access Review Evidence

Quarterly access reviews require documented evidence of who has access, why, and when it was last reviewed:

```powershell
# access-review-report.ps1
# Generates access review report for virtual infrastructure

param(
    [string]$vCenter = "vcenter.corp.local",
    [string]$OutputPath = "./access-review-$(Get-Date -Format 'yyyy-Q')"
)

New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
Connect-VIServer -Server $vCenter

# Collect all permissions
$permissions = @()

# Global permissions
Get-VIPermission | ForEach-Object {
    $permissions += [PSCustomObject]@{
        Scope      = "Global"
        Entity     = $_.Entity.Name
        EntityType = $_.EntityId
        Principal  = $_.Principal
        Role       = $_.Role
        Propagate  = $_.Propagate
        IsGroup    = $_.IsGroup
    }
}

# Export for review
$permissions | Export-Csv "$OutputPath/all-permissions.csv" -NoTypeInformation

# Identify over-privileged accounts
$adminAccounts = $permissions | Where-Object { $_.Role -match "Admin" }
$adminAccounts | Export-Csv "$OutputPath/admin-accounts.csv" -NoTypeInformation

# Service accounts (non-personal accounts)
$serviceAccounts = $permissions | Where-Object { 
    $_.Principal -match "svc_|service|system" -or
    $_.Principal -notmatch "@"
}
$serviceAccounts | Export-Csv "$OutputPath/service-accounts.csv" -NoTypeInformation

# Generate review template
$reviewTemplate = $permissions | Select-Object @{N='Principal';E={$_.Principal}},
    @{N='Role';E={$_.Role}},
    @{N='Scope';E={"$($_.EntityType):$($_.Entity)"}},
    @{N='StillRequired';E={''}},
    @{N='Justification';E={''}},
    @{N='ReviewedBy';E={''}},
    @{N='ReviewDate';E={''}}

$reviewTemplate | Export-Csv "$OutputPath/review-template.csv" -NoTypeInformation

Write-Host "Access review report generated: $OutputPath"
Write-Host "Admin accounts found: $($adminAccounts.Count)"
Write-Host "Service accounts found: $($serviceAccounts.Count)"
Write-Host "Total permissions: $($permissions.Count)"

Disconnect-VIServer -Confirm:$false
```

---

## 5. Vulnerability Assessment

### 5.1 Scanning Hypervisors — Nessus/Qualys Policies

Hypervisor scanning requires specialized scan policies that account for the unique characteristics of ESXi and Proxmox:

**Nessus Scan Policy for ESXi:**

```
Policy Name: VMware ESXi Credentialed Audit
Category: Compliance / Vulnerability

Credentials:
  - Type: VMware ESXi (SOAP API)
  - Authentication: Username/Password or Certificate
  - Account: Dedicated audit account (read-only role)
  - Port: 443

Settings:
  - Safe Checks: Enabled (CRITICAL for hypervisors)
  - Network Timeout: 30s (increase for busy hosts)
  - Max Concurrent Checks: 3 (reduce from default to avoid host overload)
  - Scan Type: All Ports + Service Discovery
  - CGI Scanning: Disabled (not applicable to ESXi)
  
Plugin Families to Enable:
  - VMware ESXi Local Security Checks
  - VMware VMSA Advisories
  - General (for SSL/TLS assessment)
  - Firewalls (for service exposure)
  - Settings (for CIS/STIG compliance)
  
Compliance:
  - VMware vSphere 8.0 ESXi CIS L1
  - VMware vSphere 8.0 ESXi CIS L2 (if applicable)
  - DISA STIG VMware vSphere 8 ESXi
```

**Nessus Scan Policy for Proxmox VE:**

```
Policy Name: Proxmox VE Host Credentialed Audit
Category: Compliance / Vulnerability

Credentials:
  - Type: SSH
  - Authentication: SSH Key (preferred) or Password
  - Account: Dedicated audit account with sudo for specific commands
  - Privilege Escalation: sudo (configured in /etc/sudoers.d/nessus-audit)

Settings:
  - Safe Checks: Enabled
  - Network Timeout: 30s
  - Max Concurrent Checks: 4
  - Port Scan Range: 1-65535
  
Plugin Families to Enable:
  - Debian Local Security Checks
  - General
  - Firewalls
  - Web Servers (for pveproxy on 8006)
  - SSL/TLS
  - Settings
  
Compliance:
  - CIS Debian Linux 12 L1 Server
  - CIS Debian Linux 12 L2 Server
  - Custom Proxmox checks (audit file)
```

**Sudoers configuration for Nessus audit account on Proxmox:**

```
# /etc/sudoers.d/nessus-audit
# Minimal privilege escalation for vulnerability scanning
# No shell access, specific commands only

nessus_audit ALL=(root) NOPASSWD: /usr/bin/dpkg -l
nessus_audit ALL=(root) NOPASSWD: /usr/bin/apt list --installed
nessus_audit ALL=(root) NOPASSWD: /usr/sbin/sysctl -a
nessus_audit ALL=(root) NOPASSWD: /usr/bin/find /etc -type f
nessus_audit ALL=(root) NOPASSWD: /usr/bin/cat /etc/ssh/sshd_config
nessus_audit ALL=(root) NOPASSWD: /usr/bin/cat /etc/pam.d/*
nessus_audit ALL=(root) NOPASSWD: /usr/bin/cat /etc/pve/storage.cfg
nessus_audit ALL=(root) NOPASSWD: /usr/bin/ss -tlnp
nessus_audit ALL=(root) NOPASSWD: /usr/bin/systemctl list-units --type=service
nessus_audit ALL=(root) NOPASSWD: /usr/sbin/iptables -L -n
nessus_audit ALL=(root) NOPASSWD: /usr/sbin/nft list ruleset
```

### 5.2 Credentialed vs Network-Based Scanning Tradeoffs

| Aspect | Credentialed Scan | Network-Based Scan |
|---|---|---|
| Coverage | Complete — sees all installed packages, configs, local vulns | External attack surface only |
| Accuracy | High — fewer false positives, detects backported patches | Lower — cannot confirm patch status |
| Performance impact | Moderate — runs commands on host | Low — only network traffic |
| Risk | Credential exposure if scanner compromised | Minimal — no credentials stored |
| Setup complexity | Higher — requires accounts, key management, firewall rules | Lower — point and scan |
| Compliance suitability | Required for PCI-DSS internal scans, STIG assessment | Acceptable for perimeter-only assessment |
| Detection of | Misconfigurations, missing patches, weak permissions, local services | Exposed services, SSL issues, network vulns |

**Recommendation for virtual infrastructure:**
- Use credentialed scans for quarterly compliance assessments.
- Use network-based scans for continuous monitoring (weekly).
- Separate credential sets per host type — never reuse ESXi credentials for Proxmox scans.
- Store scanner credentials in a vault with rotation.

### 5.3 VM-Level Scanning — Agent vs Agentless

| Approach | Agent-Based | Agentless |
|---|---|---|
| Deployment | Install agent in each VM | Use hypervisor API or network credentials |
| Resource overhead | Per-VM CPU/memory consumption | Concentrated on scanning infrastructure |
| Coverage | Real-time, continuous | Point-in-time during scan windows |
| Offline VMs | Cannot scan powered-off VMs | Can scan disk images (VMware/Proxmox QCOW2) |
| Scale | Each agent reports independently | Centralized scan management |
| Network impact | Minimal (agent-to-server comms) | Significant during large scan windows |
| Templates/snapshots | Agent in template ensures coverage | Must scan after deployment |

**VMware-specific agentless scanning (vShield/Carbon Black AppC):**

Agentless scanning leverages VMware APIs to mount VM disk images from outside the guest, scanning without installing anything in the VM. Products like Qualys Virtual Scanner Appliance and Trend Micro Deep Security use this approach.

**Proxmox agentless scanning approach:**

```bash
# Mount QCOW2 image for offline scanning
# WARNING: Only on powered-off VMs or snapshots

VM_ID=100
SNAPSHOT="audit-scan"

# Create snapshot for safe scanning
qm snapshot ${VM_ID} ${SNAPSHOT} --description "Audit scan $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Mount the disk image read-only via NBD
modprobe nbd max_part=8
qemu-nbd --connect=/dev/nbd0 --read-only \
    /var/lib/vz/images/${VM_ID}/vm-${VM_ID}-disk-0.qcow2

# Scan the mounted filesystem
mkdir -p /mnt/audit-scan
mount -o ro /dev/nbd0p1 /mnt/audit-scan

# Run vulnerability scanner against mounted filesystem
# (example with OpenSCAP)
oscap oval eval --results /tmp/scan-vm${VM_ID}.xml \
    --report /tmp/scan-vm${VM_ID}.html \
    /usr/share/xml/scap/ssg/content/ssg-debian12-oval.xml \
    --target /mnt/audit-scan

# Cleanup
umount /mnt/audit-scan
qemu-nbd --disconnect /dev/nbd0
qm delsnapshot ${VM_ID} ${SNAPSHOT}
```

### 5.4 Vulnerability Prioritization in Virtual Context

Standard CVSS scoring does not account for the amplified impact of hypervisor vulnerabilities. Apply context-aware prioritization:

**Hypervisor Vulnerability Severity Multiplier:**

| Vulnerability Location | CVSS Multiplier | Rationale |
|---|---|---|
| Hypervisor kernel (VMkernel, KVM) | 1.5x | Compromise affects ALL hosted VMs |
| Management plane (vCenter, Proxmox API) | 1.3x | Administrative access to entire infrastructure |
| Virtual networking (vSwitch, OVS) | 1.2x | Cross-VM traffic interception possible |
| Storage controller (vSAN, Ceph) | 1.2x | Data access across multiple VMs |
| Guest tools (open-vm-tools, qemu-guest-agent) | 1.0x | Limited to single VM, but may enable escape |
| Guest OS | 1.0x | Standard prioritization applies |

**VM Escape vulnerabilities (CVE examples):**
- Treat ANY confirmed VM escape vulnerability as CVSS 10.0 regardless of calculated score.
- Examples: CVE-2023-20858 (VMware), CVE-2024-21626 (container escape, applicable to LXC).
- Patch within 24 hours, not the standard 30-day window.

### 5.5 False Positive Handling

Virtual environments produce specific categories of false positives:

| False Positive Type | Explanation | Resolution |
|---|---|---|
| ESXi "missing patches" | Scanner detects old kernel version but ESXi uses monolithic builds — patches are cumulative | Verify via `esxcli software profile get` — build number confirms patch status |
| Proxmox kernel version | Proxmox uses pve-kernel with backported fixes — version number appears outdated | Check `apt list --installed pve-kernel*` and cross-reference Proxmox security advisories |
| Open ports on management interfaces | vCenter/Proxmox require specific ports — flagged as "unnecessary services" | Document as accepted risk with compensating controls (firewall, VLAN isolation) |
| SSL certificate warnings | Self-signed or internal CA certificates flagged as "untrusted" | Exclude from findings if internal CA is documented and trusted by infrastructure |
| VMware tools version mismatch | Scanner expects specific tools version but host uses open-vm-tools from distro repo | Verify tools functionality, document as acceptable variation |

**False positive documentation template:**

```
False Positive Record
=====================
Scanner:        Nessus Professional 10.x
Plugin ID:      12345
Finding:        VMware ESXi 8.0 < 8.0.2 - Multiple Vulnerabilities
Host:           esxi-01.corp.local
Date Found:     2026-05-07

Reason for False Positive:
The scanner identifies ESXi 8.0 build 22345678 as vulnerable. However, 
VMware patch ESXi80U3-2024xxxx (applied 2026-04-15) backports the fix 
without changing the major version number. The actual installed build 
includes the security fix.

Evidence:
- esxcli software profile get output showing build 22345678
- VMware advisory VMSA-2026-0003 confirms fix in this build
- Patch manifest from vLCM showing successful application

Approved By:    [Security Lead]
Approval Date:  2026-05-07
Review:         Quarterly (re-validate on next scan)
```

---

## 6. Penetration Testing Scoping

### 6.1 Defining Scope in Virtualized Environments

Virtual infrastructure introduces layers that must be explicitly included or excluded from penetration testing scope:

```
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 1: PHYSICAL/HARDWARE (Usually out of scope)                │
│   - Server BIOS/UEFI, BMC/iLO/iDRAC, physical network switches │
└──────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 2: HYPERVISOR (In scope - HIGH RISK testing)               │
│   - ESXi host exploitation                                       │
│   - Proxmox host OS exploitation                                 │
│   - VM escape attempts (requires explicit authorization)         │
│   - Hypervisor API exploitation                                  │
└──────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 3: MANAGEMENT PLANE (In scope - CRITICAL)                  │
│   - vCenter Server attack surface                                │
│   - Proxmox web UI and API                                       │
│   - SSO/identity integration (LDAP/AD attacks)                   │
│   - Backup infrastructure (Veeam, PBS)                           │
└──────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 4: VIRTUAL NETWORKING (In scope)                           │
│   - VLAN hopping from guest to management                        │
│   - Virtual switch exploitation                                  │
│   - Distributed firewall bypass                                  │
│   - Inter-VM traffic sniffing                                    │
└──────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 5: GUEST OS (Standard pentest scope)                       │
│   - Operating system exploitation                                │
│   - Application-layer attacks                                    │
│   - Privilege escalation within VM                               │
│   - Lateral movement between VMs                                 │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Rules of Engagement

**Critical constraints for production virtual infrastructure testing:**

```
RULES OF ENGAGEMENT — Virtual Infrastructure Penetration Test
==============================================================
Document ID:    ROE-VIRT-2026-001
Classification: CONFIDENTIAL
Effective:      2026-05-07 through 2026-05-21

AUTHORIZED ACTIVITIES:
- Network scanning of management interfaces (rate-limited)
- Authentication testing against vCenter/Proxmox (with lockout awareness)
- API fuzzing against management endpoints (non-destructive)
- Virtual network analysis and VLAN assessment
- Guest OS exploitation (designated test VMs only)
- Privilege escalation assessment within test VMs
- Social engineering against infrastructure team (if in scope)

PROHIBITED ACTIVITIES:
- ANY action that could cause VM migration failure (storage manipulation)
- Denial-of-service attacks against hypervisor management
- Modification or deletion of production VM configurations
- Snapshot creation/deletion on production VMs (consumes storage, triggers vMotion)
- vMotion/live migration triggering during test windows
- Exploitation of shared storage (affects all VMs)
- Resource exhaustion attacks (CPU/memory bomb VMs)
- Manipulation of HA/DRS policies
- Testing during backup windows (21:00-05:00 daily)
- Testing during maintenance windows (published separately)
- ANY VM escape attempt without explicit written authorization per attempt
- Modification of cluster configuration (corosync, HA policies)

COMMUNICATION:
- Primary contact: [Infrastructure Lead] - [phone]
- Escalation: [CISO] - [phone]
- Emergency stop phrase: "OPERATION HALT" via any channel
- Status updates: Daily at 09:00 UTC via encrypted channel
- Finding severity >= CRITICAL: Immediate notification required

IMPACT THRESHOLDS:
- If any production VM becomes unresponsive: STOP immediately, notify
- If hypervisor CPU > 90% sustained: STOP scanning of that host
- If management interface becomes unresponsive: STOP, wait 5 minutes, notify if not recovered
- If any alert fires in monitoring: STOP, coordinate with ops team
```

### 6.3 Testing Shared Infrastructure Impact Assessment

Before testing, map the blast radius of potential impacts:

```
Impact Assessment Matrix
========================

TARGET: vCenter Server (vcenter.corp.local)
├── If unavailable for >5 min:
│   ├── DRS cannot rebalance (VMs continue running)
│   ├── HA cannot restart failed VMs on other hosts
│   ├── vMotion unavailable (maintenance impossible)
│   ├── Alarms and monitoring stop
│   └── Provisioning halted
├── If compromised:
│   ├── Full control of all VMs (poweron/off/modify/delete)
│   ├── Access to all VM consoles
│   ├── Storage access to all datastores
│   ├── Network reconfiguration possible
│   └── Credential extraction (SSO database)
└── Compensating controls during test:
    ├── Secondary monitoring via ESXi direct (not vCenter-dependent)
    ├── Out-of-band management via BMC/iLO if vCenter fails
    └── Designated rollback procedure with fresh vCenter restore

TARGET: Proxmox Cluster Node (pve-01.corp.local)
├── If unavailable:
│   ├── HA migrates VMs to remaining nodes (if configured)
│   ├── Cluster quorum maintained if majority remains
│   ├── Storage (Ceph) operates in degraded mode if OSD on this node
│   └── Corosync recalculates with remaining members
├── If compromised:
│   ├── Full root access to all local VM disk images
│   ├── Cluster configuration accessible via /etc/pve (pmxcfs)
│   ├── Can manipulate cluster state if corosync key available
│   └── Network bridge manipulation affects all VMs on this node
└── Compensating controls:
    ├── Test on isolated node removed from cluster first
    ├── Ceph configured to tolerate single node failure
    └── Backup validation run immediately before test window
```

### 6.4 Timing Considerations

```
WEEKLY SCHEDULE — Virtual Infrastructure Test Windows
=====================================================

MON-FRI (Business Hours 08:00-18:00 Local):
  ✓ Guest OS testing (designated test VMs)
  ✓ Management plane authentication testing (rate-limited)
  ✓ Network analysis (passive)
  ✗ Hypervisor-level testing
  ✗ Storage testing
  ✗ Network disruption testing

TUE-THU (Maintenance Window 02:00-05:00 Local):
  ✓ Hypervisor-level testing
  ✓ Network disruption testing (with standby)
  ✓ VM escape attempts (with authorization)
  ✗ Coincides with backup window (use alternate nights)
  
SAT (Planned Downtime 06:00-12:00 Local):
  ✓ Aggressive testing with full ops team standby
  ✓ DoS resilience testing (controlled)
  ✓ Failover testing combined with pentest
  
BLACKOUT PERIODS:
  - Month-end processing: Last 2 business days
  - Quarter-end close: Last 5 business days
  - Patch Tuesday +48h: After Microsoft patches (VMs patching)
  - Scheduled infrastructure maintenance: See calendar
```

### 6.5 Credential Handling for Virtual Infrastructure Pentest

```
Credential Management for Virtual Infrastructure Pentest
=========================================================

PRINCIPLE: Least privilege per test phase. Never provide production 
admin credentials upfront.

PHASE 1: External Discovery (No credentials)
- Network scanning from untrusted VLAN
- Service enumeration
- Public certificate analysis

PHASE 2: Authenticated Testing (Read-only credentials)
- Auditor role in vCenter (read-only)
- PVEAuditor role in Proxmox (read-only)
- Purpose: Validate what attacker sees post-authentication

PHASE 3: Privilege Escalation (Standard user credentials)
- VM-level standard user account
- Proxmox user with minimal permissions
- Purpose: Test vertical and horizontal escalation

PHASE 4: Administrative Testing (Time-limited admin access)
- Temporary admin credential issued per test
- Revoked automatically after test window (vault TTL)
- Purpose: Test admin-level attack paths and post-compromise scenarios
- All actions logged separately

CREDENTIAL STORAGE:
- HashiCorp Vault with 4-hour TTL per credential lease
- Credentials wiped from tester systems post-engagement
- No credentials in pentest report (use placeholders)
- Engagement vault seal verified at engagement conclusion
```

---

## 7. Access Control Audit

### 7.1 vCenter/Proxmox Role-Based Access Review

**vCenter RBAC Audit Script:**

```powershell
# vcenter-rbac-audit.ps1
# Comprehensive RBAC audit for vCenter

Connect-VIServer -Server $vCenter

# 1. Custom roles and their privileges
$roles = Get-VIRole | Where-Object { -not $_.IsSystem }
$roleAudit = $roles | ForEach-Object {
    $privs = $_ | Get-VIPrivilege
    [PSCustomObject]@{
        RoleName       = $_.Name
        PrivilegeCount = $privs.Count
        HasAdmin       = $privs | Where-Object { $_.Id -match "VirtualMachine.Interact.ConsoleInteract|Global.Settings" } | Measure-Object | Select-Object -ExpandProperty Count
        Privileges     = ($privs.Id -join "; ")
    }
}
$roleAudit | Export-Csv "./vcenter-custom-roles.csv" -NoTypeInformation

# 2. Permission assignments with inheritance analysis
$allPerms = Get-VIPermission
$permAudit = $allPerms | ForEach-Object {
    [PSCustomObject]@{
        Principal   = $_.Principal
        IsGroup     = $_.IsGroup
        Role        = $_.Role
        Entity      = $_.Entity.Name
        EntityType  = $_.Entity.GetType().Name
        Propagate   = $_.Propagate
        Inherited   = $false  # Top-level assignment
    }
}

# 3. Identify excessive privileges
$adminPerms = $permAudit | Where-Object { $_.Role -match "Administrator" }
$dangerousPerms = $permAudit | Where-Object { 
    $_.Role -match "Admin" -and $_.EntityType -match "Datacenter|Folder" -and $_.Propagate
}

Write-Host "=== RBAC Audit Summary ==="
Write-Host "Total permissions: $($permAudit.Count)"
Write-Host "Full Administrator grants: $($adminPerms.Count)"
Write-Host "Propagating admin at Datacenter/Folder level (REVIEW): $($dangerousPerms.Count)"

$dangerousPerms | Format-Table Principal, Entity, EntityType, Propagate
```

**Proxmox RBAC Audit Script:**

```bash
#!/usr/bin/env bash
# proxmox-rbac-audit.sh
# Comprehensive access control audit for Proxmox VE

set -euo pipefail

OUTPUT_DIR="./proxmox-rbac-audit-$(date +%Y-%m-%d)"
mkdir -p "${OUTPUT_DIR}"

echo "=== Proxmox VE Access Control Audit ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Node: $(hostname -f)"
echo ""

# 1. All users with status
echo "--- Users ---"
pveum user list --output-format json | python3 -c "
import sys, json
users = json.load(sys.stdin)
print(f'Total users: {len(users)}')
print(f'Enabled users: {len([u for u in users if u.get(\"enable\", 1) == 1])}')
print(f'Disabled users: {len([u for u in users if u.get(\"enable\", 1) == 0])}')
print(f'Users without expiry: {len([u for u in users if not u.get(\"expire\")])}')
print()
for u in users:
    exp = u.get('expire', 0)
    status = 'ENABLED' if u.get('enable', 1) else 'DISABLED'
    expiry = 'NEVER' if not exp else f'expires {exp}'
    print(f\"  {u['userid']:30s} {status:10s} {expiry}\")
" | tee "${OUTPUT_DIR}/users.txt"

# 2. Groups and membership
echo ""
echo "--- Groups ---"
pveum group list --output-format json | python3 -c "
import sys, json
groups = json.load(sys.stdin)
for g in groups:
    members = g.get('members', '')
    count = len(members.split(',')) if members else 0
    print(f\"  {g['groupid']:20s} members: {count:3d}  [{members}]\")
" | tee "${OUTPUT_DIR}/groups.txt"

# 3. Roles and their privileges
echo ""
echo "--- Custom Roles (non-default) ---"
pveum role list --output-format json | python3 -c "
import sys, json
roles = json.load(sys.stdin)
# Default roles to exclude from review
defaults = ['Administrator', 'NoAccess', 'PVEAdmin', 'PVEAuditor',
            'PVEDatastoreAdmin', 'PVEDatastoreUser', 'PVEPoolAdmin',
            'PVEPoolUser', 'PVESysAdmin', 'PVETemplateUser', 'PVEUserAdmin',
            'PVEVMAdmin', 'PVEVMUser']
for r in roles:
    custom = '(CUSTOM)' if r['roleid'] not in defaults else ''
    privs = r.get('privs', '').split(',')
    print(f\"  {r['roleid']:25s} {custom:10s} privileges: {len(privs)}\")
    if custom:
        for p in sorted(privs):
            print(f'    - {p}')
" | tee "${OUTPUT_DIR}/roles.txt"

# 4. ACL assignments (the critical audit data)
echo ""
echo "--- ACL Assignments ---"
pveum acl list --output-format json | python3 -c "
import sys, json
acls = json.load(sys.stdin)
print(f'Total ACL entries: {len(acls)}')
print()
# Flag dangerous: Administrator role, root path, propagate
for acl in sorted(acls, key=lambda x: x.get('roleid', '')):
    path = acl.get('path', '/')
    role = acl.get('roleid', '')
    ugid = acl.get('ugid', '')
    atype = acl.get('type', '')
    propagate = acl.get('propagate', 1)
    
    danger = ''
    if role == 'Administrator' and path == '/':
        danger = '  *** ROOT ADMIN ***'
    elif role == 'Administrator':
        danger = '  ** ADMIN **'
    elif 'Sys' in role and path == '/':
        danger = '  * SysAdmin at root *'
    
    print(f\"  {atype:5s} {ugid:25s} role={role:20s} path={path:20s} propagate={propagate}{danger}\")
" | tee "${OUTPUT_DIR}/acls.txt"

# 5. API tokens
echo ""
echo "--- API Tokens ---"
pveum user list --output-format json | python3 -c "
import sys, json, subprocess
users = json.load(sys.stdin)
for u in users:
    result = subprocess.run(
        ['pveum', 'user', 'token', 'list', u['userid'], '--output-format', 'json'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        tokens = json.loads(result.stdout) if result.stdout.strip() else []
        for t in tokens:
            expire = t.get('expire', 0)
            privsep = 'privilege-separated' if t.get('privsep', 1) else 'FULL USER PRIVS'
            exp_str = 'NEVER EXPIRES' if not expire else f'expires {expire}'
            print(f\"  {u['userid']}!{t.get('tokenid','?'):20s} {privsep:25s} {exp_str}\")
" 2>/dev/null | tee "${OUTPUT_DIR}/api-tokens.txt"

# Generate SHA256 manifest
find "${OUTPUT_DIR}" -type f -exec sha256sum {} \; > "${OUTPUT_DIR}/manifest.sha256"

echo ""
echo "Audit complete. Results in: ${OUTPUT_DIR}"
```

### 7.2 Privilege Escalation Assessment

Key escalation paths to assess in virtual infrastructure:

**VMware privilege escalation vectors:**

1. **vCenter SSO → Administrator**: Exploit SSO misconfigurations (default administrator@vsphere.local password, SSO domain trust).
2. **VM operator → Host access**: If VM has VMware Tools running as SYSTEM, and host has weak isolation, potential for VMCI socket abuse.
3. **Network admin → Full admin**: DVS port group modification can enable traffic interception, leading to credential theft.
4. **Backup operator → Data access**: Backup roles can export VMs, accessing all data within.
5. **Storage admin → VM disk access**: Direct datastore access allows reading any VM disk file.

**Proxmox privilege escalation vectors:**

1. **PVEVMUser → root via QEMU Guest Agent**: If QEMU guest agent commands are unrestricted and VM runs as root internally.
2. **PVEAdmin → root via custom storage**: Creating a storage definition pointing to `/etc` or `/root`.
3. **Any user → cluster manipulation**: If corosync authentication is weak, cluster state can be manipulated.
4. **API token without privsep → full user context**: Non-privilege-separated tokens inherit all user permissions.
5. **LDAP/AD user → Proxmox escalation**: If LDAP groups map to PVEAdmin without additional controls.

### 7.3 Service Account Inventory

```powershell
# service-account-audit.ps1
# Inventory all service accounts with risk assessment

$serviceAccounts = @()

# vCenter service accounts (by naming convention)
Get-VIPermission | Where-Object { 
    $_.Principal -match "svc_|^CORP\\SVC-|service|backup|monitor|scan"
} | ForEach-Object {
    $serviceAccounts += [PSCustomObject]@{
        Account      = $_.Principal
        Type         = "vCenter Permission"
        Role         = $_.Role
        Scope        = "$($_.Entity.Name) ($($_.Entity.GetType().Name))"
        LastUsed     = "Check AD logs"
        PasswordAge  = "Check AD"
        Risk         = if ($_.Role -match "Admin") { "HIGH" } else { "MEDIUM" }
        Owner        = ""  # Fill from CMDB
        Purpose      = ""  # Fill from documentation
    }
}

# Check for accounts with non-expiring passwords in vCenter SSO
# (Requires direct SSO lookup or AD query)

$serviceAccounts | Sort-Object Risk -Descending | 
    Export-Csv "./service-account-inventory.csv" -NoTypeInformation

# Risk summary
$serviceAccounts | Group-Object Risk | Format-Table Name, Count
```

### 7.4 API Token Audit

```bash
#!/usr/bin/env bash
# api-token-audit.sh
# Audit all API tokens for scope, expiry, and usage

echo "=== API Token Security Audit ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

FINDINGS=0

# Check all tokens
pveum user list --output-format json | python3 << 'PYEOF'
import json, subprocess, sys
from datetime import datetime, timezone

users = json.loads(subprocess.check_output(
    ["pveum", "user", "list", "--output-format", "json"]
))

findings = []
for user in users:
    uid = user["userid"]
    result = subprocess.run(
        ["pveum", "user", "token", "list", uid, "--output-format", "json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        continue
    tokens = json.loads(result.stdout) if result.stdout.strip() else []
    
    for token in tokens:
        tid = token.get("tokenid", "unknown")
        expire = token.get("expire", 0)
        privsep = token.get("privsep", 1)
        
        issues = []
        
        # Check: non-expiring tokens
        if not expire:
            issues.append("NEVER EXPIRES - set expiration date")
        elif expire > 0:
            exp_date = datetime.fromtimestamp(expire, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            if exp_date < now:
                issues.append(f"EXPIRED on {exp_date.isoformat()} - revoke immediately")
            elif (exp_date - now).days > 365:
                issues.append(f"Expires in {(exp_date - now).days} days - consider shorter TTL")
        
        # Check: not privilege-separated
        if not privsep:
            issues.append("NOT PRIVILEGE-SEPARATED - inherits full user permissions")
        
        if issues:
            for issue in issues:
                findings.append({
                    "token": f"{uid}!{tid}",
                    "issue": issue,
                    "severity": "HIGH" if "NEVER EXPIRES" in issue or "NOT PRIVILEGE" in issue else "MEDIUM"
                })

print(f"\nTotal findings: {len(findings)}")
for f in sorted(findings, key=lambda x: x["severity"]):
    print(f"  [{f['severity']:6s}] {f['token']:40s} - {f['issue']}")
PYEOF
```

### 7.5 Certificate Management Audit

```bash
#!/usr/bin/env bash
# cert-audit.sh
# Audit all certificates in virtual infrastructure

echo "=== Certificate Audit ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Proxmox node certificates
echo "--- Proxmox Node Certificates ---"
for cert_file in /etc/pve/nodes/*/pve-ssl.pem /etc/pve/pve-root-ca.pem; do
    if [ -f "${cert_file}" ]; then
        subject=$(openssl x509 -in "${cert_file}" -noout -subject 2>/dev/null | sed 's/subject=//')
        expiry=$(openssl x509 -in "${cert_file}" -noout -enddate 2>/dev/null | sed 's/notAfter=//')
        issuer=$(openssl x509 -in "${cert_file}" -noout -issuer 2>/dev/null | sed 's/issuer=//')
        
        # Check if expiring within 30 days
        if openssl x509 -in "${cert_file}" -noout -checkend 2592000 2>/dev/null; then
            status="OK"
        else
            status="EXPIRING SOON"
        fi
        
        echo "  File:    ${cert_file}"
        echo "  Subject: ${subject}"
        echo "  Issuer:  ${issuer}"
        echo "  Expires: ${expiry}"
        echo "  Status:  ${status}"
        echo ""
    fi
done

# Check certificate key strength
echo "--- Key Strength Assessment ---"
for cert_file in /etc/pve/nodes/*/pve-ssl.pem; do
    if [ -f "${cert_file}" ]; then
        key_info=$(openssl x509 -in "${cert_file}" -noout -text 2>/dev/null | grep "Public-Key:")
        sig_algo=$(openssl x509 -in "${cert_file}" -noout -text 2>/dev/null | grep "Signature Algorithm:" | head -1)
        echo "  ${cert_file}: ${key_info} ${sig_algo}"
        
        # Flag weak algorithms
        if echo "${sig_algo}" | grep -qi "sha1\|md5"; then
            echo "    ** WARNING: Weak signature algorithm detected **"
        fi
    fi
done
```

### 7.6 Emergency/Break-Glass Account Procedures

Document and audit break-glass access for virtual infrastructure:

```
Break-Glass Account Inventory and Procedures
=============================================

Account: root@pam (Proxmox local root)
- Password stored: Physical safe + Vault (sealed)
- Last rotation: 2026-04-01
- Rotation schedule: Quarterly
- Usage trigger: Complete LDAP/AD failure, all normal admin accounts locked
- Post-use requirement: Immediate password rotation, incident report within 24h

Account: administrator@vsphere.local (vCenter SSO)
- Password stored: Physical safe + Vault (sealed)
- Last rotation: 2026-03-15
- Rotation schedule: Quarterly
- Usage trigger: Complete AD failure, SSO unavailable
- Post-use requirement: Immediate rotation, full audit log review

Audit verification:
1. Verify sealed status quarterly (tamper-evident envelope intact)
2. Test credentials annually (scheduled maintenance window)
3. Review usage logs monthly (should show zero usage normally)
4. Cross-reference any usage with approved change tickets
```

### 7.7 Cross-Platform Access Correlation (VMware → Proxmox Hybrid)

During migration, accounts exist in both platforms. Audit requires correlation:

```python
#!/usr/bin/env python3
"""
cross_platform_access_audit.py
Correlates access between VMware vCenter and Proxmox VE
Identifies inconsistencies and orphaned access during migration.
"""

import json
import subprocess
from dataclasses import dataclass


@dataclass
class AccessEntry:
    principal: str
    platform: str
    role: str
    scope: str
    source: str


def get_vcenter_access(vcenter_export_csv: str) -> list[AccessEntry]:
    """Parse vCenter permission export."""
    entries = []
    # In production, use pyVmomi or PowerCLI export
    # This demonstrates the correlation logic
    with open(vcenter_export_csv) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 4:
                entries.append(AccessEntry(
                    principal=parts[0].lower(),
                    platform="vCenter",
                    role=parts[1],
                    scope=parts[2],
                    source="vcenter-export"
                ))
    return entries


def get_proxmox_access() -> list[AccessEntry]:
    """Get Proxmox ACL entries."""
    entries = []
    result = subprocess.run(
        ["pveum", "acl", "list", "--output-format", "json"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        acls = json.loads(result.stdout)
        for acl in acls:
            entries.append(AccessEntry(
                principal=acl.get("ugid", "").lower(),
                platform="Proxmox",
                role=acl.get("roleid", ""),
                scope=acl.get("path", "/"),
                source="pveum-acl"
            ))
    return entries


def correlate_access(vcenter: list[AccessEntry], proxmox: list[AccessEntry]):
    """Find discrepancies between platforms."""
    vc_principals = {e.principal for e in vcenter}
    px_principals = {e.principal for e in proxmox}

    print("=== Cross-Platform Access Correlation ===\n")

    # Users in vCenter but not Proxmox (may need migration)
    vc_only = vc_principals - px_principals
    if vc_only:
        print(f"Users in vCenter only ({len(vc_only)}):")
        for p in sorted(vc_only):
            roles = [e.role for e in vcenter if e.principal == p]
            print(f"  {p:30s} roles: {', '.join(roles)}")

    # Users in Proxmox but not vCenter (new accounts or orphaned)
    px_only = px_principals - vc_principals
    if px_only:
        print(f"\nUsers in Proxmox only ({len(px_only)}):")
        for p in sorted(px_only):
            roles = [e.role for e in proxmox if e.principal == p]
            print(f"  {p:30s} roles: {', '.join(roles)}")

    # Users in both — check role consistency
    both = vc_principals & px_principals
    if both:
        print(f"\nUsers in both platforms ({len(both)}) — Role comparison:")
        for p in sorted(both):
            vc_roles = sorted(set(e.role for e in vcenter if e.principal == p))
            px_roles = sorted(set(e.role for e in proxmox if e.principal == p))
            match = "MATCH" if vc_roles == px_roles else "MISMATCH"
            print(f"  {p:30s} vCenter={vc_roles}  Proxmox={px_roles}  [{match}]")
```

---

## 8. Network Security Audit

### 8.1 Virtual Switch Security Policy Review

**VMware vSwitch/DVS Security Policy Audit:**

```powershell
# vswitch-security-audit.ps1
# Audits all virtual switch security policies

Connect-VIServer -Server $vCenter

$findings = @()

# Standard vSwitches
Get-VMHost | ForEach-Object {
    $hostName = $_.Name
    $_ | Get-VirtualSwitch -Standard | ForEach-Object {
        $policy = $_.ExtensionData.Spec.Policy.Security
        $finding = [PSCustomObject]@{
            Host             = $hostName
            SwitchType       = "Standard"
            SwitchName       = $_.Name
            PromiscuousMode  = $policy.AllowPromiscuous
            MacChanges       = $policy.MacChanges
            ForgedTransmits  = $policy.ForgedTransmits
            Compliant        = (-not $policy.AllowPromiscuous) -and (-not $policy.MacChanges) -and (-not $policy.ForgedTransmits)
        }
        $findings += $finding
        
        # Also check port groups (override switch policy)
        $_ | Get-VirtualPortGroup | ForEach-Object {
            $pgPolicy = $_.ExtensionData.Spec.Policy.Security
            if ($pgPolicy.AllowPromiscuous -or $pgPolicy.MacChanges -or $pgPolicy.ForgedTransmits) {
                $findings += [PSCustomObject]@{
                    Host             = $hostName
                    SwitchType       = "Standard-PortGroup"
                    SwitchName       = "$($_.VirtualSwitch.Name)/$($_.Name)"
                    PromiscuousMode  = if ($null -ne $pgPolicy.AllowPromiscuous) { $pgPolicy.AllowPromiscuous } else { "Inherited" }
                    MacChanges       = if ($null -ne $pgPolicy.MacChanges) { $pgPolicy.MacChanges } else { "Inherited" }
                    ForgedTransmits  = if ($null -ne $pgPolicy.ForgedTransmits) { $pgPolicy.ForgedTransmits } else { "Inherited" }
                    Compliant        = $false
                }
            }
        }
    }
}

# Distributed vSwitches
Get-VDSwitch | ForEach-Object {
    $dvsPolicy = $_.ExtensionData.Config.DefaultPortConfig.SecurityPolicy
    $findings += [PSCustomObject]@{
        Host             = "DVS"
        SwitchType       = "Distributed"
        SwitchName       = $_.Name
        PromiscuousMode  = $dvsPolicy.AllowPromiscuous.Value
        MacChanges       = $dvsPolicy.MacAddressChanges.Value
        ForgedTransmits  = $dvsPolicy.ForgedTransmits.Value
        Compliant        = (-not $dvsPolicy.AllowPromiscuous.Value) -and (-not $dvsPolicy.MacAddressChanges.Value) -and (-not $dvsPolicy.ForgedTransmits.Value)
    }
}

# Report
$nonCompliant = $findings | Where-Object { -not $_.Compliant }
Write-Host "`n=== vSwitch Security Audit ===" -ForegroundColor Cyan
Write-Host "Total switches/port groups assessed: $($findings.Count)"
Write-Host "Non-compliant: $($nonCompliant.Count)" -ForegroundColor $(if ($nonCompliant) { "Red" } else { "Green" })

if ($nonCompliant) {
    Write-Host "`nNon-compliant configurations:" -ForegroundColor Red
    $nonCompliant | Format-Table -AutoSize
}

$findings | Export-Csv "./vswitch-security-audit.csv" -NoTypeInformation
```

### 8.2 VLAN Configuration Audit

```bash
#!/usr/bin/env bash
# vlan-audit-proxmox.sh
# Audits VLAN configuration on Proxmox VE nodes

echo "=== VLAN Configuration Audit ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Node: $(hostname -f)"
echo ""

# 1. Bridge and VLAN inventory
echo "--- Bridge Configuration ---"
for bridge in /sys/class/net/vmbr*/; do
    bridge_name=$(basename "${bridge}")
    echo "  ${bridge_name}:"
    
    # Check if bridge has VLAN filtering enabled
    vlan_filtering=$(cat "${bridge}/bridge/vlan_filtering" 2>/dev/null || echo "N/A")
    echo "    VLAN Filtering: ${vlan_filtering}"
    
    # Show VLAN assignments
    bridge vlan show dev "${bridge_name}" 2>/dev/null | sed 's/^/    /'
    
    # List ports on this bridge
    echo "    Ports:"
    ls "${bridge}/brif/" 2>/dev/null | while read -r port; do
        echo "      - ${port}"
    done
    echo ""
done

# 2. Check for VLAN-unaware bridges (potential security issue)
echo "--- Security Assessment ---"
echo ""
echo "Bridges without VLAN filtering (all traffic shared):"
for bridge in /sys/class/net/vmbr*/; do
    bridge_name=$(basename "${bridge}")
    vf=$(cat "${bridge}/bridge/vlan_filtering" 2>/dev/null)
    if [ "${vf}" = "0" ] || [ -z "${vf}" ]; then
        # Check if VMs from different trust zones share this bridge
        echo "  WARNING: ${bridge_name} has no VLAN filtering"
    fi
done

# 3. Check network interfaces configuration for proper VLAN tagging
echo ""
echo "--- Network Interfaces VLAN Configuration ---"
grep -E "^(auto|iface|bridge_vlan_aware)" /etc/network/interfaces | sed 's/^/  /'

# 4. Verify management VLAN isolation
echo ""
echo "--- Management Interface Assessment ---"
mgmt_ip=$(pvesh get /nodes/$(hostname)/network --output-format json 2>/dev/null | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
for iface in data:
    if iface.get('type') == 'bridge' and 'address' in iface:
        if iface.get('address','').startswith(('10.0.0', '192.168.1')):
            print(f\"  Management: {iface['iface']} = {iface['address']}\")
" 2>/dev/null)
echo "${mgmt_ip}"

# 5. Check for trunk ports exposed to VMs (VLAN 4095 equivalent)
echo ""
echo "--- Trunk Port Exposure Check ---"
qm list --full 2>/dev/null | while read -r line; do
    vmid=$(echo "${line}" | awk '{print $1}')
    if [ "${vmid}" -gt 0 ] 2>/dev/null; then
        config=$(cat "/etc/pve/qemu-server/${vmid}.conf" 2>/dev/null)
        if echo "${config}" | grep -q "trunks="; then
            vm_name=$(echo "${config}" | grep "^name:" | awk '{print $2}')
            trunk_line=$(echo "${config}" | grep "trunks=")
            echo "  VM ${vmid} (${vm_name}): ${trunk_line}"
        fi
    fi
done
```

### 8.3 Distributed Firewall Rule Review

```powershell
# dfw-audit.ps1
# Audit NSX-T / vSphere Distributed Firewall rules

# For NSX-T environments
# Alternatively, for vSphere native DFW (via dvFilter):

Get-VM | ForEach-Object {
    $vm = $_
    $fwRules = $vm | Get-VMFirewallPolicy -ErrorAction SilentlyContinue
    
    if ($fwRules) {
        [PSCustomObject]@{
            VM            = $vm.Name
            IncomingRules = ($fwRules.IncomingEnabled)
            OutgoingRules = ($fwRules.OutgoingEnabled)
            DefaultAction = $fwRules.IncomingDefaultAction
        }
    }
}

# For Proxmox firewall rule audit:
# See /etc/pve/firewall/ for datacenter and per-VM rules
```

**Proxmox firewall rule completeness check:**

```bash
#!/usr/bin/env bash
# proxmox-fw-audit.sh
# Checks Proxmox firewall for completeness and security

echo "=== Proxmox Firewall Audit ==="

# Check datacenter-level firewall
echo ""
echo "--- Datacenter Firewall ---"
if [ -f /etc/pve/firewall/cluster.fw ]; then
    enabled=$(grep "^enable:" /etc/pve/firewall/cluster.fw | awk '{print $2}')
    policy_in=$(grep "^policy_in:" /etc/pve/firewall/cluster.fw | awk '{print $2}')
    policy_out=$(grep "^policy_out:" /etc/pve/firewall/cluster.fw | awk '{print $2}')
    
    echo "  Enabled: ${enabled:-NOT SET (disabled by default)}"
    echo "  Default policy IN:  ${policy_in:-ACCEPT (dangerous default)}"
    echo "  Default policy OUT: ${policy_out:-ACCEPT}"
    
    if [ "${enabled}" != "1" ]; then
        echo "  ** FINDING: Datacenter firewall is NOT enabled **"
    fi
    if [ "${policy_in}" != "DROP" ] && [ "${policy_in}" != "REJECT" ]; then
        echo "  ** FINDING: Default inbound policy is not deny-all **"
    fi
    
    echo ""
    echo "  Rules:"
    grep "^\[RULES\]" -A 1000 /etc/pve/firewall/cluster.fw 2>/dev/null | \
        grep -v "^\[" | grep -v "^$" | sed 's/^/    /'
else
    echo "  ** FINDING: No datacenter firewall configuration file exists **"
fi

# Check each VM has firewall enabled
echo ""
echo "--- Per-VM Firewall Status ---"
for conf in /etc/pve/qemu-server/*.conf; do
    vmid=$(basename "${conf}" .conf)
    vm_name=$(grep "^name:" "${conf}" | awk '{print $2}')
    
    # Check if firewall is enabled on network interfaces
    fw_enabled=$(grep -c "firewall=1" "${conf}")
    net_count=$(grep -c "^net[0-9]" "${conf}")
    
    if [ "${fw_enabled}" -lt "${net_count}" ]; then
        echo "  VM ${vmid} (${vm_name}): ${fw_enabled}/${net_count} interfaces have firewall enabled"
    fi
done
```

### 8.4 Traffic Flow Analysis

```bash
#!/usr/bin/env bash
# traffic-flow-analysis.sh
# Captures and analyzes traffic patterns on virtual bridges

# WARNING: This captures packets — ensure authorization and data handling compliance

CAPTURE_DURATION=300  # 5 minutes
BRIDGE="vmbr0"
OUTPUT_DIR="/tmp/traffic-analysis-$(date +%Y%m%d)"

mkdir -p "${OUTPUT_DIR}"

echo "Capturing traffic on ${BRIDGE} for ${CAPTURE_DURATION}s..."

# Capture with size limit (headers only for analysis)
timeout "${CAPTURE_DURATION}" tcpdump -i "${BRIDGE}" -nn -c 100000 \
    -w "${OUTPUT_DIR}/capture.pcap" \
    'not port 22' 2>/dev/null &

TCPDUMP_PID=$!
wait ${TCPDUMP_PID} 2>/dev/null

# Analyze flows
echo ""
echo "=== Traffic Flow Analysis ==="
echo ""

# Top talkers
echo "--- Top Source IPs ---"
tcpdump -r "${OUTPUT_DIR}/capture.pcap" -nn 2>/dev/null | \
    awk '{print $3}' | cut -d. -f1-4 | sort | uniq -c | sort -rn | head -20

echo ""
echo "--- Top Destination Ports ---"
tcpdump -r "${OUTPUT_DIR}/capture.pcap" -nn 2>/dev/null | \
    grep -oP '\.\d+:' | sort | uniq -c | sort -rn | head -20

echo ""
echo "--- Cross-VLAN Traffic (Unexpected) ---"
# Identify traffic that should not cross VLAN boundaries
# This requires knowledge of the expected traffic matrix
tcpdump -r "${OUTPUT_DIR}/capture.pcap" -nn 2>/dev/null | \
    awk '{print $3, "->", $5}' | sort -u | head -50

# Cleanup capture (contains potentially sensitive data)
rm -f "${OUTPUT_DIR}/capture.pcap"
echo ""
echo "Analysis complete. Capture file removed for security."
```

### 8.5 Management Network Isolation Verification

```bash
#!/usr/bin/env bash
# mgmt-isolation-verify.sh
# Verifies management network cannot be reached from VM networks

echo "=== Management Network Isolation Verification ==="
echo ""

# Identify management interface
MGMT_IFACE=$(ip route get 1 | awk '{print $5; exit}')
MGMT_IP=$(ip -4 addr show "${MGMT_IFACE}" | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
MGMT_SUBNET=$(ip -4 addr show "${MGMT_IFACE}" | grep -oP '(?<=inet\s)\d+(\.\d+){3}/\d+')

echo "Management interface: ${MGMT_IFACE} (${MGMT_SUBNET})"
echo ""

# Check: Can VMs reach management port 8006?
echo "--- Checking firewall rules protecting management ---"
echo ""

# iptables rules filtering management access
echo "iptables rules for port 8006:"
iptables -L -n -v | grep -E "8006|pve" | sed 's/^/  /'

echo ""
echo "nftables rules:"
nft list ruleset 2>/dev/null | grep -A2 -B2 "8006" | sed 's/^/  /'

# Check if VM bridges can route to management
echo ""
echo "--- Bridge-to-management routing assessment ---"
for bridge in $(ls /sys/class/net/ | grep vmbr); do
    bridge_ip=$(ip -4 addr show "${bridge}" | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)
    if [ -n "${bridge_ip}" ]; then
        echo "  ${bridge}: ${bridge_ip}"
        # Check if this is same subnet as management
        if [ "${bridge}" != "${MGMT_IFACE}" ]; then
            # Verify no route from this bridge to management port
            echo "    Route to management: $(ip route get ${MGMT_IP} from ${bridge_ip} 2>&1 | head -1)"
        fi
    fi
done
```

### 8.6 Storage Network Security Assessment

```bash
#!/usr/bin/env bash
# storage-network-audit.sh

echo "=== Storage Network Security Audit ==="
echo ""

# Identify storage interfaces (Ceph, iSCSI, NFS)
echo "--- Storage Interfaces ---"

# Ceph
if command -v ceph &>/dev/null; then
    echo "Ceph cluster network:"
    ceph config get mon cluster_network 2>/dev/null | sed 's/^/  /'
    echo "Ceph public network:"
    ceph config get mon public_network 2>/dev/null | sed 's/^/  /'
    echo ""
    
    # Verify Ceph traffic is encrypted (msgr2)
    echo "Ceph messenger protocol:"
    ceph config get global ms_cluster_mode 2>/dev/null | sed 's/^/  Cluster mode: /'
    ceph config get global ms_service_mode 2>/dev/null | sed 's/^/  Service mode: /'
    ceph config get global ms_client_mode 2>/dev/null | sed 's/^/  Client mode:  /'
fi

# iSCSI
echo ""
echo "--- iSCSI Configuration ---"
if [ -f /etc/iscsi/iscsid.conf ]; then
    echo "  CHAP authentication:"
    grep -i "chap" /etc/iscsi/iscsid.conf | grep -v "^#" | sed 's/^/    /'
    
    echo "  Connected targets:"
    iscsiadm -m session 2>/dev/null | sed 's/^/    /' || echo "    No active sessions"
fi

# NFS
echo ""
echo "--- NFS Mounts ---"
mount | grep nfs | while read -r line; do
    echo "  ${line}"
    # Check if using NFSv4 with Kerberos
    if echo "${line}" | grep -qv "sec=krb5"; then
        echo "    WARNING: Not using Kerberos authentication"
    fi
done

# Verify storage network isolation from VM networks
echo ""
echo "--- Storage Network Isolation ---"
# Storage traffic should NOT be on the same subnet as VM traffic
pvesm status --output-format json 2>/dev/null | python3 -c "
import sys, json
storages = json.load(sys.stdin)
for s in storages:
    stype = s.get('type', '')
    if stype in ('iscsi', 'nfs', 'cephfs', 'rbd', 'glusterfs'):
        print(f\"  {s['storage']:15s} type={stype:10s} active={s.get('active', 0)}\")
" 2>/dev/null
```

---

## 9. Backup and DR Compliance

### 9.1 Backup Encryption Verification

```bash
#!/usr/bin/env bash
# backup-encryption-audit.sh
# Verifies all backups are encrypted at rest

echo "=== Backup Encryption Audit ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Proxmox Backup Server verification
echo "--- Proxmox Backup Server ---"

# Check datastore encryption
if command -v proxmox-backup-manager &>/dev/null; then
    echo "Datastores:"
    proxmox-backup-manager datastore list 2>/dev/null | while read -r line; do
        echo "  ${line}"
    done
    
    # Check encryption key configuration
    for ds_path in /etc/proxmox-backup/datastore.d/*.cfg; do
        if [ -f "${ds_path}" ]; then
            ds_name=$(basename "${ds_path}" .cfg)
            echo ""
            echo "  Datastore: ${ds_name}"
            if grep -q "encryption" "${ds_path}"; then
                echo "    Encryption configured: YES"
            else
                echo "    Encryption configured: NO ** FINDING **"
            fi
        fi
    done
else
    echo "  PBS not installed on this node"
fi

echo ""
echo "--- Proxmox VE Backup Jobs ---"
# Check vzdump configuration for encryption
for job_file in /etc/pve/jobs.cfg; do
    if [ -f "${job_file}" ]; then
        echo "  Backup jobs from ${job_file}:"
        # Parse vzdump jobs
        grep -A10 "vzdump:" "${job_file}" | while read -r line; do
            if echo "${line}" | grep -q "encrypt"; then
                echo "    ${line}"
            fi
        done
    fi
done

# Verify backup files are actually encrypted
echo ""
echo "--- Backup File Encryption Verification ---"
# Sample check on recent backup files
BACKUP_STORE=$(pvesm status --output-format json 2>/dev/null | python3 -c "
import sys, json
storages = json.load(sys.stdin)
for s in storages:
    if s.get('content', '').find('backup') >= 0:
        print(s.get('path', s.get('storage', '')))
        break
" 2>/dev/null)

if [ -n "${BACKUP_STORE}" ] && [ -d "${BACKUP_STORE}" ]; then
    echo "  Checking backup store: ${BACKUP_STORE}"
    # Check if .enc extension present or header shows encryption
    find "${BACKUP_STORE}" -name "*.vma*" -newer /dev/null -mtime -7 | head -5 | while read -r f; do
        if file "${f}" | grep -qi "encrypted\|openssl"; then
            echo "    [ENCRYPTED] ${f}"
        elif echo "${f}" | grep -q "\.enc"; then
            echo "    [ENCRYPTED] ${f}"
        else
            echo "    [UNENCRYPTED] ${f} ** FINDING **"
        fi
    done
fi
```

### 9.2 Backup Integrity Testing

```bash
#!/usr/bin/env bash
# backup-integrity-test.sh
# Automated backup restore testing for compliance evidence

set -euo pipefail

REPORT_DIR="/var/audit/backup-test-$(date +%Y-%m-%d)"
LOG_FILE="${REPORT_DIR}/test-log.txt"
RESULTS_FILE="${REPORT_DIR}/results.json"

mkdir -p "${REPORT_DIR}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG_FILE}"; }

log "=== Backup Integrity Test Started ==="

# Select test candidates (one per backup policy/type)
TEST_VMS=(
    "100:daily-backup"
    "200:weekly-backup"
    "300:monthly-backup"
)

RESULTS=()

for entry in "${TEST_VMS[@]}"; do
    IFS=: read -r VMID POLICY <<< "${entry}"
    
    log "Testing VM ${VMID} (policy: ${POLICY})"
    
    # Find most recent backup
    BACKUP=$(vzdump-list 2>/dev/null | grep "vm-${VMID}" | tail -1 || \
        find /var/lib/vz/dump -name "vzdump-qemu-${VMID}-*" -printf '%T@ %p\n' | sort -n | tail -1 | awk '{print $2}')
    
    if [ -z "${BACKUP}" ]; then
        log "  ERROR: No backup found for VM ${VMID}"
        RESULTS+=("{\"vmid\":${VMID},\"policy\":\"${POLICY}\",\"status\":\"NO_BACKUP\",\"error\":\"No backup file found\"}")
        continue
    fi
    
    log "  Backup file: ${BACKUP}"
    
    # Verify backup checksum if available
    CHECKSUM_FILE="${BACKUP}.sha256"
    if [ -f "${CHECKSUM_FILE}" ]; then
        if sha256sum -c "${CHECKSUM_FILE}" &>/dev/null; then
            log "  Checksum verification: PASS"
        else
            log "  Checksum verification: FAIL"
            RESULTS+=("{\"vmid\":${VMID},\"policy\":\"${POLICY}\",\"status\":\"CHECKSUM_FAIL\"}")
            continue
        fi
    fi
    
    # Attempt restore to temporary VM (high ID range)
    TEST_VMID=$((VMID + 9000))
    log "  Restoring to temporary VM ${TEST_VMID}"
    
    RESTORE_START=$(date +%s)
    
    if qmrestore "${BACKUP}" "${TEST_VMID}" --unique true --force true 2>>"${LOG_FILE}"; then
        RESTORE_END=$(date +%s)
        RESTORE_DURATION=$((RESTORE_END - RESTORE_START))
        log "  Restore successful in ${RESTORE_DURATION}s"
        
        # Verify VM configuration is intact
        if [ -f "/etc/pve/qemu-server/${TEST_VMID}.conf" ]; then
            log "  Configuration file present: PASS"
            
            # Optional: Start VM and verify boot (if safe to do)
            # qm start ${TEST_VMID} && sleep 30 && qm status ${TEST_VMID}
            
            RESULTS+=("{\"vmid\":${VMID},\"policy\":\"${POLICY}\",\"status\":\"PASS\",\"restore_seconds\":${RESTORE_DURATION}}")
        else
            RESULTS+=("{\"vmid\":${VMID},\"policy\":\"${POLICY}\",\"status\":\"CONFIG_MISSING\"}")
        fi
        
        # Cleanup
        qm destroy "${TEST_VMID}" --purge true 2>>"${LOG_FILE}" || true
    else
        RESULTS+=("{\"vmid\":${VMID},\"policy\":\"${POLICY}\",\"status\":\"RESTORE_FAIL\"}")
        log "  Restore FAILED"
    fi
done

# Write results
echo "[$(printf '%s,' "${RESULTS[@]}" | sed 's/,$//')]" | python3 -m json.tool > "${RESULTS_FILE}"

log ""
log "=== Backup Integrity Test Complete ==="
log "Results: ${RESULTS_FILE}"

# Summary
PASS_COUNT=$(grep -c '"PASS"' "${RESULTS_FILE}" || echo 0)
TOTAL=${#TEST_VMS[@]}
log "Passed: ${PASS_COUNT}/${TOTAL}"
```

### 9.3 Retention Policy Compliance

```python
#!/usr/bin/env python3
"""
retention_compliance_check.py
Verifies backup retention meets policy requirements.
"""

import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path


# Define retention policies
RETENTION_POLICIES = {
    "production": {
        "daily": 7,       # Keep 7 daily backups
        "weekly": 4,      # Keep 4 weekly backups
        "monthly": 12,    # Keep 12 monthly backups
        "yearly": 3,      # Keep 3 yearly backups
    },
    "development": {
        "daily": 3,
        "weekly": 2,
        "monthly": 3,
        "yearly": 0,
    },
    "compliance": {  # For regulated data (PCI, HIPAA)
        "daily": 30,
        "weekly": 12,
        "monthly": 36,
        "yearly": 7,
    }
}


def check_retention_compliance(backup_store: str, vm_policies: dict[int, str]):
    """
    Check that each VM has backups meeting its retention policy.
    
    Args:
        backup_store: Path to backup storage
        vm_policies: Dict mapping VM ID to policy name
    """
    findings = []
    now = datetime.now(timezone.utc)
    
    for vmid, policy_name in vm_policies.items():
        policy = RETENTION_POLICIES.get(policy_name)
        if not policy:
            findings.append({
                "vmid": vmid,
                "severity": "HIGH",
                "finding": f"Unknown policy '{policy_name}' assigned"
            })
            continue
        
        # Get backup list for this VM
        backup_files = sorted(
            Path(backup_store).glob(f"**/vzdump-qemu-{vmid}-*.vma*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not backup_files:
            findings.append({
                "vmid": vmid,
                "severity": "CRITICAL",
                "finding": "No backups found"
            })
            continue
        
        # Check daily retention
        daily_required = policy["daily"]
        recent_backups = [
            f for f in backup_files
            if (now - datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)).days <= daily_required
        ]
        
        if len(recent_backups) < daily_required:
            findings.append({
                "vmid": vmid,
                "severity": "HIGH",
                "finding": f"Only {len(recent_backups)} backups in last {daily_required} days (need {daily_required})"
            })
        
        # Check oldest backup age for monthly requirement
        oldest = datetime.fromtimestamp(backup_files[-1].stat().st_mtime, tz=timezone.utc)
        months_covered = (now - oldest).days / 30
        
        if months_covered < policy["monthly"]:
            findings.append({
                "vmid": vmid,
                "severity": "MEDIUM",
                "finding": f"Oldest backup is {months_covered:.0f} months old (need {policy['monthly']} months)"
            })
    
    return findings


if __name__ == "__main__":
    # Example usage
    vm_policies = {
        100: "production",
        101: "production",
        200: "compliance",
        300: "development",
    }
    
    findings = check_retention_compliance("/var/lib/vz/dump", vm_policies)
    
    print("=== Retention Policy Compliance ===\n")
    if not findings:
        print("All VMs meet retention requirements.")
    else:
        for f in sorted(findings, key=lambda x: x["severity"]):
            print(f"  [{f['severity']:8s}] VM {f['vmid']}: {f['finding']}")
    
    # Export for evidence
    with open("retention-compliance.json", "w") as fp:
        json.dump({
            "audit_date": now.isoformat(),
            "findings": findings,
            "policies_applied": RETENTION_POLICIES,
        }, fp, indent=2, default=str)
```

### 9.4 DR Plan Testing

**DR test documentation template (compliance-ready):**

```
DISASTER RECOVERY TEST REPORT
===============================
Test ID:        DR-TEST-2026-Q2-001
Date Executed:  2026-05-07
Test Type:      Tabletop + Partial Technical Validation
Participants:   [Names/Roles]
Scope:          Full site failover of Production Cluster to DR site

SCENARIO:
Primary site (DC1) complete power failure. All Proxmox nodes offline.
Network connectivity to DC1 severed.

OBJECTIVES:
1. Validate VM recovery at DR site within RTO (4 hours)
2. Verify data loss within RPO (1 hour)
3. Confirm network connectivity from DR site
4. Validate application functionality post-failover

EXECUTION STEPS AND RESULTS:

Step 1: Detection and Declaration (Target: 15 min)
  Actual time: 12 minutes
  Status: PASS
  Notes: Monitoring alert triggered at T+2min. On-call engineer 
         acknowledged at T+5min. DR declaration at T+12min.

Step 2: DR Site Activation (Target: 30 min)
  Actual time: 25 minutes
  Status: PASS
  Notes: Proxmox Backup Server replication confirmed current.
         Last successful sync: T-45min (within RPO).

Step 3: VM Restoration (Target: 2 hours)
  Actual time: 1 hour 45 minutes
  Status: PASS
  Notes: 45 VMs restored from PBS. 3 VMs required manual 
         network reconfiguration (documented for improvement).

Step 4: Application Validation (Target: 1 hour)
  Actual time: 1 hour 30 minutes
  Status: PARTIAL PASS
  Notes: 42/45 applications validated. 3 applications with 
         external dependencies could not be fully validated 
         without DNS cutover.

OVERALL RESULT: PASS WITH OBSERVATIONS

RTO ACHIEVED: 3 hours 52 minutes (Target: 4 hours) ✓
RPO ACHIEVED: 45 minutes (Target: 1 hour) ✓

FINDINGS AND IMPROVEMENTS:
1. [MEDIUM] Three VMs require manual network config — automate with 
   post-restore scripts
2. [LOW] DR runbook page 12 has outdated IP addresses
3. [LOW] PBS restore UI slow with >20 concurrent restores — test 
   CLI-based parallel restore next quarter

SIGN-OFF:
  Infrastructure Lead: _____________ Date: _______
  Security Lead:       _____________ Date: _______
  Business Owner:      _____________ Date: _______
```

### 9.5 RTO/RPO Verification

```bash
#!/usr/bin/env bash
# rto-rpo-measurement.sh
# Measures actual RTO/RPO against defined targets

echo "=== RTO/RPO Compliance Measurement ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Define targets (from BCP documentation)
declare -A RTO_TARGETS  # in minutes
RTO_TARGETS[tier1]=60    # Critical business applications
RTO_TARGETS[tier2]=240   # Important business applications
RTO_TARGETS[tier3]=480   # Standard business applications

declare -A RPO_TARGETS  # in minutes
RPO_TARGETS[tier1]=15    # Near-zero data loss
RPO_TARGETS[tier2]=60    # Up to 1 hour data loss acceptable
RPO_TARGETS[tier3]=240   # Up to 4 hours acceptable

# Check actual replication/backup frequency
echo "--- RPO Assessment (Last Backup Age) ---"
echo ""

# Check PBS replication status
if command -v proxmox-backup-client &>/dev/null; then
    echo "Proxmox Backup Server - Last Sync:"
    # In practice, query PBS API for last successful backup per VM
fi

# Check local backup timestamps
for conf in /etc/pve/qemu-server/*.conf; do
    vmid=$(basename "${conf}" .conf)
    vm_name=$(grep "^name:" "${conf}" 2>/dev/null | awk '{print $2}')
    
    # Find most recent backup
    latest_backup=$(find /var/lib/vz/dump -name "vzdump-qemu-${vmid}-*" -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1)
    
    if [ -n "${latest_backup}" ]; then
        backup_epoch=$(echo "${latest_backup}" | awk '{print $1}' | cut -d. -f1)
        current_epoch=$(date +%s)
        age_minutes=$(( (current_epoch - backup_epoch) / 60 ))
        
        # Determine tier (in practice, from CMDB)
        tier="tier2"  # Default
        
        target=${RPO_TARGETS[${tier}]}
        status="PASS"
        if [ "${age_minutes}" -gt "${target}" ]; then
            status="FAIL"
        fi
        
        printf "  VM %s (%s): last backup %d min ago (target: %d min) [%s]\n" \
            "${vmid}" "${vm_name}" "${age_minutes}" "${target}" "${status}"
    fi
done
```

### 9.6 Backup Access Control Audit

```bash
#!/usr/bin/env bash
# backup-access-audit.sh

echo "=== Backup Access Control Audit ==="
echo ""

# Who can access backup storage?
echo "--- Backup Storage Permissions ---"
pvesm status --output-format json 2>/dev/null | python3 -c "
import sys, json, subprocess
storages = json.load(sys.stdin)
for s in storages:
    content = s.get('content', '')
    if 'backup' in content:
        print(f\"Storage: {s['storage']} (type: {s['type']})\")
        # Check filesystem permissions
        path = s.get('path', '')
        if path:
            import os
            if os.path.exists(path):
                stat = os.stat(path)
                print(f'  Path: {path}')
                print(f'  Owner: {stat.st_uid}:{stat.st_gid}')
                print(f'  Permissions: {oct(stat.st_mode)}')
" 2>/dev/null

# Who can trigger backups (vzdump privilege)?
echo ""
echo "--- Users with Backup Privileges ---"
pveum acl list --output-format json 2>/dev/null | python3 -c "
import sys, json, subprocess
acls = json.load(sys.stdin)
# Roles that include VM.Backup or Datastore.AllocateSpace
backup_roles = ['Administrator', 'PVEAdmin', 'PVEDatastoreAdmin']
for acl in acls:
    if acl.get('roleid') in backup_roles:
        print(f\"  {acl.get('type',''):5s} {acl.get('ugid',''):25s} role={acl.get('roleid',''):20s} path={acl.get('path','/')}\")
" 2>/dev/null

# PBS access (if available)
echo ""
echo "--- Proxmox Backup Server Access ---"
if [ -f /etc/proxmox-backup/user.cfg ]; then
    echo "  PBS Users:"
    grep "^user:" /etc/proxmox-backup/user.cfg | sed 's/^/    /'
fi
```

---

## 10. Audit Reporting and Remediation

### 10.1 Audit Report Structure

**Comprehensive virtual infrastructure audit report template:**

```
╔══════════════════════════════════════════════════════════════╗
║     VIRTUAL INFRASTRUCTURE COMPLIANCE AUDIT REPORT         ║
╠══════════════════════════════════════════════════════════════╣
║ Report ID:     VIRT-AUDIT-2026-001                         ║
║ Classification: CONFIDENTIAL                                ║
║ Date:          2026-05-07                                   ║
║ Auditor:       [Name, Certification]                        ║
║ Scope:         Production VMware/Proxmox Infrastructure     ║
║ Standard:      CIS Benchmark / DISA STIG / PCI-DSS 4.0     ║
╚══════════════════════════════════════════════════════════════╝

TABLE OF CONTENTS
=================
1. Executive Summary
2. Scope and Methodology
3. Infrastructure Overview
4. Findings Summary
5. Detailed Findings
6. Remediation Recommendations
7. Evidence Index
8. Appendices

1. EXECUTIVE SUMMARY
=====================
This audit assessed [N] hypervisor hosts, [N] virtual machines, and 
[N] management systems against [framework(s)]. The assessment identified:

  CRITICAL findings: [N] (require immediate action)
  HIGH findings:     [N] (remediate within 30 days)
  MEDIUM findings:   [N] (remediate within 90 days)
  LOW findings:      [N] (remediate within 180 days)

Overall compliance score: [X]% (target: 95%)

Key concerns:
- [Top 3 critical issues in plain language]
- [Business risk statement]

2. SCOPE AND METHODOLOGY
=========================
In-Scope Systems:
- vCenter Server: vcenter.corp.local (version 8.0 U3)
- ESXi Hosts: esxi-01 through esxi-08 (version 8.0 U3)
- Proxmox Nodes: pve-01 through pve-04 (version 8.2-1)
- Virtual Machines: [N] production VMs
- Network: [N] virtual switches, [N] VLANs
- Storage: [description]
- Backup: [description]

Out-of-Scope:
- Physical security (covered under separate audit)
- Guest OS hardening (covered under server hardening audit)
- Application security (covered under application security program)

Methodology:
- Automated scanning: [tools used]
- Manual verification: [areas requiring manual assessment]
- Configuration review: PowerCLI, pvesh, direct inspection
- Interviews: [roles interviewed]
- Evidence collection: Automated scripts with SHA-256 manifests

Standards Applied:
- CIS VMware ESXi 8.0 Benchmark v1.1.0 (Level 1 + Level 2)
- DISA STIG vSphere 8.0 V1R1
- PCI-DSS 4.0 Requirements 2, 6, 10, 11
- ISO 27001:2022 Annex A technological controls

3. INFRASTRUCTURE OVERVIEW
============================
[Architecture diagram]
[Host inventory table]
[VM inventory summary by classification]
[Network topology summary]

4. FINDINGS SUMMARY
====================
| ID | Severity | Category | Finding | Affected Systems |
|----|----------|----------|---------|------------------|
| F-001 | CRITICAL | Access | SSH enabled on production ESXi hosts | esxi-03, esxi-05 |
| F-002 | CRITICAL | TLS | TLS 1.0/1.1 not disabled | esxi-01 through esxi-04 |
| F-003 | HIGH | Logging | No syslog forwarding configured | esxi-02 |
| F-004 | HIGH | Access | Lockdown mode disabled | esxi-05, esxi-06 |
| ... | ... | ... | ... | ... |

5. DETAILED FINDINGS
=====================

--- FINDING F-001 ---
Severity:       CRITICAL
Category:       Access Control
CIS Control:    2.2 (Ensure SSH is disabled)
STIG ID:        V-ESXI-80-000002
PCI-DSS Ref:    Req 2.2.2 (Disable unnecessary services)

Description:
SSH service is running and set to auto-start on ESXi hosts esxi-03 
and esxi-05. This provides a direct attack vector bypassing vCenter 
management controls and lockdown mode protections.

Impact:
- Direct interactive shell access to hypervisor
- Bypasses lockdown mode controls
- Enables brute-force authentication attacks
- Increases attack surface for known SSH vulnerabilities

Evidence:
- PowerCLI output: [reference to evidence file]
- Nessus plugin 12345: [reference to scan results]
- Screenshot: [reference to screenshot evidence]

Remediation:
1. Disable SSH service:
   Get-VMHost esxi-03,esxi-05 | Get-VMHostService | 
     Where-Object {$_.Key -eq "TSM-SSH"} | 
     Set-VMHostService -Policy Off | Stop-VMHostService
2. Document exception process for maintenance SSH access
3. Implement monitoring alert when SSH is enabled

Verification:
After remediation, verify with:
   Get-VMHost | Get-VMHostService | Where-Object {$_.Key -eq "TSM-SSH"} |
     Select-Object VMHost, Running, Policy

6. REMEDIATION RECOMMENDATIONS
================================
[Priority-ordered remediation plan]
[Quick wins vs. longer-term improvements]
[Resource requirements]

7. EVIDENCE INDEX
==================
| Evidence ID | Type | Description | Hash (SHA-256) | Location |
|-------------|------|-------------|----------------|----------|
| E-001 | Script output | CIS benchmark assessment | abc123... | /evidence/cis/ |
| E-002 | Screenshot | SSH service status | def456... | /evidence/screenshots/ |
| ... | ... | ... | ... | ... |

8. APPENDICES
==============
A. Tools and Versions Used
B. Full Scan Results (attached)
C. Configuration Exports
D. Interview Notes
E. Glossary of Terms
```

### 10.2 Risk Rating for Virtual Infrastructure Findings

Custom risk matrix accounting for virtualization-specific amplification:

| Base Severity | Hypervisor Layer | Management Plane | Guest Level | Network |
|---|---|---|---|---|
| Informational | Low | Low | Informational | Low |
| Low | Medium | Medium | Low | Low |
| Medium | High | High | Medium | Medium |
| High | Critical | Critical | High | High |
| Critical | Critical+ (Immediate) | Critical+ (Immediate) | Critical | Critical |

**Risk score calculation:**

```
Risk Score = Likelihood × Impact × Context Multiplier

Where:
- Likelihood (1-5): Based on exploitability, attack vector, privileges required
- Impact (1-5): Based on scope (single VM vs all VMs), data sensitivity
- Context Multiplier:
  - Hypervisor kernel vulnerability: 2.0
  - Management plane (vCenter/Proxmox): 1.8
  - Shared resource (storage/network): 1.5
  - Single VM guest level: 1.0
  - Development environment: 0.7
```

### 10.3 Remediation Tracking

```json
{
  "remediation_tracker": {
    "report_id": "VIRT-AUDIT-2026-001",
    "generated": "2026-05-07T14:00:00Z",
    "items": [
      {
        "finding_id": "F-001",
        "severity": "CRITICAL",
        "title": "SSH enabled on production ESXi hosts",
        "priority": 1,
        "owner": "Infrastructure Team Lead",
        "assigned_to": "john.doe@corp.local",
        "deadline": "2026-05-14",
        "status": "IN_PROGRESS",
        "status_history": [
          {"date": "2026-05-07", "status": "OPEN", "notes": "Finding identified during audit"},
          {"date": "2026-05-08", "status": "IN_PROGRESS", "notes": "Change ticket CR-2026-0456 created"}
        ],
        "remediation_plan": "Disable SSH via PowerCLI, implement alerting for SSH enable events",
        "verification_method": "Re-run CIS control 2.2 check via automated script",
        "compensating_controls": "Monitoring alert fires if SSH enabled >5 minutes",
        "risk_accepted": false
      },
      {
        "finding_id": "F-002",
        "severity": "CRITICAL",
        "title": "TLS 1.0/1.1 not disabled on ESXi hosts",
        "priority": 2,
        "owner": "Infrastructure Team Lead",
        "assigned_to": "jane.smith@corp.local",
        "deadline": "2026-05-21",
        "status": "PLANNED",
        "remediation_plan": "Apply TLS 1.2 minimum via advanced setting, test client compatibility first",
        "verification_method": "SSL scan confirming only TLS 1.2+ accepted",
        "dependencies": ["Verify all management tools support TLS 1.2+"],
        "risk_accepted": false
      }
    ],
    "summary": {
      "total": 25,
      "critical_open": 2,
      "high_open": 5,
      "medium_open": 8,
      "low_open": 10,
      "closed": 0,
      "risk_accepted": 0
    }
  }
}
```

### 10.4 Plan of Action and Milestones (POA&M)

```
PLAN OF ACTION AND MILESTONES (POA&M)
=======================================
System Name:     Corporate Virtual Infrastructure
System Owner:    [Name]
Date Prepared:   2026-05-07
Next Review:     2026-06-07

┌────┬──────────────┬────────────┬────────────────────────┬──────────┬──────────┬────────┐
│ #  │ Weakness     │ Severity   │ Milestones             │ Resources│ Target   │ Status │
├────┼──────────────┼────────────┼────────────────────────┼──────────┼──────────┼────────┤
│ 1  │ SSH enabled  │ CRITICAL   │ M1: Change ticket      │ 2 hrs    │ 05/08    │ Done   │
│    │ on prod ESXi │ CAT I      │ M2: Disable SSH        │ Infra    │ 05/10    │ Open   │
│    │              │            │ M3: Verify + evidence  │ team     │ 05/11    │ Open   │
│    │              │            │ M4: Alert implemented  │          │ 05/14    │ Open   │
├────┼──────────────┼────────────┼────────────────────────┼──────────┼──────────┼────────┤
│ 2  │ Weak TLS     │ CRITICAL   │ M1: Compatibility test │ 4 hrs    │ 05/12    │ Open   │
│    │ versions     │ CAT I      │ M2: Apply fix (maint.) │ Infra +  │ 05/17    │ Open   │
│    │              │            │ M3: SSL scan verify    │ Security │ 05/18    │ Open   │
│    │              │            │ M4: Close finding      │          │ 05/21    │ Open   │
├────┼──────────────┼────────────┼────────────────────────┼──────────┼──────────┼────────┤
│ 3  │ Missing      │ HIGH       │ M1: Design syslog arch │ 8 hrs    │ 05/15    │ Open   │
│    │ syslog       │ CAT II     │ M2: Deploy collector   │ Infra +  │ 05/22    │ Open   │
│    │ forwarding   │            │ M3: Configure hosts    │ SIEM     │ 05/29    │ Open   │
│    │              │            │ M4: Verify logs flow   │ team     │ 06/01    │ Open   │
└────┴──────────────┴────────────┴────────────────────────┴──────────┴──────────┴────────┘

RISK ACCEPTANCE (If applicable):
Finding #: N/A (no findings accepted at this time)

REVIEW AND APPROVAL:
System Owner:     _____________ Date: _______
ISSO:             _____________ Date: _______
Authorizing Ofcl: _____________ Date: _______
```

### 10.5 Continuous Compliance Monitoring Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                 CONTINUOUS COMPLIANCE MONITORING                          │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────┐
│ Hypervisors │    │ Config Mgmt  │    │ Compliance       │    │ Dashboard│
│ ESXi/Proxmox├───→│ Ansible/Salt ├───→│ Scanner         ├───→│ & Alert  │
│             │    │              │    │ (InSpec/OpenSCAP)│    │          │
└─────────────┘    └──────────────┘    └─────────────────┘    └──────────┘
       │                                        │                     │
       │           ┌──────────────┐             │                     │
       └──────────→│ SIEM         │←────────────┘                     │
                   │ (Wazuh/Elk)  │                                   │
                   │              │←──────────────────────────────────┘
                   └──────┬───────┘
                          │
                   ┌──────▼───────┐
                   │ Ticket System │
                   │ (JIRA/ServiceNow)
                   └──────────────┘

COMPONENTS:

1. Configuration Drift Detection (runs hourly):
   - Ansible/Salt enforces desired state
   - Any drift triggers alert + auto-remediation (for approved items)
   - Non-approved drift triggers investigation ticket

2. Compliance Scanning (runs daily):
   - InSpec profiles for CIS/STIG
   - Results stored in compliance database
   - Trend reporting (improving/degrading)

3. Vulnerability Scanning (runs weekly):
   - Credentialed scan of all hypervisors
   - Automatic correlation with asset criticality
   - Integration with patch management workflow

4. Log-Based Monitoring (real-time):
   - Configuration change events → immediate alert
   - Authentication anomalies → investigation trigger
   - Service state changes (SSH enabled) → automated response

5. Reporting (automated):
   - Daily: Compliance score dashboard
   - Weekly: New findings + remediation progress
   - Monthly: Executive summary + trend analysis
   - Quarterly: Full compliance report for governance
```

**Ansible playbook for continuous compliance check:**

```yaml
---
# playbook: continuous-compliance.yml
# Scheduled via cron/systemd timer for regular compliance verification
# Reports drift from baseline

- name: Continuous Compliance Check
  hosts: all_hypervisors
  become: true
  vars:
    compliance_api: "https://compliance.corp.local/api/v1"
    alert_webhook: "https://alerts.corp.local/webhook/compliance"
    
  tasks:
    - name: Run InSpec CIS profile
      ansible.builtin.command:
        cmd: >
          inspec exec /opt/compliance/cis-profile
          --reporter json:/tmp/inspec-results.json
          --chef-license accept-silent
      register: inspec_result
      failed_when: false
      changed_when: false

    - name: Parse InSpec results
      ansible.builtin.slurp:
        src: /tmp/inspec-results.json
      register: inspec_json

    - name: Calculate compliance score
      ansible.builtin.set_fact:
        compliance_data: "{{ inspec_json.content | b64decode | from_json }}"

    - name: Report compliance status
      ansible.builtin.uri:
        url: "{{ compliance_api }}/report"
        method: POST
        body_format: json
        body:
          host: "{{ inventory_hostname }}"
          timestamp: "{{ ansible_date_time.iso8601 }}"
          total_controls: "{{ compliance_data.statistics.controls.total }}"
          passed: "{{ compliance_data.statistics.controls.passed.total }}"
          failed: "{{ compliance_data.statistics.controls.failed.total }}"
          skipped: "{{ compliance_data.statistics.controls.skipped.total }}"
          score: "{{ (compliance_data.statistics.controls.passed.total | int / compliance_data.statistics.controls.total | int * 100) | round(1) }}"
        headers:
          Authorization: "Bearer {{ lookup('env', 'COMPLIANCE_API_TOKEN') }}"
      when: compliance_data is defined

    - name: Alert on critical failures
      ansible.builtin.uri:
        url: "{{ alert_webhook }}"
        method: POST
        body_format: json
        body:
          severity: "critical"
          host: "{{ inventory_hostname }}"
          message: "Compliance score below threshold"
          details: "{{ compliance_data.statistics }}"
      when:
        - compliance_data is defined
        - (compliance_data.statistics.controls.passed.total | int / compliance_data.statistics.controls.total | int * 100) < 85

    - name: Cleanup
      ansible.builtin.file:
        path: /tmp/inspec-results.json
        state: absent
```

### 10.6 Preparing for External Audits

**Pre-audit checklist for virtual infrastructure:**

```
EXTERNAL AUDIT PREPARATION CHECKLIST
=====================================
Audit Type: [PCI-DSS QSA / SOC 2 Type II / ISO 27001 / Custom]
Auditor:    [Firm name]
Dates:      [Start - End]
Lead:       [Internal contact]

PRE-AUDIT (4 weeks before):
□ Run full internal compliance scan — identify and remediate gaps
□ Update all documentation (architecture diagrams, policies, procedures)
□ Prepare dedicated auditor accounts (read-only, time-limited)
□ Verify all evidence collection automation is functioning
□ Run backup integrity test (evidence of working backups)
□ Complete access review (evidence of quarterly review)
□ Verify log retention (12 months for PCI, verify availability)
□ Update risk register with virtual infrastructure items
□ Prepare POA&M status (show remediation progress)
□ Brief infrastructure team on audit logistics

EVIDENCE PREPARATION (2 weeks before):
□ Generate fresh configuration exports (all hypervisors)
□ Collect 90-day sample of change management tickets
□ Export access control reports (current state + last review)
□ Compile vulnerability scan results (quarterly reports)
□ Gather patch management records (application evidence)
□ Prepare incident response documentation (past incidents + drills)
□ Document compensating controls for any known gaps
□ Screenshot GUI configurations that cannot be exported

LOGISTICS (1 week before):
□ Auditor workspace prepared (network access, conference room)
□ VPN/remote access configured for auditor if needed
□ Point-of-contact schedule distributed
□ Evidence repository organized and indexed
□ Technical SMEs scheduled for walkthroughs
□ Management available for governance interviews

DURING AUDIT:
□ Respond to information requests within 24 hours
□ Track all requests in shared document
□ Note any areas where auditor identifies gaps (remediate immediately if possible)
□ Do not make configuration changes during audit period without coordination
□ Document any demonstrations performed live

POST-AUDIT:
□ Review draft findings before report finalization
□ Provide management response for each finding
□ Create remediation plan for any new findings
□ Update POA&M with new items
□ Schedule follow-up assessment for remediated items
□ Lessons learned — update internal processes
```

**Auditor account provisioning script:**

```bash
#!/usr/bin/env bash
# provision-auditor.sh
# Creates time-limited read-only auditor accounts

set -euo pipefail

AUDITOR_NAME="${1:?Usage: $0 <auditor_name> <days_valid>}"
DAYS_VALID="${2:-14}"
EXPIRE_DATE=$(date -d "+${DAYS_VALID} days" +%s)
AUDIT_ROLE="PVEAuditor"

echo "Provisioning auditor account: ${AUDITOR_NAME}"
echo "Valid for: ${DAYS_VALID} days (expires: $(date -d "+${DAYS_VALID} days" +%Y-%m-%d))"
echo ""

# Generate secure random password
PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 20)

# Create Proxmox account
pveum user add "${AUDITOR_NAME}@pam" \
    --comment "External auditor - expires $(date -d "+${DAYS_VALID} days" +%Y-%m-%d)" \
    --expire "${EXPIRE_DATE}" \
    --enable 1

# Set password
echo -e "${PASSWORD}\n${PASSWORD}" | pveum passwd "${AUDITOR_NAME}@pam"

# Assign read-only role at datacenter level
pveum acl modify / --users "${AUDITOR_NAME}@pam" --roles "${AUDIT_ROLE}"

# Create Linux account for SSH-based evidence collection (if needed)
useradd -m -s /bin/bash -e "$(date -d "+${DAYS_VALID} days" +%Y-%m-%d)" \
    -c "External Auditor" "${AUDITOR_NAME}" 2>/dev/null || true

echo ""
echo "=== Account Created ==="
echo "Username: ${AUDITOR_NAME}@pam"
echo "Password: ${PASSWORD}"
echo "Role: ${AUDIT_ROLE} (read-only)"
echo "Scope: / (all datacenter)"
echo "Expires: $(date -d "+${DAYS_VALID} days" +%Y-%m-%d)"
echo ""
echo "IMPORTANT: Deliver credentials via secure channel. Delete this output."
echo "Post-audit: Run 'pveum user delete ${AUDITOR_NAME}@pam' to remove."
```

---

## Appendix A: Quick Reference — Framework Control Mapping

| Control Area | PCI-DSS 4.0 | HIPAA | SOC 2 | ISO 27001 | CIS ESXi | STIG |
|---|---|---|---|---|---|---|
| Access control | 7.1-7.3 | §164.312(a) | CC6.1-6.3 | A.5.15, A.8.5 | 4.x | Multiple |
| Logging | 10.1-10.7 | §164.312(b) | CC7.1 | A.8.15 | 3.x | Multiple |
| Encryption (transit) | 4.1-4.2 | §164.312(e) | CC6.7 | A.8.24 | 2.4 | TLS controls |
| Encryption (rest) | 3.5-3.7 | §164.312(a)(2)(iv) | CC6.7 | A.8.24 | 6.x | VM encryption |
| Patching | 6.3 | §164.308(a)(1) | CC8.1 | A.8.8 | 1.x | Patching |
| Network segmentation | 1.2-1.4 | §164.312(e) | CC6.6 | A.8.20 | 7.x | vNetwork |
| Change management | 6.5 | §164.308(a)(8) | CC8.1 | A.8.9 | N/A | CM controls |
| Vulnerability mgmt | 11.3 | §164.308(a)(1) | CC7.1 | A.8.8 | N/A | Scanning |
| Backup/DR | N/A | §164.308(a)(7) | A1.2-A1.3 | A.8.13-14 | N/A | N/A |
| Incident response | 12.10 | §164.308(a)(6) | CC7.3-7.5 | A.5.24-28 | N/A | N/A |

## Appendix B: Automation Tool Matrix

| Task | VMware Tool | Proxmox Tool | Cross-Platform |
|---|---|---|---|
| CIS Assessment | PowerCLI script | Ansible + InSpec | InSpec with custom transports |
| STIG Assessment | PowerCLI + STIG Viewer | N/A (no Proxmox STIG) | OpenSCAP (Linux STIG for Proxmox) |
| Vulnerability Scan | Nessus (VMware policy) | Nessus (Linux policy) | Qualys, Rapid7 |
| Configuration Backup | PowerCLI export | pvesh + file copy | Ansible facts gathering |
| Access Review | PowerCLI Get-VIPermission | pveum commands | Custom correlation scripts |
| Log Forwarding | ESXi syslog settings | rsyslog/journald | Common SIEM integration |
| Compliance Dashboard | vRealize Operations | Custom (Grafana + API) | SIEM-based dashboards |
| Drift Detection | vCenter Config Profiles | Ansible --check mode | Chef InSpec + custom profiles |
| Patch Assessment | vLCM | apt + Proxmox advisories | WSUS/SCCM for guests |

## Appendix C: Common Audit Findings Severity Reference

**CRITICAL (Remediate within 7 days):**
- Hypervisor with default credentials
- Unpatched hypervisor with known exploited vulnerabilities (KEV)
- VM escape vulnerability present
- Management interface exposed to internet
- No audit logging configured
- Backup encryption keys stored alongside backups

**HIGH (Remediate within 30 days):**
- SSH enabled without justification
- Weak TLS versions accepted
- No lockdown mode
- Missing syslog forwarding
- Service accounts with excessive privileges
- API tokens without expiration
- No MFA on management access

**MEDIUM (Remediate within 90 days):**
- Non-optimal password complexity
- Missing NTP synchronization
- Promiscuous mode enabled on port groups
- Incomplete backup testing
- Access reviews overdue
- Certificates expiring within 60 days

**LOW (Remediate within 180 days):**
- Shell timeout not configured to standard
- SNMP enabled but using v3 (acceptable but unnecessary)
- Minor documentation gaps
- Non-critical configuration drift
- Cosmetic policy naming inconsistencies

---

## Appendix D: Evidence Retention Requirements

| Framework | Minimum Retention | Notes |
|---|---|---|
| PCI-DSS 4.0 | 12 months (logs), policy period (policies) | 3 months immediately accessible |
| HIPAA | 6 years (policies), retention per policy (data) | From date of creation or last effective date |
| SOC 2 | Audit period + 1 year typical | Retain for the assertion period minimum |
| ISO 27001 | 3 years minimum (records) | Per documented retention schedule |
| DISA STIG | Duration of system operation | Until system decommissioned |
| Internal audit | 5 years recommended | Supports trend analysis and recertification |

---

*End of document.*
