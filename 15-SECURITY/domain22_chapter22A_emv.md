---
corso: "Cybersecurity Masterclass"
fase: "Domain 22 — Financial Security"
modulo: "22.1"
titolo: "EMV Payment Security"
versione: "EMV 4.4 / ISO 7816 / PCI DSS 4.0.1"
livello: "Advanced"
prerequisiti:
  - "Domain 13 Chapter 13A — Applied Cryptography (RSA, 3DES, AES-CMAC, ECDSA)"
  - "Domain 17 — Physical Security (side-channel attacks, tamper resistance)"
  - "Working knowledge of ISO 7816 smart-card communication"
obiettivi:
  - "Parse a raw ATR byte sequence and determine supported protocols, IFSC, and speed-negotiation parameters"
  - "Trace a complete EMV transaction from SELECT through GENERATE AC, identifying every APDU, TLV structure, and cryptographic operation"
  - "Implement ARQC computation using 3DES-CBC-MAC (ISO 9797-1 Algorithm 3) given an Issuer Master Key and transaction data"
  - "Evaluate the security properties and limitations of SDA, DDA, and CDA, and recommend the appropriate ODA method for a given deployment"
  - "Construct and execute a contactless relay-attack lab scenario and demonstrate distance-bounding countermeasures"
tag: [emv, payment-security, smart-card, contactless, pci-dss, cryptogram, oda, relay-attack]
---

# Domain 22, Chapter 22A — EMV Payment Security

> **Learning objectives.** After completing this chapter, the student will be able to: (1) decode EMV ATR sequences and APDU exchanges at the byte level, including protocol negotiation and status-word interpretation; (2) walk through the full EMV transaction lifecycle — application selection, GPO, READ RECORD, ODA, CVM processing, and cryptogram generation — explaining the security rationale at each stage; (3) derive ICC session keys from issuer master keys and compute ARQC MACs programmatically; (4) compare SDA, DDA, and CDA certificate-recovery chains, articulate their threat models, and identify real-world bypass vulnerabilities; (5) analyze contactless relay, shimming, CVM-bypass, and pre-play attacks, mapping each to specific protocol weaknesses and defenses.

> **Scope.** EMV contact communication (T=0, T=1, ATR byte-level parsing). APDU command/response structure. Application selection (PSE, PPSE, AID, FCI parsing). The complete EMV transaction flow: GET PROCESSING OPTIONS (PDOL, AIP, AFL), READ RECORD (data elements, TLV encoding), offline data authentication (SDA, DDA, CDA — certificate recovery, RSA operations, signed data composition), GENERATE APPLICATION CRYPTOGRAM (ARQC/TC/AAC — key derivation, MAC computation, IAD structure), EXTERNAL AUTHENTICATE and Issuer Script processing. PIN verification (ISO 9564 Format 0/4, online/offline plaintext/enciphered, PIN try counter). CVM list processing (condition codes, fallback logic). Attacks: pre-play, contactless relay, mag-stripe fallback, shimming, CVM bypass, wedge device, EMV kernel vulnerabilities. EMV contactless (EMV mode, qVSDC, MSD contactless). EMV security evolution: 3DS 2.0, SRC, FIDO/WebAuthn SCA, PSD2, post-quantum payment cryptography. Detection and defense.

---

## 1. Contact interface protocols

### 1.1 Electrical interface

The EMV chip has eight contacts defined by ISO 7816-2. In practice, five are used for communication: C1 (VCC — 5V or 3V or 1.8V supply, negotiated via ATR), C2 (RST — reset line; the terminal pulses RST to initiate the ATR sequence), C3 (CLK — clock signal, typically 1–5 MHz; the clock rate can be adjusted upward after ATR negotiation via the Fi/Di parameters), C5 (GND — ground), and C7 (I/O — the bidirectional serial data line). C6 (VPP — programming voltage) is unused in modern cards. C4 and C8 are reserved for future use (C4 is used by some USB-ICC interfaces).

The I/O line carries serial data at a rate determined by the clock divider ratio. The default rate is CLK/372 (the "etu" — elementary time unit — is 372 clock cycles per bit). During ATR, the card communicates at this default rate; after ATR, the terminal and card may negotiate a faster rate using the Fi (clock rate conversion factor) and Di (bit-rate adjustment factor) parameters from the ATR's TA1 byte. The effective bit rate is CLK × Di / Fi. For example, with CLK = 4.8 MHz, Fi = 372, Di = 1: rate = 4,800,000 / 372 ≈ 12,903 bps. With Fi = 512, Di = 32: rate = 4,800,000 × 32 / 512 = 300,000 bps.

### 1.2 Answer to Reset (ATR) — byte-level

When the terminal asserts RST (after powering the card via VCC), the card transmits the ATR within 400–40,000 clock cycles. The ATR is a sequence of bytes with strict structure:

**TS (byte 0).** `0x3B` = direct convention (logical 1 is high voltage). `0x3F` = inverse convention (logical 1 is low voltage, bit order reversed). Almost all modern EMV cards use `0x3B`.

**T0 (byte 1).** The upper nibble (bits 7–4) is a mask indicating which interface bytes follow in the first group: bit 7 set → TA1 present, bit 6 → TB1, bit 5 → TC1, bit 4 → TD1. The lower nibble (bits 3–0) is K, the number of historical bytes.

**TA1 (if present).** Encodes Fi (upper nibble, index into a table of clock-rate conversion factors: 0→372, 1→372, 2→558, 3→744, 4→1116, ...) and Di (lower nibble, index into bit-rate adjustment factors: 1→1, 2→2, 3→4, 4→8, ...). The terminal uses these to negotiate the communication speed after ATR. If TA1 is absent, defaults apply (Fi=372, Di=1).

**TB1 (if present).** Encodes the programming voltage (VPP) — deprecated in modern EMV; TB1 is typically `0x00` (no VPP).

**TC1 (if present).** Encodes N, the extra guard time between characters. N additional etu are inserted between consecutive bytes on the I/O line. `0x00` = no extra guard time; `0xFF` = minimum guard time (for T=1, means 11 etu instead of 12).

**TD1 (if present).** The upper nibble indicates the presence of the next group of interface bytes (TA2, TB2, TC2, TD2), and the lower nibble encodes the protocol type: `0` = T=0, `1` = T=1. If TD1's lower nibble is `1`, the card offers T=1. If multiple TDi bytes are present, each introduces another group and potentially another protocol.

**TA2 (if present after TD1).** Indicates the specific mode of operation (negotiable vs specific mode). If TA2 is present, the card is in "specific mode" (the protocol is fixed; no PPS — Protocol and Parameters Selection — is needed). If absent, the card is in "negotiable mode" (the terminal may send PPS to select a protocol and parameters).

Subsequent interface bytes (TB2, TC2, TD2, TA3, TB3, TC3, ...) provide additional parameters for the selected protocol. For T=1: TB3 encodes BWI (Block Waiting time Integer) and CWI (Character Waiting time Integer) — the timeout values the terminal must respect when waiting for the card's response. TA3 encodes IFSI (Information Field Size Integer for the card — the maximum number of data bytes the card can receive in one T=1 I-block).

**Historical bytes (K bytes).** Card-specific data. In EMV, these often follow a TLV structure defined by ISO 7816-4 (category indicator byte, followed by COMPACT-TLV data objects encoding: card service data, card capabilities, application identifier, and pre-issuing data). The historical bytes are informational and do not affect the communication protocol.

**TCK (check byte).** Present if any TDi byte indicates a protocol other than T=0. TCK = XOR of all bytes from T0 to the last interface byte/historical byte. The terminal verifies TCK; a mismatch indicates a communication error.

### 1.3 Complete ATR parsing example

The following real-world ATR is from a Mastercard chip card:

```
3B 6D 00 00 80 31 80 65 B0 83 11 00 01 83 90 00
```

Byte-by-byte decode:

```
Byte  Hex   Field          Meaning
----  ----  -----          -------
 0    3B    TS             Direct convention
 1    6D    T0             Upper nibble 0x6 → TA1 present (bit 6), TB1 absent,
                           TC1 present (bit 5), TD1 present (bit 4).
                           Lower nibble 0xD → K=13 historical bytes.
 2    00    TA1            Fi index=0 (372), Di index=0 → default speed (card
                           does not request speed negotiation; uses Fi=372, Di=1).
 3    00    TC1            N=0 → no extra guard time.
 4    80    TD1            Upper nibble 0x8 → TA2 absent, TB2 absent, TC2 absent,
                           TD2 present. Lower nibble 0x0 → T=0 protocol offered.
 5    31    TD2            Upper nibble 0x3 → TA3 present, TB3 present. Lower
                           nibble 0x1 → T=1 protocol also offered. (Card supports
                           both T=0 and T=1.)
 6    80    TA3            IFSI = 0x80 = 128 → max 128 bytes per T=1 I-block
                           from card.
 7    65    TB3            Upper nibble 0x6 → BWI=6 (Block Waiting Time =
                           2^6 × 11 etu × 372/f ≈ 960 ms at 4 MHz).
                           Lower nibble 0x5 → CWI=5 (Character Waiting Time =
                           2^5 + 11 = 43 etu).
 8    B0    Historical[0]  Category indicator 0xB0 → COMPACT-TLV data objects
                           follow (ISO 7816-4 §8.1.1.3, status indicator present).
 9    83    Historical[1]  Tag 0x8 (status indicator), length 3 → 3 bytes follow.
10    11    Historical[2]  Card service data byte 1.
11    00    Historical[3]  Card service data byte 2.
12    01    Historical[4]  Card service data byte 3.
13    83    Historical[5]  Tag 0x8 (card capabilities), length 3 → 3 bytes follow.
14    90    Historical[6]  Card capability byte 1 (DF selection by full/partial AID).
15    00    Historical[7]  Card capability byte 2.
16    —     TCK            0x3B ⊕ 0x6D ⊕ 0x00 ⊕ 0x00 ⊕ 0x80 ⊕ 0x31 ⊕ 0x80
                           ⊕ 0x65 ⊕ 0xB0 ⊕ 0x83 ⊕ 0x11 ⊕ 0x00 ⊕ 0x01 ⊕ 0x83
                           ⊕ 0x90 ⊕ 0x00 = check. TCK is present because T=1
                           is offered. If the XOR of bytes T0 through TCK (inclusive)
                           is zero, the ATR is valid.
```

The terminal parses this ATR to determine: the card supports T=0 and T=1 (the terminal selects T=1 if it prefers block-oriented communication, or T=0 if it prefers character-oriented); the card accepts up to 128-byte I-blocks in T=1 mode; the card does not request speed negotiation (default etu = 372 clock cycles); and the historical bytes indicate full/partial AID selection is supported.

### 1.4 T=0 protocol mechanics

T=0 is character-oriented: the terminal sends a 5-byte command header (CLA INS P1 P2 P3), where P3 is either Lc (the number of data bytes the terminal will send) or Le (the number of response bytes expected). The card responds with a procedure byte:

If the procedure byte is INS (the instruction byte): the terminal sends or receives the next byte of data (single-byte transfer). If the procedure byte is INS XOR `0xFF` (the complement): the terminal sends or receives all remaining data bytes. If the procedure byte is `0x60` (null byte): the card requests more time (the terminal waits). If the procedure byte is `0x61 XX`: SW1=`0x61`, meaning "XX bytes of response data available" — the terminal sends `GET RESPONSE` (CLA=`0x00`, INS=`0xC0`, P1=P2=`0x00`, Le=XX) to retrieve the data. If the procedure byte is `0x6C XX`: SW1=`0x6C`, meaning "wrong Le; the correct Le is XX" — the terminal re-issues the command with the corrected Le.

The interleaving of procedure bytes makes T=0 chattier but simpler to implement (no block framing, no error-recovery protocol). For EMV transactions, T=0 is adequate — the data volumes are small (a few hundred bytes per command).

A critical constraint of T=0: it cannot handle Case 4 APDUs (data in and data out) directly. The terminal sends the 5-byte header plus Lc data bytes; the card processes them and returns SW1 SW2 only. If the card has response data, it returns `0x61 XX` as the status word, and the terminal issues a separate GET RESPONSE command to retrieve the data. This two-step dance is transparent to the application layer but adds round trips compared to T=1.

### 1.5 T=1 protocol mechanics

T=1 is block-oriented. Each block has: a prologue (NAD — Node Address byte, PCB — Protocol Control Byte, LEN — length of the INF field), an information field (INF, 0–254 bytes), and an epilogue (LRC — Longitudinal Redundancy Check, or CRC-16 — selected by TC1/TC3 in the ATR).

Block types, determined by PCB: **I-block** (Information block — carries APDU data; PCB bit 7 = 0; includes a sequence number N(S) and a More-data bit M for chaining long APDUs across multiple I-blocks). **R-block** (Receive-ready — acknowledgment or error; PCB bits 7–6 = 10; carries the expected sequence number N(R)). **S-block** (Supervisory — protocol management; PCB bits 7–6 = 11; types: RESYNCH request/response, IFS request/response for changing the information-field size, ABORT request/response, WTX — Waiting Time Extension request/response).

Chaining: if the APDU data exceeds the negotiated IFSC (card) or IFSD (terminal), the sender splits the data across multiple I-blocks, setting the M (more) bit on all but the last block. The receiver acknowledges each block with an R-block before the sender transmits the next.

Error recovery: if a block is received with an incorrect LRC/CRC, the receiver sends an R-block indicating the error. The sender retransmits the failed block. After multiple retransmission failures, the terminal initiates a RESYNCH (S-block) to reset the protocol state.

T=1 handles Case 4 APDUs natively: the terminal sends the full command APDU (CLA INS P1 P2 Lc Data Le) in one or more I-blocks, and the card responds with the full response APDU (Data SW1 SW2) in one or more I-blocks. No GET RESPONSE intermediary is needed.

### 1.6 T=0 vs T=1 comparison and APDU case analysis

The practical differences between the two protocols are relevant to EMV implementers because the choice affects timing, error-recovery behavior, and the way the terminal software handles Case 4 commands.

**APDU Case Analysis.** ISO 7816-3 defines four cases that determine the C-APDU structure:

**Case 1 — command, no data in or out.** The C-APDU is exactly 4 bytes: CLA INS P1 P2. No Lc, no data, no Le. Example: `EXTERNAL AUTHENTICATE` when no data is sent (rare; most EMV uses of EXTERNAL AUTHENTICATE include data).

**Case 2 — no data in, data out expected.** C-APDU: CLA INS P1 P2 Le. Example: `GET DATA` with Le=`0x00` (expect up to 256 bytes). In T=0, P3 = Le; the card responds with data plus SW1 SW2. In T=1, the terminal sends the 5-byte APDU in an I-block; the card responds with data and status in its I-block.

**Case 3 — data in, no data out.** C-APDU: CLA INS P1 P2 Lc Data. Example: `VERIFY` (PIN command) with the PIN data. In T=0, P3 = Lc; the terminal sends the data; the card responds with SW1 SW2. In T=1, identical flow in I-blocks.

**Case 4 — data in and data out.** C-APDU: CLA INS P1 P2 Lc Data Le. Example: `GET PROCESSING OPTIONS` (the terminal sends PDOL data and expects AIP/AFL in response), `GENERATE APPLICATION CRYPTOGRAM` (terminal sends CDOL data and expects the cryptogram). This is the critical case. In T=0, the terminal sends CLA INS P1 P2 Lc Data (the Le byte is dropped from the wire format). The card processes the data and returns SW1=`0x61`, SW2=number of response bytes available. The terminal then sends GET RESPONSE with Le = the value from SW2. This means every Case 4 command requires two exchanges in T=0. In T=1, the full 5+Lc+1 byte APDU is sent in one shot (one or more I-blocks if chaining is needed), and the card responds directly with the data and SW1 SW2.

### 1.7 Status words — comprehensive table

The card's SW1 SW2 bytes encode the result of every APDU. EMV-relevant status words:

```
SW1 SW2   Meaning                                                     EMV Context
--------  -------                                                     -----------
90  00    Command successfully executed                               Normal success
61  XX    SW2 bytes of response data available (use GET RESPONSE)     T=0 Case 4 response
6C  XX    Wrong Le; correct Le is SW2 (re-issue with correct Le)      Le negotiation
62  83    Selected file deactivated (warning)                         Application blocked
63  00    Verification failed (no information given)                  Wrong PIN (general)
63  CX    Verification failed; X retries remaining                   63C2 = 2 PIN tries left
64  00    State of non-volatile memory unchanged (error)              Persistent write failed
65  81    Memory write failure                                        Card EEPROM problem
67  00    Wrong length (Lc/Le does not match expected)                Malformed APDU
69  83    Authentication method blocked                               PIN try counter = 0
69  84    Referenced data invalidated                                 Key/cert invalidated
69  85    Conditions of use not satisfied                             CVM not performed
69  86    Command not allowed (no current EF)                         No record selected
6A  81    Function not supported                                      Unsupported INS
6A  82    File or application not found                               AID not found
6A  83    Record not found                                            READ RECORD past end
6A  86    Incorrect P1-P2                                             Invalid parameters
6A  88    Referenced data (data object) not found                     Tag not found
6B  00    Wrong parameters (offset outside EF)                        Bad P1/P2 value
6D  00    Instruction code not supported or invalid                   Unknown INS byte
6E  00    Class not supported                                         Wrong CLA byte
6F  00    No precise diagnosis                                        Internal card error
```

The terminal's state machine must handle all of these. In particular, `0x63CX` is critical for PIN management: the terminal must display the remaining retry count to the cardholder and track that `0x6983` (PIN blocked) terminates the CVM attempt permanently for that card until the issuer unblocks the PIN (via issuer script command `0x24` — PIN CHANGE/UNBLOCK).

---

## 2. APDU structure and TLV encoding

### 2.1 Command APDU

The command APDU (C-APDU) consists of a mandatory header and an optional body:

Header (4 bytes): **CLA** (Class byte — `0x00` for ISO 7816 standard commands, `0x80`–`0x8F` for proprietary, `0x0C`/`0x8C` for secure messaging). **INS** (Instruction — `0xA4` SELECT, `0xB2` READ RECORD, `0xCA` GET DATA, `0x88` INTERNAL AUTHENTICATE, `0x82` EXTERNAL AUTHENTICATE, `0xAE` GENERATE AC, `0x20` VERIFY, etc.). **P1** (parameter 1 — command-specific). **P2** (parameter 2 — command-specific).

Body (optional): **Lc** (1 or 3 bytes — length of the following data field; 0 if no data), **Data** (Lc bytes — command-specific data), **Le** (1 or 3 bytes — maximum expected response length; `0x00` means 256 bytes for short Le, or `0x0000` means 65536 for extended Le).

Four cases: Case 1 (no data, no response expected — header only), Case 2 (no data, response expected — header + Le), Case 3 (data, no response — header + Lc + Data), Case 4 (data and response — header + Lc + Data + Le).

### 2.2 Response APDU

Body (optional): **Data** (the response data, length determined by the actual data the card returns). Trailer: **SW1 SW2** (Status Word — 2 bytes). See §1.7 for the comprehensive status word table.

### 2.3 BER-TLV encoding

EMV data is encoded in BER-TLV (Basic Encoding Rules — Tag-Length-Value). Each data object has: a **Tag** (1 or 2 bytes — identifies the data element; first byte bits 4–0 = `0x1F` means the tag continues in the next byte), a **Length** (1 or 2 or 3 bytes — `0x00`–`0x7F` for 0–127 bytes; `0x81 XX` for 128–255 bytes; `0x82 XX YY` for 256–65535 bytes), and a **Value** (the data content).

Constructed tags (bit 5 of the first tag byte set) contain nested TLV objects. Primitive tags contain raw data. Key EMV tags: `0x5A` (PAN), `0x5F24` (Application Expiration Date, YYMMDD), `0x5F20` (Cardholder Name), `0x57` (Track 2 Equivalent Data), `0x8C` (CDOL1 — Card Risk Management Data Object List 1), `0x8D` (CDOL2), `0x8E` (CVM List), `0x9F26` (Application Cryptogram), `0x9F27` (Cryptogram Information Data — indicates ARQC/TC/AAC), `0x9F10` (Issuer Application Data), `0x9F36` (Application Transaction Counter), `0x9F4B` (Signed Dynamic Application Data).

---

## 3. Application selection — deep dive

### 3.1 PSE for contact — complete APDU sequence

The terminal sends SELECT PSE:

```
>> 00 A4 04 00 0E 31 50 41 59 2E 53 59 53 2E 44 44 46 30 31 00
   CLA=00 INS=A4 P1=04(select by name) P2=00(first occurrence)
   Lc=0E(14 bytes)
   Data="1PAY.SYS.DDF01" (ASCII: 31 50 41 59 2E 53 59 53 2E 44 44 46 30 31)
   Le=00(up to 256 bytes)

<< 6F 1E 84 0E 31 50 41 59 2E 53 59 53 2E 44 44 46 30 31 A5 0C 88 01 01
   BF 0C 05 9F 4D 02 0B 0A
   SW1=90 SW2=00

FCI template (tag 6F) decoded:
  84 0E  DF Name: "1PAY.SYS.DDF01"
  A5 0C  FCI Proprietary Template:
    88 01 01  SFI of PSE directory = 0x01 (SFI 1)
    BF0C 05   FCI Issuer Discretionary Data:
      9F4D 02 0B 0A  Log Entry: SFI 11, 10 records (transaction log)
```

The terminal then reads the PSE directory. SFI 1 means the directory file is accessed by READ RECORD with SFI = 1:

```
>> 00 B2 01 0C 00
   INS=B2(READ RECORD) P1=01(record 1) P2=0C(SFI 1 << 3 | 0x04 = 0x0C)
   Le=00

<< 70 23 61 21 4F 07 A0 00 00 00 04 10 10 50 0A 4D 61 73 74 65 72 63 61
   72 64 87 01 01 9F 12 0A 4D 61 73 74 65 72 63 61 72 64
   SW1=90 SW2=00

Record template (tag 70) decoded:
  61 21  Application Template:
    4F 07 A0000000041010  AID: Mastercard Credit (RID A0000000 04 = Mastercard,
                          PIX 1010 = credit/debit)
    50 0A "Mastercard"    Application Label
    87 01 01              Application Priority Indicator: priority 1 (highest)
    9F12 0A "Mastercard"  Application Preferred Name
```

