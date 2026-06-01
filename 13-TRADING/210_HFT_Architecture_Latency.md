# 210 — HFT Architecture and Latency Engineering

> Engineering reference for high-frequency trading systems. Covers the latency budget anatomy, kernel-bypass networking, NIC selection, CPU/memory architecture, lock-free programming, FPGA acceleration, time synchronization, co-location, microwave links, software architecture, exchange protocols, fault tolerance, and regulatory compliance. Self-contained beyond document 201.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Latency Budget Anatomy](#latency-budget)
3. [Network Stack Basics](#network-basics)
4. [Kernel Bypass Networking](#kernel-bypass)
5. [NIC Selection](#nic-selection)
6. [CPU Pinning and Isolation](#cpu-pinning)
7. [Memory Architecture](#memory)
8. [Lock-Free Programming](#lock-free)
9. [Microbenchmarking](#benchmarking)
10. [FPGA Acceleration](#fpga)
11. [ASIC for Ultra-Low-Latency](#asic)
12. [Time Synchronization](#time-sync)
13. [Co-Location](#colo)
14. [Microwave and Hollow-Core Fiber](#microwave)
15. [Software Architecture for Low-Latency C++](#cpp-arch)
16. [Risk Gates](#risk-gates)
17. [Order Entry Protocols](#order-protocols)
18. [Market Data Parsing](#market-data)
19. [Gateway Architecture](#gateway)
20. [Strategy Engine](#strategy-engine)
21. [Backtesting at HFT Scale](#hft-backtesting)
22. [A/B Testing in Production](#ab-testing)
23. [Monitoring and Observability](#monitoring)
24. [Fault Tolerance](#fault-tolerance)
25. [Capacity Planning](#capacity)
26. [Regulatory Compliance](#compliance)
27. [Code Examples](#code)
28. [Case Studies](#cases)
29. [Reality Checks](#reality-checks)
30. [Reference Tables, Cheat Sheets, Bibliography](#reference)

---

## Introduction

High-frequency trading is a systems-engineering discipline as much as a quantitative one. The mathematical edge in a typical HFT strategy is small — a fraction of a basis point per trade. Capturing it requires being faster than the competition by margins measured in nanoseconds. This means the engineering stack — from NIC firmware to user-space code — is the differentiator between profit and loss.

The latency arms race has stabilized in some respects (most participants have invested in similar hardware) but remains active in others (FPGA logic, microwave network paths, novel chip designs). For a hedge fund or prop shop entering HFT, the choice is not whether to pay for latency but how much to pay. Each microsecond saved costs progressively more, and the marginal return depends on the specific strategy.

This document maps the engineering surface area. We assume the reader has a programming background (C++ or Rust preferred) and basic understanding of computer architecture. For the strategy side, document 201 covers microstructure theory and document 208 covers execution; this document focuses on *how to make code fast enough to act on those signals*.

A practical framing. Every microsecond shaved from the round-trip latency translates to a marginal increase in the probability of being first to a profitable opportunity. For a typical latency-arbitrage strategy, the relationship is approximately:

$$
\text{Profitability rate} \propto \int_{t}^{T} P(\text{first arrival in interval}) \cdot \text{value of arbitrage} \, dt.
$$

Going from 5μs to 2μs round-trip multiplies the rate by 2-3× depending on competitive density. Beyond that, returns diminish — at sub-microsecond scales, the variance of the latency distribution dominates the mean.

---

## Latency Budget Anatomy

A typical HFT round-trip:

| Component | Typical Latency | Notes |
|---|---|---|
| Wire to NIC | ~50ns | Photons in fiber over 10m |
| NIC to OS / app | ~250ns–10μs | Kernel bypass: 250-500ns; standard: 5-15μs |
| Market data parse | ~50-500ns | Software / FPGA |
| Decision logic | ~100ns–10μs | Strategy-dependent |
| Order construct | ~50-200ns | Serialize protocol |
| App to NIC | ~250ns–10μs | Symmetric to incoming |
| NIC to wire | ~50ns | Outgoing photon |
| Wire to exchange | ~50ns–5μs | Co-loc: <1μs; cross-DC: more |
| Exchange match | varies | Outside our control |

Total wire-to-wire (excluding exchange): a tier-1 HFT firm achieves 800ns to 3μs. Exchange match latency adds 5-50μs typically.

### Exchange-side Latency

Different exchanges:
- Nasdaq: ~5-20μs round trip.
- NYSE: ~10-30μs.
- CME (futures): ~10-40μs.
- Eurex: ~15-50μs.

The matching engine itself takes ~1-5μs; the rest is gateway and order book processing.

### What to Optimize

For a 1μs decision logic, optimizing it to 100ns is 9x improvement. For a 5ms market data feed, optimizing the feed by 10ms (impossible) doesn't move the needle. Target the largest costs first.

---

## Network Stack Basics

### TCP vs UDP

- **TCP**: ordered, reliable, slow. Used for order entry where reliability matters.
- **UDP**: unordered, lossy, fast. Used for market data multicast where speed matters.

### Multicast for Market Data

Exchanges broadcast market data via UDP multicast. Subscribers receive identical copies without exchange-side per-subscriber processing.

### Message Protocols

| Protocol | Use | Format |
|---|---|---|
| FIX | Order entry, less time-critical | ASCII tag-value |
| ITCH | Market data (Nasdaq) | Binary, fixed-width |
| OUCH | Order entry (Nasdaq) | Binary, fixed-width |
| SBE | Generic binary | Schema-defined |
| FAST | Compressed FIX | Variable-length |
| ASTS | Direct exchange protocol | Binary |
| MDP 3.0 | CME Globex market data | Binary |

Binary protocols (ITCH, OUCH, SBE) are 5-10× faster to parse than ASCII (FIX).

### Sequence Numbers and Recovery

UDP loses packets. Multicast feeds use sequence numbers; subscribers detect gaps and request retransmission via separate TCP channel. Retransmission adds latency but is mandatory for state consistency.

---

## Kernel Bypass Networking

The Linux kernel network stack is too slow for HFT (5-10μs per packet through TCP/IP). Kernel bypass moves packet processing into userspace.

### DPDK (Data Plane Development Kit)

Open-source. Provides:
- Polled-mode drivers (no interrupts, busy-poll).
- Hugepages and DMA buffers.
- Ring buffers between NIC and userspace.

Result: 100-300ns per packet, plus user code latency.

### OpenOnload (Solarflare)

Commercial. Provides:
- TCP/UDP stack in userspace.
- Hardware offload of stateful operations.
- Compatible with standard sockets API.

Result: similar to DPDK with less coding effort.

### Mellanox VMA / RDMA

Mellanox Voltaire Messaging Accelerator. Direct memory access patterns:
- Message-driven I/O.
- Zero-copy.
- Submicrosecond latency.

### io_uring

Newer Linux kernel feature (5.1+). Asynchronous I/O with reduced context switching. Slower than DPDK but easier integration with existing code.

### Trade-offs

- DPDK: max performance, more development cost.
- OpenOnload: good performance, lower dev cost (binary compatibility with sockets).
- io_uring: standard kernel, moderate performance gain.

For tier-1 HFT, DPDK or kernel-bypass equivalent is mandatory. For tier-2 latency-tolerant strategies, io_uring is sufficient.

---

## NIC Selection

NIC choice affects raw latency and available offload features.

| NIC | Latency (sub-μs) | Hardware Offload | Notes |
|---|---|---|---|
| Mellanox ConnectX-7 | ~250ns | RDMA, RoCE, GPU-Direct | Standard tier-1 |
| Solarflare X2 | ~400ns | TCP offload, OpenOnload | Strong sub-μs |
| Exablaze | ~80ns | FPGA-based | Niche tier-1 (acquired by Cisco) |
| Intel 800 series | ~500ns | RDMA | Common, accessible |
| Broadcom NetXtreme | ~600ns | Standard | Cheaper alternative |

### FPGA NIC

Some firms use FPGA NICs (Exablaze) for on-NIC parsing of market data. The FPGA decodes the binary protocol and outputs structured data to host memory directly. Saves 200-500ns of host-side parsing.

### Latency vs Bandwidth

For HFT, latency (single-packet round-trip) matters more than bandwidth. A 10Gbps NIC at 250ns latency beats a 100Gbps NIC at 1μs latency for HFT.

---

## CPU Pinning and Isolation

### CPU Affinity (Pinning)

Bind specific threads to specific CPU cores. Prevents OS scheduler from migrating the thread, which would invalidate L1/L2 caches.

```bash
# Pin process to core 5
taskset -c 5 ./hft_engine

# Or in code:
# pthread_setaffinity_np(...) with cpu_set_t containing core 5
```

### isolcpus

Boot parameter to remove CPU cores from the OS scheduler entirely:

```
# /etc/default/grub
GRUB_CMDLINE_LINUX="isolcpus=4-15 nohz_full=4-15 rcu_nocbs=4-15"
```

Cores 4-15 are removed from the scheduler. Userspace must explicitly pin to them.

### NUMA Awareness

Multi-socket servers have non-uniform memory access. Memory access local to a CPU's NUMA node is faster than cross-node.

```bash
# Check NUMA topology
numactl --hardware

# Run on NUMA node 0 with memory from node 0
numactl --cpunodebind=0 --membind=0 ./hft_engine
```

For HFT: keep network buffers, code, and data on the same NUMA node as the trading thread.

### Hyperthreading

Disable hyperthreading. Competing logical cores share execution resources, adding jitter.

```bash
# Disable HT in BIOS, or via:
echo 0 > /sys/devices/system/cpu/cpu5/online  # disable hyperthread sibling
```

### CPU Governor

Set to "performance" mode. Default "powersave" reduces frequency under low load, adding latency on first packet.

```bash
echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Cache Effects

Hot path code and data should fit in L1/L2:
- L1 instruction: 32KB typical.
- L1 data: 32KB.
- L2: 256KB-1MB.
- L3: 8-64MB shared.

Profile with `perf` to find cache misses on the hot path.

---

## Memory Architecture

### Cache Lines

64-byte cache line is the unit of memory transfer. Avoid:
- **False sharing**: two threads writing to different variables on the same cache line cause cache invalidation pings.
- **Cache thrashing**: data structure access patterns that exceed cache size.

### Padding for False Sharing

```cpp
struct alignas(64) ThreadCounter {
    std::atomic<uint64_t> count;
    char padding[64 - sizeof(std::atomic<uint64_t>)];
};
ThreadCounter counters[NUM_THREADS];
```

Each counter on its own cache line; no false sharing.

### Hugepages

Default page size is 4KB. With 2MB hugepages, TLB (translation lookaside buffer) can cover more memory with fewer entries:

```bash
echo 1024 > /proc/sys/vm/nr_hugepages
```

Allocate huge pages for shared memory and DPDK.

### Memory Prefetching

CPUs predict memory access; explicit prefetching can help:

```cpp
__builtin_prefetch(&next_data, 0, 3);  // read, high temporal locality
```

Most useful when iterating over sequential data with predictable access patterns.

### Lock-Free Data Structures

Mutexes are slow (microseconds). Lock-free alternatives:
- **Single Producer Single Consumer (SPSC) ring buffer**: most efficient.
- **MPMC ring buffer**: more complex; higher contention.
- **Hazard pointers**: alternative to reference counting for shared pointers.

### NUMA Memory Allocation

Allocate memory on the same NUMA node as the consuming CPU:

```cpp
// libnuma
void* mem = numa_alloc_onnode(size, node_id);
```

Cross-NUMA memory access is 50-100ns slower than local.

---

## Lock-Free Programming

### Atomics

C++ `std::atomic<T>` provides hardware-supported atomic operations:
- load, store: with memory_order specification.
- exchange, compare_exchange_strong, compare_exchange_weak: CAS operations.
- fetch_add, fetch_sub: atomic arithmetic.

### Memory Ordering

| Order | Guarantee | Performance |
|---|---|---|
| memory_order_relaxed | Atomicity only | Fastest |
| memory_order_acquire | No reads can move before this load | Moderate |
| memory_order_release | No writes can move after this store | Moderate |
| memory_order_acq_rel | Both | Slow |
| memory_order_seq_cst | Total order | Slowest |

For high-throughput, use the weakest ordering that guarantees correctness.

### MPMC Ring Buffer

```cpp
template<typename T, size_t N>
class MPMC_Queue {
    std::atomic<size_t> head_{0};
    std::atomic<size_t> tail_{0};
    T buffer_[N];
    
public:
    bool try_push(const T& item) {
        size_t tail = tail_.load(std::memory_order_relaxed);
        size_t next_tail = (tail + 1) % N;
        if (next_tail == head_.load(std::memory_order_acquire)) return false;
        buffer_[tail] = item;
        tail_.store(next_tail, std::memory_order_release);
        return true;
    }
    
    bool try_pop(T& item) {
        size_t head = head_.load(std::memory_order_relaxed);
        if (head == tail_.load(std::memory_order_acquire)) return false;
        item = buffer_[head];
        head_.store((head + 1) % N, std::memory_order_release);
        return true;
    }
};
```

For full SPSC/MPMC with proper memory ordering, see Boost.Lockfree, Disruptor pattern (LMAX), or Folly MPMCQueue.

### Hazard Pointers

For atomic shared pointers without reference counting overhead:
- Each thread maintains a list of "hazard pointers" — pointers it is currently using.
- Before deletion, check that no hazard pointer references the object.

Used in concurrent containers (e.g., MPSC queues with dynamic allocation).

---

## Microbenchmarking

Measuring nanoseconds requires careful methodology.

### RDTSC (x86 timestamp counter)

Read CPU cycle counter directly:

```cpp
inline uint64_t rdtsc() {
    uint32_t lo, hi;
    __asm__ __volatile__ ("rdtsc" : "=a" (lo), "=d" (hi));
    return ((uint64_t)hi << 32) | lo;
}
```

Caveat: rdtsc itself takes ~30 cycles. Across NUMA nodes, RDTSC values may differ. Use `rdtscp` for serialized reads (more expensive but more accurate).

### perf

Linux `perf` tool measures CPU events:

```bash
perf stat -e cache-misses,branch-misses ./benchmark
perf record -g ./benchmark
perf report
```

Provides cache misses, branch mispredictions, instruction counts.

### Intel VTune

Commercial profiler with deeper microarchitecture insights. Useful for finding pipeline stalls.

### Statistical Discipline

Single measurements are unreliable. Run benchmark N times, report:
- Median, mean, max.
- 99th, 99.9th percentile (tail latency matters most for HFT).
- Compare distributions, not point estimates.

### FPGA Verification

For sub-microsecond claims, verify with FPGA-timestamped packets:
- FPGA timestamps incoming packet at NIC.
- FPGA timestamps outgoing packet.
- Difference is wire-to-wire latency (no software clock drift).

---

## FPGA Acceleration

FPGAs provide deterministic, low-latency processing for selected hot path operations.

### What Goes on FPGA

- **Market data parsing**: ITCH/OUCH/SBE decoder. Output structured data.
- **Order book maintenance**: build top-N book in hardware.
- **Risk gates**: pre-trade risk checks (position limits, etc.).
- **Simple strategies**: triangular arbitrage detector, NBBO checker.
- **Order serialization**: build outgoing OUCH packet.

### FPGA Tools

- **Verilog/VHDL**: traditional HDL. Maximum control, longest dev time.
- **Vivado HLS, Catapult**: high-level synthesis from C++. Faster dev.
- **OpenCL FPGA**: more accessible, less performant.

### Commercial FPGA Cores

- **Algo-Logic**: order book maintenance, FIX parser.
- **AccelTrade**: full HFT FPGA stack.
- **Solarflare AOE**: programmable NIC + FPGA.

Cost: $10K-$100K per FPGA card; integration cost is bigger.

### When to Use FPGA

Cost-benefit: FPGA project is 6-18 months for 200-500ns reduction. Worth it for:
- Strategies competing on raw latency (latency arb).
- High-frequency operations on hot path.

Not worth for:
- Strategies competing on data quality or signal strength.
- Low-frequency or research-stage strategies.

---

## ASIC for Ultra-Low-Latency

Custom ASICs eliminate FPGA overhead but require huge upfront investment ($500K-$5M NRE per chip). Used by:
- Top-tier HFT firms (Jump, Citadel, Tower).
- Specific use cases (matching engines, FPGA-replacement chips).

For 99.9% of HFT firms, FPGA is the best speed/cost trade-off.

---

## Time Synchronization

Critical for:
- Order timestamping.
- Cross-venue latency measurement.
- Regulatory compliance (audit trails).

### NTP

Network Time Protocol. Accuracy: ~1ms. Insufficient for HFT.

### PTP (IEEE 1588)

Precision Time Protocol. Hardware-supported in NICs and switches. Accuracy: ~100ns to ~1μs.

```bash
# Sync time via PTP
ptp4l -i eth0 -m -H
phc2sys -s eth0 -O 0
```

### White Rabbit

Sub-nanosecond accuracy. Used at CERN. Some HFT firms deploy for ultra-precise timing.

### Co-location Time

Within an exchange data center, all firms can sync to same source. Cross-DC requires PTP grandmaster + GPS reference.

---

## Co-Location

Physical proximity to the matching engine. Major data centers:

- **NY4, NJ5 (Equinix New Jersey)**: NYSE, Nasdaq.
- **LD4, LD5 (Equinix London)**: LSE, Eurex.
- **TY3 (Equinix Tokyo)**: Tokyo Stock Exchange, JPX.
- **CH4 (Equinix Chicago)**: CME.
- **SG3 (Equinix Singapore)**: SGX.

### Cross-Connect

Physical fiber connection from your rack to exchange's rack:
- Length matters (each meter = 5ns).
- Routing through patches adds ns.
- Tier-1 firms negotiate "best paths."

### Floor Switches

In-DC switches add latency:
- Cisco Nexus: 1-3μs.
- Arista: 500ns-1μs.
- Mellanox: 300-700ns.
- Custom FPGA switches: <100ns.

For HFT hot path, prefer direct cross-connect over switch routing.

---

## Microwave and Hollow-Core Fiber

For cross-data-center connections, microwave is faster than fiber:
- Fiber: ~5μs/km (light slows in glass).
- Microwave: ~3.3μs/km (speed of light in air).

### Major Microwave Routes

- **Aurora-Mahwah** (Chicago-NYC): connects CME futures (Aurora, IL) to NYSE/Nasdaq (NYC). ~4ms one-way.
- **Slough-Frankfurt**: London exchanges to Eurex.
- **Tokyo-Singapore**: regional Asia routing.

### Providers

- McKay Brothers, New Line Networks, Quincy: commercial microwave providers.
- Custom: some HFT firms own their own routes.

### Hollow-Core Fiber

Newer technology: light travels at near-vacuum speed in hollow fiber:
- ~3.3μs/km — same as microwave.
- More reliable than microwave (weather-resistant).
- Limited deployment.

### Trade-offs

- Microwave: weather-sensitive (rain fade), bandwidth-limited.
- Fiber: reliable, high bandwidth, slightly slower.

Tier-1 firms use both: microwave primary, fiber backup.

---

## Software Architecture for Low-Latency C++

### Single-Threaded Hot Path

The trading thread must be single-threaded:
- No locks (other threads excluded from hot path).
- Cache-friendly (single thread keeps locality).
- Predictable (no scheduler interference).

Other threads (logging, monitoring, GUI) run on isolated cores.

### Mechanical Sympathy

Code aware of CPU architecture:
- Branch prediction-friendly: predictable patterns.
- Pipeline-friendly: avoid dependent instruction chains.
- Cache-friendly: data locality, prefetch.

### No Allocations on Hot Path

Heap allocation is unpredictable (5-1000ns). Avoid by:
- Object pools.
- Stack allocation.
- Pre-allocated buffers.

### Inline / Constexpr / Templates

- Inline small functions to avoid call overhead.
- constexpr for compile-time computation.
- Templates for type-specialized code without runtime branching.

### Branch Prediction

```cpp
if (__builtin_expect(rare_condition, 0)) {
    // Cold path
}
```

Hint to compiler that condition is rarely true. Allows it to optimize hot path layout.

### Sample Hot Path

```cpp
// Pseudo-code
struct Quote { uint64_t timestamp; double bid, ask; };

inline void on_market_data(const Quote& q) {
    // No allocations, no locks, no syscalls
    if (__builtin_expect(strategy.signal(q), 0)) {
        // Construct order in pre-allocated buffer
        order_buffer[buf_idx++ & MASK].populate(q);
        // Send via DPDK
        dpdk_send(order_buffer);
    }
}
```

---

## Risk Gates

Pre-trade risk checks must complete in nanoseconds:

### Position Limits

Track current position; reject orders that would exceed limits. Implementation: per-symbol atomic counter.

### Per-Order Size Limits

Reject orders > max_size. Simple comparison.

### Daily Loss Limits

If realized P&L below threshold, halt. Atomic flag.

### Throughput Limits

Reject if order rate > threshold. Sliding window counter.

### FPGA Risk Gate

For sub-microsecond gates:
- FPGA on outbound path checks every order.
- Software path validates state.
- FPGA enforces hard limits.

### Reality Check — Risk vs Speed

A risk gate that adds 200ns and saves $1M from one bad order is worth it. Production firms over-invest in risk gates relative to pure speed: a single un-gated rogue strategy has bankrupted firms (Knight Capital 2012, $440M loss in 30 minutes).

---

## Order Entry Protocols

### FIX (Financial Information Exchange)

ASCII tag-value protocol. Slow but human-readable. Used for:
- Order entry where reliability and standardization matter.
- Cross-venue connectivity.

### OUCH (Nasdaq)

Binary order entry. Each message is a single packed C struct.

```c
struct OuchEnterOrder {
    uint8_t  type;        // 'O'
    uint64_t order_token;
    uint8_t  side;        // 'B' or 'S'
    uint32_t shares;
    char     stock[8];
    uint32_t price;       // 1/10000 of $
    uint32_t time_in_force;
    char     firm[4];
    char     display;     // 'Y'/'N'
    char     capacity;
    char     intermarket;
    char     min_qty[4];
    char     cross_type;
    char     customer;
};
```

48 bytes, deterministic parse time.

### EOBI (Eurex)

Eurex's binary protocol.

### Session Management

Login with client ID. Heartbeats every 30s. Sequence numbers track all messages. Disconnection: re-login, fetch missed sequences.

---

## Market Data Parsing

### ITCH 5.0 (Nasdaq)

Binary, fixed-width messages. Common types:
- `T`: timestamp (seconds).
- `A`: add order.
- `E`: order executed.
- `X`: order cancel.
- `D`: order delete.
- `U`: order replace.

### Software ITCH Parser

```cpp
inline void parse_itch_message(const char* buf, size_t len) {
    char type = buf[0];
    switch (type) {
        case 'A': parse_add_order(buf); break;
        case 'E': parse_execution(buf); break;
        case 'X': parse_cancel(buf); break;
        // ...
    }
}

inline void parse_add_order(const char* buf) {
    AddOrder ao;
    memcpy(&ao, buf, sizeof(AddOrder));
    // Network byte order to host order
    ao.order_id = be64toh(ao.order_id);
    ao.shares = be32toh(ao.shares);
    ao.price = be32toh(ao.price);
    // Apply to order book
    book.add(ao);
}
```

Optimized parser: 50-200ns per message.

### FPGA Parser

FPGA decodes ITCH messages and outputs structured data via PCIe DMA. Saves software parsing cost.

### SBE (Simple Binary Encoding)

CME, Eurex, others use SBE. Schema-defined messages with code generation. Faster than FIX, slower than OUCH/ITCH due to optional fields.

---

## Gateway Architecture

The gateway translates between exchange protocol and internal message bus:

- **Inbound**: parse market data → publish on internal bus.
- **Outbound**: receive order from strategy → format → send to exchange.

### Architecture

```
[Exchange]  <==>  [Gateway]  <==>  [Strategy Engine]
                  - Parse        - Trade decisions
                  - Risk gate    - Risk management
                  - Translate    - Allocation
```

Multiple gateways per strategy engine (one per venue). Each gateway has its own latency profile.

### Reliability

- Gateway failures must not affect other gateways.
- Hot standby gateways take over within milliseconds.
- Strategy engine sees venue list with availability flags.

---

## Strategy Engine

### Hot Path

The "hot path" is:
1. Receive market data.
2. Update internal state.
3. Run strategy logic.
4. Decide if/when/where to trade.
5. Send order.

All on a single isolated CPU core. Sub-microsecond budget.

### Cold Path

The "cold path" is:
- Logging (writes to ring buffer; another thread persists).
- Monitoring (publishes metrics to another thread).
- Risk recomputation (runs periodically, not per message).
- Strategy recalibration (overnight, not real-time).

Cold path runs on different cores from hot path.

### Strategy Logic

Strategies are typically:
- **Stateful**: maintain internal model, update on each tick.
- **Decision-light**: most ticks don't trigger trades.
- **Branch-light**: minimize unpredictable branches on hot path.

Pseudo-code:

```cpp
class MarketMakingStrategy {
    OrderBook book;
    Position position;
    
    void on_tick(const Quote& q) {
        book.update(q);
        // Compute fair value
        double fair = compute_fair();
        // Compute desired quotes given inventory
        auto [bid, ask] = compute_quotes(fair, position);
        // Send if quotes have changed
        if (bid != current_bid || ask != current_ask) {
            cancel_replace(bid, ask);
        }
    }
};
```

---

## Backtesting at HFT Scale

### Tick-by-Tick Replay

Replay historical market data tick-by-tick into the strategy engine. Simulate exchange responses.

### Realistic Order Book Simulation

Naive simulation: assume your orders fill if price reaches them. Reality: queue position matters.

Sophisticated simulator:
- Track queue position based on order time and size.
- Simulate cancellations by other queue participants.
- Model partial fills.

### Computational Cost

A single day of US equity tick data is ~100-500GB. Replaying and simulating one day takes:
- Naive: ~1-5 minutes per CPU.
- Realistic: 30-60 minutes per CPU.

For a year of data, parallelize across hundreds of cores.

### Production Backtesters

- Open-source: Backtrader, zipline, vectorbt — not HFT-grade.
- Commercial: Imandra, Strategy Studio.
- Internal: most HFT firms build their own.

---

## A/B Testing in Production

### Canary Deployments

New strategy rolls out gradually:
1. Run on 1% of capital for 1-7 days.
2. Compare to control (existing strategy).
3. If profitable and stable, ramp to 10%.
4. Iterate.

### Shadow Mode

Run new strategy alongside production but without sending orders. Compare predicted P&L to actual market moves. If predictions match, deploy live.

### Risk Limits per Variant

Each variant has its own risk limits. Aggregated risk monitored at portfolio level.

---

## Monitoring and Observability

### Metrics to Track

- **Latency**: per-message wire-to-wire, p50, p99, p99.9.
- **Order rate**: messages per second.
- **Fill rate**: order acknowledgments per submission.
- **Reject rate**: by reason (rate limit, risk, exchange).
- **P&L**: realized, unrealized, by strategy and asset.
- **Risk metrics**: VaR, position limits, gross/net exposure.
- **System**: CPU, memory, network packet loss.

### Tools

- **Prometheus + Grafana**: standard monitoring stack.
- **InfluxDB**: time-series database for high-cardinality metrics.
- **OpenTelemetry**: distributed tracing.

### Alerts

- Hard alerts: position limit breach, P&L floor, system failure.
- Soft alerts: latency degradation, fill rate drop, anomalous behavior.

---

## Fault Tolerance

### Redundancy

- Hot standby for critical components.
- Active-active where possible (same strategy on multiple machines).
- Data replication: market data feed split across multiple paths.

### Failover Time

For HFT, failover must be sub-second:
- Detect failure (heartbeat, packet loss).
- Activate standby.
- Resume operations.

### Message Deduplication

If hot standby is also processing messages, deduplicate at output (only one order to exchange).

---

## Capacity Planning

### Peak Message Rates

US equity peaks: 100M+ messages/second across all symbols. Per-strategy: typically 1-10M/sec.

### Burst Handling

Market opens, FOMC, etc. cause bursts:
- 10x normal rate for minutes.
- Buffer overflows = lost messages = bad state.

Provision for 5-10x normal rate.

### Capacity per CPU

Modern Xeon CPU at 3GHz: 100M+ small operations/sec. For HFT hot path, 1-10M messages/sec per CPU.

---

## Regulatory Compliance

### MiFID II RTS 6 (EU)

Algorithmic trading regulation requirements:
- Pre-trade risk controls.
- Real-time monitoring.
- Annual self-assessment.
- Stress testing.
- Audit trail of all decisions.

### SEC Market Access Rule (US)

Pre-trade risk controls for direct market access:
- Position limits.
- Per-order size limits.
- Erroneous order prevention.

### Audit Trails

All orders and decisions logged with nanosecond timestamps:
- 5+ years retention.
- Immutable (write-once).
- Available for regulatory inspection.

### Spoofing Prevention

Firm-side controls:
- Track cancellation rates.
- Flag suspicious patterns.
- Internal review before regulatory issue.

Document 78 covers spoofing detection.

---

## Code Examples

### C++ Lock-Free SPSC Queue

```cpp
template<typename T, size_t Size>
class SPSCQueue {
    static_assert((Size & (Size - 1)) == 0, "Size must be power of 2");
    static constexpr size_t Mask = Size - 1;
    
    alignas(64) std::atomic<size_t> head_{0};
    alignas(64) std::atomic<size_t> tail_{0};
    alignas(64) T buffer_[Size];
    
public:
    bool try_push(const T& item) {
        const size_t tail = tail_.load(std::memory_order_relaxed);
        const size_t next = (tail + 1) & Mask;
        if (next == head_.load(std::memory_order_acquire)) return false;
        buffer_[tail] = item;
        tail_.store(next, std::memory_order_release);
        return true;
    }
    
    bool try_pop(T& item) {
        const size_t head = head_.load(std::memory_order_relaxed);
        if (head == tail_.load(std::memory_order_acquire)) return false;
        item = buffer_[head];
        head_.store((head + 1) & Mask, std::memory_order_release);
        return true;
    }
};
```

### Rust for Memory Safety

```rust
use std::sync::atomic::{AtomicUsize, Ordering};

pub struct SpscQueue<T, const N: usize> {
    head: AtomicUsize,
    tail: AtomicUsize,
    buffer: [Option<T>; N],
}

impl<T, const N: usize> SpscQueue<T, N> {
    pub fn try_push(&mut self, item: T) -> Result<(), T> {
        let tail = self.tail.load(Ordering::Relaxed);
        let next = (tail + 1) % N;
        if next == self.head.load(Ordering::Acquire) { return Err(item); }
        self.buffer[tail] = Some(item);
        self.tail.store(next, Ordering::Release);
        Ok(())
    }
}
```

### Python Backtesting Skeleton

```python
import numpy as np
from collections import deque

class HFTBacktester:
    def __init__(self, strategy):
        self.strategy = strategy
        self.book = OrderBook()
        self.positions = {}
        self.pnl = 0
    
    def replay(self, ticks):
        for tick in ticks:
            self.book.update(tick)
            actions = self.strategy.on_tick(tick, self.book)
            for action in actions:
                self.execute(action)
        return self.pnl
    
    def execute(self, action):
        # Simulate fill based on book state
        # Update positions and P&L
        pass
```

---

## Case Studies

### Knight Capital 2012

August 1, 2012: a misconfigured deployment activated a dormant routing module. In 30 minutes, $440M in losses. Lessons:
- Deployment hygiene critical.
- Kill switches must be testable and accessible.
- Risk gates must be defense-in-depth.

### Flash Crash May 6, 2010

3:00pm ET: HFT liquidity withdrew during cascading sell pressure. SPX dropped 9% in minutes; partially recovered within 30 minutes. Lessons:
- HFT liquidity is conditional, not guaranteed.
- Single-event circuit breakers added later.
- Market makers may have legitimate withdrawal during extreme volatility.

### Goldman Code Theft 2009

Programmer Sergey Aleynikov accused of stealing HFT code from Goldman, taken to a competitor. Convicted (later overturned). Lessons:
- IP protection of HFT systems matters.
- Background checks and access controls.

---

## Reality Checks

- **Diminishing returns**: 100ns improvements cost millions and rarely deliver proportional alpha.
- **Vendor lock-in**: NIC, switch, FPGA decisions are sticky.
- **The cost of being last**: in pure latency arbitrage, second place often makes nothing.
- **Strategy diversification**: not all strategies need μs latency; ms-class strategies have different cost economics.
- **Operational risk**: a fast firm with bad ops loses to a slow firm with good ops.

---

## Reference Tables, Cheat Sheets, Bibliography

### Latency Targets

| Tier | Wire-to-Wire | Notes |
|---|---|---|
| Tier 1 | <1μs | FPGA + custom NIC + co-loc |
| Tier 2 | 1-5μs | Standard NIC kernel-bypass |
| Tier 3 | 5-50μs | io_uring or standard kernel |
| Tier 4 | 50μs+ | Cloud-based, retail HFT |

### Bibliography

- **Aldridge, I. (2013), *High-Frequency Trading* (2nd ed.), Wiley.** Practical reference.
- **Lewis, M. (2014), *Flash Boys*, Norton.** Popular but informative.
- **Hasbrouck, J. and Saar, G. (2013), "Low-Latency Trading", *J. Financial Markets* 16(4): 646–679.**
- **Brogaard, J. (2010), "High Frequency Trading and Its Impact on Market Quality", working paper.**
- **Williams, A. (2012), *C++ Concurrency in Action*, Manning.** Lock-free programming.
- **Drepper, U. (2007), "What Every Programmer Should Know About Memory".** Cache and memory.
- **Intel 64 and IA-32 Architectures Optimization Reference Manual.**
- **Budish, E., Cramton, P., Shim, J. (2015), "The High-Frequency Trading Arms Race", *QJE*.**
- **Patterson and Hennessy, *Computer Architecture: A Quantitative Approach*.**
- **CME, Nasdaq, Eurex official protocol documentation.**

### Cross-References

- Document 201 — Microstructure Theory.
- Document 208 — Optimal Execution.
- Document 211 — Backtesting.
- Document 218 — Hedge Fund Risk Operations.
- Document 78 — Spoofing Detection.

---

*End of document 210. ~1,400 lines.*
