# 17 — Identity, Access & Credential Inventory

**Assessment Date:** 2026-05-26
**Machine:** PCFRANCESCA (HP ProBook 450 G7)
**Current IP:** 192.168.192.61 (Adami_Guest Wi-Fi)
**Assessor:** sandro / macena IT Security
**Purpose:** Complete extraction and cataloging of all accounts, credentials, permissions, group memberships, and access tokens present on this machine.

> **For IT:** This document is the raw inventory. Every credential found here represents something an attacker could extract if they compromise this machine. IT should decide which credentials need rotation, which profiles need cleanup, and which access paths need to be revoked.

---

## Part 1 — Account Matrix

### 1.1 Local User Accounts

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        LOCAL ACCOUNTS INVENTORY                           │
│                                                                          │
│  Machine SID: S-1-5-21-872622826-2128076652-1825121607                  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  ACCOUNT: sandro                                    ACTIVE ★  │      │
│  │                                                                │      │
│  │  SID:              S-1-5-21-...-1003 (RID 1003)              │      │
│  │  Enabled:          YES                                        │      │
│  │  Password Required: NO                                        │      │
│  │  Password Set:     2025-11-03 09:24:07                       │      │
│  │  Password Expires: NEVER                                      │      │
│  │  Last Logon:       2026-05-26 08:40:58 (TODAY)               │      │
│  │  Can Change Pwd:   YES                                        │      │
│  │  Account Expires:  NEVER                                      │      │
│  │  Description:      (empty)                                    │      │
│  │  Groups:           Administrators                             │      │
│  │                                                                │      │
│  │  ⚠ CRITICAL: Local admin with NO PASSWORD                    │      │
│  │  ⚠ SMB/WMI/PsExec all work without credentials              │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  ACCOUNT: Administrator                           DISABLED    │      │
│  │                                                                │      │
│  │  SID:              S-1-5-21-...-500 (Built-in)               │      │
│  │  Enabled:          NO                                         │      │
│  │  Password Required: NO                                        │      │
│  │  Password Set:     2020-05-05 22:04:13 (6 YEARS OLD)        │      │
│  │  Last Logon:       2021-03-20 12:31:08                       │      │
│  │  Account Expires:  NEVER                                      │      │
│  │  Description:      Account predefinito per                    │      │
│  │                    l'amministrazione del computer/dominio     │      │
│  │  Groups:           Administrators                             │      │
│  │                                                                │      │
│  │  ⚠ Disabled but password is 6 years old with no complexity  │      │
│  │  ⚠ Built-in admin SID-500 bypasses some security controls   │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  ACCOUNT: ASPNET                                    ACTIVE ⚠  │      │
│  │                                                                │      │
│  │  SID:              S-1-5-21-...-1002 (RID 1002)              │      │
│  │  Enabled:          YES                                        │      │
│  │  Password Required: NO                                        │      │
│  │  Password Set:     2022-02-09 14:02:24                       │      │
│  │  Can Change Pwd:   NO (locked)                                │      │
│  │  Last Logon:       NEVER                                      │      │
│  │  Description:      Account used for running the ASP.NET       │      │
│  │                    worker process (aspnet_wp.exe)             │      │
│  │  Groups:           Users                                      │      │
│  │                                                                │      │
│  │  ⚠ HIGH: Enabled, no password, never used                   │      │
│  │  ⚠ Created for IIS but IIS is not running                   │      │
│  │  ⚠ Can be used for SMB authentication with no password      │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  ACCOUNT: Guest                                   DISABLED    │      │
│  │                                                                │      │
│  │  SID:              S-1-5-21-...-501 (Built-in)               │      │
│  │  Enabled:          NO                                         │      │
│  │  Password Required: NO                                        │      │
│  │  Can Change Pwd:   NO                                         │      │
│  │  Last Logon:       2023-05-12 12:37:37 ← INVESTIGATE         │      │
│  │  Groups:           Guests                                     │      │
│  │                                                                │      │
│  │  ⚠ MEDIUM: Guest should NEVER have login history            │      │
│  │  ⚠ Someone used this account in May 2023                    │      │
│  │  ⚠ Date overlaps with AnyDesk activity from 905591417       │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  ACCOUNT: CHIARA                                  DELETED ✗   │      │
│  │                                                                │      │
│  │  SID:              S-1-5-21-...-1001 (RID 1001)              │      │
│  │  Status:           ACCOUNT DELETED — profile remains         │      │
│  │  SID Resolution:   FAILS (account no longer exists)          │      │
│  │  Profile Path:     C:\Users\CHIARA (still on disk)           │      │
│  │  Profile Last Use: 2026-05-26 08:50:54 (TODAY — tasks run)   │      │
│  │                                                                │      │
│  │  ⚠ HIGH: Profile contains credentials, VPN certs,           │      │
│  │  browser passwords, corporate data, digital signature data    │      │
│  │  ⚠ 12+ scheduled tasks still run under this deleted SID     │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  ACCOUNT: DefaultAccount                          DISABLED    │      │
│  │  SID: S-1-5-21-...-503   | System managed | LOW risk         │      │
│  ├────────────────────────────────────────────────────────────────┤      │
│  │  ACCOUNT: WDAGUtilityAccount                      DISABLED    │      │
│  │  SID: S-1-5-21-...-504   | Password REQUIRED (correct)       │      │
│  │  Password Expires: 2020-06-16 (expired — normal for unused)  │      │
│  └────────────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Domain Account (Cached)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    DOMAIN ACCOUNT — CACHED ON MACHINE                     │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  ACCOUNT: elena.malini                            DOMAIN ⬡    │      │
│  │                                                                │      │
│  │  SID:           S-1-5-21-3521058280-4105139221-               │      │
│  │                 2070416120-1247                                │      │
│  │  Domain SID:    S-1-5-21-3521058280-4105139221-2070416120     │      │
│  │  RID:           1247                                          │      │
│  │  Domain:        adamitrasporti.local (inferred)              │      │
│  │  Profile Path:  C:\Users\elena.malini                        │      │
│  │  Profile Created: ~2025-03-01                                │      │
│  │  Last Profile Use: 2026-05-26 08:50:57                       │      │
│  │  Roaming Profile: NO                                          │      │
│  │  SID Resolution:  FAILS (domain unreachable from guest WiFi) │      │
│  │                                                                │      │
│  │  HOW WE KNOW THIS IS A DOMAIN ACCOUNT:                       │      │
│  │  The SID prefix S-1-5-21-3521058280-... does NOT match       │      │
│  │  the local machine SID S-1-5-21-872622826-...                │      │
│  │  Therefore it originates from a different security authority  │      │
│  │  — the Active Directory domain adamitrasporti.local.         │      │
│  │                                                                │      │
│  │  IMPLICATIONS:                                                │      │
│  │  • This machine authenticated to the domain at some point    │      │
│  │  • Cached domain credentials (DCC2 hash) may be in the       │      │
│  │    SECURITY registry hive                                     │      │
│  │  • If the machine is compromised, the attacker could         │      │
│  │    extract elena.malini's domain password hash                │      │
│  │  • The machine is NOT currently domain-joined (WORKGROUP)    │      │
│  └────────────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Account Risk Summary

