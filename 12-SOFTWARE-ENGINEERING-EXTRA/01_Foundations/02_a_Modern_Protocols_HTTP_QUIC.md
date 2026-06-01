---
corso: "SWE Masterclass"
fase: "1 — Foundations"
modulo: "1.2.b"
titolo: "Module 1.2.b: Modern Application Protocols (HTTP/2, HTTP/3, TLS)"
versione: "1.0"
livello: "Advanced"
prerequisiti:
  - "TCP three-way handshake, flow control, and congestion control (Module 1.2.a)"
  - "OSI/TCP-IP model layers, UDP vs TCP trade-offs"
  - "Basic public-key cryptography concepts (key exchange, certificates)"
obiettivi:
  - "Explain head-of-line blocking at both the HTTP/1.1 and TCP layers and how HTTP/2 multiplexing partially solves it"
  - "Describe how QUIC eliminates TCP-level HOL blocking by providing independent streams over UDP"
  - "Trace a TLS 1.3 handshake (1-RTT) and a 0-RTT resumption, including the replay attack risk"
  - "Compare HPACK (HTTP/2) and QPACK (HTTP/3) header compression and their resilience to out-of-order delivery"
  - "Diagnose HTTP/2 and HTTP/3 connection behaviour using curl, openssl s_client, and Wireshark"
tag: [http2, http3, quic, tls-1.3, hpack, qpack, head-of-line-blocking, 0-rtt, connection-migration, grpc]
---

# Module 1.2.b: Modern Application Protocols (HTTP/2, HTTP/3, TLS)

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Explain head-of-line blocking at both the HTTP/1.1 and TCP layers and how HTTP/2 multiplexing partially solves it
> - Describe how QUIC eliminates TCP-level HOL blocking by providing independent streams over UDP
> - Trace a TLS 1.3 handshake (1-RTT) and a 0-RTT resumption, including the replay attack risk
> - Compare HPACK (HTTP/2) and QPACK (HTTP/3) header compression and their resilience to out-of-order delivery
> - Diagnose HTTP/2 and HTTP/3 connection behaviour using curl, openssl s_client, and Wireshark

> **Module 01.2.a** · **Last updated:** 2026-04-27

## Guiding ideas
1. **HTTP/2: multiplexing over single TCP; head-of-line blocking issue.**
2. **HTTP/3: QUIC transport (UDP); no HOL blocking.**
3. **TLS 1.3: 1-RTT handshake; 0-RTT for resumption (replay risk).**
4. **gRPC + HTTP/2: binary protobuf, streaming.**


**Date:** 2026-02-06
**Status:** Completed

## 1. The Head-of-Line (HOL) Blocking Problem

The history of HTTP is a history of fighting HOL Blocking.
*   **HTTP/1.0:** New TCP connection for every file. (Slow, high RTT overhead).
*   **HTTP/1.1:**
    *   **Keep-Alive:** Reuse TCP connection.
    *   **Pipelining:** Send `Req1, Req2` without waiting.
    *   **The HOL Problem:** Server must send `Resp1` before `Resp2`. If `Req1` needs a DB Query (2s) and `Req2` is a static image (1ms), the image is blocked for 2s.
*   **HTTP/2 (RFC 7540):**
    *   **Multiplexing:** Split messages into binary **Frames** with Stream IDs.
    *   **Interleaving:** `Stream 1` and `Stream 2` frames are mixed on the wire.
    *   **App-Layer HOL Solved:** Fast static assets are not blocked by slow DB queries.
    *   **The *New* HOL Problem (TCP Level):** TCP guarantees order. If Packet 10 is lost, Packet 11 (even if it belongs to a different, independent stream) sits in the kernel buffer waiting for Packet 10. **Result:** On lossy networks, HTTP/2 is *slower* than HTTP/1.1.

## 2. HTTP/3 & QUIC (RFC 9000)

Google (gQUIC) -> IETF (QUIC). The move to UDP.

