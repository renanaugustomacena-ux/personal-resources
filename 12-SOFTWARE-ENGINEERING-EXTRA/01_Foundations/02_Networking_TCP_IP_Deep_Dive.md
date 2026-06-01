---
corso: "SWE Masterclass"
fase: "1 — Foundations"
modulo: "1.2.a"
titolo: "Module 1.2.a: TCP/IP & Congestion Control Deep Dive"
versione: "1.0"
livello: "Advanced"
prerequisiti:
  - "OSI/TCP-IP model layers and their responsibilities"
  - "Basic understanding of IP addressing, ports, and sockets"
  - "Familiarity with Linux CLI (ss, netstat, sysctl)"
obiettivi:
  - "Trace the full TCP state machine from SYN through TIME_WAIT and diagnose leaked CLOSE_WAIT sockets"
  - "Distinguish flow control (rwnd) from congestion control (cwnd) and explain how each limits throughput"
  - "Compare the loss-based algorithms Reno and CUBIC with the model-based algorithm BBR"
  - "Tune Linux sysctl knobs (window scaling, SACK, ECN, keepalive) for high-BDP links"
  - "Capture and interpret TCP handshake, retransmission, and congestion events with tcpdump/Wireshark"
tag: [tcp, congestion-control, cubic, bbr, networking, linux-kernel, sysctl, flow-control, window-scaling, sack]
---

# Module 1.2.a: TCP/IP & Congestion Control Deep Dive

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Trace the full TCP state machine from SYN through TIME_WAIT and diagnose leaked CLOSE_WAIT sockets
> - Distinguish flow control (rwnd) from congestion control (cwnd) and explain how each limits throughput
> - Compare the loss-based algorithms Reno and CUBIC with the model-based algorithm BBR
> - Tune Linux sysctl knobs (window scaling, SACK, ECN, keepalive) for high-BDP links
> - Capture and interpret TCP handshake, retransmission, and congestion events with tcpdump/Wireshark

> **Module 01.2** · **Last updated:** 2026-04-27

## Guiding ideas
1. **TCP congestion control: Reno → CUBIC (default) → BBR (Google).**
2. **Three-way handshake; FIN_WAIT2 timeouts.**
3. **Window scaling, SACK, ECN (Explicit Congestion Notification).**
4. **`tcp_syn_retries`, `tcp_keepalive_*` sysctl tuning.**


**Date:** 2026-02-06
**Status:** Completed

## 1. The TCP State Machine & Lifecycle

### 1.1 Connection Establishment (3-Way Handshake)
1.  **SYN:** Client sends `SYN`, enters `SYN_SENT`.
2.  **SYN-ACK:** Server receives `SYN`, sends `SYN-ACK`, enters `SYN_RCVD`.
3.  **ACK:** Client receives `SYN-ACK`, sends `ACK`, enters `ESTABLISHED`. Server receives `ACK`, enters `ESTABLISHED`.

### 1.2 Connection Termination (4-Way Teardown)
This is where complexity lives.
1.  **Active Close (Client):** Sends `FIN`. Enters `FIN_WAIT_1`.
2.  **Passive Close (Server):** Receives `FIN`. Sends `ACK`. Enters `CLOSE_WAIT`.
    *   *Critical:* The Server App *must* detect EOF and call `close()` explicitly. If not, the socket hangs in `CLOSE_WAIT` forever (Resource Leak).
3.  **Server Sends FIN:** Server calls `close()`, sends `FIN`. Enters `LAST_ACK`.
4.  **Client Receives FIN:** Sends `ACK`. Enters **`TIME_WAIT`**.
    *   *Purpose:* Wait 2xMSL (Max Segment Lifetime) to catch delayed packets.
    *   *Problem:* High-load servers run out of ephemeral ports if too many sockets are in `TIME_WAIT`. (Fix: `SO_REUSEADDR` or `tcp_tw_reuse`).

## 2. Window Management: Flow vs. Congestion