| Account | Type | Status | Password | Admin | Last Logon | Risk |
|---------|------|--------|----------|-------|------------|------|
| sandro | Local | **ACTIVE** | **NONE** | **YES** | Today | **CRITICAL** |
| ASPNET | Local | **ACTIVE** | **NONE** | No | Never | **HIGH** |
| CHIARA | Local | **DELETED** | Profile on disk | Was unknown | Profile: today | **HIGH** |
| elena.malini | Domain | Cached | DCC2 in registry | Unknown | Profile: today | **HIGH** |
| Guest | Local | Disabled | None | No | 2023-05-12 | **MEDIUM** |
| Administrator | Local | Disabled | 6yr old, no req. | Yes | 2021-03-20 | **MEDIUM** |
| DefaultAccount | System | Disabled | None | No | Never | LOW |
| WDAGUtilityAccount | System | Disabled | Required/expired | No | Never | LOW |

---

## Part 2 — Group Memberships

### 2.1 Local Groups with Members

| Group | Members | Security Notes |
|-------|---------|---------------|
| **Administrators** | `PCFRANCESCA\Administrator` (disabled), `PCFRANCESCA\sandro` (active, no pwd) | Only local accounts — no domain groups |
| **Users** | `NT AUTHORITY\Authenticated Users`, `NT AUTHORITY\INTERACTIVE`, `PCFRANCESCA\ASPNET` | ASPNET is in Users group — can authenticate locally |
| **Guests** | `PCFRANCESCA\Guest` (disabled) | Standard, low risk |
| **IIS_IUSRS** | `NT AUTHORITY\IUSR` | IIS group exists — implies IIS was installed at some point |
| **System Managed Accounts** | `PCFRANCESCA\DefaultAccount` | Standard, low risk |

### 2.2 Empty Groups (No Members)

These groups exist but have no members. Some are relevant:

| Group | Relevance |
|-------|-----------|
| Amministratori Hyper-V | Hyper-V is installed (services present) |
| Backup Operators | Could be used for privilege escalation (SeBackupPrivilege) |
| Cryptographic Operators | Access to crypto operations |
| **Utenti desktop remoto** (Remote Desktop Users) | Empty = RDP not configured for non-admins |
| **Utenti gestione remota** (Remote Management Users) | Empty = WinRM not configured for non-admins |
| Utenti OpenSSH | OpenSSH may be installed |
| Network Configuration Operators | Network config rights |
| Power Users | Legacy group |
| Replicator | Legacy group |

### 2.3 What Group Membership Means for Attackers

```
ESCALATION PATHS VIA GROUPS:

  1. sandro is in Administrators
     → Full local admin: can read SAM, install software, modify services
     → Can access admin shares (C$, ADMIN$, IPC$)
     → Can run as SYSTEM via PsExec/scheduled tasks
     → NO PASSWORD REQUIRED for any of this

  2. ASPNET is in Users
     → Can authenticate via SMB (no password)
     → Can access "Users" share (Everyone = Full)
     → Cannot directly escalate, but can read sensitive files
     → Could be used as initial foothold for privilege escalation

  3. NT AUTHORITY\INTERACTIVE in Users
     → Anyone physically at the console (or via AnyDesk/RDP)
       gets automatic membership in Users group
     → Plus: INTERACTIVE has Full access to admin shares
       (C$, ADMIN$) per the share permissions

  4. No domain groups in Administrators
     → Good: domain compromise doesn't auto-grant local admin
     → But: the machine isn't domain-joined anyway
```

---

## Part 3 — Password Policy

```
┌──────────────────────────────────────────────────────────────────┐
│                    LOCAL PASSWORD POLICY                           │
│                    (from "net accounts")                          │
│                                                                  │
│  Minimum password length:          0 (NONE)                     │
│  Password complexity:              NOT ENFORCED                  │
│  Maximum password age:             42 days                       │
│  Minimum password age:             0 days                        │
│  Password history:                 NONE (no previous tracking)  │
│  Account lockout threshold:        NEVER (unlimited attempts)   │
│  Lockout duration:                 30 minutes                    │
│  Lockout observation window:       30 minutes                    │
│  Force logoff after time limit:    NEVER                        │
│  Computer role:                    WORKSTATION                   │
│                                                                  │
│  ⚠ CRITICAL: No lockout threshold means unlimited brute-force  │
│  ⚠ No complexity requirement means any password is accepted    │
│  ⚠ No history means the same password can be reused forever    │
│  ⚠ Max age of 42 days is set but irrelevant when no pwd exists │
└──────────────────────────────────────────────────────────────────┘
```

---

## Part 4 — Credential Store Inventory

### 4.1 Windows Credential Manager