### 2.1 The Architecture
*   **Transport:** UDP (User Datagram Protocol). No kernel handshake.
*   **Reliability:** Implemented in User Space (on top of UDP).
*   **Streams:** QUIC streams are independent. Loss of a packet in Stream A *does not* block Stream B.

### 2.2 Key Features
1.  **Connection Migration:**
    *   TCP uses 4-tuple (SrcIP, SrcPort, DstIP, DstPort). Switching from WiFi to LTE changes SrcIP -> Connection breaks.
    *   QUIC uses **CID (Connection ID)**. A 64-bit ID persists across IP changes. Seamless handover.
2.  **QPACK:**
    *   HTTP/2 used **HPACK**. It relied on a global stateful table. If a packet updating the table is lost, all future header decoding stalls.
    *   HTTP/3 uses **QPACK**. It separates the "Compression Context" stream from the "Data" stream. Allowed out-of-order delivery without breaking compression context.

## 3. TLS 1.3 Deep Dive (RFC 8446)

Encryption is no longer a layer *on top*; in QUIC, it's baked in.

### 3.1 Handshake Latency
*   **TLS 1.2:** 2-RTT (ClientHello -> ServerHello -> KeyExchange -> Finished).
*   **TLS 1.3:** 1-RTT.
    *   Client guesses the Key Share (usually Elliptic Curve Diffie-Hellman - X25519) and sends it in the *first* packet (ClientHello).
    *   If Server accepts, it sends ServerHello + Finished. Immediate encryption.

### 3.2 0-RTT Resumption (Early Data)
*   **Mechanism:** If Client has talked to Server before, they share a **PSK (Pre-Shared Key)** or Session Ticket.
*   **Action:** Client sends encrypted HTTP Request *inside* the very first packet (ClientHello).
*   **The Risk: Replay Attacks.**
    *   Attacker captures the 0-RTT packet.
    *   Attacker resends it 10 times.
    *   If the request was `POST /pay-money`, user pays 10 times.
*   **Mitigation:**
    *   Server must implement **Anti-Replay** (Time windows, Nonce cache).
    *   **Idempotency:** Browsers/Apps should ONLY use 0-RTT for Safe Methods (`GET`, `HEAD`).

## 4. Summary: The Stack Evolution

| Layer | Old Stack | New Stack (HTTP/3) |
| :--- | :--- | :--- |
| **App** | HTTP/1.1 or HTTP/2 | HTTP/3 |
| **Security** | TLS 1.2 | TLS 1.3 (Integrated) |
| **Transport** | TCP | QUIC |
| **Network** | IP | IP |
| **Link** | UDP | UDP |

---

## Exercises

### Exercise 1 — Inspect HTTP/2 Multiplexing with curl
1. Run a verbose HTTP/2 request: `curl -v --http2 https://www.google.com/ 2>&1 | grep -E '^\* |^< |^> '`
2. Observe the negotiated protocol (`h2`), ALPN selection, and stream IDs in the output.
3. Now force HTTP/1.1: `curl -v --http1.1 https://www.google.com/ 2>&1 | head -30`
4. Compare the connection reuse behaviour. With HTTP/2, a single connection carries multiplexed streams; with HTTP/1.1, you see sequential request/response.
**Expected output:** The `--http2` request shows `ALPN: h2` negotiation and binary frame references. The `--http1.1` request shows a plain text protocol exchange.

### Exercise 2 — TLS 1.3 Handshake Analysis with openssl s_client
1. Connect with TLS 1.3 explicitly: `openssl s_client -connect www.cloudflare.com:443 -tls1_3 -brief`
2. Note the cipher suite (e.g., `TLS_AES_256_GCM_SHA384`), the key exchange group (e.g., `X25519`), and the handshake completion in 1-RTT.
3. Compare with TLS 1.2: `openssl s_client -connect www.cloudflare.com:443 -tls1_2 -brief`
4. Document the differences in cipher negotiation, number of round trips, and certificate chain presentation.
**Expected output:** TLS 1.3 shows a single round-trip with forward-secret key exchange; TLS 1.2 shows a multi-round-trip handshake and may negotiate non-AEAD ciphers.

