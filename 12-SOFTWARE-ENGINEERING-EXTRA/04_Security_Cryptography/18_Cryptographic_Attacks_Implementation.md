# Cryptographic Attacks and Implementation Vulnerabilities

## Table of Contents

1. [Cryptographic Fundamentals Review](#1-cryptographic-fundamentals-review)
2. [Block Cipher Attacks](#2-block-cipher-attacks)
3. [Hash Function Attacks](#3-hash-function-attacks)
4. [Public Key Cryptography Attacks](#4-public-key-cryptography-attacks)
5. [TLS/SSL Attacks](#5-tlsssl-attacks)
6. [Password Hashing Attacks](#6-password-hashing-attacks)
7. [Side-Channel Attacks](#7-side-channel-attacks)
8. [Random Number Generator Failures](#8-random-number-generator-failures)
9. [Post-Quantum Cryptography](#9-post-quantum-cryptography)
10. [Lab: Cryptographic Attack Exercises](#10-lab-cryptographic-attack-exercises)

---

## 1. Cryptographic Fundamentals Review

### Symmetric vs Asymmetric Cryptography

Symmetric cryptography uses a single shared key for both encryption and decryption. The security assumption is that only authorized parties possess this key. Performance is typically 100-1000x faster than asymmetric counterparts for bulk data encryption.

Asymmetric (public-key) cryptography uses a mathematically linked key pair: a public key for encryption/verification and a private key for decryption/signing. The hardness assumptions differ by algorithm family — integer factorization (RSA), discrete logarithm (DH, DSA), elliptic curve discrete logarithm (ECDSA, ECDH, EdDSA).

In practice, hybrid schemes dominate: asymmetric crypto establishes a session key, then symmetric crypto encrypts the payload. TLS, PGP, and Signal all follow this pattern.

### Block Ciphers — AES and 3DES

**AES (Advanced Encryption Standard)** operates on 128-bit blocks with key sizes of 128, 192, or 256 bits. The algorithm consists of substitution (SubBytes), permutation (ShiftRows), mixing (MixColumns), and key addition (AddRoundKey) stages repeated 10/12/14 rounds respectively. AES remains unbroken in the classical computational model — the best known attack on full AES-128 is a biclique attack with complexity 2^126.1, computationally irrelevant.

**3DES (Triple DES)** applies the 56-bit DES cipher three times with two or three keys (EDE mode). The 64-bit block size creates a practical birthday-bound limitation at roughly 2^32 blocks (32 GB), exploited by Sweet32. 3DES is deprecated by NIST as of 2023 and prohibited for new applications.

### Block Cipher Modes of Operation

**ECB (Electronic Codebook):** Each block encrypted independently. Identical plaintext blocks produce identical ciphertext blocks, leaking patterns. Never use for data larger than one block.

**CBC (Cipher Block Chaining):** Each plaintext block XORed with the previous ciphertext block before encryption. Requires an unpredictable IV. Sequential encryption prevents parallelization. Vulnerable to padding oracle attacks when error messages leak padding validity.

**CTR (Counter Mode):** Encrypts a counter value to produce a keystream XORed with plaintext. Fully parallelizable. Nonce reuse is catastrophic — XORing two ciphertexts cancels the keystream, exposing XOR of plaintexts. No padding required.

**GCM (Galois/Counter Mode):** CTR mode combined with GHASH polynomial authentication. Provides authenticated encryption with associated data (AEAD). Maximum message size per key-nonce pair: 2^39 - 256 bits. Nonce reuse breaks both confidentiality and authenticity — the GHASH key H is recoverable.

**CCM (Counter with CBC-MAC):** Combines CTR mode encryption with CBC-MAC authentication. Two-pass algorithm (MAC then encrypt). Used in IEEE 802.11i (WPA2) and Bluetooth. Less efficient than GCM but simpler to implement correctly.

### Stream Ciphers

**ChaCha20:** A 256-bit key, 96-bit nonce, 32-bit counter stream cipher by Daniel Bernstein. 20 rounds of quarter-round operations on a 4x4 matrix of 32-bit words. Combined with Poly1305 MAC as ChaCha20-Poly1305 (RFC 8439). Favored on platforms without AES hardware acceleration (mobile ARM pre-ARMv8). No known weaknesses at full 20 rounds.

**RC4:** A variable-key-size stream cipher historically used in WEP, SSL/TLS, and Microsoft products. Known weaknesses:
- Statistical biases in the first bytes of output (Fluhrer-Mantin-Shamir attack)
- Related-key vulnerabilities in WEP key scheduling
- Single-byte biases allowing plaintext recovery after ~2^30 encryptions (Royal Holloway attack)
- Prohibited by RFC 7465 for TLS since 2015

### Hash Functions

**SHA-2 Family (SHA-256, SHA-384, SHA-512):** Merkle-Damgård construction with Davies-Meyer compression. No practical collision or preimage attacks known. SHA-256 provides 128-bit collision resistance, SHA-512 provides 256-bit. Current standard for most applications.

**SHA-3 (Keccak):** Sponge construction — fundamentally different from Merkle-Damgård. Absorbs input blocks into a state, squeezes output. Immune to length extension attacks by design. SHA3-256 provides 128-bit collision resistance. Also provides SHAKE128/SHAKE256 extendable-output functions (XOFs).

**MD5:** 128-bit Merkle-Damgård hash. Collision attacks practical since 2004 (Wang et al.). Chosen-prefix collisions demonstrated in 2009. Used in certificate forgery (RapidSSL/MD5, Flame malware). Completely broken for any security purpose requiring collision resistance. Still acceptable for non-cryptographic checksums only.

**SHA-1:** 160-bit Merkle-Damgård hash. Theoretical weakness since 2005 (Wang). Practical collision demonstrated by Google/CWI in 2017 (SHAttered) — cost approximately $110,000 in cloud compute. Chosen-prefix collision achieved in 2020 (SHA-1 is a Shambles) for roughly $50,000. Deprecated everywhere except legacy compatibility.

### MACs (Message Authentication Codes)

**HMAC (Hash-based MAC):** HMAC-H(K, m) = H((K ⊕ opad) || H((K ⊕ ipad) || m)). Proven secure under the assumption that the underlying hash is a pseudorandom function. Resistant to length extension by construction. HMAC-SHA256 is the de facto standard.

**CMAC (Cipher-based MAC):** Based on CBC-MAC with a fix for variable-length message vulnerability. Uses AES as the block cipher. Produces tags up to the block size (128 bits for AES). Standardized in NIST SP 800-38B.

**Poly1305:** A one-time authenticator by Bernstein. Takes a 256-bit one-time key (split into r and s) and produces a 128-bit tag. Polynomial evaluation over GF(2^130-5). Must never reuse the key — designed for use with ChaCha20 or AES-CTR which provide fresh per-message keys.

### Digital Signatures

**RSA (PKCS#1 v2.1 / PSS):** Sign with private key, verify with public. Security relies on the RSA problem (related to factoring). Minimum recommended key size: 2048 bits (3072 bits for post-2030). PSS padding is probabilistic and provably secure; PKCS#1 v1.5 signatures are deterministic and have known vulnerabilities (Bleichenbacher's attack).

**ECDSA (Elliptic Curve DSA):** Based on the elliptic curve discrete logarithm problem. Key sizes: 256 bits (P-256), 384 bits (P-384). Critical requirement: the per-signature nonce k must be uniformly random and secret. Any leakage of k bits allows private key recovery via lattice attacks. Deterministic ECDSA (RFC 6979) mitigates nonce generation failures.

**EdDSA (Ed25519, Ed448):** Schnorr-type signature over twisted Edwards curves. Deterministic nonce derived from the private key and message via hash — eliminates the nonce reuse catastrophe. Ed25519 uses Curve25519, provides ~128-bit security. Fast, constant-time implementations available. Increasingly preferred over ECDSA.

### Key Exchange

**Diffie-Hellman (DH):** Classical finite-field key exchange. Security based on the computational Diffie-Hellman assumption. Vulnerable to man-in-the-middle without authentication. Group selection critical — weak/small groups enable Logjam; reuse of group parameters enables precomputation (NOBUS primes).

**ECDH (Elliptic Curve DH):** DH over elliptic curve groups. Same security at smaller key sizes (256-bit ECDH ≈ 3072-bit DH). Curve choice matters: NIST curves (P-256, P-384) are standardized but have lingering concerns about parameter generation; Curve25519 is rigid and widely trusted.

**X25519:** ECDH specifically using Curve25519 in Montgomery form. Designed for simple, safe implementation: clamping eliminates small-subgroup attacks, all 32-byte strings are valid public keys. Used in TLS 1.3, Signal, WireGuard, Noise Protocol.

### Randomness and CSPRNGs

A **Cryptographically Secure Pseudo-Random Number Generator (CSPRNG)** must satisfy:
1. **Next-bit unpredictability:** Given the first k bits of output, no polynomial-time algorithm can predict bit k+1 with probability significantly better than 1/2.
2. **State compromise resistance (forward secrecy):** Compromising the current state does not reveal past outputs.

Platform CSPRNGs:
- Linux: `/dev/urandom` (always safe after boot, uses ChaCha20), `getrandom()` syscall (blocks until entropy available)
- Windows: `BCryptGenRandom()` (replaces CryptGenRandom)
- OpenSSL: `RAND_bytes()` using a DRBG (AES-CTR-DRBG or HASH-DRBG)

NIST SP 800-90A approved DRBGs: HMAC-DRBG, Hash-DRBG, CTR-DRBG. Dual_EC_DRBG was withdrawn (NSA backdoor).

---

## 2. Block Cipher Attacks

### ECB Mode — The Penguin Problem

ECB's fatal flaw is determinism: identical plaintext blocks always produce identical ciphertext blocks under the same key. The "ECB penguin" is the canonical demonstration — encrypting a bitmap image in ECB mode preserves the spatial structure because identical color regions produce identical ciphertext blocks.

**Block Substitution Attack:**

In ECB mode, an attacker who can capture multiple ciphertexts can rearrange blocks freely. Consider a financial transaction encrypted with AES-ECB:

```
Block 1: "FROM: Alice     " → C1
Block 2: "TO:   Bob       " → C2  
Block 3: "AMOUNT: $100.00 " → C3
```

An attacker who previously captured a block encrypting "TO:   Mallory   " as C2' can substitute C2 with C2' without detection. No integrity check exists in raw ECB.

**Real-world occurrence:** Adobe's 2013 breach stored password "hints" encrypted under ECB with the same key. Identical passwords produced identical ciphertexts, enabling pattern analysis across 150 million accounts.

### CBC Mode — Padding Oracle Attack (Vaudenay 2002)

The padding oracle attack exploits applications that reveal whether decryption produced valid PKCS#7 padding. An attacker can decrypt any ciphertext block without the key by making at most 256 × block_size_in_bytes oracle queries per block.

**Mechanics:**

CBC decryption: P_i = D_K(C_i) ⊕ C_{i-1}

To decrypt block C_i, the attacker submits modified (C'_{i-1} || C_i) pairs and observes the padding validation response. By varying the last byte of C'_{i-1} through all 256 values, exactly one will produce valid padding (0x01 in the last position). When the oracle confirms valid padding:

```
D_K(C_i)[last_byte] ⊕ C'_{i-1}[last_byte] = 0x01
```

Therefore: `D_K(C_i)[last_byte] = 0x01 ⊕ C'_{i-1}[last_byte]`

The attacker recovers the intermediate state byte, then derives the plaintext byte:
`P_i[last_byte] = D_K(C_i)[last_byte] ⊕ C_{i-1}[last_byte]`

Repeat for each byte position from right to left, each time setting the already-known bytes to form valid padding of increasing length.

**Complexity:** Maximum 256 × 16 = 4,096 oracle queries per 128-bit block. In practice, often fewer due to known plaintext structure.

**Affected systems:**
- ASP.NET (CVE-2010-3332) — MS10-070, exploitable via timing differences
- JavaServer Faces (JSF) ViewState
- Ruby on Rails session cookies (pre-4.0)
- CBC-mode TLS ciphersuites (POODLE, Lucky13)

### Bit-Flipping Attack in CBC

CBC's malleability allows targeted plaintext modification without knowing the key. Flipping bit j in ciphertext block C_{i-1} flips the same bit j in plaintext block P_i (while corrupting P_{i-1} entirely).

**Attack scenario:** An encrypted cookie contains `role=user`. If the attacker knows the byte offset of this field, they can XOR the corresponding position in the previous ciphertext block with `user ⊕ admn` to change decrypted text to `role=admn`.

```python
# Bit-flip demonstration
import os

target_byte_position = 5  # position of 'u' in 'user'
original_char = ord('u')
desired_char = ord('a')

# XOR difference applied to the previous ciphertext block
flip_mask = original_char ^ desired_char  # 0x14
ciphertext_modified = bytearray(ciphertext)
ciphertext_modified[prev_block_offset + target_byte_position] ^= flip_mask
```

**Mitigation:** Always use authenticated encryption (GCM, CCM, ChaCha20-Poly1305) or Encrypt-then-MAC.

### BEAST Attack (Browser Exploit Against SSL/TLS) — CVE-2011-3389

BEAST exploits CBC in TLS 1.0 where the IV for each record is the last ciphertext block of the previous record (predictable IV). This enables a chosen-plaintext attack:

1. Attacker controls part of the plaintext (e.g., via malicious JavaScript in the same origin)
2. Attacker knows the IV (last ciphertext block of previous record)
3. Attacker crafts plaintext to align a guessed byte at a block boundary
4. If C_new == C_target, the guess is correct

**Complexity:** 256 queries per byte on average (128 expected).

**Mitigations:**
- TLS 1.1+ uses explicit random IVs (fixed by design)
- 1/n-1 record splitting: Send a 1-byte record first, making the IV unpredictable for the remaining data
- Move to AEAD ciphersuites

### POODLE (Padding Oracle On Downgraded Legacy Encryption) — CVE-2014-3566

POODLE attacks SSLv3's padding scheme. Unlike PKCS#7, SSLv3 padding is not fully specified — only the last byte (padding length) is checked. This creates a padding oracle:

1. Force TLS downgrade to SSLv3 (via protocol version intolerance simulation)
2. Align target byte at the end of a block
3. Copy the block containing the target to the final position (replacing the padding block)
4. If the server accepts (1/256 probability), the padding byte equals the block cipher's intermediate value XORed with the known padding length

**POODLE on TLS (CVE-2014-8730):** Some TLS implementations (F5, A10 Networks) accepted SSLv3-style padding in TLS, creating the same vulnerability without downgrade.

**Mitigation:** Disable SSLv3 entirely. Use TLS_FALLBACK_SCSV to prevent downgrade.

### LUCKY13 — Timing Attack on CBC-Mode TLS

LUCKY13 (CVE-2013-0169) exploits timing differences in CBC-mode MAC verification. TLS computes HMAC over the plaintext after removing padding. Different padding lengths result in different amounts of data hashed, creating a timing signal:

- Valid padding of length L: HMAC computed over (header || plaintext minus L padding bytes)
- Invalid padding: HMAC computed over (header || plaintext minus 0 padding bytes), then comparison fails

The timing difference between hashing N bytes vs N-L bytes is measurable over many samples. Attacks require ~2^23 sessions for byte recovery.

**Mitigation:** Constant-time padding validation and MAC computation (process the maximum possible data length regardless of actual padding). TLS 1.3 eliminates CBC entirely.

### Bleichenbacher's Padding Oracle on RSA PKCS#1 v1.5 (1998)

RSA PKCS#1 v1.5 encryption pads the message as: `0x00 || 0x02 || [random non-zero bytes] || 0x00 || [message]`

If a server reveals whether decrypted ciphertext has valid PKCS#1 v1.5 structure (starts with 0x0002), an attacker can decrypt arbitrary ciphertexts:

1. Multiply the ciphertext by chosen values: c' = c · s^e mod n
2. Decryption of c' = m·s mod n — if the server confirms valid padding, m·s falls within a known range
3. Iteratively narrow the range of possible m values

**Complexity:** Approximately 2^20 oracle queries for a 2048-bit RSA key (median case from the original paper).

**Impact:** Recovers TLS premaster secrets, enabling session decryption. Resurfaced repeatedly as DROWN (2016) and ROBOT (2017).

### Related-Key Attacks

Related-key attacks assume the adversary can observe encryptions under keys with known mathematical relationships. While unrealistic for most protocols, they apply to:

- Key-schedule weaknesses (AES-192/256 have related-key distinguishers at full rounds — Biryukov/Khovratovich 2009, but with impractical complexity ~2^99)
- WEP protocol: RC4 keys derived as (base_key || incrementing IV), enabling Fluhrer-Mantin-Shamir attack
- Hash function constructions using block ciphers (e.g., Davies-Meyer)

### Meet-in-the-Middle Attack

The classic attack on Double-DES demonstrates why doubling key length doesn't double security:

1. Encrypt plaintext P under all 2^56 possible K1 values → store as table T
2. Decrypt ciphertext C under all 2^56 possible K2 values → look up in T
3. Match gives candidate (K1, K2) pair

**Complexity:** 2^57 operations and 2^56 storage instead of the expected 2^112.

This is why 3DES uses three operations (EDE) — providing 112-bit effective security (due to MITM on the outer two operations).

---

## 3. Hash Function Attacks

### Collision Attacks — The Birthday Paradox

The birthday paradox states that in a set of n randomly chosen values from a space of N, a collision occurs with >50% probability when n ≈ 1.2√N. For a hash with d-bit output, expect collisions after approximately 2^(d/2) evaluations.

| Hash Function | Output Bits | Collision Resistance | Status |
|---|---|---|---|
| MD5 | 128 | 2^18 (practical) | **Broken** — collisions in seconds |
| SHA-1 | 160 | 2^63 (practical) | **Broken** — chosen-prefix at ~$50K |
| SHA-256 | 256 | 2^128 (theoretical) | **Secure** |
| SHA-3-256 | 256 | 2^128 (theoretical) | **Secure** |
| SHA-512 | 512 | 2^256 (theoretical) | **Secure** |

**MD5 Collision History:**
- 2004: Wang et al. produce first collision (~hours on a PC)
- 2006: Chosen-prefix collisions (Stevens et al.)
- 2008: RapidSSL rogue CA certificate via MD5 collision
- 2012: Flame malware used a novel MD5 chosen-prefix collision to forge Windows Update signatures
- 2024: Collisions achievable in < 1 second on commodity hardware

**SHA-1 Collision History:**
- 2005: Wang theoretical attack (2^63)
- 2017: SHAttered (Google/CWI) — first practical collision, ~6,500 CPU-years / $110K
- 2020: SHA-1 is a Shambles (Leurent/Peyrin) — chosen-prefix collision for ~$50K
- Impact: PGP key spoofing, Git commit manipulation demonstrated

### Preimage Attacks — Current Status

A preimage attack finds m such that H(m) = h for a given h. A second preimage finds m' ≠ m such that H(m') = H(m).

| Algorithm | Preimage Status |
|---|---|
| MD5 | No practical preimage (2^123.4 best known) |
| SHA-1 | No practical preimage (2^159 expected) |
| SHA-256 | Secure (2^256 expected) |
| SHA-3-256 | Secure (2^256 expected) |

Even MD5, despite catastrophic collision weakness, has no known practical preimage attack. This is why MD5 remains acceptable for HMAC (where preimage resistance matters more than collision resistance) but unacceptable for digital signatures (where collision resistance is essential).

### Length Extension Attacks

Merkle-Damgård hashes (MD5, SHA-1, SHA-256) are vulnerable to length extension: given H(m) and len(m), an attacker can compute H(m || padding || m') without knowing m.

**Mechanism:** The hash state after processing m is embedded in the output. The attacker initializes the hash state to H(m), appends the known padding that would have been applied, then continues hashing attacker-controlled data.

**Exploitable pattern:** `MAC = SHA256(secret || message)` — the attacker can extend the message and compute a valid MAC without the secret.

```python
# Length extension attack (conceptual)
# Given: hash = SHA256(secret || original_message), len(secret)=16
# Attacker computes: SHA256(secret || original_message || padding || extension)

import struct

def sha256_length_extend(original_hash, original_msg_len, extension):
    """
    Recover internal state from hash output,
    continue hashing from that state.
    """
    # The 256-bit hash IS the internal state after processing
    # Split into eight 32-bit state words
    h = struct.unpack('>8I', bytes.fromhex(original_hash))
    
    # Calculate the padding that was applied
    total_bits = (original_msg_len) * 8
    # padding: 0x80 || zeros || 64-bit length
    pad_len = (55 - original_msg_len) % 64 + 1
    
    # New message length for hash computation
    new_len = original_msg_len + pad_len + 8 + len(extension)
    
    # Continue hashing 'extension' starting from state h
    # (Implementation requires modifying SHA-256 to accept initial state)
    pass
```

**SHA-3 resistance:** SHA-3 (Keccak sponge) is immune by design — the capacity portion of the state is never output, preventing state recovery from the hash value.

**Mitigation:** Use HMAC (immune due to outer hash), or use SHA-3/BLAKE2/BLAKE3.

### Hash Collision in Practice

**Certificate Forgery (2008 RapidSSL):**
Researchers generated an MD5 collision between a legitimate certificate request and a rogue CA certificate. The legitimate cert was signed by the CA; the signature was equally valid for the rogue CA cert. Result: a trusted CA certificate under attacker control.

**Git Commit Manipulation:**
Git uses SHA-1 for object identification. The SHAttered collision demonstrated that two distinct PDF files could have the same SHA-1 hash. Applied to Git: an attacker could create two commits (one benign, one malicious) with the same hash. The benign commit gets reviewed and merged; the malicious version is substituted later. Git has implemented SHA-1 collision detection (checking for the SHAttered technique specifically) and is migrating to SHA-256.

**File Replacement:**
Any system using MD5/SHA-1 for integrity verification is vulnerable. Software distribution, forensic evidence chains, and backup verification systems that rely on broken hashes can be subverted by chosen-prefix collisions.

### HMAC Security vs Raw Hash

HMAC provides a security proof: if the underlying hash function is a PRF (pseudorandom function), HMAC is a secure MAC. The double-hashing structure:

```
HMAC-H(K, m) = H((K ⊕ opad) || H((K ⊕ ipad) || m))
```

eliminates length extension by design (the outer hash processes fixed-length input). HMAC-MD5 is not known to be broken despite MD5's collision weakness — the PRF assumption holds independently of collision resistance. However, migrating away from HMAC-MD5 is recommended to reduce audit surface.

---

## 4. Public Key Cryptography Attacks

### RSA Attacks

**Small Public Exponent Attack:**
If e=3 and the message m satisfies m^3 < n (no modular reduction occurs), then c = m^3 and the plaintext is simply the cube root of c. Proper padding (OAEP) ensures m is close to n in size, preventing this.

**Håstad's Broadcast Attack:**
If the same message is encrypted with e=3 to three different recipients (different moduli n1, n2, n3), the attacker recovers m^3 via the Chinese Remainder Theorem, then takes the integer cube root.

**Common Modulus Attack:**
If two users share the same RSA modulus n but have different (e1, d1) and (e2, d2) key pairs, either user can factor n (recovering the other's private key). Never share moduli between distinct keys.

**Bleichenbacher's Attack (PKCS#1 v1.5 — detailed):**
See Section 2 for the mechanism. The attack adaptively multiplies the ciphertext by chosen blinding factors, using the padding oracle to narrow the plaintext range. Each oracle response that confirms valid padding (starts with 0x0002) cuts the search space roughly in half. After ~10,000-20,000 queries (depending on the implementation), the full plaintext is recovered.

**Coppersmith's Method:**
Exploits small solutions to polynomial equations modulo n. Applications:
- Recovering plaintext when 2/3 of the bits are known (stereotyped messages)
- Factoring n when 1/2 of the bits of a factor are known
- Breaking RSA signatures when the hash is too short relative to the modulus

**Factoring Advances:**
- RSA-768 (768-bit) factored in 2009 — ~2,000 core-years
- RSA-250 (829-bit decimal) factored in 2020 — ~2,700 core-years
- Current estimate for RSA-2048: ~2^100 operations (far beyond reach)
- Number Field Sieve remains the best classical algorithm: L[1/3, (64/9)^(1/3)]

### ECDSA Attacks

**Nonce Reuse Catastrophe (PS3 Hack, 2010):**
If the same nonce k is used for two different messages, the private key is immediately recoverable:

```
s1 = k^(-1)(H(m1) + r·d) mod q
s2 = k^(-1)(H(m2) + r·d) mod q

s1 - s2 = k^(-1)(H(m1) - H(m2)) mod q
k = (H(m1) - H(m2)) · (s1 - s2)^(-1) mod q
d = (s1·k - H(m1)) · r^(-1) mod q
```

Sony used a static nonce (k was a constant) for PS3 code signing. The private key was recoverable from any two signatures. The entire PS3 security model collapsed — arbitrary code signing became trivial.

**Biased Nonce / Lattice Attacks:**
Even partial nonce leakage is catastrophic. If an attacker knows the most significant L bits of each nonce across many signatures, the hidden number problem (HNP) can be solved via lattice reduction (LLL/BKZ algorithms):

- 1-2 bits of bias per nonce: recoverable with ~200 signatures
- Known LSB: recoverable with ~100 signatures
- ECDSA implementations leaking nonce bits through timing side channels are exploitable

Research by Brumley & Tuveri (2011) demonstrated this against OpenSSL's ECDSA on P-256.

**Minerva Attack (2019):** Timing leakage in nonce generation across multiple cryptographic libraries (libgcrypt, wolfSSL, MatrixSSL) enabled practical private key recovery through lattice methods.

### Diffie-Hellman Attacks

**Logjam (2015):**
Exploits weak DH groups. The attack has two components:
1. Precomputation: For a fixed DH group (prime p), compute a massive table allowing discrete log computation. Cost: ~academic resources for 512-bit primes, estimated state-level for 1024-bit.
2. Active downgrade: MitM forcing export-grade 512-bit DH (DHE_EXPORT) via protocol downgrade.

8.4% of top-1M HTTPS sites were vulnerable. The attack directly reads the session key.

**NOBUS (Nobody But Us) Primes:**
Hypothesis: intelligence agencies may have influenced the selection of common DH groups (RFC primes) to enable precomputation with classified algorithmic advantages or dedicated hardware. Evidence is circumstantial but:
- NSA reportedly spent ~$250M/year on "cryptanalytic IT program"
- Snowden documents mention "vast amounts of encrypted Internet data which have up till now been discarded are now exploitable"
- The 1024-bit Oakley Group 2 (RFC 2409) was used by the majority of VPN connections

**Mitigation:** Use 2048+ bit groups or switch to X25519/X448.

**Small Subgroup Attacks:**
If the DH group order has small factors, an attacker can send a public key in a small-order subgroup. The resulting shared secret leaks bits of the private key modulo the subgroup order. Mitigations: validate that received public keys are in the correct subgroup, use safe primes (p = 2q + 1), or use X25519 (which clamps to prevent this).

### Implementation Attacks on RSA

**Timing Attacks (Kocher 1996):**
RSA private key operations (modular exponentiation) take variable time depending on the key bits. Square-and-multiply: when a key bit is 1, an additional multiplication is performed. Statistical analysis of operation timing across many decryptions reveals individual key bits.

**Countermeasure:** RSA blinding — multiply the ciphertext by a random value before decryption, then remove the blinding after: `m = (c · r^e)^d · r^(-1) mod n = m · r · r^(-1) = m`

**Power Analysis (SPA/DPA):**
Simple Power Analysis: A single power trace during exponentiation directly reveals the sequence of squares and multiplies (and thus key bits) on unprotected hardware.

Differential Power Analysis: Statistical correlation between intermediate values and power consumption across many operations. Breaks even implementations that attempt to make control flow constant.

**Countermeasures:** Constant-time Montgomery ladder, blinding, noise injection, balanced logic.

### EdDSA Resilience to Nonce Issues

EdDSA derives the per-signature nonce deterministically: `r = H(prefix || secret_key_component || message)`. This design choice means:
- Same message always produces the same signature (deterministic — no random component)
- Nonce reuse from PRNG failure is impossible
- The "nonce" is as secure as the hash function itself
- No timing variation from nonce generation

This makes EdDSA categorically immune to the class of attacks that have destroyed ECDSA deployments (PS3, blockchain wallets, HSMs with poor RNG).

---

## 5. TLS/SSL Attacks

### DROWN — Cross-Protocol Attack via SSLv2 (2016, CVE-2016-0800)

DROWN (Decrypting RSA with Obsolete and Weakened eNcryption) enables decryption of TLS connections by exploiting SSLv2 support on any server sharing the same RSA key. Even if the target server only supports TLS 1.2, if any other server with the same certificate supports SSLv2, the attack succeeds.

**Mechanism:** SSLv2 has a Bleichenbacher-like padding oracle. The attacker converts captured TLS ciphertexts into SSLv2-compatible queries, uses the SSLv2 oracle to decrypt the TLS premaster secret.

**General DROWN:** ~2^50 SSLv2 connections required.
**Special DROWN (CVE-2016-0703):** Exploits an additional bug in OpenSSL's SSLv2 implementation, reducing to ~2^18 connections — practical in under a minute.

**Impact:** 33% of all HTTPS servers were vulnerable at disclosure (sharing keys with SSLv2-capable servers).

### ROBOT — Return of Bleichenbacher's Oracle Threat (2017)

ROBOT demonstrated that Bleichenbacher's 1998 RSA padding oracle persists in modern TLS implementations. Vendors had attempted fixes, but subtle timing and error-handling differences still leaked padding validity:

- F5 BIG-IP: Different alert messages for padding errors vs decryption errors
- Cisco ACE: Timing differences in error paths
- Citrix NetScaler: Exploitable timing oracle
- Palo Alto: Similar issues in TLS termination

**Impact:** Decryption of any captured TLS session using RSA key exchange (not forward-secret). Facebook's TLS infrastructure was vulnerable.

**Mitigation:** Disable RSA key exchange entirely (use ECDHE). TLS 1.3 removes RSA key transport by specification.

### Heartbleed (CVE-2014-0160)

A buffer over-read in OpenSSL's TLS Heartbeat extension implementation. The client sends a Heartbeat request specifying a payload length; the server echoes that many bytes back — but the server reads beyond the actual payload into adjacent memory (up to 64KB per request).

**What leaked:**
- Server private keys (confirmed extractable within hours)
- Session cookies and tokens
- User credentials in flight
- Source code fragments from process memory

**Root cause:** Missing bounds check:

```c
// Vulnerable code (simplified)
memcpy(response, request_payload, payload_length);
// payload_length was from the request, not validated against actual data received
```

**Impact:** Affected ~17% of TLS servers (all using vulnerable OpenSSL 1.0.1-1.0.1f). Patching required certificate revocation and reissuance.

### CRIME / BREACH — Compression Side-Channel

**CRIME (Compression Ratio Info-leak Made Easy, 2012):**
Exploits TLS-level compression (DEFLATE). If an attacker can inject known plaintext adjacent to secrets in the compressed stream, they observe compression ratio changes indicating when guesses match existing content.

Attack: Guess bytes of a session cookie one at a time. If the guess matches existing data, compression shrinks the ciphertext. Observe length → confirm correct byte.

**BREACH (Browser Reconnaissance and Exfiltration via Adaptive Compression of Hypertext, 2013):**
Same principle but exploits HTTP-level compression (gzip). Since virtually all HTTP responses are gzip-compressed, disabling TLS compression alone is insufficient.

**Requirements:**
1. Attacker can cause victim to make requests (reflected input)
2. Response body contains a secret (CSRF token) and reflects attacker-controlled text
3. HTTP compression is enabled

**Mitigation:** Randomize secrets per response, add random padding to responses, separate secrets from attacker-controlled content, use per-request CSRF tokens.

### Sweet32 — Birthday Bound on 64-bit Block Ciphers (2016)

Block ciphers with 64-bit blocks (3DES, Blowfish) have a birthday bound at 2^32 blocks (32 GB). After this much data under one key, CBC mode leaks plaintext blocks when collisions occur in the ciphertext.

**Attack:** Capture long-lived HTTPS session (e.g., keep-alive connection serving many requests). After ~32 GB of data, ciphertext block collisions reveal XOR of plaintext blocks. Combined with known plaintext structure (HTTP headers), extract session cookies.

**Impact:** Affected 3DES ciphersuites in TLS (still enabled on 1-2% of servers at disclosure).

**Mitigation:** Disable 3DES. Limit data per key (rekeying). Use AES (128-bit block).

### Renegotiation Attack (CVE-2009-3555)

TLS renegotiation allows mid-connection parameter changes. The flaw: data sent before renegotiation (by the attacker) gets concatenated with post-renegotiation data (from the legitimate client) at the application layer.

**Attack scenario:**
1. Attacker establishes TLS connection to server
2. Attacker sends partial HTTP request: `GET /transfer?to=attacker HTTP/1.1\r\nX-Ignore: `
3. Attacker initiates renegotiation, relays client's handshake
4. Client completes handshake and sends: `POST /account HTTP/1.1\r\nCookie: auth=...\r\n\r\n`
5. Server sees: Attacker's prefix + Client's authenticated request

**Fix:** RFC 5746 — Renegotiation Indication Extension. Both parties include the previous handshake Finished messages in the renegotiation, binding old and new sessions.

### Downgrade Attacks — FREAK, Logjam, Version Rollback

**FREAK (Factoring RSA Export Keys, 2015):**
MitM downgrades to export-grade RSA (512-bit RSA_EXPORT ciphersuites). 512-bit RSA is factorable in ~7 hours on EC2 (~$100). Once factored, the attacker recovers the session key.

**Logjam (2015):**
Same concept for DH — downgrade to 512-bit DHE_EXPORT. Precomputation for common 512-bit DH primes enables real-time decryption.

**Version Rollback:**
Pre-TLS 1.3, version negotiation was unauthenticated. An active attacker could modify ClientHello to advertise only older versions, forcing use of weaker protocols. TLS 1.3 authenticates the version negotiation within the handshake transcript.

**TLS_FALLBACK_SCSV (RFC 7507):** A signaling ciphersuite value indicating the client is retrying with a lower version — the server rejects if it supports higher.

### Raccoon Attack (2020, CVE-2020-1968)

A timing vulnerability in DH-based TLS key exchange. The premaster secret derivation involves stripping leading zero bytes. When the shared DH secret starts with zero(s), the subsequent KDF processing takes measurably less time (fewer bytes to hash).

**Mechanism:** The attacker observes timing of the ServerKeyExchange → Finished message flow. A shorter premaster secret (leading zeros stripped) produces detectable timing. Combined with lattice techniques, partial information about the premaster secret enables full recovery.

**Practicality:** Requires extremely precise timing measurements and many connections. More of a theoretical protocol weakness than a practical threat against most deployments.

**Mitigation:** TLS 1.3 uses HKDF with fixed-length inputs. For older versions, constant-time padding of DH shared secrets before KDF.

---

## 6. Password Hashing Attacks

### Offline Cracking — Hashcat and John the Ripper

Offline password cracking assumes the attacker has obtained password hashes (via database breach, SAM file extraction, /etc/shadow access, NTDS.dit dump). The attacker performs unlimited guesses locally without rate limiting.

**Hashcat** is a GPU-accelerated password recovery tool supporting 300+ hash types:

```bash
# Basic dictionary attack against SHA-256 hashes
hashcat -m 1400 hashes.txt wordlist.txt

# Rule-based attack (dictionary + mutations)
hashcat -m 1400 hashes.txt wordlist.txt -r rules/best64.rule

# Mask attack (brute force with pattern)
# ?u = uppercase, ?l = lowercase, ?d = digit, ?s = special
hashcat -m 1400 hashes.txt -a 3 ?u?l?l?l?l?l?d?d

# Combinator attack (word1+word2)
hashcat -m 1400 hashes.txt -a 1 wordlist1.txt wordlist2.txt

# Show cracked passwords
hashcat -m 1400 hashes.txt --show
```

**John the Ripper** excels at CPU-based cracking and format detection:

```bash
# Auto-detect and crack
john hashes.txt

# Specify format and wordlist
john --format=sha256crypt --wordlist=rockyou.txt hashes.txt

# Incremental (brute force) mode
john --format=raw-sha256 --incremental hashes.txt

# Show results
john --show hashes.txt
```

### Rainbow Tables and Their Limitations

Rainbow tables are precomputed hash chains mapping hash outputs back to plaintexts. A table for a given hash function and keyspace allows near-instant lookup.

**Limitations:**
1. **Salt defeats them entirely.** A random salt prepended/appended to the password means each salt value requires a separate rainbow table. With a 128-bit salt, precomputation is infeasible.
2. Storage requirements: Complete table for 8-char alphanumeric (62^8 ≈ 218 trillion) SHA-1 is ~2+ TB.
3. GPU cracking has largely made rainbow tables obsolete — modern GPUs achieve billions of SHA-1/s, making real-time cracking of weak passwords faster than table lookup for salted hashes.

**When rainbow tables still apply:** Unsalted hashes (NTLM, LM hashes, older web applications that hashed without salt).

### Hash Algorithm Comparison for Password Storage

| Algorithm | Speed (RTX 4090) | Salt | Memory-Hard | GPU Resistant | Recommendation |
|---|---|---|---|---|---|
| MD5 | ~160 GH/s | No (usually) | No | No | **Never use** |
| SHA-1 | ~70 GH/s | No (usually) | No | No | **Never use** |
| SHA-256 | ~22 GH/s | If added | No | No | **Never use for passwords** |
| bcrypt (cost 12) | ~70 KH/s | Yes (128-bit) | Limited (4KB) | Yes (FPGA-limited) | **Acceptable** |
| scrypt (N=2^14) | ~2 KH/s | Yes | Yes | Yes | **Good** |
| Argon2id (t=3,m=64MB) | ~10 H/s | Yes (128-bit) | Yes (tunable) | Yes | **Best practice** |

### GPU and ASIC Acceleration

Modern GPUs are massively parallel hash engines. Hash rates on a single NVIDIA RTX 4090:

| Algorithm | Hash Rate | Time for 10B guesses |
|---|---|---|
| NTLM | ~300 GH/s | ~0.03 seconds |
| MD5 | ~160 GH/s | ~0.06 seconds |
| SHA-256 | ~22 GH/s | ~0.45 seconds |
| SHA-512 | ~4 GH/s | ~2.5 seconds |
| bcrypt (cost 5) | ~180 KH/s | ~15 hours |
| bcrypt (cost 12) | ~70 KH/s | ~40 hours |
| sha512crypt ($6$) | ~2 MH/s | ~1.4 hours |
| Argon2id (64MB) | ~10 H/s | ~31 years |

**ASIC considerations:** Bitcoin mining ASICs perform SHA-256d at ~200 TH/s per unit. Purpose-built password cracking ASICs for bcrypt exist but are limited by the algorithm's memory access pattern. Argon2 was specifically designed to resist ASIC advantage through configurable memory requirements.

### Password Spraying vs Credential Stuffing

**Password Spraying:** Try a small set of common passwords against many accounts. Avoids lockout thresholds (1-2 attempts per account per lockout window). Effective against organizations with weak password policies.

```bash
# Spraying against Office365 using known tool
# Common passwords: Company2024!, Welcome1!, Spring2024!
# Timing: 1 attempt per 30 minutes per account to avoid detection
```

**Credential Stuffing:** Reuse stolen username:password pairs from breach databases against other services. Exploits password reuse across services. Tools: Sentry MBA, STORM, custom scripts with proxy rotation.

**Economics:**
- Breach databases: billions of credentials available for < $100
- Success rate: typically 0.1-2% of attempts yield valid sessions
- ROI: Even 0.1% success on 1M credentials = 1,000 compromised accounts

### Cracking Methodologies

**Dictionary Attack:** Direct wordlist lookup. RockYou (14M), SecLists, breach compilations, language-specific lists. Base hit rate: 30-60% of password sets.

**Rule-Based Attack:** Apply transformations to dictionary words. Hashcat rules:
- `l` = lowercase, `u` = uppercase, `c` = capitalize
- `$1` = append "1", `^!` = prepend "!"
- `sa@` = substitute a→@, `ss$` = substitute s→$
- Combined: `c $1 $!` transforms "password" → "Password1!"

```bash
# Hashcat with dive.rule (comprehensive mutations)
hashcat -m 1000 ntlm_hashes.txt wordlist.txt -r rules/dive.rule
```

**Mask Attack:** Define character sets per position. For patterns like "Word####!":
```bash
hashcat -m 1000 hashes.txt -a 3 -1 ?u?l ?1?l?l?l?d?d?d?d?s
```

**Combinator Attack:** Concatenate words from two dictionaries. "correct" + "horse" = "correcthorse".

**Markov Chain Attack:** Statistically model character probability per position based on real password corpora. Characters that commonly appear at position N given the previous characters. More efficient than pure brute force.

**Hybrid Attack:** Dictionary + mask: append/prepend patterns to dictionary words.
```bash
# Dictionary word + 4 digits + special
hashcat -m 1000 hashes.txt -a 6 wordlist.txt ?d?d?d?d?s
```

---

## 7. Side-Channel Attacks

### Timing Attacks and Constant-Time Programming

Timing attacks exploit data-dependent execution time. Cryptographic operations that branch on secret values, perform variable-iteration loops, or access memory at secret-dependent addresses leak information through measurable timing differences.

**Classic example — String comparison:**

```c
// VULNERABLE: Early-exit comparison
int compare(const char *a, const char *b, size_t len) {
    for (size_t i = 0; i < len; i++) {
        if (a[i] != b[i]) return 0;  // Timing reveals match position
    }
    return 1;
}

// SECURE: Constant-time comparison
int ct_compare(const unsigned char *a, const unsigned char *b, size_t len) {
    unsigned char result = 0;
    for (size_t i = 0; i < len; i++) {
        result |= a[i] ^ b[i];  // Always processes all bytes
    }
    return result == 0;  // Single branch at the end
}
```

**Constant-time programming rules:**
1. No branching on secret data (use bitwise selection: `mask = -(condition); result = (a & mask) | (b & ~mask)`)
2. No secret-dependent memory access (table lookups with secret index leak via cache timing)
3. No secret-dependent loop iteration counts
4. No variable-time arithmetic (some CPUs have variable-time multiply/divide)

**Cache Timing Attacks:**
AES T-table implementations perform table lookups indexed by secret-dependent values. These accesses hit different cache lines, and cache hit/miss timing reveals which table entries were accessed. Demonstrated remote key recovery against AES (Bernstein 2005, Osvik et al. 2006).

**Mitigation:** Bitsliced AES implementations, AES-NI hardware instructions (constant-time by design), cache-line-aligned tables.

### Power Analysis — SPA and DPA

**Simple Power Analysis (SPA):**
A single power trace during RSA private key operation directly reveals the key bits on unprotected implementations. The square-and-multiply algorithm shows distinctive power patterns: squaring operations are visually distinct from multiply operations in the power trace.

**Differential Power Analysis (DPA):**
Statistical technique correlating power consumption with hypothesized intermediate values across many operations:

1. Collect N power traces for known plaintexts
2. For each key byte hypothesis, compute the expected intermediate value (e.g., SubBytes output in AES round 1)
3. Correlate the expected Hamming weight of intermediate values with actual power consumption at each time point
4. The correct key hypothesis shows the highest correlation peak

**Targets:** Smart cards, embedded controllers, HSMs, IoT devices — anything where the attacker has physical proximity.

**Countermeasures:**
- Masking (randomize intermediate values with random shares)
- Hiding (add noise, randomize execution order, insert dummy operations)
- Dual-rail logic (constant Hamming weight regardless of data)
- Amplitude/timing randomization

### Electromagnetic Emanations — TEMPEST / Van Eck Phreaking

TEMPEST (Telecommunications Electronics Material Protected from Emanating Spurious Transmissions) refers to the exploitation of unintentional electromagnetic emissions from electronic equipment.

**Van Eck phreaking:** Reconstructing display content by capturing EM emissions from video cables and monitors. Demonstrated at distances of 100+ meters with directional antennas.

**Modern EM attacks on crypto:**
- RSA key extraction from laptop EM emissions at 1.5 meters (Genkin et al., 2014)
- AES key recovery from EM emanations of a smartphone (measured against the phone's chassis ground)
- GnuPG key extraction via EM side channel at 50cm using a consumer-grade radio receiver

**Countermeasures:** EM shielding (Faraday cages), filtered power lines, TEMPEST-rated equipment (NSA NSTISSAM TEMPEST/2-95), distance.

### Acoustic Cryptanalysis

RSA key extraction via sound emitted by capacitors and coils during computation. Demonstrated by Genkin, Shamir, and Tromer (2014):
- Frequency analysis of CPU acoustic emissions distinguishes different RSA operations
- GnuPG RSA key extracted by placing a mobile phone next to a target laptop
- Effective at 4+ meters with parabolic microphone

**Mitigation:** Acoustic dampening, algorithmic blinding (random noise in computation), disable CPU frequency scaling during crypto operations.

### Spectre/Meltdown and Transient Execution Attacks

**Meltdown (CVE-2017-5754):**
Exploits out-of-order execution on Intel CPUs to read kernel memory from userspace. The CPU speculatively accesses forbidden memory; even though the access is architecturally rolled back, the cache state change persists and can be measured.

**Spectre (CVE-2017-5753, CVE-2017-5715):**
Exploits branch prediction to execute code paths that leak secrets via cache side channels. Variant 1 (bounds check bypass) and Variant 2 (branch target injection) enable cross-process secret extraction.

**Impact on crypto:**
- Process isolation guarantees broken — crypto running in one process may leak keys to a co-located attacker process
- Cloud VMs: potential cross-tenant key leakage
- Browser JS: potential key extraction via browser engine speculation
- Constant-time code is insufficient if speculative execution follows secret-dependent paths

**Mitigations:** Retpoline (indirect branch protection), IBRS/IBPB microcode updates, kernel page table isolation (KPTI), serializing instructions (lfence), compiler barriers.

### Hertzbleed (2022, CVE-2022-23823, CVE-2022-24436)

Hertzbleed demonstrates that power side channels manifest as timing side channels through dynamic voltage and frequency scaling (DVFS). CPU frequency varies with power consumption, which depends on the data being processed.

**Mechanism:**
1. Modern CPUs adjust clock frequency based on power draw (Intel Turbo Boost, AMD Precision Boost)
2. Different intermediate values in crypto operations draw different amounts of power
3. Different power levels → different CPU frequencies → different wall-clock execution times
4. An attacker measuring execution time indirectly observes power consumption

**Impact:** Demonstrated full key extraction from SIKE (post-quantum KEM) on Intel and AMD CPUs. Applies to any algorithm with data-dependent power consumption, even if the code is "constant-time" in instruction count.

**Mitigation:** Disable frequency scaling (performance impact), or ensure intermediate values are independent of secrets (algorithmic masking).

### Microarchitectural Attacks — Flush+Reload and Prime+Probe

**Flush+Reload:**
Exploits shared memory (shared libraries, deduplication):
1. Attacker flushes a target cache line (using `clflush`)
2. Victim executes (potentially accessing the target line)
3. Attacker measures reload time — fast (cache hit) = victim accessed the line; slow (cache miss) = not accessed

Application: Determine which code paths the victim executes (AES T-table entries, RSA multiplication routines). Enables key recovery with high resolution.

**Prime+Probe:**
Works without shared memory (applicable across VMs):
1. Attacker fills a cache set with their own data (Prime)
2. Victim executes
3. Attacker accesses their data — slow access indicates the victim evicted attacker's line from that cache set (Probe)

Lower granularity than Flush+Reload but works across isolation boundaries.

**Practical impact:**
- Cross-VM RSA key extraction demonstrated on AWS/GCP
- AES key extraction from co-located processes
- Combined with speculative execution for enhanced capabilities

---

## 8. Random Number Generator Failures

### Debian OpenSSL PRNG Catastrophe (CVE-2008-0166)

In 2006, a Debian maintainer removed two lines from OpenSSL's random number generation code because Valgrind reported use of uninitialized memory. The "fix" eliminated all entropy sources except the process ID:

```c
// What was removed (critical entropy mixing)
MD_Update(&m, buf, j);  // Removed - Valgrind warning
// ...
MD_Update(&m, buf, j);  // Removed - Valgrind warning
```

**Consequence:** The PRNG was seeded solely by the PID (15-bit space on 32-bit systems, effectively ~32,767 possible seeds). All RSA, DSA, and ECDSA keys generated on affected Debian/Ubuntu systems from September 2006 to May 2008 were from a set of ~32,767 keys per key size.

**Impact:**
- All affected SSH host keys trivially crackable (precompute all 32K possible keys)
- All affected SSL certificates had predictable private keys
- All ECDSA signatures made with predictable nonces — private keys recoverable
- Estimated millions of systems affected worldwide

**Detection:** Generate all possible keys for each PID and check against public keys: `ssh-keyscan` + comparison against precomputed weak key list.

### Intel RDRAND Controversy

Intel's RDRAND instruction provides hardware random numbers from an on-die entropy source (thermal noise through a digital circuit) processed through AES-CBC-MAC conditioning.

**Concerns:**
1. **Opacity:** The hardware design is not publicly auditable. Users trust Intel's black-box implementation.
2. **Theoretical backdoor:** A malicious modification to the conditioning function could produce output that appears random but is predictable to the designer.
3. **Linus Torvalds' position:** Linux uses RDRAND as one of multiple entropy sources mixed into the kernel CSPRNG — never as the sole source. `/dev/urandom` output depends on RDRAND AND software entropy AND interrupt timing AND device timing.
4. **Recommendation:** Use RDRAND as one entropy source among many. Never rely on it exclusively.

### Dual_EC_DRBG — NSA Backdoor Analysis

Dual Elliptic Curve Deterministic Random Bit Generator, standardized in NIST SP 800-90A (2006):

**Design:** Uses two elliptic curve points P and Q to advance state and generate output:
```
state_new = (state_old * P).x
output = (state_new * Q).x  (truncated)
```

**The backdoor mechanism:**
If Q = d·P (the relationship d between P and Q is known), then:
```
output = (state_new * Q).x = (state_new * d * P).x
state_new can be recovered from output using d^(-1)
```

Anyone knowing d can predict all future outputs from a single observed output block.

**Evidence of deliberate backdoor:**
1. No justification given for the specific choice of P and Q
2. The standard provided no mechanism to generate new P,Q verifiably
3. Performance was 1000x slower than alternatives (discouraging replacement)
4. RSA Security (EMC) received $10M from NSA to make Dual_EC the default in BSAFE
5. Edward Snowden documents confirmed NSA "insert[ed] vulnerabilities into commercial encryption systems"

**Impact:** Any product using Dual_EC_DRBG with the standard constants had a state-level adversary backdoor. Affected: Juniper ScreenOS (additionally exploited by a third party who modified the Q constant), RSA BSAFE, and others.

### Android SecureRandom Bug — Bitcoin Wallet Theft (2013)

Android's Java `SecureRandom` implementation (Apache Harmony) on certain versions failed to properly seed the OpenSSL PRNG:

1. PRNG initialized at process start
2. Multiple processes could start with identical PRNG state (forked from Zygote)
3. Insufficient entropy mixed into the PRNG after fork

**Bitcoin impact:** ECDSA signatures require unique nonces (k values). With predictable PRNG output, multiple Bitcoin transactions from the same wallet used the same nonce. Attackers scanning the blockchain for nonce reuse extracted private keys and stole funds (estimated $5.7M across affected wallets).

**Detection:** Monitor blockchain for (r, s) signature pairs sharing the same r value (indicating nonce reuse). Automated tools extracted private keys within seconds of detection.

### VM Fork and Random State

When a virtual machine is cloned or restored from snapshot, the PRNG state is replicated. Both instances continue from identical state, producing identical "random" output.

**Attack scenarios:**
- VM snapshot restoration: resumed VM reuses TLS session tickets, generating identical random nonces
- Container image replication: multiple containers starting from the same image with identical /dev/urandom state
- Live migration: PRNG state potentially observable during migration

**Mitigations:**
- Reseed PRNG after any fork/clone event
- Include VM-unique data in entropy pool (VM UUID, current time, hardware serial)
- Use `RDSEED` instruction (not `RDRAND`) which provides raw entropy not recycled state
- Hypervisor-level entropy injection (virtio-rng, TPM-backed sources)

### PRNG State Recovery Attacks

If an attacker observes enough PRNG output, they may recover the internal state:

**Mersenne Twister (MT19937):** After observing 624 consecutive 32-bit outputs, the full internal state is recoverable. MT19937 is not cryptographically secure — it is used in many language default `random()` functions (Python's `random`, Ruby's `rand`, PHP's `mt_rand`). Never use for cryptographic purposes.

**Linear Congruential Generators:** Completely predictable from a few outputs — the modulus, multiplier, and increment are recoverable.

**Truncated PRNG output:** Even if only partial output is visible (e.g., fewer bits per call), lattice reduction techniques can recover internal state given sufficient observations.

### Testing Randomness — NIST SP 800-22 and Dieharder

**NIST SP 800-22** (Statistical Test Suite for Random Number Generators): 15 statistical tests including:
- Frequency (monobit) test
- Block frequency test
- Runs test
- Longest run of ones
- Binary matrix rank
- Discrete Fourier Transform
- Non-overlapping/overlapping template matching
- Maurer's universal statistical test
- Linear complexity
- Serial test
- Approximate entropy
- Cumulative sums
- Random excursions

```bash
# Running NIST STS
./assess 1000000  # Test sequence of 1M bits
# Select all tests, provide input file
```

**Dieharder** (extended test suite):
```bash
# Test a file of random bytes
dieharder -a -f random_bytes.bin -g 201

# Run specific test
dieharder -d 0 -f random_bytes.bin -g 201  # Diehard birthdays test
```

**PractRand:**
```bash
# Pipe PRNG output to PractRand
./my_prng | PractRand stdin
# Reports failures at specific data sizes
```

**Important caveat:** Passing statistical tests does NOT prove cryptographic security. A compromised PRNG (Dual_EC_DRBG) can pass all statistical tests while being completely predictable to the adversary. Statistical tests detect bias and patterns but cannot detect trapdoors.

---

## 9. Post-Quantum Cryptography

### Quantum Threat to Current Cryptography

**Shor's Algorithm:**
A quantum algorithm that factors integers and computes discrete logarithms in polynomial time on a quantum computer. Implications:

| System | Classical Security | Quantum Threat |
|---|---|---|
| RSA-2048 | ~112 bits | **Broken** — polynomial time factoring |
| RSA-4096 | ~140 bits | **Broken** — polynomial time factoring |
| ECDSA P-256 | ~128 bits | **Broken** — ECDLP in polynomial time |
| DH-2048 | ~112 bits | **Broken** — DLP in polynomial time |
| X25519 | ~128 bits | **Broken** — ECDLP in polynomial time |

Required quantum resources (estimated): ~4,000 logical qubits and ~10^10 T-gates for RSA-2048 with optimistic assumptions. Current (2025) quantum computers: ~1,000+ physical qubits with high error rates. Logical qubit overhead: ~1000-10,000 physical qubits per logical qubit with current error correction. Timeline estimates vary: 5-20+ years for cryptanalytically relevant quantum computers.

**Grover's Algorithm:**
A quantum search algorithm providing quadratic speedup for unstructured search. Impact on symmetric crypto:

| System | Classical Security | Quantum Security (post-Grover) |
|---|---|---|
| AES-128 | 128 bits | ~64 bits (insufficient) |
| AES-256 | 256 bits | ~128 bits (sufficient) |
| SHA-256 (preimage) | 256 bits | ~128 bits (sufficient) |
| SHA-256 (collision) | 128 bits | ~85 bits (marginal) |

**Practical Grover caveats:** The quadratic speedup requires sequential quantum iterations (no parallelism benefit), massive quantum memory (QRAM), and long coherence times. Some analyses suggest Grover's practical impact is less severe than the naive halving model implies.

**Recommendation:** Double symmetric key sizes (AES-256) for post-quantum resilience. All asymmetric crypto must be replaced.

### NIST PQC Standards (2024)

NIST selected and standardized the following post-quantum algorithms:

**ML-KEM (Module-Lattice-Based Key-Encapsulation Mechanism) — FIPS 203:**
Based on the CRYSTALS-Kyber submission. Security assumption: Module Learning With Errors (MLWE).
- ML-KEM-512: ~AES-128 equivalent security (category 1)
- ML-KEM-768: ~AES-192 equivalent security (category 3)
- ML-KEM-1024: ~AES-256 equivalent security (category 5)

Key sizes: Public key ~800-1568 bytes, ciphertext ~768-1568 bytes. Performance: Faster than RSA-2048 for key generation and encapsulation on most platforms.

**ML-DSA (Module-Lattice-Based Digital Signature Algorithm) — FIPS 204:**
Based on CRYSTALS-Dilithium. Security assumption: MLWE and Module Short Integer Solution (MSIS).
- ML-DSA-44: Category 2 security
- ML-DSA-65: Category 3 security
- ML-DSA-87: Category 5 security

Signature sizes: ~2420-4627 bytes. Public key: ~1312-2592 bytes. Performance: Fast signing and verification.

**SLH-DSA (Stateless Hash-Based Digital Signature Algorithm) — FIPS 205:**
Based on SPHINCS+. Security assumption: Only hash function security (most conservative — survives even if lattice problems are broken by new mathematical advances).
- Larger signatures (~7-50 KB) but minimal assumptions
- Suitable as a conservative backup to lattice-based schemes

### Hybrid Approaches

Hybrid key exchange combines a classical algorithm (X25519) with a post-quantum algorithm (ML-KEM-768). The combined shared secret requires breaking both to compromise:

```
shared_secret = KDF(X25519_shared || ML-KEM_shared)
```

**Deployed implementations:**
- Chrome/BoringSSL: X25519+ML-KEM-768 (previously X25519+Kyber768)
- Signal Protocol: X25519+ML-KEM-768 for initial key agreement (PQXDH)
- WireGuard: Proposals for hybrid handshake
- AWS KMS: Hybrid TLS with ML-KEM

**Rationale:** If the PQC algorithm has an unknown weakness (lattice problems broken), the classical component maintains security. If a quantum computer arrives, the PQC component maintains security.

### Migration Timeline and Planning

**NIST recommended timeline:**
- 2024-2030: Begin transition, deploy hybrid modes
- 2030-2035: Deprecate non-quantum-resistant algorithms for most uses
- 2035+: Mandate PQC for all government applications

**Migration considerations:**
1. Inventory all cryptographic systems (certificates, VPNs, stored data)
2. Identify systems with long-term confidentiality requirements (25+ year secrets are already at risk from "harvest now, decrypt later")
3. Deploy hybrid modes where possible (TLS, VPN, messaging)
4. Update root of trust infrastructure (CA certificates, code signing)
5. Test PQC performance on resource-constrained devices (IoT, embedded)
6. Update protocols and formats for larger keys/signatures/ciphertexts

### Crypto-Agility

Crypto-agility is the ability to replace cryptographic algorithms without redesigning the system:

**Design principles:**
- Algorithm negotiation in all protocols (not hardcoded choices)
- Key/certificate format abstraction (support multiple algorithm families)
- Modular cryptographic backends (easily swap implementations)
- Version fields in data formats (enable future algorithm changes)
- Inventory and lifecycle tracking for all cryptographic components

**Anti-patterns:**
- Hardcoded `algorithm: "RSA-2048"` with no negotiation
- Fixed-size fields that cannot accommodate larger PQC keys
- Protocol designs that assume specific signature/key sizes
- Certificates with 30-year validity and no rotation mechanism

### Harvest Now, Decrypt Later (HNDL)

State-level adversaries and well-resourced organizations are recording encrypted traffic today with the expectation of decrypting it when quantum computers become available.

**Threat model:**
- Data with long-term value (state secrets, medical records, financial data, intellectual property) encrypted today with RSA/ECDH key exchange
- Ciphertext stored indefinitely
- Quantum computer arrives in 10-20 years → all recorded sessions decrypted

**Currently at risk:**
- TLS sessions without forward secrecy (RSA key transport — static key allows bulk decryption)
- VPN tunnels using non-PFS DH groups
- Stored encrypted emails (PGP/S/MIME with RSA encryption)
- Encrypted backups with long-term retention

**Mitigation priority:** Deploy PQC hybrid key exchange NOW for forward-looking confidentiality. Even if the PQC implementation has bugs, the classical component prevents regression; the PQC component prevents future harvest attacks.

---

## 10. Lab: Cryptographic Attack Exercises

### Exercise 1: Padding Oracle Attack Against CBC

Implement a padding oracle attack that decrypts a CBC-encrypted message without the key.

```python
#!/usr/bin/env python3
"""
Padding Oracle Attack Implementation
Demonstrates full decryption of AES-CBC ciphertext using only a padding oracle.
"""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import os

BLOCK_SIZE = 16

class VulnerableServer:
    """Simulates a server that leaks padding validity."""
    
    def __init__(self):
        self.key = get_random_bytes(16)
    
    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt with AES-CBC and random IV."""
        iv = get_random_bytes(BLOCK_SIZE)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        padded = pad(plaintext, BLOCK_SIZE)
        ciphertext = cipher.encrypt(padded)
        return iv + ciphertext
    
    def decrypt_and_check_padding(self, data: bytes) -> bool:
        """
        THE ORACLE: Returns True if padding is valid, False otherwise.
        In a real attack, this might be:
        - HTTP 200 vs 500
        - Different error messages
        - Timing difference
        """
        iv = data[:BLOCK_SIZE]
        ciphertext = data[BLOCK_SIZE:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(ciphertext)
        try:
            unpad(plaintext, BLOCK_SIZE)
            return True
        except ValueError:
            return False


def attack_block(oracle, prev_block: bytes, target_block: bytes) -> bytes:
    """
    Decrypt a single block using the padding oracle.
    
    We manipulate prev_block to control what the XOR produces in the target
    plaintext position, checking when valid padding is achieved.
    """
    intermediate = bytearray(BLOCK_SIZE)  # D_K(target_block)
    decrypted = bytearray(BLOCK_SIZE)
    
    for byte_pos in range(BLOCK_SIZE - 1, -1, -1):
        padding_value = BLOCK_SIZE - byte_pos  # 1, 2, 3, ... 16
        
        # Set already-known bytes to produce desired padding
        crafted_prev = bytearray(BLOCK_SIZE)
        for i in range(byte_pos + 1, BLOCK_SIZE):
            crafted_prev[i] = intermediate[i] ^ padding_value
        
        # Try all 256 values for the target byte
        found = False
        for guess in range(256):
            crafted_prev[byte_pos] = guess
            
            # Submit to oracle: crafted_prev || target_block
            test_data = bytes(crafted_prev) + target_block
            
            if oracle(test_data):
                # Valid padding! We know:
                # D_K(target_block)[byte_pos] XOR guess = padding_value
                # Therefore: intermediate[byte_pos] = guess XOR padding_value
                
                # Handle false positive for padding_value=1
                # (e.g., last two bytes might form \x02\x02)
                if byte_pos == BLOCK_SIZE - 1 and padding_value == 1:
                    # Verify by modifying penultimate byte
                    verify = bytearray(crafted_prev)
                    verify[byte_pos - 1] ^= 0x01
                    if not oracle(bytes(verify) + target_block):
                        continue  # False positive
                
                intermediate[byte_pos] = guess ^ padding_value
                decrypted[byte_pos] = intermediate[byte_pos] ^ prev_block[byte_pos]
                found = True
                break
        
        if not found:
            raise RuntimeError(f"Failed to decrypt byte at position {byte_pos}")
    
    return bytes(decrypted)


def padding_oracle_attack(server: VulnerableServer, ciphertext: bytes) -> bytes:
    """Full padding oracle attack on a multi-block ciphertext."""
    iv = ciphertext[:BLOCK_SIZE]
    ct_blocks = [ciphertext[i:i+BLOCK_SIZE] 
                 for i in range(BLOCK_SIZE, len(ciphertext), BLOCK_SIZE)]
    
    oracle_calls = [0]
    
    def oracle(data: bytes) -> bool:
        oracle_calls[0] += 1
        return server.decrypt_and_check_padding(data)
    
    plaintext = b""
    all_blocks = [iv] + ct_blocks
    
    for i in range(1, len(all_blocks)):
        print(f"  Decrypting block {i}/{len(all_blocks)-1}...")
        block_plaintext = attack_block(oracle, all_blocks[i-1], all_blocks[i])
        plaintext += block_plaintext
    
    print(f"  Total oracle calls: {oracle_calls[0]}")
    
    # Remove PKCS#7 padding
    pad_len = plaintext[-1]
    if all(b == pad_len for b in plaintext[-pad_len:]):
        plaintext = plaintext[:-pad_len]
    
    return plaintext


def main():
    server = VulnerableServer()
    
    secret_message = b"Transfer $10000 to account 1337-4242-EVIL"
    print(f"Original message: {secret_message.decode()}")
    
    ciphertext = server.encrypt(secret_message)
    print(f"Ciphertext length: {len(ciphertext)} bytes")
    print(f"Blocks: {(len(ciphertext) - BLOCK_SIZE) // BLOCK_SIZE}")
    
    print("\nExecuting padding oracle attack...")
    recovered = padding_oracle_attack(server, ciphertext)
    print(f"\nRecovered plaintext: {recovered.decode()}")
    assert recovered == secret_message, "Attack failed!"
    print("Attack successful!")


if __name__ == "__main__":
    main()
```

### Exercise 2: ECB Block Manipulation

Demonstrate how ECB mode allows block substitution attacks.

```python
#!/usr/bin/env python3
"""
ECB Block Manipulation — Demonstrate block substitution attack.
Shows how an attacker can manipulate encrypted data without the key.
"""

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad

BLOCK_SIZE = 16

class ECBApplication:
    """Simulates an application using AES-ECB (vulnerable)."""
    
    def __init__(self):
        self.key = get_random_bytes(16)
    
    def create_token(self, username: str, role: str) -> bytes:
        """Create an encrypted role token."""
        # Fixed-format: "user=<16 bytes>role=<16 bytes>"
        data = f"user={username:<11}|role={role:<11}|".encode()
        cipher = AES.new(self.key, AES.MODE_ECB)
        return cipher.encrypt(pad(data, BLOCK_SIZE))
    
    def verify_token(self, token: bytes) -> dict:
        """Decrypt and parse a role token."""
        cipher = AES.new(self.key, AES.MODE_ECB)
        plaintext = cipher.decrypt(token)
        # Remove padding
        pad_len = plaintext[-1]
        plaintext = plaintext[:-pad_len]
        
        result = {}
        parts = plaintext.decode(errors='replace').split('|')
        for part in parts:
            if '=' in part:
                k, v = part.split('=', 1)
                result[k] = v.strip()
        return result


def demonstrate_ecb_substitution():
    app = ECBApplication()
    
    # Step 1: Get a legitimate user token
    user_token = app.create_token("alice", "viewer")
    print(f"Alice's token (viewer): {user_token.hex()}")
    print(f"Parsed: {app.verify_token(user_token)}")
    
    # Step 2: Get a token where "admin" appears in a known block position
    # Craft input so "role=admin      |" aligns to a block boundary
    # "user=XXXXXXXXXXX|" = 16 bytes (one full block)
    # "role=admin      |" = 16 bytes (second block)
    admin_token = app.create_token("XXXXXXXXXXX", "admin")
    print(f"\nCrafted admin token: {admin_token.hex()}")
    print(f"Parsed: {app.verify_token(admin_token)}")
    
    # Step 3: Block substitution attack
    # Take block 2 (role=admin) from admin_token
    # Replace block 2 in alice's token
    blocks_alice = [user_token[i:i+BLOCK_SIZE] for i in range(0, len(user_token), BLOCK_SIZE)]
    blocks_admin = [admin_token[i:i+BLOCK_SIZE] for i in range(0, len(admin_token), BLOCK_SIZE)]
    
    # Substitute the role block
    forged_token = blocks_alice[0] + blocks_admin[1] + blocks_alice[2]
    
    print(f"\nForged token: {forged_token.hex()}")
    print(f"Parsed: {app.verify_token(forged_token)}")
    print("\n[*] Alice is now admin without knowing the key!")


def demonstrate_ecb_pattern_leak():
    """Show how ECB leaks patterns in structured data."""
    key = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_ECB)
    
    # Encrypt repeated data
    data = b"AAAAAAAAAAAAAAAA" * 4  # 4 identical blocks
    ct = cipher.encrypt(data)
    
    blocks = [ct[i:i+BLOCK_SIZE].hex() for i in range(0, len(ct), BLOCK_SIZE)]
    print("\nECB Pattern Leak Demonstration:")
    print(f"  Plaintext: 4 identical 16-byte blocks")
    print(f"  Block 1: {blocks[0]}")
    print(f"  Block 2: {blocks[1]}")
    print(f"  Block 3: {blocks[2]}")
    print(f"  Block 4: {blocks[3]}")
    print(f"  All identical: {len(set(blocks)) == 1}")


if __name__ == "__main__":
    demonstrate_ecb_substitution()
    demonstrate_ecb_pattern_leak()
```

### Exercise 3: Password Hash Cracking with Hashcat

```bash
#!/bin/bash
# Password Hash Cracking Laboratory
# Demonstrates hashcat against various algorithms

# === Setup: Generate test hashes ===

# NTLM (Windows passwords) - raw MD4 of UTF-16LE password
echo -n "Password123!" | iconv -f UTF-8 -t UTF-16LE | openssl dgst -md4 | \
    awk '{print $NF}' > ntlm_hashes.txt

# SHA-256 with salt (Linux sha256crypt format)
# Format: $5$rounds=5000$salt$hash
openssl passwd -5 -salt "testsalt" "Summer2024!" >> sha_hashes.txt

# bcrypt hash
python3 -c "
import bcrypt
passwords = ['Welcome1!', 'Company2024', 'P@ssw0rd!', 'Qwerty123!']
for p in passwords:
    h = bcrypt.hashpw(p.encode(), bcrypt.gensalt(rounds=10))
    print(h.decode())
" > bcrypt_hashes.txt

# === Hashcat Attack Examples ===

# 1. NTLM — Dictionary + rules (mode 1000)
hashcat -m 1000 ntlm_hashes.txt \
    /usr/share/wordlists/rockyou.txt \
    -r /usr/share/hashcat/rules/best64.rule \
    --force -O

# 2. SHA-256 crypt — Targeted mask attack (mode 7400)
# Pattern: Capitalword + 4 digits + special
hashcat -m 7400 sha_hashes.txt \
    -a 3 \
    -1 '?u' -2 '?l' -3 '?d' -4 '!@#$%' \
    '?1?2?2?2?2?2?2?3?3?3?3?4' \
    --force

# 3. bcrypt — Dictionary attack (mode 3200)
# bcrypt is slow (~70 KH/s on RTX 4090), so targeted approach matters
hashcat -m 3200 bcrypt_hashes.txt \
    /usr/share/wordlists/rockyou.txt \
    --force

# 4. Combinator + rule: word1 + word2 + mutations
hashcat -m 1000 ntlm_hashes.txt \
    -a 1 \
    /usr/share/wordlists/english_words.txt \
    /usr/share/wordlists/english_words.txt \
    -j '$1' -k '$!'  \
    --force

# 5. Mask attack with custom charsets
# ?1 = custom (uppercase+digits), ?l = lowercase
hashcat -m 1000 ntlm_hashes.txt \
    -a 3 \
    -1 '?u?d' \
    '?1?l?l?l?l?l?d?d?d?s' \
    --force

# === Performance Benchmarks ===
hashcat -b --force  # Benchmark all algorithms

# === Status Checking ===
# While running: press 's' for status, 'q' to quit
# hashcat --session=crack1 --restore  # Resume interrupted session

# === Output Analysis ===
# Show cracked passwords
hashcat -m 1000 ntlm_hashes.txt --show
hashcat -m 3200 bcrypt_hashes.txt --show

# Output format: hash:password
# For reporting:
hashcat -m 1000 ntlm_hashes.txt --show --outfile-format=2
# Format 2 = plain only
```

### Exercise 4: ECDSA Nonce Reuse Exploitation

```python
#!/usr/bin/env python3
"""
ECDSA Nonce Reuse Attack
Demonstrates private key recovery when the same nonce k is used for two signatures.
This is the exact vulnerability class that broke PS3 code signing (2010).
"""

from Crypto.PublicKey import ECC
from Crypto.Hash import SHA256
import hashlib

def ecdsa_sign_with_nonce(private_key, message: bytes, k: int):
    """
    Sign with a specified nonce (simulating the vulnerability).
    Normal ECDSA should use a random k each time.
    """
    curve = private_key._curve
    n = int(curve.order)
    d = int(private_key.d)
    
    # Compute r = (k*G).x mod n
    G = curve.G
    point = k * G
    r = int(point.x) % n
    
    # Compute s = k^(-1) * (hash + r*d) mod n
    h = int.from_bytes(SHA256.new(message).digest(), 'big') % n
    k_inv = pow(k, -1, n)
    s = (k_inv * (h + r * d)) % n
    
    return (r, s, h)


def recover_private_key_from_nonce_reuse(r, s1, s2, h1, h2, n):
    """
    Given two signatures with the same nonce:
    s1 = k^-1 * (h1 + r*d) mod n
    s2 = k^-1 * (h2 + r*d) mod n
    
    s1 - s2 = k^-1 * (h1 - h2) mod n
    k = (h1 - h2) * (s1 - s2)^-1 mod n
    d = (s1*k - h1) * r^-1 mod n
    """
    # Recover k
    ds = (s1 - s2) % n
    dh = (h1 - h2) % n
    k = (dh * pow(ds, -1, n)) % n
    
    # Recover private key d
    r_inv = pow(r, -1, n)
    d = ((s1 * k - h1) * r_inv) % n
    
    return k, d


def main():
    # Generate a key pair
    key = ECC.generate(curve='P-256')
    n = int(key._curve.order)
    private_key_actual = int(key.d)
    
    print(f"Actual private key: {private_key_actual}")
    print(f"Public key X: {int(key.pointQ.x)}")
    
    # VULNERABILITY: Reusing the same nonce for two messages
    vulnerable_nonce = 0xDEADBEEF1337CAFE4242424242424242  # Fixed nonce (BAD!)
    # Clamp to valid range
    vulnerable_nonce = vulnerable_nonce % n
    if vulnerable_nonce == 0:
        vulnerable_nonce = 1
    
    # Sign two different messages with the SAME nonce
    msg1 = b"Transaction: Send 1 BTC to Alice"
    msg2 = b"Transaction: Send 2 BTC to Bob"
    
    r1, s1, h1 = ecdsa_sign_with_nonce(key, msg1, vulnerable_nonce)
    r2, s2, h2 = ecdsa_sign_with_nonce(key, msg2, vulnerable_nonce)
    
    print(f"\nSignature 1: r={r1}, s={s1}")
    print(f"Signature 2: r={r2}, s={s2}")
    print(f"Same r value (nonce reuse indicator): {r1 == r2}")
    
    # ATTACK: Recover private key from the two signatures
    k_recovered, d_recovered = recover_private_key_from_nonce_reuse(
        r1, s1, s2, h1, h2, n
    )
    
    print(f"\nRecovered nonce k: {k_recovered}")
    print(f"Actual nonce k:    {vulnerable_nonce}")
    print(f"Nonce recovery:    {'SUCCESS' if k_recovered == vulnerable_nonce else 'FAILED'}")
    
    print(f"\nRecovered private key: {d_recovered}")
    print(f"Actual private key:    {private_key_actual}")
    print(f"Key recovery:          {'SUCCESS' if d_recovered == private_key_actual else 'FAILED'}")
    
    if d_recovered == private_key_actual:
        print("\n[CRITICAL] Private key fully compromised from nonce reuse!")
        print("  Attacker can now sign arbitrary messages as the victim.")
        print("  This is exactly how the PS3 signing key was extracted in 2010.")


if __name__ == "__main__":
    main()
```

### Exercise 5: Detecting Timing Vulnerabilities

```python
#!/usr/bin/env python3
"""
Timing Attack Detection Lab
Demonstrates measurable timing differences in insecure comparison functions
and implements a constant-time alternative.
"""

import time
import statistics
import os
import hmac
import hashlib

SECRET_TOKEN = b"s3cr3t_api_t0ken_value_2024"


def insecure_compare(a: bytes, b: bytes) -> bool:
    """VULNERABLE: Early-exit comparison leaks match length."""
    if len(a) != len(b):
        return False
    for i in range(len(a)):
        if a[i] != b[i]:
            return False  # Returns as soon as mismatch found
    return True


def constant_time_compare(a: bytes, b: bytes) -> bool:
    """SECURE: Processes all bytes regardless of match position."""
    if len(a) != len(b):
        # Length check still leaks length info — acceptable for fixed-size tokens
        # For variable-length: hash both first
        return False
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y
    return result == 0


def hmac_compare(a: bytes, b: bytes) -> bool:
    """SECURE: Python's hmac.compare_digest (constant-time, C implementation)."""
    return hmac.compare_digest(a, b)


def measure_timing(compare_func, secret: bytes, guess: bytes, iterations=10000):
    """Measure average comparison time."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        compare_func(secret, guess)
        end = time.perf_counter_ns()
        times.append(end - start)
    return statistics.median(times)


def timing_attack_demonstration():
    """Show measurable timing difference in insecure comparison."""
    print("=== Timing Attack Detection Lab ===\n")
    
    token = SECRET_TOKEN
    token_len = len(token)
    
    # Test with progressively more correct prefix bytes
    print("Insecure comparison timing (median nanoseconds):")
    print("-" * 60)
    
    for correct_bytes in range(0, min(token_len, 12), 2):
        # Create a guess with 'correct_bytes' matching prefix
        guess = token[:correct_bytes] + b'\x00' * (token_len - correct_bytes)
        t = measure_timing(insecure_compare, token, guess, iterations=50000)
        bar = '#' * int(t / 10)
        print(f"  {correct_bytes:2d} correct bytes: {t:8.0f} ns  {bar}")
    
    print(f"\n  Full match:      ", end="")
    t = measure_timing(insecure_compare, token, token, iterations=50000)
    print(f"{t:8.0f} ns")
    
    # Constant-time comparison should show uniform timing
    print("\n\nConstant-time comparison timing (median nanoseconds):")
    print("-" * 60)
    
    for correct_bytes in range(0, min(token_len, 12), 2):
        guess = token[:correct_bytes] + b'\x00' * (token_len - correct_bytes)
        t = measure_timing(constant_time_compare, token, guess, iterations=50000)
        bar = '#' * int(t / 10)
        print(f"  {correct_bytes:2d} correct bytes: {t:8.0f} ns  {bar}")
    
    print(f"\n  Full match:      ", end="")
    t = measure_timing(constant_time_compare, token, token, iterations=50000)
    print(f"{t:8.0f} ns")
    
    print("\n\n[Analysis]")
    print("  Insecure: timing increases linearly with correct prefix length")
    print("  Constant-time: timing remains uniform regardless of input")
    print("  An attacker can recover the token one byte at a time using the")
    print("  insecure comparison, needing only 256 * len(token) attempts.")


def byte_by_byte_timing_attack():
    """Simulate a full timing attack recovering a token byte-by-byte."""
    print("\n\n=== Byte-by-Byte Token Recovery Simulation ===\n")
    
    target = SECRET_TOKEN
    recovered = bytearray(len(target))
    
    for pos in range(min(len(target), 8)):  # Demo first 8 bytes
        best_time = 0
        best_byte = 0
        
        for guess_byte in range(256):
            recovered[pos] = guess_byte
            guess = bytes(recovered)
            t = measure_timing(insecure_compare, target, guess, iterations=5000)
            
            if t > best_time:
                best_time = t
                best_byte = guess_byte
        
        recovered[pos] = best_byte
        print(f"  Position {pos}: recovered 0x{best_byte:02x} "
              f"('{chr(best_byte) if 32 <= best_byte < 127 else '?'}') "
              f"expected 0x{target[pos]:02x} "
              f"({'CORRECT' if best_byte == target[pos] else 'WRONG'})")
    
    print(f"\n  Recovered: {bytes(recovered[:8])}")
    print(f"  Expected:  {target[:8]}")


if __name__ == "__main__":
    timing_attack_demonstration()
    byte_by_byte_timing_attack()
```

### Exercise 6: TLS Configuration Testing with testssl.sh

```bash
#!/bin/bash
# TLS Configuration Security Audit using testssl.sh
# Tests a server for known vulnerabilities and misconfigurations

TARGET="${1:-example.com}"

echo "=== TLS Security Audit: $TARGET ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# --- Full vulnerability scan ---
testssl.sh --severity HIGH \
    --vulnerable \
    --headers \
    --protocols \
    --ciphers \
    --server-preference \
    --server-defaults \
    --fs \
    --rc4 \
    --sweet32 \
    --freak \
    --drown \
    --logjam \
    --beast \
    --lucky13 \
    --poodle \
    --robot \
    --breach \
    --crime \
    --heartbleed \
    --ccs-injection \
    --ticketbleed \
    --renegotiation \
    "$TARGET" 2>&1 | tee "tls_audit_${TARGET}_$(date +%Y%m%d).txt"

# --- Specific checks with analysis ---

echo ""
echo "=== Protocol Support Analysis ==="
echo ""

# Check specific protocol versions
testssl.sh --protocols "$TARGET" 2>&1 | grep -E "(SSLv2|SSLv3|TLS 1|TLS 1.1|TLS 1.2|TLS 1.3)"

echo ""
echo "=== Cipher Suite Analysis ==="
echo ""

# List all supported ciphers sorted by strength
testssl.sh --cipher-per-proto "$TARGET" 2>&1

echo ""
echo "=== Certificate Chain Analysis ==="
echo ""

# Detailed certificate information
testssl.sh --server-defaults "$TARGET" 2>&1 | \
    grep -E "(Signature Algorithm|Key Size|Serial|Issuer|Subject|Valid|OCSP|CT)"

echo ""
echo "=== Forward Secrecy Assessment ==="
echo ""

testssl.sh --fs "$TARGET" 2>&1

# --- OpenSSL direct testing ---

echo ""
echo "=== OpenSSL Direct Verification ==="
echo ""

# Test TLS 1.3 support
echo | openssl s_client -connect "$TARGET:443" \
    -tls1_3 -brief 2>&1 | head -5

# Check certificate details
echo | openssl s_client -connect "$TARGET:443" 2>/dev/null | \
    openssl x509 -noout -text -certopt no_sigdump,no_pubkey | \
    grep -E "(Issuer|Subject|Not Before|Not After|Signature Algorithm|Public Key Algorithm)"

# Check for weak DH parameters
echo | openssl s_client -connect "$TARGET:443" \
    -cipher 'DHE' 2>/dev/null | grep -i "server temp key"

# Check HSTS header
curl -sI "https://$TARGET" | grep -i "strict-transport-security"

echo ""
echo "=== Interpretation Guide ==="
echo ""
echo "CRITICAL findings (immediate action required):"
echo "  - SSLv2/SSLv3 enabled → disable immediately"
echo "  - Heartbleed vulnerable → patch OpenSSL"
echo "  - DROWN vulnerable → disable SSLv2 on all servers sharing the cert"
echo "  - ROBOT vulnerable → disable RSA key exchange"
echo "  - RC4 enabled → remove from cipher list"
echo ""
echo "HIGH findings (fix within 48 hours):"
echo "  - TLS 1.0/1.1 enabled → disable (deprecated)"
echo "  - BEAST/POODLE vulnerable → disable affected ciphers"
echo "  - No forward secrecy → prefer ECDHE ciphersuites"
echo "  - Weak DH parameters (<2048 bit) → use 2048+ or switch to ECDHE"
echo ""
echo "MEDIUM findings (fix within 30 days):"
echo "  - Missing HSTS header → add with includeSubDomains"
echo "  - No OCSP stapling → enable for performance and privacy"
echo "  - Certificate transparency absent → use CT-enabled CA"
echo "  - Sweet32 exposure → disable 3DES"
```

### Exercise 7: Constant-Time Comparison Implementation

```python
#!/usr/bin/env python3
"""
Implementing Constant-Time Cryptographic Operations
Critical for avoiding timing side channels in authentication and MAC verification.
"""

import hmac
import hashlib
import time
import os
from typing import Union


def constant_time_bytes_eq(a: bytes, b: bytes) -> bool:
    """
    Constant-time byte string comparison.
    
    Properties:
    - Execution time depends only on length, not on content
    - No early exit regardless of mismatch position
    - Uses XOR accumulator (no branch on intermediate values)
    
    Note: Length comparison still leaks len(a) != len(b).
    For variable-length secrets, hash both inputs first.
    """
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y
    
    return result == 0


def constant_time_select(condition: int, a: int, b: int) -> int:
    """
    Constant-time conditional selection: returns a if condition else b.
    condition must be 0 or 1.
    
    mask = -condition  (all 1s if condition=1, all 0s if condition=0)
    result = (a & mask) | (b & ~mask)
    """
    mask = -condition  # 0xFFFFFFFF if condition=1, 0x00000000 if condition=0
    return (a & mask) | (b & ~mask)


def constant_time_lookup(table: list, index: int) -> int:
    """
    Constant-time table lookup — accesses ALL entries to prevent cache timing.
    Prevents cache-based side channel attacks on table lookups (e.g., AES T-tables).
    """
    result = 0
    for i in range(len(table)):
        # Create mask: all 1s if i == index, all 0s otherwise
        # (i ^ index) == 0 only when i == index
        # Avoid branch: use arithmetic to create mask
        eq = ((i ^ index) - 1) >> 63  # -1 >> 63 = 1 (MSB of -1 shifted), 0 >> 63 = 0
        # For Python's arbitrary precision, constrain to a fixed bit width
        mask = -(int(i == index))  # Python-specific, but demonstrates the concept
        result |= (table[i] & mask)
    return result


def secure_mac_verify(key: bytes, message: bytes, received_mac: bytes) -> bool:
    """
    Secure MAC verification — constant-time and correct.
    
    Pitfalls avoided:
    1. Early-exit comparison (timing oracle)
    2. Comparing truncated MACs (reduced security)
    3. Computing MAC with wrong algorithm
    """
    computed_mac = hmac.new(key, message, hashlib.sha256).digest()
    return hmac.compare_digest(computed_mac, received_mac)


def constant_time_padding_check(data: bytes, block_size: int = 16) -> tuple:
    """
    Constant-time PKCS#7 padding validation.
    
    Returns (is_valid, unpadded_length) without timing leakage.
    Processes all bytes regardless of padding value.
    """
    if len(data) == 0 or len(data) % block_size != 0:
        return (False, 0)
    
    # Last byte is the padding length
    pad_len = data[-1]
    
    # Valid padding: 1 <= pad_len <= block_size
    # All last pad_len bytes must equal pad_len
    
    # Check pad_len is in valid range (constant-time)
    valid = 1
    # pad_len must be >= 1
    valid &= int(pad_len >= 1)
    # pad_len must be <= block_size
    valid &= int(pad_len <= block_size)
    # pad_len must be <= len(data)
    valid &= int(pad_len <= len(data))
    
    # Check all padding bytes (process ALL bytes to avoid timing leak)
    for i in range(len(data)):
        # Is this byte in the padding region?
        in_padding = int(i >= (len(data) - pad_len))
        # Does it have the correct value?
        correct_value = int(data[i] == pad_len)
        # If in padding and incorrect, mark invalid
        # valid &= (not in_padding) or correct_value
        valid &= (1 - in_padding) | correct_value
    
    unpadded_length = len(data) - pad_len if valid else 0
    return (bool(valid), unpadded_length)


# --- Verification ---

def verify_implementations():
    """Test the constant-time implementations."""
    print("=== Constant-Time Implementation Verification ===\n")
    
    # Test bytes_eq
    assert constant_time_bytes_eq(b"hello", b"hello") == True
    assert constant_time_bytes_eq(b"hello", b"world") == False
    assert constant_time_bytes_eq(b"abc", b"abcd") == False
    print("[PASS] constant_time_bytes_eq")
    
    # Test select
    assert constant_time_select(1, 42, 99) == 42
    assert constant_time_select(0, 42, 99) == 99
    print("[PASS] constant_time_select")
    
    # Test padding check
    valid_padded = b"Hello, World!\x03\x03\x03"
    invalid_padded = b"Hello, World!\x03\x03\x04"
    
    assert constant_time_padding_check(valid_padded) == (True, 13)
    assert constant_time_padding_check(invalid_padded)[0] == False
    print("[PASS] constant_time_padding_check")
    
    # Test MAC verify
    key = os.urandom(32)
    msg = b"test message"
    mac = hmac.new(key, msg, hashlib.sha256).digest()
    assert secure_mac_verify(key, msg, mac) == True
    assert secure_mac_verify(key, msg, b'\x00' * 32) == False
    print("[PASS] secure_mac_verify")
    
    print("\nAll implementations verified.")


if __name__ == "__main__":
    verify_implementations()
```

### Exercise 8: RSA Key Analysis with OpenSSL and SageMath

```bash
#!/bin/bash
# RSA Key Analysis and Weakness Detection

# === Generate test RSA keys ===
openssl genrsa -out test_2048.pem 2048 2>/dev/null
openssl genrsa -out test_4096.pem 4096 2>/dev/null

# === Extract key parameters ===
echo "=== RSA Key Parameter Analysis ==="

# View key components
openssl rsa -in test_2048.pem -text -noout 2>/dev/null | \
    grep -E "(Private-Key|publicExponent|prime1|prime2)" | head -10

# Extract modulus for analysis
openssl rsa -in test_2048.pem -modulus -noout 2>/dev/null

# === Check for weak keys ===
echo ""
echo "=== Weak Key Checks ==="

# Check public exponent (should be 65537)
E=$(openssl rsa -in test_2048.pem -text -noout 2>/dev/null | \
    grep "publicExponent" | grep -oP '\d+')
echo "Public exponent: $E"
if [ "$E" -eq 3 ]; then
    echo "[CRITICAL] e=3 — vulnerable to cube root and broadcast attacks"
elif [ "$E" -lt 65537 ]; then
    echo "[WARNING] Small public exponent — potential vulnerability"
else
    echo "[OK] Standard public exponent (65537)"
fi

# Check key size
BITS=$(openssl rsa -in test_2048.pem -text -noout 2>/dev/null | \
    grep "Private-Key" | grep -oP '\d+')
echo "Key size: $BITS bits"
if [ "$BITS" -lt 2048 ]; then
    echo "[CRITICAL] Key size < 2048 bits — factoring is feasible"
elif [ "$BITS" -lt 3072 ]; then
    echo "[INFO] 2048 bits — acceptable until ~2030"
else
    echo "[OK] Key size >= 3072 bits"
fi

# === Check certificate for known weak key databases ===
# Using openssl to check the public key fingerprint against known-weak keys
openssl rsa -in test_2048.pem -pubout -outform DER 2>/dev/null | \
    sha256sum | awk '{print $1}'

# Cleanup
rm -f test_2048.pem test_4096.pem
```

**SageMath: RSA Small Public Exponent Attack**

```python
# SageMath script: RSA attacks via number theory
# Run with: sage rsa_attacks.sage

# === Fermat's Factoring (close primes) ===
def fermat_factor(n):
    """
    Factor n when p and q are close together.
    If |p - q| < n^(1/4), factoring is trivial.
    """
    a = isqrt(n)
    if a * a == n:
        return a, a
    
    a += 1
    b2 = a*a - n
    
    iterations = 0
    while not is_square(b2):
        a += 1
        b2 = a*a - n
        iterations += 1
        if iterations > 1000000:
            return None, None
    
    b = isqrt(b2)
    p = a + b
    q = a - b
    return p, q


# === Wiener's Attack (small private exponent) ===
def wiener_attack(e, n):
    """
    Recover d when d < n^(1/4) / 3.
    Uses continued fraction expansion of e/n.
    """
    cf = continued_fraction(e / n)
    convergents = cf.convergents()
    
    for conv in convergents:
        k = conv.numerator()
        d = conv.denominator()
        
        if k == 0:
            continue
        
        # Check: phi = (e*d - 1) / k must be integer
        if (e * d - 1) % k != 0:
            continue
        
        phi = (e * d - 1) // k
        
        # Check: x^2 - (n - phi + 1)x + n = 0 must have integer roots
        # (these would be p and q)
        s = n - phi + 1
        discriminant = s*s - 4*n
        
        if discriminant >= 0:
            t = isqrt(discriminant)
            if t*t == discriminant:
                p = (s + t) // 2
                q = (s - t) // 2
                if p * q == n:
                    return d, p, q
    
    return None, None, None


# === Hastad's Broadcast Attack ===
def hastad_broadcast(ciphertexts, moduli, e=3):
    """
    Given e ciphertexts of the same message encrypted under
    different moduli with public exponent e, recover the message.
    Uses CRT to find m^e, then takes the e-th root.
    """
    # CRT to find m^e mod (n1*n2*...*ne)
    from sage.all import CRT_list, Integer
    
    me = CRT_list(ciphertexts, moduli)
    
    # Take integer e-th root
    m = Integer(me).nth_root(e)
    
    return m


# === Demo with small numbers ===
print("=== Fermat's Factoring Demo ===")
# Generate two close primes
p = next_prime(2^64)
q = next_prime(p + 1000)  # Close primes — vulnerable
n = p * q
print(f"n = {n}")
print(f"Actual: p = {p}, q = {q}")

p_found, q_found = fermat_factor(n)
print(f"Fermat:  p = {p_found}, q = {q_found}")
print(f"Correct: {p_found == p and q_found == q}")

print("\n=== Wiener's Attack Demo ===")
# Generate RSA with small d
p = random_prime(2^512)
q = random_prime(2^512)
n = p * q
phi = (p-1)*(q-1)
d = random_prime(isqrt(isqrt(n)) // 3)  # d < n^(1/4)/3
e = inverse_mod(d, phi)
print(f"n has {n.nbits()} bits")
print(f"Actual d: {d}")

d_found, p_found, q_found = wiener_attack(e, n)
if d_found:
    print(f"Recovered d: {d_found}")
    print(f"Correct: {d_found == d}")
else:
    print("Attack failed (d may be too large)")
```

### Exercise 9: Length Extension Attack Demonstration

```python
#!/usr/bin/env python3
"""
SHA-256 Length Extension Attack
Demonstrates why MAC = SHA256(secret || message) is insecure.
"""

import struct
import hashlib

def sha256_internal_state(hash_hex: str) -> tuple:
    """Extract SHA-256 internal state from a hash output."""
    h = bytes.fromhex(hash_hex)
    return struct.unpack('>8I', h)


def sha256_padding(msg_len: int) -> bytes:
    """Compute SHA-256 padding for a message of given length."""
    # Padding: 0x80 + zeros + 64-bit big-endian length
    bit_len = msg_len * 8
    # Pad to 56 mod 64 bytes (448 mod 512 bits)
    pad_len = (55 - msg_len) % 64 + 1
    padding = b'\x80' + b'\x00' * (pad_len - 1) + struct.pack('>Q', bit_len)
    return padding


def sha256_extend(original_hash: str, original_msg_len: int, 
                  extension: bytes) -> tuple:
    """
    Perform length extension: given SHA256(unknown_prefix || msg) and
    len(unknown_prefix || msg), compute SHA256(unknown_prefix || msg || pad || extension)
    without knowing unknown_prefix.
    
    Returns: (new_hash, forged_message_suffix)
    """
    # Recover internal state from the hash
    state = sha256_internal_state(original_hash)
    
    # The padding that was applied to the original message
    original_padding = sha256_padding(original_msg_len)
    
    # Total processed length (message + padding)
    processed_len = original_msg_len + len(original_padding)
    
    # Now we continue SHA-256 from the recovered state
    # We need a SHA-256 implementation that accepts an initial state
    # For demonstration, we'll use a pure-Python implementation or
    # simulate by prepending a dummy block
    
    # The forged message is: original_msg + original_padding + extension
    # The MAC is: SHA256(secret + original_msg + original_padding + extension)
    # We compute this without knowing 'secret'!
    
    # Using hlextend library concept (manual implementation):
    # Initialize SHA-256 with the recovered state and continue hashing
    
    # Simulated approach: create a message that, when hashed from scratch
    # with the secret prepended, produces the same intermediate state
    forged_suffix = original_padding + extension
    
    # The new hash = SHA256_continue(state, extension, total_processed_len)
    # This requires a modified SHA-256 — demonstrating the concept:
    
    # For verification, if we know the secret we can confirm:
    # SHA256(secret + original_msg + pad + extension) == extended_hash
    
    return state, forged_suffix


def demonstrate_length_extension():
    """
    Scenario: A server uses MAC = SHA256(secret || command) to authenticate commands.
    We have a valid MAC for "amount=100" and want to extend to "amount=100...&amount=999"
    """
    # Server's secret (we do NOT know this)
    secret = b"server_secret_k3y"
    
    # Original authenticated message
    original_msg = b"amount=100&to=alice"
    
    # MAC computed by server (we observe this)
    original_mac = hashlib.sha256(secret + original_msg).hexdigest()
    
    print("=== SHA-256 Length Extension Attack ===\n")
    print(f"Original message: {original_msg.decode()}")
    print(f"Original MAC:     {original_mac}")
    print(f"Secret length:    {len(secret)} bytes (known to attacker)")
    
    # Attacker wants to append this
    extension = b"&amount=99999&to=attacker"
    
    # Compute the extended message and new MAC
    total_original_len = len(secret) + len(original_msg)
    padding = sha256_padding(total_original_len)
    
    # The forged message (what the server will see after the secret)
    forged_msg = original_msg + padding + extension
    
    # Verify by computing the actual hash (simulating the attack result)
    # In a real attack, we'd use a SHA-256 implementation that accepts initial state
    actual_extended_hash = hashlib.sha256(secret + forged_msg).hexdigest()
    
    print(f"\nForged message:   {original_msg.decode()}[padding]{extension.decode()}")
    print(f"Extended MAC:     {actual_extended_hash}")
    
    # Verify the MAC is valid for the forged message
    verification = hashlib.sha256(secret + forged_msg).hexdigest()
    print(f"\nServer verifies:  {verification == actual_extended_hash}")
    print(f"\n[*] Attack succeeds — we computed a valid MAC for the extended")
    print(f"    message without knowing the secret key!")
    print(f"\n[*] Mitigation: Use HMAC-SHA256 instead of SHA256(secret||msg)")
    
    # Show HMAC is immune
    import hmac as hmac_mod
    hmac_mac = hmac_mod.new(secret, original_msg, hashlib.sha256).hexdigest()
    print(f"\n--- HMAC comparison ---")
    print(f"HMAC(secret, msg): {hmac_mac}")
    print(f"HMAC cannot be extended without the key (double-hash structure)")


if __name__ == "__main__":
    demonstrate_length_extension()
```

### Exercise 10: Comprehensive TLS Vulnerability Scanner Script

```python
#!/usr/bin/env python3
"""
TLS Vulnerability Assessment Framework
Checks for common cryptographic misconfigurations programmatically.
"""

import ssl
import socket
import subprocess
import json
from datetime import datetime, timezone


class TLSAuditor:
    """Automated TLS configuration auditor."""
    
    def __init__(self, host: str, port: int = 443):
        self.host = host
        self.port = port
        self.findings = []
    
    def check_protocol_support(self) -> dict:
        """Test which TLS/SSL versions are supported."""
        protocols = {
            'SSLv3': ssl.PROTOCOL_SSLv23,  # Will negotiate SSLv3 if allowed
            'TLS 1.0': None,
            'TLS 1.1': None,
            'TLS 1.2': None,
            'TLS 1.3': None,
        }
        
        results = {}
        
        # Test TLS 1.2
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.maximum_version = ssl.TLSVersion.TLSv1_2
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            
            with socket.create_connection((self.host, self.port), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=self.host) as ssock:
                    results['TLS 1.2'] = True
        except Exception:
            results['TLS 1.2'] = False
        
        # Test TLS 1.3
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.minimum_version = ssl.TLSVersion.TLSv1_3
            
            with socket.create_connection((self.host, self.port), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=self.host) as ssock:
                    results['TLS 1.3'] = True
        except Exception:
            results['TLS 1.3'] = False
        
        # Check for deprecated protocols via OpenSSL
        for proto in ['ssl3', 'tls1', 'tls1_1']:
            try:
                result = subprocess.run(
                    ['openssl', 's_client', '-connect', f'{self.host}:{self.port}',
                     f'-{proto}', '-brief'],
                    capture_output=True, text=True, timeout=10,
                    input=''
                )
                proto_name = {'ssl3': 'SSLv3', 'tls1': 'TLS 1.0', 
                             'tls1_1': 'TLS 1.1'}[proto]
                results[proto_name] = 'Protocol' in result.stdout
            except Exception:
                pass
        
        # Findings
        if results.get('SSLv3'):
            self.findings.append({
                'severity': 'CRITICAL',
                'issue': 'SSLv3 supported',
                'impact': 'POODLE attack possible',
                'remediation': 'Disable SSLv3 immediately'
            })
        
        if results.get('TLS 1.0') or results.get('TLS 1.1'):
            self.findings.append({
                'severity': 'HIGH',
                'issue': 'TLS 1.0/1.1 supported',
                'impact': 'Deprecated protocols with known weaknesses',
                'remediation': 'Disable TLS 1.0 and 1.1; require TLS 1.2+'
            })
        
        if not results.get('TLS 1.3'):
            self.findings.append({
                'severity': 'MEDIUM',
                'issue': 'TLS 1.3 not supported',
                'impact': 'Missing modern security improvements',
                'remediation': 'Enable TLS 1.3 support'
            })
        
        return results
    
    def check_certificate(self) -> dict:
        """Analyze server certificate for weaknesses."""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((self.host, self.port), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=self.host) as ssock:
                    cert = ssock.getpeercert(binary_form=True)
                    cert_info = ssock.getpeercert()
            
            # Parse with OpenSSL for details
            result = subprocess.run(
                ['openssl', 'x509', '-inform', 'DER', '-text', '-noout'],
                input=cert, capture_output=True, timeout=10
            )
            cert_text = result.stdout.decode()
            
            findings = {}
            
            # Check signature algorithm
            if 'sha1WithRSAEncryption' in cert_text:
                self.findings.append({
                    'severity': 'HIGH',
                    'issue': 'Certificate signed with SHA-1',
                    'impact': 'SHA-1 collisions are practical — certificate forgery possible',
                    'remediation': 'Reissue with SHA-256 or stronger'
                })
            
            if 'md5WithRSAEncryption' in cert_text:
                self.findings.append({
                    'severity': 'CRITICAL',
                    'issue': 'Certificate signed with MD5',
                    'impact': 'MD5 collisions trivial — certificate forgery easy',
                    'remediation': 'Reissue immediately with SHA-256'
                })
            
            # Check key size
            if 'RSA Public-Key: (1024 bit)' in cert_text:
                self.findings.append({
                    'severity': 'CRITICAL',
                    'issue': 'RSA-1024 key',
                    'impact': 'Factoring feasible with moderate resources',
                    'remediation': 'Reissue with RSA-2048 minimum (RSA-3072 preferred)'
                })
            
            return {'cert_text': cert_text[:500]}
            
        except Exception as e:
            return {'error': str(e)}
    
    def check_cipher_suites(self) -> list:
        """Identify weak cipher suites."""
        weak_ciphers = []
        
        # Test for specific weak ciphers via OpenSSL
        weak_tests = {
            'RC4': 'RC4',
            'DES-CBC3': '3DES',
            'NULL': 'NULL encryption',
            'EXPORT': 'Export-grade',
            'anon': 'Anonymous (no auth)',
        }
        
        for cipher_filter, description in weak_tests.items():
            try:
                result = subprocess.run(
                    ['openssl', 's_client', '-connect', f'{self.host}:{self.port}',
                     '-cipher', cipher_filter, '-brief'],
                    capture_output=True, text=True, timeout=10,
                    input=''
                )
                if 'Cipher is' in result.stdout and 'NONE' not in result.stdout:
                    weak_ciphers.append(cipher_filter)
                    self.findings.append({
                        'severity': 'HIGH' if cipher_filter != '3DES' else 'MEDIUM',
                        'issue': f'{description} cipher supported ({cipher_filter})',
                        'impact': f'Weak encryption — {description} is deprecated/broken',
                        'remediation': f'Remove {cipher_filter} from cipher suite list'
                    })
            except Exception:
                pass
        
        return weak_ciphers
    
    def generate_report(self) -> str:
        """Generate findings report."""
        report = []
        report.append(f"TLS Security Audit Report")
        report.append(f"Target: {self.host}:{self.port}")
        report.append(f"Date: {datetime.now(timezone.utc).isoformat()}")
        report.append(f"{'=' * 60}")
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        sorted_findings = sorted(self.findings, 
                                key=lambda x: severity_order.get(x['severity'], 99))
        
        for i, finding in enumerate(sorted_findings, 1):
            report.append(f"\n[{finding['severity']}] Finding #{i}: {finding['issue']}")
            report.append(f"  Impact: {finding['impact']}")
            report.append(f"  Remediation: {finding['remediation']}")
        
        if not self.findings:
            report.append("\nNo significant findings. Configuration appears sound.")
        
        return '\n'.join(report)


def main():
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "example.com"
    
    auditor = TLSAuditor(target)
    
    print(f"Scanning {target}...")
    auditor.check_protocol_support()
    auditor.check_certificate()
    auditor.check_cipher_suites()
    
    print(auditor.generate_report())


if __name__ == "__main__":
    main()
```

---

## References and Further Reading

### Foundational Papers

- Vaudenay, S. (2002). "Security Flaws Induced by CBC Padding" — Padding oracle attack formalization
- Bleichenbacher, D. (1998). "Chosen Ciphertext Attacks Against Protocols Based on RSA PKCS#1" — RSA padding oracle
- Kocher, P. (1996). "Timing Attacks on Implementations of DH, RSA, DSS, and Other Systems" — Timing side channels
- Bernstein, D.J. (2005). "Cache-timing attacks on AES" — Cache-based side channels
- Genkin, D. et al. (2014). "RSA Key Extraction via Low-Bandwidth Acoustic Cryptanalysis" — Acoustic attacks
- Adrian, D. et al. (2015). "Imperfect Forward Secrecy: How Diffie-Hellman Fails in Practice" — Logjam
- Stevens, M. et al. (2017). "The First Collision for Full SHA-1" — SHAttered
- Aviram, N. et al. (2016). "DROWN: Breaking TLS using SSLv2" — Cross-protocol attack

### Standards and Specifications

- NIST SP 800-38A: Recommendation for Block Cipher Modes of Operation
- NIST SP 800-56A Rev. 3: Recommendation for Pair-Wise Key-Establishment Schemes
- NIST SP 800-90A Rev. 1: Recommendation for Random Number Generation Using DRBGs
- NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard
- NIST FIPS 204: Module-Lattice-Based Digital Signature Standard
- RFC 8446: TLS 1.3
- RFC 8439: ChaCha20 and Poly1305 for IETF Protocols
- RFC 6979: Deterministic Usage of DSA and ECDSA

### Tools

- **hashcat**: GPU-accelerated password recovery — https://hashcat.net
- **John the Ripper**: CPU-based password cracker — https://www.openwall.com/john/
- **testssl.sh**: TLS/SSL testing — https://testssl.sh
- **PyCryptodome**: Python cryptographic library — https://pycryptodome.readthedocs.io
- **SageMath**: Mathematical software for number theory — https://www.sagemath.org
- **OpenSSL**: Cryptographic toolkit — https://www.openssl.org
- **PractRand**: PRNG testing suite — http://pracrand.sourceforge.net
- **Dieharder**: Random number test suite

---

## Appendix A: Quick Reference — Algorithm Security Status (2025)

| Algorithm | Use Case | Status | Recommendation |
|---|---|---|---|
| AES-128/256 | Symmetric encryption | Secure | Use with AEAD mode (GCM/CCM) |
| ChaCha20-Poly1305 | Symmetric AEAD | Secure | Preferred on non-AES-NI platforms |
| 3DES | Legacy symmetric | Deprecated | Remove; replace with AES |
| RC4 | Stream cipher | Broken | Prohibited (RFC 7465) |
| SHA-256/SHA-512 | Hashing | Secure | Standard choice |
| SHA-3 | Hashing | Secure | Preferred for new designs |
| SHA-1 | Hashing | Broken (collision) | Deprecate; accept only for HMAC legacy |
| MD5 | Hashing | Broken (collision) | Never use for security |
| RSA-2048+ (OAEP) | Encryption | Secure (classical) | Minimum 2048, prefer 3072 |
| RSA-2048+ (PSS) | Signatures | Secure (classical) | Prefer EdDSA for new systems |
| ECDSA P-256 | Signatures | Secure (classical) | Use RFC 6979 deterministic nonce |
| Ed25519 | Signatures | Secure (classical) | Preferred for new systems |
| X25519 | Key exchange | Secure (classical) | Preferred for ECDH |
| ML-KEM-768 | PQC key exchange | Secure (quantum) | Deploy in hybrid mode now |
| ML-DSA-65 | PQC signatures | Secure (quantum) | Begin evaluation |
| Argon2id | Password hashing | Secure | Best practice (memory-hard) |
| bcrypt | Password hashing | Acceptable | Good alternative where Argon2 unavailable |

## Appendix B: Common Hashcat Modes Reference

| Mode | Algorithm | Example |
|---|---|---|
| 0 | MD5 | `hashcat -m 0 hash.txt wordlist.txt` |
| 100 | SHA-1 | `hashcat -m 100 hash.txt wordlist.txt` |
| 1000 | NTLM | `hashcat -m 1000 hash.txt wordlist.txt` |
| 1400 | SHA-256 | `hashcat -m 1400 hash.txt wordlist.txt` |
| 1700 | SHA-512 | `hashcat -m 1700 hash.txt wordlist.txt` |
| 1800 | sha512crypt ($6$) | `hashcat -m 1800 hash.txt wordlist.txt` |
| 3200 | bcrypt | `hashcat -m 3200 hash.txt wordlist.txt` |
| 5600 | NetNTLMv2 | `hashcat -m 5600 hash.txt wordlist.txt` |
| 7400 | sha256crypt ($5$) | `hashcat -m 7400 hash.txt wordlist.txt` |
| 13100 | Kerberoast (TGS-REP) | `hashcat -m 13100 hash.txt wordlist.txt` |
| 18200 | AS-REP Roast | `hashcat -m 18200 hash.txt wordlist.txt` |
| 22000 | WPA-PBKDF2 (pmkid/hccapx) | `hashcat -m 22000 hash.txt wordlist.txt` |

## Appendix C: OpenSSL Command Reference for Crypto Analysis

```bash
# === Key Generation ===
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out rsa4096.pem
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out ec256.pem
openssl genpkey -algorithm ED25519 -out ed25519.pem

# === Encryption/Decryption ===
# AES-256-GCM
openssl enc -aes-256-gcm -in plain.txt -out cipher.bin -K $(openssl rand -hex 32) -iv $(openssl rand -hex 12)

# === Hash Operations ===
echo -n "data" | openssl dgst -sha256
echo -n "data" | openssl dgst -sha3-256

# === HMAC ===
echo -n "message" | openssl dgst -sha256 -hmac "secret_key"

# === RSA Operations ===
# Encrypt
openssl pkeyutl -encrypt -inkey pub.pem -pubin -in plain.txt -out cipher.bin -pkeyopt rsa_padding_mode:oaep
# Decrypt
openssl pkeyutl -decrypt -inkey priv.pem -in cipher.bin -out plain.txt -pkeyopt rsa_padding_mode:oaep
# Sign
openssl pkeyutl -sign -inkey priv.pem -in hash.bin -out sig.bin -pkeyopt rsa_padding_mode:pss
# Verify
openssl pkeyutl -verify -inkey pub.pem -pubin -in hash.bin -sigfile sig.bin -pkeyopt rsa_padding_mode:pss

# === Certificate Analysis ===
# View certificate details
openssl x509 -in cert.pem -text -noout
# Check certificate chain
openssl verify -CAfile ca.pem cert.pem
# Check OCSP status
openssl ocsp -issuer ca.pem -cert cert.pem -url http://ocsp.example.com

# === TLS Testing ===
# Connect and show negotiated parameters
openssl s_client -connect host:443 -tls1_3 -brief
# Show all certificates in chain
openssl s_client -connect host:443 -showcerts
# Test specific cipher
openssl s_client -connect host:443 -cipher 'ECDHE-RSA-AES256-GCM-SHA384'
# Check DH parameters
openssl s_client -connect host:443 -cipher 'DHE' 2>/dev/null | grep "Server Temp Key"

# === Random Number Generation ===
openssl rand -hex 32    # 256-bit random value
openssl rand -base64 24 # 192-bit random (32 base64 chars)

# === Key Derivation ===
# PBKDF2
openssl kdf -keylen 32 -kdfopt digest:SHA256 -kdfopt pass:password -kdfopt salt:$(openssl rand -hex 16) -kdfopt iter:600000 PBKDF2

# === ASN.1 Parsing (for analyzing crypto structures) ===
openssl asn1parse -in cert.pem
openssl asn1parse -in sig.bin -inform DER
```