```
┌──────────────────────────────────────────────────────────────────────────┐
│                 WINDOWS CREDENTIAL MANAGER — FULL DUMP                    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  CREDENTIAL #1: itgroup@adamitrasporti.com                    │      │
│  │                                                                │      │
│  │  Target:     MicrosoftAccount:target=SSO_POP_User:            │      │
│  │              user=itgroup@adamitrasporti.com                  │      │
│  │  Type:       Generic                                          │      │
│  │  User:       itgroup@adamitrasporti.com                      │      │
│  │  Persistence: This logon session only                         │      │
│  │                                                                │      │
│  │  ⚠ CRITICAL: This is a SHARED IT GROUP ACCOUNT               │      │
│  │  ⚠ Stored in credential manager = can be extracted           │      │
│  │  ⚠ "itgroup" implies shared credentials among IT staff       │      │
│  │  ⚠ If this email has admin access to M365/Azure AD,          │      │
│  │     compromising this machine = compromising IT admin access  │      │
│  │                                                                │      │
│  │  ALSO STORED AS:                                              │      │
│  │  LegacyGeneric:target=MicrosoftAccount:user=                 │      │
│  │    itgroup@adamitrasporti.com                                 │      │
│  │  Persistence: Local computer (survives reboot!)               │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  CREDENTIAL #2: formazione20262026@hotmail.com                │      │
│  │                                                                │      │
│  │  Target:     MicrosoftAccount SSO_POP_User                   │      │
│  │  Type:       Generic                                          │      │
│  │  User:       formazione20262026@hotmail.com                  │      │
│  │  Persistence: Session + Local computer                        │      │
│  │                                                                │      │
│  │  ℹ Training account ("formazione" = training in Italian)     │      │
│  │  ℹ The year 2026 in the name suggests annual rotation        │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  CREDENTIAL #3: renan.macena1@outlook.com                     │      │
│  │                                                                │      │
│  │  Target:     LegacyGeneric:MicrosoftAccount                  │      │
│  │  Type:       Generic                                          │      │
│  │  User:       renan.macena1@outlook.com                       │      │
│  │  Persistence: Local computer                                  │      │
│  │                                                                │      │
│  │  ℹ Personal account of current assessor (sandro/macena)      │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  CREDENTIAL #4: GitHub — renanaugustomacena-ux                │      │
│  │                                                                │      │
│  │  Target:     LegacyGeneric:target=git:https://github.com     │      │
│  │  Type:       Generic                                          │      │
│  │  User:       renanaugustomacena-ux                            │      │
│  │  Persistence: Local computer                                  │      │
│  │                                                                │      │
│  │  ℹ GitHub personal access token for code operations          │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  CREDENTIAL #5: Windows Live Token                            │      │
│  │                                                                │      │
│  │  Target:     WindowsLive:target=virtualapp/didlogical        │      │
│  │  Type:       Generic                                          │      │
│  │  User:       02hbqmzzlbvjsdyf                                │      │
│  │  Persistence: Local computer                                  │      │
│  │                                                                │      │
│  │  ℹ Internal Windows Live SSO token — auto-generated          │      │
│  └────────────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Wi-Fi Passwords (Plaintext)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      WI-FI CREDENTIAL STORE                               │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  NETWORK: Adami_Guest                                         │      │
│  │                                                                │      │
│  │  SSID:           Adami_Guest                                  │      │
│  │  Security:       WPA3-Personal (CCMP/GCMP-256)               │      │
│  │  Auto-Connect:   YES                                          │      │
│  │  Broadcast Only: YES                                          │      │
│  │                                                                │      │
│  │  ★ PASSWORD:     1DfGhYu53                                   │      │
│  │                                                                │      │
│  │  ⚠ Anyone with this password can join the guest network      │      │
│  │  ⚠ Guest network has partial access to main LAN (port 7680) │      │
│  │  ⚠ Guest network has partial access to infra (port 7680)    │      │
│  │  ⚠ SMB on this machine is accessible from guest network     │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  NETWORK: montresor                                           │      │
│  │                                                                │      │
│  │  SSID:           montresor                                    │      │
│  │  Security:       WPA3-Personal + WPA2-Personal fallback      │      │
│  │                  (CCMP/GCMP/GCMP-256)                         │      │
│  │  Auto-Connect:   YES                                          │      │
│  │                                                                │      │
│  │  ★ PASSWORD:     Htowermontresor                              │      │
│  │                                                                │      │
│  │  ℹ Unknown network — could be:                               │      │
│  │    - Another Adami location                                   │      │
│  │    - A user's home network                                    │      │
│  │    - A client/partner location                                │      │
│  │  ⚠ WPA2 fallback enabled = downgrade attack possible        │      │
│  └────────────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.3 OpenVPN Certificates & Keys

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    OPENVPN CREDENTIAL INVENTORY                           │
│                                                                          │
│  VPN User:        francescav                                            │
│  VPN Server:      45.151.15.58 (pfSense, UDP 1194)                     │
│  Auth Method:     Certificate (PKCS12) + username/password              │
│  TLS Auth:        Static key (2048-bit)                                 │
│  Internal DNS:    192.168.1.146 (via VPN tunnel)                        │
│  Tunnel Subnet:   10.37.169.0/24 (client gets .2)                      │
│  Server Cert CN:  OpenVpnServerCert2021                                 │
│  Full Tunnel:     YES (redirect-gateway def1 + block-outside-dns)      │
│  Last Connected:  2024-12-18 12:24 → 13:58 (1.5 hours)                │
│  OpenVPN Version: 2.5.0 (Oct 2020 — OUTDATED)                         │
│                                                                          │
│  ═════════════════════════════════════════════════════════════════       │
│  LOCATIONS WHERE VPN CREDENTIALS ARE STORED:                            │
│                                                                          │
│  Location 1: C:\Program Files\OpenVPN\config\                           │
│  (Global — accessible to all users)                                     │
│  ├── pfSense-UDP4-1194-francescav-tls.key  (657 bytes)                 │
│  └── pfSense-UDP4-1194-francescav.p12      (3,357 bytes)               │
│                                                                          │
│  Location 2: C:\Users\CHIARA\OpenVPN\config\                           │
│  (CHIARA's deleted profile)                                             │
│  ├── pfSense-UDP4-1194-francescav.ovpn     (500 bytes) — config        │
│  ├── pfSense-UDP4-1194-francescav-tls.key  (657 bytes)                 │
│  └── pfSense-UDP4-1194-francescav.p12      (3,357 bytes)               │
│                                                                          │
│  Location 3: C:\Users\elena.malini\OpenVPN\config\                     │
│  (Domain user profile)                                                  │
│  └── EMPTY (config + log folders exist but no files)                    │
│  ═════════════════════════════════════════════════════════════════       │
│                                                                          │
│  ─── PKCS12 CERTIFICATE DETAILS ───                                     │
│                                                                          │
│  Subject:        CN=francescav                                          │
│  Issuer:         CN=Internal CA                                         │
│  Serial:         0x1A                                                   │
│  Valid From:     2022-01-13 10:27:53                                    │
│  Valid Until:    2032-01-11 10:27:53 (still valid for 6 years)         │
│  Thumbprint:     D61DE6F4F0F735CC02B95B47D714C8B880DFAE5A              │
│  Has Private Key: YES                                                   │
│  Key Password:   NONE (p12 opened without password!)                   │
│                                                                          │
│  ⚠ CRITICAL: The PKCS12 bundle has NO password protection             │
│  ⚠ Anyone who copies this file can authenticate to the VPN            │
│  ⚠ The VPN still requires username/password (auth-user-pass)          │
│     but the certificate+key are half the authentication               │
│  ⚠ Certificate is valid until 2032 — long-lived credential           │
│  ⚠ Stored in global Program Files = accessible to ANY local user     │
│  ═════════════════════════════════════════════════════════════════       │
│                                                                          │
│  ─── TLS AUTH KEY (FULL CONTENT) ───                                    │
│                                                                          │
│  # 2048 bit OpenVPN static key                                          │
│  -----BEGIN OpenVPN Static key V1-----                                  │
│  5cb2b9b85248a553ade0bad460d01467                                       │
│  7fede77530494e7432ebf13578815d2d                                       │
│  ef11ec8297c27bf7ca57341695ea0575                                       │
│  4dcfca1ef3820860c1a4d022abd455a3                                       │
│  52889408d38012501fddc83b4c42da15                                       │
│  7fe7b2954346c607bae4fb60847a58ec                                       │
│  42579ce5d2b049420f2a1e7ca2554782                                       │
│  9dd8fe9b7ff341aa7dbcfba7046ec45f                                       │
│  a5ad3a2cdbf97c5844e11f9ab770f7fa                                       │
│  31eb3168945933079140eef7cd87b7b9                                       │
│  b5e9d2f09dc12f8140ed56e827cdbfd9                                       │
│  b0250a36dc645aa66f27d8a8e44908fa                                       │
│  b397cb610b7d06ef192f602ab81ea97f                                       │
│  05587ae9e0c07a77a98c8e0f03ebb16c                                       │
│  a40b46ac8e7355e824457d36d50f5720                                       │
│  ee02cf5b74a0dfa5482c1a760c58db42                                       │
│  -----END OpenVPN Static key V1-----                                    │
│                                                                          │
│  ⚠ This key is shared between ALL VPN clients using this config       │
│  ⚠ It provides TLS channel authentication (prevents unauthorized      │
│     connection attempts to the VPN server)                              │
│  ⚠ If compromised, an attacker can attempt VPN connections            │
│                                                                          │
│  ─── VPN CONFIG (FULL CONTENT) ───                                      │
│                                                                          │
│  dev tun                                                                │
│  persist-tun                                                            │
│  persist-key                                                            │
│  cipher AES-128-CBC                                                     │
│  data-ciphers AES-128-GCM                                              │
│  auth SHA256                                                            │
│  tls-client                                                             │
│  client                                                                 │
│  resolv-retry infinite                                                  │
│  remote 45.151.15.58 1194 udp4                                         │
│  auth-user-pass                                                         │
│  pkcs12 pfSense-UDP4-1194-francescav.p12                               │
│  tls-auth pfSense-UDP4-1194-francescav-tls.key 1                       │
│  remote-cert-tls server                                                 │
│  redirect-gateway def1                                                  │
│  dhcp-option DNS 192.168.1.146                                          │
│  --block-outside-dns                                                    │
│                                                                          │
│  ⚠ cipher AES-128-CBC is deprecated — should use AES-256-GCM         │
│  ⚠ OpenVPN warned about missing AES-128-CBC in data-ciphers list      │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.4 AnyDesk Credentials

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    ANYDESK CREDENTIAL INVENTORY                           │
│                                                                          │
│  AnyDesk ID:      325232966                                             │
│  Alias:           desktop-q8qvcf4@ad                                    │
│  License:         free-1 (FREE — no enterprise features)                │
│  Install ID:      a0967e95cfb1c4d61fb20b0738393bb8                      │
│  Fingerprint:     ca3f08c330e8a7e6df1d3e843ff08e0428ff6273              │
│  WOL MAC Hash:    9bd6f363288d462ead0937136c387d49ef9c1371              │
│                                                                          │
│  ─── UNATTENDED ACCESS CREDENTIALS ───                                  │
│                                                                          │
│  Password Hash:   68d71c8c2a6fe4cb41cddcab961fba36608bf81449f51b22d     │
│                   416339399f601f8                                        │
│  Salt:            ced3b533b45d3d69ef3467d4e01e06c1                      │
│                                                                          │
│  ⚠ These are SHA-256 based hashes                                      │
│  ⚠ If the unattended password is weak, it can be cracked offline      │
│  ⚠ Anyone who cracks this hash can connect without user approval       │
│                                                                          │
│  ─── ANYDESK TLS CERTIFICATE (FULL) ───                                 │
│                                                                          │
│  -----BEGIN CERTIFICATE-----                                            │
│  MIICqDCCAZACAQEwDQYJKoZIhvcNAQELBQAwGTEXMBUGA1UEAwwOQW55RGVzayBD     │
│  bGllbnQwIBcNMjIwMjAxMDg1NjIxWhgPMjA3MjAxMjAwODU2MjFaMBkxFzAVBgNV     │
│  BAMMDkFueURlc2sgQ2xpZW50MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKC     │
│  AQEA4euLrm2NEyzuMUvYmGzMk9QtCsd/7DK9nNVx7u00GczD0bpOG8IXLBvV0a8y     │
│  ZYsQ9dIwsDdEwBM1rBanmvz81wVv90q1Hn8PkdfWomoG+Eg4mxLSN2gXdBJcctWs     │
│  k91EaFGOhPvQvq/ypDzRdsiSW/Mv/g7Je8ZRMuq4GJ4HL2XJ2+rmRS0rHsaYr3uk     │
│  xWLzi7r0QYcuDgf3mfeRZDa1SV0TATyCAFhzPFnIYhq2nWUVAVTRgL3ONRaqEfji     │
│  Eb/W5eBZw3F1LrXqBVvh7HNV+n737o7ZNedbCoVHL3QlDofYyqPvoWLfI4BfpMnK     │
│  2CHKZdlVxuvyEtNjw050ogsrJwIDAQABMA0GCSqGSIb3DQEBCwUAA4IBAQBqZAd4     │
│  VK589fQ51jul0xLlbrG/B4omzy3wkWEesv6R2iq4ZmPgBxxHXMTZ5taH//cfg3st     │
│  ABgO6sKSe2Z0SgMtKD9rKdMGUTB7ueUOuiVRHCtrY+mWK/xnMLEL5U/b9oN2yqo5     │
│  ztuyzM0ZoNswg0/GzfOi7UaXVeO9hyXr9MCbmkWZ3hVRz+zoNrEhqaXXe3FPb04S     │
│  iFqhzKfRDyAUrhwI+nhKejcREEYVnmYcDTRBSweR3uqFDvm1KN7UjfXBDEoVAsS7     │
│  NL9Fr8azzGp8JbYWVZ8oS1NmO61x1MVKu3UnwOiB3Anj/fDLvphvug9L+9g+/x0X     │
│  cxPYh3Y2QJmAb+dd                                                      │
│  -----END CERTIFICATE-----                                             │
│                                                                          │
│  ─── ANYDESK PRIVATE KEY (FULL) ───                                     │
│                                                                          │
│  -----BEGIN PRIVATE KEY-----                                            │
│  MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDh64uubY0TLO4x     │
│  S9iYbMyT1C0Kx3/sMr2c1XHu7TQZzMPRuk4bwhcsG9XRrzJlixD10jCwN0TAEzWs     │
│  Fqea/PzXBW/3SrUefw+R19aiagb4SDibEtI3aBd0Elxy1ayT3URoUY6E+9C+r/Kk     │
│  PNF2yJJb8y/+Dsl7xlEy6rgYngcvZcnb6uZFLSsexpive6TFYvOLuvRBhy4OB/eZ     │
│  95FkNrVJXRMBPIIAWHM8WchiGradZRUBVNGAvc41FqoR+OIRv9bl4FnDcXUuteoF     │
│  W+Hsc1X6fvfujtk151sKhUcvdCUOh9jKo++hYt8jgF+kycrYIcpl2VXG6/IS02PD     │
│  TnSiCysnAgMBAAECggEBANT9VlD6I1iCsYV0Nh1t5WkxTc2ty+KI685iROm2Y7o3     │
│  HB4sANuWnnYNQAZRn7ev5it7ID/hu0VCVwWIzjcGb/DfxXFk02CO9cTPsiCoyS1m     │
│  GUfJ9LobvpDFhrcUz4EPyCB5U134chJ0mtNQK0JLUgCyQvrIQhgZHhBczXcX9Tou     │
│  fNBFytLfWc3m37Yr+O5VlPzD32ijKW2c3Vu7bbLBWWZw3L/H5kgs2a/ldrSAsF07     │
│  WvBTx168q9fIGXOwsSdmu9tViLGoqERtvtXLer3yOdXYVSTuoUfddOlIT7Rjq1iv     │
│  X2gNAwpkIN10k16xpU3/LHg8H1fZhQeGiaGuFAYGhtECgYEA+k21SjGTC6Si2lfD     │
│  jGJf8ip7j1+i1CTfv7EYOG594J/mI/ru3odXDuRyU8oPzopWcRHCZm9kr3tJGxjM     │
│  l3MI34lQW0iXMVLN4RIPubctUQQ2Rc8xR1BKd6ZQwE/cgeXaVvIW9gtM70AwVr+P     │
│  HgZXdMOLdnLWMzPvPNBpSTFaBysCgYEA5w/G+EeRJ2s4hzDICMPfWcW2LKe9+bMJ     │
│  IY7cAqUpuCX+2t5omEbuxbvFMAWaZzV00HP/ic8lUVKCiMA8FzWIUtzXtO5Hv7Lh     │
│  CSjR3DalJJeKtAovi31Be6wlHAwNioeKYTDG74da/jFEg0rixSaPnP4xTTwRDTu8     │
│  oNQFMMr/bfUCgYEAsb+1WjbSQZZsv7lLeMnzcLmSfUJhE14MNsjAdnKgmX9zo2Fz     │
│  eDuMK1s3hSEdEINU137RGoVIbwWR6Ng3keVzC6srkWd/VtuCsK5u1GesmrfvAqwc     │
│  RpRSDZ3iAm+0G9rqrovEmn1z6QMgULpAHAZM3PJwe3EZg8sBvaIS4pNVZ3kCgYAR     │
│  qPoLJeUpPx+t7YOMb/QVN3BKD3QMrqtm/jVAmoEKyxSkg9U4tksvn79dgUAg3UwV     │
│  VphUXxm6EnVZoF+3YmcN9kUiVgfz1ecvPQh1LVQH7PEz+4dQwP0NR8X6U82BJgTk     │
│  ksbRreW9geR7qHCWovDdDeyUu5+OBF/RZwMSjKFjNQKBgQC/1QYwcXaCxuOatwRg     │
│  H5hJuzSC4bZa0myl+wuD+PACC3CSqnY6OPzWQAUEnYW3EAWJGPcXAmMXPF71edCn     │
│  v3ZSrs+JbFtkYZaxG5D3HxCI2l8UEHcRuY3+bInnjwFHxSs1G6C/3kjUp306Xu6+     │
│  tveDSWaLb2uYhQGYPBj6Qx5tGg==                                         │
│  -----END PRIVATE KEY-----                                             │
│                                                                          │
│  ⚠ CRITICAL: This private key allows IMPERSONATING this AnyDesk       │
│  ⚠ Combined with the ID (325232966) and the password hash,            │
│     an attacker with these credentials has full remote desktop access   │
│  ⚠ The key is stored unencrypted in C:\ProgramData\AnyDesk\           │
│     which is readable by all local users                                │
│                                                                          │
│  SECURITY SETTINGS:                                                     │
│  ├── Clipboard sharing:  ENABLED (files too)                           │
│  ├── Ctrl+Alt+Del send:  ALLOWED                                       │
│  └── Unattended access:  ENABLED with password                         │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.5 Browser Credential Databases

These databases contain saved website passwords. They are encrypted with DPAPI (Windows Data Protection API), which is tied to the user's login credentials. Since `sandro` has NO password, the DPAPI master key can be derived trivially.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    BROWSER CREDENTIAL DATABASES                           │
│                                                                          │
│  USER: sandro (current user, admin, NO PASSWORD)                        │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  Chrome:  C:\Users\sandro\AppData\Local\Google\Chrome\        │      │
│  │           User Data\Default\Login Data                        │      │
│  │  Size:    40,960 bytes                                        │      │
│  │  Modified: 2026-05-18 15:09:38                                │      │
│  │  Format:  SQLite3 database, AES-256-GCM encrypted             │      │
│  │  DPAPI:   Trivially decryptable (no user password → weak key)│      │
│  ├────────────────────────────────────────────────────────────────┤      │
│  │  Edge:    C:\Users\sandro\AppData\Local\Microsoft\Edge\       │      │
│  │           User Data\Default\Login Data                        │      │
│  │  Size:    53,248 bytes                                        │      │
│  │  Modified: 2026-05-21 16:43:17                                │      │
│  │  Format:  SQLite3 database, AES-256-GCM encrypted             │      │
│  │  DPAPI:   Trivially decryptable (no user password → weak key)│      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  USER: CHIARA (deleted account — profile still on disk)                 │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  Chrome:  C:\Users\CHIARA\...\Login Data                     │      │
│  │  Size:    135,168 bytes  ← LARGE — many saved passwords      │      │
│  │  Modified: 2025-11-03 09:32:19                                │      │
│  │  DPAPI:   Keys orphaned (account deleted)                     │      │
│  │           May still be decryptable with old DPAPI master key  │      │
│  ├────────────────────────────────────────────────────────────────┤      │
│  │  Edge:    C:\Users\CHIARA\...\Login Data                     │      │
│  │  Size:    61,440 bytes                                        │      │
│  │  Modified: 2025-03-12 10:18:08                                │      │
│  ├────────────────────────────────────────────────────────────────┤      │
│  │  Firefox: C:\Users\CHIARA\...\Profiles\52h38nkv.default-     │      │
│  │           release\key4.db + logins.json                       │      │
│  │  key4.db: Contains NSS encryption keys                       │      │
│  │  Modified: ~2023                                              │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  USER: elena.malini (domain account)                                    │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  Chrome:  C:\Users\elena.malini\...\Login Data               │      │
│  │  Size:    40,960 bytes                                        │      │
│  │  Modified: 2025-03-05 13:23:25                                │      │
│  ├────────────────────────────────────────────────────────────────┤      │
│  │  Edge:    C:\Users\elena.malini\...\Login Data               │      │
│  │  Size:    51,200 bytes                                        │      │
│  │  Modified: 2025-03-01 09:24:03                                │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  TOTAL BROWSER CREDENTIAL DATABASES: 7                                  │
│  TOTAL SIZE: ~383 KB of saved passwords across 3 users                  │
│                                                                          │
│  ⚠ CHIARA's Chrome has 135KB — likely 100+ saved passwords            │
│  ⚠ sandro's DPAPI is weak due to empty password                       │
│  ⚠ CHIARA's profile should have been wiped when account was deleted   │
│  ⚠ elena.malini's credentials are from the domain                     │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.6 GoSign Digital Signature Data

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    GOSIGN DIGITAL SIGNATURE                               │
│                    (Italian qualified electronic signature)               │
│                                                                          │
│  Location:      C:\Users\CHIARA\.gosign\                                │
│  GAID:          e5215ca1-5975-4c15-a32a-881be4f852b3                    │
│  License:       No license found                                        │
│  Last Run:      2025-11-03 09:40:43                                     │
│  Smart Card:    NOT DETECTED (PCSC service not active)                  │
│  TSL Loaded:    IT (Italian Trust Service List)                         │
│  Proxy:         NOPROXY                                                 │
│                                                                          │
│  Installers on disk (consuming ~960MB):                                 │
│  ├── GoSignDesktop-standard-1.3.10-fddaa93.msi  (139 MB)              │
│  ├── GoSignDesktop-standard-1.3.11-9572ad2.msi  (139 MB)              │
│  ├── GoSignDesktop-standard-1.3.12-a3ec21f.msi  (139 MB)              │
│  ├── GoSignDesktop-standard-1.3.13-39689e1.msi  (140 MB)              │
│  ├── GoSignDesktop-standard-1.3.14-250b508.msi  (140 MB)              │
│  ├── GoSignDesktop-standard-2.0.2-1eac8acc.exe  (134 MB)              │
│  ├── GoSignDesktop-standard-2.0.3-e2767a9.exe   (137 MB)              │
│  └── GoSignDesktop-standard-2.0.5-e422767.exe   (137 MB)              │
│                                                                          │
│  ⚠ GoSign is for legally-binding digital signatures (Italian PEC/CNS) │
│  ⚠ The CA chain file contains Italian trust anchors                    │
│  ⚠ If CHIARA had a smart card configured, those keys would be          │
│     accessible to whoever gets CHIARA's DPAPI master key               │
│  ℹ Currently no smart card reader active — certificates were likely    │
│     on a physical USB token that was removed                            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Part 5 — Corporate Data Exposure

### 5.1 OneDrive — ADAMI TRASPORTI SPA

The deleted CHIARA profile has a synced corporate OneDrive:

```
C:\Users\CHIARA\OneDrive - ADAMI TRASPORTI SPA\
├── Allegati/                    (Attachments)
├── App/
├── Desktop/
├── Documenti/                   (Documents)
├── Documenti Societari/         (Corporate Documents) ← SENSITIVE
├── File di chat di Microsoft Teams/
├── Immagini/                    (Images)
├── Microsoft Teams Chat Files/
├── Scansioni/                   (Scans — likely scanned documents)
└── Video/
```

### 5.2 Dropbox — GRUPPO ADAMI QUALITA'

```
C:\Users\CHIARA\Dropbox\
└── GRUPPO ADAMI QUALITA'/       (Adami Group Quality — ISO/QMS docs?)

