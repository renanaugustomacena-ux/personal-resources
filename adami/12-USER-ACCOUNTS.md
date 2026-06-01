# 12 — User Accounts & Privilege Analysis

## Local User Accounts

```
┌──────────────────────────────────────────────────────────────┐
│                    LOCAL USER ACCOUNTS                         │
│                                                              │
│  ┌───────────────────────────────────────────────┐          │
│  │  sandro ★ (ACTIVE - ADMIN)                    │          │
│  │                                                │          │
│  │  Enabled:          YES                        │          │
│  │  Password Required: NO  ← ⚠ CRITICAL         │          │
│  │  Password Last Set: 2025-11-03                │          │
│  │  Last Logon:       2026-05-19 08:38           │          │
│  │  SID: S-1-5-21-872622826-2128076652-          │          │
│  │       1825121607-1003                          │          │
│  │  Groups: Administrators                       │          │
│  │                                                │          │
│  │  ⚠ Local admin with NO PASSWORD               │          │
│  │  ⚠ Any network access attempt = auto-auth     │          │
│  └───────────────────────────────────────────────┘          │
│                                                              │
│  ┌───────────────────────────────────────────────┐          │
│  │  Administrator (DISABLED)                      │          │
│  │                                                │          │
│  │  Enabled:          NO                         │          │
│  │  Password Required: NO  ← ⚠                  │          │
│  │  Password Last Set: 2020-05-05                │          │
│  │  Last Logon:       2021-03-20                 │          │
│  │  Groups: Administrators                       │          │
│  │                                                │          │
│  │  Password is 6 years old, no complexity req.  │          │
│  └───────────────────────────────────────────────┘          │
│                                                              │
│  ┌───────────────────────────────────────────────┐          │
│  │  ASPNET (ENABLED - NO PASSWORD)               │          │
│  │                                                │          │
│  │  Enabled:          YES  ← ⚠ WHY?             │          │
│  │  Password Required: NO  ← ⚠ CRITICAL         │          │
│  │  Password Last Set: 2022-02-09                │          │
│  │  Last Logon:       Never                      │          │
│  │  Groups: (default)                            │          │
│  │                                                │          │
│  │  Created for IIS/ASP.NET, never used,         │          │
│  │  still enabled with no password.              │          │
│  └───────────────────────────────────────────────┘          │
│                                                              │
│  ┌───────────────────────────────────────────────┐          │
│  │  Guest (DISABLED)                              │          │
│  │                                                │          │
│  │  Enabled:          NO                         │          │
│  │  Last Logon:       2023-05-12  ← ⚠ UNUSUAL   │          │
│  │  Password Required: NO                        │          │
│  │                                                │          │
│  │  Someone logged in as Guest in May 2023.      │          │
│  │  Guest should NEVER have login history.        │          │
│  └───────────────────────────────────────────────┘          │
│                                                              │
│  ┌───────────────────────────────────────────────┐          │
│  │  DefaultAccount (DISABLED)                     │          │
│  │  WDAGUtilityAccount (DISABLED)                │          │
│  │                                                │          │
│  │  Standard Windows system accounts.            │          │
│  │  WDAG has password required = YES (correct)   │          │
│  └───────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

## Administrators Group

| Account | Object Class | Source |
|---------|-------------|--------|
| PCFRANCESCA\Administrator | User | Local |
| PCFRANCESCA\sandro | User | Local |

Only local accounts — no domain groups in the admin group (machine is not domain-joined).

## Account Risk Matrix

| Account | Enabled | Password | Admin | Last Logon | Risk Level |
|---------|---------|----------|-------|------------|------------|
| sandro | YES | **NONE** | **YES** | Today | **CRITICAL** |
| ASPNET | **YES** | **NONE** | No | Never | **HIGH** |
| Administrator | No | None required | Yes | 2021 | MEDIUM (disabled) |
| Guest | No | None | No | 2023 | **MEDIUM** (was used) |
| DefaultAccount | No | None | No | Never | LOW |
| WDAGUtilityAccount | No | Required | No | Never | LOW |

## Password Policy Concerns

```
┌──────────────────────────────────────────────────────┐
│              PASSWORD POLICY STATUS                    │
│                                                      │
│  ┌──────────────────────────────────────────┐       │
│  │  No domain policy (WORKGROUP machine)    │       │
│  │  No local security policy configured     │       │
│  │                                          │       │
│  │  Effective policy:                       │       │
│  │  ├── Minimum length:      0 (none)      │       │
│  │  ├── Complexity:          Not enforced   │       │
│  │  ├── Max age:             Not enforced   │       │
│  │  ├── Account lockout:     Not configured │       │
│  │  ├── Lockout threshold:   Not configured │       │
│  │  └── Password history:    Not configured │       │
│  │                                          │       │
│  │  ⚠ Brute force via SMB/RDP has no       │       │
│  │    lockout protection                    │       │
│  └──────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────┘
```

## Privilege Escalation Paths

```
FROM NETWORK (unauthenticated):
  1. SMB with no password → sandro (ADMIN) → full system
  2. AnyDesk relay → if session active → desktop control
  3. ASPNET account → SMB auth → limited access → priv esc

FROM LOCAL (any user):
  1. Any local user → su as sandro (no password) → ADMIN
  2. NT AUTHORITY\INTERACTIVE → admin shares (C$, ADMIN$)
  3. PowerShell Bypass → unrestricted script execution
```

## Remediation

| Priority | Action |
|----------|--------|
| 1 | Set strong password on sandro account |
| 2 | Disable ASPNET account |
| 3 | Investigate Guest login from 2023-05-12 |
| 4 | Set password on built-in Administrator (even if disabled) |
| 5 | Configure local security policy (lockout, complexity) |
| 6 | Remove sandro from Administrators if possible (use separate admin account) |