### Exercise 3 — Detect HTTP/3 (QUIC) Support with curl
1. Check if a target supports HTTP/3: `curl -I --http3 https://www.cloudflare.com/ 2>&1 | head -10`
   (Requires curl 7.88+ compiled with HTTP/3 support, e.g., via ngtcp2 or quiche.)
2. If your curl lacks `--http3`, check the `Alt-Svc` header from an HTTP/2 response: `curl -sI https://www.cloudflare.com/ | grep -i alt-svc`
3. The `Alt-Svc: h3=":443"` header advertises HTTP/3 availability on UDP port 443.
4. Use Wireshark with display filter `quic` to capture the QUIC Initial packet and observe the Connection ID (CID) field.
**Expected output:** The Alt-Svc header confirms HTTP/3 availability. Wireshark shows QUIC Initial packets on UDP/443 with a visible CID.

### Exercise 4 — Capture and Decode a QUIC Handshake in Wireshark
1. Set the `SSLKEYLOGFILE` environment variable: `export SSLKEYLOGFILE=/tmp/quic-keys.log`
2. Run a curl HTTP/3 request: `curl --http3 -o /dev/null https://www.cloudflare.com/`
3. Open the capture in Wireshark. Go to Edit > Preferences > Protocols > TLS and set the "(Pre)-Master-Secret log filename" to `/tmp/quic-keys.log`.
4. Apply filter `quic` and expand the QUIC Initial, Handshake, and 1-RTT packet layers.
5. Identify the TLS 1.3 ClientHello inside the QUIC Initial packet and the server's Handshake response.
**Expected output:** Wireshark decrypts the QUIC payload, revealing TLS 1.3 messages embedded within QUIC frames. You can see the key exchange, certificate, and Finished messages.

### Exercise 5 — 0-RTT Replay Risk Demonstration
1. Using `openssl s_client`, establish a session and save the ticket:
   `openssl s_client -connect www.cloudflare.com:443 -tls1_3 -sess_out /tmp/session.pem -brief < /dev/null`
2. Resume with early data (0-RTT):
   `echo -e "GET / HTTP/1.1\r\nHost: www.cloudflare.com\r\n\r\n" | openssl s_client -connect www.cloudflare.com:443 -tls1_3 -sess_in /tmp/session.pem -early_data /dev/stdin -brief`
3. Observe whether the server accepts or rejects the early data (check for `Early data was accepted/rejected`).
4. Replay the same session ticket a second time and note the server's anti-replay response.
**Expected output:** The first resumption may succeed (early data accepted). Replaying the same ticket typically results in rejection or a full handshake, demonstrating server-side anti-replay protection.

---

## Readings and References

### RFCs and Standards
- **RFC 9110** — HTTP Semantics. <https://datatracker.ietf.org/doc/html/rfc9110> (retrieved: 2026-05-29)
- **RFC 9113** — HTTP/2. <https://datatracker.ietf.org/doc/rfc9113/> (retrieved: 2026-05-29)
- **RFC 9114** — HTTP/3. <https://datatracker.ietf.org/doc/html/rfc9114> (retrieved: 2026-05-29)
- **RFC 9000** — QUIC: A UDP-Based Multiplexed and Secure Transport. <https://datatracker.ietf.org/doc/html/rfc9000> (retrieved: 2026-05-29)
- **RFC 9204** — QPACK: Field Compression for HTTP/3. <https://datatracker.ietf.org/doc/rfc9204/> (retrieved: 2026-05-29)
- **RFC 8446** — The Transport Layer Security (TLS) Protocol Version 1.3. <https://datatracker.ietf.org/doc/html/rfc8446> (retrieved: 2026-05-29)