C:\Users\CHIARA\Dropbox (Precedente)\
└── (Previous Dropbox — moved/migrated)
```

### 5.3 Corporate Structure Revealed

From the data collected, we can map the corporate structure:

```
ADAMI TRASPORTI SPA
├── IT Department
│   ├── itgroup@adamitrasporti.com (shared IT account)
│   ├── Massimo (massimo-it@ad, AnyDesk ID 988685941) — IT technician
│   └── AnyDesk ID 905591417 — primary IT support (unknown name)
│
├── Domain: adamitrasporti.local
│   ├── DC/DNS: 192.168.60.2
│   ├── DC/DNS: 192.168.60.3
│   └── Domain SID: S-1-5-21-3521058280-4105139221-2070416120
│
├── VPN Infrastructure
│   ├── pfSense at 45.151.15.58
│   ├── Internal CA: "Internal CA"
│   ├── VPN DNS: 192.168.1.146
│   └── Tunnel: 10.37.169.0/24
│
├── Known Employees/Users on this machine
│   ├── Francesca (original user → PCFRANCESCA hostname)
│   ├── CHIARA (local account, RID 1001, deleted)
│   │   └── VPN username: francescav (Francesca V.)
│   ├── elena.malini (domain account, RID 1247)
│   └── sandro (current user, RID 1003)
│
├── ISP: Welcome Italia
│   ├── DNS: 80.93.143.42 (dnsunico.welcomeitalia.it)
│   └── DNS: 80.93.143.44
│
├── Quality Group
│   └── "GRUPPO ADAMI QUALITA'" (Dropbox)
│
└── Known Machines
    ├── PCFRANCESCA (this machine, .192.61)
    ├── laptop-014t20a2 (AnyDesk ID 227837777)
    └── 14+ hosts on 192.168.1.0/24