Transmission rate is limited by the **Minimum** of two windows:
$$Rate = \min(rwnd, cwnd)$$

### 2.1 Flow Control (`rwnd` - Receiver Window)
*   **Goal:** Don't drown the receiver.
*   **Mechanism:** Receiver advertises "I have 64KB buffer space left" in every ACK header.
*   **Window Scaling:** Original TCP limit was 64KB ($2^{16}$). RFC 1323 added "Window Scale" option to shift bits, allowing GB-sized windows (LFN - Long Fat Networks).

### 2.2 Congestion Control (`cwnd` - Congestion Window)
*   **Goal:** Don't drown the network (routers/switches).
*   **Mechanism:** Sender maintains a hidden variable `cwnd`. It starts small and grows until packet loss occurs.

## 3. Congestion Algorithms: The Evolution

### 3.1 TCP Reno (The Classic - Loss Based)
*   **Slow Start:** Double `cwnd` every RTT (Exponential).
*   **Congestion Avoidance:** Upon `ssthresh`, increase `cwnd` linearly (+1 MSS per RTT).
*   **AIMD:** Additive Increase, Multiplicative Decrease.
    *   Packet Loss? Cut `cwnd` in half.
*   **Flaw:** In high-speed networks, recovering from a 50% cut takes too long.

### 3.2 TCP CUBIC (The Standard - Loss Based)
Default in Linux since 2.6.19.
*   **Concept:** Instead of Linear increase, use a **Cubic Function** ($f(t) = Ct^3$).
*   **Mechanism:**
    *   When loss happens, remember `W_max`.
    *   Ramp up fast to regain `W_max`, slow down near the limit, then accelerate fast if no loss is found.
*   **Benefit:** Independent of RTT. Very efficient on High Bandwidth-Delay Product (BDP) links (e.g., Transatlantic Fiber).

### 3.3 TCP BBR (The Modern - Model Based)
Google's "Bottleneck Bandwidth and RTT" (2016).
*   **Paradigm Shift:** **Loss $
eq$ Congestion.**
    *   Loss can be random (WiFi noise). Reno/Cubic panic and slow down.
*   **Mechanism:**
    *   Estimates **BtlBw** (Bottleneck Bandwidth) and **RTprop** (Round Trip Propagation).
    *   **Pacing:** Sends data at exactly the BtlBw rate.
    *   Does not fill buffers (avoids Bufferbloat).
*   **Result:** High throughput even with 1-5% packet loss. Critical for modern internet.

---

## Exercises

### Exercise 1 — Observe the TCP Three-Way Handshake with tcpdump
**Setup:** Two terminals on a Linux host (or one host + a remote server).
1. In terminal A, start a capture: `sudo tcpdump -i any -nn -S 'tcp port 443 and (tcp-syn|tcp-ack)' -c 6 -w /tmp/handshake.pcap`
2. In terminal B, initiate a TLS connection: `curl -so /dev/null https://example.com`
3. Stop the capture and read it: `tcpdump -r /tmp/handshake.pcap -nn -S`
4. Identify the SYN, SYN-ACK, and ACK packets. Note the sequence numbers and the Window Scale option advertised in SYN/SYN-ACK.
**Expected output:** Three packets showing `Flags [S]`, `Flags [S.]`, `Flags [.]` with `wscale` values in the options field.

### Exercise 2 — Map TCP States with ss
1. Open a long-lived connection: `curl -so /dev/null --limit-rate 1k https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso &`
2. In another terminal, run: `ss -tanop | grep -E 'ESTAB|FIN-WAIT|CLOSE-WAIT|TIME-WAIT'`
3. Kill the curl process (`kill %1`) and immediately re-run `ss -tanop` every second for 10 seconds.
4. Document the state transitions you observe (ESTABLISHED -> FIN_WAIT_1 -> FIN_WAIT_2 -> TIME_WAIT).
**Expected output:** A clear sequence of state changes ending in TIME_WAIT, persisting for 2xMSL (typically 60 s on Linux).

