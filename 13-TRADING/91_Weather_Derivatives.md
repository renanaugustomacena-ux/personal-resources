# 91 - Weather Derivatives \u0026 Topological Data Analysis (TDA)

**Volume:** 91 of 100
**Strategy Type:** Alternative Data / Commodities / TDA / Chaos Theory
**Risk Profile:** Climate Drift / Basis Risk
**Mathematical Basis:** Ornstein-Uhlenbeck Process, Persistent Homology (Betti Numbers) \u0026 Vietoris-Rips Complex

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Historical Context](#2-historical-context)
    * 2.1. Weather as an Asset Class (Enron, Citadel).
    * 2.2. Topological Data Analysis (Gunnar Carlsson).
3. [The Theory: Chaos \u0026 Shape](#3-the-theory-chaos--shape)
    * 3.1. Degree Days (HDD/CDD).
    * 3.2. Topology of Data (Indicator 095): Measuring the "Shape" of the Atmosphere.
4. [Mathematical Derivation](#4-mathematical-derivation)
    * 4.1. Pricing Weather Futures.
    * 4.2. Betti Numbers \u0026 Persistence Diagrams.
5. [The Strategy Rules](#5-the-strategy-rules)
    * 5.1. Fair Value Calculation (Forecast + Climatology).
    * 5.2. TDA Signal (Phase Transition Detection).
    * 5.3. Execution \u0026 Hedging.
6. [Implementation: Production Grade](#6-implementation-production-grade)
    * 6.1. Python: HDD/CDD Calculator.
    * 6.2. Python: TDA Pipeline (Giotto-TDA).
7. [Risk Management](#7-risk-management)
8. [Conclusion](#8-conclusion)

---

# 1. Executive Summary

**Strategy 91** trades **Weather Derivatives** (HDD/CDD Futures) to capture alpha that is completely uncorrelated to financial markets.
Weather is a chaotic dynamic system. Linear models (ARIMA) often fail to predict extreme events (Polar Vortex).
We detect these events using **Topological Data Analysis (Indicator 095)**.
TDA treats weather data (Pressure/Temp grids) as high-dimensional point clouds and measures their "Shape" (Topology).
Approaching a "Phase Transition" (Major Storm/Regime Shift) changes the topology (e.g., created "Holes" or "Loops" in the data manifold), signaling a massive volatility event before it hits the forecast models.

---

# 2. Historical Context

### 2.1. Weather Derivatives

Enron invented this market in 1997. It is now used by Energy companies to hedge volume risk (Warm winter = Less gas sales).
Hedge Funds (Citadel/RenTech) hire meteorologists to beat the NOAA models.

### 2.2. TDA (Indicator 095)

Developed at Stanford by Gunnar Carlsson (2000s). Originally for biological data (Protein folding).
Quants realized financial/weather time series are high-dimensional structures. TDA provides a way to visualize the structure without dimensionality reduction (PCA) loss.

---

# 3. The Theory: Chaos \u0026 Shape

### 3.1. Degree Days

$$ HDD = \max(0, 65 - T_{avg}) $$
$$ CDD = \max(0, T_{avg} - 65) $$
The contract pays out cumulative Degree Days.

### 3.2. Topological Data Analysis (Indicator 095)

**Vietoris-Rips Complex:**
Given a point cloud $X$ (Weather stations) and radius $\epsilon$.
Connect points if distance $<\epsilon$.
**Betti Numbers:**

* $\beta_0$: Connected Components (Islands).
* $\beta_1$: Loops (Holes).
* $\beta_2$: Voids (Bubbles).
**Signal:** Stable weather has simple topology. Pre-Crash/Storm weather exhibits "Topological Complexity" (Spike in $\beta_1$).

---

# 4. Mathematical Derivation

### 4.1. Pricing Model

$$ F(t, \mathcal{T}) = E_Q \left[ \int_t^{\mathcal{T}} HDD(u) du \right] $$
Using an Ornstein-Uhlenbeck process for daily temperature.

### 4.2. Persistence Diagram (from 095)

A plot of (Birth, Death) for each topological feature as we increase $\epsilon$.
Long-lived features are "Real". Short-lived features are "Noise".
**Metric:** Persistence Entropy.
$$ S = -\sum p_i \log p_i $$
High Entropy = High Structural Chaos = Buy Volatility.

---

# 5. The Strategy Rules

### 5.1. Fair Value (The Baseline)

Blend:

1. **Forecast (0-14 days):** GFS/ECMWF Ensemble.
2. **Climatology (15-30 days):** 10-year de-trended average (Accounting for Climate Change).

### 5.2. The TDA Signal (The Alpha)

1. **Input:** 3D array of Pressure/Temp (Lat, Lon, Time).
2. **Compute:** Persistence Entropy of the system.
3. **Trigger:** If Entropy spikes > 2 Sigma.
4. **Prediction:** The current regime is breaking. Forecast models will fail.
5. **Action:** Buy Options (Straddles) on Weather Futures.

---

# 6. Implementation: Production Grade

### 6.1. Python: HDD Calculator

*(From Strategy 91 Source)*

```python
def calculate_hdd_cdd(t_min, t_max, base=65):
    t_avg = (t_min + t_max) / 2
    hdd = max(0, base - t_avg)
    cdd = max(0, t_avg - base)
    return hdd, cdd
```

### 6.2. Python: TDA Analysis

*(From Indicator 095 Source - Integrated)*

```python
import numpy as np
from gtda.homology import VietorisRipsPersistence
from gtda.diagrams import PersistenceEntropy

def measure_weather_topology(pressure_cloud):
    """
    pressure_cloud: Array of shape (N_samples, Dim) representing weather state
    """
    # 1. Compute Persistence Diagram
    VR = VietorisRipsPersistence(homology_dimensions=[0, 1])
    diagrams = VR.fit_transform([pressure_cloud])
    
    # 2. Compute Entropy (Complexity of the shape)
    PE = PersistenceEntropy()
    entropy = PE.fit_transform(diagrams)
    
    return entropy[0] # Signal: High Entropy = Storm Risk
```

---

# 7. Risk Management

### 7.1. Climate Drift

"10-year Average" is useless if the planet is warming.
**Rule:** Use de-trended averages to price Climatology.

### 7.2. Topological Noise

TDA is sensitive to outliers.
**Mitigation:** Use "Robust TDA" (Weighted Rips Filtration) to ignore sensor noise.

---

# 8. Conclusion

Strategy 91 is the **Meteorologist**.
It trades the one variable that affects the entire global economy (Energy, Food, Transport).
By applying **Topological Data Analysis**, it moves beyond linear thermodynamics and visualizes the geometric structure of chaos.
It predicts the storm by seeing the "holes" in the atmosphere's stability.