```

---

## Part 6 — Orphaned Scheduled Tasks

These tasks still reference the deleted CHIARA account (SID -1001) or elena.malini's domain SID:

```
┌──────────────────────────────────────────────────────────────────────────┐
│              SCHEDULED TASKS RUNNING AS ORPHANED/NON-LOCAL SIDS           │
│                                                                          │
│  ── CHIARA (SID S-1-5-21-...-1001, account DELETED) ──                 │
│                                                                          │
│  OneDrive Reporting Task                         State: Ready           │
│  OneDrive Startup Task                           State: Ready           │
│  TrackerAutoUpdate                               State: Ready           │
│  Agent Activation Runtime (S-1-5-...-1001)       State: Disabled        │
│  DropboxUpdaterTaskUser123.0.6299.129            State: Ready           │
│  Firefox Background Update 539525D28429A5F6      State: Ready           │
│  Firefox Background Update (SID variant)         State: Ready           │
│  Firefox Default Browser Agent 539525D28429A5F6  State: Ready           │
│                                                                          │
│  ⚠ These tasks attempt to run as a deleted account                     │
│  ⚠ Behavior is unpredictable — they may fail silently                 │
│  ⚠ Some may run as SYSTEM if the scheduler falls back                 │
│  ⚠ Dropbox updater may attempt network connections as orphan          │
│                                                                          │
│  ── elena.malini (Domain SID S-1-5-21-3521058280-...-1247) ──         │
│                                                                          │
│  OneDrive Reporting Task                         State: Ready           │
│  OneDrive Startup Task                           State: Ready           │
│                                                                          │
│  ⚠ These run as a domain account that cannot authenticate             │
│     from the guest Wi-Fi network                                        │
│  ⚠ May generate failed auth events or silent failures                 │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Part 7 — SMB Share Permissions

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    SMB SHARE PERMISSIONS                                   │
│                                                                          │
│  SHARE: C$ (C:\)                                                        │
│  ├── BUILTIN\Administrators    → Full Control                           │
│  ├── BUILTIN\Backup Operators  → Full Control                           │
│  └── NT AUTHORITY\INTERACTIVE  → Full Control                           │
│  Encryption: NO | Current Users: 0                                      │
│                                                                          │
│  SHARE: ADMIN$ (C:\WINDOWS)                                            │
│  ├── BUILTIN\Administrators    → Full Control                           │
│  ├── BUILTIN\Backup Operators  → Full Control                           │
│  └── NT AUTHORITY\INTERACTIVE  → Full Control                           │
│  Encryption: NO | Current Users: 0                                      │
│                                                                          │
│  SHARE: IPC$ (Remote IPC)                                               │
│  └── Standard system share for named pipes                              │
│  Encryption: NO | Current Users: 0                                      │
│                                                                          │
│  SHARE: Users (C:\Users)    ⚠ CUSTOM SHARE — CRITICAL                  │
│  ├── BUILTIN\Administrators    → Full Control                           │
│  └── Everyone                  → Full Control   ← CRITICAL             │
│  Encryption: NO | Current Users: 0                                      │
│                                                                          │
│  NTFS PERMISSIONS ON C:\Users:                                          │
│  ├── Everyone                → ReadAndExecute + special flags           │
│  ├── NT AUTHORITY\SYSTEM     → Full Control                             │
│  ├── BUILTIN\Administrators  → Full Control                             │
│  └── BUILTIN\Users           → ReadAndExecute + special flags           │
│                                                                          │
│  EFFECTIVE ACCESS (SMB share + NTFS combined):                          │
│  ├── Admin (sandro, no pwd): Full Control via C$ and Users shares      │
│  ├── Everyone (no auth):     ReadAndExecute on C:\Users contents        │
│  │   (SMB grants Full but NTFS limits to ReadAndExecute)                │
│  ├── ASPNET (no pwd):        ReadAndExecute on C:\Users                 │
│  └── INTERACTIVE (console):  Full Control via admin shares              │
│                                                                          │
│  ⚠ Even with NTFS limiting to ReadAndExecute, an unauthenticated      │
│     user can READ all user profiles, documents, browser data,           │
│     VPN configs, and corporate files via the Users share                │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Part 8 — Security Audit Log Status

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    SECURITY AUDIT LOG ANALYSIS                            │
│                                                                          │
│  The Windows Security event log was queried for:                        │
│  - Event 4624 (Successful logon)                                        │
│  - Event 4625 (Failed logon)                                            │
│  - Event 4634 (Logoff)                                                  │
│  - Event 4672 (Special privileges assigned)                             │
│                                                                          │
│  RESULT: Only SYSTEM logon events found                                 │
│                                                                          │
│  All 20 most recent events are:                                         │
│    Account: PCFRANCESCA$ (machine account)                              │
│    SID: S-1-5-18 (SYSTEM)                                               │
│    Logon Type: System                                                   │
│                                                                          │
│  MISSING:                                                               │
│  ✗ No interactive logon events (Type 2)                                │
│  ✗ No remote interactive events (Type 10 — RDP/AnyDesk)               │
│  ✗ No network logon events (Type 3 — SMB)                             │
│  ✗ No failed logon attempts                                            │
│  ✗ No logoff events                                                    │
│                                                                          │
│  CONCLUSION:                                                            │
│  User logon auditing is NOT configured. IT has NO forensic              │
│  trail of who logs into this machine, when, or from where.             │
│  If this machine is compromised, there will be no evidence              │
│  in the security log of the attacker's authentication.                  │
│                                                                          │
│  TO ENABLE (for IT):                                                    │
│  auditpol /set /subcategory:"Logon" /success:enable /failure:enable    │
│  auditpol /set /subcategory:"Logoff" /success:enable                   │
│  auditpol /set /subcategory:"Special Logon" /success:enable            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Part 9 — Credential Risk Heat Map