### Exercise 3 — Compare CUBIC and BBR Throughput
**Prerequisites:** Linux kernel >= 4.9, `iperf3` installed on two hosts (or localhost loopback with `tc netem` for simulated loss).
1. Add 1% packet loss: `sudo tc qdisc add dev lo root netem loss 1%`
2. Start iperf3 server: `iperf3 -s`
3. Run a 30-second test with CUBIC: `iperf3 -c 127.0.0.1 -t 30 -C cubic`
4. Run a 30-second test with BBR: `iperf3 -c 127.0.0.1 -t 30 -C bbr`
5. Compare the throughput and retransmission count from both runs.
6. Clean up: `sudo tc qdisc del dev lo root`
**Expected output:** BBR achieves significantly higher throughput under 1% loss because it does not treat loss as a congestion signal.

### Exercise 4 — Tune Sysctl Parameters and Measure Impact
1. Record current values: `sysctl net.ipv4.tcp_window_scaling net.ipv4.tcp_sack net.core.rmem_max net.core.wmem_max`
2. Increase buffer limits: `sudo sysctl -w net.core.rmem_max=16777216` and `sudo sysctl -w net.core.wmem_max=16777216`
3. Set TCP buffer auto-tuning range: `sudo sysctl -w net.ipv4.tcp_rmem="4096 131072 16777216"` and `sudo sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216"`
4. Run `iperf3 -c <remote-host> -t 20` before and after the change on a high-latency link (or use `tc netem delay 100ms`).
5. Observe the difference in throughput and compute the BDP to verify the buffers are large enough.
**Expected output:** Throughput increases on high-BDP links because the kernel can now keep a larger volume of data in flight.

### Exercise 5 — Detect CLOSE_WAIT Leaks
1. Write a minimal Python server that accepts connections but never calls `conn.close()` after receiving EOF:
   ```python
   import socket
   s = socket.socket(); s.bind(('',9999)); s.listen(1)
   while True:
       conn, _ = s.accept()
       data = conn.recv(1024)  # read but never close
   ```
2. Connect and disconnect from another terminal: `echo hello | nc -q0 localhost 9999`
3. Run `ss -tanop | grep 9999` — observe the socket stuck in CLOSE_WAIT on the server side.
4. Fix the server by adding `conn.close()` after `recv()` and verify the socket transitions to LAST_ACK then disappears.
**Expected output:** Without the fix, `ss` shows an ever-growing list of CLOSE_WAIT sockets (resource leak). With the fix, sockets close cleanly.

---

## Readings and References

### RFCs and Standards
- **RFC 793** — Transmission Control Protocol. <https://datatracker.ietf.org/doc/html/rfc793> (retrieved: 2026-05-29)
- **RFC 5681** — TCP Congestion Control (slow start, congestion avoidance, fast retransmit, fast recovery). <https://datatracker.ietf.org/doc/html/rfc5681> (retrieved: 2026-05-29)
- **RFC 7323** — TCP Extensions for High Performance (Window Scaling, Timestamps). <https://datatracker.ietf.org/doc/html/rfc7323> (retrieved: 2026-05-29)
- **RFC 2018** — TCP Selective Acknowledgment Options (SACK). <https://datatracker.ietf.org/doc/html/rfc2018> (retrieved: 2026-05-29)
- **RFC 3168** — The Addition of Explicit Congestion Notification (ECN) to IP. <https://datatracker.ietf.org/doc/html/rfc3168> (retrieved: 2026-05-29)
- **RFC 9438** — CUBIC for Fast and Long-Distance Networks (Standards Track, obsoletes RFC 8312). <https://datatracker.ietf.org/doc/html/rfc9438> (retrieved: 2026-05-29)
- **Internet-Draft: BBR Congestion Control** — draft-ietf-ccwg-bbr (Work in Progress, experimental). <https://datatracker.ietf.org/doc/draft-ietf-ccwg-bbr/> (retrieved: 2026-05-29)