If there are more records, the terminal continues reading (record 2, 3, ...) until it receives SW1 SW2 = `6A 83` (record not found). Each record may contain additional Application Templates (`0x61`) for other applications on the card (e.g., a Maestro debit application alongside the Mastercard credit application).

### 3.2 PPSE for contactless

Identical flow but using `"2PAY.SYS.DDF01"`. The PPSE response additionally includes: `0x9F2A` (Kernel Identifier — identifies which contactless kernel to use: Visa kernel, Mastercard kernel, etc.) and `0xBF0C` (FCI Issuer Discretionary Data — containing scheme-specific parameters for the contactless transaction).

### 3.3 AID selection and FCI parsing

After identifying the AID (from PSE/PPSE or from the terminal's configured list), the terminal sends SELECT with the AID:

```
>> 00 A4 04 00 07 A0 00 00 00 04 10 10 00
   Lc=07, Data=A0000000041010 (Mastercard AID), Le=00

<< 6F 38 84 07 A0 00 00 00 04 10 10 A5 2D 50 0A 4D 61 73 74 65 72 63 61
   72 64 87 01 01 9F 38 12 9F 66 04 9F 02 06 9F 03 06 9F 1A 02 5F 2A 02
   9A 03 9C 01 9F 37 04
   SW1=90 SW2=00

FCI (tag 6F) decoded:
  84 07 A0000000041010    DF Name (full AID — exact match confirmed)
  A5 2D                   FCI Proprietary Template:
    50 0A "Mastercard"    Application Label
    87 01 01              Application Priority Indicator: 1
    9F38 12               PDOL (18 bytes of tag-length pairs):
      9F66 04             Terminal Transaction Qualifiers (4 bytes)
      9F02 06             Amount, Authorized (6 bytes BCD)
      9F03 06             Amount, Other (6 bytes BCD)
      9F1A 02             Terminal Country Code (2 bytes)
      5F2A 02             Transaction Currency Code (2 bytes)
      9A   03             Transaction Date (3 bytes YYMMDD)
      9C   01             Transaction Type (1 byte)
      9F37 04             Unpredictable Number (4 bytes)
```

The PDOL tells the terminal exactly which data elements the card needs for GPO. The terminal concatenates the values (without tags, in PDOL order) to form the PDOL data. For this example, the PDOL data would be 28 bytes: 4 (TTQ) + 6 (amount) + 6 (amount other) + 2 (country) + 2 (currency) + 3 (date) + 1 (type) + 4 (UN).

### 3.4 AID matching: exact and partial

The terminal maintains a list of supported AIDs. When matching against the card's applications, two algorithms apply:

**Exact match.** The terminal's AID must exactly equal the card's AID. Example: terminal has `A0000000041010`; card reports `A0000000041010` — match.

**Partial match.** The terminal's AID is a prefix of the card's AID. Example: terminal has `A000000004` (Mastercard RID only); card reports `A0000000041010` — the terminal's AID is a prefix, so partial match succeeds. The card responds with the full AID in the `0x84` (DF Name) tag of the FCI, which may be longer than what the terminal requested. The terminal uses partial matching when it wants to accept any product from a given payment network (any Mastercard product, regardless of PIX).

The Application Priority Indicator (tag `0x87`) determines selection order when multiple applications match. Bits 3–0 encode the priority (1 = highest, 15 = lowest). Bit 7 indicates whether cardholder confirmation is required before selecting. If two applications have the same priority, the first one encountered in the directory has precedence.

---

## 4. EMV transaction flow — complete walkthrough

### 4.1 GET PROCESSING OPTIONS (GPO)

The terminal sends: CLA=`0x80`, INS=`0xA8`, P1=`0x00`, P2=`0x00`, with data containing tag `0x83` (Command Template) whose value is the concatenated PDOL data (the values of all data elements requested in the PDOL, in order, without tags).

The card processes the GPO: initializes the transaction, evaluates the terminal data, and responds with:

**AIP (Application Interchange Profile, tag `0x82`, 2 bytes).** Bit flags: byte 1 bit 7 = SDA supported, bit 6 = DDA supported, bit 5 = cardholder verification supported, bit 4 = terminal risk management performed, bit 3 = issuer authentication supported, bit 0 = CDA supported. Byte 2 is RFU (Reserved for Future Use). The AIP tells the terminal which security features are available.

**AFL (Application File Locator, tag `0x94`, variable length, multiple of 4 bytes).** Each 4-byte entry: byte 1 = SFI (Short File Identifier, upper 5 bits, shifted left 3) || `0x00` (lower 3 bits), byte 2 = first record number, byte 3 = last record number, byte 4 = number of records involved in offline data authentication (starting from the first record). Example: `0x08 01 03 02` means SFI 1 (0x08 >> 3 = 1), records 1 through 3, first 2 records are signed for ODA.

**Concrete GPO exchange.** The terminal constructs the PDOL data from the FCI's PDOL template (§3.3) and wraps it in tag `0x83`:

```
>> 80 A8 00 00 1E 83 1C
   B6 20 40 00             TTQ: 9F66 = contactless+online+CVM
   00 00 00 00 10 00       Amount Authorized: 9F02 = 10.00
   00 00 00 00 00 00       Amount Other: 9F03 = 0.00
   08 40                   Country Code: 9F1A = US (0840)
   08 40                   Currency Code: 5F2A = USD (0840)
   26 05 08                Transaction Date: 9A = 2026-05-08
   00                      Transaction Type: 9C = purchase
   7A E3 91 F2             Unpredictable Number: 9F37
   00

<< 77 12 82 02 5C 00 94 0C 08 01 03 02 10 01 01 00 18 01 01 00
   SW1=90 SW2=00

Response Format 2 (tag 77) decoded:
  82 02 5C00    AIP = 0x5C00:
                  Byte 1: 0x5C = 0101 1100
                    bit 6 (0x40): DDA supported
                    bit 4 (0x10): terminal risk management to be performed
                    bit 3 (0x08): issuer authentication supported
                    bit 2 (0x04): CDA supported
                  Byte 2: 0x00 (RFU)
  94 0C         AFL (12 bytes = 3 entries):
    08 01 03 02   SFI 1 (08>>3=1), records 1-3, first 2 for ODA
    10 01 01 00   SFI 2 (10>>3=2), record 1 only, 0 for ODA
    18 01 01 00   SFI 3 (18>>3=3), record 1 only, 0 for ODA
```

The terminal now knows: the card supports DDA and CDA (from AIP), and it must read records 1-3 from SFI 1 (where records 1-2 contain signed data for ODA — typically the certificates), record 1 from SFI 2 (typically PAN, expiry, Track 2 equivalent), and record 1 from SFI 3 (typically CDOL1, CDOL2, CVM list).

### 4.2 READ RECORD

For each AFL entry, the terminal reads records: `READ RECORD` (INS=`0xB2`, P1=record number, P2 = SFI << 3 | `0x04`). The card responds with the record data (TLV-encoded data objects).

The terminal accumulates all data objects from the records. Key data elements retrieved:

From the card's records: PAN (tag `0x5A`), Expiration Date (`0x5F24`), Cardholder Name (`0x5F20`), Track 2 Equivalent Data (`0x57`), Application Usage Control (`0x9F07` — 2 bytes of bit flags: valid for domestic/international cash/goods/services, ATM, cashback), CVM List (`0x8E`), CDOL1 (`0x8C` — the list of data elements the card wants in the GENERATE AC command), CDOL2 (`0x8D` — for the second GENERATE AC), Issuer Public Key Certificate (`0x90`), Issuer Public Key Remainder (`0x92`), Issuer Public Key Exponent (`0x9F32`), ICC Public Key Certificate (`0x9F46`), ICC Public Key Remainder (`0x9F48`), ICC Public Key Exponent (`0x9F47`), Static Data Authentication Tag List (`0x9F4A`).

The terminal also accumulates the "offline data authentication data" — the raw record data (as received, before TLV parsing) for the records specified by the AFL's "number of ODA records" field. This data is the input to the ODA process (§5).

### 4.3 Terminal risk management

Before generating the cryptogram, the terminal evaluates the transaction against its risk-management parameters: floor limit (transactions below the floor limit can be approved offline; above requires online authorization), random transaction selection (a configurable probability of randomly selecting transactions for online authorization), and velocity checking (the card's internal counters — consecutive offline transactions, cumulative offline amount — are compared against the terminal's thresholds).

The terminal sets bits in the **TVR (Terminal Verification Results, 5 bytes)** to record the outcome of each check. The TVR bitfield layout:

```
Byte 1 (ODA results):
  bit 8: Offline data authentication was not performed
  bit 7: SDA failed
  bit 6: ICC data missing
  bit 5: Card appears on terminal exception file
  bit 4: DDA failed
  bit 3: CDA failed
  bits 2-1: RFU

Byte 2 (Issuer / application):
  bit 8: ICC and terminal have different application versions
  bit 7: Expired application
  bit 6: Application not yet effective
  bit 5: Requested service not allowed for card product
  bit 4: New card
  bits 3-1: RFU

Byte 3 (Cardholder verification):
  bit 8: Cardholder verification was not successful
  bit 7: Unrecognised CVM
  bit 6: PIN try limit exceeded
  bit 5: PIN entry required and PIN pad not present or not working
  bit 4: PIN entry required, PIN pad present, but PIN was not entered
  bit 3: Online PIN entered
  bits 2-1: RFU

Byte 4 (Terminal risk management):
  bit 8: Transaction exceeds floor limit
  bit 7: Lower consecutive offline limit exceeded
  bit 6: Upper consecutive offline limit exceeded
  bit 5: Transaction selected randomly for online processing
  bit 4: Merchant forced transaction online
  bits 3-1: RFU

Byte 5 (Default values / issuer):
  bit 8: Default TDOL used
  bit 7: Issuer authentication failed
  bit 6: Script processing failed before final GENERATE AC
  bit 5: Script processing failed after final GENERATE AC
  bits 4-1: RFU
```

The TVR is input to the GENERATE AC command and is also transmitted in the online authorization message (DE55 / tag `0x95`), giving the issuer full visibility into what the terminal observed.

### 4.4 Cardholder verification — CVM list processing

The terminal processes the CVM List (tag `0x8E`). The CVM List consists of: an 8-byte header (4 bytes: Amount X — threshold for the "if amount > X" condition; 4 bytes: Amount Y — secondary threshold), followed by a variable number of 2-byte CVM entries.

Each CVM entry: byte 1 = CVM code (bits 5–0: `0x01` plaintext PIN offline, `0x02` enciphered PIN online, `0x03` plaintext PIN + signature, `0x04` enciphered PIN offline, `0x1E` signature, `0x1F` no CVM required; bit 6: if set, apply succeeding CVM if this one fails — fallback behavior). Byte 2 = condition code (`0x00` always, `0x01` if unattended cash, `0x02` if not unattended cash and not manual cash, `0x03` if terminal supports CVM, `0x05` if PIN pad present, `0x06` if transaction > Amount X, `0x08` if transaction < Amount X, `0x09` if transaction > Amount Y).

**CVM list walkthrough example.** Consider a card with the following CVM List (tag `0x8E`, 16 bytes):

```
00 00 00 00 00 00 00 00   Amount X = 0, Amount Y = 0
42 03                      Entry 1: CVM code 0x42 = enciphered PIN online (0x02)
                                    + bit 6 set (0x40 = fallback if fails)
                                    Condition 0x03 = if terminal supports CVM
1E 03                      Entry 2: CVM code 0x1E = signature
                                    Condition 0x03 = if terminal supports CVM
1F 00                      Entry 3: CVM code 0x1F = no CVM required
                                    Condition 0x00 = always
```

The terminal processes entries in order: (1) Check condition for Entry 1: does the terminal support the CVM? If yes, attempt online enciphered PIN. If the cardholder enters the correct PIN and the issuer confirms it during online authorization, CVM succeeds. If the PIN pad is unavailable or the attempt fails: bit 6 is set, so fall back to the next entry. (2) Check Entry 2: terminal supports CVM? If yes, request signature. If cardholder signs, CVM succeeds. If signature capture is unavailable: the fallback bit is not set (byte 1 = `0x1E`, bit 6 = 0), so if this entry fails, CVM processing fails — unless the terminal reaches Entry 3 because the condition for Entry 2 was not met. (3) Entry 3: condition "always" is trivially true. No CVM required — transaction proceeds without cardholder verification (typical for contactless below the CVM limit).

The terminal records the CVM result in the **CVM Results** (tag `0x9F34`, 3 bytes): byte 1 = the CVM code that was performed, byte 2 = the condition code under which it was performed, byte 3 = the result (`0x02` = successful, `0x01` = failed, `0x00` = unknown). These bytes are included in the GENERATE AC input and in the online authorization message, allowing the issuer to verify that the terminal performed the expected CVM.

### 4.5 GENERATE APPLICATION CRYPTOGRAM

The terminal sends: CLA=`0x80`, INS=`0xAE`, P1 = reference control parameter (bit 7–6: `0x80` = ARQC requested, `0x40` = TC requested, `0x00` = AAC requested; bit 4: CDA requested if set), P2=`0x00`, with data = the values of the data elements listed in CDOL1 (concatenated in order, without tags).

CDOL1 typically requests: Amount Authorized (`0x9F02`), Amount Other (`0x9F03`), Terminal Country Code (`0x9F1A`), TVR (`0x95`), Transaction Currency Code (`0x5F2A`), Transaction Date (`0x9A`), Transaction Type (`0x9C`), Unpredictable Number (`0x9F37`), Terminal Type (`0x9F35`), Data Authentication Code (`0x9F45`).

**CDOL1 data construction example.** Suppose the card's CDOL1 (tag `0x8C`) is:

```
9F02 06  9F03 06  9F1A 02  95 05  5F2A 02  9A 03  9C 01  9F37 04  9F35 01  9F45 02
```

This means the GENERATE AC data field must be exactly: 6 + 6 + 2 + 5 + 2 + 3 + 1 + 4 + 1 + 2 = 32 bytes, concatenated in order:

```
00 00 00 00 10 00   Amount Authorized = 10.00 (BCD, 6 bytes)
00 00 00 00 00 00   Amount Other = 0 (BCD, 6 bytes)
08 40               Terminal Country Code = US (2 bytes)
00 00 00 00 00      TVR = no exceptions set (5 bytes)
08 40               Transaction Currency Code = USD (2 bytes)
26 05 08            Transaction Date = 2026-05-08 (YYMMDD, 3 bytes)
00                  Transaction Type = purchase (1 byte)
7A E3 91 F2         Unpredictable Number (4 bytes, random)
22                  Terminal Type = attended, online (1 byte)
00 00               Data Authentication Code (2 bytes)
```

The terminal sends: `80 AE 80 00 20` (CLA=80, INS=AE, P1=80 requesting ARQC, P2=00, Lc=0x20=32) followed by these 32 bytes, then Le=`00`.

The card processes the command: evaluates its own risk management (checking internal counters against card-defined thresholds), and decides the cryptogram type to return. The card may override the terminal's request: if the terminal requests TC (offline approval) but the card's risk management requires online authorization, the card returns ARQC instead. If the card declines, it returns AAC.

The card's response contains: Cryptogram Information Data (`0x9F27`, 1 byte — `0x80` = ARQC, `0x40` = TC, `0x00` = AAC, `0xA0` = AAR — Application Authentication Cryptogram), Application Transaction Counter (`0x9F36`, 2 bytes — incremented with each transaction), Application Cryptogram (`0x9F26`, 8 bytes — the MAC), Issuer Application Data (`0x9F10`, variable — issuer-specific data including the card's internal counters and the cryptogram version number).

If CDA was requested (P1 bit 4 set) and the card supports CDA, the response also includes Signed Dynamic Application Data (`0x9F4B`) — a signature over the cryptogram, the terminal's unpredictable number, and the transaction data, signed by the ICC's private key. CDA combines the cryptogram generation with the dynamic data authentication in a single response.

### 4.6 Cryptogram computation — key derivation and MAC

The Application Cryptogram (ARQC/TC/AAC) is a MAC computed over the transaction data using a session key derived from the card's master key. The full derivation chain:

**Step 1: Issuer Master Key (IMK).** The issuer holds a 16-byte 3DES key (the Issuer Master Key for Application Cryptograms). This key is stored in the issuer's HSM and is the root of the card-level key hierarchy.

**Step 2: ICC Master Key (MK_ICC).** Derived from the IMK using the card's PAN and PAN Sequence Number. The derivation method (EMV Book 2, Annex A1.4, "Option A"): compute `MK_ICC_left = 3DES_Encrypt(IMK, PAN_padded_left)` and `MK_ICC_right = 3DES_Encrypt(IMK, PAN_padded_right)`, where the PAN is formatted as the rightmost 16 digits (excluding the check digit) of the PAN, left-padded with zeros. "Option B" (for AES-based systems): uses AES-CMAC over the PAN and PSN.

**Step 3: Session Key (SK).** Derived from MK_ICC using the Application Transaction Counter (ATC). For EMV Common Session Key derivation: `SK_left = 3DES_Encrypt(MK_ICC, ATC || 0xF0 || 00...00)` and `SK_right = 3DES_Encrypt(MK_ICC, ATC || 0x0F || 00...00)`. The resulting 16-byte SK is used for exactly one transaction. The two derivation data blocks differ only in the diversification constant (`0xF0` for the left half, `0x0F` for the right half).

**Step 4: ARQC computation.** The input data is the concatenation of the CDOL1 elements (Amount Authorized, Amount Other, Terminal Country Code, TVR, Transaction Currency Code, Transaction Date, Transaction Type, Unpredictable Number) plus the AIP and ATC. For Mastercard (CVN 10/17), additional fields from the Card Verification Results (CVR, in the IAD) are included. The MAC is computed as ISO 9797-1 MAC Algorithm 3 (retail MAC): `ARQC = DES_Encrypt(SK_left, DES_Decrypt(SK_right, DES_Encrypt(SK_left, data_block_1 XOR IV) XOR data_block_2 XOR ...))`. For data shorter than 8 bytes, it is right-padded with `0x80 00 00...` (ISO 9797-1 padding method 2).

The following Python code demonstrates ARQC computation:

```python
"""
ARQC computation using 3DES-CBC-MAC (ISO 9797-1 Algorithm 3).
Requires: pip install pycryptodome
"""
from Crypto.Cipher import DES, DES3

def derive_icc_master_key(imk: bytes, pan: str, psn: str) -> bytes:
    """Derive ICC Master Key from Issuer Master Key (Option A)."""
    # Format PAN: rightmost 16 digits excluding check digit, as 8-byte BCD
    pan_digits = pan[:-1]  # strip check digit
    pan_digits = pan_digits[-16:].rjust(16, '0')
    pan_block = bytes.fromhex(pan_digits)

    # Left half derivation data: PAN block as-is
    # Right half derivation data: PAN block XOR 0xFF bytes
    cipher = DES3.new(imk, DES3.MODE_ECB)
    mk_left = cipher.encrypt(pan_block)
    mk_right = cipher.encrypt(bytes(b ^ 0xFF for b in pan_block))
    return mk_left + mk_right

def derive_session_key(mk_icc: bytes, atc: bytes) -> bytes:
    """Derive session key from ICC Master Key using ATC (Common SK derivation)."""
    cipher = DES3.new(mk_icc, DES3.MODE_ECB)
    # Left half: ATC || F0 || 00 00 00 00 00
    sk_data_left = atc + b'\xF0' + b'\x00' * 5
    # Right half: ATC || 0F || 00 00 00 00 00
    sk_data_right = atc + b'\x0F' + b'\x00' * 5
    sk_left = cipher.encrypt(sk_data_left)
    sk_right = cipher.encrypt(sk_data_right)
    return sk_left + sk_right

def iso9797_pad(data: bytes) -> bytes:
    """ISO 9797-1 padding method 2: append 0x80 then zeros to 8-byte boundary."""
    padded = data + b'\x80'
    while len(padded) % 8 != 0:
        padded += b'\x00'
    return padded

def compute_arqc(session_key: bytes, transaction_data: bytes) -> bytes:
    """Compute ARQC using ISO 9797-1 MAC Algorithm 3 (retail MAC).
    1. CBC-MAC with SK_left (single DES) over all blocks except the last.
    2. Decrypt the intermediate result with SK_right (single DES).
    3. Encrypt the result with SK_left (single DES).
    """
    sk_left = session_key[:8]
    sk_right = session_key[8:16]
    padded = iso9797_pad(transaction_data)
    blocks = [padded[i:i+8] for i in range(0, len(padded), 8)]

    # Step 1: single-DES CBC-MAC with SK_left over all blocks
    cipher_left = DES.new(sk_left, DES.MODE_ECB)
    intermediate = b'\x00' * 8  # IV = 0
    for block in blocks:
        xored = bytes(a ^ b for a, b in zip(intermediate, block))
        intermediate = cipher_left.encrypt(xored)

    # Step 2: decrypt with SK_right (single DES)
    cipher_right = DES.new(sk_right, DES.MODE_ECB)
    intermediate = cipher_right.decrypt(intermediate)

    # Step 3: encrypt with SK_left (single DES)
    arqc = cipher_left.encrypt(intermediate)
    return arqc

# --- Example ---
imk = bytes.fromhex('0123456789ABCDEFFEDCBA9876543210')
pan = '5413339000001513'   # Mastercard test PAN
psn = '00'
atc = bytes.fromhex('001C')  # ATC = 28

mk_icc = derive_icc_master_key(imk, pan, psn)
sk = derive_session_key(mk_icc, atc)

# Transaction data: Amount(6) + AmountOther(6) + CountryCode(2) + TVR(5)
# + CurrencyCode(2) + Date(3) + Type(1) + UN(4) + AIP(2) + ATC(2) = 33 bytes
txn_data = bytes.fromhex(
    '000000001000'   # Amount Authorized: 10.00
    '000000000000'   # Amount Other: 0
    '0840'           # Terminal Country Code: US
    '0000000000'     # TVR: no exceptions
    '0840'           # Transaction Currency Code: USD
    '260508'         # Transaction Date: 2026-05-08
    '00'             # Transaction Type: purchase
    'A1B2C3D4'       # Unpredictable Number
    '5C00'           # AIP: SDA + DDA + CVM + TRM supported
    '001C'           # ATC
)

arqc = compute_arqc(sk, txn_data)
print(f"ARQC: {arqc.hex().upper()}")
```