```
┌──────────────────────────────────────────────────────────────────────────┐
│                 CREDENTIAL RISK HEAT MAP                                  │
│                                                                          │
│  ██████████  CRITICAL — Immediate compromise possible                   │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │ • sandro: admin, NO password, SMB accessible                  │      │
│  │ • ASPNET: active, NO password, SMB accessible                 │      │
│  │ • AnyDesk: private key + password hash on disk                │      │
│  │ • VPN: certificate + private key, no p12 password             │      │
│  │ • Wi-Fi Adami_Guest: plaintext PSK → network access          │      │
│  │ • Users share: Everyone Full Control                          │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ████████░░  HIGH — Extractable with local access                       │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │ • CHIARA browser passwords (Chrome 135KB, Edge 61KB, Firefox) │      │
│  │ • sandro browser passwords (Chrome 40KB, Edge 53KB)           │      │
│  │ • elena.malini browser passwords (Chrome, Edge)               │      │
│  │ • itgroup@adamitrasporti.com in credential manager            │      │
│  │ • elena.malini domain cached creds (DCC2 in registry)         │      │
│  │ • Wi-Fi montresor: plaintext PSK                              │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ██████░░░░  MEDIUM — Requires specific tools/knowledge                 │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │ • GoSign GAID and session data                                │      │
│  │ • formazione20262026@hotmail.com token                        │      │
│  │ • GitHub PAT (renanaugustomacena-ux)                          │      │
│  │ • DPAPI master keys (weak due to empty password)              │      │
│  │ • AnyDesk connection history (IT personnel IDs)               │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ████░░░░░░  LOW — Limited value                                        │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │ • Windows Live SSO token (02hbqmzzlbvjsdyf)                  │      │
│  │ • Administrator account (disabled, 6yr old password)          │      │
│  │ • WDAGUtilityAccount (disabled, expired password)             │      │
│  └────────────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Part 10 — Recommendations for IT

> These are observations and suggestions. IT has the final decision on all actions.

### Immediate Actions (Priority 1)

| # | Action | Why | Effort |
|---|--------|-----|--------|
| 1 | Set strong password on `sandro` account | Admin with no password = instant full compromise | 1 min |
| 2 | Disable ASPNET account | Active, no password, never used, no reason to exist | 1 min |
| 3 | Revoke VPN certificate `francescav` (serial 0x1A) on pfSense | Certificate is on disk unprotected; user may no longer need VPN | 5 min |
| 4 | Change AnyDesk unattended password + rotate certificate | Password hash and private key are extractable | 5 min |
| 5 | Remove or fix "Users" SMB share | Everyone=Full exposes all user data | 1 min |
| 6 | Disable SMBv1 | EternalBlue vector, no legitimate use in 2026 | 1 min |

### Short-Term Actions (Priority 2)

| # | Action | Why |
|---|--------|-----|
| 7 | Delete CHIARA and elena.malini user profiles | Contains accumulated credentials, corporate data, VPN certs |
| 8 | Clean orphaned scheduled tasks (SID -1001, domain SID) | Running as deleted/unreachable accounts |
| 9 | Change Wi-Fi PSK for Adami_Guest | Plaintext on this machine (and likely others) |
| 10 | Enable SMB signing and encryption | Prevents relay attacks and traffic sniffing |
| 11 | Disable LLMNR, NetBIOS, mDNS | Broadcast poisoning vectors |
| 12 | Enable logon auditing | Currently no forensic trail |
| 13 | Remove expired/distrusted root CAs | WoSign, StartCom, expired QuoVadis/DST/SECOM/AddTrust |

### Architecture Actions (Priority 3)

| # | Action | Why |
|---|--------|-----|
| 14 | Fix VLAN segmentation — block DO (7680) cross-VLAN | Guest can reach main LAN and infrastructure |
| 15 | Upgrade OpenVPN from 2.5.0 to 2.6.x | 5-year-old version with known vulnerabilities |
| 16 | Replace free AnyDesk with enterprise or managed remote access | No central logging, no access control |
| 17 | Configure machine for corporate network (domain join or VPN auto-connect) | Currently on guest Wi-Fi with ISP DNS |
| 18 | Implement a credential rotation policy for shared accounts | itgroup@ is cached on user machines |
| 19 | Evaluate BitLocker deployment | No disk encryption = physical theft = full data access |
| 20 | Standardize machine handoff procedure | Profile cleanup, credential revocation, task cleanup |
