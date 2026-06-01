# 97 - Neuromorphic Computing & Spiking Neural Networks (SNN)

**Volume:** 97 of 100
**Strategy Type:** Future Tech / AI / Hardware Acceleration / Event-Driven
**Risk Profile:** Hardware Availability (Intel Loihi) / Toolchain Maturity
**Mathematical Basis:** Leaky Integrate-and-Fire (LIF) Neuron Model ($\tau \frac{dV}{dt} = -(V - V_{rest}) + RI$) & Spike-Timing-Dependent Plasticity (STDP)

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Historical Context](#2-historical-context)
    * 2.1. Carver Mead & The Silicon Brain.
    * 2.2. The Energy Equation: Why Brains beat GPUs (Sparsity).
3. [The Theory: Trading Time](#3-the-theory-trading-time)
    * 3.1. Von Neumann Bottleneck vs Neuromorphic Architecture.
    * 3.2. Spiking Neural Networks (Indicator 096): Processing events, not frames.
    * 3.3. Spike-Timing-Dependent Plasticity (STDP): Learning causality from time.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. The LIF Neuron Differential Equation.
    * 4.2. Synaptic Weight Update (Hebbian Learning).
5. [The Strategy Rules](#5-the-strategy-rules)
    * 5.1. Encoding: Turning Prices into Spikes (Temporal Coding).
    * 5.2. Architecture: Liquid State Machines (LSM).
    * 5.3. Signal: High-Density Spike Cascades (The "Surprise" Factor).
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python: Simulation with `snntorch` / `Nengo`.
    * 6.2. Rust: Custom LIF Simulation.
    * 6.3. Hardware: Intel Loihi 2 Deployment.
7. [Risk Management](#7-risk-management)
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Strategy 97** is the deployment of **Neuromorphic Computing** using **Spiking Neural Networks (Indicator 096)**.
Financial markets are not "frames" (like video). They are asynchronous event streams (Ticks).
Standard AI (CNNs/Transformers) forces these events into artificial "batches", wasting energy and latency.
SNNs process data sparsely—only firing when something changes.
By running SNNs on Neuromorphic chips (Intel Loihi), Goliath achieves **nanosecond** decision latency with **microwatt** power consumption, processing the market as a biological brain processes reality: In real-time, event-by-event.

---

# 2. Historical Context

### 2.1. Carver Mead (1980s)

Standard computers separate Memory (RAM) and Processing (CPU). Moving data between them takes 90% of the energy.
Carver Mead proposed **Neuromorphic Engineering**: Co-locating memory and processing, just like a synapse.

### 2.2. The "Surprise" Spike (Indicator 096)

Brains don't process "background noise". They process "surprise".
If a stock trades flat for an hour, the SNN is silent (Zero energy).
When a block trade hits, the SNN explodes with activity.
This matches the "Fat Tail" distribution of markets perfectly.

---

# 3. The Theory: Trading Time

### 3.1. Spiking Neural Networks (Indicator 096)

**LIF Neuron:**
It accumulates voltage (Information). It leaks voltage (Forgetting). It fires (Decision) only when threshold is breached.
**Temporal Coding:**
Information is encoded in the *timing* of the spike.
Faster spike = Stronger signal.
This allows the network to react to the *first* arriving photon (or tick), rather than waiting for the whole "frame" to load.

### 3.2. STDP (The Learning Rule)

"Neurons that fire together, wire together."

* If Input A (Order Book Imbalance) fires *before* Input B (Price Up), the connection strengthens. (Causal).
* If Input A fires *after* Input B, the connection weakens. (Acausal).
The network learns the *causal structure* of the microstructure unsupervised.

---

# 4. Mathematical Derivation

### 4.1. Leaky Integrate-and-Fire

$$ \tau \frac{dV(t)}{dt} = -(V(t) - V_{rest}) + R I(t) $$
Discrete update:
$$ V[t+1] = \beta V[t] + (1-\beta)I[t] $$
Where $\beta = e^{-\Delta t/\tau}$ (Decay factor).

### 4.2. STDP Weight Update

$$ \Delta w = A_+ e^{-\Delta t / \tau_+} \quad \text{if } t_{pre} < t_{post} $$
$$ \Delta w = -A_- e^{\Delta t / \tau_-} \quad \text{if } t_{pre} > t_{post} $$

---

# 5. The Strategy Rules

### 5.1. Encoding (The Retina)

* **Input:** L3 Feed.
* **Delta Modulation:**
  * Price $+\delta$: Fire Positive Spike.
  * Price $-\delta$: Fire Negative Spike.
  * Volume $>$ Threshold: Fire Volume Spike.

### 5.2. Architecture: Liquid State Machine

* **Input Layer:** 100 Neurons (Price, Vol, Order Book Levels).
* **Liquid Layer:** 1000 Neurons, randomly connected, recurrent. Generates high-dimensional "ripples" from inputs.
* **Readout Layer:** Trained Linear Classifier. Detects "Pre-Crash" ripples.

---

# 6. Implementation: Production Grade

### 6.1. Python: SNN Simulation (snntorch)

*(From Indicator 096 Source)*

```python
import torch
import snntorch as snn
from snntorch import spikeplot as splt

# LIF Parameters
beta = 0.95 
threshold = 1.0

# Define Neuron
lif = snn.Leaky(beta=beta, threshold=threshold)

def simulate_market_tick(spike_train):
    mem = torch.zeros(1)
    spk_out = []
    
    for x in spike_train:
        # x is 1 if trade occurred, 0 otherwise
        spk, mem = lif(x, mem)
        spk_out.append(spk)
        
    return torch.stack(spk_out)
```

### 6.2. Python: Nengo (Neuromorphic Compiler)

*(From Strategy 97 Source)*

```python
import nengo

def build_neuromorphic_trader():
    with nengo.Network() as model:
        # Input: Normalized Price Stream
        stim = nengo.Node(lambda t: get_market_price(t))
        
        # Ensemble: 1000 Spiking Neurons
        ens = nengo.Ensemble(n_neurons=1000, dimensions=1, neuron_type=nengo.LIF())
        
        nengo.Connection(stim, ens)
        
        # Readout: Smoothed Output (Buying Pressure)
        output = nengo.Node(size_in=1)
        nengo.Connection(ens, output, synapse=0.01) # 10ms filter
        
    return model
```

---

# 7. Risk Management

### 7.1. The Seizure (Runaway Excitation)

If positive feedback loops in the Liquid Layer are too strong, the network enters "Epilepsy" (Firing max rate continuously).
**Solution:** Refractory Periods (Force silence for 2ms after firing) and Homeostatic Plasticity (Dynamic thresholds).

### 7.2. Hardware Failure

Loihi is experimental.
**Fallback:** If Heartbeat from Neuromorphic chip fails, switch to CPU-based MLP immediately.

---

# 8. Conclusion

Strategy 97 is the **Cyborg**.
It is not software running on hardware.
It is logic fused with silicon.
By adopting the **Spiking Neural Network**, Goliath moves from "Computing the Market" to "Sensing the Market".
It doesn't just predict the next tick. It *feels* it.