### Official Documentation
- **Cloudflare — HTTP/3: the past, the present, and the future** — Production deployment perspective on QUIC/HTTP/3. <https://blog.cloudflare.com/http3-the-past-present-and-future/> (retrieved: 2026-05-29)
- **curl — HTTP/3 documentation** — Build and usage instructions for HTTP/3 in curl. <https://curl.se/docs/http3.html> (retrieved: 2026-05-29)
- **Google Cloud Blog — TCP BBR congestion control comes to GCP** — BBR deployment at scale and its interaction with QUIC. <https://cloud.google.com/blog/products/networking/tcp-bbr-congestion-control-comes-to-gcp-your-internet-just-got-faster> (retrieved: 2026-05-29)

### Books
- Grigorik, I., *High Performance Browser Networking*, O'Reilly, 2013 (online edition updated). <https://hpbn.co/>
- Rescorla, E., *TLS 1.3: The New Standard for Transport Security*, 2018 (background context for RFC 8446).
- Iyengar, J. & Thomson, M., "QUIC: A UDP-Based Multiplexed and Secure Transport," IETF RFC 9000, 2021.

---

## Cross-References

| Module | Relationship |
|---|---|
| `02_Networking_TCP_IP_Deep_Dive.md` | TCP congestion control, three-way handshake, flow control — the transport layer that HTTP/2 sits on and that QUIC replaces |
| `01_OS_Internals_Processes_Memory.md` | Kernel network stack, socket buffer management, user-space vs kernel-space for QUIC implementation |
| `01_a_CPU_Kernel_Boundary.md` | System call overhead for UDP recvmsg/sendmsg in user-space QUIC vs kernel TCP |
| `01_c_Memory_Management_Algorithms.md` | Buffer allocation strategies for QUIC stream reassembly in user space |
| `03_Advanced_Data_Structures_Algorithms.md` | Huffman coding in HPACK/QPACK, hash tables for header field lookup, priority trees in HTTP/2 |
| `04_Compilers_Interpreters.md` | Protocol parsers, binary frame decoding, state machines for HTTP/2 frame processing |

---

## Glossary

| Term | Definition |
|---|---|
| **HOL Blocking** | Head-of-Line Blocking — a condition where a delayed item at the front of a queue prevents subsequent items from being processed |
| **Multiplexing** | Sending multiple independent streams over a single connection, interleaving their frames |
| **QUIC** | A UDP-based transport protocol (RFC 9000) providing multiplexed streams, built-in encryption, and connection migration |
| **CID** | Connection ID — a QUIC identifier that persists across IP address changes, enabling seamless connection migration |
| **ALPN** | Application-Layer Protocol Negotiation — a TLS extension that allows client and server to agree on the application protocol (h2, h3) during the TLS handshake |
| **HPACK** | Header compression format for HTTP/2 (RFC 7541) using a static table, dynamic table, and Huffman encoding |
| **QPACK** | Header compression format for HTTP/3 (RFC 9204) redesigned from HPACK to tolerate out-of-order delivery |
| **0-RTT** | Zero Round-Trip Time resumption — a TLS 1.3 feature allowing encrypted application data in the first flight, at the cost of replay vulnerability |
| **PSK** | Pre-Shared Key — a symmetric key established from a previous TLS session, used for 0-RTT resumption |
| **Alt-Svc** | Alternative Services HTTP header that advertises protocol upgrades (e.g., h3) to clients |
| **Stream** | An independent, bidirectional sequence of frames within an HTTP/2 or QUIC connection; stream-level loss in QUIC does not affect other streams |
| **X25519** | An elliptic-curve Diffie-Hellman key exchange function (Curve25519) widely used in TLS 1.3 for forward-secret key agreement |
| **Connection Migration** | QUIC's ability to maintain a connection when the client's IP address changes (e.g., WiFi to cellular), identified by CID rather than the 4-tuple |
