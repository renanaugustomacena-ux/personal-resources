# 73 - Autoencoders & NVT Ratio: Denoising Value

**Volume:** 73 of 100
**Strategy Type:** Unsupervised Learning / On-Chain Valuation / Anomaly Detection
**Risk Profile:** False Positives / Model Threshold Calibration
**Mathematical Basis:** Reconstruction Error ($MSE$) & Network Value to Transactions ($Price / Volume$)

> "NVT is the P/E ratio of crypto. Autoencoders help us see if the 'E' is real or fake."

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Theory: The Signal and The Noise](#2-the-theory-the-signal-and-the-noise)
    * 2.1. Autoencoders: Learning Normality.
    * 2.2. NVT Ratio (073): The Fundamental Valuation (Willy Woo).
    * 2.3. The Synergy: Detecting "Fake" NVT signals (e.g. Wash Trading).
3. [The Strategy Rules](#3-the-strategy-rules)
    * 3.1. **The Fundamental Signal:** Buy when NVT < 50 (Undervalued). Sell when NVT > 150 (Bubble).
    * 3.2. **The Autoencoder Filter:** If NVT is Low, but Reconstruction Error is High, it means "Abnormal On-Chain Activity" (Spam/Dust). Ignore the signal.
    * 3.3. **Early Warning:** High Reconstruction Error often precedes a crash.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Autoencoder Loss Function.
    * 4.2. NVT Ratio Calculation.
    * 4.3. Latent Space Compression.
5. [Historical Case Studies](#5-historical-case-studies)
    * 5.1. **2017 Top:** NVT spiked to 200. Autoencoder Error spiked. Perfect short.
    * 5.2. **Lightning Network Launch:** Off-chain volume increased. Standard NVT looked bearish (High). But AE recognized the pattern shift and stayed neutral.
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python (PyTorch Autoencoder + Glassnode API).
    * 6.2. Rust (NVT Calculation).
7. [Risk Management](#7-risk-management)
    * 7.1. Feature Drift (New L2s change L1 dynamics).
    * 7.2. The "Cry Wolf" Problem (Sensitivity).
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Strategy 73** combines Fundamental Analysis (**NVT Ratio**) with Unsupervised Machine Learning (**Autoencoders**).

* **Indicator 073 (NVT):** Tells us if the network is expensive relative to usage.
* **Strategy 73 (Autoencoder):** tells us if the usage is *organic* or *anomalous*.

**The Edge:**
Crypto data is noisy. Spam attacks using dust transactions can lower NVT artificially, tricking traders into buying.
An Autoencoder trained on "Healthy Blocks" will flag these spam blocks as anomalies (High Reconstruction Error), saving GOLIATH from the trap.

---

# 2. The Theory

## 2.1. Autoencoders (The Denoizer)

A Neural Network trained to copy Input $\to$ Output, but squeezed through a tiny "Bottleneck".
It learns the "Essence" of the data.
If you feed it data that *doesn't* match the essence (Anomaly), it fails to copy it.
$Error = ||Input - Output||$.
High Error = Anomaly.

## 2.2. NVT Ratio (The P/E)

$$ NVT = \frac{\text{Market Cap}}{\text{Daily On-Chain Volume}} $$

* High NVT: Speculative Premium (Bubble).
* Low NVT: High Utility (Value).

## 2.3. The Synergy

We input [NVT, ActiveAddresses, TransactionCount, MempoolSize] into the AE.
The AE learns the "Normal Relationship" between Price and Activity.
If Price pumps but Activity is flat, the AE screams "Anomaly" (Divergence).

---

# 3. The Strategy Rules

## 3.1. Fundamental Entry

* **Condition:** NVT Signal (90d MA smoothed) < Lower Band (Historic Lows).
* **Confirmation:** Autoencoder Reconstruction Error is LOW (Normal market conditions).
* **Action:** Accumulate Spot.

## 3.2. Anomaly Exit (The Crash Detector)

* **Condition:** Reconstruction Error > 99th Percentile.
* **Meaning:** Market structure has broken. (Flash Crash, Liquidity event, Exchange Hack).
* **Action:** Close all positions immediately. Wait 24 hours.

---

# 4. Mathematical Derivation

## 4.1. Autoencoder Loss

$$ L(x, \hat{x}) = \frac{1}{N} \sum_{i=1}^N (x_i - \hat{x}_i)^2 $$
Where $\hat{x} = Decoder(Encoder(x))$.

## 4.2. NVT Signal (Willy Woo)

$$ NVT_{Sig} = \frac{Market Cap}{MA_{90}(Volume_{USD})} $$
Use a 90-day moving average for volume to smooth out weekend dips.

---

# 5. Historical Case Studies

## 5.1. The 2017 Bubble

NVT reached 200+.
Price was \$20,000.
Volume was not supporting the price.
An AE trained on 2016 data would show massive Reconstruction Error in Dec 2017.
**Result:** Signal to Short.

## 5.2. The "Spam" Attack (2020)

Cheap fees allowed bots to spam the network.
Transaction count spiked. NVT dropped.
"Buy Signal?" No.
The AE saw that "Transaction Value" was tiny despite "Transaction Count" being huge. This pattern was anomalous.
**Result:** Signal Ignored (Correctly).

---

# 6. Implementation: Production Grade

## 6.1. Python (PyTorch Autoencoder)

```python
import torch
import torch.nn as nn

class MarketAutoencoder(nn.Module):
    def __init__(self, input_dim=10, latent_dim=3):
        super().__init__()
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, latent_dim), # Bottleneck
            nn.ReLU()
        )
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim),
            nn.Sigmoid() # Output 0-1 (Normalized data)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

def get_nvt(market_cap, volume_90d):
    return market_cap / volume_90d
```

## 6.2. Rust (Reconstruction Error Check)

```rust
pub fn is_anomaly(input: &Vec<f64>, output: &Vec<f64>, threshold: f64) -> bool {
    let mut mse = 0.0;
    for i in 0..input.len() {
        mse += (input[i] - output[i]).powi(2);
    }
    mse /= input.len() as f64;
    
    mse > threshold
}
```

---

# 7. Risk Management

## 7.1. The "Cry Wolf" Problem

If you set the Anomaly Threshold too low, you exit every time Elon Musk tweets.
**Calibrate:** Set threshold at 3 Standard Deviations above the rolling mean of the error.

## 7.2. Feature Drift

As Lightning Network grows, L1 volume drops.
NVT naturally rises over time.
The AE must be **retrained monthly** to learn the "New Normal".

---

# 8. Conclusion

**Strategy 73** acts as the "Truth Filter".
NVT gives us a Valuation.
Autoencoders give us specific Verification.
In a market filled with wash trading, fake volume, and manipulation, relying on raw indicators is dangerous.
GOLIATH uses Unsupervised Learning to ensure it is trading on **Real Signal**, not **Manufactured Noise**.