The issuer, who shares the Issuer Master Key, independently derives MK_ICC (from the PAN in the authorization message) and then SK (from the ATC in DE55), and recomputes the ARQC. If the recomputed MAC matches, the issuer knows: the transaction data is authentic (not modified in transit), the card that generated the ARQC possesses the correct key material (proving card genuineness), and the transaction details (amount, currency, date) are as presented.

### 4.7 Issuer authentication and scripts

If the transaction went online (the terminal sent the ARQC to the issuer), the issuer responds with: an Authorization Response Code (DE39 in ISO 8583 — `00` = approved, `05` = declined, etc.), an Issuer Authentication Data (tag `0x91` — typically 8 or 16 bytes, containing the ARPC — Authorization Response Cryptogram), and optionally Issuer Scripts (tag `0x71` for Script Template 1, `0x72` for Script Template 2).

The **ARPC** is computed by the issuer as: `ARPC = 3DES_Encrypt(SK, ARQC XOR Authorization Response Code || padding)`. The terminal sends `EXTERNAL AUTHENTICATE` (INS=`0x82`) with the ARPC data. The card verifies: it recomputes the ARPC using the same formula (it has the SK and the ARQC) and compares. If the ARPC verifies, the card knows the response came from the genuine issuer (mutual authentication).

**ARPC Method 2** (used by Mastercard M/Chip and newer EMV specifications): `ARPC = 3DES_MAC(SK, ARQC || CSU || proprietary_auth_data)`, where CSU is the Card Status Update (2 bytes — issuer commands to the card: update counters, block the application, change PIN try counter). Method 2 enables the issuer to embed commands in the ARPC itself, reducing the need for separate issuer scripts.

**Issuer Scripts.** Each script contains one or more APDU commands (typically `PUT DATA` to update internal card data, or `PIN CHANGE/UNBLOCK` — INS `0x24` — to manage the PIN). Script commands are MACed with a script session key (derived from the master key and a counter) — the `MAC` tag in the script template contains the MAC that the card verifies before executing the command. This prevents an attacker from injecting fake issuer scripts.

Script 71 (pre-second-GENERATE-AC): executed before the terminal sends the second GENERATE AC (if a second GENERATE AC is needed). Script 72 (post-second-GENERATE-AC or post-final-AC): executed after the final cryptogram. Common script uses: updating the card's offline counters, unblocking a blocked PIN, updating card risk parameters, or blocking a compromised application.

---

## 5. Offline Data Authentication — deep dive

### 5.1 Certificate recovery — step by step

The CA Public Key is stored in the terminal (loaded during terminal configuration — one per CA Public Key Index per payment network). The terminal uses the CA Public Key to recover the Issuer Public Key from the Issuer Public Key Certificate (tag `0x90`):

