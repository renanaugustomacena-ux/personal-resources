# 80 - Queue Position Estimation & Execution Probability: The Line Cutter

**Volume:** 80 of 100
**Strategy Type:** Market Microstructure / HFT / Execution Algo / Smart Order Routing
**Risk Profile:** Non-Execution Risk / Adverse Selection
**Mathematical Basis:** FIFO Logic + Probability of Fill ($P_{fill}$)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: First In, First Out](#2-the-theory-first-in-first-out)
    * 2.1. The Queue: Priority is Price, then Time.
    * 2.2. The Problem: You execute 100ms late, you are #500 in line.
    * 2.3. The Solution: Estimate position to calculate Fill Probability.
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. Input: L3/MBO Data or L2 Estimate.
    * 3.2. Calculation: Track Volume Ahead & Cancellation Rate.
    * 3.3. Signal: if $P_{fill} < 20\%$, Cancel and Improving Price (Jump the Queue).
    * 3.4. Signal: If Queue Depletes Rapidly (Smart Money fleeing), Cancel.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Queue Position ($Pos_t$).
    * 4.2. Fill Probability Formula.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. Penny Jumpers.
    * 5.2. Pro-Rata vs FIFO Matching.
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python: Simulation.
    * 6.2. Rust: Real-time MBO Tracker.
7. [Optimization & Variations](#7-optimization--variations)
8. [Risk Management: Adverse Selection](#8-risk-management-adverse-selection)
9. [Conclusion: The Waitlist](#9-conclusion-the-waitlist)

---

# 1. Executive Summary

**Queue Position Estimation** determines your rank in the Limit Order Book.
In a FIFO (First-In-First-Out) market, being at the back of the line means you only get filled if *everyone else* gets filled first.
If the queue is huge, you are providing a "Free Option" to the market (Risk of being picked off) with low probability of a profitable fill.
Goliath tracks its virtual position to answer: **"Should I wait, or should I pay the spread?"**

---

# 2. The Theory: First In, First Out

### 2.1. The Queue

Limit Orders at the same price are a Linked List.
Head = First to Fill.
Tail = Last to Fill.
Exchange matches Head first.

### 2.2. The Latency Arms Race

Being 1 microsecond faster means you are #1 in the queue, not #100.
\#1 gets the fill. \#100 gets nothing (or gets filled only when the price crashes through the level).

---

# 3. Strategy Rules

### 3.1. Join vs Improve

* **Scenario:** You want to buy at Bid.
* **Metric:** Queue Size vs Average Trade Size.
* **Signal:**
  * If Queue is Massive (> 500 BTC): **Improve**. Bid + 0.01. You skip the entire line.
  * If Queue is Small (< 1 BTC): **Join**. You will be filled quickly.

### 3.2. The Cancel Game

* HFTs cancel orders constantly.
* **Estimated Position:** $Pos_{est} = Pos_{initial} - MarketExecutions - Cancellations_{estimated}$.
* If Cancellations comprise 90% of queue depletion, the "Support" is fake.

---

# 4. Mathematical Derivation

### 4.1. Fill Probability used in Execution Algos

$$ P_{fill}(t) = 1 - e^{-\mu t / Q(p)} $$
Where:

* $Q(p)$: Volume ahead of you.
* $\mu$: Order Flow Rate (how fast volume is eaten).
* $t$: Time elapsed.

### 4.2. Position Update

$$ Pos_t = Pos_{t-1} - V_{trade} - (C_{total} \times \frac{Pos_{t-1}}{Size_{total}}) $$
(Assuming cancellations are uniformly distributed).

---

# 5. Historical Case Studies

### 5.1. The "Penny Jump"

HFTs detect a large institutional order joining the queue (creating a "Floor").
They place a bid 1 tick higher.
If price goes up, they profit.
If price goes down, they sell to the institution (scratch trade).
Risk-free arbitrage at the expense of the large order.

---

# 6. Implementation: Production Grade

### 6.1. Python (Simulation)

```python
class QueueSimulator:
    def place_order(self, current_level_volume, my_size):
        self.queue_ahead = current_level_volume
        
    def on_market_trade(self, qty):
        if self.queue_ahead > 0:
            self.queue_ahead -= qty
            if self.queue_ahead < 0:
                print("FILLED!")
```

### 6.2. Rust (MBO Data)

```rust
pub struct QueueTracker {
    my_order_id: u64,
    orders_ahead: Vec<u64>, // List of IDs ahead of me
}

impl QueueTracker {
    pub fn on_cancel(&mut self, cancelled_id: u64) {
        if let Some(idx) = self.orders_ahead.iter().position(|&x| x == cancelled_id) {
            self.orders_ahead.remove(idx); // I move up!
        }
    }
}
```

---

# 7. Optimization

### 7.1. Queue Hopping

If Queue at Best Bid is 1000 BTC, but Queue at Best Bid + 1 tick is empty.
Pay the 1 tick. The "Cost" of waiting is higher than the spread.

### 7.2. LIFO execution

Some exchanges offer Last-In-First-Out for market makers.
Strategy reverses: Always be the *last* to join.

---

# 8. Risk Management: Adverse Selection

### 8.1. The "Toxic Fill"

You typically get filled when you *shouldn't* have been.
(i.e., when a massive sell order crushes the level).
**Rule:** If Order Flow Toxicity (VPIN) spikes, Cancel your Limit Order. Don't be a sitting duck.

### 8.2. Rear View Mirror

If orders *behind* you cancel, the support is eroding.
Even if you are #1, if there is no one #2-#100, you are exposed.

---

# 9. Conclusion: The Waitlist

Queue Position Estimation is the **Optimization of Patience**.
It tells Goliath exactly when to stand in line, and when to buy the VIP pass.
It transforms execution from "Hope" to "Calculated Probability".
It is the strategy of the Line Cutter.
