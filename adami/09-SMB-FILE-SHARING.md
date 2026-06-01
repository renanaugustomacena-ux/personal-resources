# 09 — SMB & File Sharing

## SMB Server Configuration

### Protocol Versions

```
┌─────────────────────────────────────────────────────────┐
│                SMB PROTOCOL STATUS                        │
│                                                          │
│  SMBv1:  ████████████████  ENABLED  ← CRITICAL RISK    │
│  SMBv2:  ████████████████  ENABLED                      │
│  SMBv3:  ████████████████  ENABLED                      │
│  QUIC:   ████████████████  ENABLED                      │
│                                                          │
│  ⚠ SMBv1 is the protocol exploited by:                  │
│    - EternalBlue (MS17-010) → WannaCry, NotPetya       │
│    - EternalRomance                                     │
│    - Multiple other NSA-leaked exploits                  │
└─────────────────────────────────────────────────────────┘
```

### Security Settings

| Setting | Value | Recommended | Status |
|---------|-------|-------------|--------|
| EnableSMB1Protocol | **True** | False | **CRITICAL** |
| EnableSMB2Protocol | True | True | OK |
| EnableSMBQUIC | True | True | OK |
| EncryptData | **False** | True | **HIGH RISK** |
| EnableSecuritySignature | **False** | True | **HIGH RISK** |
| RequireSecuritySignature | **False** | True | **CRITICAL** |
| RejectUnencryptedAccess | True | True | OK |
| AuditSmb1Access | **False** | True | **MISSING VISIBILITY** |
| AuditClientDoesNotSupportEncryption | **False** | True | MISSING |
| AuditClientDoesNotSupportSigning | **False** | True | MISSING |
| AuditInsecureGuestLogon | **False** | True | MISSING |
| AutoShareWorkstation | True | False | MEDIUM (admin shares) |
| AutoShareServer | True | False | MEDIUM |
| EnableMailslots | False | False | OK |
| ServerHidden | True | True | OK (not announcing) |
| EnableMultiChannel | True | True | OK |

### Encryption Configuration

| Setting | Value |
|---------|-------|
| EncryptData (global) | False |
| EncryptionCiphers | AES_128_GCM, AES_128_CCM, AES_256_GCM, AES_256_CCM |
| DisableSmbEncryptionOnSecureConnection | True |

The server supports AES encryption but does **not require it**. Any client can connect without encryption.

## Network Shares

```
┌──────────────────────────────────────────────────────────────┐
│                       SMB SHARES                              │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   C$       │  │  ADMIN$    │  │   IPC$     │            │
│  │            │  │            │  │            │            │
│  │ C:\        │  │ C:\WINDOWS │  │ Remote IPC │            │
│  │            │  │            │  │            │            │
│  │ Default    │  │ Default    │  │ Default    │            │
│  │ admin share│  │ admin share│  │ admin share│            │
│  │            │  │            │  │            │            │
│  │ Encrypted: │  │ Encrypted: │  │ Encrypted: │            │
│  │ NO         │  │ NO         │  │ NO         │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│                                                              │
│  ┌────────────────────────────────────────┐                 │
│  │   Users                                │  ← CUSTOM SHARE│
│  │                                        │                 │
│  │   Path: C:\Users                       │                 │
│  │   Encrypted: NO                        │                 │
│  │   Folder Enumeration: AccessBased      │                 │
│  │                                        │                 │
│  │   ⚠ EVERYONE has FULL ACCESS          │                 │
│  └────────────────────────────────────────┘                 │
└──────────────────────────────────────────────────────────────┘
```

## Share Permissions Detail

### Administrative Shares (C$, ADMIN$)

| Account | Access Type | Rights |
|---------|------------|--------|
| BUILTIN\Administrators | Allow | Full |
| BUILTIN\Backup Operators | Allow | Full |
| NT AUTHORITY\INTERACTIVE | Allow | Full |

### Users Share — **CRITICAL**

| Account | Access Type | Rights |
|---------|------------|--------|
| BUILTIN\Administrators | Allow | Full |
| **Everyone** | **Allow** | **Full** |

```
⚠⚠⚠ CRITICAL FINDING ⚠⚠⚠

The "Users" share (C:\Users) grants FULL access to EVERYONE.
This means ANY authenticated user on the network can:
  - Read all user profiles
  - Read Documents, Desktop, Downloads
  - Read saved browser data
  - Read application data
  - Write/modify/delete any user file
  - Plant malicious files (DLL hijacking, shortcuts, etc.)

This share contains:
  C:\Users\sandro\          (active admin user)
  C:\Users\Administrator\   (admin profile)
  C:\Users\Public\          (public profile)
```

## SMB Attack Surface Analysis

```
┌─────────────────────────────────────────────────────────┐
│                SMB ATTACK VECTORS                        │
│                                                         │
│  1. EternalBlue (MS17-010)                              │
│     ├── SMBv1 ENABLED                                   │
│     ├── If unpatched: Remote Code Execution             │
│     └── Even if patched: SMBv1 should be disabled       │
│                                                         │
│  2. SMB Relay Attack                                    │
│     ├── Signing NOT required                            │
│     ├── Capture NTLM auth → relay to another host      │
│     └── Can escalate to domain admin (if joined)        │
│                                                         │
│  3. Password Spraying via SMB                           │
│     ├── SMB accepts authentication attempts             │
│     ├── No account lockout visible                      │
│     └── Admin account has no password!                  │
│                                                         │
│  4. Data Exfiltration                                   │
│     ├── "Users" share = Everyone Full Control           │
│     ├── No encryption on any share                      │
│     └── Traffic can be sniffed on Wi-Fi                 │
│                                                         │
│  5. Lateral Movement                                    │
│     ├── Admin shares (C$, ADMIN$) accessible           │
│     ├── PsExec / WMI / WinRM potential                  │
│     └── NT AUTHORITY\INTERACTIVE = local console users  │
└─────────────────────────────────────────────────────────┘
```

## Remediation Priority

| Priority | Action | Command |
|----------|--------|---------|
| 1 (ASAP) | Disable SMBv1 | `Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force` |
| 2 (ASAP) | Remove "Users" share or fix permissions | `Remove-SmbShare -Name "Users" -Force` |
| 3 (HIGH) | Enable SMB signing | `Set-SmbServerConfiguration -RequireSecuritySignature $true -Force` |
| 4 (HIGH) | Enable SMB encryption | `Set-SmbServerConfiguration -EncryptData $true -Force` |
| 5 (MED) | Enable SMB auditing | `Set-SmbServerConfiguration -AuditSmb1Access $true -Force` |
| 6 (MED) | Disable admin shares | `Set-SmbServerConfiguration -AutoShareWorkstation $false -Force` |