1. Decrypt the certificate: `recovered_data = RSA_Public(CA_PK, Issuer_Certificate)`. The recovered data has structure: `0x6A` (header) + `0x02` (certificate format) + Issuer Identifier (4 bytes — leftmost 3–4 digits of the issuer's PAN prefix) + Certificate Expiration Date (MMYY, 2 bytes) + Certificate Serial Number (3 bytes) + Hash Algorithm Indicator (`0x01` = SHA-1) + Issuer Public Key Algorithm Indicator (`0x01` = RSA) + Issuer Public Key Length (1 byte) + Issuer Public Key Exponent Length (1 byte) + Issuer Public Key or Leftmost Digits (NCA - 36 bytes, where NCA is the CA key modulus length in bytes) + Hash (20 bytes, SHA-1) + `0xBC` (trailer).

2. Verify the hash: compute SHA-1 over (certificate format + issuer identifier + ... + issuer PK data + issuer PK remainder [tag `0x92`] + issuer PK exponent [tag `0x9F32`]). Compare against the hash in the recovered data. If mismatch, ODA fails.

3. Extract the Issuer Public Key: concatenate the issuer PK data from the certificate with the Issuer Public Key Remainder (tag `0x92`).

The ICC Public Key is recovered similarly: decrypt the ICC Public Key Certificate (tag `0x9F46`) using the recovered Issuer Public Key. The certificate structure is analogous (header `0x6A`, format `0x04` for ICC certificates, ICC-specific fields, hash, trailer `0xBC`).

### 5.2 SDA verification

1. Recover the Issuer Public Key (§5.1).
2. Decrypt the Signed Static Application Data (SSAD, tag `0x93`) using the Issuer Public Key.
3. Recovered data: `0x6A` + `0x03` (format) + Hash Algorithm + Data Auth Code (2 bytes) + padding + Hash + `0xBC`.
4. Compute SHA-1 over: (format + hash algorithm + data auth code + padding + the offline data authentication records accumulated during READ RECORD + the Static Data Authentication Tag List values [tag `0x9F4A` — typically the AIP]).
5. Compare the computed hash against the recovered hash. Match = SDA succeeds (the card data is authentic as signed by the issuer).

SDA limitation: the signature is static — a cloned card with copied SSAD passes SDA. SDA proves data integrity but not card genuineness.

### 5.3 DDA verification

1. Recover the ICC Public Key (via the Issuer PK → ICC Certificate chain, §5.1).
2. Send `INTERNAL AUTHENTICATE` (INS=`0x88`) with data = the unpredictable number (tag `0x9F37`, generated by the terminal's RNG) plus any data elements in the DDOL (Dynamic Data Authentication Data Object List — if defined by the card; if not, defaults to the unpredictable number only).
3. The card signs the dynamic data with its ICC Private Key and returns the Signed Dynamic Application Data (SDAD, tag `0x9F4B`).
4. Decrypt SDAD using the ICC Public Key. Recovered data: `0x6A` + `0x05` (format) + Hash Algorithm + ICC Dynamic Data Length (1 byte) + ICC Dynamic Data (containing the ICC Dynamic Number — a card-generated random value) + padding + Hash + `0xBC`.
5. Compute SHA-1 over: (format + hash algorithm + ICC Dynamic Data Length + ICC Dynamic Data + padding + unpredictable number).
6. Compare. Match = DDA succeeds (the card possesses the ICC Private Key → the card is genuine, not a clone).

### 5.4 DDA — complete APDU exchange

The full DDA sequence, continuing from the ODA setup after READ RECORD:

```
Terminal constructs DDOL data. If the card defines a DDOL (tag 0x9F49),
it lists the tags the terminal must include. Most cards do not define a DDOL,
in which case the default is the Unpredictable Number (tag 0x9F37, 4 bytes).

>> 00 88 00 00 04 7A E3 91 F2 00
   CLA=00 INS=88(INTERNAL AUTHENTICATE) P1=00 P2=00
   Lc=04 Data=7AE391F2 (Unpredictable Number)
   Le=00

<< 80 81 80 [128 bytes of SDAD] 90 00
   Tag 80 = Response Message Template (primitive form)
   Length = 0x81 0x80 = 128 bytes (the RSA signature, same length as ICC PK modulus)

The terminal recovers the SDAD:
  recovered = RSA_Public(ICC_PK, SDAD_bytes)
  recovered[0]    = 0x6A (header)
  recovered[1]    = 0x05 (format: DDA)
  recovered[2]    = 0x01 (hash algorithm: SHA-1)
  recovered[3]    = LDD  (ICC dynamic data length)
  recovered[4..4+LDD-1] = ICC Dynamic Data:
    byte 0 = length of ICC Dynamic Number
    bytes 1..N = ICC Dynamic Number (card-generated nonce)
  recovered[4+LDD..NI-22] = padding (0xBB bytes)
  recovered[NI-21..NI-2] = 20-byte SHA-1 hash
  recovered[NI-1] = 0xBC (trailer)

  where NI = length of ICC public key modulus in bytes.

  Hash verification:
    hash_input = format(05) || hash_algo(01) || ICC_Dynamic_Data(LDD bytes)
                 || padding(BB bytes) || Unpredictable_Number(4 bytes)
    computed_hash = SHA-1(hash_input)
    if computed_hash == recovered_hash: DDA PASSED
```

The ICC Dynamic Number is critical: it is a random value generated fresh by the card for each INTERNAL AUTHENTICATE command, proving that the card is computing the signature in real time (not replaying a pre-computed one). This is what makes DDA resistant to cloning — even if an attacker copies all the card's public data (certificates, PAN, records), they cannot compute a valid DDA signature without the ICC private key.

### 5.5 CDA verification

CDA combines the DDA signature with the GENERATE AC response. When P1 of GENERATE AC has bit 4 set (CDA requested), the card's response includes SDAD (tag `0x9F4B`). The SDAD covers: the cryptogram (ARQC/TC/AAC), the unpredictable number, and the transaction data — binding the card's identity proof to the specific transaction. The terminal verifies the SDAD using the ICC Public Key, simultaneously verifying card genuineness and cryptogram integrity.

CDA is the strongest ODA method because it prevents a MitM from substituting a different cryptogram (the signature binds the cryptogram to the card's key) and proves the card is genuine at the moment of the transaction (not just that the data was once signed by the issuer, as in SDA).

### 5.6 Python implementation — ODA certificate recovery and signature verification

The following demonstrates issuer public key recovery and SDA verification using raw RSA operations. EMV does not use PKCS#1 v1.5 padding; it uses its own envelope format (`0x6A` header, `0xBC` trailer), so the code performs raw modular exponentiation.

```python
"""
EMV Offline Data Authentication — Issuer Public Key Recovery and SDA Verification.
Requires: pip install cryptography
"""
import hashlib
from cryptography.hazmat.backends import default_backend

def int_to_bytes(n: int, length: int) -> bytes:
    return n.to_bytes(length, byteorder='big')

def bytes_to_int(b: bytes) -> int:
    return int.from_bytes(b, byteorder='big')

def raw_rsa_recover(public_key_modulus: bytes, public_key_exponent: int,
                     ciphertext: bytes) -> bytes:
    """Raw RSA public-key operation: plaintext = ciphertext^e mod n.
    EMV certificate recovery is raw RSA (no PKCS#1 padding)."""
    n = bytes_to_int(public_key_modulus)
    c = bytes_to_int(ciphertext)
    m = pow(c, public_key_exponent, n)
    return int_to_bytes(m, len(public_key_modulus))

def recover_issuer_public_key(
    ca_modulus: bytes, ca_exponent: int,
    issuer_cert: bytes,         # tag 0x90
    issuer_pk_remainder: bytes, # tag 0x92 (may be empty)
    issuer_pk_exponent: bytes   # tag 0x9F32
) -> bytes:
    """Recover the Issuer Public Key from the Issuer PK Certificate."""
    recovered = raw_rsa_recover(ca_modulus, ca_exponent, issuer_cert)
    n_ca = len(ca_modulus)

    # Validate envelope
    assert recovered[0] == 0x6A, f"Bad header: {recovered[0]:02X}"
    assert recovered[-1] == 0xBC, f"Bad trailer: {recovered[-1]:02X}"
    assert recovered[1] == 0x02, f"Bad format: {recovered[1]:02X}"

    # Parse fields (EMV Book 2, Table 4)
    cert_format = recovered[1:2]
    issuer_id = recovered[2:6]
    cert_expiry = recovered[6:8]
    cert_serial = recovered[8:11]
    hash_algo = recovered[11:12]
    pk_algo = recovered[12:13]
    pk_length = recovered[13]
    pk_exp_length = recovered[14]
    # Issuer PK (or leftmost bytes): bytes 15 to (n_ca - 36 - 1)
    pk_data = recovered[15:n_ca - 21]  # NCA - 36 bytes of PK data
    cert_hash = recovered[n_ca - 21:n_ca - 1]  # 20-byte SHA-1

    # Reconstruct full Issuer PK
    issuer_pk_full = pk_data[:pk_length]
    if issuer_pk_remainder:
        issuer_pk_full = pk_data + issuer_pk_remainder
        issuer_pk_full = issuer_pk_full[:pk_length]

    # Verify hash
    hash_input = (cert_format + issuer_id + cert_expiry + cert_serial +
                  hash_algo + pk_algo + bytes([pk_length, pk_exp_length]) +
                  pk_data + issuer_pk_remainder + issuer_pk_exponent)
    computed_hash = hashlib.sha1(hash_input).digest()
    assert computed_hash == cert_hash, "Issuer PK certificate hash mismatch — ODA FAILED"

    return issuer_pk_full

def verify_sda(
    issuer_pk_modulus: bytes, issuer_pk_exponent: int,
    ssad: bytes,              # tag 0x93 — Signed Static Application Data
    oda_data: bytes,          # concatenated offline data auth records from READ RECORD
    sda_tag_list_values: bytes  # values of tags in tag 0x9F4A (typically AIP)
) -> bool:
    """Verify SDA: recover and verify the Signed Static Application Data."""
    recovered = raw_rsa_recover(issuer_pk_modulus, issuer_pk_exponent, ssad)
    n_iss = len(issuer_pk_modulus)

    assert recovered[0] == 0x6A, f"Bad header: {recovered[0]:02X}"
    assert recovered[-1] == 0xBC, f"Bad trailer: {recovered[-1]:02X}"
    assert recovered[1] == 0x03, f"Bad format: {recovered[1]:02X}"

    data_format = recovered[1:2]
    hash_algo = recovered[2:3]
    data_auth_code = recovered[3:5]
    padding = recovered[5:n_iss - 21]
    cert_hash = recovered[n_iss - 21:n_iss - 1]

    # Compute hash over: format + hash_algo + data_auth_code + padding
    #                     + ODA records + SDA tag list values
    hash_input = (data_format + hash_algo + data_auth_code + padding +
                  oda_data + sda_tag_list_values)
    computed_hash = hashlib.sha1(hash_input).digest()
    return computed_hash == cert_hash
```

The same pattern applies to ICC public key recovery (from the ICC certificate using the recovered Issuer PK) and DDA verification (recovering the signed dynamic data from tag `0x9F4B` using the ICC PK, then verifying the hash over the dynamic data and unpredictable number).

---

## 6. PIN verification — ISO 9564

### 6.1 PIN block Format 0 (ISO 9564-1)

Format 0 is the most widely used PIN block format. It XORs a prepared PIN field with a prepared PAN field to produce an 8-byte PIN block:

**Prepared PIN field (8 bytes):**
```
Byte layout: 0 L P P P P P P F F F F F F F F
             | | |<-- PIN digits -->|<- 0xF fill ->|
             | +-- PIN length (1 nibble, 4-12)
             +---- Format code (0x0 for Format 0)
```

Example for PIN "1234" (length 4):
```
04 12 34 FF FF FF FF FF
```

**Prepared PAN field (8 bytes):**
```
Byte layout: 00 00 PP PP PP PP PP PP
                   |<-- rightmost 12 PAN digits (excluding check digit), BCD-encoded -->|
```

For PAN `5413339000001513`: strip the check digit (rightmost digit `3`) → `541333900000151`. Take the rightmost 12 digits of this result → `339000001510`. Left-pad with four zero nibbles to fill 8 bytes → `0000 3390 0000 1510`. Formatted as 8 bytes:

```
00 00 33 90 00 00 15 10
```

**PIN block = Prepared PIN XOR Prepared PAN:**
```
  04 12 34 FF FF FF FF FF
⊕ 00 00 33 90 00 00 15 10
= 04 12 07 6F FF FF EA EF
```

This 8-byte PIN block is then encrypted with the terminal's Zone PIN Key (ZPK, a 3DES key shared between the terminal's EPP and the acquirer's HSM) before transmission: `encrypted_pin_block = 3DES_Encrypt(ZPK, pin_block)`.

The XOR with the PAN means the same PIN produces different PIN blocks for different PANs, preventing trivial PIN-harvesting attacks across stolen PIN blocks. However, if an attacker knows the PAN (which is transmitted in the clear in DE2 of the ISO 8583 message), the XOR provides no security — the PAN block is known, and the attacker can recover the prepared PIN field by XORing the decrypted PIN block with the PAN block. The real security comes from the 3DES encryption with the ZPK.

### 6.2 PIN block Format 4 (AES-based)

Format 4 (ISO 9564-1:2017 Amendment 1) replaces 3DES with AES and adds a random component:

```
Byte layout (16 bytes): 4 L P P P P P P P P P P P P A A
                         | | |<--- PIN digits ---->| |<->|
                         | +-- PIN length              Padding algorithm
                         +---- Format code (0x4)       indicator + random fill
```

The 16-byte block is: format nibble `0x4`, PIN length nibble, PIN digits (each as one nibble), then the remaining nibbles are filled with a cryptographically random value (not `0xF` as in Format 0). This random fill means the same PIN produces a different PIN block every time, defeating frequency analysis.

The PIN block is encrypted with AES-128 or AES-256 (the terminal's AES PIN key, replacing the 3DES ZPK). The move to AES provides 128-bit block size (vs. 64-bit for 3DES, eliminating birthday-bound attacks on the cipher) and future-proofs against the 3DES deprecation timeline (NIST SP 800-131A, 3DES disallowed after 2023 for new applications).

### 6.3 Online vs offline PIN

**Online PIN.** The EPP encrypts the PIN block with the ZPK. The encrypted PIN block is placed in ISO 8583 DE52 (PIN Data). The acquirer's HSM translates the PIN block from the ZPK to the issuer's Zone PIN Key (using the acquirer-to-issuer key exchange). The issuer's HSM decrypts the PIN block and verifies it against the stored PIN reference (typically a PIN offset or a PIN verification value — PVV). The result is returned in DE39 of the response. The card itself never sees the PIN in an online-PIN transaction; the verification is entirely between the terminal and the issuer.

**Offline plaintext PIN.** The terminal sends `VERIFY` (INS=`0x20`, P1=`0x00`, P2=`0x80` — plaintext PIN) with data = the PIN block (Format 0, but unencrypted — the plain 8-byte prepared PIN field without XOR with PAN). The card compares the PIN against its internally stored reference. If correct: `SW1 SW2 = 90 00`. If incorrect: `SW1 SW2 = 63 CX` (X = remaining retries). If blocked: `SW1 SW2 = 69 83`.

Security risk: the plaintext PIN travels over the card-terminal interface in the clear. A shim (§8.3) can intercept it. Offline plaintext PIN is used only for low-value transactions where the card's CVM list specifies it and no better option is available. PCI PTS requires that offline plaintext PIN is supported only in attended environments with physical tamper protection.

**Offline enciphered PIN.** The terminal encrypts the PIN with the ICC's RSA public key (recovered from the ICC Public Key Certificate during ODA). The APDU: `VERIFY` (INS=`0x20`, P1=`0x00`, P2=`0x88` — enciphered PIN) with data = the RSA-encrypted PIN block. The card decrypts using its ICC private key and verifies. This is secure against shim attacks because the shim does not have the ICC private key and cannot decrypt the PIN from the intercepted APDU.

### 6.4 PIN try counter management

The card maintains a PIN Try Counter (typically initialized to 3). Each failed offline PIN attempt decrements the counter. When the counter reaches 0, the card blocks offline PIN verification (`SW1 SW2 = 69 83`). The counter can only be reset by the issuer via an issuer script (the `PIN CHANGE/UNBLOCK` command, INS `0x24`, MACed with the script session key).

Online PIN verification does not decrement the card's PIN try counter (the card is not involved in online PIN verification). However, the issuer may maintain its own PIN try counter server-side.

A deliberate attack: an attacker with physical access to a stolen card tries PINs offline (e.g., using a custom terminal emulator). They get 3 attempts. If the card also supports online PIN, the attacker cannot use online PIN without the issuer's cooperation. The limited offline attempts are a deliberate trade-off: enough for cardholder mistakes, too few for brute-force (10,000 possible 4-digit PINs, 3 attempts = 0.03% probability of guessing correctly).

### 6.5 PIN bypass attacks

**Bypass via CVM list modification (wedge/shim).** As described in §7.3 and §7.5, a device between the card and terminal can modify the CVM list to remove PIN requirements or fake the PIN verification response. The defenses are: issuer cross-check of CVM Results vs. IAD/CVR (§10.3), and terminal/card insistence on DDA/CDA (which authenticates the data exchange, though CDA does not cover the CVM List in its signature input — only the ARQC, AIP, and transaction-specific fields).

**Bypass via protocol downgrade (the "PIN OK" attack, Basin, Sasse, and Toro-Pozo, ETH Zurich, IEEE S&P 2021 — "The EMV Standard: Break, Fix, Verify").** Researchers demonstrated that for Visa contactless transactions (qVSDC / kernel 3), an attacker using a modified Android app acting as a MitM between a stolen card and a legitimate terminal could modify the Card Transaction Qualifiers (CTQ, tag `0x9F6C`) returned by the card. The CTQ tells the terminal which CVM the card requests. By clearing the "online PIN required" bit and setting the "CDCVM performed" bit, the attacker's app tells the terminal that the cardholder's device (phone) has already performed on-device CVM (e.g., fingerprint). The terminal accepts this and does not request PIN, even for transactions above the CVM limit.

This attack succeeded because: (1) Visa's qVSDC kernel trusts the CTQ from the card without verifying it against a signature (the CTQ is not included in the fDDA signature), and (2) the terminal does not independently verify CDCVM — it trusts the card's assertion. The fix required Visa to update the kernel specification to include the CTQ in the fDDA signature input, and terminal vendors to update their kernel implementations. Mastercard's kernel 2 was not vulnerable to this specific attack because Mastercard includes CVM-related data in its offline data authentication.

**Bypass via offline PIN interception and replay.** If the card uses offline plaintext PIN and the attacker has a shim, the PIN is captured in the clear. The attacker can then use this PIN at a different terminal with the stolen card (if the card has remaining PIN tries). Mitigation: offline enciphered PIN (§6.3) eliminates the plaintext PIN exposure. Cards should prefer online PIN or offline enciphered PIN over offline plaintext PIN in their CVM list.

---

## 7. EMV attacks — full mechanics

### 7.1 Pre-play attack (Bond et al., 2014)

The attack exploits terminals where the `Unpredictable Number` (tag `0x9F37`) is not truly random. If the terminal uses a predictable PRNG (e.g., a counter, a weak LFSR, or a PRNG seeded with a known value), the attacker can predict the UN that the terminal will use for a future transaction.

Attack procedure: (1) The attacker interacts with the victim's card (e.g., via a malicious NFC reader while the card is in the victim's wallet). The attacker sends GPO and GENERATE AC with the predicted UN, obtaining a valid ARQC for a transaction with that UN, the current ATC, and the specified amount/currency/date. (2) At the predicted time, the attacker (or a mule) presents a counterfeit card at the target terminal. The terminal generates the predicted UN and sends it to the counterfeit card. The counterfeit card replays the pre-computed ARQC. (3) The terminal forwards the ARQC to the issuer. The issuer verifies the ARQC (it is valid — computed by the real card with the real key) and approves the transaction.

The ATC is a complication: the pre-played ARQC was generated with ATC=N, but by the time the counterfeit card presents it, the real card may have been used for other transactions (advancing the ATC to N+k). The issuer should detect the ATC gap (the pre-played transaction uses ATC=N, but the issuer's last-seen ATC is N+k, meaning the pre-played ATC is in the past). However, not all issuers perform strict ATC-sequence checking (some allow small gaps for out-of-order settlement).

**CVE and incident context.** The Bond et al. paper ("Chip and Skim: Cloning EMV Cards with the Pre-play Attack," IEEE S&P 2014) demonstrated that multiple terminal models from major vendors (including several widely deployed in the UK) used sequential or low-entropy UNs. The UK Cards Association disputed the practical exploitability but acknowledged the theoretical weakness. Following the paper, EMVCo updated its terminal testing requirements (EMV Level 2 Type Approval) to include UN randomness testing, requiring terminals to generate cryptographically random UNs using hardware RNG or a CSPRNG seeded from hardware entropy.

Defense: hardware RNG for the unpredictable number (not a software PRNG), issuer-side strict ATC-sequence validation, and anomaly detection on ATC values that arrive out of order or with values the issuer has already seen.

### 7.2 Contactless relay

Two NFC-capable devices (smartphones with NFC, custom NFC readers, or Proxmark devices): the "mole" device near the victim's card emulates a terminal (sends SELECT, GPO, READ RECORD, GENERATE AC); the "proxy" device at a POS terminal emulates a card (receives the terminal's commands and relays them to the mole). All APDUs are relayed in real time over a network link.

The relay adds latency (the round-trip network delay plus the card's processing time). EMV contactless specifications do not enforce strict timing — the Field Timeout is 5 seconds for the initial response, and subsequent commands have generous timeouts. A relay with < 500 ms round-trip latency is well within the timeout limits.

Practical demonstrations (Emms et al., 2013; Francis et al., 2012): relayed contactless transactions over distances of 100+ meters using two Android phones with NFC, with a success rate > 90%. The transaction completes normally; the cardholder and terminal detect nothing anomalous. The Emms et al. demonstration specifically showed relay of Visa payWave transactions where the foreign-currency flag was set to bypass the UK CVM limit, enabling high-value transactions without PIN.

**Tool setup for research/testing (authorized scope only):** The NFCGate project (open-source, TU Darmstadt) implements NFC relay on rooted Android devices. One device runs in "reader" mode (emulates a terminal to the victim card), the other in "relay" mode (emulates a card to the legitimate terminal). The relay channel uses TCP/IP over Wi-Fi or mobile data. Proxmark3 can also serve as the reader-side device with `hf 14a relay` commands. In a test environment, the relay chain is: `Proxmark3 (reader at card) ←→ TCP socket ←→ Android phone (card emulator at POS terminal)`.

Defense: relay detection via timing analysis (the terminal measures the card's response time and rejects responses that are slower than expected — but the threshold must be loose enough to accommodate slow cards, limiting effectiveness), and distance bounding (using UWB or time-of-flight RF measurements — the same defense as for PKE relay in automotive, Chapter 21B §2.3 — but UWB is not currently part of the EMV contactless specification). Mastercard's "relay resistance" protocol (introduced in kernel C-8) adds terminal-side timing checks with tighter tolerances, but adoption is not universal.

### 7.3 Shimming and CVM bypass via shim

A **shim** is a thin flexible PCB (typically 0.1mm thick, matching the ISO 7816 contact dimensions) inserted into the chip slot between the card and the terminal's contacts. The shim intercepts all APDU communication on the I/O line (contact C7) and can passively record or actively modify APDUs in transit.

What a shim can capture: all data exchanged between card and terminal — PAN, expiry, Track 2 equivalent, CVM list, AIP, all READ RECORD data, the ARQC, and critically, offline plaintext PIN (if the terminal uses offline plaintext PIN verification, the PIN travels unencrypted on the I/O line and the shim records it).

What a shim CANNOT clone: the ICC private key (stored in the chip's secure element, never exported), and the card's Master Key (also never exported). Therefore, a shim alone cannot produce a chip clone that generates valid ARQCs. The captured data (PAN, expiry, Track 2 equivalent) can be used to create a counterfeit magnetic-stripe card (if the victim terminal or another terminal accepts mag-stripe fallback — see §7.4).

**CVM bypass via shim.** The shim modifies the `VERIFY` response from the card: if the card returns `63 C2` (wrong PIN, 2 retries), the shim replaces it with `90 00` (success). The terminal believes PIN verification succeeded. However, the card's internal CVR (Card Verification Results) will record that PIN verification failed. The issuer can detect this discrepancy: the terminal reports "PIN verified" in the CVM Results (tag `0x9F34`), but the card's IAD (tag `0x9F10`) records "PIN not successfully verified." This detection requires the issuer to cross-check these fields, which not all issuers do rigorously in real time.

### 7.4 Mag-stripe fallback

If a chip-card transaction fails (terminal reads chip, gets an error — legitimately due to dirty contacts, or deliberately caused by the attacker using a card with a damaged chip area), the terminal may fall back to reading the magnetic stripe. The magnetic stripe contains: Track 1 and Track 2 data (PAN, expiration, service code, discretionary data including the CVV/CVC — a static 3-digit value computed from the PAN, expiration, and the issuer's CVV key).

An attacker who has obtained Track 1/2 data (from a data breach, a skimmer, or a RAM scraper) can produce a counterfeit magnetic-stripe card and use it at terminals that support fallback. The EMV liability shift places the financial loss on the terminal that allowed fallback, incentivizing terminal operators to disable fallback — but many terminals still support it for compatibility.

The **service code** in the track data (`2XX` = chip-capable, `1XX` = mag-stripe only) signals the terminal whether to expect a chip. An attacker who modifies the service code from `2XX` to `1XX` tells the terminal the card has no chip, bypassing the chip-first requirement. The issuer can detect this (the issuer knows the real card has a chip; a mag-stripe transaction with service code `1XX` from a chip-capable card is suspicious), but real-time detection requires the issuer to check the service code against their records during authorization.

### 7.5 Wedge device / man-in-the-middle

A wedge device is more sophisticated than a shim: it is an active computing device (typically a microcontroller — STM32 or similar — with two sets of ISO 7816 contacts) that sits between the card and the terminal. Unlike a passive shim that can only modify individual bytes, the wedge device can:

**Modify the CVM list.** The wedge intercepts the READ RECORD response containing tag `0x8E` (CVM List) and replaces it with a modified version that specifies "No CVM Required" (`0x1F 0x00`) as the only entry. The terminal processes the modified CVM list and does not request PIN or signature. The card never sees the modification (the wedge sends the original terminal commands to the card). The ARQC generated by the card is valid (the CVM list is not an input to the ARQC MAC), but the IAD/CVR will reflect the card's internal state (which may differ from the terminal's CVM results).

**Relay the PIN to a second transaction.** In a two-terminal attack: the wedge captures the cardholder's PIN at one terminal (legitimate transaction) and relays it to a second terminal (fraudulent transaction at a different location) where an accomplice uses a second wedge with a different stolen card. This requires real-time coordination but has been demonstrated in lab settings.

**Downgrade ODA.** The wedge modifies the AIP (tag `0x82`) in the GPO response to indicate SDA-only (clearing the DDA and CDA bits). If the terminal accepts SDA, it will not request INTERNAL AUTHENTICATE or CDA, and the wedge does not need the card's private key. If the terminal mandates DDA/CDA and refuses SDA-only, this attack fails. Terminal configuration should require DDA or CDA; accepting SDA alone is a security weakness.

### 7.6 EMV kernel vulnerabilities

Payment terminal software implements the EMV kernel — the state machine that processes the transaction flow. Implementation flaws in kernels have led to real-world vulnerabilities:

**TLV parsing bugs.** Malformed TLV data from a malicious card can exploit buffer overflows or integer overflows in the kernel's TLV parser. A crafted tag with a length field indicating a value larger than the actual data, or a constructed tag with deeply nested sub-tags, can trigger out-of-bounds reads or writes. CVE-2017-14061 (Ingenico terminals): a malformed EMV record caused a stack buffer overflow in the kernel, potentially allowing code execution. The fix required a firmware update to all affected terminals.

**Status word handling.** Incorrect handling of unexpected status words can leave the kernel in an inconsistent state. For example, if the kernel does not properly handle a `0x6985` (conditions not satisfied) from GENERATE AC and instead proceeds as if a TC was received, it may approve a transaction that the card declined.

**AID selection bypass.** Some kernels do not properly enforce the AID matching algorithm, accepting partial matches when they should require exact matches, or vice versa. This can allow an attacker's card to be selected with an unintended kernel configuration.

**Real-world kernel vulnerabilities.** Multiple terminal vendors have disclosed TLV parsing flaws through vendor security advisories and PCI Security Council bulletins. A representative class of bugs: the TLV parser does not validate the total length of nested constructed tags against the parent tag's length field. A malicious card returns a GPO response with a constructed tag `0x77` whose inner TLV objects declare lengths exceeding the outer container. This causes the parser to read past the allocated buffer, leaking terminal memory contents — including portions of the previous transaction's data (PAN, amount) — into the card's subsequent READ RECORD responses. These flaws are patched via firmware updates distributed through the terminal management system, but terminals that do not receive timely updates remain vulnerable.

Separately, researchers at Positive Technologies demonstrated that certain Ingenico Telium 2 terminals accepted GENERATE AC responses where the Cryptogram Information Data (tag `0x9F27`) indicated TC (offline approval) even when the terminal had requested ARQC (online authorization). The kernel's state machine did not enforce the constraint that the card must not return a more-permissive cryptogram type than requested. An attacker with a modified card could force offline approval for transactions that should have gone online, bypassing the issuer's fraud-detection entirely. The fix required patching the kernel's cryptogram-type validation logic.

**Countermeasure.** EMVCo's terminal type-approval testing (Level 2) includes negative testing with malformed APDUs and out-of-sequence responses. The EMVCo test suite was expanded in 2021 to include fuzzing of TLV structures and cryptogram-type override tests. However, the test suite is not exhaustive, and implementation-specific bugs still surface. Terminal vendors must maintain a firmware update mechanism (typically remote, via the terminal management system — TMS) with signed firmware images to deploy patches when vulnerabilities are discovered. PCI PTS requires that terminals support remote firmware updates and that the update channel is authenticated and encrypted.

---

## 8. EMV security evolution and future

### 8.1 EMV 3-D Secure 2.0

3-D Secure 2.0 (EMV 3DS, specified by EMVCo) replaced the original 3DS 1.0 protocol (Verified by Visa, Mastercard SecureCode) which relied on a full-page redirect and static password entry. 3DS 2.0 introduces a risk-based authentication flow with two paths: frictionless and challenge.

**Protocol participants.** The 3DS ecosystem involves: the **3DS Requestor** (the merchant's payment page or SDK), the **3DS Server** (merchant-side component that initiates the protocol), the **Directory Server (DS)** (operated by the card network — Visa, Mastercard — routes authentication requests to the correct issuer), and the **Access Control Server (ACS)** (operated by the issuer — makes the authentication decision).

**Frictionless flow.** The 3DS Server sends an Authentication Request (AReq) to the DS, which routes it to the ACS. The AReq contains rich risk data: device fingerprint (collected by the 3DS Method — a hidden iframe or SDK call that gathers browser/device characteristics before checkout), cardholder account information (billing address, email, phone — with cardholder consent), transaction details (amount, currency, merchant), and prior authentication history. The ACS evaluates this data against its risk models. If the transaction is deemed low-risk, the ACS returns an Authentication Response (ARes) with `transStatus = Y` (authenticated) — no cardholder interaction required. The transaction proceeds with a full liability shift to the issuer.

**Challenge flow.** If the ACS determines the transaction is high-risk or requires Strong Customer Authentication (SCA) per PSD2, it returns `transStatus = C` (challenge required). The 3DS Requestor then initiates the Challenge Flow: the cardholder is presented with an authentication challenge (OTP sent to registered phone, biometric prompt on a banking app, or knowledge-based question). The challenge is rendered in a modal (browser) or native UI (SDK). Upon successful challenge completion, the ACS returns `transStatus = Y` and a CAVV (Cardholder Authentication Verification Value) — a cryptographic proof of authentication that is included in the authorization message.

**The 3DS Method (device fingerprinting).** Before the AReq, the 3DS Server loads a hidden iframe (browser flow) or calls the 3DS SDK's `createTransaction` (app flow) pointing to the ACS's 3DS Method URL. This endpoint collects: browser user-agent, screen resolution, timezone, installed plugins, WebGL renderer string, canvas fingerprint hash, and IP geolocation. The fingerprint is sent to the ACS before the authentication request arrives, giving the ACS time to evaluate device reputation. If the ACS recognizes the device from prior successful authentications, the risk score drops significantly, enabling frictionless authentication.

**Security improvements over 3DS 1.0.** No static passwords (eliminates phishing of 3DS passwords). Device fingerprinting enables risk-based decisions without cardholder friction for low-risk transactions. The SDK-based flow (for mobile apps) uses app-to-app authentication, avoiding browser redirects that were vulnerable to MitM. The protocol supports exemptions (low-value transactions under EUR 30, trusted beneficiaries, recurring payments) defined by PSD2 RTS.

**Attack surface.** The 3DS Method iframe is a potential tracking vector (the ACS can fingerprint the cardholder's browser across merchants). Social engineering attacks can target the challenge flow: an attacker who controls a phishing site can initiate a real 3DS challenge and proxy the cardholder's OTP or biometric response in real time (real-time phishing proxy). Mitigation: FIDO/WebAuthn-based challenges (§8.3) that bind authentication to the relying party origin, preventing proxy attacks.

### 8.2 EMV Secure Remote Commerce (SRC)

EMV SRC (branded as "Click to Pay" by the card networks) provides a standardized framework for tokenized card-not-present transactions. SRC replaces the fragmented guest checkout experience with a unified flow:

The cardholder enrolls their card(s) with an SRC Initiator (the merchant's checkout page or app). The card is tokenized — a DPAN (Device PAN, or "SRC token") replaces the real PAN. When the cardholder clicks "Pay," the SRC system (maintained by the card network's Digital Card Facilitator — DCF) retrieves the stored card token, generates a transaction-specific cryptogram, and returns the tokenized payment credentials to the merchant. The merchant submits the DPAN and cryptogram to the acquirer, which routes it through the network to the issuer for authorization. The issuer de-tokenizes the DPAN to the real PAN using the Token Service Provider (MDES for Mastercard, VTS for Visa — detailed in Chapter 22B §4).

SRC eliminates the need for the cardholder to manually enter card details at each merchant, reducing both friction and the risk of card data exposure. The tokenization means the merchant never handles the real PAN, reducing PCI DSS scope. The transaction-specific cryptogram prevents replay.

### 8.3 FIDO/WebAuthn integration with payment authentication

The FIDO Alliance and EMVCo have published joint specifications for using FIDO authentication (WebAuthn / FIDO2) as a Strong Customer Authentication (SCA) method for payment transactions.

In this model, the cardholder's device (phone, laptop) holds a FIDO authenticator (platform authenticator — built into the device's secure enclave, e.g., Apple's Secure Enclave, Android's StrongBox, Windows Hello TPM). During a payment challenge (3DS 2.0 challenge flow or in-app authentication), the ACS issues a FIDO challenge. The cardholder authenticates via biometric (fingerprint, face) or device PIN. The FIDO authenticator signs the challenge with the private key bound to the issuer's relying party ID. The ACS verifies the signature with the registered public key.

The security benefit is significant: FIDO authentication is phishing-resistant (the authenticator verifies the relying party's origin, preventing credential replay to a different site), resistant to credential stuffing (no reusable password), and bound to the hardware (the private key cannot be exported from the secure enclave). This makes it the strongest SCA method currently available for remote payments, surpassing OTP (vulnerable to SIM-swap and real-time phishing proxies) and knowledge-based authentication (vulnerable to social engineering).

### 8.4 PSD2 SCA requirements and EMV ecosystem impact

The revised Payment Services Directive (PSD2, EU 2015/2366) and its Regulatory Technical Standards (RTS, Commission Delegated Regulation 2018/389) mandate Strong Customer Authentication for electronic payments within the European Economic Area. SCA requires two of three independent factors: knowledge (something the cardholder knows — PIN, password), possession (something the cardholder has — card, phone), and inherence (something the cardholder is — fingerprint, face).

**Impact on EMV card-present transactions.** Chip + PIN already satisfies SCA (possession of the card + knowledge of the PIN). Contactless below the SCA exemption threshold (EUR 50 per transaction, cumulative EUR 150 or 5 consecutive contactless transactions) does not require SCA. Above the threshold, PIN is required. Some issuers use on-device CVM (biometric) on mobile wallets to satisfy SCA for contactless above the threshold.

**Impact on card-not-present transactions.** 3DS 2.0 (§8.1) is the primary mechanism for SCA compliance in e-commerce. Exemptions include: low-value transactions (under EUR 30, subject to cumulative limits), trusted beneficiaries (whitelisted merchants), recurring payments (SCA required for the first payment, not subsequent), and Transaction Risk Analysis (TRA — the acquirer or issuer can apply an exemption if their fraud rate is below defined thresholds: < 0.13% for transactions up to EUR 100, < 0.06% for up to EUR 250, < 0.01% for up to EUR 500).

**Dynamic linking.** For remote electronic payments, PSD2 requires that the authentication code is dynamically linked to the specific amount and payee. This means the CAVV or cryptogram must bind the transaction amount and merchant identity into the authentication, preventing an attacker from replaying an authentication code for a different amount or to a different merchant. 3DS 2.0's CAVV generation includes the transaction amount and merchant in the input, satisfying this requirement.

### 8.5 Post-quantum considerations for payment cryptography

EMV's current cryptographic foundation relies on RSA (1024–2048 bit keys for ODA certificates) and 3DES/AES (for symmetric cryptogram computation and PIN encryption). A cryptographically relevant quantum computer (CRQC) would break RSA via Shor's algorithm and reduce the effective security of symmetric keys via Grover's algorithm (halving the key strength — AES-128 → 64-bit effective, AES-256 → 128-bit effective).

**RSA vulnerability timeline.** EMV ODA certificates use RSA-1024 (some networks) or RSA-2048. RSA-1024 is already considered weak against classical attacks; RSA-2048 is estimated to require approximately 4,000 logical qubits to break. Current quantum computers are far from this capability, but the "harvest now, decrypt later" threat model applies less to EMV than to long-lived encrypted data, because EMV authentication is real-time and session-bound (an ARQC or ODA signature has no value after the transaction completes). However, the CA certificates and Issuer certificates have multi-year validity; a CRQC that can factor the CA modulus would allow forging Issuer and ICC certificates, enabling the creation of counterfeit cards that pass ODA.

**Symmetric key impact.** 3DES (used for ARQC in many deployed systems) already has a 112-bit effective key length; Grover's algorithm would reduce this to ~56 bits, making it trivially breakable. AES-128 (increasingly used in newer EMV specifications) would be reduced to 64-bit effective — uncomfortably close to brute-force range. AES-256 would retain 128-bit effective security, which is sufficient.

**Migration path.** EMVCo and the PCI Security Standards Council have begun evaluating post-quantum algorithms. The likely approach: (1) migrate symmetric cryptography from 3DES to AES-256 (already underway — EMV specifications support AES-based session keys and CMAC), (2) migrate ODA certificates from RSA to a post-quantum digital signature scheme (ML-DSA / CRYSTALS-Dilithium, standardized as FIPS 204, is the leading candidate — but the signature sizes are significantly larger than RSA, impacting card storage and APDU transfer times), and (3) migrate PIN encryption from 3DES to AES (ISO 9564 Format 4, §6.2, already addresses this).

**Concrete size impact on EMV APDUs.** The current RSA-2048 Issuer PK Certificate (tag `0x90`) is 256 bytes — fitting comfortably within a single READ RECORD response (max ~253 bytes for a single record in SFI, but the certificate is split across the record value and the remainder tag `0x92`). ML-DSA-65 (NIST security level 3, comparable to RSA-2048 security): the public key is 1952 bytes and the signature is 3293 bytes. This would require either: chaining across many READ RECORD responses (increasing transaction time), expanding the APDU length limits (requiring T=1 extended-length APDUs or ISO 7816-4 extended-length fields), or using a hybrid approach (classical RSA signature for backward compatibility plus a post-quantum signature for forward security, doubling the total certificate data).

SLH-DSA (SPHINCS+, the stateless hash-based alternative) has even larger signatures (up to 49,856 bytes for security level 5), making it impractical for on-card storage within current EMV APDU constraints. The most likely candidate remains ML-DSA-44 (security level 2: 1312-byte public key, 2420-byte signature), which is the smallest post-quantum signature scheme standardized by NIST while still providing adequate security margins.

The card ecosystem's replacement cycle is slow (cards have 3–5 year lifespans, terminals have 7–10 year lifespans), so the migration will likely be phased: AES for symmetric operations first (achievable via firmware updates to terminals and new card personalization), post-quantum signatures for ODA second (requires new CA infrastructure, new card chip hardware with larger memory for ML-DSA keys and signatures, and terminal firmware updates to support the new algorithms). EMVCo's Post-Quantum Cryptography Working Group (established 2023) is evaluating hybrid signature schemes as a transition mechanism, allowing terminals to verify either the classical or the post-quantum signature during the migration period.

---

## 9. EMV contactless — expanded

### 9.1 Contactless communication (ISO 14443)

EMV contactless uses ISO 14443 (13.56 MHz NFC). Two types: Type A (modified Miller encoding, 100% ASK modulation — used by most payment cards) and Type B (NRZ-L encoding, 10% ASK — used by some). The reader powers the card via the RF field (passive card — no battery); the card communicates by load-modulating the field.

The contactless activation sequence: the reader sends `REQA`/`REQB` (Request commands), cards respond with `ATQA`/`ATQB` (Answer to Request). Anticollision resolves multiple cards. `SELECT` selects one card. `RATS` (Request for Answer to Select) initiates the T=CL (contactless transport) protocol. After RATS, APDU communication proceeds identically to contact — the same SELECT, GPO, READ RECORD, GENERATE AC commands.

### 9.2 EMV Contactless Kernels

Different payment networks define different contactless transaction optimizations: **Kernel 2 (Mastercard)**: supports full EMV mode (online and offline transactions, ODA, CVM). **Kernel 3 (Visa)**: supports qVSDC (quick Visa Smart Debit/Credit — a streamlined flow where the card generates the cryptogram in the GPO response) and full EMV mode. **Kernel 4 (Amex)**: ExpressPay, similar to qVSDC. **Kernel 5 (JCB)**: J/Speedy. **Kernel 6 (Discover)**: D-PAS. **Kernel 7 (UnionPay)**: QuickPass.

**qVSDC flow.** The card generates a cryptogram (fDDA — Fast DDA, a dynamic signature over a card-generated nonce and the unpredictable number) in the GPO response itself. The terminal does not need to send READ RECORD or GENERATE AC — the GPO response contains everything needed for a single-tap online transaction. This reduces the number of APDUs from ~6-8 (full EMV) to 2 (SELECT + GPO), enabling the "tap and go" experience.

**MSD (Magnetic Stripe Data) contactless.** The card provides Track 1/2 equivalent data plus a dynamic CVC3 (computed from the ATC and a card key). Each transaction has a unique CVC3, preventing simple replay. However, MSD contactless lacks the full EMV security model (no ODA, no full cryptogram, limited issuer-authentication capability). MSD is being phased out.

### 9.3 Contactless CVM limits

Below the CVM limit (varies by country and card network: US $100, EU €50, UK £100, Australia AUD$200), contactless transactions typically proceed with "No CVM" — no PIN, no signature. Above the limit, the terminal requests PIN (the cardholder may need to insert the card for contact-mode PIN entry, or enter PIN on the terminal's keypad if "Contactless + PIN" is supported). Some card networks support "on-device CVM" (CDCVM — Consumer Device CVM) for mobile payments: the phone's biometric (Face ID, fingerprint) satisfies the CVM requirement even above the limit.

---

## 10. Detection and defense architecture

### 10.1 Issuer-side transaction monitoring

The issuer receives (via the acquirer and card network) the full EMV data for every online transaction: ARQC, ATC, TVR, CVM Results, IAD (including card verification results and internal counters), Terminal Country Code, Transaction Amount and Currency, POS Entry Mode, and the Unpredictable Number.

Fraud-detection rules: **ATC gaps** (missing ATCs indicate transactions the issuer didn't see — potential offline fraud or pre-play), **CVM downgrade** (a chip transaction without PIN from a PIN-required card), **geographic velocity** (two transactions in different countries with insufficient travel time), **amount velocity** (rapid successive transactions), **offline-counter anomalies** (the card's offline transaction count or cumulative amount exceeding expected limits), and **service-code mismatch** (a mag-stripe transaction from a chip-capable card).

Real-time machine-learning models (Random Forest, neural networks, GBMs) evaluate transactions on: velocity features, geographic features, amount features, merchant-category features, cardholder-behavior features (time of day, transaction frequency, typical merchants), and device features (for mobile payments). The model outputs a risk score; transactions above a threshold are declined or sent for additional verification (3D Secure — cardholder authentication via the issuing bank's interface).

### 10.2 Terminal and network hardening

Terminal physical security: PCI PTS certification (tamper-detection mesh in the PIN pad, key zeroization on tamper, active shields — Domain 17 §2 for the physical techniques). Terminal software security: signed firmware, application whitelisting, secure boot, and encrypted communication with the acquirer. Network security: TLS/VPN for the terminal-to-acquirer connection, ISO 8583 message authentication (MAC on each message using the terminal's session key), and terminal management authentication (the remote-management system must authenticate to the terminal using mutual TLS or a management key).

### 10.3 EMV data in fraud detection — IAD and CVR cross-checks

The most underutilized fraud-detection signal is the cross-check between terminal-reported CVM results (tag `0x9F34`) and card-reported CVR (in tag `0x9F10` — Issuer Application Data). The IAD contains the Cryptogram Version Number (bits identifying the key derivation scheme), the Card Verification Results (a bitfield recording what the card observed: PIN try counter, offline data authentication result, whether offline PIN was attempted, last online ATC), and the DAC (Derivation Data for the Application Cryptogram).

When a wedge or shim modifies the CVM result visible to the terminal, the card's CVR will reflect the truth. For example: the terminal reports CVM result = "online PIN verified" (tag `0x9F34` = `02 05 02`), but the card's CVR in the IAD records "no CVM performed" or "PIN verification not attempted." An issuer rule that compares these two fields catches CVM bypass attacks that shims and wedges enable. This cross-check is recommended by all major card networks but is not universally implemented by issuers.

---

## 11. EMV Protocol Analysis and Tooling

### 11.1 Smart card development environment

JavaCard is the dominant platform for EMV applet development and security research. The JavaCard SDK (version 3.1 as of 2025) provides a development kit that compiles standard Java source into CAP (Converted Applet) files suitable for deployment onto smart card hardware. The compilation pipeline proceeds from `.java` source through the JavaCard converter, which produces a `.cap` file containing the applet bytecode, a `.exp` export file for inter-package linking, and a `.jca` human-readable assembly listing. The converter enforces a restricted Java subset: no multithreading, no garbage collection, no floating point, no large object graphs. The resulting applet runs inside the JCRE (JavaCard Runtime Environment) on the card, which provides isolation between applets via the firewall mechanism — each applet context has its own object space, and cross-context access is mediated by shareable interface objects (SIOs).

GlobalPlatform (GP) defines the card management framework that governs applet lifecycle operations: installation, deletion, locking, and key management. The GP card manager exposes an ISD (Issuer Security Domain) that authenticates the card administrator before allowing privileged operations. Communication with the ISD uses Secure Channel Protocol (SCP02 or SCP03). SCP02 uses 3DES-CBC for encryption and 3DES-CBC-MAC for command authentication. SCP03 migrates to AES-128-CBC for encryption and AES-CMAC for authentication, providing a stronger security margin. A typical GP session proceeds through INITIALIZE UPDATE (the card returns a card challenge and key diversification data), EXTERNAL AUTHENTICATE (the host proves knowledge of the session keys derived from the static keys and the challenges), and then any subsequent command APDUs are wrapped in a secure messaging envelope (MAC and optionally encrypted).

The GlobalPlatform key hierarchy consists of three base keys stored in the ISD: the S-ENC key (for session encryption), the S-MAC key (for command authentication), and the DEK key (for sensitive data encryption, such as new key injection). These base keys are diversified per card using the card's unique identifier (typically the CPLC — Card Production Life Cycle data). During SCP03 session establishment, session keys are derived from the base keys and the host/card challenges using a KDF based on the NIST SP 800-108 counter-mode construction with AES-CMAC as the PRF.

Applet deployment follows a strict sequence: INSTALL [for load] (prepares the card to receive a package), LOAD (transmits the CAP file in multiple APDU blocks), and INSTALL [for install and make selectable] (instantiates the applet and registers its AID). Each step is authenticated via the secure channel. The DAP (Data Authentication Pattern) verification, when enabled, requires the CAP file to carry a signature from a trusted authority — the card verifies this signature before allowing installation. DAP prevents unauthorized applet sideloading, which is critical for payment card security because a malicious applet could attempt to access another applet's data via SIO abuse or exploit JCRE vulnerabilities.

### 11.2 Proxmark3 for EMV protocol interaction

The Proxmark3 (RDV4 or Easy variant with firmware from the Iceman fork) is the primary tool for contact and contactless smart card research. For EMV analysis within an authorized test environment, the following commands interact with a payment card's chip:

```
# Scan for contactless cards in the field
pm3 --> hf search

# Read the full ATR and card metadata from a contact card (via the SIM-sized smart card slot)
pm3 --> smart info

# Select the PSE (Payment System Environment) on a contact card
pm3 --> smart apdu -s 00A4040007A000000003101000
# The -s flag enables auto-detection of T=0/T=1 transport

# Select the PPSE on a contactless card
pm3 --> hf emv ppse

# Full EMV transaction sequence (contactless): select, GPO, read records
pm3 --> hf emv exec
# This automates: PPSE select -> AID select -> GPO -> READ RECORD for all AFL entries
# Output includes parsed TLV with tag names, AIP, AFL, PAN, expiry, and all record data

# Select a specific AID manually (Visa: A0000000031010)
pm3 --> hf emv select -s A0000000031010

# Send GET PROCESSING OPTIONS with a manually constructed PDOL
# Example: PDOL data = 83 1C + PDOL values (28 bytes for a typical Mastercard PDOL)
pm3 --> hf emv gpo -d 831CB6204000000000001000000000000000084008402605080000000000

# Read a specific record: SFI 1, record 1 (P2 = SFI<<3 | 0x04 = 0x0C)
pm3 --> hf emv readrec -s 1 -n 1
# Equivalent raw APDU:
pm3 --> smart apdu 00B2010C00

# Send GENERATE APPLICATION CRYPTOGRAM (request ARQC, P1=0x80)
# with CDOL1 data (example: 32 bytes per §4.5)
pm3 --> smart apdu 80AE800020000000001000000000000000084000000000000840260508007AE391F222000000

# Read the card's internal transaction log (tag 9F4D specifies SFI and record count)
# If 9F4D = 0B 0A (SFI 11 = 0x58>>3, 10 records):
pm3 --> smart apdu 00B2015C00
pm3 --> smart apdu 00B2025C00
# ... through record 10
```

The `hf emv exec` command produces a complete dump of the card's public EMV data, including all records from every SFI listed in the AFL. The output is TLV-parsed with human-readable tag names. This data is sufficient to analyze the card's ODA configuration (SDA/DDA/CDA support from AIP), CVM list, CDOL structure, and certificate chain. The private key material and master keys remain inaccessible — they never leave the chip's secure element.

For contact-mode interaction, the Proxmark3's SIM slot accepts full-size ISO 7816 cards. The `smart` command family handles ATR parsing, T=0/T=1 protocol negotiation, and raw APDU exchange. For extended-length APDUs (needed when reading large certificates), the `smart apdu -t` flag enables T=1 chaining.

### 11.3 libnfc and PC/SC middleware

The libnfc library provides low-level access to NFC readers compliant with ISO 14443. On Linux, the typical setup for EMV contactless research uses an ACR122U or SCL3711 reader:

```bash
# Install libnfc and tools (Debian/Ubuntu)
sudo apt install libnfc-dev libnfc-bin

# Scan for NFC devices and cards in the field
nfc-list

# Poll for an ISO 14443-A card (most EMV contactless cards)
nfc-poll

# Send raw APDUs via nfc-tools (select PPSE)
# libnfc does not provide high-level EMV commands; use nfc-relay-picc for relay research
# or build custom tools using the libnfc C API
```

PC/SC (Personal Computer / Smart Card) is the standard middleware for contact smart card readers. On Linux, the pcscd daemon manages reader access. Key tools in the PC/SC ecosystem:

```bash
# Install PC/SC tools
sudo apt install pcscd pcsc-tools opensc

# Start the PC/SC daemon
sudo systemctl start pcscd

# Scan for connected readers and inserted cards
pcsc_scan
# Output: reader name, ATR, card type detection (using the ATR database)

# List available PKCS#11 slots and tokens
pkcs11-tool --list-slots

# Use opensc-tool for card interaction
opensc-tool --atr          # Display the card's ATR
opensc-tool --serial       # Display the card's serial number
opensc-tool --send-apdu 00A4040007A000000003101000  # Send raw APDU (SELECT Visa AID)
```

The `scriptor` tool (part of the pcsc-tools package) provides an interactive shell for sending APDUs to a card through the PC/SC stack. Each command is a hex-encoded APDU; the tool displays the response APDU with status words:

```bash
# Interactive APDU session
scriptor
> 00 A4 04 00 0E 31 50 41 59 2E 53 59 53 2E 44 44 46 30 31 00
< 6F 1E 84 0E ... 90 00
> 00 B2 01 0C 00
< 70 23 61 21 ... 90 00
> CTRL+D to exit
```

### 11.4 Python scripting for EMV analysis

The following Python module demonstrates automated EMV card reading, TLV parsing, and data extraction using the pyscard library (which wraps the PC/SC middleware). This code reads a card's public EMV data, parses the FCI and records, and extracts the PAN, expiry, and cardholder name.

```python
"""
EMV Card Reader — automated data extraction via PC/SC.
Requires: pip install pyscard
Requires: pcscd running, smart card reader connected, EMV card inserted.
"""
from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from typing import Optional

# --- EMV Tag Dictionary (subset) ---
EMV_TAGS = {
    0x4F: "Application Identifier (AID)",
    0x50: "Application Label",
    0x57: "Track 2 Equivalent Data",
    0x5A: "Application PAN",
    0x5F20: "Cardholder Name",
    0x5F24: "Application Expiration Date",
    0x5F25: "Application Effective Date",
    0x5F28: "Issuer Country Code",
    0x5F2A: "Transaction Currency Code",
    0x5F2D: "Language Preference",
    0x5F34: "PAN Sequence Number",
    0x61: "Application Template",
    0x6F: "FCI Template",
    0x70: "EMV Record Template",
    0x77: "Response Message Template (Format 2)",
    0x80: "Response Message Template (Format 1)",
    0x82: "Application Interchange Profile (AIP)",
    0x84: "DF Name",
    0x87: "Application Priority Indicator",
    0x88: "SFI of the Directory (PSE)",
    0x8C: "CDOL1",
    0x8D: "CDOL2",
    0x8E: "CVM List",
    0x90: "Issuer PK Certificate",
    0x92: "Issuer PK Remainder",
    0x93: "Signed Static Application Data",
    0x94: "Application File Locator (AFL)",
    0x95: "Terminal Verification Results (TVR)",
    0x9A: "Transaction Date",
    0x9C: "Transaction Type",
    0x9F07: "Application Usage Control",
    0x9F08: "Application Version Number (Card)",
    0x9F0D: "Issuer Action Code - Default",
    0x9F0E: "Issuer Action Code - Denial",
    0x9F0F: "Issuer Action Code - Online",
    0x9F10: "Issuer Application Data (IAD)",
    0x9F12: "Application Preferred Name",
    0x9F26: "Application Cryptogram",
    0x9F27: "Cryptogram Information Data",
    0x9F32: "Issuer PK Exponent",
    0x9F36: "Application Transaction Counter (ATC)",
    0x9F37: "Unpredictable Number",
    0x9F38: "PDOL",
    0x9F42: "Application Currency Code",
    0x9F44: "Application Currency Exponent",
    0x9F46: "ICC PK Certificate",
    0x9F47: "ICC PK Exponent",
    0x9F48: "ICC PK Remainder",
    0x9F49: "DDOL",
    0x9F4A: "Static Data Authentication Tag List",
    0x9F4B: "Signed Dynamic Application Data",
    0x9F4D: "Log Entry",
    0x9F4F: "Log Format",
    0x9F6C: "Card Transaction Qualifiers (CTQ)",
    0xA5: "FCI Proprietary Template",
    0xBF0C: "FCI Issuer Discretionary Data",
}

# Tags that contain nested TLV (constructed tags)
CONSTRUCTED_TAGS = {0x61, 0x6F, 0x70, 0x77, 0xA5, 0xBF0C}


def parse_tag(data: bytes, offset: int) -> tuple[int, int]:
    """Parse a BER-TLV tag. Returns (tag_value, bytes_consumed)."""
    if offset >= len(data):
        raise ValueError(f"Tag parse: offset {offset} past end of data ({len(data)} bytes)")
    first = data[offset]
    if (first & 0x1F) == 0x1F:
        # Two-byte tag
        if offset + 1 >= len(data):
            raise ValueError("Two-byte tag truncated")
        tag = (first << 8) | data[offset + 1]
        return tag, 2
    return first, 1


def parse_length(data: bytes, offset: int) -> tuple[int, int]:
    """Parse a BER-TLV length. Returns (length_value, bytes_consumed)."""
    if offset >= len(data):
        raise ValueError(f"Length parse: offset {offset} past end")
    first = data[offset]
    if first <= 0x7F:
        return first, 1
    if first == 0x81:
        return data[offset + 1], 2
    if first == 0x82:
        return (data[offset + 1] << 8) | data[offset + 2], 3
    raise ValueError(f"Unsupported length encoding: 0x{first:02X}")


def parse_tlv(data: bytes, depth: int = 0) -> list[dict]:
    """Recursively parse BER-TLV data into a list of tag-value dicts."""
    result = []
    offset = 0
    while offset < len(data):
        if data[offset] == 0x00:
            offset += 1
            continue
        tag, tag_len = parse_tag(data, offset)
        offset += tag_len
        length, len_len = parse_length(data, offset)
        offset += len_len
        value = data[offset:offset + length]
        offset += length

        tag_name = EMV_TAGS.get(tag, f"Unknown (0x{tag:02X})")
        entry = {"tag": tag, "tag_hex": f"0x{tag:04X}" if tag > 0xFF else f"0x{tag:02X}",
                 "name": tag_name, "length": length, "value": value.hex().upper()}

        if tag in CONSTRUCTED_TAGS:
            entry["children"] = parse_tlv(value, depth + 1)

        result.append(entry)
    return result


def send_apdu(connection, apdu_hex: str) -> tuple[bytes, int, int]:
    """Send an APDU and return (data, SW1, SW2). Handles GET RESPONSE for 0x61XX."""
    apdu = toBytes(apdu_hex)
    data, sw1, sw2 = connection.transmit(apdu)

    # Handle T=0 Case 4: card says "61 XX" — issue GET RESPONSE
    while sw1 == 0x61:
        get_resp = toBytes(f"00 C0 00 00 {sw2:02X}")
        more_data, sw1, sw2 = connection.transmit(get_resp)
        data.extend(more_data)

    return bytes(data), sw1, sw2


def read_emv_card() -> Optional[dict]:
    """Connect to the first available reader and extract EMV card data."""
    available = readers()
    if not available:
        print("No smart card readers found.")
        return None

    reader = available[0]
    print(f"Using reader: {reader}")
    connection = reader.createConnection()
    connection.connect()
    atr = toHexString(connection.getATR())
    print(f"ATR: {atr}")

    card_data = {"atr": atr, "applications": []}

    # Step 1: SELECT PSE
    pse_apdu = "00 A4 04 00 0E 31 50 41 59 2E 53 59 53 2E 44 44 46 30 31 00"
    data, sw1, sw2 = send_apdu(connection, pse_apdu)

    if sw1 != 0x90:
        print(f"PSE not found (SW={sw1:02X}{sw2:02X}), trying known AIDs directly.")
        known_aids = [
            "A0000000041010",  # Mastercard
            "A0000000031010",  # Visa
            "A00000002501",    # Amex
            "A0000000651010",  # JCB
        ]
        for aid in known_aids:
            aid_bytes = " ".join(aid[i:i+2] for i in range(0, len(aid), 2))
            lc = len(aid) // 2
            sel_apdu = f"00 A4 04 00 {lc:02X} {aid_bytes} 00"
            data, sw1, sw2 = send_apdu(connection, sel_apdu)
            if sw1 == 0x90:
                app_info = _process_application(connection, data, aid)
                if app_info:
                    card_data["applications"].append(app_info)
        return card_data

    # Parse PSE FCI to find SFI
    fci = parse_tlv(data)
    sfi = _extract_pse_sfi(fci)
    if sfi is None:
        print("Could not extract SFI from PSE FCI.")
        return card_data

    # Step 2: READ RECORD from PSE directory
    aids = []
    for rec in range(1, 20):
        p2 = (sfi << 3) | 0x04
        rr_apdu = f"00 B2 {rec:02X} {p2:02X} 00"
        data, sw1, sw2 = send_apdu(connection, rr_apdu)
        if sw1 != 0x90:
            break
        records = parse_tlv(data)
        for entry in records:
            if entry["tag"] == 0x70:
                for child in entry.get("children", []):
                    if child["tag"] == 0x61:
                        aid = _extract_aid_from_template(child)
                        if aid:
                            aids.append(aid)

    # Step 3: SELECT each AID and read card data
    for aid in aids:
        aid_bytes = " ".join(aid[i:i+2] for i in range(0, len(aid), 2))
        lc = len(aid) // 2
        sel_apdu = f"00 A4 04 00 {lc:02X} {aid_bytes} 00"
        data, sw1, sw2 = send_apdu(connection, sel_apdu)
        if sw1 == 0x90:
            app_info = _process_application(connection, data, aid)
            if app_info:
                card_data["applications"].append(app_info)

    connection.disconnect()
    return card_data


def _extract_pse_sfi(fci: list) -> Optional[int]:
    """Walk parsed FCI TLV to find the SFI of the PSE directory (tag 0x88)."""
    for entry in fci:
        if entry["tag"] == 0x88:
            return int(entry["value"], 16)
        children = entry.get("children", [])
        result = _extract_pse_sfi(children)
        if result is not None:
            return result
    return None


def _extract_aid_from_template(template: dict) -> Optional[str]:
    """Extract AID (tag 0x4F) from an Application Template."""
    for child in template.get("children", []):
        if child["tag"] == 0x4F:
            return child["value"]
    return None


def _process_application(connection, fci_data: bytes, aid: str) -> Optional[dict]:
    """Process a selected EMV application: parse FCI, send GPO, read records."""
    fci = parse_tlv(fci_data)
    app = {"aid": aid, "fci": fci, "records": [], "pan": None,
           "expiry": None, "cardholder_name": None}

    # Extract PDOL from FCI
    pdol = _find_tag_recursive(fci, 0x9F38)

    # Construct minimal GPO data (zeros for all PDOL fields)
    if pdol:
        pdol_len = _compute_pdol_total_length(bytes.fromhex(pdol))
        gpo_data = bytes(pdol_len)
    else:
        gpo_data = b""

    # Wrap in tag 0x83
    gpo_value = bytes([0x83, len(gpo_data)]) + gpo_data
    lc = len(gpo_value)
    gpo_hex = f"80 A8 00 00 {lc:02X} " + " ".join(f"{b:02X}" for b in gpo_value) + " 00"
    data, sw1, sw2 = send_apdu(connection, gpo_hex)

    if sw1 != 0x90:
        print(f"GPO failed for AID {aid}: SW={sw1:02X}{sw2:02X}")
        return app

    gpo_parsed = parse_tlv(data)
    afl_hex = _find_tag_recursive(gpo_parsed, 0x94)
    if not afl_hex:
        return app

    afl = bytes.fromhex(afl_hex)

    # Read all records specified by AFL
    for i in range(0, len(afl), 4):
        sfi = (afl[i] >> 3) & 0x1F
        first_rec = afl[i + 1]
        last_rec = afl[i + 2]
        for rec in range(first_rec, last_rec + 1):
            p2 = (sfi << 3) | 0x04
            rr_apdu = f"00 B2 {rec:02X} {p2:02X} 00"
            data, sw1, sw2 = send_apdu(connection, rr_apdu)
            if sw1 == 0x90:
                rec_parsed = parse_tlv(data)
                app["records"].append(rec_parsed)
                # Extract key fields
                pan = _find_tag_recursive(rec_parsed, 0x5A)
                if pan:
                    app["pan"] = pan
                exp = _find_tag_recursive(rec_parsed, 0x5F24)
                if exp:
                    app["expiry"] = exp
                name = _find_tag_recursive(rec_parsed, 0x5F20)
                if name:
                    app["cardholder_name"] = bytes.fromhex(name).decode(
                        "ascii", errors="replace").strip()

    return app


def _find_tag_recursive(parsed: list, target_tag: int) -> Optional[str]:
    """Search parsed TLV recursively for a tag, return its hex value."""
    for entry in parsed:
        if entry["tag"] == target_tag:
            return entry["value"]
        children = entry.get("children", [])
        result = _find_tag_recursive(children, target_tag)
        if result is not None:
            return result
    return None


def _compute_pdol_total_length(pdol_bytes: bytes) -> int:
    """Sum the lengths declared in a DOL (tag-length pairs without values)."""
    total = 0
    offset = 0
    while offset < len(pdol_bytes):
        if (pdol_bytes[offset] & 0x1F) == 0x1F:
            offset += 2  # two-byte tag
        else:
            offset += 1  # one-byte tag
        if offset < len(pdol_bytes):
            total += pdol_bytes[offset]
            offset += 1
    return total


if __name__ == "__main__":
    result = read_emv_card()
    if result:
        for app in result.get("applications", []):
            print(f"\nAID: {app['aid']}")
            if app.get("pan"):
                print(f"PAN: {app['pan']}")
            if app.get("expiry"):
                print(f"Expiry: {app['expiry']}")
            if app.get("cardholder_name"):
                print(f"Name: {app['cardholder_name']}")
```

### 11.5 Wireshark EMV dissection

Wireshark can dissect EMV APDU traffic when the communication is captured through a spy reader (a hardware device that taps the I/O line between the card and terminal, outputting the serial data to a USB interface). The Omnikey CardMan 6321 in "transparent" mode, or a purpose-built ISO 7816 tap device, feeds the raw APDU exchange to the host. Wireshark's built-in ISO 7816 dissector parses the APDUs at the transport layer (T=0 procedure bytes, T=1 block framing), and the EMV protocol dissector (available as a Lua plugin or via the `emv` protocol filter in recent builds) parses the TLV data within the APDU payloads.

To capture EMV traffic with Wireshark:

```
1. Connect the spy reader to the host via USB.
2. Start Wireshark, select the USB interface corresponding to the reader.
3. Apply the display filter: iso7816 || emv
4. Insert the card into the terminal (with the spy reader inline).
5. The capture shows each APDU: SELECT, GPO, READ RECORD, GENERATE AC, VERIFY, EXTERNAL AUTHENTICATE.
6. Click on any APDU to see the TLV-parsed payload in the packet detail pane.
7. Export the parsed EMV data: File → Export Packet Dissections → As JSON.
```

The Lua dissector for EMV TLV parsing can be extended to decode issuer-proprietary tags within the IAD (tag `0x9F10`). Mastercard's IAD structure (CVN 10/17/18) encodes the CVR (Card Verification Results) in specific byte positions, and Visa's IAD encodes the CVN and derivation data. A custom Lua script that decodes these proprietary structures significantly accelerates forensic analysis of captured transactions.

For researchers who need to capture contactless EMV traffic without a hardware tap, the Proxmark3's `hf 14a sniff` command captures the RF-level communication between a legitimate reader and card. The captured frames include the full APDU exchange (after ISO 14443-4 framing is stripped), which can be exported to a PCAP file and loaded into Wireshark for dissection.

### 11.6 JavaCard exploitation

JavaCard's security model relies on the bytecode verifier (which runs either on-card or off-card during CAP file conversion) and the firewall (which enforces applet isolation at runtime). Exploitation of JavaCard targets weaknesses in both mechanisms.

**Buffer overflow in applets.** JavaCard does not provide automatic bounds checking on all array operations in the same way that full Java does. When the on-card bytecode verifier is absent or incomplete (some older cards skip verification for performance), a malicious applet can craft array operations that read or write beyond the allocated buffer. For example, an applet that calls `Util.arrayCopy(src, (short)0, dst, (short)0, (short)300)` where `dst` is only 256 bytes long will overwrite adjacent memory if the verifier did not catch the length mismatch. On cards without hardware memory protection (MMU), this overwrite can corrupt another applet's data or the JCRE's internal structures.

**Type confusion across package boundaries.** The classic "type confusion" attack (Barbu et al., 2010; Lancia, 2012) exploits the fact that JavaCard's firewall checks are based on the applet context, not the package context. If two applets in different packages share an interface, and one applet passes an object reference to the other through a shareable interface object, the receiving applet may cast the reference to a different type than the sender intended. If the bytecode verifier does not fully validate type consistency across package boundaries, the attacker gains the ability to reinterpret object fields — reading a `short` field as an object reference, or vice versa. This enables reading arbitrary memory (by fabricating an array header with a large length field) or calling arbitrary methods (by fabricating a method table entry). CVE-2019-16929 documented a type confusion flaw in a widely deployed JavaCard implementation that allowed a malicious applet installed on the card to read the private key material of other applets, including the EMV payment applet's ICC private key.

**Transaction rollback attacks.** JavaCard provides an atomic transaction mechanism: `JCSystem.beginTransaction()` and `JCSystem.commitTransaction()`. If the card loses power between begin and commit, the JCRE rolls back all changes made during the transaction. An attacker can exploit this: trigger a transaction that decrements a counter (e.g., the PIN try counter or offline transaction counter), then deliberately reset the card (by cutting power) before the commit. The counter reverts to its pre-transaction value. Repeated resets allow unlimited PIN attempts or unlimited offline transactions. The defense is to design counter decrements to commit atomically before the operation that depends on them — decrement first, commit, then perform the sensitive operation. If the card resets after the decrement but before the operation, the counter is decremented but the operation did not occur, which is the safe failure mode.

**GlobalPlatform key extraction.** If an attacker obtains the static keys of the ISD (through supply-chain compromise, insider threat, or side-channel attack on the key injection facility), they can establish a secure channel to the card and install arbitrary applets. The installed applet can then exploit JCRE vulnerabilities (type confusion, buffer overflow) to extract the EMV payment applet's key material. This attack chain — key compromise → applet installation → JCRE exploit → key extraction — is the most severe threat to the JavaCard security model. Mitigation: hardware security modules (HSMs) for key injection with strict dual-control procedures, GP DAP verification to prevent unauthorized applet installation, and regular security evaluation of the JavaCard platform against the Common Criteria (CC EAL4+ or EAL5+ for payment cards).

---

## 12. EMV Forensics and Fraud Investigation

### 12.1 Card-present fraud forensics

#### 12.1.1 Transaction log analysis

EMV cards maintain an on-card transaction log whose format is defined by tag `0x9F4F` (Log Format) and whose location is specified by tag `0x9F4D` (Log Entry — SFI and record count). The log records the most recent N transactions (typically 10-20), each containing the data elements specified in the Log Format DOL: Amount Authorized (`0x9F02`), Transaction Date (`0x9A`), Transaction Currency Code (`0x5F2A`), Terminal Country Code (`0x9F1A`), ATC (`0x9F36`), and often the Cryptogram Information Data (`0x9F27`) indicating whether the transaction was approved online (ARQC→TC), offline (TC directly), or declined (AAC).

Reading the transaction log from a recovered card provides a forensic timeline of the card's recent usage. The ATC values in the log, compared against the issuer's authorization records, reveal gaps that indicate unrecorded transactions — a hallmark of offline-only fraud (e.g., a cloned card used at an offline-capable terminal) or pre-play attacks (§7.1). The terminal country codes in the log, cross-referenced with the cardholder's known travel history, identify geographically anomalous transactions.

```
# Read transaction log using Proxmark3 (SFI 11 = 0x58>>3, record 1-10)
pm3 --> smart apdu 00B2015C00
pm3 --> smart apdu 00B2025C00
pm3 --> smart apdu 00B2035C00
# ... through record 10

# Parse the log: each record is encoded per the Log Format DOL.
# Example Log Format (tag 9F4F):
#   9F02 06 9A 03 5F2A 02 9F1A 02 9F27 01 9F36 02
# Total: 6+3+2+2+1+2 = 16 bytes per record
```

To automate log extraction and parsing, the Python EMV reader from §11.4 can be extended to read tag `0x9F4F` from the card's records, then read the log SFI and decode each record according to the Log Format DOL.

#### 12.1.2 Terminal audit trail analysis

Compromised terminals leave identifiable patterns in acquirer transaction logs. A terminal that has been fitted with a shim or wedge device (§7.3, §7.5) exhibits characteristic anomalies: an elevated rate of CVM downgrades (transactions that should require PIN proceeding with signature or no CVM), an increased incidence of specific status word errors (repeated `63 CX` responses suggesting PIN brute-forcing), and sudden changes in the ratio of contact-to-contactless transactions (indicating hardware modification).

Acquirer fraud analysts query transaction databases for terminals exhibiting these patterns:

```sql
-- Identify terminals with abnormal CVM downgrade rates
-- CVM Results (tag 9F34) byte 1: 0x1F = no CVM, 0x1E = signature
-- Expected for a chip-and-PIN terminal: >90% PIN transactions above CVM limit
SELECT terminal_id,
       COUNT(*) AS total_txns,
       SUM(CASE WHEN cvm_result_byte1 IN (0x1F, 0x1E)
                 AND amount > cvm_limit THEN 1 ELSE 0 END) AS downgraded_txns,
       ROUND(100.0 * SUM(CASE WHEN cvm_result_byte1 IN (0x1F, 0x1E)
                                    AND amount > cvm_limit THEN 1 ELSE 0 END)
             / COUNT(*), 2) AS downgrade_pct
FROM emv_transactions
WHERE txn_date BETWEEN '2026-04-01' AND '2026-05-01'
GROUP BY terminal_id
HAVING downgrade_pct > 20.0
ORDER BY downgrade_pct DESC;
```

#### 12.1.3 Shimming device forensics

When a shimming device is recovered from a terminal during physical inspection, the forensic examination proceeds through several phases. The physical examination documents the device dimensions (typically 0.08-0.12mm thick, matching the ISO 7816 contact array dimensions), the contact layout (which contacts are tapped — at minimum C7/I-O for data, often C1/VCC and C5/GND for power), and the presence of storage components (flash memory for captured data) or communication interfaces (Bluetooth Low Energy for wireless data exfiltration).

The electronics examination identifies the microcontroller (commonly an STM32F0 or ATtiny series for passive shims, ARM Cortex-M4 for active wedge devices), the firmware storage (internal flash or external SPI flash), and any communication modules. The firmware is extracted via JTAG or SWD debug interfaces (if not fused) or via flash chip desoldering and direct read. Firmware reverse engineering reveals the APDU filtering logic — which commands the shim records (typically READ RECORD responses containing PAN and Track 2 data, and VERIFY commands containing the PIN block) — and any modification logic (replacing status words for CVM bypass).

The captured data is recovered from the storage component. The shim's memory layout typically stores transactions sequentially: each entry containing a timestamp (from the shim's RTC or a counter), the PAN, expiry, Track 2 equivalent data, and (if offline plaintext PIN was used) the PIN. The examiner must maintain chain of custody: photograph the device in situ before removal, document with UTC ISO 8601 timestamps, compute SHA-256 hashes of firmware dumps and extracted data, and store the physical device in a tamper-evident evidence bag.

#### 12.1.4 Relay attack forensics

Relay attacks (§7.2) introduce measurable timing anomalies that serve as forensic indicators. A legitimate contactless transaction completes the full APDU sequence (SELECT → GPO → READ RECORD → GENERATE AC) in 200-500 ms, depending on the card and terminal. A relayed transaction adds the network round-trip time for each APDU relay, typically adding 100-800 ms total (depending on the relay channel — Wi-Fi adds less latency than mobile data).

Forensic identification of relayed transactions requires access to the terminal's detailed timing logs (not all terminals record per-APDU timing). When available, the analysis compares the total transaction time and individual command-response intervals against the terminal's baseline for the same card type. A transaction where the GPO response took 350 ms instead of the typical 80-120 ms, and the READ RECORD responses each took 200 ms instead of 30-50 ms, exhibits the characteristic latency inflation of a relay.

An additional forensic indicator is the geographic impossibility test: the cardholder's legitimate card was used at Terminal A at time T1, and the relayed transaction occurred at Terminal B at time T2, where the physical distance between A and B is incompatible with the elapsed time T2-T1 given any plausible mode of transportation. This analysis requires correlating the issuer's transaction log (which contains terminal location data from the acquirer) with the card's on-card transaction log (which records ATC values sequentially).

### 12.2 Card-not-present fraud investigation

#### 12.2.1 BIN attack detection

A BIN (Bank Identification Number) attack systematically tests card numbers within a BIN range to identify valid cards. The attacker generates sequential or random PANs within a target BIN (the first 6-8 digits identify the issuing bank), computes the Luhn check digit to ensure syntactic validity, and submits low-value authorization requests (typically USD $0.01 or $1.00) to e-commerce merchants with weak fraud controls. Valid PANs that return authorization approval codes are harvested for subsequent fraudulent purchases.

Detection patterns in authorization logs:

```
Indicators of BIN attack:
- High volume of authorization requests from a single merchant in a short timeframe
- Sequential or near-sequential PAN values across requests
- Uniform low amounts (e.g., all $1.00 or $0.00 authorization-only)
- High decline ratio (>80% of attempts declined)
- Declined reasons concentrated on "invalid card number" (response code 14)
  or "insufficient funds" (response code 51)
- Requests from a small set of IP addresses or device fingerprints
- Absence of 3DS authentication (attacker targets merchants without 3DS)
```

Issuer-side detection analyzes declined authorization logs for clusters of requests against PANs within the same BIN range that were never issued. The pattern is distinctive: legitimate declines are scattered across BIN ranges; BIN attacks produce dense clusters within a single range with a high proportion of "invalid card number" declines.

#### 12.2.2 3DS bypass techniques and forensic indicators

Attackers bypass 3DS authentication through several vectors, each leaving forensic traces:

The merchant-side bypass exploits merchants that have not implemented 3DS or that apply exemptions aggressively. The forensic indicator is the ECI (Electronic Commerce Indicator) value in the authorization message: ECI=07 (Visa) or ECI=00 (Mastercard) indicates no 3DS authentication was attempted, while ECI=05/02 indicates a fully authenticated transaction. A pattern of fraudulent transactions concentrated on ECI=07/00 merchants suggests the attacker deliberately targets non-3DS merchants.

The real-time phishing proxy attack intercepts the 3DS challenge: the attacker operates a phishing site that mirrors the merchant checkout, initiates a real 3DS authentication flow with the victim's card, and proxies the challenge (OTP or biometric prompt) to the victim in real time. The victim believes they are authenticating a legitimate purchase. The forensic indicator is a mismatch between the merchant name shown to the cardholder during the challenge (the real merchant) and the merchant the cardholder believed they were purchasing from. ACS logs record the merchant name, transaction amount, and challenge delivery channel — discrepancies in these fields, combined with cardholder dispute statements, identify the proxy attack.

### 12.3 Issuer-side forensic capabilities

#### 12.3.1 Authorization log analysis

The issuer's authorization system records every authorization request and response, including the full EMV data transmitted in DE55 (tag-length-value encoded). Forensic queries against this data reveal:

Declined transaction clustering: a burst of declined authorizations against a single PAN, all with response code 55 (incorrect PIN) or 14 (invalid card number), indicates credential testing. The time distribution of these declines (e.g., 50 attempts in 2 minutes) distinguishes automated attacks from manual cardholder errors (which are spaced minutes or hours apart).

CVV/CVC mismatch patterns: for card-not-present transactions, the CVV2/CVC2 (the 3-digit code on the card back) is verified by the issuer. A pattern of transactions with correct PAN and expiry but incorrect CVV2 indicates the attacker obtained the card number (from a breach or BIN attack) but not the CVV2. The forensic analyst queries for PANs with high CVV2 mismatch rates:

```sql
-- Identify PANs under active credential testing (CVV2 brute-force)
SELECT pan_hash, COUNT(*) AS attempts,
       SUM(CASE WHEN cvv2_result = 'N' THEN 1 ELSE 0 END) AS cvv_mismatches,
       MIN(auth_timestamp) AS first_attempt,
       MAX(auth_timestamp) AS last_attempt
FROM authorizations
WHERE auth_date = '2026-05-13'
  AND pos_entry_mode IN ('010', '011')  -- e-commerce
GROUP BY pan_hash
HAVING cvv_mismatches >= 3 AND attempts <= 20
ORDER BY cvv_mismatches DESC;
```

#### 12.3.2 Script command forensics

When the issuer sends issuer scripts (tag `0x71` or `0x72`) to a card and receives the script results in subsequent transactions (via the TVR bit indicating script processing success/failure), the pattern of script failures reveals card tampering. A legitimate card that receives a PIN UNBLOCK script (INS `0x24`) and processes it successfully returns TVR byte 5 bits 6-5 clear. A tampered card — or a wedge device that intercepts and blocks issuer scripts — returns TVR byte 5 bit 6 or 5 set (script processing failed). Repeated script failures from the same card, combined with CVM anomalies, strongly indicate a wedge device or modified card.

### 12.4 Case studies

#### 12.4.1 Large-scale shimming operation investigation

In 2024, a European issuer detected an anomalous pattern: approximately 200 cards issued to a single regional bank exhibited CVM Result/CVR mismatches (terminal reported "PIN verified" but card's IAD recorded "PIN verification not attempted") concentrated at five terminals operated by the same merchant chain. The investigation proceeded:

Phase 1 (pattern detection): the issuer's real-time fraud system flagged individual transactions, but the operational significance emerged only when a fraud analyst queried for CVM mismatch clusters grouped by terminal ID. The query revealed that 95% of mismatched transactions originated from five terminal IDs, all belonging to the same merchant.

Phase 2 (terminal inspection): law enforcement, coordinated with the acquirer, conducted physical inspections of the five terminals. Three contained shimming devices inserted into the chip reader slot. The shims were thin-film PCBs (0.09mm) with an STM32F030 microcontroller, 2MB SPI flash, and a Bluetooth Low Energy (BLE) module for data exfiltration.

Phase 3 (device forensics): the shims were examined in a forensic lab. Firmware extraction via SWD yielded the complete APDU interception logic. The shims recorded: PAN, expiry, Track 2 equivalent, and offline plaintext PIN (captured from VERIFY commands). The BLE module transmitted harvested data to a nearby smartphone at 15-minute intervals. The SPI flash contained 1,847 complete card records spanning a 6-week period.

Phase 4 (fraud correlation): the compromised PANs were cross-referenced with the issuer's fraud reports. Approximately 60% of the harvested cards had been used for counterfeit magnetic-stripe transactions at terminals in a neighboring country within days of the shimming capture. The counterfeit cards used the stolen Track 2 data with the service code modified from `2XX` to `1XX` (§7.4).

Phase 5 (attribution): the BLE exfiltration records, combined with surveillance footage from the merchant locations and cell-tower data for the receiving smartphone, enabled law enforcement to identify the criminal group.

#### 12.4.2 EMV relay attack in the wild

A 2025 incident at a luxury retailer involved contactless transactions totaling EUR 47,000 over a 3-hour window, all from cards whose legitimate holders were located in a different city. The investigation identified the attack as a coordinated relay:

The attacker team consisted of two roles: "moles" who positioned NFC-capable Android devices near victims' wallets in a crowded transit station, and "buyers" who presented relay devices (also Android phones) at the retailer's contactless terminals. The relay channel used a custom Android application (derived from the open-source NFCGate project) communicating over a 4G mobile data link.

Forensic evidence: (1) the terminal's transaction timing logs showed GPO response times averaging 380 ms (baseline for the same card types: 95 ms), indicating relay latency; (2) the on-card transaction logs (read from two of the victims' cards after they reported unauthorized transactions) showed ATC values that matched the fraudulent transactions, confirming the real cards were involved; (3) the geographic impossibility — the victims' cards were simultaneously "present" at both the transit station (where legitimate contactless taps occurred minutes before) and the luxury retailer 200 km away.

Detection and response: the issuer's transaction monitoring system flagged the velocity anomaly (multiple high-value contactless transactions from different cards at the same terminal in rapid succession). The retailer's acquirer placed the terminal on monitoring. Subsequent analysis of the timing data confirmed the relay signature.

#### 12.4.3 BIN attack campaign analysis

An acquiring processor detected a BIN attack campaign targeting a food-delivery platform. Over 48 hours, 340,000 authorization requests arrived from 12 merchant accounts (all created within the previous week), testing PANs within 47 distinct BIN ranges. The campaign characteristics:

The requests followed a systematic pattern: PANs were tested in ascending sequence within each BIN, with Luhn-valid numbers only. Each PAN was tested once with amount USD $0.50 and a fabricated CVV2. The IP addresses rotated across 200+ residential proxies, but the device fingerprint (browser user-agent, screen dimensions, WebGL renderer hash collected by the 3DS Method iframe) showed only 3 distinct devices.

The processor implemented countermeasures: velocity limits per merchant (max 100 authorizations per hour), BIN-range monitoring (alert when >50 declines within a single 8-digit BIN in 10 minutes), and device-fingerprint blacklisting. The 12 merchant accounts were suspended, and the BIN ranges were flagged to issuing banks for enhanced monitoring.

### 12.5 Expert witness considerations

Presenting EMV forensic evidence in legal proceedings requires adherence to chain-of-custody standards and translation of technical findings into terms accessible to non-technical audiences. The expert witness must document: the acquisition method for physical evidence (shim devices, terminal hard drives), the tools and procedures used for data extraction (firmware dump tool versions, hash algorithms, analysis software), the logical chain from raw data to conclusions (e.g., "the CVM Result / CVR mismatch in 200 transactions from these 5 terminals, combined with the physical shim recovery, demonstrates that the shim device modified the PIN verification response"), and the limitations of the analysis (e.g., "the transaction log analysis covers only the most recent 10 transactions retained on the card; earlier transactions are overwritten and cannot be recovered from the card itself").

Digital evidence from EMV transactions must meet admissibility standards: authenticity (the data was not altered — demonstrated by hash verification of raw captures), reliability (the tools used are accepted in the field — Proxmark3, Wireshark, and PC/SC tools are widely used in forensic practice), and relevance (the evidence directly addresses the matter at issue). For cross-border cases, the expert must address jurisdictional differences in digital evidence standards (EU Directive 2014/41/EU on the European Investigation Order, US Federal Rules of Evidence 901-902 for authentication of digital records).

---

## 13. Detection Engineering for Payment Security

### 13.1 Sigma rules for payment fraud detection

The following Sigma rules detect EMV-specific fraud patterns in transaction monitoring systems, terminal management logs, and payment infrastructure telemetry. Each rule uses the standard Sigma format and targets log sources commonly available in payment processing environments.

```yaml
title: EMV Shimming Indicator — SDA-Only Transaction from DDA-Capable Card
id: a7c3e1f0-8b42-4d9e-b5a1-3f2e6d8c9b01
status: experimental
description: >
  Detects transactions where the terminal reports SDA was performed (TVR byte 1 bit 7 clear,
  bit 8 clear) but the card's AIP indicates DDA/CDA capability. A shimming device or wedge
  may have downgraded the AIP to force SDA, which does not require the ICC private key.
  Cross-reference with §7.5 (wedge device ODA downgrade).
references:
  - https://emvco.com/specifications/
author: Payment Security Operations
date: 2026-05-13
logsource:
  category: payment
  product: emv_transaction_log
detection:
  selection:
    aip_dda_supported: true
    oda_method_performed: "SDA"
  condition: selection
falsepositives:
  - Terminal configuration error (DDA certificates not loaded for the CA index)
  - Card with DDA-capable AIP but missing ICC PK certificate (issuer personalization error)
level: high
tags:
  - attack.credential_access
  - emv.shimming
  - emv.oda_downgrade
```

```yaml
title: EMV CVM Bypass — Terminal Reports No CVM for Above-Limit Transaction
id: b2d4f5a1-9c63-4e7b-a6b2-4g3f7e9d0c12
status: experimental
description: >
  Detects chip transactions above the CVM limit where the terminal reports CVM Result =
  "No CVM Performed" (tag 9F34 byte 1 = 0x1F). For chip-capable terminals with PIN pads,
  above-limit transactions should require PIN or signature. This pattern indicates CVM list
  manipulation via shim/wedge (§7.3, §7.5) or terminal misconfiguration.
author: Payment Security Operations
date: 2026-05-13
logsource:
  category: payment
  product: emv_transaction_log
detection:
  selection:
    pos_entry_mode|startswith: "05"  # chip contact
    cvm_result_method: "no_cvm"
  filter_below_limit:
    amount|lt: 50  # adjust per network/country CVM limit
  condition: selection AND NOT filter_below_limit
falsepositives:
  - Unattended terminal where no CVM is the configured default
  - Card CVM list specifying no CVM as the only option
level: high
tags:
  - attack.credential_access
  - emv.cvm_bypass
```

```yaml
title: EMV Relay Attack Indicator — Contactless Transaction Timing Anomaly
id: c3e5g6b2-0d74-5f8c-b7c3-5h4g8f0e1d23
status: experimental
description: >
  Detects contactless transactions where the total transaction time (first APDU to final
  response) exceeds the expected baseline by more than 200ms, indicating potential relay
  attack latency (§7.2). Requires terminal-level APDU timing telemetry.
author: Payment Security Operations
date: 2026-05-13
logsource:
  category: payment
  product: terminal_timing_log
detection:
  selection:
    interface: "contactless"
    total_transaction_time_ms|gt: 700
  filter_slow_card:
    card_type: "mobile_wallet"  # mobile wallets are inherently slower
  condition: selection AND NOT filter_slow_card
falsepositives:
  - Slow card (old chip, weak RF coupling)
  - Terminal RF interference causing retransmissions
level: medium
tags:
  - attack.collection
  - emv.relay_attack
```

```yaml
title: EMV Terminal Compromise — Unauthorized Firmware Modification
id: d4f6h7c3-1e85-6g9d-c8d4-6i5h9g1f2e34
status: experimental
description: >
  Detects terminal management system (TMS) events indicating firmware changes outside
  the authorized maintenance window or from unauthorized sources. Terminal firmware
  tampering enables kernel manipulation, key extraction, or data exfiltration.
author: Payment Security Operations
date: 2026-05-13
logsource:
  category: terminal_management
  product: tms_audit_log
detection:
  selection:
    event_type: "firmware_update"
  filter_authorized:
    source_server|endswith:
      - ".tms.acquirer.internal"
      - ".management.payment.corp"
    maintenance_window: true
  condition: selection AND NOT filter_authorized
falsepositives:
  - Emergency out-of-window patch deployment (should be documented)
level: critical
tags:
  - attack.persistence
  - emv.terminal_compromise
```

```yaml
title: BIN Attack Detection — Rapid Sequential Authorization Attempts
id: e5g7i8d4-2f96-7h0e-d9e5-7j6i0h2g3f45
status: experimental
description: >
  Detects BIN attack patterns: high volume of authorization requests with sequential or
  near-sequential PANs, concentrated decline rates, and uniform small amounts from a
  single merchant or IP range (§12.2.1).
author: Payment Security Operations
date: 2026-05-13
logsource:
  category: payment
  product: authorization_log
detection:
  selection:
    response_code|contains:
      - "14"   # invalid card number
      - "54"   # expired card
    amount|lt: 5.00
  timeframe: 10m
  condition: selection | count(pan_prefix_8) by merchant_id > 50
falsepositives:
  - Legitimate card testing by payment service provider (should use designated test BINs)
level: critical
tags:
  - attack.credential_access
  - emv.bin_attack
```

```yaml
title: Card Testing Pattern — Small Authorization Followed by Large Purchase
id: f6h8j9e5-3g07-8i1f-e0f6-8k7j1i3h4g56
status: experimental
description: >
  Detects the classic card-testing pattern: a small-value authorization (under $5) followed
  by a large purchase (over $200) on the same PAN within a short time window, from
  different merchants. Attackers test stolen cards with micro-authorizations before
  making high-value fraudulent purchases.
author: Payment Security Operations
date: 2026-05-13
logsource:
  category: payment
  product: authorization_log
detection:
  small_auth:
    amount|lt: 5.00
    response_code: "00"  # approved
  large_purchase:
    amount|gt: 200.00
    response_code: "00"
  timeframe: 30m
  condition: small_auth | near large_purchase ON pan_hash WITHIN 30m
    AND small_auth.merchant_id != large_purchase.merchant_id
falsepositives:
  - Legitimate cardholder making a small purchase (coffee) then a large purchase (electronics)
    at different merchants within 30 minutes — common, but merchant category analysis reduces FP
level: medium
tags:
  - attack.credential_access
  - emv.card_testing
```

```yaml
title: EMV Fallback Fraud — Chip-to-Swipe Downgrade at Chip-Capable Terminal
id: g7i9k0f6-4h18-9j2g-f1g7-9l8k2j4i5h67
status: experimental
description: >
  Detects magnetic stripe transactions (POS entry mode 90) at terminals known to be
  chip-capable, for cards known to be chip-enabled. This pattern indicates either
  deliberate fallback fraud (§7.4) or terminal malfunction. High-confidence when the
  same card successfully completed chip transactions at other terminals recently.
author: Payment Security Operations
date: 2026-05-13
logsource:
  category: payment
  product: authorization_log
detection:
  selection:
    pos_entry_mode: "90"  # magnetic stripe
    terminal_capability|contains: "chip"
    card_product_type: "chip_enabled"
  condition: selection
falsepositives:
  - Dirty chip contacts causing legitimate fallback (correlate with terminal error logs)
  - Cards with damaged chips
level: high
tags:
  - attack.defense_evasion
  - emv.fallback_fraud
```

```yaml
title: Contactless Replay Attempt — Duplicate Cryptogram Detection
id: h8j0l1g7-5i29-0k3h-g2h8-0m9l3k5j6i78
status: experimental
description: >
  Detects authorization requests containing an Application Cryptogram (tag 9F26) and
  ATC (tag 9F36) combination that has been seen in a previous transaction. A valid
  EMV card increments the ATC for every transaction and generates a unique cryptogram;
  duplicate values indicate replay of a captured transaction (pre-play attack §7.1
  or contactless capture-and-replay).
author: Payment Security Operations
date: 2026-05-13
logsource:
  category: payment
  product: authorization_log
detection:
  selection:
    interface|contains:
      - "contactless"
      - "chip"
  condition: selection | count() by pan_hash, atc_value, cryptogram > 1
falsepositives:
  - Authorization reversal/retry by the terminal (same ARQC resent after timeout)
  - Acquirer duplicate detection failure
level: critical
tags:
  - attack.replay
  - emv.cryptogram_replay
```

```yaml
title: POS Malware Indicator — Suspicious Process Execution on Payment Terminal
id: i9k1m2h8-6j30-1l4i-h3i9-1n0m4l6k7j89
status: experimental
description: >
  Detects execution of unauthorized processes on Linux-based payment terminals.
  POS malware (FrameworkPOS, TreasureHunter, RawPOS, MajikPOS) typically spawns
  processes that scan memory for card data patterns. Requires terminal endpoint
  detection telemetry or process audit logs.
author: Payment Security Operations
date: 2026-05-13
logsource:
  category: process_creation
  product: linux
detection:
  selection_memory_scan:
    CommandLine|contains:
      - "/proc/"
      - "mem"
      - "dd if="
    User|contains: "payment"
  selection_unusual_binary:
    Image|re: "^/tmp/|^/dev/shm/|^/var/tmp/"
  selection_network_exfil:
    CommandLine|contains:
      - "curl"
      - "wget"
      - "nc "
      - "ncat"
    ParentImage|contains: "payment"
  condition: selection_memory_scan OR selection_unusual_binary OR selection_network_exfil
falsepositives:
  - Legitimate terminal diagnostic utilities
  - Authorized remote management tools
level: critical
tags:
  - attack.collection
  - attack.exfiltration
  - emv.pos_malware
```

```yaml
title: EMV CVM Result / CVR Mismatch — Shim or Wedge Indicator
id: j0l2n3i9-7k41-2m5j-i4j0-2o1n5m7l8k90
status: experimental
description: >
  Detects transactions where the terminal-reported CVM Result (tag 9F34) claims
  "PIN verified successfully" but the card's CVR (within IAD, tag 9F10) records
  "PIN verification not performed" or "PIN verification failed". This mismatch is
  the primary indicator of a shimming or wedge device modifying VERIFY responses
  (§7.3, §10.3).
author: Payment Security Operations
date: 2026-05-13
logsource:
  category: payment
  product: emv_transaction_log
detection:
  selection:
    cvm_result_method: "online_pin_verified"
    iad_cvr_pin_status: "not_performed"
  condition: selection
falsepositives:
  - IAD parsing error (incorrect CVN interpretation)
  - Issuer personalization error (CVR not properly updated by card)
level: critical
tags:
  - attack.credential_access
  - emv.cvm_mismatch
  - emv.shimming
```

### 13.2 YARA rules for POS malware detection

The following YARA rules detect known POS malware families and payment card data patterns in memory dumps or binary samples from compromised terminal environments. These rules are designed for deployment on terminal forensic workstations and endpoint detection agents.

```
rule FrameworkPOS_Strings {
    meta:
        description = "Detects FrameworkPOS memory-scraping malware targeting POS terminals"
        author = "Payment Security Operations"
        date = "2026-05-13"
        severity = "critical"
        reference = "https://www.trustwave.com/en-us/resources/blogs/spiderlabs-blog/"

    strings:
        $dns_exfil = "nslookup" ascii
        $track_regex = /[3-6][0-9]{12,18}=[0-9]{4}/ ascii
        $proc_scan = "/proc/" ascii
        $mem_read = "mem" ascii
        $dns_tunnel_pattern = {2E [1-60] 2E [1-60] 2E}
        $framework_mutex = "frmwrk" ascii nocase

    condition:
        uint32(0) == 0x464C457F  // ELF header
        and ($dns_exfil and $track_regex)
        or ($proc_scan and $mem_read and $track_regex)
        or ($dns_tunnel_pattern and $framework_mutex)
}

rule TreasureHunter_POS {
    meta:
        description = "Detects TreasureHunter POS malware — RAM scraping variant"
        author = "Payment Security Operations"
        date = "2026-05-13"
        severity = "critical"
        reference = "https://www.flashpoint-intel.com/"

    strings:
        $th_str1 = "TREASURE" ascii wide
        $th_str2 = "HUNTER" ascii wide
        $th_mutex = "TreasureHunter" ascii
        $track1_pattern = /%B[0-9]{13,19}\^[A-Z\/ ]{2,26}\^[0-9]{4}/ ascii
        $track2_pattern = /;[0-9]{13,19}=[0-9]{4}/ ascii
        $reg_persist = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" ascii

    condition:
        (any of ($th_str*) or $th_mutex)
        and ($track1_pattern or $track2_pattern)
        and $reg_persist
}

rule RawPOS_Variant {
    meta:
        description = "Detects RawPOS memory dumper — extracts card data from process memory"
        author = "Payment Security Operations"
        date = "2026-05-13"
        severity = "critical"

    strings:
        $rawpos_dump = "procdump" ascii nocase
        $rawpos_service = "rawpos" ascii nocase
        $memdump_cmd = "comsvcs.dll" ascii
        $lsass_target = "lsass" ascii
        $pan_regex_broad = /[3-6][0-9]{14,18}D[0-9]{4}/ ascii  // Track 2 separator 'D'

    condition:
        ($rawpos_dump or $rawpos_service or $memdump_cmd)
        and ($lsass_target or $pan_regex_broad)
}

rule MajikPOS_Indicators {
    meta:
        description = "Detects MajikPOS — modular POS malware with C2 communication"
        author = "Payment Security Operations"
        date = "2026-05-13"
        severity = "critical"
        reference = "https://www.trendmicro.com/"

    strings:
        $majik_c2 = /https?:\/\/[a-z0-9\-\.]+\.(top|xyz|pw|cc)\// ascii
        $majik_ua = "Mozilla/4.0" ascii
        $ram_scrape_loop = { 4D 5A ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? 50 45 }
        $card_validate_luhn = "luhn" ascii nocase
        $base64_exfil = "base64" ascii nocase
        $process_enum = "CreateToolhelp32Snapshot" ascii

    condition:
        ($majik_c2 or $majik_ua)
        and $process_enum
        and ($card_validate_luhn or $base64_exfil)
}

rule Card_Data_In_Process_Memory {
    meta:
        description = "Detects PAN and Track 2 data patterns in process memory dumps"
        author = "Payment Security Operations"
        date = "2026-05-13"
        severity = "high"

    strings:
        // Track 2: PAN=Expiry (separator D or =)
        $track2_eq = /[3-6][0-9]{12,18}=[0-9]{4}[0-9]{3}/ ascii
        $track2_d = /[3-6][0-9]{12,18}D[0-9]{4}[0-9]{3}/ ascii
        // Track 1: %B + PAN + ^ + Name + ^ + Expiry
        $track1 = /%B[3-6][0-9]{12,18}\^[A-Z\/ ]{2,26}\^[0-9]{4}/ ascii
        // Bare PAN (Visa, MC, Amex, Discover ranges)
        $pan_visa = /4[0-9]{15}/ ascii
        $pan_mc = /5[1-5][0-9]{14}/ ascii
        $pan_amex = /3[47][0-9]{13}/ ascii
        $pan_disc = /6(?:011|5[0-9]{2})[0-9]{12}/ ascii

    condition:
        (3 of ($track*))
        or (#pan_visa + #pan_mc + #pan_amex + #pan_disc > 10)
}

rule Terminal_Config_Tampering {
    meta:
        description = "Detects modification of EMV terminal configuration files"
        author = "Payment Security Operations"
        date = "2026-05-13"
        severity = "high"

    strings:
        $emv_cfg = "emv_config" ascii nocase
        $kernel_cfg = "kernel_config" ascii nocase
        $aid_table = "aid_table" ascii nocase
        $ca_keys = "ca_public_key" ascii nocase
        $cvm_limit_mod = "cvm_limit" ascii nocase
        $floor_limit_mod = "floor_limit" ascii nocase
        $disable_online = "force_offline" ascii nocase
        $disable_pin = "pin_bypass" ascii nocase

    condition:
        3 of them
}
```

### 13.3 Network-level detection

Compromised payment terminals exfiltrate captured card data through several network channels, each detectable with appropriate network monitoring.

**DNS tunneling.** FrameworkPOS and its derivatives encode stolen card data in DNS query subdomains. Each DNS query carries a fragment of base32 or hex-encoded card data: `4[PAN_fragment].6[expiry].data.attacker.tld`. Detection: monitor DNS query logs for abnormally long subdomain labels (>30 characters), high query volume to a single domain, and domains with high entropy in subdomain components. A DNS inspection rule:

```
# Suricata rule: detect DNS queries with suspiciously long subdomains
alert dns any any -> any any (msg:"POS Malware DNS Tunnel - Long Subdomain";
    dns.query; content:"."; depth:1; offset:30;
    pcre:"/^[a-z0-9]{30,}\./i";
    threshold: type threshold, track by_src, count 10, seconds 60;
    classtype:trojan-activity; sid:2026001; rev:1;)
```

**HTTP POST exfiltration.** Some POS malware families exfiltrate card data via HTTP POST to a command-and-control server. The POST body contains base64-encoded or custom-encoded card records. Detection: inspect HTTP POST traffic from terminal network segments for outbound connections to non-whitelisted endpoints, POST bodies containing base64-encoded data matching Track 2 patterns (after decoding), and connections to recently registered domains or known bulletproof hosting IP ranges.

**Payment gateway anomaly detection.** At the payment network level, anomaly detection operates on aggregated authorization patterns. Velocity checks flag merchants or terminals exceeding expected transaction rates. Geographic impossible-travel detection flags the same card used at terminals in different cities within an interval shorter than the minimum travel time. Amount-pattern detection flags sudden changes in a terminal's average transaction value or a shift toward round-number amounts (which indicate manually keyed transactions replacing chip transactions).

### 13.4 Integration with payment fraud platforms

The Sigma and YARA rules above must be integrated with the payment ecosystem's existing risk scoring infrastructure. Visa Advanced Authorization (VAA) and Mastercard Decision Intelligence assign real-time risk scores to every authorization request. The detection rules feed into this scoring as supplementary signals:

A Sigma rule match for "CVM Result / CVR mismatch" on a transaction increases the risk score by a configurable weight, potentially triggering a decline or a 3DS stepup challenge. A YARA match for POS malware on a terminal triggers an alert to the acquirer's terminal management system, which can remotely disable the terminal and initiate an incident response. Network-level DNS tunnel detection triggers a firewall block on the compromised terminal's outbound DNS and an alert to the terminal operations team.

The mapping to 3DS challenge triggers is particularly important for card-not-present fraud: when the issuer's risk model detects BIN attack patterns (Sigma rule §13.1) against a cardholder's BIN range, subsequent 3DS authentication requests for cards in that range are automatically routed to the challenge flow (no frictionless exemption), adding an authentication barrier that the attacker cannot bypass without access to the cardholder's phone or biometric.

---

## 14. Terminal Security and Hardening

### 14.1 PCI PTS device security requirements

The PCI Security Standards Council's PIN Transaction Security (PTS) standard governs the physical and logical security of payment terminals. The current standard, PTS POI (Point of Interaction) version 6, defines requirements across several security modules:

**Physical security.** The terminal must resist physical tampering through multiple layers of defense. Tamper-responsive mechanisms include: a conductive mesh layer beneath the keypad that detects drilling or penetration attempts and triggers key zeroization (immediate erasure of all cryptographic keys from volatile and non-volatile memory); active tamper-detection circuits that monitor the integrity of the housing seals, screws, and access panels; and epoxy potting of critical components (the secure cryptographic module containing the PIN encryption key, the main processor, and the key storage) to resist desoldering and probing. PTS POI v6 Module 3 (Physical Security) requires that any attack achieving key extraction must take a minimum of 26 hours with equipment costing at least USD $25,000 (the "attack potential" threshold). The terminal must also detect environmental attacks: extreme temperature (attempting to freeze the RAM to slow key decay), voltage glitching on the power supply, and electromagnetic fault injection.

**Logical security.** PTS POI v6 Module 4 (Logical Security) requires: secure boot (the terminal verifies the firmware signature against a trusted root key before executing any code), code signing (all firmware and application updates must be cryptographically signed by the terminal vendor's signing key), and application isolation (the payment application runs in a protected environment separated from non-payment applications). The terminal must enforce secure key loading: keys can only be loaded via a secure key injection facility (using an HSM) or via remote key injection (RKI) over an authenticated and encrypted channel. The terminal must not allow key extraction by any software command — keys are used internally for encryption/MAC operations but never output in plaintext.

**Key injection facility requirements.** New terminals must be initialized with their base keys (the acquirer's master key for PIN encryption, the terminal management key for TMS authentication) at a PCI-certified Key Injection Facility (KIF). The KIF operates under dual-control procedures: at least two authorized custodians are required to perform any key operation. The facility uses an HSM (e.g., Thales payShield 10K, Utimaco CryptoServer) to generate and inject keys. The ceremony proceeds: the HSM generates the terminal's unique key components; each component is loaded by a separate custodian under dual-control; the combined key is injected into the terminal's secure cryptographic module; and the ceremony is documented with UTC-timestamped audit records and custodian signatures.

### 14.2 Terminal software hardening

#### 14.2.1 Kernel hardening for Linux-based payment terminals

Many modern payment terminals run Linux-based operating systems (Ingenico's Telium TETRA, PAX Technology's PayDroid, Verifone's Engage platform). Hardening these platforms follows defense-in-depth principles:

```bash
# dm-verity: verified boot for the root filesystem
# The root filesystem is read-only; dm-verity ensures integrity at the block level.
# During build, compute the dm-verity hash tree:
veritysetup format /dev/mmcblk0p2 /dev/mmcblk0p3
# Output: root hash = <hex>
# The root hash is embedded in the kernel command line or signed bootloader.
# At boot, the kernel verifies every block read from the rootfs partition against the hash tree.
# Any modification (malware injection, config tampering) causes a verification failure and boot halt.

# SELinux policy for the payment application
# The payment process runs in a dedicated SELinux domain: payment_app_t
# Policy restricts:
#   - File access: only /opt/payment/data (read-write), /opt/payment/bin (read-execute)
#   - Network: only outbound TCP to acquirer gateway on port 443
#   - IPC: only UNIX domain sockets to pcscd (smart card daemon)
#   - Device access: only /dev/ttyS0 (card reader) and /dev/input/event0 (keypad)

# Read-only root filesystem
# Mount rootfs as read-only; use a tmpfs overlay for runtime data:
mount -o remount,ro /
mount -t tmpfs tmpfs /var/run -o size=16M,noexec,nosuid
mount -t tmpfs tmpfs /tmp -o size=32M,noexec,nosuid

# Disable unnecessary kernel modules
echo "install usb-storage /bin/false" >> /etc/modprobe.d/blacklist-payment.conf
echo "install bluetooth /bin/false" >> /etc/modprobe.d/blacklist-payment.conf
echo "install uvcvideo /bin/false" >> /etc/modprobe.d/blacklist-payment.conf

# Kernel sysctl hardening
sysctl -w kernel.kptr_restrict=2       # hide kernel pointers
sysctl -w kernel.dmesg_restrict=1      # restrict dmesg access
sysctl -w kernel.yama.ptrace_scope=3   # no ptrace allowed
sysctl -w net.ipv4.conf.all.accept_redirects=0
sysctl -w net.ipv4.conf.all.send_redirects=0
sysctl -w net.ipv4.tcp_syncookies=1
```

#### 14.2.2 Application whitelisting and secure communication

Application whitelisting ensures that only authorized executables run on the terminal. The implementation uses dm-verity for the root filesystem (guaranteeing that system binaries are unmodified) and a separate integrity verification for any writable partitions. The payment application binary and its shared libraries are signed; the loader verifies the signature before execution. Any unsigned or modified binary is rejected.

Secure communication between the terminal and the acquirer's host uses TLS 1.2 or 1.3 with mutual authentication. The terminal presents its client certificate (provisioned during key injection or via RKI), and the acquirer's host presents its server certificate. Certificate pinning (the terminal stores a hash of the expected server certificate or its public key, and rejects connections presenting a different certificate) prevents MitM attacks even if a CA is compromised. The TLS configuration restricts cipher suites to those approved by PCI DSS:

```
# Terminal TLS configuration (OpenSSL cipher string)
# TLS 1.2: ECDHE key exchange, AES-256-GCM, SHA-384
TLS_CIPHERS="ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384"
# TLS 1.3: only TLS_AES_256_GCM_SHA384
TLS_13_CIPHERS="TLS_AES_256_GCM_SHA384"
# Minimum protocol version
MIN_TLS_VERSION="TLSv1.2"
# Certificate pinning: SHA-256 hash of the acquirer gateway's public key
PINNED_PUBKEY_HASH="sha256//YLh1dUR9y6Kja30RrAn7JKnbQG/uEtLMkBgFF2Fuihg="
```

#### 14.2.3 Point-to-Point Encryption (P2PE)

P2PE encrypts cardholder data at the point of interaction (the card reader) before it reaches the terminal's main processor. The encryption occurs within the SRED (Secure Reading and Exchange of Data) module — a tamper-resistant hardware component that reads the card data, encrypts it immediately, and passes only ciphertext to the terminal's application processor. The application never sees plaintext card data, rendering RAM-scraping POS malware ineffective (the malware can only capture encrypted data that it cannot decrypt).

The SRED module uses DUKPT (Derived Unique Key Per Transaction) for key management. DUKPT derives a unique encryption key for each transaction from a Base Derivation Key (BDK) and a Key Serial Number (KSN) that increments with each transaction. The derivation is one-way: compromising a single transaction key does not reveal the BDK or any other transaction key. The BDK is held only in the acquirer's HSM and the SRED module; it is injected during manufacturing or via RKI under dual-control.

```
DUKPT Key Hierarchy:
  BDK (Base Derivation Key, 128-bit AES or 112-bit 3DES)
    → IPEK (Initial PIN Encryption Key, derived from BDK and initial KSN)
      → Future Keys (derived from IPEK using the DUKPT key tree)
        → Transaction Key N (derived from the future key register and current KSN counter)

Each transaction:
  1. SRED reads card data (PAN, Track 2)
  2. SRED derives the current transaction key from the DUKPT state
  3. SRED encrypts the card data: ciphertext = AES-CBC(txn_key, plaintext_card_data)
  4. SRED outputs: {KSN, ciphertext} to the terminal application
  5. Terminal forwards {KSN, ciphertext} to the acquirer
  6. Acquirer HSM derives the same transaction key from BDK + KSN
  7. HSM decrypts the card data for authorization processing
```

Format-Preserving Encryption (FPE, NIST SP 800-38G, FF1 or FF3-1 mode) is used when the downstream system expects data in the original format (e.g., a 16-digit PAN). FPE encrypts a PAN into another syntactically valid PAN (same length, same character set, valid Luhn check digit), allowing the ciphertext to flow through systems that validate PAN format without modification. The real PAN is recoverable only by the entity holding the FPE key (typically the acquirer's HSM or the P2PE solution provider).

### 14.3 Terminal lifecycle security

#### 14.3.1 Secure provisioning workflows

New terminals arrive from the manufacturer in a "pre-personalized" state: they contain the vendor's root certificate (for firmware verification) and a transport key (a temporary key used for the initial key injection session). The provisioning workflow:

Step 1: the terminal is powered on in the KIF's secure room. The KIF operator authenticates to the HSM under dual control. Step 2: the HSM establishes a secure session with the terminal using the transport key (SCP02 or SCP03 protocol, identical to GlobalPlatform card management — §11.1). Step 3: the HSM injects the production keys: the acquirer's Master Key (for deriving session keys for PIN encryption and MAC), the TMS authentication key (for terminal management system communication), and the P2PE DUKPT BDK (if the terminal supports P2PE). Step 4: the transport key is replaced with the production key set, and the terminal is marked as "provisioned" in the TMS inventory. Step 5: the provisioning ceremony is documented: terminal serial number, key check values (KCV — the first 3 bytes of the encrypted zero block under each key, used to verify key integrity without revealing the key), custodian names, and UTC timestamp.

#### 14.3.2 Remote Key Injection (RKI)

RKI eliminates the need to ship terminals to a KIF for key injection, reducing deployment time from weeks to hours. The RKI protocol proceeds:

The terminal generates an RSA or ECC key pair within its secure cryptographic module. The public key is signed by the terminal's device certificate (provisioned by the manufacturer). The terminal sends the signed public key to the RKI server (operated by the acquirer or a trusted key injection service). The RKI server verifies the terminal's certificate chain (terminal cert → manufacturer CA → root CA), ensuring the terminal is genuine. The RKI server encrypts the production keys under the terminal's public key and sends the encrypted key block. The terminal decrypts the key block within its secure module, loads the production keys, and erases the transport key. The entire exchange is authenticated (mutual TLS between terminal and RKI server) and the key material is never exposed outside the secure module or the HSM.

PCI PTS POI v6 requires that RKI implementations provide security equivalent to in-person key injection: the terminal's key generation must use a hardware RNG within the secure module, the private key must never be exportable, and the RKI server must verify the terminal's identity through a certificate chain rooted in a trusted CA.

#### 14.3.3 Firmware update security

Terminal firmware updates are distributed through the Terminal Management System (TMS). Each firmware image is signed by the terminal vendor's code-signing key (RSA-2048 or ECDSA P-256). The terminal verifies the signature before applying the update. The verification proceeds: the terminal downloads the firmware image and its detached signature from the TMS; the terminal's bootloader computes the hash of the firmware image (SHA-256); the bootloader verifies the signature using the vendor's public key (embedded in the terminal's secure boot chain); if the signature is valid, the firmware is written to the update partition; on next boot, the bootloader switches to the updated partition.

Rollback protection prevents an attacker from downgrading the firmware to a version with known vulnerabilities. The terminal maintains a monotonic counter (stored in one-time-programmable fuses or a secure counter in the TPM/secure element). Each firmware release includes a minimum counter value; the bootloader rejects any firmware image whose counter value is less than the current counter. This ensures that once a terminal is updated to a patched firmware, it cannot be reverted to the vulnerable version.

#### 14.3.4 Decommissioning procedures

When a terminal reaches end-of-life or is removed from service, the decommissioning procedure ensures that all cryptographic material is destroyed:

Step 1: the terminal is placed into "decommission" mode via the TMS (authenticated command from the acquirer). Step 2: the terminal's secure module executes key zeroization — all keys (master key, session keys, DUKPT state, TMS key, P2PE BDK) are overwritten with zeros and then with random data. Step 3: the terminal's non-volatile storage (flash, EEPROM) is erased — a full-chip erase followed by a verification read. Step 4: the terminal's TMS inventory record is updated to "decommissioned" status. Step 5: the physical terminal is either returned to the manufacturer for certified destruction or destroyed on-site (shredding of the PCB to prevent recovery of any residual data from flash memory cells that survived software erasure).

PCI DSS Requirement 9.8 mandates that media containing cardholder data (which includes terminal storage that may have cached transaction data) must be destroyed when no longer needed. The decommissioning procedure satisfies this requirement when properly documented with UTC timestamps, custodian signatures, and destruction certificates.

### 14.4 Contactless-specific hardening

#### 14.4.1 Relay attack countermeasures

Current EMV contactless specifications do not include distance bounding (§7.2), but several countermeasures reduce relay attack effectiveness:

**Timing checks.** Mastercard's Relay Resistance Protocol (RRP, introduced in EMV Contactless Kernel C-8) adds terminal-side timing measurements to the contactless transaction. The terminal records the exact time it sends a challenge and the exact time it receives the card's response. If the round-trip time exceeds a terminal-configured threshold (typically 100-150 ms for the RRP-specific exchange), the terminal rejects the transaction or requests a fallback to contact mode. The RRP exchange is separate from the standard EMV APDU flow and uses a dedicated command that the card must respond to within the timing window. A relay adds at minimum the network round-trip latency (typically 50-200 ms over mobile data), which exceeds the tight RRP threshold.

**Distance bounding protocols.** Research prototypes (Brands and Chaum, 1993; Hancke and Kuhn, 2005) use ultra-wideband (UWB) time-of-flight measurements to verify that the card is physically close to the terminal. The terminal transmits a UWB pulse and measures the response time at the nanosecond level (1 ns corresponds to ~30 cm distance). A relay over any network link adds microseconds of delay, which is easily detectable. UWB-based distance bounding is not yet part of the EMV specification, but the technology is mature (Apple U1/U2 chips, NXP Trimension) and is being evaluated by EMVCo's Contactless Working Group for future kernel versions.

#### 14.4.2 Transaction limits and floor limits

Contactless CVM limits (§9.3) and offline floor limits provide layered defense. The terminal enforces: a per-transaction CVM limit (transactions above this limit require PIN or CDCVM), a cumulative offline limit (the card tracks offline transactions internally; when the cumulative amount or count exceeds the threshold, the card forces online authorization by returning ARQC instead of TC), and a terminal floor limit (transactions above the floor limit are always sent online, even if the card would approve offline).

These limits are configured per payment network and per country. Best practice is to set the terminal floor limit to zero for contactless transactions (always online), which ensures that every contactless transaction is authorized by the issuer in real time. This eliminates the risk of offline-only fraud (using a cloned or replayed card at an offline-capable terminal) at the cost of requiring network connectivity for every transaction.

#### 14.4.3 Kernel configuration per payment network

Each payment network's contactless kernel has configurable parameters that affect the security posture. Best practices per kernel:

**Kernel 2 (Mastercard).** Enable Relay Resistance Protocol (RRP). Set the RRP timing threshold to the minimum value that does not cause false rejections for legitimate cards (typically 100-120 ms). Enable CDA for all contactless transactions (Mastercard supports CDA in contactless mode). Disable MSD contactless (MSD lacks ODA and full cryptogram security; all Mastercard contactless transactions should use EMV mode).

**Kernel 3 (Visa).** Enable fDDA (Fast DDA) validation. Following the CTQ bypass vulnerability (§6.5, Basin et al., 2021), ensure the kernel version includes the fix that validates CTQ against the fDDA signature. Set the CVM limit per the issuer's country configuration. Disable MSD contactless (Visa's qVSDC provides superior security).

**Kernel 7 (UnionPay).** Enable online-only mode for international transactions. Enable ODA (DDA or CDA) for all transactions. Set floor limit to zero for contactless to ensure all transactions go online.

For all kernels: disable fallback from contactless to magnetic stripe (if the contactless transaction fails, the terminal should prompt for chip insertion, not magnetic stripe swipe). Log all contactless transaction timing data (total transaction time, per-APDU timing) for relay attack forensic analysis (§12.1.4). Apply kernel updates promptly when the payment network releases security patches (delivered via TMS).

---

## 15. Cross-references

**To Domain 13 (crypto):** EMV's RSA-based ODA (§5) uses the RSA primitives from Chapter 13A §2.1. The certificate chain (CA → Issuer → ICC) is a standard PKI hierarchy. The ARQC (§4.6) is a MAC — either 3DES-CBC-MAC or AES-CMAC. PIN block encryption uses 3DES or AES (Chapter 13A §1). The post-quantum migration (§8.5) references ML-DSA (FIPS 204) and AES-256.

**To Domain 17 (physical):** Side-channel and fault-injection attacks on EMV chip cards (recovering the ICC private key via DPA, or glitching the PIN-verification logic) use the techniques from Chapter 17 §1–2. PCI PTS PIN-pad tamper resistance (§10.2) is designed to resist these physical attacks.

**To Chapter 22B:** The ISO 8583 message format (Chapter 22B §1.4) carries the EMV data elements (DE55) between the terminal, acquirer, network, and issuer. ATM and POS security (Chapter 22B) describes the infrastructure that processes the EMV transactions detailed here. RAM scrapers (Chapter 22B §3.1) target the Track 1/2 data that EMV was designed to make obsolete. Mobile tokenization (Chapter 22B §4) provides supplementary context for the SRC and FIDO flows described in §8.

**To Domain 15 (mobile):** Apple Pay / Google Pay tokenization (Chapter 22B §4) provides an additional security layer: the DPAN replaces the PAN, and the device-specific cryptogram replaces the card's ARQC — making relay attacks on mobile contactless payments significantly harder (the token is device-bound).

---

## Exercises

1. **ATR decoding lab.** Given the raw ATR `3B 67 00 00 00 29 80 67 04 17 00 6F 6E 00 01 90 00`, parse every byte: identify TS, T0, interface bytes, historical bytes, and TCK. Determine the supported protocols, IFSC, BWI/CWI, and whether speed negotiation is requested. Verify the TCK checksum.

2. **ARQC computation exercise.** Using the Python code from section 4.6, compute the ARQC for a purchase transaction of EUR 50.00 at a terminal in Germany (country code 0276, currency code 0978) on 2026-05-29 with ATC = 0x003A and IMK = `AABBCCDDEEFF00112233445566778899`. Verify your result by independently re-deriving the ICC master key and session key. Then modify the amount to EUR 500.00 and confirm the ARQC changes — explain why this proves transaction-data binding.

3. **EMV relay attack analysis.** Set up a contactless relay lab using two NFC-capable Android devices and the NFCGate framework. Measure the round-trip relay latency over (a) local Wi-Fi, (b) a VPN tunnel across the internet. Compare measured latencies against Mastercard's Relay Resistance Protocol (RRP) timing threshold (100-120 ms). Document at which relay distance the RRP rejects the transaction and explain the physics behind UWB distance-bounding as a countermeasure.

4. **CVM bypass reconstruction.** Reproduce the Basin et al. (2021) Visa CTQ bypass on a test terminal: craft a modified PDOL response where the Terminal Transaction Qualifiers indicate no CVM required for a high-value transaction. Analyze which kernel versions are vulnerable and which include the fDDA-signature validation fix. Write a Sigma detection rule that flags contactless transactions above the CVM limit where CVM Results (tag 9F34) indicate "No CVM Performed."

5. **ODA certificate chain verification.** Using the Python ODA code from section 5.6, recover the Issuer Public Key and ICC Public Key from a set of test certificates (available from EMVCo's test-card data). Verify the SHA-1 hash chain. Then deliberately corrupt one byte in the Issuer Public Key Certificate and confirm that SDA/DDA verification fails. Document the exact failure point and the security implication.

---

## Readings and References

- EMVCo, *EMV Integrated Circuit Card Specifications for Payment Systems, Book 1-4, Version 4.4*, 2024. https://www.emvco.com/specifications/ (retrieved: 2026-05-29)
- EMVCo, *EMV Contactless Specifications for Payment Systems, Version 3.1*, 2023. https://www.emvco.com/specifications/ (retrieved: 2026-05-29)
- Basin, D., Sasse, R., and Toro-Pozo, J., "The EMV Standard: Break, Fix, Verify," *IEEE S&P 2021*. https://doi.org/10.1109/SP40001.2021.00037 (retrieved: 2026-05-29)
- Chothia, T. and de Ruiter, J., "A Systematic Review of EMV Contactless Protocol Security," *SoK: Attacks on Modern Card Payments*, arXiv:2504.03363, April 2025. https://arxiv.org/abs/2504.03363 (retrieved: 2026-05-29)
- PCI Security Standards Council, *PCI DSS v4.0.1*, March 2025. https://www.pcisecuritystandards.org/document_library/ (retrieved: 2026-05-29)
- ISO/IEC 7816-3:2006, *Identification cards — Integrated circuit cards — Part 3: Cards with contacts — Electrical interface and transmission protocols*. (retrieved: 2026-05-29)
- ISO 9564-1:2017, *Financial services — Personal Identification Number (PIN) management and security — Part 1: Basic principles and requirements for PINs in card-based systems*. (retrieved: 2026-05-29)
- Murdoch, S.J. et al., "Chip and PIN is Broken," *IEEE S&P 2010*. https://doi.org/10.1109/SP.2010.33 (retrieved: 2026-05-29)
- NFCGate relay-attack research framework. https://github.com/nfcgate/nfcgate (retrieved: 2026-05-29)

---

## Cross-References

| Topic | Reference | Relationship |
|---|---|---|
| RSA, 3DES, AES-CMAC cryptographic primitives | Domain 13, Chapter 13A §1-2 | EMV ODA uses RSA; ARQC uses 3DES-CBC-MAC or AES-CMAC |
| Side-channel and fault-injection attacks on chip cards | Domain 17, Chapter 17 §1-2 | DPA/SPA key recovery and PIN-verification glitching |
| ISO 8583 message format carrying DE55 EMV data | Domain 22, Chapter 22B §3 | Authorization messages transport ARQC, ATC, TVR between terminal and issuer |
| Mobile tokenization (Apple Pay, Google Pay) | Domain 22, Chapter 22B §4 | DPAN replaces PAN; device cryptogram replaces card ARQC |
| PCI DSS and PCI PTS compliance | Domain 22, Chapter 22B §6 | PIN pad tamper resistance and cardholder data protection |
| Post-quantum payment cryptography | Domain 13, Chapter 13B §5 | ML-DSA (FIPS 204) candidates for future EMV ODA |

---

## Glossary

- **AIP (Application Interchange Profile):** Two-byte bitfield returned in GPO response indicating which security features the card supports (SDA, DDA, CDA, CVM, issuer authentication).
- **AFL (Application File Locator):** Data structure in the GPO response specifying which SFI records to read and which records participate in offline data authentication.
- **APDU (Application Protocol Data Unit):** The command-response message structure defined by ISO 7816-4 for communication between a terminal and a smart card.
- **ARQC (Authorization Request Cryptogram):** An 8-byte MAC computed by the card over transaction data using a session key, sent online to the issuer for verification.
- **ATR (Answer to Reset):** The byte sequence a smart card transmits after reset, encoding supported protocols, speed-negotiation parameters, and historical bytes.
- **BER-TLV:** Basic Encoding Rules Tag-Length-Value — the data encoding scheme used for all EMV data objects.
- **CDA (Combined Dynamic Data Authentication):** The strongest ODA method — binds the card's DDA signature to the cryptogram, proving card genuineness at the moment of transaction.
- **CVM (Cardholder Verification Method):** The method used to verify the cardholder's identity — PIN (online/offline, plaintext/enciphered), signature, CDCVM, or no CVM.
- **DDA (Dynamic Data Authentication):** ODA method where the card signs a terminal-generated nonce with its ICC private key, proving the card is genuine (not a clone).
- **EMV (Europay, Mastercard, Visa):** The global standard for chip-card payment transactions, maintained by EMVCo.
- **GPO (GET PROCESSING OPTIONS):** The APDU command that initiates the EMV transaction, providing terminal data (PDOL) and receiving AIP and AFL from the card.
- **ODA (Offline Data Authentication):** The process by which the terminal verifies the authenticity of card data without going online — SDA, DDA, or CDA.
- **PDOL (Processing Data Object List):** A list of tags (in the FCI) specifying which data elements the card requires from the terminal in the GPO command.
- **SDA (Static Data Authentication):** The simplest ODA method — the issuer signs the card's static data; proves data integrity but not card genuineness.
- **TVR (Terminal Verification Results):** Five-byte bitfield recording the outcome of every terminal check (ODA, CVM, risk management), included in the cryptogram input and authorization message.