### Official Documentation
- **Linux Kernel — IP Sysctl** — TCP tunables reference (tcp_rmem, tcp_wmem, tcp_congestion_control, etc.). <https://docs.kernel.org/networking/ip-sysctl.html> (retrieved: 2026-05-29)
- **Linux Kernel — TCP protocol** — Kernel TCP implementation notes. <https://www.kernel.org/doc/Documentation/networking/tcp.txt> (retrieved: 2026-05-29)
- **ESnet Fasterdata — Linux Tuning** — Host tuning guide for high-performance networking. <https://fasterdata.es.net/host-tuning/linux/> (retrieved: 2026-05-29)

### Books
- Stevens, W. R., *TCP/IP Illustrated, Volume 1: The Protocols*, 2nd ed., Addison-Wesley, 2011.
- Fall, K. & Stevens, W. R., *TCP/IP Illustrated, Volume 2: The Implementation*, Addison-Wesley, 1995.
- Cardwell, N. et al., "BBR: Congestion-Based Congestion Control," *ACM Queue*, vol. 14, no. 5, 2016. <https://research.google/pubs/bbr-congestion-based-congestion-control-2/>

---

## Cross-References

| Module | Relationship |
|---|---|
| `01_OS_Internals_Processes_Memory.md` | Kernel socket buffers, process scheduling of network I/O, interrupt handling for NIC drivers |
| `01_a_CPU_Kernel_Boundary.md` | System calls (`socket`, `bind`, `connect`, `send`, `recv`), user-kernel boundary for network stack |
| `01_d_File_Systems_Storage.md` | `sendfile()` zero-copy I/O, page cache interaction with TCP write path |
| `02_a_Modern_Protocols_HTTP_QUIC.md` | HTTP/2 over TCP vs HTTP/3 over QUIC; TCP HOL blocking motivates QUIC design |
| `03_Advanced_Data_Structures_Algorithms.md` | Hash tables in connection tracking, timer wheels for retransmission, red-black trees in CUBIC |
| `04_Compilers_Interpreters.md` | BPF/eBPF programs compiled for in-kernel packet filtering and TCP congestion control |

---

## Glossary

| Term | Definition |
|---|---|
| **MSS** | Maximum Segment Size — the largest payload (excluding headers) a TCP segment can carry, typically 1460 bytes on Ethernet |
| **RTT** | Round-Trip Time — elapsed time for a segment to reach the receiver and its ACK to return |
| **BDP** | Bandwidth-Delay Product — the volume of data (in bytes) that can be in flight on a link; equals bandwidth x RTT |
| **cwnd** | Congestion Window — sender-side variable limiting how much unacknowledged data may be in flight |
| **rwnd** | Receiver Window — advertised by the receiver in each ACK to prevent buffer overflow |
| **SACK** | Selective Acknowledgment — TCP option allowing the receiver to report non-contiguous blocks received, enabling efficient loss recovery |
| **ECN** | Explicit Congestion Notification — mechanism where routers mark packets instead of dropping them to signal congestion |
| **AIMD** | Additive Increase / Multiplicative Decrease — the classic congestion control strategy used by Reno |
| **ssthresh** | Slow Start Threshold — the cwnd value at which TCP transitions from exponential (slow start) to linear (congestion avoidance) growth |
| **TIME_WAIT** | TCP state entered by the side that initiates close; lasts 2xMSL to absorb delayed segments |
| **CLOSE_WAIT** | TCP state on the passive-close side indicating the remote peer has sent FIN but the local application has not yet called close() |
| **Bufferbloat** | Excessive latency caused by oversized network buffers that queue packets instead of signaling congestion |
| **LFN** | Long Fat Network — a path with high bandwidth and high delay (large BDP), requiring window scaling for full utilization |
| **Window Scaling** | TCP option (RFC 7323) that shifts the 16-bit window field to support receive windows up to 1 GB |
